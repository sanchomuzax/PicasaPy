"""A `blur` („Elhomályosítás") szűrő — a kiolvasott natív lánc (#762, #3482, #3493).

## A lánc (`docs/specs/filters-decoded.md`, „⭐ A `blur` GÉPEZETE")

A natív mag (`0x0090cf60` → `0x0090cd90`) **élmegőrző, háromléptékű
simítás**, minden száma a binárisból jön:

1. **Fal-rács** (`0x0090cf60`): `(h+1)×(w+1)` darab 16 bites cella. A kép
   bal és jobb széle `0x5555` (vízszintes fal), a felső és az alsó `0xaaaa`
   (függőleges fal). A vízszintes fal az `x` és az `x+1` képpont között a
   `(y, x+1)` cellában, a függőleges az `y` és az `y+1` sor között a
   `(y+1, x)` cellában ül.
2. **Küszöb** (`0x0090cd90`): `K = CSONK(t² · 65536)`.
3. **Léptékenként** (`n = 1, 2, 4`):
   * **jelölés** (`0x0090ca10`): a MINDIG szomszédos pár fal, ha
     `ΔR² + ΔG² + ΔB² > K // n²`; a bit `n²·0x5555`, illetve `n²·0xaaaa`,
     16 bitre vágva;
   * **terjesztés** (`0x0090cbe0`, csak `n > 1`): a fal-bit sorok, illetve
     oszlopok mentén `n − 1` cellával mindkét irányba szélesedik, és a
     sor két szélső `n` cellája is megkapja;
   * **két simító menet** (`0x0090c6b0`): `(4·közép + 3·Σ4 szomszéd + 8) >> 4`
     csatornánként, a szomszéd `n` távolságra. A menet vízszintesen az
     `n²`, függőlegesen a `2n²` bitet nézi; falnál (és a képen kívül) a
     szomszéd helyére a KÖZÉP kerül.

## A mérés

A lánc a `PicasaPy merokit-2` három eredeti exportját (0,1 · 0,5 · 2,0) az
export kvantálótábláival újratömörítve **képpontra** adja vissza; a 762-es
hat exportot 0,000-val (0,1…1,4) és 0,010-zel (2,0). A korábban mért
„1,4-ig tétlen" viselkedés a kétszínű 762-es ÁBRA sajátja: annak egyetlen
fekete-fehér élén a fal addig áll, amíg `3·255² = 195 075 > K`, azaz
`t ≤ 1,725285`-ig. Valódi, zajos tartalmon a szűrő a csúszka tartományában
is simít.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image

#: A három lépték (`0x0090cd90`: `0x0090ce65` / `0x0090ceda` / `0x0090cf18`).
LEPTEKEK = (1, 2, 4)

#: A peremek fal-bitjei (`0x0090d07d`, `0x0090d0a0`).
_VIZSZINTES_PEREM = 0x5555
_FUGGOLEGES_PEREM = 0xAAAA


def kuszob(t: float) -> int:
    """`K = CSONK(t² · 65536)` — a lánc float32 paraméteréből (`0x0090cdf3`)."""
    t32 = float(np.float32(t))
    return int(t32 * t32 * 65536.0)


def _vizszintes_maszk(n: int) -> int:
    return (n * n * _VIZSZINTES_PEREM) & 0xFFFF


def _fuggoleges_maszk(n: int) -> int:
    return (n * n * _FUGGOLEGES_PEREM) & 0xFFFF


def _ures_racs(magassag: int, szelesseg: int) -> np.ndarray:
    racs = np.zeros((magassag + 1, szelesseg + 1), dtype=np.uint16)
    racs[:, 0] |= _VIZSZINTES_PEREM
    racs[:, szelesseg] |= _VIZSZINTES_PEREM
    racs[0, :] |= _FUGGOLEGES_PEREM
    racs[magassag, :] |= _FUGGOLEGES_PEREM
    return racs


def _falakkal(racs: np.ndarray, kep: np.ndarray, n: int, k: int) -> np.ndarray:
    """A jelölő (`0x0090ca10`): új rács a lépték falaival."""
    kuszob_n = k // (n * n)
    egesz = kep.astype(np.int32)
    ki = racs.copy()
    vizszintes = ((egesz[:, 1:] - egesz[:, :-1]) ** 2).sum(axis=2) > kuszob_n
    ki[:-1, 1:-1][vizszintes] |= _vizszintes_maszk(n)
    fuggoleges = ((egesz[1:, :] - egesz[:-1, :]) ** 2).sum(axis=2) > kuszob_n
    ki[1:-1, :-1][fuggoleges] |= _fuggoleges_maszk(n)
    return ki


def _szelesitve(jeloltek: np.ndarray, n: int) -> np.ndarray:
    """A terjesztő egy iránya (`0x0090cc3c`–`0x0090cc5a`): előre, majd hátra
    `n` cellás számlálóval — a jelölt `n − 1` cellával mindkét irányba
    szélesedik, és a sor két szélső `n` cellája is bitet kap."""
    ki = jeloltek.copy()
    for d in range(1, n):
        ki[..., d:] |= jeloltek[..., :-d]
        ki[..., :-d] |= jeloltek[..., d:]
    ki[..., :n] = True
    ki[..., -n:] = True
    return ki


def _terjesztve(racs: np.ndarray, n: int) -> np.ndarray:
    """A terjesztő (`0x0090cbe0`): a vízszintes maszk a sorok, a függőleges
    az oszlopok mentén."""
    ki = racs.copy()
    vm = _vizszintes_maszk(n)
    ki[_szelesitve((ki & vm) != 0, n)] |= vm
    fm = _fuggoleges_maszk(n)
    ki[_szelesitve(((ki & fm) != 0).T, n).T] |= fm
    return ki


def _simitva(kep: np.ndarray, racs: np.ndarray, n: int) -> np.ndarray:
    """Egy simító menet (`0x0090c6b0`).

    Szeletekkel dolgozik, nem indextömbökkel: exportnál teljes felbontáson
    fut, és a köztes tömbök így a kép méretének néhányszorosán maradnak. A
    legnagyobb összeg `16·255 + 8 = 4088`, tehát `uint16`-ban pontos.
    """
    magassag, szelesseg = kep.shape[:2]
    kozep = kep.astype(np.uint16)
    osszeg = 4 * kozep + 8
    vizszintes_bit, fuggoleges_bit = n * n, 2 * n * n
    racs_kep = racs[:magassag, :szelesseg]
    for irany in ("bal", "jobb", "fel", "le"):
        #: falnál és a képen kívül a szomszéd helyére a KÖZÉP kerül — ezért
        #: indul a szomszéd-tömb a közép másolataként
        szomszed = kozep.copy()
        if irany == "bal" and n < szelesseg:
            # (y, x−n), fal-cella (y, x−n+1)
            nyitott = (racs_kep[:, 1:szelesseg - n + 1] & vizszintes_bit) == 0
            szomszed[:, n:] = np.where(nyitott[..., None], kozep[:, :-n], kozep[:, n:])
        elif irany == "jobb" and n < szelesseg:
            # (y, x+n), fal-cella (y, x+n)
            nyitott = (racs[:magassag, n:szelesseg] & vizszintes_bit) == 0
            szomszed[:, :-n] = np.where(nyitott[..., None], kozep[:, n:], kozep[:, :-n])
        elif irany == "fel" and n < magassag:
            # (y−n, x), fal-cella (y−n+1, x)
            nyitott = (racs_kep[1:magassag - n + 1, :] & fuggoleges_bit) == 0
            szomszed[n:, :] = np.where(nyitott[..., None], kozep[:-n, :], kozep[n:, :])
        elif irany == "le" and n < magassag:
            # (y+n, x), fal-cella (y+n, x)
            nyitott = (racs[n:magassag, :szelesseg] & fuggoleges_bit) == 0
            szomszed[:-n, :] = np.where(nyitott[..., None], kozep[n:, :], kozep[:-n, :])
        osszeg += 3 * szomszed
    return (osszeg >> 4).astype(np.uint8)


def apply_blur(image: np.ndarray, threshold: float) -> np.ndarray:
    """A `blur` szűrő a natív lánc szerint (#3493).

    Args:
        image: `uint8`, HxWx3 (RGB) kép.
        threshold: a Küszöbérték a láncból (a `t` a `K = CSONK(t²·65536)`-ban).

    Returns:
        ÚJ kép — a bemenet változatlan marad.
    """
    validate_image(image)
    magassag, szelesseg = image.shape[:2]
    k = kuszob(threshold)
    racs = _ures_racs(magassag, szelesseg)
    kep = image.copy()
    for n in LEPTEKEK:
        racs = _falakkal(racs, kep, n, k)
        if n > 1:
            racs = _terjesztve(racs, n)
        kep = _simitva(kep, racs, n)
        kep = _simitva(kep, racs, n)
    return kep
