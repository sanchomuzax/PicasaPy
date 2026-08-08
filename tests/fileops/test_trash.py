"""delete_to_trash / find_trash_dir / trash_available / delete_permanently:
freedesktop.org Trash-specifikáció (#15, #457 — mount-specifikus lomtár és
kuka/végleges törlés megkülönböztetés NAS-on)."""

import os
import urllib.parse

import pytest

from picasapy.fileops import (
    TrashUnavailableError,
    delete_permanently,
    delete_to_trash,
    find_trash_dir,
    trash_available,
)


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


def _split_device_by_prefix(topdir):
    """Segéd a `_device_of` mockolásához: a `topdir` alatti útvonalak
    "1"-es, minden más "2"-es eszközön "van" — így a mount-határ
    szimulálható anélkül, hogy valódi másik fájlrendszer kellene."""
    return lambda p: 1 if str(p).startswith(str(topdir)) else 2


@pytest.mark.skipif(
    not hasattr(os, "getuid"),
    reason="A mount-specifikus lomtár freedesktop.org (POSIX) fogalom — "
    "Windowson a #457 előtti, home-trash viselkedés marad.",
)
class TestFindTrashDir:
    """#457: mount-specifikus lomtár (freedesktop `$topdir/.Trash[-uid]`) —
    a `_device_of`/`_mount_point` mockolásával szimulált fájlrendszer-
    határral, mivel a tesztkonténerben nincs valódi másik mount elérhető."""

    def test_trash_dir_override_wins_over_everything(self, tmp_path):
        override = tmp_path / "T"
        assert find_trash_dir(tmp_path / "a.jpg", trash_dir=override) == override

    def test_same_filesystem_as_home_uses_home_trash(self, tmp_path, monkeypatch):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        assert find_trash_dir(photo) == tmp_path / "xdg" / "Trash"

    def test_other_filesystem_uses_shared_trash_when_valid(self, tmp_path, monkeypatch):
        topdir = tmp_path / "nas"
        shared = topdir / ".Trash"
        shared.mkdir(parents=True)
        shared.chmod(0o1777)  # sticky bit, nem symlink
        photo = topdir / "sub" / "a.jpg"
        photo.parent.mkdir(parents=True)
        photo.write_bytes(b"kep")
        monkeypatch.setattr(
            "picasapy.fileops.trash._device_of", _split_device_by_prefix(topdir)
        )
        monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)

        assert find_trash_dir(photo) == shared / str(os.getuid())

    def test_shared_trash_symlink_is_rejected(self, tmp_path, monkeypatch):
        topdir = tmp_path / "nas"
        topdir.mkdir()
        real_dir = tmp_path / "masutt"
        real_dir.mkdir()
        (topdir / ".Trash").symlink_to(real_dir)
        photo = topdir / "a.jpg"
        photo.write_bytes(b"kep")
        monkeypatch.setattr(
            "picasapy.fileops.trash._device_of", _split_device_by_prefix(topdir)
        )
        monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)

        # symlink miatt elutasítva -> a topdir írható, tehát .Trash-uid jön
        assert find_trash_dir(photo) == topdir / f".Trash-{os.getuid()}"

    def test_shared_trash_without_sticky_bit_is_rejected(self, tmp_path, monkeypatch):
        topdir = tmp_path / "nas"
        shared = topdir / ".Trash"
        shared.mkdir(parents=True)
        shared.chmod(0o777)  # nincs sticky bit
        photo = topdir / "a.jpg"
        photo.write_bytes(b"kep")
        monkeypatch.setattr(
            "picasapy.fileops.trash._device_of", _split_device_by_prefix(topdir)
        )
        monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)

        assert find_trash_dir(photo) == topdir / f".Trash-{os.getuid()}"

    def test_falls_back_to_per_user_trash_when_topdir_writable(
        self, tmp_path, monkeypatch
    ):
        topdir = tmp_path / "nas"
        topdir.mkdir()
        photo = topdir / "a.jpg"
        photo.write_bytes(b"kep")
        monkeypatch.setattr(
            "picasapy.fileops.trash._device_of", _split_device_by_prefix(topdir)
        )
        monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)

        assert find_trash_dir(photo) == topdir / f".Trash-{os.getuid()}"

    def test_returns_none_when_topdir_not_writable(self, tmp_path, monkeypatch):
        topdir = tmp_path / "nas"
        topdir.mkdir()
        photo = topdir / "a.jpg"
        photo.write_bytes(b"kep")
        monkeypatch.setattr(
            "picasapy.fileops.trash._device_of", _split_device_by_prefix(topdir)
        )
        monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)
        monkeypatch.setattr(
            "picasapy.fileops.trash.os.access", lambda path, mode: False
        )

        assert find_trash_dir(photo) is None

    def test_uses_existing_per_user_trash_even_if_topdir_now_readonly(
        self, tmp_path, monkeypatch
    ):
        # ha a .Trash-uid MÁR létezik egy korábbi törlésből, akkor a
        # topdir írhatóságát nem kell újra ellenőrizni hozzá
        topdir = tmp_path / "nas"
        topdir.mkdir()
        per_user = topdir / f".Trash-{os.getuid()}"
        per_user.mkdir()
        photo = topdir / "a.jpg"
        photo.write_bytes(b"kep")
        monkeypatch.setattr(
            "picasapy.fileops.trash._device_of", _split_device_by_prefix(topdir)
        )
        monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)
        monkeypatch.setattr(
            "picasapy.fileops.trash.os.access", lambda path, mode: False
        )

        assert find_trash_dir(photo) == per_user


