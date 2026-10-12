"""Natív SSE2-goldenek a tört CircularGradient geometriához (#4905).

A SHA-256-ok a Picasa3.exe 0x00bc2a50 natív QEMU-kimenetének vágott
alfa-bájtsorozatát rögzítik, a `filterdesc-registry.md` 4.11 táblájából.
Minden futás a `[0xd695d2] = 1` SSE2-ágat használta.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pytest

from picasapy.render.glimmer_ops import circular_gradient_mask


@pytest.mark.parametrize(
    (
        "name",
        "width",
        "height",
        "center",
        "inner_radius",
        "outer_radius",
        "inner_alpha",
        "outer_alpha",
        "aspect_ratio",
        "native_rect",
        "golden_sha256",
        "samples",
    ),
    [
        (
            "cx_half",
            64,
            48,
            (31.5, 24.0),
            10.0,
            30.0,
            0.0,
            1.0,
            1.0,
            (2, 0, 62, 48),
            "e5ef0edc53ae56421077aeb6287f6a8b2ba8e60e1521ccdd161fc00d8a462cd2",
            ((0, 0, 255), (24, 30, 0), (47, 59, 255)),
        ),
        (
            "cy_half",
            64,
            48,
            (32.0, 23.5),
            10.0,
            30.0,
            0.0,
            1.0,
            1.0,
            (2, 0, 62, 48),
            "e5ef0edc53ae56421077aeb6287f6a8b2ba8e60e1521ccdd161fc00d8a462cd2",
            ((0, 0, 255), (24, 30, 0), (47, 59, 255)),
        ),
        (
            "center_quarters",
            64,
            48,
            (31.25, 22.75),
            8.0,
            24.0,
            0.125,
            0.875,
            1.0,
            (7, 0, 55, 47),
            "45960324c8483c32f6b36fcf06bd3dc674941af1e7ef59c9bce7cb46213087ad",
            ((0, 0, 223), (23, 24, 31), (46, 47, 223)),
        ),
        (
            "radius_halves",
            64,
            48,
            (32.0, 24.0),
            7.5,
            21.5,
            0.25,
            0.75,
            1.0,
            (10, 2, 53, 45),
            "b52e90e3a335edb70e9c718f15d092b5bcca2eeb5b8f5e7b0cce8a704c3cb463",
            ((0, 0, 191), (21, 21, 63), (42, 42, 191)),
        ),
        (
            "radius_quarters",
            64,
            48,
            (31.5, 23.5),
            7.25,
            21.75,
            0.125,
            0.875,
            1.0,
            (10, 2, 54, 46),
            "9bbd12272a3b122d9c31c2ff1a36af5ace17955f6e6e1329afb9e7337b84030e",
            ((0, 0, 223), (22, 22, 31), (43, 43, 223)),
        ),
        (
            "aspect_075",
            64,
            48,
            (32.0, 24.0),
            10.0,
            30.0,
            0.0,
            1.0,
            0.75,
            (10, 0, 55, 48),
            "2bb994695ea2797828403d78ef7c9fd79efce1079812832e118f7e58082b51bf",
            ((0, 0, 255), (24, 22, 0), (47, 44, 255)),
        ),
        (
            "aspect_125",
            64,
            48,
            (31.5, 23.5),
            10.0,
            30.0,
            0.0,
            1.0,
            1.25,
            (0, 0, 64, 48),
            "5f81617394ad63c92653df910de9ed16b240b0864981379e1141d53aff5f56b7",
            ((0, 0, 255), (24, 32, 0), (47, 63, 255)),
        ),
        (
            "all_fractional",
            37,
            23,
            (18.5, 11.25),
            3.25,
            18.75,
            0.25,
            0.75,
            0.75,
            (4, 0, 32, 23),
            "60947e9b615a0adaa65306481a2b347f13deaaa97dbee6f05903c311e6539969",
            ((0, 0, 191), (11, 14, 63), (22, 27, 191)),
        ),
    ],
    ids=[
        "cx-half",
        "cy-half",
        "center-quarters",
        "radius-halves",
        "radius-quarters",
        "aspect-075",
        "aspect-125",
        "all-fractional",
    ],
)
def test_tort_geometria_bajtra_egyezik_a_nativ_sse2_goldenhez(
    name,
    width,
    height,
    center,
    inner_radius,
    outer_radius,
    inner_alpha,
    outer_alpha,
    aspect_ratio,
    native_rect,
    golden_sha256,
    samples,
):
    x0, y0, x1, y1 = native_rect
    mask = circular_gradient_mask(
        height,
        width,
        inner_radius,
        outer_radius,
        center=center,
        inner_alpha=inner_alpha,
        outer_alpha=outer_alpha,
        aspect_ratio=aspect_ratio,
    )
    alpha = np.rint(mask[y0:y1, x0:x1] * np.float32(255.0)).astype(np.uint8)

    assert alpha.shape == (y1 - y0, x1 - x0), name
    assert hashlib.sha256(alpha.tobytes()).hexdigest() == golden_sha256, name
    actual_samples = tuple(
        (y, x, int(alpha[y, x])) for y, x, _ in samples
    )
    assert actual_samples == samples, name
