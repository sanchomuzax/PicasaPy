"""Segédek történeti keresésiindex-sémák teszt-fixture-eihez."""

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
INSERT INTO photos_fts(photos_fts) VALUES ('rebuild');
"""


def downgrade_search_schema_to_v28(conn):
    """A jelenlegi DDL-ből hiteles, EXIF-keresés előtti indexet készít."""
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
