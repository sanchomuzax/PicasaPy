"""A migráció nem hagyhat NYITOTT SQLite-kapcsolatot (#1076).

## A lelet

A windows-CI-láb ezen bukott, a termékben:

```
PermissionError: [WinError 32] The process cannot access the file because
it is being used by another process: '…\\.index.db.<rand>.tmp'
```

⚠️ A `with sqlite3.connect(...)` **NEM zárja be a kapcsolatot** — csak a
tranzakciót kezeli (commit/rollback). A `_copy_sqlite_database` az
integritás-ellenőrzést ilyen `with`-ben futtatta, tehát a másolat
fájl-leírója NYITVA maradt.

Linuxon ez láthatatlan: ott a nyitott fájl is linkelhető és törölhető.
Windowson viszont a rákövetkező publikálás/törlés `WinError 32`-vel bukik,
és az **egész migráció** hibára fut — a felhasználó indexe nem kerül át.

Ezért ez az őr **nem a hibaüzenetet** állítja (azt linuxon nem lehet
előidézni), hanem az INVARIÁNST: amennyi kapcsolat megnyílt, annyit be is
kell zárni. Ez mindkét platformon ugyanazt jelenti.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from picasapy.app import platform_storage


@pytest.fixture
def forras(tmp_path) -> Path:
    ut = tmp_path / "index.db"
    kapcsolat = sqlite3.connect(str(ut))
    kapcsolat.execute("CREATE TABLE t (a INTEGER)")
    kapcsolat.execute("INSERT INTO t VALUES (1)")
    kapcsolat.commit()
    kapcsolat.close()
    return ut


def _le_van_zarva(kapcsolat: sqlite3.Connection) -> bool:
    """Lezárt kapcsolat minden használatra `ProgrammingError`-t dob."""
    try:
        kapcsolat.execute("SELECT 1")
    except sqlite3.ProgrammingError:
        return True
    return False


def test_a_masolas_minden_kapcsolatot_BEZAR(forras, tmp_path, monkeypatch):
    """A másolás után egyetlen megnyitott kapcsolat sem maradhat nyitva.

    ⚠️ A `with sqlite3.connect(...)` NEM zár — csak a tranzakciót kezeli.
    Ez az őr pontosan azt a hiedelmet fogja meg, ami a windows-lábat
    megbuktatta: ott a nyitva maradt másolat `WinError 32`-vel viszi el az
    EGÉSZ migrációt, a felhasználó indexe pedig nem kerül át."""
    megnyitott: list[sqlite3.Connection] = []
    eredeti = sqlite3.connect

    def figyelo(*args, **kwargs):
        kapcsolat = eredeti(*args, **kwargs)
        megnyitott.append(kapcsolat)
        return kapcsolat

    monkeypatch.setattr(platform_storage.sqlite3, "connect", figyelo)
    cel = tmp_path / "cel" / "index.db"

    platform_storage._copy_sqlite_database(forras, cel)

    assert megnyitott, "meg sem nyitottunk adatbázist"
    nyitva = [k for k in megnyitott if not _le_van_zarva(k)]
    assert not nyitva, (
        f"{len(nyitva)} SQLite-kapcsolat NYITVA maradt a {len(megnyitott)}-ből "
        "— windowson ez WinError 32-vel viszi el az egész migrációt"
    )
    assert cel.exists()
