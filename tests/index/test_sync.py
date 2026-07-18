"""Ismételhető szinkron: scan + .picasa.ini → index (7. rögzített döntés)."""

import pytest

from picasapy.index import (
    open_index,
    photos_in_folder,
    prune_foreign_folders,
    sync_tree,
)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    (root / "nyaralas" / "IMG_0001.jpg").write_bytes(b"x" * 10)
    (root / "nyaralas" / "IMG_0002.jpg").write_bytes(b"y" * 20)
    (root / "nyaralas" / ".picasa.ini").write_text(
        "[IMG_0001.jpg]\nstar=yes\ncaption=naplemente\nkeywords=balaton,nyár\n"
        "rotate=rotate(1)\n"
    , encoding="utf-8")
    return root


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as connection:
        yield connection


class TestSyncTree:
    def test_imports_photos_with_ini_metadata(self, conn, library):
        sync_tree(conn, library)
        photos = photos_in_folder(conn, library / "nyaralas")
        assert [p.name for p in photos] == ["IMG_0001.jpg", "IMG_0002.jpg"]
        starred = photos[0]
        assert starred.star
        assert starred.caption == "naplemente"
        assert starred.keywords == "balaton,nyár"
        assert starred.rotate_steps == 1
        assert photos[1].star is False
        assert photos[1].caption is None
        assert photos[1].rotate_steps == 0

    def test_sync_is_idempotent(self, conn, library):
        sync_tree(conn, library)
        first = photos_in_folder(conn, library / "nyaralas")
        sync_tree(conn, library)
        second = photos_in_folder(conn, library / "nyaralas")
        assert first == second  # azonos id-k is: nem duplikál, nem törli-újraírja

    def test_deleted_file_pruned(self, conn, library):
        sync_tree(conn, library)
        (library / "nyaralas" / "IMG_0002.jpg").unlink()
        sync_tree(conn, library)
        names = [p.name for p in photos_in_folder(conn, library / "nyaralas")]
        assert names == ["IMG_0001.jpg"]

    def test_deleted_folder_pruned(self, conn, library, tmp_path):
        sync_tree(conn, library)
        import shutil

        shutil.rmtree(library / "nyaralas")
        sync_tree(conn, library)
        assert photos_in_folder(conn, library / "nyaralas") == ()

    def test_ini_change_updates_metadata(self, conn, library):
        # A felhasználó a Windows-os Picasában csillagoz → resync átveszi.
        sync_tree(conn, library)
        (library / "nyaralas" / ".picasa.ini").write_text(
            "[IMG_0002.jpg]\nstar=yes\n"
        , encoding="utf-8")
        sync_tree(conn, library)
        photos = photos_in_folder(conn, library / "nyaralas")
        assert photos[0].star is False  # IMG_0001: csillag elvéve
        assert photos[1].star is True

    def test_file_change_updates_size(self, conn, library):
        sync_tree(conn, library)
        (library / "nyaralas" / "IMG_0001.jpg").write_bytes(b"x" * 99)
        sync_tree(conn, library)
        assert photos_in_folder(conn, library / "nyaralas")[0].size == 99

    def test_unreadable_ini_treated_as_missing(self, conn, library):
        # Zárolt/olvashatatlan ini (pl. a futó Picasa fogja) nem buktathatja
        # el a szinkront — a képek metaadat nélkül is bekerülnek.
        import os

        ini = library / "nyaralas" / ".picasa.ini"
        ini.chmod(0)
        if os.access(ini, os.R_OK):  # rootként futva nincs értelme
            pytest.skip("root alatt minden olvasható")
        try:
            sync_tree(conn, library)
        finally:
            ini.chmod(0o644)
        photos = photos_in_folder(conn, library / "nyaralas")
        assert [p.name for p in photos] == ["IMG_0001.jpg", "IMG_0002.jpg"]
        assert photos[0].star is False

    def test_relative_root_stored_as_absolute(self, conn, library, monkeypatch):
        # Az index kanonikus (abszolút) útvonalakra kulcsol — különböző
        # alakú gyökerekkel sem duplikálódhat / maradhat árva sor.
        monkeypatch.chdir(library.parent)
        sync_tree(conn, "kepek")
        photos = photos_in_folder(conn, library / "nyaralas")
        assert len(photos) == 2
        assert photos[0].folder_path == str(library / "nyaralas")

    def test_prune_photos_empty_list_clears_folder(self, conn, library):
        from picasapy.index.sync import _prune_photos

        sync_tree(conn, library)
        folder_id = conn.execute("SELECT id FROM folders").fetchone()[0]
        _prune_photos(conn, folder_id, [])
        conn.commit()
        assert photos_in_folder(conn, library / "nyaralas") == ()

    def test_remove_root_deletes_folders_and_photos(self, conn, library, tmp_path):
        from picasapy.index import remove_root

        other = tmp_path / "masik"
        (other / "m").mkdir(parents=True)
        (other / "m" / "x.jpg").write_bytes(b"x")
        sync_tree(conn, library)
        sync_tree(conn, other)
        remove_root(conn, library)
        assert photos_in_folder(conn, library / "nyaralas") == ()
        assert len(photos_in_folder(conn, other / "m")) == 1  # más gyökér marad
        # FTS is kitakarítva (nincs árva bejegyzés)
        assert conn.execute("SELECT count(*) FROM photos").fetchone()[0] == 1

    def test_missing_ini_defaults(self, conn, library):
        (library / "nyaralas" / ".picasa.ini").unlink()
        sync_tree(conn, library)
        photo = photos_in_folder(conn, library / "nyaralas")[0]
        assert photo.star is False
        assert photo.caption is None
        assert photo.keywords is None


class TestPruneForeignFolders:
    def test_folders_outside_roots_removed(self, conn, library, tmp_path):
        # #58: az előző futásokból ottragadt gyökér (pl. régi parancssori
        # argumentum) mappái induláskor kikerülnek az indexből.
        regi = tmp_path / "regi-gyoker"
        (regi / "archiv").mkdir(parents=True)
        (regi / "archiv" / "IMG_0009.jpg").write_bytes(b"z" * 9)
        sync_tree(conn, library)
        sync_tree(conn, regi)
        prune_foreign_folders(conn, (str(library),))
        assert len(photos_in_folder(conn, library / "nyaralas")) == 2
        assert photos_in_folder(conn, regi / "archiv") == ()
        # FTS sem tartalmaz árva sort
        assert conn.execute("SELECT count(*) FROM photos").fetchone()[0] == 2

    def test_empty_roots_keep_index(self, conn, library):
        # Védekezés: üres gyökérlista (pl. kézzel törölt WatchedFolders.txt)
        # nem ürítheti ki csendben az egész indexet.
        sync_tree(conn, library)
        prune_foreign_folders(conn, ())
        assert len(photos_in_folder(conn, library / "nyaralas")) == 2

    def test_watched_roots_untouched(self, conn, library):
        sync_tree(conn, library)
        prune_foreign_folders(conn, (str(library),))
        photos = photos_in_folder(conn, library / "nyaralas")
        assert [p.name for p in photos] == ["IMG_0001.jpg", "IMG_0002.jpg"]
