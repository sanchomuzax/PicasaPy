"""Megjelenítési módok (`Nézet ▸ Megjelenítési mód`) — KÉPERNYŐRE ható átalakítók.

Ezek NEM a `filters=` lánc elemei: a mentett képre semmilyen hatásuk nincs.
Az eredetiben a hívás helye az ablak újrarajzolása (`0x009e285d`), tehát a
kép a lemezen és az exportban változatlan marad. A modul ennek megfelelően a
`render/` sáv szabályát követi: **képet kap és képet ad**, lemezhez nem nyúl.

## `overflow` — `ID_VIEW_OV`, a túlcsordult képpontok jelölése (#1576)

**MÉRVE** (`0x009e8810`, 49 bájt; `docs/specs/picasa-megjelenitesi-modok.md`
5.6. szakasz):

```asm
mov esi, [pixel]
and esi, 0xffffff
cmp esi, 0xffffff          ; B == G == R == 255 ?
jne tovabb
mov dword ptr [pixel], 0xffff7f7f
```

⚠️ **Három dolog, amit tilos „megjavítani":**

* **Nincs tűrés.** A küszöb pontosan 255 mindhárom csatornán; a 254 még nem
  túlcsordulás. A `>= 254`-re lazítás nem javítás, hanem paritás-vesztés.
* **Nincs csatornánkénti jelölés.** A `(255, 200, 10)` R-csatornája telített,
  az eredeti mégsem jelöli.
* **A fekete oldali levágás nincs jelölve.** A `(0, 0, 0)` érintetlen marad.

Ha bármelyik jobbnak látszik, az KÜLÖN jegy — az eredeti viselkedést ez a
modul adja vissza.

A jelölőszín a beírt dword bájtsorrendjéből: `0xFFFF7F7F` ⇒ `B=0x7F`,
`G=0x7F`, `R=0xFF`, `A=0xFF` ⇒ **RGB(255, 127, 127) = `#FF7F7F`**.

## A többi tíz mód

A `#1577`/`#1578` hozza őket (szemcsézés, LCD-fehérpont, projektor, gammák,
szépia, fekete-fehér). Addig az `apply_display_mode` ezekre **átereszt** — a
menütétel a #1575 óta kattintható, de képpontot nem mozdít. Ez szándékosan
NÉMA áteresztés: a menüt nem az itteni névsor tiltja le.
"""

from __future__ import annotations

import numpy as np

#: `ID_VIEW_OV` módazonosítója (a `DISPLAY_MODES` egyike, ld.
#: `picasapy.app.display_mode_controller`).
OVERFLOW_MODE = "overflow"

#: A jelölőszín RGB-ben — a `0xFFFF7F7F` dword bájtsorrendjéből (5.6).
OVERFLOW_MARK_RGB: tuple[int, int, int] = (255, 127, 127)

#: Az a néhány mód, amely MA ténylegesen átírja a képpontokat. A hívó ebből
#: tudja, hogy megéri-e egyáltalán a képet numpy-tömbbé alakítania.
PIXEL_AFFECTING_MODES: frozenset[str] = frozenset({OVERFLOW_MODE})

def display_mode_changes_pixels(mode: str) -> bool:
    """Mozdít-e ez a mód képpontot? (Ismeretlen/üres módra `False`.)"""
    return mode in PIXEL_AFFECTING_MODES


def mark_overflow(rgb: np.ndarray) -> np.ndarray:
    """A tökéletesen fehér képpontok átfestése `#FF7F7F`-re (`ID_VIEW_OV`).

    A bemenet `(H, W, 3)` uint8 RGB-tömb. A visszaadott tömb **új**, ha volt
    mit jelölni — a bemenetet SOHA nem írjuk át helyben, mert a hívó
    (edit-előnézet) gyorsítótárazott köztes eredményt ad át, és annak
    megmérgezése a mód kikapcsolása után is festve hagyná a képet.

    Ha nincs jelölendő képpont, a bemenetet adja vissza változatlanul (a
    hívók nem mutálnak, tehát a másolat itt fölösleges munka volna).

    **Mérve** (RPi5, 4000×3000, `min` 5 futásból): kifehéredett folt nélkül
    34 ms, ~5 %-nyi folttal 58 ms, végig fehér képen 117 ms. A néző valódi
    előnézeti mérete (2560 px-es élhossz) mellett ~24 ms. A kézenfekvő
    alakok LASSABBAK: a `(r == 255) & (g == 255) & (b == 255)` maszk és a
    `kép[maszk] = szín` háromdimenziós szórás együtt 2–4-szeres idő
    (68/127/469 ms), a `min(axis=2)` pedig 5–10-szeres. Ezért készül a maszk
    bitenkénti ÉS-sel, és ezért csatornánként (kétdimenziós nézeten) írunk.
    """
    if rgb is None or rgb.ndim != 3 or rgb.shape[2] != 3:
        return rgb
    # `(r & g & b) == 255` pontosan akkor igaz, ha MINDHÁROM csatorna 255 —
    # ez maga a mért `and esi, 0xffffff` + `cmp esi, 0xffffff`, tűrés nélkül.
    mask = (rgb[:, :, 0] & rgb[:, :, 1] & rgb[:, :, 2]) == 255
    if not mask.any():
        return rgb
    marked = rgb.copy()
    for channel, value in enumerate(OVERFLOW_MARK_RGB):
        # `marked[:, :, channel]` NÉZET — a beírás a másolatba megy.
        plane = marked[:, :, channel]
        plane[mask] = value
    return marked


def apply_display_mode(rgb: np.ndarray | None, mode: str) -> np.ndarray | None:
    """A megjelenítési mód alkalmazása a MEGJELENÍTENDŐ képre.

    A nem (még) megvalósított módokra és az ismeretlen azonosítóra a képet
    változatlanul adja vissza — a hívónak nem kell módonként elágaznia.
    """
    if rgb is None:
        return None
    if mode == OVERFLOW_MODE:
        return mark_overflow(rgb)
    return rgb
