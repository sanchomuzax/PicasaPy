"""#6281: a csak az indexben élő üres album törlése és szerkesztése.

A #6278 óta az új üres album a `local_empty_albums` táblába kerül, a mappa
ini-je változatlan. A törlésnek és a tulajdonság-műveleteknek ezt a tárat is
látniuk kell, és közben ini-t sem írhatnak.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "varos").mkdir(parents=True)
    make_jpeg(root / "varos" / "c.jpg")
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
    return ctl


@pytest.fixture
def empty_token(controller, library):
    token = controller.createEmptyAlbum(
        "Budapest",
        str(library / "varos"),
        "2026-10-25",
        "Lánchíd",
        "Üres album",
        False,
        "",
    )
    assert token
    return token


def _ini(library):
    return library / "varos" / ".picasa.ini"


def _tokens(controller):
    return {album["token"] for album in controller.albums}


def test_delete_removes_index_only_album(controller, library, empty_token):
    assert empty_token in _tokens(controller)

    assert controller.deleteAlbum(empty_token) is True

    assert empty_token not in _tokens(controller)
    assert not _ini(library).exists()


def test_deleted_empty_album_stays_deleted_after_reload(
    controller, library, empty_token
):
    controller.deleteAlbum(empty_token)
    controller._reload()

    assert empty_token not in _tokens(controller)


def test_properties_of_index_only_album(controller, empty_token):
    assert controller.albumProperties(empty_token) == {
        "name": "Budapest",
        "date": "2026-10-25",
        "location": "Lánchíd",
        "description": "Üres album",
        "use_music": False,
        "music_file": "",
    }


def test_edit_properties_of_index_only_album(controller, library, empty_token):
    assert controller.editAlbumProperties(
        empty_token, "Szeged", "2026-10-26", "Tisza", "Más leírás"
    ) is True

    props = controller.albumProperties(empty_token)
    assert (props["name"], props["date"], props["location"], props["description"]) == (
        "Szeged",
        "2026-10-26",
        "Tisza",
        "Más leírás",
    )
    assert {a["token"]: a["name"] for a in controller.albums}[empty_token] == "Szeged"
    assert not _ini(library).exists()


def test_edit_music_of_index_only_album(controller, library, empty_token):
    music = library / "varos" / "tone.mp3"
    music.write_bytes(b"ID3")

    assert controller.editAlbumMusic(empty_token, True, "tone.mp3") is True

    props = controller.albumProperties(empty_token)
    assert props["use_music"] is True
    assert props["music_file"] == "tone.mp3"
    assert controller.albumMusicFile(empty_token) == str(music.resolve())
    assert not _ini(library).exists()
