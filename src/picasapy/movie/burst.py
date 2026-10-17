"""A Filmkészítő időcsoportjai és ordering=0 képlánca (#4194)."""

from __future__ import annotations

from collections.abc import Callable, Sequence
import math


_HOG_EPSILON = 1e-8
_MAX_CANDIDATES = 100
_DIRECTION_SWITCH_BELOW = 15
_MAX_COST = 1e8


def capture_groups(
    capture_times: Sequence[float | int | None], threshold_seconds: int
) -> list[int]:
    """Szomszédos, egész másodpercre kerekített idők csoportazonosítói.

    Nulla küszöbnél minden elem saját csoportot kap. Ismeretlen időbélyeg
    esetén az adott kép külön csoportot kezd, mert a közelségét nem lehet
    megállapítani.
    """
    if threshold_seconds <= 0:
        return list(range(len(capture_times)))

    rounded = [None if value is None else round(float(value)) for value in capture_times]
    if not rounded:
        return []

    groups = [0]
    group = 0
    for previous, current in zip(rounded[:-1], rounded[1:], strict=True):
        if (
            previous is None
            or current is None
            or current - previous >= threshold_seconds
        ):
            group += 1
        groups.append(group)
    return groups


def d_hog(first: Sequence[float], second: Sequence[float]) -> float:
    """A mért HOG-párdistancia chi-négyzet képlete, 1e-8 regularizálással."""
    if len(first) != len(second):
        raise ValueError("A HOG-jellemzővektorok mérete nem egyezik.")
    return math.fsum(
        (float(a) - float(b)) ** 2 / (float(a) + float(b) + _HOG_EPSILON)
        for a, b in zip(first, second, strict=True)
    )


def _spiral_positions(center: int, count: int):
    """Indexek a középpontból: +1, -1, +2, -2, …"""
    for distance in range(1, count + 1):
        yield center + distance
        yield center - distance


def _candidates(
    groups: Sequence[int],
    selected: bytearray,
    center: int,
    *,
    forward_only: bool,
) -> list[int]:
    candidates: list[int] = []
    for position in _spiral_positions(center, len(groups)):
        if position < 0 or position >= len(groups):
            continue
        if forward_only and position <= center:
            continue
        if selected[position] or groups[position] == groups[center]:
            continue
        candidates.append(position)
        if len(candidates) == _MAX_CANDIDATES:
            break
    return candidates


def select_chain(
    groups: Sequence[int],
    count: int,
    *,
    feature_for_index: Callable[[int], Sequence[float]],
    anchor: int = 0,
) -> list[int]:
    """Kiválasztási sorrend az `ordering=0` G/5 modellje szerint.

    A jellemzőforrás szándékosan injektálható: a Picasa `0x00873cb0`
    jellemzővektorának előállítása még nincs feltárva (#4194).
    """
    size = len(groups)
    if size == 0 or count <= 0:
        return []
    if not 0 <= anchor < size:
        raise ValueError("A filmhorgony kívül esik a képlista tartományán.")

    result = [anchor]
    selected = bytearray(size)
    selected[anchor] = 1
    target = min(int(count), size)

    while len(result) < target:
        center = result[-1]
        candidates = _candidates(
            groups, selected, center, forward_only=True
        )
        if len(candidates) < _DIRECTION_SWITCH_BELOW:
            # A natív kód irányt vált, és ugyanazzal a spirállal mindkét
            # oldalról enged jelölteket. Az érvényes, korábbi oldali képek
            # így is a +1,-1,+2,-2… bejárási sorrendben kerülnek a pontozóhoz.
            candidates = _candidates(
                groups, selected, center, forward_only=False
            )
        if not candidates:
            break

        best = candidates[0]
        best_cost = _MAX_COST
        center_feature = feature_for_index(center)
        for candidate in candidates:
            cost = d_hog(center_feature, feature_for_index(candidate))
            if cost < best_cost:
                best = candidate
                best_cost = cost

        selected[best] = 1
        result.append(best)

    return result
