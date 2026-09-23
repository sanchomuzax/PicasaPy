"""#3453: a `radtint` a natív sugaras maszkkal fut (`0x0090b050` + `0x0090aeb0`).

A spec (`filters-decoded.md`, „A Feather affin leképezése — MEGFEJTVE A
KÓDBÓL", #317) szerint a `radtint` a `radblur`/`radsat` közös maszképítőjét
hívja, `FUN_0090aeb0(0, Feather)` alakban:

* a sugár `min(W, H)/2 · (Feather + 1)` — IZOTRÓP, képpontban;
* az élesség argumentuma beégetett nulla, tehát a smoothstep a normált
  sugáron végig fut, nincs külön „átmeneti sáv";
* a közép az eredeti kép, a sugáron túl a teljes szorzó-tint.

A kódunk ehelyett tengelyenként normált (elliptikus) távolságon, a
`(0,5 ± Feather/2) · r_max` sávban keverett. A 684-es golden ΔE-je:
min 11,79 → 0,70, alap 8,91 → 0,73, max 4,37 → 0,74.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.radial_mask import apply_radial_mask
from picasapy.render.tinting import apply_radtint

SZIN = (255, 128, 64)


def _kep() -> np.ndarray:
    rng = np.random.default_rng(3453)
    return rng.integers(0, 256, size=(40, 90, 3), dtype=np.uint8)


def _teljes_tint(kep: np.ndarray) -> np.ndarray:
    return (kep.astype(np.int64) * np.array(SZIN) // 256).astype(np.uint8)


@pytest.mark.parametrize("feather", [0.0, 0.25, 1.0])
def test_a_kozos_nativ_maszkkal_kever(feather):
    kep = _kep()
    vart = apply_radial_mask(kep, _teljes_tint(kep), 0.3, 0.6, feather, 0.0)
    np.testing.assert_array_equal(apply_radtint(kep, 0.3, 0.6, feather, SZIN), vart)


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
