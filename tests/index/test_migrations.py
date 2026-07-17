"""Séma-migráció: v1 → aktuális, adatvesztés nélkül."""

import sqlite3

import pytest

from picasapy.index import SCHEMA_VERSION, open_index, photos_in_folder, search_photos

# A v1 séma befagyasztott másolata (2026-07-17 előtti állapot) — a migrációs
# tesztnek történeti sémára van szüksége, nem az aktuálisra.
DDL_V1 = """
CREATE TABLE folders (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    has_ini INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE photos (
    id INTEGER PRIMARY KEY,
    folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    star INTEGER NOT NULL DEFAULT 0,
    caption TEXT,
    keywords TEXT,
    rotate_steps INTEGER NOT NULL DEFAULT 0,
    UNIQUE (folder_id, name)
);
CREATE INDEX idx_photos_starred ON photos(folder_id) WHERE star = 1;
CREATE VIRTUAL TABLE photos_fts USING fts5(
    name, caption, keywords, content='photos', content_rowid='id'
);
CREATE TRIGGER photos_fts_insert AFTER INSERT ON photos BEGIN
    INSERT INTO photos_fts(rowid, name, caption, keywords)
    VALUES (new.id, new.name, new.caption, new.keywords);
END;
CREATE TRIGGER photos_fts_delete AFTER DELETE ON photos BEGIN
    INSERT INTO photos_fts(photos_fts, rowid, name, caption, keywords)
    VALUES ('delete', old.id, old.name, old.caption, old.keywords);
END;
CREATE TRIGGER photos_fts_update AFTER UPDATE ON photos BEGIN
    INSERT INTO photos_fts(photos_fts, rowid, name, caption, keywords)
    VALUES ('delete', old.id, old.name, old.caption, old.keywords);
    INSERT INTO photos_fts(rowid, name, caption, keywords)
    VALUES (new.id, new.name, new.caption, new.keywords);
END;
PRAGMA user_version = 1;
"""


def _make_v1_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(DDL_V1)
    conn.execute("INSERT INTO folders(id, path, has_ini) VALUES (1, '/kepek', 1)")
    conn.execute(
        "INSERT INTO photos(folder_id, name, kind, size, mtime_ns, star, caption,"
        " keywords) VALUES (1, 'a.jpg', 'photo', 10, 5, 1, 'régi felirat', 'régi,kulcs')"
    )
    conn.commit()
    conn.close()


class TestMigrationV1:
    def test_upgrades_to_current_version(self, tmp_path):
        db = tmp_path / "index.db"
        _make_v1_db(db)
        with open_index(db) as conn:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION

    def test_data_preserved(self, tmp_path):
        db = tmp_path / "index.db"
        _make_v1_db(db)
        with open_index(db) as conn:
            photo = photos_in_folder(conn, "/kepek")[0]
            assert photo.name == "a.jpg"
            assert photo.star is True
            assert photo.caption == "régi felirat"
            assert photo.keywords == "régi,kulcs"
            assert photo.orientation == 1  # új oszlop default

    def test_fts_works_after_migration(self, tmp_path):
        db = tmp_path / "index.db"
        _make_v1_db(db)
        with open_index(db) as conn:
            assert [p.name for p in search_photos(conn, "felirat")] == ["a.jpg"]


class TestMigrationSafety:
    def test_failed_migration_rolls_back_completely(self, tmp_path, monkeypatch):
        # Félbeszakadó migráció nem hagyhat félig átalakított sémát:
        # vagy teljesen lefut, vagy érintetlen v1 marad (újrapróbálható).
        import picasapy.index.database as db_module

        db = tmp_path / "index.db"
        _make_v1_db(db)
        broken = {1: "ALTER TABLE photos RENAME COLUMN caption TO caption_x;\nHIBAS SQL;"}
        monkeypatch.setattr(db_module, "MIGRATIONS", broken)
        with pytest.raises(RuntimeError, match="migrá"):
            with open_index(db):
                pass
        raw = sqlite3.connect(db)
        columns = {row[1] for row in raw.execute("PRAGMA table_info(photos)")}
        version = raw.execute("PRAGMA user_version").fetchone()[0]
        raw.close()
        assert "caption" in columns  # a rename visszagördült
        assert "caption_x" not in columns
        assert version == 1

    def test_failed_migration_is_retryable(self, tmp_path, monkeypatch):
        import picasapy.index.database as db_module

        db = tmp_path / "index.db"
        _make_v1_db(db)
        broken = {1: "HIBAS SQL;"}
        monkeypatch.setattr(db_module, "MIGRATIONS", broken)
        with pytest.raises(RuntimeError):
            with open_index(db):
                pass
        monkeypatch.undo()
        with open_index(db) as conn:  # ép v1-ről most már sikerül
            assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION

    def test_missing_migration_path_clear_error(self, tmp_path, monkeypatch):
        import picasapy.index.database as db_module

        db = tmp_path / "index.db"
        _make_v1_db(db)
        monkeypatch.setattr(db_module, "MIGRATIONS", {})
        with pytest.raises(RuntimeError, match="migrációs útvonal"):
            with open_index(db):
                pass
