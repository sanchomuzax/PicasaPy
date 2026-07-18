"""image://editpreview/<id> képszolgáltató a szerkesztő-panelhez.

A Qt a providert saját szálon hívja, így a szűrő-lánc alkalmazása nem
blokkolja a felületet. Az `EditController` regisztrálja nála az éppen
szerkesztett fotó (útvonal, filter-lánc) párját; a requestImage minden
hívásnál újra alkalmazza a láncot — élő előnézet. A `?rev=<n>` az URL-ben
csak cache-buster (a QML ettől tudja, mikor kérje újra a képet); az azonosító
az URL első (kérdőjel előtti) része, a thumbnail_provider mintája szerint.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QImageReader
from PySide6.QtQuick import QQuickImageProvider

from picasapy.ini.filters import FilterOp
from picasapy.render import apply_filters

_PLACEHOLDER_COLOR = 0xFFE8E8E8
_PLACEHOLDER_SIZE = 16


class EditPreviewProvider(QQuickImageProvider):
    """`image://editpreview/<photo_id>?rev=<n>` — élő szerkesztési előnézet."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._registry: dict[str, tuple[Path, tuple[FilterOp, ...]]] = {}

    def register(self, photo_id: str, path: Path, ops: tuple[FilterOp, ...]) -> None:
        """Az aktuálisan szerkesztett fotó regisztrálása/frissítése."""
        self._registry[str(photo_id)] = (path, ops)

    def unregister(self, photo_id: str) -> None:
        """A fotó eltávolítása a registry-ből (szerkesztés vége)."""
        self._registry.pop(str(photo_id), None)

    def requestImage(self, photo_id, size, requested_size):
        # az URL-ben ?rev=<szám> cache-buster jöhet — az id az első rész
        entry = self._registry.get(photo_id.split("?")[0])
        image = self._render(entry) if entry is not None else QImage()
        if image.isNull():
            image = _placeholder()
        if requested_size is not None and requested_size.isValid():
            image = image.scaled(
                requested_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image

    def _render(self, entry: tuple[Path, tuple[FilterOp, ...]]) -> QImage:
        path, ops = entry
        # QImageReader + autoTransform: az EXIF-orientációt a betöltés
        # alkalmazza — a néző natív Image-e is így tesz (autoTransform: true)
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        source = reader.read()
        if source.isNull():
            return QImage()
        array = _qimage_to_rgb_array(source)
        result_array, _skipped = apply_filters(array, ops)
        return _rgb_array_to_qimage(result_array)


def _placeholder() -> QImage:
    image = QImage(_PLACEHOLDER_SIZE, _PLACEHOLDER_SIZE, QImage.Format.Format_RGB32)
    image.fill(_PLACEHOLDER_COLOR)
    return image


def _qimage_to_rgb_array(image: QImage) -> np.ndarray:
    """QImage → RGB uint8 (H, W, 3) numpy tömb, a bufferre hivatkozás nélkül
    (a `.copy()` a QImage megszűnése után is biztonságos marad)."""
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    stride = converted.bytesPerLine()
    buffer = bytes(converted.constBits())
    raw = np.frombuffer(buffer, dtype=np.uint8).reshape((height, stride))
    return raw[:, : width * 3].reshape((height, width, 3)).copy()


def _rgb_array_to_qimage(array: np.ndarray) -> QImage:
    """RGB uint8 (H, W, 3) numpy tömb → QImage (a numpy-puffer másolatával)."""
    contiguous = np.ascontiguousarray(array)
    height, width = contiguous.shape[:2]
    stride = width * 3
    image = QImage(
        contiguous.data, width, height, stride, QImage.Format.Format_RGB888
    )
    return image.copy()
