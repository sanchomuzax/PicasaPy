"""A Szerkesztés menü tételei VALÓDI egérkattintással (#5150, 2. rész).

Minden tétel a főmenü fejlécére (Szerkesztés, illetve Kép ▸ Csoportos
szerkesztés), majd magára a tételre kattintva indul. A kiinduló állapotot
(képek, feliratok, effektlánc) a vezérlő adja, a tesztelt műveletet mindig
kattintás indítja. Parancsot közvetlenül nem hívunk: nincs `triggered`/
`clicked`/`activated` hívás és nincs `.emit()`.

Nincs már valódi kattintásos teszt a Szerkesztés menü itt felsorolt
tételeire. A `menuEditInvertSelection` csak invokeMethod-os tesztet kapott
(test_invert_selection_menu_1686.py), ezért itt is megírjuk.

Lefedve itt: `menuEditCut`, `menuEditCopy`, `menuEditPaste`,
`menuEditCopyEffects`, `menuEditPasteEffects`, `menuEditUndoPasteAllEffects`,
`menuEditUndoBatchEdit`, `menuEditCopyText`, `menuEditPasteText`,
`menuEditInvertSelection`.
"""

from __future__ import annotations

import configparser
from pathlib import Path

import pytest

from conftest import _build_qml_app
from picasapy.app.fileops_controller import vagolap_fajlok
from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _kattints
from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional.test_fajl_szerkesztes_menu_valodi_5150 import (
    _KEPEK,
    _elokeszit,
    _gyerek,
    _keszits_konyvtarakat,
    _kijelol,
    _mappa_ut,
    _tetel_kattintasa,
    _varj,
)
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135 import (
    _almenu_megnyitasa,
)

_CEL = "cel"
_FELIRAT = "Elso felirat"


@pytest.fixture
def szerk_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarakat,
    )


def _szerkesztes_tetelt_kattint(window, qt_app, nev: str) -> None:
    """Megnyitja a Szerkesztés menüt valódi kattintással, majd a tételre kattint."""
    menu_bar = window.property("menuBar")
    menu = _megnyit(menu_bar, qt_app, "&Edit")
    assert menu is not None, "a Szerkesztés menü nem nyílt meg"
    _tetel_kattintasa(window, qt_app, nev)


def _csoportos_szerkesztes_tetelt_kattint(window, qt_app, controller, nev: str) -> None:
    """Kép ▸ Csoportos szerkesztés ▸ `nev` valódi kattintásokkal; a háttérmunka
    végét megvárjuk, mert a kötegelt effekt az ini-fájlba ír."""
    menu_bar = window.property("menuBar")
    kep = _megnyit(menu_bar, qt_app, "&Picture")
    _almenu_megnyitasa(menu_bar, qt_app, kep, "&Batch Edit")
    wait_for_photo_op(
        controller,
        lambda: _kattints(qt_app, _gyerek(window, nev)),
        qt_app=qt_app,
    )


def _ini_ut(controller, sor: int) -> Path:
    return Path(str(controller.photos.filePathAt(sor))).parent / ".picasa.ini"


def _filters(controller, sor: int) -> str | None:
    """A `sor`-hoz tartozó kép nyers `filters=` értéke a lemezen."""
    ut = _ini_ut(controller, sor)
    if not ut.exists():
        return None
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    parser.read(ut, encoding="utf-8")
    nev = Path(str(controller.photos.filePathAt(sor))).name
    if not parser.has_section(nev):
        return None
    return parser[nev].get("filters")


def _lancot_ad(window, qt_app, controller, sor: int) -> str:
    """Előkészítés: a `sor` képére kötegelt szerkesztéssel (Warmify) láncot tesz."""
    _kijelol(window, qt_app, [sor])
    _csoportos_szerkesztes_tetelt_kattint(window, qt_app, controller, "menuBatchWarmify")
    lanc = _filters(controller, sor)
    assert lanc, "az előkészítő Warmify nem írt effektláncot"
    return lanc


def _sorok(window) -> list[int]:
    """A kijelölt sorok listája; a QML-ből JS-tömbként jöhet."""
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return list(ertek)


def _vagolap_fajlok(fileops) -> tuple[list[str], str]:
    return vagolap_fajlok(fileops._vagolap_adata())


class TestFajlVagolap:
    def test_a_masolas_valodi_kattintassal_masolas_jelzessel_teszi_fel_a_kepet(
        self, szerk_app, qt_app
    ):
        window, controller, engine = szerk_app
        _elokeszit(window, qt_app, controller)
        fileops = engine.rootContext().contextProperty("fileOpsController")
        fileops._vagolap_adat = None

        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditCopy")

        fajlok, muvelet = _vagolap_fajlok(fileops)
        assert muvelet == "copy", f"a Másolás nem „copy” jelzést tett fel: {muvelet}"
        assert [Path(f) for f in fajlok] == [Path(str(controller.photos.filePathAt(0)))], (
            f"a Másolás nem a kijelölt képet tette a vágólapra: {fajlok}"
        )

    def test_a_kivagas_valodi_kattintassal_cut_jelzessel_teszi_fel_a_kepet(
        self, szerk_app, qt_app
    ):
        window, controller, engine = szerk_app
        _elokeszit(window, qt_app, controller)
        fileops = engine.rootContext().contextProperty("fileOpsController")
        fileops._vagolap_adat = None

        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditCut")

        fajlok, muvelet = _vagolap_fajlok(fileops)
        assert muvelet == "cut", f"a Kivágás nem „cut” jelzést tett fel: {muvelet}"
        assert [Path(f) for f in fajlok] == [Path(str(controller.photos.filePathAt(0)))]

    def test_a_beillesztes_valodi_kattintassal_masolja_a_kepet_a_mappaba(
        self, szerk_app, qt_app
    ):
        window, controller, _engine = szerk_app
        _elokeszit(window, qt_app, controller)
        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditCopy")
        cel = _mappa_ut(controller, _CEL)
        cel.mkdir()
        controller.selectFolder(str(cel))
        assert _varj(
            qt_app, lambda: Path(str(controller.currentFolder)) == cel
        ), "a célmappa nem lett aktív"

        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditPaste")

        assert _varj(qt_app, lambda: (cel / _KEPEK[0]).exists()), (
            "a Beillesztés nem másolta a képet a kiválasztott mappába"
        )


