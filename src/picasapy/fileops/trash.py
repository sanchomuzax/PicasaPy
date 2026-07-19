"""Fájl törlése a lomtárba — freedesktop.org Trash specifikáció (#15).

A törölt fájl nem vész el visszavonhatatlanul: a desktopkörnyezet lomtár-
nézete (Nautilus, Dolphin stb.) ugyanígy olvassa vissza. Csak a "home
trash"-t (`$XDG_DATA_HOME/Trash`) valósítja meg — a más fájlrendszeren lévő
mappák `$topdir/.Trash-$uid` változata (mount-specifikus lomtár) nincs
lefedve; a `shutil.move` viszont a NAS-mappák esetén is működik (a
fájlrendszer-határon át másolással pótolja az atomikus rename-et).
"""

from __future__ import annotations

import os
import shutil
import urllib.parse
from datetime import datetime
from pathlib import Path


def delete_to_trash(path: Path, *, trash_dir: Path | None = None) -> Path:
    """A `path` fájl áthelyezése a lomtárba.

    Args:
        path: A törlendő fájl elérési útja.
        trash_dir: Teszteléshez felülírható lomtár-gyökér; alapból
            `$XDG_DATA_HOME/Trash` (`~/.local/share/Trash`).

    Returns:
        A fájl új elérési útja a lomtár `files/` alkönyvtárában.

    Raises:
        FileNotFoundError: Ha `path` nem létezik.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"A fájl nem létezik: {path}")

    trash = trash_dir if trash_dir is not None else _trash_home()
    files_dir = trash / "files"
    info_dir = trash / "info"
    files_dir.mkdir(parents=True, exist_ok=True)
    info_dir.mkdir(parents=True, exist_ok=True)

    trashed_path, info_path = _unique_destination(path.name, files_dir, info_dir)
    original = str(path.resolve())

    shutil.move(str(path), str(trashed_path))
    info_path.write_text(
        "[Trash Info]\n"
        f"Path={urllib.parse.quote(original)}\n"
        f"DeletionDate={datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}\n",
        encoding="utf-8",
    )
    return trashed_path


def _trash_home() -> Path:
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / "Trash"


def _unique_destination(
    name: str, files_dir: Path, info_dir: Path
) -> tuple[Path, Path]:
    """Ütközésmentes célnév a `files/`+`info/` párban (Picasa/Nautilus-minta:
    `_1`, `_2`, … utótag a kiterjesztés elé)."""
    candidate = name
    suffix = 0
    while (files_dir / candidate).exists() or (
        info_dir / f"{candidate}.trashinfo"
    ).exists():
        suffix += 1
        stem, dot, ext = name.partition(".")
        candidate = f"{stem}_{suffix}{dot}{ext}" if dot else f"{name}_{suffix}"
    return files_dir / candidate, info_dir / f"{candidate}.trashinfo"
