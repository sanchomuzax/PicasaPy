"""A kollázs közös építőelemei — illesztő és MSVC-véletlen (#431).

A számok forrása: `docs/specs/picasa-create-features.md` 1.9.1.
"""

from __future__ import annotations

import pytest

from picasapy.collage.fitting import fit_inside, msvc_uniform01, picasa_round


def test_picasa_round_felfele_kerekit_a_felnel():
    """A C `floor(x + 0.5)` idióma: a 0,5 MINDIG felfelé megy.

    A Python beépített `round()`-ja bankári kerekítést csinál (0,5 → páros),
    ami minden második egész felénél egy képpontnyi eltérést adna."""
    assert picasa_round(0.5) == 1
    assert picasa_round(1.5) == 2
    assert picasa_round(2.5) == 3
    assert picasa_round(2.49) == 2


def test_fit_inside_arányt_tart():
    """A 3:2 kép egy 100×100-as keretben 100×67 lesz (szélességre illeszt)."""
    assert fit_inside(300, 200, 100, 100) == (100, 67)


def test_fit_inside_magassagra_illeszt_allo_kepnel():
    assert fit_inside(200, 300, 100, 100) == (67, 100)


def test_fit_inside_a_0_499_es_toldalek_szamit():
    """A Picasa `+0.499`-cel tágítja a célkeretet, ezért a határesetben
    egy képponttal NAGYOBB méret jön ki, mint a naiv `round(s*src)`-ből.

    Példa: 3×1-es kép egy 10×10-es keretben. Naivan s = 10/3 = 3,333…,
    a magasság `round(3,333)` = 3. A Picasa képlete s = 10,499/3 = 3,4997,
    így a magasság 3 marad, de a szélesség 10-re kerekül — az illesztés
    tehát a hosszabb oldalt PONTOSAN a keretre viszi, nem alá."""
    assert fit_inside(3, 1, 10, 10) == (10, 3)


def test_fit_inside_azonos_arany_pontos():
    assert fit_inside(400, 300, 800, 600) == (800, 600)


@pytest.mark.parametrize("bad", [(0, 10), (10, 0), (-1, 5)])
def test_fit_inside_ervenytelen_forras(bad):
    with pytest.raises(ValueError):
        fit_inside(bad[0], bad[1], 10, 10)


def test_msvc_uniform01_a_tartomanyban_marad():
    """Az MSVC `_rand()` 0…32767-es értékéből a bittrükk [0,1)-et csinál."""
    assert msvc_uniform01(0) == 0.0
    assert 0.0 <= msvc_uniform01(32767) < 1.0
    assert msvc_uniform01(16384) == pytest.approx(0.5, abs=1e-4)


def test_msvc_uniform01_monoton():
    values = [msvc_uniform01(r) for r in range(0, 32768, 997)]
    assert values == sorted(values)


def test_msvc_uniform01_ervenytelen_bemenet():
    with pytest.raises(ValueError):
        msvc_uniform01(32768)
