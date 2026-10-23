"""Teljes képernyős Időrend bemutató (#5377), Qt/QML-híd.

Az eredeti képlánc és az `A` tömb dátumjelentése még nyitott (#5401). A
felvétel szerint látható mappakártyákat ezért a helyi index mappánkénti
csoportosításából építi. A kártya dátuma a mappa legrégebbi ismert képdátuma;
a csúszka a képek tényleges dátumtartományát mutatja. A képek mappán belüli
sorrendje az index stabil névsorrendje.

#2486: a fájlidő itt is a BEFAGYASZTOTT, első látáskori érték
(`PhotoRecord.sort_mtime_ns`), nem az élő `mtime`. Enélkül ugyanaz az
EXIF nélküli kép MÁS korszakba került volna az Időrendben, mint amilyen
dátummal a rácsban és a mappa fejlécében szerepel - a két nézet
ugyanarról a képről mondott volna mást. A döntés lapja:
`docs/decisions/befagyasztott-fajlido.md`.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import Property, QLocale, QObject, Signal, Slot

from picasapy.index import PhotoRecord, all_photos, open_index
from picasapy.timeline import record_date

from .models import PhotoGridModel, _has_edits, _thumb_url
from ..timeline_motion import (
    DEFAULT_BEZIER_POINTS,
    frame_transforms,
    random_slide_offsets,
    rational_cubic_bezier,
    slider_index,
    slider_thumb_x,
    slideshow_easing,
    timeline_dot_positions,
)


class TimelineController(QObject):
    """A teljes könyvtár mappakártyáit és mozgásképleteit szolgáltatja a QML-nek.

    """

    collectionsChanged = Signal()

    def __init__(self, db_path: Path, provider, parent: QObject | None = None):
        """`provider`: a MEGLÉVŐ (az AppControllerrel közös) ThumbnailProvider
        - a bélyegkép-URL-ek (`image://thumbs/<id>`) csak akkor oldódnak fel,
        ha a fotó nála regisztrálva van (`register_photos`)."""
        super().__init__(parent)
        self._db_path = db_path
        self._provider = provider
        self._collections: list[dict] = []
        self._collection_records_by_folder: dict[str, tuple[PhotoRecord, ...]] = {}
        self._collection_slideshow_model: PhotoGridModel | None = None

    @Property("QVariantList", notify=collectionsChanged)
    def collections(self) -> list:
        """A teljes könyvtár mappakártyái, legrégebbi képdátum szerint."""
        return self._collections

    @Slot(float, result="QVariantMap")
    def bezierAt(self, t: float) -> dict:
        """A runtime/bezier.txt négy pontjából számolt görbehely (38.2.61)."""
        x, y, z = rational_cubic_bezier(t, DEFAULT_BEZIER_POINTS)
        return {"x": x, "y": y, "z": z}

    @Slot(float, result=float)
    def easingAt(self, progress: float) -> float:
        return slideshow_easing(progress)

    @Slot(float, float, float, float, float, bool, result="QVariantMap")
    def frameAt(
        self,
        progress: float,
        current_x: float,
        current_y: float,
        previous_x: float,
        previous_y: float,
        previous_present: bool,
    ) -> dict:
        return frame_transforms(
            progress,
            current_offset=(current_x, current_y),
            previous_offset=(previous_x, previous_y),
            previous_present=previous_present,
        )

    @Slot(float, float, int, int, int, int, result="QVariantMap")
    def randomOffsets(
        self,
        previous_x: float,
        previous_y: float,
        rand_y: int,
        rand_x: int,
        width: int,
        height: int,
    ) -> dict:
        current, previous = random_slide_offsets(
            (previous_x, previous_y),
            rand_y=rand_y,
            rand_x=rand_x,
            width=width,
            height=height,
        )
        return {"current": list(current), "previous": list(previous)}

    @Slot("QVariantList", float, result=int)
    def sliderIndex(self, values: list, ratio: float) -> int:
        return slider_index(values, ratio)

    @Slot(float, int, int, int, result=int)
    def sliderThumbX(self, x: float, left: int, width: int, thumb_width: int) -> int:
        return slider_thumb_x(
            x, left=left, width=width, thumb_width=thumb_width
        )

    @Slot("QVariantList", int, int, int, int, int, int, result="QVariantList")
    def dotPositions(
        self,
        values: list,
        x_start: int,
        track_span_minus_four: int,
        dot_width: int,
        y_top: int,
        track_spacing: int,
        dot_height: int,
    ) -> list:
        return timeline_dot_positions(
            values,
            x_start=x_start,
            track_span_minus_four=track_span_minus_four,
            dot_width=dot_width,
            y_top=y_top,
            track_spacing=track_spacing,
            dot_height=dot_height,
        )

    @Slot(str, result=QObject)
    def slideshowModel(self, folder_path: str) -> QObject:
        """Az Időrend-kártya saját mappájára szűrt diavetítésmodellt adja."""
        if self._collection_slideshow_model is None:
            self._collection_slideshow_model = PhotoGridModel(self)
        records = self._collection_records_by_folder.get(folder_path, ())
        self._collection_slideshow_model.set_photos(records)
        return self._collection_slideshow_model

    @Slot()
    def reload(self) -> None:
        """A teljes könyvtár friss lekérdezése és újracsoportosítása.

        A rejtett képek kimaradnak (a fő rács alapértelmezésével
        összhangban, #17) - józan alapértelmezés, hogy a böngészhető
        áttekintésben ne látsszanak rejtett fotók; a Timeline egyelőre
        nem ismeri a Nézet → Rejtett képek kapcsolót.

        #4887: a rejtett MAPPÁK képeit már maga a lekérdezés kihagyja (a
        közös kapu, `index/hidden_scope.py`), a kapcsoló tényleges értéke
        szerint.
        """
        with open_index(self._db_path) as conn:
            records = tuple(r for r in all_photos(conn) if not r.hidden)
        # a bélyegkép-provider regisztere a TELJES könyvtárral bővül -
        # ez szuperhalmaza bármely szűkebb (mappa/keresés) nézetnek, tehát
        # a főrács regisztrációját sosem szűkíti (nem veszít kulcsot)
        self._provider.register_photos(records)
        locale = QLocale()
        self._collections = self._collections_to_qml(records, locale)
        self.collectionsChanged.emit()

    def _collections_to_qml(self, records: tuple, locale: QLocale) -> list[dict]:
        grouped: dict[str, list[PhotoRecord]] = {}
        for record in records:
            grouped.setdefault(record.folder_path, []).append(record)
        self._collection_records_by_folder = {
            folder_path: tuple(photos)
            for folder_path, photos in grouped.items()
        }

        prepared = []
        all_dates = [
            photo_date
            for record in records
            if (photo_date := record_date(record)) is not None
        ]
        first_date = min(all_dates) if all_dates else None
        last_date = max(all_dates) if all_dates else None
        first_label = self._date_label(first_date, locale)
        last_label = self._date_label(last_date, locale)

        for folder_path, photos in grouped.items():
            dates = [
                photo_date
                for photo in photos
                if (photo_date := record_date(photo)) is not None
            ]
            # A kártya egyetlen dátuma a csoport legkorábbi képdátuma.
            # A Picasa saját A-tömbjének szemantikája a #5401-ben nyitott.
            card_date = min(dates) if dates else None
            prepared.append((card_date, folder_path, photos))

        prepared.sort(
            key=lambda item: (
                item[0] is None,
                item[0] or date.max,
                Path(item[1]).name.casefold(),
                item[1].casefold(),
            )
        )
        first_ordinal = first_date.toordinal() if first_date else None
        date_span = (
            last_date.toordinal() - first_ordinal
            if first_ordinal is not None and last_date is not None
            else 0
        )

        result = []
        for card_date, folder_path, photos in prepared:
            if card_date is None:
                slider_position = 1.0 if first_ordinal is not None else 0.0
            elif first_ordinal is None or date_span <= 0:
                slider_position = 0.0
            else:
                slider_position = (
                    card_date.toordinal() - first_ordinal
                ) / date_span
            result.append(
                {
                    "name": Path(folder_path).name or folder_path,
                    "folderPath": folder_path,
                    "dateLabel": self._date_label(card_date, locale),
                    "dateValue": card_date.toordinal() if card_date else None,
                    "firstDateLabel": first_label,
                    "lastDateLabel": last_label,
                    "sliderPosition": slider_position,
                    "count": len(photos),
                    # A kártya legfeljebb négy képből álló, egymásra döntött
                    # bélyegköteget mutat; a teljes rekordlista a
                    # diavetítésmodellben marad.
                    "photos": [
                        self._photo_to_qml(photo) for photo in photos[:4]
                    ],
                }
            )
        return result

    @staticmethod
    def _date_label(value, locale: QLocale) -> str:
        if value is None:
            return ""
        month = locale.standaloneMonthName(
            value.month, QLocale.FormatType.LongFormat
        )
        return f"{month[:1].upper()}{month[1:]} {value.year}"

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
            # #463: piros geo-pin jelvény - ld. models.py itemAt()
            "hasGeo": photo.location is not None,
        }
