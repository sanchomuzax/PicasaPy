"""move_photo: áthelyezés másik mappába, az ini-szekció átvitelével (#15)."""

import pytest

from picasapy.fileops import move_photo
from picasapy.ini import load_document


class TestMovePhoto:
    def test_moves_file_on_disk(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"kep")
        new_path = move_photo(photo, dest)
        assert new_path == dest / "a.jpg"
        assert new_path.exists()
        assert not photo.exists()

    def test_ini_section_moves_with_full_fidelity(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"kep")
        (src / ".picasa.ini").write_text(
            "[a.jpg]\n; komment\nstar=yes\nfilters=enhance=1;\n", encoding="utf-8"
        )
        move_photo(photo, dest)
        source_doc = load_document(src / ".picasa.ini")
        assert source_doc.section("a.jpg") is None
        dest_doc = load_document(dest / ".picasa.ini")
        moved = dest_doc.section("a.jpg")
        assert moved.get("star") == "yes"
        assert moved.get("filters") == "enhance=1;"
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
        move_photo(photo, dest)
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
        new_path = move_photo(photo, dest)
        assert new_path.exists()
        assert not (dest / ".picasa.ini").exists()

    def test_missing_source_raises(self, tmp_path):
        dest = tmp_path / "cel"
        dest.mkdir()
        with pytest.raises(FileNotFoundError):
            move_photo(tmp_path / "nincs.jpg", dest)

    def test_missing_dest_folder_raises(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        with pytest.raises(FileNotFoundError):
            move_photo(photo, tmp_path / "nincs-mappa")

    def test_dest_not_a_directory_raises(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        not_a_dir = tmp_path / "fajl.txt"
        not_a_dir.write_text("x")
        with pytest.raises(NotADirectoryError):
            move_photo(photo, not_a_dir)

    def test_target_file_exists_raises(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"kep")
        (dest / "a.jpg").write_bytes(b"mar-van")
        with pytest.raises(FileExistsError):
            move_photo(photo, dest)
        assert photo.exists()

    def test_target_ini_section_exists_raises_without_moving_file(self, tmp_path):
        src = tmp_path / "forras"
        dest = tmp_path / "cel"
        src.mkdir()
        dest.mkdir()
        photo = src / "a.jpg"
        photo.write_bytes(b"kep")
        (src / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        (dest / ".picasa.ini").write_text("[a.jpg]\nstar=no\n", encoding="utf-8")
        with pytest.raises(FileExistsError):
            move_photo(photo, dest)
        assert photo.exists()
        assert not (dest / "a.jpg").exists()
