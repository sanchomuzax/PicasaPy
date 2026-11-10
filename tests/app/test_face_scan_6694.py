"""#6694: a szinkron utáni arckeresés csak az új munkát végzi el."""

from __future__ import annotations

import time
from contextlib import contextmanager

import numpy as np

from picasapy.index import all_photos, open_index
from picasapy.paths import path_key
from support.jpeg_factory import make_jpeg
from test_face_scan_controller import _FakeDetector, _make_controller, _run


def test_pending_folders_reuse_ini_and_exclusion_and_read_face_state_once(
    qt_app, tmp_path, monkeypatch
):
    import picasapy.app.face_ignore_ini as ini_module

    root = tmp_path / "kepek"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(100, 100))
    exclusion_calls = []
    ctl = _make_controller(
        qt_app,
        tmp_path,
        root,
        face_detection_enabled=lambda folder: exclusion_calls.append(
            path_key(folder)
        )
        or True,
    )
    ini_calls = []
    original_load_existing = ini_module.load_existing

    def counted_load_existing(*args, **kwargs):
        ini_calls.append(args[0])
        return original_load_existing(*args, **kwargs)

    monkeypatch.setattr(ini_module, "load_existing", counted_load_existing)
    statements = []
    with open_index(tmp_path / "index.db") as conn:
        photos = all_photos(conn)
        conn.set_trace_callback(statements.append)
        pending = ctl._build_pending(conn, photos)

    face_state_reads = [
        statement
        for statement in statements
        if "FROM FACE_SCAN" in statement.upper()
    ]
    assert len(pending) == 3
    assert len(face_state_reads) == 1
    assert len(ini_calls) == 1
    assert exclusion_calls == [path_key(root)]


def test_unchanged_automatic_scan_does_not_read_ini_or_detect_again(
    qt_app, tmp_path, monkeypatch
):
    import picasapy.app.face_ignore_ini as ini_module
    import picasapy.app.face_scan_controller_scan_mixin as scan_module

    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "a.jpg", size=(100, 100))
    make_jpeg(root / "b.jpg", size=(100, 100))
    detector = _FakeDetector()
    ctl = _make_controller(qt_app, tmp_path, root, detector=detector)
    ctl.setSuggestionsEnabled(False)

    _run(ctl.scanFinished, ctl.scanNewFaces)
    assert ctl.waitForBackgroundWorkers(5.0)
    assert len(detector.calls) == 2

    ini_calls = []
    original_load_existing = ini_module.load_existing

    def counted_load_existing(*args, **kwargs):
        ini_calls.append(args[0])
        return original_load_existing(*args, **kwargs)

    monkeypatch.setattr(ini_module, "load_existing", counted_load_existing)
    statements = []
    original_open_index = scan_module.open_index

    @contextmanager
    def traced_open_index(path):
        with original_open_index(path) as conn:
            conn.set_trace_callback(statements.append)
            yield conn

    monkeypatch.setattr(scan_module, "open_index", traced_open_index)
    _run(ctl.scanFinished, ctl.scanNewFaces)
    assert ctl.waitForBackgroundWorkers(5.0)

    assert len(detector.calls) == 2
    assert ini_calls == []
    assert len(
        [statement for statement in statements if "FROM FACE_SCAN" in statement.upper()]
    ) == 1


def test_3670_reconciles_only_folders_whose_ini_changed(qt_app, tmp_path, monkeypatch):
    import picasapy.app.face_scan_controller_scan_mixin as scan_module

    root = tmp_path / "kepek"
    first = root / "album-a"
    second = root / "album-b"
    first.mkdir(parents=True)
    second.mkdir()
    for folder in (first, second):
        make_jpeg(folder / "a.jpg", size=(100, 100))
    ctl = _make_controller(qt_app, tmp_path, root)
    ctl.setSuggestionsEnabled(False)
    _run(ctl.scanFinished, ctl.scanNewFaces)
    assert ctl.waitForBackgroundWorkers(5.0)

    reconciled = []
    monkeypatch.setattr(
        scan_module,
        "_mark_previously_ignored",
        lambda _conn, photo_id, _faces: reconciled.append(photo_id),
    )
    _run(ctl.scanFinished, ctl.scanNewFaces)
    assert ctl.waitForBackgroundWorkers(5.0)
    assert reconciled == []

    from test_face_scan_controller import _FFFF, _FAKE_RECT_SHIFTED, _write_ini_faces

    _write_ini_faces(first, "a.jpg", [(_FAKE_RECT_SHIFTED, _FFFF)])
    _run(ctl.scanFinished, ctl.scanNewFaces)
    assert ctl.waitForBackgroundWorkers(5.0)

    with open_index(tmp_path / "index.db") as conn:
        photos = {photo.folder_path: photo.id for photo in all_photos(conn)}
    assert reconciled == [photos[str(first)]]


