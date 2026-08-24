"""A kollázs-panel vezérlője (#943) — az AppController szelete.

Szerződés: `docs/specs/kollazs-panel-ui-spec.md` **8.** (property-k,
slotok, jelzések, PONTOSAN ezekkel a nevekkel). A panel felülete külön
jegyekben épül; ez a réteg felület nélkül is teljes, és önmagában
tesztelhető.

Négy elv, ami végigmegy a fájlon:

1. **Minden vászonművelet a `collage/canvas.py` tiszta függvényeire épül**
   (rétegsorrend, bepattintó forgatás, keverés) — a logika egy helyen él, a
   `.cxf` mentése és a felület ugyanazt látja. Ez a fájl csak listát cserél.
2. **A képességek EGYETLEN forrásból jönnek**
   (`collage.themes.capabilities_for`): a `collageCapabilities` térkép a
   maszkot adja tovább a QML-nek. Témánkénti `if` sem itt, sem a QML-ben
   nem születik.
3. **Egy kódút a mentésre**: a „Kollázs létrehozása" és az „Asztali
   háttérkép" ugyanaz a `createCollage(asDesktopBackground)` — aki kettőt
   ír meg belőle, kétszer fogja karbantartani.
4. **A számolás tiszta modulokban van** (`collage_layout`, `collage_prefs`,
   `collage_output`); itt csak állapot, jelzés és a slot-felület marad.
5. **A HÁTTÉR külön szeletben él** (`collage_background`, #1009): a három
   mód, a szín és a háttérkép indexe. A háttérkép a kollázs SAJÁT képeinek
   egyike — ezért kellett a `_set_nodes`-ba egy visszakötés
   (`_sync_background_index`), hogy a hivatkozás sose maradjon törött.
6. **A MENTÉS külön szeletben él** (`collage_save.CollageSaveMixin`, #949):
   a cím, a célfájl, a folyamatjelzés, a megszakítás és a piszkozat. A
   `CollageMixin` abból örököl, tehát a spec 8. szakaszának szerződése
   kívülről EGY objektum marad — a vágás a fájlméret miatt kellett (a
   nyolcadik jegy 1100 sor fölé vitte), nem az API miatt.

⚠️ **Névterek:** a `create_controller.CreateMixin` a `_collage_*` előtagot
már használja (`_collage_seed`, `_collage_preview`). Ez a szelet ezért
mindenhol `_collage_panel_*` mezőneveket használ — a kettő ugyanabban az
`AppController`-ben él majd, és egy néma felülírás a régi Kollázs-menüt
törné el.
"""

from __future__ import annotations

import threading
from collections.abc import Sequence
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot
from PySide6.QtGui import QColor, QGuiApplication

from picasapy.collage import canvas
from picasapy.collage.fitting import MsvcRandom
from picasapy.collage.page_formats import (
    FALLBACK_SCREEN_RATIO,
    ORIENTATIONS,
    is_known_format,
    page_ratio,
)
from picasapy.collage.themes import (
    BORDER_THEMES,
    COLLAGE_THEMES,
    CONTACTSHEET,
    MULTIEXP,
    NOBORDER,
    WHITEBORDER,
    capabilities_for,
    capability_map,
)

from . import collage_layout as layout
from . import collage_prefs as prefs
from .collage_background import BACKGROUND_MODES, CollageBackgroundMixin
from .collage_model import (
    CollageNode,
    CollageNodeModel,
    group_bounds,
    initial_node_width,
    pictures_of,
    selected_indices,
    with_pictures,
    with_pictures_swapped,
    with_selection,
)
from .collage_save import CollageSaveMixin
from .collage_shadow import CollageShadowMixin

#: A kimeneti mappa beállítás-kulcsa — a `collage_prefs`-ből átemelve, hogy a
#: felület és a teszt EGY nevet lásson.
COLLAGE_OUTPUT_DIR_KEY = prefs.OUTPUT_DIR_KEY


