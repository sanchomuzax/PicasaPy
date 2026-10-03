"""A `GradientMap` LUT bitre követi a natív képletet (#4092).

Forrás: `docs/specs/filterdesc-registry.md`, „Az RGB-megállók
interpolációja — képlet, LUT és perem (#4090, 2026-10-03)”. A modell
szándékosan külön lépésekben használ float32 megállókat és súlyt, majd
double szorzást/összeadást és `+0,5` utáni csonkolást.
"""

from __future__ import annotations

import math

import numpy as np

from picasapy.render import glimmer_ops as g


def _spec_positions(n: int, *, float32: bool = True) -> tuple[float, ...]:
    """A spec stopképlete; a `float32=False` a linspace-mutáció kontrollja."""
    belso = [(k * 255.0) / (n - 1) for k in range(1, n - 1)]
    if float32:
        belso = [float(np.float32(p)) for p in belso]
    return (0.0, *belso, 255.0)


def _spec_lut(
    colors: tuple[tuple[int, int, int], ...],
    positions: tuple[float, ...] | None = None,
    *,
    float32_weight: bool = True,
    rounding: str = "native",
) -> np.ndarray:
    """A spec skalármodellje, a `< 8` LUT-on láthatatlan kapuja nélkül."""
    stops = positions if positions is not None else _spec_positions(len(colors))
    lut = np.empty((256, 3), dtype=np.uint8)
    for x in range(256):
        x_f32 = float(np.float32(x))
        lower_candidates = [j for j, p in enumerate(stops) if p <= x_f32]
        if not lower_candidates:
            lut[x] = colors[0]
            continue
        lo = lower_candidates[-1]
        if lo == len(stops) - 1:
            lut[x] = colors[-1]
            continue
        hi = next(j for j, p in enumerate(stops) if p > x_f32)
        weight = (stops[hi] - x_f32) / (stops[hi] - stops[lo])
        if float32_weight:
            weight = float(np.float32(weight))
        for channel in range(3):
            lower = int(colors[lo][channel])
            upper = int(colors[hi][channel])
            value = upper + weight * (lower - upper)
            if rounding == "native":
                value = math.trunc(value + 0.5)
            elif rounding == "truncate":
                value = math.trunc(value)
            elif rounding == "bankers":
                value = int(np.rint(value))
            else:
                raise AssertionError(f"Ismeretlen kerekítési kontroll: {rounding}")
            lut[x, channel] = max(0, min(255, int(value)))
    return lut


def _layouts() -> tuple[tuple[str, tuple[tuple[int, int, int], ...]], ...]:
    """27 determinisztikus n=2…10 paletta és a NightVision palettája."""
    layouts: list[tuple[str, tuple[tuple[int, int, int], ...]]] = []
    for n in range(2, 11):
        for variant in range(3):
            if variant == 0:
                colors = tuple(
                    ((i * 37 + 13) % 256, (i * 91 + 29) % 256, (255 - i * 17) % 256)
                    for i in range(n)
                )
            elif variant == 1:
                colors = tuple(
                    ((i * 73 + 251) % 256, (i * 19 + 1) % 256, (i * 61 + 88) % 256)
                    for i in range(n)
                )
            else:
                colors = tuple(
                    ((i * 127 + 3) % 256, (i * 53 + 127) % 256, (i * 101 + 202) % 256)
                    for i in range(n)
                )
            layouts.append((f"n={n}, palette={variant}", colors))
    layouts.append(("NightVision", ((0, 0, 0), (0x57, 0xCC, 0x29))))
    return tuple(layouts)


