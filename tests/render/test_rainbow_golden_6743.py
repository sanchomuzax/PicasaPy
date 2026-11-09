"""A #460 TwoTone-export Rainbow-paritása és a natív paraméterkerekítés."""

from __future__ import annotations

import sys
from pathlib import Path

import cv2
import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
_GOLDEN_TOOLS = _ROOT / "tools" / "golden"
if str(_GOLDEN_TOOLS) not in sys.path:
    sys.path.insert(0, str(_GOLDEN_TOOLS))

from compare_render import _read_rgb, delta_e_cie76, ssim  # noqa: E402
from picasapy.ini.filters import parse_filters  # noqa: E402
from picasapy.render import apply_filters  # noqa: E402
from picasapy.render.rainbow import apply_rainbow  # noqa: E402

_DATA = Path(__file__).parent / "data" / "rainbow_6743"
_INPUT = _read_rgb(_DATA / "input_k06_twotone.jpg")
_REFERENCE = _read_rgb(_DATA / "reference_crop.png")
_FILTERS = "rainbow=1,244.890456;"
_CROP_X = 504
_CROP_WIDTH = 208
_BLUR_MARGIN = 8

# rontás-kontroll: picasapy.render.rainbow._RAINBOW_CAREFUL_ENHANCE = True → 1 failed


def test_a_szinertek_parametere_a_binari_szerint_kerekul() -> None:
    """A 0x008f92d0 ROUND-ja a 244,890456 értéket 245-re viszi."""
    rendered = apply_filters(_INPUT, parse_filters(_FILTERS)).image

    assert np.array_equal(rendered, apply_rainbow(_INPUT, preserve=245))


def test_a_k06_picasa_export_egyezik_a_dither_tolerans_mercevel() -> None:
    """A teljes képen futó szinthúzás után a középső sávot méri sigma 2,5-tel."""
    rendered = apply_filters(_INPUT, parse_filters(_FILTERS)).image
    rendered_crop = rendered[:, _CROP_X : _CROP_X + _CROP_WIDTH]

    rendered_blur = cv2.GaussianBlur(rendered_crop, (0, 0), 2.5)
    reference_blur = cv2.GaussianBlur(_REFERENCE, (0, 0), 2.5)
    measured = rendered_blur[:, _BLUR_MARGIN:-_BLUR_MARGIN]
    expected = reference_blur[:, _BLUR_MARGIN:-_BLUR_MARGIN]
    delta_e = delta_e_cie76(measured, expected)
    mean_delta_e = float(delta_e.mean())
    p99_delta_e = float(np.percentile(delta_e, 99))
    similarity = ssim(measured, expected)

    assert similarity >= 0.98, f"SSIM {similarity:.5f} < 0.98"
    assert mean_delta_e <= 2.0, (
        f"átlagos ΔE {mean_delta_e:.3f} > 2.0; p99={p99_delta_e:.3f}"
    )
