"""Az AppController mappa- és fotólistáinak összeállítása és megjelenítése."""

from __future__ import annotations

from PySide6.QtCore import QLocale
from picasapy.index import albums_in_index
from . import formatting
from .models import folder_order
from .small_picture_filter import is_big_picture
from .search_results import group_by_folder


class AppControllerPhotoListMixin:
    def _feed_records(self, conn) -> tuple:
        """A teljes könyvtár a Mappa ▸ Rendezés szerint (#64, #321).

        A sorrendet KÜLÖN kérdezzük le, nem a bal hasáb modelljéből vesszük:
        a fa a saját rögzített sorrendjében áll, a rács a beállítást követi.
        """
        order = {
            path: i
            for i, path in enumerate(
                folder_order(conn, self.folderSort, self.folderSortReverse)
            )
        }
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

    def _show(self, records) -> None:
        # #4526: a kor-szűrő felirata és csúszkája csak a kor-nézethez
        # tartozik. Bármely más nézet betöltése törölje, így a szűrőgombok,
        # keresések és mappaváltások után sem maradhat régi kor-felirat.
        if self._view_mode[0] != "age" and self._age_filter_days is not None:
            self._age_filter_days = None
        # #17: a rejtett képek alapból sehol nem látszanak (rács, keresés,
        # csillag-szűrő) — a Nézet → Rejtett képek kapcsolóval igen
        if not self.showHidden:
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
        self._albums = [
            {
                "token": album.token,
                "name": album.name or self._album_placeholder_name(album.token),
                "count": album.photo_count,
            }
            for album in albums_in_index(conn)
        ]
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
