"""Az `imagedata.deferredregion` oszlop értelmezése (#1).

Éles db3-validálás (2026-07-16, MEMORY.md): ez az oszlop a valódi
arcadat-hordozó — formátuma `rect64(<hex>),<Név>;rect64(<hex>),<Név>;...`
tisztanevű (nem hash-elt) régiólistával. A rect64 hex itt is rövidülhet,
a dekóder zfill(16)-tal pótol (ini/rect64 közös logika).
"""

from __future__ import annotations

from dataclasses import dataclass

from picasapy.ini.rect64 import Rect64, decode_rect64


@dataclass(frozen=True)
class DeferredFace:
    rect: Rect64
    name: str


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
