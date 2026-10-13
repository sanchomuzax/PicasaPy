"""#4597 — hibaágak: olvashatatlan ini, összevonás.

Rejtett (privát) mappa átmeneti hiba miatt sem válhat tartósan láthatóvá.
"""

from __future__ import annotations

import os

import pytest

from picasapy.index import is_folder_hidden, open_index, sync_tree
from picasapy.index import sync as sync_modul
from picasapy.index.dedup_folders import merge_duplicate_folders

_REGI = 1_000_000_000  # 2001 — jóval a frissesség-védőablak előtt


@pytest.fixture
def gyoker(tmp_path):
    gyoker = tmp_path / "kepek"
    titkos = gyoker / "titkos"
    titkos.mkdir(parents=True)
    (titkos / "a.jpg").write_bytes(b"1")
    (titkos / ".picasa.ini").write_text(
        "[Picasa]\nP2category=Hidden Folders\n", encoding="utf-8"
    )
    for ut in (titkos / "a.jpg", titkos / ".picasa.ini", titkos):
        os.utime(ut, (_REGI, _REGI))
    return gyoker


def test_olvashatatlan_ini_nem_menti_a_scan_allapotot(tmp_path, gyoker, monkeypatch):
    titkos = str(gyoker / "titkos")
    db = tmp_path / "index.db"

    def hibas(_ut):
        raise OSError("zárolt")

    with monkeypatch.context() as m:
        m.setattr(sync_modul, "load_document", hibas)
        with open_index(db) as conn:
            sync_tree(conn, gyoker, incremental=True)
            assert is_folder_hidden(conn, titkos) is False
    # második kör, olvasható ini: az inkrementális sync NEM hagyhatja ki
    with open_index(db) as conn:
        sync_tree(conn, gyoker, incremental=True)
        assert is_folder_hidden(conn, titkos) is True


def test_olvashatatlan_ini_a_2_es_jelolest_nem_nullazza(tmp_path, gyoker, monkeypatch):
    titkos = str(gyoker / "titkos")
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        conn.execute("UPDATE folders SET hidden = 2")
        conn.commit()

    def hibas(_ut):
        raise OSError("zárolt")

    with monkeypatch.context() as m:
        m.setattr(sync_modul, "load_document", hibas)
        with open_index(db) as conn:
            sync_tree(conn, gyoker, incremental=True)
            assert conn.execute(
                "SELECT hidden FROM folders WHERE path = ?", (titkos,)
            ).fetchone()[0] == 2


def test_osszevonaskor_a_rejtes_megmarad(tmp_path):
    valodi = tmp_path / "kepek"
    valodi.mkdir()
    with open_index(tmp_path / "index.db") as conn:
        conn.execute(
            "INSERT INTO folders(path, has_ini, hidden) VALUES (?, 1, 0) RETURNING id",
            (str(valodi),),
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO folders(path, has_ini, hidden) VALUES (?, 1, 1)",
            (str(valodi) + "/",),
        )
        merge_duplicate_folders(conn)
        sorok = conn.execute("SELECT id, hidden FROM folders").fetchall()
        assert len(sorok) == 1
        assert sorok[0]["hidden"] == 1
