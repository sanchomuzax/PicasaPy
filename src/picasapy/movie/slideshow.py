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
from functools import lru_cache
import os
from pathlib import Path
import tempfile
from typing import NamedTuple

from picasapy.lazy_cv2 import cv2
import numpy as np
from PIL import ImageFont

from picasapy.cvimage import dekodolj_forrast
from picasapy.ini import IniDocument, load_or_empty, parse_faces
from picasapy.scanner import PICASA_INI_NAME

from .burst import capture_groups, hog_descriptor, select_chain
from .face_crop import face_is_usable, rect64_to_pixel_rect, render_face_crop
from . import slideshow_audio as _audio
from . import slideshow_frames as _frames
from . import slideshow_text as _text
from . import slideshow_transitions as _transitions

# A kodek-négyes: MP4 konténer, széles körben elérhető OpenCV-ben.
_FOURCC = "mp4v"

_TRANSITION_TYPES = frozenset(
    {
        "cut",
        "dissolve",
        "dissolveblack",
        "dissolvewhite",
        "wipeleft",
        "wiperight",
        "wipeup",
        "wipedown",
        "diagwipeul",
        "diagwipeur",
        "diagwipedl",
        "diagwipedr",
        "pushleft",
        "pushright",
        "pushtop",
        "pushdown",
        "circlein",
        "circleout",
        "kenburns",
        "kenburnsaoi",
        "timelapse",
        "rect",
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
    face_movie: bool = False
    ordering: int = 0
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
            raise ValueError(f"Érvénytelen képenkénti idő: {self.seconds_per_photo}")
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
    # Az arcfilmklipek pixeles forrás-rectjei, a `used` sorrendjében.
    used_face_rects: tuple[tuple[int, int, int, int] | None, ...] = ()


_DEFAULT_SETTINGS = MovieSettings()


def decode_photo(source: Path, goal: int | None = None) -> np.ndarray:
    """A slideshow fotódekódoló publikus belépője.

    A `goal` a preview célmérete; JPEG és RAW esetén a közös képdekóder
    kicsinyített olvasást választ, ha az elérhető.
    """
    if goal is None:
        return _decode(source)
    image = dekodolj_forrast(source, goal=goal)
    if image is None:
        raise ValueError(f"A kép nem dekódolható: {source}")
    return image


def transition_frame(
    outgoing: np.ndarray,
    incoming: np.ndarray,
    transition: str,
    progress: float,
) -> np.ndarray:
    """A kész film és az előnézet közös átmeneti képkockája."""
    return _atmeneti_kocka(outgoing, incoming, transition, progress)


@lru_cache(maxsize=256)
def _betu_utvonal(fontfajlok: tuple[str, ...]) -> str | None:
    """Az első betölthető betűfájl TELJES útvonala (vagy None: alapbetű).

    A fájlnév nélküli betűnév keresése a rendszer betűmappáit járja be, ami
    hideg gépen ~1 s; ezt a szerkesztés közben nem fizetjük újra (#4852).
    Futás közben telepített betű csak a program újraindítása után látszik."""
    for fontfajl in fontfajlok:
        try:
            return str(ImageFont.truetype(fontfajl, 10).path)
        except OSError:
            continue
    return None


def _betu_betoltese(fontfajlok: tuple[str, ...], meret: int):
    """A gyorsítótárazott útvonalról tölt; ha a fájl közben eltűnt, újrakeres."""
    for _ in range(2):
        utvonal = _betu_utvonal(fontfajlok)
        if utvonal is None:
            break
        try:
            return ImageFont.truetype(utvonal, meret)
        except OSError:
            _betu_utvonal.cache_clear()
    return ImageFont.load_default()


class _Vaszon(NamedTuple):
    """Csak a méret: a kis előnézeti vászon nem esik a páros/min. méret alá."""

    width: int
    height: int


def render_text_slide(
    slide: dict[str, object],
    settings: MovieSettings,
    size: tuple[int, int] | None = None,
) -> np.ndarray:
    """A film szöveges diájának publikus renderelője.

    `size` nélkül (export) a teljes filmméreten rajzol. `size`-zal (előnézet)
    közvetlenül az adott méretű vászonra rajzol, a betű/elrendezés arányosan
    skálázva, így nem kell a teljes méretet renderelni és kicsinyíteni."""
    if size is None or tuple(size) == (settings.width, settings.height):
        return _szovegdia(slide, settings)
    width, height = max(2, int(size[0])), max(2, int(size[1]))
    return _szovegdia(slide, _Vaszon(width, height), width / settings.width)


# A régi importútvonal és a tesztek monkeypatch-célpontjai változatlanok.
letterbox = _transitions.letterbox
crop_to_fit = _transitions.crop_to_fit
_atmenet_koordinatak = _transitions._atmenet_koordinatak
_ffmpeg_exe = _audio._ffmpeg_exe
_hang_hossza = _audio._hang_hossza
_hanggal_osszeilleszt = _audio._hanggal_osszeilleszt
_capture_timestamp = _frames._capture_timestamp


def _decode(source: Path) -> np.ndarray:
    return _transitions._decode(source)


def _atmeneti_kocka(kilepo: np.ndarray, erkezo: np.ndarray, tipus: str, arany: float) -> np.ndarray:
    return _transitions._atmeneti_kocka(
        kilepo, erkezo, tipus, arany, koordinatak=_atmenet_koordinatak
    )


def _szovegdia(
    slide: dict[str, object],
    settings: MovieSettings | _Vaszon,
    skala: float = 1.0,
    *,
    ido: float | None = None,
) -> np.ndarray:
    return _text.render_text_frame(slide, settings, skala, ido=ido, font_loader=_betu_betoltese)


def _picasa_caption(path: Path, documents: dict[Path, IniDocument | None]) -> str:
    return _frames.picasa_caption_core(
        path, documents, ini_name=PICASA_INI_NAME, loader=load_or_empty
    )


def _picasa_face_rectangles(
    path: Path,
    image: np.ndarray,
    documents: dict[Path, IniDocument | None],
) -> tuple[tuple[np.float32, np.float32, np.float32, np.float32], ...]:
    return _frames.picasa_face_rectangles_core(
        path,
        image,
        documents,
        ini_name=PICASA_INI_NAME,
        loader=load_or_empty,
        parse_faces_fn=parse_faces,
        rect64_to_pixel_rect_fn=rect64_to_pixel_rect,
    )


def _prepare_face_frame(
    path: Path,
    image: np.ndarray,
    rectangle: tuple[float, float, float, float],
    settings: MovieSettings,
    ini_docs: dict[Path, IniDocument | None],
) -> np.ndarray:
    return _frames.prepare_face_frame_core(
        path,
        image,
        rectangle,
        settings,
        ini_docs,
        render_face_crop_fn=render_face_crop,
        caption_fn=_picasa_caption,
        annotate_fn=_fotofelirat,
    )


def _fotofelirat(
    frame: np.ndarray, path: Path, settings: MovieSettings, picasa_caption: str = ""
) -> np.ndarray:
    return _frames.fotofelirat_core(frame, path, settings, picasa_caption)


def prepare_photo_frame(
    path: Path,
    settings: MovieSettings,
    ini_docs: dict[Path, IniDocument | None],
    *,
    decoder=None,
) -> np.ndarray:
    return _frames.prepare_photo_frame_core(
        path,
        settings,
        ini_docs,
        decoder=decoder or _decode,
        crop_to_fit_fn=crop_to_fit,
        letterbox_fn=letterbox,
        caption_fn=_picasa_caption,
        annotate_fn=_fotofelirat,
    )


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
    used_face_rects: list[tuple[int, int, int, int] | None] = []
    skipped: list[Path] = []
    reasons: list[str] = []
    missing: list[Path] = []
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)

    decoded: list[
        tuple[
            Path | None,
            np.ndarray,
            dict[str, object] | None,
            tuple[int, int, int, int] | None,
        ]
    ] = []
    capture_times: list[float | None] = []
    ini_documents: dict[Path, IniDocument | None] = {}
    for path in paths:
        if not path.exists():
            # #459/3: hiányzó fájl — a film a maradékkal elkészül
            missing.append(path)
            skipped.append(path)
            reasons.append("a fájl nem található")
            continue
        try:
            if settings.face_movie:
                image = _decode(path)
                rectangles = _picasa_face_rectangles(path, image, ini_documents)
                face_count = 0
                for rectangle in rectangles:
                    if not face_is_usable(
                        rectangle,
                        remove_low_res_faces=settings.remove_low_res_faces,
                    ):
                        continue
                    try:
                        frame = _prepare_face_frame(path, image, rectangle, settings, ini_documents)
                    except ValueError:
                        continue
                    pixel_rectangle = tuple(int(value) for value in rectangle)
                    decoded.append((path, frame, None, pixel_rectangle))
                    capture_times.append(_capture_timestamp(path))
                    face_count += 1
                if face_count:
                    continue
                skipped.append(path)
                reasons.append("a képen nincs a beállításnak megfelelő arc-téglalap")
                continue
            frame = prepare_photo_frame(path, settings, ini_documents)
        except (ValueError, OSError) as error:
            skipped.append(path)
            reasons.append(str(error))
            continue
        decoded.append((path, frame, None, None))
        capture_times.append(_capture_timestamp(path))

    text_frames = [
        (
            None,
            _szovegdia(
                slide,
                settings,
                ido=settings.frames_per_photo / settings.fps,
            ),
            slide,
            None,
        )
        for slide in settings.text_slides
    ]
    if settings.ordering == 2:
        decoded.sort(key=lambda entry: entry[0].stat().st_mtime if entry[0] else float("inf"))
    elif settings.ordering == 0 and len(decoded) > 1:
        # Az eredeti a felvételi idő szerint rendez (a tulajdonos 2026-10-19-i
        # exportja, #5386); ismeretlen idejű kép a végére kerül, sorrendtartóan.
        rend = sorted(
            range(len(decoded)),
            key=lambda i: (capture_times[i] is None, capture_times[i] or 0.0),
        )
        decoded = [decoded[i] for i in rend]
        capture_times = [capture_times[i] for i in rend]
    if settings.ordering == 0 and len(decoded) > 1 and settings.burstmodethresh > 0:
        groups = capture_groups(capture_times, settings.burstmodethresh)

        features: dict[int, np.ndarray] = {}

        def feature_for_index(index: int) -> np.ndarray:
            if index not in features:
                features[index] = hog_descriptor(decoded[index][1])
            return features[index]

        order = select_chain(
            groups,
            len(decoded),
            feature_for_index=feature_for_index,
        )
        decoded = [decoded[index] for index in order]
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
        raise RuntimeError("A videó nem hozható létre: a rendszeren nincs elérhető MP4-kodek.")
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
        for index, (path, frame, text_slide, face_rectangle) in enumerate(decoded):
            if index and settings.transition_frames:
                previous = decoded[index - 1][1]
                for step in range(1, settings.transition_frames + 1):
                    weight = step / (settings.transition_frames + 1)
                    incoming = (
                        _szovegdia(
                            text_slide,
                            settings,
                            ido=(step - 1) / settings.fps,
                        )
                        if text_slide is not None
                        else frame
                    )
                    writer.write(
                        _atmeneti_kocka(previous, incoming, settings.transition_type, weight)
                    )
                    frames_written += 1
            for local_frame in range(holds[index]):
                kocka = (
                    _szovegdia(
                        text_slide,
                        settings,
                        ido=(local_frame + (settings.transition_frames if index else 0))
                        / settings.fps,
                    )
                    if text_slide is not None
                    else frame
                )
                writer.write(kocka)
                frames_written += 1
            if path is not None:
                used.append(path)
                used_face_rects.append(face_rectangle)
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
        used_face_rects=tuple(used_face_rects),
    )
