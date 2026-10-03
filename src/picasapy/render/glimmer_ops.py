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
import math

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.curves import (
    CurvePoints,
    apply_byte_luts,
    evaluate_curve_extrapolated,
    validate_image,
)
from picasapy.render import nativ_noise
from picasapy.render.nativ_blur import blur_image_operation
from picasapy.render.nativ_noise import ALAP_CSATORNAK
from picasapy.render.quantize_palette import pontminta_racs

_REC601_WEIGHTS = (0.299, 0.587, 0.114)

#: A Glimmer `SimpleColorMatrix` (#903) telítettség-ágának luminancia-súlyai
#: — a klasszikus Haeberli-készlet, NEM Rec.601 és NEM Rec.709. A natív
#: `0x008f1d00` ezt olvassa be közvetlenül; Rec.601-gyel látható
#: színeltolás keletkezik (`docs/specs/filterdesc-registry.md` 4.9).
_HAEBERLI_WEIGHTS = (0.3086, 0.6094, 0.0820)

#: A Glimmer `SimpleColorMatrix` (#904) kontraszt-görbéjének (`0x008f2990`)
#: pozitív ága ZÁRT KÉPLETTEL NEM közelíthető — a natív kód egy 101 elemű,
#: kézzel hangolt táblázatból interpolál. A tábla forrása:
#: `referencia/kontraszt-tabla.csv` (a `sanchomuzax/picasapy-agent` privát
#: repóban, 101 sor, a `0x00c7d688` címről kimentve — ld. a fenti spec
#: 4.9-es szakaszát). Index = a csúszka egész része (0..100), az érték a
#: `kontraszt_gorbe(c)` visszatérési értéke `c` egész pontjaiban.
_KONTRASZT_TABLA: tuple[float, ...] = (
    0.00, 0.01, 0.02, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10, 0.11,
    0.12, 0.14, 0.15, 0.16, 0.17, 0.18, 0.20, 0.21, 0.22, 0.24,
    0.25, 0.27, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40, 0.42,
    0.44, 0.46, 0.48, 0.50, 0.53, 0.56, 0.59, 0.62, 0.65, 0.68,
    0.71, 0.74, 0.77, 0.80, 0.83, 0.86, 0.89, 0.92, 0.95, 0.98,
    1.00, 1.06, 1.12, 1.18, 1.24, 1.30, 1.36, 1.42, 1.48, 1.54,
    1.60, 1.66, 1.72, 1.78, 1.84, 1.90, 1.96, 2.00, 2.12, 2.25,
    2.37, 2.50, 2.62, 2.75, 2.87, 3.00, 3.20, 3.40, 3.60, 3.80,
    4.00, 4.30, 4.70, 4.90, 5.00, 5.50, 6.00, 6.50, 6.80, 7.00,
    7.30, 7.50, 7.80, 8.00, 8.40, 8.70, 9.00, 9.40, 9.60, 9.80,
    10.00,
)

#: `|k − 1| < eps` esetén a kontraszt-lépés TÉTLEN (a natív `0x008f1bd0`
#: korai kilépése) — #904.
_CONTRAST_EPS = 1e-6

#: `_resaturate_table_entry`: hány kompenzáló menet fusson a gamut-levágás
#: után egy-egy táblabejegyzésre. Menetenként legalább egy csatorna
#: véglegesen kifut a tartományból, ezért három menet a három csatornás
#: esetre elég — a negyedik biztonsági tartalék (#3631).
_TINT_GAMUT_PASSES = 4
_TINT_EPSILON = 1e-6
#: A végső csonkolás előtti lebegőpontos zajszűrő — a súlyösszeggel való
#: osztás valódi tizedeseit nem érheti, ezért jóval az 1e-6 alatt van.
_TINT_TRUNC_EPS = 1e-9

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


def _haeberli_luma(image_f: np.ndarray) -> np.ndarray:
    """Haeberli-luminancia (H, W) float32 tömbként — a `Tint` szürkítése
    (#3631) ezt használja, NEM a Rec.601-es `luma`-t."""
    red_w, green_w, blue_w = _HAEBERLI_WEIGHTS
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
    `w = trunc(256α)`, és ha `w > 0`, `w − 1`; `ki = (b·(255−w) + t·w) >> 8`
    — a súlyok összege 255, az osztó 256, tehát két 255-ös bemenetből 254.
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
    kevert = (_bajt(base) * (255 - w) + _bajt(top) * w) >> 8
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


#: Az `AutoFix` LUT-képletének kiolvasott konstansai (#2229):
#: `0x00cf39d0` = 255,0 és `0x00c72150` = 0,5.
_AUTOFIX_SKALA = 255.0
_AUTOFIX_KEREKITES = 0.5

#: A pontminta küszöbe (#3797, `0x00bc2ea6` `cmp eax, 0x3e8`): ennél NEM
#: nagyobb képpontszámnál a teljes kép számít.
_AUTOFIX_MINTA_KUSZOB = 1000


def _autofix_mintameret(szelesseg: int, magassag: int) -> tuple[int, int]:
    """A pontminta rácsmérete 1000 képpont fölött (#3797, `0x00bc2f6a`,
    `0x00bc2fb5`): `s = sqrt(float32(1000 / (w·h)))`,
    `nW = max(1, trunc(w·s + 0,5))`, `nH = max(1, trunc(h·s + 0,5))`.
    960 × 640-nél ez 39 × 26."""
    arany = np.float32(_AUTOFIX_MINTA_KUSZOB / float(szelesseg * magassag))
    s = float(np.sqrt(arany))
    nW = max(1, int(szelesseg * s + 0.5))
    nH = max(1, int(magassag * s + 0.5))
    return nW, nH


def _autofix_hisztogram_forras(image: np.ndarray) -> np.ndarray:
    """A hisztogram forrása: ≤ 1000 képpontnál a teljes kép, fölötte az
    `nW × nH` pontminta (#3797). A `diag(w/nW, h/nH)` mátrix, 16.16
    fixpontban, ugyanazzal a mintavevővel, mint a `QuantizePalette`
    (`render/quantize_palette.py`, `pontminta_racs`)."""
    magassag, szelesseg = image.shape[:2]
    if szelesseg * magassag <= _AUTOFIX_MINTA_KUSZOB:
        return image
    nW, nH = _autofix_mintameret(szelesseg, magassag)
    return pontminta_racs(image, nW, nH, szelesseg / float(nW), magassag / float(nH))


