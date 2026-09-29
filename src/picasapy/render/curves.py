"""Görbe- és LUT-segédek a render-műveletekhez.

A golden-elemzés (`docs/specs/filters-decoded.md`) mérési pontjaiból
töréspontos görbéket építünk: 256 elemű float LUT, lineáris interpolációval
a pontok között. A kerekítés egyetlen helyen, az alkalmazáskor történik.
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

#: Görbe-töréspontok típusa: ((bemenet, kimenet), ...) — bemenet 0..255.
CurvePoints = tuple[tuple[float, float], ...]


def validate_image(image: np.ndarray) -> None:
    """RGB uint8 (H, W, 3) alak-ellenőrzés — hibás bemenetnél ValueError."""
    if not isinstance(image, np.ndarray):
        raise ValueError(f"A kép numpy.ndarray kell legyen, nem {type(image)!r}")
    if image.dtype != np.uint8:
        raise ValueError(f"A kép dtype-ja uint8 kell legyen, nem {image.dtype}")
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError(f"A kép alakja (H, W, 3) kell legyen, nem {image.shape}")


def _natural_spline_second_derivatives(
    xs: np.ndarray, ys: np.ndarray
) -> np.ndarray:
    """A természetes köbös spline második deriváltjai (#629).

    A natív `0x008f33b0` a klasszikus tridiagonális megoldást futtatja
    (`2.0`-s főátló, `6.0`-s osztott differencia, Numerical Recipes
    `spline`); **természetes** spline, azaz a két végén a második derivált
    nulla — ezt a dekompilátum a `y2[0] = y2[n−1] = 0` beállítással mondja ki.
    """
    count = len(xs)
    second = np.zeros(count, dtype=np.float64)
    scratch = np.zeros(count, dtype=np.float64)
    for index in range(1, count - 1):
        sigma = (xs[index] - xs[index - 1]) / (xs[index + 1] - xs[index - 1])
        pivot = sigma * second[index - 1] + 2.0
        second[index] = (sigma - 1.0) / pivot
        slope_diff = (ys[index + 1] - ys[index]) / (xs[index + 1] - xs[index]) - (
            ys[index] - ys[index - 1]
        ) / (xs[index] - xs[index - 1])
        scratch[index] = (
            6.0 * slope_diff / (xs[index + 1] - xs[index - 1])
            - sigma * scratch[index - 1]
        ) / pivot
    for index in range(count - 2, 0, -1):
        second[index] = second[index] * second[index + 1] + scratch[index]
    second[0] = 0.0
    second[count - 1] = 0.0
    return second


def _validate_points(points: CurvePoints) -> tuple[np.ndarray, np.ndarray]:
    if len(points) < 2:
        raise ValueError(f"Legalább két töréspont kell, kaptunk: {points!r}")
    xs = np.array([point[0] for point in points], dtype=np.float64)
    ys = np.array([point[1] for point in points], dtype=np.float64)
    if np.any(np.diff(xs) <= 0):
        raise ValueError(f"A töréspontok x-e szigorúan növekvő kell legyen: {points!r}")
    return xs, ys


def _evaluate_natural_spline(xs: np.ndarray, ys: np.ndarray, x: np.ndarray) -> np.ndarray:
    """A természetes köbös spline kiértékelése `x` TETSZŐLEGES (a
    töréspontok tartományán kívül eső) pontjaiban is — EXTRAPOLÁLVA (#3941).

    **#629: az eredeti nem lineárisan interpolál.** A `0x008f3290`
    munkafüggvény (a Numerical Recipes `splint` mintája) a szakaszon belül
    köbös tagot is számol:

        h = x[j+1] − x[j]
        A = (x[j+1] − x)/h          B = (x − x[j])/h
        y = A·y[j] + B·y[j+1] + ((A³−A)·y2[j] + (B³−B)·y2[j+1]) · h²/6

    A töréspontok tartományán KÍVÜL a natív a szélső intervallum köbös
    polinomját EXTRAPOLÁLJA (#3941 kutatás) — ezt a `searchsorted` indexének
    a szélső szakaszra való vágása (`np.clip(..., 1, len(xs) - 1)`) magától
    megadja: a súlyok `[0, 1]`-en KÍVÜLRE is kerülhetnek, a képlet emiatt
    a szélső szakasz görbéjét folytatja.
    """
    second = _natural_spline_second_derivatives(xs, ys)
    upper = np.clip(np.searchsorted(xs, x, side="right"), 1, len(xs) - 1)
    lower = upper - 1

    width = xs[upper] - xs[lower]
    left_weight = (xs[upper] - x) / width
    right_weight = (x - xs[lower]) / width
    return (
        left_weight * ys[lower]
        + right_weight * ys[upper]
        + (
            (left_weight**3 - left_weight) * second[lower]
            + (right_weight**3 - right_weight) * second[upper]
        )
        * width
        * width
        / 6.0
    )


def curve_lut(points: CurvePoints) -> np.ndarray:
    """Töréspontokból 256 elemű float64 LUT, TERMÉSZETES KÖBÖS SPLINE-nal.

    A korábbi lineáris közelítés a valódi `filterdesc.xml` görbéken a
    **60-as évek** effektnél 21,6, a **Kinemaszkópnál** 17,5 szintet tévedett
    — hússzorosa a ditherelés ±1-es tűrésének, tehát szemmel látható.

    **Kétpontos görbénél a kettő azonos** (mindkét végén nulla a második
    derivált, így a köbös tag eltűnik) — a Színinvertálás, a Neon és a
    Ceruzarajz kimenete bájtra változatlan.

    A töréspontok tartományán KÍVÜL a szélső értéket tartjuk (nem
    extrapolálunk): ez a 256 elemű, 0..255 indexű LUT-hoz igazodó
    egyszerűsítés, ÖNMAGÁBAN álló görbékre (a jelenlegi hívók mindegyikénél
    a töréspontok lefedik a teljes 0..255 tartományt, tehát ez nem térne
    el az extrapolációtól). **Az `AdjustCurves`-lánc** (mestergörbe →
    csatornagörbe) viszont a natívval megegyezően EXTRAPOLÁL — ott a
    mestergörbe kimenete túlfuthat a 0..255 tartományon, és ezt a
    csatornagörbének extrapolálva kell fogadnia (#3941, ld.
    `evaluate_curve_extrapolated` és `glimmer_ops.adjust_curves`). Ha ide
    valaha olyan hívó kerülne, aminek a töréspontjai NEM fedik a teljes
    0..255 tartományt, és a natív ott is extrapolál, azt új hívóként az
    `evaluate_curve_extrapolated`-del kell megoldani, ezt a függvényt nem
    szabad átállítani (más, már validált hívói erre a „tartás" viselkedésre
    építenek).
    """
    xs, ys = _validate_points(points)
    levels = np.arange(256, dtype=np.float64)
    values = _evaluate_natural_spline(xs, ys, levels)
    # a tartományon kívül a szélső érték (ld. a docstringet)
    return np.where(
        levels < xs[0], ys[0], np.where(levels > xs[-1], ys[-1], values)
    )


def evaluate_curve_extrapolated(points: CurvePoints, x: np.ndarray) -> np.ndarray:
    """A töréspontos görbe kiértékelése TETSZŐLEGES (akár 0..255-ön kívüli)
    `x` float-tömbre, a natív `0x008f3290` szerint EXTRAPOLÁLVA a szélső
    szakasz köbös polinomjával — nem vágva, nem kerekítve (#3941).

    Kizárólag az `AdjustCurves`-lánc (`glimmer_ops.adjust_curves`) használja:
    ott a mestergörbe kimenete a csatornagörbének továbbadva túlfuthat a
    0..255 tartományon. A `curve_lut` (256 elemű, 0..255 indexű LUT, a
    tartományon kívül a szélső értéket tartja) minden MÁS hívónál
    változatlan marad — ld. a docstringjét.

    Eltérés a natívtól: kettőnél kevesebb töréspontra a natív a bemenetet adja
    vissza (identitás, `0x008f329e`), ez a függvény `ValueError`-t dob. Egyik
    mai effekt görbéje sem ilyen; a viselkedést szándékosan nem változtattuk.
    """
    xs, ys = _validate_points(points)
    return _evaluate_natural_spline(xs, ys, np.asarray(x, dtype=np.float64))


def blend_luts(first: np.ndarray, second: np.ndarray, weight: float) -> np.ndarray:
    """Két LUT lineáris keveréke: `(1−weight)·first + weight·second`."""
    if first.shape != (256,) or second.shape != (256,):
        raise ValueError("A LUT-ok 256 eleműek kell legyenek")
    return (1.0 - weight) * first + weight * second


def apply_lut(image: np.ndarray, lut: np.ndarray) -> np.ndarray:
    """A float LUT alkalmazása a kép mindhárom csatornájára, kerekítéssel."""
    validate_image(image)
    if lut.shape != (256,):
        raise ValueError(f"A LUT alakja (256,) kell legyen, nem {lut.shape}")
    table = np.clip(np.rint(lut), 0, 255).astype(np.uint8)
    return table[image]


def lut_ramp() -> np.ndarray:
    """Identitás-LUT (0..255 float64 rámpa) — csatornánkénti LUT-ok alapja."""
    return np.arange(256, dtype=np.float64)


def apply_channel_luts(
    image: np.ndarray, luts: tuple[np.ndarray, np.ndarray, np.ndarray]
) -> np.ndarray:
    """Csatornánként KÜLÖN float LUT alkalmazása (R, G, B sorrend, #140).

    Pontonkénti (csatornánként független) műveletek uint8-natív, képméret-
    független költségű futtatása: a LUT-ok 256 elemű float tömbök, a
    kerekítés/clippelés az `apply_lut`-tal azonos módon itt történik.

    Az alkalmazás az OpenCV `LUT`-jával megy (#22): ugyanaz a bájttábla,
    bitre azonos kimenet, de a célgép előnézeti felbontásán ~100 ms helyett
    néhány ms (`tests/render/test_lut_gyorsitas_22.py`).
    """
    validate_image(image)
    if len(luts) != 3:
        raise ValueError(f"Pontosan három (R, G, B) LUT kell, kaptunk: {len(luts)}")
    for lut in luts:
        if lut.shape != (256,):
            raise ValueError(f"A LUT alakja (256,) kell legyen, nem {lut.shape}")
    tables = np.stack(
        [np.clip(np.rint(lut), 0, 255).astype(np.uint8) for lut in luts], axis=-1
    )
    return apply_byte_luts(image, tables)


def apply_byte_luts(image: np.ndarray, tables: np.ndarray) -> np.ndarray:
    """Csatornánkénti uint8 táblák alkalmazása: `ki[..., c] = tables[be[..., c], c]`.

    `tables` alakja `(256, 3)`, uint8. Új tömböt ad, a bemenetet nem írja át.
    """
    validate_image(image)
    if tables.shape != (256, 3) or tables.dtype != np.uint8:
        raise ValueError(
            f"A táblák alakja (256, 3) uint8 kell legyen, nem {tables.shape} {tables.dtype}"
        )
    if image.size == 0:
        # a `cv2.LUT` nulla kiterjedésű képre `None`-t ad
        # (ld. `display_modes._tablat_alkalmaz`)
        return image.copy()
    return cv2.LUT(np.ascontiguousarray(image), np.ascontiguousarray(tables[None]))
