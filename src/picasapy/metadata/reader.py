"""EXIF/IPTC metaadat-olvasás (Pillow) — a rács dátum/felirat adataihoz.

Picasa-viselkedés: JPEG-nél a felirat és a kulcsszavak az IPTC-ben élnek
(nem a .picasa.ini-ben). Az olvasó soha nem dob: sérült vagy nem kép fájlra
EMPTY_METADATA-t ad — a szinkron nem bukhat el egyetlen rossz fájlon.

#134: ide tartozik a Pillow "decompression bomb" védelme is — egy irreálisan
nagy deklarált méretű (fejlécben meghamisított) fájl a `PIL.Image.open()`-t
DecompressionBombError-ral (vagy szigorú módban Warning-gal) buktatja, ezt is
el kell nyelni EMPTY_METADATA-ként. Az `Image.MAX_IMAGE_PIXELS` küszöbét
TUDATOSAN nem emeljük meg: a Pillow alapértéke (~178 megapixel) a valós
panorámaképeket (jellemzően összefűzött, de értelmes felbontású fájlok) még
átengedi, a támadó célú, irreálisan nagy deklarált méretű fájlokat viszont
kiszűri — a küszöb feltornázása épp ezt a védelmet venné el.
"""

from __future__ import annotations

import math
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.IptcImagePlugin import getiptcinfo

from .gps import gps_from_exif

_BOMB_EXCEPTIONS = (
    OSError,
    ValueError,
    SyntaxError,
    Image.DecompressionBombError,
    Image.DecompressionBombWarning,
)

_ORIENTATION_TAG = 274
_DATETIME_TAG = 306
_EXIF_IFD = 0x8769
_DATETIME_ORIGINAL_TAG = 36867
_MAKE_TAG = 271
_MODEL_TAG = 272
_EXPOSURE_TIME_TAG = 33434
_FNUMBER_TAG = 33437
_ISO_TAG = 34855
_FLASH_TAG = 37385
_FOCAL_LENGTH_TAG = 37386
_FOCAL_35MM_TAG = 41989  # FocalLengthIn35mmFilm (#235)
_WHITE_BALANCE_TAG = 41987
# #529: a `properties.xml` további látható mezői
_DATETIME_DIGITIZED_TAG = 36868
_LENS_MODEL_TAG = 42036
_SUBJECT_DISTANCE_TAG = 37382
_METERING_MODE_TAG = 37383
_EXPOSURE_PROGRAM_TAG = 34850
_COLOR_SPACE_TAG = 40961
_COMPRESSION_TAG = 259
_IMAGE_UNIQUE_ID_TAG = 42016
_GPS_IFD = 0x8825
_GPS_ALTITUDE_TAG = 6
_IPTC_KEYWORDS = (2, 25)
_IPTC_CAPTION = (2, 120)
_IPTC_CHARSET = (1, 90)
_UTF8_CHARSET_MARKER = b"\x1b%G"
_EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"


@dataclass(frozen=True)
class FileMetadata:
    """Fájlból olvasott metaadat.

    A width/height az orientáció ALKALMAZÁSA ELŐTTI (nyers) méret — 5–8-as
    orientációnál a megjelenítéshez a kettőt fel kell cserélni.
    """

    taken_at: str | None = None
    orientation: int = 1
    width: int | None = None
    height: int | None = None
    caption: str | None = None
    keywords: tuple[str, ...] = ()
    # #30: a fényképezőgép rögzítette hely (EXIF GPS-IFD), tizedes fokban;
    # None, ha a fájlban nincs (értelmes) GPS-adat
    latitude: float | None = None
    longitude: float | None = None


EMPTY_METADATA = FileMetadata()


