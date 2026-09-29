"""#3453: a `radtint` a natív sugaras maszkkal fut (`0x0090b050` + `0x0090aeb0`).

A spec (`filters-decoded.md`, „A Feather affin leképezése — MEGFEJTVE A
KÓDBÓL", #317) szerint a `radtint` a `radblur`/`radsat` közös maszképítőjét
hívja, `FUN_0090aeb0(0, Feather)` alakban:

* a sugár `min(W, H)/2 · (Feather + 1)` — IZOTRÓP, képpontban;
* az élesség argumentuma beégetett nulla, tehát a smoothstep a normált
  sugáron végig fut, nincs külön „átmeneti sáv";
* a közép az eredeti kép, a sugáron túl a teljes szorzó-tint.

⚠️ A #3453 itt még az eredeti és a tintelt kép KEVERÉSÉT rögzítette
(`apply_radial_mask`). A #3945 kiolvasta a munkafüggvényt (`0x0090b370`):
a maszk a tint SZÍNÉT húzza a fehér felé, és a képet egyszer szorozza — ezt
a `test_radtint_munkafuggveny_3946.py` őrzi; a képkeverő teszt kikerült.

A kódunk ehelyett tengelyenként normált (elliptikus) távolságon, a
`(0,5 ± Feather/2) · r_max` sávban keverett. A 684-es golden ΔE-je:
min 11,79 → 0,70, alap 8,91 → 0,73, max 4,37 → 0,74.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.tinting import apply_radtint

SZIN = (255, 128, 64)


def test_a_sugar_izotrop_kepontban():
    """Széles képen a vízszintes és a függőleges irány azonos képpont-
    távolságra azonos súlyt kap — tengelyenkénti normálásnál nem."""
    kep = np.full((60, 200, 3), 200, dtype=np.uint8)
    ki = apply_radtint(kep, 0.5, 0.5, 0.25, SZIN)
    assert tuple(ki[30, 100 + 20]) == tuple(ki[30 + 20, 100])


def test_feather_nullanal_sincs_eles_hatar():
    """Az élesség nulla, tehát a smoothstep a középponttól a sugárig tart."""
    kep = np.full((80, 80, 3), 200, dtype=np.uint8)
    ki = apply_radtint(kep, 0.5, 0.5, 0.0, SZIN)
    kek = ki[40, 40:80, 2].astype(int)
    assert len(set(kek.tolist())) > 10
    assert np.all(np.diff(kek) <= 0)
