"""image://thumbs/<id> képszolgáltató a QML-rácsnak.

#144 óta ASZINKRON provider: a Qt alapból egyetlen image-loader szálon
hívná a szinkron providert, itt viszont saját QThreadPool (max 4 szál)
dolgozik — az OpenCV a dekódolás alatt elengedi a GIL-t, így RPi5-ön a
4 mag ténylegesen párhuzamosan generál. A controller regisztrálja nála az
aktuális fotókat; az albumon kívüli arc-csempék azonosítóját a szolgáltató
szükség esetén az indexből oldja fel.

A cache, a pool-feladatok, a kérés-ütemezés, a regiszter és a render-mag
külön, belső modulokban él. A nyilvános importútvonal és az itt importált
régi nevek változatlanul használhatók.

Szálkezelés (#53 GIL↔Qt deadlock-osztály): a pool-szálakon KIZÁRÓLAG
érték-típusú Qt-objektum (QImage) készül, QObject nem; a kész képet a
QQuickImageResponse.finished jelzi. A busy-számláló jelzése queued
kézbesítéssel jut a főszálra.

Élettartam (#1457): a jelzés KIBOCSÁTÁSA szálbiztos, de ez nem ugyanaz,
mint élettartam-biztos — egy már megsemmisített válaszon a `finished`
kibocsátása use-after-free, és a folyamat összeomlik (mért SIGSEGV).
A válasz C++ oldalát a QML-motor kezeli: a saját olvasószálán hozza
létre, és ott is semmisíti meg, amikor végzett vele. A PySide viszont
a Python-oldali referenciaszámot is figyeli — ezért a provider maga tart
erős hivatkozást minden élő válaszra, és csak a `destroyed` jelzésre
engedi el.

Hibatűrés (#66): a renderből kivétel SOHA nem szökhet ki — hiba esetén
placeholder megy vissza, a részletek a logba.
"""

from __future__ import annotations

import itertools
import logging
import os
import threading
import time
import zlib
from collections import deque
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtCore import QThreadPool, Signal
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickAsyncImageProvider

from picasapy.cvimage import read_image_bytes
from picasapy.edit.session import EditSession
from picasapy.index import PhotoRecord
from picasapy.ini import PhotoCropReader
from picasapy.ini.filters import serialize_filters
from picasapy.thumbs import ThumbnailCache
from .arc_nagyitas_forras import arc_eredetibol
from .thumbnail_provider_constants import (
    _MAX_RENDER_THREADS,
    _OPS_CACHE_CAPACITY,
)
from .thumbnail_provider_constants import PLACEHOLDER_COLOR as PLACEHOLDER_COLOR
from .thumbnail_provider_constants import (
    _FILTERED_MEMO_CAPACITY as _FILTERED_MEMO_CAPACITY,
    _PREFETCH_QUEUE_CAPACITY as _PREFETCH_QUEUE_CAPACITY,
    _PREFETCH_THUMB_PRIORITY as _PREFETCH_THUMB_PRIORITY,
    _VISIBLE_THUMB_PRIORITY as _VISIBLE_THUMB_PRIORITY,
)
from .thumbnail_provider_cache import _FilteredThumbMemo  # noqa: F401
from .thumbnail_provider_jobs import (
    _PrefetchJob,  # noqa: F401
    _ThumbJob,  # noqa: F401
    _ThumbResponse,  # noqa: F401
    _placeholder,  # noqa: F401
)
from .thumbnail_provider_registry import (
    _photo_for_render as _registry_photo_for_render,
    _photo_record as _registry_photo_record,
    _register_additional_photos,
    _register_photos,
    _unregister_additional_photos,
)
from .thumbnail_provider_requests import (
    _live_response_count,
    _prefetch_images,
    _release_response,
    _request_image_response,
    _run_prefetch_job,
)
from .thumbnail_provider_render import (
    _arc_forras as _render_arc_forras,
    _render as _render_thumbnail,
    _render_szinten as _render_szinten_impl,
    _request_image as _request_image_impl,
)
from .worker_thread import register_pool_owner

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


