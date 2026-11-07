"""Index-kapcsolat megnyitása: pragmák, séma-létrehozás, verzió-ellenőrzés."""

from __future__ import annotations

import os
import re
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .schema import DDL, MIGRATIONS, SCHEMA_VERSION

# ON CONFLICT ... RETURNING miatt (a bookworm 3.40-e és a CPython 3.12+
# beépített SQLite-ja is bőven újabb).
_MIN_SQLITE = (3, 35, 0)

_WRITE_LOCKS: dict[str, threading.RLock] = {}
_OPEN_CONNECTION_COUNTS: dict[str, int] = {}
_WRITE_LOCKS_GUARD = threading.Lock()
_DEFAULT_BUSY_TIMEOUT_SECONDS = 5.0

_SQLITE_COMMENTS = re.compile(r"/\*.*?\*/|--[^\r\n]*", re.DOTALL)
_SQLITE_WORD = re.compile(r"[A-Za-z_]+")
_SQLITE_DML = re.compile(r"\b(?:INSERT|UPDATE|DELETE|REPLACE)\b", re.IGNORECASE)
_SQLITE_WRITE_WORDS = frozenset(
    {
        "ALTER",
        "ANALYZE",
        "ATTACH",
        "CREATE",
        "DELETE",
        "DETACH",
        "DROP",
        "INSERT",
        "REINDEX",
        "RELEASE",
        "REPLACE",
        "ROLLBACK",
        "SAVEPOINT",
        "UPDATE",
        "VACUUM",
        "END",
        "COMMIT",
    }
)
_SQLITE_WRITE_PRAGMAS = frozenset(
    {
        "application_id",
        "auto_vacuum",
        "encoding",
        "journal_mode",
        "page_size",
        "schema_version",
        "user_version",
    }
)


def _write_lock_for(path: str | Path) -> threading.RLock:
    """Azonos indexútvonalhoz minden szál ugyanazt az író/checkpoint zárat kapja."""
    key = _index_path_key(path)
    if key is None:
        # Minden memóriakapcsolat külön adatbázis, nincs mit megosztani.
        return threading.RLock()
    with _WRITE_LOCKS_GUARD:
        return _WRITE_LOCKS.setdefault(key, threading.RLock())


def _index_path_key(path: str | Path) -> str | None:
    path_text = os.fspath(path)
    if path_text == ":memory:":
        return None
    return os.path.normcase(str(Path(path_text).resolve()))


def _register_open_connection(path: str | Path) -> tuple[str | None, threading.RLock]:
    """A SQLite megnyitása előtt lefoglalja a kapcsolat helyét a számlálóban."""
    key = _index_path_key(path)
    lock = _write_lock_for(path)
    if key is not None:
        with _WRITE_LOCKS_GUARD:
            _OPEN_CONNECTION_COUNTS[key] = _OPEN_CONNECTION_COUNTS.get(key, 0) + 1
    return key, lock


def _unregister_open_connection(key: str | None) -> None:
    if key is None:
        return
    with _WRITE_LOCKS_GUARD:
        count = _OPEN_CONNECTION_COUNTS.get(key, 0)
        if count <= 1:
            _OPEN_CONNECTION_COUNTS.pop(key, None)
        else:
            _OPEN_CONNECTION_COUNTS[key] = count - 1


def _restore_open_connection(key: str | None) -> None:
    if key is None:
        return
    with _WRITE_LOCKS_GUARD:
        _OPEN_CONNECTION_COUNTS[key] = _OPEN_CONNECTION_COUNTS.get(key, 0) + 1


def _begin_connection_close(key: str | None) -> bool:
    """Levon egy kapcsolatot; igaz, ha ez volt a legutolsó nyitott kapcsolat."""
    if key is None:
        return True
    with _WRITE_LOCKS_GUARD:
        count = _OPEN_CONNECTION_COUNTS.get(key, 0)
        if count <= 1:
            _OPEN_CONNECTION_COUNTS.pop(key, None)
            return True
        _OPEN_CONNECTION_COUNTS[key] = count - 1
        return False


