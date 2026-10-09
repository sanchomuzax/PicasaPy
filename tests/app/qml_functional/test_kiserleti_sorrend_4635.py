"""#4635 — a Kísérleti almenü tételei a mért sorrendben állnak.

Az eredeti Picasa menüsora mért (`docs/specs/picasa-menusor-csoportok.md`,
Eszközök ▸ Kísérleti): Publish via FTP… · Show Duplicate Files · Search for…
· Save search results… · Show tag as album… · Passport photo… · Delete
empty online albums… · Choose database location… · Write faces to XMP….

Nálunk a FTP és a törölt online albumok hatókörön kívül vannak. A
`Choose database location…` a mért 8. hely volt, nálunk a kilencből
az első állt — ez a teszt a kattintással megnyitott almenü TÉNYLEGES
sorrendjét méri (objectName-ek ÉS a képernyőn elfoglalt y-koordináta).

A saját tételek (Manage Duplicates, Compact Database) a csoportjukban
maradnak: a duplikátum-kezelő a Show Duplicate Files mellett, az
adatbázis-tömörítés a sor végén.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QPointF

from tests.app.qml_functional._fomenu_4420_menu import (
    _almenu,
    _felirat,
    _kattints,
    _megnyit,
    _menupont,
    _normalizal,
    _varj,
    _zarj_menuket,
)

_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)

# A mért sorrend, a nálunk is meglévő tételekre szűkítve, plusz a saját
# tételek a csoportjukban (a duplikátum-kezelő a keresés mellett).
_VART_SORREND = (
    "menuToolsDedup",
    "menuToolsDedupManager",
    "Search for...",
    "menuToolsSaveSearch",
    "menuToolsShowTagAsAlbum",
    "menuToolsPassportPhoto",
    "menuToolsMoveDatabase",
    "menuToolsWriteXmpFaces",
    "menuToolsCompactDatabase",
)


def _kulcs(sor, menu_bar) -> str:
    return sor.objectName() or _felirat(sor, menu_bar)


def _kiserleti_almenu(menu_bar, qt_app):
    tools = _megnyit(menu_bar, qt_app, "Tools")
    sor = next(
        (
            _menupont(tools, index)
            for index in range(int(tools.property("count") or 0))
            if _normalizal(_felirat(_menupont(tools, index), menu_bar))
            == "experimental"
        ),
        None,
    )
    assert sor is not None, "az Eszközök menüben nincs Kísérleti almenü"
    almenu = _almenu(menu_bar, tools, sor)
    assert almenu is not None, "a Kísérleti almenü nem található"
    if almenu.property("opened") is not True:
        _kattints(qt_app, sor)
    assert _varj(qt_app, lambda: almenu.property("opened") is True), (
        "a Kísérleti almenü nem nyílt meg kattintásra"
    )
    return almenu


def _lathato_sorrend(almenu, menu_bar) -> list[str]:
    """A tételek a képernyőn elfoglalt függőleges sorrendben."""
    sorok = []
    for index in range(int(almenu.property("count") or 0)):
        sor = _menupont(almenu, index)
        if "Separator" in sor.metaObject().className():
            continue
        y = sor.mapToScene(QPointF(0, 0)).y()
        sorok.append((y, _kulcs(sor, menu_bar)))
    return [kulcs for _y, kulcs in sorted(sorok)]


def _logikai_sorrend(almenu, menu_bar) -> list[str]:
    """A tételek a menü építési (index) sorrendjében."""
    kulcsok = []
    for index in range(int(almenu.property("count") or 0)):
        sor = _menupont(almenu, index)
        if "Separator" in sor.metaObject().className():
            continue
        kulcsok.append(_kulcs(sor, menu_bar))
    return kulcsok


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_a_kiserleti_almenu_a_mert_sorrendben_all(
    qml_app, qt_app, height_offset
):
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + height_offset)
    menu_bar = window.property("menuBar")
    try:
        almenu = _kiserleti_almenu(menu_bar, qt_app)

        assert _logikai_sorrend(almenu, menu_bar) == list(_VART_SORREND)
    finally:
        _zarj_menuket(menu_bar, qt_app)


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_a_kepernyon_is_ez_a_sorrend(qml_app, qt_app, height_offset):
    """Ugyanaz, mint fent, de a KÉPERNYŐN elfoglalt y-koordinátából: a
    menü index-sorrendje nem bizonyíték, ha a tételek fizikailag másként
    állnak."""
    window, _controller, _engine = qml_app
    window.setHeight(window.height() + height_offset)
    menu_bar = window.property("menuBar")
    try:
        almenu = _kiserleti_almenu(menu_bar, qt_app)

        assert _lathato_sorrend(almenu, menu_bar) == list(_VART_SORREND)
    finally:
        _zarj_menuket(menu_bar, qt_app)
