"""A kollázs-vászon kezdő elrendezése és lista-műveletei (#943, #989).

Tiszta függvények — Qt, jelzés és állapot nélkül —, hogy a vezérlő
(`collage_controller.py`) csak listát cseréljen, és hogy az elrendezés
önmagában, felület nélkül tesztelhető legyen (a `custom_aspect_ratios.py`
+ `custom_aspect_ratios_controller.py` páros mintája).

**Semmi új geometria nem születik itt.** A hat téma pakolója a magban él
(`collage.picasa_render.layout_nodes_for_aspects`), és a MENTÉS is azt
futtatja; ez a modul csak lefordítja a panel forrásait a pakoló nyelvére,
és a kapott csomópontokat a felület modelljére.

## ⚠️ #989: a téma-választó eddig nem hatott a vászonra

A `laid_out` szignatúrájában NEM VOLT `theme` paraméter, a törzse pedig
mindig a Képkupac szórását hívta — a hat elrendezésből tehát egy sem
látszott a Képkupacon kívül. A pakolók KÉSZEN álltak a magban, csak a
panel nem hívta őket; a javítás ezért nem új geometria, hanem BEKÖTÉS.

A panel csak az index **oldalarányát** ismeri (a képeket nem dekódolja —
350 képnél nem is tehetné), ezért az aspektus-alapú bejáraton megy be. A
geometria egyik oldalon sem függ a forráskép abszolút képpontméretétől
(`fitting.fit_aspect_inside`).
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import replace
from pathlib import Path
from typing import NamedTuple

from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    layout_nodes_for_aspects,
)
from picasapy.collage.pile import UniformSource, scatter_centers
from picasapy.collage.themes import FRAMEGRID, PICTUREPILE

from .collage_model import SHEET_UNITS, CollageNode


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
        aspect=source.aspect,
    )


def sheet_settings(
    theme: str,
    page_ratio: float,
    border: str,
    *,
    spacing: float = 0.0,
    frame_center: int = -1,
    seed: int = 1,
) -> PicasaCollageSettings:
    """A pakoló beállításai a LAP egységrendszerében (spec 6.1).

    A lap belső szélessége 1024 EGYSÉG, ezért a pakolót is 1024 „képpont"
    széles lapra futtatjuk: így a `pixels_to_sheet` átváltás azonosság, és a
    csomópontok egyből lapegységben állnak elő. A `−1` képkockaközéppont a
    „nincs rögzített kép" jelzés (spec 8.1).

    A háttérszín és az árnyék szándékosan hiányzik: az elrendezést egyik
    sem befolyásolja, a RAJZOLÁS beállításait a `collage_output` állítja
    össze."""
    return PicasaCollageSettings(
        theme=theme,
        border=border,
        width=int(SHEET_UNITS),
        height=max(16, round(SHEET_UNITS * page_ratio)),
        spacing=spacing,
        seed=seed,
        frame_center=None if frame_center < 0 else int(frame_center),
    )


def laid_out(
    sources: Sequence[CollageSource],
    page_ratio: float,
    border: str,
    *,
    theme: str = PICTUREPILE,
    spacing: float = 0.0,
    frame_center: int = -1,
    seed: int = 1,
    exists=Path.exists,
) -> tuple[CollageNode, ...]:
    """A kezdő elrendezés a TÉMA pakolójából (#989).

    A geometriát a mag adja (`layout_nodes_for_aspects`), a képhez tartozó
    adatokat (felirat, „nem található", oldalarány) pedig a forrás. A kettőt
    az ÚTVONAL köti össze, nem a sorrend: a Képkockamozaik a hangsúlyos
    képet a lista VÉGÉRE emeli (az a legfelső réteg), tehát a pozíció
    szerinti párosítás idegen feliratot adna a képekhez.

    Ugyanaz a fájl kétszer is szerepelhet a kollázsban; a hozzá tartozó
    felirat és oldalarány viszont ilyenkor is ugyanaz (mindkettő a fotó
    indexbeli sorából jön), ezért az útvonal-kulcs egyértelmű."""
    if not sources:
        return ()
    beallitas = sheet_settings(
        theme,
        page_ratio,
        border,
        spacing=spacing,
        frame_center=frame_center,
        seed=seed,
    )
    nodes = layout_nodes_for_aspects(
        [source.aspect for source in sources],
        [source.path for source in sources],
        beallitas,
    )
    kepek = {source.path: source for source in sources}
    hianyzik = {
        source.path: not exists(Path(source.path)) for source in sources
    }
    return tuple(
        CollageNode(
            path=str(node.path),
            center_x=node.center_x,
            center_y=node.center_y,
            width=node.width,
            height=node.height,
            theta=node.theta,
            border=node.border,
            caption=kepek[str(node.path)].caption,
            missing=hianyzik[str(node.path)],
            aspect=kepek[str(node.path)].aspect,
        )
        for node in nodes
    )


def layout_uses_frame_center(theme: str) -> bool:
    """Olvassa-e a téma pakolója a képkockaközéppontot.

    Csak a Képkockamozaiké — a többi téma elrendezését a „Beállítás
    képkockaközéppontként" nem befolyásolja. A tudás ITT él, a pakoló
    mellett, hogy a vezérlőben ne kelljen témát vizsgálni."""
    return theme == FRAMEGRID


def frame_center_after(theme: str, frame_center: int, count: int) -> int:
    """A képkockaközéppont ÚJ indexe az újrarendezés után.

    A pakoló a hangsúlyos képet a lista VÉGÉRE teszi (az a legfelső réteg,
    ld. `picasa_render.layout_nodes_for_aspects`). A panel indexének ezt
    követnie kell, különben a következő újrarendezés már más képet emelne
    ki — némán."""
    if theme != FRAMEGRID or not 0 <= frame_center < count:
        return frame_center
    return count - 1


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
    "frame_center_after",
    "laid_out",
    "layout_uses_frame_center",
    "node_for",
    "replaced_at",
    "replaced_many",
    "rescattered",
    "scatter",
    "sheet_settings",
    "sources_from_photos",
]
