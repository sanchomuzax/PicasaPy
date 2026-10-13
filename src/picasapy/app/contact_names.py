"""Névjegy-azonosító -> név feloldás, közösen (#4579).

A nevek elsődleges forrása a PicasaPy központi `contacts/contacts.xml`-je
(a db melletti mappában), másodlagos a mappa `.picasa.ini` `[Contacts2]`
szakasza — ugyanez a sorrend érvényes a `people_controller` névjegy-
egyesítésére is (a központi név a mérvadó).
"""

from __future__ import annotations

from pathlib import Path

from picasapy.ini import contacts_of, load_contacts_xml


def central_contacts_path(db_path) -> Path:
    """A központi tár `contacts/contacts.xml` fájlja az index útvonalából."""
    return Path(db_path).parent / "contacts" / "contacts.xml"


def contact_names_by_id(document, central_path=None) -> dict[str, str]:
    """`casefold`-olt azonosító -> név; a központi név felülírja a mappabelit.

    Elérhetetlen vagy romlott központi fájl esetén csak a mappabeli nevek."""
    nevek = {
        contact.person_id.casefold(): contact.name
        for contact in contacts_of(document)
    }
    if central_path is not None:
        try:
            kozponti = load_contacts_xml(central_path)
        except (OSError, ValueError):
            kozponti = ()
        for contact in kozponti:
            if contact.name and contact.person_id:
                nevek[contact.person_id.casefold()] = contact.name
    return nevek
