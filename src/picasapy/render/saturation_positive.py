"""A `sat` szűrő POZITÍV ága — a natív mag (`0x0090b930`) hű mása (#693).

## Miért külön modul

A `sat` callback (`0x008f8ff0`) **két külön magra** ágazik:

```c
if (amount < 0.0)  FUN_0090e200(dst, amount + 1.0f);   // negatív: luma-keverés
else               FUN_0090b930(dst, src, amount);     // pozitív: EZ a modul
```

A negatív ág egyszerű luma-keverés `1 + amount` erősítéssel — az a
`color.apply_saturation`-ben maradt. A pozitív ág viszont **nem erősítés**,
hanem a `csatorna / luma` aránynak adott, **csatornánként MÁS kitevőjű**
gamma:

```
C' ≈ Y · pow(C / Y, 1 + e·s)      s = amount·3,  e = 0,3 (R) / 0,7 (G) / 0,9 (B)
```

Ez **önmagában korlátozó**: ahol a csatorna a lumához közeli (`C/Y ≈ 1`),
ott `pow(1, bármi) = 1`, tehát a csúszka akármekkora is, nem mozdít. Csak a
lumától távoli csatornák mozdulnak, és azok is egyre kisebb hozadékkal.
**Ezért telítődik** a mért erősítés (1,15 → 1,95 a 0,10 → 0,87 sávban),
ahelyett hogy lineárisan 3,6-ig futna — ez volt a #693 kulcskérdése.

## Két csapda, amit NEM szabad „egyszerűsíteni"

1. **A három kitevő különbözik** (0,3 / 0,7 / 0,9), tehát a hatás
   **színárnyalat-függő**. Egyetlen közös kitevő más képet ad.
2. **Az itteni luma-képlet MÁS**, mint a `sepia`/`radsat`/`tint` közös
   `(77·R + 151·G + 28·B) >> 8` súlyozása: itt `(2·R + 5·G + 1·B) >> 3`.
   **Közös segédfüggvényt kivonni tilos** — a két képlet szándékosan
   különbözik, és az összevonás némán elrontaná mindkettőt.

A fixpontos lépések (`>> 8`, a 2047-es indexvágás, a záró `65280/m`
maxnormálás) a natív kódot követik. A `DAT_00d3a148 = 256` állandó a
binárisból van kiolvasva; a `.text`-ben egyetlen hivatkozás mutat rá.

Forrás: `docs/specs/filters-decoded.md`, „`sat` pozitív ág" szakasz.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from picasapy.lazy_cv2 import cv2

#: Csatornánkénti kitevő-szorzó (R, G, B) — a natív kód három külön táblája.
CHANNEL_EXPONENTS: tuple[float, float, float] = (0.3, 0.7, 0.9)

#: A keresőtáblák hossza és a leképezett bemeneti tartomány (`0 .. 8`).
_LUT_SIZE = 2048
_LUT_RANGE = 8.0

#: `DAT_00d3a148` = 256 → `k = (256·256 − 1) / Y`.
_K_NUMERATOR = 256 * 256 - 1

#: A záró maxnormálás számlálója (`65280 = 255 << 8`).
_MAXNORM_NUMERATOR = 65280


def channel_lut(exponent_scale: float, strength: float) -> np.ndarray:
    """Egy csatorna 2048 elemű táblája, a natív `powf`-ciklus szerint."""
    index = np.arange(_LUT_SIZE, dtype=np.float64)
    x = index * _LUT_RANGE / _LUT_SIZE
    return np.rint(
        np.power(x, 1.0 + exponent_scale * strength) * 256.0
    ).astype(np.int64)


@lru_cache(maxsize=16)
def _luma_channel_tables(amount: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Az eredeti két lépéses LUT egyesítése `luma × csatorna` táblákba."""
    strength = amount * 3.0
    y = np.arange(256, dtype=np.uint32)[:, None]
    channel = np.arange(256, dtype=np.uint32)[None, :]
    k = np.uint32(_K_NUMERATOR) // np.maximum(y, np.uint32(1))
    index = np.minimum((k * channel) >> 8, _LUT_SIZE - 1).astype(np.intp)

    tables = []
    for exponent in CHANNEL_EXPONENTS:
        lut = channel_lut(exponent, strength).astype(np.uint32)
        values = (lut[index] * y) >> 8
        # A remap támogatja a uint16 forrást is, ami a szokásos sliderértékek
        # táblájának felére csökkenti a memóriaforgalmát. A maximális állás
        # kimenete meghaladhatja a uint16 tartományát, de float32-ben pontos
        # egészek maradnak.
        if int(values.max()) <= np.iinfo(np.uint16).max:
            tables.append(values.astype(np.uint16))
        else:
            tables.append(values.astype(np.float32))
    return tuple(tables)


def apply_positive_saturation(image: np.ndarray, amount: float) -> np.ndarray:
    """A `sat` pozitív ága, a natív fixpontos lépésekkel.

    `amount` a csúszka `[0, 1]` tartományban; `0`-nál azonosság.
    """
    if amount <= 0.0:
        return image.copy()
    tables = _luma_channel_tables(float(amount))
    output = np.empty_like(image)

    # Egyetlen képtömbös körben csak három remap indul. A táblázat uint16
    # eredményét uint16-ben tartjuk a közös maximumkeresésig.
    red = image[..., 0].astype(np.uint16)
    green = image[..., 1].astype(np.uint16)
    blue = image[..., 2].astype(np.uint16)
    luma = ((2 * red + 5 * green + blue) >> 3).astype(np.uint8)
    non_black = luma > 0
    maps = np.empty((*luma.shape, 2), dtype=np.int16)
    maps[..., 1] = luma
    adjusted: list[np.ndarray] = []
    for channel, table in enumerate(tables):
        maps[..., 0] = image[..., channel]
        values = cv2.remap(
            table,
            maps,
            None,
            interpolation=cv2.INTER_NEAREST,
            borderMode=cv2.BORDER_REPLICATE,
        )
        adjusted.append(values.astype(np.uint32) if values.dtype == np.float32 else values)
    maximum = np.maximum(np.maximum(adjusted[0], adjusted[1]), adjusted[2])
    scale = np.where(
        maximum > 255,
        _MAXNORM_NUMERATOR // np.maximum(maximum, 1),
        256,
    ).astype(np.uint32)

    for channel, values in enumerate(adjusted):
        normalized = ((scale * values) >> 8).astype(np.uint8)
        output[..., channel] = np.where(non_black, normalized, image[..., channel])
    return output
