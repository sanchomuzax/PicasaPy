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

    def test_viewer_info_breadcrumb_and_counter(self, controller, library):
        # Picasa: "mappa > név   dátum   SZxM képpont   méret   (i / N)"
        controller.selectFolder(str(library / "nyaralas"))
        info = controller.viewerInfo(0)
        assert info.startswith("nyaralas > IMG_0001.jpg")
        assert "(1 / 2)" in info

    def test_viewer_info_invalid_index_empty(self, controller):
        assert controller.viewerInfo(-1) == ""


class TestToggleStar:
    def test_star_written_to_ini_and_model(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(1)  # IMG_0002: nincs csillag
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text()
        assert "[IMG_0002.jpg]" in ini_text
        assert "star=yes" in ini_text.split("[IMG_0002.jpg]")[1]
        assert controller.photos.photos[1].star is True

    def test_unstar_removes_key(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(0)  # IMG_0001: csillag levétele
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text()
        # a kiürült szekció el is tűnik — csak az biztos, hogy csillag nincs
        assert "star=yes" not in ini_text
        assert controller.photos.photos[0].star is False

    def test_existing_ini_content_preserved(self, controller, library):
        # A kézzel írt (Picasa-féle) tartalom bitre pontosan megmarad.
        ini = library / "nyaralas" / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\nstar=yes\nbackuphash=36003\n\n"
            "[Picasa]\nname=Teszt\n"
        )
        from picasapy.index import open_index, sync_tree

        with open_index(controller._db_path) as conn:
            sync_tree(conn, library)
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(1)
        text = ini.read_text()
        assert "backuphash=36003" in text
        assert "name=Teszt" in text

    def test_backup_created(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(1)
        assert (library / "nyaralas" / ".picasa.ini.bak").exists()

    def test_creates_ini_when_missing(self, controller, library):
        ini = library / "nyaralas" / ".picasa.ini"
        ini.unlink()
        from picasapy.index import open_index, sync_tree

        with open_index(controller._db_path) as conn:
            sync_tree(conn, library)
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(0)
        assert "star=yes" in ini.read_text()

    def test_invalid_index_noop(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(99)  # nem dobhat

    def test_toggle_twice_restores_ini_bytes(self, controller, library):
        # Round-trip invariáns: fel + le = bitre azonos .picasa.ini.
        ini = library / "nyaralas" / ".picasa.ini"
        before = ini.read_bytes()
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(1)
        controller.toggleStar(1)
        assert ini.read_bytes() == before

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
