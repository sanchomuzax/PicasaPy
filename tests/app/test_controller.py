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


class TestPropertiesOf:
    """#13: a Tulajdonságok-panel adatai — csak olvasás."""

    def _labels(self, entries):
        return [e["label"] for e in entries]

    def test_basic_fields_present(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        entries = controller.propertiesOf(0)
        labels = self._labels(entries)
        values = {e["label"]: e["value"] for e in entries}
        assert "File name" in labels
        assert values["File name"] == "IMG_0001.jpg"
        assert values["Folder"] == str(library / "nyaralas")
        assert "File size" in labels
        assert "Dimensions" in labels
        assert "Date taken" in labels  # a fixture taken_at-ot ír

    def test_exif_camera_fields(self, controller, library, tmp_path):
        import piexif
        from picasapy.index import open_index, sync_tree
        from PIL import Image

        path = library / "nyaralas" / "gep.jpg"
        Image.new("RGB", (8, 6), "red").save(path, "JPEG")
        piexif.insert(
            piexif.dump({
                "0th": {piexif.ImageIFD.Make: b"Canon",
                        piexif.ImageIFD.Model: b"EOS 550D"},
                "Exif": {piexif.ExifIFD.ExposureTime: (1, 125),
                         piexif.ExifIFD.FNumber: (28, 10),
                         piexif.ExifIFD.ISOSpeedRatings: 400,
                         piexif.ExifIFD.WhiteBalance: 0},
            }),
            str(path),
        )
        with open_index(controller._db_path) as conn:
            sync_tree(conn, library)
        controller.selectFolder(str(library / "nyaralas"))
        row = next(
            i for i, p in enumerate(controller.photos.photos)
            if p.name == "gep.jpg"
        )
        values = {e["label"]: e["value"] for e in controller.propertiesOf(row)}
        assert values["Camera"] == "Canon EOS 550D"
        assert values["Exposure"] == "1/125 s"
        assert values["Aperture"] == "f/2.8"
        assert values["ISO"] == "400"
        assert values["White balance"] == "Automatic"

    def test_invalid_row_empty(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        assert controller.propertiesOf(-1) == []
        assert controller.propertiesOf(99) == []


class TestHiddenPictures:
    """#17: Elrejtés/Megjelenítés — hidden=yes az ini-ben, a rács alapból
    nem mutatja a rejtettet, Nézet→Rejtett képek kapcsolóval igen."""

    def test_hide_writes_ini_and_disappears_from_grid(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleHiddenRows([1])  # IMG_0002.jpg
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(
            encoding="utf-8"
        )
        assert "hidden=yes" in ini_text.split("[IMG_0002.jpg]")[1]
        assert [p.name for p in controller.photos.photos] == ["IMG_0001.jpg"]

    def test_show_hidden_reveals_dimmed_row(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleHiddenRows([1])
        controller.setShowHidden(True)
        names = [p.name for p in controller.photos.photos]
        assert names == ["IMG_0001.jpg", "IMG_0002.jpg"]
        assert controller.photos.photos[1].hidden is True
        assert controller.photos.itemAt(1)["hidden"] is True

    def test_unhide_removes_ini_key(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleHiddenRows([1])
        controller.setShowHidden(True)
        controller.toggleHiddenRows([1])  # most már látszik, sorszáma 1
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(
            encoding="utf-8"
        )
        assert "hidden=yes" not in ini_text
        controller.setShowHidden(False)
        assert len(controller.photos.photos) == 2

    def test_mixed_selection_hides_all(self, controller, library):
        # Picasa-viselkedés (mint a csillagnál): ha van még nem rejtett a
        # kijelöltek közt, mindet elrejti
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleHiddenRows([0, 1])
        assert controller.photos.photos == ()

    def test_show_hidden_persisted(self, controller, library):
        controller.setShowHidden(True)
        assert controller.showHidden is True
        settings = controller._get_settings()
        assert settings.value("view/showHidden") in (True, "true")

    def test_hidden_excluded_from_search_by_default(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.toggleHiddenRows([0])  # IMG_0001, caption: naplemente
        controller.search("IMG_0001")
        assert controller.photos.photos == ()
        controller.setShowHidden(True)
        controller.search("IMG_0001")
        assert [p.name for p in controller.photos.photos] == ["IMG_0001.jpg"]


class TestVideoRotationGuard:
    """#103: videóra a forgatás nem írhat rotate= kulcsot az ini-be."""

    def _with_video(self, controller, library):
        from picasapy.index import open_index, sync_tree

        (library / "nyaralas" / "film.mp4").write_bytes(b"\x00" * 32)
        with open_index(controller._db_path) as conn:
            sync_tree(conn, library)
        controller.selectFolder(str(library / "nyaralas"))
        return next(
            i
            for i, photo in enumerate(controller.photos.photos)
            if photo.name == "film.mp4"
        )

    def test_single_rotate_on_video_noop(self, controller, library):
        row = self._with_video(controller, library)
        controller.rotateRight(row)
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(
            encoding="utf-8"
        )
        assert "film.mp4" not in ini_text
        assert controller.photos.photos[row].rotate_steps == 0

    def test_mixed_selection_rotates_only_photos(self, controller, library):
        video_row = self._with_video(controller, library)
        photo_rows = [
            i
            for i, photo in enumerate(controller.photos.photos)
            if photo.kind == "photo"
        ]
        controller.rotateRightMany([*photo_rows, video_row])
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(
            encoding="utf-8"
        )
        assert "film.mp4" not in ini_text
        for row in photo_rows:
            assert controller.photos.photos[row].rotate_steps == 1
        assert controller.photos.photos[video_row].rotate_steps == 0

    def test_video_only_selection_rotate_many_noop(self, controller, library):
        video_row = self._with_video(controller, library)
        before = (library / "nyaralas" / ".picasa.ini").read_text(
            encoding="utf-8"
        )
        controller.rotateLeftMany([video_row])
        after = (library / "nyaralas" / ".picasa.ini").read_text(
            encoding="utf-8"
        )
        assert after == before


class TestKeywords:
    """#12: kulcsszavak (címkék) hozzáadása/törlése a kijelölésre.

    Picasa-szabály: JPEG-nél az IPTC Keywords (2:25) a tár, más
    formátumnál a .picasa.ini `keywords=` CSV kulcsa."""

    def _png_row(self, controller, library):
        from picasapy.index import open_index, sync_tree

        png_path = library / "nyaralas" / "kep.png"
        Image.new("RGB", (4, 4), "blue").save(png_path, "PNG")
        with open_index(controller._db_path) as conn:
            sync_tree(conn, library)
        controller.selectFolder(str(library / "nyaralas"))
        return next(
            i
            for i, photo in enumerate(controller.photos.photos)
            if photo.name == "kep.png"
        )

    def test_add_keyword_jpeg_written_to_iptc_and_model(self, controller, library):
        from picasapy.metadata import read_file_metadata

        controller.selectFolder(str(library / "nyaralas"))
        controller.addKeywordToRows([1], "balaton")  # IMG_0002.jpg
        photo_path = library / "nyaralas" / "IMG_0002.jpg"
        assert read_file_metadata(photo_path).keywords == ("balaton",)
        assert controller.photos.photos[1].keywords == "balaton"

    def test_add_second_keyword_keeps_first(self, controller, library):
        from picasapy.metadata import read_file_metadata

        controller.selectFolder(str(library / "nyaralas"))
        controller.addKeywordToRows([1], "balaton")
        controller.addKeywordToRows([1], "nyár")
        photo_path = library / "nyaralas" / "IMG_0002.jpg"
        assert read_file_metadata(photo_path).keywords == ("balaton", "nyár")

    def test_duplicate_add_ignored_case_insensitive(self, controller, library):
        from picasapy.metadata import read_file_metadata

        controller.selectFolder(str(library / "nyaralas"))
        controller.addKeywordToRows([1], "Balaton")
        controller.addKeywordToRows([1], "balaton")
        photo_path = library / "nyaralas" / "IMG_0002.jpg"
        assert read_file_metadata(photo_path).keywords == ("Balaton",)

    def test_remove_keyword_jpeg(self, controller, library):
        from picasapy.metadata import read_file_metadata

        controller.selectFolder(str(library / "nyaralas"))
        controller.addKeywordToRows([1], "balaton")
        controller.addKeywordToRows([1], "nyár")
        controller.removeKeywordFromRows([1], "balaton")
        photo_path = library / "nyaralas" / "IMG_0002.jpg"
        assert read_file_metadata(photo_path).keywords == ("nyár",)
        assert controller.photos.photos[1].keywords == "nyár"

    def test_add_keyword_png_written_to_ini(self, controller, library):
        row = self._png_row(controller, library)
        controller.addKeywordToRows([row], "kék")
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(
            encoding="utf-8"
        )
        assert "[kep.png]" in ini_text
        assert "keywords=kék" in ini_text.split("[kep.png]")[1]

    def test_remove_last_keyword_png_removes_ini_key(self, controller, library):
        row = self._png_row(controller, library)
        controller.addKeywordToRows([row], "kék")
        controller.removeKeywordFromRows([row], "kék")
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(
            encoding="utf-8"
        )
        assert "keywords=" not in ini_text

    def test_add_to_many_rows(self, controller, library):
        from picasapy.metadata import read_file_metadata

        controller.selectFolder(str(library / "nyaralas"))
        controller.addKeywordToRows([0, 1], "közös")
        for name in ("IMG_0001.jpg", "IMG_0002.jpg"):
            path = library / "nyaralas" / name
            assert "közös" in read_file_metadata(path).keywords

    def test_keywords_of_rows_union_sorted(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.addKeywordToRows([0], "zebra")
        controller.addKeywordToRows([1], "alma")
        controller.addKeywordToRows([1], "zebra")
        assert controller.keywordsOfRows([0, 1]) == ["alma", "zebra"]

    def test_comma_stripped_from_keyword(self, controller, library):
        # a CSV-tár (ini/index) miatt a vessző nem lehet kulcsszó része
        from picasapy.metadata import read_file_metadata

        controller.selectFolder(str(library / "nyaralas"))
        controller.addKeywordToRows([1], "egy, kettő")
        photo_path = library / "nyaralas" / "IMG_0002.jpg"
        assert read_file_metadata(photo_path).keywords == ("egy kettő",)

    def test_empty_or_invalid_input_noop(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.addKeywordToRows([1], "   ")
        controller.addKeywordToRows([99], "rossz sor")  # nem dobhat
        controller.removeKeywordFromRows([1], "nincs ilyen")
        assert controller.photos.photos[1].keywords is None

    def test_search_finds_added_keyword(self, controller, library):
        # a DoD kereshetőséget kér: a frissen írt címke azonnal találat
        controller.selectFolder(str(library / "nyaralas"))
        controller.addKeywordToRows([1], "vitorlás")
        controller.search("vitorlás")
        assert [p.name for p in controller.photos.photos] == ["IMG_0002.jpg"]


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

    def test_add_folder_with_accents_and_spaces(self, controller, tmp_path):
        # #58: klasszikus Windows-mappa (ékezet + szóköz) becsatolása a
        # FolderDialog százalék-kódolt URL-alakjából sem bukhat el.
        from PySide6.QtCore import QEventLoop, QTimer, QUrl

        target = tmp_path / "Régi képek 2020"
        target.mkdir()
        make_jpeg(target / "kep.jpg")
        url = bytes(QUrl.fromLocalFile(str(target)).toEncoded()).decode("ascii")
        assert "%20" in url and "%C3" in url  # tényleg kódolt alakot adunk át
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller.addWatchedFolder(url)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        assert str(target) in controller.watchedFolders

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

    def test_cache_error_gives_placeholder_and_log(
        self, controller, library, monkeypatch, caplog
    ):
        # #66: a betöltő szálra kiszökő kivétel a kérést némán megölné —
        # hibánál placeholder jár, a részletek a logba kerülnek.
        import logging

        controller.selectFolder(str(library / "nyaralas"))
        photo = controller.photos.photos[0]
        monkeypatch.setattr(
            controller._provider._cache,
            "get_or_create",
            lambda *a, **k: (_ for _ in ()).throw(OSError("NAS-hiba")),
        )
        with caplog.at_level(logging.ERROR, "picasapy.app.thumbnail_provider"):
            image = controller._provider.requestImage(str(photo.id), None, None)
        assert not image.isNull() and image.width() == 16
        assert "thumbnail-render hiba" in caplog.text

    def test_failed_thumbnail_logged_not_silent(
        self, controller, library, monkeypatch, caplog
    ):
        # Ha a forrás nem dekódolható (a cache None-t ad), az ne néma
        # szürkeség legyen: warning a logba, placeholder a rácsra.
        import logging

        controller.selectFolder(str(library / "nyaralas"))
        photo = controller.photos.photos[0]
        monkeypatch.setattr(
            controller._provider._cache, "get_or_create", lambda *a, **k: None
        )
        with caplog.at_level(logging.WARNING, "picasapy.app.thumbnail_provider"):
            image = controller._provider.requestImage(str(photo.id), None, None)
        assert not image.isNull() and image.width() == 16
        assert "thumbnail nem készült el" in caplog.text


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


class TestLibraryFeed:
    """#64: a rács nem mappánkénti — az EGÉSZ könyvtár egyetlen görgethető
    feed, a bal hasáb mappa-sorrendjében, mappa-csoportokra bontva."""

    @pytest.fixture
    def two_folders(self, controller, library, tmp_path):
        from picasapy.index import open_index, sync_tree

        (library / "telek").mkdir()
        make_jpeg(library / "telek" / "IMG_0100.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        controller._reload()
        return library

    def test_select_folder_loads_whole_library(self, controller, two_folders):
        controller.selectFolder(str(two_folders / "nyaralas"))
        assert controller.photos.rowCount() == 3  # nyaralas(2) + telek(1)

    def test_feed_order_follows_folder_pane(self, controller, two_folders):
        controller.selectFolder(str(two_folders / "nyaralas"))
        pane_order = controller.folders.folder_paths()
        feed_folders = []
        for photo in controller.photos.photos:
            if photo.folder_path not in feed_folders:
                feed_folders.append(photo.folder_path)
        assert tuple(feed_folders) == pane_order

    def test_feed_groups_cover_all_rows(self, controller, two_folders):
        controller.selectFolder(str(two_folders / "nyaralas"))
        groups = controller.feedGroups
        assert [g["count"] for g in groups] == [2, 1] or [
            g["count"] for g in groups
        ] == [1, 2]
        assert groups[0]["start"] == 0
        assert groups[1]["start"] == groups[0]["count"]
        assert {g["name"] for g in groups} == {"nyaralas", "telek"}
        photos = controller.photos.photos
        for g in groups:
            for row in range(g["start"], g["start"] + g["count"]):
                assert photos[row].folder_path == g["path"]

    def test_select_folder_emits_folder_activated(self, controller, two_folders):
        activated = []
        controller.folderActivated.connect(activated.append)
        target = str(two_folders / "telek")
        controller.selectFolder(target)
        assert activated == [target]

    def test_feed_groups_stable_across_refresh(self, controller, two_folders):
        # A csillagozás utáni _refresh_view NEM adhat ki feedChanged-et
        # (a csoportok nem változtak) — különben a görgetés nullázódna.
        controller.selectFolder(str(two_folders / "nyaralas"))
        changed = []
        controller.feedChanged.connect(lambda: changed.append(1))
        controller.toggleStar(0)
        assert changed == []

    def test_search_still_restricts(self, controller, two_folders):
        # A keresés/szűrő nézetek maradnak részhalmazok — csak a sima
        # mappanézet feed.
        controller.search("naplemente")
        assert controller.photos.rowCount() == 1
        assert len(controller.feedGroups) == 1

    def test_starred_filter_groups(self, controller, two_folders):
        controller.showStarred()
        assert controller.photos.rowCount() == 1
        groups = controller.feedGroups
        assert len(groups) == 1 and groups[0]["count"] == 1

    def test_group_date_text(self, controller, two_folders):
        controller.selectFolder(str(two_folders / "nyaralas"))
        by_name = {g["name"]: g for g in controller.feedGroups}
        assert "2025" in by_name["nyaralas"]["dateText"]  # IMG_0001 taken_at
        assert by_name["telek"]["dateText"] == ""  # nincs felvételi dátum

    def test_sort_change_reorders_feed(self, controller, two_folders):
        controller.selectFolder(str(two_folders / "nyaralas"))
        before = tuple(p.name for p in controller.photos.photos)
        controller.setFolderSort("name")
        after_names = tuple(p.name for p in controller.photos.photos)
        assert sorted(before) == sorted(after_names)  # ugyanaz a tartalom
        pane_order = controller.folders.folder_paths()
        feed_folders = []
        for photo in controller.photos.photos:
            if photo.folder_path not in feed_folders:
                feed_folders.append(photo.folder_path)
        assert tuple(feed_folders) == pane_order


class TestFolderDescriptionPerPath:
    """#64: a feed-fejlécek mappánként olvassák/írják a leírást."""

    def test_description_of_reads_ini(self, controller, library):
        (library / "nyaralas" / ".picasa.ini").write_text(
            "[Picasa]\ndescription=nyári képek\n[IMG_0001.jpg]\nstar=yes\n",
            encoding="utf-8",
        )
        assert (
            controller.folderDescriptionOf(str(library / "nyaralas"))
            == "nyári képek"
        )

    def test_set_description_of_writes_and_caches(self, controller, library):
        path = str(library / "nyaralas")
        controller.setFolderDescriptionOf(path, "új leírás")
        assert controller.folderDescriptionOf(path) == "új leírás"
        ini_text = (library / "nyaralas" / ".picasa.ini").read_text(
            encoding="utf-8"
        )
        assert "description=új leírás" in ini_text

    def test_description_revision_bumped_on_set(self, controller, library):
        before = controller.descriptionRevision
        controller.setFolderDescriptionOf(str(library / "nyaralas"), "x")
        assert controller.descriptionRevision == before + 1


class TestFolderClickDuringSearch:
    """#45: keresés közben a mappa-kattintás nem dobja el a szűrést —
    a találatok az adott mappára szűkülnek (Picasa-viselkedés)."""

    @pytest.fixture
    def two_folders(self, controller, library, tmp_path):
        from picasapy.index import open_index, sync_tree

        (library / "telek").mkdir()
        make_jpeg(library / "telek" / "IMG_0100.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        controller._reload()
        return library

    def test_folder_click_keeps_search_and_restricts(self, controller, two_folders):
        controller.selectFolder(str(two_folders / "nyaralas"))
        controller.search("IMG")
        assert controller.photos.rowCount() == 3  # minden mappából
        controller.selectFolderKeepSearch(str(two_folders / "telek"))
        assert controller.photos.rowCount() == 1  # csak a telek találata
        assert controller.currentFolder == str(two_folders / "telek")

    def test_restricted_view_survives_reload(self, controller, two_folders):
        controller.search("IMG")
        controller.selectFolderKeepSearch(str(two_folders / "telek"))
        controller._reload()  # háttér-sync sem dobhatja el (#38 mintájára)
        assert controller.photos.rowCount() == 1

    def test_without_active_search_plain_select(self, controller, two_folders):
        # Keresés nélkül a mappa-kattintás sima selectFolder → a teljes
        # könyvtár-feed jön (#64), nem csak az egy mappa.
        controller.selectFolderKeepSearch(str(two_folders / "telek"))
        assert controller.photos.rowCount() == 3  # feed: minden mappa
        controller.search("IMG")
        controller.search("")
        controller.selectFolderKeepSearch(str(two_folders / "nyaralas"))
        assert controller.photos.rowCount() == 3  # törölt keresés → feed


class TestSearchFiltersFolderPane:
    """#49: aktív keresésnél a bal hasáb a találatos mappákra szűkül."""

    @pytest.fixture
    def two_folders(self, controller, library, tmp_path):
        from picasapy.index import open_index, sync_tree

        (library / "telek").mkdir()
        make_jpeg(library / "telek" / "IMG_0100.jpg")
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        controller._reload()
        return library

    def _pane_rows(self, controller):
        from picasapy.app.models import FolderListModel

        model = controller.folders
        return [
            (
                model.data(model.index(i, 0), FolderListModel.NameRole),
                model.data(model.index(i, 0), FolderListModel.CountRole),
            )
            for i in range(model.rowCount())
            if model.data(model.index(i, 0), FolderListModel.KindRole) == "folder"
        ]

    def test_search_narrows_pane_with_match_counts(self, controller, two_folders):
        controller.search("naplemente")
        assert self._pane_rows(controller) == [("nyaralas", 1)]

    def test_search_all_matching_folders_listed(self, controller, two_folders):
        controller.search("IMG")
        assert sorted(self._pane_rows(controller)) == [
            ("nyaralas", 2), ("telek", 1)
        ]

    def test_cleared_search_restores_full_pane(self, controller, two_folders):
        controller.search("naplemente")
        controller.search("")
        rows = self._pane_rows(controller)
        assert sorted(rows) == [("nyaralas", 2), ("telek", 1)]

    def test_folder_click_keeps_filtered_pane(self, controller, two_folders):
        # A mappára szűkítés után a hasáb továbbra is az ÖSSZES találatos
        # mappát mutatja, hogy át lehessen kattintani a másikba.
        controller.search("IMG")
        controller.selectFolderKeepSearch(str(two_folders / "telek"))
        assert sorted(self._pane_rows(controller)) == [
            ("nyaralas", 2), ("telek", 1)
        ]

    def test_plain_select_restores_full_pane(self, controller, two_folders):
        # Javaslatból ugrás (selectFolder) = a keresés vége → teljes lista.
        controller.search("naplemente")
        controller.selectFolder(str(two_folders / "telek"))
        assert sorted(self._pane_rows(controller)) == [
            ("nyaralas", 2), ("telek", 1)
        ]

    def test_search_exposes_active_query_and_total_count(
        self, controller, two_folders
    ):
        # #7: a bal paneli „Találatok a(z) … kifejezésre (N)” sorhoz.
        controller.search("IMG")
        assert controller.searchActive is True
        assert controller.searchQuery == "IMG"
        assert controller.searchResultCount == 3

    def test_search_folder_keeps_total_count_not_subset(
        self, controller, two_folders
    ):
        # A mappára szűkítés a rácsot szűkíti, de a darabszám az ÖSSZES
        # találaté marad (nem a rácsban látszó részhalmazé).
        controller.search("IMG")
        controller.selectFolderKeepSearch(str(two_folders / "telek"))
        assert controller.searchActive is True
        assert controller.searchResultCount == 3

    def test_cleared_search_deactivates(self, controller, two_folders):
        controller.search("IMG")
        controller.search("")
        assert controller.searchActive is False
        assert controller.searchQuery == ""

    def test_search_inactive_by_default(self, controller):
        assert controller.searchActive is False
        assert controller.searchQuery == ""
        assert controller.searchResultCount == 0

    def test_search_groups_by_folder_with_global_row_indexes(
        self, controller, two_folders
    ):
        # #7: a rács mappánkénti csoportosítása — minden fotóhoz a lapos
        # `photos` modellbeli (globális) sorindex tartozik.
        controller.search("IMG")
        groups = controller.searchGroups
        assert sorted(g["folderName"] for g in groups) == ["nyaralas", "telek"]
        rows = sorted(
            photo["row"] for g in groups for photo in g["photos"]
        )
        assert rows == list(range(controller.photos.rowCount()))

    def test_search_groups_empty_outside_search(self, controller, two_folders):
        assert controller.searchGroups == []

    def test_search_folder_narrows_groups_to_one(self, controller, two_folders):
        controller.search("IMG")
        controller.selectFolderKeepSearch(str(two_folders / "telek"))
        groups = controller.searchGroups
        assert [g["folderName"] for g in groups] == ["telek"]

    def test_background_reload_keeps_filtered_pane(self, controller, two_folders):
        controller.search("naplemente")
        controller._reload()
        assert self._pane_rows(controller) == [("nyaralas", 1)]


class TestExportRows:
    """#16: kijelölt sorok exportja célmappába, háttérszálon."""

    @staticmethod
    def _run_export(controller, qt_app, rows, target, max_dim=0, quality=85):
        """exportRows hívása + várakozás az exportFinished-re (max 5 mp)."""
        from PySide6.QtCore import QEventLoop, QTimer

        results = []
        loop = QEventLoop()
        controller.exportFinished.connect(
            lambda done, failed: results.append((done, failed))
        )
        controller.exportFinished.connect(loop.quit)
        controller.exportRows(rows, target, max_dim, quality)
        if not results:  # háttérszálas út: a jel az eseményhurokban érkezik
            QTimer.singleShot(5000, loop.quit)
            loop.exec()
        return results

    def test_exports_selected_rows(self, controller, library, tmp_path, qt_app):
        controller.selectFolder(str(library / "nyaralas"))
        target = tmp_path / "export-cel"
        results = self._run_export(controller, qt_app, [0, 1], str(target))
        assert results == [(2, 0)]
        assert sorted(p.name for p in target.glob("*.jpg")) == [
            "IMG_0001.jpg",
            "IMG_0002.jpg",
        ]

    def test_export_resizes_to_max_dimension(self, controller, library, tmp_path, qt_app):
        from PIL import Image

        controller.selectFolder(str(library / "nyaralas"))
        target = tmp_path / "export-kicsi"
        results = self._run_export(
            controller, qt_app, [0], str(target), max_dim=4
        )
        assert results == [(1, 0)]
        exported = next(target.glob("*.jpg"))
        with Image.open(exported) as image:
            assert max(image.size) == 4

    def test_export_accepts_file_url_target(self, controller, library, tmp_path, qt_app):
        # a QML FolderDialog file:// URL-t ad — annak is működnie kell
        controller.selectFolder(str(library / "nyaralas"))
        target = tmp_path / "export-url"
        results = self._run_export(
            controller, qt_app, [0], (target).as_uri()
        )
        assert results == [(1, 0)]
        assert len(list(target.glob("*.jpg"))) == 1

    def test_invalid_rows_finish_immediately(self, controller, tmp_path, qt_app):
        results = []
        controller.exportFinished.connect(
            lambda done, failed: results.append((done, failed))
        )
        controller.exportRows([99], str(tmp_path / "sehova"), 0, 85)
        assert results == [(0, 0)]
        assert not (tmp_path / "sehova").exists()


class TestBusyAndBackgroundResync:
    """#86: a resyncFolder nem blokkolja a UI-szálat; #70: busy-állapot."""

    def test_resync_folder_runs_off_main_thread(
        self, controller, library, qt_app, monkeypatch
    ):
        import threading as _threading

        import picasapy.app.controller as controller_module
        from PySide6.QtCore import QEventLoop, QTimer

        on_main = []
        original = controller_module.sync_tree

        def recording(conn, folder):
            on_main.append(
                _threading.current_thread() is _threading.main_thread()
            )
            return original(conn, folder)

        monkeypatch.setattr(controller_module, "sync_tree", recording)
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller.resyncFolder(str(library / "nyaralas"))
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        assert on_main == [False]

    def test_resync_returns_while_sync_still_running(
        self, controller, library, qt_app, monkeypatch
    ):
        # a „Vissza a könyvtárhoz" útja (#86): a hívás visszatér, miközben a
        # (lassú, NAS-t szimuláló) szinkron még fut — közben busy a jelzés
        import threading as _threading

        import picasapy.app.controller as controller_module
        from PySide6.QtCore import QEventLoop, QTimer

        started = _threading.Event()
        release = _threading.Event()

        def slow(conn, folder):
            started.set()
            release.wait(5)

        monkeypatch.setattr(controller_module, "sync_tree", slow)
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller.resyncFolder(str(library / "nyaralas"))
        # a hívás után azonnal itt vagyunk; a worker még a release-re vár
        assert started.wait(5)
        assert controller.isWorking is True
        release.set()
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()
        assert controller.isWorking is False

    def test_is_working_during_rescan(self, controller, qt_app):
        from PySide6.QtCore import QEventLoop, QTimer

        transitions = []
        controller.busyChanged.connect(
            lambda: transitions.append(controller.isWorking)
        )
        loop = QEventLoop()
        controller.syncFinished.connect(loop.quit)
        controller.rescan()
        assert controller.isWorking is True
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        qt_app.processEvents()
        assert controller.isWorking is False
        assert transitions[0] is True
        assert transitions[-1] is False

    def test_thumbnail_activity_drives_busy(self, controller, qt_app):
        provider = controller._provider
        provider.activeCountChanged.emit(2)
        qt_app.processEvents()
        assert controller.isWorking is True
        provider.activeCountChanged.emit(0)
        qt_app.processEvents()
        assert controller.isWorking is False

    def test_provider_request_emits_balanced_counts(self, controller, qt_app, tmp_path):
        # a requestImage körül 1 → 0 párnak kell kimennie (ismeretlen id-nél
        # placeholderrel tér vissza, de a könyvelés akkor is kiegyenlített)
        counts = []
        provider = controller._provider
        provider.activeCountChanged.connect(counts.append)
        provider.requestImage("nem-letezo", None, None)
        qt_app.processEvents()
        assert counts == [1, 0]
