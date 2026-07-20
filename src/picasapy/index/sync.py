"""Ismételhető szinkron: fájlrendszer-scan + .picasa.ini → SQLite index.

A 7. rögzített döntés (ismételhető migráció) miatt a szinkron idempotens:
upsert a meglévő sorokra (stabil id-k), a fájlrendszerről eltűnt fájlok és
mappák törlése. Az ini az igazságforrás — minden futás a friss tartalmát
veszi át.
"""

from __future__ import annotations

import logging
import os
import re
import sqlite3
import time
from collections.abc import Callable
from pathlib import Path

from picasapy.ini import IniDocument, load_document
from picasapy.metadata import EMPTY_METADATA, read_file_metadata
from picasapy.scanner import (
    PICASA_INI_NAME,
    FolderScan,
    MediaFile,
    scan_folder,
    scan_tree,
)

_ROTATE = re.compile(r"^rotate\((\d+)\)$")

# #143: az inkrementális kihagyás frissesség-védőablaka. A mappa- és
# ini-mtime felbontása durva lehet (SMB/FAT: 2 s; ext4 is csak jiffy-pontos),
# ezért az ennél frissebb mappát sosem hagyjuk ki — különben egy, a mentett
# mtime-mal azonos időbélyegű változás észrevétlen maradna.
_SKIP_SAFETY_NS = 2_000_000_000

# #143: a scan-állapot segédtáblája. Szándékosan nem a schema.py-ban él
# (sémaverziót csak az integrátor oszt ki): tisztán eldobható cache —
# hiánya vagy törlése csak egy teljes újra-stat-olást jelent, adatvesztést nem.
_SCAN_STATE_DDL = (
    "CREATE TABLE IF NOT EXISTS folder_scan_state ("
    " path TEXT PRIMARY KEY,"
    " mtime_ns INTEGER NOT NULL,"
    " ini_mtime_ns INTEGER)"
)

logger = logging.getLogger(__name__)

# #209: streamelt sync — mappánkénti haladás-jelzés. Paraméterek:
# (mappa útvonala, kész mappák száma, összes ismert mappa, az eddig talált
# ÚJ fotók kumulált száma). FIGYELEM: a callback a sync_tree hívási szálán
# fut — az app-ban ez a háttér-worker szála, NEM a GUI-szál; a hívó dolga
# a szál-átadás (pl. Qt queued signal) és a ritkítás.
#
# #216: a callback VISSZATÉRÉSI ÉRTÉKE megszakítás-kérés — igaz érték esetén
# a sync a mappa-határon tisztán leáll (a már commitolt mappák megmaradnak,
# a takarítás kimarad). A None/False (a korábbi, érték nélküli callbackek)
# nem szakít meg — visszafelé kompatibilis.
SyncProgressCallback = Callable[[str, int, int, int], object]


