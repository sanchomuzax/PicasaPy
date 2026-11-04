"""Geometriai regreszios tesztek az alkalmazasikon mereteihez (#6514)."""

from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image


_ASSETS_DIR = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "picasapy"
    / "app"
    / "assets"
)
_ICON_ICO = _ASSETS_DIR / "icon.ico"
_ICON_PNG = _ASSETS_DIR / "icon.png"
_LOGO_SVG = _ASSETS_DIR / "logo.svg"
_GENERATOR = Path(__file__).resolve().parents[1] / "scripts" / "generate_app_icon.py"
_SVG_NS = "http://www.w3.org/2000/svg"

_MEASURED = {
    16: (16, 16, 8, 8),
    32: (30, 30, 16, 16),
    48: (44, 44, 23, 23),
    256: (226, 226, 124, 126),
}


def _frame(size: int) -> Image.Image:
    with Image.open(_ICON_ICO) as icon:
        return icon.ico.getimage((size, size)).convert("RGBA")


def _opaque_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    opaque = image.getchannel("A").point(lambda value: 255 if value == 255 else 0)
    bbox = opaque.getbbox()
    assert bbox is not None
    return bbox


def _bbox_center(bbox: tuple[int, int, int, int]) -> tuple[float, float]:
    left, top, right, bottom = bbox
    return (left + right) / 2, (top + bottom) / 2


def test_icon_frames_match_measured_geometry() -> None:
    with Image.open(_ICON_ICO) as icon:
        assert icon.info["sizes"] == {(16, 16), (24, 24), (32, 32), (48, 48),
                                      (64, 64), (128, 128), (256, 256)}

    for size, (expected_width, expected_height, center_x, center_y) in _MEASURED.items():
        frame = _frame(size)
        bbox = _opaque_bbox(frame)
        left, top, right, bottom = bbox
        assert right - left == expected_width
        assert bottom - top == expected_height
        actual_x, actual_y = _bbox_center(bbox)
        assert abs(actual_x - center_x) <= 1
        assert abs(actual_y - center_y) <= 1

        alpha = frame.getchannel("A")
        if size == 16:
            assert alpha.getextrema() == (255, 255)
        else:
            assert alpha.getpixel((0, 0)) == 0
            assert alpha.getpixel((size // 2, top)) == 255
            assert alpha.getpixel((left, size // 2)) == 255
            opaque_count = alpha.histogram()[255]
            assert 0.70 <= opaque_count / (expected_width * expected_height) <= 0.85


def test_scaled_frames_follow_the_256_geometry() -> None:
    for size in (24, 64, 128):
        bbox = _opaque_bbox(_frame(size))
        left, top, right, bottom = bbox
        expected_diameter = 226 * size / 256
        assert abs((right - left) - expected_diameter) <= 2
        assert abs((bottom - top) - expected_diameter) <= 2
        center_x, center_y = _bbox_center(bbox)
        assert abs(center_x - (124 * size / 256)) <= 1
        assert abs(center_y - (126 * size / 256)) <= 1


def test_png_is_the_256_icon_frame() -> None:
    with Image.open(_ICON_PNG) as png:
        png_rgba = png.convert("RGBA")
    assert png_rgba.tobytes() == _frame(256).tobytes()


def test_logo_mark_is_the_icon_generator_source() -> None:
    root = ET.parse(_LOGO_SVG).getroot()
    mark = root.find(f".//{{{_SVG_NS}}}g[@id='picasapy-icon-mark']")
    assert mark is not None
    assert {element.get("id") for element in mark} == {
        "color-1",
        "color-2",
        "color-3",
        "color-4",
        "color-5",
    }
    assert 'MARK_ID = "picasapy-icon-mark"' in _GENERATOR.read_text(encoding="utf-8")


# A színes jel átmérője az eredeti Picasa-képkockákon (telített képpontok
# befoglalója, docs/specs/picasa-inditoikon-meres.md): ennyi kell nálunk is.
_PICASA_SZINES_ATMERO = {16: 14, 32: 29, 48: 42, 256: 210}


def _szines_atmero(image: Image.Image) -> int:
    import numpy as np

    rgba = np.asarray(image).astype(int)
    rgb = rgba[..., :3]
    telitett = ((rgb.max(-1) - rgb.min(-1)) > 60) & (rgba[..., 3] > 128)
    ys, xs = np.nonzero(telitett)
    return max(int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))


def test_szines_kor_atmeroje_az_eredeti_picasaval_egyezik() -> None:
    for size, vart in _PICASA_SZINES_ATMERO.items():
        tures = 1 if size == 32 else 0
        assert abs(_szines_atmero(_frame(size)) - vart) <= tures, size


def test_a_16_px_csempe_vilagos_mint_az_eredeti() -> None:
    sarok = _frame(16).getpixel((0, 0))
    assert sarok[3] == 255
    assert min(sarok[:3]) >= 240
