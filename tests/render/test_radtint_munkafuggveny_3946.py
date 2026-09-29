"""#3946: a `radtint` munkafüggvénye (`0x0090b370`) és a CSONKOLÓ sugaras tábla.

A spec (`filters-decoded.md`, „⛳ A `radtint` munkafüggvénye kiolvasva",
#3945) szerint:

* a közös súlytábla (`0x0090aeb0`) csonkol: a `fistp` előtt `or eax, 0xc00`
  állítja csonkolásra a vezérlőszót — `tabla[i] = trunc((3 − 2v)·v²·255)`;
* a `radtint` középpontja csonkolt: `cx = trunc(W·x)`, `cy = trunc(H·y)`;
* a maszk NEM két képet kever, hanem a tint SZÍNÉT húzza a fehér felé:
  `t′ = 255 − (((255 − t)·(256 − w)) >> 8)`, és a képet egyszer szorozza:
  `ki = (be·t′) >> 8`; a táblán kívül (`idx > 0x3ff`) `ki = (be·t) >> 8`.
  (Az alfát a natív érintetlenül hagyja; a mi csővezetékünk RGB.)
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from picasapy.render.radial_mask import RADIAL_TABLE_SIZE, radial_weight_table
from picasapy.render.tinting import apply_radtint

SZIN = (255, 128, 64)


def _spec_tabla(width: int, height: int, size: float, sharpness: float):
    """A `0x0090aeb0` táblája tisztán a spec szövegéből, elemenként."""
    r = min(width, height) / 2.0 * (size + 1.0)
    r2 = r * r
    shift = 0
    while r2 > 1024.0:
        r2 *= 0.5
        shift += 1
    tabla = []
    for i in range(1024):
        t = math.sqrt(i * (1.0 / 1024.0) * (1024.0 / r2))
        v = 0.5 + (1.0 / (1.0 - sharpness * 0.99)) * (t - 0.5)
        v = 1.0 - min(max(v, 0.0), 1.0)
        tabla.append(math.trunc((3.0 - 2.0 * v) * v * v * 255.0))
    return tabla, shift


def _spec_radtint(kep: np.ndarray, x: float, y: float, feather: float, szin):
    """A `0x0090b370` munkafüggvénye képpontonként, a spec szerint."""
    height, width = kep.shape[:2]
    tabla, shift = _spec_tabla(width, height, feather, 0.0)
    cx = math.trunc(width * x)
    cy = math.trunc(height * y)
    ki = np.empty_like(kep)
    for sor in range(height):
        for oszlop in range(width):
            idx = ((oszlop - cx) ** 2 + (sor - cy) ** 2) >> shift
            for c in range(3):
                t = szin[c]
                if idx <= 0x3FF:
                    w = tabla[idx]
                    t = 255 - (((255 - t) * (256 - w)) >> 8)
                ki[sor, oszlop, c] = (int(kep[sor, oszlop, c]) * t) >> 8
    return ki


class TestCsonkoloTabla:
    @pytest.mark.parametrize(
        ("width", "height", "size", "sharpness"),
        [(400, 400, 0.0, 0.0), (1600, 1200, 0.3, 0.0), (90, 40, 0.25, 0.0),
         (640, 480, 1.0, 0.7)],
    )
    def test_a_tabla_a_spec_szerint_csonkol(self, width, height, size, sharpness):
        vart, vart_shift = _spec_tabla(width, height, size, sharpness)
        tabla, shift = radial_weight_table(width, height, size, sharpness)
        assert shift == vart_shift
        assert tabla.tolist() == vart

    def test_a_tort_resz_lefele_megy(self):
        # 400×400, Size 0 (shift 6): az i = 156 / 352 elemnél a smoothstep
        # 127,65… / 39,71… — kerekítve 128 / 40 (a régi `np.rint`), csonkolva
        # 127 / 39.
        tabla, _ = radial_weight_table(400, 400, 0.0, 0.0)
        assert [int(tabla[i]) for i in (0, 39, 156, 352)] == [255, 215, 127, 39]
        assert len(tabla) == RADIAL_TABLE_SIZE


class TestRadtintMunkafuggveny:
    @pytest.mark.parametrize("feather", [0.0, 0.25, 1.0])
    @pytest.mark.parametrize(("x", "y"), [(0.5, 0.5), (0.3, 0.6), (0.77, 0.19)])
    def test_bitre_egyezik_a_spec_munkafuggvenyevel(self, feather, x, y):
        rng = np.random.default_rng(3946)
        kep = rng.integers(0, 256, size=(37, 53, 3), dtype=np.uint8)
        vart = _spec_radtint(kep, x, y, feather, SZIN)
        np.testing.assert_array_equal(apply_radtint(kep, x, y, feather, SZIN), vart)

    def test_a_kozeppont_csonkolt(self):
        # W·x = 10,7 → a csonkolt középpont a 10. oszlop, a kerekített a 11.
        # Egyenletes képen a középpont képpontja `(be·255) >> 8` (w = 255),
        # a szomszédja már kisebb súlyt kap — a kettő szétválik.
        kep = np.full((21, 21, 3), 200, dtype=np.uint8)
        ki = apply_radtint(kep, 10.7 / 21, 10.2 / 21, 0.0, SZIN)
        vart = _spec_radtint(kep, 10.7 / 21, 10.2 / 21, 0.0, SZIN)
        np.testing.assert_array_equal(ki, vart)

    def test_kozepen_a_tint_feher(self):
        # w = 255 → t′ = 255 − ((255 − t)·1 >> 8) = 255 minden t-re
        kep = np.full((40, 40, 3), 200, dtype=np.uint8)
        ki = apply_radtint(kep, 0.5, 0.5, 0.25, SZIN)
        assert tuple(ki[20, 20]) == ((200 * 255) >> 8,) * 3

    def test_tablan_kivul_a_teljes_tint(self):
        kep = np.full((40, 120, 3), 200, dtype=np.uint8)
        ki = apply_radtint(kep, 0.5, 0.5, 0.0, SZIN)
        assert tuple(ki[0, 0]) == tuple((200 * c) >> 8 for c in SZIN)
