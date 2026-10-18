"""A rács helyi menüi VALÓDI kattintással (#5150, 6. rész, 1. fájl): a Mappa-menü.

Lefedve a FolderContextMenu B-listás tételei: kijelölés, indexképek frissítése,
rendezés, elrejtés, lemez-műveletek, áthelyezés, gyűjtemény és névcímkék.
A mappalista-, album- és Emberek-menü a `..._5150_b.py`-ban, a fotó- és
címke-menü a `..._5150_c.py`-ban van; a közös segédek a
`_racs_helyimenuk_5150_helpers.py`-ban.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, Qt

from picasapy.app.kezi_sorrend import mentsd_a_prioritasokat
from picasapy.index import open_index
from picasapy.index.colors import backfill_colors
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import KEPEK, app_epitese, nyitott
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    almenu_megnyitasa,
    egyezik,
    elokeszit_str,
    gyerek,
    ini_sorrend,
    jobbklikk_mappan,
    keres_vizualis,
    kattints,
    kijelolt,
    kijelol,
    prioritasok,
    sorrend,
    uj_kep,
    varj,
    zar,
)


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _rendezes_menu(window, qt_app, cel: str):
    """Mappa-menü, majd a Sort Folder By almenü valódi megnyitása."""
    menu = jobbklikk_mappan(window, qt_app, cel)
    almenu_megnyitasa(window, qt_app, menu, "folderMenuSortBy")
    return menu


def _szin_index_epitese(controller) -> None:
    """Előkészítés: a színrendezés a háttér-színindexre (#383) épül; a kattintás
    előtt a háttérhajtó egy körét szinkron lefuttatjuk."""
    with open_index(controller._db_path) as conn:
        backfill_colors(conn, limit=100)


class TestMappaMenuKijeloles:
    def test_a_mind_kijelolese_valodi_kattintassal_kijeloli_a_kepeket(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [])

        jobbklikk_mappan(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuSelectAll"))

        assert varj(qt_app, lambda: kijelolt(window) == [0, 1, 2]), (
            f"a Select All kattintás után a kijelölés: {kijelolt(window)}"
        )

    def test_a_kijeloles_torlese_valodi_kattintassal_uriti_a_kijelolest(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0, 1])

        jobbklikk_mappan(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuClearSelection"))

        assert varj(qt_app, lambda: kijelolt(window) == []), (
            f"a Clear Selection kattintás után a kijelölés: {kijelolt(window)}"
        )

    def test_a_kijeloles_forditasa_valodi_kattintassal_megfordítja_a_kijelolest(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])

        jobbklikk_mappan(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuInvertSelection"))

        assert varj(qt_app, lambda: kijelolt(window) == [1, 2]), (
            f"az Invert Selection kattintás után a kijelölés: {kijelolt(window)}"
        )


class TestMappaMenuNezet:
    def test_az_indexkepek_frissitese_valodi_kattintassal_beolvassa_a_lemezt(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        uj_kep(cel, "d_uj.jpg")

        jobbklikk_mappan(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuRefreshThumbnails"))

        assert varj(qt_app, lambda: len(sorrend(controller, cel)) == 4), (
            "a Refresh Thumbnails kattintás nem olvasta be az új képet"
        )


class TestMappaMenuRendezes:
    @pytest.mark.parametrize("nev", ["folderMenuSortByDate", "folderMenuSortByColor"])
    def test_a_rendezes_valodi_kattintassal_kimenti_a_mappa_sorrendjet(
        self, mappa_app, qt_app, nev
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        # a mappának még nincs mentett sorrendje: a kattintásnak kell létrehoznia
        assert prioritasok(cel) == {}, "a mappának már volt mentett sorrendje"
        if nev == "folderMenuSortByColor":
            _szin_index_epitese(controller)

        _rendezes_menu(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, nev))

        def teljes_sorrend() -> bool:
            mentett = prioritasok(cel)
            return (
                set(mentett) == set(sorrend(controller, cel))
                and sorted(mentett.values()) == [1.0, 2.0, 3.0]
            )

        assert varj(qt_app, teljes_sorrend), (
            f"a {nev} kattintás nem mentette el a mappa teljes, 1..3 sorrendjét"
        )

    def test_a_kezi_sorrend_valodi_kattintassal_atszamozza_a_mentett_helyeket(
        self, mappa_app, qt_app
    ):
        """Ha a mentett helyek nem 1..n-ek (10/20/30), a Manual order kattintás
        a kézi sorrendet a sorszámokkal együtt 1..n-re írja át."""
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        mentsd_a_prioritasokat(cel, dict(zip(KEPEK, (10.0, 20.0, 30.0), strict=True)))
        assert varj(qt_app, lambda: sorted(prioritasok(cel).values()) == [10.0, 20.0, 30.0])

        _rendezes_menu(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuSortByPriority"))

        assert varj(qt_app, lambda: sorted(prioritasok(cel).values()) == [1.0, 2.0, 3.0]), (
            f"a Manual order kattintás nem írta át 1..3-ra: {prioritasok(cel)}"
        )
        assert ini_sorrend(cel) == list(KEPEK), (
            f"a Manual order kattintás megváltoztatta a sorrendet: {ini_sorrend(cel)}"
        )

    def test_a_fordított_sorrend_valodi_kattintassal_megfordítja_a_mentett_sorrendet(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        controller.sortFolderBy(cel, "name")
        assert varj(qt_app, lambda: len(ini_sorrend(cel)) == 3)
        elotte = ini_sorrend(cel)

        _rendezes_menu(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuSortReverse"))

        assert varj(qt_app, lambda: ini_sorrend(cel) == elotte[::-1]), (
            f"a Reverse order kattintás nem fordította meg a sorrendet: {ini_sorrend(cel)}"
        )


class TestMappaMenuRejtesLemezMozgatas:
    def test_a_mappa_elrejtese_valodi_kattintassal_jelolest_ir_az_indexbe(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        assert controller.isFolderHidden(cel) is False

        jobbklikk_mappan(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuHideFolder"))

        assert varj(qt_app, lambda: controller.isFolderHidden(cel) is True), (
            "a Hide Folder kattintás nem jelölte rejtettnek a mappát"
        )

    def test_a_lemezen_megmutatas_valodi_kattintassal_a_mappat_adja_at(
        self, mappa_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a valódi fájlkezelő-indítás ki van váltva."""
        import picasapy.app.fileops_controller as fileops_module

        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        megnyitva: list[Path] = []
        monkeypatch.setattr(
            fileops_module,
            "open_folder_in_file_manager",
            lambda path: megnyitva.append(Path(path)),
        )

        jobbklikk_mappan(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuLocate"))

        assert varj(qt_app, lambda: megnyitva == [Path(cel)]), (
            f"a Locate on Disk nem a mappát adta át: {megnyitva}"
        )

    def test_az_eltavolitas_valodi_kattintassal_megerositest_ker(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)

        jobbklikk_mappan(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuRemoveFromPicasa"))

        dialog = gyerek(window, "removeFolderConfirmDialog")
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "a Remove from PicasaPy kattintás nem kért megerősítést"
        )
        zar(qt_app, dialog)
        assert len(sorrend(controller, cel)) == 3, (
            "a megerősítés nélkül a mappa képei eltűntek"
        )

    def test_az_athelyezes_valodi_kattintassal_megnyitja_a_mappavalasztot(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)

        jobbklikk_mappan(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuMoveFolder"))

        pane = gyerek(window, "folderPane")
        assert varj(qt_app, lambda: egyezik(pane.property("_movingFolder"), cel)), (
            "a Move Folder nem jelölte ki az áthelyezendő mappát"
        )
        dialog = gyerek(window, "moveFolderDialog")
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "a Move Folder nem nyitotta meg a mappaválasztót"
        )
        zar(qt_app, dialog)


class TestMappaMenuGyujtemenyEsCimkek:
    def test_a_gyujtemenybe_helyezes_valodi_kattintassal_a_mappat_adja_hozza(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        controller.createCollection("Gyujtemeny")
        assert varj(qt_app, lambda: any(
            c["name"] == "Gyujtemeny" for c in controller.customCollections
        ))
        # a mappa-menü gyűjtemény-listáját a QML a létrehozás UTÁN frissíti
        # (FolderPane.refreshCustomCollections); az előkészítés ugyanezt kéri
        pane = gyerek(window, "folderPane")
        QMetaObject.invokeMethod(
            pane, "refreshCustomCollections", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()

        menu = jobbklikk_mappan(window, qt_app, cel)
        almenu_megnyitasa(window, qt_app, menu, "folderContextMenuMoveToCollection")
        # a Repeater-delegált nem a QObject-fában, hanem a vizuális fában él
        tetel = keres_vizualis(window, "folderContextMenuMoveToCollectionItem_Gyujtemeny")
        assert tetel is not None, "a gyűjtemény-tétel nem jelent meg a Move to Collection almenüben"
        kattints(window, qt_app, tetel)

        def mappa_tagja() -> bool:
            return any(
                Path(str(mappa)) == Path(cel)
                for c in controller.customCollections
                if c["name"] == "Gyujtemeny"
                for mappa in c["folders"]
            )

        assert varj(qt_app, mappa_tagja), (
            "a gyűjtemény-tétel kattintás nem tette a mappát a gyűjteménybe"
        )

    def test_a_nevcimkek_hozzaadasa_valodi_kattintassal_a_mappa_kepeit_vizsgalja(
        self, mappa_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a face-scan ténylegesen futna; a hívást rögzítjük."""
        window, controller, engine = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        arc = engine.rootContext().contextProperty("faceScanController")
        hivasok: list[str] = []
        monkeypatch.setattr(arc, "scanFolder", lambda path: hivasok.append(path))

        jobbklikk_mappan(window, qt_app, cel)
        kattints(window, qt_app, gyerek(window, "folderMenuAddNameTags"))

        assert varj(qt_app, lambda: [egyezik(h, cel) for h in hivasok] == [True]), (
            f"az Add name tags kattintás nem a mappa vizsgálatát indította: {hivasok}"
        )

    def test_a_felolto_tetel_valodi_kattintasra_nem_csinal_semmit(
        self, mappa_app, qt_app
    ):
        """A megszűnt szolgáltatás tétele tiltott: nincs kezelője, nincs hatása."""
        window, controller, _motor = mappa_app
        cel = elokeszit_str(window, qt_app, controller)
        elotte = sorrend(controller, cel)

        menu = jobbklikk_mappan(window, qt_app, cel)
        tetel = gyerek(window, "folderMenuUploadToGooglePhotos")
        assert tetel.property("enabled") is False, "a megszűnt tétel nincs letiltva"
        kattints(window, qt_app, tetel)

        assert sorrend(controller, cel) == elotte
        assert not nyitott(gyerek(window, "moveFolderDialog"))
        zar(qt_app, menu)
