"""#381: a közös Glimmer-primitívek (`glimmer_ops.py`/`glimmer_frame_ops.py`)
egységtesztjei — görbe-interpoláció, blend-módok, Fade-szabály, maszkolt
keverés, belső ragyogás, zaj, gradiens-leképezés, keret-primitívek.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_frame_ops as gf
from picasapy.render import glimmer_ops as g


@pytest.fixture
def image() -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.integers(20, 235, size=(32, 48, 3), dtype=np.uint8)


class TestFadeRule:
    def test_fade_0_teljes_alfa(self):
        assert g.fade_alpha(0.0) == 1.0

    def test_fade_100_nulla_alfa(self):
        assert g.fade_alpha(100.0) == 0.0

    def test_fade_50_fel_alfa(self):
        assert g.fade_alpha(50.0) == pytest.approx(0.5)

    def test_fade_tartomanyon_kivul_vagva(self):
        assert g.fade_alpha(-20.0) == 1.0
        assert g.fade_alpha(150.0) == 0.0


class TestBlendModes:
    def test_normal_a_top_reteget_adja(self):
        base = np.zeros((2, 2, 3), dtype=np.float32)
        top = np.full((2, 2, 3), 200.0, dtype=np.float32)
        result = g.apply_blend_mode(base, top, "normal", 1.0)
        np.testing.assert_allclose(result, top)

    def test_multiply_feketevel_fekete(self):
        base = np.full((2, 2, 3), 200.0, dtype=np.float32)
        top = np.zeros((2, 2, 3), dtype=np.float32)
        result = g.apply_blend_mode(base, top, "multiply", 1.0)
        np.testing.assert_allclose(result, 0.0)

    def test_screen_feherrel_feher(self):
        base = np.full((2, 2, 3), 50.0, dtype=np.float32)
        top = np.full((2, 2, 3), 255.0, dtype=np.float32)
        result = g.apply_blend_mode(base, top, "screen", 1.0)
        np.testing.assert_allclose(result, 255.0)

    def test_darken_a_kisebbet_adja(self):
        base = np.array([[100.0, 100.0, 100.0]])
        top = np.array([[50.0, 150.0, 100.0]])
        result = g.apply_blend_mode(base, top, "darken", 1.0)
        np.testing.assert_allclose(result, [[50.0, 100.0, 100.0]])

    def test_lighten_a_nagyobbat_adja(self):
        base = np.array([[100.0, 100.0, 100.0]])
        top = np.array([[50.0, 150.0, 100.0]])
        result = g.apply_blend_mode(base, top, "lighten", 1.0)
        np.testing.assert_allclose(result, [[100.0, 150.0, 100.0]])

    def test_opacity_nulla_a_bazist_adja(self):
        base = np.full((2, 2, 3), 60.0, dtype=np.float32)
        top = np.full((2, 2, 3), 240.0, dtype=np.float32)
        result = g.apply_blend_mode(base, top, "overlay", 0.0)
        np.testing.assert_allclose(result, base)

    def test_ismeretlen_mod_hibat_dob(self):
        base = np.zeros((1, 1, 3), dtype=np.float32)
        with pytest.raises(ValueError):
            g.apply_blend_mode(base, base, "xyz", 1.0)


class TestMaskedBlend:
    def test_maszk_nulla_a_bazist_tartja(self):
        base = np.full((2, 2, 3), 10.0, dtype=np.float32)
        overlay = np.full((2, 2, 3), 200.0, dtype=np.float32)
        mask = np.zeros((2, 2), dtype=np.float32)
        np.testing.assert_allclose(g.masked_blend(base, overlay, mask), base)

    def test_maszk_egy_az_overlayt_adja(self):
        base = np.full((2, 2, 3), 10.0, dtype=np.float32)
        overlay = np.full((2, 2, 3), 200.0, dtype=np.float32)
        mask = np.ones((2, 2), dtype=np.float32)
        np.testing.assert_allclose(g.masked_blend(base, overlay, mask), overlay)


class TestAutofix:
    """#535: az `AutoFix` a `apply_enhance`-szel AZONOS megfejtett modellt
    használ — csatornánkénti, hisztogram-darabszám alapú lineáris
    szinthúzás. A hat érintett Glimmer-effekt (Holga, NightVision,
    PencilSketch, Sixties, Cinemascope) ezen keresztül örökli a modellt."""

    def _teljes_tartomanyu_kep(self, height: int = 40, width: int = 60) -> np.ndarray:
        image = np.full((height, width, 3), 128, dtype=np.uint8)
        body_rows = height - 8
        ramp = np.linspace(10, 245, width, dtype=np.uint8)
        image[:body_rows] = ramp[np.newaxis, :, np.newaxis]
        image[body_rows : body_rows + 5] = 0
        image[body_rows + 5 :] = 255
        return image

    def test_azonossag_teljes_tartomanyu_kepen(self):
        image = self._teljes_tartomanyu_kep()
        np.testing.assert_array_equal(g.autofix(image), image)

    def test_szethuzza_a_nem_teljes_tartomanyu_kepet(self):
        image = np.tile(np.linspace(60, 180, 50, dtype=np.uint8), (30, 1))
        image = np.stack([image, image, image], axis=-1)
        result = g.autofix(image)
        assert result.min() == 0
        assert result.max() == 255

    def test_nem_mutalja_a_bemenetet(self):
        image = np.tile(np.linspace(60, 180, 50, dtype=np.uint8), (30, 1))
        image = np.stack([image, image, image], axis=-1)
        original = image.copy()
        g.autofix(image)
        np.testing.assert_array_equal(image, original)


class TestAdjustCurves:
    def test_azonossag_valtozatlan(self, image):
        result = g.adjust_curves(image, master=((0.0, 0.0), (255.0, 255.0)))
        np.testing.assert_array_equal(result, image)

    def test_invert_curve(self, image):
        result = g.invert_curve(image)
        assert not np.array_equal(result, image)
        np.testing.assert_array_equal(g.invert_curve(result), image)


class TestInnerGlow:
    def test_alfa_nulla_valtozatlan(self, image):
        result = g.inner_glow(image, (0, 0, 0), 5.0, 5.0, 1.4, alpha=0.0)
        np.testing.assert_array_equal(result, image)

    def test_pozitiv_alfa_valtoztat(self, image):
        result = g.inner_glow(image, (0, 0, 0), 5.0, 5.0, 1.4, alpha=1.0)
        assert not np.array_equal(result, image)

    def test_szelek_sotetebbek_feher_alapon(self):
        white = np.full((40, 60, 3), 255, dtype=np.uint8)
        result = g.inner_glow(white, (0, 0, 0), 6.0, 6.0, 1.4, alpha=1.0)
        assert int(result[0, 30, 0]) < int(result[20, 30, 0])

    @pytest.mark.parametrize("sigma", [5.0, 20.0, 60.0])
    def test_kis_szigmanal_a_kozeppont_sulya_kozel_nulla(self, sigma):
        """#522: az analitikus modellben (a #509 min-max normálásának
        felváltása) a középpont súlya akkor tart nullához, ha σ jóval
        kisebb a kép méreténél — ez a VALÓS üzemi tartomány (a
        `clamp_glow_radius` 255-re vágja σ-t, a fényképek pedig ennél
        nagyságrendekkel nagyobbak, ld. `TestAnalyticWeightMapProperties`).
        Ezen a 600×800-as képen az 5–60 tartomány σ << méret."""
        white = np.full((600, 800, 3), 255, dtype=np.uint8)
        result = g.inner_glow(white, (0, 0, 0), sigma, sigma, 1.1, alpha=1.0)
        center = result[300, 400]
        assert center.astype(np.float64).mean() > 250.0

    @pytest.mark.parametrize("sigma", [140.0, 280.0])
    def test_nagy_szigmanal_a_kozep_is_erintve_analitikus_modellben(self, sigma):
        """#522: ELTÉRÉS a korábbi (#504-es) teszttől — SZÁNDÉKOSAN.

        A #509-es min-max modell ezen a 600×800-as képen MESTERSÉGESEN
        ~0-n tartotta a közép súlyát FÜGGETLENÜL σ-tól (a saját min/maxára
        nyújtott) — ez volt pontosan a #522 jegyben megnevezett hiba: a σ
        nem csak az ALAKOT, hanem tévesen a MÉLYSÉGET is befolyásolta. Az
        analitikus modellben, ha σ összemérhető a kép méretével, a közép
        LEGITIM módon kap ragyogást — ez a valódi fizika, amit a
        referencia-mérés igazol (Holga-eltérés 31,64→14,19, Lomo-eltérés
        14,63→8,55, ld. a PR-jelentést). A teszt csak azt várja el, hogy a
        hatás MÉRHETŐ (nem nullázott mesterségesen), és σ növelésével nő.
        """
        white = np.full((600, 800, 3), 255, dtype=np.uint8)
        result = g.inner_glow(white, (0, 0, 0), sigma, sigma, 1.1, alpha=1.0)
        center = result[300, 400].astype(np.float64).mean()
        assert center < 250.0

    def test_nagy_szigmanal_a_kozep_hatasa_no_sigmaval(self):
        """#522: a 140→280 σ-emelés a fenti (600×800-as, összemérhető méretű)
        képen ERŐSÍTI a közép-hatást — ez a valódi, renormalizálatlan
        mélység-viselkedés."""
        white = np.full((600, 800, 3), 255, dtype=np.uint8)
        center_140 = g.inner_glow(white, (0, 0, 0), 140.0, 140.0, 1.1, alpha=1.0)[300, 400].mean()
        center_280 = g.inner_glow(white, (0, 0, 0), 280.0, 280.0, 1.1, alpha=1.0)[300, 400].mean()
        assert center_280 < center_140

    def test_nagy_kepen_sem_feketedik_be_a_kozep(self):
        """A #504 jelentés konkrét mérete (800×600) valódi zajképen."""
        rng = np.random.default_rng(7)
        img = rng.integers(20, 235, size=(600, 800, 3), dtype=np.uint8)
        radius = 35.0 * 0.02 * max(img.shape[:2]) / 2.0  # apply_lomo sugara ~280
        result = g.inner_glow(img, (0, 0, 0), radius, radius, 1.1, alpha=1.0)
        assert result.mean() > 20.0


