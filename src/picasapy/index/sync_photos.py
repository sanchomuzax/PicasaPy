"""Az index-szinkron felelősségi része; a régi API a sync.py-n át él."""

from __future__ import annotations

import logging
import sqlite3
from typing import NamedTuple

from picasapy.index.queries import HIDDEN_INI_PENDING
from picasapy.index.origin import forget_origin_keys_outside
from picasapy.ini import (
    IniDocument,
    ini_source_path,
    is_hidden_folders_category,
    read_folder_category,
    read_folder_date_override,
    set_folder_hidden_in_ini,
)
from picasapy.ini.names import INI_NAME
from picasapy.ini.album_order import places_of_section
from picasapy.ini.albums import albums_of, parse_album_refs
from picasapy.metadata import (
    EMPTY_METADATA,
    EMPTY_VIDEO_METADATA,
)
from picasapy.render.flip import FLIP_MASK
from picasapy.scanner import (
    FolderScan,
    MediaFile,
)

from .sync_compat import legacy

logger = logging.getLogger("picasapy.index.sync")


class _FolderSyncResult(NamedTuple):
    """Egy mappa szinkronjának eredménye: az új fotók száma (#209) és hogy
    a mappa újrapróbálandó-e (#4597: olvashatatlan ini — a scan-állapot nem
    menthető, különben az inkrementális sync többé nem nézné meg)."""

    new_count: int
    retry: bool


