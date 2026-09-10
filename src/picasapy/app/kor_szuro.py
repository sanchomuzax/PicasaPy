"""A keresősáv idő-csúszkája: KOR-szűrő (#1830).

## Amit a bináris mond, és amit a felirat NEM

A csúszka felirata az eredetiben „Filter by date range"
(`searchcontainer.tre:101–102`), ami **tartományt** sejtet — a viselkedés
viszont más: a csúszka egyetlen értéke **maximális KORT** ad meg. A
félrevezető felirat az EREDETI sajátja, nem fordítási hiba nálunk.

```
s == 0    →  NINCS kor-szűrés
egyébként →  napok = 2 ^ (13 · (1 − s)) + 1
             vágópont = MOST − napok
```

A képlet **két egymástól független** helyen azonos: a találati fejléc
feliratát építő `0x0066345c`-ben és a tényleges szűrőben (`0x0065ee3f`, a
`0x0065d010` keresés-végrehajtóban) — az utóbbi ténylegesen szűkíti a
találatokat, tehát nem csak feliratról van szó. A három konstans a `.text`
szakaszból olvasva: `0xcf4c08 = 13.0`, `0xcf3a48 = 2.0`, `0xc7e328 = 1.0`.

A mértékegység szabálya (`0x006634b0`) mind **csonkolt** (nulla felé
kerekített) egész — ez nem stílus: 29,9 nap „29 napos", nem „30".

Spec: `docs/specs/picasa-kereses-modok.md`, „Az idő-csúszka" szakasz.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Callable

#: `2 ^ (13 · (1 − s)) + 1` — a három konstans a binárisból (ld. a fejlécet).
ALAP = 2.0
KITEVO_SZORZO = 13.0
ELTOLAS = 1.0

#: A mértékegység-váltás küszöbei, szintén mérve (`0x006634b0`).
_NAP_HATAR = 30.0
_HET_HOSSZ = 7.0
_HET_HATAR = 10
_HONAP_HOSSZ = 30.0
_HONAP_HATAR = 12
_EV_HOSSZ = 365.0


def napok(s: float) -> float | None:
    """A csúszka nyers `[0, 1]` értékéből a megengedett legnagyobb KOR napban.

    `None`, ha nincs szűrés (`s == 0`) — ez az eredeti nulla-ága, nem a mi
    kényelmi döntésünk.
    """
    if not 0.0 <= s <= 1.0:
        raise ValueError(f"A csúszka értéke 0 és 1 közé esik: {s}")
    if s == 0.0:
        return None
    return ALAP ** (KITEVO_SZORZO * (1.0 - s)) + ELTOLAS


def vagopont(nap: float, most: datetime) -> datetime:
    """`MOST − napok` — a szűrő vágópontja.

    A `nap` szándékosan `float`: az eredeti nap-egységű `double`-lal
    számol (ugyanaz az ábrázolás, mint a `.picasa.ini` `date=` kulcsában),
    tehát a fél nap is fél napot jelent.
    """
    return most - timedelta(days=nap)


def felirat(nap: float, tr: Callable[[str], str]) -> str:
    """A találati fejléc szövege a `.tre` négy kulcsából.

    A `tr` befecskendezett fordító (a `formatting.filter_status_text`
    mintája), hogy ez a modul Qt nélkül is mérhető legyen.

    ⚠️ A hónap-ág feltétele `hónap ≤ 12 **VAGY** év == 0` — a `VAGY` mérve
    van, és nem díszítés: 370 napnál a hónap 12, az év 1, és az eredeti
    ilyenkor még hónapot ír. `ÉS`-re átírva a 370 nap „1 éves"-re fordulna.
    """
    if nap < _NAP_HATAR:
        #: `CThumUI::searchpicsdaysold`
        return tr("Pictures up to %d days old.") % math.trunc(nap)
    hetek = math.trunc(nap / _HET_HOSSZ)
    if hetek < _HET_HATAR:
        #: `CThumUI::searchpicswksold`
        return tr("Pictures up to %d weeks old.") % hetek
    honapok = math.trunc(nap / _HONAP_HOSSZ)
    evek = math.trunc(nap / _EV_HOSSZ)
    if honapok <= _HONAP_HATAR or evek == 0:
        #: `CThumUI::searchpicsmosold`
        return tr("Pictures up to %d months old.") % honapok
    #: `CThumUI::searchpicsyearsold`
    return tr("Pictures up to %d years old.") % evek


__all__ = ["ALAP", "ELTOLAS", "KITEVO_SZORZO", "felirat", "napok", "vagopont"]
