"""#6788: az A=0 `dir_brite` után a DropShadow a mért háttérszínt adja."""

# rontás-kontroll: picasapy.render.chain._ALPHA_TRANSPARENT = 255 -> 2 failed.

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters


_LANC = (
    "dir_brite=1,-0.884987,-0.873954;"
    "DropShadow=1,5.692017,241.473639,41.331983,00c9dd31,005df725,98.258864;"
)
_HATTER = (0x5D, 0xF7, 0x25)


@pytest.mark.parametrize("mert_sorrend", (True, False), ids=("mert", "halasztott"))
def test_dir_brite_utan_a_dropshadow_a_mert_hatterre_kompozital(mert_sorrend: bool) -> None:
    """A k05 mérés eredeti exportja minden képponton #5df725 (#6585/lanc-0045)."""
    y, x = np.indices((64, 64))
    source = np.stack((x * 3, y * 3, (x + y) * 2), axis=-1).astype(np.uint8)
    ops = parse_filters(_LANC)

    iranyitott = apply_filters(source, ops[:1])
    assert iranyitott.alpha == 0

    report = apply_filters(source, ops, mert_sorrend=mert_sorrend)

    assert report.skipped == ()
    assert report.alpha == 255
    np.testing.assert_array_equal(report.image, np.full_like(report.image, _HATTER))
