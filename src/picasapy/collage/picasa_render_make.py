"""A Picasa-hű kollázskép összeállítása."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .multi_exposure import blend_multi_exposure
from .nodes import CollageNode, draw_nodes
from .picasa_render_layouts import _contact_sheet_nodes
from .picasa_render_placement import _aspects, _multiexp_node, layout_nodes
from .picasa_render_settings import (
    PicasaCollageSettings,
    _DEFAULT_SETTINGS,
    _canvas,
    shadow_for_settings,
)
from .render import CollageReport, _decode
from .themes import CONTACTSHEET, MULTIEXP


def _header_from_facade(canvas, settings, count=0):
    from . import picasa_render

    return picasa_render._draw_contact_header(canvas, settings, count)


_draw_contact_header = _header_from_facade

def make_picasa_collage(
    sources, settings: PicasaCollageSettings = _DEFAULT_SETTINGS
) -> CollageReport:
    """Picasa-hű kollázs a hat téma egyikével.

    A hibás/hiányzó források kimaradnak, nem állítják meg a munkát — a hívó
    a `CollageReport.used` üres voltából látja, ha nincs mit menteni (ez a
    `render.make_collage` viselkedése, szándékosan azonos).
    """
    paths = [Path(s) for s in sources]
    if not paths:
        raise ValueError("Kollázshoz legalább egy kép kell.")

    decoded: list[np.ndarray] = []
    used: list[Path] = []
    skipped: list[Path] = []
    reasons: list[str] = []
    missing: list[Path] = []
    for path in paths:
        if not path.exists():
            missing.append(path)
            skipped.append(path)
            reasons.append("a fájl nem található")
            continue
        try:
            decoded.append(_decode(path))
            used.append(path)
        except (ValueError, OSError) as error:
            skipped.append(path)
            reasons.append(str(error))

    canvas = _canvas(settings)
    if not decoded:
        return CollageReport(
            image=canvas,
            used=(),
            skipped=tuple(skipped),
            reasons=tuple(reasons),
            missing=tuple(missing),
        )

    # #960: a kirajzolt csomópontok — a `.cxf` piszkozat egyetlen hiteles
    # forrása. A Többszörös exponálás sem kivétel (#1248): geometriát nem
    # ad, a FORRÁSKÉPEK listáját viszont neki is ki kell adnia.
    rajzolt: tuple[CollageNode, ...] = ()
    if settings.theme == MULTIEXP:
        # A Többszörös exponálás nem HELYEZ el képeket, hanem egymásra keveri
        # őket — ezért nem a közös rajzolón megy át. A képesség-maszkja is
        # ezt mondja: se kijelölés, se keret, se háttér.
        canvas = blend_multi_exposure(
            decoded, settings.width, settings.height, settings.background
        )
        # ⚠️ #1248: a csomópontok ettől függetlenül KELLENEK. A geometria
        # tényleg nem hordoz információt, a `.cxf`-nek viszont tudnia kell,
        # MELYIK képekből készült a kollázs — enélkül az újraszerkesztés
        # fekete lapot ad, és a mentés azt jelenti, hogy „az összes képet
        # eltávolították" (a tulajdonos jelentése, v0.8.45).
        #
        # Az alak MÉRVE (`referencia/kollazs-golden/AI7.cxf`, valódi
        # Picasa-minta): képenként EGY csomópont, mind a TELJES lapon,
        # forgatás és keret nélkül.
        rajzolt = tuple(_multiexp_node(ut, settings) for ut in used)
    elif settings.theme == CONTACTSHEET:
        # Ugyanez a teljes-lapos csomópontlista megy az élő vászonra és a
        # mentésbe; ettől a szerkesztés közbeni frissítés nem válhat el.
        _draw_contact_header(canvas, settings, len(decoded))
        nodes, _, alsobeallitas = _contact_sheet_nodes(
            _aspects(decoded), used, settings
        )
        draw_nodes(
            canvas,
            nodes,
            decoded,
            alsobeallitas.width,
            shadow_for_settings(settings, len(decoded)),
            captions=settings.captions,
        )
        rajzolt = tuple(nodes)
    else:
        nodes = layout_nodes(decoded, used, settings)
        draw_nodes(
            canvas,
            nodes,
            decoded,
            settings.width,
            shadow_for_settings(settings, len(decoded)),
            captions=settings.captions,
        )
        rajzolt = tuple(nodes)

    return CollageReport(
        image=canvas,
        used=tuple(used),
        skipped=tuple(skipped),
        reasons=tuple(reasons),
        missing=tuple(missing),
        nodes=rajzolt,
    )

