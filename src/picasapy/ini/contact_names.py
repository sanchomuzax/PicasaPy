"""Közös személyazonosító → név feloldás (#4579, #5179).

A PicasaPy központi névjegytára az elsődleges forrás; a mappa
`.picasa.ini` `[Contacts2]` szakasza csak tartalék.
"""

from __future__ import annotations

from pathlib import Path

from .contacts import contacts_of
from .contacts_xml import ContactXmlEntry, load_contacts_xml


def central_contacts_path(db_path: str | Path) -> Path:
    """A központi tár `contacts/contacts.xml` fájlja az index útvonalából."""
    return Path(db_path).parent / "contacts" / "contacts.xml"


class ContactNameResolver:
    """Egy központi névjegytár és egy ini-dokumentum közös névfeloldója.

    A központi XML-t egyszer olvassa be, ezért egy teljes mappa-söprésben
    nem nyitja meg újra minden `.picasa.ini` feldolgozásakor.
    """

    def __init__(self, central_path: str | Path | None = None) -> None:
        try:
            self.central_contacts: tuple[ContactXmlEntry, ...] = (
                load_contacts_xml(central_path) if central_path is not None else ()
            )
        except (OSError, ValueError):
            self.central_contacts = ()
        self._central_by_id = {
            contact.person_id.casefold(): contact.name
            for contact in self.central_contacts
            if contact.person_id and contact.name
        }

    def names_by_id(self, document) -> dict[str, str]:
        """`casefold`-olt id → név; a központi név felülírja a helyit."""
        names = {
            contact.person_id.casefold(): contact.name
            for contact in contacts_of(document)
            if contact.person_id and contact.name
        }
        names.update(self._central_by_id)
        return names

    def central_names(self) -> tuple[str, ...]:
        """A központi tár nevei, kis-nagybetű szerint egyedítve."""
        names: dict[str, str] = {}
        for contact in self.central_contacts:
            if contact.name:
                names.setdefault(contact.name.casefold(), contact.name)
        return tuple(names.values())


def contact_names_by_id(document, central_path=None) -> dict[str, str]:
    """A közös feloldó kényelmi függvénye egyetlen dokumentumhoz."""
    return ContactNameResolver(central_path).names_by_id(document)


__all__ = [
    "ContactNameResolver",
    "central_contacts_path",
    "contact_names_by_id",
]
