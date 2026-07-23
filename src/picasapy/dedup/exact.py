"""Pontos (bitre azonos) duplikátumok felderítése (#31).

Két lépés: méret-előszűrés (a fájlrendszer `stat()`-jából ingyen jön), majd
csak az azonos méretű fájlokra tartalom-hash (SHA-256). Egyedi méretű fájlnak
nem lehet bitre azonos párja, ezért ezekre a drága hash-számítás elmarad.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

_CHUNK_SIZE = 1 << 20  # 1 MiB — nagy fájloknál sem terheli túl a memóriát


@dataclass(frozen=True)
class ExactDuplicateGroup:
    """Bitre azonos tartalmú fájlok csoportja.

    `paths` legalább két elemű, determinisztikusan (útvonal szerint) rendezve.
    """

    content_hash: str
    paths: tuple[Path, ...]


def file_content_hash(path: Path) -> str | None:
    """A fájl bájtjainak SHA-256 hash-e (hex string).

    `None`, ha a fájl időközben eltűnt/elérhetetlen (NAS-forrás) — ez nem
    kivétel, a hívó egyszerűen kihagyja a fájlt az összevetésből."""
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def group_exact_duplicates(paths: Sequence[Path]) -> tuple[ExactDuplicateGroup, ...]:
    """Bitre azonos fájlok csoportosítása.

    A bemeneti sorozatot NEM mutálja. Az eredmény determinisztikus sorrendű:
    a csoportok az első (rendezett) útvonaluk szerint következnek, a
    csoporton belüli útvonalak szintén rendezve vannak — így a kimenet a
    bemeneti sorrendtől függetlenül reprodukálható."""
    by_size: dict[int, list[Path]] = defaultdict(list)
    for path in paths:
        try:
            size = path.stat().st_size
        except OSError:
            continue  # törölt/elérhetetlen fájl — kihagyjuk
        by_size[size].append(path)

    by_hash: dict[str, list[Path]] = defaultdict(list)
    for candidates in by_size.values():
        if len(candidates) < 2:
            continue  # egyedi méret: bitre azonos párja nem lehet
        for candidate in candidates:
            content_hash = file_content_hash(candidate)
            if content_hash is not None:
                by_hash[content_hash].append(candidate)

    groups = [
        ExactDuplicateGroup(
            content_hash=content_hash,
            paths=tuple(sorted(group_paths, key=str)),
        )
        for content_hash, group_paths in by_hash.items()
        if len(group_paths) >= 2
    ]
    return tuple(sorted(groups, key=lambda group: str(group.paths[0])))
