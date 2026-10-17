"""A Rács maradék vezérlőinek valódi bemenetű segédei (#5150, Rács-maradék).

Minden vezérlőt a NEVÉN keresünk: előbb a QObject-fában (`findChild`), majd a
vizuális fában. A delegátumoknak (bélyegkép, mappasor) nincs QObject-szülőjük,
ezért a vizuális keresés nélkül nem érnénk el őket. A kattintás valódi
`QTest.mouseClick`, a hatást a vezérlő állapotán vagy a lemezen mérjük.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    kattints,
    varj,
    vizualis_bejaras,
)


def keres(
    window,
    nev: str,
    feltetel: Callable[[QQuickItem], bool] | None = None,
):
    """A `nev` objectName-ű elem.

    Szűrés nélkül a QObject-fa találata az elsődleges. Ha ott nincs (delegátum),
    vagy szűrőt kaptunk, a látható vizuális elemek között keresünk. A `feltetel`
    például a mappasorra szűr a `folderPath` alapján."""
    talalat = window.findChild(QObject, nev)
    if talalat is not None and feltetel is None:
        return talalat
    elem = _vizualis_keres(window, nev, feltetel)
    assert elem is not None, f"{nev} nem található (látható elemként sem)"
    return elem


def _vizualis_keres(window, nev: str, feltetel):
    for elem in _ablak_elemei(window):
        if elem.objectName() != nev or not elem.isVisible():
            continue
        if feltetel is None or feltetel(elem):
            return elem
    return None


def _ablak_elemei(window):
    """A főablak és a nyitott menü-ablakok vizuális elemei."""
    ablakok = [window, *QGuiApplication.topLevelWindows()]
    for ablak in ablakok:
        if isinstance(ablak, QQuickWindow):
            yield from vizualis_bejaras(ablak.contentItem())


def kattint(window, qt_app, nev: str, gomb=Qt.MouseButton.LeftButton, feltetel=None):
    """Valódi egérkattintás a `nev` elemen. Visszaadja az elemet."""
    elem = keres(window, nev, feltetel)
    kattints(window, qt_app, elem, gomb)
    return elem


def keres_latszo(window, nev: str):
    """A `nev` látható eleme, vagy `None`, ha még nincs (a sor még nem élt)."""
    for elem in _ablak_elemei(window):
        if elem.objectName() == nev and elem.isVisible():
            return elem
    return None


def sor_pontja(elem) -> QPointF:
    """Az elem középpontja a főablak koordinátáiban."""
    return elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))


def utvonal(ertek) -> Path:
    """Útvonalat `Path`-ként ad vissza (Windowson a `str` alak eltérhet, #5155)."""
    return Path(str(ertek))


def jobbklikk_a_ponton(window, qt_app, pont: QPointF) -> None:
    """Valódi jobbklikk a főablak `pont` koordinátáján."""
    QTest.mouseClick(
        window,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        pont.toPoint(),
    )
    qt_app.processEvents()


def kep_cellaja(window, sor: int) -> QQuickItem:
    """A `sor` indexű kép bélyegképének cellája (a `thumbMouseArea` szülője)."""
    for elem in _ablak_elemei(window):
        if elem.objectName() != "thumbMouseArea" or not elem.isVisible():
            continue
        szulo = elem
        while szulo is not None and szulo.property("index") is None:
            szulo = szulo.parentItem()
        if szulo is not None and szulo.property("index") == sor:
            return szulo
    raise AssertionError(f"a {sor}. kép bélyegképe nem látszik")


def ures_pont_a_folyamon(window) -> QPointF:
    """Egy pont a képfolyam területén, amelyet egyetlen bélyegkép sem takar.

    Mérjük, nem számoljuk: a lasszó saját `MouseArea`-ját pásztázzuk, és az
    első ablakon belüli, cellával nem fedett pontot adjuk vissza. A görgetősáv
    nem számít üres pontnak (ugyanaz a szabály, mint a lasszó tesztjében)."""
    terulet = None
    for elem in _ablak_elemei(window):
        if elem.objectName() == "feedFlowLasso" and elem.isVisible():
            terulet = elem
            break
    assert terulet is not None, "a képfolyam lasszó-területe nem látszik"
    keretek = []
    for elem in _ablak_elemei(window):
        if elem.objectName() in ("thumbMouseArea", "feedScrollBar") and elem.isVisible():
            cella = elem.parentItem() if elem.objectName() == "thumbMouseArea" else elem
            if cella is None:
                continue
            sarok = cella.mapToScene(QPointF(0, 0))
            keretek.append(
                (sarok.x(), sarok.y(), sarok.x() + cella.width(), sarok.y() + cella.height())
            )
    lepes = 10
    for y in range(lepes, int(terulet.height()), lepes):
        for x in range(lepes, int(terulet.width()), lepes):
            pont = terulet.mapToScene(QPointF(x, y))
            if not (0 <= pont.x() <= window.width() and 0 <= pont.y() <= window.height()):
                continue
            if not any(bx <= pont.x() <= jx and by <= pont.y() <= jy for bx, by, jx, jy in keretek):
                return pont
    raise AssertionError("nincs cellával nem takart pont a képfolyamon")


def az_ablakban(window, elem) -> bool:
    """Az elem egészben a főablakon belül látszik."""
    bal_felso = elem.mapToScene(QPointF(0, 0))
    return (
        elem.isVisible()
        and bal_felso.x() >= 0
        and bal_felso.y() >= 0
        and bal_felso.x() + elem.width() <= window.width()
        and bal_felso.y() + elem.height() <= window.height()
    )


def varj_helyen_all(window, qt_app, elem) -> None:
    """Megvárja, hogy az elem a helyén megálljon, és az ablakon belül legyen.

    A fiókok és a párbeszédek animáltan nyílnak: nyitás közben a kattintás
    mellé eshet. Két egymás utáni azonos helyzet jelzi, hogy megállt."""
    elozo: list[tuple[float, float] | None] = [None]

    def megallt() -> bool:
        pont = elem.mapToScene(QPointF(0, 0))
        helyzet = (pont.x(), pont.y())
        allt = helyzet == elozo[0]
        elozo[0] = helyzet
        return allt and az_ablakban(window, elem)

    assert varj(qt_app, megallt), (
        f"{elem.objectName()}: a helye nem állt meg az ablakon belül"
    )
