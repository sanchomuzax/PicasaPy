"""image://thumbs/<id> képszolgáltató a QML-rácsnak.

#144 óta ASZINKRON provider: a Qt alapból egyetlen image-loader szálon
hívná a szinkron providert, itt viszont saját QThreadPool (max 4 szál)
dolgozik — az OpenCV a dekódolás alatt elengedi a GIL-t, így RPi5-ön a
4 mag ténylegesen párhuzamosan generál. A provider nem ér el adatbázist:
a controller regisztrálja nála az aktuális fotók (útvonal, mtime, méret)
hármasait.

Szálkezelés (#53 GIL↔Qt deadlock-osztály): a pool-szálakon KIZÁRÓLAG
érték-típusú Qt-objektum (QImage) készül, QObject nem; a kész képet a
QQuickImageResponse.finished jelzi, amit a Qt dokumentáltan bármely
szálról fogad. A busy-számláló jelzése queued kézbesítéssel jut a
főszálra.

Hibatűrés (#66): a renderből kivétel SOHA nem szökhet ki — az elszökő
kivétel a kérést némán megölné, és a rácson random üres/beragadt cellák
maradnának. Hiba esetén placeholder megy vissza, a részletek a logba.
"""

from __future__ import annotations

import logging
import os
import threading
import zlib
from collections import OrderedDict
from pathlib import Path

from PySide6.QtCore import QRunnable, QThreadPool, Signal
from PySide6.QtGui import QImage, QTransform
from PySide6.QtQuick import (
    QQuickAsyncImageProvider,
    QQuickImageResponse,
    QQuickTextureFactory,
)

from picasapy.edit.session import EditSession
from picasapy.index import PhotoRecord
from picasapy.ini.filters import serialize_filters
from picasapy.thumbs import ThumbnailCache

# #151/7: közös konstans — az edit-előnézet provider is ezt importálja,
# hogy a placeholder-szürke egyetlen helyen legyen definiálva.
PLACEHOLDER_COLOR = 0xFFE8E8E8

# A generáló pool mérete: a 4 mag a mért optimum (rpi5-image-libs.md,
# ~3× gyorsulás 1 szálhoz képest); több szál RPi5-ön már nem segít.
_MAX_RENDER_THREADS = 4

# #142: az értelmezett filters-láncok cache-korlátja — kulcs a nyers
# filters= sztring (az azonos láncú képek osztoznak az eredményen);
# túlcsordulásnál a cache egyszerűen ürül, a következő render újraépíti.
_OPS_CACHE_CAPACITY = 4096

# A szűrt-thumb memóriacache bejegyzés-korlátja: 256 px-es JPEG-ből
# dekódolt QImage ~256 KB, a korlát így legfeljebb ~32 MB — egy mappányi
# szerkesztett kép görgetéséhez bőven elég, memóriában mégis szerény.
_FILTERED_MEMO_CAPACITY = 128

_log = logging.getLogger(__name__)


def _parse_ops(photo: PhotoRecord) -> tuple:
    """A filters= érték op-listája; parse-hibánál üres lánc (#73) — egy
    értelmezhetetlen Picasa-bejegyzés miatt nem eshet ki a bélyegkép."""
    try:
        return EditSession.from_value(photo.filters).ops
    except ValueError:
        _log.warning(
            "filters= nem értelmezhető (%s): %r", photo.name, photo.filters
        )
        return ()


def _chain_crc(ops: tuple) -> int:
    """A filters-lánc crc32-je (#144) — a szűrt-thumb memóriacache kulcsa
    ebből + a forgatásból áll; üres láncra 0."""
    if not ops:
        return 0
    return zlib.crc32(serialize_filters(ops).encode("utf-8"))


