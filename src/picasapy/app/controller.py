"""Az alkalmazás vezérlője: index-lekérdezések és a QML közti híd."""

from __future__ import annotations

import re
import threading
import time
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QDate,
    QDateTime,
    QLocale,
    QObject,
    QSettings,
    Signal,
    Slot,
)

from picasapy.export import ExportItem, ExportSettings, export_photos
from picasapy.index import (
    all_photos,
    open_index,
    photos_in_folder,
    remove_root,
    search_photos,
    search_suggestions,
    starred_photos,
    sync_tree,
)
from picasapy.ini import load_document, parse_document, save_document
from picasapy.metadata import write_iptc_caption
from picasapy.scanner import (
    PICASA_INI_NAME,
    LibraryWatcher,
    write_watched_folders,
)
from .models import FolderListModel, PhotoGridModel
from .search_results import group_by_folder, groups_to_qml
from .thumbnail_provider import ThumbnailProvider


_PATH_TAIL = re.compile(r"[/\\]")


def _to_local_path(path_or_url: str) -> str:
    """file:// URL vagy sima útvonal → OS-natív lokális útvonal.

    A QUrl.toLocalFile Windowson per-jeles utat ad (C:/...) — a Path-on
    átfuttatás normalizálja, különben ugyanaz a mappa két alakban
    szerepelhetne a figyeltek közt."""
    from PySide6.QtCore import QUrl

    text = path_or_url.strip()
    if text.startswith("file:"):
        text = QUrl(text).toLocalFile()
    return str(Path(text)) if text else ""

_THUMB_CAPTION_MODES = ("none", "filename", "caption", "tags", "resolution")


