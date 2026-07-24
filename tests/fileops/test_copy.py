"""copy_photo: másolás másik mappába, a forrás érintetlenül marad (#23).

A `test_move.py` mintáját követi, kiegészítve az ütközés-feloldás (nem
felülíró, `név-1.jpg` stílusú átnevezés) esetére, mivel a copy — a
move-tól eltérően — sosem hibázhat egyszerű névütközésen: a forrás
(kártya/mappa) tartalma bármikor újra bemásolható legyen.
"""

import pytest

from picasapy.fileops import copy_photo
from picasapy.ini import load_document


class TestCopyPhoto:
    def test_copies_file_on_disk_and_keeps_source(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"kep")
        new_path = copy_photo(photo, dest)
        assert new_path == dest / "a.jpg"
        assert new_path.read_bytes() == b"kep"
        assert photo.exists()  # a forrás ÉRINTETLEN (nem-destruktív alapértelmezés)

    def test_ini_section_is_copied_with_full_fidelity(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"kep")
        (src / ".picasa.ini").write_text(
            "[a.jpg]\n; komment\nstar=yes\nfilters=enhance=1;\n", encoding="utf-8"
        )
        copy_photo(photo, dest)

        # a forrás ini-je is változatlan marad (nem move_photo!)
        source_doc = load_document(src / ".picasa.ini")
        assert source_doc.section("a.jpg").get("star") == "yes"

        dest_doc = load_document(dest / ".picasa.ini")
        copied = dest_doc.section("a.jpg")
        assert copied.get("star") == "yes"
        assert copied.get("filters") == "enhance=1;"
        assert "; komment" in dest_doc.serialize()

    def test_dest_ini_other_sections_untouched(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"kep")
        (src / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        (dest / ".picasa.ini").write_text("[x.jpg]\nstar=no\n", encoding="utf-8")
        copy_photo(photo, dest)
        dest_doc = load_document(dest / ".picasa.ini")
        assert dest_doc.section("x.jpg").get("star") == "no"
        assert dest_doc.section("a.jpg").get("star") == "yes"

    def test_no_source_ini_is_fine(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"kep")
        new_path = copy_photo(photo, dest)
        assert new_path.exists()
        assert not (dest / ".picasa.ini").exists()

    def test_missing_source_raises(self, tmp_path):
        dest = tmp_path / "cel"
        dest.mkdir()
        with pytest.raises(FileNotFoundError):
            copy_photo(tmp_path / "nincs.jpg", dest)

    def test_missing_dest_folder_raises(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        with pytest.raises(FileNotFoundError):
            copy_photo(photo, tmp_path / "nincs-mappa")

    def test_dest_not_a_directory_raises(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        not_a_dir = tmp_path / "fajl.txt"
        not_a_dir.write_text("x")
        with pytest.raises(NotADirectoryError):
            copy_photo(photo, not_a_dir)

    def test_target_name_collision_gets_non_overwriting_suffix(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"uj")
        (dest / "a.jpg").write_bytes(b"regi")
        new_path = copy_photo(photo, dest)
        assert new_path == dest / "a-1.jpg"
        assert (dest / "a.jpg").read_bytes() == b"regi"  # a régi NEM íródott felül
        assert new_path.read_bytes() == b"uj"

    def test_repeated_collisions_increment_the_suffix(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"uj")
        (dest / "a.jpg").write_bytes(b"x")
        (dest / "a-1.jpg").write_bytes(b"x")
        new_path = copy_photo(photo, dest)
        assert new_path == dest / "a-2.jpg"

    def test_collision_ini_section_header_follows_the_renamed_file(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"uj")
        (src / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        (dest / "a.jpg").write_bytes(b"regi")

        new_path = copy_photo(photo, dest)

        assert new_path == dest / "a-1.jpg"
        dest_doc = load_document(dest / ".picasa.ini")
        assert dest_doc.section("a.jpg") is None
        assert dest_doc.section("a-1.jpg").get("star") == "yes"
