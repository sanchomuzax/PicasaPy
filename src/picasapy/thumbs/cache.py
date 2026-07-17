"""OpenCV-alapú thumbnail-generálás lemez-gyorsítótárral (ADR: rpi5-image-libs).

A cache-kulcs a forrásfájl útvonalából + mtime-jából + méretéből képzett
hash: fájlváltozáskor automatikusan új bejegyzés készül, a régit a későbbi
takarító dolga eltüntetni. Az OpenCV imread alapból alkalmazza az
EXIF-orientációt, ezért a thumbnail már helyesen forgatott.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path

import cv2
from PIL import Image, UnidentifiedImageError

_JPEG_QUALITY = 85

# Nagy forrásképnél redukált JPEG-dekódolás kíméli az RPi memóriáját;
# a cél a thumbnail-méret legalább kétszerese, hogy az INTER_AREA
# kicsinyítésnek maradjon mintavételi tartaléka.
_REDUCED_FLAGS = (
    (8, cv2.IMREAD_REDUCED_COLOR_8),
    (4, cv2.IMREAD_REDUCED_COLOR_4),
    (2, cv2.IMREAD_REDUCED_COLOR_2),
)


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
        image = cv2.imread(str(source), self._read_flag(source))
        if image is None:
            return None
        thumb = self._scale_down(image)
        ok, encoded = cv2.imencode(
            ".jpg", thumb, [cv2.IMWRITE_JPEG_QUALITY, _JPEG_QUALITY]
        )
        if not ok:
            return None
        self._write_atomic(target, encoded.tobytes())
        return target

    def _read_flag(self, source: Path) -> int:
        """Dekódolási flag: nagy képre redukált beolvasás (memóriakímélés)."""
        try:
            with Image.open(source) as probe:
                longest = max(probe.size)
        except (OSError, UnidentifiedImageError, ValueError):
            return cv2.IMREAD_COLOR
        for factor, flag in _REDUCED_FLAGS:
            if longest // factor >= self._size * 2:
                return flag
        return cv2.IMREAD_COLOR

    @staticmethod
    def _write_atomic(target: Path, payload: bytes) -> None:
        """Egyedi temp-név: a provider több szálról is kérheti ugyanazt a
        thumbnailt, fix névvel a párhuzamos írók összeakadnának."""
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(dir=target.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
            os.replace(temp_name, target)
        except BaseException:
            os.unlink(temp_name)
            raise

    def _scale_down(self, image):
        height, width = image.shape[:2]
        longest = max(width, height)
        if longest <= self._size:
            return image
        scale = self._size / longest
        new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
        return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
