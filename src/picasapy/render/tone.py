"""Tónus-műveletek: fill light, highlights/shadows, színhőmérséklet,
semleges-szín pipetta és a `finetune2` kompozit.

A számértékek a golden-elemzés mérési pontjai (`docs/specs/filters-decoded.md`).
A fill a mért görbecsaládból interpolál; a highlights/shadows/temp/pipetta a
dokumentált pontokra illesztett közelítés (a teljes LUT-sweep a személyes
golden-kitben él, nem a repóban) — a pixelhű finomítás követő feladat.
"""

from __future__ import annotations

import re

import numpy as np

from picasapy.render.curves import (
    CurvePoints,
    apply_channel_luts,
    apply_lut,
    blend_luts,
    curve_lut,
    lut_ramp,
    validate_image,
)

# A fill görbecsalád mért pontjai (golden 1. kör): árnyék-emelő,
# fehérpont-tartó görbék; s=0 az identitás. Köztes s-re a szomszédos
# görbék lineáris keveréke (a sűrű sweepen mért hiba max 1,25/255).
_FILL_CURVES: tuple[tuple[float, CurvePoints], ...] = (
    (0.00, ((0.0, 0.0), (255.0, 255.0))),
    (0.25, ((0.0, 0.0), (32.0, 45.7), (128.0, 145.6), (224.0, 228.6), (255.0, 255.0))),
    (0.50, ((0.0, 0.0), (32.0, 69.7), (128.0, 168.6), (224.0, 234.6), (255.0, 255.0))),
    (0.75, ((0.0, 0.0), (32.0, 107.7), (128.0, 194.0), (224.0, 240.0), (255.0, 255.0))),
    (1.00, ((0.0, 0.0), (32.0, 162.7), (128.0, 218.0), (224.0, 243.0), (255.0, 255.0))),
)

# Highlights: fehérpont-húzás. Mérve: h=0,40-nél a 192-es bemenet fehérbe
# csap → a fehérpont 255 − h·157,5.
_HIGHLIGHTS_WHITEPOINT_DROP = 157.5
# Shadows: feketepont-húzás — a highlights tükör-közelítése (mért görbék a
# személyes golden-kitben; itt szimmetrikus modellt használunk).
_SHADOWS_BLACKPOINT_RISE = 157.5

# Színhőmérséklet (finetune2 p5): aszimmetrikus, mért csatorna-eltolások.
_TEMPERATURE_KNOTS = (-1.0, -0.5, 0.0, 1.0)
_TEMPERATURE_RED_DELTAS = (-50.0, -16.0, 0.0, 8.0)
_TEMPERATURE_BLUE_DELTAS = (91.0, 20.0, 0.0, -20.0)

# Semleges-szín pipetta: csillapított fehéregyensúly (mérve: a korrekció a
# teljes szürkevilág-korrekció ~50–75%-a).
_NEUTRAL_DAMPING = 0.6

_ARGB_PATTERN = re.compile(r"^[0-9a-fA-F]{8}$")


def _clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def _fill_lut(strength: float) -> np.ndarray:
    """A fill görbecsalád LUT-ja tetszőleges s∈[0..1] erősségre."""
    clamped = _clamp(strength, 0.0, 1.0)
    for (low_s, low_points), (high_s, high_points) in zip(
        _FILL_CURVES, _FILL_CURVES[1:]
    ):
        if low_s <= clamped <= high_s:
            weight = (clamped - low_s) / (high_s - low_s)
            return blend_luts(curve_lut(low_points), curve_lut(high_points), weight)
    return curve_lut(_FILL_CURVES[-1][1])


def apply_fill(image: np.ndarray, strength: float) -> np.ndarray:
    """Fill light (árnyék-emelés) a mért görbecsaládból interpolálva."""
    return apply_lut(image, _fill_lut(strength))


def apply_highlights(image: np.ndarray, strength: float) -> np.ndarray:
    """Csúcsfények erősítése: a fehérpont lineáris lehúzása."""
    validate_image(image)
    clamped = _clamp(strength, 0.0, 1.0)
    if clamped == 0.0:
        return image.copy()
    white_point = max(255.0 - _HIGHLIGHTS_WHITEPOINT_DROP * clamped, 1.0)
    # pontonkénti lineáris művelet → 256 elemű LUT (#140): képméret-független
    return apply_lut(image, lut_ramp() * (255.0 / white_point))


