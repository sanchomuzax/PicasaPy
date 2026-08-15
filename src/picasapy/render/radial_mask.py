"""A Picasa sugaras keverőmaszkja — `0x0090b050` + `0x0090aeb0` (#668).

A `radblur` („Lágy fókusz") és a `radsat` („Fókuszos FF") közös maszkja.
A natív mag **nem** von gyököt a képpont-ciklusban: egy 1024 elemű, bájtos
súlytáblát a **négyzetes** távolsággal indexel, és a táblát egy előre
kiszámolt eltolás (`shift`) hozza a tábla tartományába.

```
r  = min(szélesség, magasság) / 2 · (Size + 1,0)
r2 = r²;  shift = 0
while (r2 > 1024) { r2 ·= 0,5;  shift++ }

tábla[i] = round( (3 − 2u)·u²·255 ),  ahol
    d = sqrt( (i/1024) · (1024/r2) )        ← normált sugár, d = táv / r
    v = clamp( 0,5 + (d − 0,5) / (1 − Sharpness·0,99), 0, 1 )
    u = 1 − v

képpontonként:
    idx = (dx² + dy²) >> shift
    ki  = perem + (közép − perem) · tábla[idx] / 256      (ha idx < 1024)
    ki  = perem                                           (különben)
```

Az átmenet **smoothstep** (`3u² − 2u³`), nem lineáris — ez adja a lágy
peremet. A `Sharpness` a meredekséget állítja: 0-nál a normált sugár
maga, 1 felé `1/(1−0,99) = 100`-szoros meredekség, azaz éles körvonal.

Forrás: `docs/specs/picasa-native-filter-workers.md` 4.2.4. A geometria a
`radblur` négy golden-párján (három kép, két Amount-érték) ellenőrizve —
ld. a `#668` mérését a `docs/specs/filters-decoded.md`-ben.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image

#: A natív súlytábla mérete (`0x400`).
RADIAL_TABLE_SIZE = 1024

#: A natív keverés osztója (a tábla maximuma 255, ezért a közép súlya
#: 255/256 — a natív csomagolt aritmetika sajátja, nem kerekítési hiba).
_BLEND_DIVISOR = 256

#: A `Sharpness` meredekség-szorzója a natív képletben.
_SHARPNESS_SCALE = 0.99


def radial_weight_table(
    width: int, height: int, size: float, sharpness: float
) -> tuple[np.ndarray, int]:
    """A `0x0090aeb0` súlytáblája és a négyzetes távolság eltolása.

    A visszaadott tábla `int64`, 0…255 értékekkel; az `index = (dx²+dy²)
    >> shift` képlettel indexelendő.
    """
    radius = min(width, height) / 2.0 * (float(size) + 1.0)
    squared = radius * radius
    shift = 0
    while squared > RADIAL_TABLE_SIZE:
        squared *= 0.5
        shift += 1
    steps = np.arange(RADIAL_TABLE_SIZE, dtype=np.float64)
    normalized = np.sqrt(
        (steps / RADIAL_TABLE_SIZE) * (RADIAL_TABLE_SIZE / max(squared, 1e-9))
    )
    span = 1.0 - float(sharpness) * _SHARPNESS_SCALE
    edge = np.clip(0.5 + (normalized - 0.5) / max(span, 1e-9), 0.0, 1.0)
    inner = 1.0 - edge
    table = np.rint((3.0 - 2.0 * inner) * inner * inner * 255.0)
    return table.astype(np.int64), shift


def _squared_distance(
    width: int, height: int, x: float, y: float, shift: int
) -> np.ndarray:
    """A natív `idx = (dx² + dy²) >> shift` rács (egész aritmetikával)."""
    center_x = round(width * float(x))
    center_y = round(height * float(y))
    columns = (np.arange(width, dtype=np.int64) - center_x) ** 2
    rows = (np.arange(height, dtype=np.int64) - center_y) ** 2
    return (rows[:, np.newaxis] + columns[np.newaxis, :]) >> shift


def apply_radial_mask(
    center: np.ndarray,
    edge: np.ndarray,
    x: float,
    y: float,
    size: float,
    sharpness: float,
) -> np.ndarray:
    """A `0x0090b050` keverése: `center` a korong közepén, `edge` kívül.

    A két képnek azonos alakúnak kell lennie. A táblán túli (`idx >= 1024`)
    képpontokat a natív mag érintetlenül hagyja — vagyis ott tisztán az
    `edge` látszik.
    """
    validate_image(center)
    validate_image(edge)
    if center.shape != edge.shape:
        raise ValueError(
            f"A két kép alakja eltér: {center.shape} vs {edge.shape}"
        )
    height, width = center.shape[:2]
    table, shift = radial_weight_table(width, height, size, sharpness)
    index = _squared_distance(width, height, x, y, shift)
    weight = table[np.clip(index, 0, RADIAL_TABLE_SIZE - 1)][..., np.newaxis]
    base = edge.astype(np.int64)
    blended = base + (center.astype(np.int64) - base) * weight // _BLEND_DIVISOR
    inside = (index < RADIAL_TABLE_SIZE)[..., np.newaxis]
    return np.clip(np.where(inside, blended, base), 0, 255).astype(np.uint8)


__all__ = ["RADIAL_TABLE_SIZE", "apply_radial_mask", "radial_weight_table"]
