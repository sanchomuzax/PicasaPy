"""A Picasa diááttűnésének időből számolt alfa-görbéje (#6920)."""

from __future__ import annotations

from math import exp


def _gorbe(y: float) -> float:
    """A 0x0072df60 nemlineáris görbéje a 38.2.270 szerint."""
    if y < 1.0:
        return y - 1.0 + exp(-y)
    a = exp(-1.0)
    return a + (1.0 - a) * (1.0 - exp(-(y - 1.0)))


_NORMALIZALO = 1.0 / _gorbe(8.0)


def dissolve_alpha256(elapsed_seconds: float, slide_seconds: float) -> int:
    """Visszaadja a bináris Dissolve alfa-kódját a 0…256 tartományban.

    A `SimpleSlideshow=1` ág a diaidő első 1,5-szeresét használja progresszióként,
    majd a `g(8x)` görbét normalizálja. A függvény tisztán számol, nem módosít
    állapotot, és a bináris csonkolást követi.
    """
    eltelt = float(elapsed_seconds)
    diaido = float(slide_seconds)
    if diaido <= 0.0:
        return 256 if eltelt >= 0.0 else 0

    x = min(1.0, max(0.0, 1.5 * eltelt / diaido))
    y = 8.0 * x
    alfa = int(256.0 * _NORMALIZALO * _gorbe(y))
    return min(256, max(0, alfa))


def dissolve_duration_ms(slide_seconds: float) -> int:
    """A Dissolve görbe telítési ideje: `T / 1,5` másodperc."""
    return round(1000.0 * float(slide_seconds) / 1.5)
