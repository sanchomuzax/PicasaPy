"""#2902: veszteségmentes tükrözés — a mért két irány."""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.flip import (
    FLIP_HORIZONTAL,
    FLIP_MASK,
    FLIP_VERTICAL,
    apply_flip,
    toggled_flip,
)


@pytest.fixture
def kep():
    """Aszimmetrikus kép: minden sarok más — így a tengely-tévesztés kiderül."""
    tomb = np.zeros((2, 3, 3), dtype=np.uint8)
    tomb[0, 0] = (10, 10, 10)
    tomb[0, 2] = (20, 20, 20)
    tomb[1, 0] = (30, 30, 30)
    tomb[1, 2] = (40, 40, 40)
    return tomb


def test_a_vizszintes_a_BAL_JOBB_tengely(kep):
    tukor = apply_flip(kep, FLIP_HORIZONTAL)
    assert tuple(tukor[0, 0]) == (20, 20, 20)
    assert tuple(tukor[0, 2]) == (10, 10, 10)
    assert tuple(tukor[1, 0]) == (40, 40, 40)


def test_a_fuggoleges_a_FEL_LE_tengely(kep):
    tukor = apply_flip(kep, FLIP_VERTICAL)
    assert tuple(tukor[0, 0]) == (30, 30, 30)
    assert tuple(tukor[1, 0]) == (10, 10, 10)
    assert tuple(tukor[0, 2]) == (40, 40, 40)


def test_mindketto_a_180_fokos_forgatas(kep):
    assert np.array_equal(apply_flip(kep, FLIP_MASK), np.rot90(kep, 2))


def test_nulla_jelzo_valtozatlan(kep):
    assert apply_flip(kep, 0) is kep


def test_ketszer_ugyanaz_visszaad(kep):
    """A tükrözés önmaga inverze — ezért veszteségmentes."""
    for irany in (FLIP_HORIZONTAL, FLIP_VERTICAL, FLIP_MASK):
        assert np.array_equal(apply_flip(apply_flip(kep, irany), irany), kep)


class TestAJelzoValtasa:
    def test_ki_es_be(self):
        assert toggled_flip(0, FLIP_HORIZONTAL) == FLIP_HORIZONTAL
        assert toggled_flip(FLIP_HORIZONTAL, FLIP_HORIZONTAL) == 0

    def test_a_ket_irany_egymas_mellett_all(self):
        egy = toggled_flip(0, FLIP_VERTICAL)
        ketto = toggled_flip(egy, FLIP_HORIZONTAL)
        assert ketto == FLIP_MASK
        assert toggled_flip(ketto, FLIP_VERTICAL) == FLIP_HORIZONTAL

    def test_az_ertelmezhetetlen_bit_leesik(self):
        """Egy régi vagy idegen index 7-et is tartalmazhat — a felesleges
        bitektől a jelző megtisztul, nem hibázik."""
        assert toggled_flip(7, 0) == FLIP_MASK
        assert apply_flip(np.zeros((2, 2, 3), dtype=np.uint8), 255).shape == (2, 2, 3)