@pytest.mark.skipif(
    not hasattr(os, "getuid"),
    reason="A mount-specifikus lomtár freedesktop.org (POSIX) fogalom — "
    "Windowson a #457 előtti, home-trash viselkedés marad.",
)
class TestTrashAvailable:
    def test_true_when_a_trash_dir_is_found(self, tmp_path):
        assert trash_available(tmp_path / "a.jpg", trash_dir=tmp_path / "T") is True

    def test_false_when_no_trash_is_available(self, tmp_path, monkeypatch):
        topdir = tmp_path / "nas"
        topdir.mkdir()
        photo = topdir / "a.jpg"
        monkeypatch.setattr(
            "picasapy.fileops.trash._device_of", _split_device_by_prefix(topdir)
        )
        monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)
        monkeypatch.setattr(
            "picasapy.fileops.trash.os.access", lambda path, mode: False
        )

        assert trash_available(photo) is False


@pytest.mark.skipif(
    not hasattr(os, "getuid"),
    reason="A mount-specifikus lomtár freedesktop.org (POSIX) fogalom — "
    "Windowson a #457 előtti, home-trash viselkedés marad.",
)
class TestDeleteToTrashRaisesWhenNoTrashAvailable:
    def test_raises_trash_unavailable_error_and_keeps_the_file(
        self, tmp_path, monkeypatch
    ):
        topdir = tmp_path / "nas"
        topdir.mkdir()
        photo = topdir / "a.jpg"
        photo.write_bytes(b"kep")
        monkeypatch.setattr(
            "picasapy.fileops.trash._device_of", _split_device_by_prefix(topdir)
        )
        monkeypatch.setattr("picasapy.fileops.trash._mount_point", lambda p: topdir)
        monkeypatch.setattr(
            "picasapy.fileops.trash.os.access", lambda path, mode: False
        )

        with pytest.raises(TrashUnavailableError):
            delete_to_trash(photo)
        assert photo.exists()  # semmiképp nem törlődött csendben véglegesen


class TestDeletePermanently:
    def test_deletes_a_file(self, tmp_path):
        photo = tmp_path / "a.jpg"
        photo.write_bytes(b"kep")
        delete_permanently(photo)
        assert not photo.exists()

    def test_deletes_a_directory_recursively(self, tmp_path):
        folder = tmp_path / "mappa"
        folder.mkdir()
        (folder / "a.jpg").write_bytes(b"kep")
        delete_permanently(folder)
        assert not folder.exists()

    def test_missing_source_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            delete_permanently(tmp_path / "nincs.jpg")
