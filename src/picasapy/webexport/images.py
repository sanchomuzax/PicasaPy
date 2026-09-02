"""Bélyegkép/nagyméretű kép generálás a webexporthoz — a meglévő
`picasapy.export.exporter` infrastruktúrára építve (forgatás + `filters=`
lánc beégetése, WYSIWYG a rács/néző képével, ld. a modul docstringjét).

Fényképenként KÉT külön exportfutás történik (bélyegkép- és nagyméretű
célmappába) — ez képenként 1:1 megfelelést ad a forrás és a legenerált
fájl között, ami a `PhotoRecord` → `PhotoExportData` leképezéshez kell (az
`export_photos` kötegelt API-ja hibás elemnél "kicsúsztatná" a sorrendet)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from picasapy.cvimage import read_image_bytes
from picasapy.lazy_cv2 import cv2

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.index import PhotoRecord

from .context import PhotoExportData

logger = logging.getLogger(__name__)

_THUMBNAIL_SUBDIR = "thumbnail"
_IMAGE_SUBDIR = "image"


@dataclass(frozen=True)
class ImagePreparationReport:
    """A képgenerálás eredménye: sikeresen feldolgozott képek (a webexport
    hurokjaiban ebben a sorrendben szerepelnek) + a kihagyott — nem
    dekódolható vagy videó — forrásfájlok neve/oka."""

    photos: tuple[PhotoExportData, ...]
    skipped: tuple[str, ...]


def prepare_photo_exports(
    records: tuple[PhotoRecord, ...],
    target_dir: Path,
    settings,
) -> ImagePreparationReport:
    """A megadott `PhotoRecord`-okból bélyegkép + nagyméretű másolat
    készítése a `target_dir/thumbnail/` és `target_dir/image/` alá, és a
    webexport-motor számára kész `PhotoExportData` sor összeállítása.

    `settings`: `webexport.context.WebExportSettings` — csak a
    `thumbnail_max_dimension`/`image_max_dimension`/`jpeg_quality` mezőket
    használja. Videó típusú elemek (kind == "video") kihagyásra kerülnek
    (a webexport fényképgalériát generál, mozgóképet nem) — ld. a
    `WebExportReport.skipped` a hívási láncban."""
    thumb_dir = target_dir / _THUMBNAIL_SUBDIR
    image_dir = target_dir / _IMAGE_SUBDIR
    thumb_settings = ExportSettings(
        max_dimension=settings.thumbnail_max_dimension,
        jpeg_quality=settings.jpeg_quality,
    )
    image_settings = ExportSettings(
        max_dimension=settings.image_max_dimension,
        jpeg_quality=settings.jpeg_quality,
    )

    photos: list[PhotoExportData] = []
    skipped: list[str] = []
    for record in records:
        if record.kind == "video":
            skipped.append(f"{record.name}: videó — a webexport csak fényképet exportál")
            continue
        source = Path(record.folder_path) / record.name
        item = ExportItem(
            source=source, rotate_steps=record.rotate_steps, filters=record.filters
        )
        thumb_report = export_photos((item,), thumb_dir, thumb_settings)
        image_report = export_photos((item,), image_dir, image_settings)
        if not thumb_report.exported or not image_report.exported:
            reason = (thumb_report.reasons or image_report.reasons or ("ismeretlen hiba",))[0]
            skipped.append(f"{record.name}: {reason}")
            continue
        thumb_path = thumb_report.exported[0]
        image_path = image_report.exported[0]
        thumb_width, thumb_height = _image_size(thumb_path)
        large_width, large_height = _image_size(image_path)
        photos.append(
            PhotoExportData(
                name=record.name,
                caption=record.caption or "",
                original_width=record.width or large_width,
                original_height=record.height or large_height,
                size_bytes=record.size,
                thumbnail_rel_path=f"{_THUMBNAIL_SUBDIR}/{thumb_path.name}",
                thumbnail_width=thumb_width,
                thumbnail_height=thumb_height,
                large_rel_path=f"{_IMAGE_SUBDIR}/{image_path.name}",
                large_width=large_width,
                large_height=large_height,
            )
        )
    return ImagePreparationReport(photos=tuple(photos), skipped=tuple(skipped))


def _image_size(path: Path) -> tuple[int, int]:
    """A legenerált JPEG tényleges mérete (szélesség, magasság); (0, 0),
    ha a fájl valamiért mégsem dekódolható (nem szakítja meg az exportot,
    csak a méret-változók maradnak 0-n).

    #1991: BÁJT-alapon olvas. A `cv2.imread` fájlútvonalas alakja
    Windowson az ANSI kódlapon megy át, ezért ékezetes néven **némán**
    `None`-t ad (#65/#190) — és a felhasználó fényképeinek a neve
    rendszeresen ékezetes. A projekt négy másik modulja már így megy; ez
    a hely maradt ki.

    A (0, 0) visszatérés marad a szerződés (az export nem szakad meg), de
    NEM néma többé: naplózzuk, mert enélkül a felhasználó csak annyit
    látna, hogy a lapon nulla a képméret."""
    payload = read_image_bytes(path)
    image = (
        None if payload is None else cv2.imdecode(payload, cv2.IMREAD_COLOR)
    )
    if image is None:
        logger.warning(
            "A webexport nem tudta beolvasni a kép méretét: %s "
            "(a lapon nulla méret marad)",
            path,
        )
        return (0, 0)
    height, width = image.shape[:2]
    return (width, height)
