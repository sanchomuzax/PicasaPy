"""Mappa-fa bejárás: média-fájlok és .picasa.ini felderítése.

Csak a médiát tartalmazó mappákat adja vissza (a Picasa is így listáz);
a rejtett mappákat — köztük a .picasaoriginals-t — kihagyja. A `exclude`
paraméterrel megadott mappák (és az alfáik) sem kerülnek bejárásra (#145,
FRExcludeFolders.txt — ld. `picasapy.scanner.exclude`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .filetypes import media_kind_of

PICASA_INI_NAME = ".picasa.ini"
# Korai Picasa-verziók vezető pont nélküli, nagybetűs néven írták az init
# (ld. docs/specs/picasa-ini-format.md) — a bejárás ezt is ini-jelenlétnek
# tekinti, hogy a mappa ne maradjon ki tévesen ini nélkülinek.
PICASA_INI_LEGACY_NAME = "Picasa.ini"


@dataclass(frozen=True)
class MediaFile:
    name: str
    kind: str
    size: int
    mtime_ns: int


@dataclass(frozen=True)
class FolderScan:
    path: Path
    has_ini: bool
    files: tuple[MediaFile, ...]


def scan_tree(
    root: str | Path, exclude: tuple[str | Path, ...] = ()
) -> tuple[FolderScan, ...]:
    """A gyökér alatti összes médiatartalmú mappa, útvonal szerint rendezve.

    Az `exclude`-ban felsorolt mappák (és az alfáik) kimaradnak a bejárásból
    (#145) — sem médiafájljaik, sem a bennük lévő almappák nem kerülnek az
    eredménybe."""
    root_path = Path(root)
    if not root_path.is_dir():
        raise FileNotFoundError(f"A szkennelendő gyökér nem létezik: {root_path}")
    exclude_paths = tuple(Path(item).resolve() for item in exclude)
    folders = []
    for current, dirnames, filenames in os.walk(root_path):
        current_path = Path(current)
        if _is_under_any(current_path, exclude_paths):
            dirnames[:] = []
            continue
        dirnames[:] = sorted(
            d
            for d in dirnames
            if not d.startswith(".")
            and not _is_under_any(current_path / d, exclude_paths)
        )
        scan = _scan_folder(current_path, filenames)
        if scan is not None:
            folders.append(scan)
    return tuple(sorted(folders, key=lambda f: f.path))


def _is_under_any(path: Path, roots: tuple[Path, ...]) -> bool:
    if not roots:
        return False
    resolved = path.resolve()
    return any(resolved == root or root in resolved.parents for root in roots)


def _scan_folder(path: Path, filenames: list[str]) -> FolderScan | None:
    files = []
    for name in sorted(filenames):
        kind = media_kind_of(name)
        if kind is None:
            continue
        try:
            info = (path / name).stat()
        except OSError:
            # Élő könyvtárban (NAS, futó Picasa) a fájl eltűnhet a listázás
            # és a stat között — egy fájl kihagyása nem buktathat scant.
            continue
        files.append(
            MediaFile(name=name, kind=kind, size=info.st_size, mtime_ns=info.st_mtime_ns)
        )
    if not files:
        return None
    has_ini = PICASA_INI_NAME in filenames or PICASA_INI_LEGACY_NAME in filenames
    return FolderScan(path=path, has_ini=has_ini, files=tuple(files))
