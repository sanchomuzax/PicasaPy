"""A régi fotóművelet-modul stabil belső patchpontjai (#6023)."""

from __future__ import annotations

from picasapy.ini import FilterWriteError, IniConflictError, IniSaveError

RENAME_USE_DATE_KEY = "RenameUseDate"
RENAME_USE_SIZE_KEY = "RenameUseSize"

_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError, FilterWriteError)


def update_document(path, mutate, backup=True):
    """Az ini-írót futáskor a régi modul patchpontjáról veszi."""
    from . import photo_ops_controller

    return photo_ops_controller.update_document(path, mutate, backup=backup)


def rename_sample_constants():
    """A tesztek által is cserélhető átnevezési mintákat olvassa."""
    from . import photo_ops_controller

    return (
        photo_ops_controller.RENAME_SAMPLE_DATE,
        photo_ops_controller.RENAME_SAMPLE_SIZE,
        photo_ops_controller.RENAME_SAMPLE_EXTENSION,
    )