class CollageMixin(CollageSaveMixin, CollageBackgroundMixin, CollageShadowMixin):
    """A kollázs-lap állapota és parancsai — a spec 8. szakasza."""

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
    collageFrameCenterChanged = Signal()
    collageClipCountChanged = Signal()
    collageDirtyChanged = Signal()
    collageCapabilitiesChanged = Signal()

    # -- lusta állapot -----------------------------------------------------

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
        # a legutóbb kiírt kollázs útvonala — ebből lesz a „Meglévő cseréje"
        # ága (spec 9.2). Üres szöveg = még nem mentettük ezt a kollázst.
        self._collage_panel_saved_path = ""
        # a megszakítás EGYETLEN jelzője. Esemény, nem bool: a háttérszál
        # olvassa, a felület írja, és a `threading.Event` pont ezt a
        # találkozást teszi biztonságossá zár nélkül.
        self._collage_panel_cancel = threading.Event()
        # a legutóbb kiadott százalék — a megszakítás ezzel tudja a
        # folyamatjelzőt a HELYÉN hagyni, miközben a címét „leállítás"-ra írja
        self._collage_panel_percent = 0

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

    # -- property-k (8.1) --------------------------------------------------

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

    @Property(int, notify=collageFrameCenterChanged)
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

    # -- a húzás közbeni feliratok (7.4) -----------------------------------
    #
    # A két formázó a `collage/canvas.py`-ban KÉSZ; ez a két slot csak
    # átjáró a QML felé. Nem véletlenül nem a felület számol: a szög kiírása
    # előjelet vált (#921 `fchs`), a kerekítés pedig `floor(x + 0,5)` és nem
    # a JavaScript `Math.round`-ja — két apró eltérés, amit egy párhuzamos
    # megvalósítás garantáltan elvét.

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

    # -- a lap megnyitása és bezárása (8.2) --------------------------------

    def _title_from_sources(self, sources) -> str:
        """A közös FORRÁSMAPPA neve — ez lesz a kimeneti fájl neve (9.1).

        Több mappából érkező kijelölésnél nincs egy címe a kollázsnak, tehát
        üres szöveget adunk, és a „kollázs" tartalékra esünk. Kitalált,
        „Nyaralás + 2 másik mappa" jellegű nevet nem gyártunk."""
        mappak = {Path(source.path).parent for source in sources if source.path}
        if len(mappak) != 1:
            return ""
        return next(iter(mappak)).name

    @Slot(list)
    def openCollage(self, rows) -> None:
        """A kollázs-lap megnyitása a megadott rács-sorokkal."""
        self._ensure_collage_panel()
        self._collage_panel_frame_center = -1
        self._set_saved_path("")
        sources = self._sources_from_rows(rows)
        self.setCollageTitle(self._title_from_sources(sources))
        self._relayout(sources, dirty=False)
        self.collageFrameCenterChanged.emit()
        if not self._collage_panel_open:
            self._collage_panel_open = True
            self.collageOpenChanged.emit()

    @Slot()
    def closeCollage(self) -> None:
        """A lap bezárása. A mentetlen módosítás kérdése a felületé (9.2)."""
        self._ensure_collage_panel()
        self._set_nodes((), dirty=False)
        self._set_dirty(False)
        if self._collage_panel_open:
            self._collage_panel_open = False
            self.collageOpenChanged.emit()

    def _sources_from_rows(self, rows) -> tuple[layout.CollageSource, ...]:
        """A rács-sorokból kép-források (a fotólista a host-controlleré)."""
        photos = getattr(getattr(self, "_photos", None), "photos", ())
        return layout.sources_from_photos(photos, rows)

    def _current_sources(self) -> tuple[layout.CollageSource, ...]:
        """A kollázs jelenlegi képei forrásként — a CSOMÓPONTOKBÓL.

        Külön forrás-listát tartani hibaforrás: a keverés és a csere a
        képeket a rések között mozgatja, tehát egy párhuzamosan vezetett
        lista pár művelet után más sorrendben állna, mint a vászon.

        ⚠️ #989: a kép oldalarányát a csomópont `aspect` mezője őrzi, NEM a
        `width / height` hányados — a rácsos témák CELLÁBA vágnak, ott a
        doboz a celláé."""
        return tuple(
            layout.CollageSource(node.path, node.caption, node.aspect)
            for node in self._nodes()
        )

    def _relayout_for_page_shape(self) -> None:
        """Újraszámolás a lap ALAKJÁNAK változása után (#991).

        A `setCollageFormat` és a `setCollageOrientation` eddig csak a lap
        arányát cserélte ki — a kártyák a régi helyükön maradtak, tehát
        kilógtak, összetorlódtak, vagy nagy üres rész maradt. A
        `setCollageTheme` már ma is helyesen újraszámol.

        Az eredetiben ezt a képesség-maszk **1. bitje** kapcsolja
        (`0x0087e960`, a kapcsolók a `0x00839f07` és a `0x0083a201` címen;
        spec 2.), és a rácsos témák pakolói eleve a lap arányából dolgoznak
        — mindkét ágon újraszámolás következik.

        ⚠️ A kézi elrendezés ilyenkor ELVESZIK. Ez az eredeti viselkedése
        (ugyanaz, mint téma-váltásnál, spec 5.), és nincs értelme
        megőrizni: a régi helyek a RÉGI lap alakjához tartoztak.

        A `dirty` jelző igazra vált — a `_relayout(dirty=True)` állítja be,
        ezért itt külön `_set_dirty` nem kell."""
        self._relayout(self._current_sources(), dirty=True)

    def _relayout(
        self, sources: Sequence[layout.CollageSource], *, dirty: bool
    ) -> None:
        """A csomópontok újraszámolása a TÉMA pakolójával (#989).

        A kézi szerkesztés ilyenkor ELVESZIK — ez az eredeti viselkedése
        téma-váltásnál és visszaállításnál (spec 5.), nem hiba. A
        képkockaközéppont indexe a pakolás UTÁN igazodik: a hangsúlyos kép a
        legfelső rétegbe, tehát a lista végére kerül."""
        self._set_nodes(
            layout.laid_out(
                sources,
                self.collagePageRatio,
                self._collage_panel_border,
                theme=self._collage_panel_theme,
                spacing=self._collage_panel_spacing,
                frame_center=self._collage_panel_frame_center,
                seed=self._collage_panel_seed,
            ),
            dirty=dirty,
        )
        self._set_frame_center(
            layout.frame_center_after(
                self._collage_panel_theme,
                self._collage_panel_frame_center,
                len(self._nodes()),
            )
        )
        self._set_dirty(dirty)

    def _set_frame_center(self, index: int) -> None:
        """A képkockaközéppont beállítása; a jelzés csak valódi változásnál."""
        self._ensure_collage_panel()
        if self._collage_panel_frame_center == index:
            return
        self._collage_panel_frame_center = index
        self.collageFrameCenterChanged.emit()

    # -- beállítás-slotok (8.2) --------------------------------------------

    @Slot(str)
    def setCollageTheme(self, key: str) -> None:
        """Téma-váltás. A kézi elrendezés ilyenkor ÚJRASZÁMOLÓDIK (a maszk
        1. bitje, spec 5.) — az eredeti sem kérdez rá."""
        self._ensure_collage_panel()
        if key not in COLLAGE_THEMES or key == self._collage_panel_theme:
            return
        self._collage_panel_theme = key
        self._get_settings().setValue(prefs.THEME_KEY, key)
        self.collageThemeChanged.emit()
        self.collageCapabilitiesChanged.emit()
        capabilities = self._capabilities()
        if key == CONTACTSHEET:
            # A valódi AI6 alap-Indexképe fehér szegélyes. A választó ettől
            # még aktív: a felhasználó a témaváltás UTÁN felülírhatja.
            self._collage_panel_border = WHITEBORDER
            self.collageBorderChanged.emit()
        if not self._collage_panel_shadows_explicit:
            self._collage_panel_shadows = capabilities.shadow_default
        self.collageShadowsChanged.emit()
        if not capabilities.selection:
            self._set_nodes(with_selection(self._nodes(), ()), dirty=False)
        if self._nodes():
            self._relayout(self._current_sources(), dirty=True)

    @Slot(str)
    def setCollageBorder(self, key: str) -> None:
        """Képkeret — a KIJELÖLTEKRE, ha van kijelölés; egyébként mindenkire."""
        self._ensure_collage_panel()
        if key not in BORDER_THEMES:
            return
        self._collage_panel_border = key
        self.collageBorderChanged.emit()
        nodes = self._nodes()
        if not nodes:
            return
        selection = selected_indices(nodes) or range(len(nodes))
        self._set_nodes(layout.replaced_many(nodes, selection, border=key))

    @Slot(float)
    def setCollageSpacing(self, value: float) -> None:
        """A „Rács vastagsága" csúszka 0…1 értéke (nem képpont!)."""
        self._ensure_collage_panel()
        spacing = min(1.0, max(0.0, float(value)))
        if spacing != self._collage_panel_spacing:
            self._collage_panel_spacing = spacing
            self.collageSpacingChanged.emit()
            # #1121: a térköz a PAKOLÁS bemenete, nem csak a rajzolásé — a
            # rácsos témák cellamérete tőle függ. Enélkül a vászon a RÉGI
            # elrendezést mutatta, és a felhasználó azt látta, hogy a
            # csúszka nem csinál semmit („hiába állítom be"). A
            # `setCollageFormat`/`setCollageOrientation` ugyanígy rendez újra.
            self._relayout_for_page_shape()
        self._apply_zero_spacing_shadow_rule()

    def _apply_zero_spacing_shadow_rule(self) -> None:
        """Spec 5./1.: ha a térköz-csúszka LÁTSZIK és az értéke 0, az
        árnyék-jelölő BEkapcsol (nem tiltódik le) — nulla térköznél az árnyék
        az egyetlen, ami elválasztja egymástól a képeket.

        Ez ÁLLAPOT-szabály, nem esemény: akkor is érvényesül, ha a csúszka
        már eddig is nullán állt."""
        if self._collage_panel_spacing == 0.0 and self._capabilities().spacing:
            self.setCollageShadows(True)

    @Slot(bool)
    def setCollageShadows(self, on: bool) -> None:
        self._ensure_collage_panel()
        wanted = bool(on) and self._capabilities().shadow
        self._collage_panel_shadows_explicit = True
        self._get_settings().setValue(
            prefs.SHADOWS_KEY, "true" if wanted else "false"
        )
        if wanted == self._collage_panel_shadows:
            return
        self._collage_panel_shadows = wanted
        self.collageShadowsChanged.emit()
        self._set_dirty(True)

    @Slot(bool)
    def setCollageCaptions(self, on: bool) -> None:
        self._ensure_collage_panel()
        wanted = bool(on)
        self._get_settings().setValue(
            prefs.CAPTIONS_KEY, "true" if wanted else "false"
        )
        if wanted == self._collage_panel_captions:
            return
        self._collage_panel_captions = wanted
        self.collageCaptionsChanged.emit()
        self._set_dirty(True)

    @Slot(str)
    def setCollageOrientation(self, kind: str) -> None:
        self._ensure_collage_panel()
        if kind not in ORIENTATIONS or kind == self._collage_panel_orientation:
            return
        self._collage_panel_orientation = kind
        self._get_settings().setValue(prefs.ORIENTATION_KEY, kind)
        self.collageOrientationChanged.emit()
        self.collagePageRatioChanged.emit()
        self._relayout_for_page_shape()

    @Slot(str)
    def setCollageFormat(self, key: str) -> None:
        self._ensure_collage_panel()
        if not is_known_format(key) or key == self._collage_panel_format:
            return
        self._collage_panel_format = key
        self._get_settings().setValue(prefs.FORMAT_KEY, key)
        self.collageFormatKeyChanged.emit()
        self.collagePageRatioChanged.emit()
        self._relayout_for_page_shape()

    def _single_selected_index(self) -> int:
        """A pontosan egy kijelölt csomópont INDEXE, vagy −1 + kérés a felület
        felé. A „Beállítás háttérként", a „Megjelenítés és szerkesztés" és a
        „Beállítás képkockaközéppontként" mind egy képet vár (spec 4.4).

        Külön az indexre (#1009): a háttérnek épp az index kell, a másik két
        hívónak a csomópont — a kijelölés SZABÁLYA viszont egy helyen él."""
        selection = selected_indices(self._nodes())
        if len(selection) != 1:
            self.collageNeedsSelection.emit()
            return -1
        return selection[0]

    def _single_selected(self) -> CollageNode | None:
        """A pontosan egy kijelölt csomópont, vagy `None`."""
        index = self._single_selected_index()
        return None if index < 0 else self._nodes()[index]

    # -- kijelölés (8.2) ---------------------------------------------------

    @Slot(list)
    def setCollageSelection(self, indices) -> None:
        self._ensure_collage_panel()
        wanted = indices if self._capabilities().selection else ()
        self._set_nodes(with_selection(self._nodes(), wanted or ()), dirty=False)

    @Slot()
    def selectAllNodes(self) -> None:
        self.setCollageSelection(list(range(len(self._nodes()))))

    @Slot()
    def selectNoNodes(self) -> None:
        self.setCollageSelection([])

    @Slot()
    def removeSelectedNodes(self) -> None:
        """A kijelöltek kivétele (Del). Minden kép eltávolítható — a mentés
        ilyenkor „Mentés mellőzve" üzenettel áll meg."""
        nodes = self._nodes()
        selection = selected_indices(nodes)
        if not selection:
            return
        self._set_nodes(canvas.remove_at(nodes, selection))

    # -- vászon-manipuláció (8.2) ------------------------------------------

    @Slot(int, float, float)
    def moveNode(self, index: int, cx: float, cy: float) -> None:
        """Egy csomópont áthelyezése — a középpont LAPEGYSÉGBEN."""
        nodes = self._nodes()
        if not 0 <= index < len(nodes):
            return
        self._set_nodes(
            layout.replaced_at(nodes, index, center_x=float(cx), center_y=float(cy))
        )

    @Slot(int, float, float)
    def transformNode(self, index: int, scale: float, theta: float) -> None:
        """Méretezés + forgatás EGY fogantyúval (7.4).

        A `scale` a kollázs ALAPMÉRETÉHEZ képest szól (1,0 = a kezdő méret),
        ahogy a húzás közbeni „Méretarány: %d%%" felirat is
        (`canvas.scale_caption_percent`). A kép oldalaránya megmarad."""
        nodes = self._nodes()
        if not 0 <= index < len(nodes) or float(scale) <= 0.0:
            return
        node = nodes[index]
        width = float(scale) * initial_node_width(len(nodes))
        self._set_nodes(
            layout.replaced_at(
                nodes,
                index,
                width=width,
                height=width * node.height / node.width,
                theta=float(theta),
            )
        )

    @Slot(int, int)
    def swapNodes(self, a: int, b: int) -> None:
        """Egy képet a másikra ejtve CSERÉLNEK: a fogadó rés mérete, kerete
        és szöge marad, csak a kép költözik."""
        nodes = self._nodes()
        if not (0 <= a < len(nodes) and 0 <= b < len(nodes)) or a == b:
            return
        self._set_nodes(with_pictures_swapped(nodes, a, b))

    @Slot(int)
    def raiseNodeToTop(self, index: int) -> None:
        """Alt+húzás: a csomópont a legfelső rétegbe.

        Ha MÁR a legfelső (a lista végén áll), semmi nem történik — sem a
        modell, sem a „piszkos" jelző nem változik."""
        nodes = self._nodes()
        if not 0 <= index < len(nodes) or index == len(nodes) - 1:
            return
        self._set_nodes(canvas.move_to_top(nodes, [index]))

    @Slot()
    def moveSelectionTop(self) -> None:
        self._move_selection(canvas.move_to_top)

    @Slot()
    def moveSelectionUp(self) -> None:
        self._move_selection(canvas.move_up)

    @Slot()
    def moveSelectionDown(self) -> None:
        self._move_selection(canvas.move_down)

    @Slot()
    def moveSelectionBottom(self) -> None:
        self._move_selection(canvas.move_to_bottom)

    def _move_selection(self, operation) -> None:
        """A négy rétegsorrend-parancs közös törzse — a `canvas.py`-ból.

        A kijelölés a csomópont `selected` mezőjében él, ezért a lista
        átrendezésével MAGÁTÓL követi a képet; nincs mit újraszámolni."""
        nodes = self._nodes()
        selection = selected_indices(nodes)
        if not selection:
            return
        self._set_nodes(operation(nodes, selection))

    @Slot(str)
    def snapRotation(self, command: str) -> None:
        """A négy bepattintó forgatás (`snap_12`/`snap_3`/`snap_6`/`snap_9`).

        ⚠️ A `snap_9` **−90,0 fokot** tárol (nem 270-et): a `.cxf`-be
        −1,570796 kerül, különben a windowsos Picasával az oda-vissza olvasás
        elcsúszna. Az értéket a `canvas.snap_theta` adja."""
        nodes = self._nodes()
        selection = selected_indices(nodes)
        if not selection:
            self.collageNeedsSelection.emit()
            return
        if not self._capabilities().rotate:
            return
        try:
            theta = canvas.snap_theta(command)
        except ValueError:
            return
        self._set_nodes(layout.replaced_many(nodes, selection, theta=theta))

    # -- véletlenszerűsítés (8.2) ------------------------------------------

    @Slot()
    def shufflePictures(self) -> None:
        """„Képek összekeverése" (`rand_order`): a KÉPEK cserélnek helyet, a
        rések (méret, keret, szög) maradnak — ugyanaz a szabály, mint az
        egymásra ejtésnél. A keverő a `canvas.shuffle_order`."""
        nodes = self._nodes()
        if len(nodes) < 2 or not self._capabilities().shuffle:
            return
        self._collage_panel_seed += 1
        pictures = canvas.shuffle_order(pictures_of(nodes), self._rng())
        self._set_nodes(with_pictures(nodes, pictures))

    @Slot()
    def scrambleCollage(self) -> None:
        """„Véletlenszerű kollázs" / „Képek szétszórása" (`rand_placement`):
        az ELRENDEZÉS sorsolódik újra, a képek sorrendje marad."""
        nodes = self._nodes()
        if not nodes or not self._capabilities().scramble:
            return
        self._collage_panel_seed += 1
        self._set_nodes(
            layout.rescattered(nodes, self.collagePageRatio, self._rng())
        )

    @Slot()
    def setFrameCenterFromSelection(self) -> None:
        """„Beállítás képkockaközéppontként" — a hangsúlyos központi kép.

        #989: a Képkockamozaiknál a beállítás UTÁN újrarendezünk, különben a
        parancsnak nem volna látható hatása — a hangsúlyos hely az
        elrendezésben születik meg (`picasa_render._FRAMEGRID_CENTER`). A
        többi téma pakolója nem olvassa ezt az értéket."""
        node = self._single_selected()
        if node is None:
            return
        self._set_frame_center(self._nodes().index(node))
        self._set_dirty(True)
        if layout.layout_uses_frame_center(self._collage_panel_theme):
            self._relayout(self._current_sources(), dirty=True)

    @Slot()
    def viewAndEditSelection(self) -> None:
        """„Megjelenítés és szerkesztés" — a képet a szerkesztő nyitja meg."""
        node = self._single_selected()
        if node is not None:
            self.collageEditRequested.emit(node.path)

    # -- klipek (8.2) ------------------------------------------------------

    @Slot(list)
    def addClips(self, rows) -> None:
        """A „+" gomb: további képek a kollázsba, a LEGFELSŐ rétegbe.

        ⚠️ #996: a SZÓRÁS csak a Képkupacnál helyes. A rácsos témáknál az
        új kép a kupac alapméretével, döntetlenül, véletlen helyre került —
        vagyis KILÓGOTT a rácsból. Ott a téma pakolójának kell újraszámolnia.

        A megkülönböztetés a téma `rotate` képessége (a szabad forgatás):
        ez EGYETLEN témánál áll, a Képkupacnál — pont annál, aminek az
        elrendezése eleve szórás, és amit a felhasználó kézzel rendez.
        A többinél a hely a pakoló dolga, nem a véletlené."""
        self._ensure_collage_panel()
        added = self._sources_from_rows(rows)
        if not added:
            return
        if not self._capabilities().rotate:
            self._relayout(self._current_sources() + tuple(added), dirty=True)
            return
        width = initial_node_width(len(self._nodes()) + len(added))
        centers = layout.scatter(len(added), self.collagePageRatio, self._rng())
        new_nodes = tuple(
            layout.node_for(source, center, width, self._collage_panel_border)
            for source, center in zip(added, centers, strict=True)
        )
        self._set_nodes((*self._nodes(), *new_nodes))

    @Slot(list)
    def deleteClips(self, rows) -> None:
        """A „–" gomb: a megadott klipek (csomópont-indexek) kivétele.

        ⚠️ #996: rácsos témánál a törölt kép helyén LYUK maradt — a rács
        hiányos lett. A Képkupacnál viszont a lyuk természetes: a csempék
        eleve átfedik egymást, és az újraszámolás elvenné a felhasználó
        kézi elrendezését. A határ ugyanaz, mint az `addClips`-nél: a téma
        `rotate` képessége."""
        self._ensure_collage_panel()
        nodes = self._nodes()
        indices = [int(r) for r in (rows or ()) if 0 <= int(r) < len(nodes)]
        if not indices:
            return
        maradek = canvas.remove_at(nodes, indices)
        if not self._capabilities().rotate and maradek:
            self._set_nodes(maradek, dirty=True)
            self._relayout(self._current_sources(), dirty=True)
            return
        self._set_nodes(maradek)

    @Slot()
    def resetCollage(self) -> None:
        """A kézi szerkesztés elvetése: elrendezés újra, a jelenlegi képekből."""
        self._ensure_collage_panel()
        self._collage_panel_seed += 1
        self._relayout(self._current_sources(), dirty=False)


__all__ = [
    "BACKGROUND_MODES",
    "COLLAGE_OUTPUT_DIR_KEY",
    "CollageMixin",
]
