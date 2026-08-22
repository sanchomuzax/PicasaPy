"""#455: a `TrayBar.qml` „Kijelölés megtartása"/„Tálca ürítése" gombjai
és a tálca-előnézet — a `TrayMixin` (tray_controller.py) bekötése.
A `test_qml_tray_print_email.py` betöltési mintáját követi, de valódi
(fake) `controller` context-property-vel, mert a hold/clear gombok a
`tray.ctl`-en (nem az `appWindow`-n) hatnak."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, Signal, Slot


@pytest.fixture
def app_module():
    import picasapy.app.application as module

    return module


class FakeAppWindow(QObject):
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


class FakePhotos(QObject):
    revisionChanged = Signal()

    def __init__(self):
        super().__init__()

    @Property(int, notify=revisionChanged)
    def revision(self):
        return 0

    @Slot(int, result=str)
    def thumbUrlAt(self, row):
        return f"image://thumbs/sel-{row}"

    @Slot(int, result=bool)
    def starAt(self, row):
        return False


class FakeController(QObject):
    """A `TrayMixin` felülete — csak azok a tagok, amiket a `TrayBar.qml`
    ténylegesen olvas (a `test_qml_tray_print_email.py` mintája)."""

    heldChanged = Signal()
    isWorkingChanged = Signal()

    def __init__(self):
        super().__init__()
        self._held_ids: list[int] = []
        self._photos = FakePhotos()
        self.hold_calls: list[list] = []
        self.clear_calls = 0

    @Property(QObject, constant=True)
    def photos(self):
        return self._photos

    @Property(bool, notify=isWorkingChanged)
    def isWorking(self):
        return False

    @Property(str, notify=isWorkingChanged)
    def statusText(self):
        return "0 pictures"

    @Slot(int, result=str)
    def photoInfo(self, row):
        return "photo.jpg"

    @Slot("QVariantList", result=str)
    def selectionInfo(self, rows):
        # #1189: a valódi vezérlő a kijelölés összesítését adja; a duplum
        # csak annyit vállal, hogy LÉTEZIK — különben a TrayBar kötése
        # szkripthibára fut (a #305 őre ezt ki is szúrta).
        return f"{len(rows or [])} pictures"

    @Slot(int, result=str)
    def viewerInfo(self, row):
        return "photo.jpg"

    @Property(int, notify=heldChanged)
    def heldCount(self):
        return len(self._held_ids)

    @Slot(list)
    def holdRows(self, rows):
        self.hold_calls.append(list(rows))
        for row in rows:
            if row not in self._held_ids:
                self._held_ids.append(int(row))
        self.heldChanged.emit()

    @Slot(int, result=bool)
    def isHeldAt(self, row):
        return int(row) in self._held_ids

    @Slot()
    def clearHeld(self):
        self.clear_calls += 1
        if self._held_ids:
            self._held_ids = []
            self.heldChanged.emit()

    @Slot(int, result=str)
    def heldThumbUrlAt(self, index):
        if not 0 <= index < len(self._held_ids):
            return ""
        return f"image://thumbs/held-{self._held_ids[index]}"


def _load_tray(app_module, qt_app, app_window, controller):
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    factory = QQmlComponent(
        engine, str(app_module._APP_DIR / "qml" / "PicasaPy" / "TrayBar.qml")
    )
    item = factory.createWithInitialProperties({"appWindow": app_window})
    assert item is not None, factory.errorString()
    engine._tray_factory = factory
    engine._controller_ref = controller
    return item, engine


def _load_tray_in_window(app_module, qt_app, app_window, controller):
    """Mint `_load_tray`, de VALÓDI `ApplicationWindow`-ba ágyazva — a
    `Dialog`/`Popup` (`trayClearConfirm`) az `Overlay.overlay`-en át csak
    ablak-ősben tud ténylegesen megnyílni/láthatóvá válni."""
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("appWindowRef", app_window)
    from PySide6.QtCore import QUrl

    component = QQmlComponent(engine)
    component.setData(
        b"""
        import QtQuick
        import QtQuick.Controls
        import PicasaPy
        ApplicationWindow {
            visible: true
            width: 400; height: 100
            TrayBar { anchors.fill: parent; appWindow: appWindowRef }
        }
        """,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "test_tray_window.qml")),
    )
    window = component.create()
    assert window is not None, component.errorString()
    engine._window_factory = component
    engine._controller_ref = controller
    return window, engine


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _repeater_item_at(repeater, index):
    """`Repeater.itemAt(index)` közvetlen meghívása (a #320-as
    MEMORY-minta) — a headless `QQmlComponent.create()`-tel létrejött
    delegátumok nem érhetők el `findChild`-dal."""
    from PySide6.QtCore import QMetaObject, Q_ARG, Q_RETURN_ARG

    item = QMetaObject.invokeMethod(
        repeater, "itemAt", Q_RETURN_ARG("QQuickItem*"), Q_ARG(int, index)
    )
    assert item is not None
    return item


class TestHoldButton:
    def test_disabled_without_selection(self, app_module, qt_app):
        controller = FakeController()
        app_window = FakeAppWindow()
        tray, engine = _load_tray(app_module, qt_app, app_window, controller)
        hold_button = _child(tray, "trayHoldButton")
        assert hold_button.property("enabled") is False
        tray.deleteLater()
        engine.deleteLater()

    def test_clicking_holds_current_selection(self, app_module, qt_app):
        controller = FakeController()
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [2, 5]
        tray, engine = _load_tray(app_module, qt_app, app_window, controller)
        hold_button = _child(tray, "trayHoldButton")
        assert hold_button.property("enabled") is True
        hold_button.clicked.emit()
        qt_app.processEvents()
        assert controller.hold_calls == [[2, 5]]
        assert controller.heldCount == 2
        tray.deleteLater()
        engine.deleteLater()


class TestClearButton:
    def test_disabled_when_tray_empty(self, app_module, qt_app):
        controller = FakeController()
        app_window = FakeAppWindow()
        tray, engine = _load_tray(app_module, qt_app, app_window, controller)
        clear_button = _child(tray, "trayClearButton")
        assert clear_button.property("enabled") is False
        tray.deleteLater()
        engine.deleteLater()

    def test_enabled_after_hold_and_confirms_before_clearing(
        self, app_module, qt_app
    ):
        controller = FakeController()
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [1]
        window, engine = _load_tray_in_window(
            app_module, qt_app, app_window, controller)
        _child(window, "trayHoldButton").clicked.emit()
        qt_app.processEvents()

        clear_button = _child(window, "trayClearButton")
        assert clear_button.property("enabled") is True
        clear_button.clicked.emit()
        qt_app.processEvents()
        # a kattintás csak a dialógust nyitja meg, még NEM ürít
        assert controller.clear_calls == 0
        dialog = _child(window, "trayClearConfirmDialog")
        assert dialog.property("visible") is True

        yes_button = _child(window, "trayClearConfirmYesButton")
        yes_button.clicked.emit()
        qt_app.processEvents()
        assert controller.clear_calls == 1
        assert controller.heldCount == 0
        window.deleteLater()
        engine.deleteLater()

    def test_dont_clear_leaves_tray_untouched(self, app_module, qt_app):
        controller = FakeController()
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [1]
        window, engine = _load_tray_in_window(
            app_module, qt_app, app_window, controller)
        _child(window, "trayHoldButton").clicked.emit()
        qt_app.processEvents()
        _child(window, "trayClearButton").clicked.emit()
        qt_app.processEvents()

        no_button = _child(window, "trayClearConfirmNoButton")
        no_button.clicked.emit()
        qt_app.processEvents()
        assert controller.clear_calls == 0
        assert controller.heldCount == 1
        window.deleteLater()
        engine.deleteLater()


class TestTrayPreviewPrefersHeldItems:
    """A #320-as MEMORY-minta szerint (`test_folder_context_menu_320.py`):
    headless `QQmlComponent.create()`-tel a Repeater-delegátumok NEM
    kereshetők `findChild`-dal — a `count` és az `itemAt()` a helyes út."""

    def test_preview_uses_selection_before_hold(self, app_module, qt_app):
        controller = FakeController()
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [3]
        tray, engine = _load_tray(app_module, qt_app, app_window, controller)
        repeater = _child(tray, "trayPreviewRepeater")
        assert repeater.property("count") == 1
        item = _repeater_item_at(repeater, 0)
        assert item.property("source").toString() == "image://thumbs/sel-3"
        tray.deleteLater()
        engine.deleteLater()

    def test_preview_shows_held_thumb_url_once_held(self, app_module, qt_app):
        controller = FakeController()
        app_window = FakeAppWindow()
        app_window.selectedIndexes = [3]
        tray, engine = _load_tray(app_module, qt_app, app_window, controller)
        _child(tray, "trayHoldButton").clicked.emit()
        qt_app.processEvents()

        repeater = _child(tray, "trayPreviewRepeater")
        assert repeater.property("count") == 1
        item = _repeater_item_at(repeater, 0)
        assert "held-" in item.property("source").toString()
        tray.deleteLater()
        engine.deleteLater()
