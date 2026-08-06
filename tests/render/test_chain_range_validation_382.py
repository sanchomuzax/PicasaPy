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
