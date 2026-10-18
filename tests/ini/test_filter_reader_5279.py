"""#5279: a láncbeolvasó fogadja a két irányított értéket, és ismeretlennél megáll."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters_prefix
from picasapy.render.chain import apply_filters
from picasapy.render.directional import apply_dir_brite, apply_dir_sharp


@pytest.fixture
def kep() -> np.ndarray:
    rng = np.random.default_rng(5279)
    return rng.integers(20, 235, size=(48, 64, 3), dtype=np.uint8)


@pytest.mark.parametrize(
    ("tag", "alkalmaz"),
    [
        ("dir_brite=1,0.500000,0.500000;", apply_dir_brite),
        ("dir_sharp=1,0.500000,0.500000;", apply_dir_sharp),
    ],
)
def test_a_ket_vezerloerteku_iranyitott_tag_lefut(kep, tag, alkalmaz):
    ops = parse_filters_prefix(tag)

    assert [op.name for op in ops] == [tag.split("=", maxsplit=1)[0]]
    report = apply_filters(kep, ops)
    assert report.skipped == ()
    np.testing.assert_array_equal(report.image, alkalmaz(kep, 0.5, 0.5))


def test_az_ismeretlen_tag_utan_a_bw_sem_fut_le(kep):
    ops = parse_filters_prefix("nincsilyen=1;bw=1;")

    assert ops == ()
    report = apply_filters(kep, ops)
    np.testing.assert_array_equal(report.image, kep)
