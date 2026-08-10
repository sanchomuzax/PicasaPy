"""QML-funkcionális teszt — #459: `EditorPanel.qml` a `editController.
editSaveReadOnly`/`editSaveFailed` jelzésekre az eredeti Picasa szövege
szerinti `ConfirmDialog`-ot nyitja meg. Az „Igen" (mappa-másolás) ág NEM
készült el (a jegy szerint külön munka) — a gomb ezért LÁTHATÓAN tiltott
(`yesEnabled: false`), nem néma no-op.

Az `EditorPanel`-t önállóan tölti be a `test_editor_411.py` mintáját
követve — egy `_FakeEditController` szimulálja a jelzéseket."""

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtQml import QQmlComponent, QQmlEngine

import pytest

_KEEPALIVE = []


class _FakeEditController(QObject):
    editSaveReadOnly = Signal()
    editSaveFailed = Signal(str)


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, qml_source):
    component = QQmlComponent(engine)
    component.setData(qml_source.encode("utf-8"), QUrl())
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None, "a komponens betöltése sikertelen"
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(obj)
    return obj


def _make_panel(engine, fake_controller):
    engine.rootContext().setContextProperty("editController", fake_controller)
    _KEEPALIVE.append(fake_controller)
    return _load(
        engine,
        "import QtQuick\nimport PicasaPy 1.0\n"
        'EditorPanel { objectName: "panel"; activeTab: 0 }\n',
    )


class TestReadOnlyDialog:
    def test_readonly_signal_opens_dialog_with_original_text(self, qml_engine, qt_app):
        fake = _FakeEditController()
        panel = _make_panel(qml_engine, fake)
        qt_app.processEvents()
        dialog = panel.findChild(QObject, "editReadOnlyDialog")
        assert dialog is not None
        assert dialog.property("message") == ""
        fake.editSaveReadOnly.emit()
        qt_app.processEvents()
        message = dialog.property("message")
        assert "read only" in message
        assert "copy the file's folder" in message

    def test_readonly_dialog_yes_button_is_disabled(self, qml_engine, qt_app):
        """Nem tehetünk úgy, mintha a mappa-másolás működne — a gomb
        LÁTHATÓAN tiltott, nem néma no-op (CLAUDE.md #459, (j) szabály)."""
        fake = _FakeEditController()
        panel = _make_panel(qml_engine, fake)
        qt_app.processEvents()
        fake.editSaveReadOnly.emit()
        qt_app.processEvents()
        yes_button = panel.findChild(QObject, "editReadOnlyYesButton")
        assert yes_button is not None
        assert yes_button.property("enabled") is False

    def test_save_failed_signal_opens_error_dialog_with_details(self, qml_engine, qt_app):
        fake = _FakeEditController()
        panel = _make_panel(qml_engine, fake)
        qt_app.processEvents()
        dialog = panel.findChild(QObject, "editSaveErrorDialog")
        assert dialog is not None
        fake.editSaveFailed.emit("teszt: lemez megtelt")
        qt_app.processEvents()
        message = dialog.property("message")
        assert "disk error" in message
        assert "teszt: lemez megtelt" in message
