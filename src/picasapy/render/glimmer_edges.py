"""`glimmer::EdgeDetectionBImageOperation` — a Picasa élkiemelő ÖSSZETETT
művelete (#878).

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

## Ami MÉRÉSBŐL való (a binárisból nem derül ki)

- **A Sobel-kimenet skálája** (`_SOBEL_SCALE`): a natív konvolúció a 128-as
  eltolás előtti osztóját a dekompilátum nem őrizte meg. A #685 mérőszettje
  `neon__alap.jpg` golden párján illesztve.
- **A 10. lépés keverési módja**: a `BlendImageOperation` alapja a móddal
  együtt regiszterben érkezik. A `multiply` és a `darken` a mérésen egyaránt
  illeszkedik (a különbségük a fehér alapon elhanyagolható); `multiply`-t
  használunk.
- **A 2. lépés melyik `SimpleColorMatrix` paramétere** — a kontraszt
  illeszkedett a legjobban.

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3), tiszta függvény.
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import (
    adjust_curves,
    apply_blend_mode,
    simple_color_matrix,
    to_float,
    to_uint8,
)

#: A natív `EdgeDetectionSobel` 6. slotja (`0x00bb6620`) két 3×3 magot
#: választ — a klasszikus Sobel KÉTSZERES súlyokkal (±2/±4 a ±1/±2 helyett).
_SOBEL_VERTICAL = np.array(
    [[-2.0, 0.0, 2.0], [-4.0, 0.0, 4.0], [-2.0, 0.0, 2.0]], dtype=np.float32
)
_SOBEL_HORIZONTAL = np.array(
    [[2.0, 4.0, 2.0], [0.0, 0.0, 0.0], [-2.0, -4.0, -2.0]], dtype=np.float32
)

#: `BlurImageOperation(xblur=2, yblur=2, quality=2)`: a Flash-örökségű
#: elmosás `quality` menetben futtat egy `xblur` széles dobozszűrőt. Két
#: menet egy 2 képpont széles dobozból pontosan a `[1,2,1]/4` háromszög-mag
#: (a `BitmapFilterQuality` Flash-konstansról ld. `filterdesc-registry.md` 4.5).
_BLUR_KERNEL = np.array([1.0, 2.0, 1.0], dtype=np.float32) / np.float32(4.0)

#: A Sobel-kimenet 128 köré tolása előtti osztó — MÉRT skalár (ld. a
#: modul-docstring „Ami mérésből való" szakaszát).
_SOBEL_SCALE = np.float32(4.0)

#: A két irány közös görbéje — a natív a MasterCurve-öt szó szerint
#: `"{[{x:0, y:0}, {x:128, y:255}, {x:255, y:0}]}"` sztringként adja át.
_EDGE_CURVE = ((0.0, 0.0), (128.0, 255.0), (255.0, 0.0))


def _sobel_direction(image_f: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Egy irány Sobel-válasza, 128 köré tolva és `[0,255]`-re vágva."""
    response = cv2.filter2D(image_f, -1, kernel, borderType=cv2.BORDER_REPLICATE)
    return np.clip(np.float32(128.0) + response / _SOBEL_SCALE, 0.0, 255.0)


def edge_detection_b(image: np.ndarray, detail: float = 50.0) -> np.ndarray:
    """`EdgeDetectionB(detail=…)` — fehér alapon sötét vonalas élrajz.

    A `detail` `[0..100]`; a natív a `100 − detail` értéket teszi az
    előkészítő `SimpleColorMatrix` kontrasztjába, tehát a NAGYOBB `detail`
    KISEBB előkontrasztot (több megmaradó finom élt) jelent.
    """
    validate_image(image)
    if not 0.0 <= detail <= 100.0:
        raise ValueError(f"A detail 0..100 tartományba kell essen: {detail}")

    blurred = cv2.sepFilter2D(
        to_float(image), -1, _BLUR_KERNEL, _BLUR_KERNEL, borderType=cv2.BORDER_REPLICATE
    )
    prepared = to_float(simple_color_matrix(to_uint8(blurred), contrast=100.0 - detail))

    vertical = to_float(
        adjust_curves(to_uint8(_sobel_direction(prepared, _SOBEL_VERTICAL)), master=_EDGE_CURVE)
    )
    horizontal = to_float(
        adjust_curves(to_uint8(_sobel_direction(prepared, _SOBEL_HORIZONTAL)), master=_EDGE_CURVE)
    )
    return to_uint8(apply_blend_mode(horizontal, vertical, "multiply", 1.0))


__all__ = ["edge_detection_b"]
