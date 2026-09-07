"""A `dir_tint` (Graduated Tint) — a natív modell, utasításszinten kiolvasva.

A régi közelítés (fix függőleges átmenet, lineáris keverés a szín felé)
helyett ez a modul a Picasa 3.9.141.259 tényleges számítását követi. A
lánc három natív függvényből áll:

* **`0x008f9880`** — a regisztráló callback: kiolvassa a puckot, a
  `Feather`-t (`[szűrő+0x28]`, **minimum 0,001**), a `Shade`-et
  (`[szűrő+0x2c]`), a színt (`[szűrő+0x50]`) és az irányt
  (`[szűrő+0xc4]`), majd hat argumentummal hívja a munkafüggvényt.
* **`0x0090f470`** — a munkafüggvény: szöget számol, `sin`/`cos`-ból
  16.16 fixpontos lépésvektort épít, feltölti a 384 bájtos térbeli
  rámpát és a 256 × `uint16` tónusgörbét, majd végigmegy a képpontokon.
* **`0x0090ecd0`** / **`0x0090ec40`** — a tónusgörbe-LUT és a mögötte
  álló reciprok torzítógörbe.

## Amit a mérés igazol

A Picasa-referencia (`PicasaPy meroszett`, `export-202608151229`) és a
mi kimenetünk átlagos csatornaeltérése a három beállításon
(#874, 2026-09-07):

| beállítás | régi közelítés | ez a modul | érintetlen kép |
|---|---:|---:|---:|
| alap (Feather 0,25 · Shade 0,25) | 22,285 | **0,624** | 6,635 |
| max (Feather 1,0 · Shade 1,0) | 124,171 | **0,470** | 61,591 |
| min (Feather 0 · Shade 0) | 0,615 | **0,615** | 0,615 |

A `min` beállítás mért 0,615-e a **JPEG-újrakódolás zaja** (ott a szűrő
igazoltan tétlen), tehát az `alap` és a `max` maradéka a zajszint ALATT
van — a modell képpont-hű.

## HELYESBÍTÉS a jegy törzséhez képest (#874)

A jegy leírása szerint `[szűrő+0xc4]` „az irány, FOKBAN", és a
`(puck − 0,5) × 30` a **középpont skálája**. A veremre pakolás
kiolvasása szerint **fordítva van**:

* `[szűrő+0xc4]` egy **egész negyedválasztó** — a munkafüggvény
  kizárólag `& 1`-gyel (`0x0090f503`) és `& 3`-mal (`0x0090f5d4`)
  használja, tehát 90°-os lépés, nem fok;
* a `(puck − 0,5) × 30` a **3. argumentum** (`0x008f9983` → `[esp+8]`),
  és épp ezt szorozza a munkafüggvény a `π/180`-nal
  (`0x0090f543`) — vagyis ez a **szög fokban**, ±15° tartományban;
* a **középpont** mindig a teljes puck: `(W·x, H·y)`, egészre csonkítva
  (`0x008f98a0`–`0x008f98ce`), nincs `× 30`-as skála.

A kép **EXIF-tájolása** (`[ebp+0x10]+0x1c`) csak akkor számít, ha az
irány **nem** `-1` (`0x008f9933  cmp eax, -1`). A `.picasa.ini`
`dir_tint=` alakja irányt nem hordoz, tehát az `-1 → 0` ágon megyünk, és
a tájolás kimarad a számításból.
"""

from __future__ import annotations

import math

import numpy as np

from picasapy.render.curves import validate_image

#: A `Feather` (0. csúszka) alsó korlátja a natív callbackben
#: (`0x008f9916` küszöb `0xcf3db0` = 0,001, pótérték `0xc7999c` = 0,001).
DIR_TINT_FEATHER_FLOOR = 0.001

#: A `Shade`-ből képzett görbeparaméter vágása (`0x0090f484`–`0x0090f4cd`
#: és `0x0090ecd0`): `q = clamp(1 − Shade, 0,01, 99,9)`, majd `p = 1/q`.
_CURVE_PARAM_MIN = 0.01
_CURVE_PARAM_MAX = 99.9

#: A tónusgörbe-LUT bejegyzésszáma és skálája (`0x0090ecd0`).
_TONE_LUT_SIZE = 256
_TONE_LUT_SCALE = 65535.0
#: A LUT bemenetének normálása: `i × 1/255` (`0xcf4138`).
_TONE_LUT_STEP = 0.003921568859368563

#: A térbeli rámpa hossza és lépésköze (`0x0090f724  cmp ecx, 0x180`,
#: `0xcf3d40` = 1/256), valamint a bájtra váltó szorzó (`0xcf48c8`).
_RAMP_SIZE = 384
_RAMP_STEP = 1.0 / 256.0
_RAMP_SCALE = 255.99989318847656

#: A natív fok→radián szorzó (`0xcf48d0`) és a puck-szög terjedelme
#: (`0xcf3ed8` = 30,0): a szög `(puck − 0,5) × 30`, azaz ±15°.
_DEG_TO_RAD = 0.017453277777777776
_ANGLE_SPAN_DEG = 30.0

