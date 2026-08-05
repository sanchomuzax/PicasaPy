"""`picasapy.ini.text_overlay` — a `text=`/`textactive=` kulcsok típusos
parse/serialize tesztjei (#148). A `raw_x`/`raw_y` mezők jelentése
megerősítetlen — a modul docsztringje részletezi; a tesztek a MEZŐ-
SZÉTBONTÁST és a PicasaPy-eredetű round-tripet ellenőrzik."""

from __future__ import annotations

import pytest

from picasapy.ini.text_overlay import (
    TextOverlay,
    parse_text,
    parse_text_active,
    serialize_text,
    serialize_text_active,
)


class TestParseText:
    def test_dokumentalt_pelda_mezoi(self) -> None:
        """A spec (`docs/specs/picasa-ini-format.md`) rövidített példája:
        `text=1; 136;11;sample text;Aharoni;...` — a mezők kiolvasása."""
        overlay = parse_text("1; 136;11;sample text;Aharoni;...")
        assert overlay.enabled is True
        assert overlay.raw_x == 136
        assert overlay.raw_y == 11
        assert overlay.content == "sample text"
        assert overlay.font == "Aharoni"
        assert overlay.raw_tail == "..."

    def test_farok_nelkuli_alak(self) -> None:
        overlay = parse_text("1;0;0;szöveg;Arial")
        assert overlay.raw_tail == ""

    def test_kikapcsolt_flag(self) -> None:
        overlay = parse_text("0;0;0;;Arial")
        assert overlay.enabled is False
        assert overlay.content == ""

    def test_tul_keves_mezo_value_error(self) -> None:
        with pytest.raises(ValueError):
            parse_text("1;0;0")

    def test_nem_szam_x_value_error(self) -> None:
        with pytest.raises(ValueError):
            parse_text("1;abc;0;szöveg;Arial")


class TestSerializeText:
    def test_round_trip_farok_nelkul(self) -> None:
        overlay = TextOverlay(
            enabled=True, raw_x=50, raw_y=20, content="Nyár 2026", font="Tahoma"
        )
        text = serialize_text(overlay)
        assert parse_text(text) == overlay

    def test_round_trip_farokkal(self) -> None:
        overlay = TextOverlay(
            enabled=True,
            raw_x=136,
            raw_y=11,
            content="sample text",
            font="Aharoni",
            raw_tail="...",
        )
        text = serialize_text(overlay)
        assert text == "1;136;11;sample text;Aharoni;..."
        assert parse_text(text) == overlay

    def test_kikapcsolt_flag_nullat_ir(self) -> None:
        overlay = TextOverlay(
            enabled=False, raw_x=0, raw_y=0, content="", font="Arial"
        )
        assert serialize_text(overlay).startswith("0;")


class TestTextActive:
    def test_parse_1_aktiv(self) -> None:
        assert parse_text_active("1") is True

    def test_parse_0_inaktiv(self) -> None:
        assert parse_text_active("0") is False

    def test_parse_ures_inaktiv(self) -> None:
        assert parse_text_active("") is False

    def test_serialize_round_trip(self) -> None:
        assert parse_text_active(serialize_text_active(True)) is True
        assert parse_text_active(serialize_text_active(False)) is False
