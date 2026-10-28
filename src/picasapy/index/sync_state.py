"""Az index-szinkron felelősségi része; a régi API a sync.py-n át él."""

from __future__ import annotations

import logging
import sqlite3
import time
from collections.abc import Collection
from pathlib import Path

from picasapy.index.queries import HIDDEN_INI_PENDING
from picasapy.scanner import (
    FolderScan,
)

from .sync_compat import legacy

logger = logging.getLogger("picasapy.index.sync")


def _ensure_photo_hashes(conn: sqlite3.Connection) -> None:
    """A #294 hash-gyorsítótár lusta létrehozása — a `move_folder_tree`
    régi (a tábla bevezetése előtt született) indexen is futhat.

    A MAI alakot hozza létre (#1494: nullázható `dhash` + `originfast`), a
    `schema.py` `_PHOTO_HASHES_DDL`-jével egyezően. Egy MÁR LÉTEZŐ
    táblát nem alakít át — az a sémaverzió-migráció dolga."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS photo_hashes ("
        " path TEXT PRIMARY KEY,"
        " mtime_ns INTEGER NOT NULL,"
        " size INTEGER NOT NULL,"
        " dhash INTEGER,"
        " originfast INTEGER)"
    )


def _ensure_similarity_features(conn: sqlite3.Connection) -> None:
    """Régi, közvetlenül megnyitott indexekhez is létrehozza a jellemző-cache-t."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS photo_similarity ("
        " path TEXT PRIMARY KEY,"
        " mtime_ns INTEGER NOT NULL,"
        " size INTEGER NOT NULL,"
        " rgb565 BLOB NOT NULL,"
        " histogram BLOB NOT NULL,"
        " edges BLOB NOT NULL)"
    )


def folder_scan_stamps(
    conn: sqlite3.Connection, paths: tuple[str, ...]
) -> dict[str, tuple[int, int | None]]:
    """A megadott mappák utoljára LÁTOTT pecsétje (mtime_ns, ini_mtime_ns).

    A `folder_scan_state` táblát a szinkron amúgy is vezeti — ez csak
    OLVASSA (#1435), új séma nincs. A hívó (`app/folder_freshness.py`)
    ehhez hasonlítja a lemezen mért pecsétet, és csak eltérésnél kér
    teljes újraolvasást. A még sosem látott mappa egyszerűen kimarad a
    szótárból."""
    if not paths:
        return {}
    legacy("_ensure_scan_state")(conn)
    placeholders = ",".join("?" for _ in paths)
    return {
        row["path"]: (row["mtime_ns"], row["ini_mtime_ns"])
        for row in conn.execute(
            "SELECT s.path, s.mtime_ns, s.ini_mtime_ns"
            " FROM folder_scan_state s JOIN folders f ON f.path = s.path"
            f" WHERE s.path IN ({placeholders})",
            paths,
        )
    }


def _filetype_signature(enabled_filetypes: Collection[str] | None) -> str | None:
    """Beállítás-kulcs a pecséthez: csoportváltáskor ne legyen régi skip."""
    if enabled_filetypes is None:
        return None
    return ",".join(sorted(enabled_filetypes))


def _make_skip(conn: sqlite3.Connection, filetype_signature: str | None = None):
    """Kihagyás-predikátum az inkrementális rescanhez (#143).

    Csak olyan mappa hagyható ki, amely (1) az indexben is szerepel,
    (2) mappa- és ini-mtime-ja bitre egyezik a tárolt állapottal, és
    (3) mindkét mtime idősebb a frissesség-védőablaknál."""
    state = {
        row["path"]: (row["mtime_ns"], row["ini_mtime_ns"], row["filetype_signature"])
        for row in conn.execute(
            "SELECT s.path, s.mtime_ns, s.ini_mtime_ns, s.filetype_signature"
            " FROM folder_scan_state s JOIN folders f ON f.path = s.path"
        )
    }
    # #4580: migráció után a régi indexek videói NULL formátummal indulnak.
    # Ezek mappája nem hagyható ki akkor sem, ha a scan-pecsét még friss.
    # #4597: az ini-be még be nem írt rejtés (régi index) mappája sem — az
    # egyszeri átállás az első szinkronon lefut.
    always_scan = {
        row["path"]
        for row in conn.execute(
            "SELECT DISTINCT f.path FROM photos p"
            " JOIN folders f ON f.id = p.folder_id"
            " WHERE p.kind = 'video' AND p.movie_format IS NULL"
        )
    } | {
        row["path"]
        for row in conn.execute("SELECT path FROM folders WHERE hidden = ?", (HIDDEN_INI_PENDING,))
    }
    fresh_limit = time.time_ns() - legacy("_SKIP_SAFETY_NS")

    def skip(path: Path, mtime_ns: int, ini_mtime_ns: int | None) -> bool:
        if str(path) in always_scan:
            return False
        return (
            state.get(str(path)) == (mtime_ns, ini_mtime_ns, filetype_signature)
            and mtime_ns <= fresh_limit
            and (ini_mtime_ns is None or ini_mtime_ns <= fresh_limit)
        )

    return skip


def _store_scan_state(
    conn: sqlite3.Connection,
    scan: FolderScan,
    filetype_signature: str | None = None,
) -> None:
    if not scan.mtime_ns:
        return  # a mappa statja nem sikerült — ne rögzítsünk hamis állapotot
    conn.execute(
        "INSERT INTO folder_scan_state(path, mtime_ns, ini_mtime_ns, "
        "filetype_signature) VALUES (?, ?, ?, ?)"
        " ON CONFLICT(path) DO UPDATE SET mtime_ns = excluded.mtime_ns,"
        " ini_mtime_ns = excluded.ini_mtime_ns,"
        " filetype_signature = excluded.filetype_signature",
        (str(scan.path), scan.mtime_ns, scan.ini_mtime_ns, filetype_signature),
    )