class _FilteredThumbMemo:
    """Második cache-szint a szűrt bélyegképeknek (#144): kulcs a forrás
    azonosítói + crc32(filters) + rotate, érték a KÉSZ (szűrt, forgatott)
    QImage. Találatnál se a filters-lánc, se a lemez-dekód, se a forgatás
    nem fut újra. LRU-kilakoltatás, szál-biztos (a pool több szála is
    olvassa/írja)."""

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

    def put(self, key: tuple, image: QImage) -> None:
        with self._lock:
            self._items[key] = QImage(image)
            self._items.move_to_end(key)
            while len(self._items) > self._capacity:
                self._items.popitem(last=False)


class _ThumbResponse(QQuickImageResponse):
    """Egy aszinkron thumbnail-kérés eredménye. A `finished` a pool-szálról
    megy ki — a Qt ezt dokumentáltan bármely szálról fogadja, és a korai
    (bekötés előtti) kibocsátást is kezeli."""

    def __init__(self):
        super().__init__()
        self._image = QImage()
        self._done = threading.Event()  # tesztek várakozásához

    def _finish(self, image: QImage) -> None:
        self._image = image
        self._done.set()
        self.finished.emit()

    def textureFactory(self) -> QQuickTextureFactory:
        return QQuickTextureFactory.textureFactoryForImage(self._image)


class _ThumbJob(QRunnable):
    """Pool-feladat: a szinkron render futtatása, majd a válasz lezárása.
    Kivétel innen sem szökhet ki (a render maga is hibatűrő)."""

    def __init__(self, provider: "ThumbnailProvider", photo_id: str,
                 response: _ThumbResponse):
        super().__init__()
        self._provider = provider
        self._photo_id = photo_id
        self._response = response

    def run(self) -> None:  # pool-szálon fut
        try:
            image = self._provider.requestImage(self._photo_id, None, None)
        except Exception:  # noqa: BLE001 — védőháló, elvileg elérhetetlen
            _log.exception("thumbnail-job hiba: %s", self._photo_id)
            image = _placeholder()
        self._response._finish(image)


def _placeholder() -> QImage:
    image = QImage(16, 16, QImage.Format.Format_RGB32)
    image.fill(PLACEHOLDER_COLOR)
    return image