def autofix(image: np.ndarray) -> np.ndarray:
    """`AutoFix`: a Glimmer belső, effekt-csővezetékekben újrahasznált
    automatikus javítása — **vágás nélküli min–max szinthúzás** (#2229).

    ⚠️ **NEM azonos a „Jó napom van"-nal.** A natív parancs
    (`0x009db610`, #535/#721) vágópont-keverést végez; a Glimmer
    `AutoFixImageOperation` **másik kódút**, és a munkavégzője
    (`0x00bc2d70`) mást csinál:

    1. három **egyszerű** 256 rekeszes hisztogram (`0x00bc2e50`) — vágás,
       súlyozás, percentilis **nincs** benne, és 1000 képpont fölött NEM
       a teljes képen, hanem egy pontmintán számol (ld. lent);
    2. csatornánként LUT (`0x00bc3170`), ami viszont a TELJES képre hat:

    ```
    lo = az első nem üres rekesz,  hi = az utolsó nem üres rekesz
    lo == hi  ->  LUT[x] = 255
    egyébként ->  LUT[x] = clamp(trunc((x − lo)/(hi − lo)·255 + 0,5), 0, 255)
    ```

    A `255,0` és a `0,5` konstans kiolvasva (`0x00cf39d0`, `0x00c72150`).

    A különbség nem elméleti: egyetlen kiugró szélső képpont a vágópontos
    modellben eltűnik, itt viszont **meghatározza a tartományt**. Hat
    Glimmer-effekt hívja belül (Holga, NightVision, PencilSketch, Sixties,
    Cinemascope, kétszer a PencilSketch), tehát mindegyik kimenetét
    érinti.

    **A hisztogram mintája (#3797).** 1000 képpont fölött a hisztogram
    NEM a teljes képből, hanem egy `nW × nH` pontmintából épül:
    `s = sqrt(float32(1000/(w·h)))`, `nW = max(1, trunc(w·s + 0,5))`,
    `nH = max(1, trunc(h·s + 0,5))`. A minta legközelebbi szomszéd,
    a mintaképpont közepét (`+0,5`) vetíti vissza a `diag(w/nW, h/nH)`
    mátrixszal, 16.16 fixpontban — ugyanaz a mintavevő, mint a
    `QuantizePalette`-ben (`render/quantize_palette.py`,
    `pontminta_racs`). A ritka szélső képpontok (pl. egy vékony sötét
    vonal) így kimaradnak a tartomány-számításból; a LUT-ot ennek
    ellenére a teljes képre alkalmazzuk. Ld. `docs/specs/filterdesc-registry.md`,
    6/a pont.
    """
    validate_image(image)
    minta = _autofix_hisztogram_forras(image)
    kimenet = np.empty_like(image)
    for csatorna in range(image.shape[2]):
        sik = minta[..., csatorna]
        hasznalt = np.flatnonzero(np.bincount(sik.reshape(-1), minlength=256))
        lo, hi = int(hasznalt[0]), int(hasznalt[-1])
        if lo == hi:
            kimenet[..., csatorna] = 255
            continue
        x = np.arange(256, dtype=np.float64)
        # CSONKOLÁS, nem kerekítés: a natív út a `0x00c29990`-en át megy,
        # ami `cvttsd2si` — trunkál. A `+ 0,5` MAGA a felfelé kerekítés
        # idiómája; `np.round`-dal kétszer kerekítenénk, és a felezőpontok
        # a numpy bankár-kerekítése miatt páros felé csúsznának el
        # (pl. 101,5 -> 102 helyett a natív 101-et ad).
        lut = np.clip(
            np.floor((x - lo) / (hi - lo) * _AUTOFIX_SKALA + _AUTOFIX_KEREKITES),
            0.0,
            255.0,
        ).astype(np.uint8)
        kimenet[..., csatorna] = lut[image[..., csatorna]]
    return kimenet


def _telitettseg_k(saturation: float) -> float:
    """A Haeberli-mátrix `k` erősítése (#903, `0x008f1d00`) — a csúszka
    ASZIMMETRIKUS: a pozitív oldal háromszoros skálázást kap, a negatív
    nem. `+100 → k=4,0`, `-100 → k=0,0` (teljes szürke)."""
    if saturation > 0:
        return 1.0 + (saturation * 3.0) / 100.0
    return 1.0 + saturation / 100.0


def _saturation_matrix(saturation: float) -> np.ndarray:
    """A `SimpleColorMatrix` telítettség-ágának teljes 3×3 Haeberli-
    színmátrixa (#903). A luminancia-súlyok 0,3086/0,6094/0,0820 —
    NEM Rec.601 (ld. `_HAEBERLI_WEIGHTS` docstringje)."""
    k = _telitettseg_k(saturation)
    w = 1.0 - k
    red_w, green_w, blue_w = _HAEBERLI_WEIGHTS
    rw, gw, bw = w * red_w, w * green_w, w * blue_w
    return np.array(
        [
            [k + rw, gw, bw],
            [rw, k + gw, bw],
            [rw, gw, k + bw],
        ],
        dtype=np.float32,
    )


def _kontraszt_gorbe(c: float) -> float:
    """`kontraszt_gorbe` (#904, `0x008f2990`): negatív oldalon zárt képlet
    (`c/100`), pozitív oldalon a 101 elemű `_KONTRASZT_TABLA`-ból lineáris
    interpolációval — SEMMILYEN zárt képlet nem illeszkedik rá (a legjobb
    exponenciális illesztés 0,64-gyel téved), ezért a táblát kell átvenni.
    """
    if c == 0.0:
        return 0.0
    if c < 0.0:
        return c / 100.0
    if c >= 100.0:
        return _KONTRASZT_TABLA[100]
    i = int(c)
    f = c - i
    if f < 1e-9:
        return _KONTRASZT_TABLA[i]
    return (1.0 - f) * _KONTRASZT_TABLA[i] + f * _KONTRASZT_TABLA[i + 1]


def _homogen(matrix: np.ndarray | None = None, offset: float = 0.0) -> np.ndarray:
    """4×4-es homogén float32 mátrix: bal felső 3×3 = `matrix` (alap:
    egység), a 4. oszlop első három eleme = `offset`."""
    result = np.eye(4, dtype=np.float32)
    if matrix is not None:
        result[:3, :3] = matrix
    result[:3, 3] = np.float32(offset)
    return result


def _szorzas_x87(gyujto: np.ndarray, uj: np.ndarray) -> np.ndarray:
    """`G ← G × Ú` a natív szorzó (`0x008f28d0`) módján: 4×4-es, float32-ként
    tárolt elemek, x87-FPU. Egy elem: `acc = 0,0` (`[0xcf3a60]`); `l = 0…3`:
    `acc = f32(f64(acc) + f64(G[i,l]) · f64(Ú[l,j]))` — minden részösszeg
    float32-be tárolódik (`fstp dword`), tehát a sorrend és a köztes
    kerekítés számít."""
    result = np.zeros((4, 4), dtype=np.float32)
    for i in range(4):
        for j in range(4):
            acc = np.float32(0.0)
            for n in range(4):
                acc = np.float32(float(acc) + float(gyujto[i, n]) * float(uj[n, j]))
            result[i, j] = acc
    return result


def _kontraszt_matrix(contrast: float) -> np.ndarray | None:
    """A KÜLÖN kontraszt-lépés (#904/#3735, `0x008f1bd0`) homogén mátrixa:
    skála `k`, eltolás `(1-k)·63,5` — a forgáspont **63,5**, nem 128.
    `|k-1| < eps` esetén a lépés tétlen (a natív korai kilépése): `None`."""
    c = float(np.clip(contrast, -100.0, 100.0))
    k = 1.0 + _kontraszt_gorbe(c)
    if abs(k - 1.0) < _CONTRAST_EPS:
        return None
    result = _homogen(np.eye(3, dtype=np.float32) * np.float32(k), (1.0 - k) * 127.0 * 0.5)
    return result


def _fenyero_matrix(brightness: float) -> np.ndarray:
    """A fényerő-lépés (`0x008f1af0`) homogén mátrixa: egység + a fényerő a
    4. oszlopban (KÖZVETLEN additív, nincs ×2,55 skálázás)."""
    return _homogen(None, float(np.clip(brightness, -100.0, 100.0)))


def _kontraszt_fenyero_egyuttes_matrix(contrast: float, brightness: float) -> np.ndarray:
    """A `ContrastAndBrightnessLinked` ág (#904, `0x008f2040`) homogén
    mátrixa — KÜLÖN kódút, nem a különálló kontraszt+fényerő egymás után:
    a forgáspont **127,5**, és a fényerő-tag súlya a kontraszttól függ
    (`(k+1)·127,5/100`)."""
    c = float(np.clip(contrast, -100.0, 100.0))
    b = float(np.clip(brightness, -100.0, 100.0))
    k = 1.0 + _kontraszt_gorbe(c)
    t = ((k + 1.0) * 127.5 * b) / 100.0 + (127.5 - k * 127.5)
    return _homogen(np.eye(3, dtype=np.float32) * np.float32(k), t)


