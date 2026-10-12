"""#4683: a második lenyomás diagnosztikája legyen QML-ből olvasható."""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
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


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_a_masodik_lenyomas_rogziti_az_idozitot_es_a_kilepesi_agat(
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
    timer = ablak.findChild(QObject, "singleClickExitTimer")
    assert pan_area is not None and timer is not None
    assert _varj(
        qt_app,
        lambda: pan_area.property("enabled")
        and pan_area.property("width") > 0
        and pan_area.property("height") > 0,
    )
    pont = pan_area.mapToScene(
        QPointF(pan_area.property("width") / 2, pan_area.property("height") / 2)
    ).toPoint()

    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=pont, delay=10)
    qt_app.processEvents()
    assert timer.property("running") is True, (
        f"az első kattintás után timer={timer.property('running')!r}, "
        f"pressCount={pan_area.property('pressEventCount')!r}, "
        f"branch={pan_area.property('lastPressBranch')!r}, "
        f"timerAtPress={pan_area.property('timerRunningOnLastPress')!r}"
    )
    assert pan_area.property("pressEventCount") == 1
    assert pan_area.property("lastPressBranch") == "accepted"

    QTest.mousePress(ablak, Qt.MouseButton.LeftButton, pos=pont, delay=10)
    qt_app.processEvents()
    assert pan_area.property("pressEventCount") == 2
    assert pan_area.property("timerRunningOnLastPress") is True
    assert pan_area.property("lastPressBranch") == "second-press-exit"
    assert pan_area.property("exitAfterDoubleClick") is True

    QTest.mouseRelease(ablak, Qt.MouseButton.LeftButton, pos=pont, delay=10)
    assert _varj(qt_app, lambda: ablak.property("viewerOpen") is False), (
        "a második lenyomás után a néző nem zárult be"
    )
