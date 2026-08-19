"""A kollázs VETETT ÁRNYÉKA — a négy témánkénti paraméterkészlet (#977).

Spec: `docs/specs/picasa-kollazs-felulet.md` **9/b**.

## Miért külön modul

Az árnyék eddig csak **kapcsoló** volt: a jelölőnégyzet bekapcsolható, az
érték a `.cxf`-be is bekerül — rajzolás viszont sehol nem történt. A
felhasználó élesben jelezte: „nem látszik a vetett árnyék". Ez a modul a
geometriát adja hozzá: eltolás, elmosás, alfa, befoglaló-bővítés.

## ⚠️ NÉGY paraméterkészlet van, nem egy közös

A `ytShadowNode` konstruktorát (`0x0087b170`) **négy** hely hívja, mind egy
téma osztályához tartozik, mind **külön konstansokkal**. Aki egyetlen
átlátszatlansággal írja meg, négy témából kettőt elront — és ez zöld teszt
mellett is néma hiba, mert a különbség csak a képen látszik.

| téma | eltolás x | eltolás y | elmosás | átlátsz. | alfa |
|---|---|---|---|---|---|
| Képkupac | `0,001·A·W + 1` | `0,0015·A·W + 1` | `0,01·A·W` | 0,4 | **102** |
| Mozaik, Képkockamozaik | `0,0017·W + 1` | `0,0025·W + 1` | `0,008·W` | 0,4 | **102** |
| Rács, Indexkép | `0,001·k + 1` | `0,002·k + 2` | `0,03·k` | **0,6** | **153** |
| Többszörös exponálás | — | — | — | **nincs** | — |

`W` a **lap** szélessége képpontban (ezt a golden `AI4` mérése dönti el),
`A` a darabszámból számolt lépték (9.0), `k` a téma egész cellaéle (9/b.3).

Mindegyikre közösen (`0x0087b1e0`):

```
raszterizáló.sugár = elmosás · 8,0
raszterizáló.alfa  = (egész)(átlátszatlanság · 256,0)
befoglaló_téglalap += elmosás · 1,5   MINDEN élen
```

## Hogy melyik témának VAN árnyéka, a MASZK dönti el

A Többszörös exponálás tiltása a képesség-maszk **11. bitjéből** jön
(`themes.capabilities_for`), nem témanév-hasonlításból. A golden `AI7.cxf`-ben
`shadows="0"`, és a felhasználó be sem tudta kapcsolni — a bit független
igazolása.

## A lecsengés alakja — a szórás megválasztása

A spec 9/b.1 szerint a raszterizáló „külön X és Y irányú lecsengés
**szorzatát**" adja: ez pontosan egy **szeparábilis** elmosás egy téglalapon.
Ezért Gauss-elmosást használunk, `szórás = elmosás / 2` értékkel. A választás
nem szabad: így a lecsengés **3·szórás = elmosás · 1,5** távolságban hal el,
azaz pontosan ott, ameddig az eredeti a befoglalót bővíti. A két, egymástól
független szám (a `0xd34128 = 1.5` és a hármas-szórásos támasz) így
illeszkedik — a bővítés nem önkényes ráhagyás, hanem a lecsengés támasza.

⚠️ **Amit ez NEM bizonyít:** hogy a mi kimenetünk az eredetivel egyező lesz
(#879 tanulsága). A képlet a binárisból jön, a golden-mérés igazolja a
számokat — a rajzolt kép egyezését csak összevetés mutathatja meg.

Bemenet/kimenet: OpenCV **BGR** `uint8` képek (a `render.py` konvenciója).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import NamedTuple

import cv2
import numpy as np

from .render import screen_rotation
from .themes import (
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
    capabilities_for,
)

# --- A tizenkét konstans (spec 9/b.2) ---------------------------------------
#
# Minden szám a binárisból, a `.rdata` címével együtt. Nevesítve állnak, hogy
# a receptek táblája olvasható maradjon — és hogy egy elgépelt tizedesjegy ne
# tudjon némán elbújni egy témánkénti `if`-ben.

#: Képkupac (`CPileTheme`, `0x0087da1d`–`0x0087da87`).
PILE_OFFSET_X_SCALE = 0.001  # 0xcf3db0
PILE_OFFSET_Y_SCALE = 0.0015  # 0xcf4e10
PILE_BLUR_SCALE = 0.01  # 0xcf40b8

#: Mozaik és Képkockamozaik (`CGridTheme`/`CFrameGridTheme`, `0x008832ad`–).
GRID_OFFSET_X_SCALE = 0.0017  # 0xcf4e08
GRID_OFFSET_Y_SCALE = 0.0025  # 0xcf4e00
GRID_BLUR_SCALE = 0.008  # 0xcf4df8

#: Rács és Indexkép (`CRegularGridTheme`/`CContactSheetTheme`, `0x008856b0`–).
CELL_OFFSET_X_SCALE = 0.001  # 0xcf3db0
CELL_OFFSET_Y_SCALE = 0.002  # 0xcf4120
CELL_BLUR_SCALE = 0.03  # 0xcf4dc8

#: Az eltolás ADDITÍV tagja. ⚠️ Nem elhagyható: a golden `AI4` mérése külön
#: kimondja, hogy nélküle 8,70/12,80 jönne a mért 10,0/14,5 helyett.
OFFSET_BASE_ONE = 1.0  # 0xc7e328
OFFSET_BASE_TWO = 2.0  # 0xc7d9d0

#: A két átlátszatlanság — **ez a legkönnyebben elrontható szám**.
SOFT_OPACITY = 0.4  # 0xc7c838 (Képkupac, Mozaik, Képkockamozaik)
STRONG_OPACITY = 0.6  # 0xc7e304 (Rács, Indexkép)

# --- Amit mindegyik téma közösen csinál (`0x0087b1e0`) ----------------------

#: `raszterizáló.sugár = elmosás · 8,0` (`0xc7ea10`).
RASTER_RADIUS_FACTOR = 8.0

#: `alfa = (egész)(átlátszatlanság · 256,0)` (`0xcf39d8`) — 0,4 → 102, 0,6 → 153.
ALPHA_SCALE = 256.0

#: `befoglaló_téglalap += elmosás · 1,5` MINDEN élen (`0xd34128`).
#: Enélkül az árnyék éles vonalban levágódna a csempe szélén.
BOUNDS_GROWTH_FACTOR = 1.5

#: A Gauss-szórás az elmosásból: `elmosás / 2`, hogy a 3·szórásos támasz
#: PONTOSAN a `BOUNDS_GROWTH_FACTOR`-ral bővített befoglalót töltse ki.
BLUR_TO_SIGMA = 0.5

# --- A `k` cellaél levezetése (spec 9/b.3, `0x00887e50`) --------------------

#: A lap hasznos területe vízszintesen (`0xd3a140 = 0.88f`).
CONTACT_USABLE_WIDTH = 0.88

#: …és függőlegesen (`0xd3a144 = 0.79f`). A maradék 21 % az Indexkép fejlécéé —
#: a szorzó önmagában igazolja az olvasatot.
CONTACT_USABLE_HEIGHT = 0.79

#: Érvényességi kapu: cellánként legalább ennyi képpont, különben az eredeti
#: rajzolás `−1`-gyel hibázik (`0x008881ca`, `0x008881f1`).
MIN_CELL_EDGE_PIXELS = 8


class CellEdgeTooSmall(ValueError):
    """A cella a 8-képpontos kapu alá esne — az eredeti itt hibát jelez.

    Szándékosan kivétel és nem néma alapértelmezés: a torz rajz rosszabb,
    mint a hangos hiba."""


# --- A recept: melyik téma melyik képletet használja ------------------------

#: A képlet BEMENETE: a lap szélessége önmagában, léptékkel szorozva, vagy a
#: téma egész cellaéle.
BASIS_SHEET = "sheet"
BASIS_SHEET_SCALED = "sheet_scaled"
BASIS_CELL = "cell"


class ShadowRecipe(NamedTuple):
    """Egy paraméterkészlet — a négyből (a hat témára háromféle recept).

    A Mozaik és a Képkockamozaik UGYANAZT a receptet kapja (egy hívó, két
    vtable), ugyanígy a Rács és az Indexkép; a Képkupacé áll magában. A
    „négy készlet" a binárisbeli négy HÍVÓ; képletből három van."""

    offset_x_scale: float
    offset_y_scale: float
    blur_scale: float
    offset_x_base: float
    offset_y_base: float
    opacity: float
    basis: str


