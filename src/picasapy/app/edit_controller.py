"""EditController: a szerkesztő-panel (QML) és az EditSession/ini-réteg
közti híd. A bekötést (QML-regisztráció, jelzések) az integrátor végzi."""

from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
from PIL import Image, UnidentifiedImageError
from PySide6.QtCore import Property, QLocale, QObject, Signal, Slot

from picasapy.app.effect_params import (
    format_param_values,
    has_params,
    resolve_effect_params,
)
from picasapy.edit.session import EditSession
from picasapy.fileops import is_folder_writable
from picasapy.ini import IniConflictError, IniSaveError, load_document, update_document
from picasapy.ini.rect64 import Rect64, encode_rect64
from picasapy.ini.retouch import RetouchPatch
from picasapy.ini.text_overlay import (
    TextOverlay,
    parse_text,
    parse_text_active,
    serialize_text,
    serialize_text_active,
)
from picasapy.metadata import read_exif_details
from picasapy.render.gpu_point_pipeline import build_finetune2_lut
from picasapy.render.tone import parse_neutral_argb
from picasapy.scanner import PICASA_INI_NAME

from . import formatting
from .edit_preview import EditPreviewProvider, TextOverlaySpec
from .histogram_helper import EMPTY_HISTOGRAM
from .worker_thread import BackgroundWorkerMixin

_log = logging.getLogger(__name__)

# #459: a csillag/album-írás mintája (photo_ops_controller.py) — a tartós
# ütközés/lemezhiba is kezelt hiba, nem néma adatvesztés/kivétel.
_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError)

# redeye: teljes képes kapcsoló a régió-alapú eszközig (#116)
_TOGGLE_NAMES = ("redeye",)
# egygombos javítások: append-only rétegezés, levétel csak Visszavonással
_ONE_SHOT_NAMES = ("enhance", "autolight", "autocolor")
# Effektek (#20): append-only rétegek. A render-op nélküli effektek is a
# láncba kerülnek (round-trip), az előnézeten csak kimaradnak. A paramétert
# igénylők (pl. sat) dokumentált alapértékkel indulnak — a finomhangolt
# csúszkázás követő feladat.
_EFFECT_PARAMS: dict[str, tuple[str, ...]] = {
    "sat": ("1", "0.500000"),
}
_EFFECT_NAMES = (
    "unsharp",
    "sepia",
    "bw",
    "warm",
    "grain2",
    "tint",
    "sat",
    "radblur",
    "glow2",
    "ansel",
    "radsat",
    "dir_tint",
    "vignette",
    # 4. fül — kreatív effektek (#329)
    "ir",
    "lomo",
    "holga",
    "hdr",
    "cinemascope",
    "orton",
    "sixties",
    "invert",
    "heatmap",
    "crossprocess",
    "quantizepalette",
    "twotone",
    "matte",
    "nightvision",
    "localcontrast",
    # 5. fül — művészi effektek (#330)
    "boost",
    "soften",
    "pixelate",
    "focalzoom",
    "pencilsketch",
    "neon",
    "comicize",
    "border",
    "dropshadow",
    "museummatte",
    "polaroid",
    "roundededges",
    "picnikgrain",
)

#: A `.picasa.ini`-be írandó betűzés, ahol az eltér a belső kulcstól. A
#: Picasa a vignette-et NAGYBETŰVEL írja (`Vignette=1,...`); a round-trip
#: elv (CLAUDE.md 1. döntés) szerint mi is úgy írjuk, hogy a párhuzamosan
#: futó eredeti Picasa is felismerje. Beolvasásnál mindkét alak jó — a
#: renderelő kis-nagybetű-tűrő.
_EFFECT_INI_NAMES: dict[str, str] = {
    "vignette": "Vignette",
    # a 4-5. fül effektjeit a Picasa nagy kezdőbetűvel (több szónál
    # CamelCase-szel) írja — a `filters=` így marad kölcsönösen olvasható
    "ir": "IR",
    "lomo": "Lomo",
    "holga": "Holga",
    "hdr": "HDR",
    "cinemascope": "Cinemascope",
    "orton": "Orton",
    "sixties": "Sixties",
    "invert": "Invert",
    "heatmap": "HeatMap",
    "crossprocess": "CrossProcess",
    "quantizepalette": "QuantizePalette",
    "twotone": "TwoTone",
    "matte": "Matte",
    "nightvision": "NightVision",
    "localcontrast": "LocalContrast",
    "roundededges": "RoundedEdges",
    "picnikgrain": "PicnikGrain",
    "boost": "Boost",
    "soften": "Soften",
    "pixelate": "Pixelate",
    "focalzoom": "FocalZoom",
    "pencilsketch": "PencilSketch",
    "neon": "Neon",
    "comicize": "Comicize",
    "border": "Border",
    "dropshadow": "DropShadow",
    "museummatte": "MuseumMatte",
    "polaroid": "Polaroid",
}

#: A retusálás-eszköz (#445) kör alakú ecsetének mérete-csúszkája [1..100]
#: egész egységben ("Brush Size", ld. `EditorPanel.qml`) — a valódi Picasa
#: ecsetméret-egysége nem ismert (ld. `picasapy.ini.retouch` docsztring),
#: ezért ez egy PicasaPy-saját, dokumentált leképezés: a csúszka-érték a
#: `_BRUSH_SIZE_TO_RELATIVE_DIVISOR`-ral osztva adja a relatív [0..1]
#: sugarat (a kép rövidebb oldalára vonatkoztatva, ld.
#: `picasapy.render.retouch.apply_retouch_patches`) — a felső határnál
#: (100) ez 0.1, azaz a kép rövidebb oldalának 10%-a, ami a legnagyobb
#: gyakorlati foltnak is elég, anélkül, hogy a fél képet lefedné.
_BRUSH_SIZE_MIN = 1
_BRUSH_SIZE_MAX = 100
_DEFAULT_BRUSH_SIZE = 20
_BRUSH_SIZE_TO_RELATIVE_DIVISOR = 1000.0

#: A szöveg-eszköz (#148) rögzített betűtípusa — a valódi Picasa `text=`
#: kulcsának betűtípus-mezője csak ROUND-TRIP-elve kerül megőrzésre (ld.
#: `picasapy.ini.text_overlay` docsztring), a rajzoláshoz pedig a render-
#: réteg (`picasapy.render.text_overlay`) amúgy is egységes Hershey-fontot
#: használ — betűtípus-választó ezért nincs a UI-ban.
_DEFAULT_TEXT_FONT = "Arial"

#: A `text=` kulcs `raw_x`/`raw_y` mezőinek JELENTÉSE ismeretlen (ld. az
#: `picasapy.ini.text_overlay` modul docsztringje) — ezért a PicasaPy a
#: relatív [0..1] pozíciót SAJÁT, dokumentált skálázással kódolja ezekbe az
#: egész mezőkbe (kerekítve, 4 tizedesjegynyi felbontással). Ez PicasaPy-
#: eredetű szövegre 100%-ban round-trip-biztos (a modul-docsztring
#: garanciája szerint); egy VALÓDI Picasa `text=` sorát a PicasaPy nem
#: próbálja értelmezni/felülírni, amíg a felhasználó ténylegesen nem
#: szerkeszti (akkor a generikus round-trip réteg helyett ez a modul veszi
#: át — attól kezdve ez a konvenció érvényes rá is).
_TEXT_COORD_SCALE = 10000

#: A szöveg-eszköz stílus-beállításai (#450: kitöltés+körvonal szín,
#: körvonal-vastagság, kitöltés ki/be, átlátszóság) NEM ismert `text=`
#: mezők — a valódi Picasa `text=` sorának `raw_tail` (a betűtípus UTÁNI,
#: tagolatlan) része is ismeretlen jelentésű (ld. `picasapy.ini.text_overlay`
#: docsztring), ezért ide NEM próbálunk kódolni. Ezek a beállítások PicasaPy-
#: saját, KIZÁRÓLAG a folyamatban lévő szerkesztési munkamenet állapotában
#: élnek (mint a `_text_draft`/`_text_pending_pos`) — beginEdit/endEdit
#: alapértékre állnak, a `.picasa.ini`-be jelenleg NEM kerülnek be.
_DEFAULT_TEXT_FILL_COLOR = (255, 255, 255)
_DEFAULT_TEXT_OUTLINE_COLOR = (0, 0, 0)
_DEFAULT_TEXT_OUTLINE_THICKNESS = 0
_DEFAULT_TEXT_FILL_ENABLED = True
_DEFAULT_TEXT_OPACITY = 1.0


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    r, g, b = rgb
    return f"#{r:02x}{g:02x}{b:02x}"


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    text = value.strip().lstrip("#")
    if len(text) != 6:
        raise ValueError(f"Érvénytelen szín (nem #rrggbb alakú): {value!r}")
    try:
        return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))
    except ValueError as error:
        raise ValueError(f"Érvénytelen szín (nem #rrggbb alakú): {value!r}") from error


