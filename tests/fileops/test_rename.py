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


def _patch_update_with_intruder(monkeypatch, intrude):
    """Az ELSŐ `mutate`-hívás közben egy „idegen író" (a párhuzamosan futó
    eredeti Picasa) belenyúl az ini-be — ez kényszeríti ki az
    `update_document` ütközés-újrajátszását. Ha az átnevezés NEM az
    `update_document`-en menne át (#295), a becsempészett sor elveszne."""
    from picasapy.fileops import rename as rename_module
    from picasapy.ini import update_document as real_update_document

    def patched(path, mutate, **kwargs):
        calls = {"n": 0}

        def wrapped(document):
            calls["n"] += 1
            if calls["n"] == 1:
                intrude()
            return mutate(document)

        return real_update_document(path, wrapped, **kwargs)

    monkeypatch.setattr(rename_module, "update_document", patched)


class TestConcurrentIniWriter:
    """#295: az átnevezés ini-írása ütközésbiztos (a #137-es minta szerint) —
    a párhuzamosan futó eredeti Picasa írása nem veszhet el."""

    def test_foreign_writer_change_survives(self, tmp_path, monkeypatch):
        from picasapy.ini import save_document

        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        ini = tmp_path / ".picasa.ini"
        ini.write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")

        def intrude():
            save_document(
                load_document(ini).with_value("c.jpg", "caption", "picasa"), ini
            )

        _patch_update_with_intruder(monkeypatch, intrude)
        rename_photo(photo, "b.jpg")

        document = load_document(ini)
        assert document.section("a.jpg") is None
        assert document.section("b.jpg").get("star") == "yes"  # a miénk
        assert document.section("c.jpg").get("caption") == "picasa"  # az idegen íróé

    def test_target_section_taken_meanwhile_raises_file_exists(
        self, tmp_path, monkeypatch
    ):
        """Ha az idegen író közben elfoglalja a célnevet, a szerződés szerinti
        FileExistsError jön — az üzenet megmondja, hogy a fájl már át van
        nevezve, és hol maradt a metaadat."""
        from picasapy.ini import save_document

        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        ini = tmp_path / ".picasa.ini"
        ini.write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")

        def intrude():
            save_document(load_document(ini).with_value("b.jpg", "star", "no"), ini)

        _patch_update_with_intruder(monkeypatch, intrude)
        with pytest.raises(FileExistsError) as excinfo:
            rename_photo(photo, "b.jpg")

        assert (tmp_path / "b.jpg").exists()  # a fájl már át van nevezve
        assert "b.jpg" in str(excinfo.value)
        assert "a.jpg" in str(excinfo.value)
