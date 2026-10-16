"""`contacts.xml` import (#26, 2. kör) — a Picasa központi, „legpontosabb"
kapcsolat-fájlja (`docs/specs/pmp-database.md`), a `[Contacts2]` nevek
egyeztetéséhez.

**A fájl OPCIONÁLIS**: sok telepítésen sosem jött létre (a felhasználó nem
kapcsolta össze Google-fiókkal a Picasát) — a hiánya éppúgy nem hiba, mint
a `.picasa.ini` hiánya egy mappában (ld. `docs/research-plan.md`).

Olvasás: a mért `<contacts><contact id=… name=… modified_time=…
local_contact=…/></contacts>` alak, valamint a bináris szövegtáblájából
következtetett Atom feed (`gphoto:personid2`, `gphoto:fullname`, `gaia_id`).
Íráskor a mért, helyi kontakt-alakot használjuk. Az Atom-parser névtér-
független (a helyi nevet nézi), mert a névtér-prefix verziónként változhatott.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
from xml.etree import ElementTree

from picasapy.ioutil import write_atomic

from .contacts import contacts_of
from .document import IniDocument

_SECTION_NAME = "Contacts2"
_CONTACT_ID = re.compile(r"^[0-9a-fA-F]{16}$")


@dataclass(frozen=True)
class ContactXmlEntry:
    """Egy központi névjegy a mért vagy az Atom-alakú contacts.xml-ből."""

    person_id: str
    name: str
    gaia_id: str = ""
    modified_time: str = ""
    local_contact: str = ""


def _local_name(tag: str) -> str:
    """A névtér-előtag levágása (`{ns}tag` → `tag`) — a névtér-URI Picasa-
    verziónként eltérhetett, a mezőnevet a helyi név azonosítja."""
    return tag.rpartition("}")[2]


def parse_contacts_xml(xml_text: str) -> tuple[ContactXmlEntry, ...]:
    """A mért `contacts/contact` vagy következtetett Atom `feed/entry`
    alak feldolgozása. Azonosító VAGY név nélküli bejegyzés kimarad.

    Raises:
        ValueError: érvénytelen XML esetén (nem nyeljük el csendben — a
            hívó eldöntheti, hogy figyelmeztet-e a felhasználónak)."""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Érvénytelen contacts.xml: {exc}") from exc
    entries = []
    if _local_name(root.tag) == "contacts":
        for contact_el in root:
            if _local_name(contact_el.tag) != "contact":
                continue
            person_id = contact_el.get("id", "").strip()
            name = contact_el.get("name", "").strip()
            if person_id and name:
                entries.append(
                    ContactXmlEntry(
                        person_id=person_id,
                        name=name,
                        modified_time=contact_el.get("modified_time", "").strip(),
                        local_contact=contact_el.get("local_contact", "").strip(),
                    )
                )
        return tuple(entries)

    for entry_el in root:
        if _local_name(entry_el.tag) != "entry":
            continue
        person_id = ""
        name = ""
        gaia_id = ""
        for field in entry_el:
            local = _local_name(field.tag)
            text = (field.text or "").strip()
            if local == "personid2":
                person_id = text
            elif local == "fullname":
                name = text
            elif local == "gaia_id":
                gaia_id = text
        if person_id and name:
            entries.append(
                ContactXmlEntry(person_id=person_id, name=name, gaia_id=gaia_id)
            )
    return tuple(entries)


def load_contacts_xml(path: str | Path) -> tuple[ContactXmlEntry, ...]:
    """A `path` beolvasása, vagy üres eredmény, ha a fájl nem létezik —
    a hívónak NEM kell külön `.exists()` ellenőrzést végeznie (opcionális
    bemenet, ld. modul-docstring)."""
    target = Path(path)
    if not target.exists():
        return ()
    return parse_contacts_xml(target.read_text(encoding="utf-8"))


def serialize_contacts_xml(entries: tuple[ContactXmlEntry, ...]) -> str:
    """A mért, `<contacts><contact …/></contacts>` alak kiírása.

    A hiányzó időbélyeg vagy nem helyi névjegy adata nem következtethető ki
    az Atom-import alakjából, ezért a hívónak kell a mért mezőket megadnia.
    """
    root = ElementTree.Element("contacts")
    for entry in entries:
        if not _CONTACT_ID.fullmatch(entry.person_id):
            raise ValueError("A contacts.xml azonosítója 16 hex jegy legyen.")
        try:
            modified = datetime.fromisoformat(entry.modified_time)
        except ValueError as exc:
            raise ValueError("A contacts.xml módosítási ideje legyen ISO-8601.") from exc
        if modified.tzinfo is None:
            raise ValueError("A contacts.xml módosítási ideje tartalmazzon időzónát.")
        if entry.local_contact != "1":
            raise ValueError("A PicasaPy helyi névjegyénél local_contact=1 kell.")
        ElementTree.SubElement(
            root,
            "contact",
            {
                "id": entry.person_id.lower(),
                "name": entry.name,
                "modified_time": entry.modified_time,
                "local_contact": entry.local_contact,
            },
        )
    ElementTree.indent(root, space=" ")
    return ElementTree.tostring(root, encoding="unicode", xml_declaration=True) + "\n"


def save_contacts_xml(path: str | Path, entries: tuple[ContactXmlEntry, ...]) -> None:
    """A központi tár kiírása a specifikált, mért XML-alakban, atomikusan."""
    payload = serialize_contacts_xml(entries).encode("utf-8")
    write_atomic(Path(path), payload, make_parents=True)


def apply_contacts_xml(
    document: IniDocument, entries: tuple[ContactXmlEntry, ...]
) -> IniDocument:
    """A `[Contacts2]` nevek egyeztetése a contacts.xml (elsődleges forrás,
    ld. `pmp-database.md`) alapján: a MEGLÉVŐ bejegyzések neve frissül, ha
    eltér — a másik két mező (`email`, `gaia_id`) és a kulcs eredeti írásmódja
    (kis/nagybetű) megmarad. Új személyt NEM hoz létre (ld. teszt-docstring:
    az árva kontaktok felhalmozódását kerüli — új személy a
    faces_helper arc-hozzárendelésén keresztül jön létre)."""
    section = document.section(_SECTION_NAME)
    if section is None or not entries:
        return document
    by_id = {entry.person_id.casefold(): entry.name for entry in entries}
    for contact in contacts_of(document):
        fresh_name = by_id.get(contact.person_id.casefold())
        if fresh_name is None or fresh_name == contact.name:
            continue
        # #2526: az érték HÁROM mezős; a másik kettőt változatlanul visszük
        value = ";".join((fresh_name, contact.email, contact.gaia_id))
        document = document.with_value(_SECTION_NAME, contact.person_id, value)
    return document
