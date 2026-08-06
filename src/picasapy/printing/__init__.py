"""Nyomtatás (#32, RÉSZLEGES kör): egyszerű, Picasa-szellemű elrendezés.

A teljes Picasa nyomtatási sablonrendszer (`print.fen`/`reviewprint.fen`,
kontaktlap, több kép egy oldalon) NEM ebben a körben készül el — csak az
alap "teljes oldal / oldalhoz igazítva" elrendezés, képenként egy oldal.
Ez a csomag a Qt-független, determinisztikus geometria-számítást
tartalmazza (`layout.py`); a tényleges `QPrinter`/`QPainter`-rajzolás az
app-rétegben (`picasapy.app.print_controller`) történik."""

from .layout import (
    ImagePlacement,
    PageGeometry,
    PrintFitMode,
    PrintOrientation,
    compute_print_layout,
    resolve_orientation,
)

__all__ = [
    "ImagePlacement",
    "PageGeometry",
    "PrintFitMode",
    "PrintOrientation",
    "compute_print_layout",
    "resolve_orientation",
]