def test_automatic_scan_waits_during_user_activity(qt_app, tmp_path):
    import threading

    root = tmp_path / "kepek"
    root.mkdir()
    for number in range(21):
        make_jpeg(root / f"{number:02}.jpg", size=(100, 100))
    detector = _FakeDetector()
    ctl = _make_controller(qt_app, tmp_path, root, detector=detector)
    ctl.setSuggestionsEnabled(False)
    activity = threading.Event()
    waiting = threading.Event()

    def should_pause():
        if activity.is_set():
            waiting.set()
        return activity.is_set()

    ctl._scan_should_pause = should_pause
    activity.set()
    ctl.scanNewFaces()
    assert waiting.wait(2.0)
    assert detector.calls == []

    activity.clear()
    assert ctl.waitForBackgroundWorkers(5.0)
    assert len(detector.calls) == 21


def test_automatic_scan_waits_for_a_duration_proportional_to_detection(
    qt_app, tmp_path
):
    root = tmp_path / "kepek"
    root.mkdir()
    for name in ("a.jpg", "b.jpg"):
        make_jpeg(root / name, size=(100, 100))
    ctl = _make_controller(qt_app, tmp_path, root)
    ctl.setSuggestionsEnabled(False)
    starts = []

    def slow_detect(_path, **_kwargs):
        starts.append(time.perf_counter())
        time.sleep(0.025)
        return ()

    ctl._detect = slow_detect
    _run(ctl.scanFinished, ctl.scanNewFaces)
    assert ctl.waitForBackgroundWorkers(5.0)

    assert len(starts) == 2
    assert starts[1] - starts[0] >= 0.04


def test_scan_commits_database_changes_in_batches(qt_app, tmp_path, monkeypatch):
    import picasapy.app.face_scan_controller_scan_mixin as scan_module

    root = tmp_path / "kepek"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(100, 100))
    ctl = _make_controller(qt_app, tmp_path, root)
    commits = []
    original_open_index = scan_module.open_index

    @contextmanager
    def traced_open_index(path):
        with original_open_index(path) as conn:
            conn.set_trace_callback(
                lambda statement: commits.append(statement)
                if statement.strip().upper() == "COMMIT"
                else None
            )
            yield conn

    monkeypatch.setattr(scan_module, "open_index", traced_open_index)
    _run(ctl.scanFinished, ctl.scanForFaces)
    assert ctl.waitForBackgroundWorkers(5.0)

    assert len(commits) <= 2


def test_thumbnail_cache_reuses_a_recent_960px_face_decode(tmp_path, monkeypatch):
    from picasapy import cvimage
    from picasapy.thumbs import cache as cache_module
    from picasapy.thumbs import ThumbnailCache

    source = tmp_path / "photo.jpg"
    make_jpeg(source, size=(640, 480))
    stat = source.stat()
    decoded = np.zeros((480, 640, 3), dtype=np.uint8)
    remember = getattr(cvimage, "_remember_decoded_image", None)
    find_cached = getattr(cvimage, "_find_decoded_image", None)
    assert callable(remember) and callable(find_cached)
    remember(source, stat.st_mtime_ns, stat.st_size, 960, decoded)
    cache = ThumbnailCache(tmp_path / "thumbs", size=64)

    def unexpected_source_read(_source):
        raise AssertionError("a bélyegkép újra dekódolta a fotót")

    monkeypatch.setattr(cache_module, "read_image_bytes", unexpected_source_read)
    reused = cache._decode_source(
        source, 64, mtime_ns=stat.st_mtime_ns, size_bytes=stat.st_size
    )

    assert reused is decoded


def test_activity_monitor_pauses_for_viewer_or_recent_input(qt_app):
    from PySide6.QtCore import QEvent

    from picasapy.app.face_scan_activity import FaceScanActivityMonitor

    class _Window:
        viewer_open = False

        def property(self, name):
            return self.viewer_open if name == "viewerOpen" else None

    class _Engine:
        def __init__(self, window):
            self.window = window

        def rootObjects(self):
            return [self.window]

    now = [100.0]
    window = _Window()
    monitor = FaceScanActivityMonitor(qt_app, _Engine(window), clock=lambda: now[0])
    try:
        assert not monitor.should_pause()
        window.viewer_open = True
        monitor._refresh_viewer_open()
        assert monitor.should_pause()

        window.viewer_open = False
        monitor._refresh_viewer_open()
        monitor.eventFilter(None, QEvent(QEvent.Type.KeyPress))
        assert monitor.should_pause()
        now[0] += 31.0
        assert not monitor.should_pause()
    finally:
        monitor.stop()
