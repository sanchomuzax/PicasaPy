"""A PixelateImageOperation natív kimenetei (#4908), QEMU-függőség nélkül."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from picasapy.render.effects_artistic import pixelate_centered


_VEKTOROK = json.loads(
    (Path(__file__).parent / "data" / "pixelate_4908_native.json").read_text(
        encoding="utf-8"
    )
)["cases"]


@pytest.mark.parametrize("vektor", _VEKTOROK, ids=lambda v: v["name"])
def test_pixelate_centered_bajtra_egyezik_a_nativ_maggal(vektor: dict) -> None:
    """A rögzített BGRA-bemenet és a 0x00bcdf10 natív kimenete egyezzen."""
    width, height = vektor["source_wh"]
    block_w, block_h = vektor["pixel_width_height"]
    source = np.frombuffer(bytes.fromhex(vektor["input_hex"]), dtype=np.uint8)
    source = source.reshape(height, width, 4)

    rgb = pixelate_centered(source[:, :, :3], block_w, block_h)
    alpha_rgb = np.repeat(source[:, :, 3:4], 3, axis=2)
    alpha = pixelate_centered(alpha_rgb, block_w, block_h)[:, :, :1]
    actual = np.concatenate((rgb, alpha), axis=2)
    expected = np.frombuffer(
        bytes.fromhex(vektor["native_output_hex"]), dtype=np.uint8
    ).reshape(height, width, 4)

    np.testing.assert_array_equal(actual, expected, err_msg=vektor["name"])
