"""Az SQLite index sémája — elvek a docs/benchmarks/rpi5-sqlite-inotify.md-ből.

A caption/keywords két forrásból jön: a `.picasa.ini`-ből (`*_ini`) és a fájl
IPTC-jéből (`*_file`, JPEG-nél ez az elsődleges — Picasa-viselkedés). A hatásos
értéket a lekérdezés COALESCE-olja; az FTS mindkét forrást indexeli.

A séma verzióját a user_version pragma tartja; a MIGRATIONS szótár vezet
verzióról verzióra, adatvesztés nélkül.
"""

SCHEMA_VERSION = 3

_FTS_DDL = """
CREATE VIRTUAL TABLE IF NOT EXISTS photos_fts USING fts5(
    name, caption_ini, keywords_ini, caption_file, keywords_file,
    content='photos', content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS photos_fts_insert AFTER INSERT ON photos BEGIN
    INSERT INTO photos_fts
        (rowid, name, caption_ini, keywords_ini, caption_file, keywords_file)
    VALUES (new.id, new.name, new.caption_ini, new.keywords_ini,
            new.caption_file, new.keywords_file);
END;

CREATE TRIGGER IF NOT EXISTS photos_fts_delete AFTER DELETE ON photos BEGIN
    INSERT INTO photos_fts(photos_fts, rowid, name, caption_ini, keywords_ini,
                           caption_file, keywords_file)
    VALUES ('delete', old.id, old.name, old.caption_ini, old.keywords_ini,
            old.caption_file, old.keywords_file);
END;

CREATE TRIGGER IF NOT EXISTS photos_fts_update AFTER UPDATE ON photos BEGIN
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

DDL = f"""
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    has_ini INTEGER NOT NULL DEFAULT 0,
    date TEXT
);

CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY,
    folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    star INTEGER NOT NULL DEFAULT 0,
    caption_ini TEXT,
    keywords_ini TEXT,
    rotate_steps INTEGER NOT NULL DEFAULT 0,
    taken_at TEXT,
    orientation INTEGER NOT NULL DEFAULT 1,
    width INTEGER,
    height INTEGER,
    caption_file TEXT,
    keywords_file TEXT,
    UNIQUE (folder_id, name)
);

CREATE INDEX IF NOT EXISTS idx_photos_starred ON photos(folder_id) WHERE star = 1;

{_FTS_DDL}
"""

# kulcs: kiinduló verzió → az azt következőre emelő szkript
MIGRATIONS = {
    1: f"""
DROP TRIGGER IF EXISTS photos_fts_insert;
DROP TRIGGER IF EXISTS photos_fts_delete;
DROP TRIGGER IF EXISTS photos_fts_update;
DROP TABLE IF EXISTS photos_fts;

ALTER TABLE photos RENAME COLUMN caption TO caption_ini;
ALTER TABLE photos RENAME COLUMN keywords TO keywords_ini;
ALTER TABLE photos ADD COLUMN taken_at TEXT;
ALTER TABLE photos ADD COLUMN orientation INTEGER NOT NULL DEFAULT 1;
ALTER TABLE photos ADD COLUMN width INTEGER;
ALTER TABLE photos ADD COLUMN height INTEGER;
ALTER TABLE photos ADD COLUMN caption_file TEXT;
ALTER TABLE photos ADD COLUMN keywords_file TEXT;

{_FTS_DDL}

INSERT INTO photos_fts(photos_fts) VALUES ('rebuild');
""",
    2: """
ALTER TABLE folders ADD COLUMN date TEXT;
UPDATE folders SET date = (
    SELECT MIN(p.taken_at) FROM photos p WHERE p.folder_id = folders.id
);
""",
}
