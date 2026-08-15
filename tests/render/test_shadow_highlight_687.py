"""Az `shadow` („Árnyék és kiemelés") natív modellje (#687) — `0x0090d3e0`.

A mag (`0x0090d170`) dekompilált: a képpont SAJÁT és az ELMOSOTT kép
világosságából számol súlyt, külön árnyék- és csúcsfény-ággal. A tesztek a
képlet horgonyértékeit és az azonosság-eseteket őrzik; a valódi
Picasa-kimenethez mért illeszkedés az `apply_shadow_highlight` docstringjében.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.shadow_highlight import apply_shadow_highlight


@pytest.fixture
def gradient() -> np.ndarray:
    """Vízszintes 0..255 rámpa, elég széles ahhoz, hogy az elmosás értelmes
    legyen (az árnyék-/csúcsfény-súly az elmosott világosságtól függ)."""
    levels = np.linspace(0, 255, 128, dtype=np.uint8).reshape(1, 128, 1)
    return np.repeat(np.repeat(levels, 32, axis=0), 3, axis=2)


class TestAzonossag:
    def test_mindket_szazalek_nullan_valtozatlan(self, gradient):
        result = apply_shadow_highlight(gradient, 0.5, 0.0, 0.0)
        assert np.array_equal(result, gradient)

    def test_a_bemenetet_nem_mutalja(self, gradient):
        eredeti = gradient.copy()
        apply_shadow_highlight(gradient, 0.5, 1.0, 1.0)
        assert np.array_equal(gradient, eredeti)

    def test_uint8_kimenet_es_alak(self, gradient):
        result = apply_shadow_highlight(gradient, 0.5, 0.5, 0.5)
        assert result.dtype == np.uint8
        assert result.shape == gradient.shape


class TestArnyekAg:
    def test_az_arnyekot_emeli(self, gradient):
        result = apply_shadow_highlight(gradient, 0.5, 1.0, 0.0)
        # a sötét negyed szintjei feljebb kerülnek
        assert int(result[16, 16, 0]) > int(gradient[16, 16, 0])

    def test_a_csucsfenyt_nem_bantja(self, gradient):
        result = apply_shadow_highlight(gradient, 0.5, 1.0, 0.0)
        assert int(result[16, 120, 0]) == int(gradient[16, 120, 0])

    def test_a_teljes_fekete_helyben_marad(self, gradient):
        # a súly SZORZÓ (`c + (k·c >> 8)`), tehát a nulla nulla marad
        result = apply_shadow_highlight(gradient, 0.5, 1.0, 0.0)
        assert int(result[16, 0, 0]) == 0


class TestCsucsfenyAg:
    def test_a_csucsfenyt_lehuzza(self, gradient):
        result = apply_shadow_highlight(gradient, 0.5, 0.0, 1.0)
        assert int(result[16, 112, 0]) < int(gradient[16, 112, 0])

    def test_az_arnyekot_nem_bantja(self, gradient):
        result = apply_shadow_highlight(gradient, 0.5, 0.0, 1.0)
        assert int(result[16, 8, 0]) == int(gradient[16, 8, 0])

    def test_a_teljes_feher_helyben_marad(self, gradient):
        # a lehúzás `c − ((255 − c)·k >> 8)`, tehát a 255 nem mozdul
        result = apply_shadow_highlight(gradient, 0.5, 0.0, 1.0)
        assert int(result[16, 127, 0]) == 255


class TestMertSulySkala:
    """A csúszka → egész súly szorzója (×256) KIZÁRÓLAG mérésből ismert (a
    natív kódban az x87-veremen megy át). Ezek a horgonyértékek egy
    egyenletes foltra vonatkoznak — ott az elmosott világosság megegyezik a
    képpont sajátjával, tehát a súly kizárólag a szorzótól függ. Ha a
    `_PERCENT_SCALE` elcsúszik, ez a három szám azonnal mást ad.
    """

    def test_arnyek_100_szazalek_horgony(self):
        patch = np.full((32, 32, 3), 64, dtype=np.uint8)
        assert int(apply_shadow_highlight(patch, 0.5, 1.0, 0.0)[16, 16, 0]) == 87

    def test_arnyek_50_szazalek_horgony(self):
        patch = np.full((32, 32, 3), 64, dtype=np.uint8)
        assert int(apply_shadow_highlight(patch, 0.5, 0.5, 0.0)[16, 16, 0]) == 75

    def test_csucsfeny_100_szazalek_horgony(self):
        patch = np.full((32, 32, 3), 200, dtype=np.uint8)
        assert int(apply_shadow_highlight(patch, 0.5, 0.0, 1.0)[16, 16, 0]) == 175


class TestErossegMonotonitas:
    def test_erosebb_arnyek_tobbet_emel(self, gradient):
        gyenge = apply_shadow_highlight(gradient, 0.5, 0.3, 0.0)
        eros = apply_shadow_highlight(gradient, 0.5, 1.0, 0.0)
        assert int(eros[16, 16, 0]) > int(gyenge[16, 16, 0])

    def test_erosebb_csucsfeny_tobbet_huz(self, gradient):
        gyenge = apply_shadow_highlight(gradient, 0.5, 0.0, 0.3)
        eros = apply_shadow_highlight(gradient, 0.5, 0.0, 1.0)
        assert int(eros[16, 112, 0]) < int(gyenge[16, 112, 0])