@contextmanager
def _serialize_index_writes(path: str | Path) -> Iterator[None]:
    """Zárójelbe tesz egy olyan indexírást, amely nem `open_index`-et használ."""
    key, lock = _register_open_connection(path)
    acquired = False
    try:
        if not lock.acquire(timeout=_DEFAULT_BUSY_TIMEOUT_SECONDS):
            raise sqlite3.OperationalError("database is locked")
        acquired = True
        yield
    finally:
        try:
            if acquired:
                lock.release()
        finally:
            _unregister_open_connection(key)


def _needs_write_lock(sql: str) -> bool:
    """Író SQL-t és checkpointot ismer fel; a sima olvasókat nem sorosítja."""
    normalized = _SQLITE_COMMENTS.sub(" ", sql).lstrip()
    first_word = _SQLITE_WORD.match(normalized)
    if first_word is None:
        return False
    command = first_word.group().upper()

    if command in _SQLITE_WRITE_WORDS:
        return True
    if command == "BEGIN":
        return bool(re.match(r"BEGIN\s+(?:IMMEDIATE|EXCLUSIVE)\b", normalized, re.I))
    if command == "WITH":
        return bool(_SQLITE_DML.search(normalized))
    if command != "PRAGMA":
        return False

    pragma_match = re.match(
        r"(?:[A-Za-z_]\w*\s*\.\s*)?([A-Za-z_]\w*)",
        normalized[first_word.end() :].lstrip(),
    )
    if pragma_match is None:
        return False
    pragma = pragma_match.group(1).lower()
    if pragma in {"wal_checkpoint", "incremental_vacuum", "optimize"}:
        return True
    return pragma in _SQLITE_WRITE_PRAGMAS and "=" in normalized


class _GuardedCursor(sqlite3.Cursor):
    """A kurzoron át indított írásokat is az indexkapcsolat zárja védi."""

    def execute(self, sql, parameters=(), /):
        connection = self.connection
        return connection._run_guarded_sql(
            sql, lambda: sqlite3.Cursor.execute(self, sql, parameters)
        )

    def executemany(self, sql, seq_of_parameters, /):
        connection = self.connection
        return connection._run_guarded_sql(
            sql,
            lambda: sqlite3.Cursor.executemany(self, sql, seq_of_parameters),
        )

    def executescript(self, sql_script, /):
        connection = self.connection
        return connection._run_guarded_sql(
            sql_script,
            lambda: sqlite3.Cursor.executescript(self, sql_script),
            force=True,
        )


