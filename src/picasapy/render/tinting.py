"""Színező effekt-műveletek: tint, ansel, dir_tint.

Mért és binárisból megerősített alapok (`docs/specs/filters-decoded.md`):

- **tint** — a natív callback (`0x008f9630`, #872) előbb a közös
  `0x009db610` szinthúzót futtatja 0,30-as keveréssel, majd 256-os súlyú,
  egész lumás telítetlenítést, telítettségfüggő gamma-LUT-ot és a tint
  legnagyobb komponensére normalizált szorzást végez. A `CarefulEnhance`
  nálunk nem beállítás; a Picasa alapértelmezett KI ágát használjuk.
- **ansel** (Filtered B&W) — a színparaméter **SZŰRŐ**, nem festék: a
  csatornák súlyát adja a szürkévé alakításban, a kimenet mindig semleges
  (R=G=B). A natív mag (`0x0090e680`) egész aritmetikáját követi: fixpontos
  súlyok, a képből számolt `k` erősségű S-görbe (#3840). Ld. `apply_ansel`
  docstringjét.
- **dir_tint** (Graduated Tint) — a natív modell visszafejtve és a
  Picasa-referenciához MÉRVE (#874): elforgatható átmenet, tónusgörbés
  szorzó színezés. A megvalósítás a `picasapy.render.dir_tint` modulban
  él, innen csak újraexportáljuk; a részletek és a mért eltérések ott.

#510: a `color` paraméterek (mind a három függvénynél) **RGB**
csatornasorrendűek — ugyanaz, mint a hívó `render/chain.py`/`glimmer_*`
csővezeték belső képábrázolása (ld. `glimmer_ops.py` modul-docstringjét).
`parse_rgb_hex` a `filters=` hexát (`AARRGGBB`) is `(R, G, B)`-ként adja
vissza, nincs csere.
"""

from __future__ import annotations

import re

import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.dir_tint import apply_dir_tint
from picasapy.render.ops import apply_channel_levels_stretch
from picasapy.render.radial_mask import (
    RADIAL_TABLE_SIZE,
    radial_weight_table,
    squared_distance_index,
)

_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]+$")

#: Az eredeti beolvasó ennyi jegyet vesz a hexmezőből — a nyolcadik utáni
#: rész NEM számít (#1142). Mérve: `000000ffff` ugyanazt a ΔE-t adja
#: (106,728), mint a `0000ff` — ld. `docs/specs/picasa-ini-format.md`,
#: „A hex színmező" szakasz.
_HEX_FIELD_DIGITS = 8

#: A `tint` a `-1,0f` jelzővel hívja a közös szinthúzót; ez a natív
#: alapértelmezett 0,30-as vágópont-keverést választja (#872).
_TINT_LEVELS_BLEND = 0.30

#: `ansel` (Filtered B&W) natív magja (`0x0090e680`, #3840): a súlyok és a
#: 16 bites szürke fixpontja (`W_c = csonk(256 · w_c)`, `[0xcf39d8]` = 256,0).
_ANSEL_WEIGHT_SCALE = 256
_ANSEL_Y_MAX = 0xFFFF


def parse_rgb_hex(value: str) -> tuple[int, int, int]:
    """A filters-beli hex színparaméter (AARRGGBB) értelmezése (R, G, B)-ként.

    A Picasa a vezető nullákat elhagyja (pl. `ffff` = `0000ffff` → cián),
    ezért a rövidebb értéket balra nullákkal 8 jegyre egészítjük ki; az
    alfa-mezőt nem használjuk.

    A NYOLCNÁL HOSSZABB mező sem hiba: az eredeti beolvasó az **első 8
    jegyet** veszi, a többit eldobja (#1142). Mérve: `000000ffff` →
    `000000ff` = kék, pontosan ugyanazzal a ΔE-vel, mint a `0000ff`. Ez
    korábban kivételt dobott, amitől a lánc EGÉSZ tagja elesett — az
    eredeti viszont lefuttatta.
    """
    text = value.strip()
    if not _HEX_PATTERN.match(text):
        raise ValueError(f"Érvénytelen hex színérték: {value!r}")
    field = text[:_HEX_FIELD_DIGITS].rjust(_HEX_FIELD_DIGITS, "0")
    return (int(field[2:4], 16), int(field[4:6], 16), int(field[6:8], 16))


