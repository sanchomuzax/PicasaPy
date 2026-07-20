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
import threading
from pathlib import Path


def prune_cache_dir(root: str | Path, max_bytes: int) -> int:
    """A `root` alatti cache-fájlok LRU-takarítása `max_bytes` korlátig.

    Visszatérés: a ténylegesen törölt bájtok száma. Nem létező gyökérnél
    (még sosem generálódott thumbnail) 0, hiba nélkül."""
    if max_bytes < 0:
        raise ValueError("max_bytes nem lehet negatív")
    root = Path(root)
    if not root.is_dir():
        return 0
    entries: list[tuple[float, int, Path]] = []
    total = 0
    try:
        for path in root.rglob("*.jpg"):
            try:
                info = path.stat()
            except OSError:
                continue  # időközben eltűnt (párhuzamos takarító/író)
            # atime, ha a fájlrendszer vezeti; különben az mtime a közelítés
            last_used = max(info.st_atime, info.st_mtime)
            entries.append((last_used, info.st_size, path))
            total += info.st_size
    except OSError:
        # Maga a bejárás is megszakadhat (a fát közben törlik — pl. a
        # cache-gyökér eltűnik a háttérszál futása alatt): best-effort,
        # az addig összegyűjtött bejegyzésekkel megyünk tovább.
        pass
    if total <= max_bytes:
        return 0
    freed = 0
    for _last_used, size, path in sorted(entries):
        if total <= max_bytes:
            break
        with contextlib.suppress(OSError):
            path.unlink()
            total -= size
            freed += size
    _remove_empty_subdirs(root)
    return freed


def _remove_empty_subdirs(root: Path) -> None:
    """A kiürült shard-almappák (pl. `ab/`) eltávolítása — best-effort."""
    with contextlib.suppress(OSError):  # a gyökér is eltűnhetett közben
        for child in root.iterdir():
            if child.is_dir():
                with contextlib.suppress(OSError):
                    child.rmdir()  # csak ha üres; különben OSError, lenyelve


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
