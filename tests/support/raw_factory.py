"""Közös teszt-fixture: **valódi**, apró CFA DNG előállítása (#528).

⛔ **Miért generálunk, és nem tárolunk mintát.** A kamerák nyers fájljai
tízmegabájtosak (a jegy Leica-mintája 9,9 MB) — a repóba nem tehetők, a
`nagy_fajl_or.py` sem engedné. Egy tömörítetlen CFA DNG viszont a TIFF
szerkezetére épül, tehát **kézzel összeírható**, és 6,5 KB-ból elég valódi
ahhoz, hogy a LibRaw tényleg dekódolja.

⚠️ **Amit ez a minta NEM mér.** Nem kameragyártmány: nincs benne MakerNote,
nincs beágyazott JPEG-előnézet, és a színmátrixa kitalált. Tehát
**színhelyességet vagy gyártóspecifikus viselkedést NE mérj vele** — arra a
jegyben nevesített Leica-minta való (`referencia/i18n`-nel egy szinten, a
privát repó képleltárában). Ez a fixture azt méri, hogy a **kódút** jó: a
nyers fájlra a nyers dekóder fut, a kép mérete és alakja stimmel, és nem a
`cv2.imdecode` néma `None`-ja jön vissza.
"""

from __future__ import annotations

import struct
from pathlib import Path

#: A minimális DNG rácsmérete. Kicsi, de a demozaikolásnak elég.
SZELESSEG = 64
MAGASSAG = 48

#: TIFF-típuskódok, amiket használunk.
_SHORT, _LONG, _BYTE, _ASCII, _RATIONAL, _SRATIONAL = 3, 4, 1, 2, 5, 10


def _cfa_adat(szelesseg: int, magassag: int) -> bytes:
    """16 bites Bayer-rács: átlós gradiens, hogy a dekódolt kép ne legyen
    egyenletes (egy konstans rácson a demozaikolás hibája nem látszana)."""
    px = bytearray()
    for y in range(magassag):
        for x in range(szelesseg):
            ertek = ((x * 1024 // szelesseg) + (y * 1024 // magassag)) * 32
            px += struct.pack("<H", ertek % 65536)
    return bytes(px)


def dng_bajtok(szelesseg: int = SZELESSEG, magassag: int = MAGASSAG) -> bytes:
    """Tömörítetlen, RGGB mintás CFA DNG (1.4) bájtjai.

    A kötelező DNG-mezők: `DNGVersion`, `UniqueCameraModel`, `ColorMatrix1`,
    `CalibrationIlluminant1`, `AsShotNeutral`, `BlackLevel`/`WhiteLevel` —
    ezek nélkül a LibRaw „unsupported file format"-tal utasítja el.
    """
    adat = _cfa_adat(szelesseg, magassag)
    szinmatrix = b"".join(
        struct.pack("<ii", n, 10000)
        for n in (6000, -1500, -500, -2000, 9000, 1000, -300, 1500, 6000)
    )
    semleges = b"".join(struct.pack("<II", n, 1000) for n in (500, 1000, 700))

    # (címke, típus, darab, külső payload VAGY beágyazott szám)
    bejegyzesek: list[tuple[int, int, int, bytes | None, int | None]] = [
        (254, _LONG, 1, None, 0),  # NewSubfileType — ez a fő kép
        (256, _SHORT, 1, None, szelesseg),  # ImageWidth
        (257, _SHORT, 1, None, magassag),  # ImageLength
        (258, _SHORT, 1, None, 16),  # BitsPerSample
        (259, _SHORT, 1, None, 1),  # Compression = nincs
        (262, _SHORT, 1, None, 32803),  # PhotometricInterpretation = CFA
        (273, _LONG, 1, None, None),  # StripOffsets — a végén töltjük ki
        (277, _SHORT, 1, None, 1),  # SamplesPerPixel
        (278, _SHORT, 1, None, magassag),  # RowsPerStrip
        (279, _LONG, 1, None, len(adat)),  # StripByteCounts
        (284, _SHORT, 1, None, 1),  # PlanarConfiguration
        (33421, _SHORT, 2, struct.pack("<HH", 2, 2), None),  # CFARepeatPatternDim
        (33422, _BYTE, 4, bytes([0, 1, 1, 2]), None),  # CFAPattern = RGGB
        (50706, _BYTE, 4, bytes([1, 4, 0, 0]), None),  # DNGVersion 1.4
        (50707, _BYTE, 4, bytes([1, 1, 0, 0]), None),  # DNGBackwardVersion
        (50708, _ASCII, 9, b"PicasaPy\x00", None),  # UniqueCameraModel
        (50714, _SHORT, 1, None, 0),  # BlackLevel
        (50717, _SHORT, 1, None, 65535),  # WhiteLevel
        (50721, _SRATIONAL, 9, szinmatrix, None),  # ColorMatrix1
        (50728, _RATIONAL, 3, semleges, None),  # AsShotNeutral
        (50778, _SHORT, 1, None, 17),  # CalibrationIlluminant1 = D55
    ]
    bejegyzesek.sort(key=lambda e: e[0])

    fejlec_hossz = 8
    ifd_hossz = 2 + 12 * len(bejegyzesek) + 4
    kulso_kezdet = fejlec_hossz + ifd_hossz

    # A négy bájtnál hosszabb értékek az IFD UTÁN állnak; a bejegyzés az
    # eltolásukat hordozza (TIFF-szabály).
    eltolasok: dict[int, int] = {}
    kulso = bytearray()
    kurzor = kulso_kezdet
    for cimke, _typ, _db, payload, _szam in bejegyzesek:
        if payload is not None and len(payload) > 4:
            eltolasok[cimke] = kurzor
            kulso += payload
            kurzor += len(payload)
            if len(payload) % 2:  # a TIFF páros határra igazít
                kulso += b"\x00"
                kurzor += 1
    adat_eltolas = kurzor

    ki = bytearray(b"II*\x00" + struct.pack("<I", fejlec_hossz))
    ki += struct.pack("<H", len(bejegyzesek))
    for cimke, typ, db, payload, szam in bejegyzesek:
        if cimke == 273:
            ertek = struct.pack("<I", adat_eltolas)
        elif payload is not None and len(payload) > 4:
            ertek = struct.pack("<I", eltolasok[cimke])
        elif payload is not None:
            ertek = payload.ljust(4, b"\x00")
        elif typ == _SHORT:
            ertek = struct.pack("<HH", szam, 0)
        else:
            ertek = struct.pack("<I", szam)
        ki += struct.pack("<HHI", cimke, typ, db) + ertek
    ki += struct.pack("<I", 0)  # nincs következő IFD
    ki += kulso
    assert len(ki) == adat_eltolas, (len(ki), adat_eltolas)
    ki += adat
    return bytes(ki)


def ir_dng(cel: Path, szelesseg: int = SZELESSEG, magassag: int = MAGASSAG) -> Path:
    """A generált DNG kiírása; a célútvonalat adja vissza."""
    cel.write_bytes(dng_bajtok(szelesseg, magassag))
    return cel
