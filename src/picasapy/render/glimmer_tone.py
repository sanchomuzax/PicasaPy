"""Glimmer-effektek — tónus-csővezetékek (#381): `Vignette`, `Matte`, `HDR`,
`LocalContrast`, `CrossProcess`, `Sixties`, `HeatMap`, `NightVision`,
`TwoTone`, `QuantizePalette`.

Minden csővezeték a `docs/specs/filterdesc-registry.md` 4. fejezetében
(a `filterdesc.xml`-ből) rögzített LÉPÉSSORREND és SZÁMÉRTÉK szerint fut —
ez a modul a korábbi `effects_creative_tone.py`/`effects.py` KÖZELÍTŐ
modelljeinek egzakt utódja. A `picasapy.render.glimmer_ops` primitíveket
használja (`hdr_local_contrast`, `adjust_curves`, `apply_noise`,
`hsv_gradient_map` stb.) — az alacsony szintű kernelek (Gauss-elmosás,
LERP-interpoláció) szokásos, jól bevált megfelelői a Picasa nem publikus
C++ motorjának, de a PARAMÉTEREZÉS és a LÉPÉSSORREND bitre a `filterdesc.xml`
szerinti (ld. a modul-docstring `glimmer_ops.py`-ban).

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3). Minden függvény
TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

from picasapy.render.belso_ragyogas import inner_glow
from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import (
    adjust_curves,
    alpha_blend,
    apply_blend_mode,
    apply_noise,
    autofix,
    fade_alpha,
    hsv_gradient_map,
    hdr_local_contrast,
    simple_color_matrix,
    tint_luma_preserving,
    to_float,
    to_uint8,
    xml_local_contrast,
)

# --- Vignette / Matte: GlowImageOperation(innerglow=true) ------------------


#: A `filterdesc.xml` `xblur`-képlete: `Blur · 0,02 · max(W,H) / 4`
#: (`filterdesc-registry.md` 4.3). #3827 óta ez megy VÁLTOZATLANUL a natív
#: láncba (`belso_ragyogas.inner_glow`): a lekicsinyítést, a dobozsugarat és
#: a 253-as vágást a lánc maga végzi. A korábbi illesztett `/8`-as sugár
#: (#317) és a levezetett `vignette_radius` (#2159) ennek a közelítése volt.
VIGNETTE_XBLUR_FACTOR = 0.02 / 4.0

def _glow_vignette(image, blur, strength, color, fade):
    validate_image(image)
    height, width = image.shape[:2]
    xblur = blur * VIGNETTE_XBLUR_FACTOR * max(width, height)
    glowed = inner_glow(image, color, xblur, xblur, strength)
    return to_uint8(alpha_blend(to_float(image), to_float(glowed), fade_alpha(fade)))


def apply_vignette(
    image, blur: float = 35.0, strength: float = 1.4, fade: float = 0.0, color=(0, 0, 0)
):
    """`Vignette=1,Blur,Strength,Fade,szín` — belső, fekete ragyogás a szélektől.

    Blur `[0..50]` (alap 35), Strength `[1..2]` (alap 1,4).

    A ragyogás a natív lánc (#3827, `belso_ragyogas.inner_glow`): a
    `filterdesc` `xblur`-je (`Blur·0,02·max(W,H)/4`) a blur-átváltón
    (`0x00bb89b0`) át lekicsinyített pufferbe kerül, ott dobozmenetekkel
    mosódik, és a súlyt a Mitchell-átméretező nagyítja vissza.
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


def apply_local_contrast(image, radius: float = 15.0, strength: float = 1.5):
    """`LocalContrast=1,Radius,Contrast` — a `filterdesc.xml` lánca, Fade
    nélkül. Radius `[1,3..40]` (alap 15), Contrast `[1..3]` (alap 1,5).

    #3520: `ki = elm + C·(be − elm)` (`glimmer_ops.xml_local_contrast`),
    tehát `Contrast = 1`-nél a kimenet bitre azonos a bemenettel (#688) —
    ehhez már nem kell külön `Contrast − 1` eltolás.
    """
    validate_image(image)
    return xml_local_contrast(image, radius, strength)


def apply_hdr(image, radius: float = 20.0, strength: float = 3.0, fade: float = 0.0):
    """`HDR=1,Radius,Contrast,Fade` — a natív `LocalContrastImageOperation`,
    majd Fade-keverés. Radius `[1,3..80]` (alap 20), Strength `[1..7]` (alap 3).

    #3520: a natív lánc az EREDETIBŐL indul, `ki = be + C·(be − elm)`
    (`glimmer_ops.hdr_local_contrast`), ezért `Contrast = 1`-nél is élesít.
    A `LocalContrast`-tól ez különbözteti meg.
    """
    validate_image(image)
    contrasted = to_float(hdr_local_contrast(image, radius, strength))
    return to_uint8(alpha_blend(to_float(image), contrasted, fade_alpha(fade)))


# --- CrossProcess ------------------------------------------------------------

_CROSS_RED = ((0.0, 0.0), (60.0, 30.0), (210.0, 255.0), (255.0, 255.0))
_CROSS_GREEN = ((0.0, 0.0), (47.0, 38.0), (101.0, 111.0), (187.0, 206.0), (255.0, 255.0))
_CROSS_BLUE = ((0.0, 32.0), (255.0, 216.0))
_CROSS_TINT_COLOR = (0xFC, 0xFF, 0x00)


def apply_crossprocess(image, fade: float = 0.0):
    """`CrossProcess=1,Fade` — fix csatornagörbék → `SimpleColorMatrix
    (Contrast=+10, Brightness=+10)` → `#fcff00` `Tint`.

    A `Tint` maga a fényesség-tartó színezés; a leíró `BlendMode="multiply"`
    és `BlendAlpha=".2"` mezője az eredményét keveri a bemenetére (#3452).
    """
    validate_image(image)
    curved = adjust_curves(image, red=_CROSS_RED, green=_CROSS_GREEN, blue=_CROSS_BLUE)
    matrixed = simple_color_matrix(curved, brightness=10.0, contrast=10.0)
    colored = tint_luma_preserving(matrixed, _CROSS_TINT_COLOR)
    tinted = apply_blend_mode(to_float(matrixed), to_float(colored), "multiply", 0.2)
    return to_uint8(alpha_blend(to_float(image), to_float(tinted), fade_alpha(fade)))


# --- Sixties -----------------------------------------------------------------

# A `filterdesc.xml` `Sixties` görbéi szó szerint (#3451). A csatornagörbék
# ELSŐ pontja emeli a feketét (piros 59, zöld 22, kék 9) — ez adja a meleg,
# fakó alapot. Az `adjust_curves`-lánc (#3942) a saját töréspontjain túl
# EXTRAPOLÁL (a mestergörbe 243 fölötti kimenete a kék csatornát is a
# 255-ös töréspontján túl viszi), tehát a pontokat itt sem kell 0-ig vagy
# 255-ig kiegészíteni.
_SIXTIES_MASTER = ((0.0, 0.0), (150.0, 104.0), (243.0, 255.0))
_SIXTIES_RED = ((0.0, 59.0), (96.0, 156.0), (210.0, 255.0))
_SIXTIES_GREEN = ((0.0, 22.0), (150.0, 166.0), (255.0, 216.0))
_SIXTIES_BLUE = ((0.0, 9.0), (126.0, 98.0), (255.0, 231.0))


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
    """`HeatMap=1,Hue,Fade` — `SimpleColorMatrix(Saturation=0)` →
    `HSVGradientMap` a 240°→120°→0° hőtérkép-skálán, `Hue` (`[-180..180]`)
    eltolással.

    #3421: a leíró `Saturation="0"`-t ír, ami NEM szürkít (mint a TwoTone-nál,
    #3433); a korábbi `-100`-as teljes szürkítés a gradiens piros-csatornás
    indexével együtt a Picasa-exporttól ΔE ~21-re vitt.
    """
    validate_image(image)
    matrixed = simple_color_matrix(image, saturation=0.0)
    mapped = hsv_gradient_map(matrixed, _HEATMAP_STOPS, hue_offset=hue)
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
    xblur = 35.0 * 0.02 * max(height, width) / 3.0
    glowed = inner_glow(mapped, (0, 0, 0), xblur, xblur, 1.5)
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
    `SimpleColorMatrix(Saturation=0, Brightness, Contrast,
    ContrastAndBrightnessLinked=true)` → lineáris interpoláció a
    `black_color`/`white_color` között, a mátrix utáni NYERS PIROS
    csatorna szerint.

    #3433: a gradiens indexe NEM luma. A `0x00bb87b0` LUT-építő a négy
    256-os rekeszből csak a `+0x800`-at (a BGRA-képpont `src[2]` bájtja,
    a piros) tölti az interpolált színnel, a másik kettőt nullázza; a
    `0x00bcb2f0` alkalmazó a rekeszeket bájtonként összegzi.
    """
    import numpy as np

    validate_image(image)

    matrixed = simple_color_matrix(
        image,
        saturation=0.0,
        brightness=brightness,
        contrast=contrast,
        linked=True,
    )
    gray = to_float(matrixed)[..., 0:1] / 255.0
    black = np.array(black_color, dtype=float)
    white = np.array(white_color, dtype=float)
    mapped = black + gray * (white - black)
    return to_uint8(alpha_blend(to_float(image), mapped, fade_alpha(fade)))


# --- QuantizePalette -------------------------------------------------------


def apply_quantizepalette(image, steps: float = 8.0, smoothing: float = 80.0, fade: float = 0.0):
    """`QuantizePalette=1,Steps,Smoothing,Fade` — előzetes elmosás
    (`(100−Smoothing)/10 + 0,1` szigma), majd a kép SAJÁT, `Steps − 1`
    elemű palettájára kvantálás, végül `Fade` szerinti visszakeverés.

    A `filterdesc.xml` lánca (1244–1258. sor): `BlurImageOperation` →
    `QuantizePaletteImageOperation Depth="4"`, egy `NestedImageOperation`
    `BlendAlpha = 1 − Fade/100` keverésében. A kvantálás a binárisból
    kiolvasott oktree-út (#3084): 50 × 50-es pontminta → oktree →
    `Steps − 1` levél → 3-3-2 keresőtábla — a részletek és a címek a
    `picasapy.render.quantize_palette` modulban.

    ## Miért nem egyenletes rács (a #2231 régi modellje)

    A korábbi megvalósítás csatornánként egyenletes rácsra kvantált, egy
    olyan referencia alapján, amely a PicasaPy SAJÁT exportja volt, nem a
    Picasáé (PR #3440). A valódi Picasa-exportokon (NAS
    `3084-poszterizalas`, 8/80/0, kanonikus ΔE) a rácsos modell 16,64 /
    17,16, ez 0,54 / 0,91 — az őr:
    `tests/render/test_quantizepalette_paletta_3084.py`.

    Az elmosás a `BlurImageOperation` natív útja (`quality="3"`,
    `render/nativ_blur.blur_image_operation`): a Gauss-közelítéssel a
    három valódi export ΔE-je 2,45 / 4,01 / 1,74 volt, ezzel 0,54 / 0,34 /
    0,91 — a JPEG-újratömörítés zajszintje.
    """
    from picasapy.render.nativ_blur import blur_image_operation
    from picasapy.render.quantize_palette import kvantal

    validate_image(image)
    sugar = (100.0 - smoothing) / 10.0 + 0.1
    blurred = blur_image_operation(image, sugar, sugar, quality=3)
    quantized = kvantal(blurred, steps)
    return to_uint8(alpha_blend(to_float(image), to_float(quantized), fade_alpha(fade)))


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
