"""Ismételhető szinkron: fájlrendszer-scan + .picasa.ini → SQLite index.

A 7. rögzített döntés (ismételhető migráció) miatt a szinkron idempotens:
upsert a meglévő sorokra (stabil id-k), a fájlrendszerről eltűnt fájlok és
mappák törlése. Az ini az igazságforrás — minden futás a friss tartalmát
veszi át.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from picasapy.ini import IniDocument, load_document
from picasapy.metadata import EMPTY_METADATA, read_file_metadata
from picasapy.scanner import PICASA_INI_NAME, FolderScan, MediaFile, scan_tree

_ROTATE = re.compile(r"^rotate\((\d+)\)$")


def sync_tree(conn: sqlite3.Connection, root: str | Path) -> None:
    """A gyökér alatti könyvtár teljes szinkronja az indexbe.

    Az index kanonikus (feloldott, abszolút) útvonalakra kulcsol, ezért a
    gyökeret belépéskor normalizáljuk. Mappánként commitolunk: nagy (100k+)
    könyvtárnál nem nő össze a WAL, és megszakadás után a futás onnan
    folytatható, ahol tartott (a szinkron mappánként idempotens).

    Ismert korlátok:
    - RAW és videó fájloknál nincs EXIF/IPTC-olvasás (a Pillow nem dekódolja
      őket) → taken_at/orientation/méret üres marad; RAW-támogatás később.
    - A változás-detektálás (mtime_ns, size) páros: egy mtime-őrző, azonos
      méretű IPTC-átírást (pl. exiftool -P) nem vesz észre. A Picasa maga
      mindig frissíti az mtime-ot, így ez a gyakorlatban nem fordul elő.
    - A keywords_file vesszővel join-olt lista: vesszőt tartalmazó kulcsszó
      nem bontható vissza veszteség nélkül (FTS-t és megjelenítést nem zavar).
    """
    root_path = Path(root).resolve()
    scans = scan_tree(root_path)
    for scan in scans:
        _sync_folder(conn, scan)
        conn.commit()
    _prune_folders(conn, root_path, {str(scan.path) for scan in scans})
    conn.commit()


def _sync_folder(conn: sqlite3.Connection, scan: FolderScan) -> None:
    folder_id = conn.execute(
        "INSERT INTO folders(path, has_ini) VALUES (?, ?) "
        "ON CONFLICT(path) DO UPDATE SET has_ini = excluded.has_ini "
        "RETURNING id",
        (str(scan.path), int(scan.has_ini)),
    ).fetchone()[0]
    existing = {
        row["name"]: (row["mtime_ns"], row["size"])
        for row in conn.execute(
            "SELECT name, mtime_ns, size FROM photos WHERE folder_id = ?",
            (folder_id,),
        )
    }
    document = _load_ini(scan)
    for media in scan.files:
        section = document.section(media.name) if document else None
        ini_fields = (
            int(section.get("star") == "yes") if section else 0,
            section.get("caption") if section else None,
            section.get("keywords") if section else None,
            _rotate_steps(section.get("rotate")) if section else 0,
            section.get("filters") if section else None,
        )
        if existing.get(media.name) == (media.mtime_ns, media.size):
            # Változatlan fájl: csak az ini-mezők frissülnek, a (drága)
            # EXIF/IPTC-olvasás kimarad, a fájl-metaadat oszlopok maradnak.
            conn.execute(
                "UPDATE photos SET star = ?, caption_ini = ?, keywords_ini = ?,"
                " rotate_steps = ?, filters = ?"
                " WHERE folder_id = ? AND name = ?",
                (*ini_fields, folder_id, media.name),
            )
        else:
            _upsert_photo(conn, folder_id, scan, media, ini_fields)
    _prune_photos(conn, folder_id, [media.name for media in scan.files])
    # mappa-dátum (Picasa): automatikusan a legrégebbi felvétel ideje
    conn.execute(
        "UPDATE folders SET date = ("
        " SELECT MIN(p.taken_at) FROM photos p WHERE p.folder_id = ?"
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
        read_file_metadata(scan.path / media.name)
        if media.kind == "photo"
        else EMPTY_METADATA
    )
    conn.execute(
        "INSERT INTO photos"
        "(folder_id, name, kind, size, mtime_ns, star, caption_ini,"
        " keywords_ini, rotate_steps, filters, taken_at, orientation,"
        " width, height, caption_file, keywords_file)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
        "ON CONFLICT(folder_id, name) DO UPDATE SET "
        "kind = excluded.kind, size = excluded.size, "
        "mtime_ns = excluded.mtime_ns, star = excluded.star, "
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

    Explicit photos-törlés a folders előtt, hogy az FTS-triggerek biztosan
    lefussanak (az FK-cascade nem minden konfigurációban futtat triggert).
    """
    stale_ids = [
        row["id"]
        for row in conn.execute("SELECT id, path FROM folders")
        if row["path"] not in seen_paths
        and _is_under(Path(row["path"]), root)
    ]
    for folder_id in stale_ids:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))


def _is_under(path: Path, root: Path) -> bool:
    return path == root or path.is_relative_to(root)


def remove_root(conn: sqlite3.Connection, root: str | Path) -> None:
    """Egy gyökér teljes eltávolítása az indexből (Mappakezelő:
    „Eltávolítás a Picasából"). Explicit photos-törlés a folders előtt,
    hogy az FTS-triggerek lefussanak."""
    root_path = Path(root).resolve()
    _prune_folders(conn, root_path, set())
    conn.commit()
