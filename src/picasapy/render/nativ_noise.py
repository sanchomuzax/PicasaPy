"""A `NoiseImageOperation` natív zajrétege (#3736).

A spec: `docs/specs/filterdesc-registry.md`, „A `NoiseImageOperation`
véletlengenerátora" (#3747). A munkavégző (`0x00bce8c0`) MT19937-et futtat
szabványos twisttel és temperálással; egyetlen eltérése a magvetés
(`0x00aa28f0`):

    s[0] = randomSeed
    s[i] = 1664525 · (s[i−1] ^ (s[i−1] >> 30)) + i     (i = 1…623)
    index = 624   ⇒ az első húzás twistet vált ki

A `numpy` `MT19937` bitgenerátora ugyanezt a twistet és temperálást
számolja, a `random_raw` pedig a nyers 32 bites kimenetet adja — ezért az
állapotot a natív magvetéssel töltjük fel, és a húzásokat vektorosan
kérjük le.
"""

from __future__ import annotations

import numpy as np

#: A natív magvető szorzója (`0x00aa28f0`); a szabványos 1812433253.
_MAGVETO_SZORZO = 1664525

_ALLAPOT_MERET = 624
_SZO_MASZK = 0xFFFFFFFF

#: A `channelOptions` alapértéke: mindhárom színcsatorna zajos.
ALAP_CSATORNAK = 7


def _nativ_allapot(seed: int) -> np.ndarray:
    allapot = [int(seed) & _SZO_MASZK]
    for i in range(1, _ALLAPOT_MERET):
        elozo = allapot[-1]
        allapot.append((_MAGVETO_SZORZO * (elozo ^ (elozo >> 30)) + i) & _SZO_MASZK)
    return np.array(allapot, dtype=np.uint32)


def picasa_mt19937(seed: int, darab: int) -> np.ndarray:
    """A natív generátor első `darab` 32 bites húzása (`uint32`)."""
    generator = np.random.MT19937()
    generator.state = {
        "bit_generator": "MT19937",
        "state": {"key": _nativ_allapot(seed), "pos": _ALLAPOT_MERET},
    }
    return generator.random_raw(darab).astype(np.uint32)


def _vagott(ertek: float) -> int:
    return min(int(ertek), 255)


def noise_layer(
    height: int,
    width: int,
    seed: int,
    low: float,
    high: float,
    grayscale: bool,
    channel_options: int = ALAP_CSATORNAK,
) -> np.ndarray:
    """A natív zajréteg float32 RGB-ként, `[low, high]` egész értékekkel.

    Képpontonként egy húzás, sorfolytonosan a kép tetejétől. Színesen
    R/G/B = a húzás 2./1./0. bájtja `% r + low`, szürkén a teljes húzás
    `% r + low`, ahol `r = high − low + 1`, a `low`/`high` 255-re vágva. A
    `channel_options` 0./1./2. bitje tartja meg az R/G/B-t; a letiltott
    csatorna 0. (Az alfát a lánc nem használja, ezért itt nincs.)
    """
    also, felso = _vagott(low), _vagott(high)
    if also < 0 or felso < also:
        raise ValueError(f"A zaj tartománya hibás: low={low}, high={high}")
    r = felso - also + 1
    huzasok = picasa_mt19937(seed, height * width).reshape(height, width)
    if grayscale:
        sik = (huzasok % np.uint32(r)).astype(np.float32) + np.float32(also)
        reteg = np.repeat(sik[..., np.newaxis], 3, axis=2)
    else:
        # a húzás bájtjai kis-endián sorrendben: 0. = B, 1. = G, 2. = R
        bajtok = huzasok.astype("<u4").view(np.uint8).reshape(height, width, 4)
        ertek = (np.arange(256) % r + also).astype(np.float32)
        reteg = ertek[bajtok[..., 2::-1]]
    if channel_options & ALAP_CSATORNAK == ALAP_CSATORNAK:
        return reteg
    maszk = np.array([(channel_options >> bit) & 1 for bit in range(3)], dtype=np.float32)
    return reteg * maszk


__all__ = ["ALAP_CSATORNAK", "noise_layer", "picasa_mt19937"]
