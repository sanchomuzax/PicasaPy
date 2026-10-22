"""A rács helyi menüi VALÓDI kattintással (#5150, 6. rész, 2. fájl).

Lefedve: a bal panel mappalista-menüje (FolderListContextMenu), az album-menü
(AlbumContextMenu), az Emberek-album menü (PeopleAlbumContextMenu) és az
Emberek-albumban látszó két fotó-menü tétel (PhotoContextMenu). A mappa-menü a
`test_racs_helyimenuk_valodi_5150.py`-ban, a többi fotó- és a címke-menü a
`..._5150_c.py`-ban van.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import app_epitese
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    cel_utja,
    elokeszit_str,
    gyerek,
    jobbklikk_fotón,
    jobbklikk_mappalistan,
    keres_vizualis,
    kattints,
    kijelolt,
    kijelol,
    nyitott,
    sorrend,
    uj_kep,
    varj,
    zar,
)
from tests.app.qml_functional.test_people_album_menu_4645 import (
    _prepare_person as emberek_elokeszitese,
)


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


class TestMappalistaMenu:
    @pytest.mark.parametrize(
        ("nev", "ertek"),
        [
            ("folderListMenuSortByDate", "date"),
            ("folderListMenuSortByName", "name"),
            ("folderListMenuSortBySize", "size"),
            ("folderListMenuSortByChanged", "changed"),
        ],
    )
    def test_a_bal_hasab_rendezese_valodi_kattintassal_allitja_a_rendezest(
        self, mappa_app, qt_app, nev, ertek
    ):
        window, controller, _motor = mappa_app
        window.show()
        window.requestActivate()
        elozo = "name" if ertek != "name" else "size"
        controller.setPaneSort(elozo)
        assert varj(qt_app, lambda: controller.paneSort == elozo)

        jobbklikk_mappalistan(window, qt_app)
        kattints(window, qt_app, gyerek(window, nev))

        assert varj(qt_app, lambda: controller.paneSort == ertek), (
            f"a {nev} kattintás nem állította a bal hasáb rendezését: {ertek}"
        )

    def test_a_bal_hasab_fordított_sorrende_valodi_kattintassal_billen(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        window.show()
        window.requestActivate()
        elozo = controller.paneSortReverse

        jobbklikk_mappalistan(window, qt_app)
        kattints(window, qt_app, gyerek(window, "folderListMenuSortReverse"))

        assert varj(qt_app, lambda: controller.paneSortReverse is (not elozo)), (
            "a Reverse order kattintás nem billentette a bal hasáb fordított sorrendjét"
        )

    @pytest.mark.parametrize(
        ("nev", "ertek"),
        [
            ("folderListMenuSortPeopleByName", "name"),
            ("folderListMenuSortPeopleByCount", "count"),
            ("folderListMenuSortPeopleByTopList", "top"),
        ],
    )
    def test_az_emberek_rendezese_valodi_kattintassal_allitja_a_rendezest(
        self, mappa_app, qt_app, nev, ertek
    ):
        window, controller, _motor = mappa_app
        window.show()
        window.requestActivate()
        elozo = "count" if ertek != "count" else "name"
        controller.setPeopleSort(elozo)
        assert varj(qt_app, lambda: controller.peopleSort == elozo)

        jobbklikk_mappalistan(window, qt_app)
        kattints(window, qt_app, gyerek(window, nev))

        assert varj(qt_app, lambda: controller.peopleSort == ertek), (
            f"a {nev} kattintás nem állította az Emberek rendezését: {ertek}"
        )

    def test_az_egyszerusitett_fanezet_valodi_kattintassal_billen(
        self, mappa_app, qt_app
    ):
        window, controller, _motor = mappa_app
        window.show()
        window.requestActivate()
        pane = gyerek(window, "folderPane")
        fa = pane.property("hierarchyController")
        elozo = bool(fa.property("simplified"))

        jobbklikk_mappalistan(window, qt_app)
        kattints(window, qt_app, gyerek(window, "folderListMenuSimplifiedTree"))

        assert varj(qt_app, lambda: bool(fa.property("simplified")) is (not elozo)), (
            "az Egyszerűsített fanézet kattintás nem billentette a kapcsolót"
        )


class TestAlbumMenu:
    @pytest.fixture
    def album_token(self, mappa_app, qt_app):
        window, controller, _motor = mappa_app
        elokeszit_str(window, qt_app, controller)
        kijelol(window, qt_app, [0])
        token = controller.createAlbum("Album", [0])
        assert token, "az album nem jött létre"
        assert varj(
            qt_app,
            lambda: keres_vizualis(window, f"albumItem_{token}") is not None,
        ), "az album sora nem jelent meg a bal hasábon"
        return token

    def _album_menu(self, window, qt_app, token):
        sor = keres_vizualis(window, f"albumItem_{token}")
        kattints(window, qt_app, sor, Qt.MouseButton.RightButton)
        menu = gyerek(window, "albumContextMenu")
        assert varj(qt_app, lambda: menu.property("visible") is True), (
            "az album jobbklikkje nem nyitotta meg a helyi menüt"
        )
        return menu

    def test_a_leiras_szerkesztese_valodi_kattintassal_az_album_parbeszedet_nyitja(
        self, mappa_app, qt_app, album_token
    ):
        window, _controller, _motor = mappa_app
        self._album_menu(window, qt_app, album_token)
        kattints(window, qt_app, gyerek(window, "albumMenuEditDescription"))

        dialog = gyerek(window, "folderPropertiesDialog")
        assert varj(qt_app, lambda: dialog.property("opened") is True), (
            "az Edit Description kattintás nem nyitotta meg a párbeszédet"
        )
        assert dialog.property("mode") == "album"
        assert dialog.property("albumToken") == album_token
        zar(qt_app, dialog)

    def test_a_nevcimkek_hozzaadasa_valodi_kattintassal_az_album_kepeit_vizsgalja(
        self, mappa_app, qt_app, album_token, monkeypatch
    ):
        """Helyettesítő: a face-scan ténylegesen futna; a hívást rögzítjük."""
        window, _controller, engine = mappa_app
        arc = engine.rootContext().contextProperty("faceScanController")
        hivasok: list[str] = []
        monkeypatch.setattr(arc, "scanAlbum", lambda token: hivasok.append(token))

        self._album_menu(window, qt_app, album_token)
        kattints(window, qt_app, gyerek(window, "albumMenuAddNameTags"))

        assert varj(qt_app, lambda: hivasok == [album_token]), (
            f"az Add name tags kattintás nem az album vizsgálatát indította: {hivasok}"
        )

    @pytest.mark.parametrize(
        ("nev", "kijeloles_elotte", "vart"),
        [
            ("albumMenuSelectAll", [], [0, 1, 2]),
            ("albumMenuClearSelection", [0], []),
            ("albumMenuInvertSelection", [0], [1, 2]),
        ],
    )
    def test_a_kijeloles_parancsai_valodi_kattintassal_az_album_menubol(
        self, mappa_app, qt_app, album_token, nev, kijeloles_elotte, vart
    ):
        window, _controller, _motor = mappa_app
        kijelol(window, qt_app, kijeloles_elotte)

        self._album_menu(window, qt_app, album_token)
        kattints(window, qt_app, gyerek(window, nev))

        assert varj(qt_app, lambda: kijelolt(window) == vart), (
            f"a {nev} kattintás után a kijelölés: {kijelolt(window)}"
        )

    def test_az_indexkepek_frissitese_valodi_kattintassal_beolvassa_a_lemezt(
        self, mappa_app, qt_app, album_token
    ):
        window, controller, _motor = mappa_app
        cel = cel_utja(controller)
        uj_kep(cel, "d_uj.jpg")

        self._album_menu(window, qt_app, album_token)
        kattints(window, qt_app, gyerek(window, "albumMenuRefreshThumbnails"))

        assert varj(qt_app, lambda: len(sorrend(controller, cel)) == 4), (
            "a Refresh Thumbnails kattintás nem olvasta be az új képet"
        )

    def test_az_album_export_html_valodi_kattintassal_megnyitja_a_webexportot(
        self, mappa_app, qt_app, album_token
    ):
        window, _controller, _motor = mappa_app
        self._album_menu(window, qt_app, album_token)
        kattints(window, qt_app, gyerek(window, "albumMenuExportAsHtml"))

        dialog = gyerek(window, "webExportDialog")
        assert varj(qt_app, lambda: nyitott(dialog)), (
            "az Export as HTML kattintás nem nyitotta meg a webexportot"
        )
        zar(qt_app, dialog)

    @pytest.mark.parametrize(
        "nev",
        [
            "albumMenuOnlineActions",
            "albumMenuUploadToGooglePhotos",
        ],
    )
    def test_a_megszunt_szolgaltatas_tetele_valodi_kattintasra_nem_csinal_semmit(
        self, mappa_app, qt_app, album_token, nev
    ):
        window, controller, _motor = mappa_app
        cel = cel_utja(controller)
        elotte = sorrend(controller, cel)

        menu = self._album_menu(window, qt_app, album_token)
        tetel = gyerek(window, nev)
        assert tetel.property("enabled") is False, f"{nev}: a megszűnt tétel nincs letiltva"
        kattints(window, qt_app, tetel)

        assert sorrend(controller, cel) == elotte
        zar(qt_app, menu)


class TestEmberekMenu:
    @pytest.mark.parametrize(
        ("nev", "kijeloles_elotte", "vart"),
        [
            ("peopleAlbumMenuSelectAll", [], [0, 1]),
            ("peopleAlbumMenuClearSelection", [0], []),
        ],
    )
    def test_a_kijeloles_parancsai_valodi_kattintassal_az_emberek_menubol(
        self, qml_app, qt_app, nev, kijeloles_elotte, vart
    ):
        window, controller, _engine = qml_app
        emberek_elokeszitese(window, controller, qt_app, 0)
        kijelol(window, qt_app, kijeloles_elotte)

        sor = keres_vizualis(window, "personItem_Anna")
        assert sor is not None, "az Anna személy sora nem látszik"
        kattints(window, qt_app, sor, Qt.MouseButton.RightButton)
        menu = gyerek(window, "peopleAlbumContextMenu")
        assert varj(qt_app, lambda: menu.property("visible") is True)
        kattints(window, qt_app, gyerek(window, nev))

        assert varj(qt_app, lambda: kijelolt(window) == vart), (
            f"a {nev} kattintás után a kijelölés: {kijelolt(window)}"
        )


class TestEmberekFotoMenu:
    """A fotó-menü két tétele csak az Emberek-albumban látszik (`personName != ""`)."""

    @pytest.mark.parametrize(
        ("nev", "parbeszed"),
        [
            ("contextMenuRemoveFromPeopleAlbum", "removePeopleFacesDialog"),
            ("contextMenuMoveToNewPerson", "moveToNewPersonDialog"),
        ],
    )
    def test_az_emberek_albumos_fotomenu_tetele_valodi_kattintassal_parbeszedet_nyit(
        self, qml_app, qt_app, nev, parbeszed
    ):
        window, controller, _engine = qml_app
        emberek_elokeszitese(window, controller, qt_app, 0)
        kattints(window, qt_app, keres_vizualis(window, "personItem_Anna"))
        assert varj(qt_app, lambda: controller.currentPersonName == "Anna"), (
            "az Anna sorára kattintás nem nyitotta meg az Emberek-albumot"
        )
        kijelol(window, qt_app, [0])

        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, nev))

        dialog = gyerek(window, parbeszed)
        assert varj(qt_app, lambda: nyitott(dialog)), (
            f"a(z) {nev} kattintás nem nyitotta meg a(z) {parbeszed} párbeszédet"
        )
        zar(qt_app, dialog)
