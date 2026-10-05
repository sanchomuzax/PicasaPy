"""#4233: a részleges filters-tag elvágja a PicasaPy olvasóláncát."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filter_registry import MAX_PARAM_COUNTS
from picasapy.ini.filters import parse_filters, parse_filters_prefix
from picasapy.render.chain import apply_filters


def _kep() -> np.ndarray:
    rng = np.random.default_rng(4233)
    return rng.integers(20, 230, size=(48, 64, 3), dtype=np.uint8)


def test_a_reszleges_vignette_elott_futott_hatas_megmarad_utana_nem_fut():
    forras = _kep()

    # Pozitív kontrollok: az =1 és a teljes Vignette továbbra is elfogadott.
    flag_only = apply_filters(forras, parse_filters_prefix("Vignette=1;"))
    teljes = apply_filters(
        forras,
        parse_filters_prefix("Vignette=1,35,1.4,0,00000000;"),
    )
    np.testing.assert_array_equal(flag_only.image, teljes.image)

    timeline = "movieend=b40728fd;moviestart=80252d;"
    assert [op.name for op in parse_filters_prefix(timeline)] == [
        "movieend",
        "moviestart",
    ]
    # A `desat` a különálló, 84-es regiszteren kívüli régi alias.
    assert [
        op.name
        for op in parse_filters_prefix("desat=1,0,0,0;bw=1;")
    ] == ["desat", "bw"]

    teljes_lanc = "sepia=1;Vignette=1,35,1.4,0,00000000;bw=1;"
    assert parse_filters_prefix(teljes_lanc) == parse_filters(teljes_lanc)

    lanc = "sepia=1;Vignette=1,35,1.4,0;bw=1;"
    report = apply_filters(forras, parse_filters_prefix(lanc))
    csak_elotte = apply_filters(forras, parse_filters_prefix("sepia=1;"))
    elotte_es_utana = apply_filters(
        forras, parse_filters_prefix("sepia=1;bw=1;")
    )

    np.testing.assert_array_equal(report.image, csak_elotte.image)
    assert not np.array_equal(report.image, forras)
    assert not np.array_equal(report.image, elotte_es_utana.image)


@pytest.mark.parametrize(
    "name,expected",
    tuple(
        (name, count)
        for name, count in MAX_PARAM_COUNTS.items()
        if name not in {"moviestart", "movieend"}
    ),
)
def test_az_ismert_vezerloalak_flag_only_teljes_vagy_hibas(name, expected):
    teljes = "1" + ("," + ",".join("0" for _ in range(expected)) if expected else "")
    teljes_lanc = f"{name}={teljes};"

    # A teljes vezérlősor és a puszta engedélyező flag érvényes marad.
    assert parse_filters_prefix(teljes_lanc) == parse_filters(teljes_lanc)
    assert [op.name for op in parse_filters_prefix(f"{name}=1;")] == [name]

    # Legalább egy megadott, de hiányos mező, illetve fölös mező hibás tag.
    if expected >= 2:
        partial = ",".join("0" for _ in range(expected - 1))
        invalid = f"{name}=1,{partial}"
    else:
        extra = ",".join("0" for _ in range(expected + 1))
        invalid = f"{name}=1,{extra}"
    lanc = f"bw=1;{invalid};sepia=1;"

    assert [op.name for op in parse_filters_prefix(lanc)] == ["bw"]
