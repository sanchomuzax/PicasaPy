"""#7457: a renderelő a blokk középpontja körül forgat."""

from __future__ import annotations

import math

import numpy as np
import pytest

from picasapy.ini.text_overlay import DEFAULT_FAMILY
from picasapy.render import text_overlay
from picasapy.render.text_fonts import qt_font_for


def test_rotation_transform_uses_center_and_clockwise_direction(qt_app, monkeypatch):
    image = np.zeros((90, 140, 3), dtype=np.uint8)
    angle = math.radians(17.234)
    font_size = 36
    font_px = text_overlay.betumeret_keppontban(font_size, image.shape[0])
    font = qt_font_for(DEFAULT_FAMILY, font_px)
    text_width, text_height = text_overlay._text_box_size(
        "Rotate", font, None, font_px / text_overlay._SCALE_TO_PIXELS
    )
    rotated_width = (
        text_width * abs(math.cos(angle)) + text_height * abs(math.sin(angle))
    )
    rotated_height = (
        text_width * abs(math.sin(angle)) + text_height * abs(math.cos(angle))
    )
    expected_center = (
        0.3 * image.shape[1] + rotated_width / 2,
        0.6 * image.shape[0] + rotated_height / 2,
    )
    original = text_overlay.cv2.getRotationMatrix2D
    captured = []

    def track_transform(center, degrees, scale):
        captured.append((center, degrees, scale))
        return original(center, degrees, scale)

    monkeypatch.setattr(text_overlay.cv2, "getRotationMatrix2D", track_transform)
    result = text_overlay.apply_text_overlay(
        image,
        "Rotate",
        x=0.3,
        y=0.6,
        font_size_pt=font_size,
        rotation=angle,
        font_family=DEFAULT_FAMILY,
    )

    assert result.shape == image.shape
    assert len(captured) == 1
    center, degrees, scale = captured[0]
    assert center == pytest.approx(expected_center, abs=0.01)
    assert degrees == pytest.approx(-17.234, abs=1e-6)
    assert scale == 1.0