def apply_shadows(image: np.ndarray, strength: float) -> np.ndarray:
    """Árnyékok mélyítése: a feketepont lineáris felhúzása."""
    validate_image(image)
    clamped = _clamp(strength, 0.0, 1.0)
    if clamped == 0.0:
        return image.copy()
    black_point = _SHADOWS_BLACKPOINT_RISE * clamped
    scale = 255.0 / (255.0 - black_point)
    # pontonkénti lineáris művelet → 256 elemű LUT (#140): képméret-független
    return apply_lut(image, (lut_ramp() - black_point) * scale)


def apply_color_temperature(image: np.ndarray, temperature: float) -> np.ndarray:
    """Színhőmérséklet-eltolás a mért (aszimmetrikus) R/B deltákkal.

    Negatív érték hűt (B nő, R csökken), pozitív melegít; a hűtés jóval
    erősebb — a deltákat a mért pontok közt lineárisan interpoláljuk.
    """
    validate_image(image)
    clamped = _clamp(temperature, -1.0, 1.0)
    if clamped == 0.0:
        return image.copy()
    red_delta = float(np.interp(clamped, _TEMPERATURE_KNOTS, _TEMPERATURE_RED_DELTAS))
    blue_delta = float(np.interp(clamped, _TEMPERATURE_KNOTS, _TEMPERATURE_BLUE_DELTAS))
    # csatornánkénti eltolás → csatornánkénti LUT (#140): képméret-független
    ramp = lut_ramp()
    return apply_channel_luts(image, (ramp + red_delta, ramp, ramp + blue_delta))


def parse_neutral_argb(value: str) -> tuple[int, int, int] | None:
    """A finetune2 p4 (AARRGGBB hex) értelmezése.

    Nulla alfa = nincs kijelölt semleges szín → None; egyébként (R, G, B).
    """
    text = value.strip()
    if not _ARGB_PATTERN.match(text):
        raise ValueError(f"Érvénytelen AARRGGBB színérték: {value!r}")
    if int(text[0:2], 16) == 0:
        return None
    return (int(text[2:4], 16), int(text[4:6], 16), int(text[6:8], 16))


def apply_neutral_pipette(
    image: np.ndarray, neutral: tuple[int, int, int]
) -> np.ndarray:
    """Fehéregyensúly a kijelölt semlegesnek szánt szín alapján, csillapítva.

    A csatorna-erősítések a színt a saját szürkeátlaga felé húznák; a mért
    viselkedés szerint csak a korrekció egy része érvényesül
    (`_NEUTRAL_DAMPING`).
    """
    validate_image(image)
    red, green, blue = neutral
    gray = (red + green + blue) / 3.0
    if gray <= 0.0:
        return image.copy()
    # csatornánkénti gain → csatornánkénti LUT (#140): képméret-független
    ramp = lut_ramp()
    luts = []
    for value in (red, green, blue):
        if value <= 0:
            luts.append(ramp)
            continue
        gain = 1.0 + _NEUTRAL_DAMPING * (gray / value - 1.0)
        luts.append(ramp * gain)
    return apply_channel_luts(image, (luts[0], luts[1], luts[2]))


def apply_finetune2(
    image: np.ndarray,
    *,
    fill: float,
    highlights: float,
    shadows: float,
    neutral: tuple[int, int, int] | None,
    temperature: float,
) -> np.ndarray:
    """A `finetune2=1,p1,p2,p3,p4,p5` kompozit alkalmazása.

    p1=fill (a mért LUT azonos az önálló fill szűrőével), p2=highlights,
    p3=shadows, p4=semleges-szín pipetta, p5=színhőmérséklet. Az alkalmazási
    sorrend dokumentált feltevés (tónus előbb, szín utána).
    """
    validate_image(image)
    result = apply_fill(image, fill)
    result = apply_highlights(result, highlights)
    result = apply_shadows(result, shadows)
    if neutral is not None:
        result = apply_neutral_pipette(result, neutral)
    return apply_color_temperature(result, temperature)
