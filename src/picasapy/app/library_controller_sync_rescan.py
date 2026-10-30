"""A könyvtárvezérlő teljes újraszinkronjának felelősségei (#6257)."""

from __future__ import annotations

import sqlite3

from PySide6.QtCore import Slot
from picasapy.index import open_index

from .library_controller_activity import _FILETYPE_SNAPSHOT_UNSET
from .library_controller_sync import _legacy


class _LibrarySyncRescanMixin:
    #: #1977: a `@Slot()` NÉLKÜL a QML `controller.rescan()` hívása
    #: `TypeError: … is not a function`-nel elszáll — a „Frissítés"
    #: menüpont némán nem csinál semmit. A dekorátor a #150-es
    #: mixin-felbontáskor még megvolt (`8de1358e`), azóta kiesett.
    @Slot()
    def rescan(self) -> None:
        """Teljes újrapásztázás — az ötperces időzítő és a „Frissítés" menü.

        #1456: a `_dirty_running`-ot IS nézi. Enélkül a célzott szinkron
        (`_on_folders_dirty`, #1440) mellé indult egy második index-író, és
        a felhasználó `sqlite3.OperationalError` → `syncFailed` hibát
        látott — ugyanaz a hibaosztály, mint a #1440-ben, csak másik
        belépési ponton.

        **Kihagy, nem várólistáz.** A #1440 `_pending_dirty` várólistája ott
        azért kell, mert egy KONKRÉT mappa jelzése veszne el; itt nincs
        ilyen: a rescan az egészet nézi, az időzítő öt perc múlva újra
        próbál, és a futó szinkron végén amúgy is frissül a nézet.
        """
        if self._sync_running or self._dirty_running:
            return  # egy író elég; a futó szinkron végén úgyis frissülünk
        self._sync_running = True
        self._sync_worker_filetype_snapshot = getattr(
            self, "_filetype_scan_snapshot", None
        )
        # #438/#505: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430) —
        # a busy-bejelentkezés is ITT, a mixinben történik (ld. worker_thread.py)
        # #1123: a projekt-célmappák gyorstára itt ürül — így a beállítás
        # megváltozása vagy egy újonnan létrejött célmappa legkésőbb öt
        # perc múlva bekerül a tízmásodperces körbe.
        self._projekt_kimenet_cache = None
        self._start_background(
            self._sync_worker,
            name="picasapy-sync-rescan",
            cancel=self.cancelScan,
        )


    def _sync_worker(
        self, enabled_filetypes=_FILETYPE_SNAPSHOT_UNSET
    ) -> None:
        """Háttér-szinkron. Egy rossz gyökér (pl. elavult Windows-útvonal a
        WatchedFolders-ből) nem nyelhet el mindent némán: hibánként jelzünk,
        a többi gyökér feldolgozása folytatódik, és a vége mindig
        syncFinished."""
        if enabled_filetypes is _legacy()._FILETYPE_SNAPSHOT_UNSET:
            enabled_filetypes = getattr(
                self,
                "_sync_worker_filetype_snapshot",
                getattr(self, "_filetype_scan_snapshot", None),
            )
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
                        self._sync_folder_manager_tree(
                            conn,
                            root,
                            progress=progress,
                            enabled_filetypes=enabled_filetypes,
                        )
                    except (OSError, RuntimeError, sqlite3.OperationalError) as error:
                        errors.append(f"{root}: {error}")
                # #1601: a hasáb ini-alapú gyűjteményei MÉG ITT, a
                # háttérszálon állnak elő — a `syncFinished` utáni
                # `_reload()` így csak átveszi őket, és a felület szála
                # egyetlen `.picasa.ini`-t sem olvas. A söprés a szinkron
                # UTÁN fut, hogy a frissen felvett mappák is benne legyenek.
                self._precompute_side_pane(conn)
        except Exception as error:  # pl. index-migrációs hiba
            errors.append(str(error))
        finally:
            self._sync_running = False
            if errors:
                self.syncFailed.emit("; ".join(errors))
            self.syncFinished.emit()
