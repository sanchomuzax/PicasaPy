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

from picasapy.lazy_cv2 import cv2
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


def autofix(image: np.ndarray) -> np.ndarray:
    """`AutoFix`: a Glimmer belső, effekt-csővezetékekben újrahasznált
    automatikus javítása — **vágás nélküli min–max szinthúzás** (#2229).

    ⚠️ **NEM azonos a „Jó napom van"-nal.** A natív parancs
    (`0x009db610`, #535/#721) vágópont-keverést végez; a Glimmer
    `AutoFixImageOperation` **másik kódút**, és a munkavégzője
    (`0x00bc2d70`) mást csinál:

    1. három **egyszerű** 256 rekeszes hisztogram (`0x00bc2e50`) —
       vágás, súlyozás, percentilis **nincs** benne;
    2. csatornánként LUT (`0x00bc3170`):

    ```
    lo = az első nem üres rekesz,  hi = az utolsó nem üres rekesz
    lo == hi  ->  LUT[x] = 255
    egyébként ->  LUT[x] = clamp(trunc((x − lo)/(hi − lo)·255 + 0,5), 0, 255)
    ```

    A `255,0` és a `0,5` konstans kiolvasva (`0x00cf39d0`, `0x00c72150`).

    A különbség nem elméleti: egyetlen kiugró szélső képpont a vágópontos
    modellben eltűnik, itt viszont **meghatározza a tartományt**. Hat
    Glimmer-effekt hívja belül (Holga, NightVision, PencilSketch, Sixties,
    Cinemascope, HDR-család), tehát mindegyik kimenetét érinti.

    *(A natív `0x00bc2d70` 1000 képpont fölött lekicsinyített mintán
    számol — a MI hisztogramunk a teljes képet nézi. A LUT szempontjából
    ez csak a szélső rekeszek ritka esetén térhet el, és a mintavételezés
    pontos rácsa nincs megmérve; találgatott közelítés rosszabb volna,
    mint a teljes minta.)*
    """
    validate_image(image)
    kimenet = np.empty_like(image)
    for csatorna in range(image.shape[2]):
        sik = image[..., csatorna]
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
        kimenet[..., csatorna] = lut[sik]
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


def _kontraszt_alkalmaz(image_f: np.ndarray, contrast: float) -> np.ndarray:
    """A KÜLÖN kontraszt-ág (#904, `0x008f1bd0`): a forgáspont **63,5**,
    nem 128 — `t = (1-k)·127·0,5`. `|k-1| < eps` esetén a művelet tétlen
    (a natív korai kilépése)."""
    c = float(np.clip(contrast, -100.0, 100.0))
    k = 1.0 + _kontraszt_gorbe(c)
    if abs(k - 1.0) < _CONTRAST_EPS:
        return image_f
    t = (1.0 - k) * 127.0 * 0.5
    return np.float32(k) * image_f + np.float32(t)


