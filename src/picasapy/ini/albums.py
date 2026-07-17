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
