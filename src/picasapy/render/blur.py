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

## A köztes sáv — a tulajdonos exportja (#762, 2026-09-21)

Hat bájtra azonos forrás (800×512), `EXIF Software = Picasa` exportok:

| lánc | az export a forráshoz képest |
|---|---|
| `blur=1,0.100000;` · `0.5` · `0.8` · `1.1` · `1.4` | képpontra AZONOS (átlag \|Δ\| = 0,000) |
| `blur=1,2.000000;` | teljes elsimítás (Laplace-szórás 162,6 → 0,4) |

A 2,0-s exporttól a `BLUR_SIGMA` = 4-es elmosásunk átlagosan 0,026-tal tér
el — a fenti illesztés tehát egy független ábrán is áll.

## Amit a mérés NEM dönt el — és ezért a modell határa

A váltás 1,4 és 2,0 KÖZÖTT van; a pontos helyére nincs mérési pontunk, és
találgatni tilos. A modell ezért a váltást a LEGNAGYOBB mérten tétlen
értékre (1,4) teszi. Az 1,4 és 2,0 közötti sáv a mérés által NEM fedett
rész; ilyen érték a felületről (`[-0,5; 0,5]`) nem is keletkezik, csak kézzel
szerkesztett vagy idegen ini-ből. A küszöb pontos helyét a bináris
(`0x0090cf60`) falképző feltételéből kell kiolvasni (#762).
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.curves import validate_image

#: A legnagyobb MÉRTEN tétlen küszöb. Eddig bezárólag a Picasa a forrást
#: adta vissza (#685: −0,5 / 0,1 / 0,5; #1142: 0,5; #762: 0,8 / 1,1 / 1,4 —
#: képpontra azonos exportok). 2,0-nél már teljes elmosás.
BLUR_IDLE_THRESHOLD_MAX = 1.4

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
