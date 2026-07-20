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

    def test_hidden_flag_from_ini(self, conn, library):
        # #17: a Picasa hidden=yes kulcsa — mtime-változás nélkül is átjön
        # (az ini-mezők a változatlan fájlokon is frissülnek)
        sync_tree(conn, library)
        (library / "nyaralas" / ".picasa.ini").write_text(
            "[IMG_0001.jpg]\nhidden=yes\n", encoding="utf-8"
        )
        sync_tree(conn, library)
        photos = photos_in_folder(conn, library / "nyaralas")
        assert photos[0].hidden is True
        assert photos[1].hidden is False

    def test_sync_is_idempotent(self, conn, library):
        sync_tree(conn, library)
        first = photos_in_folder(conn, library / "nyaralas")
        sync_tree(conn, library)
        second = photos_in_folder(conn, library / "nyaralas")
        assert first == second  # azonos id-k is: nem duplikál, nem törli-újraírja

    def test_unchanged_files_and_ini_touch_no_rows(self, conn, library):
        # #139: változatlan fájl + változatlan ini-mezők esetén a sync nem
        # ír át egyetlen photos-sort sem — így az FTS-trigger sem sül el
        # (WAL-hízás és flash-kopás elkerülése az 5 percenkénti syncnél).
        sync_tree(conn, library)
        conn.execute("CREATE TEMP TABLE update_szamlalo(n INTEGER NOT NULL)")
        conn.execute("INSERT INTO update_szamlalo VALUES (0)")
        conn.execute(
            "CREATE TEMP TRIGGER photos_update_figyelo AFTER UPDATE ON photos"
            " BEGIN UPDATE update_szamlalo SET n = n + 1; END"
        )
        sync_tree(conn, library)
        assert conn.execute("SELECT n FROM update_szamlalo").fetchone()[0] == 0

    def test_ini_change_still_updates_unchanged_file(self, conn, library):
        # #139 ellenpróba: ha CSAK az ini változik (a fájl nem), az UPDATE
        # ág továbbra is lefut, és pontosan az érintett sort írja át.
        sync_tree(conn, library)
        conn.execute("CREATE TEMP TABLE update_szamlalo(n INTEGER NOT NULL)")
        conn.execute("INSERT INTO update_szamlalo VALUES (0)")
        conn.execute(
            "CREATE TEMP TRIGGER photos_update_figyelo AFTER UPDATE ON photos"
            " BEGIN UPDATE update_szamlalo SET n = n + 1; END"
        )
        (library / "nyaralas" / ".picasa.ini").write_text(
            "[IMG_0001.jpg]\nstar=yes\ncaption=naplemente\n"
            "keywords=balaton,nyár\nrotate=rotate(1)\nhidden=yes\n",
            encoding="utf-8",
        )
        sync_tree(conn, library)
        assert conn.execute("SELECT n FROM update_szamlalo").fetchone()[0] == 1
        photos = photos_in_folder(conn, library / "nyaralas")
        assert photos[0].hidden is True

    def test_deleted_file_pruned(self, conn, library):
        sync_tree(conn, library)
        (library / "nyaralas" / "IMG_0002.jpg").unlink()
        sync_tree(conn, library)
        names = [p.name for p in photos_in_folder(conn, library / "nyaralas")]
        assert names == ["IMG_0001.jpg"]

    def test_deleted_folder_pruned(self, conn, library, tmp_path):
        # A gyökér alatt egy másik, érintetlen mappa is marad — a scan tehát
        # nem üres, így a #132-es védelem nem lép közbe, és a törölt mappa
        # rendesen kikerül az indexből.
        (library / "tavasz").mkdir()
        (library / "tavasz" / "IMG_9999.jpg").write_bytes(b"z" * 5)
        sync_tree(conn, library)
        import shutil

        shutil.rmtree(library / "nyaralas")
        sync_tree(conn, library)
        assert photos_in_folder(conn, library / "nyaralas") == ()
        assert len(photos_in_folder(conn, library / "tavasz")) == 1

    def test_empty_scan_keeps_previously_indexed_subtree(self, conn, library, caplog):
        # #132: lecsatolt NAS-mount esetén a gyökér létezik, de üresen
        # scannelődik — ez megkülönböztethetetlen attól, hogy minden mappa
        # ténylegesen eltűnt. A korábban felindexelt részfa ilyenkor NEM
        # törlődik, csak egy figyelmeztetés kerül a naplóba.
        sync_tree(conn, library)
        before = photos_in_folder(conn, library / "nyaralas")
        assert len(before) == 2

        (library / "nyaralas" / "IMG_0001.jpg").unlink()
        (library / "nyaralas" / "IMG_0002.jpg").unlink()
        (library / "nyaralas" / ".picasa.ini").unlink()

        import logging

        with caplog.at_level(logging.WARNING, logger="picasapy.index.sync"):
            sync_tree(conn, library)

        after = photos_in_folder(conn, library / "nyaralas")
        assert after == before  # a részfa érintetlen maradt
        assert any("elérhetetlen" in record.message for record in caplog.records)

    def test_empty_scan_with_previously_empty_index_is_noop(self, conn, tmp_path):
        # Ha a gyökér már korábban is üres volt az indexben, nincs mit óvni:
        # a takarítás lefut (ami itt nem csinál semmit).
        root = tmp_path / "ures-gyoker"
        root.mkdir()
        sync_tree(conn, root)
        assert photos_in_folder(conn, root) == ()

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

    def test_decompression_bomb_photo_does_not_abort_sync(self, conn, library):
        # #134: egy irreálisan nagy deklarált méretű ("óriáskép",
        # decompression bomb) fájl a metaadat-olvasásnál eddig kivételt
        # dobott, ami a teljes sync_tree-t megakasztotta — a többi fájl be
        # sem került az indexbe. A bombának csak a saját metaadata legyen
        # üres, a szinkron menjen tovább.
        (library / "nyaralas" / "oriaskep.jpg").write_bytes(
            b"P6\n50000 50000\n255\n" + b"\x00" * 16
        )
        sync_tree(conn, library)
        photos = photos_in_folder(conn, library / "nyaralas")
        assert [p.name for p in photos] == [
            "IMG_0001.jpg",
            "IMG_0002.jpg",
            "oriaskep.jpg",
        ]

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


