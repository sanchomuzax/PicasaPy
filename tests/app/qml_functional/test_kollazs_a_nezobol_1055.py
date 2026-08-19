"""A Kollázs lap a NÉZŐBŐL (szerkesztőből) is látszik (#1055).

A felhasználó a v0.8.7-en így jelentette: *„Visszamegy a mappa/feed nézetbe
az editor a Kollázs létrehozásakor."*

## A hiba

A `CollagePanel` látszása `!window.viewerOpen`-re van kötve (spec 3.1: a
kollázs a KÖNYVTÁR lapjának testvére, a néző viszont MINDKETTŐT lefedi). Az
`openCollageTab()` viszont nem hagyta el a nézőt — csak fület váltott.

A képtálca kollázs-gombja a nézőben IS ott van (`libraryFrameVisible`
tartalmazza a `viewerOpen`-t), tehát az út valóban járható: a lap
megnyílt, a kollázs elkészült, és a felhasználó közben a mappanézetet
látta. A kollázsból SEMMI nem látszott.

## Miért nem fogta meg egyetlen teszt sem

A meglévő kollázs-tesztek a könyvtárból indulnak, ahol a `viewerOpen` már
`false` — a hibás ág sosem futott le bennük. Ez a fájl szándékosan a
NÉZŐBŐL indul.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _nezot_nyit(window, qt_app):
    """A néző állapota, ahogy a `Main.qml` beállítja megnyitáskor."""
    window.setProperty("viewerOpen", True)
    window.setProperty("selectedIndexes", [0])
    qt_app.processEvents()


def _kollazst_nyit(window, qt_app):
    window.metaObject().invokeMethod(window, "openCollageTab")
    qt_app.processEvents()


def test_a_nezobol_nyitva_a_kollazs_panel_LATSZIK(qml_app, qt_app):
    """⚠️ Ez a felhasználó panasza. A többi állítás ezt bontja szét."""
    window, _controller, _engine = qml_app
    _nezot_nyit(window, qt_app)

    _kollazst_nyit(window, qt_app)

    panel = window.findChild(QObject, "collagePanel")
    assert panel is not None
    assert panel.property("visible") is True, (
        "a kollázs lapja aktív, de a panel nem látszik — a felhasználó a "
        "mappanézetben marad"
    )


def test_a_nezot_elhagyjuk(qml_app, qt_app):
    window, _controller, _engine = qml_app
    _nezot_nyit(window, qt_app)

    _kollazst_nyit(window, qt_app)

    assert window.property("viewerOpen") is False


def test_a_konyvtar_kerete_eltunik(qml_app, qt_app):
    """A kollázs a TELJES területet kapja (spec 3.1) — a könyvtár kerete nem
    maradhat ott alatta."""
    window, _controller, _engine = qml_app
    _nezot_nyit(window, qt_app)

    _kollazst_nyit(window, qt_app)

    assert window.property("libraryFrameVisible") is False


def test_a_kollazs_ful_lesz_az_aktiv(qml_app, qt_app):
    window, _controller, _engine = qml_app
    _nezot_nyit(window, qt_app)

    _kollazst_nyit(window, qt_app)

    sav = window.findChild(QObject, "documentTabStrip")
    assert sav.property("activeTabId") == window.property("collageTabId")


def test_a_konyvtarbol_nyitva_valtozatlan(qml_app, qt_app):
    """A régi út nem sérülhet: nézőn kívülről ugyanaz marad."""
    window, controller, _engine = qml_app
    window.setProperty("selectedIndexes", [0])
    qt_app.processEvents()

    _kollazst_nyit(window, qt_app)

    panel = window.findChild(QObject, "collagePanel")
    assert controller.property("collageOpen") is True
    assert panel.property("visible") is True
    assert window.property("viewerOpen") is False
