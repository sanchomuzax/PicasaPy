"""#9: virtuális albumok az indexben.

A `.picasa.ini` `[.album:<token>]` szekciói adják az album NEVÉT és dátumát,
a képek `albums=` CSV-kulcsa pedig a TAGSÁGOT. Mindkettő parse-olva volt már
(`picasapy.ini.albums`), csak az index nem tárolta — ezért a bal hasáb
Albumok gyűjteménye üres maradt.

A séma v8: `albums` + `photo_albums`. A migráció üres táblákkal jön létre,
a következő szinkron tölti fel — újraindexelés nem kell.
"""

from __future__ import annotations

import pytest

from picasapy.index import open_index, sync_tree
from picasapy.index.albums import album_photos, albums_in_index
from support.jpeg_factory import make_jpeg

_TOKEN_A = "604c294a68b0de9cc9222c4714f289d5"
_TOKEN_B = "1f2e3d4c5b6a79880123456789abcdef"


@pytest.fixture
def library(tmp_path):
    """Két mappa, két albummal; az egyik album két mappán ÁTNYÚLIK."""
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    (root / "varos").mkdir()

    make_jpeg(root / "nyaralas" / "a.jpg")
    make_jpeg(root / "nyaralas" / "b.jpg")
    make_jpeg(root / "varos" / "c.jpg")

    (root / "nyaralas" / ".picasa.ini").write_text(
        f"[.album:{_TOKEN_A}]\n"
        f"name=Nyár 2025\n"
        f"token={_TOKEN_A}\n"
        f"date=2025-07-01T10:00:00\n"
        f"[.album:{_TOKEN_B}]\n"
        f"name=Kedvencek\n"
        f"token={_TOKEN_B}\n"
        f"[a.jpg]\n"
        f"albums={_TOKEN_A},{_TOKEN_B}\n"
        f"[b.jpg]\n"
        f"albums={_TOKEN_A}\n",
        encoding="utf-8",
    )
    (root / "varos" / ".picasa.ini").write_text(
        f"[.album:{_TOKEN_B}]\nname=Kedvencek\ntoken={_TOKEN_B}\n"
        f"[c.jpg]\nalbums={_TOKEN_B}\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def conn(tmp_path, library):
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        yield connection


class TestAlbumCatalogue:
    def test_albums_are_indexed(self, conn):
        by_token = {album.token: album for album in albums_in_index(conn)}
        assert set(by_token) == {_TOKEN_A, _TOKEN_B}
        assert by_token[_TOKEN_A].name == "Nyár 2025"
        assert by_token[_TOKEN_B].name == "Kedvencek"

    def test_album_defined_in_two_folders_appears_once(self, conn):
        tokens = [album.token for album in albums_in_index(conn)]
        assert tokens.count(_TOKEN_B) == 1, "a token az azonosító, nem a mappa"

    def test_photo_counts(self, conn):
        by_token = {album.token: album for album in albums_in_index(conn)}
        assert by_token[_TOKEN_A].photo_count == 2   # a.jpg, b.jpg
        assert by_token[_TOKEN_B].photo_count == 2   # a.jpg, c.jpg

    def test_date_is_kept(self, conn):
        by_token = {album.token: album for album in albums_in_index(conn)}
        assert by_token[_TOKEN_A].date == "2025-07-01T10:00:00"
        assert by_token[_TOKEN_B].date is None

    def test_sorted_by_name(self, conn):
        names = [album.name for album in albums_in_index(conn)]
        assert names == sorted(names, key=str.casefold)


class TestAlbumMembership:
    def test_photos_of_an_album(self, conn):
        names = sorted(photo.name for photo in album_photos(conn, _TOKEN_A))
        assert names == ["a.jpg", "b.jpg"]

    def test_membership_spans_folders(self, conn):
        photos = album_photos(conn, _TOKEN_B)
        folders = {photo.folder_path.rsplit("/", 1)[-1] for photo in photos}
        assert len(photos) == 2
        assert len(folders) == 2, "az album két mappát fog át"

    def test_unknown_token_gives_nothing(self, conn):
        assert album_photos(conn, "nincs-ilyen-token") == ()


class TestResync:
    def test_membership_follows_the_ini(self, conn, library):
        """Az albumból kivett kép a következő szinkron után eltűnik onnan."""
        ini = library / "nyaralas" / ".picasa.ini"
        ini.write_text(
            ini.read_text(encoding="utf-8").replace(
                f"[b.jpg]\nalbums={_TOKEN_A}\n", "[b.jpg]\n"
            ),
            encoding="utf-8",
        )
        sync_tree(conn, library, incremental=False)
        names = sorted(photo.name for photo in album_photos(conn, _TOKEN_A))
        assert names == ["a.jpg"]

    def test_deleted_album_disappears(self, conn, library):
        for folder in ("nyaralas", "varos"):
            ini = library / folder / ".picasa.ini"
            if ini.exists():
                ini.write_text(
                    "\n".join(
                        line
                        for line in ini.read_text(encoding="utf-8").splitlines()
                        if _TOKEN_B not in line and "Kedvencek" not in line
                    ),
                    encoding="utf-8",
                )
        sync_tree(conn, library, incremental=False)
        assert _TOKEN_B not in {album.token for album in albums_in_index(conn)}