def parse_alpha_hex(value: str) -> int:
    """A filters-beli hex színparaméter (AARRGGBB) alfa-bájtja (#3902).

    Ugyanazzal a kiegészítéssel és csonkítással, mint a `parse_rgb_hex`:
    a rövidebb mező balra nullázva (`ffffff` → alfa `0`), a hosszabbnak
    az első 8 jegye számít.
    """
    text = value.strip()
    if not _HEX_PATTERN.match(text):
        raise ValueError(f"Érvénytelen hex színérték: {value!r}")
    return int(text[:_HEX_FIELD_DIGITS].rjust(_HEX_FIELD_DIGITS, "0")[:2], 16)


def _desaturate_native(image: np.ndarray, preserve: float) -> np.ndarray:
    """Egész lumás telítetlenítés a natív `0x009a9550` szerint (#872)."""
    # A callback a paramétert 32 bites dwordként (`float`) tölti be, és csak
    # ezután vált FPU-csonkítással egésszé. Az egészhatárok körül a sorrend
    # látható: pl. 79,999999 float32-ként már pontosan 80,0.
    preserve_int = int(np.trunc(np.float32(preserve)))
    if preserve_int == 256:
        return image.copy()

    channels = image.astype(np.int64)
    luma = (
        77 * channels[..., 0]
        + 151 * channels[..., 1]
        + 28 * channels[..., 2]
    ) >> 8
    weight = 256 - preserve_int
    desaturated = channels + (((luma[..., np.newaxis] - channels) * weight) >> 8)
    return np.clip(desaturated, 0, 255).astype(np.uint8)


def _gamma_lut_for_tint(color: tuple[int, int, int]) -> np.ndarray | None:
    """A tint telítettségéből származó gamma-LUT, szürkén `None` (#872)."""
    maximum = max(color)
    scaled_sum = sum(color) * 85
    if maximum <= 0 or scaled_sum <= 0:
        return None

    ratio = np.float32(maximum * 255) / np.float32(scaled_sum)
    factor = (ratio - np.float32(1.0)) * np.float32(0.5) + np.float32(1.0)
    if factor == np.float32(1.0):
        return None
    levels = np.arange(256, dtype=np.float32) / np.float32(255.0)
    gamma_values = (
        np.power(levels, np.float32(1.0) / factor) * np.float32(255.0)
    )
    return np.clip(
        np.floor(gamma_values + np.float32(0.5)), 0, 255
    ).astype(np.uint8)


def _multiply_by_normalized_tint(
    image: np.ndarray, color: tuple[int, int, int]
) -> np.ndarray:
    """Fixpontos tint-szorzás, a legnagyobb színkomponensre normálva."""
    maximum = max(color)
    if maximum <= 0:
        return np.zeros_like(image)
    # A natív callback `lround(65536 / mx)`-et ad a 16.16 szorzónak.
    scale = int(np.floor(65536.0 / maximum + 0.5))
    tint = np.array(color, dtype=np.int64)
    multiplied = (image.astype(np.int64) * tint * scale) >> 16
    return np.minimum(multiplied, 255).astype(np.uint8)


def apply_tint(
    image: np.ndarray, preserve: float, color: tuple[int, int, int]
) -> np.ndarray:
    """A `tint` binárisból megerősített hatlépéses receptje (#872).

    A képi előkészítés után a közös szinthúzó fut 0,30-as keveréssel és
    **CarefulEnhance=KI** beállítással. A `preserve` nulla felé csonkolódik;
    a telítetlenítés súlya `256 − preserve`, a 256-os őrértéknél pedig a
    lépés kimarad. Ezt az egész `77/151/28` luma, a tint telítettségéből
    számolt opcionális gamma-LUT, végül az `mx`-normalizált 16.16 szorzás
    követi. Az opcionális ICC-átvezetés a szokásos Picasa-útvonalon `NULL`,
    ezért a numpy renderútban is tétlen.
    """
    validate_image(image)
    leveled = apply_channel_levels_stretch(
        image, blend=_TINT_LEVELS_BLEND, careful=False
    )
    desaturated = _desaturate_native(leveled, preserve)
    gamma_lut = _gamma_lut_for_tint(color)
    gamma_adjusted = desaturated if gamma_lut is None else gamma_lut[desaturated]
    return _multiply_by_normalized_tint(gamma_adjusted, color)


