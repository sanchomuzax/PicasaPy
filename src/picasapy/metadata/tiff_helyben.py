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

A helyben írás célja csak a fejléc (8 bájt) utáni, a forrás hosszán belüli
tartomány lehet, amely nem fed olvasott IFD-táblát (IFD0, Exif, GPS, Interop,
IFD1), más tag értékét, sem a beágyazott előnézet bájtjait; ami nem ilyen, az
hozzáfűzéssel kerül át. A fájlból olvasott darabszám a célellenőrzés ELŐTT
nem foglalhat (#3964).

A végén két önellenőrzés fut: (1) a kimenet a forrás hosszáig bájtra egyezik
a forrással, kivéve a helyben írt tartományokat (és a lecserélt előnézetet);
(2) a kimenetet visszaolvasva (IFD0, Exif, GPS, Interop, IFD1 és a nem cserélt
előnézet bájtjai) minden forrás-tag típusa, darabszáma és értéke egyezik,
kivéve a szándékosan írtakat. Az egy IFD-ben kétszer szereplő tag minden
példánya átkerül, és az ellenőrzés listaként hasonlít (#3968).

Az InteropIFD (`"Interop"` változás, #3989) ugyanezen az úton bővül: a meglévő
Interop IFD bővített másolata a blokk végére kerül, és csak az Exif IFD
`0xa005` mutatója íródik helyben; ha nincs Interop IFD, újat fűz a végére, és
a mutató az (átmásolt) Exif IFD-be kerül. Csak `csak_ha_hianyzik` tag adható
hozzá; érvénytelen vagy kétszer szereplő `0xa005`-nél az Interop érintetlen.
Az érvénytelen (0-s vagy ismeretlen) típusú bejegyzés az áthelyezéskor a forrásbeli
relatív helyén marad (a forrás végén állók a végén), csak az érvényesek rendeződnek
tag szerint (#3999).
Az IFD1 ÚJRAÉPÍTÉSE (`uj_ifd1`, #3998, spec 16. H): az export az IFD1-et
mindig a kimenetéből készíti, a forrásé sosem kerül át. A forrás IFD1-táblája
a helyén marad (árván), a beágyazott előnézetének bájtjai kinullázódnak (vagy,
ha a blokk végén álltak, le is vágódnak), hogy a forrás bélyegképe ne
szivárogjon a kimenetbe; az új IFD1 (`0x103`, `0x11a`, `0x11b`, `0x128`,
`0x201`, `0x202`) a többi hozzáfűzés UTÁN a blokk végére kerül, utána a
bélyegkép (páratlan hossznál 1 nullbájt követi), és csak az IFD0 következő-IFD
mutatója íródik. Bélyegkép nélkül (`None`) a mutató 0: nincs IFD1. A kimenetet
külön önellenőrzés olvassa vissza.
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
_GPS_MUTATO = 0x8825
_INTEROP_MUTATO = 0xA005
#: az előnézet bájtjainak kulcsa az önellenőrző szerkezetben (nem valódi tag)
_ELONEZET_BAJTOK = 0x10000
_JPEG_ELONEZET, _JPEG_ELONEZET_HOSSZ = 0x0201, 0x0202
#: üres (metaadat nélküli) forráshoz: nagy végű fejléc + 0 bejegyzéses IFD0
_URES_TIFF = b"MM\x00\x2a\x00\x00\x00\x08" + b"\x00\x00" + b"\x00\x00\x00\x00"


_TAJOLAS = 0x0112


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


def _nyers(blokk: _Blokk, ertek: Ertek) -> tuple[int, int, bytes]:
    """(típus, darab, nyers bájtok) a blokk bájtsorrendjében."""
    if isinstance(ertek.tartalom, int):
        tipus = ertek.tipus
        if tipus == SHORT and ertek.tartalom > 0xFFFF:
            tipus = LONG
        return tipus, 1, blokk.egesz(tipus, ertek.tartalom)
    return ertek.tipus, len(ertek.tartalom), ertek.tartalom


def _cel_szabad(blokk: _Blokk, kezdet: int, hossz: int, kiveve: int | None = None) -> bool:
    """A `[kezdet, kezdet+hossz)` a fejléc után, a forrás hosszán belül van,
    és sem az olvasott IFD-táblákat, sem egy másik olvasott tag külső értékét
    (az előnézet bájtjait is) nem fedi — ide szabad írni/cserélni.

    `kiveve`: annak a tagnak a bejegyzés-helye, amelyiket éppen helyben írjuk
    (a saját értéktartománya nem akadály)."""
    veg = kezdet + hossz
    if kezdet < 8 or veg > blokk.eredeti_hossz:
        return False
    if any(kezdet < t_veg and t_kezdet < veg for t_kezdet, t_veg in blokk.tablak):
        return False
    return not any(
        kezdet < e_veg and e_kezdet < veg
        for e_kezdet, e_veg, hely in blokk.ertekek
        if hely != kiveve
    )


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
    # a fájlból olvasott darabszám (akár 0xFFFFFFFF) előbb a célellenőrzésen megy át,
    # csak utána foglal (#3964 B1)
    meret = _TIPUS_MERET.get(meglevo.tipus, 1) * meglevo.darab
    if meret <= 4:
        hely = meglevo.hely + 8
    else:
        hely = blokk.u32(meglevo.hely + 8)
        if not _cel_szabad(blokk, hely, meret, meglevo.hely):
            return False
    blokk.ir_helyben(hely, ertek.tartalom.ljust(meret, b"\x00"))
    return True


def _alkalmaz(
    blokk: _Blokk, bejegyzesek: list[_Bejegyzes], valtozasok: list[Valtozas]
) -> dict[int, tuple[int, int, bytes]]:
    """A helyben nem írható változások: tag → új (típus, darab, nyers érték)."""
    uj: dict[int, tuple[int, int, bytes]] = {}
    tagek = {b.tag: b for b in bejegyzesek}
    for v in valtozasok:
        meglevo = tagek.get(v.tag)
        if meglevo is None and v.csak_ha_megvan:
            continue
        if meglevo is not None and not v.csak_ha_hianyzik:
            _nem_ketszer_szereplo(bejegyzesek, v.tag)
        if meglevo is not None and (v.csak_ha_hianyzik or _helyben_irhato(blokk, meglevo, v.ertek)):
            continue
        uj[v.tag] = _nyers(blokk, v.ertek)
    return uj


def _rendez(sorok: list[tuple]) -> list[tuple]:
    """Az érvényes típusú sorok tag szerint (stabilan: az azonos tagek sorrendje
    marad); az érvénytelen (0-s vagy ismeretlen) típusú sor a forrásban ELŐTTE
    álló érvényes sor után marad, a forrás végén álló a végén (#3999). Így az
    IFD elejére csak az kerülhet, ami a forrásban is elöl állt — az IFD elején
    álló 0-s típusra az exiftool az egész IFD-t eldobja.

    `sorok`: a forrás sorai forrássorrendben (5. elem False), utánuk az újak."""
    if all(sor[1] in _TIPUS_MERET for sor in sorok):
        return sorted(sorok, key=lambda sor: sor[0])
    # érvénytelen sorok, amelyek UTÁN még áll forrásbeli érvényes sor
    kozepen: set[int] = set()
    van_utana = False
    for i in reversed(range(len(sorok))):
        if sorok[i][1] not in _TIPUS_MERET:
            if van_utana:
                kozepen.add(i)
        elif not sorok[i][4]:
            van_utana = True
    utana: dict[int | None, list[int]] = {}  # előző érvényes forrássor → szemét
    vegen: list[int] = []
    elozo: int | None = None
    for i, sor in enumerate(sorok):
        if sor[1] not in _TIPUS_MERET:
            (utana.setdefault(elozo, []) if i in kozepen else vegen).append(i)
        elif not sor[4]:
            elozo = i
    ervenyes = sorted(
        (i for i, sor in enumerate(sorok) if sor[1] in _TIPUS_MERET), key=lambda i: sorok[i][0]
    )
    rend = list(utana.get(None, []))
    for i in ervenyes:
        rend.append(i)
        rend += utana.get(i, [])
    return [sorok[i] for i in rend + vegen]


def _athelyez(
    blokk: _Blokk,
    bejegyzesek: list[_Bejegyzes],
    uj: dict[int, tuple[int, int, bytes]],
    kovetkezo: int,
) -> int:
    """Az IFD bővített másolata a blokk végére; visszaadja az új eltolását.

    A kétszer szereplő tag minden példánya átkerül, a forrásbeli sorrendjükben
    (#3968); az ilyen tag cseréje nem egyértelmű, ezért `TiffHiba`."""
    cserelt = [b.tag for b in bejegyzesek if b.tag in uj]
    if len(cserelt) != len(set(cserelt)):
        raise TiffHiba("kétszer szereplő tag nem cserélhető")
    # a mező a JELENLEGI bájtokból: a helyben írt érték is átkerüljön
    sorok = [
        (b.tag, b.tipus, b.darab, bytes(blokk.buf[b.hely + 8 : b.hely + 12]), False)
        for b in bejegyzesek
        if b.tag not in uj
    ]
    sorok += [(tag, t, d, nyers, True) for tag, (t, d, nyers) in uj.items()]
    sorok = _rendez(sorok)
    if len(sorok) > 0xFFFF:
        raise TiffHiba("túl sok bejegyzés")
    if len(blokk.buf) % 2:
        blokk.buf.append(0)
    kezdet = len(blokk.buf)
    adat_kezdet = kezdet + 2 + 12 * len(sorok) + 4
    fej, adat = struct.pack(blokk.e + "H", len(sorok)), bytearray()
    for tag, tipus, darab, tartalom, uj_ertek in sorok:
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


def _helyben_1st(blokk: _Blokk, ifd1: list[_Bejegyzes], valtozasok: list[Valtozas]) -> None:
    """Az IFD1 MEGLÉVŐ tagjei helyben; új tagot nem ad hozzá, és amit a helyén
    nem lehet felülírni, azt érintetlenül hagyja (#3966)."""
    tagek = {b.tag: b for b in ifd1}
    for v in valtozasok:
        meglevo = tagek.get(v.tag)
        if meglevo is not None and not v.csak_ha_hianyzik:
            _nem_ketszer_szereplo(ifd1, v.tag)
            _helyben_irhato(blokk, meglevo, v.ertek)


def _nem_ketszer_szereplo(bejegyzesek: list[_Bejegyzes], tag: int) -> None:
    """A kétszer szereplő tag felülírása nem egyértelmű (az olvasók hol az
    elsőt, hol az utolsót veszik): `TiffHiba`, a hívó a forrás bájtjaira esik
    vissza (#3968)."""
    if sum(b.tag == tag for b in bejegyzesek) > 1:
        raise TiffHiba(f"kétszer szereplő tag nem írható: 0x{tag:04x}")


def tajolas_1_helyben(tiff: bytes) -> bytes:
    """Tartalék út (#3966): az IFD0 és az IFD1 meglévő `Orientation` (0x0112)
    tagje a helyén `1`-re; semmi más nem változik. Hibánál `TiffHiba`: a helyén
    nem írható tag, és az is, ha a visszaolvasott kimenetben a tájoláson kívül
    bármi más megváltozott (ugyanaz a szerkezeti önellenőrzés, mint a fő úton)."""
    blokk = _Blokk(tiff)
    ifd0, ifd1_off = blokk.ifd(blokk.u32(4))
    ifd1 = _ifd1_tagek(blokk, ifd1_off)
    ertek = Ertek(SHORT, 1)
    for tagek in (ifd0, ifd1):
        for b in tagek:
            if b.tag == _TAJOLAS and not _helyben_irhato(blokk, b, ertek):
                raise TiffHiba("a tájolás-tag a helyén nem írható")
    kimenet = bytes(blokk.buf)
    _ellenoriz_szerkezet(tiff, kimenet, {("0th", _TAJOLAS), ("1st", _TAJOLAS)})
    return kimenet


def _elonezet_csere(blokk: _Blokk, ifd1: list[_Bejegyzes], uj_kep: bytes) -> bool:
    """Az IFD1 JPEG-előnézete helyett `uj_kep`; nem megfelelő IFD1-nél kimarad
    (`False`)."""
    tagek = {b.tag: b for b in ifd1}
    hely, hossz = tagek.get(_JPEG_ELONEZET), tagek.get(_JPEG_ELONEZET_HOSSZ)
    if not hely or not hossz or {hely.tipus, hossz.tipus} != {LONG} or hely.darab != 1:
        return False
    if hossz.darab != 1:
        # a több elemű LONG mezője eltolás, nem hossz (#3968)
        raise TiffHiba("az előnézet hosszának darabszáma nem 1")
    regi_kezdet, regi_hossz = blokk.u32(hely.hely + 8), blokk.u32(hossz.hely + 8)
    if (
        regi_kezdet + regi_hossz == blokk.eredeti_hossz == len(blokk.buf)
        and _cel_szabad(blokk, regi_kezdet, regi_hossz, hely.hely)
    ):
        # a régi előnézet a blokk végén: a helyére kerül az új
        del blokk.buf[regi_kezdet:]
        blokk.eredeti_hossz = regi_kezdet
        blokk.buf += uj_kep
        kezdet = regi_kezdet
    else:
        kezdet = blokk.hozzafuz(uj_kep)
    blokk.ir_helyben(hely.hely + 8, blokk.egesz(LONG, kezdet))
    blokk.ir_helyben(hossz.hely + 8, blokk.egesz(LONG, len(uj_kep)))
    return True


def _ellenoriz(forras: bytes, blokk: _Blokk, csonk: int) -> None:
    """A forrás bájtjai — a helyben írt tartományokon, az IFD0-mutatón és a
    lecserélt előnézeten kívül — változatlanok."""
    szabad = sorted(blokk.irt + [(4, 8), (csonk, len(forras))])
    pos = 0
    for kezdet, veg in szabad + [(len(forras), len(forras))]:
        if kezdet > pos and blokk.buf[pos:kezdet] != forras[pos:kezdet]:
            raise TiffHiba("önellenőrzés: elmozdult forrásbájt")
        pos = max(pos, veg)


def _tartalom(blokk: _Blokk, b: _Bejegyzes, forras_hossz: int) -> tuple[int, int, bytes]:
    """(típus, darab, érték-bájtok); ismeretlen típusnál, és ha az érték a
    `forras_hossz`-on túlra mutat, a nyers 4 bájtos mező (a forrásból kilógó
    mutatónál a kimenetbe hozzáfűzött adat nem különbözhet a forrás üres
    szeletétől)."""
    mezo = bytes(blokk.buf[b.hely + 8 : b.hely + 12])
    elem = _TIPUS_MERET.get(b.tipus)
    if elem is None or elem * b.darab <= 4:
        return b.tipus, b.darab, mezo
    off = blokk.u32(b.hely + 8)
    if off + elem * b.darab > forras_hossz:
        return b.tipus, b.darab, mezo
    return b.tipus, b.darab, bytes(blokk.buf[off : off + elem * b.darab])


def _mutatott_ifd(blokk: _Blokk, mutato: _Bejegyzes | None) -> list[_Bejegyzes]:
    """A mutató által kijelölt IFD tagjei; érvénytelen mutatónál üres (kimarad)."""
    if mutato is None or mutato.tipus not in (LONG, 13) or mutato.darab != 1:
        return []
    try:
        return blokk.ifd(blokk.u32(mutato.hely + 8))[0]
    except TiffHiba:
        return []


def _ifd1_tagek(blokk: _Blokk, ifd1_off: int) -> list[_Bejegyzes]:
    """Az IFD1 tagjei; olvashatatlan vagy hiányzó IFD1-nél üres („nincs IFD1”)."""
    if not ifd1_off:
        return []
    try:
        return blokk.ifd(ifd1_off)[0]
    except TiffHiba:
        return []


def _elonezet_bajtok(blokk: _Blokk, ifd1: list[_Bejegyzes], forras_hossz: int) -> bytes | None:
    tagek = {b.tag: b for b in ifd1}
    hely, hossz = tagek.get(_JPEG_ELONEZET), tagek.get(_JPEG_ELONEZET_HOSSZ)
    if not hely or not hossz or {hely.tipus, hossz.tipus} != {LONG}:
        return None
    if hely.darab != 1 or hossz.darab != 1:
        return None
    kezdet = blokk.u32(hely.hely + 8)
    veg = kezdet + blokk.u32(hossz.hely + 8)
    if kezdet >= veg or veg > forras_hossz or veg > len(blokk.buf):
        return None
    return bytes(blokk.buf[kezdet:veg])


def _szerkezet(
    tiff: bytes, forras_hossz: int
) -> dict[tuple[str, int], list[tuple[int, int, bytes]]]:
    """A blokk tagjei visszaolvasva: IFD0 → Exif (→ Interop) → GPS → IFD1, és az
    előnézet bájtjai. Kulcsonként LISTA: a kétszer szereplő tag minden példánya
    külön elem, sorrendben (#3968)."""
    blokk = _Blokk(tiff)
    ifd0, ifd1_off = blokk.ifd(blokk.u32(4))
    out: dict[tuple[str, int], list[tuple[int, int, bytes]]] = {}

    def felvesz(nev: str, tagek: list[_Bejegyzes]) -> None:
        for b in tagek:
            out.setdefault((nev, b.tag), []).append(_tartalom(blokk, b, forras_hossz))

    felvesz("0th", ifd0)
    mutato = next((b for b in ifd0 if b.tag == _EXIF_MUTATO), None)
    if mutato is not None and mutato.tipus in (LONG, 13) and mutato.darab == 1:
        exif = blokk.ifd(blokk.u32(mutato.hely + 8))[0]
        felvesz("Exif", exif)
        interop = _mutatott_ifd(blokk, next((b for b in exif if b.tag == _INTEROP_MUTATO), None))
        felvesz("Interop", interop)
    gps = _mutatott_ifd(blokk, next((b for b in ifd0 if b.tag == _GPS_MUTATO), None))
    felvesz("GPS", gps)
    ifd1 = _ifd1_tagek(blokk, ifd1_off)
    felvesz("1st", ifd1)
    kep = _elonezet_bajtok(blokk, ifd1, forras_hossz)
    if kep is not None:
        out[("1st", _ELONEZET_BAJTOK)] = [(0, len(kep), kep)]
    return out


def _ellenoriz_szerkezet(
    forras: bytes,
    kimenet: bytes,
    szandekolt: set[tuple[str, int]],
    ifd1_ujra: bool = False,
) -> None:
    """Minden forrás-tag — a szándékosan írtakon kívül — típusra, darabra és
    értékre változatlanul olvasható vissza a kimenetből (az előnézet bájtjai is,
    ha nem cserélődtek). `ifd1_ujra`: az IFD1 tagjai (és az előnézet bájtjai)
    szándékosan mind eldobódnak; az újat a `_ellenoriz_ifd1` nézi."""
    regi, uj = _szerkezet(forras, len(forras)), _szerkezet(kimenet, len(forras))
    for kulcs, ertek in regi.items():
        if ifd1_ujra and kulcs[0] == "1st":
            continue
        if kulcs not in szandekolt and uj.get(kulcs) != ertek:
            raise TiffHiba(f"önellenőrzés: megváltozott tag {kulcs[0]}/{kulcs[1]:#06x}")


def _szandekolt(
    valtozasok: list[Valtozas],
    elonezet_csere: bool,
    interop_mutato: bool,
) -> set[tuple[str, int]]:
    kulcsok = {(v.ifd, v.tag) for v in valtozasok if not v.csak_ha_hianyzik}
    kulcsok.add(("0th", _EXIF_MUTATO))
    if interop_mutato:
        kulcsok.add(("Exif", _INTEROP_MUTATO))
    if elonezet_csere:
        kulcsok |= {("1st", _JPEG_ELONEZET), ("1st", _JPEG_ELONEZET_HOSSZ)}
        kulcsok.add(("1st", _ELONEZET_BAJTOK))
    return kulcsok


#: az újraépített IFD1 tagjai, sorrendben (spec 16. H) 5.)
_IFD1_TAGEK = (0x0103, 0x011A, 0x011B, 0x0128, _JPEG_ELONEZET, _JPEG_ELONEZET_HOSSZ)
_RACIONALIS = 5


def _regi_elonezet_torlese(blokk: _Blokk, ifd1: list[_Bejegyzes]) -> None:
    """A forrás IFD1-előnézetének bájtjai nem maradhatnak a kimenetben (a
    bélyegkép sosem másolódik át; a levágott képrészt is mutathatná): a blokk
    végén álló előnézet levágódik, másutt kinullázódik. Csak érvényes, más
    taggel és IFD-táblával nem fedő tartományhoz nyúl."""
    tagek = {b.tag: b for b in ifd1}
    hely, hossz = tagek.get(_JPEG_ELONEZET), tagek.get(_JPEG_ELONEZET_HOSSZ)
    if not hely or not hossz or {hely.tipus, hossz.tipus} != {LONG}:
        return
    if hely.darab != 1 or hossz.darab != 1:
        return
    kezdet = blokk.u32(hely.hely + 8)
    meret = blokk.u32(hossz.hely + 8)
    if meret == 0 or kezdet + meret > len(blokk.buf):
        return
    if not _cel_szabad(blokk, kezdet, meret, hely.hely):
        return
    if kezdet + meret == blokk.eredeti_hossz == len(blokk.buf):
        del blokk.buf[kezdet:]
        blokk.eredeti_hossz = kezdet
    else:
        blokk.ir_helyben(kezdet, bytes(meret))


def _ifd1_epites(blokk: _Blokk, jpeg: bytes) -> int:
    """Az új IFD1 a blokk végére, utána a bélyegkép; visszaadja az IFD1
    eltolását. A racionális értékek (72/1) az IFD1-tábla után, a bélyegkép
    azok után áll (mind páros eltoláson), és páratlan hossznál 1 nullbájt követi."""
    e = blokk.e
    kezdet = len(blokk.buf) + len(blokk.buf) % 2
    tabla = 2 + 12 * len(_IFD1_TAGEK) + 4
    x_off, y_off = kezdet + tabla, kezdet + tabla + 8
    kep_off = kezdet + tabla + 16
    sorok = {
        0x0103: (SHORT, blokk.egesz(SHORT, 6).ljust(4, b"\x00")),
        0x011A: (_RACIONALIS, struct.pack(e + "I", x_off)),
        0x011B: (_RACIONALIS, struct.pack(e + "I", y_off)),
        0x0128: (SHORT, blokk.egesz(SHORT, 2).ljust(4, b"\x00")),
        _JPEG_ELONEZET: (LONG, struct.pack(e + "I", kep_off)),
        _JPEG_ELONEZET_HOSSZ: (LONG, struct.pack(e + "I", len(jpeg))),
    }
    adat = struct.pack(e + "H", len(_IFD1_TAGEK))
    for tag in _IFD1_TAGEK:
        tipus, mezo = sorok[tag]
        adat += struct.pack(e + "HHI", tag, tipus, 1) + mezo
    adat += struct.pack(e + "I", 0)
    adat += struct.pack(e + "II", 72, 1) * 2 + jpeg + (b"\x00" if len(jpeg) % 2 else b"")
    if blokk.hozzafuz(adat) != kezdet:
        raise TiffHiba("igazítási hiba")
    return kezdet


def _ifd0_kovetkezo(blokk: _Blokk, ifd0_hely: int, kovetkezo: int, athelyezett: bool) -> None:
    """Az IFD0 következő-IFD mutatója (az IFD1 helye) a jelenlegi helyén. A
    forrásbeli táblában helyben írásként számít (az önellenőrzés ismeri); az
    áthelyezett másolat a forrás hosszán túl van, ott nincs mit ellenőrizni."""
    hely = ifd0_hely + 2 + 12 * blokk.u16(ifd0_hely)
    if athelyezett:
        blokk._hatar(hely, 4)
        blokk.buf[hely : hely + 4] = blokk.egesz(LONG, kovetkezo)
    else:
        blokk.ir_helyben(hely, blokk.egesz(LONG, kovetkezo))


def _ellenoriz_ifd1(kimenet: bytes, jpeg: bytes | None) -> None:
    """Az újraépített IFD1 visszaolvasva: bélyegkép nélkül nincs IFD1; egyébként
    pontosan a hat tag, és a bélyegkép bájtra a helyén, a blokk végén."""
    blokk = _Blokk(kimenet)
    _, kovetkezo = blokk.ifd(blokk.u32(4))
    if jpeg is None:
        if kovetkezo:
            raise TiffHiba("önellenőrzés: az IFD1 nem maradhat")
        return
    if not kovetkezo:
        raise TiffHiba("önellenőrzés: hiányzik az új IFD1")
    tagek, kov1 = blokk.ifd(kovetkezo)
    if [b.tag for b in tagek] != list(_IFD1_TAGEK) or kov1:
        raise TiffHiba("önellenőrzés: az IFD1 tagjai")
    kezdet = blokk.u32(tagek[4].hely + 8)
    hossz = blokk.u32(tagek[5].hely + 8)
    if hossz != len(jpeg) or kimenet[kezdet : kezdet + hossz] != jpeg:
        raise TiffHiba("önellenőrzés: a bélyegkép bájtjai")
    if kimenet[kezdet + hossz :] != (b"\x00" if len(jpeg) % 2 else b""):
        raise TiffHiba("önellenőrzés: a bélyegkép nem a blokk végén áll")


def _exif_ifd(
    blokk: _Blokk, exif_mutato: _Bejegyzes | None
) -> tuple[list[_Bejegyzes], int]:
    if exif_mutato is None:
        return [], 0
    if exif_mutato.tipus not in (LONG, 13) or exif_mutato.darab != 1:
        raise TiffHiba("ExifIFD-mutató típusa")
    return blokk.ifd(blokk.u32(exif_mutato.hely + 8))


def _interop_ifd(
    blokk: _Blokk, exif: list[_Bejegyzes]
) -> tuple[_Bejegyzes | None, list[_Bejegyzes], int] | None:
    """Az Exif IFD `0xa005` mutatója, a mutatott Interop IFD tagjei és
    következő-mutatója. `(None, [], 0)`: nincs mutató; `None`: a mutató
    érvénytelen, kétszer szerepel, vagy a táblája nem olvasható — ilyenkor az
    Interop IFD-hez nem nyúlunk (második mutatót sem adunk mellé)."""
    mutatok = [b for b in exif if b.tag == _INTEROP_MUTATO]
    if not mutatok:
        return None, [], 0
    if len(mutatok) > 1:
        # az első mutató táblája ettől még olvasott: a `_cel_szabad` védi
        _mutatott_ifd(blokk, mutatok[0])
        return None
    if mutatok[0].tipus not in (LONG, 13) or mutatok[0].darab != 1:
        return None
    try:
        tagek, kovetkezo = blokk.ifd(blokk.u32(mutatok[0].hely + 8))
    except TiffHiba:
        return None
    return mutatok[0], tagek, kovetkezo


def frissitett_tiff(
    tiff: bytes | None,
    valtozasok: list[Valtozas],
    *,
    elonezet: Callable[[], bytes | None] | None = None,
    uj_ifd1: Callable[[], bytes | None] | None = None,
) -> bytes:
    """A frissített TIFF-blokk (`tiff=None`: új, üres blokkból építve).

    `elonezet`: ha van IFD1 JPEG-előnézet, ez adja az újat (lustán, mert
    dekódolás kell hozzá); `None` visszatérésnél a forrásé marad.
    `uj_ifd1` (#3998; `elonezet`-tel nem adható meg): az IFD1 újraépül, a
    forrásé nem kerül át; a hívott függvény a bélyegkép JPEG-je, vagy `None`
    (akkor nincs IFD1).
    Hibánál `TiffHiba`."""
    if elonezet is not None and uj_ifd1 is not None:
        raise TiffHiba("elonezet és uj_ifd1 együtt nem adható meg")
    forras = tiff if tiff is not None else _URES_TIFF
    blokk = _Blokk(forras)
    ifd0_off = blokk.u32(4)
    ifd0, ifd1_off = blokk.ifd(ifd0_off)
    exif_valtozasok = [v for v in valtozasok if v.ifd == "Exif"]
    interop_valtozasok = [v for v in valtozasok if v.ifd == "Interop"]
    if any(not v.csak_ha_hianyzik for v in interop_valtozasok):
        raise TiffHiba("az Interop IFD-be csak hiányzó tag adható")
    exif_mutato = next((b for b in ifd0 if b.tag == _EXIF_MUTATO), None)
    # minden érintett IFD-tábla a helyben írás ELŐTT beolvasva: a célkorlát
    # (`_cel_szabad`) mindegyiket ismeri
    if exif_valtozasok or interop_valtozasok:
        exif, exif_kov = _exif_ifd(blokk, exif_mutato)
    else:
        exif, exif_kov = _mutatott_ifd(blokk, exif_mutato), 0
    # a GPS- és az InteropIFD táblája (és értékei) is olvasott: érvénytelen
    # mutatónál kimarad
    _mutatott_ifd(blokk, next((b for b in ifd0 if b.tag == _GPS_MUTATO), None))
    interop = _interop_ifd(blokk, exif)
    ifd1 = _ifd1_tagek(blokk, ifd1_off)
    elonezet_csere = False
    ifd1_ujra = uj_ifd1 is not None
    belyegkep = uj_ifd1() if uj_ifd1 is not None else None
    if ifd1_ujra:
        _regi_elonezet_torlese(blokk, ifd1)
    elif ifd1 and elonezet is not None:
        uj_kep = elonezet()
        if uj_kep:
            elonezet_csere = _elonezet_csere(blokk, ifd1, uj_kep)
    csonk = blokk.eredeti_hossz

    uj0 = _alkalmaz(blokk, ifd0, [v for v in valtozasok if v.ifd == "0th"])
    if not ifd1_ujra:  # az újraépülő IFD1-be a régi tagek írása fölösleges
        _helyben_1st(blokk, ifd1, [v for v in valtozasok if v.ifd == "1st"])
    uj_exif: dict[int, tuple[int, int, bytes]] = {}
    interop_mutato = False
    if exif_valtozasok:
        uj_exif = _alkalmaz(blokk, exif, exif_valtozasok)
    if interop_valtozasok and interop is not None:
        # az Interop IFD az Exif IFD ELŐTT: a mutatója az Exif IFD másolatába is
        # a JELENLEGI bájtokból kerül át
        mutato, interop_tagek, interop_kov = interop
        uj_interop = _alkalmaz(blokk, interop_tagek, interop_valtozasok)
        if uj_interop:
            interop_off = _athelyez(blokk, interop_tagek, uj_interop, interop_kov)
            interop_mutato = True
            if mutato is not None:
                blokk.ir_helyben(mutato.hely + 8, blokk.egesz(LONG, interop_off))
            else:
                uj_exif[_INTEROP_MUTATO] = (LONG, 1, blokk.egesz(LONG, interop_off))
    if uj_exif:
        uj_off = _athelyez(blokk, exif, uj_exif, exif_kov)
        if exif_mutato is not None:
            blokk.ir_helyben(exif_mutato.hely + 8, blokk.egesz(LONG, uj_off))
        else:
            uj0[_EXIF_MUTATO] = (LONG, 1, blokk.egesz(LONG, uj_off))
    ifd0_hely = ifd0_off
    if uj0:
        ifd0_hely = _athelyez(blokk, ifd0, uj0, ifd1_off)
        blokk.buf[4:8] = blokk.egesz(LONG, ifd0_hely)
    if ifd1_ujra:
        # az IFD1 és a bélyegkép a LEGVÉGÉN: minden más hozzáfűzés előttük áll
        if belyegkep:
            _ifd0_kovetkezo(blokk, ifd0_hely, _ifd1_epites(blokk, belyegkep), bool(uj0))
        elif ifd1_off:
            _ifd0_kovetkezo(blokk, ifd0_hely, 0, bool(uj0))
    kimenet = bytes(blokk.buf)
    if ifd1_ujra:
        _ellenoriz_ifd1(kimenet, belyegkep or None)
    if tiff is not None:
        _ellenoriz(forras, blokk, csonk)
        _ellenoriz_szerkezet(
            forras,
            kimenet,
            _szandekolt(valtozasok, elonezet_csere, interop_mutato),
            ifd1_ujra,
        )
    return kimenet
