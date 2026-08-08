"""Fájlműveletek: átnevezés, áthelyezés, lomtár, fájlkezelő (#15).

A `.picasa.ini` érintett szekciói minden művelet után round-trip-hűen
(bitre pontosan, a nem értelmezett sorokkal együtt) követik a fájlt.
"""

from .copy import copy_photo
from .move import move_photo
from .rename import RenameItem, preview_name, rename_photo, rename_photos_many
from .reveal import open_folder_in_file_manager, reveal_in_file_manager
from .trash import (
    TrashUnavailableError,
    delete_permanently,
    delete_to_trash,
    find_trash_dir,
    trash_available,
)

__all__ = [
    "RenameItem",
    "TrashUnavailableError",
    "copy_photo",
    "delete_permanently",
    "delete_to_trash",
    "find_trash_dir",
    "move_photo",
    "preview_name",
    "rename_photo",
    "rename_photos_many",
    "open_folder_in_file_manager",
    "reveal_in_file_manager",
    "trash_available",
]