def _sync_folder(conn: sqlite3.Connection, scan: FolderScan) -> _FolderSyncResult:
    """Egy mappa szinkronja; az eredményben az ÚJ (az indexben eddig
    nem szereplő) fotók száma (#209, a haladás-jelzéshez)."""
    # #459/5: a sikeres scan bizonyítja, hogy a mappa elérhető — az esetleges
    # offline jelölés magától elmúlik (a NAS visszatérése után nincs teendő).
    folder_id = conn.execute(
        "INSERT INTO folders(path, has_ini, offline) VALUES (?, ?, 0) "
        "ON CONFLICT(path) DO UPDATE SET has_ini = excluded.has_ini,"
        " offline = 0 "
        "RETURNING id",
        (str(scan.path), int(scan.has_ini)),
    ).fetchone()[0]
    # Az ini-mezőket is beolvassuk (#139): változatlan fájl + változatlan
    # ini-mezők esetén az UPDATE teljesen kimarad — az SQLite azonos
    # értékeknél is átírná a sort és elsütné az FTS-triggert (delete+insert
    # minden fotóra minden syncnél → WAL-hízás, flash-kopás).
    existing = {
        row["name"]: (
            (row["mtime_ns"], row["size"]),
            (
                row["star"],
                row["hidden"],
                row["caption_ini"],
                row["keywords_ini"],
                row["rotate_steps"],
                row["flip_flags"],
                row["filters"],
                row["geotag_ini"],
            ),
            row["movie_format"],
        )
        for row in conn.execute(
            "SELECT name, mtime_ns, size, star, hidden, caption_ini,"
            " keywords_ini, rotate_steps, flip_flags, filters, geotag_ini,"
            " movie_format"
            " FROM photos WHERE folder_id = ?",
            (folder_id,),
        )
    }
    document = _load_ini(scan)
    _sync_folder_hidden(conn, folder_id, scan, document)
    new_count = 0
    for media in scan.files:
        section = document.section(media.name) if document else None
        ini_fields = (
            int(section.get("star") == "yes") if section else 0,
            int(section.get("hidden") == "yes") if section else 0,
            section.get("caption") if section else None,
            section.get("keywords") if section else None,
            _rotate_steps(section.get("rotate")) if section else 0,
            # #2976: a tükrözés is ini-eredetű (a bit-jelentés a #2938 mérése)
            flip_jelzo(section.get("flipped")) if section else 0,
            section.get("filters") if section else None,
            # #30: a geocímke nyers ini-értéke — a feloldást (ini > EXIF)
            # a lekérdezés-réteg végzi, itt bitre pontosan az tárolódik,
            # ami az ini-ben áll
            section.get("geotag") if section else None,
        )
        current = existing.get(media.name)
        if current is not None and current[0] == (media.mtime_ns, media.size):
            # Változatlan fájl: a (drága) EXIF/IPTC-olvasás kimarad, a
            # fájl-metaadat oszlopok maradnak. UPDATE csak akkor fut, ha
            # az ini-mezők ténylegesen eltérnek (#139) — különben a sor
            # érintetlen, az FTS-trigger sem sül el.
            if media.kind == "video" and current[2] is None:
                # #4580: a v20-ról migrált sorokból a fájl újraolvasása tölti
                # fel a videómezőket.
                _upsert_photo(conn, folder_id, scan, media, ini_fields)
            elif current[1] != ini_fields:
                conn.execute(
                    "UPDATE photos SET star = ?, hidden = ?, caption_ini = ?,"
                    " keywords_ini = ?, rotate_steps = ?, flip_flags = ?,"
                    " filters = ?, geotag_ini = ?"
                    " WHERE folder_id = ? AND name = ?",
                    (*ini_fields, folder_id, media.name),
                )
        else:
            if current is None:
                new_count += 1  # #209: eddig nem indexelt fotó
            _upsert_photo(conn, folder_id, scan, media, ini_fields)
    nevek = [media.name for media in scan.files]
    _prune_photos(conn, folder_id, nevek)
    # #2038: a származás-öröklés (`origin_keys`) útvonalra van kulcsolva, és a
    # takarítása eddig kimaradt. Ez a MINDEN utat lefedő pont: a fájl eltűnhet
    # kukába dobással, átnevezéssel vagy a felhasználó fájlkezelőjéből — a
    # mappa-szinkron mindegyiket itt látja meg.
    forget_origin_keys_outside(conn, scan.path, nevek)
    _sync_albums(conn, folder_id, document)
    sync_folder_date(conn, folder_id, document)
    # #1644: „olvasatlan" jelölő — a mappába ÚJ kép került. A `new_count` a
    # #209 óta pontosan ezt számolja (az indexben eddig nem szereplő
    # fotókat), tehát nincs szükség külön észlelésre.
    #
    # ⚠️ Csak BEÁLLÍT, sosem töröl: az első indexeléskor MINDEN mappa új
    # képeket kap, de a visszaállítás a felhasználó dolga (megnyitja a
    # mappát) — a sync nem tudhatja, mit nézett már meg.
    if new_count:
        conn.execute("UPDATE folders SET unread = 1 WHERE id = ?", (folder_id,))
    if not scan.files and not scan.has_ini:
        # A beállítás által kiszűrt, `.picasa.ini` nélküli mappa ne maradjon
        # üres sorként a könyvtárban.
        legacy("_remove_folder")(conn, scan.path)
    return _FolderSyncResult(new_count, scan.has_ini and document is None)


