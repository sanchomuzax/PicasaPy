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

#: `tint_luma_preserving`: hány kompenzáló menet fusson a gamut-levágás után.
#: Menetenként legalább egy csatorna véglegesen kifut a tartományból, ezért
#: három menet a három csatornás esetre elég — a negyedik biztonsági tartalék.
_TINT_GAMUT_PASSES = 4
_TINT_EPSILON = np.float32(1e-6)

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
    automatikus javítása — megfejtett modell (#535): ugyanaz a hisztogram-
    darabszám alapú lineáris szinthúzás, mint a „Jó napom van" (I'm Feeling
    Lucky) `apply_enhance`-e (ld. `apply_channel_levels_stretch` docstringjét
    a bizonyítékért). A vágópont-keverés az ALAPÉRTELMEZETT 0,30: a natív
    `0x009db610`-nek ezek a hívói is a `-1,0` jelzőt adják át (#721). Ez hat
    Glimmer-effektet is érint (Holga, NightVision, PencilSketch, Sixties,
    Cinemascope, HDR-család), amelyek belül `AutoFix`-et hívnak.
    """
    from picasapy.render.ops import apply_channel_levels_stretch

    validate_image(image)
    return apply_channel_levels_stretch(image)


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
LOCAL_CONTRAST_RADIUS_FACTOR = 0.5

#: A művelet fényerő-tagja `Strength`-egységenként (#545). A mérés szerint
#: a lokális kontraszt mellett egy ezzel arányos világosítás is fut: a
#: `referencia/hdrish/` exportjain a legjobb közös érték 2,9 (az
#: exportonként illesztett eltolás 1,3–2,5 · Strength között szór).
#:
#: ⚠️ **Az EREDETIBEN nincs megfelelője — és MÉRVE nem a 8 bites
#: telítődés pótléka (#1607).** A `filterdesc.xml` `LocalContrast`
#: csővezetéke két, egymást kiegészítő telítődő blokkból áll (`subtract`
#: és `add`), világosító lépés nélkül. A kézenfekvő magyarázat az volt,
#: hogy ez a tag a mi lebegőpontos számolásunkból hiányzó telítődést
#: pótolja. **Megmérve: nem.**
#:
#: A mérés az EGYETLEN olyan referencia-mintán futott, ahol nincs szabad
#: paraméter: `referencia/hdrish/HDS-ish default` — az XML szerinti
#: alapállás (`Radius` 20, `Strength` 3, `Fade` 0). Alap a
#: `research/lomo-referencia/Lomo no effect` export (ugyanaz a JPEG-út,
#: így a tömörítés műterméke kiesik). Mérték: képpontonkénti euklideszi
#: RGB-távolság átlaga.
#:
#:     érintetlen kép                          ΔE 41,8
#:     MAI modell (+2,9·Strength)              ΔE  4,6
#:     ugyanaz, világosítás nélkül             ΔE 12,3
#:     XML-hű, blokkonként 8 bitre vágó modell ΔE 26,5
#:
#: A telítődő változat tehát ÖTSZÖRTE rosszabb. Kontroll: az a modell
#: `Contrast = 1`-nél bitre azonosságot ad, ahogy az XML előírja — az
#: implementáció helyes, a HIPOTÉZIS dőlt meg.
#:
#: ⇒ A konstans MARAD. Amit ez a tag helyettesít, **nyitott kérdés**.
#:
#: ⚠️ A fenti ΔE-k csak EGYMÁSSAL vethetők össze: a #545 „2,58"-as száma
#: más mérőszámmal és több mintán készült. A `referencia/hdrish/` a
#: privát repóban él, ezért ez a mérés a CI-ben nem futtatható —
#: a számok ITT élnek, a módszerrel együtt, hogy megismételhető legyen.
#:
#: ⚠️ A készlet többi nyolc mintáján a csúszkaértékek NINCSENEK rögzítve
#: (csak `min`/`mid`/`max` címkék), tehát ott a mérés szabad paramétert
#: tartalmazna — épp azt a hibát, ami miatt a #1607 megnyílt.
LOCAL_CONTRAST_BRIGHTNESS_PER_STRENGTH = 2.9


def local_contrast(image_f: np.ndarray, radius: float, strength: float) -> np.ndarray:
    """`LocalContrastImageOperation`: `ki = be + (be − elmosott)·strength +
    2,9·strength` — a `HDR`/`LocalContrast` effektek implementációja.

    #545: a `filterdesc.xml` a `Radius`-t adja meg, a MÉRÉS szerint viszont
    a tényleges Gauss-szigma ennek a fele, és a művelethez egy
    `Strength`-arányos világosítás is tartozik. A `referencia/hdrish/` hét
    exportján a modell átlagos eltérése a valódi Picasa-kimenettől **2,58**
    (a korábbi változaté 12,6, az érintetlen képé 25,3).
    """
    blurred = gaussian_blur_f(image_f, max(radius * LOCAL_CONTRAST_RADIUS_FACTOR, 0.3))
    brightened = np.float32(LOCAL_CONTRAST_BRIGHTNESS_PER_STRENGTH * strength)
    return image_f + (image_f - blurred) * np.float32(strength) + brightened


# --- Ragyogás-sugár korlátozása (Flash blurX/blurY limit, #504) ------------

#: A Picasa `GlowImageOperation` a Flash `GlowFilter` portja, a Flashben
#: pedig a `blurX`/`blurY` `[0, 255]`-re korlátozott (Flash 8+ dokumentáció).
#: A méretfüggő sugár-képletek (`35·0,02·max(W,H)/2` stb., ld. lentebb Lomo,
#: Holga, NightVision, Matte, Vignette) ezt a korlátot NEM ismerik — nagy
#: képen tehát a Picasa tényleges σ-ja jóval kisebb, mint amit a képlet
#: naivan adna.
#:
#: Bizonyíték (#504, mérve a `sanchomuzax/picasapy-agent` privát repó
#: `referencia/lomo/` öt mappás készletéhez, 2560×1702-es Lomo-exporttal):
#: a `filterdesc.xml` képlete ezen a képen 896-ot adna; az illesztés
#: optimuma σ≈255–340. A teljes láncon a Picasa kimenetétől való átlagos
#: csatorna-eltérés **41,8-ról (korlát nélkül) 9,0-ra** csökken a 255-ös
#: korláttal — viszonyításul az ÉRINTETLEN kép eltérése 32,1, azaz korlát
#: nélkül ROSSZABBAK vagyunk, mintha meg sem csináltuk volna az effektet.
GLOW_RADIUS_MAX = 255.0


def clamp_glow_radius(radius: float) -> float:
    """A méretfüggő ragyogás-sugár képletek (Lomo, Holga, NightVision,
    Matte, Vignette, MuseumMatte) KÖZÖS korlátja — ld. `GLOW_RADIUS_MAX`
    docstringjét a bizonyítékért (#504). Minden méretfüggő σ-számítás ide
    fusson be, hogy a korlát egy helyen legyen dokumentálva és karbantartva.
    """
    return min(float(radius), GLOW_RADIUS_MAX)


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

    `colors` elemeinek csatornasorrendje **RGB** — ld. `tint_multiply`
    docstringjét (#510).
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


def tint_luma_preserving(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """`TintImageOperation(Color=…)` — FÉNYESSÉG-TARTÓ színezés (#878).

    **Megfejtve a #685 mérőszettjének `picniktint__alap.jpg` golden párjából**
    (`PicnikTint=1,0.000000,0080cfff;`): a művelet a bemenet Rec.601
    luminanciáját **bájtra megőrzi**, és a szín krómáját adja hozzá. Formálisan

    ```
    kimenet = luma(kép) + (szín − luma(szín))
    ```

    majd a tartományon kívülre kerülő csatornákat levágja, és a levágás
    fényesség-veszteségét a MÉG SZABAD csatornákon kompenzálja, amíg a
    luminancia újra a bemenetivel egyezik.

    A mérés ezt három független ponton igazolja (a golden pár mediánjain,
    a szín `0x80cfff`, `luma = 188,9`):

    | bemeneti luma | mért kimenet (R, G, B) | a kimenet lumája |
    |---:|---|---:|
    | 16 | (0, 16, 65) | 16,8 |
    | 128 | (69, 147, 195) | 129,1 |
    | 248 | (231, 255, 255) | 247,9 |

    A 248-as sor a döntő: két csatorna 255-ön áll, és a HARMADIK áll be arra
    az értékre, amellyel a luminancia pontosan visszajön — vagyis a levágás
    nem egyszerű `clip`, hanem fényesség-visszaállítással jár. A modell
    csatornánkénti átlagos abszolút hibája a teljes golden páron **1,7–2,4
    szint** (a JPEG-zaj nagyságrendje).

    A `color` csatornasorrendje a `tint_multiply`-jal azonos: **RGB**.
    """
    validate_image(image)
    image_f = to_float(image)
    target = luma(image_f)[..., np.newaxis]

    weights = np.array(_REC601_WEIGHTS, dtype=np.float32)
    color_f = np.array(color, dtype=np.float32)
    result = target + (color_f - float(color_f @ weights))

    # a levágott csatornák fényesség-veszteségének kompenzálása a szabadokon
    for _ in range(_TINT_GAMUT_PASSES):
        clipped = np.clip(result, 0.0, 255.0)
        free = ((result > 0.0) & (result < 255.0)).astype(np.float32)
        free_weight = (free * weights).sum(axis=2, keepdims=True)
        if not np.any(free_weight > _TINT_EPSILON):
            break
        missing = target - (clipped * weights).sum(axis=2, keepdims=True)
        correction = np.where(
            free_weight > _TINT_EPSILON, missing / np.maximum(free_weight, _TINT_EPSILON), 0.0
        )
        result = clipped + correction * free
    return to_uint8(result)


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
    "GLOW_RADIUS_MAX",
    "clamp_glow_radius",
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