#: A frissen írt cache-fájl olvasásának újrapróbái (#5553).
_CACHE_OLVASAS_VARAKOZASOK = (0.05, 0.1, 0.2)
_alszik = time.sleep


def _olvass_cache_kepet(thumb: Path) -> QImage:
    """A cache-elt bélyegkép a Python fájl-API-n át beolvasva (#5542),
    átmeneti hibánál rövid várakozással újrapróbálva (#5553)."""
    for varakozas in (*_CACHE_OLVASAS_VARAKOZASOK, None):
        payload = read_image_bytes(thumb)
        if payload is not None:
            image = QImage.fromData(payload.tobytes())
            if not image.isNull():
                return image
        if varakozas is not None:
            _alszik(varakozas)
    return QImage()


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

    def __init__(
        self,
        cache: ThumbnailCache,
        max_threads: int | None = None,
        index_path: str | Path | None = None,
    ):
        super().__init__()
        self._cache = cache
        self._index_path = Path(index_path) if index_path is not None else None
        self._registry: dict[str, PhotoRecord] = {}
        self._registry_lock = threading.Lock()
        # #142: lustán értelmezett filters-láncok — kulcs a nyers
        # filters= sztring, érték az (ops, crc32) pár
        self._ops_cache: dict[str, tuple[tuple, int]] = {}
        self._ops_lock = threading.Lock()
        # A crop nincs az indexben: az igazságforrás a képszekció ini-je.
        # A közös olvasó dokumentum-szinten gyorsítótáraz, és a fájl
        # változásakor automatikusan újraolvas.
        self._crop_reader = PhotoCropReader()
        self._active = 0
        self._active_lock = threading.Lock()
        self._memo = _FilteredThumbMemo()
        # Egyetlen előtöltő dolgozik egyszerre. Így a háttérmunka nem tudja
        # elfoglalni a látható cellák elől a teljes QThreadPool-t. Az újabb
        # görgetési tartományok a sor elejére kerülnek, a régi sor vége
        # korlátos és eldobható.
        self._prefetch_lock = threading.Lock()
        self._prefetch_queue: deque[str] = deque()
        self._prefetch_pending: set[str] = set()
        self._prefetch_scheduled = False
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
        return _register_photos(self, photos)

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
            (`dedup_controller.DEDUP_THUMB_ID_BASE`, #298);
          * `-8_000_000_000_000_000` körül: parancssoros gyorsnézegető
            (#5762; a kiszámítható QML-számábrázolási tartományban).
        Új hívó ide vegyen fel magának új sávot."""
        return _register_additional_photos(self, photos)

    def photo_record(self, photo_id: str) -> PhotoRecord | None:
        """A regisztrált fotó rekordja (#338 effekt-bélyegképek): a
        szerkesztőpanel effekt-gombjainak bélyegkép-providere (
        `effect_thumbnails.py`) ebből olvassa ki az útvonalat — nem kell
        neki saját, párhuzamos fotó-regisztrációt vezetnie."""
        return _registry_photo_record(self, photo_id)

    def unregister_additional_photos(self, ids: tuple[str, ...]) -> None:
        """A `register_additional_photos`-szal felvett bejegyzések
        eltávolítása (pl. új szkennelés előtt vagy a dialógus zárásakor) —
        a valódi könyvtár bejegyzéseit nem érinti."""
        return _unregister_additional_photos(self, ids)

    def _photo_for_render(self, photo_id: str) -> PhotoRecord | None:
        """Az album-regisztrációból, majd szükség esetén az indexből old fel.

        A `requestImageResponse` pool-szálán fut, ezért az indexkapcsolatot
        helyben nyitja meg és zárja le; SQLite-kapcsolatot nem oszt meg a Qt
        szálai között. Az indexből talált rekordot immutábilis szótárcserével
        jegyzi meg a következő kéréshez.
        """
        return _registry_photo_for_render(self, photo_id)

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

    def clear_cache(self) -> int:
        """A bélyegkép-tár ürítése lemezen ÉS memóriában (#598).

        A memóriabeli rekeszeket és a lánc-gyorstárat is törli. A
        `disposepreviews` kilépéskori szabályánál is ezt a meglévő utat
        használjuk (#5897)."""
        freed = self._cache.clear()
        self._memo.clear()
        with self._ops_lock:
            self._ops_cache.clear()
        return freed

    def level_for(self, cella_px: int) -> int:
        """A cellamérethez tartozó bélyegkép-szint (#598) — a tár dönti el."""
        return self._cache.level_for(cella_px)

    @property
    def top_level(self) -> int:
        """A tár legnagyobb szintje (#598): a rács maximuma × a képernyő DPR-je."""
        return self._cache.levels[-1]

    def requestImageResponse(self, photo_id: str, requested_size) -> _ThumbResponse:
        """Aszinkron belépési pont (a Qt a saját olvasószálán hívja): a
        munka a poolba kerül, a válasz azonnal visszamegy.

        A válasz #1457 óta bekerül a provider nyilvántartásába is, és csak
        a motor általi megszüntetéskor (`destroyed`) kerül ki onnan."""
        return _request_image_response(self, photo_id, requested_size)

    def prefetch_images(self, photo_ids: Iterable[str]) -> int:
        """A megadott bélyegkép-azonosítók alacsony prioritású előtöltése.

        A render-mag a már meglévő `ThumbnailCache`-t és a szűrt képek
        memóriatárát használja. A sorosított futás egy pool-helyet legfeljebb
        egy kép idejére foglal; a látható kérések közben a Qt magasabb
        prioritással előzik meg a sorban álló előtöltéseket.
        """
        return _prefetch_images(self, photo_ids)

    def _run_prefetch_job(self) -> None:
        """Egy cache-felmelegítő munka; a következő csak a befejezés után indul."""
        return _run_prefetch_job(self)

    def _release_response(self, token: int) -> None:
        """A motor elpusztította a választ — elengedhetjük a hivatkozást."""
        return _release_response(self, token)

    def live_response_count(self) -> int:
        """A nyilvántartott (a motor által még el nem engedett) válaszok
        száma — a #1457 őr-tesztek ebből látják, hogy a nyilvántartás
        ürül, azaz nem szivárog."""
        return _live_response_count(self)

    def wait_for_done(self, msecs: int = 10_000) -> bool:
        """Minden folyamatban lévő pool-feladat bevárása (tesztekhez)."""
        return self._pool.waitForDone(msecs)

    def requestImage(self, photo_id, size, requested_size):
        """Szinkron render-mag (a pool-feladat és a tesztek hívják) —
        a korábbi szinkron provider változatlan szerződésével."""
        return _request_image_impl(self, photo_id, size, requested_size)

    def _arc_forras(self, photo_id: str, image: QImage, arc: tuple) -> QImage:
        """Az arc-vágás forrásképe (#2187): akkora, hogy a kivágott négyzet
        oldala elérje a kért cellát (`&sz=`, cimke nélkül a felső szint).

        Sorrend, a legolcsóbbtól: a már kész `image`, ha elég; a tár egy
        nagyobb szintje; az eredeti fájl (`arc_eredetibol`). Szerkesztett
        képnél az eredeti fájl a `filters=` láncot nem hordozza, ezért ott a
        felső szint a határ."""
        return _render_arc_forras(self, photo_id, image, arc, arc_eredetibol)

    def _render_szinten(self, photo_id: str, szint: int) -> QImage | None:
        """A `_render` a megadott szinten (az URL `&sz=` cimkéjét cseréljük);
        `None`, ha nem készült el."""
        return _render_szinten_impl(self, photo_id, szint)

    def _render(self, photo_id: str) -> QImage:
        """A kész (szerkesztett, forgatott) thumbnail; null-QImage, ha a
        forrás nem dekódolható — a hívó ebből csinál placeholdert."""
        return _render_thumbnail(self, photo_id, _olvass_cache_kepet)
