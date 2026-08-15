"""A #687-ben bekötött natív szűrők a `filters=` láncban.

A #685 mérőszettje kimutatta, hogy nyolc olyan szűrőt, amit az eredeti
Picasa ténylegesen végrehajt, mi NÉMÁN kihagytunk. Ezek a tesztek azt
őrzik, hogy (a) a lánc immár renderel rájuk, (b) a paraméter-leképezés a
dekompilált burkolókat követi, és (c) az öt tétlen bejegyzés jelölve van.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import (
    KNOWN_UNRENDERED_OPS,
    MEASURED_IDLE_OPS,
    apply_filters,
    can_render_filter,
)
from picasapy.render.native_colortemp import apply_native_colortemp
from picasapy.render.native_tone import apply_native_contrast, apply_native_levels
from picasapy.render.tone import apply_fill

#: A #685-ben mérten ÉLŐ, de renderelő nélküli nyolc szűrő.
ELO_SZUROK = (
    "triple2=1,0.500000,0.500000,1.000000;",
    "colortemp=1,0.125000,0.500000;",
    "triple3=1,0.500000,0.240000,0.240000;",
    "backlight=1,0.250000;",
    "gamma=1,0.161800;",
    "contrast=1,0.100000;",
    "autocontrast=1;",
)


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(687)
    return rng.integers(20, 235, size=(64, 96, 3), dtype=np.uint8)


class TestMindenElioSzuroRenderel:
    @pytest.mark.parametrize("chain", ELO_SZUROK)
    def test_nem_kerul_a_kihagyott_listaba(self, sample, chain):
        report = apply_filters(sample, parse_filters(chain))
        assert report.skipped == ()

    @pytest.mark.parametrize("chain", ELO_SZUROK)
    def test_tenylegesen_valtoztat_a_kepen(self, sample, chain):
        report = apply_filters(sample, parse_filters(chain))
        assert not np.array_equal(report.image, sample)

    @pytest.mark.parametrize("chain", ELO_SZUROK)
    def test_can_render_filter_igazat_ad(self, chain):
        name = chain.split("=", 1)[0]
        assert can_render_filter(name)

    @pytest.mark.parametrize("chain", ELO_SZUROK)
    def test_mar_nem_szerepel_a_kalibralatlanok_kozott(self, chain):
        name = chain.split("=", 1)[0]
        assert name not in KNOWN_UNRENDERED_OPS


class TestParameterLekepezes:
    def test_backlight_a_deritofennyel_azonos(self, sample):
        report = apply_filters(sample, parse_filters("backlight=1,0.400000;"))
        assert np.array_equal(report.image, apply_fill(sample, 0.4))

    def test_contrast_a_natív_kontraszt_maggal_azonos(self, sample):
        report = apply_filters(sample, parse_filters("contrast=1,0.300000;"))
        assert np.array_equal(report.image, apply_native_contrast(sample, 0.3))

    def test_colortemp_sorrendje_hidegmeleg_majd_fehervaltas(self, sample):
        report = apply_filters(sample, parse_filters("colortemp=1,0.500000,1.000000;"))
        assert np.array_equal(
            report.image, apply_native_colortemp(sample, 0.5, 1.0)
        )

    def test_triple2_deritofeny_majd_szinthuzas(self, sample):
        # p0 = Derítőfény, p1 = Feketepont, p2 = Fehérpont
        report = apply_filters(
            sample, parse_filters("triple2=1,0.500000,0.200000,0.900000;")
        )
        expected = apply_native_levels(apply_fill(sample, 0.5), 0.2, 0.9)
        assert np.array_equal(report.image, expected)

    def test_triple3_a_kiemeleseket_feherpontta_forditja(self, sample):
        # p1 = Kiemelések → fehérpont = 1 − p1; p2 = Árnyékok → feketepont
        report = apply_filters(
            sample, parse_filters("triple3=1,0.500000,0.240000,0.100000;")
        )
        expected = apply_native_levels(apply_fill(sample, 0.5), 0.1, 0.76)
        assert np.array_equal(report.image, expected)

    def test_triple_deritofeny_majd_kontraszt(self, sample):
        # p0 = Fényerő, p1 = Kontraszt, p2 = Derítőfény
        report = apply_filters(
            sample, parse_filters("triple=1,0.100000,0.200000,0.500000;")
        )
        expected = apply_native_contrast(
            apply_fill(sample, 0.5), contrast=0.2, brightness=0.1
        )
        assert np.array_equal(report.image, expected)


class TestAzonossagEsetek:
    def test_triple3_csupa_nulla_valtozatlan(self, sample):
        report = apply_filters(sample, parse_filters("triple3=1,0,0,0;"))
        assert np.array_equal(report.image, sample)

    def test_triple2_semleges_allasa_valtozatlan(self, sample):
        # a natív burkoló „nincs teendő" ága: fill = 0, fekete = 0, fehér = 1
        report = apply_filters(sample, parse_filters("triple2=1,0,0,1.000000;"))
        assert np.array_equal(report.image, sample)

    def test_triple_csupa_nulla_valtozatlan(self, sample):
        report = apply_filters(sample, parse_filters("triple=1,0,0,0;"))
        assert np.array_equal(report.image, sample)

    def test_backlight_nullan_valtozatlan(self, sample):
        report = apply_filters(sample, parse_filters("backlight=1,0.000000;"))
        assert np.array_equal(report.image, sample)

    def test_gamma_nullan_valtozatlan(self, sample):
        report = apply_filters(sample, parse_filters("gamma=1,0.000000;"))
        assert np.array_equal(report.image, sample)

    def test_contrast_nullan_valtozatlan(self, sample):
        report = apply_filters(sample, parse_filters("contrast=1,0.000000;"))
        assert np.array_equal(report.image, sample)


class TestTartomanyValidacio:
    def test_kilogo_kontraszt_vagva_fut(self, sample):
        report = apply_filters(sample, parse_filters("contrast=1,5.000000;"))
        assert report.skipped == ()
        assert len(report.range_warnings) == 1
        vagott = apply_filters(sample, parse_filters("contrast=1,0.500000;"))
        assert np.array_equal(report.image, vagott.image)

    def test_kilogo_gamma_vagva_fut(self, sample):
        report = apply_filters(sample, parse_filters("gamma=1,9.000000;"))
        assert report.skipped == ()
        assert len(report.range_warnings) == 1


class TestMertenTetlenBejegyzesek:
    #: A #685 mérésben a Picasa MAGA sem változtatott ezeken (ΔE ≤ 1,0).
    TETLEN = ("blur", "colorfix", "whitept")

    @pytest.mark.parametrize("name", TETLEN)
    def test_a_tetlen_nevek_jelolve_vannak(self, name):
        assert name in MEASURED_IDLE_OPS

    @pytest.mark.parametrize("name", TETLEN)
    def test_a_lanc_figyelmeztet_rajuk(self, sample, name):
        report = apply_filters(sample, parse_filters(f"{name}=1,0.500000;"))
        assert report.skipped == (name,)
        assert len(report.legacy_warnings) == 1
        assert name in report.legacy_warnings[0]

    def test_a_focalpixelate_marad_halott_legacy(self, sample):
        # #567: ennél a natív regiszterben SINCS feldolgozó — más ok, más üzenet
        report = apply_filters(sample, parse_filters("focalpixelate=1,;"))
        assert report.skipped == ("focalpixelate",)
        assert "halott" in report.legacy_warnings[0]

    def test_a_tetlen_nevek_nem_keverednek_a_halottakkal(self):
        from picasapy.render.chain import DEAD_LEGACY_OPS

        assert not (MEASURED_IDLE_OPS & DEAD_LEGACY_OPS)


class TestOsszetettLanc:
    def test_tobb_uj_szuro_egymas_utan_lefut(self, sample):
        report = apply_filters(
            sample,
            parse_filters("contrast=1,0.200000;gamma=1,0.300000;backlight=1,0.300000;"),
        )
        assert report.skipped == ()
        assert not np.array_equal(report.image, sample)

    def test_a_hibas_parameteru_bejegyzes_nem_dobja_el_a_lancot(self, sample):
        report = apply_filters(
            sample, parse_filters("contrast=1,zzz;gamma=1,0.300000;")
        )
        assert report.skipped == ("contrast",)
        assert not np.array_equal(report.image, sample)
