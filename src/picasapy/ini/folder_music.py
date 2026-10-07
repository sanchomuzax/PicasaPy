"""A mappa diavetítés- és filmzenéje a `.picasa.ini`-ben (#4448)."""

from __future__ import annotations

from .document import IniDocument, Section


def _logikai(ertek: str | None) -> bool:
    return (ertek or "").strip().casefold() in {"1", "true", "yes", "on"}


def read_music_settings(
    document: IniDocument, section_name: str
) -> tuple[bool, str]:
    """A `usemusic` és `music` mező egy szekcióból; a hiányzó zene ki."""
    section: Section | None = document.section(section_name)
    if section is None:
        return False, ""
    return _logikai(section.get("usemusic")), section.get("music") or ""


def with_music_settings(
    document: IniDocument,
    section_name: str,
    *,
    use_music: bool | None = None,
    music_file: str | None = None,
) -> IniDocument:
    """Zene-beállítások írása egy INI-szekcióba.

    A `None` változatlanul hagyja az adott mezőt. Bekapcsolt jelölőnégyzethez
    `usemusic=1` kerül; kikapcsoláskor a kulcs törlődik. Üres fájlútvonal a
    korábbi `music` kulcsot törli.
    """
    result = document
    if use_music is not None:
        if use_music:
            result = result.with_value(section_name, "usemusic", "1")
        else:
            result = result.with_removed(section_name, "usemusic")

    if music_file is not None:
        if music_file.strip():
            result = result.with_value(section_name, "music", music_file)
        else:
            result = result.with_removed(section_name, "music")
    return result


def read_folder_music(document: IniDocument) -> tuple[bool, str]:
    """A fizikai mappa `[Picasa]` zene-beállítása."""
    return read_music_settings(document, "Picasa")


def with_folder_music(
    document: IniDocument, use_music: bool, music_file: str
) -> IniDocument:
    """A fizikai mappa `[Picasa]` zene-beállításának módosítása."""
    return with_music_settings(
        document, "Picasa", use_music=use_music, music_file=music_file
    )
