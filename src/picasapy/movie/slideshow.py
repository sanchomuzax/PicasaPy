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
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.cvimage import read_image_bytes

# A kodek-négyes: MP4 konténer, széles körben elérhető OpenCV-ben.
_FOURCC = "mp4v"


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


def _decode(source: Path) -> np.ndarray:
    payload = read_image_bytes(source)
    if payload is None:
        raise ValueError("üres vagy nem olvasható fájl")
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("nem dekódolható kép")
    return image


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

    decoded: list[tuple[Path, np.ndarray]] = []
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
        decoded.append(
            (path, letterbox(image, settings.width, settings.height, settings.background))
        )

    if not decoded:
        return MovieReport(
            target=target,
            used=(),
            skipped=tuple(skipped),
            reasons=tuple(reasons),
            frames=0,
            missing=tuple(missing),
        )

    writer = cv2.VideoWriter(
        str(target),
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
        for index, (path, frame) in enumerate(decoded):
            if index and settings.transition_frames:
                previous = decoded[index - 1][1]
                for step in range(1, settings.transition_frames + 1):
                    weight = step / (settings.transition_frames + 1)
                    writer.write(
                        cv2.addWeighted(previous, 1.0 - weight, frame, weight, 0.0)
                    )
                    frames_written += 1
            for _ in range(hold):
                writer.write(frame)
                frames_written += 1
            used.append(path)
            if progress is not None:
                progress(len(used), len(decoded))
    finally:
        writer.release()

    return MovieReport(
        target=target,
        used=tuple(used),
        skipped=tuple(skipped),
        missing=tuple(missing),
        reasons=tuple(reasons),
        frames=frames_written,
    )
