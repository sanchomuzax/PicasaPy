"""#368/#3214: MoveDatabaseDialog.qml — önállóan betöltve, fake kontrollerrel
(a `test_qml_import_drop_area.py` mintája). A Main.qml-be illesztés (a
felület-belépési pont, pl. eszköztár-gomb/menü) az integrátoré.

⚠️ #3214 óta ez a párbeszéd **nem költöztet**: a gomb SZÁNDÉKOT rögzít, a
másolás a következő induláskor fut (`StartupRelocateWindow.qml`). A
haladás-, megszakítás- és „kész, indítsd újra"-próbák ezért eltűntek —
nincs mit mérniük. Ami maradt: a cél átadása, az előjegyzés visszajelzése,
a visszavonás és a hibaág."""

from __future__ import annotations

import pytest
from PySide6.QtCore import (
    Property,
    QMetaObject,
    QObject,
    Qt,
    Signal,
    Slot,
)


class FakeRelocateController(QObject):
    relocateFailed = Signal(str)
    relocateScheduled = Signal(str)

    def __init__(self, current_location="/home/user/.local/share/picasapy"):
        super().__init__()
        self._current_location = current_location
        self.start_calls = []
        self.cancel_calls = 0

    def _get_current_location(self):
        return self._current_location

    currentLocation = Property(str, _get_current_location)

    @Slot(str)
    def startRelocate(self, new_location) -> None:
        self.start_calls.append(new_location)

    @Slot()
    def cancelScheduledRelocate(self) -> None:
        self.cancel_calls += 1


@pytest.fixture
def fake():
    return FakeRelocateController()


@pytest.fixture
def dialog(qt_app, fake):
    """A MoveDatabaseDialog.qml önállóan betöltve, fake kontrollerrel."""
    import picasapy.app.application as app_module
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("relocateController", fake)
    factory = QQmlComponent(
        engine,
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "MoveDatabaseDialog.qml"),
    )
    item = factory.create()
    assert item is not None, factory.errorString()
    yield item, fake, qt_app
    item.deleteLater()
    qt_app.processEvents()


def _child(window, name):
    obj = window.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _click(button):
    QMetaObject.invokeMethod(button, "clicked", Qt.ConnectionType.DirectConnection)


class TestDialogWindow:
    def test_is_a_standalone_resizable_window(self, dialog):
        window, _fake, _qt_app = dialog
        assert window.property("minimumWidth") is not None
        assert window.property("minimumWidth") >= 400
        assert window.property("minimumHeight") is not None

    def test_starts_hidden(self, dialog):
        window, _fake, _qt_app = dialog
        assert window.property("visible") is False

    def test_open_makes_it_visible_and_resets_state(self, dialog):
        window, _fake, qt_app = dialog
        window.setProperty("lastError", "korábbi hiba")
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert window.property("visible") is True
        assert window.property("lastError") == ""

    def test_close_button_hides_the_window(self, dialog):
        window, _fake, qt_app = dialog
        window.setProperty("visible", True)
        qt_app.processEvents()
        _click(_child(window, "moveDatabaseCloseButton"))
        qt_app.processEvents()
        assert window.property("visible") is False


class TestCurrentAndNewLocation:
    def test_shows_current_location_from_controller(self, dialog):
        window, fake, _qt_app = dialog
        text = _child(window, "moveDatabaseCurrentPathText")
        assert text.property("text") == fake.currentLocation

    def test_default_button_fills_new_location_with_current(self, dialog, qt_app):
        window, _fake, _qt_app2 = dialog
        _click(_child(window, "moveDatabaseDefaultButton"))
        qt_app.processEvents()
        assert window.property("newLocation") == window.property("currentLocation")

    def test_move_button_disabled_without_new_location(self, dialog):
        window, _fake, _qt_app = dialog
        move_button = _child(window, "moveDatabaseMoveButton")
        assert move_button.property("enabled") is False

    def test_move_button_enabled_once_new_location_chosen(self, dialog, qt_app):
        window, _fake, _qt_app2 = dialog
        window.setProperty("newLocation", "/mnt/nas/picasapy-adatok")
        qt_app.processEvents()
        move_button = _child(window, "moveDatabaseMoveButton")
        assert move_button.property("enabled") is True


class TestStartMove:
    def test_move_button_forwards_new_location_to_controller(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        window.setProperty("newLocation", "/mnt/nas/picasapy-adatok")
        qt_app.processEvents()
        _click(_child(window, "moveDatabaseMoveButton"))
        qt_app.processEvents()
        assert fake.start_calls == ["/mnt/nas/picasapy-adatok"]

    def test_az_elojegyzes_visszajelzese_megjelenik(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.relocateScheduled.emit("/mnt/nas/picasapy-adatok")
        qt_app.processEvents()

        eredmeny = _child(window, "moveDatabaseResultText")
        assert eredmeny.property("visible") is True
        assert window.property("scheduledLocation") == "/mnt/nas/picasapy-adatok"

    def test_az_elojegyzes_utan_a_gomb_nem_nyomhato_ujra(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        window.setProperty("newLocation", "/mnt/nas/picasapy-adatok")
        fake.relocateScheduled.emit("/mnt/nas/picasapy-adatok")
        qt_app.processEvents()

        assert _child(window, "moveDatabaseMoveButton").property("enabled") is False

    def test_a_visszavonas_szol_a_vezerlonek(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.relocateScheduled.emit("/mnt/nas/picasapy-adatok")
        qt_app.processEvents()

        _click(_child(window, "moveDatabaseUndoScheduleButton"))
        qt_app.processEvents()

        assert fake.cancel_calls == 1
        assert window.property("scheduledLocation") == ""

    def test_failed_signal_shows_error(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.relocateFailed.emit("Nincs elég szabad hely.")
        qt_app.processEvents()

        error_text = _child(window, "moveDatabaseErrorText")
        assert error_text.property("visible") is True
        assert "Nincs elég szabad hely" in str(error_text.property("text"))


class TestRelocateControllerQtProperty:
    """#377: a `currentLocation` Qt-Property kell legyen — sima Python-
    property-ként a QML `undefined`-et olvasott, és induláskor
    "Unable to assign [undefined] to QString" figyelmeztetés jött."""

    def test_current_location_qt_property(self, tmp_path, qt_app):
        from picasapy.app.relocate_controller import RelocateController

        ctl = RelocateController(
            tmp_path / "index.db", tmp_path / "thumbs", tmp_path / "cfg"
        )
        mo = ctl.metaObject()
        nevek = {str(mo.property(i).name()) for i in range(mo.propertyCount())}
        assert "currentLocation" in nevek
        # a QMetaObject-úton olvasott érték soha nem undefined/None
        assert isinstance(ctl.property("currentLocation"), str)
        assert ctl.property("currentLocation")
