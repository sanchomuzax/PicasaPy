"""Egységteszt: `picasapy.importsource` (#23) — forrás-beolvasás és a
mappa-sablon szerinti cél-alútvonal, tiszta Python (Qt/GUI nélkül).

Peremesetek: hiányzó EXIF-dátum → mtime-visszaesés, teljesen ismeretlen
dátum (sem EXIF, sem statolható mtime), egyéni sablon, üres/hiányzó forrás.
"""

import dataclasses
import os
from datetime import date

import pytest

from picasapy.importsource import (
    DEFAULT_TEMPLATE,
    UNKNOWN_DATE_FOLDER_NAME,
    ImportCandidate,
    destination_subpath,
    scan_source,
)
from support.jpeg_factory import make_jpeg


class TestScanSource:
    def test_missing_source_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            scan_source(tmp_path / "nincs-ilyen")

    def test_empty_source_returns_no_candidates(self, tmp_path):
        source = tmp_path / "ures-kartya"
        source.mkdir()
        assert scan_source(source) == ()

    def test_finds_pictures_with_exif_date(self, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg", taken_at="2024:01:15 10:00:00")

        candidates = scan_source(source)

        assert len(candidates) == 1
        assert candidates[0].path == source / "a.jpg"
        assert candidates[0].date == date(2024, 1, 15)

    def test_falls_back_to_mtime_when_exif_date_missing(self, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        photo = source / "b.jpg"
        make_jpeg(photo)  # nincs EXIF-dátum

        some_time = 1_700_000_000  # 2023-11-14 körüli időbélyeg (UNIX s)
        os.utime(photo, (some_time, some_time))

        candidates = scan_source(source)

        assert len(candidates) == 1
        from datetime import datetime

        assert candidates[0].date == datetime.fromtimestamp(some_time).date()

    def test_recurses_into_camera_card_style_subfolders(self, tmp_path):
        source = tmp_path / "kartya"
        (source / "DCIM" / "100CANON").mkdir(parents=True)
        make_jpeg(source / "DCIM" / "100CANON" / "img1.jpg")

        candidates = scan_source(source)

        assert len(candidates) == 1
        assert candidates[0].path == source / "DCIM" / "100CANON" / "img1.jpg"

    def test_non_media_files_are_ignored(self, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        (source / "olvasdel.txt").write_text("nem kép")

        candidates = scan_source(source)

        assert [c.path.name for c in candidates] == ["a.jpg"]


class TestDestinationSubpath:
    def test_default_template_is_year_then_year_month_day(self):
        result = destination_subpath(date(2024, 3, 5))
        assert result == destination_subpath(date(2024, 3, 5), DEFAULT_TEMPLATE)
        assert str(result) == os.path.join("2024", "2024-03-05")

    def test_custom_template_is_honored(self):
        result = destination_subpath(date(2024, 3, 5), "{YYYY}/{MM}")
        assert str(result) == os.path.join("2024", "03")

    def test_unknown_date_falls_back_to_collection_folder(self):
        result = destination_subpath(None)
        assert str(result) == UNKNOWN_DATE_FOLDER_NAME

    def test_single_level_template_without_separator(self):
        result = destination_subpath(date(2024, 3, 5), "{YYYY}")
        assert str(result) == "2024"


class TestImportCandidateIsImmutable:
    def test_is_a_frozen_dataclass(self, tmp_path):
        candidate = ImportCandidate(path=tmp_path / "a.jpg", date=date(2024, 1, 1))
        with pytest.raises(dataclasses.FrozenInstanceError):
            candidate.path = tmp_path / "b.jpg"