def _ansel_weights(color: tuple[int, int, int]) -> tuple[int, int, int]:
    """Az `ansel` fixpontos csatornasúlyai a natív mag szerint (#3840).

    A visszahívás (`0x008f8410`) `szín_c / 255`-öt ad át `float`-ként, a mag
    az összeggel normál (`1/Σ`, `f32`), majd `256`-tal szoroz és CSONKOL
    (`0x00c29990`). Fehér szűrőnél `256 · f32(1/3)` = 85,33 → **85**, a
    súlyok összege tehát 255, nem 256.

    A fekete szűrőt (összeg 0) az eredeti NEM kezeli: 0-val oszt. Mi
    ilyenkor a semleges, egyenlő súlyt adjuk — ugyanazt, mint a fehér
    szűrő —, hogy a kép ne romoljon el.
    """
    raw = [float(np.float32(channel / 255.0)) for channel in color]
    total = sum(raw)
    if total <= 0.0:
        raw, total = [1.0, 1.0, 1.0], 3.0
    inverse = 1.0 / total
    scale = np.float32(_ANSEL_WEIGHT_SCALE)
    red, green, blue = (
        int(np.trunc(scale * np.float32(weight * inverse))) for weight in raw
    )
    return red, green, blue


def _ansel_gray16(
    image: np.ndarray,
    weights: tuple[int, int, int],
    channels: np.ndarray | None = None,
) -> np.ndarray:
    """A 16 bites szűrt szürke: `Y = clamp(W·RGB, 0, 0xffff)`.

    `int32` elég: `W_c ≤ 256`, így `Y < 2¹⁸`, és a második menet
    `(0xffff − Y)·Y` szorzata is `2³⁰` alatt marad.
    """
    if channels is None:
        channels = image.astype(np.int32)
    gray = (
        weights[0] * channels[..., 0]
        + weights[1] * channels[..., 1]
        + weights[2] * channels[..., 2]
    )
    return np.clip(gray, 0, _ANSEL_Y_MAX)


def _ansel_strength_details(
    image: np.ndarray,
    weights: tuple[int, int, int],
    gray: np.ndarray | None = None,
    channels: np.ndarray | None = None,
) -> tuple[int, int, int, int | None]:
    """Az `ansel` előjeles `N`, 64 bites összegei és `k` erőssége.

    `S₁ = Σ (2R + 5G + B + 4) >> 3` (gyors luma), `S₂ = Σ Y >> 8`,
    `N = Σⱼ hist[j]·(((256 − j)·j) >> 6)`; `t = f32((S₁ − S₂) / N)`
    `[−1, 1]`-re szorítva, `k = csonk(256 · t)`. Az `N` előjelesen
    olvasott 32 bites akkumulátor, ezért a pontos összeg előbb modulo 2³²
    körbefordul. `S₁` és `S₂` előjeles 64 bites összegek. `N = 0` esetén a
    mag második menet nélkül kilép — ekkor `k` értéke `None`.
    """
    if channels is None:
        channels = image.astype(np.int32)
    if gray is None:
        gray = _ansel_gray16(image, weights, channels)
    fast_luma = (
        2 * channels[..., 0] + 5 * channels[..., 1] + channels[..., 2] + 4
    ) >> 3
    bins = gray >> 8
    histogram = np.bincount(bins.ravel(), minlength=256)
    levels = np.arange(256, dtype=np.int64)
    exact_n = int(histogram @ (((256 - levels) * levels) >> 6))
    midtone = ((exact_n + (1 << 31)) % (1 << 32)) - (1 << 31)
    s1 = int(fast_luma.sum(dtype=np.int64))
    s2 = int(bins.sum(dtype=np.int64))
    if midtone == 0:
        return midtone, s1, s2, None
    ratio = np.float32((s1 - s2) / midtone)
    ratio = min(max(ratio, np.float32(-1.0)), np.float32(1.0))
    strength = int(np.trunc(np.float32(_ANSEL_WEIGHT_SCALE) * ratio))
    return midtone, s1, s2, strength


def _ansel_strength(
    image: np.ndarray,
    weights: tuple[int, int, int],
    gray: np.ndarray | None = None,
    channels: np.ndarray | None = None,
) -> int | None:
    """A natív mag `k` erőssége az első menet összegeiből (#3840, #3990)."""
    return _ansel_strength_details(image, weights, gray, channels)[3]


def _ansel_curve_lift(gray: np.ndarray, strength: int) -> np.ndarray:
    """Az `ansel` S-görbe előjeles eltolása, aritmetikai `>> 8`-cal."""
    return (((_ANSEL_Y_MAX - gray) * gray) >> 14) * strength >> 8


