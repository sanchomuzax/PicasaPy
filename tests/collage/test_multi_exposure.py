"""A Többszörös exponálás (`multiexp`) és az Indexkép (`contactsheet`)
fejlécének mérete (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.9.4.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.collage.contact_sheet import (
    CONTACT_SHEET_TITLE_RATIO,
    NARROW_PANEL_FACTOR,
    header_font_size,
)
from picasapy.collage.multi_exposure import blend_multi_exposure, multi_exposure_size


# --- Többszörös exponálás ---------------------------------------------------


def test_minden_kep_a_TELJES_lapra_kerul():
    """Nincs pozíciószámítás: mindegyik kép a lapra igazodik, oldalarányt
    tartva."""
    assert multi_exposure_size(300, 200, 900, 900) == (900, 600)
    assert multi_exposure_size(200, 300, 900, 900) == (600, 900)


def test_ket_azonos_kep_keverese_ugyanazt_adja():
    """Egyenlő súlyú keverésnél két azonos kép átlaga önmaga."""
    kep = np.full((10, 10, 3), 120, dtype=np.uint8)
    kevert = blend_multi_exposure([kep, kep], 10, 10)
    assert int(kevert[5, 5, 0]) == 120


def test_a_kepek_SULYA_EGYENLO():
    """Fekete és fehér keveréke középszürke — nem az utolsó kép nyer, és
    nem is telítődik ki a kimenet."""
    fekete = np.zeros((10, 10, 3), dtype=np.uint8)
    feher = np.full((10, 10, 3), 255, dtype=np.uint8)
    kevert = blend_multi_exposure([fekete, feher], 10, 10)
    assert 126 <= int(kevert[5, 5, 0]) <= 129


def test_harom_kep_egyenlo_harmaddal():
    keverek = blend_multi_exposure(
        [
            np.zeros((8, 8, 3), dtype=np.uint8),
            np.zeros((8, 8, 3), dtype=np.uint8),
            np.full((8, 8, 3), 255, dtype=np.uint8),
        ],
        8,
        8,
    )
    assert 84 <= int(keverek[4, 4, 0]) <= 86  # 255 / 3


def test_a_keveres_nem_telitodik_ki():
    """Öt világos kép sem lesz tiszta fehér — ez különbözteti meg az
    egyenlő súlyú keverést a puszta összeadástól."""
    vilagos = np.full((8, 8, 3), 200, dtype=np.uint8)
    kevert = blend_multi_exposure([vilagos] * 5, 8, 8)
    assert int(kevert[4, 4, 0]) < 255


def test_a_kimenet_a_lap_merete():
    kevert = blend_multi_exposure(
        [np.full((30, 40, 3), 100, dtype=np.uint8)], 200, 100
    )
    assert kevert.shape == (100, 200, 3)


def test_a_bemenetet_nem_modositja():
    kep = np.full((8, 8, 3), 50, dtype=np.uint8)
    elotte = kep.copy()
    blend_multi_exposure([kep, kep], 8, 8)
    assert np.array_equal(kep, elotte)


def test_ures_lista_hibat_dob():
    with pytest.raises(ValueError):
        blend_multi_exposure([], 10, 10)


# --- Indexkép-fejléc --------------------------------------------------------


def test_a_fejlec_betumerete_a_lapmagassag_negy_szazaleka():
    assert CONTACT_SHEET_TITLE_RATIO == 0.04
    assert header_font_size(1000, panel_aspect=1.5) == 40


def test_keskeny_panelen_haromnegyedere_csokken():
    """`f = 1,0`, ha a panel oldalaránya nagyobb 1-nél, különben 0,75."""
    assert NARROW_PANEL_FACTOR == 0.75
    assert header_font_size(1000, panel_aspect=0.8) == 30


def test_a_pontosan_negyzetes_panel_is_keskenynek_szamit():
    """A feltétel szigorú `>`, tehát az 1,0 a kisebbik ágra esik."""
    assert header_font_size(1000, panel_aspect=1.0) == 30


def test_ervenytelen_lapmagassag():
    with pytest.raises(ValueError):
        header_font_size(0, panel_aspect=1.5)
