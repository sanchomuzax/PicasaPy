"""A Picasa-kollázs elrendezéseinek csomóponttá alakítása."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import numpy as np

from .fitting import MsvcRandom
from .location_tree import pack_with_center
from .nodes import SHEET_UNITS, CollageNode
from .picasa_render_layouts import (
    _cell_nodes,
    _contact_sheet_nodes,
    _multi_exposure_nodes,
    _pile_nodes,
)
from .packing import pack
from .regular_grid import regular_grid_rects, regular_grid_shape
from .themes import (
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    NOBORDER,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
)
from .picasa_render_settings import PicasaCollageSettings, _DEFAULT_SETTINGS

def _aspects(images: list[np.ndarray]) -> list[float]:
    return [image.shape[1] / image.shape[0] for image in images]


def layout_nodes_for_aspects(
    aspects: Sequence[float],
    paths: Sequence[Path],
    settings: PicasaCollageSettings = _DEFAULT_SETTINGS,
) -> list[CollageNode]:
    """MIND A HAT téma pakolója, a képek OLDALARÁNYÁBÓL (#989).

    Ez a kollázs elrendezésének **egyetlen** forrása: innen tölti fel a
    vásznát a kollázs-panel, és ezt futtatja a `make_picasa_collage` is a
    rajzolás előtt. Aki két pakoló-utat épít, előbb-utóbb azt kapja, hogy a
    mentett kép mást mutat, mint a vászon (spec 6.5).

    Miért oldalarány és nem kép: a panel a képeket **nem dekódolja** (350
    képnél nem is tehetné) — az indexből csak az arányt ismeri. A rajzolónak
    van dekódolt képe, abból a `layout_nodes` számol arányt. A geometria
    egyik esetben sem függ a forrás abszolút képpontméretétől
    (`fitting.fit_aspect_inside`).

    | téma | a geometriát adó mag |
    |---|---|
    | `picturepile` | `pile.pile_layout` |
    | `picturegrid` | `packing.pack` |
    | `framegrid` | `packing.pack` + a hangsúlyos kép a középső területre |
    | `regulargrid` | `regular_grid` |
    | `contactsheet` | `regular_grid` a fejlécsáv ALATT |
    | `multiexp` | a közös illesztő: mindenki a teljes lapra, középre |

    A keret és a térköz a téma KÉPESSÉG-MASZKJÁN át hat (`effective_border`,
    `effective_spacing`) — témánkénti `if` sem itt, sem a felületen nem
    születik.
    """
    if len(aspects) != len(paths):
        raise ValueError("Minden képhez tartoznia kell útvonalnak.")
    if not aspects:
        return []
    if settings.theme == PICTUREPILE:
        return _pile_nodes(aspects, paths, settings)
    if settings.theme == MULTIEXP:
        return _multi_exposure_nodes(aspects, paths, settings)
    if settings.theme == CONTACTSHEET:
        nodes, _, _ = _contact_sheet_nodes(aspects, paths, settings)
        return nodes
    if settings.theme in (PICTUREGRID, FRAMEGRID):
        rogzitett = (
            settings.frame_center
            if settings.theme == FRAMEGRID
            and settings.frame_center is not None
            and 0 <= settings.frame_center < len(aspects)
            else None
        )
        if rogzitett is None:
            # nincs rögzített kép → az EREDETI IS az alap pakolóra esik vissza
            rects = pack(
                list(aspects),
                settings.width / settings.height,
                MsvcRandom(settings.seed),
            )
            return _cell_nodes(paths, rects, settings)
        #: #916: a hangsúlyos kép a MÉRT cellát kapja (`0x00889185`), a
        #: többi a maradék sávokra — a `CLocationTree` pakolója.
        rects = pack_with_center(
            list(aspects),
            settings.width / settings.height,
            MsvcRandom(settings.seed),
            center=rogzitett,
        )
        #: a hangsúlyos kép LEGFELÜL: a lista VÉGÉN áll, hogy a rajzoló ne
        #: takarja el a köré pakolt csempékkel
        sorrend = [i for i in range(len(aspects)) if i != rogzitett] + [rogzitett]
        nodes = _cell_nodes(
            [paths[i] for i in sorrend],
            tuple(rects[i] for i in sorrend),
            settings,
        )
        return nodes
    if settings.theme == REGULARGRID:
        sorok, oszlopok = regular_grid_shape(
            list(aspects), settings.width, settings.height
        )
        rects = regular_grid_rects(len(aspects), sorok, oszlopok)
        return _cell_nodes(paths, rects, settings)
    raise ValueError(
        f"Ehhez a témához nincs csomópont-elrendezés: {settings.theme!r}"
    )


def layout_nodes(
    images: Sequence[np.ndarray],
    paths: Sequence[Path],
    settings: PicasaCollageSettings = _DEFAULT_SETTINGS,
) -> list[CollageNode]:
    """A téma pakolója DEKÓDOLT képekből — a `make_picasa_collage` első fele.

    Csak annyit tesz, hogy a képekből oldalarányt számol, és átadja a
    `layout_nodes_for_aspects`-nek; a geometria egyetlen helyen él.
    """
    if len(images) != len(paths):
        raise ValueError("Minden képhez tartoznia kell útvonalnak.")
    return layout_nodes_for_aspects(_aspects(list(images)), paths, settings)


def _multiexp_node(path: Path, settings: PicasaCollageSettings) -> CollageNode:
    """A Többszörös exponálás egyetlen csomópont-alakja (#1248).

    Mérve az `AI7.cxf`-en: `x=0 y=0 w=1 h=1 theta=0`, `noborder` — vagyis
    minden kép a TELJES lapot fedi. Lapegységben ez a lap közepén álló,
    lap méretű doboz."""
    lap_magassag = SHEET_UNITS * settings.height / settings.width
    return CollageNode(
        path=str(path),
        center_x=SHEET_UNITS / 2.0,
        center_y=lap_magassag / 2.0,
        width=SHEET_UNITS,
        height=lap_magassag,
        theta=0.0,
        border=NOBORDER,
        fill=False,
    )

