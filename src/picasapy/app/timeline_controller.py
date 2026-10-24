"""Teljes képernyős Időrend bemutató (#5770), Qt/QML-híd.

A mappa- és albumkártyák az indexelt, látható fotókból épülnek. A kártya
hónap/év felirata és időrendi helye az indexelt felvételi dátumot használja;
hiányzó dátumnál nem helyettesíti fájlidővel. A qshow `A` tömbjének valódi
jelentése nyitott (#5401), ezért a QML `sliderPosition` értéke normalizált
dátumtartomány, nem az eredeti tömb rekonstruálása. A teljes képkockánkénti
mozgás és rétegrajzolás szintén nyitott; a mért görbe- és transzformációs
képleteket a `timeline_motion` szolgáltatja.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from PySide6.QtCore import Property, QLocale, QObject, Signal, Slot

from picasapy.index import (
    PhotoRecord,
    album_photos,
    albums_in_index,
    all_photos,
    open_index,
)

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
    """A mappa- és albumkártyákat, illetve a mozgásképleteket adja a QML-nek."""

    collectionsChanged = Signal()

    def __init__(self, db_path: Path, provider, parent: QObject | None = None):
        """`provider`: a MEGLÉVŐ (az AppControllerrel közös) ThumbnailProvider
        - a bélyegkép-URL-ek (`image://thumbs/<id>`) csak akkor oldódnak fel,
        ha a fotó nála regisztrálva van (`register_photos`)."""
        super().__init__(parent)
        self._db_path = db_path
        self._provider = provider
        self._collections: list[dict] = []
        self._collection_records_by_id: dict[str, tuple[PhotoRecord, ...]] = {}
        self._collection_slideshow_model: PhotoGridModel | None = None

    @Property("QVariantList", notify=collectionsChanged)
    def collections(self) -> list:
        """A teljes könyvtár gyűjteménykártyái, legrégebbi dátum szerint."""
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
    def slideshowModel(self, collection_id: str) -> QObject:
        """Az Időrend-kártya mappa- vagy albumsaját diavetítésmodellje."""
        if self._collection_slideshow_model is None:
            self._collection_slideshow_model = PhotoGridModel(self)
        records = self._collection_records_by_id.get(collection_id)
        if records is None:
            # A korábbi hívó közvetlenül mappaútvonalat adott meg.
            records = self._collection_records_by_id.get(f"folder:{collection_id}", ())
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
            albums = tuple(
                (
                    album,
                    tuple(
                        r for r in album_photos(conn, album.token) if not r.hidden
                    ),
                )
                for album in albums_in_index(conn)
            )
        # a bélyegkép-provider regisztere a TELJES könyvtárral bővül -
        # ez szuperhalmaza bármely szűkebb (mappa/keresés) nézetnek, tehát
        # a főrács regisztrációját sosem szűkíti (nem veszít kulcsot)
        self._provider.register_photos(records)
        locale = QLocale()
        self._collections = self._collections_to_qml(records, locale, albums)
        self.collectionsChanged.emit()

    def _collections_to_qml(
        self, records: tuple, locale: QLocale, albums: tuple = ()
    ) -> list[dict]:
        grouped: dict[str, list[PhotoRecord]] = {}
        for record in records:
            grouped.setdefault(record.folder_path, []).append(record)
        self._collection_records_by_id = {}

        prepared = []
        all_dates = [
            photo_date
            for record in records
            if (photo_date := self._exif_date(record)) is not None
        ]
        first_date = min(all_dates) if all_dates else None
        last_date = max(all_dates) if all_dates else None
        first_label = self._date_label(first_date, locale)
        last_label = self._date_label(last_date, locale)

        for folder_path, photos in grouped.items():
            self._append_collection(
                prepared,
                collection_id=f"folder:{folder_path}",
                kind="folder",
                name=Path(folder_path).name or folder_path,
                folder_path=folder_path,
                album_token="",
                photos=tuple(photos),
            )

        for album, photos in albums:
            if not photos:
                continue
            self._append_collection(
                prepared,
                collection_id=f"album:{album.token}",
                kind="album",
                name=album.name or album.token,
                folder_path="",
                album_token=album.token,
                photos=photos,
            )

        prepared.sort(
            key=lambda item: (
                item["date"] is None,
                item["date"] or date.max,
                item["name"].casefold(),
                item["collectionId"].casefold(),
            )
        )
        first_ordinal = first_date.toordinal() if first_date else None
        date_span = (
            last_date.toordinal() - first_ordinal
            if first_ordinal is not None and last_date is not None
            else 0
        )

        result = []
        for collection in prepared:
            card_date = collection["date"]
            collection_id = collection["collectionId"]
            photos = collection["records"]
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
                    "collectionId": collection_id,
                    "kind": collection["kind"],
                    "name": collection["name"],
                    "folderPath": collection["folderPath"],
                    "albumToken": collection["albumToken"],
                    "firstPhotoPath": self._photo_path(photos[0]),
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
            self._collection_records_by_id[collection_id] = photos
        return result

    def _append_collection(
        self,
        prepared: list[dict],
        *,
        collection_id: str,
        kind: str,
        name: str,
        folder_path: str,
        album_token: str,
        photos: tuple[PhotoRecord, ...],
    ) -> None:
        dates = [
            photo_date
            for photo in photos
            if (photo_date := self._exif_date(photo)) is not None
        ]
        prepared.append(
            {
                "collectionId": collection_id,
                "kind": kind,
                "name": name,
                "folderPath": folder_path,
                "albumToken": album_token,
                "date": min(dates) if dates else None,
                "records": photos,
            }
        )

    @staticmethod
    def _exif_date(record: PhotoRecord) -> date | None:
        """Csak az indexelt felvételi dátumot használja; fájlidőre nem esik vissza."""
        if not record.taken_at:
            return None
        try:
            return datetime.fromisoformat(record.taken_at).date()
        except ValueError:
            return None

    @staticmethod
    def _photo_path(photo: PhotoRecord) -> str:
        return str(Path(photo.folder_path) / photo.name)

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
