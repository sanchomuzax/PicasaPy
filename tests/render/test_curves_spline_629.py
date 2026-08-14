"""A töréspontos görbék TERMÉSZETES KÖBÖS SPLINE-ja — #629.

Az eredeti Picasa `AdjustCurves`-e nem lineárisan interpolál a töréspontok
között, hanem természetes köbös spline-nal (`0x008f3290` + `0x008f33b0`, a
#626 dekompilálási kör). A korábbi lineáris közelítés a valódi
`filterdesc.xml` görbéken a **60-as évek** effektnél 21,6, a
**Kinemaszkópnál** 17,5 szintet tévedett.

**A referenciát ez a fájl a KÉPLETBŐL számolja**, nem egy könyvtárból — így
ha a megvalósítás alatta kicserélődik (pl. SciPy-ra), a teszt akkor is a
Picasa algoritmusát méri, nem önmagát.
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.render.curves import curve_lut
from picasapy.render.glimmer_tone import (
    _SIXTIES_BLUE,
    _SIXTIES_GREEN,
    _SIXTIES_MASTER,
    _SIXTIES_RED,
)


def _referencia_spline(points) -> np.ndarray:
    """A Numerical Recipes `spline` + `splint` közvetlen, ciklusos mása.

    Szándékosan a lehető legegyszerűbb, vektorizálatlan alak: ez a
    „papírról" leírt képlet, amivel a tényleges megvalósítást összevetjük.
    """
    xs = [float(p[0]) for p in points]
    ys = [float(p[1]) for p in points]
    n = len(xs)

    y2 = [0.0] * n
    u = [0.0] * n
    for i in range(1, n - 1):
        sig = (xs[i] - xs[i - 1]) / (xs[i + 1] - xs[i - 1])
        p = sig * y2[i - 1] + 2.0
        y2[i] = (sig - 1.0) / p
        u[i] = (ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) - (ys[i] - ys[i - 1]) / (
            xs[i] - xs[i - 1]
        )
        u[i] = (6.0 * u[i] / (xs[i + 1] - xs[i - 1]) - sig * u[i - 1]) / p
    y2[n - 1] = 0.0
    for k in range(n - 2, -1, -1):
        y2[k] = y2[k] * y2[k + 1] + u[k]

    out = []
    for x in range(256):
        if x <= xs[0]:
            out.append(ys[0])
            continue
        if x >= xs[-1]:
            out.append(ys[-1])
            continue
        # bináris keresés: a befoglaló szakasz
        lo, hi = 0, n - 1
        while hi - lo > 1:
            mid = (hi + lo) // 2
            if xs[mid] > x:
                hi = mid
            else:
                lo = mid
        h = xs[hi] - xs[lo]
        a = (xs[hi] - x) / h
        b = (x - xs[lo]) / h
        out.append(
            a * ys[lo]
            + b * ys[hi]
            + ((a**3 - a) * y2[lo] + (b**3 - b) * y2[hi]) * (h * h) / 6.0
        )
    return np.array(out, dtype=np.float64)


SIXTIES_GORBEK = {
    "master": _SIXTIES_MASTER,
    "red": _SIXTIES_RED,
    "green": _SIXTIES_GREEN,
    "blue": _SIXTIES_BLUE,
}


class TestKobosSpline:
    @pytest.mark.parametrize("nev", sorted(SIXTIES_GORBEK))
    def test_a_60as_evek_gorbei_a_keplettel_egyeznek(self, nev: str) -> None:
        """A 256 elemű LUT a képletből számolt referenciával egyezik."""
        pontok = SIXTIES_GORBEK[nev]

        np.testing.assert_allclose(
            curve_lut(pontok), _referencia_spline(pontok), atol=1e-9
        )

    def test_egy_otpontos_gorbe_is_egyezik(self) -> None:
        """Kinemaszkóp-jellegű, öt töréspontos görbe."""
        pontok = (
            (0.0, 0.0),
            (48.0, 32.0),
            (128.0, 140.0),
            (200.0, 220.0),
            (255.0, 255.0),
        )

        np.testing.assert_allclose(
            curve_lut(pontok), _referencia_spline(pontok), atol=1e-9
        )

    def test_ketpontos_gorbenel_azonos_a_linearissal(self) -> None:
        """A Színinvertálás/Neon/Ceruzarajz kimenete NEM változhat: két
        pontnál mindkét végén nulla a második derivált, a köbös tag eltűnik."""
        pontok = ((0.0, 255.0), (255.0, 0.0))

        np.testing.assert_allclose(
            curve_lut(pontok),
            np.interp(np.arange(256, dtype=np.float64), (0.0, 255.0), (255.0, 0.0)),
            atol=1e-9,
        )

    def test_a_torespontokat_pontosan_atveszi(self) -> None:
        """A spline INTERPOLÁL: a töréspontokban a megadott értéket adja."""
        pontok = _SIXTIES_MASTER
        lut = curve_lut(pontok)

        for x, y in pontok:
            assert lut[int(x)] == pytest.approx(y, abs=1e-9)

    def test_a_linearistol_valo_elteres_erdemi(self) -> None:
        """A jegy állítása: a 60-as évek mestergörbéjén a lineáris közelítés
        húsz szintnél is többet téved — ez nem kerekítési zaj."""
        pontok = _SIXTIES_MASTER
        linearis = np.interp(
            np.arange(256, dtype=np.float64),
            [p[0] for p in pontok],
            [p[1] for p in pontok],
        )

        elteres = np.abs(curve_lut(pontok) - linearis)

        assert elteres.max() > 15.0, (
            f"a legnagyobb eltérés csak {elteres.max():.1f} szint"
        )


class TestATartomanyonKivul:
    def test_a_szelso_erteket_tartja(self) -> None:
        """Nem extrapolálunk: a köbös tag a tartományon kívül túllőne."""
        pontok = ((32.0, 20.0), (128.0, 160.0), (200.0, 210.0))
        lut = curve_lut(pontok)

        assert lut[0] == pytest.approx(20.0)
        assert lut[31] == pytest.approx(20.0)
        assert lut[255] == pytest.approx(210.0)

    def test_a_hibas_bemenet_tovabbra_is_ValueError(self) -> None:
        with pytest.raises(ValueError):
            curve_lut(((0.0, 0.0),))
        with pytest.raises(ValueError):
            curve_lut(((10.0, 0.0), (10.0, 5.0)))
