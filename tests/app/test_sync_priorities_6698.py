"""#6698: a szinkron- és előtöltő munkák alacsony prioritásúak."""

from __future__ import annotations

from types import SimpleNamespace

from picasapy.app import library_controller_sync as _sync_facade  # noqa: F401
from picasapy.app import library_controller_sync_dirty as dirty_module
from picasapy.app import library_controller_sync_rescan as rescan_module
from picasapy.app import library_controller_sync_sweep as sweep_module
from picasapy.app import thumbnail_provider_jobs as thumbnail_jobs


class _Signal:
    def __init__(self, events, name):
        self.events = events
        self.name = name

    def emit(self, *args):
        self.events.append((self.name, args))


def test_rescan_elore_betolti_a_cv2_t_a_hivas_szalatol(monkeypatch):
    events = []
    monkeypatch.setattr(
        rescan_module,
        "elore_betolt",
        lambda: events.append("cv2-load"),
        raising=False,
    )
    controller = SimpleNamespace(
        _sync_running=False,
        _dirty_running=False,
        _sync_worker=lambda: None,
        cancelScan=lambda: None,
        _start_background=lambda worker, **kwargs: events.append("worker-start"),
    )
    def start_rescan(worker):
        return rescan_module._LibrarySyncRescanMixin._start_rescan(controller, worker)

    controller._start_rescan = start_rescan

    rescan_module._LibrarySyncRescanMixin.rescan(controller)

    assert events == ["cv2-load", "worker-start"]


def test_teljes_szinkron_worker_alacsony_prioritasu(tmp_path, monkeypatch):
    from picasapy.index import open_index

    events = []
    db_path = tmp_path / "index.db"
    with open_index(db_path):
        pass
    monkeypatch.setattr(
        rescan_module,
        "kerjafonal_alacsony_prioritasa",
        lambda: events.append("low-priority"),
        raising=False,
    )
    controller = SimpleNamespace(
        _sync_worker_filetype_snapshot=None,
        _filetype_scan_snapshot=None,
        _roots=(),
        _db_path=db_path,
        _precompute_side_pane=lambda _conn: events.append("sync"),
        syncFailed=_Signal(events, "failed"),
        syncFinished=_Signal(events, "finished"),
    )

    rescan_module._LibrarySyncRescanMixin._sync_worker_roots(controller, ())

    assert events[:2] == ["low-priority", "sync"]


def test_dirty_worker_alacsony_prioritasu_es_egyetlen_album_prune(
    tmp_path, monkeypatch
):
    from picasapy.index import open_index, sync as sync_module
    from picasapy import lazy_cv2

    root = tmp_path / "kepek"
    folders = (root / "egy", root / "ketto")
    for folder in folders:
        folder.mkdir(parents=True)
    db_path = tmp_path / "index.db"
    with open_index(db_path):
        pass

    events = []
    workers = []
    original_prune = sync_module._prune_albums

    def count_prune(conn):
        events.append("prune")
        return original_prune(conn)

    monkeypatch.setattr(sync_module, "_prune_albums", count_prune)
    monkeypatch.setattr(
        dirty_module,
        "kerjafonal_alacsony_prioritasa",
        lambda: events.append("low-priority"),
        raising=False,
    )
    monkeypatch.setattr(dirty_module, "folder_fingerprint", lambda _path: None)
    monkeypatch.setattr(dirty_module, "open_index", lambda _path: open_index(db_path))
    monkeypatch.setattr(
        lazy_cv2, "elore_betolt", lambda: events.append("cv2-load")
    )

    legacy = SimpleNamespace(
        _coalesce_watcher_changes=lambda values: values,
        _sqlite_write_lock_error=lambda _error: False,
        sync_folder=sync_module.sync_folder,
        logger=SimpleNamespace(exception=lambda *_args, **_kwargs: None),
    )
    monkeypatch.setattr(dirty_module, "_legacy", lambda: legacy)
    controller = SimpleNamespace(
        _sync_running=False,
        _dirty_running=False,
        _filetype_scan_snapshot=None,
        _db_path=db_path,
        cancelScan=lambda: None,
        _dirty_ujjlenyomatok_tar=lambda: {},
        _root_for_folder=lambda _path: str(root),
        _folder_manager_path_excluded=lambda _path, _root: False,
        _folder_manager_excludes_for_root=lambda _root: (),
        _make_should_stop=lambda _root: lambda: False,
        _start_background=lambda worker, **_kwargs: workers.append(worker),
        syncFinished=_Signal(events, "finished"),
        syncFailed=_Signal(events, "failed"),
    )

    dirty_module._LibrarySyncDirtyMixin._on_folders_dirty(
        controller, [str(folder) for folder in folders]
    )
    assert events == ["cv2-load"]
    workers[0]()

    assert events.index("cv2-load") < events.index("low-priority")
    assert events.count("low-priority") == 1
    assert events.count("prune") == 1
    assert events.index("low-priority") < events.index("prune")


def test_sweeper_alacsony_prioritasu(monkeypatch):
    events = []
    workers = []
    monkeypatch.setattr(
        sweep_module,
        "kerjafonal_alacsony_prioritasa",
        lambda: events.append("low-priority"),
        raising=False,
    )
    monkeypatch.setattr(
        sweep_module,
        "_legacy",
        lambda: SimpleNamespace(
            _dedupe_paths=lambda values: tuple(dict.fromkeys(values)),
            logger=SimpleNamespace(exception=lambda *_args, **_kwargs: None),
        ),
    )
    controller = SimpleNamespace(
        _current_folder="kijelolt",
        _sync_running=False,
        _sweep_running=False,
        _sweep_candidates=lambda _folder: ("masik",),
        _projekt_kimeneti_mappak=lambda: (),
        _stale_feed_folders=lambda _batch: events.append("sweep") or (),
        _start_background=lambda worker, **_kwargs: workers.append(worker),
        watcherDirty=_Signal(events, "dirty"),
    )

    sweep_module._LibrarySyncSweepMixin._poll_current_folder(controller)
    workers[0]()

    assert events[:2] == ["low-priority", "sweep"]


def test_thumbnail_prefetch_alacsony_prioritassal_fut(monkeypatch):
    events = []
    monkeypatch.setattr(
        thumbnail_jobs,
        "kerjafonal_alacsony_prioritasa",
        lambda: events.append("low-priority"),
        raising=False,
    )
    job = thumbnail_jobs._PrefetchJob(
        SimpleNamespace(_run_prefetch_job=lambda: events.append("prefetch"))
    )

    job.run()

    assert events == ["low-priority", "prefetch"]
