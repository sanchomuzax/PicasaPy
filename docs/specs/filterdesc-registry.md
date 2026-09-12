# `filterdesc.xml` — a Picasa hivatalos szűrő-regisztere

**Forrás:** `research/copy_Picasa_3_7/Picasa3/runtime/filterdesc.xml`
(63 KB, 1408 sor) — Picasa **3.9.141.259**. Feltárva: 2026-08-06.

Ez a fájl **a Picasa saját, gépi olvasásra szánt szűrő-definíciója**: mind a
**84 szűrő** azonosítója, UI-neve, üzemmódja, csúszkáinak *neve,
tartománya, eltolása és alapértéke*, valamint a 32 „Glimmer" (Picnik-örökös)
effekt **teljes képfeldolgozó-csővezetéke** — görbékkel, keverési módokkal és
csúszka→paraméter képletekkel együtt.

Eddig ezt a fájlt csak „létezik" szinten említette a
`picasa-program-resources.md`. Valójában ez **a legfontosabb egyetlen fájl a
`filters=` lánc dekódolásához** — a golden-mérésekkel kikísérletezett
összefüggések nagy részét kerek-perec kimondja.

## 0. Mit old meg azonnal

| Eddigi nyitott kérdés | Amit a `filterdesc.xml` ad |
|---|---|
| a 4–5. effektfül paraméter-jelentései (`filters-decoded.md`, Nyitva 7) | minden csúszka **neve, min–max, alapérték** és a sorrendjük |
| `finetune` (v1) és `finetune2` (v2) hőmérséklet-eltérése | **nem más algoritmus, más SKÁLA**: v1 `[-0,5..0,5]`, v2 `[-1..1]` |
| `Vignette` analitikus modellje (Nyitva 2) | belső ragyogás (inner glow), `sugár = blur·0,02·max(W,H)/4`, erősség = 2. paraméter |
| `unsharp` v1 ↔ `unsharp2` | ugyanaz az „Amount", csak a v1 felső korlátja **1,0**, a v2-é **3,0** |
| `tilt` 2. paramétere | a v1-kompatibilitás miatt fenntartott, **letiltott** (`enable="0"`) csúszka |
| miért ír a Picasa néha tizedesjegy nélküli `0`-t | a **jelölőnégyzetek** egész számként szerializálódnak |
| `tint` színparaméter-anomália (Nyitva 4) | ~~`colorwheel version` = két külön színkódolás~~ — **MEGCÁFOLVA (2026-08-15)**: a `dir_tint`/`radtint` is `version="0"`, mégis 8 hex jegyet ír |

## 1. Fájlszerkezet

```xml
<filter id="finetune2" mode="soft" zerostate="zero">
  <label>Tuning</label>
  <tooltip>…</tooltip>
  <cursor type="dropper" persist="0"/>
  <colorcircle id="0"/>            <!-- vagy <colorwheel version="0|1"/> -->
  <sliders>
    <slider id="3">
      <label>Color Temperature</label>
      <range>2.0</range>           <!-- a csúszka teljes hossza -->
      <offset>1.0</offset>         <!-- a 0-pont eltolása -->
      <default>0.6</default>
      <log>250.0</log>             <!-- logaritmikus leképezés -->
    </slider>
  </sliders>
  <presets>…</presets>
  <effect>…</effect>               <!-- csak a Glimmer-effekteknél -->
</filter>
```

### 1.1 A csúszka-matematika (a legfontosabb szabály)

A `.picasa.ini`-be **nem** a csúszka 0..1 arányos állása kerül, hanem az
eltolással korrigált érték:

```
tárolt érték ∈ [ −offset , range − offset ]
```

- `range=1.0`, nincs `offset` → `[0 .. 1]` (pl. Fill Light)
- `range=2.0`, `offset=1.0` → `[−1 .. +1]` (pl. `sat`, `finetune2` hőmérséklet, `tilt`)
- `range=1.0`, `offset=0.5` → `[−0,5 .. +0,5]` (pl. `finetune` v1 hőmérséklet, `contrast`)
- `<log>` jelenlétében a tárolt érték a **logaritmikusan leképezett tényleges**
  paraméter, nem a csúszkaállás — ezt a valós adat igazolja:
  `glow2=1,0.650000,3.000000` pontosan a két `default` érték (0,65 és 3,0),
  holott a `range` mindkettőnél 1,0.

**Ellenőrizve valós `.picasa.ini`-ken** (`research/testdata`): a `Vignette`,
`glow2`, `dir_tint` alapértelmezett sorai bájtra a `filterdesc.xml`
`default` értékeit tartalmazzák — a fájl tehát nem elméleti dokumentáció,
hanem a futásidejű igazságforrás.

### 1.2 Üzemmódok (`mode`)

| mód | jelentés | példa |
|---|---|---|
| `history` | nem képi művelet, csak a szerkesztési előzményben él | `save`, `crop64`, `rot`, `redeye`, `retouch`, `picnik` |
| `oneclick` | paraméter nélküli egykattintásos javítás | `enhance`, `autolight`, `bw`, `sepia` |
| `soft` | a „Gyakori javítások"/„Finomhangolás" fül csúszkái | `fill`, `finetune2`, `triple2` |
| `tool` | interaktív eszköz (saját vászon-interakcióval) | `tilt`, `rainbow` |
| `effect` | effekt-fül eleme | minden más |

A `zerostate` azt mondja meg, mit jelent a „nulla" állapot: `none` (nincs
alapállapot), `zero` (minden paraméter 0), `defaults` (a `default` értékek).

### 1.3 Teljesítmény- és geometria-jelzők

| attribútum | jelentés — **PicasaPy-relevancia** |
|---|---|
| `fullres="1"` | csak **teljes felbontáson** helyes (nem skálázható előnézeten) — a gyorsnézetet külön kell kezelni |
| `slow="1"` | drága művelet → külön szálon, jelzéssel |
| `resize="1"` | **megváltoztatja a kép méretét** (keret, matt, Polaroid, Cinemascope) — a downstream geometria (vágás, arcok) ezt figyelembe kell vegye |
| `rotate="1"` | forgatható irány-paramétere van (`dir_tint`) |
| `persist="1"` | régió-adatot őriz (`redeye`, `retouch`, `picnik`) |

> ⭐ **MÉRVE (2026-09-09, 225. kör): a jelzőket a `0x008ff550` olvassa be** —
> ez a `filterdesc.xml` szűrő-elem attribútum-olvasója (2807 bájt). A
> `zerostate`, `fullres`, `slow`, `resize`, `glimmer`, `persist` és további 29
> attribútumnév itt dől el, `repe cmpsb` illetve `0x0057f350` összehasonlítóval.
>
> **A tárolási mód a két jelzőnél KÜLÖNBÖZŐ, és ez mérve van:**
>
> | jelző | kód | mit tárol |
> |---|---|---|
> | `fullres` | `0x008ff726`–`0x008ff733`: `call 0x00bf6a1c` (sztring→szám), majd `mov [esp+0x2c], eax` | az **egész** értéket |
> | `slow` | `0x008ff74e`–`0x008ff75d`: ugyanaz a konverzió, majd `test eax, eax` + `setne byte [esp+0xf]` | **logikai** 0/1-et |
>
> ⇒ A két jelző tehát **nem** ugyanolyan típusú: a `fullres` szám, a `slow`
> igen/nem. A lenti értelmezések (a jelentésük) továbbra is a NÉVBŐL vannak —
> hogy ki kérdezi VISSZA a tárolt értéket, az nyitott (#2746).
>
> ⚠️ **Az index itt megtévesztett:** a `slow` a `string_xrefs` táblában
> **nem szerepel**, holott a kód összehasonlítja (`0x00cd1760`). A táblán
> mért hiányosság 26 % — ld. `binaris-regeszet-modszertan.md`.

Ez a négy jelző **eddig sehol nem volt dokumentálva**, és közvetlenül
meghatározza, hogy egy renderelő motor melyik szűrőt teheti be az „olcsó,
előnézeten is futtatható" útvonalba.

## 2. A teljes regiszter (84 szűrő)

A tartományok már az `offset`-tel korrigáltak, azaz **a `.picasa.ini`-ben
ténylegesen előforduló értéktartományt** mutatják.

| id | UI-név | mód | jelzők | csúszkák (`id=név [min..max] d=alap`) | szín | kurzor |
|---|---|---|---|---|---|---|
| `save` | Save | history | — | — | — | — |
| `crop64` | Crop | history | — | — | — | — |
| `crop` | Crop | history | — | — | — | — |
| `redeye` | Red Eye | history | persist | — | — | — |
| `retouch` | Retouches | history | persist | — | — | — |
| `picnik` | Creative Kit | history | persist | — | — | — |
| `rot` | Rotate | history | — | — | — | — |
| `debug` | Debug | effect | — | 0=Size [0..100] | — | puck |
| `triple` | Lighting Fixes | soft | — | 0=Brightness [-1..1] <br>1=Contrast [-0.5..0.5] <br>2=Fill Light [0..1] | — | — |
| `triple2` | Lighting Fixes | soft | — | 0=Fill Light [0..1] <br>1=Black Point [0..1] <br>2=White Point [0..1] d=1.0 | — | — |
| `triple3` | Lighting Fixes | soft | — | 0=Fill Light [0..1] <br>1=Highlights [0..0.48] <br>2=Shadows [0..0.48] | — | — |
| `finetune` | Tuning | soft | — | 0=Fill Light [0..1] <br>1=Highlights [0..0.48] <br>2=Shadows [0..0.48] <br>3=Color Temperature [-0.5..0.5] | colorcircle | dropper |
| `finetune2` | Tuning | soft | — | 0=Fill Light [0..1] <br>1=Highlights [0..0.48] <br>2=Shadows [0..0.48] <br>3=Color Temperature [-1..1] | colorcircle | dropper |
| `colorfix` | Color Fixes | soft | — | 0=Choose White Point (rejtett) <br>1=Color Temperature [-0.5..0.5] | colorcircle | dropper |
| `autobacklight` | Fill Light | oneclick | — | — | — | fix 25%-os Derítőfény (#567) |
| `autolight` | Auto Contrast | oneclick | — | — | — | — |
| `autocolor` | Auto Color | oneclick | — | — | — | — |
| `bw` | B&W | oneclick | — | — | — | — |
| `enhance` | I'm Feeling Lucky | oneclick | — | — | — | — |
| `warm` | Warmify | oneclick | — | — | — | — |
| `grain` | Film Grain (Old) | oneclick | — | — | — | — |
| `grain2` | Film Grain | oneclick | fullres+slow | — | — | — |
| `sepia` | Sepia | oneclick | — | — | — | — |
| `unsharp` | Sharpen (Old) | effect | — | 0=Amount [0..1] d=0.6 | — | — |
| `unsharp2` | Sharpen | effect | fullres+slow | 0=Amount [0..3] d=0.6 | — | — |
| `autocontrast` | Auto Contrast | oneclick | — | — | — | — |
| `tilt` | Straighten | tool | — | 0=— [-1..1] d=0.0 (rejtett) <br>1=— (rejtett, v1-kompat) | — | — |
| `rainbow` | Rainbow | tool | — | 0=— [0..256] d=0.0 | — | — |
| `radblur` | Soft Focus | effect | — | 0=Size [-1..1] <br>1=Amount [-1..1] | — | puck |
| `radsat` | Focal B&W | effect | — | 0=Size [-1..1] <br>1=Sharpness [0..1] | — | puck |
| `linblur` | Linear Blur | effect | — | 0=Amount [0..10] d=2.0 | — | puck |
| `ansel` | Filtered B&W | effect | — | — | colorwheel v1 | — |
| `tint` | Tint (Old) | effect | — | 0=Color Preservation [-1..255] | colorwheel v0 | — |
| `dir_tint` | Graduated Tint | effect | rotate | 0=Feather [0..1] d=0.25 <br>1=Shade [0..1] d=0.25 | colorwheel v0 | puck |
| `radtint` | Radial Tint | effect | — | 0=Feather [0..1] d=0.25 | colorwheel v0 | puck |
| `glow` | Glow (Old) | effect | — | 0=Intensity [0..1] d=0.65 <br>1=Radius d=3.0 (log 250) | — | — |
| `glow2` | Glow | effect | fullres+slow | 0=Intensity [0..1] d=0.65 <br>1=Radius d=3.0 (log 250) | — | — |
| `sat` | Saturation | effect | — | 0=Amount [-1..1] d=0.1618 | — | — |
| `colortemp` | Color Temperature | effect | — | 0=Cool to Warm [-0.5..0.5] d=0.125 <br>1=White Shift [0..1] | — | — |
| `shadow` | Shadow & Highlight | effect | — | 0=Radius (log 250) <br>1=Shadow % [0..1] <br>2=Highlight % [0..1] | — | — |
| `blur` | Blur | effect | — | 0=Threshold [-0.5..0.5] d=0.1 | — | — |
| `contrast` | Contrast | effect | — | 0=Contrast [-0.5..0.5] d=0.1 | — | — |
| `gamma` | Gamma Correct | effect | — | 0=Level [-1..1] d=0.1618 | — | — |
| `backlight` | Backlight Fix | effect | — | 0=Amount [0..1] d=0.25 | — | — |
| `fill` | Fill Light | soft | — | 0=— [0..1] d=0.0 (rejtett) | — | — |
| `whitept` | Whitepoint | effect | — | 0=Choose Whitepoint Color (rejtett) | colorcircle | dropper |
| `dir_sat` | Directional Saturation | effect | — | 0=Left to Right [-1..1] <br>1=Top to Bottom [-1..1] | — | puck |
| `dir_brite` | Directional Brightness | effect | — | 0=Left to Right [-1..1] <br>1=Top to Bottom [-1..1] | — | puck |
| `dir_sharp` | Directional Sharpen | effect | — | 0=Left to Right [-1..1] <br>1=Top to Bottom [-1..1] | — | puck |
| `focalpixelate` | Focal Pixelate | effect | — | 0=Pixel Size [0..100] d=15 <br>1=Focal Size [0..2] d=1.0 <br>2=Edge Hardness [0..0.95] d=0.25 <br>3=Fade [0..1] d=0.0 | — | puck — **HALOTT (legacy)**: a 3.9.141.259 natív regiszterében nincs hozzá se callback, se névregisztráció (#567); NEM azonos az élő `PicnikFocalPixelate`-tel |
| `Boost` | Boost | effect | — | ld. 4. pont | — | — |
| `Border` | Border | effect | resize | ld. 4. pont | — | — |
| `Cinemascope` | Cinemascope | effect | fullres+resize | ld. 4. pont | — | — |
| `Comicize` | Comic Book | effect | fullres+slow | ld. 4. pont | — | — |
| `CrossProcess` | Cross Process | effect | fullres | ld. 4. pont | — | — |
| `DropShadow` | Drop Shadow | effect | fullres+slow+resize | ld. 4. pont | — | — |
| `PicnikFocalPixelate` | Focal Pixelate | effect | fullres | ld. 4. pont | — | puck — **ini-aritása 7** (puck + 5 vezérlő), és a #685 szettje sosem ezt próbálta: ld. 4.1/b és 4.1/c (#2456) |
| `FocalZoom` | Focal Zoom | effect | fullres | ld. 4. pont | — | puck |
| `PicnikGrain` | Film Grain | effect | fullres+slow | ld. 4. pont | — | — |
| `HDR` | HDR-ish | effect | fullres+slow | ld. 4. pont | — | — |
| `HeatMap` | Heat Map | effect | fullres | ld. 4. pont | — | — |
| `Holga` | Holga-ish | effect | fullres+slow | ld. 4. pont | — | — |
| `Invert` | Invert Colors | effect | — | — | — | — |
| `IR` | Infrared Film | effect | — | ld. 4. pont | — | — |
| `LocalContrast` | Local Contrast | effect | — | ld. 4. pont | — | — |
| `Lomo` | Lomo-ish | effect | fullres+slow | ld. 4. pont | — | — |
| `Matte` | Matte | effect | — | ld. 4. pont | — | — |
| `MuseumMatte` | Museum Matte | effect | resize | ld. 4. pont | — | — |
| `Neon` | Neon | effect | fullres+slow | ld. 4. pont | — | — |
| `NightVision` | Night Vision | effect | — | ld. 4. pont | — | — |
| `Orton` | Orton-ish | effect | fullres+slow | ld. 4. pont | — | — |
| `PencilSketch` | Pencil Sketch | effect | fullres+slow | ld. 4. pont | — | — |
| `Pixelate` | Pixelate | effect | fullres | ld. 4. pont | — | — |
| `Polaroid` | Polaroid | effect | resize | ld. 4. pont | — | — |
| `QuantizePalette` | Posterize | effect | fullres+slow | ld. 4. pont | — | — |
| `ReanimatedEyeColor` | Ghoul Eye | effect | — | ld. 4. pont | — | — |
| `RoundedEdges` | Rounded Edges | effect | — | ld. 4. pont | — | — |
| `Sixties` | 1960's | effect | — | ld. 4. pont | — | — |
| `Soften` | Soften | effect | — | ld. 4. pont | — | — |
| `PicnikTint` | Tint | effect | — | ld. 4. pont | — | — |
| `TwoTone` | Duo-Tone | effect | — | ld. 4. pont | — | — |
| `Vignette` | Vignette | effect | — | ld. 4. pont | — | — |
| `moviestart` | Start Point | oneclick | — | — | — | — |
| `movieend` | End Point | oneclick | — | — | — | — |

**Új szűrők, amelyek eddig egyik specben sem szerepeltek:** `triple`,
`triple2`, `triple3`, `colorfix`, `autobacklight`, `autocontrast`,
`rainbow`, `linblur`, `radtint`, `colortemp`, `shadow`, `blur`, `contrast`,
`gamma`, `backlight`, `whitept`, `dir_sat`, `dir_brite`, `dir_sharp`,
`focalpixelate`, `debug`, `save`, `rot`, `crop`, `moviestart`, `movieend`.
Ezek egy része a UI-ban nem érhető el (fejlesztői/örökölt), de a
`filters=` láncban **előfordulhat régi könyvtárakban** — az ini-parszernek
ismernie kell őket a round-triphez.

## 3. A natív szűrők paraméter-sorrendje

A `<presets>` blokk `real id`/`pixel` indexei **NEM** az ini-beli sorrendet
adják (ez tévútnak bizonyult). A valós `.picasa.ini`-adat a mérvadó:

```
radblur=1,0.500000,0.500000,0.300000,0.500000     → x, y, Size, Amount
dir_tint=1,0.432422,0.554167,0.250000,0.250000,ffffffff
                                                  → x, y, Feather, Shade, szín
glow2=1,0.650000,3.000000                         → Intensity, Radius
tint=1,79.842102,ffff                             → Color Preservation, szín
ansel=1,ffffffff                                  → szín
```

Szabály: **`puck` kurzoros szűrőnél a fókuszpont (x, y) megy elöl**, utána a
csúszkák `id` sorrendben, a színparaméter a végén. A `dir_tint` mért
alapértékei (0,25 / 0,25) pontosan a `filterdesc.xml` `default` értékei —
a csúszkanevek tehát ezzel a sorrenddel egyeznek.

**Színformátum-figyelmeztetés:** a `tint` `ffff` (4 hex), az `ansel` és a
`dir_tint` `ffffffff` (8 hex). A parszernek **változó hosszú** hex-színt kell
elfogadnia.

> ~~A `colorwheel` verziókülönbsége (v0 vs v1) magyarázza a hex-hosszt.~~
> **MEGCÁFOLVA (2026-08-15):** a fenti táblázat szerint a `dir_tint` és a
> `radtint` **is `version="0"`**, mégis 8 jegyet ír. A `version` és a
> hex-hossz nem korrelál. A legvalószínűbb magyarázat prózai: az író
> **elhagyja a vezető nullákat**. Részletek és a színkezelés-lelet:
> [`filters-decoded.md`](filters-decoded.md), `tint` szakasz.

## 4. Glimmer-effektek — a teljes csővezeték

A 32 „Glimmer" effekt (a Picnik-felvásárlásból örökölt réteg) `<effect>`
blokkja **deklaratív képfeldolgozó-gráf**: vezérlők (csúszka, színválasztó,
jelölőnégyzet) + `imageOperations:` műveletek, adatkötés-kifejezésekkel
(`{_sldrImpact.value * 20 / 50}`). Ez gyakorlatilag **az effektek
forráskódja** — de csak a *recept*, nem a pixel-szemantika (ld. 4.4).

### 4.1 A `.picasa.ini` paraméter-sorrend szabálya

A vezérlők deklarációs sorrendjéből és a valós ini-mintákból levezetve:

> **Először a numerikus csúszkák** (deklarációs sorrendben, legfeljebb
> háromig), **utána a színek** (deklarációs sorrendben), **utána a maradék
> numerikus**, végül a **jelölőnégyzetek egész számként**.

Ellenőrzés a valós mintákon:

| ini-minta | leképezés |
|---|---|
| `Vignette=1,35.000000,1.400000,0.000000,00000000` | Blur=35, Strength=1,4, Fade=0, szín=fekete — **mind a négy a `filterdesc` alapértéke** ✅ |
| `MuseumMatte=1,25.0,40.0,001a0e03,00f0eae4` | OuterThickness=25, InnerThickness=40, külső szín, belső szín ✅ |
| `TwoTone=1,0.0,20.0,0.0,00004488,00ffff00` | Brightness, Contrast, Fade, fekete-szín, fehér-szín ✅ |
| `Holga=1,70.0,30.0,0.0` | Blur=70, Grain=30, Fade=0 ✅ |
| `QuantizePalette=1,8.0,80.0,0.0` | Steps=8, Smoothing=80, Fade=0 ✅ |
| `Sixties=1,20.0,00ffffff,0` | Fade=20, szín, **Rounded jelölő = 0** (tizedes nélkül!) ✅ |
| `Border=1,20.0,5.0,0.0,00000000,00ffffff,0.0` | 3 szám, 2 szín, majd a **4. szám** (CaptionHeight) ✅ |
| `DropShadow=1,4.0,90.0,10.0,00000000,00ffffff,30.0` | Distance, Angle, Blur, 2 szín, majd Fade ✅ |

**Ez zárja le a `filters-decoded.md` „Nyitva 7" pontját** — a
`tools/golden/make_param_sweep.py` találgatott tartományai helyett most
egzakt min/max/alapérték áll rendelkezésre; a sweep innentől nem felfedezés,
hanem **ellenőrzés**.

Két nyitott részlet:
- `Cinemascope=1,0` — az egyetlen paraméter a Letterbox jelölő, de a
  `filterdesc` alapértéke `true`, az ini-ben `0` áll. A polaritás
  ellenőrizendő egy célzott exporttal.
- `FocalZoom=1,0.5,0.5,50.0,50.0,50.0,0.0` — itt a **puck (x, y) elöl** van,
  a natív szűrők mintájára; a `PicnikFocalPixelate`-ra **továbbra sincs valós
  mintánk**, és a #685 szettje sem adta meg neki a saját alakját — ld. 4.1/b.

### 4.1/b A paraméter-aritás SZABÁLYA, és az egyetlen szűrő, amely sosem kapta meg a magáét (2026-09-05, #2456)

**A szabály:** egy Glimmer-effekt `.picasa.ini`-alakja pontosan

    <vezérlőszám> + (van puck ? 2 : 0)

értéket visz az engedélyező `1` után; a puck (x, y) elöl, utána a vezérlők a
`filterdesc.xml`-beli **deklarációs sorrendben** (a jelölők is, záró
`0`/`1`-ként — pl. `Sixties`, `PicnikGrain`).

**Mérve** a `referencia/meroszett-685-verdikt.json` (178 tétel) és a
`filterdesc.xml` összevetésével: a szettben szereplő **31 Glimmer-effektből 30**
pontosan ennyi értéket kapott, és mind a 30-nak volt ható esete. A kivétel:

| effekt | vezérlők | puck | a szabály szerinti aritás | amit a szett próbált |
|---|---|---|---|---|
| `FocalZoom` | 4 | ✔ | **6** | 6 → lefut (ΔE 7,61) |
| `Pixelate` | 3 | — | **3** | 3 → lefut (ΔE 7,96 / 23,30) |
| `PicnikGrain` | 2 | — | **2** | 2 → lefut (ΔE 3,09 / 14,24) |
| `PicnikTint` | 2 | — | **2** | 2 → lefut (ΔE 36,93) |
| **`PicnikFocalPixelate`** | **5** | ✔ | **7** | **1 · 4 · 6 — hetes alak SOHA** |

A `PicnikFocalPixelate` ötödik vezérlője a `_chkReverse` jelölő
(`filterdesc.xml:869`), amit a korábbi leírásaink kihagytak; a szett hatos
alakja a **`FocalZoom` vezérlőkészletét** másolta, nem ezét.

**Rövid lista sehol nem hatott.** A `meroszett-685-2kor.json` „halott”
csoportjában **9 rövid alak** futott le (`blur`, `colorfix`, `whitept`,
`triple`, `focalpixelate`), és **mind a 9 tétlen maradt** — köztük a
`triple=1;`, holott ugyanaz a `triple` a saját hármas alakján **ΔE 21,42**-t
ad. ⇒ A rövid alaknál a „nem történt semmi” a **lista hosszára** bizonyíték,
nem a szűrőre.

**Következmény:** az az állítás, hogy „a 3.9.141.259 a `PicnikFocalPixelate`-et
sem futtatja le” (#1142, `chain.MEASURED_NOT_RUNNING_OPS`), **kizárólag rövid
alakokon nyugszik**, tehát nem megalapozott. Egyetlen export dönti el:

    PicnikFocalPixelate=1,0.500000,0.500000,40.000000,60.000000,50.000000,0.000000,0.000000;

(`Reverse = 0` mellett a hatás a körön KÍVÜL jelentkezik, tehát a kép nagy
részén — összetéveszthetetlen.) Jegy: **#2456** (`blocked`).

### 4.1/c A `PicnikFocalPixelate` teljes műveletgráfja (`filterdesc.xml:859–886`)

A szállított leíró a teljes algoritmust megadja — ez nem következtetés,
hanem a fájl tartalma:

| lépés | mit ad |
|---|---|
| `CircularGradientImageMask` (`:870`) | `xCenter/yCenter` = a puck (`xFocus`, `yFocus`); `innerRadius = Radius · Hardness/101`; `outerRadius = Radius · (2 − Hardness/101)`; `outerAlpha = Reverse ? 0 : 1`, `innerAlpha = Reverse ? 1 : 0` |
| `NestedImageOperation` (`:871`) | `BlendAlpha = 1 − Fade/100`, **`Mask = {_msk}`**, `dynamicAlphaCachePriority = 10` |
| 1. gyerek `ResizeImageOperation` (`:873`) | `W/Impact × H/Impact`, `ignoreObjects="true"` |
| 2. gyerek `ResizeImageOperation` (`:874`) | vissza `W × H`-ra, **`smoothing="false"`** (legközelebbi szomszéd) |

Csúszkák (`:865–869`): `Impact` 2–100 (alap 20) · `Radius` 10–`min(W,H)/2`
(alap a tartomány közepe) · `Hardness` 0–100 (alap 50) · `Fade` 0–100 (alap 0)
· `Reverse` jelölő (alap ki). `<presets>`: `8 · 20 · 90 · 0,5 · 0,5` — a
`FocalZoom` presetjének mintájára `Impact · Radius · Hardness · puckX · puckY`
(a `Fade` és a `Reverse` nincs benne).

⭐ **Kimerítő pásztázás mind a 84 szűrőn:** a `PicnikFocalPixelate` az
**egyetlen**, ahol egy számított `CircularGradientImageMask` magán a
`NestedImageOperation`-ön ül. A másik három `CircularGradientImageMask`-használó
(`FocalZoom` `:898`, `Holga` `:971`, `Lomo` `:1045`) a **gyerekre** köti; a
másik két `Mask`-os `Nested` (`Pixelate` `:1199`, `ReanimatedEyeColor` `:1283`) a
festő-maszkot (`_mctr.mask`) használja. Ez a szerkezeti egyediség a
legerősebb jelöltje annak, hogy a lánc-úton miért maradhatna tétlen — de
**nincs megmérve**, ezért csak jelölt.

⛔ **Negatív lelet, hogy ne járja újra senki:** a `Picasa3.exe` hivatkozik a
`runtime\picnik_effects\` könyvtárra (`0x00c7f168`, hívók: `0x004051b0`,
`0x0053fe30`) és a `%s%sEffect.mxml` formátumsztringre (`0x00cd1788`) — mindkettőt a
`<filter>`-olvasó `0x008ff550` használja, a `Picnik` sztringgel (`0x00cd1780`)
egy kódblokkban: `0x008ff8c1` (`Picnik`) és `0x008ff907` (a formátumsztring)
70 bájtra egymástól — **a szállított telepítésben ez a könyvtár nem
létezik**
(`research/copy_Picasa_3_7/Picasa3/runtime/`: csak `geotag/` és `slingshot/`).
A `PicnikGrain` és a `PicnikTint` viszont MÉRTEN lefut ⇒ a hiányzó
`picnik_effects/` **nem** magyarázza a tétlenséget, és a `Picnik` előtagú
nevet a lánc felismeri.

#### 4.1/d Az `.mxml`-ág teljesen kimérve (#2599) — **tartalék-ág NINCS**

A `0x008ff8bf`–`0x008ff9d9` blokk pontos működése, utasításról utasításra
(`eszkozok/pe_dis.py`; a `Picasa3.exe` 3.9.141.259):

| lépés | cím | mit tesz |
|---|---|---|
| előtag levágása | `0x008ff8c1` → `0x009870d0` | a szűrőnévről lehúzza a `Picnik` előtagot |
| név összeállítása | `0x008ff907` → `0x0040eab0` | `"%s%sEffect.mxml" % (könyvtár, csonkolt név)` |
| fájlnyitás | `0x008ff927` → `0x00991490` | a `yt` I/O megnyitja a fájlt |
| elágazás | `0x008ff92f` `test eax,eax` / `jne 0x008ff9d9` | **hibakód ≠ 0 → takarít és kilép** |
| feldolgozó | `0x008ff937`–`0x008ff989` | 0x2c bájtos objektum + `0x00cefc14` vtábla |

**A `0x00991490` VISSZATÉRÉSI ÉRTÉKE HIBAKÓD, nem mutató — 0 a siker.**
Bizonyítékok, egymástól függetlenül:

1. hibaágon `GetLastError()` (`0x00c4025c`) → `0x0099cd30`, ami egy
   **ugrótáblával** kis egészre képezi le a Win32 hibakódot
   (`2`, `0x0a`…`0x0e`) — nem foglal, nem ad vissza mutatót;
2. `0x0099cde0(kód, útvonal, ".\yt\ytIO.cpp", 417)` a naplózó: csak akkor
   ír, ha `kód != 0 && kód != 0x0a` — a nullát kifejezetten sikerként kezeli;
3. a `0x00991490` **mind a négy hívója** ugyanígy olvassa: `0x006376dd`
   (`jne` → átugorja a munkát), `0x00971698` (átadja tovább), és a
   `0x0099166e`, amely `jne` után **felszabadítja az erőforrást és
   visszaadja a kódot** — ez a klasszikus státusz-propagálás.

⇒ **A `0x00cefc14`-es objektum az `.mxml` SIKERES megnyitásakor épül fel,
nem a hiányakor.** A jegy (#2599) eredeti olvasata — „ha a keresés nem
talál, van tartalék-ág" — **fordítva olvasta az elágazást**. Ezen az úton
`.mxml` nélkül **semmi nem fut**.

**A `0x00991490` maga is kimérve:** a `0x00d69520` rekeszen át hív, ami egy
NT/9x kapcsoló (`0x00c331c0`): `GetVersion` (`0x00c40450`) < `0x80000000` →
`0x009afe60` (UTF-8 → UTF-16 `MultiByteToWideChar` CP 65001, majd
`CreateFileW`), különben a `KERNEL32!CreateFileA` IAT-rekesz (`0x00c40424`).
A paraméterek: `GENERIC_READ` · `FILE_SHARE_READ` · `OPEN_EXISTING` ·
`FILE_ATTRIBUTE_NORMAL`. ⇒ **valódi fájlrendszer-nyitás**, nem
erőforrás-tábla és nem regisztrált gyár.

**A `0x00cefc14` osztálya (RTTI-vel feloldva):** teljes objektum-lokátor
`0x00d1b6e4`, típusleíró `0x00d485e8` =
`.?AVEffectParserHandler@glimmer@@` → **`glimmer::EffectParserHandler`**,
két ősosztállyal: önmaga és `.?AVHandler@EffectParser@glimmer@@`
(`glimmer::EffectParser::Handler`). Vagyis az `.mxml` **SAX-stílusú
feldolgozójának eseménykezelője** — pontosan az, amire egy megnyitott
XML-fájlhoz szükség van.

**Az előtag-levágás mostantól MÉRT, nem „erős":** a `0x009870d0` előbb
`0x00987030`-cal ellenőrzi az előtagot, majd `strlen`-nel kiszámolja a
hosszát és `0x00986120`-szal levágja a sztring elejéről. Tehát a keresett
fájl `runtime\picnik_effects\<név a Picnik nélkül>Effect.mxml` —
`PicnikGrain` → `GrainEffect.mxml`.

#### 4.1/e A MÁSIK út: az `<effect>` blokk a `filterdesc.xml`-ben (#2636)

A #2599 nyitva hagyta, hogy `.mxml` nélkül MI futtatja a `PicnikGrain`-t és
a `PicnikTint`-et. A válasz a lehető legegyszerűbb: **nincs másik
mechanizmus — az effekt leírása MAGÁBAN a `filterdesc.xml`-ben áll,
inline.**

Számolva a szállított
`research/copy_Picasa_3_7/Picasa3/runtime/filterdesc.xml`-en:

| tétel | darab |
|---|---|
| `<filter>` összesen | **84** |
| ebből inline `<effect>` blokkal | **32** |
| `Picnik` előtagú, `<effect>` blokk NÉLKÜL | **0** |

⇒ pontosan a 32 Glimmer-effekt kapja az `<effect>`-et, és **mind a három
`Picnik*` szűrő köztük van** — a `PicnikFocalPixelate` is.

A `PicnikGrain` teljes leírása például (a fájlból, változatlanul):

```xml
<effect>
  <cnt:EffectCanvas>
    <Variable id="grain.val" val="{_radioLighten.selected?2.55*_sldrGrain.value:255-2.55*_sldrGrain.value}"/>
    <HSliderPlus minimum="0" maximum="50" value="10" id="_sldrGrain"/>
    <mx:CheckBox id="_radioLighten" groupName="_rGroup"/>
    <imageOperations:NestedImageOperation id="_op" BlendAlpha="1" BlendMode="{...}" maskWithSourceAlpha="true">
      <imageOperations:children>
        <imageOperations:NoiseImageOperation randomSeed="1" low="{...}" high="{...}" channelOptions="7" grayScale="true"/>
      </imageOperations:children>
    </imageOperations:NestedImageOperation>
  </cnt:EffectCanvas>
</effect>
```

⇒ **A `runtime\picnik_effects\<név>Effect.mxml` fájl nem forrás, hanem
FELÜLÍRÁS.** A `<filter>`-olvasó (#2599) előbb megpróbálja megnyitni; ha
megvan, azt dolgozza fel, ha nincs, marad az inline blokk. A szállított
telepítésben a könyvtár nem létezik, tehát **mind a 32 effekt az inline
leírásból fut**.

**A végrehajtó natívan bent van.** Az `.mxml` nyelvjárás minden eleméhez
tartozik RTTI-vel azonosított C++ osztály a `Picasa3.exe`-ben — nem
értelmezett szkript, hanem osztály-gyár:

* **31 műveleti osztály**, `glimmer::…ImageOperation` alakban: `Blend`,
  `Blur`, `Rotate`, `Shader`, `QuantizePalette`, `ColorMatrix`,
  `SimpleColorMatrix`, `MultiplyColorMatrix`, `EdgeDetectionSobel`,
  `EdgeDetectionB`, `PaletteMap`, `GradientMap`, `HSVGradientMap`, `Glow`,
  `AdjustCurves`, `DropShadow`, `Nested`, `Pixelate`, `Tint`, `Crop`, `BW`,
  `Border`, `SimpleBorder`, `Noise`, `GetVar`, `Sharpen`, `Exposure`,
  `RadialBlur`, `TwoTone`, `AutoFix`, `Resize`, `IR`, `LocalContrast`
  (`0x00d4866c`…`0x00d48e18`);
* **13 utasítás**: `Op`, `NamedVar`, `ReExecuting`, `ClearVar`, `GetVar`,
  `Dupe`, `SetVar`, `Blend`, `Apply`, `PartialMask`, `MaskWithSourceAlpha`,
  `Mask`, `Pop` (`0x00d44ac0`…`0x00d48fc8`);
* maszkok és vezérlők: `ImageMask`, `TiledImageMask`,
  `ShapeGradientImageMask`, `CircularGradientImageMask`,
  `PaintMaskPlusImageMask`, `Slider`, `StaticRangeSlider`,
  `DynamicRangeSlider`, `BrushSizeSlider`, `Button`, `RadioButton`,
  `EraserButton`, `ColorPicker`, `Control`, `Parameter`, `Brush`,
  `CircularBrush`.

### Amit ez a #1142 / #2456 kérdésére mond

**Az út GENERIKUS**, és ezen az úton **semmi nem különbözteti meg** a
`PicnikFocalPixelate`-et: neki is van inline `<effect>`-je
(`filterdesc.xml`, a `CircularOverlayEffectCanvas`-szal és a
`CircularGradientImageMask` + kétlépcsős `Resize` gráffal), ugyanúgy, mint
a mérten LEFUTÓ `PicnikGrain`-nek és `PicnikTint`-nek.

⇒ A tétlensége **nem a betöltési útból** ered. A #1142
`MEASURED_NOT_RUNNING` verdiktje ezzel se nem igazolódik, se nem dől meg;
a #2456 helyesbítése (a hetes alakkal még nem mértünk) érvényben marad.

### 4.2 Vezérlők effektenként (min–max–alap)

| effekt | vezérlők deklarációs sorrendben |
|---|---|
| `Boost` | Impact 0–100 (50) |
| `Border` | szín Outer (#000), OuterThickness 0–100 (20), szín Inner (#fff), InnerThickness 0–100 (5), CornerRadius 0–min(W,H)/2 (0), CaptionHeight 0–H/6 (0) |
| `Cinemascope` | Letterbox jelölő (be) |
| `Comicize` | BlurXY 0–100 (20), DotContrast 0–100 (50), DotFade 0–100 (50) |
| `CrossProcess` | Fade 0–100 (0) |
| `DropShadow` | szín Shadow (#000), Distance 0–30 (4), Angle 0–360 (90), Blur 0–100 (10), Fade 0–100 (30), szín Background (#fff) |
| `PicnikFocalPixelate` | Impact 2–100 (20), Radius 10–min(W,H)/2 (közép), Hardness 0–100 (50), Fade 0–100 (0), Reverse jelölő (ki) |
| `FocalZoom` | Impact 1–100 (50), Radius 10–min(W,H)/2 (közép), Hardness 0–100 (50), Fade 0–100 (0) |
| `PicnikGrain` | Grain 0–50 (10), Lighten jelölő (ki) |
| `HDR` | Radius 1,3–80 (20), Contrast 1–7 (3), Fade 0–100 (0) |
| `HeatMap` | Hue −180–180 (0), Fade 0–100 (0) |
| `Holga` | Blur 0–100 (70), Grain 0–100 (30), Fade 0–100 (0) |
| `Invert` | — |
| `IR` | Fade 0–100 (0) |
| `LocalContrast` | Radius 1,3–40 (15), Contrast 1–3 (1,5) — a `Contrast = 1` a NULLA-ÁLLAPOT, a művelet `Strength`-je `Contrast − 1` (#688, ld. 4.3) |
| `Lomo` | Blur 0–100 (50), Fade 0–100 (0) |
| `Matte` | Blur 0–50 (40), Strength 1–2 (1,2), szín (#fff), Fade 0–100 (0) |
| `MuseumMatte` | szín Outer (#1a0e03), OuterThickness 0–100 (25), szín Inner (#f0eae4), InnerThickness 0–100 (40) |
| `Neon` | szín (#f00), Fade 0–100 (0) |
| `NightVision` | Brightness −50–50 (0), Contrast −50–50 (0), Fade 0–100 (0) |
| `Orton` | Bloom 0–50 (25), Brightness 0–100 (50), Fade 0–100 (0) |
| `PencilSketch` | Radius 1,3–5 (2), Contrast 0–200 (100), Fade 0–100 (0) |
| `Pixelate` | Impact 2–150 (20), BlendMode 0–9 (9), Fade 0–100 (0) |
| `Polaroid` | szín Outer (#E2E2E2), Rotate −10–10 (5) |
| `QuantizePalette` | Steps 2–30 (8), Smoothing 0–100 (80), Fade 0–100 (0) |
| `ReanimatedEyeColor` | Blur 0–30 (6), Fade 0–100 (20) + ecset (festhető maszk, **ÜRESEN indul** — befestés nélkül az effekt tétlen, #688) |
| `RoundedEdges` | szín Outer (#fff), CornerRadius 0–min(W,H)/2 (min(W,H)/10) |
| `Sixties` | Rounded jelölő (be), szín Outer (#fff), Fade 0–100 (20) |
| `Soften` | Impact 0–100 (50), Fade 0–100 (50) + festhető maszk |
| `PicnikTint` | szín (#80cfff), Fade 0–100 (0) + festhető maszk |
| `TwoTone` | szín Black (#004488), szín White (#ffff00), Brightness −95–95 (0), Contrast 0–100 (20), Fade 0–100 (0) |
| `Vignette` | Blur 0–50 (35), Strength 1–2 (1,4), szín (#000), Fade 0–100 (0) |

A `Fade` mindenütt ugyanazt jelenti: a művelet átlátszósága
`BlendAlpha = 1 − Fade/100`. Ez **egységes implementációs mintát** ad: a
PicasaPy minden Glimmer-effektet „alap-effekt + globális keverési alfa"
formában rakhat össze.

### 4.3 Kiemelt algoritmusok (a csővezetékből kiolvasva)

- **`Vignette`** és **`Matte`**: ugyanaz a művelet (`GlowImageOperation`),
  csak fekete vs fehér színnel és más alapértékekkel. (Az XML `innerglow="true"`
  attribútuma **halott** — a natív motor nem olvassa ki; ld. lent.)
  `xblur = yblur = Blur · 0,02 · max(W,H) / 4`, `strength = Strength`.
  **Ez a `filters-decoded.md` „Nyitva 2" pontjának megoldása** — a korábban
  csak *mért* radiális profil mögötti tényleges modell.
- **`HDR`** = `LocalContrastImageOperation(Radius, Strength)` — semmi más.
  A `LocalContrast` effekt ugyanezt bontja ki explicit lépésekre:
  `orig − blur(r)`, `× Strength`, visszaadás — klasszikus unsharp-jellegű
  helyi kontraszt.
  **A két effekt `Strength`-je viszont NEM ugyanaz (#688).** A `HDR` a
  csúszkát közvetlenül adja tovább; a `LocalContrast`-nál a csúszka `[1..3]`
  tartományának ALSÓ vége a nulla-állapot, azaz `Strength = Contrast − 1`.
  A #685 mérőszettjének valódi Picasa-exportján mérve (modell ↔ Picasa,
  ΔE CIE76 átlag):

  | eset | Picasa Δ az eredetitől | `s = Contrast` | `s = Contrast − 1` |
  |---|---|---|---|
  | `LocalContrast` min (R 1,3 / C 1,0) | 0,18 (= JPEG-zaj, tétlen) | 1,85 | **0,18** |
  | `LocalContrast` alap (R 15 / C 1,5) | 3,08 | 2,24 | **0,37** |
  | `LocalContrast` max (R 40 / C 3,0) | 9,43 | 2,77 | **0,87** |
  | `HDR` alap (R 20 / C 3,0) | 7,48 | **1,24** | 1,71 |

  Vagyis az eltolás a `LocalContrast`-on mindhárom állást megjavítja, a
  `HDR`-en viszont ront — ezért kizárólag a `LocalContrast` kapja meg.
- **`Invert`** = egyetlen mestergörbe `(0,255) → (255,0)`.
- **`CrossProcess`**: fix csatornagörbék
  R `(0,0)(60,30)(210,255)(255,255)`, G `(0,0)(47,38)(101,111)(187,206)(255,255)`,
  B `(0,32)(255,216)`; utána `Contrast +10`, `Brightness +10`, majd
  `#fcff00` szorzó-színezés 0,2 alfával.
- **`Sixties`**: `AutoFix` → mester `(0,0)(150,104)(243,255)` +
  R `(0,59)(96,156)(210,255)`, G `(0,22)(150,166)(255,216)`,
  B `(0,9)(126,98)(255,231)` → szemcse (235–255, szorzó, 0,6) → lekerekített
  sarok `min(W,H)/14`.
- **`Cinemascope`**: 1,7:1 vágás → 95%-os függőleges zsugorítás → `AutoFix`
  → `Saturation −25` → mester `(0,0)(29,19)(110,150)(233,245)(255,255)` →
  szemcse → 15–15% fekete letterbox-sáv.
- **`Orton`**: `overlay`-módú elmosás (Bloom) + mester középpont-emelés
  `(128, 128 + (Brightness−50)·1,5)`.
- **`PencilSketch`**: B&W → AutoFix → invertált elmosás `add` módban →
  eredeti `overlay` → AutoFix → kontrasztgörbe.
- **`HeatMap`**: deszaturálás + HSV-gradiensleképezés a
  240°→240°→120°→0°→0° (v 50→100→100→100→50) színskálán, `Hue` eltolással.
- **`NightVision`**: AutoFix → `#000000`→`#57cc29` gradiensleképezés →
  belső ragyogás → zaj (`lighten`, 0,2) → fényerő/kontraszt.
- **`Polaroid`**: négyzetes középvágás, keretarányok a rövidebb oldal
  arányában: oldalt 6,45%, fent 9,68%, lent **25,8%** — ez a klasszikus
  Polaroid-arány, egzakt számokkal.
- **`Comicize`**: két, félpixellel eltolt csempézett pontmaszk (`_nDotSize =
  W/70 + 1`) + pixelesítés + küszöbgörbék → valódi féltónusos raszter.

Ezek **a Picasa saját lépéssorai** — a *sorrend*, a *műveletnevek* és a
*paraméterértékek* nem közelítések. A műveletek **pixel-szemantikája**
viszont NEM ebből a fájlból jön (ld. 4.4).

### 4.4 Amit a fájl NEM mond meg — a Flash/Flex-örökség

Az `<effect>` blokkok **Adobe Flex MXML**-ben íródtak: `cnt:EffectCanvas`
gyökér, `{…}` adatkötések `Math.max`-szal, `HSliderPlus`/`HSliderFastDrag`
vezérlők. Ez a Picnik-örökség közvetlen nyoma — a futtató viszont a Picasa
saját, natív C++ motorja (`Picasa3.exe`, RTTI-nevek: `glimmer::EffectParser`,
`glimmer::GlowImageOperation`, `glimmer::BlurImageOperation`, …), tehát a
fájl egy **Flash-korabeli receptet** ír le egy **natív végrehajtónak**.

A műveletek paraméterlistája karakterre a Flash szűrő-API-t követi:

| `filterdesc.xml` | Flash megfelelő |
|---|---|
| `GlowImageOperation(color, glowalpha, xblur, yblur, strength, quality, innerglow, knockout)` | `flash.filters.GlowFilter(color, alpha, blurX, blurY, strength, quality, inner, knockout)` |
| `BlurImageOperation(xblur, yblur, quality)` | `flash.filters.BlurFilter(blurX, blurY, quality)` |
| `DropShadowImageOperation(blurX, blurY, …)` | `flash.filters.DropShadowFilter` |

Ebből következik két dolog, amit a fájl **nem** közöl, és amit ezért
**mérésből** kell eldönteni:

1. **A `quality` jelentése.** Flashben ez az elmosás *átfutásainak száma*
   (1–3, ahol 3 ≈ Gauss). A Glimmer-effektekben végig `quality="3"`. A
   PicasaPy jelenleg figyelmen kívül hagyja.
2. **Az `xblur`/`yblur` pixel-jelentése.** Flashben a `blurX` **nem
   Gauss-σ**, hanem elmosás-szélesség, és **0–255-re korlátozott**.
   **A natív port átvette a korlátot — ez MÉRÉSBŐL ÉS A BINÁRISBÓL IS
   bizonyított.** A `glimmer::BlurImageOperation` `apply` metódusában
   (`0x00bb4de0`, dekompilálva) ott áll szó szerint, **tengelyenként külön**:

   ```c
   local_a0 = 1.0;
   iVar2 = FUN_008ef520(param_2, &local_98);   // az xblur attribútum
   if (iVar2 == 0) local_a0 = (float)local_98;
   if (local_a0 <= 255.0) { fVar3 = FUN_00bb5050(); }
   else                   { fVar3 = 255.0; }    // <-- A KORLÁT
   // ugyanez megismételve az yblur-re
   ```

   Ez megmagyarázza a mérést is: a `255/255` illeszkedett jobban, mint az
   arányt megtartó `255/204` — mert a két tengelyt **függetlenül** vágja. Eredeti
   windowsos Picasa-exportokból (Lomo, 2560×1702) visszafejtve a ragyogás
   súlytérképét, az illeszkedés optimuma **σ ≈ 255–340**, miközben a nyers
   képlet 896-ot adna; a teljes láncon a Picasa kimenetétől való átlagos
   csatorna-eltérés korlát nélkül 41,8, **255-ös korláttal 9,0**. Vagyis:
   a méretfüggő képletek eredményét **255-re kell vágni** (#504, #317).

#### A 255-ös korlát KÉT külön mechanizmussal valósul meg

**`BlurImageOperation`** (`0x00bb4de0`) — nyílt vágás, tengelyenként:

```c
if (xblur <= 255.0) { r = FUN_00bb5050(xblur); }   // kvantálás
else                { r = 255.0; }                  // vágás
```

A `0x00bb5050` **sugár-kvantáló**: 1 alatt 0-t ad (nincs elmosás), és a
2/3/4/5-ös egészeket felfelé igazítja (2,065 · 3,0625 · 4,13 · 5,13) — a
Flash `BlurFilter` diszkrét viselkedésének átvétele.

**`GlowImageOperation`** (`0x00bb8f70` → `0x00bb89b0`) — **skálázó
tényezővel**, nem `min()`-nel:

```c
float sugar_skala(float blur, float size) {
    if (blur <= 0) blur = 1e-05;
    scale = 1.0;
    if (blur > 255.0) { scale = 255.0 / blur; blur = 255.0; }
    v = (100.0 + size - scale*size) / blur;
    return (v >= 3.0) ? scale : (v / 3.0) * scale;
}
```

A hívó ezt **megszorozza** a sugárral (`local_188 * xblur`), tehát 255 fölött
az eredmény **pontosan 255** — vagyis effektíve ugyanaz a korlát, csak más
úton. (A `v < 3` ág tovább csökkenti a skálát; ez a minőség/méret
kompromisszum ága.)

**Következmény:** a Lomo/Holga vignettájára (ami Glow) és a maszkolt
elmosásra (ami Blur) **egyaránt 255 a felső határ** — a mérés, a
Flash-örökségből vett következtetés és a natív kód **mind egyezik**.

#### `GlowImageOperation`: az `innerglow` és a `knockout` HALOTT attribútum (#2076)

A `filterdesc.xml` mind a nyolc `GlowImageOperation`-je `innerglow="true"`-t és
`knockout="false"`-t ír. **A natív motor egyiket sem olvassa ki.**

Az attribútum-olvasó `0x00bb8c40` pontosan nyolc nevet keres, mindegyiket egy
8 bájtos rekeszbe kötve:

| attribútum | rekesz | a névsztring |
|---|---|---|
| `color` | `+0x24` | `0x00cbda84` |
| `glowalpha` | `+0x2c` | `0x00cf0144` |
| `xblur` | `+0x34` | `0x00cefe84` |
| `yblur` | `+0x3c` | `0x00cefe8c` |
| `strength` | `+0x44` | `0x00cf0150` |
| `quality` | `+0x4c` | `0x00cafa3c` |
| **`inner`** | `+0x54` | `0x00cf015c` |
| `knockout` | `+0x5c` | `0x00cf0164` |

A névkeresés (`0x008eb160`) kis-nagybetűre érzéketlen, de **teljes** egyezést
kíván: a ciklus a tű végén (`[edx]==0`) azt is megköveteli, hogy a szénakazal
is nullára fusson (`[esi]==0`). Ezért `"inner"` ≠ `"innerglow"`.

Az `innerglow` szó a `Picasa3.exe`-ben **egyáltalán nem fordul elő** — sem a
bináris-index sztringtárában, sem a nyers fájlban bájtsorozatként (két
független lekérdezés). A meglévő `inner*` sztringek: `inner`, `innercolor`,
`innerthickness` (a `BorderImageOperation`-é), `innerRadius`, `innerAlpha`
(a `CircularGradientImageMask`-é).

A `knockout` neve **egyezik**, tehát kiolvasódik — de sehova nem jut el: a
konstruktor (`0x00bb8a60`) minden rekeszt nulláz, a rajzolás előtti kiértékelő
(`0x00bb8e10`) pedig a `+0x54` és a `+0x5c` rekeszt **ugyanabba a verem-kukába**
(`[esp+0x38]`) értékeli ki, és egyiket sem vizsgálja meg. A tényleges rajzoló
(`0x00bb8f70`) `color`-t, négy lebegőpontost és a `quality`-t kapja —
**logikai kapcsolót nem**.

> **Következmény.** A `GlowImageOperation`-nek **egy** módja van, a XML-től
> függetlenül. A Flash-örökségből átvett `inner`/`knockout` kapcsolópár a natív
> portban nem épült meg. Amit a Vignette, a Matte és a MuseumMatte mérése mutat
> — széltől befelé ható izzás —, az tehát nem az „inner ág", hanem **az
> egyetlen ág**. A PicasaPy `render/glimmer_ops.py::inner_glow`-ja ezt az egy
> módot valósítja meg; a neve történeti.

**Ami még nincs kimérve:** a mód pontos képlete a `0x00bb8f70`-ben, és azon
belül a `strength` viselkedése **1 fölött** (a Comicize 1,1-et ad; a mi
modellünk a súlyt `[0,1]`-re vágja, tehát telít). Ez a Vignette-et és a
Matte-ot is érinti. Nyitott kérdés: #2076.



#### A maszképítő (`0x00bcc2e0`) TELJES kiolvasása — és egy HELYESBÍTÉS (#2102)

A #2102 nyitott kérdése: *a `0x00bcc2e0` második fele, és hogy a két
kiszámolt, 255-re vágott egész MIT vezérel.* Megvan — és közben kiderült,
hogy az előző kör **rossz paraméterhez** kötötte a lépcsős képletet.

##### A paraméterek és a bemeneti vágásuk

A maszképítő nyolc argumentumot kap; a rajzoló dokumentált sorrendjével
(`forrás, color, glowalpha, xblur, yblur, strength, quality, cél`) a
keretbeli helyük:

| arg | hol a keretben | mi | vágás |
|---|---|---|---|
| 1 | `[esp+0x70]` → `ebp` | forrás/rect | – |
| 2 | – | `color` | – |
| 3 | `[esp+0x80]` | **glowalpha** | **[0, 1]**, majd bájt: `trunc(a × 255)` (`0x00bcc4d9`) |
| 4 | `[esp+0x84]` | **xblur** | **[0, 253]** |
| 5 | `[esp+0x88]` | **yblur** | **[0, 253]** |
| 6 | `[esp+0x8c]` | **strength** | **[0, 255]** |
| 7 | `[esp+0x90]` | **quality** (egész) | **[1, 15]** |
| 8 | `[esp+0x20]` (belépéskor) | cél | nem lehet `NULL` (`0x00bcc2f3`) |

A vágásokat a **`0x00bc52c0`** segédfüggvény végzi (két float **[0, 253]**-ra
— a `0x00cf0b4c` = `253.0f`, a `0x00cf4090` = `253.0`; egy egész
**[1, 15]**-re, `0x00bc5345`–`0x00bc534f`); a `glowalpha` [0, 1] és a
`strength` [0, 255] vágása a hívó törzsében van (`0x00bcc34c`–`0x00bcc3b8`,
a felső korlát a `0x00cf39d0` = `255.0` és a `0x00cf3a00` = `255.0f`).

##### A két egész: a KÉT BLUR-SUGÁR

A `0x00bcc3d5`–`0x00bcc434` és a `0x00bcc438`–`0x00bcc48d` blokk **ugyanaz a
képlet, két különböző bemenetre**:

```
r_x = min(255, trunc( ceil((xblur − 1) · 0,5) · quality + 1 ))
r_y = min(255, trunc( ceil((yblur − 1) · 0,5) · quality + 1 ))
```

- a `−1,0` a `0x00c7e328`, a `×0,5` a `0x00c72150` (kiolvasva);
- a `ceilf` a `0x00529e10` (a `_matherr` névtáblája, `0x00c1324c`, a `0x3ec`
  kódra a `0x00c43bac` = `"ceil"`-t adja);
- a csonkítás `fldcw | 0x0c00` (nulla felé) + `fistp`;
- a 255-ös korlát az `esi = 0xff` / `cmp` / `ja` párossal
  (`0x00bcc42c`, `0x00bcc485`).

**Miért nézett ki egyformának a két blokk:** az elsőt egy `push ecx`
(`0x00bcc3d4`) előzi meg, ezért az `[esp+0x88]` ott **a bázis `[esp+0x84]`**
— vagyis az `xblur`; a másodikban a verem már vissza van állítva
(`add esp, 4`, `0x00bcc403`), tehát az `[esp+0x88]` valóban az `yblur`.

A két egész a bázis `[esp+0x1c]` (r_x) és `[esp+0x18]` (r_y) rekeszbe kerül,
és a `0x00bcbfb0` hívásba megy (`0x00bcc5de`–`0x00bcc5ef`), onnan a
`0x00bcc700`-ba (`0x00bcc02a`).

##### ⛔ HELYESBÍTÉS: a lépcsős képlet NEM a `strength`-é

A #2102 első köre azt írta, hogy *„a `strength` a maszképítőben
`ceil((s−1)/2)` alakban lép be"*, és ebből azt a jóslatot vezette le, hogy a
`filterdesc.xml` minden Glow-hívására ez a tag **állandó 1**. **Mindkettő
megdőlt:** a képlet az `xblur`/`yblur`-re megy, a `strength` pedig egészen
máshol lép be.

##### Ahol a `strength` VALÓJÁBAN belép: 8.8-as fixpontos szorzó

A `0x00bcbfb0` a `strength`-et (`[ebp+0x20]`) és a `color`-t (`[ebp+0x14]`) a
**`0x00bcbd90`** regiszter-előkészítőnek adja (`0x00bcbfd7`–`0x00bcbfe1`). Az
onnan kiolvasott mag:

```
0x00bcbda4  fld dword ptr [ebp+0xc]        ; strength
0x00bcbda8  fmul qword ptr [0xcf39d8]      ; × 256,0   (kiolvasva)
0x00bcbdc5  fistp dword ptr [esp+8]        ; csonkítás (fldcw | 0x0c00)
0x00bcbdc9  mov ax, word ptr [esp+8]       ; az ALSÓ SZÓ
```

Ez a szó kerül **négyszer** az `mm7`-be (`[esp+0x30]`…`[esp+0x36]`), mellette
a `0x0100` **nyolcszor** az `xmm7`-be és a `0x0080` **négyszer** az `mm6`-ba
(`0x00bcbdf4`–`0x00bcbe41`). A `0x0100` = **1,0** és a `0x0080` = **0,5** a
klasszikus **8.8-as fixpontos** ábrázolásban ⇒

> **A `strength` egy 8.8-as fixpontos szorzó: `trunc(strength × 256)`**,
> a `color` B/G/R/A bájtjai mellé töltve (`xmm6`, két példányban).

A `[0, 255]`-ös bemeneti vágás miatt a szorzó **1,0 fölé is mehet** (egészen
255-ig) — tehát a `strength` **erősíthet**, nem csak halványíthat.

##### Nálunk (mérve) — két eltérés

`src/picasapy/render/glimmer_ops.py`:

| | eredeti (mérve) | nálunk ma (mérve) |
|---|---|---|
| blur-sugár | **egész**: `min(255, trunc(ceil((b−1)/2)·quality + 1))`, `b` ∈ [0, 253], `quality` ∈ [1, 15] (alap 3) | a nyers `xblur`/`yblur` **közvetlenül szigmaként** az analitikus `erf`-modellbe (`_box_blur_axis`, `:575`) |
| `strength` | 8.8-as **szorzó**, `trunc(s × 256)`, a bemenet [0, 255] | keverési súly, **[0, 1]-re vágva**: `np.clip((1−covered)·strength, 0, 1)` (`:578`) |
| `glowalpha` | bájt: `trunc(a × 255)`, a bemenet [0, 1] | `* np.float32(alpha)` (`:578`) — nincs bájtra kvantálás |
| sugár-korlát | a **bemenet** 253, a **kimenet** 255 | `GLOW_RADIUS_MAX = 255.0` a sugárra (`:495`) |

⚠️ **Megfejtve, de a mért eltérésre gyakorolt hatása NINCS mérve.** Sem a
Vignette-, sem a Comicize-goldenen nem futott összevetés ezzel a
modellel — a fenti két eltérés önmagában **nem bizonyítja**, hogy a
javításuk csökkenti a ΔE-t. Megvalósítás és mérés: **#2159**.

**Bizalmi fok: megerősített** a vágásokra, a két sugár-képletre, a `ceilf`
azonosítására és a 8.8-as szorzóra (mind közvetlen kiolvasás).

##### A blur ÁTVÁLTÓJA (`0x00bb89b0`) — ÁTMÉRETEZÉSI ARÁNY (⛔ 2026-09-05: az „azonosság" HELYESBÍTVE, #2159)

A hívó (`0x00bb8f70`) a maszképítő előtt mindkét blur-paramétert átengedi a
`0x00bb89b0(p, d)` függvényen: `p` = a hívó **4. argumentuma** (`xblur`,
`0x00bb8fa7`), illetve az **5.** (`yblur`, `0x00bb8fdd`); `d` = a kép
szélessége (`[ebp+8]`), illetve magassága (`[ebp+0xc]`), egésszé-floattá
alakítva (`0x00bb8f8b`, `0x00bb8fc5`).

A függvény teljes zárt alakja, kiolvasva:

```
if (p <= 0)  p = 1e-5                       ; 0x00cf3a10
k = (p < 255) ? 1,0 : 255/p                 ; 0x00cf39d0 = 255,0
X = ((100 + d) − d·k) / p                   ; 0x00cf3a08 = 100,0
return (X > 3,0) ? k : k · X / 3,0          ; 0x00c49618 = 3,0f, 0x00cf39f8 = 3,0
```

⛔ **HELYESBÍTÉS (2026-09-05, #2159): NEM azonosság, és a `Vignette`/`Matte`
épp a legfelső ágra esik.** A korábbi szöveg azt írta, hogy „a
`filterdesc.xml` Glow-hívásainak blur-értékei jóval kisebbek 33,33-nál ⇒ a
függvény pontosan 1,0-t ad". A `filterdesc.xml:1394` (`Vignette`) és `:1066` (`Matte`) szerint viszont
`xblur = _sldrBlur.value · 0,02 · max(W,H) / 4` — a 2560×1702-es
referenciaképen `Blur = 35` mellett ez **448,0**, `Blur = 50` mellett
**640,0**. Nem kisebb 33,33-nál: **13–19-szer nagyobb 255-nél.** A helyes
sor tehát mindkét effektre a táblázat **alsó** ága.

Egy hiba a képletben is: az `X` nevezője **nem `p`, hanem `min(p, 255)`** —
a `p ≥ 255` ágon a `0x00cf3a00` (**255,0f**) írja felül a paraméter-rekeszt
(`0x00bb89fe`–`0x00bb8a08`), a `p < 255` ág pedig a `0x00bb8a4e`-en ugorva
érintetlenül hagyja. Egységesen:

```
p'  = min(p, 255)                            ; 0x00cf3a00 = 255,0f
k   = p' / p                                 ; 0x00cf39d0 = 255,0
X   = ((100 + d) − d·k) / p'                 ; 0x00cf3a08 = 100,0
f   = (X > 3) ? k : k·X/3                    ; 0x00c49618 = 3,0f, 0x00cf39f8 = 3,0
```

| tartomány | `f` |
|---|---|
| `p < 33,33` | **1,0** (az egyetlen valódi azonosság) |
| `33,33 ≤ p < 255` | `100 / (3·p)` |
| `p ≥ 255` | `255/p`, ha `X > 3` — a `Vignette`/`Matte` mindig ide esik |

##### Amire a visszatérés VALÓ: átméretezés, nem elmosás

Az `f` **nem** a blur szorzója, hanem a **munkapuffer léptéke**. Az egyetlen
hívó (`0x00bb8f70`, `call_count = 2`) így használja:

- `0x00bb8ff3`–`0x00bb9013` — **gyorsút**: csak akkor, ha **mindkét**
  visszatérés pontosan `1,0` (`fld1`, majd két `fcom`);
- különben `0x00bb91d3`: `fmul dword ptr [esp+0x24]` — az arányt megszorozza
  a kép **float szélességével** (`0x00bb8f8b`-ben előállítva), majd
  `fldcw | 0x0c00` + `fistp` (`0x00bb921a`) **csonkít egésszé**, és ez lesz a
  munkapuffer mérete (`[esp+0xcc]`, `[esp+0xd0]`).

⇒ **Nagy blurnál a Glow lekicsinyített képen dolgozik**, és a maszképítő
`[0, 253]`-as vágása meg a 255-ös sugárkorlát **a lekicsinyített térben**
érvényes. Teljes felbontásra visszaszámolva a korlát így épp visszaadja az
eredeti nagyságrendet: `p ≥ 255`-re `p·f = 255` pontosan, tehát a
lekicsinyített térbeli `255` a teljes felbontásban `255/f = p`.

**Bizalmi fok: megerősített** az átváltó képletére és arra, hogy a
visszatérés a puffer-méretet szorozza (mind a 165 + a hívó vonatkozó bájtjai
elolvasva). ⚠️ **Feltételes** — és NEM olvastuk vissza —, hogy a
maszképítőbe a **lekicsinyített térbeli** blur (`b = p·f`) érkezik; ezt csak
a lenti három-pontos egyezés és a ΔE-mérés támasztja alá.

#### A négy eltérés HATÁSA a mi kimenetünkre — mérve, mind a négy NEGATÍV (#2159)

A fenti kiolvasás megmondja, **mit csinál** az eredeti maszképítő. Az, hogy
a mi modellünkbe átvezetve **javítana-e**, külön kérdés — és a mérés
szerint egyik sem javít. A #879 tanulsága szerint a megfejtett mechanizmus
önmagában nem diagnózis, ezért mind a négyet egyenként vezettük be és
mértük.

**Mérőszett:** `referencia/vignette/*` (valódi Picasa-export), forráskép
`referencia/lomo/Lomo no effect/…`, 2560×1702. Metrika: csatornánkénti
átlagos |Δ| szintben.

| eltérés | `Vignette default` átlag \|Δ\| | verdikt |
|---|---:|---|
| — (a mai modell) | **0,892** | viszonyítási alap |
| egész, lépcsős blur-sugár (`r = min(255, trunc(ceil((b−1)·0,5)·q + 1))`) | **17,69** | **13× romlás** |
| `xblur/yblur` vágás 253-ra | 0,892 | hatástalan (ld. lent) |
| `strength` 8.8-as fixpont (`trunc(s·256)/256`) | 0,888 | a zajszint alatt |
| `glowalpha` bájtra kvantálva (`trunc(a·255)/255`) | 0,892 | azonosság ezen az úton |

**Miért hatástalan a három kicsi — mindegyikre megvan az ok:**

1. **A 253-as vágás nem aktiválódik** az alapesetben: a mi sugarunk
   `35 · 0,0025 · 2560 = 224`. Ahol viszont aktiválódik (`Vignette size
   max`, blur=50 → sugár 320), ott **ötszörös romlást** ad (1,224 → 5,983).
   Ez **kontroll-mérés**: a `glimmer_tone.py` kommentje ugyanezt már
   rögzítette a 255-ös korlátra (5,79 vs 1,22).
2. **A 8.8-as fixpont a mérési zaj alatt van.** `strength = 1,4`-nél az
   eltérés `0,0016`; a csúszka két végpontján (`1,0`, `2,0`) a 8.8-as alak
   **pontos**, ott az eltérés szigorúan nulla.
3. **A `glowalpha` a Vignette/Matte úton mindig `1,0`**, és
   `trunc(1,0·255)/255 = 1,0`. Más Glow-hívásoknál (ahol az alfa nem 1,0) a
   kvantálás hatása **nincs mérve**.

**Amit a mérés POZITÍVAN mutat:** a `Vignette size min` (blur=0) esetben az
eltérés **pontosan 0,000**, és az alapesetben a kép középső 2%-ában
(`r < 0,2`) is nulla. A kép alap-útja (dekódolás, színtér, változatlan
képpontok) tehát hibátlan — a teljes maradék hiba a vignetta-súly
ALAKJÁBAN ül.

⇒ **Egyiket sem építettük be.** A mi analitikus (`erf`-alapú) modellünk és
az eredeti dobozmenetes maszképítője nem ugyanaz a számítás; a bináris
konstansainak egyenkénti átemelése ezért nem közelít, hanem ront.

##### ⛔ A „13× romlás" oka: a korlát a LEKICSINYÍTETT térben él (2026-09-05, #2159)

A fenti tábla első sora (egész, lépcsős sugár → **13× romlás**) helyes
mérés, de **rossz térben** végzett bevezetést mér. A korlátot teljes
felbontásban alkalmazva a `Vignette` minden `Blur > 13,2` állása ugyanazt a
sugarat kapja:

| `Blur` | `xblur = Blur·0,02·2560/4` | 253-ra vágva | `r = min(255, ⌈(b−1)/2⌉·3+1)` |
|---:|---:|---:|---:|
| 10 | 128,0 | 128,0 | 193 |
| 13 | 166,4 | 166,4 | 250 |
| **14** | 179,2 | 179,2 | **255** ← innentől mind |
| 20 | 256,0 | 253,0 | 255 |
| 35 | 448,0 | 253,0 | 255 |
| 50 | 640,0 | 253,0 | 255 |

⇒ Teljes felbontásban a `Blur = 35` és a `Blur = 50` **azonos** kimenetet
adna. **A golden ezt megcáfolja:** a két valódi Picasa-export egymáshoz
képest **ΔE 10,233** (`Vignette default` vs `Vignette size max`,
CIE76-átlag; a `Blur = 0` exporttól mérve 20,928, illetve 30,971). A mi
mai modellünk hibája ugyanezeken **1,277** és **1,667** — a teljes
felbontású bevezetés tehát 6–8-szoros visszalépés lenne.

##### ⭐ A levezetett sugár — a `/8` konstans MÁR NEM szabad paraméter

A lekicsinyítéssel a lánc végigszámolható, illesztés nélkül
(`f` = az átváltó visszatérése, `b_red = p·f`, `rp = ⌈(min(b_red,253)−1)/2⌉`):

| `Blur` | `xblur = p` | `f` | lekicsinyített szélesség | `b_red` | `rp` | `rp/f` (teljes felb.) | a mi sugarunk (`p/2`) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 128,0 | 0,26042 | 666 | 33,33 | 17 | 65,3 | 64,0 |
| 35 | 448,0 | 0,56920 | 1457 | 255,0 → 253 | 126 | 221,4 | 224,0 |
| 50 | 640,0 | 0,39844 | 1020 | 255,0 → 253 | 126 | 316,2 | 320,0 |

Három **független** Blur-álláson 1–2%-os egyezés a mi eddig **illesztett**
`VIGNETTE_RADIUS_FACTOR = 0,02/8` konstansunkkal. Az egyezés nem véletlen:
`p/2 = ⌈(p−1)/2⌉` egész `p`-re, vagyis a mi „sugarunk" pontosan az eredeti
**menetenkénti dobozsugara**. És mert `quality = 3` dobozmenet szórása
`σ = √(r(r+1)) ≈ r`, a mi `erf`-modellünk `σ = r`-rel épp ezt a hármas
dobozláncot közelíti — ezért illeszkedett a mérés a `/8`-ra, és ezért NEM
a `filterdesc` `/4`-ére.

⇒ **A `/8` levezetett érték, nem illesztett.** A `glimmer_tone.py:78`
kommentje eddig „valódi Picasa-exportokon mért illesztésre" hivatkozott;
ez a levezetés váltja ki.

**Amit a levezetett sugár MÉR** (ugyanaz a szett, CIE76-átlag ΔE):

| eset | mai `r` | levezetett `r` | ΔE ma | ΔE levezetett |
|---|---:|---:|---:|---:|
| `Vignette default` | 224,0 | 221,4 | 1,277 | **1,225** |
| `Vignette size max` | 320,0 | 316,2 | 1,667 | **1,552** |
| `Vignette strenght max` | 224,0 | 221,4 | 1,315 | **1,309** |
| `Vignette strenght min` | 224,0 | 221,4 | 1,109 | 1,116 |

Négyből háromban javít, egyben 0,007-tel ront; átlag **1,342 → 1,301**. A
nyereség kicsi — az érték a levezetettségben van, nem a 3%-ban.

**Alapmérés (a #2159 első „Kész, ha" pontja), a mai modell, CIE76-átlag ΔE
a valódi exporthoz:** `default` 1,277 · `size max` 1,667 · `size min` 0,000 ·
`strenght max` 1,315 · `strenght min` 1,109 · `fade max` 0,000 ·
`strenght mid` 1,304 (a csúszka-állás FELTEVÉS: 1,5) · `fade mid` 1,301
(FELTEVÉS: 50). Forrás: `referencia/lomo/Lomo no effect/…` — a `size min` és
a `fade max` export bájtra ezzel azonos, ami a forrásválasztást is igazolja.

#### A csempe MÁSODIK szűrője: a SHIFT kapcsolja be (#2141)

A `0x00c7e5a0` csempe-tábla rekordjai **hármasak** (elsődleges, másodlagos,
0). A #1869 köre a másodlagost „örökölt id"-nek nevezte; a **feltétele** most
ki van mérve, és a név is pontosításra szorul.

**A kapcsoló: a SHIFT lenyomott állapota**, a fül felépülésekor lekérdezve:

```
0x005d7c91  push 0x10                        ; VK_SHIFT
0x005d7ca3  call dword ptr [0xc406f8]        ; GetAsyncKeyState
0x005d7cbb  shr  eax, 0xf                    ; a 15. bit = „épp le van nyomva"
0x005d7cbe  and  al, 1
0x005d7cc0  mov  byte ptr [ecx+0x33a8], al   ; a panel kapcsolója
```

Az importnév a betöltési táblából kiolvasva: a `0x00c406f8` rekesz a
`0x00922efc` név-rekordra mutat, ami **`GetAsyncKeyState`** (hint 256).

**A csempeépítő ezt nézi**, és csak akkor nyúl a második mezőhöz:

```
0x005d7d2e  mov ecx, [esi+esi + 0xc7e5a0]    ; ELSŐDLEGES szűrőnév
0x005d7d63  cmp byte ptr [ebx + 0x33a8], 0
0x005d7d6a  je  0x5d7e07                     ; nincs Shift -> marad az elsődleges
0x005d7d70  mov esi, [esi + 0xc7e5a4]        ; MÁSODLAGOS szűrőnév
0x005d7d76  cmp esi, edi (0)
0x005d7d78  je  0x5d7e07                     ; nincs második -> marad az elsődleges
```

⇒ **Shift nélkül mindig az elsődleges fut.** A második akkor és csak akkor,
ha a Shift le van nyomva ÉS az adott csempéhez van második név.

#### A kilenc csempe, amelynek VAN második szűrője

| # | elsődleges | Shift-tel | a második felirata |
|---|---|---|---|
| 1 | `unsharp2` | `unsharp` | **Sharpen (Old)** |
| 5 | `PicnikGrain` | `grain` | **Film Grain (Old)** |
| 6 | `PicnikTint` | `tint` | **Tint (Old)** |
| 9 | `glow2` | `glow` | **Glow (Old)** |
| 12 | `dir_tint` | `radtint` | Radial Tint |
| 21 | `HeatMap` | `NightVision` | Night Vision |
| 27 | `Vignette` | `Matte` | Matte |
| 28 | `Pixelate` | `PicnikFocalPixelate` | Focal Pixelate |
| 33 | `Border` | `RoundedEdges` | Rounded Edges |

A maradék **27** csempe második mezője `NULL` — azokra a Shift nem hat.

⚠️ **A „örökölt/régi" olvasat csak a felére igaz.** Négy másodlagos felirata
kimondottan **„(Old)"**, öté viszont **saját, önálló név** (Radial Tint,
Night Vision, Matte, Focal Pixelate, Rounded Edges) — ott a Shift nem régi
változatot, hanem **másik effektet** ad. A #1869 köre ezt „örökölt id"-nek
nevezte; **ez pontatlan volt**, és itt helyesbítjük.

**Bizalmi fok: megerősített.** A kapcsoló, az importnév, a feltétel és a
kilenc pár közvetlen kiolvasásból; a feliratok a `filterdesc.xml`-ből.

> **Nálunk (mérve):** az effekt-füleken **nincs** Shift-kezelés — a
> `ShiftModifier` és a `Qt.Shift` egyáltalán nem fordul elő az
> `EditorEffectsTab*.qml` és a `ToolTile.qml` fájlokban. A funkció tehát
> hiányzik; jegy: **#2146**.

##### ⛔ HELYESBÍTÉS: a Shift-váltás ÉLŐ, nem a fül felépülésekor (#2164, 2026-09-03)

A fenti szakasz azt írta, hogy a Shift állapota **„a fül felépülésekor
egyszer"** dől el. **Ez pontatlan volt.** A panel üzenetkezelője
(`0x005e6710`) a VK-vizsgálat ELŐTT külön ágat futtat:

```
0x005e6745  cmp dword ptr [ebx+4], 0x102     ; WM_CHAR -> kihagy
0x005e674e  cmp byte ptr [ebx+8], 0x10       ; VK_SHIFT?
0x005e6754  push 0x10 ; call [0xc406f8]      ; GetAsyncKeyState(VK_SHIFT)
0x005e675c  shr eax, 0xf ; and al, 1
0x005e6761  cmp byte ptr [edi+0x33a8], al    ; a TÁROLT Shift-jelző
0x005e6767  je  0x5e6776                     ; nem változott -> nincs teendő
0x005e6769  mov eax, dword ptr [edi+0x3378]
0x005e6771  call 0x5d7c20                    ; a CSEMPEÉPÍTŐ újrafuttatása
```

⇒ A `VK_SHIFT` **minden le- és felengedésére** (`WM_KEYDOWN` és
`WM_KEYUP`; a `WM_CHAR` kizárva) a program **újraépíti a csempéket**, ha a
`[panel+0x33a8]` jelző értéke megváltozott. A felhasználó tehát a kilenc
csempét **nyomva tartás közben látja átváltani**, elengedéskor pedig
visszaváltani — nem kell hozzá fület váltani.

**Bizalmi fok: megerősített** (közvetlen kiolvasás; a `0x005d7c20` és a
`[panel+0x33a8]` ugyanaz, mint a fenti szakaszban).

**Megvalósítási következmény (#2146):** a Shift-ág nem elég a fül
felépülésekor egyszer kiértékelni — a billentyű **le- és felengedésére**
is újra kell építeni a csempéket. A jegy „Kész, ha" listája ezzel bővül.

#### A HÁROM effekt-fül TELJES összevetése a csempe-táblával (#2141)

A #2141 „Kész, ha" listájának pontja — *a fül **összes** csempéje összevetve
a `0x00c7e5a0` táblával* — itt teljesül, és nem egy, hanem **mind a három**
fülre. A tábla 36 rekordja pontosan a három eredeti effekt-fül 3×12-es
rácsa; a mi `EditorEffectsTab1/2/3.qml`-ünk **pozícióról pozícióra** ennek
felel meg.

**A 2. és a 3. fül mind a 24 csempéje EGYEZIK** (csak a kis/nagybetűs alak
tér el: `ir`↔`IR`, `heatmap`↔`HeatMap` stb.):

```
2. fül: IR · Lomo · Holga · HDR · Cinemascope · Orton · Sixties · Invert
        · HeatMap · CrossProcess · QuantizePalette · TwoTone
3. fül: Boost · Soften · Vignette · Pixelate · FocalZoom · PencilSketch
        · Neon · Comicize · Border · DropShadow · MuseumMatte · Polaroid
```

**Az 1. fülön HÁROM csempe téves — és mind a három ugyanazt a hibát követi
el:** a felirat az eredeti **elsődleges** szűrőé, a hívás viszont **másik**
szűrőt indít.

| # | felirat nálunk | eredeti elsődleges | nálunk hívott kulcs | a hívott kulcs SAJÁT felirata (eredeti szövegtár) |
|---|---|---|---|---|
| 1 | „Sharpen" / „Élesítés" | **`unsharp2`** | `unsharp` | **Sharpen (Old)** / **Élesítés (régi)** |
| 5 | „Film Grain" / „Filmszemcse" | **`PicnikGrain`** | `grain2` | Film Grain / Filmszemcse *(azonos felirat, másik szűrő)* |
| 6 | „Tint" / „Árnyalás" | **`PicnikTint`** | `tint` | **Tint (Old)** / **Árnyalás (régi)** |

Az 1. és a 6. csempénél a hívott kulcs éppen az, amit az eredeti a **Shift**
alá rejt (ld. az előző szakaszt) — a felhasználó tehát ma az „Élesítés"
gombbal a „(régi)" változatot kapja, jelzés nélkül. Az 5-nél a `grain2`
**létező eredeti szűrő** (`filter_grain2_label0` = *Film Grain*), csak épp
nem az, amelyik a csempén ül.

A többi kilenc csempe (`sepia`, `bw`, `warm`, `sat`, `radblur`, `glow2`,
`ansel`, `radsat`, `dir_tint`) **egyezik** — köztük a `glow2`, ahol a
tartalék `glow` lett volna a hasonló hiba.

**Bizalmi fok: megerősített.** A tábla a binárisból (`0x00c7e5a0`, 36×12 b),
a mi oldalunk az `EditorEffectsTab*.qml` `effectRequested(...)` hívásaiból,
a feliratok az eredeti szövegtárból (`filter_*_label0`) és a
`render/registry_data.py`-ból.

##### Amit a Shift-lelet a MI 6. és 7. fülünkről mond

- A **6. fül** (`EditorEffectsTab4.qml`, #422) öt csempéjéből **négy**
  (`matte`, `nightvision`, `roundededges`, `picnikgrain`) az eredetiben
  **Shift-másodlagos**, az ötödik (`localcontrast`) egyetlen csempén sincs
  rajta. Ez nem hiba — a hét fül a tulajdonos rögzített döntése —, de ha a
  Shift-ág elkészül (**#2146**), ez a négy csempe **két úton** is elérhető
  lesz; a jegy ezt vegye figyelembe.
- A **7. (örökölt) fül** bevezető mondata viszont **téves állítást tesz**:
  *„These filters come from older versions of Picasa. **They are not
  available in today's Picasa**"* — a lista első eleme, a `radtint`
  (*Radial Tint* / *Sugaras árnyalás*) **elérhető a Picasa 3.9-ben**: az
  1. fül 12. csempéjén (`dir_tint`) a Shift hozza elő. Jegy: **#2148**.

#### A `mode` attribútum SZÁMÉRTÉKE — és az effekt-csempe kék jelvénye (#1869)

A `mode` nem csak besorolás: a parser **egésszé fordítja**, és ez az egész
kapcsolja a csempe jobb alsó sarkában látható kék jelvényt.

**A `mode` → egész leképzés — TELJES, a `0x00900490`-ből kiolvasva:**

| `mode` | érték | a sztring címe |
|---|---|---|
| `oneclick` | **1** | `0x00cd182c` |
| `hard` | 2 | `0x00cd1824` |
| `effect` | 4 | `0x00cd1814` |
| `soft` | 5 | `0x00cd181c` |
| `tool` | 6 | `0x00cd1838` |
| `history` | 7 | `0x00cd1840` |
| bármi más | **0** | — |

*(A 3-as érték nincs kiosztva. A `history` ága `neg al; sbb eax,eax; and eax,7`
— egyezésre 7, egyébként 0.)*

**Hol lesz ebből a `FilterDesc` mezője.** A `filterdesc.xml` parsere
(`CImageFilterRegistrar::+0x04`, `0x008ff550`) az attribútumnevet a
`0x00cd1730` = `"mode"` sztringgel veti össze; egyezésre:

```
0x008ff693  call 0x900490            ; mode → egész
0x008ff698  mov dword ptr [esp+0x28], eax
   …
0x008ff81f  call 0x8f6910            ; FilterDesc konstruktor (+4 := 0)
0x008ff847  mov dword ptr [eax+4], ecx   ; ★ FilterDesc+4 := a mode egésze
0x008ff851  mov dword ptr [edx+8], eax   ; FilterDesc+8 := a zerostate egésze
```

**A jelvény feltétele — a fogyasztó oldaláról.** A csempéket felépítő
`0x005d7c20` (1614 b) minden csempére:

```
0x005d7eb9  mov edx, [eax+0x14]      ; CGenericFilter vtable +0x14 = 0x008f6cc0
0x005d7ebc  call edx                 ;   -> this->desc->[+4]
0x005d7ec2  cmp eax, 1
0x005d7eca  sete byte ptr [esp+0x64] ; ★ a jelvény-jelző
   …
0x005d80d4  push 0xc96304            ; "editpanel/fx%d_adorn"
0x005d8108  cmp byte ptr [esp+0x64], 0
0x005d8111  mov eax, [edx+0x6c]      ; igaz  -> MUTAT
0x005d8116  mov eax, [edx+0x68]      ; hamis -> REJT
```

⇒ **A kék jelvény jelentése: `mode="oneclick"`.** Az „1" nem számláló és nem
erőforrás-index — az `oneclick` mód **enum-értéke**. Ezért nem is látható más
számjegy: a feltétel szigorúan `== 1`.

**Az effekt-csempék TELJES táblája — `0x00c7e5a0`, 36 rekord × 12 bájt.**
A rekord első mezője a mai szűrő azonosítója, a második a régi (örökölt)
azonosító vagy `NULL`. Tizenkét csempe fülenként, tehát **három effekt-fül**:

| # | csempe (mai id) | örökölt id | `mode` | jelvény |
|---|---|---|---|---|
| 1 | `unsharp2` | `unsharp` | effect | – |
| 2 | **`sepia`** | – | **oneclick** | **✔** |
| 3 | **`bw`** | – | **oneclick** | **✔** |
| 4 | **`warm`** | – | **oneclick** | **✔** |
| 5 | `PicnikGrain` | `grain` | effect | – |
| 6 | `PicnikTint` | `tint` | effect | – |
| 7 | `sat` | – | effect | – |
| 8 | `radblur` | – | effect | – |
| 9 | `glow2` | `glow` | effect | – |
| 10 | `ansel` | – | effect | – |
| 11 | `radsat` | – | effect | – |
| 12 | `dir_tint` | `radtint` | effect | – |
| 13 | `IR` | – | effect | – |
| 14 | `Lomo` | – | effect | – |
| 15 | `Holga` | – | effect | – |
| 16 | `HDR` | – | effect | – |
| 17 | `Cinemascope` | – | effect | – |
| 18 | `Orton` | – | effect | – |
| 19 | `Sixties` | – | effect | – |
| 20 | `Invert` | – | effect | – |
| 21 | `HeatMap` | `NightVision` | effect | – |
| 22 | `CrossProcess` | – | effect | – |
| 23 | `QuantizePalette` | – | effect | – |
| 24 | `TwoTone` | – | effect | – |
| 25 | `Boost` | – | effect | – |
| 26 | `Soften` | – | effect | – |
| 27 | `Vignette` | `Matte` | effect | – |
| 28 | `Pixelate` | `PicnikFocalPixelate` | effect | – |
| 29 | `FocalZoom` | – | effect | – |
| 30 | `PencilSketch` | – | effect | – |
| 31 | `Neon` | – | effect | – |
| 32 | `Comicize` | – | effect | – |
| 33 | `Border` | `RoundedEdges` | effect | – |
| 34 | `DropShadow` | – | effect | – |
| 35 | `MuseumMatte` | – | effect | – |
| 36 | `Polaroid` | – | effect | – |

**Ez oldja fel a #1869 „Filmszemcse nincs megjelölve" rejtvényét:** a
Filmszemcse csempéje a **`PicnikGrain`**-hez kötődik (`mode="effect"`), nem a
`grain`/`grain2`-höz — azok `oneclick`-ek ugyan, de **nincs csempéjük**. A 12
`oneclick` szűrőből csak három van a 36 csempe közt.

**A vizsgált bináris VERZIÓJA — mérve:** `Picasa3.exe` `3.9.141.259`
(`strings -el`), tehát a `research/copy_Picasa_3_7/` mappanév **félrevezető**;
a `filterdesc.xml` ugyanabból a telepítésből való. A „más verziót nézünk"
magyarázat ezzel **kizárva**.

> ⚠️ **Egy megfigyelés NEM illeszkedik**, és ezt nem söpörjük a szőnyeg alá: a
> tulajdonos **négy** jelvényt látott, a negyediket a **Színinvertálás**
> csempén (`Invert`, a 2. effekt-fül 8. csempéje). Az `Invert` viszont
> `mode="effect"` (a `filterdesc.xml` **egyetlen** `id="Invert"` sora, 986.).
> A fenti lánc szerint ott nem lehetne jelvény. Jegy: **#2125**.

**A lánc TELJES — nincs második út (#2125, mérve az indexen).** A jegy azt
kérdezte, van-e még egy író a `FilterDesc + 4`-re. Nincs, és a fogyasztói
oldalon sincs kerülőút. Négy egymástól független mérés:

| kérdés | mérés | eredmény |
|---|---|---|
| hol jön létre `FilterDesc`? | hívások a ctorra (`0x008f6910`) | **1** hívó: `0x008ff550`, a `filterdesc.xml` parsere |
| honnan kaphat nem-nulla értéket? | hívások a `mode`→egészre (`0x00900490`) | **1** hívó: ugyanaz a parser |
| felülírhatja-e más osztály a jelvény-gettert? | a `0x008f6cc0` mely vtable-ökben szerepel | **1** vtable: `CGenericFilter::vftable`, 5. slot (= +0x14) |
| van-e leszármazott/testvér, ami mást tesz az 5. slotba? | vtable-ök ≥12 azonos indexű közös slottal | **0** — a `CGenericFilter` vtable rokon nélküli |

Ötödikként a **fogyasztó** oldala: a csempéket felépítő `0x005d7c20`
összesen hét sztringet hivatkozik (`editpanel/fx%d`, `…_adorn`,
`editpanel/fxlabel%d`, `editpanel/fxpreview1`, `editpanel/fxthumbs`,
`_mod%s`, `_tab%d`) — **egyetlen** jelvény-erőforrás, az `fx%d_adorn`. Az
effekt-csempén tehát más díszítés nem is jelenhet meg.

> **Kontrollok** (a negatívumok önmagukban semmit sem érnének):
> a testvér-kereső ugyanezzel a küszöbbel az `AMgrDlg::vftable`-hez **9**
> rokont talál — tehát működik ott, ahol van mit találnia. A hívás-élek
> rögzítése sem hiányos: az index 78 901 `call`-élt tart 14 130 célfüggvényre.
> Ami **NEM** bizonyíték: a getter „0 közvetlen hivatkozása" — 300 véletlen
> vtable-slotból 275-nek szintén 0, mert az index a vtable-adatból induló
> hivatkozásokat nem rögzíti.

**Bizalmi fok:** a `mode`→egész tábla, a `FilterDesc+4` írása, a jelvény
feltétele és a 36 elemű csempe-tábla **megerősített** (közvetlen kiolvasás).

⛔ **MEGDŐLT (2026-09-04, #2125): NÉGY jelvény van, nem három.** A tulajdonos
felvételei (`research/#2061-effekt-latszik/`) fülenként ezt mutatják:

| effekt-fül | jelvényes csempék |
|---|---|
| 1. (Élesítés…Színátmenet) | **Szépia**, **Fekete-fehér**, **Melegítés** |
| 2. (Infravörös film…Kéttónusú) | **Színinvertálás** |
| 3. (Felpörgetés…Polaroid) | *egy sem* |

A `Színinvertálás` (`Invert`) `mode="effect"`, tehát a `mode`-ból levezetett
lánc szerint **nem lehetne** jelvénye — a jelvénye viszont **két különböző
felvételen** is látszik, eltérő szerkesztési állapot mellett.

##### ⛔ A „második író" hipotézis MEGDŐLT — nyolc független ellenőrzés (2026-09-04, #2125)

A #2125 azt kereste, **ki írja még** a `FilterDesc + 4`-et. **Senki.** Az
olcsó lánc kimerítve; mind a nyolc lépés a `filterdesc.xml`-t és a kódot
igazolja:

| # | amit ellenőriztem | eredmény |
|---:|---|---|
| 1 | a `FilterDesc` **konstruktorának** (`0x008f6910`) hívói, teljes `.text`-pásztázás | **pontosan egy**: `0x008ff81f`, az XML-elemző |
| 2 | a `+4` értékadás — első kézből olvasva | `0x008ff847` `mov [eax+4], ecx` = a `mode` egésze (a `+8` a `zerostate`, `0x008ff851`) |
| 3 | a jelvény-jelző **összes** írása a csempeépítőben (`0x005d7c20`, 1614 b) | **egyetlen**: `0x005d7eca` `sete`, a `cmp eax, 1`-ből |
| 4 | a jelvény-érték forrása | `call [vtbl+0x14]` a szűrőobjektumon |
| 5 | a `+0x14` getter (`0x008f6cc0` = `this->desc->[+4]`) hány vtáblában szerepel | **egyben**: `CGenericFilter::vftable` (`0x00cd184c`) |
| 6 | mind a **2856** RTTI-vtábla `+0x14` slotja: van-e konstans `1`-et adó vagy másik kétszeres indirekció | **nulla**, illetve **egy** (maga a `CGenericFilter`) |
| 7 | a csempe-tábla (`0x00c7e5a0`) mind a 36 rekordja, és minden id `mode`-ja az XML-ből | **három** `oneclick` (`sepia`, `bw`, `warm`), mind az 1. fülön; **nincs** ismételt `id` |
| 8 | a jelvény-elem a `respack.yt` `.tre`-jében | csempénként **egy** `fx<N>_adorn` (`m_fxadorner`) — más jelvény-réteg nincs |

⇒ **Ebben a `filterdesc.xml`-ben az `Invert` nem kaphat jelvényt**, és a
kódban nincs másik út. A felvétel viszont mutatja — és a képernyőkép
erősebb bizonyíték, mint a mi olvasatunk.

**A jelvény azonossága is ellenőrizve:** a `Színinvertálás` és a `Szépia`
jelvényét képpont-szinten nagyítva **ugyanaz az elem** (kék negyedkorong a
jobb alsó sarokban, fehér „1"), tehát nem másik rajz. **A csempe azonossága
is:** a `filter_Invert_label0` szövegtár-kulcs magyar értéke épp
„Színinvertálás", és a csempe-tábla 20. rekordja (2. fül, 8. hely) az
`Invert`.

⇒ **A maradék EGYETLEN magyarázat: a futó telepítés
`runtime\filterdesc.xml`-je ELTÉR a kutatási másolatunkétól**
(`research/copy_Picasa_3_7/…`). A Picasa `update/` mappával szállít, a
`filterdesc.xml` pedig futásidejű adatfájl, amit egy frissítés kicserélhet.
A telepítésben **egyetlen** `filterdesc.xml` van, és az `oneclick` szó is
csak abban fordul elő — más forrás tehát nincs.

**Amit ez eldönt:** a kérdés **nem a binárisban** van. A #2125 ezért
`blocked` + `felhasználóra-vár`, egyetlen, gépies kéréssel: a futó
telepítés `Picasa3\runtime\filterdesc.xml`-jéből az `Invert` sora.

#### A 21 örökölt szűrőből HÁROM ma is elérhető a felületről (#2148)

A 7. („örökölt") szerkesztő-fülünk bevezetője azt állította, hogy ezek a
szűrők „nem érhetők el a mai Picasában". **Három elemre ez nem igaz** — mind
a három út a binárisból kimérve:

| örökölt kulcs | hol érhető el a mai Picasában | bizonyíték |
|---|---|---|
| `radtint` | 1. effekt-fül, **12. csempe** (`dir_tint`), **Shifttel** | a `0x00c7e5a0` tábla 12. rekordjának másodlagos mezője (ld. fentebb) |
| `autobacklight` | Alapvető javítások fül, **egykattintásos gomb** | `editpanel/autobacklight` → `push "autobacklight"` + `call 0x6021d0` (`0x005d6848`) |
| `rainbow` | **Kiegyenesítés** gomb + **ALT** | `editpanel/horizonadjust` ágában `push 0x12` (**VK_MENU**) → `GetAsyncKeyState` → `push "rainbow"` (`0x005d6733`–`0x005d6746`) |

⚠️ A `rainbow` kapcsolója **ALT (`0x12`), nem Shift** — a csempék
másodlagosát a Shift (`0x10`) hozza elő. A két rejtett út **különböző
módosítót** használ; ezt ne mossuk össze.

**A `0x6021d0` a felületi „szűrőt alkalmaz" belépési pont**, és az egész
binárisban **két** hívója van (`xrefs`): a `0x005d59f0` szerkesztő-panel
(7 hívás) és a `0x005d3290` (1 hívás, futásidejű névvel). A panel hét
statikus szűrőneve **kimerítően**: `autolight` (Automatikus kontraszt),
`autocolor` (Automatikus szín), `rainbow`, `tilt` (Kiegyenesítés),
`enhance` („Jó napom van"), `autobacklight`, és egy dinamikus.

**A maradék 18-ra a mondat IGAZ.** Felületi vezérlőjük nincs; a
`0x008fc690` név-átfordító csak a **lánc betöltésekor** ismeri fel őket
(`repe cmpsb` névhasonlítás: `colorfix`, `triple`, `triple2`, `triple3` →
`finetune` / `finetune2`). Tizenhárom örökölt név egy tömbben ül
(`0x00cd05d0`–`0x00cd0650`): `contrast`, `gamma`, `dir_sharp`, `dir_brite`,
`dir_sat`, `linblur`, `autocontrast`, `backlight`, `colortemp`, `whitept`,
`triple2`, `triple`, **`debug`** — az utolsó fejlesztői eszköz, ezért marad
ki a fülünkről.

**Ráadás-lelet:** a `focalpixelate` kulcs sztringként **nincs benne** a
`Picasa3.exe`-ben (a `PicnikFocalPixelate` igen), a `filterdesc.xml`-ben
viszont **van** — tehát XML-vezérelt bejegyzés, nem beégetett. Ez
összhangban van a #567 „halott bejegyzés" magyarázatával.

~~**Amit ez NEM mond meg:** hogy a `rainbow` ALT-os ágát őrző globális
kapcsoló (`cmp byte ptr [0xd67849]`, `0x005d672b`) mikor nem nulla.~~
**LEZÁRVA (#2224, 2026-09-04):** a kapcsoló azt jelenti, hogy **a Picasa az
előtérben lévő alkalmazás** — hétköznapi kattintáskor tehát MINDIG 1. A
`rainbow` elérhetősége ezért **nem feltételes**: az ALT + Kiegyenesítés út
egy átlagos telepítésen él. A levezetés a lenti „A `rainbow` ALT-os ága"
szakaszban.

**Bizalmi fok: megerősített** — a három út, a kétféle módosító és a
`0x00d67849` jelentése egyaránt (közvetlen kiolvasás + diszasszemblálás).

#### A `GlowImageOperation` keverése: KÖZÖNSÉGES source-over (#2102)

A #2076 után nyitva maradt kérdés első fele **eldőlt**: a ragyogás-réteg
összeillesztése a képre nem tartalmaz semmilyen erősség-tagot.

**A hívási lánc** (mind kiolvasva, nem következtetve):

```
0x00bb8e10  a vtable-belépés: kiolvassa a nyolc attribútumot
   └─ 0x00bb8f70  a rajzoló (2579 b)
        ├─ 0x00bb89b0  a sugár-skálázó (xblur, yblur × lapméret)
        ├─ 0x00bcc2e0  a ragyogás-maszk építője (855 b) — IDE megy a strength
        └─ 0x00bb992d → 0x008f59d0  a kompozitáló (549 b)
                          └─ 0x008f4780  a képpont-mag (137 b)
```

**A rajzoló argumentumlistája — a BINÁRISBÓL levezetve.** Eddig ez csak a
Flash-analógiából volt meg (`GlowFilter`); most a `0x00bb8e10` veremépítése
adja, tehát a sorrend mérve van:

| # | mi | honnan | alapérték |
|---|---|---|---|
| 1 | forráskép | `[ebp+8]` | — |
| 2 | `color` (dword) | `+0x24`, `0x8eea90`-nel számmá | — |
| 3 | `glowalpha` (float) | `+0x2c` | **1,0** (`fld1`, `0x00bb8e4b`) |
| 4 | `xblur` (float) | `+0x34` | **1,0** (`0x00bb8e75`) |
| 5 | `yblur` (float) | `+0x3c` | **1,0** (`0x00bb8e95`) |
| 6 | **`strength`** (float) | `+0x44` | **0,0** (`fldz`, `0x00bb8eb5`) |
| 7 | `quality` (int) | `+0x4c` | **3** (`mov ebx, 3`, `0x00bb8ede`) |
| 8 | célkép | `[ebp+0x10]` | — |

⚠️ Két meglepetés, amit a Flash-analógia **nem** adott volna meg:

- a `strength` natív alapértéke **0,0**, nem 1,0 (a Flash `GlowFilter`-é 1,0);
- a `color` **alfa-bájtja beégetve `0xFF`** (`mov byte ptr [esp+0x3b], 0xff`,
  `0x00bb8e5f`) — a ragyogás színe mindig teljesen átlátszatlan, az
  átlátszóságot nem a szín hordozza.

**A képpont-mag (`0x008f4780`) — TELJES képlet.** SSE2, négy képpont
egyszerre; az alfa a **forrás** képpont 4. bájtja
(`pshuflw/pshufhw imm=0xff` = a 4 szóból a 3. indexű):

```
T   = src·a + dst·(255 − a)            ; 16 bites szorzatok, a = 0..255
out = (T + (T >> 8) + 1) >> 8          ; a /255 egész osztás gyors alakja
```

A két SSE-konstans **kiolvasva**: `0xcd0550` = `1` (nyolc `word`),
`0xcd0560` = `255` (nyolc `word`); a `pandn xmm4, xmm7` adja a `255 − a`-t.
A `0x008f59d0` mindössze a sor/oszlop-bejárás: a rect `[+8]`/`[+0xc]` mezői
a sorhatárok, a maradék képpontokra `movd` fut `movupd` helyett.

> **Következmény.** A keverés egy **szabványos source-over**, egyetlen
> erősség-, mód- vagy súlyparaméter nélkül. Tehát a `strength` **nem** a
> keverés súlya lehet — ezt a modellcsaládot a mérés **kizárja**. A mi
> `render/glimmer_ops.py::inner_glow`-unk épp ilyen súlyt vág `[0,1]`-re.

**Hol lép be a `strength`.** A `0x00bb9186` hívás hatodik dword-argumentuma
(`0x00bb913e  fstp dword ptr [esp+0xc]`, a `0x00bb9107  fld dword ptr [esp+0x218]`
értéke) — tehát a `0x00bcc2e0`-ban dől el, a maszképítéskor, nem a
kompozitáláskor.

**A `0x00bcc2e0` első strength-felhasználása — kvantálás.** A
`0x00bcc3d5`–`0x00bcc434` blokk:

```
0x00bcc3d5  fld   dword [esp+0x88]      ; strength
0x00bcc3dc  fsub  qword [0xc7e328]      ; − 1,0     (kiolvasva)
0x00bcc3e2  fmul  qword [0xc72150]      ; × 0,5     (kiolvasva)
0x00bcc3f3  call  0x529e10              ; ceilf     (ld. lent)
0x00bcc3f8  fmul  dword [esp+0x1c]      ; × n  (a struktúrából jövő egész)
0x00bcc401  fld1 / fadd / fxch          ; + 1,0
0x00bcc424  fistp qword [esp+0x20]      ; csonkoló kerekítés (or eax,0xc00)
0x00bcc42c  cmp eax, 0xff / ja          ; felső korlát 255
```

**A `0x00529e10` = `ceilf` — BIZONYÍTVA, nem feltételezve.** A wrapper a
`0x00c090f0`-t hívja (exponens-mezőt kicsomagoló, tört bitet nyíró SSE2
rutin); az hibaágon `0x00c12fd0`-t hívja a **`0x3ec`** kóddal. A `0x00c12fd0`
ugrótáblája (`0x00c1324c`, 13 bejegyzés, `0x3e8`-tól) a `0x3ec`-re a
`0x00c131d5` ágat választja, ami a **`0x00c43bac` = `"ceil"`** sztringet
teszi a névmezőbe. (A tábla többi neve: `log`, `log10`, `exp`, `atan`,
**`ceil`**, `floor`, `modf`, `sin`, `cos`, `tan` — tehát a hozzárendelés
egyértelmű.)

**Amit ebből MA állítani lehet — és amit nem.**

*Erős (a veremleképzés két független horgonyon ellenőrizve: `[esp+0x1f8]`
= 1. argumentum a prológusban, `[esp+0x214]`/`[esp+0x218]` = `xblur`/`yblur`
a sugár-skálázó hívásánál):*

> A `strength` ebbe a tagba **`ceil((strength − 1) / 2)`** alakban lép be,
> tehát **lépcsősen**, nem folytonosan.

Ennek azonnali, **ellenőrizhető** következménye: a `filterdesc.xml`
**minden** Glow-hívására (`1,1` · `1,2` · `1,3` · `1,4` · `1,5` és a
Vignette/Matte `[1..2]` csúszkája) `ceil((s−1)/2) = 1` — **állandó**. Csak
a pontosan `s = 1,0` eset ad `0`-t, és a következő lépcső `s > 3,0`-nál jön.

⇒ Ez megmagyarázza, miért illeszkedik a Vignette golden-készletére
kalibrált modellünk: **abban a tartományban ez a tag nem is változik.**

*NINCS MEG (a következő kör dolga):* a `0x00bcc2e0` további szakasza — a
`0x00bcc438`-tól induló második, szimmetrikus blokk operandusai, és hogy a
két kiszámolt, `255`-re vágott egész **mit** vezérel (menetszám? sugár?
alfa-szorzó?). A veremleképzés ott már nem követhető megbízhatóan kézzel:
**célzott dekompiláció** kell a `0x00bcc2e0`-ra. Amíg ez nincs meg, a
Comicize-eltérés oka sem magyarázható.

#### Méretfüggő elmosás-sugarak — a hét érintett szűrő

Ezek a képletek a képmérethez skálázódnak, hogy az effekt **arányos**
legyen (ugyanúgy nézzen ki kicsiben és nagyban):

| szűrő | képlet | σ egy 4000 px-es fotón |
|---|---|---|
| `Lomo` | `35·0,02·max(W,H)/2` = 0,35·max | 1400 |
| `Holga` | `0,5·max/2` és `0,4·max/2` | 1000 / 800 |
| `NightVision` | `35·0,02·max(W,H)/3` | 933 |
| `Matte` | `Blur·0,02·max(W,H)/4` (alap Blur=40) | 800 |
| `Vignette` | `Blur·0,02·max(W,H)/4` (alap Blur=35) | 700 |
| `Comicize` | `35·0,02·max(W,H)/2` (a második elmosás) | 1400 |
| `MuseumMatte` | `2·0,02·max(W,H)/4` = 0,01·max | 40 |

> **Implementációs csapda (#504).** Ha az `xblur`-t közvetlenül
> Gauss-σ-ként adjuk egy kernel-alapú elmosásnak (pl.
> `cv2.GaussianBlur(..., (0,0), sigma)`, ahol a kernel ≈ 8σ+1), a költség a
> kép méretével **köbösen** nő: egy 4000×3000-es fotón a Lomo egyetlen
> ragyogás-lépése RPi5-en **168 s** (mérés). Belső ragyogásnál erre nincs
> szükség: a bemenet mindig egy tömör téglalap alfa-maszk, aminek a
> Gauss-elmosása **zárt formában** (tengelyenként egy `erf`) számolható,
> sugártól független költséggel.

### 4.5 A művelet-készlet — a `filterdesc.xml` által HASZNÁLT 31 művelet

> ⚠️ **A „31" a HASZNÁLAT száma, nem a készleté.** A binárisban 35 művelet
> van **név szerint regisztrálva**, és 37 konkrét osztály létezik az
> RTTI-ben. A három leltár és a különbségük: ld. a lap végén, „HÁROM
> leltár" szakasz.

A `<effect>` blokkok **31 különböző** műveletet használnak. A `db` oszlop azt
mutatja, hányszor fordul elő; az attribútumok a fájlból kigyűjtve.

| művelet | db | attribútumok |
|---|---|---|
| `NestedImageOperation` | 31 | `BlendAlpha BlendMode Mask maskWithSourceAlpha dynamicAlphaCachePriority id` |
| `AdjustCurvesImageOperation` | 12 | `MasterCurve RedCurve GreenCurve BlueCurve` |
| `GetVarImageOperation` | 11 | `Name BlendMode Mask` |
| `SetVar` | 10 | `Name` |
| `BlurImageOperation` | 9 | `xblur yblur quality BlendAlpha BlendMode Mask` |
| `SimpleColorMatrixImageOperation` | 8 | `Brightness Contrast Saturation ContrastAndBrightnessLinked BlendAlpha Mask` |
| `GlowImageOperation` | 8 | `color glowalpha xblur yblur strength quality innerglow knockout BlendAlpha` |
| `AutoFixImageOperation` | 6 | — |
| `BorderImageOperation` | 5 | `outercolor innercolor outerthickness innerthickness cornerradius captionheight` |
| `ResizeImageOperation` | 5 | `width height smoothing ignoreObjects` |
| `NoiseImageOperation` | 5 | `low high channelOptions grayScale randomSeed BlendAlpha BlendMode` |
| `BWImageOperation` | 4 | `filtercolor` |
| `TintImageOperation` | 4 | `Color BlendAlpha BlendMode Mask` |
| `CircularGradientImageMask` | 4 | `width height xCenter yCenter innerRadius outerRadius innerAlpha outerAlpha` |
| `CropImageOperation` | 2 | `x y width height` |
| `SimpleBorderImageOperation` | 2 | `color top bottom left right` |
| `TiledImageMask` | 2 | `tileWidth tileHeight offsetX offsetY alphaMin width height` |
| `PixelateImageOperation` | 2 | `pixelWidth pixelHeight offsetX offsetY` |
| `ColorMatrixImageOperation` | 2 | `Matrix UseAlpha` |
| `DropShadowImageOperation` | 2 | `distance angle blurX blurY strength quality shadowColor shadowAlpha backgroundColor` |
| `LocalContrastImageOperation` | 2 | `Radius Strength BlendAlpha` |
| `MultiplyColorMatrixImageOperation` | 2 | `Multiplier` |
| `RadialBlurImageOperation` | 1 | `amount x y Mask ignoreObjects` |
| `HSVGradientMapImageOperation` | 1 | `gradientObjectArray hueOffset` |
| `IRImageOperation` | 1 | `greenglow greenglowalpha redweight BlendAlpha` |
| `EdgeDetectionBImageOperation` | 1 | `detail` |
| `GradientMapImageOperation` | 1 | `gradientArray` |
| `RotateImageOperation` | 1 | `degAngle borderColor padBorder` |
| `QuantizePaletteImageOperation` | 1 | `Steps Depth` |
| `TwoToneImageOperation` | 1 | `blackColor whiteColor` |

#### A csővezeték NEM lineáris: rétegek és nevesített regiszterek

Három szerkezeti elem, ami nélkül a receptek félreolvashatók:

1. **`NestedImageOperation`** — a gyerekei a **pillanatnyi kép másolatán**
   futnak, az eredmény pedig a `BlendMode`/`BlendAlpha`/`Mask` szerint
   keveredik vissza a szülőbe. Minden effekt legkülső burka egy ilyen, aminek
   a `BlendAlpha`-ja `{1-(_sldrFade.value/100)}` — **így valósul meg a Fade,
   egységesen, mind a 31 effektnél.**
2. **`SetVar Name="A"` / `GetVarImageOperation Name="A"`** — nevesített
   képregiszter: elmenti a pillanatnyi képet, később `BlendMode`-dal
   visszakeveri. Négy effekt használja: `Comicize` (6 pár), `LocalContrast`
   (2/3), `Neon`, `PencilSketch`.
3. **`Mask`** — bármely művelet korlátozható egy `CircularGradientImageMask`
   vagy `TiledImageMask` objektumra hivatkozva (`Mask="{_msk}"`).

Példa (`PencilSketch`, a teljes recept):

```xml
<BWImageOperation/> <AutoFixImageOperation/>
<SetVar Name="A"/>                                  <!-- elmentjük -->
<NestedImageOperation BlendMode="{BlendMode.ADD}">  <!-- másolaton dolgozik -->
  <AdjustCurvesImageOperation MasterCurve="{[{x:0,y:255},{x:255,y:0}]}"/>
  <BlurImageOperation xblur="{_sldrRadius.value}" .../>
</NestedImageOperation>                             <!-- ADD-dal vissza -->
<GetVarImageOperation Name="A" BlendMode="{BlendMode.OVERLAY}"/>
<AutoFixImageOperation/> <AdjustCurvesImageOperation .../>
```

#### Végleges bizonyíték a Flash-örökségre

A fájl **szó szerint ActionScript 3 osztálykonstansokat** használ:
`quality="{BitmapFilterQuality.HIGH}"` (a `flash.filters.BitmapFilterQuality`,
`HIGH = 3`) és `BlendMode.ADD` / `.OVERLAY` / `.SCREEN` / `.LIGHTEN` (a
`flash.display.BlendMode`). Ez zárja le a `quality` kérdését: **az elmosás
átfutásainak száma**, és a Glimmer-effektekben végig 3.

### 4.6 A natív motor többet tud, mint amit a fájl használ

A `Picasa3.exe` MSVC-RTTI nevei **69 `glimmer::` osztályt** őriznek, ebből
**32 nem szerepel a `filterdesc.xml`-ben**. Ez azt jelenti, hogy a fájl a
motornak csak egy részhalmazát szólítja meg.

**A végrehajtási modell: verem-alapú utasításlista.** A deklaratív XML-t a
motor `glimmer::EffectParser`-rel utasításokra fordítja:

> `OpInstruction`, `ApplyInstruction`, `BlendInstruction`, `MaskInstruction`,
> `PartialMaskInstruction`, `MaskWithSourceAlphaInstruction`,
> `DupeInstruction`, `PopInstruction`, `SetVarInstruction`,
> `GetVarInstruction`, `ClearVarInstruction`, `NamedVarInstruction`,
> `ReExecutingInstruction`

A `Dupe`/`Pop` pár elárulja, hogy **verem** van mögötte: a 4.5-ben leírt
`NestedImageOperation` valójában `Dupe → (gyerekek) → Blend → Pop`-ra fordul,
a `SetVar`/`GetVar` pedig a verem melletti nevesített regiszterekre. A
`ReExecutingInstruction` a csúszkamozgatás közbeni újraszámolás
(`dynamic*CachePriority` attribútumok) végrehajtója.

**Képi műveletek, amikre a `filterdesc.xml` nem hivatkozik:**

| osztály | mire utal |
|---|---|
| `ShaderImageOperation` | programozható shader-lépés a láncban |
| `SharpenImageOperation` | a natív élesítés (`unsharp`) |
| `ExposureImageOperation` | expozíció (a `finetune` „fill light" családja) |
| `PaletteMapImageOperation` | paletta-leképezés |
| `EdgeDetectionSobelImageOperation` | Sobel (a fájl csak az `EdgeDetectionB`-t hívja) |
| `BlendImageOperation` | önálló keverő-lépés |
| `PaintMaskPlusImageMask` | **festett** maszk (ecsettel) |
| `ShapeGradientImageMask` | nem körkörös, alakzat-alapú színátmenetes maszk |

A festett maszkhoz tartozó vezérlők is megvannak (`BrushSizeSlider`,
`CircularBrush`), valamint két, a fájlban nem használt vezérlőtípus
(`RadioButton`, `StaticRangeSlider`). Ezek a `mode="paint"` szűrőket
(`PicnikTint`, `Soften` — `cnt:PaintEffectCanvas`) szolgálják ki: ott a
felhasználó **ecsettel jelöli ki**, hol hasson az effekt.

> **Figyelem:** a `ShaderImageOperation` léte önmagában nem bizonyítja, hogy a
> Picasa GPU-t használt az effektekhez — a binárisban **nincs** `ps_*`/`vs_*`
> shader-bájtkód vagy `d3dx`/`glsl` nyom (keresve: 0 találat). Az osztály
> létezik, a használatára nincs bizonyíték.

### 4.7 A 37 token cáfoló auditja és a két rejtett keverési mód (2026-08-14)

> **Helyesbítés:** a korábbi „37 nem használt attribútum” nem valódi
> attribútumleltár volt. Egy széles címtartomány azonosítószerű szövegeit
> hasonlította a nyers XML-hez kis-/nagybetűérzékenyen. Így XMP-mezők,
> vezérlőtípusok, enumértékek és belső factory-nevek is bekerültek.

A natív attribútumkereső (`0x008eb160`) ASCII-kis-/nagybetűfüggetlen. Ezért a
`brightness/Brightness`, `grayscale/grayScale` és `multiplier/Multiplier`
párok ugyanazok az **élő, kiadott mezők**, nem három rejtett képesség.
Biztos hamis pozitív például a `Rating`, `RegionInfo`, `Regions`, `normalized`
(XMP), a `Number`, `NumberPlus`, `ResizingCheckbox` (vezérlőtípus), valamint a
`False`, `MEDIUM`, `horizontal` (érték). A `Script` elemtípus, a
`TiledImageTileMask` belső factory/cache-típus.

Valódi, működő, de kiadott receptben nem használt mezők többek között:
`ColorMaps`, `ExposureAdjustmentStops`, `alphaMax`, `aspectRatio`, `blacks`,
`bytecode`, `direction`, `exposure`, `flipH`, `flipV`, `padding*`, `params`,
`radAngle`, `scaleWidth`, `scaleHeight`, `sharpness`. Ezek parserében nincs
felhasználói min/max tartomány; recept vagy valós adat nélkül nem indokolnak
új felületet. `_clsVibrance` és `HexCells` működő shader-selector, de egyik
kiadott effekt sem hivatkozza őket.

#### `PaletteMapImageOperation`: Picasa-pontos keverések

A `0x00bb7e40` fogyasztó öt végrehajtót választ. Jelölje `x` a 0–255
LUT-bemenetet, `c` a térképszín csatornáját, `a` az alfát:

```text
Softlight: q=c&0xfe
  x<128  -> x*(q+128)/255
  x>=128 -> (65025-(382-q)*(255-x))/255

Hardlight:
  x<=127 -> 2*x*c/255
  x>127  -> 2*(32512-(255-x)*(255-c))/255
  x=c=255 -> pontosan 255

Multiply = x*c/255
Screen   = (65025-(255-x)*(255-c))/255
Normal   = ((255-a)*c+a*x)/255
```

Az eredményt 0–255 közé vágja, majd `+0,5` után egészre alakítja. A két első
képlet **nem** a szokásos Photoshop/CSS-változat. A főprogram öt címe rendre
`0x00bb82b0`, `0x00bb8330`, `0x00bb83b0`, `0x00bb83d0`, `0x00bb8400`;
a külön PhotoViewer utasításszinten azonos megvalósítása független kontroll.

**Fejlesztési következmény:** a közös Glimmer-primitívekhez a két Picasa-pontos
mód kell, teljes LUT-határteszttel. Általános filterdesc-parserben az
attribútumnév ASCII-case-insensitive legyen. Kiadatlan motorparaméterhez ne
készüljön UI kiadott recept vagy valós adat nélkül.

## 5. Következmények a PicasaPy-ra

1. A `.picasa.ini` **paraméter-validáció** most már tartomány-alapú lehet
   (`sat ∈ [−1,1]`, `finetune2` hőmérséklet `∈ [−1,1]`, highlights/shadows
   `∈ [0, 0,48]`) — a tartományon kívüli érték gyanús adat, nem néma
   elfogadás.
2. A **`finetune` v1 → v2 átszámítás** ezentúl egzakt: a hőmérséklet-tengely
   skálája **kétszeres** (`v2 = 2 · v1`), nem külön LUT-ot igényel. Ezt a
   `filters-decoded.md` 1. körének „a v1 temp-skálája más" megfigyelése
   mellé kell tenni és méréssel megerősíteni.
3. A `fullres` / `slow` / `resize` jelzők alapján a renderelő **három
   sávra** bontható: olcsó-előnézetes, teljes-felbontású, méretváltó.
4. A szerkesztő UI csúszkáinak **feliratai, tartományai és alapértékei**
   közvetlenül átvehetők — nincs többé találgatás, hogy egy csúszka
   0–100-as vagy 0–1-es.
5. Az effekt-lista `label`/`tooltip` szövege az angol eredeti; a magyar
   megfelelő a `Picasa3i18n.dll`-ből jön (ld. `picasa-hu-terminology.md`).

## 6. Reprodukálhatóság

A táblázatok generálása (a névtér-előtagok miatt az `<effect>` blokkot
előbb el kell távolítani, különben az `ElementTree` „unbound prefix"
hibával áll meg):

```python
import re, xml.etree.ElementTree as ET
src = open("runtime/filterdesc.xml", encoding="utf8").read()
root = ET.fromstring(re.sub(r"<effect>.*?</effect>", "", src, flags=re.S))
```

### 4.8 A Glimmer-műveletek magja — az `apply` slot szabálya és az `AdjustCurves` (#626)

**Futás:** 2026-08-13, Ghidra 12.1.2, ugyanaz a bináris. 20 gyökér, 3 szint,
**223 dekompilált függvény**. Nyers kimenet: `referencia/dekompilalt-626/`.

#### A vtable-szabály — pontosítva

A korábbi kör megállapítása („az `apply` a 6. slot") **csak a 8 slotos
osztályokra igaz**. A vtable-ek két családra oszlanak:

| | slot 0–2 | slot 3–5, 7 | **slot 6** | **slot 8** |
|---|---|---|---|---|
| **8 slotos** | dtor / free / attribútum-olvasás | közös alaposztály | **saját `apply`** | — |
| **9 slotos** | ugyanaz | közös alaposztály | **KÖZÖS alkalmazó** | **saját mag** |

A 9 slotos család két közös alkalmazón osztozik:

- **`0x00bb7c80`** — LUT-alkalmazó: `AutoFix`, `AdjustCurves`, `TwoTone`,
  `Exposure`, `HSVGradientMap`, `GradientMap`, `PaletteMap`
- **`0x00bc16b0`** — színmátrix-alkalmazó: `BW`, `SimpleColorMatrix`,
  `ColorMatrix`, `MultiplyColorMatrix`

> **Helyesbítés:** a `referencia/dekompilalt/glimmer-apply.c`-ben
> `GLIMMER_AutoFix_APPLY` és `GLIMMER_BW_APPLY` néven szereplő két függvény
> **nem** az AutoFix, illetve a BW saját magja, hanem ez a két **megosztott
> alkalmazó**. Az osztályspecifikus rész a 8. slotban van.

A szabály mind a 10 korábban dekompilált művelet címére illeszkedik (ellenőrizve).

#### `AdjustCurves` — **természetes köbös spline** (9 effekt)

A LUT-építő (`0x00bcd1e0`) minden `i ∈ 0…255` értékre:

```c
v = MasterCurve(i);                 // előbb a MESTER görbe
R = clamp(round(RedCurve(v)));      // majd a CSATORNA-görbe ANNAK az eredményén
G = clamp(round(GreenCurve(v)));
B = clamp(round(BlueCurve(v)));
LUT_R[i] = R << 16 | 0xff000000;    // eltolva a csatorna helyére, hogy az
LUT_G[i] = G << 8;                  // alkalmazó csak OR-ozni tudjon
LUT_B[i] = B;
```

**Két dolog, ami eddig nem volt tudva:**

1. **A mester- és a csatorna-görbe kompozíció**, nem összeadás:
   `out_R = RedCurve(MasterCurve(i))`.
2. **A görbe kiértékelése természetes köbös spline** (`0x008f3290`), nem
   lineáris interpoláció. A képlet szó szerint a Numerical Recipes `splint`:

```
h = x[j+1] − x[j]
A = (x[j+1] − x)/h        B = (x − x[j])/h
y = A·y[j] + B·y[j+1] + ((A³−A)·y2[j] + (B³−B)·y2[j+1]) · h²/6
```

ahol `y2[]` a második deriváltak tömbje, amit a `0x008f33b0` számol ki
(a klasszikus tridiagonális megoldás `2.0`-s főátlóval és a `6.0`-s
osztott differenciával — **természetes** spline, azaz `y2[0] = y2[n−1] = 0`).
A töréspont-keresés **bináris keresés**.

> ⚠️ **Ez mérhető eltérés.** A `filterdesc.xml` görbéire lineáris és spline
> interpolációval számolva:
>
> | effekt | pont | max eltérés | átlagos |
> |---|---:|---:|---:|
> | **Sixties** | 3 | **21,6 szint** | 8,4 |
> | **Cinemascope** | 5 | **17,5 szint** | 6,8 |
>
> Ez **hússzorosa** a ditherelés ±1-es tűrésének — szemmel látható.
> A kétpontos görbéknél (Invert, Neon, PencilSketch) a kettő azonos.

#### `SimpleColorMatrix` — a `ContrastAndBrightnessLinked` jelentése (8 effekt)

A mag (`0x00bb6400`) öt attribútumot olvas, majd **a jelzőtől függően más
sorrendben** fűzi a mátrixokat:

```c
telítettség(m, Saturation);
if (ContrastAndBrightnessLinked)  egyuttes(m, Brightness, Contrast);   // EGY lépés
else                            { kontraszt(m, Contrast); fenyero(m, Brightness); }
otodik_op(m, param5);
```

Vagyis a jelző **nem** finomhangolás: **külön kódutat** választ. Az egyes
mátrixok pontos együtthatói a `0x008f1d00` / `0x008f1bd0` / `0x008f1af0` /
`0x008f2040` / `0x008f1e70` függvényekben vannak — ezek dekompilálva a nyers
kimenetben, de számszerű feldolgozásuk még hátravan.

#### A kör többi eredménye

Dekompilálva és archiválva: `Border`, `DropShadow`, `Rotate`, `SimpleBorder`,
`Crop`, `Resize`, `QuantizePalette`, `IR`, `EdgeDetectionB`, `Tiled`,
`Sharpen`, `TwoTone`, `ColorMatrix`, `MultiplyColorMatrix`, `HSVGradientMap`,
`Exposure`. Ezek számszerű feldolgozása a következő kör tárgya — a **Polaroid**
két érzékeny művelete (`DropShadow`, `Rotate`) is köztük van.

### 4.9 A `SimpleColorMatrix` öt mátrixa — SZÁMSZERŰEN (2026-08-14, #626)

A 4.8 még csak a függvénycímeket adta meg. Az akkori kimenetből
(`referencia/dekompilalt-626/`) most kiolvasva mind az öt mátrix-építő. A közös
alkalmazó (`0x008f28d0`) egy **5×5 affin színmátrixot** szoroz az akkumulálthoz;
a mátrix a 0…255 skálán működik (a negyedik oszlop az eltolás).

Ez **nyolc effektet** érint, amelyek a `SimpleColorMatrix` műveletet használják.

#### Telítettség (`0x008f1d00`)

```c
if (s > 0)  k = 1.0f + (s * 3.0f) / 100.0f;    // +100 -> k = 4.0
else        k = 1.0f + s / 100.0f;             // -100 -> k = 0.0 (szürke)
w  = 1.0f - k;
rw = w * 0.3086f;  gw = w * 0.6094f;  bw = w * 0.0820f;

R' = (k + rw)*R +      gw *G +      bw *B
G' =      rw *R + (k + gw)*G +      bw *B
B' =      rw *R +      gw *G + (k + bw)*B
```

> ⚠️ **Két buktató.** (1) A csúszka **aszimmetrikus**: a pozitív oldal
> háromszoros skálázást kap, a negatív nem. (2) A luminancia-súlyok
> **0,3086 / 0,6094 / 0,0820** — ez a Haeberli-féle klasszikus készlet, **nem**
> a Rec.601 (0,299/0,587/0,114) és **nem** a Rec.709 (0,2126/0,7152/0,0722).
> Rec.601-gyel megvalósítva látható színeltolás keletkezik.

#### Fényerő (`0x008f1af0`) — tisztán additív

```c
b = clamp(b, -100, 100);
R' = R + b;   G' = G + b;   B' = B + b;
```

#### Kontraszt (`0x008f1bd0`) — TÁBLÁZATOS, nincs rá képlet

```c
c = clamp(c, -100, 100);
k = 1.0f + kontraszt_gorbe(c);      // 0x008f2990
if (|k - 1.0f| < eps) return;       // nincs teendő
t = (1.0f - k) * 127.0f * 0.5f;     // = (1-k) * 63.5
R' = k*R + t;  G' = k*G + t;  B' = k*B + t;
```

ahol a görbe:

```c
float kontraszt_gorbe(float c) {
    if (c == 0)  return 0.0f;
    if (c <  0)  return c / 100.0f;             // ZÁRT: -100 -> -1 (k = 0, teljes szürke)
    // c > 0: 101 elemű TÁBLÁZAT lineáris interpolációval
    i = (int)floorf(c);  f = c - i;
    return (f < eps) ? T[i] : (1-f)*T[i] + f*T[i+1];
}
```

A `T[]` tábla a `0x00c7d688` címen (fájloffszet `0x87d688`), **101 darab
`float`**, 0,0-tól 10,0-ig, **kézzel hangolt, szakaszonként más lépésközzel**:

| csúszka | 0 | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `T` | 0,00 | 0,12 | 0,25 | 0,44 | 0,71 | 1,00 | 1,60 | 2,37 | 4,00 | 7,30 | 10,00 |

A lépésköz 0,01-ről (0–16) 0,015-re (16–23), 0,02-re (23–33), 0,03-ra (33–50),
0,06-ra (50–67), 0,125-re (67–75), majd egyre nagyobbra nő. **Semmilyen zárt
képlet nem illeszkedik rá** (a legjobb exponenciális illesztés 0,64-gyel téved),
tehát a táblát **át kell venni**. Teljes lista:
`referencia/kontraszt-tabla.csv` (privát repó).

#### Együttes fényerő + kontraszt (`0x008f2040`) — a `ContrastAndBrightnessLinked` ág

```c
k = 1.0f + kontraszt_gorbe(kontraszt);           // ugyanaz a tábla
t = ((k + 1.0f) * 127.5f * fenyero) / 100.0f  +  (127.5f - k * 127.5f);
R' = k*R + t;   G' = k*G + t;   B' = k*B + t;
```

> ⚠️ **A két kódút tényleg különböző eredményt ad**, ahogy a 4.8 sejtette — és
> most már számszerűen látszik, miben: a **külön** kontraszt a `63,5` érték
> körül forgat (`t = (1−k)·63,5`), az **együttes** viszont a valódi középszürke,
> `127,5` körül (`t = (1−k)·127,5 + …`). A fényerő-tag súlya `127,5·(k+1)/100`,
> vagyis **erős kontraszt mellett a fényerő is erősebben hat**.
>
> A `63,5`-ös fixpont meglepő (a középszürke fele). A dekompilátorban
> `(1.0 - k) * 127.0 * 0.5` alakban áll; a másik ágban viszont explicit
> `127.5 - k*127.5` szerepel, tehát nem fordítási artefaktum. **Referencia-
> exporttal érdemes ellenőrizni**, mielőtt véglegesítjük.

#### Színárnyalat-forgatás (`0x008f1e70`)

`h = clamp(h, -180, 180)`, majd `szog = h/180 · π`, és `sin`/`cos`
(`0x00c29d20`, `0x00c285f0`) alapján a szokásos hue-rotation mátrix.

> A mátrix együtthatói **nem olvashatók ki** a dekompilátumból: az FPU-veremben
> mennek át, a `FUN_008f28d0` argumentumlistája üresen látszik. A szerkezet
> (szögkorlát, fok→radián, sin/cos) biztos; a konkrét együtthatók
> **feltételesek** — a Haeberli-féle hue-rotation a valószínű, de ez még nincs
> bizonyítva.

### 4.10 `Sharpen` és `Exposure` — a kernel, amit a `filterdesc.xml` NEM ad meg (2026-08-14, #626)

A 4.9-hez hasonlóan ez is a meglévő `referencia/dekompilalt-626/` kimenetből
került elő, új futtatás nélkül. Ez a két művelet azért fontos, mert a
`filterdesc.xml` csak a **paraméternevet** adja meg — a tényleges pixelműveletet
nem.

#### `Sharpen` (`0x00bbf9e0`) — 3×3 konvolúció, teljesen megvan

```c
a = clamp(amount, 0, 100);       // a csúszka értéke
w = a / -100.0f;                 // NEGATÍV súly a nyolc szomszédra
c = 1.0f - w * 8.0f;             // = 1 + 8*a/100  — a középső súly

kernel =  [ w  w  w ]
          [ w  c  w ]
          [ w  w  w ]
```

**Energiamegőrző:** `8w + c = 1,0` minden `a`-ra, tehát egyenletes felületen
nincs fényerő-eltolás. A csúszka végén (`a = 100`) `w = −1`, `c = 9` — ez a
klasszikus erős Laplace-élesítő.

#### `Exposure` (`0x00bc1ba0` → `0x00bc1c80`) — négy csúszka, négy görbe

A művelet egy 256 elemű LUT-ot épít, és **négy külön tónusgörbét fűz egymás
után**, mindegyiket a 4.8-ból ismert **természetes köbös spline-nal**
(`0x008f3290`) kiértékelve. A csúszkák sorrendje a `.picasa.ini`-beli sorrend
(4.1). A töréspontok (x, y), `p` = az adott csúszka értéke:

**3. csúszka — árnyékok** (`0x008f2b30` egy ötpontos görbét kap):

| x | y |
|---:|---|
| 0 | 0 |
| 6 | `42·p + 6` |
| 36 | `112·p + 36` |
| 126 | `72·p + 126` |
| 255 | 255 |

> Figyeld meg, hogy az `y` konstans tagja **pontosan az `x`** — `p = 0`-nál a
> görbe az identitás. Ez erős jel arra, hogy jól olvastuk ki a pontokat.

**4. csúszka — csúcsfények** (pontonként, `0x008f2c70`):

```
(0, 0)
ha (68·p > 1):        (68·p, 0)                    // a fekete pont eltolása
ha (p > 0.5):  t = 2·p − 1
               (127, 118 − 41·t)
               (188, 192 − 12·t)
egyébként:     (127, 127 − 4.5·p)
               (188, 188 + 2·p)
(255, 255)
```

**2. csúszka — S-görbés kontraszt**, a 128 körül forgatva:

| x | y |
|---:|---|
| 0 | 0 |
| 64 | `64 − 23·p` |
| 128 | 128 |
| 192 | `192 + 27·p` |
| 255 | 255 |

**1. csúszka — expozíció**: nem görbe, hanem **eltolás görbe-térben**:

```c
v = gorbe0(i);                 // 0x008f3290 — spline-kiértékelés
v = gorbe0_inverz(26*p + v);   // 0x008f2e00
// majd a maradék három görbe egymás után
```

A `0x008f2e00` (1168 b) **a görbe inverzét** keresi: végigmegy a spline-on
egész lépésekben, minden `[x, x+1]` szakaszra eltárolja a `[min, max]`
kimeneti tartományt, és ebből egy visszakereső táblát épít (`+0x10`), amiben
lineárisan interpolál. Vagyis az expozíció-csúszka **a görbe kimeneti terében
tol el `26·p`-vel, majd visszatér a képpont-térbe** — ez a klasszikus
„expozíció perceptuális térben" megoldás, nem egyszerű szorzás vagy összeadás.

> A `26`-os szorzó és az inverz-tábla szerkezete biztos. Az, hogy melyik
> görbének az inverzét használja (a négy közül), a dekompilátumból nem
> egyértelmű — ez **feltételes**.

A záró lépés minden `i ∈ 0…255`-re: a négy görbe egymás utáni kiértékelése,
`clamp(0, 255)`, kerekítés, majd a LUT három csatorna-változatba tárolása
(`<<16`, `<<8`, `<<0`) — ugyanaz a „csak OR-ozni kell" minta, mint az
`AdjustCurves`-nél (4.8).

### 4.11 `Tiled`, `EdgeDetectionB` és a Sobel-változat (2026-08-14, #626)

Két célzott kör futott ezekre párhuzamosan (nyers kimenet:
`referencia/dekompilalt-pakolo/script-DecompileTiled.log`, `-Edge.log`).

#### `Tiled` — **maszk**, nem képművelet (TELJES, 2026-08-14)

Az osztály neve `glimmer::TiledImageMask`, nem `…ImageOperation`.

**A csempe előállítása** (`0x00bbaa90`). A maszk nyolc paramétert tárol —
négy egész margót (`+0x18` bal, `+0x1c` felső, `+0x20` jobb, `+0x24` alsó) és
két skálát (`+0x10` x, `+0x14` y; alapérték **0,8**):

```c
w0 = kepSzelesseg - jobb  - bal;      // a margókkal levágott belső terület
h0 = kepMagassag  - also  - felso;
w  = w0 * xSkala;                     // a méretezett csempe
h  = h0 * ySkala;
x  = bal   - (w - w0) * 0.5f;         // a méretezés a KÖZÉPPONT körül történik
y  = felso - (h - h0) * 0.5f;
```

A gyorsítótár-kulcsot ugyanez a nyolc érték adja
(`"-%d-%d-%d-%d-%g-%g-%g-%g"`, `0x00bba980`), tehát a paraméterkészlet teljes.

**A csempézés** (`0x00bba670`):

```c
oszlopok = kepSzelesseg / csempeSzelesseg;     // EGÉSZ osztás
sorok    = kepMagassag  / csempeMagassag;
ox = round(param[10]);   oy = round(param[11]);   // eltolás

for (r = 0; r <= sorok; r++)
  for (c = 0; c <= oszlopok; c++) {
      x = csempeSzelesseg * c + (kepSzelesseg - rajzoltSzelesseg)/2 + ox;
      y = csempeMagassag  * r + (kepMagassag  - rajzoltMagassag )/2 + oy;
      rajzol(csempe, x, y);
  }
```

Két részlet, ami nélkül nem stimmel: a ciklus **`<=`**, tehát mindkét irányban
**eggyel több** csempe készül, mint amennyi elférne (ez fedi le a jobb és alsó
peremet), és a csempe a rendelkezésre álló területhez képest **középre
igazítva** indul, nem a bal felső sarokból.

##### ⭐ A csempe rajzolása: KÉTMEGÁLLÓS színátmenet, közös a kör-maszkkal (2026-09-05, #2476)

A `0x00bbaa90` a méretezett téglalap kiszámítása után **két** függvényt hív:
`0x008f3840` (`0x00bbaca9`, öt float — a téglalap) és `0x008f3970`
(`0x00bbacc3`, 2158 b). **Ugyanezt a párost hívja a
`CircularGradientImageMask` előállítója is** (`0x00bc2a50`, a hívás
`0x00bc2d1d`), és **ugyanazzal a harmadik argumentummal: 2.**

A harmadik argumentum **nem alakzat-azonosító, hanem MEGÁLLÓSZÁM.** A
`0x008f3970` az `[ebp+8]`-at bájttömbként olvassa (`0x008f39c2`
`movzx ecx, byte ptr [ecx]`), és `[ebp+0xc] − 1` hosszú cikluson hasonlítja
a szomszédos elemeket (`0x008f39dd` `lea ecx,[esi-1]`, `0x008f39f6`–
`0x008f3a01`). A harmadik hívó (`0x008ed730`) **15** megállót ad át
(`0x008edcf9` `push 0xf`).

⇒ A féltónusos pont pereme **nem kemény küszöb**, hanem rámpa két megálló
között — ugyanaz a primitív, mint a kör-maszké. A csempe alapból a cella
**0,8-szeresére** méretezve, középre igazítva (ld. fent).

⚠️ **NINCS visszaolvasva**, hol áll pontosan a két megálló (a
`0x008f3840` öt floatja és a `0x00bbac13`–`0x00bbac39` blokk 1/0 értékei
adnák meg). A mért kompozit profil és a hatás a mi kimenetünkre:
`filters-decoded.md`, „A Comicize PONTMASZKJA".

#### `EdgeDetectionSobel` — a kernel teljesen megvan

A `glimmer::EdgeDetectionSobelImageOperation` 6. slotja (`0x00bb6620`) egy
jelzőtől függően két 3×3 kernel közül választ:

```
függőleges élek:            vízszintes élek:
  [ -2   0   2 ]              [  2   4   2 ]
  [ -4   0   4 ]              [  0   0   0 ]
  [ -2   0   2 ]              [ -2  -4  -2 ]
```

Ez a **klasszikus Sobel kétszeres súlyokkal** (a szokásos ±1/±2 helyett ±2/±4).
A konvolúciót ugyanaz a 3×3 mag futtatja, mint a `Sharpen`-nél (`0x00bbfca0`) —
ott a szomszéd-eltolások (`±1`, `±sor`, `±sor±1`) a dekompilátumban közvetlenül
látszanak, ami a 4.10-es `Sharpen`-kernel olvasatát is megerősíti.

#### `EdgeDetectionB` — NEM konvolúció

> ⚠️ **Helyesbítés a korábbi feltevéshez.** A 6. slot (`0x00bbcdd0`) egyetlen
> értéket (`100 − csúszka`) tesz egy egyelemű paraméterlistába, majd a
> `0x009a8ca0`-t hívja. Ez **nem szűrő-diszpécser**, hanem egy 40 bájtos,
> hivatkozásszámlált rajzoló-objektum **értékadó operátora** — vagyis a
> `Sharpen`-nél és mindenhol máshol is csak másol. A `EdgeDetectionB` tényleges
> élkiemelése tehát **nem a művelet-osztályban van**, és ebből a körből sem
> került elő.
>
> ✅ **MEGFEJTVE (2026-08-14, második nekifutás).** Nincs rejtett kernel:
> az `EdgeDetectionBImageOperation` a **`NestedImageOperation`-ből származik**,
> vagyis **összetett művelet**, amely a gyerekeit **kódban** építi fel (nem az
> XML-ből — a `filterdesc.xml` csak egyetlen `detail="50"` attribútumot ad neki).
>
> A belső csővezeték az 1. slotban (`0x00bbca60`) épül fel, ebben a sorrendben:
>
> | # | osztály | megjegyzés |
> |---|---|---|
> | 1 | `BlurImageOperation(2.0f, 2.0f)` | 2×2 elmosás |
> | 2 | `SimpleColorMatrixImageOperation` | **ez a `+0x34` mező** — ide megy a `100 − detail` |
> | 3 | `SetVar("edgedetectimgop_orig")` | a köztes kép elmentése |
> | 4 | **`EdgeDetectionSobelImageOperation(0)`** | Sobel, első irány |
> | 5 | `…` + `"horizontal"` | Sobel, második irány |
> | 6 | `SetVar` / `GetVar` + kompozíció | a két irány egyesítése az eredetivel |
>
> **Minden komponens ismert:** a Sobel-kernelek fent, a `SimpleColorMatrix`
> matematikája a 4.9-ben, a `Blur` a `picasa-native-filter-workers.md` 4.2-ben.
> A `detail` csúszka a `SimpleColorMatrix` egyetlen paraméterébe megy
> `100 − detail` alakban.
>
> **Ami maradt:** a `SimpleColorMatrix` melyik paramétere ez (telítettség /
> kontraszt / fényerő). Egy golden-összevetés eldönti.
>
> ✅ **LEZÁRVA (2026-08-17, #878).** A golden-összevetés megtörtént (a #685
> mérőszettjének `neon__alap.jpg` párja — a `Neon` az `EdgeDetectionB`
> EGYETLEN hívója a fájlban): a **kontraszt** illeszkedik. Egyúttal a fenti
> lépéstábla is pontosításra szorult, ld. lent.

#### `EdgeDetectionB` — a TELJES lépéssor (2026-08-17, #878)

A dekompilátum (`script-DecompileEdge.log`, 3321. sortól) két olyan lépést
tartalmaz, ami a fenti hatsoros olvasatból kimaradt:

| # | natív hívás | mit épít |
|---|---|---|
| 1 | `FUN_00bb4c40(2.0f, 2.0f, 2)` | `Blur(xblur=2, yblur=2, quality=2)` |
| 2 | `FUN_00bb6150()` → `+0x34` | `SimpleColorMatrix` — **kontraszt = `100 − detail`** |
| 3 | `FUN_00bc25d0("edgedetectimgop_orig")` | `SetVar` |
| 4 | `FUN_00bb6560(0)` | `EdgeDetectionSobel(0)` — függőleges élek |
| 5 | `FUN_00bb9990` + `"{[{x:0, y:0}, {x:128, y:255}, {x:255, y:0}]}"` | **háromszög-görbe** |
| 6 | `FUN_00bc25d0("horizontal")` | `SetVar` — az első irány eltétele |
| 7 | `FUN_00bbf740("edgedetectimgop_orig")` | `GetVar` — vissza a 2. lépés képére |
| 8 | `FUN_00bb6560(1)` | `EdgeDetectionSobel` — vízszintes élek |
| 9 | `FUN_00bb9990` + ugyanaz a görbe | |
| 10 | `FUN_00bbf780("horizontal")` | `GetVar` **keverési móddal** (`BlendImageOperation` alap) |

**A háromszög-görbe a kulcs, és megfordítja az egész effekt olvasatát.**
A Sobel kimenete 128 körül van középre tolva; a görbe a 128-at **255-re**
viszi, a széleket 0-ra — vagyis az `EdgeDetectionB` **fehér alapon sötét
vonalas rajzot** ad, nem fekete alapon világos éleket. A `Neon` ezért
invertál a végén, és ezért lesz a kimenete fekete alapon világos él.

**Amit a bináris NEM ad meg** (mérésből, a fenti golden páron illesztve):
a Sobel-válasz osztója a 128-as eltolás előtt (`4,0`), és a 10. lépés
keverési módja (`multiply` és `darken` egyaránt illeszkedik — a fehér alap
mellett gyakorlatilag megkülönböztethetetlenek).

A `quality="2"` a Flash `BitmapFilterQuality` szerint az elmosás
átfutásainak száma (4.5): két menet egy 2 képpont széles dobozszűrőből
pontosan a `[1, 2, 1]/4` háromszög-mag.

#### `TintImageOperation` — FÉNYESSÉG-TARTÓ színezés (2026-08-17, #878)

A `Neon` záró lépése és a `PicnikTint` teljes csővezetéke ugyanez az egy
művelet. A #685 `picniktint__alap.jpg` golden párjából
(`PicnikTint=1,0.000000,0080cfff;`) mérve:

```
kimenet = luma(kép) + (szín − luma(szín))          Rec.601 luma
```

majd a tartományon kívülre került csatornák levágása, és a levágás
fényesség-veszteségének kompenzálása a **még szabad** csatornákon, amíg a
luminancia újra a bemenetivel egyezik. A művelet tehát a bemenet
luminanciáját bájtra megőrzi, és csak a krómát cseréli le.

Bizonyíték (a golden pár mediánjai, a szín lumája 188,9):

| bemeneti luma | mért kimenet (R, G, B) | a kimenet lumája |
|---:|---|---:|
| 16 | (0, 16, 65) | 16,8 |
| 128 | (69, 147, 195) | 129,1 |
| 248 | (231, 255, 255) | 247,9 |

A 248-as sor a döntő: két csatorna 255-ön áll, és a **harmadik** pontosan
arra az értékre, amellyel a luminancia visszajön — tehát nem egyszerű
`clip`. A modell csatornánkénti átlagos abszolút hibája a teljes golden
páron **1,7–2,4 szint** (a JPEG-zaj nagyságrendje).

> ⚠️ **A `PicnikTint` ebből még NEM lett átállítva** (ma szorzó-tinten fut,
> ΔE 33,45 / SSIM 0,63) — arra külön jegy van. Ez a kör (#878) csak a
> `Neon`-t vitte át az új primitívre.

### 4.12 A Polaroid / Múzeumi matt műveletcsaládja (2026-08-14, agent-#21)

A privát `picasapy-agent` #21 második prioritása. Célzott kör:
`referencia/dekompilalt-pakolo/script-DecompileOps21.log`.

#### `SimpleBorderImageOperation` (`0x00bbf4a0`)

```c
kimenetSzelesseg = kepSzelesseg + bal + jobb;
kimenetMagassag  = kepMagassag  + felso + also;
szin = 0xff000000 | color;          // az alfa mindig teljesen átlátszatlan
```

A kép a `(bal, felso)` pozícióba kerül. Ennyi — nincs lekerekítés, nincs
árnyék.

#### `BorderImageOperation` (`0x00bbe320` → `0x00bbe570`)

```c
t = innerthickness + outerthickness;
kimenetSzelesseg = kepSzelesseg + 2*t;
kimenetMagassag  = kepMagassag  + 2*t + extraAlso;
```

Vagyis a belső és a külső vastagság **összeadódik** és **mind a négy oldalra**
jut, plusz egy külön alsó ráadás — ez adja a paszpartu jellegzetes, alul
szélesebb arányát. A Múzeumi matt ezt kétszer használja (belső világos, külső
sötét keret), közéjük két belső ragyogással — a csővezetéket a `filterdesc.xml`
adja (`0x1a0e03` külső, `0xf0eae4` belső, 25 és 40 alapvastagság).

#### `DropShadowImageOperation` (`0x00bbb720`)

**Az árnyék eltolása** — polárkoordinátából, apró kerekítési igazítással:

```c
dx = round( (cosf(szog * π/180) + 6.7e-06f) * tavolsag + 0.001825f );
dy = round( (sinf(szog * π/180) + 6.7e-06f) * tavolsag + 0.001825f );
```

A `6,7e−06` és a `0,001825` nem paraméter, hanem **döntetlen-eldöntő eltolás**:
enélkül a 0°/90°/180°/270° körüli egész értékeknél a kerekítés platformfüggően
billenne. Át kell venni őket, ha képpontra pontos egyezést akarunk.

**A paraméterek vágása** (`0x00bcd640`):

| paraméter | tartomány |
|---|---|
| `shadowAlpha` | `clamp(0, 1)` |
| `blurX`, `blurY` | `clamp(1, 255)` |
| `strength` | `clamp(0, 255)` |
| `quality` | negatívnál 0, egyébként **15** (a maximum) |

Az alapértékek a burkolóból (`0x00bbb8d0`): `shadowAlpha = 1`, `angle = 45`,
`shadowColor` = fekete, `distance = 4`, `strength = 1`, `blurX = blurY = 4`.
A Polaroid-recept ezeket írja felül (`alpha = .4`, `distance = 3`, `blur = 8`,
`angle = 90 − forgatás`).

#### `RotateImageOperation` (`0x00bb5640` → `0x00bc8060`)

A transzformáció a szokásos hármas: eltolás a kép közepére (`−W/2`, `−H/2`),
forgatás, majd vissza. A **simítás (élsimított mintavételezés) be van
kapcsolva**, és a `padBorder` esetén a keletkező üres sarkokat a `borderColor`
tölti ki (`0x009a91a0`).

> ⛔ **MEGDŐLT (2026-08-17):** az alábbi Skia-olvasat téves. A
> `0x00bcb5e0` közvetlen hívottai a **`ytResampler` konstruktora**
> (`0x00a3f490`) és **diszpécsere** (`0x00a42c20`) — Skia-hívás nincs
> köztük. A mód **explicit**: lépték = 1 → **0-s (doboz)**, egyébként
> **3-as (Mitchell–Netravali, B = C = 0,4)**. Ld.
> `filters-decoded.md`, „A `RotateImageOperation` a `ytResampler`-t
> használja". A 46 befordított Skia-osztály önmagában nem bizonyíték.
>
> ~~**A mintavételező a Skia** — nem a Picasa saját kódja (2026-08-14). A hívási
> lánc `RotateImageOperation` slot6 → `0x00bc8060` (transzform) → `0x00bcb5e0`
> → `0x00a42c20` a rajzoló rétegbe fut, és az RTTI-tábla szerint a binárisba
> **46 Skia-osztály** van statikusan befordítva, köztük a
> **`SkBitmapProcShader`** — pontosan az, ami a bitmap-mintavételezést végzi
> (mellette `SkShaderBlitter`, `SkARGB32_Shader_Blitter`, `SkFilterShader`).
>
> **Ez jó hír:** a Skia nyílt forráskódú, tehát az algoritmust **nem kell
> visszafejteni és nem kell megmérni** — a korabeli Skia forrásából szó szerint
> kiolvasható. Ott a `SkBitmapProcState` a szűrési szinttől függően vagy
> legközelebbi-szomszéd, vagy **bilineáris 4 bites (16 lépcsős) részpixel-
> súlyokkal** — ez utóbbi mérhetően eltér a naiv, lebegőpontos bilineáristól.
>
> **Ami a mi oldalunkon maradt eldöntendő:** melyik szűrési szintet kéri a
> `Rotate` (a `0x00bc8060`-ban két eltérő festék-beállítás van). Ez egy
> jelzőbit, nem algoritmus — és golden-összevetéssel is ellenőrizhető.

#### `CropImageOperation` (`0x00bbdbd0`)

Egyszerű kivágás; a Polaroid a `min(szélesség, magasság)` méretű, **középre
igazított négyzetet** kéri (a képlet a `filterdesc.xml`-ben van).

## A színválasztó diszpécsere: `ImageFilters::PickColor` (`0x008fee80`, 2026-08-16)

Egyetlen 1 737 bájtos függvény dönti el, hogy **melyik szűrőhöz melyik
színrekesz tartozik**, és milyen címmel nyílik a színválasztó. Ez adja meg a
teljes listát arról, **mely szűrőknek van felhasználó által választható
színe** — és megválaszolja a `picasa-ini-format.md` „dekódolatlan" jelölését
a `RoundedEdges` és a `Matte` tokenre.

### A teljes leképezés (a diszasszemblált if-láncból, sorrendben)

| kiváltó név | színrekesz (beállítás-kulcs) | a párbeszéd címe | offset |
|---|---|---|---|
| `Polaroid` | `ImageFilters::BackgroundColor` | „Background Color" | `0x008feed8` |
| **`RoundedEdges`** | `ImageFilters::BackgroundColor` | „Background Color" | `0x008fef7c` → `0x008feed8` |
| `Sixties` | `ImageFilters::BackgroundColor` | „Background Color" | `0x008fefe4` → `0x008feed8` |
| **`Matte`** | `ImageFilters::MatteColor` | „Matte Color" | `0x008ff072` |
| `Vignette` | `ImageFilters::VignetteColor` | „Vignette Color" | `0x008ff104` |
| `Neon` | `ImageFilters::NeonColor` | „Neon Color" | `0x008ff193` |
| `Tint` | `ImageFilters::TintColor` | „Tint Color" | `0x008ff1f2` |
| `_cpkrOuter` | `ImageFilters::OuterColor` | „Outer Color" | `0x008ff265` |
| `_cpkrInner` | `ImageFilters::InnerColor` | „Inner Color" | `0x008ff2ef` |
| `_cpkrShadow` | `ImageFilters::ShadowColor` | „Shadow Color" | `0x008ff379` |
| `_cpkrBackground` | `ImageFilters::BackgroundColor` | „Background Color" | `0x008ff403` |
| `_cpkrBlack` | `ImageFilters::BlackColor` | **„First Color"** | `0x008ff445` köre |
| `_cpkrWhite` | `ImageFilters::WhiteColor` | **„Second Color"** | ugyanott |

Az első hét sor **szűrőnév**, az utolsó hat a `.tre` felületen elhelyezett
**általános színválasztó gomb** azonosítója (`_cpkr…` = *color picker*).

### Három tanulság

**1. Három szűrő OSZTOZIK egy színrekeszen.** A `Polaroid`, a
`RoundedEdges` és a `Sixties` mind az `ImageFilters::BackgroundColor`-t
használja — ha a felhasználó a Polaroidnál átállítja a színt, a
`RoundedEdges` is azzal a színnel nyílik legközelebb.

**2. A szín BEÁLLÍTÁSBAN él, nem a képnél.** Az `ImageFilters::*Color`
kulcsok a `Preferences`-ben tárolódnak — ez a színválasztó **legutóbb
használt** értéke, nem a fotó paramétere. A fotóhoz tartozó szín a
`filters=` láncba kerül (`%08x`, lásd `filters-decoded.md`).

**3. A `_cpkrBlack`/`_cpkrWhite` felirata „First Color" / „Second Color"** —
tehát a kétszínű szűrőknél (pl. duotone-szerű) a felület **nem** „fekete" és
„fehér" néven mutatja őket, hanem sorszámozva.

### Amit ez NEM mond meg

A **paraméter-indexet** a `filters=` láncon belül (hányadik mező a szín), és
az **alapértelmezett színt** friss telepítés után. A diszpécser csak a
rekeszt választja ki; az alapérték a beállítás-olvasóban (`0x009ae560`,
417 bájt) dől el.

*Bizonyítottsági fok: megerősített* (diszasszemblált if-lánc, minden ághoz
fájloffset).

## ⭐ HÁROM leltár, és egyik sem teljes önmagában (2026-09-03)

A Glimmer-műveletekről **három különböző** lista készíthető, és a
számuk eltér. Aki egyet használ közülük „a készletként", téves
hiánylistát kap.

| leltár | forrás | darab |
|---|---|---:|
| **HASZNÁLT** | a `filterdesc.xml` `<effect>` blokkjai | **31** |
| **REGISZTRÁLT** | `imageOperations:<Név>` sztringek a binárisban | **35** |
| **LÉTEZŐ** | `glimmer::*ImageOperation` / `*ImageMask` az RTTI-ben | **37** konkrét + 2 ősosztály |

### A különbségek — névvel

**REGISZTRÁLT (35), de a `filterdesc.xml` nem használja (4):**
`ShaderImageOperation` · `SharpenImageOperation` · `ExposureImageOperation` ·
`PaletteMapImageOperation` · `EdgeDetectionSobelImageOperation`
*(a lap 4.6-os táblája ezeket már felsorolta)*

**LÉTEZIK az RTTI-ben, de NINCS `imageOperations:` regisztrációs sztringje (3):**

| osztály | RTTI-cím |
|---|---|
| `glimmer::BlendImageOperation` | `0x00c9b0bc` |
| `glimmer::PaintMaskPlusImageMask` | `0x00cf0750` |
| `glimmer::ShapeGradientImageMask` | `0x00cf0e50` |

⇒ Ezek **nem hozhatók létre névvel** a `filterdesc.xml`-ből; a motor
belsőleg példányosítja őket (a `Blend` például a `NestedImageOperation`
`Dupe → gyerekek → Blend → Pop` fordításában).

**Az anonim névtérben (1):** `_anon_BEC5211C::ResaturateImageOperation`
(`0x00cf0578`) — ld. `picasa-native-filter-registry.md`, ahol a lap már
kimondta, hogy **nem önálló algoritmus**.

### Módszertani következmény

Egy „mi hiányzik" listát **nem szabad** egyetlen forrásra alapozni:

- csak a **regisztrációs sztringekre** ⇒ kimarad a fenti három osztály;
- csak az **RTTI-re** ⇒ bekerül két ősosztály és egy anonim névtér-beli
  osztály, ami nem felhasználói művelet;
- csak a **`filterdesc.xml`-re** ⇒ kimarad mind a négy nem használt, de
  regisztrált művelet.

*Bizonyítottsági fok: **megerősített** — mindhárom leltár lekérdezésből
származik (a `string_xrefs`, illetve az `rtti` tábla), és a három
különbséglista névvel, címmel kiírva. A „nincs `imageOperations:` sztringje"
állítás **mind a 13 bináris-indexen** ellenőrizve (a fő index + 12 kísérő
bináris), mindenütt nulla találattal.*


---

## ⭐ A 34 Glimmer-művelet VTABLE-TÉRKÉPE — cím, attribútum-offszet, közös motor (2026-09-03, #2211)

**Mit old meg:** a #2211 tíz „csak regisztrációs sorral" szereplő művelete
eddig cím nélkül állt — nem lehetett rájuk kutatást indítani. Ez a szakasz
mind a **34** `glimmer::*ImageOperation` osztályhoz megadja a **vtable-t**, a
**belépési függvényeket** és az **attribútum → tagoffszet** táblát. A
képletek ettől még nincsenek meg, de mostantól **minden művelethez van
horgony**.

### A vtable-rések JELENTÉSE

Az RTTI-táblából minden osztály vtable-je kiolvasható. A rések szerepe a
már megfejtett műveletekből horgonyozható le — a `DropShadow` (`0x00bbb720`),
a `SimpleBorder` (`0x00bbf4a0`) és a `Rotate` (`0x00bb5640`) korábban
levezetett „alkalmazó" címe **mind a 6. résben** áll.

| rés | szerep | bizonyíték |
|---|---|---|
| **1** | **attribútum-beolvasó** — a `<effect>` leíró nevesített attribútumait tagváltozókba tölti | `FUN_008eb160(leíró, név)` keres, `FUN_008eb520` tárol a `[this + offszet]` címre |
| **3, 4, 5, 7** | közös ősmetódusok (`0x00bc4ae0`, `0x00bc5160`, `0x00bc5180`, `0x00bc51d0`) | minden osztályban azonos cím |
| **6** | **alkalmazó** — vagy saját, vagy a két közös motor egyike | a három korábban megfejtett művelet alkalmazója itt áll |
| **8** | **munkavégző** — csak ott van, ahol a 6. rés közös motor | a motor `mov eax,[eax+0x20]; call eax` hívása (`0x20/4 = 8`) |

### A KÉT közös motor — és egy no-op

| motor | mit csinál | kik használják |
|---|---|---|
| **`0x00bb7c80`** (435 b) | általános **kép-bejáró**: felépíti a csomópontot, majd a 8. résen át hívja a művelet saját munkavégzőjét | `AdjustCurves` · `AutoFix` · `Exposure` · `GradientMap` · `HSVGradientMap` · `PaletteMap` · `TwoTone` |
| **`0x00bc16b0`** (428 b) | **színmátrix-alkalmazó** — szintén a 8. résen kéri el a mátrixot | `BW` · `ColorMatrix` · `MultiplyColorMatrix` · `SimpleColorMatrix` |
| **`0x00bbf920`** (6 b) | **no-op**: `or eax, 0xffffffff; ret 0xc` — nincs saját képpont-menete | `GetVar` · `Nested` · `Tint` |

⇒ A `GetVar`, a `Nested` és a `Tint` **szerkezeti** művelet: a hatásukat a
csővezeték keverő rétege adja, nem saját képpont-menet. Ez megerősíti a 4.
szakasz „a csővezeték nem lineáris" megállapítását — **a `Tint` tehát nem
képpont-szűrő**, hanem egy szín, amit a keverés visz fel.

### ⭐ A `TwoTone` UGYANAZT a munkavégzőt használja, mint a `GradientMap`

Mindkettő 8. rése **`0x00bb87b0`** (493 b). ⇒ A `TwoTone` a motorban **egy
kétmegállós színátmenet-leképezés**: a `blackColor` és a `whiteColor`
attribútum a gradiens két végpontja. Ez nem következtetés a névből — a két
osztály **bitre ugyanazt a kódot** futtatja.

*(A munkavégző első lépése egy `[ebx+4] >> 1` elemszám-számítás és egy
`< 2` ellenőrzés: kevesebb mint két megállóval nem csinál semmit — ami
pontosan egy gradienstábla szemantikája.)*

### A teljes tábla

Az attribútum-oszlop alakja `név@tagoffszet`. Az offszet a **művelet-objektum**
eleje.

| művelet (`…ImageOperation`) | vtable RVA | 1. rés (attribútumok) | 6. rés (alkalmazó) | 8. rés (munkavégző) | attribútum → tagoffszet |
|---|---|---|---|---|---|
| `AdjustCurves` | `0x008f01e0` | `0x00bb9b60` | `0x00bb7c80` (435 b) | `0x00bb9d20` (224 b) | ExposureAdjustmentStops@0x50 |
| `AutoFix` | `0x008f08bc` | `0x00bc2d60` | `0x00bb7c80` (435 b) | `0x00bc2d70` (217 b) | — |
| `BW` | `0x008f05d0` | `0x00bbdd40` | `0x00bc16b0` (428 b) | `0x00bbdd80` (392 b) | filtercolor@0x28 |
| `Blend` *(ős)* | `0x008f0b2c` | `0x00bc4900` | `0x00c07709` (42 b) | — | maskWithSourceAlpha@0x34, BlendAlpha@0xc, dynamicParamsCachePriority@0x2c, dynamicAlphaCachePriority@0x2c |
| `Blur` | `0x008efe98` | `0x00bb4d50` | `0x00bb4de0` (616 b) | — | xblur@0x24, yblur@0x2c, quality@0x34 |
| `Border` | `0x008f0650` | `0x00bbe090` | `0x00bbe320` (266 b) | — | outercolor@0x24, innercolor@0x2c, cornerradius@0x34, innerthickness@0x3c, outerthickness@0x44, captionheight@0x4c |
| `ColorMatrix` | `0x008f0798` | `0x00bc1620` | `0x00bc16b0` (428 b) | `0x00bc1860` (245 b) | — *(a `Matrix` tömb más úton)* |
| `Crop` | `0x008f05a0` | `0x00bbd9a0` | `0x00bbdbd0` (227 b) | — | width@0x34, height@0x3c |
| `DropShadow` | `0x008f039c` | `0x00bbb350` | `0x00bbb720` (417 b) | — | shadowAlpha@0x24, angle@0x2c, shadowColor@0x34, backgroundColor@0x3c, distance@0x44, inner@0x4c, quality@0x54, strength@0x5c, blurX@0x64, blurY@0x6c |
| `EdgeDetectionB` | `0x008f04a0` | `0x00bbca60` | `0x00bbcdd0` (124 b) | — | detail@0x2c |
| `EdgeDetectionSobel` | `0x008efff4` | `0x00bb6590` | `0x00bb6620` (544 b) | — | — |
| `Exposure` | `0x008f07d4` | `0x00bc1a90` | `0x00bb7c80` (435 b) | `0x00bc1ba0` (210 b) | **exposure@0x40, contrast@0x48, blacks@0x58** |
| `GetVar` | `0x008f06f0` | `0x00bbf7e0` | `0x00bbf920` (6 b) | — | — |
| `Glow` | `0x008f0174` | `0x00bb8c40` | `0x00bb8e10` (342 b) | — | color@0x24, glowalpha@0x2c, xblur@0x34, yblur@0x3c, strength@0x44, quality@0x4c, inner@0x54, knockout@0x5c |
| `GradientMap` | `0x008f0120` | `0x00bb8710` | `0x00bb7c80` (435 b) | `0x00bb87b0` (493 b) | — *(a `gradientArray` más úton)* |
| `HSVGradientMap` | `0x008f03ec` | `0x00bbc190` | `0x00bb7c80` (435 b) | `0x00bbc260` (1448 b) | hueOffset@0x44 |
| `IR` | `0x008f0a14` | `0x00bc3d80` | `0x00bc3f50` (395 b) | — | greenglow@0x2c, greenglowalpha@0x34, redweight@0x3c |
| `ImageOperation` *(ős)* | `0x008f0b0c` | `0x00c07709` | `0x00c07709` (42 b) | — | — |
| `LocalContrast` | `0x008f0a7c` | `0x00bc41e0` | `0x00bc4730` (220 b) | — | Strength@0x2c, Radius@0x34 |
| `MultiplyColorMatrix` | `0x008f0024` | `0x00bb7730` | `0x00bc16b0` (428 b) | `0x00bb77a0` (165 b) | multiplier@0x28 |
| `Nested` | `0x008f0774` | `0x00bc12d0` | `0x00bbf920` (6 b) | — | — |
| `Noise` | `0x008f06a8` | `0x00bbee70` | `0x00bbefa0` (391 b) | — | randomSeed@0x24, channelOptions@0x3c, grayscale@0x44 |
| `PaletteMap` | `0x008f00d0` | `0x00bb7900` | `0x00bb7c80` (435 b) | `0x00bb7e40` (1093 b) | — *(a `ColorMaps` tömb más úton)* |
| `Pixelate` | `0x008f04f4` | `0x00bbd050` | `0x00bbd150` (199 b) | — | pixelWidth@0x24, pixelHeight@0x2c, offsetX@0x34, offsetY@0x3c |
| `QuantizePalette` | `0x008eff58` | `0x00bb5a30` | `0x00bb5ad0` (139 b) | — | Steps@0x24, Depth@0x2c |
| `RadialBlur` | `0x008f07fc` | `0x00bc2420` | `0x00bc24e0` (169 b) | — | amount@0x34 |
| `Resize` | `0x008f0908` | `0x00bc3370` | `0x00bc3650` (407 b) | — | width@0x24, height@0x2c, smoothing@0x34 |
| `Rotate` | `0x008efefc` | `0x00bb5270` | `0x00bb5640` (239 b) | — | radAngle@0x24, degAngle@0x2c, borderColor@0x34, flipH@0x3c, flipV@0x44, padBorder@0x4c |
| `Shader` | `0x008eff2c` | `0x00bb5830` | `0x00bb58d0` (202 b) | — | — |
| `Sharpen` | `0x008f0720` | `0x00bbf990` | `0x00bbf9e0` (550 b) | — | sharpness@0x24 |
| `SimpleBorder` | `0x008f06cc` | `0x00bbf280` | `0x00bbf4a0` (391 b) | — | right@0x2c, bottom@0x3c, color@0x44 |
| `SimpleColorMatrix` | `0x008effb4` | `0x00bb62c0` | `0x00bc16b0` (428 b) | `0x00bb6400` (296 b) | saturation@0x28, contrast@0x30, brightness@0x38, ContrastAndBrightnessLinked@0x48 |
| `Tint` ⚠ | `0x008f0554` | `0x00bbd630` | `0x00bbf920` (6 b) | — | color@0x10 *(a kiolvasás itt nem megbízható)* |
| `TwoTone` | `0x008f085c` | `0x00bc2760` | `0x00bb7c80` (435 b) | `0x00bb87b0` (493 b) | whiteColor@0x24, blackColor@0x2c |

### A `BlendAlpha` NEM műveletenkénti attribútum

A `QuantizePalette` attribútum-beolvasója a saját két kulcsa után
**átadja a vezérlést** az ős beolvasójának (`0x00bb5a89 call 0x00bc4900`),
és ez a `0x00bc4900` a `Blend` 1. rése. ⇒ A `BlendAlpha`, a
`maskWithSourceAlpha` és a két gyorsítótár-prioritás **minden művelethez
elérhető**, nem csak azokhoz, amelyeknél a `red.cfg` kiírja őket. Ez
magyarázza, miért szerepel a `BlendAlpha` a legkülönbözőbb blokkokban a 4.
szakasz recept-listáiban.

### Amit a bináris TÖBBET tud, mint amit a `red.cfg` használ

A 4. szakasz attribútum-listája a `red.cfg`-ből készült — abból, amit a
szállított effektek **használnak**. A motor ennél többet ismer:

| művelet | csak a binárisban | mit jelenthet |
|---|---|---|
| `Exposure` | **`exposure`, `contrast`, `blacks`** | teljes expozíció-hármas; a `red.cfg` egyetlen effektben sem használja |
| `AdjustCurves` | **`ExposureAdjustmentStops`** | rekesz-alapú expozíció a görbék mellett |
| `Rotate` | `radAngle`, `flipH`, `flipV` | tükrözés is van, nem csak forgatás |
| `Glow` | `inner`, `knockout` | belső ragyogás és kivágás |
| `LocalContrast` | `Strength` offszete | a `red.cfg` ismeri a nevet, a tagoffszet új |

⇒ **Ez a lista NEM megvalósítási igény.** Azt mutatja meg, hol tudna a
motor többet, mint amennyit az effektek kihasználnak — a megvalósításnak a
`red.cfg` a szerződése.

### Ami NINCS mérve (őszintén)

- **Egyetlen képlet sem** ebből a szakaszból. A cél a horgony volt.
- Négy művelet **tömb-típusú attribútuma** (`ColorMatrix::Matrix`,
  `GradientMap::gradientArray`, `PaletteMap::ColorMaps`,
  `AdjustCurves::*Curve`) **más úton** kerül be — a fenti mintával nem
  olvasható ki.
- A `Tint`, a `Crop` és a `SimpleBorder` sora **hiányos**: a `red.cfg`
  több nevet sorol (`x`/`y`, illetve `top`/`left`), mint amennyit a minta
  megtalált.
- A `QuantizePalette` **KÓDBELI** alapértékei mérve vannak: `Steps` = 255,
  `Depth` = 2 (`0x00bb5aed`, `0x00bb5b1d`) — a tényleges kvantálást a
  `0x00bb5b60` (1510 b) végzi.
  ⚠️ **De a SZÁLLÍTOTT érték más** (2026-09-05): a `filterdesc.xml` a
  `Depth`-et **`4`**-re állítja, és a `Steps`-et a csúszkára köti. Ld. a
  „A szállított `Depth` = 4" szakaszt lentebb.

### Módszer

Helyi diszasszemblálás (capstone), felhős dekompiláció nélkül; a helyi
`Picasa3.exe` SHA-256-a azonos az indexeltével (`644b7bec…3ddc96`). Az
attribútum-tábla úgy készült, hogy a szkript **minden** osztály 1. résének
törzsében párba állította a betöltött névsztringet a `FUN_008eb520` tároló
hívás előtti tagcímmel — tehát nem mintaillesztés a nevekre, hanem a
tényleges tárolási hely kiolvasása.

*Bizonyítottsági fok: **megerősített** a címekre, a rés-szerepekre, a közös
motorokra és a fenti attribútum-offszetekre; **nincs mérve** minden képlet.*

---

## ⭐ HÉT Glimmer-művelet KIMÉRVE (2026-09-03, #2211)

*`IR` · `MultiplyColorMatrix` · `EdgeDetectionB` · `TwoTone` · `Resize` ·
`AutoFix` · `AdjustCurves`*

Az előző szakasz horgonyt adott mind a 34 művelethez. Ez a szakasz **hetet
számszerűen is megold** — és a megoldás módszere maga is eredmény: a
**saját attribútum-offszet táblánk** dekódolta a gyerekműveleteket.

### 1. `IRImageOperation` — szürkeárnyalatos mátrix + zöld ragyogás

**Három attribútum, mérve az alapértékekkel** (a `0x00bc3f50` alkalmazóban a
getter elé betöltött konstans az alapérték):

| attribútum | tag | alapérték | cím |
|---|---|---|---|
| `greenglow` | `+0x2c` | **5,0** | `0x00bc3f5c` → `0x00cf3a58` |
| `greenglowalpha` | `+0x34` | **0,25** | `0x00bc3f8a` → `0x00c7c608` |
| `redweight` | `+0x3c` | **−0,5** | `0x00bc3fae` → `0x00cf3ea0` |

**a) A szürkítő 4×5 mátrix** (`0x00bc402d`–`0x00bc40b9`, dupla pontosságú
elemek). A `−1,0` (`0x00cf3f58`) és a `2,0` (`0x00c7d9d0`) beolvasott
konstans:

```
| r   2,0   −1−r   0   0 |      r = redweight
| r   2,0   −1−r   0   0 |
| r   2,0   −1−r   0   0 |
| 0    0      0    1   0 |
```

⇒ **Mindhárom kimeneti csatorna ugyanazt kapja — ez szürkeárnyalatos
átalakítás**, az alfa érintetlen. Alapértékkel a súlyhármas
**(−0,5 · R + 2,0 · G − 0,5 · B)**: erős zöld-túlsúly, negatív vörös és kék
— pontosan a hamis-infravörös hatás.

⭐ **A súlyok összege MINDIG 1**: `r + 2 + (−1 − r) = 1`, bármi is a
`redweight`. A paraméter tehát a vörös↔kék egyensúlyt tolja, a
világosságot nem — ez a képlet önellenőrzése.

**b) A zöld ragyogás — két GYEREKMŰVELET.** A függvény a saját attribútumait
két beágyazott művelet tagjaiba tölti (`0x00bc3ff3`, `0x00bc400c`,
`0x00bc4021`, a `FUN_008ef2b0` beállítón át):

| forrás | cél | mi ez az előző szakasz tábláját használva |
|---|---|---|
| `greenglowalpha` | `[this+0x44]` objektum `+0xc` | **`BlendAlpha`** (a `Blend` ős tagja) |
| `greenglow` | `[this+0x48]` objektum `+0x24` | **`xblur`** (`Blur`) |
| `greenglow` | `[this+0x48]` objektum `+0x2c` | **`yblur`** (`Blur`) |

⇒ **Az `IR` = szürkítő mátrix + egy izotróp elmosás (`xblur = yblur =
greenglow`), amit `greenglowalpha` erősséggel visszakeverünk.**
Alapértékkel: 5 képpontos elmosás, 25%-os keveréssel.

> Ez a leolvasás **az előző szakasz saját táblájával** történt: a `+0x24` /
> `+0x2c` a `BlurImageOperation`, a `+0xc` a `Blend` ős regisztrált
> tagoffszete. Két független forrás mutat ugyanoda — a tábla itt
> **használatban igazolta magát**.

### 2. `MultiplyColorMatrixImageOperation` — TELJES, egy sorban

A `0x00bb77a0` (165 b) egyetlen attribútumot olvas (`multiplier`, tag
`+0x28`, alapérték **0,0**), és felépít egy **20 elemű** (`mov eax, 0x14`)
egyszeres pontosságú mátrixot:

```
| m  0  0  0  0 |      m = multiplier
| 0  m  0  0  0 |
| 0  0  m  0  0 |
| 0  0  0  1  0 |
```

⇒ **A művelet a három színcsatornát szorozza `multiplier`-rel; az alfa
változatlan, eltolás sehol nincs.** A `red.cfg` egyetlen attribútuma
(`Multiplier`) ezzel maradéktalanul megvan magyarázva.

*Levezetés: a `0x00bb77d7` `fst`-je az első elembe teszi `m`-et, a
`0x00bb7825`/`0x00bb7829` a 6. és a 13. elembe (a `fxch st(1)` után),
a `fld1` a 19. elembe 1,0-t, a maradék mind nulla.*

### 3. `EdgeDetectionBImageOperation` — a paraméter INVERTÁLVA megy tovább

A `0x00bbcdd0` (124 b) a `detail` attribútumot (tag `+0x2c`, alapérték
**0,0**) beolvassa, majd

```
0x00bbce1b  fsubr qword ptr [0x00cf3a08]     ; 0x00cf3a08 = 100,0
```

⇒ a belső paraméter **`100 − detail`**, és ezt adja tovább a
`[this+0x34]` gyerekműveletnek. Ha a `+0x34` üres, a művelet **`4`-gyel
tér vissza** (`0x00bbcde2`) — vagyis nem csinál semmit.

> ✅ **MEGVAN (2026-09-04, #2238).** A `[this+0x34]` gyerek egy
> **`SimpleColorMatrixImageOperation`** — a beolvasó (`0x00bbca60`) a
> `0x00bb6150`-nel hozza létre, és az a `0x00ceffb4` vtable-t írja bele,
> ami a `SimpleColorMatrix` (RVA `0x008effb4`).
>
> A `100 − detail` a gyerek **`+0x30`** tagjába megy (`0x00bbce24`
> `add eax, 0x30`, majd `FUN_008ef2b0` beállító) — a fenti attribútum-tábla
> szerint az a **`contrast`**.
>
> ⇒ **A `detail` csúszka a beágyazott színmátrix KONTRASZTJA, fordított
> irányban:** `contrast = 100 − detail`.
>
> **A művelet egyébként összetett:** ugyanez a beolvasó létrehoz egy
> `BlurImageOperation`-t (`0x00bb4c40` → `0x00cefe98`), egy
> `EdgeDetectionSobelImageOperation`-t (`0x00bb6560` → `0x00cefff4`) és egy
> `AdjustCurvesImageOperation`-t (`0x00bb9990` → `0x00cf01e0`) — az utóbbi
> kettőt **két külön ágon** is. Csak a színmátrix kapott saját tagoffszetet;
> a többi a gyereklistába fűződik. **A négy gyerek összekapcsolási sorrendje
> nincs mérve.**


### 4. `TwoToneImageOperation` — bizonyítottan a `GradientMap` két megállóval

Az előző szakasz megállapította, hogy a `TwoTone` és a `GradientMap`
**ugyanazt a munkavégzőt** futtatja (`0x00bb87b0`). Az attribútum-beolvasó
megmutatja, miért:

```
0x00bc289e  call 0x0097c5d0          ; 0x14 bájtos színátmenet-objektum foglalása
0x00bc28cf  call 0x008e81b0          ; felépítés a két beolvasott színből
0x00bc2923  mov  dword ptr [edi + 0x40], esi   ; -> a művelet +0x40 tagjába
0x00bc2949  call 0x00bb8710          ; ÉS ÁTADJA A VEZÉRLÉST a GradientMap beolvasójának
```

A munkavégző pedig épp ezt a tagot olvassa (`0x00bb87d1
mov esi, dword ptr [esi + 0x40]`), és **kevesebb mint két megállónál nem
csinál semmit** (`0x00bb87f4` `shr esi, 1`, `0x00bb87f6` `cmp esi, 2`).

⇒ **A `TwoTone` nem önálló algoritmus:** a `blackColor` és a `whiteColor`
egy kétmegállós színátmenetté áll össze, onnantól a `GradientMap` fut. Három
független horgony mondja ugyanezt: a közös munkavégző, a `+0x40` tag
írása/olvasása, és a `GradientMap` beolvasójának meghívása.

**Ami NINCS kiolvasva:** a két megálló pontos pozíciója (feltehetően 0 és 1,
de ez nem mérés).

### 5. `ResizeImageOperation` — UGYANAZ a mintavételező, mint a forgatásnál

Az alkalmazó (`0x00bc3650`, 407 b) tengelyenként `forrás / cél` léptéket
számol (`0x00bc3700`–`0x00bc3731`), majd a végén a **`0x00bcb5e0`**
segédfüggvénynek adja át a transzformációt és a `smoothing` kapcsolót
(harmadik argumentum, `0x00bc37d6`).

⭐ **Ez ugyanaz a `0x00bcb5e0`, amit a `RotateImageOperation` hív** a
`0x00bc8060` transzformáción keresztül. Mérve (`xrefs`): a `0x00bcb5e0`-nak
négy hívója van, köztük mindkettő.

⇒ A lap `RotateImageOperation` szakaszának 2026-08-17-i helyesbítése **a
`Resize`-ra is érvényes**: a mintavételező a **`ytResampler`**, a mód
**explicit** — *lépték = 1 → **0-s (doboz)**, egyébként **3-as
(Mitchell–Netravali, B = C = 0,4)***. **Nem bilineáris.**

**A `smoothing` attribútum:** tag `+0x34`, **alapértéke `true`**
(`0x00bc36ac` `mov byte ptr [esp+0x18], 1` a getter előtt, a
`FUN_00c29990` logikai átalakítóval).

> ✅ **Megvalósítva (#2227, 2026-09-04).** A `resize_image`
> (`src/picasapy/render/glimmer_ops.py`) mostantól a mért viselkedést
> követi: tengelyenként dönt a `forrás / cél` léptékből — **lépték = 1 →
> azonosság** (a 0-s dobozmód ilyenkor pontosan az), egyébként **valódi
> Mitchell–Netravali mag `B = C = 0,4`-gyel**, szeparábilisan. Nem
> közelítés: a `mitchell_netravali()` a klasszikus képletet számolja, és a
> próbák a mag értékeit a képletből ellenőrzik (`x = 0`, `1`, `2`), nem a
> kimenetből.

**Ami NINCS mérve — két külön nyitott kérdés:**

1. Hogy `smoothing = false` esetén a bináris a `0`-s dobozmódot
   választja-e, vagy tényleg legközelebbi szomszédot. Nálunk marad az
   `INTER_NEAREST`, és a docstring kimondja, hogy ez nem mérés.
2. **Hogy a mag KICSINYÍTÉSKOR a léptékkel nyúlik-e** (élsimítás). A
   bináris annyit árul el, hogy a mód 3-as; a `ytResampler` belső
   lépték-kezelése nincs visszafejtve. A mi implementációnk a szokásos
   nyújtott magot használja — **dokumentált döntés, nem visszafejtett
   viselkedés**. Aki ezt kiméri, itt írja át.

### 6. ⭐ `AutoFixImageOperation` — TELJES: csatornánkénti min–max szinthúzás, vágás NÉLKÜL

A `red.cfg` **hat** effektje hívja, attribútum nélkül. A munkavégző
(`0x00bc2d70`, 217 b) három lépést tesz:

1. **Három hisztogram.** Három 256 dwordös puffert nulláz
   (`0x3fc` bájt `memset` + a 256. rekesz külön), majd a `0x00bc2e50`
   (231 b) képpontonként számol: `hist_R[bájt0]`, `hist_G[bájt1]`,
   `hist_B[bájt2]` — **egyszerű darabszám, semmilyen vágás vagy súlyozás
   nincs benne**.
2. **Ha a kép nagyobb 1000 képpontnál, KICSINYÍTVE mintavételez**
   (`0x00bc2ea6` `cmp eax, 0x3e8`): a `0x00bc2f40` a `0x00cf3e10` =
   **1000,0** és a képpontszám hányadosából számol léptéket. *(A léptéket
   egy egyargumentumú CRT-függvény adja — a négyzetgyök a kézenfekvő
   olvasat, de nem azonosítottam.)*
3. **Csatornánként LUT** a `0x00bc3170` (232 b) függvénnyel, a
   `0x10` / `0x8` / `0x0` bit-eltolással (B / G / R a csomagolt képpontban).

**A LUT képlete — teljes:**

```
lo = a legkisebb index, ahol a hisztogram nem nulla
hi = a legnagyobb index, ahol a hisztogram nem nulla

ha lo == hi:                       LUT[x] = 255            (a csatorna telítve)
egyébként:  LUT[x] = clamp( trunc( (x − lo) / (hi − lo) · 255 + 0,5 ), 0, 255 )
```

> ⛔ **Helyesbítés (2026-09-04, #2229): CSONKOLÁS, nem kerekítés.** A lap
> korábban `round`-ot írt. A float→egész átalakítás a **`0x00c29990`**-en
> megy, ami **`cvttsd2si`** — trunkál; a `+ 0,5` MAGA a felfelé kerekítés
> idiómája. A különbség nem részletkérdés: `np.round`-dal (bankár-kerekítés)
> **256 rekeszből 128-ban** más értéket kapnánk. A negatív oldalt a
> `test eax,eax; jge` ág vágja 0-ra, a felsőt a `cmp eax,0xff`.

A `255,0` a `0x00cf39d0`, a `0,5` a `0x00c72150` (mindkettő dupla
pontosságú, kiolvasva); a `+0,5` a `0x00c29990` **csonkoló** egészre
alakítójával együtt adja a felfelé kerekítést. A `lo` keresése ötösével kibontott ciklus (`0x00bc3180`–
`0x00bc31a9`), a `hi`-é visszafelé megy 255-től.

> ⚠️ **ELTÉRÉS a mai kódunktól — és NEM elírás.** A mi `autofix`-ünk
> (`src/picasapy/render/glimmer_ops.py`) az `apply_channel_levels_stretch`-re
> mutat, ami a **natív „Jó napom van" modellt** használja, **0,30-as
> vágópont-keveréssel** (#535, #721 — a `0x009db610` kutatása). A Glimmer
> `AutoFixImageOperation` viszont **másik kódút**, és **vágás nélküli
> teljes min–max húzás**. A két függvény az eredetiben is különbözik; nálunk
> ugyanaz. Jegy: **#2229**.

### 7. `AdjustCurvesImageOperation` — a négy görbe tagoffszete

A munkavégző (`0x00bb9d20`, 224 b) sorrendben:

| tag | mi | hogyan |
|---|---|---|
| `+0x50` | **`ExposureAdjustmentStops`** | beolvasás (`0x008ef520`), majd `0x00bcd3b0` |
| `+0x40` | 1. görbe | `0x00bb9e00` (438 b), csak ha nem nulla |
| `+0x44` | 2. görbe | ugyanaz |
| `+0x48` | 3. görbe | ugyanaz |
| `+0x4c` | 4. görbe | ugyanaz |

A `red.cfg` négy görbe-attribútumot ismer (`MasterCurve`, `RedCurve`,
`GreenCurve`, `BlueCurve`) — és a **sorrendjük is kiolvasva** (2026-09-04,
#2238): a beolvasó (`0x00bb9b60`) mind a négyet **saját néven** keresi, és
tárolja:

| attribútum | tag | a tároló utasítás |
|---|---|---|
| `MasterCurve` | **`+0x40`** | `0x00bb9bb4` |
| `RedCurve` | **`+0x44`** | `0x00bb9be4` |
| `GreenCurve` | **`+0x48`** | `0x00bb9c14` |
| `BlueCurve` | **`+0x4c`** | `0x00bb9c44` |
| `ExposureAdjustmentStops` | `+0x50` | `0x00bb9b8b` |

*(A korábbi „a sorrend nincs mérve" megjegyzés ezzel megszűnt.)*

> ⛔ **Ez a bekezdés korábban azt írta, hogy „a sorrendjük nincs mérve, mert
> a beolvasó a tömb-attribútumokat nem a szokásos mintával veszi át".** A
> második fele igaz — más a minta —, de a névsorrend attól még kiolvasható,
> és ki is van olvasva (a fenti tábla).

⭐ Az **`ExposureAdjustmentStops`** ELŐBB fut, mint a görbék, és **nem
szerepel a `red.cfg`-ben** — a motor tehát rekesz-alapú expozíciót is tud a
görbék mellett.

#### Az `ExposureAdjustmentStops` SZEREPE — két kész görbe, előjel szerint (2026-09-04)

A `0x00bcd3b0` (253 b) az értéket **nullához hasonlítja**, és három ágra
megy. Mindkét nem-nulla ág egy **négypontos** görbét épít
(`mov eax, 4; call 0x008f2b30`) — csupa beolvasott konstansból:

| ág | a négy `(x, y)` pont | hatás |
|---|---|---|
| **sötétítő** (`0x00bcd3c7`) | (13, 0) · (116, 74) · (208, 156) · (255, 221) | minden kimenet a bemenet ALATT |
| **világosító** (`0x00bcd431`) | (0, 17) · (47, 81) · (129, 186) · (221, 255) | minden kimenet a bemenet FÖLÖTT |
| **nulla** (`0x00bcd48a`) | — | `0x008f2da0` (82 b) hívása, görbeépítés nélkül |

Utána — mindkét ágon — az **abszolút értéket** veszi és továbbadja:

```
0x00bcd491  fld  dword ptr [esp + 0x2c]   ; az eredeti érték
0x00bcd499  call 0x0049f5c0               ; fabs
0x00bcd4a1  call 0x00bcd4b0               ; (103 b) — az erősség felhasználása
```

⇒ **Az `ExposureAdjustmentStops` ELŐJELE választja a görbét (sötétít vagy
világosít), az ABSZOLÚT ÉRTÉKE pedig az erősséget adja.** A két görbe
egymáshoz közel tükrös, de **nem pontosan** az (a sötétítő 13-nál kezd, a
világosító 17-nél végződik) — külön szerzett táblák, nem egy képlet két
iránya.

**Ami NINCS mérve:** mit csinál a `0x00bcd4b0` az abszolút értékkel
(skálázás? több lépcső?), és mit tesz a nullás ág `0x008f2da0`-ja.


### Amit ez a három eset MÓDSZERTANILAG mutat

1. **Az alapérték mindig ott van a getter előtt.** A minta:
   `fld dword [konstans]` → `fstp` a kimenő rekeszbe → `call 0x008ef520`.
   Ha az attribútum hiányzik a leíróból, a konstans marad. Ez az egész
   Glimmer-készletre végigfuttatható.
2. **A gyerekművelet tagoffszete azonosítja a gyerek OSZTÁLYÁT.** Az `IR`
   ragyogása azért olvasható, mert az előző szakasz tábláját visszafelé
   használtuk: `+0x24`/`+0x2c` ⇒ `Blur`, `+0xc` ⇒ `Blend`.
3. **A belső konstans önellenőrzést adhat.** Az `IR` súlyainak összege
   levezethetően 1 — ha egy megvalósítás mást kap, elrontotta.

*Bizonyítottsági fok: **megerősített** mind a hét leletre (kiolvasott
utasítások és beolvasott konstansok); az `EdgeDetectionB` gyerekműveletének
tartalma, a `TwoTone` megálló-pozíciói, a `Resize` `smoothing = false` ága,
az `AutoFix` lekicsinyítő léptékének CRT-függvénye és az `AdjustCurves` négy
görbéjének SORRENDJE **nincsenek mérve**.*

---

## ⭐ A `QuantizePalette` OKTREE, és a MASZK-osztályok térképe (2026-09-04, #2211)

### 1. `QuantizePaletteImageOperation` — palettaválasztó, nem lépésközös kvantálás

A művelet két attribútuma és alapértéke (`0x00bb5ad0`, 139 b):

| attribútum | tag | alapérték | cím |
|---|---|---|---|
| `Steps` | `+0x24` | **255** | `0x00bb5aed` |
| `Depth` | `+0x2c` | **2** | `0x00bb5b1d` |

A munkát a `0x00bb5b60` (1510 b) végzi, négy argumentummal
(`kép`, `Steps`, `Depth`, `cél`). Három lépés olvasható ki belőle:

**a) Végigmegy a kép MINDEN képpontján**, kibontja a csomagolt képpontot
`(R, G, B)`-re (`shr 0x10` / `shr 8` / `movzx al`), és a `0x00bcb8e0`
beszúróval egy fába teszi (`0x00bb5d3b`–`0x00bb5d8c`).

**b) A beszúró OKTREE-t épít.** A csomópont **32 bájt**, és a beszúró
mind a **nyolc** mutatóját nullázza (`0x00bcb8f2` `push 0x20`,
`0x00bcb8ff`–`0x00bcb913`); a redukáló (`0x00bcb6f0`, 389 b) szintén
**nyolcasával** járja a gyerekeket (`0x00bcb71e` `lea ecx, [edx + 8]`).

**c) A redukció mérete a `Steps`-ből jön** (`0x00bb5da8`):

```
Steps == 2  ->  0x00bcb6f0(2)
egyébként   ->  0x00bcb6f0(Steps − 1)
```

**d) Tartalék: fix 3-3-2 bites paletta.** A `0x00bb5e02`–`0x00bb5e53` ciklus
három 256 elemű táblát tölt fel: `r & 0xE0`, `(g >> 3) & 0x1C`, `b >> 6` —
a klasszikus 8 bites (256 színű) RGB-palettaindex.

⇒ **A `Steps` a PALETTA MÉRETE, nem a csatornánkénti szintszám.** Az
eredmény a kép saját színeihez igazodik, nem egy fix rácshoz.

> ⚠️ **ELTÉRÉS a mai kódunktól.** Mind a két megvalósításunk
> (`effects_creative_tone.apply_quantizepalette`,
> `glimmer_tone.apply_quantizepalette`) **egyenletes lépésközű** kvantálást
> csinál, és a docstringjük ki is mondja, hogy a pontos algoritmus „NEM
> ismert", zárójelben megemlítve, hogy „esetleg palettaválasztó". **A
> zárójeles sejtés igaz volt.** Jegy: **#2231**.

#### A `Depth` az oktree MÉLYSÉG-KERETE (2026-09-04, #2238)

A `Depth` (3. argumentum) a gyűjtő objektum **`+0x10`** mezőjébe kerül
(`0x00bb5bdc`, a `[esp+0x50]`-en álló objektum `+0x10`-e). Onnan:

```
; a leszálló lépés (0x00bcb950)
0x00bcb954  mov eax, [ebx + 0xc]      ; a csomópont SZINTJE
0x00bcb962  mov ecx, 7
0x00bcb967  sub ecx, eax              ; a vizsgált BIT: 7 − szint
...                                   ; gyerekindex = R-bit<<2 | G-bit<<1 | B-bit
0x00bcb99d  mov edx, [ebx + 0x10]
0x00bcb9a6  sub edx, 1                ; a gyerek kerete EGGYEL kevesebb
0x00bcb9bc  mov [eax + 0x10], edx

; a beszúró kapuja (0x00bcb8e0)
0x00bcb8e6  cmp dword ptr [esi + 0x10], 1
0x00bcb8ea  jbe <nem megy tovább>
```

⇒ **A `Depth` azt mondja meg, hány SZINT mélyre mehet az oktree**, azaz
hány bitet vesz figyelembe csatornánként. Minden szint eggyel csökkenti a
keretet, és a leszállás megáll, amikor 1-re fogy.

A gyerekindex a klasszikus oktree-képlet, a `7 − szint`-edik bittel:

```
index = ((R >> k) & 1) << 2 | ((G >> k) & 1) << 1 | ((B >> k) & 1)      k = 7 − szint
```

**A szétvágás LUSTA:** a csomópont csak akkor bomlik gyerekekre, ha már van
benne egy szín és érkezik a második (`0x00bcb8ec` `cmp dword ptr [esi+4], 1`).

~~**Ami NINCS mérve:** mikor lép életbe a 3-3-2-es tartalék paletta, és milyen
szabály szerint választ a redukáló leveleket.~~ — **mindkettő MEGVAN**: a
3-3-2 tábla nem tartalék, hanem minden futásban felépülő gyorsító (ld. az
alábbi #2231-szakasz 5–6. pontját), a redukáló pedig `floor(N / hátralévő)`
kvótával oszt, rögzített gyerekbejárási sorrendben. Hogy az így kapott
kimenet mégsem egyezik a szállított szűrő MÉRT kimenetével, arról a lap
végi „A `QuantizePalette` OKTREE-útja NEM az, ami a képre kerül" szakasz
szól.


### 2. A MASZK-osztályok — más vtable-elrendezés, és több attribútum, mint a `red.cfg`-ben

A `glimmer::*ImageMask` osztályok **nem** ugyanazt a réskiosztást használják,
mint a műveletek: náluk az attribútum-beolvasó az **5. rés**, és a 3–4. rés
közös metódusa is más (`0x004bdeb0`, nem `0x00bc4ae0`). Ezt nem feltevésből
tudjuk: a `tileWidth` és társai sztring-xrefje **pontosan** az 5. rés
függvényére mutat.

| maszk | vtable RVA | 5. rés (attribútumok) | 6. rés | attribútum → tagoffszet |
|---|---|---|---|---|
| `ImageMask` *(ős)* | `0x008f0d34` | `0x00bcd5c0` | `0x00c07709` (no-op) | width@0x8, height@0x10 |
| `TiledImageMask` | `0x008f02e8` | `0x00bba2e0` | `0x00bba4d0` (169 b) | tileWidth@0x18, tileHeight@0x20, **scaleWidth@0x28**, **scaleHeight@0x30**, **paddingLeft@0x38**, **paddingTop@0x40**, **paddingRight@0x48**, **paddingBottom@0x50**, offsetX@0x58, offsetY@0x60, alphaMin@0x68, **alphaMax@0x70** |
| `CircularGradientImageMask` | `0x008f0890` | `0x00bcfc70` | `0x00bcfda0` (100 b) | **aspectRatio@0x18**, innerRadius@0x20, outerRadius@0x28, innerAlpha@0x30, outerAlpha@0x38, xCenter@0x40, yCenter@0x48 |
| `ShapeGradientImageMask` | `0x008f0e50` | **ugyanaz** (`0x00bcfc70`) | **ugyanaz** (`0x00bcfda0`) | ugyanaz |
| `PaintMaskPlusImageMask` | `0x008f0750` | `0x00bcd5c0` (az ősé) | `0x005baa00` (5 b) | width@0x8, height@0x10 |

**Két szerkezeti következmény:**

1. ⭐ **A `CircularGradient` és a `ShapeGradient` bitre ugyanazt a beolvasót
   és ugyanazt az alkalmazót futtatja** — a különbségük nem itt van, hanem a
   9./10. résben (a `ShapeGradient`-é `0x00c07709`, azaz **no-op**, a
   `CircularGradient`-é `0x00bc2a30`). Vagyis a `ShapeGradient` a
   `CircularGradient` egy **lecsupaszított** változata.
2. A `PaintMaskPlusImageMask` **saját attribútumot nem ismer** — csak az ős
   `width`/`height`-jét; a festett maszkot máshonnan kapja.

**Amit a `red.cfg` NEM használ, de a motor tud:** a `Tiled` maszk **öt**
extra attribútuma (`scaleWidth`, `scaleHeight`, a négy `padding*`,
`alphaMax`) és a gradiens-maszkok `aspectRatio`-ja. A 4. szakasz
attribútum-táblája a `red.cfg`-ből készült, tehát csak a **használt**
neveket sorolja.

> Ezzel a **#2211** `Tiled` tétele is horgonyt kapott — a
> `glimmer::TiledImageMask` **nem `ImageOperation`**, ezért hiányzott a
> műveleti táblából.

*Bizonyítottsági fok: **megerősített** a címekre, a rés-szerepekre és az
attribútum-offszetekre; a `QuantizePalette` `Depth`-jelentése, a
levélválasztó szabály és a maszkok viselkedése **nincs mérve**.*

---

## `HSVGradientMapImageOperation` — a megállók HSV-ben vannak (2026-09-04, #2211)

A `red.cfg` két attribútumot mutat (`gradientObjectArray`, `hueOffset`). A
munkavégző (`0x00bbc260`, 1448 b) megmutatja, **mi van a tömbben**: minden
megálló egy `color` és egy `position` mezőből áll, és a **`color` maga is
objektum, három mezővel**:

| mező | sztring címe | hol olvassa |
|---|---|---|
| `h` | `0x00cbf800` | `0x00bbc373` |
| `s` | `0x00cd6fb4` | `0x00bbc3a6` |
| `v` | `0x00cb92e8` | `0x00bbc3d9` |
| *(a burkoló)* `color` | `0x00cbda84` | `0x00bbc328` |
| `position` | `0x00cf03dc` | `0x00bbc412` |

*(A három egybetűs név nem szerepel a bináris-index sztringtáblájában —
közvetlenül a fájlból olvastam ki a `mov edi, <cím>` operandusai alapján.)*

⇒ **Ez különbözteti meg a `GradientMap`-tól:** ott a megállók RGB-színek,
itt **HSV**-ben adottak, tehát az interpoláció is HSV-térben történik. A
`hueOffset` ezért értelmes: a színezetet forgatja el.

### A HSV-modell mértékegységei — mérve

A leképezést építő `0x00bbbe20` (673 b) beolvasott konstansai:

| konstans | érték | szerep |
|---|---|---|
| `0x00cf3d50` (dupla) | **360,0** | `fadd` — a negatív színezet körbefordítása |
| `0x00cf4098` (egyszeres) | **360,0** | `fsub` — a 360 fölötti körbefordítása |
| `0x00cf39ec` / `0x00cf3a08` | **100,0** | az `s` és a `v` osztója |
| `0x00cf39f0` (dupla) | **6,0** | a szektor-szorzó (`h/360 · 6`) |
| `0x00cf39d0` (dupla) | **255,0** | a kimeneti csatorna skálája |

⇒ **`h` fokban (0–360, körbefordítással), `s` és `v` SZÁZALÉKBAN (0–100)**,
a szektorválasztás a szokásos hatodolás, a kimenet 0–255.

### Az interpoláció — LINEÁRIS, a színezetben a RÖVIDEBB ÍVEN (2026-09-04, #2238)

A megálló-keresést és a keverést a `0x00bbbcf0` (302 b) és a `0x00bbbbf0`
(254 b) végzi.

**a) A megálló-keresés.** A `0x00bbbcf0` végigmegy a pozíció-tömbön, és
megkeresi az utolsó `position ≤ x` (alsó) és az első `position ≥ x` (felső)
megállót. Ha a kettő egybeesik — vagy a keresett érték bitmintája 8-nál
közelebb van valamelyik megállóéhoz —, a megálló három mezőjét
(`h`, `s`, `v`) **változtatás nélkül** másolja ki. A megállók a tömbben
**hármasával** állnak (`lea ecx, [ecx + ecx*2]`, majd `*4` — három float).

**b) A súly.** `0x00bbbdc0`–`0x00bbbdd7`:

```
t = (position[felső] − x) / (position[felső] − position[alsó])
```

⇒ `t` az **alsó** megálló súlya (1, ha `x` az alsón áll; 0, ha a felsőn).

**c) A keverés.** A `0x00bbbbf0`-ben az `s` és a `v` **sima lineáris**
interpoláció (`a + t · (b − a)`, `0x00bbbc00`–`0x00bbbc22`).

⭐ **A színezet NEM az:**

```
0x00bbbc36  fsubp             ; Δ = h_alsó − h_felső
0x00bbbc47  call 0x0049f5c0   ; fabs
0x00bbbc4c  fcomp dword ptr [0x00cf409c]   ; 180,0
0x00bbbc5a  jp   <|Δ| ≤ 180: sima lineáris>
0x00bbbc81  fld  qword ptr [0x00cf3d50]    ; 360,0 — a KISEBBIK végpontot eltolja
```

⇒ **Ha a két színezet távolsága nagyobb 180 foknál, a motor az egyiket
±360-nal eltolja, és a RÖVIDEBB ÍVEN interpolál** — a színkörön a közelebbi
irányba megy körbe. (A `0x0049f5c0` bizonyítottan `fabs`: 26 bájt, egyetlen
`fabs` utasítással.)

**Ami NINCS mérve:** a `position` tartománya. A keresett érték egészként
érkezik, és előjel nélküli javítással (`+ 2³²`) válik lebegőpontossá
(`0x00bbbd0f`–`0x00bbbd1b`) — a pozíciók tehát egész indexhez hasonlítódnak,
de a felső határt nem olvastam ki.


---

## `ExposureImageOperation` — KÉT görbe, mindkettő számszerűen (2026-09-04, #2211)

Ezzel a **#2211** tízes listájának utolsó művelete is horgonyt kapott —
és két teljes kontrollpont-tábla jött ki belőle.

A munkavégző (`0x00bc1ba0`, 210 b) **négy** tagot olvas be
(`+0x40`, `+0x48`, `+0x50`, `+0x58`), de a beolvasó (`0x00bc1a90`) csak
**hármat** nevez meg: `exposure`, `contrast`, `blacks`. A négy értéket
átadja a `0x00bc1c80`-nak (1758 b), és ott épül a két görbe.

### 1. A FIX, nyolcpontos tábla

Egyszer, indításkor töltődik fel (`0x00d9fda0` az „már megvolt" jelző), a
`0x00d9fd60`-tól kezdődő 16 float:

| # | x | y |
|---|---|---|
| 0 | **14** | **0** |
| 1 | **27** | **19** |
| 2 | **41** | **36** |
| 3 | **81** | **70** |
| 4 | **128** | **94** |
| 5 | **193** | **123** |
| 6 | **220** | **136** |
| 7 | **255** | **160** |

A görbeépítő hívása egyértelmű: `push 0x00d9fd60; mov eax, 8;
call 0x008f2b30` — **nyolc pont**.

⇒ **Sötétítő, csúcsokat összenyomó görbe**: a 255 csak 160-ig jut, a 14 alatti
rész nullára esik.

### 2. Az ÖT pontos, PARAMÉTERES görbe

Közvetlenül utána (`0x00bc1e01`–`0x00bc1e71`, `mov eax, 5`), ahol `s` az
egyik beolvasott attribútum értéke:

| # | x | y |
|---|---|---|
| 0 | 0 | 0 |
| 1 | 6 | **42 · s + 6** |
| 2 | 36 | **112 · s + 36** |
| 3 | 126 | **72 · s + 126** |
| 4 | 255 | 255 |

Minden szorzó és eltolás kiolvasott konstans (`0x00cf4b00` = 42,
`0x00cf4af8` = 112, `0x00cf3f90` = 72; az eltolások `6`, `36`, `126`).

⇒ **`s = 0`-nál a görbe azonosság** (a pontok a felezővonalon ülnek), és a
paraméter nő

- a **sötét részt** emeli a legkevésbé (x = 6 → +42 s),
- a **mélyárnyékot/középsötétet** a legjobban (x = 36 → +112 s),
- a **középtónust** mérsékelten (x = 126 → +72 s),
- a **fehéret egyáltalán nem** (x = 255 rögzített).

Ez a **derítőfény (fill light)** jellegű görbe alakja.

> ✅ **Mindkét kérdés megválaszolva.** Az `s` a **`fill`** attribútum
> (2/b. pont). A görbék pedig **SORBAN**, nem keverve:
>
> ```
> 0x00bc218c  call 0x008f3290   ; érték = 1. görbe(érték)
> 0x00bc21a1  call 0x008f3290   ; érték = 2. görbe(érték)
> 0x00bc21b6  call 0x008f3290   ; érték = 3. görbe(érték)
> 0x00bc21bf  fldz ... fcom     ; majd alsó vágás nullára
> ```
>
> A `0x008f3290` (280 b) a **görbe kiértékelése egy pontban**: ha a görbe
> kevesebb mint két pontból áll, **változatlanul visszaadja** a bemenetet
> (`0x008f32a0`). A `0x008f2c70` (299 b) ennek a párja: **pont hozzáfűzése**
> a görbéhez (kapacitás-duplázás, `eax*8` ⇒ 8 bájt = egy `(x, y)` pár).
>
> ⇒ **A művelet a bemeneti szintet három görbén futtatja át egymás után
> (kompozíció), majd nullára vágja alul.** Egy külön ág (`0x00bc2125`–
> `0x00bc2163`) egyetlen görbét értékel ki, hozzáad egy skálázott tagot, és
> a `0x008f2e00`-t hívja — mikor lép életbe, **nincs mérve**.
>
> **Ami szintén nincs mérve:** melyik veremrekesz melyik görbe. A három
> kiértékelés a `[esp+0x74]`, `[esp+0x1c]` és `[esp+0x34]` címekre megy, de
> az építési helyükhöz képest a verem közben eltolódik, és a jelen
> olvasatból nem dönthető el egyértelműen a párosítás. **Találgatás helyett
> kimondva marad.**

### 2/b. ⛔ HELYESBÍTÉS: az `Exposure` NEGYEDIK attribútuma a `fill` — és épp az hajtja az 5 pontos görbét (2026-09-04, #2238)

Az előző bekezdés azt írta, hogy a munkavégző **négy** tagot olvas, de a
beolvasó csak **hármat** nevez meg. **A negyedik neve megvan:** `fill`
(`0x00c87128`, a `+0x50` tagba, `0x00bb…`/`0x00bc1b04`). A kiolvasó szkript
azért hagyta ki, mert ez a sztring — a `h`/`s`/`v`-hez hasonlóan — **nincs
benne a bináris-index sztringtáblájában**; közvetlenül a fájlból olvastam ki
a `mov edi, <cím>` operandusa alapján.

**Az `ExposureImageOperation` NÉGY attribútuma:**

| attribútum | tag | melyik ágat hajtja |
|---|---|---|
| `exposure` | `+0x40` | a **8 pontos FIX tábla** ága (`0x00bc1c86`) |
| `contrast` | `+0x48` | `0x00bc2036` |
| **`fill`** | `+0x50` | ⭐ **az 5 pontos, paraméteres görbe** (`0x00bc1dbc`) |
| `blacks` | `+0x58` | `0x00bc1e80` · `0x00bc1eda` · `0x00bc1f1b` |

*(A hozzárendelés a hívási sorrendből: a munkavégző `(exposure, contrast,
fill, blacks)` sorrendben adja át a négy lebegőpontos értéket
`0x00bc1c42`–`0x00bc1c64`, a görbeépítő pedig ezeket a veremrekeszeket
olvassa vissza.)*

⇒ **A 2. pont paraméteres görbéje a DERÍTŐFÉNY (fill light) görbéje** — nem
találgatás a görbe alakjából, hanem az attribútum neve. A két olvasat
egybeesik: a görbe a mélyárnyékot emeli a legjobban (x = 36 → +112 · s), a
fehéret nem mozdítja.

### 3. Egy módszertani apróság: a „közel a nullához" próba BITMINTÁN megy

Mindkét görbe elé ugyanaz a kapu kerül:

```
mov eax, dword ptr [esp + 0xc]   ; a float BITMINTÁJA egészként
sub eax, dword ptr [esp + 8]     ; a 0,0 bitmintája
cdq / xor eax, edx / sub eax, edx ; abszolút érték
cmp eax, 8
jb  <kihagyás>
```

⇒ A program a lebegőpontos értéket **egészként** hasonlítja a nullához, és
ha a bitminta-különbség **8-nál kisebb**, a görbét egyszerűen **kihagyja**.
Ez nem hiba, hanem szándékos „elhanyagolható a csúszka" gyorsítás — de aki
átveszi, ne `abs(x) < eps`-t írjon a helyére: a bitminta-távolság nem
arányos az értékkel.

*Bizonyítottsági fok: **megerősített** a két táblára, a pontszámokra és a
kapura (kiolvasott konstansok és utasítások); az attribútum-hozzárendelés és
a két görbe összekapcsolása **nincs mérve**.*

## ⭐ A `rainbow` ALT-os ága: a `0x00d67849` kapcsoló MEGVAN (#2224, 2026-09-04)

A #2148 nyitott kérdése: *mikor nem nulla a `0x00d67849` bájt, ki írja?*
A kérdést az tette nyitottá, hogy a **lineáris pásztázás hiányos** —
a #2224 maga is kimondta, hogy még azt a hivatkozást sem találta meg,
amiből a kérdés indult.

### A módszer: nyers cím-keresés, nem lineáris diszasszemblálás

A `0x00d67849` **négy bájtos, little-endian** alakjára kerestem rá a
végrehajtható szekciók teljes tartalmában, majd minden találatot a
**előtte álló opkód** szerint osztályoztam.

| | darab |
|---|---:|
| nyers előfordulás | **139** |
| ebből **olvasás** (`cmp` / `mov` / `movzx` / `test`) | **137** |
| ebből **ÍRÁS** | **2** |

*(A #2224 négy hivatkozást és nulla írást talált.)*

### A két írás

| cím | utasítás | tartalmazó függvény | a függvény sztringjei |
|---|---|---|---|
| `0x00576419` | `mov byte ptr [0x00d67849], 1` | `0x005760e0` (940 b) | `Preferences`, `mainwinismax`, `mainwinpos` |
| `0x00a52e66` | `mov byte ptr [0x00d67849], al` | `0x00a52890` | `#32768` (a Windows menü-ablakosztálya) |

A második `al`-t tárol, amit közvetlenül előtte a `mov eax, [ecx+8]` /
`test eax, eax` állít elő ⇒ **nullázni is tud**.

### A kezdőérték: 0 — mérve

A `0x00d67849` a tartalmazó szekció **inicializálatlan farkába** esik:

| | érték |
|---|---|
| szekció virtuális kezdete | `0x00d24000` |
| virtuális méret | 513 684 |
| **nyers (fájlbeli) méret** | **155 648** |
| a cím eltolása a szekcióban | **`0x43849` = 276 041** |

276 041 **> 155 648** ⇒ a bájt a fájlban nem szerepel, betöltéskor a
rendszer **nullázza**. ⇒ **A folyamat indulásának pillanatában a kapcsoló
0** — de a főablak megjelenítése (lentebb) rögtön 1-re állítja, tehát ebből
NEM következik, hogy a `rainbow` ág ne élne.

### Az írást KAPU védi

```
0x005763d9   xor ebx, ebx
0x005763db   cmp byte ptr [esp + 0xbc], bl      ; a helyi bájt 0-e?
0x005763e2   je  0x00576426                     ; ⇐ ha 0, ÁTUGORJA az írást
…
0x005763e8   call 0x004019b0                    ; a beállítás-OLVASÓ
0x005763ed   neg eax / sbb eax, eax / and eax, 2 / add eax, 1   ⇒ 1 vagy 3
0x00576419   mov byte ptr [0x00d67849], 1
```

A függvényben **ez az egyetlen** olyan elágazás, amely az írást átugorja
(a 940 bájt teljes ugrás-leltára: 73 jelölt, ebből öt lépi át az írás
címét, és három közülük a kép határain kívülre mutat, azaz téves
dekódolás).

⇒ A kapcsoló akkor és csak akkor lesz 1, ha a főablak-függvény ezen az
ágon fut le — és ugyanez az ág olvas be egy beállítást a `0x004019b0`-on
(a `Preferences` olvasója) keresztül.

### A KAPU: a `[esp + 0xbc]` a függvény MÁSODIK PARAMÉTERE (#2224, 2026-09-04)

A korábbi kör „helyi bájtnak" nevezte, és a verem-normalizálás hiányára
hivatkozva nyitva hagyta. **A verem kiszámolható**, és nem helyi változó:

| lépés | esp elmozdulása |
|---|---|
| belépéskor | `[esp]`=visszatérési cím, `[esp+4]`=1. paraméter, `[esp+8]`=2. paraméter |
| `sub esp, 0xa4` | +0xa4 |
| `push ebx` · `push ebp` · `push esi` · `push edi` | +0x10 |
| **összesen** | **+0xb4** |

⇒ `[esp+0xb4]` = visszatérési cím, **`[esp+0xb8]` = 1. paraméter**,
**`[esp+0xbc]` = 2. paraméter**. Ezt a függvény maga is megerősíti: a
`0x005761d2` `mov edx, [esp+0xb8]` után rögtön `mov byte ptr [edx+0xdd5],
al` következik — objektumtagba ír, tehát az `[esp+0xb8]` **objektummutató**,
nem helyi. A lezárás `ret 8` = **két** paraméter, stdcall.

### A függvény szerepe — kiolvasva

`0x005760e0` a **főablak helyreállítója**: a `Preferences\mainwinpos`
és `Preferences\mainwinismax` kulcsokból visszaállítja a főablak helyét és
maximalizált állapotát, ellenőrzi a képernyő-határokat
(`GetWindowPlacement` / `AdjustWindowRectEx` / `SetWindowPos`), majd — **ha
a 2. paraméter igaz** — meg is jeleníti:

```
0x005763db   cmp byte ptr [esp+0xbc], bl   ; 2. paraméter == 0 ?
0x005763e2   je  0x00576426                ; ha 0 → NEM jeleníti meg
0x005763e8   call 0x004019b0               ; „maximalizált volt?" beállítás
0x005763ed   neg/sbb/and 2/add 1           ⇒ 3 (SW_SHOWMAXIMIZED) vagy 1 (SW_SHOWNORMAL)
0x005763f9   ShowWindow(hwnd, nCmdShow)        [0xc40890]
0x00576404   SetFocus(...)                     [0xc408a4]
0x0057640b   BringWindowToTop(...)             [0xc408c8]
0x00576412   SetForegroundWindow(hwnd)         [0xc40888]
0x00576419   mov byte ptr [0x00d67849], 1      ⬅️ A KAPCSOLÓ
0x00576420   UpdateWindow(hwnd)                [0xc40848]
```

Az import-nevek a betöltési tábla rekeszeiből feloldva (a
`binaris-regeszet-modszertan.md` 21. szakaszának módszerével).

⇒ **A kapcsoló akkor lesz 1, amikor a főablak ténylegesen megjelenik és
előtérbe kerül.**

### Az öt hívó — mind kimérve

| hívás helye | 2. paraméter | kapu |
|---|---|---|
| `0x0040ce0b` | **1** | — |
| `0x0040d078` | **1** | — |
| `0x0040d428` | **1** | `cmp byte [0x00d67666], 0` |
| `0x0040da02` | **0** | `cmp byte [0x00d67666], 0` |
| `0x0040dcaa` | **1** | `cmp byte [0x00d67666], 0` |

*(A hívás-helyeket nem lineáris diszasszemblálás adta, hanem a `.text`
teljes pásztázása az `e8` relatív hívás célcíme szerint — ez a
0x005760e0-ra **öt** helyet talált, míg az index `xrefs` táblája hármat.)*

Négy hívó igazzal hív ⇒ a kapcsoló a **rendes indulás** része.

### A MÁSODIK írás: a kapcsoló jelentése ZÁRT

A `0x00a52890` ablakeljárás elején `mov edi, [ebp+8]` (üzenet-struktúra),
`mov esi, [edi+4]` = **üzenetazonosító**, `[edi+8]` = `wParam`. Az ugrótábla
(`0x00a53900` / index `0x00a53918`) a **`0x1C`** azonosítót — és **csak**
azt — a `0x00a52e0c` blokkra irányítja, ahol:

```
0x00a52e55   cmp esi, 0x1c                 ; WM_ACTIVATEAPP
0x00a52e58   jne 0x00a52edf
0x00a52e5e   mov ecx, [ebp+8]
0x00a52e61   mov eax, [ecx+8]              ; wParam = aktiválódik-e
0x00a52e64   test eax, eax
0x00a52e66   mov byte ptr [0x00d67849], al ⬅️ A KAPCSOLÓ
```

⇒ **`0x00d67849` = „a Picasa az ELŐTÉRBEN lévő alkalmazás".** A
`WM_ACTIVATEAPP` `wParam`-ja írja: aktiválódáskor 1, elvesztéskor 0. A
másik írás (a főablak megjelenítése) ugyanezt mondja ki induláskor.

> **Helyesbítés a korábbi körhöz:** a második írás címe **`0x00a52e66`**,
> nem `0x00a52e65` — a nyers cím-keresés a *operandus* kezdetét adta, az
> `a2` opkód eggyel előrébb van.

### Miért pont ez őrzi az ALT-ot — 81 olvasás ugyanabban a mintában

A 137 olvasásból **81** olyan, hogy **28 bájton belül** utána a
`GetAsyncKeyState` betöltési rekesze (`0x00c406f8`) hívódik. A minta
mindenütt azonos — például a nyitóképernyő-függvényben:

```
0x0040b4a7   cmp byte ptr [0x00d67849], bl
0x0040b4ad   je  0x0040b4c2                ; nem aktív → NE nézd a billentyűt
0x0040b4af   push 0x10                     ; VK_SHIFT
0x0040b4b1   call [0x00c406f8]             ; GetAsyncKeyState
```

Ez pontosan az, amit a `GetAsyncKeyState` megkövetel: a függvény
**rendszerszintű**, tehát egy háttérben lévő alkalmazásnak nem szabad
reagálnia rá. A `0x005d672b` (a Kiegyenesítés ALT-ága) ennek a 81-nek
**egyike**.

### A gyakorlati válasz

**A `rainbow` ALT-os útja egy átlagos telepítésen ÉL.** A kapcsoló nem
rejtett beállítás és nem parancssori kapcsoló: hétköznapi kattintáskor a
Picasa az előtérben van, tehát 1. A korábbi óvatosság („alapból nem él")
**csak az induló pillanatra** volt igaz, a megjelenített főablakra már nem.

### Nálunk MA — mérve

| | eredeti | nálunk (MÉRVE) | hol |
|---|---|---|---|
| `rainbow` mint név | natív szűrő | **ismert**, öt helyen | `render/legacy_effects.py:66`, `render/registry_data.py:159`, `render/chain.py:112`, `ini/filter_registry.py:91` és `:214` |
| `rainbow` RENDERELÉSE | natív mag | **NINCS** — a `KNOWN_UNRENDERED_OPS` halmazban ül | `render/chain.py:86`+`112` ⇒ a `can_render_filter` hamisat ad rá |
| előhívás a felületről | ALT + Kiegyenesítés | **az örökölt-fülön** (szándékos többlet, #571); ALT-ág **nincs** | a Kiegyenesítés `toolName: "tilt"` — `app/qml/PicasaPy/EditorTabCommonFixes.qml:100` |
| `AltModifier` a szerkesztőben | VK_MENU-vizsgálat | **nulla előfordulás** (csak a `CollageSheet.qml`-ben, más célra) | `grep -rn "AltModifier" src/` |

⇒ **Az ALT-ág megépítése ma nem volna őszinte:** a `rainbow`-nak nincs
renderelő modellje, tehát a gomb aktívnak látszana, de nem hatna — pont
azt csinálná, amit a `legacy_effects.py` fejléce kizár. A rejtett
módosítós ágak közös jegye a **#2146**.

> **Negatív eredmény, ami MUNKÁT SPÓROL:** a `0x00d67849`-nek megfelelő
> „előtérben vagyunk-e" őrt nálunk **nem kell megépíteni**. Az eredetiben
> azért kell, mert a `GetAsyncKeyState` rendszerszintű; Qtben a
> billentyű-módosítót az esemény hozza magával (`event.modifiers`), és
> esemény csak fókuszált ablakhoz érkezik. Aki a Shift-/ALT-ágakat
> megépíti, ezt az őrt **ne másolja át**.

*Bizonyítottsági fok: **megerősített** — a paraméter-azonosítás
verem-számolásból, az öt hívó a `.text` teljes pásztázásából, a
`WM_ACTIVATEAPP` az ugrótáblából és a `wParam`-eltolásból, a 81-es
minta megszámolva. A „nálunk" oszlop minden sora lemért `grep`.*

## ⭐ `AdjustCurves`: a négy görbe-tag SORRENDJE megvan (#2238/1, 2026-09-04)

A #2238 első kérdése: a `+0x40`…`+0x4c` tagok közül melyik a Master / Red /
Green / Blue? A választ az **attribútum-olvasó** adja: `0x00bb9b60` (255 b),
amely mind a négy nevet hivatkozza.

### A megfeleltetés — ZÁRT

| attribútum | tagoffszet | a név betöltése | olvasás | írás |
|---|---|---|---|---|
| `MasterCurve` | **`+0x40`** | `0x00bb9b90` | `0x00bb9ba2` | `0x00bb9bb4` |
| `RedCurve` | **`+0x44`** | `0x00bb9bc0` | `0x00bb9bd2` | `0x00bb9be4` |
| `GreenCurve` | **`+0x48`** | `0x00bb9bf0` | `0x00bb9c02` | `0x00bb9c14` |
| `BlueCurve` | **`+0x4c`** | `0x00bb9c20` | `0x00bb9c32` | `0x00bb9c44` |

**A megfeleltetés zárt:** mind a négy név **pontosan egyszer** szerepel,
mind a négy eltolás **pontosan egyszer**, és a kettő sorrendje azonos
(növekvő). Minden névhez ugyanaz a háromlépéses minta tartozik: név
betöltése → `mov ecx, [ebx+eltolás]` (a régi érték) → `mov [ebx+eltolás],
esi` (az új).

⇒ **A sorrend tehát a természetes: Master, Red, Green, Blue.** Aki
megvalósítja, ezt a hozzárendelést használja — nem feltevésből.

### Nálunk MA — és a lelet MEGERŐSÍTI a meglévő kódot

| | eredeti | nálunk | hol |
|---|---|---|---|
| `adjust_curves()` | négy görbe, `+0x40`…`+0x4c` | **megvan**, `master`/`red`/`green`/`blue` paraméterrel | `src/picasapy/render/glimmer_ops.py:125` |
| sorrend | `MasterCurve` az **első** beolvasott | **master előbb**, utána a csatornánkénti | ugyanott, a docstringben kimondva |

⇒ A mostani mérés **független úton megerősíti** a meglévő függvényünk
paramétersorrendjét. ⚠️ Amit **nem** mond meg: hogy a görbe-alkalmazás
*matematikája* egyezik-e — az attribútum-sorrend nem pixel-matematika.

### Melléklelet: az `AdjustCurves`-nek van `ExposureAdjustmentStops`
attribútuma is

Ugyanez az olvasó a négy görbe **előtt** beolvassa az
`ExposureAdjustmentStops` nevű attribútumot is, a `+0x50` tagba
(`0x00bb9b68` a név, `0x00bb9b88` `lea esi, [ebx + 0x50]`).

⚠️ *Amit ez NEM mond meg:* hogy a művelet mit kezd vele. Csak a beolvasás
helye mérve.

### ⛔ Amit NEM sikerült megmérni — pontos hatókörrel

**Az alkalmazó (`0x00bb9e00`, 438 b) nem hivatkozik a négy tagra** a
`mov r32, [reg+disp8]` kódolással — a teljes 438 bájton **nulla** találat
erre az alakra. ⚠️ Ebből **nem következik**, hogy nem használja: más
címzési alak (SIB, `disp32`, más bázisregiszter) vagy paraméterátadás is
lehetséges. A görbék feltehetően a hívótól érkeznek, de ez **NINCS MÉRVE**.

*Bizonyítottsági fok: a **név → tagoffszet megfeleltetés megerősített**
(bájtszinten kiolvasva, zárt); az alkalmazó hozzáférési módja **NINCS
MEG**, és a fenti negatívum csak a megnevezett kódolási alakra áll.*

## ✅ A szállított `Depth` = 4 — a leíróból kiolvasva (2026-09-05, #2454)

A lap utolsó nyitott kérdése — **mekkora `Depth`-et szállít a
`filterdesc.xml`** — megválaszolva, és **nem kellett hozzá a tulajdonos
gépe**: a kutatási másolatunkban ott a fájl.

```xml
<filter id="QuantizePalette" mode="effect" zerostate="none" fullres="1" slow="1">
  <label>Posterize</label>
  <HSliderFastDrag minimum="2"  maximum="30"  value="8"  id="_sldrSteps"/>
  <HSliderFastDrag minimum="0"  maximum="100" value="80" id="_sldrSmoothing"/>
  <HSliderPlus     minimum="0"  maximum="100" value="0"  id="_sldrFade"/>
  <NestedImageOperation BlendAlpha="{1-(_sldrFade.value/100)}">
    <BlurImageOperation xblur="{(100-_sldrSmoothing.value)/10 + 0.1}"
                        yblur="{(100-_sldrSmoothing.value)/10 + 0.1}" quality="3"/>
    <QuantizePaletteImageOperation Depth="4" Steps="{_sldrSteps.value}"/>
  </NestedImageOperation>
</filter>
```

*(Forrás: `research/copy_Picasa_3_7/Picasa3/runtime/filterdesc.xml:1244–1258`;
a `Depth` a 1255. soron.)*

| érték | honnan |
|---|---|
| **`Depth = 4`** | a szállított leíró (1255. sor) |
| a kódbeli alapérték `2` | `0x00bb5b1d` (`mov ebx, 2`) |
| Steps 2–30, alap **8** | 1249. sor |
| Smoothing 0–100, alap **80** | 1250. sor |
| Fade 0–100, alap **0** | 1251. sor |
| elmosás | `σ = (100 − Smoothing)/10 + 0,1`, `quality=3` (1254. sor) |
| keverés | `BlendAlpha = 1 − Fade/100` (1252. sor) |

**Amit ez a lap saját szabályával együtt jelent:** a csomópont csak akkor
hasad, ha a **hátralévő** `Depth` **> 1** (`0x00bcb8e6`), és a gyerek
`Depth − 1`-et örököl (`0x00bcb9a6`). Ezért `Depth = 4` mellett **három**
osztási szint fut le (4→3→2 hasad, az 1-es már nem) ⇒ legfeljebb
**8³ = 512** oktree-levél. A kódbeli alapérték (2) ezzel szemben **egyetlen**
szintet, **8** levelet adna — a szállított beállítás tehát lényegesen
finomabb palettát épít.

⚠️ **Nálunk (mérve):** a `render/glimmer_tone.py:286–305` az elmosást és a
keverést **bitre az eredeti képlettel** végzi, a kvantálást viszont
**csatornánként egyenletes lépésközzel**, `Steps` szintre. A docstring
(`:290–292`) azt állítja, hogy ez a `Depth` konstans mellett
„egyenértékű" — ~~**ez az állítás nincs mérve**, és 512 palettacella mellett
kétséges~~. **MOST MÉRVE (#2231):** a szállított szűrő kimenete
csatornánként EGYENLETES rácson ül, tehát a lineáris modell nem közelítés,
hanem a mért viselkedés; a hű oktree-újraépítés 100-szor nagyobb ΔE-t ad.
Ld. a lap végi „A `QuantizePalette` OKTREE-útja NEM az, ami a képre kerül"
szakaszt. Jegy: **#2454** (mérést kért, nem átírást).

## `QuantizePalette` `Depth` — MEGVAN, és a 3-3-2 tábla NEM tartalék (2026-09-04, #2231)

*(Ez a szakasz **felváltja** a 2026-09-04-i korábbi, „részleges mérés, NYITVA
marad" változatot. Az akkori negatív keresés — `and al, 0xE0` és társai a
`0x00bb5b60` törzsén — **helyes volt, de rossz helyen keresett**: a maszkok
ott vannak, csak `cl`/`dl` regiszterrel (`0x00bb5e04`, `0x00bb5e1c`), és a
`Depth` egyáltalán nem ebben a függvényben dől el, hanem az oktree
csomópont-beszúrójában.)*

> **Bizonyítottság: megerősített** — minden állítás mellett cím áll, minden
> konstans kiolvasva.
>
> ⚠️ **Attribúció:** a `Depth` **jelentését** (oktree-mélységkeret) a #2238
> köre már helyesen mondta ki; ez a szakasz az **ellenőrzése és a pontos
> szabálya** (a `> 1` kapu, a lefelé számolás, és hogy az alapérték 2
> **egyetlen** osztási szintet jelent). A 2–6. pont ezen felül **új**.

### 1. `Depth` = az oktree HÁTRALÉVŐ osztási mélysége, és lefelé számol

| cím | utasítás | mit jelent |
|---|---|---|
| `0x00bcb8e6` | `cmp dword ptr [esi + 0x10], 1` · `jbe` | a csomópont **csak akkor** hasad, ha a hátralévő mélység **> 1** |
| `0x00bcb9a6` | `sub edx, 1` | a gyerek `Depth − 1`-et örököl |
| `0x00bcb9bc` | `mov [eax + 0x10], edx` | …és ezt a `+0x10` résbe kapja |
| `0x00bcb9a0` | `add ecx, 1` → `[eax + 0x0c]` | a gyerek szintje `szülő + 1` |

⇒ **A `Depth` a megengedett hasítások száma.** A `0x00bb5ad0` alkalmazóban
mért **alapérték 2** (`0x00bb5b1d`, `mov ebx, 2`) ⇒ a gyökér hasad, a nyolc
gyereke (`Depth = 1`) **már nem**: egyetlen osztási szint, **8 levél**.

### 2. A csomópont — 32 bájt, mért mezőkiosztás

| eltolás | mező | bizonyíték |
|---|---|---|
| `+0x00` | mutató a **8 elemű gyerektömbre** (vagy `NULL`) | `0x00bcb8fd`, `0x00bcb986` |
| `+0x04` | a belefolyt színek **száma** | `0x00bcb942` |
| `+0x08` | bájt-jelző, létrehozáskor `1` | `0x00bcb9b8` |
| `+0x0c` | **szint** (a gyökér 0) | `0x00bcb9a3` |
| `+0x10` | **hátralévő `Depth`** | `0x00bcb9bc` |
| `+0x14` · `+0x18` · `+0x1c` | R · G · B **összeg** | `0x00bcb933` · `0x00bcb939` · `0x00bcb93f` |

Mind a csomópont, mind a gyerektömb foglalása **32 bájt**
(`0x00bcb8f2` és `0x00bcb98c`: `push 0x20`).

### 3. A gyerek-index — klasszikus bit-átlapolás (`0x00bcb962`–`0x00bcb984`)

`cl = 7 − szint`, majd:

```
eax = ((r << 2) >> cl) & 4      ; az r (7−szint). bitje a 2. helyre
esi = ((g << 1) >> cl) & 2      ; a g   ugyanaz a bitje az 1. helyre
edx = ( b        >> cl) & 1     ; a b   ugyanaz a bitje a 0. helyre
index = eax + esi + edx         ; 0…7
```

⇒ a `szint` szinten a három csatorna **(7 − szint). bitje** dönt.

### 4. Hasítás csak a MÁSODIK színnél

`0x00bcb8ec`: `cmp dword ptr [esi + 4], 1` · `jne` — a gyerektömb akkor jön
létre, amikor a számláló **pontosan 1** (tehát a második szín érkezésekor), és
a `0x00bcb919` a **már felhalmozott** összeget (`[esi+0x14]`) színként
**lenyomja** a fába. Az összegzés és a számlálás **minden szinten** történik
(`0x00bcb931`–`0x00bcb942`), tehát minden csomópont a teljes alatta lévő
halmaz összegét tartja.

### 5. ⛔ HELYESBÍTÉS — a 3-3-2 tábla NEM tartalék út

A korábbi olvasat „tartalék útnak" nevezte. **Megdőlt.** A `Steps == 2`
vizsgálat két ága (`0x00bb5db6` `jne`) **ugyanoda fut össze**:

```
0x00bb5daf  cmp eax, 2            ; eax = Steps
0x00bb5db6  jne 0x00bb5dc4
0x00bb5db9    call 0x00bcb6f0     ; redukálás(2)
0x00bb5dc2    jmp 0x00bb5dcd
0x00bb5dc4  add eax, -1
0x00bb5dc8  call 0x00bcb6f0       ; redukálás(Steps − 1)
0x00bb5dcd  <<< MINDKÉT ág ide >>>
```

⇒ a táblák **minden futásban felépülnek**, a redukálás után.

### 6. Mire valók a táblák — gyorsító, nem paletta

**a) Három 256 elemű `dword` tábla** (`0x00bb5e02`–`0x00bb5e53`), a
verem-keret `0xb8`, `0x4b8` és `0x8b8` eltolásán (fejenként 1024 bájt):

```
Rtab[i] =  (i & 0xE0)          <<16 | 0xFF000000     ; 0x00bb5e04
Gtab[i] = ((i >> 3) & 0x1C)    <<16 | 0xFF000000     ; 0x00bb5e1c
Btab[i] = ((i >> 6) & 0x03)    <<16 | 0xFF000000     ; 0x00bb5e0d
```

A három érték **ugyanabba a bájtba** kerül, tehát az `Rtab[r] | Gtab[g] |
Btab[b]` egyetlen `OR`-ral a klasszikus **3-3-2 csomagolt indexet** adja
(3 bit R, 3 bit G, 2 bit B → 0…255).

**b) A harmadik táblát egy második, 256 menetes ciklus FELÜLÍRJA**
(`0x00bb6055`–`0x00bb60e8`): minden 3-3-2 rekeszre megkérdezi az oktree-től a
**legközelebbi palettaszínt** (`0x00bcb9f0`, 475 b), és az eredményt teszi a
`0x8b8` táblába (`0x00bb60dd`).

**c) A képpontonkénti alkalmazás** ezt az objektumot kapja meg
(`0x00bb6110` → `0x00bcb2f0`, 744 b).

⇒ **A paletta-leképezés 256 rekeszre ELŐRE ki van számolva**, nem
képpontonként fut. Ennek **látható következménye**: két olyan szín, amely
ugyanabba a 3-3-2 rekeszbe esik, **mindig ugyanazt** a kimeneti színt kapja —
akkor is, ha az oktree egyébként szétválasztaná őket. A tényleges bemeneti
felbontás tehát **8 × 8 × 4 = 256 rekesz**.

**d) Ezzel a 4268 bájtos (`0x10AC`) veremkeret is megvan:** a három tábla a
`0xb8`…`0xCB8` tartományt foglalja (3 × 1024 bájt); a korábbi változat ezt
„NINCS MEG"-nek jelölte.

### 7. Amit a fentiek NEM döntenek el

⚠️ **BLOKKOLT: a `Depth` TÉNYLEGES értéke a szállított `filterdesc.xml`-ben.**
A binárisból mért **alapérték 2** (az attribútum hiányában ez lép életbe), a
mi `glimmer_tone.py:282` docstringünk viszont **`Depth=4`**-et állít. Melyik a
szállított érték, azt csak a futó Picasa `filterdesc.xml`-je mondja meg — az a
fájl **már kérve van** a **#2125**-ben. *(A különbség nem elhanyagolható:
`Depth = 2` egy osztási szint, `Depth = 4` három ⇒ redukálás előtt akár 512
levél.)*

⇒ A `Depth` **jelentése LEZÁRVA**; a szállított ~~**értéke BLOKKOLT**
(#2125)~~ **értéke is LEZÁRVA: `Depth = 4`** — a kutatási másolatunkban ott
a fájl (`filterdesc.xml:1255`), ld. a fenti „A szállított `Depth` = 4"
szakaszt (#2454). Ehhez a tulajdonos gépe nem kellett.

---

## A CSEMPE-TÁBLA és a kék jelvény — a `mode="oneclick"` szabály ÉL, csak rossz azonosítóval mértük (2026-09-08, 216. kör, #2125)

Ez a szakasz három dolgot zár le: (1) megvan a három effekt-fül **teljes,
36 tételes csempe-táblája** a binárisból, (2) megvan a kék jelvény
**megjelenítési feltétele** utasításszinten, és (3) **önhelyesbítés**: a
2026-09-06-i kör cáfolata téves volt — rossz azonosító `mode`-ját olvasta.

### 1. A csempe-tábla: `0x00c7e5a0`, 12 bájtos tételek

A csempéket a `FUN_005d7c20` építi (12 csempe fülenként, `cmp ebx, 0xc` a
`0x005d820d`-en). A tábla indexelése, utasításszinten:

```
0x005d7ce5  lea ebp, [ebp + ebp*2 - 9]   ; ebp = fül-szám (arg1)
0x005d7ce9  add ebp, ebp
0x005d7cee  add ebp, ebp                 ; ⇒ alap = 12*(fül - 3)
0x005d7d29  lea esi, [eax + eax*2]       ; eax = alap + csempe-index
0x005d7d2c  add esi, esi                 ; esi = 6*eax
0x005d7d2e  mov ecx, [esi + esi + 0xc7e5a0]   ; ELSŐDLEGES azonosító (12*eax)
0x005d7d70  mov esi, [esi + 0xc7e5a4]         ; MÁSODLAGOS azonosító (+4)
```

⇒ **tételméret 12 bájt**, `+0` = elsődleges szűrő-azonosító,
`+4` = másodlagos (örökölt) azonosító vagy `NULL`, `+8` = 0 mindenütt.
A három effekt-fül a `tabpanel3` / `editpanel/tabpanel4` / `editpanel/tabpanel5`.

| # | fül | `+0` (elsődleges) | `+4` (másodlagos) | `mode=` (a szállított `filterdesc.xml`-ből) |
|---|---|---|---|---|
| 0 | 3 | `unsharp2` | `unsharp` | effect |
| 1 | 3 | `sepia` | — | **oneclick** |
| 2 | 3 | `bw` | — | **oneclick** |
| 3 | 3 | `warm` | — | **oneclick** |
| 4 | 3 | `PicnikGrain` | `grain` | effect |
| 5 | 3 | `PicnikTint` | `tint` | effect |
| 6 | 3 | `sat` | — | effect |
| 7 | 3 | `radblur` | — | effect |
| 8 | 3 | `glow2` | `glow` | effect |
| 9 | 3 | `ansel` | — | effect |
| 10 | 3 | `radsat` | — | effect |
| 11 | 3 | `dir_tint` | `radtint` | effect |
| 12 | 4 | `IR` | — | effect |
| 13 | 4 | `Lomo` | — | effect |
| 14 | 4 | `Holga` | — | effect |
| 15 | 4 | `HDR` | — | effect |
| 16 | 4 | `Cinemascope` | — | effect |
| 17 | 4 | `Orton` | — | effect |
| 18 | 4 | `Sixties` | — | effect |
| 19 | 4 | `Invert` | — | effect |
| 20 | 4 | `HeatMap` | `NightVision` | effect |
| 21 | 4 | `CrossProcess` | — | effect |
| 22 | 4 | `QuantizePalette` | — | effect |
| 23 | 4 | `TwoTone` | — | effect |
| 24 | 5 | `Boost` | — | effect |
| 25 | 5 | `Soften` | — | effect |
| 26 | 5 | `Vignette` | `Matte` | effect |
| 27 | 5 | `Pixelate` | `PicnikFocalPixelate` | effect |
| 28 | 5 | `FocalZoom` | — | effect |
| 29 | 5 | `PencilSketch` | — | effect |
| 30 | 5 | `Neon` | — | effect |
| 31 | 5 | `Comicize` | — | effect |
| 32 | 5 | `Border` | `RoundedEdges` | effect |
| 33 | 5 | `DropShadow` | — | effect |
| 34 | 5 | `MuseumMatte` | — | effect |
| 35 | 5 | `Polaroid` | — | effect |

✅ **Pozitív kontroll — a tábla EGYEZIK a tulajdonos képernyőképeivel.**
A `research/#1869-effekt-ful-kis-kek-jel/` két felvételén a 3. és a 4. fül
mind a **24** csempéje sorrendhelyesen felel meg a tábla 0–11 és 12–23
tételének (Élesítés=`unsharp2` … Színátmenet=`dir_tint`;
Infravörös film=`IR` … Kéttónusú=`TwoTone`). A tábla 36. tételétől már más
adat áll (`us-ascii`, `iso-8859-1`, `utf-8` — karakterkészlet-tábla), tehát
a csempe-tábla **pontosan 36 tételes**.

**A másodlagos azonosító akkor lép életbe**, ha a `[ebx + 0x33a8]` jelző áll
(`0x005d7d63`); azt a `0x005d7cbe  shr eax, 0xf` + `and al, 1` állítja be,
vagyis egy beállítás **15. bitje** (a `FUN_00a67be0` visszatérési értékéből).
Ilyenkor a csempe a `+4`-es azonosítót használja, és a
`0x005d7df4 push 0x00c962e4` = `_mod%s` alakot is felépíti.

### 2. A kék jelvény: `editpanel/fx%d_adorn`, és a feltétele `mode == 1`

A jelvény réteg-neve a `0x005d80d4 push 0x00c96304` = **`editpanel/fx%d_adorn`**.
A `respack.yt` szerint (`m_fxadorner`, 10464. sor):

```
XConstraint 1, 1, -6
YConstraint 1, 1, -19
```

⇒ a bélyegkép **jobb alsó sarkához** rögzítve, (−6, −19) eltolással — pontosan
ott, ahol a képernyőképeken látszik.

A megjelenítés/elrejtés utasításszinten:

```
0x005d8108  cmp byte ptr [esp + 0x64], 0     ; a JELZŐ
0x005d810d  mov edx, dword ptr [ecx]
0x005d810f  je  0x5d8116
0x005d8111  mov eax, dword ptr [edx + 0x6c]  ; jelző = 1 → vtbl+0x6c
0x005d8114  jmp 0x5d8119
0x005d8116  mov eax, dword ptr [edx + 0x68]  ; jelző = 0 → vtbl+0x68
0x005d8119  call eax
```

A jelző előállítása ugyanabban a menetben:

```
0x005d7e7b  mov ecx, dword ptr [0xd67f68]    ; globális szolgáltatás
0x005d7e92  mov edx, [ecx] ; mov edx, [edx + 4]
0x005d7e9c  mov byte ptr [esp + 0x6c], 0     ; a jelző ALAPÉRTÉKE 0
0x005d7ea1  call edx                          ; szolgáltatás(azonosító, &kimenet)
0x005d7eab  mov ecx, dword ptr [esp + 0x20]   ; a kapott objektum
0x005d7eb9  mov edx, dword ptr [eax + 0x14]
0x005d7ebc  call edx                          ; → egész
0x005d7ec2  cmp eax, 1
0x005d7eca  sete byte ptr [esp + 0x64]        ; jelző = (érték == 1)
```

*(A veremhely azonosságát végigszámoltam: a belépő `sub esp,0x4c` + négy
`push` után a hurok-keretben `esp = E−0x5c`, így a `0x005d7eca`-nál és a
`0x005d8108`-nál a `[esp+0x64]` ugyanaz a rekesz, `E+8`.)*

**És mi az az 1?** A `mode=` attribútum kódja. A leíró-elemző
`FUN_00900490` a teljes leképezést megadja:

| `mode=` | kód | hol |
|---|---|---|
| `oneclick` | **1** | `0x00900500 lea eax, [edx + 1]` |
| `hard` | 2 | `0x009004e3` |
| `effect` | 4 | `0x009004c8 lea eax, [edx + 4]` |
| `soft` | 5 | `0x009004ab` |
| `tool` | 6 | `0x00900519` |
| `history` | 7 | `0x00900535 and eax, 7` |
| bármi más | 0 | ugyanott, a `sbb` ága |

⇒ **a kék jelvény akkor és csak akkor jelenik meg, ha a csempe szűrőjének
`mode="oneclick"`.**

### 3. ⛔ ÖNHELYESBÍTÉS: a 2026-09-06-i cáfolat ROSSZ azonosítót mért

Az a kör azt írta, hogy a szabály megdől, mert a **Filmszemcse** csempe
`mode="oneclick"`, mégsincs rajta jelvény. **A csempe azonosítója azonban nem
`grain`, hanem `PicnikGrain`** — a `grain` csak a *másodlagos* azonosító,
amit a program kizárólag a `[ebx + 0x33a8]` jelző mellett használ. A
`PicnikGrain` `mode="effect"`, tehát **helyesen** nincs rajta jelvény.

A táblabeli **elsődleges** azonosítókkal a szállított `filterdesc.xml`-ben
pontosan **három** csempe `oneclick`: `sepia`, `bw`, `warm` — és a
képernyőképen pontosan **ezen a hármon** van jelvény, a 3. fül másik kilenc
csempéjén nincs. ⇒ **a #1869 szabálya a 3. fülre hibátlanul teljesül.**

*(Ugyanez a hibaosztály fenyeget a `PicnikTint`/`tint`, `glow2`/`glow`,
`unsharp2`/`unsharp`, `dir_tint`/`radtint`, `HeatMap`/`NightVision`,
`Vignette`/`Matte`, `Pixelate`/`PicnikFocalPixelate`, `Border`/`RoundedEdges`
párokon is: a `filterdesc.xml`-t mindig a tábla ELSŐDLEGES azonosítójával
kell kikeresni.)*

### 4. Ami továbbra sem áll össze: az `Invert`

Az `Invert` a `filterdesc.xml` 986. sorában `mode="effect"`
(`<filter id="Invert" mode="effect" zerostate="none">`), a 4. fül
képernyőképén viszont **van** rajta jelvény. A `properties.xml`-ben az
`Invert` **nem szerepel** (0 találat), és a telepítésben **egyetlen**
`filterdesc.xml` van, tehát felülíró leíró-fájl nincs.

⇒ A maradék kérdés pontosan lehatárolva: **mi a `[0x00d67f68]` globális
szolgáltatás, és mit ad vissza a kapott objektum `vtbl+0x14`-e?** Ha az
tényleg a `mode`, akkor az `Invert` futásidejű módja eltér a leírótól (a
szolgáltatás felülírja); ha nem, akkor a jelvény nem a `mode`-ot nézi, és a
3. fül egyezése egy szűkebb szabály következménye. A globálisra
**31 hivatkozás** van a `.text`-ben (indextől független abszolút pásztázás),
a beállító/leszedő pár a `FUN_00401fb0` és a `FUN_00401fe0`.

**Amit ez a kör NEM dönt el, kimondva:** a jelvényben álló **„1" számjegy**
eredete. A csempeépítő `FUN_005d7c20` a `fx%d_adorn` rétegre **kizárólag**
a `vtbl+0x68`/`+0x6c` hívást teszi — szöveget vagy számot **nem** ír bele.
Ebben a függvényben tehát a számjegy nem áll elő; hogy a réteg képi
tartalma statikus-e, ez a mérés nem mondja meg. *(A képernyőképek
képpont-összevetése erre nem alkalmas: a jelvény átlátszósággal keveredik a
bélyegképre, így a képpontjai háttérfüggőek.)*

### 5. 🔓 A `filterdesc.xml` NEM BLOKKOLT többé

A #2125 törzse (és a `filterdesc-registry.md` fejléce) a tulajdonos
telepítésének `filterdesc.xml`-jét kérte. **Megvan:** a 2026-09-05-i
telepítés-mentésben
(`Picasa-telepites-mappa-mentes-20260905/Picasa3/runtime/filterdesc.xml`,
63 005 bájt), és **bájtra azonos** a kutatási fánkban már meglévő
példánnyal — mindkettő `md5 = 2cdd163f7ab2cec09d0f6990f2a179bc`.

⇒ Ez a **kérés lezárható**: a szállított leíró már eddig is a kezünkben volt.
A fenti `mode=` oszlop és a #2231/#2454 `Depth` értéke is ebből olvasható ki.

### 6. Melléklelet: a jobbról-balra író nyelvek ága

A csempe-felirat rétegén (`editpanel/fxlabel%d`) a `0x005d804e`–`0x005d80b6`
a területi beállítás első három bájtját hasonlítja a `0x00c7f2c0` = `"fa"`
és a `0x00c96300` = `"ar"` konstansokhoz (perzsa, arab), és egyezéskor
`push 0x190` a `vtbl+0xc`-re, majd `push 0xa` a `vtbl+8`-ra. Ez a felirat
RTL-igazítása; a többi nyelven nem fut le.

*Bizonyítottsági fok: **megerősített** az 1. és a 2. pont (a tábla a
képernyőképekkel, a mód-tábla a leíró-elemzőből, a veremhely számolással);
**megerősített** az 5. pont (md5-egyezés); a 4. pont **nyitott**, pontos
következő lépéssel.*

---

## A jelvény LÁNCA végig kimérve — `[0x00d67f68]` = a `filterdesc.xml` regisztere (2026-09-08, 217. kör, #2125)

A 216. kör eljutott odáig, hogy a jelvény akkor látszik, ha egy szolgáltatástól
kapott objektum `vtbl+0x14`-e **1**-et ad. Ez a kör a lánc **mindkét
maradék szemét** kimérte: mi az a szolgáltatás, és mi az a `vtbl+0x14`.

### 1. `[0x00d67f68]` = a szűrő-regiszter, a `runtime\filterdesc.xml`-ből

A globálist egyetlen hely tölti fel — `FUN_004051b0` (indextől független
`E8`-pásztázás: a beállító `FUN_00401fb0`-nak **1**, a leszedő
`FUN_00401fe0`-nak **1** hívási helye van, mindkettő itt):

```
0x00405615  mov eax, 0x00c7f150        ; "runtime\filterdesc.xml"
0x0040563c  mov eax, 0x00c7f168        ; "runtime\picnik_effects\"
0x0040566c  push 0x146c
0x00405671  call 0x0097c5d0            ; operator new(0x146c)
0x0040568c  call 0x004021a0            ; ctor(útvonalak) — vtable 0x00c7f724
0x00405697  call 0x00401fb0            ; ⇒ [0x00d67f68] = a regiszter
```

⇒ a szolgáltatás **a `filterdesc.xml` beolvasott regisztere**.
*(A második útvonal, a `runtime\picnik_effects\` mappa, **nincs meg** sem a
kutatási fánk telepítésében, sem a tulajdonos 2026-09-05-i
telepítés-mentésében — tehát ebben a telepítésben nincs második forrás.)*

A regiszter `vtbl+4`-e a kereső (`FUN_0050e460`): egy különleges azonosítót
(`0x00c86f24` = **`desat`**) saját osztállyal szolgál ki, minden mást a
`FUN_008f9fe0`-nek ad tovább. Az XML-ből regisztrált leírót a `vtbl+8`
(`FUN_008fa400`) keresi ki a `[regiszter+0x1454]` térképből az azonosító
sztringgel; találat esetén `operator new(0xcc)` + `FUN_008f6ad0` — ez a
**`CGenericFilter`** konstruktora (ugyanaz, amit a `filters-decoded.md`
használ), és a **leíró mutatója a `this+8`-ba** kerül
(`0x008f6ad0 mov [esi + 8], ecx`).

### 2. `vtbl+0x14` = `GetMode()` — hét utasítás

A `CGenericFilter` vtáblája `0x00cd184c`, és az `+0x14`-es rés a
`FUN_008f6cc0`, teljes egészében:

```
0x008f6cc0  mov eax, dword ptr [ecx + 8]   ; this->leíró
0x008f6cc3  mov eax, dword ptr [eax + 4]   ; leíró->[+4]
0x008f6cc6  ret
```

A leíró `+4`-e pedig pontosan az a mező, amit az XML-elemző ír a
`mode=` attribútumból:

```
0x008ff80a  push 0xec ; call 0x0097c5d0     ; a leíró: operator new(0xec)
0x008ff81f  call 0x008f6910                 ; ctor — [+4] = 0, [+8] = 1, vtable 0x00cd18fc
0x008ff847  mov dword ptr [eax + 4], ecx    ; [+4] = a mode KÓDJA
```

⇒ **`vtbl+0x14` = a szűrő `mode=` kódja**, és a `FUN_00900490` táblája
szerint az **1 = `oneclick`**.

### 3. A teljes lánc, egy sorban

```
csempe-tábla (0x00c7e5a0) → azonosító
  → regiszter [0x00d67f68] (filterdesc.xml) → CGenericFilter
    → GetMode() = leíró[+4] = a mode kódja
      → == 1 (oneclick) ? editpanel/fx%d_adorn MEGJELENIK : elrejtve
```

✅ **A jelvényt egyetlen hely vezérli.** Az `editpanel/fx%d_adorn`
sztring (`0x00c96304`) abszolút hivatkozása a `.text`-ben **1**, a
`FUN_005d7c20`-ban; a bájtsorozat a teljes fájlban **egyszer** fordul elő.
Kontroll: a `_tab%d` (`0x00c962dc`) és az `editpanel/fx%d` (`0x00c9631c`)
ugyanígy 1-1 hivatkozás, ugyanabban a függvényben — a pásztázás tehát működik.
Nincs második író, nincs második megjelenítő.

### 4. A `mode=` megoszlása a szállított leíróban

A `mode=` attribútum **kizárólag** `<filter>` elemeken áll (beágyazott
elemen egy sincs), és a 84 szűrő megoszlása:

| `mode=` | darab |
|---|---|
| `effect` | 56 |
| `oneclick` | 12 |
| `soft` | 7 |
| `history` | 7 |
| `tool` | 2 |

A 36 csempe **elsődleges** azonosítói közül pontosan három esik az
`oneclick`-be: `sepia`, `bw`, `warm`.

### 5. ⚠️ Az `Invert` ellentmondása — a GÉPI oldal ezzel KIMERÜLT

Az `Invert` a leíró 986. sorában `mode="effect"`
(`<filter id="Invert" mode="effect" zerostate="none">`), a benne álló
`<effect>` blokk egyetlen művelete egy `AdjustCurvesImageOperation`; sem
ott, sem máshol nincs második `mode=`. A tulajdonos 2026-09-02-i
felvételén viszont **van** rajta a kék „1".

Amit a bináris és a szállított fájl együtt kizárnak:

| lehetőség | mi zárta ki |
|---|---|
| más `mode` a leíróban | `mode="effect"`, és a `mode=` csak `<filter>`-en áll |
| felülíró leíró-fájl | egyetlen `filterdesc.xml`; a `properties.xml`-ben `Invert`-re 0 találat |
| a `picnik_effects` mappa második forrása | a mappa **nem létezik** a telepítésben |
| a másodlagos azonosító lép életbe | az `Invert` `+4`-e NULL; és ha a `[ebx+0x33a8]` jelző állna, a Filmszemcse a `grain`-t (`oneclick`) használná, tehát **azon is** lenne jelvény — nincs |
| a jelvényt más kód is megjeleníti | a réteg-név hivatkozása a teljes fájlban **1** |
| a beépített (nem XML-es) tábla útja | ott a `this+8` a **regiszter**, amelynek a `+4`-e egy sztring-objektum (`0x00401ac1 lea eax,[esi+4]` + sztring-ktor), nem 1 |

⇒ **A gépi bizonyítéklánc ezen a kérdésen kimerült.** A mechanizmus zárt és
megerősített; a megfigyelés viszont ellentmond neki, és ezt már csak **friss,
élő megfigyelés** döntheti el a tulajdonos gépén — nem a bináris.

*Bizonyítottsági fok: **megerősített** az 1–4. pont (utasításszintű lánc,
egyszeres hivatkozás működő kontrollal, a leíróból számolt megoszlás);
az 5. pont **nyitott**, és a gépi úton nem eldönthető része nevesítve.*

---

## ⛔ A `QuantizePalette` OKTREE-útja NEM az, ami a képre kerül (2026-09-08, #2231)

Ez a szakasz **nem cáfolja** a fenti két oktree-szakaszt — a binárisbeli
olvasat megerősítve marad, sőt bővül —, hanem **szembeállítja egy
viselkedés-méréssel**, amely az ellenkezőjét mondja. Mindkettő mérés; a
kettő nem áll össze, és ezt kimondani helyesebb, mint választani.

### 1. A MÉRÉS: a szállított szűrő kimenete csatornánként egyenletes rács

Bemenet a NAS-mérőszett három `quantizepalette__*` képe, referencia a
Picasa saját exportja (`PicasaPy meroszett/export-202608202231/`).
ΔE = CIE Lab, átlagos képpont-távolság.

| eset | Steps | Smoothing | Fade | ΔE mi (rácsos) | ΔE hű oktree | ΔE forrás |
|---|---|---|---|---|---|---|
| alap | 8 | 80 | 0 | **0,268** | 28,552 | 19,009 |
| min | 2 | 0 | 0 | **0,687** | 93,301 | 73,485 |
| max | 30 | 100 | 100 | 0,136 | 0,136 | 0,136 |

*(A `max` `Fade = 100` miatt kontroll, nem bizonyíték. Az oktree-oszlop a
lenti 2. pont szerinti hű újraépítés, `Depth = 4` és `Depth = 2` mellett
egyaránt ugyanezt adta.)*

**Kontroll — a metrika diszkriminál.** Ugyanaz a rácsos modell más
`Steps`-szel az `alap` képre: `Steps=6` → 17,26 · `7` → 16,66 ·
**`8` → 0,268** · `9` → 11,74 · `10` → 11,02. A 0,268 tehát nem
véletlen egybeesés.

**Kontroll — a kimenet tényleg a rácson ül.** A Picasa kimeneti
csatornaértékeinek **97,62%-a** (`alap`, `Steps=8`) illetve **98,36%-a**
(`min`, `Steps=2`) ±2-n belül van a `round(i·255/(Steps−1))` rács egy
pontjától. A rács `Steps = 8`-ra: `0, 36, 73, 109, 146, 182, 219, 255`.

**A döntő lelet — a csatornák FÜGGETLENEK.** A mérőkép mezőinek
közepén (a `Steps = 8` exportban) minden csatorna külön ugrik a hozzá
legközelebbi rácspontra:

```
forrás           Picasa kimenete
(200, 40,  40) → (182, 36,  36)
( 40, 179, 60) → ( 36, 182, 73)
( 41, 60, 199) → ( 36,  72, 182)      ← ez a szín NINCS a forrásképben
(235,235, 235) → (219, 219, 219)
szürke sáv:  10→0 · 31→36 · 53→36 · 74→73 · 95→109 · 116→109 ·
             138→146 · 159→146 · 180→182 · 202→219 · 223→219 · 244→255
```

⇒ **Palettaválasztás ezt nem tudja előállítani.** Egy oktree-paletta a
kép SAJÁT színeinek átlagaiból áll; a `(36, 73, 182)` egyik forrásszín
átlagaként sem jön ki. A leképezés ráadásul **képfüggetlen**: ugyanaz a
bemeneti szín ugyanazt a kimenetet adja más színeloszlású képben is.

Őr: `tests/render/test_quantizepalette_racs_2231.py` (28 állítás; a hű
oktree-modellel 27 bukik).

### 2. A binárisbeli olvasat — megerősítve és BŐVÍTVE

A fenti #2211/#2238/#2231 szakaszok minden állítását ellenőriztem
utasításszinten. Az attribútum-nevek is kiolvasva: a `0x00bb5a30`
beolvasó a **`Steps`** nevet a `0x00ceff4c`, a **`Depth`**-et a
`0x00c85524` sztringből veszi, és a `+0x24` illetve `+0x2c` tagba írja —
tehát a névhozzárendelés zárt. Ami ehhez képest ÚJ:

| lelet | cím | mit mond |
|---|---|---|
| a paletta **50×50-es mintából** épül | `0x00bb5c44` `mov eax, 0x32`, majd `0x00bb5ce5` hívás 256-tal | nem a teljes képet gyűjti be, hanem egy legfeljebb 50×50-es, 256 színű kicsinyítést |
| a redukáló **gyerekbejárási sorrendje** rögzített tábla | `0x00cf0c28` = `[3, 1, 2, 5, 4, 6, 0, 7]` | nem 0…7 sorrendben oszt |
| a kvótaosztás **`floor`** | `0x00c0b1e0` (a `0…1` ág `fldz`-t ad ⇒ floor, nem ceil) | `kvóta = floor(N / hátralévő_gyerekszám)`; `kvóta == 0` ⇒ a gyerek a szülőbe olvad, `N` nem csökken |
| a `Steps == 2` ág **kikapcsolja a gyökér `+0x8` jelzőjét** | `0x00bb5dbe` `mov byte [esp+0x58], bl` | ettől a keresés hiányzó gyerek esetén **helyettesítő testvért** keres a `0x00cf0c48` táblából (8 sor × 7) |
| a keresés **nem valódi legközelebbi-szomszéd** | `0x00bcb9f0` | bit-alapú leszállás; ha nincs gyerek és a `+0x8` jelző áll, ott megáll, és a csomópont ÁTLAGÁT adja (`floor(összeg/darab)`) |
| a 3-3-2 tábla **két menetben** működik | `0x00bb5fe9` és `0x00bb6110` (mindkettő `0x00bcb2f0`), közte `0x00bb601c`/`0x00bb6032` `memset(…, 0, 0x400)` | 1. menet: `Rtab[r] \| Gtab[g] \| Btab[b]` ⇒ a 3-3-2 index az `R` bájtba; a másik két tábla kinullázása után a 2. menet ugyanezzel az OR-ral már `LUT[index]`-et ad |
| a LUT-építő **visszafejti** a rekesz színét | `0x00bb6055`–`0x00bb6072` | `r = c & 0xE0`, `g = (c & 0x1C) << 3`, `b = (c & 3) << 6`, és ERRE kérdezi a fát |

Ezzel a fenti „a 3-3-2 tábla gyorsító, nem tartalék" olvasat is
**megerősítve**: a kétmenetes szerkezet és a köztes nullázás csak így áll
össze.

### 3. Amit ez a `Kész, ha` lista két nyitott pontjáról jelent

- **`Depth` (alapérték 2)** — LEZÁRVA (a #2238/#2231 szakaszok, itt
  újraellenőrizve): az oktree megengedett hasítási mélysége, lefelé
  számol, a csomópont csak `> 1` esetén hasad. A szállított érték
  `Depth = 4` (`filterdesc.xml:1255`), tehát három osztási szint —
  a fenti #2454-es szakasz ezt már feloldotta, a #2231 szakasz
  „BLOKKOLT (#2125)" megjegyzése tehát **elavult**.
- **A 3-3-2 paletta szerepe** — LEZÁRVA: nem tartalék út, hanem a
  képpontonkénti leképezés **előre kiszámolt gyorsítója**, ami minden
  futásban felépül. Következménye, hogy az oktree-út tényleges bemeneti
  felbontása 8 × 8 × 4 = 256 rekesz.

### 4. ⚠️ A NYITOTT kérdés

**Miért nem az oktree-út eredménye kerül a képre?** Egyetlen
`QuantizePaletteImageOperation` osztály van (RTTI, vtábla `0x008eff58`,
az alkalmazó a 7. rés = `0x00bb5ad0`), és a `filterdesc.xml` egyetlen
`QuantizePalette` szűrője pontosan ezt köti be. A `runtime/` alatt
nincs másik leíró (`grep -ri quantizepalette` ⇒ 2 találat, mindkettő a
`filterdesc.xml`-ben), és a `glimmer::*ImageOperation` RTTI-listában
nincs második kvantáló osztály.

Amit ez a kör NEM tudott eldönteni, és amivel folytatható:

1. van-e a `.picasa.ini` `filters=` sztringhez tartozó, a leírót
   MEGKERÜLŐ teljes felbontású renderút (a szűrő `fullres="1" slow="1"`);
2. az alkalmazó `return 4` korai ága (`0x00bb5ee6`: `[cél+0x10] == 0`)
   mikor lép életbe, és mi fut helyette;
3. a `0x00bcb2f0` (744 b) képponti alkalmazó teljes dekódolása — a
   táblahasználatot a fenti kétmenetes olvasat magyarázza, de a függvény
   maga nincs végigolvasva.

### 5. A 221. kör: KÉT irány kizárva, a korai ág pontosítva (2026-09-08, #2746)

A fenti három folytatási irány közül kettő lezárult — mindkettő **negatív**
eredménnyel, ami itt önmagában lelet: a következő kör ne járja újra.

#### 5.1 ⛔ KIZÁRVA: a rács NEM a képponti alkalmazóban keletkezik

A `0x00bcb2f0` (744 bájt) teljes törzsét végigpásztázva **egyetlen osztás
és egyetlen lebegőpontos utasítás sincs benne**. A négy szorzás mind
címszámítás:

| cím | utasítás | mit csinál |
|---|---|---|
| `0x00bcb368` | `imul edx, [ebx + 0x14]` | sor-eltolás (stride) |
| `0x00bcb37a` | `imul edx, eax` | sor-eltolás |
| `0x00bcb50b` | `imul eax, [ebx + 0x14]` | sor-eltolás |
| `0x00bcb528` | `imul ecx, [ebp + 0x1c]` | sor-eltolás |

A mért kimenet `round(i·255/(Steps−1))` alakú, ami **osztást kíván**
`Steps−1`-gyel. Ilyen művelet itt nincs ⇒ a rács nem itt áll elő. A
függvény tényleg csak a LUT-ot alkalmazza, ahogy a kétmenetes olvasat
mondta.

*(Módszer: `pe_dis.cdis(0x00bcb2f0, 744)`, majd szűrés a
`div|idiv|mul|imul|fdiv|fmul|fld|fstp|cvt` mintára. A negatívum HATÓKÖRE: ez
az egy függvény, a hívottjai nem.)*

#### 5.2 ⛔ KIZÁRVA: a binárisban NINCS név szerinti megkerülő út

A #2231 köre a `runtime/` alatt grepelt (2 találat, mindkettő a
`filterdesc.xml`-ben). **A binárisbeli sztring-hivatkozásokat viszont nem
nézte meg.** Most igen, az indexből:

```sql
SELECT string, function_address FROM string_xrefs WHERE string LIKE '%uantize%';
```

⇒ **pontosan egy találat**: `imageOperations:QuantizePaletteImageOperation`,
hivatkozó `0x00bb31f0` (a művelet-gyár regisztrálója). A `Posterize`
(a felhasználói felirat) sztringre **nulla** hivatkozás.

⇒ A `.picasa.ini` `filters=QuantizePalette=…` sora **nem tud** egy
alternatív, névre kereső natív feldolgozóhoz jutni: ilyen nincs. A
megkerülő út — ha van — nem a szűrő NEVÉN keresztül megy.

#### 5.3 A korai kilépő ág — pontosítva, és a kódkészlet kimérve

A feltétel a lap eddigi „`[cél+0x10] == 0`" alakjánál pontosabban:

```
0x00bb5ba4  xor ebx, ebx                 ; ebx = 0 — IGAZOLVA
…
0x00bb5ec3  mov edi, [esp + 0x10cc]      ; a munkavégző 4. paramétere
0x00bb5edd  mov eax, [edi + 0x10]
0x00bb5ee0  cmp eax, ebx                 ; == 0 ?
0x00bb5ee6  jne 0x00bb5f1a               ; nem 0 → a FŐ ÚT
0x00bb5f02  mov eax, 4                   ; 0 → korai kilépés
```

A veremeltolás kiszámolva: a `0x10ac` bájtos foglalás után négy `push`
(`ebx, ebp, esi, edi`) ⇒ `[esp+0x10c0]` = 1., `[esp+0x10c4]` = 2.,
`[esp+0x10c8]` = 3., **`[esp+0x10cc]` = 4. paraméter**. A hívó
(`0x00bb5ad0`) push-sorrendjéből a 4. paraméter az **alkalmazó 3.
paramétere** (`[ebp+0x10]`), a 2. és 3. pedig a `Steps` és a `Depth`.

**A visszatérési kódkészlet — mind a négy kilépési pont kimérve:**

| cím | érték | |
|---|---|---|
| `0x00bb6143` | `xor eax, eax` ⇒ **0** | a fő út vége — siker |
| `0x00bb6019` | `or eax, 0xffffffff` ⇒ **−1** | hiba |
| `0x00bb5f11` | **4** | a korai ág |
| `0x00bb5d22` | `mov eax, edi` | egy továbbadott kód |

⭐ **Ebből következik, hogy a `4` NEM hibakód** — a hibának saját értéke van
(−1). A `4` külön állapot, amit a hívó valamiként értelmez.

#### 5.4 Egy mellékes, de fontos részlet: a `Steps` kódbeli alapértéke 255

```
0x00bb5aed  mov dword ptr [esp + 0x3c], 0xff   ; Steps := 255
0x00bb5af5  call 0x008ef520                    ; a {_sldrSteps.value} kiértékelése
0x00bb5afc  jne 0x00bb5b14                     ; ha NEM 0-t adott → a 255 MARAD
```

Tehát ha a kifejezés-kiértékelés nem jár sikerrel, a művelet **255 lépéssel**
fut — ami a 256 színű mintán gyakorlatilag azonosság. Ez NEM magyarázza a
mért rácsot (az `Steps = 8`-ra illeszkedik), de a következő körnek tudnia
kell róla: a `Steps` útja a kifejezés-kiértékelőn át megy, nem konstansként.

#### 5.5 Ami ezek után NYITVA marad — egyetlen irány

**Mit csinál a hívó a `4`-es visszatérési értékkel?** A művelet vtáblája
`0x008eff58`, az alkalmazó a 7. rés; a hívás tehát `call [reg + 0x18]`
alakú, közvetlen xref nincs rá. A következő kör ezt keresse — és azt, hogy
`[3. paraméter + 0x10]` mikor 0.

*(Amit ez a kör NEM próbált: a `0x00bb5d22` ág `edi`-jének eredete, és a
hívó oldali `cmp eax, 4` minta pásztázása. Egyik sem drága.)*

### 6. ⛔ ÖNHELYESBÍTÉS: a `4`-es kódot SENKI nem vizsgálja (2026-09-08, 222. kör, #2746)

Az 5.3 szakasz azzal zárult, hogy a `4` „külön állapot, amit a hívó
valamiként értelmez", és hogy „épp ez teszi érdemessé a folytatást".
**Ez az állítás megdőlt — a sajátom, egy körrel később.**

#### 6.1 Módszertani lelet ELŐBB: a slot-hívás alakja

A vtábla-slot hívása **két alakban** áll a binárisban, és a gyakoribb nem az,
amire az 5. szakasz mintája épült:

| alak | előfordulás a `.text`-ben |
|---|---|
| `call dword ptr [reg + 0x18]` (közvetlen) | **9** |
| `mov reg, [reg + 0x18]` … `call reg` (közvetett) | **2 806** |

⇒ Aki csak a közvetlen alakra keres, a hívóhelyek **99,7 %-át nem látja**, és
hamis negatívot kap. (A teljes binárisban 208 143 `call` van, ebből
mindössze 115 bármilyen `call dword ptr [reg(+N)]` alakú — ez maga volt a
jel, hogy a minta rossz.)

#### 6.2 A mérés — és három hamis pozitív, elolvasva

A **közvetett** alakra pásztázva 2 806 slot-6 hívás van. Ezek közül 10
utasításon belül `cmp/sub eax, 4` **három** helyen áll — és mindhárom
**hamis pozitív**, mert az `eax` a hívás után felülíródik:

| hívás | a `cmp eax, 4` | miért nem a visszatérési érték |
|---|---|---|
| `0x00918f05` | `0x00918f15` | `0x00918f11 mov eax, [esp+0x1c]` — verem-változó; a `cmp` egy **switch-tábla** határa (`0x00918f1e jmp [eax*4 + 0x9190e4]`) |
| `0x0061122f` | `0x0061124e` | `0x00611243 mov eax, [ebp+0x134]` — **tagváltozó** állapota (a `cmp eax, 3` a párja) |
| `0x0066854e` | `0x00668567` | `0x00668564 mov eax, [esi+0x70]` — **tagváltozó** állapota |

**Kontrollok, hogy a negatívum ne a minta hibája legyen:**

1. a `4`-es minta érzékel: ugyanaz a futás **4 890** `mov reg, 4`-et talált,
   és **benne a `0x00bb5f02`-t** — épp azt, amit keresünk;
2. a hívás-minta érzékel: 2 806 találat (ld. 6.1);
3. mindhárom találatot **elolvastam**, nem a számot jelentem.

⇒ **A `4`-es visszatérési értéket egyetlen hívó sem vizsgálja.** A `4` tehát
nem „csináld te" jelzés: aki a slot 6-ot hívja, eldobja az eredményt.

#### 6.3 Amit ez a kérdésről mond

Ha a korai ág (`[3. paraméter + 0x10] == 0`) lefutna, a művelet egyszerűen
**nem módosítaná a képet** — a `NestedImageOperation` láncában a `Blur`
eredménye mennne tovább kvantálás nélkül. A mért kimenet viszont
**kvantált** (csatornánként egyenletes rács), tehát:

⇒ **a korai ág élesben nem fut le**, és a fő út (az oktree-építés) FUT.

Ez a kérdést nem oldja meg, de **átfordítja**: nem a vezérlésben van az
ellentmondás, hanem a fő út **kimenetének értelmezésében**. A következő kör
ne vezérlési utat keressen, hanem azt mérje meg, mit ad a fő út a
3-3-2 LUT-tal együtt — a lap 2. pontja szerint a LUT-építő a rekesz színét
`r = c & 0xE0`, `g = (c & 0x1C) << 3`, `b = (c & 3) << 6` alakban
**visszafejti**, és ERRE kérdezi a fát; a keresés pedig „nem valódi
legközelebbi-szomszéd", hanem bit-alapú leszállás, ami a csomópont
**átlagát** adja. Egy 50×50-es minta fölött ez elvben közel egyenletes
rácsot is adhat — de ezt **mérni kell, nem feltételezni**.

#### 6.4 Mellékesen: a `NestedImageOperation` slot 6-ja STUB

`0x00bbf920` (6 bájt): `or eax, 0xffffffff; ret 0xc` — mindig `−1`. A
`Nested` tehát **nem** a slot 6-on végzi a munkát. A két vtábla
(`0x00ceff58` QuantizePalette, `0x00cf0774` Nested) a **3., 4. és 5. slotot
megosztja** (`0x00bc4ae0`, `0x00bc5160`, `0x00bc5180`); a `0x00bc4ae0`
(1660 bájt) viszont **egyetlen virtuális hívást sem tartalmaz**, tehát nem ő
a lánc-diszpécser.

*(A vtáblát az INDEXBŐL kell olvasni: a `rtti` tábla `slotok` mezője adja.
A nyers `read(0x008eff58, …)` értelmetlen bájtokat ad — az a tábla „második"
címe, nem a VA; a helyes VA a `0x00ceff58`.)*

### 7. Hol NINCS a rács, és mi a keresési kulcs pontosan (2026-09-08, 223. kör, #2746)

A 222. kör után a kérdés átfordult: nem „melyik út fut", hanem **„a futó út hol
számol rácsot"**. A mért kimenet `round(i·255/(Steps−1))` alakú, tehát valahol
kell lennie egy `255`-tel szorzásnak vagy `Steps−1`-gyel osztásnak.

#### 7.1 ⛔ A munkavégző törzsében NINCS ilyen skálázás

A `0x00bb5b60` **teljes** törzsét (1510 bájt) átnézve **egyetlen** lebegőpontos
osztás van, és a konstansa kiolvasva:

```
0x00bb5bd0  fild dword ptr [ebp + 8]        ; egész → FPU
0x00bb5bf6  fadd dword ptr [0xcf39e4]       ; csak a negatív ágon
0x00bb5bfc  fdiv qword ptr [0xcf3bd8]       ; ← a konstans: 50.0
0x00bb5c11  fstp dword ptr [esp + 0x10]
```

**`[0x00cf3bd8] = 50,0`** — ez a **mintaméret** (50 × 50, ld. a lap 2. pontját,
`0x00bb5c44 mov eax, 0x32`), nem a rács. `255`-tel szorzás és `Steps−1`-gyel
osztás a törzsben **nem szerepel**.

⇒ A 221. kör kizárta a képponti alkalmazót (`0x00bcb2f0`), ez a kör a
munkavégzőt: **a rács egyik helyen sem keletkezik.**

#### 7.2 A keresési kulcs képlete — SZÁMMAL, nem maszkokként

A lap eddig csak a maszkokat adta meg. A `0x00bb6055`–`0x00bb6082` kód
átszámolva:

```
c = (r3 << 5) | (g3 << 2) | b2
eax = ((((c & 0xE0) << 5) + (c & 0x1C)) << 5) + (c & 3)) << 6
R = (eax >> 16) & 0xFF ;  G = (eax >> 8) & 0xFF ;  B = eax & 0xFF
```

⇒ **`R = r3·32`, `G = g3·32`, `B = b2·64`** (ellenőrizve mind a 8, illetve 4
értékre):

| | szintek | tartomány |
|---|---|---|
| a keresési kulcs R/G | 8 × `i·32` | 0 … **224** |
| a keresési kulcs B | 4 × `i·64` | 0 … **192** |
| a **mért** Picasa-kimenet (`Steps=8`) | 8 × `i·36,43` | 0 … **255** |

A kulcs rácsa tehát **más léptékű ÉS más végpontú** (224/192 vs 255). Ez nem
cáfolja az oktree-utat (a kulcsra a fa válaszol, és a válasza bármi lehet), de
rögzíti, hogy a lap „3-3-2 tábla" szakaszát ezentúl SZÁMOKKAL is olvasni kell.

#### 7.3 ⚠️ ÖNHELYESBÍTÉS a lap 5.1 szakaszához: a „képfüggetlen" NINCS mérve

Az 5.1 így zárul: *„A leképezés ráadásul **képfüggetlen**: ugyanaz a bemeneti
szín ugyanazt a kimenetet adja más színeloszlású képben is."*

**Ehhez nincs mérés.** Az 5.1 táblázatának három sora (`alap`, `min`, `max`) a
**szűrő három BEÁLLÍTÁSA** (`Steps` 8 / 2 / 30, más `Smoothing` és `Fade`) —
nem három különböző színeloszlású forráskép. A mérés tehát **egy** forrásképen
készült, három exporttal.

Ez fontos, mert a képfüggetlenség lett volna a **legerősebb** érv az oktree
ellen: egy oktree-paletta definíció szerint képfüggő.

⛳ **Amit ez NEM dönt meg:** a rács-hipotézist. A `min` eset (`Steps = 2`) a
kimenet **98,4 %**-át a két végpontra (`0` és `255`) teszi — egy 2 színű
oktree-paletta a mérőkép saját színeiből (szürke sáv + színes mezők) nem adna
tiszta 0/255-öt. A rács-olvasat tehát áll; csak a „képfüggetlen" mondatot kell
**mérésre visszavezetni vagy törölni**.

**A megszerzés útja:** egy MÁSODIK, eltérő színeloszlású kép exportja
ugyanazzal a `Steps = 8` beállítással (a tulajdonos windowsos Picasájából). Ez
a mérés a rács-hipotézist megerősíti vagy megdönti — ma egyik sincs.

### 8. ⭐ A PALETTA KISEBB, mint a mért kimenet színkészlete (2026-09-09, 224. kör, #2746)

Négy kör keresett vezérlési magyarázatot. Ez a kör egy **számolást** végzett el,
ami eddig kimaradt — és ez a legerősebb érv eddig, új export nélkül.

#### 8.1 A `Steps − 1` redukció — most SAJÁT szemmel igazolva

A lap eddig állította; a 224. kör kiolvasta:

```
0x00bb5da8  mov eax, [esp + 0x10c4]   ; a 2. paraméter = Steps
0x00bb5daf  cmp eax, 2
0x00bb5db6  jne 0x00bb5dc4
0x00bb5db8  push eax                  ; Steps == 2  ⇒  2 szín
0x00bb5db9  call 0x00bcb6f0
…
0x00bb5dc4  add eax, -1               ; egyébként  Steps − 1
0x00bb5dc7  push eax
0x00bb5dc8  call 0x00bcb6f0           ; ugyanaz a redukáló
```

(A veremeltolás a 221. kör számításával egyezik: `[esp+0x10c0]` = 1. par,
`[esp+0x10c4]` = 2. par = `Steps`.)

⇒ **`Steps = 8` ⇒ a paletta 7 színű.**

#### 8.2 A mért kimenet ennél TÖBB színt tartalmaz

A `tests/render/test_quantizepalette_racs_2231.py` docstringjében rögzített,
a Picasa exportjából a **mezők közepén** kiolvasott értékek:

| mit | egyedi értékek | darab |
|---|---|---|
| a szürke sáv 12 mezője | 0, 36, 73, 109, 146, 182, 219, 255 | **8** |
| + a három színes mező | (182,36,36), (36,182,73), (36,72,182) | +3 |
| **összesen a mért pontokon** | | **11** |

⇒ **Már a szürke sávon belül 8 > 7**, és összesen 11 > 7.

**Egy 7 színű palettából ez nem állítható elő.** A palettaválasztás
definíció szerint a paletta elemeire képez le; ha a paletta 7 színű, a kimenet
legfeljebb 7 különböző színt tartalmazhat.

#### 8.3 A bizonyítottsági fok — és a fenntartás kimondva

**Erős, de nem bitre menő.** A referencia egy `.jpg`, tehát a tömörítés
színeket kever. Ezt két dolog tartja kordában:

1. az értékek a mezők **közepéről** vannak olvasva, ahol a JPEG nagy homogén
   területen nagyon pontos;
2. a nyolc szürke érték **egyenletes, 36 lépésenkénti lépcsőt** ad
   (`round(i·255/7)`) — a JPEG egy 7 színű képből nem hoz létre ilyen
   szabályos, nyolcfokú lépcsőt.

⚠️ Amit ez **nem** ad: bitre menő cáfolatot. Egy veszteségmentes (PNG)
referencia adná, de a Picasa exportja JPEG.

#### 8.4 Mit jelent ez a fő kérdésre

A 221–223. kör kizárta a képponti alkalmazót, a név szerinti megkerülő utat, a
`4`-es kódot és a munkavégzőt. Ez a kör hozzáteszi, hogy **a palettaválasztó út
a mért kimenetet elvben sem tudja előállítani** — nem azért, mert nem fut,
hanem mert **túl kevés színt ad**.

⇒ A `.picasa.ini`-vezérelt, teljes felbontású render **nem** a
`QuantizePaletteImageOperation` palettaválasztásának eredményét írja a képre.
Hogy akkor MI írja, továbbra is nyitott — de a kérdés innentől nem az, hogy
„melyik ág fut a művelet belsejében", hanem hogy **fut-e egyáltalán ez a
művelet abban az útban**.

**A következő kör ezt kérdezze:** mi bizonyítja, hogy a `filterdesc.xml`
`QuantizePalette` szűrője egyáltalán részt vesz a `.picasa.ini`-ből
visszaállított, teljes felbontású renderben? A `fullres="1" slow="1"` jelzők
(1247. sor) épp arra utalnak, hogy ott **külön út** van.

### 9. ✅ A „nincs név szerinti megkerülő út" MEGERŐSÍTVE — indextől függetlenül (2026-09-09, 226. kör, #2746)

A 225. kör kimérte, hogy az index `string_xrefs` táblája **26 %-ban hiányos**,
és ezzel gyengült az 5.2 szakasz lelete (*„pontosan egy `Quantize`-hivatkozás
van"*). A 226. kör **indextől függetlenül** újramérte.

**A módszer:** nyers bájtkeresés a teljes EXE-ben a `Quantize` mintára (nem az
indexből), majd a `.text` végigpásztázása a talált VA-kra (`paszta.py`,
darabolva, plafon alatt). Kontroll: a `0x00bb31f0` ismert hivatkozásának elő
KELL kerülnie — `assert`-tel kikényszerítve.

**A fájlban három** `Quantize`-tartalmú sztring van:

| VA | sztring | mi ez |
|---|---|---|
| `0x00c94c90` | `QuantizePalette` | a leíró `id` attribútumának értéke |
| `0x00cef9dc` | `imageOperations:QuantizePaletteImageOperation` | a művelet-gyár kulcsa |
| `0x00d48744` | `.?AVQuantizePaletteImageOperation@glimmer@@` | RTTI-név |

**A `.text`-ben ezekre pontosan EGY hivatkozás van:**

```
0x00bb3769  mov ecx, 0xcef9dc     ; a gyár-regisztráció (a 0x00bb31f0 törzsében)
```

⇒ **Az 5.2 szakasz lelete megerősítve**, most az indextől függetlenül.

#### 9.1 ⭐ ÚJ részlet: a rövid névre NULLA kódbeli hivatkozás

A `0x00c94c90` (`'QuantizePalette'`, a leíró `id`-je) címére a `.text`-ben
**egyetlen utasítás sem** hivatkozik. ⇒ A `.picasa.ini`
`filters=QuantizePalette=…` sorát a kód **nem beégetett névvel** azonosítja,
hanem a `filterdesc.xml`-ből betöltött `id` attribútummal (azt a
`0x008ff550` olvassa be, ld. az 1.3 szakasz mért jegyzetét).

**Ez a fő kérdés szempontjából számít:** nincs olyan út, amely a szűrő NEVÉRE
keresve kerülné meg a leíró-láncot. A `.picasa.ini`-vezérelt render a
leíró-láncon megy.

#### 9.2 A negatívum HATÓKÖRE — kimondva

A pásztázás a **`.text` szakaszra** és a **közvetlen érték** alakra ment
(`mov`, `push`, `cmp`, `lea` operandusában szereplő cím). Amit NEM zár ki:
egy számított cím (bázis + eltolás, tábla-indexelés). Ez a hatókör szűkebb,
mint a „nincs hivatkozás" — de a 223. kör indexre alapozott állításánál
lényegesen erősebb.

### 10. ⛔ A `fullres` HÁROMÁLLAPOTÚ, és a 2-es érték EGYETLEN szűrőé (2026-09-09, 227. kör, #2746)

A 225. kör megtalálta a jelzők olvasóját; ez a kör végigvitte, **ki kérdezi
vissza** a tárolt értéket. A fő kérdésre az eredmény **negatív**, de három
önálló lelettel.

#### 10.1 A jelzők tagoffszetei — mérve

A `0x008ff550` a beolvasott értékeket a leíró-objektum tagjaiba írja
(`[ebx+0x2c]` a leíró, a `0x008ff840`–`0x008ff891` sávban):

| jelző | cím | tag | típus |
|---|---|---|---|
| `fullres` | `0x008ff85b` | **`+0xd8`** | dword |
| `slow` | `0x008ff869` | **`+0xdc`** | byte |
| (3 további byte-jelző) | `0x008ff876`, `0x008ff883`, `0x008ff891` | `+0xdd`, `+0xde`, `+0xdf` | byte |

#### 10.2 ⭐ A `+0xd8` OLVASÓJA egy predikátum, ami a `2`-t vizsgálja

`0x008f6fc0` (27 bájt), teljes törzs:

```
mov  eax, [ecx + 8]              ; [this+8] = a leíró-objektum
cmp  dword [eax + 0xd8], 2       ; fullres == 2 ?
jne  0x008f6fd8                  ;   nem → false
cmp  byte [ecx + 0xc8], 0        ; [this+0xc8] != 0 ?
je   0x008f6fd8                  ;   nulla → false
mov  al, 1 ; ret                 ; TRUE
xor  al, al ; ret                ; FALSE
```

⇒ **`fullres == 2` ÉS `[this+0xc8] != 0`.** A `+0xd8` tehát **nem logikai**
jelző: a `2` kitüntetett érték.

*(A `0x008f6f90` egy egyszerű getter: `mov eax, [eax+0xd8]`.)*

#### 10.3 ⭐ A leíróban a `fullres` értékei — megszámolva

`runtime/filterdesc.xml` (63 005 bájt), `grep -o` + `uniq -c`:

| érték | darab |
|---|---|
| `fullres="1"` | **18** |
| `fullres="2"` | **1** |

**A `fullres="2"` egyetlen szűrőé: a `FocalZoom`** (888. sor):
```xml
<filter id="FocalZoom" mode="effect" zerostate="none" fullres="2">
```

A `QuantizePalette` (1244. sor) ezzel szemben `fullres="1" slow="1"`.

⇒ **A `0x008f6fc0` predikátum a szállított leíróban KIZÁRÓLAG a `FocalZoom`-ra
teljesülhet.** A `QuantizePalette` nem kap külön utat a `fullres` jelzőn át —
a #2746 „külön renderút" hipotézise ezen a szálon **elesik**.

#### 10.4 A többi jelző darabszáma — ugyanabból a mérésből

| jelző | előfordulás |
|---|---|
| `slow="1"` | **13** (köztük a `QuantizePalette`) |
| `resize="1"` | **5** |
| `persist="1"` | **16** · `persist="0"` | **9** |

⚠️ A lap 1.3 szakaszának jelentés-értelmezései (mit „jelent" a jelző) továbbra
is a NÉVBŐL vannak. Ami MÉRVE van: a beolvasás helye, a tagoffszet, a `2`-es
predikátum, és a fenti darabszámok.

#### 10.5 Következmény a `FocalZoom`-ra (#723)

A `FocalZoom` az **egyetlen** szűrő, amely a `fullres="2"` kitüntetett
állapotot kapja, és van rá egy külön predikátum a binárisban. Ha a
`FocalZoom`-ot valaha implementáljuk vagy javítjuk, ezt figyelembe kell venni
— a #723 (a `FocalZoom` vezérlő-készlete) kapott erről kommentet.

### 11. ⛔ A GÉPI LÁNC KIMERÜLT — nyolc irány kizárva (2026-09-09, 228. kör, #2746)

A 228. kör az utolsó gépi jelöltet, a `NestedImageOperation` keverő ágát vitte
végig. **Ott sincs.** Ezzel a `.picasa.ini`-vezérelt renderre nézve a bináris
oldali lehetőségek elfogytak, és ezt kimondani helyesebb, mint újabb kört
nyitni rá.

#### 11.1 A `Nested` lánca — nincs benne aritmetika

| mit néztem meg | eredmény |
|---|---|
| slot 0 (`0x00bc1280`, 73 b) | 0 aritmetikai utasítás |
| slot 1 (`0x00bc12d0`, 5 b) → `jmp 0x00bc4900` | thunk |
| slot 7 (`0x00bc12e0`, 246 b) | 0 aritmetikai utasítás |
| slot 6 (`0x00bbf920`, 6 b) | **stub**: `or eax,-1; ret` (225. kör) |
| a hívottak: `0x00bc4880` (123 b), `0x00bc13e0` (61 b), `0x00638ff0` (78 b) | 0 aritmetikai utasítás |
| **`0x00bc4900`** (474 b) — a `Nested` attribútum-olvasója | 5 lebegőpontos utasítás, **mind `fld`/`fstp`** (érték-mozgatás), **osztás és szorzás nincs** |

**A `BlendAlpha` hivatkozása pontosan EGY** — a `0x00bc4999`-nél, ebben az
attribútum-olvasóban (indextől független pásztázás, a `fullres`-re állított
kontrollal: `0x008ff714`, előkerült).

⇒ A mért `round(i·255/(Steps−1))` rács **`Steps−1`-gyel osztást kíván**. A
`Nested` láncában ilyen művelet nincs.

#### 11.2 A nyolc kizárt irány — együtt

| # | irány | kör | mi zárta ki |
|---|---|---|---|
| 1 | képponti alkalmazó (`0x00bcb2f0`) | 221 | 744 b törzs, 0 osztás, 0 lebegőpontos |
| 2 | névre kereső megkerülő út | 223 → 226 | indextől függetlenül **1** hivatkozás (a regisztráló) |
| 3 | a `4`-es visszatérési kód | 222 | 2806 hívóhely, 0 vizsgálja (3 hamis pozitív, elolvasva) |
| 4 | a munkavégző (`0x00bb5b60`) | 223 | 1510 b, egyetlen osztás, konstansa **50,0** (mintaméret) |
| 5 | a palettaméret | 224 | `Steps−1` = **7** szín vs a mért **11** egyedi szín |
| 6 | a `fullres` jelző | 227 | a `2`-es predikátum a szállított leíróban **csak a `FocalZoom`-ra** áll |
| 7 | a `Nested` slotjai | 228 | 0 aritmetikai utasítás |
| 8 | a `Nested` attribútum-olvasója | 228 | a `BlendAlpha` egyetlen hivatkozója, 0 osztás/szorzás |

#### 11.3 Amit ez a kérdésről mond — és amit NEM

**A rács a szűrő-láncban sehol nem keletkezik.** Ez nyolc, egymástól független
mérés eredménye, mindegyik címmel.

⚠️ **Amit ez NEM jelent:** hogy a rács-olvasat hibás. A viselkedés-mérés
(`ΔE 0,268`, 97,6 % a rácson) továbbra is megerősített. A két oldal
**összeegyeztetése** a nyitott kérdés — és ehhez a bináris oldalán elfogytak a
megnevezhető jelöltek.

#### 11.4 Ami hátravan — és NEM gépi munka

1. **#2770** (`felhasználóra-vár`): egy második, természetes átmenetes kép
   exportja `Steps = 8`-cal. Ez **a rács-hipotézist** dönti el (képfüggő-e a
   leképezés) — ma erre nincs mérésünk.
2. Ha a #2770 azt adja, hogy a leképezés **képfüggő**, akkor az oktree-út
   mégis futhat, és a 8-as pont (a palettaméret-ellentmondás) magyarázatra vár.
3. Ha **képfüggetlen**, akkor a rács forrása a szűrő-láncon KÍVÜL van (a
   mentési/JPEG-út vagy a színkezelés) — az új, még nem vizsgált terület.

⛔ **Amíg a #2770 nem érkezik meg, erre a kérdésre gépi kört nyitni nem
érdemes.** A jegy ezért `blocked`, nem `ready`.

*Bizonyítottsági fok: a **viselkedés-mérés megerősített** (referencia-export,
két kontrollal); a **binárisbeli olvasat megerősített** (minden állítás
mellett cím); a **kettő összeegyeztetése NYITOTT**, a folytatás nevesítve.*

## ⛔ A jelvény-lánc MINDEN szeme utasításszinten mérve — és az ellentmondás ezzel ÉLESEDIK (2026-09-09, 232. kör, #2125)

A tulajdonos 2026-09-08-án megválaszolta a jegy blokkoló kérdését: *„Rajta
van-e a kék »1« a Színinvertáláson egy másik képen? IGEN! SOK képen tesztelve
Picasa 3 alatt!"* — és kimondta, hogy **több felhasználói teszt nem kérhető, a
választ a binárisnak kell megadnia.**

Ez a kör ezért egyetlen dolgot csinált: a 216–217. kör láncát **újramérte,
szemenként, örökölt feltevés nélkül** — mert egy zárt láncnak és egy
megismételt megfigyelésnek nem szabadna ellentmondania.

### 1. Előbb a megfigyelés: a jelvény GEOMETRIÁVAL azonosítva

A `research/#1869-effekt-ful-kis-kek-jel/` két felvételén a kék foltok
befoglaló dobozai (küszöb: `B≥165 ∧ B−R≥70 ∧ B−G≥45`, összefüggő klaszterek
≥25 képpont):

| fül | doboz | méret |
|---|---|---|
| 3. (Szépia) | x 162–174, y 86–97 | **13×12** |
| 3. (Fekete-fehér) | x 251–262, y 86–97 | 12×12 |
| 3. (Melegítés) | x 74–86, y 158–168 | 13×11 |
| **4. (Színinvertálás)** | **x 162–174**, y 224–235 | **13×12** |

A 4. fül jelvénye **ugyanakkora és ugyanabban az oszlop-eltolásban** áll, mint
a 3. fül szépia-jelvénye (a sorköz 72 képpont, a két ablak magassága 6
képponttal tér el) ⇒ **ugyanaz a réteg**, nem valami más felületi elem. A 4.
fülön ez az EGYETLEN ilyen doboz; a többi kék klaszter a Hőtérkép/HDR
bélyegképének saját tartalma (75×46, 20×18 — nagyságrenddel nagyobbak).

⇒ A megfigyelés **megerősítve, a saját anyagunkból, mérve** — nem emlékezeti
tévedés és nem képfüggő.

### 2. A lánc újramérése — mind a nyolc szem

| # | állítás | ahol MÉRTEM |
|---|---|---|
| 1 | a csempe-tábla 36×12 bájt; `+0` elsődleges, `+4` másodlagos, **`+8` mind a 36 tételen 0** | nyers kiolvasás `0x00c7e5a0`-ról |
| 2 | a csempeépítő a táblából **csak** a `+0`-t és a `+4`-et olvassa | `FUN_005d7c20` teljes törzsében pontosan 2 hivatkozás (`0x005d7d2e`, `0x005d7d70`) |
| 3 | a kereső (`regiszter vtbl+4` = `FUN_0050e460`) **egyetlen** azonosítót kezel külön: `desat` (`0x00c86f24`, 6 bájt) | `0x0050e481`–`0x0050e4ad` |
| 4 | ⭐ **ÚJ: a `FUN_008f9fe0` egy ÁLNEVET is felold** — `crop` (`0x00c812f8`) → **`crop64`** (`0x00c80adc`), és ez az egyetlen álnév | `0x008fa030`–`0x008fa06f` |
| 5 | ⭐ **ÚJ: a keresés hibaágai** — ha a kereső nem 0-t ad, vagy a kapott mutató NULL, a jelző **érintetlen marad**, és az alapértéke 0 | `0x005d7ea3 test eax,eax / jne`, `0x005d7eaf test ecx,ecx / je` → `0x005d7fd2`; az alapérték `0x005d7e9c` |
| 6 | a `CGenericFilter` vtáblája `0x00cd184c`, és a `+0x14` **tényleg** a `FUN_008f6cc0` | a vtábla nyers kiolvasása (`+0x10`→`0x008f6bc0`, `+0x14`→`0x008f6cc0`, `+0x18`→`0x008fc000`) |
| 7 | `this+8` = a leíró | a ktor **első** utasítása: `0x008f6ad0 mov [esi+8], ecx` |
| 8 | a leíró `+4` alapértéke **0**, és egyetlen írója van | `0x008ff5a7 mov [esp+0x28], 0` (alapérték) → `0x008ff847 mov [eax+4], ecx`; a `FUN_00900490`-nek **egy** hívója van (`0x008ff693`) |
| 9 | a `mode=` kódtábla — az összehasonlítás **hosszával** együtt | `effect`=4 (`"effect\0"`, 7 bájt), `oneclick`=1 (9 bájt), `soft`=5, `hard`=2, `tool`=6, `history`=7, egyéb 0 |
| 10 | a jelvény-réteg neve a **hurokindexszel** épül | `0x005d80d3 push ebx` + `push 0x00c96304` (`editpanel/fx%d_adorn`) |

**Kontroll a vtábla-olvasásra:** a `+0x18`-as rés visszatérési értékét a hívó
`strlen`-nel dolgozza fel és sztringgé alakítja (`0x005d7ee0`–`0x005d7ef2`) ⇒
`char*` felirat. Egy egész és egy sztring a szomszédos réseken — a
rés-kiosztás tehát nem elcsúszott olvasat.

**Nincs második építési út:** a leíró vtáblájára (`0x00cd18fc`) és a
`CGenericFilter` vtáblájára (`0x00cd184c`) egyaránt **pontosan két** abszolút
hivatkozás van, és a második mindkét esetben **destruktor**
(`0x008fa740`, `0x008fa880` — a végükön az ősosztály vtáblája,
`0x00c7f980`). Konstruktor + destruktor = egy osztály, egy építési út.

### 3. Amit ez a kör ÚJRA kizárt — indextől függetlenül

| lehetőség | a mérés |
|---|---|
| beágyazott leíró az EXE-ben | `<filter` **0** előfordulás; `oneclick` **1** (maga az összehasonlítási literál); `zerostate` 1 |
| második `Invert` azonosító | az `Invert` bájtsorozat a **teljes fájlban 4×**: `&Invert Selection`, a csempe-azonosító, egy hibaüzenet, egy RTTI-név — **nincs** második szűrő-azonosító |
| kulcsütközés a 12 `oneclick` szűrővel | a 12: `autobacklight, autolight, autocolor, bw, enhance, warm, grain, grain2, sepia, autocontrast, moviestart, movieend` — egyik sem ütközik |
| eltolt regisztráció (a szomszéd leírója) | fájlsorrend: az `Invert` (986. sor) elődje a `Holga`, utódja az `IR` — mindkettő `effect` |
| a jelvényt más attribútum vezérli | a négy jelvényes (`sepia`,`bw`,`warm`,`Invert`) nyitótagját **egyetlen** attribútum sem különbözteti meg a jelvénytelen, ugyanilyen „csupasz" `effect`-ektől (`PicnikTint`, `radblur`, `IR`, `Sixties`, `TwoTone`) |
| második leíró-fájl a telepítésben | a teljes fánkon `find -iname '*filterdesc*' -o -iname '*picnik*'` ⇒ **egyetlen** találat: `runtime/filterdesc.xml`; a `runtime/filters.txt` mappaszűrő (13 sor, `DirectoryFilters`), nem szűrőleíró |

### 4. Az ellentmondás — élesen kimondva

Három állítás, amelyek közül **legfeljebb kettő** lehet igaz:

1. a jelvény akkor és csak akkor látszik, ha a csempe szűrőjének leíró-`+4`-e
   `1` — *utasításszinten mérve, fent, tíz ponton*;
2. a Színinvertálás csempéjén **van** jelvény — *a saját felvételünkön,
   geometriával mérve, és a tulajdonos sok képen megerősítette*;
3. a futásidejű leíróban az `Invert` `mode="effect"` (kód 4) — *ez az EGYETLEN,
   amit nem a binárisból, hanem a LEMEZEN lévő fájlból tudunk.*

⇒ **A cáfolható elem a 3.** A `0x00405615`-nél a program a
`runtime\filterdesc.xml` **relatív** útvonalat kapja, és azt futásidőben oldja
fel egy útvonal-objektumba (`FUN_00408b50`, `[reg+0x1450]`). Amíg nem tudjuk,
**mihez képest** relatív ez az útvonal, addig a kutatási fánk 2015-ös
telepítés-másolatának `filterdesc.xml`-je nem bizonyítottan azonos azzal, amit
a tulajdonos futó Picasája beolvas.

### 5. A következő lépés — és az is GÉPI

**Nyitott kérdés (ÖRÖKÖLT, a 216. kör óta):** melyik könyvtárhoz képest oldja
fel a szűrő-regiszter a `runtime\...` útvonalait? A megszerzés útja
utasításszintű és nem igényel felhasználói tesztet: a regiszter
(`0x146c` bájtos objektum, vtábla `0x00c7f724`) betöltő metódusából a
`[this+0x1450]` útvonal-objektumot használó fájlmegnyitásig kell eljutni, és
ki kell olvasni, mi kerül elé (telepítési mappa a `GetModuleFileName`-ből, vagy
felhasználói adatkönyvtár). Ha felhasználói adatkönyvtár, akkor a telepítés
melletti fájl **nem** az igazságforrás, és az ellentmondás magától feloldódik.

*Bizonyítottsági fok: **megerősített** az 1–3. szakasz (utasításszintű
újramérés, képpont-geometria, kimerítő bájtszintű kizárások); a 4. szakasz
következtetése **erős**; az 5. szakasz kérdése **nyitott**, a megszerzés útja
megnevezve.*

## ✅ A `runtime\...` útvonalak GYÖKERE megvan — és ezzel a „másik fájl" magyarázat is BEZÁRUL (2026-09-09, 233. kör, #2125)

A 232. kör azt mondta ki, hogy a jelvény-lánc három állítása közül az egyetlen
cáfolható az, hogy a **futásidőben beolvasott** leíró azonos-e a lemezen
lévővel. Ez a kör azt mérte ki — és **a saját előző következtetésemet is
helyesbíti**: a magyarázat nem áll.

### 1. A gyökér: egy globális, PONTOSAN két íróval

A relatív utat (`runtime\filterdesc.xml`) az útvonal-objektum feloldója
(`FUN_00980ec0`) a `[0x00d689f0]` globális elé fűzve állítja elő. A globálisra
a `.text`-ben **15 hivatkozás** van (indextől független abszolút pásztázás);
közvetlen `mov [globális], reg` alakú írás **egy sincs** (mind a kilenc
lehetséges opkód-alakra kerestem) — a globális egy sztring-**objektum**, tehát
értékadással kap értéket, és pontosan két helyen kap:

| # | hol | mit tesz bele |
|---|---|---|
| 1 | `0x004057b3` (`call 0x407760`, `ecx = 0x00d689f0`) | a **`Runtime` / `AppPath` beállítás** értékét — de csak ha nem üres ÉS eltér a jelenlegitől (a `0x00405780`–`0x0040579a` összehasonlító hurok után) |
| 2 | `0x00980f77` (`call 0x4084f0`, `eax = 0x00d689f0`) | **lusta alapérték**: ha a globális üres, a `[0x00d67840]` modul-leíróra hívott `GetModuleFileNameA` (`0x00980c7b`) eredményének a **könyvtár-része** (`0x004089e0`), és bejegyzi a globálisba |

⇒ **Alapértelmezés: a futó modul saját könyvtára** (a telepítési mappa).
**Felülírás: a `Runtime\AppPath` beállítás**, amelyet a beállítás-olvasó
(`FUN_00407630`) a **`HKEY_CURRENT_USER`** kulcsból vesz
(`0x0040764f mov eax, 0x80000001`).

### 2. ⛔ ÖNHELYESBÍTÉS: a „másik fájl" magyarázat NEM áll

A tulajdonos 2026-09-05-i telepítés-mentése (`/mnt/nas/My Pictures/
Picasa-telepites-mappa-mentes-20260905/Picasa3/`) alapján, mérve:

| mit | eredmény |
|---|---|
| `Picasa3.exe` md5 | `5a361547dc3abed7fc54c13c82c355ce` — **bájtra azonos** a kutatási fánkéval |
| `runtime/filterdesc.xml` md5 | `2cdd163f7ab2cec09d0f6990f2a179bc` — **bájtra azonos** |
| `runtime/picnik_effects/` | **nincs** |
| `update/` | üres (`LifeScapeUpdater/`, tartalom nélkül) |
| második `filterdesc*.xml` | nincs |

Tehát **ugyanaz a bináris ugyanazt a leírót olvassa**. A `Runtime\AppPath`
felülírás elvben más gyökeret adhatna, de az az EGÉSZ `runtime\` fát átvinné
(i18n, respack, `constants.ui`) — egy ilyen telepítésben a program nem a
megszokott felületét mutatná. ⇒ A 232. kör „az egyetlen cáfolható elem"
állítása **megdőlt**: a leíró azonossága ezzel megerősített, nem nyitott.

### 3. Ami ebben a körben MÉG megerősítést kapott

- **`[0x00d67f68]` tényleg a szűrő-regiszter**: a beállítója (`FUN_00401fb0`,
  `0x00401fc6 mov [0xd67f68], esi`) és a leszedője egyaránt **egyetlen**
  hívóhelyű (`0x00405697`, `0x00405aea`), és a regiszter ktora
  (`FUN_004021a0`) is egyetlen hívóhelyű (`0x0040568c`). A globálisra a
  `.text`-ben 31 hivatkozás van, más beállító nincs.
- **A térkép-keresés kulcsra megy** (`FUN_008fa400` → `FUN_00901c30` →
  `FUN_0063dd70`, majd `[[reg+0x1454]+8][index*4]`) — nincs prefix- vagy
  „legközelebbi" találat.
- **A jelző rekeszét bájtszinten** is ellenőriztem (a lineáris dekódolás
  elcsúszhat, ezért nem elég): a `0x005d7c20`–`0x005d8260` tartományban a
  `[esp+0x64]` rekeszt **öt** utasítás érinti (`0x005d7d81`, `0x005d7d9d`,
  `0x005d7ddf`, `0x005d7ecc` = a `sete`, `0x005d8109` = a `cmp`), a
  `[esp+0x6c]`-et egy (`0x005d7e9d` = az alapérték). **Nincs rejtett író.**
- **A rétegnevek 1-alapúak** (`editpanel/fx1_adorn` … `fx12_adorn`, `fx0_adorn`
  **nincs**; a csempe-rétegek ugyanígy `fx1`…`fx12`), és a hurokváltozó a
  névadáskor épp az 1-alapú index (a hurokvég `0x005d820d cmp ebx,0xc` +
  `mov [esp+0x24], ebx` szerint `ebx` a KÖVETKEZŐ 0-alapú tábla-index, azaz a
  törzsben az aktuális csempe **+1**). ⇒ **Nincs eltolódás** a jelvény és a
  csempéje között.

### 4. Hol tart ezzel a kérdés

Két állítás mérve (a mechanizmus utasításszinten, a megfigyelés
képpont-geometriával), a harmadik — a leíró azonossága — **most már szintén
mérve**. A három együtt nem állhat fenn, tehát a hiba a **modellünkben** van,
nem az adatban.

**A megmaradt, meg nem vizsgált rés — kimondva:** a 232. kör azt igazolta, hogy
a leíró `+4` mezőjének **az XML-elemzőben** egyetlen írója van. Azt **nem**
igazolta, hogy a program futása során **máshonnan** senki nem ír bele. A
`+4` egy közönséges tagoffszet; egy másik kódúton kapott leíró-mutatón át
végzett írás a mostani pásztázásban nem látszana.

**A következő kérdés (K15), és az is gépi:** ki írja a leíró `+4` mezőjét a
program EGÉSZÉBEN? A megszerzés útja: a leíró-mutatót előállító helyek
(`CGenericFilter+8`, a `[regiszter+0x1454]` térkép értékei, a
`FUN_008fa0ea` ág) hívási környezetében minden `mov [reg+4], …` alakú írás
összegyűjtése — nem csak az elemzőben.

*Bizonyítottsági fok: **megerősített** az 1–3. szakasz (utasításszintű
mérés, md5-összevetés, bájtszintű rekesz-pásztázás); a 4. szakasz rése
**nevesített és gépi úton zárható**.*

## ⛔ A regisztert KÉT hely építi — önhelyesbítés, és miért nem pásztázható a `mode` mező (2026-09-09, 234. kör, #2125)

### 1. A `+4` offszet NEM pásztázható — ez maga is lelet

A 233. kör kérdése az volt: ki írja a leíró `+4` (`mode`) mezőjét a program
egészében? A válasz módszertani: **így nem lehet kérdezni.** Mérve a teljes
`.text`-en, bájtszintű mintával:

| alak | előfordulás |
|---|---|
| `mov [reg+4], reg` (`89 /r`, mod=01, disp8=4) | **8 796** |
| `mov [reg+4], imm32` (`C7 /0`) | **869** |

A `+4` a program leggyakoribb tagoffszete. Egy „ki írja" kérdés tehát csak
**provenienciával** dönthető el — azzal, hogy honnan lehet egyáltalán
leíró-mutatót szerezni —, nem bájtmintával. *(Ez visszamenőleg pontosítja a
232. kör „egyetlen író" leletét: az az állítás az XML-elemzőre igaz, és csak
arra volt értve.)*

**A provenienciát viszont kimértem, és szűk:**

- a leíró-osztály ktorának (`FUN_008f6910`) **egyetlen** hívóhelye van
  (`0x008ff81f`), és az egyetlen `push 0xec` a szűrő-ágon ugyanott
  (`0x008ff80a`);
- leíró **kizárólag** olyan elemre készül, amelynek a neve szó szerint
  `filter` (`0x00c843d8`, 7 bájtos `repe cmpsb` a `0x008ff592`-nél);
- leíróhoz hozzáférni két úton lehet: a `[regiszter+0x1454]` térképen át, és a
  `CGenericFilter+8` tagon át.

### 2. ⛔ ÖNHELYESBÍTÉS: a regiszter-globálisnak KÉT írója van, nem egy

A 233. kör azt írta, hogy a `[0x00d67f68]` beállítójának (`FUN_00401fb0`)
**egyetlen** hívóhelye van, és ezt a regiszter egyediségének bizonyítékaként
adta elő. A **függvényre** igaz — a **globálisra nem**:

```
FUN_0053fe30:
  0x0053fe77  mov eax, 0x00c7f150        ; "runtime\filterdesc.xml"
  0x0053fe9f  mov eax, 0x00c7f168        ; "runtime\picnik_effects\"
  0x0053fed4  push 0x146c ; call operator new
  0x0053fef6  call 0x00401ac0            ; alaposztály-ktor a két útvonallal
  0x0053fefb  mov [esi], 0x00c7f724      ; A REGISZTER VTÁBLÁJA
  0x0053ff13  … call [[régi]+0]          ; a RÉGI regiszter felszabadítása
  0x0053ff1b  mov [0x00d67f68], esi      ; ⭐ KÖZVETLEN írás — a beállítót MEGKERÜLVE
  0x0053ff26  call 0x008fa470            ; és betöltés
```

⇒ **a szűrő-regiszter futásidőben újraépül és kicserélődik.** Az előző kör
pásztázása azért nem vette észre, mert a beállító *függvény* hívóit kereste, a
globális *írásait* pedig csak a `mov [globális], reg` alakokra — ez az ág
viszont `mov [0xd67f68], esi` alakban ír, ami benne VOLT a 31 hivatkozás
között (`0x0053ff1d`), csak nem lett elolvasva. **A hivatkozás-listát nem elég
előállítani, el is kell olvasni.**

**Amit ez NEM jelent:** az újraépítés **ugyanazt a két útvonal-literált**
használja (`0x00c7f150`, `0x00c7f168`), tehát nem másik fájlból tölt.

### 3. További mérések ebből a körből

- **A betöltő** (`FUN_008fa470`, hívói: `0x00401fd1` és `0x0053ff26`) a leírót
  `fopen(útvonal, "rb")` + `fseek`/`ftell` + `malloc` + `fread` úton olvassa be
  (`0x00c82fdc = "rb"`), majd a `[reg+0x1454]` térképbe szúr be
  (`0x008fa658 add ecx, 0x1454` → `call 0x009c1750`).
- **A második útvonal NEM halott:** a betöltő a `0x008fa5b3`-nál kiolvassa a
  `[reg+0xa2c]` mezőt — ez a `runtime\picnik_effects\` út —, és ha nem üres,
  külön ágon dolgozza fel.
- **A regiszter mezőkiosztása** (`FUN_00401ac0`): `+0` vtábla, `+4` az első
  útvonal-objektum, `+0xa2c` a második, `+0x1454`…`+0x1460` a térkép,
  `+0x1464` és `+0x1468` két gyár (`0x0050d740`, `0x0050e260`).
- **A `GetMode()`-nak van MÁSODIK fogyasztója:** a `0x0050d740` gyár a
  `0x0050d751`-nél maga is a `vtbl+0x14`-et hívja — tehát a mód nem csak a
  csempeépítőt érdekli.

### 4. A következő kérdés (K16) — és az is gépi

Két, egymást kiegészítő rész:

1. **Mikor fut az újratöltés?** A `FUN_0053fe30`-nak két hívója van
   (`0x0054188a`, `0x00541e93`); ki kell olvasni, milyen eseményre futnak, és
   hogy a szerkesztő-fül felépülése előtt vagy után.
2. **Felülír-e a beszúrás?** A `0x009c1750` beszúró: ha egy már meglévő
   azonosítót egy későbbi bejegyzés **felülír**, akkor a betöltés sorrendje
   (első fájl → második út) érdemben más leírót adhat ugyanarra az azonosítóra.

*Bizonyítottsági fok: **megerősített** az 1–3. szakasz (bájtszintű
számlálás, egyértelmű hívólista, utasításszintű olvasás); a 4. szakasz
kérdései **nyitottak**, a megszerzés útja megnevezve.*

## ✅ MEGOLDVA: az `Invert` futásidőben `oneclick` lesz — a leíró-elemző ELŐLÉPTETI (2026-09-09, 235. kör, #2125)

Négy körön át állt az ellentmondás: a jelvény feltétele mérve `mode == 1`, az
`Invert` a leíróban `mode="effect"` (4), a jelvény mégis ott van rajta. A hiba
a **modellünkben** volt, ahogy a 234. kör kimondta: azt igazoltuk, hogy a
leíró `+4` mezőjének **az elem NYITÓTAGJÁBAN** egy írója van — azt nem, hogy a
program egészében.

### 1. A hiányzó szem: előléptetés a `</filter>` lezárásakor

A proveniencia-csatornát végigmérve (minden `[ctx+0x2c]` olvasás után írás a
leíró `+4`-ébe, a `0x008fe000`–`0x00906000` tartományban bájtszintű mintával)
**két** valódi író adódott, nem egy. *(A pásztázás három jelöltet adott; a
`0x008fff9c` HAMIS POZITÍV: az ott betöltött leírót a `0x008fff8a`
`operator new(0x20)` felülírja, tehát az írás egy ÚJ objektum `+4`-ét érinti,
nem a leíróét — a 236. kör helyesbítése.)* A második író a lezáró-kezelőben
áll, közvetlenül a `"filter"` elemnév egyeztetése után (`0x0090016e`, 7 bájtos
`repe cmpsb` a `0x00c843d8`-ra):

```
0x00900180  mov  eax, [ebp + 0x2c]        ; a leíró
0x00900183  cmp  dword ptr [eax + 4], 4   ; mode == effect ?
0x0090018a  jne  0x9001b0
0x0090018c  cmp  byte  ptr [eax + 0x38], dl   ; (dl = 0)
0x0090018f  jne  0x9001b0
0x00900191  cmp  byte  ptr [eax + 0xa1], dl
0x00900197  jne  0x9001b0
0x00900199  cmp  byte  ptr [eax + 0x80], dl
0x0090019f  jne  0x9001b0
0x009001a1  cmp  dword ptr [eax + 0x84], edx
0x009001a7  jne  0x9001b0
0x009001a9  mov  dword ptr [eax + 4], 1   ; ⭐ MODE := 1 (oneclick)
```

⇒ **egy `mode="effect"` szűrő, amelynek ez a négy mezője üres marad a törzs
feldolgozása után, futásidőben `oneclick`-ké válik** — és ezért kap kék
jelvényt. A négy mezőt a `<filter>` **gyerekelemei** töltik (a nyitótag csak a
`+4`, `+8`, `+0xd8`…`+0xdf` mezőket írja, `0x008ff847`–`0x008ff891`); a
gyakorlatban ezek a **felhasználói vezérlők** tárolói.

### 2. Kontroll: a szabály MIND A 24 megfigyelt csempére teljesül

A leíró oldaláról a „nulla vezérlő" próbája: van-e a `<filter>` törzsében
`<slider>`, `<colorwheel>`, `ctrl:*`, `mx:*` vagy névtér nélküli
`HSlider*`/`VSlider*` elem. Előrejelzés = `mode=="oneclick"` **vagy** nulla
vezérlő; megfigyelés = a `research/#1869-effekt-ful-kis-kek-jel/` két
felvételén mért jelvények.

| fül | egyezés |
|---|---|
| 3. (12 csempe) | 12/12 |
| 4. (12 csempe) | 12/12 |
| **eltérés** | **0** |

*(A próba két saját hibáját a kontroll fogta meg: először a `ctrl:`/`mx:`
névterű vezérlők, majd a névtér nélküli `HSliderPlus` maradt ki a mintából —
mindkétszer az `assert` állította meg a jelentést. A vezérlő-készlet a
javítás után zárt.)*

### 3. A szállított leíróban PONTOSAN EGY szűrő esik az előléptetés alá

A 84 szűrő végigmérve: `mode="effect"` **és** nulla vezérlő ⇒ **`Invert`**, és
csak az. Az eredetileg `oneclick` 12 (`autobacklight, autocolor, autocontrast,
autolight, bw, enhance, grain, grain2, movieend, moviestart, sepia, warm`)
mellé tehát futásidőben **13.** lép be az `Invert`.

⇒ **A tulajdonos megfigyelése helyes volt, a mechanizmus is helyes volt** — a
kettő közé az előléptetés hiányzott. Az ellentmondás megszűnt.

### 4. Nálunk MA — mérve

~~`src/picasapy/render/registry.py: one_click_keys()` a `mode == "oneclick"`
bejegyzéseket adja vissza: **12 kulcs**. A `registry_data.py:375` szerint az
`invert` nálunk `"effect"`, tehát a Színinvertálás csempéjén **nincs**
jelvény. Az eredetiben van. ⇒ termékoldali teendő (külön jegy): az
`one_click_keys()` vegye fel az előléptetést is, azaz `effect` + nulla vezérlő
⇒ jelvény; a várt eredmény **13 kulcs**.~~

✅ **MEGVAN (2026-09-10, #2800):** az `one_click_keys()` alkalmazza az
előléptetést (`_elolepteteshez_ures`), és **13 kulcsot** ad — az `invert`-tel
együtt. A mi oldali megfelelés: nincs csúszka, nincs fókuszpont-kurzor, nincs
színválasztó, ÉS egyetlen viselkedés-jelző sem áll (`full_res`, `slow`,
`resizes`, `rotates`, `persists_region`). **Kontroll a szűkösségre:** így
pontosan EGY szűrő lép elő, ahogy az eredetiben is; a `cinemascope` (aminek
szintén nincs csúszkája) a `full_res`/`resizes` jelzőin fennakad. Őrök:
`tests/render/test_egykattintasos_eloleptetes_2800.py` (7 eset) és a rajzolt
csempén `TestSzininvertalasJelveny`
(`tests/app/qml_functional/test_effect_tile_grid_704.py`).

### 5. Ami ebből NYITVA marad — pontosan

A négy mező (`+0x38`, `+0xa1`, `+0x80`, `+0x84`) **jelentése** mérésből
következtetett, nem közvetlenül kiolvasott: a „felhasználói vezérlő" olvasat a
24/24 egyezésen és a 84 szűrős kimerítő pásztázáson nyugszik. A közvetlen
lezáráshoz a mezők ÍRÓIT kell megnevezni a gyerekelem-kezelőkben (jelöltek:
`0x00903a48`, `0x0090407f`, `0x00904109`, `0x0090421c`, `0x00904338`,
`0x0090436f` a `+0x38`-ra és `0x00900e1a` a `+0x84`-re). Ez a szabály
ÉRVÉNYESSÉGÉT nem érinti, csak a mezők nevét.

*Bizonyítottsági fok: **megerősített** az 1–4. szakasz (utasításszintű
előléptetés, 24/24 kontroll nulla eltéréssel, kimerítő 84-es pásztázás, a mi
oldalunk mért állapota); az 5. szakasz **nyitott**, a megszerzés útja
megnevezve.*


## A négy döntő mező — részleges névadás és egy KIMONDOTT feszültség (2026-09-09, 236. kör)

A #2799 az előléptetés **szabályát** utasításszinten adta meg; ez a szakasz a
négy vizsgált mező **nevét** kereste. Az eredmény részleges, és a hiányt
kimondom.

### 1. `+0x84` = a felhasználói vezérlők SZÁMLÁLÓJA — mérve

| bizonyíték | cím |
|---|---|
| a leíró konstruktora nullázza | `0x008f6955` |
| a `colorwheel`-kezelő olvassa, és **nem vesz fel többet, ha már ≥ 2** (`cmp dword ptr [leíró+0x84], 2` / `jge`) | `0x008ffb32` |
| az `<effect>` törzsét feldolgozó `FUN_00900540` **növeli** (`edx = számláló + 1`, majd `mov [leíró+0x84], edx`) | `0x00900e1a` |

A `FUN_00900540` azonosítása a sztringjeiből: `filter_%s_label%d` és
`_sldrRadius` (az utóbbi a HDR sugár-csúszkájának azonosítója a leíróban) ⇒ ez
a függvény az effekt-vászon **vezérlőit** veszi számba.

### 2. `+0x38`, `+0x80`, `+0xa1` — az elemzőben CSAK a konstruktor írja őket

Bájtszintű, teljes `.text`-re futtatott pásztázás (a `+0x80`/`+0xa1` a
`disp32`, a `+0x38` a `disp8` alakban):

| mező | írás a `.text`-ben | ebből a leíró-modulban |
|---|---|---|
| `+0x38` (bájt) | 78 | **1** — `0x008f694c`, a ktor |
| `+0x80` (bájt) | 40 | **1** — `0x008f694f`, a ktor |
| `+0xa1` (bájt) | 51 | **1** — `0x008f696d`, a ktor |

### 3. ⚠️ A feszültség, kimondva

Ha a fenti térkép teljes volna, akkor a `<sliders>`-szel rendelkező
`unsharp2` is előléptetést kapna: a csúszka-adat mérve a leíró `+0x30`/`+0x34`
mezőibe megy (`0x008ffe1a`, `0x008ffe1d`), a `<slider>` darabszámát pedig az
ELEMZŐ objektum `+0x30` mezője gyűjti (`0x008ffcba` nullázás, `0x008ffce2`
növelés) — egyik sem a négy vizsgált mező. Az `unsharp2` csempéjén viszont
**nincs** jelvény (mérve a felvételen).

⇒ **legalább egy beállító hiányzik a térképemből**: a négy mező valamelyikét
egy segédfüggvényen keresztül, közvetett úton kell megkapnia a leírónak. A
közvetlen írásokra futtatott pásztázás ezt szerkezetileg nem látja.

**Amit ez NEM érint:** magát az előléptetési szabályt. Az közvetlenül az
utasításfolyamból van kiolvasva (`0x00900180`–`0x009001a9`), és a 24/24-es
kontroll nulla eltéréssel igazolta. A hiány a mezők NEVÉT érinti, nem a
szabály érvényességét.

**A következő lépés:** a `</slider>` / `</sliders>` záró-kezelőkből
(`0x00900215`, `0x0090027e`, `0x009002d7`, `0x00900330`, `0x00900389` — a
záró-diszpécser lánca) kiindulva a HÍVOTT segédfüggvényekben kell keresni a
négy mező írását, nem a hívóban.

*Bizonyítottsági fok: **megerősített** az 1–2. szakasz (utasításszintű olvasás,
kimerítő bájtszintű pásztázás a teljes `.text`-en); a 3. szakasz **nyitott**, a
hiány szerkezeti oka és a megszerzés útja megnevezve.*

## ✅ A négy döntő mező MEGVAN — bitmaszkok, és a pásztázásaim vakfoltja (2026-09-09, 237. kör)

A 236. kör kimondott feszültsége (az `unsharp2` a térképem szerint
előléptetődne, pedig nincs rajta jelvény) **feloldva**. Az ok módszertani volt:
a mezőket **`or`**-ral írja a program, nem `mov`-val, és a pásztázásaim csak
mozgató utasításokat kerestek.

### 1. A négy mező — mind a négy megnevezve

| mező | mi ez | az író |
|---|---|---|
| `+0x38` | a **csúszkák bitmaszkja**: `1 << <slider id>` | `0x008ffdcb` `or byte ptr [leíró+0x38], dl` (a `dl = 1 << [ctx+0x34]`), és `0x008ffdd8` `or …, 0x80` (a 7. bit egy további csúszka-tulajdonságra); harmadik író: `0x009007b0` |
| `+0x80` | a **színkerék** (`colorcircle`) bitmaszkja: `1 << id` | `0x008ffc29` `or byte ptr [leíró+0x80], al` |
| `+0xa1` | egy harmadik vezérlő-család bitmaszkja: `1 << n` | `0x00900c55` `or byte ptr [leíró+0xa1], dl` |
| `+0x84` | az `<effect>`-ben talált vezérlők **darabszáma** | `0x00900e1a` (`FUN_00900540`, a `filter_%s_label%d` / `_sldrRadius` sztringekkel azonosítva); a `colorwheel`-kezelő 2-nél megáll (`0x008ffb32`) |

A csúszka-bitmaszk előállítása utasításszinten:

```
0x008ffdc1  mov ecx, [ctx + 0x34]     ; a csúszka ID-je (az `id` attribútumból)
0x008ffdc4  mov esi, [ctx + 0x2c]     ; a LEÍRÓ
0x008ffdc7  mov dl, 1
0x008ffdc9  shl dl, cl                ; 1 << id
0x008ffdcb  or  byte ptr [esi + 0x38], dl
```

### 2. Ezzel az előléptetési szabály emberi nyelven

> Egy `mode="effect"` szűrő futásidőben `oneclick`-ké válik, ha **semmi
> állítható nincs rajta**: nincs csúszkája (`+0x38` = 0), nincs színkereke
> (`+0x80` = 0), nincs a harmadik vezérlő-családból (`+0xa1` = 0), és az
> `<effect>` törzse sem hozott vezérlőt (`+0x84` = 0).

Az `unsharp2` egy csúszkát deklarál ⇒ `+0x38` 0. bitje áll ⇒ **nem** léptetődik
elő ⇒ nincs rajta jelvény. Ez pontosan egyezik a felvétellel (a csempe jobb
alsó sarkában **0** kékes képpont, szemben a szépia-csempe 114-ével).

⇒ A 236. kör 3. szakaszának feszültsége **megszűnt**; a mezőtérkép zárt.

### 3. ⛔ MÓDSZERTANI TANULSÁG — a „ki írja ezt a mezőt" pásztázás

Három egymást követő kör pásztázása hibázott ugyanabban: csak **mozgató**
utasításokat keresett (`mov`, `88/89/C6/C7`). A valódi írók
**olvas-módosít-ír** alakúak voltak:

- `or  r/m8, r8` (`08 /r`) — ez írja a `+0x38`, `+0x80`, `+0xa1` maszkokat;
- `or  r/m8, imm8` (`80 /1 ib`) — a `0x008ffdd8`.

Ezenfelül a 236. kör egy másik alakot is kihagyott: a **SIB-címzésű, indexelt**
írásokat (`mov byte ptr [eax + ecx + 0x7c], 1`, `0x008ffdf6`) — ezek töltik a
leíró csúszkánkénti jelző-tömbjét a `+0x7c`-nél (index 0–3, `cmp ecx, 4`).

**A szabály:** egy „ki írja ezt a mezőt" kérdés pásztázása **kötelezően**
tartalmazza (a) az olvas-módosít-ír opkódokat (`or`/`and`/`add`/`xor`) és
(b) a SIB-címzésű alakokat. Enélkül a negatív eredmény („csak a konstruktor
írja") **nem bizonyíték** — és nálunk három körön át nem is volt az.

### 4. Melléklelet: a leíró csúszka-tárolása

A `</slider>` feldolgozásakor mérve: lebegőpontos mezők a `+0x4c`-nél
(`0x00900845`), csúszkánkénti bájt-jelzők a `+0x7c`-nél (`0x008ffdf6`,
`0x0090084b`; index 0–3), további lebegőpontos tömb a `+0xa4`-nél
(`0x0090085f`, `ecx*4` léptékkel). A `<slider>` `id` attribútuma a
`[ctx+0x34]`-be megy (`0x008ffd30`), és ez az index minden fenti tömbben.

*Bizonyítottsági fok: **megerősített** — utasításszintű olvasás mind a négy
íróra, és a szabály a felvételen mért jelvényekkel egyezik (24/24, ebből az
`unsharp2` ellenpróbája képpont-szinten is).*

---

## 11. A SÁV-JELZŐK TELJES LÁNCA: öt jelző, hat vtábla-rekesz, és a `fullres` VALÓDI fogyasztója (2026-09-11, 278. kör, #2924)

*A #819 („Ami NYITVA marad") bináris blokkolója. A 10. szakasz a
tag-eltolásokig jutott; ez a szakasz megnevezi mind az öt jelzőt, megtalálja
az olvasóikat, és kimondja, mit CSINÁL velük az eredeti.*

### 11.1 ⭐ Mind az ÖT jelző neve és tagja — a parser utasításszinten

A `0x008ff690`–`0x008ff891` sávban az attribútumnév-összehasonlítás és a
tagba írás párba állítható. A név a `repe cmpsb`/`0x0057f350` hasonlítás
operandusa, a tag a `[ebx+0x2c]` leíróba írt eltolás:

| attribútum | verem-rekesz | tag | típus | feldolgozás |
|---|---|---|---|---|
| `fullres` | `[esp+0x2c]` | **`+0xd8`** | dword | **`_atoi`** (`0x00bf6a1c`) — ezért van értelme az `1`/`2` megkülönböztetésnek |
| `slow` | `[esp+0x0f]` | **`+0xdc`** | byte | `setne` (jelenlét) |
| `resize` | `[esp+0x10]` | **`+0xdd`** | byte | `setne` |
| `persist` | `[esp+0x11]` | **`+0xde`** | byte | `setne` |
| `rotate` | `[esp+0x12]` | **`+0xdf`** | byte | `setne` |
| `glimmer` | `[esp+0x13]` | **— nincs tag** | — | csak a `0x008ff897` elágazást kapuzza |

⇒ A 10.1 „(3 további byte-jelző)" sora ezzel **név szerint feloldva**. A
`glimmer` **nem kerül a leíróba**, és a szállított `filterdesc.xml`-ben
egyszer sem fordul elő.

Darabszámok a szállított fájlból (`grep -o … | uniq -c`):

| jelző | darab |
|---|---|
| `fullres="1"` | 18 |
| `fullres="2"` | 1 (`FocalZoom`) |
| `slow="1"` | 13 |
| `resize="1"` | 5 |
| `persist` | 16 × `"1"`, 9 × `"0"` |
| `rotate="1"` | **1** — kizárólag a `dir_tint` |
| `glimmer` | **0** |

### 11.2 ⭐ A hat akcesszor a `CGenericFilter` vtáblájának 35–40. rekesze

A `0x008f6f90` és a `0x008f6fc0` **közvetlen hívóhelye NULLA** a teljes
`.text`-en (kontroll: a `0x008f6fc3 cmp dword [eax+0xd8], 2` megvan). Mind a
hat cím **adatként** áll, hat egymást követő dwordban (`0xcd18d8`–`0xcd18ec`)
— ez a `0xcd184c`-nál kezdődő vtábla, RTTI-neve **`.?AVCGenericFilter@@`**:

| rekesz | eltolás | cím | mit ad |
|---:|---|---|---|
| 35 | `+0x8c` | `0x008f6f90` | **`fullres == 1`** predikátum |
| 36 | `+0x90` | `0x008f6fc0` | **`fullres == 2` ÉS `[this+0xc8] != 0`** |
| 37 | `+0x94` | `0x008f6fe0` | `slow` (`+0xdc`) |
| 38 | `+0x98` | `0x008f6ff0` | `resize` (`+0xdd`) |
| 39 | `+0x9c` | `0x008f7000` | `persist` (`+0xde`) |
| 40 | `+0xa0` | `0x008f7010` | `rotate` (`+0xdf`) |

Mind a hat cím **pontosan EGYSZER** fordul elő adatként az egész fájlban ⇒
**egyetlen vtábla tartalmazza őket, felülíró leszármazott nincs.** Mindegyik
`this`-en kívül argumentum nélküli (`ret` immediate nélkül), és a leírót a
`[this+8]`-ból veszi.

### 11.3 ⛳ A `fullres` FOGYASZTÓJA — a lánc KETTÉVÁGÁSA

Három lánc-szintű lekérdező ül egymás mellett, mindhárom ugyanazon a
szerkezeten: `[lánc+0x48]` a szűrő-mutatók tömbje, `[lánc+0x4c] >> 1` a
darabszám.

| cím | mit csinál | rekesz |
|---|---|---|
| **`0x009084c0`** | **VISSZAFELÉ** járja be a láncot, és az UTOLSÓ olyan szűrő **INDEXÉT** adja vissza, amelyre a `fullres == 1` igaz; ha nincs ilyen: **`-1`** | 35 |
| `0x00908500` | előrefelé: van-e `slow` szűrő a láncban | 37 |
| `0x00908540` | előrefelé: van-e `persist` szűrő (logikai) | 39 |

A `0x009084c0`-nak **három hívója** van, mind a szerkesztő/előnézet
moduljában (`0x0069e74a`, `0x0069e931`, `0x0069f25c`), és **kettő ugyanazt
teszi az indexszel**:

```
0x0069e74a  call 0x9084c0          ; esi = az utolso fullres INDEXE
0x0069e766  cmp  esi, -1
0x0069e769  je   0x69e786          ;   nincs fullres -> egyszeru ut
0x0069e77d  lea  eax, [esi + 1]    ; ⭐ INDEX + 1
0x0069e781  call 0x907f30          ;   a lancot INNENTOL futtatja
```

```
0x0069f25c  call 0x9084c0
0x0069f261  cmp  eax, -1
0x0069f268  jne  0x69f2bb
0x0069f315  add  edi, 1            ; ⭐ ugyanaz: INDEX + 1
```

> ### ⛳ A VÁLASZ a #819 nyitott kérdésére
> Az eredeti **nem** külön előnézeti útvonalat tart fenn a `fullres`
> szűrőknek, és nem is rendereli az egész láncot teljes felbontáson.
> **Kettévágja a láncot** az utolsó `fullres` szűrőnél: az `index`-ig
> bezárólag tartó rész az egyik úton megy, a maradék **`index + 1`-től**
> külön hívással. Ha nincs `fullres` szűrő (`-1`), az egyszerű út fut.

### 11.4 A `rotate` két beolvasott olvasója — és mit mond a VALÓS korpusz

A teljes `.text`-en a `[reg+8] → [reg+0xd8…0xdf]` ujjlenyomatra **15**
találat van (kontroll: mind a **6/6** akcesszor megvan). Ebből a szűrő-modulban
a hat akcesszoron kívül **kettő** akad, és mindkettő a **`rotate`** (`+0xdf`)
olvasója:

| cím | hol | mit tesz |
|---|---|---|
| `0x008faf6f` | a paraméter-**sorosító** (`0x008fae60`-tól: `,%f` ×4 · `,%08x` · `,%d` ×2) | ha `rotate`, a végére fűzi a `[szűrő+0xc4] & 3` értéket `,%d`-vel |
| `0x008fb8c0` | a paraméter-**visszaolvasó** | ha `rotate`, egy további mezőt olvas `_atoi`-val és `& 3` |

A `fullres`-nek és a `slow`-nak **egyetlen beágyazott olvasója sincs** — azok
kizárólag a 11.3 lánc-lekérdezőin át fogynak.

⚠️ **A valós korpusz mérése:** a 859 `.picasa.ini`-ből kigyűjtött **kilenc**
`dir_tint=` sor **mind** a `%08x` színnel ér véget, záró egész mező nélkül
(pl. `dir_tint=1,0.898417,0.861160,0.250000,0.250000,ffbba6a2`). ⇒ A
`rotate`-ág ezeken a fájlokon **nem futott le**, tehát a
`filters-decoded.md` állítása — *„a `.picasa.ini` `dir_tint=` alakja irányt
nem hordoz"* — **áll**. (A `dir_tint=1,0.432422,…` alak, ami a repóban
szerepel, a SAJÁT golden-kitünk generált sora, nem Picasa-kimenet.)

### 11.5 ⛔ ÖNHELYESBÍTÉS menet közben: a `+0x90` eltolás ÖNMAGÁBAN nem azonosít

A kör első jelöltje a `0x0093e7b0` jelzőszó-építő volt: `[esi+0x74]`-ből
indul, `or ebx, 0x10`-et tesz egy `[vtbl+0x90]` hívás igaz ágán, és a
végeredmény egy ` [%u]` alakú **szöveges** címkébe megy (`0x0093e972`).
Kézenfekvőnek látszott, hogy ez a `fullres == 2` predikátum fogyasztója.

**Nem az.** Ugyanez a függvény a `+0x60`, `+0x70` és `+0x88` rekeszeket is
**argumentum nélkül** hívja, a `CGenericFilter` ezen rekeszei viszont
argumentumot várnak (`0x008fbeb0 ret 8`, `0x008f6f20 ret 4`,
`0x008f6d40 ret 4`) ⇒ a fogadó **más osztály**.

⭐ **Ebből lett a kör olcsó szűrője:** a virtuális hívóhelyeket az
**argumentumszám** választja szét. A `mov reg,[obj+N]` → `call reg` alakra
a `+0x8c`-nél 47 találat van, de csak **16** olyan, amelyik a hívásig
semmit nem push-ol; a `+0xa0`-nál 131-ből mindössze **10**. A megoldás
mindhárom lánc-lekérdezője ebben a szűk halmazban volt.

*Bizonyítottsági fok: **megerősített** — minden állítás mögött indextől
független, kontroll-pozitívval futtatott pásztázás (csúcs-RSS 87 MiB) vagy
utasításszintű olvasás áll.*

*Kérdés-mérleg (SAJÁT kérdések): **1 LEZÁRVA** (K1 — ki olvassa a jelzőket
és mit tesz velük) · 0 nyitott · 0 blokkolt · 0 hatókörön kívül · 0 „csak
nyitva".*

## ⛳ A festhető maszk: ÖT effekt, KÉT család — és a maszk nem lánc-paraméter (2026-09-12, 296. kör, #1908)

A #1908 azt kérdezte, hogy a festett maszk **foglal-e lánc-paramétert**, és
**visszatölthető-e**. A `filterdesc.xml` mindkettőre válaszol — és közben
kiderül, hogy a jegy (és a kódunk) **kettőt** ismer az **ötből**.

### Mind az öt `Mask="{_mctr.mask}"` — sorszámmal

| sor | szűrő | a kanavász |
|---:|---|---|
| 715 | **`Boost`** | `cnt:PaintEffectCanvas` |
| 1199 | **`Pixelate`** | `cnt:PaintEffectCanvas` |
| 1283 | **`ReanimatedEyeColor`** | **`eff:PaintOnEffectBase`** |
| 1348 | **`Soften`** | `cnt:PaintEffectCanvas` |
| 1360 | **`PicnikTint`** | `cnt:PaintEffectCanvas` |

⚠️ **Két különböző befoglaló elem adja a `_mctr`-t.** Ezért téveszt, aki
csak a `PaintEffectCanvas`-ra keres: a `ReanimatedEyeColor` **más** bázison
ül (`eff:PaintOnEffectBase`, ecset-paraméterekkel:
`_nBrushHardness="0.15"`, `BrushSizeAndEraserButton startValueFactor="0.03"
maximumFactor="0.2"`).

⛔ **Nálunk `PAINTABLE_MASK_OPS = {"picniktint", "reanimatedeyecolor"}`**
(`render/chain_glimmer_handlers.py:263`) — **egy tag mindkét családból, a
másik három hiányzik**. A `Boost`, a `Pixelate` és a `Soften` így **nem kap**
festhető-maszk figyelmeztetést a láncban.

### A maszk NEM lánc-paraméter — a forrásból

A `Mask` értéke minden esetben **`{_mctr.mask}`**: futásidejű
**vezérlő-objektum** hivatkozása, amit a kanavász ad. A szűrő **deklarált**
bemenetei ezzel szemben a csúszkák és a színválasztó — például a
`PicnikTint`-nél `_clrsw` (`ImageColorSwatch`) és `_sldrFade`.

⇒ a `filters=` lánc **csak a deklarált értékeket** hordozhatja; a maszknak
**nincs mezője**. Ebből következik a #1908 3. kérdésének válasza is: a
`.picasa.ini`-n keresztül a festett maszk **nem jön vissza**.

⚠️ **A hatókör kimondva:** ez azt bizonyítja, hogy az **ini-lánc** nem
hordozza. Hogy a Picasa **máshol** (pl. a `db3`-ban) tárolja-e, ezt a mérés
**nem zárja ki** — az a következő gépi lépés.

### A valódi korpusz — egyik sem fordul elő

A tulajdonos **859** `.picasa.ini`-jében (`ini-korpusz/korpusz.txt`,
5 658 `filters=` sor) **28 különböző** szűrő szerepel:

```
autocolor autolight Boost bw Cinemascope crop64 CrossProcess dir_tint
enhance fill finetune2 glow2 HDR Holga Lomo movieend moviestart radblur
redeye retouch sat sepia Sixties tilt tint unsharp2 Vignette warm
```

**`PicnikTint` és `ReanimatedEyeColor` egyszer sem.** ⚠️ Ez **összhangban
van** a fentivel, de önmagában **nem bizonyíték** — a tulajdonos egyszerűen
nem használta őket. A bizonyíték a `filterdesc.xml` szerkezete.

⭐ A `Boost` viszont **szerepel** a korpuszban — tehát egy festhető maszkos
effekt **igenis eljut az ini-be**, a maszkja nélkül.

*Forrás: `research/copy_Picasa_3_7/Picasa3/runtime/filterdesc.xml:715`,
`:1199`, `:1283`, `:1348`, `:1360`; `referencia/ini-korpusz/korpusz.txt`;
`src/picasapy/render/chain_glimmer_handlers.py:263`.*

### Nyitott kérdések mérlege (296.)

`1 nyílt · 3 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva"`

| kérdés | állapot |
|---|---|
| foglal-e a maszk lánc-paramétert | ✅ **NEM** — `{_mctr.mask}` futásidejű objektum |
| visszatölthető-e a `.picasa.ini`-ből | ✅ **NEM** — következik a fentiből |
| hány festhető maszkos effekt van | ✅ **ÖT**, két családban (a jegy kettőt mondott) |
| tárolja-e a Picasa **máshol** (db3) | ⛔ **NYITOTT** — ezt a mérés nem zárja ki |
