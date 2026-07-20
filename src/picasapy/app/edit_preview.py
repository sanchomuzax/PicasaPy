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
from collections import OrderedDict
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
# LRU-kapacitás (#128): lapozáskor a beginEdit új id-vel regisztrál, endEdit
# nélkül — evikció híján a dekódolt források (~10–30 MB/kép) képenként
# halmozódnának. Két elem elég: az aktuális + az előző kép, így az
# előre-hátra lapozás újradekód nélkül gyors marad, a régebbiek felszabadulnak.
_LRU_CAPACITY = 2

_log = logging.getLogger(__name__)


class EditPreviewProvider(QQuickImageProvider):
    """`image://editpreview/<photo_id>?rev=<n>` — élő szerkesztési előnézet."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        # LRU-rendezett tárak (#128): a legrégebben használt kép esik ki,
        # ha a kapacitás betelik — lapozásnál így nem szivárog a memória.
        self._images: OrderedDict[str, QImage] = OrderedDict()
        # dekódolt forrás gyorsítótár (#72): élő csúszka-húzásnál (pl. tilt)
        # a register() gyakran hívódik ugyanarra a fotóra, csak a szűrő-
        # lánc változik — a lemezes dekódot nem kell minden alkalommal
        # megismételni, csak a filter-lánc újraszámolását.
        self._sources: OrderedDict[
            str, tuple[Path, float | None, np.ndarray | None]
        ] = OrderedDict()
        # lánc-prefix gyorsítótár (#140): élő csúszka-húzásnál csak az UTOLSÓ
        # op paramétere változik — az utolsó op ELŐTTI köztes eredményt
        # egyetlen rekeszben tároljuk (kulcs, prefix-lánc, forrás-referencia,
        # prefix-kép), így interakció közben csak az utolsó op fut újra.
        self._prefix_cache: (
            tuple[str, tuple[FilterOp, ...], np.ndarray, np.ndarray] | None
        ) = None
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
        # LRU-frissítés (#128): az aktuális kulcs a sor végére kerül, és a
        # kapacitáson túli legrégebbi bejegyzések felszabadulnak — az
        # előző kép még bent marad (gyors visszalapozás), a régebbiek nem.
        # A forrás-referencia (source_array) azonossága megmarad, így a
        # lánc-prefix gyorsítótár (#140) találata a re-store után is érvényes.
        self._sources[key] = (path, mtime, source_array)
        self._sources.move_to_end(key)
        while len(self._sources) > _LRU_CAPACITY:
            self._sources.popitem(last=False)
        # lánc-prefix gyorsítótár (#140): interakció közben csak az utolsó op fut
        image = self._render_cached(key, source_array, tuple(ops), path)
        with self._lock:
            self._images[key] = image
            self._images.move_to_end(key)
            while len(self._images) > _LRU_CAPACITY:
                self._images.popitem(last=False)

    def unregister(self, photo_id: str) -> None:
        """A fotó eltávolítása (szerkesztés vége)."""
        key = str(photo_id)
        self._sources.pop(key, None)
        if self._prefix_cache is not None and self._prefix_cache[0] == key:
            self._prefix_cache = None
        with self._lock:
            self._images.pop(key, None)

    # -- lánc-prefix gyorsítótár (#140) ------------------------------------

    def _render_cached(
        self,
        key: str,
        source_array: np.ndarray | None,
        ops: tuple[FilterOp, ...],
        path: Path,
    ) -> QImage:
        """Renderelés lánc-prefix gyorsítótárral: interakció közben (azonos
        prefix, csak az utolsó op paramétere változik) csak az utolsó op fut."""
        if source_array is None:
            return QImage()
        if not ops:
            return _rgb_array_to_qimage(source_array)
        try:
            prefix_array = self._cached_prefix(key, source_array, ops[:-1])
            result_array, _skipped = apply_filters(prefix_array, ops[-1:])
        except Exception:
            # #73: hibás/idegen lánc-bejegyzésnél a szűretlen kép a helyes
            # visszaesés, nem a placeholder (részleges előnézet elve)
            _log.exception("filters= nem alkalmazható az előnézeten: %s", path)
            return _rgb_array_to_qimage(source_array)
        return _rgb_array_to_qimage(result_array)

    def _cached_prefix(
        self,
        key: str,
        source_array: np.ndarray,
        prefix_ops: tuple[FilterOp, ...],
    ) -> np.ndarray:
        """Az utolsó op ELŐTTI köztes eredmény, gyorsítótárból ha lehet.

        A találat feltétele: azonos fotó-kulcs, azonos prefix-lánc és
        ugyanaz a (referencia szerint azonos) dekódolt forrás — a
        forrás-cache frissülésekor a prefix automatikusan érvénytelen."""
        cached = self._prefix_cache
        if (
            cached is not None
            and cached[0] == key
            and cached[1] == prefix_ops
            and cached[2] is source_array
        ):
            return cached[3]
        if prefix_ops:
            prefix_array, _skipped = apply_filters(source_array, prefix_ops)
        else:
            prefix_array = source_array
        self._prefix_cache = (key, prefix_ops, source_array, prefix_array)
        return prefix_array

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
