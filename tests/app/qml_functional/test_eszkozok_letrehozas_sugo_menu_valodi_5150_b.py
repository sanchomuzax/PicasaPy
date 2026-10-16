"""Az Eszközök menü tételei VALÓDI egérkattintással (#5150, 4. rész, B).

A tételek a főmenü `&Tools` fejlécére, majd (ahol kell) az almenü sorára,
végül magára a tételre kattintva indulnak: a menüsor kezelését is a valódi
bemenet viszi. Parancsot közvetlenül nem indítunk: nincs `triggered`/
`clicked`/`activated` hívás és nincs `.emit()`.

Lefedve ebben a fájlban:
- `menuToolsFolderManager` - Mappakezelő párbeszéd nyílik;
- `menuToolsExportEarth` - Geocímke ▸ Google Earth-fájl: kijelölés nélkül
  megszólal, kijelöléssel a célmappa-párbeszédet nyitja, és `doc.kml` íródik;
- `menuToolsViewEarth` - Geocímke ▸ Megtekintés a Google Earth-ben: a
  társított program indítása hamis fogantyú, így csak a megnyitandó fájlt
  mérjük;
- `menuToolsDedup` - Kísérleti ▸ Show Duplicate Files: másodpéldány-nézet;
- `menuToolsSearchRed` … `menuToolsSearchPurple` - Kísérleti ▸ Search for…:
  a szín-token a keresőmezőbe kerül, és a keresés lefut;
- `menuToolsSaveSearch` - Kísérleti ▸ Save search results…: a találatokból
  album lesz;
- `menuToolsShowTagAsAlbum` - Kísérleti ▸ Show tag as album…: a bekérő nyílik;
- `menuToolsCompactDatabase` - Kísérleti ▸ Compact Database…: a párbeszéd nyílik.

Már lefedett tételek (ezeket itt nem ismételjük):
- `menuToolsMoveDatabase`: test_menu_talca_egyeb_valodi_5135_d.py:162
- `menuToolsImportFromPicasa`: test_menu_talca_egyeb_valodi_5135_d.py:137
- `menuToolsAdjustTimestamp`: test_adjust_timestamp_4332.py:183
- `menuToolsSearchBlack`: test_fekete_feher_kereses_menu_4689.py:69
- `menuToolsDedupManager`: test_maradek_valodi_kattintas_5127.py:319
- a Nyelv almenü tételei: test_language_menu.py:160-224

A menü-segédek a `_eszkozok_menu_5150_helpers.py`-ban élnek.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QUrl, Qt

from conftest import _build_qml_app
from picasapy.app import export_controller
from tests.app.qml_functional._eszkozok_menu_5150_helpers import (
    almenu_nyit,
    elokeszit,
    gyerek,
    keszits_konyvtarat,
    kijelol,
    latszik,
    menupont_kattintasa,
    varj,
    zar,
)
from tests.app.qml_functional._fomenu_4420_menu import _megnyit

_SZINEK = (
    ("menuToolsSearchRed", "color:red"),
    ("menuToolsSearchOrange", "color:orange"),
    ("menuToolsSearchYellow", "color:yellow"),
    ("menuToolsSearchGreen", "color:green"),
    ("menuToolsSearchBlue", "color:blue"),
    ("menuToolsSearchPurple", "color:purple"),
)


@pytest.fixture
def eszkoz_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=keszits_konyvtarat,
    )


def _geocimkez(controller, qt_app, sorok, szelesseg=47.4979, hosszusag=19.0402):
    """A kijelölés geocímkézése a TERMÉK útján (`.picasa.ini` `geotag=`)."""
    controller.setGeotagRows(list(sorok), szelesseg, hosszusag)
    qt_app.processEvents()
    assert varj(
        qt_app,
        lambda: controller.photos.photos[sorok[0]].location is not None,
    ), "a geocímke nem került a képre"


def _celmappat_valaszt(parbeszed, qt_app, mappa: Path) -> None:
    """A célmappa-párbeszéd elfogadása: a natív mappaválasztó helyettesítője.

    A tesztelt vezérlő a menütétel; a mappaválasztó az OS saját ablaka, amit
    a teszt nem nyithat meg. Ugyanezt a fogantyút használja a Google Earth
    menütétel többi tesztje is (test_earth_megtekintes_1589.py).
    """
    mappa.mkdir(parents=True, exist_ok=True)
    parbeszed.setProperty("selectedFolder", QUrl.fromLocalFile(str(mappa)))
    QMetaObject.invokeMethod(parbeszed, "accepted", Qt.ConnectionType.DirectConnection)
    parbeszed.setProperty("visible", False)
    qt_app.processEvents()


def _google_earth_menu(window, qt_app, menu_bar, nev: str) -> None:
    """Eszközök ▸ Geocímke ▸ `nev` valódi kattintással."""
    tools = _megnyit(menu_bar, qt_app, "&Tools")
    almenu_nyit(menu_bar, qt_app, tools, "&Geotag")
    menupont_kattintasa(window, qt_app, nev)


def _kiserleti(qt_app, menu_bar):
    """Eszközök ▸ Kísérleti almenü valódi kattintással megnyitva."""
    tools = _megnyit(menu_bar, qt_app, "&Tools")
    return almenu_nyit(menu_bar, qt_app, tools, "Experimental")


class TestMappakezelo:
    def test_valodi_kattintassal_megnyitja_a_mappakezelot(self, eszkoz_app, qt_app):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        _megnyit(menu_bar, qt_app, "&Tools")

        menupont_kattintasa(window, qt_app, "menuToolsFolderManager")

        assert varj(qt_app, lambda: latszik(window, "folderManagerDialog")), (
            "az Eszközök ▸ Folder Manager kattintás nem nyitotta meg a mappakezelőt"
        )
        zar(qt_app, gyerek(window, "folderManagerDialog"))


class TestGoogleEarth:
    def test_export_kijeloles_nelkul_valodi_kattintassal_megszolal(
        self, eszkoz_app, qt_app
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, [])
        menu_bar = window.property("menuBar")

        _google_earth_menu(window, qt_app, menu_bar, "menuToolsExportEarth")

        assert varj(qt_app, lambda: latszik(window, "earthResultDialog")), (
            "kijelölés nélkül a menütétel nem szólalt meg"
        )
        assert "No geotagged images to export." in str(
            gyerek(window, "earthResultText").property("text")
        )
        zar(qt_app, gyerek(window, "earthResultDialog"))

    def test_export_valodi_kattintassal_kiirja_a_doc_kml_t(
        self, eszkoz_app, qt_app, tmp_path
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        _geocimkez(controller, qt_app, [0])
        kijelol(window, qt_app, [0])
        menu_bar = window.property("menuBar")

        _google_earth_menu(window, qt_app, menu_bar, "menuToolsExportEarth")
        parbeszed = gyerek(window, "earthTargetDialog")
        assert varj(qt_app, lambda: parbeszed.property("visible") is True), (
            "az Export to Google Earth kattintás nem nyitotta meg a célmappát"
        )
        cel = tmp_path / "earth-export"
        _celmappat_valaszt(parbeszed, qt_app, cel)

        kml = cel / "doc.kml"
        assert varj(
            qt_app,
            lambda: kml.is_file() and "<Placemark" in kml.read_text(encoding="utf-8"),
        ), "a célmappába nem íródott a geocímkézett doc.kml"

    def test_megtekintes_valodi_kattintassal_megnyitja_a_doc_kml_t(
        self, eszkoz_app, qt_app, tmp_path, monkeypatch
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        _geocimkez(controller, qt_app, [0])
        kijelol(window, qt_app, [0])
        megnyitott: list[Path] = []

        def hamis_megnyitas(url):
            # a társított Google Earth indítása helyett csak feljegyezzük az utat
            megnyitott.append(Path(url.toLocalFile()))
            return True

        monkeypatch.setattr(export_controller, "_open_url", hamis_megnyitas)
        menu_bar = window.property("menuBar")

        _google_earth_menu(window, qt_app, menu_bar, "menuToolsViewEarth")
        parbeszed = gyerek(window, "earthTargetDialog")
        assert varj(qt_app, lambda: parbeszed.property("visible") is True), (
            "a View in Google Earth kattintás nem nyitotta meg a célmappát"
        )
        cel = tmp_path / "earth-megtekintes"
        _celmappat_valaszt(parbeszed, qt_app, cel)

        kml = cel / "doc.kml"
        assert varj(qt_app, lambda: bool(megnyitott)), (
            "a View in Google Earth nem nyitotta meg a kiírt fájlt"
        )
        assert megnyitott[0] == kml, "a megnyitott fájl nem a kiírt doc.kml"


class TestKiserletiAlmenu:
    def test_masolatok_mutatasa_valodi_kattintassal_masodpeldany_nezetbe_visz(
        self, eszkoz_app, qt_app
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        _kiserleti(qt_app, menu_bar)

        menupont_kattintasa(window, qt_app, "menuToolsDedup")

        assert varj(qt_app, lambda: controller.viewModeName == "dupes"), (
            "a Show Duplicate Files kattintás nem váltott másodpéldány-nézetbe"
        )

    @pytest.mark.parametrize("nev,szoveg", _SZINEK)
    def test_szin_valodi_kattintassal_a_keresomezobe_ir_es_keres(
        self, eszkoz_app, qt_app, nev, szoveg
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        kiserleti = _kiserleti(qt_app, menu_bar)
        almenu_nyit(menu_bar, qt_app, kiserleti, "Search for...")

        menupont_kattintasa(window, qt_app, nev)

        mezo = gyerek(window, "searchField")
        assert mezo.property("text") == szoveg, (
            f"a {nev} kattintás nem a keresőmezőbe írta a színtokent"
        )
        assert mezo.property("cursorPosition") == len(szoveg)
        assert varj(qt_app, lambda: controller.viewModeName == "search"), (
            f"a {nev} kattintás után nem futott le a keresés"
        )

    def test_talalatok_mentese_valodi_kattintassal_albumot_keszit(
        self, eszkoz_app, qt_app
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        controller.search("elso")
        assert varj(qt_app, lambda: controller.searchResultCount > 0), (
            "a keresés nem talált képet, a mentés nem tesztelhető"
        )
        menu_bar = window.property("menuBar")
        _kiserleti(qt_app, menu_bar)

        menupont_kattintasa(window, qt_app, "menuToolsSaveSearch")

        assert varj(qt_app, lambda: len(controller.albums) == 1), (
            "a Save search results kattintás nem hozott létre albumot"
        )

    def test_cimke_albumkent_valodi_kattintassal_megnyitja_a_bekerot(
        self, eszkoz_app, qt_app
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        _kiserleti(qt_app, menu_bar)

        menupont_kattintasa(window, qt_app, "menuToolsShowTagAsAlbum")

        assert varj(qt_app, lambda: latszik(window, "showTagAsAlbumDialog")), (
            "a Show tag as album kattintás nem nyitotta meg a bekérőt"
        )
        zar(qt_app, gyerek(window, "showTagAsAlbumDialog"))

    def test_adatbazis_tomoritese_valodi_kattintassal_megnyitja_a_parbeszedet(
        self, eszkoz_app, qt_app
    ):
        window, controller, _engine = eszkoz_app
        elokeszit(window, qt_app, controller)
        menu_bar = window.property("menuBar")
        _kiserleti(qt_app, menu_bar)

        menupont_kattintasa(window, qt_app, "menuToolsCompactDatabase")

        assert varj(qt_app, lambda: latszik(window, "compactDatabaseDialog")), (
            "a Compact Database kattintás nem nyitotta meg a tömörítést"
        )
        zar(qt_app, gyerek(window, "compactDatabaseDialog"))
