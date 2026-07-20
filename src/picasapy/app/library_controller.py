"""Könyvtár-felügyelet: figyelt mappák, élő figyelés (watchdog), háttér-
szinkron és a busy-állapot (#70) — az AppController könyvtár-szelete (#150).

Mixin-osztály: az `AppController` örökli; a jelzések (syncFinished stb.)
és a slotok a végső osztály meta-objektumába regisztrálódnak, így a QML és
a tesztek felülete változatlan."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.index import open_index, remove_root, sync_folder
from picasapy.scanner import LibraryWatcher, write_watched_folders

from .formatting import to_local_path


class LibraryMixin:
    """Figyelt gyökerek kezelése + szinkron-munkák könyvelése."""

    syncFinished = Signal()
    syncFailed = Signal(str)
    # a watchdog szálából érkezik — a Qt automatikusan sorba állítja
    watcherDirty = Signal(list)
    # #70: a háttérmunka (indexelés/thumbnail) állapota változott — a QML
    # busy-animációjának triggere; CSAK tényleges átmenetnél megy ki
    busyChanged = Signal()

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

        def worker():
            try:
                with open_index(self._db_path) as conn:
                    self._sync_tree(conn, path)
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
                            sync_folder(conn, root, folder, exclude=())
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
                for root in self._roots:
                    try:
                        self._sync_tree(conn, root)
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
