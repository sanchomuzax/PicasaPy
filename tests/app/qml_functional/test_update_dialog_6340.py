"""#6340: a verziócímkére kattintás a valódi frissítési ablakot nyitja."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import Property, QPoint, QPointF, QObject, Signal, Slot, Qt
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre


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


def test_az_uj_verzio_cimkeje_kifer_a_mezo_mogotti_helyre(qml_app, qt_app):
    """#6340/#6348: a frissítés címkéje nem lóghat a keresőmezőre, és nem is
    vágódhat le — a rövid jel („↑9.8.7”) a teljes szélességében látszik."""
    window, _controller, engine = qml_app
    window.resize(1200, 800)
    fake = _FakeUpdateController()
    engine.rootContext().setContextProperty("updateController", fake)
    for _ in range(5):
        qt_app.processEvents()
    cimke = window.findChild(QObject, "versionLabel")
    mezo = window.findChild(QObject, "toolbarSearchBox")
    sav = window.findChild(QObject, "mainToolbar")
    assert cimke.property("text") == "↑9.8.7"
    assert cimke.property("truncated") is False
    cimke_bal = cimke.mapToItem(sav, QPointF(0, 0)).x()
    mezo_jobb = mezo.mapToItem(sav, QPointF(0, 0)).x() + mezo.property("width")
    assert cimke_bal >= mezo_jobb + 2
    assert "9.8.7" in cimke.property("tooltipText")


class _LetoltesreValtoFake(_FakeUpdateController):
    def __init__(self):
        super().__init__()
        self._download_state = "idle"

    @Property(bool, notify=_FakeUpdateController.updateAvailableChanged)
    def oneClickUpdateSupported(self):  # noqa: N802
        return True

    @Property(str, notify=_FakeUpdateController.progressChanged)
    def downloadState(self):  # noqa: N802
        return self._download_state

    @Slot()
    def downloadUpdate(self):  # noqa: N802
        self._download_state = "downloading"
        self.progressChanged.emit()


@pytest.mark.parametrize("magassag_elteres", (-5, 0, 5))
def test_a_frissites_gomb_elso_kattintasa_azonnali_foglalt_allapotot_ad(
    qml_app, qt_app, magassag_elteres
):
    """A kattintásra azonnal mozgó folyamatsáv jelenik meg a gomb helyén (#6380)."""
    window, _controller, engine = qml_app
    window.resize(window.width(), 800 + magassag_elteres)
    fake = _LetoltesreValtoFake()
    engine.rootContext().setContextProperty("updateController", fake)
    qt_app.processEvents()

    dialog = window.findChild(QObject, "updateDialog")
    progress = window.findChild(QObject, "updateDialogProgress")
    button = window.findChild(QObject, "updateDialogDownloadButton")
    dialog.open()
    _wait_for(qt_app, lambda: bool(dialog.property("opened")), "az ablak nem nyílt meg")
    assert button.property("visible")
    elotte = window.grabWindow()

    center = button.mapToScene(
        QPointF(button.property("width") / 2, button.property("height") / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    assert fake.downloadState == "downloading", "a kattintás nem indította el a próbaletöltést"
    assert var_feltetelre(
        qt_app, lambda: bool(progress.property("visible")), 3.0
    ), "a letöltés folyamatsávja nem jelent meg"
    assert progress.property("indeterminate"), "a 0%-os folyamatsáv nem mozgott"
    assert not button.property("visible"), "a letöltés újraindítható maradt"

    utana = window.grabWindow()
    dpr = utana.width() / window.width()
    bal_felso = progress.mapToScene(QPointF(0, 0))
    bal = round((bal_felso.x() + 2) * dpr)
    jobb = round((bal_felso.x() + progress.property("width") - 2) * dpr)
    y = round((bal_felso.y() + progress.property("height") / 2) * dpr)
    eltero_pixelek = sum(
        elotte.pixelColor(x, y) != utana.pixelColor(x, y)
        for x in range(bal, jobb + 1)
    )
    assert eltero_pixelek > 0, "a folyamatsáv nem adott látható képpont-visszajelzést"

    dialog.close()
    del fake
