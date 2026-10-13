"""#4941: érvénytelen (kétparaméteres) `PicnikFocalPixelate`-lánc.

A `merokit-2` szett `halott_14` képén a rövid lánc a mi renderünkben
kivételt dobott, és a szűrő kimaradt. Az eredeti Picasa ugyanezt a láncot
csendben változatlanul hagyja (export ≈ forrás), ezért a helyes viselkedés:
kivétel nélkül fut, a kép nem változik, a lánc többi tagja pedig lefut.
"""

from __future__ import annotations

import logging

import numpy as np
import pytest

from picasapy.ini import parse_filters
from picasapy.render import apply_filters

ROVID = "PicnikFocalPixelate=1,20.000000;"
ROVID_UTANA_BW = "PicnikFocalPixelate=1,20.000000;bw=1;"


@pytest.fixture
def minta():
    y, x = np.mgrid[0:64, 0:96]
    return np.dstack([(x * 255 // 96), (y * 255 // 64), np.full((64, 96), 120)]).astype(np.uint8)


def test_a_ketparameteres_lanc_kivetel_nelkul_fut(minta, caplog):
    with caplog.at_level(logging.WARNING):
        report = apply_filters(minta, parse_filters(ROVID))
    hibak = [r for r in caplog.records if r.levelno >= logging.ERROR]
    assert hibak == []
    assert np.array_equal(report.image, minta)


def test_a_lanc_tobbi_tagja_ettol_fut(minta):
    report = apply_filters(minta, parse_filters(ROVID_UTANA_BW))
    csak_bw = apply_filters(minta, parse_filters("bw=1;"))
    assert np.array_equal(report.image, csak_bw.image)
