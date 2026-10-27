"""Az alkalmazás vezérlője: index-lekérdezések és a QML közti híd.

#150: a vezérlő felelősség-szeletei külön mixin-modulokban élnek
(keresés: `search_controller`, címkék: `keywords_controller`, fotó-
műveletek: `photo_ops_controller`, export: `export_controller`, könyvtár-
felügyelet: `library_controller`, formázók: `formatting`) — a QML és a
tesztek felülete (a `controller` context property slotjai/jelzései)
változatlan."""

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

FOLDER_PANE_WIDTH_DEFAULT = _folder_view_mixin.FOLDER_PANE_WIDTH_DEFAULT
FOLDER_PANE_WIDTH_MAX = _folder_view_mixin.FOLDER_PANE_WIDTH_MAX
FOLDER_PANE_WIDTH_MIN = _folder_view_mixin.FOLDER_PANE_WIDTH_MIN

_log = logging.getLogger(__name__)

_FILETYPE_SNAPSHOT_UNSET = object()


class AppController(
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
        self._db_path = db_path
        self._roots = list(roots)
        self._watched_file = watched_file
        # #449: a Mappakezelő NEGYEDIK, a Scan Always/Once/Remove hármastól
        # FÜGGETLEN kapcsolója — az arcfelismerésből kizárt gyökerek
        # (FRExcludeFolders.txt, ld. library_controller.py). A
        # FaceScanController ezt minden háttérdetektálás előtt ellenőrzi;
        # a fájlformátum az eredeti Picasáéval kompatibilis.
        self._exclude_file = exclude_file
        self._face_excluded_roots = list(face_excluded)
        self._provider = provider
        # #459: sérült/betölthetetlen kép — elrejtés-felajánlás bekötése
        # MÁR itt (nem lusta, első-íráskor), mert a detektálás böngészés
        # közben, bármilyen szerkesztés NÉLKÜL is bekövetkezhet
        # (PhotoOpsMixin, `_ensure_broken_photo_wired`).
        self._ensure_broken_photo_wired()
        self._folders = FolderListModel(self)
        self._photos = PhotoGridModel(self)
        self._quick_view_active = False
        self._quick_view_photo_ids: tuple[str, ...] = ()
        self._init_screensaver()
        self._albums: list = []  # #9: a bal hasáb Albumok gyűjteménye
        self._current_folder = ""
        self._status = ""
        self._folder_date = ""
        self._folder_description = ""
        self._sync_running = False
        # #1440: fut-e CÉLZOTT mappa-szinkron (ld. `_on_folders_dirty`)
        self._dirty_running = False
        # #1181: a futó szinkron alatt kért célzott frissítések — a
        # szinkron végén be kell hozni a lemaradást (ld. a
        # `_on_folders_dirty` és a `_flush_pending_dirty` docstringjét)
        self._pending_dirty: set[object] = set()
        #: #1458: hány FELHASZNÁLÓI kérés vár a `_pending_dirty`-ben nyitott
        #: foglaltság-bejegyzéssel. A `_flush_pending_dirty` ennyit zár.
        self._pending_busy: int = 0
        self._view_mode = ("folder", "")  # (mód, paraméter) az újratöltéshez
        self._filter_active = False
        self._filter_status = ""
        #: #1830: az idő-csúszka kor-szűrője — a MEGENGEDETT legnagyobb kor
        #: napban, vagy `None`, ha nincs kor-szűrés. A csúszka nyers értékét
        #: nem tartjuk meg: a felirat és a vágópont is a napokból számol.
        self._age_filter_days: float | None = None
        self._folders_filtered = False  # a bal hasáb keresésre szűkítve (#49)
        self._feed_groups: tuple[dict, ...] = ()  # a rács mappa-csoportjai (#64)
        # #142: az index fájl-pecsétje a feed betöltésekor — amíg egyezik,
        # a mappaváltás nem olvassa újra a teljes könyvtárat
        self._feed_stamp: tuple | None = None
        self._descriptions: dict[str, str] = {}  # mappa-leírás cache (NAS!)
        self._description_revision = 0
        self._search_result_count = 0  # összes találat (#7, a bal paneli sorhoz)
        self._search_groups: tuple = ()  # a rács mappánkénti csoportosításához
        self._settings = settings
        # A háttérben futó szkennelések ezt az immutable pillanatképet
        # használják; a QSettings-et a GUI-szálon olvassuk/írjuk.
        self._filetype_scan_snapshot = load_enabled_filetypes(self._get_settings())
        self._thumb_caption_mode = self._get_settings().value(
            "view/thumbCaption", "none"
        )
        self._watcher = None
        self._rescan_timer = None
        self._folder_poll_timer = None
        # #70/#505: a busy-számlálás magában a közös `AppBusyRegistry`-ben él
        # (`busy_registry.py`) — itt csak a thumbnail-provider él-figyeléséhez
        # kell a legutóbbi SZINT (ld. `LibraryMixin._on_thumb_active`).
        self._thumb_active = 0
        # #209: a lebegő „Importálás" panel állapota (LibraryMixin kezeli)
        self._import_folder = ""
        self._import_done = 0
        self._import_total = 0
        self._import_new = 0
        self._import_visible = False
        self._import_forced = False
        self._import_dismissed = False
        self._import_last_reload = 0.0
        self._import_new_at_reload = 0
        # #211: kapcsolható teljesítmény-monitor — alapból KI, semmi extra
        # költség (PerfMonitorMixin saját inicializáló-metódusa)
        self._init_perf_monitor()
        # #1654: tartós tesztüzem — két olcsó olvasás, semmi több
        self._init_tesztuzem()
        # #28: sötét téma kapcsoló — alapból világos, QSettings-ből visszaáll
        self._init_appearance()
        self._init_editor_controls()
        self._init_color_management()  # #1725
        self._init_viewer_startup()  # #4432
        self._init_language()
        self._init_display_mode()
        # #26 (3. lépcső): a bal hasáb Emberek gyűjteménye — a PeopleMixin
        # saját kezdeti állapota (`people` property üres listával indul,
        # a `_reload()` tölti fel az indexből)
        self._init_people()
        # #1029: a Projektek gyűjtemény kezdeti (üres) állapota — a
        # `_reload()` tölti fel az indexből, a mappalistával együtt
        self._init_project_folders()
        # #5145: a hálózati napló szintje a beállításból indul
        self._apply_network_log()
        # #4887: az index a tényleges „rejtettek megjelenítése” értékkel indul
        self._rejtett_lathatosag_kozlese()
        # #173: a háttér-sync frissítsen, de NE görgessen a mappa tetejére
        # (folderActivated) — az elvenné a nézőből visszatérő felhasználó
        # görgetési pozícióját. A scroll-to-top csak explicit mappa-választásé.
        self.syncFinished.connect(self._reload_after_sync)
        # #1181: a szinkron alatt elhalasztott mappa-frissítések
        self.syncFinished.connect(self._flush_pending_dirty)
        # #209: mappánkénti haladás a workerből (queued) + panel-lezárás
        self.syncProgress.connect(self._on_sync_progress)
        self.syncFinished.connect(self._on_import_finished)
        self.watcherDirty.connect(self._on_folders_dirty)
        provider.activeCountChanged.connect(self._on_thumb_active)
        # #505: a közös busy-nyilvántartás (bármely controller munkája,
        # ld. `busy_registry.py`) LÁTHATÓ-állapot-változása közvetlenül a
        # meglévő `busyChanged` jelzést váltja ki — a QML/tesztek felülete
        # (`controller.isWorking`/`busyChanged`) változatlan marad.
        get_app_busy_registry().visibleChanged.connect(self.busyChanged)
        # #2966: a megszakíthatóság a saját jelzésén megy a QML felé
        get_app_busy_registry().cancellableChanged.connect(
            self.activityCancellableChanged
        )

    def _get_settings(self) -> QSettings:
        """Lusta alapértelmezés: `QSettings("PicasaPy", "PicasaPy")`, hacsak
        a konstruktor nem kapott sajátot (tesztekhez)."""
        if self._settings is None:
            self._settings = QSettings("PicasaPy", "PicasaPy")
        return self._settings

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



    def _feed_records(self, conn) -> tuple:
        """A teljes könyvtár a Mappa ▸ Rendezés szerint (#64, #321).

        A sorrendet KÜLÖN kérdezzük le, nem a bal hasáb modelljéből vesszük:
        a fa a saját rögzített sorrendjében áll, a rács a beállítást követi.
        """
        order = {
            path: i
            for i, path in enumerate(
                folder_order(conn, self.folderSort, self.folderSortReverse)
            )
        }
        return tuple(
            sorted(
                all_photos(conn),
                key=lambda r: (
                    order.get(r.folder_path, len(order)),
                    r.folder_path,
                    r.name,
                ),
            )
        )

    # -- mappa-leírás (#64) --------------------------------------------------


    # -- csillag-szűrő és különleges album ----------------------------------


    # -- belső --------------------------------------------------------------

    def _sync_tree(
        self,
        conn,
        folder: str,
        progress=None,
        enabled_filetypes=_FILETYPE_SNAPSHOT_UNSET,
    ) -> None:
        """Indirekció a mappa-resynchez (#150): a mixinek ezen át hívják a
        `sync_tree`-t, így a tesztek patch-pontja (a modul-szintű
        `picasapy.app.controller.sync_tree`) változatlanul él.

        #209: az opcionális `progress` callback (worker-szál!) mappánkénti
        haladás-jelzést ad tovább a `sync_tree`-nek."""
        if enabled_filetypes is _FILETYPE_SNAPSHOT_UNSET:
            enabled_filetypes = self._filetype_scan_snapshot
        kwargs = {}
        if progress is not None:
            kwargs["progress"] = progress
        if enabled_filetypes is not None:
            kwargs["enabled_filetypes"] = enabled_filetypes
        sync_tree(conn, folder, **kwargs)

    def _show_filtered(self, records, elapsed: float) -> None:
        """Szűrt nézet megjelenítése a ZÖLD EREDMÉNYSÁV szövegével együtt.

        #1443: eddig csak a `showStarred`/`showAlbum` állította a sáv
        szövegét, az újralekérdezés (`_refresh_view`) nem — így a
        „N folders / M pictures visible" a csillag levétele után elavult
        darabszámot mutatott, miközben a rács már helyesen frissült.
        A szöveget a `_show` közben kimenő `statusChanged` viszi ki, ezért
        a beállítás sorrendben ELŐTTE áll."""
        self._filter_active = True
        self._filter_status = formatting.filter_status_text(
            records, elapsed, QLocale(), formatting.fordit
        )
        self._show(records)

    def _refresh_view(self) -> None:
        """Az aktuális nézet újratöltése az indexből (mód szerint)."""
        mode, param = self._view_mode
        if mode == "search":
            started = time.perf_counter()
            with open_index(self._db_path) as conn:
                records = search_photos(conn, param)
            self._show_search_pane(records)
            # #4531: a zöld sáv (és a visszalépő gomb) a frissítésnél sem tűnhet el
            self._show_search_results(records, time.perf_counter() - started)
        elif mode == "search-folder":
            query, folder = param
            started = time.perf_counter()
            with open_index(self._db_path) as conn:
                all_matches = search_photos(conn, query)
            self._show_search_pane(all_matches)
            self._show_search_results(
                tuple(r for r in all_matches if r.folder_path == folder),
                time.perf_counter() - started,
            )
        elif mode in ("starred", "starred_album"):
            started = time.perf_counter()
            with open_index(self._db_path) as conn:
                records = starred_photos(conn)
            self._show_filtered(records, time.perf_counter() - started)
        elif mode == "videos":
            # #1830: enélkül egy frissítés némán visszadobná a felhasználót
            # a mappa-nézetbe — a csillag-szűrőnek is ezért van ága
            started = time.perf_counter()
            with open_index(self._db_path) as conn:
                records = video_photos(conn)
            self._show_filtered(records, time.perf_counter() - started)
        elif mode == "age":
            # #1830: enélkül egy frissítés némán visszadobná a felhasználót
            # a mappa-nézetbe (a film- és a hasonlóság-szűrőnek is ezért van
            # ága). A vágópont ilyenkor ÚJRA számolódik a mostani időhöz.
            self._show_age_filtered(param)
        elif mode == "dupes":
            # #1398: a másodpéldány-mód is nézet-mód, tehát egy frissítés
            # (ini-írás, háttér-szinkron) ne dobja vissza a felhasználót a
            # mappa-nézetbe — a #1830/#1833 ágainak mintája.
            self._show_filtered(self._duplicate_records(), 0.0)
        elif mode == "similar":
            # #1833: enélkül egy frissítés némán visszadobná a felhasználót
            # a mappa-nézetbe (a film-szűrőnek is ezért van ága, #1830).
            self._show_filtered(self._similar_records(param), 0.0)
        elif mode == "album":
            started = time.perf_counter()
            with open_index(self._db_path) as conn:
                records = album_photos(conn, param)
            self._show_filtered(records, time.perf_counter() - started)
        elif self._refresh_people_view(mode, param):
            pass  # #26: a PeopleMixin saját ágon kezelte ("person" mód)
        elif mode == "geo":
            # #30: hely-szűrő — a friss geocímkék (ini-írás után is) látszanak
            with open_index(self._db_path) as conn:
                self._show(geotagged_photos(conn))
        elif param:
            with open_index(self._db_path) as conn:
                self._show(self._feed_records(conn))

    @Slot()
    def refreshCollections(self) -> None:
        """#26 (3. lépcső): a bal hasáb gyűjteményeinek (Albumok/Emberek)
        frissítése — a `faceScanController.assignNameToFaces()` sikeres
        névadása után hívandó a QML-ből, hogy az első névadásnál keletkező
        új Emberek-album azonnal megjelenjen (`_reload_after_sync` mintája:
        a görgetési pozíció megmarad)."""
        self._reload(preserve_scroll=True)

    @Slot()
    def _reload_after_sync(self) -> None:
        """A háttér-sync (syncFinished) utáni frissítés: a görgetési pozíció
        MEGŐRZÉSÉVEL (#173) — folder-módban NEM emittál folderActivated-et,
        így a QML nem görget a mappa tetejére (scrollToGroup). A nézőből
        visszatérve a feed így a megnyitás előtti pozícióján marad."""
        self._reload(preserve_scroll=True)

    def _reload(
        self, preserve_scroll: bool = False, defer_collections: bool = False
    ) -> None:
        """#1601: `defer_collections=True` esetén a hasáb két ini-alapú
        gyűjteménye (Emberek, Projektek) NEM töltődik be itt — az indulás
        használja így, hogy a `.picasa.ini`-söprés ne a felület szálán
        blokkoljon. Az elmaradt betöltést a háttér-szinkron végi
        `_reload_after_sync()` hozza be (ld. `side_pane_controller.py`)."""
        # a háttér-sync külső ini-változást is hozhat — a leírás-cache
        # elavulhatott, a fejlécek olvassák újra
        self._descriptions.clear()
        self._description_revision += 1
        self.descriptionsChanged.emit()
        mode, _ = self._view_mode
        # Keresésre szűkített hasábnál (#49) a teljes lista betöltése
        # felvillanást okozna — a _refresh_view frissíti a szűkítettet.
        if mode not in ("search", "search-folder"):
            with open_index(self._db_path) as conn:
                self._folders.load(conn)  # #321: a fa sorrendje rögzített
                self._load_albums(conn)  # #9: a bal hasáb albumlistája
                # #26 (Emberek) + #1029 (Projektek): mindkettő a `.picasa.ini`-kből
                # él, ezért EGY söprésből áll elő (#1601). Induláskor pedig
                # egyáltalán nem itt, hanem a háttér-szinkron szálán.
                if not defer_collections:
                    self._load_side_pane(conn)
        if mode != "folder":
            # #38: aktív keresés/szűrő a háttér-sync után is megmarad —
            # a selectFolder eldobná, ezért csak a nézetet frissítjük.
            self._refresh_view()
        elif self._current_folder:
            # #173: háttér-sync után csak a feedet frissítjük (folderActivated
            # nélkül) — a scroll-to-top csak explicit mappa-választásé. Induláskor
            # (preserve_scroll=False) viszont a selectFolder a visszaállított
            # mappához görget, ahogy eddig.
            if preserve_scroll:
                self._refresh_view()
            else:
                self.selectFolder(self._current_folder)
        else:
            self._update_status(())
            self.restoreSession()

    def _show(self, records) -> None:
        # #4526: a kor-szűrő felirata és csúszkája csak a kor-nézethez
        # tartozik. Bármely más nézet betöltése törölje, így a szűrőgombok,
        # keresések és mappaváltások után sem maradhat régi kor-felirat.
        if self._view_mode[0] != "age" and self._age_filter_days is not None:
            self._age_filter_days = None
        # #17: a rejtett képek alapból sehol nem látszanak (rács, keresés,
        # csillag-szűrő) — a Nézet → Rejtett képek kapcsolóval igen
        if not self.showHidden:
            records = tuple(r for r in records if not r.hidden)
        # #461: a BEZÁRT gyűjtemények képei sehol nem látszanak — rácsban,
        # keresésben, csillag-szűrőben sem. Ez az EGY pont, ahol minden
        # nézetmód átmegy, ezért a szűrés itt van (a rejtett képek mintája).
        # A bezárás nem törlés: a mappák a gyűjteményben maradnak.
        closed_folders = self._closed_collection_folders()
        if closed_folders:
            records = tuple(
                r for r in records if r.folder_path not in closed_folders
            )
        # #3751: mentés-üzemmódban csak a még el nem mentett fájlok
        records = self._mentes_szurt(records)
        # #4346: az eredeti `Show only big images` preferenciája a
        # könyvtári képrács láthatóságát szűri. A videók és a méretadat
        # nélküli sorok megmaradnak; ez utóbbiaknál az eredeti is az
        # általános hozzáadási ágra jut.
        if self.showOnlyBigImages:
            records = tuple(
                record
                for record in records
                if record.kind not in ("photo", "image")
                or is_big_picture(record.width, record.height)
            )
        # #142: a mappaváltás-gyorsút pecsétje — csak a teljes feedet
        # mutató mappa-nézet érvényes hozzá (szűrt/keresett nézet nem)
        self._feed_stamp = (
            self._index_stamp()
            if self._view_mode[0] == "folder" and not self.backupFilterActive
            else None
        )
        # #644: itt látjuk először a friss ini-állapotot — ha egy külső
        # program (a párhuzamosan futó Picasa) letörölte a mi mentett
        # láncunkat, ez az a pont, ahol észrevehetjük. Képenként egyszer
        # jelzünk; a néma eltűnés a legrosszabb változat.
        self._check_external_overwrites(records)
        self._provider.register_photos(records)
        self._photos.set_photos(records)
        self._update_feed_groups(records)
        # #2304: a mappa-fejléc dátumsora — a `formatting.first_date_text`-tel
        # és az állapotsorral KÖZÖS `photo_dates`-en át, hogy EXIF nélküli
        # mappában is legyen dátum, és hogy a három felirat ne mondhasson
        # mást ugyanarról a mappáról. (Ez a property ma bekötetlen —
        # `scripts/kepesseg_or_baseline.txt` —, de bekötéskor a hiba
        # azonnal visszatérne.)
        dates = formatting.photo_dates(records)
        self._folder_date = (
            formatting.long_date(dates[0], QLocale()) if dates else ""
        )
        search_active = self._view_mode[0] in ("search", "search-folder")
        self._search_groups = group_by_folder(records) if search_active else ()
        self._update_status(records)
        # #30: a térkép-jelölők mindig a LÁTSZÓ képeket tükrözik
        self.geoChanged.emit()

    def _update_feed_groups(self, records) -> None:
        """Mappa-csoportok a rács-feedhez (#64). feedChanged CSAK valódi
        változásnál megy ki — különben minden háttér-frissítés nullázná a
        rács görgetését."""
        groups = formatting.build_feed_groups(records, QLocale())
        if groups != self._feed_groups:
            self._feed_groups = groups
            self.feedChanged.emit()

    def _load_albums(self, conn) -> None:
        """Az albumlista frissítése (#9) — ugyanott hívjuk, mint a
        mappalistát: a `_reload()`-ban, a háttér-szinkron után is friss
        marad. A névtelen albumnak is van megjelenítendő neve, hogy ne
        maradjon üres sor a hasábon."""
        self._albums = [
            {
                "token": album.token,
                "name": album.name or self._album_placeholder_name(album.token),
                "count": album.photo_count,
            }
            for album in albums_in_index(conn)
        ]
        self.albumsChanged.emit()

    def _album_placeholder_name(self, token: str) -> str:
        """Megjelenítendő név a névtelen albumnak: a token rövidített
        alakja — sose maradjon üres sor a hasábon."""
        return self.tr("Album %1").replace("%1", token[:8])

    def _update_status(self, records) -> None:
        self._status = formatting.status_text(
            records, QLocale(), formatting.fordit, self.tr
        )
        self.statusChanged.emit()

    def _set_folder_hidden_in_ini(self, path: str, hidden: bool) -> None:
        """A rejtési írás cserélhető pontja a korábbi controller API-hoz."""
        set_folder_hidden_in_ini(path, hidden)

    # SZÁNDÉKOSAN nincs QML-hivatkozása (#1052): a felület a mappát is átadó
    # `setFolderDescriptionOf(path, …)` alakot hívja; ez a kompatibilitási út.
    def setFolderDescription(self, text: str) -> None:
        """A KIVÁLASZTOTT mappa leírásának mentése (kompatibilitási út —
        a feed-fejlécek a setFolderDescriptionOf-ot hívják)."""
        if not self._current_folder:
            return
        self.setFolderDescriptionOf(self._current_folder, text)

    @Slot(str, str)
    def setFolderDescriptionOf(self, folder_path: str, text: str) -> None:
        """Mappa-leírás mentése — Picasa-kompatibilis: `[Picasa]/description`
        kulcs a mappa `.picasa.ini`-jében (nem indexelt, resync nem kell)."""
        if not folder_path:
            return
        text = text.strip()
        ini_path = Path(folder_path) / PICASA_INI_NAME

        # #137: útvonalanként soros írás — az előzetes ujjlenyomat-
        # ellenőrzésig észlelt Picasa-módosítás újrajátszódik. A check/save
        # közti külső írás teljes kizárását a fájlrendszer nem garantálja.
        def mutate(document):
            if text:
                return document.with_value("Picasa", "description", text)
            return document.with_removed("Picasa", "description")

        # #2506: az írás bukása NEM lehet néma. Írásvédett mappán vagy tele
        # lemezen a kivétel eddig a QML-slotból szökött ki, a feed-fejléc
        # pedig már az ÚJ leírást mutatta — a felhasználó azt hitte,
        # mentett. A projekt meglévő hibacsatornája ez (#459: a
        # `photoOpFailed` a `syncFailed`-en át a `Main.qml` `errorBanner`-be
        # fut be); a gyorstárat és a jelzéseket csak SIKERES írás után
        # frissítjük, hogy a felület se hazudjon (#2497 tanulsága).
        try:
            update_document(ini_path, mutate, backup=True)
        except _WRITE_ERRORS as error:
            self.jelentsdAzIrasiHibat(error)
            return
        self._descriptions[folder_path] = text
        if folder_path == self._current_folder:
            self._folder_description = text
        self._description_revision += 1
        self.descriptionsChanged.emit()
        self.statusChanged.emit()

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
