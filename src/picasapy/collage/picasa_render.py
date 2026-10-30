"""A Picasa-hű kollázs RAJZOLÓJA — a hat elrendezés és a három keret (#431).

## Miért külön modul

A #431 magja (`pile`, `packing`, `regular_grid`, `contact_sheet`,
`multi_exposure`, `frames`, `rects`, `themes`) elkészült és 214 teszt fedte,
**de senki nem hívta** — a `render.make_collage` a #29-es, SAJÁT TERVEZÉSŰ
négy elrendezésen maradt. A kollázs tehát működött, csak nem a Picasa
elrendezéseivel. Ez a modul köti össze a kettőt: itt fut össze a hat téma,
a keretek és a közös illesztő.

A régi `render.make_collage` egyelőre MEGMARAD (a `.picasa.ini`/API
kompatibilitás miatt), de a felület mostantól ezt hívja.

## Elrendezés ÉS rajzolás — két lépés, egy rajzoló (#942)

A modul **kettéválik**: a téma pakolója `CollageNode` csomópontokat állít
elő (hol, mekkorán, milyen szögben áll egy kép), a rajzoló pedig CSAK
kirajzolja őket. Enélkül a kollázs-panel élő vászna hazudna: a
`make_picasa_collage` mindig újraszámolta az elrendezést, tehát egy kézzel
átrendezett vászon mentéskor visszaugrott volna a gépi elrendezésre.

```
make_picasa_collage ─→ layout_nodes ─→ csomópontok ─┐
render_nodes ─→ (a felülettől kapott csomópontok) ──┴─→ nodes.draw_nodes
```

A `render_nodes` a felület bejárata: MEGADOTT elhelyezésekből rajzol,
elrendezés-számolás nélkül. A csomópont-modell és a közös rajzoló a
`nodes.py`-ban él.

## A hat téma és a hozzájuk tartozó mag

| téma (`.cxf` kulcs) | felületi név | a geometriát adó modul |
|---|---|---|
| `picturepile` | Képkupac | `pile.pile_layout` |
| `picturegrid` | Mozaik | `packing.pack` |
| `framegrid` | Képkockamozaik | `packing.pack` **korláttal** |
| `regulargrid` | Rács | `regular_grid` |
| `contactsheet` | Indexkép | `regular_grid` + fejléc |
| `multiexp` | Többszörös exponálás | `multi_exposure.blend_multi_exposure` |

⚠️ A `themes.py` csapdája itt is él: a felületi „Mozaik" kulcsa
`picturegrid`, a „Rács"-é `regulargrid`. A `.cxf` ezeket írja ki, tehát a
kettő felcserélése olvashatatlan projektfájlt adna.

Bemenet/kimenet: OpenCV **BGR** `uint8` képek (a `render.py` konvenciója).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass  # noqa: F401 - régi modulimportútvonal
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np
from PIL import Image, ImageDraw

from .fitting import MsvcRandom, picasa_round  # noqa: F401 - régi modulimportútvonal
from .frames import POLAROID_HEIGHT_RATIO, POLAROID_WIDTH_RATIO
from .multi_exposure import blend_multi_exposure  # noqa: F401 - régi modulimportútvonal
from .nodes import (  # noqa: F401 - régi modulimportútvonal
    SHEET_UNITS,
    CollageNode,
    border_growth,
    draw_nodes,
    outer_box,
    photo_box,
    pixels_to_sheet,
    sheet_to_pixels,
)
from .location_tree import pack_with_center  # noqa: F401 - régi modulimportútvonal
from .packing import pack  # noqa: F401 - régi modulimportútvonal
from .regular_grid import regular_grid_rects, regular_grid_shape  # noqa: F401 - régi modulimportútvonal
from .render import CollageReport, _decode, fit_to_frame  # noqa: F401 - régi modulimportútvonal
from .shadow import (  # noqa: F401 - régi modulimportútvonal
    ShadowParams,
    shadow_params,
)
from .themes import (  # noqa: F401 - régi modulimportútvonal
    BORDER_THEMES,
    COLLAGE_THEMES,
    THEME_CAPABILITIES,
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    NOBORDER,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
)
from .picasa_render_layouts import (  # noqa: F401 - régi modulimportútvonal
    _ContactSheetGeometry,  # noqa: F401 - régi modulimportútvonal
    _cell_nodes,
    _contact_sheet_band,
    _contact_sheet_geometry,  # noqa: F401 - régi modulimportútvonal
    _contact_sheet_nodes,
    _contact_sheet_position,  # noqa: F401 - régi modulimportútvonal
    _framed_size_inside,  # noqa: F401 - régi modulimportútvonal
    _multi_exposure_nodes,
    _pile_nodes,
    _polaroid_negyzet,  # noqa: F401 - régi modulimportútvonal
    _unicode_font,
    contact_sheet_cell_scale,
)
from .picasa_render_settings import (
    PicasaCollageSettings,
    _DEFAULT_SETTINGS,
    _canvas,
    shadow_for_settings,
)
from .picasa_render_placement import (  # noqa: F401 - régi modulimportútvonal
    _aspects,
    _multiexp_node,
    layout_nodes,
    layout_nodes_for_aspects,
)
from .picasa_render_make import make_picasa_collage

# A régi importútvonal metaadatai is a homlokzathoz kötődnek.
PicasaCollageSettings.__module__ = __name__
for _nev in (
    "_canvas",
    "shadow_for_settings",
    "_aspects",
    "layout_nodes_for_aspects",
    "layout_nodes",
    "_multiexp_node",
    "make_picasa_collage",
):
    globals()[_nev].__module__ = __name__

#: A polaroid csempe RÖGZÍTETT oldalaránya (#1053). Nem új szám: a keret két
#: aránya adja (`1,145 / 1,374 = 0,83333`), és a golden csempéken mérve
#: `0,83313` / `0,83328` — négy tizedesig egyezik. Azért él nevesítve, mert a
#: Képkupacban ez a csempe ALAKJA, nem csak a keret növekménye.
POLAROID_CSEMPE_ARANY = POLAROID_WIDTH_RATIO / POLAROID_HEIGHT_RATIO

logger = logging.getLogger(__name__)

#: A háttérkép TOMPÍTÁSA (`DimmedBitmapTheme`, spec 6.4) — a felület
#: `#26000000` fekete rétege, azaz **38/255** alfa.
BACKGROUND_DIM_ALPHA = 0x26

#: A szorzó, amivel a háttérkép képpontjai halványodnak: `(255 − 38) / 255`.
#:
#: ⚠️ A számot MÉRÉS adja, nem a felületi réteg átvétele. A tulajdonos
#: `AI2.jpg`-jének háttérképe csempeként is szerepel az `AI1.jpg`-ben,
#: tompítás NÉLKÜL — a két előfordulás közvetlenül összevethető:
#:
#: | | 90% | 99% | 99,9% |
#: |---|---:|---:|---:|
#: | csempeként | 255 | 255 | 255 |
#: | háttérként | 77 | **217** | 218 |
#:
#: A telített fehér 217-nél **falba ütközik** (117 646 képpont egyetlen
#: tüskében), és `(255 − 217) / 255 = 0,1490 = 38/255` — bájtra a felületi
#: `#26000000`. A kimenetnek tehát ugyanazt kell tennie, amit az élő
#: előnézet már ma is tesz.
BACKGROUND_DIM_FACTOR = (255 - BACKGROUND_DIM_ALPHA) / 255

_DEFAULT_WIDTH = 1600
_DEFAULT_HEIGHT = 1200

def render_nodes(
    nodes: Sequence[CollageNode],
    settings: PicasaCollageSettings = _DEFAULT_SETTINGS,
) -> CollageReport:
    """A MEGADOTT csomópont-elhelyezésekből rajzol — nem számol elrendezést.

    Ez a kollázs-panel élő vásznának mentő-bejárata (spec 6.5): a
    felhasználó által kézzel átrendezett vászon PONTOSAN úgy kerül a
    kimenetre, ahogy a képernyőn áll. A `make_picasa_collage` ugyanezt a
    rajzolót használja, csak előbb lefuttatja a téma pakolóját — egy
    rajzoló, két hívó.

    A hibás vagy hiányzó képek nem állítják meg a munkát: helykitöltő
    csempeként jelennek meg, és a `CollageReport.missing` / `skipped`
    sorolja fel őket."""
    canvas = _canvas(settings)
    images: list[np.ndarray | None] = []
    used: list[Path] = []
    skipped: list[Path] = []
    reasons: list[str] = []
    missing: list[Path] = []
    for node in nodes:
        path = Path(node.path) if node.path is not None else None
        if path is None:
            images.append(None)
            continue
        if node.missing or not path.exists():
            images.append(None)
            missing.append(path)
            skipped.append(path)
            reasons.append("a fájl nem található")
            continue
        try:
            images.append(_decode(path))
            used.append(path)
        except (ValueError, OSError) as error:
            images.append(None)
            skipped.append(path)
            reasons.append(str(error))

    if settings.theme == CONTACTSHEET:
        # #1273: ez az ÉLŐ vászon és az újraszerkesztés bejárata. Korábban
        # csak a gépi `make_picasa_collage` rajzolta a fejlécet, ezért az a
        # szerkesztés első frissítésekor eltűnt.
        # A fejléc ugyanazt számolja, mint a mentett út: csak a ténylegesen
        # dekódolt képeket. A hiányzó helykitöltő nem lehet „kép” a számban.
        _draw_contact_header(canvas, settings, len(used))
    draw_nodes(
        canvas,
        nodes,
        images,
        settings.width,
        shadow_for_settings(settings, len(nodes)),
        captions=settings.captions,
    )
    return CollageReport(
        image=canvas,
        used=tuple(used),
        skipped=tuple(skipped),
        reasons=tuple(reasons),
        missing=tuple(missing),
        # #960: amit kirajzoltunk, azt jelentjük is — ebből lesz a piszkozat
        nodes=tuple(nodes),
    )


def _draw_contact_header(
    canvas: np.ndarray, settings: PicasaCollageSettings, count: int = 0
) -> int:
    """Az Indexkép fejlécsávja; a felhasznált magasságot adja vissza.

    A `contact_sheet.header_font_size` a betűméretet a lap magasságából és a
    panel oldalarányából számolja; a sáv maga a lap tetején ül.
    """
    from .contact_sheet import (
        CONTACT_SHEET_LEFT_RATIO,
        CONTACT_SHEET_SUBTITLE_OFFSET_RATIO,
        CONTACT_SHEET_SUBTITLE_SIZE_RATIO,
        CONTACT_SHEET_TITLE_TOP_RATIO,
        NARROW_PANEL_FACTOR,
        header_font_size,
        header_lines,
    )

    band = _contact_sheet_band(settings)
    canvas[:band, :] = settings.background
    title, subtitle = header_lines(
        settings.album_title or settings.caption, settings.album_date, count
    )
    panel_aspect = settings.width / settings.height
    meret = header_font_size(settings.height, panel_aspect)
    factor = 1.0 if panel_aspect > 1.0 else NARROW_PANEL_FACTOR
    subtitle_size = max(
        1, picasa_round(factor * CONTACT_SHEET_SUBTITLE_SIZE_RATIO * settings.height)
    )
    # 0x00887aff–0x00887b23: világos háttéren #4A4A4A, sötéten fehér.
    blue, green, red = settings.background
    packed_rgb = (red << 16) | (green << 8) | blue
    color = (255, 255, 255) if packed_rgb < 0x7F7F7F else (74, 74, 74)
    x = picasa_round(settings.width * CONTACT_SHEET_LEFT_RATIO)
    title_top = picasa_round(settings.height * CONTACT_SHEET_TITLE_TOP_RATIO)
    subtitle_top = picasa_round(
        settings.height
        * (CONTACT_SHEET_TITLE_TOP_RATIO + factor * CONTACT_SHEET_SUBTITLE_OFFSET_RATIO)
    )
    # Az OpenCV Hershey-fontja nem Unicode: a „kép" szót „k??p" alakban
    # rajzolná. A Pillow/FreeType ugyanazt háttérszálon, GUI-objektum nélkül
    # és valódi magyar karakterekkel rajzolja.
    header_rgb = cv2.cvtColor(canvas[:band], cv2.COLOR_BGR2RGB)
    image = Image.fromarray(header_rgb)
    draw = ImageDraw.Draw(image)
    if title:
        draw.text((x, title_top), title, font=_unicode_font(meret), fill=color)
    draw.text(
        (x, subtitle_top), subtitle, font=_unicode_font(subtitle_size), fill=color
    )
    canvas[:band] = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    return band


__all__ = [
    "SHEET_UNITS",
    "CollageNode",
    "PicasaCollageSettings",
    "border_growth",
    "contact_sheet_cell_scale",
    "layout_nodes",
    "layout_nodes_for_aspects",
    "make_picasa_collage",
    "outer_box",
    "photo_box",
    "pixels_to_sheet",
    "render_nodes",
    "shadow_for_settings",
    "sheet_to_pixels",
]
