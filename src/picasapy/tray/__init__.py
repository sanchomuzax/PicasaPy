"""Képtálca (Picture Tray, `scratch`) — a felület-független állapotmag.

A csomag a `model` modul teljes felületét újraexportálja, hogy a hívók
`from picasapy import tray` után `tray.with_selection(...)` alakban
dolgozhassanak. A részletes indoklás a `model.py` docstringjében.
"""

from picasapy.tray.model import (
    EMPTY,
    TrayAlbumToken,
    TrayEntry,
    TrayItem,
    TrayState,
    album_tokens,
    cleared,
    contains,
    held_ids,
    is_held,
    needs_old_items_prompt,
    photo_ids,
    unused_ids,
    used_ids,
    with_album_token,
    with_hold,
    with_remembered_count,
    with_selection,
    with_used,
    without,
    without_album_token,
)

__all__ = [
    "EMPTY",
    "TrayAlbumToken",
    "TrayEntry",
    "TrayItem",
    "TrayState",
    "album_tokens",
    "cleared",
    "contains",
    "held_ids",
    "is_held",
    "needs_old_items_prompt",
    "photo_ids",
    "unused_ids",
    "used_ids",
    "with_album_token",
    "with_hold",
    "with_remembered_count",
    "with_selection",
    "with_used",
    "without",
    "without_album_token",
]
