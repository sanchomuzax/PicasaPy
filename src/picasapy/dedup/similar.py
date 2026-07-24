"""Perceptuális-hasonló képek klaszterezése Hamming-távolság alapján (#31).

Alapértelmezett küszöb: **≤10** (64 bites dHash-en) — ez a klasszikus
dHash/aHash-ajánlás gyakorlati értéke: elég szűk ahhoz, hogy két, tartalmában
teljesen eltérő kép ne párosodjon hamisan, és elég tág ahhoz, hogy egy
átméretezett vagy enyhén újratömörített változat is a küszöb alatt maradjon.
A küszöb hívóként felülírható (`phash_threshold` a `find_duplicates`-en).

#294 — SÁVOS (banding) jelöltszűrés a korábbi, minden párt összevető O(n²)
helyett. Az elv a pigeonhole: a 64 bitet `küszöb+1` sávra osztjuk, így ha két
hash távolsága legfeljebb a küszöb, akkor a legfeljebb ennyi eltérő bit nem
juthat MINDEN sávba — legalább egy sávjuk bitre azonos. Elég tehát csak azokat
a párokat összevetni, amelyek legalább egy sávon egyeznek; a többi biztosan a
küszöb fölött van. A szűrés EGZAKT: hamis negatív nincs, az eredmény bitre
ugyanaz, mint a naiv összevetésé (ld. `tests/dedup/test_similar.py::
TestBucketedCandidates`). Az összefésülés továbbra is union-find.

A sávozás előtt az AZONOS hash-ű képek egyetlen reprezentánsba olvadnak
össze (távolságuk triviálisan 0), és a jelöltszűrés már csak a KÜLÖNBÖZŐ
hash-értékeken fut. Enélkül egy nagy, azonos lenyomatú tömeg (több ezer
egyszínű/üres kép egy könyvtárban — pont ami a #294 fagyást is okozta)
sávonként is négyzetes jelöltszámot adna.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from picasapy.dedup.phash import hamming_distance

DEFAULT_PHASH_THRESHOLD = 10

_HASH_BITS = 64

# A klaszteren belüli pontos (páronkénti) max-távolság csak eddig a
# tagszámig fut le — fölötte a reprezentánshoz (az első taghoz) mért
# legnagyobb távolság az eredmény. Dokumentált ALSÓ BECSLÉS: a UI-nak
# csak tájékoztató „mennyire hasonló" jelzés, egy több ezer tagú klaszter
# pontos átmérőjéért nem éri meg O(k²)-t fizetni.
_MAX_EXACT_DISTANCE_MEMBERS = 64


@dataclass(frozen=True)
class SimilarGroup:
    """Perceptuálisan hasonló képek klasztere.

    `paths` legalább két elemű, determinisztikusan (útvonal szerint) rendezve.
    `max_distance` a klaszteren belüli legnagyobb páronkénti Hamming-távolság
    (informatív — a hívó UI ebből tud "mennyire hasonló" jelzést adni);
    nagyon nagy klaszternél alsó becslés, ld. `_MAX_EXACT_DISTANCE_MEMBERS`."""

    paths: tuple[Path, ...]
    max_distance: int


def _band_layout(threshold: int) -> tuple[tuple[int, int], ...]:
    """`(eltolás, szélesség)` sávok a jelöltszűréshez.

    `küszöb+1` sáv fedi le a 64 bitet (a maradék bitek az első sávok
    között oszlanak el). Ha a küszöb már 64 vagy afölötti, a sávozás
    értelmét veszti (minden pár jelölt) — ilyenkor egyetlen, 0 bites
    „sáv" jelzi a hívónak, hogy mindent össze kell vetni."""
    bands = threshold + 1
    if bands >= _HASH_BITS:
        return ((0, 0),)
    width, remainder = divmod(_HASH_BITS, bands)
    layout = []
    offset = 0
    for index in range(bands):
        band_width = width + (1 if index < remainder else 0)
        layout.append((offset, band_width))
        offset += band_width
    return tuple(layout)


