"""albums= CSV hivatkozások + [.album:token] virtuális albumok."""

import pytest

from picasapy.ini import (
    albums_of,
    parse_album_refs,
    parse_document,
    serialize_album_refs,
)

SAMPLE = (
    "[.album:604c294a68b0de9cc9222c4714f289d5]\n"
    "name=Kedvencek\n"
    "token=604c294a68b0de9cc9222c4714f289d5\n"
    "date=2024-07-15T10:30:00+02:00\n"
    "location=Balaton\n"
    "[.album:65d12673f3b51e3fb4b3e330119a76f8]\n"
    "name=Kirándulás\n"
    "token=65d12673f3b51e3fb4b3e330119a76f8\n"
    "[IMG_0001.jpg]\n"
    "albums=604c294a68b0de9cc9222c4714f289d5,65d12673f3b51e3fb4b3e330119a76f8\n"
)


class TestAlbumRefs:
    def test_parse_csv(self):
        refs = parse_album_refs(
            "604c294a68b0de9cc9222c4714f289d5,65d12673f3b51e3fb4b3e330119a76f8"
        )
        assert refs == (
            "604c294a68b0de9cc9222c4714f289d5",
            "65d12673f3b51e3fb4b3e330119a76f8",
        )

    def test_single_ref(self):
        assert parse_album_refs("604c294a68b0de9cc9222c4714f289d5") == (
            "604c294a68b0de9cc9222c4714f289d5",
        )

    def test_empty(self):
        assert parse_album_refs("") == ()

    def test_roundtrip(self):
        value = "604c294a68b0de9cc9222c4714f289d5,65d12673f3b51e3fb4b3e330119a76f8"
        assert serialize_album_refs(parse_album_refs(value)) == value


class TestAlbumsOf:
    def test_finds_album_sections(self):
        albums = albums_of(parse_document(SAMPLE))
        assert [a.token for a in albums] == [
            "604c294a68b0de9cc9222c4714f289d5",
            "65d12673f3b51e3fb4b3e330119a76f8",
        ]

    def test_fields(self):
        album = albums_of(parse_document(SAMPLE))[0]
        assert album.name == "Kedvencek"
        assert album.date == "2024-07-15T10:30:00+02:00"
        assert album.location == "Balaton"
        assert album.description is None

    def test_missing_optional_fields_are_none(self):
        album = albums_of(parse_document(SAMPLE))[1]
        assert album.name == "Kirándulás"
        assert album.date is None
        assert album.location is None

    def test_token_from_section_name_wins(self):
        # A szekciónévbeli token az azonosító akkor is, ha a token= kulcs hiányzik.
        doc = parse_document("[.album:abc123]\nname=X\n")
        assert albums_of(doc)[0].token == "abc123"

    def test_no_albums(self):
        assert albums_of(parse_document("[a.jpg]\nstar=yes\n")) == ()


class TestImmutability:
    def test_album_is_frozen(self):
        album = albums_of(parse_document(SAMPLE))[0]
        with pytest.raises(AttributeError):
            album.name = "Más"
