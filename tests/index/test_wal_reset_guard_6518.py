"""#6518: az indexírás és WAL-checkpoint ne fusson párhuzamosan."""

from __future__ import annotations

import sqlite3
import threading

import pytest

from picasapy.index import open_index
from picasapy.index.database import _needs_write_lock


class _ObservedRLock:
    """RLock, amely jelzi, ha a megadott szál zárolást kér."""

    def __init__(self, watched_thread: str):
        self._lock = threading.RLock()
        self.watched_thread = watched_thread
        self.acquire_attempted = threading.Event()

    def acquire(self, blocking=True, timeout=-1):
        if threading.current_thread().name == self.watched_thread:
            self.acquire_attempted.set()
        if timeout == -1:
            return self._lock.acquire(blocking)
        return self._lock.acquire(blocking, timeout)

    def release(self):
        self._lock.release()


def test_checkpoint_waits_until_another_connection_commits(tmp_path, monkeypatch):
    import picasapy.index.database as database

    db_path = tmp_path / "index.db"
    lock = _ObservedRLock("index-checkpointer")
    monkeypatch.setattr(database, "_write_lock_for", lambda _path: lock)
    with open_index(db_path) as conn:
        conn.execute("CREATE TABLE canary (value INTEGER PRIMARY KEY)")
        conn.commit()

    write_started = threading.Event()
    finish_write = threading.Event()
    checkpoint_finished = threading.Event()
    errors: list[BaseException] = []

    def write_transaction():
        try:
            with open_index(db_path) as conn:
                conn.execute("INSERT INTO canary(value) VALUES (1)")
                write_started.set()
                if not finish_write.wait(5):
                    raise TimeoutError("az író tranzakció nem kapott feloldást")
                conn.commit()
        except BaseException as error:
            errors.append(error)

    def checkpoint():
        try:
            with open_index(db_path) as conn:
                conn.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()
        except BaseException as error:
            errors.append(error)
        finally:
            checkpoint_finished.set()

    writer = threading.Thread(target=write_transaction, name="index-writer")
    checkpointer = threading.Thread(target=checkpoint, name="index-checkpointer")
    writer.start()
    assert write_started.wait(5), "az író tranzakció nem indult el"
    checkpointer.start()
    try:
        assert lock.acquire_attempted.wait(5), "a checkpoint nem kérte el a zárat"
        lock_is_free = lock.acquire(blocking=False)
        if lock_is_free:
            lock.release()
        assert not lock_is_free, "az író nem tartja a zárat"
        assert not checkpoint_finished.is_set(), (
            "a WAL-checkpoint az író tranzakció commitja előtt lefutott"
        )
    finally:
        finish_write.set()

    writer.join(5)
    checkpointer.join(5)
    assert not writer.is_alive(), "az író szál beragadt"
    assert not checkpointer.is_alive(), "a checkpoint-szál beragadt"
    assert errors == []

    with open_index(db_path) as conn:
        assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert conn.execute("SELECT value FROM canary").fetchone()[0] == 1


def test_reader_connection_closes_without_waiting_for_writer(tmp_path, monkeypatch):
    import picasapy.index.database as database

    db_path = tmp_path / "index.db"
    lock = _ObservedRLock("index-reader")
    monkeypatch.setattr(database, "_write_lock_for", lambda _path: lock)
    with open_index(db_path) as conn:
        conn.execute("CREATE TABLE canary (value INTEGER PRIMARY KEY)")

    writer_started = threading.Event()
    release_writer = threading.Event()
    reader_ready = threading.Event()
    release_reader = threading.Event()
    reader_closed = threading.Event()
    errors: list[BaseException] = []

    def write_transaction():
        try:
            with open_index(db_path) as conn:
                conn.execute("INSERT INTO canary(value) VALUES (1)")
                writer_started.set()
                if not release_writer.wait(5):
                    raise TimeoutError("az író tranzakció nem kapott feloldást")
        except BaseException as error:
            errors.append(error)

    def close_reader():
        try:
            with open_index(db_path) as conn:
                conn.execute("SELECT value FROM canary").fetchall()
                reader_ready.set()
                if not release_reader.wait(5):
                    raise TimeoutError("az olvasó kapcsolat nem kapott feloldást")
        except BaseException as error:
            errors.append(error)
        finally:
            reader_closed.set()

    writer = threading.Thread(target=write_transaction, name="index-writer")
    reader = threading.Thread(target=close_reader, name="index-reader")
    writer.start()
    assert writer_started.wait(5), "az író tranzakció nem indult el"
    reader.start()
    try:
        assert reader_ready.wait(5), "az olvasó kapcsolat nem nyílt meg"
        release_reader.set()
        assert reader_closed.wait(5), "az olvasó kapcsolat zárása megvárta az írót"
        assert not lock.acquire_attempted.is_set(), (
            "az olvasó kapcsolat zárása fölöslegesen kérte el az írózárat"
        )
    finally:
        release_writer.set()
    writer.join(5)
    reader.join(5)
    assert not writer.is_alive(), "az író szál beragadt"
    assert not reader.is_alive(), "az olvasó szál beragadt"
    assert errors == []


