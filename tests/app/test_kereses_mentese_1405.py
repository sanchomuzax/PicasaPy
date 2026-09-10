"""A keresés mentése albumként (#1405).

MÉRVE (`0x005d86a0`, 362 bájt, spec `picasa-menu-parancsok-viselkedes.md`
35.5): a parancs az aktív keresés TELJES találatát albumba mentette, és
**csak 1000 találat FELETT** kért megerősítést („This will create an album
with more than 1000 images."), a gombja pedig a művelet neve volt („Create
Album"), nem Igen/Nem. 1000 alatt csendben létrejött az album.

A menütétel helye szintén mérve: az `eMenuTools` 36 kulcsát egyetlen
menüépítő függvény használja, és ott az `ID_SAVESEARCH` a **Kísérleti**
almenü negyedik tétele.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg

from picasapy.app.photo_ops_controller import PhotoOpsMixin


class TestAKuszob:
    def test_a_kuszob_a_MERT_ezer(self):
        """Ha valaki „szebb" számra írja át, itt bukik el."""
        assert PhotoOpsMixin.SAVE_SEARCH_CONFIRM_OVER == 1000


class TestAMentes:
    @pytest.fixture
    def vezerlo(self, qt_app, tmp_path):
        from PySide6.QtCore import QSettings

        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache

        gyoker = tmp_path / "kepek"
        gyoker.mkdir()
        make_jpeg(gyoker / "a.jpg")
        make_jpeg(gyoker / "b.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, gyoker)
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        ctl = AppController(
            tmp_path / "index.db",
            (str(gyoker),),
            provider,
            settings=settings,
            watched_file=tmp_path / "WatchedFolders.txt",
        )
        yield ctl
        ctl.shutdown()

    def test_kereses_nelkul_nem_mentheto(self, vezerlo):
        """Mappa-nézetben a menütétel szürke: nincs mit menteni."""
        assert vezerlo.canSaveSearch is False
        assert vezerlo.saveSearchAsAlbum() == ""

    def test_kereses_utan_mentheto_es_albumot_ad(self, vezerlo):
        vezerlo.search("a")
        assert vezerlo.canSaveSearch is True, (
            "keresés után a menütételnek élnie kell"
        )

        token = vezerlo.saveSearchAsAlbum()

        assert token, "a mentés nem adott album-tokent"
        nevek = [a["name"] for a in vezerlo.albums]
        assert "a" in nevek, (
            f"az album neve a keresés szövege legyen: {nevek}"
        )

    def test_ures_talalat_nem_mentheto(self, vezerlo):
        vezerlo.search("nincs-ilyen-kep-xyz")
        assert vezerlo.canSaveSearch is False, (
            "üres keresésből nem lesz album (a menütétel szürke)"
        )
