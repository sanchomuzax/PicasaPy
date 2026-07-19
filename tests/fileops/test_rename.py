"""rename_photo: átnevezés a lemezen, az ini-szekció követésével (#15)."""

import pytest

from picasapy.fileops import rename_photo
from picasapy.ini import load_document


class TestRenamePhoto:
    def test_renames_file_on_disk(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        new_path = rename_photo(photo, "b.jpg")
        assert new_path == tmp_path / "b.jpg"
        assert new_path.exists()
        assert not photo.exists()

    def test_ini_section_follows_rename(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        ini = tmp_path / ".picasa.ini"
        ini.write_text("[a.jpg]\nstar=yes\nfilters=enhance=1;\n", encoding="utf-8")
        rename_photo(photo, "b.jpg")
        document = load_document(ini)
        assert document.section("a.jpg") is None
        renamed = document.section("b.jpg")
        assert renamed.get("star") == "yes"
        assert renamed.get("filters") == "enhance=1;"

    def test_no_ini_present_is_fine(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        new_path = rename_photo(photo, "b.jpg")
        assert new_path.exists()
        assert not (tmp_path / ".picasa.ini").exists()

    def test_other_sections_untouched(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        (tmp_path / "c.jpg").write_bytes(b"masik")
        ini = tmp_path / ".picasa.ini"
        ini.write_text("[a.jpg]\nstar=yes\n[c.jpg]\nstar=no\n", encoding="utf-8")
        rename_photo(photo, "b.jpg")
        document = load_document(ini)
        assert document.section("c.jpg").get("star") == "no"

    def test_missing_source_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            rename_photo(tmp_path / "nincs.jpg", "b.jpg")

    def test_target_file_exists_raises(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        (tmp_path / "b.jpg").write_bytes(b"mar-van")
        with pytest.raises(FileExistsError):
            rename_photo(photo, "b.jpg")
        assert photo.exists()  # nem történt semmi

    def test_target_ini_section_exists_raises_without_renaming_file(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        ini = tmp_path / ".picasa.ini"
        ini.write_text("[a.jpg]\nstar=yes\n[b.jpg]\nstar=no\n", encoding="utf-8")
        with pytest.raises(FileExistsError):
            rename_photo(photo, "b.jpg")
        assert photo.exists()
        assert not (tmp_path / "b.jpg").exists()

    @pytest.mark.parametrize("bad_name", ["", ".", "..", "al/könyvtár.jpg", "a\\b.jpg"])
    def test_invalid_name_raises(self, tmp_path, bad_name):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        with pytest.raises(ValueError):
            rename_photo(photo, bad_name)
