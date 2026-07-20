""".picasa.ini dokumentum parse + byte-pontos round-trip."""

import pytest

from picasapy.ini import parse_document

SAMPLE = (
    "[Picasa]\r\n"
    "name=Nyaralás 2024\r\n"
    "\r\n"
    "[Contacts2]\r\n"
    "b8e4117cf1d6615b=Roy Avery;;\r\n"
    "\r\n"
    "[IMG_0001.jpg]\r\n"
    "star=yes\r\n"
    "filters=sat=1,-1.000000;\r\n"
    "backuphash=36003\r\n"
    "\r\n"
    "[.album:604c294a68b0de9cc9222c4714f289d5]\r\n"
    "name=Kedvencek\r\n"
    "token=604c294a68b0de9cc9222c4714f289d5\r\n"
)


class TestParse:
    def test_section_names(self):
        doc = parse_document(SAMPLE)
        assert [s.name for s in doc.sections] == [
            "Picasa",
            "Contacts2",
            "IMG_0001.jpg",
            ".album:604c294a68b0de9cc9222c4714f289d5",
        ]

    def test_get_value(self):
        doc = parse_document(SAMPLE)
        assert doc.section("IMG_0001.jpg").get("star") == "yes"

    def test_get_is_case_insensitive(self):
        doc = parse_document(SAMPLE)
        assert doc.section("IMG_0001.jpg").get("STAR") == "yes"

    def test_missing_section_and_key(self):
        doc = parse_document(SAMPLE)
        assert doc.section("nincs.jpg") is None
        assert doc.section("Picasa").get("nincs") is None

    def test_value_split_at_first_equals(self):
        # A filters= érték maga is tartalmaz '='-t.
        doc = parse_document(SAMPLE)
        assert doc.section("IMG_0001.jpg").get("filters") == "sat=1,-1.000000;"

    def test_items_order(self):
        doc = parse_document(SAMPLE)
        keys = [k for k, _ in doc.section("IMG_0001.jpg").items()]
        assert keys == ["star", "filters", "backuphash"]

    def test_duplicate_keys_preserved(self):
        doc = parse_document("[a.jpg]\nk=1\nk=2\n")
        assert doc.section("a.jpg").items() == (("k", "1"), ("k", "2"))
        assert doc.section("a.jpg").get("k") == "1"

    def test_special_vs_file_sections(self):
        doc = parse_document(SAMPLE)
        assert doc.section("Picasa").is_special
        assert doc.section("Contacts2").is_special
        assert doc.section(".album:604c294a68b0de9cc9222c4714f289d5").is_special
        assert not doc.section("IMG_0001.jpg").is_special
        assert [s.name for s in doc.file_sections()] == ["IMG_0001.jpg"]

    def test_empty_document(self):
        doc = parse_document("")
        assert doc.sections == ()


class TestRoundTrip:
    def test_crlf_byte_exact(self):
        assert parse_document(SAMPLE).serialize() == SAMPLE

    def test_lf_byte_exact(self):
        text = SAMPLE.replace("\r\n", "\n")
        assert parse_document(text).serialize() == text

    def test_u0085_inside_value_does_not_split_line(self):
        # #133: regi (CP125x) fajl latin-1-kent betoltve -- a NEL bajtja
        # (0x85) U+0085 kodpontta dekodolodik. A str.splitlines() ezt
        # sorvegnek venne (fantomszekcio/csonka caption); a parse_document
        # sortordelese csak '\n'/'\r\n' menten tortenhet.
        text = "[a.jpg]\ncaption=Hello" + chr(0x0085) + "World\nstar=yes\n"
        doc = parse_document(text)
        assert doc.serialize() == text
        assert doc.section("a.jpg").get("caption") == "Hello" + chr(0x0085) + "World"
        assert doc.section("a.jpg").get("star") == "yes"
        assert [s.name for s in doc.sections] == ["a.jpg"]

    def test_u2028_inside_value_does_not_split_line(self):
        # Ugyanaz a hiba mas Unicode sorhatar-kodponttal (U+2028).
        text = "[a.jpg]\ncaption=Elso" + chr(0x2028) + "Masodik\nstar=yes\n"
        doc = parse_document(text)
        assert doc.serialize() == text
        assert doc.section("a.jpg").get("caption") == "Elso" + chr(0x2028) + "Masodik"
        assert [s.name for s in doc.sections] == ["a.jpg"]

    def test_verbatim_garbage_preserved(self):
        # Round-trip elv: amit nem értünk, változatlanul visszaírjuk.
        text = "; komment\n[a.jpg]\nstar=yes\nvalami kulcs nélkül\n"
        assert parse_document(text).serialize() == text

    def test_preamble_before_first_section(self):
        text = "kósza sor\n\n[a.jpg]\nstar=yes\n"
        assert parse_document(text).serialize() == text

    def test_empty_roundtrip(self):
        assert parse_document("").serialize() == ""


