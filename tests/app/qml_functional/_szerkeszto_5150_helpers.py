"""Közös segédek a Szerkesztő-panel valódi kattintásos teszteihez (#5150).

A kattintás mindig `QTest.mouseClick`: a teszt sosem hívja a vezérlő
`buttonClicked`/`clicked`/`activated` jelét, és nem emittál. Az állapot-
előkészítés a controlleren vagy a panel tulajdonságain át történik.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from support.varakozas import hibaturo_feltetel, var_feltetelre

#: a Szerkesztőt is tartalmazó ablak mérete (ugyanaz, mint a #3924-es próbán)
ABLAK = (1280, 1005)


def item(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def figyel(jel) -> list:
    """A panel jelzését figyeli: minden kiváltásnál egy elemet tesz a listába.

    Csak olvas: a jelet sosem emittáljuk, a kezelő lefutását figyeljük."""
    kapott: list = []
    jel.connect(lambda *ertek: kapott.append(ertek))
    return kapott


def kozeppont(elem) -> QPointF:
    """Az elem közepe a jelenetben (a `window` koordinátarendszerében)."""
    return elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))


def kattint(window, elem, qt_app) -> None:
    """Valódi bal egérkattintás az elem közepére, az ablakra küldve (`window`)."""
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nincs kattintható mérete"
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        kozeppont(elem).toPoint(),
    )
    for _ in range(5):
        qt_app.processEvents()


def sor(lista, index: int, qt_app):
    """A lenyíló lista `index`. sora, ha már felépült."""
    kifejezes = QQmlExpression(qmlContext(lista), lista, f"itemAtIndex({index})")
    talalat: list = []

    def _epul() -> bool:
        ertek, hiba = kifejezes.evaluate()
        assert not hiba, kifejezes.error()
        if ertek is not None:
            talalat.append(ertek)
        return ertek is not None

    assert varj(qt_app, _epul), f"a lista {index}. sora nem épült fel"
    return talalat[-1]


def nyitott_panel(qml_app_negyzet_kepek, qt_app):
    """Megnyitja a nézőt a Szerkesztővel. Visszaad: ablak, vezérlő, néző, panel."""
    window, controller, _engine = qml_app_negyzet_kepek
    window.setProperty("width", ABLAK[0])
    window.setProperty("height", ABLAK[1])
    for _ in range(5):
        qt_app.processEvents()
    window.setProperty("viewerOpen", True)
    viewer = item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    for _ in range(8):
        qt_app.processEvents()
    return window, controller, viewer, item(window, "viewerEditorPanel")


def szerkeszto(viewer):
    """A nézőhöz tartozó szerkesztő-vezérlő (a `editCtl` tulajdonság)."""
    return viewer.property("editCtl")


def fulre(window, qt_app, fulnev: str) -> None:
    """A Szerkesztő fülére valódi kattintással vált."""
    kattint(window, item(window, fulnev), qt_app)


def szovegeszkoz(window, qt_app) -> None:
    """A szöveg-eszköz valódi kattintással nyílik (a Gyakori javítások fülön)."""
    kattint(window, item(window, "editToolText"), qt_app)


def vorosszem_nyitva(window, qt_app, panel) -> None:
    kattint(window, item(window, "editToolRedeye"), qt_app)
    assert varj(qt_app, lambda: panel.property("redeyeActive") is True), (
        "a vörösszem eszköz nem aktiválódott"
    )


def retusalas_nyitva(window, qt_app, panel) -> None:
    kattint(window, item(window, "editToolRetouch"), qt_app)
    assert varj(qt_app, lambda: panel.property("retouchActive") is True), (
        "a retusálás eszköz nem aktiválódott"
    )


def folt_veglegesitve(szerkeszto_vezerlo) -> None:
    """Egy retusálási folt véglegesítése a controlleren (állapot-előkészítés)."""
    szerkeszto_vezerlo.beginRetouchPatch(0.5, 0.5)
    szerkeszto_vezerlo.previewRetouchSource(0.2, 0.2)
    szerkeszto_vezerlo.commitRetouchPatch(0.2, 0.2)
