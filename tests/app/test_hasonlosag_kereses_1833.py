"""Mintakép-alapú hasonlóság-keresés — #1833.

Az eredeti Picasa keresésének második rétegében (`searchoptions`) a
másodpéldány-keresés MELLETT ül egy mintakép-alapú hasonlóság-keresés:
kiválasztasz EGY képet, és a program megmutatja a hozzá hasonlókat. Nálunk
eddig csak az előbbi volt meg (`dedup/`), ami MÁS kérdésre felel: „mely
képek duplikátumai egymásnak?".

A korábbi motor (`dedup/phash.py` dHash + Hamming-távolság, `photo_hashes`
gyorstár) a #5744-ben a Picasa három jellemzőjére és rangsorára cserélődik.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg
from tests.support.py_blokk import fuggveny_torzs

_SIM = (
    Path(picasapy.app.__file__).parent / "similarity_controller.py"
).read_text(encoding="utf-8")
_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")
_MENU = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "PhotoContextMenu.qml"
).read_text(encoding="utf-8")
_TS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")


@pytest.fixture
def library(tmp_path):
    """Két EGYFORMA kép és egy harmadik, feltűnően más."""
    root = tmp_path / "kepek"
    (root / "mappa").mkdir(parents=True)
    make_jpeg(root / "mappa" / "a.jpg", size=(120, 90))
    make_jpeg(root / "mappa" / "a-masolat.jpg", size=(120, 90))
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


class TestAKereses:
    def test_a_minta_ONMAGAT_is_visszaadja(self, controller, library):
        """Egy kép önmagához 0 távolságra van — ha kimaradna, a nézet
        nem tartalmazná azt, amire a felhasználó rákeresett."""
        minta = str(library / "mappa" / "a.jpg")
        talalatok = controller._similar_records(minta)
        nevek = {r.name for r in talalatok}
        assert "a.jpg" in nevek

    def test_az_EGYFORMA_kepet_megtalalja(self, controller, library):
        minta = str(library / "mappa" / "a.jpg")
        nevek = {r.name for r in controller._similar_records(minta)}
        assert "a-masolat.jpg" in nevek

    def test_ismeretlen_mintara_URES(self, controller, tmp_path):
        assert controller._similar_records(str(tmp_path / "nincs.jpg")) == ()

    def test_a_gyorstarba_BEKERULNEK_a_harom_jellemzok(
        self, controller, library, tmp_path
    ):
        """Ettől lesz »legközelebb gyors«: a három jellemzőt cache-eli."""
        from picasapy.index import open_index

        controller._similar_records(str(library / "mappa" / "a.jpg"))
        with open_index(tmp_path / "index.db") as conn:
            darab = conn.execute(
                "SELECT COUNT(*) FROM photo_similarity"
            ).fetchone()[0]
        assert darab >= 3


class TestAJelzes:
    def test_indulaskor_NEM_epul(self, controller):
        assert controller.similarityUpdating is False

    def test_a_jelzes_finally_ban_all(self):
        """A jegy külön kiköti: kivételnél se ragadjon be."""
        blokk = fuggveny_torzs(_SIM, "def worker()")
        assert "finally:" in blokk
        assert "self._set_similarity_updating(False)" in blokk

    def test_a_jelzes_CSAK_akkor_megy_ki_ha_van_mit_epiteni(self):
        """Minden kereséskor felvillanó »épül« hazug állapot lenne."""
        blokk = fuggveny_torzs(_SIM, "hianyzo = [")
        assert "if hianyzo:" in blokk
        assert "self._set_similarity_updating(True)" in blokk


class TestAMinta:
    def test_kereses_utan_van_minta(self, controller, library):
        minta = str(library / "mappa" / "a.jpg")
        controller._on_similarity_ready(
            controller._similar_records(minta), minta
        )
        assert controller.similaritySample == minta

    def test_a_torles_VISSZAALLIT(self, controller, library):
        minta = str(library / "mappa" / "a.jpg")
        controller._on_similarity_ready(
            controller._similar_records(minta), minta
        )
        assert controller.filterActive is True

        controller.clearSimilarity()

        assert controller.similaritySample == ""
        assert controller.filterActive is False

    def test_minta_nelkul_a_torles_NEM_bant_semmit(self, controller):
        """A `clearsim` üresen ne söpörje el egy MÁSIK szűrő nézetét."""
        controller.showStarred()
        aktiv = controller.filterActive
        controller.clearSimilarity()
        assert controller.filterActive == aktiv


class TestASpecSzerintiRangsor:
    def test_rogzitett_kepkeszlet_sorrendje(self, controller, tmp_path, monkeypatch):
        """A mintakép, az azonos másolat és a távolabbi kép sorrendjét
        a hasonlósági rang és az időrang adja, nem az index sorrendje."""
        from dataclasses import replace

        from picasapy.index import open_index
        from picasapy.index import queries

        with open_index(tmp_path / "index.db") as conn:
            rekordok = queries.all_photos(conn)
        datumok = {
            "a.jpg": "2024-01-02T00:00:00",
            "a-masolat.jpg": "2024-01-01T00:00:00",
            "mas.jpg": "2024-01-04T00:00:00",
        }
        rögzített = tuple(
            replace(rekord, taken_at=datumok[rekord.name])
            for rekord in rekordok
        )
        monkeypatch.setattr(queries, "all_photos", lambda _conn: rögzített)

        találatok = controller._similar_records(
            str(Path(controller._roots[0]) / "mappa" / "a.jpg")
        )

        assert [rekord.name for rekord in találatok] == [
            "a.jpg",
            "a-masolat.jpg",
            "mas.jpg",
        ]

    def test_a_regi_kuszob_es_hamming_motor_nincs_a_keresesben(self):
        assert "HASONLOSAG_KUSZOB" not in _SIM
        assert "hamming_distance" not in _SIM

    def test_a_rankmax_alapertelmezese_1000(self):
        from picasapy.dedup.similarity import DEFAULT_RANK_MAX

        assert DEFAULT_RANK_MAX == 1000

    def test_a_preferences_rankmax_levagja_a_talalatokat(
        self, controller, library
    ):
        controller._get_settings().setValue("Preferences/RankMax", 2)

        találatok = controller._similar_records(
            str(library / "mappa" / "a.jpg")
        )

        assert len(találatok) == 2


class TestABekotes:
    def test_a_belepes_a_ctrl_f7_nem_a_helyi_menu(self):
        """#3468: az eredeti helyi menüjében hasonlóság-keresés NINCS
        (`ui-audit-context-menus.md` D) — a keresősáv Ctrl+F7 parancsa."""
        assert 'objectName: "contextMenuFindSimilar"' not in _MENU
        assert "signal findSimilarRequested()" not in _MENU
        assert 'objectName: "findSimilarShortcut"' in _MAIN
        assert 'sequence: "Ctrl+F7"' in _MAIN

    def test_a_belepes_ELJUT_a_vezerlohoz(self):
        """A #1153 osztálya: a belépő jelet ad, de senki nem veszi fel."""
        assert "controller.showSimilarTo(" in _MAIN

    def test_a_minta_savja_es_a_torles_ott_van(self):
        assert 'objectName: "similaritySampleLabel"' in _MAIN
        assert 'objectName: "similarityClearButton"' in _MAIN
        assert "controller.clearSimilarity()" in _MAIN

    def test_az_epules_savja_ott_van(self):
        assert 'objectName: "similarityUpdatingBar"' in _MAIN
        assert "controller.similarityUpdating" in _MAIN

    def test_a_frissites_NEM_dobja_vissza_a_mappaba(self):
        """A #1830 tanulsága: nézet-mód ág nélkül egy frissítés némán
        visszavinné a felhasználót."""
        ctl = (
            Path(picasapy.app.__file__).parent / "controller.py"
        ).read_text(encoding="utf-8")
        assert 'elif mode == "similar":' in ctl


class TestAFeliratok:
    @pytest.mark.parametrize(
        "angol,magyar",
        [
            ("Find Similar Pictures", "Keresés hasonló képekre"),
            ("Similarity Search Results", "Hasonlósági keresés eredménye"),
            ("Clear Sample", "Minta törlése"),
            (
                "Updating similarity database (will be fast next time)",
                "Hasonlósági adatbázis frissítése (legközelebb gyors lesz)",
            ),
        ],
    )
    def test_le_van_forditva(self, angol, magyar):
        assert f"<source>{angol}</source>" in _TS
        assert f"<translation>{magyar}</translation>" in _TS
