"""#4936: a szemcse magja a renderen belüli CRT `rand()` sorszámából jön.

A merokit-2 mérés leíró adatai: a Picasa `szemcse_02` exportja a munkamenet
k=1 magját használta; k=0 mellett ΔE 2,661, k=1 mellett 1,447. A kétszeres
grain lánc per-render k=0,1 maggal ΔE 3,679; a mért Picasa munkamenet k=2,3
értéke 1,866 volt. Ezek nem elfogadási küszöbök: a Picasa és a mi renderünk
eltérő hívássorrendjét dokumentálják. A 684 `grain__alap` k=0 mért nyers
ΔE-je 1,509 (az elfogadási küszöb 1,6). A grain2 méréseire nem vonatkozik
ΔE ≤ 2,0; a fenti számok leíró adatok, nem tesztküszöbök.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render import native_grain
from picasapy.render.color import apply_grain
from picasapy.render.chain import apply_filters


def _picasa_seed(ordinal: int) -> int:
    """Független teszt-orákulum a spec képletéhez, CRT-alapállapotból."""
    state = 1
    rand_values = []
    for _ in range(3 * ordinal + 3):
        state = (state * 0x343FD + 0x269EC3) & 0xFFFFFFFF
        rand_values.append((state >> 16) & 0x7FFF)
    r1, r2, r3 = rand_values[-3:]
    return (r3 ^ ((r2 ^ (r1 << 12)) << 12)) & 0xFFFFFFFF


@pytest.fixture
def sample() -> np.ndarray:
    y, x = np.indices((63, 79), dtype=np.uint16)
    return np.stack(
        ((x * 7 + y * 3) % 256, (x * 2 + y * 5) % 256, (x * 11 + y) % 256),
        axis=-1,
    ).astype(np.uint8)


def test_grain_seed_az_elso_ket_harmasbol_picasa_kepletet_adja() -> None:
    seed_for = getattr(native_grain, "grain_seed", None)
    assert callable(seed_for), "hiányzik a `grain_seed(ordinal)` függvény"
    assert seed_for(0) == 0x2D8228BE
    assert seed_for(1) == 0x80AE2D6C


@pytest.mark.parametrize(
    ("chain", "ordinals"),
    [
        ("grain=1;", (0,)),
        ("grain2=1;", (0,)),
        ("grain=1;grain=1;", (0, 1)),
    ],
)
def test_a_lanc_minden_szemcsehez_a_render_sorszamat_hasznalja(
    sample: np.ndarray, chain: str, ordinals: tuple[int, ...]
) -> None:
    expected = sample.copy()
    for ordinal in ordinals:
        expected = apply_grain(expected, seed=_picasa_seed(ordinal))

    report = apply_filters(sample, parse_filters(chain))

    np.testing.assert_array_equal(report.image, expected)
    assert report.skipped == ()
