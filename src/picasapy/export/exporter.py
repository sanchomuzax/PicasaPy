"""Kijelölt képek exportja célmappába (Ctrl+Shift+S) — issue #16.

A render-motor (V2) előtti első kör: a forgatás (rotate_steps) beleégetése
és opcionális átméretezés OpenCV-vel, állítható JPEG-minőséggel. A videók
bitre pontos másolással kerülnek át. Az UI-bekötés az integrátor lépése.
"""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from picasapy.ioutil import write_atomic
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS

_ROTATIONS = {
    1: cv2.ROTATE_90_CLOCKWISE,
    2: cv2.ROTATE_180,
    3: cv2.ROTATE_90_COUNTERCLOCKWISE,
}


@dataclass(frozen=True)
class ExportSettings:
    """Export-beállítások: leghosszabb oldal (None = eredeti) és JPEG-minőség."""

    max_dimension: int | None = None
    jpeg_quality: int = 85

    def __post_init__(self) -> None:
        if self.max_dimension is not None and self.max_dimension < 1:
            raise ValueError(f"Érvénytelen max_dimension: {self.max_dimension}")
        if not 1 <= self.jpeg_quality <= 100:
            raise ValueError(f"Érvénytelen jpeg_quality: {self.jpeg_quality}")


@dataclass(frozen=True)
class ExportItem:
    """Egy exportálandó elem: forrásfájl + beégetendő forgatás (90°-os lépések)."""

    source: Path
    rotate_steps: int = 0


@dataclass(frozen=True)
class ExportReport:
    """Az exportfutás eredménye: kész célfájlok és sikertelen források."""

    exported: tuple[Path, ...]
    failed: tuple[Path, ...]


def export_photos(
    items: Iterable[ExportItem],
    target_dir: Path,
    settings: ExportSettings = ExportSettings(),
) -> ExportReport:
    """Elemek exportja a célmappába; egy elem hibája nem állítja le a többit."""
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    exported: list[Path] = []
    failed: list[Path] = []
    for item in items:
        source = Path(item.source)
        try:
            exported.append(_export_one(source, item.rotate_steps, target_dir, settings))
        except (OSError, ValueError, cv2.error):
            failed.append(source)
    return ExportReport(exported=tuple(exported), failed=tuple(failed))


def _export_one(
    source: Path, rotate_steps: int, target_dir: Path, settings: ExportSettings
) -> Path:
    if source.suffix.lower() in VIDEO_EXTENSIONS:
        target = _unique_target(target_dir, source.stem, source.suffix)
        shutil.copyfile(source, target)
        return target
    image = _decode_image(source)
    image = _apply_rotation(image, rotate_steps)
    image = _scale_down(image, settings.max_dimension)
    ok, encoded = cv2.imencode(
        ".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, settings.jpeg_quality]
    )
    if not ok:
        raise ValueError(f"JPEG-kódolás sikertelen: {source}")
    target = _unique_target(target_dir, source.stem, ".jpg")
    # Közös helper (#129): fsync + atomikus csere — félkész célfájl sose
    # maradjon (NAS/tele lemez).
    write_atomic(target, encoded.tobytes())
    return target


def _decode_image(source: Path) -> np.ndarray:
    """Bájt-alapú dekódolás a cv2.imread helyett (#65 tanulság: az imread
    Windowson ékezetes útvonalon némán None-t ad). EXIF-forgatással dekódol."""
    payload = np.fromfile(source, dtype=np.uint8)
    if payload.size == 0:
        raise ValueError(f"Üres forrásfájl: {source}")
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Nem dekódolható kép: {source}")
    return image


def _apply_rotation(image: np.ndarray, rotate_steps: int) -> np.ndarray:
    """90°-os órairányú lépések beégetése (a Picasa/Qt konvenciója szerint)."""
    steps = rotate_steps % 4
    if steps == 0:
        return image
    return cv2.rotate(image, _ROTATIONS[steps])


def _scale_down(image: np.ndarray, max_dimension: int | None) -> np.ndarray:
    """A leghosszabb oldal korlátozása; felskálázás soha nincs."""
    if max_dimension is None:
        return image
    height, width = image.shape[:2]
    longest = max(width, height)
    if longest <= max_dimension:
        return image
    scale = max_dimension / longest
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)


def _unique_target(target_dir: Path, stem: str, suffix: str) -> Path:
    """Ütközésmentes célnév: `név.jpg`, `név-1.jpg`, `név-2.jpg`, ..."""
    candidate = target_dir / f"{stem}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = target_dir / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate
