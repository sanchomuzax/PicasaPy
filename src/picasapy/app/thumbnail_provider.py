"""image://thumbs/<id> képszolgáltató a QML-rácsnak.

A Qt a providert saját szálon hívja, így a thumbnail-generálás nem
blokkolja a felületet. A provider nem ér el adatbázist: a controller
regisztrálja nála az aktuális fotók (útvonal, mtime, méret) hármasait.

Hibatűrés (#66): a requestImage-ből kivétel SOHA nem szökhet ki — a Qt
képbetöltő szálán az elszökő kivétel a kérést némán megöli, és a rácson
random üres/beragadt cellák maradnak. Hiba esetén placeholder megy
vissza, a részletek pedig a logba kerülnek.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtGui import QImage, QTransform
from PySide6.QtQuick import QQuickImageProvider

from picasapy.edit.session import EditSession
from picasapy.index import PhotoRecord
from picasapy.render import apply_filters
from picasapy.thumbs import ThumbnailCache

from .edit_preview import _qimage_to_rgb_array, _rgb_array_to_qimage

_PLACEHOLDER_COLOR = 0xFFE8E8E8

_log = logging.getLogger(__name__)


class ThumbnailProvider(QQuickImageProvider):
    def __init__(self, cache: ThumbnailCache):
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._cache = cache
        self._registry: dict[str, tuple[Path, int, int, int, tuple]] = {}

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
        try:
            image = self._render(photo_id)
        except Exception:
            _log.exception("thumbnail-render hiba: %s", photo_id)
            image = QImage()
        if image.isNull():
            image = QImage(16, 16, QImage.Format.Format_RGB32)
            image.fill(_PLACEHOLDER_COLOR)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image

    def _render(self, photo_id: str) -> QImage:
        """A kész (szerkesztett, forgatott) thumbnail; null-QImage, ha a
        forrás nem dekódolható — a hívó ebből csinál placeholdert."""
        # az URL-ben ?r=<lépés> cache-buster jöhet — az id az első rész
        entry = self._registry.get(photo_id.split("?")[0])
        if entry is None:
            return QImage()
        thumb = self._cache.get_or_create(*entry[:3])
        if thumb is None:
            _log.warning("thumbnail nem készült el: %s", entry[0])
            return QImage()
        image = QImage(str(thumb))
        if image.isNull():
            _log.warning("cache-elt thumbnail nem olvasható: %s", thumb)
            return image
        if entry[4]:
            # szerkesztő-lánc (filters=) a bélyegképen is (#59) — a
            # cache-elt thumb az eredeti, a láncot itt alkalmazzuk
            # (thumb-méreten olcsó)
            array, _skipped = apply_filters(_qimage_to_rgb_array(image), entry[4])
            image = _rgb_array_to_qimage(array)
        if entry[3]:
            # nem-destruktív ini-forgatás (a cache-elt thumb forgatatlan)
            image = image.transformed(QTransform().rotate(90 * entry[3]))
        return image
