"""Az arc-kereső háttérszálai alacsony prioritással és egy OpenCV-szállal futnak."""

from __future__ import annotations

import importlib
import threading

import numpy as np

from support.jpeg_factory import make_jpeg
from support.qt_wait import hangos_hurok


def _prio_process() -> int:
    from picasapy.app import hatter_prioritas

    return hatter_prioritas._PRIO_PROCESS


class _Detector:
    available = True


class _Embedder:
    available = True

    def __init__(self, observations=None):
        self.observations = observations if observations is not None else []

    def compute(self, _image, _detection):
        from picasapy.lazy_cv2 import cv2

        self.observations.append((cv2.getNumThreads(), threading.get_native_id()))
        return None


def _make_controller(tmp_path, *, face=False, embedding_observations=None):
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.faces.detector import FaceDetection, FaceLandmarks
    from picasapy.index import all_photos, open_index, replace_faces, sync_tree

    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "a.jpg", size=(128, 96))
    index_path = tmp_path / "index.db"
    with open_index(index_path) as conn:
        sync_tree(conn, root)
        if face:
            photo = all_photos(conn)[0]
            replace_faces(
                conn,
                photo.id,
                (
                    FaceDetection(
                        left=10,
                        top=10,
                        right=60,
                        bottom=60,
                        score=0.9,
                        landmarks=FaceLandmarks(
                            right_eye=(20, 25),
                            left_eye=(40, 25),
                            nose=(30, 35),
                            mouth_right=(23, 45),
                            mouth_left=(37, 45),
                        ),
                    ),
                ),
            )
        conn.commit()

    return FaceScanController(
        index_path,
        detector=_Detector(),
        embedder=_Embedder(embedding_observations),
    )


def _run(signal, action):
    loop = hangos_hurok(signal, timeout_ms=10000)
    action()
    loop.exec()
    return loop.jelzes_megjott, loop.jelzes_argumentumai


def _set_linux_priority_failure(monkeypatch, calls):
    from picasapy.app import hatter_prioritas

    monkeypatch.setattr(hatter_prioritas, "_platform", lambda: "linux")

    def fail(which, native_id, priority):
        calls.append((which, native_id, priority))
        raise OSError("a rendszer nem engedte a prioritás módosítását")

    monkeypatch.setattr(hatter_prioritas, "_linux_setpriority", fail)


def _record_cv2_thread_setting(monkeypatch):
    cv2_module = importlib.import_module("cv2")
    previous = cv2_module.getNumThreads()
    calls = []
    original_set_num_threads = cv2_module.setNumThreads

    def record_and_set(count):
        calls.append((count, threading.get_native_id()))
        original_set_num_threads(count)

    monkeypatch.setattr(cv2_module, "setNumThreads", record_and_set)
    return cv2_module, previous, calls


def test_linux_priority_uses_native_thread_id_and_nice_10(monkeypatch):
    from picasapy.app import hatter_prioritas

    calls = []
    monkeypatch.setattr(hatter_prioritas, "_platform", lambda: "linux")
    monkeypatch.setattr(
        hatter_prioritas, "_native_thread_id", lambda: 731
    )
    monkeypatch.setattr(
        hatter_prioritas, "_linux_setpriority", lambda *args: calls.append(args)
    )

    hatter_prioritas.kerjafonal_alacsony_prioritasa()

    assert calls == [(_prio_process(), 731, 10)]


def test_windows_priority_sets_current_thread_below_normal(monkeypatch):
    from picasapy.app import hatter_prioritas

    class _SetThreadPriority:
        def __init__(self):
            self.restype = None
            self.argtypes = None

        def __call__(self, *args):
            calls.append(args)
            return 1

    class _GetCurrentThread:
        restype = None

        def __call__(self):
            return 1234

    calls = []

    class _Kernel32:
        GetCurrentThread = _GetCurrentThread()
        SetThreadPriority = _SetThreadPriority()

    monkeypatch.setattr(hatter_prioritas, "_platform", lambda: "win32")
    monkeypatch.setattr(
        hatter_prioritas, "_windows_kernel32", lambda: _Kernel32
    )

    hatter_prioritas.kerjafonal_alacsony_prioritasa()

    assert calls == [(1234, -1)]


def test_scan_continues_after_priority_error_and_uses_one_opencv_thread(
    qt_app, tmp_path, monkeypatch
):
    from picasapy.lazy_cv2 import cv2

    priority_calls = []
    _set_linux_priority_failure(monkeypatch, priority_calls)
    cv2_module, previous, cv2_calls = _record_cv2_thread_setting(monkeypatch)
    observed = []
    ctl = _make_controller(tmp_path)
    ctl.setSuggestionsEnabled(False)

    def detect(_path, **_kwargs):
        observed.append((cv2.getNumThreads(), threading.get_native_id()))
        return ()

    monkeypatch.setattr(ctl, "_detect", detect)
    try:
        arrived, _args = _run(ctl.scanFinished, ctl.scanForFaces)
        assert arrived is True
        assert ctl.waitForBackgroundWorkers(5.0)
        assert len(priority_calls) == 1
        assert priority_calls[0][0] == _prio_process()
        assert priority_calls[0][2] == 10
        assert cv2_calls == [(1, priority_calls[0][1]), (previous, priority_calls[0][1])]
        assert observed == [(1, priority_calls[0][1])]
    finally:
        cv2_module.setNumThreads(previous)


def test_embedding_continues_after_priority_error_and_uses_one_opencv_thread(
    qt_app, tmp_path, monkeypatch
):
    priority_calls = []
    _set_linux_priority_failure(monkeypatch, priority_calls)
    cv2_module, previous, cv2_calls = _record_cv2_thread_setting(monkeypatch)
    observed = []
    ctl = _make_controller(tmp_path, face=True, embedding_observations=observed)
    monkeypatch.setattr(
        ctl,
        "_decode",
        lambda _path: np.zeros((96, 128, 3), dtype=np.uint8),
    )
    try:
        arrived, _args = _run(ctl.embeddingFinished, ctl.computeEmbeddings)
        assert arrived is True
        assert ctl.waitForBackgroundWorkers(5.0)
        assert len(priority_calls) == 1
        assert priority_calls[0][0] == _prio_process()
        assert priority_calls[0][2] == 10
        assert cv2_calls == [(1, priority_calls[0][1]), (previous, priority_calls[0][1])]
        assert observed == [(1, priority_calls[0][1])]
    finally:
        cv2_module.setNumThreads(previous)


def test_a_kereses_utan_az_opencv_szalszam_visszaall(monkeypatch):
    """A szálszám az egész folyamatra érvényes: a keresés végén vissza kell
    állnia, különben a szerkesztő effektjei is egy szálon maradnának."""
    from picasapy.app import hatter_prioritas
    from picasapy.lazy_cv2 import cv2

    monkeypatch.setattr(hatter_prioritas, "kerjafonal_alacsony_prioritasa", lambda: None)
    eredeti = cv2.getNumThreads()
    try:
        cv2.setNumThreads(3)
        elozo = hatter_prioritas.arckeres_szal_elokeszitese()
        assert elozo == 3
        assert cv2.getNumThreads() == 1
        hatter_prioritas.arckeres_szal_lezarasa(elozo)
        assert cv2.getNumThreads() == 3
    finally:
        cv2.setNumThreads(eredeti)
