"""Az `imagedata.deferredregion` oszlop értelmezése (#1).

Éles db3-validálás (2026-07-16, MEMORY.md): ez az oszlop a valódi
arcadat-hordozó — formátuma `rect64(<hex>),<Név>;rect64(<hex>),<Név>;...`
tisztanevű (nem hash-elt) régiólistával. A rect64 hex itt is rövidülhet,
a dekóder zfill(16)-tal pótol (ini/rect64 közös logika).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from picasapy.ini.rect64 import Rect64, decode_rect64


@dataclass(frozen=True)
class DeferredFace:
    rect: Rect64
    name: str
    #: A `deferredface` row carries the Picasa contact id. A `deferredregion`
    #: snapshot has no id and leaves this as `None`.
    contact_id: str | None = None


_CONTACT_ID = re.compile(r"^[0-9a-fA-F]{1,16}$")


def parse_deferred_region(value: str | None) -> tuple[DeferredFace, ...]:
    """A régiólista parse-olása; üres/None értékre üres tuple.

    Raises:
        ValueError: Formátumhibás bejegyzésnél (nem rect64-gyel kezdődik,
            vagy hiányzik a név-elválasztó vessző).
    """
    if not value:
        return ()
    faces = []
    for entry in value.split(";"):
        if not entry:
            continue
        rect_part, sep, name = entry.partition(",")
        if not sep or not rect_part.startswith("rect64("):
            raise ValueError(f"Érvénytelen deferredregion-bejegyzés: {entry!r}")
        faces.append(DeferredFace(rect=decode_rect64(rect_part), name=name))
    return tuple(faces)


def parse_deferred_face(value: str | None) -> tuple[DeferredFace, ...]:
    """Parse the id-bearing `imagedata.deferredface` region list.

    Names are resolved later from `contacts.xml`; the returned `name` is
    empty and `contact_id` holds the normalized, 16-digit source id.
    """
    if not value:
        return ()
    faces = []
    for entry in value.split(";"):
        if not entry:
            continue
        rect_part, sep, contact_id = entry.partition(",")
        if (
            not sep
            or not rect_part.startswith("rect64(")
            or not _CONTACT_ID.fullmatch(contact_id)
        ):
            raise ValueError(f"Érvénytelen deferredface-bejegyzés: {entry!r}")
        faces.append(
            DeferredFace(
                rect=decode_rect64(rect_part),
                name="",
                contact_id=contact_id.casefold().zfill(16),
            )
        )
    return tuple(faces)
