"""A PicasaPy személyalbum-borítójának `.picasa.ini` kiterjesztése.

A Picasa formátumában nem találtunk dokumentált, személyenkénti borítómezőt.
Ezért a PicasaPy a saját `[PicasaPy]` szekciójában tárolja a nevet és a
képmappa-relatív fájlnevet. A dokumentummodell ismeretlen adatainak
round-trip szabálya a többi szekciót változatlanul megőrzi.
"""

from __future__ import annotations

from picasapy.ini.document import IniDocument

_SECTION = "PicasaPy"
_KEY_PREFIX = "person_album_thumbnail_"


def _validated_person_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("A személy neve nem lehet üres.")
    return name.casefold()


def _key_for_name(name: str) -> str:
    normalized = _validated_person_name(name)
    encoded = normalized.encode("utf-8").hex()
    return f"{_KEY_PREFIX}{encoded}"


def _valid_photo_name(photo_name: str) -> bool:
    return (
        isinstance(photo_name, str)
        and bool(photo_name)
        and photo_name not in {".", ".."}
        and "/" not in photo_name
        and "\\" not in photo_name
        and "\x00" not in photo_name
    )


def set_person_album_thumbnail(
    document: IniDocument, person_name: str, photo_name: str
) -> IniDocument:
    """Beállítja a személy borítóját a képmappán belüli fájlnévvel.

    A személynév kisbetűtől független kulcsba kerül, a fájlnév pedig nem
    tartalmazhat útvonalat: a borító mindig ugyanabban a mappában van, mint
    az ezt tároló `.picasa.ini`.
    """
    key = _key_for_name(person_name)
    if not _valid_photo_name(photo_name):
        raise ValueError("A borítóképnek képmappán belüli fájlnévnek kell lennie.")
    cleaned = clear_person_album_thumbnail(document, person_name)
    return cleaned.with_value(_SECTION, key, photo_name)


def clear_person_album_thumbnail(
    document: IniDocument, person_name: str
) -> IniDocument:
    """Eltávolítja a személy PicasaPy-borítóját, más adatot nem módosítva."""
    key = _key_for_name(person_name)
    result = document
    section = result.section(_SECTION)
    while section is not None and section.get(key) is not None:
        result = result.with_removed(_SECTION, key)
        section = result.section(_SECTION)
    return result


def person_album_thumbnails(document: IniDocument) -> dict[str, str]:
    """Visszaadja a biztonságos, képmappán belüli borítóhivatkozásokat."""
    section = document.section(_SECTION)
    if section is None:
        return {}

    result: dict[str, str] = {}
    for key, photo_name in section.items():
        folded_key = key.casefold()
        if not folded_key.startswith(_KEY_PREFIX):
            continue
        encoded_name = folded_key[len(_KEY_PREFIX):]
        try:
            person_name = bytes.fromhex(encoded_name).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            continue
        if not person_name or not _valid_photo_name(photo_name):
            continue
        result[person_name] = photo_name
    return result


__all__ = [
    "clear_person_album_thumbnail",
    "person_album_thumbnails",
    "set_person_album_thumbnail",
]
