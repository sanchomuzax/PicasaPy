"""A `picasapy.render.color` szín-műveletek tesztjei a golden-elemzés
dokumentált mérési pontjai ellen (`docs/specs/filters-decoded.md`)."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.color import (
    apply_bw,
    apply_saturation,
    apply_sepia,
    apply_warm,
)


def _uniform_image(value: int | tuple[int, int, int]) -> np.ndarray:
    return np.full((6, 8, 3), value, dtype=np.uint8)


class TestApplyBw:
    def test_rec601_luma(self) -> None:
        # bw = Rec.601: 0,299·R + 0,587·G + 0,114·B, csatornánként visszaírva
        image = _uniform_image((100, 150, 200))
        result = apply_bw(image)
        expected = round(0.299 * 100 + 0.587 * 150 + 0.114 * 200)
        assert abs(int(result[0, 0, 0]) - expected) <= 1
        assert result[0, 0, 0] == result[0, 0, 1] == result[0, 0, 2]

    def test_szurke_bemenet_valtozatlan(self) -> None:
        image = _uniform_image(90)
        np.testing.assert_array_equal(apply_bw(image), image)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image((10, 200, 30))
        original = image.copy()
        apply_bw(image)
        np.testing.assert_array_equal(image, original)

    def test_hibas_bemenet_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_bw(np.zeros((4, 4), dtype=np.uint8))


class TestApplySepia:
    def test_dokumentalt_csatornagorbe_g128(self) -> None:
        # mért közelítés: R≈0,82g+58 · G≈0,86g+35 · B≈0,90g+15
        image = _uniform_image(128)
        result = apply_sepia(image)
        assert abs(int(result[0, 0, 0]) - 163) <= 1
        assert abs(int(result[0, 0, 1]) - 145) <= 1
        assert abs(int(result[0, 0, 2]) - 130) <= 1

    def test_szines_bemenet_monokrom_tonusra_kepez(self) -> None:
        image = _uniform_image((30, 180, 60))
        result = apply_sepia(image)
        # szépia: R > G > B tónus-sorrend
        assert int(result[0, 0, 0]) > int(result[0, 0, 1]) > int(result[0, 0, 2])


class TestApplyWarm:
    def test_dokumentalt_csatornagorbe_g128(self) -> None:
        # mért közelítés: R≈0,89g+19 · G≈0,88g+1 · B≈0,93g−16
        image = _uniform_image(128)
        result = apply_warm(image)
        assert abs(int(result[0, 0, 0]) - 133) <= 1
        assert abs(int(result[0, 0, 1]) - 114) <= 1
        assert abs(int(result[0, 0, 2]) - 103) <= 1

    def test_melegit_szurke_kepen(self) -> None:
        image = _uniform_image(128)
        result = apply_warm(image)
        assert int(result[0, 0, 0]) > int(result[0, 0, 2])


class TestApplySaturation:
    def test_nulla_identitas(self) -> None:
        image = _uniform_image((200, 100, 100))
        np.testing.assert_array_equal(apply_saturation(image, 0.0), image)

    def test_minusz_egy_szurkeskala(self) -> None:
        image = _uniform_image((200, 100, 100))
        result = apply_saturation(image, -1.0)
        assert result[0, 0, 0] == result[0, 0, 1] == result[0, 0, 2]

    def test_dokumentalt_gain_pont(self) -> None:
        # mért gain-tábla: s=+0,5 → 1,729× króma-erősítés
        image = _uniform_image((200, 100, 100))
        result = apply_saturation(image, 0.5)
        luma = 0.299 * 200 + 0.587 * 100 + 0.114 * 100
        expected_r = luma + 1.729 * (200 - luma)
        assert abs(int(result[0, 0, 0]) - expected_r) <= 1

    def test_csokkentes_dokumentalt_gain(self) -> None:
        # mért: s=−0,333 → 0,683× gain
        image = _uniform_image((200, 100, 100))
        result = apply_saturation(image, -0.333)
        luma = 0.299 * 200 + 0.587 * 100 + 0.114 * 100
        expected_r = luma + 0.683 * (200 - luma)
        assert abs(int(result[0, 0, 0]) - expected_r) <= 1

    def test_clip_255(self) -> None:
        image = _uniform_image((250, 30, 30))
        result = apply_saturation(image, 1.0)
        assert result.max() <= 255

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image((200, 100, 100))
        original = image.copy()
        apply_saturation(image, 0.7)
        np.testing.assert_array_equal(image, original)
