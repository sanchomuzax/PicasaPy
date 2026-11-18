"""Keresés és javaslatok (#7/#45/#49) — az AppController keresési szelete
(#150-es felbontás).

Mixin-osztály: az `AppController` örökli, a slotok a Qt meta-objektumba a
végső osztályon regisztrálódnak — a QML és a tesztek változatlanul a
`controller.search(...)` felületet hívják (nincs viselkedés-változás)."""

from __future__ import annotations

import time

from PySide6.QtCore import Slot

from picasapy.index import open_index, search_photos, search_suggestions
from picasapy.index.queries import _normalize_search_query

from .search_button_filter import (
    BUTTON_FILTERS,
    SEARCH_MODES,
    intersect_with_button,
)
from .search_results import group_by_folder


class SearchMixin:
    """Keresés, kereső-javaslatok és a bal hasáb találat-szűkítése."""

    @Slot(str)
    def search(self, text: str) -> None:
        """Szabadszavas keresés; üres szöveg vissza a mappa-feedhez.

        #1515: a keresés a CSILLAGOZOTT/ALBUM szűrőt is leváltja, ezért a
        zöld eredménysávot (`filterActive`) kikapcsoljuk — ahogy a
        `selectFolder` és a `clearFilter` is teszi. Enélkül a
        Csillagozottakból a keresőmezőbe gépelve a sáv OTTMARADT a szűrő
        elavult darabszámával, miközben a rács már a találatokat mutatta.
        #4531: nem üres keresésnél a sáv újra bekapcsol, de a keresés SAJÁT
        darabszámával - rajta ül a „Back to View All" gomb.
        #7081: a nézetállapot (`searchQuery`, a mentett album neve) a
        BEÍRT szöveget őrzi; az eredeti tisztítás és szóhatár-bontás csak az
        illesztéshez (`matching`) kell, és a `search_photos` maga is ezt
        végzi.
        #7191: a csillag-, arc- és geocímke-gomb a szöveggel KÖZÖS állapot
        (az eredetiben a szöveg és a gomb szava egy listában van, a találat a
        metszet). A bekapcsolt gomb ezért a keresés közben is él, és a szöveg
        törlése (üres `text`) a gombot megtartja: a gomb nézetére lépünk."""
        query = text.strip()
        matching = _normalize_search_query(query)
        button = self._active_button_filter()
        if not query and button:
            self._restore_full_folder_pane()
            self._show_button_view(button)
            return
        self._filter_active = False
        self._filter_status = ""
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            if not query:
                records = (
                    self._feed_records(conn) if self._current_folder else ()
                )
                self._view_mode = ("folder", self._current_folder or "")
            else:
                self._search_button = button
                self._view_mode = ("search", query)
                # #1500: a `color:`/`szín:` keresés gyorsítótárát EZ a
                # hívás tölteti fel (háttérben), és ez jelzi a felületnek,
                # ha még hiányos — enélkül a színkeresés némán, mindig
                # üres listával tért vissza. Színtoken nélküli keresésnél
                # azonnal visszatér, tehát a szöveges keresés útja
                # változatlan. A SORREND fontos: előbb a jelzés, hogy a
                # felhasználó akkor is tájékoztatást kapjon, ha a keresés
                # amúgy nulla találatot ad.
                self._note_color_search(conn, matching)
                records = self._search_matches(conn, query)
        if query:
            records = self._filter_search_hidden(records)
            self._show_search_pane(records)
            self._show_search_results(records, time.perf_counter() - started)
        else:
            self._restore_full_folder_pane()
            self._show(records)

    def _filter_search_hidden(self, records: tuple | list) -> tuple:
        """A rejtett képek szűrése a keresési találatokból (#7194).

        Az eredetiben a keresés eleve kizárja a rejtett képeket
        (`Preferences\\ShowHidden` hiányában, 0x00660ca2). A bal hasáb, a
        darabszám és a zöld sáv előtt szűrünk, hogy mind ugyanazt a látható
        halmazt mutassa.
        """
        if not self.showHidden:
            return tuple(r for r in records if not r.hidden)
        return tuple(records)

    def _show_search_results(self, records, elapsed: float) -> None:
        """Keresési találatok a ZÖLD SÁVVAL (#4531).

        A sáv hordozza a „Vissza az összes megtekintéséhez" gombot, ezért
        szöveges keresés után is kell (az eredetiben a keresősáv
        `viewallbutton`-ja). A darabszám mindig az épp megjelenő találatokból
        készül, így nem avulhat el (#1443/#1515 tanulsága)."""
        self._show_filtered(records, elapsed)

    def _active_button_filter(self) -> str:
        """A most bekapcsolt csillag-/arc-/geocímke-gomb neve, vagy üres (#7191).

        Keresés közben a keresés mellé kötött gomb (`_search_button`), egyébként
        a gomb saját nézetmódja. Mindig a pillanatnyi nézetmódból számolódik,
        ezért egy másik nézetre váltás után nem maradhat elavult gomb."""
        mode = self._view_mode[0]
        if mode in SEARCH_MODES:
            return self._search_button
        return mode if mode in BUTTON_FILTERS else ""

    def _search_matches(self, conn, query: str):
        """A keresés találatai a bekapcsolt gombbal metszve (#7191).

        A bal hasáb, a darabszám és a rács ugyanebből a halmazból épül."""
        return intersect_with_button(
            conn, search_photos(conn, query), self._search_button
        )

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
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            all_matches = self._search_matches(conn, query)
        all_matches = self._filter_search_hidden(all_matches)
        # a hasáb az ÖSSZES találatos mappát mutatja tovább (#49), hogy
        # át lehessen kattintani a többibe; a rács a mappára szűkül
        self._show_search_pane(all_matches)
        self._show_search_results(
            tuple(r for r in all_matches if r.folder_path == folder_path),
            time.perf_counter() - started,
        )

    @Slot(str, result="QVariantList")
    def searchSuggestions(self, text: str) -> list:
        """Mappa-, album- és kulcsszó-javaslatok a legördülőnek.

        Minden adat az indexből jön; gépeléskor nem olvassuk be újra a
        mappák `.picasa.ini` fájljait.
        """
        with open_index(self._db_path) as conn:
            return [
                {"kind": s.kind, "name": s.name, "count": s.count, "param": s.param}
                for s in search_suggestions(conn, text, include_albums=True)
            ]
