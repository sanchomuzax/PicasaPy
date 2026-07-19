"""Fájlműveletek: átnevezés, áthelyezés, lomtár, fájlkezelő (#15).

A `.picasa.ini` érintett szekciói minden művelet után round-trip-hűen
(bitre pontosan, a nem értelmezett sorokkal együtt) követik a fájlt.
"""

from .move import move_photo
from .rename import rename_photo
from .reveal import reveal_in_file_manager
from .trash import delete_to_trash

__all__ = [
    "delete_to_trash",
    "move_photo",
    "rename_photo",
    "reveal_in_file_manager",
]
