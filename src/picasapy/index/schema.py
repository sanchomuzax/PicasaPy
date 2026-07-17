"""Az SQLite index sémája — elvek a docs/benchmarks/rpi5-sqlite-inotify.md-ből.

Partial index a csillagozottakra, FTS5 external-content tábla triggerekkel a
név/felirat/kulcsszó keresésre. A séma verzióját a user_version pragma tartja.
"""

SCHEMA_VERSION = 1

DDL = """
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    has_ini INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS photos (
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

CREATE INDEX IF NOT EXISTS idx_photos_starred ON photos(folder_id) WHERE star = 1;

CREATE VIRTUAL TABLE IF NOT EXISTS photos_fts USING fts5(
    name, caption, keywords,
    content='photos', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS photos_fts_insert AFTER INSERT ON photos BEGIN
    INSERT INTO photos_fts(rowid, name, caption, keywords)
    VALUES (new.id, new.name, new.caption, new.keywords);
END;

CREATE TRIGGER IF NOT EXISTS photos_fts_delete AFTER DELETE ON photos BEGIN
    INSERT INTO photos_fts(photos_fts, rowid, name, caption, keywords)
    VALUES ('delete', old.id, old.name, old.caption, old.keywords);
END;

CREATE TRIGGER IF NOT EXISTS photos_fts_update AFTER UPDATE ON photos BEGIN
    INSERT INTO photos_fts(photos_fts, rowid, name, caption, keywords)
    VALUES ('delete', old.id, old.name, old.caption, old.keywords);
    INSERT INTO photos_fts(rowid, name, caption, keywords)
    VALUES (new.id, new.name, new.caption, new.keywords);
END;
"""
