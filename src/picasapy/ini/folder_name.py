"""A fizikai mappa neve a `.picasa.ini` `[Picasa]` szekciójában."""

from __future__ import annotations

from .document import IniDocument

_FOLDER_SECTION = "Picasa"
_NAME_KEY = "name"


def with_folder_name(document: IniDocument, name: str) -> IniDocument:
    """Új dokumentum a mappa `[Picasa]/name` értékével."""
    return document.with_value(_FOLDER_SECTION, _NAME_KEY, name)
