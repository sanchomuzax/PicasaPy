"""A `photo_colors` gyorsítótár-tábla (#383, #1480) — a `photo_hashes`
(#294) mintájára: útvonal-azonosság szerinti upsert, batch-biztos
lekérdezés. #1480 óta a tábla TOKEN-LISTÁT tárol (az akromatikus kép
egyszerre `black`, `white` és `gray`), és a besorolás a rasztert nézi,
nem az átlagszínt."""

import sqlite3

import cv2
import numpy as np

from picasapy.index import open_index
from picasapy.index.colors import (
    ColorKey,
    compute_photo_color,
    ensure_color_table,
    load_color_tokens,
    paths_with_color,
    save_colors,
)

ACHROMATIC = ("black", "white", "gray")


def _write_png(path, image):
    encoded_ok, encoded = cv2.imencode(".png", image)
    assert encoded_ok
    path.write_bytes(encoded.tobytes())
    return path


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
        result = compute_photo_color(_write_png(tmp_path / "atlagszin.png", image))

        assert result is not None
        assert result[0] == 0xFF1D1309

    def test_token_comes_from_the_raster_not_the_average(self, tmp_path):
        """#1480: a kép TÖBBSÉGE fakó kék (S = 51 alatt marad, tehát
        kimarad), egyetlen sarka viszont tiszta piros — az átlagszín
        kékes, a MÉRT besorolás mégis piros."""
        image = np.zeros((16, 16, 3), dtype=np.uint8)
        image[:, :] = (255, 235, 235)  # BGR: alig telített kék
        image[0, 0] = (0, 0, 255)  # BGR: tiszta piros
        result = compute_photo_color(_write_png(tmp_path / "raszter.png", image))

        assert result is not None
        assert result[1] == ("red",)

    def test_achromatic_photo_matches_all_three_tokens(self, tmp_path):
        image = np.full((8, 8, 3), 128, dtype=np.uint8)
        result = compute_photo_color(_write_png(tmp_path / "szurke.png", image))

        assert result is not None
        assert result[1] == ACHROMATIC

    def test_small_image_has_no_avgcolor_but_has_tokens(self, tmp_path):
        image = np.zeros((1, 2, 3), dtype=np.uint8)
        image[:, :] = (0, 0, 255)  # BGR: piros

        assert compute_photo_color(_write_png(tmp_path / "kicsi.png", image)) == (
            0,
            ("red",),
        )

    def test_unreadable_file(self, tmp_path):
        broken = tmp_path / "nem-kep.jpg"
        broken.write_bytes(b"ez nem kep")
        assert compute_photo_color(broken) is None


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
            save_colors(conn, [("/kepek/a.jpg", 1, 2, 0xFF0000, ("red",))])
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        assert "photo_colors" in tables

    def test_pre_1480_table_is_dropped_not_migrated(self, tmp_path):
        """A régi (átlagszínből számolt) `color_token` oszlopú tábla MOST
        MÁR hibás besorolást tárol — eldobjuk, a feltöltés újraszámolja."""
        with open_index(tmp_path / "index.db") as conn:
            conn.execute(
                "CREATE TABLE photo_colors (path TEXT PRIMARY KEY, "
                "mtime_ns INTEGER NOT NULL, size INTEGER NOT NULL, "
                "avgcolor INTEGER NOT NULL, color_token TEXT NOT NULL)"
            )
            conn.execute(
                "INSERT INTO photo_colors VALUES ('/kepek/regi.jpg', 1, 1, 0, 'blue')"
            )

            ensure_color_table(conn)

            columns = {row[1] for row in conn.execute("PRAGMA table_info(photo_colors)")}
            assert "color_tokens" in columns
            assert "color_token" not in columns
            assert conn.execute("SELECT COUNT(*) FROM photo_colors").fetchone()[0] == 0


