"""Szerkesztési-lánc állapotkezelő + nem-destruktív mentés (#21)."""

from picasapy.edit.save import (
    ORIGINALS_DIR_NAME,
    RevertResult,
    SaveError,
    SaveResult,
    revert,
    save_edited,
)
from picasapy.edit.session import EditSession

__all__ = [
    "ORIGINALS_DIR_NAME",
    "EditSession",
    "RevertResult",
    "SaveError",
    "SaveResult",
    "revert",
    "save_edited",
]
