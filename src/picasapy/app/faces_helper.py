"""FacesHelper: a `faces=` régiók (#147) QML-hídja — olvasás ÉS írás (#26,
2. kör: az arc-téglalap szerkesztő overlay ezen keresztül ér el).

A néző overlay-je ezen keresztül kéri le egy adott fotóhoz a mentett
arc-régiókat: a `faces=` kulcsot és a nevet adó `[Contacts2]` szekciót
közvetlenül a fotó mappájának `.picasa.ini`-jéből olvassuk — nincs
index-bővítés (`people.py` a mintája: mindig friss ini-olvasás, nem
cache-elt tábla).

Az ÍRÁS a csillag/album-mintát követi (`photo_ops_controller.py`,
`ini.io.update_document`): ütközésbiztos (párhuzamos Picasa-írás esetén
újrajátszott), atomikus, backuppal. Index-UPDATE NEM kell (a `people.py`
minden híváskor újraolvassa az ini-t), ezért — a csillag/forgatással
ellentétben — nincs szükség háttérszálra/`_run_photo_write`-ra: az
ini-írás önmagában is gyors (kis fájl), a szinkron hívás itt egyszerűbb."""

from __future__ import annotations

import secrets
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from picasapy.ini import (
    UNIDENTIFIED_CONTACT,
    IniConflictError,
    IniSaveError,
    contacts_of,
    ensure_contact,
    find_contact_id,
    load_document,
    parse_faces,
    update_document,
    with_face,
    with_reassigned_face,
    without_face_at_rect,
)
from picasapy.ini.faces import Face
from picasapy.ini.rect64 import Rect64
from picasapy.scanner import PICASA_INI_NAME

# a csillag/album-írás mintája (photo_ops_controller.py): a tartós
# ütközés is kezelt hiba, nem néma adatvesztés/omlás
_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError)


class FacesHelper(QObject):
    """QML-nek kitett lekérdező/író: fotó-útvonal → arc-régiók."""

    # a szerkesztő overlay ezt figyeli hibaüzenethez (a albumWriteFailed
    # mintája, photo_ops_controller.py)
    faceWriteFailed = Signal(str)

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
        document, path = self._load(image_path)
        if document is None:
            return []
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

    @Slot(str, result="QVariantList")
    def knownNames(self, image_path: str) -> list[str]:
        """A fotó mappájának `[Contacts2]`-jében ismert nevek, kis-nagybetű-
        tűrően rendezve — a névhozzárendelő mező javaslatlistájának
        (meglévő személy kiválasztása új helyett)."""
        if not image_path:
            return []
        document, _path = self._load(image_path)
        if document is None:
            return []
        names = {contact.name for contact in contacts_of(document) if contact.name}
        return sorted(names, key=str.casefold)

    @Slot(str, float, float, float, float, str, result=bool)
    def addFace(
        self, image_path: str, left: float, top: float, right: float, bottom: float, name: str
    ) -> bool:
        """Új arc-téglalap felvétele — üres `name`-nél azonosítatlanul (a
        régió megrajzolható a névadás előtt is, Picasa-mintára)."""
        def mutate(document, photo_name, rect):
            _document, contact_id = self._resolve_contact_id(document, name)
            return with_face(_document, photo_name, Face(rect=rect, contact_id=contact_id))

        return self._mutate(image_path, mutate, left, top, right, bottom)

    @Slot(str, float, float, float, float, str, result=bool)
    def renameFace(
        self, image_path: str, left: float, top: float, right: float, bottom: float, name: str
    ) -> bool:
        """A `(left,top,right,bottom)` régiót viselő MEGLÉVŐ arc névhozzá-
        rendelésének cseréje — a régió maga változatlan. Üres `name`:
        névcímke levétele (a régió azonosítatlanná válik, Picasa-viselkedés).
        Nem létező régiónál no-op (igaz eredménnyel — nem hiba)."""
        def mutate(document, photo_name, rect):
            _document, contact_id = self._resolve_contact_id(document, name)
            return with_reassigned_face(_document, photo_name, rect, contact_id)

        return self._mutate(image_path, mutate, left, top, right, bottom)

    @Slot(str, float, float, float, float, result=bool)
    def removeFace(
        self, image_path: str, left: float, top: float, right: float, bottom: float
    ) -> bool:
        """A `(left,top,right,bottom)` régió törlése (a contact_id nem
        számít — `without_face_at_rect`)."""
        return self._mutate(
            image_path,
            lambda document, photo_name, rect: without_face_at_rect(document, photo_name, rect),
            left, top, right, bottom,
        )

    # -- belső segédek -----------------------------------------------------

    def _load(self, image_path: str):
        path = Path(image_path)
        ini_path = path.parent / PICASA_INI_NAME
        if not ini_path.exists():
            return None, path
        return load_document(ini_path), path

    def _resolve_contact_id(self, document, name: str) -> tuple[object, str]:
        """A `name` személy contact_id-ja EBBEN a dokumentumban — meglévőt
        újrahasznosít (`find_contact_id`), újat csak akkor hoz létre, ha
        nincs ilyen nevű kontakt még (64 bites véletlen hex, a Picasa-
        formátum szerint). Üres név: azonosítatlan (`UNIDENTIFIED_CONTACT`),
        a dokumentum változatlan."""
        clean_name = (name or "").strip()
        if not clean_name:
            return document, UNIDENTIFIED_CONTACT
        existing = find_contact_id(document, clean_name)
        if existing is not None:
            return document, existing
        new_id = secrets.token_hex(8)
        return ensure_contact(document, new_id, clean_name), new_id

    def _mutate(self, image_path: str, mutate, left=None, top=None, right=None, bottom=None) -> bool:
        """Közös írási keret: ütközésbiztos `update_document` egyetlen
        atomi mutate-tal (a rekonstrukciós azonosító-lookup ÉS az arc-írás
        együtt, hogy ütközés-újrajátszásnál konzisztens maradjon)."""
        if not image_path:
            return False
        path = Path(image_path)
        ini_path = path.parent / PICASA_INI_NAME
        rect = Rect64(left, top, right, bottom) if left is not None else None

        def do_mutate(document):
            return mutate(document, path.name, rect)

        try:
            update_document(ini_path, do_mutate, backup=True)
        except _WRITE_ERRORS as error:
            self.faceWriteFailed.emit(str(error))
            return False
        return True


def _face_to_dict(face: Face, names: dict[str, str]) -> dict:
    return {
        "left": face.rect.left,
        "top": face.rect.top,
        "right": face.rect.right,
        "bottom": face.rect.bottom,
        "name": names.get(face.contact_id.casefold(), "") if face.is_identified else "",
    }
