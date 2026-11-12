"""AppController Recently Updated (#6851) tesztek."""

import pytest

from picasapy.app.controller import AppController
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.thumbs import ThumbnailCache
from picasapy.index import open_index, sync_tree
from picasapy.ini import RECENT_ALBUM_TOKEN
from support.jpeg_factory import make_jpeg


@pytest.fixture
def controller(tmp_path, qt_app):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "img1.jpg")
    make_jpeg(root / "img2.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    c = AppController(tmp_path / "index.db", (str(root),), provider)
    qt_app.processEvents()
    yield c
    c.deleteLater()
    qt_app.processEvents()


def test_show_recently_updated_album(controller, qt_app):
    assert hasattr(controller, "showRecentlyUpdatedAlbum")
    controller.showRecentlyUpdatedAlbum()
    qt_app.processEvents()

    assert controller.viewModeName == "recent_album"
    assert controller.currentAlbumToken == RECENT_ALBUM_TOKEN
    assert controller.currentAlbumToken == "]updated"
    assert controller.filterActive is True
    assert controller.recentlyUpdatedCount == 2
    assert len(controller.photos.photos) == 2
    # Legújabb felvett kép elöl
    assert controller.photos.photos[0].name == "img2.jpg"
    assert controller.photos.photos[1].name == "img1.jpg"


def test_show_album_updated_token_routes_to_recently_updated(controller, qt_app):
    controller.showAlbum("]updated")
    qt_app.processEvents()

    assert controller.viewModeName == "recent_album"
    assert controller.currentAlbumToken == "]updated"
