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
