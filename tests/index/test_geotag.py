"""Geocímke az indexben (#30): tárolás, feloldás, `geotagged_photos`."""

import pytest

from picasapy.index import geotagged_photos, open_index, photos_in_folder, sync_tree
from picasapy.metadata.gps import GeoPoint
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "exif.jpg", gps=(47.4979, 19.0402))
    make_jpeg(root / "nyaralas" / "ini.jpg")
    make_jpeg(root / "nyaralas" / "sehol.jpg")
    make_jpeg(root / "nyaralas" / "romlott_ini.jpg")
    (root / "nyaralas" / ".picasa.ini").write_text(
        "[ini.jpg]\ngeotag=10.5,20.25\n\n[romlott_ini.jpg]\ngeotag=hupak\n",
        encoding="utf-8",
    )
    return root


@pytest.fixture
def conn(tmp_path, library):
    with open_index(tmp_path / "index.db") as connection:
        sync_tree(connection, library)
        yield connection


def _by_name(records):
    return {record.name: record for record in records}


class TestStoredLocation:
    def test_exif_gps_is_indexed(self, conn, library):
        record = _by_name(photos_in_folder(conn, library / "nyaralas"))["exif.jpg"]
        assert record.location is not None
        assert record.location.latitude == pytest.approx(47.4979, abs=1e-4)

    def test_ini_geotag_is_indexed(self, conn, library):
        record = _by_name(photos_in_folder(conn, library / "nyaralas"))["ini.jpg"]
        assert record.geotag == "10.5,20.25"
        assert record.location == GeoPoint(10.5, 20.25)

    def test_photo_without_location(self, conn, library):
        record = _by_name(photos_in_folder(conn, library / "nyaralas"))["sehol.jpg"]
        assert record.location is None

    def test_broken_geotag_is_kept_but_not_located(self, conn, library):
        record = _by_name(photos_in_folder(conn, library / "nyaralas"))[
            "romlott_ini.jpg"
        ]
        # a nyers érték megmarad (round-trip elv), de helyet nem ad
        assert record.geotag == "hupak"
        assert record.location is None

    def test_ini_wins_over_exif(self, conn, library):
        ini = library / "nyaralas" / ".picasa.ini"
        ini.write_text("[exif.jpg]\ngeotag=1.5,2.5\n", encoding="utf-8")
        sync_tree(conn, library)
        record = _by_name(photos_in_folder(conn, library / "nyaralas"))["exif.jpg"]
        assert record.location == GeoPoint(1.5, 2.5)


class TestGeotaggedPhotos:
    def test_only_located_photos(self, conn):
        names = {record.name for record in geotagged_photos(conn)}
        assert names == {"exif.jpg", "ini.jpg"}

    def test_every_record_has_a_location(self, conn):
        assert all(record.location is not None for record in geotagged_photos(conn))

    def test_empty_library(self, tmp_path):
        empty = tmp_path / "ures"
        empty.mkdir()
        with open_index(tmp_path / "ures.db") as connection:
            sync_tree(connection, empty)
            assert geotagged_photos(connection) == ()


class TestIniChangeIsPickedUp:
    def test_new_geotag_without_file_change(self, conn, library):
        """Csak az ini változik (a fájl bitre azonos) — a gyorsútnak is
        át kell vinnie az új geocímkét (#139-es változás-detektálás)."""
        ini = library / "nyaralas" / ".picasa.ini"
        ini.write_text("[sehol.jpg]\ngeotag=5.5,6.5\n", encoding="utf-8")
        sync_tree(conn, library)
        record = _by_name(photos_in_folder(conn, library / "nyaralas"))["sehol.jpg"]
        assert record.location == GeoPoint(5.5, 6.5)

    def test_removed_geotag_falls_back_to_exif(self, conn, library):
        ini = library / "nyaralas" / ".picasa.ini"
        ini.write_text("[exif.jpg]\ngeotag=1.5,2.5\n", encoding="utf-8")
        sync_tree(conn, library)
        ini.write_text("[exif.jpg]\nstar=yes\n", encoding="utf-8")
        sync_tree(conn, library)
        record = _by_name(photos_in_folder(conn, library / "nyaralas"))["exif.jpg"]
        assert record.geotag is None
        assert record.location.latitude == pytest.approx(47.4979, abs=1e-4)
