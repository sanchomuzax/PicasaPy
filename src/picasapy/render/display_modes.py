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
hat, a fájlhoz és a `.picasa.ini`-hez nem nyúl. A két képlet ráadásul
KÜLÖNBÖZIK (amaz lebegőpontos Rec.601), tehát a kimenetük sem azonos —
összevonni paritás-vesztés volna.

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

## A maradék öt mód

A `dither16`, `rdesk`, `mac` (és a no-op `auto`/`normal`) külön jegyeké — a
`sepia` és a `bw` a #1657 óta KIKERÜLT ebből a névsorból. A maradékra az
`apply_display_mode` **átereszt**: a menütétel a #1575 óta kattintható, de
képpontot nem mozdít. Ez szándékosan NÉMA áteresztés: a menüt nem az itteni
névsor tiltja le.

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

from picasapy import cv as cv2
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

#: A Mac gamma kitevője — a MÉRÉSBŐL, nem a menüfeliratból.
#:
#: 🟡 SZÁMÍTOTT érték, NEM mért tábla. A `LINEAR_GAMMA_LUT` (2.2) minden
#: bájtja a binárisból van kiolvasva; ez NEM az. A #1580 képpont-mérése a
#: világosítás irányát és nagyságát adta meg, a bináris tábláját nem
#: láttuk.
#:
#: ⚠️ A MENÜFELIRAT („Mac gamma (1.6)") ÉS A MÉRÉS NEM EGYEZIK. A #1730
#: jegy azt írta, hogy a mérés „konzisztens az `x^(1/1,6)` gammával" —
#: SZÁMSZERŰEN NEM AZ. A mért pár a központi fotón luma **133,5 → 154,5**;
#: ebből a kitevő:
#:
#:     ln(154,5/255) / ln(133,5/255) = 0,7743   →   gamma = 1,292
#:
#: Az `1/1,6 = 0,625` kitevő ugyanerre a bemenetre **170,2**-t adna, azaz
#: jóval világosabbat a mértnél.
#:
#: A MÉRÉST követjük, nem a feliratot: a felirat az eredeti UI szövege, a
#: 154,5 viszont a tulajdonos gépén készült felvétel képpontja. Hogy az
#: 1,6-os felirat mire vonatkozik (más színtér? a felület más rétege?),
#: NYITOTT KÉRDÉS — a jegyben rögzítve.
MAC_GAMMA_MEASURED_PAIR: tuple[float, float] = (133.5, 154.5)
MAC_GAMMA_EXPONENT = 0.7743

#: A számított tábla, hogy a futásidőben ne kelljen hatványozni.
MAC_GAMMA_LUT: tuple[int, ...] = tuple(
    int(round(255.0 * (ertek / 255.0) ** MAC_GAMMA_EXPONENT))
    for ertek in range(256)
)

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
_MAC_GAMMA_TABLE: np.ndarray = np.array(MAC_GAMMA_LUT, dtype=np.uint8)


def _luma_tabla() -> np.ndarray:
    """Csatornánkénti `súly · érték` tábla uint16-ban (spec 5.7 1. fele).

    `cv2.LUT`-kész `(1, 256, 3)` alak. A **uint16** kimenet szándékos: a
    legnagyobb részszorzat `151 · 255 = 38505` nem férne 8 bitre, a három
    csatorna összege (`65280`) viszont még uint16-ban is elfér, tehát az
    összegzés túlcsordulás nélkül, **egészben** elvégezhető.
    """
    ertekek = np.arange(256, dtype=np.uint16)
    tabla = np.empty((1, 256, 3), dtype=np.uint16)
    for csatorna, suly in enumerate(LUMA_WEIGHTS_RGB):
        tabla[0, :, csatorna] = ertekek * np.uint16(suly)
    return tabla


def _szepia_tabla() -> np.ndarray:
    """A szépia 2–4. lépése `Y`-nal indexelt `(1, 256, 3)` uint8 táblává.

    A szépia teljes egészében a lumából származik (az 1. lépés mindhárom
    csatornára ugyanazt az `Y`-t teríti szét), ezért a maradék három lépés
    **egyetlen, 256 soros keresőtáblává** előszámolható — a képpontonkénti
    munka így egy `cv2.LUT` hívás.

    A számítás végig `int32`-n megy, de minden lépés a mért **egész**
    aritmetika: `>> 8` levágás, nem osztás és nem kerekítés.
    """
    y = np.arange(256, dtype=np.int32)
    # 2. lépés — világosítás: xor 0xFF → ·218 → >>8 → xor 0xFF.
    v1 = 255 - (((255 - y) * SEPIA_LIGHTEN_MULTIPLIER) >> 8)
    # 3. lépés — a mért `((v1 >> 7) & 0x010101) · 0xFF` csatornánkénti alakja:
    # 0xFF, ha az érték felső bitje áll (≥ 128), különben 0x00.
    maszk = ((v1 >> 7) & 1) * 0xFF
    # 4. lépés — a maszkkal tükrözött érték kétszerese.
    v2 = (v1 ^ maszk) * 2
    tabla = np.empty((1, 256, 3), dtype=np.uint8)
    for csatorna, keveroszin in enumerate(SEPIA_BLEND_RGB):
        # …szorzás a szintén tükrözött keverőszínnel, `>> 8`, majd vissza.
        tabla[0, :, csatorna] = (((v2 * (keveroszin ^ maszk)) >> 8) ^ maszk).astype(
            np.uint8
        )
    return tabla


#: A luma-súlytábla — egyszer épül fel, modulszinten.
_LUMA_TABLE: np.ndarray = _luma_tabla()

#: A szépia `Y → (R, G, B)` táblája — egyszer épül fel, modulszinten.
_SEPIA_TABLE: np.ndarray = _szepia_tabla()