class TestFiltersSync:
    """#59: a filters= lánc az indexbe kerül — a thumbnail ebből renderel."""

    def test_filters_synced_and_updated(self, tmp_path):
        from picasapy.index import open_index, photos_in_folder, sync_tree
        from support.jpeg_factory import make_jpeg

        lib = tmp_path / "kepek"
        lib.mkdir()
        make_jpeg(lib / "a.jpg")
        ini = lib / ".picasa.ini"
        ini.write_text("[a.jpg]\nfilters=enhance=1;\n", encoding="utf-8")
        with open_index(tmp_path / "i.db") as conn:
            sync_tree(conn, lib)
            record = photos_in_folder(conn, lib)[0]
            assert record.filters == "enhance=1;"
            # ini-only változás (a fájl nem változik) → UPDATE ág
            ini.write_text(
                "[a.jpg]\nfilters=crop64=1,1234abcd5678ef00;enhance=1;\n",
                encoding="utf-8",
            )
            sync_tree(conn, lib)
            record = photos_in_folder(conn, lib)[0]
            assert record.filters == "crop64=1,1234abcd5678ef00;enhance=1;"

    def test_no_filters_is_none(self, tmp_path):
        from picasapy.index import open_index, photos_in_folder, sync_tree
        from support.jpeg_factory import make_jpeg

        lib = tmp_path / "kepek"
        lib.mkdir()
        make_jpeg(lib / "a.jpg")
        with open_index(tmp_path / "i.db") as conn:
            sync_tree(conn, lib)
            assert photos_in_folder(conn, lib)[0].filters is None
