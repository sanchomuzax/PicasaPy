"""Könyvtár-felügyelet: figyelt mappák, élő figyelés (watchdog), háttér-
szinkron és a busy-állapot (#70) — az AppController könyvtár-szelete (#150).

Mixin-osztály: az `AppController` örökli; a jelzések (syncFinished stb.)
és a slotok a végső osztály meta-objektumába regisztrálódnak, így a QML és
a tesztek felülete változatlan."""

from __future__ import annotations

import sqlite3
import threading
import time
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.index import open_index, remove_root, sync_folder
from picasapy.scanner import LibraryWatcher, write_watched_folders

from .formatting import to_local_path

# #209: a worker-oldali jelzés-ritkítás minimuma (mp) — sok gyorsan kihagyott
# mappánál a queued jelzések ne árasszák el a GUI-szál eseménysorát.
_PROGRESS_EMIT_MIN_S = 0.25
# #209: a rács fokozatos frissítésének minimum-időköze (mp) — a köztes
# eredmények látszanak, de nem fut modell-újratöltés minden kötegnél.
_PROGRESS_RELOAD_MIN_S = 1.5


class LibraryMixin:
    """Figyelt gyökerek kezelése + szinkron-munkák könyvelése."""

    syncFinished = Signal()
    syncFailed = Signal(str)
    # a watchdog szálából érkezik — a Qt automatikusan sorba állítja
    watcherDirty = Signal(list)
    # #70: a háttérmunka (indexelés/thumbnail) állapota változott — a QML
    # busy-animációjának triggere; CSAK tényleges átmenetnél megy ki
    busyChanged = Signal()
    # #209: mappánkénti sync-haladás (mappa, kész, összes, új fotók) — a
    # worker-szálból emittálva; a Qt queued kapcsolattal hozza a GUI-szálra
    syncProgress = Signal(str, int, int, int)
    # #209: a lebegő „Importálás" panel állapota változott
    importChanged = Signal()

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

    # -- „Importálás" folyamat-panel (#209) ----------------------------------

    @Property(bool, notify=importChanged)
    def importPanelVisible(self):
        """Látszódjon-e a lebegő panel: fut érdemi szkennelés (új gyökér
        importja, vagy a rescan új fotókat talált), és a felhasználó nem
        zárta be kézzel."""
        return self._import_visible and not self._import_dismissed

    @Property(str, notify=importChanged)
    def importFolderName(self):
        """Az éppen feldolgozott mappa neve (nem a teljes útvonal)."""
        return Path(self._import_folder).name if self._import_folder else ""

    @Property(int, notify=importChanged)
    def importDoneCount(self):
        return self._import_done

    @Property(int, notify=importChanged)
    def importTotalCount(self):
        return self._import_total

    @Property(int, notify=importChanged)
    def importNewCount(self):
        """Az eddig talált ÚJ képek kumulált száma."""
        return self._import_new

    @Slot()
    def dismissImportPanel(self) -> None:
        """Kézi bezárás — a panel a futó szkennelés végéig nem tér vissza
        (a következő szkennelés újra megjelenítheti)."""
        self._import_dismissed = True
        self.importChanged.emit()

    @Slot(str, int, int, int)
    def _on_sync_progress(self, folder, done, total, new_photos) -> None:
        """Sync-haladás a GUI-szálon (queued jelzés a workerből).

        #216 — késői jelzések védelme: eltávolított (már nem figyelt)
        gyökér alatti mappa haladása nem frissít semmit — se panelt, se
        rácsot. A worker queued jelzései az eltávolítás UTÁN is beeshetnek
        még; ezek itt csendben elnyelődnek.

        A panel automatikusan akkor jelenik meg, ha a szkennelés érdemi:
        új gyökér importja (forced), vagy új fotók kerültek elő — a csendes,
        mindent-kihagyó 5 perces rescan nem villogtatja. A rács fokozatos
        frissítése ritkított (max ~1,5 mp-enként), és a meglévő
        megőrzött-görgetésű újratöltési úton fut, nem kötegenkénti
        modell-resettel."""
        if self._root_for_folder(folder) is None:
            return  # #216: eltávolított gyökér késői jelzése — ignorálva
        self._import_folder = folder
        self._import_done = done
        self._import_total = total
        self._import_new = new_photos
        if not self._import_visible and (self._import_forced or new_photos > 0):
            self._import_visible = True
        self.importChanged.emit()
        now = time.monotonic()
        if (
            new_photos > self._import_new_at_reload
            and now - self._import_last_reload >= _PROGRESS_RELOAD_MIN_S
        ):
            self._import_last_reload = now
            self._import_new_at_reload = new_photos
            # a már feldolgozott (commitolt) mappák fotói jelenjenek meg
            self._reload(preserve_scroll=True)

    @Slot()
    def _on_import_finished(self) -> None:
        """A sync vége (syncFinished): a panel eltűnik, az állapot nulláz —
        a záró teljes frissítést a meglévő _reload_after_sync út végzi."""
        self._import_folder = ""
        self._import_done = 0
        self._import_total = 0
        self._import_new = 0
        self._import_visible = False
        self._import_forced = False
        self._import_dismissed = False
        self._import_new_at_reload = 0
        self.importChanged.emit()

    def _make_progress_emitter(self, should_stop=None):
        """WORKER-SZÁLON futó progress-callback (ld. SyncProgressCallback):
        a jelzés-emisszió ritkított — új fotót hozó mappa és az utolsó mappa
        mindig átmegy, a gyors (kihagyott) mappák max ~4/s ütemben.

        #216: a visszatérési érték megszakítás-kérés a `sync_tree` felé —
        igaz, ha a `should_stop` hívható igazat ad (pl. a gyökér leállítási
        jelzője be van állítva). A ritkítástól függetlenül MINDEN híváskor
        kiértékelődik, így a leállás mappa-határon, másodpercen belül él."""
        state = {"last": 0.0, "new": -1}

        def progress(folder: str, done: int, total: int, new_photos: int) -> bool:
            now = time.monotonic()
            if (
                new_photos != state["new"]
                or done == total
                or now - state["last"] >= _PROGRESS_EMIT_MIN_S
            ):
                state["last"] = now
                state["new"] = new_photos
                self.syncProgress.emit(folder, done, total, new_photos)
            return should_stop() if should_stop is not None else False

        return progress

    # -- leállítási jelzők (#216) --------------------------------------------

    def _cancel_event(self, root: str) -> threading.Event:
        """A gyökér leállítási jelzője (lustán létrehozva — a mixinnek nincs
        __init__-je, a szótár első használatkor születik). Beállítja a
        `removeWatchedFolder`; a worker-oldali should_stop olvassa; az
        újra-hozzáadás (`addWatchedFolder`) törli."""
        try:
            events = self._sync_cancel_events
        except AttributeError:
            events = self._sync_cancel_events = {}
        if root not in events:
            events[root] = threading.Event()
        return events[root]

    def _make_should_stop(self, root: str):
        """Worker-oldali leállás-predikátum egy gyökérhez: igaz, ha a
        leállítási jelző be van állítva VAGY a gyökér már nem figyelt —
        a kettős ellenőrzés a jelző-törlés versenyhelyzetét is lefedi."""
        event = self._cancel_event(root)
        return lambda: event.is_set() or root not in self._roots

    # -- életciklus ----------------------------------------------------------

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

    # -- Mappakezelő ---------------------------------------------------------

    @Slot(str)
    def addWatchedFolder(self, path_or_url: str) -> None:
        """Új figyelt mappa (Mappakezelő / első indítás). file:// URL-t is
        elfogad (a QML FolderDialog azt ad)."""
        path = to_local_path(path_or_url)
        if not path or path in self._roots or not Path(path).is_dir():
            return
        self._roots.append(path)
        self._persist_roots()
        self._restart_watcher()
        self.statusChanged.emit()
        # #216: újra-hozzáadásnál a korábbi eltávolítás leállítási jelzője
        # már nem érvényes — törölni kell, különben a sync azonnal leállna
        self._cancel_event(path).clear()
        # #209: új gyökér importja mindig „nagy" szkennelés — a lebegő
        # panel az első haladás-jelzéstől látszik (forced)
        self._import_forced = True
        progress = self._make_progress_emitter(
            should_stop=self._make_should_stop(path)
        )

        def worker():
            try:
                with open_index(self._db_path) as conn:
                    self._sync_tree(conn, path, progress=progress)
            finally:
                self.syncFinished.emit()

        self._begin_sync_job()
        threading.Thread(target=worker, daemon=True).start()

    @Slot(str)
    def removeWatchedFolder(self, path: str) -> None:
        """„Eltávolítás a Picasából": a gyökér kikerül a figyeltek közül és
        az indexből is (a fájlokhoz természetesen nem nyúlunk).

        #216 — futó szkennelés közben is konzisztens: (1) a leállítási
        jelző beállítása — a gyökér futó syncje a következő mappa-határon
        tisztán leáll; (2) azonnali index-takarítás (`remove_root`,
        SQL-oldali prune); (3) az Importálás-panel eltüntetése, ha épp az
        eltávolított gyökér mappáját mutatta; (4) nézet-frissítés. A worker
        késői jelzéseit a `_on_sync_progress` gyökér-ellenőrzése nyeli el."""
        if path not in self._roots:
            return
        # a jelző MÉG a gyökér-lista módosítása előtt áll be — a worker
        # should_stop-ja bármelyik feltételen (jelző VAGY lista) elkapja
        self._cancel_event(path).set()
        self._roots.remove(path)
        self._persist_roots()
        self._restart_watcher()
        with open_index(self._db_path) as conn:
            remove_root(conn, path)
        # a panel ne ragadjon be: ha az eltávolított gyökér mappáját
        # mutatta, azonnal tűnjön el (állapot-nullázással)
        if self._import_folder and self._root_for_folder(self._import_folder) is None:
            self._on_import_finished()
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

    # -- háttér-szinkron -----------------------------------------------------

    @Slot(list)
    def _on_folders_dirty(self, folders) -> None:
        """A watcher által jelzett (esetleg több) mappa célzott, nem-
        rekurzív szinkronja EGY háttérszálon (#143).

        A `sync_tree` helyett a mappa-pontos `sync_folder`-t hívjuk: a
        watcher konkrét mappát jelez, nincs ok a teljes részfa
        újrajárására. A jelzett mappák koaleszálva, egyetlen worker-
        szálban dolgozódnak fel — a watcher amúgy is debounce-ol
        (`scanner/watcher.py`), így egy jelzésben több mappa is jöhet."""
        if self._sync_running:
            return  # a futó teljes szinkron úgyis lefedi
        paths = [str(f) for f in folders]

        def worker():
            errors = []
            try:
                with open_index(self._db_path) as conn:
                    for folder in paths:
                        root = self._root_for_folder(folder)
                        if root is None:
                            continue  # már nem figyelt gyökér alatt — kihagyva
                        try:
                            # #216: eltávolított gyökér mappája már ne íródjon
                            sync_folder(
                                conn,
                                root,
                                folder,
                                exclude=(),
                                should_stop=self._make_should_stop(root),
                            )
                        except (OSError, RuntimeError):
                            pass  # eltűnt mappa — a periodikus rescan rendezi
                        except sqlite3.OperationalError as error:
                            # busy_timeout lejárt (párhuzamos író) — ez NEM
                            # nyelhető el némán: a felhasználó jelzést kap,
                            # a maradék mappák feldolgozása folytatódik.
                            errors.append(f"{folder}: {error}")
            finally:
                if errors:
                    self.syncFailed.emit("; ".join(errors))
                self.syncFinished.emit()

        self._begin_sync_job()
        threading.Thread(target=worker, daemon=True).start()

    def _root_for_folder(self, folder: str) -> str | None:
        """A jelzett mappához tartozó figyelt gyökér (a `sync_folder`
        védőkorlátjához) — a leghosszabb egyező előtag, ha van ilyen."""
        folder_path = Path(folder).resolve()
        best: str | None = None
        for root in self._roots:
            root_path = Path(root).resolve()
            if folder_path == root_path or folder_path.is_relative_to(root_path):
                if best is None or len(root) > len(best):
                    best = root
        return best

    @Slot()
    def rescan(self) -> None:
        if self._sync_running:
            return  # egy író elég; a futó szinkron végén úgyis frissülünk
        self._sync_running = True
        self._begin_sync_job()
        threading.Thread(target=self._sync_worker, daemon=True).start()

    def _sync_worker(self) -> None:
        """Háttér-szinkron. Egy rossz gyökér (pl. elavult Windows-útvonal a
        WatchedFolders-ből) nem nyelhet el mindent némán: hibánként jelzünk,
        a többi gyökér feldolgozása folytatódik, és a vége mindig
        syncFinished."""
        errors = []
        try:
            with open_index(self._db_path) as conn:
                # pillanatkép: a lista a főszálon menet közben módosulhat
                # (#216, removeWatchedFolder) — az iteráció ettől független
                for root in tuple(self._roots):
                    should_stop = self._make_should_stop(root)
                    if should_stop():
                        continue  # már az indulás előtt eltávolították
                    # gyökerenkénti emitter: a megszakítás-kérés (a progress
                    # visszatérési értéke) csak a saját gyökerére áll be
                    progress = self._make_progress_emitter(should_stop=should_stop)
                    try:
                        self._sync_tree(conn, root, progress=progress)
                    except (OSError, RuntimeError, sqlite3.OperationalError) as error:
                        errors.append(f"{root}: {error}")
        except Exception as error:  # pl. index-migrációs hiba
            errors.append(str(error))
        finally:
            self._sync_running = False
            if errors:
                self.syncFailed.emit("; ".join(errors))
            self.syncFinished.emit()

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
