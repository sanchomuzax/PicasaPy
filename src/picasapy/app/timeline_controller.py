"""A teljes képernyős Időrend kártya- és diavetítés-adatai (#5377)."""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from PySide6.QtCore import Property, QDate, QLocale, QObject, Signal, Slot

from picasapy.index import (
    PhotoRecord,
    album_photos,
    albums_in_index,
    all_photos,
    open_index,
)
from picasapy.timeline import record_date

from .models import PhotoGridModel, _has_edits, _thumb_url

_PATH_PARTS = re.compile(r"[/\\]+")


class TimelineController(QObject):
    """Az index mappáiból és albumjaiból épít időrendben rendezett kártyákat."""

    collectionsChanged = Signal()

    def __init__(self, db_path: Path, provider, parent: QObject | None = None):
        super().__init__(parent)
        self._db_path = db_path
        self._provider = provider
        self._collections: list[dict] = []
        self._collection_records: list[tuple[PhotoRecord, ...]] = []
        self._slideshow_photos = PhotoGridModel(self)
        self._date_range_start_label = ""
        self._date_range_end_label = ""

    @Property("QVariantList", notify=collectionsChanged)
    def collections(self) -> list:
        """QML-nek átadható kártyaadatok, legrégebbitől a legújabbig."""
        return self._collections

    @Property(str, notify=collectionsChanged)
    def dateRangeStartLabel(self) -> str:  # noqa: N802
        return self._date_range_start_label

    @Property(str, notify=collectionsChanged)
    def dateRangeEndLabel(self) -> str:  # noqa: N802
        return self._date_range_end_label

    @Property(QObject, notify=collectionsChanged)
    def slideshowPhotos(self) -> QObject:  # noqa: N802
        """A jelenlegi kártya képei a meglévő vetítőmodell számára."""
        return self._slideshow_photos

    @Slot()
    def reload(self) -> None:
        """Újraolvassa a látható mappákat és albumokat az SQLite indexből."""
        with open_index(self._db_path) as conn:
            records = tuple(record for record in all_photos(conn) if not record.hidden)
            folder_dates = {
                row["path"]: row["date"]
                for row in conn.execute("SELECT path, date FROM folders")
            }
            albums = albums_in_index(conn)
            album_records = {
                album.token: tuple(
                    record
                    for record in album_photos(conn, album.token)
                    if not record.hidden
                )
                for album in albums
            }

        self._provider.register_photos(records)
        by_folder: dict[str, list[PhotoRecord]] = {}
        for record in records:
            by_folder.setdefault(record.folder_path, []).append(record)

        raw_collections: list[tuple[str, str, str, str, tuple[PhotoRecord, ...]]] = []
        for folder_path, folder_records in by_folder.items():
            folder_name = _PATH_PARTS.split(folder_path.rstrip("/\\"))[-1]
            folder_date = folder_dates.get(folder_path)
            raw_collections.append((
                folder_name,
                "folder",
                folder_path,
                folder_date or self._fallback_date(folder_records),
                tuple(folder_records),
            ))

        for album in albums:
            photos = album_records[album.token]
            if not photos:
                continue
            album_name = (album.name or "").strip()
            if not album_name:
                continue
            raw_collections.append((
                album_name,
                "album",
                album.token,
                album.date or self._fallback_date(photos),
                photos,
            ))

        prepared = []
        for name, kind, key, raw_date, photos in raw_collections:
            date_key, date_label = self._format_date(raw_date)
            prepared.append((
                date_key,
                name.casefold(),
                kind,
                key,
                {
                    "name": name,
                    "date": date_label,
                    "dateKey": date_key,
                    "kind": kind,
                    "key": key,
                    "count": len(photos),
                    "photos": [self._photo_to_qml(photo) for photo in photos],
                },
                photos,
            ))

        prepared.sort(key=lambda row: (not row[0], row[0] or "9999", row[1], row[2], row[3]))
        self._collections = [row[4] for row in prepared]
        self._collection_records = [row[5] for row in prepared]
        dated = [row[0] for row in prepared if row[0]]
        if dated:
            _, self._date_range_start_label = self._format_date(dated[0])
            _, self._date_range_end_label = self._format_date(dated[-1])
        else:
            self._date_range_start_label = ""
            self._date_range_end_label = ""
        self._slideshow_photos.set_photos(())
        self.collectionsChanged.emit()

    @Slot(int)
    def setCurrentCollection(self, index: int) -> None:  # noqa: N802
        """A kártya saját képeit teszi elérhetővé a diavetítésnek."""
        if index < 0 or index >= len(self._collection_records):
            self._slideshow_photos.set_photos(())
            return
        self._slideshow_photos.set_photos(self._collection_records[index])

    @staticmethod
    def _fallback_date(records: tuple[PhotoRecord, ...] | list[PhotoRecord]) -> str:
        dates = [record_date(record) for record in records]
        valid = [value.isoformat() for value in dates if value is not None]
        return min(valid) if valid else ""

    def _format_date(self, raw_date: str | None) -> tuple[str, str]:
        if raw_date:
            qdate = QDate.fromString(raw_date[:10], "yyyy-MM-dd")
            if qdate.isValid():
                return qdate.toString("yyyy-MM-dd"), QLocale().toString(qdate, "MMMM yyyy")
            try:
                parsed = date.fromisoformat(raw_date[:10])
            except ValueError:
                parsed = None
            if parsed is not None:
                qdate = QDate(parsed.year, parsed.month, parsed.day)
                return qdate.toString("yyyy-MM-dd"), QLocale().toString(qdate, "MMMM yyyy")
        return "", self.tr("Unknown date")

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
            "hasGeo": photo.location is not None,
        }
