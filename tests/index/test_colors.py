"""A `photo_colors` gyorsítótár-tábla (#383) — a `photo_hashes` (#294)
mintájára: útvonal-azonosság szerinti upsert, batch-biztos lekérdezés."""

import sqlite3

from picasapy.index import open_index
from picasapy.index.colors import (
    ColorKey,
    load_color_tokens,
    paths_with_color,
    save_colors,
)


class TestLazyTable:
    def test_table_does_not_exist_before_use(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        assert "photo_colors" not in tables

    def test_first_save_creates_the_table(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [("/kepek/a.jpg", 1, 2, 0xFF0000, "red")])
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        assert "photo_colors" in tables


class TestLoadAndSave:
    def test_roundtrip(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [("/kepek/a.jpg", 11, 22, 0xFF0000, "red")])
            loaded = load_color_tokens(conn, [("/kepek/a.jpg", 11, 22)])
        assert loaded == {("/kepek/a.jpg", 11, 22): "red"}

    def test_unknown_key_absent(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            assert load_color_tokens(conn, [("/kepek/nincs.jpg", 1, 1)]) == {}

    def test_changed_mtime_or_size_invalidates(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [("/kepek/a.jpg", 11, 22, 1, "blue")])
            assert load_color_tokens(conn, [("/kepek/a.jpg", 99, 22)]) == {}
            assert load_color_tokens(conn, [("/kepek/a.jpg", 11, 99)]) == {}

    def test_rewriting_a_path_replaces_the_old_row(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [("/kepek/a.jpg", 11, 22, 1, "blue")])
            save_colors(conn, [("/kepek/a.jpg", 33, 44, 2, "red")])
            rows = conn.execute("SELECT COUNT(*) FROM photo_colors").fetchone()[0]
            assert rows == 1
            assert load_color_tokens(conn, [("/kepek/a.jpg", 33, 44)]) == {
                ("/kepek/a.jpg", 33, 44): "red"
            }

    def test_empty_inputs_are_noops(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [])
            assert load_color_tokens(conn, []) == {}

    def test_many_keys_do_not_hit_the_sqlite_variable_limit(self, tmp_path):
        items = [
            (f"/kepek/{i}.jpg", i, i, i, "red" if i % 2 else "blue")
            for i in range(2000)
        ]
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, items)
            keys: list[ColorKey] = [(path, mtime, size) for path, mtime, size, *_ in items]
            loaded = load_color_tokens(conn, keys)
        assert len(loaded) == 2000
        assert loaded[("/kepek/1999.jpg", 1999, 1999)] == "red"


class TestPathsWithColor:
    def test_matches_any_of_the_requested_tokens(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(
                conn,
                [
                    ("/kepek/a.jpg", 1, 1, 0xFF0000, "red"),
                    ("/kepek/b.jpg", 1, 1, 0x0000FF, "blue"),
                    ("/kepek/c.jpg", 1, 1, 0x00FF00, "green"),
                ],
            )
            paths = paths_with_color(conn, ["red", "blue"])
        assert paths == {"/kepek/a.jpg", "/kepek/b.jpg"}

    def test_empty_token_list_is_empty_set(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            assert paths_with_color(conn, []) == set()

    def test_many_tokens_do_not_hit_the_sqlite_variable_limit(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [("/kepek/a.jpg", 1, 1, 0xFF0000, "red")])
            tokens = ["red"] + [f"nem-létező-{i}" for i in range(2000)]
            assert paths_with_color(conn, tokens) == {"/kepek/a.jpg"}


class TestDroppability:
    def test_table_is_pure_cache_and_may_be_dropped(self, tmp_path):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            save_colors(conn, [("/kepek/a.jpg", 1, 1, 1, "blue")])
        raw = sqlite3.connect(db)
        raw.execute("DELETE FROM photo_colors")
        raw.commit()
        raw.close()
        with open_index(db) as conn:
            assert load_color_tokens(conn, [("/kepek/a.jpg", 1, 1)]) == {}
