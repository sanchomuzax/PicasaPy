"""Nyomtatás (#32, RÉSZLEGES kör): egyszerű, Picasa-szellemű elrendezés.

A teljes Picasa nyomtatási sablonrendszer (`print.fen`/`reviewprint.fen`,
minden papírmérettel) NEM ebben a körben készül el — az alap „teljes oldal
/ oldalhoz igazítva" elrendezés (képenként egy oldal, `layout.py`), és
#1590 óta az INDEXKÉP (több bélyegkép egy lapon, `contact_sheet.py`). Ez a
csomag a Qt-független, determinisztikus geometria-számítást tartalmazza; a
tényleges `QPrinter`/`QPainter`-rajzolás az app-rétegben
(`picasapy.app.print_controller`) történik."""

from .contact_sheet import (
    DEFAULT_COLUMNS,
    ContactSheetPage,
    header_rect,
    rows_per_page,
    sheet_pages,
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
    "ImagePlacement",
    "PageGeometry",
    "PrintFitMode",
    "PrintOrientation",
    "compute_print_layout",
    "header_rect",
    "resolve_orientation",
    "rows_per_page",
    "sheet_pages",
]