def sync_folder_date(
    conn: sqlite3.Connection, folder_id: int, document: IniDocument | None
) -> None:
    """Mappa-dátum (#320): a `.picasa.ini` `[Picasa]` `date=` kézi
    felülírása elsőbbséget élvez; ennek hiányában az alapértelmezett Picasa-
    viselkedés — automatikusan a legrégebbi felvétel ideje.

    #2304: a felvételi idő hiányában a FÁJL ideje a tartalék. Enélkül egy
    csupa EXIF-nélküli mappa (letöltött vagy generált képek) dátum nélkül
    maradt: a fejlécében nem állt dátum, a bal hasábban pedig — mivel a
    `models._with_year_separators` dátumtalan mappához nem tesz
    évszám-fejlécet — az ELŐZŐ év alá csúszott. A tartalék nem új
    találmány: a rács rendezőkulcsa (`app/photo_sort.photo_date`) már
    eddig is pontosan erre esett vissza, és a `mtime_ns` a `photos`
    táblában is megvan.

    A `taken_at` ISO-alakú helyi idő, ezért a fájlidőt is helyi időre
    alakítjuk (`'localtime'`) — különben a két ág nem lenne
    összehasonlítható, és a `MIN` a nyári időszámítás körül rossz sorrendet
    adna.

    #2486: a tartalék a BEFAGYASZTOTT fájlidő (`first_seen_mtime_ns`),
    nem az élő `mtime`. A mappa dátuma így nem ugrik el attól, hogy egy
    mentés vagy a saját `photo_touch`-unk átírta a képek idejét; a
    `COALESCE` a második tagja csak a v17 előtti, még fel nem töltött
    sorokra kell (ott a viselkedés a #2486 előtti marad)."""
    override = read_folder_date_override(document) if document else None
    if override is not None:
        conn.execute("UPDATE folders SET date = ? WHERE id = ?", (override, folder_id))
        return
    conn.execute(
        "UPDATE folders SET date = ("
        " SELECT MIN(COALESCE("
        "  COALESCE(p.taken_at_override, p.taken_at),"
        "  strftime('%Y-%m-%dT%H:%M:%S',"
        "           COALESCE(p.first_seen_mtime_ns, p.mtime_ns) / 1000000000,"
        "           'unixepoch', 'localtime')"
        " )) FROM photos p WHERE p.folder_id = ?"
        ") WHERE id = ?",
        (folder_id, folder_id),
    )


def _upsert_photo(
    conn: sqlite3.Connection,
    folder_id: int,
    scan: FolderScan,
    media: MediaFile,
    ini_fields: tuple,
) -> None:
    meta = (
        legacy("read_file_metadata")(scan.path / media.name)
        if media.kind == "photo"
        else EMPTY_METADATA
    )
    video_meta = (
        legacy("read_video_metadata")(scan.path / media.name)
        if media.kind == "video"
        else EMPTY_VIDEO_METADATA
    )
    conn.execute(
        "INSERT INTO photos"
        "(folder_id, name, kind, size, mtime_ns, star, hidden, caption_ini,"
        " keywords_ini, rotate_steps, flip_flags, filters, geotag_ini,"
        " taken_at, orientation, width, height, caption_file, keywords_file,"
        " movie_format, frame_rate, duration_seconds,"
        " exif_lat, exif_lon, first_seen_mtime_ns)"
        " VALUES (" + ", ".join("?" for _ in range(25)) + ") "
        "ON CONFLICT(folder_id, name) DO UPDATE SET "
        # #2486: a BEFAGYASZTÁS egyetlen sora. A `mtime_ns` az élő érték —
        # a változás-detektálásé, a bélyegkép-gyorstáré, a „legutóbbi
        # változtatás" rendezésé —, a `first_seen_mtime_ns` viszont az
        # ELSŐ látáskori, és az ütközési ágon SOHA nem íródik felül. A
        # `COALESCE` csak a még üres (v17 elé indexelt, majd újra
        # feltűnő) sort tölti fel.
        "first_seen_mtime_ns = COALESCE(photos.first_seen_mtime_ns,"
        " excluded.first_seen_mtime_ns), "
        "kind = excluded.kind, size = excluded.size, "
        "mtime_ns = excluded.mtime_ns, star = excluded.star, "
        "hidden = excluded.hidden, "
        "caption_ini = excluded.caption_ini, "
        "keywords_ini = excluded.keywords_ini, "
        "rotate_steps = excluded.rotate_steps, "
        "flip_flags = excluded.flip_flags, "
        "filters = excluded.filters, "
        "geotag_ini = excluded.geotag_ini, "
        "taken_at = excluded.taken_at, orientation = excluded.orientation, "
        # #4332: a kézi dátum a fájl változása után is megmarad — a program
        # saját Mentése is átírja a fájlt, és az eredeti Picasa a dátumot a
        # saját adatbázisában tartja.
        "taken_at_override = photos.taken_at_override, "
        "width = excluded.width, height = excluded.height, "
        "caption_file = excluded.caption_file, "
        "keywords_file = excluded.keywords_file, "
        "movie_format = excluded.movie_format, "
        "frame_rate = excluded.frame_rate, "
        "duration_seconds = excluded.duration_seconds, "
        "exif_lat = excluded.exif_lat, exif_lon = excluded.exif_lon",
        (
            folder_id,
            media.name,
            media.kind,
            media.size,
            media.mtime_ns,
            *ini_fields,
            meta.taken_at,
            meta.orientation,
            meta.width,
            meta.height,
            meta.caption,
            ",".join(meta.keywords) or None,
            video_meta.movie_format,
            video_meta.frame_rate,
            video_meta.duration_seconds,
            meta.latitude,
            meta.longitude,
            media.mtime_ns,
        ),
    )


