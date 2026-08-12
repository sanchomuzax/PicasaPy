"""Glimmer-effektek — kreatív csővezetékek (#381): `Cinemascope`, `Orton`,
`PencilSketch`, `Holga`, `Lomo`, `IR`, `Neon`.

Ld. `glimmer_tone.py` modul-docstringjét az egzaktság-elvről: a lépéssorrend
és a számértékek a `filterdesc-registry.md` 4. fejezetéből jönnek, az
alacsony szintű kernelek (Gauss-elmosás, LERP) a szokásos megfelelőik. Az
Az `IR` a #566 óta már NEM interpretáció: a `filterdesc.xml` valóban csak a
három paraméternevet és fix értéket adja, de a `Picasa3.exe` statikus
visszafejtése (`glimmer::IRImageOperation`) a teljes csővezetéket feltárta —
ld. az `apply_ir` docstringjét.

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
    (`Bloom` `[0..50]`, alap 25; a Gauss-szigma a FELE, ld. lent) → mestergörbe középpont-emelés
    `(128, 128+(Brightness−50)·96/50)` (`Brightness` `[0..100]`, alap 50).
    """
    validate_image(image)
    image_f = to_float(image)
    # #317: a Flash-örökségű `Bloom` NEM közvetlenül Gauss-szigma — a
    # `referencia/ortonish/` két bloom-állása egymástól függetlenül a FELÉT
    # adta (Bloom=25 → σ≈12, Bloom=50 → σ≈25); az eltérés az alap-exporttól
    # 5,06 → 1,99, a bloom-maxon 5,19 → 2,04. Ugyanez a 2-es szorzó jött ki a
    # Vignette és a Museum Matte ragyogás-sugaránál is.
    blurred = gaussian_blur_f(image_f, max(bloom / 2.0, 1e-3))
    overlaid = apply_blend_mode(image_f, blurred, "overlay", 1.0)
    # #317: a mestergörbe középpontjának kitérése MÉRVE ±96 (nem ±75) a
    # csúszka két végén (`referencia/ortonish/`: Brightness=0 → 26,
    # Brightness=100 → 219; az eltérés 8,51/5,34 → 3,85/3,17). A maradék
    # eltérés a görbe ALAKJÁBÓL jön (a Picasa vélhetően spline-t húz a
    # három pont közé, mi töröttvonalat) — ez külön kérdés.
    mid = 128.0 + (brightness - 50.0) * 96.0 / 50.0
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

#: Az `IRImageOperation` fix paraméterei a natív visszafejtésből (#566).
#: A `greenglow = 5` a blur szigmája (x és y egyaránt), a `greenglowalpha`
#: a LIGHTEN-keverés súlya, a záró monokróm mátrix súlyai pedig
#: `(−0,5, +2,0, −0,5)` — a KÉK súlya is negatív (ezt hagyta ki a korábbi,
#: paraméternevekből következtetett modell).
_IR_GLOW_BLUR = 5.0
_IR_GLOW_ALPHA = 0.25
_IR_RED_WEIGHT = np.float32(-0.5)
_IR_GREEN_WEIGHT = np.float32(2.0)
_IR_BLUE_WEIGHT = np.float32(-0.5)


def apply_ir(image, fade: float = 0.0):
    """`IR=1,Fade` — `glimmer::IRImageOperation` (RTTI/vtable `0xcf0a14`,
    konstruktor `0xbc3d80`, feldolgozás `0xbc3f50`).

    **MEGFEJTVE (#566)** — a `Picasa3.exe` statikus visszafejtéséből, nem a
    paraméternevek értelmezéséből. A csővezeték:

    1. **színmátrix**: csak a ZÖLD csatorna (és az alfa) marad meg — a
       glow-réteg `(0, G, 0)`;
    2. **elmosás**: `x = 5`, `y = 5` (quality 3 — a minőségfok a natív
       Gauss-közelítés lépésszáma, a mi `cv2.GaussianBlur`-ünkkel nem
       paraméterezhető és a kimenetet nem is befolyásolja érdemben);
    3. a zöld glow **LIGHTEN** módban kerül az EREDETI képre, `alpha = 0,25`;
    4. záró monokróm színmátrix:
       `Y = clamp(−0,5·R + 2,0·G − 0,5·B)`, majd `RGB = (Y, Y, Y)`;
    5. végül a Glimmer-közös Fade-keverés (`1 − Fade/100`).

    A korábbi modell három ponton tért el: SCREEN-t kevert LIGHTEN helyett,
    a glow-t a már monokrómmá tett képre tette (nem az eredetire), és a KÉK
    csatorna negatív súlyát teljesen figyelmen kívül hagyta.

    A LIGHTEN-azonosítást a `PicnikGrain` deklarációja is megerősíti: ott a
    7-es blend-mód LIGHTEN, az 5-ös MULTIPLY.
    """
    validate_image(image)
    image_f = to_float(image)
    # 1. színmátrix: csak a zöld marad
    green = image_f[..., 1]
    zeros = np.zeros_like(green)
    green_layer = np.stack([zeros, green, zeros], axis=-1)
    # 2. elmosás (x = y = 5)
    glow = gaussian_blur_f(green_layer, _IR_GLOW_BLUR)
    # 3. LIGHTEN az EREDETI képre, 0,25 súllyal
    lightened = apply_blend_mode(image_f, glow, "lighten", _IR_GLOW_ALPHA)
    # 4. záró monokróm mátrix — a kék súlya is negatív
    luma_ir = np.clip(
        _IR_RED_WEIGHT * lightened[..., 0]
        + _IR_GREEN_WEIGHT * lightened[..., 1]
        + _IR_BLUE_WEIGHT * lightened[..., 2],
        0.0,
        255.0,
    )
    ir = np.stack([luma_ir, luma_ir, luma_ir], axis=-1)
    # 5. Fade
    return to_uint8(alpha_blend(image_f, ir, fade_alpha(fade)))


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