def test_reader_connection_closes_during_compaction(tmp_path, monkeypatch):
    from contextlib import contextmanager

    import picasapy.index.compact as compact_module
    import picasapy.index.database as database

    db_path = tmp_path / "index.db"
    lock = _ObservedRLock("index-reader")
    monkeypatch.setattr(database, "_write_lock_for", lambda _path: lock)
    with open_index(db_path) as conn:
        conn.execute("CREATE TABLE canary (value INTEGER PRIMARY KEY)")
        conn.executemany(
            "INSERT INTO canary(value) VALUES (?)", ((value,) for value in range(100))
        )

    compact_started = threading.Event()
    release_compact = threading.Event()
    reader_ready = threading.Event()
    release_reader = threading.Event()
    reader_closed = threading.Event()
    errors: list[BaseException] = []
    original_serialize = compact_module._serialize_index_writes

    @contextmanager
    def observed_serialize(path):
        with original_serialize(path):
            compact_started.set()
            if not release_compact.wait(5):
                raise TimeoutError("a tömörítés nem kapott feloldást")
            yield

    monkeypatch.setattr(compact_module, "_serialize_index_writes", observed_serialize)

    def compact():
        try:
            compact_module.compact_database(db_path)
        except BaseException as error:
            errors.append(error)

    def close_reader():
        try:
            with open_index(db_path) as conn:
                conn.execute("SELECT value FROM canary").fetchall()
                reader_ready.set()
                if not release_reader.wait(5):
                    raise TimeoutError("az olvasó kapcsolat nem kapott feloldást")
        except BaseException as error:
            errors.append(error)
        finally:
            reader_closed.set()

    reader = threading.Thread(target=close_reader, name="index-reader")
    compactor = threading.Thread(target=compact, name="index-compactor")
    reader.start()
    assert reader_ready.wait(5), "az olvasó kapcsolat nem nyílt meg"
    compactor.start()
    try:
        assert compact_started.wait(5), "a tömörítés nem jutott el a zárig"
        release_reader.set()
        assert reader_closed.wait(5), "az olvasó kapcsolat zárása megvárta a VACUUM-ot"
        assert not lock.acquire_attempted.is_set(), (
            "az olvasó kapcsolat zárása a tömörítés alatt kérte el az írózárat"
        )
    finally:
        release_compact.set()
    reader.join(5)
    compactor.join(5)
    assert not reader.is_alive(), "az olvasó szál beragadt"
    assert not compactor.is_alive(), "a tömörítő szál beragadt"
    assert errors == []


def test_write_lock_wait_obeys_connection_busy_timeout(tmp_path, monkeypatch):
    import picasapy.index.database as database

    db_path = tmp_path / "index.db"
    lock = threading.RLock()
    monkeypatch.setattr(database, "_write_lock_for", lambda _path: lock)
    with open_index(db_path) as conn:
        conn.execute("CREATE TABLE canary (value INTEGER PRIMARY KEY)")

    writer_started = threading.Event()
    release_writer = threading.Event()
    contender_started = threading.Event()
    contender_finished = threading.Event()
    errors: list[BaseException] = []

    def write_transaction():
        with open_index(db_path) as conn:
            conn.execute("INSERT INTO canary(value) VALUES (1)")
            writer_started.set()
            if not release_writer.wait(5):
                raise TimeoutError("az író tranzakció nem kapott feloldást")

    def competing_write():
        try:
            with open_index(db_path) as conn:
                conn.execute("PRAGMA busy_timeout=100")
                contender_started.set()
                conn.execute("INSERT INTO canary(value) VALUES (2)")
        except BaseException as error:
            errors.append(error)
        finally:
            contender_finished.set()

    writer = threading.Thread(target=write_transaction, name="index-writer")
    contender = threading.Thread(target=competing_write, name="index-contender")
    writer.start()
    assert writer_started.wait(5), "az író tranzakció nem indult el"
    contender.start()
    try:
        assert contender_started.wait(5), "a második író nem indult el"
        assert contender_finished.wait(2), "a második író túllépte a busy_timeout értékét"
    finally:
        release_writer.set()
    writer.join(5)
    contender.join(5)
    assert not writer.is_alive(), "az író szál beragadt"
    assert not contender.is_alive(), "a második író szála beragadt"
    assert len(errors) == 1
    assert isinstance(errors[0], sqlite3.OperationalError)
    assert str(errors[0]) == "database is locked"


@pytest.mark.parametrize(
    "sql",
    [
        "PRAGMA main.wal_checkpoint(PASSIVE)",
        "PRAGMA main.journal_mode=WAL",
    ],
)
def test_schema_qualified_write_pragma_is_guarded(sql):
    assert _needs_write_lock(sql)


def test_cursor_executescript_keeps_write_lock_for_open_transaction(tmp_path):
    with open_index(tmp_path / "index.db") as conn:
        conn.cursor().executescript(
            "BEGIN IMMEDIATE; INSERT INTO folders(path) VALUES ('/script');"
        )

        assert conn.in_transaction
        assert conn._holds_write_lock

        conn.rollback()


def test_failed_lock_release_keeps_connection_ownership_flag(tmp_path):
    class _FailingLock:
        def release(self):
            raise RuntimeError("nem tulajdonos szál")

    with open_index(tmp_path / "index.db") as conn:
        conn.execute("BEGIN IMMEDIATE")
        original_lock = conn._write_lock
        conn._write_lock = _FailingLock()
        try:
            with pytest.raises(RuntimeError, match="nem tulajdonos"):
                conn._release_write_lock()
            assert conn._holds_write_lock
        finally:
            conn._write_lock = original_lock
            conn._holds_write_lock = True
            conn.rollback()


def test_non_owner_cannot_clear_another_threads_lock_ownership(tmp_path):
    with open_index(tmp_path / "index.db") as conn:
        conn.execute("BEGIN IMMEDIATE")
        errors: list[BaseException] = []

        def release_from_other_thread():
            try:
                conn._release_write_lock()
            except BaseException as error:
                errors.append(error)

        releaser = threading.Thread(target=release_from_other_thread)
        releaser.start()
        releaser.join(5)

        assert not releaser.is_alive()
        assert len(errors) == 1
        assert isinstance(errors[0], sqlite3.ProgrammingError)
        assert conn._holds_write_lock
        conn._holds_write_lock = True
        conn.rollback()
