"""Az Időrend jelenlegi felületi kivételei és belső QML-próbái.

A teljes képernyős, animált Időrend külön feladat (#4443). Addig a menüpont
és a Ctrl+5 szándékosan inaktív (#1903); a közvetlen `toggleTimeline()`-
hívások alább csak a meglévő placeholder belső állapotát fedik le, nem
felhasználói belépési utak.
"""

import time

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, Qt
from PySide6.QtTest import QTest


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


def _wait_for(qt_app, predicate, timeout_ms=3000):
    deadline = time.monotonic() + timeout_ms / 1000
    while time.monotonic() < deadline:
        if predicate():
            return True
        QTest.qWait(10)
    return predicate()


class TestTimelineEntryPoints:
    def test_internal_placeholder_toggle_opens_timeline(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _invoke(qt_app, window, "toggleTimeline")
        assert window.property("timelineOpen") is True
        view = _child(window, "timelineView")
        assert view.property("visible") is True

    def test_internal_placeholder_toggle_closes_timeline(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _invoke(qt_app, window, "toggleTimeline")
        _invoke(qt_app, window, "toggleTimeline")
        assert window.property("timelineOpen") is False
        view = _child(window, "timelineView")
        assert view.property("visible") is False

    def test_internal_placeholder_toggle_hides_grid(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        grid = _child(window, "photoGrid")
        assert grid.property("visible") is True
        _invoke(qt_app, window, "toggleTimeline")
        assert grid.property("visible") is False

    @pytest.mark.parametrize("height", [795, 800, 805])
    def test_real_ctrl5_keypress_keeps_timeline_inactive(
        self, qml_app, qt_app, height
    ):
        """A gyorsbillentyű nem kerülheti meg az inaktív menüpontot (#1903)."""
        window, _controller, _lib, _engine = qml_app
        window.resize(window.width(), height)
        window.requestActivate()
        assert _wait_for(qt_app, window.isActive), "a főablak nem lett aktív"

        QTest.keyClick(
            window,
            Qt.Key.Key_5,
            Qt.KeyboardModifier.ControlModifier,
        )
        qt_app.processEvents()

        assert window.property("timelineOpen") is False
        view = _child(window, "timelineView")
        assert view.property("visible") is False

    @pytest.mark.parametrize("height", [795, 800, 805])
    def test_menu_item_is_disabled_and_does_NOT_open(
        self, qml_app, qt_app, height
    ):
        """#1903: a menütétel INAKTÍV — a nézet nem nyílik meg róla.

        ⚠️ Ez az állítás MEGFORDULT. Korábban azt mértük, hogy a tétel
        megnyitja az Időrendet; a tulajdonos élesben jelentette (két
        képernyőképpel), hogy amit megnyit, az NEM az eredeti funkció: a
        Picasa Időrendje teljes képernyős, animált bemutató a diavetítő
        motorján (`oneup/timeline` + `BigSlideshow2`, `0x008037e0`), saját
        rátétes vezérlősávval — a miénk lapos rács volt.

        A tétel HELYE megmarad (az eredetiben létezik), de amíg a valódi
        nézet nincs megépítve, nem nyithat meg mást."""
        window, _controller, _lib, _engine = qml_app
        item = _child(window, "menuViewTimeline")
        assert item.property("enabled") is False
        window.resize(window.width(), height)
        view_menu = _child(window, "menuView")
        assert QMetaObject.invokeMethod(
            view_menu, "open", Qt.ConnectionType.DirectConnection
        )
        assert _wait_for(
            qt_app, lambda: item.isVisible() and item.width() > 0
        ), "a Nézet menü Időrend eleme nem jelent meg"
        popup_window = item.window()
        center = item.mapToScene(item.boundingRect().center())
        QTest.mouseClick(
            popup_window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        qt_app.processEvents()
        assert window.property("timelineOpen") is not True

    def test_close_button_closes_timeline(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _invoke(qt_app, window, "toggleTimeline")
        close_button = _child(window, "timelineCloseButton")
        QMetaObject.invokeMethod(
            close_button, "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert window.property("timelineOpen") is False


class TestTimelinePeriods:
    def test_reload_groups_the_two_fixture_photos(self, qml_app, qt_app):
        # a qml_app fixture két fotót szinkronizál (a.jpg, b.jpg) — a
        # reload (a placeholder belső váltófüggvényében fut) mindkettőt egyetlen korszakba
        # csoportosítja (mtime-fallback: egy futáson belül szinte mindig
        # ugyanaz a hónap), és a bélyegkép-URL-ek nem üresek
        window, _controller, _lib, engine = qml_app
        _invoke(qt_app, window, "toggleTimeline")
        timeline_controller = engine.rootContext().contextProperty(
            "timelineController"
        )
        periods = timeline_controller.periods
        assert len(periods) >= 1
        total_photos = sum(p["count"] for p in periods)
        assert total_photos == 2
        for period in periods:
            for photo in period["photos"]:
                assert photo["thumbUrl"].startswith("image://thumbs/")
                assert photo["folderPath"]
                assert isinstance(photo["id"], int)

    def test_empty_library_shows_no_periods(self, qml_app, qt_app, tmp_path):
        window, controller, _lib, engine = qml_app
        # üres könyvtár — a bekötés ne hasaljon el peremesetnél sem
        empty_lib = tmp_path / "ures"
        empty_lib.mkdir()
        empty_db = tmp_path / "empty_index.db"
        from picasapy.index import open_index

        with open_index(empty_db):
            pass
        timeline_controller = engine.rootContext().contextProperty(
            "timelineController"
        )
        timeline_controller._db_path = empty_db
        timeline_controller.reload()
        assert timeline_controller.periods == []


class TestTimelinePhotoChosen:
    def test_click_thumbnail_selects_folder_and_opens_viewer(
        self, qml_app, qt_app
    ):
        window, controller, lib, engine = qml_app
        _invoke(qt_app, window, "toggleTimeline")
        timeline_controller = engine.rootContext().contextProperty(
            "timelineController"
        )
        photo = timeline_controller.periods[0]["photos"][0]
        view = _child(window, "timelineView")
        _invoke(qt_app, view, "requestOpen", photo["id"], photo["folderPath"])
        assert window.property("timelineOpen") is False
        assert window.property("viewerOpen") is True
        assert controller.currentFolder == photo["folderPath"]
        row = controller.photos.rowOfId(photo["id"])
        assert row >= 0
        photo_viewer = _child(window, "photoViewer")
        assert photo_viewer.property("currentIndex") == row

    def test_click_thumbnail_unknown_id_does_not_crash(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        _invoke(qt_app, window, "toggleTimeline")
        view = _child(window, "timelineView")
        _invoke(qt_app, view, "requestOpen", -1, "")
        # nincs ilyen id — a néző nem nyílik meg, de nem is omlik össze
        assert window.property("timelineOpen") is False
