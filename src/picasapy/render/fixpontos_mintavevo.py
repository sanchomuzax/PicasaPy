"""A natív forgató mintavevő (`0x009e7060`): 16.16 fixpont, 8 bites súlyú
bilineáris — a Polaroid forgatása (#3809) és a Kiegyenesítés (#3846) közös
magja, ezért semleges modulban él.

Soronként `U = fistp(u(x+0,5, y+0,5) · 65536) − 32767`, a lépés
`fistp(m0 · 65536)`; `ix = U >> 16`, `fx = (U >> 8) & 0xFF`. A súly 8 bites:
`lerp(a, b, f) = a + floor((b − a)·f/256)`, előbb vízszintesen. A perem egy
képpontos sávjában a kilógó szomszéd a szélső képpont; azon kívül a cél a
`border_color` marad. (`fistp` = páros felé kerekítés, mint az `np.rint`.)

A gyorsítás (#3846), bitre azonosan: a `lerp` ekvivalens alakja
`(a·(256 − f) + b·f) >> 8` (a `256·a` egész többszörös, tehát a floor nem
változik), ami nemnegatív és `uint16`-ban elfér; a `>> 8` a felső bájt. A
négy szomszédot egész koordinátás `cv2.remap` gyűjti, a peremet a
`BORDER_REPLICATE` clampeli; a keverést a `cv2.multiply`/`add` végzi.

A memória (#3846): a köztes tömbök a cél képpontszámával arányosak (a kép
~17-szerese), ezért a cél `_SAV_SOROK` soros sávokban készül. A sorok
függetlenek (`u0`, `v0` soronként számolódik), így a sávolás a kimenetet nem
változtatja, a csúcsmemória viszont egy sávnyi.

A bitre azonosságot a régi, numpy-s alakhoz mérve a
`tests/render/test_polaroid_irany_szin_3420.py` őrzi.
"""

from __future__ import annotations

import sys

from picasapy.lazy_cv2 import cv2
import numpy as np

#: A mintavevő 16.16 fixpontban lép; a forrás képpontközepét a `− 32767`
#: (`add edx, 0xffff8001`) teszi az egész koordinátára.
_FIX_EGY = 65536
_FIX_FEL = 32767

#: Ennyi célsor készül egyszerre — a csúcsmemória ennyi sornyi köztes tömb.
_SAV_SOROK = 256

#: A `cv2.remap` méretkorlátja (`SHRT_MAX`): a forrás és a cél is ez alatt.
_REMAP_HATAR = 32767

#: A `uint16` felső bájtja kis endiánon a páratlan bájt (`_lerp8`).
_KIS_ENDIAN = sys.byteorder == "little"


def fixpontos_bilinearis(
    image: np.ndarray, matrix: tuple[float, ...], cel_w: int, cel_h: int,
    border_color: tuple[int, int, int],
) -> np.ndarray:
    """A `matrix` (cél → forrás, képpontközepes koordinátában) szerinti
    `cel_w × cel_h`-s kép, `_SAV_SOROK` soros sávokban."""
    cel = np.empty((cel_h, cel_w, image.shape[2]), dtype=image.dtype)
    for elso in range(0, cel_h, _SAV_SOROK):
        utolso = min(cel_h, elso + _SAV_SOROK)
        cel[elso:utolso] = _sav(image, matrix, cel_w, elso, utolso, border_color)
    return cel


def _sav(
    image: np.ndarray, matrix: tuple[float, ...], cel_w: int, elso: int, utolso: int,
    border_color: tuple[int, int, int],
) -> np.ndarray:
    """A cél `[elso, utolso)` sorai."""
    src_h, src_w = image.shape[:2]
    ix, iy, fx, fy = _fixpontos_koordinatak(matrix, cel_w, elso, utolso)
    ervenyes = (ix >= -1) & (ix <= src_w - 1) & (iy >= -1) & (iy <= src_h - 1)
    a, b, c, d = _negy_szomszed(image, ix, iy)
    del ix, iy
    csatorna = image.shape[2]
    f = cv2.merge((fx,) * csatorna)
    fent = _lerp8(a, b, 256 - f, f)
    lent = _lerp8(c, d, 256 - f, f)
    f = cv2.merge((fy,) * csatorna)
    sav = _lerp8(fent, lent, 256 - f, f).reshape(utolso - elso, cel_w, csatorna)
    if not ervenyes.all():
        sav[~ervenyes] = np.array(border_color, dtype=image.dtype)
    return sav


