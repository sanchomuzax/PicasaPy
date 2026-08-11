"""Szerkesztési-lánc állapotkezelő + nem-destruktív mentés (#21)."""

from picasapy.edit.save import (
    ORIGINALS_DIR_NAME,
    RevertResult,
    SaveError,
    SaveResult,
    UndoSaveResult,
    revert,
    save_edited,
    undo_save,
)
from picasapy.edit.session import EditSession

__all__ = [
    "ORIGINALS_DIR_NAME",
    "EditSession",
    "RevertResult",
    "SaveError",
    "SaveResult",
    "UndoSaveResult",
    "revert",
    "save_edited",
    "undo_save",
]
