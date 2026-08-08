"""#448: egyéni vágás-képarányok — `custom_aspect_ratios.py` tiszta
függvényei (JSON parse/serialize, felvétel, törlés), Qt nélkül."""

from __future__ import annotations

from picasapy.app.custom_aspect_ratios import (
    CustomAspectRatio,
    add_custom_aspect_ratio,
    delete_custom_aspect_ratio,
    parse_custom_aspect_ratios,
    serialize_custom_aspect_ratios,
)


class TestParseRoundTrip:
    def test_empty_or_missing_raw_yields_empty_tuple(self):
        assert parse_custom_aspect_ratios(None) == ()
        assert parse_custom_aspect_ratios("") == ()

    def test_garbage_json_yields_empty_tuple(self):
        assert parse_custom_aspect_ratios("nem json{{{") == ()

    def test_non_list_json_yields_empty_tuple(self):
        assert parse_custom_aspect_ratios('{"name": "x"}') == ()

    def test_round_trip_preserves_name_and_dimensions(self):
        ratios = (
            CustomAspectRatio(name="Small print", width=4, height=6),
            CustomAspectRatio(name="Panorama", width=16.5, height=5.25),
        )
        raw = serialize_custom_aspect_ratios(ratios)
        assert parse_custom_aspect_ratios(raw) == ratios

    def test_malformed_items_are_skipped_not_fatal(self):
        raw = (
            '[{"name": "OK", "width": 4, "height": 6}, "nem-dict", '
            '{"width": 4, "height": 6}, {"name": "  ", "width": 4, "height": 6}, '
            '{"name": "NoDims"}, '
            '{"name": "Negative", "width": -1, "height": 6}, '
            '{"name": "ZeroHeight", "width": 4, "height": 0}, '
            '{"name": "StringDims", "width": "4", "height": "6"}]'
        )
        result = parse_custom_aspect_ratios(raw)
        assert result == (CustomAspectRatio(name="OK", width=4.0, height=6.0),)


class TestAddCustomAspectRatio:
    def test_adds_new_ratio(self):
        result = add_custom_aspect_ratio((), 4, 6, "Small print")
        assert result == (CustomAspectRatio(name="Small print", width=4, height=6),)

    def test_strips_whitespace_from_name(self):
        result = add_custom_aspect_ratio((), 4, 6, "  Small print  ")
        assert result[0].name == "Small print"

    def test_blank_name_is_rejected(self):
        assert add_custom_aspect_ratio((), 4, 6, "   ") == ()

    def test_zero_or_negative_width_is_rejected(self):
        assert add_custom_aspect_ratio((), 0, 6, "X") == ()
        assert add_custom_aspect_ratio((), -4, 6, "X") == ()

    def test_zero_or_negative_height_is_rejected(self):
        assert add_custom_aspect_ratio((), 4, 0, "X") == ()
        assert add_custom_aspect_ratio((), 4, -6, "X") == ()

    def test_non_numeric_dimensions_are_rejected(self):
        assert add_custom_aspect_ratio((), "négy", 6, "X") == ()

    def test_exact_duplicate_is_not_added_twice(self):
        existing = (CustomAspectRatio(name="Small print", width=4, height=6),)
        result = add_custom_aspect_ratio(existing, 4, 6, "Small print")
        assert result == existing

    def test_same_name_different_dimensions_is_allowed(self):
        existing = (CustomAspectRatio(name="Print", width=4, height=6),)
        result = add_custom_aspect_ratio(existing, 5, 7, "Print")
        assert result == (
            CustomAspectRatio(name="Print", width=4, height=6),
            CustomAspectRatio(name="Print", width=5, height=7),
        )

    def test_appends_after_existing(self):
        existing = (CustomAspectRatio(name="A", width=1, height=1),)
        result = add_custom_aspect_ratio(existing, 2, 3, "B")
        assert result == (
            CustomAspectRatio(name="A", width=1, height=1),
            CustomAspectRatio(name="B", width=2, height=3),
        )


class TestDeleteCustomAspectRatio:
    def test_removes_matching_entry(self):
        existing = (
            CustomAspectRatio(name="A", width=1, height=1),
            CustomAspectRatio(name="B", width=2, height=3),
        )
        result = delete_custom_aspect_ratio(existing, "A", 1, 1)
        assert result == (CustomAspectRatio(name="B", width=2, height=3),)

    def test_non_matching_name_is_noop(self):
        existing = (CustomAspectRatio(name="A", width=1, height=1),)
        assert delete_custom_aspect_ratio(existing, "nincs-ilyen", 1, 1) == existing

    def test_matching_name_but_different_dimensions_is_noop(self):
        existing = (CustomAspectRatio(name="A", width=1, height=1),)
        assert delete_custom_aspect_ratio(existing, "A", 9, 9) == existing

    def test_only_removes_the_matching_duplicate_name(self):
        existing = (
            CustomAspectRatio(name="Print", width=4, height=6),
            CustomAspectRatio(name="Print", width=5, height=7),
        )
        result = delete_custom_aspect_ratio(existing, "Print", 4, 6)
        assert result == (CustomAspectRatio(name="Print", width=5, height=7),)
