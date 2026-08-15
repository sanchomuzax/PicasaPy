"""Szín-műveletek: bw, sepia, warm, sat.

A számértékek a golden-elemzés mérési eredményei
(`docs/specs/filters-decoded.md`): a bw pontosan Rec.601; a sepia a mért
csatornagörbék lineáris közelítése; a warm a binárisból kinyert, beégetett
tábla PONTOS leképezése (#611); a sat a mért gain-tábla interpolációja
luma-tartó króma-erősítésként.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import apply_channel_luts, lut_ramp, validate_image
from picasapy.render.saturation_positive import apply_positive_saturation
from picasapy.render.warmify_lut import warmify_lut_array

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
    """Melegítés: a natív `0x0090c040` munkafüggvény beégetett táblája (#611).

    A szűrő nem számol semmit — egyetlen, 256×3 elemű, csatornánkénti
    táblából olvas (`0x00d33b70`, PE-fájloffszet `0x933b70`,
    `docs/specs/picasa-native-filter-workers.md` 2.8. pont):

        out_R = tábla[R][0];  out_G = tábla[G][1];  out_B = tábla[B][2]

    Csatornánként a SAJÁT bemeneti értékével indexel (nem keresztbe), ezért
    csatornánkénti LUT-ként pontosan alkalmazható (#140: uint8-natív,
    képméret-független költség). PONTOS — nem közelítés.
    """
    validate_image(image)
    table = warmify_lut_array()
    luts = (
        table[:, 0].astype(np.float64),
        table[:, 1].astype(np.float64),
        table[:, 2].astype(np.float64),
    )
    return apply_channel_luts(image, luts)


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
    """Telítettség — a natív `sat` KÉT külön ága (#693).

    A callback (`0x008f8ff0`) az előjel szerint két külön magra ágazik:

    - **negatív** (`0x0090e200`): luma-keverés `1 + amount` erősítéssel,
      `ki = luma + gain·(be − luma)`;
    - **pozitív** (`0x0090b930`): NEM erősítés, hanem a `csatorna / luma`
      aránynak adott, csatornánként MÁS kitevőjű gamma
      (`saturation_positive`).

    A kettő nem vonható össze egyetlen képletbe: a pozitív ágra semmilyen
    skalár erősítés nem illeszthető (mérve, #693).
    """
    validate_image(image)
    clamped = min(max(float(strength), -1.0), 1.0)
    if clamped == 0.0:
        return image.copy()
    if clamped > 0.0:
        # #693: a POZITÍV ág nem erősítés, hanem csatornánkénti gamma a
        # `C/Y` arányon — ld. `saturation_positive`. A mérőszetten
        # (`golden-kit3/12-sat-sweep`) a hiba 13,34 → 0,74 szintre esett.
        return apply_positive_saturation(image, clamped)
    # A NEGATÍV ág luma-keverés, pontosan `1 + amount` erősítéssel: a natív
    # callback ezt adja át (`FUN_0090e200(dst, amount + 1.0f)`), és a mérés
    # is ezt igazolja (a korábbi interpolált tábla mindenhol azonos vagy
    # kicsit rosszabb volt).
    gain = 1.0 + clamped
    luma = _luma(image)[..., np.newaxis]
    # float32 munkatér (#140): a ±1/255 tűrésen belül azonos eredmény
    return _to_uint8(luma + np.float32(gain) * (image.astype(np.float32) - luma))


def saturation_gain(strength: float) -> float:
    """A `sat` erősítés-skalárja a GPU-előnézethez (#22).

    ⚠️ **A NEGATÍV ágon pontos, a POZITÍVON KÖZELÍTÉS (#693).** A CPU-út
    (`apply_saturation`) a pozitív oldalon már a natív, csatornánkénti
    gamma-modellt futtatja, amire **semmilyen skalár erősítés nem
    illeszthető**. A GPU-shader viszont ezt az egyetlen uniformot kapja,
    ezért élő csúszka-húzás közben az előnézet a pozitív oldalon eltér a
    véglegestől (a mérőszetten a különbség 13,3 vs. 0,7 szint). A tábla
    értékei ezért maradnak: ezek a MÉRT legjobb egy-skalár illesztések,
    tehát az előnézet így áll a legközelebb a végleges képhez.

    A GPU-oldal rendes lefedése külön jegy."""
    clamped = min(max(strength, -1.0), 1.0)
    return float(np.interp(clamped, _SATURATION_KNOTS, _SATURATION_GAINS))
