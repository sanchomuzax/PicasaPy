"""#6753: leállításkor álljon meg az arckeresés és induljon a maradékkal."""

from __future__ import annotations

import threading
import time
from pathlib import Path
from types import SimpleNamespace

from support.jpeg_factory import make_jpeg
from test_face_scan_controller import _FakeDetector, _make_controller, _run


class _SlowDetector(_FakeDetector):
    def __init__(self, delay: float = 0.1):
        super().__init__()
        self.delay = delay
        self.entered = threading.Event()
        self.release = threading.Event()
        self._first = True

    def detect(self, image):
        if self._first:
            self._first = False
            self.entered.set()
            self.release.wait(timeout=10.0)
        else:
            time.sleep(self.delay)
        return super().detect(image)


def _shutdown_application(monkeypatch, controller, detector):
    import picasapy.app.application_startup_qml as startup

    monkeypatch.setattr(startup, "_destroy_qml_engine", lambda *_args: None)
    release_image = threading.Timer(0.1, detector.release.set)
    release_image.start()
    state = SimpleNamespace(
        effect_slice_controller=None,
        face_scan_controller=controller,
        engine=object(),
        app=object(),
    )
    started = time.monotonic()
    startup._shutdown_application_qml(state)
    release_image.join()
    return time.monotonic() - started


def _library(tmp_path, count: int):
    root = tmp_path / "kepek"
    root.mkdir()
    for index in range(count):
        make_jpeg(root / f"{index:03}.jpg", size=(100, 100))
    return root


def test_qt_exit_signal_is_connected_to_face_scan_cancellation():
    from picasapy.app import application_startup_qml

    source = Path(application_startup_qml.__file__).read_text(encoding="utf-8")
    assert "app.aboutToQuit.connect(face_scan_controller.cancelScan)" in source


def test_application_shutdown_stops_face_scan_worker_within_timeout(
    qt_app, tmp_path, monkeypatch
):
    root = _library(tmp_path, 16)
    detector = _SlowDetector(delay=0.2)
    controller = _make_controller(qt_app, tmp_path, root, detector=detector)
    controller.setSuggestionsEnabled(False)

    controller.scanForFaces()
    if not detector.entered.wait(10.0):
        controller.cancelScan()
        assert controller.waitForBackgroundWorkers(5.0)
        raise AssertionError("a lassú detektor nem indult el")

    elapsed = _shutdown_application(monkeypatch, controller, detector)
    try:
        assert elapsed < 2.5
        assert controller.waitForBackgroundWorkers(0.2)
        assert len(detector.calls) == 1
    finally:
        controller.cancelScan()
        assert controller.waitForBackgroundWorkers(5.0)


def test_shutdown_resume_scans_only_remaining_photos_and_then_zero(
    qt_app, tmp_path, monkeypatch
):
    root = _library(tmp_path, 4)
    first_detector = _SlowDetector(delay=0.1)
    first_controller = _make_controller(
        qt_app, tmp_path, root, detector=first_detector
    )
    first_controller.setSuggestionsEnabled(False)

    first_controller.scanForFaces()
    deadline = time.monotonic() + 2.0
    assert first_detector.entered.wait(max(0.0, deadline - time.monotonic()))

    _shutdown_application(monkeypatch, first_controller, first_detector)
    assert first_controller.waitForBackgroundWorkers(0.2)
    assert len(first_detector.calls) == 1

    resumed_detector = _FakeDetector()
    resumed_controller = _make_controller(
        qt_app, tmp_path, root, detector=resumed_detector
    )
    resumed_controller.setSuggestionsEnabled(False)
    arrived, _args = _run(resumed_controller.scanFinished, resumed_controller.scanForFaces)
    assert arrived
    assert resumed_controller.waitForBackgroundWorkers(5.0)
    assert len(resumed_detector.calls) == 3

    arrived, args = _run(resumed_controller.scanFinished, resumed_controller.scanForFaces)
    assert arrived
    assert args == (0, 0)
    assert len(resumed_detector.calls) == 3
