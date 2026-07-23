"""A duplikátum-kereső egyesített API-ja (#31): `find_duplicates`.

Ez a jegy csak a MAGOT (algoritmus + adatmodell) adja — a kezelő-felület
(UI, listázás, "egyesítés/törlés" műveletek) külön jegyre marad."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from picasapy.dedup.exact import ExactDuplicateGroup, group_exact_duplicates
from picasapy.dedup.phash import compute_dhash
from picasapy.dedup.similar import (
    DEFAULT_PHASH_THRESHOLD,
    SimilarGroup,
    group_similar,
)


@dataclass(frozen=True)
class DuplicateReport:
    """A duplikátum-keresés teljes, immutábilis eredménye.

    `exact_groups`: bitre azonos fájlok csoportjai.
    `similar_groups`: perceptuálisan hasonló (de NEM bitre azonos) képek
    klaszterei — egy csoport, amelynek útvonal-halmaza megegyezik egy
    `exact_groups`-beli csoportéval, itt szándékosan nem szerepel újra
    (a hívónak nem kell kétszer megjelenítenie ugyanazt az együttest)."""

    exact_groups: tuple[ExactDuplicateGroup, ...]
    similar_groups: tuple[SimilarGroup, ...]


def find_duplicates(
    paths: Sequence[str | Path],
    *,
    phash_threshold: int = DEFAULT_PHASH_THRESHOLD,
) -> DuplicateReport:
    """Duplikátum- és hasonlóság-keresés a megadott képútvonalakon.

    Két független réteg fut:
    1. **Pontos duplikátum** — tartalom-hash (SHA-256), méret-előszűrővel.
    2. **Perceptuálisan hasonló** — dHash + Hamming-távolság, `phash_threshold`
       küszöbbel (alapértelmezés: `DEFAULT_PHASH_THRESHOLD` = 10).

    A képek, amik nem dekódolhatók (sérült fájl, nem támogatott formátum),
    a perceptuális rétegből szótlanul kimaradnak — a pontos-duplikátum
    rétegre ez nem vonatkozik, az bármilyen fájltípuson (bájt-szinten) működik.

    A bemenetet nem mutálja, és nem is szűri/rendezi a hívó számára látható
    módon — az eredmény (`DuplicateReport`) determinisztikus sorrendű,
    független a `paths` bemeneti sorrendjétől."""
    normalized = tuple(Path(path) for path in paths)

    exact_groups = group_exact_duplicates(normalized)
    exact_path_sets = {frozenset(group.paths) for group in exact_groups}

    hashes: list[tuple[Path, int]] = []
    for path in normalized:
        value = compute_dhash(path)
        if value is not None:
            hashes.append((path, value))

    similar_groups = tuple(
        group
        for group in group_similar(hashes, threshold=phash_threshold)
        if frozenset(group.paths) not in exact_path_sets
    )

    return DuplicateReport(exact_groups=exact_groups, similar_groups=similar_groups)
