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

    def test_a_fenyero_negativ_iranyba_megy(self, image):
        # a filterdesc.xml szerint Brightness = Impact·-20/50 — NAGYOBB
        # Impact SÖTÉTEBB képet ad (issue #381 figyelmeztetése)
        low = a.apply_boost(image, impact=10.0).astype(np.int32)
        high = a.apply_boost(image, impact=90.0).astype(np.int32)
        assert high.mean() < low.mean()


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
