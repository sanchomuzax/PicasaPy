"""A Picasa `dir_*` irányított effektcsaládja — a natív magokból (#623).

A család közös váza egy **lineáris térbeli rámpa**, amit a `dir_brite`
natív magja (`0x0090d8b0`) explicit módon mutat:

```
s(x, y) = a · (2x/W − 1) + b · (2y/H − 1)          a, b ∈ [−1, 1]
```

`a` a „Balról jobbra", `b` a „Felülről lefelé" csúszka; a natív kód maga
vágja be őket `[−1, 1]`-re. A rámpa a **kép közepére szimmetrikus**, és a
koordináta-rendszer a képhez kötött (nem a tartalomhoz).

A burkolók (`0x008f8fb0`, `0x008f9050`) a két csúszkát **közvetlenül**
adják tovább (`param+0x28`, `param+0x2c`) — a felületi korong (`puck`)
csak beállítja őket, a `filters=` láncban nem jelenik meg külön.

A képpontsúly mindhárom magban `w = csonk(128 · (x + y))`, ahol `x` és `y`
két float32 akkumulátor (`−a`-ról, ill. `−b`-ről indul, `a / (W >> 1)`,
ill. `b / (H >> 1)` lépéssel). A súly tehát a rámpa 128-szorosa, NEM
256-szorosa: a hatás a teljes kitérés felét adja (#3858, #3859).

Ld. `docs/specs/picasa-native-filter-workers.md` 2.7, „A súly szorzója
128, csonkolva”.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.iir_blur import apply_picasa_blur

#: A natív magok a súlyt `>> 8`-cal osztják vissza (8.8 fixpont).
_WEIGHT_SCALE = 256.0

#: A rámpa szorzója a súlyhoz: `w = csonk(128 · (x + y))` — `[0xcf3a38]`
#: = 128,0 (double), a `dir_sharp`-ban `[0xcf3d58]` = −128,0 (#3858).
_WEIGHT_MULTIPLIER = 128.0

#: A `dir_sharp` burkolója (`0x008f9090`) ezzel az osztóval számol
#: elmosási sugarat a rövidebb oldalból: `min(W, H) >> 3`.
_DIR_SHARP_RADIUS_DIVISOR = 8


def _clamped_sliders(horizontal: float, vertical: float) -> tuple[np.float32, np.float32]:
    """A két csúszka, a natív kód szerint `[−1, 1]`-re vágva, float32-ben."""
    return (
        np.float32(np.clip(horizontal, -1.0, 1.0)),
        np.float32(np.clip(vertical, -1.0, 1.0)),
    )


def _accumulator(count: int, start: np.float32) -> np.ndarray:
    """A natív float32 akkumulátor egy tengely mentén.

    `−start`-ról indul, és minden képpont után `start / (count >> 1)`-et
    ad hozzá, az eredményt float32-be VISSZAÍRVA (`0x0090db3c`,
    `0x0090db82`). A `np.add.accumulate` float32-ben sorban összegez, tehát
    a kerekítési hibák ugyanúgy halmozódnak, mint a natív hurokban.
    """
    # egy képpontos tengelynél a natív osztó 0 volna — ott a rámpa úgyis
    # csak a kezdőértékét veszi fel, ezért 1-gyel osztunk
    step = np.float32(float(start) / max(count >> 1, 1))
    terms = np.full(count, step, dtype=np.float32)
    terms[0] = -start
    return np.add.accumulate(terms, dtype=np.float32)


def directional_ramp(
    height: int, width: int, horizontal: float, vertical: float
) -> np.ndarray:
    """A `dir_*` család közös rámpája (`x + y`), `(H, W)` alakban.

    A natív kód a bal felső saroktól `−a`-ról indul és (majdnem) `+a`-ig nő
    (a függőleges tengelyre ugyanígy), két float32 akkumulátorral — a
    képpont KÖZEPÉT nem tolja el, a rámpa a `[0, W)` egészek felett fut. A
    két akkumulátor összege az x87-veremen áll össze, ezért itt float64.
    """
    if height <= 0 or width <= 0:
        raise ValueError(f"Érvénytelen képméret: {width}×{height}")
    a, b = _clamped_sliders(horizontal, vertical)
    xs = _accumulator(width, a).astype(np.float64)
    ys = _accumulator(height, b).astype(np.float64)
    return xs[np.newaxis, :] + ys[:, np.newaxis]


def directional_weight(
    height: int, width: int, horizontal: float, vertical: float
) -> np.ndarray:
    """A `dir_brite` és a `dir_sat` képpontsúlya: `csonk(128 · (x + y))`.

    Egész értékű float32 tömb, `[−256, 256]`-ban — vágás nincs, mert a
    rámpa legfeljebb `|a| + |b| ≤ 2` (`0x0090da70`–`0x0090da7a`).
    """
    ramp = directional_ramp(height, width, horizontal, vertical)
    return np.trunc(ramp * _WEIGHT_MULTIPLIER).astype(np.float32)


def dir_sharp_amount(
    height: int, width: int, horizontal: float, vertical: float
) -> np.ndarray:
    """A `dir_sharp` képpontonkénti élesítési ereje (`0x0090d600`).

    ```c
    K = trunc(128 * (fabs(a) + fabs(b)));      // globális horgony
    w = trunc(-128 * (x + y));                 // képpontsúly
    amount = (K - w) * 2;
    ```

    Az erő a rámpa NEGATÍV sarkában nulla, a pozitívban `≈ 2 · 2K`: az
    élesítés tehát oda esik, ahová a rámpa mutat.
    """
    ramp = directional_ramp(height, width, horizontal, vertical)
    a, b = _clamped_sliders(horizontal, vertical)
    anchor = np.trunc(_WEIGHT_MULTIPLIER * (abs(float(a)) + abs(float(b))))
    weight = np.trunc(ramp * -_WEIGHT_MULTIPLIER)
    return ((anchor - weight) * 2.0).astype(np.float32)


def apply_dir_sat(
    image: np.ndarray, horizontal: float, vertical: float
) -> np.ndarray:
    """Irányított telítettség — a natív `0x0090dbb0` mag.

    ```c
    L = (2*R + 5*G + B) >> 3;                 // súlyozott luma
    a = trunc(128 * (x + y));                 // ld. directional_weight
    if (a < 0) { a += 256; out_c = L + (((c - L) * a) >> 8); }        // telítetlenítés
    else       { out_c = clamp(c + (((c - L) * a) >> 8), 0, 255); }   // telítés
    ```

    **A luma-súlyozás itt más, mint a Derítőfényben** (`(B + 2G + R) >> 2`):
    a Picasa két különböző képletet használ, és a kettő összekeverése néma,
    nehezen megtalálható színhibát okoz.
    """
    validate_image(image)
    height, width = image.shape[:2]
    weight = directional_weight(height, width, horizontal, vertical)

    values = image.astype(np.float32)
    luma = np.floor(
        (
            np.float32(2.0) * values[..., 0]
            + np.float32(5.0) * values[..., 1]
            + values[..., 2]
        )
        / np.float32(8.0)
    )

    # A két natív ág UGYANAZT az értéket adja: a negatív ágban
    # `L + ((c−L)·(a+256) >> 8)` = `c + ((c−L)·a >> 8)`, mert `c−L` egész.
    # Csak a vágás különbözik — ott nem kell, mert a kimenet L és c közé
    # esik; a `clip` ezt nem befolyásolja.
    delta = values - luma[..., np.newaxis]
    result = values + np.floor(
        delta * weight[..., np.newaxis] / np.float32(_WEIGHT_SCALE)
    )
    return np.clip(result, 0.0, 255.0).astype(np.uint8)


def apply_dir_brite(
    image: np.ndarray, horizontal: float, vertical: float
) -> np.ndarray:
    """Irányított fényesség — a natív `0x0090d8b0` mag.

    ```c
    // a burkoló az ötödik argumentumot 0-nak adja: az előkorrekciós
    // középtónus-parabola tehát AZONOSSÁG, nem kell külön LUT
    w = trunc(128 * (x + y));                       // ld. directional_weight
    v = c;  a = |w|;
    if (w > 0) v ^= 0xff;                           // világosításhoz tükrözés
    v = (((v*v*v) >> 16) * a + (256 - a) * v) >> 8; // keverés a KÖBÖS görbével
    if (w > 0) v ^= 0xff;
    ```

    Vagyis **köbös tónusgörbe** (sötétítés), a világosítás pedig ugyanez
    **invertált tartományon**. A súly csak azt szabja meg, képpontonként
    mennyit keverünk a köbösből: 0-nál változatlan, 256-nál teljesen köbös.
    A 0-s súly a sötétítő ágra esik, de ott azonosság.
    """
    validate_image(image)
    height, width = image.shape[:2]
    weight = directional_weight(height, width, horizontal, vertical)
    amount = np.abs(weight)
    lighten = (weight > 0)[..., np.newaxis]

    values = image.astype(np.float32)
    mirrored = np.where(lighten, np.float32(255.0) - values, values)
    cubic = np.floor(mirrored * mirrored * mirrored / np.float32(65536.0))
    blended = np.floor(
        (cubic * amount[..., np.newaxis] + (np.float32(_WEIGHT_SCALE) - amount[..., np.newaxis]) * mirrored)
        / np.float32(_WEIGHT_SCALE)
    )
    result = np.where(lighten, np.float32(255.0) - blended, blended)
    return np.clip(result, 0.0, 255.0).astype(np.uint8)


def dir_sharp_blur_radius(height: int, width: int) -> int:
    """A `dir_sharp` elmosási sugara a burkolóból (`0x008f9090`).

    ```c
    uVar1 = min(szélesség, magasság) >> 3;
    if (uVar1 == 0) uVar1 = 1;
    FUN_009dd0d0(&másolat, (float)uVar1, (float)uVar1, ...);
    ```

    Vagyis a rövidebb oldal nyolcada — NAGY sugár: ez tehát nem finom
    részlet-élesítés, hanem **helyi kontraszt** („clarity") jellegű hatás.
    """
    if height <= 0 or width <= 0:
        raise ValueError(f"Érvénytelen képméret: {width}×{height}")
    return max(1, min(height, width) // _DIR_SHARP_RADIUS_DIVISOR)


def apply_dir_sharp(
    image: np.ndarray, horizontal: float, vertical: float
) -> np.ndarray:
    """Irányított unsharp mask — a natív `0x0090d600` mag.

    ```c
    K = trunc(128 * (fabs(a) + fabs(b)));  // globális horgony
    w = trunc(-128 * (x + y));             // képpontsúly
    amount = (K - w) * 2;                  // ld. dir_sharp_amount
    if (amount > 0)
        out_c = clamp(c + (((c − elmosott_c) * amount) >> 8), 0, 255);
    ```

    A mag maga **nem konvolvál**: az elmosott puffert a burkoló készíti el,
    `min(W, H) / 8` sugárral, a közös IIR-maggal (`iir_blur`). Az élesítés
    a rámpa **pozitív** sarkában a legerősebb (`≈ 2·2K`), a negatívban nulla
    (#3858).
    """
    validate_image(image)
    height, width = image.shape[:2]
    radius = float(dir_sharp_blur_radius(height, width))
    blurred = apply_picasa_blur(image, radius, radius).astype(np.float32)

    amount = dir_sharp_amount(height, width, horizontal, vertical)

    values = image.astype(np.float32)
    # a natív `>> 8` PADLÓ (nem kerekítés), és csak a pozitív erősségű
    # képpontokra fut le — a többit érintetlenül másolja
    sharpened = values + np.floor(
        (values - blurred) * amount[..., np.newaxis] / np.float32(_WEIGHT_SCALE)
    )
    result = np.where(
        (amount > 0.0)[..., np.newaxis], np.clip(sharpened, 0.0, 255.0), values
    )
    return result.astype(np.uint8)
