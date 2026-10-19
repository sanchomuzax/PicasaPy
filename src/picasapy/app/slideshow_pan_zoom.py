"""A diavetítés Pan and Zoom kivágásainak tiszta geometriája (#5258, #5351)."""

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
_TORT_NEVEZO = 32768
_MAX_TORT = 32767 / 32768
_LCG_MULTIPLIER = 0x343FD
_LCG_INCREMENT = 0x269EC3
_LCG_MASK = 0xFFFFFFFF
# Az egész alap illesztése (`0x009b4aa0`, #5225 4.4): a forrásméret felé
# tolt arány és a kerekítés előtti apró hozzáadás.
_ILLESZTES_FELE = 0.499
_ILLESZTES_APROSAG = 0.00001


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


def _alap_meret(
    forras_szelesseg: float,
    forras_magassag: float,
    nezet_szelesseg: float,
    nezet_magassag: float,
) -> tuple[int, int]:
    """A nézet képarányát tartó egész alaptéglalap, amely a forrásba illeszkedik.

    A kisebb arány adja a skálát. A kerekítési mód nyitott (#5225); itt a
    legközelebbi egész a választás, az x87 alapbeállítása szerint.
    """
    skala = min(
        (forras_szelesseg + _ILLESZTES_FELE) / nezet_szelesseg,
        (forras_magassag + _ILLESZTES_FELE) / nezet_magassag,
    )
    return (
        round(nezet_szelesseg * skala + _ILLESZTES_APROSAG),
        round(nezet_magassag * skala + _ILLESZTES_APROSAG),
    )


def _alap_poziciok(
    forras_szelesseg: float,
    forras_magassag: float,
    alap_szelesseg: int,
    alap_magassag: int,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Az A és a B alaptéglalap bal felső sarka; a B a forrás szélei felé tolódik."""
    b_x = 0.0
    if forras_szelesseg > alap_szelesseg:
        b_x = forras_szelesseg - alap_szelesseg
    b_y = 0.0
    if forras_magassag > alap_magassag:
        b_y = forras_magassag - alap_magassag
    return (0.0, 0.0), (b_x, b_y)


def _ket_csere(
    poziciok: tuple[tuple[float, float], tuple[float, float]],
    helyi_forras: Callable[[], float],
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Két helyi LCG-csere a skálázás előtt; a 16. állapotbit páratlansága dönt."""
    for _ in range(2):
        if round(_huz_tort(helyi_forras) * _TORT_NEVEZO) & 1:
            poziciok = (poziciok[1], poziciok[0])
    return poziciok


def _u_es_v(helyi_forras: Callable[[], float]) -> tuple[float, float]:
    """A helyi LCG u, v párja; újrahúzza, amíg a különbség el nem éri a küszöböt."""
    while True:
        u = _huz_tort(helyi_forras)
        v = _huz_tort(helyi_forras)
        if abs(u - v) >= _UJRAHUZASI_HATAR:
            return u, v


def _eltolas(
    nagyobb: bool,
    rhos: list[float],
    forras: tuple[float, float],
) -> tuple[float, float]:
    """A nagyobb skálájú jelölt a ρ0, ρ1 párt, a kisebb a ρ3, ρ2 párt kapja."""
    forras_szelesseg, forras_magassag = forras
    rho0, rho1, rho2, rho3 = rhos
    if nagyobb:
        return (
            forras_szelesseg * (_ELTOLAS_MERTEKE * rho1 - _ELTOLAS_KOZEPE),
            forras_magassag * (_ELTOLAS_MERTEKE * rho0 - _ELTOLAS_KOZEPE),
        )
    return (
        forras_szelesseg * (_ELTOLAS_MERTEKE * rho3 - _ELTOLAS_KOZEPE),
        -forras_magassag * _ELTOLAS_MERTEKE * rho2,
    )


def _nyujtott_kivagas(
    pozicio: tuple[float, float],
    alap: tuple[int, int],
    meret: float,
    eltolas: tuple[float, float],
    forras: tuple[float, float],
) -> PanZoomRect:
    """Az alaptéglalap a saját közepe körül nyújtva, eltolva és határolva."""
    x0, y0 = pozicio
    alap_szelesseg, alap_magassag = alap
    dx, dy = eltolas
    szelesseg = alap_szelesseg * meret
    magassag = alap_magassag * meret
    return _hataron_belul(
        x0 + (alap_szelesseg - szelesseg) / 2 + dx,
        y0 + (alap_magassag - magassag) / 2 + dy,
        szelesseg,
        magassag,
        *forras,
    )


def pan_zoom_rectangles(
    forras_szelesseg: float,
    forras_magassag: float,
    nezet_szelesseg: float,
    nezet_magassag: float,
    helyi_forras: Callable[[], float],
    crt_forras: Callable[[], float],
) -> tuple[PanZoomRect, PanZoomRect]:
    """Két véletlen jelölt kivágást készít az egész alaptéglalapokból.

    A `helyi_forras` adja a két cserét, majd az `u`, `v` törteket; a
    `crt_forras` a négy eltolási törtet (`ρ0…ρ3`). Mindkét forrás a
    ``0 … 32767/32768`` tartományú törtet ad, így rögzített forrás mellett a
    függvény determinisztikus.
    """
    forras_szelesseg = _ellenoriz_meret("forrásszélesség", forras_szelesseg)
    forras_magassag = _ellenoriz_meret("forrásmagasság", forras_magassag)
    nezet_szelesseg = _ellenoriz_meret("nézetszélesség", nezet_szelesseg)
    nezet_magassag = _ellenoriz_meret("nézetmagasság", nezet_magassag)

    alap = _alap_meret(
        forras_szelesseg, forras_magassag, nezet_szelesseg, nezet_magassag
    )
    poziciok = _ket_csere(
        _alap_poziciok(forras_szelesseg, forras_magassag, *alap),
        helyi_forras,
    )
    u, v = _u_es_v(helyi_forras)
    rhos = [_huz_tort(crt_forras) for _ in range(4)]

    forras = (forras_szelesseg, forras_magassag)
    a_nagyobb = u > v
    a = _nyujtott_kivagas(
        poziciok[0],
        alap,
        _ALAP_MERET + _MERET_VALTOZAS * u,
        _eltolas(a_nagyobb, rhos, forras),
        forras,
    )
    b = _nyujtott_kivagas(
        poziciok[1],
        alap,
        _ALAP_MERET + _MERET_VALTOZAS * v,
        _eltolas(not a_nagyobb, rhos, forras),
        forras,
    )
    return a, b


def _lcg_fraction_source(seed: int | None = None) -> Callable[[], float]:
    """MSVC-LCG tört-forrás: a felső 15 bit adja a 0…32767/32768 törtet.

    A slideshow eredeti CRT-szálmagja nem ismert; minden forrás (a helyi és a
    CRT is) a Python véletlenforrásából kap új magot.
    """
    state = random.getrandbits(32) if seed is None else int(seed) & _LCG_MASK

    def kovetkezo() -> float:
        nonlocal state
        state = (state * _LCG_MULTIPLIER + _LCG_INCREMENT) & _LCG_MASK
        return ((state >> 16) & 0x7FFF) / _TORT_NEVEZO

    return kovetkezo


def qml_pan_zoom_rectangles(
    forras_szelesseg: int,
    forras_magassag: int,
    nezet_szelesseg: int,
    nezet_magassag: int,
) -> list[dict[str, float]]:
    """QML-nek átadható kivágástérkép-lista a véletlen forrásokkal."""
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
            _lcg_fraction_source(),
        )
    ]
