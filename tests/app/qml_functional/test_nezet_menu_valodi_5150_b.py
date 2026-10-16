"""A Nézet ▸ Mappanézet tételei VALÓDI egérkattintással (#5150, 2. rész, B).

A Mappanézet almenü tételei (fa-nézet, gyökerek, Shortcuts, Egyszerűsített
fa, Albumbélyegképek) és a rendezési tételek (dátum, utolsó módosítás,
méret, név, fordított sorrend) valódi kattintással futnak. A hatást a
bal oldali hasáb nézetállapotán (`folderViewCtl`) és a mappa-rendezésen
(`controller.paneSort`) mérjük.

A gyökér-tételeknél a hatást a gyökér-jelölőn mérjük, nem a fa tartalmán:
a rendszermappák (Képek, Dokumentumok, Asztal) nem feltétlenül léteznek a
CI-gépen, és ott a fa csendben a teljes fára esik vissza.

Már lefedett tétel: `menuViewSortPeopleBy*` (Emberek rendezése) a
test_view_options_people_shortcuts_4528.py:106 valódi kattintásos tesztjében.
"""

from __future__ import annotations

import pytest

from picasapy.app import folder_hierarchy_controller as fhc

from tests.app.qml_functional._nezet_menu_5150_helpers import (
    elokeszit,
    nezet_app_epitese,
    tetel_kattintasa,
    varj,
)

_FA_ELEM = "menuViewFolderView"
_SHORTCUTS = "menuViewFolderViewShortcuts"

_GYOKEREK = (
    ("menuViewRootMyComputer", "all"),
    ("menuViewRootMyPictures", "mypics"),
    ("menuViewRootMyDocuments", "mydocs"),
    ("menuViewRootDesktop", "desktop"),
)

_GYORS_GYOKEREK = (
    ("menuViewShortcutMyComputer", "all"),
    ("menuViewShortcutMyPictures", "mypics"),
    ("menuViewShortcutMyDocuments", "mydocs"),
    ("menuViewShortcutDesktop", "desktop"),
)

_RENDEZESEK = (
    ("menuViewSortByDate", "date"),
    ("menuViewSortByRecent", "changed"),
    ("menuViewSortBySize", "size"),
    ("menuViewSortByName", "name"),
)


@pytest.fixture
def mappa_app(qt_app, tmp_path, monkeypatch):
    # A rendszermappa-gyökerek (Képek, Dokumentumok, Asztal) a futtató gép
    # mappáitól függenek: a CI-gépen nincsenek, és a program akkor helyesen a
    # Sajátgépre esik vissza. Ezért a teszt saját mappákat ad (#1407 mintája).
    utak = {}
    for token, nev in (("mypics", "Kepek"), ("mydocs", "Iratok"), ("desktop", "Asztal")):
        mappa = tmp_path / "rendszer" / nev
        mappa.mkdir(parents=True)
        utak[token] = str(mappa)
    monkeypatch.setattr(fhc, "_rendszermappa", lambda token: utak.get(token, ""))
    yield from nezet_app_epitese(qt_app, tmp_path)


def _fa_allapot(window):
    """A bal hasáb nézetállapota (`FolderHierarchyController`)."""
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    allapot = menu_bar.property("folderViewCtl")
    assert allapot is not None, "a mappanézet vezérlője hiányzik"
    return allapot


def _elozo(ertek: str, lehetosegek: tuple[str, str]) -> str:
    """Olyan állapot, amely eltér a céltól, hogy a kattintás hatása látszódjon."""
    return lehetosegek[0] if ertek != lehetosegek[0] else lehetosegek[1]


