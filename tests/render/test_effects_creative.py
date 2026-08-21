"""A `picasapy.render.effects_creative` és `effects_creative_tone` kreatív
effektjeinek tesztjei (#329).

Ezekhez az effektekhez NINCS golden-mérés (a Picasa algoritmusa nem
publikus) — a tesztek ezért a MEGFIGYELHETŐ, kvalitatív viselkedést
rögzítik (pl. az Invert tényleg invertál, a HeatMap tényleg színez szürke
bemeneten, a QuantizePalette tényleg kevesebb egyedi színt ad), nem csak
azt, hogy a hívás lefut (false-green elkerülése).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_tone as glimmer_tone
from picasapy.render.effects_creative import (
    apply_cinemascope,
    apply_holga,
    apply_ir,
    apply_lomo,
    apply_orton,
    apply_sixties,
)
from picasapy.render.effects_creative_tone import (
    apply_crossprocess,
    apply_hdr,
    apply_heatmap,
    apply_invert,
    apply_quantizepalette,
    apply_twotone,
)
from picasapy.render.glimmer_ops import luma


def _uniform_image(
    value: int | tuple[int, int, int], height: int = 12, width: int = 16
) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


def _gradient_image(height: int = 24, width: int = 32) -> np.ndarray:
    """Determinisztikus RGB gradiens, közepes kontraszttal."""
    row = np.linspace(60, 200, width, dtype=np.uint8)
    plane = np.tile(row, (height, 1))
    return np.stack([plane, plane, plane], axis=-1).astype(np.uint8)


def _textured_image(height: int = 40, width: int = 40) -> np.ndarray:
    """Determinisztikus, több frekvenciájú szürke minta (helyi kontraszt-
    tesztekhez: sima gradiensen a CLAHE alig változtat)."""
    ys, xs = np.meshgrid(np.arange(height), np.arange(width), indexing="ij")
    pattern = 128.0 + 40.0 * np.sin(xs / 2.0) + 20.0 * np.cos(ys / 3.0)
    gray = np.clip(pattern, 0, 255).astype(np.uint8)
    return np.stack([gray, gray, gray], axis=-1)


def _checkerboard(height: int = 16, width: int = 16, cell: int = 2) -> np.ndarray:
    ys, xs = np.meshgrid(np.arange(height), np.arange(width), indexing="ij")
    black_white = (((ys // cell) + (xs // cell)) % 2 == 0).astype(np.uint8) * 255
    return np.stack([black_white] * 3, axis=-1)


_EXTREME_IMAGES = [
    pytest.param(lambda: _uniform_image(0), id="fekete"),
    pytest.param(lambda: _uniform_image(255), id="feher"),
]

_ALL_EFFECTS = [
    pytest.param(lambda image: apply_ir(image), id="ir"),
    pytest.param(lambda image: apply_lomo(image), id="lomo"),
    pytest.param(lambda image: apply_holga(image), id="holga"),
    pytest.param(lambda image: apply_cinemascope(image), id="cinemascope"),
    pytest.param(lambda image: apply_orton(image), id="orton"),
    pytest.param(lambda image: apply_sixties(image), id="sixties"),
    pytest.param(lambda image: apply_hdr(image), id="hdr"),
    pytest.param(lambda image: apply_invert(image), id="invert"),
    pytest.param(lambda image: apply_heatmap(image), id="heatmap"),
    pytest.param(lambda image: apply_crossprocess(image), id="crossprocess"),
    pytest.param(lambda image: apply_quantizepalette(image), id="quantizepalette"),
    pytest.param(lambda image: apply_twotone(image), id="twotone"),
]


class TestKozosViselkedes:
    """Minden effektre érvényes közös elvárások: alak/dtype, immutabilitás,
    szélsőséges bemenet."""

    @pytest.mark.parametrize("apply", _ALL_EFFECTS)
    def test_alak_es_dtype_megmarad(self, apply) -> None:
        image = _gradient_image()
        result = apply(image)
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    @pytest.mark.parametrize("apply", _ALL_EFFECTS)
    def test_nem_mutalja_a_bemenetet(self, apply) -> None:
        image = _gradient_image()
        original = image.copy()
        apply(image)
        np.testing.assert_array_equal(image, original)

    @pytest.mark.parametrize("apply", _ALL_EFFECTS)
    @pytest.mark.parametrize("make_image", _EXTREME_IMAGES)
    def test_szelsoseges_bemenet_nem_dob(self, apply, make_image) -> None:
        image = make_image()
        result = apply(image)
        assert result.shape == image.shape
        assert result.dtype == np.uint8


class TestApplyIr:
    def test_voros_dominancia(self) -> None:
        image = _uniform_image(128)
        result = apply_ir(image, strength=1.0)
        red, green, blue = (int(result[0, 0, channel]) for channel in range(3))
        assert red > green > blue

    def test_nulla_erosseg_identitas(self) -> None:
        image = _gradient_image()
        result = apply_ir(image, strength=0.0)
        np.testing.assert_array_equal(result, image)

    def test_negativ_erosseg_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_ir(_uniform_image(100), strength=-0.1)


class TestApplyLomo:
    def test_sarok_sotetebb_mint_a_kozep_vignetta(self) -> None:
        image = _uniform_image((180, 150, 120), height=40, width=40)
        result = apply_lomo(image)
        center = int(result[20, 20, 0])
        corner = int(result[0, 0, 0])
        assert corner < center

    def test_novekvo_telitettseg_novekvo_kromat_ad(self) -> None:
        image = _uniform_image((200, 120, 60), height=40, width=40)
        low = apply_lomo(image, saturation=0.0, contrast=1.0, vignette_strength=0.0)
        high = apply_lomo(image, saturation=2.0, contrast=1.0, vignette_strength=0.0)
        # a közepen (nincs vignetta-hatás) a nagyobb telítettség messzebb
        # viszi a csatornákat a lumától, mint a telítetlenített (low) eset.
        center_low = low[20, 20].astype(int)
        center_high = high[20, 20].astype(int)
        spread_low = int(center_low.max()) - int(center_low.min())
        spread_high = int(center_high.max()) - int(center_high.min())
        assert spread_high > spread_low

    def test_negativ_parameter_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_lomo(_uniform_image(100), saturation=-1.0)
        with pytest.raises(ValueError):
            apply_lomo(_uniform_image(100), contrast=-1.0)
        with pytest.raises(ValueError):
            apply_lomo(_uniform_image(100), vignette_strength=-1.0)


class TestApplyHolga:
    def test_lagy_fokusz_csokkenti_az_elesseg(self) -> None:
        image = _checkerboard(height=20, width=20, cell=2)
        result = apply_holga(image, softness=0.9, vignette_strength=0.0)
        original_variation = int(np.abs(np.diff(image[:, :, 0].astype(int), axis=1)).sum())
        result_variation = int(np.abs(np.diff(result[:, :, 0].astype(int), axis=1)).sum())
        assert result_variation < original_variation

    def test_sarok_sotetebb_mint_a_kozep_vignetta(self) -> None:
        image = _uniform_image(180, height=40, width=40)
        result = apply_holga(image, softness=0.0, vignette_strength=2.0)
        assert int(result[0, 0, 0]) < int(result[20, 20, 0])

    def test_ervenytelen_lagyitas_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_holga(_uniform_image(100), softness=1.5)

    def test_hibas_szineltolas_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_holga(_uniform_image(100), color_shift=(1.0, 2.0))


class TestApplyCinemascope:
    def test_fekete_savok_fent_es_lent(self) -> None:
        image = _uniform_image(150, height=100, width=100)
        result = apply_cinemascope(image, aspect_ratio=2.39)
        assert int(result[0, 50].sum()) == 0
        assert int(result[-1, 50].sum()) == 0

    def test_kozep_nem_fekete(self) -> None:
        image = _uniform_image(150, height=100, width=100)
        result = apply_cinemascope(image, aspect_ratio=2.39)
        assert int(result[50, 50].sum()) > 0

    def test_alak_megegyezik_a_bemenettel(self) -> None:
        image = _gradient_image(height=50, width=120)
        result = apply_cinemascope(image)
        assert result.shape == image.shape

    def test_hibas_kepArany_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_cinemascope(_uniform_image(100), aspect_ratio=0.0)

    def test_hibas_tint_erosseg_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_cinemascope(_uniform_image(100), tint_strength=1.5)


class TestApplyOrton:
    def test_kozepszurke_bemeneten_fenyesebb_lesz(self) -> None:
        image = _uniform_image(128, height=20, width=20)
        result = apply_orton(image, brightness=1.4, blend=0.5)
        assert int(result[0, 0, 0]) > 128

    def test_nulla_keveres_identitas(self) -> None:
        image = _gradient_image()
        result = apply_orton(image, blend=0.0)
        np.testing.assert_array_equal(result, image)

    def test_hibas_parameterek_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_orton(_uniform_image(100), brightness=0.0)
        with pytest.raises(ValueError):
            apply_orton(_uniform_image(100), blur_sigma=0.0)
        with pytest.raises(ValueError):
            apply_orton(_uniform_image(100), blend=1.5)


class TestApplySixties:
    def test_fakitas_csokkenti_a_kontrasztot(self) -> None:
        image = _gradient_image()
        result = apply_sixties(image, fade=0.8, warmth=0.0)
        original_spread = int(image[:, :, 0].astype(int).max() - image[:, :, 0].astype(int).min())
        result_spread = int(result[:, :, 0].astype(int).max() - result[:, :, 0].astype(int).min())
        assert result_spread < original_spread

    def test_melegites_novelia_a_voros_es_zold_csatornat(self) -> None:
        image = _uniform_image(128, height=10, width=10)
        result = apply_sixties(image, fade=0.0, warmth=1.0)
        red, green, blue = (int(result[0, 0, channel]) for channel in range(3))
        assert red > 128
        assert green > 128
        assert blue < 128

    def test_ervenytelen_parameterek_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_sixties(_uniform_image(100), fade=1.5)
        with pytest.raises(ValueError):
            apply_sixties(_uniform_image(100), warmth=-0.1)


class TestApplyHdr:
    def test_helyi_kontraszt_novekszik(self) -> None:
        image = _textured_image()
        result = apply_hdr(image, clip_limit=3.0, tile_grid_size=8, strength=1.0)
        original_std = float(image[:, :, 0].astype(float).std())
        result_std = float(result[:, :, 0].astype(float).std())
        assert result_std > original_std

    def test_nulla_erosseg_identitas(self) -> None:
        image = _textured_image()
        result = apply_hdr(image, strength=0.0)
        np.testing.assert_array_equal(result, image)

    def test_ervenytelen_parameterek_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_hdr(_uniform_image(100), clip_limit=0.0)
        with pytest.raises(ValueError):
            apply_hdr(_uniform_image(100), tile_grid_size=0)
        with pytest.raises(ValueError):
            apply_hdr(_uniform_image(100), strength=1.5)


class TestApplyInvert:
    def test_pontosan_invertal(self) -> None:
        image = np.array([[[10, 100, 250]]], dtype=np.uint8)
        result = apply_invert(image)
        np.testing.assert_array_equal(result, np.array([[[245, 155, 5]]], dtype=np.uint8))

    def test_ketszeri_invertalas_visszaadja_az_eredetit(self) -> None:
        image = _gradient_image()
        twice = apply_invert(apply_invert(image))
        np.testing.assert_array_equal(twice, image)

    def test_hibas_bemenet_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_invert(np.zeros((4, 4), dtype=np.uint8))


class TestApplyHeatmap:
    def test_szurke_bemeneten_szinez(self) -> None:
        image = _uniform_image(128)
        result = apply_heatmap(image, blend=1.0)
        red, green, blue = (int(result[0, 0, channel]) for channel in range(3))
        assert not (red == green == blue)

    def test_nulla_keveres_identitas(self) -> None:
        image = _gradient_image()
        result = apply_heatmap(image, blend=0.0)
        np.testing.assert_array_equal(result, image)

    def test_hibas_keveres_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_heatmap(_uniform_image(100), blend=1.5)


class TestApplyCrossprocess:
    def test_nulla_erosseg_identitas(self) -> None:
        image = _gradient_image()
        result = apply_crossprocess(image, strength=0.0)
        np.testing.assert_array_equal(result, image)

    def test_szurke_bemeneten_szinez(self) -> None:
        # a csatornánként eltérő S-görbék szürke bemeneten is elszínezik
        # a képet (ez a kereszthívás jellemző jegye).
        image = _uniform_image(100)
        result = apply_crossprocess(image, strength=1.0)
        red, green, blue = (int(result[0, 0, channel]) for channel in range(3))
        assert not (red == green == blue)

    def test_hibas_erosseg_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_crossprocess(_uniform_image(100), strength=1.5)


class TestApplyQuantizepalette:
    def test_kevesebb_egyedi_szin(self) -> None:
        image = _gradient_image(height=4, width=64)
        original_unique = len(np.unique(image[:, :, 0]))
        result = apply_quantizepalette(image, levels=4)
        result_unique = len(np.unique(result[:, :, 0]))
        assert result_unique <= 4
        assert result_unique < original_unique

    def test_vegpontok_megmaradnak(self) -> None:
        black = apply_quantizepalette(_uniform_image(0), levels=4)
        white = apply_quantizepalette(_uniform_image(255), levels=4)
        assert int(black[0, 0, 0]) == 0
        assert int(white[0, 0, 0]) == 255

    def test_ervenytelen_szintszam_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_quantizepalette(_uniform_image(100), levels=1)
        with pytest.raises(ValueError):
            apply_quantizepalette(_uniform_image(100), levels=300)
        with pytest.raises(ValueError):
            apply_quantizepalette(_uniform_image(100), levels=2.5)  # type: ignore[arg-type]


class TestApplyTwotone:
    def test_a_szinkevero_linkelt_es_tetlen_telitettséget_hasznal(self) -> None:
        """#966: a TwoTone előtti SimpleColorMatrix az XML szerinti ág."""
        image = np.array([[[40, 120, 220]]], dtype=np.uint8)
        result = glimmer_tone.apply_twotone(
            image,
            black_color=(0, 0, 0),
            white_color=(255, 255, 255),
            brightness=10.0,
            contrast=20.0,
        )
        matrixed = glimmer_tone.simple_color_matrix(
            image, saturation=0.0, brightness=10.0, contrast=20.0, linked=True
        )
        expected_value = int(round(float(luma(matrixed.astype(np.float32))[0, 0])))
        np.testing.assert_array_equal(
            result[0, 0], np.array([expected_value, expected_value, expected_value], dtype=np.uint8)
        )

    def test_fekete_bemenet_arnyek_szint_ad(self) -> None:
        result = apply_twotone(_uniform_image(0), shadow_color=(10, 20, 30))
        np.testing.assert_array_equal(result[0, 0], np.array([10, 20, 30], dtype=np.uint8))

    def test_feher_bemenet_feny_szint_ad(self) -> None:
        result = apply_twotone(_uniform_image(255), highlight_color=(200, 210, 220))
        np.testing.assert_array_equal(result[0, 0], np.array([200, 210, 220], dtype=np.uint8))

    def test_hibas_szin_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_twotone(_uniform_image(100), shadow_color=(10, 20))
        with pytest.raises(ValueError):
            apply_twotone(_uniform_image(100), highlight_color=(10, 20, 300))