def _candidate_pairs(values: Sequence[int], threshold: int):
    """A küszöb alatt lehetséges `(i, j)` indexpárok (i < j).

    Egy pár többször is előjöhet (több sávon egyezhet) — a hívó union-findja
    ezt olcsón kiszűri, ezért nem tartunk fenn külön pár-halmazt (140k képnél
    az maga lenne a memória-robbanás)."""
    layout = _band_layout(threshold)
    if layout == ((0, 0),):  # sávozás nélkül: minden pár jelölt
        for i in range(len(values)):
            for j in range(i + 1, len(values)):
                yield i, j
        return
    for offset, width in layout:
        mask = (1 << width) - 1
        buckets: dict[int, list[int]] = defaultdict(list)
        for index, value in enumerate(values):
            buckets[(value >> offset) & mask].append(index)
        for indices in buckets.values():
            if len(indices) < 2:
                continue
            for a in range(len(indices)):
                for b in range(a + 1, len(indices)):
                    yield indices[a], indices[b]


def _cluster_max_distance(values: Sequence[int], indices: Sequence[int]) -> int:
    """A klaszter „átmérője" bitekben. Kis klaszterre pontos (minden pár),
    `_MAX_EXACT_DISTANCE_MEMBERS` fölött a reprezentánshoz (az első taghoz)
    mért maximum — dokumentált alsó becslés, korlátos költséggel."""
    if len(indices) <= _MAX_EXACT_DISTANCE_MEMBERS:
        return max(
            hamming_distance(values[indices[a]], values[indices[b]])
            for a in range(len(indices))
            for b in range(a + 1, len(indices))
        )
    representative = values[indices[0]]
    return max(hamming_distance(representative, values[i]) for i in indices[1:])


def group_similar(
    hashes: Sequence[tuple[Path, int]],
    threshold: int = DEFAULT_PHASH_THRESHOLD,
    should_stop: Callable[[], bool] | None = None,
) -> tuple[SimilarGroup, ...]:
    """`(útvonal, dHash)` párok klaszterezése a küszöb alatti Hamming-
    távolság szerint (union-find az átfedő párosítások összefésüléséhez —
    ha A~B és B~C, mindhárom egy klaszterbe kerül még akkor is, ha A és C
    távolsága önmagában a küszöb felett lenne).

    A jelöltpárok sávos szűréssel állnak elő (ld. a modul docstringjét) —
    az eredmény azonos a minden párt összevető változatéval.

    `should_stop`: megszakítás-kérés (a `sync_tree` #216-os mintája szerint).
    Igaz értéknél a klaszterezés félbehagyja a munkát és ÜRES eredményt ad —
    a részleges klaszterezés félrevezető lenne (hiányzó él = szétesett
    csoport), ezért részeredményt szándékosan nem közlünk.

    A bemenetet nem mutálja. Az eredmény determinisztikus sorrendű."""
    ordered = sorted(hashes, key=lambda item: str(item[0]))
    count = len(ordered)
    values = [value for _path, value in ordered]
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

    # 1. Az azonos hash-ű képek azonnal egy klaszterbe (távolságuk 0), és a
    #    továbbiakban csak a KÜLÖNBÖZŐ értékek vesznek részt a szűrésben.
    by_value: dict[int, list[int]] = defaultdict(list)
    for index, value in enumerate(values):
        by_value[value].append(index)
    for members in by_value.values():
        for other in members[1:]:
            union(members[0], other)

    distinct = sorted(by_value)  # determinisztikus sávozás
    representatives = [by_value[value][0] for value in distinct]

    # 2. Sávos jelöltszűrés a különböző értékeken.
    checked = 0
    for left, right in _candidate_pairs(distinct, threshold):
        # a megszakítás-ellenőrzés ritkítva fut: a jelöltpárok száma
        # milliós is lehet, hívásonkénti kérdezés maga lenne a szűk hely
        checked += 1
        if should_stop is not None and checked % 4096 == 0 and should_stop():
            return ()
        left_index, right_index = representatives[left], representatives[right]
        if find(left_index) == find(right_index):
            continue  # már egy klaszterben — a távolság mérése felesleges
        if hamming_distance(distinct[left], distinct[right]) <= threshold:
            union(left_index, right_index)

    if should_stop is not None and should_stop():
        return ()

    clusters: dict[int, list[int]] = defaultdict(list)
    for index in range(count):
        clusters[find(index)].append(index)

    groups = []
    for indices in clusters.values():
        if len(indices) < 2:
            continue
        member_paths = tuple(sorted((ordered[i][0] for i in indices), key=str))
        groups.append(
            SimilarGroup(
                paths=member_paths,
                max_distance=_cluster_max_distance(values, indices),
            )
        )

    return tuple(sorted(groups, key=lambda group: str(group.paths[0])))
