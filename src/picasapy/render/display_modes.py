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

## `projector` és `lcd` — a két egyenletes sötétítő (#1577)

**MÉRVE** (`0x009e8a10` és `0x009e8a70`, 87–87 bájt; spec 5.4 és 5.5): a két
rutin **bitre azonos**, csak a szorzó más. Mindhárom csatorna ugyanazt a
szorzót kapja, az alfa érintetlen:

```
Projektor mód   c' = (c · 220) >> 8      ≈ −14,1 %
LCD fehérpont   c' = (c · 246) >> 8      ≈  −3,9 %
```

⚠️ **Az „LCD fehérpont" NEM állít fehérpontot.** A három szorzó azonos,
tehát **színeltolás nincs** — a mód pusztán egyenletesen sötétít. A felirat
félrevezet; a `.tre`/`stringres` sem ad hozzá buboréksúgót, ami mást
mondana. **A kód az igazságforrás**, ezt tehát nem szabad „kijavítani"
színhőmérséklet-korrekcióra. Ugyanígy a „Projektor mód" **nem** teljes
képernyő, **nem** energiagazdálkodás és **nem** nagyítás.

A szorzás **egész aritmetikával** megy (`>> 8`, nem `/ 256` kerekítéssel):
a levágás iránya a mért viselkedés része, `255 · 246 >> 8 = 245`, nem 246.

## `linear` — Lineáris gamma (2.2) (#1578)

**MÉRVE** (`0x009e8b60` → `0x00aa3f80`; spec 5.9): csatornánként egy 256
bájtos keresőtábla B-re, G-re, R-re; az alfa marad.

🔴 **A tábla NEM `x^(1/2.2)` — és semmilyen más képlet sem.** A `2.2f` float
a binárisban a **tábla kiválasztó kulcsa**, nem kitevő; maga a tábla a
`0x00d32bd0` címen **előre kitöltve** érkezik. A legjobb hatványillesztés
`p = 0,6944` (gamma ≈ 1,44), és még az is 256-ból 37 helyen téved ±1-gyel.

⇒ **Aki képletet illeszt ide, mérhetően rossz eredményt kap.** A
`LINEAR_GAMMA_LUT` ezért **mért adat, nem levezetés**: a spec 5.9
szakaszának 256 bájtja, kiírva. Hatványfüggvényre cserélni nem
egyszerűsítés, hanem paritás-vesztés — a
`tests/render/test_display_modes_1577_1578.py::TestNemKeplet` ezt tételesen
őrzi.

## A maradék hét mód

A `dither16`, `rdesk`, `mac`, `sepia`, `bw` (és a no-op `auto`/`normal`)
külön jegyeké. Addig az `apply_display_mode` ezekre **átereszt** — a
menütétel a #1575 óta kattintható, de képpontot nem mozdít. Ez szándékosan
NÉMA áteresztés: a menüt nem az itteni névsor tiltja le.

## Miért `cv2.LUT`, és nem numpy-indexelés?

**Mérve** (RPi5, 4000×3000×3 véletlen kép, `min` 5 futásból) — csak a tábla
alkalmazása: `cv2.LUT` **13 ms**, a numpy `lut[kép]` fancy-indexelés
199 ms, az `np.take` 294 ms, a nyers `(kép.astype(uint16) · m) >> 8`
129 ms. A tizenötszörös különbség a képernyő-frissítés útján érzékelhető,
ezért mindhárom mód ugyanazon a 256 elemű táblás úton megy — a sötétítés is
táblává előszámolva, nem tömbszorzással.

