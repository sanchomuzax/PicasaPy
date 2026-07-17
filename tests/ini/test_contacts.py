"""[Contacts2] személybejegyzések — spec: `<person_id>=Név;;`."""

import pytest

from picasapy.ini import contacts_of, parse_document

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
