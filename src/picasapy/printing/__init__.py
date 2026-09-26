"""Nyomtatás (#32, RÉSZLEGES kör): egyszerű, Picasa-szellemű elrendezés.

A teljes Picasa nyomtatási sablonrendszer (`print.fen`/`reviewprint.fen`,
minden papírmérettel) NEM ebben a körben készül el — az alap kép-illesztő
geometria (`layout.py`), a nyomatméretet CELLÁKÉNT rácsba rendező,
laptörős elrendező (#3647, `grid_layout.py`), és #1590 óta az INDEXKÉP
(több bélyegkép egy lapon, `contact_sheet.py`). Ez a csomag a Qt-független,
determinisztikus geometria-számítást tartalmazza; a tényleges
`QPrinter`/`QPainter`-rajzolás az app-rétegben
(`picasapy.app.print_controller`) történik."""

from .contact_sheet import (
    DEFAULT_COLUMNS,
    ContactSheetPage,
    header_rect,
    rows_per_page,
    sheet_pages,
)
from .grid_layout import (
    GridCell,
    GridPage,
    choose_page_orientation,
    grid_pages,
    page_capacity,
)
from .layout import (
    ImagePlacement,
    PageGeometry,
    PrintFitMode,
    PrintOrientation,
    compute_print_layout,
    resolve_orientation,
)

__all__ = [
    "DEFAULT_COLUMNS",
    "ContactSheetPage",
    "GridCell",
    "GridPage",
    "ImagePlacement",
    "PageGeometry",
    "PrintFitMode",
    "PrintOrientation",
    "choose_page_orientation",
    "compute_print_layout",
    "grid_pages",
    "header_rect",
    "page_capacity",
    "resolve_orientation",
    "rows_per_page",
    "sheet_pages",
]
