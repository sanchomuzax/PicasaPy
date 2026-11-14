"""`TimelineController._photo_to_qml` — a rács-adatok kigyűjtése egy
`PhotoRecord`-ból (#463: a piros geo-pin jelvény is innen jön)."""

from dataclasses import replace
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QLocale

from picasapy.app.timeline_controller import TimelineController
from picasapy.index import PhotoRecord


def _record(geotag: str | None = None, exif_lat=None, exif_lon=None):
    return PhotoRecord(
        id=1,
        folder_path="/kepek",
        name="a.jpg",
        kind="photo",
        size=0,
        mtime_ns=0,
        star=False,
        caption=None,
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=None,
        height=None,
        geotag=geotag,
        exif_lat=exif_lat,
        exif_lon=exif_lon,
    )


class TestPhotoToQmlHasGeo:
    def test_no_location_no_geo_mark(self, qt_app):
        item = TimelineController._photo_to_qml(_record())
        assert item["hasGeo"] is False

    def test_ini_geotag_marks_geo(self, qt_app):
        item = TimelineController._photo_to_qml(_record(geotag="47.5,19.05"))
        assert item["hasGeo"] is True

    def test_exif_gps_marks_geo(self, qt_app):
        item = TimelineController._photo_to_qml(
            _record(exif_lat=47.5, exif_lon=19.05)
        )
        assert item["hasGeo"] is True


class TestTimelineCollectionCards:
    def test_same_day_collections_sort_by_full_taken_at_not_name(self, qt_app):
        controller = TimelineController(Path("unused-index.db"), provider=None)
        later = replace(
            _record(),
            id=1,
            folder_path="/library/Alpha",
            name="later.jpg",
            taken_at="2024-05-08T17:45:00",
        )
        earlier = replace(
            _record(),
            id=2,
            folder_path="/library/Zulu",
            name="earlier.jpg",
            taken_at="2024-05-08T09:15:00",
        )

        collections = controller._collections_to_qml(
            (later, earlier), QLocale("en_US")
        )

        assert TimelineController._exif_date(earlier) == datetime(
            2024, 5, 8, 9, 15
        )
        assert [item["name"] for item in collections] == ["Zulu", "Alpha"]
        assert [item["dateValue"] for item in collections] == [
            datetime(2024, 5, 8).toordinal(),
            datetime(2024, 5, 8).toordinal(),
        ]
        assert [item["dateLabel"] for item in collections] == [
            "May 2024",
            "May 2024",
        ]
        assert [item["firstDateLabel"] for item in collections] == [
            "May 2024",
            "May 2024",
        ]
        assert [item["lastDateLabel"] for item in collections] == [
            "May 2024",
            "May 2024",
        ]
        assert [item["sliderPosition"] for item in collections] == [0.0, 0.0]

    def test_exif_nelkul_a_befagyasztott_fajlido_adja_a_kartyat_es_a_savot(
        self, qt_app
    ):
        controller = TimelineController(Path("unused-index.db"), provider=None)
        before = replace(
            _record(),
            id=1,
            folder_path="/library/before",
            taken_at="2014-05-01T10:00:00",
        )
        without_exif = replace(
            _record(),
            id=2,
            folder_path="/library/without-exif",
            first_seen_mtime_ns=int(datetime(2015, 5, 10, 12).timestamp() * 1e9),
        )
        after = replace(
            _record(),
            id=3,
            folder_path="/library/after",
            taken_at="2016-07-11T10:00:00",
        )

        collections = controller._collections_to_qml(
            (before, without_exif, after), QLocale("en_US")
        )

        assert [item["name"] for item in collections] == [
            "before",
            "without-exif",
            "after",
        ]
        assert collections[1]["dateLabel"] == "May 2015"
        assert collections[1]["sliderPosition"] not in (0.0, 1.0)
        assert {item["firstDateLabel"] for item in collections} == {"May 2014"}
        assert {item["lastDateLabel"] for item in collections} == {"July 2016"}

    def test_recently_updated_kartya_a_megnyitaskori_honapban_a_lista_vegere_kerul(
        self, qt_app
    ):
        from picasapy.index.albums import AlbumRecord
        from picasapy.ini import RECENT_ALBUM_TOKEN

        controller = TimelineController(Path("unused-index.db"), provider=None)
        controller._timeline_opened_at = datetime(2026, 11, 14, 9, 30)
        old_photo = replace(
            _record(), id=1, taken_at="2005-04-03T10:00:00"
        )
        recent_album = AlbumRecord(
            token=RECENT_ALBUM_TOKEN,
            name="Recently Updated",
            date=None,
            photo_count=1,
        )

        collections = controller._collections_to_qml(
            (old_photo,),
            QLocale("en_US"),
            ((recent_album, (old_photo,)),),
        )

        card = collections[-1]
        assert card["albumToken"] == RECENT_ALBUM_TOKEN
        assert card["dateLabel"] == "November 2026"
        assert card["dateValue"] == datetime(2026, 11, 14).toordinal()
        assert card["sliderPosition"] == 1.0
        assert card["lastDateLabel"] == "November 2026"

    def test_timezone_aware_taken_at_sorts_with_naive_ones(self, qt_app):
        controller = TimelineController(Path("unused-index.db"), provider=None)
        aware = replace(
            _record(), id=1, folder_path="/library/Video",
            name="clip.mp4", taken_at="2024-05-08T12:00:00Z",
        )
        naive = replace(
            _record(), id=2, folder_path="/library/Photo",
            name="photo.jpg", taken_at="2024-05-08T09:15:00",
        )

        collections = controller._collections_to_qml(
            (aware, naive), QLocale("en_US")
        )

        assert [item["name"] for item in collections] == ["Photo", "Video"]

    def test_cards_are_chronological_and_slideshow_model_is_folder_scoped(
        self, qt_app
    ):
        controller = TimelineController(Path("unused-index.db"), provider=None)
        late = replace(
            _record(),
            id=1,
            folder_path="/library/later",
            name="later.jpg",
            taken_at="2022-01-01T00:00:00",
        )
        early = replace(
            _record(),
            id=2,
            folder_path="/library/earlier",
            name="earlier.jpg",
            taken_at="2020-01-01T00:00:00",
        )
        same_folder = replace(
            early,
            id=3,
            name="next.jpg",
            taken_at="2021-01-01T00:00:00",
        )
        third_in_earlier = replace(
            early,
            id=4,
            name="last.jpg",
            taken_at="2022-01-01T00:00:00",
        )

        collections = controller._collections_to_qml(
            (late, early, same_folder, third_in_earlier), QLocale("en_US")
        )

        assert [item["name"] for item in collections] == ["earlier", "later"]
        assert [item["sliderPosition"] for item in collections] == [0.0, 1.0]
        assert collections[0]["count"] == 3
        # Mindhárom rekord látszik a kötegben; a képkocka legfeljebb négyet rajzol.
        assert len(collections[0]["photos"]) == 3
        model = controller.slideshowModel("/library/earlier")
        assert model.rowCount() == 3
        assert model.filePathAt(0) == "/library/earlier/earlier.jpg"
        assert model.filePathAt(1) == "/library/earlier/next.jpg"
        assert model.filePathAt(2) == "/library/earlier/last.jpg"
