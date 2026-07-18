"""Lekérdezések: mappalista, csillagozottak, FTS5 szövegkeresés."""

import pytest

from picasapy.index import (
    open_index,
    photos_in_folder,
    search_photos,
    starred_photos,
    sync_tree,
)


@pytest.fixture
def conn(tmp_path):
    root = tmp_path / "kepek"
    (root / "a").mkdir(parents=True)
    (root / "b").mkdir()
    (root / "a" / "alpha.jpg").write_bytes(b"1")
    (root / "a" / "beta.jpg").write_bytes(b"2")
    (root / "b" / "gamma.jpg").write_bytes(b"3")
    (root / "a" / ".picasa.ini").write_text(
        "[alpha.jpg]\nstar=yes\ncaption=balatoni naplemente\n"
        "[beta.jpg]\nkeywords=család,szülinap\n"
    , encoding="utf-8")
    (root / "b" / ".picasa.ini").write_text("[gamma.jpg]\nstar=yes\n", encoding="utf-8")
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, root)
        yield connection


class TestQueries:
    def test_photos_in_folder_sorted(self, conn, tmp_path):
        names = [p.name for p in photos_in_folder(conn, tmp_path / "kepek" / "a")]
        assert names == ["alpha.jpg", "beta.jpg"]

    def test_unknown_folder_empty(self, conn, tmp_path):
        assert photos_in_folder(conn, tmp_path / "nincs") == ()

    def test_starred_across_folders(self, conn):
        assert [p.name for p in starred_photos(conn)] == ["alpha.jpg", "gamma.jpg"]

    def test_search_caption(self, conn):
        assert [p.name for p in search_photos(conn, "naplemente")] == ["alpha.jpg"]

    def test_search_keyword(self, conn):
        assert [p.name for p in search_photos(conn, "szülinap")] == ["beta.jpg"]

    def test_search_name(self, conn):
        assert [p.name for p in search_photos(conn, "gamma")] == ["gamma.jpg"]

    def test_search_no_hit(self, conn):
        assert search_photos(conn, "nincsilyen") == ()

    def test_search_matches_folder_name(self, conn, tmp_path):
        # A kereső MINDENRE keres: mappanévre is (Picasa-viselkedés) —
        # az egyező nevű mappa összes képe találat.
        hits = [p.name for p in search_photos(conn, "a")]  # a mappa neve: "a"
        assert "alpha.jpg" in hits and "beta.jpg" in hits

    def test_search_folder_name_case_insensitive(self, conn):
        assert len(search_photos(conn, "B")) >= 1  # "b" mappa

    def test_search_quotes_fts_syntax(self, conn):
        # A felhasználói input nem FTS-szintaxis: nem dobhat hibát.
        assert search_photos(conn, 'nap" OR x') == ()

    def test_search_reflects_ini_update(self, conn, tmp_path):
        # FTS a frissítést is követi (external content + triggerek).
        (tmp_path / "kepek" / "a" / ".picasa.ini").write_text(
            "[alpha.jpg]\ncaption=hegyi túra\n"
        , encoding="utf-8")
        sync_tree(conn, tmp_path / "kepek")
        assert search_photos(conn, "naplemente") == ()
        assert [p.name for p in search_photos(conn, "túra")] == ["alpha.jpg"]
