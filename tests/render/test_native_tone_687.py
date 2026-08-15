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
