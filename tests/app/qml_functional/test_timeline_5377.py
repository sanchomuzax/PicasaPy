"""#5377: a teljes képernyős Időrend bemutató felhasználói útjai."""

from datetime import datetime, timezone
import os
from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
import pytest

import picasapy.app
from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


def _child(window, name):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található"
    return item


def wait_until(qt_app, predicate, timeout_ms=3000):
    return var_feltetelre(qt_app, predicate, timeout_ms / 1000)


def _click_menu_item(window, qt_app, item_name, menu_name):
    menu = _child(window, menu_name)
    item = _child(window, item_name)
    assert QMetaObject.invokeMethod(
        menu, "open", Qt.ConnectionType.DirectConnection
    )
    assert wait_until(qt_app, lambda: item.isVisible() and item.width() > 0)
    center = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )


def test_ctrl5_opens_fullscreen_timeline_without_selection(qml_app, qt_app):
    window, controller, engine = qml_app
    window.setProperty("selectedIndex", -1)
    window.setProperty("selectedIndexes", [])
    window.requestActivate()
    assert wait_until(qt_app, window.isActive), "a főablak nem lett aktív"

    QTest.keyClick(
        window,
        Qt.Key.Key_5,
        Qt.KeyboardModifier.ControlModifier,
    )

    timeline = _child(window, "timelineView")
    assert wait_until(qt_app, lambda: window.property("timelineOpen") is True)
    assert window.visibility() == QQuickWindow.Visibility.FullScreen
    assert timeline.isVisible()
    assert _child(window, "timelinePresentationPanel").isVisible()
    assert _child(window, "timelineCollectionName").property("text")
    assert _child(window, "timelineCollectionDate").property("text")
    for control in (
        "timelineListIcon",
        "timelinePreviousIcon",
        "timelinePlayIcon",
        "timelineNextIcon",
        "timelineDateSliderTrack",
        "timelineDateSliderHandle",
        "timelineDateRangeStart",
        "timelineDateRangeEnd",
    ):
        assert _child(window, control).isVisible(), f"a(z) {control} nem látszik"
    assert window.property("selectedIndex") == -1


def test_right_left_space_and_escape_use_real_keys(qml_app, qt_app):
    window, controller, engine = qml_app
    root = Path(controller._roots[0])
    second_folder = root / "second-collection"
    second_folder.mkdir()
    older_photo = second_folder / "c.jpg"
    newer_photo = second_folder / "d.jpg"
    make_jpeg(older_photo, size=(120, 90))
    make_jpeg(newer_photo, size=(120, 90))
    older_timestamp = datetime(2020, 1, 2, tzinfo=timezone.utc).timestamp()
    os.utime(older_photo, (older_timestamp, older_timestamp))
    os.utime(newer_photo, (older_timestamp, older_timestamp))
    with open_index(controller._db_path) as conn:
        sync_tree(conn, root)
    timeline_controller = engine.rootContext().contextProperty("timelineController")
    timeline_controller.reload()
    assert len(timeline_controller.collections) >= 2
    date_keys = [row["dateKey"] for row in timeline_controller.collections]
    assert date_keys == sorted(date_keys)

    window.requestActivate()
    assert wait_until(qt_app, window.isActive), "a főablak nem lett aktív"
    QTest.keyClick(window, Qt.Key.Key_5, Qt.KeyboardModifier.ControlModifier)
    timeline = _child(window, "timelineView")
    assert wait_until(qt_app, timeline.isVisible)
    timeline.forceActiveFocus()
    assert timeline.property("currentIndex") == 0

    QTest.keyClick(window, Qt.Key.Key_Right)
    assert wait_until(qt_app, lambda: timeline.property("currentIndex") == 1)
    QTest.keyClick(window, Qt.Key.Key_Left)
    assert wait_until(qt_app, lambda: timeline.property("currentIndex") == 0)
    QTest.keyClick(window, Qt.Key.Key_Right)
    assert wait_until(qt_app, lambda: timeline.property("currentIndex") == 1)
    expected_count = timeline_controller.collections[1]["count"]

    QTest.keyClick(window, Qt.Key.Key_Space)
    slideshow = _child(window, "slideshowView")
    assert wait_until(qt_app, slideshow.isVisible)
    assert window.property("timelineOpen") is False
    assert slideshow.property("photosModel").rowCount() == expected_count
    assert slideshow.property("currentIndex") == 0
    QTest.keyClick(window, Qt.Key.Key_Space)
    assert slideshow.property("playing") is False

    QTest.keyClick(window, Qt.Key.Key_End)
    assert wait_until(qt_app, lambda: slideshow.property("currentIndex") == expected_count - 1)
    QTest.keyClick(window, Qt.Key.Key_Left)
    assert wait_until(qt_app, lambda: slideshow.property("currentIndex") == expected_count - 2)
    QTest.keyClick(window, Qt.Key.Key_End)
    assert wait_until(qt_app, lambda: slideshow.property("currentIndex") == expected_count - 1)
    QTest.keyClick(window, Qt.Key.Key_Home)
    assert wait_until(qt_app, lambda: slideshow.property("currentIndex") == 0)

    QTest.keyClick(window, Qt.Key.Key_Escape)
    assert wait_until(qt_app, lambda: not slideshow.isVisible())
    assert window.visibility() == QQuickWindow.Visibility.Windowed


