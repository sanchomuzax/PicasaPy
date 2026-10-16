"""A Nézet (View) menü tételei VALÓDI egérkattintással (#5150, 2. rész).

Minden tétel a Nézet menü fejlécére (és az almenü sorára), majd magára a
tételre kattintva indul (`QTest.mouseClick`). Parancsot közvetlenül nem
indítunk: nincs `triggered`/`clicked`/`activated` hívás és nincs `.emit()`.
A hatást a vezérlő állapotán, a párbeszédek láthatóságán és az ablak
állapotán mérjük.

Már lefedett tételek valódi kattintással és hatás-ellenőrzéssel (ezeket
ebben a fájlban nem ismételjük):
- `menuViewSmallThumbnails`, `menuViewNormalThumbnails`:
  test_nezet_indexkep_pipa_4623.py:230
- `menuViewEditView`: test_felsomenupontok_nezet_4329.py:37
- `menuViewThumbnailsOnly`: test_felsomenupontok_nezet_4329.py:57
- `menuViewEditControls`: test_editor_maradek_4183.py:199
- `menuViewDarkTheme`: test_sajat_menu_jeloles_4638.py:110
- `menuViewSearchOptions`: test_menu_talca_egyeb_valodi_5135.py:144
- `menuViewSortPeopleBy*`: test_view_options_people_shortcuts_4528.py:106

A `menuViewDisplayModeRemoteDesktop` tétel nyugdíjazott (`retired: true`),
ezért nincs kezelője, és csak a tiltottságát ellenőrizzük.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._nezet_menu_5150_helpers import (
    almenu_nyit,
    elokeszit,
    nezet_app_epitese,
    tetel_kattintasa,
    varj,
)

_KIJELZESI_MODOK = (
    ("menuViewDisplayModeAuto", "auto"),
    ("menuViewDisplayModeNormal", "normal"),
    ("menuViewDisplayMode16Bit", "dither16"),
    ("menuViewDisplayModeLcd", "lcd"),
    ("menuViewDisplayModeProjector", "projector"),
    ("menuViewDisplayModeOverflow", "overflow"),
    ("menuViewDisplayModeMacGamma", "mac"),
    ("menuViewDisplayModeLinearGamma", "linear"),
    ("menuViewDisplayModeSepia", "sepia"),
    ("menuViewDisplayModeBlackWhite", "bw"),
)

_KEPFELIRATOK = (
    ("menuViewThumbCaptionNone", "none"),
    ("menuViewThumbCaptionFilename", "filename"),
    ("menuViewThumbCaptionCaption", "caption"),
    ("menuViewThumbCaptionTags", "tags"),
    ("menuViewThumbCaptionResolution", "resolution"),
)

_OLDALSO_PANELEK = (
    ("menuViewProperties", "properties"),
    ("menuViewTags", "tags"),
    ("menuViewPeople", "people"),
    ("menuViewPlaces", "places"),
)


@pytest.fixture
def nezet_app(qt_app, tmp_path):
    yield from nezet_app_epitese(qt_app, tmp_path)


def _elozo(ertek: str, lehetosegek: tuple[str, str]) -> str:
    """Olyan állapot, amely eltér a céltól, hogy a kattintás hatása látszódjon."""
    return lehetosegek[0] if ertek != lehetosegek[0] else lehetosegek[1]


class TestKonyvtarNezet:
    def test_a_konyvtar_nezet_valodi_kattintassal_visszavisz_a_konyvtarba(self, nezet_app, qt_app):
        window, controller, _engine = nezet_app
        elokeszit(window, qt_app, controller)
        tetel_kattintasa(window, qt_app, "menuViewEditView")
        assert varj(qt_app, lambda: window.property("viewerOpen") is True), (
            "a Nézet ▸ Edit View nem nyitotta meg a szerkesztőt"
        )

        tetel_kattintasa(window, qt_app, "menuViewLibraryView")

        assert varj(qt_app, lambda: window.property("viewerOpen") is False), (
            "a Nézet ▸ Könyvtárnézet kattintás nem zárta be a szerkesztőt"
        )


class TestMegjelenitesiMod:
    @pytest.mark.parametrize(("nev", "ertek"), _KIJELZESI_MODOK)
    def test_a_megjelenitesi_mod_valodi_kattintassal_beallitja_a_modot(
        self, nezet_app, qt_app, nev, ertek
    ):
        window, controller, _engine = nezet_app
        elozo = _elozo(ertek, ("normal", "auto"))
        controller.setDisplayMode(elozo)
        assert varj(qt_app, lambda: controller.displayMode == elozo)

        tetel_kattintasa(window, qt_app, nev, almenu_utvonal=("menuViewDisplayMode",))

        assert varj(qt_app, lambda: controller.displayMode == ertek), (
            f"a {nev} kattintás nem állította a megjelenítési módot: {ertek}"
        )

    def test_a_nyugdijazott_remote_desktop_tetel_tiltott(self, nezet_app, qt_app):
        window, _controller, _engine = nezet_app
        almenu_nyit(window, qt_app, ("menuViewDisplayMode",))
        tetel = _objektum(window, "menuViewDisplayModeRemoteDesktop")
        assert tetel is not None, "a Remote Desktop tétel hiányzik"
        assert tetel.property("enabled") is False, "a nyugdíjazott tétel kattintható"


class TestKepfeliratok:
    @pytest.mark.parametrize(("nev", "ertek"), _KEPFELIRATOK)
    def test_a_kepfelirat_valodi_kattintassal_valtja_a_modot(self, nezet_app, qt_app, nev, ertek):
        window, controller, _engine = nezet_app
        elozo = _elozo(ertek, ("tags", "none"))
        controller.setThumbCaptionMode(elozo)
        assert varj(qt_app, lambda: controller.thumbCaptionMode == elozo)

        tetel_kattintasa(window, qt_app, nev, almenu_utvonal=("menuViewThumbnailCaption",))

        assert varj(qt_app, lambda: controller.thumbCaptionMode == ertek), (
            f"a {nev} kattintás nem állította a kép-feliratot: {ertek}"
        )


class TestSzinkezelesEsRejtettKepek:
    def test_a_szinkezeles_valodi_kattintassal_kapcsol_ket_iranyba(self, nezet_app, qt_app):
        window, controller, _engine = nezet_app
        assert controller.colorManagement is False, "alapból ki kell legyen"

        tetel_kattintasa(window, qt_app, "menuViewColorManagement")
        assert varj(qt_app, lambda: controller.colorManagement is True), (
            "a Színkezelés első kattintása nem kapcsolta be"
        )

        tetel_kattintasa(window, qt_app, "menuViewColorManagement")
        assert varj(qt_app, lambda: controller.colorManagement is False), (
            "a Színkezelés második kattintása nem kapcsolta ki"
        )

    def test_a_rejtett_kepek_valodi_kattintassal_kapcsolnak(self, nezet_app, qt_app):
        window, controller, _engine = nezet_app
        assert controller.showHidden is False, "alapból rejtett képek nélkül indul"

        tetel_kattintasa(window, qt_app, "menuViewHidden")

        assert varj(qt_app, lambda: controller.showHidden is True), (
            "a Rejtett képek kattintás nem kapcsolta be a megjelenítést"
        )


class TestDiavetitesEsIdorend:
    def test_a_diavetites_valodi_kattintassal_elindul_es_escape_leallitja(self, nezet_app, qt_app):
        window, controller, _engine = nezet_app
        elokeszit(window, qt_app, controller)

        tetel_kattintasa(window, qt_app, "menuViewSlideshow")

        assert varj(qt_app, lambda: window.property("slideshowRunning") is True), (
            "a Nézet ▸ Diavetítés kattintás nem indította el a diavetítést"
        )
        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert varj(qt_app, lambda: window.property("slideshowRunning") is False)

    def test_az_idorend_tetel_tiltott_es_a_kattintasa_nem_nyit_semmit(self, nezet_app, qt_app):
        window, controller, _engine = nezet_app
        elokeszit(window, qt_app, controller)
        almenu_nyit(window, qt_app)
        tetel = _objektum(window, "menuViewTimeline")
        assert tetel is not None and tetel.property("visible") is True
        assert tetel.property("enabled") is False, "az Időrend nincs még kész"

        kozep = tetel.mapToScene(tetel.boundingRect().center()).toPoint()
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kozep)
        qt_app.processEvents()

        assert window.property("slideshowRunning") is False
        assert window.property("activeDrawerTab") == ""


class TestOldalsavPanelek:
    @pytest.mark.parametrize(("nev", "fulnev"), _OLDALSO_PANELEK)
    def test_a_panel_valodi_kattintassal_megnyitja_a_fület(self, nezet_app, qt_app, nev, fulnev):
        window, controller, _engine = nezet_app
        window.setProperty("activeDrawerTab", "")
        qt_app.processEvents()

        tetel_kattintasa(window, qt_app, nev)

        assert varj(qt_app, lambda: window.property("activeDrawerTab") == fulnev), (
            f"a {nev} kattintás nem nyitotta meg a(z) {fulnev} lapot"
        )
