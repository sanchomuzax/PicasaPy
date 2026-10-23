"""A teljes képernyős Időrend belépési pontjai és vezérlőadatai (#5377)."""


import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt
from PySide6.QtTest import QTest
from tests.support.varakozas import var_feltetelre


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _invoke(qt_app, obj, name, *args):
    QMetaObject.invokeMethod(
        obj, name, Qt.ConnectionType.DirectConnection,
        *[Q_ARG("QVariant", a) for a in args],
    )
    qt_app.processEvents()


def _wait_for(qt_app, predicate, timeout_ms=10000):
    return var_feltetelre(qt_app, predicate, timeout_ms / 1000)


class TestTimelineEntryPoints:
    def test_internal_toggle_opens_and_closes_timeline(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        grid = _child(window, "photoGrid")
        assert grid.property("visible") is True
        _invoke(qt_app, window, "toggleTimeline")
        assert window.property("timelineOpen") is True
        view = _child(window, "timelineView")
        assert view.property("visible") is True
        assert grid.property("visible") is False
        _invoke(qt_app, window, "toggleTimeline")
        assert window.property("timelineOpen") is False
        assert view.property("visible") is False

    @pytest.mark.parametrize("height", [795, 800, 805])
    def test_real_ctrl5_keypress_opens_timeline_without_selection(
        self, qml_app, qt_app, height
    ):
        """A Ctrl+5 kijelölés nélkül is elindítja a teljes képernyős módot."""
        window, _controller, _lib, _engine = qml_app
        window.resize(window.width(), height)
        window.requestActivate()
        assert _wait_for(qt_app, window.isActive), "a főablak nem lett aktív"

        QTest.keyClick(
            window,
            Qt.Key.Key_5,
            Qt.KeyboardModifier.ControlModifier,
        )
        assert _wait_for(qt_app, lambda: window.property("timelineOpen") is True)
        view = _child(window, "timelineView")
        assert _wait_for(qt_app, view.isVisible)

    def test_close_button_closes_timeline(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _invoke(qt_app, window, "toggleTimeline")
        close_button = _child(window, "timelineCloseButton")
        QMetaObject.invokeMethod(
            close_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert window.property("timelineOpen") is False


class TestTimelineCollections:
    def test_reload_groups_the_two_fixture_photos(self, qml_app, qt_app):
        # A qml_app két fotója egy mappakártyán jelenik meg, használható
        # bélyegkép-URL-ekkel.
        window, _controller, _lib, engine = qml_app
        _invoke(qt_app, window, "toggleTimeline")
        timeline_controller = engine.rootContext().contextProperty(
            "timelineController"
        )
        collections = timeline_controller.collections
        assert len(collections) == 1
        assert collections[0]["count"] == 2
        assert len(collections[0]["photos"]) == 2
        for photo in collections[0]["photos"]:
            assert photo["thumbUrl"].startswith("image://thumbs/")
            assert photo["folderPath"]
            assert isinstance(photo["id"], int)

    def test_empty_library_shows_no_collections(self, qml_app, tmp_path):
        _window, _controller, _lib, engine = qml_app
        empty_db = tmp_path / "empty_index.db"
        from picasapy.index import open_index

        with open_index(empty_db):
            pass
        timeline_controller = engine.rootContext().contextProperty(
            "timelineController"
        )
        timeline_controller._db_path = empty_db
        timeline_controller.reload()
        assert timeline_controller.collections == []

    def test_reload_groups_photos_into_chronological_folder_cards(
        self, qml_app, qt_app
    ):
        window, _controller, _lib, engine = qml_app
        _invoke(qt_app, window, "toggleTimeline")
        timeline_controller = engine.rootContext().contextProperty(
            "timelineController"
        )
        collections = timeline_controller.collections
        assert len(collections) == 1
        assert collections[0]["count"] == 2
        assert len(collections[0]["photos"]) == 2
        assert collections[0]["folderPath"]
        assert collections[0]["sliderPosition"] == 0.0
