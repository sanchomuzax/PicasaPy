"""A Picasa 4. fülének (zöld ecset) kreatív effektjei — I. rész: IR, Lomo,
Holga, Cinemascope, Orton, Sixties.

**ŐSZINTESÉG (#329):** a Picasa e 12 effektjének pontos algoritmusa NEM
publikus, és ehhez NINCS golden-mérés (szemben a `docs/specs/filters-decoded.md`
alatt dokumentált, mért szűrőkkel). Az itt implementált modellek a fotós
szakirodalomból ismert hatás-JELLEGET közelítik (pl. mit csinál egy klasszikus
infravörös film, egy lomo-kamera vagy egy anamorf szélesvásznú felvétel) — NEM
állítjuk, hogy pixelhűen egyeznek a Picasa kimenetével. A kalibráció (ha
valaha lesz hozzá mérési adat) a #317-es jegy feladata; addig ez a modul
dokumentáltan KÖZELÍTÉS.

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3) — a projekt render-
rétegének konvenciója (ld. `picasapy.render.curves.validate_image`). Minden
függvény TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

from picasapy import cv as cv2
import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.effects import apply_vignette

_REC601_WEIGHTS = (0.299, 0.587, 0.114)


def _luma(image: np.ndarray) -> np.ndarray:
    """Rec.601 luminancia float32 (H, W) tömbként."""
    red_w, green_w, blue_w = _REC601_WEIGHTS
    return (
        np.float32(red_w) * image[..., 0].astype(np.float32)
        + np.float32(green_w) * image[..., 1].astype(np.float32)
        + np.float32(blue_w) * image[..., 2].astype(np.float32)
    )


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


def apply_ir(image: np.ndarray, strength: float = 1.0) -> np.ndarray:
    """Infravörös film hatás — KÖZELÍTÉS (#329, kalibráció: #317).

    Modell: vörös-csatorna dominancia (a klasszikus IR-film jellege szerint
    a vörös/közeli-infravörös tartomány felülreprezentált) + kontraszt-
    növelés a szürkeárnyalaton + halvány izzás (Gauss-elmosott fényes
    területek screen-keverése). A pontos csatornagörbe és izzás-erősség
    NEM mért — a fotós szakirodalomban leírt hatás-jelleget közelíti.
    """
    validate_image(image)
    if strength < 0:
        raise ValueError(f"Az IR effekt erőssége nem lehet negatív: {strength}")
    if strength == 0:
        return image.copy()
    gray = _luma(image)
    contrast_gain = np.float32(1.0 + 0.5 * strength)
    contrasted = np.clip(128.0 + (gray - 128.0) * contrast_gain, 0.0, 255.0)
    red = np.clip(contrasted * np.float32(1.0 + 0.25 * strength), 0.0, 255.0)
    green = np.clip(contrasted * np.float32(1.0 - 0.05 * strength), 0.0, 255.0)
    blue = np.clip(contrasted * np.float32(1.0 - 0.35 * strength), 0.0, 255.0)
    ir = np.stack([red, green, blue], axis=-1)
    blurred = cv2.GaussianBlur(_to_uint8(ir), (0, 0), 3.0).astype(np.float32)
    screen = 255.0 - (255.0 - ir) * (255.0 - blurred) / np.float32(255.0)
    glow_weight = np.float32(0.15 * strength)
    return _to_uint8(ir + glow_weight * (screen - ir))


def apply_lomo(
    image: np.ndarray,
    saturation: float = 1.6,
    contrast: float = 1.3,
    vignette_strength: float = 1.6,
) -> np.ndarray:
    """Lomo-kamera hatás — KÖZELÍTÉS (#329, kalibráció: #317).

    Modell: erős telítettség-növelés (luma-tartó króma-erősítés) + kontraszt-
    növelés + erős vignetta. A vignettát a mért `picasapy.render.effects`
    radiális maszkjával számoljuk (annak paraméterei is dokumentált
    közelítést tartalmaznak nem-alapértelmezett beállításokra); a
    telítettség/kontraszt-erősség itt megválasztott, NEM mért érték.
    """
    validate_image(image)
    if saturation < 0:
        raise ValueError(f"A telítettség nem lehet negatív: {saturation}")
    if contrast < 0:
        raise ValueError(f"A kontraszt nem lehet negatív: {contrast}")
    if vignette_strength < 0:
        raise ValueError(f"A vignetta erőssége nem lehet negatív: {vignette_strength}")
    image_f = image.astype(np.float32)
    luma = _luma(image)[..., np.newaxis]
    saturated = luma + np.float32(saturation) * (image_f - luma)
    contrasted = np.clip(128.0 + (saturated - 128.0) * np.float32(contrast), 0.0, 255.0)
    return apply_vignette(_to_uint8(contrasted), inner=30.0, strength=vignette_strength)


def apply_holga(
    image: np.ndarray,
    softness: float = 0.4,
    color_shift: tuple[float, float, float] = (8.0, -4.0, -18.0),
    vignette_strength: float = 2.0,
) -> np.ndarray:
    """Holga (lomografikus) hatás — KÖZELÍTÉS (#329, kalibráció: #317).

    Modell: lágy fókusz (Gauss-elmosott másolat felé keverés, a Holga-
    lencse jellemző lágyságát idézve) + csatornánkénti színeltolás + erős
    vignetta (a mért radiális maszkkal). Egyik komponens sem mért — a
    lomo-kamerák jellemző képi jegyeit közelíti.
    """
    validate_image(image)
    if not 0.0 <= softness <= 1.0:
        raise ValueError(f"A lágyítás 0..1 tartományba kell essen: {softness}")
    if vignette_strength < 0:
        raise ValueError(f"A vignetta erőssége nem lehet negatív: {vignette_strength}")
    if len(color_shift) != 3:
        raise ValueError(f"A színeltolás 3 elemű kell legyen: {color_shift!r}")
    image_f = image.astype(np.float32)
    sigma = 1.0 + 4.0 * softness
    blurred = cv2.GaussianBlur(image, (0, 0), sigma).astype(np.float32)
    softened = image_f + np.float32(softness) * (blurred - image_f)
    shift = np.array(color_shift, dtype=np.float32)
    shifted = np.clip(softened + shift, 0.0, 255.0)
    return apply_vignette(_to_uint8(shifted), inner=25.0, strength=vignette_strength)


def apply_cinemascope(
    image: np.ndarray, aspect_ratio: float = 2.39, tint_strength: float = 0.15
) -> np.ndarray:
    """Cinemascope (szélesvásznú) hatás — KÖZELÍTÉS (#329, kalibráció: #317).

    Modell: letterbox — a kép ALAKJA megmarad (a render-lánc ezt várja el),
    a `aspect_ratio` (alapértelmezetten 2,39:1) szerinti fekete sávok a
    kép tetejére/aljára kerülnek, plusz hűvös árnyalás (vörös csökkentése,
    kék emelése) az anamorf mozi jellemző hideg tónusát idézve. Nincs mért
    referencia; a sávok pontos vastagsága és a tónuseltolás mértéke itt
    megválasztott, NEM Picasa-hű érték.
    """
    validate_image(image)
    if aspect_ratio <= 0:
        raise ValueError(f"A képarány pozitív kell legyen: {aspect_ratio}")
    if not 0.0 <= tint_strength <= 1.0:
        raise ValueError(f"Az árnyalás erőssége 0..1 tartományba kell essen: {tint_strength}")
    height, width = image.shape[:2]
    target_height = min(height, max(1, round(width / aspect_ratio)))
    bar = max(0, (height - target_height) // 2)
    tinted = image.astype(np.float32)
    tinted[..., 0] = np.clip(tinted[..., 0] - 20.0 * tint_strength, 0.0, 255.0)
    tinted[..., 2] = np.clip(tinted[..., 2] + 20.0 * tint_strength, 0.0, 255.0)
    result = _to_uint8(tinted)
    if bar > 0:
        result[:bar, :, :] = 0
        result[height - bar :, :, :] = 0
    return result


def apply_orton(
    image: np.ndarray,
    brightness: float = 1.4,
    blur_sigma: float = 8.0,
    blend: float = 0.5,
) -> np.ndarray:
    """Orton-effekt (álomszerű, lágyan izzó kép) — KÖZELÍTÉS (#329, #317).

    Modell: az eredeti klasszikus sötétkamrás Orton-recept (két fényesített,
    elmosott réteg szorzat- és screen-keverése, majd az eredetivel
    keverve) egyszerűsített digitális változata: `screen` és `multiply`
    keverék az elmosott/fényesített réteggel, `blend` súllyal az
    eredetivel kombinálva. Az arányok NEM mértek, a hatás jellegét (lágy,
    izzó fény) közelítik.
    """
    validate_image(image)
    if brightness <= 0:
        raise ValueError(f"A fényesítés pozitív kell legyen: {brightness}")
    if blur_sigma <= 0:
        raise ValueError(f"Az elmosás szigmája pozitív kell legyen: {blur_sigma}")
    if not 0.0 <= blend <= 1.0:
        raise ValueError(f"A keverési súly 0..1 tartományba kell essen: {blend}")
    image_f = image.astype(np.float32)
    brightened = np.clip(image_f * np.float32(brightness), 0.0, 255.0)
    blurred = cv2.GaussianBlur(_to_uint8(brightened), (0, 0), blur_sigma).astype(np.float32)
    screen = 255.0 - (255.0 - image_f) * (255.0 - blurred) / np.float32(255.0)
    multiply = image_f * blurred / np.float32(255.0)
    combo = 0.5 * screen + 0.5 * multiply
    return _to_uint8(image_f + np.float32(blend) * (combo - image_f))


def apply_sixties(image: np.ndarray, fade: float = 0.35, warmth: float = 0.4) -> np.ndarray:
    """„60-as évek" fakó, meleg tónus — KÖZELÍTÉS (#329, kalibráció: #317).

    Modell: kontraszt-csökkentés (a kép a 128-as középszürke felé „fakul")
    + meleg, sárgás-zöldes csatornaeltolás (vörös és zöld emelése, kék
    csökkentése) — a korabeli színes filmek jellemző, fakó, sárgás
    patinájának közelítése. Nincs mért referenciapont.
    """
    validate_image(image)
    if not 0.0 <= fade <= 1.0:
        raise ValueError(f"A fakítás 0..1 tartományba kell essen: {fade}")
    if not 0.0 <= warmth <= 1.0:
        raise ValueError(f"A melegítés 0..1 tartományba kell essen: {warmth}")
    image_f = image.astype(np.float32)
    faded = 128.0 + (image_f - 128.0) * np.float32(1.0 - fade)
    warm = faded.copy()
    warm[..., 0] = np.clip(warm[..., 0] + 20.0 * warmth, 0.0, 255.0)
    warm[..., 1] = np.clip(warm[..., 1] + 12.0 * warmth, 0.0, 255.0)
    warm[..., 2] = np.clip(warm[..., 2] - 18.0 * warmth, 0.0, 255.0)
    return _to_uint8(warm)
