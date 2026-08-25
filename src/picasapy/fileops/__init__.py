"""Fájlműveletek: átnevezés, áthelyezés, lomtár, fájlkezelő (#15).

A `.picasa.ini` érintett szekciói minden művelet után round-trip-hűen
(bitre pontosan, a nem értelmezett sorokkal együtt) követik a fájlt.
"""

from .batch import (
    RENAME,
    SKIP,
    BatchResult,
    conflicting_names,
    copy_photos,
    move_photos,
)
from .copy import copy_photo
from .diskspace import has_enough_free_space, required_bytes_for
from .move import move_photo
from .move_folder import FolderMoveError, move_folder
from .originals import (
    OriginalMove,
    move_preserved_originals,
    originals_follow,
    originals_slot_free,
    plan_original_moves,
    undo_original_moves,
)
from .rename import RenameItem, preview_name, rename_photo, rename_photos_many
from .reveal import open_folder_in_file_manager, reveal_in_file_manager
from .trash import (
    TrashUnavailableError,
    delete_permanently,
    delete_to_trash,
    find_trash_dir,
    trash_available,
)
from .writable import is_folder_writable

__all__ = [
    "RENAME",
    "SKIP",
    "BatchResult",
    "OriginalMove",
    "RenameItem",
    "TrashUnavailableError",
    "conflicting_names",
    "copy_photo",
    "copy_photos",
    "delete_permanently",
    "delete_to_trash",
    "find_trash_dir",
    "has_enough_free_space",
    "is_folder_writable",
    "FolderMoveError",
    "move_folder",
    "move_photo",
    "move_photos",
    "move_preserved_originals",
    "originals_follow",
    "originals_slot_free",
    "plan_original_moves",
    "preview_name",
    "rename_photo",
    "rename_photos_many",
    "open_folder_in_file_manager",
    "required_bytes_for",
    "reveal_in_file_manager",
    "trash_available",
    "undo_original_moves",
]
