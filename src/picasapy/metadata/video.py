"""A videók indexeléséhez szükséges, könnyű metaadatok kiolvasása."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import cv2


@dataclass(frozen=True)
class VideoMetadata:
    """Videóformátum, képkockasebesség és hossz másodpercben."""

    movie_format: str | None = None
    frame_rate: float | None = None
    duration_seconds: float | None = None


EMPTY_VIDEO_METADATA = VideoMetadata()


def read_video_metadata(path: str | Path) -> VideoMetadata:
    """Videófejlécből kiolvassa a panel mezőit; sérült fájlnál nem dob.

    A formátumot a felismert fájlkiterjesztés adja. A hossz a képkockaszám
    és a dekóder által megadott képkockasebesség hányadosa; használható
    időalap hiányában csak az ismert formátum kerül az indexbe.
    """
    movie_format = Path(path).suffix.removeprefix(".").upper() or None
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
