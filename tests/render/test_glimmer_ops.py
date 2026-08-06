"""#381: a közös Glimmer-primitívek (`glimmer_ops.py`/`glimmer_frame_ops.py`)
egységtesztjei — görbe-interpoláció, blend-módok, Fade-szabály, maszkolt
keverés, belső ragyogás, zaj, gradiens-leképezés, keret-primitívek.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_frame_ops as gf
from picasapy.render import glimmer_ops as g


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.integers(20, 235, size=(32, 48, 3), dtype=np.uint8)


class TestFadeRule:
    def test_fade_0_teljes_alfa(self):
        assert g.fade_alpha(0.0) == 1.0

    def test_fade_100_nulla_alfa(self):
        assert g.fade_alpha(100.0) == 0.0

    def test_fade_50_fel_alfa(self):
        assert g.fade_alpha(50.0) == pytest.approx(0.5)

    def test_fade_tartomanyon_kivul_vagva(self):
        assert g.fade_alpha(-20.0) == 1.0
        assert g.fade_alpha(150.0) == 0.0


class TestBlendModes:
    def test_normal_a_top_reteget_adja(self):
        base = np.zeros((2, 2, 3), dtype=np.float32)
        top = np.full((2, 2, 3), 200.0, dtype=np.float32)
        result = g.apply_blend_mode(base, top, "normal", 1.0)
        np.testing.assert_allclose(result, top)

    def test_multiply_feketevel_fekete(self):
        base = np.full((2, 2, 3), 200.0, dtype=np.float32)
        top = np.zeros((2, 2, 3), dtype=np.float32)
        result = g.apply_blend_mode(base, top, "multiply", 1.0)
        np.testing.assert_allclose(result, 0.0)

    def test_screen_feherrel_feher(self):
        base = np.full((2, 2, 3), 50.0, dtype=np.float32)
        top = np.full((2, 2, 3), 255.0, dtype=np.float32)
        result = g.apply_blend_mode(base, top, "screen", 1.0)
        np.testing.assert_allclose(result, 255.0)

    def test_darken_a_kisebbet_adja(self):
        base = np.array([[100.0, 100.0, 100.0]])
        top = np.array([[50.0, 150.0, 100.0]])
        result = g.apply_blend_mode(base, top, "darken", 1.0)
        np.testing.assert_allclose(result, [[50.0, 100.0, 100.0]])

    def test_lighten_a_nagyobbat_adja(self):
        base = np.array([[100.0, 100.0, 100.0]])
        top = np.array([[50.0, 150.0, 100.0]])
        result = g.apply_blend_mode(base, top, "lighten", 1.0)
        np.testing.assert_allclose(result, [[100.0, 150.0, 100.0]])

    def test_opacity_nulla_a_bazist_adja(self):
        base = np.full((2, 2, 3), 60.0, dtype=np.float32)
        top = np.full((2, 2, 3), 240.0, dtype=np.float32)
        result = g.apply_blend_mode(base, top, "overlay", 0.0)
        np.testing.assert_allclose(result, base)

    def test_ismeretlen_mod_hibat_dob(self):
        base = np.zeros((1, 1, 3), dtype=np.float32)
        with pytest.raises(ValueError):
            g.apply_blend_mode(base, base, "xyz", 1.0)


class TestMaskedBlend:
    def test_maszk_nulla_a_bazist_tartja(self):
        base = np.full((2, 2, 3), 10.0, dtype=np.float32)
        overlay = np.full((2, 2, 3), 200.0, dtype=np.float32)
        mask = np.zeros((2, 2), dtype=np.float32)
        np.testing.assert_allclose(g.masked_blend(base, overlay, mask), base)

    def test_maszk_egy_az_overlayt_adja(self):
        base = np.full((2, 2, 3), 10.0, dtype=np.float32)
        overlay = np.full((2, 2, 3), 200.0, dtype=np.float32)
        mask = np.ones((2, 2), dtype=np.float32)
        np.testing.assert_allclose(g.masked_blend(base, overlay, mask), overlay)


class TestAdjustCurves:
    def test_azonossag_valtozatlan(self, image):
        result = g.adjust_curves(image, master=((0.0, 0.0), (255.0, 255.0)))
        np.testing.assert_array_equal(result, image)

    def test_invert_curve(self, image):
        result = g.invert_curve(image)
        assert not np.array_equal(result, image)
        np.testing.assert_array_equal(g.invert_curve(result), image)


class TestInnerGlow:
    def test_alfa_nulla_valtozatlan(self, image):
        result = g.inner_glow(image, (0, 0, 0), 5.0, 5.0, 1.4, alpha=0.0)
        np.testing.assert_array_equal(result, image)

    def test_pozitiv_alfa_valtoztat(self, image):
        result = g.inner_glow(image, (0, 0, 0), 5.0, 5.0, 1.4, alpha=1.0)
        assert not np.array_equal(result, image)

    def test_szelek_sotetebbek_feher_alapon(self):
        white = np.full((40, 60, 3), 255, dtype=np.uint8)
        result = g.inner_glow(white, (0, 0, 0), 6.0, 6.0, 1.4, alpha=1.0)
        assert int(result[0, 30, 0]) < int(result[20, 30, 0])


class TestNoiseAndGradient:
    def test_zaj_determinisztikus(self, image):
        first = g.apply_noise(image, seed=5, low=0, high=50, grayscale=True, blend_alpha=1.0, blend_mode="multiply")
        second = g.apply_noise(image, seed=5, low=0, high=50, grayscale=True, blend_alpha=1.0, blend_mode="multiply")
        np.testing.assert_array_equal(first, second)

    def test_gradient_map_vegpontok(self):
        black = np.zeros((4, 4, 3), dtype=np.uint8)
        white = np.full((4, 4, 3), 255, dtype=np.uint8)
        colors = ((10, 20, 30), (200, 210, 220))
        np.testing.assert_array_equal(g.gradient_map(black, colors)[0, 0], np.array([10, 20, 30]))
        np.testing.assert_array_equal(g.gradient_map(white, colors)[0, 0], np.array([200, 210, 220]))

    def test_hsv_gradient_map_alakhelyes(self, image):
        stops = ((0.0, 240.0, 100.0, 50.0), (255.0, 0.0, 100.0, 50.0))
        result = g.hsv_gradient_map(image, stops)
        assert result.shape == image.shape and result.dtype == np.uint8


class TestCircularGradientMask:
    def test_belul_nulla_kivul_egy(self):
        mask = g.circular_gradient_mask(40, 40, 5.0, 15.0)
        assert mask[20, 20] == 0.0
        assert mask[0, 0] == 1.0

    def test_atmenet_a_kettobetween(self):
        mask = g.circular_gradient_mask(40, 40, 5.0, 15.0)
        assert 0.0 < mask[20, 27] < 1.0


class TestFrameOps:
    def test_add_ring_novel(self, image):
        result = gf.add_ring(image, 10.0, (255, 255, 255))
        assert result.shape[0] > image.shape[0]
        assert result.shape[1] > image.shape[1]

    def test_add_ring_nulla_valtozatlan(self, image):
        result = gf.add_ring(image, 0.0, (255, 255, 255))
        np.testing.assert_array_equal(result, image)

    def test_round_corners_sarok_szinnel_tolt(self):
        image = np.zeros((40, 40, 3), dtype=np.uint8)
        result = gf.round_corners(image, 10.0, (255, 255, 255))
        assert tuple(result[0, 0]) == (255, 255, 255)
        assert tuple(result[20, 20]) == (0, 0, 0)

    def test_draw_drop_shadow_novel(self, image):
        result = gf.draw_drop_shadow(image, (0, 0, 0), (255, 255, 255), 4.0, 90.0, 10.0, fade=30.0)
        assert result.shape[0] > image.shape[0] and result.shape[1] > image.shape[1]

    def test_rotate_with_pad_novel(self, image):
        result = gf.rotate_with_pad(image, 10.0, (255, 255, 255))
        assert result.shape[0] >= image.shape[0] and result.shape[1] >= image.shape[1]

    def test_rotate_zero_megtartja_meretet(self, image):
        result = gf.rotate_with_pad(image, 0.0, (255, 255, 255))
        assert result.shape == image.shape
