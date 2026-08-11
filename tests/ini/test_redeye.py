"""A `redeye=` bejegyzés kézi régióinak kódolása/olvasása (#445)."""

import pytest

from picasapy.ini.filters import FilterOp, parse_filters, serialize_filters
from picasapy.ini.rect64 import Rect64
from picasapy.ini.redeye import (
    REDEYE_FILTER_NAME,
    build_redeye_op,
    parse_redeye_regions,
)


class TestBuildRedeyeOp:
    def test_no_regions_is_byte_identical_to_picasa(self):
        """Kézi régió nélkül a bejegyzés bájtra a valódi Picasa alakja."""
        op = build_redeye_op(())
        assert serialize_filters((op,)) == "redeye=1;"

    def test_regions_are_appended_after_the_flag(self):
        op = build_redeye_op(
            (Rect64(left=0.25, top=0.25, right=0.5, bottom=0.5),)
        )
        assert op.name == REDEYE_FILTER_NAME
        assert op.params[0] == "1"
        assert len(op.params) == 2


class TestParseRedeyeRegions:
    def test_plain_picasa_entry_has_no_regions(self):
        (op,) = parse_filters("redeye=1;")
        assert parse_redeye_regions(op) == ()

    def test_round_trip(self):
        regions = (
            Rect64(left=0.25, top=0.25, right=0.5, bottom=0.5),
            Rect64(left=0.6, top=0.1, right=0.75, bottom=0.3),
        )
        value = serialize_filters((build_redeye_op(regions),))
        (op,) = parse_filters(value)
        decoded = parse_redeye_regions(op)
        assert len(decoded) == 2
        for original, result in zip(regions, decoded, strict=True):
            assert result.left == pytest.approx(original.left, abs=1e-4)
            assert result.top == pytest.approx(original.top, abs=1e-4)
            assert result.right == pytest.approx(original.right, abs=1e-4)
            assert result.bottom == pytest.approx(original.bottom, abs=1e-4)

    def test_wrong_filter_name_raises(self):
        with pytest.raises(ValueError):
            parse_redeye_regions(FilterOp("retouch", ("1",)))

    def test_invalid_rect_raises(self):
        with pytest.raises(ValueError):
            parse_redeye_regions(FilterOp("redeye", ("1", "nem-rect64")))
