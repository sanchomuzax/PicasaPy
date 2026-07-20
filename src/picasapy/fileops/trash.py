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

    original = str(path.resolve())
    content = (
        "[Trash Info]\n"
        f"Path={urllib.parse.quote(original)}\n"
        f"DeletionDate={datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}\n"
    ).encode("utf-8")

    # freedesktop-spec: az info-fájlnak a MOVE ELŐTT kell léteznie,
    # kizárólagos létrehozással (O_EXCL) — így félbeszakadt/tele lemezes
    # move esetén sosem marad "árva" fájl visszaállítási info nélkül.
    trashed_path, info_path = _create_trashinfo_exclusively(
        path.name, files_dir, info_dir, content
    )

    try:
        shutil.move(str(path), str(trashed_path))
    except Exception:
        info_path.unlink(missing_ok=True)
        raise
    return trashed_path


def _trash_home() -> Path:
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / "Trash"


def _candidate_name(name: str, suffix: int) -> str:
    """Ütközésmentes célnév-jelölt (Picasa/Nautilus-minta: `_1`, `_2`, …
    utótag a kiterjesztés elé)."""
    if suffix == 0:
        return name
    stem, dot, ext = name.partition(".")
    return f"{stem}_{suffix}{dot}{ext}" if dot else f"{name}_{suffix}"


def _create_trashinfo_exclusively(
    name: str, files_dir: Path, info_dir: Path, content: bytes
) -> tuple[Path, Path]:
    """Az info-fájl kizárólagos (O_EXCL) létrehozása egy még szabad
    célnévvel. Ha a `files/`-ben már foglalt a név (korábbi, be nem
    fejezett törlés maradványa), a jelölt is kimarad — így a `files/` és
    az `info/` pár mindig összetartozik."""
    suffix = 0
    while True:
        candidate = _candidate_name(name, suffix)
        trashed_path = files_dir / candidate
        info_path = info_dir / f"{candidate}.trashinfo"
        if trashed_path.exists():
            suffix += 1
            continue
        try:
            fd = os.open(info_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
        except FileExistsError:
            suffix += 1
            continue
        try:
            os.write(fd, content)
        finally:
            os.close(fd)
        return trashed_path, info_path
