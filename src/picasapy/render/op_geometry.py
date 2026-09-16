"""#3229 1. lépés — MINDEN op deklarálja a saját forrás → kimenet leképezését.

## Miért kell, és mit MÉRTÜNK

Az eredeti Picasa **nem rendezi át** a láncot. A `CGenericFilter` vtáblájának
(`0x00cd184c`) két szomszédos rekesze mutatja, hogyan éri meg neki az eredeti
sorrendben renderelni:

| rekesz | függvény | mit tesz |
|---|---|---|
| `+0x80` | `FUN_008f6e40` | RENDER (a `[this+0xc]` visszahívása), majd gyorsítótár-érvénytelenítés |
| `+0x84` | `FUN_008f6e80` | a KOORDINÁTA-LEKÉPEZÉS átadása: 9 float (3×3 mátrix) + jelző a `[this+0x6c]`-be, és az **inverz** a `[this+0x94]`-be (`FUN_00a4a140` = determináns, nullára ellenőrizve) |

⇒ minden szűrő eltárolja az odaérkező leképezést ÉS annak inverzét; a
szerkesztő (`FUN_006ad860`) a lánc minden tagján sorban meghívja.

Nálunk ma az `apply_filters` a vágást és a kereteket a lánc VÉGÉRE halasztja
(#330). Ez egy híváson belül konzisztens, de az élő előnézet a lánc-prefix
gyorsítótár miatt kettévágja a láncot — és a két út MÉRHETŐEN eltér (#3169:
`crop64;Vignette` láncon 18,20 szint a 0–255 skálán).

## Mit ad ez a modul — és mit NEM

Ez a **deklaráció**: minden op megadja, hova kerül a forrása a kimenetében, és
mekkora lesz a kimenet. A lánc futtatása VÁLTOZATLAN; ezt a modult a jegy
2. lépése kapcsolja be.

* a színműveletek (a `chain._HANDLERS` többsége) **egység**-leképezést adnak —
  sem a képet, sem a méretét nem mozdítják;
* a **keret-effektek** a `chain_geometry` mért táblájából jönnek (#3166: hat
  szűrő, képpont-szinten mérve, nem képlet-feltevésből);
* a **`crop64`** eltolás + méretváltás (a rect64 relatív koordinátái a saját
  bemenetére, az `ops._rect_to_pixels` kerekítésével);
* a **`tilt`** méret-tartó forgatás a kép közepe körül (`ops.apply_tilt`).

⛔ Amit szándékosan NEM tesz: nem mondja meg, egy szűrő KÉPPONTRA mit rajzol. A
leképezés a kép HELYÉRŐL szól, nem a tartalmáról. Aki képpont-egyezést keres, a
`tests/render/test_keret_geometria_3166.py` mintáját kövesse (renderelt jelölő).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from picasapy.ini.filters import FilterOp
from picasapy.ini.rect64 import decode_rect64
from picasapy.render.chain_geometry import (
    AZONOSSAG,
    Matrix,
    _GEOMETRIA,
    _szorzat,
)


class SzingularisLekepezes(ValueError):
    """A leképezés nem invertálható (a determinánsa nulla).

    Az eredeti ugyanígy ellenőriz: a `FUN_00a4a140` kiszámolja a determinánst,
    és nullára megáll — tehát ez nem a mi óvatosságunk, hanem a mért viselkedés.
    """


@dataclass(frozen=True)
class OpGeometria:
    """Egy op (vagy egy egész lánc) forrás → kimenet leképezése."""

    #: A kimenet mérete képpontban.
    szelesseg: int
    magassag: int
    #: Forrás → kimenet affin leképezés (2×3).
    matrix: Matrix

    @property
    def valtoztat(self) -> bool:
        """Elmozdítja-e egyáltalán a forrást a kimenetben?"""
        return self.matrix != AZONOSSAG

    @property
    def inverz(self) -> Matrix:
        """Kimenet → forrás. A `+0x84` rekesz ezt is eltárolja."""
        return invertal(self.matrix)


def invertal(m: Matrix) -> Matrix:
    """Egy 2×3-as affin leképezés inverze.

    A 2×2-es rész inverze, majd az eltolás visszaszámolása. Nulla
    determinánsnál `SzingularisLekepezes` — ld. az osztály docstringjét.
    """
    (a, b, c), (d, e, f) = m
    det = a * e - b * d
    if det == 0.0:
        raise SzingularisLekepezes(f"A leképezés nem invertálható: {m!r}")
    ia, ib = e / det, -b / det
    id_, ie = -d / det, a / det
    return ((ia, ib, -(ia * c + ib * f)), (id_, ie, -(id_ * c + ie * f)))


def _eltolas_es_meret(bal: int, fent: int) -> Matrix:
    """A vágás leképezése: a forrás (bal, fent) pontja a kimenet origója."""
    return ((1.0, 0.0, float(-bal)), (0.0, 1.0, float(-fent)))


def _crop_geometria(
    szelesseg: int, magassag: int, op: FilterOp
) -> tuple[int, int, Matrix]:
    """A `crop64` leképezése — a SAJÁT bemenetére vonatkozó relatív téglalap.

    A kerekítés az `ops._rect_to_pixels`-é, hogy a megjósolt méret a valóban
    renderelt kimenettel EGYEZZEN (ezt a jegy őre méri).
    """
    if len(op.params) < 2:
        raise ValueError(f"A crop64 szűrőnek rect64 paraméter kell: {op}")
    rect = decode_rect64(op.params[1])
    bal = round(rect.left * szelesseg)
    fent = round(rect.top * magassag)
    jobb = round(rect.right * szelesseg)
    lent = round(rect.bottom * magassag)
    if jobb <= bal or lent <= fent:
        raise ValueError(f"Üres kivágás: {rect}")
    return jobb - bal, lent - fent, _eltolas_es_meret(bal, fent)


def _tilt_geometria(
    szelesseg: int, magassag: int, op: FilterOp
) -> tuple[int, int, Matrix]:
    """A `tilt` MÉRET-TARTÓ forgatás a kép közepe körül (`ops.apply_tilt`).

    A `chain._apply_tilt_op` átalakítását tükrözzük, KONSTANST NEM DUPLIKÁLVA:
    a szög `paraméter · _TILT_RADIANS_PER_UNIT`, és ha a skála 0 vagy hiányzik
    (a Picasa 3.x jellemzően `0.000000`-t ír, #73), akkor a KITÖLTŐ skála
    (`tilt_cover_scale`) — különben a megjósolt leképezés más lenne, mint amit
    a lánc tényleg renderel.
    """
    from picasapy.render.chain import _TILT_RADIANS_PER_UNIT, tilt_cover_scale

    params = op.float_params()
    if not params:
        raise ValueError(f"A tilt szűrőnek legalább egy paramétere kell: {op}")
    szog = params[0] * _TILT_RADIANS_PER_UNIT
    if len(params) >= 2 and params[1] > 0:
        skala = params[1]
    else:
        skala = tilt_cover_scale(szelesseg, magassag, szog)
    kozep_x, kozep_y = szelesseg / 2.0, magassag / 2.0
    alfa = math.cos(szog) * skala
    beta = math.sin(szog) * skala
    matrix: Matrix = (
        (alfa, beta, (1.0 - alfa) * kozep_x - beta * kozep_y),
        (-beta, alfa, beta * kozep_x + (1.0 - alfa) * kozep_y),
    )
    return szelesseg, magassag, matrix


#: Kulcs → geometria-függvény. Ami NINCS benne, az egység-leképezést ad — és
#: ezt a jegy őre a `chain._HANDLERS` MINDEN kulcsára ellenőrzi, tehát egy
#: jövőben bekötött, méretet változtató szűrő nem csúszhat át némán.
_OP_GEOMETRIA: dict[str, object] = {
    **_GEOMETRIA,
    "crop64": _crop_geometria,
    "tilt": _tilt_geometria,
}


def op_geometria(op: FilterOp, szelesseg: int, magassag: int) -> OpGeometria:
    """EGY op leképezése a `szelesseg` × `magassag`-es bemenetére."""
    geo = _OP_GEOMETRIA.get(op.name.casefold())
    if geo is None:
        return OpGeometria(int(szelesseg), int(magassag), AZONOSSAG)
    sz, ma, matrix = geo(int(szelesseg), int(magassag), op)  # type: ignore[operator]
    return OpGeometria(int(sz), int(ma), matrix)


def lanc_geometria(
    ops: tuple[FilterOp, ...], szelesseg: int, magassag: int
) -> OpGeometria:
    """A teljes lánc leképezése, az ops EREDETI sorrendjében.

    ⚠️ Ez az, amiben a `chain_geometry.keret_geometria`-tól KÜLÖNBÖZIK: az a
    keretek halasztott sorrendjét tükrözi (a mai `apply_filters`-t), ez pedig a
    mért, eredeti sorrendet. Amíg a 2. lépés nincs bekötve, a kettő ugyanazt
    adja minden olyan láncra, amiben nincs keret ELŐTT álló vágás — a jegy őre
    egy ilyen láncot ki is mér.
    """
    m: Matrix = AZONOSSAG
    sz, ma = int(szelesseg), int(magassag)
    for op in ops:
        lepes = op_geometria(op, sz, ma)
        sz, ma = lepes.szelesseg, lepes.magassag
        m = _szorzat(lepes.matrix, m)
    return OpGeometria(sz, ma, m)
