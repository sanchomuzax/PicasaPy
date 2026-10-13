"""#4597 — EGYSZERI ÁTÁLLÍTÁS: a régi indexben (v21) csak az SQLite-ban rejtett
mappa az új kód első szinkronjakor az ini-be is beíródik, és CSAK EZUTÁN
számít az ini az igazságforrásnak. Privát tartalom frissítés után sem
válhat láthatóvá.
"""

from __future__ import annotations

import shutil
import sqlite3

import pytest

from picasapy.index import is_folder_hidden, open_index, sync_tree
from picasapy.ini import load_document, read_folder_category
from picasapy.ini.io import update_document
from picasapy.ini import with_folder_category


@pytest.fixture
def gyoker(tmp_path):
    gyoker = tmp_path / "kepek"
    for nev in ("nyaralas", "titkos"):
        (gyoker / nev).mkdir(parents=True)
        (gyoker / nev / "a.jpg").write_bytes(b"1")
    return gyoker


def _regi_index(db, gyoker, rejtett):
    """Egy v21-es index, amelyben a mappa csak az SQLite-ban rejtett."""
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        conn.execute("UPDATE folders SET hidden = 1 WHERE path = ?", (str(rejtett),))
        conn.commit()
    kapcsolat = sqlite3.connect(db)
    kapcsolat.execute("PRAGMA user_version=21")
    kapcsolat.commit()
    kapcsolat.close()


def _kategoria(mappa):
    return read_folder_category(load_document(mappa / ".picasa.ini"))


def test_regi_rejtes_az_elso_szinkron_utan_az_iniben_is_ott_van(tmp_path, gyoker):
    titkos = gyoker / "titkos"
    db = tmp_path / "index.db"
    _regi_index(db, gyoker, titkos)
    with open_index(db) as conn:
        assert is_folder_hidden(conn, str(titkos)) is True  # migráció után is
        sync_tree(conn, gyoker)
        assert is_folder_hidden(conn, str(titkos)) is True
    assert _kategoria(titkos) == "Hidden Folders"


def test_az_atallas_utan_az_ini_az_igazsag(tmp_path, gyoker):
    titkos = gyoker / "titkos"
    db = tmp_path / "index.db"
    _regi_index(db, gyoker, titkos)
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
    # a Picasában megjelenítik
    update_document(
        titkos / ".picasa.ini",
        lambda d: with_folder_category(d, "Folders on Disk"),
    )
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        assert is_folder_hidden(conn, str(titkos)) is False


def test_offline_mappa_rejtese_megmarad_visszatereskor_beirodik(
    tmp_path, gyoker, monkeypatch
):
    titkos = gyoker / "titkos"
    db = tmp_path / "index.db"
    _regi_index(db, gyoker, titkos)
    # levált megosztás: a mappa nem elérhető, de a sora marad (offline)
    with monkeypatch.context() as m:
        m.setattr(
            "picasapy.index.sync.folder_looks_offline",
            lambda ut: str(ut).endswith("titkos"),
        )
        mentes = tmp_path / "mentes"
        shutil.move(str(titkos), str(mentes))
        with open_index(db) as conn:
            sync_tree(conn, gyoker)
            assert is_folder_hidden(conn, str(titkos)) is True
        shutil.move(str(mentes), str(titkos))
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        assert is_folder_hidden(conn, str(titkos)) is True
    assert _kategoria(titkos) == "Hidden Folders"


def test_ismert_ini_nelkuli_mappa_valtozatlan_marad_es_nem_rejtett(tmp_path, gyoker):
    db = tmp_path / "index.db"
    _regi_index(db, gyoker, gyoker / "titkos")
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        assert is_folder_hidden(conn, str(gyoker / "nyaralas")) is False
