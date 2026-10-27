"""Az eredeti Picasa szerkesztőfüleinek színei és függőleges igazítása (#5959)."""

# rontás-kontroll: javítás előtti QML-lel (iconTop=4, #2b2b2b, sík négyzet) → 9 failed

from __future__ import annotations

import math
import os
import time
from contextlib import contextmanager

import pytest
from PySide6.QtCore import QObject, QPointF, QRect, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

_QML = """
import QtQuick
import PicasaPy 1.0
Item {
    objectName: "stripRoot"
    width: 276
    height: 120
    Rectangle { anchors.fill: parent; color: "#e8e8e8" }
    QtObject {
        id: panel
        property int activeTab: 0
        property bool legacyEffectsPresent: false
        function selectTab(index) { activeTab = index }
    }
    EditorTabBar {
        objectName: "editorTabBar"
        panel: panel
        width: parent.width
        anchors.top: parent.top
        anchors.topMargin: 40
    }
}
"""

_TABLAK = (
    ("editTabFixes", "#373535"),
    ("editTabFinetune", "#373535"),
    ("editTabEffects", "#373535"),
    ("editTabEffects2", "#373535"),
    ("editTabEffects3", "#373535"),
)
_TAJKÉP_SZÍNEK = {
    "editTabEffects2": {
        "felso": ((191, 214, 179), 8, 1),
        "kozep": ((142, 183, 122), 8, 8),
        "also": ((154, 191, 136), 4, 11),
        "felho": ((248, 250, 247), 12, 4),
    },
    "editTabEffects3": {
        "felso": ((166, 207, 227), 8, 1),
        "kozep": ((98, 170, 207), 8, 8),
        "also": ((115, 179, 212), 4, 11),
        "felho": ((245, 249, 252), 12, 4),
    },
}


@contextmanager
def _rendered_tab_bar(qt_app, height: int):
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    component = QQmlComponent(view.engine())
    component.setData(_QML.encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    root.setWidth(276)
    root.setHeight(height)
    view.resize(276, height)
    view.show()
    try:
        yield view, root, component, _render_until_icons_ready(qt_app, view, root)
    finally:
        view.close()
        component.deleteLater()


def _render_until_icons_ready(qt_app, view, root):
    hatarido = time.monotonic() + 3
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        kep = view.grabWindow()
        if not kep.isNull():
            dpr = kep.devicePixelRatio()
            for tab_name, _ in _TABLAK:
                ikon = _child(root, tab_name + "Icon")
                pont = ikon.mapToScene(QPointF(0, 0))
                bal = round(pont.x() * dpr)
                felso = round(pont.y() * dpr)
                for y in range(felso, felso + round(ikon.height() * dpr)):
                    for x in range(bal, bal + round(ikon.width() * dpr)):
                        szin = kep.pixelColor(x, y)
                        rgb = (szin.red(), szin.green(), szin.blue())
                        if max(rgb) - min(rgb) < 35 and szin.lightness() < 110:
                            return kep
        QTest.qWait(50)
    pytest.fail("3 másodperc alatt nem rajzolódtak ki a szerkesztőfül-ikonok")


def _child(root, name: str):
    child = root.findChild(QObject, name)
    assert child is not None, f"hiányzik a kirajzolt elem: {name}"
    return child


def _pixel(kep, ikon, x: float, y: float):
    pont = ikon.mapToScene(QPointF(x, y))
    dpr = kep.devicePixelRatio()
    return kep.pixelColor(math.floor(pont.x() * dpr), math.floor(pont.y() * dpr))


def _rgb(szin: QColor) -> tuple[int, int, int]:
    return szin.red(), szin.green(), szin.blue()


@pytest.mark.parametrize("ablakmagassag", [115, 120, 125])
def test_first_five_icons_use_spec_vertical_positions(qt_app, ablakmagassag):
    """Az elvárt y a tényleges fül- és ikongeometriából számolódik."""
    with _rendered_tab_bar(qt_app, ablakmagassag) as (_, root, _, _):
        for tab_name, _ in _TABLAK:
            tab = _child(root, tab_name)
            ikon = _child(root, tab_name + "Icon")
            felso = math.floor((tab.height() - ikon.height()) / 2 - 1 + 0.5)
            assert ikon.y() == felso, (
                f"{tab_name}: y={ikon.y():g}, a középre horgonyzó képlet szerint {felso}"
            )


@pytest.mark.parametrize("ablakmagassag", [115, 120, 125])
def test_first_five_icons_use_original_stroke_color(qt_app, ablakmagassag):
    with _rendered_tab_bar(qt_app, ablakmagassag) as (_, root, _, _):
        for tab_name, elvart_vonal in _TABLAK:
            ikon = _child(root, tab_name + "Icon")
            assert QColor(ikon.property("strokeColor")).name() == elvart_vonal


@pytest.mark.parametrize("ablakmagassag", [115, 120, 125])
def test_landscape_icons_render_original_gradient_and_cloud(qt_app, ablakmagassag):
    """A három sávot és a felhőt szöveg nélküli pontokon méri."""
    with _rendered_tab_bar(qt_app, ablakmagassag) as (view, root, _, kep):
        dpr = kep.devicePixelRatio()
        for tab_name, mintak in _TAJKÉP_SZÍNEK.items():
            ikon = _child(root, tab_name + "Icon")
            hibak = []
            for nev in ("felso", "kozep", "also"):
                elvart, x, y = mintak[nev]
                kapott = _rgb(_pixel(kep, ikon, x + 0.5, y + 0.5))
                if max(abs(a - b) for a, b in zip(kapott, elvart, strict=True)) > 2:
                    hibak.append(f"{nev} átmenetsáv: {kapott}, várt {elvart}")
            felho, x, y = mintak["felho"]
            kapott_felho = _rgb(_pixel(kep, ikon, x + 0.5, y + 0.5))
            if kapott_felho != felho:
                hibak.append(f"felhő: {kapott_felho}, várt {felho}")
            elvart_felho = QColor(*felho).name()
            if QColor(ikon.property("fleckColor")).name() != elvart_felho:
                hibak.append(
                    f"felhő-tulajdonság: {ikon.property('fleckColor')}, várt {elvart_felho}"
                )
            assert not hibak, f"{tab_name}: " + "; ".join(hibak)

        cel = os.environ.get("PICASAPY_5959_SCREENSHOT")
        if cel and ablakmagassag == 120:
            sav = _child(root, "editorTabBar")
            bal_felso = sav.mapToScene(QPointF(0, 0))
            kivagas = QRect(
                round(bal_felso.x() * dpr),
                round(bal_felso.y() * dpr),
                round(sav.width() * dpr),
                round(sav.height() * dpr),
            )
            assert kep.copy(kivagas).save(cel), f"nem menthető a fülsáv képe: {cel}"
