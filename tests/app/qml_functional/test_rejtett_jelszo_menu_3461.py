"""#3461: a Rejtett mappák jelszava a felületről megadható.

A #1637 elkészítette a jelszó párbeszédét, a tárolást és a kaput, de a
gyűjtemény helyi menüjének „Jelszó megadása/módosítása…" tétele szürke
helyfoglaló maradt, és a Rejtett mappák fejlécének nem volt helyi menüje —
így jelszót beállítani nem lehetett, a kapu soha nem zárt.

Amit ez a fájl rögzít:

1. a Rejtett mappák fejlécére JOBB GOMBBAL kattintva megnyílik a
   gyűjtemény-menü, benne a jelszó-tétel ÉL;
2. a tételre KATTINTVA a jelszó-párbeszéd „megadás" módban nyílik;
3. a beépített csomópontot átnevezni és eltávolítani nem lehet (szürke);
4. felhasználói gyűjteményen a tétel továbbra is helyfoglaló (#424).

⚠️ A menütételre KATTINTUNK, nem a jelet emitáljuk: a néma bekötés
(elgépelt jelnév, rossz `enabled`) csak így derül ki.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from support.jpeg_factory import make_jpeg

REJTETT_FEJLEC = "hiddenCollectionHeader"


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        time.sleep(0.01)
    qt_app.processEvents()
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _elem(window, nev):
    return window.findChild(QObject, nev)


def _vizualis_elem(window, nev):
    """A lista sorainak nincs QObject-szülője, csak vizuális — a
    `findChild` nem látja őket, ezért a vizuális fán keresünk."""
    sor = [window.contentItem()]
    while sor:
        item = sor.pop()
        if item.objectName() == nev and item.isVisible():
            return item
        sor.extend(item.childItems())
    return None


def _kattint(qt_app, window, item, gomb=Qt.MouseButton.LeftButton) -> None:
    _var(qt_app, lambda: item.width() > 0 and item.height() > 0)
    pont = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    QTest.mouseClick(window, gomb, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _rejtett_mappaval(qml_app, qt_app):
    window, controller, _engine = qml_app
    lib = Path(controller.watchedFolders[0])
    for nev in ("latszo", "titkos"):
        (lib / nev).mkdir(parents=True, exist_ok=True)
        make_jpeg(lib / nev / "a.jpg", size=(80, 60))
    controller.rescan()
    _var(qt_app, lambda: controller.waitForBackgroundWorkers(0.05))
    controller.toggleFolderHidden(str(lib / "titkos"))
    controller.setShowHidden(True)
    assert _var(qt_app, lambda: _vizualis_elem(window, REJTETT_FEJLEC) is not None), (
        "a Rejtett mappák fejléce nem jelent meg"
    )
    return window, controller


def test_a_fejlec_helyi_menujeben_a_jelszo_tetel_EL(qml_app, qt_app):
    window, _ = _rejtett_mappaval(qml_app, qt_app)
    _kattint(qt_app, window, _vizualis_elem(window, REJTETT_FEJLEC), Qt.MouseButton.RightButton)
    menu = _elem(window, "collectionContextMenu")
    assert _var(qt_app, lambda: menu.property("opened") is True), (
        "jobb gombra nem nyílt meg a gyűjtemény-menü"
    )
    assert _elem(window, "collectionMenuPassword").property("enabled") is True
    for nev in ("collectionMenuRename", "collectionMenuRemove"):
        assert _elem(window, nev).property("enabled") is False, (
            f"{nev}: a beépített Rejtett mappák nem nevezhető át / távolítható el"
        )


def test_a_tetelre_KATTINTVA_a_megadas_parbeszed_nyilik(qml_app, qt_app):
    window, _ = _rejtett_mappaval(qml_app, qt_app)
    _kattint(qt_app, window, _vizualis_elem(window, REJTETT_FEJLEC), Qt.MouseButton.RightButton)
    menu = _elem(window, "collectionContextMenu")
    assert _var(qt_app, lambda: menu.property("opened") is True)
    tetel = _elem(window, "collectionMenuPassword")
    _kattint(qt_app, window, tetel)

    def _parbeszed():
        p = _elem(window, "hiddenPasswordDialog")
        return p if p is not None and p.property("visible") else None

    assert _var(qt_app, lambda: _parbeszed() is not None), (
        "a tételre kattintva nem nyílt meg a jelszó-párbeszéd"
    )
    ellenorzo = _elem(_parbeszed(), "hiddenPasswordVerify")
    assert ellenorzo.property("visible") is True, (
        "a párbeszéd nem „megadás” módban nyílt (nincs megerősítő mező)"
    )


def test_felhasznaloi_gyujtemenyen_a_tetel_szurke_marad(qml_app, qt_app):
    window, _controller, _engine = qml_app
    pane = _elem(window, "folderPane")
    assert isinstance(pane, QQuickItem)
    QMetaObject.invokeMethod(
        pane, "openCollectionContextMenu", Q_ARG("QVariant", "Nyaralás")
    )
    qt_app.processEvents()
    assert _elem(window, "collectionMenuPassword").property("enabled") is False
    for nev in ("collectionMenuRename", "collectionMenuRemove"):
        assert _elem(window, nev).property("enabled") is True