_PILE_RECIPE = ShadowRecipe(
    offset_x_scale=PILE_OFFSET_X_SCALE,
    offset_y_scale=PILE_OFFSET_Y_SCALE,
    blur_scale=PILE_BLUR_SCALE,
    offset_x_base=OFFSET_BASE_ONE,
    offset_y_base=OFFSET_BASE_ONE,
    opacity=SOFT_OPACITY,
    basis=BASIS_SHEET_SCALED,
)

_GRID_RECIPE = ShadowRecipe(
    offset_x_scale=GRID_OFFSET_X_SCALE,
    offset_y_scale=GRID_OFFSET_Y_SCALE,
    blur_scale=GRID_BLUR_SCALE,
    offset_x_base=OFFSET_BASE_ONE,
    offset_y_base=OFFSET_BASE_ONE,
    opacity=SOFT_OPACITY,
    basis=BASIS_SHEET,
)

_CELL_RECIPE = ShadowRecipe(
    offset_x_scale=CELL_OFFSET_X_SCALE,
    offset_y_scale=CELL_OFFSET_Y_SCALE,
    blur_scale=CELL_BLUR_SCALE,
    offset_x_base=OFFSET_BASE_ONE,
    offset_y_base=OFFSET_BASE_TWO,
    opacity=STRONG_OPACITY,
    basis=BASIS_CELL,
)

