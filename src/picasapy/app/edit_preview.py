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
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickImageProvider

from picasapy.ini import PhotoCropReader
from picasapy.ini.filters import FilterOp
from picasapy.render import apply_filters, normalize_crop_ops
from picasapy.render.chain_geometry import TartalomHely
from picasapy.render.display_modes import (
    apply_display_mode,
    display_mode_changes_pixels,
)
from picasapy.render.elonezeti_arany import elonezeti_arany
from picasapy.render.op_geometry import LancHelyzet
from picasapy.render.registry import chain_flags
from picasapy.render.text_fonts import DEFAULT_FAMILY
from picasapy.render.text_overlay import apply_text_overlay
from picasapy.scanner import PICASA_INI_NAME

from .edit_preview_cache import EditPreviewCacheMixin, _LRU_CAPACITY
from .edit_preview_redeye import (
    EditPreviewRedeyeMixin,
    _OUTLINE_MAX_PX as _OUTLINE_MAX_PX,
    _REDEYE_DETECTION_SPLIT as _REDEYE_DETECTION_SPLIT,
    _normalize_redeye_ops as _normalize_redeye_ops,
    _outline_px as _outline_px,
    _post_ops_geometry as _post_ops_geometry,
    count_redeye_spots as count_redeye_spots,
    detect_eye_circles as detect_eye_circles,
)
from .edit_preview_source import (
    _MAX_PREVIEW_EDGE as _MAX_PREVIEW_EDGE,
    _decode_source as _decode_source,
    _elonezeti_arany as _elonezeti_arany,
    _lut_array_to_qimage as _lut_array_to_qimage,
    _megjelenitendo as _megjelenitendo,
    _nyers_forras as _nyers_forras,
    _qimage_to_rgb_array as _qimage_to_rgb_array,
    _rgb_array_to_qimage as _rgb_array_to_qimage,
    _srgb_be as _srgb_be,
    _teljes_hosszabb_el as _teljes_hosszabb_el,
)
from .histogram_helper import EMPTY_HISTOGRAM, compute_rgb_histogram

# #151/7: a placeholder-szürke egyetlen helyen (thumbnail_provider) definiált
from .thumbnail_provider import PLACEHOLDER_COLOR as _PLACEHOLDER_COLOR

_PLACEHOLDER_SIZE = 16


