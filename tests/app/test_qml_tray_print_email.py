"""#32 (RÉSZLEGES kör): a `TrayBar.qml` E-Mail/Print gombjai — a Main.qml-
bekötés (dialógus megnyitása) NEM ebben a jegyben készül el (ld.
`print_controller.py`/`email_controller.py` docstringje), de a gombok
engedélyezés-logikája és a jelzés-kibocsátás önállóan, Main.qml nélkül
tesztelhető — a `test_qml_webexport_menu.py` mintája."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, Signal, Slot


@pytest.fixture
def app_module():
    import picasapy.app.application as module

    return module


class FakeAppWindow(QObject):
    """A TrayBar `appWindow` (required var) felülete — csak azok a
    property-k/függvények, amiket a komponens ténylegesen olvas."""

    selectedIndexesChanged = Signal()
    selectedIndexChanged = Signal()
    viewerOpenChanged = Signal()
    thumbSizeChanged = Signal()

    def __init__(self):
        super().__init__()
        self._selected_indexes = []
        self._selected_index = -1
        self._viewer_open = False
        self._thumb_size = 100

    def _get_selected_indexes(self):
        return self._selected_indexes

    def _set_selected_indexes(self, value):
        self._selected_indexes = list(value)
        self.selectedIndexesChanged.emit()

    selectedIndexes = Property(
        list, _get_selected_indexes, _set_selected_indexes,
        notify=selectedIndexesChanged,
    )

    def _get_selected_index(self):
        return self._selected_index

    def _set_selected_index(self, value):
        self._selected_index = value
        self.selectedIndexChanged.emit()

    selectedIndex = Property(
        int, _get_selected_index, _set_selected_index, notify=selectedIndexChanged
    )

    def _get_viewer_open(self):
        return self._viewer_open

    def _set_viewer_open(self, value):
        self._viewer_open = bool(value)
        self.viewerOpenChanged.emit()

    viewerOpen = Property(
        bool, _get_viewer_open, _set_viewer_open, notify=viewerOpenChanged
    )

    def _get_thumb_size(self):
        return self._thumb_size

    def _set_thumb_size(self, value):
        self._thumb_size = value
        self.thumbSizeChanged.emit()

    thumbSize = Property(
        int, _get_thumb_size, _set_thumb_size, notify=thumbSizeChanged
    )

    @Slot(result=bool)
    def rotateTargetsAllVideo(self):
        return False


def _load_tray(app_module, qt_app, app_window):
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", None)
    factory = QQmlComponent(
        engine, str(app_module._APP_DIR / "qml" / "PicasaPy" / "TrayBar.qml")
    )
    item = factory.createWithInitialProperties({"appWindow": app_window})
    assert item is not None, factory.errorString()
    engine._tray_factory = factory
    return item, engine


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestEmailAndPrintButtonsEnabledState:
    def test_disabled_with_no_selection_and_grid_view(self, app_module, qt_app):
        app_window = FakeAppWindow()
        tray, engine = _load_tray(app_module, qt_app, app_window)
        email_button = _child(tray, "trayEmailButton")
        print_button = _child(tray, "trayPrintButton")
        assert email_button.property("enabled") is False
        assert print_button.property("enabled") is False
        tray.deleteLater()
        engine.deleteLater()

    def test_enabled_when_grid_selection_present(self, app_module, qt_app):
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [0, 1]
        tray, engine = _load_tray(app_module, qt_app, app_window)
        email_button = _child(tray, "trayEmailButton")
        print_button = _child(tray, "trayPrintButton")
        assert email_button.property("enabled") is True
        assert print_button.property("enabled") is True
        tray.deleteLater()
        engine.deleteLater()

    def test_enabled_in_viewer_even_without_grid_selection(self, app_module, qt_app):
        app_window = FakeAppWindow()
        app_window.viewerOpen = True
        tray, engine = _load_tray(app_module, qt_app, app_window)
        tray.setProperty("viewerIndex", 0)
        email_button = _child(tray, "trayEmailButton")
        print_button = _child(tray, "trayPrintButton")
        assert email_button.property("enabled") is True
        assert print_button.property("enabled") is True
        tray.deleteLater()
        engine.deleteLater()

    def test_disabled_in_viewer_with_no_current_row(self, app_module, qt_app):
        app_window = FakeAppWindow()
        app_window.viewerOpen = True
        tray, engine = _load_tray(app_module, qt_app, app_window)
        tray.setProperty("viewerIndex", -1)
        email_button = _child(tray, "trayEmailButton")
        print_button = _child(tray, "trayPrintButton")
        assert email_button.property("enabled") is False
        assert print_button.property("enabled") is False
        tray.deleteLater()
        engine.deleteLater()


class TestEmailAndPrintButtonsEmitSignals:
    def test_clicking_email_emits_email_requested(self, app_module, qt_app):
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [0]
        tray, engine = _load_tray(app_module, qt_app, app_window)
        seen = []
        tray.emailRequested.connect(lambda: seen.append(True))
        email_button = _child(tray, "trayEmailButton")
        email_button.clicked.emit()
        qt_app.processEvents()
        assert seen == [True]
        tray.deleteLater()
        engine.deleteLater()

    def test_clicking_print_emits_print_requested(self, app_module, qt_app):
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [0]
        tray, engine = _load_tray(app_module, qt_app, app_window)
        seen = []
        tray.printRequested.connect(lambda: seen.append(True))
        print_button = _child(tray, "trayPrintButton")
        print_button.clicked.emit()
        qt_app.processEvents()
        assert seen == [True]
        tray.deleteLater()
        engine.deleteLater()
