"""#4679: az ablakig eljutó dupla kattintás a nézőből is kilép.

A probe Windows-on olyan MouseButtonDblClick eseményt látott, amely nem
zárta be a nézőt. A teszt a window event filterben elnyeli ezt az eseményt,
így azt ellenőrzi, hogy a második lenyomásra épülő tartalék út bezár-e.
"""

# rontás-kontroll: PhotoViewer.viewerPanArea.secondPressExit = False → 3 failed

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


class _DoubleClickElnyelo(QObject):
    def __init__(self):
        super().__init__()
        self.elnyelt = 0

    def eventFilter(self, _cel, event):
        if event.type() == QEvent.Type.MouseButtonDblClick:
            self.elnyelt += 1
            return True
        return False


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_gyors_masodik_kattintas_kilep_az_allokepes_nezobol(
    qml_app, qt_app, magassageltolas
):
    ablak, controller, _engine = qml_app
    alapmagassag = ablak.height()
    ablak.setHeight(alapmagassag + magassageltolas)
    assert _varj(qt_app, lambda: ablak.height() == alapmagassag + magassageltolas)

    ablak.setProperty("viewerOpen", True)
    viewer = ablak.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    kep = ablak.findChild(QObject, "viewerImage")
    assert kep is not None and _varj(qt_app, lambda: kep.property("visible"))
    viewer.setProperty("zoomValue", 1.0)
    controller.setSingleClickExitEnabled(True)

    pan_area = ablak.findChild(QObject, "viewerPanArea")
    assert pan_area is not None
    assert _varj(
        qt_app,
        lambda: pan_area.property("enabled")
        and pan_area.property("width") > 0
        and pan_area.property("height") > 0,
    )
    pont = pan_area.mapToScene(
        QPointF(pan_area.property("width") / 2, pan_area.property("height") / 2)
    ).toPoint()
    timer = pan_area.findChild(QObject, "singleClickExitTimer")
    assert timer is not None
    double_click_ms = QGuiApplication.styleHints().mouseDoubleClickInterval()
    # A teszt előző paraméterének QTest-eseményóráját zárja le.
    QTest.mouseMove(ablak, pont + QPoint(1, 0), delay=double_click_ms + 1)

    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=pont, delay=10)
    qt_app.processEvents()
    assert ablak.property("viewerOpen") is True, (
        "az első kattintásnak meg kell várnia a duplakattintási időablakot"
    )
    assert timer.property("running") is True, (
        "az első kattintás kilépési időzítőjének még futnia kell"
    )

    elnyelo = _DoubleClickElnyelo()
    ablak.installEventFilter(elnyelo)
    dupla_kattintasok = []
    pan_area.doubleClicked.connect(lambda *_args: dupla_kattintasok.append(True))
    QTest.mouseDClick(ablak, Qt.MouseButton.LeftButton, pos=pont, delay=10)
    qt_app.processEvents()
    ablak.removeEventFilter(elnyelo)

    assert elnyelo.elnyelt == 1, "a próba nem nyelte el a dupla kattintás eseményét"
    assert dupla_kattintasok == [], "a MouseArea doubleClicked jelzése eljutott a kezelőhöz"
    assert ablak.property("viewerOpen") is False, (
        "a MouseArea doubleClicked jelzése nélkül a második kattintás "
        "nem zárta be az állóképes nézőt"
    )
