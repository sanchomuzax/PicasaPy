"""`glimmer::EdgeDetectionBImageOperation` — a Picasa élkiemelő ÖSSZETETT
művelete (#878, #3812).

A `filterdesc.xml` egyetlen attribútumot ad neki (`detail="50"`), a tényleges
csővezetéket a natív kód építi fel **kódban**: az osztály a
`NestedImageOperation`-ből származik, és az 1. slotja (`0x00bbca60`) ebben a
sorrendben fűzi össze a gyerekeit (dekompilátum:
`referencia/dekompilalt-pakolo/script-DecompileEdge.log`, 3321. sortól):

| # | natív hívás | mit épít |
|---|---|---|
| 1 | `FUN_00bb4c40(2.0f, 2.0f, 2)` | `BlurImageOperation(xblur=2, yblur=2, quality=2)` |
| 2 | `FUN_00bb6150()` → `+0x34` | `SimpleColorMatrixImageOperation` — ide megy a `100 − detail` |
| 3 | `FUN_00bc25d0("edgedetectimgop_orig")` | `SetVar` — a köztes kép elmentése |
| 4 | `FUN_00bb6560(0)` | `EdgeDetectionSobelImageOperation(0)` — függőleges élek |
| 5 | `FUN_00bb9990(…)` | `AdjustCurves` `{(0,0), (128,255), (255,0)}` |
| 6 | `FUN_00bc25d0("horizontal")` | `SetVar` — az első irány elmentése |
| 7 | `FUN_00bbf740("edgedetectimgop_orig")` | `GetVar` — vissza az elmentett képre |
| 8 | `FUN_00bb6560(1)` | `EdgeDetectionSobel` — vízszintes élek |
| 9 | `FUN_00bb9990(…)` | ugyanaz a görbe |
| 10 | `FUN_00bbf780("horizontal")` | `GetVar` **keverési móddal** — a két irány egyesítése |

A `detail` csúszkát a 6. slot (`0x00bbcdd0`) `100 − detail` alakban teszi a
2. lépés mátrixába.

**A háromszög-görbe a kulcs.** A Sobel kimenete 128 körül van középre
tolva; a `{(0,0), (128,255), (255,0)}` görbe ezt |eltérés|-re fordítja, és
mivel a 128-at 255-re viszi, a **sík felületekből FEHÉR** lesz, az erős
élekből fekete. Az `EdgeDetectionB` tehát fehér alapon sötét vonalas rajzot
ad — a Neon ezt keveri önmagával, invertálja, és színezi.

## A binárisból kiolvasott tényezők (#3812)

Spec: `docs/specs/filterdesc-registry.md`, 4.11, „EdgeDetectionB — a
»mérésből illesztett« tényezők a binárisból”.

- **Az 1. lépés elmosása** a natív `BlurImageOperation(2, 2, quality = 2)`
  (`0x00bbcaa5`): `nativ_blur.blur_image_operation`.
- **A Sobel egy csatornára** (`0x00bb6620`, skalár ág `0x00bb7140`):
  `clamp((512 + Σ kᵢ·pᵢ) idiv 4, 0, 255)` = `clamp(128 + floor(Σ/4))`, egész
  aritmetikával; az osztó `0x00bb6895` (`push 4`), a 512-es kezdőérték
  `0x00bb6faa`. A perem ismétlődik.
- **A `100 − detail` helye** a gyerek `SimpleColorMatrix` **kontrasztja**
  (`+0x30`, `0x00bbce24`).
- **A 10. lépés keverési módja** 5 = Multiply (`0x00bbcd76`).

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3), tiszta függvény.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import (
    adjust_curves,
    apply_blend_mode,
    simple_color_matrix,
    to_float,
    to_uint8,
)
from picasapy.render.nativ_blur import blur_image_operation

#: A natív `EdgeDetectionSobel` 6. slotja (`0x00bb6620`) két 3×3 magot
#: választ — a klasszikus Sobel KÉTSZERES súlyokkal (±2/±4 a ±1/±2 helyett).
_SOBEL_VERTICAL = np.array([[-2, 0, 2], [-4, 0, 4], [-2, 0, 2]], dtype=np.int32)
_SOBEL_HORIZONTAL = np.array([[2, 4, 2], [0, 0, 0], [-2, -4, -2]], dtype=np.int32)

#: `BlurImageOperation(xblur=2, yblur=2, quality=2)` — `0x00bbcaa5`.
_BLUR_RADIUS = 2.0
_BLUR_QUALITY = 2

#: A Sobel-akkumulátor kezdőértéke (`0x00bb6faa`) és osztója (`0x00bb6895`):
#: `(512 + Σ) idiv 4` = `128 + floor(Σ/4)`.
_SOBEL_BIAS = 512
_SOBEL_DIVISOR = 4

#: A natív keverési mód sorszáma a 10. lépésben: 5 = Multiply (`0x00bbcd76`).
_MULTIPLY = 5

#: A két irány közös görbéje — a natív a MasterCurve-öt szó szerint
#: `"{[{x:0, y:0}, {x:128, y:255}, {x:255, y:0}]}"` sztringként adja át.
_EDGE_CURVE = ((0.0, 0.0), (128.0, 255.0), (255.0, 0.0))


def _sobel_direction(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Egy irány natív Sobel-válasza `uint8` képen, egész aritmetikával.

    `clamp((512 + Σ kᵢ·pᵢ) idiv 4, 0, 255)`, a peremen ismétlődő képponttal.
    A jobb felső sarok a natív, irányspecifikus szomszédtáblát követi.
    Nemnegatív osztandónál az `idiv` csonkolása egyezik a `floor`-ral, a
    negatív osztandó pedig mindkét úton 0-ra vágódik — ezért `//` elég.
    """
    height, width = image.shape[:2]
    if width < 3 or height < 3:
        # A natív függvények ilyen méretnél még a képpontfeldolgozás előtt visszatérnek.
        return image.copy()

    pixels = image.astype(np.int32)
    padded = np.pad(pixels, ((1, 1), (1, 1), (0, 0)), mode="edge")
    total = np.full(image.shape, _SOBEL_BIAS, dtype=np.int32)
    for dy in range(3):
        for dx in range(3):
            weight = int(kernel[dy, dx])
            if weight:
                total += weight * padded[dy : dy + height, dx : dx + width]

    if np.array_equal(kernel, _SOBEL_VERTICAL):
        total[0, -1] = (
            _SOBEL_BIAS
            + 4 * pixels[1, -2]
            - 2 * pixels[1, -1]
            - 2 * pixels[0, -1]
        )
    elif np.array_equal(kernel, _SOBEL_HORIZONTAL):
        total[0, -1] = (
            _SOBEL_BIAS
            + 4 * pixels[0, -2]
            + 2 * pixels[0, -1]
            - 6 * pixels[1, -1]
        )

    return np.clip(total // _SOBEL_DIVISOR, 0, 255).astype(np.uint8)


def edge_detection_b(image: np.ndarray, detail: float = 50.0) -> np.ndarray:
    """`EdgeDetectionB(detail=…)` — fehér alapon sötét vonalas élrajz.

    A `detail` `[0..100]`; a natív a `100 − detail` értéket teszi az
    előkészítő `SimpleColorMatrix` kontrasztjába, tehát a NAGYOBB `detail`
    KISEBB előkontrasztot (több megmaradó finom élt) jelent.
    """
    validate_image(image)
    if not 0.0 <= detail <= 100.0:
        raise ValueError(f"A detail 0..100 tartományba kell essen: {detail}")

    blurred = blur_image_operation(image, _BLUR_RADIUS, _BLUR_RADIUS, quality=_BLUR_QUALITY)
    prepared = simple_color_matrix(blurred, contrast=100.0 - detail)

    vertical = to_float(
        adjust_curves(_sobel_direction(prepared, _SOBEL_VERTICAL), master=_EDGE_CURVE)
    )
    horizontal = to_float(
        adjust_curves(_sobel_direction(prepared, _SOBEL_HORIZONTAL), master=_EDGE_CURVE)
    )
    return to_uint8(apply_blend_mode(horizontal, vertical, _MULTIPLY, 1.0))


__all__ = ["edge_detection_b"]
