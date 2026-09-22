"""A Canon MakerNote `CameraSettings` (0x0001) tömbjének kiolvasása (#3121).

Az eredeti Picasa objektív-feloldója (`FUN_00a35a60`, spec
`picasa-metaadat-tulajdonsagok.md` 9.9) a gyártói MakerNote `0x0001`
bejegyzéséből dolgozik — ez a modul csak ezt az egy tömböt adja ki, a
számítás az `objektiv.py`-ban van.

A Canon MakerNote fejléc nélküli, szabványos TIFF-IFD, és az eltolásai a
TIFF-fejléchez (nem a MakerNote elejéhez) viszonyulnak — ezért kell a
TIFF-blokk egésze, nem csak a MakerNote bájtjai.

Sérült vagy csonka adatra soha nem dob: `None`.
"""

from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image

_EXIF_IFD_TAG = 0x8769
_MAKERNOTE_TAG = 0x927C
_CAMERA_SETTINGS_TAG = 0x0001
_SHORT = 3

#: A nyers (TIFF-alapú) fájlokból ennyit olvasunk be: a MakerNote a CR2-ben
#: az első néhány tíz kilobájton belül áll, a kép maga utána jön.
_NYERS_OLVASAS = 4 * 1024 * 1024
_EXIF_ELOTAG = b"Exif\x00\x00"


def tiff_blokk(path: str | Path) -> bytes | None:
    """A fájl EXIF TIFF-blokkja: JPEG-nél az APP1, TIFF-alapú nyers
    fájlnál (CR2) a fájl eleje."""
    try:
        with open(path, "rb") as fajl:
            if fajl.read(4) in (b"II*\x00", b"MM\x00*"):
                fajl.seek(0)
                return fajl.read(_NYERS_OLVASAS)
    except OSError:
        return None
    try:
        with Image.open(path) as kep:
            nyers = kep.info.get("exif")
    except Exception:  # noqa: BLE001 — bármilyen olvashatatlan kép: nincs blokk
        return None
    if not isinstance(nyers, bytes):
        return None
    return nyers[len(_EXIF_ELOTAG):] if nyers.startswith(_EXIF_ELOTAG) else nyers


def canon_camera_settings(tiff: bytes | None) -> tuple[int, ...] | None:
    """A `MakerNote 0x0001` SHORT-tömbje, vagy `None`."""
    if not tiff or len(tiff) < 8:
        return None
    rend = {b"II": "<", b"MM": ">"}.get(tiff[:2])
    if rend is None:
        return None
    try:
        (ifd0,) = struct.unpack_from(rend + "I", tiff, 4)
        exif = _bejegyzes(tiff, rend, ifd0, _EXIF_IFD_TAG)
        if exif is None:
            return None
        makernote = _bejegyzes(tiff, rend, _long(tiff, rend, exif), _MAKERNOTE_TAG)
        if makernote is None:
            return None
        beallitas = _bejegyzes(
            tiff, rend, _long(tiff, rend, makernote), _CAMERA_SETTINGS_TAG)
        if beallitas is None:
            return None
        return _short_tomb(tiff, rend, beallitas)
    except struct.error:
        return None


def _bejegyzes(tiff: bytes, rend: str, ifd: int, tag: int) -> int | None:
    """A `tag` bejegyzés 12 bájtos rekordjának eltolása az IFD-ben."""
    (darab,) = struct.unpack_from(rend + "H", tiff, ifd)
    for i in range(darab):
        hely = ifd + 2 + 12 * i
        (aktualis,) = struct.unpack_from(rend + "H", tiff, hely)
        if aktualis == tag:
            return hely
    return None


def _long(tiff: bytes, rend: str, bejegyzes: int) -> int:
    (ertek,) = struct.unpack_from(rend + "I", tiff, bejegyzes + 8)
    return ertek


def _short_tomb(tiff: bytes, rend: str, bejegyzes: int) -> tuple[int, ...] | None:
    tipus, darab = struct.unpack_from(rend + "HI", tiff, bejegyzes + 2)
    if tipus != _SHORT or darab == 0:
        return None
    hely = bejegyzes + 8 if darab <= 2 else _long(tiff, rend, bejegyzes)
    return struct.unpack_from(rend + f"{darab}H", tiff, hely)
