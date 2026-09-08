"""A Picasa KÖZÖS elmosó magja — `0x009dd0d0` (#623).

Ezt hívja a `glow`, a sugaras család (`radblur`, `radsat`), a `dir_sharp`
és a `linblur` is. **Nem konvolúció**, hanem elsőrendű IIR (exponenciális)
szűrő, tengelyenként oda-vissza futtatva — ezért volt a Picasa elmosása
interaktív már 2005-ben: a költsége képpontonként O(1), a sugártól
függetlenül.

```
állapot s: 9.7 fixpontban (érték << 7)
előre:   s += ((x[i] << 7) − s) · k >> 16 ;   y[i] = clamp(s >> 7, 0, 255)
vissza:  ugyanez a MÁR SZŰRT soron, visszafelé
```

⭐ **A sugár → együttható leképezés KIOLVASVA a binárisból** (2026-09-09,
#2773). A korábbi docstring azt állította, hogy a `pow` két argumentuma az
x87-veremen elveszett, és mérésből illesztett alakot használt
(`exp(−1/R)`, 65536-os skála). A diszasszemblátumban **mindkét argumentum
ott van**:

```
0x009dd177  fld1                          ; 1
0x009dd17c  fdivrp st(1)                  ; 1/R
0x009dd17e  fld qword [0x00c7dd30]        ; = 0.1        ← az ALAP
0x009dd186  call 0x00c0b410               ; pow(0.1, 1/R)
0x009dd18b  fld1 ; fsubrp st(2)           ; 1 − pow
0x009dd199  fmul qword [0x00cf3ff0]       ; = 32767.0    ← a SKÁLA
0x009dd19f  call 0x00c29990               ; __ftol → CSONKOL
```

⇒ **`k = trunc((1 − 0,1^(1/R)) · 32767)`**, tengelyenként (a második
tengelyre ugyanez `[ebp+0x10]`-zel, `0x009dd1a4`-től). A menet lépése a
MMX-kódból: `punpcklbw`+`psrlw 1` (érték `<< 7`), `psubw`, **`pmulhw`**
(előjeles `>> 16`), `paddw`, majd `psrlw 7`+`packuswb` — pontosan a lenti
rekurzió, tehát az együttható osztója 65536, a SKÁLÁJA viszont 32767.

Vagyis az `R` **nem** az e-hajtási, hanem a **tizedelési** távolság: `R`
képpont alatt esik a súly a tizedére. A korábbi, illesztett alak ezt a
különbséget a hívók sugár-paraméterében nyelte el (szabad paraméter). A
javítás mérése és a hívónkénti ΔE: `docs/specs/picasa-native-filter-workers.md`
4.2.1 és 4.2.5.

## Amit ez a modul KÖZELÍT

- **Az IIR állapotának kezdőértéke.** A natív MMX-kód ezen a ponton nem
  dekompilálható; itt a menet a szélső képpont értékéről indul (perem-
  ismétlés). A 0-ról indítás látható sötét szegélyt adna, ami az eredeti
  Picasában nem figyelhető meg — de ez érvelés, nem mérés.
- **A menetek sorrendje** (előbb vízszintes, majd függőleges) a
  specifikáció leírását követi; két lineáris szűrő sorrendje amúgy is csak
  a kerekítés szintjén számít.
"""

from __future__ import annotations

import math

import numpy as np

from picasapy.render.curves import validate_image

#: Az állapot 9.7 fixpontban tárolódik: az érték 128-szorosa.
_STATE_SHIFT = 7

#: A `pmulhw` (előjeles 16×16 → felső 16 bit) osztója.
_COEFF_SCALE = 65536

#: A natív együttható SKÁLÁJA (`[0x00cf3ff0]`) — nem azonos az osztóval: a
#: `pmulhw` 65536-tal oszt, a natív szorzó viszont 32767, tehát az egy
#: lépésben átvett arány legfeljebb ~0,5 (#2773).
_NATIVE_COEFF_SCALE = 32767

#: A natív `pow` ALAPJA (`[0x00c7dd30]`) — az `R` a TIZEDELÉSI távolság.
_NATIVE_POW_BASE = 0.1


