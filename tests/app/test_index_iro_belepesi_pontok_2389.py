"""#2389 — a két őrizetlen belépési pont: futó író mellett NINCS második.

A #1456 tesztjének mintája: a `_start_background` csak jegyzetel, így a
„még fut az első" állapot determinista, valódi időzítés nélkül.

⚠️ A #1456-tól ELTÉRŐEN itt a kihagyás NEM elfogadható végállapot. Mindkét
művelet közvetlen felhasználói kérés — ha némán kimaradna, a mappa nem
kerülne be a könyvtárba, és erről semmilyen jelzés nem születne. Ezért a
tesztek nemcsak azt állítják, hogy második író nem indul, hanem azt is,
hogy a munka a sorban MEGMARAD és le is fut.
"""

from __future__ import annotations

import pytest

from picasapy.app.index_writer_queue import IndexWriterQueue
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    for nev in ("nyaralas", "kollazsok", "uj"):
        (root / nev).mkdir(parents=True)
        make_jpeg(root / nev / "IMG_0001.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library / "nyaralas")
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    beallitas = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library / "nyaralas"),),
        provider,
        settings=beallitas,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


@pytest.fixture
def naplozo(controller, monkeypatch):
    """A `_start_background` csak jegyzetel — a szál NEM indul el."""
    inditasok: list[str | None] = []
    monkeypatch.setattr(
        controller,
        "_start_background",
        lambda *a, **k: inditasok.append(k.get("name")),
    )
    return inditasok


class TestNincsMasodikIro:
    def test_az_addWatchedFolder_nem_indit_masodikat(
        self, controller, library, naplozo
    ):
        controller._on_folders_dirty([str(library / "nyaralas")])
        assert naplozo == ["picasapy-sync-dirty"], "a felkészítő jelzés nem hatott"

        controller.addWatchedFolder(str(library / "uj"))

        assert "picasapy-sync-addfolder" not in naplozo, (
            "a mappa-hozzáadás SAJÁT írószálat indított a futó dirty-worker "
            f"mellé — indítások: {naplozo}"
        )
        assert naplozo.count(IndexWriterQueue.RUNNER_NAME) == 1, (
            f"pontosan egy sor-futtató járhat — indítások: {naplozo}"
        )

    def test_a_scanFolderOnce_nem_indit_masodikat(
        self, controller, library, naplozo
    ):
        controller._on_folders_dirty([str(library / "nyaralas")])
        assert naplozo == ["picasapy-sync-dirty"]

        controller.scanFolderOnce(str(library / "kollazsok"))

        assert "picasapy-sync-scanonce" not in naplozo, (
            f"a »Keresés egyszer« saját írószálat indított — {naplozo}"
        )
        assert naplozo.count(IndexWriterQueue.RUNNER_NAME) == 1, naplozo


class TestAMunkaNemVESZIKEL:
    def test_a_varolistara_kerult_mappa_a_sorban_marad(
        self, controller, library, naplozo
    ):
        """A #1456-os kihagyással szemben: itt a munka MEGMARAD.

        Ez a különbség a lényeg. Ha csak „nem indít második írót" lenne az
        állítás, azt a néma `return` is teljesítené — épp az a megoldás,
        amit a jegy kizár.
        """
        controller._on_folders_dirty([str(library / "nyaralas")])
        controller.addWatchedFolder(str(library / "uj"))

        assert controller._index_iro_sor.pending == 1, (
            "a felhasználó kérése eltűnt a sorból — ez a néma kihagyás, "
            "amit a #2389 kifejezetten kizár"
        )

    def test_ket_keres_kozul_egyik_sem_vesz_el(self, controller, library, naplozo):
        controller._on_folders_dirty([str(library / "nyaralas")])
        controller.addWatchedFolder(str(library / "uj"))
        controller.scanFolderOnce(str(library / "kollazsok"))

        assert naplozo.count(IndexWriterQueue.RUNNER_NAME) == 1, (
            "két felhasználói kérés is EGYETLEN futtatót kap — "
            f"indítások: {naplozo}"
        )
        assert controller._index_iro_sor.pending == 2, (
            f"a két kérésből {controller._index_iro_sor.pending} maradt meg"
        )


class TestASorAzIdegenIrotIsFigyeli:
    def test_futo_dirty_worker_idegen_ironak_szamit(self, controller):
        controller._dirty_running = True
        assert controller._fut_mas_index_iro() is True

        controller._dirty_running = False
        assert controller._fut_mas_index_iro() is False

    def test_a_sweep_es_a_sync_is_szamit(self, controller):
        controller._sync_running = True
        assert controller._fut_mas_index_iro() is True
        controller._sync_running = False

        controller._sweep_running = True
        assert controller._fut_mas_index_iro() is True
        controller._sweep_running = False
        assert controller._fut_mas_index_iro() is False
