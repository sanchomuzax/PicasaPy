"""formatting.camera_summary_text — Picasa-stílusú, egysoros gép-összefoglaló
a hisztogram-doboz alá (#25)."""

from PySide6.QtCore import QLocale

from picasapy.app.formatting import camera_summary_text
from picasapy.metadata import ExifDetails


def _tr(text):
    return text


class TestCameraSummaryText:
    def test_all_fields_are_joined(self):
        details = ExifDetails(
            camera="Canon EOS 90D",
            exposure_seconds=1 / 125,
            f_number=5.6,
            iso=200,
            focal_mm=50.0,
            flash_fired=False,
        )
        text = camera_summary_text(details, QLocale(), _tr)
        assert "Canon EOS 90D" in text
        assert "1/125 s" in text
        assert "f/5.6" in text
        assert "200" in text
        assert "50" in text
        assert "Flash: Off" in text

    def test_empty_details_gives_empty_string(self):
        assert camera_summary_text(ExifDetails(), QLocale(), _tr) == ""

    def test_missing_fields_are_skipped(self):
        details = ExifDetails(camera="Nikon D850")
        assert camera_summary_text(details, QLocale(), _tr) == "Nikon D850"

    def test_flash_fired_true_reports_fired(self):
        details = ExifDetails(camera="X", flash_fired=True)
        assert "Flash: Fired" in camera_summary_text(details, QLocale(), _tr)

    def test_sub_second_exposure_uses_fraction_form(self):
        details = ExifDetails(exposure_seconds=1 / 400)
        assert camera_summary_text(details, QLocale(), _tr) == "1/400 s"
