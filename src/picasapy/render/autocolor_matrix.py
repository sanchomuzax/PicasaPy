"""Az `autocolor` 3×3 SZÍNMÁTRIXA — `M · diag(g) · M⁻¹` (#759).

## Miért mátrix, és miért nem elég a csatornánkénti erősítés

A natív alkalmazó (`0x0090eda0`) a legelső dolgaként **kilenc float
konstanst** másol egy kilenc elemű tömbbe (`rep movsd`, `ecx = 9`,
sorfolytonosan), és a képpont-ciklusa ezzel a mátrixszal szoroz 16.16
fixpontban. Az `autocolor` tehát **nem** három független csatorna-erősítés:
a becsült erősítések a mátrix TERÉBEN épülnek be, és a kimeneten
kereszt-tagok jelennek meg.

Ezért nem ment 2,35 alá semmilyen csatornánkénti modell — nem a becslő volt
gyenge, hanem a modell alakja volt hiányos.

## A csonkoló osztás — a maradék hiba több mint fele

A becslő két előjeles egész-osztása **C-szemantikájú** (`idiv`): **nulla felé
csonkol**. A visszafejtett modell először Python `//`-t használt, ami
**padlóz** — negatív számlálónál ez 1-gyel tér el, és végigfut az egész
képen. A `c_divide` ezt hozza helyre.

## Mérés — a 12 golden páron

`referencia/imfeellucky/ImFeelLucky-noeffect/` → `referencia/autocolor/AutoColor/`
(a mérőszkript a privát repóban; a képek nem kerülhetnek ide):

| modell | átlagos csatorna-eltérés |
|---|---:|
| érintetlen kép | 5,287 |
| a korábbi, csatornánkénti modellünk (#541) | 2,352 |
| `M⁻¹ · diag(g) · M` (rossz sorrend) | 2,169 |
| `M · diag(g) · M⁻¹`, padlózó osztással | 1,370 |
| **`M · diag(g) · M⁻¹`, csonkoló osztással** | **0,614** |

A 0,614 a JPEG-újratömörítés zajszintje (~0,69) **alatt** van; a 12-ből 10
javult, egy sem romlott.

## Miért látszik a dekompilátumban KÉTSZER „a kilenc konstans"

Ez a modul legkönnyebben félreolvasható pontja, ezért ki van írva. A hívó a
`0x00a4a140` **előtt és után UGYANABBÓL a veremtömbből** olvas, és a
dekompilátumban mindkét helyen a betöltött kilenc konstans látszik — a
`0x00a4a140` viszont közben **felülírja a tömböt az inverzzel**. Vagyis:

- a hívás ELŐTTI olvasás `M`,
- a hívás UTÁNI minden olvasás már `M⁻¹`.

Ezért képződik a `g` mindkét oldala `M⁻¹`-gyel:

```
P = M⁻¹ · (L, L, L)ᵀ      0x0090eefa–0x0090ef73
Q = M⁻¹ · (kR, kG, kB)ᵀ   0x0090ef9a–0x0090effe
g = P ⊘ Q                 0x0090f002–0x0090f02b
A = M · diag(g) · M⁻¹
```

Aki a nyers dekompilátumból olvassa, `M`-et fog látni ott is, ahol `M⁻¹`
van — és `M · diag(g) · M`-re jut, ami a középszürkét fehérre égeti.

## Két csapda, amibe könnyű beleesni

1. **Végig `float32`.** A natív mag is abban számol. `float64`-gyel az
   egységmátrix `0,99999999`-re jön ki, és a csonkítás **65535**-öt ad
   65536 helyett — ez képpontonként egy szintnyi, rendszeres sötétítés.
2. **A sorrend `M · diag(g) · M⁻¹`**, nem fordítva. Képfüggetlen
   bizonyíték: semleges becslésnél (`g = 1`) csak ez adja vissza az
   egységmátrixot; a másik olvasat (`M · diag(g) · M`) `M²`-et adna, ami a
   középszürkét fehérre égetné.
"""

from __future__ import annotations

from functools import lru_cache

import numpy as np

from picasapy.lazy_cv2 import cv2
from picasapy.fixedpoint import c_int_div
from picasapy.render.curves import validate_image

#: A natív `0x0090eda0` kilenc konstansa, SORFOLYTONOSAN. `float32` —
#: ld. a modul-docstring 1. csapdáját.
AUTOCOLOR_MATRIX = np.array(
    [
        [1.9044, 0.4508, -0.3826],
        [-0.0532, 1.8018, 0.1995],
        [0.0491, -0.3057, 1.8576],
    ],
    dtype=np.float32,
)