class ThumbnailProvider(QQuickAsyncImageProvider):
    # #70: az éppen futó thumbnail-kérések száma — a pool szálaiból
    # jelezve; a controller busy-állapota köt rá (a Qt queued kézbesítéssel
    # a főszálra sorolja, polling nincs)
    activeCountChanged = Signal(int)

    def __init__(self, cache: ThumbnailCache, max_threads: int | None = None):
        super().__init__()
        self._cache = cache
        self._registry: dict[str, PhotoRecord] = {}
        # #142: lustán értelmezett filters-láncok — kulcs a nyers
        # filters= sztring, érték az (ops, crc32) pár
        self._ops_cache: dict[str, tuple[tuple, int]] = {}
        self._ops_lock = threading.Lock()
        self._active = 0
        self._active_lock = threading.Lock()
        self._memo = _FilteredThumbMemo()
        # saját pool a globalInstance helyett: a thumbnail-terhelés nem
        # szoríthatja ki az app többi háttérfeladatát (és fordítva)
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(
            max_threads
            if max_threads is not None
            else min(_MAX_RENDER_THREADS, os.cpu_count() or 1)
        )

    def register_photos(self, photos: tuple[PhotoRecord, ...]) -> None:
        """#142: a regisztráció csak a (immutábilis) rekordokat jegyzi meg —
        a filters= lánc parse-a LUSTA, először requestImage-kor fut (és az
        eredmény lánconként cache-elődik), így 50k fotó regisztrálása is
        olcsó marad."""
        self._registry = {str(photo.id): photo for photo in photos}

    def _resolved_ops(self, photo: PhotoRecord) -> tuple[tuple, int]:
        """A kép (ops, crc32) párja lusta parse-szal (#142) — az azonos
        filters= láncú képek osztoznak az eredményen. Szál-biztos: a pool
        több szála is hívhatja."""
        filters = photo.filters or ""
        if not filters.strip():
            return (), 0
        with self._ops_lock:
            cached = self._ops_cache.get(filters)
        if cached is not None:
            return cached
        ops = _parse_ops(photo)
        entry = (ops, _chain_crc(ops))
        with self._ops_lock:
            if len(self._ops_cache) >= _OPS_CACHE_CAPACITY:
                self._ops_cache.clear()
            self._ops_cache[filters] = entry
        return entry

    def requestImageResponse(self, photo_id: str, requested_size) -> _ThumbResponse:
        """Aszinkron belépési pont (a Qt a főszálon hívja): a munka a
        poolba kerül, a válasz azonnal visszamegy."""
        response = _ThumbResponse()
        self._pool.start(_ThumbJob(self, photo_id, response))
        return response

    def wait_for_done(self, msecs: int = 10_000) -> bool:
        """Minden folyamatban lévő pool-feladat bevárása (tesztekhez)."""
        return self._pool.waitForDone(msecs)

    def requestImage(self, photo_id, size, requested_size):
        """Szinkron render-mag (a pool-feladat és a tesztek hívják) —
        a korábbi szinkron provider változatlan szerződésével."""
        # a jelzés a lock ALATT megy ki: így az értékek kibocsátási sorrendje
        # a számláló sorrendjét követi (queued kézbesítésnél is), és a busy
        # nem ragadhat be egy megcserélődött 1→0 pár miatt
        with self._active_lock:
            self._active += 1
            self.activeCountChanged.emit(self._active)
        try:
            try:
                image = self._render(photo_id)
            except Exception:
                _log.exception("thumbnail-render hiba: %s", photo_id)
                image = QImage()
            if image.isNull():
                image = _placeholder()
            if size is not None:
                size.setWidth(image.width())
                size.setHeight(image.height())
            return image
        finally:
            with self._active_lock:
                self._active -= 1
                self.activeCountChanged.emit(self._active)

    def _render(self, photo_id: str) -> QImage:
        """A kész (szerkesztett, forgatott) thumbnail; null-QImage, ha a
        forrás nem dekódolható — a hívó ebből csinál placeholdert."""
        # az URL-ben ?r=<lépés> cache-buster jöhet — az id az első rész
        photo = self._registry.get(photo_id.split("?")[0])
        if photo is None:
            return QImage()
        path = Path(photo.folder_path) / photo.name
        mtime_ns, size_bytes = photo.mtime_ns, photo.size
        rotate = photo.rotate_steps
        ops, chain_crc = self._resolved_ops(photo)
        # #144: szűrt képnél előbb a memóriacache — találatnál a filters-
        # lánc, a lemez-dekód és a forgatás is kimarad
        memo_key = (str(path), mtime_ns, size_bytes, chain_crc, rotate)
        if ops:
            cached = self._memo.get(memo_key)
            if cached is not None:
                return cached
        # szerkesztő-lánc (filters=) a bélyegképen is (#59): a szűrt bélyegkép
        # a #163 óta NAGY bázison készül és külön cache-fájlba kerül — a
        # vágott kép így éles marad, nem a kész kis thumbnailt vágjuk tovább
        # (ami felnagyítva homályos lenne). A forgatás lentebb, a kész kis
        # bélyegképen történik (veszteségmentes 90°-os lépés).
        if ops:
            thumb = self._cache.get_or_create_edited(
                path, mtime_ns, size_bytes, ops
            )
        else:
            thumb = self._cache.get_or_create(path, mtime_ns, size_bytes)
        if thumb is None:
            _log.warning("thumbnail nem készült el: %s", path)
            return QImage()
        image = QImage(str(thumb))
        if image.isNull():
            _log.warning("cache-elt thumbnail nem olvasható: %s", thumb)
            return image
        if rotate:
            # nem-destruktív ini-forgatás (a cache-elt thumb forgatatlan)
            image = image.transformed(QTransform().rotate(90 * rotate))
        if ops:
            self._memo.put(memo_key, image)
        return image
