"""#3613: a Fekete-fehér (`bw=1;`) effekt a natív egész lumát számolja.

A `bw` callback (`0x008f84c0`) a közös telítetlenítőt (`0x009a9550`)
`w = 0x100` súllyal hívja (`docs/specs/filters-decoded.md`, „`bw` = egész
luma"):

    Y  = (77·R + 151·G + 28·B) >> 8          ; csonkítva
    C' = C + (((Y − C) · w) >> 8)            ; w = 256  ⇒  C' = Y

A korábbi `rint(0,299·R + 0,587·G + 0,114·B)` a színfoltos tesztképen a
képpontok 37,5%-án legfeljebb 2 szinttel eltért a Picasa 3.9.141 exportjától
(Colab #43). A foltértékek a jegy kiolvasó kommentjéből valók; a
golden-összevetést (`compare_render.py pair … --filters "bw=1;"`) a helyi
kör végzi, mert a #43 exportja itt nem érhető el.
"""

# rontás-kontroll: az `apply_bw` visszaírva a régi `rint` Rec.601-re → 10
# failed (a hat folt, a csonkítás, a véletlen kép, a lánc és a
# megjelenítési mód egyezése); a `>> 8` előtt `+ 128` (kerekítés) → 9 failed;
# a kék súly 28 helyett 29 → 9 failed.

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.color import apply_bw
from picasapy.render.display_modes import apply_display_bw


def _folt(rgb: tuple[int, int, int]) -> np.ndarray:
    return np.full((4, 5, 3), rgb, dtype=np.uint8)


def _nativ_bw(image: np.ndarray) -> np.ndarray:
    """A spec képlete szó szerint: `C + (((Y − C)·w) >> 8)`, `w = 256`."""
    c = image.astype(np.int64)
    y = (77 * c[..., 0] + 151 * c[..., 1] + 28 * c[..., 2]) >> 8
    w = 0x100
    ki = c + (((y[..., np.newaxis] - c) * w) >> 8)
    return ki.astype(np.uint8)


#: (folt, a Picasa kimenete, a régi `rint` Rec.601 kimenete) — #3613 komment
FOLTOK = [
    pytest.param((0, 0, 255), 27, 29, id="kek"),
    pytest.param((255, 255, 0), 227, 226, id="sarga"),
    pytest.param((0, 255, 255), 178, 179, id="cian"),
    pytest.param((255, 0, 255), 104, 105, id="bibor"),
    pytest.param((60, 90, 150), 87, 88, id="60-90-150"),
    pytest.param((120, 60, 140), 86, 87, id="120-60-140"),
]


class TestFoltok:
    @pytest.mark.parametrize(("rgb", "picasa", "regi"), FOLTOK)
    def test_a_folt_a_picasa_erteket_adja(self, rgb, picasa, regi):
        ki = apply_bw(_folt(rgb))
        assert np.all(ki == picasa)
        # a régi modell tényleg mást adott — különben a próba semmit nem mér
        r, g, b = rgb
        assert int(np.rint(0.299 * r + 0.587 * g + 0.114 * b)) == regi != picasa


class TestKeplet:
    def test_csonkit_nem_kerekit(self):
        # kék: 28·255 = 7140, / 256 = 27,89 → csonkítva 27 (kerekítve 28)
        assert np.all(apply_bw(_folt((0, 0, 255))) == 27)
        assert round(7140 / 256) == 28

    def test_mindharom_csatorna_ugyanaz(self):
        rng = np.random.default_rng(3613)
        ki = apply_bw(rng.integers(0, 256, size=(16, 16, 3), dtype=np.uint8))
        assert np.array_equal(ki[..., 0], ki[..., 1])
        assert np.array_equal(ki[..., 0], ki[..., 2])

    def test_a_szurke_rampa_valtozatlan(self):
        # 77 + 151 + 28 = 256, tehát Y(g,g,g) = g — nincs erősítés
        rampa = np.repeat(np.arange(256, dtype=np.uint8), 3).reshape(1, 256, 3)
        assert np.array_equal(apply_bw(rampa), rampa)

    def test_veletlen_kep_bitre_a_nativ_keplet(self):
        rng = np.random.default_rng(43)
        be = rng.integers(0, 256, size=(64, 48, 3), dtype=np.uint8)
        assert np.array_equal(apply_bw(be), _nativ_bw(be))

    def test_a_szelso_ertekek(self):
        assert np.all(apply_bw(_folt((0, 0, 0))) == 0)
        assert np.all(apply_bw(_folt((255, 255, 255))) == 255)
        assert np.all(apply_bw(_folt((255, 0, 0))) == 76)  # 19635 >> 8
        assert np.all(apply_bw(_folt((0, 255, 0))) == 150)  # 38505 >> 8

    def test_nem_mutalja_a_bemenetet(self):
        be = _folt((0, 0, 255))
        eredeti = be.copy()
        apply_bw(be)
        assert np.array_equal(be, eredeti)


class TestBekotes:
    def test_a_lanc_bw_je_a_nativ_keplet(self):
        rng = np.random.default_rng(7)
        be = rng.integers(0, 256, size=(20, 30, 3), dtype=np.uint8)
        jelentes = apply_filters(be, parse_filters("bw=1;"))
        assert np.array_equal(jelentes.image, _nativ_bw(be))

    def test_a_megjelenitesi_mod_ugyanazt_adja(self):
        """A B&W megjelenítési mód (#1657, spec 5.7) ugyanezt a lumát méri.

        Két független kiolvasás ugyanarra a képletre jutott — kereszt-
        megerősítés, mint a szépiánál (#619). A hatókör marad a különbség."""
        rng = np.random.default_rng(1657)
        be = rng.integers(0, 256, size=(32, 32, 3), dtype=np.uint8)
        assert np.array_equal(apply_bw(be), apply_display_bw(be))
