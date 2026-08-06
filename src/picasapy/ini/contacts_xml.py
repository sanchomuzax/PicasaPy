"""`contacts.xml` import (#26, 2. kör) — a Picasa központi, „legpontosabb"
kapcsolat-fájlja (`docs/specs/pmp-database.md`), a `[Contacts2]` nevek
egyeztetéséhez.

**A fájl OPCIONÁLIS**: sok telepítésen sosem jött létre (a felhasználó nem
kapcsolta össze Google-fiókkal a Picasát) — a hiánya éppúgy nem hiba, mint
a `.picasa.ini` hiánya egy mappában (ld. `docs/research-plan.md`).

Formátum: Atom feed, `gphoto:` névtér — a mezőnevek (`gphoto:personid2`,
`gphoto:fullname`, `gaia_id`) a `Picasa3.exe` string-táblájából
igazoltak (`docs/specs/picasa-exe-strings.md`). A parser névtér-független
(a helyi nevet nézi), mert a névtér-prefix verziónként változhatott.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree

from .contacts import contacts_of
from .document import IniDocument

_SECTION_NAME = "Contacts2"


@dataclass(frozen=True)
class ContactXmlEntry:
    """Egy `<entry>` a contacts.xml-ből — a [Contacts2] egyeztetéshez
    csak a személy-azonosító és a név kell, a `gaia_id`-t (Google-fiók
    azonosító) csak megőrizzük, egyelőre nem használjuk fel."""

    person_id: str
    name: str
    gaia_id: str = ""


def _local_name(tag: str) -> str:
    """A névtér-előtag levágása (`{ns}tag` → `tag`) — a névtér-URI Picasa-
    verziónként eltérhetett, a mezőnevet a helyi név azonosítja."""
    return tag.rpartition("}")[2]


def parse_contacts_xml(xml_text: str) -> tuple[ContactXmlEntry, ...]:
    """A feed `<entry>` elemeinek feldolgozása. Azonosító VAGY név nélküli
    bejegyzés kimarad (nem hasznos a [Contacts2] egyeztetéshez).

    Raises:
        ValueError: érvénytelen XML esetén (nem nyeljük el csendben — a
            hívó eldöntheti, hogy figyelmeztet-e a felhasználónak)."""
    try:
        root = ElementTree.fromstring(xml_text)
    except ElementTree.ParseError as exc:
        raise ValueError(f"Érvénytelen contacts.xml: {exc}") from exc
    entries = []
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
            entries.append(ContactXmlEntry(person_id=person_id, name=name, gaia_id=gaia_id))
    return tuple(entries)


def load_contacts_xml(path: str | Path) -> tuple[ContactXmlEntry, ...]:
    """A `path` beolvasása, vagy üres eredmény, ha a fájl nem létezik —
    a hívónak NEM kell külön `.exists()` ellenőrzést végeznie (opcionális
    bemenet, ld. modul-docstring)."""
    target = Path(path)
    if not target.exists():
        return ()
    return parse_contacts_xml(target.read_text(encoding="utf-8"))


def apply_contacts_xml(
    document: IniDocument, entries: tuple[ContactXmlEntry, ...]
) -> IniDocument:
    """A `[Contacts2]` nevek egyeztetése a contacts.xml (elsődleges forrás,
    ld. `pmp-database.md`) alapján: a MEGLÉVŐ bejegyzések neve frissül, ha
    eltér — az `extra` mezők (pl. e-mail) és a kulcs eredeti írásmódja
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
        value = ";".join((fresh_name, *contact.extra))
        document = document.with_value(_SECTION_NAME, contact.person_id, value)
    return document
