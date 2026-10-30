"""Az AppController háttérszinkronja és nézet-újratöltési útvonalai."""

from __future__ import annotations

import time
from PySide6.QtCore import QLocale, Slot
from picasapy.index import (
    album_photos,
    geotagged_photos,
    open_index,
    search_photos,
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
