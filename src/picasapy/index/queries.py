"""Olvasó lekérdezések: mappa-lista, csillagozottak, FTS5 keresés."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

# A hatásos caption/keywords: JPEG-nél az IPTC (caption_file) az elsődleges,
# egyébként a .picasa.ini értéke (Picasa-viselkedés).
_SELECT = """
SELECT p.id, f.path AS folder_path, p.name, p.kind, p.size, p.mtime_ns,
       p.star, COALESCE(p.caption_file, p.caption_ini) AS caption,
       COALESCE(p.keywords_file, p.keywords_ini) AS keywords,
       p.rotate_steps, p.taken_at, p.orientation, p.width, p.height
FROM photos p JOIN folders f ON f.id = p.folder_id
"""


@dataclass(frozen=True)
class PhotoRecord:
    id: int
    folder_path: str
    name: str
    kind: str
    size: int
    mtime_ns: int
    star: bool
    caption: str | None
    keywords: str | None
    rotate_steps: int
    taken_at: str | None
    orientation: int
    width: int | None
    height: int | None


def photos_in_folder(
    conn: sqlite3.Connection, folder: str | Path
) -> tuple[PhotoRecord, ...]:
    rows = conn.execute(
        f"{_SELECT} WHERE f.path = ? ORDER BY p.name", (str(folder),)
    )
    return _records(rows)


def starred_photos(conn: sqlite3.Connection) -> tuple[PhotoRecord, ...]:
    rows = conn.execute(f"{_SELECT} WHERE p.star = 1 ORDER BY f.path, p.name")
    return _records(rows)


def search_photos(conn: sqlite3.Connection, query: str) -> tuple[PhotoRecord, ...]:
    """FTS5 keresés név/felirat/kulcsszó mezőkben.

    A felhasználói inputot idézett kifejezéssé alakítjuk, hogy ne
    értelmeződjön FTS-szintaxisként (injection/szintaxishiba ellen).
    """
    phrase = '"' + query.replace('"', '""') + '"'
    rows = conn.execute(
        f"{_SELECT} JOIN photos_fts ON photos_fts.rowid = p.id "
        "WHERE photos_fts MATCH ? ORDER BY f.path, p.name",
        (phrase,),
    )
    return _records(rows)


def _records(rows: sqlite3.Cursor) -> tuple[PhotoRecord, ...]:
    return tuple(
        PhotoRecord(
            id=row["id"],
            folder_path=row["folder_path"],
            name=row["name"],
            kind=row["kind"],
            size=row["size"],
            mtime_ns=row["mtime_ns"],
            star=bool(row["star"]),
            caption=row["caption"],
            keywords=row["keywords"],
            rotate_steps=row["rotate_steps"],
            taken_at=row["taken_at"],
            orientation=row["orientation"],
            width=row["width"],
            height=row["height"],
        )
        for row in rows
    )
