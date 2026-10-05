"""A videó első képkockáját dekódoló alfolyamat belépési pontja (#4273)."""

from __future__ import annotations

import sys
from pathlib import Path


def main(source: str | Path | None = None, output: str | Path | None = None) -> int:
    if source is None or output is None:
        if len(sys.argv) != 3:
            return 2
        source, output = sys.argv[1:]

    from picasapy.lazy_cv2 import cv2
    from picasapy.thumbs.cache import _decode_video_frame

    frame = _decode_video_frame(Path(source))
    if frame is None:
        return 1

    try:
        ok, encoded = cv2.imencode(".png", frame)
    except cv2.error:
        return 1
    if not ok:
        return 1
    try:
        Path(output).write_bytes(encoded.tobytes())
    except OSError:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
