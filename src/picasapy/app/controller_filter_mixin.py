"""A csillag-, film-, kor-, arc- és album-szűrők."""

from __future__ import annotations

from datetime import datetime
import time
from PySide6.QtCore import Property, Slot
from picasapy.index import (
    album_photos, open_index, photos_up_to_age, photos_with_faces,
    starred_photos, video_photos,
)
from . import formatting, kor_szuro
from .controller_signals import AppControllerSignalsMixin as _Signals

class ViewFilterMixin:
    """A csillag-, film-, kor-, arc- és album-szűrők."""

    @Slot()
    def showStarred(self) -> None:
        """A ★ eszköztári szűrője — megőrzi a mappa-kontextust."""
        self._show_starred_photos("starred")

    @Slot()
    def showStarredAlbum(self) -> None:  # noqa: N802
        """A bal oldali Csillagozott különleges albumát nyitja meg (#4883).

        A tartalma ugyanazokból a csillagozott képekből áll, mint a ★ szűrőé,
        de a `]star` album-tokent is hordozza, így a törlés csak a csillagot
        veszi le. A két belépő nézete és törlési szemantikája külön marad.
        """
        self._show_starred_photos("starred_album")

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

        A csillag-szűrő mintáját követi: szűrt NÉZET, nem külön nézetmód,
        a mappa-kontextus megmarad a `clearFilter`-es visszaváltáshoz.
        A `kind` indexmezőre épül, tehát nem igényel újraindexelést."""
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
        if nap is None:
            self._age_filter_days = None
            self.clearFilter()
            return
        self._age_filter_days = nap
        self._view_mode = ("age", nap)
        self._show_age_filtered(nap)

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

    @Property(str, notify=_Signals.statusChanged)
    def ageFilterText(self) -> str:
        """A kor-szűrő felirata a találati sávra, vagy üres, ha nincs szűrés.

        A négy szövegforma és a csonkított mértékegység a `.tre`-ből és a
        binárisból mérve (`kor_szuro.felirat`)."""
        if self._age_filter_days is None:
            return ""
        return kor_szuro.felirat(self._age_filter_days, formatting.fordit)

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
        # #1830: a kor-felirat is tűnjön el — különben a sávon ottmaradna
        # egy „Legfeljebb N napos képek." mondat szűrés nélkül
        self._age_filter_days = None
        if self._current_folder:
            self.selectFolder(self._current_folder)
        else:
            self._view_mode = ("folder", "")
            self._show(())
