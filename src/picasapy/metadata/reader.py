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
                return FileMetadata(
                    taken_at=_taken_at(exif),
                    orientation=_orientation(exif),
                    width=width,
                    height=height,
                    caption=_decode(iptc.get(_IPTC_CAPTION), utf8_marked),
                    keywords=_keywords(iptc.get(_IPTC_KEYWORDS), utf8_marked),
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
    )


def _camera(make, model) -> str | None:
    """`Gyártó Modell` — de sok gyártó a modellbe is beleírja a márkát,
    ilyenkor nem duplikálunk."""
    make = make.strip() if isinstance(make, str) else ""
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