_MATRIX_INVERSE = np.linalg.inv(AUTOCOLOR_MATRIX.astype(np.float64)).astype(np.float32)

#: A natív luma-súlyok (`0x4d`, `0x97`, `0x1c`), 8 bites eltolással.
_LUMA_WEIGHTS = (77, 151, 28)

#: A semleges becslés — `128 = egység` (a `k(d)` skálája ezt adja `d = 0`-ra).
_NEUTRAL = 128

#: A becslő 64×64-es hisztogramjának mérete és a semleges pont indexe.
_BINS = 64
_CENTER = 32


#: A becslő két osztása C-szemantikájú (`idiv`, nulla felé csonkol). A
#: megvalósítás a közös `picasapy/fixedpoint.py`-ban él (#926); ez a név a
#: modul régi, kifelé is használt alakja.
c_divide = c_int_div


@lru_cache(maxsize=1)
def _illuminant_ratio_bins() -> np.ndarray:
    """A két 256×256-os arányosztás előre kiszámított, bájtos eredménye."""
    red = np.arange(256, dtype=np.int32)[:, None]
    green = np.arange(256, dtype=np.int32)[None, :]
    numerator = 32 * (red - green)
    denominator = np.maximum(np.minimum(red, green), 1)
    quotient = np.where(
        numerator < 0,
        -((-numerator) // denominator),
        numerator // denominator,
    )
    return np.clip(quotient + _CENTER, 0, _BINS - 1).astype(np.uint8)


@lru_cache(maxsize=1)
def _illuminant_pair_table() -> np.ndarray:
    """Az arány-bin; a kétcsatorna-feltétel sértése 255-ös őrértéket kap."""
    red = np.arange(256, dtype=np.uint16)[:, None]
    green = np.arange(256, dtype=np.uint16)[None, :]
    usable = (
        (green >= 32)
        & (green <= 224)
        & (2 * red > green)
        & (2 * green > red)
    )
    return np.where(usable, _illuminant_ratio_bins(), 255).astype(np.uint8)


def estimate_illuminant(image: np.ndarray) -> tuple[int, int]:
    """A megvilágítás becslése: `(kR, kB)`, ahol `128` a semleges.

    A natív becslő (`0x0090f8f0`) lépései:

    1. **semleges-képpont feltétel** — `32 ≤ G ≤ 224`, és egyik csatorna
       sem több a másik kétszeresénél;
    2. 64×64-es hisztogram az `R/G` és `B/G` kiegyensúlyozatlanságból
       (a `±32`-es tartomány a semleges pont köré igazítva);
    3. **köbös Csebisev-súlyozás** a semleges pont köré (`(32 − táv)³ / 32`);
    4. súlypont → `k(d)`, ahol a pozitív és negatív irány KÜLÖNBÖZŐ
       képlettel skálázódik (`(32+d)·4`, illetve `16384 / ((32−d)·4)`).
    """
    validate_image(image)
    red = image[..., 0]
    green = image[..., 1]
    blue = image[..., 2]
    table = _illuminant_pair_table()
    maps = np.empty((*green.shape, 2), dtype=np.int16)
    maps[..., 0] = green
    maps[..., 1] = red
    red_lookup = cv2.remap(
        table,
        maps,
        None,
        interpolation=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_REPLICATE,
    )
    maps[..., 1] = blue
    blue_lookup = cv2.remap(
        table,
        maps,
        None,
        interpolation=cv2.INTER_NEAREST,
        borderMode=cv2.BORDER_REPLICATE,
    )
    usable = (red_lookup != 255) & (blue_lookup != 255)

    if image.shape[0] * image.shape[1] < 2**24:
        # A 2560×1707-es célképen minden cellaszámláló pontosan ábrázolható
        # float32-ben; a C++-os 2D hisztogram elhagyja a NumPy-s képpontszintű
        # kód-összefűzést és indexelt gyűjtést.
        bins = cv2.merge((blue_lookup, red_lookup))
        histogram = cv2.calcHist(
            [bins], [0, 1], usable.astype(np.uint8), [_BINS, _BINS],
            [0, _BINS, 0, _BINS],
        ).astype(np.int64)
    else:
        # Nagyobb képeknél a float32 hisztogram számlálója elveszíthet egyes
        # egész értékeket; a bincount itt megtartja a korábbi pontos utat.
        blue_bin = blue_lookup[usable]
        red_bin = red_lookup[usable]
        histogram = np.bincount(
            blue_bin.astype(np.int32) * _BINS + red_bin,
            minlength=_BINS * _BINS,
        ).reshape(_BINS, _BINS)

    rows, columns = np.mgrid[0:_BINS, 0:_BINS]
    distance = np.maximum(np.abs(columns - _CENTER), np.abs(rows - _CENTER))
    radius = np.maximum(_CENTER - distance, 0).astype(np.int64)
    weight = (radius**3) >> 5
    histogram *= weight
    histogram >>= 8

    total = int(histogram.sum())
    if total == 0:
        return (_NEUTRAL, _NEUTRAL)

    offset_x = int(np.clip(int(c_divide(int((histogram * (columns - _CENTER)).sum()), total)), -32, 32))
    offset_y = int(np.clip(int(c_divide(int((histogram * (rows - _CENTER)).sum()), total)), -32, 32))

    def scale(offset: int) -> int:
        return (32 + offset) * 4 if offset >= 0 else 16384 // ((32 - offset) * 4)

    return (int(np.clip(scale(offset_x), 0, 255)), int(np.clip(scale(offset_y), 0, 255)))


def autocolor_matrix_16_16(red_gain: int, green_gain: int, blue_gain: int) -> np.ndarray:
    """`M · diag(g) · M⁻¹` 16.16 fixpontban, csonkítva — a natív alak.

    A `g` a mátrix terében képződik: a becsült megvilágítás-szín és az
    AZONOS LUMÁJÚ semleges szürke transzformáltjainak hányadosa.
    """
    gains = np.array(
        [max(red_gain, 1), max(green_gain, 1), max(blue_gain, 1)], dtype=np.float32
    )
    red_w, green_w, blue_w = _LUMA_WEIGHTS
    luma = np.float32(
        (red_w * max(red_gain, 1) + green_w * max(green_gain, 1) + blue_w * max(blue_gain, 1)) >> 8
    )
    neutral = (_MATRIX_INVERSE @ np.array([luma, luma, luma], dtype=np.float32)).astype(np.float32)
    estimated = (_MATRIX_INVERSE @ gains).astype(np.float32)
    scale = (neutral / estimated).astype(np.float32)

    matrix = (AUTOCOLOR_MATRIX @ (np.diag(scale).astype(np.float32) @ _MATRIX_INVERSE)).astype(
        np.float32
    )
    return np.trunc(matrix.astype(np.float64) * 65536.0).astype(np.int64)


def apply_autocolor_matrix(image: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    """A 16.16 mátrix alkalmazása egész aritmetikával, a natív mintájára."""
    validate_image(image)
    coeffs64 = np.asarray(matrix, dtype=np.int64)
    # A pixelcsatorna legfeljebb 255. Ha minden sor abszolút összegének
    # szorzata 255-tel elfér int32-ben, akkor az összes szorzat és összeg is
    # elfér benne. A tipikus mátrix ezen a feltételen bőven belül van; a
    # ritka, tágabb belső hívásnál megtartjuk az eredeti int64 utat.
    int32_max = np.iinfo(np.int32).max
    coefficient_limit = int32_max // 255
    if np.any(coeffs64 > coefficient_limit) or np.any(coeffs64 < -coefficient_limit):
        pixels = image.astype(np.int64)
        result = np.empty_like(pixels)
        for row in range(3):
            accumulator = (
                pixels[..., 0] * coeffs64[row, 0]
                + pixels[..., 1] * coeffs64[row, 1]
                + pixels[..., 2] * coeffs64[row, 2]
            )
            result[..., row] = np.clip(accumulator >> 16, 0, 255)
        return result.astype(np.uint8)

    row_bounds = np.sum(np.abs(coeffs64), axis=1, dtype=np.int64) * 255
    if np.any(row_bounds > int32_max):
        pixels = image.astype(np.int64)
        result = np.empty_like(pixels)
        for row in range(3):
            accumulator = (
                pixels[..., 0] * coeffs64[row, 0]
                + pixels[..., 1] * coeffs64[row, 1]
                + pixels[..., 2] * coeffs64[row, 2]
            )
            result[..., row] = np.clip(accumulator >> 16, 0, 255)
        return result.astype(np.uint8)

    # NumPy futtatja a lapos, folytonos int32 mátrixszorzást natív C-kódban.
    # A fenti sorhatár-ellenőrzés miatt minden szorzatösszeg int32-ben pontos,
    # így a Q16 jobbra tolás az eredeti, bájtra azonos csonkítást adja.
    pixels = image.astype(np.int32)
    coeffs = coeffs64.astype(np.int32)
    accumulators = pixels.reshape(-1, 3) @ coeffs.T
    return np.clip(accumulators >> 16, 0, 255).astype(np.uint8).reshape(image.shape)


__all__ = [
    "AUTOCOLOR_MATRIX",
    "apply_autocolor_matrix",
    "autocolor_matrix_16_16",
    "c_divide",
    "estimate_illuminant",
]
