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
