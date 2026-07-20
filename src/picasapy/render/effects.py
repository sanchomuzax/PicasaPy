"""Térbeli effekt-műveletek: Vignette, glow/glow2, radblur, radsat.

Mért alapok (`docs/specs/filters-decoded.md`):

- **Vignette** (4. kör): multiplikatív radiális maszk, a
  `Vignette=1,35.0,1.4,0.0,00000000` alapbeállításnál lemért profillal
  (közép 1,000 · r≈0,25: 0,994 · r≈0,45: 0,729 · r≈0,65: 0,328 ·
  sarok 0,250). A paraméterek analitikus modellje nyitott — a nem
  alapértelmezett paraméterek hatása itt KÖZELÍTÉS (sugár- és
  erősség-skálázás a mért profilon).
- **glow/glow2** (3. kör): sík szürkén mért középemelés
  (`glow=1,0.432749,2.469705` → 128→144; `glow2=1,0.65,3.0` → 128→151).
  A modell — screen-keverés Gauss-elmosott másolattal, súly ≈ 0,565·intenzitás
  — mindkét mért pontot ±1/255-ön belül visszaadja; a térbeli komponens
  (elmosási sugár szemantikája) KÖZELÍTÉS.
- **radblur / radsat**: nincs mért kimeneti adat (a golden-kit radblur-ja
  size=0, amount=0 → no-op volt) — a teljes térbeli modell dokumentált
  KÖZELÍTÉS; a #115 golden-harness pontosítja majd.
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.render.curves import validate_image

# A Vignette mért radiális profilja (r = képmérettel normált táv a középtől;
# a sarok r-je √0,5 ≈ 0,7071). A profilon túl a maszk a sarokértéken marad.
_VIGNETTE_RADII = (0.0, 0.25, 0.45, 0.65, 0.7071)
_VIGNETTE_GAINS = (1.0, 0.994, 0.729, 0.328, 0.250)

# A mért profil referencia-paraméterei (a golden-kit alapbeállítása).
_VIGNETTE_REF_INNER = 35.0
_VIGNETTE_REF_STRENGTH = 1.4

# glow: screen-keverési súly intenzitás-egységenként — a két mért középemelési
# pontból (v1: 0,251/0,4327 · v2: 0,361/0,65) illesztett közös érték.
_GLOW_WEIGHT_PER_INTENSITY = 0.565

#: A paraméter nélküli `glow` (v1) golden-kitben mért alapértékei.
GLOW_V1_INTENSITY = 0.432749
GLOW_V1_RADIUS = 2.469705

# radblur: az elmosás szigmája = amount · e szorzó · min(H, W) — KÖZELÍTÉS.
_RADBLUR_SIGMA_PER_AMOUNT = 0.05


def _radius_grid(height: int, width: int, x: float, y: float) -> np.ndarray:
    """Pixelközéppontok normált távolsága az (x, y) középponttól, float32."""
    cols = (np.arange(width, dtype=np.float32) + 0.5) / np.float32(width) - np.float32(x)
    rows = (np.arange(height, dtype=np.float32) + 0.5) / np.float32(height) - np.float32(y)
    return np.hypot(rows[:, np.newaxis], cols[np.newaxis, :])


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


def vignette_gain(
    radius: float,
    inner: float = _VIGNETTE_REF_INNER,
    strength: float = _VIGNETTE_REF_STRENGTH,
) -> float:
    """A Vignette multiplikatív maszkjának értéke a normált `radius` helyen.

    Az alapértelmezett paraméterekre a mért profilt adja vissza; más
    paraméterekre KÖZELÍTÉS: az `inner` a profilt sugárban skálázza
    (35 = referencia), a `strength` a sötétítés mélységét (1,4 = referencia).
    """
    if radius < 0:
        raise ValueError(f"A sugár nem lehet negatív: {radius}")
    scale = _VIGNETTE_REF_INNER / inner if inner > 0 else 1.0
    base = float(np.interp(radius * scale, _VIGNETTE_RADII, _VIGNETTE_GAINS))
    depth = strength / _VIGNETTE_REF_STRENGTH
    return float(np.clip(1.0 - depth * (1.0 - base), 0.0, 1.0))


def apply_vignette(
    image: np.ndarray,
    inner: float = _VIGNETTE_REF_INNER,
    strength: float = _VIGNETTE_REF_STRENGTH,
) -> np.ndarray:
    """Vignetta: a mért radiális maszkkal szorozza a képet (minden csatornát).

    A maszk középpontja a kép közepe; a 4. ini-paraméter (0,0) és az 5.
    (szín, 00000000) szerepe méretlen — figyelmen kívül hagyjuk (KÖZELÍTÉS).
    """
    validate_image(image)
    height, width = image.shape[:2]
    radii = _radius_grid(height, width, 0.5, 0.5)
    base = np.interp(
        radii * np.float32(_VIGNETTE_REF_INNER / inner if inner > 0 else 1.0),
        _VIGNETTE_RADII,
        _VIGNETTE_GAINS,
    ).astype(np.float32)
    depth = np.float32(strength / _VIGNETTE_REF_STRENGTH)
    mask = np.clip(1.0 - depth * (1.0 - base), 0.0, 1.0)
    return _to_uint8(image.astype(np.float32) * mask[..., np.newaxis])


def apply_glow(image: np.ndarray, intensity: float, radius: float) -> np.ndarray:
    """Ragyogás: screen-keverés a Gauss-elmosott másolattal.

    `ki = be + 0,565·intenzitás·(screen(be, gauss(be, σ=sugár)) − be)` —
    a súly a két mért középemelési pontból illesztett; a σ = sugár px
    értelmezés KÖZELÍTÉS (a térbeli komponens méretlen).
    """
    validate_image(image)
    if intensity < 0:
        raise ValueError(f"A glow intenzitása nem lehet negatív: {intensity}")
    weight = _GLOW_WEIGHT_PER_INTENSITY * intensity
    if weight == 0.0:
        return image.copy()
    sigma = radius if radius > 0 else GLOW_V1_RADIUS
    blurred = cv2.GaussianBlur(image, (0, 0), sigma).astype(np.float32)
    image_f = image.astype(np.float32)
    screen = 255.0 - (255.0 - image_f) * (255.0 - blurred) / np.float32(255.0)
    return _to_uint8(image_f + np.float32(weight) * (screen - image_f))


def apply_radblur(
    image: np.ndarray, x: float, y: float, size: float, amount: float
) -> np.ndarray:
    """Radiális elmosás: az (x, y) középpont körüli `size` zóna éles marad,
    kifelé az elmosott másolat felé keverünk.

    KÖZELÍTÉS (nincs mért kimeneti adat): σ = amount·0,05·min(H, W), a
    keverési súly a `size` sugártól a kép sarkáig lineárisan nő 0-ról 1-re.
    A mérten no-op eset (amount=0) identitás.
    """
    validate_image(image)
    if amount <= 0:
        return image.copy()
    height, width = image.shape[:2]
    sigma = amount * _RADBLUR_SIGMA_PER_AMOUNT * min(height, width)
    blurred = cv2.GaussianBlur(image, (0, 0), max(sigma, 0.1)).astype(np.float32)
    radii = _radius_grid(height, width, x, y)
    span = max(1.0 - size, 1e-6)
    weight = np.clip((radii - np.float32(size)) / np.float32(span), 0.0, 1.0)
    image_f = image.astype(np.float32)
    mixed = image_f + weight[..., np.newaxis] * (blurred - image_f)
    return _to_uint8(mixed)


def apply_radsat(
    image: np.ndarray, x: float, y: float, radius: float, sharpness: float
) -> np.ndarray:
    """Radiális telítettség: az (x, y) körüli `radius` zónán kívül a kép a
    Rec.601 luma felé telítetlenedik.

    KÖZELÍTÉS (nincs mért kimeneti adat): a zónán belül a kép változatlan,
    kívül a króma `1 − (r − radius)/(1 − sharpness)` súllyal tűnik el —
    `sharpness=1` éles határ, kisebb érték szélesebb átmenet.
    """
    validate_image(image)
    height, width = image.shape[:2]
    radii = _radius_grid(height, width, x, y)
    span = max(1.0 - sharpness, 1e-6)
    keep = np.clip(1.0 - (radii - np.float32(radius)) / np.float32(span), 0.0, 1.0)
    image_f = image.astype(np.float32)
    luma = (
        np.float32(0.299) * image_f[..., 0]
        + np.float32(0.587) * image_f[..., 1]
        + np.float32(0.114) * image_f[..., 2]
    )[..., np.newaxis]
    return _to_uint8(luma + keep[..., np.newaxis] * (image_f - luma))
