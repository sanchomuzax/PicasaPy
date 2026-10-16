"""Valódi billentyűk és főmenüsori kattintások (#5127).

- `Ctrl+0` és `Ctrl+3` valódi `QTest.keyClick`-kel, az ablakra küldve;
- a főmenüsor négy pontja valódi bal kattintással:
  Fájl ▸ Nyomtatás, Létrehozás ▸ Movie ▸ New Movie,
  Mappa ▸ Export as HTML Page, Súgó ▸ Keyboard Shortcuts.

A hatást a felhasználó felől nézzük: nyílik-e a jobb fiók, vált-e a nézet,
megjelenik-e a párbeszéd. Parancsot nem indítunk közvetlenül (nincs
`triggered`/`activated` hívás), csak a valódi bemenetet szimuláljuk.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, Qt
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _objektum,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit

_MAPPA = "fotok"
_KEPEK = ("a_elso.jpg", "b_masodik.jpg")


def _keszits_konyvtarat(lib: Path) -> None:
    cel = lib / _MAPPA
    cel.mkdir()
    for nev in _KEPEK:
        make_jpeg(cel / nev, size=(320, 240))


@pytest.fixture
def menu_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _elokeszit(window, qt_app, controller) -> None:
    """Megjeleníti az ablakot, betölti a mappát, és kijelöli az első képet."""
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    cel = str(Path(str(controller.watchedFolders[0])) / _MAPPA)
    controller.selectFolder(cel)
    assert _varj(
        qt_app, lambda: len(controller.photos.photos) == len(_KEPEK)
    ), "a teszt mappája nem töltődött be"
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()


def _gyerek(window, nev: str):
    elem = _objektum(window, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _latszik(window, nev: str) -> bool:
    elem = _objektum(window, nev)
    return elem is not None and elem.property("visible") is True


def _zar(qt_app, objektum) -> None:
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


def _almenu_sora(menu, almenu):
    """A szülőmenü azon sora, amely az almenüt nyitja (a címe egyezik)."""
    cim = almenu.property("title")
    pending = [menu.property("contentItem")]
    while pending:
        item = pending.pop()
        if (
            "MenuItem" in item.metaObject().className()
            and item.property("text") == cim
            and not item.objectName()
        ):
            return item
        pending.extend(item.childItems())
    raise AssertionError(f"{cim!r} almenüsora nem található")


def _menupont_kattintasa(window, qt_app, nev: str):
    """Valódi kattintás egy már megnyitott menü pontján; visszaadja a pontot."""
    item = _gyerek(window, nev)
    assert item.property("visible") is True, f"{nev} nem látszik a menüben"
    assert item.property("enabled") is True, f"{nev} tiltott"
    _kattints(qt_app, item)
    return item


class TestGyorsbillentyuk:
    def test_ctrl0_valodi_billentyuvel_kinyitja_es_bezarja_a_jobb_fiokot(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        window.setProperty("activeDrawerTab", "")
        qt_app.processEvents()

        QTest.keyClick(window, Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier)
        assert _varj(
            qt_app,
            lambda: str(window.property("activeDrawerTab") or "") != "",
        ), "a Ctrl+0 nem nyitotta ki a jobb fiókot"

        QTest.keyClick(window, Qt.Key.Key_0, Qt.KeyboardModifier.ControlModifier)
        assert _varj(
            qt_app,
            lambda: str(window.property("activeDrawerTab") or "") == "",
        ), "a második Ctrl+0 nem zárta be a jobb fiókot"

    def test_ctrl3_valodi_billentyuvel_szerkesztesi_nezetbe_valt(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        assert not window.property("viewerOpen"), "a nézet már nyitva volt"

        QTest.keyClick(window, Qt.Key.Key_3, Qt.KeyboardModifier.ControlModifier)

        assert _varj(
            qt_app, lambda: bool(window.property("viewerOpen"))
        ), "a Ctrl+3 nem nyitotta meg a szerkesztési nézetet"


class TestFomenusorKattintas:
    def test_fajl_nyomtatas_valodi_kattintassal_megnyitja_a_nyomtatast(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")

        _megnyit(menu_bar, qt_app, "&File")
        _menupont_kattintasa(window, qt_app, "menuFilePrint")

        assert _varj(qt_app, lambda: _latszik(window, "printDialog")), (
            "a Fájl ▸ Print… kattintás nem nyitotta meg a nyomtatást"
        )
        _zar(qt_app, _gyerek(window, "printDialog"))

    def test_letrehozas_movie_valodi_kattintassal_megnyitja_a_filmkeszitot(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")

        letrehozas = _megnyit(menu_bar, qt_app, "&Create")
        almenu = _gyerek(window, "menuCreateMovieMenu")
        _kattints(qt_app, _almenu_sora(letrehozas, almenu))
        assert _varj(qt_app, lambda: almenu.property("opened") is True), (
            "a Létrehozás ▸ Movie almenü nem nyílt meg valódi kattintásra"
        )
        _menupont_kattintasa(window, qt_app, "menuCreateMovie")

        assert _varj(qt_app, lambda: _latszik(window, "movieDialog")), (
            "a Movie ▸ New Movie kattintás nem nyitotta meg a filmkészítőt"
        )
        _zar(qt_app, _gyerek(window, "movieDialog"))

    def test_mappa_html_export_valodi_kattintassal_megnyitja_a_webexportot(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")

        _megnyit(menu_bar, qt_app, "F&older")
        _menupont_kattintasa(window, qt_app, "menuFolderWebExport")

        assert _varj(qt_app, lambda: _latszik(window, "webExportDialog")), (
            "a Mappa ▸ Export as HTML Page kattintás nem nyitotta meg az exportot"
        )
        _zar(qt_app, _gyerek(window, "webExportDialog"))

    def test_sugo_billentyuparancsok_valodi_kattintassal_megnyitja_a_sugot(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")

        _megnyit(menu_bar, qt_app, "&Help")
        _menupont_kattintasa(window, qt_app, "menuHelpKeyboardShortcuts")

        assert _varj(qt_app, lambda: _latszik(window, "helpDialog")), (
            "a Súgó ▸ Keyboard Shortcuts kattintás nem nyitotta meg a súgót"
        )
        _zar(qt_app, _gyerek(window, "helpDialog"))
