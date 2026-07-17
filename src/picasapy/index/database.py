"""Index-kapcsolat megnyitása: pragmák, séma-létrehozás, verzió-ellenőrzés."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .schema import DDL, MIGRATIONS, SCHEMA_VERSION

# ON CONFLICT ... RETURNING miatt (a bookworm 3.40-e és a CPython 3.12+
# beépített SQLite-ja is bőven újabb).
_MIN_SQLITE = (3, 35, 0)


@contextmanager
def open_index(path: str | Path) -> Iterator[sqlite3.Connection]:
    if sqlite3.sqlite_version_info < _MIN_SQLITE:
        raise RuntimeError(
            f"SQLite {'.'.join(map(str, _MIN_SQLITE))}+ szükséges, "
            f"a telepített verzió: {sqlite3.sqlite_version}"
        )
    conn = sqlite3.connect(path)
    try:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA foreign_keys=ON")
        conn.execute("PRAGMA busy_timeout=5000")
        _ensure_schema(conn)
        yield conn
    finally:
        conn.close()


def _ensure_schema(conn: sqlite3.Connection) -> None:
    version = conn.execute("PRAGMA user_version").fetchone()[0]
    if version > SCHEMA_VERSION:
        raise RuntimeError(
            f"Az index sémaverziója ({version}) újabb, mint a támogatott "
            f"({SCHEMA_VERSION}) — frissítsd a PicasaPy-t."
        )
    if version == SCHEMA_VERSION:
        return
    if version == 0:
        _create_schema(conn)
    else:
        _migrate(conn, version)


def _create_schema(conn: sqlite3.Connection) -> None:
    try:
        conn.executescript(DDL)
    except sqlite3.OperationalError as error:
        raise RuntimeError(
            "Az index-séma létrehozása nem sikerült — valószínűleg az "
            "SQLite FTS5 nélkül lett fordítva. Részletek: " + str(error)
        ) from error
    conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
    conn.commit()


def _migrate(conn: sqlite3.Connection, version: int) -> None:
    """Verziónkénti, atomi migráció: hiba esetén teljes rollback.

    A user_version-emelés a tranzakción belül van, így félbeszakadt lépés
    után az index érintetlen marad és a következő nyitás újrapróbálja.
    """
    for from_version in range(version, SCHEMA_VERSION):
        if from_version not in MIGRATIONS:
            raise RuntimeError(
                f"Nincs migrációs útvonal a(z) {from_version}. sémaverzióról — "
                "az index törölhető, a következő szinkron újraépíti."
            )
        script = (
            f"BEGIN;\n{MIGRATIONS[from_version]}\n"
            f"PRAGMA user_version={from_version + 1};\nCOMMIT;"
        )
        try:
            conn.executescript(script)
        except sqlite3.OperationalError as error:
            if conn.in_transaction:
                conn.rollback()
            raise RuntimeError(
                f"Az index migrációja ({from_version} → {from_version + 1}) "
                "nem sikerült, a változások visszagördültek. Az index csak "
                "gyorsítótár: törölhető, a következő szinkron újraépíti. "
                "Részletek: " + str(error)
            ) from error
