"""#4839: a megőrzött Originals/Picasa.ini szekciója is átkerül."""

from __future__ import annotations

from picasapy.fileops import move_photo
from picasapy.ini import load_or_empty
from picasapy.ini.names import INI_NAME, LEGACY_INI_NAME


def test_originals_legacy_ini_section_moves_without_writing_legacy_file(tmp_path):
    source = tmp_path / "forras"
    source.mkdir()
    photo = source / "kep.jpg"
    photo.write_bytes(b"szerkesztett")
    originals = source / "Originals"
    originals.mkdir()
    (originals / photo.name).write_bytes(b"eredeti")
    legacy_ini = originals / LEGACY_INI_NAME
    legacy_bytes = (
        b"[kep.jpg]\nstar=yes\ncaption=eredeti felirat\n\n"
        b"[masik.jpg]\nstar=no\n"
    )
    legacy_ini.write_bytes(legacy_bytes)
    destination = tmp_path / "cel"
    destination.mkdir()

    move_photo(photo, destination)

    moved_ini = destination / "Originals" / INI_NAME
    moved_document = load_or_empty(moved_ini)
    section = moved_document.section("kep.jpg")
    assert section is not None
    assert section.get("star") == "yes"
    assert section.get("caption") == "eredeti felirat"
    source_document = load_or_empty(originals / INI_NAME)
    assert source_document.section("kep.jpg") is None
    assert source_document.section("masik.jpg").get("star") == "no"
    assert legacy_ini.read_bytes() == legacy_bytes
