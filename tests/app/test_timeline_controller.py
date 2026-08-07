"""`TimelineController._photo_to_qml` — a rács-adatok kigyűjtése egy
`PhotoRecord`-ból (#463: a piros geo-pin jelvény is innen jön)."""

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
