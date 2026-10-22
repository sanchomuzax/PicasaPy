"""#4268 — a poszterlapok kimeneti geometriája és tartalma."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from picasapy.printing import poster
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


def _capture_encoder(monkeypatch):
    encoded: list[tuple[str, np.ndarray, list[int] | None]] = []

    def imencode(extension, image, params=None):
        encoded.append((extension, image.copy(), params))
        return True, np.frombuffer(b"encoded", dtype=np.uint8)

    monkeypatch.setattr(poster.cv2, "imencode", imencode)
    return encoded


def _assert_encoded_tiles(source, files, expected, encoded):
    assert tuple(path.name for path in files) == tuple(expected)
    assert all(path.parent == source.parent for path in files)
    assert len(encoded) == len(expected)
    for path, name, (extension, actual_pixels, _params) in zip(
        files, expected, encoded, strict=True
    ):
        assert path.name == name
        assert extension == ".jpg"
        assert path.read_bytes() == b"encoded"
        actual_rgb = poster.cv2.cvtColor(actual_pixels, poster.cv2.COLOR_BGR2RGB)
        np.testing.assert_array_equal(actual_rgb, expected[name], err_msg=name)


def test_200_szazalek_4x6_atfedes_nelkul_negy_400as_fajl(tmp_path, monkeypatch):
    source = tmp_path / "color_patches.png"
    rgb = _color_patches(source)
    encoded = _capture_encoder(monkeypatch)

    files = make_poster_tiles(source, 200, "4x6", False)

    expected = {
        "0-0-color_patches.jpg": rgb[0:400, 0:400],
        "1-0-color_patches.jpg": rgb[0:400, 400:800],
        "0-1-color_patches.jpg": rgb[400:800, 0:400],
        "1-1-color_patches.jpg": rgb[400:800, 400:800],
    }
    _assert_encoded_tiles(source, files, expected, encoded)


def test_200_szazalek_4x6_atfedessel_negy_440es_fajl(tmp_path, monkeypatch):
    source = tmp_path / "color_patches.png"
    rgb = _color_patches(source)
    encoded = _capture_encoder(monkeypatch)

    files = make_poster_tiles(source, 200, "4x6", True)

    expected = {
        "0-0-color_patches.jpg": rgb[0:440, 0:440],
        "1-0-color_patches.jpg": rgb[0:440, 360:800],
        "0-1-color_patches.jpg": rgb[360:800, 0:440],
        "1-1-color_patches.jpg": rgb[360:800, 360:800],
    }
    _assert_encoded_tiles(source, files, expected, encoded)


@pytest.mark.parametrize("source_format,source_suffix", [("PNG", ".png"), ("JPEG", ".jpg")])
def test_kimenet_fajlnev_es_formatum_png_es_jpeg_forrasnal(
    tmp_path, source_format, source_suffix
):
    source = tmp_path / f"source{source_suffix}"
    Image.new("RGB", (80, 80), color=(20, 40, 60)).save(source, format=source_format)

    files = make_poster_tiles(source, 200, "4x6", False)

    assert tuple(path.name for path in files) == (
        "0-0-source.jpg",
        "1-0-source.jpg",
        "0-1-source.jpg",
        "1-1-source.jpg",
    )
    for path in files:
        assert path.parent == source.parent
        assert path.suffix == ".jpg"
        with Image.open(path) as output:
            assert output.format == "JPEG"


def test_jpeg_kodolo_90es_minoseget_ad_at(tmp_path, monkeypatch):
    source = tmp_path / "source.png"
    Image.new("RGB", (80, 80), color=(20, 40, 60)).save(source, format="PNG")
    actual_imencode = poster.cv2.imencode
    calls = []

    def capture_params(extension, image, params=None):
        calls.append((extension, None if params is None else list(params)))
        if params is None:
            return actual_imencode(extension, image)
        return actual_imencode(extension, image, params)

    monkeypatch.setattr(poster.cv2, "imencode", capture_params)

    make_poster_tiles(source, 200, "4x6", False)

    expected = (".jpg", [poster.cv2.IMWRITE_JPEG_QUALITY, 90])
    assert calls == [expected] * 4


def test_racs_nagyitasa_200_1000_szazalekig_n_negyzet(tmp_path, monkeypatch):
    source = tmp_path / "grid.png"
    source.write_bytes(b"test source")
    monkeypatch.setattr(
        poster, "render_edited_image", lambda _path: np.zeros((100, 100, 3), dtype=np.uint8)
    )
    _capture_encoder(monkeypatch)

    for count in range(2, 11):
        files = make_poster_tiles(source, count * 100, "4x6", False)

        assert len(files) == count * count
        assert {path.name for path in files} == {
            f"{column}-{row}-grid.jpg"
            for row in range(count)
            for column in range(count)
        }
