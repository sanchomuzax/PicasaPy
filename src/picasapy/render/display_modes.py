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

## `linear` és `mac` — a KÉT gamma-mód, és melyik tábla kié (#1578, #3068)

**MÉRVE** (spec 12.4): mindkét mód ugyanazt a gamma-alkalmazót hívja, csak
más float-ot ad át neki, és az választja ki a táblát:

| mód | átalakító | mit ad át | melyik tábla |
|---|---|---|---|
| `mac` — Mac gamma (1,6) | `0x009e8b40` (`fldz`) | **0,0** | `0x00d32bd0`, **beégetve** |
| `linear` — Lineáris gamma (2,2) | `0x009e8b60` | **2,2** | `0x00d32cd0`, futásidőben töltve |

🔴 **A beégetett tábla a MAC gammáé, nem a lineárisé.** A `MAC_GAMMA_LUT`
ezért **mért adat**: a spec 5.9 szakaszának 256 bájtja, kiírva.
Hatványfüggvényre cserélni nem egyszerűsítés, hanem paritás-vesztés — a
legjobb illesztés (`p = 0,6945`) is 37 helyen téved ±1-gyel. A menüfelirat
1,6-ot ígér, a tábla effektív gammája ≈1,44; az eltérés az EREDETIÉ.

🟡 **A lineáris tábla viszont SZÁMÍTOTT — és épp ez a hű alak.** Az eredeti
a `0x00d32cd0`-et futásidőben tölti fel (`0x00aa3ff0`–`0x00aa404a`) a
`round(pow(i/255, 1/gamma) · 255)` képlettel, `gamma = 2,2`-vel.

⚠️ A kettő 2026-09-12-ig **fel volt cserélve** nálunk, mert a spec 5.9 és
5.10 szakasza is fel volt cserélve, és a #1578 abban az állapotban készült
el. A cserét a `tests/render/test_gamma_tablak_felcserelve_3068.py` őrzi.

## `bw` — Fekete-fehér (megjelenítési mód) (#1657)

**MÉRVE** (`0x009e89a0`, 90 bájt; spec 5.7):

```
Y = (77·R + 151·G + 28·B) >> 8          (77 + 151 + 28 = 256)
B' = G' = R' = Y                          A' = A
```

Egész, 8 bites BT.601-közeli luma. A súlyok összege pontosan 256, tehát a
`>> 8` nem veszít fényerőt: a szürke bemenet önmagát adja vissza
(`Y(g,g,g) = g`), a fehér pedig 255 marad.

⚠️ **Ez NEM a szerkesztő `bw` effektje.** Az (`render/color.py:apply_bw`) a
mentett képre ír és a `filters=` láncba kerül; ez itt csak a képernyőre
hat, a fájlhoz és a `.picasa.ini`-hez nem nyúl. A képletük a #3613 óta
UGYANAZ (az effekt is ezt az egész lumát számolja, bitre azonos kimenettel):
a különbség a hatókörben van, nem a képpontokban.

## `sepia` — Szépia (megjelenítési mód) (#1657)

**MÉRVE** — a konstansok és a MŰVELETSOR (`0x009e8850`, 336 bájt; spec 5.8).
Csatornánként, egész aritmetikával, a `Y` fenti lumájából kiindulva:

```
1.  Y   = (77·R + 151·G + 28·B) >> 8        mindhárom csatornára szétterítve
2.  v1  = 255 − ((255 − Y) · 218) >> 8      világosítás
3.  m   = 0xFF, ha v1 ≥ 128, különben 0x00  (a mért ((v1>>7) & 0x010101)·0xFF)
4.  v2  = (v1 xor m) · 2
    ki  = ((v2 · (c xor m)) >> 8) xor m     c = a #9B7D63 adott csatornája
```

