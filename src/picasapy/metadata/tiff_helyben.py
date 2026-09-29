"""EXIF (TIFF) blokk frissítése HELYBEN — a meglévő bájtok el nem mozdulnak (#3961).

## Miért nem piexif

A `piexif.load` → `piexif.dump` oda-vissza út a valódi kamerás JPEG-en
(Xiaomi 14T) rontott és törölt: a nulla nélküli ASCII-t csonkolta
(`ExifVersion` `0220` → `022`), eldobta az ismeretlen tageket és az
InteropIFD-t, és újraírta a blokkot, így a MakerNote eltolása elcsúszott —
az abszolút eltolással dolgozó gyártói jegyzetek (Canon, Olympus,
Panasonic, Pentax) ettől érvénytelenek. A régi, bájtra másoló út mindezt
megtartotta; az új út nem veszíthet el semmit.

## Hogyan

A forrás blokkja **bájtra megmarad**, és csak két dolog történhet vele:

1. **Helyben írás:** egy MEGLÉVŐ tag értéke a saját helyén felülíródik, ha a
   típusa egyező és az új érték elfér (`DateTime` 20 bájtja, a méret SHORT/LONG
   mezője).
2. **Hozzáfűzés:** ha taget kell HOZZÁADNI (vagy a meglévő nem írható
   helyben), az érintett IFD **másolata** a blokk VÉGÉRE kerül a bővített
   bejegyzéslistával, és csak a rá mutató eltolás (a fejléc IFD0-mutatója,
   ill. az IFD0 `ExifIFD`-mutatója) változik. A régi IFD árván a helyén
   marad — semmilyen meglévő érték-eltolás nem mozdul, a MakerNote sem.

A beágyazott előnézet (IFD1) cseréje ugyanígy: ha a régi előnézet a blokk
végén ül, az helyére kerül az új; ha nem, az új a végére fűződik. Az IFD1
`JPEGInterchangeFormat`/`…Length` mezője helyben íródik.

A végén egy önellenőrzés fut: a kimenet a forrás hosszáig bájtra egyezik a
forrással, kivéve a helyben írt tartományokat (és a lecserélt előnézetet).
Bármi váratlanra `TiffHiba` — a hívó ilyenkor a forrás bájtjait adja tovább.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Callable

#: TIFF-típus → elem-méret (bájt). Csak az ismert típusokat írjuk.
_TIPUS_MERET = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4}
ASCII, SHORT, LONG, UNDEFINED = 2, 3, 4, 7
_EXIF_MUTATO = 0x8769
_JPEG_ELONEZET, _JPEG_ELONEZET_HOSSZ = 0x0201, 0x0202
#: üres (metaadat nélküli) forráshoz: nagy végű fejléc + 0 bejegyzéses IFD0
_URES_TIFF = b"MM\x00\x2a\x00\x00\x00\x08" + b"\x00\x00" + b"\x00\x00\x00\x00"


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
    """`ifd`: `"0th"` vagy `"Exif"`; `csak_ha_hianyzik`: a meglévőt nem írja felül."""

    ifd: str
    tag: int
    ertek: Ertek
    csak_ha_hianyzik: bool = False


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
        bejegyzesek = []
        for i in range(n):
            hely = off + 2 + 12 * i
            tag, tipus, darab = struct.unpack_from(self.e + "HHI", self.buf, hely)
            bejegyzesek.append(_Bejegyzes(tag, tipus, darab, hely))
        return bejegyzesek, self.u32(off + 2 + 12 * n)

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


def _nyers(blokk: _Blokk, ertek: Ertek) -> tuple[int, int, bytes]:
    """(típus, darab, nyers bájtok) a blokk bájtsorrendjében."""
    if isinstance(ertek.tartalom, int):
        tipus = ertek.tipus
        if tipus == SHORT and ertek.tartalom > 0xFFFF:
            tipus = LONG
        return tipus, 1, blokk.egesz(tipus, ertek.tartalom)
    return ertek.tipus, len(ertek.tartalom), ertek.tartalom


def _helyben_irhato(blokk: _Blokk, meglevo: _Bejegyzes, ertek: Ertek) -> bool:
    """Felülírja a meglévő értéket a saját helyén, ha lehet."""
    if isinstance(ertek.tartalom, int):
        if meglevo.darab != 1 or meglevo.tipus not in (SHORT, LONG):
            return False
        if meglevo.tipus == SHORT and ertek.tartalom > 0xFFFF:
            return False
        blokk.ir_helyben(meglevo.hely + 8, blokk.egesz(meglevo.tipus, ertek.tartalom))
        return True
    if meglevo.tipus != ertek.tipus or meglevo.darab < len(ertek.tartalom):
        return False
    adat = ertek.tartalom.ljust(meglevo.darab, b"\x00")
    hely = meglevo.hely + 8 if len(adat) <= 4 else blokk.u32(meglevo.hely + 8)
    blokk.ir_helyben(hely, adat)
    return True


def _alkalmaz(
    blokk: _Blokk, bejegyzesek: list[_Bejegyzes], valtozasok: list[Valtozas]
) -> dict[int, tuple[int, int, bytes]]:
    """A helyben nem írható változások: tag → új (típus, darab, nyers érték)."""
    uj: dict[int, tuple[int, int, bytes]] = {}
    tagek = {b.tag: b for b in bejegyzesek}
    for v in valtozasok:
        meglevo = tagek.get(v.tag)
        if meglevo is not None and (v.csak_ha_hianyzik or _helyben_irhato(blokk, meglevo, v.ertek)):
            continue
        uj[v.tag] = _nyers(blokk, v.ertek)
    return uj


def _athelyez(
    blokk: _Blokk,
    bejegyzesek: list[_Bejegyzes],
    uj: dict[int, tuple[int, int, bytes]],
    kovetkezo: int,
) -> int:
    """Az IFD bővített másolata a blokk végére; visszaadja az új eltolását."""
    # a mező a JELENLEGI bájtokból: a helyben írt érték is átkerüljön
    sorok = {
        b.tag: (b.tipus, b.darab, bytes(blokk.buf[b.hely + 8 : b.hely + 12]), False)
        for b in bejegyzesek
    }
    sorok.update({tag: (t, d, nyers, True) for tag, (t, d, nyers) in uj.items()})
    if len(blokk.buf) % 2:
        blokk.buf.append(0)
    kezdet = len(blokk.buf)
    adat_kezdet = kezdet + 2 + 12 * len(sorok) + 4
    fej, adat = struct.pack(blokk.e + "H", len(sorok)), bytearray()
    for tag in sorted(sorok):
        tipus, darab, tartalom, uj_ertek = sorok[tag]
        if uj_ertek and len(tartalom) > 4:
            if (adat_kezdet + len(adat)) % 2:
                adat.append(0)
            mezo = struct.pack(blokk.e + "I", adat_kezdet + len(adat))
            adat += tartalom
        else:
            mezo = tartalom.ljust(4, b"\x00") if uj_ertek else tartalom
        fej += struct.pack(blokk.e + "HHI", tag, tipus, darab) + mezo
    fej += struct.pack(blokk.e + "I", kovetkezo)
    if blokk.hozzafuz(bytes(fej) + bytes(adat)) != kezdet:
        raise TiffHiba("igazítási hiba")
    return kezdet


def _elonezet_csere(blokk: _Blokk, ifd1_off: int, uj_kep: bytes) -> None:
    """Az IFD1 JPEG-előnézete helyett `uj_kep`; nem megfelelő IFD1-nél kimarad."""
    tagek = {b.tag: b for b in blokk.ifd(ifd1_off)[0]}
    hely, hossz = tagek.get(_JPEG_ELONEZET), tagek.get(_JPEG_ELONEZET_HOSSZ)
    if not hely or not hossz or {hely.tipus, hossz.tipus} != {LONG} or hely.darab != 1:
        return
    regi_kezdet, regi_hossz = blokk.u32(hely.hely + 8), blokk.u32(hossz.hely + 8)
    if regi_kezdet + regi_hossz == blokk.eredeti_hossz == len(blokk.buf):
        # a régi előnézet a blokk végén: a helyére kerül az új
        del blokk.buf[regi_kezdet:]
        blokk.eredeti_hossz = regi_kezdet
        blokk.buf += uj_kep
        kezdet = regi_kezdet
    else:
        kezdet = blokk.hozzafuz(uj_kep)
    blokk.ir_helyben(hely.hely + 8, blokk.egesz(LONG, kezdet))
    blokk.ir_helyben(hossz.hely + 8, blokk.egesz(LONG, len(uj_kep)))


def _ellenoriz(forras: bytes, blokk: _Blokk, csonk: int) -> None:
    """A forrás bájtjai — a helyben írt tartományokon, az IFD0-mutatón és a
    lecserélt előnézeten kívül — változatlanok."""
    szabad = sorted(blokk.irt + [(4, 8), (csonk, len(forras))])
    pos = 0
    for kezdet, veg in szabad + [(len(forras), len(forras))]:
        if kezdet > pos and blokk.buf[pos:kezdet] != forras[pos:kezdet]:
            raise TiffHiba("önellenőrzés: elmozdult forrásbájt")
        pos = max(pos, veg)


def frissitett_tiff(
    tiff: bytes | None,
    valtozasok: list[Valtozas],
    *,
    elonezet: Callable[[], bytes | None] | None = None,
) -> bytes:
    """A frissített TIFF-blokk (`tiff=None`: új, üres blokkból építve).

    `elonezet`: ha van IFD1 JPEG-előnézet, ez adja az újat (lustán, mert
    dekódolás kell hozzá); `None` visszatérésnél a forrásé marad.
    Hibánál `TiffHiba`."""
    forras = tiff if tiff is not None else _URES_TIFF
    blokk = _Blokk(forras)
    ifd0_off = blokk.u32(4)
    ifd0, ifd1_off = blokk.ifd(ifd0_off)
    if ifd1_off and elonezet is not None:
        uj_kep = elonezet()
        if uj_kep:
            _elonezet_csere(blokk, ifd1_off, uj_kep)
    csonk = blokk.eredeti_hossz

    uj0 = _alkalmaz(blokk, ifd0, [v for v in valtozasok if v.ifd == "0th"])
    exif_valtozasok = [v for v in valtozasok if v.ifd == "Exif"]
    exif_mutato = next((b for b in ifd0 if b.tag == _EXIF_MUTATO), None)
    if exif_valtozasok:
        if exif_mutato is not None:
            if exif_mutato.tipus not in (LONG, 13) or exif_mutato.darab != 1:
                raise TiffHiba("ExifIFD-mutató típusa")
            exif_off = blokk.u32(exif_mutato.hely + 8)
            exif, exif_kov = blokk.ifd(exif_off)
        else:
            exif, exif_kov = [], 0
        uj_exif = _alkalmaz(blokk, exif, exif_valtozasok)
        if uj_exif:
            uj_off = _athelyez(blokk, exif, uj_exif, exif_kov)
            if exif_mutato is not None:
                blokk.ir_helyben(exif_mutato.hely + 8, blokk.egesz(LONG, uj_off))
            else:
                uj0[_EXIF_MUTATO] = (LONG, 1, blokk.egesz(LONG, uj_off))
    if uj0:
        uj_ifd0 = _athelyez(blokk, ifd0, uj0, ifd1_off)
        blokk.buf[4:8] = blokk.egesz(LONG, uj_ifd0)
    if tiff is not None:
        _ellenoriz(forras, blokk, csonk)
    return bytes(blokk.buf)
