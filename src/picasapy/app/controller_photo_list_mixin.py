"""Az AppController mappa- és fotólistáinak összeállítása és megjelenítése."""

from __future__ import annotations

import logging

from PySide6.QtCore import QLocale, QObject, Qt, Signal, Slot
from picasapy.index import albums_in_index, count_recently_updated_photos, open_index
from picasapy.scanner.filetypes import media_kind_if_enabled
from . import formatting
from .models import folder_order
from .search_button_filter import AGE_KEEPING_MODES
from .small_picture_filter import is_big_picture
from .search_results import group_by_folder

_log = logging.getLogger(__name__)


class InitialFeedSignals(QObject):
    """Az induláskori olvasószál eredményét a felület szálának adja át."""

    ready = Signal(int, object, str)


class AppControllerPhotoListMixin:
    def _start_initial_feed_load(self) -> None:
        """A meglévő könyvtár képlistáját a bejárás előtt olvassa be."""
        self._initial_feed_generation = getattr(self, "_initial_feed_generation", 0) + 1
        generation = self._initial_feed_generation
        folder_sort = self.folderSort
        folder_sort_reverse = self.folderSortReverse
        pane_sort = self.paneSort
        pane_sort_reverse = self.paneSortReverse
        initial_feed_signals = InitialFeedSignals(self)
        initial_feed_signals.ready.connect(
            self._on_initial_feed_ready, Qt.ConnectionType.QueuedConnection
        )
        self._initial_feed_signals = initial_feed_signals

        def load_feed() -> None:
            try:
                before = self._index_stamp()
                with open_index(self._db_path) as conn:
                    records = self._feed_records(
                        conn,
                        folder_sort=folder_sort,
                        folder_sort_reverse=folder_sort_reverse,
                        pane_sort=pane_sort,
                        pane_sort_reverse=pane_sort_reverse,
                    )
                after = self._index_stamp()
            except Exception as error:  # noqa: BLE001 — a syncFinished még frissíthet
                initial_feed_signals.ready.emit(
                    generation, None, f"{type(error).__name__}: {error}"
                )
                return
            initial_feed_signals.ready.emit(generation, (before, after, records), "")

        self._start_background(load_feed, name="picasapy-initial-library-feed")

    @Slot(int, object, str)
    def _on_initial_feed_ready(self, generation: int, stamp, error: str) -> None:
        """A kezdeti feed átvétele a felület szálán."""
        if generation != getattr(self, "_initial_feed_generation", 0):
            return
        if self._view_mode[0] != "folder":
            return
        if error:
            _log.warning("a kezdeti könyvtárfeed lekérdezése hibára futott: %s", error)
            records = ()
        else:
            before, after, records = stamp
            index_changed = before != after or after != self._index_stamp()
            if index_changed and not (
                getattr(self, "_sync_running", False)
                or getattr(self, "_dirty_running", False)
            ):
                return  # a syncFinished út tölti újra a megváltozott indexet
            # Aktív bejárás közben is mutassuk a SQLite-pillanatképet. A
            # párhuzamos olvasatlanjelölő-törlés például megváltoztathatja a
            # fájlpecsétet anélkül, hogy a fotólista elavult lenne; a bejárás
            # progressz- és záró jelzése úgyis behozza az új indexállapotot.

        self._show(records)
        folder = getattr(self, "_deferred_folder_activation", None)
        self._deferred_folder_activation = None
        if folder and folder == self._current_folder:
            self.folderActivated.emit(folder)

    def _feed_records(
        self,
        conn,
        *,
        folder_sort: str | None = None,
        folder_sort_reverse: bool | None = None,
        pane_sort: str | None = None,
        pane_sort_reverse: bool | None = None,
    ) -> tuple:
        """A rács mappablokkjai a bal hasáb rendezését követik (#7341).

        A `folderSort` csak a védett „Recent &changes” tétel aktív
        (`changed`) módját tartja meg; a korábban mentett többi érték helyett
        a `paneSort` rendezi a rács mappa-blokkjait is. Az induló háttérfeed
        minden beállítást a főszálon olvas ki, a többi hívás az aktuális
        értékeket használja.
        """
        if folder_sort is None:
            folder_sort = self.folderSort
        if folder_sort_reverse is None:
            folder_sort_reverse = self.folderSortReverse
        if pane_sort is None:
            pane_sort = self.paneSort
        if pane_sort_reverse is None:
            pane_sort_reverse = self.paneSortReverse
        sort_mode, reverse = (
            (folder_sort, folder_sort_reverse)
            if folder_sort == "changed"
            else (pane_sort, pane_sort_reverse)
        )
        sorted_folders = folder_order(conn, sort_mode, reverse)
        order = {path: i for i, path in enumerate(sorted_folders)}
        from . import controller as controller_module

        return tuple(
            sorted(
                controller_module.all_photos(conn),
                key=lambda r: (
                    order.get(r.folder_path, len(order)),
                    r.folder_path,
                    r.name,
                ),
            )
        )

    def _without_disabled_filetypes(self, records) -> tuple:
        """#7414: a kikapcsolt fájltípusok elemei nélküli lista.

        A kikapcsolt típus sorai az indexben megmaradnak, a felületről viszont
        azonnal el kell tűnniük (az eredeti `0x004fb9c0` a memóriabeli listából
        veszi ki őket). Minden nézet és minden darabszám ezen át szűr."""
        enabled_types = getattr(self, "_filetype_scan_snapshot", None)
        if enabled_types is None:
            return records
        return tuple(
            r
            for r in records
            if media_kind_if_enabled(r.name, enabled_types) is not None
        )

    def _refresh_after_filetype_change(self) -> None:
        """#7414: egy fájltípus ki- vagy bekapcsolása után a felület azonnal
        az új látható halmazt mutatja: rács, mappaszámláló, projektek,
        Other Stuff, album- és Recently Updated számláló. Az indexet nem írja
        és a lemezt nem olvassa."""
        self._refresh_view()
        with open_index(self._db_path) as conn:
            if not self._refresh_side_pane_filetype_counts(conn):
                self._reload_folders()
            self._load_albums(conn)
        if hasattr(self, "_refresh_auto_album_tokens"):
            self._refresh_auto_album_tokens()

    def _show(self, records) -> None:
        records = self._without_disabled_filetypes(records)
        # #4526: a kor-szűrő felirata és csúszkája csak a kor-nézethez
        # tartozik. Bármely más nézet betöltése törölje, így a szűrőgombok és
        # mappaváltások után sem maradhat régi kor-felirat. #7255: a keresés
        # a kor-csúszkával közös állapot, ott a csúszka marad.
        if (
            self._view_mode[0] not in AGE_KEEPING_MODES
            and self._age_filter_days is not None
        ):
            self._age_filter_days = None
        # #17: a rejtett képek alapból sehol nem látszanak (rács, keresés,
        # csillag-szűrő) — a Nézet → Rejtett képek kapcsolóval igen
        # #7194: a keresési nézetekben a szűrés már a hasáb, a darabszám és a
        # sáv előtt megtörtént (_filter_search_hidden), itt nem duplikáljuk.
        if not self.showHidden and self._view_mode[0] not in (
            "search",
            "search-folder",
        ):
            records = tuple(r for r in records if not r.hidden)
        # #461: a BEZÁRT gyűjtemények képei sehol nem látszanak — rácsban,
        # keresésben, csillag-szűrőben sem. Ez az EGY pont, ahol minden
        # nézetmód átmegy, ezért a szűrés itt van (a rejtett képek mintája).
        # A bezárás nem törlés: a mappák a gyűjteményben maradnak.
        closed_folders = self._closed_collection_folders()
        if closed_folders:
            records = tuple(
                r for r in records if r.folder_path not in closed_folders
            )
        # #3751: mentés-üzemmódban csak a még el nem mentett fájlok
        records = self._mentes_szurt(records)
        # #4346: az eredeti `Show only big images` preferenciája a
        # könyvtári képrács láthatóságát szűri. A videók és a méretadat
        # nélküli sorok megmaradnak; ez utóbbiaknál az eredeti is az
        # általános hozzáadási ágra jut.
        if self.showOnlyBigImages:
            records = tuple(
                record
                for record in records
                if record.kind not in ("photo", "image")
                or is_big_picture(record.width, record.height)
            )
        # #142: a mappaváltás-gyorsút pecsétje — csak a teljes feedet
        # mutató mappa-nézet érvényes hozzá (szűrt/keresett nézet nem)
        self._feed_stamp = (
            self._index_stamp()
            if self._view_mode[0] == "folder" and not self.backupFilterActive
            else None
        )
        # #644: itt látjuk először a friss ini-állapotot — ha egy külső
        # program (a párhuzamosan futó Picasa) letörölte a mi mentett
        # láncunkat, ez az a pont, ahol észrevehetjük. Képenként egyszer
        # jelzünk; a néma eltűnés a legrosszabb változat.
        self._check_external_overwrites(records)
        self._provider.register_photos(records)
        self._photos.set_photos(records)
        self._update_feed_groups(records)
        # #2304: a mappa-fejléc dátumsora — a `formatting.first_date_text`-tel
        # és az állapotsorral KÖZÖS `photo_dates`-en át, hogy EXIF nélküli
        # mappában is legyen dátum, és hogy a három felirat ne mondhasson
        # mást ugyanarról a mappáról. (Ez a property ma bekötetlen —
        # `scripts/kepesseg_or_baseline.txt` —, de bekötéskor a hiba
        # azonnal visszatérne.)
        dates = formatting.photo_dates(records)
        self._folder_date = (
            formatting.long_date(dates[0], QLocale()) if dates else ""
        )
        search_active = self._view_mode[0] in ("search", "search-folder")
        self._search_groups = group_by_folder(records) if search_active else ()
        self._update_status(records)
        # #30: a térkép-jelölők mindig a LÁTSZÓ képeket tükrözik
        self.geoChanged.emit()

    def _update_feed_groups(self, records) -> None:
        """Mappa-csoportok a rács-feedhez (#64). feedChanged CSAK valódi
        változásnál megy ki — különben minden háttér-frissítés nullázná a
        rács görgetését."""
        groups = formatting.build_feed_groups(records, QLocale())
        if groups != self._feed_groups:
            self._feed_groups = groups
            self.feedChanged.emit()

    def _load_albums(self, conn) -> None:
        """Az albumlista frissítése (#9) — ugyanott hívjuk, mint a
        mappalistát: a `_reload()`-ban, a háttér-szinkron után is friss
        marad. A névtelen albumnak is van megjelenítendő neve, hogy ne
        maradjon üres sor a hasábon."""
        # #7414: a kikapcsolt fájltípusok az indexben maradnak, a számlálókból
        # viszont kimaradnak, hogy a bal hasáb a rács halmazát mutassa.
        enabled_types = getattr(self, "_filetype_scan_snapshot", None)
        self._albums = [
            {
                "token": album.token,
                "name": album.name or self._album_placeholder_name(album.token),
                "count": album.photo_count,
            }
            for album in albums_in_index(conn, enabled_types)
        ]
        self._recently_updated_count = count_recently_updated_photos(
            conn, enabled_filetypes=enabled_types
        )
        self.albumsChanged.emit()

    def _album_placeholder_name(self, token: str) -> str:
        """Megjelenítendő név a névtelen albumnak: a token rövidített
        alakja — sose maradjon üres sor a hasábon."""
        return self.tr("Album %1").replace("%1", token[:8])

    def _update_status(self, records) -> None:
        self._status = formatting.status_text(
            records, QLocale(), formatting.fordit, self.tr
        )
        self.statusChanged.emit()
