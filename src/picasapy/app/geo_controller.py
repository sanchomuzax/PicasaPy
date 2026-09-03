"""Geocímke: hely-szűrő, térkép-jelölők és címke-szerkesztés (#30).

Az AppController vezérlő-szelete (a `photo_ops_controller` írási mintáját
használja: `.picasa.ini` `geotag=` kulcs, atomikus, backupolt írás a
round-trip rétegen át — a párhuzamosan futó eredeti Picasa is látja).

Három felület:

- **`showGeotagged()`** — a hellyel rendelkező képek szűrője („Helyek"),
  a csillag-szűrő (`showStarred`) mintájára;
- **`geoMarkers`** — a jelenleg látszó képek térkép-jelölői (sor, név,
  koordináta) — a Helyek-panel térképe ehhez köti a jelölőit;
- **`setGeotagRows` / `clearGeotagRows`** — a kijelölés helyének
  beállítása/törlése (a térképen kattintva, vagy a kontextusmenüből).
"""

from __future__ import annotations

import time

from PySide6.QtCore import Property, QLocale, Signal, Slot

from picasapy.index import geotagged_photos, open_index
from picasapy.metadata.gps import GeoPoint, format_geotag

from . import formatting


#: #2013: a Helyek panel megerősítő küszöbei — MÉRT konstansok, nem a
#: mi döntésünk. A kettő SZÁNDÉKOSAN különbözik: a törlés
#: visszafordíthatatlanabb, ezért ott alacsonyabb a küszöb.
#:
#: * hely MEGVÁLTOZTATÁSA: `0x00652585` `cmp ebx, 0x14` — 20 fölött kérdez,
#:   és a szám a TELJES KIJELÖLÉS elemszáma;
#: * hely TÖRLÉSE: `0x006527ad` `cmp esi, 5` — 5 fölött kérdez, és a szám a
#:   ténylegesen GEOCÍMKÉZETT elemeké (`0x006524c0` predikátum-számláló),
#:   nem a kijelölésé.
HELY_MODOSITAS_KUSZOB = 20
HELY_TORLES_KUSZOB = 5


class GeoMixin:
    """Hely-szűrő, jelölő-lista és `geotag=` írás."""

    geoChanged = Signal()
    # a hely mentése nem sikerült (pl. tartós ini-ütközés) — emberi üzenet
    geoWriteFailed = Signal(str)

    @Property(list, notify=geoChanged)
    def geoMarkers(self):
        """A LÁTSZÓ képek térkép-jelölői — mindig a rács tartalmát tükrözi.

        Így a térkép és a rács sosem térhet el: mappa-nézetben a mappa
        geocímkézett képei, a Helyek-szűrőben az összes ilyen kép.
        Listát adunk (nem tuple-t): a QML-oldalon a tuple NEM tömb (#232)."""
        markers = []
        for row, photo in enumerate(self._photos.photos):
            point = photo.location
            if point is None:
                continue
            markers.append(
                {
                    "row": row,
                    "name": photo.name,
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                }
            )
        return markers

    @Property(int, notify=geoChanged)
    def geoMarkerCount(self):
        """Hány látszó képnek van helye — a szűrő-ikon állapotához."""
        return len(self.geoMarkers)

    @Slot()
    def showGeotagged(self) -> None:
        """Hely-szűrő be (szűrősor geo-ikonja): minden geocímkézett kép."""
        self._view_mode = ("geo", "")
        started = time.perf_counter()
        with open_index(self._db_path) as conn:
            records = geotagged_photos(conn)
        elapsed = time.perf_counter() - started
        self._filter_active = True
        self._filter_status = formatting.filter_status_text(
            records, elapsed, QLocale(), self.tr
        )
        self._show(records)
        self.geoChanged.emit()

    @Slot(list, float, float)
    def setGeotagRows(self, rows, latitude: float, longitude: float) -> None:
        """A kijelölt képek helyének beállítása (`geotag=` az ini-be).

        Érvénytelen koordinátánál nem ír semmit, hanem emberi üzenetet
        jelez — a felület sosem tud néma, hibás állapotot előállítani."""
        try:
            value = format_geotag(latitude, longitude)
        except (ValueError, TypeError) as error:
            self.geoWriteFailed.emit(str(error))
            return
        photos = self._selected_photos(rows)
        if not photos:
            return

        def mutate(document, photo):
            return document.with_value(photo.name, "geotag", value)

        self._write_geotag(photos, mutate)

    @Property(int, constant=True)
    def geoChangeConfirmThreshold(self) -> int:
        """A hely MEGVÁLTOZTATÁSÁNAK megerősítő küszöbe (#2013).

        A felület ezt olvassa — beégetett `20` a hívás helyén nem
        maradhat, mert a szám MÉRT konstans (`0x00652585`), nem a mi
        döntésünk."""
        return HELY_MODOSITAS_KUSZOB

    @Property(int, constant=True)
    def geoClearConfirmThreshold(self) -> int:
        """A hely TÖRLÉSÉNEK megerősítő küszöbe (#2013), `0x006527ad`."""
        return HELY_TORLES_KUSZOB

    @Slot(list, result=int)
    def geotaggedCount(self, rows) -> int:
        """Hány kijelölt képnek van TÉNYLEGESEN geocímkéje (#2013).

        A törlés megerősítő küszöbe ezt a számot nézi, nem a kijelölését:
        ha 100 kép van kijelölve és ebből 3 geocímkézett, az eredeti NEM
        kérdez (3 ≤ 5), és a kérdésben is a 3 szerepelne, nem a 100.
        """
        return sum(1 for foto in self._selected_photos(rows) if self._van_geo(foto))

    def _van_geo(self, foto) -> bool:
        """Van-e `geotag=` az ini-ben ehhez a képhez."""
        return bool(getattr(foto, "geotag", None))

    @Slot(list)
    def clearGeotagRows(self, rows) -> None:
        """A kijelölt képek helyének törlése (a kulcs kikerül az ini-ből).

        Az EXIF-ben rögzített (gépi) hely megmarad — a Picasa is csak a
        saját címkéjét törli, a fájlt nem írja át."""
        photos = self._selected_photos(rows)
        if not photos:
            return

        def mutate(document, photo):
            return document.with_removed(photo.name, "geotag")

        self._write_geotag(photos, mutate)

    def _selected_photos(self, rows) -> tuple:
        photos = self._photos.photos
        return tuple(
            photos[int(r)] for r in rows if 0 <= int(r) < len(photos)
        )

    def _write_geotag(self, photos, mutate) -> None:
        """Kötegelt ini-írás + nézet-frissítés, hangos hibajelzéssel."""
        try:
            self._apply_batch(photos, mutate)
        except (OSError, ValueError) as error:
            self.geoWriteFailed.emit(str(error))
            return
        self.geoChanged.emit()

    # SZÁNDÉKOSAN nincs QML-hivatkozása (#1052): a felület ugyanezt az adatot
    # a `geoMarkers` listából kapja meg, egyben az egész rácsra.
    @Slot(int, result="QVariant")
    def locationOfRow(self, row: int):
        """Egy sor helye a QML-nek: `{latitude, longitude}` vagy `null`."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return None
        point = photos[row].location
        if point is None:
            return None
        return {"latitude": point.latitude, "longitude": point.longitude}

    @staticmethod
    def geo_point(latitude: float, longitude: float) -> GeoPoint:
        """Validáló segéd a teszteknek/hívóknak (ValueError hibás értéknél)."""
        return GeoPoint(latitude, longitude)
