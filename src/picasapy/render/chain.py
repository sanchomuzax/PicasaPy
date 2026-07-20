"""A `filters=` lánc alkalmazása numpy képekre: `apply_filters` sorban futtatja
a támogatott műveleteket, a nem támogatottakat némán kihagyja (részleges
előnézet), de a kihagyott nevek listáját is visszaadja.
"""

from __future__ import annotations

import math

import numpy as np

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import decode_rect64
from picasapy.render.color import apply_bw, apply_saturation, apply_sepia, apply_warm
from picasapy.render.effects import (
    GLOW_V1_INTENSITY,
    GLOW_V1_RADIUS,
    apply_glow,
    apply_radblur,
    apply_radsat,
    apply_vignette,
)
from picasapy.render.ops import (
    apply_autocolor,
    apply_autolight,
    apply_crop,
    apply_enhance,
    apply_redeye,
    apply_tilt,
)
from picasapy.render.sharpen import UNSHARP_V1_STRENGTH, apply_unsharp
from picasapy.render.tinting import (
    apply_ansel,
    apply_dir_tint,
    apply_tint,
    parse_rgb_hex,
)
from picasapy.render.tone import apply_fill, apply_finetune2, parse_neutral_argb

# Megfejtve (golden 4. kör): a tilt szöge θ = p·0,2 radián (= p·11,459°).
_TILT_RADIANS_PER_UNIT = 0.2


