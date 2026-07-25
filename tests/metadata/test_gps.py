"""GPS-koordináták (#30): `geotag=` értelmezés/írás és EXIF GPS-olvasás."""

import pytest

from picasapy.metadata.gps import (
    GeoPoint,
    format_geotag,
    parse_geotag,
    photo_location,
    read_exif_gps,
)
from support.jpeg_factory import make_jpeg


class TestGeoPoint:
    def test_valid_point(self):
        point = GeoPoint(47.4979, 19.0402)
        assert point.latitude == pytest.approx(47.4979)

    @pytest.mark.parametrize(
        ("lat", "lon"), [(91.0, 0.0), (-90.5, 0.0), (0.0, 181.0), (0.0, -180.5)]
    )
    def test_out_of_range_is_error(self, lat, lon):
        with pytest.raises(ValueError):
            GeoPoint(lat, lon)

    def test_as_geotag_roundtrips(self):
        point = GeoPoint(33.770556, -84.293055)
        assert parse_geotag(point.as_geotag()) == point


class TestParseGeotag:
    def test_picasa_sample(self):
        point = parse_geotag("33.770556,-84.293055")
        assert point == GeoPoint(33.770556, -84.293055)

    def test_spaces_are_tolerated(self):
        assert parse_geotag(" 47.5 , 19.05 ") == GeoPoint(47.5, 19.05)

    def test_extra_fields_are_ignored(self):
        assert parse_geotag("47.5,19.05,123.4") == GeoPoint(47.5, 19.05)

    @pytest.mark.parametrize(
        "text", [None, "", "47.5", "észak,kelet", "999,0", "0,999", ","]
    )
    def test_invalid_is_none(self, text):
        assert parse_geotag(text) is None


class TestFormatGeotag:
    def test_six_decimals_without_trailing_zeros(self):
        assert format_geotag(47.5, 19.05) == "47.5,19.05"

    def test_negative_values(self):
        assert format_geotag(-33.9, -18.42) == "-33.9,-18.42"

    def test_zero_is_written_as_zero(self):
        assert format_geotag(0.0, 0.0) == "0,0"

    def test_out_of_range_is_error(self):
        with pytest.raises(ValueError):
            format_geotag(120.0, 0.0)


class TestReadExifGps:
    def test_reads_written_coordinates(self, tmp_path):
        path = make_jpeg(tmp_path / "gps.jpg", gps=(47.4979, 19.0402))
        point = read_exif_gps(path)
        assert point is not None
        assert point.latitude == pytest.approx(47.4979, abs=1e-4)
        assert point.longitude == pytest.approx(19.0402, abs=1e-4)

    def test_southern_western_hemisphere_is_negative(self, tmp_path):
        path = make_jpeg(tmp_path / "gps.jpg", gps=(-33.9249, -18.4241))
        point = read_exif_gps(path)
        assert point.latitude < 0 and point.longitude < 0

    def test_photo_without_gps_is_none(self, tmp_path):
        assert read_exif_gps(make_jpeg(tmp_path / "sima.jpg")) is None

    def test_broken_file_is_none(self, tmp_path):
        broken = tmp_path / "romlott.jpg"
        broken.write_bytes(b"nem kep")
        assert read_exif_gps(broken) is None

    def test_missing_file_is_none(self, tmp_path):
        assert read_exif_gps(tmp_path / "nincs.jpg") is None


class TestPhotoLocation:
    def test_ini_geotag_wins_over_exif(self, tmp_path):
        path = make_jpeg(tmp_path / "gps.jpg", gps=(47.4979, 19.0402))
        point = photo_location("10.0,20.0", path)
        assert point == GeoPoint(10.0, 20.0)

    def test_falls_back_to_exif(self, tmp_path):
        path = make_jpeg(tmp_path / "gps.jpg", gps=(47.4979, 19.0402))
        point = photo_location(None, path)
        assert point is not None and point.latitude == pytest.approx(47.4979, abs=1e-4)

    def test_broken_geotag_falls_back_to_exif(self, tmp_path):
        path = make_jpeg(tmp_path / "gps.jpg", gps=(47.4979, 19.0402))
        assert photo_location("hupak", path) is not None

    def test_nothing_anywhere_is_none(self, tmp_path):
        assert photo_location(None, make_jpeg(tmp_path / "sima.jpg")) is None

    def test_without_path_only_the_ini_counts(self):
        assert photo_location("47.5,19.05", None) == GeoPoint(47.5, 19.05)
        assert photo_location(None, None) is None
