"""#4449: a videó-előnézet kattintásos kilépési módja."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Qt, QUrl
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest


_AREA_QML = (
    Path(__file__).resolve().parents[2]
    / "src/picasapy/app/qml/PicasaPy/VideoExitGestureArea.qml"
)
_QML_DIR = _AREA_QML.parent


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


def _ablak(qt_app, magassageltolas: int):
    view = QQuickView()
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.setSource(QUrl.fromLocalFile(str(_AREA_QML)))
    assert view.status() == QQuickView.Status.Ready, view.errors()
    view.resize(640, 480 + magassageltolas)
    view.show()
    assert _varj(qt_app, lambda: view.isVisible() and view.rootObject().width() > 0)
    return view, view.rootObject()


def _kattints(ablak, elem, dupla=False):
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    if dupla:
        QTest.mouseDClick(ablak, Qt.MouseButton.LeftButton, pos=pont)
    else:
        QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, pos=pont)


def test_a_videofelulet_kilepese_a_nezo_kozos_kilepesi_utjara_vezet():
    gesztus = (_QML_DIR / "VideoExitGestureArea.qml").read_text(encoding="utf-8")
    lejatsszo = (_QML_DIR / "VideoPlayerView.qml").read_text(encoding="utf-8")
    nezo = (_QML_DIR / "PhotoViewer.qml").read_text(encoding="utf-8")

    assert "anchors.fill: viewport" in lejatsszo
    assert "singleClickExit: true" not in gesztus
    assert "onPressed:" in gesztus and "root.singleClickExit" in gesztus
    assert "onDoubleClicked:" in gesztus and "!root.singleClickExit" in gesztus
    assert "onExitRequested: player.exitRequested()" in lejatsszo
    assert "function onExitRequested()" in nezo
    assert "viewer.kerBezaras()" in nezo


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_alaperteken_egyszeres_kattintas_var_dupla_kattintast(
    qt_app, magassageltolas
):
    ablak, terulet = _ablak(qt_app, magassageltolas)
    kilepesek = []
    terulet.exitRequested.connect(lambda: kilepesek.append(True))
    terulet.setProperty("singleClickExit", False)

    _kattints(ablak, terulet)
    assert kilepesek == [], "az alapértelmezett egyszeres kattintás kiléptetett"

    _kattints(ablak, terulet, dupla=True)
    assert _varj(qt_app, lambda: len(kilepesek) == 1), (
        "alapállapotban a videó-előnézeti dupla kattintás nem kért kilépést"
    )
    ablak.close()


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_egykattintas_modban_a_balgomb_lenyomasa_kilep(
    qt_app, magassageltolas
):
    ablak, terulet = _ablak(qt_app, magassageltolas)
    kilepesek = []
    terulet.exitRequested.connect(lambda: kilepesek.append(True))
    terulet.setProperty("singleClickExit", True)

    _kattints(ablak, terulet)
    assert _varj(qt_app, lambda: len(kilepesek) == 1), (
        "SingleClickExit mellett a balgomb-lenyomás nem kért azonnali kilépést"
    )
    ablak.close()
