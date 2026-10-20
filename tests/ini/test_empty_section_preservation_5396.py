"""A Picasa csillaglevételkor üres képszakaszt hagy a fájlban (#5396)."""

from picasapy.ini import parse_document


def test_kulcs_torlese_megtarthatja_az_ures_szakaszt():
    document = parse_document("[7.jpg]\r\nstar=yes\r\n")

    updated = document.with_removed_preserving_section("7.jpg", "star")

    section = updated.section("7.jpg")
    assert section is not None
    assert section.lines == ()
    assert updated.serialize() == "[7.jpg]\r\n"
