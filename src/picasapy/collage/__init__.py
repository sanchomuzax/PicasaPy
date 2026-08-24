"""Kollázs-készítés — elrendezés (`layout`) + renderelés (`render`).

A #431 óta épül mellé a Picasa-hű réteg is: `themes` (a kilenc téma-kulcs),
`fitting` (a közös illesztő és az MSVC-véletlen), `frames` (a három
képkeret), `rects` + `regular_grid` (a térköz és a Rács), `pile` (a
Képkupac). Ezek a `docs/specs/picasa-create-features.md` 1.9 szakaszának
dekompilált képleteit követik, míg a régi `layout`/`render` a #29-es, saját
tervezésű változat — a kettő egyelőre párhuzamosan él.

⚠️ A két réteg **névütközése** miatt a Picasa-hű Képkupac NEM látszik a
csomag gyökerében: `layout.pile_layout` a régi, `pile.pile_layout` az új.
Az újat mindig a saját moduljából kell behozni:
`from picasapy.collage.pile import pile_layout`.
"""

from .contact_sheet import header_font_size
from .autosave import (
    AUTOSAVE_NAME,
    autosave_path,
    discard_autosave,
    has_recoverable_draft,
    read_autosave,
    write_autosave,
)
from .cxf import CxfBackground, CxfNode, CxfProject, read_cxf, write_cxf
from .draft_state import draft_project_path, is_draft_image
from .fitting import MsvcRandom, fit_inside, msvc_uniform01, picasa_round
from .frames import (
    PolaroidGeometry,
    apply_border,
    dim_for_background,
    polaroid_geometry,
    white_border_width,
)
from .layout import (
    COLLAGE_KINDS,
    CONTACT_SHEET,
    GRID,
    MOSAIC,
    PILE,
    Placement,
    contact_sheet_layout,
    grid_layout,
    grid_shape,
    layout_for,
    mosaic_layout,
    pile_layout,
)
from .pile import PilePlacement, pile_scale, pile_size, scatter_centers
from .multi_exposure import blend_multi_exposure, multi_exposure_size
from .packing import PackNode, pack, packing_cost
from .rects import NormRect, PixelRect, to_pixel_rects
from .regular_grid import regular_grid_rects, regular_grid_shape
from .render import (
    CollageReport,
    CollageSettings,
    fit_to_frame,
    make_collage,
    write_collage,
)
from .themes import (
    BORDER_THEMES,
    COLLAGE_THEMES,
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    NOBORDER,
    PICTUREGRID,
    PICTUREPILE,
    POLAROID,
    REGULARGRID,
    WHITEBORDER,
)

__all__ = [
    "BORDER_THEMES",
    "PackNode",
    "pack",
    "packing_cost",
    "blend_multi_exposure",
    "header_font_size",
    "multi_exposure_size",
    "CxfBackground",
    "CxfNode",
    "CxfProject",
    "AUTOSAVE_NAME",
    "autosave_path",
    "discard_autosave",
    "draft_project_path",
    "has_recoverable_draft",
    "is_draft_image",
    "read_autosave",
    "read_cxf",
    "write_autosave",
    "write_cxf",
    "PilePlacement",
    "pile_scale",
    "pile_size",
    "scatter_centers",
    "NormRect",
    "PixelRect",
    "regular_grid_rects",
    "regular_grid_shape",
    "to_pixel_rects",
    "COLLAGE_THEMES",
    "CONTACTSHEET",
    "FRAMEGRID",
    "MULTIEXP",
    "MsvcRandom",
    "NOBORDER",
    "PICTUREGRID",
    "PICTUREPILE",
    "POLAROID",
    "PolaroidGeometry",
    "REGULARGRID",
    "WHITEBORDER",
    "apply_border",
    "dim_for_background",
    "fit_inside",
    "msvc_uniform01",
    "picasa_round",
    "polaroid_geometry",
    "white_border_width",
    "COLLAGE_KINDS",
    "CONTACT_SHEET",
    "GRID",
    "MOSAIC",
    "PILE",
    "Placement",
    "contact_sheet_layout",
    "grid_layout",
    "grid_shape",
    "layout_for",
    "mosaic_layout",
    "pile_layout",
    "CollageReport",
    "CollageSettings",
    "fit_to_frame",
    "make_collage",
    "write_collage",
]
