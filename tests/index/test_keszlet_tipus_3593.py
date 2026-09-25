"""#3593 — a mentési készlet TÁROLJA a típusát.

Az eredeti „Új mentési készlet" ablaka (`newbackupset.fen`):

```
Backup type:  ( ) CD or DVD backup
              ( ) Disk-to-disk backup (for external and network drives)
```

A `backups.xml`-ben a típust a `diskroot` jelenléte hordozza
(`docs/specs/biztonsagi-mentes.md` 2.). Nálunk az index tárolja, külön
oszlopban; a régi (típus nélküli) készletek LEMEZ-LEMEZ típusúak maradnak —
ma is mappába mentenek.
"""

from __future__ import annotations

import sqlite3

import pytest

from picasapy.index.backup_sets import (
    TIPUS_CD_DVD,
    TIPUS_LEMEZ,
    TIPUSOK,
    keszlet_letrehozasa,
    keszlet_modositasa,
    keszletek,
)


@pytest.fixture
def conn():
    kapcsolat = sqlite3.connect(":memory:")
    yield kapcsolat
    kapcsolat.close()


def test_ket_tipus():
    assert set(TIPUSOK) == {TIPUS_CD_DVD, TIPUS_LEMEZ}


def test_alapbol_lemez_lemez(conn):
    keszlet = keszlet_letrehozasa(conn, "Családi", "/mnt/kulso")

    assert keszlet.tipus == TIPUS_LEMEZ
    assert keszletek(conn)[0].tipus == TIPUS_LEMEZ


def test_a_cd_dvd_tipus_megmarad(conn):
    keszlet_letrehozasa(conn, "Lemezre", "/kepek/iso", tipus=TIPUS_CD_DVD)

    assert keszletek(conn)[0].tipus == TIPUS_CD_DVD


def test_ismeretlen_tipus(conn):
    with pytest.raises(ValueError):
        keszlet_letrehozasa(conn, "X", "/a", tipus="szalag")


def test_a_tipus_modosithato_es_a_tobbi_marad(conn):
    keszlet = keszlet_letrehozasa(conn, "X", "/a")

    keszlet_modositasa(conn, keszlet.id, tipus=TIPUS_CD_DVD)

    modositott = keszletek(conn)[0]
    assert modositott.tipus == TIPUS_CD_DVD
    assert (modositott.nev, modositott.cel) == ("X", "/a")


def test_modositasnal_sem_fogad_ismeretlent(conn):
    keszlet = keszlet_letrehozasa(conn, "X", "/a")

    with pytest.raises(ValueError):
        keszlet_modositasa(conn, keszlet.id, tipus="szalag")


def test_a_regi_tabla_is_olvashato(conn):
    """Egy korábbi változat indexe (a `kind` oszlop előtti séma): a
    meglévő készlet lemez-lemez marad, és új típus is írható bele."""
    conn.executescript(
        """
        CREATE TABLE backup_sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            target TEXT NOT NULL,
            file_filter TEXT NOT NULL,
            last_run TEXT
        );
        INSERT INTO backup_sets (name, target, file_filter)
        VALUES ('Régi', '/mnt/regi', 'minden');
        """
    )

    assert keszletek(conn)[0].tipus == TIPUS_LEMEZ
    keszlet_letrehozasa(conn, "Új", "/a", tipus=TIPUS_CD_DVD)
    assert {k.nev: k.tipus for k in keszletek(conn)} == {
        "Régi": TIPUS_LEMEZ, "Új": TIPUS_CD_DVD,
    }


def test_ket_kapcsolat_egyszerre_bovit(tmp_path):
    """Az átnézés lelete: frissítés utáni első futáskor a felület és a
    mentés szála egyszerre láthatja hiányzónak az oszlopot — a második
    `ALTER` nem dönthet el semmit."""
    from picasapy.index.backup_sets import ensure_backup_tables

    db = tmp_path / "regi.db"
    elso = sqlite3.connect(db)
    elso.executescript(
        "CREATE TABLE backup_sets (id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "name TEXT NOT NULL UNIQUE, target TEXT NOT NULL, "
        "file_filter TEXT NOT NULL, last_run TEXT);"
    )
    elso.commit()
    masodik = sqlite3.connect(db)
    try:
        # a második kapcsolat még a régi sémát látta, amikor az első bővít
        masodik.execute("PRAGMA table_info(backup_sets)").fetchall()
        ensure_backup_tables(elso)
        elso.commit()
        ensure_backup_tables(masodik)
    finally:
        elso.close()
        masodik.close()
