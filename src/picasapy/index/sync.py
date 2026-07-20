"""Ismételhető szinkron: fájlrendszer-scan + .picasa.ini → SQLite index.

A 7. rögzített döntés (ismételhető migráció) miatt a szinkron idempotens:
upsert a meglévő sorokra (stabil id-k), a fájlrendszerről eltűnt fájlok és
mappák törlése. Az ini az igazságforrás — minden futás a friss tartalmát
veszi át.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path

from picasapy.ini import IniDocument, load_document
from picasapy.metadata import EMPTY_METADATA, read_file_metadata
from picasapy.scanner import PICASA_INI_NAME, FolderScan, MediaFile, scan_tree

_ROTATE = re.compile(r"^rotate\((\d+)\)$")

logger = logging.getLogger(__name__)


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


def _sync_folder(conn: sqlite3.Connection, scan: FolderScan) -> None:
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


def _has_indexed_folders(conn: sqlite3.Connection, root: Path) -> bool:
    """Van-e a gyökér alá eső mappa az indexben (a scan-eredménytől függetlenül)."""
    return any(
        _is_under(Path(row["path"]), root)
        for row in conn.execute("SELECT path FROM folders")
    )


def remove_root(conn: sqlite3.Connection, root: str | Path) -> None:
    """Egy gyökér teljes eltávolítása az indexből (Mappakezelő:
    „Eltávolítás a Picasából"). Explicit photos-törlés a folders előtt,
    hogy az FTS-triggerek lefussanak."""
    root_path = Path(root).resolve()
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
    root_paths = tuple(Path(root).resolve() for root in roots)
    stale_ids = [
        row["id"]
        for row in conn.execute("SELECT id, path FROM folders")
        if not any(_is_under(Path(row["path"]), root) for root in root_paths)
    ]
    for folder_id in stale_ids:
        conn.execute("DELETE FROM photos WHERE folder_id = ?", (folder_id,))
        conn.execute("DELETE FROM folders WHERE id = ?", (folder_id,))
    conn.commit()
