"""A képmérettől függő tartományú csúszkák vetítése (#3596).

Az eredeti a Glimmer-leíró csúszkáit a `0x00bb25f0`-ban építi fel: ha a
`minimum`/`maximum`/`value` kifejezés bármelyike a képtől függ, a csúszka
`glimmer::DynamicRangeSlider` (konstruktor `0x00bbd230`). Ennek a
`.picasa.ini`-ben tárolt értéke **SZÁZALÉK**: a `0x00bbd3d0` előbb 0 és
100 közé szorítja, majd a pillanatnyi tartományra vetíti
(`0x00bbd456`–`0x00bbd478`). Spec: `docs/specs/filters-decoded.md` (#3591).

A tartomány két végét double-ként értékeli ki, de **float32-be menti**
(`fstp dword` @ `0x00bbd40d`, `0x00bbd422`), és abból vetít (#3768,
`docs/specs/filterdesc-registry.md`, „A `Border` sarka és feliratsávja —
MÉRVE”). 640-es képen így `H/6 = 106,666664`, a 60 %-os feliratsáv
`63,9999985` — a csonkító egésszé alakítás 63-at ad, nem 64-et.

A leíróban öt ilyen csúszka van — `PicnikFocalPixelate`/`FocalZoom`
`Radius`, `RoundedEdges`/`Border` `CornerRadius`, `Border`
`CaptionHeight`; minden más csúszka nyers értéket tárol.
"""

from __future__ import annotations

import struct

_SZAZ = 100.0


def _f32(ertek: float) -> float:
    """Az érték float32-be mentve, majd visszaolvasva."""
    return struct.unpack("<f", struct.pack("<f", float(ertek)))[0]


def dinamikus_csuszka_ertek(szazalek: float, minimum: float, maximum: float) -> float:
    """`f32(min) + (f32(max) − f32(min)) · min(max(t, 0), 100) / 100`."""
    t = min(max(float(szazalek), 0.0), _SZAZ)
    also = _f32(minimum)
    return also + (_f32(maximum) - also) * t / _SZAZ


def fel_rovidebb_el(height: float, width: float) -> float:
    """A fókuszsugár és a sarok-rádiusz felső vége: `min(W, H)/2`."""
    return min(height, width) / 2.0


def felirat_maximum(height: float) -> float:
    """A `Border` feliratsávjának felső vége: `imageheight/6`."""
    return height / 6.0


def felirat_sorok(szazalek: float, height: float) -> int:
    """A `Border` feliratsávja sorokban: a vetített érték CSONKÍTVA
    (`0x008eea90`: `or eax, 0xc00` + `fistp`)."""
    return max(0, int(dinamikus_csuszka_ertek(szazalek, 0.0, felirat_maximum(height))))