class TestLoadAndSave:
    def test_roundtrip(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [("/kepek/a.jpg", 11, 22, 0xFF0000, ("red",))])
            loaded = load_color_tokens(conn, [("/kepek/a.jpg", 11, 22)])
        assert loaded == {("/kepek/a.jpg", 11, 22): ("red",)}

    def test_achromatic_triplet_roundtrip(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [("/kepek/a.jpg", 1, 1, 0, ACHROMATIC)])
            loaded = load_color_tokens(conn, [("/kepek/a.jpg", 1, 1)])
        assert loaded == {("/kepek/a.jpg", 1, 1): ACHROMATIC}

    def test_unknown_key_absent(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            assert load_color_tokens(conn, [("/kepek/nincs.jpg", 1, 1)]) == {}

    def test_changed_mtime_or_size_invalidates(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [("/kepek/a.jpg", 11, 22, 1, ("blue",))])
            assert load_color_tokens(conn, [("/kepek/a.jpg", 99, 22)]) == {}
            assert load_color_tokens(conn, [("/kepek/a.jpg", 11, 99)]) == {}

    def test_rewriting_a_path_replaces_the_old_row(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [("/kepek/a.jpg", 11, 22, 1, ("blue",))])
            save_colors(conn, [("/kepek/a.jpg", 33, 44, 2, ("red",))])
            rows = conn.execute("SELECT COUNT(*) FROM photo_colors").fetchone()[0]
            assert rows == 1
            assert load_color_tokens(conn, [("/kepek/a.jpg", 33, 44)]) == {
                ("/kepek/a.jpg", 33, 44): ("red",)
            }

    def test_empty_inputs_are_noops(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [])
            assert load_color_tokens(conn, []) == {}

    def test_many_keys_do_not_hit_the_sqlite_variable_limit(self, tmp_path):
        items = [
            (f"/kepek/{i}.jpg", i, i, i, ("red",) if i % 2 else ("blue",))
            for i in range(2000)
        ]
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, items)
            keys: list[ColorKey] = [
                (path, mtime, size) for path, mtime, size, *_ in items
            ]
            loaded = load_color_tokens(conn, keys)
        assert len(loaded) == 2000
        assert loaded[("/kepek/1999.jpg", 1999, 1999)] == ("red",)


class TestPathsWithColor:
    def test_matches_any_of_the_requested_tokens(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(
                conn,
                [
                    ("/kepek/a.jpg", 1, 1, 0xFF0000, ("red",)),
                    ("/kepek/b.jpg", 1, 1, 0x0000FF, ("blue",)),
                    ("/kepek/c.jpg", 1, 1, 0x00FF00, ("green",)),
                ],
            )
            paths = paths_with_color(conn, ["red", "blue"])
        assert paths == {"/kepek/a.jpg", "/kepek/b.jpg"}

    def test_each_achromatic_token_finds_the_same_photos(self, tmp_path):
        """#1480: a `black`, a `white` és a `gray` UGYANAZT adja — az
        eredeti nem tesz különbséget közöttük."""
        with open_index(tmp_path / "index.db") as conn:
            save_colors(
                conn,
                [
                    ("/kepek/szurke.jpg", 1, 1, 0, ACHROMATIC),
                    ("/kepek/piros.jpg", 1, 1, 0, ("red",)),
                ],
            )
            for token in ACHROMATIC:
                assert paths_with_color(conn, [token]) == {"/kepek/szurke.jpg"}

    def test_empty_token_list_is_empty_set(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            assert paths_with_color(conn, []) == set()

    def test_unknown_tokens_match_nothing(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_colors(conn, [("/kepek/a.jpg", 1, 1, 0xFF0000, ("red",))])
            tokens = ["red"] + [f"nem-létező-{i}" for i in range(2000)]
            assert paths_with_color(conn, tokens) == {"/kepek/a.jpg"}
            assert paths_with_color(conn, ["mályva"]) == set()


class TestDroppability:
    def test_table_is_pure_cache_and_may_be_dropped(self, tmp_path):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            save_colors(conn, [("/kepek/a.jpg", 1, 1, 1, ("blue",))])
        raw = sqlite3.connect(db)
        raw.execute("DELETE FROM photo_colors")
        raw.commit()
        raw.close()
        with open_index(db) as conn:
            assert load_color_tokens(conn, [("/kepek/a.jpg", 1, 1)]) == {}
