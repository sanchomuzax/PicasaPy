"""A dHash-gyorsítótár tábla (#294): `photo_hashes` — a duplikátum-kereső
ismételt futásánál csak az ÚJ/megváltozott képek hash-elődnek újra."""

import sqlite3

import pytest

from picasapy.index import SCHEMA_VERSION, open_index
from picasapy.index.hashes import load_dhashes, save_dhashes


class TestSchema:
    def test_schema_version_is_current(self):
        # v11: offline mappa-jelölés (#459/5) — a `folders.offline` oszlop
        assert SCHEMA_VERSION == 11

    def test_fresh_database_has_photo_hashes_table(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
        assert "photo_hashes" in tables

    def test_v5_database_migrates_and_gains_the_table(self, tmp_path):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            conn.execute("PRAGMA user_version = 5")
            conn.execute("DROP TABLE photo_hashes")
            # #30: az 5-ös séma még nem ismerte a geo-oszlopokat sem
            conn.execute("ALTER TABLE photos DROP COLUMN geotag_ini")
            conn.execute("ALTER TABLE photos DROP COLUMN exif_lat")
            conn.execute("ALTER TABLE photos DROP COLUMN exif_lon")
            # #26: a face/face_group táblákat is eldobjuk, hogy a 8→9→10
            # migrációs lánc a valódi (nem idempotens ALTER-t is tartalmazó)
            # útvonalon fusson végig, ne a friss DDL-ből örökölt, már
            # bővített face táblán
            conn.execute("DROP TABLE face_group")
            conn.execute("DROP TABLE face")
            # #459/5: az offline oszlop a v11-ben érkezik
            conn.execute("ALTER TABLE folders DROP COLUMN offline")
            conn.commit()
        with open_index(db) as conn:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
            save_dhashes(conn, [("/kepek/a.jpg", 1, 2, 7)])
            assert load_dhashes(conn, [("/kepek/a.jpg", 1, 2)]) == {
                ("/kepek/a.jpg", 1, 2): 7
            }


class TestLoadAndSave:
    def test_roundtrip(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_dhashes(conn, [("/kepek/a.jpg", 11, 22, 0xDEAD)])
            assert load_dhashes(conn, [("/kepek/a.jpg", 11, 22)]) == {
                ("/kepek/a.jpg", 11, 22): 0xDEAD
            }

    def test_unknown_key_absent(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            assert load_dhashes(conn, [("/kepek/nincs.jpg", 1, 1)]) == {}

    def test_changed_mtime_or_size_invalidates(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_dhashes(conn, [("/kepek/a.jpg", 11, 22, 5)])
            assert load_dhashes(conn, [("/kepek/a.jpg", 99, 22)]) == {}
            assert load_dhashes(conn, [("/kepek/a.jpg", 11, 99)]) == {}

    def test_rewriting_a_path_replaces_the_old_row(self, tmp_path):
        """A tábla útvonalra kulcsol: a megváltozott fájl SORA cserélődik,
        nem halmozódik — így a cache mérete a könyvtárral marad arányos."""
        with open_index(tmp_path / "index.db") as conn:
            save_dhashes(conn, [("/kepek/a.jpg", 11, 22, 5)])
            save_dhashes(conn, [("/kepek/a.jpg", 33, 44, 6)])
            rows = conn.execute("SELECT COUNT(*) FROM photo_hashes").fetchone()[0]
            assert rows == 1
            assert load_dhashes(conn, [("/kepek/a.jpg", 33, 44)]) == {
                ("/kepek/a.jpg", 33, 44): 6
            }

    @pytest.mark.parametrize(
        "value", [0, 1, (1 << 63) - 1, 1 << 63, (1 << 64) - 1, 0xFFFFFFFF00000000]
    )
    def test_full_unsigned_64_bit_range_survives(self, tmp_path, value):
        """A dHash ELŐJEL NÉLKÜLI 64 bites, az SQLite INTEGER viszont
        előjeles — a 2^63 fölötti hash-t a rétegnek konvertálnia kell,
        különben az sqlite3 OverflowError-t dob (élesben minden második
        kép kiesne)."""
        with open_index(tmp_path / "index.db") as conn:
            save_dhashes(conn, [("/kepek/a.jpg", 1, 1, value)])
            assert load_dhashes(conn, [("/kepek/a.jpg", 1, 1)]) == {
                ("/kepek/a.jpg", 1, 1): value
            }

    def test_empty_inputs_are_noops(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_dhashes(conn, [])
            assert load_dhashes(conn, []) == {}

    def test_many_keys_do_not_hit_the_sqlite_variable_limit(self, tmp_path):
        """A lekérdezés nem egyetlen óriási IN (...) listával megy — 140k
        képnél az `SQLITE_MAX_VARIABLE_NUMBER` azonnal elhasalna."""
        items = [(f"/kepek/{i}.jpg", i, i, i) for i in range(5000)]
        with open_index(tmp_path / "index.db") as conn:
            save_dhashes(conn, items)
            keys = [(path, mtime, size) for path, mtime, size, _ in items]
            loaded = load_dhashes(conn, keys)
        assert len(loaded) == 5000
        assert loaded[("/kepek/4999.jpg", 4999, 4999)] == 4999

    def test_save_is_idempotent(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            save_dhashes(conn, [("/kepek/a.jpg", 1, 1, 3)])
            save_dhashes(conn, [("/kepek/a.jpg", 1, 1, 3)])
            assert conn.execute("SELECT COUNT(*) FROM photo_hashes").fetchone()[0] == 1


class TestDroppability:
    def test_table_is_pure_cache_and_may_be_dropped(self, tmp_path):
        """A `photo_hashes` tisztán származtatott gyorsítótár: eldobható,
        az index többi része ettől érintetlen marad (ez az indoka, hogy
        NEM a `photos` tábla bővítése lett)."""
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            save_dhashes(conn, [("/kepek/a.jpg", 1, 1, 3)])
        raw = sqlite3.connect(db)
        raw.execute("DELETE FROM photo_hashes")
        raw.commit()
        raw.close()
        with open_index(db) as conn:
            assert load_dhashes(conn, [("/kepek/a.jpg", 1, 1)]) == {}
