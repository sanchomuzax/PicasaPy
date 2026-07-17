"""A `faces=` kulcs: rect64 régió + contact_id párok pontosvesszővel.

Formátum: `rect64(<hex>),<64-bit hex id>;...` — az azonosítatlan arc
contact_id-ja csupa `f`. A serialize normalizál (a rect64-et 16 jegyre
tölti fel), a byte-pontos megőrzést a document-réteg adja.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

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
