"""#4940: a mérőszett összevetése a referencia JPEG kódolásával egyezzen.

A Picasa-export tömörített JPEG, a mi renderünk nyers RGB. A nyers ΔE a JPEG-zajt
eltérésnek látja, ezért a mi képünket a referencia mintavételezésével és
kvantálótábláival kódoljuk. Nem JPEG referenciánál a kép változatlan marad.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pytest
from PIL import Image, JpegImagePlugin

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools" / "golden"))

from compare_render import _read_rgb, delta_e_cie76  # noqa: E402
from jpeg_reference import (  # noqa: E402
    encode_like_reference,
    jpeg_encode_like,
    reference_jpeg_settings,
)


def _scene() -> np.ndarray:
    """Szintetikus kép: gradiens, éles blokk és zaj — a JPEG-hibát ez mutatja."""
    rng = np.random.default_rng(4940)
    yy, xx = np.mgrid[0:96, 0:128]
    rgb = np.stack([xx * 2, yy * 2, xx + yy], axis=-1).astype(np.int64)
    rgb[24:60, 40:90] = (200, 30, 30)
    rgb += rng.integers(-12, 13, rgb.shape)
    return np.clip(rgb, 0, 255).astype(np.uint8)


def _write_reference(path: Path, rgb: np.ndarray, quality: int, subsampling) -> Path:
    Image.fromarray(rgb).save(path, "JPEG", quality=quality, subsampling=subsampling)
    return path


def _delta_e(first: np.ndarray, second: np.ndarray) -> float:
    return float(delta_e_cie76(first, second).mean())


def test_egyezo_kodolas_utan_de_nulla_a_nyers_meg_nem(tmp_path):
    """4:2:0 referencia: a nyers render eltér, az egyező kódolás után nincs ΔE."""
    scene = _scene()
    ref = _write_reference(tmp_path / "ref.jpg", scene, quality=60, subsampling=2)
    decoded_ref = _read_rgb(ref)

    raw_de = _delta_e(decoded_ref, scene)
    matched_de = _delta_e(decoded_ref, encode_like_reference(scene, ref))

    assert raw_de > 1.0
    assert matched_de < 0.05


@pytest.mark.parametrize("subsampling", [0, 2], ids=["444", "420"])
def test_mintavetelezes_es_kvantalotabla_egyezik_a_referenciaval(tmp_path, subsampling):
    scene = _scene()
    ref = _write_reference(
        tmp_path / "ref.jpg", scene, quality=40, subsampling=subsampling
    )
    settings = reference_jpeg_settings(ref)
    assert settings is not None

    encoded = jpeg_encode_like(scene, settings)

    with Image.open(io.BytesIO(encoded)) as ours, Image.open(ref) as theirs:
        assert JpegImagePlugin.get_sampling(ours) == JpegImagePlugin.get_sampling(theirs)
        assert ours.quantization == theirs.quantization


def test_nem_jpeg_referenciank_valtozatlan_marad(tmp_path):
    """PNG referenciánál nincs kódolási beállítás, a kép változatlan marad."""
    scene = _scene()
    png = tmp_path / "ref.png"
    Image.fromarray(scene).save(png)

    assert reference_jpeg_settings(png) is None
    assert np.array_equal(encode_like_reference(scene, png), scene)
