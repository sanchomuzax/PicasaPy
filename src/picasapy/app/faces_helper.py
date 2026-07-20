"""FacesHelper: a `faces=` régiók (#147) csak-olvasás szintű QML-hídja.

A néző overlay-je ezen keresztül kéri le egy adott fotóhoz a mentett
arc-régiókat: a `faces=` kulcsot és a nevet adó `[Contacts2]` szekciót
közvetlenül a fotó mappájának `.picasa.ini`-jéből olvassuk — nincs
index-bővítés, nincs contacts.xml (az a #26). Írás NINCS: ez a modul csak
a meglévő, más eszközzel (Picasa/import) létrehozott bejegyzéseket mutatja.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Slot

from picasapy.ini import contacts_of, load_document, parse_faces
from picasapy.ini.faces import Face
from picasapy.scanner import PICASA_INI_NAME


class FacesHelper(QObject):
    """QML-nek kitett, állapotmentes lekérdező: fotó-útvonal → arc-régiók."""

    @Slot(str, result="QVariantList")
    def facesFor(self, image_path: str) -> list[dict]:
        """A `faces=` bejegyzések a megadott fotóhoz, névvel feloldva.

        Minden elem: {left, top, right, bottom} relatív [0..1] koordináták
        (rect64) és `name` (a [Contacts2]-ből, vagy üres, ha a contact_id
        azonosítatlan vagy nincs névbejegyzés). Hiányzó ini/szekció/kulcs,
        vagy hibás `faces=` érték esetén üres lista — a néző ilyenkor
        egyszerűen nem rajzol keretet, nem omlik össze."""
        if not image_path:
            return []
        path = Path(image_path)
        ini_path = path.parent / PICASA_INI_NAME
        if not ini_path.exists():
            return []
        document = load_document(ini_path)
        section = document.section(path.name)
        raw_faces = section.get("faces") if section is not None else None
        if not raw_faces:
            return []
        try:
            faces = parse_faces(raw_faces)
        except ValueError:
            return []
        names = {contact.person_id.casefold(): contact.name for contact in contacts_of(document)}
        return [_face_to_dict(face, names) for face in faces]


def _face_to_dict(face: Face, names: dict[str, str]) -> dict:
    return {
        "left": face.rect.left,
        "top": face.rect.top,
        "right": face.rect.right,
        "bottom": face.rect.bottom,
        "name": names.get(face.contact_id.casefold(), "") if face.is_identified else "",
    }
