"""SQLite index megnyitás: WAL, séma-létrehozás, verziózás."""

import pytest

from picasapy.index import open_index


class TestOpenIndex:
    def test_creates_database_file(self, tmp_path):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            assert db.exists()
            assert conn.execute("PRAGMA journal_mode").fetchone()[0] == "wal"

    def test_pragmas(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            assert conn.execute("PRAGMA synchronous").fetchone()[0] == 1  # NORMAL
            assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 1

    def test_schema_tables(self, tmp_path):
        with open_index(tmp_path / "index.db") as conn:
            names = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type IN ('table','index')"
                )
            }
        assert {"folders", "photos", "photos_fts"} <= names
        assert "idx_photos_starred" in names

    def test_old_sqlite_rejected_with_clear_message(self, tmp_path, monkeypatch):
        import picasapy.index.database as db_module

        monkeypatch.setattr(db_module, "_MIN_SQLITE", (999, 0, 0))
        with pytest.raises(RuntimeError, match="SQLite"):
            with open_index(tmp_path / "index.db"):
                pass

    def test_schema_failure_wrapped_with_clear_message(self, tmp_path, monkeypatch):
        import picasapy.index.database as db_module

        monkeypatch.setattr(db_module, "DDL", "CREATE SYNTAX ERROR;")
        with pytest.raises(RuntimeError, match="FTS5"):
            with open_index(tmp_path / "index.db"):
                pass

    def test_newer_schema_version_rejected(self, tmp_path):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            conn.execute("PRAGMA user_version=999")
            conn.commit()
        with pytest.raises(RuntimeError, match="sémaverzió"):
            with open_index(db):
                pass

    def test_reopen_keeps_data(self, tmp_path):
        db = tmp_path / "index.db"
        with open_index(db) as conn:
            conn.execute("INSERT INTO folders(path) VALUES ('/x')")
            conn.commit()
        with open_index(db) as conn:
            assert conn.execute("SELECT count(*) FROM folders").fetchone()[0] == 1