def sync_tree(
    conn: sqlite3.Connection,
    root: str | Path,
    exclude: tuple[str | Path, ...] = (),
    incremental: bool = True,
    progress: SyncProgressCallback | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> None:
    """A gyökér alatti könyvtár teljes szinkronja az indexbe.

    Az index kanonikus (feloldott, abszolút) útvonalakra kulcsol, ezért a
    gyökeret belépéskor normalizáljuk. Mappánként commitolunk: nagy (100k+)
    könyvtárnál nem nő össze a WAL, és megszakadás után a futás onnan
    folytatható, ahol tartott (a szinkron mappánként idempotens).

    Az `exclude`-ban felsorolt mappák (és alfáik) kimaradnak az indexből
    (#145, FRExcludeFolders.txt — ld. `picasapy.scanner.exclude` a fázis-1
    szintű, ideiglenes egyszerűsítés indoklásáért).

    Ismert korlátok:
    - RAW és videó fájloknál nincs EXIF/IPTC-olvasás (a Pillow nem dekódolja
      őket) → taken_at/orientation/méret üres marad; RAW-támogatás később.
    - A változás-detektálás (mtime_ns, size) páros: egy mtime-őrző, azonos
      méretű IPTC-átírást (pl. exiftool -P) nem vesz észre. A Picasa maga
      mindig frissíti az mtime-ot, így ez a gyakorlatban nem fordul elő.
    - A keywords_file vesszővel join-olt lista: vesszőt tartalmazó kulcsszó
      nem bontható vissza veszteség nélkül (FTS-t és megjelenítést nem zavar).

    #143 — inkrementális rescan (`incremental=True`, alapértelmezés): egy
    mappa fájljainak stat-olása kimarad, ha a mappa mtime-ja ÉS az ini
    mtime-ja megegyezik az indexben tárolt állapottal, és mindkettő idősebb
    a frissesség-védőablaknál. Dokumentált kompromisszum (a NAS-rescan
    nagyságrendi gyorsítása fejében): a mappa mtime-ját nem érintő, helyben
    történt fájl-átírást a rescan nem vesz észre — azt a watcher-ág, illetve
    egy `incremental=False` teljes sync fedi le.

    #209 — streamelt haladás: ha a `progress` callback meg van adva, MINDEN
    mappa feldolgozása (vagy kihagyása) után meghívjuk
    `(mappa, kész, összes, új_fotók_kumulált)` argumentumokkal. A mappánkénti
    commit miatt a már jelzett mappák fotói ekkor MÁR olvashatók az indexből
    (másik kapcsolaton is) — erre épül a fokozatos UI-megjelenítés. A callback
    szál-kontextusa a hívóé (worker-szál!), ld. `SyncProgressCallback`.

    #216 — tiszta megszakítás mappa-határon: a futás leáll, ha a `should_stop`
    igazat ad (a soron következő mappa feldolgozása ELŐTT ellenőrizve), vagy
    ha a `progress` callback igaz értékkel tér vissza (a mappa commitja UTÁN).
    Megszakadt futásnál a takarítás (`_prune_folders`) kimarad — a hiányos
    „látott" halmaz érvényes mappákat törölne; a már commitolt mappák
    megmaradnak (konzisztens, folytatható állapot).
    """
    root_path = Path(root).resolve()
    _ensure_scan_state(conn)
    skip = _make_skip(conn) if incremental else None
    scans = scan_tree(root_path, exclude=exclude, skip=skip)
    done = 0
    new_total = 0
    cancelled = False
    for scan in scans:
        if should_stop is not None and should_stop():
            cancelled = True
            break
        done += 1
        if scan.skipped:
            # változatlan mappa: az indexbeli állapot érvényes; a haladás-
            # számláló ettől még lép (a hívó ritkítja a jelzés-árat)
            if progress is not None and progress(
                str(scan.path), done, len(scans), new_total
            ):
                cancelled = True
                break
            continue
        new_total += _sync_folder(conn, scan)
        if incremental:
            _store_scan_state(conn, scan)
        conn.commit()
        if progress is not None and progress(
            str(scan.path), done, len(scans), new_total
        ):
            cancelled = True
            break
    if cancelled:
        # megszakítva: a folyamatban lévő mappa commitja már lefutott, a
        # takarítás viszont TILOS — a hívó (pl. remove_root) takarít, ha kell
        conn.commit()
        return
    seen_paths = {str(scan.path) for scan in scans}
    if seen_paths or not _has_indexed_folders(conn, root_path):
        # Nem üres scan, vagy a gyökér az indexben is üres volt eddig —
        # nincs mit óvni, a takarítás biztonságosan lefuthat.
        _prune_folders(conn, root_path, seen_paths)
    else:
        # #132: az üres scan-eredmény megkülönböztethetetlen attól, hogy a
        # gyökér ténylegesen elérhetetlen (pl. lecsatolt NAS-mount, amely
        # üres könyvtárként van jelen). Ha korábban NEM volt üres az
        # indexben tárolt részfa, a takarítást konzervatívan kihagyjuk —
        # inkább maradjon egy ideig elavult bejegyzés, mint hogy a NAS
        # visszatérése után órákig tartó teljes újraépítés legyen és a
        # stabil rekord-id-k elvesszenek. Tényleges törléshez explicit
        # eltávolítás szükséges (Mappakezelő → „Eltávolítás a Picasából").
        logger.warning(
            "A gyökér elérhetetlennek tűnik (üres scan-eredmény, de az "
            "indexben van hozzá tartozó tartalom): %s — a takarítás "
            "kimaradt.",
            root_path,
        )
    conn.commit()


def sync_folder(
    conn: sqlite3.Connection,
    root: str | Path,
    folder: str | Path,
    exclude: tuple[str | Path, ...] = (),
    should_stop: Callable[[], bool] | None = None,
) -> None:
    """Egyetlen mappa nem-rekurzív szinkronja (watcher-ág, #143).

    A watcher mappa-pontos jelzést ad — nincs ok a teljes részfa
    újrabejárására. A mappa almappáihoz nem nyúl; ha a mappa eltűnt,
    kizárt vagy médiamentes lett, a sora (és a fotói) kikerülnek az
    indexből. A `root` a védőkorlát: csak a figyelt gyökér alatti mappa
    szinkronizálható.

    #216: ha a `should_stop` igazat ad (a mappa a hívás pillanatában már
    eltávolított gyökérhez tartozik), a sync ír-módosít nélkül visszatér —
    az egyetlen mappa maga a „mappa-határ"."""
    if should_stop is not None and should_stop():
        return  # megszakítva még a scan előtt — az index érintetlen
    root_path = Path(root).resolve()
    folder_path = Path(folder).resolve()
    if not folder_path.is_relative_to(root_path):
        raise ValueError(
            f"A mappa nem a figyelt gyökér alatt van: {folder_path} ∉ {root_path}"
        )
    _ensure_scan_state(conn)
    exclude_paths = tuple(Path(item).resolve() for item in exclude)
    excluded = any(
        folder_path == item or item in folder_path.parents for item in exclude_paths
    )
    scan = None if excluded else scan_folder(folder_path)
    if scan is None:
        _remove_folder(conn, folder_path)
    else:
        _sync_folder(conn, scan)
        _store_scan_state(conn, scan)
    conn.commit()


def _remove_folder(conn: sqlite3.Connection, folder_path: Path) -> None:
    """Egy mappa sorának (és fotóinak, scan-állapotának) törlése. Explicit
    photos-törlés a folders előtt, hogy az FTS-triggerek lefussanak."""
    row = conn.execute(
        "SELECT id FROM folders WHERE path = ?", (str(folder_path),)
    ).fetchone()
    if row is not None:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (row["id"],))
        conn.execute("DELETE FROM folders WHERE id = ?", (row["id"],))
    conn.execute(
        "DELETE FROM folder_scan_state WHERE path = ?", (str(folder_path),)
    )


