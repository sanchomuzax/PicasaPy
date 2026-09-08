"""`linblur` — „Lineáris homályosítás" (a natív `0x0090de10` mag, #623).

**Nem mozgáshomály**, hanem ÁTMENETES (graduált) életlenítés — tilt-shift
jellegű hatás. A burkoló (`0x008f99c0`) két pontot ad a magnak:

| pont | mi | a mag szerinti hatás |
|---|---|---|
| `p1` | a felületi korong (puck) helye | `t = +65536` → `alpha = 250` → **éles** |
| `p0` | a kép közepe (`W>>1`, `H>>1`) | `t = −65536` → `alpha = 5` → **homályos** |

A `t` a két ponton átmenő egyenes menti, 16.16 fixpontos vetület:

```c
kx = (d.x << 16)/|d|²;   ky = (d.y << 16)/|d|²;        d = p1 − p0
t  = 2·kx·x + 2·ky·y − ((p0.x+p1.x)·kx + (p0.y+p1.y)·ky)
idx   = t >> 8;                       // a végpontokban ±256
alpha = (súly[idx] + 255) / 2;        // súly[−i] = −súly[i]
out   = homályos + ((éles − homályos) · alpha >> 8);
```

`idx <= −384` esetén a mag **nem ír semmit** (marad a végig elmosott
puffer), `idx >= +384` esetén a **nyers éles forrást** írja.

## Amit ez a modul KÖZELÍT — és min múlik

1. ⭐ **MÉRVE (2026-09-09, #2736): a „Mennyiség" csúszka NEM hat az
   elmosásra.** A mérőszett három `linblur`-referenciája ugyanarról a
   képről készült, láncuk csak a negyedik értékben tér el
   (`2,0` / `10,0` / `0,0`), és a valódi Picasa három kimenete **bitre
   azonos** — miközben a forrástól mindhárom eltér (átlag 12,21), tehát a
   szűrő lefutott. A binárisban ugyanez: a burkoló (`0x008f99c0`)
   EGYETLEN lebegőpontos argumentumot ad a magnak (`fstp dword [esp]` a
   `call 0x0090de10` előtt), a mag pedig azt adja tovább a közös elmosónak
   mindkét tengelyre (`0x0090dec6`, `0x0090def6` → `0x009dd0d0`); a
   negyedik lánc-érték ebbe a láncba nem kerül be.

   A sugár mért értéke a mi (`iir_blur`) paraméterezésünkben **1,5**
   (`LINBLUR_MERT_SUGAR`): a ΔE a valódi exporttól 13,147 / 17,849 / 6,814
   (alap / max / min, a régi `szélesség/100·(Mennyiség+1)` képlettel)
   helyett **mindháromra 0,279** — JPEG-zaj nagyságrend.

   ⛔ **A hatókör:** a mérés EGY korong-álláson (`0,5; 0,5`) készült, mert
   csak ahhoz van referencia-exportunk. Az MÉRVE van, hogy a „Mennyiség"
   nem hat, és hogy ezen az álláson a sugár 1,5; az NINCS mérve, hogy a
   sugár függ-e a korong helyétől — ezért konstans, nem képlet: egy
   `1+|x|` alak ugyanezt az egy pontot találná el, de bizonyítatlan
   függést állítana. Második referencia-pont: #2772.
2. **A súlytábla utolsó rekeszei.** A natív kód a `round((1−2f)·255,9999)`
   értéket **bájtba** írja, így `f → 0` közelében (`i >= 338`) 256-ot
   tárolna, ami 0-ra fordul körbe — vagyis a teljesen ÉLES tartomány egy
   sávjában 50%-os homályt adna. Ez a natív oldalon túlcsordulás; a
   255,9999-es szorzó a **csonkolás** klasszikus idiómája, ezért itt 255-re
   vágunk. Egy referencia-export ezt eldöntheti (#317).
3. **A korong pozíciója.** A `filters=` láncban a korong normált `x, y`
   koordinátaként áll elöl, a puck-os szűrők általános sorrendje szerint
   (`docs/specs/filterdesc-registry.md` 3. pont). Az átváltás kérdése
   LEZÁRULT (#2702, `docs/specs/filters-decoded.md`): a `filters=` érték
   átalakítás nélkül kerül a `CGenericFilter` mezőjébe és onnan vissza, a
   `linblur` feldolgozó visszahívása pedig a mezőt `[-1, +1]`-ben olvassa
   — nem `[0, 1]`-ben, mint a többi puck-os szűrő (ez a Picasán belüli
   aszimmetria, nem a mi félreolvasásunk). Valódi `linblur=` ini-mintánk
   továbbra sincs.

Ld. `docs/specs/picasa-native-filter-workers.md` 3.3 és 4.2.1.
"""

