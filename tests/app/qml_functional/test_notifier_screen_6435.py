"""#6435: az értesítősáv a főablak képernyőjén jelenik meg."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Property, QRect, Signal
from PySide6.QtQml import QQmlComponent, QQmlEngine
import pytest
from tests.support.qt_wait import varj_feltetelre


class FakeScreen(QObject):
    geometryChanged = Signal()

    def __init__(self, geometry: QRect):
        super().__init__()
        self._geometry = geometry

    @Property(QRect, notify=geometryChanged)
    def availableGeometry(self):
        return self._geometry


class FakeMainWindow(QObject):
    screenChanged = Signal()
    visibleChanged = Signal()
    visibilityChanged = Signal()
    widthChanged = Signal()
    heightChanged = Signal()

    def __init__(self, screen: FakeScreen, height: int):
        super().__init__()
        self._screen = screen
        self._visible = True
        self._width = 1200
        self._height = height

    @Property(QObject, notify=screenChanged)
    def screen(self):
        return self._screen

    @Property(bool, notify=visibleChanged)
    def visible(self):
        return self._visible

    @Property(int, notify=visibilityChanged)
    def visibility(self):
        return 0

    @Property(int, notify=widthChanged)
    def width(self):
        return self._width

    @Property(int, notify=heightChanged)
    def height(self):
        return self._height

    def setScreen(self, screen: FakeScreen) -> None:
        self._screen = screen
        self.screenChanged.emit()

    def setVisible(self, visible: bool) -> None:
        self._visible = visible
        self.visibleChanged.emit()

    def setSize(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self.widthChanged.emit()
        self.heightChanged.emit()


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_a_masodik_kepernyon_allo_foablaknal_oda_renderelodik_az_ertesito(
    qt_app, height_delta: int
):
    import picasapy.app.application as app_module

    primary = FakeScreen(QRect(0, 0, 1920, 1080))
    second = FakeScreen(QRect(1920, 75, 1440, 900))
    assert primary.availableGeometry != second.availableGeometry
    main_window = FakeMainWindow(second, 800 + height_delta)

    qml_dir = Path(app_module._APP_DIR) / "qml"
    engine = QQmlEngine()
    engine.addImportPath(str(qml_dir))
    component = QQmlComponent(
        engine, str(qml_dir / "PicasaPy" / "PicasaNotifier.qml")
    )
    notifier = component.createWithInitialProperties(
        {"_hostWindow": main_window}
    )
    assert notifier is not None, component.errorString()

    try:
        assert notifier.property("x") == (
            second.availableGeometry.x()
            + second.availableGeometry.width()
            - notifier.property("width")
        )
        assert notifier.property("y") == (
            second.availableGeometry.y()
            + second.availableGeometry.height()
            - notifier.property("anchorOffsetPx")
        )

        notifier.notify("screen-test", "Rendered", "", "")
        assert varj_feltetelre(qt_app, lambda: notifier.property("visible"))
        tartalom = notifier.contentItem().childItems()[0]
        assert varj_feltetelre(
            qt_app, lambda: tartalom.property("opacity") >= 0.99
        )
        assert not notifier.grabWindow().isNull()

        main_window.setVisible(False)
        main_window.setScreen(primary)
        assert varj_feltetelre(
            qt_app,
            lambda: notifier.property("x")
            == second.availableGeometry.x()
            + second.availableGeometry.width()
            - notifier.property("width"),
        )

        main_window.setVisible(True)
        assert varj_feltetelre(
            qt_app,
            lambda: notifier.property("x")
            == primary.availableGeometry.x()
            + primary.availableGeometry.width()
            - notifier.property("width"),
        )
        main_window.setSize(1, 1)
        main_window.setScreen(second)
        assert varj_feltetelre(
            qt_app,
            lambda: notifier.property("x")
            == primary.availableGeometry.x()
            + primary.availableGeometry.width()
            - notifier.property("width"),
        )
    finally:
        notifier.deleteLater()
        engine.deleteLater()
        qt_app.processEvents()
