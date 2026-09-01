"""Az alkalmazás vezérlője: index-lekérdezések és a QML közti híd.

#150: a vezérlő felelősség-szeletei külön mixin-modulokban élnek
(keresés: `search_controller`, címkék: `keywords_controller`, fotó-
műveletek: `photo_ops_controller`, export: `export_controller`, könyvtár-
felügyelet: `library_controller`, formázók: `formatting`) — a QML és a
tesztek felülete (a `controller` context property slotjai/jelzései)
változatlan."""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import (
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
    is_folder_hidden,
    set_folder_hidden,
    starred_photos,
    video_photos,
    sync_tree,
)
from picasapy.ini import load_document, update_document
from picasapy.scanner import PICASA_INI_NAME
from . import formatting
from .appearance_controller import AppearanceMixin
from .batch_effect_controller import BatchEffectMixin
from .busy_registry import get_app_busy_registry
from .collage_controller import CollageMixin
from .color_index_controller import ColorIndexMixin
from .language_controller import LanguageMixin
from .display_mode_controller import DisplayModeMixin
from .create_controller import CreateMixin
from .custom_aspect_ratios_controller import CustomAspectRatiosMixin
from .custom_collections_controller import CustomCollectionsMixin
from .edit_journal_controller import EditJournalMixin
from .folder_date_controller import FolderDateMixin
from .effects_controller import EffectsClipboardMixin
from .export_controller import ExportMixin
from .save_controller import SaveMixin
from .geo_controller import GeoMixin
from .formatting import to_local_path as _to_local_path  # noqa: F401 — a
# fileops_controller kompatibilis import-útja (#150 előtt itt élt a függvény)
from .keywords_controller import KeywordsMixin
from .library_controller import LibraryMixin
from .collections import COLLECTIONS, DEFAULT_COLLAPSED, collection_setting_key
from .models import FolderListModel, PhotoGridModel, folder_order
from .people_controller import PeopleMixin
from .project_folders_controller import ProjectFoldersMixin
from .perf_controller import PerfMonitorMixin
from .tesztuzem_controller import TesztuzemMixin
from .photo_ops_controller import PhotoOpsMixin
from .search_controller import SearchMixin
from .side_pane_controller import SidePaneMixin
from .tray_controller import TrayMixin
from .search_results import group_by_folder, groups_to_qml
from .thumbnail_provider import ThumbnailProvider

_THUMB_CAPTION_MODES = ("none", "filename", "caption", "tags", "resolution")

#: A bal oldali mappapanel szélessége (#322) — a felhasználó húzhatja, az
#: érték a QSettings-ben él. A határok azt védik ki, hogy egy elrontott
#: (nulla vagy képernyőnél szélesebb) érték használhatatlan felülettel
#: indítsa a következő futást.
# #587: a forrás szerinti alapérték a `HLISTOFFSET2` = **240** px, FIX
# (a bal panel nem skálázódik az ablakkal, csak a felhasználó húzhatja).
# A korábbi 230 becslés volt; a `design-guide.md` két helyen 386-ot,
# illetve 210-et állított — mindkettő téves, a #587 javította.
FOLDER_PANE_WIDTH_DEFAULT = 240
FOLDER_PANE_WIDTH_MIN = 160
FOLDER_PANE_WIDTH_MAX = 600


def _clamp_folder_pane_width(width: int) -> int:
    return max(FOLDER_PANE_WIDTH_MIN, min(FOLDER_PANE_WIDTH_MAX, width))


