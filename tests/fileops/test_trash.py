"""delete_to_trash: freedesktop.org Trash-specifikáció (#15)."""

import urllib.parse

import pytest

from picasapy.fileops import delete_to_trash


class TestDeleteToTrash:
    def test_moves_file_into_trash_files_dir(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        trash_dir = tmp_path / "Trash"
        trashed = delete_to_trash(photo, trash_dir=trash_dir)
        assert trashed == trash_dir / "files" / "a.jpg"
        assert trashed.exists()
        assert not photo.exists()

    def test_writes_trashinfo_with_path_and_date(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        trash_dir = tmp_path / "Trash"
        delete_to_trash(photo, trash_dir=trash_dir)
        info = (trash_dir / "info" / "a.jpg.trashinfo").read_text(encoding="utf-8")
        assert info.startswith("[Trash Info]\n")
        assert f"Path={urllib.parse.quote(str(photo.resolve()))}" in info
        assert "DeletionDate=" in info

    def test_name_collision_gets_unique_suffix(self, tmp_path):
        trash_dir = tmp_path / "Trash"
        (trash_dir / "files").mkdir(parents=True)
        (trash_dir / "files" / "a.jpg").write_bytes(b"korabbi")
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"uj")
        trashed = delete_to_trash(photo, trash_dir=trash_dir)
        assert trashed == trash_dir / "files" / "a_1.jpg"
        assert (trash_dir / "info" / "a_1.jpg.trashinfo").exists()

    def test_creates_trash_dirs_if_missing(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        trash_dir = tmp_path / "meg-nem-letezik"
        delete_to_trash(photo, trash_dir=trash_dir)
        assert (trash_dir / "files").is_dir()
        assert (trash_dir / "info").is_dir()

    def test_missing_source_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            delete_to_trash(tmp_path / "nincs.jpg", trash_dir=tmp_path / "Trash")

    def test_default_trash_dir_uses_xdg_data_home(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        trashed = delete_to_trash(photo)
        assert trashed == tmp_path / "xdg" / "Trash" / "files" / "a.jpg"

    def test_trashinfo_exists_before_move_completes(self, tmp_path, monkeypatch):
        # freedesktop-spec: az info-fájlnak a move ELŐTT kell léteznie —
        # tele lemeznél / megszakadt move-nál ne maradjon "árva" fájl.
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        trash_dir = tmp_path / "Trash"

        seen_before_move = {}
        original_move = __import__("shutil").move

        def spy_move(src, dst):
            info_path = trash_dir / "info" / "a.jpg.trashinfo"
            seen_before_move["exists"] = info_path.exists()
            return original_move(src, dst)

        monkeypatch.setattr("picasapy.fileops.trash.shutil.move", spy_move)
        delete_to_trash(photo, trash_dir=trash_dir)
        assert seen_before_move["exists"] is True

    def test_trashinfo_created_exclusively(self, tmp_path):
        # kizárólagos létrehozás: ha az info-fájl már létezik (race), a
        # függvény nem írja felül, hanem másik célnevet választ
        trash_dir = tmp_path / "Trash"
        (trash_dir / "info").mkdir(parents=True)
        (trash_dir / "info" / "a.jpg.trashinfo").write_text(
            "[Trash Info]\nPath=korabbi\n", encoding="utf-8"
        )
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"uj")
        trashed = delete_to_trash(photo, trash_dir=trash_dir)
        assert trashed == trash_dir / "files" / "a_1.jpg"
        assert (trash_dir / "info" / "a_1.jpg.trashinfo").exists()
        # a korábbi info-fájl tartalma sértetlen maradt
        assert "korabbi" in (
            trash_dir / "info" / "a.jpg.trashinfo"
        ).read_text(encoding="utf-8")

    def test_move_failure_removes_orphaned_trashinfo(self, tmp_path, monkeypatch):
        # ha a move meghiúsul, az előre megírt info-fájl ne maradjon árván
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        trash_dir = tmp_path / "Trash"

        def failing_move(src, dst):
            raise OSError("lemez megtelt")

        monkeypatch.setattr("picasapy.fileops.trash.shutil.move", failing_move)
        with pytest.raises(OSError):
            delete_to_trash(photo, trash_dir=trash_dir)
        assert not (trash_dir / "info" / "a.jpg.trashinfo").exists()
