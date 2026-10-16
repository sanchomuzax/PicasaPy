"""Közös segédek a kollázs- és nyomtatás-tételek valódi kattintásos teszteihez (#5150).

A `kattints` valódi bal egérkattintás (`QTest.mouseClick`) az elem közepén, az
elem SAJÁT ablakában - a helyi menü tétele külön ablakban él, ezért nem a
főablakba küldünk. A `jobb_klikk` valódi jobbgomb-lenyomás a panel vászna fölött,
ez nyitja a helyi menüket. A menü tételei a QObject-fában élnek (`menu_tetel`),
nem a vizuális fában.

A vezérlő állapotát a tesztek előkészítésre hívhatják (kijelölés, pozíció), a
tesztelt műveletet viszont mindig kattintás indítja.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtTest import QTest

from support.collage_canvas_harness import _ablakban, _child, _kozeppont
from support.varakozas import hibaturo_feltetel, var_feltetelre


def varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def kattints(qt_app, elem) -> None:
    """Valódi bal egérkattintás az elem közepén, az elem saját ablakában."""
    assert elem is not None, "a kattintandó elem nem található"
    assert varj(
        qt_app, lambda: elem.isVisible() and elem.width() > 0 and elem.height() > 0
    ), f"{elem.objectName()}: nem látszik vagy nulla méretű, nem kattintható"
    assert elem.isEnabled(), f"{elem.objectName()}: le van tiltva, a kattintás nem hatna"
    kozep = elem.mapToScene(elem.boundingRect().center()).toPoint()
    QTest.mouseClick(
        elem.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kozep
    )
    qt_app.processEvents()


def jobb_klikk(qt_app, panel, pont: QPoint) -> None:
    """Valódi jobbgomb a panel nézetén: a helyi menü ettől nyílik meg."""
    view = panel.property("_view")
    QTest.mousePress(view, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, pont)
    QTest.mouseRelease(
        view, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, pont
    )
    qt_app.processEvents()


def kep_kozepe(panel, index: int) -> QPoint:
    """A `index`-edik csomópont közepe az ablak koordinátáiban."""
    return QPoint(*(round(k) for k in _kozeppont(_child(panel, f"collageNode{index}"))))


def vaszon_ures_pont(panel) -> QPoint:
    """A vászon bal-felső sarka, egy kis eltolással - nincs rajta csomópont."""
    x, y, _, _ = _ablakban(_child(panel, "collageCanvas"))
    return QPoint(round(x) + 3, round(y) + 3)


def menu_tetel(panel, nev: str):
    """Menü vagy menüpont a panel QObject-fájából (a menü ablakán kívül is megvan)."""
    elem = panel.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def menu_nyit(qt_app, panel, nev: str) -> None:
    """Megvárja, hogy a `nev` helyi menü ténylegesen megnyíljon."""
    menu = menu_tetel(panel, nev)
    assert varj(qt_app, lambda: menu.property("visible") is True), (
        f"{nev}: a jobbklikk nem nyitotta meg a helyi menüt"
    )


def utak(controller) -> list[str]:
    """A csomópontok képútvonalai, a lista sorrendjében (a rétegsorrend)."""
    return [node.path for node in controller.collageNodes.nodes]


def poziciok(controller) -> list[tuple[float, float]]:
    """A csomópontok középpontjai (lapegység), az elrendezés összevetéséhez."""
    return [(node.center_x, node.center_y) for node in controller.collageNodes.nodes]
