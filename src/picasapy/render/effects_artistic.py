"""A Picasa 5. fülének (kék ecset) művészi effektjei — I. rész: Boost, Soften,
Pixelate, PencilSketch, Comicize.

A `Neon` a #878-ban KIKERÜLT innen: az itteni modell a hatás jellegét
közelítette, és soha nem is futott (a `filters=` láncot mindig a
`glimmer_creative.apply_neon` szolgálta ki). A visszafejtett, mért
csővezeték ott él, az `EdgeDetectionB` pedig a `glimmer_edges.py`-ban.

A `FocalZoom` (és a `PicnikFocalPixelate`) a #570-ben átkerült a
`render/focal.py`-ba: azok a natív `glimmer::RadialBlurImageOperation`
visszafejtett paraméterezését és közös körmaszkját használják, nem a hatás
jellegének közelítését.

A `Comicize` a #569 óta KIVÉTEL a lenti őszinteség-megjegyzés alól: annak a
csővezetéke a `filterdesc.xml`-ből és a natív `glimmer::TiledImageMask`
kódjából való, nem a hatás jellegének közelítése.

**ŐSZINTESÉG (#330):** a Picasa e 11 effektjének pontos algoritmusa NEM
publikus, és ehhez NINCS golden-mérés (szemben a `docs/specs/filters-decoded.md`
alatt dokumentált, mért szűrőkkel). A `filters=` kulcsok szerkezete azonosított
(`docs/specs/filters-decoded.md`, 5. kör), de a PARAMÉTEREK JELENTÉSE
(csúszka-leképezés) nyitott — az itt implementált modellek a hatás fotós/UI
JELLEGÉT közelítik (mit csinál egy „felpörgetés", egy „lágyítás" stb.), NEM
állítjuk, hogy pixelhűen egyeznek a Picasa kimenetével. A kalibráció (ha
valaha lesz hozzá mérési adat) a #317-es jegy feladata; addig ez a modul
dokumentáltan KÖZELÍTÉS.

A méretet megváltoztató (keretes) effektek — Border, DropShadow,
MuseumMatte, Polaroid — a testvérmodulban, `effects_frames.py`-ban vannak.

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3) — a projekt render-
rétegének konvenciója (ld. `picasapy.render.curves.validate_image`). Minden
függvény TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.curves import curve_lut, validate_image
from picasapy.render.glimmer_ops import inner_glow
from picasapy.render.glimmer_tone import vignette_radius
from picasapy.render.halftone import dot_size_for, native_dot_mask

_REC601_WEIGHTS = (0.299, 0.587, 0.114)

# FocalZoom: hány léptékű másolatot átlagolunk a zoom-elmosáshoz — KÖZELÍTÉS.
_FOCAL_ZOOM_STEPS = 8


def _luma(image_f: np.ndarray) -> np.ndarray:
    """Rec.601 luminancia float32 (H, W) tömbként (float32 bemenetből)."""
    red_w, green_w, blue_w = _REC601_WEIGHTS
    return (
        np.float32(red_w) * image_f[..., 0]
        + np.float32(green_w) * image_f[..., 1]
        + np.float32(blue_w) * image_f[..., 2]
    )


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


def _radius_grid(height: int, width: int, x: float, y: float) -> np.ndarray:
    """Pixelközéppontok normált távolsága az (x, y) középponttól, float32."""
    cols = (np.arange(width, dtype=np.float32) + 0.5) / np.float32(width) - np.float32(x)
    rows = (np.arange(height, dtype=np.float32) + 0.5) / np.float32(height) - np.float32(y)
    return np.hypot(rows[:, np.newaxis], cols[np.newaxis, :])


def apply_boost(image: np.ndarray, strength: float = 50.0) -> np.ndarray:
    """Felpörgetés (Boost): telítettség- és kontrasztnövelés együtt.

    KÖZELÍTŐ MODELL (#330, kalibráció: #317) — nincs golden-mérés. `strength`
    0..100 (a `filters=` `Boost=1,50.000000;` mintája szerint az alapérték
    50; 0 = változatlan kép). A telítettséget luma-tartó króma-erősítéssel,
    a kontrasztot a 128 körüli lineáris széthúzással növeljük, mindkettőt
    `strength`-tel arányosan skálázva — az arányok NEM mértek.
    """
    validate_image(image)
    if strength < 0:
        raise ValueError(f"A felpörgetés erőssége nem lehet negatív: {strength}")
    if strength == 0:
        return image.copy()
    amount = np.float32(strength / 100.0)
    image_f = image.astype(np.float32)
    luma = _luma(image_f)[..., np.newaxis]
    saturated = luma + (np.float32(1.0) + amount) * (image_f - luma)
    contrast_gain = np.float32(1.0) + np.float32(0.5) * amount
    boosted = np.float32(128.0) + contrast_gain * (saturated - np.float32(128.0))
    return _to_uint8(boosted)


def apply_soften(image: np.ndarray, amount: float = 50.0, radius: float = 50.0) -> np.ndarray:
    """Lágyítás (Soften): lágy Gauss-elmosás keverése az eredetivel.

    KÖZELÍTŐ MODELL (#330, kalibráció: #317). `amount` 0..100 a keverési
    súly (0 = változatlan kép), `radius` 0..100 az elmosás sugarát skálázza
    a kép rövidebb oldalának százalékában — mindkettő alapértéke 50 (a
    `Soften=1,50.000000,50.000000;` minta szerint). A keverés miatt a
    részletek csak részben tűnnek el (nem tiszta elmosás).
    """
    validate_image(image)
    if amount < 0:
        raise ValueError(f"A lágyítás erőssége nem lehet negatív: {amount}")
    if radius < 0:
        raise ValueError(f"A lágyítás sugara nem lehet negatív: {radius}")
    if amount == 0:
        return image.copy()
    height, width = image.shape[:2]
    sigma = max(radius / 100.0 * 0.06 * min(height, width), 0.1)
    blurred = cv2.GaussianBlur(image, (0, 0), sigma).astype(np.float32)
    weight = np.float32(min(amount, 100.0) / 100.0)
    image_f = image.astype(np.float32)
    return _to_uint8(image_f + weight * (blurred - image_f))


def apply_pixelate(image: np.ndarray, block_size: float = 20.0) -> np.ndarray:
    """Képpontnagyítás (Pixelate): blokkosítás le-fel mintavételezéssel.

    KÖZELÍTŐ MODELL (#330, kalibráció: #317). `block_size` 0..100, a blokk
    élhossza a kép rövidebb oldalának százalékában (a
    `Pixelate=1,20.000000,...` minta szerint az alapérték 20). A képet a
    blokkméretre lekicsinyítjük (területi átlagolás, `INTER_AREA`), majd
    `INTER_NEAREST`-tel visszanagyítjuk — így blokkon belül minden pixel
    azonos.
    """
    validate_image(image)
    if block_size < 0:
        raise ValueError(f"A blokkméret nem lehet negatív: {block_size}")
    if block_size == 0:
        return image.copy()
    height, width = image.shape[:2]
    block_px = max(1, round(min(height, width) * block_size / 100.0))
    small_h = max(1, round(height / block_px))
    small_w = max(1, round(width / block_px))
    small = cv2.resize(image, (small_w, small_h), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (width, height), interpolation=cv2.INTER_NEAREST)


def apply_pencil_sketch(
    image: np.ndarray,
    blur_radius: float = 2.0,
    brightness: float = 100.0,
    color_mix: float = 0.0,
) -> np.ndarray:
    """Ceruzarajz (PencilSketch): szürkeárnyalat + invertált elmosás,
    színes-dodge (color-dodge) keveréssel.

    KÖZELÍTŐ MODELL (#330, kalibráció: #317). `blur_radius` a Gauss-elmosás
    σ-ja pixelben (a `PencilSketch=1,2.000000,...` minta szerint alapból
    2,0), `brightness` 0..200 a végeredmény fényerő-skálázása (100 =
    változatlan), `color_mix` 0..100 mennyi eredeti színt kever vissza a
    szürke rajzba (0 = tiszta szürkeárnyalatos ceruzarajz — az ini
    alapértéke). A color-dodge keverés: `rajz = szürke·255/(255 −
    elmosott_invertált)`, klippelve — a sík/világos területek szinte
    fehérré válnak, a részletgazdag élek sötétebb vonalként maradnak meg.
    """
    validate_image(image)
    if blur_radius < 0:
        raise ValueError(f"Az elmosás sugara nem lehet negatív: {blur_radius}")
    if brightness < 0:
        raise ValueError(f"A fényerő nem lehet negatív: {brightness}")
    if not 0.0 <= color_mix <= 100.0:
        raise ValueError(f"A színkeverés 0..100 tartományba kell essen: {color_mix}")
    image_f = image.astype(np.float32)
    gray = _luma(image_f)
    inverted = np.float32(255.0) - gray
    sigma = max(blur_radius, 0.1)
    blurred = cv2.GaussianBlur(inverted, (0, 0), sigma).astype(np.float32)
    denom = np.clip(np.float32(255.0) - blurred, 1.0, 255.0)
    sketch = np.clip(gray * np.float32(255.0) / denom, 0.0, 255.0)
    sketch = np.clip(sketch * np.float32(brightness / 100.0), 0.0, 255.0)
    gray_rgb = np.stack([sketch, sketch, sketch], axis=-1)
    if color_mix == 0.0:
        return _to_uint8(gray_rgb)
    mix = np.float32(color_mix / 100.0)
    return _to_uint8(gray_rgb + mix * (image_f - gray_rgb))


def pixelate_shifted(image: np.ndarray, tile: int, offset_x: float, offset_y: float) -> np.ndarray:
    """Csempeméretű pixelesítés, `offset`-tel eltolt rácson (#1351).

    A `glimmer` `PixelateImageOperation`-je `offsetX`/`offsetY`
    paramétert is kap; a `Comicize` második fázisában ez
    `_nDotSize/2` — a rács fél csempével el van tolva.

    ⚠️ **NINCS szegély-kiterjesztés**: a `filterdesc.xml`-ben egyik maszk
    sem ad meg `padding` értéket, tehát mind a négy 0, és a rács pontosan
    a kép méretére feszül. A jobb/alsó szélen kilógó csempét a KÉPHATÁR
    vágja — ezért dolgozunk `cv2.INTER_AREA`/`INTER_NEAREST` párral egy
    eltolt vágáson, és nem `copyMakeBorder`-rel.
    """
    height, width = image.shape[:2]
    dx = int(round(offset_x)) % max(1, tile)
    dy = int(round(offset_y)) % max(1, tile)
    if dx == 0 and dy == 0:
        kicsi = cv2.resize(
            image,
            (max(1, width // tile), max(1, height // tile)),
            interpolation=cv2.INTER_AREA,
        )
        return cv2.resize(kicsi, (width, height), interpolation=cv2.INTER_NEAREST)

    #: az eltolt rácshoz a képet elcsúsztatva pixelesítjük, majd
    #: visszacsúsztatjuk — a kilógó rész a képhatáron kívül marad, épp
    #: úgy, ahogy a nulla padding megköveteli.
    csuszt = np.roll(image, shift=(-dy, -dx), axis=(0, 1))
    kicsi = cv2.resize(
        csuszt,
        (max(1, width // tile), max(1, height // tile)),
        interpolation=cv2.INTER_AREA,
    )
    nagy = cv2.resize(kicsi, (width, height), interpolation=cv2.INTER_NEAREST)
    return np.roll(nagy, shift=(dy, dx), axis=(0, 1))


#: A `Comicize` fő küszöbgörbéjének RÖGZÍTETT töréspontjai — a
#: `filterdesc.xml` `<filter id="Comicize">` blokkjának
#: `AdjustCurvesImageOperation MasterCurve`-je szó szerint (#1606):
#: `[{0,0}, {24,24}, {48,48}, {90+DotContrast·1,5, 254}, {255,255}]`.
#: A negyedik pont x-ét a DotContrast mozgatja, a többi négy kötött.
_COMICIZE_CURVE_HEAD = ((0.0, 0.0), (24.0, 24.0), (48.0, 48.0))
_COMICIZE_CURVE_TAIL = (255.0, 255.0)
#: A mozgó pont y-ja — a `filterdesc.xml`-ben 254, NEM 255.
_COMICIZE_CURVE_KNEE_Y = 254.0


def comicize_master_curve(dot_contrast: float) -> np.ndarray:
    """A `Comicize` fő küszöbgörbéje 256 elemű float LUT-ként (#1606).

    A korábbi modell ezt `érték · 255 / (90 + DotContrast·1,5)` lineáris
    skálázásra egyszerűsítette. A `filterdesc.xml` viszont ÖTPONTOS
    görbét ad, és a natív kiértékelés természetes köbös spline (#629,
    `curves.curve_lut`) — a két alsó pont (24 és 48) miatt az árnyékok
    IDENTITÁSBAN maradnak, a lineáris skálázás viszont már ott is
    másfélszeresre húzta őket.

    A mozgó töréspont x-e a képhatárhoz van vágva: a csúszka tartománya
    `0…100`, tehát `DotContrast = 100`-nál `90 + 150 = 240`, ami még
    belefér. A vágás csak védőkorlát arra az esetre, ha a hívó ezen a
    tartományon kívüli értéket ad (a görbe x-einek szigorúan növekvőnek
    kell lenniük).

    ⚠️ **A spline 255 fölé lő, és ezt VÁGNI kell.** A meredek negyedik
    szakasz miatt a köbös spline a `0…100` tartományban VÉGIG 255 fölé megy,
    majd visszaereszkedik 255-re — a nyers maximum `DotContrast = 0`-nál
    417, az alapállásban (50) 272, `100`-nál pedig épp 255. Vágás nélkül a
    LUT NEM monoton, és a raszter a világos tónusokon visszafordulna. A natív művelet 8 bites pufferbe ír,
    tehát ott ugyanez a vágás történik (ld. `curves.apply_lut`); a vágott
    görbe monoton nemcsökkenő.
    """
    knee_x = float(np.clip(90.0 + dot_contrast * 1.5, 49.0, 254.0))
    curve = curve_lut(
        (*_COMICIZE_CURVE_HEAD, (knee_x, _COMICIZE_CURVE_KNEE_Y), _COMICIZE_CURVE_TAIL)
    )
    return np.clip(curve, 0.0, 255.0)


#: A 788. sor Glow-sugara a `Vignette` `Blur = 70`-es láncával egyezik:
#: `35 · 0,02 · max(W,H) / 2 = 70 · 0,02 · max(W,H) / 4` (#3522).
_COMICIZE_GLOW_BLUR = 70.0
#: 788. sor: `strength="1.1"`
_COMICIZE_GLOW_STRENGTH = 1.1
#: Az ágankénti küszöbgörbe (`filterdesc.xml`): `[0,0][150,0][160,255][255,255]`.
#: ⚠️ A természetes spline a 150–160 közti ugrásnál −724 és +690 közé lő ki —
#: a VÁGÁS a görbe része (mint a `comicize_master_curve`-nél), nem elhagyható.
_COMICIZE_KUSZOB = np.clip(
    curve_lut(((0.0, 0.0), (150.0, 0.0), (160.0, 255.0), (255.0, 255.0))), 0.0, 255.0
).astype(np.float32)


def _comicize_dot_branch(curved: np.ndarray, tile: int, offset_x: float, offset_y: float) -> np.ndarray:
    """Egy raszter-ág (2c): pixelesítés → szürke → a pontmaszk mint
    `PartialMask` a fehér fölé → küszöbgörbe → `add` a pixelesített színnel."""
    height, width = curved.shape[:2]
    pixelated = pixelate_shifted(curved, tile, offset_x, offset_y)
    szurke = _luma(pixelated)
    maszk = native_dot_mask(height, width, tile, offset_x, offset_y) / np.float32(255.0)
    fedett = np.float32(255.0) + (szurke - np.float32(255.0)) * maszk
    kuszob = _COMICIZE_KUSZOB[np.clip(np.rint(fedett), 0, 255).astype(np.uint8)]
    return np.minimum(np.float32(255.0), kuszob[..., np.newaxis] + pixelated)


def apply_comicize(
    image: np.ndarray,
    blur_xy: float = 20.0,
    dot_contrast: float = 50.0,
    dot_fade: float = 50.0,
) -> np.ndarray:
    """Képregény (Comicize) — nyomdai féltónusos raszter, a `filterdesc.xml`
    szó szerinti lánca szerint (772–824. sor; #569, #3522).

    A lánc — MINDEN lépés együtt (#3511, #3522):

    1. `darkened = min(kép, elmosás)` (`_opBlur`, `BlendMode=darken`), az
       elmosás szigmája `1 + 20·BlurXY/100`;
    2. a `_opColorSpots` blokk a `darkened`-en:

       a. **fekete belső ragyogás** (788. sor: `GlowImageOperation color="0"
          innerglow="true" strength="1.1" quality="3"`,
          `xblur = yblur = 35·0,02·max(W,H)/2` — ez a `Vignette`
          `Blur = 70`-es sugara, `glimmer_tone.vignette_radius`);
       b. `AdjustCurves` a `DotContrast` ötpontos görbéjével
          (`comicize_master_curve`);
       c. két ág, a második fél csempével eltolva (793. és 807. sor): saját
          `Pixelate`, Haeberli-szürke (#3507), a natív 8.8-as pontmaszk
          (`halftone.native_dot_mask`, #3390) mint `PartialMask` a FEHÉR
          fölé — `255 + (szürke − 255) · m` —, a
          `[0,0][150,0][160,255][255,255]` küszöbgörbe, majd `add` a
          pixelesített színnel;
       d. a két ág `darken`-nel;

    3. a blokk `multiply`-jal kerül a `darkened`-re, `BlendAlpha =
       0,5 − DotFade/200` alfával.

    ## Mérve (#3522)

    A `research/comicize-sweep/` 15 eredeti Picasa-exportján, a #3401
    mérőjével (a csempén belüli fázisprofil szórása és ΔE76):

    | | átl. amplitúdó-hiba | átl. ΔE76 |
    |---|---:|---:|
    | a korábbi küszöb-modell (1 px-es lágyítással) | 1,4331 | 2,8293 |
    | **ez a lánc** | **0,0276** | **2,4640** |

    ⚠️ A #1606 a Glow-t, a `multiply`-t és a küszöbgörbét EGYENKÉNT próbálta,
    és egyenként mindegyik rontott — csak együtt helyesek. A maradék ΔE
    (≈2,46) forrása nincs mérve (jelöltek: a Gauss-elmosás a natív helyett,
    a szürke kerekítése).
    """
    validate_image(image)
    for name, value in (
        ("BlurXY", blur_xy),
        ("DotContrast", dot_contrast),
        ("DotFade", dot_fade),
    ):
        if value < 0:
            raise ValueError(f"A(z) {name} nem lehet negatív: {value}")

    height, width = image.shape[:2]
    dot = dot_size_for(width)
    image_f = image.astype(np.float32)

    # 1. elő-elmosás DARKEN módban (a sötétebb nyer)
    sigma = 1.0 + 20.0 * min(blur_xy, 100.0) / 100.0
    blurred = cv2.GaussianBlur(image_f, (0, 0), sigmaX=sigma, sigmaY=sigma)
    darkened = np.minimum(image_f, blurred)

    # 2a. a blokkot nyitó fekete belső ragyogás (788. sor)
    sugar = vignette_radius(_COMICIZE_GLOW_BLUR, width, height)
    glowed = inner_glow(
        np.clip(np.rint(darkened), 0.0, 255.0).astype(np.uint8),
        (0, 0, 0), sugar, sugar, _COMICIZE_GLOW_STRENGTH, alpha=1.0,
    )

    # 2b. a DotContrast-görbe — LUT-indexeléssel (#2477: a natív művelet 8
    # bites pufferbe ír)
    curve = comicize_master_curve(min(dot_contrast, 100.0))
    curved = curve[glowed].astype(np.float32)

    # 2c-d. a két, fél csempével eltolt ág, DARKEN-nel
    raster = np.minimum(
        _comicize_dot_branch(curved, dot, 0.0, 0.0),
        _comicize_dot_branch(curved, dot, dot / 2.0, dot / 2.0),
    )

    # 3. MULTIPLY a darkened-re, a blokk alfájával
    alpha = float(np.clip(0.5 - min(dot_fade, 100.0) / 200.0, 0.0, 1.0))
    combined = darkened * raster / np.float32(255.0)
    return _to_uint8(darkened + alpha * (combined - darkened))


