"""A Picasa natív tónus-magjai: szinthúzás, kontraszt, gamma (#687).

A képletek a `docs/specs/picasa-native-filter-workers.md` 2.2–2.4 pontjában
rögzített, **dekompilált** munkafüggvényekből valók — nem illesztett
közelítések:

| cím | mi ez | ki hívja |
|---|---|---|
| `0x0090c1e0` | a szinthúzó LUT-építő (fekete-/fehérpont + gamma) | `triple2`, `triple3`, `autolight`, `finetune*` |
| `0x0090c100` | a kontraszt LUT-építő (exp(2·c) a középpont körül) | `contrast`, `triple` |
| `0x0090bc60` | a közös, 16 bites LUT-alkalmazó | mindkettő |

**Egy dokumentált eltérés a natívtól: a ditherelés.** A natív alkalmazó
(`0x0090bc60`) képpontonként egy MT19937-mintát húz, és a LUT helyi
meredekségével arányos, ±delta/2 amplitúdójú zajt kever a kimenetbe — ettől
nem sávosodik a széthúzott hisztogram. Ez a zaj nulla várható értékű, viszont
**nem determinisztikus**, ezért az élő előnézetben villogna, a pixelpontos
összevetést pedig ±1 szintre rontaná. A megvalósítás ezért a dither NÉLKÜLI
alakot futtatja (a natív `v >> 8` csonkolással). A #685 mérőszettjén ez
képenként 0,18–0,37 átlagos ΔE-t ad a valódi Picasa-kimenethez képest — a
JPEG-újratömörítés saját zaja alatt, tehát a különbség nem látható.
"""

from __future__ import annotations

import math

import numpy as np

from picasapy.render.curves import validate_image

#: A natív LUT teljes kitérése: `255 · 256` (8.8 fixpont).
NATIVE_LUT_FULL = 0xFF00

#: A fényerő-paraméter szorzója a kontraszt-LUT-ban (`0x0090c100`):
#: ±1 nagyjából ±100 nyolcbites szintnek felel meg.
_BRIGHTNESS_SCALE = 25600.0

#: A kontraszt-feszítés középpontja (50 %) a 16 bites skálán.
_CONTRAST_PIVOT = 32768.0

_LEVELS = np.arange(256, dtype=np.float64)


def native_level_lut(
    black: float, white: float, gamma: float = 1.0
) -> np.ndarray:
    """A szinthúzó LUT (`0x0090c1e0`) — 256 elem, 16 bites értékekkel.

    ```c
    invG  = 1.0 / gamma;
    scale = (white != black) ? 1.0 / (white - black) : 1.0;
    LUT[i] = clamp(round((pow(i/255, invG) * 65280 - black * 65280) * scale),
                   0, 0xFF00);
    ```

    A sorrend **gamma → feketepont-eltolás → fehérpont-skálázás**. A
    degenerált (`white == black`) párnál a natív kód 1,0-s skálával megy
    tovább — ezt szándékosan átvesszük, mert a `triple2` felső
    csúszkaállásában (fekete = fehér = 1,0) éppen ez adja a mérésben látott
    fekete képet.
    """
    if gamma <= 0.0:
        raise ValueError(f"A gamma pozitív kell legyen, nem {gamma}")
    scale = 1.0 / (white - black) if white != black else 1.0
    curve = np.power(_LEVELS / 255.0, 1.0 / gamma)
    values = (curve * NATIVE_LUT_FULL - black * NATIVE_LUT_FULL) * scale
    return np.clip(np.rint(values), 0, NATIVE_LUT_FULL).astype(np.int64)


