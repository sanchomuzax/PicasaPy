"""#216: figyelt mappa eltávolítása FUTÓ szkennelés közben.

Három védvonal: (1) gyökerenkénti leállítási jelző (threading.Event) — a
futó sync a következő mappa-határon tisztán leáll; (2) az eltávolítás
azonnal takarít (index + nézet + panel); (3) a késői worker-jelzések az
eltávolított gyökérre nem frissítenek semmit.
"""

import threading

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    return ctl


class TestCancelSignal:
    def test_remove_sets_cancel_event(self, controller, library):
        controller.removeWatchedFolder(str(library))
        assert controller._cancel_event(str(library)).is_set()

    def test_progress_emitter_returns_stop_request(self, controller):
        ev = threading.Event()
        progress = controller._make_progress_emitter(should_stop=ev.is_set)
        assert progress("/x", 1, 2, 0) is False
        ev.set()
        assert progress("/x", 2, 2, 0) is True

    def test_running_sync_stops_on_remove(
        self, controller, library, qt_app, monkeypatch
    ):
        """A futó (háttérszálas) sync az eltávolítás utáni ELSŐ mappa-
        határon leáll — nem dolgozza fel a maradék mappákat."""
        from PySide6.QtCore import QEventLoop, QTimer

        import picasapy.app.controller as controller_module

        started = threading.Event()
        resume = threading.Event()
        processed = []

        def fake_sync_tree(conn, root, progress=None, **kwargs):
            # worker-szálon fut: megvárja, míg a főszál eltávolítja a
            # gyökeret, majd mappánként kérdezi a progress visszatérését
            started.set()
            assert resume.wait(timeout=5)
            for i in range(50):
                processed.append(i)
                if progress is not None and progress(
                    f"{root}/mappa-{i}", i + 1, 50, 0
                ):
                    return

        monkeypatch.setattr(controller_module, "sync_tree", fake_sync_tree)
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller.rescan()
        assert started.wait(timeout=5)
        controller.removeWatchedFolder(str(library))  # főszál: cancel-jelzés
        resume.set()
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        assert len(processed) == 1  # az első mappa-határon leállt

    def test_readd_clears_cancel_event(self, controller, library, qt_app):
        from PySide6.QtCore import QEventLoop, QTimer

        controller.removeWatchedFolder(str(library))
        assert controller._cancel_event(str(library)).is_set()
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller.addWatchedFolder(str(library))
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        assert controller._cancel_event(str(library)).is_set() is False


class TestRemoveCleansUp:
    def test_remove_cleans_index_and_view(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        assert controller.photos.rowCount() == 2
        controller.removeWatchedFolder(str(library))
        assert str(library) not in controller.watchedFolders
        assert controller.folders.folderCount == 0
        assert controller.photos.rowCount() == 0

    def test_remove_hides_import_panel(self, controller, library):
        # futó importot jelző panel: az eltávolítás azonnal eltünteti
        controller._on_sync_progress(str(library / "nyaralas"), 1, 2, 5)
        assert controller.importPanelVisible is True
        controller.removeWatchedFolder(str(library))
        assert controller.importPanelVisible is False


class TestLateSignals:
    def test_late_progress_after_remove_ignored(self, controller, library):
        """Eltávolítás UTÁN beérkező haladás-jelzés az eltávolított
        gyökérre: se panel, se állapot-frissítés."""
        controller.removeWatchedFolder(str(library))
        controller._import_forced = True
        controller._on_sync_progress(str(library / "nyaralas"), 1, 2, 5)
        assert controller.importPanelVisible is False
        assert controller.importFolderName == ""
        assert controller.importNewCount == 0

    def test_progress_for_watched_root_still_updates(self, controller, library):
        # a védelem nem nyeli el az érvényes (figyelt gyökér alatti) jelzést
        controller._on_sync_progress(str(library / "nyaralas"), 1, 2, 5)
        assert controller.importPanelVisible is True
        assert controller.importFolderName == "nyaralas"
        assert controller.importNewCount == 5
