"""#381: `glimmer_tone` — Vignette/Matte/HDR/LocalContrast/CrossProcess/
Sixties/HeatMap/NightVision/TwoTone/QuantizePalette min/alap/max
határeset-tesztjei, a `filterdesc-registry.md` 4.2 tartományai szerint.
"""

from __future__ import annotations

import time

import cv2
import numpy as np
import pytest

from picasapy.render import glimmer_tone as t
from tests.support.realistic_photo import make_realistic_photo


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(9)
    img = rng.integers(20, 235, size=(48, 64, 3), dtype=np.uint8)
    img[:16, :, 0] = 220
    return img


def _real_photo_rgb(height: int, width: int, seed: int = 7) -> np.ndarray:
    """#504 (j1): ld. `test_glimmer_creative.py` ugyanilyen helperjét."""
    return cv2.cvtColor(make_realistic_photo(height=height, width=width, seed=seed), cv2.COLOR_BGR2RGB)


def _assert_valid(result, image):
    assert result.dtype == np.uint8
    assert result.shape[2] == 3


class TestVignetteMatte:
    @pytest.mark.parametrize("blur,strength,fade", [(0.0, 1.0, 0.0), (35.0, 1.4, 0.0), (50.0, 2.0, 100.0)])
    def test_vignette_hatarok(self, image, blur, strength, fade):
        _assert_valid(t.apply_vignette(image, blur=blur, strength=strength, fade=fade), image)

    @pytest.mark.parametrize("blur,strength,fade", [(0.0, 1.0, 0.0), (40.0, 1.2, 0.0), (50.0, 2.0, 100.0)])
    def test_matte_hatarok(self, image, blur, strength, fade):
        _assert_valid(t.apply_matte(image, blur=blur, strength=strength, fade=fade), image)

    def test_vignette_fade_100_valtozatlan(self, image):
        result = t.apply_vignette(image, fade=100.0)
        np.testing.assert_array_equal(result, image)

    def test_vignette_szel_sotetebb_kozepnel(self):
        white = np.full((60, 80, 3), 255, dtype=np.uint8)
        result = t.apply_vignette(white)
        assert int(result[30, 40, 0]) >= int(result[0, 40, 0])

    # a VALÓDI Picasa-kimenetből (`referencia/vignette/Vignette default`,
    # 2560×1702) mért maszk: a középtől mért, a fél-hosszabbik-oldallal
    # normált sugár → a sötétítés szorzója (a képpontok medián-aránya az
    # effekt nélküli exporthoz). A 0,45 alatti sávban a maszk 1,000.
    _PICASA_VIGNETTE_PROFILE = ((0.45, 0.973), (0.65, 0.895), (0.85, 0.746), (1.05, 0.336))

    def test_vignette_maszkja_a_picasa_mert_profiljat_adja(self):
        """#317: a `Blur=35` (alapértelmezett) maszk a VALÓDI Picasa-kimenetből
        mért profilt követi.

        Ez a mérés adta a `sugár = Blur·0,02·max(W,H)/8` képletet is: a
        `filterdesc.xml` `/4`-es képlete (és a rá tett 255-ös Flash-korlát)
        ennél a profilnál mérhetően beljebb kezdi a sötétítést.
        """
        height, width = 851, 1280  # a referencia-fotó fele, arányhelyesen
        white = np.full((height, width, 3), 255, dtype=np.uint8)
        mask = t.apply_vignette(white, blur=35.0)[..., 0].astype(float) / 255.0
        rows, cols = np.mgrid[0:height, 0:width]
        radius = np.hypot(
            (rows - height / 2) / (max(height, width) / 2),
            (cols - width / 2) / (max(height, width) / 2),
        )
        for centre, expected in self._PICASA_VIGNETTE_PROFILE:
            band = (radius >= centre - 0.05) & (radius < centre + 0.05)
            measured = float(np.median(mask[band]))
            assert measured == pytest.approx(expected, abs=0.06), (
                f"r={centre}: {measured:.3f} a Picasa mért {expected:.3f} helyett"
            )

    def test_vignette_nagy_kepen_sem_vagodik_le_a_sugar(self):
        """A 255-ös Flash-korlát (#518, Lomo/Holga) itt NEM érvényes: a
        `referencia/vignette/` Blur=50-es exportja 310–320-as szigmát kíván,
        a 255-re vágott sugár mérhetően rosszabb. Ha valaki visszatenné a
        korlátot, a Blur=35 és a Blur=50 kimenete AZONOSSÁ válna egy nagy
        képen (mindkettő 255-re vágódna) — ez a teszt épp ezt buktatja.
        """
        photo = _real_photo_rgb(1200, 1800, seed=5)
        mid = t.apply_vignette(photo, blur=35.0)
        wide = t.apply_vignette(photo, blur=50.0)
        difference = float(np.abs(mid.astype(float) - wide.astype(float)).mean())
        assert difference > 1.0, "a Blur csúszka nem hat — visszakerült a 255-ös korlát?"


