"""Mappa-fa bejárás: média-fájlok és .picasa.ini felderítése.

Csak a médiát tartalmazó mappákat adja vissza (a Picasa is így listáz);
a rejtett mappákat — köztük a .picasaoriginals-t — kihagyja. A `exclude`
paraméterrel megadott mappák (és az alfáik) sem kerülnek bejárásra (#145,
FRExcludeFolders.txt — ld. `picasapy.scanner.exclude`).

#143: a bejárás közvetlenül `os.scandir`-ra épül, és a DirEntry cache-elt
stat-eredményét használja — fájlonként pontosan egy stat fut, külön
`(path / name).stat()` hívás nélkül. A `skip` predikátummal a hívó
(inkrementális rescan) mappánként eldöntheti, hogy a fájlok stat-olása
kihagyható-e; kihagyott mappánál csak a mappa és az esetleges ini kap statot.

#303: a bejárás — az `os.walk` alapértelmezésével (`followlinks=False`)
ellentétben — KÖVETI a symlinkelt almappákat, mert NAS-os elrendezésnél
gyakori, hogy egy fotómappa symlinkkel van behúzva a figyelt gyökér alá
(pl. `~/Kepek/Regi -> /mnt/nas/foto/regi`); követés nélkül ezek szótlanul
kimaradnának az indexből. A ciklusvédelem a bejárt mappák `(st_dev, st_ino)`
azonosítóját tartja nyilván (a teljes bejáráson át élő halmazban, ld. a
`_walk` `visited_dirs` paraméterét) — ismétlődő célra mutató mappát
(symlink-kör vagy önmagára mutató symlink) kihagyja, `logger.warning`-gal
jelezve. A törött symlink (nem létező cél) csendben kimarad, nem buktatja
el a bejárást. Ez mappánként egy plusz `os.stat` hívást jelent a korábbihoz
képest — a fájlonkénti stat-optimalizáció (fentebb) ettől független marad.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .filetypes import media_kind_of

logger = logging.getLogger(__name__)

PICASA_INI_NAME = ".picasa.ini"
# Korai Picasa-verziók vezető pont nélküli, nagybetűs néven írták az init
# (ld. docs/specs/picasa-ini-format.md) — a bejárás ezt is ini-jelenlétnek
# tekinti, hogy a mappa ne maradjon ki tévesen ini nélkülinek.
PICASA_INI_LEGACY_NAME = "Picasa.ini"

# Kihagyás-döntés (#143): (mappa, mappa-mtime_ns, ini-mtime_ns vagy None)
# → True, ha a mappa fájljainak stat-olása kihagyható (a mappa változatlan).
SkipPredicate = Callable[[Path, int, "int | None"], bool]


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
    # #143: a mappa saját mtime-ja és az ini mtime-ja az inkrementális
    # rescan állapotához; csak akkor töltött, ha a hívó kérte (skip vagy
    # scan_folder) — az alapértelmezett teljes scan nem stat-ol pluszban.
    mtime_ns: int = 0
    ini_mtime_ns: int | None = None
    skipped: bool = False


def scan_tree(
    root: str | Path,
    exclude: tuple[str | Path, ...] = (),
    skip: SkipPredicate | None = None,
) -> tuple[FolderScan, ...]:
    """A gyökér alatti összes médiatartalmú mappa, útvonal szerint rendezve.

    Az `exclude`-ban felsorolt mappák (és az alfáik) kimaradnak a bejárásból
    (#145) — sem médiafájljaik, sem a bennük lévő almappák nem kerülnek az
    eredménybe.

    A `skip` predikátum (#143) mappánként dönthet a fájl-statok kihagyásáról:
    igaz válasz esetén a mappa `skipped=True`-val, üres `files`-szal kerül az
    eredménybe — a hívó tudja, hogy az indexbeli állapot érvényes maradt."""
    root_path = Path(root)
    if not root_path.is_dir():
        raise FileNotFoundError(f"A szkennelendő gyökér nem létezik: {root_path}")
    exclude_paths = tuple(Path(item).resolve() for item in exclude)
    folders: list[FolderScan] = []
    _walk(root_path, exclude_paths, skip, folders, set())
    return tuple(sorted(folders, key=lambda f: f.path))


def scan_folder(folder: str | Path) -> FolderScan | None:
    """Egyetlen mappa nem-rekurzív scanje (watcher-ág, #143).

    None, ha a mappa nem létezik / nem mappa / rejtett / nincs benne média —
    a hívó ilyenkor az indexből is eltávolíthatja."""
    path = Path(folder)
    if path.name.startswith("."):
        return None
    try:
        with os.scandir(path) as it:
            entries = list(it)
    except OSError:
        return None
    file_entries = [e for e in entries if not _entry_is_dir(e)]
    return _scan_folder(path, file_entries, skip=None, with_state=True)


def _walk(
    current: Path,
    exclude_paths: tuple[Path, ...],
    skip: SkipPredicate | None,
    out: list[FolderScan],
    visited_dirs: set[tuple[int, int]],
) -> None:
    """Rekurzív scandir-bejárás; olvashatatlan mappát csendben kihagy
    (élő NAS-on a mappa el is tűnhet menet közben).

    #303: symlinket követ, ezért a `visited_dirs` (a teljes bejáráson át
    közös, hívónként átadott állapot — NEM mappánként újul) tartja nyilván
    a már bejárt mappák `(st_dev, st_ino)` azonosítóját. Ismétlődésnél
    (symlink-kör, önmagára mutató symlink) a mappa kihagyásra kerül,
    figyelmeztetéssel."""
    if _is_under_any(current, exclude_paths):
        return
    try:
        stat = os.stat(current)
    except OSError:
        return  # törött symlink vagy időközben eltűnt/elérhetetlen mappa
    identity = (stat.st_dev, stat.st_ino)
    if identity in visited_dirs:
        logger.warning(
            "Symlink-kör kihagyva: %s (a cél már egy korábban bejárt mappa)",
            current,
        )
        return
    visited_dirs.add(identity)
    try:
        with os.scandir(current) as it:
            entries = list(it)
    except OSError:
        return
    dir_entries = []
    file_entries = []
    for entry in entries:
        if _entry_is_dir(entry):
            dir_entries.append(entry)
        else:
            file_entries.append(entry)
    scan = _scan_folder(current, file_entries, skip, with_state=skip is not None)
    if scan is not None:
        out.append(scan)
    for entry in sorted(dir_entries, key=lambda e: e.name):
        if entry.name.startswith("."):
            continue
        _walk(current / entry.name, exclude_paths, skip, out, visited_dirs)


def _entry_is_dir(entry: os.DirEntry) -> bool:
    """Mappa-e a bejegyzés — symlinket is KÖVETVE (#303, ld. a modul-
    docstring indoklását). Törött symlinkre a `DirEntry.is_dir()` nem dob
    kivételt, hanem `False`-t ad — az ilyen bejegyzés fájlként landol a
    szűrőben, ahol (jellemzően kiterjesztés hiányában) kiesik."""
    try:
        return entry.is_dir(follow_symlinks=True)
    except OSError:
        return False


def _scan_folder(
    path: Path,
    entries: list[os.DirEntry],
    skip: SkipPredicate | None,
    with_state: bool,
) -> FolderScan | None:
    by_name = {entry.name: entry for entry in entries}
    media = [
        (name, kind)
        for name in sorted(by_name)
        if (kind := media_kind_of(name)) is not None
    ]
    if not media:
        return None
    has_ini = PICASA_INI_NAME in by_name or PICASA_INI_LEGACY_NAME in by_name
    mtime_ns = 0
    ini_mtime_ns: int | None = None
    if with_state:
        try:
            mtime_ns = os.stat(path).st_mtime_ns
        except OSError:
            mtime_ns = 0
        ini_mtime_ns = _ini_mtime(by_name)
        if skip is not None and mtime_ns and skip(path, mtime_ns, ini_mtime_ns):
            return FolderScan(
                path=path,
                has_ini=has_ini,
                files=(),
                mtime_ns=mtime_ns,
                ini_mtime_ns=ini_mtime_ns,
                skipped=True,
            )
    files = []
    for name, kind in media:
        try:
            # DirEntry.stat(): az első hívás statol, az eredmény cache-elt —
            # nincs külön (path / name).stat() kör (NAS-on plusz RTT / fájl).
            info = by_name[name].stat()
        except OSError:
            # Élő könyvtárban (NAS, futó Picasa) a fájl eltűnhet a listázás
            # és a stat között — egy fájl kihagyása nem buktathat scant.
            continue
        files.append(
            MediaFile(name=name, kind=kind, size=info.st_size, mtime_ns=info.st_mtime_ns)
        )
    if not files:
        return None
    return FolderScan(
        path=path,
        has_ini=has_ini,
        files=tuple(files),
        mtime_ns=mtime_ns,
        ini_mtime_ns=ini_mtime_ns,
    )


def _ini_mtime(by_name: dict[str, os.DirEntry]) -> int | None:
    """A mappa ini-fájljának mtime-ja (elsőbbség: .picasa.ini), ha van."""
    entry = by_name.get(PICASA_INI_NAME) or by_name.get(PICASA_INI_LEGACY_NAME)
    if entry is None:
        return None
    try:
        return entry.stat().st_mtime_ns
    except OSError:
        return None


def _is_under_any(path: Path, roots: tuple[Path, ...]) -> bool:
    if not roots:
        return False
    resolved = path.resolve()
    return any(resolved == root or root in resolved.parents for root in roots)
