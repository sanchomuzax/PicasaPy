"""Perceptual-hasonló képek klaszterezése Hamming-távolság alapján (#31).

Alapértelmezett küszöb: **≤10** (64 bites dHash-en) — ez a klasszikus
dHash/aHash-ajánlás gyakorlati értéke: elég szűk ahhoz, hogy két, tartalmában
teljesen eltérő kép ne párosodjon hamisan, és elég tág ahhoz, hogy egy
átméretezett vagy enyhén újratömörített változat is a küszöb alatt maradjon.
A küszöb hívóként felülírható (`phash_threshold` a `find_duplicates`-en).

A klaszterezés naiv, O(n²) páronkénti összevetéssel dolgozik (union-find a
komponensekhez) — egy fotókönyvtár (néhány ezer kép) méretében ez elfogadható;
nagyobb gyűjteményhez (LSH/BK-fa alapú indexelés) külön optimalizáló jegy
nyitható, ha a teljesítmény ezt indokolja.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from picasapy.dedup.phash import hamming_distance

DEFAULT_PHASH_THRESHOLD = 10


@dataclass(frozen=True)
class SimilarGroup:
    """Perceptuálisan hasonló képek klasztere.

    `paths` legalább két elemű, determinisztikusan (útvonal szerint) rendezve.
    `max_distance` a klaszteren belüli legnagyobb páronkénti Hamming-távolság
    (informatív — a hívó UI ebből tud "mennyire hasonló" jelzést adni)."""

    paths: tuple[Path, ...]
    max_distance: int


def group_similar(
    hashes: Sequence[tuple[Path, int]],
    threshold: int = DEFAULT_PHASH_THRESHOLD,
) -> tuple[SimilarGroup, ...]:
    """`(útvonal, dHash)` párok klaszterezése a küszöb alatti Hamming-
    távolság szerint (union-find az átfedő párosítások összefésüléséhez —
    ha A~B és B~C, mindhárom egy klaszterbe kerül még akkor is, ha A és C
    távolsága önmagában a küszöb felett lenne).

    A bemenetet nem mutálja. Az eredmény determinisztikus sorrendű."""
    ordered = sorted(hashes, key=lambda item: str(item[0]))
    count = len(ordered)
    parent = list(range(count))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def union(left: int, right: int) -> None:
        root_left, root_right = find(left), find(right)
        if root_left != root_right:
            parent[root_left] = root_right

    for i in range(count):
        for j in range(i + 1, count):
            if hamming_distance(ordered[i][1], ordered[j][1]) <= threshold:
                union(i, j)

    clusters: dict[int, list[int]] = defaultdict(list)
    for index in range(count):
        clusters[find(index)].append(index)

    groups = []
    for indices in clusters.values():
        if len(indices) < 2:
            continue
        member_paths = tuple(sorted((ordered[i][0] for i in indices), key=str))
        max_distance = max(
            hamming_distance(ordered[indices[a]][1], ordered[indices[b]][1])
            for a in range(len(indices))
            for b in range(a + 1, len(indices))
        )
        groups.append(SimilarGroup(paths=member_paths, max_distance=max_distance))

    return tuple(sorted(groups, key=lambda group: str(group.paths[0])))
