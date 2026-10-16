"""A „Menüsor" tételei VALÓDI egérkattintással (#5135, 3. rész).

Minden tétel a menüsorban nyílik: a felső menü fejlécére kattintunk, majd a
menüponton (almenü esetén az almenü során is). A hatást a felhasználó felől
nézzük: megjelenik-e a párbeszéd, nyílik-e a keresési popup, indul-e a
vetítés, és a megerősítés kéri-e a törlést.

Lefedve:
- `menuViewSearchOptions` - Nézet ▸ Search Options: a keresési popup nyílik;
- `menuFolderSlideshow` - Mappa ▸ View Slideshow: a vetítés elindul;
- `menuToolsPhotoViewerSettings` - Eszközök ▸ Configure Photo Viewer…;
- `menuToolsClearGeotag` - Eszközök ▸ Geotag ▸ Clear Geotags: a törlés
  megerősítést kér (a visszavonhatatlan törlés nem fut le kérdés nélkül);
- `menuConfigureButtons` - Eszközök ▸ Configure Buttons….

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. A párbeszédek takarításához a `close` hívás szabad.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
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


def _menupont_kattintasa(window, qt_app, nev: str):
    """Valódi kattintás egy már megnyitott menü pontján; visszaadja a pontot."""
    item = _gyerek(window, nev)
    assert item.property("visible") is True, f"{nev} nem látszik a menüben"
    assert item.property("enabled") is True, f"{nev} tiltott"
    _kattints(qt_app, item)
    return item


def _almenu_megnyitasa(menu_bar, qt_app, menu, cim: str):
    """A szülőmenü `cim` almenüjét valódi kattintással nyitja meg.

    Az almenünek nincs objectName-je, ezért a `title` alapján keressük a
    menüsorban; a sorára kattintunk, amelyik az almenüt nyitja.
    """
    almenu = next(
        (
            elem
            for elem in menu_bar.findChildren(QObject)
            if elem.property("title") == cim and elem.property("opened") is not None
        ),
        None,
    )
    assert almenu is not None, f"a(z) {cim} almenü nem található"
    pending = [menu.property("contentItem")]
    while pending:
        item = pending.pop()
        if (
            "MenuItem" in item.metaObject().className()
            and item.property("text") == cim
            and not item.objectName()
        ):
            _kattints(qt_app, item)
            break
        pending.extend(item.childItems())
    else:
        raise AssertionError(f"a(z) {cim} almenü sora nem található")
    assert _varj(qt_app, lambda: almenu.property("opened") is True), (
        f"a(z) {cim} almenü nem nyílt meg valódi kattintásra"
    )


class TestNezetMenu:
    def test_search_options_valodi_kattintassal_nyitja_a_keresesi_popupot(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        popup = _gyerek(window, "searchOptionsPopup")
        assert popup.property("opened") is False, "a keresési popup már nyitva volt"
        _megnyit(menu_bar, qt_app, "&View")
        _menupont_kattintasa(window, qt_app, "menuViewSearchOptions")

        assert _varj(qt_app, lambda: popup.property("opened") is True), (
            "a Nézet ▸ Search Options kattintás nem nyitotta meg a keresési popupot"
        )
        _zar(qt_app, popup)


class TestMappaMenu:
    def test_view_slideshow_valodi_kattintassal_elinditja_a_vetitest(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        vetites = _gyerek(window, "slideshowView")
        assert vetites.property("visible") is False, "a vetítés már futott"

        _megnyit(menu_bar, qt_app, "F&older")
        _menupont_kattintasa(window, qt_app, "menuFolderSlideshow")

        assert _varj(qt_app, lambda: vetites.property("visible") is True), (
            "a Mappa ▸ View Slideshow kattintás nem indította el a vetítést"
        )
        # a vetítést a valódi Escape-billentyű állítja le (nincs közvetlen hívás)
        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert _varj(qt_app, lambda: vetites.property("visible") is False), (
            "az Escape nem állította le a vetítést"
        )


class TestEszkozokMenu:
    def test_configure_photo_viewer_valodi_kattintassal_megnyitja_a_beallitast(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")

        _megnyit(menu_bar, qt_app, "&Tools")
        _menupont_kattintasa(window, qt_app, "menuToolsPhotoViewerSettings")

        assert _varj(
            qt_app, lambda: _latszik(window, "photoViewerSettingsDialog")
        ), "az Eszközök ▸ Configure Photo Viewer kattintás nem nyitotta meg a párbeszédet"
        _zar(qt_app, _gyerek(window, "photoViewerSettingsDialog"))

    def test_configure_buttons_valodi_kattintassal_megnyitja_a_gombbeallitast(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")

        _megnyit(menu_bar, qt_app, "&Tools")
        _menupont_kattintasa(window, qt_app, "menuConfigureButtons")

        assert _varj(
            qt_app, lambda: _latszik(window, "configureButtonsDialog")
        ), "az Eszközök ▸ Configure Buttons kattintás nem nyitotta meg a párbeszédet"
        _zar(qt_app, _gyerek(window, "configureButtonsDialog"))

    def test_clear_geotags_valodi_kattintassal_megerositest_ker(
        self, menu_app, qt_app
    ):
        window, controller, _engine = menu_app
        _elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        megerosites = _objektum(window, "clearGeotagConfirm")
        assert megerosites is None or megerosites.property("visible") is not True

        menu = _megnyit(menu_bar, qt_app, "&Tools")
        _almenu_megnyitasa(menu_bar, qt_app, menu, "&Geotag")
        _menupont_kattintasa(window, qt_app, "menuToolsClearGeotag")

        assert _varj(
            qt_app, lambda: _latszik(window, "clearGeotagConfirm")
        ), "a Geocímkék törlése kattintás nem kért megerősítést"
        _zar(qt_app, _gyerek(window, "clearGeotagConfirm"))
