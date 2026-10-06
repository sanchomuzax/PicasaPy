"""A Tiled pontmagja és csemperácsa bájtra egyezzen az eredeti Picasával (#4326)."""

from __future__ import annotations

from hashlib import sha256

import numpy as np

from picasapy.render.halftone import (
    _native_dot_alpha_lut,
    _native_dot_radius_q8_8,
    native_dot_mask,
)


_GOLDEN_7X7 = bytes(
    [
        0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 21, 21, 0, 0,
        0, 0, 60, 110, 110, 60, 0,
        0, 21, 110, 189, 189, 110, 21,
        0, 21, 110, 189, 189, 110, 21,
        0, 0, 60, 110, 110, 60, 0,
        0, 0, 0, 21, 21, 0, 0,
    ]
)
_GOLDEN_7X7_BGRA_SHA256 = "1c40c7b1c5d0d7b2b409389a6e2f569bc15ff41e342482dde22fc3999176bb4d"

_GOLDEN_Q_RAW_7X7 = np.array(
    [
        [115400, 100279, 88778, 82428, 82428, 88778, 100279],
        [100279, 82428, 67972, 59440, 59440, 67972, 82428],
        [88778, 67972, 49457, 36863, 36863, 49457, 67972],
        [82428, 59440, 36863, 16486, 16486, 36863, 59440],
        [82428, 59440, 36863, 16486, 16486, 36863, 59440],
        [88778, 67972, 49457, 36863, 36863, 49457, 67972],
        [100279, 82428, 67972, 59440, 59440, 67972, 82428],
    ],
    dtype=np.int32,
)

_GOLDEN_ALPHA_LUT = bytes([255, *range(253, 0, -1), 0, 0])

_TILE_5X4 = np.array(
    [
        [0, 0, 0, 0, 0],
        [0, 5, 82, 82, 5],
        [0, 62, 190, 190, 62],
        [0, 5, 82, 82, 5],
    ],
    dtype=np.uint8,
)

_GOLDEN_23X17_ROWS = (
    "05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52",
    "3e be be 3e 00 3e be be 3e 00 3e be be 3e 00 3e be be 3e 00 3e be be",
    "05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52",
    "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00",
    "05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52",
    "3e be be 3e 00 3e be be 3e 00 3e be be 3e 00 3e be be 3e 00 3e be be",
    "05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52",
    "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00",
    "05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52",
    "3e be be 3e 00 3e be be 3e 00 3e be be 3e 00 3e be be 3e 00 3e be be",
    "05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52",
    "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00",
    "05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52",
    "3e be be 3e 00 3e be be 3e 00 3e be be 3e 00 3e be be 3e 00 3e be be",
    "05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52",
    "00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00",
    "05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52 05 00 05 52 52",
)
_GOLDEN_23X17 = b"".join(bytes.fromhex(row) for row in _GOLDEN_23X17_ROWS)


def test_native_dot_mask_matches_qemu_7x7_alpha_bytes():
    actual = native_dot_mask(7, 7, 7).astype(np.uint8)

    assert actual.tobytes() == _GOLDEN_7X7
    bgra = np.zeros((7, 7, 4), dtype=np.uint8)
    bgra[..., 0] = actual
    bgra[..., 3] = actual
    assert sha256(bgra.tobytes()).hexdigest() == _GOLDEN_7X7_BGRA_SHA256


def test_native_dot_radius_q8_8_matches_qemu_nearest_even_values():
    actual = _native_dot_radius_q8_8(7)

    assert actual.dtype == np.int32
    np.testing.assert_array_equal(actual, _GOLDEN_Q_RAW_7X7)


def test_native_dot_alpha_lut_matches_qemu_stop_interpolation_bytes():
    actual = _native_dot_alpha_lut()

    assert actual.dtype == np.uint8
    assert actual.tobytes() == _GOLDEN_ALPHA_LUT


def test_tiled_grid_matches_qemu_23x17_bytes():
    from picasapy.render.halftone import tiled_mask_grid

    actual = tiled_mask_grid(_TILE_5X4, height=17, width=23)

    assert actual.dtype == np.uint8
    assert actual.shape == (17, 23)
    assert actual.tobytes() == _GOLDEN_23X17
