"""AppController (PhotoOpsMixin): tömeges átnevezés (#366) —
`renamePreview` (tiszta lekérdezés) és `renamePhotosMany` (a tényleges
átnevezés, háttérszálon + resync)."""

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(
        root / "a.jpg", size=(800, 600), taken_at="2025:05:01 07:00:00",
    )
    make_jpeg(
        root / "b.jpg", size=(1024, 768), taken_at="2025:06:02 08:00:00",
    )
    (root / ".picasa.ini").write_text(
        "[a.jpg]\nstar=yes\n[b.jpg]\ncaption=nyar\n", encoding="utf-8"
    )
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
    ctl.selectFolder(str(library))
    return ctl


def _rows_by_name(controller, *names) -> list:
    photos = controller.photos.photos
    by_name = {p.name: i for i, p in enumerate(photos)}
    return [by_name[name] for name in names]


def _do_rename(controller, action) -> None:
    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    controller.photoOpFinished.connect(loop.quit)
    action()
    QTimer.singleShot(5000, loop.quit)
    loop.exec()


class TestRenamePreview:
    def test_first_file_no_suffix_by_default(self, controller):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        preview = controller.renamePreview(rows, "nyaralas", False, False)
        assert preview == "nyaralas.jpg"

    def test_date_and_size_suffix(self, controller):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        preview = controller.renamePreview(rows, "nyaralas", True, True)
        assert preview == "nyaralas 2025-05-01 800x600.jpg"

    def test_empty_base_name_gives_empty_preview(self, controller):
        rows = _rows_by_name(controller, "a.jpg")
        assert controller.renamePreview(rows, "  ", False, False) == ""

    def test_empty_selection_gives_empty_preview(self, controller):
        assert controller.renamePreview([], "nev", False, False) == ""


class TestRenamePhotosMany:
    def test_renames_with_sequence_and_syncs_grid(self, controller, library):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        _do_rename(
            controller,
            lambda: controller.renamePhotosMany(rows, "nyaralas", False, False),
        )
        assert (library / "nyaralas.jpg").exists()
        assert (library / "nyaralas-1.jpg").exists()
        assert not (library / "a.jpg").exists()
        assert not (library / "b.jpg").exists()
        names = {p.name for p in controller.photos.photos}
        assert names == {"nyaralas.jpg", "nyaralas-1.jpg"}

    def test_ini_sections_follow_the_rename(self, controller, library):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        _do_rename(
            controller,
            lambda: controller.renamePhotosMany(rows, "nyaralas", False, False),
        )
        from picasapy.ini import load_document

        document = load_document(library / ".picasa.ini")
        assert document.section("nyaralas.jpg").get("star") == "yes"
        assert document.section("nyaralas-1.jpg").get("caption") == "nyar"

    def test_date_and_size_suffix_end_to_end(self, controller, library):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        _do_rename(
            controller,
            lambda: controller.renamePhotosMany(rows, "nyar", True, True),
        )
        assert (library / "nyar 2025-05-01 800x600.jpg").exists()
        assert (library / "nyar 2025-06-02 1024x768-1.jpg").exists()

    def test_collision_reports_failure_without_renaming(self, controller, library):
        # az "a.jpg" célneve ("b.jpg", sorszám nélkül) ütközik a köteg
        # MÁSIK tagjának ("b.jpg") jelenlegi nevével — semmi sem nevezhető át
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        failures = []
        controller.syncFailed.connect(lambda msg: failures.append(msg))
        _do_rename(
            controller,
            lambda: controller.renamePhotosMany(rows, "b", False, False),
        )
        assert failures  # emberi hibaüzenet érkezett
        assert (library / "a.jpg").exists()
        assert (library / "b.jpg").exists()

    def test_empty_base_name_is_a_no_op(self, controller, library):
        rows = _rows_by_name(controller, "a.jpg", "b.jpg")
        controller.renamePhotosMany(rows, "   ", False, False)
        assert (library / "a.jpg").exists()
        assert (library / "b.jpg").exists()
