"""`TrayMixin` — a képtálca (Picture Tray, #455) állapot-magja.

A `test_photo_ops_controller.py` fixtúra-mintáját követi: valódi
`AppController` két mappával (a mappákon-átnyúló gyűjtés bizonyításához).
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def two_folder_library(tmp_path):
    root = tmp_path / "kepek"
    folder_a = root / "a"
    folder_b = root / "b"
    folder_a.mkdir(parents=True)
    folder_b.mkdir(parents=True)
    make_jpeg(folder_a / "x.jpg", size=(800, 600))
    make_jpeg(folder_a / "y.jpg", size=(800, 600))
    make_jpeg(folder_b / "z.jpg", size=(800, 600))
    return root, folder_a, folder_b


@pytest.fixture
def controller(qt_app, tmp_path, two_folder_library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    root, _folder_a, _folder_b = two_folder_library
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(root),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    return ctl


def _rows_by_name(controller, *names) -> list:
    photos = controller.photos.photos
    by_name = {p.name: i for i, p in enumerate(photos)}
    return [by_name[name] for name in names]


class TestHoldRows:
    def test_empty_tray_initially(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        assert controller.heldCount == 0

    def test_hold_row_adds_to_tray(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        rows = _rows_by_name(controller, "x.jpg")
        controller.holdRows(rows)
        assert controller.heldCount == 1
        assert controller.isHeldAt(rows[0]) is True

    def test_hold_is_idempotent(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        rows = _rows_by_name(controller, "x.jpg")
        controller.holdRows(rows)
        controller.holdRows(rows)
        assert controller.heldCount == 1

    def test_hold_survives_folder_change(self, controller, two_folder_library):
        """A tálca lényege: mappaváltás után is megmarad a megtartott kép,
        holott a `selectedIndexes`/sor-index elveszne (a #150-es
        row-alapú kijelölés csak az aktuális mappára érvényes)."""
        _root, folder_a, folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        rows = _rows_by_name(controller, "x.jpg")
        controller.holdRows(rows)

        controller.selectFolder(str(folder_b))
        assert controller.heldCount == 1
        # a b mappa "z.jpg" sora NEM tartott
        z_row = _rows_by_name(controller, "z.jpg")[0]
        assert controller.isHeldAt(z_row) is False

    def test_hold_across_two_folders_accumulates(
        self, controller, two_folder_library
    ):
        _root, folder_a, folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        controller.selectFolder(str(folder_b))
        controller.holdRows(_rows_by_name(controller, "z.jpg"))
        assert controller.heldCount == 2


class TestClearHeld:
    def test_clears_all(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg", "y.jpg"))
        assert controller.heldCount == 2
        controller.clearHeld()
        assert controller.heldCount == 0

    def test_clear_empty_tray_is_noop(self, controller):
        controller.clearHeld()
        assert controller.heldCount == 0


class TestHeldThumbUrl:
    def test_returns_url_even_from_other_folder(self, controller, two_folder_library):
        _root, folder_a, folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        controller.selectFolder(str(folder_b))
        # jelenleg a b mappa van megnyitva, a tartott kép mégis az a-ból
        url = controller.heldThumbUrlAt(0)
        assert url.startswith("image://thumbs/")

    def test_out_of_range_is_empty(self, controller):
        assert controller.heldThumbUrlAt(0) == ""


class TestHeldChangedSignal:
    def test_emitted_on_hold(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        seen = []
        controller.heldChanged.connect(lambda: seen.append(True))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        assert seen == [True]

    def test_not_emitted_when_nothing_changes(self, controller, two_folder_library):
        _root, folder_a, _folder_b = two_folder_library
        controller.selectFolder(str(folder_a))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))
        seen = []
        controller.heldChanged.connect(lambda: seen.append(True))
        controller.holdRows(_rows_by_name(controller, "x.jpg"))  # már bent van
        assert seen == []
