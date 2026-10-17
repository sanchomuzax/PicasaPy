"""A névbekérő mezője (`nameInputField`) VALÓDI billentyűzettel és egérrel (#5214).

A `NameInputDialog` két példányt kap a `Main.qml`-ben (`showTagAsAlbumDialog`,
`moveToNewPersonDialog`). Itt az elsőt nyitjuk meg a valódi menüből: Eszközök ▸
Kísérleti ▸ Show tag as album (`menuToolsShowTagAsAlbum`). A hatást a
controller állapotán mérjük: az elfogadott névből album lesz, a párbeszéd
pedig bezáródik.

Lefedve:
- gépelés után az Enter elfogadja a nevet, és a név a controllerhez jut;
- az OK gomb valódi kattintása ugyanezt teszi;
- üres vagy csak szóközből álló névre az Enter nem fogadja el a nevet.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from tests.app.qml_functional._eszkozok_menu_5150_helpers import (
    MAPPA,
    almenu_nyit,
    elokeszit,
    gyerek,
    keszits_konyvtarat,
    latszik,
    menupont_kattintasa,
    varj,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional._utolso_maradek_5150_helpers import (
    gepel,
    kattint,
    kattint_elemre,
    kijelol_mindent,
    szoveges_elem,
)


def _cimkes_konyvtar(lib: Path) -> None:
    """A `fotok` mappa két képe; az elsőn van a „nyar" címke."""
    keszits_konyvtarat(lib)
    (lib / MAPPA / ".picasa.ini").write_text(
        "[a_elso.jpg]\nkeywords=nyar\n[b_masodik.jpg]\nkeywords=tenger\n",
        encoding="utf-8",
    )


@pytest.fixture
def cimke_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_cimkes_konyvtar)


def _cimke_albumot_nyit(window, qt_app, controller):
    """Megnyitja a bekérőt a valódi menüből, és visszaadja a párbeszédet."""
    elokeszit(window, qt_app, controller)
    menu_bar = window.property("menuBar")
    tools = _megnyit(menu_bar, qt_app, "&Tools")
    almenu_nyit(menu_bar, qt_app, tools, "Experimental")
    menupont_kattintasa(window, qt_app, "menuToolsShowTagAsAlbum")
    assert varj(qt_app, lambda: latszik(window, "showTagAsAlbumDialog")), (
        "a Show tag as album kattintás nem nyitotta meg a bekérőt"
    )
    return gyerek(window, "showTagAsAlbumDialog")


def _albumnevek(controller) -> list[str]:
    return [album["name"] for album in controller.albums]


def test_enterre_a_gepelt_nev_a_controllerhez_jut_es_bezarja_a_bekerot(
    cimke_app, qt_app
):
    window, controller, _engine = cimke_app
    parbeszed = _cimke_albumot_nyit(window, qt_app, controller)

    kattint(window, qt_app, "nameInputField")
    gepel(window, qt_app, "nyar")
    QTest.keyClick(window, Qt.Key.Key_Return)

    assert varj(qt_app, lambda: _albumnevek(controller) == ["nyar"]), (
        "az Enter nem adta át a beírt nevet a controllernek"
    )
    assert varj(qt_app, lambda: parbeszed.property("opened") is False), (
        "az elfogadott név után a párbeszéd nem záródott be"
    )


def test_az_ok_gomb_valodi_kattintasa_is_elfogadja_a_nevet(cimke_app, qt_app):
    window, controller, _engine = cimke_app
    _cimke_albumot_nyit(window, qt_app, controller)

    kattint(window, qt_app, "nameInputField")
    gepel(window, qt_app, "nyar")
    kattint_elemre(window, qt_app, szoveges_elem(window, "OK"))

    assert varj(qt_app, lambda: _albumnevek(controller) == ["nyar"]), (
        "az OK gomb kattintása nem adta át a beírt nevet a controllernek"
    )


def test_ures_vagy_szokoz_nev_enterre_nem_fogadodik_el(cimke_app, qt_app):
    window, controller, _engine = cimke_app
    parbeszed = _cimke_albumot_nyit(window, qt_app, controller)

    kattint(window, qt_app, "nameInputField")
    gepel(window, qt_app, "   ")
    QTest.keyClick(window, Qt.Key.Key_Return)
    qt_app.processEvents()

    assert parbeszed.property("opened") is True, (
        "szóközökből álló névre bezárult a bekérő"
    )
    assert _albumnevek(controller) == [], "szóközökből álló névből album lett"

    kijelol_mindent(window, qt_app)
    gepel(window, qt_app, "nyar")
    QTest.keyClick(window, Qt.Key.Key_Return)

    assert varj(qt_app, lambda: _albumnevek(controller) == ["nyar"]), (
        "a javított név Enterre sem fogadódott el"
    )
