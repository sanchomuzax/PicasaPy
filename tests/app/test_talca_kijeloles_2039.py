"""#2039: a képtálcának SAJÁT kijelölése van — a rács kijelölése nem az.

## A lelet (a jegyből)

Az eredetiben a tálca ugyanolyan `CSelectionNode`, mint a rács
(`docs/specs/picasa-keptalca.md` 13.: `[ebx+0xea4]`), és a csomópont
ELEMENKÉNTI állapotot tárol (`+0x32c` elemtömb, elemenként `[elem+0x59]`
kijelölt). A tálca számlálója (`0x00716cb0`) épp ezt a jelzőt olvassa.

Nálunk a tálca eddig TÜKÖR volt: vagy a megtartottakat mutatta, vagy a rács
kijelölését, és a „Kijelölés eltávolítása" a RÁCS kijelölésére hatott.

## Amit ez az őr állít

1. a tálcán ki lehet jelölni egy elemet, és a kijelölés a tálca SAJÁT
   állapota (tálca-indexek, nem rács-sorok);
2. `Ctrl` hozzáad/elvesz, `Shift` tartományt jelöl;
3. a RÁCS kijelölésének változása NEM törli a tálca kijelölését — ez a jegy
   kifejezett pontja, és a régi `syncSelection()` épp ezt tette volna;
4. a „Kijelölés eltávolítása" a TÁLCÁN kijelöltet veszi ki: három elemből
   egyet kijelölve **kettő marad**.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def two_folder_library(tmp_path):
    root = tmp_path / "kepek"
    folder_a = root / "a"
    folder_b = root / "b"
    folder_a.mkdir(parents=True)
    folder_b.mkdir(parents=True)
    for nev in ("x.jpg", "y.jpg", "z.jpg"):
        make_jpeg(folder_a / nev, size=(200, 150))
    make_jpeg(folder_b / "q.jpg", size=(200, 150))
    return root, folder_a, folder_b


@pytest.fixture
def controller(qt_app, tmp_path, two_folder_library):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    root, folder_a, _folder_b = two_folder_library
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(root),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(folder_a))
    return ctl


def _harmat_a_talcara(ctl):
    """Három kép a tálcára, MEGTARTVA (a tálca így nem tükör)."""
    ctl.holdRows([0, 1, 2])
    assert ctl.heldCount == 3, ctl.heldCount
    return ctl


class TestSajatKijeloles:
    def test_alapban_ures(self, controller):
        _harmat_a_talcara(controller)
        assert list(controller.traySelectedIndexes) == []

    def test_egy_elem_kijelolese(self, controller):
        _harmat_a_talcara(controller)
        controller.selectTrayIndex(1, False, False)
        assert list(controller.traySelectedIndexes) == [1]

    def test_masikra_kattintva_ATVALT(self, controller):
        _harmat_a_talcara(controller)
        controller.selectTrayIndex(1, False, False)
        controller.selectTrayIndex(2, False, False)
        assert list(controller.traySelectedIndexes) == [2]

    def test_CTRL_hozzaad_es_elvesz(self, controller):
        _harmat_a_talcara(controller)
        controller.selectTrayIndex(0, False, False)
        controller.selectTrayIndex(2, True, False)
        assert list(controller.traySelectedIndexes) == [0, 2]
        controller.selectTrayIndex(0, True, False)
        assert list(controller.traySelectedIndexes) == [2]

    def test_SHIFT_tartomanyt_jelol(self, controller):
        _harmat_a_talcara(controller)
        controller.selectTrayIndex(0, False, False)
        controller.selectTrayIndex(2, False, True)
        assert list(controller.traySelectedIndexes) == [0, 1, 2]

    def test_a_tartomany_visszafele_is_mukodik(self, controller):
        _harmat_a_talcara(controller)
        controller.selectTrayIndex(2, False, False)
        controller.selectTrayIndex(0, False, True)
        assert list(controller.traySelectedIndexes) == [0, 1, 2]

    def test_a_hatarokon_kivuli_index_nem_omlik_ossze(self, controller):
        _harmat_a_talcara(controller)
        controller.selectTrayIndex(99, False, False)
        controller.selectTrayIndex(-1, False, False)
        assert list(controller.traySelectedIndexes) == []


class TestARacsNemTorliEl:
    def test_a_racs_kijelolese_NEM_torli(self, controller):
        """A jegy kifejezett pontja: a `syncSelection()` ne söpörje el."""
        _harmat_a_talcara(controller)
        controller.selectTrayIndex(1, False, False)

        controller.syncSelection([0, 2])

        assert list(controller.traySelectedIndexes) == [1], (
            "a rács kijelölésének változása eltörölte a tálca saját "
            "kijelölését (#2039)"
        )


class TestKijelolesEltavolitasa:
    def test_a_TALCAN_kijeloltet_veszi_ki(self, controller):
        """A jegy őr-forgatókönyve: három elem, egy kijelölve ⇒ kettő marad."""
        _harmat_a_talcara(controller)
        controller.selectTrayIndex(1, False, False)

        controller.removeTraySelected()

        assert controller.heldCount == 2, (
            "a »Kijelölés eltávolítása« nem a tálcán kijelöltet vette ki"
        )

    def test_utana_a_kijeloles_URES(self, controller):
        _harmat_a_talcara(controller)
        controller.selectTrayIndex(1, False, False)
        controller.removeTraySelected()
        assert list(controller.traySelectedIndexes) == []

    def test_kijeloles_NELKUL_nem_tesz_semmit(self, controller):
        """Üres kijelöléssel a parancs ne ürítse ki a tálcát."""
        _harmat_a_talcara(controller)
        controller.removeTraySelected()
        assert controller.heldCount == 3
