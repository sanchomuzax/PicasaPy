"""Helyben írható változások: a meglévő tag felülírása a saját helyén, és az
IFD1 JPEG-előnézetének cseréje (#3964, #3966, #3968).

Ami helyben nem írható, azt `_alkalmaz` gyűjti, és az áthelyezés viszi át
(`tiff_athelyez`).
"""

from __future__ import annotations

from picasapy.metadata.tiff_blokk import (
    LONG,
    SHORT,
    _JPEG_ELONEZET,
    _JPEG_ELONEZET_HOSSZ,
    _TIPUS_MERET,
    Ertek,
    TiffHiba,
    Valtozas,
    _Bejegyzes,
    _Blokk,
)


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
    (az előnézet bájtjait is) nem fedi - ide szabad írni/cserélni.

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
