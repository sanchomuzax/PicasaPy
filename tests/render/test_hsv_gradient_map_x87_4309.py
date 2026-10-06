"""A HeatMap HSV→RGB LUT-ja az eredeti x87 kerekítését követi (#4309)."""

from __future__ import annotations

import hashlib

import numpy as np

from picasapy.render import glimmer_ops as g
from picasapy.render.glimmer_tone import _HEATMAP_STOPS


_NATIVE_HEATMAP_SHA256_RGB = "bdcfba4ba5fe99d9d5ad6f7f8e8179b3e18025e00d0472ae40d97006d9fa482b"
_NATIVE_HEATMAP_ANCHORS = {
    207: (255, 86, 0),
    210: (255, 70, 0),
    216: (255, 38, 0),
    219: (255, 22, 0),
    222: (255, 6, 0),
}


def _red_ramp() -> np.ndarray:
    image = np.zeros((1, 256, 3), dtype=np.uint8)
    image[0, :, 0] = np.arange(256, dtype=np.uint8)
    return image


def _spec_heatmap_reference() -> np.ndarray:
    """A HSV-stop és x87→float32 specifikáció skalár referencia-LUT-ja."""
    f32 = np.float32
    positions = np.asarray([stop[0] for stop in _HEATMAP_STOPS], dtype=f32)
    hues = np.asarray([stop[1] for stop in _HEATMAP_STOPS], dtype=f32)
    sats = np.asarray([stop[2] for stop in _HEATMAP_STOPS], dtype=f32)
    vals = np.asarray([stop[3] for stop in _HEATMAP_STOPS], dtype=f32)
    hue_lut = np.empty(256, dtype=f32)
    sat_lut = np.empty(256, dtype=f32)
    val_lut = np.empty(256, dtype=f32)

    for x in range(256):
        x_f32 = f32(x)
        upper = int(np.searchsorted(positions, x_f32, side="left"))
        if upper == 0:
            hue_lut[x], sat_lut[x], val_lut[x] = hues[0], sats[0], vals[0]
        elif upper == len(positions):
            hue_lut[x], sat_lut[x], val_lut[x] = hues[-1], sats[-1], vals[-1]
        elif positions[upper] == x_f32:
            hue_lut[x], sat_lut[x], val_lut[x] = hues[upper], sats[upper], vals[upper]
        else:
            lower = upper - 1
            weight = f32(
                (float(positions[upper]) - float(x_f32))
                / (float(positions[upper]) - float(positions[lower]))
            )
            hue_lut[x] = f32(
                float(hues[upper]) + float(weight) * (float(hues[lower]) - float(hues[upper]))
            )
            sat_lut[x] = f32(
                float(sats[upper]) + float(weight) * (float(sats[lower]) - float(sats[upper]))
            )
            val_lut[x] = f32(
                float(vals[upper]) + float(weight) * (float(vals[lower]) - float(vals[upper]))
            )

    h = np.mod(hue_lut, f32(360.0))
    s = np.clip(sat_lut, 0, 100) / f32(100.0)
    v = np.clip(val_lut, 0, 100) / f32(100.0)
    h6 = (h / f32(360.0)) * f32(6.0)
    sector = np.trunc(h6).astype(np.int64) % 6
    fraction = h6 - np.trunc(h6).astype(f32)

    # x87 uses 53-bit precision here; the native worker stores each final
    # p/q/t value as float32, rather than rounding each sub-operation to f32.
    s64, v64, f64 = (values.astype(np.float64) for values in (s, v, fraction))
    p = (v64 * (1.0 - s64)).astype(f32)
    q = (v64 * (1.0 - f64 * s64)).astype(f32)
    t = (v64 * (1.0 - s64 * (1.0 - f64))).astype(f32)
    red = np.choose(sector, (v, q, p, p, t, v))
    green = np.choose(sector, (t, v, v, q, p, p))
    blue = np.choose(sector, (p, p, t, v, v, q))
    rgb = np.stack((red, green, blue), axis=-1).astype(np.float64) * 255.0
    return np.clip(np.trunc(rgb), 0, 255).astype(np.uint8)


def test_heatmap_768_bajtja_es_a_position_kontrollok_nativak():
    red_ramp = _red_ramp()

    # A két pozíciókontroll a spec szerinti közvetlen 0–255 indexet őrzi.
    fractional = g.hsv_gradient_map(
        red_ramp,
        ((0.5, 0.0, 100.0, 100.0), (1.5, 120.0, 100.0, 100.0)),
    )[0]
    np.testing.assert_array_equal(
        fractional[:3],
        np.asarray(((255, 0, 0), (255, 255, 0), (0, 255, 0)), dtype=np.uint8),
    )
    outside = g.hsv_gradient_map(
        red_ramp,
        ((300.0, 0.0, 100.0, 100.0), (400.0, 120.0, 100.0, 100.0)),
    )[0]
    np.testing.assert_array_equal(outside, np.tile((255, 0, 0), (256, 1)))

    actual = g.hsv_gradient_map(red_ramp, _HEATMAP_STOPS)[0]
    expected = _spec_heatmap_reference()
    assert hashlib.sha256(expected.tobytes()).hexdigest() == _NATIVE_HEATMAP_SHA256_RGB
    for index, expected_rgb in _NATIVE_HEATMAP_ANCHORS.items():
        np.testing.assert_array_equal(expected[index], np.asarray(expected_rgb, dtype=np.uint8))
    np.testing.assert_array_equal(actual, expected)
