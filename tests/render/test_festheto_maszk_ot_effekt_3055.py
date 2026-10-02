"""#3055/#3541: a festhető effekt egyedül a Vámpírszem.

A Boost, Pixelate, Soften és PicnikTint az egész képre hat, ecset nélkül.
Ezek kimenete a teljes képen változik, és nem kapnak festhető-maszk
figyelmeztetést. A ReanimatedEyeColor festhető, és üres maszkkal tétlen.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.chain_glimmer_handlers import PAINTABLE_MASK_OPS


FESTHETO = frozenset({"reanimatedeyecolor"})
TELJES_KEPRE_HATO = {
    "boost": "Boost=1,80.000000;",
    "pixelate": "Pixelate=1,20.000000;",
    "soften": "Soften=1,80.000000,0.000000;",
    "picniktint": "PicnikTint=1,0.000000,80cfff;",
}


def _kep() -> np.ndarray:
    """Determinista, texturált kép, amin mind a négy effekt látható."""
    return np.random.default_rng(3055).integers(
        20, 235, size=(64, 96, 3), dtype=np.uint8
    )


def test_egyetlen_festheto_effekt_a_vampirszem() -> None:
    assert PAINTABLE_MASK_OPS == FESTHETO


@pytest.mark.parametrize(("kulcs", "lanc"), TELJES_KEPRE_HATO.items())
def test_a_negy_effekt_ecset_nelkul_a_teljes_kepet_valtoztatja(
    kulcs: str, lanc: str
) -> None:
    kep = _kep()
    jelentes = apply_filters(kep, parse_filters(lanc))
    assert jelentes.image is not None

    elteres = (jelentes.image != kep).any(axis=-1)
    assert elteres[:, : kep.shape[1] // 2].any(), f"{kulcs}: a bal oldal változatlan"
    assert elteres[:, kep.shape[1] // 2 :].any(), f"{kulcs}: a jobb oldal változatlan"
    assert not jelentes.range_warnings, (
        f"{kulcs}: az egész képre ható effekt ne jelezzen ecsetmaszkot: "
        f"{jelentes.range_warnings}"
    )


def test_a_vampirszem_uresen_valtozatlan_es_figyelmeztet() -> None:
    kep = _kep()
    jelentes = apply_filters(
        kep, parse_filters("ReanimatedEyeColor=1,6.000000,20.000000;")
    )
    assert jelentes.image is not None
    assert np.array_equal(jelentes.image, kep)
    assert any("ReanimatedEyeColor" in w for w in jelentes.range_warnings)


# rontás-kontroll: picasapy.render.chain_glimmer_handlers.PAINTABLE_MASK_OPS = {"boost", "pixelate", "soften", "picniktint", "reanimatedeyecolor"} → 1 failed
