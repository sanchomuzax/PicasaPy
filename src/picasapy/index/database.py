"""Index-kapcsolat megnyitása: pragmák, séma-létrehozás, verzió-ellenőrzés."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .schema import DDL, SCHEMA_VERSION

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
    if version < SCHEMA_VERSION:
        try:
            conn.executescript(DDL)
        except sqlite3.OperationalError as error:
            raise RuntimeError(
                "Az index-séma létrehozása nem sikerült — valószínűleg az "
                "SQLite FTS5 nélkül lett fordítva. Részletek: " + str(error)
            ) from error
        conn.execute(f"PRAGMA user_version={SCHEMA_VERSION}")
        conn.commit()
