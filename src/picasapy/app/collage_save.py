"""A kollázs-panel MENTÉSE és piszkozata (#949) — a spec 9. szakasza.

A `collage_controller.CollageMixin` szelete: minden, ami a **kimenet** körül
dől el — a cím, a célfájl, a folyamatjelzés, a megszakítás, a Kollázsok
albumba írt JPEG + `.cxf` pár, és a bezáráskori piszkozat.

Miért külön fájl: a #943-as vezérlő a nyolcadik jeggyel 1100 sor fölé nőtt.
A vágás nem önkényes — ez a szelet a panel ÁLLAPOTÁT csak olvassa
(csomópontok, téma, laparány), és kifelé ír: fájlt, jelzést, piszkozatot. A
`CollageMixin` ebből örököl, tehát a spec 8. szakaszának NÉV SZERINTI
szerződése (property-k, slotok, jelzések EGY objektumon) változatlan — a
#943 API-tesztje ezt közvetlenül állítja is.

## Két szabály, ami itt él

1. **Egy kódút a mentésre.** A „Kollázs létrehozása" és az „Asztali
   háttérkép" ugyanaz a `createCollage(asDesktopBackground)`; a „Meglévő
   cseréje" és az „Új létrehozása" sem külön ág, csak más paraméter,
   illetve egy előzetes `dropSavedCollagePath()`.
2. **Félkész fájl nem keletkezhet.** A megszakítást a rajzolás UTÁN, az
   írás ELŐTT kérdezzük meg, az írás maga pedig atomi (`collage_output`).

⚠️ **Névterek:** a `create_controller.CreateMixin` a `_collage_*` előtagot
már használja, és a két szelet ugyanabban az `AppController`-ben él. Ezért
itt is `_collage_panel_*` mezőnevek állnak, és a piszkozat mappáját a
`_collage_panel_draft_dir()` adja — a `CreateMixin._collage_draft_dir`
NEVÉHEZ nem nyúlunk, mert egy néma felülírás a régi Kollázs-menüt törné el.
"""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.collage.autosave import read_autosave, write_autosave
from picasapy.collage.draft import nodes_from_project, project_from_nodes
from picasapy.collage.page_formats import ORIENTATIONS
from picasapy.collage.themes import COLLAGE_THEMES, MULTIEXP

from . import collage_output as output
from . import collage_prefs as prefs
from .collage_model import CollageNode
from .worker_thread import BackgroundWorkerMixin

#: Az oldalformátum-egyezés tűrése az asztali háttérképnél — a képernyő
#: aránya ritkán egyezik bitre a menü tételével.
_RATIO_TOLERANCE = 0.01

logger = logging.getLogger(__name__)


