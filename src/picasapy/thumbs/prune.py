"""Méretkorlátos LRU-takarító a thumbnail-lemezcache-hez (#144).

A cache kulcsa tartalom-alapú (útvonal+mtime+méret hash), ezért minden
forrásfájl-változás ÚJ bejegyzést szül — a régiek maguktól sosem tűnnek
el, a tár korlátlanul nőne. A takarító a legrégebben használt fájlokat
törli, amíg az össz-méret a korlát alá nem esik.

„Legrégebben használt": a hozzáférési idő (atime), visszaesésként az
mtime — relatime/noatime-mal szerelt fájlrendszeren az atime nem mindig
frissül, ilyenkor a keletkezési sorrend a legjobb közelítés. Minden
fájlhiba (időközben törölt fájl, párhuzamos takarító, NAS-hiba) némán
kihagyható: a takarítás best-effort, a cache tartalma újragenerálható.
"""

from __future__ import annotations

import contextlib
import os
import threading
import time
from pathlib import Path


def _scan_cache_dir(root: Path) -> tuple[list[tuple[float, int, Path]], int]:
    """A cache-fájlokat `os.scandir` + `entry.stat` használatával gyűjti össze."""
    entries: list[tuple[float, int, Path]] = []
    total = 0
    if not root.is_dir():
        return entries, total

    stack = [root]
    while stack:
        current = stack.pop()
        try:
            with os.scandir(current) as children:
                for entry in children:
                    try:
                        if entry.is_dir(follow_symlinks=False):
                            stack.append(Path(entry.path))
                        elif entry.is_file(follow_symlinks=False) and entry.name.endswith(
                            ".jpg"
                        ):
                            info = entry.stat(follow_symlinks=False)
                            entries.append(
                                (
                                    max(info.st_atime, info.st_mtime),
                                    info.st_size,
                                    Path(entry.path),
                                )
                            )
                            total += info.st_size
                    except OSError:
                        continue
        except OSError:
            continue
    return entries, total


def _read_prune_stamp(root: Path) -> tuple[float, int] | None:
    try:
        stamp, size = (root / ".prune_stamp").read_text(encoding="ascii").split(":")
        return float(stamp), int(size)
    except (OSError, ValueError):
        return None


def _write_prune_stamp(
    root: Path, total: int, checked_at: float | None = None
) -> None:
    with contextlib.suppress(OSError):
        (root / ".prune_stamp").write_text(
            f"{time.time() if checked_at is None else checked_at}:{total}",
            encoding="ascii",
        )


def _cache_dirs_changed_since(root: Path, last_prune: float) -> bool:
    """A shardmappák olcsó statja jelzi, ha új cache-bejegyzés született."""
    try:
        with os.scandir(root) as children:
            for entry in children:
                try:
                    if not entry.is_dir(follow_symlinks=False):
                        continue
                    if entry.stat(follow_symlinks=False).st_mtime >= last_prune:
                        return True
                    if not entry.name.startswith("sz"):
                        continue
                    with os.scandir(entry.path) as shards:
                        for shard in shards:
                            if shard.is_dir(follow_symlinks=False) and (
                                shard.stat(follow_symlinks=False).st_mtime >= last_prune
                            ):
                                return True
                except OSError:
                    return True
    except OSError:
        return True
    return False


def prune_cache_dir(root: str | Path, max_bytes: int) -> int:
    """A `root` alatti cache-fájlok LRU-takarítása `max_bytes` korlátig.

    Visszatérés: a ténylegesen törölt bájtok száma. Nem létező gyökérnél
    (még sosem generálódott thumbnail) 0, hiba nélkül."""
    if max_bytes < 0:
        raise ValueError("max_bytes nem lehet negatív")
    root = Path(root)
    if not root.is_dir():
        return 0
    checked_at = time.time()
    entries, total = _scan_cache_dir(root)
    if total <= max_bytes:
        _write_prune_stamp(root, total, checked_at)
        return 0
    return _prune_entries(root, entries, total, max_bytes, checked_at)


def _remove_empty_subdirs(root: Path) -> None:
    """A kiürült shard-almappák (pl. `ab/`) eltávolítása — best-effort."""
    with contextlib.suppress(OSError):  # a gyökér is eltűnhetett közben
        for child in root.iterdir():
            if child.is_dir():
                with contextlib.suppress(OSError):
                    child.rmdir()  # csak ha üres; különben OSError, lenyelve


def _prune_entries(
    root: Path,
    entries: list[tuple[float, int, Path]],
    total: int,
    max_bytes: int,
    checked_at: float | None = None,
) -> int:
    freed = 0
    for _last_used, size, path in sorted(entries):
        if total <= max_bytes:
            break
        try:
            path.unlink()
        except OSError:
            continue
        total -= size
        freed += size
    _remove_empty_subdirs(root)
    _write_prune_stamp(root, total, checked_at)
    return freed


def prune_if_needed(
    root: str | Path,
    max_bytes: int,
    min_interval_seconds: float = 86400.0,
) -> int:
    """Naponta legfeljebb egyszer takarít, mérettúllépéskor viszont azonnal (#6697)."""
    if max_bytes < 0:
        raise ValueError("max_bytes nem lehet negatív")
    root = Path(root)
    if not root.is_dir():
        return 0

    stamp = _read_prune_stamp(root)
    now = time.time()
    if stamp is not None:
        last_prune, last_size = stamp
        if now - last_prune < min_interval_seconds:
            if last_size > max_bytes:
                return prune_cache_dir(root, max_bytes)
            if not _cache_dirs_changed_since(root, last_prune):
                return 0
            checked_at = time.time()
            entries, total = _scan_cache_dir(root)
            if total <= max_bytes:
                _write_prune_stamp(root, total, checked_at)
                return 0
            return _prune_entries(root, entries, total, max_bytes, checked_at)
    return prune_cache_dir(root, max_bytes)


def prune_in_background(root: str | Path, max_bytes: int) -> threading.Thread:
    """A takarítás háttér-daemon szálon — az app indulását nem lassítja.

    A szál tisztán fájlrendszer-műveleteket végez (Qt-objektumot nem ér
    el, ld. a #53-as GIL↔Qt deadlock-osztály), így az eseményhuroktól
    függetlenül biztonságos."""
    thread = threading.Thread(
        target=lambda: prune_cache_dir(root, max_bytes),
        name="thumb-cache-prune",
        daemon=True,
    )
    thread.start()
    return thread
