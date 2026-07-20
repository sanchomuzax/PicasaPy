"""A `picasapy.render.color.apply_grain` (grain2) tesztjei a golden-elemzés
dokumentált spec-je ellen (`docs/specs/filters-decoded.md`): a grain2
sztochasztikus, pixelhűen NEM reprodukálható — az elfogadás statisztikai
(zaj-σ, átlag), nem pixel-diff."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.color import apply_grain


def _uniform_image(value: int | tuple[int, int, int]) -> np.ndarray:
    return np.full((40, 50, 3), value, dtype=np.uint8)


class TestApplyGrain:
    def test_alak_es_dtype_megmarad(self) -> None:
        image = _uniform_image(128)
        result = apply_grain(image, seed=1)
        assert result.shape == image.shape
        assert result.dtype == np.uint8

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(128)
        original = image.copy()
        apply_grain(image, seed=1)
        np.testing.assert_array_equal(image, original)

    def test_azonos_mag_reprodukalhato(self) -> None:
        image = _uniform_image(128)
        first = apply_grain(image, seed=42)
        second = apply_grain(image, seed=42)
        np.testing.assert_array_equal(first, second)

    def test_elteroe_mag_elteroe_kimenet(self) -> None:
        image = _uniform_image(128)
        first = apply_grain(image, seed=1)
        second = apply_grain(image, seed=2)
        assert not np.array_equal(first, second)

    def test_atlag_kozel_valtozatlan_szoras_no(self) -> None:
        image = _uniform_image(128)
        result = apply_grain(image, sigma=8.0, seed=7)
        mean_in = float(image.mean())
        mean_out = float(result.mean())
        assert abs(mean_out - mean_in) < 2.0
        assert float(result.std()) > float(image.std())

    def test_hibas_bemenet_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_grain(np.zeros((4, 4), dtype=np.uint8))