def test_view_menu_click_opens_timeline(qml_app, qt_app):
    window, _controller, _engine = qml_app
    item = _child(window, "menuViewTimeline")
    assert item.property("enabled") is True
    _click_menu_item(window, qt_app, "menuViewTimeline", "menuView")
    assert wait_until(qt_app, lambda: window.property("timelineOpen") is True)
    assert _child(window, "timelineView").isVisible()


def test_toolbar_button_click_opens_timeline(qml_app, qt_app):
    window, _controller, _engine = qml_app
    button = _child(window, "toolbarTimelineButton")
    assert button.property("enabled") is True
    center = button.mapToScene(button.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    assert wait_until(qt_app, lambda: window.property("timelineOpen") is True)
    assert _child(window, "timelineView").isVisible()


@pytest.mark.parametrize("height", [795, 800, 805])
def test_timeline_render_geometry_tracks_window_height(qml_app, qt_app, height):
    window, _controller, _engine = qml_app
    window.showNormal()
    window.resize(1000, height)
    assert wait_until(qt_app, lambda: window.height() == height)
    window.setProperty("timelineOpen", True)
    assert wait_until(qt_app, lambda: _child(window, "timelineView").isVisible())

    timeline = _child(window, "timelineView")
    panel = _child(window, "timelinePresentationPanel")
    assert panel.width() == 600
    assert panel.height() == 480
    expected_x = (timeline.width() - panel.width()) / 2
    expected_y = (timeline.height() - panel.height()) / 2
    assert abs(panel.x() - expected_x) <= 3
    assert abs(panel.y() - expected_y) <= 3

    frame = window.grabWindow()
    assert not frame.isNull(), "az Időrend képkockája nem renderelődött"
    background_point = timeline.mapToScene(QPointF(8, 8))
    background = frame.pixelColor(
        round(background_point.x()), round(background_point.y())
    )
    assert background.name().lower() == "#000000"
    curve = _child(window, "timelineBackgroundCurve")
    blank_point = curve.mapToScene(QPointF(curve.width() * 0.1, 10))
    curve_point = curve.mapToScene(
        QPointF(curve.width() * 0.15, curve.height() * 0.8)
    )
    blank = frame.pixelColor(round(blank_point.x()), round(blank_point.y()))
    painted = frame.pixelColor(round(curve_point.x()), round(curve_point.y()))
    assert painted != blank, "a szürke háttérgörbe nem rajzolódott ki"


def _item_contains_pixel(image, item, predicate):
    origin = item.mapToScene(QPointF(0, 0))
    left = max(0, round(origin.x()))
    top = max(0, round(origin.y()))
    right = min(image.width(), round(origin.x() + item.width()))
    bottom = min(image.height(), round(origin.y() + item.height()))
    return any(
        predicate(image.pixelColor(x, y))
        for y in range(top, bottom)
        for x in range(left, right)
    )


def _is_light_ink(color):
    return min(color.red(), color.green(), color.blue()) > 185


def _is_dark_ink(color):
    return max(color.red(), color.green(), color.blue()) < 180


def test_timeline_reference_font_sizes_are_protected_by_source():
    qml_path = (
        Path(picasapy.app.__file__).parent
        / "qml"
        / "PicasaPy"
        / "TimelineView.qml"
    )
    source = qml_path.read_text(encoding="utf-8")
    name = source.split('objectName: "timelineCollectionName"', 1)[1].split(
        'objectName: "timelineCollectionDate"', 1
    )[0]
    date = source.split('objectName: "timelineCollectionDate"', 1)[1].split(
        'objectName: "timelineDottedArc"', 1
    )[0]
    range_start = source.split('objectName: "timelineDateRangeStart"', 1)[1].split(
        'objectName: "timelineDateRangeEnd"', 1
    )[0]
    range_end = source.split('objectName: "timelineDateRangeEnd"', 1)[1]
    assert "font.pixelSize: 19" in name
    assert "font.pixelSize: 14" in date
    assert "font.pixelSize: 11" in range_start
    assert "font.pixelSize: 11" in range_end


@pytest.mark.parametrize("height", [1019, 1024, 1029])
def test_timeline_rendered_card_matches_reference_structure(
    qml_app_szines_belyegkep, qt_app, tmp_path, height
):
    window, controller, engine = qml_app_szines_belyegkep
    root = Path(controller._roots[0])
    collection = root / "PicasaTeszt"
    collection.mkdir()
    earlier = datetime(2026, 10, 1, 12, tzinfo=timezone.utc).timestamp()
    later = datetime(2026, 10, 15, 12, tzinfo=timezone.utc).timestamp()
    for photo in root.glob("*.jpg"):
        os.utime(photo, (later, later))
    for name in ("first.jpg", "second.jpg"):
        photo = collection / name
        make_jpeg(photo, size=(160, 120))
        os.utime(photo, (earlier, earlier))
    os.utime(collection, (earlier, earlier))
    os.utime(root, (later, later))
    with open_index(controller._db_path) as conn:
        sync_tree(conn, root)
    timeline_controller = engine.rootContext().contextProperty("timelineController")
    timeline_controller.reload()
    assert len(timeline_controller.collections) == 2
    assert timeline_controller.collections[0]["name"] == "PicasaTeszt"

    window.showNormal()
    window.resize(1280, height)
    assert wait_until(qt_app, lambda: window.width() == 1280)
    assert wait_until(qt_app, lambda: window.height() == height)
    window.setProperty("timelineOpen", True)
    timeline = _child(window, "timelineView")
    panel = _child(window, "timelinePresentationPanel")
    assert wait_until(qt_app, lambda: timeline.isVisible() and panel.width() > 0)

    frame = window.grabWindow()
    assert not frame.isNull()
    if height == 1024:
        frame.save(str(tmp_path / "timeline-before-fix.png"))

    def point(x, y):
        scene = panel.mapToScene(QPointF(x, y))
        return frame.pixelColor(round(scene.x()), round(scene.y()))

    surface = point(12, 12)
    ellipse = point(210, 125)
    controls = point(100, 418)
    slider_background = point(10, 460)
    name = _child(window, "timelineCollectionName")
    date = _child(window, "timelineCollectionDate")
    start_date = _child(window, "timelineDateRangeStart")
    end_date = _child(window, "timelineDateRangeEnd")
    slider = _child(window, "timelineDateSliderTrack")
    handle = _child(window, "timelineDateSliderHandle")
    photos = _child(window, "timelineThumbStack")
    failures = []
    if min(surface.red(), surface.green(), surface.blue()) <= 100:
        failures.append(f"a panel felülete túl sötét: {surface.name()}")
    if ellipse.blue() <= ellipse.red() + 4:
        failures.append(f"a kékesszürke ellipszis hiányzik: {ellipse.name()}")
    if min(controls.red(), controls.green(), controls.blue()) <= 175:
        failures.append(f"a vezérlősáv nem világos: {controls.name()}")
    if min(
        slider_background.red(),
        slider_background.green(),
        slider_background.blue(),
    ) <= 160:
        failures.append("a dátumcsúszka alatti háttér nem világosszürke")
    if not _item_contains_pixel(frame, name, _is_light_ink):
        failures.append("a gyűjteménynév nem rajzolódik ki")
    if not _item_contains_pixel(frame, date, _is_light_ink):
        failures.append("a gyűjtemény dátuma nem rajzolódik ki")
    if not _item_contains_pixel(frame, start_date, _is_dark_ink):
        failures.append("a csúszka kezdődátuma nem rajzolódik ki")
    if not _item_contains_pixel(frame, end_date, _is_dark_ink):
        failures.append("a csúszka végdátuma nem rajzolódik ki")
    expected_handle_x = slider.mapToScene(QPointF(
        (slider.width() - handle.width()) * 0.305 + handle.width() / 2, 0
    )).x()
    handle_center = handle.mapToScene(
        QPointF(handle.width() / 2, handle.height() / 2)
    ).x()
    if abs(handle_center - expected_handle_x) > 3:
        failures.append("a csúszka gombja nem a referencia mért helyén áll")
    photo_origin = photos.mapToScene(QPointF(0, 0))
    photo_pixels = sum(
        1
        for y in range(round(photo_origin.y()), round(photo_origin.y() + photos.height()))
        for x in range(round(photo_origin.x()), round(photo_origin.x() + photos.width()))
        if (color := frame.pixelColor(x, y)).red() > color.green() * 1.4
        and color.red() > color.blue() * 1.4
    )
    if photo_pixels < 40 or photos.width() <= 0:
        failures.append("a bélyegköteg nem látszik a kártyán")
    assert not failures, "; ".join(failures)
