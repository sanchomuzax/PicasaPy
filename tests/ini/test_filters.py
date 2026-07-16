"""filters= lánc parse/serialize — spec: docs/specs/picasa-ini-format.md."""

import pytest

from picasapy.ini import FilterOp, parse_filters, serialize_filters

SPEC_CHAIN = (
    "enhance=1;crop64=1,45930000ba03defe;"
    "finetune2=1,0.333333,0.176842,0.193684,00000000,0.000000;"
)


class TestParse:
    def test_single_filter(self):
        ops = parse_filters("sat=1,-1.000000;")
        assert len(ops) == 1
        assert ops[0].name == "sat"
        assert ops[0].params == ("1", "-1.000000")

    def test_chain_order_preserved(self):
        ops = parse_filters(SPEC_CHAIN)
        assert [op.name for op in ops] == ["enhance", "crop64", "finetune2"]

    def test_float_params_signed(self):
        # Élesben negatív értékek is előfordulnak (tilt, finetune2 utolsó param).
        ops = parse_filters("tilt=1,-0.114659,0.000000;")
        assert ops[0].float_params() == pytest.approx((-0.114659, 0.0))

    def test_uppercase_vignette_name_preserved_and_matches(self):
        # A parser kis-nagybetű-tűrő, de round-triphez a névalak megőrzendő.
        ops = parse_filters("Vignette=1,0.500000,0.500000;")
        assert ops[0].name == "Vignette"
        assert ops[0].matches("vignette")
        assert ops[0].matches("VIGNETTE")

    def test_unknown_filter_kept(self):
        ops = parse_filters("futurefilter=1,1,2,3;")
        assert ops[0].name == "futurefilter"
        assert ops[0].params == ("1", "1", "2", "3")

    def test_empty_string(self):
        assert parse_filters("") == ()

    def test_missing_trailing_semicolon_tolerated(self):
        assert parse_filters("sat=1,-1.0") == parse_filters("sat=1,-1.0;")

    @pytest.mark.parametrize("bad", ["noequals;", ";=1;"])
    def test_malformed_raises(self, bad):
        with pytest.raises(ValueError):
            parse_filters(bad)


class TestSerialize:
    @pytest.mark.parametrize(
        "value",
        [
            "sat=1,-1.000000;",
            SPEC_CHAIN,
            "Vignette=1,0.500000,0.500000;",
            "fill=1,0.308411;",
        ],
    )
    def test_roundtrip_exact(self, value):
        assert serialize_filters(parse_filters(value)) == value

    def test_serialize_from_ops(self):
        ops = (FilterOp("enhance", ("1",)), FilterOp("sat", ("1", "0.500000")))
        assert serialize_filters(ops) == "enhance=1;sat=1,0.500000;"


class TestImmutability:
    def test_filterop_is_frozen(self):
        op = FilterOp("sat", ("1", "0.5"))
        with pytest.raises(AttributeError):
            op.name = "bw"
