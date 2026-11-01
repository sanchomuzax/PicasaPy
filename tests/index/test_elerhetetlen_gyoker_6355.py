"""Elérhetetlen hálózati gyökér: a takarítás nem vár a hálózati időkorlátra (#6355).

A windowsos CI valósághű mérésén az indulás 24,9 s volt, ebből 19,9 s a
„Mappák ellenőrzése": a védett gyökerek `resolve()`-ja és `stat`-ja egy
elérhetetlen `\\\\szerver\\megosztás` útvonalon. A gyökér védelme marad (a
takarítás nem törli a sorait), csak lemezművelet nélkül.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from picasapy import halozati_ut
from picasapy.index import open_index
from picasapy.index import sync_cleanup

UNC = "\\\\192.0.2.1\\picasa\\export\\album"


@pytest.fixture
def elerhetetlen(monkeypatch):
    halozati_ut._alaphelyzet()
    monkeypatch.setattr(halozati_ut, "_letezik", lambda _ut: False)
    hivasok: list[str] = []

    def tilos(ut):
        hivasok.append(str(ut))
        raise AssertionError(f"lemezművelet elérhetetlen gyökéren: {ut}")

    monkeypatch.setattr(sync_cleanup, "legacy", lambda nev: tilos)
    yield hivasok
    halozati_ut._alaphelyzet()


def test_a_feloldas_kihagyja_az_elerhetetlen_megosztast(elerhetetlen):
    eredmeny = sync_cleanup._resolved_protected_roots((UNC,))
    assert eredmeny == (Path(os.path.normpath(UNC)),)
    assert elerhetetlen == []


def test_a_gyorstaras_feloldas_sem_nyul_hozza(elerhetetlen, tmp_path):
    with open_index(tmp_path / "index.db") as conn:
        eredmeny = sync_cleanup._feloldas_gyorstarral(conn, (UNC,))
    assert eredmeny == (Path(os.path.normpath(UNC)),)
    assert elerhetetlen == []
