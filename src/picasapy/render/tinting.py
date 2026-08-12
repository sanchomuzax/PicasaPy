"""Színező effekt-műveletek: tint, ansel, dir_tint.

Mért alapok (`docs/specs/filters-decoded.md`, 3. kör):

- **tint** — `tint=1,79.842102,ffff` szürke rámpán az R-csatornát nullázza,
  G és B változatlan: a rövid `ffff` szín balra nullákkal kiegészítve
  `0000ffff` (cián) → a luma csatornánkénti szorzása a színnel pontosan ezt
  adja. A `preserve` paraméter szürkén mérten hatástalan; színes képen a
  króma visszakeverésének súlyaként értelmezzük (0..100 skála) — KÖZELÍTÉS.
- **ansel** (Filtered B&W) — a színparaméter **SZŰRŐ**, nem festék: a
  csatornák súlyát adja a szürkévé alakításban, a kimenet mindig semleges
  (R=G=B). A tónusgörbe a `referencia/filteredbw/` fehér szűrős exportjából
  MÉRT (#317), nem gamma-közelítés. Ld. `apply_ansel` docstringjét.
- **dir_tint** — nincs mért kimeneti adat; a modell (függőleges színátmenet
  az y középpont körül, `gradiens` szélességű átmenettel, `árnyék` erősségű
  keveréssel a szín felé; az x és az irány szerepe méretlen) dokumentált
  KÖZELÍTÉS — a #115 golden-harness pontosítja majd.

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
from picasapy.render.effects import _radius_grid

_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{1,8}$")

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

# tint: a preserve paraméter skálája (79.842102 az éles példa) — 0..100.
_PRESERVE_SCALE = 100.0


def parse_rgb_hex(value: str) -> tuple[int, int, int]:
    """A filters-beli hex színparaméter (AARRGGBB) értelmezése (R, G, B)-ként.

    A Picasa a vezető nullákat elhagyja (pl. `ffff` = `0000ffff` → cián),
    ezért az értéket balra nullákkal 8 jegyre egészítjük ki; az alfa-mezőt
    nem használjuk.
    """
    text = value.strip()
    if not _HEX_PATTERN.match(text):
        raise ValueError(f"Érvénytelen hex színérték: {value!r}")
    padded = text.rjust(8, "0")
    return (int(padded[2:4], 16), int(padded[4:6], 16), int(padded[6:8], 16))


def _luma(image: np.ndarray) -> np.ndarray:
    """Rec.601 luminancia float32 (H, W) tömbként."""
    image_f = image.astype(np.float32)
    return (
        np.float32(0.299) * image_f[..., 0]
        + np.float32(0.587) * image_f[..., 1]
        + np.float32(0.114) * image_f[..., 2]
    )


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


def _colorize(gray: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    """Szürke (H, W) float kép csatornánkénti színezése: `ki_c = szürke·c/255`."""
    factors = np.array(color, dtype=np.float32) / np.float32(255.0)
    return gray[..., np.newaxis] * factors


def apply_tint(
    image: np.ndarray, preserve: float, color: tuple[int, int, int]
) -> np.ndarray:
    """Színezés: a Rec.601 luma szorzása a színnel, króma-visszakeveréssel.

    `ki = luma·szín/255 + (preserve/100)·(be − luma)` — a mért cián eset
    (szürkén R=0, G=B változatlan) pontos; a preserve súly-értelmezése
    színes képen KÖZELÍTÉS.
    """
    validate_image(image)
    gray = _luma(image)
    tinted = _colorize(gray, color)
    keep = float(np.clip(preserve / _PRESERVE_SCALE, 0.0, 1.0))
    if keep > 0.0:
        tinted = tinted + np.float32(keep) * (
            image.astype(np.float32) - gray[..., np.newaxis]
        )
    return _to_uint8(tinted)


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
    modellé 6,11, az érintetlen képé 15,15). A nem fehér szűrőszínekre
    nincs export — ott a súlyozás a fenti képlet szerinti KÖVETKEZTETÉS.
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


def apply_dir_tint(
    image: np.ndarray,
    x: float,
    y: float,
    gradient: float,
    shade: float,
    color: tuple[int, int, int],
) -> np.ndarray:
    """Irányított (átmenetes) színezés — dokumentált KÖZELÍTÉS.

    Függőleges színátmenet: az `y` normált magasság körüli, `gradient`
    szélességű sávban a súly 1-ről 0-ra fut le; felette a kép `shade`
    erősséggel a szín felé keveredik, alatta változatlan. Az `x` paraméter
    és az átmenet iránya méretlen — itt nem használt.
    """
    validate_image(image)
    height = image.shape[0]
    rows = (np.arange(height, dtype=np.float32) + 0.5) / np.float32(height)
    span = max(gradient, 1e-6)
    weight = np.clip(0.5 - (rows - np.float32(y)) / np.float32(span), 0.0, 1.0)
    strength = float(np.clip(shade, 0.0, 1.0))
    if strength == 0.0:
        return image.copy()
    image_f = image.astype(np.float32)
    target = np.array(color, dtype=np.float32)
    blend = weight[:, np.newaxis, np.newaxis] * np.float32(strength)
    return _to_uint8(image_f + blend * (target - image_f))


#: A `radtint` maszk-LUT mérete a natív kódban (`0x90aeb0`, #565). A méret
#: önmagában nem befolyásolja a képet (a smoothstep folytonos), de a
#: visszafejtett szerkezettel való egyezés kedvéért itt is 1024 elem.
_RADTINT_LUT_SIZE = 1024

#: A `radtint` szorzó-tint osztója a natív magban (`0x90b370`):
#: `tinted = source * tint / 256`.
_RADTINT_TINT_DIVISOR = 256.0


def radtint_lut(size: int = _RADTINT_LUT_SIZE) -> np.ndarray:
    """A `radtint` maszk-LUT-ja: köbös smoothstep, `t*t*(3-2*t)` (#565).

    A natív segédfüggvény (`0x90aeb0`) egy `size` elemű táblát tölt fel a
    0..1 tartományon egyenletesen mintavételezett smoothstep-értékekkel; a
    feldolgozó mag (`0x90b370`) ebből olvassa ki a keverési súlyt.
    """
    if size < 2:
        raise ValueError(f"Érvénytelen LUT-méret: {size}")
    t = np.linspace(0.0, 1.0, size, dtype=np.float32)
    return (t * t * (np.float32(3.0) - np.float32(2.0) * t)).astype(np.float32)


def apply_radtint(
    image: np.ndarray,
    x: float,
    y: float,
    feather: float,
    color: tuple[int, int, int],
) -> np.ndarray:
    """Sugaras árnyalás (`radtint`) — radiális **szorzó** színezés (#565).

    A visszafejtett natív viselkedés (regisztráció `0x8f8730`, mag
    `0x90b370`, maszk-LUT `0x90aeb0`):

    - az (x, y) fókuszpont körül normalizált (a két tengelyen külön
      normált, tehát elliptikus) távolság számolódik,
    - a fókuszpont környékén a kép **változatlan**,
    - kifelé haladva a színezés egy 1024 elemű, köbös smoothstep LUT
      szerint erősödik,
    - a teljes tint csatornánként `tinted = source * tint / 256` (szorzás,
      nem keverés a szín FELÉ — ez a lényegi különbség a `dir_tint`-hez
      képest), az alfa érintetlen,
    - az átmeneti sávban lineáris keverés fut az eredeti és a szorzott kép
      között.

    A `feather` **affin leképezése FELTÉTELEZÉS**, golden-mérés még nincs
    rá (ld. #565 „Nyitott kalibráció"): a `filterdesc.xml` szerint a csúszka
    0..1 tartományú, alapértéke 0,25. Itt a feather az átmeneti sáv
    SZÉLESSÉGE, a fókuszponttól mért legnagyobb távolság (`r_max`) felénél
    KÖZÉPPONTOSAN: a sáv a `(0,5 − feather/2) · r_max` sugárnál kezdődik és
    a `(0,5 + feather/2) · r_max` sugárnál ér véget. Így `feather = 0` éles
    határt ad a fél sugárnál (belül érintetlen, kívül teljes tint),
    `feather = 1` pedig a fókuszponttól a legtávolabbi sarokig húzódó, végig
    lágy átmenetet. Minden feather-értéknél igaz marad a két rögzített pont:
    a fókuszpont érintetlen, a legtávolabbi sarok teljes tintet kap. A mérés
    a leképezést pontosíthatja — a pixelművelet és az algoritmuscsalád
    viszont már nem kérdéses.
    """
    validate_image(image)
    height, width = image.shape[:2]
    radii = _radius_grid(height, width, x, y)
    # a normáláshoz a fókuszponttól MÉRT legnagyobb távolság kell (a kép
    # legtávolabbi sarka) — enélkül a nem középre tett fókuszpontnál a
    # maszk egy része sosem érné el a teljes erősséget
    max_radius = float(radii.max())
    if max_radius <= 0.0:
        return image.copy()
    width = float(np.clip(feather, 0.0, 1.0))
    start = np.float32((0.5 - width / 2.0) * max_radius)
    span = np.float32(max(width * max_radius, 1e-6))
    t = np.clip((radii - start) / span, 0.0, 1.0)
    lut = radtint_lut()
    weight = lut[np.rint(t * np.float32(len(lut) - 1)).astype(np.int32)]

    image_f = image.astype(np.float32)
    tint = np.array(color, dtype=np.float32) / np.float32(_RADTINT_TINT_DIVISOR)
    tinted = image_f * tint
    blend = weight[..., np.newaxis]
    return _to_uint8(image_f + blend * (tinted - image_f))