class CollageSaveMixin(BackgroundWorkerMixin):
    """A kollázs kimenete, folyamatjelzése és piszkozata (spec 9.).

    Az állapotát a  hozza létre — a
    panel egyetlen, lusta inicializálója, hogy ne legyen két félig kész
    állapot ugyanarra a lapra."""

    # -- jelzések (8.3) ----------------------------------------------------

    collageProgress = Signal(int, str)
    collageDone = Signal(str)
    collageFailed = Signal(str)
    collageNoImages = Signal()
    collageFormatMismatch = Signal()
    collageDraftSaved = Signal(str)
    #: #949 (spec 9.4): hány kép hiányzott a mentésből. A felület ebből írja
    #: ki a „%1 kép nem található…" mondatot; nulla hiánynál NEM szólal meg.
    collageMissingImages = Signal(int)
    #: #949 (spec 9.1): a felhasználó megszakította a mentést. Fájl ilyenkor
    #: nem keletkezik — a jelzés a folyamatjelző elrejtésének a horga.
    collageCanceled = Signal()
    #: Integrációs horog: a kész kép asztali háttérképnek szánva. A tényleges
    #: beállítás asztali környezettől függ (KDE/GNOME/labwc), ezért nem itt
    #: dől el — a jelzés a  UTÁN érkezik.
    collageDesktopBackgroundReady = Signal(str)

    collageTitleChanged = Signal()
    collageSavedPathChanged = Signal()

    # -- property-k (8.1) --------------------------------------------------

    @Property(str, notify=collageTitleChanged)
    def collageTitle(self) -> str:
        """A kollázs címe — ebből lesz a kimeneti fájl neve (spec 9.1).

        A `openCollage` a FORRÁSMAPPA nevéből tölti fel; egy album-alapú
        belépési pont (Projektek ▸ Kollázsok) az album címét adhatja a
        `setCollageTitle`-lel. Üresen a „kollázs" tartalék lép életbe."""
        self._ensure_collage_panel()
        return self._collage_panel_title

    @Property(str, notify=collageSavedPathChanged)
    def collageSavedPath(self) -> str:
        """A kollázs legutóbbi kimeneti fájlja, vagy üres szöveg.

        Ha nem üres, az újramentés a „Lecseréli a meglévőt, vagy újat hoz
        létre?" kérdéssel indul (spec 9.2) — a felület ebből tudja, hogy
        egyáltalán fel kell-e tennie."""
        self._ensure_collage_panel()
        return self._collage_panel_saved_path

    # -- a cím és a mentett útvonal (9.1, 9.2) -----------------------------

    @Slot(str)
    def setCollageTitle(self, title: str) -> None:
        """A kollázs címe (a kimeneti fájl neve lesz belőle)."""
        self._ensure_collage_panel()
        wanted = str(title or "")
        if wanted == self._collage_panel_title:
            return
        self._collage_panel_title = wanted
        self.collageTitleChanged.emit()

    def _set_saved_path(self, path: str) -> None:
        self._ensure_collage_panel()
        if path == self._collage_panel_saved_path:
            return
        self._collage_panel_saved_path = path
        self.collageSavedPathChanged.emit()

    @Slot(str)
    def setCollageSavedPath(self, path: str) -> None:
        """A kollázs meglévő kimeneti fájlja — a `.cxf`-ből nyitás horga.

        Spec 9.2: „ha a kollázs egy korábban létrehozottból készült", az
        újramentés a „Lecseréli a meglévőt, vagy újat hoz létre?" kérdéssel
        indul. A Projektek ▸ Kollázsok albumból megnyitó belépési pont (3.2)
        ezen a sloton adja át, melyik fájlból dolgozunk."""
        self._set_saved_path(str(path or ""))

    @Slot()
    def dropSavedCollagePath(self) -> None:
        """„Új létrehozása" (spec 9.2): a következő mentés ÚJ fájlba megy.

        Nem maga ment: a felület ezután hívja a `createCollage`-ot. Így a
        mentésnek továbbra is EGYETLEN kódútja van, ez csak leveszi róla a
        „van már fájlja" jelzőt."""
        self._set_saved_path("")

    @Slot()
    def cancelCollage(self) -> None:
        """A futó mentés megszakítása (spec 9.1).

        A jelzőt a háttérszál a rajzolás UTÁN, az írás ELŐTT kérdezi meg —
        félkész fájl így nem keletkezhet. Futó munka nélkül ártalmatlan.

        A folyamatjelző ilyenkor „Kollázs létrehozása... leállítás"-ra vált
        (`collage::cancelling`): a megszakítás nem azonnali, és a
        felhasználónak látnia kell, hogy a kérése megérkezett."""
        self._ensure_collage_panel()
        self._collage_panel_cancel.set()
        if self.backgroundWorkersRunning():
            self._emit_progress(
                self._collage_panel_percent,
                self.tr("Creating collage… shutting down"),
            )

    def _emit_progress(self, percent: int, text: str) -> None:
        """A folyamatjelző egyetlen kapuja — a százalék itt jegyződik meg."""
        self._collage_panel_percent = int(percent)
        self.collageProgress.emit(int(percent), text)

    # -- létrehozás (8.2, 9.1) ---------------------------------------------

    @Slot(bool)
    @Slot(bool, bool)
    @Slot(bool, bool, bool)
    def createCollage(
        self,
        asDesktopBackground: bool,  # noqa: N803 — a spec 8.2 neve
        ignoreFormatMismatch: bool = False,  # noqa: N803
        replaceExisting: bool = False,  # noqa: N803
    ) -> None:
        """A kollázs mentése — EGY kódút a két gombhoz (spec 8.2).

        `asDesktopBackground` esetén a formátum-eltérésre előbb
        figyelmeztetünk (9.1); a „Beállítás ennek ellenére" gomb ugyanezt a
        slotot hívja `ignoreFormatMismatch=True`-val.

        `replaceExisting` a „Meglévő cseréje" ága (9.2): a korábbi kimeneti
        fájlt írjuk felül, számozás nélkül. Az „Új létrehozása" ág nem külön
        kódút — a felület előbb a `dropSavedCollagePath()`-t hívja, és utána
        ugyanezt a slotot."""
        self._ensure_collage_panel()
        nodes = self._nodes()
        if not nodes:
            self.collageNoImages.emit()
            return
        if (
            asDesktopBackground
            and not ignoreFormatMismatch
            and abs(self.collagePageRatio - self._screen_ratio()) > _RATIO_TOLERANCE
        ):
            self.collageFormatMismatch.emit()
            return
        if not any(not node.missing for node in nodes):
            # 9.4: a kollázs minden képe eltűnt a lemezről — ez ugyanaz a
            # zsákutca, mint amikor mindet eltávolították, és a felület
            # ugyanazt a „Mentés mellőzve" üzenetet mutatja rá. Nyers
            # kivétel-szöveg semmiképp ne menjen ki a felhasználóhoz.
            self.collageNoImages.emit()
            return

        target = self._target_path(replaceExisting)
        self._collage_panel_cancel.clear()
        self._emit_progress(0, self._progress_text_initializing())
        self._start_background(
            self._render_worker,
            args=(
                output.render_nodes_of(nodes, theme=self._collage_panel_theme),
                self._render_settings(),
                target,
                bool(asDesktopBackground),
                # #1009: a háttérkép a GUI-szálon dől el — a háttérszál a
                # modellhez nem nyúlhat
                self._background_image_for_cxf(),
            ),
            name="picasapy-collage-panel",
        )

    def _progress_text_initializing(self) -> str:
        """A folyamatjelző első sora. A Többszörös exponálásnak SAJÁT szövege
        van (spec 9.1) — nem elrendez, hanem képeket vetít egymásra."""
        if self._collage_panel_theme == MULTIEXP:
            return self.tr("Stacking pictures")
        return self.tr("Creating collage… initializing")

    def _target_path(self, replace_existing: bool) -> Path:
        """A célfájl: a meglévő útvonal, vagy a cím alapján egy új név.

        „Meglévő cseréje" esetén az EREDETI útvonalat írjuk felül, számozás
        nélkül (spec 9.1 utolsó sora) — különben minden újramentés egy újabb
        `név1.jpg`-t hagyna a Kollázsok albumban."""
        if replace_existing and self._collage_panel_saved_path:
            return Path(self._collage_panel_saved_path)
        return output.output_path(
            output.output_dir(self._get_settings().value(prefs.OUTPUT_DIR_KEY)),
            self._collage_panel_title,
        )

    def _collage_output_width(self) -> int:
        """A kimeneti kép szélessége. Külön metódus, hogy a teszt kisebb
        vásznon dolgozhasson: az éles 5120 képpont egy tesztben másodperceket
        és tíz-megabájtos tömböket jelentene, holott az állítás a fájlnévről
        és a jelzésekről szól."""
        return output.output_width(self.collagePageRatio)

    def _render_settings(self):
        """A panel állapotából renderelő-beállítás (a színváltás a modulban)."""
        color = self._collage_panel_bg_color
        return output.render_settings(
            theme=self._collage_panel_theme,
            border=self._collage_panel_border,
            spacing=self._collage_panel_spacing,
            shadows=self._collage_panel_shadows,
            page_ratio=self.collagePageRatio,
            background_rgb=(color.red(), color.green(), color.blue()),
            frame_center=self._collage_panel_frame_center,
            seed=self._collage_panel_seed,
            width=self._collage_output_width(),
        )

    def _index_saved_collage(self, path: Path) -> None:
        """A mentett kollázs mappáját felvesszük az INDEXBE.

        ⚠️ Enélkül a kollázs SEHOL nem jelenik meg a bal hasábon, hiába
        tökéletes a `.picasa.ini`. A Projektek gyűjtemény lekérdezése
        (`index/project_folders.py`) így indul:

            SELECT path FROM folders WHERE has_ini = 1

        — vagyis csak a MÁR INDEXELT mappákon megy végig. A kollázs
        célmappája (`<Képek>/Picasa/Kollázsok`) viszont tipikusan egyetlen
        figyelt gyökér alatt sincs, tehát oda sem teljes újraindexeléssel,
        sem másképp nem kerül be. Mérve a valódi indexen: 68 mappa, egy sem
        a Kollázsok.

        A `sync_folder` gyökér-korlátja itt úgy teljesül, hogy a gyökér MAGA
        a célmappa — így csak ezt az egy mappát vesszük fel, a felhasználó
        figyelt gyökereihez nem nyúlunk.

        A hiba nem buktatja el a mentést: a kép már a lemezen van, és egy
        index-gond miatt nem mondjuk azt, hogy a mentés meghiúsult."""
        mappa = Path(path).parent
        try:
            from picasapy.index import open_index
            from picasapy.index.sync import sync_folder

            with open_index(self._db_path) as conn:
                sync_folder(conn, mappa, mappa)
        except Exception:  # noqa: BLE001 - az indexelés soha ne bukatassa a mentést
            logger.warning(
                "A mentett kollázs mappája nem került az indexbe: %s", mappa,
                exc_info=True,
            )

    def _render_worker(
        self, nodes, settings, target, wallpaper: bool, background_image: str
    ) -> None:
        """A háttérszál törzse — a `BackgroundWorkerMixin`-en fut (#430).

        A folyamatjelzés SZAKASZOS, nem képenkénti: a rajzoló
        (`collage/picasa_render.py`) nem ad képenkénti visszajelzést, és
        kitalálni egyet rosszabb volna, mint durvábban jelezni. A három
        szakasz — indulás, rajzolás kész, kiírva — a felhasználónak azt
        mondja meg, ami tényleg igaz."""
        self._emit_progress(10, self._progress_text_initializing())
        try:
            eredmeny = output.render_collage(
                nodes,
                settings,
                target,
                album_title=self._collage_panel_title,
                background_image=background_image,
                should_cancel=self._rendered_now_writing,
            )
        except (ValueError, OSError) as error:
            self.collageFailed.emit(str(error))
            return
        if eredmeny.canceled:
            self.collageCanceled.emit()
            return
        if eredmeny.path is None:
            self.collageFailed.emit(
                self.tr("None of the selected pictures could be read.")
            )
            return
        self._set_dirty(False)
        self._set_saved_path(str(eredmeny.path))
        self._index_saved_collage(eredmeny.path)
        if eredmeny.missing:
            # 9.4: a hiány nem hiba — a kollázs elkészült, de a felhasználó
            # tudja meg, hogy hány kép maradt ki belőle
            self.collageMissingImages.emit(len(eredmeny.missing))
        self._emit_progress(100, self.tr("The collage is ready (click here)"))
        self.collageDone.emit(str(eredmeny.path))
        if wallpaper:
            self.collageDesktopBackgroundReady.emit(str(eredmeny.path))

    def _rendered_now_writing(self) -> bool:
        """A rajzolás kész, jön a kiírás — és közben: megszakították-e?

        Ez a `render_collage` `should_cancel` horga, és SZÁNDÉKOSAN kettős
        feladatú: a rajzoló pontosan egyszer, a két szakasz HATÁRÁN kérdezi
        meg. Ez az egyetlen pillanat, amiről a vezérlő biztosan tudja, hogy a
        munka nagyja megvan — tehát ez az egyetlen hely, ahol a 90%-ot
        őszintén ki lehet írni. Két külön horog ugyanide kötve csak
        látszatra volna tisztább."""
        self._emit_progress(90, self._progress_text_initializing())
        return self._collage_panel_cancel.is_set()

    # -- piszkozat (3.3, 9.) -----------------------------------------------

    def _collage_panel_draft_dir(self) -> Path:
        """A piszkozat mappája: a „Kollázsok" album.

        ⚠️ A név szándékosan `_collage_panel_*`: a `CreateMixin` a
        `_collage_draft_dir` nevet MÁR használja, és a két szelet ugyanabban
        az `AppController`-ben él — az azonos név néma felülírás volna."""
        return output.output_dir(self._get_settings().value(prefs.OUTPUT_DIR_KEY))

    @Slot()
    def saveCollageDraft(self) -> None:
        """„Piszkozat mentése" (spec 3.3): a vászon `.cxf`-ként a lemezre.

        Csomópont nélkül NEM ír: egy üres piszkozat visszaállítva üres lapot
        adna, ami rosszabb annál, mintha nem ajánlanánk fel semmit. A hiba
        naplózott, de nyelt — a piszkozat baja sosem viheti el a
        felhasználó kollázsát."""
        self._ensure_collage_panel()
        nodes = self._nodes()
        if not nodes:
            return
        try:
            ut = write_autosave(
                self._collage_panel_draft_dir(),
                project_from_nodes(
                    output.render_nodes_of(nodes, theme=self._collage_panel_theme),
                    self._render_settings(),
                    album_title=self._collage_panel_title,
                    background_image=self._background_image_for_cxf(),
                ),
            )
        except (OSError, ValueError) as hiba:
            logger.warning("A kollázs-piszkozat nem írható: %s", hiba)
            return
        self._get_settings().setValue(prefs.AUTOSAVE_KEY, str(ut))
        self.collageDraftSaved.emit(str(ut))

    @Slot()
    def restoreCollageDraft(self) -> None:
        """A piszkozat visszatöltése — a lap UGYANAZT a vásznat mutatja.

        A téma, az árnyék, a képfeliratok és a tájolás a `.cxf`-ből jönnek,
        de a mezőket KÖZVETLENÜL állítjuk: a `setCollageTheme` újraszámolná
        az elrendezést, és pont a visszaállítandó kézi helyeket dobná el.

        Az oldalFORMÁTUM nem áll vissza (a `.cxf` arányt tárol, nem
        menü-kulcsot) — a lap alakja a tájolásból és a jelenlegi formátumból
        áll össze. A csomópontok arányosan érkeznek, tehát a kép a lapon
        marad akkor is, ha a formátum közben más lett."""
        self._ensure_collage_panel()
        projekt = read_autosave(self._collage_panel_draft_dir())
        if projekt is None:
            return
        if projekt.theme in COLLAGE_THEMES:
            self._collage_panel_theme = projekt.theme
            self.collageThemeChanged.emit()
            self.collageCapabilitiesChanged.emit()
        if projekt.orientation in ORIENTATIONS:
            self._collage_panel_orientation = projekt.orientation
            self.collageOrientationChanged.emit()
            self.collagePageRatioChanged.emit()
        self._collage_panel_shadows = bool(projekt.shadows)
        self._collage_panel_shadows_explicit = True
        self.collageShadowsChanged.emit()
        self._collage_panel_captions = bool(projekt.captions)
        self.collageCaptionsChanged.emit()
        if projekt.album_title:
            self.setCollageTitle(projekt.album_title)

        self._set_nodes(
            _panel_nodes_of(nodes_from_project(projekt)), dirty=False
        )
        self._set_dirty(False)
        self._set_saved_path("")
        if not self._collage_panel_open:
            self._collage_panel_open = True
            self.collageOpenChanged.emit()



