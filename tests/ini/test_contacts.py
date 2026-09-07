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

#: #2526: az eredeti PONTOSAN három tokent fogad el; a kettes és a négyes
#: alakot eldobja (*„Cannot restore .ini entry for contact, %llx,
#: unexpected number of tokens in string."*, `0x00587110`). A spec
#: levezetése: `docs/specs/picasa-menu-parancsok-viselkedes.md` 24.5.
ROSSZ_TOKENSZAM = (
    "[Contacts2]\n"
    "1111111111111111=Csak Nev\n"
    "2222222222222222=Ket Token;csak@example.com\n"
    "3333333333333333=Negy Token;a@example.com;gaia;plusz\n"
    "4444444444444444=Jo Harom;jo@example.com;gaia-1\n"
)


class TestContactsOf:
    def test_parses_entries(self):
        contacts = contacts_of(parse_document(SAMPLE))
        assert len(contacts) == 2
        assert contacts[0].person_id == "b8e4117cf1d6615b"
        assert contacts[0].name == "Roy Avery"

    def test_a_masodik_es_harmadik_mezo_NEVESITVE_van(self):
        """#2526: a három mező `full_name`, `email`, `gaia_id`."""
        contacts = contacts_of(parse_document(SAMPLE))
        assert contacts[1].name == "Kis Éva"
        assert contacts[1].email == "eva@example.com"
        assert contacts[1].gaia_id == ""

    def test_ures_mezok_ures_sztringek(self):
        contacts = contacts_of(parse_document(SAMPLE))
        assert (contacts[0].email, contacts[0].gaia_id) == ("", "")

    def test_lookup_by_person_id(self):
        contacts = contacts_of(parse_document(SAMPLE))
        by_id = {c.person_id: c for c in contacts}
        assert by_id["8e62b2035b74b477"].name == "Kis Éva"

    def test_no_contacts_section(self):
        assert contacts_of(parse_document("[a.jpg]\nstar=yes\n")) == ()

    def test_empty_contacts_section(self):
        assert contacts_of(parse_document("[Contacts2]\n")) == ()


class TestAHarmasTokenSzabaly:
    """#2526: az eredeti a nem pontosan hármas bejegyzést ELDOBJA."""

    def test_csak_a_HAROM_tokenes_bejegyzes_marad(self):
        contacts = contacts_of(parse_document(ROSSZ_TOKENSZAM))
        assert [c.person_id for c in contacts] == ["4444444444444444"]

    @pytest.mark.parametrize(
        ("sor", "alak"),
        [
            ("1111111111111111=Csak Nev", "egy tokenes"),
            ("2222222222222222=Ket Token;csak@example.com", "két tokenes"),
            ("3333333333333333=Negy;a@e.hu;gaia;plusz", "négy tokenes"),
        ],
    )
    def test_a_rossz_tokenszam_eldobodik(self, sor, alak):
        document = parse_document(f"[Contacts2]\n{sor}\n")
        assert contacts_of(document) == (), (
            f"a(z) {alak} bejegyzés bent maradt — az eredeti eldobja"
        )

    def test_a_HAROM_tokenes_bejegyzes_megmarad(self):
        document = parse_document(
            "[Contacts2]\n5555555555555555=Har Om;h@example.com;gaia-9\n"
        )
        (contact,) = contacts_of(document)
        assert (contact.name, contact.email, contact.gaia_id) == (
            "Har Om", "h@example.com", "gaia-9",
        )

    def test_az_eldobott_bejegyzes_a_DOKUMENTUMBAN_marad(self):
        """A hármas szabály OLVASÁSI szűrő — a fájlt nem írja át.

        Enélkül a round-trip elveszítené a hibás sort, és a felhasználó
        `.picasa.ini`-je némán csonkulna."""
        document = parse_document(ROSSZ_TOKENSZAM)
        assert "1111111111111111=Csak Nev" in document.serialize()


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
