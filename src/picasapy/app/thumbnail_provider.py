"""image://thumbs/<id> képszolgáltató a QML-rácsnak.

A Qt a providert saját szálon hívja, így a thumbnail-generálás nem
blokkolja a felületet. A provider nem ér el adatbázist: a controller
regisztrálja nála az aktuális fotók (útvonal, mtime, méret) hármasait.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from picasapy.index import PhotoRecord
from picasapy.thumbs import ThumbnailCache

_PLACEHOLDER_COLOR = 0xFFE8E8E8


class ThumbnailProvider(QQuickImageProvider):
    def __init__(self, cache: ThumbnailCache):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._cache = cache
        self._registry: dict[str, tuple[Path, int, int]] = {}

    def register_photos(self, photos: tuple[PhotoRecord, ...]) -> None:
        self._registry = {
            str(photo.id): (
                Path(photo.folder_path) / photo.name,
                photo.mtime_ns,
                photo.size,
            )
            for photo in photos
        }

    def requestImage(self, photo_id, size, requested_size):
        entry = self._registry.get(photo_id)
        thumb = self._cache.get_or_create(*entry) if entry else None
        image = QImage(str(thumb)) if thumb else QImage()
        if image.isNull():
            image = QImage(16, 16, QImage.Format.Format_RGB32)
            image.fill(_PLACEHOLDER_COLOR)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image
