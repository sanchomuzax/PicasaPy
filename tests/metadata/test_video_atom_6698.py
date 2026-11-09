"""#6698: az MP4/MOV indexelése ne indítsa el az OpenCV-t."""

from __future__ import annotations

import builtins
import struct

import pytest

from picasapy.metadata.video import read_video_metadata


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
    suffix, tmp_path, monkeypatch
):
    path = tmp_path / f"video.{suffix}"
    path.write_bytes(_minimal_mp4())
    imported_cv2 = []
    original_import = builtins.__import__

    def track_cv2_import(name, *args, **kwargs):
        if name == "cv2":
            imported_cv2.append(name)
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", track_cv2_import)

    metadata = read_video_metadata(path)

    assert metadata.movie_format == suffix.upper()
    assert metadata.frame_rate == 30.0
    assert metadata.duration_seconds == 6.0
    assert imported_cv2 == []
