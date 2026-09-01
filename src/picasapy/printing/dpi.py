"""A nyomat effektív felbontása és a „kicsi kép” figyelmeztetés (#1782).

## A lelet

A felhasználó eddig úgy nyomtathatott ki egy 640×480-as képet 8×10
hüvelykre, hogy a program egy szót sem szólt. Az eredeti Picasa
nyomtatási panelje ezzel szemben **minőség-ellenőrzést** végez: a
választott nyomatmérethez kiszámolja minden kép effektív felbontását,
megszámolja a küszöb alattiakat, és nyomtatás előtt ellenőrzésre szólít
fel (`0x00745980`, az előnézet állapotsora).

Az eredeti szövegei (`ThumbUIPrint::Smallest`, `::ReviewPrompt`) a
`docs/specs/`-ben; a megjelenítés a `PrintDialog.qml` dolga, ez a modul
csak számol — Qt-független és determinisztikus, mint a `layout.py`.

## ⚠️ A küszöb SAJÁT DÖNTÉS

Hogy hány DPI alatt számít egy kép „kicsinek", a binárisból **nincs
mérve**: a `0x00745980` a darabszámot paraméterként kapja, a küszöb a
hívóláncban van, és nem egész-összehasonlítás. A **mechanizmust**
vesszük át, a **küszöböt** magunk választjuk — ezért nem állítjuk, hogy
az eredetit másoljuk.

A választás **150 DPI**: a fotónyomtatás szokásos alsó határa. Eldöntené
a valódi értéket egy célzott dekompilációs kör (`0x007451a0` /
`0x00746170`), vagy élő megfigyelés — kis kép 8×10-re állítva, és
leolvasni, hány DPI-nél vált a mondat.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

#: A „kicsi kép" küszöbe képpont/hüvelykben. ⚠️ SAJÁT DÖNTÉS, nem mért
#: érték — ld. a modul docstringjét. Egy helyen áll, hogy a mérés
#: elkészültekor egyetlen sort kelljen átírni.
KICSI_KUSZOB_DPI = 150


class NyomatMeret(Enum):
    """A mért öt nyomatméret (`0x00743700`, `0x00743980`), hüvelykben.

    A `TARCA` az eredeti „wallet" mérete — a legkisebb a készletben."""

    M3_5X5 = (3.5, 5.0)
    M4X6 = (4.0, 6.0)
    M5X7 = (5.0, 7.0)
    M8X10 = (8.0, 10.0)
    TARCA = (2.5, 3.5)

    @property
    def szeles_huvelyk(self) -> float:
        return self.value[0]

    @property
    def magas_huvelyk(self) -> float:
        return self.value[1]


def effektiv_dpi(
    kep_szelesseg: int, kep_magassag: int, meret: NyomatMeret
) -> int:
    """Hány képpont jut egy hüvelykre, ha a képet erre a méretre nyomtatjuk.

    A kép a nyomat területére **illeszkedik**, és a nyomat elfordítható,
    ezért a kép hosszabbik oldala a nyomat hosszabbik oldalára kerül. A
    két irány közül a **rosszabbik** dönt: ott nyúlik legjobban a képpont.

    Értelmetlen (nulla vagy negatív) képméretre `0` — hiányzó adatból ne
    szülessen hamis megnyugtatás."""
    if kep_szelesseg <= 0 or kep_magassag <= 0:
        return 0
    kep_hosszu, kep_rovid = sorted((kep_szelesseg, kep_magassag), reverse=True)
    nyomat_hosszu, nyomat_rovid = sorted(
        (meret.szeles_huvelyk, meret.magas_huvelyk), reverse=True
    )
    return int(min(kep_hosszu / nyomat_hosszu, kep_rovid / nyomat_rovid))


@dataclass(frozen=True)
class MinosegOsszegzes:
    """Amit a nyomtatási panel állapotsora kiír."""

    #: a kijelölés LEGROSSZABB képének effektív felbontása
    #: (`ThumbUIPrint::Smallest` — nem átlag)
    legkisebb_dpi: int
    #: hány kép esik a küszöb alá (`ThumbUIPrint::ReviewPrompt`)
    kicsik: int
    #: a kijelölés mérete
    osszes: int

    @property
    def keszen_all(self) -> bool:
        """„You are ready to print." — csak ha van mit nyomtatni, ÉS
        egyetlen kép sem esik a küszöb alá."""
        return self.osszes > 0 and self.kicsik == 0


def minoseg_osszegzes(
    kepmeretek, meret: NyomatMeret, *, kuszob: int = KICSI_KUSZOB_DPI
) -> MinosegOsszegzes:
    """A kijelölés minőség-összegzése a választott nyomatmérethez.

    A `kepmeretek` `(szélesség, magasság)` párok sorozata. Az **ismeretlen
    méretű** kép (0 vagy hiányzó oldal) KICSINEK számít: ha nem tudjuk,
    mekkora, ne nyugtassuk meg a felhasználót."""
    parok = list(kepmeretek)
    if not parok:
        return MinosegOsszegzes(legkisebb_dpi=0, kicsik=0, osszes=0)
    dpik = [effektiv_dpi(sz, m, meret) for sz, m in parok]
    return MinosegOsszegzes(
        legkisebb_dpi=min(dpik),
        kicsik=sum(1 for d in dpik if d < kuszob),
        osszes=len(parok),
    )
