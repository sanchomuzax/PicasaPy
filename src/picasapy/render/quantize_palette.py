"""A Poszterizálás (`QuantizePalette`) képfüggő palettája — a bináris útja (#3084).

A `glimmer::QuantizePaletteImageOperation` munkavégzője (`0x00bb5b60`) nem
csatornánként egyenletes rácsra kvantál, hanem a kép saját színeiből
`Steps − 1` elemű palettát épít. A lépések és a címek
(`docs/specs/filterdesc-registry.md`, a `QuantizePalette` szakaszok):

1. **Minta** — 50 × 50 képpont (`0x00bb5c44`), pontmintavétellel
   (`0x009e7420`): a mintaképpont KÖZEPE (`+0,5`) 16.16-os fixpontban
   visszavetítve, a lépték mindkét irányban `W / 50` (`0x00bb5bd0`). A
   képen kívül eső mintaképpont 0, azaz fekete (`0x009a8d80`).
2. **Oktree** — a minta minden képpontja, oszlopfolytonosan
   (`0x00bb5d3b`), a `0x00bcb8e0` beszúróba; a hasítás lusta, a mélységet a
   `Depth` (4) keretezi.
3. **Redukció** — `Steps − 1` levélre (`Steps == 2` esetén 2-re,
   `0x00bb5da8`), `floor(N / hátralévő)` kvótával, rögzített
   gyerekbejárási sorrendben (`0x00cf0c28`).
4. **3-3-2 keresőtábla** — a 256 rekesz színére (`R = r3·32`,
   `G = g3·32`, `B = b2·64`) a fa bit-alapú leszállással válaszol
   (`0x00bcb9f0`); a képpont a rekesze színét kapja.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.curves import validate_image

#: `0x00bb5c44  mov eax, 0x32` — a minta oldalhossza
MINTA_OLDAL = 50

#: a `filterdesc.xml` szállított `Depth`-je (1255. sor)
MELYSEG = 4

#: `0x00cf0c28` — a redukáló rögzített gyerekbejárási sorrendje
BEJARAS = (3, 1, 2, 5, 4, 6, 0, 7)

#: `0x00cf0c48` — hiányzó gyerek helyett a keresés ezekben a testvérekben
#: folytatja, sorban (csak ha a csomópont `+8` jelzője 0: a gyökérnél,
#: `Steps == 2` esetén; `0x00bb5dbe`)
HELYETTESITO = (
    (1, 2, 4, 3, 5, 6, 7),
    (2, 3, 5, 0, 7, 5, 4),
    (3, 1, 6, 0, 7, 4, 5),
    (2, 1, 5, 0, 7, 4, 6),
    (1, 5, 6, 0, 7, 2, 3),
    (4, 1, 3, 0, 7, 6, 2),
    (2, 4, 3, 7, 0, 5, 1),
    (6, 5, 3, 4, 2, 1, 0),
)

_FIX = 65536.0


class _Csomopont:
    """A 32 bájtos csomópont: gyerekek, darab, jelző, szint, keret, összegek."""

    __slots__ = ("szint", "keret", "gyerekek", "osszeg", "darab", "sajat", "helyettesit")

    def __init__(self, szint: int, keret: int, helyettesit: bool = False):
        self.szint = szint
        self.keret = keret
        self.gyerekek: list[_Csomopont | None] | None = None
        self.osszeg = [0, 0, 0]
        self.darab = 0
        #: a lusta hasítás miatt az első szín a csomópontban vár
        self.sajat: tuple[int, int, int] | None = None
        #: a `+8` jelző NEGÁLTJA — a gyerekeké mindig 1 (`0x00bcb9b8`)
        self.helyettesit = helyettesit


def _index(szin: tuple[int, int, int], szint: int) -> int:
    k = 7 - szint
    r, g, b = szin
    return ((r >> k) & 1) << 2 | ((g >> k) & 1) << 1 | ((b >> k) & 1)


def _beszur(csp: _Csomopont, szin: tuple[int, int, int]) -> None:
    """`0x00bcb8e0` — a kapu: `[esi+0x10] <= 1` ⇒ nem száll tovább."""
    for i in range(3):
        csp.osszeg[i] += szin[i]
    csp.darab += 1
    if csp.keret <= 1:
        return
    if csp.darab == 1:
        csp.sajat = szin
        return
    if csp.sajat is not None:
        elso, csp.sajat = csp.sajat, None
        _leszall(csp, elso)
    _leszall(csp, szin)


def _leszall(csp: _Csomopont, szin: tuple[int, int, int]) -> None:
    """`0x00bcb950` — a gyerek szintje +1, a kerete −1."""
    if csp.gyerekek is None:
        csp.gyerekek = [None] * 8
    i = _index(szin, csp.szint)
    if csp.gyerekek[i] is None:
        csp.gyerekek[i] = _Csomopont(csp.szint + 1, csp.keret - 1)
    _beszur(csp.gyerekek[i], szin)


def _osszeolvaszt(csp: _Csomopont) -> None:
    """`0x00bcb880` — a csomópont levél lesz; az összeg és a darab marad."""
    csp.gyerekek = None
    csp.sajat = None


def _redukal(csp: _Csomopont, n: int) -> None:
    """`0x00bcb6f0` — `N == 1` ⇒ azonnal levél; különben a gyerekek a
    bejárási sorrendben `floor(N / hátralévő)` kvótát kapnak, a 0 kvótájú
    gyerek a szülőbe olvad, és `N` nem csökken."""
    if n <= 1:
        _osszeolvaszt(csp)
        return
    if csp.gyerekek is None:
        return
    letezok = [i for i in BEJARAS if csp.gyerekek[i] is not None]
    hatra, maradek = len(letezok), n
    for i in letezok:
        kvota = maradek // hatra
        if kvota == 0:
            csp.gyerekek[i] = None
        else:
            _redukal(csp.gyerekek[i], kvota)
            maradek -= kvota
        hatra -= 1


def _atlag(csp: _Csomopont) -> tuple[int, int, int]:
    """`floor(float32(összeg / darab))` (`0x00bcbaa0`). A csatornaösszeg
    legfeljebb 2500 · 255, tehát a float32-kerekítés sosem lép át egészet:
    az egész osztás ugyanazt adja."""
    if csp.darab == 0:
        return (0, 0, 0)
    return tuple(v // csp.darab for v in csp.osszeg)  # type: ignore[return-value]


def keres(csp: _Csomopont, szin: tuple[int, int, int]) -> tuple[int, int, int]:
    """`0x00bcb9f0` — bit-alapú leszállás, nem legközelebbi-szomszéd."""
    while True:
        if csp.sajat is not None:
            return csp.sajat
        if csp.gyerekek is None:
            return _atlag(csp)
        i = _index(szin, csp.szint)
        gyerek = csp.gyerekek[i]
        if gyerek is None and csp.helyettesit:
            gyerek = next(
                (csp.gyerekek[j] for j in HELYETTESITO[i] if csp.gyerekek[j] is not None),
                None,
            )
        if gyerek is None:
            return _atlag(csp)
        csp = gyerek


def mintakep(kep: np.ndarray) -> np.ndarray:
    """Az 50 × 50-es minta (RGB, uint8) — ld. a modul 1. pontját."""
    validate_image(kep)
    magassag, szelesseg = kep.shape[:2]
    #: a mátrix float32 (`0x00bb5c11 fstp dword`), és a visszavetített
    #: koordináta is float32-be kerül, mielőtt 65536-tal szoroz (`0x009e74c3`)
    leptek = np.float32(szelesseg / float(MINTA_OLDAL))
    lepes = int(np.floor(float(leptek) * _FIX))
    kezdo = int(np.floor(float(np.float32(0.5 * float(leptek))) * _FIX))
    oszlopok = (kezdo + np.arange(MINTA_OLDAL, dtype=np.int64) * lepes) >> 16
    sor_koord = ((np.arange(MINTA_OLDAL) + 0.5) * float(leptek)).astype(np.float32)
    sorok = np.floor(sor_koord.astype(np.float64) * _FIX).astype(np.int64) >> 16
    minta = np.zeros((MINTA_OLDAL, MINTA_OLDAL, 3), dtype=np.uint8)
    jo_sor = sorok < magassag
    jo_oszlop = oszlopok < szelesseg
    minta[np.ix_(jo_sor, jo_oszlop)] = kep[np.ix_(sorok[jo_sor], oszlopok[jo_oszlop])]
    return minta


def oktree_epit(minta: np.ndarray, steps: int, melyseg: int = MELYSEG) -> _Csomopont:
    """A redukált fa — ld. a modul 2–3. pontját."""
    steps = int(steps)
    gyoker = _Csomopont(0, melyseg, helyettesit=steps == 2)
    for keppont in minta.transpose(1, 0, 2).reshape(-1, 3):
        _beszur(gyoker, (int(keppont[0]), int(keppont[1]), int(keppont[2])))
    _redukal(gyoker, 2 if steps == 2 else steps - 1)
    return gyoker


def paletta_lut(fa: _Csomopont) -> np.ndarray:
    """A 256 rekeszes 3-3-2 keresőtábla, `(256, 3)` uint8 RGB."""
    lut = np.zeros((256, 3), dtype=np.uint8)
    for c in range(256):
        lut[c] = keres(fa, (c & 0xE0, (c & 0x1C) << 3, (c & 3) << 6))
    return lut


def kvantal(kep: np.ndarray, steps: float) -> np.ndarray:
    """A kép a saját palettájára kvantálva (RGB, uint8, új tömb)."""
    validate_image(kep)
    lepesszam = max(2, int(round(steps)))
    lut = paletta_lut(oktree_epit(mintakep(kep), lepesszam))
    r = kep[..., 0].astype(np.int32)
    g = kep[..., 1].astype(np.int32)
    b = kep[..., 2].astype(np.int32)
    return lut[(r & 0xE0) | ((g >> 3) & 0x1C) | (b >> 6)]


__all__ = ["kvantal", "mintakep", "oktree_epit", "paletta_lut", "keres"]
