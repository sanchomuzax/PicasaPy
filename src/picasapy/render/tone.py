"""Tónus-műveletek: fill light, highlights/shadows, színhőmérséklet,
semleges-szín pipetta és a `finetune2` kompozit.

**#551/#575: a Finomhangolás-csúszkák modelljei.** A Kiemelések, az
Árnyékok és a Színhőmérséklet a `sanchomuzax/picasapy-agent` privát repó
mérőkészleteiből (`referencia/deritofeny/`, `referencia/szinhomerseklet/`,
`referencia/finomhangolas/`: ugyanaz a fotó, csúszkánként több állásban, a
valódi Picasa 3.9 kimenetével). A **Derítőfény** ennél erősebb forrásból: a
natív `0x0090ac20` munkafüggvény DEKOMPILÁLT kódjából (#575) — nem
illesztés, hanem a Picasa saját algoritmusa.

A korábbi közelítések átlagos csatorna-eltérése a Picasa kimenetétől 18–23
volt; a mérésből kapott modelleké 0,8–5,9, a Derítőfény natív modelljéé
0,8–4,5 (a JPEG-zaj szintje ~1). A pipetta modellje egyelőre változatlan
közelítés.
"""

from __future__ import annotations

import re

import numpy as np

from picasapy.render.curves import (
    apply_channel_luts,
    lut_ramp,
    validate_image,
)
from picasapy.render.native_tone import apply_native_lut16, native_level_lut

#: **Derítőfény (#575/#551).** A modell a NATÍV KÓDBÓL való, nem mérésből
#: illesztve: a `0x0090ac20` munkafüggvény dekompilálva (ld.
#: `docs/specs/picasa-native-filter-workers.md`). Ugyanezt a magot hívja a
#: `fill`, a `backlight`, az `autobacklight`, a `triple*` és a
#: `finetune`/`finetune2` — nyolc szűrő, EGY implementáció.
#:
#: Két hatás van egymáson, ezért nem lehetett egyetlen görbével leírni:
#:
#:     g      = 1 / ((1 − fill)·0,7 + 0,3)
#:     LUT[x] = round(255 · min(((x·g)/255)^(1/(g·0,7+0,3)), 256))
#:     luma4  = (B + 2·G + R) >> 2            # a súlyozott világosság
#:     w      = 0xff00 − luma4·256            # alpha = 1,0 a hívóban
#:     ki     = clip(be + ((LUT[be] − be)·w >> 16))
#:
#: A `w` súly a képpont világosságával FORDÍTOTTAN arányos: sötétben teljes
#: a hatás, világosban semmi. `fill = 0`-nál `g = 1`, a kitevő is 1, a LUT
#: azonosság — a művelet nem csinál semmit, ahogy kell.
#:
#: A mérőkészleten (`referencia/deritofeny/`, hat csúszkaállás) az átlagos
#: csatorna-eltérés a Picasa kimenetétől 0,8–4,5, a JPEG saját zaja ~1,0 —
#: vagyis ez a PONTOS algoritmus, nem közelítés (a korábbi, mérésre
#: illesztett világosság-görbéé 0,97–5,89 volt).
_FILL_GAMMA_BASE = 0.7
_FILL_GAMMA_OFFSET = 0.3
_FILL_WEIGHT_FULL = 0xFF00

