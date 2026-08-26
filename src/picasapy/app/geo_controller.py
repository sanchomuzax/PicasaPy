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
