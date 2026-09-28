"""#381: a közös Glimmer-primitívek (`glimmer_ops.py`/`glimmer_frame_ops.py`)
egységtesztjei — görbe-interpoláció, blend-módok, Fade-szabály, maszkolt
keverés, belső ragyogás, zaj, gradiens-leképezés, keret-primitívek.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render import glimmer_frame_ops as gf
from picasapy.render import belso_ragyogas as br
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


class TestDobozParameterek:
    """#3827: a `0x00bc5360` dobozparaméterei a jegy két kiszámolt példáján."""

    def test_33_33_egy_33_szeles_egyenletes_doboz(self):
        s, a, r, div = br.doboz_parameterek(33.33)
        assert (s, a, r, div) == (1, 0, 17, 66)
        sulyok = [a] + [1 << s] * (2 * r - 1) + [a]
        nem_nulla = [w for w in sulyok if w]
        assert len(nem_nulla) == 33
        assert len(set(nem_nulla)) == 1
        assert sum(sulyok) == div

    def test_10_5_tort_sulyu_szelekkel(self):
        assert br.doboz_parameterek(10.5) == (3, 6, 5, 84)

    def test_a_perem_szelessege(self):
        assert br.peremsugar(33.33) == 52
        assert br.peremsugar(253.0) == 255