Az `apply_display_mode` teljes hívása ugyanezen a képen (a tábla építését
is beleértve): `projector` **17 ms**, `lcd` **23 ms**, `linear` **22 ms**
(a `overflow` összevetésül 38 ms). A néző valódi előnézeti méretén
(2560×1920) rendre 6, 6 és 7 ms.
"""

from __future__ import annotations

import cv2
import numpy as np

#: `ID_VIEW_OV` módazonosítója (a `DISPLAY_MODES` egyike, ld.
#: `picasapy.app.display_mode_controller`).
OVERFLOW_MODE = "overflow"

#: A jelölőszín RGB-ben — a `0xFFFF7F7F` dword bájtsorrendjéből (5.6).
OVERFLOW_MARK_RGB: tuple[int, int, int] = (255, 127, 127)

#: `ID_VIEW_PROJECTOR` módazonosítója.
PROJECTOR_MODE = "projector"

#: `ID_VIEW_LCD` módazonosítója.
LCD_MODE = "lcd"

#: `ID_VIEW_LINEAR` módazonosítója.
LINEAR_GAMMA_MODE = "linear"

#: A projektor mód szorzója — MÉRVE `0x009e8a10`: `0xDC` (spec 5.5).
PROJECTOR_MULTIPLIER = 220

#: Az „LCD fehérpont" szorzója — MÉRVE `0x009e8a70`: `0xF6` (spec 5.4).
#: A neve ellenére NEM fehérpont-korrekció, ld. a modul-docstringet.
LCD_MULTIPLIER = 246

#: A lineáris gamma (2.2) keresőtáblája — **MÉRT ADAT, NEM LEVEZETÉS**.
#:
#: A bináris `0x00d32bd0` címén előre kitöltve álló 256 bájt (spec 5.9),
#: soronként 16 érték. **Képlettel helyettesíteni tilos**: a legjobb
#: hatványillesztés (`p = 0,6944`) is 37 helyen téved, a kézenfekvő
#: `x^(1/2.2)` pedig 16-tal is mellémegy az alacsony értékeknél.
LINEAR_GAMMA_LUT: tuple[int, ...] = (
      0,   5,   9,  11,  14,  16,  19,  21,  23,  25,  27,  29,  30,  32,  34,  36,
     37,  39,  40,  42,  44,  45,  47,  48,  49,  51,  52,  54,  55,  56,  58,  59,
     60,  62,  63,  64,  66,  67,  68,  69,  71,  72,  73,  74,  75,  77,  78,  79,
     80,  81,  82,  84,  85,  86,  87,  88,  89,  90,  91,  92,  94,  95,  96,  97,
     98,  99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113,
    114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129,
    129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 140, 141, 142, 143,
    144, 145, 146, 147, 148, 149, 149, 150, 151, 152, 153, 154, 155, 155, 156, 157,
    158, 159, 160, 161, 161, 162, 163, 164, 165, 166, 166, 167, 168, 169, 170, 171,
    171, 172, 173, 174, 175, 176, 176, 177, 178, 179, 180, 180, 181, 182, 183, 184,
    184, 185, 186, 187, 188, 188, 189, 190, 191, 192, 192, 193, 194, 195, 195, 196,
    197, 198, 199, 199, 200, 201, 202, 202, 203, 204, 205, 205, 206, 207, 208, 208,
    209, 210, 211, 211, 212, 213, 214, 214, 215, 216, 217, 217, 218, 219, 220, 220,
    221, 222, 223, 223, 224, 225, 225, 226, 227, 228, 228, 229, 230, 231, 231, 232,
    233, 233, 234, 235, 236, 236, 237, 238, 238, 239, 240, 241, 241, 242, 243, 243,
    244, 245, 245, 246, 247, 248, 248, 249, 250, 250, 251, 252, 252, 253, 254, 255,
)  # fmt: skip

#: A gamma-tábla `cv2.LUT`-kész alakja — egyszer épül fel, modulszinten.
_LINEAR_GAMMA_TABLE: np.ndarray = np.array(LINEAR_GAMMA_LUT, dtype=np.uint8)

#: Módazonosító → a hozzá tartozó sötétítő szorzó (spec 5.4/5.5).
_DARKEN_MULTIPLIERS: dict[str, int] = {
    PROJECTOR_MODE: PROJECTOR_MULTIPLIER,
    LCD_MODE: LCD_MULTIPLIER,
}

#: Az a néhány mód, amely MA ténylegesen átírja a képpontokat. A hívó ebből
#: tudja, hogy megéri-e egyáltalán a képet numpy-tömbbé alakítania.
PIXEL_AFFECTING_MODES: frozenset[str] = frozenset(
    {OVERFLOW_MODE, PROJECTOR_MODE, LCD_MODE, LINEAR_GAMMA_MODE}
)

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


def _rgb_kep_e(rgb: np.ndarray) -> bool:
    """`(H, W, 3)` uint8 tömb-e? (A hívó bármit átadhat.)"""
    return (
        rgb is not None
        and getattr(rgb, "ndim", 0) == 3
        and rgb.shape[2] == 3
        and rgb.dtype == np.uint8
    )


def _tablat_alkalmaz(rgb: np.ndarray, table: np.ndarray) -> np.ndarray:
    """256 elemű tábla mindhárom csatornára, ÚJ tömbbe.

    A `cv2.LUT` nulla kiterjedésű képre `None`-t ad — az üres tömb így a
    másolatával tér vissza (a hívó mindig új, írható tömböt kap).
    """
    if rgb.size == 0:
        return rgb.copy()
    return cv2.LUT(rgb, table)


def darken(rgb: np.ndarray, multiplier: int) -> np.ndarray:
    """Egyenletes sötétítés `c' = (c · multiplier) >> 8` (spec 5.4/5.5).

    Mindhárom csatorna UGYANAZT a szorzót kapja, tehát **színeltolás nincs**
    — ez a mért viselkedés, nem hiányosság (ld. a modul-docstringet az „LCD
    fehérpont" félrevezető feliratáról).

    A bemenet `(H, W, 3)` uint8 RGB-tömb; a visszaadott tömb **új**. A
    bemenetet SOHA nem írjuk át helyben: a hívó (edit-előnézet)
    gyorsítótárazott köztes eredményt ad át, és annak megmérgezése a mód
    kikapcsolása után is sötéten hagyná a képet.

    A számítás 256 elemű táblává előszámolva megy (`cv2.LUT`): a tábla maga
    az egész aritmetika, tehát a kerekítés bitre a mért `>> 8` levágása.
    """
    if not _rgb_kep_e(rgb):
        return rgb
    # `arange` uint16-on: 255 · 246 = 62730 nem fér 8 bitre, a `>> 8` UTÁN
    # viszont már igen. Ez maga a mért egész aritmetika, lebegőpont nélkül.
    table = ((np.arange(256, dtype=np.uint16) * int(multiplier)) >> 8).astype(
        np.uint8
    )
    return _tablat_alkalmaz(rgb, table)


def apply_linear_gamma(rgb: np.ndarray) -> np.ndarray:
    """A lineáris gamma (2.2) MÉRT keresőtáblája csatornánként (spec 5.9).

    A bemenet `(H, W, 3)` uint8 RGB-tömb; a visszaadott tömb **új**.

    🔴 A tábla (`LINEAR_GAMMA_LUT`) **mért adat**, a binárisból kiolvasva —
    **nem** `x^(1/2.2)` és nem is más képlet. Ha valaki „egyszerűsítené"
    hatványfüggvényre, a kép mérhetően eltérne az eredetitől; a részleteket
    ld. a modul-docstringben.
    """
    if not _rgb_kep_e(rgb):
        return rgb
    return _tablat_alkalmaz(rgb, _LINEAR_GAMMA_TABLE)


def apply_display_mode(rgb: np.ndarray | None, mode: str) -> np.ndarray | None:
    """A megjelenítési mód alkalmazása a MEGJELENÍTENDŐ képre.

    A nem (még) megvalósított módokra és az ismeretlen azonosítóra a képet
    változatlanul adja vissza — a hívónak nem kell módonként elágaznia.
    """
    if rgb is None:
        return None
    if mode == OVERFLOW_MODE:
        return mark_overflow(rgb)
    multiplier = _DARKEN_MULTIPLIERS.get(mode)
    if multiplier is not None:
        return darken(rgb, multiplier)
    if mode == LINEAR_GAMMA_MODE:
        return apply_linear_gamma(rgb)
    return rgb
