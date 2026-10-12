"""A Keresés almenü fekete-fehér tétele a valódi menüútvonalon (#4689)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

from tests.app.qml_functional._fomenu_4420_akciok import _kattints
from tests.app.qml_functional._fomenu_4420_menu import (
    _almenu,
    _megnyit,
    _menupont,
    _varj,
)


def _gyerek(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _almenu_cimre(menu_bar, szulo, cim: str):
    for index in range(int(szulo.property("count") or 0)):
        sor = _menupont(szulo, index)
        almenu = _almenu(menu_bar, szulo, sor)
        if almenu is not None and almenu.property("title") == cim:
            return sor, almenu
    pytest.fail(f"a(z) {cim!r} almenü nem található")


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_fekete_feher_valodi_kattintassal_keres(
    qml_app, qt_app, magassag_eltolas
):
    window, controller, _engine = qml_app
    eredeti_magassag = window.height()
    cel_magassag = eredeti_magassag + magassag_eltolas
    window.setHeight(cel_magassag)
    assert _varj(qt_app, lambda: window.height() == cel_magassag), (
        f"az ablak magassága nem állt be {cel_magassag} px-re"
    )

    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a főmenüsor nem található"
    tools = _megnyit(menu_bar, qt_app, "Tools")

    experimental_item, experimental = _almenu_cimre(
        menu_bar, tools, "Experimental"
    )
    _kattints(qt_app, experimental_item)
    assert _varj(qt_app, lambda: experimental.property("opened") is True), (
        "az Experimental almenü nem nyílt meg"
    )

    search_item, search_menu = _almenu_cimre(
        menu_bar, experimental, "Search for..."
    )
    _kattints(qt_app, search_item)
    assert _varj(qt_app, lambda: search_menu.property("opened") is True), (
        "a Search for... almenü nem nyílt meg"
    )

    fekete = _gyerek(window, "menuToolsSearchBlack")
    assert search_menu.property("count") == 7, (
        "a Search for... almenünek hét eleme van az eredeti szerint"
    )
    assert _menupont(search_menu, 6).objectName() == "menuToolsSearchBlack"
    _kattints(qt_app, fekete)

    mezo = _gyerek(window, "searchField")
    assert mezo.property("text") == "color:black"
    assert mezo.property("cursorPosition") == len("color:black")
    assert _varj(qt_app, lambda: controller.viewModeName == "search"), (
        "a fekete-fehér menüpont nem indította el a keresést"
    )
