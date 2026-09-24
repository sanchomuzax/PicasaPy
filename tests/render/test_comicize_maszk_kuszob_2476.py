"""A natív pontmaszk alakja (#2476).

A `TiledImageMask` mind a tizenkét tartalékértéke ki van olvasva a
konstruktorból (`0x00bba250`, #2476): `alphaMax = 1,0`, `alphaMin = 0,0`,
`scaleWidth/Height = 0,8`, mind a négy `padding` nulla — tehát a maszk egy
ÁLLANDÓ pontrács, a közepén 1,0-ról a csempe 0,8-szoros peremén 0,0-ra futó
lineáris rámpával.

A korábbi első osztály azt mérte, hogy a maszk küszöbe ugyanazt a sugarat
adja, mint a régi `halftone_branch` küszöb-modell. A #3522 óta a Comicize a
maszkot a `filterdesc.xml` láncában, `PartialMask`-ként használja, a
küszöb-modell megszűnt — az az osztály ezért törölve.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.halftone import (
    DOT_ALPHA_MAX,
    DOT_SCALE,
    tiled_dot_mask,
    tiled_dot_ramp,
)

_CSEMPE = 24


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