def _ensure_scan_state(conn: sqlite3.Connection) -> None:
    """A scan-állapot cache-tábla lusta létrehozása (ld. _SCAN_STATE_DDL)."""
    conn.execute(_SCAN_STATE_DDL)


def _make_skip(conn: sqlite3.Connection):
    """Kihagyás-predikátum az inkrementális rescanhez (#143).

    Csak olyan mappa hagyható ki, amely (1) az indexben is szerepel,
    (2) mappa- és ini-mtime-ja bitre egyezik a tárolt állapottal, és
    (3) mindkét mtime idősebb a frissesség-védőablaknál."""
    state = {
        row["path"]: (row["mtime_ns"], row["ini_mtime_ns"])
        for row in conn.execute(
            "SELECT s.path, s.mtime_ns, s.ini_mtime_ns"
            " FROM folder_scan_state s JOIN folders f ON f.path = s.path"
        )
    }
    fresh_limit = time.time_ns() - _SKIP_SAFETY_NS

    def skip(path: Path, mtime_ns: int, ini_mtime_ns: int | None) -> bool:
        return (
            state.get(str(path)) == (mtime_ns, ini_mtime_ns)
            and mtime_ns <= fresh_limit
            and (ini_mtime_ns is None or ini_mtime_ns <= fresh_limit)
        )

    return skip


def _store_scan_state(conn: sqlite3.Connection, scan: FolderScan) -> None:
    if not scan.mtime_ns:
        return  # a mappa statja nem sikerült — ne rögzítsünk hamis állapotot
    conn.execute(
        "INSERT INTO folder_scan_state(path, mtime_ns, ini_mtime_ns)"
        " VALUES (?, ?, ?)"
        " ON CONFLICT(path) DO UPDATE SET mtime_ns = excluded.mtime_ns,"
        " ini_mtime_ns = excluded.ini_mtime_ns",
        (str(scan.path), scan.mtime_ns, scan.ini_mtime_ns),
    )