#: A lépésvektor 16.16 fixpontos skálája (`0xcf3cb0`).
_FIXED_ONE = 65536.0

#: A natív a tiszta fehérnél (`cmp dword ptr [esp+0x3e8], 0xffffff`,
#: `0x0090f525`) KIHAGYJA a szorzást — enélkül a 255-ös csatorna 254 lenne.
_NEUTRAL_COLOR = (0xFF, 0xFF, 0xFF)

#: A szorzó színezés osztója (`shr ebx, 8`, `0x0090f81b`).
_TINT_SHIFT = 8


def dir_tint_tone_curve(
    values: np.ndarray, param: float
) -> np.ndarray:
    """A `0x0090ec40` reciprok torzítógörbéje (`float32`-ben).

    `param == 1,0`-nál **azonosság** — a natív ezt külön ággal kezeli
    (`0x0090ec47  fucom st(1)`), mert egyébként nullával osztana.
    Egyébként `A = sqrt(1/p)`, `B = sqrt(p)` és

        y = (1 / ((1 − x)·(B − A) + A) − A) / (B − A)

    Mivel `A·B = 1` azonosan, `y(0) = 0` és `y(1) = 1` pontosan teljesül.
    """
    x = np.asarray(values, dtype=np.float32)
    if param == 1.0:
        return x
    lower = np.float32(math.sqrt(1.0 / param))
    upper = np.float32(math.sqrt(param))
    span = np.float32(upper - lower)
    denominator = (np.float32(1.0) - x) * span + lower
    return ((np.float32(1.0) / denominator) - lower) / span


def dir_tint_tone_lut(param: float) -> np.ndarray:
    """A 256 bejegyzésű, `uint16` tónusgörbe-LUT (`0x0090ecd0`).

    A paramétert a natív is újravágja `[0,01 ; 99,9]`-re, a görbe
    kimenetét `65535`-tel szorozza, **nulla felé csonkítja**
    (`or eax, 0xc00`) és `0…65535`-re vágja. A képpont-ciklus a bejegyzés
    **felső bájtját** olvassa, ezért `param = 1`-nél `LUT[i] >> 8 == i`.
    """
    clamped = min(max(float(param), _CURVE_PARAM_MIN), _CURVE_PARAM_MAX)
    inputs = (
        np.arange(_TONE_LUT_SIZE, dtype=np.float64) * _TONE_LUT_STEP
    ).astype(np.float32)
    scaled = dir_tint_tone_curve(inputs, clamped).astype(np.float64)
    scaled *= _TONE_LUT_SCALE
    return np.clip(np.trunc(scaled), 0.0, _TONE_LUT_SCALE).astype(np.uint16)


def _ramp_shape(positions: np.ndarray) -> np.ndarray:
    """A rámpa mögötti szakaszonkénti köbös S-görbe (`0x0090f64b`–`0x0090f705`).

    Négy ág, a natív konstansaival (`1,125` · `0,25` · `3,0` · `1/6` és a
    `0,5625` / `0,5` / `0,4375` eltolások). A támasza `[−1,5 ; 1,5]`, a
    végein `1`, illetve `0`, a közepén `0,5`; a `t = ±0,5` határokon
    folytonos, és páratlan szimmetriájú a `(0 ; 0,5)` pontra.
    """
    t = np.asarray(positions, dtype=np.float32)
    square = t * t
    cube = square * t
    upper = np.float32(0.5625) - np.float32(1.125) * t + np.float32(0.75) * square
    upper = upper - cube / np.float32(6.0)
    middle = np.float32(0.5) - np.float32(0.75) * t + cube / np.float32(3.0)
    lower = np.float32(0.4375) - np.float32(1.125) * t - np.float32(0.75) * square
    lower = lower - cube / np.float32(6.0)
    result = np.where(t > np.float32(0.5), upper, np.where(t > np.float32(-0.5), middle, lower))
    result = np.where(t > np.float32(1.5), np.float32(0.0), result)
    return np.where(t < np.float32(-1.5), np.float32(1.0), result).astype(np.float32)


def dir_tint_ramp_table() -> np.ndarray:
    """A 384 bájtos térbeli rámpa (`0x0090f62b`–`0x0090f752`).

    A `t = i/256` helyeken `trunc((1 − 2·S(t)) × 255,99989)`; a tábla a
    `0`-tól `255`-ig monoton nő, és a rajta kívüli tartományt a
    képpont-ciklus `±255`-re vágja (`0x0090f7a6`, `0x0090f7b5`).
    """
    positions = (
        np.arange(_RAMP_SIZE, dtype=np.float64) * _RAMP_STEP
    ).astype(np.float32)
    signed = np.float32(1.0) - np.float32(2.0) * _ramp_shape(positions)
    return np.trunc(signed.astype(np.float64) * _RAMP_SCALE).astype(np.int32)


