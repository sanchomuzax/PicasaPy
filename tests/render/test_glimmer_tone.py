"""#381: `glimmer_tone` — Vignette/Matte/HDR/LocalContrast/CrossProcess/
Sixties/HeatMap/NightVision/TwoTone/QuantizePalette min/alap/max
határeset-tesztjei, a `filterdesc-registry.md` 4.2 tartományai szerint.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_tone as t


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(9)
    img = rng.integers(20, 235, size=(48, 64, 3), dtype=np.uint8)
    img[:16, :, 0] = 220
    return img


def _assert_valid(result, image):
    assert result.dtype == np.uint8
    assert result.shape[2] == 3


class TestVignetteMatte:
    @pytest.mark.parametrize("blur,strength,fade", [(0.0, 1.0, 0.0), (35.0, 1.4, 0.0), (50.0, 2.0, 100.0)])
    def test_vignette_hatarok(self, image, blur, strength, fade):
        _assert_valid(t.apply_vignette(image, blur=blur, strength=strength, fade=fade), image)

    @pytest.mark.parametrize("blur,strength,fade", [(0.0, 1.0, 0.0), (40.0, 1.2, 0.0), (50.0, 2.0, 100.0)])
    def test_matte_hatarok(self, image, blur, strength, fade):
        _assert_valid(t.apply_matte(image, blur=blur, strength=strength, fade=fade), image)

    def test_vignette_fade_100_valtozatlan(self, image):
        result = t.apply_vignette(image, fade=100.0)
        np.testing.assert_array_equal(result, image)

    def test_vignette_szel_sotetebb_kozepnel(self):
        white = np.full((60, 80, 3), 255, dtype=np.uint8)
        result = t.apply_vignette(white)
        assert int(result[30, 40, 0]) >= int(result[0, 40, 0])


class TestHdrLocalContrast:
    @pytest.mark.parametrize("radius,strength", [(1.3, 1.0), (20.0, 3.0), (80.0, 7.0)])
    def test_hdr_hatarok(self, image, radius, strength):
        _assert_valid(t.apply_hdr(image, radius=radius, strength=strength), image)

    def test_hdr_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_hdr(image, fade=100.0), image)

    @pytest.mark.parametrize("radius,strength", [(1.3, 1.0), (15.0, 1.5), (40.0, 3.0)])
    def test_local_contrast_hatarok(self, image, radius, strength):
        _assert_valid(t.apply_local_contrast(image, radius=radius, strength=strength), image)


class TestCrossProcess:
    @pytest.mark.parametrize("fade", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, fade):
        _assert_valid(t.apply_crossprocess(image, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_crossprocess(image, fade=100.0), image)

    def test_fade_0_valtoztat(self, image):
        assert not np.array_equal(t.apply_crossprocess(image, fade=0.0), image)


class TestSixties:
    @pytest.mark.parametrize("fade,rounded", [(0.0, False), (20.0, True), (100.0, True)])
    def test_hatarok(self, image, fade, rounded):
        _assert_valid(t.apply_sixties(image, fade=fade, rounded=rounded), image)

    def test_rounded_sarok_szinu(self, image):
        result = t.apply_sixties(image, fade=0.0, rounded=True, color=(1, 2, 3))
        assert tuple(result[0, 0]) == (1, 2, 3)


class TestHeatMap:
    @pytest.mark.parametrize("hue,fade", [(-180.0, 0.0), (0.0, 0.0), (180.0, 100.0)])
    def test_hatarok(self, image, hue, fade):
        _assert_valid(t.apply_heatmap(image, hue=hue, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_heatmap(image, fade=100.0), image)


class TestNightVision:
    @pytest.mark.parametrize(
        "brightness,contrast,fade", [(-50.0, -50.0, 0.0), (0.0, 0.0, 0.0), (50.0, 50.0, 100.0)]
    )
    def test_hatarok(self, image, brightness, contrast, fade):
        _assert_valid(t.apply_nightvision(image, brightness=brightness, contrast=contrast, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_nightvision(image, fade=100.0), image)


class TestTwoTone:
    @pytest.mark.parametrize(
        "brightness,contrast,fade", [(-95.0, 0.0, 0.0), (0.0, 20.0, 0.0), (95.0, 100.0, 100.0)]
    )
    def test_hatarok(self, image, brightness, contrast, fade):
        _assert_valid(t.apply_twotone(image, brightness=brightness, contrast=contrast, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_twotone(image, fade=100.0), image)


class TestQuantizePalette:
    @pytest.mark.parametrize("steps,smoothing,fade", [(2.0, 0.0, 0.0), (8.0, 80.0, 0.0), (30.0, 100.0, 100.0)])
    def test_hatarok(self, image, steps, smoothing, fade):
        _assert_valid(t.apply_quantizepalette(image, steps=steps, smoothing=smoothing, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_quantizepalette(image, fade=100.0), image)
