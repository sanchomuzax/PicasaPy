"""#26: az „Emberek" gyűjtemény — controller-szelet (a `custom_collections_
controller`/`showAlbum` mintáját követő mixin, #150).

Mixin-osztály: a végleges `AppController` örökli majd (a bekötés — az
öröklés-lista bővítése és az `_reload()`/`_refresh_view()`-beli "people"
nézetmód-ág felvétele a `controller.py`-ban — FORRÓ fájl, az integrátor
dolga, ld. jelentés). A személy-választás a `showAlbum` mintáját követi:
szűrt nézet, a mappa-kontextus megmarad a `clearFilter`-es visszaváltáshoz.

Írás (arc-régió hozzárendelése/törlése egy névhez) ebben a körben NINCS —
ld. `docs/specs` és az issue-jelentés: a #26 1. köre csak a meglévő
`faces=`/`[Contacts2]` adatok OLVASÁSÁRA épül."""

from __future__ import annotations

import time

from PySide6.QtCore import Property, QLocale, Signal, Slot

from picasapy.index import open_index
from picasapy.index.people import people_in_index, person_photos

from . import formatting


class PeopleMixin:
    """A bal hasáb Emberek gyűjteménye: a könyvtárban névvel taggelt
    személyek listája, és egy névre kattintva a rá kitaggelt fotók."""

    peopleChanged = Signal()

    @Property("QVariant", notify=peopleChanged)
    def people(self):
        """A bal hasábnak: `[{name, count}, ...]` — LISTA, nem tuple (#232,
        a QML-ben a tuple nem tömb), a `albums` property mintájára."""
        return [
            {"name": person.name, "count": person.photo_count}
            for person in self._people
        ]

    @Property(str, notify=peopleChanged)
    def currentPersonName(self):
        """Az aktív személy neve (a bal hasáb kijelöléséhez) — a
        `currentAlbumToken` mintájára."""
        mode, param = self._view_mode
        return param if mode == "person" else ""

    def _init_people(self) -> None:
        """A konstruktorból hívandó kezdeti állapot (a `people` mezőé)."""
        self._people: tuple = ()

    def _load_people(self, conn) -> None:
        """Az Emberek-lista frissítése — a `_load_albums` mintájára, ugyanott
        (a háttér-szinkron utáni `_reload()`-ban) hívandó."""
        self._people = people_in_index(conn)
        self.peopleChanged.emit()

    @Slot(str)
    def showPerson(self, name: str) -> None:
        """Személy-szűrő be — a `showAlbum` mintáját követi: szűrt nézet, a
        mappa-kontextus megmarad a `clearFilter`-es visszaváltáshoz."""
        if not name:
            return
        self._view_mode = ("person", name)
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = person_photos(conn, name)
        elapsed = time.perf_counter() - started
        self._filter_active = True
        self._filter_status = formatting.filter_status_text(
            records, elapsed, QLocale(), self.tr
        )
        self._show(records)

    def _refresh_people_view(self, mode: str, param: str) -> bool:
        """A `_refresh_view()` "person" ágának kiszervezett teste — igazat ad
        vissza, ha kezelte a módot (a hívó `elif`-lánca ez alapján dönt)."""
        if mode != "person":
            return False
        with open_index(self._db_path) as conn:
            self._show(person_photos(conn, param))
        return True