#: A paraméterkészletek EGYETLEN táblája. Témánkénti `if` sehol máshol nem
#: születik — ez a jegy egyik kimondott feltétele.
SHADOW_RECIPES: dict[str, ShadowRecipe | None] = {
    PICTUREPILE: _PILE_RECIPE,
    PICTUREGRID: _GRID_RECIPE,
    FRAMEGRID: _GRID_RECIPE,
    REGULARGRID: _CELL_RECIPE,
    CONTACTSHEET: _CELL_RECIPE,
    MULTIEXP: None,
}


@dataclass(frozen=True)
class ShadowParams:
    """Egy téma KISZÁMOLT árnyék-paraméterei, képpontban.

    | mező | jelentés |
    |---|---|
    | `offset_x`, `offset_y` | az árnyék eltolása jobbra-le |
    | `blur` | az elmosás mértéke (a származtatott értékek alapja) |
    | `opacity` | 0,4 vagy 0,6 |
    """

    offset_x: float
    offset_y: float
    blur: float
    opacity: float

    @property
    def alpha(self) -> int:
        """`(egész)(átlátszatlanság · 256)` — 0,4 → **102**, 0,6 → **153**."""
        return int(self.opacity * ALPHA_SCALE)

    @property
    def raster_radius(self) -> float:
        """A raszterizáló sugara: `elmosás · 8` (`0x0087b1e0`)."""
        return self.blur * RASTER_RADIUS_FACTOR

    @property
    def bounds_growth(self) -> float:
        """A befoglaló bővülése MINDEN élen: `elmosás · 1,5`."""
        return self.blur * BOUNDS_GROWTH_FACTOR

    @property
    def sigma(self) -> float:
        """A Gauss-szórás; a 3·szórásos támasz = `bounds_growth`."""
        return self.blur * BLUR_TO_SIGMA


# --- A két származtatott bemenet: `A` és `k` -------------------------------


def pile_scale(count: int) -> float:
    """A Képkupac lépték-argumentuma (`A`) a képek darabszámából.

    ```
    ha n <= 1:  A = 1,0
    egyébként:  A = min( 1,0 ; 1 / sqrt( sqrt(n) − 1 ) )
    ```

    Ez **szó szerint** a képek alapméretének görbéje (spec 9.0,
    `0x0082c9a0`) — a Képkupac árnyéka tehát a képmérettel EGYÜTT
    zsugorodik. Két külön kódhely, ugyanaz a görbe: a 9.0 független
    megerősítése."""
    if count <= 1:
        return 1.0
    gyok = math.sqrt(float(count)) - 1.0
    if gyok <= 0.0:
        return 1.0
    return min(1.0, 1.0 / math.sqrt(gyok))


