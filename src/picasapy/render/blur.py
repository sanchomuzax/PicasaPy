"""A `blur` („Elhomályosítás") szűrő — küszöbvezérelt simítás (#1142).

## Mit tud a bináris

A natív mag (`0x0090cf60`, ld. `docs/specs/picasa-native-filter-workers.md`
4.2.3) **nem Gauss-elmosás**, hanem ÉLMEGŐRZŐ, többléptékű simítás:

- `(szélesség+1) × (magasság+1)` méretű, 2 bit/cella navigációs rács;
- három lépték (1, 2, 4); minden léptéken „falnak" jelöli azokat a
  szomszédpárokat, ahol `ΔR² + ΔG² + ΔB² > küszöb / n²`;
- a simítás csak a falakon BELÜL dolgozik.

Ezért van a szűrőnek „Küszöbérték" csúszkája (`filterdesc.xml`:
`Threshold`, `[-0,5; 0,5]`, alapérték `0,1`) — a csúszka NEM sugár.

## Mit mond a MÉRÉS (`PicasaPy merokit-2`, 2026-08-15-i eredeti export)

Ugyanaz a 960×640-es tesztábra, három lánccal; a számok a forrástól vett
átlagos abszolút eltérések, a JPEG-újratömörítés zajszintje **0,24**:

| lánc | eltérés | mit jelent |
|---|---|---|
| `blur=1;` (alapérték, 0,1) | 0,240 | TÉTLEN (a zajszint maga) |
| `blur=1,0.500000;` (csúszka teteje) | 0,562 | gyakorlatilag tétlen |
| `blur=1,2.000000;` (tartományon KÍVÜL) | 17,317 | TELJES elmosás |

A 2,0-s kimenetre a legjobb illesztés **σ = 4,00 szórású Gauss-elmosás**,
0,552 maradékkal — a σ optimuma éles (3,90 → 0,650; 4,10 → 0,692), és
minden más próbált mag rosszabb: a Picasa saját IIR-elmosója
(`iir_blur`, legjobb sugár) 3,49, a háromléptékű `[1,2,1]` dobozlánc
2,03, a legjobb háromdobozos lánc 0,72. A σ **nem függ a paramétertől** —
ez összefér a bináris képével: a küszöb azt dönti el, HOL simíthat,
nem azt, MEKKORA sugárral.

## Amit a mérés NEM dönt el — és ezért a modell határa

A küszöb → falképzés pontos leképezése nyitva marad: 0,5-nél a hatás a
zajszinten van, 2,0-nél már NINCS egyetlen fal sem (a tesztábra
fekete-fehér csíkjai is teljesen összemosódnak). A kettő közötti átmenet
alakjára nincs mérési pontunk, és találgatni tilos — egy szabadon
választott küszöbskála pontosan az a fajta paraméter, ami elnyeli a hibát.

Ezért a modell **a mért két tartományt** adja vissza, és a váltást a
csúszka tetejére (`0,5`) teszi: ez a LEGNAGYOBB mérten tétlen érték, és
egyben a `filterdesc.xml` felső korlátja, tehát **minden felületről
elérhető érték a mért, tétlen ágon marad**. A `0,5` és a `2,0` közötti
sávot a modell teljes elmosásként kezeli — ez a mérés által NEM fedett
rész, és ilyen érték valódi Picasa-írásból nem is keletkezik (a lánc
kézzel szerkesztett vagy idegen ini-ből jöhet).

A küszöbskála kimérése önálló kutatói kör tárgya (a #1142 „Ami nyitva
marad" pontja).
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.curves import validate_image

#: A `filterdesc.xml` Threshold csúszkájának felső vége. Eddig bezárólag a
#: mérés TÉTLEN kimenetet adott (#685: −0,5 / 0,1 / 0,5; #1142: 0,5).
BLUR_IDLE_THRESHOLD_MAX = 0.5

#: A küszöb fölötti, MÉRT elmosás szórása képpontban (`merokit-2`,
#: `halott_03`: `blur=1,2.000000;` → 0,552 maradék).
BLUR_SIGMA = 4.0


def apply_blur(image: np.ndarray, threshold: float) -> np.ndarray:
    """A `blur` szűrő a MÉRT modell szerint (#1142).

    Args:
        image: `uint8`, HxWx3 (RGB) kép.
        threshold: a Küszöbérték csúszka értéke a láncból.

    Returns:
        ÚJ kép — a bemenet változatlan marad. A csúszkatartományon belül
        (`threshold <= BLUR_IDLE_THRESHOLD_MAX`) a bemenet másolata,
        fölötte a `BLUR_SIGMA` szórású elmosás.
    """
    validate_image(image)
    if threshold <= BLUR_IDLE_THRESHOLD_MAX:
        return image.copy()
    return cv2.GaussianBlur(
        image, (0, 0), sigmaX=BLUR_SIGMA, sigmaY=BLUR_SIGMA,
        borderType=cv2.BORDER_REPLICATE,
    )
