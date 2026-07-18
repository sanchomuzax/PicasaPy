"""Lekérdezések: mappalista, csillagozottak, FTS5 szövegkeresés."""

import pytest

from picasapy.index import (
    open_index,
    photos_in_folder,
    search_photos,
    search_suggestions,
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


@pytest.fixture
def suggest_conn(tmp_path):
    """Könyvtár javaslat-tesztekhez: mappák + virtuális albumok (#7)."""
    root = tmp_path / "kepek"
    (root / "HS logo").mkdir(parents=True)
    (root / "Sanoma Media logo").mkdir()
    (root / "nyaralas").mkdir()
    for i in range(2):
        (root / "HS logo" / f"h{i}.jpg").write_bytes(b"x")
    (root / "Sanoma Media logo" / "s0.jpg").write_bytes(b"x")
    (root / "nyaralas" / "n0.jpg").write_bytes(b"x")
    (root / "HS logo" / ".picasa.ini").write_text(
        "[.album:aabb01]\nname=logo valogatas\n"
        "[h0.jpg]\nalbums=aabb01\n"
        "[h1.jpg]\nalbums=aabb01\n",
        encoding="utf-8",
    )
    (root / "Sanoma Media logo" / ".picasa.ini").write_text(
        "[.album:aabb01]\nname=logo valogatas\n"
        "[.album:ccdd02]\nname=nyari kepek\n"
        "[s0.jpg]\nalbums=aabb01,ccdd02\n",
        encoding="utf-8",
    )
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, root)
        yield connection


class TestSearchSuggestions:
    def test_folder_suggestions_with_counts(self, suggest_conn):
        result = search_suggestions(suggest_conn, "logo")
        folders = [s for s in result if s.kind == "folder"]
        assert [(s.name, s.count) for s in folders] == [
            ("HS logo", 2),
            ("Sanoma Media logo", 1),
        ]

    def test_album_suggestions_aggregate_across_inis(self, suggest_conn):
        # Ugyanaz az album-token több .picasa.ini-ben is előfordulhat —
        # a javaslat egyszer jelenik meg, összesített darabszámmal.
        result = search_suggestions(suggest_conn, "logo")
        albums = [s for s in result if s.kind == "album"]
        assert [(s.name, s.count) for s in albums] == [("logo valogatas", 3)]

    def test_match_is_substring_and_casefold(self, suggest_conn):
        # Picasa: a "logo" a "Sanoma Media logo" közepén is talál; ékezet/
        # kisbetű-nagybetű nem számít.
        assert search_suggestions(suggest_conn, "LOGO")
        assert search_suggestions(suggest_conn, "NYARI")

    def test_folders_before_albums(self, suggest_conn):
        kinds = [s.kind for s in search_suggestions(suggest_conn, "logo")]
        assert kinds == sorted(kinds, key=lambda k: k != "folder")

    def test_empty_query_no_suggestions(self, suggest_conn):
        assert search_suggestions(suggest_conn, "") == ()
        assert search_suggestions(suggest_conn, "   ") == ()

    def test_no_hit(self, suggest_conn):
        assert search_suggestions(suggest_conn, "nincsilyen") == ()

    def test_limit_respected(self, suggest_conn):
        assert len(search_suggestions(suggest_conn, "o", limit=2)) == 2

    def test_folder_param_is_path_album_param_is_token(self, suggest_conn):
        result = search_suggestions(suggest_conn, "logo")
        folder = next(s for s in result if s.kind == "folder")
        album = next(s for s in result if s.kind == "album")
        assert folder.param.endswith("HS logo")
        assert album.param == "aabb01"
