"""#321: a Nézet ▸ Mappanézet rendezés a RÁCSRA hat, a bal hasábra nem.

Az eredeti Picasában a mappafa sorrendje a saját (gyűjtemény/év) szabálya
szerint áll, és a rendezés váltása nem mozdítja meg — csak a fő rács
(feed) sorrendjét cseréli. Nálunk eddig mindkettő együtt mozgott (#64).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    """Három mappa, amelyeknél a név- és a dátumsorrend SZÁNDÉKOSAN eltér."""
    root = tmp_path / "kepek"
    # névsorrend: alma, mokus, zebra — dátumsorrend (legújabb elöl):
    # mokus, zebra, alma. A kettő szándékosan NEM esik egybe.
    for folder, taken in (
        ("alma", "2020:01:01 10:00:00"),
        ("mokus", "2024:01:01 10:00:00"),
        ("zebra", "2022:01:01 10:00:00"),
    ):
        (root / folder).mkdir(parents=True)
        make_jpeg(root / folder / "IMG_0001.jpg", taken_at=taken)
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    return ctl


def _feed_folder_order(controller) -> tuple[str, ...]:
    """A rácsban megjelenő mappák sorrendje (első előfordulás szerint)."""
    seen: list[str] = []
    for photo in controller.photos.photos:
        if photo.folder_path not in seen:
            seen.append(photo.folder_path)
    return tuple(seen)


class TestSortAffectsOnlyTheFeed:
    def test_pane_order_is_stable_across_sort_changes(self, controller):
        before = controller.folders.folder_paths()
        controller.setFolderSort("name")
        assert controller.folders.folder_paths() == before
        controller.setFolderSort("size")
        assert controller.folders.folder_paths() == before

    def test_pane_order_is_stable_across_reverse(self, controller):
        before = controller.folders.folder_paths()
        controller.toggleFolderSortReverse()
        assert controller.folders.folder_paths() == before

    def test_feed_order_follows_the_sort_setting(self, controller):
        controller.setFolderSort("name")
        by_name = [Path(p).name for p in _feed_folder_order(controller)]
        assert by_name == ["alma", "mokus", "zebra"]

        controller.setFolderSort("date")
        by_date = [Path(p).name for p in _feed_folder_order(controller)]
        assert by_date == ["mokus", "zebra", "alma"], "legújabb mappa elöl"

    def test_reverse_flips_the_feed(self, controller):
        controller.setFolderSort("name")
        forward = _feed_folder_order(controller)
        controller.toggleFolderSortReverse()
        assert _feed_folder_order(controller) == tuple(reversed(forward))
