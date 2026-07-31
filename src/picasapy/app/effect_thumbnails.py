"""image://effectthumb/<photo_id>/<effekt> — effekt-gomb bélyegképek (#338).

Az eredeti Picasában minden effekt-gomb a SAJÁT fotó adott effekttel
renderelt, kicsinyített képét mutatja — nálunk eddig sima felirat-gomb volt.
Ez a modul adja a hozzá tartozó (a `render/chain.py` `apply_filters`-ét és
az `effect_params.py` katalógusát használó) képszolgáltatót.

KRITIKUS TELJESÍTMÉNY (36 effekt/fotó, a fül megnyitásakor mind egyszerre
kérhető): a `thumbnail_provider.py` mintáját követve ASZINKRON, saját
`QThreadPool`-lal — a QML-szál sosem vár a renderelésre, a kép a `finished`
jelzéssel érkezik meg, amikor kész. Két gyorsítótár-szint:

  - forrás-cache (`_source_for`): a fotó KIS FELBONTÁSÚ (``_SOURCE_EDGE``
    px-es) dekódolt tömbje, fotónként (útvonal+mtime) EGYSZER — a 36 effekt
    mind erről a közös forrásról indul, a lemez-dekód nem ismétlődik;
  - bélyegkép-cache (`_ThumbCache`): a KÉSZ (effekttel renderelt,
    ``_THUMB_EDGE`` px-re kicsinyített) QImage, (fotó, effekt) kulccsal —
    effektenként CSAK EGYSZER számol, amíg a fotó nem változik.

Tudatos egyszerűsítés: a bélyegkép a fotó ALAP (a jelenleg szerkesztett
lánc NÉLKÜLI) állapotán mutatja az effektet, nem az éppen alkalmazott
vágás/finomhangolás/korábbi effektek TETEJÉN. A pontos "mit látnál, ha most
erre kattintanál" előnézet a teljes láncot figyelembe véve minden apró
szerkesztői lépésnél (pl. csúszka-húzásnál) mind a 36 bélyegképet
újraszámolná — a válaszidő ennél fontosabb, mint ez a kis pontossági
engedmény (a nagy élő előnézet, `edit_preview.py`, változatlanul a teljes
láncot mutatja).

Hibatűrés (#66 mintája): a renderből kivétel SOHA nem szökhet ki — hiba
esetén placeholder megy vissza, a részletek a logba.
"""

from __future__ import annotations

import logging
import os
import threading
from collections import OrderedDict
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import numpy as np
from PySide6.QtCore import QRunnable, QSize, Qt, QThreadPool
from PySide6.QtGui import QImage, QImageReader
from PySide6.QtQuick import (
    QQuickAsyncImageProvider,
    QQuickImageResponse,
    QQuickTextureFactory,
)

from picasapy.app.edit_controller import _EFFECT_NAMES
from picasapy.app.effect_params import effect_params, format_param_values
from picasapy.ini.filters import FilterOp
from picasapy.render import apply_filters

from .thumbnail_provider import PLACEHOLDER_COLOR

if TYPE_CHECKING:
    from picasapy.index import PhotoRecord

_log = logging.getLogger(__name__)

#: A forrás dekódolási felbontása: a legtöbb effekt a kép RÖVIDEBB oldalának
#: százalékában skálázódik (ld. render/effects_frames.py), ezért a teljes
#: felbontású dekód (mint az edit_preview 2560px-e) itt felesleges lenne —
#: ennyi bőven elég a kért 64-96px-es bélyegkép alapjának.
_SOURCE_EDGE = 200
#: A KÉSZ bélyegkép mérete (leghosszabb él) — a feladat 64-96px sávjának közepe.
_THUMB_EDGE = 80
#: Kis pool: a bélyegkép-gyártás nem versenyezhet a nagy thumbnail-rács
#: (`thumbnail_provider.py`, 4 szál) generálásával — 2 szál is bőven elég
#: 36, már kis felbontású forrásból induló effekthez.
_MAX_RENDER_THREADS = 2
#: forrás-cache kapacitása: az aktuális + az előző fotó, a lapozás mintája
#: szerint (edit_preview.py `_LRU_CAPACITY`)
_SOURCE_CACHE_CAPACITY = 2
#: bélyegkép-cache: bőven elég egyszerre több fotó mind a 36 effektjéhez
_THUMB_CACHE_CAPACITY = 256