def apply_ansel(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """Filtered B&W (`ansel`): a szín **SZŰRŐ**, nem festék — a kimenet
    mindig szürke (#317).

    A `color` a fényképészeti szűrők szerepét játssza (a Picasa saját
    palettája sárga/narancs/vörös/zöld szűrőkből áll, ld.
    `referencia/filteredbw/panel-screenshot-2.png`): a csatornák súlyát
    adja meg a szürkévé alakításnál, NEM színezi a végeredményt.

    A számítás a natív mag (`0x0090e680`) egész aritmetikája (#3840, #3990; spec:
    `docs/specs/filters-decoded.md`, „`ansel` — a `k` erősség kiolvasva, a
    mag TELJES"), a korábbi mért töréspontsor helyett:

    1. fixpontos súlyok (`_ansel_weights`), `Y = clamp(W·RGB, 0, 0xffff)`;
    2. a kép egészéből egy `k` erősség (`_ansel_strength`), ahol `N` modulo
       2³² halmozódik és előjeles 32 bites értékként oszt;
    3. S-görbe: `v = clamp(Y + ((((0xffff − Y)·Y) >> 14)·k >> 8), 0,
       0xffff)`, a kimenet `R = G = B = v >> 8`.

    `N = 0` esetén az eredeti a második menet nélkül kilép, és a nyers
    16 bites `Y` dwordokat hagyja a pufferben. Mi ilyenkor a `k = 0` ágat
    adjuk (`v = Y`), így a súlyozott szürkeérték változatlan marad; nulla
    előállhat azért is, mert a 32 bites akkumulátor körbefordult.

    A `desat` örökölt kulcs ugyanezt a magot hívja (#711), a lánc ezért
    ide vezeti.
    """
    validate_image(image)
    weights = _ansel_weights(color)
    channels = image.astype(np.int32)
    gray = _ansel_gray16(image, weights, channels)
    strength = _ansel_strength(image, weights, gray, channels) or 0
    del channels
    lifted = _ansel_curve_lift(gray, strength)
    level = (np.clip(gray + lifted, 0, _ANSEL_Y_MAX) >> 8).astype(np.uint8)
    return np.stack([level, level, level], axis=-1)


#: A `radtint` szorzásának eltolása a natív magban (`0x0090b370`):
#: `ki = (be · t) >> 8` (#3945).
_RADTINT_SHIFT = 8


def apply_radtint(
    image: np.ndarray,
    x: float,
    y: float,
    feather: float,
    color: tuple[int, int, int],
) -> np.ndarray:
    """Sugaras árnyalás (`radtint`) — radiális **szorzó** színezés (#565, #3946).

    A natív munkafüggvény (`0x0090b370`) a `radblur`/`radsat` közös
    súlytábláját építi (`0x0090aeb0`, `render/radial_mask.py`)
    `FUN_0090aeb0(0, Feather)` alakban: a sugár `min(W, H)/2 · (Feather + 1)`,
    az élesség beégetett nulla. A képpont-ciklus viszont a sajátja (spec:
    `filters-decoded.md`, „⛳ A `radtint` munkafüggvénye kiolvasva", #3945):

    - a középpont CSONKOLT: `cx = trunc(W·x)`, `cy = trunc(H·y)`;
    - `idx = ((X − cx)² + (Y − cy)²) >> shift`;
    - a táblán belül a maszk a tint SZÍNÉT húzza a fehér felé:
      `t′ = 255 − (((255 − t)·(256 − w)) >> 8)`, kívül `t′ = t`;
    - a képet egyszer szorozza: `ki = (be·t′) >> 8`.

    """
    validate_image(image)
    height, width = image.shape[:2]
    table, shift = radial_weight_table(width, height, feather, 0.0)
    index = squared_distance_index(
        width, height, x, y, shift, truncate_center=True
    )
    tint = np.array(color, dtype=np.int64)
    inside = (index < RADIAL_TABLE_SIZE)[..., np.newaxis]
    weight = table[np.clip(index, 0, RADIAL_TABLE_SIZE - 1)][..., np.newaxis]
    toward_white = 255 - (((255 - tint) * (256 - weight)) >> _RADTINT_SHIFT)
    factor = np.where(inside, toward_white, tint)
    return ((image.astype(np.int64) * factor) >> _RADTINT_SHIFT).astype(np.uint8)


#: A `dir_tint` a saját moduljában él (#874) — a régi importútvonal
#: (`picasapy.render.tinting.apply_dir_tint`) újraexportként marad meg.
__all__ = [
    "apply_ansel",
    "apply_dir_tint",
    "apply_radtint",
    "apply_tint",
    "parse_rgb_hex",
]