class TestHdrLocalContrast:
    @pytest.mark.parametrize("radius,strength", [(1.3, 1.0), (20.0, 3.0), (80.0, 7.0)])
    def test_hdr_hatarok(self, image, radius, strength):
        _assert_valid(t.apply_hdr(image, radius=radius, strength=strength), image)

    def test_hdr_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_hdr(image, fade=100.0), image)

    @pytest.mark.parametrize("radius,strength", [(1.3, 1.0), (15.0, 1.5), (40.0, 3.0)])
    def test_local_contrast_hatarok(self, image, radius, strength):
        _assert_valid(t.apply_local_contrast(image, radius=radius, strength=strength), image)


class TestCrossProcess:
    @pytest.mark.parametrize("fade", [0.0, 50.0, 100.0])
    def test_hatarok(self, image, fade):
        _assert_valid(t.apply_crossprocess(image, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_crossprocess(image, fade=100.0), image)

    def test_fade_0_valtoztat(self, image):
        assert not np.array_equal(t.apply_crossprocess(image, fade=0.0), image)


class TestSixties:
    @pytest.mark.parametrize("fade,rounded", [(0.0, False), (20.0, True), (100.0, True)])
    def test_hatarok(self, image, fade, rounded):
        _assert_valid(t.apply_sixties(image, fade=fade, rounded=rounded), image)

    def test_rounded_sarok_szinu(self, image):
        result = t.apply_sixties(image, fade=0.0, rounded=True, color=(1, 2, 3))
        assert tuple(result[0, 0]) == (1, 2, 3)


class TestHeatMap:
    @pytest.mark.parametrize("hue,fade", [(-180.0, 0.0), (0.0, 0.0), (180.0, 100.0)])
    def test_hatarok(self, image, hue, fade):
        _assert_valid(t.apply_heatmap(image, hue=hue, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_heatmap(image, fade=100.0), image)


class TestNightVision:
    @pytest.mark.parametrize(
        "brightness,contrast,fade", [(-50.0, -50.0, 0.0), (0.0, 0.0, 0.0), (50.0, 50.0, 100.0)]
    )
    def test_hatarok(self, image, brightness, contrast, fade):
        _assert_valid(t.apply_nightvision(image, brightness=brightness, contrast=contrast, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_nightvision(image, fade=100.0), image)


class TestVignetteMatteNightVisionRealPhoto504510:
    """#504/#510 — valódi (folytonos hisztogramú) fotóval mért kiegészítés
    a `TestHolgaRealPhoto504510`-hez (`test_glimmer_creative.py`): a #509/
    #504 mind az ÖT méretfüggő ragyogás-effektet érintette (j3), nemcsak a
    Lomo/Holga párt."""

    def test_nightvision_r_nagyobb_mint_b(self):
        """#510: a NightVision `#57cc29` (R=0x57=87 > B=0x29=41) tintje a
        valódi BGR-kimeneten is R>B legyen — ellenőrzi, hogy a
        `_NIGHTVISION_COLORS` RGB-ként helyesen íródott."""
        photo_rgb = _real_photo_rgb(200, 300)
        result_rgb = t.apply_nightvision(photo_rgb)
        result_bgr = cv2.cvtColor(result_rgb, cv2.COLOR_RGB2BGR)
        assert float(result_bgr[..., 2].mean()) > float(result_bgr[..., 0].mean())

    @pytest.mark.parametrize(
        "effect_name,apply_fn",
        [
            ("Vignette", t.apply_vignette),
            ("Matte", t.apply_matte),
            ("NightVision", t.apply_nightvision),
        ],
    )
    def test_meretfuggetlen_fekete_arany(self, effect_name, apply_fn):
        """j2: a méretfüggő ragyogás-sugár ellenére a tiszta fekete arány
        96 px-en és 1600 px-en néhány százalékon belül egyezzen."""

        def black_pct(img: np.ndarray) -> float:
            return float(np.all(img == 0, axis=-1).mean() * 100.0)

        small = apply_fn(_real_photo_rgb(96, 72))
        large = apply_fn(_real_photo_rgb(1600, 1200))
        diff = abs(black_pct(small) - black_pct(large))
        assert diff <= 15.0, (
            f"{effect_name}: fekete-arány 96px={black_pct(small):.1f}% "
            f"vs 1600px={black_pct(large):.1f}% — {diff:.1f}pp eltérés"
        )

    @pytest.mark.parametrize(
        "effect_name,apply_fn",
        [
            ("Vignette", t.apply_vignette),
            ("Matte", t.apply_matte),
            ("NightVision", t.apply_nightvision),
        ],
    )
    def test_perf_nagy_kepen(self, effect_name, apply_fn):
        """j5: a közös `_border_glow` nagy képen is gyors maradjon
        (nagyvonalú korlát, hogy lassú CI-n se legyen ingatag — a
        javítás előtt a Vignette 124 s, a Matte 89 s volt egy
        4000×3000-es fotón, ld. a #504 utolsó kommentje)."""
        photo_rgb = _real_photo_rgb(1500, 2000)
        t0 = time.perf_counter()
        apply_fn(photo_rgb)
        elapsed = time.perf_counter() - t0
        assert elapsed < 20.0, f"{effect_name}(2000x1500) túl lassú: {elapsed:.2f}s"


class TestTwoTone:
    @pytest.mark.parametrize(
        "brightness,contrast,fade", [(-95.0, 0.0, 0.0), (0.0, 20.0, 0.0), (95.0, 100.0, 100.0)]
    )
    def test_hatarok(self, image, brightness, contrast, fade):
        _assert_valid(t.apply_twotone(image, brightness=brightness, contrast=contrast, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_twotone(image, fade=100.0), image)


class TestQuantizePalette:
    @pytest.mark.parametrize("steps,smoothing,fade", [(2.0, 0.0, 0.0), (8.0, 80.0, 0.0), (30.0, 100.0, 100.0)])
    def test_hatarok(self, image, steps, smoothing, fade):
        _assert_valid(t.apply_quantizepalette(image, steps=steps, smoothing=smoothing, fade=fade), image)

    def test_fade_100_valtozatlan(self, image):
        np.testing.assert_array_equal(t.apply_quantizepalette(image, fade=100.0), image)


class TestHdrMeasuredModel:
    """#545: a HDR/LocalContrast mért modellje (`referencia/hdrish/`)."""

    def test_a_szigma_a_radius_fele(self):
        """A négy Radius-állás egymástól függetlenül a felét adta.

        Közvetlenül nem tudjuk kiolvasni a szigmát, ezért az
        EGYENÉRTÉKŰSÉGET mérjük: a `Radius=20`-as HDR ugyanazt adja, mint a
        `local_contrast` primitív σ=10-zel — ha valaki visszaállítaná a
        `Radius`-t közvetlen szigmának, ez a teszt bukik.
        """
        from picasapy.render import glimmer_ops as ops

        photo = _real_photo_rgb(200, 300, seed=3)
        through_hdr = t.apply_hdr(photo, radius=20.0, strength=3.0, fade=0.0)

        image_f = ops.to_float(photo)
        blurred = ops.gaussian_blur_f(image_f, 10.0)
        expected = ops.to_uint8(image_f + (image_f - blurred) * 3.0 + 2.9 * 3.0)

        np.testing.assert_array_equal(through_hdr, expected)

    def test_a_vilagositas_a_strengthtel_aranyos(self):
        """A lokális kontraszt mellett `Strength`-arányos világosítás is fut
        — sík (részletmentes) képen csak ez látszik, ezért ott mérhető."""
        flat = np.full((40, 50, 3), 100, dtype=np.uint8)
        for strength, expected in ((1.0, 100 + 2.9), (3.0, 100 + 8.7), (7.0, 100 + 20.3)):
            result = t.apply_hdr(flat, radius=20.0, strength=strength, fade=0.0)
            assert int(result[20, 25, 0]) == round(expected)

    def test_fade_100_valtozatlan_marad(self):
        photo = _real_photo_rgb(60, 80, seed=9)
        np.testing.assert_array_equal(
            t.apply_hdr(photo, radius=20.0, strength=3.0, fade=100.0), photo
        )
