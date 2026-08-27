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


def record_point(record) -> tuple[float, float] | None:
    """A rekord koordinátája — az `.picasa.ini` `geotag=` ÉS az EXIF GPS.

    ⚠️ #1589: ez korábban KÖZVETLENÜL az `exif_lat`/`exif_lon` mezőket
    olvasta, azaz kizárólag a fényképezőgép rögzítette helyet. A PicasaPy
    SAJÁT geocímkéje viszont az ini `geotag=` kulcsába kerül
    (`geo_controller.setGeotagRows`), és azt a `PhotoRecord.location`
    oldja fel. Következmény: aki a PicasaPy-ban címkézte meg a képeit,
    ÜRES exportot kapott — a menüpont lefutott, fájl nem készült, és a
    jelentés „egyetlen képnek sincs helye"-t mondott. A `location`
    ugyanezt a sorrendet adja, mint a felület többi pontja (ini > EXIF),
    tehát ettől a térkép és a rács geo-jelvényei sem térhetnek el.

    A `location` tulajdonságot nem követeljük meg: a duck-typed
    teszt-rekordoknak (és bármely egyszerűbb hívónak) elég az
    `exif_lat`/`exif_lon` pár.
    """
    point = getattr(record, "location", None)
    if point is not None:
        return float(point.latitude), float(point.longitude)
    latitude = getattr(record, "exif_lat", None)
    longitude = getattr(record, "exif_lon", None)
    if latitude is None or longitude is None:
        return None
    return float(latitude), float(longitude)


def record_path(record) -> Path:
    """A rekord fájlútvonala — `PhotoRecord`-ból is, `path`-osból is.

    ⚠️ #1589: az export korábban KIZÁRÓLAG a `record.path` mezőt olvasta,
    a valódi `PhotoRecord`-nak viszont nincs ilyen mezője (`folder_path` +
    `name` van). A #530 tesztjei duck-typed rekorddal dolgoztak, ezért a
    hiány zölden átcsúszott — a FUTÓ alkalmazásban viszont a háttérszál
    `AttributeError`-rel elhasalt, és a felhasználó egy soha véget nem
    érő exportot nézett. Ez a segéd mindkét alakot elfogadja.
    """
    utvonal = getattr(record, "path", None)
    if utvonal:
        return Path(utvonal)
    return Path(record.folder_path) / record.name


def _placemark_name(record) -> str:
    """Az eredeti `%CAPTION_OR_NAME%`: felirat, annak híján a fájlnév."""
    caption = (getattr(record, "caption", None) or "").strip()
    if caption:
        return caption
    return record_path(record).name


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

    A `records` a szokásos `PhotoRecord`-ok (kell: `path` és egy koordináta
    — `location` vagy `exif_lat`/`exif_lon`, ld. `record_point`;
    opcionálisan `caption`, `taken_at`). A `target_dir` alá kerül a
    `doc.kml` és a `thumbs/` alkönyvtár.

    Egyetlen geocímkézett kép nélkül **nem ír fájlt** — üres térképet
    exportálni félrevezető lenne; a hívó a jelentésből tudja, mi történt.
    """
    with_point = [(r, record_point(r)) for r in records]
    geotagged = [(r, p) for r, p in with_point if p is not None]
    skipped = len(with_point) - len(geotagged)
    if not geotagged:
        return EarthExportReport(
            kml_path=None, placemarks=0, skipped_without_location=skipped
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    thumbs_dir = target_dir / THUMBS_DIR_NAME
    report = export_photos(
        (ExportItem(source=record_path(r)) for r, _ in geotagged),
        thumbs_dir,
        ExportSettings(max_dimension=thumb_max_dimension),
    )
    # a kiírt bélyegképek forrás szerint — a sikertelenek kimaradnak
    by_name = {p.name: p for p in report.exported}

    placemarks: list[KmlPlacemark] = []
    for index, (record, point) in enumerate(geotagged):
        source = record_path(record)
        thumb = by_name.get(source.name)
        if thumb is None:
            continue
        width, height = _thumb_size(thumb)
        relative = f"{THUMBS_DIR_NAME}/{thumb.name}"
        placemarks.append(
            KmlPlacemark(
                uid=str(index),
                latitude=point[0],
                longitude=point[1],
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
    "record_path",
    "record_point",
]
