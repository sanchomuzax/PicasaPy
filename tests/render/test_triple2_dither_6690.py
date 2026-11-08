"""#6690: a `triple2` golden-mérése ditherfüggetlen mércével.

Az eredeti worker (`0x008f8b90`) előbb a Derítőfényt (`0x0090ac20`), majd a
szinthúzást (`0x0090c3b0`) futtatja. A szinthúzás közös LUT-alkalmazója,
`0x0090bc60`, a `0x00c32520` CRT-inicializálásakor magozott folyamat-globális
MT19937-ből képpontonként fogyaszt mintát. Az export előtti állapot és a
korábbi mintafogyasztás egyetlen exportból nem állítható vissza, ezért a
nyers pixelminta nem reprodukálható. A teszt nyersen is mér, de az ítéletet
mindkét kép σ=2,5 pixeles Gauss-elmosása után, a golden alapküszöbökkel hozza.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from picasapy.lazy_cv2 import cv2

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "tools" / "golden"))

from compare_render import Thresholds, _read_rgb, compare_images  # noqa: E402
from jpeg_reference import jpeg_encode_like  # noqa: E402
from picasapy.ini.filters import parse_filters  # noqa: E402
from picasapy.render import apply_filters  # noqa: E402

_DATA = Path(__file__).parent / "data" / "triple2_dither_6690"
_MANIFEST = json.loads((_DATA / "esetek.json").read_text(encoding="utf-8"))
_ESETEK = _MANIFEST["cases"]
_JPEG = _MANIFEST["comparison"]["jpeg_settings"]
_JPEG["qtables"] = {int(key): value for key, value in _JPEG["qtables"].items()}
_SIGMA = float(_MANIFEST["comparison"]["sigma_px"])
_BORDER = int(_MANIFEST["comparison"]["ignored_border_px"])


def _encode_like_golden(image: np.ndarray) -> np.ndarray:
    payload = jpeg_encode_like(image, _JPEG)
    with Image.open(io.BytesIO(payload)) as encoded:
        return np.asarray(encoded.convert("RGB"))


@pytest.mark.parametrize("eset", _ESETEK, ids=[row["id"] for row in _ESETEK])
def test_triple2_dithertolerans_az_eredeti_exporthoz_merheto(
    eset: dict, request: pytest.FixtureRequest
) -> None:
    source = _read_rgb(_DATA / eset["source"])
    golden = _read_rgb(_DATA / eset["export"])
    rendered = apply_filters(source, parse_filters(eset["filters"]))
    assert not rendered.skipped

    local = _encode_like_golden(rendered.image)
    raw_verdict, raw_metrics, _note = compare_images(local, golden, Thresholds())
    local_blurred = cv2.GaussianBlur(local, (0, 0), _SIGMA)
    golden_blurred = cv2.GaussianBlur(golden, (0, 0), _SIGMA)
    margin = _BORDER
    measured_local = local_blurred[margin:-margin, margin:-margin]
    measured_golden = golden_blurred[margin:-margin, margin:-margin]
    verdict, metrics, _note = compare_images(
        measured_local, measured_golden, Thresholds()
    )
    request.node.user_properties.extend(
        (
            ("raw_verdict", raw_verdict),
            ("raw_ssim", raw_metrics.get("ssim")),
            ("raw_delta_e_mean", raw_metrics.get("delta_e_mean")),
            ("dither_tolerant_verdict", verdict),
            ("dither_tolerant_ssim", metrics.get("ssim")),
            ("dither_tolerant_delta_e_mean", metrics.get("delta_e_mean")),
        )
    )
    assert verdict in ("pixelhű", "közelítés"), (
        f"{eset['id']}: σ={_SIGMA}; nyers={raw_verdict} "
        f"(SSIM={raw_metrics.get('ssim')}, ΔE={raw_metrics.get('delta_e_mean')}), "
        f"dithertoleráns={verdict} (SSIM={metrics.get('ssim')}, "
        f"ΔE={metrics.get('delta_e_mean')})"
    )


# rontás-kontroll: picasapy.render.chain_native_handlers._MIN_WHITE_POINT = 0.5 → 1 failed
