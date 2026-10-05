"""#4273: a video decoder that hangs cannot stall the thumbnail grid."""

from __future__ import annotations

import sys
import time
from pathlib import Path

from picasapy.index import open_index, photos_in_folder, sync_tree
from support.jpeg_factory import make_jpeg


def _library_with_video(tmp_path: Path):
    library = tmp_path / "library"
    library.mkdir()
    photo = make_jpeg(library / "photo.jpg", size=(160, 80))
    video = library / "hanging.mp4"
    video.write_bytes(b"intentionally not decoded in this test")
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        records = photos_in_folder(connection, library)
    return records, photo, video


def _hanging_decoder(_source: Path, _output: Path) -> list[str]:
    return [sys.executable, "-c", "import time; time.sleep(3)"]


def test_video_decoder_is_stopped_at_its_deadline(tmp_path, monkeypatch):
    """A child that outlives the deadline is killed and yields no frame."""
    import picasapy.thumbs.cache as cache_module

    monkeypatch.setattr(cache_module, "_video_decode_worker_command", _hanging_decoder)
    started = time.monotonic()
    frame = cache_module._decode_video_frame_isolated(
        tmp_path / "hanging.mp4", timeout_s=0.15
    )

    assert frame is None
    assert time.monotonic() - started < 2.0


def test_default_video_timeout_is_finite_and_keeps_the_grid_responsive():
    import picasapy.thumbs.cache as cache_module

    assert 0 < cache_module._VIDEO_DECODE_TIMEOUT_S <= 5


def test_frozen_worker_uses_the_bundled_windows_entry_point(monkeypatch, tmp_path):
    import picasapy.thumbs.cache as cache_module

    monkeypatch.setattr(cache_module.sys, "frozen", True, raising=False)
    monkeypatch.setattr(cache_module.sys, "executable", "PicasaPy.exe")
    source = tmp_path / "clip.mp4"
    output = tmp_path / "frame.png"

    assert cache_module._video_decode_worker_command(source, output) == [
        "PicasaPy.exe",
        "--picasapy-video-decode",
        str(source),
        str(output),
    ]

    gyoker = Path(__file__).resolve().parents[2]
    launcher = (gyoker / "packaging/windows/picasapy_launcher.py").read_text(
        encoding="utf-8"
    )
    spec = (gyoker / "packaging/windows/picasapy.spec").read_text(
        encoding="utf-8"
    )
    assert "--picasapy-video-decode" in launcher
    assert '"picasapy.thumbs.video_decode_worker"' in spec


def test_timeout_reports_broken_video_and_next_grid_row_completes(
    qt_app, tmp_path, monkeypatch
):
    """A timed-out video emits the broken marker; a following photo completes."""
    from PySide6.QtCore import Qt

    import picasapy.thumbs.cache as cache_module
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    records, _photo_path, video_path = _library_with_video(tmp_path)
    video_record = next(record for record in records if record.name == video_path.name)
    photo_record = next(record for record in records if record.name == "photo.jpg")

    monkeypatch.setattr(cache_module, "_VIDEO_DECODE_TIMEOUT_S", 0.15)
    monkeypatch.setattr(cache_module, "_video_decode_worker_command", _hanging_decoder)

    provider = ThumbnailProvider(
        ThumbnailCache(tmp_path / "thumbs", size=64), max_threads=1
    )
    provider.register_photos(records)
    broken_ids = []
    provider.brokenImageDetected.connect(
        broken_ids.append, Qt.ConnectionType.DirectConnection
    )

    video_response = provider.requestImageResponse(str(video_record.id), None)
    photo_response = provider.requestImageResponse(str(photo_record.id), None)

    assert provider.wait_for_done(5000), "a thumbnail worker stayed stuck"
    assert video_response._done.wait(1)
    assert photo_response._done.wait(1)
    assert video_response._image.size().width() == 16
    assert video_response._image.size().height() == 16
    assert not photo_response._image.isNull()
    assert broken_ids == [str(video_record.id)]


# rontás-kontroll: picasapy.thumbs.cache._VIDEO_DECODE_TIMEOUT_S = 30 → 1 failed
