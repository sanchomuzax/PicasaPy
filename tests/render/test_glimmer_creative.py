"""#381: `glimmer_creative` — Cinemascope/Orton/PencilSketch/Holga/Lomo/IR/
Neon min/alap/max határeset-tesztjei.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_creative as c


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(21)
    img = rng.integers(20, 235, size=(64, 96, 3), dtype=np.uint8)
    img[:20, :, 0] = 220
    return img


def _assert_valid(result):
    assert result.dtype == np.uint8
    assert result.shape[2] == 3


class TestCinemascope:
    def test_letterbox_be(self, image):
        result = c.apply_cinemascope(image, letterbox=True)
        _assert_valid(result)
        assert result.shape[0] != image.shape[0] or result.shape[1] != image.shape[1]

    def test_letterbox_ki(self, image):
        result = c.apply_cinemascope(image, letterbox=False)
        _assert_valid(result)
        assert result.shape[1] == image.shape[1]

    def test_letterbox_sav_fekete(self, image):
        result = c.apply_cinemascope(image, letterbox=True)
        assert tuple(result[0, result.shape[1] // 2]) == (0, 0, 0)


class TestOrton:
    @pytest.mark.parametrize("bloom,brightness,fade", [(0.0, 0.0, 0.0), (25.0, 50.0, 0.0), (50.0, 100.0, 100.0)])
    def test_hatarok(self, image, bloom, brightness, fade):
        _assert_valid(c.apply_orton(image, bloom=bloom, brightness=brightness, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_orton(image, fade=100.0), image)


class TestPencilSketch:
    @pytest.mark.parametrize("radius,contrast,fade", [(1.3, 0.0, 0.0), (2.0, 100.0, 0.0), (5.0, 200.0, 100.0)])
    def test_hatarok(self, image, radius, contrast, fade):
        _assert_valid(c.apply_pencil_sketch(image, radius=radius, contrast=contrast, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_pencil_sketch(image, fade=100.0), image)


class TestHolga:
    @pytest.mark.parametrize("blur,grain,fade", [(0.0, 0.0, 0.0), (70.0, 30.0, 0.0), (100.0, 100.0, 100.0)])
    def test_hatarok(self, image, blur, grain, fade):
        _assert_valid(c.apply_holga(image, blur=blur, grain=grain, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_holga(image, fade=100.0), image)


class TestLomo:
    @pytest.mark.parametrize("blur,fade", [(0.0, 0.0), (50.0, 0.0), (100.0, 100.0)])
    def test_hatarok(self, image, blur, fade):
        _assert_valid(c.apply_lomo(image, blur=blur, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_lomo(image, fade=100.0), image)


class TestIr:
    @pytest.mark.parametrize("fade", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, fade):
        _assert_valid(c.apply_ir(image, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_ir(image, fade=100.0), image)


class TestNeon:
    @pytest.mark.parametrize("fade", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, fade):
        _assert_valid(c.apply_neon(image, fade=fade))

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(c.apply_neon(image, fade=100.0), image)
