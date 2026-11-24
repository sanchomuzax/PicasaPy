"""#7415: tilt utáni crop64 a forrásablakot vágja és azon tilt-el újra."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import decode_rect64
from picasapy.render.chain import apply_filters
from picasapy.render.ops import apply_crop, apply_tilt


def _coordinate_image(width: int = 1024, height: int = 256) -> np.ndarray:
    y, x = np.indices((height, width), dtype=np.uint16)
    return np.stack((x % 256, y % 256, (x * 13 + y * 7) % 256), axis=-1).astype(
        np.uint8
    )


@pytest.mark.parametrize(
    "crop64",
    ("418029009e3fcfff", "6a402600c47fecff"),
)
def test_tilt_utani_crop64_a_kivagott_ablakra_futtatja_ujra_a_tiltet(crop64):
    image = _coordinate_image()
    tilt = FilterOp("tilt", ("1", "0.391249", "0.000000"))
    crop = FilterOp("crop64", ("1", crop64))

    actual, skipped = apply_filters(image, (tilt, crop))
    source_window = apply_crop(image, decode_rect64(crop64))
    expected = apply_tilt(source_window, angle=0.391249 * 0.2)

    assert actual.shape == expected.shape
    np.testing.assert_array_equal(actual, expected)
    assert skipped == ()


def test_vagas_tilt_elott_tovabbra_is_a_kivagott_ablakon_futtatja_a_tiltet():
    image = _coordinate_image()
    tilt = FilterOp("tilt", ("1", "0.391249", "0.000000"))
    crop = FilterOp("crop64", ("1", "418029009e3fcfff"))

    actual, skipped = apply_filters(image, (crop, tilt))
    expected = apply_tilt(apply_crop(image, decode_rect64(crop.params[1])), angle=0.391249 * 0.2)

    np.testing.assert_array_equal(actual, expected)
    assert skipped == ()
