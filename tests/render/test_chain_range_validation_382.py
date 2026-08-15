"""#382 2. pont: renderelő-oldali tartomány-validáció.

A `.picasa.ini` PARSZER szintjén nincs szigorítás (round-trip elv) — ezek a
tesztek a RENDERELŐ (`apply_filters`) oldali softclamp-viselkedést őrzik: a
tartományon kívüli paraméter a tartományra vágva fut le, és a kihagyás a
`ChainReport.range_warnings`-ban jelenik meg (a `skipped` mintájára), a
kép pedig NEM esik ki a `skipped` listába.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(19)
    return rng.integers(30, 220, size=(48, 64, 3), dtype=np.uint8)


class TestSatRange:
    def test_tartomanyon_beluli_sat_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(sample, parse_filters("sat=1,0.500000;"))
        assert report.range_warnings == ()
        assert report.skipped == ()

    def test_tartomanyon_kivuli_sat_vagva_fut_es_figyelmeztet(self, sample):
        # sat ∈ [-1, 1] — 5.0 kilóg
        report = apply_filters(sample, parse_filters("sat=1,5.000000;"))
        assert report.skipped == ()
        assert len(report.range_warnings) == 1
        assert "sat" in report.range_warnings[0].casefold()
        # a vágott érték (1.0) tényleg lefutott — nem a nyers 5.0-val
        clamped_only, _ = apply_filters(sample, parse_filters("sat=1,1.000000;"))
        assert np.array_equal(report.image, clamped_only)


class TestTiltRange:
    def test_tartomanyon_kivuli_tilt_vagva_fut(self, sample):
        # tilt szöge ∈ [-1, 1] — 3.0 kilóg, [-1,1]-re vágva fut
        report = apply_filters(sample, parse_filters("tilt=1,3.000000,0.0;"))
        assert len(report.range_warnings) == 1
        assert "tilt" in report.range_warnings[0].casefold()


class TestFinetuneRanges:
    def test_finetune_v1_homerseklet_tartomanya_felig_akkora(self, sample):
        # finetune (v1) hőmérséklete [-0.5, 0.5] — 0.5 még pont belefér
        report = apply_filters(
            sample, parse_filters("finetune=1,0.0,0.0,0.0,,0.500000;")
        )
        assert report.range_warnings == ()

    def test_finetune_v1_homerseklet_kilogas(self, sample):
        report = apply_filters(
            sample, parse_filters("finetune=1,0.0,0.0,0.0,,0.800000;")
        )
        assert len(report.range_warnings) == 1
        assert "temperature" in report.range_warnings[0].casefold()

    def test_finetune2_homerseklet_tartomanya_duplaja(self, sample):
        # finetune2 (v2) hőmérséklete [-1, 1] — 0.8 itt még nem lóg ki
        report = apply_filters(
            sample, parse_filters("finetune2=1,0.0,0.0,0.0,,0.800000;")
        )
        assert report.range_warnings == ()

    def test_highlights_shadows_valodi_ui_tartomanya(self, sample):
        # highlights/shadows valódi UI-tartománya [0, 0.48], NEM [0, 1]
        report = apply_filters(sample, parse_filters("finetune2=1,0.0,0.9,0.9;"))
        assert len(report.range_warnings) == 2
        joined = " ".join(report.range_warnings).casefold()
        assert "highlights" in joined
        assert "shadows" in joined


class TestUnsharpRanges:
    def test_unsharp_v1_amount_felso_korlat_1(self, sample):
        report = apply_filters(sample, parse_filters("unsharp=1,2.000000;"))
        assert len(report.range_warnings) == 1
        assert "unsharp" in report.range_warnings[0].casefold()

    def test_unsharp2_amount_felso_korlat_3(self, sample):
        # unsharp2 felső korlátja 3.0 — a v1-nél még kilógó 2.0 itt belefér
        report = apply_filters(sample, parse_filters("unsharp2=1,2.000000;"))
        assert report.range_warnings == ()

    def test_unsharp2_amount_tenyleges_kilogas(self, sample):
        report = apply_filters(sample, parse_filters("unsharp2=1,5.000000;"))
        assert len(report.range_warnings) == 1


# --- #669: az irányított család (dir_*) és a linblur ----------------------


class TestDirSatRange:
    def test_tartomanyon_beluli_dir_sat_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(sample, parse_filters("dir_sat=1,0.500000,0.300000;"))
        assert report.range_warnings == ()
        assert report.skipped == ()

    def test_vizszintes_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        # horizontal ∈ [-1, 1] — 5.0 kilóg
        report = apply_filters(sample, parse_filters("dir_sat=1,5.000000,0.300000;"))
        assert report.skipped == ()
        assert len(report.range_warnings) == 1
        assert "dir_sat" in report.range_warnings[0].casefold()
        clamped_only, _ = apply_filters(
            sample, parse_filters("dir_sat=1,1.000000,0.300000;")
        )
        assert np.array_equal(report.image, clamped_only)

    def test_fuggoleges_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        # vertical ∈ [-1, 1] — -5.0 kilóg
        report = apply_filters(sample, parse_filters("dir_sat=1,0.300000,-5.000000;"))
        assert len(report.range_warnings) == 1
        assert "dir_sat" in report.range_warnings[0].casefold()


class TestDirBriteRange:
    def test_tartomanyon_beluli_dir_brite_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(
            sample, parse_filters("dir_brite=1,0.500000,0.300000;")
        )
        assert report.range_warnings == ()

    def test_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        report = apply_filters(sample, parse_filters("dir_brite=1,5.000000,0.0;"))
        assert len(report.range_warnings) == 1
        assert "dir_brite" in report.range_warnings[0].casefold()
        clamped_only, _ = apply_filters(sample, parse_filters("dir_brite=1,1.0,0.0;"))
        assert np.array_equal(report.image, clamped_only)


class TestDirSharpRange:
    def test_tartomanyon_beluli_dir_sharp_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(
            sample, parse_filters("dir_sharp=1,0.500000,0.300000;")
        )
        assert report.range_warnings == ()

    def test_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        report = apply_filters(sample, parse_filters("dir_sharp=1,0.0,-5.000000;"))
        assert len(report.range_warnings) == 1
        assert "dir_sharp" in report.range_warnings[0].casefold()
        clamped_only, _ = apply_filters(sample, parse_filters("dir_sharp=1,0.0,-1.0;"))
        assert np.array_equal(report.image, clamped_only)


class TestDirTintRange:
    def test_tartomanyon_beluli_dir_tint_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(
            sample, parse_filters("dir_tint=1,0.500000,0.500000,0.250000,0.250000;")
        )
        assert report.range_warnings == ()

    def test_feather_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        # gradiens (Feather) ∈ [0, 1] — 5.0 kilóg
        report = apply_filters(
            sample, parse_filters("dir_tint=1,0.500000,0.500000,5.000000,0.250000;")
        )
        assert len(report.range_warnings) == 1
        assert "dir_tint" in report.range_warnings[0].casefold()
        assert "feather" in report.range_warnings[0].casefold()

    def test_shade_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        # árnyalás (Shade) ∈ [0, 1] — -3.0 kilóg
        report = apply_filters(
            sample, parse_filters("dir_tint=1,0.500000,0.500000,0.250000,-3.000000;")
        )
        assert len(report.range_warnings) == 1
        assert "shade" in report.range_warnings[0].casefold()


class TestLinblurRange:
    def test_tartomanyon_beluli_linblur_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(
            sample, parse_filters("linblur=1,0.500000,0.500000,2.000000;")
        )
        assert report.range_warnings == ()

    def test_amount_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        # Amount ∈ [0, 10] — 25.0 kilóg
        report = apply_filters(
            sample, parse_filters("linblur=1,0.500000,0.500000,25.000000;")
        )
        assert len(report.range_warnings) == 1
        assert "linblur" in report.range_warnings[0].casefold()
        clamped_only, _ = apply_filters(
            sample, parse_filters("linblur=1,0.500000,0.500000,10.000000;")
        )
        assert np.array_equal(report.image, clamped_only)


# --- #669: ugyanezen az alapon felvehető további szűrők --------------------


class TestRadblurRange:
    def test_tartomanyon_beluli_radblur_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(
            sample, parse_filters("radblur=1,0.500000,0.500000,0.300000,0.300000;")
        )
        assert report.range_warnings == ()

    def test_size_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        report = apply_filters(
            sample, parse_filters("radblur=1,0.500000,0.500000,5.000000,0.300000;")
        )
        assert len(report.range_warnings) == 1
        assert "radblur" in report.range_warnings[0].casefold()

    def test_amount_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        report = apply_filters(
            sample, parse_filters("radblur=1,0.500000,0.500000,0.300000,-5.000000;")
        )
        assert len(report.range_warnings) == 1


class TestRadsatRange:
    def test_tartomanyon_beluli_radsat_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(
            sample, parse_filters("radsat=1,0.500000,0.500000,0.300000,0.500000;")
        )
        assert report.range_warnings == ()

    def test_sharpness_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        # Sharpness ∈ [0, 1] — 5.0 kilóg
        report = apply_filters(
            sample, parse_filters("radsat=1,0.500000,0.500000,0.300000,5.000000;")
        )
        assert len(report.range_warnings) == 1
        assert "radsat" in report.range_warnings[0].casefold()


class TestRadtintRange:
    def test_tartomanyon_beluli_radtint_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(
            sample, parse_filters("radtint=1,0.500000,0.500000,0.250000;")
        )
        assert report.range_warnings == ()

    def test_feather_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        report = apply_filters(
            sample, parse_filters("radtint=1,0.500000,0.500000,5.000000;")
        )
        assert len(report.range_warnings) == 1
        assert "radtint" in report.range_warnings[0].casefold()


class TestGlowRange:
    def test_tartomanyon_beluli_glow_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(sample, parse_filters("glow=1,0.500000,3.000000;"))
        assert report.range_warnings == ()

    def test_intensity_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        report = apply_filters(sample, parse_filters("glow=1,5.000000,3.000000;"))
        assert len(report.range_warnings) == 1
        assert "glow" in report.range_warnings[0].casefold()

    def test_radius_log_base_miatt_nincs_validalva(self, sample):
        # a Radius csúszka log_base-szal jelzett (softclamp-kivétel) —
        # a tárolt érték szándékosan túllépheti a névleges tartományt
        report = apply_filters(sample, parse_filters("glow=1,0.500000,999.000000;"))
        assert report.range_warnings == ()

    def test_glow2_intensity_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        report = apply_filters(sample, parse_filters("glow2=1,5.000000,3.000000;"))
        assert len(report.range_warnings) == 1
        assert "glow2" in report.range_warnings[0].casefold()


class TestTintRange:
    def test_tartomanyon_beluli_tint_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(sample, parse_filters("tint=1,50.000000;"))
        assert report.range_warnings == ()

    def test_color_preservation_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        # Color Preservation ∈ [-1, 255] — 300.0 kilóg
        report = apply_filters(sample, parse_filters("tint=1,300.000000;"))
        assert len(report.range_warnings) == 1
        assert "tint" in report.range_warnings[0].casefold()


class TestFillRange:
    def test_tartomanyon_beluli_fill_nem_ad_figyelmeztetest(self, sample):
        report = apply_filters(sample, parse_filters("fill=1,0.500000;"))
        assert report.range_warnings == ()

    def test_fill_kilogas_vagva_fut_es_figyelmeztet(self, sample):
        report = apply_filters(sample, parse_filters("fill=1,5.000000;"))
        assert len(report.range_warnings) == 1
        assert "fill" in report.range_warnings[0].casefold()
