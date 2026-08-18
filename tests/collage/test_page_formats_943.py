"""#943: a kollázs Oldalformátum-listája (`collage/page_formats.py`).

A lista forrása a `docs/specs/picasa-kollazs-felulet.md` 7. szakasza — a
menüépítő függvényből kiolvasott arányokkal. A teszt azt őrzi, hogy a
kulcsok és az arányok ne csússzanak el: egy elrontott arány a lap alakját
rontja el, és a `.cxf` is rossz `format`-tal menne ki.
"""

from __future__ import annotations

import pytest

from picasapy.collage.page_formats import (
    DEFAULT_FORMAT_KEY,
    PAGE_FORMATS,
    PageFormat,
    format_for,
    page_ratio,
)


class TestList:
    def test_kulcsok_a_specifikacio_sorrendjeben(self):
        kulcsok = tuple(f.key for f in PAGE_FORMATS)
        assert kulcsok == (
            "Manual",
            "5x8m",
            "9x13m",
            "10x15m",
            "Crop13x18m",
            "Crop20x25m",
            "A4",
            "4x6",
            "5x7",
            "FullPage",
            "8x10",
            "A4PageCollage",
            "Square",
            "Desktop4x3",
            "Widescreen",
            "HDTV16x9",
            "WideFrame",
            "CurrentDisplay",
        )

    def test_az_alapertelmezes_a_4_3(self):
        # `picasa-create-features.md` 1.9.11: „collage::format … 4:3"
        assert DEFAULT_FORMAT_KEY == "Desktop4x3"
        assert format_for(DEFAULT_FORMAT_KEY).long == 4

    def test_ismeretlen_kulcs_hibat_dob(self):
        with pytest.raises(ValueError):
            format_for("nincs_ilyen")

    def test_a_hosszabb_oldal_sosem_kisebb_a_rovidnel(self):
        for fmt in PAGE_FORMATS:
            if fmt.long is None:
                continue
            assert fmt.long >= fmt.short, fmt.key


class TestRatio:
    def test_fekvo_es_allo_egymas_reciproka(self):
        fekvo = page_ratio("10x15m", "landscape")
        allo = page_ratio("10x15m", "portrait")
        assert fekvo == pytest.approx(10 / 15)
        assert allo == pytest.approx(15 / 10)

    def test_negyzet_mindket_tajolasban_egy(self):
        assert page_ratio("Square", "landscape") == pytest.approx(1.0)
        assert page_ratio("Square", "portrait") == pytest.approx(1.0)

    def test_a_kepernyo_formatum_a_kepernyo_aranyat_adja(self):
        # a „Jelenlegi megjelenítés" a tájolást FIGYELMEN KÍVÜL hagyja
        assert page_ratio(
            "CurrentDisplay", "portrait", screen_ratio=9 / 16
        ) == pytest.approx(9 / 16)

    def test_a_manual_a_jelenlegi_aranyt_tartja(self):
        assert page_ratio("Manual", "landscape", current_ratio=0.5) == 0.5

    def test_ismeretlen_tajolas_hibat_dob(self):
        with pytest.raises(ValueError):
            page_ratio("Square", "diagonal")


class TestPageFormat:
    def test_a_leiro_rekord_ertekei(self):
        fmt = format_for("A4")
        assert isinstance(fmt, PageFormat)
        assert (fmt.long, fmt.short) == (297, 210)
