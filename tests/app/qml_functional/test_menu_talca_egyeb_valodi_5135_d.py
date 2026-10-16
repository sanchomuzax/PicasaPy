"""Az „Egyéb" táblázat tételei VALÓDI egérkattintással (#5135, 3. rész, D).

Eszközök-menüből nyíló párbeszédek: a Beállítások (Options), a Képernyővédő,
a Picasa-adatok importja és az adatbázis áthelyezése.

Lefedve:
- `optionsClearCacheButton` - a Gyorsítótár ürítése gomb megerősítést kér
  (a megerősítést nem fogadjuk el, így a gyorsítótár nem ürül);
- `screensaverSourceCheck0` - a képernyővédő forrás-jelölője: a kattintás
  a vezérlőn át átállítja a kiválasztott forrást (`screensaverSources`);
- `picasaImportCloseButton` - a Picasa-import párbeszéd Bezárás/OK gombja;
- `moveDatabaseBrowseButton` - az adatbázis-áthelyezés Tallózás gombja a
  helyválasztót nyitja (a QML-párbeszéd `visible` állapotát mérjük).

NEM lefedett, mert nem kattintható (lásd a jelentést): a Web Albums fül
jelölői (a fül `enabled: false`), és az `optionsNetworkLogBrowseButton`
(nincs `onClicked`).

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. A párbeszédek takarításához a `close` hívás szabad.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

from conftest import _build_qml_app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _kattints
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135 import (
    _almenu_megnyitasa,
    _menupont_kattintasa,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _klikk_ablakban,
    _fajlvalasztó_nyitva,
    _gyerek,
    _keszits_konyvtarat,
    _latszik,
    _valasztoablak,
    _varj,
    _zar,
)


@pytest.fixture
def eszkoz_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _vizualis_keres(window, nev: str):
    """Az elem a VIZUÁLIS fában: a Repeater-delegátumoknak nincs QObject-szülőjük."""
    verem = [window.contentItem()]
    while verem:
        elem = verem.pop()
        if elem.objectName() == nev:
            return elem
        verem.extend(elem.childItems())
    raise AssertionError(f"{nev} nem található a vizuális fában")


def _beallitasok_megnyit(window, qt_app, menu_bar):
    """Eszközök ▸ Options… valódi kattintással; visszaadja a párbeszédet."""
    _megnyit(menu_bar, qt_app, "&Tools")
    _menupont_kattintasa(window, qt_app, "menuToolsOptions")
    assert _varj(qt_app, lambda: _latszik(window, "optionsDialog")), (
        "az Eszközök ▸ Options… nem nyitotta meg a beállításokat"
    )
    return _gyerek(window, "optionsDialog")

class TestBeallitasokGyorsitotar:
    def test_gyorsitotar_uritese_valodi_kattintassal_megerositest_ker(
        self, eszkoz_app, qt_app
    ):
        window, controller, _engine = eszkoz_app
        _elokeszit(window, qt_app, controller)
        beallitasok = _beallitasok_megnyit(window, qt_app, window.property("menuBar"))

        _kattints(qt_app, _gyerek(window, "optionsClearCacheButton"))

        assert _varj(qt_app, lambda: _latszik(window, "optionsClearCacheConfirm")), (
            "a Gyorsítótár ürítése gomb nem kért megerősítést"
        )
        _zar(qt_app, _gyerek(window, "optionsClearCacheConfirm"))
        _zar(qt_app, beallitasok)


class TestKepernyovedo:
    def test_forras_jelolo_valodi_kattintassal_atallitja_a_forrast(
        self, eszkoz_app, qt_app
    ):
        window, controller, _engine = eszkoz_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&Tools")
        _menupont_kattintasa(window, qt_app, "menuToolsScreensaver")
        assert _varj(qt_app, lambda: _latszik(window, "screensaverDialog")), (
            "az Eszközök ▸ Configure Screensaver nem nyitotta meg a párbeszédet"
        )
        dialog = _gyerek(window, "screensaverDialog")
        saver = dialog.property("saverController")
        jelolo = _vizualis_keres(window, "screensaverSourceCheck0")
        kulcs = saver.property("screensaverSources")[0]["key"]

        def kivalasztott() -> bool:
            forras = next(
                s for s in saver.property("screensaverSources") if s["key"] == kulcs
            )
            return bool(forras["selected"])

        kezdeti = kivalasztott()
        _klikk_ablakban(qt_app, window, jelolo)
        assert _varj(qt_app, lambda: kivalasztott() is not kezdeti), (
            "a forrás-jelölő kattintása nem állította át a képernyővédő forrást"
        )
        # a forrás-változás újraépíti a sorokat: a jelölőt újra meg kell keresni
        jelolo = _vizualis_keres(window, "screensaverSourceCheck0")
        _klikk_ablakban(qt_app, window, jelolo)
        assert _varj(qt_app, lambda: kivalasztott() is kezdeti)
        _zar(qt_app, dialog)


class TestPicasaImport:
    def test_bezaras_valodi_kattintassal_bezarja_az_importot(
        self, eszkoz_app, qt_app
    ):
        window, controller, _engine = eszkoz_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&Tools")
        _menupont_kattintasa(window, qt_app, "menuToolsImportFromPicasa")
        assert _varj(qt_app, lambda: _latszik(window, "picasaDataImportDialog")), (
            "az Import from Picasa nem nyitotta meg a párbeszédet"
        )
        bezaras = _gyerek(window, "picasaImportCloseButton")
        assert bezaras.property("enabled") is True, (
            "a bezárás gomb tiltott: az import még fut"
        )

        _kattints(qt_app, bezaras)

        assert _varj(qt_app, lambda: not _latszik(window, "picasaDataImportDialog")), (
            "a Bezárás/OK gomb nem zárta be az importot"
        )


class TestAdatbazisAthelyezes:
    def test_tallozas_valodi_kattintassal_megnyitja_a_helyvalasztot(
        self, eszkoz_app, qt_app
    ):
        window, controller, _engine = eszkoz_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        menu = _megnyit(menu_bar, qt_app, "&Tools")
        _almenu_megnyitasa(menu_bar, qt_app, menu, "Experimental")
        _menupont_kattintasa(window, qt_app, "menuToolsMoveDatabase")
        assert _varj(qt_app, lambda: _latszik(window, "moveDatabaseDialog")), (
            "a Mozgatás adatbázis-párbeszéd nem nyílt meg"
        )
        dialog = _gyerek(window, "moveDatabaseDialog")
        assert not _fajlvalasztó_nyitva(dialog)

        _kattints(qt_app, _gyerek(window, "moveDatabaseBrowseButton"))

        assert _varj(qt_app, lambda: _fajlvalasztó_nyitva(dialog)), (
            "a Tallózás gomb nem nyitotta meg a helyválasztót"
        )
        for elem in dialog.findChildren(QObject):
            if _valasztoablak(elem):
                _zar(qt_app, elem)
        _zar(qt_app, dialog)