#: **Kiemelések / Árnyékok (#551, #879).** A mérés megcáfolta a nevüket:
#: egyik sem csúcsfény-mentés vagy árnyék-emelés, hanem a FEHÉR- illetve
#: FEKETEPONT mozgatása — a paraméter azt mondja meg, a skála hány
#: százalékával. A mért meredekség 0,48-as állásnál 1,9235 (kiemelések) és
#: 1,9244 (árnyékok); a képlet 1/(1−0,48) = 1,9231-et ad. A `filterdesc.xml`
#: ezzel egybehangzóan `[0..0.48]` tartományt ad meg mindkét paraméterre —
#: ezért a csúszkák felső határa is 0,48, nem 1,0. (A 859 valódi
#: `.picasa.ini`-ből álló korpusz mind az 566 Finomhangolás-láncában a két
#: érték a tartományon belül van, tehát a vágás éles használatban no-op.)
#:
#: **A KETTŐ EGYETLEN LEKÉPEZÉS (#879).** A natív callback (`0x008f7ee0`) nem
#: futtatja őket egymás után: egy hívással (`0x0090c430`) EGY 256×uint16
#: táblát építtet (`0x0090c1e0`), és azt EGY menetben alkalmazza:
#:
#:     a0 = p3                    ; Árnyékok   → feketepont
#:     a1 = max(1 − p2, 0,001)    ; Kiemelések → fehérpont
#:     a2 = 1,0                   ; a hívó `fld1`-je → a görbe lineáris
#:
#:     ki = clip( (be − 255·a0) / (a1 − a0) )
#:
#: A korábbi, két külön menetes számolásunk `((be/(1−h)) − 255·s)/(1−s)`-t
#: adott: EGY vezérlővel a kettő azonos, kettővel viszont a maximumon a
#: meredekség 3,70 vs 25,0, és a két görbe **217 szinten** eltér. Nem a
#: közbenső 8 bites vágás okozta — vágás nélkül is ugyanennyi.
FINETUNE_LEVEL_PARAM_MAX = 0.48

#: A natív nullaosztás-védés a fehérponton (`h = max(1 − p2, 0,001)`,
#: `0x008f7f05`; a konstans a `0xcf3da0`/`0xc7999c`). A 0,48-as vágás miatt
#: a fehérpont sosem megy 0,52 alá, tehát a padló ma nem aktiválódik — a
#: natív alakhoz való hűség kedvéért van itt.
_MIN_WHITE_POINT = 0.001

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

#: **Semleges-szín pipetta / szín-varázspálca (#551).** A `finetune2` p4
#: mezője a viszonyítási szín, `AARRGGBB` hexában — és a Picasa maga
#: NORMALIZÁLJA: a középső bájt MINDIG 0x80 = 128, vagyis a ZÖLD a
#: viszonyítási alap. A csatorna-erősítés ebből:
#:
#:     k_c = p4_zöld / p4_c        (a zöldé így mindig 1,0)
#:
#: Hat próbaképen ellenőrizve (`referencia/szinpalca-proba2/`, a p4-eket
#: maga a Picasa írta a `.picasa.ini`-be): a jósolt és a mért csatorna-
#: szorzók eltérése végig ~3 %. A korábbi, csillapított szürkevilág-
#: közelítés ennél lényegesen messzebb járt (pl. 1,09 a mért 1,16 helyett).
#:
#: A zöldre normálás egyben azt is adja, hogy egy tényleg semleges (R=G=B)
#: viszonyítási szín azonosság — ahogy kell.
#:
#: Ugyanez a mag (`0x0090eda0`) szolgálja ki a kézi pipettát és az
#: automatikus szín-varázspálcát is: egy implementáció, két belépési pont.
#: Azt, hogy az AUTOMATIKA milyen szabállyal választja a színt, még nem
#: tudjuk (szürke-képpont becslés — ld. a #551 jegyet).

_ARGB_PATTERN = re.compile(r"^[0-9a-fA-F]{8}$")


def _clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def fill_lut(strength: float) -> np.ndarray:
    """A Derítőfény 256 elemű gamma-LUT-ja (#575) — a natív kód szerint.

    Önállóan is használható (teszt, dokumentáció); a képpontonkénti
    árnyék-súlyozott keverést az `apply_fill` végzi rá.
    """
    clamped = _clamp(strength, 0.0, 1.0)
    gamma = 1.0 / ((1.0 - clamped) * _FILL_GAMMA_BASE + _FILL_GAMMA_OFFSET)
    exponent = 1.0 / (gamma * _FILL_GAMMA_BASE + _FILL_GAMMA_OFFSET)
    levels = np.arange(256, dtype=np.float64)
    values = np.power(levels * gamma / 255.0, exponent)
    # a natív kód 256,0-nál vág (a 255-ös kimenet fölött nincs értelme)
    return np.rint(255.0 * np.minimum(values, 256.0)).astype(np.int32)


