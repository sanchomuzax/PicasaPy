"""#1601/#4589/#6695: a bal hasáb ini-alapú gyűjteményei."""

from __future__ import annotations

import sqlite3
import threading
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from picasapy.ini import (
    ContactNameResolver,
    ini_source_path,
    is_custom_collection_category,
    is_projects_category,
    parse_faces,
    read_folder_category,
)
from picasapy.scanner import PICASA_INI_NAME

from . import folder_ini
from .people import FaceData, PersonRecord, people_in_index
from .project_folders import ProjectFolder, project_folders_from_paths


@dataclass(frozen=True)
class SidePaneCollections:
    """A hasáb ini-alapú gyűjteményei — fagyasztott átadási adat."""

    people: tuple[PersonRecord, ...]
    project_folders: tuple[ProjectFolder, ...]
    custom_collection_folders: tuple[tuple[str, tuple[str, ...]], ...] = ()


@dataclass(frozen=True, slots=True)
class _FolderIniCacheEntry:
    """Egy mappa ini-jéből a hasábhoz szükséges, kiszűrt adatok."""

    source_path: str | None
    mtime_ns: int | None
    size: int | None
    face_data: FaceData | None
    is_project: bool
    custom_category: str | None


_SIDE_PANE_CACHE: dict[str, _FolderIniCacheEntry] = {}
_SIDE_PANE_CACHE_LOCK = threading.RLock()


def clear_side_pane_cache() -> None:
    """A mappánkénti ini-gyorstár ürítése tesztekhez és adatbázis-váltáshoz."""
    with _SIDE_PANE_CACHE_LOCK:
        _SIDE_PANE_CACHE.clear()


def side_pane_cache_ready(conn: sqlite3.Connection) -> bool:
    """Van-e gyorstár-bejegyzés az index minden ini-s mappájához?"""
    paths = tuple(
        str(row["path"])
        for row in conn.execute("SELECT path FROM folders WHERE has_ini = 1")
    )
    with _SIDE_PANE_CACHE_LOCK:
        return all(path in _SIDE_PANE_CACHE for path in paths)


def side_pane_cache_coverage(conn: sqlite3.Connection) -> tuple[int, int]:
    """(hiányzó, összes) ini-s mappa a gyorstárban; (0, n) = kész gyorstár."""
    paths = tuple(
        str(row["path"])
        for row in conn.execute("SELECT path FROM folders WHERE has_ini = 1")
    )
    with _SIDE_PANE_CACHE_LOCK:
        missing = sum(1 for path in paths if path not in _SIDE_PANE_CACHE)
    return missing, len(paths)


def refresh_side_pane_cache(
    conn: sqlite3.Connection,
    folders: Iterable[str | Path] | None = None,
    *,
    central_path=None,
) -> bool:
    """Az érintett ini-ket frissíti, és jelzi, változott-e a gyorstár.

    `folders=None` esetén minden indexelt ini-mappát ellenőriz. Megadott
    mappák esetén az adott részfa ini-i ellenőrződnek; az útvonal-ellenőrzés
    mindkét elválasztót és a Windows kis-/nagybetűs alakját kezeli.
    Változatlan (útvonal, mtime_ns, méret) kulcsnál a fájl tartalmát nem
    olvassa be újra.
    """
    folder_paths = tuple(
        str(row["path"])
        for row in conn.execute("SELECT path FROM folders WHERE has_ini = 1")
    )
    roots = None if folders is None else tuple(_normal_path(path) for path in folders)
    if roots is None:
        candidates = folder_paths
    else:
        candidates = tuple(
            path
            for path in folder_paths
            if any(_is_under(path, root) for root in roots)
        )

    changed = False
    with _SIDE_PANE_CACHE_LOCK:
        if roots is not None:
            current_paths = set(folder_paths)
            for cached_path in tuple(_SIDE_PANE_CACHE):
                if cached_path not in current_paths and any(
                    _is_under(cached_path, root) for root in roots
                ):
                    del _SIDE_PANE_CACHE[cached_path]
                    changed = True

        name_resolver = ContactNameResolver(central_path)
        for folder_path in candidates:
            ini_path = Path(folder_path) / PICASA_INI_NAME
            source = ini_source_path(ini_path)
            if source is None:
                current = _FolderIniCacheEntry(None, None, None, None, False, None)
                if _SIDE_PANE_CACHE.get(folder_path) != current:
                    _SIDE_PANE_CACHE[folder_path] = current
                    changed = True
                continue

            try:
                stat = source.stat()
            except (OSError, ValueError):
                continue

            source_path = str(source)
            cached = _SIDE_PANE_CACHE.get(folder_path)
            if (
                cached is not None
                and cached.source_path == source_path
                and cached.mtime_ns == stat.st_mtime_ns
                and cached.size == stat.st_size
            ):
                continue

            try:
                document = folder_ini.load_document(source)
            except (OSError, ValueError):
                continue

            face_data = _face_data_for_folder(
                folder_path, document, name_resolver
            )
            category = read_folder_category(document)
            entry = _FolderIniCacheEntry(
                source_path=source_path,
                mtime_ns=stat.st_mtime_ns,
                size=stat.st_size,
                face_data=face_data,
                is_project=is_projects_category(category),
                custom_category=(
                    category if is_custom_collection_category(category) else None
                ),
            )
            if cached != entry:
                _SIDE_PANE_CACHE[folder_path] = entry
                changed = True
            else:
                # Az időbélyeg vagy a méret változott, de a gyűjtemény-adat
                # azonos: a kulcs ettől még legyen naprakész.
                _SIDE_PANE_CACHE[folder_path] = entry

    return changed


