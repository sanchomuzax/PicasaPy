"""Az alkalmazás vezérlője: index-lekérdezések és a QML közti híd.

#150: a vezérlő felelősség-szeletei külön mixin-modulokban élnek
(keresés: `search_controller`, címkék: `keywords_controller`, fotó-
műveletek: `photo_ops_controller`, export: `export_controller`, könyvtár-
felügyelet: `library_controller`, formázók: `formatting`) — a QML és a
tesztek felülete (a `controller` context property slotjai/jelzései)
változatlan."""

# Az eredeti controller importútvonalairól számos, most mixinbe költözött
# segédet továbbra is újraexportálunk a korábbi hívók kompatibilitásáért.
# ruff: noqa: F401

from __future__ import annotations

import logging
import time
from pathlib import Path

from PySide6.QtCore import (
    QCoreApplication,
    Property,
    QLocale,
    QObject,
    QSettings,
    Signal,
    Slot,
)

from picasapy.index import (
    album_photos,
    albums_in_index,
    all_photos,
    geotagged_photos,
    open_index,
    search_photos,
    starred_photos,
    video_photos,
    sync_tree,
)
from picasapy.ini import set_folder_hidden_in_ini, update_document
from picasapy.scanner import PICASA_INI_NAME
from . import formatting
from .appearance_controller import AppearanceMixin
from .color_management_controller import ColorManagementMixin
from .viewer_startup_controller import ViewerStartupMixin
from .frame_capture_controller import FrameCaptureMixin
from .movie_clip_export_controller import MovieClipExportMixin
from .movie_trim_controller import MovieTrimMixin
from .batch_effect_controller import BatchEffectMixin
from .busy_registry import get_app_busy_registry
from .collage_controller import CollageMixin
from .color_index_controller import ColorIndexMixin
from .language_controller import LanguageMixin
from .display_mode_controller import DisplayModeMixin
from .editor_controls_controller import EditorControlsMixin
from .help_controller import HelpMixin
from .create_controller import CreateMixin
from .custom_aspect_ratios_controller import CustomAspectRatiosMixin
from .custom_collections_controller import CustomCollectionsMixin
from .edit_journal_controller import EditJournalMixin
from .folder_date_controller import FolderDateMixin
from .effects_controller import EffectsClipboardMixin
from .ajandek_cd_controller import AjandekCdMixin
from .export_controller import ExportMixin
from .save_controller import SaveMixin
from .geo_controller import GeoMixin
from .formatting import to_local_path as _to_local_path  # noqa: F401 — a
# fileops_controller kompatibilis import-útja (#150 előtt itt élt a függvény)
from .keywords_controller import KeywordsMixin
from .library_controller import LibraryMixin
from .option_settings import save_all_option_settings
from .models import FolderListModel, PhotoGridModel, folder_order
from .people_controller import PeopleMixin
from .project_folders_controller import ProjectFoldersMixin
from .perf_controller import PerfMonitorMixin
from .tesztuzem_controller import TesztuzemMixin
from .photo_ops_controller import PhotoOpsMixin, _WRITE_ERRORS
from .timestamp_controller import TimestampAdjustmentMixin
from .dupe_search_controller import DupeSearchMixin
from .mentes_racs_szuro import MentesRacsSzuroMixin
from .small_picture_filter import (
    is_big_picture,
)
from .similarity_controller import SimilarityMixin
from .search_controller import SearchMixin
from .screensaver_controller import ScreensaverMixin
from .side_pane_controller import SidePaneMixin
from .tray_controller import TrayMixin
from .search_results import group_by_folder
from .thumbnail_provider import ThumbnailProvider
from .filetype_preferences import enabled_filetypes as load_enabled_filetypes
from .controller_state_mixin import AppControllerStateMixin
from .controller_slideshow_mixin import SlideshowSettingsMixin
from .controller_network_settings_mixin import NetworkSettingsMixin
from . import controller_folder_view_mixin as _folder_view_mixin
from .controller_folder_view_mixin import FolderViewMixin
from .controller_hidden_folders_mixin import HiddenFoldersMixin
from .controller_navigation_mixin import FolderNavigationMixin
from .controller_content_info_mixin import ContentInfoMixin
from .controller_filter_mixin import ViewFilterMixin
from .controller_signals import AppControllerSignalsMixin
from .controller_photo_list_mixin import AppControllerPhotoListMixin
from .controller_sync_mixin import AppControllerSyncMixin, _FILETYPE_SNAPSHOT_UNSET
from .controller_folder_description_mixin import AppControllerFolderDescriptionMixin
from .controller_initialization import initialize_controller_state

