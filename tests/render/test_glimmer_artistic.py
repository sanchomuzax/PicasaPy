"""#381: `glimmer_artistic` — Boost/Soften/Pixelate/PicnikGrain min/alap/max
határeset-tesztjei.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_artistic as a


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(31)
    return rng.integers(20, 235, size=(48, 64, 3), dtype=np.uint8)


def _assert_valid(result, shape=None):
    assert result.dtype == np.uint8
    assert result.shape[2] == 3
    if shape is not None:
        assert result.shape == shape


class TestBoost:
    @pytest.mark.parametrize("impact", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, impact):
        _assert_valid(a.apply_boost(image, impact=impact), image.shape)

    def test_impact_0_valtozatlan(self, image):
        np.testing.assert_array_equal(a.apply_boost(image, impact=0.0), image)

    def test_a_fenyero_parameter_negativ_iranyba_no(self):
        """A `filterdesc.xml` szerint `Brightness = Impact·−20/50` — a
        `SimpleColorMatrix`-nak átadott fényerő-paraméter NAGYOBB Impact-tal
        egyre negatívabb. Izoláltan, kontraszt/telítettség nélkül mérve ez
        tényleg sötétebb kimenetet ad (ld. a #903/#904 utáni
        `test_nagyobb_impact_osszkepben_vilagosabb`-ot arról, hogy a TELJES
        `Boost`-lánc miért mégis világosodik)."""
        from picasapy.render.glimmer_ops import simple_color_matrix

        pixel = np.array([[[128, 128, 128]]], dtype=np.uint8)
        low = simple_color_matrix(pixel, brightness=10.0 * -20.0 / 50.0)
        high = simple_color_matrix(pixel, brightness=90.0 * -20.0 / 50.0)
        assert int(high[0, 0, 0]) < int(low[0, 0, 0])

    def test_nagyobb_impact_osszkepben_vilagosabb(self, image):
        """#903/#904: a `Boost` TELJES kimenete NAGYOBB Impact-nál
        VILÁGOSABB lesz, nem sötétebb — ez a `SimpleColorMatrix`
        korábbi (hibás), gyenge lineáris kontrasztjával (`k=1+c/100`)
        mérve fordítva volt, mert ott a szerény negatív fényerő
        dominált. A HELYES, táblázatos kontraszt-görbe (`Contrast =
        Impact·40/50`, csúszka 72-nél `k≈3,6`) a 63,5-ös forgáspont
        körül sokkal erősebben húzza szét a képet, mint a régi,
        128-as forgáspontú, `k≤2,0`-s közelítés — a felfutó pixelek
        255-re vágódása felülírja a szerény sötétítést. Mérve (a
        fixtúra képén): Impact=10 → átlag 140,3; Impact=90 → átlag
        159,6."""
        low = a.apply_boost(image, impact=10.0).astype(np.int32)
        high = a.apply_boost(image, impact=90.0).astype(np.int32)
        assert high.mean() > low.mean()


class TestSoften:
    @pytest.mark.parametrize("impact,fade", [(0.0, 0.0), (50.0, 50.0), (100.0, 100.0)])
    def test_hatarok(self, image, impact, fade):
        _assert_valid(a.apply_soften(image, impact=impact, fade=fade), image.shape)

    def test_impact_0_valtozatlan(self, image):
        np.testing.assert_array_equal(a.apply_soften(image, impact=0.0), image)


class TestPixelate:
    @pytest.mark.parametrize("impact,fade", [(2.0, 0.0), (20.0, 0.0), (150.0, 100.0)])
    def test_hatarok(self, image, impact, fade):
        _assert_valid(a.apply_pixelate(image, impact=impact, fade=fade), image.shape)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(a.apply_pixelate(image, fade=100.0), image)


class TestPicnikGrain:
    @pytest.mark.parametrize("grain,lighten", [(0.0, False), (10.0, False), (50.0, True)])
    def test_hatarok(self, image, grain, lighten):
        _assert_valid(a.apply_picnik_grain(image, grain=grain, lighten=lighten), image.shape)

    def test_grain_0_kis_hatasu(self, image):
        result = a.apply_picnik_grain(image, grain=0.0, lighten=False)
        assert result.shape == image.shape
