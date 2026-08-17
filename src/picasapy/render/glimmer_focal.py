"""Glimmer-effektek — festhető maszkos csővezetékek (#381): `PicnikTint`,
`ReanimatedEyeColor`.

**A festhető-maszk kérdés (#381, majd #688):** mindkét effekt a Picnik
`_mctr.mask` ecset-eszközével kijelölt RÉGIÓRA hat, és a PicasaPy-nak MÉG
NINCS ecset-eszköze. A #685 mérőszettje (valódi Picasa-export) viszont
kimutatta, hogy a kettő ALAPÁLLAPOTA nem ugyanaz:

* **`PicnikTint`** befestés nélkül is a TELJES KÉPRE fut — az exporton a
  Picasa maga is átszínezte az egész mérőképet (ΔE 36,9). Nálunk tehát
  marad a teljes képes hatás. **A kalibrációs eltérés a #884-ben lezárult:**
  a művelet a #878-ban megfejtett, fényesség-tartó `TintImageOperation`,
  és ugyanezen a golden páron ΔE 1,50 / SSIM 0,9991 (JPEG-zaj szint).
* **`ReanimatedEyeColor`** („Ghoul Eye") ÜRES maszkkal indul: a Picasa
  ugyanezen az exporton semmit nem változtatott (ΔE 0,18 = JPEG-zaj),
  miközben a mi modellünk ΔE 57,5-tel átfestette a képet (#688, P1).
  Ezért maszk nélkül AZONOSSÁGOT adunk vissza; a visszafejtett pixel-
  matematika megmarad, és `mask` átadásával fut le.

(Kontroll ugyanabból az exportból: a szintén ecsetelhető `Soften` is a
teljes képre futott a Picasában — vagyis nem „minden ecsetes effekt
tétlen", hanem kifejezetten a `ReanimatedEyeColor` indul üres maszkkal.)

Bemenet/kimenet: `uint8` RGB `numpy.ndarray` (H, W, 3). Minden függvény
TISZTA: új tömböt ad vissza, a bemenetet sosem mutálja.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import (
    alpha_blend,
    apply_blend_mode,
    fade_alpha,
    gaussian_blur_f,
    masked_blend,
    tint_luma_preserving,
    to_float,
    to_uint8,
)


def _solid_layer(image_f, color):
    layer = np.empty_like(image_f)
    layer[..., 0] = color[0]
    layer[..., 1] = color[1]
    layer[..., 2] = color[2]
    return layer


def apply_picnik_tint(image, color=(0x80, 0xCF, 0xFF), fade: float = 0.0):
    """`PicnikTint=1,Fade,szín` — FÉNYESSÉG-TARTÓ színezés (#884).

    A `filterdesc.xml` szerint az effekt egyetlen műveletből áll:

    ```xml
    <TintImageOperation Color="{_clrsw.color}"
                        BlendAlpha="{1-(_sldrFade.value/100)}"
                        Mask="{_mctr.mask}"/>
    ```

    A `TintImageOperation` a bemenet Rec.601 luminanciáját **bájtra
    megőrzi**, és csak a szín krómáját adja hozzá — a részletes képlet,
    a gamut-kezelés és a mérési bizonyíték a
    `glimmer_ops.tint_luma_preserving` docstringjében.

    **A korábbi modell egy TÖMÖR SZÍNRÉTEGET kevert a képre `normal`
    módban**, tehát `Fade = 0`-nál a kimenet egyetlen egyszínű felület lett,
    a kép rajzolata nélkül. A #685 mérőszettjén ez ΔE 33,45 / SSIM 0,63 volt;
    a fenti művelettel ugyanazon a golden páron (`picniktint__alap.jpg`,
    `tools/golden/compare_render.py` mércéjével) **ΔE 1,50 / SSIM 0,9991** —
    vagyis a JPEG-zaj szintjén.

    **Ecset-maszk nélkül: a TELJES KÉPRE fut** (ld. modul-docstring) — ezt a
    #685 exportja igazolja, ahol a Picasa maga is az egész mérőképet
    átszínezte.
    """
    validate_image(image)
    tinted = tint_luma_preserving(image, color)
    return to_uint8(alpha_blend(to_float(image), to_float(tinted), fade_alpha(fade)))


def _normalized_mask(mask, shape) -> np.ndarray:
    """Ecset-maszk `[0,1]` float32 (H, W) alakra hozva, alakellenőrzéssel."""
    weights = np.clip(np.asarray(mask, dtype=np.float32), 0.0, 1.0)
    if weights.shape != shape:
        raise ValueError(
            f"A maszk alakja {weights.shape}, a képé {shape} — meg kell egyezniük."
        )
    return weights


def apply_reanimated_eye_color(
    image, blur: float = 6.0, fade: float = 20.0, color=(0xC8, 0xFF, 0x00), mask=None
):
    """`ReanimatedEyeColor=1,Blur,Fade` — a BEFESTETT terület (jellemzően az
    íriszek) enyhén elmosott szorzó-színezése. A `color` a `filterdesc.xml`
    csúszkatáblájában NEM szerepel (a registerben csak `Blur`/`Fade` van) —
    a tényleges szín-választás feltehetően egy külön, ezen effekten kívüli
    mechanizmus (pl. a felhasználó szemszín-palettája), ami itt NEM ismert;
    `color` ezért egy dokumentáltan ÖNKÉNYES alapérték. `Blur` `[0..30]`
    (alap 6), `Fade` `[0..100]` (alap 20).

    **`mask=None` (nincs ecset-maszk) → AZONOSSÁG (#688).** Az effekt üres
    maszkkal indul: a #685 mérőszettjének Picasa-exportján a `min` és az
    `alap` állás egyaránt érintetlenül hagyta a képet (ΔE 0,18 = JPEG-zaj),
    miközben a korábbi, teljes képes modellünk ΔE 57,5 / 54,6 mértékben
    átfestette. A `mask` (H, W) `[0,1]` súlytérkép: ahol nulla, ott a
    kimenet bitre azonos a bemenettel.
    """
    validate_image(image)
    if mask is None:
        return image.copy()
    weights = _normalized_mask(mask, image.shape[:2])
    image_f = to_float(image)
    blurred = gaussian_blur_f(image_f, max(blur, 1e-6))
    layer = _solid_layer(blurred, color)
    tinted = apply_blend_mode(blurred, layer, "multiply", 1.0)
    faded = alpha_blend(image_f, tinted, fade_alpha(fade))
    return to_uint8(masked_blend(image_f, faded, weights))


__all__ = ["apply_picnik_tint", "apply_reanimated_eye_color"]
