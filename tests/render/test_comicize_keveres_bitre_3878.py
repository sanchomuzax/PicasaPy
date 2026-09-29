"""A comicize záró keverése a közös `glimmer_ops.alpha_blend`-en fut (#3878).

A `0x009dc4b0`-s keverő korábban másodszor is megvolt az `effects_artistic`-ban;
a csere előtt bitre egyezést kellett igazolni a comicize bemenetein.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.glimmer_ops import alpha_blend


def _régi_keverő(bottom, top, alpha):
    """A törölt `effects_artistic.blend_alpha_native` befagyasztott mása."""

    def bitek(x):
        return int(np.array(x, dtype=np.float32).view(np.int32))

    def közel(a, c):
        return abs(bitek(a) - bitek(c)) < 8

    alfa = float(np.clip(np.float32(alpha), 0.0, 1.0))
    if közel(alfa, 1.0):
        return top.astype(np.uint8)
    if közel(alfa, 0.0):
        return bottom.astype(np.uint8)
    w = int(np.float32(alfa) * np.float32(256.0))
    if w > 0:
        w -= 1
    ki = (bottom.astype(np.int32) * (255 - w) + top.astype(np.int32) * w) >> 8
    return ki.astype(np.uint8)


@pytest.mark.parametrize("alfa", [0.0, 0.3, 0.5, 1.0])
def test_a_ket_keverő_bitre_azonos(alfa):
    rng = np.random.default_rng(3878)
    alsó = rng.integers(0, 256, (37, 53, 3), dtype=np.uint8)
    # a comicize felső eleme: `⌊b·r/255⌋` int32-ben
    raszter = rng.integers(0, 256, (37, 53, 3), dtype=np.uint8)
    felső = (alsó.astype(np.int32) * raszter.astype(np.int32)) // 255
    régi = _régi_keverő(alsó, felső, alfa)
    új = alpha_blend(alsó, felső, alfa).astype(np.uint8)
    np.testing.assert_array_equal(régi, új)
