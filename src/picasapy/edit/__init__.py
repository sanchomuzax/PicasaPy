"""Szerkesztési-lánc állapotkezelő + nem-destruktív mentés (#21)."""

from picasapy.edit.save import (
    LEGACY_ORIGINALS_DIR_NAME,
    ORIGINALS_DIR_NAME,
    ORIGINALS_DIR_NAMES,
    SNAPSHOT_DIR_NAME,
    RevertResult,
    SaveError,
    SaveResult,
    UndoSaveResult,
    find_original_backup,
    revert,
    save_edited,
    undo_save,
)
from picasapy.edit.session import EditSession

__all__ = [
    "LEGACY_ORIGINALS_DIR_NAME",
    "ORIGINALS_DIR_NAME",
    "ORIGINALS_DIR_NAMES",
    "SNAPSHOT_DIR_NAME",
    "EditSession",
    "RevertResult",
    "SaveError",
    "SaveResult",
    "UndoSaveResult",
    "find_original_backup",
    "revert",
    "save_edited",
    "undo_save",
]
