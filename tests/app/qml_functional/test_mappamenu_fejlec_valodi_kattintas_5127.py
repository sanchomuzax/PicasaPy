"""Valódi kattintások a mappa-menükön és az albumfejléc két gombján (#5127).

Minden elemet VALÓDI egérkattintással (`QTest.mouseClick`) érünk el, és a
hatását a felhasználó felől nézzük: megnyílik-e a párbeszéd, átíródik-e a
mező, átrendeződik-e a rács, vagy megnyílik-e a megerősítő.

- a bal oldali mappasor helyi menüje (jobbklikk): „Új gyűjtemény”,
  „Leírás szerkesztése”, „Méret szerint rendezés”;
- a mappatulajdonságok „Automatic date” gombja (és az OK, ami a törlést
  ténylegesen menti);
- a fejléc `headerSelectStarredButton` és `headerSaveEditsButton` gombja.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from picasapy.ini import parse_document, save_document
from support.jpeg_factory import make_jpeg
from support.varakozas import hibaturo_feltetel, var_feltetelre

_ABLAK_ELTOLASOK = (-5, 0, 5)
_MAPPA = "cel"
_CSILLAGOS = "c_kozepes.jpg"
#: a `size` (bájt) szerinti növekvő sorrend, a név- és dátumsorrendtől eltérően
_MERET_SZERINT = ["b_kicsi.jpg", "c_kozepes.jpg", "a_nagy.jpg"]


def _keszits_konyvtarat(lib: Path) -> None:
    cel = lib / _MAPPA
    cel.mkdir()
    make_jpeg(cel / "a_nagy.jpg", size=(640, 480))
    make_jpeg(cel / "b_kicsi.jpg", size=(40, 30))
    make_jpeg(cel / _CSILLAGOS, size=(200, 150))
    save_document(
        parse_document("").with_value(_CSILLAGOS, "star", "yes"),
        cel / ".picasa.ini",
    )


@pytest.fixture
def mappa_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_konyvtarat,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _vizualis_bejaras(item):
    """A VIZUÁLIS fa bejárása: a delegátumoknak nincs QObject-szülőjük."""
    for gyerek in item.childItems():
        yield gyerek
        yield from _vizualis_bejaras(gyerek)


def _vizualis(window, nev: str):
    for item in _vizualis_bejaras(window.contentItem()):
        if item.objectName() == nev:
            return item
    raise AssertionError(f"{nev} vizuális elem nem található")


def _kattints(window, qt_app, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    assert elem.isVisible() and elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nem látszik / nulla méretű, nem kattintható"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        gomb,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _mappa_sor(window, path: str):
    """A bal hasáb LAPOS listájának mappasora (az alapállapot).

    A fa-nézet (`hierRow:`) csak a `treeViewMode` alatt rajzolódik ki, a
    felhasználó alapbeállításán nem, ezért a lapos sor egérterületét
    (`folderRowMouse`) keressük, amelynek `folderPath`-ja a mappa."""
    for item in _vizualis_bejaras(window.contentItem()):
        if (
            item.objectName() == "folderRowMouse"
            and item.property("folderPath") == path
        ):
            return item
    raise AssertionError(f"a bal oldali mappasor nem található: {path}")


def _kijeloles(window) -> list:
    ertek = window.property("selectedIndexes")
    return list(ertek.toVariant() if hasattr(ertek, "toVariant") else ertek)


def _almenu_sora(menu, almenu):
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


def _cel_utja(controller) -> str:
    return str(Path(str(controller.watchedFolders[0])) / _MAPPA)


def _elokeszit(window, qt_app, controller, eltolas: int) -> str:
    window.setHeight(window.height() + eltolas)
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    cel = _cel_utja(controller)
    controller.selectFolder(cel)
    qt_app.processEvents()
    pane = _gyerek(window, "folderPane")
    pane.property("hierarchyController").expandAll()
    qt_app.processEvents()
    return cel


def _helyi_menu_megnyitasa(window, qt_app, cel: str):
    """Valódi jobbklikk a mappasoron; a menü megnyílását is megvárjuk."""
    sor = _mappa_sor(window, cel)
    _kattints(window, qt_app, sor, Qt.MouseButton.RightButton)
    menu = _gyerek(window, "folderContextMenu")
    assert _varj(qt_app, lambda: menu.property("visible") is True), (
        "a bal oldali mappasor jobbklikkje nem nyitotta meg a helyi menüt"
    )
    return menu


def _almenu_megnyitasa(window, qt_app, menu, almenu_nev: str) -> None:
    almenu = _gyerek(window, almenu_nev)
    _kattints(window, qt_app, _almenu_sora(menu, almenu))
    assert _varj(qt_app, lambda: almenu.property("visible") is True), (
        f"a(z) {almenu_nev} almenü nem nyílt meg a valódi kattintásra"
    )


def _mappa_tulajdonsagai(window, qt_app, controller, cel: str):
    """Megnyitja a mappa „Leírás szerkesztése” párbeszédét valódi kattintással."""
    menu = _helyi_menu_megnyitasa(window, qt_app, cel)
    _kattints(window, qt_app, _vizualis(window, "folderMenuEditDescription"))
    dialog = _gyerek(window, "folderPropertiesDialog")
    assert _varj(qt_app, lambda: dialog.property("opened") is True), (
        "a Leírás szerkesztése kattintás nem nyitotta meg a mappa-párbeszédet"
    )
    return menu, dialog


def _zar(qt_app, objektum) -> None:
    QMetaObject.invokeMethod(objektum, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestHelyiMenu:
    @pytest.mark.parametrize("eltolas", _ABLAK_ELTOLASOK)
    def test_uj_gyujtemeny_valodi_kattintassal_megnyitja_a_parbeszedet(
        self, mappa_app, qt_app, eltolas
    ):
        window, controller, _motor = mappa_app
        cel = _elokeszit(window, qt_app, controller, eltolas)
        menu = _helyi_menu_megnyitasa(window, qt_app, cel)

        _almenu_megnyitasa(window, qt_app, menu, "folderContextMenuMoveToCollection")
        _kattints(window, qt_app, _vizualis(window, "folderContextMenuNewCollection"))

        dialog = _gyerek(window, "newCollectionDialog")
        assert _varj(qt_app, lambda: dialog.property("opened") is True), (
            "az Új gyűjtemény kattintás nem nyitotta meg a párbeszédet"
        )
        _zar(qt_app, dialog)

    @pytest.mark.parametrize("eltolas", _ABLAK_ELTOLASOK)
    def test_leiras_szerkesztese_valodi_kattintassal_a_mappa_parbeszedet_nyitja(
        self, mappa_app, qt_app, eltolas
    ):
        window, controller, _motor = mappa_app
        cel = _elokeszit(window, qt_app, controller, eltolas)
        _menu, dialog = _mappa_tulajdonsagai(window, qt_app, controller, cel)

        assert dialog.property("mode") == "folder"
        assert dialog.property("folderPath") == cel
        _zar(qt_app, dialog)

    @pytest.mark.parametrize("eltolas", _ABLAK_ELTOLASOK)
    def test_meret_szerint_valodi_kattintassal_atrendezi_a_racsot(
        self, mappa_app, qt_app, eltolas
    ):
        window, controller, _motor = mappa_app
        cel = _elokeszit(window, qt_app, controller, eltolas)

        def sorrend() -> list[str]:
            return [
                foto.name for foto in controller.photos.photos
                if foto.folder_path == cel
            ]

        assert _varj(qt_app, lambda: len(sorrend()) == 3)
        assert sorrend() != _MERET_SZERINT, "a kiinduló sorrend már a méret szerinti: a teszt nem bizonyít"

        menu = _helyi_menu_megnyitasa(window, qt_app, cel)
        _almenu_megnyitasa(window, qt_app, menu, "folderMenuSortBy")
        _kattints(window, qt_app, _vizualis(window, "folderMenuSortBySize"))

        assert _varj(qt_app, lambda: sorrend() == _MERET_SZERINT), (
            f"a Méret szerint rendezés kattintás után a sorrend: {sorrend()}"
        )


class TestMappaTulajdonsagok:
    @pytest.mark.parametrize("eltolas", _ABLAK_ELTOLASOK)
    def test_automatikus_datum_valodi_kattintassal_uríti_a_mezot_es_menti(
        self, mappa_app, qt_app, eltolas
    ):
        window, controller, _motor = mappa_app
        cel = _elokeszit(window, qt_app, controller, eltolas)
        controller.setFolderDate(cel, "2020-01-02")
        assert controller.folderDateOverride(cel) == "2020-01-02"

        _menu, dialog = _mappa_tulajdonsagai(window, qt_app, controller, cel)
        mezo = _gyerek(window, "folderPropertiesDateField")
        assert mezo.property("text") != "", "a kézi dátum nem jelent meg a mezőben"

        _kattints(window, qt_app, _vizualis(window, "folderPropertiesAutomaticDate"))
        assert _varj(qt_app, lambda: mezo.property("text") == ""), (
            "az Automatic date kattintás nem ürítette ki a dátummezőt"
        )

        _kattints(window, qt_app, _vizualis(window, "folderPropertiesOkButton"))
        assert _varj(qt_app, lambda: controller.folderDateOverride(cel) == ""), (
            "az OK nem törölte a kézi dátum-felülírást"
        )
        assert _varj(qt_app, lambda: dialog.property("opened") is False)


class TestAlbumfejlecGombok:
    def test_csillagos_gomb_valodi_kattintassal_a_csillagosakat_jeloli_ki(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        _elokeszit(window, qt_app, controller, 0)
        assert _varj(qt_app, lambda: len(controller.photos.photos) == 3)
        csillagos_sorok = [
            i for i, foto in enumerate(controller.photos.photos)
            if foto.name == _CSILLAGOS
        ]
        assert len(csillagos_sorok) == 1

        gomb = _vizualis(window, "headerSelectStarredButton")
        _kattints(window, qt_app, gomb)

        assert _varj(
            qt_app, lambda: _kijeloles(window) == csillagos_sorok,
        ), f"a csillag gomb kattintás nem jelölte ki a csillagozott képet: {_kijeloles(window)}"

    def test_mentes_gomb_valodi_kattintassal_megnyitja_a_megerositot(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        _elokeszit(window, qt_app, controller, 0)
        assert _varj(qt_app, lambda: len(controller.photos.photos) == 3)
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        qt_app.processEvents()

        gomb = _vizualis(window, "headerSaveEditsButton")
        assert gomb.property("enabled") is True, "kijelölésnél a mentés gomb tiltott"
        _kattints(window, qt_app, gomb)

        # a megerősítő csak a kattintás után jön létre (SaveDialogs.ensure)
        megerosito = window.findChild(QObject, "saveConfirmDialog")
        assert _varj(
            qt_app,
            lambda: megerosito is not None and megerosito.property("opened") is True,
        ), "a Mentés gomb kattintás nem nyitotta meg a mentés-megerősítést"
        _zar(qt_app, megerosito)
