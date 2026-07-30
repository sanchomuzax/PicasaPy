"""A Picasa 5. fülének (kék ecset) művészi effektjei — I. rész: Boost, Soften,
Pixelate, FocalZoom, PencilSketch, Neon, Comicize.

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

import cv2
import numpy as np

from picasapy.render.curves import validate_image

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


def apply_focal_zoom(
    image: np.ndarray,
    x: float = 0.5,
    y: float = 0.5,
    radius: float = 50.0,
    strength: float = 50.0,
) -> np.ndarray:
    """Fókusznagyítás (FocalZoom): sugárirányú (zoom) elmosás a fókuszpont
    körül, középen éles.

    KÖZELÍTŐ MODELL (#330, kalibráció: #317). `x, y` a fókuszpont relatív
    [0..1] koordinátája (alapból a kép közepe, a `FocalZoom=1,0.5,0.5,...`
    mintának megfelelően), `radius` 0..100 az éles zóna sugara (a kép
    normált átlójának százalékában), `strength` 0..100 a zoom-elmosás
    mértéke. A fókuszponton belül a kép éles marad; kifelé a képnek az
    (x, y) középpontra egyre nagyobb léptékben nagyított másolatainak
    átlaga (zoom-blur) keveredik be, a középponttól mért távolsággal
    arányos súllyal.
    """
    validate_image(image)
    if not 0.0 <= x <= 1.0 or not 0.0 <= y <= 1.0:
        raise ValueError(f"Az (x, y) fókuszpont 0..1 tartományba kell essen: ({x}, {y})")
    if radius < 0:
        raise ValueError(f"A sugár nem lehet negatív: {radius}")
    if strength < 0:
        raise ValueError(f"A zoom-elmosás erőssége nem lehet negatív: {strength}")
    if strength == 0:
        return image.copy()
    height, width = image.shape[:2]
    center = (x * width, y * height)
    max_scale = 1.0 + 0.3 * min(strength, 100.0) / 100.0
    accum = np.zeros((height, width, 3), dtype=np.float32)
    for step in range(_FOCAL_ZOOM_STEPS):
        scale = 1.0 + (max_scale - 1.0) * step / (_FOCAL_ZOOM_STEPS - 1)
        matrix = cv2.getRotationMatrix2D(center, 0.0, scale)
        warped = cv2.warpAffine(
            image,
            matrix,
            (width, height),
            flags=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REPLICATE,
        )
        accum += warped.astype(np.float32)
    zoom_blurred = accum / np.float32(_FOCAL_ZOOM_STEPS)
    radii = _radius_grid(height, width, x, y)
    span = max(1.0 - radius / 100.0, 1e-6)
    weight = np.clip((radii - np.float32(radius / 100.0)) / np.float32(span), 0.0, 1.0)
    image_f = image.astype(np.float32)
    result = image_f + weight[..., np.newaxis] * (zoom_blurred - image_f)
    return _to_uint8(result)


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


def apply_neon(
    image: np.ndarray, intensity: float = 50.0, color: tuple[int, int, int] = (0, 255, 170)
) -> np.ndarray:
    """Neon: éldetektálás színes izzással, sötét háttéren.

    KÖZELÍTŐ MODELL (#330, kalibráció: #317) — a `Neon=1,0.000000,00ff0000;`
    minta paramétereinek jelentése (csúszka-leképezés) NEM dekódolt, a
    `color` alapértéke itt választott közelítés (nem a mért ini-minta
    színe). `intensity` 0..100 az izzás erőssége. Canny-éldetektálás →
    az élek Gauss-elmosott, `color` színű izzása fekete alapon; élmentes
    (sík) területeken a kimenet közel fekete.
    """
    validate_image(image)
    if intensity < 0:
        raise ValueError(f"A neon-izzás erőssége nem lehet negatív: {intensity}")
    if len(color) != 3:
        raise ValueError(f"A szín 3 elemű (R, G, B) kell legyen: {color!r}")
    gray = _to_uint8(_luma(image.astype(np.float32)))
    edges = cv2.Canny(gray, 50, 150).astype(np.float32) / np.float32(255.0)
    glow_mask = cv2.GaussianBlur(edges, (0, 0), 1.5)
    glow_mask = np.clip(glow_mask * np.float32(0.5 + intensity / 100.0), 0.0, 1.0)
    color_arr = np.array(color, dtype=np.float32)
    result = glow_mask[..., np.newaxis] * color_arr
    return _to_uint8(result)


def apply_comicize(
    image: np.ndarray,
    edge_strength: float = 20.0,
    posterize: float = 50.0,
    smoothness: float = 50.0,
) -> np.ndarray:
    """Képregény (Comicize): színposzterizálás + erős fekete élkontúr.

    KÖZELÍTŐ MODELL (#330, kalibráció: #317). `edge_strength` 0..100 a
    kontúrvonal vastagsága, `posterize` 0..100 a színposzterizálás
    erőssége (nagyobb érték = kevesebb színszint), `smoothness` 0..100 az
    éldetektálás előtti simítás mértéke — az alapértékek a
    `Comicize=1,20.000000,50.000000,50.000000;` mintát követik (a
    paraméterek pontos jelentése nem dekódolt). A poszterizált színekre
    fekete kontúrvonalat rajzolunk a (simított) szürkeárnyalatos képen
    talált élek mentén.
    """
    validate_image(image)
    if edge_strength < 0:
        raise ValueError(f"A kontúr erőssége nem lehet negatív: {edge_strength}")
    if posterize < 0:
        raise ValueError(f"A poszterizálás erőssége nem lehet negatív: {posterize}")
    if smoothness < 0:
        raise ValueError(f"A simítás erőssége nem lehet negatív: {smoothness}")
    image_f = image.astype(np.float32)
    num_levels = max(2, round(12.0 - min(posterize, 100.0) / 100.0 * 10.0))
    step = 256.0 / num_levels
    posterized = np.clip(np.floor(image_f / step) * step + step / 2.0, 0.0, 255.0)

    blur_sigma = max(smoothness / 100.0 * 3.0, 0.1)
    smooth_gray = cv2.GaussianBlur(
        _to_uint8(_luma(image_f)), (0, 0), blur_sigma
    )
    edges = cv2.Canny(smooth_gray, 50, 150)
    thickness = max(1, round(1 + min(edge_strength, 100.0) / 100.0 * 3.0))
    kernel = np.ones((thickness, thickness), dtype=np.uint8)
    edge_mask = cv2.dilate(edges, kernel) > 0

    result = posterized.copy()
    result[edge_mask] = 0.0
    return _to_uint8(result)
