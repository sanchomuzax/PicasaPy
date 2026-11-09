"""A videók indexeléséhez szükséges, könnyű metaadatok kiolvasása."""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator


@dataclass(frozen=True)
class VideoMetadata:
    """Videóformátum, képkockasebesség és hossz másodpercben."""

    movie_format: str | None = None
    frame_rate: float | None = None
    duration_seconds: float | None = None


EMPTY_VIDEO_METADATA = VideoMetadata()


_Atom = tuple[bytes, int, int]


def read_video_metadata(path: str | Path) -> VideoMetadata:
    """Videófejlécből kiolvassa a panel mezőit; sérült fájlnál nem dob.

    MP4/MOV esetén az ISO Base Media atomokat olvassa, ezért az indexelés
    nem tölti be a több tíz megabájtos OpenCV/FFmpeg modult. Más
    videóformátumnál megmarad az OpenCV dekóderút.
    """
    video_path = Path(path)
    movie_format = video_path.suffix.removeprefix(".").upper() or None
    if video_path.suffix.casefold() in {".mp4", ".mov"}:
        return _read_mp4_mov(video_path, movie_format)
    return _read_with_cv2(video_path, movie_format)


def _read_with_cv2(path: Path, movie_format: str | None) -> VideoMetadata:
    """A nem MP4/MOV formátumok korábbi dekóderútja."""
    from picasapy.lazy_cv2 import cv2

    try:
        capture = cv2.VideoCapture(str(path))
    except (cv2.error, OSError, ValueError):
        return VideoMetadata(movie_format=movie_format)

    try:
        if not capture.isOpened():
            return VideoMetadata(movie_format=movie_format)
        frame_rate = float(capture.get(cv2.CAP_PROP_FPS))
        frame_count = float(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    except (cv2.error, OSError, ValueError):
        return VideoMetadata(movie_format=movie_format)
    finally:
        capture.release()

    if not math.isfinite(frame_rate) or frame_rate <= 0:
        return VideoMetadata(movie_format=movie_format)
    if not math.isfinite(frame_count) or frame_count < 0:
        return VideoMetadata(movie_format=movie_format)
    return VideoMetadata(
        movie_format=movie_format,
        frame_rate=frame_rate,
        duration_seconds=frame_count / frame_rate,
    )


def _read_mp4_mov(path: Path, movie_format: str | None) -> VideoMetadata:
    """A moov fejlécből képkockasebességet és időtartamot olvas."""
    try:
        with path.open("rb") as stream:
            stream.seek(0, 2)
            file_end = stream.tell()
            stream.seek(0)
            for kind, payload_start, atom_end in _iter_atoms(stream, 0, file_end):
                if kind != b"moov":
                    continue
                movie_duration = None
                video_rate = None
                video_duration = None
                for child_kind, child_start, child_end in _iter_atoms(
                    stream, payload_start, atom_end
                ):
                    if child_kind == b"mvhd":
                        _timescale, movie_duration = _read_time_header(
                            stream, child_start, child_end
                        )
                    elif child_kind == b"trak":
                        rate, duration = _read_video_track(
                            stream, child_start, child_end
                        )
                        if video_rate is None and rate is not None:
                            video_rate = rate
                        if video_duration is None and duration is not None:
                            video_duration = duration
                return VideoMetadata(
                    movie_format=movie_format,
                    frame_rate=video_rate,
                    duration_seconds=(
                        video_duration
                        if video_duration is not None
                        else movie_duration
                    ),
                )
    except (OSError, OverflowError, struct.error, ValueError):
        return VideoMetadata(movie_format=movie_format)
    return VideoMetadata(movie_format=movie_format)


def _read_video_track(stream: BinaryIO, start: int, end: int) -> tuple[float | None, float | None]:
    for kind, payload_start, atom_end in _iter_atoms(stream, start, end):
        if kind != b"mdia":
            continue
        handler = None
        media_timescale = None
        media_duration = None
        stts_atom: _Atom | None = None
        for child_kind, child_start, child_end in _iter_atoms(
            stream, payload_start, atom_end
        ):
            if child_kind == b"hdlr":
                handler = _read_handler(stream, child_start, child_end)
            elif child_kind == b"mdhd":
                media_timescale, media_duration = _read_time_header(
                    stream, child_start, child_end
                )
            elif child_kind == b"minf":
                for minf_kind, minf_start, minf_end in _iter_atoms(
                    stream, child_start, child_end
                ):
                    if minf_kind != b"stbl":
                        continue
                    for stbl_kind, stbl_start, stbl_end in _iter_atoms(
                        stream, minf_start, minf_end
                    ):
                        if stbl_kind == b"stts":
                            stts_atom = (stbl_kind, stbl_start, stbl_end)
        if handler != b"vide":
            continue
        rate = (
            _read_frame_rate(stream, stts_atom, media_timescale)
            if stts_atom is not None and media_timescale is not None
            else None
        )
        return rate, media_duration
    return None, None


def _iter_atoms(stream: BinaryIO, start: int, end: int) -> Iterator[_Atom]:
    """Atomokat sorol fel a szülő határain belül, az adatokat beolvasás nélkül átugorva."""
    offset = start
    while offset + 8 <= end:
        stream.seek(offset)
        header = stream.read(8)
        if len(header) != 8:
            return
        size32, kind = struct.unpack(">I4s", header)
        header_size = 8
        if size32 == 1:
            extended = stream.read(8)
            if len(extended) != 8:
                return
            size = struct.unpack(">Q", extended)[0]
            header_size = 16
        elif size32 == 0:
            size = end - offset
        else:
            size = size32
        if size < header_size or offset + size > end:
            return
        atom_end = offset + size
        yield kind, offset + header_size, atom_end
        offset = atom_end


def _read_time_header(
    stream: BinaryIO, payload_start: int, atom_end: int
) -> tuple[int | None, float | None]:
    stream.seek(payload_start)
    full_box = stream.read(4)
    if len(full_box) != 4:
        return None, None
    version = full_box[0]
    if version == 0:
        raw = stream.read(16)
        if len(raw) != 16:
            return None, None
        _created, _modified, timescale, duration = struct.unpack(">IIII", raw)
        no_duration = 0xFFFFFFFF
    elif version == 1:
        raw = stream.read(28)
        if len(raw) != 28:
            return None, None
        _created, _modified, timescale, duration = struct.unpack(">QQIQ", raw)
        no_duration = 0xFFFFFFFFFFFFFFFF
    else:
        return None, None
    if stream.tell() > atom_end or timescale <= 0 or duration == no_duration:
        return timescale or None, None
    seconds = duration / timescale
    return timescale, seconds if math.isfinite(seconds) else None


def _read_handler(stream: BinaryIO, payload_start: int, atom_end: int) -> bytes | None:
    stream.seek(payload_start)
    raw = stream.read(12)
    if len(raw) != 12 or stream.tell() > atom_end:
        return None
    return raw[8:12]


def _read_frame_rate(
    stream: BinaryIO, atom: _Atom, timescale: int
) -> float | None:
    _kind, payload_start, atom_end = atom
    stream.seek(payload_start)
    header = stream.read(8)
    if len(header) != 8:
        return None
    _version_flags, entry_count = struct.unpack(">II", header)
    if entry_count > (atom_end - stream.tell()) // 8:
        return None
    sample_count = 0
    elapsed_ticks = 0
    for _ in range(entry_count):
        entry = stream.read(8)
        if len(entry) != 8:
            return None
        samples, delta = struct.unpack(">II", entry)
        sample_count += samples
        elapsed_ticks += samples * delta
    if sample_count <= 0 or elapsed_ticks <= 0:
        return None
    rate = sample_count * timescale / elapsed_ticks
    return rate if math.isfinite(rate) and rate > 0 else None
