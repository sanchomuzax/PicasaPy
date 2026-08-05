"""Név-alapú szkenner-kizárólista (#349, Picasa filters.txt mintája)."""

from picasapy.scanner.name_filters import (
    DEFAULT_DIRECTORY_FILTERS,
    NameFilters,
    default_name_filters,
)


class TestDefaultNameFilters:
    def test_default_directory_filters_match_original_picasa(self):
        assert set(DEFAULT_DIRECTORY_FILTERS) >= {
            "windows",
            "winnt",
            "temp",
            "Program Files",
            "Originals",
            ".picasaoriginals",
        }

    def test_default_includes_and_file_filters_empty(self):
        filters = default_name_filters()
        assert filters.directory_includes == ()
        assert filters.file_filters == ()
        assert filters.file_includes == ()


class TestDirectoryExclusionCaseInsensitive:
    def test_excludes_exact_case(self):
        filters = default_name_filters()
        assert filters.is_directory_excluded("Originals")

    def test_excludes_lowercase_variant(self):
        filters = default_name_filters()
        assert filters.is_directory_excluded("originals")

    def test_excludes_uppercase_variant(self):
        filters = default_name_filters()
        assert filters.is_directory_excluded("ORIGINALS")

    def test_excludes_mixed_case_multi_word(self):
        filters = default_name_filters()
        assert filters.is_directory_excluded("program files")
        assert filters.is_directory_excluded("PROGRAM FILES")

    def test_excludes_dot_picasaoriginals(self):
        filters = default_name_filters()
        assert filters.is_directory_excluded(".picasaoriginals")
        assert filters.is_directory_excluded(".PicasaOriginals")


class TestDirectoryExclusionIsNameBasedNotSubstring:
    def test_does_not_exclude_name_containing_filter_as_substring(self):
        filters = default_name_filters()
        # "Temp Munkak" a NEVÉBEN tartalmazza a "temp"-et, de nem egyezik
        # vele teljesen — ez valódi fotómappa lehet, nem zárható ki.
        assert not filters.is_directory_excluded("Temp Munkak")
        assert not filters.is_directory_excluded("mywindows")
        assert not filters.is_directory_excluded("Originals2024")

    def test_unrelated_names_not_excluded(self):
        filters = default_name_filters()
        assert not filters.is_directory_excluded("nyaralas")
        assert not filters.is_directory_excluded("telek")


class TestIncludesOverrideFilters:
    def test_directory_include_overrides_matching_filter(self):
        filters = NameFilters(
            directory_filters=("Originals",),
            directory_includes=("Originals",),
        )
        assert not filters.is_directory_excluded("Originals")

    def test_directory_include_is_case_insensitive(self):
        filters = NameFilters(
            directory_filters=("Originals",),
            directory_includes=("originals",),
        )
        assert not filters.is_directory_excluded("ORIGINALS")

    def test_file_include_overrides_matching_file_filter(self):
        filters = NameFilters(
            file_filters=("desktop.ini",),
            file_includes=("desktop.ini",),
        )
        assert not filters.is_file_excluded("desktop.ini")

    def test_include_does_not_affect_unrelated_filter_entries(self):
        filters = NameFilters(
            directory_filters=("Originals", "temp"),
            directory_includes=("Originals",),
        )
        assert not filters.is_directory_excluded("Originals")
        assert filters.is_directory_excluded("temp")


class TestFileExclusion:
    def test_empty_file_filters_excludes_nothing(self):
        filters = default_name_filters()
        assert not filters.is_file_excluded("desktop.ini")

    def test_custom_file_filter_matches_case_insensitively(self):
        filters = NameFilters(file_filters=("Thumbs.db",))
        assert filters.is_file_excluded("thumbs.db")
        assert filters.is_file_excluded("THUMBS.DB")


class TestImmutability:
    def test_name_filters_is_frozen(self):
        import pytest

        filters = default_name_filters()
        with pytest.raises(AttributeError):
            filters.directory_filters = ()