def blur_coefficient(radius: float) -> int:
    """A `0x009dd0d0` 16 bites együtthatója az `R` sugárhoz — a NATÍV alak.

    `k = trunc((1 − 0,1^(1/R)) · 32767)`, a binárisból kiolvasva (#2773, ld.
    a modul docstringjét). A `__ftol` **csonkol**, nem kerekít.

    `radius <= 0` esetén a natív oldal az adott tengelyt ki sem futtatja (a
    `0x009dd150`–`0x009dd177` két jelzőbájtja dönt); a hívóink ugyanígy
    kihagyják, itt a teljes átvétel a biztonságos alapérték.
    """
    if radius <= 0.0:
        return _COEFF_SCALE
    arany = 1.0 - math.pow(_NATIVE_POW_BASE, 1.0 / radius)
    return int(_NATIVE_COEFF_SCALE * arany)


def _sweep_axis_zero(values: np.ndarray, coefficient: int) -> np.ndarray:
    """Oda-vissza IIR-menet a 0. tengely mentén, egész aritmetikával.

    A `values` int64 tömb (N, …) alakban, 0…255 értékekkel; az eredmény új
    tömb — a bemenetet nem írjuk felül. (Az int64 nem fényűzés: a
    `(x − s) · k` szorzat 32 biten éppen csak elférne, és a felső határon
    némán körbefordulna.)
    """
    result = np.empty_like(values)
    delta = np.empty_like(values[0])
    # a menetek helyben dolgoznak, előre lefoglalt segédtömbökkel: egy 2000
    # képpont széles képen ez a különbség másodpercekben mérhető
    _sweep_forward(values, result, delta, coefficient)
    _sweep_backward(result, delta, coefficient)
    return result


def _step(
    source_row: np.ndarray,
    state: np.ndarray,
    delta: np.ndarray,
    coefficient: int,
    target_row: np.ndarray,
) -> None:
    """Egy IIR-lépés: `s += ((x << 7) − s) · k >> 16`, majd `y = s >> 7`."""
    np.left_shift(source_row, _STATE_SHIFT, out=delta)
    delta -= state
    delta *= coefficient
    delta >>= 16  # a natív `>> 16` ELŐJELES, azaz padló — a `>>=` is az
    state += delta
    np.right_shift(state, _STATE_SHIFT, out=target_row)


def _sweep_forward(
    values: np.ndarray, result: np.ndarray, delta: np.ndarray, coefficient: int
) -> None:
    state = values[0] << _STATE_SHIFT
    for index in range(values.shape[0]):
        _step(values[index], state, delta, coefficient, result[index])
    np.clip(result, 0, 255, out=result)


def _sweep_backward(
    result: np.ndarray, delta: np.ndarray, coefficient: int
) -> None:
    """A visszamenet a MÁR SZŰRT (bájtra vágott) soron fut — a natív mag is
    a kimeneti puffert olvassa vissza."""
    state = result[-1] << _STATE_SHIFT
    for index in range(result.shape[0] - 1, -1, -1):
        _step(result[index], state, delta, coefficient, result[index])
    np.clip(result, 0, 255, out=result)


def apply_picasa_blur(
    image: np.ndarray, radius_x: float, radius_y: float
) -> np.ndarray:
    """A natív elmosó mag: vízszintes, majd függőleges kétmenetes IIR.

    A két sugár KÉPPONTBAN értendő e-hajtási távolság (4.2.5), és
    tengelyenként külön adható meg — a natív hívás is két külön értéket kap
    (`FUN_009dd0d0(kep, blurX, blurY, …)`).
    """
    validate_image(image)
    work = image.astype(np.int64)
    if radius_x > 0.0:
        coefficient = blur_coefficient(radius_x)
        work = _sweep_axis_zero(work.transpose(1, 0, 2), coefficient).transpose(1, 0, 2)
    if radius_y > 0.0:
        work = _sweep_axis_zero(work, blur_coefficient(radius_y))
    return work.astype(np.uint8)


__all__ = ["apply_picasa_blur", "blur_coefficient"]
