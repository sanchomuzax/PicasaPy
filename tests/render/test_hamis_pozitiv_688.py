"""#688: hamis pozitívok — ahol az eredeti Picasa tétlen, mi se hassunk.

A #685 mérőszettje (valódi Picasa-export a NAS-on) két szűrőnél mutatta ki,
hogy a modellünk akkor is fest, amikor a Picasa nem nyúl a képhez:

* `ReanimatedEyeColor` („Ghoul Eye") — ecset-maszkra dolgozik, és ÜRES
  maszkkal indul: befestés nélkül a Picasa nem csinál semmit
  (ΔE 0,18 = JPEG-zaj), a mi modellünk viszont ΔE 57,5 mértékben átfestette
  a teljes képet.
* `LocalContrast` — a `Contrast` csúszka `[1..3]` tartományának ALSÓ vége a
  nulla-állapot: a natív művelet `Strength` argumentuma `Contrast − 1`.

A két effekt „foga" (hogy a javítás nem egyszerű kikapcsolás) külön
állításokkal van ellenőrizve, és a szomszédos, MÉRTEN aktív esetek
(`PicnikTint`, `HDR`) regressziós őrként szerepelnek.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.glimmer_focal import apply_reanimated_eye_color
from picasapy.render.glimmer_tone import apply_hdr, apply_local_contrast


@pytest.fixture
def sample() -> np.ndarray:
    """Sík felület + részletes sáv: a helyi kontraszt is meg tud fogni rajta."""
    rng = np.random.default_rng(688)
    image = rng.integers(40, 210, size=(64, 96, 3), dtype=np.uint8)
    image[:24, :, :] = 128
    return image


def _rendered(image: np.ndarray, chain_text: str) -> np.ndarray:
    return apply_filters(image, parse_filters(chain_text)).image


class TestReanimatedEyeColorRegioNelkul:
    """Ecset-maszk nélkül AZONOSSÁG — ez a #688 P1 magja."""

    @pytest.mark.parametrize(
        "chain_text",
        [
            "ReanimatedEyeColor=1,0.000000,0.000000;",  # a mérőszett „min" esete
            "ReanimatedEyeColor=1,6.000000,20.000000;",  # a mérőszett „alap" esete
            "ReanimatedEyeColor=1,30.000000,100.000000;",
            "ReanimatedEyeColor=1;",
        ],
    )
    def test_a_lanc_valtozatlanul_hagyja_a_kepet(self, sample, chain_text):
        np.testing.assert_array_equal(_rendered(sample, chain_text), sample)

    def test_a_fuggveny_maszk_nelkul_azonossag(self, sample):
        np.testing.assert_array_equal(
            apply_reanimated_eye_color(sample, blur=0.0, fade=0.0), sample
        )

    def test_ures_maszkkal_is_azonossag(self, sample):
        mask = np.zeros(sample.shape[:2], dtype=np.float32)
        np.testing.assert_array_equal(
            apply_reanimated_eye_color(sample, blur=0.0, fade=0.0, mask=mask), sample
        )

    def test_befestett_maszkkal_VAN_hatasa(self, sample):
        """Az őrnek foga van: maszkkal a visszafejtett pixel-matematika fut."""
        mask = np.zeros(sample.shape[:2], dtype=np.float32)
        mask[30:50, 40:70] = 1.0
        result = apply_reanimated_eye_color(sample, blur=2.0, fade=0.0, mask=mask)
        assert not np.array_equal(result[30:50, 40:70], sample[30:50, 40:70])

    def test_a_maszkon_kivul_semmi_nem_valtozik(self, sample):
        mask = np.zeros(sample.shape[:2], dtype=np.float32)
        mask[30:50, 40:70] = 1.0
        result = apply_reanimated_eye_color(sample, blur=2.0, fade=0.0, mask=mask)
        np.testing.assert_array_equal(result[:30], sample[:30])
        np.testing.assert_array_equal(result[50:], sample[50:])

    def test_a_bemenetet_nem_mutalja(self, sample):
        eredeti = sample.copy()
        apply_reanimated_eye_color(sample, blur=3.0, fade=10.0)
        np.testing.assert_array_equal(sample, eredeti)

    def test_a_figyelmeztetes_kimondja_hogy_valtozatlan(self, sample):
        report = apply_filters(sample, parse_filters("ReanimatedEyeColor=1,6.0,20.0;"))
        assert report.skipped == ()
        warnings = [w for w in report.range_warnings if "ReanimatedEyeColor" in w]
        assert warnings, report.range_warnings
        assert "változatlan" in warnings[0]


class TestPicnikTintTovabbraIsHat:
    """A `PicnikTint` NEM ugyanaz az eset: a #685 exportján a Picasa maga is
    a teljes képre vitte fel (ΔE 36,9), ezért ez marad aktív."""

    def test_a_teljes_kepre_fut(self, sample):
        result = _rendered(sample, "PicnikTint=1,0.000000,0080cfff;")
        assert not np.array_equal(result, sample)


class TestLocalContrastNullaAllapot:
    """A `Contrast` csúszka alsó vége (1,0) a nulla-állapot: `Strength = 0`."""

    def test_a_minimum_azonossag_a_lancon(self, sample):
        np.testing.assert_array_equal(
            _rendered(sample, "LocalContrast=1,1.300000,1.000000;"), sample
        )

    @pytest.mark.parametrize("radius", [1.3, 15.0, 40.0])
    def test_a_minimum_barmely_sugarral_azonossag(self, sample, radius):
        np.testing.assert_array_equal(
            apply_local_contrast(sample, radius=radius, strength=1.0), sample
        )

    @pytest.mark.parametrize(
        "chain_text",
        [
            "LocalContrast=1,15.000000,1.500000;",
            "LocalContrast=1,40.000000,3.000000;",
        ],
    )
    def test_a_tobbi_allas_tovabbra_is_hat(self, sample, chain_text):
        assert not np.array_equal(_rendered(sample, chain_text), sample)

    def test_a_bemenetet_nem_mutalja(self, sample):
        eredeti = sample.copy()
        apply_local_contrast(sample, radius=15.0, strength=1.5)
        np.testing.assert_array_equal(sample, eredeti)


class TestHdrNemKapjaMegAzEltolast:
    """A `HDR` MÁS motor: a #685 exportján `Strength=1`-nél is hatott
    (ΔE 1,04), és a `Strength`-et közvetlenül adja tovább — az eltolás
    ott ROSSZABB illeszkedést adott (1,71 vs 1,24)."""

    def test_hdr_strength_1_nel_is_hat(self, sample):
        assert not np.array_equal(apply_hdr(sample, radius=20.0, strength=1.0), sample)

    def test_hdr_fade_100_valtozatlan(self, sample):
        np.testing.assert_array_equal(apply_hdr(sample, fade=100.0), sample)