class TestAnalyticWeightMapProperties:
    """#522: az analitikus súlytérkép (`covered = ay·ax`, `weight =
    (1−covered)·strength`) ELVÁRT tulajdonságai VALÓS fényképméretű
    (2560×1702, a referencia-fotó mérete) képen, a `GLOW_RADIUS_MAX`-ig
    (255) terjedő TETSZŐLEGES σ-ra — ezt a #509-es min-max normálás NEM
    tudta garantálni (a saját min/maxára nyújtott, ami σ-tól függően
    torzította a tényleges mélységet)."""

    _HEIGHT, _WIDTH = 1702, 2560

    @pytest.mark.parametrize("sigma", [1.0, 10.0, 50.0, 100.0, 200.0, 255.0])
    def test_kozeppont_sulya_kozel_nulla_barmely_korlatozott_sigmara(self, sigma):
        white = np.full((self._HEIGHT, self._WIDTH, 3), 255, dtype=np.uint8)
        result = g.inner_glow(white, (0, 0, 0), sigma, sigma, 1.4, alpha=1.0)
        center = result[self._HEIGHT // 2, self._WIDTH // 2].astype(np.float64).mean()
        assert center > 245.0, f"σ={sigma}: közép={center:.1f}, várt >245"

    @pytest.mark.parametrize("sigma", [1.0, 10.0, 50.0, 100.0, 200.0, 255.0])
    def test_szel_sulya_szigoruan_nagyobb_mint_a_kozepe(self, sigma):
        white = np.full((self._HEIGHT, self._WIDTH, 3), 255, dtype=np.uint8)
        result = g.inner_glow(white, (0, 0, 0), sigma, sigma, 1.4, alpha=1.0)
        edge = float(result[0, self._WIDTH // 2, 0])
        center = float(result[self._HEIGHT // 2, self._WIDTH // 2, 0])
        assert edge <= center

    def test_szel_sulya_monoton_kozeliti_a_strengtht_sigma_novelesevel(self):
        """A σ növelésével a szél EGYRE SÖTÉTEBB (a `strength`-hez egyre
        közelebbi VALÓDI mélységet kap) — ez a renormalizálatlan mélység-
        hatás, amit a min-max modell elfedett (ott a szél súlya σ-tól
        gyakorlatilag függetlenül ~1-re volt nyújtva)."""
        white = np.full((self._HEIGHT, self._WIDTH, 3), 255, dtype=np.uint8)
        strength = 1.4
        sigmas = [1.0, 20.0, 80.0, 150.0, 255.0]
        edges = [
            float(g.inner_glow(white, (0, 0, 0), s, s, strength, alpha=1.0)[0, self._WIDTH // 2, 0])
            for s in sigmas
        ]
        assert edges == sorted(edges, reverse=True)


class TestClampGlowRadius:
    """#504: a Flash `GlowFilter.blurX`/`blurY` öröksége — a Picasa
    `GlowImageOperation`-je (`inner_glow`) méretfüggő sugár-képletei
    (Lomo, Holga, NightVision, Matte, Vignette, MuseumMatte) sosem
    futhatnak 255 fölé, bármekkora is a kép (ld. `GLOW_RADIUS_MAX`
    docstringje a lomo-referenciakészlettel mért bizonyítékért)."""

    def test_konstans_255(self):
        assert g.GLOW_RADIUS_MAX == 255.0

    def test_nagy_kepen_a_tenyleges_sigma_255re_vagva(self):
        # Lomo képlete: 35·0,02·max(W,H)/2 — egy 4000×3000-es fotón ez
        # 35·0,02·4000/2 = 1400 lenne, jóval a Flash-korlát fölött.
        height, width = 3000, 4000
        raw_radius = 35.0 * 0.02 * max(height, width) / 2.0
        assert raw_radius > g.GLOW_RADIUS_MAX
        assert g.clamp_glow_radius(raw_radius) == g.GLOW_RADIUS_MAX

    def test_kis_kepen_a_kepletnek_megfelelo_kisebb_ertek(self):
        # Ugyanaz a Lomo-képlet egy 96×72-es kis képen a korlát alatt marad
        # — a `clamp_glow_radius` ekkor NEM módosít az értéken.
        height, width = 72, 96
        raw_radius = 35.0 * 0.02 * max(height, width) / 2.0
        assert raw_radius < g.GLOW_RADIUS_MAX
        assert g.clamp_glow_radius(raw_radius) == pytest.approx(raw_radius)


class TestClampGlowRadiusTengelyenkent:
    """#504 (Holga-referencia): a Holga anizotrop sugarai (`0,5·R` és
    `0,4·R`) tengelyenként KÜLÖN vágandók a 255-ös korláttal — a referencia
    illesztése szerint a `255/255` jobban illeszkedik (RMS 0,112), mint az
    arányt megtartó `255/204` (RMS 0,137). A Holga-hívás
    (`glimmer_creative.apply_holga`) a `clamp_glow_radius`-t xblur-re és
    yblur-re KÜLÖN-KÜLÖN hívja — ez a teszt ezt a hívási mintát rögzíti."""

    def test_nagy_kepen_mindket_tengely_kulon_255re_vagva(self):
        # 2560×1702-es képen (a referencia mérete): xblur=0,5·1280=640,
        # yblur=0,4·1280=512 — mindkettő a korlát fölött, de nem egyenlő
        # egymással, tehát ha egy közös (pl. a nagyobbik) értéket vágnánk,
        # az arányt megtartva 255/204-et adna, NEM 255/255-öt.
        outer_r = max(2560, 1702) / 2.0
        xblur_raw = 0.5 * outer_r
        yblur_raw = 0.4 * outer_r
        xblur = g.clamp_glow_radius(xblur_raw)
        yblur = g.clamp_glow_radius(yblur_raw)
        assert xblur == g.GLOW_RADIUS_MAX
        assert yblur == g.GLOW_RADIUS_MAX
        # a rossz (arány-megtartó) eredmény 255/204 lenne — ellenőrizzük,
        # hogy NEM azt kapjuk:
        assert yblur != pytest.approx(xblur * (yblur_raw / xblur_raw))


class TestBwTint:
    """#504 (Holga-referencia): a `BW(filtercolor=...)` NEM színez, hanem a
    szürkítés Rec.601-csatornasúlyait modulálja a `color`-ral — a Picasa
    Holga-kimenete minden mért képponton R=G=B. A korábbi implementáció
    (`ki = luma/255 · color`) SZÍNES kimenetet adott — ez volt a #504 hibája,
    nem a csatornasorrend (#510 tévedett)."""

    def test_kimenet_szurke_minden_pixelen(self):
        rng = np.random.default_rng(3)
        img = rng.integers(0, 255, size=(16, 16, 3), dtype=np.uint8)
        result = g.bw_tint(img, (255, 102, 102))
        assert np.all(result[..., 0] == result[..., 1])
        assert np.all(result[..., 1] == result[..., 2])

    def test_sulyok_a_referencia_kepletnek_megfeleloen(self):
        """A `0xff6666` (255,102,102) szín melletti effektív súlyok a
        referencia-méréssel egyeznek: R 0,516 / G 0,405 / B 0,079 (2 tizedes
        tűréssel) — `w_c = luma_c·szín_c / Σ(luma_k·szín_k)`."""
        # Tiszta piros/zöld/kék síkokon a bw_tint eredménye pontosan a
        # hozzá tartozó súly (255-tel szorozva), mert a másik két csatorna
        # bemenete nulla.
        red_plane = np.zeros((1, 1, 3), dtype=np.uint8)
        red_plane[0, 0, 0] = 255
        green_plane = np.zeros((1, 1, 3), dtype=np.uint8)
        green_plane[0, 0, 1] = 255
        blue_plane = np.zeros((1, 1, 3), dtype=np.uint8)
        blue_plane[0, 0, 2] = 255

        color = (255, 102, 102)
        red_w = float(g.bw_tint(red_plane, color)[0, 0, 0]) / 255.0
        green_w = float(g.bw_tint(green_plane, color)[0, 0, 0]) / 255.0
        blue_w = float(g.bw_tint(blue_plane, color)[0, 0, 0]) / 255.0

        assert red_w == pytest.approx(0.516, abs=0.02)
        assert green_w == pytest.approx(0.405, abs=0.02)
        assert blue_w == pytest.approx(0.079, abs=0.02)

    def test_semleges_szinnel_visszaadja_a_rec601_lumat(self):
        """Ha `color` mindhárom csatornája egyenlő (pl. fehér), a súlyok a
        sima Rec.601-re egyszerűsödnek — nincs modulálás."""
        rng = np.random.default_rng(4)
        img = rng.integers(0, 255, size=(8, 8, 3), dtype=np.uint8)
        result = g.bw_tint(img, (255, 255, 255))
        image_f = img.astype(np.float32)
        expected = g.luma(image_f)
        np.testing.assert_allclose(
            result[..., 0].astype(np.float32), np.clip(np.rint(expected), 0, 255), atol=1.0
        )


class TestNoiseAndGradient:
    def test_zaj_determinisztikus(self, image):
        first = g.apply_noise(image, seed=5, low=0, high=50, grayscale=True, blend_alpha=1.0, blend_mode="multiply")
        second = g.apply_noise(image, seed=5, low=0, high=50, grayscale=True, blend_alpha=1.0, blend_mode="multiply")
        np.testing.assert_array_equal(first, second)

    def test_gradient_map_vegpontok(self):
        black = np.zeros((4, 4, 3), dtype=np.uint8)
        white = np.full((4, 4, 3), 255, dtype=np.uint8)
        colors = ((10, 20, 30), (200, 210, 220))
        np.testing.assert_array_equal(g.gradient_map(black, colors)[0, 0], np.array([10, 20, 30]))
        np.testing.assert_array_equal(g.gradient_map(white, colors)[0, 0], np.array([200, 210, 220]))

    def test_hsv_gradient_map_alakhelyes(self, image):
        stops = ((0.0, 240.0, 100.0, 50.0), (255.0, 0.0, 100.0, 50.0))
        result = g.hsv_gradient_map(image, stops)
        assert result.shape == image.shape and result.dtype == np.uint8


class TestCircularGradientMask:
    def test_belul_nulla_kivul_egy(self):
        mask = g.circular_gradient_mask(40, 40, 5.0, 15.0)
        assert mask[20, 20] == 0.0
        assert mask[0, 0] == 1.0

    def test_atmenet_a_kettobetween(self):
        mask = g.circular_gradient_mask(40, 40, 5.0, 15.0)
        assert 0.0 < mask[20, 27] < 1.0


class TestFrameOps:
    def test_add_ring_novel(self, image):
        result = gf.add_ring(image, 10.0, (255, 255, 255))
        assert result.shape[0] > image.shape[0]
        assert result.shape[1] > image.shape[1]

    def test_add_ring_nulla_valtozatlan(self, image):
        result = gf.add_ring(image, 0.0, (255, 255, 255))
        np.testing.assert_array_equal(result, image)

    def test_round_corners_sarok_szinnel_tolt(self):
        image = np.zeros((40, 40, 3), dtype=np.uint8)
        result = gf.round_corners(image, 10.0, (255, 255, 255))
        assert tuple(result[0, 0]) == (255, 255, 255)
        assert tuple(result[20, 20]) == (0, 0, 0)

    def test_draw_drop_shadow_novel(self, image):
        result = gf.draw_drop_shadow(image, (0, 0, 0), (255, 255, 255), 4.0, 90.0, 10.0, fade=30.0)
        assert result.shape[0] > image.shape[0] and result.shape[1] > image.shape[1]

    def test_rotate_with_pad_novel(self, image):
        result = gf.rotate_with_pad(image, 10.0, (255, 255, 255))
        assert result.shape[0] >= image.shape[0] and result.shape[1] >= image.shape[1]

    def test_rotate_zero_megtartja_meretet(self, image):
        result = gf.rotate_with_pad(image, 0.0, (255, 255, 255))
        assert result.shape == image.shape
