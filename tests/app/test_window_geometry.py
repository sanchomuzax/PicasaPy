"""#192: a főablak pozíciójának/méretének mentése és visszaállítása.

A mentés QSettings-be történik az ablak zárásakor; induláskor a mentett
geometria csak akkor áll vissza, ha értelmes méretű és látható részben a
mostani virtuális asztalon van (lecsatolt monitor ne hagyja képernyőn
kívül az ablakot).
"""

import pytest

from picasapy.app.window_geometry import (
    restore_window_geometry,
    sanitize_geometry,
    save_window_geometry,
    wire_window_geometry,
)

# tesztasztal: egyetlen 1920×1080-as képernyő a (0,0) sarokban
DESKTOP = (0, 0, 1920, 1080)


@pytest.fixture
def settings(tmp_path):
    from PySide6.QtCore import QSettings

    return QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)


class _FakeWindow:
    """Duck-typed ablak: csak a geometria-függvényekhez kellő felület."""

    def __init__(self, x=0, y=0, width=800, height=600, visibility=None):
        from PySide6.QtGui import QWindow

        self._geo = (x, y, width, height)
        self._visibility = visibility or QWindow.Visibility.Windowed
        self.maximize_calls = 0

    def x(self):
        return self._geo[0]

    def y(self):
        return self._geo[1]

    def width(self):
        return self._geo[2]

    def height(self):
        return self._geo[3]

    def visibility(self):
        return self._visibility

    def setGeometry(self, x, y, width, height):
        self._geo = (x, y, width, height)

    def showMaximized(self):
        self.maximize_calls += 1


class TestSanitizeGeometry:
    def test_valid_geometry_unchanged(self):
        assert sanitize_geometry(60, 40, 900, 700, DESKTOP) == (60, 40, 900, 700)

    def test_too_small_rejected(self):
        assert sanitize_geometry(0, 0, 50, 40, DESKTOP) is None

    def test_empty_desktop_rejected(self):
        assert sanitize_geometry(60, 40, 900, 700, (0, 0, 0, 0)) is None

    def test_offscreen_right_pulled_back(self):
        x, _y, _w, _h = sanitize_geometry(5000, 40, 900, 700, DESKTOP)
        assert x < 1920  # az ablakból fogható rész marad az asztalon

    def test_above_top_clamped_to_top(self):
        # a címsor nem csúszhat a képernyő fölé — különben megfoghatatlan
        _x, y, _w, _h = sanitize_geometry(60, -500, 900, 700, DESKTOP)
        assert y == 0

    def test_oversized_shrunk_to_desktop(self):
        _x, _y, w, h = sanitize_geometry(0, 0, 5000, 4000, DESKTOP)
        assert (w, h) == (1920, 1080)


class TestSaveRestore:
    def test_round_trip(self, qt_app, settings):
        source = _FakeWindow(60, 40, 900, 700)
        save_window_geometry(source, settings)
        target = _FakeWindow()
        assert restore_window_geometry(target, settings, DESKTOP) is True
        assert (target.x(), target.y(), target.width(), target.height()) == (
            60,
            40,
            900,
            700,
        )
        assert target.maximize_calls == 0

    def test_fresh_run_leaves_default(self, qt_app, settings):
        target = _FakeWindow(10, 20, 800, 600)
        assert restore_window_geometry(target, settings, DESKTOP) is False
        assert (target.x(), target.y(), target.width(), target.height()) == (
            10,
            20,
            800,
            600,
        )

    def test_corrupt_values_ignored(self, qt_app, settings):
        settings.setValue("window/x", "nem-szam")
        settings.setValue("window/y", 10)
        settings.setValue("window/width", 900)
        settings.setValue("window/height", 700)
        target = _FakeWindow(10, 20, 800, 600)
        assert restore_window_geometry(target, settings, DESKTOP) is False
        assert (target.x(), target.y(), target.width(), target.height()) == (
            10,
            20,
            800,
            600,
        )

    def test_maximized_saved_and_restored(self, qt_app, settings):
        from PySide6.QtGui import QWindow

        # először normál méret mentve, majd maximalizálva zár az app
        save_window_geometry(_FakeWindow(60, 40, 900, 700), settings)
        maximized = _FakeWindow(
            0, 0, 1920, 1080, visibility=QWindow.Visibility.Maximized
        )
        save_window_geometry(maximized, settings)
        target = _FakeWindow()
        assert restore_window_geometry(target, settings, DESKTOP) is True
        # a normál (nem maximalizált) geometria őrződik meg a visszaálláshoz
        assert (target.x(), target.y(), target.width(), target.height()) == (
            60,
            40,
            900,
            700,
        )
        assert target.maximize_calls == 1

    def test_offscreen_saved_position_clamped(self, qt_app, settings):
        # monitor-lecsatolás: a mentett pozíció kívül esik az asztalon
        save_window_geometry(_FakeWindow(4000, 2000, 900, 700), settings)
        target = _FakeWindow()
        assert restore_window_geometry(target, settings, DESKTOP) is True
        assert target.x() < 1920
        assert target.y() <= 1080 - 48


class TestWireWindowGeometry:
    def test_saves_on_window_closing(self, qt_app, settings):
        # valódi QQuickWindow: a closing jelzésre íródik a geometria
        from PySide6.QtQuick import QQuickWindow

        window = QQuickWindow()
        try:
            window.setGeometry(60, 40, 900, 700)
            wire_window_geometry(window, settings, DESKTOP)
            # a closing jel csak létrehozott (megjelenített) ablaknál jön
            window.show()
            qt_app.processEvents()
            window.close()
            qt_app.processEvents()
            target = _FakeWindow()
            assert restore_window_geometry(target, settings, DESKTOP) is True
            assert (
                target.x(),
                target.y(),
                target.width(),
                target.height(),
            ) == (60, 40, 900, 700)
        finally:
            window.deleteLater()
            qt_app.processEvents()

    def test_restores_saved_geometry_on_wire(self, qt_app, settings):
        save_window_geometry(_FakeWindow(60, 40, 900, 700), settings)
        from PySide6.QtQuick import QQuickWindow

        window = QQuickWindow()
        try:
            wire_window_geometry(window, settings, DESKTOP)
            assert (
                window.x(),
                window.y(),
                window.width(),
                window.height(),
            ) == (60, 40, 900, 700)
        finally:
            window.deleteLater()
            qt_app.processEvents()
