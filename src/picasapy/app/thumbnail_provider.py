"""image://thumbs/<id> képszolgáltató a QML-rácsnak.

A Qt a providert saját szálon hívja, így a thumbnail-generálás nem
blokkolja a felületet. A provider nem ér el adatbázist: a controller
regisztrálja nála az aktuális fotók (útvonal, mtime, méret) hármasait.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QImage, QTransform
from PySide6.QtQuick import QQuickImageProvider

from picasapy.edit.session import EditSession
from picasapy.index import PhotoRecord
from picasapy.render import apply_filters
from picasapy.thumbs import ThumbnailCache

from .edit_preview import _qimage_to_rgb_array, _rgb_array_to_qimage

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
                photo.rotate_steps,
                EditSession.from_value(photo.filters).ops,
            )
            for photo in photos
        }

    def requestImage(self, photo_id, size, requested_size):
        # az URL-ben ?r=<lépés> cache-buster jöhet — az id az első rész
        entry = self._registry.get(photo_id.split("?")[0])
        thumb = self._cache.get_or_create(*entry[:3]) if entry else None
        image = QImage(str(thumb)) if thumb else QImage()
        if image.isNull():
            image = QImage(16, 16, QImage.Format.Format_RGB32)
            image.fill(_PLACEHOLDER_COLOR)
        else:
            if entry and entry[4]:
                # szerkesztő-lánc (filters=) a bélyegképen is (#59) — a
                # cache-elt thumb az eredeti, a láncot itt alkalmazzuk
                # (thumb-méreten olcsó)
                array, _skipped = apply_filters(
                    _qimage_to_rgb_array(image), entry[4]
                )
                image = _rgb_array_to_qimage(array)
            if entry and entry[3]:
                # nem-destruktív ini-forgatás (a cache-elt thumb forgatatlan)
                image = image.transformed(QTransform().rotate(90 * entry[3]))
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image
