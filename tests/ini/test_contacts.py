"""[Contacts2] személybejegyzések — spec: `<person_id>=Név;;`."""

import pytest

from picasapy.ini import contacts_of, ensure_contact, find_contact_id, parse_document

SAMPLE = (
    "[Contacts2]\n"
    "b8e4117cf1d6615b=Roy Avery;;\n"
    "8e62b2035b74b477=Kis Éva;eva@example.com;\n"
    "[IMG_0001.jpg]\n"
    "star=yes\n"
)


class TestContactsOf:
    def test_parses_entries(self):
        contacts = contacts_of(parse_document(SAMPLE))
        assert len(contacts) == 2
        assert contacts[0].person_id == "b8e4117cf1d6615b"
        assert contacts[0].name == "Roy Avery"

    def test_extra_fields_preserved(self):
        contacts = contacts_of(parse_document(SAMPLE))
        assert contacts[1].name == "Kis Éva"
        assert contacts[1].extra == ("eva@example.com", "")

    def test_lookup_by_person_id(self):
        contacts = contacts_of(parse_document(SAMPLE))
        by_id = {c.person_id: c for c in contacts}
        assert by_id["8e62b2035b74b477"].name == "Kis Éva"

    def test_no_contacts_section(self):
        assert contacts_of(parse_document("[a.jpg]\nstar=yes\n")) == ()

    def test_empty_contacts_section(self):
        assert contacts_of(parse_document("[Contacts2]\n")) == ()


class TestImmutability:
    def test_contact_is_frozen(self):
        contact = contacts_of(parse_document(SAMPLE))[0]
        with pytest.raises(AttributeError):
            contact.name = "Más"


# -- írás (#26, 1. kör) --------------------------------------------------


class TestFindContactId:
    def test_finds_existing_name(self):
        assert find_contact_id(parse_document(SAMPLE), "Roy Avery") == "b8e4117cf1d6615b"

    def test_unknown_name_gives_none(self):
        assert find_contact_id(parse_document(SAMPLE), "Nincs Ilyen") is None

    def test_no_contacts_section_gives_none(self):
        assert find_contact_id(parse_document("[a.jpg]\nstar=yes\n"), "Roy") is None


class TestEnsureContact:
    def test_creates_section_when_missing(self):
        document = ensure_contact(
            parse_document("[a.jpg]\nstar=yes\n"), "1234567890abcdef", "Új Névtelen"
        )
        contacts = {c.person_id: c.name for c in contacts_of(document)}
        assert contacts == {"1234567890abcdef": "Új Névtelen"}

    def test_adds_to_existing_section(self):
        document = ensure_contact(parse_document(SAMPLE), "1234567890abcdef", "Harmadik")
        contacts = {c.person_id: c.name for c in contacts_of(document)}
        assert contacts["b8e4117cf1d6615b"] == "Roy Avery"  # a régi megmarad
        assert contacts["1234567890abcdef"] == "Harmadik"

    def test_existing_id_is_not_overwritten(self):
        document = ensure_contact(parse_document(SAMPLE), "b8e4117cf1d6615b", "Más Név")
        contacts = {c.person_id: c.name for c in contacts_of(document)}
        assert contacts["b8e4117cf1d6615b"] == "Roy Avery"  # nem íródott át

    def test_case_insensitive_id_match(self):
        document = ensure_contact(parse_document(SAMPLE), "B8E4117CF1D6615B", "Más Név")
        # nincs második, csupa-nagybetűs bejegyzés
        assert len(contacts_of(document)) == 2