from __future__ import annotations

import numpy as np

from picasapy.fixedpoint import c_int_div
from picasapy.render.curves import validate_image
from picasapy.render.iir_blur import apply_picasa_blur

#: A natív súlytábla mérete (`0x180`): a `t` 0-tól 1,5-ig, 1/256-os lépésben.
LINBLUR_TABLE_SIZE = 0x180

#: A tábla lépésköze (`local_1bc += 0.00390625`).
_TABLE_STEP = 1.0 / 256.0

#: A natív skálázó szorzó a súlytábla építésénél.
_TABLE_SCALE = 255.9999

#: A MÉRT elmosási sugár a mi `iir_blur`-paraméterezésünkben (#2736). A
#: referencia-exporttól mért ΔE ehhez az egy értékhez tartozik (0,279); a
#: hatókör a modul-doc 1. pontjában áll kimondva.
LINBLUR_MERT_SUGAR = 1.5


def _spline_tail(t: float) -> float:
    """A köbös B-spline átmenet-függvénye a `t >= 0` félegyenesen.

    A natív ág-szerkezet (`0x0090de10`) szerint:
    `t <= 0,5` → `f = 1/2 − (3t/4 − t³/3)`, felette pedig
    `f = 9/16 − (9t/8 + (t³/6 − 3t²/4))`, ami `t >= 1,5`-nél már 0.
    """
    if t > 1.5:
        return 0.0
    square = t * t
    cube = square * t
    if t <= 0.5:
        return 0.5 - (t * 0.75 - cube * (1.0 / 3.0))
    return 0.5625 - (t * 1.125 + (cube * (1.0 / 6.0) - square * 0.75))


def linblur_weight_table() -> np.ndarray:
    """A 384 elemű, `int32` súlytábla — a natív `local_188` tömb.

    A `[0, 255]`-re vágásról ld. a modul docstringjének 2. pontját.
    """
    values = [
        int(round((1.0 - 2.0 * _spline_tail(index * _TABLE_STEP)) * _TABLE_SCALE))
        for index in range(LINBLUR_TABLE_SIZE)
    ]
    return np.clip(np.array(values, dtype=np.int32), 0, 255)


#: Egyszer épített, csak olvasásra használt tábla.
_WEIGHT_TABLE = linblur_weight_table()
_WEIGHT_TABLE.setflags(write=False)


def linblur_blur_radius(width: int, amount: float) -> float:
    """A `linblur` elmosási sugara — MÉRVE állandó (#2736).

    A `width` és az `amount` SZÁNDÉKOSAN nem szól bele: a mérés szerint a
    „Mennyiség" nem hat (három bitre azonos referencia-export három
    különböző lánccal), és a szélesség-skálázásra sincs bizonyíték. A két
    paraméter az API stabilitása miatt marad — a hívók (`chain`, a
    regisztráció) aláírása nem változik.

    Ld. a modul-doc 1. pontját: ott áll a mérés és a hatóköre.
    """
    del width, amount  # mérve nem hatnak — ld. a docstringet
    return LINBLUR_MERT_SUGAR


