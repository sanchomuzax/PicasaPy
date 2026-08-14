"""#623: az irányított család BEKÖTÉSE a `filters=` láncba.

A négy örökölt effekt (`dir_sat`, `dir_brite`, `dir_sharp`, `linblur`) a
natív magok visszafejtése után ténylegesen renderel — nem esik ki az
„ismeretlen op = néma kihagyás" ágon.

Paraméter-alakok:

- `dir_sat`/`dir_brite`/`dir_sharp` = `1, balról-jobbra, felülről-lefelé`
  (a natív burkolók a két csúszkát KÖZVETLENÜL adják tovább; a korong csak
  beállítja őket, ld. a közös `0x008f9bc0` visszahívást);
- `linblur` = `1, korong-x, korong-y, mennyiség` — itt a korong VALÓDI
  pozíció (`0x008f9bf0`), ezért a puck-os szűrők általános sorrendje
  érvényes (`docs/specs/filterdesc-registry.md` 3. pont).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import KNOWN_UNRENDERED_OPS, apply_filters, can_render_filter
from picasapy.render.directional import apply_dir_brite, apply_dir_sat, apply_dir_sharp
from picasapy.render.linear_blur import apply_linblur

_KULCSOK = ("dir_sat", "dir_brite", "dir_sharp", "linblur")


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(19)
    return rng.integers(20, 235, size=(48, 64, 3), dtype=np.uint8)


class TestNegyEffektRendere:
    @pytest.mark.parametrize("key", _KULCSOK)
    def test_a_lanc_ismeri_es_nem_hagyja_ki(self, key: str, sample) -> None:
        assert key not in KNOWN_UNRENDERED_OPS
        assert can_render_filter(key) is True

    @pytest.mark.parametrize(
        "chain",
        [
            "dir_sat=1,1.000000,0.000000;",
            "dir_brite=1,1.000000,0.000000;",
            "dir_sharp=1,1.000000,0.000000;",
            "linblur=1,0.750000,0.500000,2.000000;",
        ],
    )
    def test_a_lanc_tenylegesen_valtoztat(self, chain: str, sample) -> None:
        report = apply_filters(sample, parse_filters(chain))
        assert report.skipped == ()
        assert not np.array_equal(report.image, sample)


class TestParameterSorrend:
    def test_dir_sat_parameterei(self, sample) -> None:
        report = apply_filters(sample, parse_filters("dir_sat=1,0.600000,-0.400000;"))
        np.testing.assert_array_equal(report.image, apply_dir_sat(sample, 0.6, -0.4))

    def test_dir_brite_parameterei(self, sample) -> None:
        report = apply_filters(sample, parse_filters("dir_brite=1,0.600000,-0.400000;"))
        np.testing.assert_array_equal(report.image, apply_dir_brite(sample, 0.6, -0.4))

    def test_dir_sharp_parameterei(self, sample) -> None:
        report = apply_filters(sample, parse_filters("dir_sharp=1,0.600000,-0.400000;"))
        np.testing.assert_array_equal(report.image, apply_dir_sharp(sample, 0.6, -0.4))

    def test_linblur_parameterei(self, sample) -> None:
        """`x, y, Mennyiség` — a korong megy elöl."""
        report = apply_filters(
            sample, parse_filters("linblur=1,0.750000,0.250000,3.000000;")
        )
        np.testing.assert_array_equal(report.image, apply_linblur(sample, 0.75, 0.25, 3.0))

    @pytest.mark.parametrize("key", _KULCSOK)
    def test_parameter_nelkul_is_lefut(self, key: str, sample) -> None:
        """Alapállás: a `dir_*` csúszkái 0-n, a `linblur` korongja középen —
        mindkettő azonosság, de NEM kihagyott bejegyzés."""
        report = apply_filters(sample, parse_filters(f"{key}=1;"))
        assert report.skipped == ()
        np.testing.assert_array_equal(report.image, sample)


class TestPublikusApi:
    """A `picasapy.render` csomag `__all__`-ja csak LÉTEZŐ nevet soroljon.

    A #623 első köre a `dir_sat`/`dir_brite`/`directional_ramp` nevet
    felvette az `__all__`-ba, de az importot nem — így a
    `from picasapy.render import *` `AttributeError`-ral szállt el.
    """

    def test_minden_exportalt_nev_letezik(self) -> None:
        import picasapy.render as render

        hianyzo = [name for name in render.__all__ if not hasattr(render, name)]
        assert hianyzo == []
