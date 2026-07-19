"""EXIF/IPTC metaadat-olvasás (Pillow) — a rács dátum/felirat adataihoz.

Picasa-viselkedés: JPEG-nél a felirat és a kulcsszavak az IPTC-ben élnek
(nem a .picasa.ini-ben). Az olvasó soha nem dob: sérült vagy nem kép fájlra
EMPTY_METADATA-t ad — a szinkron nem bukhat el egyetlen rossz fájlon.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.IptcImagePlugin import getiptcinfo

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
_WHITE_BALANCE_TAG = 41987
_IPTC_KEYWORDS = (2, 25)
_IPTC_CAPTION = (2, 120)
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
        with Image.open(path) as image:
            exif = image.getexif()
            iptc = getiptcinfo(image) or {}
            width, height = image.size
            return FileMetadata(
                taken_at=_taken_at(exif),
                orientation=_orientation(exif),
                width=width,
                height=height,
                caption=_decode(iptc.get(_IPTC_CAPTION)),
                keywords=_keywords(iptc.get(_IPTC_KEYWORDS)),
            )
    except (OSError, ValueError, SyntaxError):
        return EMPTY_METADATA


@dataclass(frozen=True)
class ExifDetails:
    """A Tulajdonságok-panel (#13) fényképezőgép-adatai — csak olvasás."""

    camera: str | None = None
    exposure_seconds: float | None = None
    f_number: float | None = None
    iso: int | None = None
    focal_mm: float | None = None
    flash_fired: bool | None = None
    white_balance: str | None = None  # "auto" | "manual"


EMPTY_EXIF_DETAILS = ExifDetails()


def read_exif_details(path: str | Path) -> ExifDetails:
    """Expozíciós EXIF-adatok igény szerinti olvasása (nem indexelt) —
    sérült/nem kép fájlra soha nem dob, EMPTY_EXIF_DETAILS-t ad."""
    try:
        with Image.open(path) as image:
            exif = image.getexif()
            ifd = exif.get_ifd(_EXIF_IFD)
    except (OSError, ValueError, SyntaxError):
        return EMPTY_EXIF_DETAILS
    flash = ifd.get(_FLASH_TAG)
    white_balance = ifd.get(_WHITE_BALANCE_TAG)
    iso = ifd.get(_ISO_TAG)
    return ExifDetails(
        camera=_camera(exif.get(_MAKE_TAG), exif.get(_MODEL_TAG)),
        exposure_seconds=_rational(ifd.get(_EXPOSURE_TIME_TAG)),
        f_number=_rational(ifd.get(_FNUMBER_TAG)),
        iso=iso if isinstance(iso, int) else None,
        focal_mm=_rational(ifd.get(_FOCAL_LENGTH_TAG)),
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


def _decode(raw: bytes | list[bytes] | None) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        raw = raw[0]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1")


def _keywords(raw: bytes | list[bytes] | None) -> tuple[str, ...]:
    if raw is None:
        return ()
    items = raw if isinstance(raw, list) else [raw]
    return tuple(decoded for item in items if (decoded := _decode(item)))