#: Módazonosító → a hozzá tartozó sötétítő szorzó (spec 5.4/5.5).
_DARKEN_MULTIPLIERS: dict[str, int] = {
    PROJECTOR_MODE: PROJECTOR_MULTIPLIER,
    LCD_MODE: LCD_MULTIPLIER,
}

#: Az a néhány mód, amely MA ténylegesen átírja a képpontokat. A hívó ebből
#: tudja, hogy megéri-e egyáltalán a képet numpy-tömbbé alakítania.
PIXEL_AFFECTING_MODES: frozenset[str] = frozenset(
    {
        OVERFLOW_MODE,
        PROJECTOR_MODE,
        LCD_MODE,
        LINEAR_GAMMA_MODE,
        MAC_MODE,
        BW_MODE,
        SEPIA_MODE,
    }
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


def apply_mac_gamma(rgb: np.ndarray) -> np.ndarray:
    """A `Mac gamma (1.6)` világosítása (#1730).

    A bemenet `(H, W, 3)` uint8 RGB-tömb; a visszaadott tömb **új**.

    🟡 A tábla **SZÁMÍTOTT**, nem mért. A `LINEAR_GAMMA_LUT` (2.2) a
    binárisból kiolvasott adat, ez NEM az — a #1580 képpont-mérése a
    világosítás irányát és nagyságát adta meg, a bináris tábláját nem
    láttuk. A kitevő a MÉRT párból jön (133,5 → 154,5), nem a
    menüfeliratból: az `1/1,6` ugyanerre 170,2-t adna. Ld. a
    `MAC_GAMMA_EXPONENT` melletti levezetést.

    A 0 és a 255 fixpont marad, tehát a fekete nem mosódik szürkévé, a
    fehér nem csordul ki.
    """
    if not _rgb_kep_e(rgb):
        return rgb
    return _tablat_alkalmaz(rgb, _MAC_GAMMA_TABLE)


def luma(rgb: np.ndarray) -> np.ndarray:
    """A mért egész luma `(H, W)` uint8 síkja: `(77·R + 151·G + 28·B) >> 8`.

    A számítás **végig egész**: a csatornánkénti szorzatokat egy uint16
    kimenetű `cv2.LUT` adja, az összegzés uint16-ban megy (a legnagyobb
    lehetséges összeg `65280`, tehát nem csordul túl), és a `>> 8` levágás
    — nem kerekítés. Lebegőpontos úton (`cv2.addWeighted`, `cv2.transform`
    float mátrixszal) a kerekítés miatt csatornánként ±1 eltérés keletkezne
    az eredetitől.

    ⚠️ **Előfeltétel:** a bemenet `(H, W, 3)` uint8, nem üres tömb — ez a
    függvény NEM ellenőriz. A védett belépési pont az `apply_display_bw`.
    Szándékosan nincs a `picasapy.render` csomagszintű névterében sem: ott
    a `luma` név összekeverhető volna a `glimmer_ops` LEBEGŐPONTOS,
    Rec.601-es `luma`-jával, ami egészen mást számol.
    """
    sulyozott = cv2.LUT(rgb, _LUMA_TABLE)
    osszeg = sulyozott[:, :, 0] + sulyozott[:, :, 1] + sulyozott[:, :, 2]
    return (osszeg >> 8).astype(np.uint8)


def apply_display_bw(rgb: np.ndarray) -> np.ndarray:
    """Fekete-fehér MEGJELENÍTÉSI mód: a luma mindhárom csatornára (spec 5.7).

    A bemenet `(H, W, 3)` uint8 RGB-tömb; a visszaadott tömb **új**. A
    bemenetet SOHA nem írjuk át helyben: a hívó (edit-előnézet)
    gyorsítótárazott köztes eredményt ad át, és annak megmérgezése a mód
    kikapcsolása után is szürkén hagyná a képet.

    ⚠️ **Nem azonos a szerkesztő `bw` effektjével** (`render/color.py`):
    az a mentett képre ír és a `filters=` láncba kerül, ez csak a
    képernyőre hat. A képletük is különbözik, ld. a modul-docstringet.
    """
    if not _rgb_kep_e(rgb):
        return rgb
    if rgb.size == 0:
        return rgb.copy()
    szurke = luma(rgb)
    return cv2.merge((szurke, szurke, szurke))


def apply_display_sepia(rgb: np.ndarray) -> np.ndarray:
    """Szépia MEGJELENÍTÉSI mód: a mért négylépéses műveletsor (spec 5.8).

    A bemenet `(H, W, 3)` uint8 RGB-tömb; a visszaadott tömb **új**.

    Az 1. lépés a fekete-fehér móddal azonos luma, a 2–4. lépés pedig
    `Y`-tól függ csak, ezért egyetlen előszámolt táblából (`_SEPIA_TABLE`)
    olvasható ki. A lépéssort ld. a modul-docstringben: **a nevét
    („overlay") nem valósítjuk meg, csak a mért műveleteket** — a szokásos
    overlay `/255`-tel normalizál, a mért kód `>> 8`-cal.

    ⚠️ **Nem azonos a szerkesztő `sepia` effektjével** (`render/color.py`):
    az a mentett képre ír, ez csak a képernyőre hat.
    """
    if not _rgb_kep_e(rgb):
        return rgb
    return _tablat_alkalmaz(apply_display_bw(rgb), _SEPIA_TABLE)


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
    if mode == MAC_MODE:
        return apply_mac_gamma(rgb)
    if mode == BW_MODE:
        return apply_display_bw(rgb)
    if mode == SEPIA_MODE:
        return apply_display_sepia(rgb)
    return rgb
