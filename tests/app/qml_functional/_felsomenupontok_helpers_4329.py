"""A #4329 felsőmenütesztjeinek közös felületi segédei."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _kattints(
    qt_app, item, modifiers=Qt.KeyboardModifier.NoModifier
) -> None:
    assert item is not None, "a kattintandó felületi elem hiányzik"
    assert item.isEnabled(), f"{item.objectName()}: a művelet le van tiltva"
    assert item.width() > 0 and item.height() > 0, (
        f"{item.objectName()}: nincs kattintható mérete"
    )
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        modifiers,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _objektum(window, nev):
    gyokerek = [window]
    menu_bar = window.property("menuBar")
    if menu_bar is not None:
        gyokerek.append(menu_bar)
    for gyoker in gyokerek:
        if hasattr(gyoker, "findChild"):
            elem = gyoker.findChild(QObject, nev)
            if elem is not None:
                return elem
    return None


def _nyisd_meg_felso_menut(qt_app, window, menu_nev, elem_nev):
    menu_feliratok = {
        "file": {"&File", "&Fájl"},
        "view": {"&View", "&Nézet"},
        "picture": {"&Picture", "&Kép"},
    }[menu_nev]
    menu_bar = window.property("menuBar")
    menu = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if item.property("title") in menu_feliratok
        ),
        None,
    )
    assert menu is not None, f"a felső {menu_nev} menü nem található"
    fejléc = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if "MenuBarItem" in item.metaObject().className()
            and item.property("text") in menu_feliratok
        ),
        None,
    )
    assert fejléc is not None, f"a felső {menu_nev} menü fejléce nem található"
    _kattints(qt_app, fejléc)

    assert _varj(
        qt_app,
        lambda: menu.property("opened") is True
        and _objektum(window, elem_nev) is not None
        and _objektum(window, elem_nev).property("visible") is True,
    ), f"a {elem_nev} menüpont nem jelent meg a megnyitott menüben"
    # A menüpontot a teljes QML-fa tartja életben; a Menu.findChild a
    # QtQuick Controls popup-delegáltját adná vissza, ami a popup
    # bezárásakor megszűnik.
    item = _objektum(window, elem_nev)
    return menu_bar, menu, fejléc, item


def _magassag(window, offset: int) -> None:
    window.setHeight(window.height() + offset)


def _kijeloles(window, qt_app, rows) -> None:
    window.setProperty("selectedIndexes", rows)
    window.setProperty("selectedIndex", rows[0] if rows else -1)
    qt_app.processEvents()