def _relative_to_raw(value: float) -> int:
    return round(_clamp01(value) * _TEXT_COORD_SCALE)


def _raw_to_relative(raw: int) -> float:
    return _clamp01(raw / _TEXT_COORD_SCALE)


class EditController(QObject, BackgroundWorkerMixin):
    """A QML szerkesztő-panelhez tervezett híd: EditSession + ini-perzisztencia
    + EditPreviewProvider-regisztráció egy helyen.

    #148: a retusálás/szöveg-eszközök property-i/slot-jai is ITT élnek (nem
    külön mixin-fájlban) — egy korábbi kísérlet, amely `_RetouchTextMixin`
    néven, közös `toolsChanged`/`revisionChanged` Signal-aliasszal
    próbálta szétválasztani a fájlt (a CLAUDE.md 800-soros irányelve
    miatt), determinisztikus szegmentálási hibát (SIGSEGV) okozott a valódi
    QQmlApplicationEngine-en át (ld. `tests/app/qml_functional/conftest.py`
    `qml_app` fixture `engine.load(...)` hívása) — feltehetően a Qt
    meta-objektum-rendszer nem szereti, ha egy QObject-leszármazott Signal-
    attribútuma egy MÁSIK QObject-leszármazott osztályból származik és a
    gyerek osztály csak alias-olja. A helyesség előbbre való a fájlméret-
    irányelvnél, ezért ez az osztály EGYBEN maradt — ld. a #148 jelentés
    "nyitva maradt" pontját."""

    revisionChanged = Signal()
    toolsChanged = Signal()
    # GPU élő-előnézet (#22): KÜLÖN jel a revisionChanged-től — a
    # finomhangolás-húzás GPU-útja (previewFinetuneGpu) csak a LUT-ot
    # frissíti, a `previewSource`/`photo` Image-nek NEM szabad ilyenkor
    # újratöltődnie (ez okozná pont azt a numpy-újraszámolást, amit a
    # GPU-réteg elkerülni hivatott). A gpuPrefixSource/gpuLutSource ezt a
    # jelet figyeli.
    gpuRevisionChanged = Signal()
    # #459: a szerkesztés mentése (minden effekt/vágás/felirat-módosítás
    # a `_save()`/`_save_text()`-en át azonnal lemezre ír) csak-olvasható
    # mappán vagy egyéb lemezhibán elbukhat — az eredeti Picasa szövege
    # szerinti kérdés/üzenet a QML-oldalon jelenik meg (a tényleges
    # mappa-másolás NEM készült el, ld. a `_save()` docstringjét).
    editSaveReadOnly = Signal()
    editSaveFailed = Signal(str)
    # #514: a háttérszálon befejezett előnézet-renderelés jelzése. A
    # `Signal` szálak közötti átadása Qt-ben sorba állított (queued), így a
    # rákötött `_on_preview_rendered` MÁR a GUI-szálon fut — a
    # `revisionChanged` (és vele a QML kép-újrakérése) sosem a
    # háttérszálról indul.
    _previewRendered = Signal()

    def __init__(self, provider: EditPreviewProvider, parent=None) -> None:
        super().__init__(parent)
        self._provider = provider
        # #514: az előnézet-renderelések sorszáma. Minden új kérés növeli;
        # a háttérszálra tett (lassú) renderelés a saját sorszámát
        # összeveti az aktuálissal, és ELAVULTKÉNT kihagyja magát, ha
        # időközben újabb kérés érkezett — így egy gyors kattintás-sorozat
        # csak az UTOLSÓ állapotot rendereli ki, és sosem írhat vissza egy
        # régebbi képet a frissebb fölé.
        self._preview_job = 0
        self._previewRendered.connect(self._on_preview_rendered)
        self._photo_id = ""
        self._image_path: Path | None = None
        # #516: a képfüggő effekt-tartományok (pl. `CornerRadius` 0..
        # min(W,H)/2) kiszámolásához — csak a fejlécet olvassuk (PIL nem
        # dekódolja a pixeleket), `beginEdit`-enként újraszámolva
        self._image_size: tuple[int, int] | None = None
        self._ini_path: Path | None = None
        self._section_name = ""
        self._session = EditSession()
        self._revision = 0
        # GPU élő-előnézet (#22): önálló számláló, ld. gpuRevisionChanged
        self._gpu_revision = 0
        # undo/redo verem (#59): (filters-érték a művelet ELŐTT, művelet-kulcs)
        self._undo_stack: list[tuple[str, str]] = []
        self._redo_stack: list[tuple[str, str]] = []
        # fényképezőgép-összefoglaló (#25): a forrásfájl EXIF-jéből, csak a
        # beginEdit-kor olvasva — a szerkesztés alatt nem változik, a
        # csúszka-húzás minden egyes revíziójánál újraolvasni felesleges lenne
        self._camera_summary = ""
        # retusálás (#445): a Vágás-mintájú enter/exit + Alkalmaz/Mégse
        # eszközhöz a kétkattintásos, irányított klónozással (cél→forrás)
        # hozott, MÉG NEM mentett foltok puffere — Alkalmazásig csak az élő
        # előnézetet befolyásolja, ini-t nem ír. A `_retouch_target` az
        # ELSŐ kattintással kijelölt, de a forrás-pont hiányában még nem
        # véglegesített folt cél-pontja (None, ha nincs ilyen félbehagyott
        # folt). A patch-enkénti Undo/Redo/Reset EZEN a pufferen dolgozik —
        # a globális (`_undo_stack`) verem csak az Alkalmazott retusálást
        # látja EGY lépésként, a foltok belső részleteit nem.
        self._retouch_patches: tuple[RetouchPatch, ...] = ()
        self._retouch_target: tuple[float, float] | None = None
        self._retouch_patch_undo: list[tuple[RetouchPatch, ...]] = []
        self._retouch_patch_redo: list[tuple[RetouchPatch, ...]] = []
        # kör alakú ecset mérete (#445) — munkamenet-szintű állapot (a
        # szöveg-stílushoz hasonlóan NEM kerül a `.picasa.ini`-be), minden
        # szerkesztés-nyitáskor alapértékre áll.
        self._brush_size: int = _DEFAULT_BRUSH_SIZE
        # szöveg-overlay (#148): a mentett `text=`/`textactive=` értékek
        # típusos alakja (None, ha nincs — vagy a bejegyzés nem értelmezhető,
        # a #301-elv szerint), plusz a szerkesztés alatti, MÉG NEM mentett
        # piszkozat (tartalom + kattintott pozíció).
        self._text_overlay: TextOverlay | None = None
        self._text_active = False
        self._text_draft = ""
        self._text_pending_pos: tuple[float, float] | None = None
        # szöveg-stílus (#450): PicasaPy-saját, csak a munkamenetben élő
        # állapot (ld. a `_DEFAULT_TEXT_*` konstansok megjegyzését) — a
        # `.picasa.ini`-be NEM kerül, minden szerkesztés-nyitáskor alapértékre
        # áll (ld. `beginEdit`/`endEdit`).
        self._text_fill_color: tuple[int, int, int] = _DEFAULT_TEXT_FILL_COLOR
        self._text_outline_color: tuple[int, int, int] = _DEFAULT_TEXT_OUTLINE_COLOR
        self._text_outline_thickness: int = _DEFAULT_TEXT_OUTLINE_THICKNESS
        self._text_fill_enabled: bool = _DEFAULT_TEXT_FILL_ENABLED
        self._text_opacity: float = _DEFAULT_TEXT_OPACITY

    # -- QML-nek kitett tulajdonságok --------------------------------------

    @Property(int, notify=revisionChanged)
    def revision(self) -> int:
        return self._revision

    @Property(str, notify=revisionChanged)
    def previewSource(self) -> str:
        """`image://editpreview/<id>?rev=<n>` vagy üres, ha nincs aktív
        szerkesztés. A QML-frissítés triggere a revision — a previewSource
        értéke (a ?rev= rész) attól függ, hogy a kép-URL biztosan változzon."""
        if not self._photo_id:
            return ""
        return f"image://editpreview/{self._photo_id}?rev={self._revision}"

    @Property(str, notify=gpuRevisionChanged)
    def gpuPrefixSource(self) -> str:
        """A finetune2 ELŐTTI köztes kép URL-je (#22), vagy üres string, ha
        nincs aktív szerkesztés vagy a jelenlegi lánc nem GPU-alkalmas
        (`EditSession.gpu_finetune_prefix()` — ld. ott a feltételt). A
        `GpuPointFilterPreview.qml` ezt tölti be `sourceItem`-ként; a hívó
        (QML) ÜRES string esetén nem is jeleníti meg a GPU-réteget."""
        if not self._photo_id or self._session.gpu_finetune_prefix() is None:
            return ""
        return f"image://editpreview/{self._photo_id}?gpuprefix=1&rev={self._gpu_revision}"

    @Property(str, notify=gpuRevisionChanged)
    def gpuLutSource(self) -> str:
        """A jelenlegi finetune2-LUT 256×1 képének URL-je (#22) — ugyanaz az
        eligibilitási feltétel, mint `gpuPrefixSource`-nál."""
        if not self._photo_id or self._session.gpu_finetune_prefix() is None:
            return ""
        return f"image://editpreview/{self._photo_id}?gpulut=1&rev={self._gpu_revision}"

    @Property("QVariant", notify=revisionChanged)
    def histogram(self):
        """A jelenleg renderelt előnézet RGB-hisztogramja (#25) — a
        HistogramBox.qml Canvas-a ebből rajzolja a három görbét. A revision
        minden előnézet-frissítéskor (csúszka-húzás közben is) bumpol, a
        provider a MEGJELENÍTETT képből számolja (ld. edit_preview.py)."""
        if not self._photo_id:
            return dict(EMPTY_HISTOGRAM)
        return self._provider.histogram_for(self._photo_id)

    @Property(str, notify=revisionChanged)
    def cameraSummary(self) -> str:
        """Picasa-stílusú, egysoros gép-összefoglaló (#25) a hisztogram
        alatt — a forrásfájl EXIF-jéből, beginEdit-kor gyorsítótárazva."""
        return self._camera_summary

    @Property(bool, notify=toolsChanged)
    def redeyeActive(self) -> bool:
        return self._session.has("redeye")

    @Property(bool, notify=toolsChanged)
    def enhanceActive(self) -> bool:
        return self._session.has("enhance")

    @Property(bool, notify=toolsChanged)
    def autolightActive(self) -> bool:
        return self._session.has("autolight")

    @Property(bool, notify=toolsChanged)
    def autocolorActive(self) -> bool:
        return self._session.has("autocolor")

    # -- retusálás (#148) ---------------------------------------------------

    @Property(bool, notify=toolsChanged)
    def hasRetouch(self) -> bool:
        """Van-e MENTETT retusálás — akár a jelenlegi (v2, folt-alapú, #445),
        akár egy korábbi PicasaPy-verzió (v1, téglalap-régiós, #148) által
        mentett alakban — a „Visszavonás: Retusálás" felirathoz és a UI
        állapot-jelzéséhez."""
        return bool(self._session.retouch_patches()) or bool(self._session.retouch_regions())

    @Property(int, notify=revisionChanged)
    def retouchPendingCount(self) -> int:
        """A retusálás-eszközben véglegesített (kétkattintásos), MÉG NEM
        alkalmazott foltok száma — az Alkalmaz gomb csak akkor engedélyezett,
        ha ez pozitív."""
        return len(self._retouch_patches)

    @Property(bool, notify=revisionChanged)
    def retouchPatchPending(self) -> bool:
        """Van-e félbehagyott folt (cél kijelölve, forrás még nincs
        véglegesítve) — a „Refining…" felirathoz a QML-ben."""
        return self._retouch_target is not None

    @Property(bool, notify=revisionChanged)
    def canUndoPatch(self) -> bool:
        """Van-e patch-enkénti visszavonható lépés a retusálás-pufferben
        (NEM a globális Visszavonás-verem, ld. `undoPatch`)."""
        return bool(self._retouch_patch_undo)

    @Property(bool, notify=revisionChanged)
    def canRedoPatch(self) -> bool:
        return bool(self._retouch_patch_redo)

    @Property(int, notify=toolsChanged)
    def brushSize(self) -> int:
        """A retusálás-ecset mérete [1..100] egészben ("Brush Size", #445)."""
        return self._brush_size

    # -- szöveg-overlay (#148) -----------------------------------------------

    @Property(str, notify=toolsChanged)
    def textDraft(self) -> str:
        """A szöveg-eszköz megnyitásakor a mezőbe töltendő piszkozat — a
        mentett tartalommal indul (ha van), a szerkesztés alatt a
        `setTextDraft` frissíti."""
        return self._text_draft

    @Property(bool, notify=revisionChanged)
    def textHasPlacement(self) -> bool:
        """Kattintott-e már pozíciót a felhasználó a jelenlegi piszkozathoz —
        az Alkalmaz gomb csak ekkor engedélyezett."""
        return self._text_pending_pos is not None

    @Property(bool, notify=toolsChanged)
    def hasTextOverlay(self) -> bool:
        """Van-e MENTETT, aktív szöveg-overlay — a „Visszavonás: Szöveg"
        felirathoz és a UI állapot-jelzéséhez."""
        return (
            self._text_overlay is not None
            and self._text_active
            and bool(self._text_overlay.content)
        )

    # -- szöveg-stílus (#450): kitöltés+körvonal szín, körvonal-vastagság,
    # kitöltés ki/be, átlátszóság — ld. a `_DEFAULT_TEXT_*` konstansok
    # megjegyzését: PicasaPy-saját, csak a munkamenetben élő állapot, a
    # `.picasa.ini`-be jelenleg NEM kerül. A `#rrggbb` sztring-alak QML-
    # barát (a `Rectangle.color`/swatch-gombok is így fogadják). ---------

    @Property(str, notify=toolsChanged)
    def textFillColor(self) -> str:
        """A kitöltés-szín `#rrggbb` alakban."""
        return _rgb_to_hex(self._text_fill_color)

    @Property(str, notify=toolsChanged)
    def textOutlineColor(self) -> str:
        """A körvonal-szín `#rrggbb` alakban (a fill-től KÜLÖN választható)."""
        return _rgb_to_hex(self._text_outline_color)

    @Property(int, notify=toolsChanged)
    def textOutlineThickness(self) -> int:
        """A körvonal vastagsága képpontban — `0` esetén nincs körvonal
        (ez az alapérték)."""
        return self._text_outline_thickness

    @Property(bool, notify=toolsChanged)
    def textFillEnabled(self) -> bool:
        """Kitöltve jelenjen-e meg a szöveg — `False` a „Don't show the
        solid fill color (show outline only)" kapcsolónak felel meg."""
        return self._text_fill_enabled

    @Property(float, notify=toolsChanged)
    def textOpacity(self) -> float:
        """A szöveg-réteg átlátszósága [0..1] — `1.0` (alapérték) a
        teljesen fedő, korábbi viselkedés."""
        return self._text_opacity

    @Slot(str)
    def setTextFillColor(self, value: str) -> None:
        """A kitöltés-szín beállítása (`#rrggbb`); élő előnézettel."""
        self._require_active()
        self._text_fill_color = _hex_to_rgb(value)
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(str)
    def setTextOutlineColor(self, value: str) -> None:
        """A körvonal-szín beállítása (`#rrggbb`); élő előnézettel."""
        self._require_active()
        self._text_outline_color = _hex_to_rgb(value)
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(int)
    def setTextOutlineThickness(self, value: int) -> None:
        """A körvonal-vastagság beállítása (>=0 képpont); élő előnézettel."""
        self._require_active()
        if value < 0:
            raise ValueError(f"A textOutlineThickness nem lehet negatív: {value}")
        self._text_outline_thickness = value
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(bool)
    def setTextFillEnabled(self, value: bool) -> None:
        """A kitöltés ki/be kapcsolása; élő előnézettel."""
        self._require_active()
        self._text_fill_enabled = value
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(float)
    def setTextOpacity(self, value: float) -> None:
        """Az átlátszóság beállítása [0..1]; élő előnézettel."""
        self._require_active()
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"A textOpacity a [0..1] tartományon kívül: {value}")
        self._text_opacity = value
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()

    # Gomb-tiltási szabály (#116): az egygombos javítás gombja addig tiltott,
    # amíg ugyanez a szűrő a lánc UTOLSÓ eleme — másik effekt után újra aktív.

    @Property(bool, notify=toolsChanged)
    def enhanceEnabled(self) -> bool:
        return not self._session.last_is("enhance")

    @Property(bool, notify=toolsChanged)
    def autolightEnabled(self) -> bool:
        return not self._session.last_is("autolight")

    @Property(bool, notify=toolsChanged)
    def autocolorEnabled(self) -> bool:
        return not self._session.last_is("autocolor")

    @Property(float, notify=toolsChanged)
    def tiltParam(self) -> float:
        """A mentett döntés-paraméter (-1..1 Picasa-egység), vagy 0.0, ha
        nincs tilt-szűrő a láncban. A döntés-csúszka ezzel áll be az eszköz
        megnyitásakor és lapozáskor a MENTETT értékre, ne 0-ra (#131)."""
        return self._session.tilt_param() or 0.0

    # Finomhangolás (#20): a négy csúszka a MENTETT finetune2 értékeire áll
    # az eszköz megnyitásakor és lapozáskor (a néző syncFinetuneSliders-e
    # ezekből tölt, a tilt-csúszka mintájára).

    @Property(float, notify=toolsChanged)
    def fillLight(self) -> float:
        return self._finetune_field("fill")

    @Property(float, notify=toolsChanged)
    def highlights(self) -> float:
        return self._finetune_field("highlights")

    @Property(float, notify=toolsChanged)
    def shadows(self) -> float:
        return self._finetune_field("shadows")

    @Property(float, notify=toolsChanged)
    def colorTemp(self) -> float:
        return self._finetune_field("temperature")

    @Property(bool, notify=toolsChanged)
    def hasFinetune(self) -> bool:
        """Van-e finomhangolás a láncban — a „Visszavonás" felirathoz."""
        return self._session.has_finetune()

    @Property(bool, notify=toolsChanged)
    def hasCrop(self) -> bool:
        """Van-e alkalmazott vágás — a „Visszavonás: Vágás" gombhoz (#51)."""
        return self._session.crop() is not None

    @Property("QVariant", notify=toolsChanged)
    def cropSelection(self):
        """A jelenlegi crop64 relatív [0..1] téglalapja (#71), vagy None ha
        nincs vágás — a Vágás eszköz ezzel tölti elő a meglévő kijelölést."""
        rect = self._session.crop()
        if rect is None:
            return None
        return {
            "x": rect.left,
            "y": rect.top,
            "width": rect.right - rect.left,
            "height": rect.bottom - rect.top,
        }

    @Property(bool, notify=toolsChanged)
    def canUndo(self) -> bool:
        return bool(self._undo_stack)

    @Property(bool, notify=toolsChanged)
    def canRedo(self) -> bool:
        return bool(self._redo_stack)

    @Property(str, notify=toolsChanged)
    def undoAction(self) -> str:
        """A visszavonható művelet kulcsa (crop/tilt/redeye/…) — a gomb
        feliratához (#59)."""
        return self._undo_stack[-1][1] if self._undo_stack else ""

    @Property(str, notify=toolsChanged)
    def redoAction(self) -> str:
        return self._redo_stack[-1][1] if self._redo_stack else ""

    # -- műveletek ------------------------------------------------------------

    @Slot(str, str)
    def beginEdit(self, photo_id: str, image_path: str) -> None:
        """Szerkesztés indítása: a filters= betöltése az iniből (hiányzó
        ini/szekció/kulcs esetén üres lánc), regisztráció a previewnél."""
        # #546: a képváltás érvényteleníti a futó háttér-rendert — az az
        # ELŐZŐ fotó képét tárolná el (és emitálna rá revíziót)
        self._preview_job += 1
        path = Path(image_path)
        self._photo_id = photo_id
        self._image_path = path
        self._image_size = self._read_image_size(path)
        self._ini_path = path.parent / PICASA_INI_NAME
        self._section_name = path.name
        self._session = EditSession.from_value(self._read_filters_value())
        self._camera_summary = formatting.camera_summary_text(
            read_exif_details(path), QLocale(), self.tr
        )
        # Perzisztens, rétegenkénti undo (#116 visszajelzés): a mentett lánc
        # maga a réteg-verem — minden elemhez visszavonás-lépés jár, fordított
        # sorrendben, képváltás és újranyitás után is.
        self._undo_stack = self._seed_undo_from_chain(self._session)
        self._redo_stack.clear()
        self._retouch_patches = ()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._brush_size = _DEFAULT_BRUSH_SIZE
        self._text_overlay = self._read_text_overlay()
        self._text_active = (
            self._read_text_active() if self._text_overlay is not None else False
        )
        self._text_draft = ""
        self._text_pending_pos = None
        self._text_fill_color = _DEFAULT_TEXT_FILL_COLOR
        self._text_outline_color = _DEFAULT_TEXT_OUTLINE_COLOR
        self._text_outline_thickness = _DEFAULT_TEXT_OUTLINE_THICKNESS
        self._text_fill_enabled = _DEFAULT_TEXT_FILL_ENABLED
        self._text_opacity = _DEFAULT_TEXT_OPACITY
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def endEdit(self) -> None:
        """Szerkesztés lezárása: leregisztrálás a previewnél, állapot ürítése.

        #546: a `_preview_job` léptetése érvényteleníti a futó háttér-
        rendert. Enélkül az a lezárt fotót a végén ÚJRA beregisztrálná (a
        10–30 MB-os dekódolt forrás visszakerülne az LRU-ba), és utólagos
        `revisionChanged`-et emitálna egy már üres szerkesztő-állapotra."""
        self._preview_job += 1
        if self._photo_id:
            self._provider.unregister(self._photo_id)
        self._photo_id = ""
        self._image_path = None
        self._image_size = None
        self._ini_path = None
        self._section_name = ""
        self._session = EditSession()
        self._camera_summary = ""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._retouch_patches = ()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._brush_size = _DEFAULT_BRUSH_SIZE
        self._text_overlay = None
        self._text_active = False
        self._text_draft = ""
        self._text_pending_pos = None
        self._text_fill_color = _DEFAULT_TEXT_FILL_COLOR
        self._text_outline_color = _DEFAULT_TEXT_OUTLINE_COLOR
        self._text_outline_thickness = _DEFAULT_TEXT_OUTLINE_THICKNESS
        self._text_fill_enabled = _DEFAULT_TEXT_FILL_ENABLED
        self._text_opacity = _DEFAULT_TEXT_OPACITY
        self._bump_revision()
        self._bump_gpu_revision()
        self.toolsChanged.emit()

    @Slot(str)
    def toggleTool(self, name: str) -> None:
        """Paraméter nélküli szűrő alkalmazása (#116).

        Egygombos javítás (enhance/autolight/autocolor): append-only réteg a
        lánc végére; ha ugyanez a szűrő a lánc utolsó eleme, a hívás no-op
        (a gomb ilyenkor a UI-ban tiltott — ez a védőkorlát). A redeye
        teljes képes be/ki kapcsoló a régió-alapú eszközig."""
        self._require_active()
        key = name.casefold()
        if key in _ONE_SHOT_NAMES:
            if self._session.last_is(key):
                return
            self._push_undo(key)
            self._session = self._session.apply(key)
        elif key in _TOGGLE_NAMES:
            self._push_undo(key)
            self._session = self._session.toggle(key)
        else:
            raise ValueError(f"Érvénytelen szerkesztő-eszköz: {name!r}")
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(float, float, float, float)
    def applyCrop(self, x: float, y: float, w: float, h: float) -> None:
        """Relatív [0..1] (x, y, szélesség, magasság) → crop64.

        A UI-ról érkező határhibákat (pl. enyhén kilógó téglalap)
        [0..1]-re clampeljük; nem-UI (pl. nulla/negatív méret) hibára
        ValueError-t emelünk."""
        self._require_active()
        if w <= 0 or h <= 0:
            raise ValueError(f"A crop szélessége/magassága pozitív kell legyen: {w}x{h}")
        left = _clamp01(x)
        top = _clamp01(y)
        right = _clamp01(x + w)
        bottom = _clamp01(y + h)
        if right <= left or bottom <= top:
            raise ValueError(
                f"A clampelt crop üres lenne: ({left}, {top}, {right}, {bottom})"
            )
        rect = Rect64(left=left, top=top, right=right, bottom=bottom)
        self._push_undo("crop")
        self._session = self._session.set_crop(rect)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def clearCrop(self) -> None:
        """A crop64 eltávolítása."""
        self._require_active()
        self._push_undo("crop")
        self._session = self._session.clear_crop()
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def enterCropTool(self) -> None:
        """A Vágás eszköz megnyitásakor (#71): az előnézet a lánc crop64
        NÉLKÜLI változatát mutatja, hogy a teljes (vágatlan) forráskép
        látsszon — a meglévő kijelölést a `cropSelection` alapján a QML
        overlay rajzolja rá. Nem ír inibe, nem tol undo-lépést."""
        self._require_active()
        self._register_preview(self._session.clear_crop())
        self._bump_revision()

    @Slot()
    def exitCropTool(self) -> None:
        """A Vágás eszköz bezárásakor (Mégse) visszaáll a rendes, a
        ténylegesen mentett crop64-et is tartalmazó előnézetre."""
        self._require_active()
        self._register_preview()
        self._bump_revision()

    # -- retusálás (#445): a Vágás mintáját követő enter/exit + Alkalmaz/
    # Mégse eszköz, DE a foltok maguk a Picasa súgószövege szerinti
    # kétkattintásos, irányított klónozással jönnek létre:
    #   1. beginRetouchPatch(x, y)   — a javítandó folt (CÉL) kijelölése,
    #   2. previewRetouchSource(x, y) — egérmozgatásra a FORRÁS élő
    #      előnézete (a cél helyére a forrás körüli tartalom kerül),
    #   3. commitRetouchPatch(x, y) — a második kattintás véglegesíti a
    #      foltot a PENDING pufferben (nem ír inibe, nem tol GLOBÁLIS
    #      undo-lépést — csak a patch-enkénti undo/redo látja, ld. lent),
    #   4. cancelRetouchPatch()      — félbehagyott folt eldobása (pl. Esc).
    # A puffer élő előnézetet azonnal frissít, de csak az Alkalmaz (a Vágás
    # mintájára) írja ini-be, EGY globális undo-lépésként. ------------------

    @Slot()
    def enterRetouchTool(self) -> None:
        """A Retusálás eszköz megnyitása: a puffer a MENTETT foltokkal
        indul (ha a felhasználó korábban már alkalmazott retusálást ezzel
        az eszközzel — egy korábbi, v1 téglalap-régiós retusálás nem
        tölthető be foltként, ld. `EditSession.retouch_patches` docsztring),
        nem ír inibe, nem tol undo-lépést."""
        self._require_active()
        self._retouch_patches = self._session.retouch_patches()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()

    @Slot()
    def exitRetouchTool(self) -> None:
        """A Retusálás eszköz bezárása (Mégse): a puffer eldobása, visszaáll
        a ténylegesen mentett előnézetre — a mentett foltok érintetlenek."""
        self._require_active()
        self._retouch_patches = ()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._register_preview()
        self._bump_revision()

    @Slot(float, float)
    def beginRetouchPatch(self, x: float, y: float) -> None:
        """1. kattintás: a javítandó folt (CÉL) kijelölése. Félbehagyott
        (korábban elkezdett, de nem véglegesített) folt esetén a régi
        cél-pontot csendben lecseréli az újra."""
        self._require_active()
        self._retouch_target = (_clamp01(x), _clamp01(y))
        self._bump_revision()

    @Slot(float, float)
    def previewRetouchSource(self, x: float, y: float) -> None:
        """Egérmozgatás a CÉL kijelölése UTÁN: a csereterület (FORRÁS) élő
        előnézete — NEM ír inibe, NEM tol undo-lépést. Cél nélkül (nincs
        folyamatban lévő folt) néma no-op."""
        self._require_active()
        if self._retouch_target is None:
            return
        patch = self._build_patch(self._retouch_target, (_clamp01(x), _clamp01(y)))
        preview_patches = (*self._retouch_patches, patch)
        self._register_preview(self._session.set_retouch_patches(preview_patches))
        self._bump_revision()

    @Slot(float, float)
    def commitRetouchPatch(self, x: float, y: float) -> None:
        """2. kattintás: a folt véglegesítése a PENDING pufferben (patch-
        enkénti undo-lépéssel) — NEM ír inibe (az Alkalmazásig). Cél nélkül
        néma no-op."""
        self._require_active()
        if self._retouch_target is None:
            return
        patch = self._build_patch(self._retouch_target, (_clamp01(x), _clamp01(y)))
        self._retouch_patch_undo.append(self._retouch_patches)
        self._retouch_patch_redo.clear()
        self._retouch_patches = (*self._retouch_patches, patch)
        self._retouch_target = None
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def cancelRetouchPatch(self) -> None:
        """Félbehagyott folt eldobása (pl. Esc) — a korábban VÉGLEGESÍTETT
        foltok érintetlenek. Félbehagyott folt nélkül néma no-op."""
        self._require_active()
        if self._retouch_target is None:
            return
        self._retouch_target = None
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()

    @Slot(int)
    def setBrushSize(self, value: int) -> None:
        """Az ecset méretének beállítása ([1..100]-ra clampelve, #445)."""
        self._require_active()
        self._brush_size = max(_BRUSH_SIZE_MIN, min(_BRUSH_SIZE_MAX, value))
        self.toolsChanged.emit()

    # -- patch-enkénti Undo/Redo/Reset (#445): a retusálás PUFFERÉN
    # (`_retouch_patches`) dolgozik, NEM a globális `_undo_stack`/
    # `_redo_stack` vermen — az eszközön belüli, foltonkénti lépegetés,
    # a „Undo Patch"/„Redo Patch"/„Reset" gombokhoz. -----------------------

    @Slot()
    def undoPatch(self) -> None:
        """Az utoljára véglegesített folt visszavonása a pufferben."""
        if not self._retouch_patch_undo:
            return
        self._require_active()
        self._retouch_patch_redo.append(self._retouch_patches)
        self._retouch_patches = self._retouch_patch_undo.pop()
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def redoPatch(self) -> None:
        """A visszavont folt ismételt alkalmazása a pufferben."""
        if not self._retouch_patch_redo:
            return
        self._require_active()
        self._retouch_patch_undo.append(self._retouch_patches)
        self._retouch_patches = self._retouch_patch_redo.pop()
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def resetPatches(self) -> None:
        """A puffer minden foltjának törlése (a félbehagyott folt is) —
        patch-enkénti undo-lépéssel (`undoPatch` visszaállíthatja). Üres
        pufferen/félbehagyott folt nélkül néma no-op."""
        if not self._retouch_patches and self._retouch_target is None:
            return
        self._require_active()
        self._retouch_patch_undo.append(self._retouch_patches)
        self._retouch_patch_redo.clear()
        self._retouch_patches = ()
        self._retouch_target = None
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def applyRetouch(self) -> None:
        """Alkalmaz: a puffer foltjainak mentése a láncba (undo + ini-írás).
        Üres puffernél no-op (a gomb ilyenkor a UI-ban tiltott) — egy
        félbehagyott (cél nélküli forrás) folt csendben elvész."""
        self._require_active()
        if not self._retouch_patches:
            return
        self._push_undo("retouch")
        self._session = self._session.set_retouch_patches(self._retouch_patches)
        self._retouch_patches = ()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    def _build_patch(
        self, target: tuple[float, float], source: tuple[float, float]
    ) -> RetouchPatch:
        return RetouchPatch(
            target_x=target[0],
            target_y=target[1],
            source_x=source[0],
            source_y=source[1],
            radius=self._brush_size / _BRUSH_SIZE_TO_RELATIVE_DIVISOR,
        )

    def _session_with_retouch_pending(self) -> EditSession:
        return self._session.set_retouch_patches(self._retouch_patches)

    # -- szöveg-overlay (#148): a `text=`/`textactive=` külön ini-kulcs (NEM
    # a filters= lánc része), ezért a piszkozat/pozíció ide, az
    # EditController állapotába kerül, nem az EditSession-be. Az enter/exit
    # + Alkalmaz/Mégse minta a retusáléhoz hasonló. -------------------------

    @Slot()
    def enterTextTool(self) -> None:
        """A Szöveg eszköz megnyitása: a mező a MENTETT tartalommal indul
        (ha van), pozíció nélkül — a felhasználónak a képre kattintva kell
        elhelyeznie."""
        self._require_active()
        self._text_draft = self._text_overlay.content if self._text_overlay else ""
        self._text_pending_pos = None
        self.toolsChanged.emit()

    @Slot()
    def exitTextTool(self) -> None:
        """A Szöveg eszköz bezárása (Mégse): a piszkozat eldobása, visszaáll
        a ténylegesen mentett előnézetre."""
        self._require_active()
        self._text_pending_pos = None
        self._text_draft = ""
        self._register_preview()
        self._bump_revision()

    @Slot(str)
    def setTextDraft(self, content: str) -> None:
        """A szövegmező tartalmának élő követése — ha már van kattintott
        pozíció, az élő előnézet is frissül; NEM ír inibe."""
        self._require_active()
        self._text_draft = content
        self._register_preview()
        self._bump_revision()

    @Slot(float, float)
    def previewTextPlacement(self, x: float, y: float) -> None:
        """Kattintás a képen: a piszkozat pozíciójának beállítása, élő
        előnézettel — NEM ír inibe, NEM tol undo-lépést (Alkalmazásig)."""
        self._require_active()
        self._text_pending_pos = (_clamp01(x), _clamp01(y))
        self._register_preview()
        self._bump_revision()

    @Slot()
    def applyText(self) -> None:
        """Alkalmaz: a piszkozat mentése `text=`/`textactive=` kulcsokba.

        Pozíció vagy tartalom nélkül no-op (a gomb ilyenkor a UI-ban
        tiltott). **NEM kerül a Visszavonás-verembe** — ld. `clearText`
        docsztringje az indoklásért; az újbóli Alkalmazás egyszerűen felülírja
        az előző mentett szöveget."""
        self._require_active()
        if self._text_pending_pos is None or not self._text_draft.strip():
            return
        raw_x = _relative_to_raw(self._text_pending_pos[0])
        raw_y = _relative_to_raw(self._text_pending_pos[1])
        self._text_overlay = TextOverlay(
            enabled=True,
            raw_x=raw_x,
            raw_y=raw_y,
            content=self._text_draft,
            font=_DEFAULT_TEXT_FONT,
        )
        self._text_active = True
        self._text_pending_pos = None
        self._save_text()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def clearText(self) -> None:
        """A mentett szöveg-overlay eltávolítása (`text=`/`textactive=`
        kulcsok törlése az iniből).

        **NEM kerül a Visszavonás-verembe**: a `text=`/`textactive=` a
        `filters=` láncon KÍVÜLI, önálló ini-kulcs (ld. modul-tetejei
        megjegyzés), a meglévő perzisztens undo-verem pedig kizárólag a
        `filters=` lánc egymást követő állapotait tárolja — egy ide tolt
        „text" lépés a Visszavonás gombon látszana, de a tényleges hatása
        (a szöveg visszaállítása) nem történne meg, ami félrevezetőbb lenne,
        mint egyáltalán nem kínálni. A törlés ezért azonnali és végleges."""
        self._require_active()
        self._text_overlay = None
        self._text_active = False
        self._text_pending_pos = None
        self._save_text()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(float)
    def setTilt(self, param: float) -> None:
        """A döntés-paraméter (-1..1 tartomány, Picasa-egység) beállítása.

        Picasa-paritás (#73): a skála-mezőbe 0.000000 kerül — a Picasa 3.x
        is így ír, a kitöltő skálát a megjelenítő számolja renderkor."""
        self._require_active()
        self._push_undo("tilt")
        self._session = self._session.set_tilt(param, 0.0)
        self._save()
        self._bump_revision()

    @Slot(float)
    def previewTilt(self, param: float) -> None:
        """Élő forgatás-előnézet a csúszka húzása közben (#72): a képet a
        pillanatnyi paraméterrel újrarenderli, de NEM ír ini-be és NEM tol
        undo-lépést — a tényleges mentés az elengedéskor hívott setTilt-tel
        történik."""
        self._require_active()
        preview_session = self._session.set_tilt(param, 0.0)
        self._register_preview(preview_session)
        self._bump_revision()

    @Slot(float, float, float, float)
    def previewFinetune(
        self, fill: float, highlights: float, shadows: float, temperature: float
    ) -> None:
        """Élő finomhangolás-előnézet a csúszkák húzása közben (#20): a képet
        a pillanatnyi négy értékkel újrarenderli, de NEM ír ini-be és NEM tol
        undo-lépést — a mentés az elengedéskor hívott setFinetune-nal történik
        (a previewTilt mintájára)."""
        self._require_active()
        preview_session = self._session.set_finetune(
            fill=fill, highlights=highlights, shadows=shadows, temperature=temperature
        )
        self._register_preview(preview_session)
        self._bump_revision()

    @Slot(float, float, float, float)
    def previewFinetuneGpu(
        self, fill: float, highlights: float, shadows: float, temperature: float
    ) -> None:
        """GPU-gyorsított élő finomhangolás-előnézet (#22).

        A `previewFinetune`-nal ellentétben ez NEM futtatja újra a teljes
        numpy filter-láncot minden húzási lépésnél — csak a (256×1, olcsó)
        LUT-ot számolja újra és frissíti a `gpuLutSource`-ot; a
        `GpuPointFilterPreview.qml` a drága munkát a GPU-n végzi, a
        `gpuPrefixSource` (a finetune2 ELŐTTI kép) a húzás alatt
        VÁLTOZATLAN. A hívó (PhotoViewer.qml) csak akkor hívja ezt
        previewFinetune HELYETT, ha a futtatókörnyezet RHI-alapú GPU-t
        biztosít ÉS a jelenlegi lánc GPU-alkalmas (`gpuPrefixSource`
        nem üres) — máskülönben a normál CPU-utat használja.

        NEM ír inibe, NEM tol undo-lépést, NEM bumpolja a `revision`-t (a
        `previewSource`/`photo` Image-nek a húzás alatt NEM szabad
        újratöltődnie) — csak a `gpuRevisionChanged`-et."""
        self._require_active()
        prefix_ops = self._session.gpu_finetune_prefix()
        if prefix_ops is None:
            # a lánc időközben (pl. párhuzamos ini-módosítás) GPU-
            # alkalmatlanná vált — néma, biztonságos no-op, a hívó a
            # gpuPrefixSource újraolvasásával úgyis visszavált CPU-ra
            return
        lut = build_finetune2_lut(
            fill=fill, highlights=highlights, shadows=shadows, temperature=temperature
        )
        self._provider.update_gpu_lut(self._photo_id, lut)
        self._bump_gpu_revision()

    @Slot(float, float, float, float)
    def setFinetune(
        self, fill: float, highlights: float, shadows: float, temperature: float
    ) -> None:
        """A finomhangolás négy csúszkájának mentése egy finetune2 rétegbe.

        A csúszka elengedésekor hívódik: undo-lépést tol és ini-be ír. Ha
        mind a négy érték semleges (0), a réteget eltávolítja — így a
        visszahúzott csúszkák nem hagynak fölösleges no-op finetune2-t."""
        self._require_active()
        self._push_undo("finetune")
        if fill == 0.0 and highlights == 0.0 and shadows == 0.0 and temperature == 0.0:
            self._session = self._session.clear_finetune()
        else:
            self._session = self._session.set_finetune(
                fill=fill,
                highlights=highlights,
                shadows=shadows,
                temperature=temperature,
            )
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot(str)
    def applyEffect(self, name: str) -> None:
        """Effekt réteg a lánc végére (#20): append-only, undo-lépéssel.

        Az ismeretlen név ValueError; a paramétert igénylő effektek (pl. sat)
        dokumentált alapértékkel kerülnek be (`_EFFECT_PARAMS`)."""
        self._require_active()
        key = name.casefold()
        if key not in _EFFECT_NAMES:
            raise ValueError(f"Érvénytelen effekt: {name!r}")
        self._push_undo(key)
        self._session = self._session.append_effect(
            _EFFECT_INI_NAMES.get(key, key), _EFFECT_PARAMS.get(key, ("1",))
        )
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def undo(self) -> None:
        """Az utolsó művelet visszavonása (a művelet ELŐTTI lánc áll vissza)."""
        if not self._undo_stack:
            return
        self._require_active()
        previous_value, action = self._undo_stack.pop()
        self._redo_stack.append((self._session.to_value(), action))
        self._session = EditSession.from_value(previous_value)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    @Slot()
    def redo(self) -> None:
        """A visszavont művelet ismételt alkalmazása."""
        if not self._redo_stack:
            return
        self._require_active()
        redo_value, action = self._redo_stack.pop()
        self._undo_stack.append((self._session.to_value(), action))
        self._session = EditSession.from_value(redo_value)
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    # -- csúszkás effekt-alpanel (#316) --------------------------------------

    @Slot(str, result=bool)
    def effectHasParams(self, name: str) -> bool:
        """Nyíljon-e csúszkás alpanel a gombra kattintva?

        A paraméter nélküli effektek (Szépia, Fekete-fehér…) az eredeti
        Picasában is egy kattintással alkalmazódnak.
        """
        return has_params(name)

    @Slot(str, result="QVariant")
    def effectParams(self, name: str):
        """Az effekt vezérlői a QML-nek — LISTÁT adunk, nem tuple-t: a
        QML-oldalon a tuple NEM tömb (#232).

        #516: a képfüggő tartományokat (`CornerRadius` 0..min(W,H)/2 stb.)
        a JELENLEG szerkesztett kép valódi méretével számoljuk ki
        (`resolve_effect_params`) — nincs bebetonozott szám."""
        width, height = self._image_size if self._image_size else (None, None)
        return [
            {
                "key": param.key,
                "label": param.label,
                "kind": param.kind,
                "minimum": param.minimum,
                "maximum": param.maximum,
                "default": param.default,
                "step": param.step,
                "color": param.color,
            }
            for param in resolve_effect_params(name, width, height)
        ]

    @Slot(str, "QVariantList")
    def previewEffect(self, name: str, values) -> None:
        """Élő előnézet a csúszkák húzása közben: a képet a pillanatnyi
        értékekkel újrarendereli, de NEM ír ini-be és NEM tol undo-lépést
        (a previewFinetune mintájára, #20)."""
        self._require_active()
        preview_session = self._session_with_effect(name, values)
        if preview_session is None:
            return
        self._register_preview(preview_session)
        self._bump_revision()

    @Slot()
    def discardEffectPreview(self) -> None:
        """Mégse: az előnézet elvetése, a mentett lánc visszaállítása."""
        self._require_active()
        self._register_preview()
        self._bump_revision()

    @Slot(str, "QVariantList")
    def applyEffectWithParams(self, name: str, values) -> None:
        """Alkalmaz: a beállított értékekkel fűzi a láncra (undo + mentés).

        Hiányzó vagy hiányos értéklistánál a katalógus alapértékei jönnek —
        így a gomb paraméter nélkül is ugyanazt adja, mint az `applyEffect`.
        """
        self._require_active()
        session = self._session_with_effect(name, values)
        if session is None:
            return
        self._push_undo(name.casefold())
        self._session = session
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()

    def _session_with_effect(self, name: str, values) -> EditSession | None:
        """A lánc az effekttel a végén; ismeretlen effektnél None.

        A hiányzó értékeket a katalógus alapértéke pótolja, a fölöslegeseket
        eldobjuk — a `filters=` sosem kaphat a katalógusnál több paramétert.
        """
        if not isinstance(name, str):
            return None
        key = name.casefold()
        if key not in _EFFECT_NAMES:
            return None
        width, height = self._image_size if self._image_size else (None, None)
        catalogue = resolve_effect_params(key, width, height)
        if not catalogue:
            # paraméter nélküli effekt: a meglévő, dokumentált alapérték-út
            return self._session.append_effect(
                _EFFECT_INI_NAMES.get(key, key), _EFFECT_PARAMS.get(key, ("1",))
            )
        supplied = list(values) if values is not None else []
        resolved = [
            supplied[index]
            if index < len(supplied)
            else (param.color if param.kind == "color" else param.default)
            for index, param in enumerate(catalogue)
        ]
        try:
            formatted = format_param_values(resolved, catalogue)
        except (TypeError, ValueError):
            return None
        return self._session.append_effect(
            _EFFECT_INI_NAMES.get(key, key), ("1", *formatted)
        )

    @staticmethod
    def _read_image_size(path: Path) -> tuple[int, int] | None:
        """A kép pixel-mérete a #516 képfüggő effekt-tartományaihoz
        (`CornerRadius` 0..min(W,H)/2, `CaptionHeight` 0..H/6 stb.) — a PIL
        `Image.open` csak a fejlécet olvassa, nem dekódolja a pixeleket, a
        próba tehát olcsó. Olvashatatlan/hiányzó fájlnál `None` — a hívó
        ilyenkor a katalógus fallback-méretére esik vissza."""
        try:
            with Image.open(path) as probe:
                return probe.size
        except (OSError, UnidentifiedImageError, ValueError):
            return None

    # -- belső ------------------------------------------------------------

    @staticmethod
    def _seed_undo_from_chain(session: EditSession) -> list[tuple[str, str]]:
        """A mentett filters-láncból épített undo-verem: az i. lépés
        visszavonása az első i elemű láncot állítja vissza. Az ismeretlen
        (pl. valódi Picasa által írt) szűrők is rétegként vonhatók vissza —
        a Visszavonásig a round-trip elv szerint érintetlenek maradnak."""
        entries: list[tuple[str, str]] = []
        for index, op in enumerate(session.ops):
            previous_value = EditSession(ops=session.ops[:index]).to_value()
            entries.append((previous_value, _action_key(op.name)))
        return entries

    def _finetune_field(self, field: str) -> float:
        """A mentett finetune2 adott csúszka-értéke, vagy 0.0, ha nincs
        finomhangolás — a QML-csúszkák így a mentett értékre állnak (#20)."""
        values = self._session.finetune_values()
        return getattr(values, field) if values is not None else 0.0

    def _push_undo(self, action: str) -> None:
        self._undo_stack.append((self._session.to_value(), action))
        self._redo_stack.clear()

    def _require_active(self) -> None:
        if not self._photo_id or self._image_path is None:
            raise ValueError("Nincs aktív szerkesztés (beginEdit hívása szükséges)")

    def _read_filters_value(self) -> str:
        if self._ini_path is None or not self._ini_path.exists():
            return ""
        section = load_document(self._ini_path).section(self._section_name)
        return (section.get("filters") if section else None) or ""

    def _read_text_overlay(self) -> TextOverlay | None:
        """A mentett `text=` érték típusos alakja, vagy None ha nincs (vagy
        nem értelmezhető, #301-elv — a generikus round-trip réteg ilyenkor
        érintetlenül megőrzi, amíg ez a modul nem szerkeszti)."""
        if self._ini_path is None or not self._ini_path.exists():
            return None
        section = load_document(self._ini_path).section(self._section_name)
        raw = section.get("text") if section else None
        if not raw:
            return None
        try:
            return parse_text(raw)
        except ValueError:
            return None

    def _read_text_active(self) -> bool:
        """A mentett `textactive=` érték — hiányzó kulcsnál a MEGLÉVŐ
        `text=` bejegyzést alapból aktívnak vesszük (a Picasa-doksi szerint
        ez a gyakoribb eset)."""
        if self._ini_path is None or not self._ini_path.exists():
            return True
        section = load_document(self._ini_path).section(self._section_name)
        raw = section.get("textactive") if section else None
        return parse_text_active(raw) if raw is not None else True

    def _save(self) -> None:
        assert self._ini_path is not None
        if not self._check_writable_before_save():
            return

        def mutate(document):
            if self._session.is_empty():
                document = document.with_removed(self._section_name, "filters")
            else:
                document = document.with_value(
                    self._section_name, "filters", self._session.to_value()
                )
            # Picasa-paritás (#73): a vágás a filters= mellett külön
            # crop=rect64(...) kulcsba is kerül — a Picasa 3.x is így ír.
            crop = self._session.crop()
            if crop is not None:
                document = document.with_value(
                    self._section_name, "crop", f"rect64({encode_rect64(crop)})"
                )
            else:
                document = document.with_removed(self._section_name, "crop")
            return document

        # #137: ütközésbiztos mentés — ha a párhuzamosan futó eredeti Picasa
        # időközben más kulcsot írt ugyanabba az iniben, az nem vész el.
        try:
            update_document(self._ini_path, mutate, backup=True)
        except _WRITE_ERRORS as error:
            self.editSaveFailed.emit(str(error))
            return
        # #514: a mentett lánc újrarenderelése HÁTTÉRSZÁLON — ez az a hely,
        # ahol egy lassú effekt (Lomo, Polaroid…) korábban befagyasztotta a
        # felületet. A csúszka-húzás alatti élő előnézet ettől független
        # (`_register_preview`, szinkron).
        self._register_preview_async()

    def _save_text(self) -> None:
        """A `text=`/`textactive=` kulcsok írása/törlése (#148) — külön az
        `_save()`-től, mert ezek NEM a `filters=` láncba tartoznak, hanem
        önálló, szekció-szintű kulcsok (ld. `picasapy.ini.text_overlay`)."""
        assert self._ini_path is not None
        if not self._check_writable_before_save():
            return

        def mutate(document):
            if self._text_overlay is None or not self._text_overlay.content:
                document = document.with_removed(self._section_name, "text")
                document = document.with_removed(self._section_name, "textactive")
            else:
                document = document.with_value(
                    self._section_name, "text", serialize_text(self._text_overlay)
                )
                document = document.with_value(
                    self._section_name,
                    "textactive",
                    serialize_text_active(self._text_active),
                )
            return document

        try:
            update_document(self._ini_path, mutate, backup=True)
        except _WRITE_ERRORS as error:
            self.editSaveFailed.emit(str(error))
            return
        self._register_preview()

    def _check_writable_before_save(self) -> bool:
        """#459: a mentés ELŐTTI, gyors csak-olvasható-ellenőrzés — az
        eredeti Picasa itt ajánlotta fel a mappa-másolást (*"This file is
        read only. In order to edit this file, Picasa needs to copy the
        file's folder. Would you like to make a copy now?"*). A tényleges
        másolás NEM készült el (a jegy szerint külön, nagyobb munka) — csak
        a FELISMERÉS és a látható jelzés (`editSaveReadOnly`), hogy a
        felhasználó NE néma bukást lásson. Visszaadja, hogy folytatható-e
        a mentés."""
        assert self._ini_path is not None
        folder = self._ini_path.parent
        if is_folder_writable(folder):
            return True
        self.editSaveReadOnly.emit()
        return False

    def _preview_request(self, session: EditSession | None = None) -> dict:
        """A `provider.register()` argumentumai a MOSTANI állapotból.

        Külön lépés, mert a háttérszálas út (#514) a kérést még a hívó
        (GUI-) szálán állítja össze: a háttérszál így nem olvassa a
        controller közben változó mezőit."""
        assert self._image_path is not None
        active_session = session if session is not None else self._session
        gpu_prefix_ops = active_session.gpu_finetune_prefix()
        gpu_lut = self._gpu_lut_for(active_session) if gpu_prefix_ops is not None else None
        return {
            "photo_id": self._photo_id,
            "path": self._image_path,
            "ops": active_session.ops,
            "text": self._current_text_spec(),
            "gpu_prefix_ops": gpu_prefix_ops,
            "gpu_lut": gpu_lut,
        }

    def _register_preview(self, session: EditSession | None = None) -> None:
        """SZINKRON renderelés — az élő (csúszka-húzás alatti) előnézeté.

        Ezek az utak eleve a gyors, gyorsítótárazott lánc-prefixre épülnek
        (#140), és a húzás minden lépésénél friss képet kell adniuk: a
        háttérszálra tolásuk csak késleltetést és villogást hozna."""
        self._preview_job += 1
        self._provider.register(**self._preview_request(session))
        self._bump_gpu_revision()

    def _register_preview_async(self, session: EditSession | None = None) -> None:
        """#514: a MENTETT állapot újrarenderelése HÁTTÉRSZÁLON.

        Ide a lassú, egykattintásos műveletek tartoznak (effekt hozzáadása,
        vágás, visszavonás…). Korábban a GUI szálán futottak, ezért egy
        percekig számoló effekt (#504: Lomo) alatt a felület befagyottnak
        látszott, és a közös haladásjelző csík (#505) sem tudott animálni —
        ugyanaz a szál számolt, ami rajzol. A `BackgroundWorkerMixin`-en át
        indítva a csík MAGÁTÓL pörög (a busy-nyilvántartás a
        `_start_background`-ben jelentkezik be).

        A kép csak a renderelés VÉGÉN frissül: addig a korábbi előnézet
        látszik, ami így is jobb, mint a befagyott felület."""
        self._preview_job += 1
        job = self._preview_job
        request = self._preview_request(session)

        def still_current() -> bool:
            return job == self._preview_job

        def worker() -> None:
            # #546: az elavultság-ellenőrzés a providerben, a TÁROLÁSSAL egy
            # zár alatt fut le (`is_current`) — ha itt kívül néznénk meg,
            # a régebbi render a zárért állva utóbb végezne, és felülírná a
            # frissebb képet. A `shared_cache=False` miatt a háttér-render
            # lokálisan dekódol: a GUI-szál soha nem vár rá záron.
            try:
                self._provider.register(
                    **request, shared_cache=False, is_current=still_current
                )
            except Exception as error:  # noqa: BLE001 — ld. lent
                # #548: a háttérszálban elhaló kivétel NÉMA lenne (a
                # `threading` excepthookja csak stderr-re ír): a kép
                # magyarázat nélkül maradna a régi. A mentés maga már
                # sikerült, ezért nem hibaüzenetet állítunk elő, hanem a
                # meglévő, szálhatáron át sorba állított jelzést használjuk
                # — és naplózunk, hogy a hiba nyomozható legyen.
                _log.exception("Az előnézet háttérszálas renderelése elbukott")
                self.editSaveFailed.emit(str(error))
                return
            if still_current():
                self._previewRendered.emit()

        self._start_background(worker, name="picasapy-editpreview")

    @Slot()
    def cancelPendingPreview(self) -> None:  # noqa: N802 — QML-stílusú név
        """A folyamatban lévő háttér-render érvénytelenítése (#547).

        A `_preview_job` léptetése után a futó worker sem eltárolni, sem
        jelzést emitálni nem fog. Kilépéskor ez zárja be a #430-as
        SIGSEGV-ablakot: a daemon-szál az interpreter leépítése közben
        NEM emitálhat egy közben megsemmisült QObject-nek.
        """
        self._preview_job += 1

    def _on_preview_rendered(self) -> None:
        """A háttérszálas renderelés kész — a GUI-szálon frissítjük a
        képet (`revisionChanged` = cache-buster) és a GPU-rétegeket."""
        self._bump_gpu_revision()
        self._bump_revision()

    @staticmethod
    def _gpu_lut_for(session: EditSession) -> np.ndarray:
        """A `session` MENTETT finetune2-értékeiből (vagy semleges alapból,
        ha nincs finomhangolás) épített LUT (#22) — ez indítja a
        `gpuLutSource`-ot minden `_register_preview()`-nál, hogy a húzás
        KEZDETÉN (az első `previewFinetuneGpu` hívás ELŐTT is) már a
        mentett állapotot tükrözze."""
        values = session.finetune_values()
        if values is None:
            return build_finetune2_lut()
        neutral = parse_neutral_argb(values.neutral)
        return build_finetune2_lut(
            fill=values.fill,
            highlights=values.highlights,
            shadows=values.shadows,
            neutral=neutral,
            temperature=values.temperature,
        )

    def _current_text_spec(self) -> TextOverlaySpec | None:
        """Az élő előnézetbe rajzolandó szöveg — a PENDING piszkozat élvez
        elsőbbséget (a szöveg-eszköz nyitva van), különben a mentett, aktív
        overlay (ha van tartalma); egyébként None (nincs mit rajzolni)."""
        if self._text_pending_pos is not None:
            content = self._text_draft
            if not content.strip():
                return None
            x, y = self._text_pending_pos
            return TextOverlaySpec(
                content=content, x=x, y=y, **self._text_style_kwargs()
            )
        if (
            self._text_overlay is not None
            and self._text_active
            and self._text_overlay.content
        ):
            x = _raw_to_relative(self._text_overlay.raw_x)
            y = _raw_to_relative(self._text_overlay.raw_y)
            return TextOverlaySpec(
                content=self._text_overlay.content,
                x=x,
                y=y,
                **self._text_style_kwargs(),
            )
        return None

    def _text_style_kwargs(self) -> dict:
        """A `TextOverlaySpec` stílus-mezői a jelenlegi (#450, munkamenet-
        szintű, ini-be nem kerülő) beállításokból."""
        return {
            "fill_color": self._text_fill_color,
            "outline_color": self._text_outline_color,
            "outline_thickness": self._text_outline_thickness,
            "fill_enabled": self._text_fill_enabled,
            "opacity": self._text_opacity,
        }

    def _bump_revision(self) -> None:
        self._revision += 1
        self.revisionChanged.emit()

    def _bump_gpu_revision(self) -> None:
        """A gpuPrefixSource/gpuLutSource cache-bustere (#22) — KÜLÖN a
        `revisionChanged`-től, ld. a `gpuRevisionChanged` docsztringjét."""
        self._gpu_revision += 1
        self.gpuRevisionChanged.emit()


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _action_key(filter_name: str) -> str:
    """Szűrő-név → művelet-kulcs a Visszavonás-felirathoz (crop64→crop)."""
    key = filter_name.casefold()
    if key == "crop64":
        return "crop"
    return key
