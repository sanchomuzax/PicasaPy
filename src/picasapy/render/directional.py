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

Ld. `docs/specs/picasa-native-filter-workers.md` 2.7.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image

#: A natív magok a rámpa-súlyt 8.8 fixpontban használják (`round(s * 256)`),
#: és `>> 8`-cal osztanak vissza.
_WEIGHT_SCALE = 256.0


def directional_ramp(
    height: int, width: int, horizontal: float, vertical: float
) -> np.ndarray:
    """A `dir_*` család közös, képpontonkénti súlya, `(H, W)` alakban.

    A natív kód a bal felső saroktól `−a`-ról indul és `+a`-ig nő (a
    függőleges tengelyre ugyanígy), tehát a képpont KÖZEPÉT nem tolja el —
    a rámpa a `[0, W)` egészek felett fut.
    """
    if height <= 0 or width <= 0:
        raise ValueError(f"Érvénytelen képméret: {width}×{height}")
    a = float(np.clip(horizontal, -1.0, 1.0))
    b = float(np.clip(vertical, -1.0, 1.0))
    xs = np.arange(width, dtype=np.float32) * np.float32(2.0 / width) - np.float32(1.0)
    ys = np.arange(height, dtype=np.float32) * np.float32(2.0 / height) - np.float32(1.0)
    return np.float32(a) * xs[np.newaxis, :] + np.float32(b) * ys[:, np.newaxis]


def apply_dir_sat(
    image: np.ndarray, horizontal: float, vertical: float
) -> np.ndarray:
    """Irányított telítettség — a natív `0x0090dbb0` mag.

    ```c
    L = (2*R + 5*G + B) >> 3;                 // súlyozott luma
    a = round(s(x,y) * 256);
    if (a < 0) { a += 256; out_c = L + (((c - L) * a) >> 8); }        // telítetlenítés
    else       { out_c = clamp(c + (((c - L) * a) >> 8), 0, 255); }   // telítés
    ```

    **A luma-súlyozás itt más, mint a Derítőfényben** (`(B + 2G + R) >> 2`):
    a Picasa két különböző képletet használ, és a kettő összekeverése néma,
    nehezen megtalálható színhibát okoz.
    """
    validate_image(image)
    height, width = image.shape[:2]
    ramp = directional_ramp(height, width, horizontal, vertical)
    weight = np.round(ramp * np.float32(_WEIGHT_SCALE))

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
    v = c;
    if (s >= 0) v ^= 0xff;                          // világosításhoz tükrözés
    v = (((v*v*v) >> 16) * a + (256 - a) * v) >> 8; // keverés a KÖBÖS görbével
    if (s >= 0) v ^= 0xff;
    ```

    Vagyis **köbös tónusgörbe** (sötétítés), a világosítás pedig ugyanez
    **invertált tartományon**. A rámpa csak azt szabja meg, képpontonként
    mennyit keverünk a köbösből: 0-nál változatlan, 256-nál teljesen köbös.
    """
    validate_image(image)
    height, width = image.shape[:2]
    ramp = directional_ramp(height, width, horizontal, vertical)
    amount = np.abs(np.round(ramp * np.float32(_WEIGHT_SCALE)))
    lighten = (ramp >= 0)[..., np.newaxis]

    values = image.astype(np.float32)
    mirrored = np.where(lighten, np.float32(255.0) - values, values)
    cubic = np.floor(mirrored * mirrored * mirrored / np.float32(65536.0))
    blended = np.floor(
        (cubic * amount[..., np.newaxis] + (np.float32(_WEIGHT_SCALE) - amount[..., np.newaxis]) * mirrored)
        / np.float32(_WEIGHT_SCALE)
    )
    result = np.where(lighten, np.float32(255.0) - blended, blended)
    return np.clip(result, 0.0, 255.0).astype(np.uint8)
