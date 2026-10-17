"""A diavetítés Pan and Zoom kivágásainak tiszta geometriája (#5258)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import math
import random


_ALAP_MERET = 0.75
_MERET_VALTOZAS = 0.2
_ELTOLAS_KOZEPE = 0.1
_ELTOLAS_MERTEKE = 0.2
_UJRAHUZASI_HATAR = 0.5
_MAX_TORT = 32767 / 32768
_LCG_MULTIPLIER = 0x343FD
_LCG_INCREMENT = 0x269EC3
_LCG_MASK = 0xFFFFFFFF


@dataclass(frozen=True, slots=True)
class PanZoomRect:
    """Forráspixel-koordinátájú, határolt kivágás."""

    x: float
    y: float
    width: float
    height: float


def _ellenoriz_meret(nev: str, ertek: float) -> float:
    ertek = float(ertek)
    if not math.isfinite(ertek) or ertek <= 0:
        raise ValueError(f"A(z) {nev} pozitív, véges méret legyen")
    return ertek


def _huz_tort(veletlenforras: Callable[[], float]) -> float:
    tort = float(veletlenforras())
    if not math.isfinite(tort) or not 0 <= tort <= _MAX_TORT:
        raise ValueError("A véletlen törtnek 0 és 32767/32768 közé kell esnie")
    return tort


def _hataron_belul(
    x: float, y: float, width: float, height: float,
    forras_szelesseg: float, forras_magassag: float,
) -> PanZoomRect:
    """A sarkot mozgatja, a már kiszámolt méretet változatlanul hagyja."""
    x = min(max(x, 0.0), forras_szelesseg - width)
    y = min(max(y, 0.0), forras_magassag - height)
    return PanZoomRect(x, y, width, height)


def pan_zoom_rectangles(
    forras_szelesseg: float,
    forras_magassag: float,
    nezet_szelesseg: float,
    nezet_magassag: float,
    veletlenforras: Callable[[], float],
) -> tuple[PanZoomRect, PanZoomRect]:
    """Két véletlen jelölt kivágást készít az illesztett alapból.

    A forrásban elférő, a nézet képarányát tartó legnagyobb középső
    alaptéglalapból indul. A `veletlenforras` minden hívása a
    ``0 … 32767/32768`` tartományú törtet ad; a függvény így rögzített
    forrás mellett teljesen determinisztikus.
    """
    forras_szelesseg = _ellenoriz_meret("forrásszélesség", forras_szelesseg)
    forras_magassag = _ellenoriz_meret("forrásmagasság", forras_magassag)
    nezet_szelesseg = _ellenoriz_meret("nézetszélesség", nezet_szelesseg)
    nezet_magassag = _ellenoriz_meret("nézetmagasság", nezet_magassag)

    nezet_arany = nezet_szelesseg / nezet_magassag
    forras_arany = forras_szelesseg / forras_magassag
    if forras_arany > nezet_arany:
        alap_magassag = forras_magassag
        alap_szelesseg = alap_magassag * nezet_arany
    else:
        alap_szelesseg = forras_szelesseg
        alap_magassag = alap_szelesseg / nezet_arany

    cx = forras_szelesseg / 2
    cy = forras_magassag / 2
    while True:
        u = _huz_tort(veletlenforras)
        v = _huz_tort(veletlenforras)
        if abs(u - v) >= _UJRAHUZASI_HATAR:
            break

    rho0 = _huz_tort(veletlenforras)
    rho1 = _huz_tort(veletlenforras)
    rho2 = _huz_tort(veletlenforras)
    rho3 = _huz_tort(veletlenforras)

    meret_a = _ALAP_MERET + _MERET_VALTOZAS * u
    meret_b = _ALAP_MERET + _MERET_VALTOZAS * v
    a = _hataron_belul(
        cx - alap_szelesseg * meret_a / 2
        + forras_szelesseg * (_ELTOLAS_MERTEKE * rho1 - _ELTOLAS_KOZEPE),
        cy - alap_magassag * meret_a / 2
        + forras_magassag * (_ELTOLAS_MERTEKE * rho0 - _ELTOLAS_KOZEPE),
        alap_szelesseg * meret_a,
        alap_magassag * meret_a,
        forras_szelesseg,
        forras_magassag,
    )
    b = _hataron_belul(
        cx - alap_szelesseg * meret_b / 2
        + forras_szelesseg * (_ELTOLAS_MERTEKE * rho3 - _ELTOLAS_KOZEPE),
        cy - alap_magassag * meret_b / 2
        - forras_magassag * _ELTOLAS_MERTEKE * rho2,
        alap_szelesseg * meret_b,
        alap_magassag * meret_b,
        forras_szelesseg,
        forras_magassag,
    )

    # A bináris egy további helyi-LCG ága a jelöltek sorrendjét felcserélheti.
    if _huz_tort(veletlenforras) >= _UJRAHUZASI_HATAR:
        return b, a
    return a, b


def _lcg_fraction_source(seed: int | None = None) -> Callable[[], float]:
    """Helyi MSVC-LCG: a felső 15 bit adja a 0…32767/32768 törtet.

    A slideshow eredeti CRT-szálmagja nem ismert; minden illesztés a Python
    véletlenforrásából kap egy új, helyi LCG-magot.
    """
    state = random.getrandbits(32) if seed is None else int(seed) & _LCG_MASK

    def kovetkezo() -> float:
        nonlocal state
        state = (state * _LCG_MULTIPLIER + _LCG_INCREMENT) & _LCG_MASK
        return ((state >> 16) & 0x7FFF) / 32768

    return kovetkezo


def qml_pan_zoom_rectangles(
    forras_szelesseg: int,
    forras_magassag: int,
    nezet_szelesseg: int,
    nezet_magassag: int,
) -> list[dict[str, float]]:
    """QML-nek átadható kivágástérkép-lista a véletlen forrással."""
    return [
        {
            "x": rect.x,
            "y": rect.y,
            "width": rect.width,
            "height": rect.height,
        }
        for rect in pan_zoom_rectangles(
            forras_szelesseg,
            forras_magassag,
            nezet_szelesseg,
            nezet_magassag,
            _lcg_fraction_source(),
        )
    ]