class TestFanezetEsGyokerek:
    def test_a_fa_nezet_valodi_kattintassal_bekapcsol(self, mappa_app, qt_app):
        window, controller, _engine = mappa_app
        elokeszit(window, qt_app, controller)
        allapot = _fa_allapot(window)
        allapot.setTreeView(False)
        assert varj(qt_app, lambda: allapot.property("treeView") is False)

        tetel_kattintasa(window, qt_app, "menuViewTreeView", almenu_utvonal=(_FA_ELEM,))

        assert varj(qt_app, lambda: allapot.property("treeView") is True), (
            "a Mappanézet ▸ Fa-nézet kattintás nem kapcsolta be a fa-nézetet"
        )

    def test_a_lapos_nezet_valodi_kattintassal_visszavalt(self, mappa_app, qt_app):
        window, controller, _engine = mappa_app
        elokeszit(window, qt_app, controller)
        allapot = _fa_allapot(window)
        allapot.setTreeView(True)
        assert varj(qt_app, lambda: allapot.property("treeView") is True)

        tetel_kattintasa(window, qt_app, "menuViewFlatFolderView", almenu_utvonal=(_FA_ELEM,))

        assert varj(qt_app, lambda: allapot.property("treeView") is False), (
            "a Mappanézet ▸ Lapos nézet kattintás nem váltott vissza"
        )

    @pytest.mark.parametrize(("nev", "token"), _GYOKEREK)
    def test_a_gyoker_valodi_kattintassal_atallitja_a_gyokeret(self, mappa_app, qt_app, nev, token):
        window, controller, _engine = mappa_app
        elokeszit(window, qt_app, controller)
        allapot = _fa_allapot(window)
        elozo = _elozo(token, ("all", "desktop"))
        allapot.setViewRoot(elozo)
        assert varj(qt_app, lambda: allapot.property("viewRoot") == elozo)

        tetel_kattintasa(window, qt_app, nev, almenu_utvonal=(_FA_ELEM,))

        assert varj(qt_app, lambda: allapot.property("viewRoot") == token), (
            f"a {nev} kattintás nem állította a gyökeret: {token}"
        )

    @pytest.mark.parametrize(("nev", "token"), _GYORS_GYOKEREK)
    def test_a_shortcuts_gyoker_valodi_kattintassal_atallitja_a_gyokeret(
        self, mappa_app, qt_app, nev, token
    ):
        window, controller, _engine = mappa_app
        elokeszit(window, qt_app, controller)
        allapot = _fa_allapot(window)
        elozo = _elozo(token, ("all", "desktop"))
        allapot.setViewRoot(elozo)
        assert varj(qt_app, lambda: allapot.property("viewRoot") == elozo)

        tetel_kattintasa(window, qt_app, nev, almenu_utvonal=(_FA_ELEM, _SHORTCUTS))

        assert varj(qt_app, lambda: allapot.property("viewRoot") == token), (
            f"a {nev} kattintás nem állította a gyökeret: {token}"
        )


class TestKapcsolok:
    @pytest.mark.parametrize("nev", ["menuViewSimplifiedTreeView", "menuViewAlbumThumbnails"])
    def test_a_mappanezet_kapcsolo_valodi_kattintassal_billen(self, mappa_app, qt_app, nev):
        window, controller, _engine = mappa_app
        elokeszit(window, qt_app, controller)
        allapot = _fa_allapot(window)
        kulcs = "simplified" if nev == "menuViewSimplifiedTreeView" else "albumThumbs"
        elozo = allapot.property(kulcs)

        tetel_kattintasa(window, qt_app, nev, almenu_utvonal=(_FA_ELEM,))

        assert varj(qt_app, lambda: allapot.property(kulcs) is (not elozo)), (
            f"a {nev} kattintás nem billentette a(z) {kulcs} állapotot"
        )


class TestRendezes:
    @pytest.mark.parametrize(("nev", "mod"), _RENDEZESEK)
    def test_a_rendezes_valodi_kattintassal_beallitja_a_modot(self, mappa_app, qt_app, nev, mod):
        window, controller, _engine = mappa_app
        elokeszit(window, qt_app, controller)
        elozo = _elozo(mod, ("date", "name"))
        controller.setPaneSort(elozo)
        assert varj(qt_app, lambda: controller.paneSort == elozo)

        tetel_kattintasa(window, qt_app, nev, almenu_utvonal=(_FA_ELEM,))

        assert varj(qt_app, lambda: controller.paneSort == mod), (
            f"a {nev} kattintás nem állította a rendezést: {mod}"
        )

    def test_a_forditott_sorrend_valodi_kattintassal_billen(self, mappa_app, qt_app):
        window, controller, _engine = mappa_app
        elokeszit(window, qt_app, controller)
        elozo = controller.paneSortReverse

        tetel_kattintasa(window, qt_app, "menuViewSortReverse", almenu_utvonal=(_FA_ELEM,))

        assert varj(qt_app, lambda: controller.paneSortReverse is (not elozo)), (
            "a Fordított sorrend kattintás nem billentette a sorrendet"
        )