def _sync_folder(conn: sqlite3.Connection, scan: FolderScan) -> int:
    """Egy mappa szinkronja; a visszatérési érték az ÚJ (az indexben eddig
    nem szereplő) fotók száma (#209, a haladás-jelzéshez)."""
    folder_id = conn.execute(
        "INSERT INTO folders(path, has_ini) VALUES (?, ?) "
        "ON CONFLICT(path) DO UPDATE SET has_ini = excluded.has_ini "
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
                row["filters"],
            ),
        )
        for row in conn.execute(
            "SELECT name, mtime_ns, size, star, hidden, caption_ini,"
            " keywords_ini, rotate_steps, filters"
            " FROM photos WHERE folder_id = ?",
            (folder_id,),
        )
    }
    document = _load_ini(scan)
    new_count = 0
    for media in scan.files:
        section = document.section(media.name) if document else None
        ini_fields = (
            int(section.get("star") == "yes") if section else 0,
            int(section.get("hidden") == "yes") if section else 0,
            section.get("caption") if section else None,
            section.get("keywords") if section else None,
            _rotate_steps(section.get("rotate")) if section else 0,
            section.get("filters") if section else None,
        )
        current = existing.get(media.name)
        if current is not None and current[0] == (media.mtime_ns, media.size):
            # Változatlan fájl: a (drága) EXIF/IPTC-olvasás kimarad, a
            # fájl-metaadat oszlopok maradnak. UPDATE csak akkor fut, ha
            # az ini-mezők ténylegesen eltérnek (#139) — különben a sor
            # érintetlen, az FTS-trigger sem sül el.
            if current[1] != ini_fields:
                conn.execute(
                    "UPDATE photos SET star = ?, hidden = ?, caption_ini = ?,"
                    " keywords_ini = ?, rotate_steps = ?, filters = ?"
                    " WHERE folder_id = ? AND name = ?",
                    (*ini_fields, folder_id, media.name),
                )
        else:
            if current is None:
                new_count += 1  # #209: eddig nem indexelt fotó
            _upsert_photo(conn, folder_id, scan, media, ini_fields)
    _prune_photos(conn, folder_id, [media.name for media in scan.files])
    # mappa-dátum (Picasa): automatikusan a legrégebbi felvétel ideje
    conn.execute(
        "UPDATE folders SET date = ("
        " SELECT MIN(p.taken_at) FROM photos p WHERE p.folder_id = ?"
        ") WHERE id = ?",
        (folder_id, folder_id),
    )
    return new_count


def _upsert_photo(
    conn: sqlite3.Connection,
    folder_id: int,
    scan: FolderScan,
    media: MediaFile,
    ini_fields: tuple,
) -> None:
    meta = (
        read_file_metadata(scan.path / media.name)
        if media.kind == "photo"
        else EMPTY_METADATA
    )
    conn.execute(
        "INSERT INTO photos"
        "(folder_id, name, kind, size, mtime_ns, star, hidden, caption_ini,"
        " keywords_ini, rotate_steps, filters, taken_at, orientation,"
        " width, height, caption_file, keywords_file)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(folder_id, name) DO UPDATE SET "
        "kind = excluded.kind, size = excluded.size, "
        "mtime_ns = excluded.mtime_ns, star = excluded.star, "
        "hidden = excluded.hidden, "
        "caption_ini = excluded.caption_ini, "
        "keywords_ini = excluded.keywords_ini, "
        "rotate_steps = excluded.rotate_steps, "
        "filters = excluded.filters, "
        "taken_at = excluded.taken_at, orientation = excluded.orientation, "
        "width = excluded.width, height = excluded.height, "
        "caption_file = excluded.caption_file, "
        "keywords_file = excluded.keywords_file",
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
        ),
    )


def _load_ini(scan: FolderScan) -> IniDocument | None:
    if not scan.has_ini:
        return None
    try:
        return load_document(scan.path / PICASA_INI_NAME)
    except (OSError, ValueError):
        # Zárolt/olvashatatlan/sérült ini (pl. a futó Picasa fogja): a mappa
        # metaadat nélkül indexelődik, a következő sync majd pótolja.
        return None


def _rotate_steps(value: str | None) -> int:
    if value is None:
        return 0
    match = _ROTATE.match(value)
    return int(match.group(1)) % 4 if match else 0


def _prune_photos(
    conn: sqlite3.Connection, folder_id: int, names: list[str]
) -> None:
    if not names:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        return
    placeholders = ",".join("?" * len(names))
    conn.execute(
        f"DELETE FROM photos WHERE folder_id = ? AND name NOT IN ({placeholders})",
        (folder_id, *names),
    )


