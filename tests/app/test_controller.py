"""AppController: mappa-választás, keresés, státusz, provider-regisztráció."""

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(
        root / "nyaralas" / "IMG_0001.jpg",
        taken_at="2025:05:01 07:00:00",
        caption="balatoni naplemente",
    )
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg")
    (root / "nyaralas" / ".picasa.ini").write_text("[IMG_0001.jpg]\nstar=yes\n")
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
    ctl = AppController(tmp_path / "index.db", (str(library),), provider)
    ctl._reload()
    return ctl


class TestController:
    def test_folders_loaded(self, controller):
        assert controller.folders.rowCount() == 1

    def test_select_folder_fills_grid_and_status(self, controller, library):
        # Picasa-stílus: "N képek   <hosszú dátum(tartomány)>   X,Y MB a lemezen"
        controller.selectFolder(str(library / "nyaralas"))
        assert controller.photos.rowCount() == 2
        assert controller.statusText.startswith("2 ")
        assert "2025" in controller.statusText
        assert "MB" in controller.statusText

    def test_photo_info_for_selection(self, controller, library):
        # Kijelöléskor a kék sáv a kép adatait mutatja (név, dátum,
        # felbontás képpontban, méret).
        controller.selectFolder(str(library / "nyaralas"))
        info = controller.photoInfo(0)
        assert "IMG_0001.jpg" in info
        assert "8x6" in info
        assert "2025" in info

    def test_photo_info_invalid_index_empty(self, controller):
        assert controller.photoInfo(-1) == ""
        assert controller.photoInfo(999) == ""

    def test_search(self, controller):
        controller.search("naplemente")
        assert controller.photos.rowCount() == 1

    def test_empty_search_restores_folder(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.search("naplemente")
        controller.search("  ")
        assert controller.photos.rowCount() == 2

    def test_show_starred(self, controller):
        controller.showStarred()
        assert controller.photos.rowCount() == 1
        assert controller.photos.photos[0].star

    def test_status_for_empty(self, controller):
        controller.search("nincstalalat")
        assert controller.statusText == "0 pictures"

    def test_sync_failure_reported_not_swallowed(self, qt_app, tmp_path):
        # Elavult/rossz gyökér (pl. Windows-útvonal a WatchedFolders-ből) nem
        # fagyaszthatja némán a UI-t: syncFailed + syncFinished is jön.
        from PySide6.QtCore import QEventLoop, QTimer
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "t"))
        ctl = AppController(
            tmp_path / "index.db", ("C:\\Users\\regi\\Pictures",), provider
        )
        errors = []
        finished = []
        ctl.syncFailed.connect(errors.append)
        ctl.syncFinished.connect(lambda: finished.append(True))
        loop = QEventLoop()
        ctl.syncFinished.connect(loop.quit)
        ctl.rescan()
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        assert finished
        assert errors and "Pictures" in errors[0]

    def test_rescan_not_reentrant(self, controller, monkeypatch):
        # Futó szinkron alatt az újabb rescan nem indíthat második írót.
        import threading

        started = []
        original = threading.Thread

        def counting_thread(*args, **kwargs):
            started.append(1)
            return original(*args, **kwargs)

        monkeypatch.setattr(threading, "Thread", counting_thread)
        monkeypatch.setattr(controller, "_sync_worker", lambda: None)
        controller._sync_running = True
        controller.rescan()
        assert started == []

    def test_sync_worker_emits(self, controller, qt_app):
        from PySide6.QtCore import QEventLoop, QTimer

        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller.rescan()
        QTimer.singleShot(5000, loop.quit)  # vészfék
        loop.exec()
        assert controller.folders.rowCount() == 1


class TestThumbnailProvider:
    def test_registered_photo_gets_thumbnail(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        photo = controller.photos.photos[0]
        image = controller._provider.requestImage(str(photo.id), None, None)
        assert not image.isNull()
        assert max(image.width(), image.height()) <= 32

    def test_unknown_id_gives_placeholder(self, controller):
        image = controller._provider.requestImage("99999", None, None)
        assert not image.isNull()
        assert image.width() == 16
