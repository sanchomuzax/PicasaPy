"""#4603 — a poszter az EXIF-tájolású, szerkesztett képből készüljön."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from picasapy.export.exporter import render_photo_pixels
from picasapy.ini.filters import parse_filters_prefix
from picasapy.lazy_cv2 import cv2
from picasapy.printing.poster import make_poster_tiles


def test_exif_es_picasa_szerkesztesek_bekerulnek_a_poszterlapokba(
    tmp_path: Path,
) -> None:
    source = tmp_path / "exif-edited.jpg"
    yy, xx = np.indices((400, 800), dtype=np.uint16)
    rgb = np.empty((400, 800, 3), dtype=np.uint8)
    rgb[..., 0] = xx % 256
    rgb[..., 1] = yy % 256
    rgb[..., 2] = (xx // 40 * 29 + yy // 40 * 17) % 256
    exif = Image.Exif()
    exif[274] = 6  # EXIF: 90° clockwise
    Image.fromarray(rgb, "RGB").save(
        source, format="JPEG", quality=100, subsampling=0, exif=exif
    )
    (tmp_path / ".picasa.ini").write_text(
        "[exif-edited.jpg]\n"
        "filters=bw=1;\n"
        "rotate=rotate(1)\n"
        "flipped=flipped(2)\n",
        encoding="utf-8",
    )

    files = make_poster_tiles(source, 200, "4x6", False)

    expected = render_photo_pixels(
        source,
        parse_filters_prefix("bw=1;"),
        rotate_steps=1,
        flip_flags=2,
    )
    height, width = expected.shape[:2]
    assert (width, height) == (800, 400)
    assert len(files) == 4
    for row in range(2):
        for column in range(2):
            tile = expected[
                row * height // 2 : (row + 1) * height // 2,
                column * width // 2 : (column + 1) * width // 2,
            ]
            encoded_ok, encoded_expected = cv2.imencode(".jpg", tile)
            assert encoded_ok
            expected_pixels = cv2.imdecode(encoded_expected, cv2.IMREAD_COLOR)
            page = next(
                path for path in files if path.name.startswith(f"{row}-{column}-")
            )
            actual_pixels = cv2.imdecode(
                np.frombuffer(page.read_bytes(), dtype=np.uint8), cv2.IMREAD_COLOR
            )
            assert actual_pixels.shape == expected_pixels.shape, page.name
            np.testing.assert_array_equal(actual_pixels, expected_pixels)
