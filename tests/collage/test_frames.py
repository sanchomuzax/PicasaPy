"""A kollázs három képkerete + a háttér tompítása (#431).

A számok forrása: `docs/specs/picasa-create-features.md` 1.9.5.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.collage.frames import (
    NOBORDER,
    POLAROID,
    POLAROID_PAPER_BGR,
    WHITEBORDER,
    WHITE_BORDER_BGR,
    apply_border,
    dim_for_background,
    polaroid_geometry,
    white_border_width,
)


def _photo(width: int, height: int, value: int = 200) -> np.ndarray:
    return np.full((height, width, 3), value, dtype=np.uint8)


# --- Polaroid ---------------------------------------------------------------


def test_polaroid_geometria_a_valodi_aranyokat_adja():
    """`1.145` szélességben, `1.374` magasságban, `0.0725` margó."""
    geometry = polaroid_geometry(100, 100)
    assert geometry.outer_width == 115  # round(100 * 1.145)
    assert geometry.outer_height == 137  # round(100 * 1.374)
    assert geometry.margin == 7  # round(100 * 0.0725)
    assert (geometry.photo_x, geometry.photo_y) == (7, 7)


def test_polaroid_also_savja_vastagabb_a_margonal():
    """A felirat sávja az, ami alul MARAD — ettől „polaroidos" a kép."""
    geometry = polaroid_geometry(100, 100)
    assert geometry.caption_height == 137 - 7 - 100
    assert geometry.caption_height > geometry.margin


def test_polaroid_margo_a_foto_SZELESSEGEBOL_szamol():
    """Fekvő fotónál is a szélesség adja a margót — nem a rövidebb oldal.

    Ez a részlet könnyen elnézhető: a fehér szegély a rövidebb oldalból
    számol, a polaroid viszont a szélességből."""
    geometry = polaroid_geometry(400, 100)
    assert geometry.margin == 29  # round(400 * 0.0725)


def test_polaroid_keret_merete_es_papirszine():
    framed = apply_border(_photo(100, 100), POLAROID)
    assert framed.shape[:2] == (137, 115)
    # a bal felső sarok papír, nem fotó
    assert tuple(int(c) for c in framed[0, 0]) == POLAROID_PAPER_BGR
    # a fotó a helyén van
    assert tuple(int(c) for c in framed[7, 7]) == (200, 200, 200)
    # az alsó sáv papír
    assert tuple(int(c) for c in framed[130, 57]) == POLAROID_PAPER_BGR


# --- Fehér szegély ----------------------------------------------------------


def test_feher_szegely_a_ROVIDEBB_oldal_ot_szazaleka():
    assert white_border_width(200, 100) == 5
    assert white_border_width(100, 200) == 5
    assert white_border_width(1000, 800) == 40


def test_feher_szegely_nem_tiszta_feher():
    """A Picasa `#EEEEEE`-t használ, nem `#FFFFFF`-et — fehér háttéren is
    látszik a szegély."""
    assert WHITE_BORDER_BGR == (238, 238, 238)
    framed = apply_border(_photo(200, 100), WHITEBORDER)
    assert framed.shape[:2] == (110, 210)
    assert tuple(int(c) for c in framed[0, 0]) == WHITE_BORDER_BGR


# --- Nincs szegély ----------------------------------------------------------


def test_nincs_szegely_valtozatlanul_hagyja_a_kepet():
    photo = _photo(40, 30)
    framed = apply_border(photo, NOBORDER)
    assert framed.shape == photo.shape
    assert np.array_equal(framed, photo)


def test_a_keret_nem_modositja_a_bemenetet():
    """Immutabilitás: a bemeneti tömb sosem változik."""
    photo = _photo(40, 30)
    before = photo.copy()
    apply_border(photo, POLAROID)
    apply_border(photo, WHITEBORDER)
    assert np.array_equal(photo, before)


def test_ismeretlen_keret_hibat_dob():
    with pytest.raises(ValueError, match="Ismeretlen képkeret"):
        apply_border(_photo(10, 10), "kacsa")


# --- Tompítás (háttérkép) ---------------------------------------------------


def test_tompitas_soteti_a_hatterkepet():
    """Fényerő −0,15 (a 0…1 skálán), kontraszt 1,0 — hogy a ráhelyezett
    képek olvashatók maradjanak."""
    dimmed = dim_for_background(_photo(4, 4, 128))
    assert int(dimmed[0, 0, 0]) == 90  # 128 - 0.15*255 = 89.75


def test_tompitas_nem_megy_nulla_ala():
    dimmed = dim_for_background(_photo(4, 4, 10))
    assert int(dimmed[0, 0, 0]) == 0
