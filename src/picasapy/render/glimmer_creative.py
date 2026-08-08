"""Glimmer-effektek — kreatív csővezetékek (#381): `Cinemascope`, `Orton`,
`PencilSketch`, `Holga`, `Lomo`, `IR`, `Neon`.

Ld. `glimmer_tone.py` modul-docstringjét az egzaktság-elvről: a lépéssorrend
és a számértékek a `filterdesc-registry.md` 4. fejezetéből jönnek, az
alacsony szintű kernelek (Gauss-elmosás, LERP) a szokásos megfelelőik. Az
`IR` kivétel: a Picasa `IRImageOperation`-jének BELSŐ képlete a
`filterdesc.xml`-ben SEM publikus (csak a három paraméternév és fix érték
adott) — ott a pixel-modell dokumentáltan INTERPRETÁCIÓ, ld. az `apply_ir`
docstringjét.

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3). Minden függvény
TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_frame_ops import add_border_sides
from picasapy.render.glimmer_ops import (
    adjust_curves,
    alpha_blend,
    apply_blend_mode,
    apply_noise,
    autofix,
    bw_tint,
    circular_gradient_mask,
    clamp_glow_radius,
    fade_alpha,
    gaussian_blur_f,
    inner_glow,
    masked_blend,
    resize_image,
    simple_color_matrix,
    tint_multiply,
    to_float,
    to_uint8,
)

# --- Cinemascope -------------------------------------------------------------

_CINEMA_MASTER = ((0.0, 0.0), (29.0, 19.0), (110.0, 150.0), (233.0, 245.0), (255.0, 255.0))
_CINEMA_RED = ((0.0, 0.0), (111.0, 141.0), (255.0, 255.0))
_CINEMA_BLUE = ((0.0, 0.0), (136.0, 121.0), (255.0, 255.0))


def apply_cinemascope(image, letterbox: bool = True):
    """`Cinemascope=1,Letterbox` — 1,7:1 középvágás → 95%-os függőleges
    zsugorítás → `AutoFix` → `Saturation −25` → görbék → szemcse (0,08 =
    225–245 tartomány, szorzó) → felül-alul fekete letterbox-sáv
    (`0,15·cropHeight`). Letterbox kikapcsolva: nincs vágás/zsugorítás,
    csak a görbék/szemcse fut, sáv nélkül. **MEGVÁLTOZTATJA A KÉP MÉRETÉT.**
    """
    validate_image(image)
    height, width = image.shape[:2]
    crop_height = min(round(width / 1.7), height) if letterbox else height
    top = max(0, (height - crop_height) // 2)
    cropped = image[top : top + crop_height, :, :].copy()
    resize_height = round(crop_height * (0.95 if letterbox else 1.0))
    resized = resize_image(cropped, width, max(1, resize_height), smoothing=True)
    fixed = autofix(resized)
    matrixed = simple_color_matrix(fixed, saturation=-25.0)
    curved = adjust_curves(matrixed, master=_CINEMA_MASTER, red=_CINEMA_RED, blue=_CINEMA_BLUE)
    noised = apply_noise(
        curved, seed=0, low=225.0, high=245.0, grayscale=True, blend_alpha=1.0, blend_mode="multiply"
    )
    if not letterbox:
        return noised
    bar = round(crop_height * 0.15)
    return add_border_sides(noised, 0, 0, bar, bar, (0, 0, 0))


# --- Orton ---------------------------------------------------------------


def apply_orton(image, bloom: float = 25.0, brightness: float = 50.0, fade: float = 0.0):
    """`Orton=1,Bloom,Brightness,Fade` — `overlay`-módú elmosott réteg
    (`Bloom` `[0..50]`, alap 25) → mestergörbe középpont-emelés
    `(128, 128+(Brightness−50)·75/50)` (`Brightness` `[0..100]`, alap 50).
    """
    validate_image(image)
    image_f = to_float(image)
    blurred = gaussian_blur_f(image_f, max(bloom, 1e-3))
    overlaid = apply_blend_mode(image_f, blurred, "overlay", 1.0)
    mid = 128.0 + (brightness - 50.0) * 75.0 / 50.0
    curved = adjust_curves(to_uint8(overlaid), master=((0.0, 0.0), (128.0, mid), (255.0, 255.0)))
    return to_uint8(alpha_blend(image_f, to_float(curved), fade_alpha(fade)))


# --- PencilSketch ----------------------------------------------------------


def apply_pencil_sketch(image, radius: float = 2.0, contrast: float = 100.0, fade: float = 0.0):
    """`PencilSketch=1,Radius,Contrast,Fade` — B&W → `AutoFix` (= „A") →
    (invertált „A" elmosva, `ADD` móddal „A"-ra keverve) → az eredmény „A"
    fölé `OVERLAY`-jal → `AutoFix` → mestergörbe `(127, 227−2·Contrast)`.
    Radius `[1,3..5]` (alap 2), Contrast `[0..200]` (alap 100).
    """
    from picasapy.render.color import apply_bw

    validate_image(image)
    base_a = autofix(apply_bw(image))
    base_f = to_float(base_a)
    inverted = 255.0 - base_f
    blurred = gaussian_blur_f(inverted, max(radius, 0.1))
    added = apply_blend_mode(base_f, blurred, "add", 1.0)
    overlaid = apply_blend_mode(added, base_f, "overlay", 1.0)
    fixed_again = autofix(to_uint8(overlaid))
    mid = 227.0 - contrast * 2.0
    curved = adjust_curves(fixed_again, master=((0.0, 0.0), (127.0, mid), (255.0, 255.0)))
    return to_uint8(alpha_blend(to_float(image), to_float(curved), fade_alpha(fade)))


# --- Holga / Lomo ------------------------------------------------------------


def apply_holga(image, blur: float = 70.0, grain: float = 30.0, fade: float = 0.0):
    """`Holga=1,Blur,Grain,Fade` — körkörös maszk (`innerR=0,9·R`,
    `outerR=(2−Blur/100)·R`) → `AutoFix` → belső ragyogás (fekete, 1,4) →
    maszkolt elmosás (18×20) → `#ff6666` tintelt B&W → kontraszt +25 →
    szemcse (`low=255−round(Grain/200·255)`, szorzó 0,6).
    """
    validate_image(image)
    height, width = image.shape[:2]
    outer_r = max(height, width) / 2.0
    mask = circular_gradient_mask(height, width, outer_r * 0.9, outer_r * (2.0 - blur / 100.0))
    fixed = autofix(image)
    glowed = inner_glow(
        fixed,
        (0, 0, 0),
        clamp_glow_radius(0.5 * outer_r),
        clamp_glow_radius(0.4 * outer_r),
        1.4,
        alpha=1.0,
    )
    blurred = gaussian_blur_f(to_float(glowed), 18.0, 20.0)
    masked = to_uint8(masked_blend(to_float(glowed), blurred, mask))
    tinted = bw_tint(masked, (255, 102, 102))
    matrixed = simple_color_matrix(tinted, contrast=25.0)
    low = max(0.0, 255.0 - round(grain / 200.0 * 255.0))
    noised = apply_noise(
        matrixed, seed=5, low=low, high=255.0, grayscale=True, blend_alpha=0.6, blend_mode="multiply"
    )
    return to_uint8(alpha_blend(to_float(image), to_float(noised), fade_alpha(fade)))


def apply_lomo(image, blur: float = 50.0, fade: float = 0.0):
    """`Lomo=1,Blur,Fade` — körkörös maszk (`innerR=0,5·R`,
    `outerR=(2−Blur/100)·R`) → belső ragyogás (fekete, 1,1) → maszkolt
    elmosás (20×20) → `SimpleColorMatrix(Saturation +20, Contrast +35,
    Brightness +5)`.
    """
    validate_image(image)
    height, width = image.shape[:2]
    outer_r = max(height, width) / 2.0
    mask = circular_gradient_mask(height, width, outer_r * 0.5, outer_r * (2.0 - blur / 100.0))
    radius = clamp_glow_radius(35.0 * 0.02 * max(height, width) / 2.0)
    glowed = inner_glow(image, (0, 0, 0), radius, radius, 1.1, alpha=1.0)
    blurred = gaussian_blur_f(to_float(glowed), 20.0, 20.0)
    masked = to_uint8(masked_blend(to_float(glowed), blurred, mask))
    matrixed = simple_color_matrix(masked, brightness=5.0, contrast=35.0, saturation=20.0)
    return to_uint8(alpha_blend(to_float(image), to_float(matrixed), fade_alpha(fade)))


# --- IR ------------------------------------------------------------------


def apply_ir(image, fade: float = 0.0):
    """`IR=1,Fade` — `IRImageOperation(greenglow=5, greenglowalpha=0,25,
    redweight=−0,5)`.

    **RÉSZBEN MEGFEJTVE:** a `filterdesc.xml` a három paraméter NEVÉT és
    FIX ÉRTÉKÉT adja (ezek nem csúszkafüggők — a `IR` effektnek csak
    `Fade` a szabad paramétere), de a `IRImageOperation` BELSŐ pixel-
    képletét (hogyan kombinálja a csatornákat) a fájl NEM közli — az a
    Picasa C++ motorjában van, nem publikus. Az itt implementált modell
    (`greenweight`-tel súlyozott zöld-dominancia + a zöld csatorna elmosott
    izzása `greenglow` sugárral, `greenglowalpha` súllyal `screen`-ezve)
    INTERPRETÁCIÓ a paraméterNEVEK alapján, nem bizonyított pixel-hű
    reprodukció.
    """
    validate_image(image)
    image_f = to_float(image)
    red = image_f[..., 0]
    green = image_f[..., 1]
    ir_base = np.clip(green * 1.5 + red * -0.5, 0.0, 255.0)
    ir_gray = np.stack([ir_base, ir_base, ir_base], axis=-1)
    green_layer = np.stack([green, green, green], axis=-1)
    glow_blur = gaussian_blur_f(green_layer, 5.0)
    glowed = apply_blend_mode(ir_gray, glow_blur, "screen", 0.25)
    return to_uint8(alpha_blend(image_f, glowed, fade_alpha(fade)))


# --- Neon ------------------------------------------------------------------


def apply_neon(image, color=(255, 0, 0), fade: float = 0.0):
    """`Neon=1,szín,Fade` — `EdgeDetectionB(detail=50)` (Canny-éldetektálás
    közelítése) → `LocalContrast(0,0)` (a fix `0,0` paraméterrel: no-op) →
    önmagával `multiply` → invertálás → `Tint(szín)`.
    """
    from picasapy.render.color import apply_bw

    validate_image(image)
    import cv2

    gray = apply_bw(image)[..., 0]
    edges = cv2.Canny(gray, 50, 150).astype(np.float32)
    edges_rgb = np.stack([edges, edges, edges], axis=-1)
    multiplied = apply_blend_mode(edges_rgb, edges_rgb, "multiply", 1.0)
    inverted = 255.0 - multiplied
    tinted = tint_multiply(to_uint8(inverted), color, 1.0)
    return to_uint8(alpha_blend(to_float(image), to_float(tinted), fade_alpha(fade)))


__all__ = [
    "apply_cinemascope",
    "apply_orton",
    "apply_pencil_sketch",
    "apply_holga",
    "apply_lomo",
    "apply_ir",
    "apply_neon",
]
