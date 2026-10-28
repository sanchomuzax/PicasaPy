"""RGB- és HSV-színátmenetek LUT-műveletei."""

from __future__ import annotations

import math

from picasapy.render.curves import validate_image
import numpy as np



# --- Gradiens-leképezés (GradientMap / HSVGradientMap) ------------------


#: #3421: a gradiens-LUT-ok INDEXE a képpont piros csatornája. A
#: `GradientMap` (`0x00bb87b0`) és a `HSVGradientMap` (`0x00bbc260`)
#: építője a színtáblát a közös futószalag (`0x00bcb2f0`) `+0x800`
#: rekeszébe írja (a BGRA `src[2]` bájtja), a másik kettőt nullázza — a
#: kimenet tehát csak a piros csatornától függ, nem a lumától.
_GRADIENS_INDEX_CSATORNA = 0



def _gradient_map_stop_positions(n: int) -> np.ndarray:
    """A `GradientMap` float32 stophelyei (#4090, #4092)."""
    positions = np.empty(n, dtype=np.float32)
    positions[0] = np.float32(0.0)
    for k in range(1, n - 1):
        # A natív kód double 255,0-val szoroz/oszt, majd dword floatba tárol.
        positions[k] = np.float32((k * 255.0) / (n - 1))
    positions[-1] = np.float32(255.0)
    return positions



def _gradient_map_weight(p_lo: float, p_hi: float, x: int) -> np.float32:
    """Az x87-hányados dword float32 tárolt súlya (#4090)."""
    x_f32 = np.float32(x)
    return np.float32((float(p_hi) - float(x_f32)) / (float(p_hi) - float(p_lo)))



def _gradient_map_interpolate_channel(
    lower: int, upper: int, p_lo: float, p_hi: float, x: int
) -> int:
    """Egy csatorna natív, float32 súlyú és `+0,5`-ös keverése."""
    weight = _gradient_map_weight(p_lo, p_hi, x)
    value = int(upper) + float(weight) * (int(lower) - int(upper))
    return max(0, min(255, math.trunc(value + 0.5)))



