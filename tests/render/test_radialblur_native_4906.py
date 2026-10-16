"""A #4906 natív SSE2 mérés 28 bemenet/kimenet párja."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from picasapy.render.focal import zoom_blur


_PAIRS = json.loads(
    (Path(__file__).parent / "data" / "radialblur-4906-pairs.json").read_text(
        encoding="utf-8"
    )
)
_INPUTS = _PAIRS["inputs_bgra_hex_by_sha256"]


@pytest.mark.parametrize("case", _PAIRS["cases"], ids=lambda case: f"case-{case['case']}")
def test_zoom_blur_matches_native_sse2_case(case):
    """Az implementációnak bájtra egyeznie kell a közvetlen natív maggal."""
    width = case["width"]
    height = case["height"]
    image = np.frombuffer(
        bytes.fromhex(_INPUTS[case["input_sha256"]]), dtype=np.uint8
    ).reshape((height, width, 4))

    actual = zoom_blur(
        image,
        case["x_px"] / width,
        case["y_px"] / height,
        case["amount"],
    )
    actual_hash = hashlib.sha256(actual.tobytes()).hexdigest()
    if actual_hash != case["native_sha256"]:
        expected = np.frombuffer(
            bytes.fromhex(case["native_bgra_hex"]), dtype=np.uint8
        ).reshape((height, width, 4))
        differing_pixels = np.any(actual != expected, axis=2)
        coords = np.argwhere(differing_pixels)
        first = [
            [int(x), int(y)]
            for y, x in coords[:8]
        ]
        pytest.fail(
            f"native SSE2 mismatch: {len(coords)}/{width * height} pixels; "
            f"first (x,y)={first}; actual sha256={actual_hash}; "
            f"expected sha256={case['native_sha256']}"
        )
