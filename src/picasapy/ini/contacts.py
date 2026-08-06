"""[Contacts2] személybejegyzések: `<person_id>=Név;;`.

A név utáni, `;`-vel elválasztott mezőket nyersen megőrizzük (`extra`) —
a nevek elsődleges forrása egyébként a központi contacts.xml.
"""

from __future__ import annotations

from dataclasses import dataclass

from .document import IniDocument

_SECTION_NAME = "Contacts2"


@dataclass(frozen=True)
class Contact:
    person_id: str
    name: str
    extra: tuple[str, ...]


def contacts_of(document: IniDocument) -> tuple[Contact, ...]:
    section = document.section(_SECTION_NAME)
    if section is None:
        return ()
    contacts = []
    for person_id, value in section.items():
        name, *extra = value.split(";")
        contacts.append(Contact(person_id=person_id, name=name, extra=tuple(extra)))
    return tuple(contacts)


def find_contact_id(document: IniDocument, name: str) -> str | None:
    """A `name` nevű személy `person_id`-je EBBEN a dokumentumban, ha van
    (a `[Contacts2]` „csak lokális" — más mappában más id-je lehet ugyan-
    annak a névnek, ld. `docs/specs/picasa-ini-format.md`)."""
    for contact in contacts_of(document):
        if contact.name == name:
            return contact.person_id
    return None


def ensure_contact(document: IniDocument, person_id: str, name: str) -> IniDocument:
    """A `[Contacts2]` bejegyzés megléte a dokumentumban (az `ensure_album`
    mintája, #26).

    A MEGLÉVŐ bejegyzést nem írja át (kis-nagybetű-tűrő `person_id`-
    egyezéssel) — csak hiányzó id-nál hoz létre újat, üres `extra`
    mezőkkel (`Név;;`, a Picasa-formátum mintájára)."""
    section = document.section(_SECTION_NAME)
    if section is not None:
        folded = person_id.casefold()
        if any(existing_id.casefold() == folded for existing_id, _ in section.items()):
            return document
    return document.with_value(_SECTION_NAME, person_id, f"{name};;")