def _szinmatrix_osszefuzve(
    saturation: float | None, contrast: float, brightness: float, linked: bool
) -> tuple[np.ndarray, np.ndarray]:
    """A `SimpleColorMatrix` kész `(3×3 mátrix, 3 eltolás)` párja, a natív
    összefűzés módján (#3951, `docs/specs/filterdesc-registry.md`, #3950):
    `M = S · C · B` (linked: `M = S · L`), a gyűjtő `G ← G × Ú`
    (`_szorzas_x87`: `l = 0…3`, float32 részösszegek). A `S` telítettség
    nélkül egység. A képpontra a fényerő hat előbb, a kontraszt utána, majd a
    telítettség (#3735)."""
    gyujto = _homogen(_saturation_matrix(float(saturation)) if saturation is not None else None)
    if linked:
        if contrast or brightness:
            gyujto = _szorzas_x87(gyujto, _kontraszt_fenyero_egyuttes_matrix(contrast, brightness))
    elif contrast or brightness:
        kontraszt = _kontraszt_matrix(contrast)
        if kontraszt is not None:
            gyujto = _szorzas_x87(gyujto, kontraszt)
        gyujto = _szorzas_x87(gyujto, _fenyero_matrix(brightness))
    return gyujto[:3, :3].copy(), gyujto[:3, 3].copy()


def _fixpont_egyutthato(matrix: np.ndarray) -> np.ndarray:
    """A közös színmátrix-alkalmazó (`0x008f21a0`) együtthatói:
    `c = trunc(m·2048 ± 0,5)` — a `±` az `m` előjele (nullától elfelé
    kerekítés; NEM `rint`, az a felezőpontot páros felé viszi). A szorzás
    float64-ben megy (a natív a `double` konstansokkal, `[0xcf3ba0]` =
    2048,0, `[0xc72150]` = 0,5).

    ⚠️ A natív a `c`-t int16-ként tárolja (`0x008f240f`), tehát `|c| < 32768`,
    azaz `|m| < 16`. A mai presetekben `|m| ≤ ~10,5` (a telítettség- és a
    kontraszt-csúszka szélső, egyidejű állásában — pl. `s = c = 100` — a
    mátrix ezt meghaladná; ott a natív is csonkolna, ezt NEM utánozzuk,
    és nem is `assert`-eljük, hogy egy szélső csúszkaállás ne dobjon
    kivételt)."""
    scaled = np.asarray(matrix, dtype=np.float64) * 2048.0
    return np.trunc(scaled + np.where(scaled < 0.0, -0.5, 0.5)).astype(np.int64)


def _fixpont_bias(offset: np.ndarray) -> np.ndarray:
    """A közös alkalmazó eltolása (`0x008f2448`): `b = trunc(eltolás·4 ± 0,5)
    + 2` — a `+2` a végső `>> 2` kerekítése (`add eax, 2` @ `0x008f2469`)."""
    scaled = np.asarray(offset, dtype=np.float64) * 4.0
    return np.trunc(scaled + np.where(scaled < 0.0, -0.5, 0.5)).astype(np.int64) + 2


def _fixpontos_szinmatrix(image: np.ndarray, matrix: np.ndarray, offset: np.ndarray) -> np.ndarray:
    """A közös FIXPONTOS színmátrix-alkalmazó (#3930/#3950/#3951,
    `0x008f2500` → `0x008f2640`), a `SimpleColorMatrix`, a `Tint` szürkítése
    és a `BW` közös útja. A lebegőpontos `matrix` (`n × 3`) és `offset`
    (`n`) egész együtthatókra váltva (`_fixpont_egyutthato`, `_fixpont_bias`),
    képpontonként:

        ki_i = clamp((Σ_j ((c_ij · x_j) >> 9) + b_i) >> 2, 0, 255)

    A `>> 9` MINDEN taggal külön fut (előjeles, lefelé), az összeg a
    biasszal indul. Bemenet `uint8` RGB, kimenet `uint8` `(H, W, n)`."""
    coeffs = _fixpont_egyutthato(matrix)
    bias = _fixpont_bias(offset)
    pixels = image.astype(np.int64)
    out = np.empty(image.shape[:2] + (coeffs.shape[0],), dtype=np.uint8)
    for row in range(coeffs.shape[0]):
        acc = ((pixels * coeffs[row]) >> 9).sum(axis=-1) + bias[row]
        out[..., row] = np.clip(acc >> 2, 0, 255)
    return out


def simple_color_matrix(
    image: np.ndarray,
    brightness: float = 0.0,
    contrast: float = 0.0,
    saturation: float | None = None,
    linked: bool = False,
) -> np.ndarray:
    """`SimpleColorMatrix`: telítettség (Haeberli-színmátrix, #903 —
    `saturation=None` → nem érinti), majd — `linked` szerint — VAGY egy
    közös `ContrastAndBrightnessLinked` lépés (127,5-ös forgáspont), VAGY
    a fényerő (KÖZVETLEN additív, nincs ×2,55 skálázás) és a kontraszt
    (101 elemű táblázatos görbe, 63,5-ös forgáspont, korai kilépés kis
    `k`-nál) EGYÜTT, `out = k·(x+b) + (1-k)·63,5` alakban — a képpontra a
    fényerő hat ELŐBB, a kontraszt UTÁNA (#3735, ld. `_kontraszt_matrix`
    és `_szinmatrix_osszefuzve` docstringje). A `brightness` és a `contrast` is `[-100..100]`-ra vágva,
    a natív mintájára.
    """
    validate_image(image)
    matrix, offset = _szinmatrix_osszefuzve(saturation, contrast, brightness, linked)
    return _fixpontos_szinmatrix(image, matrix, offset)


#: A `LocalContrast` Gauss-szigmája a `Radius` csúszka FELE (#545). A
#: `referencia/hdrish/` négy Radius-állása egymástól függetlenül ezt adta
#: (a 2560 széles képen mérve, a legkisebb vödrön-belüli szórásra
#: illesztve):
#:
#:     Radius =  1,3 (min)  ->  szigma  1,6
#:     Radius = 20   (alap) ->  szigma  9,6
#:     Radius = 40   (mid)  ->  szigma 19,2
#:     Radius = 80   (max)  ->  szigma 38,4
#:
#: Ugyanaz a 2-es szorzó, mint a Vignette/MuseumMatte/Orton elmosásainál
#: (#317) — a Flash-örökségű sugár-paraméter és a Gauss-szigma között.
#:
#: ⚠️ #3520: a `HDR` és a `LocalContrast` MÁR NEM Gauss-szal mos, hanem a
#: natív `BlurImageOperation`-nel (`quality = 3`,
#: `render/nativ_blur.blur_image_operation`). A felezés
#: (`σ² = 3(w²−1)/12`, nagy `w`-re `σ ≈ w/2`) abból magától adódik; ez a
#: megjegyzés a #545 mérésének dokumentuma.


def _szorzott_resz(kulonbseg: np.ndarray, strength: float) -> np.ndarray:
    """`Blend … Subtract` + `MultiplyColorMatrix`: a telítő (0-ra vágott)
    különbség `strength`-szerese, 8 bitre kerekítve és vágva."""
    resz = np.clip(kulonbseg, 0.0, 255.0) * np.float32(strength)
    return np.clip(np.rint(resz), 0.0, 255.0)


def _elmosott(image: np.ndarray, radius: float) -> np.ndarray:
    return blur_image_operation(image, radius, radius, quality=3).astype(np.float32)


