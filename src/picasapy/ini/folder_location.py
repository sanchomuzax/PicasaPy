"""A fizikai mappa helye a `.picasa.ini` `[Picasa]` szekciójában."""

from __future__ import annotations

from .document import IniDocument, Section

_FOLDER_SECTION = "Picasa"
_LOCATION_KEY = "location"


def read_folder_location(document: IniDocument) -> str:
    """A mappa `[Picasa]/location` értéke, vagy üres szöveg."""
    section: Section | None = document.section(_FOLDER_SECTION)
    return (section.get(_LOCATION_KEY) if section else None) or ""


def with_folder_location(document: IniDocument, location: str) -> IniDocument:
    """A mappa `[Picasa]/location` értékének módosítása.

    Az üres vagy csak whitespace érték törli a kulcsot. Más `[Picasa]`
    adatot és az INI eredeti formázását a dokumentum API őrzi meg.
    """
    value = (location or "").strip()
    if value:
        return document.with_value(_FOLDER_SECTION, _LOCATION_KEY, value)
    return document.with_removed(_FOLDER_SECTION, _LOCATION_KEY)
