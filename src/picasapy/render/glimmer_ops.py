"""Közös primitívek a Glimmer-effektek EGZAKT csővezetékeihez (#381).

A `research/copy_Picasa_3_7/Picasa3/runtime/filterdesc.xml` (feldolgozva:
`docs/specs/filterdesc-registry.md` 4. fejezet) a 33 „Glimmer" (Picnik-
örökös) effektet egy kis képfeldolgozó-nyelv műveleteivel írja le: görbék
(`AdjustCurves`), keverési módok (`BlendMode`), belső ragyogás
(`GlowImageOperation innerglow`), zaj (`Noise`), gradiens-leképezés
(`GradientMap`/`HSVGradientMap`), körkörös maszk stb. Ez a modul ezeket az
ALAPMŰVELETEKET adja, hogy az egyes effekt-modulok (`glimmer_tone.py`,
`glimmer_creative.py`, `glimmer_frames.py`, `glimmer_focal.py`) csak a
csővezeték ÖSSZERAKÁSÁÉRT feleljenek, ne a primitívekért.

**Őszinteség:** a `filterdesc.xml` a MŰVELETEK NEVÉT, SORRENDJÉT és a
PARAMÉTER-KÉPLETEKET adja meg egzaktul (ez itt bitre követve van) — a
Picasa C++ motorjának BELSŐ KERNELJE (pl. pontosan hogyan számol a
`GlowImageOperation` vagy a `Noise` a képpontszinten) nem publikus
forráskód, ezért az alant definiált primitívek a szokásos, jól bevált
képfeldolgozási megfelelőjükkel (Gauss-elmosás, LERP-interpoláció, uniform
zaj) vannak implementálva. Ez ALAPVETŐEN más jellegű, mint a korábbi
`effects_creative*.py` modulok „a hatás jellegét idézzük" közelítése: itt a
LÉPÉSSORREND és minden SZÁMÉRTÉK (görbe-kontrollpont, csúszkatartomány,
blend-mód, Fade-képlet) bitre a `filterdesc.xml`-ből jön.

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3), kivéve, ahol a
függvény kifejezetten float32-t dolgoz fel (jelölve). Minden függvény
TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.render.curves import (
    CurvePoints,
    apply_channel_luts,
    apply_lut,
    curve_lut,
    lut_ramp,
    validate_image,
)

_REC601_WEIGHTS = (0.299, 0.587, 0.114)

#: Blend-módok neve → függvény (`base`, `top` float32 [0,255] tömbök,
#: azonos alakúak) → keverendő rétegérték (a `BlendAlpha`/`strength`
#: szerinti súlyozást a hívó végzi, ld. `apply_blend_mode`).
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


def alpha_blend(base: np.ndarray, top: np.ndarray, alpha: float) -> np.ndarray:
    """Lineáris keverés: `base + alpha·(top − base)`, float32 tömbökön."""
    return base + np.float32(alpha) * (top - base)


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
    """
    validate_image(image)
    result = image
    if master is not None:
        result = apply_lut(result, curve_lut(master))
    if red is not None or green is not None or blue is not None:
        ramp = lut_ramp()
        luts = (
            curve_lut(red) if red is not None else ramp,
            curve_lut(green) if green is not None else ramp,
            curve_lut(blue) if blue is not None else ramp,
        )
        result = apply_channel_luts(result, luts)
    return result


def invert_curve(image: np.ndarray) -> np.ndarray:
    """`Invert`: az egyetlen mestergörbe `(0,255) → (255,0)` — pontos művelet."""
    validate_image(image)
    return adjust_curves(image, master=((0.0, 255.0), (255.0, 0.0)))


# --- Keverési módok -----------------------------------------------------


def _blend_multiply(base: np.ndarray, top: np.ndarray) -> np.ndarray:
    return base * top / np.float32(255.0)


def _blend_screen(base: np.ndarray, top: np.ndarray) -> np.ndarray:
    return np.float32(255.0) - (np.float32(255.0) - base) * (np.float32(255.0) - top) / np.float32(
        255.0
    )


def _blend_overlay(base: np.ndarray, top: np.ndarray) -> np.ndarray:
    low = _blend_multiply(base, top) * np.float32(2.0)
    high = np.float32(255.0) - np.float32(2.0) * (np.float32(255.0) - base) * (
        np.float32(255.0) - top
    ) / np.float32(255.0)
    return np.where(base < np.float32(128.0), low, high)


