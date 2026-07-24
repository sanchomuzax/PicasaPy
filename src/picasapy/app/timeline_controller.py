"""Időrend nézet (#24, Ctrl+5): a `picasapy.timeline` csoportosítás
Qt/QML-hídja — a teljes könyvtár fotóit év/hónap szerinti korszakokra
bontva adja a `TimelineView.qml`-nek.

Dátum-forrás (rögzített döntés, #24): elsődlegesen az EXIF `taken_at`
(a sync már kiolvasta, ld. `picasapy.index.sync`), ennek hiányában
(RAW/videó, vagy olvashatatlan EXIF) a fájl `mtime_ns`-e — ld.
`picasapy.timeline.resolve_date`. Ez a bevett fallback-elv, nem
projekt-specifikus kompromisszum: a séma `mtime_ns`-e mindig kitöltött.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QLocale, QObject, Signal, Slot

from picasapy.index import PhotoRecord, all_photos, open_index
from picasapy.timeline import TimelinePeriod, TimelinePhoto, build_periods, resolve_date

from .models import _has_edits, _thumb_url


class TimelineController(QObject):
    """Csak-olvasó vezérlő: a `reload()` az indexből építi a korszak-
    listát; a QML (`TimelineView.qml`) ebből rajzol korszak-fejléceket
    + bélyegkép-rácsot. A fotó-kattintás (mappaváltás + néző-megnyitás)
    a Main.qml dolga — ez a controller csak adatot ad."""

    periodsChanged = Signal()

    def __init__(self, db_path: Path, provider, parent: QObject | None = None):
        """`provider`: a MEGLÉVŐ (az AppControllerrel közös) ThumbnailProvider
        — a bélyegkép-URL-ek (`image://thumbs/<id>`) csak akkor oldódnak fel,
        ha a fotó nála regisztrálva van (`register_photos`)."""
        super().__init__(parent)
        self._db_path = db_path
        self._provider = provider
        self._periods: list[dict] = []

    @Property("QVariantList", notify=periodsChanged)
    def periods(self) -> list:
        """A korszakok QML-nek: {year, month, label, count, photos}
        dict-ek listája — SOHA ne Python tuple, a QML csak listát fogad
        el kötésként (ld. MEMORY-tanulság)."""
        return self._periods

    @Slot()
    def reload(self) -> None:
        """A teljes könyvtár friss lekérdezése és újracsoportosítása.

        A rejtett képek kimaradnak (a fő rács alapértelmezésével
        összhangban, #17) — józan alapértelmezés, hogy a böngészhető
        áttekintésben ne látsszanak rejtett fotók; a Timeline egyelőre
        nem ismeri a Nézet → Rejtett képek kapcsolót.
        """
        with open_index(self._db_path) as conn:
            records = tuple(r for r in all_photos(conn) if not r.hidden)
        # a bélyegkép-provider regisztere a TELJES könyvtárral bővül —
        # ez szuperhalmaza bármely szűkebb (mappa/keresés) nézetnek, tehát
        # a főrács regisztrációját sosem szűkíti (nem veszít kulcsot)
        self._provider.register_photos(records)
        by_id = {record.id: record for record in records}
        timeline_photos = tuple(
            TimelinePhoto(
                photo_id=record.id,
                date=resolve_date(record.taken_at, record.mtime_ns),
            )
            for record in records
        )
        locale = QLocale()
        self._periods = [
            self._period_to_qml(period, by_id, locale)
            for period in build_periods(timeline_photos)
        ]
        self.periodsChanged.emit()

    def _period_to_qml(
        self, period: TimelinePeriod, by_id: dict[int, PhotoRecord], locale: QLocale
    ) -> dict:
        photos = [
            self._photo_to_qml(by_id[photo.photo_id])
            for photo in period.photos
            if photo.photo_id in by_id
        ]
        return {
            "year": period.year,
            "month": period.month,
            "label": self._period_label(period, locale),
            "count": len(photos),
            "photos": photos,
        }

    def _period_label(self, period: TimelinePeriod, locale: QLocale) -> str:
        if period.year == 0 and period.month == 0:
            return self.tr("Unknown date")
        month_name = locale.standaloneMonthName(
            period.month, QLocale.FormatType.LongFormat
        )
        return f"{period.year}. {month_name}"

    @staticmethod
    def _photo_to_qml(photo: PhotoRecord) -> dict:
        return {
            "id": photo.id,
            "name": photo.name,
            "thumbUrl": _thumb_url(photo),
            "star": photo.star,
            "isVideo": photo.kind == "video",
            "folderPath": photo.folder_path,
            "hasEdits": _has_edits(photo),
        }