def _projection(
    height: int, width: int, near: tuple[int, int], far: tuple[int, int]
) -> np.ndarray:
    """A képpontonkénti `t` vetület, `(H, W)` alakú `int64` tömbként."""
    delta_x = near[0] - far[0]
    delta_y = near[1] - far[1]
    squared = delta_x * delta_x + delta_y * delta_y
    slope_x = c_int_div(delta_x << 16, squared)
    slope_y = c_int_div(delta_y << 16, squared)
    offset = -((far[1] + near[1]) * slope_y + (far[0] + near[0]) * slope_x)
    columns = np.arange(width, dtype=np.int64) * (2 * slope_x)
    rows = np.arange(height, dtype=np.int64) * (2 * slope_y)
    return columns[np.newaxis, :] + rows[:, np.newaxis] + offset


def _puck_pixel(size: int, normalized: float) -> int:
    """A normált korong-koordináta EGÉSZ képpontja — a natív burkoló szerint.

    A burkoló (`0x008f99c0`, utasításról utasításra: `0x008f99ec`–
    `0x008f9a10`) a korong képpontját

    ```
    __ftol(0,5 · méret · (1 + p))
    ```

    alakban számolja (a `0,5` a `0x00c72150`-en álló `double`) — NEM
    `méret · p`-t, mint korábban itt állt. A kettő csak `p = 1`-nél esik
    egybe; a leíró `0,5`-ös alapértéke a natív oldalon a `méret` 3/4-ét
    adja, nem a felét (#2710, ld. a modul fejlécének 3. pontját).

    Az `__ftol` (`0x00c29990`, az SSE-ágon `cvttsd2si`) a nulla felé
    **csonkol**. Ez nem részletkérdés: a mag belépő feltétele (ld.
    `apply_linblur`) egész egyenlőség, és csak a csonkolás mellett
    paritás-független, mert `csonk(méret/2) == méret>>1` minden nemnegatív
    méretre. Kerekítéssel páratlan méreten `round(63,5) = 64 != 63` — ezt
    mérte a #953.
    """
    return int(0.5 * size * (1.0 + float(normalized)))


