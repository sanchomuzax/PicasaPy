"""EXIF/IPTC olvasó: dátum, orientáció, méret, felirat, kulcsszavak."""

from picasapy.metadata import EMPTY_METADATA, read_file_metadata


class TestExif:
    def test_taken_at_from_datetime_original(self, jpeg_factory):
        meta = read_file_metadata(jpeg_factory(taken_at="2025:05:01 07:23:10"))
        assert meta.taken_at == "2025-05-01T07:23:10"

    def test_taken_at_falls_back_to_datetime(self, jpeg_factory):
        meta = read_file_metadata(jpeg_factory(datetime_0th="2025:05:02 08:00:00"))
        assert meta.taken_at == "2025-05-02T08:00:00"

    def test_datetime_original_wins(self, jpeg_factory):
        meta = read_file_metadata(
            jpeg_factory(taken_at="2025:05:01 07:23:10", datetime_0th="2025:05:02 08:00:00")
        )
        assert meta.taken_at == "2025-05-01T07:23:10"

    def test_invalid_date_is_none(self, jpeg_factory):
        meta = read_file_metadata(jpeg_factory(taken_at="nem datum"))
        assert meta.taken_at is None

    def test_orientation(self, jpeg_factory):
        assert read_file_metadata(jpeg_factory(orientation=6)).orientation == 6

    def test_orientation_defaults_to_1(self, jpeg_factory):
        assert read_file_metadata(jpeg_factory()).orientation == 1

    def test_dimensions(self, jpeg_factory):
        meta = read_file_metadata(jpeg_factory(size=(32, 16)))
        assert (meta.width, meta.height) == (32, 16)


class TestIptc:
    def test_caption_and_keywords(self, jpeg_factory):
        meta = read_file_metadata(
            jpeg_factory(caption="balatoni naplemente", keywords=("balaton", "nyár"))
        )
        assert meta.caption == "balatoni naplemente"
        assert meta.keywords == ("balaton", "nyár")

    def test_utf8_decoded(self, jpeg_factory):
        meta = read_file_metadata(jpeg_factory(caption="őszi túra — árvíztűrő"))
        assert meta.caption == "őszi túra — árvíztűrő"

    def test_no_iptc(self, jpeg_factory):
        meta = read_file_metadata(jpeg_factory())
        assert meta.caption is None
        assert meta.keywords == ()

    def test_single_keyword(self, jpeg_factory):
        assert read_file_metadata(jpeg_factory(keywords=("egy",))).keywords == ("egy",)


class TestRobustness:
    def test_corrupt_file_gives_empty(self, tmp_path):
        bad = tmp_path / "rossz.jpg"
        bad.write_bytes(b"ez nem jpeg")
        assert read_file_metadata(bad) == EMPTY_METADATA

    def test_missing_file_gives_empty(self, tmp_path):
        assert read_file_metadata(tmp_path / "nincs.jpg") == EMPTY_METADATA

    def test_png_dimensions_without_exif(self, tmp_path):
        from PIL import Image

        png = tmp_path / "kep.png"
        Image.new("RGB", (10, 20), "blue").save(png, "PNG")
        meta = read_file_metadata(png)
        assert (meta.width, meta.height) == (10, 20)
        assert meta.taken_at is None

    def test_empty_metadata_is_frozen(self):
        import pytest

        with pytest.raises(AttributeError):
            EMPTY_METADATA.caption = "x"
