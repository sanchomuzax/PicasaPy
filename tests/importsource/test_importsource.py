"""Egységteszt: `picasapy.importsource` (#23) — forrás-beolvasás és a
mappa-sablon szerinti cél-alútvonal, tiszta Python (Qt/GUI nélkül).

Peremesetek: hiányzó EXIF-dátum → mtime-visszaesés, teljesen ismeretlen
dátum (sem EXIF, sem statolható mtime), egyéni sablon, üres/hiányzó forrás.
"""

import dataclasses
import os
from datetime import date
from pathlib import Path

import pytest

from picasapy.importsource import (
    DEFAULT_TEMPLATE,
    MEDIA_FILTER_ALL,
    MEDIA_FILTER_PICTURES,
    MEDIA_FILTER_PICTURES_AND_MOVIES,
    NAMING_BY_DATE,
    NAMING_MANUAL,
    NAMING_TODAY,
    UNKNOWN_DATE_FOLDER_NAME,
    ImportCandidate,
    destination_subpath,
    destination_subpath_for_mode,
    duplicate_paths,
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


class TestDestinationSubpathForMode:
    """#441 — a HÁROM célmappa-elnevezési mód célútvonal-számítása."""

    def test_manual_mode_uses_the_given_name_for_every_date(self):
        result = destination_subpath_for_mode(
            date(2024, 3, 5), NAMING_MANUAL, manual_name="Nyaralás"
        )
        assert str(result) == "Nyaralás"

    def test_manual_mode_ignores_the_candidate_date(self):
        with_date = destination_subpath_for_mode(
            date(2024, 3, 5), NAMING_MANUAL, manual_name="Album"
        )
        without_date = destination_subpath_for_mode(
            None, NAMING_MANUAL, manual_name="Album"
        )
        assert with_date == without_date == Path("Album")

    def test_manual_mode_blank_name_falls_back_to_destination_root(self):
        result = destination_subpath_for_mode(
            date(2024, 3, 5), NAMING_MANUAL, manual_name="   "
        )
        assert result == Path(".")

    def test_by_date_mode_splits_into_one_folder_per_date(self):
        first = destination_subpath_for_mode(date(2024, 3, 5), NAMING_BY_DATE)
        second = destination_subpath_for_mode(date(2024, 3, 6), NAMING_BY_DATE)
        assert str(first) == "2024-03-05"
        assert str(second) == "2024-03-06"
        assert first != second

    def test_by_date_mode_unknown_date_falls_back_to_collection_folder(self):
        result = destination_subpath_for_mode(None, NAMING_BY_DATE)
        assert str(result) == UNKNOWN_DATE_FOLDER_NAME

    def test_today_mode_uses_a_single_folder_for_every_candidate(self):
        today = date(2024, 6, 1)
        with_date = destination_subpath_for_mode(
            date(2024, 3, 5), NAMING_TODAY, today=today
        )
        without_date = destination_subpath_for_mode(None, NAMING_TODAY, today=today)
        assert with_date == without_date == Path("2024-06-01")

    def test_unknown_mode_raises(self):
        with pytest.raises(ValueError):
            destination_subpath_for_mode(date(2024, 1, 1), "nem-letezik")


class TestDuplicatePaths:
    """#441 — "Exclude Duplicates": a jelöltek közül azok, amik tartalma
    megegyezik egy már indexelt (könyvtárbeli) fájléval."""

    def test_identical_content_is_flagged_as_duplicate(self, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        library = tmp_path / "konyvtar"
        library.mkdir()
        make_jpeg(source / "a.jpg", size=(64, 64))
        make_jpeg(library / "a.jpg", size=(64, 64))
        candidates = scan_source(source)

        result = duplicate_paths(candidates, [library / "a.jpg"])

        assert result == frozenset({source / "a.jpg"})

    def test_different_content_is_not_a_duplicate(self, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        library = tmp_path / "konyvtar"
        library.mkdir()
        make_jpeg(source / "a.jpg", size=(64, 64))
        make_jpeg(library / "other.jpg", size=(32, 32))
        candidates = scan_source(source)

        result = duplicate_paths(candidates, [library / "other.jpg"])

        assert result == frozenset()

    def test_empty_library_has_no_duplicates(self, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        make_jpeg(source / "a.jpg")
        candidates = scan_source(source)

        assert duplicate_paths(candidates, []) == frozenset()

    def test_only_the_duplicate_candidate_is_flagged(self, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        library = tmp_path / "konyvtar"
        library.mkdir()
        make_jpeg(source / "a.jpg", size=(64, 64))  # duplikátum lesz
        make_jpeg(source / "b.jpg", size=(48, 48))  # egyedi
        make_jpeg(library / "a.jpg", size=(64, 64))
        candidates = scan_source(source)

        result = duplicate_paths(candidates, [library / "a.jpg"])

        assert result == frozenset({source / "a.jpg"})


class TestMediaFilter:
    """#441: a forrás-tallózó három fájltípus-szűrője — nálunk a forrás
    mindig mappa, ezért a fokozatok a BEOLVASÁSRA vonatkoznak."""

    def _source(self, tmp_path):
        source = tmp_path / "kartya"
        source.mkdir()
        (source / "kep.jpg").write_bytes(b"\xff\xd8\xff")
        (source / "film.avi").write_bytes(b"RIFF")
        (source / "nyers.cr2").write_bytes(b"II*")
        (source / "szoveg.txt").write_text("nem media", encoding="utf-8")
        return source

    def test_pictures_and_movies_is_the_default(self, tmp_path):
        source = self._source(tmp_path)

        names = {c.path.name for c in scan_source(str(source))}

        assert names == {"kep.jpg", "film.avi", "nyers.cr2"}

    def test_pictures_only_leaves_the_movie_out(self, tmp_path):
        source = self._source(tmp_path)

        names = {
            c.path.name
            for c in scan_source(str(source), MEDIA_FILTER_PICTURES)
        }

        assert names == {"kep.jpg", "nyers.cr2"}

    def test_a_non_media_file_is_never_a_candidate(self, tmp_path):
        source = self._source(tmp_path)

        for mode in (
            MEDIA_FILTER_ALL,
            MEDIA_FILTER_PICTURES_AND_MOVIES,
            MEDIA_FILTER_PICTURES,
        ):
            names = {c.path.name for c in scan_source(str(source), mode)}
            assert "szoveg.txt" not in names

    def test_an_unknown_filter_falls_back_to_the_default(self, tmp_path):
        source = self._source(tmp_path)

        names = {c.path.name for c in scan_source(str(source), "nincs-ilyen")}

        assert names == {"kep.jpg", "film.avi", "nyers.cr2"}
