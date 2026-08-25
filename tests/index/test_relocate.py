"""Az adatbázis+cache áthelyezés magja (#368, `picasapy.index.relocate`).

A legfontosabb invariáns mindenütt tesztelve: HIBA vagy megszakítás esetén
a forrás (régi hely) MINDIG érintetlen marad."""

from __future__ import annotations

import sqlite3

import pytest

from picasapy.index import open_index, sync_tree
from picasapy.index.relocate import (
    RelocationCancelled,
    RelocationError,
    relocate_data_root,
)


def _make_source(tmp_path, with_cache=True):
    """Valódi index + (opcionálisan) cache-fájlok a régi helyen."""
    old_data = tmp_path / "old-data"
    old_data.mkdir()
    old_cache = tmp_path / "old-cache" / "thumbs"
    old_cache.mkdir(parents=True)

    photos = tmp_path / "fotok"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 100)
    index_db = old_data / "index.db"
    with open_index(index_db) as conn:
        sync_tree(conn, photos)

    if with_cache:
        (old_cache / "ab").mkdir()
        (old_cache / "ab" / "cafe.jpg").write_bytes(b"thumb-bytes")
    return index_db, old_cache


class TestValidateDestination:
    def test_rejects_destination_inside_database_folder(self, tmp_path):
        index_db, cache_dir = _make_source(tmp_path)
        with pytest.raises(RelocationError, match="belül van"):
            relocate_data_root(
                index_db, cache_dir, index_db.parent / "subdir-of-source"
            )
        assert index_db.exists()

    def test_rejects_destination_inside_cache_folder(self, tmp_path):
        index_db, cache_dir = _make_source(tmp_path)
        with pytest.raises(RelocationError, match="belül van"):
            relocate_data_root(index_db, cache_dir, cache_dir / "sub")
        assert index_db.exists()

    def test_rejects_destination_equal_to_source(self, tmp_path):
        index_db, cache_dir = _make_source(tmp_path)
        with pytest.raises(RelocationError):
            relocate_data_root(index_db, cache_dir, index_db.parent)
        assert index_db.exists()

    def test_rejects_unwritable_destination(self, tmp_path, monkeypatch):
        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "cel"

        def _boom(*args, **kwargs):
            raise OSError("nincs jogosultság")

        # #1375: a modul SAJÁT fogantyúja. A `"pathlib.Path.write_bytes"`
        # rögzítés a `Path` OSZTÁLYT írta át: a teszt idejére a folyamat
        # minden fájlkiírása dobott volna.
        monkeypatch.setattr("picasapy.index.relocate._probe_iras", _boom)
        with pytest.raises(RelocationError, match="nem írható"):
            relocate_data_root(index_db, cache_dir, new_root)
        assert index_db.exists()

    def test_rejects_insufficient_free_space(self, tmp_path, monkeypatch):
        import picasapy.index.relocate as relocate_module

        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "cel"

        class _FakeUsage:
            free = 1  # gyakorlatilag nulla szabad hely

        monkeypatch.setattr(
            relocate_module, "_disk_usage", lambda _path: _FakeUsage()
        )
        with pytest.raises(RelocationError, match="Nincs elég szabad hely"):
            relocate_data_root(index_db, cache_dir, new_root)
        assert index_db.exists()
        # a célon nem maradhat félkész adat
        assert not (new_root / "index.db").exists()


