"""A `filters=` lánc alkalmazása numpy képekre: `apply_filters` sorban futtatja
a támogatott műveleteket, a nem támogatottakat némán kihagyja (részleges
előnézet), de a kihagyott nevek listáját is visszaadja.
"""

from __future__ import annotations

import math

import numpy as np

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import decode_rect64
from picasapy.render.ops import (
    apply_autocolor,
    apply_autolight,
    apply_crop,
    apply_enhance,
    apply_redeye,
    apply_tilt,
)

# Picasa nyers tilt-paraméter → fok közelítő átváltása (empirikus, nem publikus
# spec alapján; ld. docs/specs/picasa-ini-format.md).
_TILT_DEGREES_PER_UNIT = 11.5

_CROP_NAMES = ("crop64",)
_REDEYE_NAMES = ("redeye",)
_ENHANCE_NAMES = ("enhance",)
_AUTOLIGHT_NAMES = ("autolight",)
_AUTOCOLOR_NAMES = ("autocolor",)
_TILT_NAMES = ("tilt",)


def tilt_cover_scale(width: int, height: int, angle: float) -> float:
    """A forgatás utáni levágás elkerüléséhez szükséges minimális skála.

    `angle` radiánban. Az elforgatott téglalapot úgy skálázzuk, hogy a
    forgatott kép mindenütt lefedje az eredeti (width, height) vásznat:
    `s = max(cos|a| + (w/h)*sin|a|, cos|a| + (h/w)*sin|a|)`.
    """
    if width <= 0 or height <= 0:
        raise ValueError(f"A méretek pozitívak kell legyenek: {width}x{height}")
    cos_a = abs(math.cos(angle))
    sin_a = abs(math.sin(angle))
    width_ratio = width / height
    height_ratio = height / width
    return max(cos_a + width_ratio * sin_a, cos_a + height_ratio * sin_a)


def _apply_tilt_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    params = op.float_params()
    if not params:
        raise ValueError(f"A tilt szűrőnek legalább egy paramétere kell legyen: {op}")
    angle = math.radians(params[0] * _TILT_DEGREES_PER_UNIT)
    if len(params) >= 2 and params[1] > 0:
        scale = params[1]
    else:
        # A Picasa 3.x a skála-mezőbe jellemzően 0.000000-t ír (#73): a 0
        # vagy hiányzó érték jelentése „számold ki a kitöltő skálát".
        height, width = image.shape[:2]
        scale = tilt_cover_scale(width, height, angle)
    return apply_tilt(image, angle=angle, scale=scale)


def _apply_crop_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    if len(op.params) < 2:
        raise ValueError(f"A crop64 szűrőnek rect64 paraméter kell: {op}")
    rect = decode_rect64(op.params[1])
    return apply_crop(image, rect)


_HANDLERS = {
    **{name: _apply_crop_op for name in _CROP_NAMES},
    **{name: _apply_tilt_op for name in _TILT_NAMES},
    **{name: (lambda image, op: apply_redeye(image)) for name in _REDEYE_NAMES},
    **{name: (lambda image, op: apply_enhance(image)) for name in _ENHANCE_NAMES},
    **{name: (lambda image, op: apply_autolight(image)) for name in _AUTOLIGHT_NAMES},
    **{name: (lambda image, op: apply_autocolor(image)) for name in _AUTOCOLOR_NAMES},
}


def apply_filters(
    image: np.ndarray, ops: tuple[FilterOp, ...]
) -> tuple[np.ndarray, tuple[str, ...]]:
    """Sorban alkalmazza a támogatott szűrőket (crop64, tilt, redeye, enhance,
    autolight, autocolor).

    A nem támogatott szűrőket szándékosan némán kihagyja (részleges
    előnézet), de a kihagyott nevek sorrendhelyes listáját is visszaadja:
    `(kép, kihagyott_nevek)`.
    """
    result = image
    skipped: list[str] = []
    for op in ops:
        handler = _HANDLERS.get(op.name.casefold())
        if handler is None:
            skipped.append(op.name)
            continue
        result = handler(result, op)
    return result, tuple(skipped)
