"""#320: a bal hasáb gyűjtemény-fejlécei (Albumok, Emberek, Projektek,
Mappák, Egyebek) — csukhatók, és a csukott állapot megjegyződik.

Az eredeti Picasa bal hasábján a fa gyökerén öt gyűjtemény áll, mindegyik
saját, csukható fejléccel; csak a „Mappák" tagolt évszám-szakaszokra.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.collections import (
    COLLECTIONS,
    DEFAULT_COLLAPSED,
    collection_setting_key,
)
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
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
    return AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )


class TestCollectionCatalogue:
    def test_the_five_picasa_collections_in_order(self):
        assert COLLECTIONS == ("albums", "people", "projects", "folders", "other")

    def test_folders_and_albums_start_open_the_rest_collapsed(self):
        # a Mappák a napi munka helye, az Albumok a csillagozottat hordozza;
        # a még tartalom nélküli gyűjtemények ne foglalják a helyet
        assert DEFAULT_COLLAPSED["folders"] is False
        assert DEFAULT_COLLAPSED["albums"] is False
        assert DEFAULT_COLLAPSED["people"] is True
        assert DEFAULT_COLLAPSED["other"] is True
        # #1029: a Projektek MÁR NEM üres (a P2category-mappák benne
        # állnak), ezért — az eredeti Picasához hasonlóan — nyitva indul.
        # A korábbi `is True` állítás a „még tartalom nélküli" állapotot
        # rögzítette; az elavult.
        assert DEFAULT_COLLAPSED["projects"] is False

    def test_setting_key_is_namespaced(self):
        assert collection_setting_key("people") == "view/collection/people/collapsed"


class TestCollapsedState:
    def test_defaults_are_reported(self, controller):
        assert controller.isCollectionCollapsed("folders") is False
        assert controller.isCollectionCollapsed("people") is True

    def test_toggle_round_trip(self, controller):
        controller.setCollectionCollapsed("folders", True)
        assert controller.isCollectionCollapsed("folders") is True
        controller.setCollectionCollapsed("folders", False)
        assert controller.isCollectionCollapsed("folders") is False

    def test_persisted(self, controller):
        controller.setCollectionCollapsed("projects", False)
        stored = controller._get_settings().value(
            collection_setting_key("projects")
        )
        assert stored in (False, "false", 0, "0")

    def test_unknown_collection_is_ignored(self, controller):
        controller.setCollectionCollapsed("nincs-ilyen", True)
        # nem dob, és nem is jegyzi meg
        assert controller.isCollectionCollapsed("nincs-ilyen") is False
