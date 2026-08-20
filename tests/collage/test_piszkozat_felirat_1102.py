r"""A PISZKOZAT-felirat méretezése — a natív szabály (#1102).

## Amit a bináris mond

A natív szövegrajzoló (`0x0061d350`) **nem igazít a szélességhez**:

```
ha  korlát >= a szöveg természetes szélessége:  skála = 1,0
egyébként:                                      skála = (korlát − 20) / szöveg_szélesség
```

A `20.0` a `0xcf3fa0` konstans. **A korlát a kép MAGASSÁGA.**

## Amit a két mért minta mond

| tájolás | kép | a felirat |
|---|---|---|
| **álló** (mért FÁJL) | 453 × 640 | **levágva**: `x 0…452`, nagybetű **72 kp** |
| **fekvő** (képernyőkép) | 640 × 453 | **kifér**, oldalt margóval, kisebb betűvel |

A kettő együtt zárja ki a többi magyarázatot:

- **szélességhez igazítva** → állón is kiférne. Nem fér ki. ✗
- **a magassághoz ARÁNYOS betűméret** → a szöveg szélessége is a
  magassággal skálázódna, tehát az arány állandó volna: vagy mindig
  kiférne, vagy mindig zsugorodna. A két minta ennek ellentmond. ✗
- **természetes méret + zsugorítás CSAK ha a magasság kisebb** ✓

⚠️ **A levágódás az EREDETI viselkedése, nem hiba.** Aki „javításként" a
szélességhez igazítja, ELTÉRÉST épít be — a korábbi kódunk pontosan ezt
tette, és ezért nem vágódott le soha. Ez az őr azt akadályozza meg, hogy
egy későbbi kör jóhiszeműen visszategye.
"""

from __future__ import annotations

import numpy as np

from picasapy.collage.draft_placeholder import draw_draft_label

FELIRAT = "PISZKOZAT"


def _kiterjedes(kep: np.ndarray) -> tuple[int, int, int]:
    """A rajzolt felirat (bal x, jobb x, nagybetű-magasság)."""
    oszlopok = np.nonzero(kep.max(axis=(0, 2)))[0]
    sorok = np.nonzero(kep.max(axis=(1, 2)))[0]
    return int(oszlopok.min()), int(oszlopok.max()), int(sorok.max() - sorok.min() + 1)


def _rajzolt(szeles: int, magas: int) -> np.ndarray:
    return draw_draft_label(np.zeros((magas, szeles, 3), np.uint8), FELIRAT)


class TestAlloLapon:
    """453 × 640 — a mért minta: a felirat LEVÁGÓDIK."""

    def test_a_felirat_a_kep_ket_szelen_levagodik(self):
        bal, jobb, _ = _kiterjedes(_rajzolt(453, 640))

        assert bal == 0, "a felirat nem ér a bal szélig — nincs levágás"
        assert jobb == 452, "a felirat nem ér a jobb szélig — nincs levágás"

    def test_a_nagybetu_magassag_a_mert_ertek_kozeleben(self):
        """A mért fájlon 72 kp; a rajzolónk betűtípusa nem azonos, ezért
        tűréssel."""
        _, _, nagybetu = _kiterjedes(_rajzolt(453, 640))

        assert abs(nagybetu - 72) <= 6


class TestFekvoLapon:
    """640 × 453 — a magasság kisebb a szöveg szélességénél: ZSUGORÍT."""

    def test_a_felirat_KIFER_oldalt_margoval(self):
        bal, jobb, _ = _kiterjedes(_rajzolt(640, 453))

        assert bal > 0
        assert jobb < 639

    def test_a_betu_KISEBB_mint_allo_lapon(self):
        """A zsugorítás a lényeg: ugyanaz a szöveg, kisebb betű."""
        _, _, allo = _kiterjedes(_rajzolt(453, 640))
        _, _, fekvo = _kiterjedes(_rajzolt(640, 453))

        assert fekvo < allo


class TestAZsugoritasSzabalya:
    """A korlát a MAGASSÁG — nem a szélesség, és nem a hosszabb él."""

    def test_szeles_de_ALACSONY_lapon_zsugorit(self):
        """1000 × 200: a szélesség bőven elég volna, a magasság nem."""
        bal, jobb, _ = _kiterjedes(_rajzolt(1000, 200))

        assert bal > 0 and jobb < 999, "a szélesség szerint döntött volna"

    def test_keskeny_de_MAGAS_lapon_NEM_zsugorit(self):
        """200 × 1000: a magasság elég, tehát nincs zsugorítás — és a
        keskeny képben a felirat levágódik."""
        bal, jobb, _ = _kiterjedes(_rajzolt(200, 1000))

        assert bal == 0 and jobb == 199
