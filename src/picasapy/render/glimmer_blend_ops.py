"""Görbe-, keverési és elmosási primitívek a Glimmer-láncokhoz."""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.curves import (
    CurvePoints,
    apply_byte_luts,
    evaluate_curve_extrapolated,
    validate_image,
)


_REC601_WEIGHTS = (0.299, 0.587, 0.114)


#: Keverési mód neve (`_BLEND_FUNCS` kulcsa); az `apply_blend_mode` a natív
#: sorszámot (`BLEND_MODE_BY_INDEX`) is elfogadja.
BlendMode = str



def to_uint8(values: np.ndarray) -> np.ndarray:
    """Float tömb uint8-ra kerekítve/vágva — a modul közös kimenet-konverziója."""
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)



def to_float(image: np.ndarray) -> np.ndarray:
    """`uint8` kép float32 másolata (a pipeline belső munkaformátuma)."""
    return image.astype(np.float32)



def luma(image_f: np.ndarray) -> np.ndarray:
    """Rec.601 luminancia (H, W) float32 tömbként, float32 RGB bemenetből."""
    red_w, green_w, blue_w = _REC601_WEIGHTS
    return (
        np.float32(red_w) * image_f[..., 0]
        + np.float32(green_w) * image_f[..., 1]
        + np.float32(blue_w) * image_f[..., 2]
    )



def fade_alpha(fade: float) -> float:
    """A közös Fade-szabály: `BlendAlpha = 1 − Fade/100`, `[0..1]`-re vágva.

    Minden Glimmer-effekt záró keverése ezt használja (issue #381,
    „Egységes szabályok" 1. pont) — a `Fade` csúszka mindenütt `[0..100]`.
    """
    return float(np.clip(1.0 - fade / 100.0, 0.0, 1.0))



def _float_bitek(value: float) -> int:
    return int(np.array(value, dtype=np.float32).view(np.int32))



def _kozel(alpha: float, cel: float) -> bool:
    """A natív „≈": a float32 BITMINTÁJÁN `< 8` eltérés (`0x00bd0700`, #3442)."""
    return abs(_float_bitek(alpha) - _float_bitek(cel)) < 8



def _bajt(values: np.ndarray) -> np.ndarray:
    """A keverés bemenete bájtként (int32-ben, hogy a szorzatok ne csorduljanak)
    — a natív lánc minden utasítás után 8 bites képet ad át."""
    return np.clip(np.rint(values), 0, 255).astype(np.int32)



def alpha_blend(base: np.ndarray, top: np.ndarray, alpha: float) -> np.ndarray:
    """Átlátszóság-keverés a natív EGÉSZ képlettel (`0x009dc4b0`, #3442).

    `α` `[0, 1]`-re vágva; `α ≈ 1` → `top` változatlanul, `α ≈ 0` → `base`
    (a végrehajtó `0x00bd0700` ekkor a keverőt meg sem hívja). Különben
    `w = trunc(256α)`, és ha `w > 0`, `w − 1`; az SIMD-párok képlete
    `ki = (b·(255−w) + t·w) >> 8`. Páratlan szélességnél minden sor utolsó
    pixele a natív skalárképletet kapja: `t + ((b−t)·w >> 8)`.
    A bemenetek float32 `[0,255]` tömbök (bájtra kerekítve), a kimenet
    float32.
    """
    alpha = float(np.clip(alpha, 0.0, 1.0))
    if _kozel(alpha, 1.0):
        return top.astype(np.float32)
    if _kozel(alpha, 0.0):
        return base.astype(np.float32)
    w = int(np.float32(alpha) * np.float32(256.0))
    if w > 0:
        w -= 1
    base_bajt = _bajt(base)
    top_bajt = _bajt(top)
    kevert = (base_bajt * (255 - w) + top_bajt * w) >> 8
    if base.ndim >= 2 and base.shape[1] % 2:
        kevert[:, -1, ...] = top_bajt[:, -1, ...] + (
            (base_bajt[:, -1, ...] - top_bajt[:, -1, ...]) * w >> 8
        )
    return kevert.astype(np.float32)



# --- Görbék -----------------------------------------------------------------


