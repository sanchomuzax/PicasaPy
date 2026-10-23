"""#5639: valódi Python-jelből megjelenő képernyőfelvétel-értesítés."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QSettings, Signal, Slot
from PySide6.QtGui import QColor, QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine

from picasapy.app.screen_capture import ScreenCaptureController
from tests.support.qt_wait import wait_for_signal


class FakeController(QObject):
    collageDesktopBackgroundReady = Signal(str)

    @Slot(str)
    def selectFolder(self, _folder_path: str) -> None:
        pass


class FakeCaptureSource:
    supported = True

    def __init__(self):
        self.pressed_keys = set()
        self.image = QImage(2, 2, QImage.Format.Format_RGB32)
        self.image.fill(QColor(25, 80, 140))

    def is_key_down(self, virtual_key):
        return virtual_key in self.pressed_keys

    def foreground_window(self):
        return 101

    def cursor_window(self):
        return 202

    def capture(self, _target):
        return self.image

    def window_title(self, _target):
        return "Example window"


def test_sikeres_rogzites_utan_a_sav_a_fajl_utvonalat_mutatja(qt_app, tmp_path):
    import picasapy.app.application as app_module

    qml_dir = Path(app_module._APP_DIR) / "qml"
    engine = QQmlEngine()
    engine.addImportPath(str(qml_dir))
    controller = FakeController()
    source = FakeCaptureSource()
    capture_controller = ScreenCaptureController(
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
        source=source,
        folder_resolver=lambda: tmp_path / "Picasa" / "Screen Captures",
    )
    saved_paths = []
    capture_controller.screenCaptureSaved.connect(saved_paths.append)
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty(
        "screenCaptureController", capture_controller
    )
    component = QQmlComponent(engine, str(qml_dir / "PicasaPy" / "PicasaNotifier.qml"))
    notifier = component.create()
    try:
        assert notifier is not None, component.errorString()
        wait_for_signal(
            capture_controller.screenCaptureSaved,
            lambda: source.pressed_keys.add(0x2C),
            description="a Print Screen mentési jelzés",
            process_events_with=qt_app,
        )
        source.pressed_keys.clear()

        target = saved_paths[-1]
        assert target
        assert Path(target).is_file()
        assert notifier.property("cellCount") == 1
        assert notifier.property("lastTitle") == "Screenshot saved"
        assert notifier.property("lastHint") == "click to view"
        assert notifier.property("lastPayload") == target
    finally:
        source.pressed_keys.clear()
        capture_controller.shutdown()
        if notifier is not None:
            notifier.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()
