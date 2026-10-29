"""A TIFF-blokk alapjai: a típusok, a konstansok és a szerkesztés alatti blokk
(`_Blokk`) bájtolvasása és -írása, a bájtsorrendtől függően (#3961).

A `tiff_helyben` modul ezekre épül; a nyilvános nevek onnan is elérhetők.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass


#: TIFF-típus → elem-méret (bájt). Csak az ismert típusokat írjuk.
_TIPUS_MERET = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4}
ASCII, SHORT, LONG, UNDEFINED = 2, 3, 4, 7
_EXIF_MUTATO = 0x8769
_GPS_MUTATO = 0x8825
_INTEROP_MUTATO = 0xA005
#: az előnézet bájtjainak kulcsa az önellenőrző szerkezetben (nem valódi tag)
_ELONEZET_BAJTOK = 0x10000
_JPEG_ELONEZET, _JPEG_ELONEZET_HOSSZ = 0x0201, 0x0202
#: üres (metaadat nélküli) forráshoz: kis végű (II) fejléc + 0 bejegyzéses IFD0;
#: a Picasa is II-t ír (#4009). A meglévő blokk bájtsorrendje nem változik.
_URES_TIFF = b"II\x2a\x00\x08\x00\x00\x00" + b"\x00\x00" + b"\x00\x00\x00\x00"


_TAJOLAS = 0x0112


#: az újraépített IFD1 tagjai, sorrendben (spec 16. H) 5.)
_IFD1_TAGEK = (0x0103, 0x011A, 0x011B, 0x0128, _JPEG_ELONEZET, _JPEG_ELONEZET_HOSSZ)


class TiffHiba(ValueError):
    """A blokk nem értelmezhető vagy nem írható biztonságosan."""


@dataclass(frozen=True)
class Ertek:
    """Egy írandó tag-érték: `tipus` (ASCII/SHORT/LONG/UNDEFINED) és a nyers
    tartalom (ASCII-nál a lezáró nullával együtt) vagy egész."""

    tipus: int
    tartalom: bytes | int


@dataclass(frozen=True)
class Valtozas:
    """`ifd`: `"0th"`, `"Exif"`, `"Interop"` (#3989, csak `csak_ha_hianyzik`) vagy
    `"1st"` (utóbbi csak meglévő tagot ír, helyben); `csak_ha_hianyzik`: a
    meglévőt nem írja felül; `csak_ha_megvan`: a hiányzót nem pótolja (#3966)."""

    ifd: str
    tag: int
    ertek: Ertek
    csak_ha_hianyzik: bool = False
    csak_ha_megvan: bool = False


@dataclass(frozen=True)
class _Bejegyzes:
    tag: int
    tipus: int
    darab: int
    hely: int  # a bejegyzés eltolása a blokkban


def ascii_ertek(szoveg: str) -> Ertek:
    """ASCII-érték a lezáró nullával."""
    return Ertek(ASCII, szoveg.encode("ascii") + b"\x00")


class _Blokk:
    """A szerkesztés alatti blokk: a forrás bájtjai + a hozzáfűzött rész."""

    def __init__(self, tiff: bytes) -> None:
        if len(tiff) < 8 or tiff[:4] not in (b"II*\x00", b"MM\x00*"):
            raise TiffHiba("nem TIFF-fejléc")
        self.e = "<" if tiff[:2] == b"II" else ">"
        self.buf = bytearray(tiff)
        self.eredeti_hossz = len(tiff)
        self.irt: list[tuple[int, int]] = []  # helyben írt [kezdet, vég)
        self.tablak: list[tuple[int, int]] = []  # olvasott IFD-táblák [kezdet, vég)
        #: olvasott tagek külső értéktartománya: (kezdet, vég, a tag bejegyzésének helye)
        self.ertekek: list[tuple[int, int, int]] = []

    # --- olvasás ---
    def u16(self, off: int) -> int:
        self._hatar(off, 2)
        return struct.unpack_from(self.e + "H", self.buf, off)[0]

    def u32(self, off: int) -> int:
        self._hatar(off, 4)
        return struct.unpack_from(self.e + "I", self.buf, off)[0]

    def _hatar(self, off: int, hossz: int) -> None:
        if off < 0 or off + hossz > len(self.buf):
            raise TiffHiba("eltolás a blokkon kívül")

    def ifd(self, off: int) -> tuple[list[_Bejegyzes], int]:
        n = self.u16(off)
        self._hatar(off, 2 + 12 * n + 4)
        self.tablak.append((off, off + 2 + 12 * n + 4))
        bejegyzesek = []
        for i in range(n):
            hely = off + 2 + 12 * i
            tag, tipus, darab = struct.unpack_from(self.e + "HHI", self.buf, hely)
            bejegyzesek.append(_Bejegyzes(tag, tipus, darab, hely))
        for b in bejegyzesek:
            self._ertek_tartomany(b)
        self._elonezet_tartomany(bejegyzesek)
        return bejegyzesek, self.u32(off + 2 + 12 * n)

    def _ertek_tartomany(self, b: _Bejegyzes) -> None:
        """A tag külső értékének tartománya, ha érvényes (a darabszám itt csak
        szám, nem foglal)."""
        elem = _TIPUS_MERET.get(b.tipus)
        if elem is None or elem * b.darab <= 4:
            return
        off = struct.unpack_from(self.e + "I", self.buf, b.hely + 8)[0]
        if off + elem * b.darab <= len(self.buf):
            self.ertekek.append((off, off + elem * b.darab, b.hely))

    def _elonezet_tartomany(self, bejegyzesek: list[_Bejegyzes]) -> None:
        """A JPEG-előnézet bájttartománya (0x0201/0x0202); a kulcsa a 0x0201 tag."""
        tagek = {b.tag: b for b in bejegyzesek}
        hely, hossz = tagek.get(_JPEG_ELONEZET), tagek.get(_JPEG_ELONEZET_HOSSZ)
        if not hely or not hossz or {hely.tipus, hossz.tipus} != {LONG}:
            return
        if hely.darab != 1 or hossz.darab != 1:
            return
        kezdet = struct.unpack_from(self.e + "I", self.buf, hely.hely + 8)[0]
        veg = kezdet + struct.unpack_from(self.e + "I", self.buf, hossz.hely + 8)[0]
        if kezdet < veg <= len(self.buf):
            self.ertekek.append((kezdet, veg, hely.hely))

    # --- írás ---
    def ir_helyben(self, off: int, adat: bytes) -> None:
        self._hatar(off, len(adat))
        self.buf[off : off + len(adat)] = adat
        self.irt.append((off, off + len(adat)))

    def hozzafuz(self, adat: bytes) -> int:
        if len(self.buf) % 2:
            self.buf.append(0)
        kezdet = len(self.buf)
        self.buf += adat
        return kezdet

    def egesz(self, tipus: int, ertek: int) -> bytes:
        return struct.pack(self.e + ("H" if tipus == SHORT else "I"), ertek)
