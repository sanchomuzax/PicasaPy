"""#6698: az MP4/MOV indexelése ne indítsa el az OpenCV-t."""

from __future__ import annotations

import json
import os
import subprocess
import struct
import sys
from pathlib import Path

import pytest


def _box(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I4s", len(payload) + 8, kind) + payload


def _minimal_mp4() -> bytes:
    mvhd = _box(
        b"mvhd",
        b"\x00" * 4 + struct.pack(">IIII", 0, 0, 1000, 7000) + b"\x00" * 80,
    )
    mdhd = _box(
        b"mdhd",
        b"\x00" * 4 + struct.pack(">IIII", 0, 0, 90000, 540000) + b"\x00" * 4,
    )
    hdlr = _box(
        b"hdlr",
        b"\x00" * 4 + struct.pack(">I", 0) + b"vide" + b"\x00" * 12,
    )
    stts = _box(
        b"stts",
        b"\x00" * 4 + struct.pack(">III", 1, 180, 3000),
    )
    stbl = _box(b"stbl", stts)
    minf = _box(b"minf", stbl)
    mdia = _box(b"mdia", hdlr + mdhd + minf)
    trak = _box(b"trak", mdia)
    moov = _box(b"moov", mvhd + trak)
    ftyp = _box(b"ftyp", b"isom" + struct.pack(">I", 0) + b"isom")
    return ftyp + moov


@pytest.mark.parametrize("suffix", ("mp4", "mov"))
def test_mp4_es_mov_atomokbol_olvassa_a_hosszt_es_fps_t(
    suffix, tmp_path
):
    path = tmp_path / f"video.{suffix}"
    path.write_bytes(_minimal_mp4())
    script = (
        "import json, sys\n"
        "from picasapy.metadata.video import read_video_metadata\n"
        "metadata = read_video_metadata(sys.argv[1])\n"
        "assert metadata.movie_format == sys.argv[2].upper()\n"
        "assert metadata.frame_rate == 30.0\n"
        "assert metadata.duration_seconds == 6.0\n"
        "assert 'cv2' not in sys.modules\n"
        "print(json.dumps({'format': metadata.movie_format}))\n"
    )
    repo_root = Path(__file__).resolve().parents[2]
    env = os.environ.copy()
    source_path = str(repo_root / "src")
    env["PYTHONPATH"] = os.pathsep.join(
        part for part in (source_path, env.get("PYTHONPATH", "")) if part
    )
    completed = subprocess.run(
        [sys.executable, "-c", script, str(path), suffix],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {"format": suffix.upper()}