def cell_edge(rect_width: int, rect_height: int, count: int) -> int:
    """A Rács és az Indexkép egész cellaéle (`k`) — spec 9/b.3.

    ```
    W' = (egész)( szélesség · 0,88 )
    H' = (egész)( magasság  · 0,79 )
    k  = (egész) sqrt( W' · H' / n )
    oszlopok = W' / k ;  sorok = H' / k
    amíg (oszlopok · sorok < n):  k−−, újraszámol
    ```

    Végül a 8-képpontos érvényességi kapu: `szélesség/oszlopok ≥ 8` **és**
    `magasság/sorok ≥ 8`, különben `CellEdgeTooSmall`.

    A levezetést a golden `AI6` igazolja: 3841×5120, 9 kép → `k = 1126`,
    ebből `elmosás = 33,8`; a képen MÉRT sugár 34,5."""
    if rect_width < 1 or rect_height < 1:
        raise ValueError(f"Érvénytelen téglalap: {rect_width}×{rect_height}")
    if count < 1:
        raise ValueError(f"Legalább egy kép kell a cellaélhez: {count}")

    hasznos_w = int(rect_width * CONTACT_USABLE_WIDTH)
    hasznos_h = int(rect_height * CONTACT_USABLE_HEIGHT)
    if hasznos_w < 1 or hasznos_h < 1:
        raise CellEdgeTooSmall(
            f"A lap hasznos területe üres: {rect_width}×{rect_height}"
        )

    k = int(math.sqrt(hasznos_w * hasznos_h / count))
    while k >= 1:
        oszlopok = hasznos_w // k
        sorok = hasznos_h // k
        if oszlopok * sorok >= count:
            break
        k -= 1
    if k < 1:
        raise CellEdgeTooSmall(
            f"{count} kép nem fér el a {rect_width}×{rect_height} lapon."
        )

    oszlopok = max(1, hasznos_w // k)
    sorok = max(1, hasznos_h // k)
    if (
        rect_width // oszlopok < MIN_CELL_EDGE_PIXELS
        or rect_height // sorok < MIN_CELL_EDGE_PIXELS
    ):
        raise CellEdgeTooSmall(
            f"A cella {rect_width // oszlopok}×{rect_height // sorok} képpont "
            f"volna, a legkisebb megengedett {MIN_CELL_EDGE_PIXELS}."
        )
    return k


def shadow_params(
    theme: str, *, page_width: int, page_height: int, count: int
) -> ShadowParams | None:
    """A téma árnyék-paraméterei képpontban — vagy `None`, ha nincs árnyéka.

    A „van-e árnyék" kérdésre a **képesség-maszk 11. bitje** felel
    (`themes.capabilities_for`), nem témanév-hasonlítás: így a Többszörös
    exponálás tiltása egyetlen forrásból jön.

    `count` a képek száma: a Képkupac léptéke (`A`) és a rácsos témák
    cellaéle (`k`) egyaránt ebből számol."""
    if theme not in SHADOW_RECIPES:
        raise ValueError(f"Ismeretlen kollázs-téma: {theme!r}")
    if not capabilities_for(theme).shadow:
        return None
    recept = SHADOW_RECIPES[theme]
    if recept is None:  # pragma: no cover — a maszk már kiszűrte
        return None
    if page_width < 1 or page_height < 1:
        raise ValueError(f"Érvénytelen lapméret: {page_width}×{page_height}")

    if recept.basis == BASIS_SHEET:
        alap = float(page_width)
    elif recept.basis == BASIS_SHEET_SCALED:
        alap = pile_scale(count) * page_width
    else:
        alap = float(cell_edge(page_width, page_height, max(1, count)))

    return ShadowParams(
        offset_x=recept.offset_x_scale * alap + recept.offset_x_base,
        offset_y=recept.offset_y_scale * alap + recept.offset_y_base,
        blur=recept.blur_scale * alap,
        opacity=recept.opacity,
    )


# --- A rajzolás -------------------------------------------------------------


def draw_shadow(
    canvas: np.ndarray,
    *,
    x: int,
    y: int,
    width: int,
    height: int,
    theta: float,
    params: ShadowParams,
) -> None:
    """Egy csempe vetett árnyéka a vászonra, HELYBEN.

    `x`, `y` a csempe bal felső sarka a vászonon, `theta` az elforgatása
    radiánban — ugyanaz a forgatás, amit a `render._rotated_paste` végez, és
    ugyanazzal a mátrixszal (`render.screen_rotation`), hogy az árnyék ne
    csússzon el a csempétől. A pozitív `theta` az óramutatóval EGYEZŐ irányba
    forgat, ahogy a `.cxf` és a vászon is (#1035).

    ⚠️ Az **eltolás** (`offset_x`, `offset_y`) továbbra is a VÁSZON tengelyei
    szerint értendő. Hogy az eredetiben a forgatás ELŐTT vagy UTÁN adódik a
    csomópont eltolásához, nincs levezetve — a #1035 köre ezért kizárólag a
    forgatás irányát javította, az eltolás koordinátarendszeréhez nem nyúlt.

    A menete: sziluett → befoglaló bővítése `elmosás · 1,5`-tel MINDEN élen →
    elmosás → eltolás jobbra-le → fekete keverés `alfa` súllyal. A vászon
    szélén az árnyék levágódik (a kép nem nőhet), de a csempe dobozán NEM."""
    if width < 1 or height < 1 or params.alpha <= 0:
        return

    maszk = np.ones((height, width), dtype=np.float32)
    if theta:
        # UGYANAZ a függvény, amit a `render._rotated_paste` hív — az árnyéknak
        # a csempével EGYÜTT kell fordulnia, nem tükörképben (#1035: a közös
        # hívás az, ami ezt szerkezetileg garantálja, nem egy megjegyzés)
        matrix, out_w, out_h = screen_rotation(width, height, math.degrees(theta))
        maszk = cv2.warpAffine(maszk, matrix, (out_w, out_h))
        x -= (out_w - width) // 2
        y -= (out_h - height) // 2
        width, height = out_w, out_h

    novekmeny = max(1, math.ceil(params.bounds_growth))
    maszk = cv2.copyMakeBorder(
        maszk,
        novekmeny,
        novekmeny,
        novekmeny,
        novekmeny,
        cv2.BORDER_CONSTANT,
        value=0.0,
    )
    if params.sigma > 0.0:
        maszk = cv2.GaussianBlur(
            maszk,
            (0, 0),
            sigmaX=params.sigma,
            sigmaY=params.sigma,
            borderType=cv2.BORDER_CONSTANT,
        )

    # az eltolás a csomópont eltolásához ADÓDIK (`0x0087b411`, `0x0087b423`)
    bal = x - novekmeny + round(params.offset_x)
    fent = y - novekmeny + round(params.offset_y)

    vaszon_h, vaszon_w = canvas.shape[:2]
    maszk_h, maszk_w = maszk.shape[:2]
    x0, y0 = max(0, bal), max(0, fent)
    x1 = min(vaszon_w, bal + maszk_w)
    y1 = min(vaszon_h, fent + maszk_h)
    if x0 >= x1 or y0 >= y1:
        return

    resz = maszk[y0 - fent : y1 - fent, x0 - bal : x1 - bal]
    alfa = (resz * (params.alpha / 255.0))[..., None]
    terulet = canvas[y0:y1, x0:x1].astype(np.float32)
    canvas[y0:y1, x0:x1] = np.clip(terulet * (1.0 - alfa), 0.0, 255.0).round().astype(
        np.uint8
    )


__all__ = [
    "ALPHA_SCALE",
    "BASIS_CELL",
    "BASIS_SHEET",
    "BASIS_SHEET_SCALED",
    "BOUNDS_GROWTH_FACTOR",
    "CONTACT_USABLE_HEIGHT",
    "CONTACT_USABLE_WIDTH",
    "MIN_CELL_EDGE_PIXELS",
    "RASTER_RADIUS_FACTOR",
    "SHADOW_RECIPES",
    "CellEdgeTooSmall",
    "ShadowParams",
    "ShadowRecipe",
    "cell_edge",
    "draw_shadow",
    "pile_scale",
    "shadow_params",
]
