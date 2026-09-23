"""#3443: a Pixelate `BlendMode` csúszkája a natív keverési mód SORSZÁMA.

A `filterdesc.xml` `Pixelate` blokkja: `BlendMode="{_sldrBlendMode.value}"`
(`[0..9]`, alap 9) és `BlendAlpha="{1-(_sldrFade.value/100)}"`. A mód-feloldó
(`0x00bd0b40`) a számot egésszé alakítja, és az közvetlenül a módtábla
(`0x00cf0e98`) indexe: 0 Add · 1 Darken · 2 Difference · 3 Hardlight ·
4 Lighten · 5 Multiply · 6 Overlay · 7 Screen · 8 Subtract · 9 Normal. A
keverés alsó eleme a BEMENET, felső eleme a pixelesített kép (spec
`filterdesc-registry.md`, „A `BlendInstruction`" A–C).

A 684-es golden `pixelate__min` esete (`BlendMode 0`) a mód figyelmen kívül
hagyásával ΔE 23,3 volt; az Add-dal 0,78.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render import glimmer_artistic as a
from picasapy.render.chain import apply_filters
from picasapy.render.glimmer_ops import apply_blend_mode, resize_image


def _kep() -> np.ndarray:
    rng = np.random.default_rng(3443)
    return rng.integers(0, 256, size=(40, 60, 3), dtype=np.uint8)


def _pixelesitett(kep: np.ndarray, impact: float) -> np.ndarray:
    """A pixelesítés keverés nélkül, a #3443 ELŐTTI képlettel, függetlenül
    számolva (a kicsinyítés simítással, a nagyítás simítás nélkül)."""
    h, w = kep.shape[:2]
    kicsi = resize_image(kep, max(1, round(w / impact)), max(1, round(h / impact)), smoothing=True)
    return resize_image(kicsi, w, h, smoothing=False)


class TestAHaromUjMod:
    """A spec C) táblája: `b` = alsó, `t` = felső."""

    B = np.array([[[10.0, 200.0, 128.0]]], dtype=np.float32)
    T = np.array([[[60.0, 50.0, 200.0]]], dtype=np.float32)

    def test_difference(self):
        ki = apply_blend_mode(self.B, self.T, "difference")
        np.testing.assert_allclose(ki, np.abs(self.B - self.T))

    def test_subtract_az_also_mínusz_a_felso(self):
        ki = apply_blend_mode(self.B, self.T, "subtract")
        np.testing.assert_allclose(ki, np.maximum(self.B - self.T, 0.0))

    def test_hardlight_az_overlay_csereelt_argumentummal(self):
        ki = apply_blend_mode(self.B, self.T, "hardlight")
        # a két hívás MÁS alsó réteggel megy át az átlátszóság-keverőn, ezért
        # float32-pontosságú (nem bitre azonos) az egyezés
        np.testing.assert_allclose(ki, apply_blend_mode(self.T, self.B, "overlay"), rtol=1e-6)


class TestAPixelateMod:
    def test_alapertek_9_normal_a_pixelesitett_kepet_adja(self):
        """A 9 (Normal) + Fade 0 a korábbi viselkedés: maga a pixelesített kép."""
        kep = _kep()
        np.testing.assert_array_equal(a.apply_pixelate(kep, impact=4.0, fade=0.0), _pixelesitett(kep, 4.0))

    def test_0_add(self):
        kep = _kep()
        vart = np.clip(kep.astype(np.int32) + _pixelesitett(kep, 4.0), 0, 255).astype(np.uint8)
        np.testing.assert_array_equal(a.apply_pixelate(kep, impact=4.0, fade=0.0, blend_mode=0), vart)

    def test_1_darken(self):
        kep = _kep()
        vart = np.minimum(kep, _pixelesitett(kep, 4.0))
        np.testing.assert_array_equal(a.apply_pixelate(kep, impact=4.0, fade=0.0, blend_mode=1), vart)

    @pytest.mark.parametrize("sorszam", range(10))
    def test_minden_csuszkaallas_fut(self, sorszam):
        ki = a.apply_pixelate(_kep(), impact=4.0, fade=0.0, blend_mode=sorszam)
        assert ki.shape == (40, 60, 3) and ki.dtype == np.uint8

    def test_a_fade_100_a_bemenetet_adja_barmely_modban(self):
        kep = _kep()
        np.testing.assert_array_equal(a.apply_pixelate(kep, impact=4.0, fade=100.0, blend_mode=0), kep)

    @pytest.mark.parametrize("sorszam", [-1, 10, 11])
    def test_a_csuszkan_kivuli_sorszam_hiba_nem_nema_normal(self, sorszam):
        with pytest.raises(ValueError):
            a.apply_pixelate(_kep(), impact=4.0, fade=0.0, blend_mode=sorszam)


class TestALanc:
    def test_a_lanc_atadja_a_modot(self):
        """`Pixelate=1,Impact,BlendMode,Fade` — a 2. mező a mód."""
        kep = _kep()
        lancbol = apply_filters(kep, parse_filters("Pixelate=1,4.000000,0.000000,0.000000;"))[0]
        np.testing.assert_array_equal(lancbol, a.apply_pixelate(kep, impact=4.0, fade=0.0, blend_mode=0))
