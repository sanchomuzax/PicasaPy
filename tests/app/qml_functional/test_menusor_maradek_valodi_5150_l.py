"""A Menüsor maradék tételei VALÓDI bemenettel (#5150): Fájl, Nézet, Mappa.

A menütételek valódi egérkattintással (`QTest.mouseClick`), a gyorsbillentyűk
`QTest.keyClick`-kel indulnak. Nincs `triggered`/`activated` hívás és nincs
`.emit()`. A hatást a felhasználó felől mérjük: fájl keletkezése, ablak-méret,
megnyíló panel, párbeszéd láthatósága, vezérlő-állapot.

Külső program (fájlkezelő) helyett a hívás eljutását mockoljuk: a Lemezen
megkeresés a `reveal_in_file_manager` függvényig jut el, ezt rögzítjük.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Qt

from tests.app.qml_functional._menusor_maradek_5150_helpers import (
    billentyu,
    elokeszit,
    latszik,
    nezet_app_epitese,
    tetel_kattintasa,
    varj,
)

_CTRL = Qt.KeyboardModifier.ControlModifier
_CTRL_SHIFT = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier

_SZAMGOMBOK = {"1": Qt.Key.Key_1, "2": Qt.Key.Key_2}


@pytest.fixture
def menu_app(qt_app, tmp_path):
    yield from nezet_app_epitese(qt_app, tmp_path)


class TestFajlMenu:
    def test_a_masolat_mentese_valodi_kattintassal_uj_fajlt_ir(self, menu_app, qt_app):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        forras = Path(str(controller.photos.filePathAt(0)))
        masolat = forras.parent / f"{forras.stem}-001{forras.suffix}"
        assert not masolat.exists(), "a másolat már a kiinduló állapotban megvan"
        elotte = forras.read_bytes()

        tetel_kattintasa(window, qt_app, "&File", "menuFileSaveCopy")

        assert varj(qt_app, masolat.exists), (
            "a Fájl ▸ Másolat mentése kattintás nem írt másolatot"
        )
        assert forras.read_bytes() == elotte, "a forrás képet átírta"

    def test_a_nyomtatas_gyorsbillentyuvel_megnyitja_a_nyomtatast(self, menu_app, qt_app):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)

        billentyu(window, qt_app, "shortcutPrint", Qt.Key.Key_P, _CTRL)

        assert varj(qt_app, lambda: latszik(window, "printDialog")), (
            "a Ctrl+P nem nyitotta meg a nyomtatás-párbeszédet"
        )

    def test_a_indexkep_nyomtatas_gyorsbillentyuvel_megnyitja_a_nyomtatast(self, menu_app, qt_app):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)

        billentyu(window, qt_app, "shortcutPrintContactSheet", Qt.Key.Key_P, _CTRL_SHIFT)

        assert varj(qt_app, lambda: latszik(window, "printDialog")), (
            "a Ctrl+Shift+P nem nyitotta meg az indexkép-nyomtatást"
        )

    def test_a_lemezen_megkeresese_gyorsbillentyuvel_a_kepet_mutatja(
        self, menu_app, qt_app, monkeypatch
    ):
        import picasapy.app.fileops_controller as fileops_modul

        mutatott: list[Path] = []
        monkeypatch.setattr(
            fileops_modul,
            "reveal_in_file_manager",
            lambda path: mutatott.append(Path(path)),
        )
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        kep = Path(str(controller.photos.filePathAt(0)))

        billentyu(window, qt_app, "shortcutLocateOnDisk", Qt.Key.Key_Return, _CTRL)

        assert varj(qt_app, lambda: kep in mutatott), (
            f"a Ctrl+Enter nem a kijelölt képet adta a fájlkezelőnek: {mutatott}"
        )

    def test_a_torles_gyorsbillentyuvel_megerositest_ker(self, menu_app, qt_app):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)

        billentyu(window, qt_app, "shortcutDeleteFromDisk", Qt.Key.Key_Delete)

        assert varj(qt_app, lambda: latszik(window, "deleteConfirmDialog")), (
            "a Delete nem nyitotta meg a lemezről törlés megerősítését"
        )


class TestNezetKepmeret:
    @pytest.mark.parametrize(
        ("nev", "cel", "kiindulo"),
        [
            ("menuViewSmallThumbnails", 96, 144),
            ("menuViewNormalThumbnails", 144, 96),
        ],
    )
    def test_a_kepmeret_valodi_kattintassal_allitja_a_meretet(
        self, menu_app, qt_app, nev, cel, kiindulo
    ):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        window.setProperty("thumbSize", kiindulo)
        assert varj(qt_app, lambda: window.property("thumbSize") == kiindulo)

        tetel_kattintasa(window, qt_app, "&View", nev)

        assert varj(qt_app, lambda: window.property("thumbSize") == cel), (
            f"a {nev} kattintás nem állította a képméretet: {cel}"
        )

    @pytest.mark.parametrize(
        ("nev", "gomb", "cel", "kiindulo"),
        [
            ("shortcutSmallThumbnails", "1", 96, 144),
            ("shortcutNormalThumbnails", "2", 144, 96),
        ],
    )
    def test_a_kepmeret_gyorsbillentyuvel_allitja_a_meretet(
        self, menu_app, qt_app, nev, gomb, cel, kiindulo
    ):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        window.setProperty("thumbSize", kiindulo)
        assert varj(qt_app, lambda: window.property("thumbSize") == kiindulo)

        billentyu(window, qt_app, nev, _SZAMGOMBOK[gomb], _CTRL)

        assert varj(qt_app, lambda: window.property("thumbSize") == cel), (
            f"a {nev} billentyű nem állította a képméretet: {cel}"
        )


class TestNezetPanelek:
    @pytest.mark.parametrize(
        ("nev", "fulnev"),
        [
            ("menuViewProperties", "properties"),
            ("menuViewTags", "tags"),
            ("menuViewPeople", "people"),
            ("menuViewPlaces", "places"),
        ],
    )
    def test_a_panel_valodi_kattintassal_megnyitja_a_fület(self, menu_app, qt_app, nev, fulnev):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        window.setProperty("activeDrawerTab", "")
        qt_app.processEvents()

        tetel_kattintasa(window, qt_app, "&View", nev)

        assert varj(qt_app, lambda: window.property("activeDrawerTab") == fulnev), (
            f"a {nev} kattintás nem nyitotta meg a(z) {fulnev} lapot"
        )


class TestNezetMegjelenitesiMod:
    @pytest.mark.parametrize(
        ("nev", "ertek"),
        [
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
        ],
    )
    def test_a_megjelenitesi_mod_valodi_kattintassal_beallitja_a_modot(
        self, menu_app, qt_app, nev, ertek
    ):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        elozo = "auto" if ertek == "normal" else "normal"
        controller.setDisplayMode(elozo)
        assert varj(qt_app, lambda: controller.displayMode == elozo)

        tetel_kattintasa(
            window, qt_app, "&View", nev, almenu_utvonal=("menuViewDisplayMode",)
        )

        assert varj(qt_app, lambda: controller.displayMode == ertek), (
            f"a {nev} kattintás nem állította a megjelenítési módot: {ertek}"
        )


class TestNezetKepfelirat:
    @pytest.mark.parametrize(
        ("nev", "ertek"),
        [
            ("menuViewThumbCaptionNone", "none"),
            ("menuViewThumbCaptionFilename", "filename"),
            ("menuViewThumbCaptionCaption", "caption"),
            ("menuViewThumbCaptionTags", "tags"),
            ("menuViewThumbCaptionResolution", "resolution"),
        ],
    )
    def test_a_kepfelirat_valodi_kattintassal_valtja_a_modot(self, menu_app, qt_app, nev, ertek):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        elozo = "tags" if ertek != "tags" else "none"
        controller.setThumbCaptionMode(elozo)
        assert varj(qt_app, lambda: controller.thumbCaptionMode == elozo)

        tetel_kattintasa(
            window, qt_app, "&View", nev, almenu_utvonal=("menuViewThumbnailCaption",)
        )

        assert varj(qt_app, lambda: controller.thumbCaptionMode == ertek), (
            f"a {nev} kattintás nem állította a kép-feliratot: {ertek}"
        )


class TestNezetMappanezet:
    @pytest.fixture(autouse=True)
    def _rendszermappak(self, tmp_path, monkeypatch):
        """A rendszermappa-gyökerek (Képek, Dokumentumok, Asztal) a futtató gép
        mappáitól függenek: a CI-gépen nincsenek, és a program akkor helyesen a
        Sajátgépre esik vissza. Ezért a teszt saját mappákat ad
        (a test_nezet_menu_valodi_5150_b mintája)."""
        from picasapy.app import folder_hierarchy_controller as fhc

        utak = {}
        for kulcs, mappanev in (("mypics", "Kepek"), ("mydocs", "Iratok"), ("desktop", "Asztal")):
            mappa = tmp_path / "rendszer" / mappanev
            mappa.mkdir(parents=True, exist_ok=True)
            utak[kulcs] = str(mappa)
        monkeypatch.setattr(fhc, "_rendszermappa", lambda kulcs: utak.get(kulcs, ""))

    @pytest.mark.parametrize(
        ("nev", "token"),
        [
            ("menuViewRootMyComputer", "all"),
            ("menuViewRootMyPictures", "mypics"),
            ("menuViewRootMyDocuments", "mydocs"),
            ("menuViewRootDesktop", "desktop"),
        ],
    )
    def test_a_gyoker_valodi_kattintassal_atallitja_a_gyokeret(self, menu_app, qt_app, nev, token):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        allapot = window.property("menuBar").property("folderViewCtl")
        elozo = "all" if token != "all" else "desktop"
        allapot.setViewRoot(elozo)
        assert varj(qt_app, lambda: allapot.property("viewRoot") == elozo)

        tetel_kattintasa(window, qt_app, "&View", nev, almenu_utvonal=("menuViewFolderView",))

        assert varj(qt_app, lambda: allapot.property("viewRoot") == token), (
            f"a {nev} kattintás nem állította a fanézet gyökerét: {token}"
        )

    @pytest.mark.parametrize(
        ("nev", "token"),
        [
            ("menuViewShortcutMyComputer", "all"),
            ("menuViewShortcutMyPictures", "mypics"),
            ("menuViewShortcutMyDocuments", "mydocs"),
            ("menuViewShortcutDesktop", "desktop"),
        ],
    )
    def test_a_gyorsgyoker_valodi_kattintassal_atallitja_a_gyokeret(
        self, menu_app, qt_app, nev, token
    ):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        allapot = window.property("menuBar").property("folderViewCtl")
        elozo = "all" if token != "all" else "desktop"
        allapot.setViewRoot(elozo)
        assert varj(qt_app, lambda: allapot.property("viewRoot") == elozo)

        tetel_kattintasa(
            window,
            qt_app,
            "&View",
            nev,
            almenu_utvonal=("menuViewFolderView", "menuViewFolderViewShortcuts"),
        )

        assert varj(qt_app, lambda: allapot.property("viewRoot") == token), (
            f"a {nev} kattintás nem állította a fanézet gyökerét: {token}"
        )

    @pytest.mark.parametrize(
        ("nev", "ertek"),
        [
            ("menuViewSortByDate", "date"),
            ("menuViewSortByRecent", "changed"),
            ("menuViewSortBySize", "size"),
            ("menuViewSortByName", "name"),
        ],
    )
    def test_a_bal_panel_rendezese_valodi_kattintassal_allitja_a_rendezest(
        self, menu_app, qt_app, nev, ertek
    ):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        elozo = "name" if ertek != "name" else "date"
        controller.setPaneSort(elozo)
        assert varj(qt_app, lambda: controller.paneSort == elozo)

        tetel_kattintasa(window, qt_app, "&View", nev, almenu_utvonal=("menuViewFolderView",))

        assert varj(qt_app, lambda: controller.paneSort == ertek), (
            f"a {nev} kattintás nem állította a rendezést: {ertek}"
        )


class TestMappaRendezes:
    @pytest.mark.parametrize(
        ("nev", "ertek"),
        [
            ("menuFolderSortByDate", "date"),
            ("menuFolderSortByName", "name"),
        ],
    )
    def test_a_mappa_rendezese_valodi_kattintassal_allitja_a_rendezest(
        self, menu_app, qt_app, nev, ertek
    ):
        window, controller, _engine = menu_app
        elokeszit(window, qt_app, controller)
        elozo = "name" if ertek != "name" else "date"
        controller.setFolderSort(elozo)
        assert varj(qt_app, lambda: controller.folderSort == elozo)

        tetel_kattintasa(
            window, qt_app, "F&older", nev, almenu_utvonal=("menuFolderSortBy",)
        )

        assert varj(qt_app, lambda: controller.folderSort == ertek), (
            f"a {nev} kattintás nem állította a mappa-rendezést: {ertek}"
        )
