"""A diavetítési Dissolve alfa-görbéje a Picasa 38.2.270 szerint (#6920)."""

import pytest

from picasapy.app.slideshow_transition import dissolve_alpha256


_ALFA_3_MASODPERC = (
    0, 8, 30, 63, 104, 140, 167, 188, 204, 216, 225,
    232, 238, 242, 245, 248, 249, 251, 252, 253, 254,
    254, 254, 255, 255, 255, 255, 255, 255, 255, 256,
)


@pytest.mark.parametrize("n, vart_alfa", enumerate(_ALFA_3_MASODPERC))
def test_a_teljes_tizenot_fps_kodsort_a_spec_tabla_szerint_adja(n, vart_alfa):
    assert dissolve_alpha256(n / 15, 3) == vart_alfa


def test_egy_es_ket_masodpercnel_a_spec_szerinti_alfa_kodot_adja():
    assert dissolve_alpha256(1, 3) == 248
    assert dissolve_alpha256(2, 3) == 256


@pytest.mark.parametrize("arany", (1 / 4, 1 / 2, 3 / 4, 1))
def test_a_gorbe_a_diaidovel_aranyosan_telodik(arany):
    assert dissolve_alpha256(arany * 3 / 1.5, 3) == dissolve_alpha256(
        arany * 6 / 1.5, 6
    )
