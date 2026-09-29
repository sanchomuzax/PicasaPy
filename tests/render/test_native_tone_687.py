"""A natív tónus-magok (#687): szinthúzás, kontraszt, gamma, színhőmérséklet.

A modellek a `docs/specs/picasa-native-filter-workers.md` 2.2–2.5 pontjában
rögzített, DEKOMPILÁLT munkafüggvényekből valók — nem illesztett közelítések.
Ezek a tesztek a képletek horgonyértékeit és az azonosság-eseteket őrzik; a
valódi Picasa-kimenettel való egyezést a #685 mérőszettje mutatta ki (a mért
ΔE-k az egyes `apply_*` docstringjében).
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from picasapy.render.native_tone import (
    NATIVE_LUT_FULL,
    apply_gamma,
    apply_native_contrast,
    apply_native_levels,
    native_contrast_lut,
    native_gamma_lut,
    native_level_lut,
)


@pytest.fixture
def ramp() -> np.ndarray:
    """0..255 vízszintes rámpa, mindhárom csatornán azonos."""
    levels = np.arange(256, dtype=np.uint8).reshape(1, 256, 1)
    return np.repeat(np.repeat(levels, 4, axis=0), 3, axis=2)


class TestNativeLevelLut:
    def test_semleges_parameterek_azonossagot_adnak(self):
        lut = native_level_lut(0.0, 1.0, 1.0)
        assert np.array_equal(lut, np.arange(256) * 256)

    def test_a_teljes_kiteres_a_65280(self):
        lut = native_level_lut(0.0, 1.0, 1.0)
        assert int(lut[255]) == NATIVE_LUT_FULL == 0xFF00

    def test_feketepont_eltolas_vag(self):
        # black = 0,5 → a 128 alatti szintek mind 0-ra esnek
        lut = native_level_lut(0.5, 1.0, 1.0)
        assert int(lut[127]) == 0
        assert int(lut[255]) == NATIVE_LUT_FULL

    def test_feherpont_skalazas_kifeszit(self):
        # white = 0,5 → a 128 fölötti szintek telítenek
        lut = native_level_lut(0.0, 0.5, 1.0)
        assert int(lut[128]) == NATIVE_LUT_FULL
        assert int(lut[64]) == pytest.approx(NATIVE_LUT_FULL / 2, abs=300)

    def test_degeneralt_par_eseten_a_skala_1(self):
        # white == black → a natív kód 1,0-s skálával megy tovább
        lut = native_level_lut(0.5, 0.5, 1.0)
        assert int(lut[255]) == NATIVE_LUT_FULL - int(round(0.5 * NATIVE_LUT_FULL))

    def test_gamma_a_feketepont_elott_hat(self):
        # invG = 1/gamma; gamma > 1 → világosít
        lut = native_level_lut(0.0, 1.0, math.e)
        assert int(lut[64]) > 64 * 256

    def test_invertalt_par_eseten_teljes_feher(self):
        """#3418: `black > white` (a feketepont a fehérpont FÖLÖTT) → a
        teljes LUT a maximumra (0xFF00) ugrik, nem invertált rámpát ad.

        Mérve a 684-es golden mérőkészlet `finetune__max`/`finetune2__max`
        esetén (Shadows=1,0, Highlights=0,5 → black=1,0, white=0,5): a
        képlet naiv (invertált-rámpás) kiterjesztése ΔE=43-47-et adott a
        valódi Picasa-exporthoz képest, a teljes-fehér modell ΔE=3,4-3,7-et.
        """
        lut = native_level_lut(1.0, 0.5, 1.0)
        assert np.array_equal(lut, np.full(256, NATIVE_LUT_FULL, dtype=np.int64))


class TestNativeContrastLut:
    def test_semleges_kontraszt_azonossag(self):
        assert np.array_equal(native_contrast_lut(0.0, 0.0, 1.0), np.arange(256) * 256)

    def test_a_kozeppont_helyben_marad(self):
        for contrast in (-0.5, -0.2, 0.2, 0.5):
            lut = native_contrast_lut(contrast, 0.0, 1.0)
            assert int(lut[128]) == 32768

    def test_pozitiv_kontraszt_szethuz(self):
        lut = native_contrast_lut(0.5, 0.0, 1.0)
        assert int(lut[64]) < 64 * 256
        assert int(lut[192]) > 192 * 256

    def test_negativ_kontraszt_osszehuz(self):
        lut = native_contrast_lut(-0.5, 0.0, 1.0)
        assert int(lut[0]) > 0
        assert int(lut[255]) < NATIVE_LUT_FULL

    def test_a_fenyero_additiv(self):
        # brightness · 25600, azaz ±1 ≈ ±100 nyolcbites szint
        lut = native_contrast_lut(0.0, 0.1, 1.0)
        assert int(lut[100]) - 100 * 256 == pytest.approx(2560, abs=1)


class TestApplyNativeLevels:
    def test_semleges_parameter_byte_azonos(self, ramp):
        assert np.array_equal(apply_native_levels(ramp, 0.0, 1.0), ramp)

    def test_a_bemenetet_nem_mutalja(self, ramp):
        eredeti = ramp.copy()
        apply_native_levels(ramp, 0.25, 0.75)
        assert np.array_equal(ramp, eredeti)

    def test_szuk_savra_huzas_kifeszit(self, ramp):
        result = apply_native_levels(ramp, 0.25, 0.75)
        assert int(result[0, 64, 0]) == 0
        assert int(result[0, 192, 0]) == 255

    def test_a_kimenet_csonkol_nem_kerekit(self, ramp):
        # a natív alkalmazó `v >> 8`-cal veszi ki a bájtot: a 0,75-ös
        # fehérpontnál a 191-es szint 65152-t kap, ami 254-re CSONKOL
        # (kerekítéssel 255 lenne)
        assert int(apply_native_levels(ramp, 0.25, 0.75)[0, 191, 0]) == 254

    def test_uint8_kimenet(self, ramp):
        assert apply_native_levels(ramp, 0.1, 0.9).dtype == np.uint8


class TestApplyNativeContrast:
    def test_semleges_azonossag(self, ramp):
        assert np.array_equal(apply_native_contrast(ramp, 0.0), ramp)

    def test_pozitiv_kontraszt_sotetit_es_vilagosit(self, ramp):
        result = apply_native_contrast(ramp, 0.4)
        assert int(result[0, 64, 0]) < 64
        assert int(result[0, 192, 0]) > 192


class TestApplyGamma:
    def test_nulla_szint_azonossag(self, ramp):
        assert np.array_equal(apply_gamma(ramp, 0.0), ramp)

    def test_pozitiv_szint_vilagosit(self, ramp):
        result = apply_gamma(ramp, 1.0)
        assert int(result[0, 64, 0]) > 64

    def test_negativ_szint_sotetit(self, ramp):
        result = apply_gamma(ramp, -1.0)
        assert int(result[0, 64, 0]) < 64

    def test_a_szelek_helyben_maradnak(self, ramp):
        result = apply_gamma(ramp, 1.0)
        assert int(result[0, 0, 0]) == 0
        assert int(result[0, 255, 0]) == 255

    def test_a_szint_exponenskent_exp_minusz_szint(self, ramp):
        # a natív burkoló exp(szint)-et ad át gammaként, a LUT 1/gamma-val
        # emel hatványra → a kitevő exp(−szint)
        level = 0.4
        expected = int(
            round(255.0 * (100 / 255.0) ** math.exp(-level))
        )
        assert int(apply_gamma(ramp, level)[0, 100, 0]) == pytest.approx(
            expected, abs=1
        )

    def test_nincs_dither_a_teljes_rampa_a_tablaval_egyezik(self, ramp):
        """#3939: a `gamma` a 8 bites `native_gamma_lut`-on fut, dither
        NÉLKÜL — a teljes rámpa kimenete pontosan a táblázott LUT, nem
        ±1-gyel zajos (ahogy a 16 bites, ditheres szinthúzón futna)."""
        level = 0.1618
        g = math.exp(level)
        expected = native_gamma_lut(g)[np.arange(256, dtype=np.uint8)]
        result = apply_gamma(ramp, level)
        assert np.array_equal(result[0, :, 0], expected)
        assert np.array_equal(result[0, :, 1], expected)
        assert np.array_equal(result[0, :, 2], expected)


class TestNativeGammaLut:
    """A `0x00aa40a0` 8 bites gamma-tábla (#3939, spec 5.3/b).

    ```
    g    = f32(exp(szint)); invG = f32(1 / g)
    LUT[i] = rint(f32(pow(f32(i · (1/255)), invG) · 255))
    ```

    A horgonyértékek a jegy „Kész, ha” listájából valók."""

    def test_szint_minusz_1_lut26_1_lut25_0(self):
        g = math.exp(-1.0)
        lut = native_gamma_lut(g)
        assert int(lut[26]) == 1
        assert int(lut[25]) == 0

    def test_szint_plusz_1_lut3_50(self):
        g = math.exp(1.0)
        lut = native_gamma_lut(g)
        assert int(lut[3]) == 50

    def test_semleges_azonossag(self):
        lut = native_gamma_lut(1.0)
        assert np.array_equal(lut, np.arange(256, dtype=np.uint8))

    def test_szelek_helyben_maradnak(self):
        for g in (0.1, 0.5, 1.0, 2.0, 5.0):
            lut = native_gamma_lut(g)
            assert int(lut[0]) == 0
            assert int(lut[255]) == 255

    def test_uint8_kimenet(self):
        assert native_gamma_lut(0.5).dtype == np.uint8

    def test_nem_pozitiv_gamma_hibat_dob(self):
        with pytest.raises(ValueError):
            native_gamma_lut(0.0)
        with pytest.raises(ValueError):
            native_gamma_lut(-1.0)

    def test_nem_veges_g_hibat_dob(self):
        """NaN, vagy ami float32-ben 0-ra/végtelenre kerekül — a #3944
        átnézése szerint az őrnek a float32-re CSONKOLT `g`-t kell néznie,
        nem a bejövő double-t."""
        with pytest.raises(ValueError):
            native_gamma_lut(float("nan"))
        with pytest.raises(ValueError):
            # a legkisebb pozitív double is 0.0-ra kerekül float32-ben
            native_gamma_lut(1e-46)

    @pytest.mark.parametrize(
        ("szint", "index", "vart"),
        [
            (-0.641, 205, 168),
            (-0.623, 122, 64),
            (0.748, 193, 223),
        ],
    )
    def test_1_per_255_dupla_pontossagu_allando(self, szint, index, vart):
        """#3944 átnézés (J1): `[0xcf4138]` = 1/255 **dupla** pontosságú —
        az `i · (1/255)` szorzatot dupla pontosságban kell számolni, és
        csak az EREDMÉNYT kerekíteni float32-re a `pow` előtt. Ha a
        szorzás sorrendje megfordul (előbb `i` kerekül float32-re, utána
        szorzunk egy float32 állandóval), ez a három érték eggyel eltér."""
        g = math.exp(szint)
        lut = native_gamma_lut(g)
        assert int(lut[index]) == vart

    @pytest.mark.parametrize(
        ("szint", "index", "vart"),
        [
            (0.861, 141, 198),
            (-0.1194, 206, 200),
        ],
    )
    def test_a_vegso_kerekites_legkozelebbi_paros(self, szint, index, vart):
        """#3944 átnézés (J2/B): a `fistp` a legközelebbi egészre kerekít
        (kötött esetben a páros felé, azaz `rint`), NEM `floor(x + 0,5)`
        (ami félúton mindig felfelé kerekítene). A második eset (`szint =
        −0,1194`) pontosan `x,5`-re esik: `rint` a páros 200-at adja,
        `floor(x + 0,5)` a 201-et adná."""
        g = math.exp(szint)
        lut = native_gamma_lut(g)
        assert int(lut[index]) == vart

    @pytest.mark.parametrize(
        ("szint", "index", "vart"),
        [
            (0.305, 79, 108),
            (0.415, 42, 78),
            (0.1441, 90, 104),
        ],
    )
    def test_koztes_lepesek_float32_kerekitese_szamit(self, szint, index, vart):
        """#3944 átnézés (J2/C): a hatványozás előtti szorzat ÉS a `· 255`
        utáni szorzat is float32-re kerekül a `pow`/`rint` előtt (a natív
        `fstp dword`). Ha a teljes számítást tiszta float64-ben végezzük
        (a köztes float32-lépések nélkül), ez a három érték eltér."""
        g = math.exp(szint)
        lut = native_gamma_lut(g)
        assert int(lut[index]) == vart