def _prune_folders(
    conn: sqlite3.Connection, root: Path, seen_paths: set[str]
) -> None:
    """A gyökér alatti, de a mostani scanben nem látott mappák törlése.

    #143: a gyökér-szűrés SQL-oldalon fut (indexelhető LIKE-prefix), nem
    Pythonban az összes mappán iterálva. Explicit photos-törlés a folders
    előtt, hogy az FTS-triggerek biztosan lefussanak (az FK-cascade nem
    minden konfigurációban futtat triggert).
    """
    stale = [
        (row["id"], row["path"])
        for row in conn.execute(*_under_root_query("SELECT id, path", root))
        if row["path"] not in seen_paths
    ]
    for folder_id, path in stale:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        conn.execute("DELETE FROM folder_scan_state WHERE path = ?", (path,))


def _under_root_query(select: str, root: Path) -> tuple[str, tuple[str, str]]:
    """SQL + paraméterek a gyökér alatti folders-sorokhoz (#143).

    A LIKE-minta escape-elt (%, _ és \\ a path-ban nem viselkedhet
    joker-ként), és elválasztóval zárt prefixet használ — a „/a/kep" gyökér
    nem foghatja meg a „/a/kepek" mappáit."""
    prefix = str(root).rstrip(os.sep) + os.sep
    escaped = (
        prefix.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )
    return (
        f"{select} FROM folders WHERE path = ? OR path LIKE ? ESCAPE '\\'",
        (str(root), escaped + "%"),
    )


def _is_under(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)


def _has_indexed_folders(conn: sqlite3.Connection, root: Path) -> bool:
    """Van-e a gyökér alá eső mappa az indexben (a scan-eredménytől függetlenül)."""
    query, params = _under_root_query("SELECT 1", root)
    return conn.execute(f"{query} LIMIT 1", params).fetchone() is not None


# #141: fehérlista — csak ismert, biztonságos oszlopokra engedjük a célzott
# UPDATE-et (csillag/felirat/forgatás gyors-útja, teljes resync nélkül).
_TARGETED_UPDATE_COLUMNS = {
    "star",
    "hidden",
    "caption_ini",
    "caption_file",
    "keywords_ini",
    "keywords_file",
    "rotate_steps",
}


def update_photo_fields(conn: sqlite3.Connection, photo_id: int, **fields) -> None:
    """Egy fotó indexsorának célzott, egy-soros UPDATE-je (#141).

    A csillag/felirat/forgatás gyors-útja: amikor az új érték már ismert (a
    hívó épp most írta az inibe/IPTC-be), nincs szükség a teljes mappa-
    resyncre (`sync_tree`/`sync_folder`) — egyetlen UPDATE elég, ami az
    FTS-triggert is csak az érintett sorra sütteti el."""
    if not fields:
        return
    unknown = set(fields) - _TARGETED_UPDATE_COLUMNS
    if unknown:
        raise ValueError(f"Nem célzott-frissíthető oszlop(ok): {sorted(unknown)}")
    columns = ", ".join(f"{name} = ?" for name in fields)
    conn.execute(
        f"UPDATE photos SET {columns} WHERE id = ?",
        (*fields.values(), photo_id),
    )
    conn.commit()


def remove_root(conn: sqlite3.Connection, root: str | Path) -> None:
    """Egy gyökér teljes eltávolítása az indexből (Mappakezelő:
    „Eltávolítás a Picasából"). Explicit photos-törlés a folders előtt,
    hogy az FTS-triggerek lefussanak."""
    root_path = Path(root).resolve()
    _ensure_scan_state(conn)
    _prune_folders(conn, root_path, set())
    conn.commit()


def prune_foreign_folders(
    conn: sqlite3.Connection, roots: tuple[str | Path, ...]
) -> None:
    """A figyelt gyökerek egyikéhez sem tartozó mappák törlése az indexből.

    Induláskor fut (#58): a korábbi futásokból ottragadt gyökerek (pl. régi
    parancssori argumentum) mappái ne jelenjenek meg a bal hasábban. Üres
    gyökérlistával nem csinál semmit — védekezés, nehogy egy hiányzó
    WatchedFolders.txt csendben kiürítse az egész indexet. Explicit
    photos-törlés a folders előtt, hogy az FTS-triggerek lefussanak."""
    if not roots:
        return
    _ensure_scan_state(conn)
    root_paths = tuple(Path(root).resolve() for root in roots)
    stale = [
        (row["id"], row["path"])
        for row in conn.execute("SELECT id, path FROM folders")
        if not any(_is_under(Path(row["path"]), root) for root in root_paths)
    ]
    for folder_id, path in stale:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
        conn.execute("DELETE FROM folder_scan_state WHERE path = ?", (path,))
    conn.commit()
