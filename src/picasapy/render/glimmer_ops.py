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

import functools
import math as _math
from picasapy.lazy_cv2 import cv2 as _cv2
import numpy as np
from picasapy.render import nativ_noise as _nativ_noise
from picasapy.render.curves import (
    CurvePoints as _CurvePoints,
    apply_byte_luts as _apply_byte_luts,
    evaluate_curve_extrapolated as _evaluate_curve_extrapolated,
    validate_image as _validate_image,
)
from picasapy.render import glimmer_autofix_ops as _autofix
from picasapy.render import glimmer_blend_ops as _blend
from picasapy.render import glimmer_color_ops as _color
from picasapy.render import glimmer_gradient_ops as _gradient
from picasapy.render import glimmer_mask_ops as _mask
from picasapy.render import glimmer_noise_ops as _noise
from picasapy.render import glimmer_resize_ops as _resize
from picasapy.render.nativ_blur import blur_image_operation as _blur_image_operation
from picasapy.render.nativ_noise import ALAP_CSATORNAK as _ALAP_CSATORNAK
from picasapy.render.quantize_palette import pontminta_racs as _pontminta_racs

# Régi, importból elérhető modulattribútumok.
math = _math
cv2 = _cv2
CurvePoints = _CurvePoints
apply_byte_luts = _apply_byte_luts
evaluate_curve_extrapolated = _evaluate_curve_extrapolated
validate_image = _validate_image
nativ_noise = _nativ_noise
blur_image_operation = _blur_image_operation
ALAP_CSATORNAK = _ALAP_CSATORNAK
pontminta_racs = _pontminta_racs

_REC601_WEIGHTS = _blend._REC601_WEIGHTS
BlendMode = _blend.BlendMode
to_uint8 = _blend.to_uint8
to_float = _blend.to_float
luma = _blend.luma
fade_alpha = _blend.fade_alpha
_float_bitek = _blend._float_bitek
_kozel = _blend._kozel
_bajt = _blend._bajt
alpha_blend = _blend.alpha_blend
adjust_curves = _blend.adjust_curves
invert_curve = _blend.invert_curve
_blend_multiply = _blend._blend_multiply
_blend_screen = _blend._blend_screen
_overlay_alap = _blend._overlay_alap
_blend_overlay = _blend._blend_overlay
_blend_darken = _blend._blend_darken
_blend_lighten = _blend._blend_lighten
_blend_add = _blend._blend_add
_blend_difference = _blend._blend_difference
_blend_subtract = _blend._blend_subtract
_blend_hardlight = _blend._blend_hardlight
_blend_softlight = _blend._blend_softlight
_blend_normal = _blend._blend_normal
_BLEND_FUNCS = _blend._BLEND_FUNCS
BLEND_MODE_BY_INDEX = _blend.BLEND_MODE_BY_INDEX
apply_blend_mode = _blend.apply_blend_mode
masked_blend = _blend.masked_blend
gaussian_blur_f = _blend.gaussian_blur_f
_AUTOFIX_SKALA = _autofix._AUTOFIX_SKALA
_AUTOFIX_KEREKITES = _autofix._AUTOFIX_KEREKITES
_AUTOFIX_MINTA_KUSZOB = _autofix._AUTOFIX_MINTA_KUSZOB
_autofix_mintameret = _autofix._autofix_mintameret
_autofix_hisztogram_forras = _autofix._autofix_hisztogram_forras
autofix = _autofix.autofix
_KONTRASZT_TABLA = _color._KONTRASZT_TABLA
_CONTRAST_EPS = _color._CONTRAST_EPS
_telitettseg_k = _color._telitettseg_k
_saturation_matrix = _color._saturation_matrix
_kontraszt_gorbe = _color._kontraszt_gorbe
_homogen = _color._homogen
_szorzas_x87 = _color._szorzas_x87
_kontraszt_matrix = _color._kontraszt_matrix
_fenyero_matrix = _color._fenyero_matrix
_kontraszt_fenyero_egyuttes_matrix = _color._kontraszt_fenyero_egyuttes_matrix
_szinmatrix_osszefuzve = _color._szinmatrix_osszefuzve
_fixpont_egyutthato = _color._fixpont_egyutthato
_fixpont_bias = _color._fixpont_bias
_fixpontos_szinmatrix = _color._fixpontos_szinmatrix
simple_color_matrix = _color.simple_color_matrix
_szorzott_resz = _color._szorzott_resz
_elmosott = _color._elmosott
hdr_local_contrast = _color.hdr_local_contrast
xml_local_contrast = _color.xml_local_contrast
_bw_coefficients = _color._bw_coefficients
bw_tint = _color.bw_tint
noise_layer = _noise.noise_layer
_blend_noise = _noise._blend_noise
apply_noise = _noise.apply_noise
_GRADIENS_INDEX_CSATORNA = _gradient._GRADIENS_INDEX_CSATORNA
_gradient_map_stop_positions = _gradient._gradient_map_stop_positions
_gradient_map_weight = _gradient._gradient_map_weight
_gradient_map_interpolate_channel = _gradient._gradient_map_interpolate_channel
gradient_map = _gradient.gradient_map
_hsv_rgb_lut_f32 = _gradient._hsv_rgb_lut_f32
hsv_gradient_map = _gradient.hsv_gradient_map
circular_gradient_mask = _mask.circular_gradient_mask
_KORMASZK_POZICIO_MAX = _mask._KORMASZK_POZICIO_MAX
_kormaszk_megallo_tabla = _mask._kormaszk_megallo_tabla
_kormaszk_doboz_pozicio = _mask._kormaszk_doboz_pozicio
tint_multiply = _mask.tint_multiply
_MITCHELL_B = _resize._MITCHELL_B
_MITCHELL_C = _resize._MITCHELL_C
_RESIZE_EGYSEG = _resize._RESIZE_EGYSEG
_RESIZE_ELTOLAS = _resize._RESIZE_ELTOLAS
_RESIZE_KEREKITO = _resize._RESIZE_KEREKITO
_RESIZE_FELSO = _resize._RESIZE_FELSO
mitchell_netravali = _resize.mitchell_netravali
lanczos3 = _resize.lanczos3
_tengely_sulyok = _resize._tengely_sulyok
_tengely_menten = _resize._tengely_menten
resize_image = _resize.resize_image
resize_plane = _resize.resize_plane
_csap_alairas = _resize._csap_alairas
resize_column_plane = _resize.resize_column_plane
_ytresampler = _resize._ytresampler