class _GuardedConnection(sqlite3.Connection):
    """Az író tranzakciók és WAL-checkpointok kizárólagos sora indexenként."""

    def _set_write_lock(
        self, lock: threading.RLock, path_key: str | None
    ) -> None:
        self._write_lock = lock
        self._holds_write_lock = False
        self._write_lock_owner: int | None = None
        self._index_path_key = path_key
        self._registered_open = True

    def _busy_timeout_seconds(self) -> float:
        try:
            timeout_ms = sqlite3.Connection.execute(
                self, "PRAGMA busy_timeout"
            ).fetchone()[0]
        except (sqlite3.Error, TypeError, IndexError):
            return _DEFAULT_BUSY_TIMEOUT_SECONDS
        return max(0, int(timeout_ms)) / 1000.0

    def _acquire_write_lock(self) -> None:
        if not self._write_lock.acquire(timeout=self._busy_timeout_seconds()):
            raise sqlite3.OperationalError("database is locked")
        self._write_lock_owner = threading.get_ident()

    def _release_acquired_lock(self) -> None:
        if self._write_lock_owner != threading.get_ident():
            raise sqlite3.ProgrammingError(
                "Az indexzárat csak a tulajdonos szál oldhatja fel."
            )
        self._write_lock.release()
        self._write_lock_owner = None

    def _release_write_lock(self) -> None:
        if self._holds_write_lock:
            if self._write_lock_owner != threading.get_ident():
                raise sqlite3.ProgrammingError(
                    "Az indexzárat csak a tulajdonos szál oldhatja fel."
                )
            self._write_lock.release()
            self._holds_write_lock = False
            self._write_lock_owner = None

    def execute(self, sql, parameters=(), /):
        return self._run_guarded_sql(
            sql, lambda: sqlite3.Connection.execute(self, sql, parameters)
        )

    def executemany(self, sql, seq_of_parameters, /):
        return self._run_guarded_sql(
            sql,
            lambda: sqlite3.Connection.executemany(self, sql, seq_of_parameters),
        )

    def executescript(self, sql_script, /):
        return self._run_guarded_sql(
            sql_script,
            lambda: sqlite3.Connection.executescript(self, sql_script),
            force=True,
        )

    def _run_guarded_sql(self, sql: str, operation, *, force: bool = False):
        needs_lock = force or _needs_write_lock(sql)
        if not needs_lock and not self._holds_write_lock:
            return operation()

        already_held = self._holds_write_lock
        if already_held and self._write_lock_owner != threading.get_ident():
            raise sqlite3.ProgrammingError(
                "Az indexkapcsolatot csak a zár tulajdonos szála használhatja."
            )
        if not already_held:
            self._acquire_write_lock()
        try:
            result = operation()
        except BaseException:
            if self.in_transaction:
                self._holds_write_lock = True
            elif already_held:
                self._release_write_lock()
            else:
                self._release_acquired_lock()
            raise

        if self.in_transaction:
            self._holds_write_lock = True
        elif already_held:
            self._release_write_lock()
        else:
            self._release_acquired_lock()
        return result

    def cursor(self, factory=None):
        return sqlite3.Connection.cursor(self, factory or _GuardedCursor)

    def commit(self):
        return self._run_guarded_sql(
            "COMMIT", lambda: sqlite3.Connection.commit(self), force=True
        )

    def rollback(self):
        return self._run_guarded_sql(
            "ROLLBACK", lambda: sqlite3.Connection.rollback(self), force=True
        )

    def close(self):
        if not self._registered_open:
            return sqlite3.Connection.close(self)
        if (
            self._holds_write_lock
            and self._write_lock_owner != threading.get_ident()
        ):
            raise sqlite3.ProgrammingError(
                "Az indexkapcsolatot csak a zár tulajdonos szála zárhatja le."
            )

        is_last_connection = _begin_connection_close(self._index_path_key)
        already_held = self._holds_write_lock
        acquired = False
        if not already_held and is_last_connection:
            try:
                self._acquire_write_lock()
            except BaseException:
                _restore_open_connection(self._index_path_key)
                raise
            acquired = True
        try:
            result = sqlite3.Connection.close(self)
        except BaseException:
            _restore_open_connection(self._index_path_key)
            if acquired:
                self._release_acquired_lock()
            raise
        else:
            self._registered_open = False
            if already_held:
                self._release_write_lock()
            elif acquired:
                self._release_acquired_lock()
            return result

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        return False


@contextmanager
def open_index(path: str | Path) -> Iterator[sqlite3.Connection]:
    if sqlite3.sqlite_version_info < _MIN_SQLITE:
        raise RuntimeError(
            f"SQLite {'.'.join(map(str, _MIN_SQLITE))}+ szükséges, "
            f"a telepített verzió: {sqlite3.sqlite_version}"
        )
    path_key, write_lock = _register_open_connection(path)
    try:
        conn = sqlite3.connect(path, factory=_GuardedConnection)
    except BaseException:
        _unregister_open_connection(path_key)
        raise
    conn._set_write_lock(write_lock, path_key)
    try:
        conn.row_factory = sqlite3.Row
        journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        if str(journal_mode).lower() != "wal":
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
