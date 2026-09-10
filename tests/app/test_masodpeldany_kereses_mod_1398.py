"""A másodpéldány-keresés MÓD, nem panel — #1398.

Mérve: az „Eszközök ▸ Kísérleti ▸ Show Duplicate Files"
(`eMenuTools::ID_DUPES`) a keresési sáv rejtett `dupesearch` jelzőjét
kapcsolja be, tehát szűrt NÉZETBE visz; a módból a `viewallbutton` („Back
to View All", súgó „Exit Search Mode") vezet ki. A hasonlóság-keresés az
eredetiben nem létezik (öt eleme kikommentezve) — az a mi külön funkciónk
(#1833), és nem a mért menüparancson ül.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg
from tests.support.py_blokk import fuggveny_torzs

_DUPE = (
    Path(picasapy.app.__file__).parent / "dupe_search_controller.py"
).read_text(encoding="utf-8")
_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")
_MENU = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
).read_text(encoding="utf-8")
_IMPORT = (
    Path(picasapy.app.__file__).parent / "import_source_controller.py"
).read_text(encoding="utf-8")
_IMPORT_QML = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "ImportSourceDialog.qml"
).read_text(encoding="utf-8")
_TS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")


@pytest.fixture
def library(tmp_path):
    """Egy kép KÉT bitre azonos példányban, és egy harmadik, más kép."""
    root = tmp_path / "kepek"
    (root / "mappa").mkdir(parents=True)
    make_jpeg(root / "mappa" / "a.jpg", size=(120, 90))
    (root / "mappa" / "a-masolat.jpg").write_bytes(
        (root / "mappa" / "a.jpg").read_bytes()
    )
    make_jpeg(root / "mappa" / "mas.jpg", size=(90, 120), caption="más")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library / "mappa"))
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


class TestATalalatok:
    def test_a_ket_azonos_fajl_MINDKETTEJE_bekerul(self, controller):
        """A felhasználó azt akarja látni, MI kettőződött meg — tehát az
        „eredeti" sem maradhat ki."""
        nevek = {r.name for r in controller._duplicate_records()}
        assert nevek == {"a.jpg", "a-masolat.jpg"}

    def test_a_masik_kep_KIMARAD(self, controller):
        """Ismert negatív: enélkül a „minden kép találat" is átmenne."""
        nevek = {r.name for r in controller._duplicate_records()}
        assert "mas.jpg" not in nevek

    def test_masodpeldany_nelkul_URES(self, qt_app, tmp_path):
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache

        root = tmp_path / "egyedi"
        root.mkdir()
        make_jpeg(root / "egy.jpg", size=(120, 90))
        make_jpeg(root / "ketto.jpg", size=(90, 120), caption="más")
        with open_index(tmp_path / "i.db") as conn:
            sync_tree(conn, root)
        ctl = AppController(
            tmp_path / "i.db",
            (str(root),),
            ThumbnailProvider(ThumbnailCache(tmp_path / "th", size=32)),
            settings=QSettings(
                str(tmp_path / "s.ini"), QSettings.Format.IniFormat
            ),
            watched_file=tmp_path / "W.txt",
        )
        try:
            assert ctl._duplicate_records() == ()
        finally:
            assert ctl.waitForBackgroundWorkers(30.0)


