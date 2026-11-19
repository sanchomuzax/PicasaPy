"""A csillag-, film-, kor-, arc- és album-szűrők."""

from __future__ import annotations

from datetime import datetime
import time
from PySide6.QtCore import Property, Slot
from picasapy.index import (
    album_photos, open_index, photos_up_to_age, photos_with_faces,
    recently_updated_photos, starred_photos, video_photos,
)
from picasapy.ini import RECENT_ALBUM_TOKEN
from . import formatting, kor_szuro
from .search_button_filter import FACES, GEO, SEARCH_MODES, STAR, VIDEOS
from .controller_signals import AppControllerSignalsMixin as _Signals

class ViewFilterMixin:
    """A csillag-, film-, kor-, arc- és album-szűrők."""

    # -- szöveggel közös gombok: csillag, arc, geocímke (#7191) ---------------

    def _attach_button_to_search(self, button: str) -> bool:
        """Aktív keresés közben a gombot a keresés mellé köti (#7191).

        Az eredetiben a keresőszöveg és a gomb szava egy listában van, a
        találat a metszetük: a gomb bekapcsolása nem dobja el a szöveget,
        hanem szűkíti a találatot. Igaz, ha a gomb a keresés mellé került
        (a nézet már frissült); hamis, ha nincs aktív keresés."""
        if self._view_mode[0] not in SEARCH_MODES:
            return False
        self._search_button = button
        self._refresh_view()
        return True

    def _show_button_view(self, button: str) -> None:
        """A gomb önálló (szöveg nélküli) nézete, a gomb saját útján."""
        if button == STAR:
            self._show_starred_photos("starred")
        elif button == FACES:
            self._show_faces_photos()
        elif button == GEO:
            self._show_geotagged_photos()
        elif button == VIDEOS:
            self._show_video_photos()

    @Slot()
    def clearButtonFilter(self) -> None:  # noqa: N802
        """A csillag-, arc-, geocímke- vagy filmgomb kikapcsolása.

        Aktív keresésnél a keresőszöveg MEGMARAD: a találat a gomb nélküli
        szöveges keresésre bővül. Keresés nélkül a szűrő kikapcsol, mint a
        `clearFilter`. Az „Az összes megtekintése" és a keresőmező ✕ gombja
        továbbra is a `clearFilter` (az eredeti `searchclr` a gombokat is
        törli)."""
        if self._view_mode[0] in SEARCH_MODES:
            self._search_button = ""
            self._refresh_view()
            return
        self.clearFilter()

    @Slot()
    def showStarred(self) -> None:
        """A ★ eszköztári szűrője — megőrzi a mappa-kontextust."""
        if self._attach_button_to_search(STAR):
            return
        self._show_starred_photos("starred")

    @Slot()
    def showStarredAlbum(self) -> None:  # noqa: N802
        """A bal oldali Csillagozott különleges albumát nyitja meg (#4883).

        A tartalma ugyanazokból a csillagozott képekből áll, mint a ★ szűrőé,
        de a `]star` album-tokent is hordozza, így a törlés csak a csillagot
        veszi le. A két belépő nézete és törlési szemantikája külön marad.
        """
        self._show_starred_photos("starred_album")

    @Slot()
    def showRecentlyUpdatedAlbum(self) -> None:  # noqa: N802
        """A bal oldali Legutóbb frissítve (Recently Updated) különleges albumát nyitja meg (#6851)."""
        self._view_mode = ("recent_album", RECENT_ALBUM_TOKEN)
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = recently_updated_photos(conn)
            self._recently_updated_count = len(records)
        self._show_filtered(records, time.perf_counter() - started)

    def _show_starred_photos(self, mode: str) -> None:
        self._view_mode = (mode, "")
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = starred_photos(conn)
        self._show_filtered(records, time.perf_counter() - started)

    # -- film-szűrő (#1830) --------------------------------------------------

    @Slot()
    def showVideosOnly(self) -> None:
        """„Csak filmek" — az eredeti `moviesearch` szűrője.

        #7264: aktív kereséskor a szöveggel metsz, a szöveg törlése pedig a
        filmnézetet állítja vissza. A `kind` indexmezőre épül, tehát nem
        igényel újraindexelést."""
        if self._attach_button_to_search(VIDEOS):
            return
        self._show_video_photos()

    def _show_video_photos(self) -> None:
        self._view_mode = ("videos", "")
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = video_photos(conn)
        self._show_filtered(records, time.perf_counter() - started)

    # -- kor-szűrő: az idő-csúszka (#1830) ------------------------------------

    @Slot(float)
    def setAgeFilter(self, ertek: float) -> None:
        """Az idő-csúszka: „legfeljebb ennyi napos képek" (`timeslider`).

        ⚠️ A csúszka NEM tartományt választ, hiába ezt sejti a felirata
        („Filter by date range") — az eredetiben is egyetlen érték adja meg
        a MAXIMÁLIS KORT. A képlet és a mérés az `app/kor_szuro.py`-ban áll.

        Nulla értéknél a szűrő KIKAPCSOL (ez az eredeti nulla-ága), tehát a
        csúszka bal széle nem „nagyon régi", hanem „nincs szűrés".
        """
        nap = kor_szuro.napok(max(0.0, min(1.0, float(ertek))))
        if self._view_mode[0] in SEARCH_MODES:
            # #7255: aktív keresésnél a csúszka a szöveggel KÖZÖS állapot: a
            # keresés megmarad, a találat a szöveg és a kor metszete. A 0 állás
            # csak a kor-szűrést kapcsolja ki, a szöveget nem.
            self._age_filter_days = nap
            self._refresh_view()
            return
        if nap is None:
            self._age_filter_days = None
            self.clearFilter()
            return
        self._age_filter_days = nap
        self._view_mode = ("age", nap)
        self._show_age_filtered(nap)

    def _age_cutoff(self) -> str | None:
        """A kor-szűrő vágópontja ISO-szövegként, vagy `None`, ha nincs szűrés.

        A vágópont MINDIG a hívás pillanatához mérve számolódik (ugyanaz az
        indoklás, mint a `_show_age_filtered`-nél): a napokat tároljuk, nem a
        vágópontot."""
        if self._age_filter_days is None:
            return None
        vagas = kor_szuro.vagopont(self._age_filter_days, datetime.now())
        return vagas.isoformat(timespec="seconds")

    def _show_age_filtered(self, nap: float) -> None:
        """A kor-szűrt nézet — a vágópont MINDIG a hívás pillanatához mérve.

        Ezért nem a vágópontot tároljuk, hanem a napokat: egy órákkal
        későbbi frissítésnek a MOSTANI „most"-hoz kell mérnie, különben a
        nézet észrevétlenül elavul."""
        started = time.perf_counter()
        vagas = kor_szuro.vagopont(nap, datetime.now())
        with open_index(self._db_path) as conn:
            records = photos_up_to_age(conn, vagas.isoformat(timespec="seconds"))
        self._show_filtered(records, time.perf_counter() - started)

    def _show_age_view(self) -> None:
        """A szöveg nélküli kor-nézet: a csúszka önmagában dátumszűrő (#7255).

        A keresőszöveg törlése után hívjuk: a csúszka állása marad, és a
        találat a teljes könyvtár kor szerinti szűkítése."""
        nap = self._age_filter_days
        self._view_mode = ("age", nap)
        self._show_age_filtered(nap)

    @Property(str, notify=_Signals.statusChanged)
    def ageFilterText(self) -> str:
        """A kor-szűrő felirata a találati sávra, vagy üres, ha nincs szűrés.

        A négy szövegforma és a csonkított mértékegység a `.tre`-ből és a
        binárisból mérve (`kor_szuro.felirat`)."""
        if self._age_filter_days is None:
            return ""
        return kor_szuro.felirat(self._age_filter_days, formatting.fordit)

    @Property(str, notify=_Signals.statusChanged)
    def ageFilterBarText(self) -> str:
        """A zöld sáv jobb szélén álló felirat, vagy üres, ha nincs szűrés (#7255).

        Alakja `Date Range:  Pictures up to N <egység> old.`. Az eredetiben a
        `Date Range: ` előtag az `il_SetSearchStatus::1` erőforrás, utána két
        szóközzel áll a mondat (`kor_szuro.sav_felirat`)."""
        if self._age_filter_days is None:
            return ""
        return kor_szuro.sav_felirat(self._age_filter_days, formatting.fordit)

    # -- arc-szűrő (#1830) ---------------------------------------------------

    @Slot()
    def showFacesOnly(self) -> None:
        """„Arcos képek" — az eredeti `facesearch` szűrője.

        A film- és a csillag-szűrő mintáját követi: szűrt NÉZET, nem külön
        nézetmód, a mappa-kontextus megmarad a `clearFilter`-es
        visszaváltáshoz.

        A MEGLÉVŐ `.picasa.ini` `faces=` adatára épül (`photos_with_faces`),
        tehát nem igényel arcfelismerést — a megnevezetlen arc is arc.

        ⚠️ A geo-szűrővel ellentétben ez NEM kap engedélyezési kaput. A geo
        azért kaphat, mert az adata az indexben van, tehát a darabszám
        olcsó; az arc-adat ini-söprést igényel, amit nem futtathatunk
        minden kötés-kiértékelésnél. Ha nincs arcos kép, a szűrő üres
        rácsot ad — az pedig a #1945 óta kimondja magáról, hogy üres."""
        if self._attach_button_to_search(FACES):
            return
        self._show_faces_photos()

    def _show_faces_photos(self) -> None:
        self._view_mode = ("faces", "")
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = photos_with_faces(conn)
        self._show_filtered(records, time.perf_counter() - started)

    # -- virtuális albumok (#9) -----------------------------------------------

    @Slot(str)
    def showAlbum(self, token: str) -> None:
        """Album-szűrő be — a showStarred mintáját követi: az album is
        egy szűrt nézet (nem új nézetmód), a mappa-kontextus megmarad a
        clearFilter-es visszaváltáshoz."""
        if not token:
            return
        if token == RECENT_ALBUM_TOKEN or token == "]updated":
            self.showRecentlyUpdatedAlbum()
            return
        self._view_mode = ("album", token)
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = album_photos(conn, token)
        self._show_filtered(records, time.perf_counter() - started)

    @Slot()
    def clearFilter(self) -> None:
        """Szűrő ki („Az összes megtekintése") — vissza a mappa-nézethez."""
        self._filter_active = False
        self._filter_status = ""
        self._search_button = ""
        # #1830: a kor-felirat is tűnjön el — különben a sávon ottmaradna
        # egy „Legfeljebb N napos képek." mondat szűrés nélkül
        self._age_filter_days = None
        if self._current_folder:
            self.selectFolder(self._current_folder)
        else:
            self._view_mode = ("folder", "")
            self._show(())
