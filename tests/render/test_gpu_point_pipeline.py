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

from tests.support.dither import dither_nelkul
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


#: A LUT-egyezés esetei — a dither-eltérés próbája ugyanezeket futtatja.
_LUT_ESETEK = [
    {"highlights": 0.4},
    {"shadows": 0.3},
    {"temperature": -0.6},
    {"temperature": 0.8},
    {"highlights": 0.1, "shadows": 0.1, "temperature": -0.3},
    {"neutral": (200, 190, 150), "temperature": 0.1},
]


class TestBuildFinetune2Lut:
    def test_lut_shape_and_dtype(self):
        lut = build_finetune2_lut(highlights=0.1, shadows=0.1, temperature=0.2)
        assert lut.shape == (LUT_SIZE, 3)
        assert lut.dtype == np.uint8

    def test_identity_when_all_zero(self):
        lut = build_finetune2_lut()
        ramp = np.arange(LUT_SIZE, dtype=np.uint8)
        np.testing.assert_array_equal(lut[:, 0], ramp)
        np.testing.assert_array_equal(lut[:, 1], ramp)
        np.testing.assert_array_equal(lut[:, 2], ramp)

    @pytest.mark.parametrize("kwargs", _LUT_ESETEK)
    def test_lut_matches_direct_cpu_render_on_real_image(self, kwargs):
        """A LUT-alkalmazás PONTOSAN egyezik azzal a CPU-úttal, amit
        reprodukálni hivatott — egy nem-rámpa (véletlen) képen.

        ⚠️ **#956 óta a hőmérsékletnél ez nem a MENTÉSI út.** A mentés a
        natív 3×3-as mátrixszal számol, ami keveri a csatornákat, tehát egy
        csatornánkénti LUT-textúrába nem fér bele. Az előnézet ezért a
        csatornánkénti KÖZELÍTÉSSEL megy
        (`szinhomerseklet_kozelitessel=True`), és ez a próba azt köti ki,
        hogy a LUT **azt** reprodukálja hibátlanul. Hogy a közelítés milyen
        messze van a pontos úttól, azt a
        `test_a_kozelites_elteresenek_KORLATJA` méri."""
        rng = np.random.default_rng(1234)
        image = rng.integers(0, 256, size=(17, 23, 3), dtype=np.uint8)
        lut = build_finetune2_lut(**kwargs)
        via_lut = _apply_channel_lut(image, lut)
        with dither_nelkul():
            direct = apply_finetune2(
                image,
                fill=kwargs.get("fill", 0.0),
                highlights=kwargs.get("highlights", 0.0),
                shadows=kwargs.get("shadows", 0.0),
                neutral=kwargs.get("neutral"),
                temperature=kwargs.get("temperature", 0.0),
                szinhomerseklet_kozelitessel=True,
            )
        np.testing.assert_array_equal(via_lut, direct)

    @pytest.mark.parametrize("kwargs", _LUT_ESETEK)
    def test_a_dither_elteresenek_KORLATJA(self, kwargs):
        """Mennyivel tér el a GPU-előnézet a DITHERELT CPU-kimenettől (#3092)?

        A LUT-os előnézet nem ditherel, a mentés igen — ez szándékos és
        elkerülhetetlen: egy csatorna-LUT képpontonként AZONOS leképezést ad,
        a dither viszont képpontonként más mintát húz. A próba nem elrejti az
        eltérést, hanem SZÁMOT ad rá, hogy ha egyszer megnő, szóljon.

        A korlát a dither saját amplitúdója: ±delta/2 a 16 bites skálán, ami
        a `>> 8` után legfeljebb 2 szint. Ennél nagyobb eltérés már nem
        ditherből jön."""
        rng = np.random.default_rng(1234)
        image = rng.integers(0, 256, size=(17, 23, 3), dtype=np.uint8)
        via_lut = _apply_channel_lut(
            image, build_finetune2_lut(**kwargs)
        ).astype(np.int16)
        ditherelt = apply_finetune2(
            image,
            fill=kwargs.get("fill", 0.0),
            highlights=kwargs.get("highlights", 0.0),
            shadows=kwargs.get("shadows", 0.0),
            neutral=kwargs.get("neutral"),
            temperature=kwargs.get("temperature", 0.0),
            szinhomerseklet_kozelitessel=True,
        ).astype(np.int16)

        elteres = int(np.max(np.abs(via_lut - ditherelt)))
        assert elteres <= 2, (
            f"a GPU-előnézet és a ditherelt CPU-kimenet {elteres} szinttel "
            "tér el — ez több, mint a dither amplitúdója (#3092)"
        )

    @pytest.mark.parametrize("temperature", [-0.6, -0.3, 0.1, 0.8])
    def test_a_kozelites_elteresenek_KORLATJA(self, temperature):
        """Mekkora a GPU-előnézet és a MENTETT kép eltérése (#956)?

        A kérdés jogos: az előnézet közelítéssel megy, a mentés pontosan. A
        próba nem elrejti ezt, hanem **számot ad rá**, hogy ha egyszer
        megnő, akkor szóljon.

        A 30-as korlát mért: a csatornánkénti közelítés a hideg végen hagyja
        ki a legtöbbet (ott a mátrix átlón kívüli tagja 11,8 %). Az ÁTLAGOS
        eltérés ennél nagyságrendekkel kisebb — az előnézet célja a gyors
        visszajelzés, nem a végleges kép."""
        rng = np.random.default_rng(99)
        image = rng.integers(0, 256, size=(17, 23, 3), dtype=np.uint8)
        kozelites = apply_finetune2(
            image,
            fill=0.0,
            highlights=0.0,
            shadows=0.0,
            neutral=None,
            temperature=temperature,
            szinhomerseklet_kozelitessel=True,
        ).astype(int)
        pontos = apply_finetune2(
            image,
            fill=0.0,
            highlights=0.0,
            shadows=0.0,
            neutral=None,
            temperature=temperature,
        ).astype(int)
        elteres = np.abs(kozelites - pontos)
        assert elteres.max() <= 30, f"a közelítés {elteres.max()} szintre tért el"
        assert elteres.mean() <= 8, f"átlagos eltérés {elteres.mean():.2f}"

    @pytest.mark.parametrize("fill", [0.25, 1.0])
    def test_nonzero_fill_is_rejected(self, fill):
        """#551: a Derítőfény világosság-vezérelt, tehát nem LUT-osítható —
        a GPU-út ilyenkor a CPU-tól ELTÉRŐ képet adna, ezért tiltott."""
        with pytest.raises(ValueError, match="fill"):
            build_finetune2_lut(fill=fill)


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
