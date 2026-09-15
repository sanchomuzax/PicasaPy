"""A #3092 ditherének kikapcsolása a GÖRBE-mérő próbák idejére.

## Miért kell

A `render/native_tone.apply_native_lut16` a #3092 óta **ditherel**: a natív
alkalmazó (`0x0090bc60`) képpontonként egy MT19937-mintát húz, és a görbe
helyi meredekségével arányos, ±delta/2 amplitúdójú zajt kever a kimenetbe.
Ettől nem sávosodik a széthúzott hisztogram (mérve: 117 → 0 üres rekesz).

Ez a termék helyes viselkedése — de a **görbe-mérő** próbáknak zaj. Azok a
LUT *alakját* mérik, egy szint-létra képen keresztül:

    apply_highlights(létra, 0.48)[0, 0, 0]  ==  100 / (1 − 0,48)  ± 1

Ditherrel ez az érték képpontonként ±1-et ugrál, tehát a mérés a zajt méri,
nem a görbét. A megoldás nem a tűrés tágítása (az elnyelné a valódi
modellhibát is), hanem a dither **kikapcsolása a mérés idejére**.

## Amit tudni kell a használatához

⚠️ A fogyasztó modulok `from … import apply_native_lut16` alakban vették át
a függvényt, ezért **annak a modulnak** az attribútumát kell cserélni, nem a
`native_tone`-ét — különben a próba némán a ditherelt utat mérné tovább.
A `dither_nelkul()` ezt mind a két helyen elvégzi.
"""

from __future__ import annotations

import functools
from contextlib import contextmanager

from picasapy.render import native_tone, tone


@contextmanager
def dither_nelkul():
    """A dither kikapcsolva — CSAK görbe-méréshez, nem a termék útja."""
    eredeti = native_tone.apply_native_lut16
    dithertelen = functools.partial(eredeti, dither=False)
    native_tone.apply_native_lut16 = dithertelen
    tone_eredeti = tone.apply_native_lut16
    tone.apply_native_lut16 = dithertelen
    try:
        yield
    finally:
        native_tone.apply_native_lut16 = eredeti
        tone.apply_native_lut16 = tone_eredeti
