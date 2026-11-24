"""#7457: a kijelölt képszöveg forgatókorongja valódi egérhúzással."""

from __future__ import annotations

import math

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest
from picasapy.app.text_rotation import rotation_from_drag, rotated_top_left
from picasapy.ini import load_document
from picasapy.ini.text_overlay import parse_text
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import kattints


def _varj(qt_app, feltetel, masodperc=10.0):
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


class TestTextRotation(EditorTestHelpers):
    @pytest.mark.parametrize("height_delta", [-5, 0, 5])
    def test_selected_text_rotates_by_dragging_the_red_handle(
        self, qml_app, qt_app, tmp_path, height_delta
    ):
        window, _controller, engine = qml_app
        target_height = window.height() + height_delta
        window.resize(window.width(), target_height)
        assert _varj(qt_app, lambda: window.height() == target_height)

        self._open_viewer(window, qt_app)
        edit = self._edit_controller(engine)
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None
        panel.setProperty("textActive", True)
        edit.enterTextTool()
        edit.setTextDraft("Rotate")
        edit.previewTextPlacement(0.32, 0.4)
        edit.applyText()
        qt_app.processEvents()

        click_area = window.findChild(QObject, "textClickArea")
        assert click_area is not None
        empty = click_area.mapToScene(
            QPointF(click_area.width() * 0.86, click_area.height() * 0.16)
        )
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, empty.toPoint())
        assert _varj(qt_app, lambda: edit.property("textSelectedIndex") == -1)

        hit_target = next(
            item
            for item in _visual_items(window)
            if item.objectName() == "textOverlayHitTarget_0"
        )
        kattints(window, qt_app, hit_target)
        assert _varj(qt_app, lambda: edit.property("textSelectedIndex") == 0)

        assert _varj(
            qt_app, lambda: _find_visual(window, "textRotationKnob_0") is not None
        ), (
            "kijelöléskor nem jelent meg a forgatókorong"
        )
        knob = _find_visual(window, "textRotationKnob_0")
        assert knob.isVisible()
        handle = next(
            item
            for item in _visual_items(window)
            if item.objectName() == "textRotationHandle_0"
        )
        start = handle.mapToScene(QPointF(handle.width() / 2, handle.height() / 2))
        center = knob.mapToScene(QPointF(knob.width() / 2, knob.height() / 2))
        start_point = start.toPoint()
        start_angle = math.atan2(
            start_point.y() - center.y(), start_point.x() - center.x()
        )
        before = edit.property("textOverlayItems")[0]["rotation"]
        pivot = (
            knob.property("centerX"),
            knob.property("centerY"),
        )
        text_size = (
            knob.property("widthNormalized"),
            knob.property("heightNormalized"),
        )
        endpoint = start_point + QPoint(0, 30)
        end_angle = math.atan2(
            endpoint.y() - center.y(), endpoint.x() - center.x()
        )
        expected = rotation_from_drag(start_angle, end_angle, before)

        QTest.mousePress(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            start_point,
        )
        QTest.mouseMove(window, endpoint, 100)
        QTest.mouseRelease(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            endpoint,
        )
        assert _varj(
            qt_app,
            lambda: edit.property("textOverlayItems")[0]["rotation"]
            == pytest.approx(expected, abs=math.radians(0.2)),
        ), (
            "a fogantyú húzása nem adta a végponti szöget: "
            f"actual={edit.property('textOverlayItems')[0]['rotation']!r}, "
            f"expected={expected!r}, start={start!r}, end={endpoint!r}, "
            f"center={center!r}"
        )
        edit.applyText()
        assert _varj(qt_app, lambda: edit.property("hasTextOverlay") is True)
        section = load_document(tmp_path / "kepek" / ".picasa.ini").section(
            "a.jpg"
        )
        saved = parse_text(section.get("text")).primary.geometry
        assert saved.rotation == pytest.approx(expected, abs=math.radians(0.2))
        expected_x, expected_y = rotated_top_left(
            center_x=pivot[0],
            center_y=pivot[1],
            width=text_size[0],
            height=text_size[1],
            angle=expected,
        )
        assert saved.x == pytest.approx(expected_x, abs=0.002)
        assert saved.y == pytest.approx(expected_y, abs=0.002)
        assert edit.property("canUndo") is False
        assert edit.property("canRedo") is False


def _visual_items(window):
    stack = list(window.contentItem().childItems())
    while stack:
        item = stack.pop()
        yield item
        stack.extend(item.childItems())


def _find_visual(window, name):
    return next(
        (item for item in _visual_items(window) if item.objectName() == name),
        None,
    )
