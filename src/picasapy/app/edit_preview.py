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

import threading
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage, QImageReader
from PySide6.QtQuick import QQuickImageProvider

from picasapy.ini.filters import FilterOp
from picasapy.render import apply_filters
from picasapy.render.text_overlay import apply_text_overlay

from .histogram_helper import EMPTY_HISTOGRAM, compute_rgb_histogram
# #151/7: a placeholder-szürke egyetlen helyen (thumbnail_provider) definiált
from .thumbnail_provider import PLACEHOLDER_COLOR as _PLACEHOLDER_COLOR
_PLACEHOLDER_SIZE = 16
_MAX_PREVIEW_EDGE = 2560
# LRU-kapacitás (#128): lapozáskor a beginEdit új id-vel regisztrál, endEdit
# nélkül — evikció híján a dekódolt források (~10–30 MB/kép) képenként
# halmozódnának. Két elem elég: az aktuális + az előző kép, így az
# előre-hátra lapozás újradekód nélkül gyors marad, a régebbiek felszabadulnak.
_LRU_CAPACITY = 2


@dataclass(frozen=True)
class TextOverlaySpec:
    """A szöveg-eszköz (#148/#450) élő előnézetéhez kért egyetlen szöveg-réteg.

    A `text=` ini-kulcs NEM a `filters=` láncba tartozik (ld.
    `picasapy.ini.text_overlay` docsztring), ezért a `FilterOp`-lánccal ellentétben
    ezt a hívó (`EditController`) külön adja át a `register()`-nek — a
    renderelés a filters-lánc UTÁN, a végeredményre rajzolja rá.

    A stílus-mezők (`fill_color`/`outline_color`/`outline_thickness`/
    `fill_enabled`/`opacity`, #450) alapértéke a `picasapy.render.text_overlay
    .apply_text_overlay` alapértékeivel egyezik — a régi hívók (ahol a
    hívó nem ad meg stílust) kimenete így változatlan marad."""

    content: str
    x: float
    y: float
    fill_color: tuple[int, int, int] = (255, 255, 255)
    outline_color: tuple[int, int, int] | None = None
    outline_thickness: int = 0
    fill_enabled: bool = True
    opacity: float = 1.0


