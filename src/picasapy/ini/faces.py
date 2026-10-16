"""A `faces=` kulcs: rect64 régió + contact_id párok pontosvesszővel.

Formátum: `rect64(<hex>),<64-bit hex id>;...`. A `ffffffffffffffff`
contact_id a mellőzés jele, nem azonosítatlan arcé; a `0` nem érvényes
arcbejegyzés. A serialize normalizál (a rect64-et 16 jegyre tölti fel), a
byte-pontos megőrzést a document-réteg adja.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .document import IniDocument
from .rect64 import Rect64, decode_rect64, encode_rect64

# Történeti API-név: a Picasában ez az azonosító mellőzést jelent.
UNIDENTIFIED_CONTACT = "ffffffffffffffff"
# 64 bites hex; a vezető nullák itt is hiányozhatnak, ezért 1..16 jegy.
_CONTACT_ID = re.compile(r"^[0-9a-fA-F]{1,16}$")


@dataclass(frozen=True)
class Face:
    rect: Rect64
    contact_id: str

    @property
    def is_identified(self) -> bool:
        """Van-e nem nulla, nem mellőzés-jelű kontaktazonosítója."""
        contact_id = self.contact_id.casefold()
        return bool(contact_id.strip("0")) and contact_id != UNIDENTIFIED_CONTACT

    @property
    def is_ignored(self) -> bool:
        """A Picasa mellőzést jelző contact_id-ját viseli-e."""
        return self.contact_id.casefold() == UNIDENTIFIED_CONTACT


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
    # #3792: a mért alak (docs/specs/picasa-arcfelismeres.md 190-192. sor)
    # pontosvesszővel VÁLASZTJA EL a bejegyzéseket, záró pontosvesszőt nem
    # tesz a sor végére.
    return ";".join(
        f"rect64({encode_rect64(face.rect)}),{face.contact_id}" for face in faces
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


def without_faces(document: IniDocument, photo_name: str) -> IniDocument:
    """A fotó összes `faces=` téglalapjának eltávolítása.

    A fotószekció és a mappaszintű `[Contacts2]` névjegyzék érintetlen
    marad. A hiányzó szekció vagy kulcs változatlan dokumentumot ad vissza.
    """
    section = document.section(photo_name)
    if section is None or section.get("faces") is None:
        return document
    return document.with_removed(photo_name, "faces")


def remove_all_face_data(document: IniDocument) -> IniDocument:
    """Az összes arc-jelölés és személynév eltávolítása a dokumentumból.

    A `RemoveAllFaceData` után a képek teljes újrakeresése építi vissza a
    saját arcindexet. A Picasa által írt `faces` és `facedata` kulcsokat,
    valamint a hozzájuk tartozó `[Contacts2]` személyneveket is töröljük;
    a fotószekciók minden más kulcsa és a round-trip is megmarad.
    """
    updated = document
    for section in document.file_sections():
        for key in ("faces", "facedata"):
            while True:
                current = updated.section(section.name)
                if current is None or current.get(key) is None:
                    break
                updated = updated.with_removed(section.name, key)
    return _without_all_contacts(updated)


def reset_all_faces(document: IniDocument) -> IniDocument:
    """A személyneveket törli, a régiókat névtelen arcokként megtartja.

    A `ResetAllFaces` a `faces=` minden kontaktazonosítóját `0`-ra állítja
    (ez az arc-régiót megtartó, nem mellőzött névtelen alak), majd törli a
    személyalbumokat adó `[Contacts2]` bejegyzéseket. A `facedata` és az
    egyéb fotóadatok változatlanok.
    """
    updated = document
    for section in document.file_sections():
        current = updated.section(section.name)
        raw_faces = current.get("faces") if current is not None else None
        if raw_faces is None:
            continue
        faces = parse_faces(raw_faces)
        if faces:
            unnamed = tuple(Face(rect=face.rect, contact_id="0") for face in faces)
            updated = updated.with_value(
                section.name, "faces", serialize_faces(unnamed)
            )
    return _without_all_contacts(updated)


def _without_all_contacts(document: IniDocument) -> IniDocument:
    """A dokumentum minden `[Contacts2]` személy-bejegyzését törli."""
    updated = document
    section = updated.section("Contacts2")
    if section is None:
        return updated
    for person_id, _value in section.items():
        updated = updated.with_removed("Contacts2", person_id)
    return updated


def without_face_at_rect(
    document: IniDocument, photo_name: str, rect: Rect64
) -> IniDocument:
    """Az ELSŐ, `rect`-tel egyező arc-bejegyzés törlése — a `contact_id`
    NEM számít (szemben a `without_face`-szal, ami pontos párt vár). A
    szerkesztő overlay (#26, 2. kör) ezt hívja törléskor: a QML-oldal a
    kijelölt régiót csak koordinátaként ismeri, a contact_id-t nem kell
    vele küldenie.

    Nem létező rect esetén a dokumentum változatlan (round-trip elv)."""
    section = document.section(photo_name)
    if section is None:
        return document
    current = parse_faces(section.get("faces") or "")
    updated: list[Face] = []
    removed = False
    for entry in current:
        if not removed and entry.rect == rect:
            removed = True
            continue
        updated.append(entry)
    if not removed:
        return document
    if not updated:
        return document.with_removed(photo_name, "faces")
    return document.with_value(photo_name, "faces", serialize_faces(tuple(updated)))


def with_reassigned_face(
    document: IniDocument, photo_name: str, rect: Rect64, contact_id: str
) -> IniDocument:
    """A `rect`-tel egyező (első) arc-bejegyzés contact_id-jának cseréje —
    a régió (a detektor/import eredménye) VÁLTOZATLAN marad, csak a
    személy-mező cserélődik. A `UNIDENTIFIED_CONTACT` történeti nevű érték
    a Picasában mellőzést jelöl; név levételekor a hívónak törölnie kell a
    bejegyzést.

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
