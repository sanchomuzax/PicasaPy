"""A kollázsvezérlő állapota és QML-tulajdonságai."""

from __future__ import annotations

import threading
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QColor, QGuiApplication

from picasapy.collage import canvas
from picasapy.collage.fitting import MsvcRandom
from picasapy.collage.page_formats import FALLBACK_SCREEN_RATIO, page_ratio
from picasapy.collage.themes import MULTIEXP, NOBORDER, capabilities_for, capability_map

from . import collage_prefs as prefs
from .collage_model import (
    CollageNode,
    CollageNodeModel,
    group_bounds,
    initial_node_width,
    selected_indices,
)


class _CollageControllerStateMixin:
    """Lusta panelállapot, jelzések és a QML-property felület."""

    # -- jelzések (8.3) ----------------------------------------------------

    collageNeedsSelection = Signal()
    #: Integrációs horog: a „Megjelenítés és szerkesztés" a szerkesztőt kéri
    #: a megadott képre. A megnyitás a szerkesztő-szeleté, nem ezé.
    collageEditRequested = Signal(str)

    # -- property-jelzések (8.1) -------------------------------------------

    collageOpenChanged = Signal()
    collageThemeChanged = Signal()
    collageBorderChanged = Signal()
    collageSpacingChanged = Signal()
    collageShadowsChanged = Signal()
    collageCaptionsChanged = Signal()
    collageOrientationChanged = Signal()
    collageFormatKeyChanged = Signal()
    collagePageRatioChanged = Signal()
    collageSelectionChanged = Signal()
    collageClipCountChanged = Signal()
    collageDirtyChanged = Signal()
    collageCapabilitiesChanged = Signal()
    # ⚠️ A `collageRenderingChanged` (#1168) a `collage_save.py`-ban él, a
    # `collageProgress`/`collageDone` társaságában: a Property és a jelzése
    # egy fájlban kell legyen, különben a `notify=` nem hivatkozható.

    def _ensure_collage_panel(self) -> None:
        """Egyszeri állapot-inicializálás a megőrzött beállításokból.

        A `controller.py` FORRÓ FÁJL, ezért a szelet a saját állapotát maga
        hozza létre, nem az `__init__`-ben (a `TrayMixin`/`CreateMixin`
        mintája)."""
        if getattr(self, "_collage_panel_wired", False):
            return
        self._collage_panel_wired = True
        # #1021: az árnyék értesítője a MEGLÉVŐ négy jelzésre kötve — a
        # kötés a lusta indításkor születik, mint minden más állapot.
        self._wire_collage_shadow()
        stored = prefs.load_prefs(self._get_settings())

        self._collage_panel_open = False
        self._collage_panel_model = CollageNodeModel()
        self._collage_panel_frame_center = -1
        self._collage_panel_dirty = False
        self._collage_panel_seed = 1
        self._collage_panel_border = NOBORDER
        self._collage_panel_spacing = 0.0
        self._collage_panel_bg_mode = "solid"
        # #1009: a háttérkép a kollázs SAJÁT képeinek egyike, INDEXSZEL
        # hivatkozva — az eredeti is így teszi (`0x00830a00(this, index)`,
        # és `index == -1` esetén nincs háttérkép). −1 = nincs választva.
        self._collage_panel_bg_index = -1
        # #949: a kimeneti fájl neve ebből lesz (spec 9.1); üresen a
        # „kollázs" tartalék lép életbe
        self._collage_panel_title = ""
        # #1274: a MEGNYITOTT projekt album-mezői — a panelen nem
        # szerkeszthetők, de újramentéskor változatlanul mennek vissza.
        self._collage_panel_album_uid = ""
        self._collage_panel_album_id = ""
        self._collage_panel_album_date = ""
        # #1092: a MEGNYITOTT projekt `src → uid` párjai. A `.cxf`
        # csomópont-azonosítóit a vászon-csomópont nem hordozza (nincs rá
        # mezője), ezért a panel tartja őket egy leképezésben — így az
        # eredeti Picasa írta `<uid>` túléli az újramentést, ahelyett hogy
        # a származtatott sajátunkra cserélnénk.
        self._collage_panel_node_uids: dict[str, str] = {}
        #: #2923: a megnyitott projekt `src → scale` párjai — ami innen
        #: jön, az érintetlenül megy vissza a `.cxf`-be.
        self._collage_panel_node_scales: dict[str, float] = {}
        # a legutóbb kiírt kollázs útvonala — ebből lesz a „Meglévő cseréje"
        # ága (spec 9.2). Üres szöveg = még nem mentettük ezt a kollázst.
        self._collage_panel_saved_path = ""
        # #1387: a MOST NYITOTT piszkozat TÉNYLEGES mappája — ahol az
        # `autosave.cxf` ténylegesen fekszik, NEM feltétlenül a jelenleg
        # BEÁLLÍTOTT Kollázsok-mappa (`OUTPUT_DIR_KEY`). A kettő szétválhat,
        # ha a felhasználó a piszkozat mentése UTÁN átállítja a kimeneti
        # mappát: a takarítás enélkül a rossz (új) helyen keresné a régi
        # piszkozatot, és az árván maradna a réginél. `None` = nincs
        # ismert, ettől eltérő tényleges hely (friss panel, még nincs
        # piszkozat) — ilyenkor a beállított mappa a helyes válasz.
        self._collage_panel_draft_source_dir: Path | None = None
        # a megszakítás EGYETLEN jelzője. Esemény, nem bool: a háttérszál
        # olvassa, a felület írja, és a `threading.Event` pont ezt a
        # találkozást teszi biztonságossá zár nélkül.
        self._collage_panel_cancel = threading.Event()
        # a legutóbb kiadott százalék — a megszakítás ezzel tudja a
        # folyamatjelzőt a HELYÉN hagyni, miközben a címét „leállítás"-ra írja
        self._collage_panel_percent = 0
        # #1168 (spec 16.3): fut-e ÉPPEN a kollázs rajzolása. Ebből tudja a
        # FŐABLAK, hogy kiírja-e a „Várakozás a kollázs elkészítésére…"
        # sort (`CThumbUI::CreateCollageWait`). A folyamatjelző DOBOZ a
        # panelé; ez a jelző a könyvtárnézeté, ami közben is látszik.
        self._collage_panel_rendering = False

        self._collage_panel_theme = stored.theme
        self._collage_panel_format = stored.format_key
        self._collage_panel_orientation = stored.orientation
        self._collage_panel_captions = stored.captions
        self._collage_panel_shadows = stored.shadows
        self._collage_panel_shadows_explicit = stored.shadows_explicit
        color = QColor(stored.background_color)
        self._collage_panel_bg_color = (
            color if color.isValid() else QColor(prefs.DEFAULT_BACKGROUND)
        )

    def _capabilities(self):
        self._ensure_collage_panel()
        return capabilities_for(self._collage_panel_theme)

    def _nodes(self) -> tuple[CollageNode, ...]:
        self._ensure_collage_panel()
        return self._collage_panel_model.nodes

    def _set_nodes(self, nodes: Sequence[CollageNode], *, dirty: bool = True) -> None:
        """A csomópont-lista cseréje + a származtatott jelzések.

        Egyetlen kapu: minden művelet ezen megy át, így a „piszkos" jelző, a
        kijelölés és a klipszám sosem csúszhat el a modelltől."""
        self._ensure_collage_panel()
        before = self._collage_panel_model.nodes
        if tuple(nodes) == before:
            return
        count_changed = len(nodes) != len(before)
        # a háttérkép útvonala MÉG a csere előtt kell (#1009)
        background_path = self.collageBackgroundImage
        # #995: a Többszörös exponálás vászna KEVER, nem takar — a modell
        # ebből számolja a rétegsorrend szerinti átlátszatlanságot
        self._collage_panel_model.set_multi_exposure(
            self._collage_panel_theme == MULTIEXP
        )
        self._collage_panel_model.set_nodes(nodes)
        self._sync_background_index(background_path)
        self.collageSelectionChanged.emit()
        if count_changed:
            self.collageClipCountChanged.emit()
        if dirty:
            self._set_dirty(True)

    def _set_dirty(self, dirty: bool) -> None:
        self._ensure_collage_panel()
        if self._collage_panel_dirty == dirty:
            return
        self._collage_panel_dirty = dirty
        self.collageDirtyChanged.emit()

    def _rng(self) -> MsvcRandom:
        """Új véletlenforrás a jelenlegi magból (megismételhető elrendezés)."""
        return MsvcRandom(self._collage_panel_seed)

    def _screen_ratio(self) -> float:
        """A képernyő magasság / szélesség aránya („Jelenlegi megjelenítés"
        tétel és az asztali háttérkép formátum-ellenőrzése).

        Külön metódus, hogy a teszt (és egy több képernyős környezet későbbi
        kezelése) felül tudja írni; képernyő nélkül 16:9."""
        app = QGuiApplication.instance()
        screen = app.primaryScreen() if app is not None else None
        if screen is None:
            return FALLBACK_SCREEN_RATIO
        size = screen.size()
        if size.width() <= 0 or size.height() <= 0:
            return FALLBACK_SCREEN_RATIO
        return size.height() / size.width()

    @Property(bool, notify=collageOpenChanged)
    def collageOpen(self) -> bool:
        self._ensure_collage_panel()
        return self._collage_panel_open

    @Property(str, notify=collageThemeChanged)
    def collageTheme(self) -> str:
        self._ensure_collage_panel()
        return self._collage_panel_theme

    @Property(str, notify=collageBorderChanged)
    def collageBorder(self) -> str:
        self._ensure_collage_panel()
        return self._collage_panel_border

    @Property(float, notify=collageSpacingChanged)
    def collageSpacing(self) -> float:
        self._ensure_collage_panel()
        return self._collage_panel_spacing

    @Property(bool, notify=collageShadowsChanged)
    def collageShadows(self) -> bool:
        """Rajzolunk-e árnyékot. A téma tilthatja (a maszk 11. bitje)."""
        self._ensure_collage_panel()
        return self._collage_panel_shadows and self._capabilities().shadow

    @Property(bool, notify=collageCaptionsChanged)
    def collageCaptions(self) -> bool:
        self._ensure_collage_panel()
        return self._collage_panel_captions

    @Property(str, notify=collageOrientationChanged)
    def collageOrientation(self) -> str:
        self._ensure_collage_panel()
        return self._collage_panel_orientation

    @Property(str, notify=collageFormatKeyChanged)
    def collageFormatKey(self) -> str:
        self._ensure_collage_panel()
        return self._collage_panel_format

    @Property(float, notify=collagePageRatioChanged)
    def collagePageRatio(self) -> float:
        """A lap magasság / szélesség aránya — ebből él a lap alakja."""
        self._ensure_collage_panel()
        return page_ratio(
            self._collage_panel_format,
            self._collage_panel_orientation,
            screen_ratio=self._screen_ratio(),
        )

    @Property(QObject, constant=True)
    def collageNodes(self) -> CollageNodeModel:
        """A vászon modellje. A példány azonossága sosem változik — a QML
        kötése ezért maradhat állandó."""
        self._ensure_collage_panel()
        return self._collage_panel_model

    @Property(list, notify=collageSelectionChanged)
    def collageSelection(self) -> list:
        return list(selected_indices(self._nodes()))

    @Property("QVariantMap", notify=collageSelectionChanged)
    def collageGroupRect(self) -> dict:
        """A CSOPORT-ELEM téglalapja lapegységben; ÜRES térkép = nincs elem.

        #1170: a képesség-maszk 6. bitje a `collagepanel/groupnode`
        csomópontot külön overlay-rétegbe teszi a három rács-témánál. A
        téglalapot a `group_bounds` tiszta függvény adja — a vászon csak
        felszorozza a lapegységgel.

        A jelzés a `collageSelectionChanged`, és ez nem szűkítés: a
        `_set_nodes` MINDEN csomópont-változásnál elsüti, tehát a keret a
        mozgatást és a méretezést is követi.

        ⚠️ Üres térkép, nem `None`: a QML `undefined`-ra hasal el a
        `.width` olvasásakor (#305), üres `QVariantMap`-re nem."""
        bounds = group_bounds(self._nodes())
        if bounds is None:
            return {}
        x, y, width, height = bounds
        return {"x": x, "y": y, "width": width, "height": height}

    @property
    def collageFrameCenter(self) -> int:
        """A hangsúlyos középső kép indexe a Képkockamozaikban; −1 = nincs."""
        self._ensure_collage_panel()
        return self._collage_panel_frame_center

    @Property(int, notify=collageClipCountChanged)
    def collageClipCount(self) -> int:
        """A „Klipek (%1)" fülfelirat száma — a kollázs képeinek száma."""
        return len(self._nodes())

    @Property(bool, notify=collageDirtyChanged)
    def collageDirty(self) -> bool:
        self._ensure_collage_panel()
        return self._collage_panel_dirty

    @Property("QVariantMap", notify=collageCapabilitiesChanged)
    def collageCapabilities(self) -> dict:
        """A téma képesség-maszkja a QML-nek — EGYETLEN forrásból."""
        self._ensure_collage_panel()
        return capability_map(self._collage_panel_theme)

    @Property(float, notify=collageClipCountChanged)
    def collageBaseNodeWidth(self) -> float:
        """A csomópontok ALAPSZÉLESSÉGE lapegységben (spec 6.2).

        Ez a `transformNode` `scale` paraméterének 1,0-s viszonyítási pontja:
        a fogantyú (7.4) a lenyomáskor ebből számolja ki a kiinduló
        méretarányt (`node.width / collageBaseNodeWidth`). Enélkül a felület
        kénytelen volna az `initial_node_width` képletét megismételni — egy
        elváló másolat pedig pontosan az a néma hiba, amit a #947 kerülni
        akar."""
        return initial_node_width(len(self._nodes()))

    @Slot(float, result=int)
    def collageAngleCaption(self, theta: float) -> int:
        """A „Szög: %1" felirat értéke a `theta` radiánból."""
        return canvas.angle_caption_degrees(float(theta))

    @Slot(float, float, result=int)
    def collageScaleCaption(self, scale: float, base_scale: float) -> int:
        """A „Méretarány: %1%" felirat értéke; a lenyomás pillanatában 100."""
        if base_scale <= 0.0:
            return 100
        return canvas.scale_caption_percent(float(scale), float(base_scale))
