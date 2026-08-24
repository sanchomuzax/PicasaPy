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

1. **`blur`** — nem „halott" és nem is tétlen: a küszöbcsúszkája fölött
   VALÓDI elmosás. A mérés (`render/blur.py` docstringje) szerint a
   csúszkatartományon belül tétlen, fölötte paraméterfüggetlen, σ = 4,0
   szórású elmosás.
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
from picasapy.render.blur import BLUR_IDLE_THRESHOLD_MAX, BLUR_SIGMA, apply_blur
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

    def test_a_kuszob_folott_a_mert_elmosast_adja(self, sample):
        report = apply_filters(sample, parse_filters("blur=1,2.000000;"))
        np.testing.assert_array_equal(report.image, apply_blur(sample, 2.0))

    def test_a_csuszkatartomanyon_belul_merten_tetlen(self, sample):
        """`blur=1;` és `blur=1,0.500000;` a mérésben a FORRÁST adta vissza
        (0,24 és 0,56 — a 0,24-es JPEG-zajszint közelében)."""
        for chain in ("blur=1;", "blur=1,0.500000;", "blur=1,-0.500000;"):
            report = apply_filters(sample, parse_filters(chain))
            np.testing.assert_array_equal(report.image, sample)

    def test_a_parameter_nincs_tartomanyra_vagva(self, sample):
        """A 2,0 KILÓG a filterdesc [-0,5; 0,5] csúszkatartományából, mégis
        lefut — ha a `chain_report` vágná, a mérten futó eset tétlen lenne."""
        report = apply_filters(sample, parse_filters("blur=1,2.000000;"))
        assert report.range_warnings == ()

    def test_mar_nem_tetlen_es_nem_kalibralatlan(self):
        assert "blur" not in MEASURED_IDLE_OPS
        assert "blur" not in KNOWN_UNRENDERED_OPS
        assert can_render_filter("blur")

    def test_az_elmosas_parameterfuggetlen(self, sample):
        """A csúszka a KÜSZÖB, nem a sugár: a küszöb fölött ugyanazt az
        elmosást adja minden értékre (a mérés egyetlen sugarat mutat)."""
        np.testing.assert_array_equal(apply_blur(sample, 2.0), apply_blur(sample, 9.0))

    def test_a_kuszob_hatara_a_csuszka_teteje(self, sample):
        np.testing.assert_array_equal(
            apply_blur(sample, BLUR_IDLE_THRESHOLD_MAX), sample
        )
        assert not np.array_equal(
            apply_blur(sample, BLUR_IDLE_THRESHOLD_MAX + 0.01), sample
        )

    def test_a_mert_szoras(self):
        assert BLUR_SIGMA == pytest.approx(4.0)


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


class TestPicnikFocalPixelateNemFut:
    """3. eset — az eredeti NEM futtatja, tehát mi sem futtathatjuk.

    Mindkét mért alak (hét és négy paraméterrel) a forrást adta vissza
    (0,164 = JPEG-zaj), miközben nálunk a hétparaméteres 29,19-es
    eltérést okozott.
    """

    def test_a_lanc_tag_nem_valtoztat_a_kepen(self, sample):
        report = apply_filters(
            sample,
            parse_filters(
                "PicnikFocalPixelate=1,0.500000,0.500000,40.000000,"
                "60.000000,50.000000,0.000000;"
            ),
        )
        np.testing.assert_array_equal(report.image, sample)

    def test_a_kihagyas_okat_kimondjuk(self, sample):
        report = apply_filters(
            sample,
            parse_filters(
                "PicnikFocalPixelate=1,0.500000,0.500000,40.000000,"
                "60.000000,50.000000,0.000000;"
            ),
        )
        assert report.skipped == ("PicnikFocalPixelate",)
        assert len(report.legacy_warnings) == 1
        assert "PicnikFocalPixelate" in report.legacy_warnings[0]

    def test_mar_nincs_hozza_renderer(self):
        assert "picnikfocalpixelate" in MEASURED_NOT_RUNNING_OPS
        assert not can_render_filter("PicnikFocalPixelate")

    def test_a_lanc_tobbi_tagja_fut(self, sample):
        """A #1140-es LÁNCVÁGÁS itt NINCS bizonyítva: a mérőszett egyik
        esetében sem áll másik tag a `PicnikFocalPixelate` mögött. Amíg
        nincs mérés, a tagot ELEJTJÜK (mint minden modell nélküli nevet),
        a lánc többi tagját nem dobjuk el."""
        report = apply_filters(
            sample, parse_filters("PicnikFocalPixelate=1,0.5,0.5,40,60,50,0;bw=1;")
        )
        csak_bw = apply_filters(sample, parse_filters("bw=1;"))
        np.testing.assert_array_equal(report.image, csak_bw.image)
