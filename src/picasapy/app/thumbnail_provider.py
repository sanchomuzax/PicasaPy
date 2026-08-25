"""image://thumbs/<id> képszolgáltató a QML-rácsnak.

#144 óta ASZINKRON provider: a Qt alapból egyetlen image-loader szálon
hívná a szinkron providert, itt viszont saját QThreadPool (max 4 szál)
dolgozik — az OpenCV a dekódolás alatt elengedi a GIL-t, így RPi5-ön a
4 mag ténylegesen párhuzamosan generál. A provider nem ér el adatbázist:
a controller regisztrálja nála az aktuális fotók (útvonal, mtime, méret)
hármasait.

Szálkezelés (#53 GIL↔Qt deadlock-osztály): a pool-szálakon KIZÁRÓLAG
érték-típusú Qt-objektum (QImage) készül, QObject nem; a kész képet a
QQuickImageResponse.finished jelzi. A busy-számláló jelzése queued
kézbesítéssel jut a főszálra.

Élettartam (#1457): a jelzés KIBOCSÁTÁSA szálbiztos, de ez nem ugyanaz,
mint élettartam-biztos — egy már megsemmisített válaszon a `finished`
kibocsátása use-after-free, és a folyamat összeomlik (mért SIGSEGV).
A válasz C++ oldalát a QML-motor kezeli: a saját olvasószálán hozza
létre, és ott is semmisíti meg, amikor végzett vele. A PySide viszont
a Python-oldali referenciaszámot is figyeli (a válasz `ownedByPython`
marad azután is, hogy visszaadtuk a motornak) — ha tehát az utolsó
Python-hivatkozás előbb esik ki, mint ahogy a motor végez, akkor a
PYTHON húzza ki a motor alól az objektumot, miközben az még nyers
mutatót tart rá. Márpedig az egyetlen Python-hivatkozást eddig a
pool-feladat tartotta, amit a QThreadPool a `run()` után azonnal
eldob. Ezért a provider maga tart erős hivatkozást minden élő válaszra,
és csak a `destroyed` jelzésre — vagyis miután a motor ténylegesen
elengedte — ejti el.

Hibatűrés (#66): a renderből kivétel SOHA nem szökhet ki — az elszökő
kivétel a kérést némán megölné, és a rácson random üres/beragadt cellák
maradnának. Hiba esetén placeholder megy vissza, a részletek a logba.
"""

from __future__ import annotations

import itertools
import logging
import os
import threading
import zlib
from collections import OrderedDict
from pathlib import Path

