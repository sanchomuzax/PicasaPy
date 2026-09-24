"""#762: a `blur` a kétszínű 762-es ábrán 1,4-ig bezárólag TÉTLEN — mérve.

A tulajdonos 2026-09-21-i exportja (`762-blur-kuszob`, hat bájtra azonos
forrás, 800×512, `EXIF Software = Picasa`):

| lánc | az export a forráshoz képest |
|---|---|
| `blur=1,0.100000;` … `blur=1,1.400000;` (öt érték) | képpontra AZONOS (átlag \\|Δ\\| = 0,000) |
| `blur=1,2.000000;` | teljes elsimítás (Laplace-szórás 162,6 → 0,4) |

⚠️ #3493: a tétlenség az ÁBRA sajátja, nem a szűrőé. Az ábra kétszínű, az
egyetlen fekete-fehér él négyzetes különbsége 3·255² = 195 075; a natív
lánc ezen addig húz falat, amíg `K = CSONK(t²·65536) < 195 075`. Zajos
tartalmon a csúszka tartományában is simít (`test_blur_nativ_3493.py`).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from picasapy.ini import parse_filters
from picasapy.render import apply_filters

_N762 = Path("/mnt/nas/My Pictures/762-blur-kuszob")


@pytest.fixture
def ketszinu():
    """A 762-es ábra lényege: fekete és fehér, éles élekkel."""
    kep = np.zeros((64, 96, 3), dtype=np.uint8)
    kep[:, ::4] = 255
    return kep


@pytest.mark.parametrize("ertek", ["0.100000", "0.500000", "0.800000", "1.100000", "1.400000"])
def test_a_mert_ertekek_a_ketszinu_abran_tetlenek(ketszinu, ertek):
    kimenet = apply_filters(ketszinu, parse_filters(f"blur=1,{ertek};")).image
    np.testing.assert_array_equal(kimenet, ketszinu)


def test_a_2_0_elmos(ketszinu):
    kimenet = apply_filters(ketszinu, parse_filters("blur=1,2.000000;")).image
    assert np.abs(kimenet.astype(int) - ketszinu.astype(int)).mean() > 10


@pytest.mark.skipif(not _N762.exists(), reason="a NAS-os mérőkészlet nem elérhető")
@pytest.mark.parametrize(
    "kod,ertek,tures",
    [("010", 0.1, 0.0), ("050", 0.5, 0.0), ("080", 0.8, 0.0),
     ("110", 1.1, 0.0), ("140", 1.4, 0.0), ("200", 2.0, 0.026)],
)
def test_a_picasa_exporttal_egyezik(kod, ertek, tures):
    from PIL import Image

    from picasapy.render.blur import apply_blur

    forras = np.asarray(Image.open(_N762 / f"Blur_kuszob-{kod}.jpg").convert("RGB"))
    export = np.asarray(Image.open(_N762 / "export" / f"Blur_kuszob-{kod}.jpg").convert("RGB"))
    elteres = np.abs(apply_blur(forras, ertek).astype(int) - export.astype(int)).mean()
    assert elteres <= tures
