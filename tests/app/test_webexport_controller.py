"""WebExportController (#351) — a `picasapy.webexport` motor QML-hídja.

A `test_relocate_controller.py` mintáját követi: valódi ideiglenes
könyvtárral, mock nélkül, valódi eseményhurok-várakozással a
háttérszálas eredményre."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEventLoop, QTimer

from picasapy.app.webexport_controller import WebExportController
from picasapy.index import PhotoRecord
from support.jpeg_factory import make_jpeg


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


def _record(folder, name, **overrides):
    path = folder / name
    if not path.exists():
        make_jpeg(path, size=(80, 60))
    defaults = dict(
        id=1, folder_path=str(folder), name=name, kind="photo",
        size=path.stat().st_size, mtime_ns=0, star=False, caption=None,
        keywords=None, rotate_steps=0, filters=None, taken_at=None,
        orientation=1, width=80, height=60,
    )
    defaults.update(overrides)
    return PhotoRecord(**defaults)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    return root


@pytest.fixture
def controller(qt_app, library):
    photos = [_record(library, "a.jpg", caption="Kutya"), _record(library, "b.jpg")]
    return WebExportController(photo_source=lambda: photos)


class TestListWebExportTemplates:
    def test_includes_bundled_feher_template(self, controller):
        templates = controller.listWebExportTemplates()
        ids = [t["id"] for t in templates]
        assert "feher" in ids
        assert all({"id", "name", "description"} <= set(t) for t in templates)


class TestGenerateWebExportValidation:
    def test_missing_target_emits_failure_synchronously(self, controller):
        seen = []
        controller.webExportFailed.connect(seen.append)
        controller.generateWebExport("", "feher", "Album", 0, 0, True, False)
        assert seen

    def test_unknown_template_emits_failure_synchronously(self, controller, tmp_path):
        seen = []
        controller.webExportFailed.connect(seen.append)
        controller.generateWebExport(
            str(tmp_path / "out"), "nemletezik", "Album", 0, 0, True, False
        )
        assert seen

    def test_empty_photo_source_emits_failure(self, qt_app, library, tmp_path):
        controller = WebExportController(photo_source=lambda: [])
        seen = []
        controller.webExportFailed.connect(seen.append)
        controller.generateWebExport(
            str(tmp_path / "out"), "feher", "Album", 0, 0, True, False
        )
        assert seen


class TestGenerateWebExportSuccess:
    def test_full_run_emits_finished_with_output_files(self, controller, tmp_path):
        target = tmp_path / "kimenet"
        finished = []
        controller.webExportFinished.connect(
            lambda out_dir, count: finished.append((out_dir, count))
        )
        loop = _quit_on(controller.webExportFinished)
        controller.generateWebExport(
            str(target), "feher", "Nyaralás", 100, 800, True, False
        )
        loop.exec()

        assert len(finished) == 1
        out_dir, page_count = finished[0]
        assert out_dir == str(target)
        # 1 index oldal + 2 kép egyenkénti oldala (index0/index1)
        assert page_count == 3
        assert (target / "index.html").is_file()
        assert "Nyaralás" in (target / "index.html").read_text(encoding="utf-8")
        assert (target / "style.css").is_file()

    def test_progress_signal_reports_processed_count(self, controller, tmp_path):
        progress = []
        controller.webExportProgress.connect(lambda done, total: progress.append((done, total)))
        loop = _quit_on(controller.webExportFinished)
        controller.generateWebExport(
            str(tmp_path / "kimenet"), "feher", "Album", 0, 0, True, False
        )
        loop.exec()
        assert progress == [(2, 2)]

    def test_video_only_selection_fails_after_image_generation(self, qt_app, library, tmp_path):
        video_path = library / "v.mp4"
        video_path.write_bytes(b"nem-igazi-video")
        record = _record(library, "v.mp4", kind="video")
        controller = WebExportController(photo_source=lambda: [record])
        failed = []
        controller.webExportFailed.connect(failed.append)
        loop = _quit_on(controller.webExportFailed)
        controller.generateWebExport(
            str(tmp_path / "kimenet"), "feher", "Album", 0, 0, True, False
        )
        loop.exec()
        assert failed
