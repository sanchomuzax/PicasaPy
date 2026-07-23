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


class TestEffektFulKulcsok190:
    """#190: a Picasa 3.9-es 4-5. effekt-fül VALÓDI mintái (a felhasználó
    Windows-os Picasájából, 2026-07-23). A kulcsok dekódolása:
    docs/specs/filters-decoded.md 5. kör. A round-trip elv szerint minden
    láncnak bitre pontosan meg kell őrződnie."""

    VALODI_MINTAK = [
        # 4. fül
        "IR=1,0.000000;",
        "Lomo=1,50.000000,0.000000;",
        "Holga=1,70.000000,30.000000,0.000000;",
        "HDR=1,20.000000,3.000000,0.000000;",
        "Cinemascope=1,0;",
        "Orton=1,25.000000,50.000000,0.000000;",
        "Sixties=1,20.000000,00ffffff,0;",
        "Invert=1;",
        "HeatMap=1,0.000000,0.000000;",
        "CrossProcess=1,0.000000;",
        "QuantizePalette=1,8.000000,80.000000,0.000000;",
        "TwoTone=1,0.000000,20.000000,0.000000,00004488,00ffff00;",
        # 5. fül
        "Boost=1,50.000000;",
        "Soften=1,50.000000,50.000000;",
        "Pixelate=1,20.000000,9.000000,0.000000;",
        "FocalZoom=1,0.500000,0.500000,50.000000,50.000000,50.000000,0.000000;",
        "PencilSketch=1,2.000000,100.000000,0.000000;",
        "Neon=1,0.000000,00ff0000;",
        "Comicize=1,20.000000,50.000000,50.000000;",
        "Border=1,20.000000,5.000000,0.000000,00000000,00ffffff,0.000000;",
        "DropShadow=1,4.000000,90.000000,10.000000,00000000,00ffffff,30.000000;",
        "MuseumMatte=1,25.000000,40.000000,001a0e03,00f0eae4;",
        "Polaroid=1,5.000000,00e2e2e2;",
    ]

    @pytest.mark.parametrize("value", VALODI_MINTAK)
    def test_roundtrip_exact(self, value):
        assert serialize_filters(parse_filters(value)) == value

    def test_mind_a_23_effekt_lefedve(self):
        assert len(self.VALODI_MINTAK) == 23