def _blend_darken(base: np.ndarray, top: np.ndarray) -> np.ndarray:
    return np.minimum(base, top)


def _blend_lighten(base: np.ndarray, top: np.ndarray) -> np.ndarray:
    return np.maximum(base, top)


def _blend_add(base: np.ndarray, top: np.ndarray) -> np.ndarray:
    return np.clip(base + top, 0.0, 255.0)


def _blend_normal(base: np.ndarray, top: np.ndarray) -> np.ndarray:
    del base
    return top


_BLEND_FUNCS = {
    "normal": _blend_normal,
    "multiply": _blend_multiply,
    "screen": _blend_screen,
    "overlay": _blend_overlay,
    "darken": _blend_darken,
    "lighten": _blend_lighten,
    "add": _blend_add,
}


def apply_blend_mode(
    base: np.ndarray, top: np.ndarray, mode: BlendMode, opacity: float = 1.0
) -> np.ndarray:
    """`base`/`top` float32 [0,255] rétegek keveréke a `mode` móddal,
    `opacity` (`BlendAlpha`) súllyal az eredmény felé — mindkettő azonos
    alakú kell legyen.
    """
    if mode not in _BLEND_FUNCS:
        raise ValueError(f"Ismeretlen blend-mód: {mode!r}")
    blended = _BLEND_FUNCS[mode](base, top)
    return alpha_blend(base, blended, opacity)


