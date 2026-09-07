"""A #985 kollázs-bekötési tesztjeinek KÖZÖS segédei.

A #2653 két fájlra bontotta a #985 őreit — az állapotmentes bekötés-őrök
(`test_collage_panel_wiring_985_allapotmentes.py`) egyetlen, modul-szintű
alkalmazáson futnak, a felhasználói utat végigjáró tesztek
(`test_collage_panel_wiring_985.py`) továbbra is tesztenként friss appot
kapnak. A két fájl UGYANAZOKAT a segédeket használja, ezért kerültek ide;
a viselkedésük szándékosan változatlan.

## Három csapda, amit ezek a segédek kikerülnek

* a `Repeater` delegáltjait a `findChild` **nem** találja meg — a VIZUÁLIS
  fát kell bejárni (`_walk`, a #651-es mintából);
* fejnélküli (offscreen) környezetben az elrendezés **nem** fut le egyetlen
  `processEvents()` után (#918), ezért minden mérés előtt `_var()` pörgeti
  az eseményeket határidővel;
* a `visible` öröklődik a szülőtől, ezért a fülsáv regresszió-mentességét
  nem láthatósággal, hanem a tartalomterület **helyével** állítjuk.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QEvent, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a `Repeater` elemei csak itt látszanak."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _keres(window, nev: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == nev:
            return item
    return window.findChild(QObject, nev)


def _elem(window, nev: str) -> QQuickItem:
    talalt = _keres(window, nev)
    assert talalt is not None, f"a(z) {nev} nincs a kirajzolt jelenetben"
    return talalt


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    """Esemény-pörgetés, amíg a feltétel teljesül (vagy lejár az idő).

    #918: fejnélküli környezetben az elrendezés késik — egyetlen
    `processEvents()` után a méretek még a kezdeti állapotot mutatják."""
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _ablakban(item: QQuickItem) -> tuple[float, float, float, float]:
    """Az elem doboza az ABLAK koordinátarendszerében (x, y, szél., mag.)."""
    sarok = item.mapToScene(item.boundingRect().topLeft())
    return (sarok.x(), sarok.y(), item.width(), item.height())


def _kozeppont(item: QQuickItem) -> tuple[float, float]:
    pont = item.mapToScene(item.boundingRect().center())
    return (pont.x(), pont.y())


def _kattints(window, item: QQuickItem, qt_app) -> None:
    # A kattintás helyét CSAK a tényleges elrendezés után szabad kiszámolni.
    # A `_var` csak a KÖVETKEZMÉNYT várja ki; ha a koordináta már eleve rossz
    # (az elem még 0 méretű, vagy a végleges helyére sem került), a kattintás
    # a semmibe megy, és utólag semmilyen várakozás nem javítja.
    #
    # A main ubuntu-lába pontosan ezen bukott el a 0.8.0 után: a
    # fedettség-méréssel futó, lassabb CI-n a Könyvtár fülre adott kattintás
    # elkerülte a fület, és az `activeTabId` a kollázs-lapon maradt. Helyben,
    # izoláltan mind a 34 eset zöld volt — a különbség a sebesség.
    _var(qt_app, lambda: item.width() > 0 and item.height() > 0)
    kozep_x, kozep_y = _kozeppont(item)
    # a pozíció is legyen STABIL: két egymást követő mérés egyezzen
    _var(qt_app, lambda: _kozeppont(item) == (kozep_x, kozep_y))
    kozep_x, kozep_y = _kozeppont(item)
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep_x), round(kozep_y)),
    )
    qt_app.processEvents()
    QTest.qWait(30)
    qt_app.processEvents()


def _eger_le(window, pont: QPoint) -> None:
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )


def _eger_fel(window, pont: QPoint) -> None:
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )


def _eger_mozog(window, pont: QPoint) -> None:
    """Egérmozgás nyomva tartott bal gombbal (a `QTest.mouseMove` nem viszi)."""
    helyi = QPointF(pont)
    esemeny = QMouseEvent(
        QEvent.Type.MouseMove,
        helyi,
        helyi,
        QPointF(window.mapToGlobal(pont)),
        Qt.MouseButton.NoButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )
    QGuiApplication.sendEvent(window, esemeny)


def _menusor(window):
    bar = window.property("menuBar")
    assert bar is not None, "nincs menüsor"
    return bar


def _kollazs_lapot_nyit(window, qt_app, sorok=(0, 1)) -> None:
    """A VALÓDI út: a Létrehozás menü jelzését sütjük el (#936 tanulsága)."""
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", int(sorok[0]))
    qt_app.processEvents()
    bar = _menusor(window)
    bar.metaObject().invokeMethod(bar, "collageRequested")
    qt_app.processEvents()


def _tolts_fel(controller, tmp_path, qt_app, darab: int = 60) -> None:
    """A teszt-könyvtár feltöltése, hogy a feed TÉNYLEG görgethető legyen.

    A `qml_app` fixture két képet tesz be; azzal a `contentY` beállítása
    hatástalan (a `ListView` visszaszorítja 0-ra), tehát a görgetés-megőrzést
    állító teszt vakon menne át."""
    from picasapy.index import open_index, sync_tree
    from support.jpeg_factory import make_jpeg

    lib = tmp_path / "kepek"
    for i in range(darab):
        make_jpeg(lib / f"z{i:03d}.jpg", size=(48, 36))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload()
    controller.selectFolder(str(lib))
    qt_app.processEvents()


def _fulsav(window):
    return _elem(window, "documentTabStrip")


def _fulre_kattint_amig_valt(window, qt_app, objektum_nev, vart_azonosito) -> None:
    """VALÓDI kattintás a fülre, amíg a váltás tényleg meg nem történik.

    A kattintás helyét a `_kattints` már az elrendezés kivárása után
    számolja, de fejnélküli környezetben a fülsáv a kattintás pillanatában
    még átrendeződhet — ilyenkor az esemény a fül mellé esik, és a váltás
    NÉMÁN elmarad. A main ubuntu-lába pontosan ezen bukott el a 0.8.0 után
    (helyben, izoláltan mind a 34 eset zöld volt).

    Legfeljebb háromszor próbálkozunk: ha a váltás a harmadik kattintásra
    sem történik meg, az már VALÓDI hiba, és a hívó állítása buktatja el.
    """
    sav = _fulsav(window)
    for _ in range(3):
        if sav.property("activeTabId") == vart_azonosito:
            return
        _kattints(window, _elem(window, objektum_nev), qt_app)
        if _var(qt_app, lambda: sav.property("activeTabId") == vart_azonosito, 1.0):
            return


def _konyvtar_fulre(window, qt_app) -> None:
    """VALÓDI kattintás a rögzített Könyvtár fülre (nem property-írás)."""
    _fulre_kattint_amig_valt(window, qt_app, "documentTabLibrary", "library")


def _kollazs_fulre(window, qt_app) -> None:
    """VALÓDI kattintás az első projekt-fülre."""
    _kattints(window, _elem(window, "documentTab0"), qt_app)


def _lap(window) -> QQuickItem:
    return _elem(window, "collageSheet")


def _lap_arany(item: QQuickItem, lap: QQuickItem) -> tuple[float, float]:
    """Egy elem közepe a LAP arányában (0…1, 0…1) — ezt látja a felhasználó."""
    kozep_x, kozep_y = _kozeppont(item)
    lap_x, lap_y, lap_w, lap_h = _ablakban(lap)
    return ((kozep_x - lap_x) / lap_w, (kozep_y - lap_y) / lap_h)