import shiboken6
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
from .worker_thread import register_pool_owner

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
    """Egy aszinkron thumbnail-kérés eredménye.

    A képet a pool-szál készíti el és adja át (`_finish`), de a `finished`
    jelzés #1457 óta NEM onnan megy ki, hanem a válasz saját szálán —
    ugyanazon, amelyiken a motor a választ létrehozta és el is pusztítja.
    Így a kibocsátás és a megsemmisítés nem futhat egyszerre ugyanazon az
    objektumon. Az élettartam egészéről a modul-docstring „Élettartam"
    szakasza szól; a válasz életben tartása a `ThumbnailProvider` dolga.

    Az itteni zár azt a két útvonalat választja szét, amelyik egyszerre
    nyúlna a válaszhoz: a pool-szál lezárását (`_finish`) és a motor
    lemondását (`cancel`, a motor szálán)."""

    def __init__(self):
        super().__init__()
        self._image = QImage()
        self._done = threading.Event()  # tesztek várakozásához
        self._lock = threading.Lock()
        self._cancelled = False

    def cancel(self) -> None:
        """A motor jelzi, hogy a válaszra már nincs szüksége (a QML-elem
        eltűnt, a modell újraépült). A zár alatt beállított jelző után a
        `_finish` már nem ír képet a válaszba — fölösleges munka lenne."""
        with self._lock:
            self._cancelled = True
            self._done.set()

    def _finish(self, image: QImage) -> None:
        """A pool-szál lezárja a választ. A zár a `cancel`-lel szemben véd,
        a `shiboken6.isValid` pedig a már megszűnt C++ oldal ellen: egy
        elszabadult `finished.emit()` ott SIGSEGV-vel járna (#1457)."""
        with self._lock:
            if not shiboken6.isValid(self):
                # a motor már elpusztította a választ — nincs mit lezárni,
                # és nincs kinek jeleznünk; a várakozókat elengedjük
                self._done.set()
                return
            if not self._cancelled:
                self._image = image
            self._done.set()
            # ⚠️ #1457 — A JELZÉS ITT, A POOL-SZÁLRÓL MEGY KI.
            #
            # Készült egy változat, amely ezt a válasz saját szálára
            # ütemezte át (`QMetaObject.invokeMethod` + `QueuedConnection`),
            # hogy a kibocsátás és a motor `deleteLater`-e egy szálra
            # kerüljön. Az ötlet védhető, DE a CI-ben ezután egy MÁSIK
            # tesztfájl kezdett összeomlani (`test_collage_panel_wiring_985`),
            # miközben a főág ugyanott zöld volt — és a bukást helyben,
            # terhelés alatt, nyolc körben SEM sikerült reprodukálni.
            #
            # Bizonyítatlan gyanúval nem viszünk be időzítést változtató
            # módosítást: az átütemezés kikerült, a jegy (#1457) nyitva
            # marad rá. Az itt maradó védelmek — a zár, a `cancel`, az
            # élő válaszok nyilvántartása — NEM változtatnak időzítést,
            # és mindegyiket külön őr méri.
            self.finished.emit()


    def textureFactory(self) -> QQuickTextureFactory:
        """A kész kép átadása a motornak — a MOTOR szálán hívódik.

        ⚠️ A zár nem formalitás. A `_finish` a POOL-szálon írja a
        `self._image`-et, ezt a metódust viszont a motor a SAJÁT szálán
        hívja. A `QImage` implicit megosztású: a másolat a
        hivatkozásszámlálót lépteti, nem a képpontokat másolja. Ha az írás
        és az olvasás átfedi egymást, a számláló sérül — és a hiba nem ott
        csattan, ahol keletkezett, hanem egy későbbi felszabadításnál,
        látszólag véletlenszerű helyen (#1457).

        A `_finish` és a `cancel` már ugyanezt a zárat használja; ez a
        harmadik út, amelyik ugyanahhoz a mezőhöz nyúl."""
        with self._lock:
            image = self._image
        return QQuickTextureFactory.textureFactoryForImage(image)


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
    # #459: a forrás nem dekódolható (sérült/betölthetetlen fájl) — az
    # eredeti Picasa itt ajánlotta fel az elrejtést ("Picasa had a problem
    # loading this file(s). Would you like to hide the files on disk?").
    # A pool-szálról jön, a Qt queued kézbesítéssel a főszálra sorolja
    # (az `activeCountChanged` mintája). Csak akkor emittálódik, ha a
    # fotó REGISZTRÁLT (nem lapozás/törlés miatti eltűnés) és a dekódolás
    # ténylegesen elbukott.
    brokenImageDetected = Signal(str)

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
        # #1457: erős hivatkozás MINDEN élő válaszra. A motor nyers C++
        # mutatót tart a válaszra, a PySide viszont a Python-oldali
        # referenciaszámot is figyeli — e nyilvántartás nélkül a válasz
        # utolsó Python-hivatkozását a pool-feladat tartaná, és annak
        # eldobásakor a Python semmisítené meg a motor alól (use-after-free).
        # A bejegyzés a `destroyed` jelzésre szűnik meg, vagyis miután a
        # motor ténylegesen elengedte a választ — így a Python sosem előzi
        # meg a motort.
        self._live_responses: dict[int, _ThumbResponse] = {}
        self._live_lock = threading.Lock()
        self._response_tokens = itertools.count()
        # saját pool a globalInstance helyett: a thumbnail-terhelés nem
        # szoríthatja ki az app többi háttérfeladatát (és fordítva)
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(
            max_threads
            if max_threads is not None
            else min(_MAX_RENDER_THREADS, os.cpu_count() or 1)
        )
        # #988/#999: a pool bejelentkezik a folyamat-szintű bevárásba,
        # hogy a lebontás ne felejthesse el (a `QRunnable`-ök ugyanúgy
        # Qt-objektumokat érnek el, mint a daemon-szálak — #430)
        register_pool_owner(self)

    def register_photos(self, photos: tuple[PhotoRecord, ...]) -> None:
        """#142: a regisztráció csak a (immutábilis) rekordokat jegyzi meg —
        a filters= lánc parse-a LUSTA, először requestImage-kor fut (és az
        eredmény lánconként cache-elődik), így 50k fotó regisztrálása is
        olcsó marad."""
        self._registry = {str(photo.id): photo for photo in photos}

    def register_additional_photos(self, photos: tuple[PhotoRecord, ...]) -> None:
        """#23: fotók hozzáadása a MEGLÉVŐ regisztráció mellé (nem cseréli
        le, ellentétben a `register_photos`-szal) — az Import forrásból
        előnézete így nem takarja el a fő könyvtár épp regisztrált
        bélyegképeit, amíg az Import-dialógus nyitva van. A hívó felelőssége
        (ld. `import_source_controller.py`) ütközésmentes, saját id-
        tartományt használni (pl. negatív id-k), hogy sose írjon felül
        valódi könyvtárbeli fotót.

        FOGLALT (negatív) id-tartományok — az egyszerre nyitva lévő
        dialógusok se üssék egymást:
          * `-1`-től lefelé: Import forrásból előnézet
            (`import_source_controller._preview_photo_record`);
          * `-1_000_000`-tól lefelé: duplikátum-kereső találatok
            (`dedup_controller.DEDUP_THUMB_ID_BASE`, #298).
        Új hívó ide vegyen fel magának új sávot."""
        extra = {str(photo.id): photo for photo in photos}
        self._registry = {**self._registry, **extra}

    def photo_record(self, photo_id: str) -> PhotoRecord | None:
        """A regisztrált fotó rekordja (#338 effekt-bélyegképek): a
        szerkesztőpanel effekt-gombjainak bélyegkép-providere (
        `effect_thumbnails.py`) ebből olvassa ki az útvonalat — nem kell
        neki saját, párhuzamos fotó-regisztrációt vezetnie."""
        return self._registry.get(str(photo_id))

    def unregister_additional_photos(self, ids: tuple[str, ...]) -> None:
        """A `register_additional_photos`-szal felvett bejegyzések
        eltávolítása (pl. új szkennelés előtt vagy a dialógus zárásakor) —
        a valódi könyvtár bejegyzéseit nem érinti."""
        if not ids:
            return
        excluded = set(ids)
        self._registry = {
            key: value for key, value in self._registry.items() if key not in excluded
        }

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
        """Aszinkron belépési pont (a Qt a saját olvasószálán hívja): a
        munka a poolba kerül, a válasz azonnal visszamegy.

        A válasz #1457 óta bekerül a provider nyilvántartásába is, és csak
        a motor általi megszüntetéskor (`destroyed`) kerül ki onnan."""
        response = _ThumbResponse()
        token = next(self._response_tokens)
        with self._live_lock:
            self._live_responses[token] = response
        # A kötés SZÁNDÉKOSAN nem zárja magába a választ (csak a tokent),
        # különben a nyilvántartás sosem ürülne. A `destroyed` átadja a
        # megszűnő objektumot is — azt eldobjuk (`*_`): ilyenkor a C++
        # oldal már érvénytelen, hozzányúlni tilos.
        response.destroyed.connect(
            lambda *_, token=token: self._release_response(token)
        )
        self._pool.start(_ThumbJob(self, photo_id, response))
        return response

    def _release_response(self, token: int) -> None:
        """A motor elpusztította a választ — elengedhetjük a hivatkozást."""
        with self._live_lock:
            self._live_responses.pop(token, None)

    def live_response_count(self) -> int:
        """A nyilvántartott (a motor által még el nem engedett) válaszok
        száma — a #1457 őr-tesztek ebből látják, hogy a nyilvántartás
        ürül, azaz nem szivárog."""
        with self._live_lock:
            return len(self._live_responses)

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
            self.brokenImageDetected.emit(str(photo.id))
            return QImage()
        image = QImage(str(thumb))
        if image.isNull():
            _log.warning("cache-elt thumbnail nem olvasható: %s", thumb)
            self.brokenImageDetected.emit(str(photo.id))
            return image
        if rotate:
            # nem-destruktív ini-forgatás (a cache-elt thumb forgatatlan)
            image = image.transformed(QTransform().rotate(90 * rotate))
        if ops:
            self._memo.put(memo_key, image)
        return image
