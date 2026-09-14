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
from picasapy.render.autocolor_matrix import (
    apply_autocolor_matrix,
    autocolor_matrix_16_16,
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

#: **A feketetest-tábla (#956).** A `Picasa3.exe` `0x00c7cf98` címén álló
#: tömb, csomagolt `0x00RRGGBB` dwordökként; `Kelvin = 1000 + 100·i`, tehát
#: az `i`-edik bejegyzés a `1000 + 100·i` kelvines feketetest színe.
#:
#: **Csak a 18…92 tartomány van itt**, mert a csúszka `[−1, 1]` tartománya
#: pontosan ezt címzi (`i = round(temp·37 + 55)`), azaz **2800 K … 10200 K**.
#: ⚠️ A tömb a binárisban ennél hosszabb (a 391. bejegyzésig tart a minta) —
#: a jegy „130 elemű tábla" megfogalmazása a DOKUMENTÁLT szeletre vonatkozik,
#: nem a tömb hosszára. A többi bejegyzést a hőmérséklet-csúszka nem éri el,
#: ezért nem is másoljuk ide.
#:
#: A számok a binárisból vannak KIOLVASVA, nem Planck-sugárzásból számolva:
#: egy korábbi kör számolt táblával mért, és az mást adott.
FEKETETEST_TABLA: dict[int, tuple[int, int, int]] = {
    18: (255, 173, 94),
    19: (255, 177, 101),
    20: (255, 180, 107),
    21: (255, 184, 114),
    22: (255, 187, 120),
    23: (255, 190, 126),
    24: (255, 193, 132),
    25: (255, 196, 137),
    26: (255, 199, 143),
    27: (255, 201, 148),
    28: (255, 204, 153),
    29: (255, 206, 159),
    30: (255, 209, 163),
    31: (255, 211, 168),
    32: (255, 213, 173),
    33: (255, 215, 177),
    34: (255, 217, 182),
    35: (255, 219, 186),
    36: (255, 221, 190),
    37: (255, 223, 194),
    38: (255, 225, 198),
    39: (255, 227, 202),
    40: (255, 228, 206),
    41: (255, 230, 210),
    42: (255, 232, 213),
    43: (255, 233, 217),
    44: (255, 235, 220),
    45: (255, 236, 224),
    46: (255, 238, 227),
    47: (255, 239, 230),
    48: (255, 240, 233),
    49: (255, 242, 236),
    50: (255, 243, 239),
    51: (255, 244, 242),
    52: (255, 245, 245),
    53: (255, 246, 248),
    54: (255, 248, 251),
    55: (255, 249, 253),
    56: (254, 249, 255),
    57: (252, 247, 255),
    58: (249, 246, 255),
    59: (247, 245, 255),
    60: (245, 243, 255),
    61: (243, 242, 255),
    62: (240, 241, 255),
    63: (239, 240, 255),
    64: (237, 239, 255),
    65: (235, 238, 255),
    66: (233, 237, 255),
    67: (231, 236, 255),
    68: (230, 235, 255),
    69: (228, 234, 255),
    70: (227, 233, 255),
    71: (225, 232, 255),
    72: (224, 231, 255),
    73: (222, 230, 255),
    74: (221, 230, 255),
    75: (220, 229, 255),
    76: (218, 228, 255),
    77: (217, 227, 255),
    78: (216, 227, 255),
    79: (215, 226, 255),
    80: (214, 225, 255),
    81: (212, 225, 255),
    82: (211, 224, 255),
    83: (210, 223, 255),
    84: (209, 223, 255),
    85: (208, 222, 255),
    86: (207, 221, 255),
    87: (207, 221, 255),
    88: (206, 220, 255),
    89: (205, 220, 255),
    90: (204, 219, 255),
    91: (203, 219, 255),
    92: (202, 218, 255),
}

#: **A GPU-ELŐNÉZET színhőmérséklet-KÖZELÍTÉSE (#551/#956).** Csatornánkénti,
#: konstans szorzás, a mért állások között lineárisan interpolálva.
#:
#: ⚠️ **Ez KÖZELÍTÉS, nem a pontos út.** A pontos modell a natív
#: feketetest-tábla + autocolor-mátrix (`apply_color_temperature`, #956); az
#: a képpontonkénti méréssel mind a hat állásban jobb, a hideg végen
#: négyszeresen. Ez a tábla azért MARAD MEG, mert a GPU-előnézet shaderje
#: egyetlen uniformot kap, és egy 3×3-as mátrix oda nem fér be — a szorzók a
#: gyors előnézethez elég közel járnak.
#:
#: Amit szerkezetileg NEM tud: kereszt-tagot előállítani. A natív művelet
#: 3×3-as mátrix (`0x0090e9fd` → az autocolor alkalmazója), tehát a
#: csatornánkénti alak a hideg végen 11,8 %-nyi átlón kívüli tagot hagy ki.
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


def feketetest_index(temperature: float) -> int:
    """A csúszka állásából a feketetest-tábla indexe (#956).

    A natív törzs (`0x0090e9d0`, 54 bájt):

        fmul [0xcf47e0]   ; × 37,0
        fadd [0xcf4610]   ; + 55,0
        fistp [esp+0xc]   ; i

    ⛔ **Az `fistp` a LEGKÖZELEBBI egészre kerekít, nem csonkol.** A törzsben
    nincs vezérlőszó-állítás (`fnstcw` / `or 0xc00`), tehát az x87
    alapértelmezett módja fut: legközelebbi egész, döntetlennél a páros. A
    jegy és a spec `(int)` alakja ezen a ponton téves volt — a spec SAJÁT
    mért index-táblája is a kerekítést igazolja (`+0,5` → 74, nem 73;
    `+0,8` → 85, nem 84).

    A csúszka `[−1, 1]` tartománya a 18…92 indexeket adja; a tartományon
    kívüli értéket a végpontra szorítjuk, ahogy a felület is teszi.
    """
    clamped = _clamp(float(temperature), -1.0, 1.0)
    # float32: a natív `fld dword` egyszeres pontosságban dolgozik
    nyers = np.float32(np.float32(clamped) * np.float32(37.0) + np.float32(55.0))
    # a `round` féltől-párosra kerekít — ugyanaz, mint az x87 alapmódja
    return int(round(float(nyers)))


def feketetest_szin(temperature: float) -> tuple[int, int, int]:
    """A csúszka állásához tartozó feketetest-szín (R, G, B) — #956."""
    return FEKETETEST_TABLA[feketetest_index(temperature)]


def apply_color_temperature(image: np.ndarray, temperature: float) -> np.ndarray:
    """Színhőmérséklet (#956): feketetest-tábla + autocolor MÁTRIX.

    A natív út: a csúszka állásából index lesz, az indexből egy
    feketetest-szín (`0x00c7cf98`), és a képet ezzel **semlegesíti** az
    `autocolor` 3×3-as mátrixa (`0x0090eda0`, #759).

    ⚠️ **A művelet MÁTRIX, nem csatornánkénti szorzás.** Ez a hívás
    szerkezetéből következik, nem statisztikai lelet: a kereszt-tag a hideg
    végen 11,8 %, a meleg végen 3,2 %. Egy csatornánkénti modell ezt
    **szerkezetileg** nem tudja előállítani — ezért volt érvénytelen az a
    korábbi mérés (#879), amivel a natív utat elvetettük: csatorna-LUT-okhoz
    hasonlított, amelyek maguk is vakok a mátrix átlón kívüli tagjaira.

    ⛔ **`temperature = 0` AZONOSSÁG — a HÍVÓ kapuzza, nem a tábla.** A jegy
    és a spec is azt írta, hogy a nulla állás sem azonosság, mert a tábla 55.
    bejegyzése (255, 249, 253) maga sem semleges. A bejegyzésről ez igaz —
    **de a stádium el sem indul nullánál.** A hívó (`0x008f7ee0`) a hívás
    előtt összehasonlít nullával, és egyezéskor elugrik a hőmérséklet-ág
    fölött:

        0x008f7fd7  fldz
        0x008f7fdd  fucom st(1)        ; temp ?= 0,0
        0x008f7fe3  test  ah, 0x44
        0x008f7fe6  jnp   0x8f8062     ; EGYENLŐSÉGKOR ide — a 0x90e9d0 kimarad
        …
        0x008f8010  call  0x90e9d0     ; csak a NEM nulla ágon

    A kapu nélkül minden semleges `finetune2`-es kép némán elszíneződne: a
    nulla állás mátrixa mérve `(128,128,128)` → `(126,129,126)`, ami sík
    szürke felületen látszik. A hívóhelyeket indextől FÜGGETLEN pásztázás
    adta (a `0x90e9d0`-nak kettő van: `0x8f8010`, `0x8f8051`; kontroll a
    `0x90eda0` kilenc hívója).

    A `_TEMPERATURE_GAINS` közelítés a GPU-előnézeté marad (ld. ott).
    """
    validate_image(image)
    clamped = _clamp(float(temperature), -1.0, 1.0)
    if clamped == 0.0:
        # a natív hívó kapuja (`0x008f7fe6 jnp`): nulla állásnál a
        # hőmérséklet-ág el sem indul
        return image.copy()
    piros, zold, kek = feketetest_szin(clamped)
    matrix = autocolor_matrix_16_16(piros, zold, kek)
    return apply_autocolor_matrix(image, matrix)


def apply_color_temperature_gpu_kozelites(
    image: np.ndarray, temperature: float
) -> np.ndarray:
    """A színhőmérséklet CSATORNÁNKÉNTI közelítése — csak a GPU-előnézetnek.

    ⚠️ **Ez nem a pontos modell.** A pontos út az
    `apply_color_temperature` (feketetest-tábla + 3×3-as autocolor-mátrix,
    #956); a MENTETT kép mindig azon készül.

    Miért van mégis szükség rá: a GPU-előnézet a teljes `finetune2` láncot
    **egyetlen 256×1 RGB LUT-textúrával** futtatja, ami csak akkor
    reprodukálja a CPU-utat, ha a lánc minden lépése csatornánként
    független. A mátrix keveri a csatornákat, tehát LUT-ba nem fér —
    kapcsoló nélkül a gyors előnézet elveszne. A közelítés hibája a rácson
    nem látszik, a mentés pedig pontos.

    A régi (a #551-ig egyetlen) modell: a `_TEMPERATURE_GAINS` szorzói a
    mért állások között lineárisan interpolálva.
    """
    validate_image(image)
    clamped = _clamp(float(temperature), -1.0, 1.0)
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
    szinhomerseklet_kozelitessel: bool = False,
) -> np.ndarray:
    """A `finetune2=1,p1,p2,p3,p4,p5` kompozit alkalmazása.

    p1=fill (a mért LUT azonos az önálló fill szűrőével), p2=highlights,
    p3=shadows, p4=semleges-szín pipetta, p5=színhőmérséklet.

    A lépéssor a natív callback (`0x008f7ee0`) sorrendje: Derítőfény, majd
    a Kiemelések + Árnyékok EGYETLEN közös LUT-ban (#879), végül a szín-ág.
    Mindhárom lépés kimarad, ha a hozzá tartozó paraméter semleges.

    `szinhomerseklet_kozelitessel`: **kizárólag a GPU-előnézet LUT-építője
    állítja** (#956). Ilyenkor a hőmérséklet a csatornánkénti közelítéssel
    megy, mert a pontos út 3×3-as mátrix, az pedig nem fér egy 256×1
    LUT-textúrába. A MENTETT kép mindig a pontos úton készül.
    """
    validate_image(image)
    result = apply_fill(image, fill)
    result = _apply_levels(result, highlights, shadows)
    if neutral is not None:
        result = apply_neutral_pipette(result, neutral)
    if szinhomerseklet_kozelitessel:
        return apply_color_temperature_gpu_kozelites(result, temperature)
    return apply_color_temperature(result, temperature)
