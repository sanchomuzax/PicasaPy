"""A keret-effektek FORRÁS → KIMENET leképezése (#3166, a #819 `resizes` ága).

## Mire való

A szerkesztő átfedő rétegei — a vágás-téglalap (`CropOverlay.qml`) és az
arckeretek (`FacesOverlay.qml`) — a KIRAJZOLT kép téglalapjára
horgonyozódnak, és relatív `[0..1]` koordinátákkal dolgoznak. Amint a lánc
keret-effektet tartalmaz, a kirajzolt kép már a **keretezett** kimenet:
ugyanaz a relatív koordináta más képpontra mutat. Ez a modul adja meg, hol
van a forráskép a kimenetben — eltolással, átméretezéssel és forgatással
együtt, egyetlen 2×3-as affin mátrixban.

## ⛔ Miért NEM elég az `(kimenet − forrás) / 2` képlet

Mérve (2026-09-15, 800 × 600-as forrás):

| szűrő | kimenet | a leképezés jellege |
|---|---|---|
| `Border` | 850 × 650 | szimmetrikus eltolás |
| `MuseumMatte` | 930 × 730 | szimmetrikus eltolás |
| `DropShadow` | 1048 × 848 | eltolás — az árnyék szöge miatt a vászon NEM a képre centrál |
| `Polaroid` | 770 × 892 | négyzetes vágás + aszimmetrikus keret + **forgatás** |
| `Cinemascope` | 800 × 589 | **vágás** és függőleges **átméretezés** — a kimenet KISEBB |
| `RoundedEdges` | 800 × 600 | **nem változtat** (a `resizes` jelzője mégis igaz) |

A `Cinemascope` tehát nem növel, hanem vág, a `RoundedEdges` pedig a
jelzője ellenére változatlanul hagy — a szimmetria-feltevés mindkettőre és
a `Polaroid`-ra is hamis.

## A leképezés a renderelő aritmetikáját TÜKRÖZI

Minden itteni képlet a `glimmer_frames` / `glimmer_frame_ops` /
`glimmer_creative` megfelelő sorát követi (kerekítéssel együtt). Ez
sodródhat: ezért a `tests/render/test_keret_geometria_3166.py` egyik próbája
sem képletet hasonlít képlethez, hanem **jelölő-képpontot mér a valódi
renderelt kimenetben**.

## Hatókör — kimondva

Ez a modul **csak a keret-effektekkel** számol (a regiszter `resizes`
jelzőjű, `_HANDLERS`-ben bekötött szűrői). A `crop64` és a `tilt` a lánc
ELEJÉN fut, és a mentett arc-/vágás-koordináták eleve a vágott képre
vonatkoznak — azokat nem ez a modul kezeli.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from picasapy.ini.filters import FilterOp
from picasapy.render.glimmer_frame_ops import thickness_px

#: 2×3-as affin mátrix: `((a, b, c), (d, e, f))`, azaz
#: `x' = a·x + b·y + c`, `y' = d·x + e·y + f`.
Matrix = tuple[tuple[float, float, float], tuple[float, float, float]]

AZONOSSAG: Matrix = ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0))

#: A `Polaroid` rögzített árnyék-paraméterei (`glimmer_frames`).
_POLAROID_SHADOW_BLUR_PX = 8
_POLAROID_SHADOW_DISTANCE_PX = 3


@dataclass(frozen=True)
class KeretGeometria:
    """A forráskép elhelyezkedése a renderelt kimenetben."""

    #: A kimenet mérete képpontban.
    szelesseg: int
    magassag: int
    #: Forrás → kimenet affin leképezés.
    matrix: Matrix

    @property
    def valtoztat(self) -> bool:
        """Elmozdítja-e egyáltalán a lánc a forrást a kimenetben?"""
        return self.matrix != AZONOSSAG


def _szorzat(kulso: Matrix, belso: Matrix) -> Matrix:
    """`kulso ∘ belso` — előbb a `belso` fut."""
    (a, b, c), (d, e, f) = kulso
    (g, h, i), (j, k, m) = belso
    return (
        (a * g + b * j, a * h + b * k, a * i + b * m + c),
        (d * g + e * j, d * h + e * k, d * i + e * m + f),
    )


def _eltolas(dx: float, dy: float) -> Matrix:
    return ((1.0, 0.0, float(dx)), (0.0, 1.0, float(dy)))


def _forgatas(kozep_x: float, kozep_y: float, szog_fok: float) -> Matrix:
    """A `cv2.getRotationMatrix2D(center, angle, 1.0)` képlete.

    Az OpenCV pozitív szögnél az óramutatóval ELLENTÉTESEN forgat a
    képkoordinátákban; a mátrixa pontosan ez."""
    alfa = math.cos(math.radians(szog_fok))
    beta = math.sin(math.radians(szog_fok))
    return (
        (alfa, beta, (1.0 - alfa) * kozep_x - beta * kozep_y),
        (-beta, alfa, beta * kozep_x + (1.0 - alfa) * kozep_y),
    )


def _szam(op: FilterOp, index: int, alap: float) -> float:
    """A `chain_glimmer_handlers._float_at` viselkedése."""
    try:
        return float(op.params[index])
    except (IndexError, TypeError, ValueError):
        return alap


def _logikai(op: FilterOp, index: int, alap: bool) -> bool:
    try:
        return bool(int(float(op.params[index])))
    except (IndexError, TypeError, ValueError):
        return alap


def _px(ertek: float) -> int:
    """`add_ring` / `add_caption` kerekítése."""
    return max(0, int(round(ertek)))


# --- szűrőnkénti geometria ---------------------------------------------------


def _border(w: int, h: int, op: FilterOp) -> tuple[int, int, Matrix]:
    kulso = _px(_szam(op, 1, 20.0))
    belso = _px(_szam(op, 2, 5.0))
    felirat = _px(_szam(op, 6, 0.0))
    keret = kulso + belso
    return w + 2 * keret, h + 2 * keret + felirat, _eltolas(keret, keret)


def _rounded_edges(w: int, h: int, op: FilterOp) -> tuple[int, int, Matrix]:
    # `apply_rounded_edges` nulla vastagságú gyűrűkkel hív `draw_border`-t:
    # csak a sarkokat kerekíti, a méret NEM változik (mérve).
    return w, h, AZONOSSAG


def _museum_matte(w: int, h: int, op: FilterOp) -> tuple[int, int, Matrix]:
    kulso = _px(_szam(op, 1, 25.0))
    belso = _px(_szam(op, 2, 40.0))
    keret = kulso + belso
    return w + 2 * keret, h + 2 * keret, _eltolas(keret, keret)


def _drop_shadow(w: int, h: int, op: FilterOp) -> tuple[int, int, Matrix]:
    tavolsag = int(round(_szam(op, 1, 4.0)))
    elmosas = max(1, thickness_px(h, w, _szam(op, 3, 10.0)))
    margo = elmosas * 2 + abs(tavolsag)
    return w + 2 * margo, h + 2 * margo, _eltolas(margo, margo)


def _polaroid(w: int, h: int, op: FilterOp) -> tuple[int, int, Matrix]:
    szog = _szam(op, 1, 5.0)

    # 1. négyzetes középvágás
    oldal = min(h, w)
    vagas_x = (w - oldal) // 2
    vagas_y = (h - oldal) // 2
    m = _eltolas(-vagas_x, -vagas_y)
    sz, ma = oldal, oldal

    # 2. aszimmetrikus keret
    oldalt = round(oldal * 0.0645)
    fent = round(oldal * 0.0968)
    lent = round(oldal * 0.258)
    m = _szorzat(_eltolas(oldalt, fent), m)
    sz, ma = sz + 2 * oldalt, ma + fent + lent

    # 3. vetett árnyék (rögzített pixel-margóval)
    margo = _POLAROID_SHADOW_BLUR_PX + _POLAROID_SHADOW_DISTANCE_PX
    m = _szorzat(_eltolas(margo, margo), m)
    sz, ma = sz + 2 * margo, ma + 2 * margo

    # 4. `rotate_with_pad`: előbb a bővített vászon közepére, majd forgatás
    radian = math.radians(szog)
    cos_a, sin_a = abs(math.cos(radian)), abs(math.sin(radian))
    uj_sz = int(math.floor(sz * cos_a + ma * sin_a))
    uj_ma = int(math.floor(sz * sin_a + ma * cos_a))
    m = _szorzat(_eltolas((uj_sz - sz) // 2, (uj_ma - ma) // 2), m)
    m = _szorzat(_forgatas(uj_sz / 2.0, uj_ma / 2.0, szog), m)
    return uj_sz, uj_ma, m


def _cinemascope(w: int, h: int, op: FilterOp) -> tuple[int, int, Matrix]:
    letterbox = _logikai(op, 0, True)
    if not letterbox:
        return w, h, AZONOSSAG
    vagott_ma = min(round(w / 1.7), h)
    felso = max(0, (h - vagott_ma) // 2)
    m = _eltolas(0, -felso)

    uj_ma = max(1, round(vagott_ma * 0.95))
    aranyy = uj_ma / float(vagott_ma)
    m = _szorzat(((1.0, 0.0, 0.0), (0.0, aranyy, 0.0)), m)

    sav = round(vagott_ma * 0.15)
    m = _szorzat(_eltolas(0, sav), m)
    return w, uj_ma + 2 * sav, m


#: Kulcs → geometria-függvény. A kulcsok kisbetűsek, mint a regiszterben.
_GEOMETRIA = {
    "border": _border,
    "roundededges": _rounded_edges,
    "museummatte": _museum_matte,
    "dropshadow": _drop_shadow,
    "polaroid": _polaroid,
    "cinemascope": _cinemascope,
}


def keret_geometria(ops: "tuple[FilterOp, ...]", width: int, height: int) -> KeretGeometria:
    """A `width` × `height`-es forrás elhelyezkedése az `ops` lánc kimenetében.

    A nem keret-jellegű szűrőket átugorja (azok nem mozdítják a képet). A
    keret-effektek a lánc végén, a megadott sorrendben futnak — a
    `chain._FRAME_EFFECTS` ugyanezt a halmazt alkalmazza a vágás UTÁN.
    """
    m: Matrix = AZONOSSAG
    sz, ma = int(width), int(height)
    for op in ops:
        geo = _GEOMETRIA.get(op.name.lower())
        if geo is None:
            continue
        sz, ma, lepes = geo(sz, ma, op)
        m = _szorzat(lepes, m)
    return KeretGeometria(szelesseg=sz, magassag=ma, matrix=m)


__all__ = ["KeretGeometria", "Matrix", "AZONOSSAG", "keret_geometria"]
