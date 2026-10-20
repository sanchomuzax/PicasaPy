"""Időrend kártyaadatok és ablakállapot (#5377)."""

from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest


def _toggle(qt_app, window):
    assert QMetaObject.invokeMethod(
        window, "toggleTimeline", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def test_reload_builds_a_collection_card_with_registered_thumbnails(qml_app, qt_app):
    window, _controller, _lib, engine = qml_app
    _toggle(qt_app, window)
    timeline_controller = engine.rootContext().contextProperty("timelineController")

    collections = timeline_controller.collections
    assert len(collections) == 1
    assert collections[0]["count"] == 2
    assert collections[0]["name"] == "kepek"
    assert collections[0]["date"]
    for photo in collections[0]["photos"]:
        assert photo["thumbUrl"].startswith("image://thumbs/")
        assert photo["folderPath"]
        assert isinstance(photo["id"], int)


def test_empty_library_has_no_collection_cards(qml_app, qt_app, tmp_path):
    _window, _controller, _lib, engine = qml_app
    timeline_controller = engine.rootContext().contextProperty("timelineController")
    empty_db = tmp_path / "empty_index.db"
    from picasapy.index import open_index

    with open_index(empty_db):
        pass
    timeline_controller._db_path = empty_db
    timeline_controller.reload()

    assert timeline_controller.collections == []
    assert timeline_controller.dateRangeStartLabel == ""
    assert timeline_controller.dateRangeEndLabel == ""
    assert timeline_controller.slideshowPhotos.rowCount() == 0


def test_toggle_opens_fullscreen_without_selection_and_escape_returns(
    qml_app, qt_app
):
    window, _controller, _lib, _engine = qml_app
    initial_visibility = window.visibility()
    window.setProperty("selectedIndex", -1)
    window.setProperty("selectedIndexes", [])
    _toggle(qt_app, window)
    assert window.property("timelineOpen") is True
    assert window.visibility() == QQuickWindow.Visibility.FullScreen

    QTest.keyClick(window, Qt.Key.Key_Escape)
    qt_app.processEvents()
    assert window.property("timelineOpen") is False
    assert window.visibility() == initial_visibility