class TestWithValue:
    def test_update_existing_key(self):
        doc = parse_document(SAMPLE)
        new = doc.with_value("IMG_0001.jpg", "star", "no")
        assert new.section("IMG_0001.jpg").get("star") == "no"
        assert new.serialize() == SAMPLE.replace("star=yes", "star=no")

    def test_original_unchanged(self):
        doc = parse_document(SAMPLE)
        doc.with_value("IMG_0001.jpg", "star", "no")
        assert doc.section("IMG_0001.jpg").get("star") == "yes"
        assert doc.serialize() == SAMPLE

    def test_add_key_after_last_entry(self):
        doc = parse_document(SAMPLE)
        new = doc.with_value("IMG_0001.jpg", "rotate", "rotate(1)")
        expected = SAMPLE.replace(
            "backuphash=36003\r\n", "backuphash=36003\r\nrotate=rotate(1)\r\n"
        )
        assert new.serialize() == expected

    def test_create_missing_section(self):
        doc = parse_document("[a.jpg]\nstar=yes\n")
        new = doc.with_value("b.jpg", "star", "yes")
        assert new.section("b.jpg").get("star") == "yes"
        assert new.serialize() == "[a.jpg]\nstar=yes\n[b.jpg]\nstar=yes\n"

    def test_update_only_first_duplicate(self):
        doc = parse_document("[a.jpg]\nk=1\nk=2\n")
        new = doc.with_value("a.jpg", "k", "9")
        assert new.section("a.jpg").items() == (("k", "9"), ("k", "2"))

    def test_add_section_closes_unterminated_last_line(self):
        doc = parse_document("[a.jpg]\nstar=yes")
        new = doc.with_value("b.jpg", "star", "yes")
        assert new.serialize() == "[a.jpg]\nstar=yes\n[b.jpg]\nstar=yes\n"

    def test_add_section_after_header_only_section(self):
        doc = parse_document("[a.jpg]")
        new = doc.with_value("b.jpg", "star", "yes")
        assert new.serialize() == "[a.jpg]\n[b.jpg]\nstar=yes\n"

    def test_add_key_to_unterminated_header_only_section(self):
        # A fejléc sorvégjel nélkül ér véget: a kulcs nem ragadhat rá.
        doc = parse_document("[a.jpg]")
        new = doc.with_value("a.jpg", "star", "yes")
        assert new.serialize() == "[a.jpg]\nstar=yes\n"

    def test_add_key_to_header_only_section(self):
        doc = parse_document("[a.jpg]\n")
        new = doc.with_value("a.jpg", "star", "yes")
        assert new.serialize() == "[a.jpg]\nstar=yes\n"

    def test_empty_document_gets_section(self):
        new = parse_document("").with_value("a.jpg", "star", "yes")
        assert new.serialize() == "[a.jpg]\nstar=yes\n"


class TestWithRemoved:
    def test_removes_key_line(self):
        doc = parse_document(SAMPLE)
        new = doc.with_removed("IMG_0001.jpg", "star")
        assert new.section("IMG_0001.jpg").get("star") is None
        assert new.serialize() == SAMPLE.replace("star=yes\r\n", "")

    def test_other_content_untouched(self):
        # Round-trip elv: csak az adott sor tűnhet el, minden más bitre pontos.
        doc = parse_document(SAMPLE)
        new = doc.with_removed("IMG_0001.jpg", "star")
        assert new.section("IMG_0001.jpg").get("filters") == "sat=1,-1.000000;"
        assert new.section("Picasa").get("name") == "Nyaralás 2024"

    def test_missing_key_returns_same_document(self):
        doc = parse_document(SAMPLE)
        assert doc.with_removed("IMG_0001.jpg", "nincs") is doc

    def test_missing_section_returns_same_document(self):
        doc = parse_document(SAMPLE)
        assert doc.with_removed("nincs.jpg", "star") is doc

    def test_removes_only_first_duplicate(self):
        doc = parse_document("[a.jpg]\nk=1\nk=2\n")
        new = doc.with_removed("a.jpg", "k")
        assert new.serialize() == "[a.jpg]\nk=2\n"

    def test_original_unchanged(self):
        doc = parse_document(SAMPLE)
        doc.with_removed("IMG_0001.jpg", "star")
        assert doc.serialize() == SAMPLE

    def test_case_insensitive_key(self):
        doc = parse_document("[a.jpg]\nStar=yes\nk=1\n")
        new = doc.with_removed("a.jpg", "star")
        assert new.serialize() == "[a.jpg]\nk=1\n"

    def test_emptied_section_is_dropped(self):
        # Az utolsó kulcs törlésével az (általunk létrehozott) szekció is
        # eltűnik — így a fel+le csillagozás bitre pontos round-trip.
        doc = parse_document("[a.jpg]\nstar=yes\n[b.jpg]\nk=1\n")
        new = doc.with_removed("a.jpg", "star")
        assert new.serialize() == "[b.jpg]\nk=1\n"

    def test_section_with_comment_kept(self):
        # Ismeretlen/verbatim sort tartalmazó szekciót nem dobunk el.
        doc = parse_document("[a.jpg]\n; komment\nstar=yes\n")
        new = doc.with_removed("a.jpg", "star")
        assert new.serialize() == "[a.jpg]\n; komment\n"


