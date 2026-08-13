"""Mappa áthelyezése a kísérőfájlokkal — #457.

Az eredeti `Folder::ID_MOVEFOLDER` parancsa; a hibaesetek az eredeti
üzeneteiből jönnek (`CThumbUI::MoveFolderExists` / `::MoveFolderSysPath` /
`::MoveFolderError`).

A legfontosabb, ami nálunk TÖBB, mint az eredetinél: a `.picasa.ini` az
igazságforrás, tehát a mappával együtt kell mennie — enélkül a képek
elveszítenék a feliratukat, a címkéiket és az arc-hozzárendeléseiket.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from picasapy.fileops.move_folder import (
    FolderMoveError,
    is_system_path,
    move_folder,
)


def _folder_with_photo(root, name="kepek"):
    folder = root / name
    folder.mkdir(parents=True)
    (folder / "a.jpg").write_bytes(b"kep")
    (folder / ".picasa.ini").write_text(
        "[a.jpg]\ncaption=Nyaralás\n", encoding="utf-8"
    )
    return folder


class TestMove:
    def test_the_companion_ini_goes_with_it(self, tmp_path):
        source = _folder_with_photo(tmp_path / "innen")
        dest = tmp_path / "ide"
        dest.mkdir()

        moved = move_folder(source, dest)

        assert moved == dest / "kepek"
        assert (moved / "a.jpg").read_bytes() == b"kep"
        assert "Nyaralás" in (moved / ".picasa.ini").read_text(encoding="utf-8")
        assert not source.exists()

    def test_subfolders_come_too(self, tmp_path):
        source = _folder_with_photo(tmp_path / "innen")
        (source / "2019").mkdir()
        (source / "2019" / "b.jpg").write_bytes(b"masik")
        dest = tmp_path / "ide"
        dest.mkdir()

        moved = move_folder(source, dest)

        assert (moved / "2019" / "b.jpg").read_bytes() == b"masik"


class TestRefusals:
    """Minden elutasításnál a forrás ÉRINTETLEN marad."""

    def test_an_existing_name_in_the_destination(self, tmp_path):
        source = _folder_with_photo(tmp_path / "innen")
        dest = tmp_path / "ide"
        (dest / "kepek").mkdir(parents=True)

        with pytest.raises(FolderMoveError, match="már létezik"):
            move_folder(source, dest)

        assert (source / "a.jpg").exists()

    def test_a_missing_source(self, tmp_path):
        with pytest.raises(FolderMoveError):
            move_folder(tmp_path / "nincs", tmp_path)

    def test_a_missing_destination(self, tmp_path):
        source = _folder_with_photo(tmp_path / "innen")

        with pytest.raises(FolderMoveError):
            move_folder(source, tmp_path / "nincs")

        assert source.exists()

    def test_moving_into_itself(self, tmp_path):
        source = _folder_with_photo(tmp_path / "innen")
        inner = source / "belso"
        inner.mkdir()

        with pytest.raises(FolderMoveError, match="önmagába"):
            move_folder(source, inner)

        assert (source / "a.jpg").exists()

    def test_moving_where_it_already_is(self, tmp_path):
        source = _folder_with_photo(tmp_path / "innen")

        with pytest.raises(FolderMoveError, match="már ebben"):
            move_folder(source, source.parent)

        assert (source / "a.jpg").exists()

    @pytest.mark.skipif(os.name == "nt", reason="POSIX-utak")
    def test_a_posix_system_path_is_refused(self):
        """Az eredeti külön hibaüzenetet adott rá — nem hagyta, hogy a
        felhasználó lábon lője magát."""
        assert is_system_path("/etc") is True
        assert is_system_path("/usr") is True

        with pytest.raises(FolderMoveError, match="Rendszermappa"):
            move_folder("/etc", "/tmp")

    def test_the_drive_root_is_refused_everywhere(self, tmp_path):
        """A meghajtó gyökere platformtól függetlenül védett — linuxon a
        „/", Windowson a „C:\\"."""
        root = Path(tmp_path.anchor)

        assert is_system_path(root) is True

    def test_the_home_folder_itself_is_refused(self):
        """A home-ban lévő mappák mozgathatók, maga a home nem."""
        assert is_system_path(Path.home()) is True

    def test_an_ordinary_folder_is_not_a_system_path(self, tmp_path):
        assert is_system_path(_folder_with_photo(tmp_path / "innen")) is False
