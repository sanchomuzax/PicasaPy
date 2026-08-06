"""#351: `WebExportDialog.qml` — önállóan betöltve, fake kontrollerrel (a
`test_qml_move_database.py` mintája). A Main.qml-be illesztés (menü-
bekötés, `webExportController` context property) az integrátoré."""

from __future__ import annotations

import pytest
from PySide6.QtCore import (
    QMetaObject,
    QObject,
    Qt,
    Signal,
    Slot,
)


class FakeWebExportController(QObject):
    webExportStarted = Signal()
    webExportProgress = Signal(int, int)
    webExportFinished = Signal(str, int)
    webExportFailed = Signal(str)

    def __init__(self):
        super().__init__()
        self.generate_calls = []
        self._templates = [
            {"id": "feher", "name": "Fehér", "description": "Fehér hátterű sablon"},
            {"id": "masik", "name": "Másik", "description": ""},
        ]

    @Slot(result=list)
    def listWebExportTemplates(self):
        return self._templates

    @Slot(str, str, str, int, int, bool, bool)
    def generateWebExport(
        self, target_dir, template_id, album_name, thumb_max, image_max,
        shadow_thumbs, shadow_images,
    ):
        self.generate_calls.append(
            (target_dir, template_id, album_name, thumb_max, image_max,
             shadow_thumbs, shadow_images)
        )


@pytest.fixture
def fake():
    return FakeWebExportController()


@pytest.fixture
def dialog(qt_app, fake):
    import picasapy.app.application as app_module
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("webExportController", fake)
    factory = QQmlComponent(
        engine,
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "WebExportDialog.qml"),
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

    def test_starts_hidden(self, dialog):
        window, _fake, _qt_app = dialog
        assert window.property("visible") is False

    def test_open_loads_templates_and_shows_window(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert window.property("visible") is True
        templates = window.property("templates")
        if hasattr(templates, "toVariant"):
            templates = templates.toVariant()
        assert [t["id"] for t in templates] == ["feher", "masik"]

    def test_close_button_hides_the_window(self, dialog, qt_app):
        window, _fake, _qt_app2 = dialog
        window.setProperty("visible", True)
        qt_app.processEvents()
        _click(_child(window, "webExportCloseButton"))
        qt_app.processEvents()
        assert window.property("visible") is False


class TestGenerateButtonEnablement:
    def test_disabled_without_target_folder(self, dialog, qt_app):
        window, _fake, _qt_app2 = dialog
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        button = _child(window, "webExportGenerateButton")
        assert button.property("enabled") is False

    def test_enabled_once_target_folder_chosen(self, dialog, qt_app):
        window, _fake, _qt_app2 = dialog
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        window.setProperty("targetFolder", "/tmp/webexport-cel")
        qt_app.processEvents()
        button = _child(window, "webExportGenerateButton")
        assert button.property("enabled") is True


class TestStartExport:
    def test_generate_button_forwards_settings_to_controller(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        QMetaObject.invokeMethod(window, "open", Qt.ConnectionType.DirectConnection)
        window.setProperty("targetFolder", "/tmp/webexport-cel")
        window.setProperty("albumTitle", "Nyaralás")
        qt_app.processEvents()
        _click(_child(window, "webExportGenerateButton"))
        qt_app.processEvents()
        assert len(fake.generate_calls) == 1
        target, template_id, album_name = fake.generate_calls[0][:3]
        assert target == "/tmp/webexport-cel"
        assert template_id == "feher"
        assert album_name == "Nyaralás"

    def test_started_signal_shows_progress_section(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.webExportStarted.emit()
        qt_app.processEvents()
        assert window.property("exporting") is True

    def test_progress_signal_updates_progress_bar(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.webExportStarted.emit()
        fake.webExportProgress.emit(3, 10)
        qt_app.processEvents()
        fill = _child(window, "webExportProgressFill")
        track_width = fill.parent().property("width")
        assert fill.property("width") == pytest.approx(track_width * 0.3, rel=0.05)

    def test_finished_signal_shows_result_and_hides_progress(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.webExportStarted.emit()
        qt_app.processEvents()
        fake.webExportFinished.emit("/tmp/webexport-cel", 5)
        qt_app.processEvents()
        assert window.property("exporting") is False
        result_text = _child(window, "webExportResultText")
        assert result_text.property("visible") is True

    def test_failed_signal_shows_error_and_hides_progress(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.webExportStarted.emit()
        qt_app.processEvents()
        fake.webExportFailed.emit("Nincs kijelölt kép.")
        qt_app.processEvents()
        assert window.property("exporting") is False
        error_text = _child(window, "webExportErrorText")
        assert error_text.property("visible") is True
        assert "Nincs kijelölt kép" in str(error_text.property("text"))

    def test_close_disabled_while_exporting(self, dialog, qt_app):
        window, fake, _qt_app2 = dialog
        fake.webExportStarted.emit()
        qt_app.processEvents()
        close_button = _child(window, "webExportCloseButton")
        assert close_button.property("enabled") is False