def tilt_cover_scale(width: int, height: int, angle: float) -> float:
    """A forgatás utáni levágás elkerüléséhez szükséges minimális skála.

    `angle` radiánban. Az elforgatott téglalapot úgy skálázzuk, hogy a
    forgatott kép mindenütt lefedje az eredeti (width, height) vásznat:
    `s = max(cos|a| + (w/h)*sin|a|, cos|a| + (h/w)*sin|a|)`.
    (Fekvő képen ez a mérten igazolt `cos θ + (W/H)·sin θ` képlet.)
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
    angle = params[0] * _TILT_RADIANS_PER_UNIT
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


def _apply_fill_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    params = op.float_params()
    if not params:
        raise ValueError(f"A fill szűrőnek erősség-paraméter kell: {op}")
    return apply_fill(image, params[0])


def _apply_sat_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    params = op.float_params()
    if not params:
        raise ValueError(f"A sat szűrőnek erősség-paraméter kell: {op}")
    return apply_saturation(image, params[0])


def _apply_unsharp_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    params = op.float_params()
    strength = params[0] if params else UNSHARP_V1_STRENGTH
    return apply_unsharp(image, strength)


def _finetune_float(op: FilterOp, index: int) -> float:
    return float(op.params[index]) if len(op.params) > index else 0.0


def _apply_finetune_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    """finetune/finetune2 — a hiányzó paraméterek semlegesek.

    (A v1 p1/fill-je mérten azonos a v2-ével; a v1 színhő-skálája eltér,
    ott a v2 modellje közelítésként fut.)
    """
    neutral = parse_neutral_argb(op.params[4]) if len(op.params) > 4 else None
    return apply_finetune2(
        image,
        fill=_finetune_float(op, 1),
        highlights=_finetune_float(op, 2),
        shadows=_finetune_float(op, 3),
        neutral=neutral,
        temperature=_finetune_float(op, 5),
    )


def _effect_float(op: FilterOp, index: int, default: float) -> float:
    """A flag utáni `index`-edik paraméter számként, hiányzónál `default`."""
    params = op.float_params()
    return params[index] if len(params) > index else default


def _apply_vignette_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # Vignette=1,belső%,erősség,?,szín — a 3-4. paraméter szerepe méretlen
    return apply_vignette(
        image,
        inner=_effect_float(op, 0, 35.0),
        strength=_effect_float(op, 1, 1.4),
    )


def _apply_glow_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    # glow (v1) és glow2 azonos paraméter-alakkal: 1,intenzitás,sugár;
    # paraméter nélkül a v1 golden-kitben mért alapértékei futnak
    return apply_glow(
        image,
        intensity=_effect_float(op, 0, GLOW_V1_INTENSITY),
        radius=_effect_float(op, 1, GLOW_V1_RADIUS),
    )


def _apply_tint_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    if len(op.params) < 3:
        raise ValueError(f"A tint szűrőnek preserve+szín paraméter kell: {op}")
    return apply_tint(
        image, preserve=float(op.params[1]), color=parse_rgb_hex(op.params[2])
    )


def _apply_ansel_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    if len(op.params) < 2:
        raise ValueError(f"Az ansel szűrőnek színparaméter kell: {op}")
    return apply_ansel(image, color=parse_rgb_hex(op.params[1]))


def _apply_radblur_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    return apply_radblur(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        size=_effect_float(op, 2, 0.0),
        amount=_effect_float(op, 3, 0.0),
    )


def _apply_radsat_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    return apply_radsat(
        image,
        x=_effect_float(op, 0, 0.5),
        y=_effect_float(op, 1, 0.5),
        radius=_effect_float(op, 2, 0.5),
        sharpness=_effect_float(op, 3, 0.5),
    )


def _apply_dir_tint_op(image: np.ndarray, op: FilterOp) -> np.ndarray:
    if len(op.params) < 6:
        raise ValueError(f"A dir_tint szűrőnek 5 paraméter kell: {op}")
    return apply_dir_tint(
        image,
        x=float(op.params[1]),
        y=float(op.params[2]),
        gradient=float(op.params[3]),
        shade=float(op.params[4]),
        color=parse_rgb_hex(op.params[5]),
    )


# A grain2-nek SZÁNDÉKOSAN nincs handlere (#149): a filmszemcse véletlen
# maggal fut, pixelhűen nem reprodukálható (csak statisztikailag, ld.
# docs/specs/filters-decoded.md) — a lánc kihagyja, a round-trip őrzi.
_HANDLERS = {
    "tilt": _apply_tilt_op,
    "redeye": lambda image, op: apply_redeye(image),
    "enhance": lambda image, op: apply_enhance(image),
    "autolight": lambda image, op: apply_autolight(image),
    "autocolor": lambda image, op: apply_autocolor(image),
    "fill": _apply_fill_op,
    "finetune": _apply_finetune_op,
    "finetune2": _apply_finetune_op,
    "bw": lambda image, op: apply_bw(image),
    "sepia": lambda image, op: apply_sepia(image),
    "warm": lambda image, op: apply_warm(image),
    "sat": _apply_sat_op,
    "unsharp": _apply_unsharp_op,
    "unsharp2": _apply_unsharp_op,
    "vignette": _apply_vignette_op,  # az ini-ben nagybetűs: Vignette
    "glow": _apply_glow_op,
    "glow2": _apply_glow_op,
    "tint": _apply_tint_op,
    "ansel": _apply_ansel_op,
    "radblur": _apply_radblur_op,
    "radsat": _apply_radsat_op,
    "dir_tint": _apply_dir_tint_op,
}


def apply_filters(
    image: np.ndarray, ops: tuple[FilterOp, ...]
) -> tuple[np.ndarray, tuple[str, ...]]:
    """Sorban alkalmazza a támogatott szűrőket (crop64, tilt, redeye, enhance,
    autolight, autocolor, fill, finetune/finetune2, bw, sepia, warm, sat,
    unsharp/unsharp2, Vignette, glow/glow2, tint, ansel, radblur, radsat,
    dir_tint).

    A `grain2` szándékosan NEM támogatott (#149): véletlen magos filmszemcse,
    pixelhűen nem reprodukálható — kihagyottként jelezzük, a round-trip őrzi.

    A nem támogatott szűrőket szándékosan némán kihagyja (részleges
    előnézet), de a kihagyott nevek sorrendhelyes listáját is visszaadja:
    `(kép, kihagyott_nevek)`.

    A `crop64` a láncban csak szerkesztési TÖRTÉNET — önmagában NEM vág
    (spec: `docs/specs/filters-decoded.md`). A tényleges vágást a képszekció
    külön `crop=` kulcsa adja, ami a lánc EFFEKTÍV (utolsó) crop64-ével egyezik.
    Ezt egyetlenegyszer, a teljes képre futó effektusok UTÁN alkalmazzuk, az
    EREDETI képméretre vonatkozó koordinátákkal (a tilt méret-tartó). Így a
    több crop64-et tartalmazó valódi Picasa-láncok sem kaszkádolnak (#130).
    """
    result = image
    skipped: list[str] = []
    crop_op: FilterOp | None = None
    for op in ops:
        if op.name.casefold() == "crop64":
            crop_op = op  # csak az effektív (utolsó) crop64 számít
            continue
        handler = _HANDLERS.get(op.name.casefold())
        if handler is None:
            skipped.append(op.name)
            continue
        result = handler(result, op)
    if crop_op is not None:
        result = _apply_crop_op(result, crop_op)
    return result, tuple(skipped)
