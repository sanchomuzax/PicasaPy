"""Mintakép-alapú hasonlóság-keresés — #1833.

Az eredeti Picasa keresésének második rétegében (`searchoptions`) a
másodpéldány-keresés MELLETT ül egy mintakép-alapú hasonlóság-keresés:
kiválasztasz EGY képet, és a program megmutatja a hozzá hasonlókat. Nálunk
eddig csak az előbbi volt meg (`dedup/`), ami MÁS kérdésre felel: „mely
képek duplikátumai egymásnak?".

A motor megvolt (`dedup/phash.py` dHash + Hamming-távolság, `photo_hashes`
gyorstár); a hiányzó rész a felhasználói kérdés és a beviteli út volt.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QSettings

from picasapy.app.similarity_controller import HASONLOSAG_KUSZOB
from support.jpeg_factory import make_jpeg

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

    def test_a_gyorstarba_BEKERULNEK_az_ujjlenyomatok(
        self, controller, library, tmp_path
    ):
        """Ettől lesz »legközelebb gyors«: a második keresés már nem
        számol újra."""
        from picasapy.index import open_index

        controller._similar_records(str(library / "mappa" / "a.jpg"))
        with open_index(tmp_path / "index.db") as conn:
            darab = conn.execute(
                "SELECT COUNT(*) FROM photo_hashes"
            ).fetchone()[0]
        assert darab >= 3


class TestAJelzes:
    def test_indulaskor_NEM_epul(self, controller):
        assert controller.similarityUpdating is False

    def test_a_jelzes_finally_ban_all(self):
        """A jegy külön kiköti: kivételnél se ragadjon be."""
        kezd = _SIM.index("def worker()")
        blokk = _SIM[kezd : kezd + 700]
        assert "finally:" in blokk
        assert "self._set_similarity_updating(False)" in blokk

    def test_a_jelzes_CSAK_akkor_megy_ki_ha_van_mit_epiteni(self):
        """Minden kereséskor felvillanó »épül« hazug állapot lenne."""
        kezd = _SIM.index("hianyzo = [")
        blokk = _SIM[kezd : kezd + 420]
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


class TestAKuszob:
    def test_nevvel_all_a_kodban(self):
        assert isinstance(HASONLOSAG_KUSZOB, int)

    def test_a_forras_KIMONDJA_hogy_sajat_dontes(self):
        """A jegy: a küszöb egy helyen, névvel, és a komment mondja ki,
        hogy saját döntés."""
        kezd = _SIM.index("HASONLOSAG_KUSZOB = ")
        elotte = _SIM[max(0, kezd - 900) : kezd]
        assert "SAJÁT DÖNTÉS" in elotte
        assert "nem mért érték" in elotte


class TestABekotes:
    def test_van_menutetel(self):
        assert 'objectName: "contextMenuFindSimilar"' in _MENU
        assert "signal findSimilarRequested()" in _MENU

    def test_a_jel_ELJUT_a_vezerlohoz(self):
        """A #1153 osztálya: a menü jelet ad, de senki nem veszi fel."""
        assert "onFindSimilarRequested" in _MAIN
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
                "A hasonlósági adatbázis épül (legközelebb gyors lesz)",
            ),
        ],
    )
    def test_le_van_forditva(self, angol, magyar):
        assert f"<source>{angol}</source>" in _TS
        assert f"<translation>{magyar}</translation>" in _TS
