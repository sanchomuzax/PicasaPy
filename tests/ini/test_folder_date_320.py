"""#320: mappa-dátum kézi felülírása a `.picasa.ini` `[Picasa]` `date=`
kulcsán — PicasaPy-kiterjesztés (ld. `docs/specs/picasa-ini-format.md`)."""

from __future__ import annotations

from picasapy.ini import (
    parse_document,
    read_folder_date_override,
    with_folder_date_override,
    without_folder_date_override,
)


class TestReadOverride:
    def test_missing_picasa_section_yields_none(self):
        document = parse_document("[IMG_0001.jpg]\nstar=yes\n")
        assert read_folder_date_override(document) is None

    def test_missing_date_key_yields_none(self):
        document = parse_document("[Picasa]\nname=Nyaralás\n")
        assert read_folder_date_override(document) is None

    def test_valid_iso_date_is_returned(self):
        document = parse_document("[Picasa]\ndate=2019-07-04\n")
        assert read_folder_date_override(document) == "2019-07-04"

    def test_invalid_date_format_yields_none(self):
        """Nem-ISO érték (pl. a jövőben más célra beírt kulcs) ne törje el a
        felolvasást — a hívó ilyenkor a számított dátumra esik vissza."""
        document = parse_document("[Picasa]\ndate=nem-datum\n")
        assert read_folder_date_override(document) is None


class TestWriteOverride:
    def test_with_override_adds_picasa_section(self):
        document = parse_document("[IMG_0001.jpg]\nstar=yes\n")
        updated = with_folder_date_override(document, "2020-01-15")
        assert read_folder_date_override(updated) == "2020-01-15"

    def test_with_override_replaces_existing_value(self):
        document = parse_document("[Picasa]\ndate=2019-01-01\nname=x\n")
        updated = with_folder_date_override(document, "2021-12-31")
        assert read_folder_date_override(updated) == "2021-12-31"
        assert updated.section("Picasa").get("name") == "x"  # a többi kulcs érintetlen

    def test_round_trip_preserves_unrelated_keys(self):
        raw = "[encoding]\r\nutf8=1\r\n\r\n[Picasa]\r\nname=Nyár\r\n"
        document = parse_document(raw)
        updated = with_folder_date_override(document, "2022-06-01")
        assert "utf8=1" in updated.serialize()
        assert "name=Nyár" in updated.serialize()
        assert "date=2022-06-01" in updated.serialize()

    def test_without_override_removes_key_only(self):
        document = parse_document("[Picasa]\ndate=2019-01-01\nname=x\n")
        cleared = without_folder_date_override(document)
        assert read_folder_date_override(cleared) is None
        assert cleared.section("Picasa").get("name") == "x"

    def test_without_override_on_missing_key_is_noop(self):
        document = parse_document("[Picasa]\nname=x\n")
        cleared = without_folder_date_override(document)
        assert cleared.section("Picasa").get("name") == "x"