🔴 **A lépéssort valósítjuk meg, NEM a nevet.** A spec 5.8 kimondja: a
konstansok mértek, de az „ez overlay-keverés" a kutató **olvasata**. Egy
kész overlay-rutin behívása azért tilos, mert a szokásos overlay `/255`-tel
normalizál, a mért kód viszont `>> 8`-cal — az eltérés csatornánként ±1,
és épp az a paritás, amiért a mód létezik.

Két dolog, ami elsőre hibának látszik, de mért viselkedés:

* **A fekete nem fekete marad.** A 2. lépés a 0-t 38-ra emeli
  (`255 − (255·218 >> 8) = 255 − 217`), így a kimenet `(46, 37, 29)` — sötét
  barna. Ez a szépia lényege, nem levágási hiba.
* **A fehér fehér marad.** `Y = 255 → v1 = 255 → m = 0xFF → v2 = 0`, tehát
  mindhárom csatorna `0 xor 0xFF = 255`. A mód nem tudja beszínezni a
  kifehéredett foltot.

A `v1` értékkészlete **38…255**, tehát a 3. lépés maszkja mindkét irányban
előfordul: a váltás pontosan `Y = 104` (`v1 = 127`, `m = 0`) és `Y = 105`
(`v1 = 128`, `m = 0xFF`) között van.

## A három változatlan mód

Az `auto` és a `normal` képpont-átalakítója üres, az `rdesk` módot pedig a
spec 7. táblázata hatókörön kívülinek jelöli. A `dither16` a #4412 óta az
eredeti szemcséző képletet alkalmazza.

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

A `bw` és a `sepia` **drágább**, és ez tudatosan vállalt ár: a luma három
csatorna súlyozott összege, ami nem fér 8 bitre, tehát kell egy uint16
köztes tömb (4000×3000-nél 72 MB). Mérve ugyanott: `bw` **~112 ms**,
`sepia` **~118 ms**; a néző előnézeti méretén (2560×1920) **~50** és
**~54 ms**. Négy alternatívát mértem — `cv2.split` + csatornánkénti
`cv2.LUT` + `cv2.add` (131 ms), `cv2.transform` összegzés (144 ms),
`cv2.cvtColor(GRAY2RGB)` szétterítés (119–125 ms), 64–512 soros sávokra
bontás (95–127 ms) —, **egyik sem gyorsabb**, tehát a legegyszerűbb alak
maradt. A naiv numpy út (`.astype(uint32)` + szorzás) 303 ms, azaz
2,7-szeres.

