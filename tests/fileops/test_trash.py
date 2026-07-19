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
