"""#6380: a frissítési ablak minden állapotában (ajánlat, letöltés, kész) a
gombsor és a folyamatjelző az ablakon belül marad, hosszú kiadási leírással
is; a "Frissítés most" valódi kattintásra azonnal folyamatjelzőre vált.

A geometriát a renderelt ablak elemeiből mérjük; a `PICASAPY_RENDER_KIMENET`
megadásakor az állapotok képe is lemezre kerül, szemrevételezéshez.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import Property, QObject, QPoint, QPointF, Qt, Slot
from PySide6.QtTest import QTest

from tests.app.qml_functional.test_update_dialog_6340 import (
    _FakeUpdateController,
    _wait_for,
)

_HOSSZU_LEIRAS = "\n".join(
    f"- A {i}. változás hosszú leírása, amely több sorba is átnyúlik, hogy "
    f"a kiadási jegyzet görgethető legyen és kitöltse az ablakot (#63{i:02d})."
    for i in range(14)
)


class _AllapotosFake(_FakeUpdateController):
    def __init__(self):
        super().__init__()
        self._allapot = "idle"
        self.letoltes_kerve = 0

    @Property(str, notify=_FakeUpdateController.updateAvailableChanged)
    def availableVersion(self):  # noqa: N802
        return "1.0.12"

    @Property(str, notify=_FakeUpdateController.updateAvailableChanged)
    def releaseNotes(self):  # noqa: N802
        return _HOSSZU_LEIRAS

    @Property(bool, notify=_FakeUpdateController.updateAvailableChanged)
    def oneClickUpdateSupported(self):  # noqa: N802
        return True

    @Property(str, notify=_FakeUpdateController.progressChanged)
    def downloadState(self):  # noqa: N802
        return self._allapot

    def allit(self, allapot: str) -> None:
        self._allapot = allapot
        self.progressChanged.emit()

    @Slot()
    def downloadUpdate(self):  # noqa: N802
        self.letoltes_kerve += 1
        self.allit("downloading")


def _keret(elem, gyoker):
    bal_felso = elem.mapToItem(gyoker, QPointF(0, 0))
    return (bal_felso.x(), bal_felso.y(),
            bal_felso.x() + elem.property("width"),
            bal_felso.y() + elem.property("height"))


def _megnyit(qml_app, qt_app):
    window, _controller, engine = qml_app
    window.resize(1280, 800)
    fake = _AllapotosFake()
    engine.rootContext().setContextProperty("updateController", fake)
    dialog = window.findChild(QObject, "updateDialog")
    dialog.open()
    _wait_for(qt_app, lambda: bool(dialog.property("opened")), "az ablak nem nyílt meg")
    for _ in range(5):
        qt_app.processEvents()
    return window, dialog, fake


def _lathato_elemek_az_ablakon_belul(window, dialog, nevek):
    tartalom = dialog.property("contentItem")
    ablak = _keret(dialog.property("background"), tartalom)
    lathato = []
    for nev in nevek:
        elem = window.findChild(QObject, nev)
        if not elem.property("visible"):
            continue
        bal, fent, jobb, lent = _keret(elem, tartalom)
        assert ablak[0] + 4 <= bal and jobb <= ablak[2] - 4, f"{nev} vízszintesen kilóg"
        assert ablak[1] <= fent and lent <= ablak[3] - 4, f"{nev} kilóg az ablak aljából"
        lathato.append(nev)
    return lathato


def _ment(window, nev):
    kimenet = os.environ.get("PICASAPY_RENDER_KIMENET")
    if kimenet:
        Path(kimenet).mkdir(parents=True, exist_ok=True)
        window.grabWindow().save(str(Path(kimenet) / f"frissitesi-ablak-{nev}.png"))


_GOMBOK = ("updateDialogDownloadButton", "updateDialogLaterButton",
           "updateDialogSkipButton", "updateDialogRestartButton",
           "updateDialogInstallOnExitButton", "updateDialogCloseButton",
           "updateDialogProgress")


def test_minden_allapotban_a_gombsor_az_ablakon_belul_marad(qml_app, qt_app):
    window, dialog, fake = _megnyit(qml_app, qt_app)
    vart = {
        "idle": {"updateDialogDownloadButton", "updateDialogLaterButton",
                 "updateDialogSkipButton"},
        "downloading": {"updateDialogLaterButton", "updateDialogProgress"},
        "ready": {"updateDialogRestartButton", "updateDialogInstallOnExitButton"},
    }
    for allapot, elemek in vart.items():
        fake.allit(allapot)
        for _ in range(5):
            qt_app.processEvents()
        _ment(window, allapot)
        lathato = _lathato_elemek_az_ablakon_belul(window, dialog, _GOMBOK)
        assert set(lathato) == elemek, allapot
    dialog.close()
    del fake


def test_frissites_most_kattintasra_azonnal_folyamatjelzo(qml_app, qt_app):
    window, dialog, fake = _megnyit(qml_app, qt_app)
    gomb = window.findChild(QObject, "updateDialogDownloadButton")
    kozep = gomb.mapToScene(QPointF(gomb.property("width") / 2, gomb.property("height") / 2))

    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                     QPoint(round(kozep.x()), round(kozep.y())))
    qt_app.processEvents()

    assert fake.letoltes_kerve == 1
    folyamat = window.findChild(QObject, "updateDialogProgress")
    assert folyamat.property("visible"), "a kattintás után nincs folyamatjelző"
    assert folyamat.property("indeterminate"), "ismeretlen méretnél határozatlan legyen"
    assert not gomb.property("visible"), "a zöld gomb kattintás után is látszik"
    _ment(window, "kattintas-utan")
    dialog.close()
    del fake