def _tengely_menten(
    kep: np.ndarray,
    ki_meret: int,
    tengely: int,
    doboz: bool,
    lanczos: bool = False,
    kerekito_oszlopok: np.ndarray | None = None,
) -> np.ndarray:
    """A régi segédfüggvény útvonalán a foltozható súlyfüggvényt használja."""
    return _resize._tengely_menten(
        kep,
        ki_meret,
        tengely,
        doboz,
        lanczos,
        kerekito_oszlopok,
        _sulyok_fuggveny=_tengely_sulyok,
    )


#: A Glimmer `SimpleColorMatrix` (#903) telítettség-ágának luminancia-súlyai
#: — a klasszikus Haeberli-készlet, NEM Rec.601 és NEM Rec.709. A natív
#: `0x008f1d00` ezt olvassa be közvetlenül; Rec.601-gyel látható
#: színeltolás keletkezik (`docs/specs/filterdesc-registry.md` 4.9).
_HAEBERLI_WEIGHTS = (0.3086, 0.6094, 0.0820)


#: `_resaturate_table_entry`: hány kompenzáló menet fusson a gamut-levágás
#: után egy-egy táblabejegyzésre. Menetenként legalább egy csatorna
#: véglegesen kifut a tartományból, ezért három menet a három csatornás
#: esetre elég — a negyedik biztonsági tartalék (#3631).
_TINT_GAMUT_PASSES = 4

_TINT_EPSILON = 1e-6

#: A végső csonkolás előtti lebegőpontos zajszűrő — a súlyösszeggel való
#: osztás valódi tizedeseit nem érheti, ezért jóval az 1e-6 alatt van.
_TINT_TRUNC_EPS = 1e-9



def _haeberli_luma(image_f: np.ndarray) -> np.ndarray:
    """Haeberli-luminancia (H, W) float32 tömbként — a `Tint` szürkítése
    (#3631) ezt használja, NEM a Rec.601-es `luma`-t."""
    red_w, green_w, blue_w = _HAEBERLI_WEIGHTS
    return (
        np.float32(red_w) * image_f[..., 0]
        + np.float32(green_w) * image_f[..., 1]
        + np.float32(blue_w) * image_f[..., 2]
    )



def _resaturate_color_luma(color: tuple[int, int, int]) -> int:
    """A `Resaturate` táblaépítőjének `Lc`-je: a SZÍN Haeberli-fényessége,
    a natív `0x00c29990` kerekítésével (`+0,5`, majd csonkolás — ugyanaz az
    idióma, mint az `autofix` LUT-jáé). `docs/specs/filterdesc-registry.md`
    „H) A `Tint` belseje" 3.1. pont."""
    red_w, green_w, blue_w = _HAEBERLI_WEIGHTS
    r, g, b = (float(c) for c in color)
    value = red_w * r + green_w * g + blue_w * b + 0.5
    return int(np.clip(np.floor(value), 0, 255))