#: A `filters=`-ben ismert effekt-kulcsok — a `render/chain.py` `_HANDLERS`
#: kis-nagybetű-tűrő (`op.name.casefold()`), ezért a bélyegkép-rendereléshez
#: az ini-írásnál használt CamelCase írásmód (`EditController._EFFECT_INI_NAMES`)
#: NEM szükséges, elég a kisbetűs kulcs. A lista magát az
#: `edit_controller.py`-t importálja (egyetlen forrás, nincs duplikált,
#: idővel elcsúszható másolat).
EFFECT_NAMES: tuple[str, ...] = _EFFECT_NAMES

PhotoLookup = Callable[[str], "PhotoRecord | None"]


def _default_op(effect: str) -> FilterOp:
    """Az effekt alapértékes `FilterOp`-ja — ugyanazok az alapértékek, mint
    amivel a csúszkás alpanel (EditorPanel.qml `openParamPanel`) indul."""
    params = effect_params(effect)
    if not params:
        return FilterOp(name=effect, params=("1",))
    formatted = format_param_values([p.default for p in params])
    return FilterOp(name=effect, params=("1", *formatted))


def _decode_small_source(path: Path) -> np.ndarray | None:
    """A forráskép dekódolása kis (`_SOURCE_EDGE`) RGB numpy tömbbé.

    QImageReader + autoTransform, az edit_preview.py `_decode_source`
    mintája — csak jóval kisebb célfelbontással, a bélyegkép-gyártáshoz."""
    reader = QImageReader(str(path))
    reader.setAutoTransform(True)
    native = reader.size()
    if native.isValid() and native.width() > 0 and native.height() > 0:
        longest = max(native.width(), native.height())
        scale = _SOURCE_EDGE / longest
        reader.setScaledSize(
            QSize(
                max(1, round(native.width() * scale)),
                max(1, round(native.height() * scale)),
            )
        )
    image = reader.read()
    if image.isNull():
        return None
    return _qimage_to_rgb_array(image)


def _qimage_to_rgb_array(image: QImage) -> np.ndarray:
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    stride = converted.bytesPerLine()
    buffer = bytes(converted.constBits())
    raw = np.frombuffer(buffer, dtype=np.uint8).reshape((height, stride))
    return raw[:, : width * 3].reshape((height, width, 3)).copy()


def _rgb_array_to_qimage(array: np.ndarray) -> QImage:
    contiguous = np.ascontiguousarray(array)
    height, width = contiguous.shape[:2]
    stride = width * 3
    image = QImage(
        contiguous.data, width, height, stride, QImage.Format.Format_RGB888
    )
    return image.copy()


def _scale_to_thumb(image: QImage) -> QImage:
    smooth = Qt.TransformationMode.SmoothTransformation
    if image.width() <= 0 or image.height() <= 0:
        return image
    if image.width() >= image.height():
        return image.scaledToWidth(_THUMB_EDGE, smooth)
    return image.scaledToHeight(_THUMB_EDGE, smooth)


def _placeholder() -> QImage:
    image = QImage(16, 16, QImage.Format.Format_RGB32)
    image.fill(PLACEHOLDER_COLOR)
    return image


class _ThumbCache:
    """LRU: (útvonal, mtime, effekt) → KÉSZ bélyegkép-QImage. Szál-biztos —
    a pool több szála is olvashatja/írhatja (`thumbnail_provider._FilteredThumbMemo`
    mintája)."""

    def __init__(self, capacity: int = _THUMB_CACHE_CAPACITY) -> None:
        self._capacity = capacity
        self._items: OrderedDict[tuple, QImage] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: tuple) -> QImage | None:
        with self._lock:
            image = self._items.get(key)
            if image is None:
                return None
            self._items.move_to_end(key)
            return QImage(image)

    def put(self, key: tuple, image: QImage) -> None:
        with self._lock:
            self._items[key] = QImage(image)
            self._items.move_to_end(key)
            while len(self._items) > self._capacity:
                self._items.popitem(last=False)


class _EffectThumbResponse(QQuickImageResponse):
    """Egy aszinkron bélyegkép-kérés eredménye (`thumbnail_provider._ThumbResponse`
    mintája) — a `finished` a pool-szálról megy ki, a Qt ezt bármely
    szálról dokumentáltan fogadja."""

    def __init__(self) -> None:
        super().__init__()
        self._image = QImage()
        self._done = threading.Event()  # tesztek várakozásához

    def _finish(self, image: QImage) -> None:
        self._image = image
        self._done.set()
        self.finished.emit()

    def textureFactory(self) -> QQuickTextureFactory:
        return QQuickTextureFactory.textureFactoryForImage(self._image)


