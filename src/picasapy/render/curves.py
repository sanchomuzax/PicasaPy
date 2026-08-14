"""Görbe- és LUT-segédek a render-műveletekhez.

A golden-elemzés (`docs/specs/filters-decoded.md`) mérési pontjaiból
töréspontos görbéket építünk: 256 elemű float LUT, lineáris interpolációval
a pontok között. A kerekítés egyetlen helyen, az alkalmazáskor történik.
"""

from __future__ import annotations

import numpy as np

#: Görbe-töréspontok típusa: ((bemenet, kimenet), ...) — bemenet 0..255.
CurvePoints = tuple[tuple[float, float], ...]


def validate_image(image: np.ndarray) -> None:
    """RGB uint8 (H, W, 3) alak-ellenőrzés — hibás bemenetnél ValueError."""
    if not isinstance(image, np.ndarray):
        raise ValueError(f"A kép numpy.ndarray kell legyen, nem {type(image)!r}")
    if image.dtype != np.uint8:
        raise ValueError(f"A kép dtype-ja uint8 kell legyen, nem {image.dtype}")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"A kép alakja (H, W, 3) kell legyen, nem {image.shape}")


def _natural_spline_second_derivatives(
    xs: np.ndarray, ys: np.ndarray
) -> np.ndarray:
    """A természetes köbös spline második deriváltjai (#629).

    A natív `0x008f33b0` a klasszikus tridiagonális megoldást futtatja
    (`2.0`-s főátló, `6.0`-s osztott differencia, Numerical Recipes
    `spline`); **természetes** spline, azaz a két végén a második derivált
    nulla — ezt a dekompilátum a `y2[0] = y2[n−1] = 0` beállítással mondja ki.
    """
    count = len(xs)
    second = np.zeros(count, dtype=np.float64)
    scratch = np.zeros(count, dtype=np.float64)
    for index in range(1, count - 1):
        sigma = (xs[index] - xs[index - 1]) / (xs[index + 1] - xs[index - 1])
        pivot = sigma * second[index - 1] + 2.0
        second[index] = (sigma - 1.0) / pivot
        slope_diff = (ys[index + 1] - ys[index]) / (xs[index + 1] - xs[index]) - (
            ys[index] - ys[index - 1]
        ) / (xs[index] - xs[index - 1])
        scratch[index] = (
            6.0 * slope_diff / (xs[index + 1] - xs[index - 1])
            - sigma * scratch[index - 1]
        ) / pivot
    for index in range(count - 2, 0, -1):
        second[index] = second[index] * second[index + 1] + scratch[index]
    second[0] = 0.0
    second[count - 1] = 0.0
    return second


def curve_lut(points: CurvePoints) -> np.ndarray:
    """Töréspontokból 256 elemű float64 LUT, TERMÉSZETES KÖBÖS SPLINE-nal.

    **#629: az eredeti nem lineárisan interpolál.** A `0x008f3290`
    munkafüggvény (a Numerical Recipes `splint` mintája) a szakaszon belül
    köbös tagot is számol:

        h = x[j+1] − x[j]
        A = (x[j+1] − x)/h          B = (x − x[j])/h
        y = A·y[j] + B·y[j+1] + ((A³−A)·y2[j] + (B³−B)·y2[j+1]) · h²/6

    A korábbi lineáris közelítés a valódi `filterdesc.xml` görbéken a
    **60-as évek** effektnél 21,6, a **Kinemaszkópnál** 17,5 szintet tévedett
    — hússzorosa a ditherelés ±1-es tűrésének, tehát szemmel látható.

    **Kétpontos görbénél a kettő azonos** (mindkét végén nulla a második
    derivált, így a köbös tag eltűnik) — a Színinvertálás, a Neon és a
    Ceruzarajz kimenete bájtra változatlan.

    A töréspontok tartományán KÍVÜL a szélső értéket tartjuk (nem
    extrapolálunk): a szűrők görbéi 0..255-ig érnek, a köbös extrapoláció
    viszont túllőne. A bemeneti pontok x-e szigorúan növekvő kell legyen.
    """
    if len(points) < 2:
        raise ValueError(f"Legalább két töréspont kell, kaptunk: {points!r}")
    xs = np.array([point[0] for point in points], dtype=np.float64)
    ys = np.array([point[1] for point in points], dtype=np.float64)
    if np.any(np.diff(xs) <= 0):
        raise ValueError(f"A töréspontok x-e szigorúan növekvő kell legyen: {points!r}")

    levels = np.arange(256, dtype=np.float64)
    second = _natural_spline_second_derivatives(xs, ys)
    # a szakasz megkeresése (a natív bináris keresésének megfelelője):
    # minden szinthez a befoglaló [x[j], x[j+1]] intervallum indexe
    upper = np.clip(np.searchsorted(xs, levels, side="right"), 1, len(xs) - 1)
    lower = upper - 1

    width = xs[upper] - xs[lower]
    left_weight = (xs[upper] - levels) / width
    right_weight = (levels - xs[lower]) / width
    values = (
        left_weight * ys[lower]
        + right_weight * ys[upper]
        + (
            (left_weight**3 - left_weight) * second[lower]
            + (right_weight**3 - right_weight) * second[upper]
        )
        * width
        * width
        / 6.0
    )
    # a tartományon kívül a szélső érték (ld. a docstringet)
    return np.where(
        levels < xs[0], ys[0], np.where(levels > xs[-1], ys[-1], values)
    )


def blend_luts(first: np.ndarray, second: np.ndarray, weight: float) -> np.ndarray:
    """Két LUT lineáris keveréke: `(1−weight)·first + weight·second`."""
    if first.shape != (256,) or second.shape != (256,):
        raise ValueError("A LUT-ok 256 eleműek kell legyenek")
    return (1.0 - weight) * first + weight * second


def apply_lut(image: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """A float LUT alkalmazása a kép mindhárom csatornájára, kerekítéssel."""
    validate_image(image)
    if lut.shape != (256,):
        raise ValueError(f"A LUT alakja (256,) kell legyen, nem {lut.shape}")
    table = np.clip(np.rint(lut), 0, 255).astype(np.uint8)
    return table[image]


def lut_ramp() -> np.ndarray:
    """Identitás-LUT (0..255 float64 rámpa) — csatornánkénti LUT-ok alapja."""
    return np.arange(256, dtype=np.float64)


def apply_channel_luts(
    image: np.ndarray, luts: tuple[np.ndarray, np.ndarray, np.ndarray]
) -> np.ndarray:
    """Csatornánként KÜLÖN float LUT alkalmazása (R, G, B sorrend, #140).

    Pontonkénti (csatornánként független) műveletek uint8-natív, képméret-
    független költségű futtatása: a LUT-ok 256 elemű float tömbök, a
    kerekítés/clippelés az `apply_lut`-tal azonos módon itt történik.
    """
    validate_image(image)
    if len(luts) != 3:
        raise ValueError(f"Pontosan három (R, G, B) LUT kell, kaptunk: {len(luts)}")
    channels = []
    for index, lut in enumerate(luts):
        if lut.shape != (256,):
            raise ValueError(f"A LUT alakja (256,) kell legyen, nem {lut.shape}")
        table = np.clip(np.rint(lut), 0, 255).astype(np.uint8)
        channels.append(table[image[..., index]])
    return np.stack(channels, axis=-1)
