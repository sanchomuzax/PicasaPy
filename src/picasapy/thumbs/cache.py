"""OpenCV-alapú thumbnail-generálás lemez-gyorsítótárral (ADR: rpi5-image-libs).

A cache-kulcs a forrásfájl útvonalából + mtime-jából + méretéből képzett
hash: fájlváltozáskor automatikusan új bejegyzés készül, a régit a későbbi
takarító dolga eltüntetni. Az OpenCV imread alapból alkalmazza az
EXIF-orientációt, ezért a thumbnail már helyesen forgatott.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import cv2

_JPEG_QUALITY = 85


class ThumbnailCache:
    def __init__(self, root: str | Path, size: int = 256):
        self._root = Path(root)
        self._size = size

    def thumbnail_path(self, photo_path: Path, mtime_ns: int, size_bytes: int) -> Path:
        key = f"{photo_path}\x00{mtime_ns}\x00{size_bytes}\x00{self._size}"
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
        return self._root / digest[:2] / f"{digest}.jpg"

    def get_or_create(
        self, photo_path: str | Path, mtime_ns: int, size_bytes: int
    ) -> Path | None:
        """A kész thumbnail útvonala; None, ha a forrás nem dekódolható."""
        source = Path(photo_path)
        target = self.thumbnail_path(source, mtime_ns, size_bytes)
        if target.exists():
            return target
        image = cv2.imread(str(source), cv2.IMREAD_COLOR)
        if image is None:
            return None
        thumb = self._scale_down(image)
        target.parent.mkdir(parents=True, exist_ok=True)
        ok, encoded = cv2.imencode(
            ".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY]
        )
        if not ok:
            return None
        temp = target.with_suffix(".tmp")
        temp.write_bytes(encoded.tobytes())
        temp.replace(target)
        return target

    def _scale_down(self, image):
        height, width = image.shape[:2]
        longest = max(width, height)
        if longest <= self._size:
            return image
        scale = self._size / longest
        new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
