"""`picasapy.index.dedup_folders`: történelmi mappa-duplikátumok
adatvesztés nélküli összevonása (#507)."""

from __future__ import annotations

import sqlite3

import pytest

from picasapy.index import open_index
from picasapy.index.dedup_folders import merge_duplicate_folders


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as connection:
        yield connection


def _insert_folder(conn: sqlite3.Connection, path: str, has_ini: int = 1) -> int:
    return conn.execute(
        "INSERT INTO folders(path, has_ini) VALUES (?, ?) RETURNING id",
        (path, has_ini),
    ).fetchone()[0]


def _insert_photo(conn: sqlite3.Connection, folder_id: int, name: str, **fields) -> int:
    defaults = dict(
        kind="image",
        size=10,
        mtime_ns=1,
        star=0,
        hidden=0,
        caption_ini=None,
        keywords_ini=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=None,
        height=None,
        caption_file=None,
        keywords_file=None,
        geotag_ini=None,
        exif_lat=None,
        exif_lon=None,
    )
    defaults.update(fields)
    cols = ["folder_id", "name", *defaults.keys()]
    placeholders = ", ".join("?" for _ in cols)
    values = [folder_id, name, *defaults.values()]
    return conn.execute(
        f"INSERT INTO photos({', '.join(cols)}) VALUES ({placeholders}) "
        "RETURNING id",
        values,
    ).fetchone()[0]


class TestMergeDuplicateFolders:
    def test_no_duplicates_is_noop(self, conn):
        _insert_folder(conn, "/a/kepek")
        report = merge_duplicate_folders(conn)
        assert report.merged == ()
        assert report.skipped == ()
        assert conn.execute("SELECT COUNT(*) FROM folders").fetchone()[0] == 1

    def test_disjoint_photos_merge_without_loss(self, conn, tmp_path):
        real = tmp_path / "kepek"
        real.mkdir()
        dup_a = str(real)
        dup_b = str(real) + "/"  # a normalize_path már ezt is dedup-olná,
        # de itt SZÁNDÉKOSAN közvetlen SQL-lel szimulálunk egy régi,
        # javítás-előtti duplikátumot — a merge-nek a nyers path_key-re
        # kell dolgoznia, nem a hívó normalizálására hagyatkozva.
        fid_a = _insert_folder(conn, dup_a)
        fid_b = _insert_folder(conn, dup_b)
        _insert_photo(conn, fid_a, "a.jpg", star=1, caption_ini="régi kép")
        _insert_photo(conn, fid_b, "b.jpg", keywords_ini="balaton,nyár")

        report = merge_duplicate_folders(conn)

        assert report.skipped == ()
        assert len(report.merged) == 1
        folders = conn.execute("SELECT id, path FROM folders").fetchall()
        assert len(folders) == 1
        keeper_id = folders[0]["id"]
        photos = {
            row["name"]: row
            for row in conn.execute(
                "SELECT * FROM photos WHERE folder_id = ?", (keeper_id,)
            )
        }
        assert set(photos) == {"a.jpg", "b.jpg"}
        assert photos["a.jpg"]["star"] == 1
        assert photos["a.jpg"]["caption_ini"] == "régi kép"
        assert photos["b.jpg"]["keywords_ini"] == "balaton,nyár"

    def test_colliding_photo_merges_nonconflicting_fields(self, conn, tmp_path):
        real = tmp_path / "kepek"
        real.mkdir()
        fid_a = _insert_folder(conn, str(real))
        fid_b = _insert_folder(conn, str(real) + "/")
        # ugyanaz a fájl mindkét oldalon (ez a valós eset — a két sor
        # UGYANAZT a valódi könyvtárat tükrözi): a keeperben nincs csillag,
        # a loserben van — a merge után a csillagnak MEG KELL maradnia.
        _insert_photo(conn, fid_a, "a.jpg", star=0, caption_ini=None)
        _insert_photo(conn, fid_b, "a.jpg", star=1, caption_ini="naplemente")

        report = merge_duplicate_folders(conn)

        assert report.skipped == ()
        assert len(report.merged) == 1
        rows = conn.execute("SELECT * FROM photos WHERE name = 'a.jpg'").fetchall()
        assert len(rows) == 1
        assert rows[0]["star"] == 1
        assert rows[0]["caption_ini"] == "naplemente"

    def test_conflicting_edit_skips_whole_group(self, conn, tmp_path):
        real = tmp_path / "kepek"
        real.mkdir()
        fid_a = _insert_folder(conn, str(real))
        fid_b = _insert_folder(conn, str(real) + "/")
        # MINDKÉT oldalon nem-üres, DE ELTÉRŐ felirat — valódi
        # szerkesztés-ütközés, amit nem lehet automatikusan eldönteni.
        _insert_photo(conn, fid_a, "a.jpg", caption_ini="A verzió")
        _insert_photo(conn, fid_b, "a.jpg", caption_ini="B verzió")

        report = merge_duplicate_folders(conn)

        assert report.merged == ()
        assert len(report.skipped) == 1
        # a duplikátum VÁLTOZATLANUL megmarad — adatvesztés helyett
        assert conn.execute("SELECT COUNT(*) FROM folders").fetchone()[0] == 2
        captions = {
            row["caption_ini"]
            for row in conn.execute("SELECT caption_ini FROM photos")
        }
        assert captions == {"A verzió", "B verzió"}

    def test_album_membership_survives_merge(self, conn, tmp_path):
        real = tmp_path / "kepek"
        real.mkdir()
        fid_a = _insert_folder(conn, str(real))
        fid_b = _insert_folder(conn, str(real) + "/")
        conn.execute(
            "INSERT INTO albums(folder_id, token, name) VALUES (?, 'tok1', 'Nyaralás')",
            (fid_b,),
        )
        photo_b = _insert_photo(conn, fid_b, "a.jpg")
        conn.execute(
            "INSERT INTO photo_albums(photo_id, token) VALUES (?, 'tok1')",
            (photo_b,),
        )
        _insert_photo(conn, fid_a, "b.jpg")  # nem ütköző, csak hogy A ne legyen üres

        report = merge_duplicate_folders(conn)

        assert report.skipped == ()
        keeper_id = conn.execute("SELECT id FROM folders").fetchone()["id"]
        album = conn.execute(
            "SELECT * FROM albums WHERE folder_id = ?", (keeper_id,)
        ).fetchone()
        assert album is not None and album["token"] == "tok1"
        photo_id = conn.execute(
            "SELECT id FROM photos WHERE name = 'a.jpg'"
        ).fetchone()["id"]
        membership = conn.execute(
            "SELECT * FROM photo_albums WHERE photo_id = ? AND token = 'tok1'",
            (photo_id,),
        ).fetchone()
        assert membership is not None

    def test_idempotent_second_run_is_noop(self, conn, tmp_path):
        real = tmp_path / "kepek"
        real.mkdir()
        fid_a = _insert_folder(conn, str(real))
        fid_b = _insert_folder(conn, str(real) + "/")
        _insert_photo(conn, fid_a, "a.jpg")
        _insert_photo(conn, fid_b, "b.jpg")

        first = merge_duplicate_folders(conn)
        second = merge_duplicate_folders(conn)

        assert len(first.merged) == 1
        assert second.merged == () and second.skipped == ()
