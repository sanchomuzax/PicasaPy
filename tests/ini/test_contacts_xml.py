"""`contacts.xml` import — a Picasa központi kapcsolat-fájlja (#26, 2. kör).

Spec: docs/specs/pmp-database.md („contacts.xml") + docs/specs/
picasa-exe-strings.md (`gphoto:personid2`, `gphoto:fullname`, `gaia_id`
mezőnevek az .exe-ből). A fájl OPCIONÁLIS bemenet — a Picasa nem minden
telepítésen hozza létre (pl. sosem volt Google-fiókkal használva), ezért a
hiánya NEM hiba, csak üres eredmény."""

from pathlib import Path

import pytest

from picasapy.ini import parse_document
from picasapy.ini.contacts_xml import (
    ContactXmlEntry,
    apply_contacts_xml,
    load_contacts_xml,
    parse_contacts_xml,
)

SAMPLE_XML = """<?xml version='1.0' encoding='UTF-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'
      xmlns:gphoto='http://schemas.google.com/photos/2007'>
  <entry>
    <gphoto:personid2>b8e4117cf1d6615b</gphoto:personid2>
    <gphoto:fullname>Roy Avery</gphoto:fullname>
    <gaia_id>1234567890</gaia_id>
  </entry>
  <entry>
    <gphoto:personid2>8e62b2035b74b477</gphoto:personid2>
    <gphoto:fullname>Kis Éva</gphoto:fullname>
  </entry>
</feed>
"""


class TestParseContactsXml:
    def test_parses_entries(self):
        entries = parse_contacts_xml(SAMPLE_XML)
        assert entries == (
            ContactXmlEntry(
                person_id="b8e4117cf1d6615b", name="Roy Avery", gaia_id="1234567890"
            ),
            ContactXmlEntry(person_id="8e62b2035b74b477", name="Kis Éva", gaia_id=""),
        )

    def test_empty_feed_gives_empty_tuple(self):
        empty = "<?xml version='1.0'?><feed xmlns='http://www.w3.org/2005/Atom'/>"
        assert parse_contacts_xml(empty) == ()

    def test_entry_without_name_is_skipped(self):
        # névtelen bejegyzés (pl. törölt/hiányos) nem hasznos — kihagyjuk
        xml = (
            "<?xml version='1.0'?>"
            "<feed xmlns='http://www.w3.org/2005/Atom' "
            "xmlns:gphoto='http://schemas.google.com/photos/2007'>"
            "<entry><gphoto:personid2>aaaa</gphoto:personid2></entry>"
            "</feed>"
        )
        assert parse_contacts_xml(xml) == ()

    def test_entry_without_id_is_skipped(self):
        xml = (
            "<?xml version='1.0'?>"
            "<feed xmlns='http://www.w3.org/2005/Atom' "
            "xmlns:gphoto='http://schemas.google.com/photos/2007'>"
            "<entry><gphoto:fullname>Név Nélküli Id</gphoto:fullname></entry>"
            "</feed>"
        )
        assert parse_contacts_xml(xml) == ()

    def test_malformed_xml_raises_value_error(self):
        with pytest.raises(ValueError):
            parse_contacts_xml("nem xml <<<")


class TestLoadContactsXml:
    def test_missing_file_gives_empty_tuple(self, tmp_path: Path):
        # OPCIONÁLIS bemenet — a hiánya nem hiba (docs/research-plan.md)
        assert load_contacts_xml(tmp_path / "nincs" / "contacts.xml") == ()

    def test_reads_existing_file(self, tmp_path: Path):
        path = tmp_path / "contacts.xml"
        path.write_text(SAMPLE_XML, encoding="utf-8")
        entries = load_contacts_xml(path)
        assert len(entries) == 2
        assert entries[0].name == "Roy Avery"


class TestApplyContactsXml:
    def test_updates_name_of_existing_person_id(self):
        document = parse_document(
            "[Contacts2]\nb8e4117cf1d6615b=Elgépelt Név;;\n"
        )
        entries = (
            ContactXmlEntry(person_id="b8e4117cf1d6615b", name="Roy Avery", gaia_id=""),
        )
        updated = apply_contacts_xml(document, entries)
        from picasapy.ini import contacts_of

        contacts = {c.person_id: c for c in contacts_of(updated)}
        assert contacts["b8e4117cf1d6615b"].name == "Roy Avery"

    def test_preserves_extra_fields_on_name_update(self):
        document = parse_document(
            "[Contacts2]\nb8e4117cf1d6615b=Régi;email@example.com;\n"
        )
        entries = (
            ContactXmlEntry(person_id="b8e4117cf1d6615b", name="Új Név", gaia_id=""),
        )
        updated = apply_contacts_xml(document, entries)
        from picasapy.ini import contacts_of

        contacts = {c.person_id: c for c in contacts_of(updated)}
        assert contacts["b8e4117cf1d6615b"].name == "Új Név"
        assert contacts["b8e4117cf1d6615b"].extra == ("email@example.com", "")

    def test_matching_name_is_a_no_op(self):
        document = parse_document("[Contacts2]\nb8e4117cf1d6615b=Roy Avery;;\n")
        entries = (
            ContactXmlEntry(person_id="b8e4117cf1d6615b", name="Roy Avery", gaia_id=""),
        )
        assert apply_contacts_xml(document, entries) == document

    def test_unknown_person_id_is_not_added(self):
        # az importer csak a MEGLÉVŐ [Contacts2]-bejegyzéseket egyezteti —
        # új személyt a faces_helper (arc-hozzárendelés) hoz létre, nem az
        # importer (kerüli az árva, sosem taggelt kontaktok felhalmozását)
        document = parse_document("[Contacts2]\nb8e4117cf1d6615b=Roy Avery;;\n")
        entries = (
            ContactXmlEntry(person_id="ffffffffffffff01", name="Idegen", gaia_id=""),
        )
        assert apply_contacts_xml(document, entries) == document

    def test_no_contacts_section_is_a_no_op(self):
        document = parse_document("[a.jpg]\nstar=yes\n")
        entries = (ContactXmlEntry(person_id="aaaa", name="Bárki", gaia_id=""),)
        assert apply_contacts_xml(document, entries) == document

    def test_case_insensitive_person_id_match(self):
        document = parse_document("[Contacts2]\nB8E4117CF1D6615B=Régi;;\n")
        entries = (
            ContactXmlEntry(person_id="b8e4117cf1d6615b", name="Friss", gaia_id=""),
        )
        updated = apply_contacts_xml(document, entries)
        from picasapy.ini import contacts_of

        contacts = {c.person_id: c for c in contacts_of(updated)}
        assert contacts["B8E4117CF1D6615B"].name == "Friss"