def _step_vector(
    x: float, y: float, feather: float, height: int, width: int, direction: int
) -> tuple[int, int]:
    """A 16.16 fixpontos lépésvektor (`0x0090f4fc`–`0x0090f5e5`).

    A negyed paritása dönti el, MELYIK puck-koordináta adja a szöget és
    melyik kép-oldal a normálást: páros negyednél a puck `x` és a
    **magasság**, páratlannál a puck `y` és a **szélesség**. A páratlan
    negyed felcseréli a két komponenst, a 2-es és a 3-as negyed pedig
    előjelet vált — együtt ez a négy 90°-os alapirány.
    """
    # a natív a -1-et NULLÁRA cseréli, még a maszkolás előtt
    # (`0x008f9933  cmp eax, -1`) — Pythonban a -1 & 3 = 3 volna
    quadrant = 0 if direction == -1 else direction & 3
    sideways = bool(quadrant & 1)
    extent = width if sideways else height
    puck = y if sideways else x
    angle = (puck - 0.5) * _ANGLE_SPAN_DEG * _DEG_TO_RAD
    scale = feather * float(extent)
    step_x = int(_FIXED_ONE * math.sin(angle) / scale)
    step_y = int(_FIXED_ONE * math.cos(angle) / scale)
    if sideways:
        step_x, step_y = step_y, step_x
    if quadrant == 2:
        step_y = -step_y
    elif quadrant == 3:
        step_x = -step_x
    return step_x, step_y


def _spatial_weight(
    height: int, width: int, center: tuple[int, int], step: tuple[int, int]
) -> np.ndarray:
    """A képpontonkénti keverési súly `0…255`-ben (`0x0090f79d`–`0x0090f7e9`).

    A natív egy egész akkumulátort görget: soronként `2·lépés_y`,
    képpontonként `2·lépés_x`, a középponthoz képest nullázva. Ebből
    `idx = −(akkumulátor >> 8)`, a rámpa páratlan szimmetriával olvasva,
    végül `(256 + rámpa) >> 1`.
    """
    center_x, center_y = center
    step_x, step_y = step
    columns = (np.arange(width, dtype=np.int64) - center_x) * step_x
    rows = (np.arange(height, dtype=np.int64) - center_y) * step_y
    index = -((2 * (columns[np.newaxis, :] + rows[:, np.newaxis])) >> 8)
    table = dir_tint_ramp_table()
    magnitude = np.clip(np.abs(index), 0, _RAMP_SIZE - 1)
    ramp = np.where(index < 0, -table[magnitude], table[magnitude])
    saturated = np.where(
        index > _RAMP_SIZE - 1, 255, np.where(index < -(_RAMP_SIZE - 1), -255, ramp)
    )
    return (256 + saturated) >> 1


def apply_dir_tint(
    image: np.ndarray,
    x: float,
    y: float,
    gradient: float,
    shade: float,
    color: tuple[int, int, int],
    direction: int = 0,
) -> np.ndarray:
    """Irányított (átmenetes) színezés a natív modell szerint (#874).

    A `gradient` a **Feather** csúszka (0. paraméter), a `shade` a
    **Shade** (1. paraméter). A `direction` a natív `[szűrő+0xc4]`
    negyedválasztója; a `.picasa.ini` `dir_tint=` alakja nem hordozza,
    ezért az alapértéke `0` — a natív a `-1`-et is nullának veszi.

    A lépések:

    1. a `Feather` alsó korlátja **0,001**;
    2. a középpont `(W·x, H·y)`, egészre csonkítva;
    3. a szög `(puck − 0,5) × 30` **fok** — páros negyednél a puck `x`,
       páratlannál a puck `y` adja, tehát ±15° billentés;
    4. a súly egy 384 bájtos, `sin`/`cos`-ból számolt lépésvektor mentén
       olvasott S-rámpából jön;
    5. a képpont értékét egy 256 elemű, `uint16` tónusgörbe hajlítja, a
       görbe paramétere `p = 1 / clamp(1 − Shade, 0,01, 99,9)`;
    6. a színezés **szorzás** (`tónus × szín / 256`) — tiszta fehérnél a
       natív ki is hagyja —, végül lineáris keverés az eredetivel a súly
       szerint.

    `Shade = 0` esetén a görbe azonosság, tehát a kép **változatlan**.
    """
    validate_image(image)
    height, width = image.shape[:2]
    feather = max(float(gradient), DIR_TINT_FEATHER_FLOOR)
    center = (int(width * float(x)), int(height * float(y)))
    step = _step_vector(float(x), float(y), feather, height, width, int(direction))
    weight = _spatial_weight(height, width, center, step)

    param = min(max(1.0 - float(shade), _CURVE_PARAM_MIN), _CURVE_PARAM_MAX)
    lut = dir_tint_tone_lut(1.0 / param)
    source = image.astype(np.int32)
    toned = (lut[image] >> 8).astype(np.int32)
    if tuple(int(channel) for channel in color) != _NEUTRAL_COLOR:
        tint = np.array(color, dtype=np.int32)
        toned = (toned * tint) >> _TINT_SHIFT
    blended = source + (((toned - source) * weight[..., np.newaxis]) >> 8)
    return np.clip(blended, 0, 255).astype(np.uint8)
