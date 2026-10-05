"""Mozgófilm: diavetítés-videó export (#29).

Egyszerű, kiszámítható diavetítés: minden kép azonos ideig áll a vásznon,
a képek között opcionális áttűnés (lineáris keverés). A kimenet MP4
(`mp4v` kodek) — az OpenCV minden platformon viszi, külön ffmpeg-telepítés
nélkül.

A képek **arányosan, letterbox-szal** kerülnek a vászonra: a fotó soha nem
torzul, a maradék hely a háttérszíné. Ez a Picasa mozgófilmjének
viselkedése is.

Ha a videóíró nem nyitható meg (kodek hiánya a futtató rendszeren), a
függvény **beszédes kivétellel** áll meg, nem ír fél fájlt — a hívó
(worker-szál) így emberi hibaüzenetet tud mutatni.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from picasapy.lazy_cv2 import cv2
import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFont

from picasapy.cvimage import dekodolj_forrast

# A kodek-négyes: MP4 konténer, széles körben elérhető OpenCV-ben.
_FOURCC = "mp4v"

_TRANSITION_TYPES = frozenset(
    {
        "cut", "dissolve", "dissolveblack", "dissolvewhite",
        "wipeleft", "wiperight", "wipeup", "wipedown",
        "diagwipeul", "diagwipeur", "diagwipedl", "diagwipedr",
        "pushleft", "pushright", "pushtop", "pushdown",
        "circlein", "circleout", "kenburns", "kenburnsaoi",
        "timelapse", "rect",
    }
)


@dataclass(frozen=True)
class MovieSettings:
    """Videó-beállítások: felbontás, képkocka-sebesség, képenkénti idő.

    A `transition_seconds` a két kép közti áttűnés hossza (0 = kemény
    vágás); sosem lehet hosszabb a képenkénti időnél."""

    width: int = 1280
    height: int = 720
    fps: int = 24
    seconds_per_photo: float = 3.0
    transition_seconds: float = 0.5
    background: tuple[int, int, int] = (0, 0, 0)
    transition_type: str = "dissolve"
    audio_path: Path | None = None
    audio_option: int = 0
    text_slides: tuple[dict[str, object], ...] = ()
    show_captions: bool = False
    show_dates: bool = False
    cropfit: bool = False
    remove_low_res_faces: bool = False
    ordering: int = 1
    burstmodethresh: int = 0

    def __post_init__(self) -> None:
        if self.width < 16 or self.height < 16:
            raise ValueError(f"Érvénytelen felbontás: {self.width}×{self.height}")
        if self.width % 2 or self.height % 2:
            # a legtöbb kodek páros oldalhosszt vár
            raise ValueError("A videó szélessége és magassága páros legyen.")
        if not 1 <= self.fps <= 60:
            raise ValueError(f"Érvénytelen képkocka-sebesség: {self.fps}")
        if self.seconds_per_photo <= 0:
            raise ValueError(
                f"Érvénytelen képenkénti idő: {self.seconds_per_photo}"
            )
        if self.transition_seconds < 0:
            raise ValueError(f"Érvénytelen áttűnés: {self.transition_seconds}")
        if self.transition_seconds >= self.seconds_per_photo:
            raise ValueError("Az áttűnés nem lehet hosszabb a képenkénti időnél.")
        if self.transition_type not in _TRANSITION_TYPES:
            raise ValueError(f"Ismeretlen filmátmenet: {self.transition_type}")
        if self.audio_option not in (0, 1, 2):
            raise ValueError("A hangsáv beállítása 0, 1 vagy 2 lehet.")
        if self.ordering not in (0, 1, 2):
            raise ValueError("A diák sorrendje 0, 1 vagy 2 lehet.")
        if not 0 <= self.burstmodethresh <= 86400:
            raise ValueError("A sorozatfelvétel-időszűrő 0 és 86400 másodperc közé essen.")
        object.__setattr__(self, "text_slides", tuple(dict(slide) for slide in self.text_slides))

    @property
    def frames_per_photo(self) -> int:
        return max(1, round(self.seconds_per_photo * self.fps))

    @property
    def transition_frames(self) -> int:
        return max(0, round(self.transition_seconds * self.fps))


@dataclass(frozen=True)
class MovieReport:
    """Az exportfutás eredménye: célfájl, felhasznált képek, kockaszám."""

    target: Path
    used: tuple[Path, ...]
    skipped: tuple[Path, ...]
    reasons: tuple[str, ...]
    frames: int
    # #459/3: a kihagyottak közül a NEM LÉTEZŐ fájlok (elmozdítva,
    # átnevezve, törölve) — külön üzenetet érdemelnek
    missing: tuple[Path, ...] = ()


_DEFAULT_SETTINGS = MovieSettings()


def letterbox(
    image: np.ndarray,
    width: int,
    height: int,
    background: tuple[int, int, int] = (0, 0, 0),
) -> np.ndarray:
    """A kép arányos beillesztése a vászonra, középre, háttérrel kitöltve."""
    if width < 1 or height < 1:
        raise ValueError(f"Érvénytelen vászon: {width}×{height}")
    src_h, src_w = image.shape[:2]
    if src_h < 1 or src_w < 1:
        raise ValueError("Üres kép")
    scale = min(width / src_w, height / src_h)
    new_w = max(1, min(width, round(src_w * scale)))
    new_h = max(1, min(height, round(src_h * scale)))
    interpolation = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(image, (new_w, new_h), interpolation=interpolation)
    canvas = np.full(
        (height, width, 3), np.array(background, dtype=np.uint8), dtype=np.uint8
    )
    x0 = (width - new_w) // 2
    y0 = (height - new_h) // 2
    canvas[y0 : y0 + new_h, x0 : x0 + new_w] = resized
    return canvas


def crop_to_fit(
    image: np.ndarray,
    width: int,
    height: int,
) -> np.ndarray:
    """A fotó kitölti a képkockát; a középre eső szélek levágódnak."""
    if width < 1 or height < 1:
        raise ValueError(f"Érvénytelen vászon: {width}×{height}")
    src_h, src_w = image.shape[:2]
    if src_h < 1 or src_w < 1:
        raise ValueError("Üres kép")
    scale = max(width / src_w, height / src_h)
    new_w = max(width, round(src_w * scale))
    new_h = max(height, round(src_h * scale))
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    x0 = (new_w - width) // 2
    y0 = (new_h - height) // 2
    return resized[y0 : y0 + height, x0 : x0 + width]


def _decode(source: Path) -> np.ndarray:
    #: #3120: a KÖZÖS belépőn megy — a `cv2.imdecode`-nak nincs nyers
    #: dekódere, tehát a RAW fájlokra némán `None`-t adott.
    image = dekodolj_forrast(source)
    if image is None:
        raise ValueError("nem dekódolható kép")
    return image


def _atmeneti_kocka(
    kilepo: np.ndarray, erkezo: np.ndarray, tipus: str, arany: float
) -> np.ndarray:
    """Egy áttűnés képkockája a kiválasztott Picasa-típus alapján.

    A teljes 22-es készletet a spec szerinti kulcsokkal kezeljük. Az eredeti
    program effekt-görbéi nem részei a 2.1-es leírásnak; itt a típus neve
    szerinti, kiszámítható geometriai változat készül.
    """
    p = min(1.0, max(0.0, arany))
    if tipus == "cut":
        return erkezo
    if tipus in {"dissolve", "timelapse"}:
        if tipus == "timelapse":
            p = round(p * 6) / 6
        return cv2.addWeighted(kilepo, 1.0 - p, erkezo, p, 0.0)
    if tipus in {"dissolveblack", "dissolvewhite"}:
        alapszin = 0 if tipus == "dissolveblack" else 255
        koztes = np.full_like(kilepo, alapszin)
        if p < 0.5:
            return cv2.addWeighted(kilepo, 1.0 - p * 2, koztes, p * 2, 0.0)
        return cv2.addWeighted(koztes, 1.0 - (p - 0.5) * 2, erkezo, (p - 0.5) * 2, 0.0)

    magassag, szelesseg = kilepo.shape[:2]
    y, x = np.mgrid[0:magassag, 0:szelesseg]
    xn = (x + 0.5) / max(1, szelesseg)
    yn = (y + 0.5) / max(1, magassag)

    iranyok = {
        "wipeleft": xn < p,
        "wiperight": xn >= 1.0 - p,
        "wipeup": yn >= 1.0 - p,
        "wipedown": yn < p,
        "diagwipeul": xn + yn < 2.0 * p,
        "diagwipeur": (1.0 - xn) + yn < 2.0 * p,
        "diagwipedl": xn + (1.0 - yn) < 2.0 * p,
        "diagwipedr": (1.0 - xn) + (1.0 - yn) < 2.0 * p,
    }
    if tipus in iranyok:
        return np.where(iranyok[tipus][..., None], erkezo, kilepo)

    if tipus in {"circlein", "circleout"}:
        tav = np.sqrt(((xn - 0.5) * 2) ** 2 + ((yn - 0.5) * 2) ** 2)
        sugar = p * np.sqrt(2)
        belul = tav <= sugar
        if tipus == "circleout":
            belul = ~belul
        return np.where(belul[..., None], erkezo, kilepo)

    if tipus == "rect":
        szeles = p * 0.5
        mag = p * 0.5
        kozep = (np.abs(xn - 0.5) <= szeles) & (np.abs(yn - 0.5) <= mag)
        return np.where(kozep[..., None], erkezo, kilepo)

    if tipus in {"pushleft", "pushright", "pushtop", "pushdown"}:
        out = np.empty_like(kilepo)
        if tipus == "pushleft":
            offset = round(szelesseg * p)
            out[:, : szelesseg - offset] = kilepo[:, offset:]
            out[:, szelesseg - offset :] = erkezo[:, :offset]
        elif tipus == "pushright":
            offset = round(szelesseg * p)
            out[:, offset:] = kilepo[:, : szelesseg - offset]
            out[:, :offset] = erkezo[:, szelesseg - offset :]
        elif tipus == "pushtop":
            offset = round(magassag * p)
            out[: magassag - offset, :] = kilepo[offset:, :]
            out[magassag - offset :, :] = erkezo[:offset, :]
        else:
            offset = round(magassag * p)
            out[offset:, :] = kilepo[: magassag - offset, :]
            out[:offset, :] = erkezo[magassag - offset :, :]
        return out

    if tipus in {"kenburns", "kenburnsaoi"}:
        # Az arc fókuszpontja nem része a jelenlegi fotóadat-modellnek; a
        # középpontos pásztázás mindkét Ken Burns-változatnál stabil alap.
        scale = 1.12 - 0.12 * p
        uj_w = max(1, round(szelesseg * scale))
        uj_h = max(1, round(magassag * scale))
        nagy = cv2.resize(erkezo, (uj_w, uj_h), interpolation=cv2.INTER_LINEAR)
        x0 = max(0, (uj_w - szelesseg) // 2)
        y0 = max(0, (uj_h - magassag) // 2)
        mozgatott = nagy[y0 : y0 + magassag, x0 : x0 + szelesseg]
        return cv2.addWeighted(kilepo, 1.0 - p, mozgatott, p, 0.0)

    return erkezo


def _ffmpeg_exe() -> str | None:
    """FFmpeg útvonal: beágyazott kerék, majd a rendszer PATH-ja."""
    try:
        import imageio_ffmpeg

        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        return shutil.which("ffmpeg")


def _hang_hossza(ffmpeg: str, hang: Path) -> float:
    """A hangsáv hosszát az FFmpeg bemeneti fejlécéből olvassa ki."""
    if not hang.is_file():
        raise FileNotFoundError(f"A kiválasztott hangsáv nem található: {hang}")
    eredmeny = subprocess.run(
        [ffmpeg, "-i", str(hang), "-f", "null", "-"],
        capture_output=True,
        text=True,
        check=False,
    )
    talalat = re.search(
        r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", eredmeny.stderr
    )
    if talalat is None:
        raise RuntimeError("A hangsáv időtartamát nem sikerült beolvasni.")
    ora, perc, masodperc = talalat.groups()
    return int(ora) * 3600 + int(perc) * 60 + float(masodperc)


def _hanggal_osszeilleszt(
    ffmpeg: str, video: Path, hang: Path, cel: Path, mod: int
) -> None:
    """A kész képsávhoz AAC hangsávot illeszt, a választott három mód egyikével."""
    handle, atmeneti_cel = tempfile.mkstemp(
        prefix=f".{cel.stem}-", suffix=cel.suffix or ".mp4", dir=cel.parent
    )
    os.close(handle)
    try:
        parancs = [ffmpeg, "-y"]
        if mod == 2:
            parancs.extend(["-stream_loop", "-1"])
        parancs.extend(
            [
                "-i", str(video), "-i", str(hang),
                "-map", "0:v:0", "-map", "1:a:0",
                "-c:v", "copy", "-c:a", "aac", "-shortest", atmeneti_cel,
            ]
        )
        eredmeny = subprocess.run(parancs, capture_output=True, text=True, check=False)
        if eredmeny.returncode:
            raise RuntimeError("A hangsávot nem sikerült a filmhez illeszteni.")
        os.replace(atmeneti_cel, cel)
    finally:
        Path(atmeneti_cel).unlink(missing_ok=True)


def _szovegdia(slide: dict[str, object], settings: MovieSettings) -> np.ndarray:
    """Képkockát készít a Szöveg fülön felvett dia beállításaiból."""
    def szin(ertek: object, tartalek: str) -> tuple[int, int, int]:
        try:
            return ImageColor.getrgb(str(ertek))[:3]
        except (ValueError, TypeError):
            return ImageColor.getrgb(tartalek)

    hatter = szin(slide.get("backgroundColor"), "#000000")
    betuszín = szin(slide.get("textColor"), "#ffffff")
    kep = Image.new("RGB", (settings.width, settings.height), hatter)
    rajz = ImageDraw.Draw(kep, "RGBA")
    meret = max(8, int(slide.get("size", 16)))
    betu = str(slide.get("font", "DejaVuSans"))
    fontfajlok = [betu, f"{betu}.ttf"]
    if slide.get("italic"):
        fontfajlok.append("DejaVuSans-Oblique.ttf")
    if slide.get("bold"):
        fontfajlok.append("DejaVuSans-Bold.ttf")
    fontfajlok.append("DejaVuSans.ttf")
    font = None
    for fontfajl in fontfajlok:
        try:
            font = ImageFont.truetype(fontfajl, meret)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()

    szoveg = str(slide.get("text", ""))
    if not szoveg:
        return cv2.cvtColor(np.asarray(kep), cv2.COLOR_RGB2BGR)
    stilus = int(slide.get("style", 0))
    marg = max(16, settings.width // 18)
    keret = rajz.multiline_textbbox((0, 0), szoveg, font=font)
    szoveg_szeles = keret[2] - keret[0]
    szoveg_magas = keret[3] - keret[1]
    if stilus in (2, 3, 11):
        x = max(marg, (settings.width - szoveg_szeles) // 2)
        y = settings.height - szoveg_magas - marg
    elif stilus == 9:
        x, y = marg, (settings.height - szoveg_magas) // 2
    elif stilus == 10:
        x, y = settings.width - szoveg_szeles - marg, (settings.height - szoveg_magas) // 2
    else:
        x, y = (settings.width - szoveg_szeles) // 2, (settings.height - szoveg_magas) // 2
    if stilus in (4, 5, 6, 7):
        sav = (0, 0, 0, 180) if stilus in (4, 6) else (255, 255, 255, 180)
        rajz.rectangle((0, y - marg // 2, settings.width, y + szoveg_magas + marg // 2), fill=sav)
        betuszín = (255, 255, 255) if stilus in (4, 6) else (0, 0, 0)
    kontur = bool(slide.get("outline")) or stilus in (3, 11)
    rajz.multiline_text(
        (x, y),
        szoveg,
        font=font,
        fill=betuszín,
        stroke_width=max(1, meret // 18) if kontur or slide.get("bold") else 0,
        stroke_fill=(0, 0, 0) if betuszín != (0, 0, 0) else (255, 255, 255),
    )
    return cv2.cvtColor(np.asarray(kep), cv2.COLOR_RGB2BGR)


def _fotofelirat(frame: np.ndarray, path: Path, settings: MovieSettings) -> np.ndarray:
    """Az elérhető EXIF-feliratot/dátumot diszkrét alsó sávban mutatja."""
    if not settings.show_captions and not settings.show_dates:
        return frame
    caption = ""
    date = ""
    try:
        with Image.open(path) as photo:
            exif = photo.getexif()
            caption = str(exif.get(270, "") or "").strip()
            exif_values = exif
            try:
                exif_values = exif.get_ifd(34665) or exif
            except (AttributeError, KeyError, TypeError):
                pass
            raw_date = str(exif_values.get(36867) or exif.get(306) or "")
            if raw_date:
                date = raw_date.replace(":", "-", 2)
    except (OSError, ValueError):
        pass
    if settings.show_dates and not date:
        try:
            date = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
        except OSError:
            date = ""
    sorok = [s for s in (caption if settings.show_captions else "", date if settings.show_dates else "") if s]
    if not sorok:
        return frame
    image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image, "RGBA")
    font = ImageFont.load_default()
    pad = max(6, settings.width // 80)
    box = draw.multiline_textbbox((0, 0), "\n".join(sorok), font=font, spacing=2)
    band_h = box[3] - box[1] + 2 * pad
    y0 = settings.height - band_h
    draw.rectangle((0, y0, settings.width, settings.height), fill=(0, 0, 0, 180))
    draw.multiline_text((pad, y0 + pad), "\n".join(sorok), font=font, fill="white", spacing=2)
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)


def export_movie(
    sources,
    target: Path,
    settings: MovieSettings = _DEFAULT_SETTINGS,
    progress=None,
) -> MovieReport:
    """Diavetítés-videó írása a forrásképekből.

    `progress`: opcionális `callable(kész, összes)` — a UI haladásjelzője
    hívja képenként (nem kockánként: a kockák száma nagy, a képeké a
    felhasználó számára értelmes egység).

    Egy hibás kép kimarad (a `skipped`/`reasons` párban visszakapja a
    hívó); ha egyetlen kép sem használható, a függvény nem ír fájlt és
    üres `used`-del tér vissza."""
    paths = [Path(s) for s in sources]
    if not paths:
        raise ValueError("A mozgófilmhez legalább egy kép kell.")

    frames_written = 0
    used: list[Path] = []
    skipped: list[Path] = []
    reasons: list[str] = []
    missing: list[Path] = []
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    decoded: list[tuple[Path | None, np.ndarray]] = []
    for path in paths:
        if not path.exists():
            # #459/3: hiányzó fájl — a film a maradékkal elkészül
            missing.append(path)
            skipped.append(path)
            reasons.append("a fájl nem található")
            continue
        try:
            image = _decode(path)
        except (ValueError, OSError) as error:
            skipped.append(path)
            reasons.append(str(error))
            continue
        frame = (
            crop_to_fit(image, settings.width, settings.height)
            if settings.cropfit
            else letterbox(image, settings.width, settings.height, settings.background)
        )
        decoded.append((path, _fotofelirat(frame, path, settings)))

    text_frames = [(None, _szovegdia(slide, settings)) for slide in settings.text_slides]
    if settings.ordering == 2:
        decoded.sort(key=lambda entry: entry[0].stat().st_mtime if entry[0] else float("inf"))
    elif settings.ordering == 0 and len(decoded) > 1:
        # A „legjobb átmenet” sorrend a következő, színátlagban legközelebbi
        # képet választja. A döntés determinisztikus, és az album sorrendje
        # marad azonos távolság esetén.
        maradek = decoded[1:]
        rendezett = [decoded[0]]
        while maradek:
            elozo = np.mean(rendezett[-1][1], axis=(0, 1))
            kovetkezo = min(
                range(len(maradek)),
                key=lambda i: float(np.linalg.norm(elozo - np.mean(maradek[i][1], axis=(0, 1)))),
            )
            rendezett.append(maradek.pop(kovetkezo))
        decoded = rendezett
    decoded.extend(text_frames)

    if not decoded:
        return MovieReport(
            target=target,
            used=(),
            skipped=tuple(skipped),
            reasons=tuple(reasons),
            frames=0,
            missing=tuple(missing),
        )

    ffmpeg = _ffmpeg_exe() if settings.audio_path is not None else None
    if settings.audio_path is not None and ffmpeg is None:
        raise RuntimeError("A hangsávos filmhez nem található FFmpeg.")
    audio_duration = (
        _hang_hossza(ffmpeg, Path(settings.audio_path))
        if ffmpeg is not None and settings.audio_path is not None
        else 0.0
    )
    video_target = target
    if settings.audio_path is not None:
        handle, video_temp = tempfile.mkstemp(
            prefix=f".{target.stem}-video-", suffix=".mp4", dir=target.parent
        )
        os.close(handle)
        video_target = Path(video_temp)

    writer = cv2.VideoWriter(
        str(video_target),
        cv2.VideoWriter_fourcc(*_FOURCC),
        float(settings.fps),
        (settings.width, settings.height),
    )
    if not writer.isOpened():
        raise RuntimeError(
            "A videó nem hozható létre: a rendszeren nincs elérhető MP4-kodek."
        )
    try:
        hold = settings.frames_per_photo - settings.transition_frames
        holds = [hold] * len(decoded)
        if settings.audio_option == 1 and audio_duration > 0:
            valtasi_kockak = max(0, len(decoded) - 1) * settings.transition_frames
            cel_kockaszam = round(audio_duration * settings.fps)
            osszes_tartas = max(len(decoded), cel_kockaszam - valtasi_kockak)
            alap_tartas, maradek = divmod(osszes_tartas, len(decoded))
            holds = [alap_tartas] * len(decoded)
            holds[-1] += maradek
        for index, (path, frame) in enumerate(decoded):
            if index and settings.transition_frames:
                previous = decoded[index - 1][1]
                for step in range(1, settings.transition_frames + 1):
                    weight = step / (settings.transition_frames + 1)
                    writer.write(_atmeneti_kocka(
                        previous, frame, settings.transition_type, weight
                    ))
                    frames_written += 1
            for _ in range(holds[index]):
                writer.write(frame)
                frames_written += 1
            if path is not None:
                used.append(path)
            if progress is not None:
                progress(index + 1, len(decoded))
    finally:
        writer.release()

    if settings.audio_path is not None:
        try:
            _hanggal_osszeilleszt(
                ffmpeg,
                video_target,
                Path(settings.audio_path),
                target,
                settings.audio_option,
            )
        finally:
            video_target.unlink(missing_ok=True)

    return MovieReport(
        target=target,
        used=tuple(used),
        skipped=tuple(skipped),
        missing=tuple(missing),
        reasons=tuple(reasons),
        frames=frames_written,
    )