🔴 **A lassúságot NE lebegőpontos úttal „javítsa" senki.** A
`cv2.addWeighted`, a `cv2.transform` float mátrixszal és a
`cv2.cvtColor(RGB2GRAY)` mind **kerekít** (az utóbbi ráadásul más
súlyokkal: 0,299/0,587/0,114 a mért 77/151/28 ⇒ 0,3008/0,5898/0,1094
helyett). A mért kód `>> 8`-cal **csonkol** — a csere csatornánként ±1
eltérést adna az eredetitől, azaz paritás-vesztés volna.
"""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
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

#: `ID_VIEW_MACGAMMA` módazonosítója (#1730).
MAC_MODE = "mac"

#: A #1580 képernyőkép-mérése: a központi fotó lumája a Mac gammával
#: 133,5 → 154,5. Ez a pár **kereszt-ellenőrzés**, NEM a tábla forrása —
#: a forrás a binárisból kiolvasott `MAC_GAMMA_LUT` (lent). A képernyőkép
#: illesztett kitevője 0,7743 volna, a bináris tábláé 0,6945; a kettő
#: eltérése a felvétel körülményeiből (megjelenítő, tömörítés) fakad, és
#: nem ok arra, hogy képletet tegyünk mért tábla helyére (#3068).
MAC_GAMMA_SCREENSHOT_PAIR: tuple[float, float] = (133.5, 154.5)

#: `ID_VIEW_BW` módazonosítója.
BW_MODE = "bw"

#: `ID_VIEW_SEPIA` módazonosítója.
SEPIA_MODE = "sepia"

#: A luma egész súlyai R, G, B sorrendben — MÉRVE `0x009e89a0` (spec 5.7).
#: Az összegük pontosan **256**, ezért a `>> 8` fényerő-semleges.
LUMA_WEIGHTS_RGB: tuple[int, int, int] = (77, 151, 28)

#: A szépia 2. lépésének világosító szorzója — MÉRVE `0xDA` (spec 5.8).
SEPIA_LIGHTEN_MULTIPLIER = 218

#: A szépia keverőszíne R, G, B sorrendben — MÉRVE `0x9B7D63` (spec 5.8),
#: azaz `#9B7D63` = RGB(155, 125, 99).
SEPIA_BLEND_RGB: tuple[int, int, int] = (0x9B, 0x7D, 0x63)

#: A projektor mód szorzója — MÉRVE `0x009e8a10`: `0xDC` (spec 5.5).
PROJECTOR_MULTIPLIER = 220

#: Az „LCD fehérpont" szorzója — MÉRVE `0x009e8a70`: `0xF6` (spec 5.4).
#: A neve ellenére NEM fehérpont-korrekció, ld. a modul-docstringet.
LCD_MULTIPLIER = 246

#: A **Mac gamma (1,6)** keresőtáblája — **MÉRT ADAT, NEM LEVEZETÉS**.
#:
#: A bináris `0x00d32bd0` címén előre kitöltve álló 256 bájt (spec 5.9),
#: soronként 16 érték; a fájlban a `0x00932bd0` offszeten olvasható ki.
#: **Képlettel helyettesíteni tilos**: a legjobb hatványillesztés
#: (`p = 0,6945`) is 37 helyen téved.
#:
#: ⚠️ #3068: ez a tábla sokáig a LINEÁRIS módé volt nálunk, mert a spec
#: 5.9 és 5.10 szakasza fel volt cserélve. A 12.4 szerint az `ID_VIEW_MAC`
#: átalakítója (`0x009e8b40`) `0,0`-t ad át, és a `0,0`-ág választja ezt az
#: előre kitöltött táblát (`0x00aa3fd2`). A menüfelirat 1,6-ot ígér, a
#: tábla effektív gammája ≈1,44 — az eltérés az EREDETI sajátossága, és a
#: hűség a táblát követi, nem a feliratot.
MAC_GAMMA_LUT: tuple[int, ...] = (
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

#: A **lineáris gamma (2,2)** keresőtáblája — **SZÁMÍTOTT**, és ez a hű
#: alak: az eredeti ezt a táblát (`0x00d32cd0`) nem égeti be, hanem
#: futásidőben tölti fel (`0x00aa3ff0`–`0x00aa404a`) a
#: `round(pow(i/255, 1/gamma) · 255)` képlettel. Az `ID_VIEW_LINEAR`
#: átalakítója (`0x009e8b60`) a `2,2`-t adja át (`[0x00cf4140]`), tehát a
#: kitevő pontosan `1/2,2` (spec 12.4, #3068).
LINEAR_GAMMA_GAMMA = 2.2
LINEAR_GAMMA_LUT: tuple[int, ...] = tuple(
    int(round(255.0 * (ertek / 255.0) ** (1.0 / LINEAR_GAMMA_GAMMA)))
    for ertek in range(256)
)

#: A gamma-tábla `cv2.LUT`-kész alakja — egyszer épül fel, modulszinten.
_LINEAR_GAMMA_TABLE: np.ndarray = np.array(LINEAR_GAMMA_LUT, dtype=np.uint8)
_MAC_GAMMA_TABLE: np.ndarray = np.array(MAC_GAMMA_LUT, dtype=np.uint8)

#: A spec 5.3/b.5 szerinti, bizonyított szemcsemag.
DITHER16_SEED = 0x80AE2D6C

_MT_N = 624
_MT_M = 397
_MT_UPPER_MASK = np.uint32(0x80000000)
_MT_LOWER_MASK = np.uint32(0x7FFFFFFF)
_MT_MATRIX_A = np.uint32(0x9908B0DF)
_MT_ONE = np.uint32(1)
_MT_U32_MASK = np.uint32(0xFFFFFFFF)


_DARKEN_MULTIPLIERS: dict[str, int] = {
    PROJECTOR_MODE: PROJECTOR_MULTIPLIER,
    LCD_MODE: LCD_MULTIPLIER,
}

PIXEL_AFFECTING_MODES: frozenset[str] = frozenset(
    {
        OVERFLOW_MODE,
        "dither16",
        PROJECTOR_MODE,
        LCD_MODE,
        LINEAR_GAMMA_MODE,
        MAC_MODE,
        BW_MODE,
        SEPIA_MODE,
    }
)

# A részmodulok a fenti homlokzati konstansokat használják; ezért csak
# azok inicializálása után importálhatók.
from picasapy.render.display_mode_pixels import (  # noqa: E402,F401
    _LUMA_TABLE,
    _SEPIA_TABLE,
    _luma_tabla,
    _rgb_kep_e,
    _szepia_tabla,
    _tablat_alkalmaz,
    apply_display_bw,
    apply_display_sepia,
    apply_linear_gamma,
    apply_mac_gamma,
    darken,
    display_mode_changes_pixels,
    luma,
    mark_overflow,
)
from picasapy.render.display_mode_dither import (  # noqa: E402
    PicasaDitherGenerator,
    apply_dither16,
)


__all__ = [
    "annotations",
    "cv2",
    "np",
    "OVERFLOW_MODE",
    "OVERFLOW_MARK_RGB",
    "PROJECTOR_MODE",
    "LCD_MODE",
    "LINEAR_GAMMA_MODE",
    "MAC_MODE",
    "MAC_GAMMA_SCREENSHOT_PAIR",
    "BW_MODE",
    "SEPIA_MODE",
    "LUMA_WEIGHTS_RGB",
    "SEPIA_LIGHTEN_MULTIPLIER",
    "SEPIA_BLEND_RGB",
    "PROJECTOR_MULTIPLIER",
    "LCD_MULTIPLIER",
    "MAC_GAMMA_LUT",
    "LINEAR_GAMMA_GAMMA",
    "LINEAR_GAMMA_LUT",
    "DITHER16_SEED",
    "PicasaDitherGenerator",
    "PIXEL_AFFECTING_MODES",
    "display_mode_changes_pixels",
    "apply_dither16",
    "mark_overflow",
    "darken",
    "apply_linear_gamma",
    "apply_mac_gamma",
    "luma",
    "apply_display_bw",
    "apply_display_sepia",
    "apply_display_mode",
]

def apply_display_mode(rgb: np.ndarray | None, mode: str) -> np.ndarray | None:
    """A megjelenítési mód alkalmazása a MEGJELENÍTENDŐ képre.

    A nem (még) megvalósított módokra és az ismeretlen azonosítóra a képet
    változatlanul adja vissza — a hívónak nem kell módonként elágaznia.
    """
    if rgb is None:
        return None
    if mode == OVERFLOW_MODE:
        return mark_overflow(rgb)
    if mode == "dither16":
        return apply_dither16(rgb)
    multiplier = _DARKEN_MULTIPLIERS.get(mode)
    if multiplier is not None:
        return darken(rgb, multiplier)
    if mode == LINEAR_GAMMA_MODE:
        return apply_linear_gamma(rgb)
    if mode == MAC_MODE:
        return apply_mac_gamma(rgb)
    if mode == BW_MODE:
        return apply_display_bw(rgb)
    if mode == SEPIA_MODE:
        return apply_display_sepia(rgb)
    return rgb
