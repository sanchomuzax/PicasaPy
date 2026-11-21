"""#7341: a rács mappa-blokkjai a `paneSort` szerinti sorrendet követik.

Az eredeti négy Mappa-menütétel a mappa képeit rendezi egyszer.
`folderSort == "changed"` kivételként megőrzi a védett „Recent &changes”
saját tétel működését; a korábban eltárolt többi `folderSort` értéket a
rács mappasorrendje nem használja.

Mappa-rendezés váltásakor a bal hasáb és a rács mappablokkjai együtt
követik a `paneSort` értékét.
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


class TestFolderSortIsReservedForRecentChanges:
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

    def test_feed_order_follows_the_pane_sort_setting(self, controller):
        controller.setPaneSort("name")
        by_name = [Path(p).name for p in _feed_folder_order(controller)]
        assert by_name == ["alma", "mokus", "zebra"]

        controller.setPaneSort("date")
        by_date = [Path(p).name for p in _feed_folder_order(controller)]
        assert by_date == ["mokus", "zebra", "alma"], "legújabb mappa elöl"

    def test_pane_reverse_flips_the_feed(self, controller):
        controller.setPaneSort("name")
        forward = _feed_folder_order(controller)
        controller.togglePaneSortReverse()
        assert _feed_folder_order(controller) == tuple(reversed(forward))

    def test_legacy_folder_sort_values_do_not_override_pane_sort(self, controller):
        controller.setPaneSort("name")
        controller.setFolderSort("size")
        assert [Path(p).name for p in _feed_folder_order(controller)] == [
            "alma", "mokus", "zebra"
        ]


class TestPaneHasItsOwnSort:
    """#461/3: a bal hasábnak SAJÁT rendezése van — az eredeti Picasában a
    hasáb jobbklikk-menüje (`AlbumList`, ld. ui-audit-context-menus.md A.2)
    tartalmazta a „Rendezés dátum / név / méret / legutóbbi változtatás
    alapján" tételeket, vagyis az a HASÁBOT rendezte.

    A #7341 óta a rács mappa-blokkjai is ezt az értéket követik; az egyetlen
    `folderSort`-kivétel a védett „Recent &changes” tétel."""

    def test_pane_sort_reorders_the_pane(self, controller):
        controller.setPaneSort("name")
        by_name = [Path(p).name for p in controller.folders.folder_paths()]
        assert by_name == ["alma", "mokus", "zebra"]

        controller.setPaneSort("date")
        by_date = [Path(p).name for p in controller.folders.folder_paths()]
        assert by_date == ["mokus", "zebra", "alma"], "legújabb mappa elöl"

    def test_pane_reverse_flips_the_pane(self, controller):
        controller.setPaneSort("name")
        forward = controller.folders.folder_paths()
        controller.togglePaneSortReverse()
        assert controller.folders.folder_paths() == tuple(reversed(forward))

    def test_pane_sort_reorders_both_pane_and_feed(self, controller):
        controller.setPaneSort("name")
        assert [Path(p).name for p in _feed_folder_order(controller)] == [
            "alma", "mokus", "zebra"
        ]
        assert [Path(p).name for p in controller.folders.folder_paths()] == [
            "alma", "mokus", "zebra"
        ]

    def test_folder_sort_setting_does_not_touch_the_pane(self, controller):
        """A `folderSort` csak a saját „Recent &changes” módot őrzi."""
        controller.setPaneSort("date")
        before = controller.folders.folder_paths()
        controller.setFolderSort("name")
        assert controller.folders.folder_paths() == before

    def test_recent_changes_mode_remains_a_grid_override(
        self, controller, monkeypatch
    ):
        from picasapy.app import controller_photo_list_mixin as feed_module

        controller.setPaneSort("name")
        seen: list[tuple[str, bool]] = []
        monkeypatch.setattr(
            feed_module,
            "folder_order",
            lambda _conn, mode, reverse: seen.append((mode, reverse))
            or controller.folders.folder_paths(),
        )
        controller.setFolderSort("changed")
        assert seen[-1] == ("changed", controller.folderSortReverse)

    def test_unknown_mode_is_ignored(self, controller):
        before = controller.folders.folder_paths()
        controller.setPaneSort("mandala")
        assert controller.folders.folder_paths() == before

    def test_default_is_the_picasa_date_order(self, controller):
        # alapértéken (dátum, legújabb elöl) áll, ahogy eddig is
        by_date = [Path(p).name for p in controller.folders.folder_paths()]
        assert by_date == ["mokus", "zebra", "alma"]


class TestYearHeadersBelongToTheDateView:
    """#461/3: az évszám-csoportok a DÁTUM-nézet sajátjai. Név/méret szerinti
    rendezésnél egy évszám többször, összevissza sorrendben bukkanna fel —
    ott sima felsorolás áll."""

    def _kinds(self, controller):
        from picasapy.app.models import FolderListModel

        model = controller.folders
        return [
            model.data(model.index(i, 0), FolderListModel.KindRole)
            for i in range(model.rowCount())
        ]

    def test_date_view_has_year_headers(self, controller):
        controller.setPaneSort("date")
        assert "year" in self._kinds(controller)

    def test_name_view_has_none(self, controller):
        controller.setPaneSort("name")
        assert "year" not in self._kinds(controller)

    def test_size_view_has_none(self, controller):
        controller.setPaneSort("size")
        assert "year" not in self._kinds(controller)

    def test_changed_view_keeps_them(self, controller):
        # a „legutóbbi változtatás" is dátum-alapú nézet
        controller.setPaneSort("changed")
        assert "year" in self._kinds(controller)
