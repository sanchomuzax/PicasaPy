"""A GPU pontonkénti-lánc CPU-oldali uniform-előállítása (#22).

A `build_finetune2_lut()` egy szintetikus rámpa-képen futtatja a valódi
`apply_finetune2()`-t — ez a teszt azt igazolja, hogy a kapott LUT
alkalmazása egy VALÓS (nem rámpa-) képre bájtra pontosan ugyanazt adja,
mint a `apply_finetune2()` közvetlen hívása. Ha ez teljesül, a GPU-shader
(ami ezt a LUT-ot textúraként mintavételezi) garantáltan pixel-hű a
CPU-referenciához — feltéve, hogy a shader helyesen mintavételez (ld. a
QML-oldali parity-tesztet, ha a futtatókörnyezet engedi)."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import (
    LUT_SIZE,
    apply_finetune2,
    build_finetune2_lut,
    build_point_pipeline_uniforms,
    saturation_gain,
)


def _apply_channel_lut(image: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """A shaderbeli hármas textúra-mintavételezés numpy-s megfelelője:
    csatornánként a LUT SAJÁT oszlopát olvassa, a bemeneti csatorna saját
    értékén indexelve — pontosan azt teszi, amit a fragment shader
    `texture(lut, vec2(r, 0.5)).r` stílusú hívásai végeznének."""
    red = lut[image[..., 0], 0]
    green = lut[image[..., 1], 1]
    blue = lut[image[..., 2], 2]
    return np.stack([red, green, blue], axis=-1)


class TestBuildFinetune2Lut:
    def test_lut_shape_and_dtype(self):
        lut = build_finetune2_lut(fill=0.3, highlights=0.1, shadows=0.1, temperature=0.2)
        assert lut.shape == (LUT_SIZE, 3)
        assert lut.dtype == np.uint8

    def test_identity_when_all_zero(self):
        lut = build_finetune2_lut()
        ramp = np.arange(LUT_SIZE, dtype=np.uint8)
        np.testing.assert_array_equal(lut[:, 0], ramp)
        np.testing.assert_array_equal(lut[:, 1], ramp)
        np.testing.assert_array_equal(lut[:, 2], ramp)

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"fill": 0.5},
            {"highlights": 0.4},
            {"shadows": 0.3},
            {"temperature": -0.6},
            {"temperature": 0.8},
            {"fill": 0.25, "highlights": 0.1, "shadows": 0.1, "temperature": -0.3},
            {"neutral": (200, 190, 150), "temperature": 0.1},
        ],
    )
    def test_lut_matches_direct_cpu_render_on_real_image(self, kwargs):
        """A LUT-alkalmazás (csatornánkénti textúra-mintavétel modellje)
        PONTOSAN egyezik a közvetlen `apply_finetune2()`-vel egy nem-rámpa
        (véletlen) képen — ez a parity-garancia lényege."""
        rng = np.random.default_rng(1234)
        image = rng.integers(0, 256, size=(17, 23, 3), dtype=np.uint8)
        lut = build_finetune2_lut(**kwargs)
        via_lut = _apply_channel_lut(image, lut)
        direct = apply_finetune2(
            image,
            fill=kwargs.get("fill", 0.0),
            highlights=kwargs.get("highlights", 0.0),
            shadows=kwargs.get("shadows", 0.0),
            neutral=kwargs.get("neutral"),
            temperature=kwargs.get("temperature", 0.0),
        )
        np.testing.assert_array_equal(via_lut, direct)


class TestSaturationGain:
    def test_zero_strength_is_identity_gain(self):
        assert saturation_gain(0.0) == pytest.approx(1.0)

    def test_full_desaturate_gain_is_zero(self):
        assert saturation_gain(-1.0) == pytest.approx(0.0)

    def test_clamps_out_of_range(self):
        assert saturation_gain(5.0) == saturation_gain(1.0)
        assert saturation_gain(-5.0) == saturation_gain(-1.0)


class TestBuildPointPipelineUniforms:
    def test_defaults_are_identity(self):
        uniforms = build_point_pipeline_uniforms()
        ramp = np.arange(LUT_SIZE, dtype=np.uint8)
        np.testing.assert_array_equal(uniforms.lut[:, 0], ramp)
        assert uniforms.sat_gain == pytest.approx(1.0)
        assert uniforms.bw_mix == pytest.approx(0.0)

    def test_black_and_white_sets_bw_mix(self):
        uniforms = build_point_pipeline_uniforms(black_and_white=True)
        assert uniforms.bw_mix == pytest.approx(1.0)

    def test_saturation_feeds_through_to_gain(self):
        uniforms = build_point_pipeline_uniforms(saturation=-1.0)
        assert uniforms.sat_gain == pytest.approx(0.0)