def read_file_metadata(path: str | Path) -> FileMetadata:
    try:
        with warnings.catch_warnings():
            # A DecompressionBombWarning-t (a hard limit ALATTI, de gyanúsan
            # nagy méretnél) is hibaként kezeljük, hogy az except ág elkapja
            # — így a szigorú és a "csak figyelmeztet" Pillow-eset egyaránt
            # EMPTY_METADATA-t ad, sosem dob tovább.
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                exif = image.getexif()
                iptc = getiptcinfo(image) or {}
                width, height = image.size
                utf8_marked = _has_utf8_marker(iptc.get(_IPTC_CHARSET))
                point = gps_from_exif(exif)
                return FileMetadata(
                    taken_at=_taken_at(exif),
                    orientation=_orientation(exif),
                    width=width,
                    height=height,
                    caption=_decode(iptc.get(_IPTC_CAPTION), utf8_marked),
                    keywords=_keywords(iptc.get(_IPTC_KEYWORDS), utf8_marked),
                    latitude=point.latitude if point else None,
                    longitude=point.longitude if point else None,
                )
    except _BOMB_EXCEPTIONS:
        return EMPTY_METADATA


@dataclass(frozen=True)
class ExifDetails:
    """A Tulajdonságok-panel (#13) fényképezőgép-adatai — csak olvasás."""

    camera: str | None = None
    exposure_seconds: float | None = None
    f_number: float | None = None
    iso: int | None = None
    focal_mm: float | None = None
    focal_35mm: int | None = None  # 35 mm-egyenérték (#235)
    flash_fired: bool | None = None
    white_balance: str | None = None  # "auto" | "manual"
    # #529: a Picasa `runtime/properties.xml` további látható mezői. Az
    # ENUM-értékek a Picasa saját (angol) kulcsszavaival térnek vissza
    # (`Average`, `AperturePriority`, `sRGB`…) — a magyar feliratot a
    # `formatting.py` fordítja, a `Picasa3i18n.dll`-ből kinyert szótár
    # szerint (`referencia/exif-cimkek-en-hu.tsv`).
    make: str | None = None
    model: str | None = None
    datetime_original: str | None = None
    datetime_digitized: str | None = None
    datetime_modified: str | None = None
    orientation: int | None = None
    lens: str | None = None
    subject_distance_m: float | None = None
    metering_mode: str | None = None
    exposure_program: str | None = None
    color_space: str | None = None
    compression: str | None = None
    has_icc_profile: bool = False
    has_embedded_thumbnail: bool = False
    image_unique_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    altitude_m: float | None = None


EMPTY_EXIF_DETAILS = ExifDetails()


def read_exif_details(path: str | Path) -> ExifDetails:
    """Expozíciós EXIF-adatok igény szerinti olvasása (nem indexelt) —
    sérült/nem kép fájlra soha nem dob, EMPTY_EXIF_DETAILS-t ad."""
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(path) as image:
                exif = image.getexif()
                ifd = exif.get_ifd(_EXIF_IFD)
    except _BOMB_EXCEPTIONS:
        return EMPTY_EXIF_DETAILS
    flash = ifd.get(_FLASH_TAG)
    extra = _properties_extra(exif, ifd, path)
    white_balance = ifd.get(_WHITE_BALANCE_TAG)
    iso = ifd.get(_ISO_TAG)
    focal_35mm = ifd.get(_FOCAL_35MM_TAG)
    return ExifDetails(
        camera=_camera(exif.get(_MAKE_TAG), exif.get(_MODEL_TAG)),
        exposure_seconds=_rational(ifd.get(_EXPOSURE_TIME_TAG)),
        f_number=_rational(ifd.get(_FNUMBER_TAG)),
        iso=iso if isinstance(iso, int) else None,
        focal_mm=_rational(ifd.get(_FOCAL_LENGTH_TAG)),
        # a 0 értékű 35 mm-egyenérték a specben "ismeretlen"-t jelent
        focal_35mm=(
            focal_35mm
            if isinstance(focal_35mm, int) and focal_35mm > 0
            else None
        ),
        flash_fired=bool(flash & 1) if isinstance(flash, int) else None,
        white_balance=(
            {0: "auto", 1: "manual"}.get(white_balance)
            if isinstance(white_balance, int)
            else None
        ),
        **extra,
    )


