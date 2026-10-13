"""#4597 — az ini-ben rejtett mappa az index újraépítése után is rejtett.

A `folders.hidden` az ini `P2category=Hidden Folders` sorából származik
(`index/sync.py`), nem önálló igazságforrás.
"""

from __future__ import annotations

import pytest

from picasapy.index import hidden_folders, is_folder_hidden, open_index, sync_tree
from picasapy.ini import set_folder_hidden_in_ini


@pytest.fixture
def gyoker(tmp_path):
    gyoker = tmp_path / "kepek"
    for nev in ("nyaralas", "titkos"):
        (gyoker / nev).mkdir(parents=True)
        (gyoker / nev / "a.jpg").write_bytes(b"1")
    return gyoker


def _ujraepit(tmp_path, gyoker):
    """Az index törlése és újraépítése, mint egy friss telepítésen."""
    db = tmp_path / "uj-index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        return hidden_folders(conn)


def test_ini_vel_rejtett_mappa_az_ujraepites_utan_is_rejtett(tmp_path, gyoker):
    titkos = gyoker / "titkos"
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, gyoker)
        assert hidden_folders(conn) == ()
    set_folder_hidden_in_ini(titkos, True)
    (tmp_path / "index.db").unlink()
    assert _ujraepit(tmp_path, gyoker) == (str(titkos),)


def test_picasaban_rejtett_mappa_rejtettkent_jon_be(tmp_path, gyoker):
    (gyoker / "titkos" / ".picasa.ini").write_text(
        "[Picasa]\nP2category=hidden folders\n", encoding="utf-8"
    )
    assert _ujraepit(tmp_path, gyoker) == (str(gyoker / "titkos"),)


def test_category_kulcs_is_szamit(tmp_path, gyoker):
    (gyoker / "titkos" / ".picasa.ini").write_text(
        "[Picasa]\ncategory=Hidden Folders\n", encoding="utf-8"
    )
    assert _ujraepit(tmp_path, gyoker) == (str(gyoker / "titkos"),)


def test_megjelenites_az_ujraszinkron_utan_is_latszik(tmp_path, gyoker):
    titkos = gyoker / "titkos"
    set_folder_hidden_in_ini(titkos, True)
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        assert is_folder_hidden(conn, str(titkos)) is True
    set_folder_hidden_in_ini(titkos, False)
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        assert is_folder_hidden(conn, str(titkos)) is False


def test_ini_nelkuli_mappa_regi_indexbeli_rejtese_megmarad(tmp_path, gyoker):
    """A #1637 előtti, csak indexben élő rejtést ini nélkül nem nullázzuk."""
    from picasapy.index import set_folder_hidden

    titkos = gyoker / "titkos"
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        set_folder_hidden(conn, str(titkos), True)
        (titkos / "b.jpg").write_bytes(b"2")
        sync_tree(conn, gyoker)
        assert is_folder_hidden(conn, str(titkos)) is True
