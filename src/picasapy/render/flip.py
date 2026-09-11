"""Veszteségmentes tükrözés (#2902) — a forgatás párja.

Az eredeti könyvtárnézeti billentyűkezelője (`0x005e60d0`) két ágat szán a
tükrözésnek, és mindkettő ugyanazt a függvényt hívja, más argumentummal:

| billentyű | ág | hívás | irány |
|---|---|---|---|
| `Ctrl+Shift+H` | `0x005e63d6` | `0x005eef30(panel, 2)` | vízszintes |
| `Ctrl+Shift+V` | `0x005e6408` | `0x005eef30(panel, 1)` | függőleges |

A `SHORTCUTS.xml` keymapje ugyanezt nevezi meg (35. *Flip Horizontal*,
36. *Flip Vertical*), és a 3.9 MENÜIBEN nincs ilyen parancs — a funkció csak
billentyűvel érhető el (`docs/specs/picasa-gyorsbillentyuk.md` 10.3–10.4).

**A jelzőértékek a MÉRT argumentumokat követik:** `1` = függőleges, `2` =
vízszintes, tehát a kettő bitként fér egymás mellé (`3` = mindkettő). Ez nem
találgatás, hanem a két ág átadott számának átvétele.

⛔ **Amit NEM írunk a `.picasa.ini`-be.** Az ini-nek van `flipped(N)` kulcsa
(a Picasa írójának kulcs→alapérték táblája szerint `flipped(0)` az alapérték,
`docs/specs/00-index.md`), de hogy az `N` MELYIK bitje melyik irány, **nincs
kimérve**: a tulajdonos teljes korpuszában minden `flipped` üres
(`imagedata_flipped.pmp`: 3011/3011, és 0 db `flipped=` sor 859 ini-fájlban).
Egy találgatott érték a felhasználó valódi fájljaiba menne, és a kétirányú
ini-kompatibilitás a projekt központi ígérete — ezért a tükrözés-jelző
egyelőre **csak az indexben** él, a mappa-elrejtés (#1281) mintája szerint. A
tároló kimérése külön jegy.
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

#: Függőleges tükrözés (fel-le) — a mért `0x005eef30(panel, 1)` ág.
FLIP_VERTICAL = 1
#: Vízszintes tükrözés (bal-jobb) — a mért `0x005eef30(panel, 2)` ág.
FLIP_HORIZONTAL = 2
#: A két bit együtt. Ennél nagyobb értéket nem értelmezünk.
FLIP_MASK = FLIP_VERTICAL | FLIP_HORIZONTAL


def toggled_flip(flags: int, direction: int) -> int:
    """A jelző ki/be kapcsolása egy irányra — a csillag mintája.

    Ugyanarra az irányra másodszor nyomva visszaáll az eredeti állapot, mert
    a tükrözés önmaga inverze. Az értelmezhetetlen bitek leesnek."""
    return (int(flags or 0) ^ int(direction or 0)) & FLIP_MASK


def apply_flip(image: np.ndarray, flags: int) -> np.ndarray:
    """A jelzőnek megfelelő tükrözés. `0` esetén ugyanazt a képet adja
    vissza (nincs másolás), így a hívóoldalon nem kell ágazni."""
    flags = int(flags or 0) & FLIP_MASK
    if flags == FLIP_MASK:
        # mindkét tengely: ez a 180°-os forgatás, egyetlen hívással
        return cv2.flip(image, -1)
    if flags == FLIP_HORIZONTAL:
        return cv2.flip(image, 1)
    if flags == FLIP_VERTICAL:
        return cv2.flip(image, 0)
    return image
