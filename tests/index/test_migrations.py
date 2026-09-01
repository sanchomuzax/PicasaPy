"""Séma-migráció: v1 → aktuális, adatvesztés nélkül."""

import sqlite3

import pytest

from picasapy.index import SCHEMA_VERSION, open_index, photos_in_folder, search_photos
from picasapy.index.schema import DDL

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


class TestMigrationV4Hidden:
    def test_v1_upgrade_gains_hidden_column_default_false(self, tmp_path):
        # #17: a hidden oszlop az 5-ös sémában érkezik, defaultja 0
        db = tmp_path / "index.db"
        _make_v1_db(db)
        with open_index(db) as conn:
            photo = photos_in_folder(conn, "/kepek")[0]
            assert photo.hidden is False


class TestMigrationV11Offline:
    def test_v1_upgrade_gains_offline_column_default_zero(self, tmp_path):
        # #459/5: az offline oszlop a 11-es sémában érkezik, minden meglévő
        # mappa elérhetőnek (0) indul — nem kell újraindexelés
        db = tmp_path / "index.db"
        _make_v1_db(db)
        with open_index(db) as conn:
            rows = conn.execute("SELECT path, offline FROM folders").fetchall()
            assert rows and all(row["offline"] == 0 for row in rows)


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


class TestAlbumsMigration:
    """#9 (séma v8): a virtuális albumok táblái a MEGLÉVŐ indexekhez is
    hozzájönnek, újraindexelés nélkül — üresen, a következő szinkron tölti
    fel őket az ini-kből."""

    def _v7_database(self, tmp_path):
        """Egy v7-es (album-táblák nélküli) adatbázis, egy fotóval."""
        path = tmp_path / "regi.db"
        raw = sqlite3.connect(path)
        raw.executescript(DDL)
        raw.executescript(
            "DROP TABLE IF EXISTS photo_albums;"
            "DROP TABLE IF EXISTS albums;"
            # a v7 séma a face táblát (v9-ben jött) és az embedding/csoport-
            # bővítést (v10) sem ismerte — hiteles v7 fixture ezek nélkül.
            "DROP TABLE IF EXISTS face;"
            "DROP TABLE IF EXISTS face_group;"
            # #459/5: az offline oszlop a v11-ben érkezik
            "ALTER TABLE folders DROP COLUMN offline;"
            # #1637: a hidden oszlop a v13-ban érkezik
            "ALTER TABLE folders DROP COLUMN hidden;"
            # #1644: az unread oszlop a v15-ben érkezik
            "ALTER TABLE folders DROP COLUMN unread;"
            "PRAGMA user_version = 7;"
        )
        raw.execute("INSERT INTO folders (id, path) VALUES (1, '/kepek')")
        raw.execute(
            "INSERT INTO photos (id, folder_id, name, kind, size, mtime_ns)"
            " VALUES (1, 1, 'a.jpg', 'image', 10, 1)"
        )
        raw.commit()
        raw.close()
        return path

    def test_tables_appear_and_data_survives(self, tmp_path):
        path = self._v7_database(tmp_path)
        with open_index(path) as conn:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            assert {"albums", "photo_albums"} <= tables
            # a meglévő adat érintetlen
            assert conn.execute("SELECT count(*) FROM photos").fetchone()[0] == 1
            # az új táblák üresek — nincs újraindexelés
            assert conn.execute("SELECT count(*) FROM albums").fetchone()[0] == 0

    def test_album_queries_work_on_the_migrated_database(self, tmp_path):
        from picasapy.index.albums import album_photos, albums_in_index

        path = self._v7_database(tmp_path)
        with open_index(path) as conn:
            assert albums_in_index(conn) == ()
            assert album_photos(conn, "barmi") == ()


