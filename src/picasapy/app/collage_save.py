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

import dataclasses
import os
import logging
from pathlib import Path

from PySide6.QtCore import Property, Qt, Signal, Slot
from PySide6.QtGui import QColor

from picasapy.collage.autosave import (
    discard_autosave,
    read_autosave,
    write_autosave,
)
from picasapy.collage import draft_placeholder, write_collage
from picasapy.collage.picasa_render import render_nodes
from picasapy.collage.cxf import read_cxf
from picasapy.collage.draft import nodes_from_project, project_from_nodes
from picasapy.collage.win_paths import decode_cxf_path
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

    #: **BELSŐ, szál-határon átmenő jelzések (#988/#999).** A háttérszál
    #: KIZÁRÓLAG ezeket emitálja, nyers adattal — az állapotírás, a
    #: fordítás (`tr`) és a NYILVÁNOS jelzések a rájuk kötött slotokban
    #: futnak, a fogadó (GUI-) szálon.
    #:
    #: Ok (#988 veremkiíratása): a rajzoló szál korábban maga írta a
    #: `_collage_panel_percent`-et és maga emitálta a nyilvános jelzéseket,
    #: miközben a GUI-szálon szemétgyűjtés futhat a PySide-burkolókon — ez
    #: a #430-as SIGSEGV-osztály. A minta a `busy_registry.py`-é: a
    #: szálhatárt EGY jelzés lépi át, a munka a fogadó szálán történik.
    _workerProgress = Signal(int, str)
    _workerOutcome = Signal(object)

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
        """A folyamatjelző egyetlen kapuja — a százalék itt jegyződik meg.

        ⚠️ CSAK a fogadó (GUI-) szálon hívható. A háttérszál a
        `_post_progress`-t használja (#988/#999)."""
        self._collage_panel_percent = int(percent)
        self.collageProgress.emit(int(percent), text)

    #: A háttérszálról küldhető folyamat-szövegek KULCSAI. A `tr()` hívása
    #: is a fogadó szálon történik (#988/#999) — a szál csak kulcsot küld.
    _PROGRESS_INITIALIZING = "initializing"
    _PROGRESS_READY = "ready"

    def _ensure_worker_bridge(self) -> None:
        """A belső híd-jelzések bekötése — SORBA ÁLLÍTOTT kapcsolattal.

        A GUI-szálon hívandó, a háttérszál indítása ELŐTT. Idempotens."""
        if getattr(self, "_worker_bridge_ready", False):
            return
        self._workerProgress.connect(
            self._on_worker_progress, Qt.ConnectionType.QueuedConnection
        )
        self._workerOutcome.connect(
            self._on_worker_outcome, Qt.ConnectionType.QueuedConnection
        )
        self._worker_bridge_ready = True

    def _post_progress(self, percent: int, key: str) -> None:
        """A HÁTTÉRSZÁL folyamatjelzése — csak egy jelzés, semmi más."""
        self._workerProgress.emit(int(percent), key)

    @Slot(int, str)
    def _on_worker_progress(self, percent: int, key: str) -> None:
        """A fogadó szálon: itt fordítunk és itt írjuk az állapotot."""
        if key == self._PROGRESS_READY:
            text = self.tr("The collage is ready (click here)")
        else:
            text = self._progress_text_initializing()
        self._emit_progress(percent, text)

    @Slot(object)
    def _on_worker_outcome(self, payload: dict) -> None:
        """A rajzolás eredményének feldolgozása — a fogadó szálon.

        Minden állapotírás és minden NYILVÁNOS jelzés itt történik; a
        háttérszál csak a nyers adatot adta át."""
        fajta = payload["fajta"]
        if fajta == "hiba":
            self.collageFailed.emit(payload["uzenet"])
            return
        if fajta == "olvashatatlan":
            self.collageFailed.emit(
                self.tr("None of the selected pictures could be read.")
            )
            return
        if fajta == "megszakitva":
            self.collageCanceled.emit()
            return
        ut = payload["ut"]
        self._set_dirty(False)
        self._set_saved_path(ut)
        self._index_saved_collage(Path(ut))
        # #1100: a piszkozat takarítása is a FOGADÓ szálon — a beállítás
        # írása (`QSettings`) és a jelzések ugyanabba a körbe tartoznak.
        self._discard_draft_after_render()
        if payload["hianyzo"]:
            # 9.4: a hiány nem hiba — a kollázs elkészült, de a felhasználó
            # tudja meg, hogy hány kép maradt ki belőle
            self.collageMissingImages.emit(payload["hianyzo"])
        self._emit_progress(100, self.tr("The collage is ready (click here)"))
        self.collageDone.emit(ut)
        if payload["hatterkep"]:
            self.collageDesktopBackgroundReady.emit(ut)

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
        self._ensure_worker_bridge()  # #988/#999: a GUI-szálon, a szál ELŐTT
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
        mappa = output.output_dir(
            self._get_settings().value(prefs.OUTPUT_DIR_KEY)
        )
        sajat = self._draft_placeholder_target(mappa)
        if sajat is not None:
            return sajat
        return output.output_path(mappa, self._collage_panel_title)

    def _draft_placeholder_target(self, mappa: Path) -> Path | None:
        """A SAJÁT helykitöltőnk, ha a véglegesítés azt írja felül (#1125).

        A tulajdonos jelentése: bezárás → újranyitás → „Létrehozás" után a
        PISZKOZAT-kép OTTMARADT, a kész kollázs pedig `L1.jpg` néven
        született. A #1072 szándéka az volt, hogy a helykitöltő lefoglalja a
        nevet — de a foglalás csak a NYITOTT panelen élt
        (`collageSavedPath`), bezárás után elveszett.

        **A felülírás MÉRT viselkedés**, nem használhatósági döntés: a
        tulajdonos valódi, EREDETI Picasa által készített Kollázsok
        mappájában 11 JPEG és 11 `.cxf` áll, és a párosítatlan JPEG-ek
        száma **NULLA**. Ha az eredeti a helykitöltőt meghagyná és mellé
        sorszámozna, ott pontosan olyan árva fájlok volnának, mint amilyet
        a tulajdonos most kapott. A `%s%lu` sorszámozás használatban van
        (AI → AI1 → AI2…), de csak KÜLÖN kollázsokra, ahol a nevet egy KÉSZ
        (`.cxf`-fel párosított) kollázs foglalja.

        ⚠️ A felismerés a piszkozat-NYILVÁNTARTÁSBÓL megy, nem a névből: a
        „nincs `.cxf` párja" IGAZ egy idegen JPEG-re is, amit a felhasználó
        tett a Kollázsok mappába — azt felülírni ADATVESZTÉS volna.

        ⚠️ **Ez az idegen-fájl védőág a MI döntésünk, nem az eredeti
        rekonstrukciója.** A 11 mintában ilyen eset NINCS, tehát nem tudjuk,
        mit tenne a Picasa egy idegen, `.cxf` nélküli JPEG-gel. Óvatosabb
        irányba tértünk el, szándékosan és kimondva.

        Három feltétel EGYÜTT: a nyilvántartott útvonal (a) létezik, (b) a
        célmappában van, és (c) nincs mellette `.cxf` — vagyis időközben nem
        vált kész kollázzsá."""
        jelolt = self._get_settings().value(prefs.PLACEHOLDER_KEY)
        if not jelolt:
            return None
        ut = Path(str(jelolt))
        if not ut.is_file() or ut.with_suffix(".cxf").exists():
            return None
        if os.path.normcase(str(ut.parent)) != os.path.normcase(str(mappa)):
            return None
        return ut

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
            # #1015: csak KÉP-módban — a szín- és az átlagszín-mód (#1004)
            # a `background` szín marad
            background_image=(
                self.collageBackgroundImage
                if self._collage_panel_bg_mode == "image"
                else ""
            ),
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
        self._post_progress(10, self._PROGRESS_INITIALIZING)
        try:
            eredmeny = output.render_collage(
                nodes,
                settings,
                target,
                album_title=self._collage_panel_title,
                background_image=background_image,
                format_key=self._collage_panel_format,
                should_cancel=self._rendered_now_writing,
            )
        except (ValueError, OSError) as error:
            self._workerOutcome.emit({"fajta": "hiba", "uzenet": str(error)})
            return
        if eredmeny.canceled:
            self._workerOutcome.emit({"fajta": "megszakitva"})
            return
        if eredmeny.path is None:
            self._workerOutcome.emit({"fajta": "olvashatatlan"})
            return
        self._workerOutcome.emit(
            {
                "fajta": "kesz",
                "ut": str(eredmeny.path),
                "hianyzo": len(eredmeny.missing),
                "hatterkep": bool(wallpaper),
            }
        )

    def _discard_draft_after_render(self) -> None:
        """A kész kollázs mellől ELTAKARÍTJUK a piszkozatot (#1100).

        ⚠️ Nem rendrakás: a valódi Picasa az ottfelejtett `autosave.cxf`-et
        **elárvult automentésként** ismeri fel, és a saját 640 × 480-as,
        egyszínű sötétszürke helykitöltőjét írja mellé `autosave.jpg` néven
        — a felhasználó Kollázsok mappájába. A tulajdonos ezt látta a
        v0.8.23-ban, és a mi kimenetünknek hitte.

        Vagyis a mi maradékunk SZEMETET GYÁRTAT a valódi Picasával. A
        piszkozat a véglegesítéssel betöltötte a szerepét.

        A beállításból is kivezetjük: ha csak a fájlt törölnénk, a program
        indításkor még mindig felajánlaná a helyreállítást, és a felhasználó
        egy nem létező munkát „állítana helyre".

        ⚠️ A már ott lévő, PICASA által írt `autosave.jpg`-hez NEM nyúlunk —
        az nem a mi fájlunk, a felhasználó mappájában van.

        A hiba nyelt: a kollázs ekkor már a lemezen van, és egy takarítási
        gond nem teheti kudarccá a mentést."""
        try:
            discard_autosave(self._collage_panel_draft_dir())
        except OSError as hiba:
            logger.warning("A piszkozat nem takarítható el: %s", hiba)
            return
        beallitas = self._get_settings()
        beallitas.remove(prefs.AUTOSAVE_KEY)
        # #1125: a helykitöltő szerepe is véget ért — a kész kollázs
        # foglalja a helyét. A jelölő itt szűnik meg, nem a fájl.
        beallitas.remove(prefs.PLACEHOLDER_KEY)

    def _rendered_now_writing(self) -> bool:
        """A rajzolás kész, jön a kiírás — és közben: megszakították-e?

        Ez a `render_collage` `should_cancel` horga, és SZÁNDÉKOSAN kettős
        feladatú: a rajzoló pontosan egyszer, a két szakasz HATÁRÁN kérdezi
        meg. Ez az egyetlen pillanat, amiről a vezérlő biztosan tudja, hogy a
        munka nagyja megvan — tehát ez az egyetlen hely, ahol a 90%-ot
        őszintén ki lehet írni. Két külön horog ugyanide kötve csak
        látszatra volna tisztább."""
        self._post_progress(90, self._PROGRESS_INITIALIZING)
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
                    format_key=self._collage_panel_format,
                ),
            )
        except (OSError, ValueError) as hiba:
            logger.warning("A kollázs-piszkozat nem írható: %s", hiba)
            return
        self._get_settings().setValue(prefs.AUTOSAVE_KEY, str(ut))
        self._write_draft_placeholder(nodes, ut.parent)
        self.collageDraftSaved.emit(str(ut))

    def _write_draft_placeholder(self, nodes, mappa: Path) -> None:
        """A piszkozat HELYKITÖLTŐ képe — ettől látszik a Kollázsok albumban.

        A tulajdonos jelentése: *„A friss képkollázs piszkozat mentése nem
        jelenik meg a PicasaPy és Picasa alatt sem."* Az eredeti a mentéskor
        AZONNAL ír egy képet a `.cxf` mellé (mérve a képernyőképéről:
        `AI10.jpg`, 640 × 453), és ettől jelenik meg a piszkozat.

        A kép a kollázs **végleges nevét** kapja — nem `autosave.jpg`-t. Ez
        egyben lefoglalja a nevet: a „Létrehozás" innentől a meglévő fájlt
        látja, és a felület felteszi a *„Lecseréli a meglévőt, vagy újat hoz
        létre?"* kérdést (spec 9.2), ahogy az eredeti is. Így a befejezés
        nem hagy maga után szemetet.

        ⚠️ A hiba **nyelt**: a piszkozat `.cxf`-je már a lemezen van, és egy
        helykitöltő baja nem viheti el a felhasználó munkáját. Naplózva
        viszont igen — a #1075 tanulsága, hogy a néma ág miatt vakon
        állunk."""
        if not nodes:
            return
        try:
            meglevo = self.collageSavedPath
            cel = (
                Path(meglevo)
                if meglevo
                else self._draft_placeholder_path(mappa)
            )
            szeles, magas = draft_placeholder.placeholder_size(
                self.collagePageRatio
            )
            beallitas = dataclasses.replace(
                self._render_settings(), width=szeles, height=magas
            )
            jelentes = render_nodes(
                output.render_nodes_of(nodes, theme=self._collage_panel_theme),
                beallitas,
            )
            kep = draft_placeholder.draw_draft_label(
                jelentes.image, self.tr("DRAFT")
            )
            write_collage(cel, kep, quality=output.JPEG_QUALITY)
        except Exception:  # noqa: BLE001 - a piszkozat baja nem vihet el munkát
            logger.warning(
                "A piszkozat helykitöltő képe nem írható (%s)", mappa, exc_info=True
            )
            return
        self._set_saved_path(str(cel))
        # #1125: JEGYEZZÜK FEL, melyik fájl a mi helykitöltőnk. A
        # véglegesítés csak ezt írhatja felül — a „nincs `.cxf` párja"
        # önmagában egy IDEGEN képre is igaz volna.
        self._get_settings().setValue(prefs.PLACEHOLDER_KEY, str(cel))
        self._index_saved_collage(cel)

    def _draft_placeholder_path(self, mappa: Path) -> Path:
        """A piszkozat helykitöltőjének célfájlja — ÚJRAÍRHATÓ, nem szaporodó.

        A tulajdonos szava: *„A »PISZKOZAT« felirat akkor jelenik meg …
        amikor a »Bezárás« gombot megnyomom … De csak addig van ott, amíg le
        nem menti."* — vagyis a piszkozatnak EGYETLEN képe van. Ha a
        visszaállítás után újra bezár, ugyanazt kell felülírnunk, különben
        minden körben új `Kollázs1.jpg`, `Kollázs2.jpg` keletkezne.

        A megkülönböztető a `.cxf` PÁR: a KÉSZ kollázs mellett ott áll a
        projektfájlja (#1002 ezen az egy jelen áll), a helykitöltő mellett
        nem — a piszkozat `.cxf`-je az `autosave.cxf`. Tehát ha a név
        szabad, vagy már a MI helykitöltőnk ül rajta, azt írjuk felül; ha
        egy kész kollázs foglalja, az `output_path` sorszámoz."""
        alap = mappa / f"{output.safe_stem(self._collage_panel_title)}.jpg"
        if not alap.exists() or not alap.with_suffix(".cxf").exists():
            return alap
        return output.output_path(mappa, self._collage_panel_title)

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
        mappa = self._collage_panel_draft_dir()
        projekt = read_autosave(mappa)
        if projekt is None:
            return
        self._apply_cxf_project(projekt, saved_path="")
        meglevo = self._draft_placeholder_path(mappa)
        if meglevo.exists():
            self._set_saved_path(str(meglevo))

    @Slot(str, result=bool)
    def hasCollageProject(self, image_path: str) -> bool:  # noqa: N802
        """Van-e a képnek `.cxf` párja — vagyis kollázs-e (#1002).

        A szerkesztő „Kollázs szerkesztése" gombja ezen látszik
        (`editpanel/editcollage`, `m_hidden`: alapból rejtett, csak
        kollázsnál jön elő). A tulajdonos szava: *„Ez a gomb mindig
        megjelenik, ha megnyitom a kollázst."* — tehát nem a létrehozás
        emléke kapcsolja be, hanem a fájl mellett álló projektfájl."""
        return self._collage_project_path(image_path) is not None

    @Slot(str)
    def openCollageProject(self, image_path: str) -> None:  # noqa: N802
        """A kész kollázs újranyitása SZERKESZTÉSRE (#1002).

        A tulajdonos jelentése a v0.8.17-ről: *„Jelenleg ennek hiányában
        nem szerkeszthető a kollázs."* — a kész képhez nem vezetett vissza
        út a panelra.

        A `saved_path` a MEGNYITOTT képre áll, tehát a „Létrehozás" a
        meglévő fájlt írja felül, nem újat számoz mellé: a felhasználó
        ugyanazt a kollázst szerkeszti tovább, nem másolatot készít."""
        utvonal = self._collage_project_path(image_path)
        if utvonal is None:
            return
        try:
            projekt = read_cxf(utvonal)
        except ValueError:
            logger.warning("A kollázs projektfájlja nem olvasható: %s", utvonal)
            self.collageFailed.emit(
                self.tr("The collage project file could not be opened.")
            )
            return
        self._ensure_collage_panel()
        self._apply_cxf_project(projekt, saved_path=str(image_path))

    def _collage_project_path(self, image_path: str) -> Path | None:
        """A képhez tartozó `.cxf`, ha van és olvasható fájl."""
        if not image_path:
            return None
        try:
            utvonal = Path(str(image_path)).with_suffix(".cxf")
        except (OSError, ValueError):  # pragma: no cover - platformfüggő
            return None
        try:
            return utvonal if utvonal.is_file() else None
        except OSError:  # pragma: no cover - elérhetetlen hálózati út
            return None

    def _apply_cxf_background(self, hatter) -> None:
        """A `.cxf` háttere vissza a panelra (#1085).

        A tulajdonos jelentése: *„helyreállítja az előbbi fél mentést, de a
        háttérképet elfelejti, sima színre kapcsolja vissza."* A
        visszatöltés mindent visszahozott a témától a címig — a hátteret
        nem, pedig a `.cxf` tárolja.

        ⚠️ **A képháttér INDEXKÉNT él a panelen** (#1009: a háttérkép a
        kollázs SAJÁT képeinek egyike), a `.cxf` viszont ÚTVONALAT tárol —
        itt kell a kettő közé fordítani. Ha a hivatkozott kép már nincs a
        kollázsban, **színre esünk vissza**: üres képhátteret mutatni
        rosszabb volna, mint a színt, és törött hivatkozást a #1009
        szabálya szerint sosem hagyunk.

        A mezőket KÖZVETLENÜL állítjuk, a `set*` slotok helyett: azok
        `_set_dirty(True)`-t hívnának, a visszatöltés viszont nem
        módosítás."""
        if hatter is None:
            return
        if hatter.type == "image" and hatter.src:
            # #1096: a `.cxf` a hátteret is KÓDOLT alakban tárolja
            # (`$My Pictures\…`), a csomópontok útvonala viszont a
            # `nodes_from_project`-ben már feloldva érkezik. Kódolt
            # szöveggel keresve az egyezés SOSEM jönne össze, és a háttér
            # némán színre esne vissza — pont az a hiba, amit a #1085/#1103
            # javított, csak az eredeti Picasa fájljain.
            index = self._node_index_of_path(decode_cxf_path(hatter.src))
            if index >= 0:
                self._collage_panel_bg_index = index
                self._collage_panel_bg_mode = "image"
                self.collageBackgroundModeChanged.emit()
                self.collageBackgroundImageChanged.emit()
                return
            logger.info(
                "a piszkozat háttérképe már nincs a kollázsban (%s) — szín marad",
                hatter.src,
            )
        self._collage_panel_bg_mode = "solid"
        self.collageBackgroundModeChanged.emit()
        szin = _qcolor_from_argb(hatter.color)
        if szin is not None:
            self._collage_panel_bg_color = szin
            self.collageBackgroundColorChanged.emit()

    def _node_index_of_path(self, utvonal: str) -> int:
        """Melyik csomópont ez az útvonal; −1, ha nincs a kollázsban.

        Az összehasonlítás NORMALIZÁLT: a `.cxf` a mentés platformjának
        elválasztóit hordozza, a mai csomópont az aktuálisét (#1019)."""
        cel = os.path.normcase(os.path.normpath(str(utvonal)))
        for index, csomopont in enumerate(self._nodes()):
            if csomopont.path is None:
                continue
            if os.path.normcase(os.path.normpath(str(csomopont.path))) == cel:
                return index
        return -1

    def _apply_cxf_project(self, projekt, *, saved_path: str) -> None:
        """Egy `.cxf` projekt ráterítése a panelra — EGY kódút.

        A piszkozat-visszatöltés (#1051) és a kész kollázs újranyitása
        (#1002) ugyanaz a művelet, csak a forrás más. Két külön
        megvalósítás előbb-utóbb elválna, és a felhasználó azt látná, hogy
        a kollázs máshogy jön vissza attól függően, honnan nyitotta."""
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
        # ⚠️ #1103: a háttér CSAK a csomópontok után. A képháttér a panelen
        # INDEXKÉNT él (#1009), a `.cxf` viszont ÚTVONALAT tárol, tehát a
        # visszaállítás megkeresi a képet a csomópontok között. Ha előbb
        # fut, a lista még a RÉGI (újraindítás után: ÜRES), az index −1
        # lesz, és a #1085 védőága — helyesen, de rossz pillanatban
        # kérdezve — színre ejti a hátteret. A tulajdonos ezt a v0.8.20 óta
        # látta: „a háttérképet elfelejti, sima színre kapcsolja vissza."
        self._apply_cxf_background(projekt.background)
        self._set_dirty(False)
        self._set_saved_path(saved_path)
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


def _qcolor_from_argb(ertek: str | None) -> QColor | None:
    """`FFRRGGBB` (ARGB hexa) → `QColor`; érvénytelenre `None`.

    A `.cxf` nagybetűs, nyolc karakteres ARGB-t tárol (`draft.py::_argb`); a
    `QColor` `#AARRGGBB` alakot vár. Hibás értékre nem dobunk: egy idegen
    `.cxf` sem tehet visszaállíthatatlanná egy kollázst."""
    if not ertek:
        return None
    szoveg = str(ertek).strip().lstrip("#")
    if len(szoveg) != 8:
        return None
    szin = QColor(f"#{szoveg}")
    return szin if szin.isValid() else None
