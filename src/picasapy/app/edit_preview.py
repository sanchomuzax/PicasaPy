"""image://editpreview/<id> képszolgáltató a szerkesztő-panelhez.

A renderelés (dekód + filter-lánc) a `register()` hívásakor, a hívó (GUI)
szálán történik (#54): a Qt a `requestImage`-et saját kép-betöltő szálán
hívja, és ha ott futna a nehéz Python-munka, a fő szál GIL-birtokos
Qt-várakozásai (pl. néző-bezárás, engine-leállítás) kölcsönös várakozásba
(GIL-deadlockba) futhatnak — az app és a tesztek időnként lefagytak.
A `requestImage` így csak egy előre kirenderelt QImage-et ad vissza lock
alatt. A dekód a gyorsaság érdekében 2560 px-es élhosszra korlátozott
(a néző is ekkora forrást kér). A `?rev=<n>` az URL-ben cache-buster; az
azonosító az URL első (kérdőjel előtti) része.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path

import numpy as np
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QImageReader
from PySide6.QtQuick import QQuickImageProvider

from picasapy.ini.filters import FilterOp
from picasapy.render import apply_filters

_PLACEHOLDER_COLOR = 0xFFE8E8E8
_PLACEHOLDER_SIZE = 16
_MAX_PREVIEW_EDGE = 2560

_log = logging.getLogger(__name__)


class EditPreviewProvider(QQuickImageProvider):
    """`image://editpreview/<photo_id>?rev=<n>` — élő szerkesztési előnézet."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        self._images: dict[str, QImage] = {}
        # dekódolt forrás gyorsítótár (#72): élő csúszka-húzásnál (pl. tilt)
        # a register() gyakran hívódik ugyanarra a fotóra, csak a szűrő-
        # lánc változik — a lemezes dekódot nem kell minden alkalommal
        # megismételni, csak a filter-lánc újraszámolását.
        self._sources: dict[str, tuple[Path, float | None, np.ndarray | None]] = {}
        self._lock = threading.Lock()

    def register(self, photo_id: str, path: Path, ops: tuple[FilterOp, ...]) -> None:
        """Az aktuálisan szerkesztett fotó renderelése és eltárolása.

        A hívó (GUI) szálán fut — a provider-szálra nem jut Python-munka."""
        key = str(photo_id)
        path = Path(path)
        mtime = path.stat().st_mtime if path.exists() else None
        cached = self._sources.get(key)
        if cached is not None and cached[0] == path and cached[1] == mtime:
            source_array = cached[2]
        else:
            source_array = _decode_source(path)
            self._sources[key] = (path, mtime, source_array)
        image = _render_from_array(source_array, tuple(ops), path)
        with self._lock:
            self._images[key] = image

    def unregister(self, photo_id: str) -> None:
        """A fotó eltávolítása (szerkesztés vége)."""
        key = str(photo_id)
        self._sources.pop(key, None)
        with self._lock:
            self._images.pop(key, None)

    def requestImage(self, photo_id, size, requested_size):
        # az URL-ben ?rev=<szám> cache-buster jöhet — az id az első rész
        with self._lock:
            image = self._images.get(photo_id.split("?")[0], QImage())
        if image.isNull():
            image = _placeholder()
        # A néző sourceSize.width-del (magasság nélkül) kér: a (w, 0) a
        # QSize.isValid() szerint érvényes, de a scaled() üres képet adna
        # (#48). Fél-dimenziós kérésnél képaránytartó scaledToWidth/Height.
        if requested_size is not None:
            width, height = requested_size.width(), requested_size.height()
            smooth = Qt.TransformationMode.SmoothTransformation
            if width > 0 and height > 0:
                image = image.scaled(
                    requested_size, Qt.AspectRatioMode.KeepAspectRatio, smooth
                )
            elif width > 0:
                image = image.scaledToWidth(width, smooth)
            elif height > 0:
                image = image.scaledToHeight(height, smooth)
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


def _decode_source(path: Path) -> np.ndarray | None:
    """A forráskép dekódolása RGB numpy tömbbé, előnézet-felbontásra korlátozva.

    QImageReader + autoTransform: az EXIF-orientációt a betöltés alkalmazza —
    a néző natív Image-e is így tesz (autoTransform: true). A dekód mérete
    korlátozott: az előnézethez elég, és a GUI-szálon futó renderelés így
    nagy képnél is gyors marad. `None`, ha a kép nem olvasható be."""
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    native = reader.size()
    if native.isValid():
        longest = max(native.width(), native.height())
        if longest > _MAX_PREVIEW_EDGE:
            scale = _MAX_PREVIEW_EDGE / longest
            reader.setScaledSize(
                QSize(round(native.width() * scale), round(native.height() * scale))
            )
    source = reader.read()
    if source.isNull():
        return None
    return _qimage_to_rgb_array(source)


def _render_from_array(
    source_array: np.ndarray | None, ops: tuple[FilterOp, ...], path: Path
) -> QImage:
    if source_array is None:
        return QImage()
    try:
        result_array, _skipped = apply_filters(source_array, ops)
    except Exception:
        # #73: hibás/idegen lánc-bejegyzésnél a szűretlen kép a helyes
        # visszaesés, nem a placeholder (részleges előnézet elve)
        _log.exception("filters= nem alkalmazható az előnézeten: %s", path)
        return _rgb_array_to_qimage(source_array)
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
