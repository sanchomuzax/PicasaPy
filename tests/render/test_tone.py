"""A `picasapy.render.tone` tónus-műveletek tesztjei.

A várt értékek a golden-elemzés dokumentált mérési pontjai
(`docs/specs/filters-decoded.md`), ±1/255 toleranciával.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.tone import (
    apply_color_temperature,
    apply_fill,
    apply_finetune2,
    apply_highlights,
    apply_neutral_pipette,
    apply_shadows,
    parse_neutral_argb,
)


def _uniform_image(value: int | tuple[int, int, int]) -> np.ndarray:
    return np.full((6, 8, 3), value, dtype=np.uint8)


class TestApplyFill:
    def test_nulla_erosseg_identitas(self) -> None:
        image = _uniform_image(90)
        np.testing.assert_array_equal(apply_fill(image, 0.0), image)

    @pytest.mark.parametrize(
        ("strength", "bemenet", "vart"),
        [
            # docs/specs/filters-decoded.md — fill görbecsalád mérési pontjai
            (0.25, 32, 45.7),
            (0.25, 128, 145.6),
            (0.25, 224, 228.6),
            (0.50, 32, 69.7),
            (0.50, 128, 168.6),
            (0.75, 128, 194.0),
            (1.00, 32, 162.7),
            (1.00, 128, 218.0),
            (1.00, 224, 243.0),
        ],
    )
    def test_dokumentalt_meresi_pontok(
        self, strength: float, bemenet: int, vart: float
    ) -> None:
        image = _uniform_image(bemenet)
        result = apply_fill(image, strength)
        assert abs(int(result[0, 0, 0]) - vart) <= 1.0

    def test_feherpont_tarto(self) -> None:
        image = _uniform_image(255)
        result = apply_fill(image, 1.0)
        assert result[0, 0, 0] == 255

    def test_kozbulso_erosseg_a_szomszedos_gorbek_koze_esik(self) -> None:
        image = _uniform_image(128)
        low = int(apply_fill(image, 0.25)[0, 0, 0])
        mid = int(apply_fill(image, 0.375)[0, 0, 0])
        high = int(apply_fill(image, 0.5)[0, 0, 0])
        assert low < mid < high

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(50)
        original = image.copy()
        apply_fill(image, 0.8)
        np.testing.assert_array_equal(image, original)

    def test_hibas_bemenet_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_fill(np.zeros((4, 4), dtype=np.uint8), 0.5)


class TestApplyHighlights:
    def test_nulla_erosseg_identitas(self) -> None:
        image = _uniform_image(120)
        np.testing.assert_array_equal(apply_highlights(image, 0.0), image)

    def test_dokumentalt_pont_h040(self) -> None:
        # mérve: h=0,40-nél a 192-es bemenet fehérbe húzódik (192→255)
        image = _uniform_image(192)
        result = apply_highlights(image, 0.4)
        assert result[0, 0, 0] == 255

    def test_vilagosit(self) -> None:
        image = _uniform_image(100)
        result = apply_highlights(image, 0.5)
        assert int(result[0, 0, 0]) > 100


class TestApplyShadows:
    def test_nulla_erosseg_identitas(self) -> None:
        image = _uniform_image(120)
        np.testing.assert_array_equal(apply_shadows(image, 0.0), image)

    def test_sotetit_es_feherpontot_tart(self) -> None:
        image = _uniform_image(120)
        result = apply_shadows(image, 0.5)
        assert int(result[0, 0, 0]) < 120
        white = _uniform_image(255)
        assert apply_shadows(white, 0.5)[0, 0, 0] == 255


class TestApplyColorTemperature:
    def test_nulla_identitas(self) -> None:
        image = _uniform_image(128)
        np.testing.assert_array_equal(apply_color_temperature(image, 0.0), image)

    def test_hutes_dokumentalt_pont(self) -> None:
        # mérve (finetune2 p5=−0,5): ΔB +20, ΔR −16, G változatlan
        image = _uniform_image(128)
        result = apply_color_temperature(image, -0.5)
        assert abs(int(result[0, 0, 2]) - 148) <= 1
        assert abs(int(result[0, 0, 0]) - 112) <= 1
        assert result[0, 0, 1] == 128

    def test_melegites_dokumentalt_pont(self) -> None:
        # mérve (p5=+1,0): ΔB −20, ΔR +8 — a melegítés jóval gyengébb
        image = _uniform_image(128)
        result = apply_color_temperature(image, 1.0)
        assert abs(int(result[0, 0, 2]) - 108) <= 1
        assert abs(int(result[0, 0, 0]) - 136) <= 1

    def test_clip_a_hatarokon(self) -> None:
        image = _uniform_image(250)
        result = apply_color_temperature(image, -1.0)
        assert result.max() <= 255


class TestNeutralPipette:
    def test_parse_alpha_nulla_nincs_kijeloles(self) -> None:
        assert parse_neutral_argb("00000000") is None

    def test_parse_ervenyes_szin(self) -> None:
        assert parse_neutral_argb("ffccc6b2") == (204, 198, 178)

    def test_parse_ervenytelen_value_error(self) -> None:
        with pytest.raises(ValueError):
            parse_neutral_argb("nemhexa!")

    def test_meleg_szurke_kekkel_kompenzal(self) -> None:
        # mérve: ffccc6b2 (meleg-szürke) kijelölésekor ΔB pozitív, ΔR negatív
        image = _uniform_image(128)
        result = apply_neutral_pipette(image, (204, 198, 178))
        assert int(result[0, 0, 2]) > 128
        assert int(result[0, 0, 0]) < 128

    def test_szurke_pipetta_identitas(self) -> None:
        image = _uniform_image(77)
        result = apply_neutral_pipette(image, (200, 200, 200))
        np.testing.assert_array_equal(result, image)


class TestApplyFinetune2:
    def test_minden_parameter_semleges_identitas(self) -> None:
        image = _uniform_image(140)
        result = apply_finetune2(
            image, fill=0.0, highlights=0.0, shadows=0.0, neutral=None, temperature=0.0
        )
        np.testing.assert_array_equal(result, image)

    def test_fill_p1_azonos_az_onallo_fill_szurovel(self) -> None:
        # mérve: a finetune2 p1 LUT-ja bitre azonos az önálló fill-ével
        image = _uniform_image(64)
        via_finetune = apply_finetune2(
            image, fill=0.5, highlights=0.0, shadows=0.0, neutral=None, temperature=0.0
        )
        np.testing.assert_array_equal(via_finetune, apply_fill(image, 0.5))

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(90)
        original = image.copy()
        apply_finetune2(
            image, fill=0.3, highlights=0.1, shadows=0.2, neutral=None, temperature=0.5
        )
        np.testing.assert_array_equal(image, original)
