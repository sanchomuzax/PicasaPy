"""EXIF/IPTC metaadat-olvasás (Pillow) — a rács dátum/felirat adataihoz.

Picasa-viselkedés: JPEG-nél a felirat és a kulcsszavak az IPTC-ben élnek
(nem a .picasa.ini-ben). Az olvasó soha nem dob: sérült vagy nem kép fájlra
EMPTY_METADATA-t ad — a szinkron nem bukhat el egyetlen rossz fájlon.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PIL import Image
from PIL.IptcImagePlugin import getiptcinfo

_ORIENTATION_TAG = 274
_DATETIME_TAG = 306
_EXIF_IFD = 0x8769
_DATETIME_ORIGINAL_TAG = 36867
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
