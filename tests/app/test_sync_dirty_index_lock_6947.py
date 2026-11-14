"""#6947: a dirty sync waits for the shared index writer's lock."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

from picasapy.app import library_controller_sync as _sync_facade  # noqa: F401
from picasapy.app import library_controller_sync_dirty as dirty_module
from picasapy.app.index_writer_queue import IndexWriterQueue
from picasapy.index import open_index, sync as sync_module
from picasapy.index.sync_photos import _prune_albums as original_prune_albums


class _Signal:
    def __init__(self):
        self.calls = 0

    def emit(self, *_args):
        self.calls += 1


def test_parallel_index_writer_and_sync_dirty_wait_at_prune_once(
    tmp_path, monkeypatch
):
    """The shared lock serializes the queue runner and dirty worker."""
    root = tmp_path / "kepek"
    folder = root / "nyaralas"
    folder.mkdir(parents=True)
    db_path = tmp_path / "index.db"
    with open_index(db_path):
        pass

    writer_has_lock = threading.Event()
    release_writer = threading.Event()
    reached_prune = threading.Event()
    prune_finished = threading.Event()
    started_names: list[str | None] = []
    thread_errors: list[tuple[str, BaseException]] = []
    writer_runs: list[None] = []
    sync_calls: list[Path] = []
    prune_calls: list[str] = []
    threads: list[threading.Thread] = []

    def start_background(worker, *, name, **_kwargs):
        started_names.append(name)

        def run():
            try:
                worker()
            except BaseException as error:  # noqa: BLE001 - worker errors are asserted below
                thread_errors.append((name, error))

        thread = threading.Thread(target=run, name=name, daemon=True)
        threads.append(thread)
        thread.start()
        return thread

    controller = SimpleNamespace(
        _sync_running=False,
        _dirty_running=False,
        _sweep_running=False,
        _filetype_scan_snapshot=None,
        _db_path=db_path,
        _dirty_ujjlenyomatok_tar=lambda: {},
        _root_for_folder=lambda _path: str(root),
        _folder_manager_path_excluded=lambda _path, _root: False,
        _folder_manager_excludes_for_root=lambda _root: (),
        _side_pane_cache_ready=lambda _conn: True,
        _finish_index_sync=lambda *_args, **_kwargs: None,
        _make_should_stop=lambda _root: lambda: False,
        _start_background=start_background,
        cancelScan=lambda: None,
        syncFinished=_Signal(),
        syncFailed=_Signal(),
    )
    queue_errors: list[BaseException] = []
    writer_queue = IndexWriterQueue(
        lambda worker, *, name: start_background(worker, name=name),
        is_busy=lambda: bool(controller._dirty_running),
        on_error=queue_errors.append,
    )

    def queued_writer():
        writer_runs.append(None)
        with open_index(db_path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            writer_has_lock.set()
            if not release_writer.wait(5.0):
                raise TimeoutError("az indexíró nem kapott feloldást")

    assert writer_queue.submit(queued_writer, name="tesztíró") is True

    @contextmanager
    def short_busy_timeout(path):
        with open_index(path) as conn:
            conn.execute("PRAGMA busy_timeout=50")
            yield conn

    monkeypatch.setattr(dirty_module, "open_index", short_busy_timeout)
    monkeypatch.setattr(dirty_module, "folder_fingerprint", lambda _path: None)
    monkeypatch.setattr(
        dirty_module,
        "_legacy",
        lambda: SimpleNamespace(
            _coalesce_watcher_changes=lambda values: values,
            _sqlite_write_lock_error=lambda _error: False,
            sync_folder=lambda _conn, _root, path, **_kwargs: sync_calls.append(
                Path(path)
            ),
            logger=SimpleNamespace(warning=lambda *_args: None),
        ),
    )

    def observed_prune(conn):
        prune_calls.append(threading.current_thread().name)
        reached_prune.set()
        try:
            return original_prune_albums(conn)
        finally:
            prune_finished.set()

    monkeypatch.setattr(sync_module, "_prune_albums", observed_prune)

    try:
        assert writer_has_lock.wait(5.0), "az indexíró nem fogta meg a közös zárat"
        dirty_module._LibrarySyncDirtyMixin._on_folders_dirty(
            controller, [str(folder)]
        )
        assert reached_prune.wait(5.0), "a sync-dirty nem jutott el az albumtakarításig"
        # Az eredeti kód 50 ms után itt dob. A javításnak meg kell várnia az
        # indexíró feloldását, amelyet csak ezután engedünk el.
        finished_before_release = prune_finished.wait(0.2)
    finally:
        release_writer.set()

    assert writer_queue.wait_idle(10.0), "az indexíró sora nem ürült ki"
    for thread in threads:
        thread.join(5.0)
        assert not thread.is_alive(), f"beragadt háttérszál: {thread.name}"

    assert finished_before_release is False, (
        "a sync-dirty a sorban futó író zárának feloldása előtt kilépett"
    )
    assert thread_errors == [], thread_errors
    assert queue_errors == [], queue_errors
    assert started_names.count(IndexWriterQueue.RUNNER_NAME) == 1, started_names
    assert started_names.count("picasapy-sync-dirty") == 1, started_names
    assert writer_runs == [None], writer_runs
    assert sync_calls == [folder], sync_calls
    assert len(prune_calls) == 1, prune_calls
