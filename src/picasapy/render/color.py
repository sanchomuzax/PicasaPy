"""Szín-műveletek: bw, sepia, warm, sat.

A számértékek a golden-elemzés mérési eredményei
(`docs/specs/filters-decoded.md`): a bw pontosan Rec.601; a sepia/warm a mért
csatornagörbék lineáris közelítése; a sat a mért gain-tábla interpolációja
luma-tartó króma-erősítésként.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import apply_channel_luts, lut_ramp, validate_image

_REC601_WEIGHTS = (0.299, 0.587, 0.114)

# Mért lineáris közelítések szürke bemenetre: (meredekség, eltolás) / csatorna.
_SEPIA_LINEAR = ((0.82, 58.0), (0.86, 35.0), (0.90, 15.0))
_WARM_LINEAR = ((0.89, 19.0), (0.88, 1.0), (0.93, -16.0))

# A sat mért gain-táblája (nem 1+s!); s=−1 → teljes telítetlenítés.
_SATURATION_KNOTS = (-1.0, -0.333, 0.0, 0.25, 0.5, 1.0)
_SATURATION_GAINS = (0.0, 0.683, 1.0, 1.399, 1.729, 2.241)


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


def _luma(image: np.ndarray) -> np.ndarray:
    """Rec.601 luminancia float32 (H, W) tömbként.

    float32 munkatér (#140): a 8 bites kimenethez bőven elegendő pontosság,
    fele akkora memóriaforgalommal, mint a float64.
    """
    red_w, green_w, blue_w = _REC601_WEIGHTS
    return (
        np.float32(red_w) * image[..., 0].astype(np.float32)
        + np.float32(green_w) * image[..., 1].astype(np.float32)
        + np.float32(blue_w) * image[..., 2].astype(np.float32)
    )


def apply_bw(image: np.ndarray) -> np.ndarray:
    """Fekete-fehér: Rec.601 luma csatornánként visszaírva (mérten pontos)."""
    validate_image(image)
    gray = _to_uint8(_luma(image))
    return np.stack([gray, gray, gray], axis=-1)


def _monochrome_tone(image: np.ndarray, linear: tuple) -> np.ndarray:
    """Luma-alapú monokróm tónus a mért lineáris csatornagörbékkel."""
    validate_image(image)
    gray = _luma(image)
    channels = [slope * gray + offset for slope, offset in linear]
    return _to_uint8(np.stack(channels, axis=-1))


def apply_sepia(image: np.ndarray) -> np.ndarray:
    """Szépia: monokróm tónus a mért R/G/B görbék lineáris közelítésével."""
    return _monochrome_tone(image, _SEPIA_LINEAR)


def apply_warm(image: np.ndarray) -> np.ndarray:
    """Melegítés: a mért csatornagörbék lineáris közelítése csatornánként.

    (A görbéket szürke rámpán mértük; színes képen csatornánként a saját
    értékre alkalmazzuk — közelítés.)
    """
    validate_image(image)
    # csatornánkénti lineáris görbe → csatornánkénti LUT (#140):
    # uint8-natív, képméret-független költség
    ramp = lut_ramp()
    luts = tuple(slope * ramp + offset for slope, offset in _WARM_LINEAR)
    return apply_channel_luts(image, (luts[0], luts[1], luts[2]))


#: Golden mérés (`docs/specs/filters-decoded.md`): meredekség ≈1,000,
#: eltolás ≈−2,7 — a grain2 átlagban identitás, a kerekítés/clip miatti
#: apró eltolás itt elhanyagolható, a zajat zérus középértékkel modellezzük.
_GRAIN_DEFAULT_SIGMA = 8.0


def apply_grain(
    image: np.ndarray, sigma: float = _GRAIN_DEFAULT_SIGMA, seed: int | None = None
) -> np.ndarray:
    """Filmszemcse (grain2) — sztochasztikus, pixelhűen NEM reprodukálható.

    A golden-elemzés szerint (`docs/specs/filters-decoded.md`) a grain2
    átlagban identitás (meredekség ≈1,000, eltolás ≈−2,7), zérus körüli
    additív zaj véletlen maggal — az elfogadási teszt statisztikai
    (zaj-σ, spektrum), NEM pixel-diff. Ugyanaz a zajérték kerül mindhárom
    csatornára pixelenként (monokróm szemcse, nem színes „snow"), így a
    kép átlaga megmarad, csak a szórása nő.

    `seed`-del determinisztikus/reprodukálható; `seed=None` esetén a zaj
    valóban véletlen (`numpy` alapértelmezett generátora).
    """
    validate_image(image)
    height, width = image.shape[:2]
    rng = np.random.default_rng(seed)
    noise = rng.normal(loc=0.0, scale=sigma, size=(height, width)).astype(np.float32)
    noisy = image.astype(np.float32) + noise[..., np.newaxis]
    return _to_uint8(noisy)


def apply_saturation(image: np.ndarray, strength: float) -> np.ndarray:
    """Telítettség: luma-tartó króma-erősítés a mért gain-táblával.

    `ki = luma + gain(s)·(be − luma)`; a gain a mért pontok közti lineáris
    interpoláció, s∈[−1..1]-re szorítva.
    """
    validate_image(image)
    clamped = min(max(strength, -1.0), 1.0)
    gain = float(np.interp(clamped, _SATURATION_KNOTS, _SATURATION_GAINS))
    if gain == 1.0:
        return image.copy()
    luma = _luma(image)[..., np.newaxis]
    # float32 munkatér (#140): a ±1/255 tűrésen belül azonos eredmény
    return _to_uint8(luma + np.float32(gain) * (image.astype(np.float32) - luma))
