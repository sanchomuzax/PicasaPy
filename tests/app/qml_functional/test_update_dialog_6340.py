"""#6340: a verziócímkére kattintás a valódi frissítési ablakot nyitja."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import Property, QPoint, QPointF, QObject, Signal, Slot, Qt
from PySide6.QtTest import QTest


class _FakeUpdateController(QObject):
    updateAvailableChanged = Signal()
    checkingChanged = Signal()
    progressChanged = Signal()
    autoCheckEnabledChanged = Signal()
    activityChanged = Signal()
    notificationRequested = Signal()
    manualCheckFinished = Signal(bool, str)
    downloadFinished = Signal(bool, str)

    @Property(bool, notify=updateAvailableChanged)
    def updateAvailable(self):  # noqa: N802
        return True

    @Property(str, notify=updateAvailableChanged)
    def availableVersion(self):  # noqa: N802
        return "9.8.7"

    @Property(str, notify=updateAvailableChanged)
    def releaseNotes(self):  # noqa: N802
        return "A rövid kiadási leírás."

    @Property(str, notify=updateAvailableChanged)
    def releaseUrl(self):  # noqa: N802
        return "https://example.test/release"

    @Property(bool, notify=updateAvailableChanged)
    def oneClickUpdateSupported(self):  # noqa: N802
        return False

    @Property(str, notify=updateAvailableChanged)
    def updateCommand(self):  # noqa: N802
        return "python -m pip install --upgrade picasapy"

    @Property(bool, notify=checkingChanged)
    def checking(self):
        return False

    @Property(int, notify=progressChanged)
    def downloadProgress(self):  # noqa: N802
        return 0

    @Property(str, notify=progressChanged)
    def downloadState(self):  # noqa: N802
        return "idle"

    @Property(bool, notify=activityChanged)
    def applicationBusy(self):  # noqa: N802
        return False

    @Slot()
    def checkForUpdates(self):  # noqa: N802
        self.manualCheckFinished.emit(True, "available")

    @Slot()
    def deferAvailableVersion(self):  # noqa: N802
        pass

    @Slot()
    def skipAvailableVersion(self):  # noqa: N802
        pass

    @Slot()
    def downloadUpdate(self):  # noqa: N802
        pass

    @Slot(bool, result=bool)
    def installWhenExiting(self, _restart_now=False):  # noqa: N802
        return True


def _wait_for(qt_app, condition, message: str, timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return
        time.sleep(0.05)
    qt_app.processEvents()
    assert condition(), message


@pytest.mark.parametrize("magassag_elteres", (-5, 0, 5))
def test_valodi_verzio_cimke_kattintasa_megnyitja_a_frissitesi_ablakot(
    qml_app, qt_app, magassag_elteres
):
    window, _controller, engine = qml_app
    window.resize(window.width(), 800 + magassag_elteres)
    fake = _FakeUpdateController()
    engine.rootContext().setContextProperty("updateController", fake)
    qt_app.processEvents()

    version_label = window.findChild(QObject, "versionLabel")
    update_dialog = window.findChild(QObject, "updateDialog")
    assert version_label is not None
    assert update_dialog is not None
    assert version_label.property("width") > 0
    center = version_label.mapToScene(
        QPointF(version_label.property("width") / 2,
                version_label.property("height") / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    _wait_for(qt_app, lambda: update_dialog.property("visible"),
              "a verziócímke kattintása nem nyitotta meg a frissítési ablakot")
    assert "9.8.7" in update_dialog.property("title")
    assert window.findChild(QObject, "updateDialogReleaseNotes").property("text") == (
        "A rövid kiadási leírás."
    )
