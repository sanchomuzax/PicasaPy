"""#4449: a beállítás a videóhoz kötött; az állóképes dupla kattintás marad."""

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


def _kattints(qt_app, ablak, elem, dupla=False):
    assert _varj(qt_app, lambda: elem.width() > 0 and elem.height() > 0)
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    if dupla:
        QTest.mouseDClick(ablak, Qt.MouseButton.LeftButton, pos=pont)
    else:
        QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=pont)


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_egykattintas_beallitasa_nem_valtoztatja_az_allokepes_dupla_kattintast(
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
    assert _varj(qt_app, lambda: ablak.findChild(QObject, "viewerImage") is not None)
    kep = ablak.findChild(QObject, "viewerImage")
    assert _varj(qt_app, lambda: kep.property("visible"))

    controller.setSingleClickExitEnabled(True)
    viewer.setProperty("zoomValue", 1.0)
    pan_area = ablak.findChild(QObject, "viewerPanArea")
    assert pan_area is not None
    assert _varj(qt_app, lambda: pan_area.property("enabled"))

    _kattints(qt_app, ablak, pan_area)
    assert ablak.property("viewerOpen") is True, (
        "az állóképes egyszeres kattintás bezárta a szerkesztőnézetet"
    )
    _kattints(qt_app, ablak, pan_area, dupla=True)
    assert _varj(qt_app, lambda: abs(viewer.property("zoomFactor") - 1.0) < 0.01), (
        "az állóképes dupla kattintásnak továbbra is nagyítás-illesztést kell adnia"
    )
    ablak.setProperty("viewerOpen", False)