def _resaturate_table_entry(color: tuple[int, int, int], target: int) -> tuple[int, int, int]:
    """`0x00bce2f0(szín, L)` — a `Resaturate` egyetlen táblabejegyzése: az a
    RGB, amely `szín` krómáját adja, a Haeberli-lumája pedig (a levágásig)
    `L`.

    A natív lépései, ahogy az emulált táblával bitre egyeznek (54 szín ×
    256 szint, `tests/render/test_tint_resaturate_nativ_3631.py`):

    1. `d = L − Lc`, és `v = szín + d` csatornánként;
    2. `d > 0`-nál TÜKRÖZÖTT térben számol (`v ← 255 − v`), így a 255 feletti
       túlcsordulás is negatív lesz;
    3. menetenként a negatív csatornák **súlyozott levágott összegét**
       (`over = Σ w·(−v)`) a még SZABAD (pozitív) csatornákról vonja le,
       a súlyösszegükkel osztva (`v −= over / Σ w_szabad`), a negatívakat
       pedig 0-ra teszi;
    4. csonkol (NEM kerekít), és tükrözött esetben `255 − trunc(v)`.

    ⚠️ A tükrözés NEM egyenértékű egy közvetlen, 0 és 255 felé is vágó
    ciklussal: a csonkolás a tükrözött térben lefelé, az eredetiben tehát
    FELFELÉ kerekít, és a hiányt a levágott részből (nem a célfényességből)
    számolja — a korábbi, „algebrailag egyenértékű” változat 52 színen tért
    el a natívtól.
    """
    weights = np.asarray(_HAEBERLI_WEIGHTS, dtype=np.float64)
    delta = float(target) - float(_resaturate_color_luma(color))
    values = np.asarray(color, dtype=np.float64) + delta
    mirrored = delta > 0.0
    if mirrored:
        values = 255.0 - values

    for _ in range(_TINT_GAMUT_PASSES):
        negative = values < 0.0
        if not negative.any():
            break
        over = float((weights * -values * negative).sum())
        values = np.where(negative, 0.0, values)
        free = values > 0.0
        free_weight = float((weights * free).sum())
        if free_weight <= _TINT_EPSILON:
            break
        values = values - free * (over / free_weight)

    # a végső csonkítás (`or 0xc00` + `fistp`, 0x00bce83a) — NEM kerekítés;
    # a `+_TINT_TRUNC_EPS` csak a lebegőpontos zajt söpri el (pl. 199,99999999997
    # helyett 200,0).
    truncated = np.trunc(np.clip(values, 0.0, 255.0) + _TINT_TRUNC_EPS).astype(np.int64)
    truncated = np.minimum(truncated, 255)
    if mirrored:
        truncated = 255 - truncated
    return int(truncated[0]), int(truncated[1]), int(truncated[2])



@functools.lru_cache(maxsize=64)
def _resaturate_table(color: tuple[int, int, int]) -> np.ndarray:
    """A `Resaturate` 256 elemű táblája EGY színre, `0x00bce2f0(szín, i)`
    minden `i = 0…255` Haeberli-fényességre — a szín szerint egyszer épül
    (#3631), utána a képpontok csak indexelnek bele."""
    table = np.array(
        [_resaturate_table_entry(color, level) for level in range(256)],
        dtype=np.uint8,
    )
    table.setflags(write=False)
    return table



def tint_luma_preserving(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """`TintImageOperation(Color=…)` — a natív `ColorMatrix(s=−100)` +
    `Resaturate` páros (#3631, `docs/specs/filterdesc-registry.md` „H) A
    `Tint` belseje").

    1. a bemenetet **Haeberli-szürkére** viszi (`0,3086/0,6094/0,0820`,
       NEM Rec.601), a közös FIXPONTOS alkalmazóval (#3951):
       `szürke = ((632·R >> 9) + (1248·G >> 9) + (168·B >> 9) + 2) >> 2`;
    2. a szürke érték a `_resaturate_table(szín)` 256 elemű táblájának
       indexe — a tábla a `0x00bce2f0(szín, L)` emuláltja `L = 0…255`-re,
       az emulátor kimenetével bitre egyezően (54 szín,
       `tests/render/test_tint_resaturate_nativ_3631.py`). Az 1. lépés
       kerekítése a #3950 kutatás óta kiolvasott (fixpontos, nem `rint`).

    ⛔ **KORÁBBAN** (a #878 golden-illesztése): Rec.601-súlyok +
    folytonos, per-képpont gamut-kompenzáció. Szürke bemeneten a modell
    átlagosan 1–4, telített kéknél/sárgánál (`0x0000ff`, `0xffff00`) akár
    **71 szinttel** tért el az emulált native táblától (#3631 lelete) — a
    Haeberli-súlyok és a diszkrét, szín-szerinti tábla ezt zárja.

    A `color` csatornasorrendje **RGB**.
    """
    validate_image(image)
    # A `ColorMatrix(s = −100)` a közös FIXPONTOS alkalmazón fut (#3951,
    # `c = 632 / 1248 / 168`, `b = 2`), a Haeberli-szürke ennek az indexe.
    gray = _fixpontos_szinmatrix(image, _saturation_matrix(-100.0)[:1], np.zeros(1))[..., 0]
    table = _resaturate_table((int(color[0]), int(color[1]), int(color[2])))
    return table[gray]



__all__ = [
    "to_uint8",
    "lanczos3",
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
    "hdr_local_contrast",
    "xml_local_contrast",
    "noise_layer",
    "apply_noise",
    "gradient_map",
    "hsv_gradient_map",
    "circular_gradient_mask",
    "tint_multiply",
    "resize_image",
    "resize_plane",
    "resize_column_plane",
    "bw_tint",
]