#: EXIF-enumok → a Picasa saját (angol) kulcsszavai. A számértékek az
#: EXIF 2.3 szabványból, a kulcsszavak a `Picasa3i18n.dll`-ből kinyert
#: szótárból (#529) — a magyar felirat a `formatting.py`-ban készül.
_METERING_MODES = {
    0: "Unknown", 1: "Average", 2: "CenterWeight", 3: "Spot",
    4: "MultiSpot", 5: "Pattern", 6: "Partial", 255: "Other",
}
_EXPOSURE_PROGRAMS = {
    0: "NotDefined", 1: "Manual", 2: "NormalProgram", 3: "AperturePriority",
    4: "ShutterPriority", 5: "Creative", 6: "Action", 7: "Portrait",
    8: "Landscape",
}
_COLOR_SPACES = {1: "sRGB", 0xFFFF: "Uncalibrated"}
_COMPRESSIONS = {1: "Uncompressed", 6: "JPEG", 7: "JPEG", 8: "AdobeDeflate"}


def _properties_extra(exif, ifd, path: str | Path) -> dict:
    """A #529-es Tulajdonságok-panel többi mezője egyetlen szótárban.

    Külön függvény, hogy a `read_exif_details` törzse olvasható maradjon —
    a mezők túlnyomó része egyszerű címke-kiolvasás.
    """
    from PIL import Image as _Image

    def enum(value, table):
        return table.get(value) if isinstance(value, int) else None

    def text(value):
        value = value.strip() if isinstance(value, str) else ""
        return value or None

    point = gps_from_exif(exif)
    altitude = _rational(exif.get_ifd(_GPS_IFD).get(_GPS_ALTITUDE_TAG))
    icc = False
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", _Image.DecompressionBombWarning)
            with _Image.open(path) as image:
                icc = bool(image.info.get("icc_profile"))
    except _BOMB_EXCEPTIONS:
        pass
    # a beágyazott bélyegkép az EXIF 1. IFD-jében (thumbnail) él — a Pillow
    # ezt nem adja ki egyszerűen, a piexif (a projekt meglévő függősége) igen
    thumbnail = False
    try:
        import piexif

        thumbnail = piexif.load(str(path)).get("thumbnail") is not None
    except Exception:  # noqa: BLE001 — bármilyen hibás EXIF-re: "nincs bélyegkép"
        thumbnail = False
    return {
        "make": text(exif.get(_MAKE_TAG)),
        "model": text(exif.get(_MODEL_TAG)),
        "datetime_original": _exif_datetime(ifd.get(_DATETIME_ORIGINAL_TAG)),
        "datetime_digitized": _exif_datetime(ifd.get(_DATETIME_DIGITIZED_TAG)),
        "datetime_modified": _exif_datetime(exif.get(_DATETIME_TAG)),
        "orientation": (
            exif.get(_ORIENTATION_TAG)
            if isinstance(exif.get(_ORIENTATION_TAG), int)
            else None
        ),
        "lens": text(ifd.get(_LENS_MODEL_TAG)),
        "subject_distance_m": _rational(ifd.get(_SUBJECT_DISTANCE_TAG)),
        "metering_mode": enum(ifd.get(_METERING_MODE_TAG), _METERING_MODES),
        "exposure_program": enum(ifd.get(_EXPOSURE_PROGRAM_TAG), _EXPOSURE_PROGRAMS),
        "color_space": enum(ifd.get(_COLOR_SPACE_TAG), _COLOR_SPACES),
        "compression": enum(exif.get(_COMPRESSION_TAG), _COMPRESSIONS),
        "has_icc_profile": icc,
        "has_embedded_thumbnail": thumbnail,
        "image_unique_id": text(ifd.get(_IMAGE_UNIQUE_ID_TAG)),
        "latitude": point.latitude if point else None,
        "longitude": point.longitude if point else None,
        "altitude_m": altitude,
    }


