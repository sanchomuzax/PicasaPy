"""Adatbázis-tömörítés — #449 („Compacting", `compacting.fen`).

A lényeg nem az, hogy a `VACUUM` fut, hanem hogy **megszakítható**, és
hogy megszakításkor az adatbázis érintetlen marad.
"""

import sqlite3

import pytest

from picasapy.index.compact import (
    CompactionCancelled,
    CompactionError,
    compact_database,
    needs_compaction,
    wasted_percent,
)


def _wasteful_db(path, rows=4000):
    """Adatbázis, amiben van mit visszanyerni: sok sort írunk, majd a
    többségét töröljük — a lapok a szabadlistára kerülnek."""
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, blob TEXT)")
    conn.executemany(
        "INSERT INTO t (blob) VALUES (?)", [("x" * 400,) for _ in range(rows)]
    )
    conn.commit()
    conn.execute("DELETE FROM t WHERE id > ?", (rows // 20,))
    conn.commit()
    conn.close()
    return path


class TestThreshold:
    def test_a_wasteful_database_is_worth_compacting(self, tmp_path):
        db = _wasteful_db(tmp_path / "index.db")

        assert wasted_percent(db) > 20
        assert needs_compaction(db) is True

    def test_a_fresh_database_is_not(self, tmp_path):
        db = tmp_path / "uj.db"
        conn = sqlite3.connect(db)
        conn.execute("CREATE TABLE t (id INTEGER)")
        conn.commit()
        conn.close()

        assert needs_compaction(db) is False

    def test_a_missing_database_is_not_an_error(self, tmp_path):
        assert wasted_percent(tmp_path / "nincs.db") == 0.0


class TestCompaction:
    def test_it_gives_back_disk_space(self, tmp_path):
        db = _wasteful_db(tmp_path / "index.db")
        before = db.stat().st_size

        result = compact_database(db)

        assert db.stat().st_size < before
        assert result.saved_bytes > 0
        assert result.before_bytes == before

    def test_the_data_survives(self, tmp_path):
        db = _wasteful_db(tmp_path / "index.db")
        conn = sqlite3.connect(db)
        expected = conn.execute("SELECT count(*) FROM t").fetchone()[0]
        conn.close()

        compact_database(db)

        conn = sqlite3.connect(db)
        try:
            assert conn.execute("SELECT count(*) FROM t").fetchone()[0] == expected
        finally:
            conn.close()

    def test_it_reports_progress(self, tmp_path):
        db = _wasteful_db(tmp_path / "index.db")
        ticks = []

        compact_database(db, progress=ticks.append)

        # szívverés, nem százalék — az a fontos, hogy egyáltalán jelez
        assert ticks and ticks == sorted(ticks)

    def test_cancelling_leaves_the_database_untouched(self, tmp_path):
        db = _wasteful_db(tmp_path / "index.db", rows=20000)
        conn = sqlite3.connect(db)
        expected = conn.execute("SELECT count(*) FROM t").fetchone()[0]
        conn.close()

        with pytest.raises(CompactionCancelled):
            compact_database(db, should_cancel=lambda: True)

        conn = sqlite3.connect(db)
        try:
            assert conn.execute("SELECT count(*) FROM t").fetchone()[0] == expected
        finally:
            conn.close()

    def test_a_missing_database_is_a_clean_error(self, tmp_path):
        with pytest.raises(CompactionError):
            compact_database(tmp_path / "nincs.db")