class TestSuccessfulRelocation:
    def test_moves_database_and_cache_and_removes_old(self, tmp_path):
        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "uj-hely"

        result = relocate_data_root(index_db, cache_dir, new_root)

        assert result.new_root == new_root
        assert result.old_cleanup_error is None
        assert (new_root / "index.db").exists()
        assert (new_root / "thumbs" / "ab" / "cafe.jpg").read_bytes() == b"thumb-bytes"
        assert not index_db.exists()
        assert not cache_dir.exists()

    def test_new_database_is_a_valid_independent_copy(self, tmp_path):
        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "uj-hely"

        relocate_data_root(index_db, cache_dir, new_root)

        conn = sqlite3.connect(str(new_root / "index.db"))
        try:
            count = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
        finally:
            conn.close()
        assert count == 1

    def test_missing_cache_is_tolerated(self, tmp_path):
        index_db, cache_dir = _make_source(tmp_path, with_cache=False)
        new_root = tmp_path / "uj-hely"

        result = relocate_data_root(index_db, cache_dir, new_root)

        assert (new_root / "index.db").exists()
        assert result.old_cleanup_error is None

    def test_missing_database_is_tolerated(self, tmp_path):
        # első indulás előtti állapot: még nincs index — csak a cache
        # létezik (elméletileg ritka, de a modul nem hibázhat rajta)
        old_data = tmp_path / "old-data"
        old_data.mkdir()
        old_cache = tmp_path / "old-cache"
        old_cache.mkdir()
        (old_cache / "x.jpg").write_bytes(b"thumb")
        new_root = tmp_path / "uj-hely"

        result = relocate_data_root(old_data / "index.db", old_cache, new_root)

        assert not (new_root / "index.db").exists()
        assert (new_root / "thumbs" / "x.jpg").exists()
        assert result.old_cleanup_error is None

    def test_on_verified_called_before_old_deletion(self, tmp_path):
        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "uj-hely"
        calls = []

        def on_verified(root):
            calls.append(root)
            # ekkor a régi helynek MÉG léteznie kell (a törlés csak ezután jön)
            assert index_db.exists()

        relocate_data_root(index_db, cache_dir, new_root, on_verified=on_verified)

        assert calls == [new_root]
        assert not index_db.exists()  # a hívás UTÁN már törlődött

    def test_progress_callback_reports_database_and_cache_phases(self, tmp_path):
        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "uj-hely"
        phases = []

        relocate_data_root(
            index_db,
            cache_dir,
            new_root,
            progress=lambda p: phases.append(p.phase),
        )

        assert "cache" in phases
        assert "done" in phases


class TestOnVerifiedFailure:
    def test_on_verified_error_leaves_source_untouched_and_cleans_target(
        self, tmp_path
    ):
        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "uj-hely"

        def _boom(_root):
            raise RuntimeError("nem sikerült a beállítás mentése")

        with pytest.raises(RuntimeError, match="beállítás mentése"):
            relocate_data_root(index_db, cache_dir, new_root, on_verified=_boom)

        assert index_db.exists()
        assert cache_dir.exists()
        assert not (new_root / "index.db").exists()


class TestCancellation:
    def test_cancel_before_start_leaves_source_untouched(self, tmp_path):
        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "uj-hely"

        with pytest.raises(RelocationCancelled):
            relocate_data_root(
                index_db, cache_dir, new_root, should_cancel=lambda: True
            )

        assert index_db.exists()
        assert cache_dir.exists()

    def test_cancel_mid_copy_leaves_source_untouched_and_cleans_target(
        self, tmp_path
    ):
        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "uj-hely"
        calls = {"n": 0}

        def should_cancel():
            calls["n"] += 1
            # az első pár híváson enged (validálás, kezdő ellenőrzés), a
            # ténylegesen a másolás KÖZBEN szakítja meg
            return calls["n"] > 2

        with pytest.raises(RelocationCancelled):
            relocate_data_root(
                index_db, cache_dir, new_root, should_cancel=should_cancel
            )

        assert index_db.exists()
        assert cache_dir.exists()
        assert not (new_root / "index.db").exists()
        assert not (new_root / "thumbs").exists()

    def test_cancel_never_deletes_old_data(self, tmp_path):
        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "uj-hely"
        original_bytes = index_db.read_bytes()

        with pytest.raises(RelocationCancelled):
            relocate_data_root(
                index_db, cache_dir, new_root, should_cancel=lambda: True
            )

        assert index_db.read_bytes() == original_bytes


class TestIntegrityCheckFailure:
    def test_corrupt_copy_is_rejected_and_source_stays_untouched(
        self, tmp_path, monkeypatch
    ):
        import picasapy.index.relocate as relocate_module

        index_db, cache_dir = _make_source(tmp_path)
        new_root = tmp_path / "uj-hely"

        def _fake_integrity_check(_db_path):
            raise RelocationError(
                "Az áthelyezett adatbázis integritás-ellenőrzése nem sikerült: "
                "malformed database schema"
            )

        monkeypatch.setattr(
            relocate_module, "_integrity_check", _fake_integrity_check
        )

        with pytest.raises(RelocationError, match="integritás"):
            relocate_data_root(index_db, cache_dir, new_root)

        assert index_db.exists()
        assert cache_dir.exists()
        assert not (new_root / "index.db").exists()
