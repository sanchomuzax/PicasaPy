"""Színező effekt-műveletek: tint, ansel, dir_tint.

Mért és binárisból megerősített alapok (`docs/specs/filters-decoded.md`):

- **tint** — a natív callback (`0x008f9630`, #872) előbb a közös
  `0x009db610` szinthúzót futtatja 0,30-as keveréssel, majd 256-os súlyú,
  egész lumás telítetlenítést, telítettségfüggő gamma-LUT-ot és a tint
  legnagyobb komponensére normalizált szorzást végez. A `CarefulEnhance`
  nálunk nem beállítás; a Picasa alapértelmezett KI ágát használjuk.
- **ansel** (Filtered B&W) — a színparaméter **SZŰRŐ**, nem festék: a
  csatornák súlyát adja a szürkévé alakításban, a kimenet mindig semleges
  (R=G=B). A tónusgörbe a `referencia/filteredbw/` fehér szűrős exportjából
  MÉRT (#317), nem gamma-közelítés. Ld. `apply_ansel` docstringjét.
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
from picasapy.render.radial_mask import apply_radial_mask

_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]+$")

#: Az eredeti beolvasó ennyi jegyet vesz a hexmezőből — a nyolcadik utáni
#: rész NEM számít (#1142). Mérve: `000000ffff` ugyanazt a ΔE-t adja
#: (106,728), mint a `0000ff` — ld. `docs/specs/picasa-ini-format.md`,
#: „A hex színmező" szakasz.
_HEX_FIELD_DIGITS = 8

#: A `tint` a `-1,0f` jelzővel hívja a közös szinthúzót; ez a natív
#: alapértelmezett 0,30-as vágópont-keverést választja (#872).
_TINT_LEVELS_BLEND = 0.30

#: `ansel` (Filtered B&W) MÉRT tónusgörbéje — `referencia/filteredbw/`
#: (fehér szűrőszínnel exportált 2560×1702-es kép, #317): a szűrt szürke
#: 0, 16, 32 … 240, 255 értékeihez tartozó kimenet. Enyhe S-alak, a
#: korábbi gamma-közelítésnél (0,93) mérhetően jobb: az eltérés a valódi
#: Picasa-kimenettől **6,11 → 0,53** (az érintetlen képé 15,15).
_ANSEL_ANCHOR_INPUTS = tuple(range(0, 256, 16)) + (255,)
_ANSEL_ANCHOR_CURVE = (
    0.1, 16.8, 34.0, 51.0, 67.7, 84.3, 100.7, 117.0, 133.0, 148.9,
    164.5, 180.0, 195.3, 210.4, 225.4, 240.0, 253.8,
)

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


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


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


def apply_ansel(image: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """Filtered B&W (`ansel`): a szín **SZŰRŐ**, nem festék — a kimenet
    mindig szürke (#317).

    A `color` a fényképészeti szűrők szerepét játssza (a Picasa saját
    palettája sárga/narancs/vörös/zöld szűrőkből áll, ld.
    `referencia/filteredbw/panel-screenshot-2.png`): a csatornák súlyát
    adja meg a szürkévé alakításnál — `szürke = Σ(szín_c · c) / Σ szín_c` —,
    NEM színezi a végeredményt. A korábbi változat a kimenetet a színnel
    festette; a fehér szűrős exportnál ez nem látszott (fehérrel a festés
    semleges), a mérés viszont a súlyokat is eldöntötte: fehér szűrővel a
    három csatorna súlya 0,345 / 0,336 / 0,326 — gyakorlatilag EGYENLŐ,
    tehát a szín az egyetlen súlyforrás (nem szorzódik rá a Rec.601 luma).

    A szűrt szürkére a MÉRT tónusgörbe kerül (`_ANSEL_ANCHOR_CURVE`); a
    fehér szűrős exporttól való átlagos eltérés **0,53** (a korábbi
    modellé 6,11, az érintetlen képé 15,15).

    A súlyozás 2026-08-23 óta **MEGERŐSÍTETT, nem következtetés** (#939):
    a natív visszahívás (`0x008f8410`) a szín három bájtját `255,0`-val
    osztja, a mag (`0x0090e680`) pedig **első lépésben normalizálja őket
    az ÖSSZEGÜKKEL** (`1/(w1+w2+w3)`, `0x0090e6ca`–`0x0090e6e8`), majd
    `256,0`-lal szoroz a fixpontos súlyokhoz. A `/255` a normalizálásban
    kiesik, tehát a natív számítás azonos az itteni képlettel. Levezetés:
    `docs/specs/filters-decoded.md`, „`ansel` — a SÚLYOZÁS igazolva".
    """
    validate_image(image)
    weights = np.array(color, dtype=np.float32)
    total = float(weights.sum())
    if total <= 0.0:
        # elfajult (fekete) szűrő: nincs mit súlyozni — egyenletes szürke
        weights = np.full(3, 1.0 / 3.0, dtype=np.float32)
    else:
        weights = weights / np.float32(total)
    filtered = (image.astype(np.float32) * weights).sum(axis=-1)
    toned = np.interp(filtered, _ANSEL_ANCHOR_INPUTS, _ANSEL_ANCHOR_CURVE)
    gray = _to_uint8(toned)
    return np.stack([gray, gray, gray], axis=-1)


#: A `radtint` szorzó-tint osztója a natív magban (`0x90b370`):
#: `tinted = source * tint / 256`. Az egész osztás (padló) a 684-es goldenen
#: mérve jobb a kerekítésnél (ΔE 0,70 vs 0,81, #3453); a natív osztás módja
#: nincs kiolvasva.
_RADTINT_TINT_DIVISOR = 256


def apply_radtint(
    image: np.ndarray,
    x: float,
    y: float,
    feather: float,
    color: tuple[int, int, int],
) -> np.ndarray:
    """Sugaras árnyalás (`radtint`) — radiális **szorzó** színezés (#565, #3453).

    A natív mag (`0x90b370`) a `radblur`/`radsat` közös sugaras maszkját
    hívja (`0x0090b050` + `0x0090aeb0`, `render/radial_mask.py`),
    `FUN_0090aeb0(0, Feather)` alakban (spec: `filters-decoded.md`, #317):

    - a sugár `min(W, H)/2 · (Feather + 1)` — izotróp, képpontban;
    - az élesség beégetett nulla, tehát a smoothstep a középponttól a
      sugárig végig fut;
    - a középen az eredeti kép, a sugáron túl a teljes tint, amely
      csatornánként `source · tint / 256` (szorzás, nem a szín FELÉ
      keverés — ez a lényegi különbség a `dir_tint`-hez képest).
    """
    validate_image(image)
    tint = np.array(color, dtype=np.int64)
    tinted = (image.astype(np.int64) * tint // _RADTINT_TINT_DIVISOR).astype(np.uint8)
    return apply_radial_mask(image, tinted, x, y, feather, 0.0)


#: A `dir_tint` a saját moduljában él (#874) — a régi importútvonal
#: (`picasapy.render.tinting.apply_dir_tint`) újraexportként marad meg.
__all__ = [
    "apply_ansel",
    "apply_dir_tint",
    "apply_radtint",
    "apply_tint",
    "parse_rgb_hex",
]
