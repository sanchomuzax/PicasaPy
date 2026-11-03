"""#6471: a kilépéskori frissítésnek látható nyoma van, és a sorsa kiderül.

A gomb felirata „Update on exit” (magyarul „Frissítés kilépéskor”), a
megnyomása után a verziójelző a frissítés jelét mutatja; ha a segéd el sem
jutott a végéig, a következő indulás ezt kiírja.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Property, QPoint, QPointF, Signal, Slot, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.test_update_dialog_allapotok_6380 import (
    _AllapotosFake,
    _wait_for,
)


class _KilepeskorFake(_AllapotosFake):
    installScheduledChanged = Signal()

    def __init__(self, elozo_hiba: str = ""):
        super().__init__()
        self._install_scheduled = False
        self._elozo_hiba = elozo_hiba

    @Property(bool, notify=installScheduledChanged)
    def installScheduled(self):  # noqa: N802
        return self._install_scheduled

    @Property(str, constant=True)
    def previousUpdateFailure(self):  # noqa: N802
        return self._elozo_hiba

    @Slot(bool, result=bool)
    def installWhenExiting(self, _restart_now=False):  # noqa: N802
        self._install_scheduled = True
        self.installScheduledChanged.emit()
        return True


@pytest.mark.parametrize("magassag_elteres", (-5, 0, 5))
def test_a_gomb_ertheto_es_kilepeskorra_valtva_bezarul_a_dialogus(
    qml_app, qt_app, magassag_elteres
):
    window, _controller, engine = qml_app
    window.resize(window.width(), 800 + magassag_elteres)
    fake = _KilepeskorFake()
    fake.allit("ready")
    engine.rootContext().setContextProperty("updateController", fake)
    qt_app.processEvents()

    dialog = window.findChild(QObject, "updateDialog")
    button = window.findChild(QObject, "updateDialogInstallOnExitButton")
    label = window.findChild(QObject, "versionLabel")
    assert button.property("text") == "Update on exit"
    dialog.open()
    _wait_for(qt_app, lambda: bool(dialog.property("opened")), "az ablak nem nyílt meg")
    center = button.mapToScene(
        QPointF(button.property("width") / 2, button.property("height") / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    _wait_for(qt_app, lambda: not bool(dialog.property("opened")), "a párbeszéd nem zárult be")

    assert fake.installScheduled is True
    assert label.property("text") == "↻1.0.12"
    assert "PicasaPy closes" in label.property("tooltipText")

    kimenet = os.environ.get("PICASAPY_RENDER_KIMENET")
    if kimenet:
        Path(kimenet).mkdir(parents=True, exist_ok=True)
        window.grabWindow().save(str(Path(kimenet) / f"frissites-kilepeskor-6471-{magassag_elteres}.png"))


@pytest.mark.parametrize(
    ("kod", "szoveg"),
    (("nem-futott", "stopped before it finished"), ("verzio", "earlier version started")),
)
def test_az_el_sem_keszult_frissites_oka_indulaskor_megjelenik(qml_app, qt_app, kod, szoveg):
    window, _controller, engine = qml_app
    window.resize(1280, 800)
    fake = _KilepeskorFake(kod)
    engine.rootContext().setContextProperty("updateController", fake)
    qt_app.processEvents()

    dialog = window.findChild(QObject, "updateDialog")
    feedback = window.findChild(QObject, "updateDialogFeedback")
    _wait_for(qt_app, lambda: bool(dialog.property("opened")), "a hibaablak nem nyílt meg")

    assert feedback.property("visible") is True
    assert "previous update could not be installed" in feedback.property("text")
    assert szoveg in feedback.property("text")
