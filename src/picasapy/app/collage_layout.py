"""A kollázs-vászon kezdő elrendezése és lista-műveletei (#943).

Tiszta függvények — Qt, jelzés és állapot nélkül —, hogy a vezérlő
(`collage_controller.py`) csak listát cseréljen, és hogy az elrendezés
önmagában, felület nélkül tesztelhető legyen (a `custom_aspect_ratios.py`
+ `custom_aspect_ratios_controller.py` páros mintája).

**Semmi új geometria nem születik itt**: a méret a
`collage_model.initial_node_width` (spec 6.2), a szórás a Képkupac „legjobb
jelölt" mintavételezője (`collage.pile.scatter_centers`), a lista-műveletek
pedig a `collage.canvas` tiszta függvényei. Ez a modul csak összeköti őket
a csomópont-modellel.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import NamedTuple

from picasapy.collage.pile import UniformSource, scatter_centers

from .collage_model import SHEET_UNITS, CollageNode, initial_node_width


class CollageSource(NamedTuple):
    """Egy kollázsba tett kép: útvonal, felirat és a KÉP oldalaránya."""

    path: str
    caption: str
    aspect: float


def aspect_of(width, height) -> float:
    """A kép szélesség/magasság aránya; ismeretlen méretnél négyzetes.

    Az index nem minden képhez tud méretet (régi bejegyzés, olvashatatlan
    fájl) — ilyenkor a négyzetes közelítés a legkevésbé feltűnő hiba, és a
    QML `Image` a betöltés után úgyis a valódi arányt rajzolja."""
    try:
        w = float(width)
        h = float(height)
    except (TypeError, ValueError):
        return 1.0
    return w / h if w > 0.0 and h > 0.0 else 1.0


def sources_from_photos(photos: Sequence, rows: Iterable) -> tuple[CollageSource, ...]:
    """Rács-sorokból kép-források. Az érvénytelen sor csendben kimarad.

    A `photos` elemei `PhotoRecord`-ok (vagy bármi, aminek van
    `folder_path`, `name`, `caption`, `width`, `height` mezője)."""
    result: list[CollageSource] = []
    for row in rows or ():
        index = int(row)
        if not 0 <= index < len(photos):
            continue
        photo = photos[index]
        result.append(
            CollageSource(
                path=str(Path(photo.folder_path) / photo.name),
                caption=photo.caption or "",
                aspect=aspect_of(photo.width, photo.height),
            )
        )
    return tuple(result)


def scatter(
    count: int, page_ratio: float, rng: UniformSource
) -> tuple[tuple[float, float], ...]:
    """`count` képközéppont a lapon, LAPEGYSÉGBEN (1024 × 1024·arány)."""
    if count < 1:
        return ()
    return scatter_centers(count, SHEET_UNITS, SHEET_UNITS * page_ratio, rng)


def node_for(
    source: CollageSource,
    center: tuple[float, float],
    width: float,
    border: str,
    *,
    exists=Path.exists,
) -> CollageNode:
    """Egy csomópont a forrásból. A `missing` a fájl tényleges hiánya (9.4):
    a nem található kép HELYKITÖLTŐ csempeként marad a vásznon, nem tűnik el
    némán."""
    return CollageNode(
        path=source.path,
        center_x=center[0],
        center_y=center[1],
        width=width,
        height=width / source.aspect,
        border=border,
        caption=source.caption,
        missing=not exists(Path(source.path)),
    )


def laid_out(
    sources: Sequence[CollageSource],
    page_ratio: float,
    border: str,
    rng: UniformSource,
) -> tuple[CollageNode, ...]:
    """A kezdő elrendezés: méret a DARABSZÁMBÓL, hely a szórásból."""
    if not sources:
        return ()
    width = initial_node_width(len(sources))
    centers = scatter(len(sources), page_ratio, rng)
    return tuple(
        node_for(source, center, width, border)
        for source, center in zip(sources, centers, strict=True)
    )


def rescattered(
    nodes: Sequence[CollageNode], page_ratio: float, rng: UniformSource
) -> tuple[CollageNode, ...]:
    """A „Képek szétszórása": új helyek, változatlan méret és sorrend."""
    centers = scatter(len(nodes), page_ratio, rng)
    return tuple(
        replace(node, center_x=center[0], center_y=center[1])
        for node, center in zip(nodes, centers, strict=True)
    )


def replaced_at(
    nodes: Sequence[CollageNode], index: int, **changes
) -> tuple[CollageNode, ...]:
    """Egy csomópont cseréje új értékekkel — a lista sosem íródik felül."""
    return tuple(
        replace(node, **changes) if i == index else node
        for i, node in enumerate(nodes)
    )


def replaced_many(
    nodes: Sequence[CollageNode], indices: Iterable[int], **changes
) -> tuple[CollageNode, ...]:
    """Ugyanaz a módosítás több csomóponton (keret-váltás, bepattintás)."""
    chosen = {int(i) for i in indices}
    return tuple(
        replace(node, **changes) if i in chosen else node
        for i, node in enumerate(nodes)
    )


__all__ = [
    "CollageSource",
    "aspect_of",
    "laid_out",
    "node_for",
    "replaced_at",
    "replaced_many",
    "rescattered",
    "scatter",
    "sources_from_photos",
]