def _panel_nodes_of(nodes) -> tuple[CollageNode, ...]:
    """Rajzoló-csomópontok → a panel modell-csomópontjai.

    Az `output.render_nodes_of` megfordítása: a kijelölés (a modell mezője) a
    visszatöltésnél mindig üres, a kitöltés-mód (a rajzoló mezője) pedig a
    témából él tovább — egyik sem utazik a `.cxf`-ben.

    ⚠️ #989: a KÉP oldalarányát (`aspect`) a `.cxf` sem tárolja, ezért a
    csomópont dobozából vesszük. A Képkupacnál, az Indexképnél és a
    Többszörös exponálásnál ez PONTOS (ott a doboz a képé), a rácsos
    témáknál viszont a CELLA aránya — a visszatöltött kollázs egy későbbi
    téma-váltásnál ilyenkor közelítő arányokkal rendez újra. A képfájlok
    fejlécének beolvasása pontos volna, de 350 képnél a visszatöltést
    érezhetően lassítaná; ezt a cserét tudatosan vállaljuk."""
    return tuple(
        CollageNode(
            path="" if node.path is None else str(node.path),
            center_x=node.center_x,
            center_y=node.center_y,
            width=node.width,
            height=node.height,
            theta=node.theta,
            border=node.border,
            caption=node.caption,
            missing=node.missing,
            aspect=node.width / node.height,
        )
        for node in nodes
    )


__all__ = ["CollageSaveMixin"]
