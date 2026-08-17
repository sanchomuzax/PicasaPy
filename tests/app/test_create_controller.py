"""A Létrehozás-szelet (kollázs, mozgófilm — #29) vezérlő-tesztjei.

A háttérszálas munkát a jelzésekre váró QEventLoop-minta követi (a
test_controller.py `_quit_on` mintája szerint).
"""

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QEventLoop, QSettings, QTimer

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg", size=(120, 80))
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg", size=(80, 120))
    make_jpeg(root / "nyaralas" / "IMG_0003.jpg", size=(100, 100))
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db", (str(library),), provider, settings=settings
    )
    ctl.selectFolder(str(library / "nyaralas"))
    yield ctl
    # #438: a kollázs/mozgófilm háttérszála bevárva, MÍG a controller még
    # él — a #430 SIGSEGV-osztály elkerülése (BackgroundWorkerMixin).
    assert ctl.waitForBackgroundWorkers(30.0), "a create-worker szál nem állt le"


def _run(signal, action, timeout_ms=10000):
    """A műveletet a jelzésre FELIRATKOZVA indítja, majd bevárja azt.

    A sorrend lényeges: a hibautak (üres kijelölés, hiányzó célfájl) még a
    hívó szálon, azonnal jeleznek — utólagos feliratkozás lemaradna róluk.
    Visszatérés: (megjött-e, argumentumok)."""
    loop = QEventLoop()
    received = {}

    def _on(*args):
        received["args"] = args
        loop.quit()

    signal.connect(_on)
    action()
    if "args" not in received:
        QTimer.singleShot(timeout_ms, loop.quit)
        loop.exec()
    return ("args" in received, received.get("args", ()))


def _skip_without_codec(target):
    writer = cv2.VideoWriter(
        str(target), cv2.VideoWriter_fourcc(*"mp4v"), 24.0, (64, 64)
    )
    opened = writer.isOpened()
    writer.release()
    if not opened:
        pytest.skip("Nincs elérhető MP4-kodek ezen a rendszeren.")


class TestMakeCollage:
    def test_creates_file_from_selection(self, controller, tmp_path):
        target = tmp_path / "kollazs.jpg"
        arrived, args = _run(
            controller.collageFinished,
            lambda: controller.makeCollage([0, 1, 2], "regulargrid", str(target)),
        )
        assert arrived, "nem érkezett collageFinished"
        path, used, skipped, missing = args
        assert target.exists()
        assert used == 3 and skipped == 0 and missing == 0
        decoded = cv2.imdecode(
            np.frombuffer(target.read_bytes(), np.uint8), cv2.IMREAD_COLOR
        )
        assert decoded is not None and decoded.shape[2] == 3

    def test_file_url_target_is_accepted(self, controller, tmp_path):
        target = tmp_path / "url-kollazs.jpg"
        arrived, _ = _run(
            controller.collageFinished,
            lambda: controller.makeCollage([0, 1], "picturegrid", target.as_uri()),
        )
        assert arrived and target.exists()

    def test_empty_selection_fails_with_message(self, controller, tmp_path):
        arrived, args = _run(
            controller.collageFailed,
            lambda: controller.makeCollage([], "regulargrid", str(tmp_path / "x.jpg")), 2000,
        )
        assert arrived and args[0]

    def test_missing_target_fails(self, controller):
        arrived, args = _run(
            controller.collageFailed,
            lambda: controller.makeCollage([0], "regulargrid", ""), 2000,
        )
        assert arrived and args[0]

    def test_unknown_kind_fails(self, controller, tmp_path):
        arrived, args = _run(
            controller.collageFailed,
            lambda: controller.makeCollage([0], "mandala", str(tmp_path / "x.jpg")), 2000,
        )
        assert arrived and args[0]

    def test_out_of_range_rows_are_ignored(self, controller, tmp_path):
        target = tmp_path / "k.jpg"
        arrived, args = _run(
            controller.collageFinished,
            lambda: controller.makeCollage([0, 99], "regulargrid", str(target)),
        )
        assert arrived and args[1] == 1


class TestExportMovie:
    def test_creates_video_from_selection(self, controller, tmp_path):
        _skip_without_codec(tmp_path / "proba.mp4")
        target = tmp_path / "film.mp4"
        arrived, args = _run(
            controller.movieFinished,
            lambda: controller.exportMovie([0, 1, 2], str(target), 720, 0.5), 20000,
        )
        assert arrived, "nem érkezett movieFinished"
        path, used, skipped, missing = args
        assert target.exists() and target.stat().st_size > 0
        assert used == 3 and skipped == 0 and missing == 0

    def test_progress_is_emitted(self, controller, tmp_path):
        _skip_without_codec(tmp_path / "proba.mp4")
        seen = []
        controller.movieProgress.connect(lambda done, total: seen.append(done))
        arrived, _ = _run(
            controller.movieFinished,
            lambda: controller.exportMovie(
                [0, 1], str(tmp_path / "film.mp4"), 720, 0.4
            ),
            20000,
        )
        assert arrived
        assert seen == [1, 2]

    def test_empty_selection_fails(self, controller, tmp_path):
        arrived, args = _run(
            controller.movieFailed,
            lambda: controller.exportMovie(
                [], str(tmp_path / "film.mp4"), 720, 1.0
            ),
            2000,
        )
        assert arrived and args[0]

    def test_invalid_settings_fail_with_message(self, controller, tmp_path):
        arrived, args = _run(
            controller.movieFailed,
            lambda: controller.exportMovie([0], str(tmp_path / "film.mp4"), 720, 0.0), 2000,
        )
        assert arrived and args[0]

    def test_missing_target_fails(self, controller):
        arrived, args = _run(
            controller.movieFailed,
            lambda: controller.exportMovie([0], "", 720, 1.0), 2000,
        )
        assert arrived and args[0]


class TestBackgroundThreadTeardown:
    """#438 (a #430 SIGSEGV-osztály maradéka): a kollázs/mozgófilm
    háttérszála bevárható legyen, mielőtt a controller megsemmisül."""

    def test_wait_without_a_run_returns_immediately(self, controller):
        assert controller.waitForBackgroundWorkers(0.0)

    def test_wait_joins_the_collage_worker_thread(self, controller, tmp_path):
        arrived, _args = _run(
            controller.collageFinished,
            lambda: controller.makeCollage(
                [0, 1], "regulargrid", (tmp_path / "kollazs.jpg").as_uri()
            ),
            20000,
        )
        assert arrived
        assert controller.waitForBackgroundWorkers(30.0)
        assert not controller.backgroundWorkersRunning()
