"""A retusáló ecsetköre a képen követi a kurzort és jelöli a folt két végét."""

from __future__ import annotations

import math
import time

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
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


def _jelenet_pont(elem, x: float, y: float) -> QPointF:
    return elem.mapToScene(QPointF(x, y))


def _ellenoriz_kor_kepet(kep, kozep: QPointF, sugar: float) -> None:
    """A szöveg nélküli fotóképen a körvonal képpontjait ellenőrzi."""
    lathato_iranyok = 0
    for fok in range(0, 360, 15):
        szog = math.radians(fok)
        korvonal = False
        for eltolás in range(-3, 4):
            px = round(kozep.x() + (sugar + eltolás) * math.cos(szog))
            py = round(kozep.y() + (sugar + eltolás) * math.sin(szog))
            if not (0 <= px < kep.width() and 0 <= py < kep.height()):
                continue
            szin = kep.pixelColor(px, py)
            # A teszt egyenletes szürke fotóján a fekete/fehér körvonal
            # mindkét oldala jól elkülönül az alapkép 200-as tónusától.
            if max(szin.red(), szin.green(), szin.blue()) > 230 or max(
                szin.red(), szin.green(), szin.blue()
            ) < 100:
                korvonal = True
                break
        if korvonal:
            lathato_iranyok += 1
    assert lathato_iranyok >= 18, (
        f"a renderelt ecsetkör csak {lathato_iranyok}/24 irányban látszik"
    )


def _kattint(ablak, pont: QPointF) -> None:
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        pos=QPoint(round(pont.x()), round(pont.y())),
    )


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_retus_ecsetkor_cel_es_forras_latszik_kattintas_utan(
    qml_app_valodi_belyegkep, qt_app, tmp_path, magassageltolas
):
    ablak, _controller, engine = qml_app_valodi_belyegkep
    alapmagassag = ablak.height()
    ablak.setHeight(alapmagassag + magassageltolas)
    assert _varj(qt_app, lambda: ablak.height() == alapmagassag + magassageltolas)

    ablak.setProperty("viewerOpen", True)
    nezo = ablak.findChild(QObject, "photoViewer")
    assert nezo is not None
    nezo.setProperty("currentIndex", 0)
    kep = ablak.findChild(QObject, "viewerImage")
    assert kep is not None
    assert _varj(qt_app, lambda: kep.property("visible"))

    panel = ablak.findChild(QObject, "viewerEditorPanel")
    terulet = ablak.findChild(QObject, "retouchClickArea")
    edit = engine.rootContext().contextProperty("editController")
    assert panel is not None and terulet is not None and edit is not None
    assert _varj(qt_app, lambda: terulet.width() > 0 and terulet.height() > 0)

    cel_xy = QPointF(terulet.width() * 0.32, terulet.height() * 0.43)
    forras_xy = QPointF(terulet.width() * 0.68, terulet.height() * 0.58)
    cel = _jelenet_pont(terulet, cel_xy.x(), cel_xy.y())
    forras = _jelenet_pont(terulet, forras_xy.x(), forras_xy.y())

    alap = ablak.grabWindow()
    assert not alap.isNull(), "a nézőablak alapképe nem renderelődött"

    panel.setProperty("retouchActive", True)
    QTest.mouseMove(ablak, QPoint(round(cel.x()), round(cel.y())))
    ecset = ablak.findChild(QObject, "retouchBrushCursor")
    assert ecset is not None, "a retusáló ecsetkurzor kör-overlaye hiányzik"
    assert _varj(qt_app, lambda: ecset.property("visible"))
    assert _varj(qt_app, lambda: terulet.property("containsMouse"))
    elvart_sugar = edit.property("retouchBrushRadiusRatio") * min(
        terulet.width(), terulet.height()
    )
    assert abs(float(ecset.width()) / 2 - elvart_sugar) <= 3, (
        "az ecsetkör sugara nem a retusáló patch aktuális sugarát követi"
    )

    ecset_kep = ablak.grabWindow()
    assert not ecset_kep.isNull()
    ecset_kozep = _jelenet_pont(ecset, ecset.width() / 2, ecset.height() / 2)
    ecset_sugar = float(ecset.width()) / 2
    _ellenoriz_kor_kepet(ecset_kep, ecset_kozep, ecset_sugar)

    _kattint(ablak, cel)
    assert _varj(qt_app, lambda: panel.property("retouchPatchPending"))
    cel_kor = ablak.findChild(QObject, "retouchTargetCircle")
    assert cel_kor is not None and _varj(qt_app, lambda: cel_kor.property("visible")), (
        "az első kattintás után nem maradt meg a célkör"
    )

    QTest.mouseMove(ablak, QPoint(round(forras.x()), round(forras.y())))
    assert _varj(qt_app, lambda: terulet.property("mouseX") > 0)
    cel_kozep = _jelenet_pont(cel_kor, cel_kor.width() / 2, cel_kor.height() / 2)
    assert abs(cel_kozep.x() - cel.x()) <= 3
    assert abs(cel_kozep.y() - cel.y()) <= 3

    _kattint(ablak, forras)
    assert _varj(qt_app, lambda: not panel.property("retouchPatchPending"))
    forras_kor = ablak.findChild(QObject, "retouchSourceCircle")
    assert forras_kor is not None and _varj(
        qt_app, lambda: forras_kor.property("visible")
    ), "a második kattintás után nem jelent meg a forráskör"
    forras_kozep = _jelenet_pont(
        forras_kor, forras_kor.width() / 2, forras_kor.height() / 2
    )
    assert abs(forras_kozep.x() - forras.x()) <= 3
    assert abs(forras_kozep.y() - forras.y()) <= 3

    renderelt = ablak.grabWindow()
    assert not renderelt.isNull()
    _ellenoriz_kor_kepet(renderelt, cel_kozep, float(cel_kor.width()) / 2)
    _ellenoriz_kor_kepet(renderelt, forras_kozep, float(forras_kor.width()) / 2)
    if magassageltolas == 0:
        assert renderelt.save(str(tmp_path / "retouch-4543.png"))
