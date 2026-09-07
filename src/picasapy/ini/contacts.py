"""[Contacts2] személybejegyzések: `<person_id>=full_name;email;gaia_id`.

#2526: az érték három, `;`-vel elválasztott mezője **nevesítve** van, és
az eredeti **pontosan hármat** követel meg. A levezetés (író-regiszterek
+ naplóformátum egyeztetése, címekkel) a
`docs/specs/picasa-menu-parancsok-viselkedes.md` 24.5 szakaszában áll:

    érték            `%s;%s;%s`            0x00c91104
    a három mező     full_name ; email ; gaia_id
    token-szám       pontosan 3            0x00587203 / 0x00587206
    ha nem 3         a bejegyzés ELDOBÓDIK 0x00587110 (naplóüzenet)

A nevek elsődleges forrása egyébként a központi contacts.xml.
"""

from __future__ import annotations

from dataclasses import dataclass

from .document import IniDocument

_SECTION_NAME = "Contacts2"


#: Az érték kötelező token-száma (#2526). A kettes és a négyes alakot az
#: eredeti eldobja — nem javítja, nem tölti fel üressel.
_TOKEN_SZAM = 3


@dataclass(frozen=True)
class Contact:
    person_id: str
    name: str
    email: str
    gaia_id: str


def contacts_of(document: IniDocument) -> tuple[Contact, ...]:
    """A `[Contacts2]` bejegyzések — a nem HÁRMAS alakúak nélkül.

    ⚠️ Ez OLVASÁSI szűrő: a hibás sort a dokumentumban hagyja, csak nem
    adja vissza. Így a round-trip nem csonkítja a felhasználó fájlját —
    az eredeti is csak a betöltésnél dobja el a bejegyzést."""
    section = document.section(_SECTION_NAME)
    if section is None:
        return ()
    contacts = []
    for person_id, value in section.items():
        mezok = value.split(";")
        if len(mezok) != _TOKEN_SZAM:
            continue
        name, email, gaia_id = mezok
        contacts.append(
            Contact(
                person_id=person_id, name=name, email=email, gaia_id=gaia_id
            )
        )
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