def hdr_local_contrast(image: np.ndarray, radius: float, strength: float) -> np.ndarray:
    """A natív `glimmer::LocalContrastImageOperation` (lánc-építő
    `0x00bc41e0`, #3520) — a `HDR` motorja. A lánc az EREDETIBŐL indul::

        a  = sat(be + sat(C · sat(be − elm)))
        ki = sat(a  − sat(C · sat(elm − be)))

    azaz `ki = be + C·(be − elm)`, 8 biten lépésenként vágva. `C = 1`-nél
    sem azonosság. Az elmosás a natív `BlurImageOperation(R, R, 3)`, ami az
    1,3-as sugárral is mos. Bemenet és kimenet `uint8` RGB.
    """
    be = image.astype(np.float32)
    elm = _elmosott(image, radius)
    a = np.clip(be + _szorzott_resz(be - elm, strength), 0.0, 255.0)
    ki = np.clip(a - _szorzott_resz(elm - be, strength), 0.0, 255.0)
    return ki.astype(np.uint8)


def xml_local_contrast(image: np.ndarray, radius: float, strength: float) -> np.ndarray:
    """A `filterdesc.xml` `LocalContrast` lánca (#3520) — az ELMOSOTTBÓL
    indul::

        a  = sat(elm − sat(C · sat(elm − be)))
        ki = sat(a   + sat(C · sat(be − elm)))

    azaz `ki = elm + C·(be − elm)`; `C = 1`-nél bitre azonosság (#688).
    Az elmosás a natív `BlurImageOperation(R, R, 3)`. `uint8` RGB be és ki.
    """
    be = image.astype(np.float32)
    elm = _elmosott(image, radius)
    a = np.clip(elm - _szorzott_resz(elm - be, strength), 0.0, 255.0)
    ki = np.clip(a + _szorzott_resz(be - elm, strength), 0.0, 255.0)
    return ki.astype(np.uint8)


# --- Zaj (Noise) ---------------------------------------------------------


def noise_layer(
    height: int,
    width: int,
    seed: int,
    low: float,
    high: float,
    grayscale: bool,
    channel_options: int = ALAP_CSATORNAK,
) -> np.ndarray:
    """`Noise`: a `NoiseImageOperation` natív zajrétege float32 [0,255] —
    MT19937 a Picasa 1664525-ös magvetésével, képpontonként egy húzás
    (#3736, ld. `nativ_noise.noise_layer`). Adott `seed` → a Picasáéval
    képpontra azonos zajminta.
    """
    return nativ_noise.noise_layer(height, width, seed, low, high, grayscale, channel_options)


def _blend_noise(
    image: np.ndarray, noise: np.ndarray, blend_alpha: float, blend_mode: BlendMode | int
) -> np.ndarray:
    return to_uint8(apply_blend_mode(to_float(image), noise, blend_mode, blend_alpha))


def apply_noise(
    image: np.ndarray,
    seed: int,
    low: float,
    high: float,
    grayscale: bool,
    blend_alpha: float,
    blend_mode: BlendMode | int,
) -> np.ndarray:
    """A natív zajréteg generálása és `blend_mode`/`blend_alpha` szerinti
    keverése (a lánc `NoiseImageOperation`-je, #3736). A `blend_mode` név
    vagy a natív módtábla sorszáma (`BLEND_MODE_BY_INDEX`)."""
    validate_image(image)
    height, width = image.shape[:2]
    noise = noise_layer(height, width, seed, low, high, grayscale)
    return _blend_noise(image, noise, blend_alpha, blend_mode)


# --- Gradiens-leképezés (GradientMap / HSVGradientMap) ------------------


#: #3421: a gradiens-LUT-ok INDEXE a képpont piros csatornája. A
#: `GradientMap` (`0x00bb87b0`) és a `HSVGradientMap` (`0x00bbc260`)
#: építője a színtáblát a közös futószalag (`0x00bcb2f0`) `+0x800`
#: rekeszébe írja (a BGRA `src[2]` bájtja), a másik kettőt nullázza — a
#: kimenet tehát csak a piros csatornától függ, nem a lumától.
_GRADIENS_INDEX_CSATORNA = 0


def _gradient_map_stop_positions(n: int) -> np.ndarray:
    """A `GradientMap` float32 stophelyei (#4090, #4092)."""
    positions = np.empty(n, dtype=np.float32)
    positions[0] = np.float32(0.0)
    for k in range(1, n - 1):
        # A natív kód double 255,0-val szoroz/oszt, majd dword floatba tárol.
        positions[k] = np.float32((k * 255.0) / (n - 1))
    positions[-1] = np.float32(255.0)
    return positions


def _gradient_map_weight(p_lo: float, p_hi: float, x: int) -> np.float32:
    """Az x87-hányados dword float32 tárolt súlya (#4090)."""
    x_f32 = np.float32(x)
    return np.float32((float(p_hi) - float(x_f32)) / (float(p_hi) - float(p_lo)))


def _gradient_map_interpolate_channel(
    lower: int, upper: int, p_lo: float, p_hi: float, x: int
) -> int:
    """Egy csatorna natív, float32 súlyú és `+0,5`-ös keverése."""
    weight = _gradient_map_weight(p_lo, p_hi, x)
    value = int(upper) + float(weight) * (int(lower) - int(upper))
    return max(0, min(255, math.trunc(value + 0.5)))


