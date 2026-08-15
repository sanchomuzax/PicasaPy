"""#673: sérült videó a mappában nem omlaszthatja össze a programot.

A `ThumbnailProvider` négy pool-szálról hívhatja a `_decode_video_frame`-et.
Ha a sérült fájlt az elsőként próbált FFMPEG-háttér nem tudja megnyitni, az
OpenCV a GStreamer-háttérre esne vissza — az pedig több szálból egyszerre
hívva SIGSEGV-vel viszi el az egész processzt (mérve: 15 futásból 12).

A próba ezért ALPROCESSZBEN fut: az összeomlás így exit-kódként látszik, és
nem öli meg a pytest-futást (a #103-as tanulság mintája).
"""

import os
import subprocess
import sys
from pathlib import Path

_PROBE_TIMEOUT_S = 120


def _run_probe(tmp_path: Path, threads: int, rounds: int):
    probe = Path(__file__).parent / "video_decode_probe.py"
    repo_root = Path(__file__).resolve().parents[2]
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(repo_root / "src"), str(repo_root / "tests")]
    )
    return subprocess.run(
        [sys.executable, str(probe), str(tmp_path), str(threads), str(rounds)],
        capture_output=True,
        text=True,
        timeout=_PROBE_TIMEOUT_S,
        env=env,
    )


class TestParallelBrokenVideoDecode:
    def test_no_crash_on_parallel_broken_video(self, tmp_path):
        """A javítás nélkül a próba szegmentálási hibával (exit -11) hal meg."""
        result = _run_probe(tmp_path, threads=4, rounds=12)
        assert result.returncode == 0, (
            f"a párhuzamos dekódolás összeomlott: exit={result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr[-4000:]}"
        )
        assert "OK" in result.stdout


class TestForcedFfmpegBackend:
    """Az összeomlás-próba természeténél fogva valószínűségi (a javítás
    nélkül 15-ből 12 futásban omlott össze). Ezek a tesztek DETERMINISZTIKUSAN
    rögzítik a javítás lényegét: a háttér kényszerítését — enélkül egy
    későbbi átalakítás némán visszahozhatná a visszaesést."""

    def test_ffmpeg_backend_is_forced(self, tmp_path, monkeypatch):
        import cv2

        import picasapy.thumbs.cache as cache_module

        calls = []
        original = cv2.VideoCapture

        def spy(path, *args):
            calls.append((path, args))
            return original(path, *args)

        monkeypatch.setattr(cache_module, "_FFMPEG_AVAILABLE", True)
        monkeypatch.setattr(cache_module.cv2, "VideoCapture", spy)
        broken = tmp_path / "serult.mp4"
        broken.write_bytes(b"\x00" * 64)
        cache_module._decode_video_frame(broken)

        assert calls, "nem történt VideoCapture-hívás"
        assert calls[0][1] == (cv2.CAP_FFMPEG,), (
            "a megnyitás nem kényszerítette az FFMPEG hátteret — a sérült "
            f"videó visszaeshet a GStreamerre (#673): {calls[0]!r}"
        )

    def test_falls_back_to_serialized_open_without_ffmpeg(
        self, tmp_path, monkeypatch
    ):
        """FFMPEG nélkül épült OpenCV-n nincs mire kényszeríteni: marad az
        automatikus választás, de a sorosító zár alatt."""
        import cv2

        import picasapy.thumbs.cache as cache_module

        calls = []
        held = []
        original = cv2.VideoCapture

        def spy(path, *args):
            calls.append((path, args))
            held.append(cache_module._VIDEO_FALLBACK_LOCK.locked())
            return original(path, *args)

        monkeypatch.setattr(cache_module, "_FFMPEG_AVAILABLE", False)
        monkeypatch.setattr(cache_module.cv2, "VideoCapture", spy)
        broken = tmp_path / "serult.mp4"
        broken.write_bytes(b"\x00" * 64)
        cache_module._decode_video_frame(broken)

        assert calls and calls[0][1] == (), "háttér-megjelölés nélkül kell nyitni"
        assert held == [True], "a tartalék út nem a sorosító zár alatt nyitott"


class TestBrokenVideoIsReported:
    def test_decode_failure_is_logged(self, tmp_path, caplog):
        """A sérült videó ne NÉMÁN maradjon bélyegkép nélkül: a dekódoló
        réteg beszédes figyelmeztetést ír, megnevezve a fájlt."""
        import logging

        from picasapy.thumbs.cache import _decode_video_frame

        broken = tmp_path / "serult.mp4"
        broken.write_bytes(b"\x00" * 64)
        with caplog.at_level(logging.WARNING, logger="picasapy.thumbs.cache"):
            assert _decode_video_frame(broken) is None
        assert any(
            "serult.mp4" in record.getMessage() for record in caplog.records
        ), f"nincs beszédes napló-bejegyzés: {[r.getMessage() for r in caplog.records]}"