class _EffectThumbJob(QRunnable):
    """Pool-feladat: a szinkron render futtatása, majd a válasz lezárása.
    Kivétel innen sem szökhet ki."""

    def __init__(
        self, provider: "EffectThumbnailProvider", id_str: str,
        response: _EffectThumbResponse,
    ) -> None:
        super().__init__()
        self._provider = provider
        self._id = id_str
        self._response = response

    def run(self) -> None:  # pool-szálon fut
        try:
            image = self._provider.requestImage(self._id, None, None)
        except Exception:  # noqa: BLE001 — védőháló, elvileg elérhetetlen
            _log.exception("effekt-bélyegkép job hiba: %s", self._id)
            image = _placeholder()
        self._response._finish(image)


class EffectThumbnailProvider(QQuickAsyncImageProvider):
    """`image://effectthumb/<photo_id>/<effekt>` — az EditorPanel effekt-
    rácsának bélyegképei.

    A `photo_lookup` egy `photo_id -> PhotoRecord | None` függvény — a
    valós appban a MEGLÉVŐ `ThumbnailProvider.photo_record` (a teljes
    könyvtár már regisztrálva van nála, nem kell párhuzamos regisztráció)."""

    def __init__(
        self, photo_lookup: PhotoLookup, max_threads: int | None = None
    ) -> None:
        super().__init__()
        self._lookup = photo_lookup
        self._source_cache: OrderedDict[tuple, np.ndarray] = OrderedDict()
        self._source_lock = threading.Lock()
        self._thumb_cache = _ThumbCache()
        # saját, KIS pool (#338): nem versenyezhet a nagy thumbnail-rács
        # generálásával a közös CPU-kapacitásért
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(
            max_threads
            if max_threads is not None
            else min(_MAX_RENDER_THREADS, os.cpu_count() or 1)
        )

    def requestImageResponse(self, id_str: str, requested_size) -> _EffectThumbResponse:
        """Aszinkron belépési pont (a Qt a főszálon hívja): a munka a
        poolba kerül, a válasz azonnal visszamegy."""
        response = _EffectThumbResponse()
        self._pool.start(_EffectThumbJob(self, id_str, response))
        return response

    def wait_for_done(self, msecs: int = 10_000) -> bool:
        """Minden folyamatban lévő pool-feladat bevárása (tesztekhez)."""
        return self._pool.waitForDone(msecs)

    def requestImage(self, id_str: str, size, requested_size) -> QImage:
        """Szinkron render-mag (a pool-feladat és a tesztek hívják)."""
        try:
            image = self._render(id_str)
        except Exception:  # noqa: BLE001 — védőháló (#66)
            _log.exception("effekt-bélyegkép render hiba: %s", id_str)
            image = QImage()
        if image.isNull():
            image = _placeholder()
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image

    def _render(self, id_str: str) -> QImage:
        # az id "<fotó-id>/<effekt>" alakú, opcionális "?..." cache-buster
        # résszel (a mai URL-eink nem adnak ilyet, de a többi provider
        # mintáját követve tűrjük, ha jönne)
        raw = id_str.split("?")[0]
        photo_id, _sep, effect = raw.partition("/")
        effect_key = effect.strip().casefold()
        if not photo_id or effect_key not in EFFECT_NAMES:
            return QImage()
        photo = self._lookup(photo_id)
        if photo is None:
            return QImage()
        path = Path(photo.folder_path) / photo.name
        cache_key = (str(path), photo.mtime_ns, effect_key)
        cached = self._thumb_cache.get(cache_key)
        if cached is not None:
            return cached
        source = self._source_for(path, photo.mtime_ns)
        if source is None:
            return QImage()
        op = _default_op(effect_key)
        result, _skipped = apply_filters(source, (op,))
        image = _scale_to_thumb(_rgb_array_to_qimage(result))
        self._thumb_cache.put(cache_key, image)
        return image

    def _source_for(self, path: Path, mtime_ns: int) -> np.ndarray | None:
        key = (str(path), mtime_ns)
        with self._source_lock:
            cached = self._source_cache.get(key)
            if cached is not None:
                self._source_cache.move_to_end(key)
                return cached
        source = _decode_small_source(path)
        if source is None:
            return None
        with self._source_lock:
            self._source_cache[key] = source
            self._source_cache.move_to_end(key)
            while len(self._source_cache) > _SOURCE_CACHE_CAPACITY:
                self._source_cache.popitem(last=False)
        return source
