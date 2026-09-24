"""#3549: a gyökér-gyorstár a 2^63-nál nagyobb fájlazonosítót is elbírja.

Windowson az `st_ino` a 64 bites ELŐJEL NÉLKÜLI fájlazonosító, az SQLite
`INTEGER` viszont előjeles 64 bites. A main CI Windows-lábán egy futtató
ilyen azonosítót adott, és a `_feloldas_gyorstarral` `OverflowError`-ral
megállt — egy windowsos felhasználónál a könyvtár szinkronja ugyanígy.

A próba az `os.stat`-ot helyettesíti, így platformtól függetlenül fut.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from picasapy.index import open_index
from picasapy.index import sync
from picasapy.index.sync import _feloldas_gyorstarral

LEGNAGYOBB = 2**64 - 1


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as kapcsolat:
        yield kapcsolat


@pytest.fixture
def nagy_azonosito(monkeypatch):
    eredeti = os.stat

    def stat(ut, *args, **kwargs):
        adat = eredeti(ut, *args, **kwargs)
        return SimpleNamespace(st_dev=LEGNAGYOBB - 1, st_ino=LEGNAGYOBB, st_mode=adat.st_mode)

    monkeypatch.setattr(sync.os, "stat", stat)


def test_a_legnagyobb_azonosito_is_tarolhato(conn, tmp_path, nagy_azonosito):
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    elso = _feloldas_gyorstarral(conn, (str(gyoker),))
    assert conn.execute("SELECT COUNT(*) FROM resolved_root_cache").fetchone()[0] == 1
    assert _feloldas_gyorstarral(conn, (str(gyoker),)) == elso


def test_a_masodik_hivas_a_gyorstarbol_talal(conn, tmp_path, nagy_azonosito, monkeypatch):
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    elso = _feloldas_gyorstarral(conn, (str(gyoker),))

    def ne_oldja_fel(_ut):
        raise AssertionError("a gyorstárnak kellett volna találnia")

    monkeypatch.setattr(sync, "normalize_path", ne_oldja_fel)
    assert _feloldas_gyorstarral(conn, (str(gyoker),)) == elso