def adjust_curves(
    image: np.ndarray,
    master: CurvePoints | None = None,
    red: CurvePoints | None = None,
    green: CurvePoints | None = None,
    blue: CurvePoints | None = None,
) -> np.ndarray:
    """`AdjustCurves`: opcionális mestergörbe MINDEN csatornára, utána
    opcionális, csatornánként ELTÉRŐ görbe — a `filterdesc.xml` sorrendje
    szerint (master előbb, csak utána a csatorna-specifikus finomítás).

    **#3942: a natív a 256 bemenetre EGY menetben számol** (a LUT-építő
    `0x00bcd1e0`), nem két egymást követő 8 bites LUT-tal:

        v   = f32( Master(i) )                       ; NINCS kerekítés, NINCS vágás
        C_i = clamp( trunc( Csatorna(v) + 0,5 ), 0, 255 )  ; C = R, G, B

    A mestergörbe kimenete (`v`) a saját töréspontjain túl EXTRAPOLÁL
    (`evaluate_curve_extrapolated`), és FOLYTONOSAN (kerekítés/vágás
    nélkül) adódik át a csatornagörbének — ami emiatt a 0..255-ön KÍVÜL eső
    bemenetet is kaphat, és ott is extrapolál, nem a szélső értéket tartja.
    Hiányzó görbe = identitás. A végén EGYETLEN kerekítés és vágás történik.
    """
    validate_image(image)
    levels = np.arange(256, dtype=np.float64)
    master_out = evaluate_curve_extrapolated(master, levels) if master is not None else levels
    # A spec `v = f32(Master(i))` lépése (`0x00bcd226` → `0x00bcd360`). Egyik mai
    # hívó görbéjén sem ad eltérő táblaelemet, ezért teszt nem fogja meg.
    master_out = master_out.astype(np.float32).astype(np.float64)

    def _channel_table(curve: CurvePoints | None) -> np.ndarray:
        values = evaluate_curve_extrapolated(curve, master_out) if curve is not None else master_out
        return np.clip(np.trunc(values + 0.5), 0, 255).astype(np.uint8)

    tables = np.stack(
        [_channel_table(red), _channel_table(green), _channel_table(blue)], axis=-1
    )
    return apply_byte_luts(image, tables)



def invert_curve(image: np.ndarray) -> np.ndarray:
    """`Invert`: az egyetlen mestergörbe `(0,255) → (255,0)` — pontos művelet."""
    validate_image(image)
    return adjust_curves(image, master=((0.0, 255.0), (255.0, 0.0)))



# --- Keverési módok -----------------------------------------------------
#
# Mind a tizenegy kernel a natív EGÉSZ képlete (spec „A `BlendInstruction`"
# C, #3442): `b`, `t` int32 bájtok (0–255), a `÷255` CSONKOLÓ.


