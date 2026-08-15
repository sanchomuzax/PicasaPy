"""Glimmer-effektek — tónus-csővezetékek (#381): `Vignette`, `Matte`, `HDR`,
`LocalContrast`, `CrossProcess`, `Sixties`, `HeatMap`, `NightVision`,
`TwoTone`, `QuantizePalette`.

Minden csővezeték a `docs/specs/filterdesc-registry.md` 4. fejezetében
(a `filterdesc.xml`-ből) rögzített LÉPÉSSORREND és SZÁMÉRTÉK szerint fut —
ez a modul a korábbi `effects_creative_tone.py`/`effects.py` KÖZELÍTŐ
modelljeinek egzakt utódja. A `picasapy.render.glimmer_ops` primitíveket
használja (`inner_glow`, `local_contrast`, `adjust_curves`, `apply_noise`,
`hsv_gradient_map` stb.) — az alacsony szintű kernelek (Gauss-elmosás,
LERP-interpoláció) szokásos, jól bevált megfelelői a Picasa nem publikus
C++ motorjának, de a PARAMÉTEREZÉS és a LÉPÉSSORREND bitre a `filterdesc.xml`
szerinti (ld. a modul-docstring `glimmer_ops.py`-ban).

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3). Minden függvény
TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import (
    adjust_curves,
    alpha_blend,
    apply_noise,
    autofix,
    clamp_glow_radius,
    fade_alpha,
    hsv_gradient_map,
    inner_glow,
    local_contrast,
    simple_color_matrix,
    to_float,
    to_uint8,
    tint_multiply,
)

# --- Vignette / Matte: GlowImageOperation(innerglow=true) ------------------


#: A `Vignette`/`Matte` ragyogás-sugara: `Blur · 0,02 · max(W,H) · ez`.
#:
#: A `filterdesc.xml` képlete `Blur·0,02·max(W,H)/4` — a **mérés viszont
#: ennek a FELÉT adja** (`referencia/vignette/`, 8 export ugyanarról a
#: 2560×1702-es fotóról, #317). A két szélső Blur-állás egymástól
#: függetlenül ugyanezt mondja:
#:
#:     Blur=35 (alap)  a legjobb illesztés σ ≈ 220   (a képlet /8-a: 224)
#:     Blur=50 (max)   a legjobb illesztés σ ≈ 310–320 (a képlet /8-a: 320)
#:
#: A képlet nem tévedés, csak nem közvetlenül Gauss-szigmát ad: a Flash-
#: örökségű `blurX/blurY` és a szigma között ez a 2-es szorzó ül (ld.
#: `glimmer_ops.inner_glow` docstringje).
#:
#: A 255-ös `clamp_glow_radius` korlát ITT NEM alkalmazható: a Blur=50-es
#: export illesztése 310–320-at kíván, a 255-re vágott sugár mérhetően
#: rosszabb (eltérés 5,79 a 1,22 helyett). A korlát a Lomo/Holga láncban
#: mért, ott érvényes marad (#518).
VIGNETTE_RADIUS_FACTOR = 0.02 / 8.0


def _glow_vignette(image, blur, strength, color, fade):
    validate_image(image)
    height, width = image.shape[:2]
    radius = blur * VIGNETTE_RADIUS_FACTOR * max(height, width)
    glowed = inner_glow(image, color, radius, radius, strength, alpha=1.0)
    return to_uint8(alpha_blend(to_float(image), to_float(glowed), fade_alpha(fade)))


def apply_vignette(
    image, blur: float = 35.0, strength: float = 1.4, fade: float = 0.0, color=(0, 0, 0)
):
    """`Vignette=1,Blur,Strength,Fade,szín` — belső, fekete ragyogás a szélektől.

    Blur `[0..50]` (alap 35), Strength `[1..2]` (alap 1,4), `xblur=yblur =
    Blur·0,02·max(W,H)/4` (`filterdesc-registry.md` 4.3).
    """
    return _glow_vignette(image, blur, strength, color, fade)


def apply_matte(
    image, blur: float = 40.0, strength: float = 1.2, fade: float = 0.0, color=(255, 255, 255)
):
    """`Matte=1,Blur,Strength,szín,Fade` — a Vignette motorja fehér színnel,
    Blur `[0..50]` (alap 40), Strength `[1..2]` (alap 1,2).
    """
    return _glow_vignette(image, blur, strength, color, fade)


# --- HDR / LocalContrast: LocalContrastImageOperation -----------------------


#: #688: a `LocalContrast` `Contrast` csúszkája `[1..3]`, és az ALSÓ vége a
#: NULLA-ÁLLAPOT — a natív műveletnek átadott `Strength` tehát `Contrast − 1`.
#: A `HDR` ugyanezt a motort hajtja, de a `Strength`-et KÖZVETLENÜL adja
#: tovább; a két effekt csővezetéke nem azonos (a `filterdesc-registry.md`
#: szerint a `LocalContrast` `SetVar`/`GetVar` párokra bontva építi fel).
#:
#: Bizonyíték — a #685 mérőszettje (valódi Picasa-export; a modell eltérése
#: a Picasa kimenetétől, ΔE CIE76 átlag):
#:
#:     eset                     Picasa Δ   s=Contrast   s=Contrast−1
#:     min  (R=1,3  C=1,0)         0,18       1,85          0,18
#:     alap (R=15   C=1,5)         3,08       2,24          0,37
#:     max  (R=40   C=3,0)         9,43       2,77          0,87
#:
#: (A 0,18 a mérőszett JPEG-zajszintje, azaz a `min` esetben a Picasa és az
#: eltolt modell EGYARÁNT tétlen.) Ugyanez az eltolás a `HDR`-en ROSSZABB
#: illeszkedést ad (alap: 1,71 vele, 1,24 nélküle), ezért KIZÁRÓLAG a
#: `LocalContrast`-é.
LOCAL_CONTRAST_STRENGTH_OFFSET = 1.0


def apply_local_contrast(image, radius: float = 15.0, strength: float = 1.5):
    """`LocalContrast=1,Radius,Contrast` — a `HDR`-ével AZONOS motor, Fade
    nélkül. Radius `[1,3..40]` (alap 15), Contrast `[1..3]` (alap 1,5).

    #545: a Gauss-szigma a `Radius` FELE, és a művelethez `Strength`-arányos
    világosítás is tartozik (ld. `glimmer_ops.local_contrast`).

    #688: a csúszka ALSÓ vége (`Contrast = 1`) a nulla-állapot, ezért a
    motornak `Contrast − 1` megy át — `Contrast = 1`-nél a kimenet bitre
    azonos a bemenettel (ld. `LOCAL_CONTRAST_STRENGTH_OFFSET`).
    """
    validate_image(image)
    effective = max(strength - LOCAL_CONTRAST_STRENGTH_OFFSET, 0.0)
    if effective == 0.0:
        return image.copy()
    return to_uint8(local_contrast(to_float(image), radius, effective))


def apply_hdr(image, radius: float = 20.0, strength: float = 3.0, fade: float = 0.0):
    """`HDR=1,Radius,Contrast,Fade` — ugyanaz, mint `LocalContrast`, majd
    Fade-keverés. Radius `[1,3..80]` (alap 20), Strength `[1..7]` (alap 3).

    #545: a `referencia/hdrish/` kilenc exportján mérve a modell átlagos
    eltérése a valódi Picasa-kimenettől **2,45** (az érintetlen képé 20,85;
    a korábbi változaté 11,2 — vagyis az alig volt jobb a semminél). A
    mérés két dolgot javított: a Gauss-szigma a `Radius` FELE (a négy
    Radius-állás egymástól függetlenül ugyanezt adta), és a lokális
    kontraszt mellett `Strength`-arányos világosítás is fut.
    """
    validate_image(image)
    image_f = to_float(image)
    contrasted = local_contrast(image_f, radius, strength)
    return to_uint8(alpha_blend(image_f, contrasted, fade_alpha(fade)))


# --- CrossProcess ------------------------------------------------------------

_CROSS_RED = ((0.0, 0.0), (60.0, 30.0), (210.0, 255.0), (255.0, 255.0))
_CROSS_GREEN = ((0.0, 0.0), (47.0, 38.0), (101.0, 111.0), (187.0, 206.0), (255.0, 255.0))
_CROSS_BLUE = ((0.0, 32.0), (255.0, 216.0))
_CROSS_TINT_COLOR = (0xFC, 0xFF, 0x00)


def apply_crossprocess(image, fade: float = 0.0):
    """`CrossProcess=1,Fade` — fix csatornagörbék → `SimpleColorMatrix
    (Contrast=+10, Brightness=+10)` → `#fcff00` szorzó-tint 0,2 alfával."""
    validate_image(image)
    curved = adjust_curves(image, red=_CROSS_RED, green=_CROSS_GREEN, blue=_CROSS_BLUE)
    matrixed = simple_color_matrix(curved, brightness=10.0, contrast=10.0)
    tinted = tint_multiply(matrixed, _CROSS_TINT_COLOR, 0.2)
    return to_uint8(alpha_blend(to_float(image), to_float(tinted), fade_alpha(fade)))


# --- Sixties -----------------------------------------------------------------

_SIXTIES_MASTER = ((0.0, 0.0), (150.0, 104.0), (243.0, 255.0), (255.0, 255.0))
_SIXTIES_RED = ((0.0, 0.0), (59.0, 59.0), (96.0, 156.0), (210.0, 255.0), (255.0, 255.0))
_SIXTIES_GREEN = ((0.0, 0.0), (22.0, 22.0), (150.0, 166.0), (255.0, 216.0))
_SIXTIES_BLUE = ((0.0, 0.0), (9.0, 9.0), (126.0, 98.0), (255.0, 231.0))


def apply_sixties(image, rounded: bool = True, color=(255, 255, 255), fade: float = 20.0):
    """`Sixties=1,Fade,szín,Rounded` — `AutoFix` → csatornagörbék → 235–255
    szürke szemcse (0,6 multiply) → Fade-keverés → (halványítatlan)
    `min(W,H)/14` sarok-lekerekítés, ha `Rounded`.
    """
    from picasapy.render.glimmer_frame_ops import round_corners

    validate_image(image)
    fixed = autofix(image)
    curved = adjust_curves(
        fixed, master=_SIXTIES_MASTER, red=_SIXTIES_RED, green=_SIXTIES_GREEN, blue=_SIXTIES_BLUE
    )
    noised = apply_noise(
        curved, seed=5, low=235.0, high=255.0, grayscale=True, blend_alpha=0.6, blend_mode="multiply"
    )
    blended = to_uint8(alpha_blend(to_float(image), to_float(noised), fade_alpha(fade)))
    if not rounded:
        return blended
    height, width = blended.shape[:2]
    return round_corners(blended, min(height, width) / 14.0, color)


# --- HeatMap -------------------------------------------------------------

_HEATMAP_STOPS = (
    (0.0, 240.0, 100.0, 50.0),
    (31.875, 240.0, 100.0, 100.0),
    (127.5, 120.0, 100.0, 100.0),
    (223.125, 0.0, 100.0, 100.0),
    (255.0, 0.0, 100.0, 50.0),
)


def apply_heatmap(image, hue: float = 0.0, fade: float = 0.0):
    """`HeatMap=1,Hue,Fade` — deszaturálás → `HSVGradientMap` a 240°→120°→0°
    hőtérkép-skálán, `Hue` (`[-180..180]`) eltolással.
    """
    validate_image(image)
    desaturated = simple_color_matrix(image, saturation=-100.0)
    mapped = hsv_gradient_map(desaturated, _HEATMAP_STOPS, hue_offset=hue)
    return to_uint8(alpha_blend(to_float(image), to_float(mapped), fade_alpha(fade)))


# --- NightVision -----------------------------------------------------------

_NIGHTVISION_COLORS = ((0, 0, 0), (0x57, 0xCC, 0x29))


def apply_nightvision(image, brightness: float = 0.0, contrast: float = 0.0, fade: float = 0.0):
    """`NightVision=1,Brightness,Contrast,Fade` — `AutoFix` → fekete→zöld
    `GradientMap` → belső ragyogás → színes zaj (lighten, 0,2 alfa) →
    fényerő/kontraszt → Fade-keverés.
    """
    from picasapy.render.glimmer_ops import gradient_map

    validate_image(image)
    fixed = autofix(image)
    mapped = gradient_map(fixed, _NIGHTVISION_COLORS)
    height, width = mapped.shape[:2]
    radius = clamp_glow_radius(35.0 * 0.02 * max(height, width) / 3.0)
    glowed = inner_glow(mapped, (0, 0, 0), radius, radius, 1.5, alpha=1.0)
    noised = apply_noise(
        glowed, seed=30, low=0.0, high=180.0, grayscale=False, blend_alpha=0.2, blend_mode="lighten"
    )
    matrixed = simple_color_matrix(noised, brightness=brightness, contrast=contrast)
    return to_uint8(alpha_blend(to_float(image), to_float(matrixed), fade_alpha(fade)))


# --- TwoTone -------------------------------------------------------------


def apply_twotone(
    image,
    black_color=(0x00, 0x44, 0x88),
    white_color=(0xFF, 0xFF, 0x00),
    brightness: float = 0.0,
    contrast: float = 20.0,
    fade: float = 0.0,
):
    """`TwoTone=1,Brightness,Contrast,Fade,fekete,fehér` —
    `SimpleColorMatrix(Saturation=0, Brightness, Contrast)` → luma-alapú
    lineáris interpoláció a `black_color`/`white_color` között.
    """
    import numpy as np

    validate_image(image)
    from picasapy.render.glimmer_ops import luma

    matrixed = simple_color_matrix(image, saturation=-100.0, brightness=brightness, contrast=contrast)
    gray = (luma(to_float(matrixed)) / 255.0)[..., None]
    black = np.array(black_color, dtype=float)
    white = np.array(white_color, dtype=float)
    mapped = black + gray * (white - black)
    return to_uint8(alpha_blend(to_float(image), mapped, fade_alpha(fade)))


# --- QuantizePalette -------------------------------------------------------


def apply_quantizepalette(image, steps: float = 8.0, smoothing: float = 80.0, fade: float = 0.0):
    """`QuantizePalette=1,Steps,Smoothing,Fade` — előzetes lágy elmosás
    (`(100−Smoothing)/10 + 0,1` szigma) → egyenletes lépésközű kvantálás
    (`Depth=4` — az RGB-csatornánkénti `Steps` szintre kvantálás; a
    `Depth` konstans a `filterdesc.xml`-ben nem az RGB-mélységet, hanem a
    belső paletta-keresés lépésszámát jelöli, itt a lineáris kvantálással
    egyenértékű).
    """
    import numpy as np

    from picasapy.render.glimmer_ops import gaussian_blur_f

    validate_image(image)
    sigma = max((100.0 - smoothing) / 10.0 + 0.1, 1e-6)
    blurred = gaussian_blur_f(to_float(image), sigma)
    levels = max(2, int(round(steps)))
    scale = 255.0 / (levels - 1) if levels > 1 else 255.0
    quantized = np.rint(np.rint(blurred / scale) * scale)
    return to_uint8(alpha_blend(to_float(image), quantized, fade_alpha(fade)))


__all__ = [
    "apply_vignette",
    "apply_matte",
    "apply_local_contrast",
    "apply_hdr",
    "apply_crossprocess",
    "apply_sixties",
    "apply_heatmap",
    "apply_nightvision",
    "apply_twotone",
    "apply_quantizepalette",
]
