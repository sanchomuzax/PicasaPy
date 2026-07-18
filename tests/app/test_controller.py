"""AppController: mappa-választás, keresés, státusz, provider-regisztráció."""

import pytest
from PIL import Image

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
    (root / "nyaralas" / ".picasa.ini").write_text("[IMG_0001.jpg]\nstar=yes\n", encoding="utf-8")
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
    # elszigetelt QSettings — a rendszer valós PicasaPy-beállításait ne
    # szennyezze a teszt (session/lastFolder, view/thumbCaption).
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


class TestController:
    def test_folders_loaded(self, controller):
        # az évszám-elválasztó sorral együtt 2 sor, ebből 1 valódi mappa
        assert controller.folders.folderCount == 1

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
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        assert "[IMG_0002.jpg]" in ini_text
        assert "star=yes" in ini_text.split("[IMG_0002.jpg]")[1]
        assert controller.photos.photos[1].star is True

    def test_unstar_removes_key(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(0)  # IMG_0001: csillag levétele
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        # a kiürült szekció el is tűnik — csak az biztos, hogy csillag nincs
        assert "star=yes" not in ini_text
        assert controller.photos.photos[0].star is False

    def test_existing_ini_content_preserved(self, controller, library):
        # A kézzel írt (Picasa-féle) tartalom bitre pontosan megmarad.
        ini = library / "nyaralas" / ".picasa.ini"
        ini.write_text(
            "[IMG_0001.jpg]\nstar=yes\nbackuphash=36003\n\n"
            "[Picasa]\nname=Teszt\n"
        , encoding="utf-8")
        from picasapy.index import open_index, sync_tree

        with open_index(controller._db_path) as conn:
            sync_tree(conn, library)
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(1)
        text = ini.read_text(encoding="utf-8")
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
        assert "star=yes" in ini.read_text(encoding="utf-8")

    def test_invalid_index_noop(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStar(99)  # nem dobhat

    def test_rotate_right_writes_ini_and_model(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.rotateRight(0)
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        assert "rotate=rotate(1)" in ini_text
        assert controller.photos.photos[0].rotate_steps == 1

    def test_rotate_accumulates(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.rotateRight(0)
        controller.rotateRight(0)
        assert "rotate=rotate(2)" in (
            library / "nyaralas" / ".picasa.ini"
        ).read_text(encoding="utf-8")

    def test_rotate_left_wraps_to_three(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.rotateLeft(0)
        assert "rotate=rotate(3)" in (
            library / "nyaralas" / ".picasa.ini"
        ).read_text(encoding="utf-8")

    def test_full_circle_removes_key(self, controller, library):
        # 4x jobbra = alaphelyzet → a kulcs törlődik (tiszta round-trip).
        ini = library / "nyaralas" / ".picasa.ini"
        before = ini.read_bytes()
        controller.selectFolder(str(library / "nyaralas"))
        for _ in range(4):
            controller.rotateRight(0)
        assert "rotate=" not in ini.read_text(encoding="utf-8")
        assert ini.read_bytes() == before

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

    def test_star_filter_toggles_back_to_folder(self, controller, library):
        # Picasa: a szűrő újra-kattintásra kikapcsol, vissza a mappához.
        controller.selectFolder(str(library / "nyaralas"))
        controller.showStarred()
        assert controller.filterActive is True
        controller.clearFilter()
        assert controller.filterActive is False
        assert controller.photos.rowCount() == 2  # a mappa teljes tartalma

    def test_reload_preserves_search(self, controller, library):
        # #38: a háttér-sync (watcher/rescan) végén futó _reload nem
        # dobhatja el az aktív keresést — a szűrt nézet marad.
        controller.selectFolder(str(library / "nyaralas"))
        controller.search("naplemente")
        assert controller.photos.rowCount() == 1
        controller._reload()
        assert controller.photos.rowCount() == 1

    def test_reload_preserves_starred_filter(self, controller, library):
        # #38 társ-eset: a csillag-szűrő is élje túl a háttér-sync reloadot.
        controller.selectFolder(str(library / "nyaralas"))
        controller.showStarred()
        assert controller.photos.rowCount() == 1
        controller._reload()
        assert controller.photos.rowCount() == 1
        assert controller.filterActive is True

    def test_cleared_search_resets_view_mode(self, controller, library):
        # Üres keresés után a nézet-mód a mappa — egy későbbi _refresh_view
        # (pl. csillagozás) nem hozhatja vissza a régi keresést.
        controller.selectFolder(str(library / "nyaralas"))
        controller.search("naplemente")
        controller.search("")
        controller._refresh_view()
        assert controller.photos.rowCount() == 2

    def test_filter_status_text(self, controller, library):
        # Zöld sáv (Picasa): "N mappa / M kép látható (x,xxx másodperc) Y GB"
        controller.selectFolder(str(library / "nyaralas"))
        controller.showStarred()
        status = controller.filterStatusText
        assert "1 " in status  # 1 mappa és 1 kép
        assert "/" in status
        assert "(" in status and ")" in status  # eltelt idő zárójelben
        assert "GB" in status

    def test_clear_filter_without_folder(self, controller):
        controller.showStarred()
        controller.clearFilter()  # nincs korábbi mappa — nem dobhat
        assert controller.filterActive is False

    def test_status_for_empty(self, controller):
        controller.search("nincstalalat")
        assert controller.statusText == "0 pictures"

    def test_sync_failure_reported_not_swallowed(self, qt_app, tmp_path):
        # Elavult/rossz gyökér (pl. Windows-útvonal a WatchedFolders-ből) nem
        # fagyaszthatja némán a UI-t: syncFailed + syncFinished is jön.
        from PySide6.QtCore import QEventLoop, QSettings, QTimer
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.thumbs import ThumbnailCache

        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "t"))
        settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
        ctl = AppController(
            tmp_path / "index.db",
            ("C:\\Users\\regi\\Pictures",),
            provider,
            settings=settings,
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
        assert controller.folders.folderCount == 1


class TestSetCaption:
    def test_jpeg_caption_written_to_iptc_and_model(self, controller, library):
        # Picasa-szabály: JPEG-nél a felirat az IPTC-be kerül, nem az ini-be.
        from picasapy.metadata import read_file_metadata

        controller.selectFolder(str(library / "nyaralas"))
        controller.setCaption(1, "próba felirat")  # IMG_0002.jpg
        photo_path = library / "nyaralas" / "IMG_0002.jpg"
        assert read_file_metadata(photo_path).caption == "próba felirat"
        assert controller.photos.photos[1].caption == "próba felirat"

    def test_jpeg_caption_cleared(self, controller, library):
        from picasapy.metadata import read_file_metadata

        controller.selectFolder(str(library / "nyaralas"))
        controller.setCaption(1, "próba felirat")
        controller.setCaption(1, "")
        photo_path = library / "nyaralas" / "IMG_0002.jpg"
        assert read_file_metadata(photo_path).caption is None
        assert controller.photos.photos[1].caption is None

    def test_non_jpeg_caption_written_to_ini(self, controller, library):
        # Nem-JPEG (pl. PNG) esetén a Picasa a .picasa.ini-be írja a feliratot.
        from picasapy.index import open_index, sync_tree

        png_path = library / "nyaralas" / "kep.png"
        Image.new("RGB", (4, 4), "blue").save(png_path, "PNG")
        with open_index(controller._db_path) as conn:
            sync_tree(conn, library)
        controller.selectFolder(str(library / "nyaralas"))
        row = next(
            i
            for i, photo in enumerate(controller.photos.photos)
            if photo.name == "kep.png"
        )
        controller.setCaption(row, "png felirat")
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        assert "[kep.png]" in ini_text
        assert "caption=png felirat" in ini_text.split("[kep.png]")[1]
        row = next(
            i
            for i, photo in enumerate(controller.photos.photos)
            if photo.name == "kep.png"
        )
        assert controller.photos.photos[row].caption == "png felirat"

    def test_invalid_index_noop(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.setCaption(99, "nem történhet")  # nem dobhat


class TestSessionRestore:
    def _settings(self, tmp_path):
        from PySide6.QtCore import QSettings

        return QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)

    def _controller(self, tmp_path, library, settings):
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        return AppController(
            tmp_path / "index.db",
            (str(library),),
            provider,
            settings=settings,
        )

    def test_restore_selects_saved_folder(self, qt_app, tmp_path, library):
        from picasapy.index import open_index

        settings = self._settings(tmp_path)
        saved = str(library / "nyaralas")
        settings.setValue("session/lastFolder", saved)
        settings.sync()
        ctl = self._controller(tmp_path, library, settings)
        with open_index(ctl._db_path) as conn:
            ctl._folders.load(conn)
        ctl.restoreSession()
        assert ctl.currentFolder == saved
        assert ctl.photos.rowCount() == 2

    def test_restore_falls_back_to_first_when_saved_missing(
        self, qt_app, tmp_path, library
    ):
        settings = self._settings(tmp_path)
        settings.setValue("session/lastFolder", str(library / "nincs-ilyen"))
        settings.sync()
        ctl = self._controller(tmp_path, library, settings)
        ctl._reload()
        ctl.restoreSession()
        assert ctl.currentFolder == str(library / "nyaralas")

    def test_restore_falls_back_to_first_when_nothing_saved(
        self, qt_app, tmp_path, library
    ):
        settings = self._settings(tmp_path)
        ctl = self._controller(tmp_path, library, settings)
        ctl._reload()
        ctl.restoreSession()
        assert ctl.currentFolder == str(library / "nyaralas")

    def test_select_folder_persists_choice(self, qt_app, tmp_path, library):
        settings = self._settings(tmp_path)
        ctl = self._controller(tmp_path, library, settings)
        target = str(library / "nyaralas")
        ctl.selectFolder(target)
        settings.sync()
        assert settings.value("session/lastFolder") == target


class TestThumbCaptionMode:
    def test_default_none(self, controller):
        assert controller.thumbCaptionMode == "none"

    def test_set_mode_persists(self, qt_app, tmp_path, library):
        from picasapy.app.controller import AppController
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import open_index, sync_tree
        from picasapy.thumbs import ThumbnailCache
        from PySide6.QtCore import QSettings

        settings = QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        )
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
        ctl = AppController(
            tmp_path / "index.db",
            (str(library),),
            provider,
            settings=settings,
        )
        ctl.setThumbCaptionMode("filename")
        settings.sync()
        assert ctl.thumbCaptionMode == "filename"
        assert settings.value("view/thumbCaption") == "filename"

    def test_invalid_mode_ignored(self, controller):
        controller.setThumbCaptionMode("resolution")
        controller.setThumbCaptionMode("nonsense")
        assert controller.thumbCaptionMode == "resolution"


class TestWatchedFolderManagement:
    def test_add_watched_folder_persists_and_indexes(
        self, controller, library, tmp_path, qt_app
    ):
        from PySide6.QtCore import QEventLoop, QTimer
        from picasapy.scanner import read_watched_folders

        other = tmp_path / "masik"
        (other / "m").mkdir(parents=True)
        make_jpeg(other / "m" / "x.jpg")
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        from PySide6.QtCore import QUrl

        # URL-alakban adjuk át (a QML FolderDialog is azt ad) —
        # platformhelyesen képezve, Windowson is érvényes formával
        controller.addWatchedFolder(QUrl.fromLocalFile(str(other)).toString())
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        assert str(other) in controller.watchedFolders
        assert str(other) in read_watched_folders(controller._watched_file)
        assert controller.folders.folderCount >= 2

    def test_add_duplicate_ignored(self, controller, library):
        before = list(controller.watchedFolders)
        controller.addWatchedFolder(str(library))
        assert list(controller.watchedFolders) == before

    def test_remove_watched_folder_cleans_index(self, controller, library):
        controller.removeWatchedFolder(str(library))
        assert str(library) not in controller.watchedFolders
        assert controller.folders.folderCount == 0
        assert controller.photos.rowCount() == 0  # az aktuális nézet is ürül


class TestLiveWatch:
    def test_dirty_folders_synced_into_index(self, controller, library, qt_app):
        # A watcher-jelzés (más szálból) a jelzett mappákat szinkronizálja,
        # és a nézet frissül — az új kép megjelenik.
        from PySide6.QtCore import QEventLoop, QTimer

        controller.selectFolder(str(library / "nyaralas"))
        assert controller.photos.rowCount() == 2
        make_jpeg(library / "nyaralas" / "IMG_9999.jpg")
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller._on_folders_dirty([str(library / "nyaralas")])
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()
        assert controller.photos.rowCount() == 3

    def test_shutdown_without_start_is_safe(self, controller):
        controller.shutdown()  # watcher nélkül sem dobhat


class TestBatchOperations:
    def test_toggle_star_many_stars_all(self, controller, library):
        # Picasa: a tálca-csillag a teljes kijelölésre hat — ha van még
        # csillagozatlan, mindet csillagozza.
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStarMany([0, 1])  # a 0-s már csillagos
        assert all(p.star for p in controller.photos.photos)

    def test_toggle_star_many_unstars_when_all_starred(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStarMany([0, 1])
        controller.toggleStarMany([0, 1])
        assert not any(p.star for p in controller.photos.photos)

    def test_rotate_many(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.rotateRightMany([0, 1])
        assert [p.rotate_steps for p in controller.photos.photos] == [1, 1]

    def test_batch_single_ini_write(self, controller, library):
        # A kötegelt művelet mappánként EGY írás: a backup a művelet
        # ELŐTTI teljes állapot (nem köztes), tehát bitre azonos vele.
        controller.selectFolder(str(library / "nyaralas"))
        ini = library / "nyaralas" / ".picasa.ini"
        before = ini.read_bytes()
        controller.toggleStarMany([0, 1])
        bak = library / "nyaralas" / ".picasa.ini.bak"
        assert bak.read_bytes() == before

    def test_batch_invalid_rows_ignored(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleStarMany([-1, 99])  # nem dobhat


class TestThumbnailProvider:
    def test_registered_photo_gets_thumbnail(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        photo = controller.photos.photos[0]
        image = controller._provider.requestImage(str(photo.id), None, None)
        assert not image.isNull()
        assert max(image.width(), image.height()) <= 32

    def test_rotated_photo_thumb_dims_swapped(self, controller, library):
        # rotate_steps=1 → a provider elforgatva adja vissza a thumbnailt.
        controller.selectFolder(str(library / "nyaralas"))
        photo = controller.photos.photos[0]
        base = controller._provider.requestImage(f"{photo.id}?r=0", None, None)
        controller.rotateRight(0)
        rotated_photo = controller.photos.photos[0]
        rotated = controller._provider.requestImage(
            f"{rotated_photo.id}?r=1", None, None
        )
        assert (rotated.width(), rotated.height()) == (base.height(), base.width())

    def test_unknown_id_gives_placeholder(self, controller):
        image = controller._provider.requestImage("99999", None, None)
        assert not image.isNull()
        assert image.width() == 16


class TestFolderDescription:
    """A mappa-leírás Picasa-kompatibilis mentése/olvasása:
    `[Picasa]/description` kulcs a `.picasa.ini`-ben."""

    def test_set_description_written_to_ini_and_property(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.setFolderDescription("nyári képek")
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        assert "[Picasa]" in ini_text
        assert "description=nyári képek" in ini_text
        assert controller.folderDescription == "nyári képek"

    def test_clearing_description_removes_key(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.setFolderDescription("nyári képek")
        controller.setFolderDescription("")
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        assert "description=" not in ini_text
        assert controller.folderDescription == ""

    def test_reselecting_folder_reloads_description(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.setFolderDescription("nyári képek")
        controller.selectFolder(str(library / "nyaralas"))
        assert controller.folderDescription == "nyári képek"

    def test_existing_photo_keys_preserved(self, controller, library):
        # star=yes (IMG_0001.jpg) bitre pontosan megmarad a leírás-írás után.
        controller.selectFolder(str(library / "nyaralas"))
        controller.setFolderDescription("nyári képek")
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(encoding="utf-8")
        assert "[IMG_0001.jpg]" in ini_text
        assert "star=yes" in ini_text.split("[IMG_0001.jpg]")[1]


class TestSearchSuggestionsSlot:
    def test_returns_folder_dicts(self, controller, library):
        # #7 bekötés: a QML-nek dict-lista kell (kind/name/count/param).
        result = controller.searchSuggestions("nyar")
        assert [(s["kind"], s["name"]) for s in result] == [("folder", "nyaralas")]
        assert result[0]["param"].endswith("nyaralas")
        assert result[0]["count"] == 2

    def test_empty_query_empty_list(self, controller):
        assert controller.searchSuggestions("  ") == []

    def test_albums_deferred_to_issue_9(self, controller, library):
        # Album-javaslat egyelőre nem kerül a legördülőbe: a kiválasztása
        # csak a virtuális albumok UI-jával (#9) lesz értelmes.
        (library / "nyaralas" / ".picasa.ini").write_text(
            "[.album:aabb01]\nname=nyari valogatas\n"
            "[IMG_0001.jpg]\nalbums=aabb01\nstar=yes\n",
            encoding="utf-8",
        )
        result = controller.searchSuggestions("nyari")
        assert all(s["kind"] == "folder" for s in result)
