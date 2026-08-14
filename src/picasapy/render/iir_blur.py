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

A **sugár → együttható** leképezés MÉRÉSBŐL való (a dekompilátor az
`k = round(pow(a, b))` két argumentumát az x87-veremen elvesztette):

```
r = exp(−1/R)          k = round(65536 · (1 − r))
```

vagyis **az `R` paraméter képpontban az e-hajtási távolság**. A mérés a
windowsos Picasa „Ragyogás" effektjének öt csúszkaállásán készült, a
végponttól végpontig igazolás átlagos hibája 0,6–1,2 szint (JPEG-zaj
nagyságrendje). Részletek és a mért táblázatok:
`docs/specs/picasa-native-filter-workers.md` 4.2.1 és 4.2.5.

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


def blur_coefficient(radius: float) -> int:
    """A `0x009dd0d0` 16 bites együtthatója az `R` sugárhoz (4.2.5 MÉRÉS).

    `radius <= 0` esetén `65536`-ot ad: az állapot minden lépésben teljesen
    átveszi a bemenetet, tehát a szűrő azonosság. (A natív `pow(e, −1/R)`
    itt nem lenne értelmezett — a hívók a 0 sugarat eleve kihagyják.)
    """
    if radius <= 0.0:
        return _COEFF_SCALE
    return int(round(_COEFF_SCALE * (1.0 - math.exp(-1.0 / radius))))


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
