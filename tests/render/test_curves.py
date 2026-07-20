"""A `picasapy.render.curves` LUT-segédek tesztjei (#140: csatornánkénti LUT)."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.curves import apply_channel_luts


def _ramp() -> np.ndarray:
    return np.arange(256, dtype=np.float64)


def _uniform_image(value: int | tuple[int, int, int]) -> np.ndarray:
    return np.full((4, 5, 3), value, dtype=np.uint8)


class TestApplyChannelLuts:
    def test_identitas_rampakkal(self) -> None:
        image = _uniform_image((10, 20, 30))
        result = apply_channel_luts(image, (_ramp(), _ramp(), _ramp()))
        np.testing.assert_array_equal(result, image)

    def test_csatornankent_kulon_lut(self) -> None:
        image = _uniform_image(100)
        result = apply_channel_luts(
            image, (_ramp() + 8.0, _ramp(), _ramp() - 20.0)
        )
        assert tuple(result[0, 0]) == (108, 100, 80)

    def test_clip_es_kerekites(self) -> None:
        image = _uniform_image(250)
        result = apply_channel_luts(
            image, (_ramp() + 91.4, _ramp(), _ramp() - 300.0)
        )
        assert tuple(result[0, 0]) == (255, 250, 0)

    def test_nem_mutalja_a_bemenetet(self) -> None:
        image = _uniform_image(50)
        original = image.copy()
        apply_channel_luts(image, (_ramp() + 1.0, _ramp(), _ramp()))
        np.testing.assert_array_equal(image, original)

    def test_kimenet_uint8(self) -> None:
        result = apply_channel_luts(
            _uniform_image(7), (_ramp(), _ramp(), _ramp())
        )
        assert result.dtype == np.uint8

    def test_hibas_lut_darabszam_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_channel_luts(_uniform_image(1), (_ramp(), _ramp()))

    def test_hibas_lut_alak_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_channel_luts(
                _uniform_image(1), (_ramp(), _ramp(), _ramp()[:128])
            )

    def test_hibas_kep_value_error(self) -> None:
        with pytest.raises(ValueError):
            apply_channel_luts(
                np.zeros((4, 4), dtype=np.uint8), (_ramp(), _ramp(), _ramp())
            )