class TestFaceMigration:
    """#26 (séma v9): a saját arc-detektálás `face` táblája a MEGLÉVŐ
    indexekhez is hozzájön, újraindexelés nélkül — üresen, a következő
    arc-szkennelés (`FaceScanController`) tölti fel."""

    def _v8_database(self, tmp_path):
        path = tmp_path / "regi.db"
        raw = sqlite3.connect(path)
        raw.executescript(DDL)
        raw.executescript(
            "DROP TABLE IF EXISTS face;\n"
            # #459/5: az offline oszlop a v11-ben érkezik
            "ALTER TABLE folders DROP COLUMN offline;\n"
            # #1637: a hidden oszlop a v13-ban érkezik
            "ALTER TABLE folders DROP COLUMN hidden;\n"
            # #1644: az unread oszlop a v15-ben érkezik
            "ALTER TABLE folders DROP COLUMN unread;\n"
            "PRAGMA user_version = 8;"
        )
        raw.execute("INSERT INTO folders (id, path) VALUES (1, '/kepek')")
        raw.execute(
            "INSERT INTO photos (id, folder_id, name, kind, size, mtime_ns)"
            " VALUES (1, 1, 'a.jpg', 'image', 10, 1)"
        )
        raw.commit()
        raw.close()
        return path

    def test_table_appears_and_data_survives(self, tmp_path):
        path = self._v8_database(tmp_path)
        with open_index(path) as conn:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            assert "face" in tables
            assert conn.execute("SELECT count(*) FROM photos").fetchone()[0] == 1
            assert conn.execute("SELECT count(*) FROM face").fetchone()[0] == 0

    def test_face_queries_work_on_the_migrated_database(self, tmp_path):
        from picasapy.index.faces_detected import unnamed_album_photos

        path = self._v8_database(tmp_path)
        with open_index(path) as conn:
            assert unnamed_album_photos(conn) == ()


class TestFaceEmbeddingMigration:
    """#26 (séma v10): az `embedding`/`group_id` oszlop és a `face_group`
    tábla a MEGLÉVŐ (v9) indexekhez is hozzájön, a `face` sorok tartalma és
    a fotók érintetlenül maradnak — adatvesztés nélkül."""

    def _v9_database(self, tmp_path):
        path = tmp_path / "regi.db"
        raw = sqlite3.connect(path)
        raw.executescript(DDL)
        raw.executescript(
            "DROP TABLE IF EXISTS face_group;\n"
            "DROP INDEX IF EXISTS idx_face_group;\n"
            # #26 (v12): a név-oszlopok — az indexüket ELŐBB kell eldobni,
            # különben a DROP COLUMN a tárolt DDL újraparse-olásán elhasal
            "DROP INDEX IF EXISTS idx_face_person;\n"
            "ALTER TABLE face DROP COLUMN person_name;\n"
            "ALTER TABLE face DROP COLUMN suggested_name;\n"
            "ALTER TABLE face DROP COLUMN embedding;\n"
            "ALTER TABLE face DROP COLUMN group_id;\n"
            # #459/5: az offline oszlop a v11-ben érkezik
            "ALTER TABLE folders DROP COLUMN offline;\n"
            # #1637: a hidden oszlop a v13-ban érkezik
            "ALTER TABLE folders DROP COLUMN hidden;\n"
            # #1644: az unread oszlop a v15-ben érkezik
            "ALTER TABLE folders DROP COLUMN unread;\n"
            "PRAGMA user_version = 9;"
        )
        raw.execute("INSERT INTO folders (id, path) VALUES (1, '/kepek')")
        raw.execute(
            "INSERT INTO photos (id, folder_id, name, kind, size, mtime_ns)"
            " VALUES (1, 1, 'a.jpg', 'image', 10, 1)"
        )
        raw.execute(
            "INSERT INTO face (id, photo_id, rect_left, rect_top, rect_right,"
            " rect_bottom, det_conf, right_eye_x, right_eye_y, left_eye_x,"
            " left_eye_y, nose_x, nose_y, mouth_right_x, mouth_right_y,"
            " mouth_left_x, mouth_left_y, state)"
            " VALUES (1, 1, 5, 10, 40, 50, 0.9, 10, 20, 30, 20, 20, 30, 15, 40,"
            " 25, 40, 'unnamed')"
        )
        raw.commit()
        raw.close()
        return path

    def test_columns_and_table_appear_data_survives(self, tmp_path):
        path = self._v9_database(tmp_path)
        with open_index(path) as conn:
            assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            assert "face_group" in tables
            face_columns = {row[1] for row in conn.execute("PRAGMA table_info(face)")}
            assert {"embedding", "group_id"} <= face_columns
            # a meglévő arc-sor tartalma érintetlen
            row = conn.execute("SELECT * FROM face WHERE id = 1").fetchone()
            assert row["rect_left"] == 5
            assert row["state"] == "unnamed"
            assert row["embedding"] is None
            assert row["group_id"] is None

    def test_fresh_database_has_embedding_columns_too(self, tmp_path):
        # a friss (nem migrált) telepítés is rendelkezik a v10 oszlopokkal
        with open_index(tmp_path / "friss.db") as conn:
            face_columns = {row[1] for row in conn.execute("PRAGMA table_info(face)")}
            assert {"embedding", "group_id"} <= face_columns
            tables = {
                row[0]
                for row in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'"
                )
            }
            assert "face_group" in tables
