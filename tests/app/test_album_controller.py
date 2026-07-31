"""#9 (2. lépés): a vezérlő albumlistája és az album-szűrt nézet.

A `picasapy.index.albums` réteg készen áll (`AlbumRecord`, `album_photos`,
`albums_in_index`) — ez a teszt azt ellenőrzi, hogy az `AppController` a
`.picasa.ini`-ből szinkronizált albumokat a QML-nek megfelelő alakban adja
(`albums` property: LISTA, nem tuple — #232), és hogy a `showAlbum(token)`
pontosan a `showStarred()` mintáját követi: szűrt nézet, ami túléli a
háttér-szinkront (`_reload`).
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg

_TOKEN_NAMED = "604c294a68b0de9cc9222c4714f289d5"
_TOKEN_UNNAMED = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


@pytest.fixture
def library(tmp_path):
    """Két mappa: egy névvel ellátott és egy névtelen album, az utóbbi két
    mappán átnyúlva — ugyanaz az elrendezés, mint az index-réteg tesztjeié
    (`tests/index/test_albums.py`)."""
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    (root / "varos").mkdir()

    make_jpeg(root / "nyaralas" / "a.jpg")
    make_jpeg(root / "nyaralas" / "b.jpg")
    make_jpeg(root / "varos" / "c.jpg")

    (root / "nyaralas" / ".picasa.ini").write_text(
        f"[.album:{_TOKEN_NAMED}]\n"
        f"name=Nyár 2025\n"
        f"token={_TOKEN_NAMED}\n"
        f"date=2025-07-01T10:00:00\n"
        f"[.album:{_TOKEN_UNNAMED}]\n"
        f"token={_TOKEN_UNNAMED}\n"
        f"[a.jpg]\n"
        f"albums={_TOKEN_NAMED},{_TOKEN_UNNAMED}\n"
        f"[b.jpg]\n"
        f"albums={_TOKEN_NAMED}\n",
        encoding="utf-8",
    )
    (root / "varos" / ".picasa.ini").write_text(
        "[c.jpg]\n",
        encoding="utf-8",
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
    return ctl


class TestAlbumsProperty:
    def test_albums_is_a_list(self, controller):
        # #232: a QML-ben a tuple NEM tömb — a property visszatérési
        # értéke listás alak kell legyen.
        assert isinstance(controller.albums, list)

    def test_albums_have_token_name_count(self, controller):
        by_token = {a["token"]: a for a in controller.albums}
        assert by_token[_TOKEN_NAMED]["name"] == "Nyár 2025"
        assert by_token[_TOKEN_NAMED]["count"] == 2

    def test_unnamed_album_gets_a_display_name(self, controller):
        # a névtelen album sora ne maradjon üresen a hasábon
        by_token = {a["token"]: a for a in controller.albums}
        name = by_token[_TOKEN_UNNAMED]["name"]
        assert name
        assert name.strip() != ""

    def test_two_albums_present(self, controller):
        tokens = {a["token"] for a in controller.albums}
        assert tokens == {_TOKEN_NAMED, _TOKEN_UNNAMED}


class TestShowAlbum:
    def test_show_album_fills_grid(self, controller):
        controller.showAlbum(_TOKEN_NAMED)
        assert controller.photos.rowCount() == 2
        names = {controller.photos.filePathAt(i).rsplit("/", 1)[-1] for i in range(2)}
        assert names == {"a.jpg", "b.jpg"}

    def test_show_album_spanning_folders(self, controller):
        # az egyik album csak "a.jpg"-t tartalmazza a "nyaralas" mappában
        controller.showAlbum(_TOKEN_UNNAMED)
        assert controller.photos.rowCount() == 1
        assert controller.photos.filePathAt(0).endswith("a.jpg")

    def test_show_album_activates_filter(self, controller, library):
        controller.selectFolder(str(library / "nyaralas"))
        controller.showAlbum(_TOKEN_NAMED)
        assert controller.filterActive is True
        assert controller.currentAlbumToken == _TOKEN_NAMED
        controller.clearFilter()
        assert controller.filterActive is False
        assert controller.currentAlbumToken == ""
        # #64: a rács a TELJES könyvtár-feedet mutatja (nyaralas + varos)
        assert controller.photos.rowCount() == 3

    def test_unknown_token_is_ignored_gracefully(self, controller):
        # #305-stílusú védelem: hívható, nem hasal el, csak üres nézetet ad
        controller.showAlbum("nincs-ilyen-token")
        assert controller.photos.rowCount() == 0

    def test_empty_token_is_a_no_op(self, controller):
        controller.showAlbum(_TOKEN_NAMED)
        before = controller.photos.rowCount()
        controller.showAlbum("")
        assert controller.photos.rowCount() == before


class TestAlbumViewSurvivesSync:
    def test_reload_preserves_album_filter(self, controller, library):
        # #38 társ-eset (ld. a csillag-szűrő megfelelő tesztjét): a
        # háttér-sync utáni _reload nem dobhatja el az aktív album-nézetet.
        controller.showAlbum(_TOKEN_NAMED)
        assert controller.photos.rowCount() == 2
        controller._reload()
        assert controller.photos.rowCount() == 2
        assert controller.filterActive is True
        assert controller.currentAlbumToken == _TOKEN_NAMED

    def test_reload_after_sync_keeps_album_view(self, controller, library):
        controller.showAlbum(_TOKEN_NAMED)
        controller._reload_after_sync()
        assert controller.photos.rowCount() == 2
        assert controller.currentAlbumToken == _TOKEN_NAMED

    def test_albums_list_refreshes_after_sync(self, controller, library, tmp_path):
        from picasapy.index import open_index, sync_tree

        ini = library / "nyaralas" / ".picasa.ini"
        ini.write_text(
            ini.read_text(encoding="utf-8").replace(
                "name=Nyár 2025", "name=Nyár 2025 (átnevezve)"
            ),
            encoding="utf-8",
        )
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, library, incremental=False)
        controller._reload()
        by_token = {a["token"]: a for a in controller.albums}
        assert by_token[_TOKEN_NAMED]["name"] == "Nyár 2025 (átnevezve)"
