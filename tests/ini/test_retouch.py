"""`picasapy.ini.retouch` — a retouch-régiók PicasaPy-saját kiterjesztésének
parse/build tesztjei (#148). A formátum kalibrálatlan (nincs valódi Picasa
golden retusált régióval) — a modul docsztringje ezt részletezi."""

from __future__ import annotations

import pytest

from picasapy.ini.filters import FilterOp, parse_filters, serialize_filters
from picasapy.ini.rect64 import Rect64
from picasapy.ini.retouch import build_retouch_op, parse_retouch_regions


class TestParseRetouchRegions:
    def test_puszta_retouch_ures_regio(self) -> None:
        """Valódi Picasa-eredetű `retouch=1;` — nincs régió-adat."""
        op = FilterOp("retouch", ("1",))
        assert parse_retouch_regions(op) == ()

    def test_egy_regio(self) -> None:
        op = FilterOp("retouch", ("1", "3f845bcb59418507"))
        regions = parse_retouch_regions(op)
        assert len(regions) == 1
        rect = regions[0]
        assert (rect.left, rect.top, rect.right, rect.bottom) == pytest.approx(
            (0.248108, 0.358566, 0.348648, 0.519638), abs=1e-5
        )

    def test_tobb_regio(self) -> None:
        op = FilterOp("retouch", ("1", "3f845bcb59418507", "10000000f1ddff49"))
        regions = parse_retouch_regions(op)
        assert len(regions) == 2

    def test_nem_retouch_bejegyzes_value_error(self) -> None:
        op = FilterOp("crop64", ("1", "3f845bcb59418507"))
        with pytest.raises(ValueError):
            parse_retouch_regions(op)

    def test_ervenytelen_rect64_felszall(self) -> None:
        op = FilterOp("retouch", ("1", "nemhex"))
        with pytest.raises(ValueError):
            parse_retouch_regions(op)


class TestBuildRetouchOp:
    def test_regio_nelkul_puszta_flag(self) -> None:
        op = build_retouch_op(())
        assert op == FilterOp("retouch", ("1",))

    def test_regiokkal_round_trip(self) -> None:
        regions = (
            Rect64(0.25, 0.25, 0.75, 0.75),
            Rect64(0.1, 0.1, 0.2, 0.2),
        )
        op = build_retouch_op(regions)
        parsed = parse_retouch_regions(op)
        assert len(parsed) == len(regions)
        for got, expected in zip(parsed, regions, strict=True):
            assert (got.left, got.top, got.right, got.bottom) == pytest.approx(
                (expected.left, expected.top, expected.right, expected.bottom),
                abs=1e-3,
            )

    def test_teljes_lanc_round_trip(self) -> None:
        """A build→serialize→parse→parse_retouch_regions lánc bitre
        egyezteti a régiókat (a filters= láncon keresztül is)."""
        regions = (Rect64(0.25, 0.25, 0.75, 0.75),)
        op = build_retouch_op(regions)
        chain_text = serialize_filters((op,))
        assert chain_text == "retouch=1,40004000c000c000;"
        parsed_ops = parse_filters(chain_text)
        assert parse_retouch_regions(parsed_ops[0]) == pytest.approx(
            regions, abs=1e-4
        )
