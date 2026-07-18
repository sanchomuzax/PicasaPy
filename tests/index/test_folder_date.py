"""Mappa-dátum (séma v3): automatikus dátum = a legrégebbi kép felvételi
ideje — a Picasa erre rendezi a mappalistát (legújabb elöl)."""

import sqlite3

import pytest

from picasapy.index import SCHEMA_VERSION, open_index, sync_tree
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "regi").mkdir(parents=True)
    (root / "uj").mkdir()
    (root / "datumtalan").mkdir()
    make_jpeg(root / "regi" / "a.jpg", taken_at="2020:03:01 10:00:00")
    make_jpeg(root / "regi" / "b.jpg", taken_at="2020:05-01 10:00:00".replace("-", ":"))
    make_jpeg(root / "uj" / "c.jpg", taken_at="2025:01:15 08:00:00")
    make_jpeg(root / "datumtalan" / "d.jpg")  # nincs EXIF-dátum
    return root


class TestFolderDate:
    def test_auto_date_is_oldest_photo(self, tmp_path, library):
        with open_index(tmp_path / "i.db") as conn:
            sync_tree(conn, library)
            rows = dict(
                conn.execute("SELECT path, date FROM folders").fetchall()
            )
        assert rows[str(library / "regi")].startswith("2020-03-01")
        assert rows[str(library / "uj")].startswith("2025-01-15")
        assert rows[str(library / "datumtalan")] is None

    def test_resync_updates_date(self, tmp_path, library):
        with open_index(tmp_path / "i.db") as conn:
            sync_tree(conn, library)
            make_jpeg(library / "uj" / "meguj.jpg", taken_at="2019:06:01 09:00:00")
            sync_tree(conn, library)
            date = conn.execute(
                "SELECT date FROM folders WHERE path = ?",
                (str(library / "uj"),),
            ).fetchone()[0]
        assert date.startswith("2019-06-01")


class TestMigrationV3:
    def test_v2_upgrades_with_backfill(self, tmp_path, library):
        # v2 séma szimulálása: a friss adatbázisból eldobjuk a v2 utáni
        # oszlopokat (date, filters), és a verziót 2-re állítjuk — így a
        # teljes 2→3→4 migrációs lánc fut le.
        db = tmp_path / "i.db"
        with open_index(db) as conn:
            sync_tree(conn, library)
        raw = sqlite3.connect(db)
        raw.execute("ALTER TABLE folders DROP COLUMN date")
        raw.execute("ALTER TABLE photos DROP COLUMN filters")
        raw.execute("PRAGMA user_version=2")
        raw.commit()
        raw.close()
        with open_index(db) as conn:
            assert (
                conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
            )
            date = conn.execute(
                "SELECT date FROM folders WHERE path = ?",
                (str(library / "regi"),),
            ).fetchone()[0]
        assert date.startswith("2020-03-01")  # backfill megtörtént
