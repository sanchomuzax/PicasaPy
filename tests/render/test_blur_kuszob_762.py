"""#762: a `blur` küszöbcsúszkája 1,4-ig bezárólag TÉTLEN — mérve.

A tulajdonos 2026-09-21-i exportja (`762-blur-kuszob`, hat bájtra azonos
forrás, 800×512, `EXIF Software = Picasa`) a köztes sávot is lefedte:

| lánc | az export a forráshoz képest |
|---|---|
| `blur=1,0.100000;` … `blur=1,1.400000;` (öt érték) | képpontra AZONOS (átlag \\|Δ\\| = 0,000) |
| `blur=1,2.000000;` | teljes elsimítás (Laplace-szórás 162,6 → 0,4) |

A mi σ = 4-es elmosásunk a 2,0-s exporttól átlagosan 0,026-tal tér el.
A korábbi modell 0,5 fölött már elmosott, így 0,8–1,4 között a Picasáétól
eltérő képet adott (1,4-nél átlag \\|Δ\\| = 1,008 az exporthoz képest).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini import parse_filters
from picasapy.render import apply_filters
from picasapy.render.blur import BLUR_IDLE_THRESHOLD_MAX


@pytest.fixture
def minta():
    """Éles csíkos ábra — minden simítás látszana rajta."""
    kep = np.zeros((64, 96, 3), dtype=np.uint8)
    kep[:, ::4] = 255
    kep[10:30, 20:60] = (200, 40, 90)
    return kep


@pytest.mark.parametrize("ertek", ["0.800000", "1.100000", "1.400000"])
def test_a_mert_koztes_ertekek_tetlenek(minta, ertek):
    kimenet = apply_filters(minta, parse_filters(f"blur=1,{ertek};")).image
    np.testing.assert_array_equal(kimenet, minta)


def test_a_2_0_tovabbra_is_elmos(minta):
    kimenet = apply_filters(minta, parse_filters("blur=1,2.000000;")).image
    assert np.abs(kimenet.astype(int) - minta.astype(int)).mean() > 10


def test_a_tetlen_sav_felso_hatara_a_legnagyobb_mert_tetlen_ertek():
    assert BLUR_IDLE_THRESHOLD_MAX == pytest.approx(1.4)