def apply_linblur(
    image: np.ndarray, x: float, y: float, amount: float
) -> np.ndarray:
    """Átmenetes életlenítés: a korong felőli oldal éles, a közép felőli nem.

    Az `x`, `y` a korong `filters=`-ből olvasott, ÁTALAKÍTÁS NÉLKÜL továbbadott
    értéke — a `linblur` feldolgozó visszahívása ezt `[-1, +1]`-ben olvassa
    (#2702, ld. a modul fejlécének 3. pontját), NEM `[0, 1]`-ben, mint a
    puck-os szűrők általános konvenciója. Az `amount` a „Mennyiség" csúszka.
    Ha a korong ugyanarra a KÉPPONTRA esik, mint a kép közepe, a natív mag
    ki sem lép a belépő feltételéből — a kép változatlan.

    **A belépő feltétel a binárisból** (#953, `pe_dis.py`-diszasszemblátum):

    ```
    0x0090de88  mov ecx, [ebp]      ; korong.x        (a burkoló számolta)
    0x0090de8b  cmp ecx, [esi]      ; közép.x = W>>1
    0x0090de8d  jne 0x0090de9b      ; nem egyezik → fut az elmosás
    0x0090de8f  mov edx, [ebp+4]    ; korong.y
    0x0090de92  cmp edx, [esi+4]    ; közép.y = H>>1
    0x0090de95  je  0x0090e1e5      ; ← EGYEZIK: a 0x0090e1e5 epilógusra ugrik
    ```

    A `0x0090e1e5` puszta epilógus (`pop`-ok, veremőr, `xor eax,eax`, `ret`):
    az eredeti a képhez **hozzá sem nyúl**. A rövidzár tehát a binárisban is
    ott van, és ott is EGÉSZ egyenlőség — csak a korong egészét a burkoló
    (`0x008f99c0`) `__ftol`-lal állítja elő, ami CSONKOL (ld.
    `_puck_pixel`), nem kerekít.

    A `filters=` átalakítás-mentes útjáról és a `linblur` `[-1, +1]`
    konvenciójáról ld. a modul fejlécének 3. pontját — ez a kérdés #2702
    óta LEZÁRULT.

    **A #880 mérése ÚJRAFUTOTT a javítással (#2710), és KÉT DOLGOT mond:**

    1. A színbeli ΔE a valódi Picasa-exporttól **5,42-ről 13,06-ra NŐTT**
       (`max` / `min`: 17,37 / 6,82). Ez elsőre visszaesésnek látszik.
    2. ⭐ De az **5,42 a „nem történik semmi" pontszáma volt**: a korong a
       régi képlettel a kép KÖZEPÉRE esett, tehát a mag belépő rövidzára
       (#953) elsült, és a kimenet a NYERS forrás volt. Mérve: a régi
       kimenet élesség-megtartása a kép minden oszlopában **1,000**.

    ⭐ **A HELYET a javítás eltalálja.** Az élesség-megtartás oszloponkénti
    profilja (Sobel-energia a forráshoz mérve) a valódi Picasa-exporttal:

    | | korreláció a Picasa profiljával | legjobban megtartott oszlop |
    |---|---|---|
    | régi (`méret · p` ⇒ 0,50 W) | **0,095** | 0,52 W |
    | új (`0,5·méret·(1+p)` ⇒ 0,75 W) | **0,988** | 0,98 W |
    | Picasa-export | — | 0,98 W |

    Vagyis az effekt mostantól a jó oldalon élesít (bal oldal elmosva, jobb
    oldal éles, az átmenet 0,7–0,85 W között), pontosan mint az eredeti; a
    megmaradó ΔE az elmosás ERŐSSÉGÉBŐL jön, nem a helyéből. A
    ⭐ **A #2736 ezt kimérte:** a „Mennyiség" nem hat, a sugár állandó
    (`LINBLUR_MERT_SUGAR = 1,5`), és ezzel a ΔE mindhárom esetre **0,279**
    (13,147 / 17,849 / 6,814 helyett). A súlytábla csonkolása (2. pont)
    továbbra is közelítés — a 0,279-es maradék ΔE-ben csak ez és a
    JPEG-kerekítés lehet benne.

    A paritás-függés ettől FÜGGETLENÜL szűnik meg: mindkét olvasat
    középpontja `csonk(méret/2) == méret>>1`.
    """
    validate_image(image)
    height, width = image.shape[:2]
    puck = (_puck_pixel(width, x), _puck_pixel(height, y))
    center = (width >> 1, height >> 1)
    if puck == center:
        return image.copy()

    radius = linblur_blur_radius(width, amount)
    # a natív burkoló KÉTSZER futtatja végig a közös elmosó magot
    blurred = apply_picasa_blur(
        apply_picasa_blur(image, radius, radius), radius, radius
    ).astype(np.int64)

    index = _projection(height, width, puck, center) >> 8
    clamped = np.clip(index, -(LINBLUR_TABLE_SIZE - 1), LINBLUR_TABLE_SIZE - 1)
    # a súlytábla PÁRATLAN kiterjesztéssel él: `súly[−i] = −súly[i]`
    magnitude = _WEIGHT_TABLE[np.abs(clamped)]
    weight = np.where(clamped < 0, -magnitude, magnitude)
    alpha = ((weight + 255) // 2)[..., np.newaxis]

    sharp = image.astype(np.int64)
    blended = blurred + ((sharp - blurred) * alpha >> 8)
    result = np.where(index[..., np.newaxis] >= LINBLUR_TABLE_SIZE, sharp, blended)
    result = np.where(
        index[..., np.newaxis] <= -LINBLUR_TABLE_SIZE, blurred, result
    )
    return np.clip(result, 0, 255).astype(np.uint8)


__all__ = [
    "LINBLUR_TABLE_SIZE",
    "apply_linblur",
    "LINBLUR_MERT_SUGAR",
    "linblur_blur_radius",
    "linblur_weight_table",
]
