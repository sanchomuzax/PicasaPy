"""#4157: Glimmer-keverés páratlan sorvégi pixele és Steps-csonkolás."""

from __future__ import annotations

import numpy as np

from picasapy.render import glimmer_ops
from picasapy.render import quantize_palette


def _spec_szerinti_keveres(base: np.ndarray, top: np.ndarray, alpha: float) -> np.ndarray:
    """A `0x009dc4b0` SIMD-párja és a sorvégi skalárképlet."""
    w = int(np.float32(alpha) * np.float32(256.0))
    if w > 0:
        w -= 1
    base_i = np.rint(base).astype(np.int64)
    top_i = np.rint(top).astype(np.int64)
    result = (base_i * (255 - w) + top_i * w) >> 8
    if base.shape[1] % 2:
        result[:, -1] = top_i[:, -1] + (((base_i[:, -1] - top_i[:, -1]) * w) >> 8)
    return result.astype(np.float32)


def test_alpha_blend_pares_es_paratlan_sorvegi_pixele_spec_szerint() -> None:
    rng = np.random.default_rng(4157)
    eredmenyek: dict[int, np.ndarray] = {}

    for width in (50, 51):
        base = rng.integers(0, 256, size=(49, width, 3), dtype=np.uint8).astype(np.float32)
        top = rng.integers(0, 256, size=(49, width, 3), dtype=np.uint8).astype(np.float32)
        base[22, width - 1, 0] = 0
        top[22, width - 1, 0] = 147

        result = glimmer_ops.alpha_blend(base, top, 0.5)
        expected = _spec_szerinti_keveres(base, top, 0.5)
        np.testing.assert_array_equal(result, expected)
        eredmenyek[width] = result

    # A spec példája: a páros SIMD-kontroll 72, a páratlan sorvégi skalárág 74.
    assert eredmenyek[50][22, 49, 0] == 72
    assert eredmenyek[51][22, 50, 0] == 74


def test_kvantal_a_tort_steps_erteket_csonkolja() -> None:
    rng = np.random.default_rng(4157)
    image = rng.integers(0, 256, size=(120, 180, 3), dtype=np.uint8)

    np.testing.assert_array_equal(
        quantize_palette.kvantal(image, steps=8.9),
        quantize_palette.kvantal(image, steps=8.0),
    )
