"""Fájlműveletek: átnevezés, áthelyezés, lomtár, fájlkezelő (#15).

A `.picasa.ini` érintett szekciói minden művelet után round-trip-hűen
(bitre pontosan, a nem értelmezett sorokkal együtt) követik a fájlt.
"""

from .copy import copy_photo
from .move import move_photo
from .rename import RenameItem, preview_name, rename_photo, rename_photos_many
from .reveal import reveal_in_file_manager
from .trash import delete_to_trash

__all__ = [
    "RenameItem",
    "copy_photo",
    "delete_to_trash",
    "move_photo",
    "preview_name",
    "rename_photo",
    "rename_photos_many",
    "reveal_in_file_manager",
]