class TestAMod:
    def test_a_mod_neve_dupes_es_a_szuro_AKTIV(self, controller):
        controller._on_dupes_ready(controller._duplicate_records())
        assert controller.viewModeName == "dupes"
        assert controller.filterActive is True

    def test_a_View_All_KIVEZET_a_modbol(self, controller):
        controller._on_dupes_ready(controller._duplicate_records())
        controller.clearFilter()
        assert controller.viewModeName == "folder"
        assert controller.filterActive is False

    def test_a_frissites_NEM_dobja_vissza_a_mappaba(self, controller):
        """A #1830/#1833 tanulsága: nézet-mód ág nélkül egy háttér-szinkron
        némán visszavinné a felhasználót a mappa-nézetbe."""
        controller._on_dupes_ready(controller._duplicate_records())
        controller._refresh_view()
        assert controller.viewModeName == "dupes"
        assert {r.name for r in controller._photos.photos} == {
            "a.jpg",
            "a-masolat.jpg",
        }

    def test_NEM_parbeszed(self):
        """A jegy kulcsa: a mért parancs módot kapcsol, nem dialógust nyit."""
        assert "onDuplicateSearchRequested" in _MAIN
        assert "controller.showDuplicateFiles()" in _MAIN
        # a menüpont a MÓDOT hívja, nem a kezelő-párbeszédet
        tetel = _MENU[_MENU.index('objectName: "menuToolsDedup"') :][:400]
        assert "duplicateSearchRequested()" in tetel
        assert "dedupRequested()" not in tetel


class TestAJelzes:
    def test_indulaskor_NEM_keres(self, controller):
        assert controller.dupeSearchScanning is False

    def test_a_jelzes_finally_ban_all(self):
        """Kivételnél se ragadjon be a „keresek" állapot."""
        blokk = fuggveny_torzs(_DUPE, "def worker()")
        assert "finally:" in blokk
        assert "self._set_dupe_scanning(False)" in blokk

    def test_van_savja_a_keresesnek(self):
        assert 'objectName: "dupeSearchScanningBar"' in _MAIN
        assert "controller.dupeSearchScanning" in _MAIN

    def test_a_sav_jelzi_a_modot(self):
        assert 'objectName: "dupeSearchLabel"' in _MAIN


class TestASajatFunkciok:
    def test_a_kezelo_parbeszed_MEGMARAD_sajat_jelolessel(self):
        """A #287 duplikátum-KEZELŐJE működő funkció (tilos elrontani), de
        az eredetiben nincs ilyen parancs — ezért a #1701 szerinti saját
        jelölést kapja, és nem a mért menüponton ül."""
        tetel = _MENU[_MENU.index('objectName: "menuToolsDedupManager"') :][:400]
        assert "sajat: true" in tetel
        assert "dedupRequested()" in tetel
        assert "dedupDialog.open()" in _MAIN

    def test_a_hasonlosag_kereses_NEM_menupont(self):
        """Az eredetiben a hasonlóság-keresés öt eleme kikommentezve — a
        menüsávba tehát nem kerülhet be Picasa-parancsként."""
        assert "findSimilarRequested" not in _MENU
        assert "Find Similar" not in _MENU


class TestAzImportalas:
    """A jegy negyedik pontja: az importáláskori másodpéldány-szűrés
    aszinkron, és van hozzá kapcsoló (`acquirepanel/excludedupesbutton`)."""

    def test_a_dupe_ellenorzes_a_HATTERSZALON_fut(self):
        blokk = fuggveny_torzs(_IMPORT, "duplicates = _duplikatumok(")
        assert "def worker()" in blokk

    def test_a_szkennelés_nem_a_GUI_szalon_fut(self):
        blokk = fuggveny_torzs(_IMPORT, "def scanSource(")
        assert "_start_background" in blokk or "self._start_background" in blokk

    def test_van_kizaro_kapcsolo(self):
        assert 'objectName: "importSourceAutoExcludeCheckBox"' in _IMPORT_QML
        assert "setAutoExclude(" in _IMPORT_QML


class TestAFeliratok:
    @pytest.mark.parametrize(
        "angol,magyar",
        [
            ("Back to View All", "Vissza az összes megtekintéséhez"),
            ("Duplicate Files", "Másodpéldányok"),
            ("Manage Duplicates...", "Másodpéldányok kezelése…"),
            (
                "Looking for duplicate files...",
                "Másodpéldányok keresése…",
            ),
        ],
    )
    def test_van_magyar_forditas(self, angol, magyar):
        assert f"<source>{angol}</source>" in _TS
        assert f"<translation>{magyar}</translation>" in _TS
