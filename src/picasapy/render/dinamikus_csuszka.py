"""A képmérettől függő tartományú csúszkák vetítése (#3596).

Az eredeti a Glimmer-leíró csúszkáit a `0x00bb25f0`-ban építi fel: ha a
`minimum`/`maximum`/`value` kifejezés bármelyike a képtől függ, a csúszka
`glimmer::DynamicRangeSlider` (konstruktor `0x00bbd230`). Ennek a
`.picasa.ini`-ben tárolt értéke **SZÁZALÉK**: a `0x00bbd3d0` előbb 0 és
100 közé szorítja, majd a pillanatnyi tartományra vetíti
(`0x00bbd456`–`0x00bbd478`). Spec: `docs/specs/filters-decoded.md` (#3591).

A leíróban öt ilyen csúszka van — `PicnikFocalPixelate`/`FocalZoom`
`Radius`, `RoundedEdges`/`Border` `CornerRadius`, `Border`
`CaptionHeight`; minden más csúszka nyers értéket tárol.
"""

from __future__ import annotations

_SZAZ = 100.0


def dinamikus_csuszka_ertek(szazalek: float, minimum: float, maximum: float) -> float:
    """`minimum + (maximum − minimum) · min(max(t, 0), 100) / 100`."""
    t = min(max(float(szazalek), 0.0), _SZAZ)
    return minimum + (maximum - minimum) * t / _SZAZ


def fel_rovidebb_el(height: float, width: float) -> float:
    """A fókuszsugár és a sarok-rádiusz felső vége: `min(W, H)/2`."""
    return min(height, width) / 2.0


def felirat_maximum(height: float) -> float:
    """A `Border` feliratsávjának felső vége: `imageheight/6`."""
    return height / 6.0
