"""A könyvtárvezérlő teljes újraszinkronjának felelősségei (#6257)."""

from __future__ import annotations

import sqlite3

from PySide6.QtCore import Slot
from picasapy.index import open_index
from picasapy.halozati_ut import halozati_gyoker

from .library_controller_activity import _FILETYPE_SNAPSHOT_UNSET
from .hatter_prioritas import kerjafonal_alacsony_prioritasa
from .library_controller_eltunt_gyoker import atnevezett_gyoker
from .library_controller_sync import _legacy


class _LibrarySyncRescanMixin:
    #: #1977: a `@Slot()` NÉLKÜL a QML `controller.rescan()` hívása
    #: `TypeError: … is not a function`-nel elszáll — a „Frissítés"
    #: menüpont némán nem csinál semmit. A dekorátor a #150-es
    #: mixin-felbontáskor még megvolt (`8de1358e`), azóta kiesett.
    @Slot()
    def rescan(self) -> None:
        """Teljes újrapásztázás — a „Frissítés" menü kézi művelete."""
        self._start_rescan(self._sync_worker)

    def _rescan_network_roots(self) -> None:
        """Az időzített teljes újraolvasás csak UNC-gyökereket pásztáz (#6696)."""
        roots = tuple(
            root for root in tuple(self._roots) if halozati_gyoker(root) is not None
        )
        if roots:
            self._start_rescan(self._sync_worker_roots, args=(roots,))
        else:
            # A célmappa-beállítás frissüljön a helyi könyvtár teljes
            # újraolvasása nélkül is (#6696).
            self._projekt_kimenet_cache = None

    def _start_rescan(self, worker, *, args=()) -> None:
        """Egy teljes vagy hálózati gyökérre szűkített scan elindítása.

        #1456: a `_dirty_running`-ot IS nézi. Enélkül a célzott szinkron
        (`_on_folders_dirty`, #1440) mellé indult egy második index-író, és
        a felhasználó `sqlite3.OperationalError` → `syncFailed` hibát
        látott — ugyanaz a hibaosztály, mint a #1440-ben, csak másik
        belépési ponton.

        **Kihagy, nem várólistáz.** A #1440 `_pending_dirty` várólistája ott
        azért kell, mert egy KONKRÉT mappa jelzése veszne el; itt nincs
        ilyen: a kézi teljes rescan vagy a hálózati gyökerek időzített
        újraolvasása később újra próbál, a futó szinkron végén pedig
        amúgy is frissül a nézet.
        """
        if self._sync_running or self._dirty_running:
            return  # egy író elég; a futó szinkron végén úgyis frissülünk
        # Az OpenCV-t itt szándékosan NEM töltjük elő: az indulás is teljes
        # újraolvasás, és az előtöltés üres könyvtárnál is betöltené (#6510
        # őre). Az MP4/MOV metaadata atom-olvasóval jön; a ritka egyéb
        # videóformátum a régi módon, a háttérszálon tölti be (#6698).
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
        if args:
            self._start_background(
                worker,
                args=args,
                name="picasapy-sync-rescan",
                cancel=self.cancelScan,
            )
        else:
            self._start_background(
                worker,
                name="picasapy-sync-rescan",
                cancel=self.cancelScan,
            )


    def _sync_worker(
        self, enabled_filetypes=_FILETYPE_SNAPSHOT_UNSET
    ) -> None:
        """Teljes indexszinkron a pillanatképen szereplő összes gyökérre."""
        self._sync_worker_roots(tuple(self._roots), enabled_filetypes)

    def _sync_worker_roots(
        self, roots, enabled_filetypes=_FILETYPE_SNAPSHOT_UNSET
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
        kerjafonal_alacsony_prioritasa()
        try:
            with open_index(self._db_path) as conn:
                # pillanatkép: a lista a főszálon menet közben módosulhat
                # (#216, removeWatchedFolder) — az iteráció ettől független
                for root in tuple(roots):
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
                        # #6762: az átnevezett gyökeret a szinkron végén a
                        # #6751 rendezője követi; ez nem hiba
                        if not atnevezett_gyoker(conn, root):
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
