"""A kollázs-vászon műveletei: rétegsorrend, forgatás-igazítás, keverés.

Forrás: #431 index-köre (a szerkesztőpanel 19 parancsa) és a
`docs/specs/picasa-create-features.md` 1.4.
"""

from __future__ import annotations

import math

import pytest

from picasapy.collage.canvas import (
    SNAP_COMMANDS,
    angle_caption_degrees,
    move_down,
    move_to_bottom,
    move_to_top,
    move_up,
    remove_at,
    scale_caption_percent,
    shuffle_order,
    snap_theta,
)
from picasapy.collage.fitting import MsvcRandom

ELEMEK = ("a", "b", "c", "d", "e")


# --- Rétegsorrend -----------------------------------------------------------


def test_legfelulre_helyezes_a_lista_VEGERE_visz():
    """A lista sorrendje a rajzolási sorrend (a `.cxf` is így sorolja a
    csomópontokat), tehát az UTOLSÓ elem van legfelül."""
    assert move_to_top(ELEMEK, [1]) == ("a", "c", "d", "e", "b")


def test_legalulra_helyezes_a_lista_ELEJERE_visz():
    assert move_to_bottom(ELEMEK, [3]) == ("d", "a", "b", "c", "e")


def test_egy_lepessel_fel():
    assert move_up(ELEMEK, [1]) == ("a", "c", "b", "d", "e")


def test_egy_lepessel_le():
    assert move_down(ELEMEK, [3]) == ("a", "b", "d", "c", "e")


def test_a_szelen_allo_elem_nem_mozdul():
    assert move_up(ELEMEK, [4]) == ELEMEK
    assert move_down(ELEMEK, [0]) == ELEMEK


def test_tobb_kijelolt_elem_egyutt_mozog():
    assert move_to_top(ELEMEK, [0, 2]) == ("b", "d", "e", "a", "c")
    assert move_to_bottom(ELEMEK, [1, 4]) == ("b", "e", "a", "c", "d")


def test_tobb_kijelolt_elem_egy_lepessel():
    assert move_up(ELEMEK, [0, 1]) == ("c", "a", "b", "d", "e")


def test_a_kijelolesek_relativ_sorrendje_megmarad():
    assert move_to_top(ELEMEK, [3, 1]) == ("a", "c", "e", "b", "d")


def test_a_muveletek_UJ_sorozatot_adnak():
    """Immutabilitás: az eredeti sorozat sosem változik."""
    eredeti = list(ELEMEK)
    move_to_top(ELEMEK, [0])
    assert list(ELEMEK) == eredeti


def test_ures_kijeloles_valtozatlan():
    assert move_to_top(ELEMEK, []) == ELEMEK


def test_ervenytelen_index():
    with pytest.raises(ValueError):
        move_to_top(ELEMEK, [9])
    with pytest.raises(ValueError):
        move_up(ELEMEK, [-1])


# --- Eltávolítás ------------------------------------------------------------


def test_eltavolitas():
    assert remove_at(ELEMEK, [1, 3]) == ("a", "c", "e")


def test_minden_kep_eltavolithato():
    """A mentés ilyenkor „Mentés mellőzve" — de a művelet maga megengedett."""
    assert remove_at(ELEMEK, [0, 1, 2, 3, 4]) == ()


# --- Forgatás-igazítás ------------------------------------------------------


def test_a_negy_bepattinto_parancs():
    """A `snap_*` NEM 30 fokos óralap-rács, hanem a négy fő irány —
    a súgók (és a menü-erőforrás) ezt két független forrásból igazolják."""
    assert SNAP_COMMANDS == {
        "snap_12": 0.0,
        "snap_3": 90.0,
        "snap_6": 180.0,
        "snap_9": -90.0,  # #921: a TÁROLT érték −90, nem 270
    }


@pytest.mark.parametrize(
    ("command", "fok"), [("snap_12", 0), ("snap_3", 90), ("snap_6", 180), ("snap_9", -90)]
)
def test_a_bepattintas_radiant_ad(command, fok):
    assert snap_theta(command) == pytest.approx(math.radians(fok))


def test_ismeretlen_bepattinto_parancs():
    with pytest.raises(ValueError, match="Ismeretlen"):
        snap_theta("snap_5")


# --- Élő kijelzés húzás közben ----------------------------------------------


def test_a_szog_kijelzese_fokban_egeszre_kerekitve():
    """`collage::angle_format` = „Szög: %d" — a `theta` radiánból
    `*180/π`-vel, és #921 óta NEGÁLVA (a Picasa `fchs`-sel fordít a
    kiírás előtt, `0x00868944`)."""
    assert angle_caption_degrees(math.radians(12.4)) == -12
    assert angle_caption_degrees(math.radians(-12.6)) == 13
    assert angle_caption_degrees(0.0) == 0


def test_a_meretarany_kijelzese_szazalekban():
    """`collage::scale_format` = „Méretarány: %d%%"."""
    assert scale_caption_percent(337.0, 337.0) == 100
    assert scale_caption_percent(168.5, 337.0) == 50


def test_ervenytelen_alapmeret():
    with pytest.raises(ValueError):
        scale_caption_percent(100.0, 0.0)


# --- Képek összekeverése (`rand_order`) -------------------------------------


def test_a_keveres_minden_elemet_megtart():
    kevert = shuffle_order(ELEMEK, MsvcRandom(5))
    assert sorted(kevert) == sorted(ELEMEK)


def test_a_keveres_azonos_maggal_ismetelheto():
    assert shuffle_order(ELEMEK, MsvcRandom(5)) == shuffle_order(ELEMEK, MsvcRandom(5))


def test_a_keveres_tenylegesen_atrendez():
    """Ez a `rand_order` („Képek összekeverése") — a SORRENDET keveri.
    Az elrendezés újrasorsolása külön parancs (`rand_placement`)."""
    assert shuffle_order(tuple(range(20)), MsvcRandom(3)) != tuple(range(20))
