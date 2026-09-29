"""A Comicize csemperácsa: nulla padding, képméretre feszítve (#1351).

## A bizonyíték forrása

A `glimmer::TiledImageMask` mind a 12 paramétere a szállított
`filterdesc.xml`-ben áll (a `Comicize` blokkjában) — **nem kell hozzá se
dekompiláció, se golden-export**:

* egyik maszk sem ad meg SEMMILYEN `padding` értéket ⇒ mind a négy **0**;
* a rács `width`/`height`-ja az `imagewidth`/`imageheight` ⇒ **pontosan a
  kép méretére** feszül;
* a 793. sor `PixelateImageOperation`-je eltolás nélküli, a 807. soré
  viszont `offsetX = offsetY = _nDotSize/2`.

⛔ **HELYESBÍTVE (#3876, #3878):** a natív alkalmazó (`0x00bbd150`) az
`offsetX`/`offsetY`-t kiértékeli, de NEM adja tovább a magnak
(`0x00bbd1d7`–`0x00bbd207`) — a két fázis pixelesítése AZONOS, csak a
maszk tolódik. A maszk- és a pixelesítő rács ráadásul középre igazított,
nem a `(0,0)` sarokból indul; ezeket a `test_comicize_maradek_3878.py`
őrzi. Ez a fájl a rács méretét és a részleges csempe kezelését őrzi.
"""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from picasapy.render.effects_artistic import apply_comicize, pixelate_centered
from picasapy.render.halftone import dot_size_for, tiled_dot_ramp


@pytest.fixture
def kep() -> np.ndarray:
    """Színátmenetes próbakép — a raszter így minden tónuson dolgozik."""
    ys, xs = np.mgrid[0:120, 0:213]
    alap = ((xs / 213.0) * 255.0).astype(np.uint8)
    return np.dstack([alap, alap, alap])


class TestACsempemeret:
    @pytest.mark.parametrize(
        "szelesseg,vart",
        [(70, 2), (140, 3), (213, 4), (700, 11), (1, 1)],
    )
    def test_a_kepletet_koveti(self, szelesseg, vart):
        """`round(imagewidth / 70) + 1` — a natív képlet."""
        assert dot_size_for(szelesseg) == vart


class TestARacsAKepMereteReFeszul:
    def test_a_ramp_alakja_PONTOSAN_a_kepe(self):
        """Nincs szegély-kiterjesztés: a rács mérete = a kép mérete."""
        ramp = tiled_dot_ramp(120, 213, 4)
        assert ramp.shape == (120, 213)

    def test_a_reszleges_csempe_a_jobb_szelen_NEM_hibazik(self):
        """`213 % 4 == 1` — a jobb szélső oszlop csempéje részleges.

        A képhatár vágja; nincs külön kezelés, és nincs kivétel sem.
        """
        szelesseg, dot = 213, dot_size_for(213)
        assert szelesseg % dot != 0, "a próba alapja megszűnt"
        ramp = tiled_dot_ramp(120, szelesseg, dot)
        assert ramp.shape == (120, szelesseg)
        assert np.isfinite(ramp).all(), "a részleges csempén NaN/inf keletkezett"

    def test_a_rács_horgonya_a_bal_felso_sarok(self):
        """`(0,0)` + offset — az első csempe a kép sarkából indul."""
        ramp = tiled_dot_ramp(8, 8, 4)
        #: a csempe KÖZEPÉN a rámpa 0 — a 4-es csempénél ez az (1,1) pont
        assert ramp[1, 1] < ramp[0, 0]
        assert ramp[1, 1] < ramp[3, 3]


class TestAPixelesitesnekNincsEltolasa:
    """#3878: a 807. sor eltolása a `Pixelate`-ben hatástalan."""

    def test_a_pixelesitonek_nincs_eltolas_parametere(self):
        parameterek = list(inspect.signature(pixelate_centered).parameters)
        assert parameterek == ["image", "block_w", "block_h"]

    def test_a_pixelesites_megorzi_a_kep_alakjat(self, kep):
        ki = pixelate_centered(kep, 4, 4)
        assert ki.shape == kep.shape


class TestAzEffektEgeszben:
    def test_lefut_es_valtoztat(self, kep):
        ki = apply_comicize(kep, 20.0, 50.0, 50.0)
        assert ki.shape == kep.shape
        assert ki.dtype == np.uint8
        assert not np.array_equal(ki, kep)

    def test_a_bemenetet_nem_valtoztatja(self, kep):
        elotte = kep.copy()
        apply_comicize(kep, 20.0, 50.0, 50.0)
        assert np.array_equal(kep, elotte)

    def test_nem_osztott_szelessegen_sem_hibazik(self):
        """`213 % dot != 0` — a jegy külön kikötése."""
        ys, xs = np.mgrid[0:97, 0:213]
        alap = ((xs / 213.0) * 255.0).astype(np.uint8)
        kep = np.dstack([alap, alap, alap])
        ki = apply_comicize(kep, 20.0, 50.0, 50.0)
        assert ki.shape == kep.shape
