"""#7457: a kijelölt képszöveg forgatókorongja valódi egérhúzással."""

from __future__ import annotations

import math
import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QRect, Qt
from PySide6.QtTest import QTest
from picasapy.app.text_rotation import rotation_from_drag, rotated_top_left
from picasapy.ini import load_document
from picasapy.ini.text_overlay import parse_text
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._editor_test_helpers import EditorTestHelpers
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import kattints


def _gray_split_photos(library: Path) -> None:
    """A korong áttetszőségét sötét/világos szürke képen rögzíti."""
    from PIL import Image, ImageDraw

    for name in ("a.jpg", "b.jpg"):
        image = Image.new("RGB", (320, 160), (64, 64, 64))
        draw = ImageDraw.Draw(image)
        # The text pivot is at 0.316406 × 320 ≈ 101 px; splitting there makes
        # the rendered comparison crop show dark left and light right halves.
        draw.rectangle((101, 0, 319, 159), fill=(116, 116, 116))
        image.save(library / name, "JPEG", quality=100, subsampling=0)


@pytest.fixture
def qml_app_gray(qt_app, tmp_path, request):
    """A vizuális összevetéshez a referencia szürke, két tónusú háttere."""
    from tests.app.qml_functional.conftest import _build_qml_app

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_gray_split_photos,
        keep_modul=request.module,
        nezetek_elore_epit=(
            request.node.get_closest_marker("halasztott_nezetek") is None
        ),
    )


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
        selection = _find_visual(window, "textOverlaySelector_0")
        assert selection is not None
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
        scale = (
            selection.property("rotationScaleX"),
            selection.property("rotationScaleY"),
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
            scale_x=scale[0],
            scale_y=scale[1],
        )
        assert saved.x == pytest.approx(expected_x, abs=0.002)
        assert saved.y == pytest.approx(expected_y, abs=0.002)
        assert edit.property("canUndo") is False
        assert edit.property("canRedo") is False

    @pytest.mark.parametrize("height_delta", [-5, 0, 5])
    def test_rendered_dial_is_fixed_and_handle_rotates_with_selected_text(
        self, qml_app_gray, qt_app, height_delta
    ):
        window, _controller, engine = qml_app_gray
        target_height = window.height() + height_delta
        window.resize(window.width(), target_height)
        assert _varj(qt_app, lambda: window.height() == target_height)

        self._open_viewer(window, qt_app)
        edit = self._edit_controller(engine)
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None
        panel.setProperty("textActive", True)
        edit.enterTextTool()
        edit.setTextDraft("PicasaPy7327")
        edit.previewTextPlacement(0.316406, 0.144531)
        edit.applyText()
        click_area = window.findChild(QObject, "textClickArea")
        assert click_area is not None
        empty_point = click_area.mapToScene(
            QPointF(click_area.width() * 0.86, click_area.height() * 0.16)
        )
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            empty_point.toPoint(),
        )
        assert _varj(qt_app, lambda: edit.property("textSelectedIndex") == -1)
        hit_target = _find_visual(window, "textOverlayHitTarget_0")
        assert hit_target is not None
        kattints(window, qt_app, hit_target)
        assert _varj(qt_app, lambda: edit.property("textSelectedIndex") == 0)

        knob = _find_visual(window, "textRotationKnob_0")
        assert knob is not None and knob.isVisible()
        selection = _find_visual(window, "textOverlaySelector_0")
        handle = _find_visual(window, "textRotationHandle_0")
        assert selection is not None and handle is not None

        selected_center = selection.mapToScene(
            QPointF(selection.width() / 2, selection.height() / 2)
        )
        dial_center = knob.mapToScene(QPointF(knob.width() / 2, knob.height() / 2))
        assert math.hypot(
            selected_center.x() - dial_center.x(),
            selected_center.y() - dial_center.y(),
        ) <= 3.0, (
            "a forgatókorong nem a kijelölt blokk forgáspontja köré került: "
            f"text={selected_center}, dial={dial_center}"
        )

        handle_center = handle.mapToScene(
            QPointF(handle.width() / 2, handle.height() / 2)
        )
        assert math.hypot(
            handle_center.x() - dial_center.x(),
            handle_center.y() - dial_center.y(),
        ) == pytest.approx(81.0, abs=2.0)

        # Check the translucent fill against the same rendered photo with the
        # dial hidden, so this measures actual pixels rather than QML source.
        fill_point = QPointF(
            dial_center.x() + 61 * math.cos(math.radians(55)),
            dial_center.y() + 61 * math.sin(math.radians(55)),
        )
        knob.setOpacity(0.0)
        qt_app.processEvents()
        no_dial = window.grabWindow()
        knob.setOpacity(1.0)
        qt_app.processEvents()
        zero_frame = window.grabWindow()
        dpr = float(zero_frame.devicePixelRatio())
        base_color = _pixel_color(no_dial, fill_point, dpr)
        fill_color = _pixel_color(zero_frame, fill_point, dpr)
        expected_fill = (85, 90, 100)
        for actual, base, target in zip(
            fill_color.getRgb()[:3],
            base_color.getRgb()[:3],
            expected_fill,
            strict=True,
        ):
            expected = round(base * 0.25 + target * 0.75)
            assert abs(actual - expected) <= 18, (
                "a forgatókorong kitöltése nem a mért színnel és áttetszőséggel "
                f"rajzolódott: base={base_color.getRgb()}, "
                f"actual={fill_color.getRgb()}, expected={expected_fill}"
            )

        tick_point = QPointF(dial_center.x(), dial_center.y() - 53)
        zero_tick_luma = _max_luma(zero_frame, tick_point, dpr)
        assert zero_tick_luma >= 150, (
            "a függőleges felső osztás nem a mért 50-56 px-es sugaron látszik: "
            f"luma={zero_tick_luma}"
        )

        dial_center_x = float(knob.property("centerX"))
        dial_center_y = float(knob.property("centerY"))
        text_width = float(knob.property("widthNormalized"))
        text_height = float(knob.property("heightNormalized"))
        scale_x = float(selection.property("rotationScaleX"))
        scale_y = float(selection.property("rotationScaleY"))
        edit.beginTextRotation(
            0.0,
            dial_center_x,
            dial_center_y,
            text_width,
            text_height,
            scale_x,
            scale_y,
        )
        # The inverse of the measured two-stage soft snap gives 17.234°.
        second_filter_input = 18.0 + (17.234 - 15.0) * 9.0 / 15.0
        raw_degrees = 7.0 + second_filter_input * 31.0 / 45.0
        edit.updateTextRotation(math.radians(raw_degrees))
        assert _varj(
            qt_app,
            lambda: edit.property("textOverlayItems")[0]["rotation"]
            == pytest.approx(math.radians(17.234), abs=1e-7),
        )

        inline_text = _find_visual(window, "textContentField")
        pill_frame = _find_visual(window, "textBoxFrame")
        assert inline_text is not None and inline_text.isVisible()
        assert pill_frame is not None and pill_frame.isVisible()
        assert _varj(
            qt_app,
            lambda: inline_text.rotation() == pytest.approx(17.234, abs=0.05)
            and pill_frame.rotation() == pytest.approx(17.234, abs=0.05),
        ), (
            "a szerkesztett szöveg vagy a szürke pirulakeret nem fordult "
            "együtt a blokkal: "
            f"text={inline_text.rotation()}, frame={pill_frame.rotation()}"
        )

        assert _varj(
            qt_app,
            lambda: (
                (layer := _find_visual(window, "textRotationHandleLayer_0"))
                is not None
                and layer.rotation() == pytest.approx(17.234, abs=0.01)
            ),
        ), "a forgó fogantyúréteg nem követte a szöget"
        # The controller replaces the Repeater model after each rotation
        # update; use the current scene-graph items, not wrappers from 0°.
        knob = _find_visual(window, "textRotationKnob_0")
        handle = _find_visual(window, "textRotationHandle_0")
        handle_layer = _find_visual(window, "textRotationHandleLayer_0")
        assert knob is not None and handle is not None and handle_layer is not None
        assert handle_layer.rotation() == pytest.approx(17.234, abs=0.01), (
            "a forgó fogantyúréteg nem követte a szöget: "
            f"rotation={handle_layer.rotation()}"
        )

        rotated_center = knob.mapToScene(
            QPointF(knob.width() / 2, knob.height() / 2)
        )
        assert math.hypot(
            rotated_center.x() - dial_center.x(),
            rotated_center.y() - dial_center.y(),
        ) <= 3.0, "a forgatás elmozdította a blokk középpontját"

        def fogantyu_helyes_e():
            center = knob.mapToScene(
                QPointF(knob.width() / 2, knob.height() / 2)
            )
            point = handle.mapToScene(
                QPointF(handle.width() / 2, handle.height() / 2)
            )
            expected = QPointF(
                center.x() + 81 * math.cos(math.radians(17.234)),
                center.y() + 81 * math.sin(math.radians(17.234)),
            )
            return math.hypot(
                point.x() - expected.x(), point.y() - expected.y()
            ) <= 3.0

        assert _varj(qt_app, fogantyu_helyes_e), (
            "a forgatófogantyú nem a forgás után érvényes képponthelyre került: "
            f"local={handle.mapToItem(knob, QPointF(handle.width() / 2, handle.height() / 2))}, "
            f"layer={handle_layer.mapToItem(knob, QPointF(handle_layer.width() / 2, handle_layer.height() / 2))}, "
            f"parent={handle.parentItem().objectName()}, "
            f"rotation={handle_layer.rotation()}"
        )
        rotated_handle = handle.mapToScene(
            QPointF(handle.width() / 2, handle.height() / 2)
        )
        expected_handle = QPointF(
            rotated_center.x() + 81 * math.cos(math.radians(17.234)),
            rotated_center.y() + 81 * math.sin(math.radians(17.234)),
        )
        assert math.hypot(
            rotated_handle.x() - expected_handle.x(),
            rotated_handle.y() - expected_handle.y(),
        ) <= 3.0, (
            "a forgatófogantyú nem fordult a szöveg szögével: "
            f"actual={rotated_handle}, expected={expected_handle}"
        )

        rotated_frame = window.grabWindow()
        rendered_text_angle = _rendered_text_angle(
            rotated_frame, inline_text, dpr
        )
        assert rendered_text_angle == pytest.approx(17.234, abs=5.0), (
            "a renderelt betűk nem fordultak el 17,234°-kal: "
            f"actual={rendered_text_angle:.3f}°"
        )
        rotated_tick_point = QPointF(
            rotated_center.x(), rotated_center.y() - 53
        )
        rotated_tick_luma = _max_luma(
            rotated_frame, rotated_tick_point, dpr
        )
        assert rotated_tick_luma >= 150
        assert abs(rotated_tick_luma - zero_tick_luma) <= 25, (
            "a korong osztása a szöveggel együtt elfordult: "
            f"zero={zero_tick_luma}, rotated={rotated_tick_luma}"
        )
        rotated_handle_color = _pixel_color(rotated_frame, expected_handle, dpr)
        assert (
            abs(rotated_handle_color.red() - 240) <= 20
            and abs(rotated_handle_color.green() - 90) <= 20
            and abs(rotated_handle_color.blue() - 30) <= 20
        ), (
            "a fogantyú közepének a mért narancsszínnel kell megjelennie: "
            f"{rotated_handle_color.getRgb()}"
        )
        white_button_point = QPointF(
            expected_handle.x() + 3.4 * math.cos(math.radians(17.234)),
            expected_handle.y() + 3.4 * math.sin(math.radians(17.234)),
        )
        white_button_color = _pixel_color(rotated_frame, white_button_point, dpr)
        assert min(white_button_color.red(), white_button_color.green(),
                   white_button_color.blue()) >= 210, (
            "a fogantyú narancsszínű középpontját fehér gombnak kell körülvennie: "
            f"{white_button_color.getRgb()}"
        )

        render_dir = os.environ.get("PICASAPY_7457_RENDER_DIR")
        if render_dir:
            target = Path(render_dir)
            target.mkdir(parents=True, exist_ok=True)
            for label, frame, center in (
                ("0", zero_frame, dial_center),
                ("17", rotated_frame, rotated_center),
            ):
                crop = QRect(
                    round((center.x() - 86.8) * dpr),
                    round((center.y() - 85.2) * dpr),
                    round(200 * dpr),
                    round(170 * dpr),
                )
                assert frame.copy(crop).save(str(target / f"qml-{label}.png"))


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