def cached_side_pane_collections(
    conn: sqlite3.Connection, *, central_path=None
) -> SidePaneCollections | None:
    """A teljes oldalpanel-állapot előállítása kizárólag memóriabeli ini-adatból.

    Hiányos gyorstárnál `None` a visszatérés. Ez az út nem végez fájl-I/O-t,
    így a felület száláról is biztonságosan hívható.
    """
    folder_paths = tuple(
        str(row["path"])
        for row in conn.execute("SELECT path FROM folders WHERE has_ini = 1")
    )
    with _SIDE_PANE_CACHE_LOCK:
        if any(path not in _SIDE_PANE_CACHE for path in folder_paths):
            return None
        entries = tuple(_SIDE_PANE_CACHE[path] for path in folder_paths)

    face_rows = tuple(
        entry.face_data for entry in entries if entry.face_data is not None
    )
    project_paths = tuple(
        path
        for path, entry in zip(folder_paths, entries, strict=True)
        if entry.is_project
    )
    custom_folders: dict[str, list[str]] = {}
    for path, entry in zip(folder_paths, entries, strict=True):
        if entry.custom_category is not None:
            custom_folders.setdefault(entry.custom_category, []).append(path)

    custom_collections = tuple(
        (name, tuple(sorted(paths, key=str.casefold)))
        for name, paths in sorted(
            custom_folders.items(), key=lambda item: item[0].casefold()
        )
    )
    return SidePaneCollections(
        people=people_in_index(conn, face_rows, central_path=central_path),
        project_folders=project_folders_from_paths(conn, project_paths),
        custom_collection_folders=custom_collections,
    )


def load_side_pane_collections(
    conn: sqlite3.Connection,
    *,
    central_path=None,
    refresh_folders: Iterable[str | Path] | None = None,
) -> SidePaneCollections:
    """Emberek, Projektek és egyéni gyűjtemények közös, gyorstárazott betöltése."""
    refresh_side_pane_cache(
        conn, refresh_folders, central_path=central_path
    )
    collections = cached_side_pane_collections(conn, central_path=central_path)
    if collections is None:
        # Részfás frissítéskor csak a szinkronizált részfához nyúlunk. A
        # hiányzó régi bejegyzés rendellenes állapotot jelez; a hívó a teljes
        # gyorstár-feltöltést külön kérheti.
        return SidePaneCollections((), (), ())
    return collections


def _face_data_for_folder(
    folder_path: str, document, name_resolver: ContactNameResolver
) -> FaceData | None:
    names = name_resolver.names_by_id(document)
    if not names:
        return None
    faces_by_file = {}
    for section in document.file_sections():
        raw_faces = section.get("faces")
        if not raw_faces:
            continue
        faces = parse_faces(raw_faces)
        if faces:
            faces_by_file[section.name] = faces
    if not faces_by_file:
        return None
    return folder_path, names, faces_by_file


def _normal_path(path: str | Path) -> str:
    return str(path).replace("\\", "/").rstrip("/").casefold()


def _is_under(path: str | Path, root: str) -> bool:
    normalized = _normal_path(path)
    return normalized == root or normalized.startswith(f"{root}/")


__all__ = [
    "SidePaneCollections",
    "cached_side_pane_collections",
    "clear_side_pane_cache",
    "load_side_pane_collections",
    "refresh_side_pane_cache",
    "side_pane_cache_coverage",
    "side_pane_cache_ready",
]