def _sync_folder_hidden(
    conn: sqlite3.Connection,
    folder_id: int,
    scan: FolderScan,
    document: IniDocument | None,
) -> None:
    """#4597: a `folders.hidden` az ini `P2category=Hidden Folders` sorából
    származik — az újraépített index is rejtve hagyja a mappát.

    EGYSZERI ÁTÁLLÍTÁS: a `hidden = 2` („rejtett, az ini-be még nincs
    beírva": régi index vagy offline mappa) mappára előbb az ini-be íródik a
    `Hidden Folders`, és csak ezután számít az ini az igazságforrásnak. Ha az
    ini nem írható vagy nem olvasható, a jelölés 2 marad (a mappa rejtett
    marad, a következő szinkron újrapróbálja). Ini nélküli mappánál az 1-es
    jelölés érintetlen."""
    current = conn.execute("SELECT hidden FROM folders WHERE id = ?", (folder_id,)).fetchone()[0]
    if current == HIDDEN_INI_PENDING:
        if scan.has_ini and document is None:
            return  # olvashatatlan ini: nem írunk rá, rejtett marad
        try:
            if not is_hidden_folders_category(read_folder_category(document) if document else None):
                set_folder_hidden_in_ini(scan.path, True)
        except (OSError, ValueError, RuntimeError):
            return
        conn.execute("UPDATE folders SET hidden = 1 WHERE id = ?", (folder_id,))
        return
    if document is None:
        return
    hidden = int(is_hidden_folders_category(read_folder_category(document)))
    if bool(current) != bool(hidden):
        conn.execute("UPDATE folders SET hidden = ? WHERE id = ?", (hidden, folder_id))


def _load_ini(scan: FolderScan) -> IniDocument | None:
    if not scan.has_ini:
        return None
    try:
        ini_path = ini_source_path(scan.path / INI_NAME)
        if ini_path is None:
            return None
        return legacy("load_document")(ini_path)
    except (OSError, ValueError):
        # Zárolt/olvashatatlan/sérült ini (pl. a futó Picasa fogja): a mappa
        # metaadat nélkül indexelődik, a következő sync majd pótolja.
        return None


def _rotate_steps(value: str | None) -> int:
    if value is None:
        return 0
    match = legacy("_ROTATE").match(value)
    return int(match.group(1)) % 4 if match else 0


def flip_jelzo(value: str | None) -> int:
    """A `flipped(N)` maszkja; `0`, ha nincs, üres, vagy értelmezhetetlen.

    A fölös bitek leesnek (`FLIP_MASK`): a mért írónak két bitje van, és egy
    harmadikra nincs jelentésünk — kitalálni tilos."""
    if not value:
        return 0
    match = legacy("_FLIPPED").match(value)
    return int(match.group(1)) & FLIP_MASK if match else 0


_PRUNE_TEMP_TABLE = "_prune_photos_names"


