"""A kollázs-panel MENTÉSE és piszkozata (#949) - a spec 9. szakasza.

A `collage_controller.CollageMixin` szelete: minden, ami a **kimenet** körül
dől el - a cím, a célfájl, a folyamatjelzés, a megszakítás, a Kollázsok
albumba írt JPEG + `.cxf` pár, és a bezáráskori piszkozat.

Ez a fájl a szelet ÖSSZEFOGÓJA: a jelzések, a property-k, a cím, a
folyamatjelző és a háttérszál kimenetének fogadása itt élnek. A három nagy
rész külön fájlban van, és ugyanebből az osztályból lesz egy:

- `collage_save_render.py` - a létrehozás és a rajzolás (`createCollage`,
  `_render_worker`)
- `collage_save_draft.py` - a piszkozat mentése és visszaállítása
  (`saveCollageDraft`, `restoreCollageDraft`)
- `collage_save_open.py` - a mentett kollázs megnyitása szerkesztésre
  (`openCollageProject`, `_apply_cxf_project`)

A `CollageSaveMixin` NÉV SZERINTI szerződése (property-k, slotok, jelzések
EGY objektumon) változatlan: a `collage_controller.py` és a QML ugyanúgy éri
el, mint a szétbontás előtt. A #943-as API-teszt ezt közvetlenül állítja is.

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
`_collage_panel_draft_dir()` adja - a `CreateMixin._collage_draft_dir`
NEVÉHEZ nem nyúlunk, mert egy néma felülírás a régi Kollázs-menüt törné el.

⚠️ **Fordítási kontextus:** a `tr()` hívások ebben az osztályban maradnak,
mert a `picasapy_hu.ts` és az i18n-teszt a `CollageSaveMixin` kontextusra
épít. Ami a részosztályba kerülne, az itt élő segédet hív
(`_piszkozat_felirat()`, `_collage_megnyitas_hiba()`).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, Qt, Signal, Slot

from picasapy.collage.themes import MULTIEXP

from . import collage_output as output
from . import collage_prefs as prefs
from .collage_save_draft import CollageSaveDraftMixin
from .collage_save_open import CollageSaveOpenMixin
from .collage_save_render import CollageSaveRenderMixin
from .worker_thread import BackgroundWorkerMixin

class CollageSaveMixin(
    CollageSaveRenderMixin,
    CollageSaveDraftMixin,
    CollageSaveOpenMixin,
    BackgroundWorkerMixin,
):
    """A kollázs kimenete, folyamatjelzése és piszkozata (spec 9.).

    Az állapotát a  hozza létre - a
    panel egyetlen, lusta inicializálója, hogy ne legyen két félig kész
    állapot ugyanarra a lapra."""

    # -- jelzések (8.3) ----------------------------------------------------

    #: **BELSŐ, szál-határon átmenő jelzések (#988/#999).** A háttérszál
    #: KIZÁRÓLAG ezeket emitálja, nyers adattal - az állapotírás, a
    #: fordítás (`tr`) és a NYILVÁNOS jelzések a rájuk kötött slotokban
    #: futnak, a fogadó (GUI-) szálon.
    #:
    #: Ok (#988 veremkiíratása): a rajzoló szál korábban maga írta a
    #: `_collage_panel_percent`-et és maga emitálta a nyilvános jelzéseket,
    #: miközben a GUI-szálon szemétgyűjtés futhat a PySide-burkolókon - ez
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
    #: nem keletkezik - a jelzés a folyamatjelző elrejtésének a horga.
    collageCanceled = Signal()
    #: Integrációs horog: a kész kép asztali háttérképnek szánva. A tényleges
    #: beállítás asztali környezettől függ (KDE/GNOME/labwc), ezért nem itt
    #: dől el - a jelzés a  UTÁN érkezik.
    collageDesktopBackgroundReady = Signal(str)
    #: #1005: a háttérkép TÉNYLEGESEN beállítva - az argumentum a sikeres
    #: eszköz neve (`gsettings` · `pcmanfm` · `xfconf-query` · `feh`), hogy a
    #: felhasználó (és a naplónk) lássa, mi végezte el.
    desktopBackgroundApplied = Signal(str)
    #: #1005: a BMP kiírva, de az asztalt NEM sikerült beállítani - az
    #: argumentum a BMP útvonala. A néma sikertelenség a legrosszabb kimenet
    #: (#936): a felhasználónak legalább azt meg kell tudnia, HOVA került a
    #: kép, hogy kézzel beállíthassa.
    desktopBackgroundFailed = Signal(str)

    collageSavedPathChanged = Signal()
    #: #1168 (spec 16.3): a `collageRendering` váltása - a FŐABLAK várakozó
    #: sora (`CThumbUI::CreateCollageWait`) erre köt.
    collageRenderingChanged = Signal()

    # -- property-k (8.1) --------------------------------------------------

    # SZÁNDÉKOSAN nincs QML-hivatkozása (#1052): a kollázs nevét a felhasználó
    # nem gépeli be - a fájlnév a FORRÁSMAPPÁBÓL jön (kollazs-eletciklus.md 8.6),
    # ez a property csak a mentés bemenete.
    @property
    def collageTitle(self) -> str:
        """A kollázs címe - ebből lesz a kimeneti fájl neve (spec 9.1).

        A `openCollage` a FORRÁSMAPPA nevéből tölti fel; egy album-alapú
        belépési pont (Projektek ▸ Kollázsok) az album címét adhatja a
        `setCollageTitle`-lel. Üresen a „kollázs" tartalék lép életbe."""
        self._ensure_collage_panel()
        return self._collage_panel_title

    @Property(str, notify=collageSavedPathChanged)
    def collageSavedPath(self) -> str:
        """A kollázs legutóbbi kimeneti fájlja, vagy üres szöveg.

        Ha nem üres, az újramentés a „Lecseréli a meglévőt, vagy újat hoz
        létre?" kérdéssel indul (spec 9.2) - a felület ebből tudja, hogy
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

    def _set_saved_path(self, path: str) -> None:
        self._ensure_collage_panel()
        if path == self._collage_panel_saved_path:
            return
        self._collage_panel_saved_path = path
        self.collageSavedPathChanged.emit()

    def setCollageSavedPath(self, path: str) -> None:
        """A kollázs meglévő kimeneti fájlja - a `.cxf`-ből nyitás horga.

        Spec 9.2: „ha a kollázs egy korábban létrehozottból készült", az
        újramentés a „Lecseréli a meglévőt, vagy újat hoz létre?" kérdéssel
        indul. A Projektek ▸ Kollázsok albumból megnyitó belépési pont (3.2)
        ezen a Python-segédúton adja át, melyik fájlból dolgozunk."""
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

        A jelzőt a háttérszál a rajzolás UTÁN, az írás ELŐTT kérdezi meg -
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
        """A folyamatjelző egyetlen kapuja - a százalék itt jegyződik meg.

        ⚠️ CSAK a fogadó (GUI-) szálon hívható. A háttérszál a
        `_post_progress`-t használja (#988/#999)."""
        self._collage_panel_percent = int(percent)
        self.collageProgress.emit(int(percent), text)

    # -- a főablak várakozó állapota (#1168, spec 16.3) --------------------

    @Property(bool, notify=collageRenderingChanged)
    def collageRendering(self) -> bool:
        """Fut-e éppen a kollázs rajzolása (spec 16.3).

        Az eredetiben a KÖNYVTÁRNÉZET is jelez a kollázs készítése alatt
        (`CThumbUI::CreateCollageWait` = „Várakozás a kollázs
        elkészítésére…"), nem csak a panel folyamatjelző doboza. A panel
        közben be is zárulhat - ezért kell a főablaknak SAJÁT olvasata
        arról, hogy dolgozunk-e."""
        self._ensure_collage_panel()
        return self._collage_panel_rendering

    def _set_rendering(self, running: bool) -> None:
        """A várakozó jelző EGYETLEN kapuja - idempotens.

        Minden ág ide fut be: az indítás, a siker, a hiba, a megszakítás és
        az olvashatatlan képek is. Aki új kimeneti ágat ír, ezt hívja -
        különben a könyvtárnézetben BERAGAD a várakozó sor."""
        self._ensure_collage_panel()
        if bool(running) == self._collage_panel_rendering:
            return
        self._collage_panel_rendering = bool(running)
        self.collageRenderingChanged.emit()

    #: A háttérszálról küldhető folyamat-szövegek KULCSAI. A `tr()` hívása
    #: is a fogadó szálon történik (#988/#999) - a szál csak kulcsot küld.
    _PROGRESS_INITIALIZING = "initializing"
    _PROGRESS_READY = "ready"

    def _ensure_worker_bridge(self) -> None:
        """A belső híd-jelzések bekötése - SORBA ÁLLÍTOTT kapcsolattal.

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
        """A HÁTTÉRSZÁL folyamatjelzése - csak egy jelzés, semmi más."""
        self._workerProgress.emit(int(percent), key)

    @Slot(int, str)
    def _on_worker_progress(self, percent: int, key: str) -> None:
        """A fogadó szálon: itt fordítunk és itt írjuk az állapotot."""
        if key == self._PROGRESS_READY:
            text = self.tr("The collage is ready")
        else:
            text = self._progress_text_initializing()
        self._emit_progress(percent, text)

    @Slot(object)
    def _on_worker_outcome(self, payload: dict) -> None:
        """A rajzolás eredményének feldolgozása - a fogadó szálon.

        Minden állapotírás és minden NYILVÁNOS jelzés itt történik; a
        háttérszál csak a nyers adatot adta át.

        ⚠️ A várakozó jelzőt (#1168) MINDEN ág lekapcsolja - a rajzolásnak
        ez az egyetlen visszaérkezési pontja, tehát itt nem maradhat ki."""
        self._set_rendering(False)
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
        # #1100: a piszkozat takarítása is a FOGADÓ szálon - a beállítás
        # írása (`QSettings`) és a jelzések ugyanabba a körbe tartoznak.
        self._discard_draft_after_render()
        if payload["hianyzo"]:
            # 9.4: a hiány nem hiba - a kollázs elkészült, de a felhasználó
            # tudja meg, hogy hány kép maradt ki belőle
            self.collageMissingImages.emit(payload["hianyzo"])
        self._emit_progress(100, self.tr("The collage is ready"))
        self.collageDone.emit(ut)
        if payload["hatterkep"]:
            self.collageDesktopBackgroundReady.emit(ut)
            self._allitsd_be_hatterkepnek(ut)

    def _allitsd_be_hatterkepnek(self, kep_ut: str) -> None:
        """A kész kollázs BMP-ként a Hátterek mappába, majd háttérképnek (#1005).

        Az eredeti két lépése (mérve, `0x0057aa10`): BMP a
        `<Képek>/Picasa/<Hátterek>/picasabackground.bmp` útvonalra, majd a
        rendszer háttérképének beállítása KÖZÉPRE, nyújtás nélkül
        (`WallpaperStyle=0`, `TileWallpaper=0`). A Linux-megfelelőt a
        `app/wallpaper.py` lánca végzi.

        Hiba esetén NEM hallgatunk: a `desktopBackgroundFailed` a BMP útját
        viszi, hogy a felhasználó kézzel beállíthassa."""
        from . import wallpaper

        try:
            # A Hátterek mappa a KOLLÁZSOK mappa szomszédja - a szabály és
            # az indoklása a `wallpaper.backgrounds_dir`-ben áll (a #1775 óta
            # a menüparancs is ezt használja, egy hely, egy szabály).
            mappa = wallpaper.backgrounds_dir(
                output.output_dir(self._get_settings().value(prefs.OUTPUT_DIR_KEY)),
                output._felulet_nyelve(),
            )
            bmp = wallpaper.write_background_bmp(Path(kep_ut), mappa)
        except OSError as hiba:
            self.collageFailed.emit(str(hiba))
            return
        eszkoz = wallpaper.set_desktop_background(bmp)
        if eszkoz:
            self.desktopBackgroundApplied.emit(eszkoz)
        else:
            self.desktopBackgroundFailed.emit(str(bmp))

    def _progress_text_initializing(self) -> str:
        """A folyamatjelző első sora. A Többszörös exponálásnak SAJÁT szövege
        van (spec 9.1) - nem elrendez, hanem képeket vetít egymásra."""
        if self._collage_panel_theme == MULTIEXP:
            return self.tr("Stacking pictures")
        return self.tr("Creating collage… initializing")

    def _piszkozat_felirat(self) -> str:
        """A piszkozat helykitöltő képének felirata (#1072).

        A `collage_save_draft.py` ezt hívja. A `tr()` azért marad itt, mert a
        szöveg kontextusa a `CollageSaveMixin` (ld. a modul docstringjét)."""
        return self.tr("DRAFT")

    def _collage_megnyitas_hiba(self) -> None:
        """A kész kollázs megnyitásának hibaüzenete (#1002).

        A `collage_save_open.py` innen jelez; a `tr()` szövege itt marad a
        `CollageSaveMixin` kontextusában."""
        self.collageFailed.emit(
            self.tr("The collage project file could not be opened.")
        )

__all__ = ["CollageSaveMixin"]
