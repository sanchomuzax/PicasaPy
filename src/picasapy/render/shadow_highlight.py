"""Az `shadow` („Árnyék és kiemelés") natív modellje (#687).

A burkoló (`0x008f8ee0`) a három csúszkát a `0x0090d3e0` munkafüggvénynek
adja, ami **három elmosás-menetet** futtat (`0x009dd0d0` ×3 — a `glow`-val és
a sugaras családdal közös IIR-elmosó), majd a `0x0090d170` magot hívja. Ez a
mag **dekompilált**, betű szerint:

```c
L_src  = 2*R + 5*G + B + 4;          // a KÉPPONT saját világossága (×8)
L_blur = ugyanez az ELMOSOTT képen;

if (arnyek >= 1 && L_src <= 0x3ff && L_blur <= 0x3ff) {
    k = ((0x100000 - L_src*L_src) >> 10)
      * (((0x400 - L_blur) * arnyek) >> 8) >> 12;
    ki = c + ((k * c) >> 8);                       // SZORZÓ emelés
} else if (csucsfeny > 0 && L_src > 0x400 && L_blur > 0x400) {
    k = ((0x100000 - (0x800 - L_src)^2) >> 10)
      * (((L_blur - 0x400) * csucsfeny) >> 8) >> 12;
    ki = c - (((255 - c) * k) >> 8);               // a fehér felé nem mozdul
}
```

Két dolog, ami ebből fontos:

1. **A súly kétszeresen kapuzott.** Egy képpont csak akkor kap árnyék-emelést,
   ha a SAJÁT és a KÖRNYEZETE világossága is a felezőpont alatt van (és
   fordítva a csúcsfénynél). Ettől lesz helyi hatású, nem globális
   tónusgörbe — élek mentén nem fordul ki.
2. **A két végpont fix.** Az árnyék-ág szorzó (`c + k·c`), tehát a fekete
   fekete marad; a csúcsfény-ág a fehértől vett távolságot csökkenti, tehát a
   255 nem mozdul.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image
from picasapy.render.iir_blur import apply_picasa_blur

#: A két százalék-csúszka egészre skálázása. **MÉRT** (#685 mérőszettje): a
#: szorzót 64 és 1280 között végigpróbálva mindkét mérőesetben a **×256**
#: adta a legjobb illeszkedést, és nagy ráhagyással (a következő jelölt,
#: a ×384 már 5-ször pontatlanabb). A natív kódban a szorzás az x87-veremen
#: megy át, a dekompilátum nem őrizte meg.
_PERCENT_SCALE = 256.0

#: A natív mag a súlyokat ide vágja (`0x500`), mielőtt használná őket.
_MAX_WEIGHT = 0x500

#: Az elmosás menetszáma: a `0x0090d3e0` HÁROM `0x009dd0d0` hívást tesz.
_BLUR_PASSES = 3

#: A felezőpont a ×8-as világosság-skálán (`0x400`), illetve a skála teteje
#: (`0x800`) — a csúcsfény-ág parabolájának tükörpontja.
_MIDPOINT = 0x400
_TOP = 0x800

#: A parabola normálója: `1024²`.
_PARABOLA_FULL = 0x100000


def _luma8(image: np.ndarray) -> np.ndarray:
    """A mag saját világossága: `2R + 5G + B + 4` (a 0..255 skála ×8-a).

    **Nem azonos** sem a Derítőfényével (`(B + 2G + R) >> 2`), sem a
    `dir_sat`-éval (`(2R + 5G + B) >> 3`) — a Picasa szűrőnként más
    súlyozást használ, és itt a `>> 3` is elmarad.
    """
    values = image.astype(np.int64)
    return 2 * values[..., 0] + 5 * values[..., 1] + values[..., 2] + 4


def _weight(amount: int) -> int:
    """A csúszkából a natív egész súly, a mag saját vágásával."""
    return int(min(max(amount, 0), _MAX_WEIGHT))


def apply_shadow_highlight(
    image: np.ndarray, radius: float, shadow: float, highlight: float
) -> np.ndarray:
    """`shadow=1,Sugár,Árnyék%,Kiemelés%` — a natív `0x0090d3e0` mása.

    A #685 mérőszettjén (két nem-semleges csúszkaállás) az átlagos ΔE a
    valódi Picasa-kimenethez **0,58** és **0,59**, míg az érintetlen kép
    2,59 és 5,02 — vagyis a modell a JPEG-zaj szintjén illeszkedik.

    **Ami KÖZELÍTÉS: a Sugár csúszka leképezése.** A `filterdesc.xml` ezt a
    csúszkát logaritmikusnak jelöli (`<log>250.0</log>`), a `filters=` láncban
    viszont — a `glow` mért mintája szerint (#668/4.2.5: „az `R` paraméter
    képpontban az e-hajtási távolság") — a TÁROLT érték maga a sugár. Ezt
    használjuk. A mérés ezt **nem tudja eldönteni**: a szett két esete 0,5 és
    1,0 tárolt sugarat visel, és mindkettő ugyanott, egy ~1,6 képpontos
    közös optimum körül illeszkedik legjobban (ΔE 0,27 a 0,58 helyett) — a
    különbség a JPEG-zaj alatt van. Amit a mérés kizár, az a NAGY sugár: a
    16 képpontos és afölötti értékek 5–10-szer rosszabbul illeszkednek, tehát
    a `250^csúszka` olvasat biztosan téves. A kalibráció a #317-ben fut.
    """
    validate_image(image)
    shadow_weight = _weight(int(round(shadow * _PERCENT_SCALE)))
    highlight_weight = _weight(int(round(highlight * _PERCENT_SCALE)))
    if shadow_weight < 1 and highlight_weight < 1:
        return image.copy()

    blurred = image
    for _ in range(_BLUR_PASSES):
        blurred = apply_picasa_blur(blurred, radius, radius)

    values = image.astype(np.int64)
    source_luma = _luma8(image)
    blurred_luma = _luma8(blurred)
    result = values.copy()

    shadow_mask = (
        (shadow_weight >= 1)
        & (source_luma <= _MIDPOINT - 1)
        & (blurred_luma <= _MIDPOINT - 1)
    )
    if shadow_weight >= 1:
        gate = ((_PARABOLA_FULL - source_luma * source_luma) >> 10) * (
            ((_MIDPOINT - blurred_luma) * shadow_weight) >> 8
        ) >> 12
        lifted = values + ((gate[..., None] * values) >> 8)
        result = np.where(shadow_mask[..., None], lifted, result)

    highlight_mask = (
        ~shadow_mask
        & (highlight_weight > 0)
        & (source_luma > _MIDPOINT)
        & (blurred_luma > _MIDPOINT)
    )
    if highlight_weight > 0:
        distance = _TOP - source_luma
        gate = ((_PARABOLA_FULL - distance * distance) >> 10) * (
            ((blurred_luma - _MIDPOINT) * highlight_weight) >> 8
        ) >> 12
        pulled = values - (((255 - values) * gate[..., None]) >> 8)
        result = np.where(highlight_mask[..., None], pulled, result)

    return np.clip(result, 0, 255).astype(np.uint8)


__all__ = ["apply_shadow_highlight"]
