"""#381: `glimmer_focal` — PicnikTint/ReanimatedEyeColor min/alap/max
határeset-tesztjei. A festhető-maszk hiánya miatt a hatás a TELJES KÉPRE
fut (ld. modul-docstring) — a `chain.py`-beli figyelmeztetést a
`test_chain_glimmer_381.py` fedi.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_focal as fo


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(51)
    return rng.integers(20, 235, size=(48, 64, 3), dtype=np.uint8)


class TestPicnikTint:
    @pytest.mark.parametrize("fade", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, fade):
        result = fo.apply_picnik_tint(image, fade=fade)
        assert result.dtype == np.uint8 and result.shape == image.shape

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(fo.apply_picnik_tint(image, fade=100.0), image)

    def test_fade_0_a_kep_rajzolatat_MEGTARTJA(self, image):
        """#884: ez a teszt korábban a HIBÁT rögzítette szerződésként — azt
        állította, hogy `Fade = 0`-nál a kimenet MINDEN képpontja a választott
        szín, tehát a kép egyetlen tömör felületté lapul.

        A valódi `TintImageOperation` fényesség-tartó: a kép luminanciáját
        megőrzi, és csak a krómát cseréli. A #685 golden párján ez ΔE 33,45 →
        1,50 javulást adott. A részletes őrök: `test_picniktint_884.py`.
        """
        result = fo.apply_picnik_tint(image, color=(1, 2, 3), fade=0.0)
        assert len(np.unique(result.reshape(-1, 3), axis=0)) > 1, (
            "a kimenet nem lehet egyetlen tömör szín — a kép rajzolata megmarad"
        )
        assert float(result.std()) > 1.0


class TestReanimatedEyeColor:
    @pytest.mark.parametrize("blur,fade", [(0.0, 0.0), (6.0, 20.0), (30.0, 100.0)])
    def test_hatarok(self, image, blur, fade):
        result = fo.apply_reanimated_eye_color(image, blur=blur, fade=fade)
        assert result.dtype == np.uint8 and result.shape == image.shape

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(fo.apply_reanimated_eye_color(image, fade=100.0), image)