def _fixpontos_koordinatak(
    matrix: tuple[float, ...], cel_w: int, elso: int, utolso: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """A `[elso, utolso)` sorok 16.16 koordinátái: egész rész (`ix`, `iy`) és
    8 bites tört (`fx`, `fy`, `uint16`). `int32`-ben számol, ha az
    értéktartomány belefér (a soron belüli lépés lineáris, tehát elég a két
    szélső oszlopot nézni)."""
    m0, m1, m2, m3, m4, m5 = matrix
    sor = np.arange(elso, utolso, dtype=np.float64) + 0.5
    u0 = np.rint((m0 * 0.5 + m1 * sor + m2) * _FIX_EGY).astype(np.int64) - _FIX_FEL
    v0 = np.rint((m3 * 0.5 + m4 * sor + m5) * _FIX_EGY).astype(np.int64) - _FIX_FEL
    du, dv = int(np.rint(m0 * _FIX_EGY)), int(np.rint(m3 * _FIX_EGY))
    oszlop = np.arange(cel_w, dtype=np.int64)
    szelek = [np.abs(u0), np.abs(u0 + (cel_w - 1) * du), np.abs(v0), np.abs(v0 + (cel_w - 1) * dv)]
    tipus = np.int32 if max(int(s.max()) for s in szelek) < 2**31 - 1 else np.int64
    u = u0.astype(tipus)[:, None] + (oszlop * du).astype(tipus)[None, :]
    v = v0.astype(tipus)[:, None] + (oszlop * dv).astype(tipus)[None, :]
    fx = ((u >> 8) & 0xFF).astype(np.uint16)
    fy = ((v >> 8) & 0xFF).astype(np.uint16)
    return u >> 16, v >> 16, fx, fy


def _negy_szomszed(
    image: np.ndarray, ix: np.ndarray, iy: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """A `(ix, iy)`, `(ix+1, iy)`, `(ix, iy+1)`, `(ix+1, iy+1)` képpontok,
    a forrás szélére clampelve. A `cv2.remap` csak `SHRT_MAX` alatti
    méretet fogad — e fölött (32 767 képpont) numpy-s gyűjtés."""
    src_h, src_w = image.shape[:2]
    if max(src_h, src_w, *ix.shape) < _REMAP_HATAR:
        terkep = np.empty(ix.shape + (2,), dtype=np.int16)
        terkep[..., 0] = np.clip(ix, -2, src_w)
        terkep[..., 1] = np.clip(iy, -2, src_h)

        def gyujt(dx: int, dy: int) -> np.ndarray:
            eltolt = cv2.add(terkep, (float(dx), float(dy), 0.0, 0.0)) if dx or dy else terkep
            return cv2.remap(
                image, eltolt, None, cv2.INTER_NEAREST, borderMode=cv2.BORDER_REPLICATE
            )

        return gyujt(0, 0), gyujt(1, 0), gyujt(0, 1), gyujt(1, 1)
    x0, x1 = np.clip(ix, 0, src_w - 1), np.clip(ix + 1, 0, src_w - 1)
    y0, y1 = np.clip(iy, 0, src_h - 1), np.clip(iy + 1, 0, src_h - 1)
    return image[y0, x0], image[y0, x1], image[y1, x0], image[y1, x1]


def _lerp8(p: np.ndarray, q: np.ndarray, g: np.ndarray, f: np.ndarray) -> np.ndarray:
    """`(p·g + q·f) >> 8` `uint8`-ban, `g + f = 256`: a 16 bites összeg
    (legfeljebb 255·256) felső bájtja."""
    osszeg = cv2.add(
        cv2.multiply(p, g, dtype=cv2.CV_16U), cv2.multiply(q, f, dtype=cv2.CV_16U)
    )
    if not _KIS_ENDIAN:
        return (osszeg >> 8).astype(np.uint8)
    return np.ascontiguousarray(osszeg.view(np.uint8)[..., 1::2])


__all__ = ["fixpontos_bilinearis"]
