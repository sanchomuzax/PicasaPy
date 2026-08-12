"""Tónus-műveletek: fill light, highlights/shadows, színhőmérséklet,
semleges-szín pipetta és a `finetune2` kompozit.

**#551: a négy Finomhangolás-csúszka mind mérésből származik** — a
`sanchomuzax/picasapy-agent` privát repó `referencia/deritofeny/`,
`referencia/szinhomerseklet/` és `referencia/finomhangolas/` készleteiből
(ugyanaz a fotó, csúszkánként több állásban, a valódi Picasa 3.9
kimenetével). A korábbi közelítések átlagos csatorna-eltérése a Picasa
kimenetétől 18–23 volt; a mérésből kapott modelleké 0,8–5,9 (a JPEG-zaj
szintje ~1). A pipetta modellje egyelőre változatlan közelítés.
"""

from __future__ import annotations

import re

import numpy as np

from picasapy.render.curves import (
    apply_channel_luts,
    apply_lut,
    lut_ramp,
    validate_image,
)

#: **Derítőfény (#551).** A mérés kimondta a modell alakját: a művelet
#: NEM csatornánkénti tónusgörbe, hanem a pixel VILÁGOSSÁGÁTÓL függő,
#: mindhárom csatornára AZONOS hozzáadás — `ki = be + d(világosság)`. A
#: bizonyíték: egy-egy világosság-sávon belül a három csatorna szorzója
#: gyakorlatilag megegyezik (pl. max állásban 11,12 / 11,54 / 11,41), a
#: csatornánkénti görbék látszólagos eltérése csak abból ered, hogy azonos
#: bemeneti szinten más-más világosságú pixelek keverednek. A világosság a
#: három csatorna SZÁMTANI ÁTLAGA (a mérésen ez adta a legkisebb hibát:
#: 5,56 — a 0,30/0,59/0,11 súlyozás 5,95, a Rec.709 6,21, a max 9,38).
_FILL_LUMA_ANCHORS = (
    0, 4, 8, 16, 24, 32, 48, 64, 80, 96, 112, 128, 144, 160, 176, 192, 208,
    224, 240, 255,
)
#: A mért csúszka-állások és a hozzájuk tartozó `d(világosság)` görbék.
#: A közbenső állásokra a szomszédos görbék lineáris keveréke.
_FILL_STRENGTHS = (0.0, 0.10, 0.25, 0.50, 0.75, 1.00)
_FILL_DELTAS = (
    (0.0,) * 20,
    (0.2, 0.1, 1.0, 2.1, 3.2, 4.1, 4.8, 5.5, 5.9, 5.9, 5.7, 5.3, 4.7, 4.3,
     3.7, 3.0, 2.1, 1.2, 0.3, -0.4),
    (1.3, 3.4, 6.5, 11.0, 13.7, 15.9, 18.9, 20.6, 21.3, 20.9, 20.2, 19.1,
     17.1, 15.1, 13.1, 10.7, 8.3, 5.4, 2.3, -0.8),
    (2.6, 11.4, 19.0, 27.9, 34.0, 38.5, 43.8, 46.2, 46.8, 45.0, 42.7, 39.7,
     35.2, 31.0, 26.5, 21.6, 16.5, 10.9, 4.8, -1.2),
    (7.9, 35.5, 50.2, 66.6, 76.1, 82.3, 87.9, 88.7, 86.7, 81.1, 75.2, 68.3,
     59.7, 51.5, 43.5, 34.6, 25.8, 16.6, 7.3, -2.1),
    (16.7, 74.8, 95.0, 114.1, 123.7, 128.8, 129.9, 126.1, 119.6, 108.9, 98.8,
     87.9, 75.4, 63.9, 52.7, 41.0, 29.8, 19.0, 8.1, -1.8),
)

#: **Kiemelések / Árnyékok (#551).** A mérés megcáfolta a nevüket: egyik sem
#: csúcsfény-mentés vagy árnyék-emelés, hanem a FEHÉR- illetve FEKETEPONT
#: mozgatása — a paraméter azt mondja meg, a skála hány százalékával. A
#: mért meredekség 0,48-as állásnál 1,9235 (kiemelések) és 1,9244
#: (árnyékok); a képlet 1/(1−0,48) = 1,9231-et ad. A `filterdesc.xml` ezzel
#: egybehangzóan `[0..0.48]` tartományt ad meg mindkét paraméterre —
#: ezért a csúszkák felső határa is 0,48, nem 1,0.
#:
#:     Kiemelések(h): ki = clip( be / (1 − h) )
#:     Árnyékok(s):   ki = clip( (be − 255·s) / (1 − s) )
FINETUNE_LEVEL_PARAM_MAX = 0.48

