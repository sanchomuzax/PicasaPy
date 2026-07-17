"""Mappa-fa bejárás: média-fájlok és .picasa.ini felderítése.

Csak a médiát tartalmazó mappákat adja vissza (a Picasa is így listáz);
a rejtett mappákat — köztük a .picasaoriginals-t — kihagyja.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .filetypes import media_kind_of

PICASA_INI_NAME = ".picasa.ini"


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


def scan_tree(root: str | Path) -> tuple[FolderScan, ...]:
    """A gyökér alatti összes médiatartalmú mappa, útvonal szerint rendezve."""
    root_path = Path(root)
    if not root_path.is_dir():
        raise FileNotFoundError(f"A szkennelendő gyökér nem létezik: {root_path}")
    folders = []
    for current, dirnames, filenames in os.walk(root_path):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        scan = _scan_folder(Path(current), filenames)
        if scan is not None:
            folders.append(scan)
    return tuple(sorted(folders, key=lambda f: f.path))


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
    return FolderScan(path=path, has_ini=PICASA_INI_NAME in filenames, files=tuple(files))