def _kontraszt_fenyero_egyuttes(
    image_f: np.ndarray, contrast: float, brightness: float
) -> np.ndarray:
    """A `ContrastAndBrightnessLinked` ág (#904, `0x008f2040`) — KÜLÖN
    kódút, nem a különálló kontraszt+fényerő egymás után alkalmazva: a
    forgáspont **127,5** (a valódi középszürke), és a fényerő-tag súlya a
    kontraszttól függ (`(k+1)·127,5/100`), tehát erős kontraszt mellett a
    fényerő is erősebben hat."""
    c = float(np.clip(contrast, -100.0, 100.0))
    b = float(np.clip(brightness, -100.0, 100.0))
    k = 1.0 + _kontraszt_gorbe(c)
    t = ((k + 1.0) * 127.5 * b) / 100.0 + (127.5 - k * 127.5)
    return np.float32(k) * image_f + np.float32(t)


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
    a kontraszt (101 elemű táblázatos görbe, 63,5-ös forgáspont, korai
    kilépés kis `k`-nál) és a fényerő (KÖZVETLEN additív, nincs ×2,55
    skálázás) külön-külön, ebben a sorrendben (#904). A `brightness` és a
    `contrast` is `[-100..100]`-ra vágva, a natív mintájára.
    """
    validate_image(image)
    image_f = to_float(image)
    if saturation is not None:
        matrix = _saturation_matrix(float(saturation))
        image_f = image_f @ matrix.T
    if linked:
        if contrast or brightness:
            image_f = _kontraszt_fenyero_egyuttes(image_f, contrast, brightness)
    else:
        if contrast:
            image_f = _kontraszt_alkalmaz(image_f, contrast)
        if brightness:
            b = float(np.clip(brightness, -100.0, 100.0))
            image_f = image_f + np.float32(b)
    return to_uint8(image_f)


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
#: ⚠️ #1607: a `local_contrast` MÁR NEM ezt használja — a `quality="3"`
#: háromszoros dobozelmosást számolja közvetlenül (`box_blur_trunc`),
#: amiből a felezés (`σ² = 3(w²−1)/12`, nagy `w`-re `σ ≈ w/2`) magától
#: adódik. A konstans a többi, Gauss-szal közelítő hívónak marad meg, és
#: dokumentumként: a #545 mérése így vált levezetett értékké.

#: A KORÁBBI, illesztett világosító tag (#545) — **megszűnt** (#1607).
#:
#: A `+2,9·Strength` a `referencia/hdrish/` exportjaira volt illesztve,
#: magyarázat nélkül, és a `filterdesc.xml` csővezetékében nincs megfelelője.
#: A #1607 két hipotézist járt végig:
#:
#: 1. **„a 8 bites telítődés pótléka"** — MEGMÉRVE, MEGDŐLT: a blokkonként
#:    8 bitre vágó, XML-hű modell ΔE 26,5-öt adott a mai 4,6 helyett
#:    (`referencia/hdrish/HDS-ish default`, az egyetlen szabad paraméter
#:    nélküli minta; alap a `research/lomo-referencia/Lomo no effect`).
#: 2. **„a csonkító dobozelmosás torzítása"** — MEGMÉRVE, ÁLL: a
#:    `quality="3"` hat egész osztása az elmosást rendszeresen ~2,7
#:    szinttel a Gauss-átlag alá viszi, és a `be + (be−elmosott)·strength`
#:    képlet ezt pontosan `+2,7·strength` világosításként adja vissza.
#:
#: ⇒ A tag nem külön lépés volt, hanem a HIÁNYZÓ csonkítás lenyomata.
#: A modell ezért a `box_blur_trunc`-ot használja, és a konstans elfogyott.
#: Részletek: `local_contrast` docstringje.


def _box1d_trunc(a: np.ndarray, width: int, axis: int) -> np.ndarray:
    """Egy dobozelmosás-menet EGÉSZ osztással — tehát CSONKÍTVA.

    A csonkítás nem részletkérdés, hanem ennek a modellnek a lényege:
    minden menet átlagosan fél szinttel LEJJEBB viszi az eredményt, mint a
    valódi átlag. Az összeg itt mindig NEMNEGATÍV (képpontértékek futó
    összegének különbsége), ezért a `//` padlózása és a natív `idiv`
    csonkítása egybeesik — a `//` itt hű. Ld. `local_contrast` és a #926-ot.
    """
    pad = width // 2
    kitoltes = [(pad, pad) if i == axis else (0, 0) for i in range(a.ndim)]
    kiterjesztett = np.pad(a, kitoltes, mode="reflect")
    osszeg = np.cumsum(kiterjesztett, axis=axis, dtype=np.int64)
    nulla = np.zeros_like(np.take(osszeg, [0], axis=axis))
    osszeg = np.concatenate([nulla, osszeg], axis=axis)
    n = kiterjesztett.shape[axis] - width + 1
    felso = np.take(osszeg, range(width, width + n), axis=axis)
    also = np.take(osszeg, range(0, n), axis=axis)
    return (felso - also) // width


def box_blur_trunc(image_f: np.ndarray, radius: float) -> np.ndarray:
    """`BlurImageOperation quality="3"` — HÁROMSZOROS dobozelmosás, menetenként
    (x és y) egész osztással, ahogy egy natív 8 bites megvalósítás számol.

    Az ablakszélesség a `Radius` (páratlanra kerekítve); a háromszoros doboz
    szórása `σ ≈ Radius/2`, épp az a felezés, amit a #545 négy Radius-állása
    egymástól függetlenül kimért.
    """
    szelesseg = max(1, int(round(radius)))
    if szelesseg % 2 == 0:
        szelesseg += 1
    egesz = np.rint(image_f).astype(np.int64)
    for _ in range(3):
        egesz = _box1d_trunc(egesz, szelesseg, 1)
        egesz = _box1d_trunc(egesz, szelesseg, 0)
    return egesz.astype(np.float32)


def local_contrast(image_f: np.ndarray, radius: float, strength: float) -> np.ndarray:
    """`LocalContrastImageOperation`: `ki = be + (be − elmosott)·strength`,
    ahol az elmosás a `filterdesc.xml` szerinti `quality="3"` **csonkító**
    háromszoros dobozelmosás.

    ## Miért nincs itt külön világosító tag (#1607)

    A korábbi modell `+ 2,9·strength`-et adott hozzá. A konstans a
    `referencia/hdrish/` exportjaira volt ILLESZTVE, magyarázat nélkül — és
    a `filterdesc.xml` csővezetékében nincs világosító lépés. A #1607
    kimérte, hogy a 8 bites telítődés nem magyarázza; a kérdés nyitva
    maradt.

    **A magyarázat a BLUR-ban van, nem külön tagban.** A
    `BlurImageOperation quality="3"` három dobozelmosás-menet, mindegyik
    x-ben és y-ban — hat egész osztás, egyenként átlagosan fél szint
    lefelé. Az így kapott elmosás **rendszeresen ~2,7 szinttel a valódi
    (lebegőpontos Gauss) átlag ALATT van**, és mivel a képlet
    `be + (be − elmosott)·strength`, ez pontosan `+2,7·strength`
    világosításként jelenik meg. Mérve, 400×400-as textúrán:

        Radius 15 → −2,696 · Radius 20 → −2,689 · Radius 40 → −2,566

    — a sugártól gyakorlatilag függetlenül, ahogy egy hat osztásból jövő
    torzításnak lennie kell. Az illesztett 2,9 ennek a becslése volt.

    ## Amit ez JAVÍT — a SÍK felület

    A régi tag SÍK képen is világosított (`Strength=3`-nál +8,7 szinttel),
    pedig ott nincs mit kiemelni: a csonkítás sík felületen nulla torzítást
    ad (mérve: 3e-05). Az égbolt és a sima falak tehát ok nélkül
    világosodtak. Az új modell síkon **azonosság**.

    Textúrás képen a két modell a mérési zaj alatt marad egymástól
    (átlagos eltérés 0,15…0,94 szint, `Radius` 15…40, `strength` 0,5…3),
    tehát a #545/#688 golden-illesztés NEM romlik el.

    ⚠️ A `referencia/hdrish/` a privát repóban él, a CI-ben nem futtatható;
    az itteni számok a módszerrel együtt élnek, hogy megismételhetők
    legyenek.
    """
    blurred = box_blur_trunc(image_f, radius)
    return image_f + (image_f - blurred) * np.float32(strength)


# --- A ragyogás SZIGMÁJA: a filterdesc blur ÁTMÉRŐ, a σ a fele (#3158) ----

#: A `filterdesc.xml` `xblur`/`yblur` értéke a Flash `GlowFilter`-é, ami
#: **átmérő-jellegű** elmosás-paraméter; a mi `inner_glow`-unk Gauss-**σ**-t
#: vár. A kettő hányadosa 2 — ezt a szám MÉRÉSSEL igazolja, nem illesztéssel.
#:
#: ## Mit váltott le (#504 → #3158)
#:
#: A korábbi modell egy közös **255-ös korlátot** (`GLOW_RADIUS_MAX`) tett a
#: képletre, a Flash `blurX ∈ [0, 255]` dokumentált tartománya alapján. Az a
#: korlát a hiányzó felezést pótolta, és épp ezért nem tudott mindkét
#: használónak megfelelni (#3158: a Lomo 450-et, a Holga 255-öt „kért").
#:
#: ## A mérés (`referencia/lomo` és `referencia/holga`, 2560 × 1702)
#:
#: Mindkét effekt a SAJÁT alapértékeivel (Lomo: Blur 50, Fade 0 · Holga:
#: Blur 70, Grain 30, Fade 0 — a `filterdesc.xml` `value=` mezőiből), a
#: referencia-export ugyanezekkel készült:
#:
#: | | régi (255-ös korlát) | **új (felezés)** | az ÉRINTETLEN kép |
#: |---|---:|---:|---:|
#: | Lomo ΔE | 9,09 | **1,94** | 16,27 |
#: | Lomo nullátmenet | 0,625 | **0,405** | — |
#: | Holga ΔE | 1,95 | **1,12** | 23,19 |
#: | Holga nullátmenet | 0,435 | **0,425** | — |
#:
#: A referencia-export nullátmenete **0,425** (a sugár-profil előjelváltása a
#: kép közepétől, a képátló feléhez viszonyítva, 100 gyűrűn). ⇒ a felezés
#: MINDKÉT effekten és MINDKÉT mérőszámon javít, a Holga nullátmenete pedig
#: pontosan a mértre esik.
#:
#: ⭐ **Független megerősítés a `Vignette`-ből (#518):** annak a leírója `/4`-et
#: ad, a legjobb illesztés viszont a képlet `/8`-a — a hányados ugyanaz a 2-es
#: szorzó. Két, egymástól független effekt-mérés mondja tehát ugyanazt.
#:
#: ⚠️ **A korábbi 255-ös korlát (#504) nem volt „rossz mérés", hanem a hiányzó
#: felezést pótolta:** a Lomón 896 → 255 (a felezés 448-at ad), a Holgán a
#: 640/512-es tengelypár → 255/255 (a felezés 320/256-ot, a leíró arányát).
#: Ezért tudott a Holgán majdnem jó lenni (1,95) és a Lomón nem (9,09).
def glow_sigma(blur: float) -> float:
    """A `filterdesc` blur-értékéből Gauss-σ: a FELE (#3158).

    Minden méretfüggő ragyogás-számítás ide fusson be, hogy a felezés egy
    helyen legyen dokumentálva és karbantartva. Korlát NINCS: a 255-ös
    vágás (#504) a hiányzó felezést pótolta, és a Lomo 448-as σ-ját
    levágva mérhetően rosszabb képet adott.
    """
    return float(blur) / 2.0


# --- Belső ragyogás (GlowImageOperation innerglow) ----------------------

# `erf` közelítés (Abramowitz–Stegun 7.1.26, |hiba| < 1,5·10⁻⁷) — a projekt
# nem függ a scipy-től, ez a néhány ezer elemű (egy-egy tengelyre eső)
# tömbön bőven elég pontos, és `numpy`-only marad.
_ERF_A = (0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429)
_ERF_P = 0.3275911


def _erf(x: np.ndarray) -> np.ndarray:
    sign = np.sign(x)
    ax = np.abs(x)
    t = 1.0 / (1.0 + _ERF_P * ax)
    poly = ((((_ERF_A[4] * t + _ERF_A[3]) * t + _ERF_A[2]) * t + _ERF_A[1]) * t + _ERF_A[0]) * t
    y = 1.0 - poly * np.exp(-ax * ax)
    return sign * y


def _box_blur_axis(length: int, sigma: float) -> np.ndarray:
    """Az `[0, length)` tömör (mindenütt 1) szakasz Gauss-elmosása
    `sigma` szigmával, zárt alakban (`erf`-fel), a szakasz pixelközepein
    kiértékelve — a `covered` (borítottság) egyik tengelye `inner_glow`-ban.
    """
    sigma = max(float(sigma), 1e-6)
    denom = np.sqrt(2.0) * sigma
    idx = np.arange(length, dtype=np.float64) + 0.5
    return 0.5 * (_erf(idx / denom) - _erf((idx - length) / denom))


def inner_glow(
    image: np.ndarray,
    color: tuple[int, int, int],
    xblur: float,
    yblur: float,
    strength: float,
    alpha: float = 1.0,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """`GlowImageOperation(innerglow=true)`: a kép SZÉLÉTŐL befelé ható
    „izzás" a `color` színnel — a Picasa ezt Vignette-hez (fekete) és
    Matte-hoz (fehér) használja, MuseumMatte-nál pedig a paszpartu-vonalak
    mellett.

    **Analitikus modell (#522, a #509-es min-max normálás felváltása).**
    A belső ragyogás bemenete mindig egy TÖMÖR téglalap alfa-maszk (a teljes
    kép — a régi „keret-impulzus" ennek az élén futó Gauss-elmosás
    közelítése volt). Egy tömör téglalap Gauss-elmosása a szeparábilis
    kernel miatt tengelyenként EGY-EGY `erf`-fel, zárt alakban számolható
    (`_box_blur_axis`), a 2D borítottság a két tengely SZORZATA:

        covered = ay[:, None] · ax[None, :]
        weight  = (1 − covered) · strength

    Ez a szélen ad NAGY (a `strength`-hez közeli), a középen ~0 súlyt —
    és a `strength` a súly VALÓDI mélységét szabja, nem csak az alakot: itt
    nincs saját min/maxra nyújtás, tehát (ellentétben a #509 min-max
    modelljével) nagy szigmánál a `strength` ténylegesen elhalványul, nem
    marad mesterségesen 1-re pumpálva. Nincs konvolúciós kernel, nincs
    le-fel skálázás — a költség a kép méretével lineáris és a σ-tól
    FÜGGETLEN (a `_box_blur_axis` csak a szélesség/magasság hosszú 1D
    tömbökön dolgozik, a 2D `covered` egyetlen külső szorzat).

    `mask` (opcionális, H×W [0,1]) a hatást TOVÁBB korlátozza (pl.
    MuseumMatte csak a vonal sávján). `color` csatornasorrendje **RGB** —
    ld. `tint_multiply` docstringjét (#510).
    """
    validate_image(image)
    height, width = image.shape[:2]
    ax = _box_blur_axis(width, xblur)
    ay = _box_blur_axis(height, yblur)
    covered = (ay[:, np.newaxis] * ax[np.newaxis, :]).astype(np.float32)
    weight = np.clip((1.0 - covered) * np.float32(strength), 0.0, 1.0) * np.float32(alpha)
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

    ⚠️ **A RÖGZÍTETT mag csak tesztelési célra való** (#907). Az eredeti
    szemcséje nem determinisztikus: két egymás utáni alkalmazás FÜGGETLEN
    zajmintát ad (a #685 mérőszettjén ΔE 1,804 → 2,671, ami a √2-es
    szórásnövekedés, nem a kétszeres amplitúdó). Aki termelő úton hívja ezt,
    **minden alkalmazáshoz új magot adjon** — különben kétszer alkalmazva
    kétszer akkora hatást kap, mint az eredetiben. A `glimmer_artistic.
    apply_picnik_grain` ezt a `seed=None` alapértékkel oldja meg.
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


#: #3421: a gradiens-LUT-ok INDEXE a képpont piros csatornája. A
#: `GradientMap` (`0x00bb87b0`) és a `HSVGradientMap` (`0x00bbc260`)
#: építője a színtáblát a közös futószalag (`0x00bcb2f0`) `+0x800`
#: rekeszébe írja (a BGRA `src[2]` bájtja), a másik kettőt nullázza — a
#: kimenet tehát csak a piros csatornától függ, nem a lumától.
_GRADIENS_INDEX_CSATORNA = 0


def gradient_map(image: np.ndarray, colors: tuple[tuple[int, int, int], ...]) -> np.ndarray:
    """`GradientMap`: a képpont PIROS csatornáját [0..255] a `colors`
    (egyenletes közű, `len(colors)` pontos) színátmenetére képezi le
    (#3421, ld. `_GRADIENS_INDEX_CSATORNA`).

    `colors` elemeinek csatornasorrendje **RGB** — ld. `tint_multiply`
    docstringjét (#510).
    """
    validate_image(image)
    if len(colors) < 2:
        raise ValueError("Legalább két szín kell a gradienshez")
    gray_index = image[..., _GRADIENS_INDEX_CSATORNA]
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
    """`HSVGradientMap`: a PIROS csatornához (#3421) rendelt (pozíció,
    hue°, sat%, val%) töréspontok interpolációja HSV-térben, majd RGB-re
    konvertálva — a `HeatMap` effekt implementációja.
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
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    dist = np.hypot(xs + 0.5 - cx, ys + 0.5 - cy)
    belso = float(np.clip(inner_alpha, 0.0, 1.0))
    kulso = float(np.clip(outer_alpha, 0.0, 1.0))
    if outer_radius <= inner_radius:
        arany = (dist >= inner_radius).astype(np.float32)
    else:
        arany = np.clip(
            (dist - inner_radius) / (outer_radius - inner_radius), 0.0, 1.0
        ).astype(np.float32)
    return (np.float32(belso) + arany * np.float32(kulso - belso)).astype(np.float32)


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
    RGB, amely `szín` krómáját adja, de a Haeberli-lumája PONTOSAN `L`.

    A natív a `d > 0` esetet a `255 − x` tükrözéssel a `d ≤ 0` esetre vezeti
    vissza (ugyanaz a levágás-kódút, csak fordítva bejárva). A két irány a
    Haeberli-súlyok összege = 1 miatt algebrailag EGYENÉRTÉKŰ egyetlen,
    mindkét irányban vágó ciklussal (0 ÉS 255 felé is), amíg a hiányzó
    fényességet a MÉG SZABAD (nem levágott) csatornákra osztja szét — a
    „saját súllyal" / „kiegészítő súllyal" osztás pontosan ennek felel meg,
    ha a szabad csatornák súlyösszegével osztunk. A tükrözés emulálása
    tehát nem szükséges a bitre egyező eredményhez.
    """
    weights = np.asarray(_HAEBERLI_WEIGHTS, dtype=np.float64)
    lc = _resaturate_color_luma(color)
    values = np.asarray(color, dtype=np.float64) + (float(target) - float(lc))

    for _ in range(_TINT_GAMUT_PASSES):
        clipped = np.clip(values, 0.0, 255.0)
        free = (values > 0.0) & (values < 255.0)
        free_weight = float((free * weights).sum())
        if free_weight <= _TINT_EPSILON:
            values = clipped
            break
        missing = float(target) - float((clipped * weights).sum())
        values = clipped + (missing / free_weight) * free

    # a végső csonkítás (`or 0xc00` + `fistp`, 0x00bce83a) — NEM kerekítés;
    # a `round(…, 6)` csak a lebegőpontos zajt söpri el (pl. 199,99999999997
    # helyett 200,0), a valódi tizedeseket (négy tizedesjegyű súlyokból,
    # egész színekből és egész L-ekből) nem érinti.
    truncated = np.trunc(np.clip(np.round(values, 6), 0.0, 255.0))
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
       NEM Rec.601): `szürke = round(Haeberli-luma(képpont))`;
    2. a szürke érték a `_resaturate_table(szín)` 256 elemű táblájának
       indexe — a tábla a `0x00bce2f0(szín, L)` emuláltja `L = 0…255`-re.

    ⛔ **KORÁBBAN** (a #878 golden-illesztése): Rec.601-súlyok +
    folytonos, per-képpont gamut-kompenzáció. Szürke bemeneten a modell
    átlagosan 1–4, telített kéknél/sárgánál (`0x0000ff`, `0xffff00`) akár
    **71 szinttel** tért el az emulált native táblától (#3631 lelete) — a
    Haeberli-súlyok és a diszkrét, szín-szerinti tábla ezt zárja.

    A `color` csatornasorrendje **RGB**.
    """
    validate_image(image)
    image_f = to_float(image)
    gray = to_uint8(_haeberli_luma(image_f))
    table = _resaturate_table((int(color[0]), int(color[1]), int(color[2])))
    return table[gray]


#: A Mitchell–Netravali mag paraméterei: **B = C = 0,4** (#2227). Mérve: az
#: eredeti `ResizeImageOperation` alkalmazója (`0x00bc3650`) ugyanazt a
#: `0x00bcb5e0` segédfüggvényt hívja, mint a `RotateImageOperation`, az pedig
#: a `ytResampler`-t EXPLICIT móddal — lépték = 1 → 0-s (doboz), egyébként
#: 3-as (Mitchell–Netravali, B = C = 0,4).
_MITCHELL_B = 0.4
_MITCHELL_C = 0.4


def mitchell_netravali(x: np.ndarray) -> np.ndarray:
    """A Mitchell–Netravali rekonstrukciós mag `B = C = 0,4`-gyel.

    A klasszikus alak (Mitchell & Netravali, 1988), `|x|` szerint:

        |x| < 1:  ((12−9B−6C)|x|³ + (−18+12B+6C)|x|² + (6−2B)) / 6
        1 ≤ |x| < 2:  ((−B−6C)|x|³ + (6B+30C)|x|² + (−12B−48C)|x| + (8B+24C)) / 6
        egyébként: 0

    `B = C = 0,4` mellett az **oldallebeny negatív** (1 és 2 között) — ez a
    mag azonosító jegye: éles élen enyhe alul-/túllövést ad, amit sem a
    bilineáris, sem a doboz nem produkál.
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


def _mintavetel_sulyok(
    be_meret: int, ki_meret: int
) -> tuple[np.ndarray, np.ndarray]:
    """Egy tengely mintavételi indexei és súlyai.

    A kimeneti képpont középpontját a bemeneti rácsra vetítjük, és a magot
    a szomszédos bemeneti mintákon értékeljük ki. **Kicsinyítéskor a mag a
    léptékkel nyúlik** — élsimítás.

    ⭐ #3321: a nyújtás MÉRVE van, nem feltevés. Az eredeti újramintavevő
    3-as ága (`0x00a3f660`, `0x00a3f68c`–`0x00a3f6a3`) a mag alap-tartósugarát
    a LÉPTÉKKEL OSZTJA (`0x00a3f745`–`0x00a3f74b`), tehát `scale < 1` mellett
    a mag a forrástérben szélesedik — pontosan az itteni `max(1, skala)`.

    ⚠️ Amit ez NEM bizonyít: a képpontra azonos kimenetet. A mechanizmus
    statikus bizonyíték; a golden-egyezés külön mérési feladat.

    A széleken a bemeneti index a tartományra csippentődik (peremismétlés),
    a súlyok pedig sorösszegre normálódnak, hogy a fényesség megmaradjon.
    """
    skala = be_meret / ki_meret
    nyujtas = max(1.0, skala)
    tamasz = 2.0 * nyujtas
    kozep = (np.arange(ki_meret) + 0.5) * skala - 0.5
    elso = np.ceil(kozep - tamasz).astype(np.int64)
    ablak = int(np.ceil(2 * tamasz)) + 1
    indexek = elso[:, None] + np.arange(ablak)[None, :]
    sulyok = mitchell_netravali((kozep[:, None] - indexek) / nyujtas)
    osszeg = sulyok.sum(axis=1, keepdims=True)
    # Elvi 0 nem fordul elő (a mag 0-ban pozitív), de a nullosztás
    # következménye néma NaN-kép lenne — ezért kimondottan kizárjuk.
    osszeg[osszeg == 0] = 1.0
    return np.clip(indexek, 0, be_meret - 1), sulyok / osszeg


def _tengely_menten(kep: np.ndarray, ki_meret: int, tengely: int) -> np.ndarray:
    """Átmintavételezés EGY tengely mentén, a másikat érintetlenül hagyva."""
    be_meret = kep.shape[tengely]
    if ki_meret == be_meret:
        return kep          # lépték = 1 → 0-s (doboz) = azonosság
    indexek, sulyok = _mintavetel_sulyok(be_meret, ki_meret)
    minta = np.take(kep, indexek, axis=tengely)
    # a súlyok a (ki_meret, ablak) tengelypárra szólnak: a szorzás után
    # az ablak-tengely mentén összegzünk
    alak = [1] * minta.ndim
    alak[tengely] = ki_meret
    alak[tengely + 1] = sulyok.shape[1]
    return (minta * sulyok.reshape(alak)).sum(axis=tengely + 1)


def resize_image(image: np.ndarray, width: int, height: int, smoothing: bool = True) -> np.ndarray:
    """`Resize`: a kép átméretezése.

    `smoothing=True` (az alapérték, mérve: `0x00bc36ac`) esetén a
    mintavételező **tengelyenként** dönt, a `src/dst` léptékből
    (`0x00bc3700`–`0x00bc3731`): **lépték = 1 → doboz** (azonosság),
    egyébként **Mitchell–Netravali B = C = 0,4** (#2227). A művelet
    szeparábilis: előbb a vízszintes, majd a függőleges tengely.

    ⚠️ `smoothing=False` továbbra is `INTER_NEAREST`. **Ez NEM mérés:** a
    bináris ezen ága nincs visszafejtve — hogy a 0-s dobozmódot használja-e,
    vagy tényleg legközelebbi szomszédot, nyitott kérdés.
    """
    validate_image(image)
    width = max(1, int(round(width)))
    height = max(1, int(round(height)))
    if not smoothing:
        return cv2.resize(image, (width, height), interpolation=cv2.INTER_NEAREST)
    if width == image.shape[1] and height == image.shape[0]:
        return image.copy()
    munka = image.astype(np.float64)
    munka = _tengely_menten(munka, width, 1)
    munka = _tengely_menten(munka, height, 0)
    return np.clip(np.rint(munka), 0, 255).astype(image.dtype)


def bw_tint(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """`BW(filtercolor=...)`: **valódi szürkeárnyalat** (R=G=B minden
    képponton) — a `filtercolor` NEM színezi be a kimenetet, hanem a
    szürkítéshez használt Rec.601 csatornasúlyokat modulálja, mint egy
    színszűrő a fekete-fehér film előtt.

    **Bizonyíték (#504), mérve az eredeti windowsos Picasa Holga-kimenetéhez
    (a privát `picasapy-agent` repó `referencia/holga/` hét mappás
    készlete):** mind a hat effektes exportban `R = G = B` **minden
    képponton**. A korábbi implementáció (`ki = luma/255 · color`) ezzel
    szemben SZÍNES kimenetet adott (`0xff6666`-tal R/G/B = 70/17/17) — ez
    volt a hiba, nem a csatornák sorrendje (#510 tévedett) és nem is
    „minden rendben" (#515 is tévedett).

    A helyes képlet, a referenciából levezetve és szabad illesztéssel
    ellenőrizve (a levezetett képlet maradéka 10,92, az elméleti alsó
    korlát 10,89 — 4 paraméteres szabad illesztéssel):

        w_c = luma_c · szín_c / Σ_k(luma_k · szín_k)

    ahol `luma_c` a Rec.601-súly (`_REC601_WEIGHTS`). `0xff6666`-tal ez
    B 0,079 / G 0,405 / R 0,516. A kimenet: `gray = Σ_c(w_c · pixel_c)`,
    majd `R = G = B = gray` — NEM a képen belüli (a `color`-tól független)
    lumát színezzük, hanem a `color`-ral modulált súlyokkal újraszámoljuk
    a szürkét.

    `color` csatornasorrendje **RGB** (megegyezik a `image` tömb saját
    sorrendjével) — ld. `tint_multiply` docstringjét a #510-es tanulságról.
    """
    validate_image(image)
    image_f = to_float(image)
    red_w, green_w, blue_w = _REC601_WEIGHTS
    raw_weights = np.array(
        [red_w * color[0], green_w * color[1], blue_w * color[2]], dtype=np.float64
    )
    total = float(raw_weights.sum())
    if total > 1e-9:
        weights = (raw_weights / total).astype(np.float32)
    else:
        weights = np.array([red_w, green_w, blue_w], dtype=np.float32)
    gray = (
        weights[0] * image_f[..., 0] + weights[1] * image_f[..., 1] + weights[2] * image_f[..., 2]
    )
    return to_uint8(np.repeat(gray[..., np.newaxis], 3, axis=-1))


__all__ = [
    "to_uint8",
    "to_float",
    "luma",
    "fade_alpha",
    "alpha_blend",
    "glow_sigma",
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