def gradient_map(image: np.ndarray, colors: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """`GradientMap`: a piros csatornából natív RGB-megálló-LUT-ot épít.

    A megállóhelyek és a csatornánkénti interpoláció a #4090/#4092 spec
    képletét követi; `colors` sorrendje **RGB** (#510). Az index továbbra
    is a képpont PIROS csatornája (#3421). A natív `< 8` bitminta-kapu a
    generált 0…255 LUT-on nem változtat elemet (n=2…256, 0/65 280), ezért
    nincs külön átvezetve.
    """
    validate_image(image)
    if len(colors) < 2:
        raise ValueError("Legalább két szín kell a gradienshez")
    positions = _gradient_map_stop_positions(len(colors))
    lut = np.empty((256, 3), dtype=np.uint8)
    for x in range(256):
        stop_lo = int(np.searchsorted(positions, np.float32(x), side="right")) - 1
        if stop_lo < 0:
            lut[x] = colors[0]
        elif stop_lo >= len(colors) - 1:
            lut[x] = colors[-1]
        else:
            p_lo = positions[stop_lo]
            p_hi = positions[stop_lo + 1]
            for channel in range(3):
                lut[x, channel] = _gradient_map_interpolate_channel(
                    colors[stop_lo][channel], colors[stop_lo + 1][channel], p_lo, p_hi, x
                )
    return lut[image[..., _GRADIENS_INDEX_CSATORNA]]



def _hsv_rgb_lut_f32(hue: np.ndarray, sat: np.ndarray, val: np.ndarray) -> np.ndarray:
    """A natív HSV → RGB (`0x00bbbe20`, #3814/#4309): `h`, `s`, `v`, `h6`
    és `f` float32; a p/q/t képletek x87-regiszterben futnak, majd eredményük
    float32-be tárolódik. A végső csatorna `csonk(x · 255)`, nincs +0,5.
    Spec: `docs/specs/filterdesc-registry.md`, „A HSV → RGB átalakítás".
    """
    f32 = np.float32
    h = np.mod(hue.astype(f32), f32(360.0))
    s = np.clip(sat.astype(f32), 0, 100) / f32(100.0)
    v = np.clip(val.astype(f32), 0, 100) / f32(100.0)
    h6 = (h / f32(360.0)) * f32(6.0)
    i = np.trunc(h6).astype(np.int64)
    f = h6 - i.astype(f32)
    # The native x87 expressions retain intermediates in register precision;
    # each completed p/q/t value is then stored as a float32 dword. Promoting
    # before evaluating the parenthesized expressions preserves that order.
    s64, v64, f64 = (values.astype(np.float64) for values in (s, v, f))
    p = (v64 * (1.0 - s64)).astype(f32)
    q = (v64 * (1.0 - f64 * s64)).astype(f32)
    t = (v64 * (1.0 - s64 * (1.0 - f64))).astype(f32)
    szektor = i % 6
    r = np.choose(szektor, (v, q, p, p, t, v))
    gr = np.choose(szektor, (t, v, v, q, p, p))
    b = np.choose(szektor, (p, p, t, v, v, q))
    rgb = np.stack([r, gr, b], axis=-1).astype(np.float64) * 255.0
    return np.clip(np.trunc(rgb), 0, 255).astype(np.uint8)



def hsv_gradient_map(
    image: np.ndarray,
    stops: tuple[tuple[float, float, float, float], ...],
    hue_offset: float = 0.0,
) -> np.ndarray:
    """`HSVGradientMap`: a PIROS csatornához (#3421) rendelt (pozíció,
    hue°, sat%, val%) töréspontok interpolációja HSV-térben, majd RGB-re
    konvertálva — a `HeatMap` effekt implementációja. A stoppozíciók
    float32 LUT-indexek; az S/V lineárisan interpolál, a hue pedig a natív
    szabály szerint 180° fölött a rövidebb köríven fut.

    #3814: az RGB-re alakítás a natív lebegőpontos képlettel, csonkolva
    történik (`_hsv_rgb_lut_f32`); a `hueOffset` float32-ben adódik a
    keverés utáni színezethez, a körbefordítást az átalakító végzi.
    """
    validate_image(image)
    f32 = np.float32
    positions = np.asarray([stop[0] for stop in stops], dtype=np.float32)
    hues = np.asarray([stop[1] for stop in stops], dtype=np.float32)
    sats = np.asarray([stop[2] for stop in stops], dtype=np.float32)
    vals = np.asarray([stop[3] for stop in stops], dtype=np.float32)
    hue_lut = np.empty(256, dtype=np.float32)
    sat_lut = np.empty(256, dtype=np.float32)
    val_lut = np.empty(256, dtype=np.float32)
    for x in range(256):
        upper = int(np.searchsorted(positions, f32(x), side="left"))
        if upper == 0:
            hue_lut[x], sat_lut[x], val_lut[x] = hues[0], sats[0], vals[0]
        elif upper == len(positions):
            hue_lut[x], sat_lut[x], val_lut[x] = hues[-1], sats[-1], vals[-1]
        elif positions[upper] == f32(x):
            hue_lut[x], sat_lut[x], val_lut[x] = hues[upper], sats[upper], vals[upper]
        else:
            lower = upper - 1
            p_lower = float(positions[lower])
            p_upper = float(positions[upper])
            weight = f32((p_upper - float(f32(x))) / (p_upper - p_lower))
            h_lower = float(hues[lower])
            h_upper = float(hues[upper])
            if abs(h_lower - h_upper) > 180.0:
                if h_lower < h_upper:
                    h_lower += 360.0
                elif h_upper < h_lower:
                    h_upper += 360.0
            hue_lut[x] = f32(h_upper + float(weight) * (h_lower - h_upper))
            sat_lut[x] = f32(float(sats[upper]) + float(weight) * (float(sats[lower]) - float(sats[upper])))
            val_lut[x] = f32(float(vals[upper]) + float(weight) * (float(vals[lower]) - float(vals[upper])))
    hue_lut += f32(hue_offset)
    rgb_lut = _hsv_rgb_lut_f32(hue_lut, sat_lut, val_lut)
    return rgb_lut[image[..., _GRADIENS_INDEX_CSATORNA]]
