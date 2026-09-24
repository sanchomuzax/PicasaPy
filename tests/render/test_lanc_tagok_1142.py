"""#1142 — három lánc-tag FORDÍTVA viselkedett, mint az eredeti Picasa.

A `PicasaPy merokit-2` mérőszett (eredeti export `export-202608151438`,
a miénk `export-202608202215`) képenként mérve három eltérést hozott ki.
A számok a FORRÁSTÓL vett átlagos abszolút eltérések; a JPEG-újratömörítés
zajszintje ebben a szettben **0,24**.

| kép | lánc | Picasa | mi (a jegy előtt) |
|---|---|---|---|
| `halott_03` | `blur=1,2.000000;` | 17,32 — LEFUT | 0,00 — elejtettük |
| `tintszin_04` | `tint=1,79.842102,000000ffff;` | 103,54 — LEFUT | 0,00 — elejtettük |
| `halott_14` | `PicnikFocalPixelate=1,0.5,…;` | 0,16 — NEM fut | 29,19 — lefutott |

A három eset HÁROM KÜLÖN ok, ezért három külön osztály:

1. **`blur`** — nem „halott": a lánc lefuttatja. A #3493 óta a kiolvasott
   natív láncot futtatjuk (`render/blur.py`); a korábbi „csúszkatartományon
   belül tétlen, fölötte σ = 4 Gauss" modell a kétszínű 762-es ábra sajátja
   volt, a viselkedést a `test_blur_nativ_3493.py` rögzíti.
2. **`tint` tíz jegyű hexszel** — nem a `tint` a hibás, hanem a HEXMEZŐ
   olvasója: az eredeti az első 8 jegyet veszi, mi az egész tagot
   érvénytelennek vettük.
3. **`PicnikFocalPixelate`** — az eredeti NEM futtatja; nálunk volt hozzá
   renderer, tehát a mi oldalunkon keletkezett a néma eltérés.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.blur import apply_blur
from picasapy.render.chain import (
    KNOWN_UNRENDERED_OPS,
    MEASURED_IDLE_OPS,
    MEASURED_NOT_RUNNING_OPS,
    apply_filters,
    can_render_filter,
)
from picasapy.render.tinting import parse_rgb_hex


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(1142)
    return rng.integers(10, 245, size=(64, 96, 3), dtype=np.uint8)


class TestBlurLefut:
    """1. eset — `blur=1,2.000000;` lefut (a mérésben 17,32-es eltérés)."""

    def test_a_merten_futo_alak_lefut(self, sample):
        report = apply_filters(sample, parse_filters("blur=1,2.000000;"))
        assert report.skipped == ()
        assert report.legacy_warnings == ()
        assert not np.array_equal(report.image, sample)

    def test_a_lanc_a_blur_modult_futtatja(self, sample):
        report = apply_filters(sample, parse_filters("blur=1,2.000000;"))
        np.testing.assert_array_equal(report.image, apply_blur(sample, 2.0))

    def test_a_parameter_nincs_tartomanyra_vagva(self, sample):
        """A 2,0 KILÓG a filterdesc [-0,5; 0,5] csúszkatartományából, mégis
        lefut — ha a `chain_report` vágná, a mérten futó eset tétlen lenne."""
        report = apply_filters(sample, parse_filters("blur=1,2.000000;"))
        assert report.range_warnings == ()

    def test_mar_nem_tetlen_es_nem_kalibralatlan(self):
        assert "blur" not in MEASURED_IDLE_OPS
        assert "blur" not in KNOWN_UNRENDERED_OPS
        assert can_render_filter("blur")


class TestTizJegyuHexSzin:
    """2. eset — a hexmező-olvasó az ELSŐ 8 jegyet veszi.

    A spec mérése (`docs/specs/picasa-ini-format.md`, „A hex színmező"):
    `000000ffff` → `000000ff` = kék, ugyanaz a ΔE (106,728), mint a
    `0000ff`-é.
    """

    def test_tiz_jegyu_hex_az_elso_nyolcra_vagodik(self):
        assert parse_rgb_hex("000000ffff") == (0x00, 0x00, 0xFF)

    def test_ugyanaz_mint_a_rovid_alak(self):
        assert parse_rgb_hex("000000ffff") == parse_rgb_hex("0000ff")

    def test_a_vezeto_nullak_tovabbra_is_elhagyhatok(self):
        cian = (0x00, 0xFF, 0xFF)
        assert parse_rgb_hex("ffff") == cian
        assert parse_rgb_hex("00ffff") == cian
        assert parse_rgb_hex("0000ffff") == cian

    def test_a_kilencedik_jegytol_nem_szamit(self):
        """A vágás az ELEJÉRŐL számol: a 8. jegy utáni rész nem befolyásol."""
        assert parse_rgb_hex("ff00aa55") == parse_rgb_hex("ff00aa5599")

    def test_az_ures_es_a_nem_hex_tovabbra_is_hiba(self):
        for bad in ("", "xyz", "12g4"):
            with pytest.raises(ValueError):
                parse_rgb_hex(bad)

    def test_a_lanc_tag_lefut_es_kekkel_szinez(self, sample):
        report = apply_filters(
            sample, parse_filters("tint=1,79.842102,000000ffff;")
        )
        assert report.skipped == ()
        rovid = apply_filters(sample, parse_filters("tint=1,79.842102,0000ff;"))
        np.testing.assert_array_equal(report.image, rovid.image)


class TestPicnikFocalPixelateFut:
    """3. eset — HELYESBÍTVE (#3315).

    A #1142 mérése hét, illetve négy mezős sorral készült, a natív
    lánc-ÍRÓ viszont NYOLCAT ír (`0x008fac40`: engedélyezés → puck x,y →
    három csúszka → a negyedik csúszka → a jelölőnégyzet `,%d`). A mérés
    tehát rossz aritású bemenetre vonatkozott; a betöltő úton semmi nem
    zárja ki a szűrőt (`0x008f9fe0` a `filterdesc.xml`-regiszterből építi,
    `0x008f9a60` a közös Glimmer-feldolgozó). Pozitív kontroll: a
    `FocalZoom` ugyanilyen leíró jelölőnégyzet nélkül — ott a hétmezős
    alak a TELJES alak, és mérten lefut.

    ⚠️ A nyolcmezős alak golden-mérése HÁTRAVAN (külön jegy); addig a
    bizonyíték a futás mellett szól.
    """

    def test_a_nyolcmezos_alak_LEFUT(self, sample):
        """#3315: a #1142 mérése ROSSZ ARITÁSÚ sorral készült (hét, illetve
        négy mező), a natív lánc-író viszont NYOLCAT ír:
        `PicnikFocalPixelate=1,x,y,Impact,Radius,Hardness,Fade,Reverse;`
        (`0x008fac40` mezősorrend). A betöltő úton semmi nem zárja ki a
        szűrőt, ezért rendereljük."""
        report = apply_filters(
            sample,
            parse_filters(
                "PicnikFocalPixelate=1,0.500000,0.500000,40.000000,"
                "60.000000,50.000000,0.000000,0;"
            ),
        )
        assert report.skipped == ()
        assert not np.array_equal(report.image, sample)

    def test_mar_van_hozza_renderer(self):
        assert "picnikfocalpixelate" not in MEASURED_NOT_RUNNING_OPS
        assert can_render_filter("PicnikFocalPixelate")

    def test_a_lanc_tobbi_tagja_is_fut(self, sample):
        """#3315: a tag LEFUT, és a mögötte álló tagok is.

        ⚠️ Az EREDETI Picasában egy ISMERETLEN tag a lánc maradékát is
        elejti (`0x00907740`: a `0x00908360` nem nulla hibakódjára a
        bejáró kilép a ciklusból, a hívó a hibakódot eldobja) — ezért nem
        mindegy, hogy kanonikus nevet írunk-e. Ez a tag kanonikus."""
        report = apply_filters(
            sample,
            parse_filters(
                "PicnikFocalPixelate=1,0.5,0.5,40,60,50,0,0;bw=1;"
            ),
        )
        csak_bw = apply_filters(sample, parse_filters("bw=1;"))
        assert report.skipped == ()
        assert not np.array_equal(report.image, csak_bw.image)
        # a bw a második tag: a kimenet szürke marad
        assert np.allclose(report.image[..., 0], report.image[..., 1], atol=1)
