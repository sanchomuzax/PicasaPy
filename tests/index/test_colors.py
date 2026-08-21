"""A `photo_colors` gyorsítótár-tábla (#383) — a `photo_hashes` (#294)
mintájára: útvonal-azonosság szerinti upsert, batch-biztos lekérdezés."""

import sqlite3

import cv2
import numpy as np

from picasapy.index import open_index
from picasapy.index.colors import (
    ColorKey,
    compute_photo_color,
    load_color_tokens,
    paths_with_color,
    save_colors,
)


class TestComputePhotoColor:
    def test_stores_picasa_opaque_argb_value(self, tmp_path):
        """Az OpenCV BGR-dekódolóhoz a hiányzó alfa átlátszatlan (#1171)."""
        image = np.array(
            [
                [(9, 19, 29), (10, 20, 30)],
                [(10, 20, 30), (10, 20, 30)],
            ],
            dtype=np.uint8,
        )
        encoded_ok, encoded = cv2.imencode(".png", image)
        assert encoded_ok
        photo = tmp_path / "atlagszin.png"
        photo.write_bytes(encoded.tobytes())

        result = compute_photo_color(photo)

        assert result is not None
        assert result[0] == 0xFF1D1309

    def test_small_image_has_no_avgcolor(self, tmp_path):
        image = np.zeros((1, 2, 3), dtype=np.uint8)
        encoded_ok, encoded = cv2.imencode(".png", image)
        assert encoded_ok
        photo = tmp_path / "kicsi.png"
        photo.write_bytes(encoded.tobytes())

        assert compute_photo_color(photo) == (0, "")


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
