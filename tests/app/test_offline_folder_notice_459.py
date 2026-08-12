"""#459/5 — a nem elérhető mappára lépéskor a program KIMONDJA a helyzetet.

A jegy negatív példája szerint a legrosszabb az, amikor a hiba csendben
eltűnik. Az offline mappa nem hiba, hanem állapot — de a felhasználónak
tudnia kell róla, mielőtt egy szerkesztés érthetetlenül elbukik.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "helyi").mkdir(parents=True)
    (root / "nas").mkdir()
    make_jpeg(root / "helyi" / "a.jpg")
    make_jpeg(root / "nas" / "b.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        conn.execute("UPDATE folders SET offline = 1 WHERE path LIKE '%nas'")
        conn.commit()
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


class TestOfflineFolderNotice:
    def test_selecting_an_offline_folder_announces_it(self, controller, library):
        seen: list[str] = []
        controller.folderUnavailable.connect(seen.append)
        controller.selectFolder(str(library / "nas"))
        assert seen == [str(library / "nas")]

    def test_available_folder_stays_silent(self, controller, library):
        seen: list[str] = []
        controller.folderUnavailable.connect(seen.append)
        controller.selectFolder(str(library / "helyi"))
        assert seen == []

    def test_offline_folder_photos_are_still_listed(self, controller, library):
        # a mappa megnyitható marad — a bélyegképek a gyorsítótárból jönnek
        controller.selectFolder(str(library / "nas"))
        assert controller.currentFolder == str(library / "nas")
