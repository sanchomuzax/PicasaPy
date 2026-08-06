"""A `faces=` kulcs: rect64 régió + contact_id párok pontosvesszővel.

Formátum: `rect64(<hex>),<64-bit hex id>;...` — az azonosítatlan arc
contact_id-ja csupa `f`. A serialize normalizál (a rect64-et 16 jegyre
tölti fel), a byte-pontos megőrzést a document-réteg adja.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .document import IniDocument
from .rect64 import Rect64, decode_rect64, encode_rect64

UNIDENTIFIED_CONTACT = "ffffffffffffffff"
# 64 bites hex; a vezető nullák itt is hiányozhatnak, ezért 1..16 jegy.
_CONTACT_ID = re.compile(r"^[0-9a-fA-F]{1,16}$")


@dataclass(frozen=True)
class Face:
    rect: Rect64
    contact_id: str

    @property
    def is_identified(self) -> bool:
        return self.contact_id.casefold() != UNIDENTIFIED_CONTACT


def parse_faces(value: str) -> tuple[Face, ...]:
    faces = []
    for entry in value.split(";"):
        if not entry:
            continue
        rect_part, sep, contact_id = entry.partition(",")
        if (
            not sep
            or not rect_part.startswith("rect64(")
            or not _CONTACT_ID.match(contact_id)
        ):
            raise ValueError(f"Érvénytelen faces-bejegyzés: {entry!r}")
        faces.append(Face(rect=decode_rect64(rect_part), contact_id=contact_id))
    return tuple(faces)


def serialize_faces(faces: tuple[Face, ...]) -> str:
    return "".join(
        f"rect64({encode_rect64(face.rect)}),{face.contact_id};" for face in faces
    )


# -- írás (#26, 1. kör): meglévő névhez arc-téglalap hozzárendelése/törlése --
# Az `albums.py` with_album/without_album mintáját követi: tiszta, immutábilis
# függvények, a byte-pontos round-trip-et a document-réteg adja.


def with_face(document: IniDocument, photo_name: str, face: Face) -> IniDocument:
    """Új arc-bejegyzés hozzáadása a `faces=`-hez.

    Idempotens: ha PONTOSAN ugyanez a (rect, contact_id) pár már szerepel,
    nem duplikál — a meglévő sorrend változatlan marad."""
    section = document.section(photo_name)
    current = parse_faces(section.get("faces") or "") if section else ()
    if face in current:
        return document
    return document.with_value(
        photo_name, "faces", serialize_faces((*current, face))
    )


def without_face(document: IniDocument, photo_name: str, face: Face) -> IniDocument:
    """A megadott (rect, contact_id) PONTOS párjának eltávolítása.

    Az utolsó bejegyzés törlésekor maga a `faces=` kulcs is kikerül. Ha a
    pár nem szerepel, a dokumentum változatlan (round-trip elv)."""
    section = document.section(photo_name)
    if section is None:
        return document
    current = parse_faces(section.get("faces") or "")
    if face not in current:
        return document
    remaining = tuple(f for f in current if f != face)
    if not remaining:
        return document.with_removed(photo_name, "faces")
    return document.with_value(photo_name, "faces", serialize_faces(remaining))


def with_reassigned_face(
    document: IniDocument, photo_name: str, rect: Rect64, contact_id: str
) -> IniDocument:
    """A `rect`-tel egyező (első) arc-bejegyzés contact_id-jának cseréje —
    a régió (a detektor/import eredménye) VÁLTOZATLAN marad, csak a
    névhozzárendelés cserélődik. `contact_id=UNIDENTIFIED_CONTACT` a
    névcímke levételét jelenti (a régió megmarad, csak "azonosítatlanná"
    válik — ez a Picasa-viselkedés a névcímke törlésekor).

    Nem létező rect esetén a dokumentum változatlan (nincs mit
    módosítani — a hívó felelőssége, hogy létező régiót adjon)."""
    section = document.section(photo_name)
    if section is None:
        return document
    current = parse_faces(section.get("faces") or "")
    updated: list[Face] = []
    changed = False
    for entry in current:
        if not changed and entry.rect == rect:
            updated.append(Face(rect=entry.rect, contact_id=contact_id))
            changed = True
        else:
            updated.append(entry)
    if not changed:
        return document
    return document.with_value(photo_name, "faces", serialize_faces(tuple(updated)))
