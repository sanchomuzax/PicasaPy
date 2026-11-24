"""Az AppController háttérszinkronja és nézet-újratöltési útvonalai."""

from __future__ import annotations

import time
from PySide6.QtCore import QLocale, QTimer, Slot
from picasapy.halozati_ut import fajlrendszer_gyoker
from picasapy.index import (
    album_photos,
    geotagged_photos,
    open_index,
    recently_updated_photos,
    starred_photos,
    video_photos,
)
from . import formatting

_FILETYPE_SNAPSHOT_UNSET = object()


class AppControllerSyncMixin:
    def _sync_tree(
        self,
        conn,
        folder: str,
        progress=None,
        enabled_filetypes=_FILETYPE_SNAPSHOT_UNSET,
        *,
        incremental: bool | None = None,
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
        if incremental is not None:
            kwargs["incremental"] = incremental
        from . import controller as controller_module

        controller_module.sync_tree(conn, folder, **kwargs)

    def _show_filtered(self, records, elapsed: float) -> None:
        """Szűrt nézet megjelenítése a ZÖLD EREDMÉNYSÁV szövegével együtt.

        #1443: eddig csak a `showStarred`/`showAlbum` állította a sáv
        szövegét, az újralekérdezés (`_refresh_view`) nem — így a
        „N folders / M pictures visible" a csillag levétele után elavult
        darabszámot mutatott, miközben a rács már helyesen frissült.
        A szöveget a `_show` közben kimenő `statusChanged` viszi ki, ezért
        a beállítás sorrendben ELŐTTE áll."""
        # #7414: a zöld sáv darabszáma is a látható (típus szerint szűrt) halmazt
        # számolja, nem az indexben megmaradt kikapcsolt típusú sorokat.
        records = self._without_disabled_filetypes(records)
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
                records = self._search_matches(conn, param)
            records = self._filter_search_hidden(records)
            self._show_search_pane(records)
            # #4531: a zöld sáv (és a visszalépő gomb) a frissítésnél sem tűnhet el
            self._show_search_results(records, time.perf_counter() - started)
        elif mode == "search-folder":
            query, folder = param
            started = time.perf_counter()
            with open_index(self._db_path) as conn:
                all_matches = self._search_matches(conn, query)
            all_matches = self._filter_search_hidden(all_matches)
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
        elif mode == "recent_album":
            started = time.perf_counter()
            with open_index(self._db_path) as conn:
                records = recently_updated_photos(conn)
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
        # #6695: kifejezett felhasználói lépés (névadás) után a hasáb
        # azonnal frissüljön, hideg gyorstárnál is (a main is itt söpört).
        with open_index(self._db_path) as conn:
            self._refresh_side_pane_cache(conn)
        self._reload(preserve_scroll=True)

    @Slot()
    def _reload_after_sync(self) -> None:
        """A háttér-sync (syncFinished) utáni frissítés: a görgetési pozíció
        MEGŐRZÉSÉVEL (#173) — folder-módban NEM emittál folderActivated-et,
        így a QML nem görget a mappa tetejére (scrollToGroup). A nézőből
        visszatérve a feed így a megnyitás előtti pozícióján marad."""
        self._reload(preserve_scroll=True)
        folder = getattr(self, "_deferred_folder_activation", None)
        self._deferred_folder_activation = None
        if folder and folder == self._current_folder:
            self.folderActivated.emit(folder)

    def _emit_sync_finished_if_changed(self) -> None:
        """#6695: a háttérmunka végén csak tényleges változásnál jelez."""
        if getattr(self, "_last_sync_changed", False):
            self.syncFinished.emit()

    @Slot()
    def _reload_after_sync_if_changed(self) -> None:
        """A syncFinished nézeteit csak tényleges index- vagy ini-változás frissíti."""
        current_folder = getattr(self, "_current_folder", "")
        slow_network_folder = bool(
            current_folder and fajlrendszer_gyoker(current_folder) is not None
        )
        if not slow_network_folder:
            # Helyi lemezen maradjon a főág azonnali viselkedése. A QML
            # modell késleltetése és a szinkron utáni eseményköri rés csak
            # hálózati fájlrendszeren védi a megnyitott nézőt.
            self._sync_reload_idle_ready = False
            self._sync_reload_idle_pending = False
            self._deferred_sync_reload = False
            if getattr(self, "_last_sync_changed", True) is False:
                return
            self._reload(preserve_scroll=True)
            return
        idle_ready = getattr(self, "_sync_reload_idle_ready", False)
        self._sync_reload_idle_ready = False
        edit_controller = getattr(self, "_edit_controller_for_sync", None)
        if edit_controller is not None and getattr(edit_controller, "_photo_id", ""):
            # A néző az indexet is használja; a teljes feed újraépítése közben
            # a főszál a néző QML-kötéseit blokkolná. A néző lezárásakor kért
            # mappa-resync syncFinished-je majd érvényesíti az elmaradt frissítést.
            self._deferred_sync_reload = True
            return
        deferred = getattr(self, "_deferred_sync_reload", False)
        grace_until = getattr(self, "_sync_reload_grace_until", 0.0)
        if grace_until > time.monotonic():
            self._deferred_sync_reload = True
            QTimer.singleShot(
                max(1, int((grace_until - time.monotonic()) * 1000)),
                self._finish_sync_reload_grace,
            )
            return
        if getattr(self, "_last_sync_changed", True) is False and not deferred:
            return
        if (
            not deferred
            and self._view_mode[0] == "folder"
            and not self.backupFilterActive
            and self._feed_stamp is not None
            and self._feed_stamp == self._index_stamp()
        ):
            # A ritkított progressz-frissítés már ezt az indexállapotot
            # mutatja. A záró teljes feed-újraépítés csak újra lefuttatná a
            # drága QML-csoportkötéseket, miközben semmi sem változott.
            return
        if not idle_ready:
            # A QML a mappa választása után néhány eseményből kezdi a kép
            # szerkesztését. Engedjük megérkezni ezt a jelzést, mielőtt a
            # feed teljes újraépítése a nézőnyitással versenyezne.
            self._deferred_sync_reload = True
            if not getattr(self, "_sync_reload_idle_pending", False):
                self._sync_reload_idle_pending = True
                QTimer.singleShot(100, self._finish_sync_reload_after_idle)
            return
        self._deferred_sync_reload = False
        self._reload(preserve_scroll=True, defer_feed_refresh=True)

    @Slot()
    def _finish_sync_reload_after_idle(self) -> None:
        """Egy eseményköri rés után újraellenőrzi, kell-e feedfrissítés."""
        self._sync_reload_idle_pending = False
        current_folder = getattr(self, "_current_folder", "")
        if not current_folder or fajlrendszer_gyoker(current_folder) is None:
            return
        self._sync_reload_idle_ready = True
        self._reload_after_sync_if_changed()

    @Slot()
    def _finish_sync_reload_grace(self) -> None:
        """A mappaváltást követő nézőnyitásnak ad egy eseménykört."""
        current_folder = getattr(self, "_current_folder", "")
        if not current_folder or fajlrendszer_gyoker(current_folder) is None:
            self._sync_reload_grace_until = 0.0
            return
        if getattr(self, "_sync_reload_grace_until", 0.0) > time.monotonic():
            return
        self._sync_reload_grace_until = 0.0
        edit_controller = getattr(self, "_edit_controller_for_sync", None)
        if edit_controller is not None and getattr(edit_controller, "_photo_id", ""):
            return
        if getattr(self, "_deferred_sync_reload", False):
            self._reload_after_sync_if_changed()

    def _schedule_sync_feed_refresh(self) -> None:
        """A sync utáni feedfrissítés külön eseményköri lépésben fusson.

        A néző bezárásakor a feed modelljének visszakapcsolása már önmagában
        QML-munkát végez. Ha ugyanebben az eseményben olvassuk újra az indexet
        és cseréljük le a feedet, a két költség összeadódik és megakaszthatja
        a felületet. Az előkészítő `_reload` ezért csak egy késleltetett
        frissítést ütemez.
        """
        if getattr(self, "_sync_feed_refresh_pending", False):
            return
        self._sync_feed_refresh_pending = True
        QTimer.singleShot(100, self._finish_sync_feed_refresh)

    def _finish_sync_feed_refresh(self) -> None:
        self._sync_feed_refresh_pending = False
        self._refresh_view()

    def _reload(
        self,
        preserve_scroll: bool = False,
        defer_collections: bool = False,
        defer_feed_refresh: bool = False,
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
                # #321: a fa sorrendje rögzített; #6751: a kis képek szűrője itt is
                self._folders.load(
                    conn,
                    kis_kepek_rejtve=self.showOnlyBigImages,
                    enabled_filetypes=getattr(
                        self, "_filetype_scan_snapshot", None
                    ),
                )
                self._load_albums(conn)  # #9: a bal hasáb albumlistája
                # #26 (Emberek) + #1029 (Projektek): mindkettő a `.picasa.ini`-kből
                # él, ezért EGY söprésből áll elő (#1601). Induláskor pedig
                # egyáltalán nem itt, hanem a háttér-szinkron szálán.
                if not defer_collections:
                    self._load_side_pane(conn)
        if mode != "folder":
            # #38: aktív keresés/szűrő a háttér-sync után is megmarad —
            # a selectFolder eldobná, ezért csak a nézetet frissítjük.
            if defer_feed_refresh:
                self._schedule_sync_feed_refresh()
            else:
                self._refresh_view()
        elif self._current_folder:
            # #173: háttér-sync után csak a feedet frissítjük (folderActivated
            # nélkül) — a scroll-to-top csak explicit mappa-választásé. Induláskor
            # (preserve_scroll=False) viszont a selectFolder a visszaállított
            # mappához görget, ahogy eddig.
            if preserve_scroll:
                if defer_feed_refresh:
                    self._schedule_sync_feed_refresh()
                else:
                    self._refresh_view()
            else:
                self.selectFolder(self._current_folder)
        else:
            self._update_status(())
            self.restoreSession()