def apply_fill(image: np.ndarray, strength: float) -> np.ndarray:
    """Derítőfény (#575): gamma-LUT + ÁRNYÉK-SÚLYOZOTT keverés.

    A natív `0x0090ac20` munkafüggvény pontos mása: a LUT-ot nem közvetlenül
    alkalmazza, hanem a képpont világosságával fordítottan arányos súllyal
    keveri az eredetihez — sötétben teljes hatás, világosban semmi.

    A `luma4` súlyozása szimmetrikus az R-re és a B-re, ezért a csatorna-
    sorrend (RGB/BGR) nem számít.
    """
    validate_image(image)
    if _clamp(strength, 0.0, 1.0) == 0.0:
        return image.copy()
    values = image.astype(np.int32)
    outer = values[..., 0] + values[..., 2]
    luma4 = (outer + 2 * values[..., 1]) >> 2
    weight = (_FILL_WEIGHT_FULL - luma4 * 256)[..., None]
    mapped = fill_lut(strength)[values]
    return np.clip(
        values + (((mapped - values) * weight) >> 16), 0, 255
    ).astype(np.uint8)


def finetune_level_lut(highlights: float, shadows: float) -> np.ndarray:
    """A Kiemelések + Árnyékok KÖZÖS 16 bites LUT-ja (#879).

    A `0x0090c1e0` natív szinthúzó-táblát építi fel a `finetune`/`finetune2`
    hívási alakjával: feketepont = Árnyékok, fehérpont = 1 − Kiemelések,
    gamma = 1,0. Ugyanez a mag szolgálja ki a `triple2`/`triple3` szűrőt is
    (`chain_native_handlers`), csak ott már eleve egy táblával számoltunk.

    Mindkét paraméter a `filterdesc.xml` `[0..0.48]` tartományára vágódik.
    """
    black = _clamp(shadows, 0.0, FINETUNE_LEVEL_PARAM_MAX)
    white = 1.0 - _clamp(highlights, 0.0, FINETUNE_LEVEL_PARAM_MAX)
    return native_level_lut(black=black, white=max(white, _MIN_WHITE_POINT))


def _apply_levels(image: np.ndarray, highlights: float, shadows: float) -> np.ndarray:
    """A közös szinthúzás — semleges állásban a natív burkoló is kihagyja."""
    if (
        _clamp(highlights, 0.0, FINETUNE_LEVEL_PARAM_MAX) == 0.0
        and _clamp(shadows, 0.0, FINETUNE_LEVEL_PARAM_MAX) == 0.0
    ):
        return image.copy()
    return apply_native_lut16(image, finetune_level_lut(highlights, shadows))


def apply_highlights(image: np.ndarray, strength: float) -> np.ndarray:
    """Kiemelések (#551): a FEHÉRPONT lehúzása — `ki = clip(be / (1 − h))`.

    A `h` a `filterdesc.xml` szerinti `[0..0.48]` nyers paraméter (a csúszka
    felső állása 0,48), nem [0..1]-es hányad. A közös LUT elfajult esete
    (Árnyékok = 0), hogy a két csúszka egyetlen implementációt használjon.
    """
    validate_image(image)
    return _apply_levels(image, strength, 0.0)


def apply_shadows(image: np.ndarray, strength: float) -> np.ndarray:
    """Árnyékok (#551): a FEKETEPONT felhúzása —
    `ki = clip((be − 255·s) / (1 − s))`, `s ∈ [0..0.48]`.

    A közös LUT elfajult esete (Kiemelések = 0).
    """
    validate_image(image)
    return _apply_levels(image, 0.0, strength)


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


