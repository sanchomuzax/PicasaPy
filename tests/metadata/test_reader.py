"""EXIF/IPTC olvasó: dátum, orientáció, méret, felirat, kulcsszavak."""

import piexif

from picasapy.metadata import (
    EMPTY_EXIF_DETAILS,
    EMPTY_METADATA,
    read_exif_details,
    read_file_metadata,
)


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


def _jpeg_with_exif(tmp_path, zeroth=None, exif_ifd=None):
    """Kis JPEG a megadott nyers EXIF-taggekkel (piexif)."""
    from PIL import Image

    path = tmp_path / "exif.jpg"
    Image.new("RGB", (8, 6), "red").save(path, "JPEG")
    piexif.insert(
        piexif.dump({"0th": zeroth or {}, "Exif": exif_ifd or {}}), str(path)
    )
    return path


class TestExifDetails:
    """#13: a Tulajdonságok-panel fényképezőgép-adatai."""

    def test_full_details(self, tmp_path):
        photo = _jpeg_with_exif(
            tmp_path,
            zeroth={
                piexif.ImageIFD.Make: b"Canon",
                piexif.ImageIFD.Model: b"EOS 550D",
            },
            exif_ifd={
                piexif.ExifIFD.ExposureTime: (1, 125),
                piexif.ExifIFD.FNumber: (28, 10),
                piexif.ExifIFD.ISOSpeedRatings: 400,
                piexif.ExifIFD.FocalLength: (35, 1),
                piexif.ExifIFD.Flash: 1,
                piexif.ExifIFD.WhiteBalance: 0,
            },
        )
        details = read_exif_details(photo)
        assert details.camera == "Canon EOS 550D"
        assert details.exposure_seconds == 1 / 125
        assert details.f_number == 2.8
        assert details.iso == 400
        assert details.focal_mm == 35
        assert details.flash_fired is True
        assert details.white_balance == "auto"

    def test_model_alone_without_make(self, tmp_path):
        photo = _jpeg_with_exif(
            tmp_path, zeroth={piexif.ImageIFD.Model: b"PowerShot A80"}
        )
        assert read_exif_details(photo).camera == "PowerShot A80"

    def test_model_repeating_make_not_duplicated(self, tmp_path):
        # sok gyártó a Model-be is beleírja a márkát (pl. "Canon EOS...")
        photo = _jpeg_with_exif(
            tmp_path,
            zeroth={
                piexif.ImageIFD.Make: b"Canon",
                piexif.ImageIFD.Model: b"Canon EOS 550D",
            },
        )
        assert read_exif_details(photo).camera == "Canon EOS 550D"

    def test_no_exif_gives_empty(self, tmp_path):
        from PIL import Image

        path = tmp_path / "sima.jpg"
        Image.new("RGB", (4, 4), "red").save(path, "JPEG")
        assert read_exif_details(path) == EMPTY_EXIF_DETAILS

    def test_flash_not_fired_and_manual_wb(self, tmp_path):
        photo = _jpeg_with_exif(
            tmp_path,
            exif_ifd={
                piexif.ExifIFD.Flash: 16,  # 0. bit = 0: nem villant
                piexif.ExifIFD.WhiteBalance: 1,
            },
        )
        details = read_exif_details(photo)
        assert details.flash_fired is False
        assert details.white_balance == "manual"

    def test_corrupt_file_gives_empty(self, tmp_path):
        bad = tmp_path / "rossz.jpg"
        bad.write_bytes(b"nem jpeg")
        assert read_exif_details(bad) == EMPTY_EXIF_DETAILS

    def test_zero_denominator_ignored(self, tmp_path):
        photo = _jpeg_with_exif(
            tmp_path, exif_ifd={piexif.ExifIFD.ExposureTime: (1, 0)}
        )
        assert read_exif_details(photo).exposure_seconds is None
