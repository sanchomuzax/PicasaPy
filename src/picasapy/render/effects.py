"""Térbeli effekt-műveletek: Vignette, glow/glow2, radblur, radsat.

Mért alapok (`docs/specs/filters-decoded.md`):

- **Vignette** (4. kör): multiplikatív radiális maszk, a
  `Vignette=1,35.0,1.4,0.0,00000000` alapbeállításnál lemért profillal
  (közép 1,000 · r≈0,25: 0,994 · r≈0,45: 0,729 · r≈0,65: 0,328 ·
  sarok 0,250). A paraméterek analitikus modellje nyitott — a nem
  alapértelmezett paraméterek hatása itt KÖZELÍTÉS (sugár- és
  erősség-skálázás a mért profilon).
- **glow/glow2** (#668, #3913): a KÖZÖS NATÍV elmosó magon (`render/iir_blur.py`,
  `0x009dd0d0`) fut, a binárisból kiolvasott egész aritmetikával (gamma-tábla,
  Screen `>> 8`, visszakeverés) — ld. `apply_glow`.
- **radblur** (#668): a natív elmosó mag + a natív sugaras smoothstep-maszk
  (`render/radial_mask.py`) — négy golden-páron MÉRVE, ld. `apply_radblur`.
- **radsat** (#3517): a `filters-decoded.md` „radsat — TELJES" (#317)
  algoritmusa — a `radblur`-rel KÖZÖS smoothstep-tábla (`0x0090aeb0`,
  `render/radial_mask.py`) és a saját mag (`0x0090b660`): 77/151/28 luma,
  a táblán túl teljes szürke. A 684-es Picasa-exporton MÉRVE, ld.
  `apply_radsat`.
- **vignette_gain / apply_vignette**: a zóna itt SZÁNDÉKOSAN ellipszis
  (tengelyenkénti `_radius_grid`) — nyolc eredeti Picasa-export mérése
  (#859 issue-komment, 2026-08-18) MEGCÁFOLTA az izotróp hipotézist: az
  ellipszis-sugárral számolt megfigyelt erősítés szórása kb. 40%-kal
  kisebb, mint a kör-sugárral számolté. Ez a `radsat`-tól ELTÉRŐ natív
  függvényre vezethető vissza (`0x0090b050`-től független útvonal) — ide
  tehát NEM vonatkozik az egységesítés.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.iir_blur import apply_picasa_blur
from picasapy.render.radial_mask import (
    RADIAL_TABLE_SIZE,
    apply_radial_mask,
    radial_weight_table,
    squared_distance_index,
)

# A Vignette mért radiális profilja (r = képmérettel normált táv a középtől;
# a sarok r-je √0,5 ≈ 0,7071). A profilon túl a maszk a sarokértéken marad.
_VIGNETTE_RADII = (0.0, 0.25, 0.45, 0.65, 0.7071)
_VIGNETTE_GAINS = (1.0, 0.994, 0.729, 0.328, 0.250)

# A mért profil referencia-paraméterei (a golden-kit alapbeállítása).
_VIGNETTE_REF_INNER = 35.0
_VIGNETTE_REF_STRENGTH = 1.4

#: A paraméter nélküli `glow` (v1) golden-kitben mért alapértékei.
GLOW_V1_INTENSITY = 0.432749
GLOW_V1_RADIUS = 2.469705

#: A `radblur` elmosási sugarának képszélesség-hányada: a binárisban álló
#: `0,01` (`[0xcf40b8]`, a callback `0x008f85c1`–`0x008f8617` szakasza).
#: A korábbi, illesztett `0,009` a közös elmosó mag régi együtthatóját
#: kompenzálta (#3916, #3917).
RADBLUR_WIDTH_FRACTION = 0.01

#: A natív képlet additív tagja (`+ 0,001`) — az Amount = −1 végponton ez
#: tartja a sugarat pozitívan.
RADBLUR_EPSILON = 0.001

#: A `radblur`-nak nincs „Élesség" csúszkája: a callback a maszkoló-keverőnek
#: (`0x0090b050`) beégetett `0,0`-t ad át (`0x008f8645` `fldz`) — ez a
#: bináris értéke, nem illesztés (#3916).
RADBLUR_SHARPNESS = 0.0


def _radius_grid(height: int, width: int, x: float, y: float) -> np.ndarray:
    """Pixelközéppontok normált távolsága az (x, y) középponttól, float32.

    SZÁNDÉKOSAN tengelyenkénti (anizotróp) normálás — nem négyzetes képen
    ELLIPSZIS-zónát ad. A `vignette_gain`/`apply_vignette` ezt hívja, mert
    nyolc eredeti Picasa-export mérése (#859) igazolta, hogy a vignetta
    zónája valóban ellipszis. A `render/tinting.py` (`radtint`) is ezt
    hívja — arra nincs mérésünk, ezért egyelőre változatlan marad.

    A `radsat` NEM ezt hívja: annak a zónája — a `radblur`-rel közös natív
    függvény miatt — izotróp kör (ld. `apply_radsat` és
    `radial_mask.squared_distance_index`).
    """
    cols = (np.arange(width, dtype=np.float32) + 0.5) / np.float32(width) - np.float32(x)
    rows = (np.arange(height, dtype=np.float32) + 0.5) / np.float32(height) - np.float32(y)
    return np.hypot(rows[:, np.newaxis], cols[np.newaxis, :])


def _to_uint8(values: np.ndarray) -> np.ndarray:
    return np.clip(np.rint(values), 0, 255).astype(np.uint8)


def vignette_gain(
    radius: float,
    inner: float = _VIGNETTE_REF_INNER,
    strength: float = _VIGNETTE_REF_STRENGTH,
) -> float:
    """A Vignette multiplikatív maszkjának értéke a normált `radius` helyen.

    Az alapértelmezett paraméterekre a mért profilt adja vissza; más
    paraméterekre KÖZELÍTÉS: az `inner` a profilt sugárban skálázza
    (35 = referencia), a `strength` a sötétítés mélységét (1,4 = referencia).
    """
    if radius < 0:
        raise ValueError(f"A sugár nem lehet negatív: {radius}")
    scale = _VIGNETTE_REF_INNER / inner if inner > 0 else 1.0
    base = float(np.interp(radius * scale, _VIGNETTE_RADII, _VIGNETTE_GAINS))
    depth = strength / _VIGNETTE_REF_STRENGTH
    return float(np.clip(1.0 - depth * (1.0 - base), 0.0, 1.0))


def apply_vignette(
    image: np.ndarray,
    inner: float = _VIGNETTE_REF_INNER,
    strength: float = _VIGNETTE_REF_STRENGTH,
) -> np.ndarray:
    """Vignetta: a mért radiális maszkkal szorozza a képet (minden csatornát).

    A maszk középpontja a kép közepe; a 4. ini-paraméter (0,0) és az 5.
    (szín, 00000000) szerepe méretlen — figyelmen kívül hagyjuk (KÖZELÍTÉS).
    """
    validate_image(image)
    height, width = image.shape[:2]
    radii = _radius_grid(height, width, 0.5, 0.5)
    base = np.interp(
        radii * np.float32(_VIGNETTE_REF_INNER / inner if inner > 0 else 1.0),
        _VIGNETTE_RADII,
        _VIGNETTE_GAINS,
    ).astype(np.float32)
    depth = np.float32(strength / _VIGNETTE_REF_STRENGTH)
    mask = np.clip(1.0 - depth * (1.0 - base), 0.0, 1.0)
    return _to_uint8(image.astype(np.float32) * mask[..., np.newaxis])


#: A `glow` sugarának felső korlátja (`[0xcf48e0]` = 250,0, #3912).
GLOW_MAX_RADIUS = 250.0

#: A `glow` súlyának skálája és felső korlátja: `k = |csonk(256 · i)|` ≤ 256.
_GLOW_WEIGHT_SCALE = 256


def glow_gamma_lut() -> np.ndarray:
    """A Ragyogás előgörbéjének 256 elemű gamma-táblája (#3912, #3913).

    A natív `0x00aa40a0` (argumentum `0,5` → kitevő `1 / 0,5 = 2`):
    `LUT[i] = rint(255 · (f32(i / 255))²)` — az `i / 255` egyszeres
    pontosságú szorzat (`fmul [0xcf4138]`), a hatványozás és a `· 255`
    dupla pontosságú, a `fistp` a legközelebbi egészre kerekít.
    """
    unit = (np.arange(256, dtype=np.float32) * np.float32(1.0 / 255.0)).astype(np.float64)
    return np.rint(255.0 * unit**2).astype(np.uint8)


def glow_premultiply(image: np.ndarray) -> np.ndarray:
    """A Ragyogás előgörbéje: a kép a gamma-táblán át (`glow_gamma_lut`).

    Kitevő 2 — a binárisból kiolvasva (#3912), a korábbi mérés (#668) a
    `(255−c)·c²` alakú tónusemeléssel ugyanezt illesztette.
    """
    validate_image(image)
    return glow_gamma_lut()[image]


def glow_weight(intensity: float) -> int:
    """A visszakeverés súlya: `k = min(|csonk(256 · i)|, 256)`, `i ∈ [−1, 1]`.

    A callback (`0x008f8f70`) az Intenzitás abszolút értékét adja tovább;
    a mag `[−1, 1]`-re vág és csonkol (#3912).
    """
    clipped = np.clip(np.float32(intensity), np.float32(-1.0), np.float32(1.0))
    scaled = abs(int(np.trunc(np.float32(clipped) * np.float32(_GLOW_WEIGHT_SCALE))))
    return min(scaled, _GLOW_WEIGHT_SCALE)


def glow_blend(original: np.ndarray, blurred: np.ndarray, weight: int) -> np.ndarray:
    """A natív keverés (`0x009ac3f0`) csatornánként, egész aritmetikával.

    ```
    s  = 255 − (((255 − t) · (255 − o)) >> 8)     ← Screen
    ki = s + (((o − s) · (256 − k)) >> 8)         ← visszakeverés
    ```

    A negatív szorzat `>>`-je lefelé kerekít — a csomagolt 16 bites út
    modulo-256-os összeadása ugyanezt adja. `k = 0`-nál `ki = o` pontosan.
    """
    o_val = original.astype(np.int32)
    t_val = blurred.astype(np.int32)
    screen = 255 - (((255 - t_val) * (255 - o_val)) >> 8)
    result = screen + (((o_val - screen) * (_GLOW_WEIGHT_SCALE - weight)) >> 8)
    return result.astype(np.uint8)


def radblur_blur_radius(width: int, amount: float) -> float:
    """A `radblur` elmosási sugara képpontban — a KÉPSZÉLESSÉGHEZ kötve.

    `sugár = szélesség · 0,01 · (Amount + 1) + 0,001` — a bináris képlete
    (`0x008f8520`). Ezért néz ki a Lágy fókusz ugyanúgy kicsi és nagy
    képen — **ellentétben a `glow`-val**, amelynek a sugara képpontban
    abszolút (4.2.5).
    """
    return width * RADBLUR_WIDTH_FRACTION * (float(amount) + 1.0) + RADBLUR_EPSILON


def apply_glow(image: np.ndarray, intensity: float, radius: float) -> np.ndarray:
    """Ragyogás (`glow`, `glow2`) — a natív egész aritmetika (#3912, #3913).

    ```
    k   = min(|csonk(256 · Intenzitás)|, 256)       ← Intenzitás [−1, 1]-re vágva
    elő = LUT[be]                                   ← gamma-tábla, kitevő 2
    t   = iir_blur(elő, R, R)                       ← a natív mag, R ∈ [0, 250]
    ki  = glow_blend(be, t, k)                      ← Screen + visszakeverés
    ```

    A sugár képpontban abszolút (4.2.5); 0-s sugárnál a natív mag nem mos
    el. Mérve a 684-es készlet Picasa-exportján (átlag-ΔE, `glow` = `glow2`):
    alap 0,327 → 0,264, max 0,514 → 0,284, min 0,121.
    """
    validate_image(image)
    weight = glow_weight(intensity)
    if weight == 0:
        return image.copy()
    span = float(np.clip(radius, 0.0, GLOW_MAX_RADIUS))
    blurred = apply_picasa_blur(glow_premultiply(image), span, span)
    return glow_blend(image, blurred, weight)


def apply_radblur(
    image: np.ndarray, x: float, y: float, size: float, amount: float
) -> np.ndarray:
    """Lágy fókusz (`radblur`) — natív elmosó mag + natív sugaras maszk (#668).

    A korong közepén az EREDETI kép marad, a peremen az elmosott; az átmenet
    a `radial_mask` smoothstep-táblája. A `Size` a korong sugarát adja
    (`min(SZ, MA)/2 · (Size+1)`), az `Amount` az elmosás erejét
    (ld. `radblur_blur_radius`).

    ⚠️ **Az `Amount = 0` NEM azonosság** — a korábbi modell annak vette. A
    `golden-kit/09-effects` `radblur=1,0.411585,0.611111,0,0` exportja ezt
    megcáfolja: ott a peremen a kép átlagosan 26 szintnyit változik.

    Ellenőrizve négy golden-páron (`chart_color`, `photo01`, `photo04`,
    `chart_ramp`): átlagos ΔE 0,09…0,68 (#3917), míg a korábbi közelítésé
    1,92…11,88 volt.
    """
    validate_image(image)
    radius = radblur_blur_radius(image.shape[1], amount)
    blurred = apply_picasa_blur(image, radius, radius)
    return apply_radial_mask(image, blurred, x, y, size, RADBLUR_SHARPNESS)


def apply_radsat(
    image: np.ndarray, x: float, y: float, radius: float, sharpness: float
) -> np.ndarray:
    """Fókuszos FF (`radsat`) — a natív algoritmus (#317, #3517).

    Paraméterek (a lánc sorrendjében): a középpont képarányos `x`, `y`
    koordinátája; a **méret** (`radius`, `[-1, 1]`, a szűrő `+0x28` mezője):
    `r = min(W, H)/2 · (méret + 1)`; az **élesség** (`sharpness`, `[0, 1]`,
    a `+0x2c` mező): `k = 1/(1 − 0,99·√élesség)`.

    A lecsengés-tábla a `radblur`-rel közös `0x0090aeb0` smoothstep-tábla;
    a fordulópont a sugár FELÉNÉL van (`t = 0,5`). Képpontonként
    (`0x0090b660`):

    ```
    Y = (77·R + 151·G + 28·B) >> 8
    idx < 1024:  c' = c + (((Y − c) · (256 − tábla[idx])) >> 8)
    különben:    c' = Y                       (a táblán túl teljes szürke)
    ```

    Mérve a 684-es készlet Picasa-exportján (átlag-ΔE): alap 0,082, max
    0,128, min 0,034 — a régi közelítésé 6,468, 3,657 és 2,730 volt.
    """
    validate_image(image)
    height, width = image.shape[:2]
    # A `√` miatt a tartományon kívüli élességet a széléhez vágjuk (kézzel
    # szerkesztett ini-ből jöhet); a natív csúszka `[0, 1]`.
    steepness = float(np.sqrt(min(max(float(sharpness), 0.0), 1.0)))
    table, shift = radial_weight_table(width, height, radius, steepness)
    if float(radius) <= -1.0:
        # Nulla sugárnál a spec `t = √(i/r²)`-e a 0. elemen is 0/0: ott a
        # középpont sem marad színes (a mért `min` eset ezzel 0,034).
        table = np.zeros_like(table)
    index = squared_distance_index(width, height, x, y, shift)
    inside = (index < RADIAL_TABLE_SIZE)[..., np.newaxis]
    weight = (256 - table[np.clip(index, 0, RADIAL_TABLE_SIZE - 1)])[..., np.newaxis]
    channels = image.astype(np.int64)
    luma = (
        77 * channels[..., 0] + 151 * channels[..., 1] + 28 * channels[..., 2]
    )[..., np.newaxis] >> 8
    # A `>>` itt aritmetikai eltolás (padló), ahogy a spec C-alakja.
    blended = channels + (((luma - channels) * weight) >> 8)
    return np.clip(np.where(inside, blended, luma), 0, 255).astype(np.uint8)
