"""A Main.qml gyorsbillentyűinek és a gombsor helyi menüjének valódi bemenetű tesztjei (#5150).

A billentyűket `QTest.keyClick`-kel, a gombsor helyi menüjét valódi jobb
kattintással (`QTest.mouseClick`) éri el a teszt. Parancsot közvetlenül nem
indítunk: nincs `activated`, `triggered` vagy `.emit()` hívás. A hatást a
vezérlő állapotán, a lemezen maradt `.picasa.ini`-n, a megnyíló párbeszéden,
a súgó témáján, a törlési megerősítés adatain vagy a külső megnyitás hívásán
mérjük. A külső programot (`QDesktopServices.openUrl`) mock helyettesíti.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtTest import QTest

from picasapy.app import fileops_controller
from picasapy.render.flip import FLIP_HORIZONTAL, FLIP_VERTICAL
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _kattints, _objektum
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    MAPPA,
    app_epitese,
    elokeszit,
    keszits_konyvtarat,
    kijelol,
    szures,
)
from tests.app.qml_functional._menusor_maradek_5150_helpers import (
    billentyu,
    latszik,
    varj,
)

CTRL = Qt.KeyboardModifier.ControlModifier
SHIFT = Qt.KeyboardModifier.ShiftModifier
CTRL_SHIFT = CTRL | SHIFT
KIJELOLT = [0, 1]
KIJELOLETLEN = 2


def _duplikatumos_keszito(lib: Path) -> None:
    """A `c_kozepes.jpg` bájtról bájtra az `a_nagy.jpg` másolata: ez a másodpéldány."""
    keszits_konyvtarat(lib)
    fotok = lib / MAPPA
    shutil.copyfile(fotok / "a_nagy.jpg", fotok / "c_kozepes.jpg")


def _foto_utja(controller, sor: int) -> Path:
    foto = controller.photos.photos[sor]
    return Path(str(foto.folder_path)) / foto.name


def _elem(window, nev: str):
    elem = _objektum(window, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _gyermek(szulo, nev: str):
    elem = szulo.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a párbeszédben"
    return elem


def _nev_kattintasa(window, qt_app, nev: str) -> None:
    elem = _elem(window, nev)
    assert varj(
        qt_app, lambda: elem.property("visible") is True and elem.width() > 0
    ), f"{nev} nem látszik kattintható méretben"
    _kattints(qt_app, elem)


def _kozep(elem) -> QPoint:
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    return QPoint(round(kozep.x()), round(kozep.y()))


def _jobb_kattintas(window, qt_app, nev: str) -> None:
    elem = _elem(window, nev)
    QTest.mouseClick(
        window, Qt.MouseButton.RightButton, Qt.KeyboardModifier.NoModifier, _kozep(elem)
    )
    qt_app.processEvents()


def _mutato_ide(window, qt_app, nev: str) -> None:
    QTest.mouseMove(window, _kozep(_elem(window, nev)))
    qt_app.processEvents()


def _konyvtar_fokusz(window, qt_app) -> None:
    _elem(window, "folderListView").forceActiveFocus()
    qt_app.processEvents()


def _sugo_temaja(elem) -> str:
    """Az `elem` ősei közül az első `helpTopic`-ot deklaráló súgótéma (üres, ha nincs)."""
    while elem is not None:
        tema = elem.property("helpTopic")
        if tema:
            return str(tema)
        elem = elem.parentItem()
    return ""


def _megerositett_utvonalak(dialogus) -> list[Path]:
    """A törlési megerősítés `paths` listája (a QML JS-tömbje) útvonalként."""
    return [Path(str(p)) for p in dialogus.property("paths").toVariant()]


def _torles_megszakitasa(window, qt_app, kep: Path) -> None:
    """A törlési megerősítés `Cancel` gombja valódi kattintással; a fájl marad."""
    dialogus = _elem(window, "deleteConfirmDialog")
    _kattints(qt_app, _gyermek(dialogus, "confirmCancelButton"))
    assert varj(qt_app, lambda: not latszik(window, "deleteConfirmDialog")), (
        "a Mégse nem zárta be a törlési megerősítést"
    )
    assert kep.exists(), "a Mégse ellenére a fájl törlődött"


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


@pytest.fixture
def dupla_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path, kepeket_keszit=_duplikatumos_keszito)


class TestFiokEsKereses:
    def test_a_ctrl_0_billenti_a_jobb_fiokot(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        assert window.property("activeDrawerTab") == "", (
            "a fiók kiinduláskor nyitott: a teszt nem bizonyít"
        )

        billentyu(window, qt_app, "toggleRightDrawerShortcut", Qt.Key.Key_0, CTRL)
        assert varj(qt_app, lambda: window.property("activeDrawerTab") == "tags"), (
            "a Ctrl+0 nem nyitotta meg a jobb fiókot"
        )

        billentyu(window, qt_app, "toggleRightDrawerShortcut", Qt.Key.Key_0, CTRL)
        assert varj(qt_app, lambda: window.property("activeDrawerTab") == ""), (
            "a második Ctrl+0 nem zárta be a jobb fiókot"
        )

    def test_a_ctrl_k_a_cimkek_lapot_nyitja_a_fiokban(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        assert window.property("activeDrawerTab") == "", (
            "a fiók kiinduláskor nyitott: a teszt nem bizonyít"
        )

        billentyu(window, qt_app, "tagsPanelAltShortcut", Qt.Key.Key_K, CTRL)

        assert varj(qt_app, lambda: window.property("activeDrawerTab") == "tags"), (
            "a Ctrl+K nem nyitotta meg a Címkék lapot"
        )

    def test_az_F3_a_keresomezore_viszi_a_fokuszt(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        mezo = _elem(window, "searchField")
        _konyvtar_fokusz(window, qt_app)
        assert mezo.property("activeFocus") is False, (
            "a keresőmező már fókuszban van: a teszt nem bizonyít"
        )

        billentyu(window, qt_app, "searchF3Shortcut", Qt.Key.Key_F3)

        assert varj(qt_app, lambda: mezo.property("activeFocus") is True), (
            "az F3 nem vitte a fókuszt a keresőmezőre"
        )


class TestKijeloltKepek:
    def test_az_F4_csillagozza_a_kijelolt_kepet(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        assert not controller.photos.photos[0].star, "a kép már csillagos: nem bizonyít"

        billentyu(window, qt_app, "starToggleShortcut", Qt.Key.Key_F4)

        assert varj(qt_app, lambda: bool(controller.photos.photos[0].star)), (
            "az F4 nem csillagozta a kijelölt képet"
        )
        assert not controller.photos.photos[KIJELOLETLEN].star, (
            "a kijelöletlen kép is csillagos lett"
        )

    def test_a_ctrl_3_a_kijelolt_kepet_a_nezoben_nyitja(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        assert window.property("viewerOpen") is False, "a néző már nyitva: nem bizonyít"

        billentyu(window, qt_app, "editViewShortcut", Qt.Key.Key_3, CTRL)

        assert varj(qt_app, lambda: window.property("viewerOpen") is True), (
            "a Ctrl+3 nem nyitotta meg a nézőt"
        )

    def test_az_F11_a_nezo_teljes_kepernyojet_kapcsolja(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        billentyu(window, qt_app, "editViewShortcut", Qt.Key.Key_3, CTRL)
        assert varj(qt_app, lambda: window.property("viewerOpen") is True)
        elotte = window.property("visibility")

        billentyu(window, qt_app, "viewerFullscreenShortcut", Qt.Key.Key_F11)
        assert varj(qt_app, lambda: window.property("visibility") != elotte), (
            "az F11 nem változtatta az ablak megjelenítési módját"
        )

        billentyu(window, qt_app, "viewerFullscreenShortcut", Qt.Key.Key_F11)
        assert varj(qt_app, lambda: window.property("visibility") == elotte), (
            "a második F11 nem állította vissza az ablak módját"
        )


class TestKoteg:
    @pytest.mark.parametrize(
        ("nev", "billentyu_betu", "kulcs"),
        [
            ("batchBwShortcut", "B", "bw=1;"),
            ("batchEnhanceShortcut", "E", "enhance=1;"),
        ],
    )
    def test_a_koteg_effekt_a_kijelolt_kepekre_kerul(
        self, kep_app, qt_app, nev, billentyu_betu, kulcs
    ):
        kod = getattr(Qt.Key, f"Key_{billentyu_betu}")
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, KIJELOLT)
        assert all(kulcs not in szures(controller, sor) for sor in KIJELOLT), (
            f"a {kulcs} már a kiinduló láncban van: a teszt nem bizonyít"
        )

        billentyu(window, qt_app, nev, kod, CTRL_SHIFT)

        assert varj(
            qt_app, lambda: all(kulcs in szures(controller, sor) for sor in KIJELOLT)
        ), f"a {nev} billentyű nem írta a {kulcs} szűrőt a kijelölt képekre"
        assert kulcs not in szures(controller, KIJELOLETLEN), (
            "a kijelöletlen kép is kapta az effektet"
        )


class TestTukrozes:
    @pytest.mark.parametrize(
        ("nev", "billentyu_betu", "jelzo_neve"),
        [
            ("flipHorizontalShortcut", "H", "vizszintes"),
            ("flipVerticalShortcut", "V", "fuggoleges"),
        ],
    )
    def test_a_tukrozes_billentyu_a_kijelolt_kepeket_tukrozi(
        self, kep_app, qt_app, nev, billentyu_betu, jelzo_neve
    ):
        kod = getattr(Qt.Key, f"Key_{billentyu_betu}")
        jelzo = {"vizszintes": FLIP_HORIZONTAL, "fuggoleges": FLIP_VERTICAL}[jelzo_neve]
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, KIJELOLT)
        assert (controller.photos.photos[0].flip_flags & jelzo) == 0, (
            "a kép már tükrözött: a teszt nem bizonyít"
        )

        billentyu(window, qt_app, nev, kod, CTRL_SHIFT)

        assert varj(
            qt_app,
            lambda: (controller.photos.photos[0].flip_flags & jelzo) != 0,
        ), f"a {nev} billentyű nem tükrözte a kijelölt képet"
        assert (controller.photos.photos[KIJELOLETLEN].flip_flags & jelzo) == 0, (
            "a kijelöletlen kép is tükröződött"
        )


class TestKeresesek:
    def test_a_ctrl_f6_a_masodpeldanyokat_mutatja(self, dupla_app, qt_app):
        window, controller, _engine = dupla_app
        elokeszit(window, qt_app, controller)
        assert len(controller.photos.photos) == 3, "a teszt mappája nem a várt"

        billentyu(window, qt_app, "dupeSearchShortcut", Qt.Key.Key_F6, CTRL)

        assert varj(
            qt_app,
            lambda: sorted(f.name for f in controller.photos.photos)
            == ["a_nagy.jpg", "c_kozepes.jpg"],
        ), "a Ctrl+F6 nem a másodpéldányokat mutatta"

    def test_a_ctrl_f7_a_kijelolt_kephez_hasonlot_keres(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        assert controller.similaritySample == "", (
            "a hasonlósági minta nem üres: a teszt nem bizonyít"
        )

        billentyu(window, qt_app, "findSimilarShortcut", Qt.Key.Key_F7, CTRL)

        assert varj(qt_app, lambda: controller.similaritySample != ""), (
            "a Ctrl+F7 nem állított be hasonlósági mintát"
        )

    def test_a_ctrl_f8_torli_a_hasonlosagi_mintat(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        billentyu(window, qt_app, "findSimilarShortcut", Qt.Key.Key_F7, CTRL)
        assert varj(qt_app, lambda: controller.similaritySample != ""), (
            "a minta nem állt be: a teszt nem bizonyít"
        )

        billentyu(window, qt_app, "clearSimilarShortcut", Qt.Key.Key_F8, CTRL)

        assert varj(qt_app, lambda: controller.similaritySample == ""), (
            "a Ctrl+F8 nem törölte a hasonlósági mintát"
        )


class TestSugo:
    def test_az_F1_megnyitja_a_fosugot(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        assert not latszik(window, "helpDialog"), "a súgó már nyitva: nem bizonyít"

        billentyu(window, qt_app, "helpShortcut", Qt.Key.Key_F1)

        assert varj(qt_app, lambda: latszik(window, "helpDialog")), (
            "az F1 nem nyitotta meg a súgót"
        )

    def test_a_shift_F1_a_mutato_alatti_elem_sugojat_nyitja(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        tema = _sugo_temaja(_elem(window, "folderListView"))
        assert tema, "a mappalista alatt nincs súgótéma: a teszt nem bizonyít"
        _mutato_ide(window, qt_app, "folderListView")

        billentyu(window, qt_app, "helpContextShortcut", Qt.Key.Key_F1, SHIFT)

        assert varj(
            qt_app,
            lambda: latszik(window, "helpDialog")
            and _elem(window, "helpDialog").property("topic") == tema,
        ), f"a Shift+F1 nem a mappalista súgótémáját ({tema}) nyitotta meg"


class TestTorles:
    def test_a_ctrl_delete_a_racson_a_torlesi_megerositest_nyitja(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kep = _foto_utja(controller, 0)
        assert kep.exists(), "a teszt képe hiányzik"

        billentyu(window, qt_app, "shortcutDeleteFromDiskGrid", Qt.Key.Key_Delete, CTRL)

        assert varj(qt_app, lambda: latszik(window, "deleteConfirmDialog")), (
            "a Ctrl+Delete nem nyitotta meg a törlési megerősítést"
        )
        dialogus = _elem(window, "deleteConfirmDialog")
        assert _megerositett_utvonalak(dialogus) == [kep], (
            "a megerősítés nem a kijelölt képre vonatkozik"
        )
        _torles_megszakitasa(window, qt_app, kep)

    def test_a_ctrl_delete_a_nezoben_is_a_torlesi_megerositest_nyitja(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        billentyu(window, qt_app, "editViewShortcut", Qt.Key.Key_3, CTRL)
        assert varj(qt_app, lambda: window.property("viewerOpen") is True)
        kep = _foto_utja(controller, 0)

        billentyu(window, qt_app, "shortcutDeleteFromDiskViewer", Qt.Key.Key_Delete, CTRL)

        assert varj(qt_app, lambda: latszik(window, "deleteConfirmDialog")), (
            "a Ctrl+Delete a nézőben nem nyitotta meg a törlési megerősítést"
        )
        dialogus = _elem(window, "deleteConfirmDialog")
        assert _megerositett_utvonalak(dialogus) == [kep], (
            "a nézőben a megerősítés nem a megnyitott képre vonatkozik"
        )
        _torles_megszakitasa(window, qt_app, kep)


class TestKulsoProgram:
    def test_a_ctrl_shift_o_a_kijelolt_kepet_a_rendszer_megnyitojaval_nyitja(
        self, kep_app, qt_app, monkeypatch
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        hivasok: list[QUrl] = []

        def _rogzit(url: QUrl) -> bool:
            hivasok.append(url)
            return True

        # A külső program (alapértelmezett fájltársítás) helyben nem indítható:
        # csak azt mérjük, hogy a billentyű eljut-e a megnyitó hívásig.
        monkeypatch.setattr(fileops_controller, "_open_url", _rogzit)

        billentyu(window, qt_app, "openInEditorShortcut", Qt.Key.Key_O, CTRL_SHIFT)

        assert varj(qt_app, lambda: len(hivasok) == 1), (
            "a Ctrl+Shift+O nem hívta meg a rendszer megnyitóját"
        )
        assert Path(hivasok[0].toLocalFile()) == _foto_utja(controller, 0), (
            "a megnyitó nem a kijelölt képet kapta"
        )


class TestGombsorHelyiMenu:
    def test_a_gombsor_jobb_klikkje_a_helyi_menut_nyitja_es_a_tetel_a_gombokat_allitja(
        self, kep_app, qt_app
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        menu = _elem(window, "configureButtonsContextMenu")
        assert not latszik(window, "configureButtonsDialog"), (
            "a gombok párbeszéde már nyitva: a teszt nem bizonyít"
        )

        _jobb_kattintas(window, qt_app, "trayActionRow")

        assert varj(qt_app, lambda: menu.property("opened") is True), (
            "a gombsor jobb kattintása nem nyitotta meg a helyi menüt"
        )
        _nev_kattintasa(window, qt_app, "configureButtonsContextMenuItem")
        assert varj(qt_app, lambda: latszik(window, "configureButtonsDialog")), (
            "a helyi menü tétele nem nyitotta meg a gombok testreszabását"
        )
