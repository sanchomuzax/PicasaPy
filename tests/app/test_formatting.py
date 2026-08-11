"""formatting.camera_summary_text — Picasa-mintájú, kétoszlopos gép-
összefoglaló a hisztogram-doboz alá (#25, #235).

Formátum: soronként `bal\tjobb` cellapár, sorok `\n`-nel elválasztva — a
QML-oldal (HistogramBox.qml) ebből rendereli a két címkézett oszlopot."""

from PySide6.QtCore import QLocale

from picasapy.app.formatting import camera_summary_text
from picasapy.metadata import ExifDetails


def _tr(text):
    return text


def _rows(text):
    return [line.split("\t") for line in text.split("\n")]


def _photo(folder, name, *, width, height, size=1024, kind="photo"):
    """Minimál PhotoRecord-utánzat a Tulajdonságok-panel formázójához."""
    from types import SimpleNamespace

    return SimpleNamespace(
        name=name,
        folder_path=str(folder),
        size=size,
        width=width,
        height=height,
        taken_at=None,
        kind=kind,
        keywords=(),
    )



class TestCameraSummaryText:
    def test_all_fields_in_two_labeled_columns(self):
        details = ExifDetails(
            camera="Canon EOS 90D",
            exposure_seconds=1 / 125,
            f_number=5.6,
            iso=200,
            focal_mm=50.0,
            focal_35mm=80,
            flash_fired=False,
        )
        rows = _rows(camera_summary_text(details, QLocale(), _tr))
        # bal oszlop: gép, fókusztávolság címkével, 35 mm-egyenérték
        assert rows[0][0] == "Canon EOS 90D"
        assert rows[1][0] == "Focal length: 50 mm"
        assert rows[2][0] == "(35 mm equivalent: 80 mm)"
        # jobb oszlop: expozíció, rekesz, ISO címkével, vaku
        assert rows[0][1] == "1/125 s"
        assert rows[1][1] == "f/5.6"
        assert rows[2][1] == "ISO: 200"
        assert rows[3][1] == "Flash: Off"

    def test_empty_details_gives_empty_string(self):
        assert camera_summary_text(ExifDetails(), QLocale(), _tr) == ""

    def test_missing_fields_are_skipped(self):
        details = ExifDetails(camera="Nikon D850")
        assert camera_summary_text(details, QLocale(), _tr) == "Nikon D850\t"

    def test_flash_fired_true_reports_fired(self):
        details = ExifDetails(camera="X", flash_fired=True)
        rows = _rows(camera_summary_text(details, QLocale(), _tr))
        assert rows[0] == ["X", "Flash: Fired"]

    def test_sub_second_exposure_uses_fraction_form(self):
        details = ExifDetails(exposure_seconds=1 / 400)
        assert camera_summary_text(details, QLocale(), _tr) == "\t1/400 s"

    def test_no_equivalent_without_35mm_field(self):
        details = ExifDetails(camera="X", focal_mm=6.72)
        text = camera_summary_text(details, QLocale(), _tr)
        assert "equivalent" not in text
        assert "Focal length: 6.72 mm" in text


class TestPropertiesOrderFollowsPicasa:
    """#529: a mezők sorrendje és felirata a Picasa `runtime/properties.xml`
    szerinti — EXIF-gazdag képen rögzítve."""

    @staticmethod
    def _rich_jpeg(path):
        import piexif
        from PIL import Image

        Image.new("RGB", (12, 8), "blue").save(path, "JPEG")
        piexif.insert(
            piexif.dump({
                "0th": {
                    piexif.ImageIFD.Make: b"NIKON CORPORATION",
                    piexif.ImageIFD.Model: b"NIKON D40",
                    piexif.ImageIFD.Orientation: 6,
                    piexif.ImageIFD.DateTime: b"2020:01:02 03:04:05",
                },
                "Exif": {
                    piexif.ExifIFD.DateTimeOriginal: b"2019:05:06 07:08:09",
                    piexif.ExifIFD.DateTimeDigitized: b"2019:05:06 07:08:10",
                    piexif.ExifIFD.ExposureTime: (1, 250),
                    piexif.ExifIFD.FNumber: (56, 10),
                    piexif.ExifIFD.ISOSpeedRatings: 800,
                    piexif.ExifIFD.FocalLength: (50, 1),
                    piexif.ExifIFD.FocalLengthIn35mmFilm: 75,
                    piexif.ExifIFD.Flash: 1,
                    piexif.ExifIFD.WhiteBalance: 0,
                    piexif.ExifIFD.MeteringMode: 2,
                    piexif.ExifIFD.ExposureProgram: 3,
                    piexif.ExifIFD.ColorSpace: 1,
                    piexif.ExifIFD.LensModel: b"AF-S 18-55",
                    piexif.ExifIFD.SubjectDistance: (3, 1),
                    piexif.ExifIFD.ImageUniqueID: b"abc123",
                },
            }),
            str(path),
        )

    def test_field_order_matches_properties_xml(self, tmp_path):
        from picasapy.app.formatting import properties_entries

        path = tmp_path / "gazdag.jpg"
        self._rich_jpeg(path)
        photo = _photo(tmp_path, "gazdag.jpg", width=12, height=8)
        labels = [
            label
            for label, _ in properties_entries(photo, QLocale("en"), lambda t: t)
        ]

        expected_order = [
            "File Path", "File Size", "Dimensions",
            "Camera Make", "Camera Model",
            "Camera Date", "Digitized Date", "Modified Date",
            "Orientation", "Flash", "Lens",
            "Focal Length", "Focal Length in 35mm Film",
            "Exposure Time", "F Number", "Subject Distance", "ISO",
            "White Balance", "Metering Mode", "Exposure Program",
            "Color Space", "Unique ID",
        ]
        present = [label for label in expected_order if label in labels]
        assert [label for label in labels if label in expected_order] == present
        # a sorrend a properties.xml-é: minden várt mező meg is jelenik
        assert present == expected_order

    def test_enum_values_are_labels_not_raw_exif_keys(self, tmp_path):
        from picasapy.app.formatting import properties_entries

        path = tmp_path / "gazdag.jpg"
        self._rich_jpeg(path)
        photo = _photo(tmp_path, "gazdag.jpg", width=12, height=8)
        values = dict(properties_entries(photo, QLocale("en"), lambda t: t))

        assert values["Metering Mode"] == "Center Weight"
        assert values["Exposure Program"] == "Aperture Priority"
        assert values["Color Space"] == "sRGB"
        assert values["Orientation"] == "Rotated 90° CW"
        assert values["Flash"] == "Fired"
        assert values["White Balance"] == "Auto"

    def test_missing_fields_are_skipped(self, tmp_path):
        """Adat nélküli mező KIMARAD — nem üres sorként jelenik meg."""
        from PIL import Image

        from picasapy.app.formatting import properties_entries

        path = tmp_path / "csupasz.jpg"
        Image.new("RGB", (4, 4), "red").save(path, "JPEG")
        photo = _photo(tmp_path, "csupasz.jpg", width=4, height=4)
        entries = properties_entries(photo, QLocale("en"), lambda t: t)

        assert all(value not in (None, "") for _, value in entries)
        assert "Lens" not in dict(entries)
