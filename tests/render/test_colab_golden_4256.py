"""#4256: az eredeti Picasa Colab-exportok foltátlagos összevetése.

Forrás: tests/fixtures/golden_colab/README.md — Picasa 3.9, Colab #87/#92/#93/#94.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters

_FIXTURE_ROOT = Path(__file__).parents[1] / "fixtures" / "golden_colab"
_PATCH_NAMES = (
    "vörös", "zöld", "kék", "sárga",
    "cián", "bíbor", "fehér", "fekete",
    "szürke", "barna", "kékesszürke", "olívazöld",
    "arany", "lila", "világosszürke", "sötétszürke",
)
_PATCH_EDGE = 200
_CENTER_EDGE = 40
# A q93-es Picasa JPEG és a PicasaPy bemeneti JPEG dekódolása közti zajra ±2.
_TOLERANCE = 2
_EFFECTS = (
    ("sepia", "sepia=1;", "sepia.jpg"),
    ("bw", "bw=1;", "bw.jpg"),
    ("warm", "warm=1;", "warm.jpg"),
)


def _read_rgb(filename: str) -> np.ndarray:
    with Image.open(_FIXTURE_ROOT / filename) as image:
        return np.asarray(image.convert("RGB"))


def _patch_mean(image: np.ndarray, patch_index: int) -> np.ndarray:
    row, column = divmod(patch_index, 4)
    inset = (_PATCH_EDGE - _CENTER_EDGE) // 2
    y0 = row * _PATCH_EDGE + inset
    x0 = column * _PATCH_EDGE + inset
    sample = image[y0 : y0 + _CENTER_EDGE, x0 : x0 + _CENTER_EDGE]
    return sample.astype(np.float64).mean(axis=(0, 1))


@pytest.mark.parametrize(("effect", "filter_chain", "golden"), _EFFECTS)
def test_picasa_colab_golden_patch_means(effect, filter_chain, golden):
    """Mind a 16 folt középső 40×40-es átlagának csatornái egyezzenek."""
    source = _read_rgb("forras.jpg")
    expected = _read_rgb(golden)
    assert source.shape == expected.shape == (800, 800, 3)

    rendered = apply_filters(source, parse_filters(filter_chain)).image
    assert rendered.shape == source.shape

    for index, name in enumerate(_PATCH_NAMES):
        actual_mean = _patch_mean(rendered, index)
        expected_mean = _patch_mean(expected, index)
        error = np.abs(actual_mean - expected_mean)
        assert float(error.max()) <= _TOLERANCE, (
            f"{effect}, {name}: PicasaPy={actual_mean.tolist()}, "
            f"Picasa={expected_mean.tolist()}, eltérés={error.tolist()}, "
            f"tűrés=±{_TOLERANCE}"
        )