#: **Színhőmérséklet (#551).** Csatornánkénti, KONSTANS szorzás (nem
#: eltolás): a mérésen a világosság-függő változat sem javított rajta
#: (5,00 vs 5,09 a leghidegebb állásban). A hideg irány jóval erősebb, mint
#: a meleg — épp ezt hibázta el a korábbi közelítés (hideg 20,94 / meleg
#: 4,43). A szorzókat a nem túlvezérelt pixelekre illesztettük.
_TEMPERATURE_KNOTS = (-1.0, -0.8, -0.5, 0.0, 0.5, 0.8, 1.0)
_TEMPERATURE_GAINS = (
    (0.6580, 1.1102, 1.8713),
    (0.7843, 1.0574, 1.4740),
    (0.8956, 1.0225, 1.1739),
    (1.0000, 1.0000, 1.0000),
    (1.0298, 1.0010, 0.8929),
    (1.0455, 0.9966, 0.8550),
    (1.0546, 0.9974, 0.8430),
)

# Semleges-szín pipetta: csillapított fehéregyensúly (mérve: a korrekció a
# teljes szürkevilág-korrekció ~50–75%-a).
_NEUTRAL_DAMPING = 0.6

_ARGB_PATTERN = re.compile(r"^[0-9a-fA-F]{8}$")


def _clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def _fill_delta_curve(strength: float) -> np.ndarray:
    """A `d(világosság)` görbe (256 elem) tetszőleges s∈[0..1] erősségre."""
    clamped = _clamp(strength, 0.0, 1.0)
    anchors = np.asarray(_FILL_LUMA_ANCHORS, dtype=np.float32)
    levels = np.arange(256, dtype=np.float32)
    # strict=False: szándékosan szomszédos-pár (pairwise) iteráció — az
    # eltolt lista eggyel rövidebb, ez a felépítés lényege, nem hiba.
    for index, (low_s, high_s) in enumerate(
        zip(_FILL_STRENGTHS, _FILL_STRENGTHS[1:], strict=False)
    ):
        if low_s <= clamped <= high_s:
            weight = (clamped - low_s) / (high_s - low_s)
            low = np.asarray(_FILL_DELTAS[index], dtype=np.float32)
            high = np.asarray(_FILL_DELTAS[index + 1], dtype=np.float32)
            return np.interp(levels, anchors, low + (high - low) * weight)
    return np.interp(levels, anchors, np.asarray(_FILL_DELTAS[-1], dtype=np.float32))


def apply_fill(image: np.ndarray, strength: float) -> np.ndarray:
    """Derítőfény (#551): világosság-vezérelt, csatorna-független hozzáadás.

    A pixel világossága (a három csatorna számtani átlaga) választja ki a
    hozzáadandó értéket a mért `d(világosság)` görbéből; ugyanaz az érték
    kerül mindhárom csatornára. Ez NEM csatornánkénti tónusgörbe — ld. a
    `_FILL_LUMA_ANCHORS` melletti indoklást.
    """
    validate_image(image)
    if _clamp(strength, 0.0, 1.0) == 0.0:
        return image.copy()
    values = image.astype(np.float32)
    luma = np.clip(values.mean(axis=-1), 0.0, 255.0)
    delta = _fill_delta_curve(strength)[np.round(luma).astype(np.int32)]
    return np.clip(values + delta[..., None], 0.0, 255.0).astype(np.uint8)


def apply_highlights(image: np.ndarray, strength: float) -> np.ndarray:
    """Kiemelések (#551): a FEHÉRPONT lehúzása — `ki = clip(be / (1 − h))`.

    A `h` a `filterdesc.xml` szerinti `[0..0.48]` nyers paraméter (a csúszka
    felső állása 0,48), nem [0..1]-es hányad.
    """
    validate_image(image)
    clamped = _clamp(strength, 0.0, FINETUNE_LEVEL_PARAM_MAX)
    if clamped == 0.0:
        return image.copy()
    # pontonkénti lineáris művelet → 256 elemű LUT (#140): képméret-független
    return apply_lut(image, lut_ramp() / (1.0 - clamped))


