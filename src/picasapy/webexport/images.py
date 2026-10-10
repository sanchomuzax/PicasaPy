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

from picasapy.cvimage import dekodolj_forrast

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
    dekódolható — forrásfájlok neve/oka."""

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

    `settings`: `webexport.context.WebExportSettings` — a
    `thumbnail_max_dimension`/`image_max_dimension`/`jpeg_quality`/
    `movie_full` mezőket használja.

    #4610 (spec `picasa-menu-parancsok-viselkedes.md` 6.1): a film a
    mozgókép-mód szerint kerül a galériába. „Első képkocka": a film első
    kockája állóképként, mint egy fénykép. „Teljes mozgófilm": a bélyegkép
    az első kocka, a nagy kép maga a film bájthű másolata. Olvashatatlan
    filmnél nincs mit a galériába tenni — a tétel okkal kimarad."""
    thumb_settings = ExportSettings(
        max_dimension=settings.thumbnail_max_dimension,
        jpeg_quality=settings.jpeg_quality,
        movie_full=False,
    )
    image_settings = ExportSettings(
        max_dimension=settings.image_max_dimension,
        jpeg_quality=settings.jpeg_quality,
        movie_full=bool(getattr(settings, "movie_full", False)),
    )
    dirs = (target_dir / _THUMBNAIL_SUBDIR, target_dir / _IMAGE_SUBDIR)

    photos: list[PhotoExportData] = []
    skipped: list[str] = []
    for record in records:
        result = _export_record(record, dirs, thumb_settings, image_settings)
        if isinstance(result, str):
            skipped.append(f"{record.name}: {result}")
        else:
            photos.append(result)
    return ImagePreparationReport(photos=tuple(photos), skipped=tuple(skipped))


def _export_record(
    record: PhotoRecord,
    dirs: tuple[Path, Path],
    thumb_settings: ExportSettings,
    image_settings: ExportSettings,
) -> PhotoExportData | str:
    """Egy tétel bélyegképe és nagy képe; hiba esetén az ok szövege."""
    thumb_dir, image_dir = dirs
    is_video = record.kind == "video"
    item = ExportItem(
        source=Path(record.folder_path) / record.name,
        rotate_steps=record.rotate_steps,
        flip_flags=getattr(record, "flip_flags", 0),  # #2902
        filters=record.filters,
        taken_at_override=getattr(record, "taken_at_override", None),
    )
    thumb_report = export_photos((item,), thumb_dir, thumb_settings)
    image_report = export_photos((item,), image_dir, image_settings)
    if not thumb_report.exported or not image_report.exported:
        return (thumb_report.reasons or image_report.reasons or ("ismeretlen hiba",))[0]
    thumb_path = thumb_report.exported[0]
    image_path = image_report.exported[0]
    movie_embed = is_video and image_settings.movie_full
    if is_video and not _is_still(thumb_path, image_path, movie_embed):
        # az exportáló olvashatatlan kockánál a filmet másolja a JPEG
        # helyett — a galériába ebből nem lesz kép
        _discard(thumb_path, image_path)
        return "a videó első képkockája nem olvasható"
    thumb_width, thumb_height = _image_size(thumb_path)
    if movie_embed:
        large_width, large_height = _movie_size(record, item.source)
    else:
        large_width, large_height = _image_size(image_path)
    return PhotoExportData(
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
        movie_embed=movie_embed,
    )


def _movie_size(record: PhotoRecord, source: Path) -> tuple[int, int]:
    """A film mérete a lejátszóhoz. Az index videóra nem tölt méretet
    (`index/sync.py` EMPTY_METADATA), ezért hiányában az első kockából
    olvassuk — az elszigetelt dekóderen át, mint a bélyegképnél. (0, 0),
    ha az sem olvasható; a sablon ilyenkor nem ír méret-attribútumot."""
    if record.width and record.height:
        return record.width, record.height
    from picasapy.export.exporter import _first_frame

    frame = _first_frame(source)
    if frame is None:
        return (0, 0)
    height, width = frame.shape[:2]
    return (width, height)


def _is_still(thumb_path: Path, image_path: Path, movie_embed: bool) -> bool:
    """A film kimenete használható-e: a bélyegkép JPEG kocka, és — első
    kockás módban — a nagy kép is az."""
    if thumb_path.suffix.lower() != ".jpg":
        return False
    return movie_embed or image_path.suffix.lower() == ".jpg"


def _discard(*paths: Path) -> None:
    """A kimaradó tétel félkész kimenetének eltávolítása."""
    for path in paths:
        try:
            path.unlink(missing_ok=True)
        except OSError as error:
            logger.warning("A webexport nem tudta törölni: %s (%s)", path, error)


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
    #: #3120: a KÖZÖS belépőn megy — a `cv2.imdecode`-nak nincs nyers
    #: dekódere, tehát a RAW fájlok mérete nulla maradt a lapon.
    image = dekodolj_forrast(path)
    if image is None:
        logger.warning(
            "A webexport nem tudta beolvasni a kép méretét: %s "
            "(a lapon nulla méret marad)",
            path,
        )
        return (0, 0)
    height, width = image.shape[:2]
    return (width, height)