class EditPreviewProvider(QQuickImageProvider):
    """`image://editpreview/<photo_id>?rev=<n>` — élő szerkesztési előnézet."""

    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Image)
        # LRU-rendezett tárak (#128): a legrégebben használt kép esik ki,
        # ha a kapacitás betelik — lapozásnál így nem szivárog a memória.
        self._images: OrderedDict[str, QImage] = OrderedDict()
        # RGB-hisztogram a hisztogram-dobozhoz (#25): a MEGJELENÍTETT (a
        # filters-lánccal renderelt) előnézetből számol, az _images-szel
        # azonos LRU-életciklussal — nem külön gyorsítótár, csak melléktermék.
        self._histograms: OrderedDict[str, dict] = OrderedDict()
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
        # GPU élő-előnézet (#22): KÜLÖN prefix-gyorsítótár-rekesz a fentitől
        # — a `gpu_prefix_ops` (a finetune2 ELŐTTI lánc) ÁLTALÁBAN eltér a
        # rendes render `ops[:-1]`-jétől (pl. ha még nincs finetune2, a GPU
        # prefix a TELJES láncot jelenti). Ha a kettő UGYANAZT a
        # `_prefix_cache` rekeszt használná, minden `register()`-hívás
        # kölcsönösen kiütné a másik gyorsítótár-találatát (cache-
        # csörgés) — MINDEN szerkesztői művelet (crop/tilt/effekt) duplán
        # futtatná a teljes filter-láncot, nem csak a finetune-húzás
        # alattiak. A gyakori esetben (finetune2 a lánc VÉGén) a két
        # prefix EGYEZIK (`gpu_prefix_ops == ops[:-1]`) — ott a `register()`
        # mindkét rekeszt frissen tartja, nincs dupla munka.
        self._gpu_prefix_cache: (
            tuple[str, tuple[FilterOp, ...], np.ndarray, np.ndarray] | None
        ) = None
        # GPU élő-előnézet (#22): a finetune2 ELŐTTI köztes kép, illetve a
        # jelenlegi finetune2-LUT, 256×1 QImage-ként — a GpuPointFilterPreview.qml
        # ezeket tölti be `sourceItem`/`lutItem`-ként. Ugyanazzal az LRU-
        # életciklussal, mint `_images` (lapozáskor evikció, ld. #128).
        # `None` a `register()` gpu_prefix_ops/gpu_lut paramétere, ha a
        # jelenlegi lánc nem GPU-alkalmas (`EditSession.gpu_finetune_prefix()`)
        # — ilyenkor a hívó (EditController) egyszerűen üres URL-t ad a
        # QML-nek, a réteg nem jelenik meg.
        self._gpu_prefix_images: OrderedDict[str, QImage] = OrderedDict()
        self._gpu_lut_images: OrderedDict[str, QImage] = OrderedDict()
        self._lock = threading.Lock()
        # #514: a `register()` renderelése MÁR NEM csak a GUI-szálon fut (a
        # lassú effekteket az EditController háttérszálra teszi), a
        # dekód-/prefix-gyorsítótárak viszont sima dict/tuple mezők — két
        # egyidejű render egymás alól húzná ki őket. Ez a zár a TELJES
        # `register()`-t sorosítja; a fenti `self._lock` marad a (rövid)
        # kép-/hisztogram-tárolás védelme, és MINDIG ezen BELÜL kerül sorra
        # (egyirányú zár-sorrend, nincs holtpont).
        self._render_lock = threading.RLock()

    def register(
        self,
        photo_id: str,
        path: Path,
        ops: tuple[FilterOp, ...],
        text: TextOverlaySpec | None = None,
        gpu_prefix_ops: tuple[FilterOp, ...] | None = None,
        gpu_lut: np.ndarray | None = None,
    ) -> None:
        """Az aktuálisan szerkesztett fotó renderelése és eltárolása.

        A hívó (GUI) szálán fut — a provider-szálra nem jut Python-munka.
        A `text` (ha van) a `filters=` lánc UTÁN, a végeredményre kerül —
        ez PicasaPy-saját szöveg-eszköz (#148) élő előnézete, a `text=`
        ini-kulcs önálló (nem a lánc része, ld. `TextOverlaySpec`).

        `gpu_prefix_ops`/`gpu_lut` (#22): ha a hívó (`EditController`) a
        jelenlegi lánchoz GPU-alkalmas finetune2-előtagot és LUT-ot ad meg
        (`EditSession.gpu_finetune_prefix()`), ezeket is kirendereljük/
        eltároljuk a `gpuprefix=1`/`gpulut=1` jelzős `requestImage`-
        kéréshez — a köztes kép a `_cached_prefix()`-fel MEGOSZTOTT
        gyorsítótárból jön (nem duplikált munka), ha `ops[:-1] ==
        gpu_prefix_ops` (a szokásos eset: finetune2-húzás alatt).

        #514: a hívó GUI- ÉS háttérszálról is hívhatja (a lassú effektek
        renderelése a szerkesztőben háttérszálra került) — a `_render_lock`
        sorosítja a két utat, hogy a dekód-/prefix-gyorsítótárak ne
        keveredjenek."""
        with self._render_lock:
            self._register_locked(
                photo_id,
                path,
                ops,
                text=text,
                gpu_prefix_ops=gpu_prefix_ops,
                gpu_lut=gpu_lut,
            )

    def _register_locked(
        self,
        photo_id: str,
        path: Path,
        ops: tuple[FilterOp, ...],
        text: TextOverlaySpec | None = None,
        gpu_prefix_ops: tuple[FilterOp, ...] | None = None,
        gpu_lut: np.ndarray | None = None,
    ) -> None:
        """A `register()` törzse — CSAK a `_render_lock` birtokában hívható."""
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
        result_array = self._render_cached(key, source_array, tuple(ops))
        if text is not None and result_array is not None and text.content:
            # a szöveg a filters-lánc UTÁN kerül a képre — a hisztogram (lent)
            # így is a TÉNYLEGESEN megjelenített (szöveggel együtt renderelt)
            # képet tükrözi, a modul-docsztring elve szerint
            result_array = apply_text_overlay(
                result_array,
                text.content,
                text.x,
                text.y,
                color=text.fill_color,
                outline_color=text.outline_color,
                outline_thickness=text.outline_thickness,
                fill_enabled=text.fill_enabled,
                opacity=text.opacity,
            )
        image = _rgb_array_to_qimage(result_array) if result_array is not None else QImage()
        histogram = (
            compute_rgb_histogram(result_array)
            if result_array is not None
            else EMPTY_HISTOGRAM
        )
        gpu_prefix_image = None
        if gpu_prefix_ops is not None:
            prefix_array = self._cached_gpu_prefix(key, source_array, gpu_prefix_ops)
            gpu_prefix_image = _rgb_array_to_qimage(prefix_array)
        gpu_lut_image = _lut_array_to_qimage(gpu_lut) if gpu_lut is not None else None
        with self._lock:
            self._images[key] = image
            self._images.move_to_end(key)
            while len(self._images) > _LRU_CAPACITY:
                self._images.popitem(last=False)
            self._histograms[key] = histogram
            self._histograms.move_to_end(key)
            while len(self._histograms) > _LRU_CAPACITY:
                self._histograms.popitem(last=False)
            self._store_gpu_image(self._gpu_prefix_images, key, gpu_prefix_image)
            self._store_gpu_image(self._gpu_lut_images, key, gpu_lut_image)

    def update_gpu_lut(self, photo_id: str, lut: np.ndarray) -> None:
        """A finetune2-LUT (#22) frissítése ÖNMAGÁBAN, a teljes `register()`
        (dekód + filter-lánc + hisztogram) megkerülésével — ezt hívja a GPU
        élő-előnézet húzás közben (`EditController.previewFinetuneGpu`),
        hogy a húzás olcsó maradjon: csak a 256×1 LUT-kép cserélődik, a
        forráskép/prefix érintetlen."""
        key = str(photo_id)
        with self._lock:
            self._store_gpu_image(self._gpu_lut_images, key, _lut_array_to_qimage(lut))

    def unregister(self, photo_id: str) -> None:
        """A fotó eltávolítása (szerkesztés vége)."""
        key = str(photo_id)
        self._sources.pop(key, None)
        if self._prefix_cache is not None and self._prefix_cache[0] == key:
            self._prefix_cache = None
        if self._gpu_prefix_cache is not None and self._gpu_prefix_cache[0] == key:
            self._gpu_prefix_cache = None
        with self._lock:
            self._images.pop(key, None)
            self._histograms.pop(key, None)
            self._gpu_prefix_images.pop(key, None)
            self._gpu_lut_images.pop(key, None)

    def histogram_for(self, photo_id: str) -> dict:
        """Az utoljára renderelt előnézet RGB-hisztogramja (#25), vagy üres
        hisztogram, ha a fotó nincs (már) regisztrálva."""
        with self._lock:
            return self._histograms.get(str(photo_id), EMPTY_HISTOGRAM)

    @staticmethod
    def _store_gpu_image(
        store: OrderedDict[str, QImage], key: str, image: QImage | None
    ) -> None:
        """GPU-előnézeti kép (LRU-tárolt) frissítése — `image is None` esetén
        a bejegyzés törlődik (a lánc jelenleg nem GPU-alkalmas, #22)."""
        if image is None:
            store.pop(key, None)
            return
        store[key] = image
        store.move_to_end(key)
        while len(store) > _LRU_CAPACITY:
            store.popitem(last=False)

    # -- lánc-prefix gyorsítótár (#140) ------------------------------------

    def _render_cached(
        self,
        key: str,
        source_array: np.ndarray | None,
        ops: tuple[FilterOp, ...],
    ) -> np.ndarray | None:
        """Renderelés lánc-prefix gyorsítótárral: interakció közben (azonos
        prefix, csak az utolsó op paramétere változik) csak az utolsó op fut.

        A visszaadott RGB-tömb a hisztogram (#25) és a QImage-konverzió közös
        forrása — így a hisztogram mindig a TÉNYLEGESEN megjelenített képet
        tükrözi, nem egy külön újraszámolt változatot.

        #301: hibás/idegen lánc-bejegyzésnél az apply_filters saját maga esik
        vissza a szűretlen köztes eredményre (kivétel nem szökik ki innen),
        a #73-elv (részleges előnézet a placeholder helyett) így is teljesül."""
        if source_array is None:
            return None
        if not ops:
            return source_array
        prefix_array = self._cached_prefix(key, source_array, ops[:-1])
        result_array, _skipped = apply_filters(prefix_array, ops[-1:])
        return result_array

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

    def _cached_gpu_prefix(
        self,
        key: str,
        source_array: np.ndarray,
        prefix_ops: tuple[FilterOp, ...],
    ) -> np.ndarray:
        """A GPU-előnézet (#22) prefix-je, KÜLÖN gyorsítótár-rekeszben.

        Ugyanaz a találat-logika, mint `_cached_prefix`-nél, de saját
        `_gpu_prefix_cache` rekesszel — ld. a rekesz mellé írt docsztringet
        a cache-csörgés elkerüléséről. A gyakori esetben (finetune2 a lánc
        VÉGén, `prefix_ops == ops[:-1]`) ez a hívás olcsó: a tömb-tartalom
        MEGEGYEZIK a `_cached_prefix`-ben az imént kiszámolttal, csak a
        referencia más — az `apply_filters` itt is lefut, de a KÖVETKEZŐ,
        AZONOS prefixű hívásnál már ez a rekesz is talál."""
        cached = self._gpu_prefix_cache
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
        self._gpu_prefix_cache = (key, prefix_ops, source_array, prefix_array)
        return prefix_array

    def requestImage(self, photo_id, size, requested_size):
        # az URL-ben ?rev=<szám> cache-buster jöhet — az id az első rész.
        # A `gpuprefix=1`/`gpulut=1` jelző (#22) a GPU-előnézeti köztes
        # képet/LUT-ot kéri a rendes (teljes lánccal renderelt) kép helyett
        # — ezekre a placeholder-fallback NEM vonatkozik: null képnél a
        # QML-oldali GpuPointFilterPreview egyszerűen nem kap forrást, a
        # hívó (EditController) pedig üres URL-t ad, amíg nincs friss adat.
        key = photo_id.split("?")[0]
        is_gpu_prefix = "gpuprefix=1" in photo_id
        is_gpu_lut = "gpulut=1" in photo_id
        with self._lock:
            if is_gpu_prefix:
                image = self._gpu_prefix_images.get(key, QImage())
            elif is_gpu_lut:
                image = self._gpu_lut_images.get(key, QImage())
            else:
                image = self._images.get(key, QImage())
        if image.isNull() and not (is_gpu_prefix or is_gpu_lut):
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


def _lut_array_to_qimage(lut: np.ndarray) -> QImage:
    """`(256, 3)` uint8 finetune2-LUT → 256×1 RGB8 `QImage` (#22) — a
    `GpuPointFilterPreview.qml` ezt tölti be `lutItem`-ként és mintavételezi
    csatornánként a shaderben (ld. `gpu_point_pipeline` modul-docsztring)."""
    return _rgb_array_to_qimage(lut[np.newaxis, :, :])