def native_contrast_lut(
    contrast: float, brightness: float = 0.0, gamma: float = 1.0
) -> np.ndarray:
    """A kontraszt-LUT (`0x0090c100`) — 256 elem, 16 bites értékekkel.

    ```c
    k = exp(2.0 * contrast);
    LUT[i] = clamp(round(k * ((pow(i/255, 1/gamma) * 65280
                               + brightness * 25600) - 32768) + 32768),
                   0, 0xFF00);
    ```

    A kontraszt a **középpont (50 %) körül** feszít, a fényerő **additív**, a
    gamma pedig a kontraszt ELŐTT hat.
    """
    if gamma <= 0.0:
        raise ValueError(f"A gamma pozitív kell legyen, nem {gamma}")
    factor = math.exp(2.0 * contrast)
    curve = np.power(_LEVELS / 255.0, 1.0 / gamma)
    shifted = curve * NATIVE_LUT_FULL + brightness * _BRIGHTNESS_SCALE
    values = factor * (shifted - _CONTRAST_PIVOT) + _CONTRAST_PIVOT
    return np.clip(np.rint(values), 0, NATIVE_LUT_FULL).astype(np.int64)


def apply_native_lut16(image: np.ndarray, lut16: np.ndarray) -> np.ndarray:
    """A közös 16 bites LUT-alkalmazó (`0x0090bc60`) — ditherelés nélkül.

    A natív kód `v >> 8`-cal veszi ki a nyolcbites kimenetet (csonkolás, nem
    kerekítés); a modul docstringje írja le, miért marad ki a dither.
    """
    validate_image(image)
    table = np.clip(lut16 >> 8, 0, 255).astype(np.uint8)
    return table[image]


def apply_native_levels(
    image: np.ndarray, black: float, white: float, gamma: float = 1.0
) -> np.ndarray:
    """Szinthúzás a natív magok szerint (`0x0090c3b0`).

    Ez a `triple2` (fekete-/fehérpont csúszka) és a `triple3`
    (Kiemelések/Árnyékok) második lépése. A #685 mérőszettjén a teljes
    `triple2`/`triple3` lánc átlagos ΔE-je a valódi Picasa-kimenethez
    **0,00–0,37** (az érintetlen kép 14,8–58,8) — vagyis pixelpontos.
    """
    return apply_native_lut16(image, native_level_lut(black, white, gamma))


def apply_native_contrast(
    image: np.ndarray,
    contrast: float,
    brightness: float = 0.0,
    gamma: float = 1.0,
) -> np.ndarray:
    """Kontraszt a natív mag szerint (`0x0090c2c0`).

    A `contrast` szűrő burkolója (`0x008f8a20`) fényerőnek 0-t, gammának
    1,0-t ad; a `triple` (`0x008f8a60`) mindkettőt csúszkából tölti.

    A #685 mérőszettjén az önálló `contrast` szűrő átlagos ΔE-je a valódi
    Picasa-kimenethez **0,18–0,31** (az érintetlen kép 6,0–20,9).
    """
    return apply_native_lut16(
        image, native_contrast_lut(contrast, brightness, gamma)
    )


def apply_gamma(image: np.ndarray, level: float) -> np.ndarray:
    """`gamma` („Gamma Correct") — a szinthúzó LUT tiszta gamma-ága.

    A burkoló (`0x008f8e30`) az egyetlen csúszkából `exp(szint)`-et számol
    (`0x0040eac0` = `exp`), és ezt adja tovább GAMMA-ként; a LUT-építő
    `1/gamma`-val emel hatványra, tehát a tényleges kitevő `exp(−szint)`.
    Pozitív szint világosít, negatív sötétít, a 0 azonosság, és a két
    végpont (0 és 255) helyben marad.

    A #685 mérőszettjén ez a leképezés adódott (mindhárom csúszkaálláson
    ΔE **0,34–0,41**, míg a fordított irány 8,3–45,7) — vagyis a kitevő
    iránya nem feltevés, hanem mért.
    """
    return apply_native_levels(image, 0.0, 1.0, gamma=math.exp(level))


__all__ = [
    "NATIVE_LUT_FULL",
    "apply_gamma",
    "apply_native_contrast",
    "apply_native_levels",
    "apply_native_lut16",
    "native_contrast_lut",
    "native_level_lut",
]
