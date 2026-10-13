"""Kollázs-készítés — elrendezés (`layout`) és renderelés (`render`).

A Picasa-hű réteg a `themes`, `fitting`, `frames`, `rects`, `regular_grid`
és `pile` modulokban él. Ezek a `docs/specs/picasa-create-features.md`
képleteit követik, míg a régi `layout`/`render` réteg a korábbi, saját
tervezésű változat.

A két réteg névütközése miatt a Picasa-hű Képkupac nem látszik a csomag
gyökerében: a régi `layout.pile_layout` helyett a
`picasapy.collage.pile.pile_layout` útvonalat kell használni.

A publikus függvények és típusok csak kéréskor töltődnek be, így egy másik
funkció importja nem húzza be a teljes kollázs-csomagot.
"""

from __future__ import annotations

from importlib import import_module

# A két réteg névütközése miatt a Picasa-hű Képkupac továbbra is csak a
# saját moduljából érhető el: ``picasapy.collage.pile.pile_layout``.
_EXPORT_MODULES = {
    "contact_sheet": ("header_font_size",),
    "autosave": (
        "AUTOSAVE_NAME",
        "autosave_path",
        "discard_autosave",
        "has_recoverable_draft",
        "recover_orphan_draft",
        "read_autosave",
        "write_autosave",
    ),
    "cxf": ("CxfBackground", "CxfNode", "CxfProject", "read_cxf", "write_cxf"),
    "draft_state": ("draft_project_path", "is_draft_image"),
    "fitting": ("MsvcRandom", "fit_inside", "msvc_uniform01", "picasa_round"),
    "frames": (
        "PolaroidGeometry",
        "apply_border",
        "dim_for_background",
        "polaroid_geometry",
        "white_border_width",
    ),
    "layout": (
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
    ),
    "pile": ("PilePlacement", "pile_scale", "pile_size", "scatter_centers"),
    "multi_exposure": ("blend_multi_exposure", "multi_exposure_size"),
    "packing": ("PackNode", "pack", "packing_cost"),
    "rects": ("NormRect", "PixelRect", "to_pixel_rects"),
    "regular_grid": ("regular_grid_rects", "regular_grid_shape"),
    "render": (
        "CollageReport",
        "CollageSettings",
        "fit_to_frame",
        "make_collage",
        "write_collage",
    ),
    "themes": (
        "BORDER_THEMES",
        "COLLAGE_THEMES",
        "CONTACTSHEET",
        "FRAMEGRID",
        "MULTIEXP",
        "NOBORDER",
        "PICTUREGRID",
        "PICTUREPILE",
        "POLAROID",
        "REGULARGRID",
        "WHITEBORDER",
    ),
}

_NAME_TO_MODULE = {
    name: module_name
    for module_name, names in _EXPORT_MODULES.items()
    for name in names
}
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
    "recover_orphan_draft",
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


def __getattr__(name: str):
    """A csomag publikus API-ját csak a kért funkció betöltésekor oldja fel."""
    module_name = _NAME_TO_MODULE.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(f".{module_name}", __name__), name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