def _pixel_color(image, point, device_pixel_ratio):
    return image.pixelColor(
        round(point.x() * device_pixel_ratio),
        round(point.y() * device_pixel_ratio),
    )


def _rendered_text_angle(image, text_item, device_pixel_ratio):
    """A látható fehér betűképpontok főtengelyét méri, betűméret nélkül."""
    corners = [
        text_item.mapToScene(QPointF(0, 0)),
        text_item.mapToScene(QPointF(text_item.width(), 0)),
        text_item.mapToScene(QPointF(0, text_item.height())),
        text_item.mapToScene(QPointF(text_item.width(), text_item.height())),
    ]
    x_min = max(
        0,
        math.floor(min(point.x() for point in corners) * device_pixel_ratio),
    )
    x_max = min(
        image.width() - 1,
        math.ceil(max(point.x() for point in corners) * device_pixel_ratio),
    )
    y_min = max(
        0,
        math.floor(min(point.y() for point in corners) * device_pixel_ratio),
    )
    y_max = min(
        image.height() - 1,
        math.ceil(max(point.y() for point in corners) * device_pixel_ratio),
    )

    glyph_pixels = []
    for y in range(y_min, y_max + 1):
        for x in range(x_min, x_max + 1):
            scene_point = QPointF(x / device_pixel_ratio, y / device_pixel_ratio)
            local_point = text_item.mapFromScene(scene_point)
            if not (0 <= local_point.x() <= text_item.width()):
                continue
            if not (0 <= local_point.y() <= text_item.height()):
                continue
            color = image.pixelColor(x, y)
            if min(color.red(), color.green(), color.blue()) >= 190:
                glyph_pixels.append((x, y))

    assert glyph_pixels, "nem találhatók a kirajzolt fehér betűképpontok"
    mean_x = sum(x for x, _ in glyph_pixels) / len(glyph_pixels)
    mean_y = sum(y for _, y in glyph_pixels) / len(glyph_pixels)
    var_x = sum((x - mean_x) ** 2 for x, _ in glyph_pixels)
    var_y = sum((y - mean_y) ** 2 for _, y in glyph_pixels)
    cov_xy = sum(
        (x - mean_x) * (y - mean_y) for x, y in glyph_pixels
    )
    return math.degrees(0.5 * math.atan2(2 * cov_xy, var_x - var_y))


def _max_luma(image, point, device_pixel_ratio, radius=3):
    center_x = round(point.x() * device_pixel_ratio)
    center_y = round(point.y() * device_pixel_ratio)
    return max(
        (
            0.2126 * image.pixelColor(x, y).red()
            + 0.7152 * image.pixelColor(x, y).green()
            + 0.0722 * image.pixelColor(x, y).blue()
            for x in range(center_x - radius, center_x + radius + 1)
            for y in range(center_y - radius, center_y + radius + 1)
        ),
        default=0.0,
    )
