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

from picasapy.render.curves import validate_image
from picasapy.render.halftone import dot_size_for, halftone_branch

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


def apply_comicize(
    image: np.ndarray,
    blur_xy: float = 20.0,
    dot_contrast: float = 50.0,
    dot_fade: float = 50.0,
) -> np.ndarray:
    """Képregény (Comicize) — nyomdai FÉLTÓNUSOS raszter (#569).

    A korábbi modell posterizálással és **Canny-élkereséssel** közelítette; a
    Picasa effektje viszont nem élkiemelő képregényszűrő, hanem **két,
    egymáshoz képest fél csempével eltolt pontmaszkból** épített nyomdai
    raszter (`filterdesc.xml` + a natív `glimmer::TiledImageMask`).

    A csővezeték:

    1. `dotSize = round(W / 70) + 1` — a raszter csempemérete a kép
       SZÉLESSÉGÉBŐL (ld. `halftone.dot_size_for`);
    2. elő-elmosás `radius = 1 + 20·BlurXY/100` szigmával, **DARKEN** módban
       visszakeverve — ettől a sötét vonalak vastagodnak, a világosak nem;
    3. küszöbgörbe, amelynek a FELSŐ kontrollpontját a `DotContrast` mozgatja:
       `90 + DotContrast·1,5`;
    4. pixelesítés a csempeméretre, majd szürkeárnyalatos (BW) átalakítás —
       innen jön a pontonkénti „festéksűrűség";
    5. **két ág**, csempézett pontmaszkkal: az első eltolása `(0, 0)`, a
       másodiké `(dotSize/2, dotSize/2)`; az ágak **DARKEN**-nel egyesülnek;
    6. a blokk alfája `0,5 − DotFade/200`;
    7. a kész raszter **DARKEN** jelleggel kerül az eredeti képre.

    **Nyitott részlet** (a #569 elfogadási feltétele szerint is): a natív
    pontmaszk pontos antialiasingja és peremkerekítése — ehhez golden-
    összevetés kell (#317). A raszter szerkezete, a csempeméret képlete és a
    keverési módok viszont a `filterdesc.xml`-ből és a natív kódból valók.
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

    # 2. elő-elmosás DARKEN módban (a sötétebb nyer)
    sigma = 1.0 + 20.0 * min(blur_xy, 100.0) / 100.0
    blurred = cv2.GaussianBlur(image_f, (0, 0), sigmaX=sigma, sigmaY=sigma)
    darkened = np.minimum(image_f, blurred)

    # 3. küszöbgörbe — a felső kontrollpont a DotContrast-tól függ
    upper = float(np.clip(90.0 + min(dot_contrast, 100.0) * 1.5, 1.0, 255.0))
    curved = np.clip(darkened * (255.0 / upper), 0.0, 255.0)

    # 4. pixelesítés a csempeméretre + szürkeárnyalat
    small = cv2.resize(
        curved,
        (max(1, width // dot), max(1, height // dot)),
        interpolation=cv2.INTER_AREA,
    )
    pixelated = cv2.resize(
        small, (width, height), interpolation=cv2.INTER_NEAREST
    )
    ink = _luma(pixelated)

    # 5. két ág, fél csempével eltolva; az ágak DARKEN-nel egyesülnek
    branch_a = halftone_branch(ink, dot, 0.0, 0.0)
    branch_b = halftone_branch(ink, dot, dot / 2.0, dot / 2.0)
    raster = np.minimum(branch_a, branch_b)

    # 6-7. a blokk alfájával, DARKEN jelleggel az EREDETI képre
    alpha = float(np.clip(0.5 - min(dot_fade, 100.0) / 200.0, 0.0, 1.0))
    raster_rgb = np.repeat(raster[..., np.newaxis], 3, axis=-1)
    combined = np.minimum(image_f, raster_rgb)
    return _to_uint8(image_f + alpha * (combined - image_f))