@dataclass(frozen=True)
class TextOverlaySpec:
    """A szöveg-eszköz (#148/#450) egy szövegrétegének renderelési adatai.

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
    #: #2271: `[0, 1]` folytonos, az eredeti mértékegységében. A
    #: RAJZOLÁSHOZ képpontra váltjuk (`_OUTLINE_MAX_PX`) — az a leképezés
    #: KÖZELÍTÉS, mert az eredetiben nincs megmérve; a TÁROLT érték
    #: viszont mért, és átszámítás nélkül megy a `text=` 5. mezőjébe.
    outline_thickness: float = 0.0
    fill_enabled: bool = True
    opacity: float = 1.0
    #: #450 (2. lépcső): tipográfia — betűcsalád, méret-szorzó, stílusok és
    #: a sorok igazítása. Az alapértékek a rajzolóéval egyeznek, ezért a
    #: régi hívók kimenete változatlan marad.
    font_family: str = DEFAULT_FAMILY
    font_scale: float = 1.0
    #: #2287: a választott listaérték (8…96); ebből és a kép magasságából
    #: számol a rajzoló — a `font_scale` csak tartalék.
    font_size_pt: float | None = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    align: str = "left"


class EditPreviewProvider(EditPreviewCacheMixin, EditPreviewRedeyeMixin, QQuickImageProvider):
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
        #: #3166: az utolsó render KERET-elhelyezése fotónként — a szerkesztő
        #: átfedő rétegei (vágás-téglalap, arckeretek) ezen át kapják a
        #: helyüket. `None`-t NEM tárolunk: a keret nélküli lánc TÖRLI a
        #: bejegyzést, különben egy visszavont keret eltolva hagyná a
        #: rétegeket.
        self._placements: OrderedDict[str, TartalomHely] = OrderedDict()
        # dekódolt forrás gyorsítótár (#72): élő csúszka-húzásnál (pl. tilt)
        # a register() gyakran hívódik ugyanarra a fotóra, csak a szűrő-
        # lánc változik — a lemezes dekódot nem kell minden alkalommal
        # megismételni, csak a filter-lánc újraszámolását.
        self._sources: OrderedDict[str, tuple[Path, float | None, np.ndarray | None]] = (
            OrderedDict()
        )
        # lánc-prefix gyorsítótár (#140): élő csúszka-húzásnál csak az UTOLSÓ
        # op paramétere változik — az utolsó op ELŐTTI köztes eredményt
        # egyetlen rekeszben tároljuk (kulcs, prefix-lánc, forrás-referencia,
        # prefix-kép, lánc-helyzet, alfaállapot), így interakció közben csak az utolsó op
        # fut újra. A lánc-helyzet (#3229) azért kell bele, mert a folytatás
        # koordinátái az EREDETI képre vonatkoznak. Az 5. mező a gyors
        # élő-előnézet jelzője (#3846), a 6. az alfaállapot (#5299): a húzás
        # közbeni gyors Kiegyenesítés képe nem szolgálja ki a natív renderelést.
        self._prefix_cache: (
            tuple[
                str,
                tuple[FilterOp, ...],
                np.ndarray,
                np.ndarray,
                LancHelyzet,
                bool,
                int,
            ]
            | None
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
            tuple[str, tuple[FilterOp, ...], np.ndarray, np.ndarray, bool] | None
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
        # #546: EGYETLEN zár, és csak a (rövid) kép-/hisztogram-tárolásra.
        # A dekód-/prefix-gyorsítótárakat (`_sources`, `_prefix_cache`,
        # `_gpu_prefix_cache`) KIZÁRÓLAG a GUI-szál írja: a háttérszálas
        # render (`shared_cache=False`) lokálisan dekódol és renderel.
        # Így nincs olyan zár, amin a GUI-szál render-hosszan állhatna —
        # a #514 első változata épp ezt hozta vissza egy másik ajtón.
        self._lock = threading.Lock()
        # Megjelenítési mód (#1576): KÉPERNYŐRE ható átalakító, a `Nézet ▸
        # Megjelenítési mód` almenüből (#1575). SZÁNDÉKOSAN nem a
        # `register()`-ben, tárolás előtt alkalmazzuk, hanem a
        # `requestImage()`-ben, a tárolt képet ÉRINTETLENÜL hagyva:
        #
        # * a `_images`/`_prefix_cache`/`_sources` rekeszek tiszták maradnak,
        #   így a mód kikapcsolása után a kép BÁJTRA az eredeti (a beégetett
        #   jelölés különben ott ragadna a gyorsítótárban),
        # * a hisztogram (#25) és a pipetta (#464) a VALÓDI képet méri, nem
        #   a képernyő figyelmeztető színét,
        # * a mód váltásához nem kell újrarenderelni (dekód + filter-lánc),
        #   elég a QML-lel újrakéretni a képet.
        #
        # A `requestImage` a Qt kép-betöltő szálán fut, ezért az érték a
        # meglévő (rövid tartású) `_lock` alatt cserélődik és olvasódik.
        self._display_mode = ""
        # #1725: a `Színkezelés használata` — a forrás dekódolására hat
        self._color_management = False
        # A crop kulcs a `.picasa.ini`-ben van, nem az indexrekordban. Az
        # olvasó fájlváltozáskor frissül, de a csúszka-húzások nem parse-olják
        # újra minden alkalommal a teljes dokumentumot.
        self._crop_reader = PhotoCropReader()

    def set_color_management(self, enabled: bool) -> None:
        """A `Színkezelés használata` állapota (#1725) — a FORRÁSRA hat.

        A megjelenítési módtól eltérően ez a dekódolt forráskép tartalmát
        változtatja, ezért a forrás- és a lánc-prefix gyorsítótárat is ki
        kell üríteni: különben a váltás után a régi, át nem alakított tömb
        maradna bent. (Az eredeti ugyanígy dobja el az előnézeti állapotot,
        `0x005c966a`.)"""
        enabled = bool(enabled)
        with self._lock:
            if enabled == self._color_management:
                return
            self._color_management = enabled
            self._sources.clear()
            self._prefix_cache = None

    @property
    def color_management(self) -> bool:
        """Érvényesül-e a beágyazott ICC-profil a dekódolt forráson."""
        with self._lock:
            return self._color_management

    def set_display_mode(self, mode: str) -> None:
        """A megjelenítési mód beállítása (#1576) — csak a KÉPERNYŐRE hat.

        A hívó a `wire_display_mode()` (ld.
        `picasapy.app.display_mode_controller`); a mentett/exportált képet
        ez az érték soha nem érinti."""
        with self._lock:
            self._display_mode = str(mode or "")

    @property
    def display_mode(self) -> str:
        """Az érvényes megjelenítési mód azonosítója (üres: nincs hatás)."""
        with self._lock:
            return self._display_mode

    def register(
        self,
        photo_id: str,
        path: Path,
        ops: tuple[FilterOp, ...],
        text: TextOverlaySpec | tuple[TextOverlaySpec, ...] | None = None,
        gpu_prefix_ops: tuple[FilterOp, ...] | None = None,
        gpu_lut: np.ndarray | None = None,
        shared_cache: bool = True,
        is_current: Callable[[], bool] | None = None,
        paint_strokes: tuple = (),
        crop: str | None = None,
        crop_ini_readable: bool | None = None,
    ) -> None:
        """Az aktuálisan szerkesztett fotó renderelése és eltárolása.

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

        #546: a hívó GUI- ÉS háttérszálról is hívhatja. A háttér-út
        `shared_cache=False`-szal jön: lokálisan dekódol/renderel, a
        megosztott gyorsítótárakhoz hozzá sem nyúl. Az `is_current`
        visszahívás (ha van) közvetlenül a TÁROLÁS előtt fut le, a `_lock`
        alatt — az időközben túlhaladott render így nem írhatja felül a
        frissebb képet."""
        self._register_impl(
            photo_id,
            path,
            ops,
            text=text,
            gpu_prefix_ops=gpu_prefix_ops,
            gpu_lut=gpu_lut,
            shared_cache=shared_cache,
            paint_strokes=paint_strokes,
            is_current=is_current,
            crop=crop,
            crop_ini_readable=crop_ini_readable,
        )

    def _register_impl(
        self,
        photo_id: str,
        path: Path,
        ops: tuple[FilterOp, ...],
        text: TextOverlaySpec | tuple[TextOverlaySpec, ...] | None = None,
        gpu_prefix_ops: tuple[FilterOp, ...] | None = None,
        gpu_lut: np.ndarray | None = None,
        shared_cache: bool = True,
        is_current: Callable[[], bool] | None = None,
        paint_strokes: tuple = (),
        crop: str | None = None,
        crop_ini_readable: bool | None = None,
    ) -> None:
        """A `register()` törzse (#546)."""
        key = str(photo_id)
        path = Path(path)
        if crop_ini_readable is None:
            crop, crop_ini_readable = self._crop_reader.read(
                path.parent / PICASA_INI_NAME, path.name
            )
        ops = normalize_crop_ops(
            tuple(ops),
            crop,
            crop_ini_readable=crop_ini_readable,
            warning_key=str(path),
        )
        if gpu_prefix_ops is not None:
            gpu_prefix_ops = normalize_crop_ops(
                tuple(gpu_prefix_ops),
                crop,
                crop_ini_readable=crop_ini_readable,
                warning_key=str(path),
            )
        try:
            mtime = path.stat().st_mtime
        except OSError:
            # #548: NAS-on a fájl az ellenőrzés és a `stat()` közt eltűnhet
            # (TOCTOU), és a jogosultsági hiba is ide fut. A `None` azt
            # jelenti: „nincs érvényes időbélyeg" — a forrás-gyorsítótár
            # ilyenkor egyszerűen nem talál, és újra dekódolunk (a dekóder
            # a hiányzó fájlra `None`-nal, azaz helyőrzővel felel).
            mtime = None
        #: #819: a lánc sáv-jelzői. A `fullres` szűrők csak teljes
        #: felbontáson helyesek, ezért náluk a dekód korlátja elmarad.
        teljes_felbontas, _lassu, _ujrameretez = chain_flags([op.name for op in ops])
        source_array = self._resolve_source(
            key, path, mtime, shared_cache, full_res=teljes_felbontas
        )
        # #3377: a lánc a kicsinyítés arányával fut — a keret vastagsága így
        # a mentett képpel arányos marad (az eredeti `imageWidth /
        # fullResImageWidth` tényezője).
        with elonezeti_arany(_elonezeti_arany(path, mtime, source_array, teljes_felbontas)):
            result_array, elhelyezes = self._futtasd_a_lancot(
                key, source_array, ops, shared_cache, paint_strokes
            )
        text_specs = (text,) if isinstance(text, TextOverlaySpec) else (text or ())
        if result_array is not None:
            # a szövegek a filters-lánc UTÁN, fájlbeli sorrendben kerülnek
            # a képre — a hisztogram így a tényleges előnézetet tükrözi.
            for text_spec in text_specs:
                if not text_spec.content:
                    continue
                result_array = apply_text_overlay(
                    result_array,
                    text_spec.content,
                    text_spec.x,
                    text_spec.y,
                    color=text_spec.fill_color,
                    outline_color=text_spec.outline_color,
                    outline_thickness=_outline_px(text_spec.outline_thickness),
                    fill_enabled=text_spec.fill_enabled,
                    opacity=text_spec.opacity,
                    font_family=text_spec.font_family,
                    font_scale=text_spec.font_scale,
                    font_size_pt=text_spec.font_size_pt,
                    bold=text_spec.bold,
                    italic=text_spec.italic,
                    underline=text_spec.underline,
                    align=text_spec.align,
                )
        image = (
            _rgb_array_to_qimage(_megjelenitendo(result_array, teljes_felbontas))
            if result_array is not None
            else QImage()
        )
        histogram = (
            compute_rgb_histogram(result_array) if result_array is not None else EMPTY_HISTOGRAM
        )
        gpu_prefix_image = None
        if gpu_prefix_ops is not None and source_array is not None:
            if shared_cache:
                prefix_array = self._cached_gpu_prefix(key, source_array, gpu_prefix_ops)
            elif gpu_prefix_ops:
                prefix_array, _skipped = apply_filters(source_array, gpu_prefix_ops)
            else:
                prefix_array = source_array
            gpu_prefix_image = _rgb_array_to_qimage(prefix_array)
        gpu_lut_image = _lut_array_to_qimage(gpu_lut) if gpu_lut is not None else None
        with self._lock:
            # #546: az elavultság-ellenőrzés ITT, a tárolással EGY zár alatt
            # — a régebbi render így tárolás ELŐTT bukik el, nem csak az
            # értesítésnél (különben felülírná a frissebb képet).
            if is_current is not None and not is_current():
                return
            self._images[key] = image
            self._images.move_to_end(key)
            while len(self._images) > _LRU_CAPACITY:
                self._images.popitem(last=False)
            self._histograms[key] = histogram
            self._histograms.move_to_end(key)
            while len(self._histograms) > _LRU_CAPACITY:
                self._histograms.popitem(last=False)
            if elhelyezes is None:
                self._placements.pop(key, None)
            else:
                self._placements[key] = elhelyezes
                self._placements.move_to_end(key)
                while len(self._placements) > _LRU_CAPACITY:
                    self._placements.popitem(last=False)
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

    def gpu_preview_ready(self, photo_id: str) -> bool:
        """Van-e mindkét, nem-null kép a GPU-előnézeti kéréshez?

        A QML csak akkor kaphat `gpuprefix`/`gpulut` URL-t, ha a provider már
        ténylegesen ki tudja szolgálni őket. A teljes `register()` a két
        képet ugyanazon zár alatt teszi a cache-be, ezért a lekérdezés sem
        láthat félkész állapotot.
        """
        key = str(photo_id)
        with self._lock:
            prefix = self._gpu_prefix_images.get(key)
            lut = self._gpu_lut_images.get(key)
            return (
                prefix is not None and not prefix.isNull() and lut is not None and not lut.isNull()
            )

    def unregister(self, photo_id: str) -> None:
        """A fotó eltávolítása (szerkesztés vége).

        #546: a `_sources`/`_prefix_cache`/`_gpu_prefix_cache` mezőket csak
        a GUI-szál írja (a háttér-render `shared_cache=False`-szal fut),
        ezért ez a metódus is CSAK a GUI-szálról hívható — a hívó
        (`EditController.endEdit`) a `_preview_job` léptetésével gondoskodik
        arról, hogy a futó háttér-render ne regisztrálhassa vissza a
        lezárt fotót."""
        key = str(photo_id)
        self._sources.pop(key, None)
        if self._prefix_cache is not None and self._prefix_cache[0] == key:
            self._prefix_cache = None
        if self._gpu_prefix_cache is not None and self._gpu_prefix_cache[0] == key:
            self._gpu_prefix_cache = None
        with self._lock:
            self._images.pop(key, None)
            self._histograms.pop(key, None)
            self._placements.pop(key, None)
            self._gpu_prefix_images.pop(key, None)
            self._gpu_lut_images.pop(key, None)

    def kepet_elenged(self, photo_id: str) -> None:
        """A fotó RENDERELT képeinek elengedése, a dekódolt forrás marad.

        #3773: a képtár két helyes, és a kettős nézet két vezérlője közösen
        tölti — a másik fotóra lépő vezérlő régi képe különben a másik
        vezérlő élő képét szorítaná ki. A forrás (`_sources`) és a
        lánc-prefix gyorsítótár érintetlen: a visszalapozás így sem dekódol
        újra (#128)."""
        key = str(photo_id)
        with self._lock:
            self._images.pop(key, None)
            self._histograms.pop(key, None)
            self._placements.pop(key, None)
            self._gpu_prefix_images.pop(key, None)
            self._gpu_lut_images.pop(key, None)

    def sample_color(self, photo_id: str, nx: float, ny: float):
        """A MEGJELENÍTETT előnézet színe a (nx, ny) normált ponton (#464).

        A pipetta („semleges szín") ezt kérdezi: a felhasználó a képre
        kattint, a hívó a kattintás helyét normált [0..1] koordinátaként
        adja át. `None`, ha a fotó nincs (már) regisztrálva, vagy a pont a
        képen kívülre esik.
        """
        with self._lock:
            image = self._images.get(str(photo_id))
        if image is None or image.isNull():
            return None
        x = int(round(nx * (image.width() - 1)))
        y = int(round(ny * (image.height() - 1)))
        if not (0 <= x < image.width() and 0 <= y < image.height()):
            return None
        colour = image.pixelColor(x, y)
        return (colour.red(), colour.green(), colour.blue())

    def source_image(self, photo_id: str, path: Path):
        """A dekódolt FORRÁSKÉP (RGB uint8), vagy `None`.

        A vágás-javaslatok (#448) elemzik — a `redeye_spot_count` mintájára a
        GUI-szálról hívandó, mert a megosztott dekód-gyorsítótárat használja.
        """
        try:
            mtime = Path(path).stat().st_mtime
        except OSError:
            mtime = None
        return self._resolve_source(str(photo_id), Path(path), mtime, shared_cache=True)

    def histogram_for(self, photo_id: str) -> dict:
        """Az utoljára renderelt előnézet RGB-hisztogramja (#25), vagy üres
        hisztogram, ha a fotó nincs (már) regisztrálva."""
        with self._lock:
            return self._histograms.get(str(photo_id), EMPTY_HISTOGRAM)

    def frame_placement(self, photo_id: str) -> TartalomHely | None:
        """Hol van a FÉNYKÉP az utoljára renderelt előnézetben (#3166)?

        `None`, ha a lánc nem tartalmaz keret-effektet (vagy a fotó nincs
        regisztrálva) — ilyenkor a rétegek a kirajzolt kép TELJES
        téglalapját kapják, ahogy eddig."""
        with self._lock:
            return self._placements.get(str(photo_id))

    @staticmethod
    def _store_gpu_image(store: OrderedDict[str, QImage], key: str, image: QImage | None) -> None:
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
            display_mode = self._display_mode
        if image.isNull() and not (is_gpu_prefix or is_gpu_lut):
            image = _placeholder()
        # Fél-dimenziós kérés (csak `sourceSize.width`, magasság nélkül): a (w, 0) a
        # QSize.isValid() szerint érvényes, de a scaled() üres képet adna
        # (#48). Fél-dimenziós kérésnél képaránytartó scaledToWidth/Height.
        # #1185: null képet NEM méretezünk — a `gpuprefix=1`/`gpulut=1`
        # ágon szándékosan nincs placeholder-tartalék, ezért üres tárnál a
        # kép null marad, a Qt pedig minden ilyen kérésnél kiírja, hogy
        # „QImage::scaleWidth: Image is a null image". Ártalmatlan, de
        # elfedi a valódi hibákat a naplóban.
        jelol = not (is_gpu_prefix or is_gpu_lut) and display_mode_changes_pixels(display_mode)
        if requested_size is not None and not image.isNull():
            width, height = requested_size.width(), requested_size.height()
            # #3800 (GPU-előtag), #3819 (fő fotó): a befoglaló dobozba
            # csak KICSINYÍTÜNK — a kis kép felnagyítása csak memóriát és
            # méretezési időt visz, a kirajzolás úgyis a kép méretére nyújt.
            # KIVÉTEL a képpontot mozdító megjelenítési mód: az lent, a
            # méretezés UTÁN jelöl, és natív méreten jelölve a kirajzolás
            # nyújtaná szét a jelölőszínt a szomszédokba (#1576).
            if _belefer(image, width, height) and not jelol:
                width = height = 0
            smooth = Qt.TransformationMode.SmoothTransformation
            if width > 0 and height > 0:
                image = image.scaled(requested_size, Qt.AspectRatioMode.KeepAspectRatio, smooth)
            elif width > 0:
                image = image.scaledToWidth(width, smooth)
            elif height > 0:
                image = image.scaledToHeight(height, smooth)
        # Megjelenítési mód (#1576) — az UTOLSÓ lépés, a méretezés UTÁN.
        #
        # A sorrend nem közömbös: a méretezés simító (SmoothTransformation),
        # tehát előbb jelölve a lazacpiros belekeveredne a szomszédokba, és
        # a képernyőn se a jelölőszín, se az eredeti fehér nem maradna meg.
        # Az eredetiben is a KIRAJZOLÁS a hely (`0x009e285d`), vagyis a
        # ténylegesen látható képpontokon dől el, mi számít kifehéredettnek.
        #
        # A GPU-ágak (`gpuprefix=1`/`gpulut=1`) KIMARADNAK: a LUT adat, nem
        # kép — átfestve a shader hibás tábláról mintavételezne.
        if jelol and not image.isNull():
            image = _rgb_array_to_qimage(
                apply_display_mode(_qimage_to_rgb_array(image), display_mode)
            )
        if size is not None:
            size.setWidth(image.width())
            size.setHeight(image.height())
        return image


def _belefer(image: QImage, width: int, height: int) -> bool:
    """A kép a kért (`0` = korlátlan) dobozba már méretezés nélkül is
    belefér (#3800)."""
    return (width <= 0 or image.width() <= width) and (height <= 0 or image.height() <= height)


def _placeholder() -> QImage:
    image = QImage(_PLACEHOLDER_SIZE, _PLACEHOLDER_SIZE, QImage.Format.Format_RGB32)
    image.fill(_PLACEHOLDER_COLOR)
    return image
