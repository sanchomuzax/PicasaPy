"""Térbeli effekt-műveletek: Vignette, glow/glow2, radblur, radsat.

Mért alapok (`docs/specs/filters-decoded.md`):

- **Vignette** (4. kör): multiplikatív radiális maszk, a
  `Vignette=1,35.0,1.4,0.0,00000000` alapbeállításnál lemért profillal
  (közép 1,000 · r≈0,25: 0,994 · r≈0,45: 0,729 · r≈0,65: 0,328 ·
  sarok 0,250). A paraméterek analitikus modellje nyitott — a nem
  alapértelmezett paraméterek hatása itt KÖZELÍTÉS (sugár- és
  erősség-skálázás a mért profilon).
- **glow/glow2** (#668): a KÖZÖS NATÍV elmosó magon (`render/iir_blur.py`,
  `0x009dd0d0`) fut, nem Gauss-közelítéssel. A teljes modell nyolc valódi
  Picasa-exporton MÉRVE — ld. `apply_glow`.
- **radblur** (#668): a natív elmosó mag + a natív sugaras smoothstep-maszk
  (`render/radial_mask.py`) — négy golden-páron MÉRVE, ld. `apply_radblur`.
- **radsat**: továbbra sincs mért kimeneti adata — az átmenet ALAKJA
  (a `sharpness` hatása a lágyságra) dokumentált KÖZELÍTÉS. A zóna
  GEOMETRIÁJA (a sugár és a középponttól mért távolság) viszont #859 óta
  MÉRT ténnyel igazolt: a `radblur`-rel KÖZÖS natív függvény
  (`0x008f9cf0`) adja, ezért a `radsat` a `radblur`-rel MEGEGYEZŐ
  `native_radius_pixels`/`pixel_distance_grid` segédfüggvényt hívja
  (`render/radial_mask.py`) — izotróp kör, nem tengelyenkénti ellipszis.
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
    apply_radial_mask,
    native_radius_pixels,
    pixel_distance_grid,
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

#: A `radblur` elmosási sugarának képszélesség-hányada. A 4.2.4 dekompilátum
#: `0,01`-et olvas; a négy golden-pár (három kép, két Amount-érték) illesztési
#: minimuma egybehangzóan **0,009**-nél van, ezért a MÉRT értékkel futunk. Az
#: eltérés oka nyitott — a #317 effekt-kalibráció dolga eldönteni.
RADBLUR_WIDTH_FRACTION = 0.009

#: A natív képlet additív tagja (`+ 0,001`) — az Amount = −1 végponton ez
#: tartja a sugarat pozitívan.
RADBLUR_EPSILON = 0.001

#: A `radblur`-nak nincs „Élesség" csúszkája: a közös sugaras maszk
#: `Sharpness` bemenete nála 0 — ezt a négy golden-pár illesztése is
#: megerősíti (0 a minimum, 0,1-től már monoton romlik).
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
    `radial_mask.pixel_distance_grid`).
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


def glow_premultiply(image: np.ndarray) -> np.ndarray:
    """A Ragyogás előgörbéje: a kép **önmagával szorozva** (`be²/255`).

    A natív burkoló (`0x0090d4b0`) az elmosás előtt előkészíti a puffert
    (`FUN_009aabf0` / `FUN_00aa40a0`); hogy ez pontosan négyzetre emelés,
    az MÉRÉSBŐL derült ki: a valódi Picasa-export sík foltjain a tónus-
    emelés `(255−c)·c²` alakú, nem `(255−c)·c` (ami a puszta screen lenne).
    A kitevő illesztése éles minimumot ad 2,0-nál (1,9-nél és 2,1-nél az
    átlagos hiba a kétszeresére nő).
    """
    validate_image(image)
    squared = image.astype(np.int64) ** 2
    return ((squared + 127) // 255).astype(np.uint8)


def radblur_blur_radius(width: int, amount: float) -> float:
    """A `radblur` elmosási sugara képpontban — a KÉPSZÉLESSÉGHEZ kötve.

    `sugár = szélesség · 0,009 · (Amount + 1) + 0,001` (4.2.4 szerkezet,
    MÉRT együtthatóval). Ezért néz ki a Lágy fókusz ugyanúgy kicsi és nagy
    képen — **ellentétben a `glow`-val**, amelynek a sugara képpontban
    abszolút (4.2.5).
    """
    return width * RADBLUR_WIDTH_FRACTION * (float(amount) + 1.0) + RADBLUR_EPSILON


def apply_glow(image: np.ndarray, intensity: float, radius: float) -> np.ndarray:
    """Ragyogás (`glow`, `glow2`) — a KÖZÖS NATÍV elmosó magon (#668).

    ```
    elő = be² / 255                      ← multiply önmagával
    hom = iir_blur(elő, R, R)            ← a natív mag, R képpontban
    ki  = be + Intenzitás · (255 − be) · hom / 255      ← screen
    ```

    Mindhárom összetevő MÉRT:

    - a **sugár** a tárolt (logaritmikusan leképezett) paraméter képpontban,
      a `blur-meres` öt csúszkaállásán igazolva (4.2.5);
    - az **előgörbe** négyzetre emelés (ld. `glow_premultiply`);
    - a **súly** maga az Intenzitás — nincs illesztett szorzó.

    Ellenőrizve nyolc valódi Picasa-exporton (golden-kit `chart_color`,
    `photo01`, `photo04` × `glow1`/`glow2`, golden-kit3 `chart_ramp` ×
    `glow1`/`glow2`): átlagos ΔE 0,15…1,19, míg a korábbi Gauss-közelítésé
    1,74…4,25 volt. A sík foltok tónusa ±0,4 szinten belül egyezik.
    """
    validate_image(image)
    if intensity < 0:
        raise ValueError(f"A glow intenzitása nem lehet negatív: {intensity}")
    weight = min(float(intensity), 1.0)
    if weight == 0.0:
        return image.copy()
    span = radius if radius > 0 else GLOW_V1_RADIUS
    blurred = apply_picasa_blur(glow_premultiply(image), span, span)
    image_f = image.astype(np.float32)
    lift = (255.0 - image_f) * blurred.astype(np.float32) / np.float32(255.0)
    return _to_uint8(image_f + np.float32(weight) * lift)


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
    `chart_ramp`): átlagos ΔE 0,27…0,85, míg a korábbi közelítésé
    1,92…11,88 volt.
    """
    validate_image(image)
    radius = radblur_blur_radius(image.shape[1], amount)
    blurred = apply_picasa_blur(image, radius, radius)
    return apply_radial_mask(image, blurred, x, y, size, RADBLUR_SHARPNESS)


def apply_radsat(
    image: np.ndarray, x: float, y: float, radius: float, sharpness: float
) -> np.ndarray:
    """Radiális telítettség: az (x, y) körüli KÖR alakú zónán kívül a kép a
    Rec.601 luma felé telítetlenedik.

    A zóna GEOMETRIÁJA MÉRT tény (#859), nem KÖZELÍTÉS: a `radblur`-rel
    KÖZÖS natív függvény (`0x008f9cf0`) adja a sugarat, ezért itt is a
    `radblur`-rel MEGEGYEZŐ `native_radius_pixels`/`pixel_distance_grid`
    segédfüggvényeket hívjuk (`render/radial_mask.py`) — IZOTRÓP kör, a kép
    RÖVIDEBB oldalához méretezve, nem tengelyenkénti ellipszis.

    Az átmenet ALAKJA továbbra is KÖZELÍTÉS (nincs mért kimeneti adat a
    `radsat`-hoz): a zónán belül a kép változatlan, kívül a króma
    `1 − (r_px − sugár_px) / span_px` súllyal tűnik el — `span_px` a
    sugárral azonos egységben (a kép rövidebb oldalának fele) skálázva;
    `sharpness=1` éles határ, kisebb érték szélesebb átmenet.
    """
    validate_image(image)
    height, width = image.shape[:2]
    distance_px = pixel_distance_grid(height, width, x, y)
    radius_px = native_radius_pixels(width, height, radius)
    span_px = max(1.0 - sharpness, 1e-6) * (min(width, height) / 2.0)
    keep = np.clip(
        1.0 - (distance_px - radius_px) / span_px, 0.0, 1.0
    ).astype(np.float32)
    image_f = image.astype(np.float32)
    luma = (
        np.float32(0.299) * image_f[..., 0]
        + np.float32(0.587) * image_f[..., 1]
        + np.float32(0.114) * image_f[..., 2]
    )[..., np.newaxis]
    return _to_uint8(luma + keep[..., np.newaxis] * (image_f - luma))
