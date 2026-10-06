"""#4268 — a poszterlapok kimeneti geometriája és tartalma."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from picasapy.printing.poster import make_poster_tiles


# rontás-kontroll: picasapy.printing.poster.OVERLAP_RATIO = 0.05 → 1 failed


def _color_patches(path: Path) -> np.ndarray:
    """800×800-as veszteségmentes ábra, minden koordinátája felismerhető."""
    yy, xx = np.indices((800, 800), dtype=np.uint16)
    rgb = np.empty((800, 800, 3), dtype=np.uint8)
    rgb[..., 0] = (xx // 40 * 31 + yy // 40 * 17) % 256
    rgb[..., 1] = xx % 256
    rgb[..., 2] = yy % 256
    Image.fromarray(rgb, "RGB").save(path, format="PNG")
    return rgb


def _ellenorizd_lapokat(source: Path, expected: dict[str, np.ndarray]):
    assert {p.name for p in source.parent.glob("*-color_patches.png")} == set(expected)
    for filename, expected_pixels in expected.items():
        with Image.open(source.parent / filename) as image:
            actual = np.asarray(image.convert("RGB"))
        assert actual.shape == expected_pixels.shape, filename
        np.testing.assert_array_equal(actual, expected_pixels, err_msg=filename)


def test_200_szazalek_4x6_atfedes_nelkul_negy_400as_fajl(tmp_path):
    source = tmp_path / "color_patches.png"
    rgb = _color_patches(source)

    files = make_poster_tiles(source, 200, "4x6", False)

    assert {p.name for p in files} == {
        "0-0-color_patches.png",
        "0-1-color_patches.png",
        "1-0-color_patches.png",
        "1-1-color_patches.png",
    }
    expected = {
        "0-0-color_patches.png": rgb[0:400, 0:400],
        "0-1-color_patches.png": rgb[0:400, 400:800],
        "1-0-color_patches.png": rgb[400:800, 0:400],
        "1-1-color_patches.png": rgb[400:800, 400:800],
    }
    _ellenorizd_lapokat(source, expected)


def test_200_szazalek_4x6_atfedessel_negy_440es_fajl(tmp_path):
    source = tmp_path / "color_patches.png"
    rgb = _color_patches(source)

    files = make_poster_tiles(source, 200, "4x6", True)

    assert {p.name for p in files} == {
        "0-0-color_patches.png",
        "0-1-color_patches.png",
        "1-0-color_patches.png",
        "1-1-color_patches.png",
    }
    expected = {
        "0-0-color_patches.png": rgb[0:440, 0:440],
        "0-1-color_patches.png": rgb[0:440, 360:800],
        "1-0-color_patches.png": rgb[360:800, 0:440],
        "1-1-color_patches.png": rgb[360:800, 360:800],
    }
    _ellenorizd_lapokat(source, expected)
