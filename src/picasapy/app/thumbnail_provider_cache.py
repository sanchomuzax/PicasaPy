"""A szűrt bélyegképek szálbiztos, korlátos memóriatára."""

from __future__ import annotations

import threading
from collections import OrderedDict

from PySide6.QtGui import QImage

from .thumbnail_provider_constants import _FILTERED_MEMO_CAPACITY


class _FilteredThumbMemo:
    """Második cache-szint a szűrt bélyegképeknek (#144): kulcs a forrás
    azonosítói + filters CRC + aktuális crop + rotate, érték a KÉSZ (szűrt,
    forgatott) QImage. Találatnál se a filters-lánc, se a lemez-dekód, se a
    forgatás nem fut újra. LRU-kilakoltatás, szál-biztos (a pool több szála
    is olvassa/írja)."""

    def __init__(self, capacity: int = _FILTERED_MEMO_CAPACITY):
        self._capacity = capacity
        self._items: OrderedDict[tuple, QImage] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: tuple) -> QImage | None:
        with self._lock:
            image = self._items.get(key)
            if image is None:
                return None
            self._items.move_to_end(key)
            # sekély (copy-on-write) másolat: a hívó felé kiadott példány
            # független a cache-belitől, a pixeladat mégis közös
            return QImage(image)

    def clear(self) -> None:
        """A rekesz ürítése (#598) — a kézi gyorsítótár-ürítés hívja."""
        with self._lock:
            self._items.clear()

    def put(self, key: tuple, image: QImage) -> None:
        with self._lock:
            self._items[key] = QImage(image)
            self._items.move_to_end(key)
            while len(self._items) > self._capacity:
                self._items.popitem(last=False)
