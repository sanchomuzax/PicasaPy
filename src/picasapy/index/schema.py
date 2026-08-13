"""Az SQLite index sémája — elvek a docs/benchmarks/rpi5-sqlite-inotify.md-ből.

A caption/keywords két forrásból jön: a `.picasa.ini`-ből (`*_ini`) és a fájl
IPTC-jéből (`*_file`, JPEG-nél ez az elsődleges — Picasa-viselkedés). A hatásos
értéket a lekérdezés COALESCE-olja; az FTS mindkét forrást indexeli.

A séma verzióját a user_version pragma tartja; a MIGRATIONS szótár vezet
verzióról verzióra, adatvesztés nélkül.
"""

SCHEMA_VERSION = 12

# #294 — a duplikátum-kereső dHash-gyorsítótára. SZÁNDÉKOSAN külön tábla,
# nem a `photos` bővítése:
#   * tisztán származtatott adat (a képből bármikor újraszámolható), ezért
#     eldobható/üríthető anélkül, hogy az index bármely más része sérülne;
#   * a `photos` bővítése az FTS5 külső-tartalmú (content='photos') tábla és
#     a három szinkron-trigger környékét bolygatná — a triggerek csak a
#     szöveges oszlopokat indexelik, egy bináris hash-oszlopnak semmi
#     keresnivalója abban a szerződésben;
#   * a kulcs a fájl AZONOSSÁGA (útvonal + mtime_ns + méret), nem a fotó
#     index-beli id-je — így a hash a fotó újraindexelését (új id) is
#     túléli, és a keresés indexen kívüli útvonalra is használható.
# A PRIMARY KEY az útvonal: a megváltozott fájl SORA cserélődik (upsert),
# nem halmozódik — a cache mérete a könyvtárral marad arányos.
_PHOTO_HASHES_DDL = """
CREATE TABLE IF NOT EXISTS photo_hashes (
    path TEXT PRIMARY KEY,
    mtime_ns INTEGER NOT NULL,
    size INTEGER NOT NULL,
    dhash INTEGER NOT NULL
);
"""

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


# #9: virtuális albumok. Az azonosító a `.picasa.ini` `[.album:<token>]`
# szekciójának tokenje. Ugyanaz az album TÖBB mappa ini-jében is szerepel
# (a Picasa minden érintett mappába kiírja a definíciót), ezért a tárolás
# DEFINÍCIÓNKÉNTI: (mappa, token) a kulcs, és a hasáb-lekérdezés vonja
# össze őket tokenre. Így a mappánként futó, idempotens szinkron egyszerűen
# újraírhatja a saját sorait, és az ini-ből törölt album magától kiesik —
# akkor is, ha másik mappa még hivatkozik rá.
_ALBUMS_DDL = """
CREATE TABLE IF NOT EXISTS albums (
    folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    name TEXT,
    date TEXT,
    description TEXT,
    location TEXT,
    PRIMARY KEY (folder_id, token)
);

CREATE TABLE IF NOT EXISTS photo_albums (
    photo_id INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    token TEXT NOT NULL,
    PRIMARY KEY (photo_id, token)
);

CREATE INDEX IF NOT EXISTS idx_photo_albums_token ON photo_albums(token);
"""

# #26 (1. lépcső): saját (YuNet) arc-detektálás találatai — SZÁNDÉKOSAN
# külön tábla, a `photo_hashes` mintáját követve: tisztán származtatott
# adat (a képből újraszámolható), fotónkénti UPSERT-tel (a scan-worker
# egyszerűen törli-és-újraírja egy fotó sorait, ld. `index/faces_detected.py`).
#
# A `.picasa.ini` `faces=`/`deferredface` mezőit ez a tábla NEM érinti és
# NEM írja felül — azok a saját, motorspecifikus round-trip rétegen
# (`ini/faces.py`) élnek tovább változatlanul (a Picasa döntései szentek,
# ld. issue #26 terve). A `state` oszlop a tervezett későbbi lépcsőké
# (javaslat/elnevezés/ignorálás) — 1. lépcsőben mindig 'unnamed'.
#
# NINCS `embedding` oszlop (SFace-lenyomat) — az a terv 2. lépcsője
# (csoportosítás), ez az 1. lépcső csak detektál, nem azonosít.
#
# A rect és a landmark-koordináták KÉPPIXELBEN tárolódnak (nem [0..1]
# relatív, szemben a rect64-gyel) — a szemvonalra igazított arc-indexkép
# (`picasapy.faces.align`) ezekkel dolgozik közvetlenül, konverzió nélkül;
# a fotó `width`/`height`-je (a `photos` táblában már megvan) elég a
# relatívvá alakításhoz, ha egy jövőbeli lépcsőnek arra lesz szüksége.
_FACE_DDL = """
CREATE TABLE IF NOT EXISTS face (
    id INTEGER PRIMARY KEY,
    photo_id INTEGER NOT NULL REFERENCES photos(id) ON DELETE CASCADE,
    rect_left REAL NOT NULL,
    rect_top REAL NOT NULL,
    rect_right REAL NOT NULL,
    rect_bottom REAL NOT NULL,
    det_conf REAL NOT NULL,
    right_eye_x REAL NOT NULL,
    right_eye_y REAL NOT NULL,
    left_eye_x REAL NOT NULL,
    left_eye_y REAL NOT NULL,
    nose_x REAL NOT NULL,
    nose_y REAL NOT NULL,
    mouth_right_x REAL NOT NULL,
    mouth_right_y REAL NOT NULL,
    mouth_left_x REAL NOT NULL,
    mouth_left_y REAL NOT NULL,
    state TEXT NOT NULL DEFAULT 'unnamed'
);

CREATE INDEX IF NOT EXISTS idx_face_photo ON face(photo_id);
CREATE INDEX IF NOT EXISTS idx_face_state ON face(state);
"""