def _sync_albums(conn, folder_id: int, document) -> None:
    """A mappa virtuális albumainak és a tagságoknak a szinkronizálása (#9).

    Két külön dolog jön az ini-ből:
    - a `[.album:<token>]` szekciók az album DEFINÍCIÓJÁT adják (név, dátum);
      ugyanaz az album több mappában is definiálva lehet, ezért `upsert` a
      tokenre — az utoljára látott, nem üres név nyer,
    - a képek `albums=` kulcsa a TAGSÁGOT adja; ezt mappánként újraépítjük,
      hogy az ini-ből kivett kép az indexből is kiessen.

    Az ini nélküli mappa csak a saját tagságait törli — a máshol definiált
    albumokat nem bántja.
    """
    photo_ids = {
        row["name"]: row["id"]
        for row in conn.execute("SELECT id, name FROM photos WHERE folder_id = ?", (folder_id,))
    }
    conn.execute(
        "DELETE FROM photo_albums WHERE photo_id IN (SELECT id FROM photos WHERE folder_id = ?)",
        (folder_id,),
    )
    # a mappa SAJÁT definícióit írjuk újra — így az ini-ből törölt album
    # akkor is kiesik, ha egy másik mappa még hivatkozik rá
    conn.execute("DELETE FROM albums WHERE folder_id = ?", (folder_id,))
    if document is None:
        _prune_albums(conn)
        return

    for album in albums_of(document):
        conn.execute(
            "INSERT INTO albums"
            " (folder_id, token, name, date, description, location)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (
                folder_id,
                album.token,
                album.name,
                album.date,
                album.description,
                album.location,
            ),
        )

    # #4599 (ADR-016): az album kézi helye (`albumorder=`) — az index csak
    # gyorsítótárazza, az igazságforrás az ini.
    for name, photo_id in photo_ids.items():
        section = document.section(name)
        if section is None:
            continue
        refs = section.get("albums")
        if not refs:
            continue
        photo_places = places_of_section(section)
        for token in parse_album_refs(refs):
            conn.execute(
                "INSERT OR IGNORE INTO photo_albums (photo_id, token, place) VALUES (?, ?, ?)",
                (photo_id, token, photo_places.get(token)),
            )
    _prune_albums(conn)


def _prune_albums(conn) -> None:
    """A már sehol nem DEFINIÁLT albumok tagságainak kivezetése.

    Az albumot a definíciója tartja életben: ha egyetlen mappa ini-jében sem
    szerepel többé a `[.album:<token>]` szekció, akkor a rá mutató tagságok
    is értelmüket vesztik. A definíciós sorokat maga a mappa-szinkron írja
    újra, itt csak az árván maradt hivatkozásokat takarítjuk.
    """
    conn.execute("DELETE FROM photo_albums WHERE token NOT IN (SELECT token FROM albums)")


def _prune_photos(conn: sqlite3.Connection, folder_id: int, names: list[str]) -> None:
    """A mappából eltűnt fotók (indexbeli sorai) törlése.

    #304: `names` egy nagy (32 766-nál — az SQLite `SQLITE_MAX_VARIABLE_
    NUMBER` alapértéke — több elemű) mappánál nem paraméterezhető közvetlenül
    egy `NOT IN (?, ?, ...)` listaként — az `sqlite3.OperationalError`-ral
    bukna. Ehelyett egy ideiglenes (kapcsolat-lokális) táblába kerülnek a
    látott nevek, és a törlés egy al-SELECT-tel szűr. A temp tábla neve nem
    ütközhet más kapcsolattal (az SQLite temp táblái kapcsolat-lokálisak),
    de a `_sync_folder` ugyanazon a kapcsolaton mappánként újra hívja ezt a
    függvényt — ezért a hívás elején `DROP TABLE IF EXISTS`-szel takarítunk,
    a végén pedig explicit `DROP TABLE`-lel."""
    if not names:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        return
    conn.execute(f"DROP TABLE IF EXISTS temp.{_PRUNE_TEMP_TABLE}")
    conn.execute(f"CREATE TEMP TABLE {_PRUNE_TEMP_TABLE} (name TEXT PRIMARY KEY)")
    conn.executemany(
        f"INSERT INTO {_PRUNE_TEMP_TABLE}(name) VALUES (?)",
        [(name,) for name in names],
    )
    conn.execute(
        "DELETE FROM photos WHERE folder_id = ? AND name NOT IN"
        f" (SELECT name FROM {_PRUNE_TEMP_TABLE})",
        (folder_id,),
    )
    conn.execute(f"DROP TABLE {_PRUNE_TEMP_TABLE}")
