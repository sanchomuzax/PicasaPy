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

import numpy as np

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


def c_divide(numerator, denominator):
    """Előjeles egész-osztás **nulla felé csonkolva** — a C `/` (x86 `idiv`).

    A Python `//` PADLÓZ: `-7 // 2 == -4`, miközben a C `-7 / 2 == -3`.
    A becslő két osztásánál ez 1-es eltérést okoz minden negatív
    számlálónál, és a 12 páron mért hiba több mint felét ez adta
    (1,370 → 0,614).
    """
    numerator = np.asarray(numerator)
    denominator = np.asarray(denominator)
    quotient = np.abs(numerator) // np.abs(denominator)
    negative = (numerator < 0) != (denominator < 0)
    return np.where(negative, -quotient, quotient)


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
    red = image[..., 0].astype(np.int64)
    green = image[..., 1].astype(np.int64)
    blue = image[..., 2].astype(np.int64)

    usable = (
        (green >= 32)
        & (green <= 224)
        & (2 * red > green)
        & (2 * green > red)
        & (2 * blue > green)
        & (2 * green > blue)
    )
    if not usable.any():
        return (_NEUTRAL, _NEUTRAL)

    r, g, b = red[usable], green[usable], blue[usable]
    red_bin = np.clip(c_divide(32 * (r - g), np.minimum(r, g)) + _CENTER, 0, _BINS - 1)
    blue_bin = np.clip(c_divide(32 * (b - g), np.minimum(b, g)) + _CENTER, 0, _BINS - 1)

    histogram = np.zeros((_BINS, _BINS), dtype=np.int64)
    np.add.at(histogram, (blue_bin, red_bin), 1)

    rows, columns = np.mgrid[0:_BINS, 0:_BINS]
    distance = np.maximum(np.abs(columns - _CENTER), np.abs(rows - _CENTER))
    weight = ((_CENTER - distance).astype(np.int64) ** 3) >> 5
    histogram = np.where(weight > 0, (histogram * weight) >> 8, 0)

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
    pixels = image.astype(np.int64)
    result = np.empty_like(pixels)
    for row in range(3):
        accumulator = (
            pixels[..., 0] * matrix[row, 0]
            + pixels[..., 1] * matrix[row, 1]
            + pixels[..., 2] * matrix[row, 2]
        )
        result[..., row] = np.clip(accumulator >> 16, 0, 255)
    return result.astype(np.uint8)


__all__ = [
    "AUTOCOLOR_MATRIX",
    "apply_autocolor_matrix",
    "autocolor_matrix_16_16",
    "c_divide",
    "estimate_illuminant",
]