class AppController(QObject):
    statusChanged = Signal()
    syncFinished = Signal()
    syncFailed = Signal(str)
    # a watchdog szálából érkezik — a Qt automatikusan sorba állítja
    watcherDirty = Signal(list)
    # #64: a rács-feed mappa-csoportjai változtak (csak valódi változásnál!)
    feedChanged = Signal()
    # #64: mappa-választás — a rács a feedben ehhez a csoporthoz görget
    folderActivated = Signal(str)
    descriptionsChanged = Signal()
    # #16: export kész — (exportált darab, sikertelen darab); háttérszálból
    # érkezik, a Qt automatikusan a főszálra sorolja
    exportFinished = Signal(int, int)
    # #70: a háttérmunka (indexelés/thumbnail) állapota változott — a QML
    # busy-animációjának triggere; CSAK tényleges átmenetnél megy ki
    busyChanged = Signal()

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
        self.syncFinished.connect(self._reload)
        self.syncFinished.connect(self._on_sync_job_done)
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

    # -- busy-állapot (#70) --------------------------------------------------

    @Property(bool, notify=busyChanged)
    def isWorking(self):
        """Fut-e háttérmunka (indexelés/szinkron vagy thumbnail-betöltés) —
        az alsó sáv animációja erre köt."""
        return self._busy

    def _begin_sync_job(self) -> None:
        """Egy háttér-szinkron indul — a főszálon hívandó, a worker
        indítása ELŐTT (a syncFinished zárja le)."""
        self._sync_jobs += 1
        self._update_busy()

    @Slot()
    def _on_sync_job_done(self) -> None:
        self._sync_jobs = max(0, self._sync_jobs - 1)
        self._update_busy()

    @Slot(int)
    def _on_thumb_active(self, count: int) -> None:
        """A thumbnail-provider aktív kéréseinek száma (a provider szálából
        jelezve; a Qt a főszálra sorolja)."""
        self._thumb_active = count
        self._update_busy()

    def _update_busy(self) -> None:
        busy = self._sync_jobs > 0 or self._thumb_active > 0
        if busy != self._busy:
            self._busy = busy
            self.busyChanged.emit()

    # -- műveletek ----------------------------------------------------------

    def start(self) -> None:
        """Indulás: modellek betöltése, háttér-szinkron, élő figyelés.

        Az inotify-figyelő az azonnali frissülést adja; NAS-mounton
        (SMB/NFS) nem érkezik esemény, ezért 5 percenként periodikus
        rescan fut fallbackként (a Picasa is folyamatosan pásztázott)."""
        from PySide6.QtCore import QTimer

        self._reload()
        if not self._current_folder:
            self.restoreSession()
        self.rescan()
        self._watcher = LibraryWatcher(
            tuple(self._roots),
            lambda folders: self.watcherDirty.emit(list(folders)),
        )
        self._watcher.start()
        self._rescan_timer = QTimer(self)
        self._rescan_timer.setInterval(5 * 60 * 1000)
        self._rescan_timer.timeout.connect(self.rescan)
        self._rescan_timer.start()

    def shutdown(self) -> None:
        """Leállítás: figyelő és időzítő leállítása (kilépéskor hívandó)."""
        if self._rescan_timer is not None:
            self._rescan_timer.stop()
        if self._watcher is not None:
            self._watcher.stop()
            self._watcher = None

    # -- Mappakezelő --------------------------------------------------------

    @Property(list, notify=statusChanged)
    def watchedFolders(self):
        return list(self._roots)

    @Slot(str)
    def addWatchedFolder(self, path_or_url: str) -> None:
        """Új figyelt mappa (Mappakezelő / első indítás). file:// URL-t is
        elfogad (a QML FolderDialog azt ad)."""
        path = _to_local_path(path_or_url)
        if not path or path in self._roots or not Path(path).is_dir():
            return
        self._roots.append(path)
        self._persist_roots()
        self._restart_watcher()
        self.statusChanged.emit()

        def worker():
            try:
                with open_index(self._db_path) as conn:
                    sync_tree(conn, path)
            finally:
                self.syncFinished.emit()

        self._begin_sync_job()
        threading.Thread(target=worker, daemon=True).start()

    @Slot(str)
    def removeWatchedFolder(self, path: str) -> None:
        """„Eltávolítás a Picasából": a gyökér kikerül a figyeltek közül és
        az indexből is (a fájlokhoz természetesen nem nyúlunk)."""
        if path not in self._roots:
            return
        self._roots.remove(path)
        self._persist_roots()
        self._restart_watcher()
        with open_index(self._db_path) as conn:
            remove_root(conn, path)
        if self._current_folder and (
            self._current_folder == path
            or Path(self._current_folder).is_relative_to(path)
        ):
            self._current_folder = ""
            self._view_mode = ("folder", "")
            self._show(())
        self._reload()

    def _persist_roots(self) -> None:
        if self._watched_file is not None:
            write_watched_folders(self._watched_file, tuple(self._roots))

    def _restart_watcher(self) -> None:
        if self._watcher is None:
            return  # a start() még nem futott (tesztek, korai hívás)
        self._watcher.stop()
        self._watcher = LibraryWatcher(
            tuple(self._roots),
            lambda folders: self.watcherDirty.emit(list(folders)),
        )
        self._watcher.start()

    @Slot(list)
    def _on_folders_dirty(self, folders) -> None:
        """A watcher által jelzett mappák célzott szinkronja háttérszálon."""
        if self._sync_running:
            return  # a futó teljes szinkron úgyis lefedi
        paths = [str(f) for f in folders]

        def worker():
            try:
                with open_index(self._db_path) as conn:
                    for folder in paths:
                        try:
                            sync_tree(conn, folder)
                        except (OSError, RuntimeError):
                            pass  # eltűnt mappa — a periodikus rescan rendezi
            finally:
                self.syncFinished.emit()

        self._begin_sync_job()
        threading.Thread(target=worker, daemon=True).start()

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

    @Slot()
    def rescan(self) -> None:
        if self._sync_running:
            return  # egy író elég; a futó szinkron végén úgyis frissülünk
        self._sync_running = True
        self._begin_sync_job()
        threading.Thread(target=self._sync_worker, daemon=True).start()

    @Slot(str)
    def selectFolder(self, folder_path: str) -> None:
        """Mappa-választás (#64): a rács a TELJES könyvtár-feedet mutatja a
        bal hasáb sorrendjében — a választott mappához a rács odagörget
        (folderActivated), ahogy az eredeti Picasa tette."""
        self._current_folder = folder_path
        self._view_mode = ("folder", folder_path)
        self._filter_active = False
        self._filter_status = ""
        self._restore_full_folder_pane()
        self._get_settings().setValue("session/lastFolder", folder_path)
        self._folder_description = self._read_folder_description(folder_path)
        with open_index(self._db_path) as conn:
            records = self._feed_records(conn)
        self._show(records)
        self.folderActivated.emit(folder_path)

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
        document = (
            load_document(ini_path) if ini_path.exists() else parse_document("")
        )
        if text:
            document = document.with_value("Picasa", "description", text)
        else:
            document = document.with_removed("Picasa", "description")
        save_document(document, ini_path, backup=True)
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

    @Slot(str)
    def setThumbCaptionMode(self, mode: str) -> None:
        """Indexkép-felirat mód beállítása (Nézet menü) — 5 kizáró opció."""
        if mode not in _THUMB_CAPTION_MODES:
            return
        self._thumb_caption_mode = mode
        self._get_settings().setValue("view/thumbCaption", mode)
        self.statusChanged.emit()

    @Slot(str)
    def search(self, text: str) -> None:
        query = text.strip()
        with open_index(self._db_path) as conn:
            if not query:
                records = self._feed_records(conn) if self._current_folder else ()
                self._view_mode = ("folder", self._current_folder or "")
            else:
                self._view_mode = ("search", query)
                records = search_photos(conn, query)
        if query:
            self._show_search_pane(records)
        else:
            self._restore_full_folder_pane()
        self._show(records)

    def _show_search_pane(self, records) -> None:
        """A bal hasáb keresésre szűkítése (#49): csak a találatos mappák,
        találat-darabszámmal."""
        self._folders.load_matches(group_by_folder(records))
        self._folders_filtered = True
        self._search_result_count = len(records)

    def _restore_full_folder_pane(self) -> None:
        """A teljes mappalista vissza, ha a hasáb keresésre volt szűkítve."""
        if self._folders_filtered:
            self._folders_filtered = False
            self._reload_folders()

    @Slot(str)
    def selectFolderKeepSearch(self, folder_path: str) -> None:
        """Mappa-választás aktív keresés közben (#45, Picasa-viselkedés):
        a keresés megmarad, a találatok az adott mappára szűkülnek.
        Keresés nélkül sima selectFolder."""
        mode, param = self._view_mode
        if mode == "search-folder":
            query = param[0]
        elif mode == "search":
            query = param
        else:
            self.selectFolder(folder_path)
            return
        self._current_folder = folder_path  # a bal paneli kijelölés kövessen
        self._view_mode = ("search-folder", (query, folder_path))
        self._get_settings().setValue("session/lastFolder", folder_path)
        with open_index(self._db_path) as conn:
            all_matches = search_photos(conn, query)
        # a hasáb az ÖSSZES találatos mappát mutatja tovább (#49), hogy
        # át lehessen kattintani a többibe; a rács a mappára szűkül
        self._show_search_pane(all_matches)
        self._show(
            tuple(r for r in all_matches if r.folder_path == folder_path)
        )

    @Slot(int)
    def resyncFolderOfRow(self, row: int) -> None:
        """A sorhoz tartozó mappa resyncje — a néző bezárásakor hívjuk:
        a feedben (#64) a néző át is léphetett másik mappába, ezért nem a
        kiválasztott, hanem az épp nézett kép mappáját frissítjük."""
        photos = self._photos.photos
        if 0 <= row < len(photos):
            self.resyncFolder(photos[row].folder_path)

    @Slot(str)
    def resyncFolder(self, folder_path: str) -> None:
        """Egy mappa újraszinkronja + nézetfrissítés — a néző bezárásakor
        hívjuk (#59): a szerkesztések (filters=) így NAS-on is rögtön
        látszanak a rácson, nem az 5 perces rescanre várva.

        #86: a szinkron HÁTTÉRSZÁLON fut (a _on_folders_dirty útján), így a
        hívó nézetváltás — „Vissza a könyvtárhoz" — hálózati meghajtón sem
        blokkolja a UI-szálat; a végén a syncFinished frissíti a nézetet."""
        if not folder_path:
            return
        self._on_folders_dirty([folder_path])

    @Slot(str, result="QVariantList")
    def searchSuggestions(self, text: str) -> list:
        """Kereső-javaslatok a legördülőnek (#7) — dict-lista a QML-nek.

        Egyelőre csak mappa-javaslatok: az album-sor kiválasztása csak a
        virtuális albumok UI-jával (#9) lesz értelmes."""
        with open_index(self._db_path) as conn:
            return [
                {"kind": s.kind, "name": s.name, "count": s.count, "param": s.param}
                for s in search_suggestions(conn, text)
                if s.kind == "folder"
            ]

    @Slot(int)
    def toggleStar(self, row: int) -> None:
        """Csillag be/ki — a .picasa.ini-be írva (kétirányú kompatibilitás:
        a párhuzamosan futó eredeti Picasa is látja). Levételkor a kulcs
        törlődik, ahogy a Picasa csinálja."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        ini_path = Path(photo.folder_path) / PICASA_INI_NAME
        document = (
            load_document(ini_path) if ini_path.exists() else parse_document("")
        )
        if photo.star:
            document = document.with_removed(photo.name, "star")
        else:
            document = document.with_value(photo.name, "star", "yes")
        save_document(document, ini_path, backup=True)
        with open_index(self._db_path) as conn:
            sync_tree(conn, photo.folder_path)
        self._refresh_view()

    @Slot(int, str)
    def setCaption(self, row: int, text: str) -> None:
        """Felirat mentése — Picasa írási szabály (spec #3): JPEG-nél az
        IPTC-be (a képfájlba) írjuk, minden más formátumnál a .picasa.ini-be,
        ahogy a csillag/forgatás is. Az IPTC-írás sikertelensége esetén
        (pl. sérült fájl) defenzíven az ini-útra esünk vissza."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        text = text.strip()
        is_jpeg = photo.name.lower().endswith((".jpg", ".jpeg"))
        wrote_iptc = False
        if is_jpeg:
            path = Path(photo.folder_path) / photo.name
            wrote_iptc = write_iptc_caption(path, text)
        if not wrote_iptc:
            ini_path = Path(photo.folder_path) / PICASA_INI_NAME
            document = (
                load_document(ini_path) if ini_path.exists() else parse_document("")
            )
            if text:
                document = document.with_value(photo.name, "caption", text)
            else:
                document = document.with_removed(photo.name, "caption")
            save_document(document, ini_path, backup=True)
        with open_index(self._db_path) as conn:
            sync_tree(conn, photo.folder_path)
        self._refresh_view()

    @Slot(list)
    def toggleStarMany(self, rows) -> None:
        """Csillag a teljes kijelölésre (Picasa-viselkedés): ha van még
        csillagozatlan a kijelöltek közt, mindet csillagozza; ha mind az,
        mindről leveszi. Mappánként EGY ini-írás + sync."""
        photos = self._photos.photos
        valid = [
            photos[int(r)] for r in rows if 0 <= int(r) < len(photos)
        ]
        if not valid:
            return
        star_all = not all(p.star for p in valid)

        def mutate(document, photo):
            if star_all:
                return document.with_value(photo.name, "star", "yes")
            return document.with_removed(photo.name, "star")

        self._apply_batch(valid, mutate)

    @Slot(list)
    def rotateRightMany(self, rows) -> None:
        self._rotate_many(rows, 1)

    @Slot(list)
    def rotateLeftMany(self, rows) -> None:
        self._rotate_many(rows, -1)

    def _rotate_many(self, rows, delta: int) -> None:
        photos = self._photos.photos
        valid = [
            photos[int(r)] for r in rows if 0 <= int(r) < len(photos)
        ]
        if not valid:
            return

        def mutate(document, photo):
            steps = (photo.rotate_steps + delta) % 4
            if steps == 0:
                return document.with_removed(photo.name, "rotate")
            return document.with_value(photo.name, "rotate", f"rotate({steps})")

        self._apply_batch(valid, mutate)

    def _apply_batch(self, photos, mutate) -> None:
        """Kötegelt ini-módosítás: mappánként egyetlen (atomikus, backupolt)
        írás és egyetlen resync — sok kijelölt képnél is gyors."""
        by_folder: dict[str, list] = {}
        for photo in photos:
            by_folder.setdefault(photo.folder_path, []).append(photo)
        for folder, folder_photos in by_folder.items():
            ini_path = Path(folder) / PICASA_INI_NAME
            document = (
                load_document(ini_path) if ini_path.exists() else parse_document("")
            )
            for photo in folder_photos:
                document = mutate(document, photo)
            save_document(document, ini_path, backup=True)
            with open_index(self._db_path) as conn:
                sync_tree(conn, folder)
        self._refresh_view()

    @Slot(int)
    def rotateRight(self, row: int) -> None:
        self._apply_rotate(row, 1)

    @Slot(int)
    def rotateLeft(self, row: int) -> None:
        self._apply_rotate(row, -1)

    def _apply_rotate(self, row: int, delta: int) -> None:
        """Nem-destruktív forgatás: rotate=rotate(n) az ini-be; n=0-nál a
        kulcs törlődik, így a teljes kör bitre pontos round-trip."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        steps = (photo.rotate_steps + delta) % 4
        ini_path = Path(photo.folder_path) / PICASA_INI_NAME
        document = (
            load_document(ini_path) if ini_path.exists() else parse_document("")
        )
        if steps == 0:
            document = document.with_removed(photo.name, "rotate")
        else:
            document = document.with_value(photo.name, "rotate", f"rotate({steps})")
        save_document(document, ini_path, backup=True)
        with open_index(self._db_path) as conn:
            sync_tree(conn, photo.folder_path)
        self._refresh_view()

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

    @Slot(int, result=str)
    def photoInfo(self, row: int) -> str:
        """A kék infó-sáv kijelöléskori tartalma, Picasa-stílusban:
        `név   dátum   SZxM képpont   méret`."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return ""
        photo = photos[row]
        locale = QLocale()
        parts = [photo.name]
        if photo.taken_at:
            taken = QDateTime.fromString(photo.taken_at, "yyyy-MM-ddTHH:mm:ss")
            parts.append(locale.toString(taken, QLocale.FormatType.ShortFormat))
        if photo.width and photo.height:
            parts.append(
                self.tr("%1x%2 pixels")
                .replace("%1", str(photo.width))
                .replace("%2", str(photo.height))
            )
        parts.append(_format_size(photo.size, locale, self.tr))
        return "   ".join(parts)

    @Slot(int, result=str)
    def viewerInfo(self, row: int) -> str:
        """A néző infó-sávja: `mappa > név   ...   (i / N)` — Picasa-minta."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return ""
        photo = photos[row]
        folder = _PATH_TAIL.split(photo.folder_path)[-1]
        base = self.photoInfo(row).replace(photo.name, f"{folder} > {photo.name}", 1)
        return f"{base}   ({row + 1} / {len(photos)})"

    @Slot()
    def showStarred(self) -> None:
        """Csillag-szűrő be — a mappa-kontextus megmarad a visszaváltáshoz."""
        self._view_mode = ("starred", "")
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = starred_photos(conn)
        elapsed = time.perf_counter() - started
        self._filter_active = True
        self._filter_status = self._format_filter_status(records, elapsed)
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

    @Slot(list, str, int, int)
    def exportRows(self, rows, target_dir: str, max_dimension: int,
                   jpeg_quality: int) -> None:
        """Kijelölt sorok exportja célmappába (#16, Ctrl+Shift+S).

        A forgatás (rotate_steps) beleég a célfájlba; max_dimension<=0 =
        eredeti méret. Háttérszálon fut (NAS-on percekig tarthat), a végén
        exportFinished(exportált, sikertelen)."""
        photos = self._photos.photos
        items = tuple(
            ExportItem(
                source=Path(photos[int(r)].folder_path) / photos[int(r)].name,
                rotate_steps=photos[int(r)].rotate_steps,
            )
            for r in rows
            if 0 <= int(r) < len(photos)
        )
        target = _to_local_path(target_dir)
        if not items or not target:
            self.exportFinished.emit(0, 0)
            return
        settings = ExportSettings(
            max_dimension=max_dimension if max_dimension > 0 else None,
            jpeg_quality=jpeg_quality,
        )

        def worker():
            report = export_photos(items, Path(target), settings)
            self.exportFinished.emit(len(report.exported), len(report.failed))

        threading.Thread(target=worker, daemon=True).start()

    def _format_filter_status(self, records, elapsed: float) -> str:
        locale = QLocale()
        folders = len({r.folder_path for r in records})
        total_gb = sum(r.size for r in records) / (1024**3)
        return (
            self.tr("%1 folders / %2 pictures visible (%3 seconds) %4 GB")
            .replace("%1", str(folders))
            .replace("%2", str(len(records)))
            .replace("%3", locale.toString(elapsed, "f", 3))
            .replace("%4", locale.toString(total_gb, "f", 1))
        )

    # -- belső --------------------------------------------------------------

    def _sync_worker(self) -> None:
        """Háttér-szinkron. Egy rossz gyökér (pl. elavult Windows-útvonal a
        WatchedFolders-ből) nem nyelhet el mindent némán: hibánként jelzünk,
        a többi gyökér feldolgozása folytatódik, és a vége mindig
        syncFinished."""
        errors = []
        try:
            with open_index(self._db_path) as conn:
                for root in self._roots:
                    try:
                        sync_tree(conn, root)
                    except (OSError, RuntimeError) as error:
                        errors.append(f"{root}: {error}")
        except Exception as error:  # pl. index-migrációs hiba
            errors.append(str(error))
        finally:
            self._sync_running = False
            if errors:
                self.syncFailed.emit("; ".join(errors))
            self.syncFinished.emit()

    def _reload(self) -> None:
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
            self.selectFolder(self._current_folder)
        else:
            self._update_status(())
            self.restoreSession()

    def _show(self, records) -> None:
        self._provider.register_photos(records)
        self._photos.set_photos(records)
        self._update_feed_groups(records)
        dates = sorted(r.taken_at for r in records if r.taken_at)
        self._folder_date = _long_date(dates[0], QLocale()) if dates else ""
        search_active = self._view_mode[0] in ("search", "search-folder")
        self._search_groups = group_by_folder(records) if search_active else ()
        self._update_status(records)

    def _update_feed_groups(self, records) -> None:
        """Mappa-csoportok a rács-feedhez (#64): az egymást követő azonos
        mappájú futamok. feedChanged CSAK valódi változásnál megy ki —
        különben minden háttér-frissítés nullázná a rács görgetését."""
        runs: list[list] = []
        for row, record in enumerate(records):
            if not runs or runs[-1][0] != record.folder_path:
                runs.append([record.folder_path, row, 0])
            runs[-1][2] += 1
        locale = QLocale()
        groups = tuple(
            {
                "path": path,
                "name": _PATH_TAIL.split(path)[-1],
                "start": start,
                "count": count,
                "dateText": _first_date_text(
                    records[start : start + count], locale
                ),
            }
            for path, start, count in runs
        )
        if groups != self._feed_groups:
            self._feed_groups = groups
            self.feedChanged.emit()

    def _update_status(self, records) -> None:
        if not records:
            self._status = self.tr("0 pictures")
        else:
            locale = QLocale()
            total_mb = sum(r.size for r in records) / (1024 * 1024)
            dates = sorted(r.taken_at for r in records if r.taken_at)
            date_part = ""
            if dates:
                first = _long_date(dates[0], locale)
                last = _long_date(dates[-1], locale)
                date_part = first if first == last else f"{first}-{last}"
            self._status = self.tr("%n picture(s)", "", len(records)) + (
                f"   {date_part}   " if date_part else "   "
            ) + self.tr("%1 MB on disk").replace(
                "%1", locale.toString(total_mb, "f", 1)
            )
        self.statusChanged.emit()


def _long_date(iso: str, locale: QLocale) -> str:
    """Picasa-stílusú hosszú dátum: `2026. január 2., péntek`."""
    date = QDate.fromString(iso[:10], "yyyy-MM-dd")
    return locale.toString(date, QLocale.FormatType.LongFormat)


def _first_date_text(records, locale: QLocale) -> str:
    """A csoport fejléc-dátuma: a legkorábbi felvétel hosszú dátuma."""
    dates = sorted(r.taken_at for r in records if r.taken_at)
    return _long_date(dates[0], locale) if dates else ""


def _format_size(size_bytes: int, locale: QLocale, tr) -> str:
    if size_bytes < 1024 * 1024:
        return tr("%1 KB").replace("%1", str(round(size_bytes / 1024)))
    return tr("%1 MB").replace(
        "%1", locale.toString(size_bytes / (1024 * 1024), "f", 1)
    )