class TestEffektekEsVisszavonas:
    def test_az_effektek_masolasa_valodi_kattintassal_engedelyezi_a_beillesztest(
        self, szerk_app, qt_app
    ):
        window, controller, _engine = szerk_app
        _elokeszit(window, qt_app, controller)
        _lancot_ad(window, qt_app, controller, 0)
        _kijelol(window, qt_app, [0])

        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditCopyEffects")

        assert _varj(
            qt_app,
            lambda: _gyerek(window, "menuEditPasteEffects").property("enabled") is True,
        ), "az Effektusok másolása nem tette elérhetővé a beillesztést"

    def test_az_effektek_beillesztese_valodi_kattintassal_atmasolja_a_lancot(
        self, szerk_app, qt_app
    ):
        window, controller, _engine = szerk_app
        _elokeszit(window, qt_app, controller)
        forras = _lancot_ad(window, qt_app, controller, 0)
        _kijelol(window, qt_app, [0])
        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditCopyEffects")
        _kijelol(window, qt_app, [1])

        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditPasteEffects")

        assert _varj(qt_app, lambda: _filters(controller, 1) == forras), (
            f"a beillesztés nem írta a láncot a célképre: {_filters(controller, 1)}"
        )

    def test_a_beillesztes_visszavonasa_valodi_kattintassal_visszaallitja_az_elotte_lancot(
        self, szerk_app, qt_app
    ):
        window, controller, _engine = szerk_app
        _elokeszit(window, qt_app, controller)
        _lancot_ad(window, qt_app, controller, 0)
        _kijelol(window, qt_app, [0])
        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditCopyEffects")
        _kijelol(window, qt_app, [1])
        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditPasteEffects")
        assert _varj(qt_app, lambda: _filters(controller, 1) is not None)

        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditUndoPasteAllEffects")

        assert _varj(qt_app, lambda: _filters(controller, 1) is None), (
            "a visszavonás nem állította vissza a beillesztés előtti (üres) láncot"
        )

    def test_a_kotegelt_szerkesztes_visszavonasa_valodi_kattintassal_torli_a_lancot(
        self, szerk_app, qt_app
    ):
        window, controller, _engine = szerk_app
        _elokeszit(window, qt_app, controller)
        _lancot_ad(window, qt_app, controller, 0)

        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditUndoBatchEdit")

        assert _varj(qt_app, lambda: _filters(controller, 0) is None), (
            "a kötegelt szerkesztés visszavonása nem állította vissza az üres láncot"
        )


class TestFeliratEsKijeloles:
    def test_a_felirat_masolasa_valodi_kattintassal_engedelyezi_a_felirat_beillesztest(
        self, szerk_app, qt_app
    ):
        window, controller, _engine = szerk_app
        _elokeszit(window, qt_app, controller)
        controller.setCaption(0, _FELIRAT)
        assert _varj(qt_app, lambda: controller.photos.captionAt(0) == _FELIRAT)

        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditCopyText")

        assert _varj(
            qt_app,
            lambda: _gyerek(window, "menuEditPasteText").property("enabled") is True,
        ), "a Felirat másolása nem tette elérhetővé a Felirat beillesztését"
        assert controller.captionClipboardText() == _FELIRAT, (
            "a Felirat másolása nem a feliratot tette a szöveg-vágólapra"
        )

    def test_a_felirat_beillesztese_valodi_kattintassal_atmasolja_a_feliratot(
        self, szerk_app, qt_app
    ):
        window, controller, _engine = szerk_app
        _elokeszit(window, qt_app, controller)
        controller.setCaption(0, _FELIRAT)
        assert _varj(qt_app, lambda: controller.photos.captionAt(0) == _FELIRAT)
        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditCopyText")
        _kijelol(window, qt_app, [1])

        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditPasteText")

        assert _varj(qt_app, lambda: controller.photos.captionAt(1) == _FELIRAT), (
            "a Felirat beillesztése nem írta a feliratot a másik képre"
        )

    def test_a_kijeloles_megfordítása_valodi_kattintassal_a_masik_kepet_jelöli(
        self, szerk_app, qt_app
    ):
        window, controller, _engine = szerk_app
        _elokeszit(window, qt_app, controller)
        assert _sorok(window) == [0]

        _szerkesztes_tetelt_kattint(window, qt_app, "menuEditInvertSelection")

        assert _varj(qt_app, lambda: _sorok(window) == [1]), (
            "a Kijelölés megfordítása nem a másik képet jelölte ki"
        )
