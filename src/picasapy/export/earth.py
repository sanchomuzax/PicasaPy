"""Google Earth-export: KML + bélyegképek kiírása (#530).

A `kml.py` a dokumentumot építi; ez a modul köti össze a képekkel: kiválogatja
a geocímkézett fotókat, bélyegképet készít melléjük (a meglévő export-
csővezetéken át), és kiírja a `.kml`-t.

**Csak a geocímkézett képek kerülnek bele.** Koordináta nélkül nincs mit a
térképre tenni; a kihagyottak számát a jelentés visszaadja, hogy a hívó meg
tudja mondani a felhasználónak, miért kevesebb a helyjelző, mint a kijelölés.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from picasapy.export.exporter import ExportItem, ExportSettings, export_photos
from picasapy.export.kml import DEFAULT_LOOK_AT_RANGE_M, KmlPlacemark, build_kml

#: A buborékban megjelenő bélyegkép leghosszabb oldala. Az eredeti buborék
#: 400 képpont széles táblázatot használ, ezért ennél nagyobb kép fölösleges.
THUMB_MAX_DIMENSION = 400

#: A bélyegképek alkönyvtára a `.kml` mellett — a KML-ben relatív hivatkozás.
THUMBS_DIR_NAME = "thumbs"

#: A kiírt dokumentum neve.
KML_FILE_NAME = "doc.kml"


@dataclass(frozen=True)
class EarthExportReport:
    """Az export eredménye."""

    #: a kiírt KML útvonala (None, ha egyetlen geocímkézett kép sem volt)
    kml_path: Path | None
    #: hány kép került a térképre
    placemarks: int
    #: hány képet hagytunk ki koordináta híján
    skipped_without_location: int
    #: a bélyegkép-készítés során meghiúsult források
    failed: tuple[Path, ...] = ()


def _thumb_size(path: Path) -> tuple[int, int]:
    """A kiírt bélyegkép tényleges mérete — a buborék HTML-jéhez kell.

    Olvashatatlan fájlnál (0, 0): a méret elhagyható attribútum, a kép attól
    még megjelenik."""
    try:
        with Image.open(path) as kep:
            return int(kep.width), int(kep.height)
    except (OSError, ValueError):
        return (0, 0)


def _placemark_name(record) -> str:
    """Az eredeti `%CAPTION_OR_NAME%`: felirat, annak híján a fájlnév."""
    caption = (getattr(record, "caption", None) or "").strip()
    if caption:
        return caption
    return Path(record.path).name


def export_google_earth(
    records,
    target_dir: Path,
    *,
    folder_name: str,
    generated: str = "",
    thumb_max_dimension: int = THUMB_MAX_DIMENSION,
    look_at_range_m: float = DEFAULT_LOOK_AT_RANGE_M,
) -> EarthExportReport:
    """A geocímkézett képek kiírása Google Earth-höz.

    A `records` a szokásos `PhotoRecord`-ok (kell: `path`, `exif_lat`,
    `exif_lon`, opcionálisan `caption`, `taken_at`). A `target_dir` alá kerül
    a `doc.kml` és a `thumbs/` alkönyvtár.

    Egyetlen geocímkézett kép nélkül **nem ír fájlt** — üres térképet
    exportálni félrevezető lenne; a hívó a jelentésből tudja, mi történt.
    """
    geotagged = [
        r
        for r in records
        if getattr(r, "exif_lat", None) is not None
        and getattr(r, "exif_lon", None) is not None
    ]
    skipped = len(list(records)) - len(geotagged)
    if not geotagged:
        return EarthExportReport(
            kml_path=None, placemarks=0, skipped_without_location=skipped
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir = target_dir / THUMBS_DIR_NAME
    report = export_photos(
        (ExportItem(source=Path(r.path)) for r in geotagged),
        thumbs_dir,
        ExportSettings(max_dimension=thumb_max_dimension),
    )
    # a kiírt bélyegképek forrás szerint — a sikertelenek kimaradnak
    by_name = {p.name: p for p in report.exported}

    placemarks: list[KmlPlacemark] = []
    for index, record in enumerate(geotagged):
        source = Path(record.path)
        thumb = by_name.get(source.name)
        if thumb is None:
            continue
        width, height = _thumb_size(thumb)
        relative = f"{THUMBS_DIR_NAME}/{thumb.name}"
        placemarks.append(
            KmlPlacemark(
                uid=str(index),
                latitude=float(record.exif_lat),
                longitude=float(record.exif_lon),
                name=_placemark_name(record),
                caption=(getattr(record, "caption", None) or ""),
                icon_href=relative,
                thumb_href=relative,
                thumb_width=width,
                thumb_height=height,
                file_date=(getattr(record, "taken_at", None) or ""),
            )
        )

    kml_path = target_dir / KML_FILE_NAME
    kml_path.write_text(
        build_kml(
            tuple(placemarks),
            folder_name=folder_name,
            generated=generated,
            look_at_range_m=look_at_range_m,
        ),
        encoding="utf-8",
    )
    return EarthExportReport(
        kml_path=kml_path,
        placemarks=len(placemarks),
        skipped_without_location=skipped,
        failed=report.failed,
    )


__all__ = [
    "KML_FILE_NAME",
    "THUMBS_DIR_NAME",
    "THUMB_MAX_DIMENSION",
    "EarthExportReport",
    "export_google_earth",
]
