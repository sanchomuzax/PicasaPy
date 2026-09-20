"""A natív pontmaszk és a mai sugár-moduláció AZONOSSÁGA (#2476).

A jegy címe azt állította, hogy „nálunk a tónus a sugarat modulálja, az
eredetiben állandó". A `TiledImageMask` mind a tizenkét tartalékértéke ki van
olvasva a konstruktorból (`0x00bba250`, #2476): `alphaMax = 1,0`,
`alphaMin = 0,0`, `scaleWidth/Height = 0,8`, mind a négy `padding` nulla —
tehát a maszk egy ÁLLANDÓ pontrács, a közepén 1,0-ról a csempe 0,8-szoros
peremén 0,0-ra futó lineáris rámpával.

Ez a fájl azt méri, hogy ez a két leírás UGYANAZ a szerkezet: az állandó
maszk KÜSZÖBE a (pixelesített) tónus pontosan azt a pontsugarat adja, amit a
`halftone_branch` számol. A kontroll-eset elhangolt skálával fut — ha a
mérés a hangolásra érzéketlen volna, az őr nem érne semmit.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.halftone import (
    DOT_ALPHA_MAX,
    DOT_SCALE,
    halftone_branch,
    tiled_dot_mask,
    tiled_dot_ramp,
)

_CSEMPE = 24
_MERET = _CSEMPE * 4
#: A pontosan a rámpára eső tónusokat kihagyjuk: ott a két oldal a
#: lebegőpontos egyenlőségen dől el, nem a szerkezeten.
_TIES_TURES = 1e-3


def _festek_a_mai_kodbol(tone: float) -> np.ndarray:
    """A mai ág festékes képpontjai: a lágyított perem 0,5-ös átmenete."""
    ink = np.full((_MERET, _MERET), tone * 255.0, np.float32)
    return halftone_branch(ink, _CSEMPE) < 127.5


def _festek_a_nativ_maszkbol(tone: float, skala: float = DOT_SCALE) -> np.ndarray:
    """A natív, ÁLLANDÓ maszk küszöbe a tónus."""
    maszk = tiled_dot_mask(_MERET, _MERET, _CSEMPE, scale=skala)
    return maszk > np.float32(tone)


def _nem_hatareset(tone: float, skala: float = DOT_SCALE) -> np.ndarray:
    maszk = tiled_dot_mask(_MERET, _MERET, _CSEMPE, scale=skala)
    return np.abs(maszk - np.float32(tone)) > _TIES_TURES


#: Az a tónus-szint, amelytől a pont MÉRETE a lágyított perem szélessége alá
#: esik (24 képpontos csempén). Efölött a mai ág a küszöb antialiasingjával
#: elnyeli az utolsó, képpont alatti szemcsét — a szerkezet ott nem dől el.
_KEPPONT_ALATTI_SZINT = 234


class TestAzAllandoMaszkEsASugarModulacioUgyanaz:
    def test_a_kepponthataron_kivul_nulla_az_elteres(self):
        """A két leírás UGYANAZ: 234 alatt egyetlen képpont sem tér el."""
        elteres = 0
        for szint in range(_KEPPONT_ALATTI_SZINT):
            tone = szint / 255.0
            elteres += int(
                np.count_nonzero(
                    (_festek_a_nativ_maszkbol(tone) != _festek_a_mai_kodbol(tone))
                    & _nem_hatareset(tone)
                )
            )
        assert elteres == 0, f"{elteres} képpont tér el a két leírás között"

    def test_a_maradek_elteres_EGYIRANYU_es_a_keppont_alatti_pontban_van(self):
        """A képpont alatti szemcsénél csak a MAI ág veszít festéket.

        Ez a lágyított perem (`_EDGE_SOFTNESS_PX`) hatása, nem a sugár-törvény
        eltérése: a natív maszk küszöbe még festéket ad, a mai ág viszont a
        perem-átmenettel a fele alá csillapítja. A #3390 méri ki, mi a helyes
        fedettségi profil — ez az őr addig rögzíti, hogy az eltérés IRÁNYA egy.
        """
        rossz_irany = 0
        for szint in range(_KEPPONT_ALATTI_SZINT, 256):
            tone = szint / 255.0
            nativ = _festek_a_nativ_maszkbol(tone)
            mai = _festek_a_mai_kodbol(tone)
            rossz_irany += int(np.count_nonzero(mai & ~nativ & _nem_hatareset(tone)))
        assert rossz_irany == 0, (
            f"{rossz_irany} képponton a MAI ág ad festéket a natív maszk nélkül"
        )

    def test_kontroll_az_elhangolt_skala_ELTERESt_ad(self):
        """Negatív kontroll: 0,8 helyett 0,9-es maszk-skálával nem egyezik."""
        elteres = 0
        for szint in range(0, _KEPPONT_ALATTI_SZINT, 8):
            tone = szint / 255.0
            elteres += int(
                np.count_nonzero(
                    (_festek_a_nativ_maszkbol(tone, skala=0.9) != _festek_a_mai_kodbol(tone))
                    & _nem_hatareset(tone, skala=0.9)
                )
            )
        assert elteres > 1000, f"a kontroll is egyezett ({elteres} eltérés)"


class TestANativMaszkAlakja:
    def test_a_kozepen_alphaMax_a_peremen_alphaMin(self):
        maszk = tiled_dot_mask(_CSEMPE, _CSEMPE, _CSEMPE)
        felezo = _CSEMPE // 2
        # a maximum a csempe közepén van, és `alphaMax`-hoz tapad (a
        # képpontközép fél képponttal a geometriai közép mellett van, ezért
        # nem pontosan 1,0)
        assert maszk.max() == maszk[felezo, felezo]
        assert maszk[felezo, felezo] == pytest.approx(DOT_ALPHA_MAX, abs=0.08)
        assert maszk[felezo, felezo] < DOT_ALPHA_MAX
        # a 0,8-szoros peremen KÍVÜL (a csempe sarka) már alphaMin
        assert maszk[0, 0] == pytest.approx(0.0)

    def test_a_rampa_linearis_a_sugarban(self):
        """A két megálló között lineáris — ez a `0x008f3970` két megállója."""
        maszk = tiled_dot_mask(_CSEMPE, _CSEMPE, _CSEMPE)
        ramp = tiled_dot_ramp(_CSEMPE, _CSEMPE, _CSEMPE)
        belul = ramp < DOT_SCALE
        vart = 1.0 - ramp[belul] / DOT_SCALE
        assert np.allclose(maszk[belul], vart, atol=1e-5)

    def test_alphaMin_emeli_a_padlot_alphaMax_a_tetot(self):
        maszk = tiled_dot_mask(_CSEMPE, _CSEMPE, _CSEMPE, alpha_min=0.3, alpha_max=0.7)
        assert maszk.min() == pytest.approx(0.3, abs=1e-6)
        assert maszk.max() == pytest.approx(0.7, abs=0.05)

    def test_az_ervenytelen_parameterek_elhasalnak(self):
        with pytest.raises(ValueError):
            tiled_dot_mask(8, 8, 4, alpha_min=1.5)
        with pytest.raises(ValueError):
            tiled_dot_mask(8, 8, 4, alpha_max=1.5)
        with pytest.raises(ValueError):
            tiled_dot_mask(8, 8, 4, scale=0.0)
