"""Keresés és javaslatok (#7/#45/#49) — az AppController keresési szelete
(#150-es felbontás).

Mixin-osztály: az `AppController` örökli, a slotok a Qt meta-objektumba a
végső osztályon regisztrálódnak — a QML és a tesztek változatlanul a
`controller.search(...)` felületet hívják (nincs viselkedés-változás)."""

from __future__ import annotations

from PySide6.QtCore import Slot

from picasapy.index import open_index, search_photos, search_suggestions

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
        A keresésnek saját darabszáma van: a bal hasáb „Search results for
        … (N)" fejléce (`searchResultCount`)."""
        query = text.strip()
        self._filter_active = False
        self._filter_status = ""
        with open_index(self._db_path) as conn:
            if not query:
                records = (
                    self._feed_records(conn) if self._current_folder else ()
                )
                self._view_mode = ("folder", self._current_folder or "")
            else:
                self._view_mode = ("search", query)
                # #1500: a `color:`/`szín:` keresés gyorsítótárát EZ a
                # hívás tölteti fel (háttérben), és ez jelzi a felületnek,
                # ha még hiányos — enélkül a színkeresés némán, mindig
                # üres listával tért vissza. Színtoken nélküli keresésnél
                # azonnal visszatér, tehát a szöveges keresés útja
                # változatlan. A SORREND fontos: előbb a jelzés, hogy a
                # felhasználó akkor is tájékoztatást kapjon, ha a keresés
                # amúgy nulla találatot ad.
                self._note_color_search(conn, query)
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
