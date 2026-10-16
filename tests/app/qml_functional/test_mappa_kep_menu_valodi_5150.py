"""A Mappa és a Kép menü tételei VALÓDI egérkattintással (#5150, 3. rész).

Minden tétel a menüsor fejlécére (és az almenü sorára) kattintva indul, a
hatást a vezérlő állapotán, a lemezen maradt fájlokon vagy a párbeszédek
láthatóságán mérjük. A közös segédek a `_mappa_kep_menu_5150_helpers.py`-ban
vannak.

Már lefedett tételek (ezeket itt nem ismételjük):
- `menuFolderHide`, `menuFolderShow`: test_mappa_menu_elrejt_megjelenit_4416.py:83
- `menuFolderWebExport`: test_menusor_billentyu_valodi_5127.py:181
- `menuFolderSlideshow`: test_menu_talca_egyeb_valodi_5135.py:153
- `menuPictureViewAndEdit`: test_felsomenupontok_kep_4329.py:20
- `menuPictureHide`, `menuPictureUnhide`: test_felsomenupontok_kep_4329.py:40
- `menuPictureResetFaces`: test_felsomenupontok_kep_4329.py:140
- `menuPictureBatchEdit` (almenü-nyitás): test_photo_menu_commands.py:123
- `menuPictureShowText`, `menuPictureHideText`: test_photo_menu_commands.py:366

Lefedve itt: a Mappa ▸ Rendezés négy tétele és a Fordított sorrend, a Leírás
szerkesztése, a Nyomtatás indexképként, a Lemezen megmutatás, az Eltávolítás a
Picasából, az Áthelyezés és a Törlés; a Kép ▸ Undo All Edits és a Tulajdonságok.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    KEPEK,
    MASIK,
    app_epitese,
    elokeszit,
    gyerek,
    keszits_ket_mappat,
    nyitott,
    szures,
    tetel_kattintasa,
    varj,
    zar,
)

_RENDEZESEK = (
    ("menuFolderSortByDate", "date"),
    ("menuFolderSortByName", "name"),
    ("menuFolderSortBySize", "size"),
    ("menuFolderSortByChanged", "changed"),
)


@pytest.fixture
def mappa_kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


@pytest.fixture
def ket_mappas_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path, kepeket_keszit=keszits_ket_mappat)


def _rendezes_elotti(ertek: str) -> str:
    """Olyan kiinduló rendezés, amely eltér a céltól, hogy a kattintás hatása látszódjon."""
    return "size" if ertek != "size" else "name"


class TestMappaRendezes:
    @pytest.mark.parametrize(("nev", "ertek"), _RENDEZESEK)
    def test_a_rendezes_valodi_kattintassal_allitja_a_mappa_rendezeset(
        self, mappa_kep_app, qt_app, nev, ertek
    ):
        window, controller, _engine = mappa_kep_app
        elokeszit(window, qt_app, controller)
        elozo = _rendezes_elotti(ertek)
        controller.setFolderSort(elozo)
        assert varj(qt_app, lambda: controller.folderSort == elozo)

        tetel_kattintasa(
            window, qt_app, "F&older", nev, almenu_utvonal=("menuFolderSortBy",)
        )

        assert varj(qt_app, lambda: controller.folderSort == ertek), (
            f"a {nev} kattintás nem állította a mappa rendezését: {ertek}"
        )

    def test_a_meret_szerinti_rendezes_valodi_kattintassal_atrendezi_a_mappablokkokat(
        self, ket_mappas_app, qt_app
    ):
        """A Mappa ▸ Rendezés a MAPPÁK sorrendjét adja a rácson, nem a képekét
        (ld. `controller.setFolderSort` dokumentációja), ezért a mappák
        sorrendjét mérjük."""
        window, controller, _engine = ket_mappas_app
        window.show()
        window.requestActivate()
        qt_app.processEvents()
        controller.setFolderSort("name")

        def mappak_sorrendje() -> list[str]:
            sorrend: list[str] = []
            for foto in controller.photos.photos:
                nev = Path(str(foto.folder_path)).name
                if not sorrend or sorrend[-1] != nev:
                    sorrend.append(nev)
            return sorrend

        assert varj(qt_app, lambda: mappak_sorrendje() == ["fotok", MASIK]), (
            f"a név szerinti kiinduló sorrend nem áll be: {mappak_sorrendje()}"
        )

        tetel_kattintasa(
            window, qt_app, "F&older", "menuFolderSortBySize",
            almenu_utvonal=("menuFolderSortBy",),
        )

        assert varj(qt_app, lambda: mappak_sorrendje() == [MASIK, "fotok"]), (
            f"a Mappa ▸ Méret kattintás után a mappák sorrendje: {mappak_sorrendje()}"
        )

    def test_a_forditott_sorrend_valodi_kattintassal_billenti_a_kapcsolot(
        self, mappa_kep_app, qt_app
    ):
        window, controller, _engine = mappa_kep_app
        elokeszit(window, qt_app, controller)
        elozo = controller.folderSortReverse

        tetel_kattintasa(
            window, qt_app, "F&older", "menuFolderSortReverse",
            almenu_utvonal=("menuFolderSortBy",),
        )

        assert varj(qt_app, lambda: controller.folderSortReverse == (not elozo)), (
            "a Fordított sorrend kattintás nem billentette a kapcsolót"
        )


class TestMappaMuveletek:
    def test_a_leiras_szerkesztese_valodi_kattintassal_a_mappa_parbeszedet_nyitja(
        self, mappa_kep_app, qt_app
    ):
        window, controller, _engine = mappa_kep_app
        cel = elokeszit(window, qt_app, controller)

        tetel_kattintasa(window, qt_app, "F&older", "menuFolderEditDescription")

        dialog = gyerek(window, "folderPropertiesDialog")
        assert varj(qt_app, lambda: dialog.property("opened") is True), (
            "a Mappa ▸ Edit Description kattintás nem nyitotta meg a mappa-párbeszédet"
        )
        assert dialog.property("mode") == "folder"
        assert dialog.property("folderPath") == str(cel)
        zar(qt_app, dialog)

    def test_a_nyomtatas_indexkepkent_valodi_kattintassal_megnyitja_a_nyomtatast(
        self, mappa_kep_app, qt_app
    ):
        window, controller, _engine = mappa_kep_app
        elokeszit(window, qt_app, controller)

        tetel_kattintasa(window, qt_app, "F&older", "menuFolderPrintContactSheet")

        dialog = gyerek(window, "printDialog")
        assert varj(
            qt_app,
            lambda: dialog.property("visible") is True
            and dialog.property("contactSheet") is True,
        ), "a Mappa ▸ Print Contact Sheet kattintás nem nyitotta meg az indexképes nyomtatást"
        zar(qt_app, dialog)

    def test_a_lemezen_megmutatas_valodi_kattintassal_a_mappat_adja_at(
        self, mappa_kep_app, qt_app, monkeypatch
    ):
        """Helyettesítő: a valódi fájlkezelő-indítás ki van váltva."""
        import picasapy.app.fileops_controller as fileops_module

        window, controller, _engine = mappa_kep_app
        cel = elokeszit(window, qt_app, controller)
        megnyitva: list[Path] = []
        monkeypatch.setattr(
            fileops_module,
            "open_folder_in_file_manager",
            lambda path: megnyitva.append(Path(path)),
        )

        tetel_kattintasa(window, qt_app, "F&older", "menuFolderLocate")

        assert varj(qt_app, lambda: megnyitva == [cel]), (
            f"a Lemezen megmutatás nem a mappát adta át: {megnyitva}"
        )

    def test_az_eltavolitas_valodi_kattintassal_megerositest_ker(
        self, mappa_kep_app, qt_app
    ):
        window, controller, _engine = mappa_kep_app
        elokeszit(window, qt_app, controller)

        tetel_kattintasa(window, qt_app, "F&older", "menuFolderRemoveFromPicasa")

        assert varj(
            qt_app, lambda: nyitott(_objektum(window, "removeFolderConfirmDialog"))
        ), "a Mappa ▸ Remove from Picasa nem kért megerősítést"
        zar(qt_app, _objektum(window, "removeFolderConfirmDialog"))
        assert len(controller.photos.photos) == len(KEPEK), (
            "a megerősítés nélkül a mappa képei eltűntek"
        )

    def test_az_athelyezes_valodi_kattintassal_megnyitja_a_mappavalasztot(
        self, mappa_kep_app, qt_app
    ):
        window, controller, _engine = mappa_kep_app
        cel = elokeszit(window, qt_app, controller)

        tetel_kattintasa(window, qt_app, "F&older", "menuFolderMove")

        pane = gyerek(window, "folderPane")
        assert varj(qt_app, lambda: pane.property("_movingFolder") == str(cel)), (
            "a Mappa ▸ Move nem jelölte ki az áthelyezendő mappát"
        )
        assert varj(qt_app, lambda: nyitott(_objektum(window, "moveFolderDialog"))), (
            "a Mappa ▸ Move nem nyitotta meg a mappaválasztót"
        )
        zar(qt_app, _objektum(window, "moveFolderDialog"))

    def test_a_torles_valodi_kattintassal_megerositest_ker(
        self, mappa_kep_app, qt_app
    ):
        window, controller, _engine = mappa_kep_app
        cel = elokeszit(window, qt_app, controller)

        tetel_kattintasa(window, qt_app, "F&older", "menuFolderDelete")

        assert varj(
            qt_app, lambda: nyitott(_objektum(window, "deleteFolderConfirmDialog"))
        ), "a Mappa ▸ Delete nem kért megerősítést"
        zar(qt_app, _objektum(window, "deleteFolderConfirmDialog"))
        assert cel.is_dir(), "a megerősítés nélkül a mappa eltűnt a lemezről"


class TestKepMenu:
    def test_a_visszavonas_valodi_kattintassal_megerositest_ker_es_nem_vonja_vissza(
        self, mappa_kep_app, qt_app
    ):
        window, controller, _engine = mappa_kep_app
        elokeszit(window, qt_app, controller)
        wait_for_photo_op(
            controller, lambda: controller.applyEffectMany([0], "sepia"), qt_app=qt_app
        )
        assert varj(qt_app, lambda: "sepia=1;" in szures(controller, 0)), (
            "az előkészítő Sepia nem írt effektláncot"
        )

        tetel_kattintasa(window, qt_app, "&Picture", "menuPictureUndoAllEdits")

        assert varj(
            qt_app, lambda: nyitott(_objektum(window, "undoAllEditsDialog"))
        ), "a Kép ▸ Undo All Edits nem kért megerősítést"
        zar(qt_app, _objektum(window, "undoAllEditsDialog"))
        assert "sepia=1;" in szures(controller, 0), (
            "a megerősítés nélkül a szerkesztési lánc törlődött"
        )

    def test_a_tulajdonsagok_valodi_kattintassal_megnyitja_a_tulajdonsagok_lapot(
        self, mappa_kep_app, qt_app
    ):
        window, controller, _engine = mappa_kep_app
        elokeszit(window, qt_app, controller)
        window.setProperty("activeDrawerTab", "")
        qt_app.processEvents()

        tetel_kattintasa(window, qt_app, "&Picture", "menuPictureProperties")

        assert varj(qt_app, lambda: window.property("activeDrawerTab") == "properties"), (
            "a Kép ▸ Properties kattintás nem nyitotta meg a tulajdonságok lapot"
        )
