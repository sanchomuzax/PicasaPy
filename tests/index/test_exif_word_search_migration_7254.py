"""#7254: a meglévő index EXIF-szavai migrációkor újraépítés nélkül töltődnek."""

from __future__ import annotations

import sqlite3

import piexif

from picasapy.index import SCHEMA_VERSION, open_index, search_photos
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
    for column in ("artist_file", "copyright_file"):
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
    conn.execute("PRAGMA user_version=28")
    conn.commit()
    conn.close()


def test_v28_index_gains_artist_and_copyright_search_without_resync(tmp_path):
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

    with open_index(db) as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION
        assert {photo.name for photo in search_photos(conn, "delso")} == {"legacy.jpg"}
        assert {photo.name for photo in search_photos(conn, "cc sa")} == {"legacy.jpg"}
        row = conn.execute(
            "SELECT artist_file, copyright_file FROM photos WHERE name = 'legacy.jpg'"
        ).fetchone()
        assert row["artist_file"] == "diego delso"
        assert row["copyright_file"] == "cc by sa"
