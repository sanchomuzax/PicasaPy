"""`linblur` — „Lineáris homályosítás" (a natív `0x0090de10` mag, #623).

**Nem mozgáshomály**, hanem ÁTMENETES (graduált) életlenítés — tilt-shift
jellegű hatás. A burkoló (`0x008f99c0`) két pontot ad a magnak:

| pont | mi | a mag szerinti hatás |
|---|---|---|
| `p1` | a felületi korong (puck) helye | `t = +65536` → `alpha = 250` → **éles** |
| `p0` | a kép közepe (`W>>1`, `H>>1`) | `t = −65536` → `alpha = 5` → **homályos** |

A `t` a két ponton átmenő egyenes menti, 16.16 fixpontos vetület:

```c
kx = (d.x << 16)/|d|²;   ky = (d.y << 16)/|d|²;        d = p1 − p0
t  = 2·kx·x + 2·ky·y − ((p0.x+p1.x)·kx + (p0.y+p1.y)·ky)
idx   = t >> 8;                       // a végpontokban ±256
alpha = (súly[idx] + 255) / 2;        // súly[−i] = −súly[i]
out   = homályos + ((éles − homályos) · alpha >> 8);
```

`idx <= −384` esetén a mag **nem ír semmit** (marad a végig elmosott
puffer), `idx >= +384` esetén a **nyers éles forrást** írja.

## Amit ez a modul KÖZELÍT — és min múlik

1. **A „Mennyiség" csúszka → elmosási sugár leképezése.** A burkoló ezt az
   x87-veremen adja át, a dekompilátor elvesztette. A testvér `radblur`
   burkolójában viszont olvasható a minta (`szélesség/100 · (Amount+1)`),
   ezért itt is ezt használjuk — **feltevés, nem mérés**; a kalibráció a
   #317-es jegyben fut. A hatás JELLEGE (hol éles, hol homályos, milyen az
   átmenet) ettől független és egzakt.
2. **A súlytábla utolsó rekeszei.** A natív kód a `round((1−2f)·255,9999)`
   értéket **bájtba** írja, így `f → 0` közelében (`i >= 338`) 256-ot
   tárolna, ami 0-ra fordul körbe — vagyis a teljesen ÉLES tartomány egy
   sávjában 50%-os homályt adna. Ez a natív oldalon túlcsordulás; a
   255,9999-es szorzó a **csonkolás** klasszikus idiómája, ezért itt 255-re
   vágunk. Egy referencia-export ezt eldöntheti (#317).
3. **A korong pozíciója.** A `filters=` láncban a korong normált `x, y`
   koordinátaként áll elöl, a puck-os szűrők általános sorrendje szerint
   (`docs/specs/filterdesc-registry.md` 3. pont) — valódi `linblur=`
   ini-mintánk nincs.

Ld. `docs/specs/picasa-native-filter-workers.md` 3.3 és 4.2.1.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.iir_blur import apply_picasa_blur

#: A natív súlytábla mérete (`0x180`): a `t` 0-tól 1,5-ig, 1/256-os lépésben.
LINBLUR_TABLE_SIZE = 0x180

#: A tábla lépésköze (`local_1bc += 0.00390625`).
_TABLE_STEP = 1.0 / 256.0

#: A natív skálázó szorzó a súlytábla építésénél.
_TABLE_SCALE = 255.9999

#: A `radblur` burkolójából átvett sugár-képlet együtthatói (KÖZELÍTÉS).
_RADIUS_WIDTH_FRACTION = 0.01
_RADIUS_EPSILON = 0.001


def _spline_tail(t: float) -> float:
    """A köbös B-spline átmenet-függvénye a `t >= 0` félegyenesen.

    A natív ág-szerkezet (`0x0090de10`) szerint:
    `t <= 0,5` → `f = 1/2 − (3t/4 − t³/3)`, felette pedig
    `f = 9/16 − (9t/8 + (t³/6 − 3t²/4))`, ami `t >= 1,5`-nél már 0.
    """
    if t > 1.5:
        return 0.0
    square = t * t
    cube = square * t
    if t <= 0.5:
        return 0.5 - (t * 0.75 - cube * (1.0 / 3.0))
    return 0.5625 - (t * 1.125 + (cube * (1.0 / 6.0) - square * 0.75))


def linblur_weight_table() -> np.ndarray:
    """A 384 elemű, `int32` súlytábla — a natív `local_188` tömb.

    A `[0, 255]`-re vágásról ld. a modul docstringjének 2. pontját.
    """
    values = [
        int(round((1.0 - 2.0 * _spline_tail(index * _TABLE_STEP)) * _TABLE_SCALE))
        for index in range(LINBLUR_TABLE_SIZE)
    ]
    return np.clip(np.array(values, dtype=np.int32), 0, 255)


#: Egyszer épített, csak olvasásra használt tábla.
_WEIGHT_TABLE = linblur_weight_table()
_WEIGHT_TABLE.setflags(write=False)


def linblur_blur_radius(width: int, amount: float) -> float:
    """A „Mennyiség" csúszka elmosási sugara — KÖZELÍTÉS (ld. modul-doc 1.).

    A testvér `radblur` burkolójának mért alakja:
    `sugár = szélesség · 0,01 · Mennyiség + 0,001 + szélesség · 0,01`.
    """
    return width * _RADIUS_WIDTH_FRACTION * (max(amount, 0.0) + 1.0) + _RADIUS_EPSILON


def _c_int_div(numerator: int, denominator: int) -> int:
    """Egész osztás NULLA FELÉ csonkolva — a C `/` szemantikája.

    A numpy/Python `//` a padló felé kerekít, ami negatív `d.x`-nél más
    `kx`-et adna, mint a natív kód.
    """
    quotient = abs(numerator) // abs(denominator)
    return -quotient if (numerator < 0) != (denominator < 0) else quotient


def _projection(
    height: int, width: int, near: tuple[int, int], far: tuple[int, int]
) -> np.ndarray:
    """A képpontonkénti `t` vetület, `(H, W)` alakú `int64` tömbként."""
    delta_x = near[0] - far[0]
    delta_y = near[1] - far[1]
    squared = delta_x * delta_x + delta_y * delta_y
    slope_x = _c_int_div(delta_x << 16, squared)
    slope_y = _c_int_div(delta_y << 16, squared)
    offset = -((far[1] + near[1]) * slope_y + (far[0] + near[0]) * slope_x)
    columns = np.arange(width, dtype=np.int64) * (2 * slope_x)
    rows = np.arange(height, dtype=np.int64) * (2 * slope_y)
    return columns[np.newaxis, :] + rows[:, np.newaxis] + offset


def apply_linblur(
    image: np.ndarray, x: float, y: float, amount: float
) -> np.ndarray:
    """Átmenetes életlenítés: a korong felőli oldal éles, a közép felőli nem.

    Az `x`, `y` a korong NORMÁLT helye (`0…1`), az `amount` a „Mennyiség"
    csúszka. Ha a korong a kép közepére esik, a natív mag ki sem lép a
    belépő feltételéből — a kép változatlan.
    """
    validate_image(image)
    height, width = image.shape[:2]
    puck = (int(round(width * float(x))), int(round(height * float(y))))
    center = (width >> 1, height >> 1)
    if puck == center:
        return image.copy()

    radius = linblur_blur_radius(width, amount)
    # a natív burkoló KÉTSZER futtatja végig a közös elmosó magot
    blurred = apply_picasa_blur(
        apply_picasa_blur(image, radius, radius), radius, radius
    ).astype(np.int64)

    index = _projection(height, width, puck, center) >> 8
    clamped = np.clip(index, -(LINBLUR_TABLE_SIZE - 1), LINBLUR_TABLE_SIZE - 1)
    # a súlytábla PÁRATLAN kiterjesztéssel él: `súly[−i] = −súly[i]`
    magnitude = _WEIGHT_TABLE[np.abs(clamped)]
    weight = np.where(clamped < 0, -magnitude, magnitude)
    alpha = ((weight + 255) // 2)[..., np.newaxis]

    sharp = image.astype(np.int64)
    blended = blurred + ((sharp - blurred) * alpha >> 8)
    result = np.where(index[..., np.newaxis] >= LINBLUR_TABLE_SIZE, sharp, blended)
    result = np.where(
        index[..., np.newaxis] <= -LINBLUR_TABLE_SIZE, blurred, result
    )
    return np.clip(result, 0, 255).astype(np.uint8)


__all__ = [
    "LINBLUR_TABLE_SIZE",
    "apply_linblur",
    "linblur_blur_radius",
    "linblur_weight_table",
]
