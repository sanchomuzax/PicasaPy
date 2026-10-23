"""`TimelineController._photo_to_qml` — a rács-adatok kigyűjtése egy
`PhotoRecord`-ból (#463: a piros geo-pin jelvény is innen jön)."""

from dataclasses import replace
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