def masked_blend(base: np.ndarray, overlay: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """`base·(1−mask) + overlay·mask` — `mask` (H, W) float32 [0,1]."""
    return base * (1.0 - mask[..., np.newaxis]) + overlay * mask[..., np.newaxis]


# --- Elmosás / AutoFix / SimpleColorMatrix -----------------------------


def gaussian_blur_f(image_f: np.ndarray, xblur: float, yblur: float | None = None) -> np.ndarray:
    """Gauss-elmosás float32 rétegen, `xblur`/`yblur` szigmával (`Blur`
    lépés — a Picasa a σ-t közvetlenül a csúszkából vezényli le,
    ld. az effektenkénti képleteket).
    """
    sigma_x = max(float(xblur), 1e-6)
    sigma_y = max(float(yblur if yblur is not None else xblur), 1e-6)
    return cv2.GaussianBlur(image_f, (0, 0), sigmaX=sigma_x, sigmaY=sigma_y)


def autofix(image: np.ndarray) -> np.ndarray:
    """`AutoFix`: a Picasa belső, effekt-csővezetékekben újrahasznált
    automatikus javítása — a projekt már megfejtett `autocolor` (fehér-
    egyensúly) + `autolight` (kontraszt-széthúzás) párosa, ugyanabban a
    sorrendben, mint az `enhance` (I'm Feeling Lucky) belső lépése (a
    reziduál-görbe NÉLKÜL, ami az `enhance`-re jellemző extra simítás).
    """
    from picasapy.render.ops import apply_autocolor, apply_autolight

    validate_image(image)
    return apply_autolight(apply_autocolor(image))


def simple_color_matrix(
    image: np.ndarray,
    brightness: float = 0.0,
    contrast: float = 0.0,
    saturation: float | None = None,
) -> np.ndarray:
    """`SimpleColorMatrix`: fényerő (additív, `[-100..100]` → `±255`),
    kontraszt (a 128 körüli lineáris széthúzás, `[-100..100]` → gain
    `1 + contrast/100`) és telítettség (luma-tartó króma-erősítés,
    `[-100..100]` → gain `1 + saturation/100`, `-100` = teljes
    szürkeárnyalat). `saturation=None` → a telítettséget nem érinti.
    """
    validate_image(image)
    image_f = to_float(image)
    if saturation is not None:
        gray = luma(image_f)[..., np.newaxis]
        gain = np.float32(1.0 + saturation / 100.0)
        image_f = gray + gain * (image_f - gray)
    if contrast:
        gain = np.float32(1.0 + contrast / 100.0)
        image_f = np.float32(128.0) + gain * (image_f - np.float32(128.0))
    if brightness:
        image_f = image_f + np.float32(brightness * 2.55)
    return to_uint8(image_f)


def local_contrast(image_f: np.ndarray, radius: float, strength: float) -> np.ndarray:
    """`LocalContrastImageOperation`: `ki = be + (be − elmosott(be, r))·strength`
    — a `HDR`/`LocalContrast` effektek referencia-implementációja
    (`filterdesc-registry.md` 4.3).
    """
    blurred = gaussian_blur_f(image_f, radius)
    return image_f + (image_f - blurred) * np.float32(strength)


# --- Belső ragyogás (GlowImageOperation innerglow) ----------------------


def inner_glow(
    image: np.ndarray,
    color: tuple[int, int, int],
    xblur: float,
    yblur: float,
    strength: float,
    alpha: float = 1.0,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """`GlowImageOperation(innerglow=true)`: a kép SZÉLÉTŐL befelé ható,
    Gauss-elmosott „izzás" a `color` színnel — a Picasa ezt Vignette-hez
    (fekete) és Matte-hoz (fehér) használja, MuseumMatte-nál pedig a
    paszpartu-vonalak mellett.

    Implementáció: a képhatár egypixeles impulzusát `xblur`/`yblur`
    szigmával elmosva kapjuk a befelé futó „izzás-térképet" (a szélen
    ~1, a középpont felé lecsengő), ezt `strength`-tel súlyozva keverjük
    a `color`-ral az eredeti kép fölé. `mask` (opcionális, H×W [0,1])
    ezt a hatást TOVÁBB korlátozza (pl. MuseumMatte csak a vonal sávján).
    """
    validate_image(image)
    height, width = image.shape[:2]
    border = np.zeros((height, width), dtype=np.float32)
    border[0, :] = 1.0
    border[-1, :] = 1.0
    border[:, 0] = 1.0
    border[:, -1] = 1.0
    glow = gaussian_blur_f(border, xblur, yblur)
    peak = float(glow.max())
    if peak > 0:
        glow = glow / np.float32(peak)
    weight = np.clip(glow * np.float32(strength), 0.0, 1.0) * np.float32(alpha)
    if mask is not None:
        weight = weight * mask
    color_arr = np.array(color, dtype=np.float32)
    image_f = to_float(image)
    result = image_f * (1.0 - weight[..., np.newaxis]) + color_arr * weight[..., np.newaxis]
    return to_uint8(result)


# --- Zaj (Noise) ---------------------------------------------------------


def noise_layer(
    height: int, width: int, seed: int, low: float, high: float, grayscale: bool
) -> np.ndarray:
    """`Noise`: egyenletes eloszlású zajréteg float32 [0,255], `seed`-del
    determinisztikus (a Picasa saját PRNG-je nem publikus — a determinisztikus
    reprodukálhatóság a lényeg, nem a bitre azonos zajminta).
    """
    rng = np.random.default_rng(seed)
    if grayscale:
        plane = rng.uniform(low, high, size=(height, width)).astype(np.float32)
        return np.repeat(plane[..., np.newaxis], 3, axis=2)
    return rng.uniform(low, high, size=(height, width, 3)).astype(np.float32)


def apply_noise(
    image: np.ndarray,
    seed: int,
    low: float,
    high: float,
    grayscale: bool,
    blend_alpha: float,
    blend_mode: BlendMode,
) -> np.ndarray:
    """Zajréteg generálása és `blend_mode`/`blend_alpha` szerinti keverése."""
    validate_image(image)
    height, width = image.shape[:2]
    noise = noise_layer(height, width, seed, low, high, grayscale)
    image_f = to_float(image)
    return to_uint8(apply_blend_mode(image_f, noise, blend_mode, blend_alpha))


# --- Gradiens-leképezés (GradientMap / HSVGradientMap) ------------------


def gradient_map(image: np.ndarray, colors: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """`GradientMap`: a Rec.601 luma [0..255] értékét a `colors` (egyenletes
    közű, `len(colors)` pontos) színátmenetére képezi le.
    """
    validate_image(image)
    if len(colors) < 2:
        raise ValueError("Legalább két szín kell a gradienshez")
    image_f = to_float(image)
    gray_index = to_uint8(luma(image_f))
    xs = np.linspace(0.0, 255.0, len(colors))
    channel_luts = []
    for channel in range(3):
        points = tuple(zip(xs.tolist(), (float(c[channel]) for c in colors), strict=True))
        channel_luts.append(curve_lut(points))
    tables = [to_uint8(lut) for lut in channel_luts]
    return np.stack([tables[channel][gray_index] for channel in range(3)], axis=-1)


def hsv_gradient_map(
    image: np.ndarray,
    stops: tuple[tuple[float, float, float, float], ...],
    hue_offset: float = 0.0,
) -> np.ndarray:
    """`HSVGradientMap`: a luma-hoz rendelt (pozíció, hue°, sat%, val%)
    töréspontok interpolációja HSV-térben, majd RGB-re konvertálva —
    a `HeatMap` effekt implementációja.
    """
    validate_image(image)
    positions = np.array([stop[0] for stop in stops], dtype=np.float64)
    hues = np.array([stop[1] for stop in stops], dtype=np.float64)
    sats = np.array([stop[2] for stop in stops], dtype=np.float64)
    vals = np.array([stop[3] for stop in stops], dtype=np.float64)
    idx = np.arange(256, dtype=np.float64)
    hue_lut = (np.interp(idx, positions, hues) + hue_offset) % 360.0
    sat_lut = np.interp(idx, positions, sats)
    val_lut = np.interp(idx, positions, vals)
    hsv_lut = np.stack(
        [hue_lut / 2.0, sat_lut * 2.55, val_lut * 2.55], axis=-1
    )
    hsv_lut = np.clip(np.rint(hsv_lut), 0, 255).astype(np.uint8).reshape(1, 256, 3)
    rgb_lut = cv2.cvtColor(hsv_lut, cv2.COLOR_HSV2RGB).reshape(256, 3)
    image_f = to_float(image)
    gray_index = to_uint8(luma(image_f))
    return rgb_lut[gray_index]


# --- Térbeli maszkok -------------------------------------------------------


def circular_gradient_mask(
    height: int,
    width: int,
    inner_radius: float,
    outer_radius: float,
    center: tuple[float, float] | None = None,
) -> np.ndarray:
    """`CircularGradient`: (H, W) float32 [0,1] maszk — 0 az `inner_radius`-on
    belül (védett, „éles" zóna), 1 az `outer_radius`-on túl (teljesen
    hatásba vont zóna), lineárisan a kettő között. `center` alapból a kép
    közepe, pixel-egységben.
    """
    cx, cy = center if center is not None else (width / 2.0, height / 2.0)
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    dist = np.hypot(xs + 0.5 - cx, ys + 0.5 - cy)
    if outer_radius <= inner_radius:
        return (dist >= inner_radius).astype(np.float32)
    return np.clip((dist - inner_radius) / (outer_radius - inner_radius), 0.0, 1.0)


def tint_multiply(image: np.ndarray, color: tuple[int, int, int], alpha: float) -> np.ndarray:
    """`Tint(Color=..., BlendMode=multiply)`: szorzó-színezés `alpha` súllyal."""
    validate_image(image)
    image_f = to_float(image)
    color_layer = np.empty_like(image_f)
    color_layer[..., 0] = color[0]
    color_layer[..., 1] = color[1]
    color_layer[..., 2] = color[2]
    return to_uint8(apply_blend_mode(image_f, color_layer, "multiply", alpha))


def resize_image(image: np.ndarray, width: int, height: int, smoothing: bool = True) -> np.ndarray:
    """`Resize`: a kép átméretezése — `smoothing=False` a Pixelate blokkos
    (`INTER_NEAREST`) visszanagyítását adja, egyébként bilineáris.
    """
    validate_image(image)
    width = max(1, int(round(width)))
    height = max(1, int(round(height)))
    interp = cv2.INTER_LINEAR if smoothing else cv2.INTER_NEAREST
    return cv2.resize(image, (width, height), interpolation=interp)


def bw_tint(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """`BW(filtercolor=...)`: szürkeárnyalat, a luma-val arányosan a `color`
    felé színezve (`ki = luma/255 · color`) — a Holga „vörösesbarna" B&W-je.
    """
    validate_image(image)
    image_f = to_float(image)
    gray = luma(image_f) / np.float32(255.0)
    color_arr = np.array(color, dtype=np.float32)
    return to_uint8(gray[..., np.newaxis] * color_arr)


__all__ = [
    "to_uint8",
    "to_float",
    "luma",
    "fade_alpha",
    "alpha_blend",
    "adjust_curves",
    "invert_curve",
    "apply_blend_mode",
    "masked_blend",
    "gaussian_blur_f",
    "autofix",
    "simple_color_matrix",
    "local_contrast",
    "inner_glow",
    "noise_layer",
    "apply_noise",
    "gradient_map",
    "hsv_gradient_map",
    "circular_gradient_mask",
    "tint_multiply",
    "resize_image",
    "bw_tint",
]
