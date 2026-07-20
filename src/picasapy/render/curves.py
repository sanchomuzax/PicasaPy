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


def curve_lut(points: CurvePoints) -> np.ndarray:
    """Töréspontokból 256 elemű float64 LUT (lineáris interpolációval).

    A bemeneti pontok x-e szigorúan növekvő kell legyen.
    """
    if len(points) < 2:
        raise ValueError(f"Legalább két töréspont kell, kaptunk: {points!r}")
    xs = np.array([point[0] for point in points], dtype=np.float64)
    ys = np.array([point[1] for point in points], dtype=np.float64)
    if np.any(np.diff(xs) <= 0):
        raise ValueError(f"A töréspontok x-e szigorúan növekvő kell legyen: {points!r}")
    return np.interp(np.arange(256, dtype=np.float64), xs, ys)


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
