"""Mentés-készletek és a már elmentett fájlok nyilvántartása (#440).

Az eredeti Picasa saját szavaival: *„A Backup Set records where to store
backed-up files, and it also keeps a record of which files have been
backed up already, so you don't have to back them up again."* Tehát a
készlet **nevesített, újrafuttatható, inkrementális** mentés-definíció.

Az eredeti a `backups.xml`-ben tárolta (`Picasa2Backups` szekció, mezők:
`bkset`, `setname`, `diskroot`, fájlszűrő; az utoljára használt:
`LastBkSet`). Nálunk az index SQLite-ja a tár — a séma az `index/`
csomagé (sáv-invariáns), és a tábla lustán jön létre, a
`photo_colors`-minta szerint.

## Két tábla

| tábla | mit tárol |
|---|---|
| `backup_sets` | a készlet: név, célútvonal, fájlszűrő, utolsó futás |
| `backup_files` | mit mentettünk már el: forrás-útvonal, méret, mtime |

A `backup_files` sora a FORRÁS állapotát rögzíti a mentés pillanatában —
így a következő futás a méret/mtime eltéréséből tudja, hogy a fájl
azóta megváltozott. (Ugyanaz a feltétel-szerkezet, mint a
`photo_colors`-nál, #1500.)
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

#: A három fájlszűrő-állás — az eredeti dialógusáé (#440).
SZURO_MINDEN = "minden"
SZURO_KEPEK = "kepek"
SZURO_FENYKEPEZOGEP = "fenykepezogep"
SZUROK = (SZURO_MINDEN, SZURO_KEPEK, SZURO_FENYKEPEZOGEP)

_DDL = """
CREATE TABLE IF NOT EXISTS backup_sets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    target TEXT NOT NULL,
    file_filter TEXT NOT NULL,
    last_run TEXT
);
CREATE TABLE IF NOT EXISTS backup_files (
    set_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    PRIMARY KEY (set_id, source)
);
"""


@dataclass(frozen=True)
class MentesKeszlet:
    """Egy nevesített mentés-definíció."""

    id: int
    nev: str
    cel: str
    szuro: str
    utolso_futas: str | None = None


def ensure_backup_tables(conn: sqlite3.Connection) -> None:
    """A két tábla lusta létrehozása — idempotens."""
    conn.executescript(_DDL)


def keszlet_letrehozasa(
    conn: sqlite3.Connection, nev: str, cel: str, szuro: str = SZURO_MINDEN
) -> MentesKeszlet:
    """Új készlet. A név egyedi — ugyanazon a néven nincs két definíció."""
    if not nev.strip():
        raise ValueError("a mentés-készletnek neve kell")
    if szuro not in SZUROK:
        raise ValueError(f"ismeretlen fájlszűrő: {szuro!r} (várt: {SZUROK})")
    ensure_backup_tables(conn)
    kurzor = conn.execute(
        "INSERT INTO backup_sets (name, target, file_filter) VALUES (?, ?, ?)",
        (nev.strip(), str(cel), szuro),
    )
    return MentesKeszlet(int(kurzor.lastrowid), nev.strip(), str(cel), szuro)


def keszletek(conn: sqlite3.Connection) -> tuple[MentesKeszlet, ...]:
    """Az összes készlet, név szerint."""
    ensure_backup_tables(conn)
    sorok = conn.execute(
        "SELECT id, name, target, file_filter, last_run "
        "FROM backup_sets ORDER BY name"
    ).fetchall()
    return tuple(
        MentesKeszlet(int(s[0]), s[1], s[2], s[3], s[4]) for s in sorok
    )


def keszlet_nev_szerint(
    conn: sqlite3.Connection, nev: str
) -> MentesKeszlet | None:
    for keszlet in keszletek(conn):
        if keszlet.nev == nev:
            return keszlet
    return None


def keszlet_modositasa(
    conn: sqlite3.Connection,
    keszlet_id: int,
    *,
    nev: str | None = None,
    cel: str | None = None,
    szuro: str | None = None,
) -> None:
    """Az eredeti „Edit Set" művelete — a nyilvántartás MEGMARAD."""
    if szuro is not None and szuro not in SZUROK:
        raise ValueError(f"ismeretlen fájlszűrő: {szuro!r}")
    ensure_backup_tables(conn)
    mezok = {"name": nev, "target": cel, "file_filter": szuro}
    valtozok = {kulcs: ertek for kulcs, ertek in mezok.items() if ertek is not None}
    if not valtozok:
        return
    beallitas = ", ".join(f"{kulcs} = ?" for kulcs in valtozok)
    conn.execute(
        f"UPDATE backup_sets SET {beallitas} WHERE id = ?",
        (*valtozok.values(), keszlet_id),
    )


def keszlet_torlese(conn: sqlite3.Connection, keszlet_id: int) -> None:
    """A készlet ÉS a hozzá tartozó nyilvántartás törlése.

    Az eredeti megerősítést kér a törlés előtt — az a felület dolga; itt
    az a fontos, hogy a nyilvántartás ne maradjon árván, mert egy
    ugyanilyen id-jű új készlet örökölné."""
    ensure_backup_tables(conn)
    conn.execute("DELETE FROM backup_files WHERE set_id = ?", (keszlet_id,))
    conn.execute("DELETE FROM backup_sets WHERE id = ?", (keszlet_id,))


def elmentett_allapot(
    conn: sqlite3.Connection, keszlet_id: int
) -> dict[str, tuple[int, int]]:
    """A készlet nyilvántartása: forrás-útvonal → (méret, mtime_ns)."""
    ensure_backup_tables(conn)
    sorok = conn.execute(
        "SELECT source, size, mtime_ns FROM backup_files WHERE set_id = ?",
        (keszlet_id,),
    ).fetchall()
    return {sor[0]: (int(sor[1]), int(sor[2])) for sor in sorok}


def jegyezd_fel_az_elmentettet(
    conn: sqlite3.Connection,
    keszlet_id: int,
    tetelek: list[tuple[str, int, int]],
) -> None:
    """A sikeresen átmásolt fájlok felvétele a nyilvántartásba.

    ⚠️ Csak a MÁSOLÁS UTÁN hívható: ha előre jegyeznénk fel, egy megszakadt
    mentés után a következő futás átugraná a ki nem másolt fájlokat."""
    if not tetelek:
        return
    ensure_backup_tables(conn)
    conn.executemany(
        "INSERT INTO backup_files (set_id, source, size, mtime_ns) "
        "VALUES (?, ?, ?, ?) "
        "ON CONFLICT(set_id, source) DO UPDATE SET "
        "size = excluded.size, mtime_ns = excluded.mtime_ns",
        [(keszlet_id, forras, meret, mtime) for forras, meret, mtime in tetelek],
    )


def jegyezd_fel_a_futast(
    conn: sqlite3.Connection, keszlet_id: int, idopont: str
) -> None:
    conn.execute(
        "UPDATE backup_sets SET last_run = ? WHERE id = ?",
        (idopont, keszlet_id),
    )