def apply_shadows(image: np.ndarray, strength: float) -> np.ndarray:
    """Árnyékok (#551): a FEKETEPONT felhúzása —
    `ki = clip((be − 255·s) / (1 − s))`, `s ∈ [0..0.48]`."""
    validate_image(image)
    clamped = _clamp(strength, 0.0, FINETUNE_LEVEL_PARAM_MAX)
    if clamped == 0.0:
        return image.copy()
    # pontonkénti lineáris művelet → 256 elemű LUT (#140): képméret-független
    return apply_lut(image, (lut_ramp() - 255.0 * clamped) / (1.0 - clamped))


def apply_color_temperature(image: np.ndarray, temperature: float) -> np.ndarray:
    """Színhőmérséklet (#551): csatornánkénti, mért KONSTANS szorzás.

    A szorzókat a mért állások között lineárisan interpoláljuk; 0 =
    változatlan. A hűtés lényegesen erősebb, mint a melegítés (ld. a
    `_TEMPERATURE_GAINS` táblát).
    """
    validate_image(image)
    clamped = _clamp(temperature, -1.0, 1.0)
    if clamped == 0.0:
        return image.copy()
    gains = [
        float(np.interp(clamped, _TEMPERATURE_KNOTS, [g[ch] for g in _TEMPERATURE_GAINS]))
        for ch in range(3)
    ]
    # csatornánkénti szorzás → csatornánkénti LUT (#140): képméret-független
    ramp = lut_ramp()
    return apply_channel_luts(image, (ramp * gains[0], ramp * gains[1], ramp * gains[2]))


def parse_neutral_argb(value: str) -> tuple[int, int, int] | None:
    """A finetune2 p4 (AARRGGBB hex) értelmezése.

    Nulla alfa = nincs kijelölt semleges szín → None; egyébként (R, G, B).
    """
    text = value.strip()
    if not _ARGB_PATTERN.match(text):
        raise ValueError(f"Érvénytelen AARRGGBB színérték: {value!r}")
    if int(text[0:2], 16) == 0:
        return None
    return (int(text[2:4], 16), int(text[4:6], 16), int(text[6:8], 16))


def apply_neutral_pipette(
    image: np.ndarray, neutral: tuple[int, int, int]
) -> np.ndarray:
    """Fehéregyensúly a kijelölt semlegesnek szánt szín alapján, csillapítva.

    A csatorna-erősítések a színt a saját szürkeátlaga felé húznák; a mért
    viselkedés szerint csak a korrekció egy része érvényesül
    (`_NEUTRAL_DAMPING`).
    """
    validate_image(image)
    red, green, blue = neutral
    gray = (red + green + blue) / 3.0
    if gray <= 0.0:
        return image.copy()
    # csatornánkénti gain → csatornánkénti LUT (#140): képméret-független
    ramp = lut_ramp()
    luts = []
    for value in (red, green, blue):
        if value <= 0:
            luts.append(ramp)
            continue
        gain = 1.0 + _NEUTRAL_DAMPING * (gray / value - 1.0)
        luts.append(ramp * gain)
    return apply_channel_luts(image, (luts[0], luts[1], luts[2]))


def apply_finetune2(
    image: np.ndarray,
    *,
    fill: float,
    highlights: float,
    shadows: float,
    neutral: tuple[int, int, int] | None,
    temperature: float,
) -> np.ndarray:
    """A `finetune2=1,p1,p2,p3,p4,p5` kompozit alkalmazása.

    p1=fill (a mért LUT azonos az önálló fill szűrőével), p2=highlights,
    p3=shadows, p4=semleges-szín pipetta, p5=színhőmérséklet. Az alkalmazási
    sorrend dokumentált feltevés (tónus előbb, szín utána).
    """
    validate_image(image)
    result = apply_fill(image, fill)
    result = apply_highlights(result, highlights)
    result = apply_shadows(result, shadows)
    if neutral is not None:
        result = apply_neutral_pipette(result, neutral)
    return apply_color_temperature(result, temperature)
