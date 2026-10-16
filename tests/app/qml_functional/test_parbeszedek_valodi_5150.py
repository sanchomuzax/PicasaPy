"""Az „Egyéb" tételei VALÓDI egérkattintással (#5150, 10. rész, 1. fájl).

Gombok szerkesztése és az importálás forrása. Minden tétel
valódi `QTest.mouseClick`-kel indul; a hatást a párbeszéd és a vezérlő
állapotán mérjük, nem a kezelő meghívásán.

Lefedve (menü ▸ párbeszéd, tétel → mért hatás):
- `ConfigureButtonsDialog` (Eszközök ▸ Configure Buttons…): `configButtonsAddButton`,
  `configButtonsRemoveButton`, `configButtonsUpButton`, `configButtonsDownButton`,
  `configButtonsResetButton` - a munkapéldány listája változik. Az OK-t nem
  nyomjuk meg, így a beállítás nem íródik.
- `ImportSourceDialog` (Fájl ▸ Import From…): `importSourceAutoExcludeCheckBox`
  (a vezérlő `autoExclude` állapota), `importSourceExcludeAllButton` és
  `importSourceIncludeAllButton` (a forrás-jelöltek `excluded` jelzője),
  `importSourceCloseButton` (a párbeszéd bezárul).

Tiltott vezérlők (`importSourceUploadCheckBox`, `importSourceSyncStarredOnlyCheckBox`):
valódi kattintás van, de a hatás nulla - a teszt ezt méri.

A négy mozgató gomb (`configButtonsAddButton`, `configButtonsRemoveButton`,
`configButtonsUpButton`, `configButtonsDownButton`) valódi kattintással fut, és a
feliratuk kifér bennük (#5170: korábban nulla szélességűek voltak, 0 px).

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. A párbeszédek takarításához a `close` hívás szabad.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from conftest import _build_qml_app
from picasapy.app.gombsav_beallitas import ALAP_SORREND
from support.jpeg_factory import make_jpeg
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135 import (
    _menupont_kattintasa,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
    _gyerek,
    _keszits_konyvtarat,
    _klikk_ablakban,
    _latszik,
    _varj,
    _vizualis_bejaras,
    _zar,
)


@pytest.fixture
def parbeszed_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
    )


def _lista(ertek) -> list:
    """A QML-tömb Python listaként (a QVariant és a QJSValue alakját is kezeli)."""
    return list(ertek.toVariant() if hasattr(ertek, "toVariant") else ertek)


_MOZGATO_GOMBOK = (
    "configButtonsAddButton",
    "configButtonsRemoveButton",
    "configButtonsUpButton",
    "configButtonsDownButton",
)


def _felirat_kifer(window, nev: str) -> bool:
    """A `nev` gomb szélessége eléri a feliratának természetes szélességét."""
    gomb = _gyerek(window, nev)
    felirat = _gyerek(window, f"{nev}Label")
    return 0 < felirat.property("implicitWidth") <= gomb.property("width")


def _js_lista(engine, elemek: list):
    """A `elemek` JavaScript-tömbként: a QML `var` tulajdonsága ezt várja.

    Egy Python-lista `setProperty`-vel PyObject-ként érkezne, és a QML
    `indexOf` hívása elhasalna.
    """
    tomb = engine.newArray(len(elemek))
    for index, elem in enumerate(elemek):
        tomb.setProperty(index, elem)
    return tomb


def _sor(window, lista_nev: str, index: int):
    """A `lista_nev` lista `index`-edik sorának szövegeleme, ha már megjelent."""
    for elem in _vizualis_bejaras(_gyerek(window, lista_nev)):
        if elem.property("modelData") is not None and elem.property("index") == index:
            return elem
    return None


def _sorra_kattint(qt_app, window, lista_nev: str, index: int) -> None:
    """Valódi kattintás a lista `index`-edik során; megvárja, hogy a sor megjelenjen."""
    assert _varj(qt_app, lambda: _sor(window, lista_nev, index) is not None), (
        f"{lista_nev}: nincs {index}. sor"
    )
    _klikk_ablakban(qt_app, window, _sor(window, lista_nev, index))


def _gombok_megnyit(window, qt_app):
    """Eszközök ▸ Configure Buttons… valódi kattintással; visszaadja a párbeszédet."""
    menu_bar = window.property("menuBar")
    _megnyit(menu_bar, qt_app, "&Tools")
    _menupont_kattintasa(window, qt_app, "menuConfigureButtons")
    assert _varj(qt_app, lambda: _latszik(window, "configureButtonsDialog")), (
        "az Eszközök ▸ Configure Buttons nem nyitotta meg a párbeszédet"
    )
    return _gyerek(window, "configureButtonsDialog")


class TestGombSzerkeszto:
    def test_a_negy_mozgato_gomb_szelesse_legalabb_a_feliratuk(self, parbeszed_app, qt_app):
        """A Hozzáad, Eltávolít, Fel és Le gomb legalább akkora, mint a felirata (#5170)."""
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _gombok_megnyit(window, qt_app)

        assert _varj(
            qt_app, lambda: all(_felirat_kifer(window, nev) for nev in _MOZGATO_GOMBOK)
        ), "a mozgató gombok felirata nem fér ki a gombba"
        for nev in _MOZGATO_GOMBOK:
            gomb = _gyerek(window, nev)
            felirat = _gyerek(window, f"{nev}Label")
            assert _felirat_kifer(window, nev), (
                f"{nev}: a gomb {gomb.property('width')} px, "
                f"a felirat {felirat.property('implicitWidth')} px széles"
            )
        _zar(qt_app, dialog)

    def test_hozzaad_valodi_kattintassal_a_kivalasztott_gombot_a_sorba_teszi(
        self, parbeszed_app, qt_app
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _gombok_megnyit(window, qt_app)
        dialog.setProperty("jelenlegi", _js_lista(engine, ALAP_SORREND[1:]))  # előkészítés
        assert _varj(qt_app, lambda: _sor(window, "configButtonsAvailableList", 0) is not None)
        szabad = _lista(dialog.property("szabadok"))

        _sorra_kattint(qt_app, window, "configButtonsAvailableList", 0)
        _klikk_ablakban(qt_app, window, _gyerek(window, "configButtonsAddButton"))

        assert _varj(
            qt_app, lambda: len(_lista(dialog.property("jelenlegi"))) == len(ALAP_SORREND)
        ), "a Hozzáadás kattintás nem bővítette a jelenlegi gombok listáját"
        assert _lista(dialog.property("jelenlegi"))[-1] == szabad[0]
        _zar(qt_app, dialog)

    def test_eltavolit_valodi_kattintassal_kiveszi_a_kijelolt_gombot(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _gombok_megnyit(window, qt_app)
        elotte = _lista(dialog.property("jelenlegi"))

        _sorra_kattint(qt_app, window, "configButtonsCurrentList", 0)
        _klikk_ablakban(qt_app, window, _gyerek(window, "configButtonsRemoveButton"))

        assert _varj(
            qt_app, lambda: len(_lista(dialog.property("jelenlegi"))) == len(elotte) - 1
        ), "az Eltávolítás kattintás nem vette ki a kijelölt gombot"
        assert elotte[0] not in _lista(dialog.property("jelenlegi"))
        _zar(qt_app, dialog)

    def test_fel_valodi_kattintassal_egy_hellyel_feljebb_viszi(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _gombok_megnyit(window, qt_app)
        elotte = _lista(dialog.property("jelenlegi"))

        _sorra_kattint(qt_app, window, "configButtonsCurrentList", 1)
        _klikk_ablakban(qt_app, window, _gyerek(window, "configButtonsUpButton"))

        assert _varj(
            qt_app, lambda: _lista(dialog.property("jelenlegi"))[:2] == [elotte[1], elotte[0]]
        ), "a Fel kattintás nem cserélte fel a kijelölt gombot az előzővel"
        _zar(qt_app, dialog)

    def test_le_valodi_kattintassal_egy_hellyel_lejjebb_viszi(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _gombok_megnyit(window, qt_app)
        elotte = _lista(dialog.property("jelenlegi"))

        _sorra_kattint(qt_app, window, "configButtonsCurrentList", 0)
        _klikk_ablakban(qt_app, window, _gyerek(window, "configButtonsDownButton"))

        assert _varj(
            qt_app, lambda: _lista(dialog.property("jelenlegi"))[:2] == [elotte[1], elotte[0]]
        ), "a Le kattintás nem cserélte fel a kijelölt gombot a következővel"
        _zar(qt_app, dialog)

    def test_alaphelyzet_valodi_kattintassal_visszaallitja_az_alapsorrendet(
        self, parbeszed_app, qt_app
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _gombok_megnyit(window, qt_app)
        dialog.setProperty("jelenlegi", _js_lista(engine, ALAP_SORREND[1:]))  # előkészítés
        assert _lista(dialog.property("jelenlegi")) != list(ALAP_SORREND)

        _klikk_ablakban(qt_app, window, _gyerek(window, "configButtonsResetButton"))

        assert _varj(
            qt_app, lambda: _lista(dialog.property("jelenlegi")) == list(ALAP_SORREND)
        ), "az Alaphelyzet kattintás nem állította vissza az alapsorrendet"
        _zar(qt_app, dialog)


def _import_megnyit(window, qt_app):
    """Fájl ▸ Import From… valódi kattintással; visszaadja az importáló ablakot."""
    menu_bar = window.property("menuBar")
    _megnyit(menu_bar, qt_app, "&File")
    _menupont_kattintasa(window, qt_app, "menuFileImportFrom")
    assert _varj(qt_app, lambda: _latszik(window, "importSourceDialog")), (
        "a Fájl ▸ Import From… nem nyitotta meg az importálást"
    )
    return _gyerek(window, "importSourceDialog")


def _forras_jeloltjei(importer, dialog, qt_app, mappa: Path) -> None:
    """Két kép a forrásban: a jelöltek megjelenése a párbeszéd előnézetében.

    Előkészítés (nem a tesztelt tétel): a forrás-beolvasás a controlleren át megy.
    """
    fajlok = []
    for nev in ("elso.jpg", "masodik.jpg"):
        fajl = mappa / nev
        make_jpeg(fajl, size=(64, 48))
        fajlok.append(str(fajl))
    importer.scanFiles(fajlok)
    assert _varj(
        qt_app, lambda: len(_lista(dialog.property("previewItems"))) == 2
    ), "a forrás jelöltjei nem jelentek meg az előnézetben"


class TestImportForras:
    def test_a_duplikatum_jelolo_valodi_kattintassal_atallitja_a_vezerlot(
        self, parbeszed_app, qt_app
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        importer = engine.rootContext().contextProperty("importSourceController")
        elotte = bool(importer.property("autoExclude"))

        _klikk_ablakban(qt_app, dialog, _gyerek(dialog, "importSourceAutoExcludeCheckBox"))

        assert _varj(
            qt_app, lambda: bool(importer.property("autoExclude")) is not elotte
        ), "a Duplikátumok kizárása jelölő kattintása nem állította át a vezérlőt"
        _zar(qt_app, dialog)

    def test_mind_kizar_valodi_kattintassal_az_osszes_jeloltet(
        self, parbeszed_app, qt_app, tmp_path
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        importer = engine.rootContext().contextProperty("importSourceController")
        _forras_jeloltjei(importer, dialog, qt_app, tmp_path)

        _klikk_ablakban(qt_app, dialog, _gyerek(dialog, "importSourceExcludeAllButton"))

        assert _varj(
            qt_app,
            lambda: all(bool(t["excluded"]) for t in _lista(dialog.property("previewItems"))),
        ), "a Mind kizárása kattintás nem jelölte ki az összes képet"
        _zar(qt_app, dialog)

    def test_mind_bevesz_valodi_kattintassal_visszaveszi_a_kizartakat(
        self, parbeszed_app, qt_app, tmp_path
    ):
        window, controller, engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        importer = engine.rootContext().contextProperty("importSourceController")
        _forras_jeloltjei(importer, dialog, qt_app, tmp_path)
        importer.excludeAll()  # előkészítés: minden kizárva
        assert _varj(
            qt_app,
            lambda: all(bool(t["excluded"]) for t in _lista(dialog.property("previewItems"))),
        ), "a próba feltétele: minden kép kizárva"

        _klikk_ablakban(qt_app, dialog, _gyerek(dialog, "importSourceIncludeAllButton"))

        assert _varj(
            qt_app,
            lambda: not any(bool(t["excluded"]) for t in _lista(dialog.property("previewItems"))),
        ), "a Mind bevesz kattintás nem vette vissza a kizárt képeket"
        _zar(qt_app, dialog)

    def test_bezaras_valodi_kattintassal_zarja_az_importot(self, parbeszed_app, qt_app):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)

        _klikk_ablakban(qt_app, dialog, _gyerek(dialog, "importSourceCloseButton"))

        assert _varj(qt_app, lambda: dialog.property("visible") is False), (
            "a Bezárás kattintás nem zárta be az importálást"
        )

    def test_a_feltoltes_jelolo_tiltott_a_kattintas_nem_valtoztatja(
        self, parbeszed_app, qt_app
    ):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        jelolo = _gyerek(dialog, "importSourceUploadCheckBox")
        assert jelolo.property("enabled") is False, "a Feltöltés jelölőnek tiltottnak kell lennie"
        elotte = jelolo.property("checked")

        _klikk_ablakban(qt_app, dialog, jelolo)

        assert jelolo.property("checked") == elotte, "a tiltott Feltöltés jelölő átváltott"
        _zar(qt_app, dialog)

    def test_a_csillagozottak_jelolo_tiltott_a_kattintas_nem_valt(self, parbeszed_app, qt_app):
        window, controller, _engine = parbeszed_app
        _elokeszit(window, qt_app, controller)
        dialog = _import_megnyit(window, qt_app)
        # a jelölő az Options menüben él: valódi kattintással nyitjuk meg
        _klikk_ablakban(qt_app, dialog, _gyerek(dialog, "importSourceOptionsButton"))
        assert _varj(
            qt_app, lambda: _gyerek(dialog, "importSourceSyncStarredOnlyCheckBox").property("visible") is True
        ), "az Options menü nem nyitotta meg a csillagozottak jelölőt"
        jelolo = _gyerek(dialog, "importSourceSyncStarredOnlyCheckBox")
        assert jelolo.property("enabled") is False, "a csillagozottak jelölőnek tiltottnak kell lennie"
        elotte = jelolo.property("checked")

        _klikk_ablakban(qt_app, dialog, jelolo)

        assert jelolo.property("checked") == elotte, "a tiltott csillagozottak jelölő átváltott"
        _zar(qt_app, dialog)
