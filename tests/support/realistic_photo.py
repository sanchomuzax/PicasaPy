"""Élethű, folytonos hisztogramú szintetikus fénykép a render-tesztekhez.

**Miért kell ez, és miért NEM elég az egyenletes véletlen zaj (#504):**
egy sík, egyenletes eloszlású (`rng.integers(lo, hi, ...)`) "zajlap" bár
folytonos hisztogramú, nincs benne térbeli szerkezet (gradiens, folt) — az
`AutoFix` (hisztogram-nyújtás) és a maszkolt elmosás ilyen bemeneten
másképp viselkedik, mint egy valódi fotón. A #504 vizsgálat során ez
egyszer már félrevezette a mérést. Ez a generátor egy egyszerű, de
térben strukturált "fotó"-t ad: felül sötétebb, alul enyhén melegebb
"égbolt"-gradiens + néhány elmosott fényesség-folt ("tereptárgy") +
finom Gauss-zaj — a hisztogramja egycsúcsú és folytonos, NEM a
kétértékű/lapos típus, ami az `AutoFix`-et és ezzel a Holgát/Lomót
önmagában feketévé teheti.

A visszaadott tömb `uint8`, **OpenCV BGR** csatornasorrendű (mint egy
`cv2.imread`/`cv2.imdecode` eredménye) — a hívónak kell RGB-re
konvertálnia, ha a `render/chain.py`/`glimmer_*` RGB-terű csővezetéket
hívja közvetlenül (ld. `render/chain.py::_apply_filter_chain` mintáját).
"""

from __future__ import annotations

import cv2
import numpy as np


def make_realistic_photo(height: int = 800, width: int = 600, seed: int = 7) -> np.ndarray:
    """`(height, width, 3)` `uint8` BGR kép, egycsúcsú/folytonos hisztogrammal."""
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    sky = 90.0 + 90.0 * (ys / height)
    base = np.stack([sky * 0.9, sky * 0.95, sky * 1.05], axis=-1)
    for _ in range(12):
        cx = rng.uniform(0, width)
        cy = rng.uniform(0, height)
        radius = rng.uniform(30, 140)
        amplitude = rng.uniform(-60, 60)
        dist2 = (xs - cx) ** 2 + (ys - cy) ** 2
        blob = amplitude * np.exp(-dist2 / (2 * radius * radius))
        for channel in range(3):
            base[..., channel] += blob * rng.uniform(0.7, 1.3)
    noise = rng.normal(0.0, 6.0, size=base.shape).astype(np.float32)
    image = np.clip(base + noise, 0, 255).astype(np.uint8)
    return cv2.GaussianBlur(image, (5, 5), 1.2)


__all__ = ["make_realistic_photo"]
