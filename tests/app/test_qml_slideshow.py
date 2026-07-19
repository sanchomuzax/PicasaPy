"""QML-funkcionális tesztek: diavetítés (#8).

A léptetés-logika (videó-kihagyás, körbefordulás), az időzítő, a szünet,
a kilépés utáni kijelölés-követés és a vetítés közbeni forgatás/csillag
bekötése — a közös qml_app fixture-ön (Main.qml betöltve offscreen).
"""

from PySide6.QtCore import Q_ARG, QEventLoop, QMetaObject, QObject, Qt, QTimer


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


def _start(window, qt_app, index=-1):
    _invoke(qt_app, window, "startSlideshow", index)
    return _child(window, "slideshowView")


def _wait_ms(qt_app, ms):
    loop = QEventLoop()
    QTimer.singleShot(ms, loop.quit)
    loop.exec()
    qt_app.processEvents()


class TestSlideshowBasics:
    def test_start_shows_and_timer_runs(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndex", 0)
        show = _start(window, qt_app)
        assert show.property("visible") is True
        assert show.property("playing") is True
        assert show.property("currentIndex") == 0
        assert _child(window, "slideshowTimer").property("running") is True
        _invoke(qt_app, show, "stop")
        assert show.property("visible") is False
        assert _child(window, "slideshowTimer").property("running") is False

    def test_advance_wraps_around(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 0)
        _invoke(qt_app, show, "advance")
        assert show.property("currentIndex") == 1
        _invoke(qt_app, show, "advance")   # 2 fotó: körbefordul
        assert show.property("currentIndex") == 0
        _invoke(qt_app, show, "goBack")
        assert show.property("currentIndex") == 1
        _invoke(qt_app, show, "stop")

    def test_exit_syncs_grid_selection(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndex", 0)
        window.setProperty("selectedIndexes", [0])
        show = _start(window, qt_app)
        _invoke(qt_app, show, "advance")
        _invoke(qt_app, show, "stop")
        assert window.property("selectedIndex") == 1

    def test_pause_stops_timer(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 0)
        _invoke(qt_app, show, "togglePause")
        assert show.property("playing") is False
        assert _child(window, "slideshowTimer").property("running") is False
        _invoke(qt_app, show, "togglePause")
        assert _child(window, "slideshowTimer").property("running") is True
        _invoke(qt_app, show, "stop")

    def test_timer_advances_slides(self, qml_app, qt_app):
        # DoD: léptetés-időzítő — rövid intervallummal valóban lép
        window, _controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 0)
        show.setProperty("intervalMs", 50)
        steps = []
        show.currentIndexChanged.connect(
            lambda: steps.append(show.property("currentIndex"))
        )
        _wait_ms(qt_app, 400)
        assert len(steps) >= 1, "az időzítőnek legalább egyet lépnie kellett"
        _invoke(qt_app, show, "stop")


class TestSlideshowVideoSkip:
    def test_videos_are_skipped(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        (lib / "c.mp4").write_bytes(b"\x00" * 64)
        from picasapy.index import open_index, sync_tree

        with open_index(controller._db_path) as conn:
            sync_tree(conn, lib)
        controller._reload()
        qt_app.processEvents()
        assert controller.photos.isVideoAt(2) is True
        show = _start(window, qt_app, 1)
        _invoke(qt_app, show, "advance")   # a 2-es (videó) kimarad
        assert show.property("currentIndex") == 0
        _invoke(qt_app, show, "stop")

    def test_start_on_video_clamps_to_photo(self, qml_app, qt_app):
        window, controller, lib, _engine = qml_app
        (lib / "c.mp4").write_bytes(b"\x00" * 64)
        from picasapy.index import open_index, sync_tree

        with open_index(controller._db_path) as conn:
            sync_tree(conn, lib)
        controller._reload()
        qt_app.processEvents()
        show = _start(window, qt_app, 2)   # videó-soron indítva
        assert show.property("visible") is True
        assert show.property("currentIndex") == 0   # az első fotóra ugrik
        _invoke(qt_app, show, "stop")


class TestSlideshowActions:
    def test_rotate_during_show_writes_ini(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 0)
        _invoke(qt_app, show, "rotateCurrent", 1)
        assert controller.photos.rotateAt(0) == 1
        _invoke(qt_app, show, "rotateCurrent", -1)
        assert controller.photos.rotateAt(0) == 0
        _invoke(qt_app, show, "stop")

    def test_star_during_show(self, qml_app, qt_app):
        window, controller, _lib, _engine = qml_app
        show = _start(window, qt_app, 0)
        _invoke(qt_app, show, "starCurrent")
        assert controller.photos.starAt(0) is True
        _invoke(qt_app, show, "starCurrent")
        assert controller.photos.starAt(0) is False
        _invoke(qt_app, show, "stop")


class TestSlideshowEntryPoints:
    def test_view_menu_item_starts_show(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        window.setProperty("selectedIndex", 0)
        item = _child(window, "menuViewSlideshow")
        assert item.property("enabled") is True
        QMetaObject.invokeMethod(
            item, "triggered", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        show = _child(window, "slideshowView")
        assert show.property("visible") is True
        _invoke(qt_app, show, "stop")

    def test_viewer_play_button_enabled(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        button = _child(window, "viewerPlayButton")
        assert button.property("enabled") is True
