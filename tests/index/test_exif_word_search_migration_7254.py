"""#7254: a meglévő index EXIF-szavai migrációkor újraépítés nélkül töltődnek."""

from __future__ import annotations

import os
import sqlite3
import time

import piexif

from picasapy.index import SCHEMA_VERSION, open_index, search_photos, sync_tree
from picasapy.index.schema import DDL
from tests.support.jpeg_factory import make_jpeg


_V28_FTS_DDL = """
CREATE VIRTUAL TABLE photos_fts USING fts5(
    name, caption_ini, keywords_ini, caption_file, keywords_file,
    content='photos', content_rowid='id'
);
CREATE TRIGGER photos_fts_insert AFTER INSERT ON photos BEGIN
    INSERT INTO photos_fts
        (rowid, name, caption_ini, keywords_ini, caption_file, keywords_file)
    VALUES (new.id, new.name, new.caption_ini, new.keywords_ini,
            new.caption_file, new.keywords_file);
END;
CREATE TRIGGER photos_fts_delete AFTER DELETE ON photos BEGIN
    INSERT INTO photos_fts(photos_fts, rowid, name, caption_ini, keywords_ini,
                           caption_file, keywords_file)
    VALUES ('delete', old.id, old.name, old.caption_ini, old.keywords_ini,
            old.caption_file, old.keywords_file);
END;
CREATE TRIGGER photos_fts_update AFTER UPDATE ON photos BEGIN
    INSERT INTO photos_fts(photos_fts, rowid, name, caption_ini, keywords_ini,
                           caption_file, keywords_file)
    VALUES ('delete', old.id, old.name, old.caption_ini, old.keywords_ini,
            old.caption_file, old.keywords_file);
    INSERT INTO photos_fts
        (rowid, name, caption_ini, keywords_ini, caption_file, keywords_file)
    VALUES (new.id, new.name, new.caption_ini, new.keywords_ini,
            new.caption_file, new.keywords_file);
END;
"""


def _v28_database(path, photo_path):
    conn = sqlite3.connect(path)
    conn.executescript(DDL)
    conn.executescript(
        "DROP TRIGGER IF EXISTS photos_fts_insert;"
        "DROP TRIGGER IF EXISTS photos_fts_delete;"
        "DROP TRIGGER IF EXISTS photos_fts_update;"
        "DROP TABLE photos_fts;"
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(photos)")}
    for column in ("artist_file", "copyright_file", "exif_words_pending"):
        if column in columns:
            conn.execute(f"ALTER TABLE photos DROP COLUMN {column}")
    conn.executescript(_V28_FTS_DDL)
    stat = photo_path.stat()
    conn.execute("INSERT INTO folders(id, path) VALUES (1, ?)", (str(photo_path.parent),))
    conn.execute(
        "INSERT INTO photos(folder_id, name, kind, size, mtime_ns) "
        "VALUES (1, ?, 'photo', ?, ?)",
        (photo_path.name, stat.st_size, stat.st_mtime_ns),
    )
    folder_mtime_ns = time.time_ns() - 10 * 60 * 1_000_000_000
    os.utime(photo_path.parent, ns=(folder_mtime_ns, folder_mtime_ns))
    conn.execute(
        "CREATE TABLE folder_scan_state ("
        "path TEXT PRIMARY KEY, mtime_ns INTEGER NOT NULL, ini_mtime_ns INTEGER, "
        "filetype_signature TEXT)"
    )
    conn.execute(
        "INSERT INTO folder_scan_state(path, mtime_ns, ini_mtime_ns, "
        "filetype_signature) VALUES (?, ?, NULL, NULL)",
        (str(photo_path.parent), folder_mtime_ns),
    )
    conn.execute("PRAGMA user_version=28")
    conn.commit()
    conn.close()


def test_v28_migration_defers_exif_reads_to_one_background_sync(
    tmp_path, monkeypatch
):
    folder = tmp_path / "library"
    folder.mkdir()
    photo_path = make_jpeg(folder / "legacy.jpg")
    piexif.insert(
        piexif.dump(
            {
                "0th": {
                    piexif.ImageIFD.Artist: b"Diego Delso",
                    piexif.ImageIFD.Copyright: b"CC-BY-SA 4.0",
                },
                "Exif": {},
                "GPS": {},
            }
        ),
        str(photo_path),
    )
    db = tmp_path / "index.db"
    _v28_database(db, photo_path)

    def forbidden_migration_read(_path):
        raise AssertionError("a séma-migráció nem nyithat meg képfájlt")

    monkeypatch.setattr(
        "picasapy.metadata.read_file_metadata", forbidden_migration_read
    )
    with open_index(db) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert conn.execute(
            "SELECT exif_words_pending FROM photos WHERE name = 'legacy.jpg'"
        ).fetchone()[0] == 1

    import picasapy.index.sync as sync_module

    original_read = sync_module.read_file_metadata
    read_paths = []

    def counted_read(path):
        read_paths.append(path)
        return original_read(path)

    monkeypatch.setattr(sync_module, "read_file_metadata", counted_read)
    with open_index(db) as conn:
        sync_tree(conn, photo_path.parent)
        assert {photo.name for photo in search_photos(conn, "delso")} == {"legacy.jpg"}
        assert {photo.name for photo in search_photos(conn, "cc")} == {"legacy.jpg"}
        assert {photo.name for photo in search_photos(conn, "sa")} == {"legacy.jpg"}
        assert conn.execute(
            "SELECT exif_words_pending FROM photos WHERE name = 'legacy.jpg'"
        ).fetchone()[0] == 0
        assert len(read_paths) == 1

        sync_tree(conn, photo_path.parent)
        assert len(read_paths) == 1