def test_gradient_map_lut_bitre_egyezik_a_nativ_modellel() -> None:
    # A spec külön, nem egyenletes példa rögzíti a súly irányát és a félértéket.
    pelda_szinek = ((0x0A, 0x14, 0x33), (0xC9, 0x65, 0x00))
    pelda = _spec_lut(pelda_szinek, (10.0, 200.0))
    assert tuple(int(v) for v in pelda[105]) == (0x6A, 0x3D, 0x1A)
    assert tuple(int(v) for v in pelda[0]) == pelda_szinek[0]
    assert tuple(int(v) for v in pelda[201]) == pelda_szinek[-1]

    layouts = _layouts()
    assert len(layouts) >= 20
    source = np.zeros((1, 256, 3), dtype=np.uint8)
    source[0, :, 0] = np.arange(256, dtype=np.uint8)

    # Rontás-kontrollok: a +0,5 nélkül modell/LUT-kimenet tér el; float64
    # linspace 12 megálló bitpontosságát veszíti el n=2…10 között, bár a
    # vizsgált egész LUT-indexeken 0 csatornabájtot változtat; a bankárkerekítés
    # a [10,200] példa 1 csatornáján tér el.
    fel_kimarad = 0
    f64_lut_eltetes = 0
    for _, colors in layouts:
        native = _spec_lut(colors)
        fel_kimarad += int(np.count_nonzero(native != _spec_lut(colors, rounding="truncate")))
        f64_lut_eltetes += int(
            np.count_nonzero(
                native
                != _spec_lut(
                    colors,
                    _spec_positions(len(colors), float32=False),
                )
            )
        )
    f64_pozicio_eltetes = 0
    for n in range(2, 11):
        native_positions = np.asarray(_spec_positions(n), dtype=np.float32)
        f64_positions = np.linspace(0.0, 255.0, n, dtype=np.float64)
        f64_pozicio_eltetes += int(
            np.count_nonzero(native_positions.astype(np.float64) != f64_positions)
        )
    fel_egesz_kerekites_eltetes = int(
        np.count_nonzero(pelda != _spec_lut(pelda_szinek, (10.0, 200.0), rounding="bankers"))
    )
    assert (
        fel_kimarad,
        f64_pozicio_eltetes,
        f64_lut_eltetes,
        fel_egesz_kerekites_eltetes,
    ) == (10534, 12, 0, 1)

    pelda_vegrehajto = getattr(g, "_gradient_map_interpolate_channel", None)
    pelda_eltetes = 0
    if not callable(pelda_vegrehajto):
        pelda_eltetes = 3
    else:
        pelda_kapott = tuple(
            pelda_vegrehajto(pelda_szinek[0][c], pelda_szinek[1][c], 10.0, 200.0, 105)
            for c in range(3)
        )
        pelda_eltetes = sum(a != b for a, b in zip(pelda_kapott, (0x6A, 0x3D, 0x1A), strict=True))

    lut_eltetes = 0
    peldak = []
    for name, colors in layouts:
        vart = _spec_lut(colors)
        kapott = g.gradient_map(source, colors)[0]
        eltetes = int(np.count_nonzero(kapott != vart))
        lut_eltetes += eltetes
        if eltetes:
            peldak.append(f"{name}: {eltetes}/768")
    stophely_seged = getattr(g, "_gradient_map_stop_positions", None)
    stophely_eltetes = 0
    if not callable(stophely_seged):
        stophely_eltetes = 9
    else:
        for n in range(2, 11):
            actual = stophely_seged(n)
            expected = np.asarray(_spec_positions(n), dtype=np.float32)
            if actual.dtype != np.float32:
                stophely_eltetes += len(expected)
            else:
                stophely_eltetes += int(
                    np.count_nonzero(actual.view(np.uint32) != expected.view(np.uint32))
                )

    suly_seged = getattr(g, "_gradient_map_weight", None)
    suly_eltetes = 0
    if not callable(suly_seged):
        suly_eltetes = 1
    else:
        for n in range(2, 11):
            stops = np.asarray(_spec_positions(n), dtype=np.float32)
            for x in range(256):
                lower_candidates = np.flatnonzero(stops <= np.float32(x))
                if not len(lower_candidates) or lower_candidates[-1] == n - 1:
                    continue
                lo = int(lower_candidates[-1])
                hi = lo + 1
                expected = np.float32(
                    (float(stops[hi]) - float(np.float32(x)))
                    / (float(stops[hi]) - float(stops[lo]))
                )
                actual = suly_seged(stops[lo], stops[hi], x)
                if np.asarray(actual).dtype != np.dtype(np.float32):
                    suly_eltetes += 1
                elif actual.view(np.uint32) != expected.view(np.uint32):
                    suly_eltetes += 1

    assert (
        lut_eltetes == 0
        and pelda_eltetes == 0
        and stophely_eltetes == 0
        and suly_eltetes == 0
    ), (
        f"A natív modell és a gradient_map LUT eltér: {lut_eltetes} csatornaérték; "
        f"első eltérések: {', '.join(peldak[:8])}. "
        f"A közös csatorna-interpolátor példája {pelda_eltetes}/3, "
        f"a float32 stophely-segéd {stophely_eltetes} helyen, a float32 súly {suly_eltetes} helyen tér el. "
        f"Rontás-kontroll: +0,5 elhagyása {fel_kimarad}, float64 megállóhely "
        f"{f64_pozicio_eltetes} megálló / {f64_lut_eltetes} LUT-bájt, bankárkerekítés "
        f"{fel_egesz_kerekites_eltetes} csatorna eltérés."
    )
