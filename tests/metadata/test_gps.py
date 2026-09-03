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
    """#2012: a Picasa MINDIG hat tizedesjegyet ír, a záró nullákkal együtt.

    A korábbi három állítás a mi HIBÁS viselkedésünket rögzítette (záró
    nullák levágva). Bizonyíték a javításra:

    - a `sprintf` formátuma `%lf,%lf` (`0x00c8187c`, a hívás `0x007d57fb`),
      a kulcsnév `geotag` (`0x00c81874`, `0x007d582e`); MSVC-ben a
      `printf`-beli `%lf` azonos a `%f`-fel ⇒ hat tizedesjegy;
    - a tulajdonos 859 fájlos `.picasa.ini`-korpuszában mind a **84**
      valós `geotag=` érték 6/6 tizedesjeggyel áll.

    A `rstrip` indoka („a kerek koordináta ne `33.770556000` alakban
    íródjon") téves volt: a `%.6f` sosem ad hatnál több tizedest, tehát a
    levágás KIZÁRÓLAG olyan jegyeket vett el, amiket a Picasa megtart.
    """

    def test_a_kerek_ertek_is_hat_tizedessel_all(self):
        assert format_geotag(47.5, 19.05) == "47.500000,19.050000"

    def test_negative_values(self):
        assert format_geotag(-33.9, -18.42) == "-33.900000,-18.420000"

    def test_zero_is_written_as_zero(self):
        assert format_geotag(0.0, 0.0) == "0.000000,0.000000"

    def test_a_korpuszbol_vett_valodi_ertek(self):
        """A jegyben nevesített két érték — ma `47.82002`-t adnánk."""
        assert format_geotag(47.82002, 18.848376) == "47.820020,18.848376"
        assert format_geotag(47.82002, 18.85157) == "47.820020,18.851570"

    def test_a_hetedik_tizedes_KEREKITODIK_nem_csonkul(self):
        """A `%.6f` kerekít; ezt a javítás nem változtatja meg."""
        assert format_geotag(1.00000049, 0.0).startswith("1.000000")
        assert format_geotag(1.00000051, 0.0).startswith("1.000001")


class TestABeolvasasTOVABBRA_IS_TURO:
    """#2012: a javítás CSAK az írást érinti.

    A korábbi verzióink rövid alakot írtak a felhasználók fájljaiba; azt
    továbbra is el kell tudni olvasni, különben a saját múltunkat
    veszítjük el."""

    def test_a_rovid_alak_beolvashato(self):
        pont = parse_geotag("47.82002,18.848376")
        assert pont is not None
        assert pont.latitude == pytest.approx(47.82002)
        assert pont.longitude == pytest.approx(18.848376)

    def test_a_HAT_tizedeses_alak_is_beolvashato(self):
        pont = parse_geotag("47.820020,18.848376")
        assert pont is not None
        assert pont.latitude == pytest.approx(47.82002)

    def test_a_rovid_alak_beolvasva_es_visszairva_a_HOSSZU_alakot_adja(self):
        pont = parse_geotag("47.5,19.05")
        assert pont is not None
        assert pont.as_geotag() == "47.500000,19.050000"

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
