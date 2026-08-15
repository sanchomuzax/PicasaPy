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

import numpy as np

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


def apply_positive_saturation(image: np.ndarray, amount: float) -> np.ndarray:
    """A `sat` pozitív ága, a natív fixpontos lépésekkel.

    `amount` a csúszka `[0, 1]` tartományban; `0`-nál azonosság.
    """
    if amount <= 0.0:
        return image.copy()
    strength = amount * 3.0
    luts = [channel_lut(e, strength) for e in CHANNEL_EXPONENTS]

    channels = [image[..., i].astype(np.int64) for i in range(3)]
    red, green, blue = channels
    luma = (2 * red + 5 * green + 1 * blue) >> 3

    # Y == 0 (tiszta fekete): a natív kód ilyenkor NEM nyúl a képponthoz.
    nem_fekete = luma > 0
    biztos_luma = np.where(nem_fekete, luma, 1)
    k = _K_NUMERATOR // biztos_luma

    eredmeny = []
    for csatorna, lut in zip(channels, luts, strict=True):
        index = np.minimum((k * csatorna) >> 8, _LUT_SIZE - 1)
        eredmeny.append((lut[index] * luma) >> 8)

    maximum = np.maximum(np.maximum(eredmeny[0], eredmeny[1]), eredmeny[2])
    tulcsordul = maximum > 255
    szorzo = np.where(tulcsordul, _MAXNORM_NUMERATOR // np.maximum(maximum, 1), 256)
    eredmeny = [(szorzo * ertek) >> 8 for ertek in eredmeny]

    kimenet = np.stack(
        [np.where(nem_fekete, ertek, csatorna) for ertek, csatorna in zip(eredmeny, channels, strict=True)],
        axis=-1,
    )
    return np.clip(kimenet, 0, 255).astype(np.uint8)
