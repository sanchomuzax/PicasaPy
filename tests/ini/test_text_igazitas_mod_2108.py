"""#2108 — a `text=` stílus 8. mezője HÁROM rész, és mind eljut a fájlig.

## A mérés forrása

`docs/specs/picasa-ini-format.md` → „A 8. MEZŐ MINDHÁROM RÉSZE" (2026-09-05).
Nem minta-illesztés: az olvasó (`0x00a4dd50`) három külön beállítóhoz vágja
a mezőt, és az `edittextpanel` kezelője megmondja, melyik mit jelent.

| rész | jelentés | értékkészlet |
|---|---|---|
| bit 8–15 | vízszintes igazítás | 0 = bal · 1 = közép · 2 = jobb |
| bit 0–7 | kitöltés/körvonal mód | 0 = csak kitöltés · 1 = nincs kitöltés · 2 = mindkettő |
| bit 16–31 | a panel NULLÁZZA (`[vtbl+0x48]` konstans 0) |

A **mód nem szabad érték**: a panel minden hívásnál újraszámolja
(`0x0063045a`–`0x006304a9`) — `no_fill` bepipálva → **1**; különben a
körvonalvastagság pontosan 0,0 → **0**; egyébként → **2**. A `no_fill` ága
**ELŐBBRE való**, tehát vastag körvonal mellett is lehet a mód 1.
"""

from __future__ import annotations

import pytest

from picasapy.ini.text_overlay import (
    TextStyle,
    alignment_code,
    alignment_name,
    fill_mode_from,
    parse_text,
    serialize_text,
)

#: A binárisból mért öt minta (a spec táblája), plusz a régi korpusz kettője.
MERT_MINTAK = (
    # (8. mező, igazítás, mód, honnan)
    (0x100, 1, 0, "A — Arial, 1 sor"),
    (0x100, 1, 0, "B — Arial Black, forgatott"),
    (0x200, 2, 0, "C — Arial, 3 sor"),
    (0x202, 2, 2, "D — Arial Black, 3 sor"),
    (0x101, 1, 1, "E — Arial Black, 1 sor"),
    (0x102, 1, 2, "régi korpusz"),
    (0x000, 0, 0, "régi korpusz"),
)


class TestAHaromResz:
    @pytest.mark.parametrize(
        ("mezo", "igazitas", "mod", "honnan"),
        MERT_MINTAK,
        ids=[m[3] for m in MERT_MINTAK],
    )
    def test_a_mert_mintak_szetesnek(self, mezo, igazitas, mod, honnan):
        stilus = TextStyle(fill_argb=0, outline_argb=0, layout_field=mezo)
        assert stilus.alignment == igazitas, honnan
        assert stilus.fill_mode == mod, honnan

    def test_a_felso_16_bit_kulon_all(self):
        """A panel nullázza, de ha egy fájlban mégis áll, meg kell őrizni."""
        stilus = TextStyle(fill_argb=0, outline_argb=0, layout_field=0x0007_0102)
        assert stilus.alignment == 1
        assert stilus.fill_mode == 2


class TestAzIgazitasNevei:
    @pytest.mark.parametrize(
        ("kod", "nev"), [(0, "left"), (1, "center"), (2, "right")]
    )
    def test_oda_vissza(self, kod, nev):
        assert alignment_name(kod) == nev
        assert alignment_code(nev) == kod

    def test_ismeretlen_kod_BALRA_esik(self):
        """Sérült fájl ne dobjon kivételt a szerkesztő megnyitásakor."""
        assert alignment_name(7) == "left"

    def test_ismeretlen_nev_BALRA_esik(self):
        assert alignment_code("justify") == 0


class TestAModLEVEZETESE:
    """A három ág — a `no_fill` ELŐBBRE való (`0x0063046a`)."""

    def test_no_fill_nelkul_es_nulla_vastagsaggal_0(self):
        assert fill_mode_from(no_fill=False, outline_width=0.0) == 0

    def test_no_fill_bepipalva_1(self):
        assert fill_mode_from(no_fill=True, outline_width=0.0) == 1

    def test_kitoltes_es_korvonal_2(self):
        assert fill_mode_from(no_fill=False, outline_width=0.5) == 2

    def test_a_no_fill_VASTAG_korvonal_mellett_is_1(self):
        """A jegy kiemelt esete: a sorrend miatt a 2 NEM nyer."""
        assert fill_mode_from(no_fill=True, outline_width=0.9) == 1


class TestAzIras:
    def test_a_felso_16_bitet_VALTOZATLANUL_viszi(self):
        """Nem újraépítjük a mezőt: a fel nem tárt biteket megőrizzük — a
        `with_style_flags` (#2448) mintájára."""
        stilus = TextStyle(fill_argb=0, outline_argb=0, layout_field=0x00AB_0000)
        uj = stilus.with_text_layout(alignment=2, fill_mode=1)
        assert uj.layout_field == 0x00AB_0201

    def test_csak_az_also_16_bitet_irja_at(self):
        stilus = TextStyle(fill_argb=0, outline_argb=0, layout_field=0x0102)
        assert stilus.with_text_layout(alignment=0, fill_mode=0).layout_field == 0

    @pytest.mark.parametrize("igazitas", [0, 1, 2])
    @pytest.mark.parametrize("mod", [0, 1, 2])
    def test_oda_vissza_minden_parositasra(self, igazitas, mod):
        stilus = TextStyle(fill_argb=0, outline_argb=0).with_text_layout(
            alignment=igazitas, fill_mode=mod
        )
        assert (stilus.alignment, stilus.fill_mode) == (igazitas, mod)


class TestABajtazonossag:
    """A legerősebb állítás: a valódi sorok bitre azonosan mennek vissza."""

    GOLDENEK = (
        "1;161;19;Boldog Karácsonyt!;Bickham Script Pro Regular;"
        "0.023961,0.841368,0.100000,0.000000;"
        "v1,4294899423,4278190080,128.000000,1.000000,0.000000,1.000000,700,0,49152;;",
        "2;187;63;Kellemes karácsonyi ünnepeket és&#010;boldog újévet kívánunk!;Arial;"
        "0.105605,0.008726,0.059259,-4.712389;"
        "v1,4292215592,4293454056,128.000000,1.000000,0.500000,1.000000,700,258,49152;;"
        "126;4;2010;Arial;"
        "0.943794,0.039316,0.112127,1.308997;"
        "v1,4292215592,4293454056,128.000000,1.000000,0.500000,1.000000,700,258,49152;;",
    )

    @pytest.mark.parametrize("golden", GOLDENEK, ids=["egyblokkos", "ketblokkos"])
    def test_a_valodi_sor_bajtazonos(self, golden):
        assert serialize_text(parse_text(golden)) == golden

    def test_a_ketblokkos_mindket_blokkja_KOZEPRE_igazit(self):
        """`258` = `0x102` → igazítás 1 (közép), mód 2 (kitöltés+körvonal).
        A blokkok körvonalvastagsága `0.500000` — a mód ezzel egybevág."""
        blokkok = parse_text(self.GOLDENEK[1]).blocks
        assert len(blokkok) == 2
        for blokk in blokkok:
            assert blokk.style.alignment == 1
            assert blokk.style.fill_mode == 2

    def test_az_egyblokkos_BALRA_igazit(self):
        blokk = parse_text(self.GOLDENEK[0]).blocks[0]
        assert (blokk.style.alignment, blokk.style.fill_mode) == (0, 0)