def _exif_datetime(raw) -> str | None:
    """EXIF-dátum (`YYYY:MM:DD hh:mm:ss`) → ISO-szöveg; hibásra None."""
    if not isinstance(raw, str):
        return None
    try:
        return datetime.strptime(raw.strip(), _EXIF_DATE_FORMAT).isoformat()
    except ValueError:
        return None


# #429: a Picasa `.exe`-jéből előkerült, gyártói EXIF-szemetet takarító
# átírás — konkrétan csak ez az egy eset dokumentált (a binárisban a
# `histogram` rétegtípus natív kódja van, a további gyártói átírások nem
# derülnek ki innen; ÚJ bejegyzést csak bizonyított forrás alapján vegyünk fel).
_MAKE_NORMALIZATION = {"NIKON CORPORATION": "NIKON"}


def _camera(make, model) -> str | None:
    """`Gyártó Modell` — de sok gyártó a modellbe is beleírja a márkát,
    ilyenkor nem duplikálunk. A gyártónevet a Picasa-mintájú takarítás után
    (`_MAKE_NORMALIZATION`, #429) használjuk fel."""
    make = make.strip() if isinstance(make, str) else ""
    make = _MAKE_NORMALIZATION.get(make.upper(), make)
    model = model.strip() if isinstance(model, str) else ""
    if not model:
        return make or None
    if make and not model.lower().startswith(make.lower()):
        return f"{make} {model}"
    return model


def _rational(value) -> float | None:
    """EXIF-racionális (IFDRational/tuple/szám) → float; hibásra None.
    A 0 nevezőjű racionálist a Pillow NaN-ként adja — az is hibás."""
    try:
        result = float(value)
    except (TypeError, ValueError, ZeroDivisionError):
        return None
    return result if math.isfinite(result) else None


def _taken_at(exif: Image.Exif) -> str | None:
    raw = exif.get_ifd(_EXIF_IFD).get(_DATETIME_ORIGINAL_TAG) or exif.get(
        _DATETIME_TAG
    )
    if not isinstance(raw, str):
        return None
    try:
        return datetime.strptime(raw.strip(), _EXIF_DATE_FORMAT).isoformat()
    except ValueError:
        return None


def _orientation(exif: Image.Exif) -> int:
    value = exif.get(_ORIENTATION_TAG)
    return value if isinstance(value, int) and 1 <= value <= 8 else 1


def _has_utf8_marker(raw: bytes | list[bytes] | None) -> bool:
    """Az IPTC 1:90-es karakterkészlet-jelölő (a saját writerünk írja,
    #133) — ha jelen van és UTF-8-at jelöl, a szöveget megbízhatóan
    UTF-8-ként lehet dekódolni, heurisztika nélkül."""
    if raw is None:
        return False
    if isinstance(raw, list):
        raw = raw[0] if raw else b""
    return raw == _UTF8_CHARSET_MARKER


def _decode(raw: bytes | list[bytes] | None, utf8_marked: bool = False) -> str | None:
    """IPTC-szöveg dekódolása.

    Sorrend (#133): ha az 1:90-es jelölő UTF-8-at mond, azt hisszük el —
    ez a saját writerünk és a modern eszközök (digiKam, Lightroom) esete.
    Jelölő nélkül a legtöbb mai fájl akkor is UTF-8, ezért előbb azt
    próbáljuk; ha nem az, a régi (jellemzően magyar) Picasa-telepítések
    tipikus CP1250-es kódolására esik vissza a heurisztika; végső
    tartalékként a latin-1 mindig sikerül (byte-őrző, de mojibake-es).
    """
    if raw is None:
        return None
    if isinstance(raw, list):
        raw = raw[0]
    if utf8_marked:
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError:
            pass  # a jelölő ellenére sem UTF-8 — essünk vissza a heurisztikára
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        return raw.decode("cp1250")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _keywords(
    raw: bytes | list[bytes] | None, utf8_marked: bool = False
) -> tuple[str, ...]:
    if raw is None:
        return ()
    items = raw if isinstance(raw, list) else [raw]
    return tuple(
        decoded for item in items if (decoded := _decode(item, utf8_marked))
    )