def _blend_multiply(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    return b * t // 255



def _blend_screen(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    return (65025 - (255 - b) * (255 - t)) // 255



def _overlay_alap(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    # `0x008f53f0`: `x ≤ 127` → `⌊2xy/255⌋`; `x = y = 255` → 255 (külön ág);
    # különben `⌊(65024 − 2(255−x)(255−y))/255⌋`
    also = 2 * x * y // 255
    felso = (65024 - 2 * (255 - x) * (255 - y)) // 255
    felso = np.where((x == 255) & (y == 255), 255, felso)
    return np.where(x <= 127, also, felso)



def _blend_overlay(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    return _overlay_alap(b, t)



def _blend_darken(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    return np.minimum(b, t)



def _blend_lighten(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    return np.maximum(b, t)



def _blend_add(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    return np.minimum(b + t, 255)



def _blend_difference(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    # `|b − t|` — két `psubusb` + `por` (`0x008f42d0`, #3443)
    return np.abs(b - t)



def _blend_subtract(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    # `max(b − t, 0)` — az ALSÓBÓL vonja ki a felsőt (`psubusb`, `0x008f46c0`)
    return np.maximum(b - t, 0)



def _blend_hardlight(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    # az Overlay CSERÉLT argumentummal (a tábla-építő `0x008f6568`, #3443)
    return _overlay_alap(t, b)



def _blend_softlight(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    # `0x008f6620`: a döntő operandus a FELSŐ, és az alsó legalsó bitje
    # eldobódik (`and al, 0xfe`, `0x008f6642`)
    bv = b & 0xFE
    also = t * (bv + 128) // 255
    felso = (65025 - (382 - bv) * (255 - t)) // 255
    return np.where(t < 128, also, felso)



def _blend_normal(b: np.ndarray, t: np.ndarray) -> np.ndarray:
    # a felső elem saját alfájával kompozitál — RGB-ben az alfa 255, tehát `t`
    del b
    return t



_BLEND_FUNCS = {
    "normal": _blend_normal,
    "multiply": _blend_multiply,
    "screen": _blend_screen,
    "overlay": _blend_overlay,
    "darken": _blend_darken,
    "lighten": _blend_lighten,
    "add": _blend_add,
    "difference": _blend_difference,
    "subtract": _blend_subtract,
    "hardlight": _blend_hardlight,
    "softlight": _blend_softlight,
}


#: A natív módtábla (`0x00cf0e98`) sorszám → mód. A csúszkák és a
#: `BlendMode="{…}"` kifejezések EZT a sorszámot adják át (#3443, #3442).
BLEND_MODE_BY_INDEX: dict[int, str] = {
    0: "add",
    1: "darken",
    2: "difference",
    3: "hardlight",
    4: "lighten",
    5: "multiply",
    6: "overlay",
    7: "screen",
    8: "subtract",
    9: "normal",
    10: "softlight",
}



def apply_blend_mode(
    base: np.ndarray, top: np.ndarray, mode: BlendMode | int, opacity: float = 1.0
) -> np.ndarray:
    """`base` (alsó) és `top` (felső) float32 `[0,255]` rétegek keveréke a
    `mode` móddal — névvel vagy a natív SORSZÁMMAL (`BLEND_MODE_BY_INDEX`)
    —, utána `opacity` (`BlendAlpha`) szerinti átlátszóság-keverés az
    `alpha_blend` egész képletével. A kettő azonos alakú kell legyen.

    A végrehajtó (`0x00bd0700`, #3442) menete: `α` `[0,1]`-re vágva;
    `normal` és `α ≈ 1` → `top` változatlanul; `α ≈ 0` → `base`; különben
    a mód egész kernele a bájtra kerekített rétegeken, és ha `α` nem ≈ 1,
    az átlátszóság-keverés. A kimenet float32.
    """
    if isinstance(mode, (int, np.integer)) and not isinstance(mode, bool):
        name = BLEND_MODE_BY_INDEX.get(int(mode))
        if name is None:
            raise ValueError(f"Ismeretlen blend-mód sorszám: {mode!r}")
        mode = name
    if mode not in _BLEND_FUNCS:
        raise ValueError(f"Ismeretlen blend-mód: {mode!r}")
    opacity = float(np.clip(opacity, 0.0, 1.0))
    if mode == "normal" and _kozel(opacity, 1.0):
        return top.astype(np.float32)
    if _kozel(opacity, 0.0):
        return base.astype(np.float32)
    blended = _BLEND_FUNCS[mode](_bajt(base), _bajt(top)).astype(np.float32)
    return alpha_blend(base, blended, opacity)



def masked_blend(base: np.ndarray, overlay: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Maszkolt keverés a natív EGÉSZ képlettel (`0x008f62a0` →
    `0x008f4810`/`0x008f49a0`, #3442): `⌊(t·m + b·(255 − m)) / 255⌋`.

    `mask` (H, W): `uint8` maszk-bájt (0–255), vagy float `[0,1]` súly —
    ez utóbbi `rint(255·mask)`-kal bájtra kerekítve. `base`/`overlay`
    float32 `[0,255]` (bájtra kerekítve); a kimenet float32.
    """
    mask = np.asarray(mask)
    if mask.dtype == np.uint8:
        m = mask.astype(np.int32)
    else:
        m = np.clip(np.rint(mask.astype(np.float32) * np.float32(255.0)), 0, 255).astype(np.int32)
    m = m[..., np.newaxis]
    kevert = (_bajt(overlay) * m + _bajt(base) * (255 - m)) // 255
    return kevert.astype(np.float32)



# --- Elmosás / AutoFix / SimpleColorMatrix -----------------------------


def gaussian_blur_f(image_f: np.ndarray, xblur: float, yblur: float | None = None) -> np.ndarray:
    """Gauss-elmosás float32 rétegen, `xblur`/`yblur` szigmával (`Blur`
    lépés — a Picasa a σ-t közvetlenül a csúszkából vezényli le,
    ld. az effektenkénti képleteket).
    """
    sigma_x = max(float(xblur), 1e-6)
    sigma_y = max(float(yblur if yblur is not None else xblur), 1e-6)
    return cv2.GaussianBlur(image_f, (0, 0), sigmaX=sigma_x, sigmaY=sigma_y)
