"""Az AppController állapotának és induláskori kapcsolódásainak inicializálása."""

from __future__ import annotations

from .busy_registry import get_app_busy_registry
from .filetype_preferences import enabled_filetypes as load_enabled_filetypes
from .models import FolderListModel, PhotoGridModel


def initialize_controller_state(
    self,
    db_path,
    roots,
    provider,
    settings,
    watched_file,
    exclude_file,
    face_excluded,
) -> None:
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
