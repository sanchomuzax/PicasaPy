"""#357: éles `.picasa.ini`-kben a tint/ansel/dir_tint szín-paramétere
OPCIONÁLIS — a Picasa elhagyja, ha az alapértelmezett színnel mentett
(élő NAS-os állományból származó minták, felhasználói futásnapló,
2026-08-05). Hiányzó szín esetén a lánc a dokumentált alapértékkel
(fehér) fut, nem esik ki a kihagyott-listába."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(357)
    return rng.integers(30, 220, size=(48, 64, 3), dtype=np.uint8)


# Az éles futásnaplóban látott PONTOS alakok:
ELO_MINTAK = (
    "tint=1,0.500000;",
    "ansel=1;",
    "dir_tint=1,0.500000,0.500000,0.500000,0.500000;",
)


class TestOpcionalisSzinparameter:
    @pytest.mark.parametrize("lanc", ELO_MINTAK)
    def test_szin_nelkuli_alak_nem_kerul_kihagyasra(self, sample, lanc):
        ops = parse_filters(lanc)
        eredmeny, kihagyott = apply_filters(sample, ops)
        assert kihagyott == ()
        assert eredmeny.shape == sample.shape
        assert eredmeny.dtype == sample.dtype

    def test_ansel_szin_nelkul_tiszta_fekete_feher(self, sample):
        # Fehér alapértékkel az ansel tiszta B/W: a csatornák a tónusgörbe
        # után is egyformák maradnak.
        ops = parse_filters("ansel=1;")
        eredmeny, kihagyott = apply_filters(sample, ops)
        assert kihagyott == ()
        assert np.array_equal(eredmeny[..., 0], eredmeny[..., 1])
        assert np.array_equal(eredmeny[..., 1], eredmeny[..., 2])

    def test_szines_alak_tovabbra_is_mukodik(self, sample):
        # A meglévő, szín-paraméteres alak viselkedése nem változhatott.
        ops = parse_filters("tint=1,0.300000,ff8040;")
        eredmeny, kihagyott = apply_filters(sample, ops)
        assert kihagyott == ()
        assert not np.array_equal(eredmeny, sample)

    def test_tint_parameter_nelkul_tovabbra_is_hibas(self, sample):
        # A `tint=1;` (preserve nélkül) továbbra is érvénytelen — kihagyás.
        ops = parse_filters("tint=1;")
        _, kihagyott = apply_filters(sample, ops)
        assert kihagyott == ("tint",)
