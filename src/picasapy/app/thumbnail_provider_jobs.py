"""A bélyegkép-kérések válasz- és pool-feladatai."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

import shiboken6
from PySide6.QtCore import QRunnable
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageResponse, QQuickTextureFactory

from .thumbnail_provider_constants import PLACEHOLDER_COLOR

if TYPE_CHECKING:
    from .thumbnail_provider import ThumbnailProvider

_log = logging.getLogger("picasapy.app.thumbnail_provider")


class _ThumbResponse(QQuickImageResponse):
    """Egy aszinkron thumbnail-kérés eredménye.

    A képet a pool-szál készíti el és adja át (`_finish`), és a `finished`
    jelzés is ONNAN megy ki.

    ⚠️ Itt korábban az állt, hogy a kibocsátás a válasz saját szálára van
    átütemezve, mert különben a motor „a kibocsátás belsejében" törölné az
    objektumot. **Ez a modell HAMIS** — független átnézés mutatta ki, a Qt
    forrására hivatkozva: a Qt 6.8 a `finished`-et egy
    `ReaderThreadExecutionEnforcer`-hez köti, tehát a más szálról érkező
    jelzés magától queued lesz, és a `textureFactory()` meg a
    `deleteLater()` az image-reader szálon fut. A pool-szálról való
    kibocsátás **támogatott** működés; a hivatalos Qt-példa is így csinálja.

    Az átütemezést ezért visszavontuk (#1457) — nem azért, mert veszélyes,
    hanem mert fölösleges volt, és időzítést változtatott egy olyan
    hibakeresés közben, ahol ez félrevisz.

    A zár, amit itt tartunk, NEM a `QImage` hivatkozásszámlálóját védi (az
    atomikus), hanem a `cancel` és a befejezés **állapotát** tartja
    konzisztensen: lemondott válaszba ne írjunk képet, és a `_done` jelző
    a képpel együtt álljon be.

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


class _PrefetchJob(QRunnable):
    """Egy alacsony prioritású bélyegkép a cache felmelegítéséhez."""

    def __init__(self, provider: "ThumbnailProvider"):
        super().__init__()
        self._provider = provider

    def run(self) -> None:
        self._provider._run_prefetch_job()


def _placeholder() -> QImage:
    image = QImage(16, 16, QImage.Format.Format_RGB32)
    image.fill(PLACEHOLDER_COLOR)
    return image