def gradient_map(image: np.ndarray, colors: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """`GradientMap`: a piros csatornából natív RGB-megálló-LUT-ot épít.

    A megállóhelyek és a csatornánkénti interpoláció a #4090/#4092 spec
    képletét követi; `colors` sorrendje **RGB** (#510). Az index továbbra
    is a képpont PIROS csatornája (#3421). A natív `< 8` bitminta-kapu a
    generált 0…255 LUT-on nem változtat elemet (n=2…256, 0/65 280), ezért
    nincs külön átvezetve.
    """
    validate_image(image)
    if len(colors) < 2:
        raise ValueError("Legalább két szín kell a gradienshez")
    positions = _gradient_map_stop_positions(len(colors))
    lut = np.empty((256, 3), dtype=np.uint8)
    for x in range(256):
        stop_lo = int(np.searchsorted(positions, np.float32(x), side="right")) - 1
        if stop_lo < 0:
            lut[x] = colors[0]
        elif stop_lo >= len(colors) - 1:
            lut[x] = colors[-1]
        else:
            p_lo = positions[stop_lo]
            p_hi = positions[stop_lo + 1]
            for channel in range(3):
                lut[x, channel] = _gradient_map_interpolate_channel(
                    colors[stop_lo][channel], colors[stop_lo + 1][channel], p_lo, p_hi, x
                )
    return lut[image[..., _GRADIENS_INDEX_CSATORNA]]


def _hsv_rgb_lut_f32(hue: np.ndarray, sat: np.ndarray, val: np.ndarray) -> np.ndarray:
    """A natív HSV → RGB (`0x00bbbe20`, #3814): float32 köztes értékek,
    `h` körbe `[0, 360)`-ba, `s`/`v` százalékban `[0, 100]`-ra szorítva,
    hatodolás, és a végén csatornánként `csonk(x · 255)` — nincs +0,5.
    Spec: `docs/specs/filterdesc-registry.md`, „A HSV → RGB átalakítás".
    """
    f32 = np.float32
    h = np.mod(hue.astype(f32), f32(360.0))
    s = np.clip(sat.astype(f32), 0, 100) / f32(100.0)
    v = np.clip(val.astype(f32), 0, 100) / f32(100.0)
    h6 = (h / f32(360.0)) * f32(6.0)
    i = np.trunc(h6).astype(np.int64)
    f = h6 - i.astype(f32)
    p = v * (f32(1.0) - s)
    q = v * (f32(1.0) - f * s)
    t = v * (f32(1.0) - s * (f32(1.0) - f))
    szektor = i % 6
    r = np.choose(szektor, (v, q, p, p, t, v))
    gr = np.choose(szektor, (t, v, v, q, p, p))
    b = np.choose(szektor, (p, p, t, v, v, q))
    rgb = np.stack([r, gr, b], axis=-1).astype(np.float64) * 255.0
    return np.clip(np.trunc(rgb), 0, 255).astype(np.uint8)


def hsv_gradient_map(
    image: np.ndarray,
    stops: tuple[tuple[float, float, float, float], ...],
    hue_offset: float = 0.0,
) -> np.ndarray:
    """`HSVGradientMap`: a PIROS csatornához (#3421) rendelt (pozíció,
    hue°, sat%, val%) töréspontok interpolációja HSV-térben, majd RGB-re
    konvertálva — a `HeatMap` effekt implementációja.

    #3814: az RGB-re alakítás a natív lebegőpontos képlettel, csonkolva
    történik (`_hsv_rgb_lut_f32`); a `hueOffset` float32-ben adódik a
    keverés utáni színezethez, a körbefordítást az átalakító végzi.
    """
    validate_image(image)
    positions = np.array([stop[0] for stop in stops], dtype=np.float64)
    hues = np.array([stop[1] for stop in stops], dtype=np.float64)
    sats = np.array([stop[2] for stop in stops], dtype=np.float64)
    vals = np.array([stop[3] for stop in stops], dtype=np.float64)
    idx = np.arange(256, dtype=np.float64)
    hue_lut = np.interp(idx, positions, hues).astype(np.float32) + np.float32(hue_offset)
    sat_lut = np.interp(idx, positions, sats)
    val_lut = np.interp(idx, positions, vals)
    rgb_lut = _hsv_rgb_lut_f32(hue_lut, sat_lut, val_lut)
    return rgb_lut[image[..., _GRADIENS_INDEX_CSATORNA]]


# --- Térbeli maszkok -------------------------------------------------------


def circular_gradient_mask(
    height: int,
    width: int,
    inner_radius: float,
    outer_radius: float,
    center: tuple[float, float] | None = None,
    inner_alpha: float = 0.0,
    outer_alpha: float = 1.0,
) -> np.ndarray:
    """`CircularGradient`: (H, W) float32 [0,1] maszk — `inner_alpha` az
    `inner_radius`-on belül (védett, „éles" zóna), `outer_alpha` az
    `outer_radius`-on túl, lineárisan a kettő között. `center` alapból a kép
    közepe, pixel-egységben.

    #3958: a maszk az eredeti szerint 16 bites pozícióval, egész
    koordinátával és megálló-táblával számol (`R = max(inner, outer)`), a
    kimenet egész bájtokból (`alfa / 255`) áll. `outer <= inner` esetén a
    spec képlete is érvényes (`R = max` miatt `p₁ = 255`, a fordított alfa
    `trunc`-kal csonkol); a korábbi kemény lépcsőt csak azért tartjuk meg,
    mert `inner = outer = 0` mellett az új út nullával osztana. Egyedül a
    páratlan méret középpontja (`cx = W/2`) nem rögzített.

    #788: a két alfa a natív `CircularGradientImageMask`
    `innerAlpha`/`outerAlpha` attribútuma; az alapértékek a KIOLVASOTT
    tartalékok (`0,0` → `1,0`), tehát az alapeset változatlan. A natív olvasó
    mindkettőt `[0,1]`-re vágja (`0x00bd0391`, `0x00bd03e1`).

    ⚠️ **`aspectRatio` SZÁNDÉKOSAN nem paraméter.** A 283. kutatói kör
    kimérte, hogy a tartaléka `1,0`, és a `filterdesc.xml` mind a négy
    használatban elhagyja — a maszk tehát KÖR, és a `np.hypot` helyes. A nem
    1,0-s eset geometriája NINCS kimérve, ezért egy ilyen paraméter csak
    találgatást hordozhatna (`docs/specs/filters-decoded.md`).
    """
    cx, cy = center if center is not None else (width / 2.0, height / 2.0)
    belso = float(np.clip(inner_alpha, 0.0, 1.0))
    kulso = float(np.clip(outer_alpha, 0.0, 1.0))
    if outer_radius <= inner_radius:
        # A spec képlete erre is érvényes, de `inner = outer = 0` mellett az
        # új út `R = 0`-val osztana: ezért marad a korábbi kemény lépcső (a
        # hívók, `Lomo` és `Holga`, ide sosem jutnak).
        ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
        dist = np.hypot(xs + 0.5 - cx, ys + 0.5 - cy)
        arany = (dist >= inner_radius).astype(np.float32)
        return (np.float32(belso) + arany * np.float32(kulso - belso)).astype(np.float32)
    tabla = _kormaszk_megallo_tabla(inner_radius, outer_radius, belso, kulso)
    pozicio = _kormaszk_pozicio(height, width, cx, cy, outer_radius)
    rekesz = pozicio >> 8
    tort = pozicio & 0xFF
    alfa = (tabla[rekesz + 1] * tort + tabla[rekesz] * (256 - tort)) >> 8
    return (alfa.astype(np.float32) / np.float32(255.0)).astype(np.float32)


#: A körmaszk pozíciójának teljes skálája (`0xff00`, 16 bites; a Flash
#: színátmenet 255 rekesze × 256).
_KORMASZK_POZICIO_MAX = 0xFF00


def _kormaszk_megallo_tabla(
    inner_radius: float, outer_radius: float, inner_alpha: float, outer_alpha: float
) -> np.ndarray:
    """A `CircularGradientImageMask` 257 elemű megálló-táblája (`0x008f3700`,
    #3957): `p₁ = csonk(255·inner/R)`, `T[i] = csonk(a₀ + (a₁−a₀)·f32((i−p₁)/
    (255−p₁)))` a `p₁ ≤ i < 255` rekeszekre, `a₀` előtte, `a₁` 255-től 256-ig.
    """
    sugar = max(inner_radius, outer_radius)
    a0 = int(np.trunc(255.0 * inner_alpha))
    a1 = int(np.trunc(255.0 * outer_alpha))
    p1 = int(np.trunc(255.0 * inner_radius / sugar))
    tabla = np.full(257, a0, dtype=np.int64)
    if p1 < 255:
        i = np.arange(p1, 255)
        arany = ((i - p1).astype(np.float32) / np.float32(255 - p1)).astype(np.float64)
        tabla[p1:255] = np.trunc(a0 + (a1 - a0) * arany).astype(np.int64)
    tabla[255:] = a1
    return tabla


def _kormaszk_tavolsag(
    height: int, width: int, cx: float, cy: float, sugar: float
) -> np.ndarray:
    """A pozíció kerekítés előtti értéke, `√(u²+v²)`, float32-ben (`sqrtps`,
    egyszeres pontosság — a spec rögzíti). Az `u`/`v` float64-ben képződik,
    és float32-re csonkul; az `u²+v²` összeg és a gyök már float32."""
    skala = _KORMASZK_POZICIO_MAX / sugar
    u = ((np.arange(width, dtype=np.float64) - cx) * skala).astype(np.float32)
    v = ((np.arange(height, dtype=np.float64) - cy) * skala).astype(np.float32)
    return np.sqrt(v[:, np.newaxis] * v[:, np.newaxis] + u[np.newaxis, :] * u[np.newaxis, :])


def _kormaszk_pozicio(
    height: int, width: int, cx: float, cy: float, sugar: float
) -> np.ndarray:
    """A 16 bites pozíció (`0x008f3970`, #3957): `u = (x−cx)·65280/R` EGÉSZ
    képpontindexből (nincs `+0,5`), `P = min(round(√(u²+v²)), 0xff00)` —
    az SSE2-ág (`sqrtps` + `cvtps2dq`) legközelebbire kerekít.

    Rögzített (spec): a `√` egyszeres pontosságú (float32), a `rint` a
    float32 eredményen fut. NEM rögzített: az `u`/`v` képzésének pontos alakja
    (a bináris a befoglaló téglalapot a `1638,4`-es Flash-egységre képezi, és
    `79,6875`-tel szoroz; mi `(x−cx)·65280/R`-t használunk float64-ben, majd
    float32-re váltunk). A két alak néhány ezer képpontban egy egységgel
    eltérhet."""
    tavolsag = _kormaszk_tavolsag(height, width, cx, cy, sugar)
    return np.minimum(np.rint(tavolsag), _KORMASZK_POZICIO_MAX).astype(np.int64)


def tint_multiply(image: np.ndarray, color: tuple[int, int, int], alpha: float) -> np.ndarray:
    """`Tint(Color=..., BlendMode=multiply)`: szorzó-színezés `alpha` súllyal.

    `color` csatornasorrendje **ugyanaz, mint a `image` tömbé** — ez a
    modul (és a teljes `render/chain.py` csővezeték, ld. a modul-docstring
    tetejét) **RGB**-terű, NEM BGR: `color[0]` = R, `color[1]` = G,
    `color[2]` = B. A `filterdesc.xml` hex színeit (`0xRRGGBB`) ezért
    közvetlenül, csere nélkül `(R, G, B)` sorrendben kell megadni. A
    BGR/RGB keveredés (#510) csak a modulhatárokon (pl. `cv2.imread`
    kimenete, `export/exporter.py::_apply_filter_chain`) számít, ahol a
    hívó `cv2.cvtColor(..., COLOR_BGR2RGB/RGB2BGR)`-rel konvertál.
    """
    validate_image(image)
    image_f = to_float(image)
    color_layer = np.empty_like(image_f)
    color_layer[..., 0] = color[0]
    color_layer[..., 1] = color[1]
    color_layer[..., 2] = color[2]
    return to_uint8(apply_blend_mode(image_f, color_layer, "multiply", alpha))


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


#: A Mitchell–Netravali mag paraméterei: **B = C = 0,4** (#2227). Az eredeti
#: `ResizeImageOperation` alkalmazója (`0x00bc3650`) a `0x00bcb5e0`
#: segédfüggvényt hívja, az pedig a `ytResampler`-t explicit móddal: a
#: vízszintes cél/forrás lépték `≤ 1` → 0-s (doboz), egyébként 3-as
#: (Mitchell–Netravali). Spec: `filterdesc-registry.md`, 5/c (#3805).
_MITCHELL_B = 0.4
_MITCHELL_C = 0.4

#: A fixpontos súlyok egysége: a súlyok összege mindig ennyi, a kimenet
#: `(Σ w·p + 255) >> 14` (`0x00a4031f`: 1,0 × `[0x00cf3b70]` = 16383,0).
_RESIZE_EGYSEG = 16383
_RESIZE_ELTOLAS = 14
_RESIZE_KEREKITO = 255
#: Az alkalmazó a `0x3fffff` fölötti összeget vágja (`0x00a427b0`–`0x00a4283a`).
_RESIZE_FELSO = 0x3FFFFF


def mitchell_netravali(x: np.ndarray) -> np.ndarray:
    """A Mitchell–Netravali rekonstrukciós mag `B = C = 0,4`-gyel.

    A klasszikus alak (Mitchell & Netravali, 1988), `|x|` szerint:

        |x| < 1:  ((12−9B−6C)|x|³ + (−18+12B+6C)|x|² + (6−2B)) / 6
        1 ≤ |x| < 2:  ((−B−6C)|x|³ + (6B+30C)|x|² + (−12B−48C)|x| + (8B+24C)) / 6
        egyébként: 0

    `B = C = 0,4` mellett az **oldallebeny negatív** (1 és 2 között) — ez a
    mag azonosító jegye: éles élen enyhe alul-/túllövést ad, amit a doboz
    nem produkál. A határ kizáró: `|x| ≥ 2` → 0 (`0x00a3fcde`).
    """
    tav = np.abs(np.asarray(x, dtype=np.float64))
    b, c = _MITCHELL_B, _MITCHELL_C
    belso = (
        (12 - 9 * b - 6 * c) * tav**3
        + (-18 + 12 * b + 6 * c) * tav**2
        + (6 - 2 * b)
    ) / 6.0
    kulso = (
        (-b - 6 * c) * tav**3
        + (6 * b + 30 * c) * tav**2
        + (-12 * b - 48 * c) * tav
        + (8 * b + 24 * c)
    ) / 6.0
    return np.where(tav < 1, belso, np.where(tav < 2, kulso, 0.0))


def lanczos3(x: np.ndarray) -> np.ndarray:
    """A Lanczos-3 mag (`ytResampler` 5-ös mód, `0x00a3fdf5`, #3998):
    `|x| >= 3` → 0, egyébként `sinc(π|x|) · sinc(π|x|/3)`. Az oldallebenyek
    negatívak (1 és 2 között), a sugár 3."""
    tav = np.abs(np.asarray(x, dtype=np.float64))
    return np.where(tav < 3.0, np.sinc(tav) * np.sinc(tav / 3.0), 0.0)


def _tengely_sulyok(
    be_meret: int, ki_meret: int, doboz: bool, lanczos: bool = False
) -> tuple[np.ndarray, np.ndarray]:
    """Egy tengely csapindexei és EGÉSZ súlyai, a `ytResampler` szerint.

    Spec 5/b–5/c (`0x00a3f660`): a csap helye `j + 0,5`, a kimeneti képpont
    középpontja `c = (i + 0,5) · forrás/cél` (float32). A mag kicsinyítéskor
    a léptékkel nyúlik (`nyujtas = max(1, forrás/cél)`, `0x00a3f74b`):

    * **doboz** (0-s mód): súly 1, ha `|x| < 0,5` — a határon álló csap nem
      számít (`0x00a3fb12`);
    * **Mitchell** (3-as mód): `B = C = 0,4`, `|x| < 2`;
    * **Lanczos-3** (5-ös mód, `lanczos=True`, #3998): `|x| < 3`.

    Az egész súly `csonk(w · 16383 / Σw)` (`0x00a4035d`), a maradékot
    (`16383 − Σ`) a `csonk(c)` indexű csap kapja, a csaptartományba
    szorítva (`0x00a40462`–`0x00a4049f`). A képen kívüli csap nem kerül a
    listába. Visszaad: `(indexek, sulyok)`, mindkettő `(ki_meret, ablak)`
    alakú; a lista végét 0 súlyú, érvényes indexű csapok töltik ki.

    ⚠️ Ha a dobozban egyetlen csap sincs (nagyításnál `c` pontosan egy
    képponthatárra esik), a teljes súly a `csonk(c)` csapé. Ezt az esetet a
    bináris nem mérte ki; a maradék-szabály folytatása.
    """
    skala = np.float32(be_meret) / np.float32(ki_meret)
    nyujtas = max(1.0, float(skala))
    sugar = (0.5 if doboz else 3.0 if lanczos else 2.0) * nyujtas
    kozep = ((np.arange(ki_meret, dtype=np.float32) + np.float32(0.5)) * skala).astype(np.float64)
    elso = np.floor(kozep - sugar - 0.5).astype(np.int64)
    ablak = int(np.ceil(2 * sugar)) + 2
    indexek = elso[:, None] + np.arange(ablak)[None, :]
    tav = indexek + 0.5 - kozep[:, None]
    ervenyes = (np.abs(tav) < sugar) & (indexek >= 0) & (indexek < be_meret)
    if doboz:
        nyers = ervenyes.astype(np.float64)
    else:
        mag = lanczos3 if lanczos else mitchell_netravali
        nyers = np.where(ervenyes, mag(tav / nyujtas), 0.0)
    osszeg = nyers.sum(axis=1, keepdims=True)
    osztott = np.divide(
        nyers * _RESIZE_EGYSEG, osszeg, out=np.zeros_like(nyers), where=osszeg != 0
    )
    sulyok = np.trunc(osztott).astype(np.int32)
    # a maradék a `csonk(c)` csapé, az érvényes csaptartományba szorítva
    van = ervenyes.any(axis=1)
    also = np.where(van, np.argmax(ervenyes, axis=1), 0)
    felso = np.where(van, ablak - 1 - np.argmax(ervenyes[:, ::-1], axis=1), ablak - 1)
    cel = np.trunc(kozep).astype(np.int64)
    cel = np.where(van, cel, np.clip(cel, 0, be_meret - 1)) - elso
    cel = np.clip(np.where(van, np.clip(cel, also, felso), cel), 0, ablak - 1)
    sorok = np.arange(ki_meret)
    sulyok[sorok, cel] += _RESIZE_EGYSEG - sulyok.sum(axis=1)
    return np.clip(indexek, 0, be_meret - 1), sulyok


def _tengely_menten(
    kep: np.ndarray,
    ki_meret: int,
    tengely: int,
    doboz: bool,
    lanczos: bool = False,
    kerekito_oszlopok: np.ndarray | None = None,
) -> np.ndarray:
    """Fixpontos tengelymenet; a függőleges `W mod 4` farkat a #4004 szerint számolja."""
    be_meret = kep.shape[tengely]
    if (doboz or lanczos) and ki_meret == be_meret:
        # 1:1-es menet: a középső csap súlya 16383 (a Lanczos többi csapja az
        # egész távolságokon 0) — `(16383·p + 255) >> 14 = p`
        return kep
    indexek, sulyok = _tengely_sulyok(be_meret, ki_meret, doboz, lanczos)
    alak = [1] * kep.ndim
    alak[tengely] = ki_meret
    gyujto = np.zeros(
        kep.shape[:tengely] + (ki_meret,) + kep.shape[tengely + 1:], dtype=np.int32
    )
    for k in range(sulyok.shape[1]):
        oszlop = sulyok[:, k]
        if not oszlop.any():
            continue
        gyujto += np.take(kep, indexek[:, k], axis=tengely).astype(np.int32) * oszlop.reshape(alak)
    if tengely == 0:
        # A ytResampler függőleges főciklusa négy oszloponként indul, és itt
        # kapja meg a +255-öt. A sor végén maradó W mod 4 oszlop skalár
        # farkában a Picasa nem ad hozzá kerekítőtagot.
        if kerekito_oszlopok is None:
            kerekito_oszlopok = np.arange(gyujto.shape[1]) < (gyujto.shape[1] & ~3)
        elif kerekito_oszlopok.shape != (gyujto.shape[1],):
            raise ValueError("A függőleges kerekítőmaszk szélessége eltér a bemenetétől")
        alak_kerekito = (1, gyujto.shape[1]) + (1,) * (gyujto.ndim - 2)
        kerekito = np.where(kerekito_oszlopok, _RESIZE_KEREKITO, 0).reshape(alak_kerekito)
        gyujto += kerekito
    else:
        gyujto += _RESIZE_KEREKITO
    np.clip(gyujto, 0, _RESIZE_FELSO, out=gyujto)
    return (gyujto >> _RESIZE_ELTOLAS).astype(np.uint8)


def resize_image(
    image: np.ndarray,
    width: int,
    height: int,
    smoothing: bool = True,
    lanczos3: bool = False,
) -> np.ndarray:
    """`Resize`: a kép átméretezése.

    `smoothing=True` (az alapérték, mérve: `0x00bc36ac`) a `ytResampler`-t
    futtatja (spec `filterdesc-registry.md`, 5/c, #3805):

    * **A mód a VÍZSZINTES cél/forrás léptékből** (`0x00bcb629`–`0x00bcb659`):
      `≤ 1` (kicsinyítés vagy 1:1) → **doboz**, egyébként
      **Mitchell–Netravali B = C = 0,4**. Ugyanaz a mód fut MINDKÉT
      tengelyen — a függőleges nagyítás kicsinyítő szélesség mellett is
      dobozzal, a függőleges kicsinyítés nagyító szélesség mellett is
      Mitchell-lel.
    * **Fixpontos súlyok**: `csonk(w · 16383 / Σw)`, a maradék a `csonk(c)`
      csapé (`_tengely_sulyok`).
    * **Kimenet**: a vízszintes menetben csatornánként `(Σ w·p + 255) >> 14`;
      a függőleges menet négyes főciklusa ugyanezt használja, a sor utolsó
      `W mod 4` oszlopa viszont `(Σ w·p) >> 14` szerint készül (#4004). Az
      értékek 0..255-re szorítódnak. Előbb a vízszintes menet fut, 8 bites köztes
      képpel, utána a függőleges.

    `lanczos3=True` a 5-ös mód (#3998, spec 16. H) 3.): mindkét tengelyen
    Lanczos-3 (`lanczos3`), a többi lépés ugyanaz. Az EXIF-bélyegkép használja.

    `smoothing=False` a 9-es, legközelebbi-szomszéd ág (mérve, 5/a):
    `INTER_NEAREST`.
    """
    validate_image(image)
    width = max(1, int(round(width)))
    height = max(1, int(round(height)))
    if not smoothing:
        return cv2.resize(image, (width, height), interpolation=cv2.INTER_NEAREST)
    return _ytresampler(image, width, height, lanczos3)


def resize_plane(plane: np.ndarray, width: int, height: int) -> np.ndarray:
    """Egyetlen `HxW` uint8 sík átméretezése ugyanazzal a `ytResampler`-rel.

    A belső ragyogás a súlyát így nagyítja vissza (#3827): a natív kód a
    négy bájtot egymástól függetlenül, azonos súlyokkal méretezi, és a
    ragyogás színe állandó, tehát csak az alfa változik.
    """
    if plane.ndim != 2 or plane.dtype != np.uint8:
        raise ValueError("resize_plane: HxW uint8 tömb kell")
    return _ytresampler(plane, max(1, int(round(width))), max(1, int(round(height))))


def _csap_alairas(oszlop_index: np.ndarray, sulyok: np.ndarray) -> np.ndarray:
    """A kimeneti oszlopok `(oszlop, súly)` aláírása; az egyetlen oszlopra
    eső csapok kanonikus alakot kapnak (`[c, −1, …] + [16383, 0, …]`)."""
    van = sulyok != 0
    index = np.where(van, oszlop_index, -1)
    elso = index[np.arange(index.shape[0]), np.argmax(van, axis=1)]
    egyforma = np.all((index == elso[:, None]) | ~van, axis=1)
    kanon_index = np.full_like(index, -1)
    kanon_index[:, 0] = elso
    kanon_suly = np.zeros_like(sulyok)
    kanon_suly[:, 0] = _RESIZE_EGYSEG
    index = np.where(egyforma[:, None], kanon_index, index)
    suly = np.where(egyforma[:, None], kanon_suly, sulyok)
    return np.concatenate([index, suly], axis=1)


def resize_column_plane(
    oszlopok: np.ndarray, vissza: np.ndarray, width: int, height: int
) -> np.ndarray:
    """`resize_plane(oszlopok[:, vissza], width, height)` — bitre ugyanaz, gyorsabban.

    A sík kevés különböző oszlopból áll (`oszlopok`, `H×n`; `vissza` a `W`
    hosszú oszlopindex). Egy kimeneti oszlopot a vízszintes menet csapjainak
    `(oszlop, súly)` párjai határoznak meg; az azonos párú kimeneti oszlopok
    azonosak, ezért mindkét menet csak a különböző párokra fut, és a teljes
    méretű síkot egyetlen indexelés adja (#3827). Ha egy kimeneti oszlop
    minden nem nulla súlyú csapja ugyanarra az oszlopra esik, a kimenet maga
    az az oszlop (a súlyok összege 16383, `(16383·p + 255) >> 14 = p`), ezért
    ezek egy közös párt kapnak. A #4004 függőleges sorvégi maradékát a teljes
    kimeneti szélességhez igazítja, ezért két kerekítési változatot is tárol.
    """
    magas, be_szeles = oszlopok.shape[0], vissza.size
    width = max(1, int(round(width)))
    height = max(1, int(round(height)))
    doboz = width <= be_szeles
    if width == be_szeles:
        kulonbozo, kimeneti = oszlopok, vissza
    else:
        indexek, sulyok = _tengely_sulyok(be_szeles, width, doboz)
        alairas = _csap_alairas(vissza[indexek], sulyok)
        parok, kimeneti = np.unique(alairas, axis=0, return_inverse=True)
        csapok = indexek.shape[1]
        gyujto = np.full((magas, parok.shape[0]), _RESIZE_KEREKITO, dtype=np.int32)
        for k in range(csapok):
            sor_suly = parok[:, csapok + k].astype(np.int32)
            gyujto += oszlopok[:, parok[:, k]].astype(np.int32) * sor_suly
        np.clip(gyujto, 0, _RESIZE_FELSO, out=gyujto)
        kulonbozo = (gyujto >> _RESIZE_ELTOLAS).astype(np.uint8)
    kimeneti = np.asarray(kimeneti).reshape(-1)
    # A sorvégi szabály a teljes kimeneti W-hez igazodik, nem a tömör
    # oszloppárok darabszámához. Egy pár belső és maradék oszlopban is
    # megjelenhet, ezért a két kerekítési változatot külön tartjuk.
    teljes_kerekites = _tengely_menten(
        kulonbozo,
        height,
        0,
        doboz,
        kerekito_oszlopok=np.ones(kulonbozo.shape[1], dtype=bool),
    )
    kimenet = teljes_kerekites[:, kimeneti].copy()
    maradek = width % 4
    if maradek:
        maradek_kerekites = _tengely_menten(
            kulonbozo,
            height,
            0,
            doboz,
            kerekito_oszlopok=np.zeros(kulonbozo.shape[1], dtype=bool),
        )
        kimenet[:, -maradek:] = maradek_kerekites[:, kimeneti[-maradek:]]
    return kimenet


def _ytresampler(kep: np.ndarray, width: int, height: int, lanczos: bool = False) -> np.ndarray:
    """A mód a vízszintes léptékből (`lanczos`: az 5-ös mód, mindkét tengelyen);
    előbb vízszintes, aztán függőleges menet."""
    if width == kep.shape[1] and height == kep.shape[0]:
        return kep.copy()
    doboz = width <= kep.shape[1] and not lanczos
    vizszintes = _tengely_menten(kep, width, 1, doboz, lanczos)
    kimenet = _tengely_menten(vizszintes, height, 0, doboz, lanczos)
    return kimenet.copy() if kimenet is kep else kimenet


def _bw_coefficients(color: tuple[int, int, int]) -> tuple[int, int, int]:
    """A `bw_tint` fixpontos csatornaegyütthatói (`c = trunc(w·2048 + 0,5)`,
    int16) a `color` szűrőszínre. `0xff6666`-tal `c = 1080 / 853 / 115`
    (#3930, #3931 „Kész, ha")."""
    red_w, green_w, blue_w = _HAEBERLI_WEIGHTS
    raw_weights = np.array(
        [red_w * color[0], green_w * color[1], blue_w * color[2]], dtype=np.float64
    )
    total = float(raw_weights.sum())
    if total > 0:
        weights = raw_weights / total
    else:
        weights = np.array([red_w, green_w, blue_w], dtype=np.float64)
    coeffs = _fixpont_egyutthato(weights)
    return int(coeffs[0]), int(coeffs[1]), int(coeffs[2])


def bw_tint(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """`BW(filtercolor=...)`: **valódi szürkeárnyalat** (R=G=B minden
    képponton) — a `filtercolor` NEM színezi be a kimenetet, hanem a
    szürkítéshez használt HAEBERLI csatornasúlyokat modulálja, mint egy
    színszűrő a fekete-fehér film előtt, majd a natív FIXPONTOS
    színmátrix-alkalmazóval számol.

    **Bizonyíték (#504), mérve az eredeti windowsos Picasa Holga-kimenetéhez
    (a privát `picasapy-agent` repó `referencia/holga/` hét mappás
    készlete):** mind a hat effektes exportban `R = G = B` **minden
    képponton**. A korábbi implementáció (`ki = luma/255 · color`) ezzel
    szemben SZÍNES kimenetet adott (`0xff6666`-tal R/G/B = 70/17/17) — ez
    volt a hiba, nem a csatornák sorrendje (#510 tévedett) és nem is
    „minden rendben" (#515 is tévedett).

    **A pontos képlet (#3930, utasításszintű bináris-kutatás, a `BW`
    közös színmátrix-alkalmazójára — `0x00bc16b0`/`0x00bbdd80`/`0x008f2500`):**

        w_c = haeberli_c · szín_c / Σ_k(haeberli_k · szín_k)
        c_c = trunc(w_c · 2048 + 0,5)                         (int16)
        Y   = clamp(((Σ_c (c_c · pixel_c) >> 9) + 2) >> 2, 0, 255)

    ahol `haeberli_c` a Haeberli-súly (`_HAEBERLI_WEIGHTS`, NEM Rec.601 —
    a #504 mérésből illesztett lebegőpontos modell ezt tévesen feltételezte,
    #3931). `0xff6666`-tal `c = 1080 / 853 / 115` (`_bw_coefficients`). A
    kettő a hetedes fixpontos kvantálás miatt NEM ugyanaz, mint a
    lebegőpontos `rint(Σ w·x)`: a teljes RGB-kockán 27%-ban eltérnek (pl.
    `(0,0,98)` fixpontosan 6, lebegőpontosan 5).

    Nulla összegnél (fekete szűrőszín) a natív kód a Haeberli-súlyokat
    használja módosítatlanul — ez az ág egyetlen hívónál sem fordul elő
    (a `color` mindig `0xff6666`), és a natív viselkedést erre az esetre
    **nem olvastuk ki** a bináris-kutatás során; a `0x00cf3a00` fallback
    egyenértékűsége a Haeberli-súlyokkal feltételezés, nem igazolt tény.
    `R = G = B = Y` — NEM a képen belüli (a `color`-tól független) lumát
    színezzük, hanem a `color`-ral modulált, fixpontosított súlyokkal
    újraszámoljuk a szürkét.

    `color` csatornasorrendje **RGB** (megegyezik a `image` tömb saját
    sorrendjével) — ld. `tint_multiply` docstringjét a #510-es tanulságról.
    """
    validate_image(image)
    coeffs = np.array([_bw_coefficients(color)], dtype=np.float64)
    # A `_bw_coefficients` már egész `c`; a közös alkalmazó a `c / 2048`
    # mátrixot pontosan ugyanerre az egészre váltja vissza.
    gray = _fixpontos_szinmatrix(image, coeffs / 2048.0, np.zeros(1))[..., 0]
    return np.repeat(gray[..., np.newaxis], 3, axis=-1)


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
