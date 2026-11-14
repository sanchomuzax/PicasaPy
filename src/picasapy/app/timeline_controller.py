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

from PySide6.QtCore import Property, QCoreApplication, QLocale, QObject, Signal, Slot

from picasapy.index import (
    PhotoRecord,
    AlbumRecord,
    album_photos,
    albums_in_index,
    all_photos,
    open_index,
)
from picasapy.ini import RECENT_ALBUM_TOKEN

from .models import PhotoGridModel, _has_edits, _thumb_url
from ..timeline_motion import (
    CARD_STEP,
    DEFAULT_BEZIER_POINTS,
    animator_position,
    card_stack_offset,
    carousel_layout,
    clamp_offset,
    frame_transforms,
    focus_index,
    focus_parameter,
    rational_cubic_bezier,
    slider_index,
    slider_thumb_x,
    slideshow_easing,
    timeline_leader_points,
    timeline_dot_positions,
    timeline_text_alphas,
)


class TimelineController(QObject):
    """A mappa- és albumkártyákat, illetve a mozgásképleteket adja a QML-nek."""

    collectionsChanged = Signal()

    def __init__(
        self,
        db_path: Path,
        provider,
        parent: QObject | None = None,
        sync_controller=None,
    ):
        """`provider`: a MEGLÉVŐ (az AppControllerrel közös) ThumbnailProvider
        - a bélyegkép-URL-ek (`image://thumbs/<id>`) csak akkor oldódnak fel,
        ha a fotó nála regisztrálva van (`register_photos`)."""
        super().__init__(parent)
        self._db_path = db_path
        self._provider = provider
        self._sync_controller = sync_controller
        self._timeline_open = False
        self._dirty = True
        self._collections: list[dict] = []
        self._collection_records_by_id: dict[str, tuple[PhotoRecord, ...]] = {}
        self._collection_slideshow_model: PhotoGridModel | None = None

    @Property("QVariantList", notify=collectionsChanged)
    def collections(self) -> list:
        """A teljes könyvtár gyűjteménykártyái, legrégebbi dátum szerint."""
        return self._collections

    @Slot(bool)
    def setTimelineOpen(self, is_open: bool) -> None:
        """Nyitáskor betölti az elhalasztott vagy elavult Időrend-adatokat."""
        is_open = bool(is_open)
        if self._timeline_open == is_open:
            return
        self._timeline_open = is_open
        if is_open and self._dirty:
            self._do_reload()

    @Slot(float, result="QVariantMap")
    def bezierAt(self, t: float) -> dict:
        """A runtime/bezier.txt négy pontjából számolt görbehely (38.2.61)."""
        x, y, z = rational_cubic_bezier(t, DEFAULT_BEZIER_POINTS)
        return {"x": x, "y": y, "z": z}

    @Slot(result=float)
    def focusParameter(self) -> float:
        return focus_parameter()

    @Slot(float, int, result="QVariantList")
    def carouselLayout(self, offset: float, count: int) -> list:
        return carousel_layout(offset, count)

    @Slot(int, int, result="QVariantList")
    def cardStackOffset(self, collection_index: int, photo_index: int) -> list:
        return list(card_stack_offset(collection_index, photo_index))

    @Slot(float, float, float, float, result="QVariantList")
    def leaderPoints(
        self, start_x: float, start_y: float, end_x: float, end_y: float
    ) -> list:
        return [
            {"x": x, "y": y}
            for x, y in timeline_leader_points(
                (start_x, start_y), (end_x, end_y)
            )
        ]

    @Slot(float, result="QVariantList")
    def labelAlphas(self, progress: float) -> list:
        return list(timeline_text_alphas(progress))

    @Slot(float, int, result=float)
    def clampOffset(self, offset: float, count: int) -> float:
        return clamp_offset(offset, count)

    @Slot(float, int, result=int)
    def focusIndex(self, offset: float, count: int) -> int:
        return focus_index(offset, count)

    @Slot(float, "QVariantList", float, result=float)
    def animatorPosition(self, base_offset: float, records: list, current_time: float) -> float:
        return animator_position(base_offset, records, current_time)

    @Property(float, constant=True)
    def carouselCardStep(self) -> float:
        return CARD_STEP

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
        """Nyitott Időrendben frissít, zárva csak piszkosnak jelöli.

        A nyitott nézet csak akkor kérdez újra, ha az utolsó szinkron tényleg
        megváltoztatta az indexet vagy egy ini-t. A rekordokat mindig a teljes
        indexből olvassa, a rács pillanatnyi szűrésétől függetlenül.
        """
        if not self._timeline_open:
            self._dirty = True
            return
        if (
            self._sync_controller is not None
            and getattr(self._sync_controller, "_last_sync_changed", True) is False
        ):
            return
        self._do_reload()

    def _do_reload(self) -> None:
        self._dirty = False
        with open_index(self._db_path) as conn:
            records = tuple(r for r in all_photos(conn) if not r.hidden)
            albums = albums_in_index(conn)
            visible_by_id = {record.id: record for record in records}
            photos_by_album: dict[str, list[PhotoRecord]] = {
                album.token: [] for album in albums
            }
            for row in conn.execute(
                "SELECT pa.token, pa.photo_id FROM photo_albums pa "
                "JOIN photos p ON p.id = pa.photo_id "
                "JOIN folders f ON f.id = p.folder_id "
                "ORDER BY pa.token, (pa.place IS NULL), pa.place, f.path, p.name"
            ):
                photo = visible_by_id.get(row["photo_id"])
                album_photo_list = photos_by_album.get(row["token"])
                if photo is not None and album_photo_list is not None:
                    album_photo_list.append(photo)
            album_records = tuple(
                (album, tuple(photos_by_album[album.token])) for album in albums
            )
            # a rejtett képek itt sem látszanak, mint a többi kártyán
            recent_photos = tuple(
                p for p in album_photos(conn, RECENT_ALBUM_TOKEN) if p.id in visible_by_id
            )
            if recent_photos:
                recent_album = AlbumRecord(
                    token=RECENT_ALBUM_TOKEN,
                    name=QCoreApplication.translate(
                        "AlbumsSection", "Recently Updated"
                    ),
                    date=None,
                    photo_count=len(recent_photos),
                )
                album_records = tuple(
                    (album, photos)
                    for album, photos in album_records
                    if album.token != RECENT_ALBUM_TOKEN
                ) + ((recent_album, recent_photos),)
        # a bélyegkép-provider regisztere a TELJES könyvtárral bővül -
        # ez szuperhalmaza bármely szűkebb (mappa/keresés) nézetnek, tehát
        # a főrács regisztrációját sosem szűkíti (nem veszít kulcsot)
        self._provider.register_photos(records)
        locale = QLocale()
        self._collections = self._collections_to_qml(
            records, locale, album_records
        )
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
    def _exif_date(record: PhotoRecord) -> datetime | None:
        """Csak az indexelt felvételi dátumot használja; fájlidőre nem esik vissza."""
        if not record.taken_at:
            return None
        try:
            # #6807: időzónás érték (pl. videó `...Z`) se keveredjen a naiv EXIF-időkkel
            return datetime.fromisoformat(record.taken_at).replace(tzinfo=None)
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