# #26 (2. lépcső): SFace-lenyomat + inkrementális csoportosítás
# (`picasapy.faces.clustering`, `picasapy.index.face_groups`).
#
# `face_group`: egy „Névtelenek”-csoport centroidja — SZÁNDÉKOSAN külön
# tábla (nem a `face` bővítése), mert egy csoportnak TÖBB arca van, a
# centroid pedig a csoport tulajdonsága, nem egyetlen arcé. `face_count`
# a súlyozott centroid-frissítéshez kell (`clustering._weighted_centroid`)
# — anélkül minden új tag egyformán mozgatná el a centroidot, függetlenül
# attól, hogy a csoportnak már 2 vagy 200 tagja van.
#
# `face.embedding`: 128 float32 (SFace, `EMBEDDING_DIM`) kis-endian bájtsor
# (`numpy.tobytes()`/`numpy.frombuffer(..., dtype=float32)`), NULL amíg a
# lenyomat-számítás (alacsonyabb prioritású, a detektálás UTÁN futó sor,
# ld. `faces/embedder.py` modul-docstringje) még nem érte el az arcot.
#
# `face.group_id`: melyik `face_group`-hoz tartozik — NULL, amíg nincs
# lenyomat VAGY amíg a csoportosítás még nem futott le rá. A `group_unnamed_
# faces` (`index/face_groups.py`) KIZÁRÓLAG a `state = 'unnamed'` sorokon
# dolgozik — a már névvel ellátott arcok hozzárendelését SOHA nem
# értékeli újra (issue #26 alapszabálya, „a Picasa döntései szentek”).
#
# Mindkettő ALTER TABLE-lel jön (nem a `_FACE_DDL` CREATE TABLE-jének
# bővítésével!), hogy a régi migrációs lépés (8: `_FACE_DDL`) VÁLTOZATLAN
# maradjon — az már production-ben lefutott v8→v9 migrációkat ír le, a
# szövegét utólag módosítani a már migrált (v9) indexeket és az újonnan
# migrálókat összezavarná (kettős oszlop-hozzáadás). Ehelyett ez a blokk a
# saját migrációs lépéseként (9) ÉS a friss telepítés `DDL`-jébe ágyazva is
# szerepel — mindkét esetben a `face` tábla már létezik (CREATE TABLE IF
# NOT EXISTS a `_FACE_DDL`-ben), az ALTER csak a hiányzó oszlopokat pótolja.
_FACE_EMBEDDING_DDL = """
CREATE TABLE IF NOT EXISTS face_group (
    id INTEGER PRIMARY KEY,
    centroid BLOB NOT NULL,
    face_count INTEGER NOT NULL DEFAULT 0
);

ALTER TABLE face ADD COLUMN embedding BLOB;
ALTER TABLE face ADD COLUMN group_id INTEGER REFERENCES face_group(id);

CREATE INDEX IF NOT EXISTS idx_face_group ON face(group_id);
"""

# #26 (4. lépcső): a név-javaslathoz KÉT oszlop hiányzott. A `person_name`
# köti a lenyomatot a névhez (`state = 'named'` soroknál) — enélkül a
# javaslat-ágnak nincs miből centroidot számolnia, ez volt a
# `face_groups.group_unnamed_faces` dokumentált hiánya („NINCS forrás,
# amiből ez automatikusan összeállna"). A `suggested_name` a MÉG EL NEM
# DÖNTÖTT javaslatot hordozza; az arc állapota ilyenkor `'unnamed'` marad,
# mert a javaslat nem döntés — a felhasználó erősíti meg vagy veti el
# (`PeopleAlbum::ConfirmText`: „Press checkmark to confirm match, press
# »x« to ignore.").
#
# A `_FACE_EMBEDDING_DDL` mintáját követi: ALTER TABLE-lel jön, hogy a
# korábbi migrációs lépések SZÖVEGE VÁLTOZATLAN maradjon, és ugyanez a
# blokk szerepel a friss telepítés `DDL`-jében is.
_FACE_NAME_DDL = """
ALTER TABLE face ADD COLUMN person_name TEXT;
ALTER TABLE face ADD COLUMN suggested_name TEXT;

CREATE INDEX IF NOT EXISTS idx_face_person ON face(person_name);
"""