def _referencia_maszk(magas, szeles, bx, by, q=3):
    """Független újralevezetés (386. kör): kibővített puffer 255-ös peremmel,
    kumulált összegű dobozmenetek, 255-ös pótlás a puffer szélén."""
    import math

    def menet(m, b, tengely):
        s, a, r, div = br.doboz_parameterek(b)
        p = np.moveaxis(m, tengely, -1).astype(np.int64)
        n = p.shape[-1]
        pp = np.pad(p, [(0, 0)] * (p.ndim - 1) + [(r, r)], constant_values=255)
        c = np.concatenate([np.zeros(p.shape[:-1] + (1,), np.int64), np.cumsum(pp, axis=-1)], -1)
        i = np.arange(n) + r
        belso = c[..., i + r] - c[..., i - r + 1]
        szel = pp[..., i - r] + pp[..., i + r]
        return np.moveaxis((a * szel + (belso << s)) // div, -1, tengely)

    bx, by = min(bx, 253.0), min(by, 253.0)
    rx = min(255, int(math.ceil((bx - 1) * 0.5) * q + 1))
    ry = min(255, int(math.ceil((by - 1) * 0.5) * q + 1))
    m = np.full((magas + 2 * ry, szeles + 2 * rx), 255, np.int64)
    m[ry:ry + magas, rx:rx + szeles] = 0
    bxx, byy = min(bx, m.shape[1] * 0.5), min(by, m.shape[0] * 0.5)
    for _ in range(q):
        if bxx > 1.0:
            m = menet(m, bxx, 1)
    for _ in range(q):
        if byy > 1.0:
            m = menet(m, byy, 0)
    return m[ry:ry + magas, rx:rx + szeles].astype(np.uint8)


class TestBelsoRagyogasMaszk:
    """#3827: a maszk bitre egyezik a kibővített pufferes újralevezetéssel
    (a mi utunk konstans 255-ös peremmel és oszlop-egyedítéssel számol)."""

    @pytest.mark.parametrize(
        "magas,szeles,bx,by",
        [
            (40, 60, 9.6, 9.6),
            (61, 47, 33.33, 20.5),
            (120, 180, 64.0, 70.7),
            (7, 5, 30.0, 30.0),
            (200, 90, 253.0, 120.25),
            (30, 30, 1.0, 0.0),
        ],
    )
    def test_bitre_egyezik_a_referenciaval(self, magas, szeles, bx, by):
        sajat = br.ragyogas_maszk(magas, szeles, bx, by)
        np.testing.assert_array_equal(sajat, _referencia_maszk(magas, szeles, bx, by))

    def test_a_suly_8_8_as_fixpont(self):
        maszk = np.array([[0, 100, 180, 255]], dtype=np.uint8)
        # csonk(1,4·256) = 358: 100·358 >> 8 = 139, 180·358 >> 8 = 251, 255 → 255
        np.testing.assert_array_equal(br.ragyogas_suly(maszk, 1.4), [[0, 139, 251, 255]])
        np.testing.assert_array_equal(br.ragyogas_suly(maszk, 1.0), maszk)


class TestResizeColumnPlane:
    """#3827: a tömör oszlopalakú átméretezés bitre a `resize_plane`-t adja."""

    @pytest.mark.parametrize(
        "magas,szeles,cel_w,cel_h",
        [(50, 70, 131, 97), (50, 70, 70, 97), (50, 70, 40, 30), (61, 83, 100, 61), (5, 7, 400, 300)],
    )
    def test_bitre_egyezik(self, magas, szeles, cel_w, cel_h):
        rng = np.random.default_rng(magas * szeles)
        oszlopok = rng.integers(0, 256, size=(magas, 6), dtype=np.uint8)
        vissza = np.sort(rng.integers(0, 6, size=szeles))
        teljes = oszlopok[:, vissza]
        np.testing.assert_array_equal(
            g.resize_column_plane(oszlopok, vissza, cel_w, cel_h),
            g.resize_plane(teljes, cel_w, cel_h),
        )


class TestInnerGlow:
    def test_alfa_nulla_valtozatlan(self, image):
        result = br.inner_glow(image, (0, 0, 0), 10.0, 10.0, 1.4, alpha=0.0)
        np.testing.assert_array_equal(result, image)

    def test_nulla_blur_azonossag(self, image):
        np.testing.assert_array_equal(br.inner_glow(image, (0, 0, 0), 0.0, 0.0, 2.0), image)

    def test_szelek_sotetebbek_feher_alapon(self):
        white = np.full((40, 60, 3), 255, dtype=np.uint8)
        result = br.inner_glow(white, (0, 0, 0), 12.0, 12.0, 1.4)
        assert int(result[0, 30, 0]) < int(result[20, 30, 0])

    def test_teljes_felbontasu_ag_kepletre(self):
        """`p < 33,33`: `((256 − e)·S + e·G) >> 8`, a maszk a teljes képen."""
        rng = np.random.default_rng(3)
        kep = rng.integers(0, 256, size=(50, 70, 3), dtype=np.uint8)
        e = br.ragyogas_suly(_referencia_maszk(50, 70, 9.6, 9.6), 1.3).astype(np.int64)[..., None]
        vart = ((256 - e) * kep.astype(np.int64)) >> 8
        np.testing.assert_array_equal(br.inner_glow(kep, (0, 0, 0), 9.6, 9.6, 1.3), vart)

    def test_blend_alpha_a_lanc_keverojevel(self):
        """MuseumMatte: `k′ = csonk(α·256) − 1`, `(be·(255 − k′) + t·k′) >> 8`."""
        rng = np.random.default_rng(4)
        kep = rng.integers(0, 256, size=(40, 40, 3), dtype=np.uint8)
        teljes = br.inner_glow(kep, (0, 0, 0), 9.6, 9.6, 1.3).astype(np.int64)
        k = 178  # csonk(0,7·256) − 1
        vart = (kep.astype(np.int64) * (255 - k) + teljes * k) >> 8
        np.testing.assert_array_equal(br.inner_glow(kep, (0, 0, 0), 9.6, 9.6, 1.3, alpha=0.7), vart)

    def test_lekicsinyitett_ag_kepletre(self):
        """`p ≥ 33,33`: a súly a `csonk(f·W) × csonk(f·H)` pufferben, Mitchell-
        nagyítás, `⌊(G·a + S·(255 − a)) / 255⌋`."""
        rng = np.random.default_rng(5)
        kep = rng.integers(0, 256, size=(320, 480, 3), dtype=np.uint8)
        p = 35 * 0.02 * 480 / 4  # 84: a Vignette alap
        f = np.float32(br.blur_atvalto(p, 480.0))
        assert f < 1.0
        kis_w, kis_h = int(np.float32(f * np.float32(480))), int(np.float32(f * np.float32(320)))
        b = float(np.float32(f * np.float32(p)))
        a = br.ragyogas_suly(_referencia_maszk(kis_h, kis_w, b, b), 1.4)
        nagy = g.resize_plane(a, 480, 320).astype(np.int64)[..., None]
        vart = (255 * nagy + kep.astype(np.int64) * (255 - nagy)) // 255
        np.testing.assert_array_equal(br.inner_glow(kep, (255, 255, 255), p, p, 1.4), vart)

    def test_nagy_kepen_a_szel_sotetebb_a_kozepnel(self):
        """A Lomo 800 képpontos képen: a lekicsinyített ágon a ragyogás a
        közepet is érinti, de a szél a legsötétebb, és a kép nem fekszik be."""
        white = np.full((600, 800, 3), 255, dtype=np.uint8)
        p = 35.0 * 0.02 * 800 / 2.0  # a Lomo xblur-je
        result = br.inner_glow(white, (0, 0, 0), p, p, 1.1)[..., 0].astype(int)
        assert result[0, 0] < result[0, 400] < result[300, 400]
        assert result[300, 400] > 200


class TestBwTint:
    """#504 (Holga-referencia): a `BW(filtercolor=...)` NEM színez, hanem a
    szürkítés csatornasúlyait modulálja a `color`-ral — a Picasa
    Holga-kimenete minden mért képponton R=G=B. A korábbi implementáció
    (`ki = luma/255 · color`) SZÍNES kimenetet adott — ez volt a #504 hibája,
    nem a csatornasorrend (#510 tévedett).

    #3931 (a #3930 bináris-kutatás alapján): a súlyok Haeberli-alapúak (NEM
    Rec.601, ahogy a #504 mérésből illesztett modell feltételezte), és a
    natív kód FIXPONTOSAN alkalmazza őket
    (`c = trunc(w·2048 + 0,5)`, `Y = ((Σᵢ (cᵢ·xᵢ) >> 9) + 2) >> 2`) —
    ld. `docs/specs/filters-decoded.md`, „A színmátrix-alkalmazó fixpontos
    aritmetikája"."""

    def test_kimenet_szurke_minden_pixelen(self):
        rng = np.random.default_rng(3)
        img = rng.integers(0, 255, size=(16, 16, 3), dtype=np.uint8)
        result = g.bw_tint(img, (255, 102, 102))
        assert np.all(result[..., 0] == result[..., 1])
        assert np.all(result[..., 1] == result[..., 2])

    def test_sulyok_a_referencia_kepletnek_megfeleloen(self):
        """A `0xff6666` (255,102,102) szín melletti effektív súlyok a
        Haeberli-képletnek megfelelnek: R 0,527 / G 0,417 / B 0,056
        (`w_c = 0,3086/0,6094/0,0820 · szín_c / Σ`, #3930)."""
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

        assert red_w == pytest.approx(0.527, abs=0.02)
        assert green_w == pytest.approx(0.417, abs=0.02)
        assert blue_w == pytest.approx(0.056, abs=0.02)

    def test_semleges_szinnel_visszaadja_a_haeberli_lumat(self):
        """Ha `color` mindhárom csatornája egyenlő (pl. fehér), a súlyok a
        sima Haeberli-lumára egyszerűsödnek — nincs modulálás (a fixpontos
        kvantálás (`>>9`, `>>2`) miatt csatornánként legfeljebb 1 szintnyi
        eltéréssel a lebegőpontos lumához képest — mérve a legnagyobb
        eltérés 1)."""
        rng = np.random.default_rng(4)
        img = rng.integers(0, 255, size=(8, 8, 3), dtype=np.uint8)
        result = g.bw_tint(img, (255, 255, 255))
        image_f = img.astype(np.float32)
        expected = g._haeberli_luma(image_f)
        np.testing.assert_allclose(
            result[..., 0].astype(np.float32), np.clip(np.rint(expected), 0, 255), atol=1.0
        )

    def test_holga_szinnel_a_nativ_egyutthatok_1080_853_115(self):
        """#3931 „Kész, ha": a `0xff6666` szűrőszínre a fixpontos
        együtthatók pontosan `c = 1080 / 853 / 115` (a #3930 levezetése).

        A korábbi alak csak azt ellenőrizte, hogy egy tiszta csatornasíkon
        `R = G = B` — az együtthatók számértékét sosem nézte meg, tehát egy
        hibás `c` mellett is zöld maradt volna. Itt a `_bw_coefficients`
        segédfüggvényt hívjuk közvetlenül (#3933 review)."""
        assert g._bw_coefficients((255, 102, 102)) == (1080, 853, 115)

    def test_fixpontos_kerekites_eltero_a_lebegopontostol(self):
        """A fixpontos alkalmazó (`c = trunc(w·2048 + 0,5)`,
        `Y = ((Σ c·x >> 9) + 2) >> 2`) NEM ugyanaz, mint a lebegőpontos
        Haeberli-képlet (`rint(Σ w·x)`) — a teljes RGB-kockán 27%-ban
        eltérnek (#3933 review). E két megkülönböztető képpont buktatná,
        ha valaki a `bw_tint`-et lebegőpontosra írná vissza."""
        color = (255, 102, 102)

        pixel_98 = np.array([[[0, 0, 98]]], dtype=np.uint8)
        result_98 = g.bw_tint(pixel_98, color)
        assert int(result_98[0, 0, 0]) == 6

        pixel_187 = np.array([[[0, 0, 187]]], dtype=np.uint8)
        result_187 = g.bw_tint(pixel_187, color)
        assert int(result_187[0, 0, 0]) == 11

    @pytest.mark.parametrize(
        ("rgb", "expected"),
        [
            ((255, 0, 0), 134),
            ((0, 255, 0), 106),
            ((0, 0, 255), 14),
            ((200, 100, 50), 150),
            ((128, 128, 128), 128),
            ((255, 255, 255), 255),
        ],
    )
    def test_holga_pixelkepletek_a_jegybol(self, rgb, expected):
        """#3931 „Kész, ha": a hat rögzített képpont pontosan az elvárt
        szürkeszintre esik a `0xff6666` szűrőszínnel (`c = 1080/853/115`,
        `Y = ((Σᵢ (cᵢ·xᵢ) >> 9) + 2) >> 2`)."""
        pixel = np.array([[list(rgb)]], dtype=np.uint8)
        result = g.bw_tint(pixel, (255, 102, 102))
        assert int(result[0, 0, 0]) == expected
        assert int(result[0, 0, 1]) == expected
        assert int(result[0, 0, 2]) == expected


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


class TestSimpleColorMatrixSaturation:
    """#903: a `SimpleColorMatrix` telítettség-ága Haeberli-színmátrix,
    aszimmetrikus csúszkával — nem sima Rec.601 luma-tartó erősítés."""

    def test_pozitiv_oldal_haromszoros_k(self):
        """+20 → k = 1,60 (NEM 1,20 — a régi, hibás képlet)."""
        assert g._telitettseg_k(20.0) == pytest.approx(1.6)

    def test_negativ_oldal_egyszeres_k(self):
        """−25 → k = 0,75 (a negatív ág skálázása változatlan)."""
        assert g._telitettseg_k(-25.0) == pytest.approx(0.75)

    def test_hatarertekek(self):
        assert g._telitettseg_k(100.0) == pytest.approx(4.0)
        assert g._telitettseg_k(-100.0) == pytest.approx(0.0)

    def test_matrix_egzakt_kimenet_pozitiv_oldalon(self):
        """A teljes 3×3 Haeberli-mátrixot egy tetszőleges, nem szürke
        képponton, a képlettől FÜGGETLENÜL számolt várt értékkel vetjük
        össze — ha a mátrix vagy a súlyok eltérnek, ez elüt."""
        pixel = np.array([[[200, 100, 50]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, saturation=20.0)
        r, gr, b = 200.0, 100.0, 50.0
        k = 1.6
        w = 1.0 - k
        rw, gw, bw = w * 0.3086, w * 0.6094, w * 0.0820
        vart = np.array(
            [
                (k + rw) * r + gw * gr + bw * b,
                rw * r + (k + gw) * gr + bw * b,
                rw * r + gw * gr + (k + bw) * b,
            ]
        )
        np.testing.assert_allclose(result[0, 0].astype(np.float64), np.clip(np.round(vart), 0, 255), atol=1.0)

    def test_teljes_szurke_haeberli_sullyal_nem_rec601(self):
        """−100-nál a szürke a Haeberli-súlyokból jön, nem a Rec.601-ből —
        a kettő ezen a tiszta piroson jól szétválik."""
        pixel = np.array([[[255, 0, 0]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, saturation=-100.0)
        haeberli_gray = round(0.3086 * 255)
        rec601_gray = round(0.299 * 255)
        assert haeberli_gray != rec601_gray
        assert abs(int(result[0, 0, 0]) - haeberli_gray) <= 1
        assert result[0, 0, 0] == result[0, 0, 1] == result[0, 0, 2]

    def test_nincs_telitettseg_valtozatlan(self, image):
        result = g.simple_color_matrix(image, saturation=None)
        np.testing.assert_array_equal(result, image)


class TestSimpleColorMatrixContrast:
    """#904: 101 elemű táblázatos kontraszt-görbe, 63,5-ös forgáspont,
    korai kilépés kis `k`-nál."""

    def test_k_csuszka_35(self):
        assert 1.0 + g._kontraszt_gorbe(35.0) == pytest.approx(1.56, abs=0.01)

    def test_k_csuszka_50(self):
        assert 1.0 + g._kontraszt_gorbe(50.0) == pytest.approx(2.00, abs=0.005)

    def test_k_csuszka_100(self):
        assert 1.0 + g._kontraszt_gorbe(100.0) == pytest.approx(11.00, abs=0.005)

    def test_negativ_ag_zart_keplet(self):
        assert 1.0 + g._kontraszt_gorbe(-40.0) == pytest.approx(0.6)
        assert 1.0 + g._kontraszt_gorbe(-100.0) == pytest.approx(0.0)

    def test_forgaspont_63_5(self):
        """A forgáspont 63,5, NEM 128 — ugyanaz a szürke, más eredmény."""
        pixel = np.array([[[163, 163, 163]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, contrast=50.0)  # k = 2,00
        assert result[0, 0, 0] == 255  # 63.5 + 2*(163-63.5) = 262.5 -> vágva

    def test_kis_kontraszt_korai_kilepes_valtozatlan(self):
        """`|k − 1| < eps` esetén a művelet TÉTLEN — a kép bitre azonos marad."""
        rng = np.random.default_rng(3)
        image = rng.integers(20, 235, size=(6, 6, 3), dtype=np.uint8)
        result = g.simple_color_matrix(image, contrast=1e-8)
        np.testing.assert_array_equal(result, image)

    def test_negativ_100_egyenletes_szurke(self):
        rng = np.random.default_rng(5)
        image = rng.integers(0, 255, size=(8, 8, 3), dtype=np.uint8)
        result = g.simple_color_matrix(image, contrast=-100.0)
        assert result.std() == 0
        assert abs(int(result[0, 0, 0]) - 64) <= 1  # k=0 -> R' = 63.5

    def test_tabla_101_elemu(self):
        assert len(g._KONTRASZT_TABLA) == 101
        assert g._KONTRASZT_TABLA[0] == pytest.approx(0.0)
        assert g._KONTRASZT_TABLA[50] == pytest.approx(1.0)
        assert g._KONTRASZT_TABLA[100] == pytest.approx(10.0)

    def test_linearis_interpolacio_tablasorok_kozott(self):
        """0,5-ös csúszkánál a 0. és 1. táblaérték felezőpontja jön ki."""
        vart = (g._KONTRASZT_TABLA[0] + g._KONTRASZT_TABLA[1]) / 2.0
        assert g._kontraszt_gorbe(0.5) == pytest.approx(vart)


class TestSimpleColorMatrixBrightness:
    """#904: a fényerő közvetlenül adódik hozzá, nincs ×2,55 skálázás."""

    def test_nincs_255_szorzas(self):
        pixel = np.array([[[100, 100, 100]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, brightness=50.0)
        assert result[0, 0, 0] == 150

    def test_hatarnal_vagas(self):
        pixel = np.array([[[240, 240, 240]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, brightness=50.0)
        assert result[0, 0, 0] == 255

    def test_csuszka_100_fole_vagva(self):
        pixel = np.array([[[100, 100, 100]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, brightness=500.0)
        assert result[0, 0, 0] == 200  # clamp(500,-100,100) -> 100 -> 100+100


class TestSimpleColorMatrixLinked:
    """#904: `ContrastAndBrightnessLinked` — külön kódút, 127,5-ös
    forgásponttal, a `Brightness` a kontraszttal súlyozva hat."""

    def test_forgaspont_127_5(self):
        pixel = np.array([[[227, 227, 227]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, contrast=50.0, linked=True)  # k=2
        # t = (k+1)*127.5*0/100 + (127.5 - k*127.5) = 127.5-255 = -127.5
        # R' = 2*227 - 127.5 = 326.5 -> vágva
        assert result[0, 0, 0] == 255

    def test_kulonbozik_a_kulon_agtol(self):
        # `brightness=10`-nél a két ág kerekítve véletlenül ugyanazt az
        # egész pixelt adja (#3735: 184,125 vs 184,3125) — `brightness=20`
        # már egyértelműen szétválik.
        pixel = np.array([[[150, 150, 150]]], dtype=np.uint8)
        sep = g.simple_color_matrix(pixel, contrast=20.0, brightness=20.0, linked=False)
        linked = g.simple_color_matrix(pixel, contrast=20.0, brightness=20.0, linked=True)
        assert int(sep[0, 0, 0]) != int(linked[0, 0, 0])


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



def test_a_ragyogas_nem_veges_parameterre_valtozatlan() -> None:
    """Kézzel írt ini-ből jöhet inf/NaN: nem dob, a kép változatlan (#3827)."""
    from picasapy.render.belso_ragyogas import inner_glow

    kep = np.full((8, 8, 3), 120, dtype=np.uint8)
    for x, y, s in ((float("inf"), 5.0, 1.0), (5.0, float("nan"), 1.0), (5.0, 5.0, float("nan"))):
        np.testing.assert_array_equal(inner_glow(kep, (0, 0, 0), x, y, s), kep)


def test_a_ragyogas_paranyi_alfaja_sem_fordul_korbe() -> None:
    """1/256 alatti alfánál a k′ −1 lenne: a tábla nem fordulhat körbe
    (0 helyett 255), a kép gyakorlatilag változatlan (#3827, PR-átnézés)."""
    from picasapy.render.belso_ragyogas import inner_glow

    kep = np.full((16, 16, 3), 200, dtype=np.uint8)
    ki = inner_glow(kep, (255, 255, 255), 6.0, 6.0, 1.0, alpha=0.001)
    assert int(np.abs(ki.astype(int) - kep.astype(int)).max()) <= 1
