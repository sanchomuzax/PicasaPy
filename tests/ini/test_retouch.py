"""`picasapy.ini.retouch` — a retouch-régiók PicasaPy-saját kiterjesztésének
parse/build tesztjei (#148). A formátum kalibrálatlan (nincs valódi Picasa
golden retusált régióval) — a modul docsztringje ezt részletezi."""

from __future__ import annotations

import pytest

from picasapy.ini.filters import FilterOp, parse_filters, serialize_filters
from picasapy.ini.rect64 import Rect64
from picasapy.ini.retouch import (
    RetouchPatch,
    build_retouch_op,
    build_retouch_patches_op,
    decode_patch,
    encode_patch,
    parse_retouch_patches,
    parse_retouch_regions,
)


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

    def test_v2_bejegyzesnel_v1_olvaso_ures_tuplet_ad(self) -> None:
        """Backward-kompat: egy v2 (folt-alapú) bejegyzést a v1 (régiós)
        olvasó NEM próbálja rect64-ként dekódolni — üres tuple-t ad."""
        patch = RetouchPatch(0.25, 0.25, 0.5, 0.5, 0.05)
        op = build_retouch_patches_op((patch,))
        assert parse_retouch_regions(op) == ()


class TestPatchEncoding:
    """#445: `RetouchPatch` 20 hex jegyű kódolása — a `rect64` mintáját
    követi, eggyel több mezővel (target_x, target_y, source_x, source_y,
    radius)."""

    def test_kerek_ertekek_round_trip(self) -> None:
        patch = RetouchPatch(
            target_x=0.25, target_y=0.5, source_x=0.75, source_y=0.1, radius=0.05
        )
        encoded = encode_patch(patch)
        assert len(encoded) == 20
        decoded = decode_patch(encoded)
        assert (
            decoded.target_x,
            decoded.target_y,
            decoded.source_x,
            decoded.source_y,
            decoded.radius,
        ) == pytest.approx(
            (patch.target_x, patch.target_y, patch.source_x, patch.source_y, patch.radius),
            abs=1e-3,
        )

    def test_hatarertekek_nem_dobnak(self) -> None:
        patch = RetouchPatch(0.0, 0.0, 1.0, 1.0, 0.0)
        decoded = decode_patch(encode_patch(patch))
        assert decoded.target_x == pytest.approx(0.0, abs=1e-4)
        assert decoded.source_x == pytest.approx(1.0, abs=1e-3)

    def test_tartomanyon_kivuli_koordinata_value_error(self) -> None:
        patch = RetouchPatch(1.5, 0.0, 0.0, 0.0, 0.0)
        with pytest.raises(ValueError):
            encode_patch(patch)

    def test_ervenytelen_hex_value_error(self) -> None:
        with pytest.raises(ValueError):
            decode_patch("nemhex")


class TestParseRetouchPatches:
    def test_puszta_retouch_ures_folt(self) -> None:
        """Valódi Picasa-eredetű `retouch=1;` — a v2 olvasó is üres tuple-t ad."""
        op = FilterOp("retouch", ("1",))
        assert parse_retouch_patches(op) == ()

    def test_v1_bejegyzesnel_ures_tuplet_ad(self) -> None:
        """Egy korábbi PicasaPy-verzió v1 (régiós) bejegyzését a v2 (folt-
        alapú) olvasó NEM próbálja patch-ként dekódolni."""
        op = FilterOp("retouch", ("1", "3f845bcb59418507"))
        assert parse_retouch_patches(op) == ()

    def test_egy_folt(self) -> None:
        patch = RetouchPatch(0.25, 0.25, 0.5, 0.5, 0.05)
        op = build_retouch_patches_op((patch,))
        patches = parse_retouch_patches(op)
        assert len(patches) == 1
        assert (patches[0].target_x, patches[0].target_y) == pytest.approx(
            (0.25, 0.25), abs=1e-3
        )

    def test_tobb_folt(self) -> None:
        patches_in = (
            RetouchPatch(0.1, 0.1, 0.2, 0.2, 0.02),
            RetouchPatch(0.8, 0.8, 0.6, 0.6, 0.05),
        )
        op = build_retouch_patches_op(patches_in)
        assert len(parse_retouch_patches(op)) == 2

    def test_nem_retouch_bejegyzes_value_error(self) -> None:
        op = FilterOp("crop64", ("2", "40004000800080000ccd"))
        with pytest.raises(ValueError):
            parse_retouch_patches(op)

    def test_ervenytelen_patch_felszall(self) -> None:
        op = FilterOp("retouch", ("2", "nemhex"))
        with pytest.raises(ValueError):
            parse_retouch_patches(op)

    def test_teljes_lanc_round_trip(self) -> None:
        """A build→serialize→parse→parse_retouch_patches lánc a filters=
        láncon keresztül is bitre egyezteti a foltokat."""
        patches = (RetouchPatch(0.25, 0.25, 0.75, 0.75, 0.1),)
        op = build_retouch_patches_op(patches)
        chain_text = serialize_filters((op,))
        assert chain_text.startswith("retouch=2,")
        parsed_ops = parse_filters(chain_text)
        parsed = parse_retouch_patches(parsed_ops[0])
        assert len(parsed) == 1
        assert (
            parsed[0].target_x,
            parsed[0].target_y,
            parsed[0].source_x,
            parsed[0].source_y,
            parsed[0].radius,
        ) == pytest.approx(
            (0.25, 0.25, 0.75, 0.75, 0.1), abs=1e-3
        )