# A `folders.offline` (#459/5): a mappa jelenleg nem elérhető (levált
# NAS-mount, kihúzott lemez). Ilyenkor a mappa és a fotói BENNMARADNAK az
# indexben — a takarítás kihagyja őket —, csak jelölést kapnak; a következő
# sikeres scan magától nullázza. A magyarázat SZÁNDÉKOSAN itt, Python-
# kommentben áll: az SQLite az `ALTER TABLE … DROP COLUMN`-nál újraparse-olja
# a tárolt DDL-szöveget, és a benne maradó `--` sorkommenttől elhasal.
DDL = f"""
CREATE TABLE IF NOT EXISTS folders (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    has_ini INTEGER NOT NULL DEFAULT 0,
    date TEXT,
    offline INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS photos (
    id INTEGER PRIMARY KEY,
    folder_id INTEGER NOT NULL REFERENCES folders(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    star INTEGER NOT NULL DEFAULT 0,
    hidden INTEGER NOT NULL DEFAULT 0,
    caption_ini TEXT,
    keywords_ini TEXT,
    rotate_steps INTEGER NOT NULL DEFAULT 0,
    filters TEXT,
    taken_at TEXT,
    orientation INTEGER NOT NULL DEFAULT 1,
    width INTEGER,
    height INTEGER,
    caption_file TEXT,
    keywords_file TEXT,
    geotag_ini TEXT,
    exif_lat REAL,
    exif_lon REAL,
    UNIQUE (folder_id, name)
);

CREATE INDEX IF NOT EXISTS idx_photos_starred ON photos(folder_id) WHERE star = 1;

{_PHOTO_HASHES_DDL}

{_ALBUMS_DDL}

{_FACE_DDL}

{_FACE_EMBEDDING_DDL}
{_FACE_NAME_DDL}

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
    3: """
ALTER TABLE photos ADD COLUMN filters TEXT;
""",
    4: """
ALTER TABLE photos ADD COLUMN hidden INTEGER NOT NULL DEFAULT 0;
""",
    # #294: a dHash-gyorsítótár tábla. Üresen jön létre — a meglévő
    # indexekhez nem kell újraszámolni semmit, az első duplikátum-keresés
    # tölti fel magától.
    5: _PHOTO_HASHES_DDL,
    # #30: geocímke — az ini nyers `geotag=` értéke és a fájl EXIF GPS-e
    # külön oszlopban (a feloldás sorrendje: ini, majd EXIF). Üresen jön
    # létre; a következő szinkron tölti fel, újraindexelés nélkül is.
    6: """
ALTER TABLE photos ADD COLUMN geotag_ini TEXT;
ALTER TABLE photos ADD COLUMN exif_lat REAL;
ALTER TABLE photos ADD COLUMN exif_lon REAL;
""",
    # #9: virtuális albumok. Üres táblákkal jön létre — a meglévő indexekhez
    # nem kell újraindexelés, a következő szinkron tölti fel őket az
    # ini-kből (a `[.album:token]` szekciók és az `albums=` kulcs alapján).
    7: _ALBUMS_DDL,
    # #26 (1. lépcső): a saját arc-detektálás táblája. Üresen jön létre —
    # a meglévő indexekhez nem kell újraindexelés; a következő arc-scan
    # (`FaceScanController`, opcionális háttérfolyamat) tölti fel.
    8: _FACE_DDL,
    # #26 (2. lépcső): SFace-lenyomat oszlop + a `face_group` tábla. Üresen
    # jön létre / NULL-lal jön a meglévő sorokra — a következő lenyomat-
    # számítás (alacsonyabb prioritású sor, ld. `faces/embedder.py`) tölti
    # fel; a meglévő `face` sorok (keret, 5 pont, állapot) érintetlenek.
    9: _FACE_EMBEDDING_DDL,
    # #459/5: offline (jelenleg nem elérhető) mappa jelölése. Minden
    # meglévő mappa 0-val (elérhető) indul — a következő szinkron állítja
    # be, ha kell; újraindexelés nem szükséges.
    10: """
ALTER TABLE folders ADD COLUMN offline INTEGER NOT NULL DEFAULT 0;
""",
    # #26 (4. lépcső): a név-javaslat két hiányzó oszlopa (ld.
    # `_FACE_NAME_DDL`). NULL-lal jön a meglévő sorokra: a következő
    # névadás/csoportosítás tölti fel, újraindexelés nem kell.
    11: _FACE_NAME_DDL,
}
