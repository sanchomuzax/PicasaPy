"""#4564: a videó exportja csak a megadott vágási szakaszt tartalmazza."""

from __future__ import annotations

from concurrent.futures import CancelledError
from pathlib import Path
import subprocess
import threading

import cv2
import pytest

from tests.support.video_factory import make_mp4


def _duration_seconds(path):
    capture = cv2.VideoCapture(str(path))
    try:
        assert capture.isOpened(), f"A kimeneti videó nem nyitható meg: {path}"
        fps = capture.get(cv2.CAP_PROP_FPS)
        frames = capture.get(cv2.CAP_PROP_FRAME_COUNT)
        assert fps > 0
        return frames / fps
    finally:
        capture.release()


def test_a_kimeneti_fajl_csak_a_vagott_szakaszt_tartalmazza(tmp_path):
    from picasapy.movie.clip_export import export_clip

    source = make_mp4(tmp_path / "eredeti.mp4", frames=30, fps=10)
    output_dir = tmp_path / "Exportált videoklipek"

    output = export_clip(source, output_dir, start_ms=500, end_ms=1500)

    assert output.is_file()
    assert output.parent == output_dir
    assert output.suffix == ".mp4"
    assert _duration_seconds(output) == pytest.approx(1.0, abs=0.15)


def test_ismetelt_export_nem_irja_felul_a_meglevo_klipet(tmp_path):
    from picasapy.movie.clip_export import export_clip

    source = make_mp4(tmp_path / "eredeti.mp4", frames=30, fps=10)
    output_dir = tmp_path / "Exportált videoklipek"

    elso = export_clip(source, output_dir, start_ms=500, end_ms=1500)
    masodik = export_clip(source, output_dir, start_ms=500, end_ms=1500)

    assert elso.is_file()
    assert masodik.is_file()
    assert masodik != elso
    assert _duration_seconds(masodik) == pytest.approx(1.0, abs=0.15)


def test_megszakitas_leallitja_az_ffmpeg_et_es_torol_minden_felkesz_fajlt(
    monkeypatch, tmp_path
):
    from picasapy.movie import clip_export, slideshow

    source = tmp_path / "forras.mp4"
    source.write_bytes(b"video")
    output_dir = tmp_path / "Exportált videoklipek"
    cancel_event = threading.Event()
    folyamatok = []

    class BeragadtFolyamat:
        def __init__(self, command, **_kwargs):
            folyamatok.append(self)
            self.command = command
            self.terminated = False
            self.killed = False
            self.returncode = None
            Path(command[-1]).write_bytes("részleges kódolás".encode("utf-8"))
            cancel_event.set()

        def poll(self):
            return self.returncode

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            if not self.killed:
                raise subprocess.TimeoutExpired("fake-ffmpeg", timeout)
            self.returncode = -9
            return self.returncode

        def kill(self):
            self.killed = True

        def communicate(self, timeout=None):
            if self.killed:
                self.returncode = -9
                return "", "terminated"
            raise subprocess.TimeoutExpired("fake-ffmpeg", timeout)

    monkeypatch.setattr(slideshow, "_ffmpeg_exe", lambda: "fake-ffmpeg")
    monkeypatch.setattr(clip_export.subprocess, "Popen", BeragadtFolyamat)
    monkeypatch.setattr(
        clip_export.subprocess,
        "run",
        lambda *_args, **_kwargs: pytest.fail("export_clip még subprocess.run-t hív"),
    )

    with pytest.raises(CancelledError):
        clip_export.export_clip(
            source,
            output_dir,
            start_ms=100,
            end_ms=800,
            cancel_event=cancel_event,
        )

    assert len(folyamatok) == 1
    assert folyamatok[0].command[0] == "fake-ffmpeg"
    assert folyamatok[0].terminated
    assert folyamatok[0].killed
    assert list(output_dir.iterdir()) == []
