"""A gyártói MakerNote objektív-mezőinek kiolvasása: Canon (#3121), Nikon (#3495).

Az eredeti Picasa objektív-feloldója (`FUN_00a35a60`, spec
`picasa-metaadat-tulajdonsagok.md` 9.9) a gyártói MakerNote `0x0001`
bejegyzéséből, a Nikon-ág (9.13) a `0x0083`/`0x0098` mezőkből dolgozik — ez a
modul csak a nyers mezőket adja ki, a számítás az `objektiv.py`-ban van.

A Canon MakerNote fejléc nélküli, szabványos TIFF-IFD, és az eltolásai a
TIFF-fejléchez (nem a MakerNote elejéhez) viszonyulnak — ezért kell a
TIFF-blokk egésze, nem csak a MakerNote bájtjai.

A Nikon MakerNote (a D100-tól) `Nikon\\0\\x02` fejléccel kezdődik, utána
SAJÁT TIFF-fejléc jön (bájtsorrenddel), és az eltolásai ehhez viszonyulnak
(`nikon_objektiv_mezok`). A fejléc nélküli és az 1-es típusú (régi Coolpix)
MakerNote-ban nincs `LensData` — ott nincs mit kiolvasni.

Sérült vagy csonka adatra soha nem dob: `None`.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

_EXIF_IFD_TAG = 0x8769
_MAKERNOTE_TAG = 0x927C
_CAMERA_SETTINGS_TAG = 0x0001
_BYTE = 1
_ASCII = 2
_SHORT = 3
_LONG = 4
_UNDEFINED = 7

#: A Nikon MakerNote-mezők (az exiftool `Nikon::Main` táblája szerint).
_NIKON_FEJLEC = b"Nikon\x00\x02"
_NIKON_TIFF_ELTOLAS = 10
_NIKON_SOROZATSZAM = 0x001D
_NIKON_LENS_TYPE = 0x0083
_NIKON_LENS_DATA = 0x0098
_NIKON_ZARSZAMLALO = 0x00A7

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


@dataclass(frozen=True)
class NikonObjektivMezok:
    """A Nikon-ág (spec 9.13) bemenete a MakerNote-ból; a hiányzó mező `None`."""

    lens_type: int | None
    lens_data: bytes | None
    sorozatszam: str | None
    zarszamlalo: int | None


def nikon_objektiv_mezok(tiff: bytes | None) -> NikonObjektivMezok | None:
    """A Nikon MakerNote `LensType`, `LensData`, `SerialNumber` és
    `ShutterCount` mezője, vagy `None`, ha nincs `Nikon\\0\\x02` MakerNote."""
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
        (darab,) = struct.unpack_from(rend + "I", tiff, makernote + 4)
        if darab <= 4:
            return None
        hely = _long(tiff, rend, makernote)
        mn = tiff[hely:hely + darab]
    except struct.error:
        return None
    if not mn.startswith(_NIKON_FEJLEC):
        return None
    belso = mn[_NIKON_TIFF_ELTOLAS:]
    belso_rend = {b"II": "<", b"MM": ">"}.get(belso[:2])
    if belso_rend is None:
        return None
    try:
        (ifd,) = struct.unpack_from(belso_rend + "I", belso, 4)
        struct.unpack_from(belso_rend + "H", belso, ifd)
    except struct.error:
        return None

    def mezo(tag: int, tipusok: tuple[int, ...]) -> bytes | None:
        try:
            bejegyzes = _bejegyzes(belso, belso_rend, ifd, tag)
            if bejegyzes is None:
                return None
            return _nyers_ertek(belso, belso_rend, bejegyzes, tipusok)
        except struct.error:
            return None

    lens_type = mezo(_NIKON_LENS_TYPE, (_BYTE, _UNDEFINED))
    sorozat = mezo(_NIKON_SOROZATSZAM, (_ASCII,))
    zar = mezo(_NIKON_ZARSZAMLALO, (_LONG,))
    return NikonObjektivMezok(
        lens_type=lens_type[0] if lens_type else None,
        lens_data=mezo(_NIKON_LENS_DATA, (_UNDEFINED, _BYTE)),
        sorozatszam=(
            sorozat.split(b"\x00", 1)[0].decode("latin-1").strip()
            if sorozat is not None else None),
        zarszamlalo=(
            struct.unpack(belso_rend + "I", zar[:4])[0]
            if zar is not None and len(zar) >= 4 else None),
    )


def _nyers_ertek(
    tiff: bytes, rend: str, bejegyzes: int, tipusok: tuple[int, ...]
) -> bytes | None:
    """Egy bájt-, szöveg- vagy LONG-bejegyzés nyers bájtjai (csonkán `None`)."""
    tipus, darab = struct.unpack_from(rend + "HI", tiff, bejegyzes + 2)
    if tipus not in tipusok or darab == 0:
        return None
    meret = darab * (4 if tipus == _LONG else 1)
    hely = bejegyzes + 8 if meret <= 4 else _long(tiff, rend, bejegyzes)
    ertek = tiff[hely:hely + meret]
    return ertek if len(ertek) == meret else None
