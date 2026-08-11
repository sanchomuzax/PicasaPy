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

#: A szépia luma-súlyai. #317: a `referencia/sepia/` exportján a
#: Flash-örökségű (0,3 / 0,59 / 0,11) súlyozás adta a legkisebb szórást a
#: luma-vödrökön belül (1,21) — a Rec.601 (1,26) és a Rec.709 (2,29)
#: rosszabb. A különbség kicsi, de következetes.
_SEPIA_LUMA_WEIGHTS = (0.3, 0.59, 0.11)

#: A szépia MÉRT tónusgörbéi (`referencia/sepia/`, 2560×1702-es export a
#: `filterdesc.xml`-en kívülről): luma 0, 16, 32 … 240, 255 → kimenő
#: csatornaérték. A korábbi lineáris közelítés (meredekség/eltolás
#: csatornánként) átlagosan **4,40**-gyel tért el a valódi Picasa-
#: kimenettől; ezekkel a horgonypontokkal **0,86** (viszonyításul: az
#: érintetlen kép eltérése 30,16). A görbe erősen nemlineáris — a kék
#: csatorna a sötét felén lapos, a világos felén meredek —, ezért nem
#: lehetett egyenessel eltalálni.
_SEPIA_ANCHOR_INPUTS = tuple(range(0, 256, 16)) + (255,)
_SEPIA_ANCHOR_CURVES = (
    (46.0, 61.9, 79.1, 95.1, 111.6, 128.1, 144.3, 160.4, 171.1, 181.6,
     192.2, 202.8, 213.6, 224.4, 234.6, 246.4, 254.8),
    (36.7, 49.2, 63.2, 77.2, 89.5, 103.1, 116.9, 132.5, 146.0, 159.5,
     173.3, 186.8, 201.4, 215.0, 228.7, 242.5, 254.8),
    (27.7, 39.4, 49.9, 61.0, 71.0, 81.2, 92.6, 108.1, 123.6, 140.0,
     157.4, 173.2, 190.1, 206.2, 222.7, 239.4, 254.4),
)
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
    """Szépia: luma → a MÉRT R/G/B tónusgörbék (#317).

    A valódi Picasa-kimenettől való átlagos csatorna-eltérés **0,86**
    (a korábbi lineáris közelítésé 4,40; az érintetlen képé 30,16).
    """
    validate_image(image)
    red_w, green_w, blue_w = _SEPIA_LUMA_WEIGHTS
    gray = (
        np.float32(red_w) * image[..., 0].astype(np.float32)
        + np.float32(green_w) * image[..., 1].astype(np.float32)
        + np.float32(blue_w) * image[..., 2].astype(np.float32)
    )
    ramp = lut_ramp()
    luts = tuple(
        np.interp(ramp, _SEPIA_ANCHOR_INPUTS, curve).astype(np.float32)
        for curve in _SEPIA_ANCHOR_CURVES
    )
    index = np.clip(np.rint(gray), 0, 255).astype(np.uint8)
    return _to_uint8(np.stack([lut[index] for lut in luts], axis=-1))


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
    gain = saturation_gain(strength)
    if gain == 1.0:
        return image.copy()
    luma = _luma(image)[..., np.newaxis]
    # float32 munkatér (#140): a ±1/255 tűrésen belül azonos eredmény
    return _to_uint8(luma + np.float32(gain) * (image.astype(np.float32) - luma))


def saturation_gain(strength: float) -> float:
    """A `sat` mért erősítés-táblájának (`_SATURATION_KNOTS`/`_GAINS`)
    interpolációja önmagában — a GPU-pipeline (#22, `gpu_point_pipeline.py`)
    ezt a skalárt kapja `satGain` uniformként, hogy a shaderben ugyanazt a
    `luma + gain·(be − luma)` képletet futtassa, mint a CPU-út."""
    clamped = min(max(strength, -1.0), 1.0)
    return float(np.interp(clamped, _SATURATION_KNOTS, _SATURATION_GAINS))
