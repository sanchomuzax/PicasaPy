"""Virtuális albumok: `[.album:<token>]` szekciók és az `albums=` CSV kulcs.

Figyelem: a parse→serialize normalizál (üres tokeneket elhagy), a byte-pontos
megőrzést a document-réteg adja — nem módosított `albums=` értéket nem szabad
ezen a modulon átengedni.
"""

from __future__ import annotations

from dataclasses import dataclass

from .document import ALBUM_SECTION_PREFIX, IniDocument


@dataclass(frozen=True)
class Album:
    token: str
    name: str | None
    date: str | None
    description: str | None
    location: str | None


def parse_album_refs(value: str) -> tuple[str, ...]:
    """Az `albums=` kulcs token-listája."""
    return tuple(token for token in value.split(",") if token)


def serialize_album_refs(refs: tuple[str, ...]) -> str:
    return ",".join(refs)


def albums_of(document: IniDocument) -> tuple[Album, ...]:
    """A dokumentum összes virtuális albuma, definíciós sorrendben."""
    return tuple(
        Album(
            # A szekciónévbeli token az azonosító, a token= kulcs redundáns.
            token=section.name[len(ALBUM_SECTION_PREFIX) :],
            name=section.get("name"),
            date=section.get("date"),
            description=section.get("description"),
            location=section.get("location"),
        )
        for section in document.sections
        if section.name.startswith(ALBUM_SECTION_PREFIX)
    )


def with_album(document: IniDocument, photo_name: str, token: str) -> IniDocument:
    """A kép felvétele az albumba — az `albums=` CSV bővítése (#9).

    Idempotens: a már bent lévő token nem kerül be másodszor, és a meglévő
    sorrend sem változik (a Picasa a hozzáadás sorrendjét őrzi).
    """
    section = document.section(photo_name)
    current = parse_album_refs(section.get("albums") or "") if section else ()
    if token in current:
        return document
    return document.with_value(
        photo_name, "albums", serialize_album_refs((*current, token))
    )


def without_album(
    document: IniDocument, photo_name: str, token: str
) -> IniDocument:
    """A kép kivétele az albumból.

    Az utolsó tagság törlésekor maga az `albums=` kulcs is kikerül — üres
    kulcsot a Picasa sem hagy maga után.
    """
    section = document.section(photo_name)
    if section is None:
        return document
    current = parse_album_refs(section.get("albums") or "")
    if token not in current:
        return document
    remaining = tuple(ref for ref in current if ref != token)
    if not remaining:
        return document.with_removed(photo_name, "albums")
    return document.with_value(
        photo_name, "albums", serialize_album_refs(remaining)
    )


def ensure_album(
    document: IniDocument, token: str, name: str | None = None
) -> IniDocument:
    """A `[.album:<token>]` definíció megléte a dokumentumban.

    A MEGLÉVŐ definíciót nem írja át: ha az album már szerepel az ini-ben,
    a neve marad (a Picasa oldali átnevezés a felhasználó szándéka, nem a
    miénk). Új szekciónál a `token=` kulcsot is kiírjuk, ahogy a Picasa is.
    """
    section_name = f"{ALBUM_SECTION_PREFIX}{token}"
    if document.section(section_name) is not None:
        return document
    result = document.with_value(section_name, "token", token)
    if name is not None:
        result = result.with_value(section_name, "name", name)
    return result
