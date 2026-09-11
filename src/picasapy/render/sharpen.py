"""Élesítés: unsharp / unsharp2.

Mért modell (`docs/specs/filters-decoded.md`, golden 4. kör): unsharp mask,
erősítés ≈ 1,21·s; az `unsharp=1` (v1) bitre azonos az
`unsharp2=1,0.600000`-val.

## Az elmosómag: köbös B-spline, 3 képpont tartósugárral (#762)

Az `unsharp` (`0x0090c4a0`) nem Gauss-szal mos, hanem az ÁTMÉRETEZŐT
(`ytResampler`) hívja **1 : 1 léptékkel**, és a **2-es szűrőmódot** írja be
(`0x0090c4fa`: `mov [esp+0x58], 2`). A 2-es mód magja **köbös B-spline**,
tartósugár 2 — a beégetett `1,5f` harmadik argumentum pedig a szórásszorzóba
megy (`0x0090c4e2`–`0x0090c4e8`), ami a magot másfélszeresre szélesíti, tehát
a **tényleges tartósugár 3 képpont**.

| bizonyíték | cím |
|---|---|
| a súlytáblát két móddal indexelt ugrótábla építi | `0xa40550` (tartósugár) · `0xa40574` (súlyfüggvény) |
| a 2-es mód tartósugara **2,0** | `0xa40550[2] = 0xa3f6df` |
| a 2-es mód magja **köbös B-spline** | `0xa40574[2] = 0xa3fb82`; `x ≥ 2 → 0`, `1 ≤ x < 2 → (2−x)³/6`, `0 ≤ x < 1 → (4−6x²+3x³)/6` |
| a szélesítő szorzó alapon 1,0, az `unsharp` **1,5**-öt ír bele | `0x00a3f553` `fld1` · `0x0090c4e2` |

⚠️ **Miért mos egyáltalán 1 : 1 arányban?** Mert a B-spline **nem
interpoláló**: `w(±1) = 1/6 ≠ 0`. Ugyanitt egy Lanczos-mag pontos másolatot
adna. Ez volt a hiányzó láncszem — a régi „doboz-átlag" olvasat téves volt (az
a piramis-felezés, ami 1 : 1-nél le sem fut).

## Amit ez a Gauss-közelítéshez képest változtat

A mag szórása **σ = 0,8684**, nem 1,0: a korábbi `GaussianBlur(σ=1,0)` egy
hajszállal túl erősen mosott, és a farka is más alakú volt. A #685 mérőszettje
szerint a Gauss-változat eltérése a Picasától már így is **0,47** (max
erősségen „JÓ" verdikt), tehát ez **finomítás, nem hibajavítás** — a
felhasználó a különbséget nem látja.

Az elfogadási feltétel ezért a **SÚLYOKRA** van kimondva, nem ΔE-re: a #685
mérőszett képei nincsenek a repóban, csak a verdikt-JSON, tehát a váltás
utólagos ΔE-újramérése új exportot igényelne.
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.curves import validate_image

_UNSHARP_AMOUNT_PER_STRENGTH = 1.21

#: A B-spline tartósugara a 2-es szűrőmódban (`0xa40550[2]`).
_BSPLINE_SUPPORT = 2.0

#: Az `unsharp` beégetett szélesítő szorzója (`0x0090c4e2`) — ettől lesz a
#: tényleges tartósugár 3 képpont.
_UNSHARP_KERNEL_SCALE = 1.5

#: A paraméter nélküli (v1) unsharp mért egyenértékese: unsharp2 s=0,6.
UNSHARP_V1_STRENGTH = 0.6

_KERNEL: np.ndarray | None = None


def _cubic_bspline(x: float) -> float:
    """A köbös B-spline súlyfüggvény, a MÉRT három szakasszal (`0xa3fb82`)."""
    x = abs(x)
    if x >= _BSPLINE_SUPPORT:
        return 0.0
    if x >= 1.0:
        return (2.0 - x) ** 3 / 6.0
    return (4.0 - 6.0 * x * x + 3.0 * x**3) / 6.0


def unsharp_blur_kernel() -> np.ndarray:
    """Az `unsharp` 1D elmosómagja, normálva (#762).

    A mag **szeparábilis** (előbb x, aztán y), és a szélessége a szélesített
    tartósugárból jön: `ceil(2,0 · 1,5) = 3` képpont mindkét irányban. A ±3-as
    csap értéke **pontosan 0** (`B₃(2) = 0`), tehát a mag valójában 5 csapos —
    a hetes szélesség a tartósugárból következik, nem többlet-elmosásból.

    A súlyok (a #762 mérése): `0 · 0,0328 · 0,2459 · 0,4426 · 0,2459 ·
    0,0328 · 0`.
    """
    global _KERNEL
    if _KERNEL is None:
        radius = int(np.ceil(_BSPLINE_SUPPORT * _UNSHARP_KERNEL_SCALE))
        raw = np.array(
            [
                _cubic_bspline(offset / _UNSHARP_KERNEL_SCALE)
                for offset in range(-radius, radius + 1)
            ],
            dtype=np.float32,
        )
        _KERNEL = (raw / raw.sum()).astype(np.float32)
    return _KERNEL


def unsharp_blur(image: np.ndarray) -> np.ndarray:
    """Az `unsharp` elmosása: szeparábilis köbös B-spline (#762)."""
    kernel = unsharp_blur_kernel()
    return cv2.sepFilter2D(image, cv2.CV_32F, kernel, kernel)


def apply_unsharp(
    image: np.ndarray, strength: float = UNSHARP_V1_STRENGTH
) -> np.ndarray:
    """Unsharp mask: `ki = be + 1,21·s·(be − bspline_blur(be))`, klippel."""
    validate_image(image)
    if strength < 0:
        raise ValueError(f"Az élesítés erőssége nem lehet negatív: {strength}")
    if strength == 0:
        return image.copy()
    blurred = unsharp_blur(image)
    amount = _UNSHARP_AMOUNT_PER_STRENGTH * strength
    # float32 munkatér (#140): a 8 bites kimenethez elegendő pontosság,
    # fele akkora memóriaforgalommal, mint a float64
    image_f = image.astype(np.float32)
    sharpened = image_f + np.float32(amount) * (image_f - blurred)
    return np.clip(np.rint(sharpened), 0, 255).astype(np.uint8)
