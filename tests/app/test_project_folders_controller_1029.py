"""#1029: a **Projektek** gyűjtemény a vezérlőben — a
`P2category=Projects (internal)` mappák eljutnak a bal hasábig.

A `controller.projectFolders` a `albums`/`people` property mintáját követi:
`[{path, name, count}]` LISTA (#232 — a QML-ben a tuple nem tömb), és a
`_reload()`-ban frissül, tehát a háttér-szinkron után is friss.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

_PROJECTS = "[Picasa]\nP2category=Projects (internal)\n"


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    for name in ("Kollázsok", "nyaralas"):
        (root / name).mkdir(parents=True)
        (root / name / "IMG_0001.jpg").write_bytes(b"x" * 10)
    (root / "Kollázsok" / ".picasa.ini").write_text(_PROJECTS, encoding="utf-8")
    (root / "nyaralas" / ".picasa.ini").write_text(
        "[Picasa]\nP2category=Folders on Disk\n", encoding="utf-8"
    )
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
    app_controller = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    # a valódi indulás sorrendje: a szinkron UTÁN tölt a bal hasáb
    app_controller._reload_after_sync()
    return app_controller


class TestProjectFoldersProperty:
    def test_project_folder_reaches_the_controller(self, controller, library):
        assert controller.projectFolders == [
            {
                "path": str(library / "Kollázsok"),
                "name": "Kollázsok",
                "count": 1,
            }
        ]

    def test_property_is_a_list_for_qml(self, controller):
        # #232: a QML-ben a tuple nem tömb — a hasáb `.length`-et olvas
        assert isinstance(controller.projectFolders, list)

    def test_new_project_folder_appears_after_reload(
        self, controller, tmp_path, library
    ):
        """A mentett kollázs mappája a következő szinkron után LÁTSZIK —
        enélkül a felhasználó hiába kapja meg a kulcsot az ini-be."""
        from picasapy.index import open_index, sync_tree

        (library / "Filmek").mkdir()
        # kép nélküli mappát a beolvasó nem indexel (walker._scan_folder)
        (library / "Filmek" / "film.jpg").write_bytes(b"x" * 10)
        (library / "Filmek" / ".picasa.ini").write_text(
            _PROJECTS, encoding="utf-8"
        )
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library)
        controller._reload_after_sync()

        assert [row["name"] for row in controller.projectFolders] == [
            "Filmek",
            "Kollázsok",
        ]

    def test_signal_fires_on_reload(self, controller, qt_app):
        seen = []
        controller.projectFoldersChanged.connect(lambda: seen.append(1))
        controller._reload_after_sync()
        qt_app.processEvents()
        assert seen


class TestFoldersViewIsNotBroken:
    """⚠️ A legvalószínűbb regresszió: a Mappák nézet MINDEN mappája
    megmarad — a `Folders on Disk` értékű is, a projekt-mappa is."""

    def test_folder_list_still_has_every_folder(self, controller, library):
        paths = set(controller.folders.folder_paths())
        assert str(library / "nyaralas") in paths
        assert str(library / "Kollázsok") in paths

    def test_folder_count_is_unchanged(self, controller):
        assert controller.folders.folderCount == 2