FOLDER_PANE_WIDTH_DEFAULT = _folder_view_mixin.FOLDER_PANE_WIDTH_DEFAULT
FOLDER_PANE_WIDTH_MAX = _folder_view_mixin.FOLDER_PANE_WIDTH_MAX
FOLDER_PANE_WIDTH_MIN = _folder_view_mixin.FOLDER_PANE_WIDTH_MIN

_log = logging.getLogger(__name__)


class AppController(
    AppControllerPhotoListMixin,
    AppControllerSyncMixin,
    AppControllerFolderDescriptionMixin,
    #: #2054: a felhasználói súgó fejezetei, szövege és keresése
    HelpMixin,
    CustomAspectRatiosMixin,
    ScreensaverMixin,
    # #4597: a rejtett mappák valódi megvalósítása megelőzi az egyéni és
    # projektgyűjtemények alapértelmezett, üres hookjait.
    HiddenFoldersMixin,
    CustomCollectionsMixin,
    # #644: a saját szerkesztések védelme a párhuzamosan futó Picasa
    # felülírása ellen (észlelés + figyelmeztetés + helyreállítás)
    EditJournalMixin,
    FolderDateMixin,
    SearchMixin,
    # #1500: a `color:`/`szín:` keresés gyorsítótárának háttér-feltöltése.
    # A `SearchMixin` hívja (`_note_color_search`), ezért közvetlenül
    # utána áll — a szelet lustán inicializálja magát, az `__init__`-hez
    # (forró fájl) nem kell nyúlni.
    ColorIndexMixin,
    KeywordsMixin,
    # #1833: „keress ehhez hasonlót" — a minta-alapú hasonlóság-keresés.
    # Lustán inicializálja magát, tehát az `__init__`-hez (forró fájl) nem
    # kell nyúlni.
    SimilarityMixin,
    # #1398: „Fájlok másodpéldányainak megjelenítése" — az eredetiben
    # keresési MÓD (`dupesearch`), nem párbeszéd. Szintén lustán
    # inicializálja magát, tehát az `__init__`-hez nem kell nyúlni.
    DupeSearchMixin,
    # #3751: a mentés-üzemmód képrács-szűrője — lusta állapot, az
    # `__init__`-hez nem kell nyúlni
    MentesRacsSzuroMixin,
    # #4332: eredeti kép/ini írása nélküli, indexbeli dátumfelülírás.
    TimestampAdjustmentMixin,
    PhotoOpsMixin,
    BatchEffectMixin,
    ExportMixin,
    # #3503: Ajándék CD — a tálca elemeiből lemezkép
    AjandekCdMixin,
    # #444: Mentés / Visszaállítás / Utolsó mentés visszavonása — a mag
    # (`picasapy.edit.save`) régóta kész volt, csak felület nem volt hozzá
    SaveMixin,
    EffectsClipboardMixin,
    PerfMonitorMixin,
    # #1654: TARTÓS tesztüzem — a #211-gyel szemben túléli a kilépést,
    # és a KÖVETKEZŐ indulást naplózza az első ezredmásodperctől
    TesztuzemMixin,
    AppearanceMixin,
    ColorManagementMixin,
    ViewerStartupMixin,
    MovieTrimMixin,
    # #4564: a `movieeditpanel/export_movie` klipet készít a vágáspontokból.
    MovieClipExportMixin,
    # #1838: a `capture_frame` — a vágás-szelet `_vago_sor` kapuját használja
    FrameCaptureMixin,
    LanguageMixin,
    # #1575: Nézet ▸ Megjelenítési mód — a tizenegy tagú kizáró
    # csoport állapota. A szelet nem perzisztens (mérve: az eredeti
    # sem tárolja el), ezért csak egy `_init_display_mode()` kell.
    DisplayModeMixin,
    # #4336: a szerkesztő kezelősávjának láthatósága az indítások között is
    # megmarad.
    EditorControlsMixin,
    CreateMixin,
    # #985: a Kollázs-LAP vezérlője (#920 sorozat). A `CollageMixin` maga
    # örökli a `CollageSaveMixin`-t (`class CollageMixin(CollageSaveMixin)`,
    # a #949 vágta ketté a 1122 sorossá hízott fájlt), ezért itt EGY bázist
    # sorolunk fel, nem kettőt — a mentés-szelet vele együtt érkezik, és a
    # `test_collage_panel_wiring_985_allapotmentes.py` mindkét
    # `isinstance`-t állítja (a #2653 vitte át oda a #985 fájljából).
    # A szelet a saját állapotát lustán hozza létre (`_ensure_collage_panel`),
    # tehát az `__init__`-hez — ehhez a FORRÓ fájlhoz — nem kell nyúlni.
    CollageMixin,
    GeoMixin,
    LibraryMixin,
    # #26 (3. lépcső): a bal hasáb Emberek gyűjteménye — a `PeopleMixin`
    # (#397) MOSTANTÓL bekötve (korábban önállóan, host-osztályos teszttel
    # élt, ld. `people_controller.py` modul-docstring és a jegy jelentése).
    PeopleMixin,
    # #1029: a bal hasáb Projektek gyűjteménye — a `.picasa.ini`
    # `P2category=Projects (internal)` mappái
    ProjectFoldersMixin,
    # #1601: a fenti KETTŐ betöltése EGY ini-söpréssel, és induláskor a
    # felület szálán kívül — mérve ez volt az indulás szinkron munkájának
    # 94%-a (ld. `side_pane_controller.py` mérési táblája)
    SidePaneMixin,
    TrayMixin,
    AppControllerStateMixin,
    SlideshowSettingsMixin,
    NetworkSettingsMixin,
    FolderViewMixin,
    FolderNavigationMixin,
    ContentInfoMixin,
    ViewFilterMixin,
    AppControllerSignalsMixin,
    QObject,
):
    # A QML property-értesítő jelek és a Property ugyanabban a fájlban
    # maradnak, ahogy a némajelzés-őr is párosítja őket.
    quickViewChanged = Signal()
    descriptionsChanged = Signal()

    def __init__(
        self,
        db_path: Path,
        roots: tuple[str, ...],
        provider: ThumbnailProvider,
        parent=None,
        settings=None,
        watched_file: Path | None = None,
        exclude_file: Path | None = None,
        face_excluded: tuple[str, ...] = (),
    ):
        super().__init__(parent)
        initialize_controller_state(
            self,
            db_path,
            roots,
            provider,
            settings,
            watched_file,
            exclude_file,
            face_excluded,
        )

    def _get_settings(self) -> QSettings:
        """Lusta alapértelmezés: `QSettings("PicasaPy", "PicasaPy")`, hacsak
        a konstruktor nem kapott sajátot (tesztekhez)."""
        if self._settings is None:
            self._settings = QSettings("PicasaPy", "PicasaPy")
        return self._settings

    @Slot("QVariantMap")
    def saveOptionSettings(self, values: dict[str, object]) -> None:  # noqa: N802
        """Az Opciók OK gombja kiírja a teljes, már elfogadott értékképet."""
        save_all_option_settings(self._get_settings(), values)

    # -- QML-nek kitett tulajdonságok --------------------------------------

    @Property(QObject, constant=True)
    def folders(self):
        return self._folders

    @Property(QObject, constant=True)
    def photos(self):
        return self._photos

    @Property(bool, notify=quickViewChanged)
    def quickViewActive(self):  # noqa: N802 — QML-property-stílus
        return self._quick_view_active

    @Property(int, notify=descriptionsChanged)
    def descriptionRevision(self):
        """Leírás-mentéskor nő — a feed-fejlécek leírás-kötésének triggere."""
        return self._description_revision

    #: #5653: az eredeti `Preferences/BigSlideshow2` kapcsoló: hiányzó
    #: értéknél az eredeti 1-es alapértékkel.




    # -- rejtett MAPPÁK (#1637) ----------------------------------------------


    # -- műveletek ----------------------------------------------------------



    @Slot(str)
    def selectFolder(self, folder_path: str) -> None:
        """Mappa-választás (#64): a rács a TELJES könyvtár-feedet mutatja a
        bal hasáb sorrendjében — a választott mappához a rács odagörget
        (folderActivated), ahogy az eredeti Picasa tette.

        #142: ha a feed már betöltve áll (sima mappa-nézet, szűrő nélkül)
        ÉS az index azóta nem változott (fájl-pecsét, 1-2 stat() hívás),
        a mappaváltás CSAK görgetés — a feed tartalma nem változik, ezért
        nem olvassuk újra a teljes indexet (50k fotónál több száz ms)."""
        already_in_feed = (
            self._view_mode[0] == "folder"
            and bool(self._view_mode[1])
            and not self._filter_active
            and self._feed_stamp is not None
            and self._feed_stamp == self._index_stamp()
        )
        self._current_folder = folder_path
        self._view_mode = ("folder", folder_path)
        self._filter_active = False
        self._filter_status = ""
        self._restore_full_folder_pane()
        self._get_settings().setValue("session/lastFolder", folder_path)
        self._folder_description = self._read_folder_description(folder_path)
        # #1644: az „olvasatlan" jelölő a mappa MEGNYITÁSAKOR áll vissza —
        # a felhasználó megnézte, ami benne van.
        #
        # ⚠️ A jegy kimondja: hogy az EREDETI pontosan mikor törli, NINCS
        # kimérve; a megnyitás a jegy által előírt ésszerű alapértelmezés.
        # Ha egy későbbi kör mást mér, a mérés győz.
        self._clear_unread(folder_path)
        if folder_path in self._folders.offline_paths():
            # #459/5: néma bukás helyett kimondjuk, mi a helyzet — a mappa
            # megnyitható marad (a bélyegképek a gyorsítótárból jönnek), de
            # az eredeti fájlok most nem érhetők el.
            self.folderUnavailable.emit(folder_path)
        if already_in_feed:
            # currentFolder/folderDescription frissült — jelzés a QML-nek
            self.statusChanged.emit()
            self.folderActivated.emit(folder_path)
            return
        with open_index(self._db_path) as conn:
            records = self._feed_records(conn)
        self._show(records)
        self.folderActivated.emit(folder_path)




    # -- mappa-leírás (#64) --------------------------------------------------


    # -- csillag-szűrő és különleges album ----------------------------------


    # -- belső --------------------------------------------------------------













    # SZÁNDÉKOSAN nincs QML-hivatkozása (#1052): a felület a mappát is átadó
    # `setFolderDescriptionOf(path, …)` alakot hívja; ez a kompatibilitási út.


    @staticmethod
    def szamlalo_szoveg(aktualis: int, osszes: int) -> str:
        """A „hányadik / hányból" számláló — a SORREND a fordításé (#1960).

        Az eredeti angol erőforrása `%1$d of %2$d` (aktuális / összes), a
        magyar `%2$d / %1$d` (**összes / aktuális**) —
        `ThumbUIPrint::PrintCount`, `stringres` 2287. Élesben a tulajdonos
        felvételén egy ötképes mappa harmadik képénél `(5 / 3)` áll.

        Ezért nem fűzünk össze és nem égetünk be sorrendet: nevesített
        pozíció-argumentumokat adunk át, és a `.ts` dönti el, melyik nyelv
        melyik sorrendet kapja."""
        sablon = QCoreApplication.translate(
            "AppController", "({current} / {total})"
        )
        return sablon.format(current=aktualis, total=osszes)
