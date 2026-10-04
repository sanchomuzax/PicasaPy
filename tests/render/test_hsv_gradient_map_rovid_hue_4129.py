"""A HSVGradientMap a hue-ot a natív rövidebb köríven interpolálja (#4129)."""

from __future__ import annotations

import hashlib

import numpy as np

from picasapy.render import glimmer_ops as g


_QEMU_350_10_SHA256_RGB = "ed1c417ba58ca0d06da0b855df9342613c0dd2ecc89f70045b4498f9b096ce55"


def _reference_lut(stops, hue_offset: float = 0.0) -> np.ndarray:
    """Egyszerű, skalár referencia a specifikáció képletéhez.

    A stoppozíciók előbb float32-vé alakulnak; `t` az alsó stop súlya.
    Csak a hue tér el: 180 foknál nagyobb különbségnél a kisebbik végpontot
    360 fokkal eltoljuk. Az RGB-konverzió a már külön specifikált kernel.
    """
    positions = np.asarray([stop[0] for stop in stops], dtype=np.float32)
    hues = np.asarray([stop[1] for stop in stops], dtype=np.float32)
    sats = np.asarray([stop[2] for stop in stops], dtype=np.float32)
    vals = np.asarray([stop[3] for stop in stops], dtype=np.float32)
    out_hue: list[np.float32] = []
    out_sat: list[np.float32] = []
    out_val: list[np.float32] = []
    offset = np.float32(hue_offset)

    for index in range(256):
        x = np.float32(index)
        upper = int(np.searchsorted(positions, x, side="left"))
        if upper == 0:
            hue, sat, val = hues[0], sats[0], vals[0]
        elif upper == len(positions):
            hue, sat, val = hues[-1], sats[-1], vals[-1]
        elif positions[upper] == x:
            hue, sat, val = hues[upper], sats[upper], vals[upper]
        else:
            lower = upper - 1
            p_lower = positions[lower]
            p_upper = positions[upper]
            weight = np.float32((float(p_upper) - float(x)) / (float(p_upper) - float(p_lower)))
            h_lower = float(hues[lower])
            h_upper = float(hues[upper])
            if abs(h_lower - h_upper) > 180.0:
                if h_lower < h_upper:
                    h_lower += 360.0
                elif h_upper < h_lower:
                    h_upper += 360.0
            hue = np.float32(h_upper + float(weight) * (h_lower - h_upper))
            sat = np.float32(float(sats[upper]) + float(weight) * (float(sats[lower]) - float(sats[upper])))
            val = np.float32(float(vals[upper]) + float(weight) * (float(vals[lower]) - float(vals[upper])))
        out_hue.append(np.float32(hue + offset))
        out_sat.append(sat)
        out_val.append(val)

    return g._hsv_rgb_lut_f32(np.asarray(out_hue), np.asarray(out_sat), np.asarray(out_val))


def _red_ramp() -> np.ndarray:
    image = np.zeros((1, 256, 3), dtype=np.uint8)
    image[0, :, 0] = np.arange(256, dtype=np.uint8)
    return image


def test_350_rol_10_fokos_qemu_lut_sha_es_minden_elem() -> None:
    stops = ((0.0, 350.0, 100.0, 100.0), (255.0, 10.0, 100.0, 100.0))
    actual = g.hsv_gradient_map(_red_ramp(), stops)[0]
    expected = _reference_lut(stops)

    np.testing.assert_array_equal(actual, expected)
    assert hashlib.sha256(actual.tobytes()).hexdigest() == _QEMU_350_10_SHA256_RGB
    assert [actual[index].tobytes().hex() for index in (0, 127, 128, 255)] == [
        "ff002a",
        "ff0000",
        "ff0000",
        "ff2a00",
    ]


def test_180_foknal_nincs_eltolas_es_felett_mar_rovid_iven_fut() -> None:
    boundary = ((0.0, 0.0, 100.0, 100.0), (255.0, 180.0, 100.0, 100.0))
    beyond = ((0.0, 0.0, 100.0, 100.0), (255.0, 180.5, 100.0, 100.0))
    boundary_pixel = np.array([[[128, 0, 0]]], dtype=np.uint8)
    beyond_pixel = boundary_pixel.copy()

    boundary_rgb = g.hsv_gradient_map(boundary_pixel, boundary)[0, 0]
    beyond_rgb = g.hsv_gradient_map(beyond_pixel, beyond)[0, 0]

    # 90,35 foknál az R = csonk(125,999...) = 125; ez a határeset
    # eltolás nélkül interpolál, de a HSV → RGB lépés továbbra is csonkol.
    np.testing.assert_array_equal(boundary_rgb, np.array([125, 255, 0], dtype=np.uint8))
    np.testing.assert_array_equal(beyond_rgb, _reference_lut(beyond)[128])


def test_heatmap_tort_stopokkal_is_rovid_hue_iven_interpolal() -> None:
    # A HeatMap leírójának float32 LUT-tengelyű stophelyei; az első szakasz
    # körbejár, így a próba a pozíciókezelést és a rövid hue-ívet is elüti.
    stops = (
        (0.0, 350.0, 70.0, 70.0),
        (31.875, 10.0, 35.0, 100.0),
        (127.5, 120.0, 100.0, 90.0),
        (223.125, 120.0, 10.0, 60.0),
        (255.0, 120.0, 100.0, 50.0),
    )
    actual = g.hsv_gradient_map(_red_ramp(), stops)[0]

    np.testing.assert_array_equal(actual, _reference_lut(stops))
