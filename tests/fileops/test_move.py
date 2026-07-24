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


def _patch_update_with_intruder(monkeypatch, intrude):
    """Minden érintett ini ELSŐ `mutate`-hívása közben egy „idegen író" (a
    párhuzamosan futó eredeti Picasa) belenyúl a fájlba — ez kényszeríti ki az
    `update_document` ütközés-újrajátszását. Ha az áthelyezés NEM az
    `update_document`-en menne át (#295), a becsempészett sor elveszne."""
    from pathlib import Path

    from picasapy.fileops import move as move_module
    from picasapy.ini import update_document as real_update_document

    seen: set[str] = set()

    def patched(path, mutate, **kwargs):
        def wrapped(document):
            if str(path) not in seen:
                seen.add(str(path))
                intrude(Path(path))
            return mutate(document)

        return real_update_document(path, wrapped, **kwargs)

    monkeypatch.setattr(move_module, "update_document", patched)


@pytest.fixture
def folders(tmp_path):
    """Forrás- és célmappa egy áthelyezendő, ini-bejegyzéssel bíró fotóval."""
    src = tmp_path / "forras"
    dest = tmp_path / "cel"
    src.mkdir()
    dest.mkdir()
    (src / "a.jpg").write_bytes(b"kep")
    (src / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
    return src, dest


class TestConcurrentIniWriter:
    """#295: MINDKÉT ini-írás ütközésbiztos (a #137-es minta szerint) — a
    párhuzamosan futó eredeti Picasa írása egyik mappában sem veszhet el."""

    def test_foreign_writer_changes_survive_in_both_inis(
        self, folders, monkeypatch
    ):
        from picasapy.ini import load_or_empty, save_document

        src, dest = folders
        (dest / ".picasa.ini").write_text("[x.jpg]\nstar=no\n", encoding="utf-8")

        def intrude(ini_path):
            save_document(
                load_or_empty(ini_path).with_value(
                    "idegen.jpg", "caption", ini_path.parent.name
                ),
                ini_path,
            )

        _patch_update_with_intruder(monkeypatch, intrude)
        move_photo(src / "a.jpg", dest)

        source_doc = load_document(src / ".picasa.ini")
        dest_doc = load_document(dest / ".picasa.ini")
        assert source_doc.section("a.jpg") is None  # a miénk (takarítás)
        assert source_doc.section("idegen.jpg").get("caption") == "forras"
        assert dest_doc.section("a.jpg").get("star") == "yes"  # a miénk (átvitel)
        assert dest_doc.section("idegen.jpg").get("caption") == "cel"
        assert dest_doc.section("x.jpg").get("star") == "no"

    def test_replay_carries_freshly_read_source_section(self, folders, monkeypatch):
        """Újrajátszáskor a FRISS forrás-tartalom kerül át: ha az idegen író a
        cél-ini mellett a forrás szekcióhoz feliratot is ad, az sem veszik el."""
        from picasapy.ini import load_or_empty, save_document

        src, dest = folders
        source_ini = src / ".picasa.ini"
        dest_ini = dest / ".picasa.ini"

        def intrude(ini_path):
            if ini_path != dest_ini:
                return
            # A cél-ini módosítása kényszeríti ki az újrajátszást, a
            # forrásé pedig azt, hogy legyen mit „frissen" átvinni.
            save_document(load_or_empty(dest_ini).with_value("z.jpg", "star", "yes"), dest_ini)
            save_document(
                load_or_empty(source_ini).with_value("a.jpg", "caption", "friss"),
                source_ini,
            )

        _patch_update_with_intruder(monkeypatch, intrude)
        move_photo(src / "a.jpg", dest)

        moved = load_document(dest_ini).section("a.jpg")
        assert moved.get("star") == "yes"
        assert moved.get("caption") == "friss"

    def test_dest_ini_write_failure_keeps_metadata_in_source(
        self, folders, monkeypatch
    ):
        """Ha a cél-ini írása bukik, a metaadat a forrásmappában marad (nem
        vész el), és a hiba cselekvésre fordítható üzenettel jön a felszínre."""
        from pathlib import Path

        from picasapy.fileops import move as move_module
        from picasapy.ini import IniConflictError
        from picasapy.ini import update_document as real_update_document

        src, dest = folders
        dest_ini = dest / ".picasa.ini"

        def patched(path, mutate, **kwargs):
            if Path(path) == dest_ini:
                raise IniConflictError("teszt: a cél-ini nem írható")
            return real_update_document(path, mutate, **kwargs)

        monkeypatch.setattr(move_module, "update_document", patched)

        with pytest.raises(IniConflictError) as excinfo:
            move_photo(src / "a.jpg", dest)

        assert (dest / "a.jpg").exists()  # a fájl már átkerült
        assert not (src / "a.jpg").exists()
        # A bejegyzés a forrásban maradt — visszakereshető, nem veszett el.
        assert load_document(src / ".picasa.ini").section("a.jpg").get("star") == "yes"
        message = str(excinfo.value)
        assert str(dest / "a.jpg") in message
        assert str(src / ".picasa.ini") in message