class TestWithRenamedSection:
    """#15: fájl-átnevezéskor a szekciónév követi, a tartalom bitre pontos."""

    def test_renames_header_keeps_content(self):
        doc = parse_document(SAMPLE)
        new = doc.with_renamed_section("IMG_0001.jpg", "IMG_0002.jpg")
        assert new.section("IMG_0001.jpg") is None
        renamed = new.section("IMG_0002.jpg")
        assert renamed is not None
        assert renamed.get("star") == "yes"
        assert renamed.get("filters") == "sat=1,-1.000000;"
        assert renamed.get("backuphash") == "36003"

    def test_serialized_header_updated(self):
        doc = parse_document("[a.jpg]\nstar=yes\n")
        new = doc.with_renamed_section("a.jpg", "b.jpg")
        assert new.serialize() == "[b.jpg]\nstar=yes\n"

    def test_missing_section_returns_same_document(self):
        doc = parse_document(SAMPLE)
        assert doc.with_renamed_section("nincs.jpg", "b.jpg") is doc

    def test_collision_raises(self):
        doc = parse_document("[a.jpg]\nstar=yes\n[b.jpg]\nk=1\n")
        with pytest.raises(ValueError):
            doc.with_renamed_section("a.jpg", "b.jpg")

    def test_comment_and_unknown_lines_preserved(self):
        doc = parse_document("[a.jpg]\n; komment\nstar=yes\nfuture_key=42\n")
        new = doc.with_renamed_section("a.jpg", "b.jpg")
        assert new.serialize() == "[b.jpg]\n; komment\nstar=yes\nfuture_key=42\n"

    def test_original_unchanged(self):
        doc = parse_document(SAMPLE)
        doc.with_renamed_section("IMG_0001.jpg", "IMG_0002.jpg")
        assert doc.serialize() == SAMPLE

    def test_other_sections_untouched(self):
        doc = parse_document(SAMPLE)
        new = doc.with_renamed_section("IMG_0001.jpg", "IMG_0002.jpg")
        assert new.section("Picasa").get("name") == "Nyaralás 2024"


class TestWithSection:
    """#15: teljes szekció átvitele egyik dokumentumból a másikba (áthelyezés)."""

    def test_appends_section_with_full_fidelity(self):
        source = parse_document("[a.jpg]\n; komment\nstar=yes\nfilters=enhance=1;\n")
        dest = parse_document("[b.jpg]\nk=1\n")
        moved = dest.with_section(source.section("a.jpg"))
        assert moved.serialize() == (
            "[b.jpg]\nk=1\n[a.jpg]\n; komment\nstar=yes\nfilters=enhance=1;\n"
        )

    def test_replaces_existing_section_of_same_name(self):
        source = parse_document("[a.jpg]\nstar=yes\n")
        dest = parse_document("[a.jpg]\nk=old\n")
        moved = dest.with_section(source.section("a.jpg"))
        assert moved.section("a.jpg").get("star") == "yes"
        assert moved.section("a.jpg").get("k") is None

    def test_into_empty_document(self):
        source = parse_document("[a.jpg]\nstar=yes\n")
        moved = parse_document("").with_section(source.section("a.jpg"))
        assert moved.serialize() == "[a.jpg]\nstar=yes\n"


class TestWithoutSection:
    """#15: teljes szekció eltávolítása (áthelyezéskor a forrás iniből)."""

    def test_removes_whole_section(self):
        doc = parse_document(SAMPLE)
        new = doc.without_section("IMG_0001.jpg")
        assert new.section("IMG_0001.jpg") is None
        assert new.section("Picasa") is not None

    def test_missing_section_returns_same_document(self):
        doc = parse_document(SAMPLE)
        assert doc.without_section("nincs.jpg") is doc

    def test_serialize_drops_header_and_lines(self):
        doc = parse_document("[a.jpg]\nstar=yes\n[b.jpg]\nk=1\n")
        new = doc.without_section("a.jpg")
        assert new.serialize() == "[b.jpg]\nk=1\n"
