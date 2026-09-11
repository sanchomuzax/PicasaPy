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

**A jelzőértékek az ini BITMASZKJÁT követik (#2976):** `1` = vízszintes,
`2` = függőleges, `3` = mindkettő. A #2938 kimérte az ini-írót
(`0x0042d7e0`): a 0. bit a `2`-es, az 1. bit az `1`-es műveletet váltja ki,
és a fenti tábla szerint a `2` a vízszintes. A billentyű-ág argumentuma
tehát MÁS számtér, mint a fájlba írt maszk — a jelzőnk korábban azt vette
át, és emiatt fordítva állt.

**A jelző a `.picasa.ini`-be megy (#2976).** A #2902 idejében a bit-jelentés
még feltevés volt, ezért a jelző csak az indexben élt; a #2938 mérése óta a
tárolás igazolt, tehát a `flipped(N)` kulcsba írjuk — a `rotate(N)` mintája
szerint.

⚠️ **Nulla maszknál a kulcs ÜRES értéket kap**, nem `flipped(0)`-t
(`0x0042d864`). Ez magyarázza a korpuszt is: az `imagedata_flipped.pmp`
3011/3011 üres, és 859 ini-fájlban 0 db `flipped=` sor van — a tulajdonos
sosem tükrözött, a nulla pedig nem ír ki számot.

⚠️ **A forgatás és a tükrözés SORRENDJE nincs kimérve** (a #2938 örökölt
kérdése). A mai sorrend — előbb forgatás, utána tükrözés — kimondott
feltevés, nem mérés.
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

#: Vízszintes tükrözés (bal-jobb) — az ini-maszk 0. bitje (#2976).
FLIP_HORIZONTAL = 1
#: Függőleges tükrözés (fel-le) — az ini-maszk 1. bitje (#2976).
FLIP_VERTICAL = 2
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