#: **A szín-varázspálca színválasztása (#551).** A pálca nem külön szűrő:
#: ugyanabba a p4 mezőbe ír, mint a kézi pipetta — csak a színt a program
#: találja ki. A szabályt a tulajdonos 11 mérőképéből illesztettük
#: (`referencia/szinpalca/` és `szinpalca-proba2/`, ahol a választott p4-et
#: MAGA a Picasa írta a `.picasa.ini`-be):
#:
#:     a KEVÉSSÉ TELÍTETT képpontok átlaga, a zöldre normálva
#:
#: A telítettség a HSV-definíció (`(max − min) / max`), a küszöb 0,30 — ez
#: adta a legkisebb hibát (átlag 2,9, maximum 7,5 egység a 0..255 skálán),
#: és 1,0-hoz illeszkedő skálázással, tehát a nyers átlag SEMMILYEN
#: erősítést nem igényel. A mérés iránya is stimmel: a csúcsfények alig
#: számítanak, a semleges-közeli képpontok a döntőek.
_NEUTRAL_ESTIMATE_SATURATION = 0.30
#: A p4 zöld bájtja a Picasánál MINDIG 0x80 — a normálás alapja.
NEUTRAL_GREEN_ANCHOR = 128


def estimate_neutral_color(image: np.ndarray) -> tuple[int, int, int]:
    """A szín-varázspálca által választott viszonyítási szín (#551).

    A kevéssé telített („szürke-közeli") képpontok átlaga, a zöldre
    normálva — ugyanabban az alakban, ahogy a Picasa a `finetune2` p4
    mezőjébe írja (a zöld mindig 128).

    Ha nincs elég szürke-közeli képpont, a TELJES kép átlagára esünk vissza;
    ha a zöld átlaga nulla (fekete kép), a semleges színt adjuk vissza — a
    művelet ilyenkor azonosság.
    """
    validate_image(image)
    values = image.astype(np.float32)
    high = values.max(axis=-1)
    low = values.min(axis=-1)
    saturation = np.where(high > 0.0, (high - low) / np.maximum(high, 1.0), 0.0)
    mask = saturation < _NEUTRAL_ESTIMATE_SATURATION
    selected = values[mask] if mask.any() else values.reshape(-1, 3)
    means = selected.mean(axis=0)
    if means[1] <= 0.0:
        return (NEUTRAL_GREEN_ANCHOR, NEUTRAL_GREEN_ANCHOR, NEUTRAL_GREEN_ANCHOR)
    scale = NEUTRAL_GREEN_ANCHOR / float(means[1])
    return (
        int(np.clip(round(float(means[0]) * scale), 0, 255)),
        NEUTRAL_GREEN_ANCHOR,
        int(np.clip(round(float(means[2]) * scale), 0, 255)),
    )


def apply_neutral_pipette(
    image: np.ndarray, neutral: tuple[int, int, int]
) -> np.ndarray:
    """Fehéregyensúly a semlegesnek jelölt szín alapján (#551).

    A csatorna-erősítés a ZÖLDHÖZ viszonyít (`k_c = p4_zöld / p4_c`), mert a
    Picasa a p4-et így normalizálja: a középső bájt mindig 0x80 = 128.
    Semleges (R=G=B) viszonyítási színnél ez azonosság.
    """
    validate_image(image)
    red, green, blue = neutral
    if green <= 0:
        return image.copy()
    # csatornánkénti gain → csatornánkénti LUT (#140): képméret-független
    ramp = lut_ramp()
    luts = [
        ramp if value <= 0 else ramp * (float(green) / float(value))
        for value in (red, green, blue)
    ]
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
    p3=shadows, p4=semleges-szín pipetta, p5=színhőmérséklet.

    A lépéssor a natív callback (`0x008f7ee0`) sorrendje: Derítőfény, majd
    a Kiemelések + Árnyékok EGYETLEN közös LUT-ban (#879), végül a szín-ág.
    Mindhárom lépés kimarad, ha a hozzá tartozó paraméter semleges.
    """
    validate_image(image)
    result = apply_fill(image, fill)
    result = _apply_levels(result, highlights, shadows)
    if neutral is not None:
        result = apply_neutral_pipette(result, neutral)
    return apply_color_temperature(result, temperature)