class AppController(
    CustomAspectRatiosMixin,
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
    PhotoOpsMixin,
    BatchEffectMixin,
    ExportMixin,
    # #444: Mentés / Visszaállítás / Utolsó mentés visszavonása — a mag
    # (`picasapy.edit.save`) régóta kész volt, csak felület nem volt hozzá
    SaveMixin,
    EffectsClipboardMixin,
    PerfMonitorMixin,
    # #1654: TARTÓS tesztüzem — a #211-gyel szemben túléli a kilépést,
    # és a KÖVETKEZŐ indulást naplózza az első ezredmásodperctől
    TesztuzemMixin,
    AppearanceMixin,
    LanguageMixin,
    # #1575: Nézet ▸ Megjelenítési mód — a tizenegy tagú kizáró
    # csoport állapota. A szelet nem perzisztens (mérve: az eredeti
    # sem tárolja el), ezért csak egy `_init_display_mode()` kell.
    DisplayModeMixin,
    CreateMixin,
    # #985: a Kollázs-LAP vezérlője (#920 sorozat). A `CollageMixin` maga
    # örökli a `CollageSaveMixin`-t (`class CollageMixin(CollageSaveMixin)`,
    # a #949 vágta ketté a 1122 sorossá hízott fájlt), ezért itt EGY bázist
    # sorolunk fel, nem kettőt — a mentés-szelet vele együtt érkezik, és a
    # `test_collage_panel_wiring_985.py` mindkét `isinstance`-t állítja.
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
    QObject,
):
    statusChanged = Signal()
    # #64: a rács-feed mappa-csoportjai változtak (csak valódi változásnál!)
    feedChanged = Signal()
    # #64: mappa-választás — a rács a feedben ehhez a csoporthoz görget
    folderActivated = Signal(str)
    descriptionsChanged = Signal()
    # #9: az albumlista változott (szinkron után, a mappalistával együtt)
    albumsChanged = Signal()
    # #459/5: a választott mappa jelenleg nem elérhető (levált NAS-mount,
    # kihúzott lemez). NEM hiba — tájékoztatás: a mappa és a bélyegképei
    # megmaradnak, csak az eredeti fájlok nem érhetők el most.
    folderUnavailable = Signal(str)

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
        # (FRExcludeFolders.txt, ld. library_controller.py). Arcfelismerés-
        # motor MÉG NINCS a projektben: ez egyelőre csak a SZÁNDÉKOT
        # rögzíti, a fájl-formátum viszont már az eredeti Picasáéval
        # kompatibilis.
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
        self._pending_dirty: set[str] = set()
        self._view_mode = ("folder", "")  # (mód, paraméter) az újratöltéshez
        self._filter_active = False
        self._filter_status = ""
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
        self._init_language()
        self._init_display_mode()
        # #26 (3. lépcső): a bal hasáb Emberek gyűjteménye — a PeopleMixin
        # saját kezdeti állapota (`people` property üres listával indul,
        # a `_reload()` tölti fel az indexből)
        self._init_people()
        # #1029: a Projektek gyűjtemény kezdeti (üres) állapota — a
        # `_reload()` tölti fel az indexből, a mappalistával együtt
        self._init_project_folders()
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

    @Property(list, notify=albumsChanged)
    def albums(self):
        """Albumlista a bal hasábnak (#9): {token, name, count} elemek —
        LISTA, nem tuple (#232, a QML-ben a tuple nem tömb). A névtelen
        albumnak is van megjelenítendő neve (a token rövidített alakja),
        hogy ne maradjon üres sor a hasábon."""
        return list(self._albums)

    @Property(str, notify=statusChanged)
    def currentAlbumToken(self):
        """Az aktív album token-je (#9) — a bal hasáb kijelöléséhez."""
        mode, param = self._view_mode
        return param if mode == "album" else ""

    @Property(str, notify=statusChanged)
    def statusText(self):
        return self._status

    @Property(str, notify=statusChanged)
    def currentFolder(self):
        return self._current_folder

    @Property(str, notify=statusChanged)
    def folderDateText(self):
        """A mappa-fejléc dátumsora (a legkorábbi felvétel hosszú dátuma)."""
        return self._folder_date

    @Property(str, notify=statusChanged)
    def folderDescription(self):
        """A mappa leírása — Picasa-kompatibilis: `[Picasa]/description`
        kulcs a mappa `.picasa.ini`-jében."""
        return self._folder_description

    @Property(bool, notify=statusChanged)
    def searchActive(self):
        """Aktív-e a keresés (#7): bal paneli sor + rács-csoportosítás."""
        return self._view_mode[0] in ("search", "search-folder")

    @Property(str, notify=statusChanged)
    def searchQuery(self):
        mode, param = self._view_mode
        if mode == "search":
            return param
        if mode == "search-folder":
            return param[0]
        return ""

    @Property(int, notify=statusChanged)
    def searchResultCount(self):
        """Az ÖSSZES találat (#7) — mappára szűkítve is, nem a részhalmaz."""
        return self._search_result_count

    @Property(list, notify=statusChanged)
    def searchGroups(self):
        """A jelenleg látszó fotók mappánkénti csoportjai QML-nek (#7)."""
        return groups_to_qml(self._search_groups)

    @Property(bool, notify=statusChanged)
    def filterActive(self):
        return self._filter_active

    @Property(str, notify=statusChanged)
    def viewModeName(self):
        """A jelenlegi szűrt nézet neve (`folder` · `starred` · `videos` ·
        `album` · `search`…).

        #1830: a szűrő-gombok ebből tudják, hogy ŐK vannak-e bekapcsolva.
        A `filterActive` erre nem elég: az csak azt mondja, hogy szűrünk,
        azt nem, hogy MIVEL — két szűrő-gomb egyszerre látszana aktívnak."""
        return self._view_mode[0]

    @Property(str, notify=statusChanged)
    def filterStatusText(self):
        """A zöld eredménysáv szövege (Picasa-minta)."""
        return self._filter_status

    @Property("QVariantList", notify=feedChanged)
    def feedGroups(self):
        """A rács-feed mappa-csoportjai (#64): {path, name, start, count,
        dateText} — a QML ebből rajzol mappa-fejlécet és képfolyamot."""
        return [dict(group) for group in self._feed_groups]

    @Property(int, notify=descriptionsChanged)
    def descriptionRevision(self):
        """Leírás-mentéskor nő — a feed-fejlécek leírás-kötésének triggere."""
        return self._description_revision

    @Property(list, notify=statusChanged)
    def watchedFolders(self):
        return list(self._roots)

    @Property(list, notify=statusChanged)
    def faceExcludedFolders(self):
        """Az arcfelismerésből kizárt gyökér-mappák (#449) — a
        `FolderStatePanel.qml` ebből számolja (ős-mappákra is kiterjedő
        egyezéssel) a jelölőnégyzet állapotát, a `watchedFolders` mintáját
        követve."""
        return list(self._face_excluded_roots)

    @Property(str, notify=statusChanged)
    def folderSort(self):
        return self._get_settings().value("view/folderSort", "date")

    @Property(bool, notify=statusChanged)
    def folderSortReverse(self):
        value = self._get_settings().value("view/folderSortReverse", "false")
        return value in (True, "true", "1")

    @Property(str, notify=statusChanged)
    def paneSort(self):
        """A BAL HASÁB rendezése (#461/3) — a rácsétól FÜGGETLEN beállítás.

        Az eredeti Picasában a bal panel saját jobbklikk-menüje
        (`AlbumList`, ld. `ui-audit-context-menus.md` A.2) tartalmazta a
        „Rendezés dátum / név / méret / legutóbbi változtatás alapján"
        tételeket — vagyis az a HASÁBOT rendezte. A Mappa ▸ Rendezés ettől
        külön, a RÁCSOT állítja (#321). Két parancs, két cél."""
        return self._get_settings().value("view/paneSort", "date")

    @Property(bool, notify=statusChanged)
    def paneSortReverse(self):
        value = self._get_settings().value("view/paneSortReverse", "false")
        return value in (True, "true", "1")

    @Slot(str)
    def setPaneSort(self, mode: str) -> None:
        """A bal hasáb rendezésének váltása (#461/3)."""
        if mode not in ("date", "changed", "size", "name"):
            return
        self._get_settings().setValue("view/paneSort", mode)
        self._reload_folders()

    @Slot()
    def togglePaneSortReverse(self) -> None:
        self._get_settings().setValue(
            "view/paneSortReverse", not self.paneSortReverse
        )
        self._reload_folders()

    @Slot(str)
    def setFolderSort(self, mode: str) -> None:
        """A MAPPA-BLOKKOK sorrendje a rácson (Mappa ▸ Rendezés):
        date / changed / size / name.

        ⚠️ #1759 — MÉRVE, mert a korábbi leírás félrevezetett. Ez a
        beállítás azt dönti el, milyen sorrendben követik egymást a
        MAPPÁK a rácson (`_feed_records` → `folder_order`). Nem rendezi
        át a mappán BELÜLI képeket, és nem a bal hasáb sorrendje.

        Három, egymástól FÜGGETLEN rendezés él a programban:

        | beállítás | mit rendez | honnan |
        |---|---|---|
        | `folderSort` (ez) | a mappa-blokkokat a RÁCSON | Mappa ▸ Rendezés |
        | `folderPhotoSort` (#1436) | a mappa KÉPEIT | mappa-jobbklikk |
        | `paneSort` (#461/3) | a BAL HASÁB sorait | a hasáb helyi menüje |

        A #1595 kutatása épp azért vont le téves következtetést, mert a
        korábbi docstring („a RÁCS rendezése") alapján úgy tűnt, hogy ez
        és a `folderPhotoSort` ugyanaz kétféle felirattal — az összevonás
        egy működő szempontot („legutóbbi változtatások") vett volna el.

        #1454: a Nézet ▸ Mappanézet almenü — ahonnan ez korábban szintén
        hívható volt — nem rendez, hanem a bal hasáb szerkezetét állítja.
        """
        if mode not in ("date", "changed", "size", "name"):
            return
        self._get_settings().setValue("view/folderSort", mode)
        self._refresh_view()

    @Slot()
    def toggleFolderSortReverse(self) -> None:
        self._get_settings().setValue(
            "view/folderSortReverse", not self.folderSortReverse
        )
        self._reload_folders()
        self._refresh_view()  # a feed sorrendje követi a hasábot (#64)

    def _reload_folders(self) -> None:
        # #321 + #461/3: a bal hasábnak SAJÁT rendezése van — a Mappa ▸
        # Rendezés (folderSort) továbbra sem nyúl hozzá, azt csak a rács
        # követi. A hasáb sorrendjét a saját jobbklikk-menüje állítja
        # (`paneSort`), ahogy az eredeti Picasa `AlbumList` menüje tette.
        with open_index(self._db_path) as conn:
            self._folders.load(
                conn,
                self.paneSort,
                self.paneSortReverse,
                # #1637: a rejtett mappákat ugyanaz a kapcsoló hozza
                # vissza, ami a rejtett fotókat — nem külön beállítás
                include_hidden=self.showHidden,
            )
        self.statusChanged.emit()

    # -- gyűjtemények a bal hasábon (#320) -----------------------------------

    @Slot(str, result=bool)
    def isCollectionCollapsed(self, name: str) -> bool:
        """Csukva van-e a gyűjtemény fejléce (perzisztens)."""
        if name not in COLLECTIONS:
            return False
        stored = self._get_settings().value(
            collection_setting_key(name), DEFAULT_COLLAPSED[name]
        )
        return stored in (True, "true", "1", 1)

    @Slot(str, bool)
    def setCollectionCollapsed(self, name: str, collapsed: bool) -> None:
        """A gyűjtemény-fejléc csukása/nyitása — ismeretlen nevet kihagy."""
        if name not in COLLECTIONS:
            return
        self._get_settings().setValue(collection_setting_key(name), bool(collapsed))
        self.statusChanged.emit()

    # -- bal oldali mappapanel szélessége (#322) -----------------------------

    @Property(int, notify=statusChanged)
    def folderPaneWidth(self):
        """A mappapanel szélessége képpontban — perzisztens, határok közé
        szorítva. Olvashatatlan (kézzel elrontott) érték esetén az
        alapértelmezés jön vissza, nem hiba."""
        raw = self._get_settings().value(
            "view/folderPaneWidth", FOLDER_PANE_WIDTH_DEFAULT
        )
        try:
            width = int(raw)
        except (TypeError, ValueError):
            return FOLDER_PANE_WIDTH_DEFAULT
        return _clamp_folder_pane_width(width)

    @Slot(int)
    def setFolderPaneWidth(self, width: int) -> None:
        """A húzással beállított szélesség mentése (a QML a SplitView
        fogantyújának elengedésekor hívja)."""
        try:
            clamped = _clamp_folder_pane_width(int(width))
        except (TypeError, ValueError):
            return
        self._get_settings().setValue("view/folderPaneWidth", clamped)
        self.statusChanged.emit()

    @Property(str, notify=statusChanged)
    def thumbCaptionMode(self):
        """Indexkép-felirat mód (Nézet → Indexkép felirata) — perzisztens."""
        return self._thumb_caption_mode

    @Slot(str)
    def setThumbCaptionMode(self, mode: str) -> None:
        """Indexkép-felirat mód beállítása (Nézet menü) — 5 kizáró opció."""
        if mode not in _THUMB_CAPTION_MODES:
            return
        self._thumb_caption_mode = mode
        self._get_settings().setValue("view/thumbCaption", mode)
        self.statusChanged.emit()

    # -- felirat-sáv láthatósága (#1816) -------------------------------------

    @Property(bool, notify=statusChanged)
    def captionVisible(self):
        """Látszik-e a nagy kép alatti felirat-sáv.

        #1816: az eredetiben ez TARTÓS állapot, nem pillanatnyi kapcsoló —
        a `Preferences\\LastCaptionButton` őrzi, és a főablak-építő
        (`0x0040bf70`) induláskor visszaállítja. Ha egyszer elrejtetted, a
        Picasa legközelebb is elrejtve indul.

        Alapból LÁTSZIK: a felirat a Picasa egyik fő fogalma, az elrejtés a
        felhasználó külön döntése."""
        value = self._get_settings().value("view/captionVisible", "true")
        return value in (True, "true", "1")

    def setCaptionVisible(self, visible: bool) -> None:
        """A felirat-sáv láthatóságának beállítása.

        SZÁNDÉKOSAN nem `@Slot`: a QML-nek csak a BILLENTŐ-t kínáljuk (az
        eredeti `captionbutton` megfelelője). Egy felületről elérhetetlen
        slot a képesség-őr szerint szakadás — és joggal: néma ígéret."""
        self._get_settings().setValue("view/captionVisible", bool(visible))
        self.statusChanged.emit()

    @Slot()
    def toggleCaptionVisible(self) -> None:
        """A `captionbutton` („Show/Hide Caption") viselkedése."""
        self.setCaptionVisible(not self.captionVisible)

    # -- rejtett MAPPÁK (#1637) ----------------------------------------------

    @Slot(str, result=bool)
    def isFolderHidden(self, path: str) -> bool:
        """Rejtett-e a mappa — a menütétel felirata ebből vált."""
        if not path:
            return False
        with open_index(self._db_path) as conn:
            return is_folder_hidden(conn, path)

    @Slot(str)
    def toggleFolderHidden(self, path: str) -> None:
        """A „Mappa elrejtése / Megjelenítés" menütétel.

        A LEMEZEN semmit nem mozgat — csak jelöl. Elrejtés után a mappa
        eltűnik a bal hasábról, és a Nézet ▸ Rejtett képek kapcsolóval jön
        vissza (ugyanaz az út, mint a rejtett fotóknál); rejtett
        állapotban a kijelölés a mappáról lekerül, hogy ne maradjon egy
        láthatatlan mappa tartalma a rácsban."""
        if not path:
            return
        with open_index(self._db_path) as conn:
            rejtve = is_folder_hidden(conn, path)
            set_folder_hidden(conn, path, not rejtve)
        if not rejtve and not self.showHidden and self._current_folder == path:
            self._current_folder = ""
            self._view_mode = ("folder", "")
            self._show(())
        self._reload_folders()

    # -- rejtett képek (#17) -------------------------------------------------

    @Property(bool, notify=statusChanged)
    def showHidden(self):
        """Nézet → Rejtett képek: látszanak-e a rejtettek (halványítva)."""
        value = self._get_settings().value("view/showHidden", "false")
        return value in (True, "true", "1")

    @Slot(bool)
    def setShowHidden(self, show: bool) -> None:
        # #1637/2: a bal hasábot IS újra kell tölteni. A #1637 első köre a
        # rejtett MAPPÁKAT is erre a kapcsolóra bízta, de itt csak a rács
        # frissült — a mappa így csak egy későbbi, más okból kiváltott
        # újratöltéskor bukkant elő. A kapcsoló látszólag működött (a
        # rejtett KÉPEK azonnal megjelentek), ezért maradt észrevétlen.
        self._get_settings().setValue("view/showHidden", bool(show))
        self._refresh_view()
        self._reload_folders()
        self.statusChanged.emit()

    @Slot()
    def toggleShowHidden(self) -> None:
        self.setShowHidden(not self.showHidden)

    # -- műveletek ----------------------------------------------------------

    @Slot()
    def restoreSession(self) -> None:
        """Az utoljára kiválasztott mappa visszaállítása (session restore).

        Ha nincs mentett mappa, vagy az már nincs az indexben, az első
        mappát választjuk. Nem ír felül kézi választást: csak akkor fut,
        ha még nincs kiválasztott mappa."""
        if self._current_folder:
            return
        saved = self._get_settings().value("session/lastFolder", "")
        with open_index(self._db_path) as conn:
            paths = [
                row["path"]
                for row in conn.execute("SELECT path FROM folders ORDER BY path")
            ]
        if saved and saved in paths:
            self.selectFolder(saved)
        elif paths:
            self.selectFolder(paths[0])

    @Slot(str)
    def focusFolder(self, folder_path: str) -> None:
        """A rács fókusza másik mappára került (#1183) — a bal hasáb
        kiemelése kövesse, de a nézet NE mozduljon.

        Az eredetiben a jelenlegi mappa a rács fókuszát követi: a váltó
        (`0x0056bc10`) elengedi az előző mappa kijelölés-csomópontját
        (`0x718a50`), beállítja az újat (`[this+0xeac]`), és kimondja, hogy
        „a jelenlegi album megváltozott" (`0x56b910`). Ez tehát nem
        nézetváltás — ezért itt NINCS `folderActivated` (nem görgetünk oda,
        a felhasználó már ott van) és nincs feed-újraolvasás sem.

        Csak sima mappanézetben fut: keresés/album nézetben a bal hasáb mást
        mutat, ott a fókusz nem határozza meg a kiemelést.
        """
        if not folder_path or self._view_mode[0] != "folder":
            return
        if folder_path == self._current_folder:
            return
        self._current_folder = folder_path
        self._view_mode = ("folder", folder_path)
        self._folder_description = self._read_folder_description(folder_path)
        self.statusChanged.emit()

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

    def _index_stamp(self) -> tuple:
        """Az index-adatbázis olcsó változás-pecsétje (#142): a db és a
        -wal fájl (mtime_ns, méret) párja. Bármely index-írás (sync,
        fotóművelet — akár külső folyamatból) megváltoztatja, így a
        mappaváltás gyorsútja sosem mutathat elavult feedet."""
        stamp = []
        for path in (self._db_path, Path(f"{self._db_path}-wal")):
            try:
                stat = path.stat()
                stamp.append((stat.st_mtime_ns, stat.st_size))
            except OSError:
                stamp.append(None)
        return tuple(stamp)

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

    @staticmethod
    def _read_folder_description(folder_path: str) -> str:
        """A mappa `[Picasa]/description` kulcsának beolvasása az ini-ből."""
        ini_path = Path(folder_path) / PICASA_INI_NAME
        if not ini_path.exists():
            return ""
        section = load_document(ini_path).section("Picasa")
        return (section.get("description") if section else None) or ""

    # SZÁNDÉKOSAN nincs QML-hivatkozása (#1052): a felület a mappát is átadó
    # `setFolderDescriptionOf(path, …)` alakot hívja; ez a kompatibilitási út.
    @Slot(str)
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

        # #137: ütközésbiztos írás — a párhuzamosan futó eredeti Picasa
        # módosítása nem veszhet el (a mutate tiszta, újrajátszható)
        def mutate(document):
            if text:
                return document.with_value("Picasa", "description", text)
            return document.with_removed("Picasa", "description")

        update_document(ini_path, mutate, backup=True)
        self._descriptions[folder_path] = text
        if folder_path == self._current_folder:
            self._folder_description = text
        self._description_revision += 1
        self.descriptionsChanged.emit()
        self.statusChanged.emit()

    @Slot(str, result=str)
    def folderDescriptionOf(self, folder_path: str) -> str:
        """Mappa-leírás a feed-fejlécnek (#64) — ini-olvasás kis cache-sel,
        hogy NAS-on se olvassunk fejléc-megjelenésenként fájlt."""
        if folder_path not in self._descriptions:
            self._descriptions[folder_path] = self._read_folder_description(
                folder_path
            )
        return self._descriptions[folder_path]

    # -- infó-szövegek (formázás: formatting.py) -----------------------------

    @Slot(int, result=str)
    def photoInfo(self, row: int) -> str:
        """A kék infó-sáv kijelöléskori tartalma, Picasa-stílusban:
        `név   dátum   SZxM képpont   méret`."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return ""
        return formatting.photo_info_text(photos[row], QLocale(), self.tr)

    @Slot("QVariantList", result=str)
    def selectionInfo(self, rows) -> str:
        """A kék sáv szövege TÖBB kijelölt képnél (#1189).

        Az eredetiben ezt a `GetSelectionInfo` (`0x0056fbc0`) állítja elő,
        és a KIJELÖLÉSRŐL ír: darabszám, dátum(tartomány), összméret
        (`il_GetSelectionInfo::3/4/5`). Valódi Picasa-képernyőképpel
        megerősítve: „25 képek   2026. január 2., péntek-2026. május 18.,
        hétfő   37,5 MB a lemezen".

        Ugyanaz a formázó fut, mint a mappa-összesítésre (`statusText`) —
        csak a KIJELÖLT rekordokon. Érvénytelen/ismétlődő sorindexek
        kiszűrve, hogy egy elszállt QML-tömb ne torzítsa az összeget.
        """
        photos = self._photos.photos
        latott: set[int] = set()
        kijelolt = []
        for nyers in rows or ():
            try:
                row = int(nyers)
            except (TypeError, ValueError):
                continue
            if 0 <= row < len(photos) and row not in latott:
                latott.add(row)
                kijelolt.append(photos[row])
        if not kijelolt:
            return self._status
        return formatting.status_text(kijelolt, QLocale(), self.tr, self.tr)

    @Slot(int, result="QVariantList")
    def propertiesOf(self, row: int) -> list:
        """A Tulajdonságok-panel (#13) sorai: {label, value} párok."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return []
        entries = formatting.properties_entries(photos[row], QLocale(), self.tr)
        return [{"label": label, "value": value} for label, value in entries]

    @Slot(int, result=str)
    def viewerInfo(self, row: int) -> str:
        """A néző infó-sávja: `mappa > név   ...   (i / N)` — Picasa-minta."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return ""
        photo = photos[row]
        folder = formatting.PATH_TAIL.split(photo.folder_path)[-1]
        base = self.photoInfo(row).replace(photo.name, f"{folder} > {photo.name}", 1)
        return f"{base}   ({row + 1} / {len(photos)})"

    # -- csillag-szűrő -------------------------------------------------------

    @Slot()
    def showStarred(self) -> None:
        """Csillag-szűrő be — a mappa-kontextus megmarad a visszaváltáshoz."""
        self._view_mode = ("starred", "")
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = starred_photos(conn)
        self._show_filtered(records, time.perf_counter() - started)

    # -- film-szűrő (#1830) --------------------------------------------------

    @Slot()
    def showVideosOnly(self) -> None:
        """„Csak filmek" — az eredeti `moviesearch` szűrője.

        A csillag-szűrő mintáját követi: szűrt NÉZET, nem külön nézetmód,
        a mappa-kontextus megmarad a `clearFilter`-es visszaváltáshoz.
        A `kind` indexmezőre épül, tehát nem igényel újraindexelést."""
        self._view_mode = ("videos", "")
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = video_photos(conn)
        self._show_filtered(records, time.perf_counter() - started)

    # -- virtuális albumok (#9) -----------------------------------------------

    @Slot(str)
    def showAlbum(self, token: str) -> None:
        """Album-szűrő be — a showStarred mintáját követi: az album is
        egy szűrt nézet (nem új nézetmód), a mappa-kontextus megmarad a
        clearFilter-es visszaváltáshoz."""
        if not token:
            return
        self._view_mode = ("album", token)
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = album_photos(conn, token)
        self._show_filtered(records, time.perf_counter() - started)

    @Slot()
    def clearFilter(self) -> None:
        """Szűrő ki („Az összes megtekintése") — vissza a mappa-nézethez."""
        self._filter_active = False
        self._filter_status = ""
        if self._current_folder:
            self.selectFolder(self._current_folder)
        else:
            self._view_mode = ("folder", "")
            self._show(())

    # -- belső --------------------------------------------------------------

    @staticmethod
    def _sync_tree(conn, folder: str, progress=None) -> None:
        """Indirekció a mappa-resynchez (#150): a mixinek ezen át hívják a
        `sync_tree`-t, így a tesztek patch-pontja (a modul-szintű
        `picasapy.app.controller.sync_tree`) változatlanul él.

        #209: az opcionális `progress` callback (worker-szál!) mappánkénti
        haladás-jelzést ad tovább a `sync_tree`-nek."""
        if progress is None:
            sync_tree(conn, folder)
        else:
            sync_tree(conn, folder, progress=progress)

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
            records, elapsed, QLocale(), self.tr
        )
        self._show(records)

    def _refresh_view(self) -> None:
        """Az aktuális nézet újratöltése az indexből (mód szerint)."""
        mode, param = self._view_mode
        if mode == "search":
            with open_index(self._db_path) as conn:
                records = search_photos(conn, param)
            self._show_search_pane(records)
            self._show(records)
        elif mode == "search-folder":
            query, folder = param
            with open_index(self._db_path) as conn:
                all_matches = search_photos(conn, query)
            self._show_search_pane(all_matches)
            self._show(
                tuple(r for r in all_matches if r.folder_path == folder)
            )
        elif mode == "starred":
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
        # #142: a mappaváltás-gyorsút pecsétje — csak a teljes feedet
        # mutató mappa-nézet érvényes hozzá (szűrt/keresett nézet nem)
        self._feed_stamp = (
            self._index_stamp() if self._view_mode[0] == "folder" else None
        )
        # #644: itt látjuk először a friss ini-állapotot — ha egy külső
        # program (a párhuzamosan futó Picasa) letörölte a mi mentett
        # láncunkat, ez az a pont, ahol észrevehetjük. Képenként egyszer
        # jelzünk; a néma eltűnés a legrosszabb változat.
        self._check_external_overwrites(records)
        self._provider.register_photos(records)
        self._photos.set_photos(records)
        self._update_feed_groups(records)
        dates = sorted(r.taken_at for r in records if r.taken_at)
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
            records, QLocale(), self.tr, self.tr
        )
        self.statusChanged.emit()
