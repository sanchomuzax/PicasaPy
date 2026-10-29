"""Az IFD bővített másolata a blokk végére, és az IFD1 újraépítése (#3968,
#3998, #3999). A régi IFD árván marad a helyén; csak a rá mutató eltolás változik.
"""

from __future__ import annotations

import struct

from picasapy.metadata.tiff_blokk import (
    LONG,
    SHORT,
    _IFD1_TAGEK,
    _JPEG_ELONEZET,
    _JPEG_ELONEZET_HOSSZ,
    _TIPUS_MERET,
    TiffHiba,
    _Bejegyzes,
    _Blokk,
)


_RACIONALIS = 5


def _rendez(sorok: list[tuple]) -> list[tuple]:
    """Az érvényes típusú sorok tag szerint (stabilan: az azonos tagek sorrendje
    marad); az érvénytelen (0-s vagy ismeretlen) típusú sor a forrásban ELŐTTE
    álló érvényes sor után marad, a forrás végén álló a végén (#3999). Így az
    IFD elejére csak az kerülhet, ami a forrásban is elöl állt - az IFD elején
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
