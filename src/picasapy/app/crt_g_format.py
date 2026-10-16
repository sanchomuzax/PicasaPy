"""Az eredeti Picasa CRT-jének `%.3g` / `%g` számformátuma (#4579).

Az eredeti `_vsnprintf` (`0x00c08769`) a pontos fél értéket a nullától ELKEREKÍTI
(`22.25 -> "22.3"`, `1.125 -> "1.13"`), a Python `format(x, ".3g")` viszont a
bináris érték szerint, párosra (`22.2`, `1.12`). A kitevős alak háromjegyű
kitevőt használ (`1e+003`). Spec: `picasa-metaadat-tulajdonsagok.md` 17. A.
"""

from __future__ import annotations

import math
from decimal import ROUND_HALF_UP, Decimal

#: A közös érték→szöveg átalakító küszöbei (`0x00cf40b8`, `0x00cf4c40`).
_ALSO_HATAR = 0.01
_FELSO_HATAR = 999.0


def crt_g(value: float, precision: int) -> str:
    """`%.<precision>g` az eredeti CRT kerekítésével (fél érték nullától el)."""
    if not math.isfinite(value):
        return str(value)
    if value == 0:
        return "0"
    pontos = Decimal(value)
    elojel = "-" if pontos < 0 else ""
    pontos = abs(pontos)
    kitevo = pontos.adjusted()
    kerekitett = _kerekit(pontos, kitevo, precision)
    if kerekitett.adjusted() != kitevo:  # pl. 999.6 -> 1.00e3
        kitevo = kerekitett.adjusted()
        kerekitett = _kerekit(pontos, kitevo, precision)
    if -4 <= kitevo < precision:
        tizedes = max(precision - 1 - kitevo, 0)
        return elojel + _vagd(f"{kerekitett:.{tizedes}f}")
    mantissza = _vagd(f"{kerekitett.scaleb(-kitevo):.{precision - 1}f}")
    return f"{elojel}{mantissza}e{'-' if kitevo < 0 else '+'}{abs(kitevo):03d}"


def _kerekit(pontos: Decimal, kitevo: int, precision: int) -> Decimal:
    lepeskoz = Decimal(1).scaleb(kitevo - precision + 1)
    return pontos.quantize(lepeskoz, rounding=ROUND_HALF_UP)


def _vagd(szoveg: str) -> str:
    """A záró nullák és az árva tizedespont elhagyása (`%g`)."""
    if "." in szoveg:
        szoveg = szoveg.rstrip("0").rstrip(".")
    return szoveg


def picasa_szam(value: float) -> str:
    """A `0x0040fed0` átalakító: `%.3g`, ha 0,01 <= v <= 999, különben `%g`."""
    if _ALSO_HATAR <= value <= _FELSO_HATAR:
        return crt_g(value, 3)
    return crt_g(value, 6)
