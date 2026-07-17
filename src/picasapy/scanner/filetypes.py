"""Picasa-kompatibilis médiatípus-felismerés kiterjesztés alapján.

Forrás: Picasa 3.9 hivatalos támogatott-formátum lista (NotebookLM notebook,
Picasa help). A WebP szándékosan hiányzik — a Picasa nem támogatta; felvétele
későbbi, tudatos bővítés lehet.
"""

from __future__ import annotations

from pathlib import PurePath

PHOTO_EXTENSIONS = frozenset(
    {".jpeg", ".jpg", ".tif", ".tiff", ".bmp", ".gif", ".psd", ".png", ".tga"}
)

RAW_EXTENSIONS = frozenset(
    {
        ".3fr", ".arw", ".cr2", ".crw", ".dcr", ".dng", ".kdc", ".mrw",
        ".nef", ".nrw", ".orf", ".pef", ".raf", ".raw", ".rw2", ".sr2",
        ".srf", ".x3f",
    }
)

VIDEO_EXTENSIONS = frozenset(
    {
        ".3g2", ".3gp", ".asf", ".avi", ".divx", ".m2t", ".m2ts", ".m4v",
        ".mkv", ".mmv", ".mod", ".mov", ".mp4", ".mpg", ".mts", ".tod",
        ".wmv",
    }
)


def media_kind_of(name: str) -> str | None:
    """'photo' / 'raw' / 'video', vagy None, ha nem Picasa-média."""
    extension = PurePath(name).suffix.lower()
    if extension in PHOTO_EXTENSIONS:
        return "photo"
    if extension in RAW_EXTENSIONS:
        return "raw"
    if extension in VIDEO_EXTENSIONS:
        return "video"
    return None
