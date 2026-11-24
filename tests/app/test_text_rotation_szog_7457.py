"""#7457: a szövegforgatás végponti szabálya és dobozgeometriája."""

from __future__ import annotations

import math

import pytest

from picasapy.ini import load_document
from picasapy.ini.text_overlay import parse_text
from picasapy.app.text_rotation import (
    rotation_from_drag,
    rotated_bounds,
    rotated_top_left,
    snap_text_rotation_degrees,
)
from support.jpeg_factory import make_jpeg


@pytest.mark.parametrize(
    ("dy", "expected"),
    [
        (13, 0.00),
        (15, 3.47),
        (22, 14.74),
        (30, 17.24),
        (37, 27.30),
        (47, 30.96),
        (53, 38.42),
        (57, 43.09),
        (60, 45.00),
    ],
)
def test_measured_vertical_drag_uses_pointer_angles_and_soft_snaps(dy, expected):
    """A node saját, képpont alatti középpontjával a mért sor 0,2°-on belül áll."""
    center = (626.8, 405.2)
    start = (708.0, 405.0)
    end = (708.0, 405.0 + dy)
    start_angle = math.atan2(start[1] - center[1], start[0] - center[0])
    end_angle = math.atan2(end[1] - center[1], end[0] - center[0])

    rotation = math.degrees(rotation_from_drag(start_angle, end_angle, 0.0))

    assert rotation == pytest.approx(expected, abs=0.2)


def test_soft_snap_has_no_45_degree_upper_clamp():
    assert snap_text_rotation_degrees(62.0) > 45.0


@pytest.mark.parametrize(
    ("width", "height", "degrees", "expected"),
    [
        (100.0, 20.0, 0.0, (100.0, 20.0)),
        (100.0, 20.0, 90.0, (20.0, 100.0)),
        (100.0, 20.0, 17.234, (101.436, 48.730)),
    ],
)
def test_rotation_bounds_match_the_rotated_rectangle(width, height, degrees, expected):
    assert rotated_bounds(width, height, math.radians(degrees)) == pytest.approx(
        expected, abs=0.001
    )


def test_stored_position_is_the_rotated_bounds_top_left():
    left, top = rotated_top_left(
        center_x=0.5,
        center_y=0.5,
        width=0.2,
        height=0.1,
        angle=math.radians(30),
    )
    rotated_width, rotated_height = rotated_bounds(
        0.2, 0.1, math.radians(30)
    )
    assert left + rotated_width / 2 == pytest.approx(0.5)
    assert top + rotated_height / 2 == pytest.approx(0.5)


def test_apply_persists_rotation_radians_and_rotated_top_left(qt_app, tmp_path):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    photo = make_jpeg(tmp_path / "rotation.jpg", size=(320, 160))
    edit = EditController(EditPreviewProvider())
    edit.beginEdit("7457", str(photo))
    edit.enterTextTool()
    edit.setTextDraft("Rotate")
    edit.previewTextPlacement(0.3, 0.6)
    edit.applyText()
    edit.selectTextOverlay(0)

    center = (0.42, 0.64)
    width, height = 0.2, 0.06
    start_angle = 0.0
    end_angle = math.radians(20)
    edit.beginTextRotation(start_angle, *center, width, height, 320.0, 160.0)
    edit.updateTextRotation(end_angle)
    expected_rotation = rotation_from_drag(start_angle, end_angle, 0.0)
    assert edit._current_text_spec()[0].rotation == pytest.approx(
        expected_rotation, abs=1e-6
    )
    edit.applyText()

    section = load_document(photo.parent / ".picasa.ini").section(photo.name)
    saved = parse_text(section.get("text")).primary.geometry
    expected_x, expected_y = rotated_top_left(
        center_x=center[0],
        center_y=center[1],
        width=width,
        height=height,
        angle=expected_rotation,
        scale_x=320.0,
        scale_y=160.0,
    )
    assert saved.rotation == pytest.approx(expected_rotation, abs=1e-6)
    assert saved.rotation > 0
    assert saved.x == pytest.approx(expected_x, abs=1e-6)
    assert saved.y == pytest.approx(expected_y, abs=1e-6)
