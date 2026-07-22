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
    all_photos,
    open_index,
    search_photos,
    starred_photos,
    sync_tree,
)
from picasapy.ini import load_document, update_document
from picasapy.scanner import PICASA_INI_NAME
from . import formatting
from .effects_controller import EffectsClipboardMixin
from .export_controller import ExportMixin
from .formatting import to_local_path as _to_local_path  # noqa: F401 — a
# fileops_controller kompatibilis import-útja (#150 előtt itt élt a függvény)
from .keywords_controller import KeywordsMixin
from .library_controller import LibraryMixin
from .models import FolderListModel, PhotoGridModel
from .perf_controller import PerfMonitorMixin
from .photo_ops_controller import PhotoOpsMixin
from .search_controller import SearchMixin
from .search_results import group_by_folder, groups_to_qml
from .thumbnail_provider import ThumbnailProvider

_THUMB_CAPTION_MODES = ("none", "filename", "caption", "tags", "resolution")


class AppController(
    SearchMixin,
    KeywordsMixin,
    PhotoOpsMixin,
    ExportMixin,
    EffectsClipboardMixin,
    PerfMonitorMixin,
    LibraryMixin,
    QObject,
):
    statusChanged = Signal()
    # #64: a rács-feed mappa-csoportjai változtak (csak valódi változásnál!)
    feedChanged = Signal()
    # #64: mappa-választás — a rács a feedben ehhez a csoporthoz görget
    folderActivated = Signal(str)
    descriptionsChanged = Signal()

    def __init__(
        self,
        db_path: Path,
        roots: tuple[str, ...],
        provider: ThumbnailProvider,
        parent=None,
        settings=None,
        watched_file: Path | None = None,
    ):
        super().__init__(parent)
        self._db_path = db_path
        self._roots = list(roots)
        self._watched_file = watched_file
        self._provider = provider
        self._folders = FolderListModel(self)
        self._photos = PhotoGridModel(self)
        self._current_folder = ""
        self._status = ""
        self._folder_date = ""
        self._folder_description = ""
        self._sync_running = False
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
        # #70: busy-könyvelés — futó szinkron-munkák száma + a thumbnail-
        # provider aktív kérései; jelzés-alapú, nincs polling
        self._sync_jobs = 0
        self._thumb_active = 0
        self._busy = False
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
        # #173: a háttér-sync frissítsen, de NE görgessen a mappa tetejére
        # (folderActivated) — az elvenné a nézőből visszatérő felhasználó
        # görgetési pozícióját. A scroll-to-top csak explicit mappa-választásé.
        self.syncFinished.connect(self._reload_after_sync)
        self.syncFinished.connect(self._on_sync_job_done)
        # #209: mappánkénti haladás a workerből (queued) + panel-lezárás
        self.syncProgress.connect(self._on_sync_progress)
        self.syncFinished.connect(self._on_import_finished)
        self.watcherDirty.connect(self._on_folders_dirty)
        provider.activeCountChanged.connect(self._on_thumb_active)

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

    @Property(str, notify=statusChanged)
    def folderSort(self):
        return self._get_settings().value("view/folderSort", "date")

    @Property(bool, notify=statusChanged)
    def folderSortReverse(self):
        value = self._get_settings().value("view/folderSortReverse", "false")
        return value in (True, "true", "1")

    @Slot(str)
    def setFolderSort(self, mode: str) -> None:
        """Mappalista-rendezés (Nézet → Mappanézet): date/changed/size/name."""
        if mode not in ("date", "changed", "size", "name"):
            return
        self._get_settings().setValue("view/folderSort", mode)
        self._reload_folders()
        self._refresh_view()  # a feed sorrendje követi a hasábot (#64)

    @Slot()
    def toggleFolderSortReverse(self) -> None:
        self._get_settings().setValue(
            "view/folderSortReverse", not self.folderSortReverse
        )
        self._reload_folders()
        self._refresh_view()  # a feed sorrendje követi a hasábot (#64)

    def _reload_folders(self) -> None:
        with open_index(self._db_path) as conn:
            self._folders.load(
                conn, sort_mode=self.folderSort, reverse=self.folderSortReverse
            )
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

    # -- rejtett képek (#17) -------------------------------------------------

    @Property(bool, notify=statusChanged)
    def showHidden(self):
        """Nézet → Rejtett képek: látszanak-e a rejtettek (halványítva)."""
        value = self._get_settings().value("view/showHidden", "false")
        return value in (True, "true", "1")

    @Slot(bool)
    def setShowHidden(self, show: bool) -> None:
        self._get_settings().setValue("view/showHidden", bool(show))
        self._refresh_view()
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
        """A teljes könyvtár a bal hasáb mappa-sorrendjében (#64)."""
        order = {
            path: i for i, path in enumerate(self._folders.folder_paths())
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
        elapsed = time.perf_counter() - started
        self._filter_active = True
        self._filter_status = formatting.filter_status_text(
            records, elapsed, QLocale(), self.tr
        )
        self._show(records)

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
            with open_index(self._db_path) as conn:
                self._show(starred_photos(conn))
        elif param:
            with open_index(self._db_path) as conn:
                self._show(self._feed_records(conn))

    @Slot()
    def _reload_after_sync(self) -> None:
        """A háttér-sync (syncFinished) utáni frissítés: a görgetési pozíció
        MEGŐRZÉSÉVEL (#173) — folder-módban NEM emittál folderActivated-et,
        így a QML nem görget a mappa tetejére (scrollToGroup). A nézőből
        visszatérve a feed így a megnyitás előtti pozícióján marad."""
        self._reload(preserve_scroll=True)

    def _reload(self, preserve_scroll: bool = False) -> None:
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
                self._folders.load(
                    conn,
                    sort_mode=self.folderSort,
                    reverse=self.folderSortReverse,
                )
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
        # #142: a mappaváltás-gyorsút pecsétje — csak a teljes feedet
        # mutató mappa-nézet érvényes hozzá (szűrt/keresett nézet nem)
        self._feed_stamp = (
            self._index_stamp() if self._view_mode[0] == "folder" else None
        )
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

    def _update_feed_groups(self, records) -> None:
        """Mappa-csoportok a rács-feedhez (#64). feedChanged CSAK valódi
        változásnál megy ki — különben minden háttér-frissítés nullázná a
        rács görgetését."""
        groups = formatting.build_feed_groups(records, QLocale())
        if groups != self._feed_groups:
            self._feed_groups = groups
            self.feedChanged.emit()

    def _update_status(self, records) -> None:
        self._status = formatting.status_text(
            records, QLocale(), self.tr, self.tr
        )
        self.statusChanged.emit()
