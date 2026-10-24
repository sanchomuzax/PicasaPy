"""Az eredeti színválasztó HSL-palettájának képpontjai (#5730)."""

from __future__ import annotations

import colorsys
from functools import lru_cache
import math

from PySide6.QtCore import Slot
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

_WIDTH = 181
_HEIGHT = 147
_HUE_ANCHORS = (
    (1, 213, 64, 62), (6, 210, 64, 47), (11, 210, 87, 47),
    (16, 210, 115, 47), (21, 210, 143, 47), (26, 210, 169, 47),
    (31, 210, 192, 47), (36, 210, 209, 47), (41, 196, 210, 47),
    (46, 175, 210, 47), (51, 149, 210, 47), (56, 121, 210, 47),
    (61, 95, 210, 47), (66, 70, 210, 47), (71, 52, 210, 47),
    (76, 47, 210, 55), (81, 47, 210, 75), (86, 47, 210, 102),
    (91, 47, 210, 130), (96, 47, 210, 157), (101, 47, 210, 183),
    (106, 47, 210, 204), (111, 47, 204, 210), (116, 47, 184, 210),
    (121, 47, 160, 210), (126, 47, 132, 210), (131, 47, 105, 210),
    (136, 47, 79, 210), (141, 47, 59, 210), (146, 48, 47, 210),
    (151, 67, 47, 210), (156, 91, 47, 210), (161, 119, 47, 210),
    (166, 148, 47, 210), (171, 174, 47, 210), (176, 196, 47, 210),
    (180, 212, 62, 213),
)
_LIGHTNESS_ANCHORS = (
    (56, 234, 250, 241), (61, 219, 247, 232), (66, 199, 242, 220),
    (71, 176, 238, 205), (76, 150, 233, 189), (81, 124, 226, 172),
    (86, 99, 221, 156), (91, 76, 217, 143), (96, 58, 212, 130),
    (101, 45, 209, 122), (106, 42, 195, 114), (111, 38, 179, 105),
    (116, 34, 158, 92), (121, 29, 135, 79), (126, 24, 112, 65),
    (131, 19, 89, 52), (136, 15, 69, 41), (141, 11, 52, 31),
    (144, 9, 44, 26),
)


def _hue_degrees(red: int, green: int, blue: int) -> float:
    hue, _lightness, _saturation = colorsys.rgb_to_hls(
        red / 255, green / 255, blue / 255
    )
    return hue * 360


def _lightness(red: int, green: int, blue: int) -> float:
    _hue, lightness, _saturation = colorsys.rgb_to_hls(
        red / 255, green / 255, blue / 255
    )
    return lightness


_HUE_PROFILE = tuple(
    (x, _hue_degrees(red, green, blue))
    for x, red, green, blue in _HUE_ANCHORS
)
_LIGHTNESS_PROFILE = tuple(
    (y, _lightness(red, green, blue))
    for y, red, green, blue in _LIGHTNESS_ANCHORS
)


def _interpolate(profile: tuple[tuple[int, float], ...], point: int) -> float:
    for (left_x, left_value), (right_x, right_value) in zip(
        profile, profile[1:], strict=False
    ):
        if point <= right_x:
            fraction = (point - left_x) / (right_x - left_x)
            return left_value + (right_value - left_value) * fraction
    return profile[-1][1]


def _hsl_rgb(hue: float, saturation: float, lightness: float) -> tuple[int, int, int]:
    red, green, blue = colorsys.hls_to_rgb(hue / 360, lightness, saturation)
    return tuple(
        math.floor(channel * 255 + 0.5) for channel in (red, green, blue)
    )


def palette_color_at(x: int, y: int, mode: int) -> str:
    """A HSL-mező egy képpontja, round-half-up kerekítéssel."""
    x = min(179, max(2, int(x)))
    y = min(144, max(56, int(y)))
    saturation = 97 / 253 if mode == 1 else 163 / 253
    rgb = _hsl_rgb(
        _interpolate(_HUE_PROFILE, x),
        saturation,
        _interpolate(_LIGHTNESS_PROFILE, y),
    )
    return "#" + "".join(f"{channel:02x}" for channel in rgb)


@lru_cache(maxsize=2)
def palette_image(mode: int) -> QImage:
    """A spec belső tartományát tartalmazó, átlátszó QImage."""
    image = QImage(_WIDTH, _HEIGHT, QImage.Format.Format_ARGB32)
    image.fill(0)
    saturation = 97 / 253 if mode == 1 else 163 / 253
    for x in range(2, 180):
        hue = _interpolate(_HUE_PROFILE, x)
        for y in range(56, 145):
            red, green, blue = _hsl_rgb(
                hue, saturation, _interpolate(_LIGHTNESS_PROFILE, y)
            )
            image.setPixel(x, y, 0xFF000000 | red << 16 | green << 8 | blue)
    return image


class ColorPaletteProvider(QQuickImageProvider):
    """A QML Image számára adja a palettát és a kattintott szín értékét."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)

    def requestImage(self, image_id, size, requested_size):
        mode = 1 if image_id.endswith("1") else 0
        image = palette_image(mode)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image

    @Slot(int, int, int, result=str)
    def colorAt(self, x: int, y: int, mode: int) -> str:
        return palette_color_at(x, y, mode)


__all__ = ["ColorPaletteProvider", "palette_color_at", "palette_image"]
