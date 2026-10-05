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
| `finetune` (v1) és `finetune2` (v2) hőmérséklet-tartománya | a tartomány valóban v1 `[-0,5..0,5]`, v2 `[-1..1]`; az algoritmus viszont **is eltér**: v1 `0x0090ea10`, v2 `0x0090e9d0` (#958) |
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

*(A `tint` sora a paraméter-SORRENDET mutatja, de nem valós export: a saját
golden-kitünk kézzel írt mérőfájljából való — ld. alább.)*

Szabály: **`puck` kurzoros szűrőnél a fókuszpont (x, y) megy elöl**, utána a
csúszkák `id` sorrendben, a színparaméter a végén. A `dir_tint` mért
alapértékei (0,25 / 0,25) pontosan a `filterdesc.xml` `default` értékei —
a csúszkanevek tehát ezzel a sorrenddel egyeznek.

**Színformátum:** a Picasa a színt **mindig nyolc jeggyel** írja (`%08x`),
a `tint`-et is; a régi, színkerekes effektek (`tint`, `ansel`, `dir_tint`,
`radtint`) `ff` alfával. A fenti `ffff` a saját golden-kitünk terméke, nem a
Picasáé. A parszer változó hosszú hex-színt is elfogad, de ez csak
robusztussági kényelem. Részletek: [`filters-decoded.md`](filters-decoded.md),
„A `tint` 4 hex jegyet ír — SAJÁT TESZTADAT-ARTEFAKTUM (2026-08-16)".

> ~~A `colorwheel` verziókülönbsége (v0 vs v1) magyarázza a hex-hosszt.~~
> **MEGCÁFOLVA (2026-08-15):** a `dir_tint` és a `radtint` **is
> `version="0"`**, mégis 8 jegyet ír. ~~A legvalószínűbb magyarázat prózai:
> az író **elhagyja a vezető nullákat**.~~ **MEGHALADVA (2026-08-16):** az
> író nem hagy el semmit — a binárisban egyetlen hex-darabka van (`,%08x`),
> és a valós korpusz mind a 11 `tint`/`dir_tint` sora 8 jegyes. A 4 jegyes
> `tint` a saját tesztadatunk volt.

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
- A `PicnikFocalPixelate` teljes, hétmezős alakja már szerepel a `merokit-2`
  valódi `.picasa.ini`-jében; a **mentett lánc** no-op mérését és a
  **szerkesztői élő utat** külön kell kezelni — lásd 4.1/b és a
  `filters-decoded.md` #2456-szakaszát.

### 4.1/b A paraméter-aritás SZABÁLYA és a mentett/élő út szétválása (#2456)

**A szabály:** egy Glimmer-effekt `.picasa.ini`-alakja pontosan

    <vezérlőszám> + (van puck ? 2 : 0)

értéket visz az engedélyező `1` után; a puck (x, y) elöl, utána a vezérlők a
`filterdesc.xml`-beli **deklarációs sorrendben** (a jelölők is, záró
`0`/`1`-ként — pl. `Sixties`, `PicnikGrain`).

A `PicnikFocalPixelate`-nél a leíró öt vezérlőt ad: `_sldrImpact`,
`_sldrRadius`, `_sldrHardness`, `_sldrFade` és `_chkReverse` (`:869`),
valamint egy tartós puckot.

⛔ **HELYESBÍTÉS (2026-09-22, #3315): a mentett alak NYOLCMEZŐS, és a
`Reverse` tokenje MEGVAN.** A natív lánc-ÍRÓ (`FUN_0042a800`,
`0x0042abcc` `"%s=%s;"`) a nevet a leíró `+0x14` mezőjéből veszi
(`0x008f6bc0`), az értékrészt pedig a `0x008fac40` állítja össze, kötött
sorrendben: engedélyezés (`%c`) → puck `x,y` (`,%f`) → az első három
csúszka (`,%f`) → szín(ek) → a NEGYEDIK csúszka (`,%f`, `+0x7f` jelző) →
a jelölőnégyzetek (**`,%d`**, `+0xa1` bitjei). Tehát:

    PicnikFocalPixelate=1,x,y,Impact,Radius,Hardness,Fade,Reverse;

Független visszaigazolás ugyanerre a sorrendre: `PicnikGrain=1,10.000000,0;`
(csúszka + jelölő) és `Sixties=1,100.000000,00ffffff,0;` (csúszka + szín +
jelölő).

⚠️ **Ettől a #1142 „mérten nem fut" besorolása ELAVULT:** a mért sorok
hét-, illetve ötmezősek voltak, és a `merokit-2` `.picasa.ini`-jébe **a mi
generátorunk** írta őket (`tools/golden/make_validation_kit2.py`), nem a
Picasa. A betöltő úton semmi nem zárja ki a szűrőt: a név a
`filterdesc.xml`-regiszterben van, a gyártó (`0x008f9fe0`) a közös
Glimmer-feldolgozót (`0x008f9a60`) építi rá, és a beolvasó ugyanazokkal a
jelzőkkel tölti fel a mezőket, amikkel az író kiírta. Pozitív kontroll: a
`FocalZoom` — ugyanilyen leíró jelölőnégyzet nélkül, ott a hétmezős alak a
TELJES alak, és mérten lefut. A PicasaPy ezért a #3315 óta rendereli
(`chain._apply_focal_pixelate_op`); a nyolcmezős alak golden-mérése
hátravan.

**A szerkesztői élő út külön:** a csempe-tábla (`0x00c7e5a0`) a `Pixelate`
Shift-párjaként ezt a nevet választja (`0x005d59f0`, `0x005d6e6c`–
`0x005d6ea6`), majd a közös kattintási végpontba lép (`0x006021d0` →
`0x005f8520`). A névfeloldó/alkalmazó útban nincs erre a névre szűkített
elutasítás; a descriptor `effect` módja 4 (`0x005f85a0`–`0x005f85b3`). A
következtetés **megerősített statikus bináris bizonyíték**: az élő csempe
nem halott, a mentett lánc mérése nem vihető át rá.

A pontos élő pixelkimenet és a mentés utáni újratöltés viszonya **NINCS MEG**;
a mintavételezési perem-/interpolációs részlet golden-összevetésre vár (#317).
A megvalósítási teendő külön fejlesztői jegy: **#3315**.

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
| `FocalZoom` | Impact 1–100 (50), Radius 10–min(W,H)/2 (közép), Hardness 0–100 (50), Fade 0–100 (0) — ✅ **nálunk is, a #723 2. köre óta** (a Radius képfüggő maximuma és a felezőpont-alapérték: `effect_params.py`, `max_formula="half_min_wh"` + `default_formula="tartomany_kozepe"`) |
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
| `Orton` | Bloom 0–50 (25), Brightness 0–100 (50), Fade 0–100 (0)  — ⭐ a mestergörbe középpontja a leíró szerint `128 + (Brightness − 50)·75/50`, a természetes spline-nal MÉRVE (2026-09-27, #626): a 684-es `min` ΔE 3,21 → 0,15, a `referencia/ortonish` Fényerő max/min 4,45/4,18 → 0,95/0,82; a korábbi ±96 töröttvonalhoz illesztett érték volt → #3788 |
| `PencilSketch` | Radius 1,3–5 (2), Contrast 0–200 (100), Fade 0–100 (0) |
| `Pixelate` | Impact 2–150 (20), BlendMode 0–9 (9 = Normal; a sorszám a natív módtábla indexe, ld. „A `BlendInstruction`” szakasz), Fade 0–100 (0) |
| `Polaroid` | szín Outer (#E2E2E2), Rotate −10–10 (5) |
| `QuantizePalette` | Steps 2–30 (8), Smoothing 0–100 (80), Fade 0–100 (0) |
| `ReanimatedEyeColor` | Blur 0–30 (6), Fade 0–100 (20) + ecset (festhető maszk, **ÜRESEN indul** — befestés nélkül az effekt tétlen, #688) |
| `RoundedEdges` | szín Outer (#fff), CornerRadius 0–min(W,H)/2 (min(W,H)/10) |
| `Sixties` | Rounded jelölő (be), szín Outer (#fff), Fade 0–100 (20) |
| `Soften` | Impact 0–100 (50), Fade 0–100 (50) + festhető maszk |
| `PicnikTint` | szín (#80cfff), Fade 0–100 (0) + festhető maszk |
| `TwoTone` | szín Black (#004488), szín White (#ffff00), Brightness −95–95 (0), Contrast 0–100 (20), Fade 0–100 (0) |
| `Vignette` | Blur 0–50 (35), Strength 1–2 (1,4), szín (#000), Fade 0–100 (0) |

#### A két csúszka FELIRATA — nem „Impact" és nem „Radius" (#723)

A `filterdesc.xml` az azonosítót adja (`_sldrImpact`, `_sldrRadius`), a
felirat viszont a szövegtárból jön, és MÁS:

| azonosító | szövegtár-kulcs | angol | **hivatalos magyar** |
|---|---|---|---|
| `_sldrImpact` | `ImageFilters::Zoominess` | Zoominess | **„Suhanás"** |
| `_sldrRadius` | `ImageFilters::FocalSize` | Focal Size | **„Fókuszméret"** |

*Forrás: `referencia/stringres-en-hu.tsv:1852`, `panel-feliratok-hu.tsv:1422`
és `:1430`.*

⚠️ A `Soften` `_sldrImpact`-ja ezzel szemben **„Softness"**
(`ImageFilters::Softness` / „Lágyítás") — ugyanaz az azonosító, MÁS
felirat. Az azonosítóból tehát a feliratra következtetni nem szabad; a
szövegtár dönt.


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
  ⭐ **2026-09-26 (#3520):** a natív művelet a láncot az EREDETIBŐL indítja (`be + C·(be − elm)`), az XML-es `LocalContrast` az elmosottból; ez a lenti `Contrast − 1` különbség bináris oka. Ld. `filters-decoded.md`, „`HDR` — a natív `LocalContrastImageOperation`…”.
  A `LocalContrast` effekt hasonlót bont ki explicit lépésekre:
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

##### Nálunk (#3827 óta) — a natív lánc

`src/picasapy/render/belso_ragyogas.py` (`inner_glow`):

| | eredeti (mérve) | nálunk |
|---|---|---|
| blur-sugár | **egész**: `min(255, trunc(ceil((b−1)/2)·quality + 1))`, `b` ∈ [0, 253], `quality` ∈ [1, 15] (alap 3) | ugyanez (`peremsugar`, `ragyogas_maszk`); a doboz a `0x00bc5360` paramétereivel (`nativ_blur.sugar_egyutthatok`) |
| `strength` | 8.8-as **szorzó**, `trunc(s × 256)`, a bemenet [0, 255] | ugyanez (`ragyogas_suly`) |
| `glowalpha` | holt paraméter | nem kerül a láncba; a MuseumMatte 0,7/0,6-a a `BlendAlpha` (`k′ = trunc(α·256) − 1`) |
| sugár-korlát | a **bemenet** 253, a **kimenet** 255 | ugyanez |

A régi analitikus `erf`-modell (`_box_blur_axis`), a `glow_sigma`-felezés
(#3158), az illesztett `VIGNETTE_RADIUS_FACTOR` (#317) és a levezetett
`vignette_radius` (#2159) megszűnt: a hívók a `filterdesc.xml` `xblur`-jét
adják át változatlanul. A mérés a lenti „A belső ragyogás TELJES lánca"
szakasz végén.

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

##### ⛳ A golden zajszintje képfüggő — és a Glow-család a zajszint FÖLÖTT van (2026-09-28, 385. kör, #626)

A 684-es mérőkészlet `Fade = 100`-as esetei 0,121-et adnak. Ez **nem** a
mérés zajszintje: ott a forrás kódolódik újra ugyanazokkal a JPEG-táblákkal.
Új tartalomnál a zajszint ennél nagyobb, és képfüggő. Mérni így lehet: a
saját kimenetünket 95-ös minőségű, 4:4:4-es JPEG-be kódoljuk (a Picasa
exportja 4:4:4), és önmagához hasonlítjuk.

| eset | ΔE a Picasához | zajszint (mi ↔ mi-JPEG95) | verdikt |
|---|---:|---:|---|
| `CrossProcess` alap | 0,807 | 0,723 | **zajszinten** — nincs teendő |
| `Holga` alap | 0,750 | 0,411 | fölötte |
| `Matte` alap | 0,910 | 0,157 | **fölötte** |
| `Vignette` alap | 0,585 | 0,147 | **fölötte** |
| `MuseumMatte` alap / min / max | 0,773 / 0,842 / 0,645 | 0,196 / 0,088 / 0,267 | **fölötte** |

A `CrossProcess` csatornánkénti előjeles eltérése a forrás minden
tartományában ±0,2 körüli (a kéknél legfeljebb +0,9). Az egész Multiply és
az egész átlátszóság-keverés nem változtat rajta (0,807 → 0,807).

**A Glow-család** (belső ragyogás) viszont valódi modellhibát hordoz. A fenti
kiolvasott darabokból épített emuláció nem áll össze: lekicsinyítés
`0x00bb89b0`-val, teljes téglalap-maszk, 3 doboz `⌈(b_red − 1)/2⌉`
sugárral és nullás peremmel, `(255 − A)·strength`, bilineáris vagy
Mitchell-nagyítás, source-over. Ez **Vignette 6,12 / Matte 5,61**-et ad, a
mai erf-modell 0,585 / 0,910-et. Hiányzik, milyen maszkot épít a
`0x00bcbfb0`, és hogyan nagyít vissza a rajzoló (`0x00bb8f70`,
`0x00bb91d3`–`0x00bb992d`). Kutatási jegy: **#3820** — megválaszolva a következő szakaszban.

##### ⭐ A belső ragyogás TELJES lánca a lekicsinyített ágon — emulálva 0,28 (2026-09-28, 386. kör, #3820)

*Bizonyítottsági fok: **megerősített**, utasításszinten, független újralevezetéssel (EGYEZIK) és golden-méréssel.*

A #2159 kiolvasta a darabokat (a lekicsinyítés aránya, a sugár, a 8.8-as
`strength`), de a lánc nem állt össze. Két dolog hiányzott: **mit mos el a
maszképítő**, és **milyen dobozzal**. Most megvan, és a Picasa-exporton mérve
a mai erf-modellnél jobb.

**1. A munkapuffer.** Ha a `0x00bb89b0` aránya (`f`) 1 alatt van, a rajzoló
(`0x00bb8f70`) `W' = csonk(f_x·W)`, `H' = csonk(f_y·H)` méretű pufferbe
**tömör téglalapot** fest (`0x009acb60`, `0xff0000ff`). Ez a maszk forrása,
nem a kép. A maszképítő a `f·xblur`, `f·yblur` blurt kapja.

**2. A maszk.** A `0x00bcbbd0` a forrás alfájának inverzét (`0xff − α`,
`0x00bcbcb6`) teszi egy `r_x`/`r_y`-nal kibővített 8 bites pufferbe; a perem
255 (`memset 0xff`). Tömör téglalapnál a belső rész 0, a perem 255.

**3. Az elmosás (`0x00bcc7b0`).** Tengelyenként **`quality` darab menet**
(itt 3), előbb vízszintesen (`0x00bccbd0`), utána függőlegesen (`0x00bcce20`).
A blurt előbb a méret felére vágja (`0x0049fab0` = fmin, `× 0,5`). A doboz
paramétereit a `0x00bc5360` adja a blurból (`b`):

```
n = trunc(b);  s = 6;  amíg n > 1: s −= 1, n >>= 1
v = trunc((b − 1)·2^(s−1));  a = v & (2^s − 1);  r = (v >> s) + 1;  div = 2^s + 2v
ki[x] = ( a·(be[x−r] + be[x+r]) + 2^s·Σ(be[x−r+1 … x+r−1]) ) / div      (csonkolva)
```

(`b ≥ 64`-nél: `s = a = 0`, `r = 1 − trunc(⌈b−1⌉·(−0,5))`, `div = 2r − 1`.)
A doboz **teljes szélessége a blur maga**, tört súlyú szélső képpontokkal.
A puffer szélén minden menetben **255 a pótlás**. Példa: `b = 33,33` →
33 képpontos, egyenletes doboz (`⌊Σ₃₃/33⌋`).

**4. A súly, a szín, a visszanagyítás, a keverés.** 

- a súly: `a = min(255, (M · trunc(strength · 256)) >> 8)` (`0x00bcc1f0`
  `imul`/`sar 8`, `0x00408af0` min; `0x00cf39d8` = 256,0);
- a maszképítő a lekicsinyített ágon **rögzített vörös** színt kap
  (`0xffff0000`, `0x00bb91dd`–`0x00bb91f9`), így a súly a vörös csatornába
  kerül; a valódi színt a `0x008f2500` színmátrixa teszi rá (R, G, B = a szín,
  alfa = a súly, nem előszorozva);
- a `glowalpha` **holt paraméter**: a szín alfa-bájtja `k = a = 0`-val megy be
  (`0x00bcc285`), a SIMD-ág pedig nullázza (`pslld 8`/`psrld 8`);
- a visszanagyítás `0x00bcb5e0(…, diag(w'/W, h'/H), smoothing = 1)`
  (`0x00bb9796`): nagyítás, tehát a **3-as Mitchell (B = C = 0,4)** (ld. 5/c);
- a keverés `0x008f59d0`: `ki = ⌊(G·a + S·(255 − a)) / 255⌋`, a ragyogás a
  forrás fölött.

**Mérve** (684-es készlet, ΔE a Picasa-exporthoz; az emuláció a fenti lánc):

| eset | ma (erf-modell) | **natív lánc** | zajszint (mi ↔ mi-JPEG95) |
|---|---:|---:|---:|
| `Vignette` alap (Blur 35, Strength 1,4) | 0,585 | **0,283** | 0,147 |
| `Matte` alap (Blur 40, Strength 1,2) | 0,910 | **0,286** | 0,157 |

Soronkénti profil a `Vignette` alap középső sorában (a kép bal szélétől 0, 5,
20, 50 képpontra): Picasa 77,7 / 81,7 / 104,0 / 142,7 · natív lánc 76,3 /
80,7 / 103,7 / 143,7 · ma 71,0 / 78,7 / 100,7 / 142,7.

A többi Glow-felhasználót (`Lomo`, `Holga`, `NightVision`, `MuseumMatte`)
ebben a körben nem mértük a lánccal.

**Nálunk (#3827 óta)** a `render/belso_ragyogas.py` ezt a láncot számolja,
mindkét ágon ugyanazzal a maszkkal és elmosással. A maszkot bitre ugyanúgy
kapja, mint a kibővített pufferes újralevezetés (teszt), de gyorsabban: a
vízszintes menetek után minden belső sor azonos, ezért a függőleges menetek
csak a sor különböző értékein futnak (legfeljebb 256 oszlop). A
visszanagyítás a fixpontos `ytResampler` (`resize_plane`, #3805), a keverés
`⌊…/255⌋`. Mérve (684-es készlet, ΔE a Picasa-exporthoz):

| eset | az erf-modell | **nálunk** |
|---|---:|---:|
| `Vignette` alap | 0,585 | **0,169** |
| `Matte` alap | 0,910 | **0,176** |
| `Lomo` alap / min | 0,453 / 0,442 | **0,289 / 0,280** |
| `Holga` alap / min | 0,750 / 0,500 | **0,604 / 0,253** |
| `NightVision` alap / min | 4,595 / 3,663 | **4,528 / 3,624** |
| `Comicize` alap / max / min | 2,689 / 2,328 / 2,299 | **2,687 / 2,328 / 2,294** |

A fenti 0,283/0,286-nál jobb érték a fixpontos Mitchell-nagyításból és az
egész keverésből jön (a kutatási mérés lebegőpontos nagyítással és
`rint`-tel futott). A `NightVision` és a `Comicize` maradék hibája nem a
ragyogásban ül.

##### ⭐ A teljes felbontású ág és a MuseumMatte — emulálva a zajszint közelében (2026-09-28, 387. kör, #626)

*Bizonyítottsági fok: **megerősített** a láncra (utasításszinten, független újralevezetéssel: EGYEZIK), **mért** az `imagewidth` jelentésére.*

A `MuseumMatte` ragyogása kis blurral fut: `xblur = 2·0,02·max(W,H)/4`, egy
960 × 640-es képen **9,6**. A `0x00bb89b0` ekkor 1,0-t ad (`p < 33,33`), tehát a
rajzoló a **teljes felbontású** ágon marad
(`0x00bb8ff3`–`0x00bb9013`):

- a maszképítő (`0x00bcc2e0`) a **bemeneti képet** kapja, a **valódi**
  színnel és változatlan blurral, és közvetlenül a kimenetbe ír; utána nincs
  átméretezés, színmátrix vagy további keverés (`0x00bb918b`–`0x00bb91ce`);
- a maszk, az elmosás és a súly ugyanaz, mint a lekicsinyített ágon (fent);
- fekete színnél és átlátszatlan forrásnál a kimenet
  `ki = ((256 − e) · S) >> 8`, ahol `e = min(255, (M · trunc(strength·256)) >> 8)`
  (`0x00bcbd60`; a szín-tag feketénél 0);
- a művelet `BlendAlpha`-ja utána a lánc keverője (`0x00bd0700` →
  `0x009dc4b0`): `k′ = trunc(α·256) − 1`, `ki = (be·(255 − k′) + t·k′) >> 8`,
  és az alfa 255 lesz. *(Páratlan szélességnél az utolsó oszlopot a skalár ág
  fordított súllyal keveri, `0x009dc646`–`0x009dc6fb`; a hatását nem mértük.)*

**Mérve** (684-es készlet, ΔE a Picasa-exporthoz; a két ragyogás a fenti
lánccal, a két gyűrű a mai `add_ring`-gel):

| eset | ma | **natív lánc** | zajszint (mi ↔ mi-JPEG95) |
|---|---:|---:|---:|
| `MuseumMatte` min (vastagság 0 / 0) | 0,842 | **0,128** | 0,088 |
| `MuseumMatte` alap (25 / 40) | 0,773 | **0,230** | 0,196 |
| `MuseumMatte` max (100 / 100) | 0,645 | **0,287** | 0,267 |

**Az `imagewidth` a második ragyogásnál az EREDETI kép mérete, mérve.** A
második ragyogás a belső gyűrű UTÁN fut, már a nagyobb képen. Ha a blurt
ennek a méretéből számoljuk, az alap 0,251 és a max 0,343; az eredeti méretből
0,230 és 0,287. A leíró `imagewidth`-je tehát nem a lánc aktuális képére
vonatkozik. Ezt a binárisból nem olvastuk ki, a két értelmezés közül a mérés
dönt.

⇒ A korábbi `/8`-as, illesztett sugár (`VIGNETTE_RADIUS_FACTOR`, #317) a
fenti lánccal feleslegessé vált: a blur a leíró `/4`-es képlete, változatlanul.

**Nálunk (#3827 óta)** a `glimmer_frames.apply_museum_matte` így számol, a
második ragyogás blurja is az eredeti kép méretéből. Mérve: min **0,128**,
alap **0,230**, max **0,287** (előtte 0,842 / 0,773 / 0,645). ⚠️ A teljes
felbontású ágon a nem fekete szín tagját (`e·G`) nem mértük: a
`((256 − e)·S + e·G) >> 8` alak feketére bizonyított, más színre a képlet
folytatása.

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

**Az Elhomályosítás (`blur`) sem érhető el a felületről (2026-09-22, #3485).**
A `filterdesc.xml` definiálja (`id="blur"`, `mode="effect"`, felirat *Blur*,
egy *Threshold* csúszka), de ettől még nem kap csempét. A `blur` név-sztringre
(`0x00c7fc14`) a teljes fájlban **öt** hivatkozás van (indextől független
pásztázás), és egyik sem felületi:

| hivatkozás | mi ez |
|---|---|
| `0x0040aad1` | név-visszaadó (`mov eax, "blur"; ret`), egy szűrőosztály vtáblájának eleme (`0x00c80794`) |
| `0x00bc437c` · `0x00bc4484` · `0x00bc4571` | a Glimmer-sávban (`0x00bc41e0`) egy `blur` nevű attribútum — nem a natív szűrő |
| `0x00cd07b8` | a natív szűrő-nyilvántartás 23. rekordja (`picasa-native-filter-registry.md`) |

⛳ **Pozitív kontroll:** a csempetáblák sávjában (`0x00c7e400`–`0x00c7e800`)
ugyanez a pásztázás megtalálja a csempés effektek nevét — `sepia`
(`0x00c7e5ac`), `bw` (`0x00c7e5b8`), `warm` (`0x00c7e5c4`), a Shifttel
elérhető `radtint` (`0x00c7e628`), `Soften` (`0x00c7e6cc`), `Vignette`
(`0x00c7e6d8`); a `blur`-ét nem. A szerkesztőpanel belépési pontjának
(`0x006021d0`) statikus nevei között sincs (fent). UTF-16-os `blur` sztring
nincs a fájlban.

⇒ **LEZÁRVA: az eredeti Picasában az Elhomályosításnak nincs menüje,
csempéje és gombja** — csak egy betöltött szerkesztési láncból (`filters=` a
`.picasa.ini`-ben) fut le. Nálunk a
„Régi effektek” fülön szürkén áll (`chain.UI_INERT_RANGE_OPS`), ami ennek
megfelel: a felületről ott sem alkalmazható.

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
| `HSVGradientMapImageOperation` | 1 | `gradientObjectArray` (`color.h/s/v`; `position`: float32 LUT-koordináta 0…255, tört érték megengedett) · `hueOffset` |
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
2. A **`finetune` v1 → v2 kétszeres átszámítás nem létezik**. A tartományok
   valóban kétszeresek, de a #958 célzott disassembly-je szerint a v1 a
   középtónus-parabolás `0x0090ea10`, a v2 a feketetest-táblás
   `0x0090e9d0` workert futtatja. A v1 pontos képlete és golden-kontrollja a
   `filters-decoded.md` „`finetune` v1 színága" szakaszában áll.
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

##### Mért LUT és pixelalkalmazás (2026-10-04, #626)

*Bizonyítottsági fok: **megerősített** a lent megnevezett négy görbekonfiguráció
LUT-jára és a Fade előtti pixelkimenetére. Az utasításszintű binárislelet és a
natív QEMU-futtatás egyezik. Az eredeti XML-parser útja és a teljes
effektcsővezeték bájtszintű ellenőrzése **NINCS MEG**.*

**Bináris út.** A művelet négy görbeleírója a `this+0x40`, `+0x44`, `+0x48`,
`+0x4c` helyeken van; a leírók feldolgozását a `0x00bb9d20` → `0x00bb9e00`
lánc végzi. A természetes köbös spline LUT-építője `0x00bcd1e0`, a mester
kiértékelője `0x00bcd360`: a mester eredménye float32-ként jut a csatornagörbékhez,
azok eredményére `0,5` kerül, majd csonkolás és 0…255 közötti korlátozás. Az
effekt az `0x00bb7c80` alkalmazón át jut a `0x00bcb2f0` BGRA-pixelciklushoz.

**Natív futtatás.** QEMU-wrapperrel, a `filterdesc.xml` pontos pontjaiból
közvetlenül felépített műveletekkel négy konfigurációt futtattam: CrossProcess,
Sixties, Orton@50 és Orton@25. A tesztkép 5 sor magas volt; szélessége 8 vagy 9
képpont, a Fade értéke 0 vagy 50. A szintetikus forrás RGB-je:
`R=(13x+17y)&255`, `G=(11x+5y)&255`, `B=(7x+3y)&255`; az alfa 255. Így összesen
4 × 2 × 2 = 16 futás készült.

| konfiguráció | natív ↔ jelenlegi RGB-LUT eltérés | Fade előtti képkimenet | 9×5, Fade 50: eltérő RGB-bájt |
|---|---:|---:|---:|
| CrossProcess | 0/768 | 0 bájt | 6/135, legfeljebb 1 szint |
| Sixties | 0/768 | 0 bájt | 4/135, legfeljebb 1 szint |
| Orton@50 | 0/768 | 0 bájt | 15/135, legfeljebb 1 szint |
| Orton@25 | 0/768 | 0 bájt | 1/135, legfeljebb 1 szint |

A Fade 50-es, páratlan szélességű eltérések kizárólag az utolsó oszlopban,
a sorvégi keverőágban vannak; a görbe LUT-ja és Fade előtti képe ezekben az
esetekben is bájtra egyezik. A keverőút súlyozási lépései a `0x00bd0700` és
`0x009dc4b0` címeken követhetők. A sorvégi különbség az ismert, #4157-ben
javított Fade-ág tárgya, nem új `AdjustCurves`-eltérés.

**Két független út:** (A) az utasításszintű híváslánc és lebegőpontos/kerekítési
műveletek a görbetagoktól a LUT-on át a pixelalkalmazóig; (B) a natív QEMU
LUT-építő és pixelalkalmazó, összevetve a jelenlegi kimenettel. A négy
konfiguráció LUT- és Fade előtti képpont-eredménye egyezik.

**Cáfoló próbák.** A spline-leletet lineáris interpolációval próbáltam
cáfolni, ugyanazokon az XML-pontokon és a 256 LUT-bemeneten: CrossProcess
424/768 (max. 18), Sixties 695/768 (max. 16), Orton@25 723/768 (max. 8)
RGB-értékkel tért el a natív táblától. Orton@50 identitásgörbéje önmagában nem
különbözteti meg a módszereket. A mester köztes eredményének előzetes
kerekítése/klippelése Sixties esetén 185/768 (max. 24), Orton@25 esetén 3/768
(max. 1) eltérést adott. Az ellenpróbák is a natív LUT-tal, azonos pontokkal
és azonos RGB-összehasonlítással készültek.

**Korlát és nyitott kérdés.** A QEMU-wrapper a művelet görbepont-struktúráit a
XML pontos értékeiből közvetlenül építette fel; nem futtatta a `filterdesc.xml`
parserét és a teljes effektláncot. A parser által előállított műveletet és az
eredeti lánc teljes kimenetét azonos képen QEMU alatt összevetni **NINCS MEG**.
Ehhez a QEMU-futtatást az eredeti parseres műveletfelépítésen és a teljes
effektláncon kell végigvezetni. A mért görbematematikához új fejlesztői javítás
nem indokolt; az eltérő Fade-ágat a #4157 kezeli.

#### ⛔ A `SimpleColorMatrix` KÉPPONTRA ható sorrendje FORDÍTOTT: színárnyalat → fényerő → kontraszt → telítettség (2026-09-27, 374. kör, #626)

*Forrás: a mag `0x00bb6400` · a szorzó `0x008f28d0` · a fényerő-építő `0x008f1af0` · a kontraszt-építő `0x008f1bd0` · az alkalmazó `0x008f2640` · golden: `684-merokeszlet`.*

Az alábbi (régebbi) blokk az **építési** sorrendet írja: telítettség, kontraszt, fényerő, majd az ötödik lépés (`0x008f1e70`, színárnyalat-forgatás: a paraméter `[−180, 180]`-ra vágva, fokból radiánba, sin/cos). A képpontra ható sorrend ennek a **fordítottja**:
- a szorzó a gyűjtőt **jobbról** szorozza az új részmátrixszal: `G ← G × Ú` (a gyűjtő az `eax`, az új az `ecx`; `0x008f1b40`/`0x008f1b47`; eredmény vissza a gyűjtő sorába);
- a kész mátrix **oszlopvektort** szoroz: `out = M · [R, G, B, A, 1]ᵀ`. A sor a kimeneti csatorna, a 4. oszlop az eltolás. A fényerő a `M[0..2][4]`-be kerül (`0x008f1ba0`–`0x008f1ba8`), az alkalmazó `out_R = M[0][0]·R + … + M[0][4]`.

⇒ `M = S · C · B · X`, tehát a képpontra **előbb X (színárnyalat), aztán B (fényerő), aztán C (kontraszt), végül S (telítettség)** hat. Összekapcsolás nélkül, színárnyalat és telítettség nélkül csatornánként:

```
out = k·(x + b) + (1 − k)·63,5        (vágás 0..255-re csak a végén, egyszer)
```

**Mérve** (a Picasa exportjai, `analyze_validation_kit.py`, átlagos ΔE a Picasához; „fordított” = képpontra fényerő → kontraszt → telítettség):

| effekt · eset | a mai (kontraszt → fényerő, a telítettség elöl) | **fordított** |
|---|---:|---:|
| `Boost` max (100) | 13,071 (ROSSZ, #3516) | **0,095** |
| `Boost` alap (50) | 2,686 | **0,143** |
| `Lomo` alap / min | 1,046 / 1,021 | **0,453 / 0,442** |
| `CrossProcess` alap | 0,883 | **0,807** |
| `NightVision` min (−50 / −50) | 10,813 | **5,436** |
| `NightVision` alap (0 / 0) | 11,696 | 11,696 (nincs mátrixlépés) |

Független ellenőrzés az exportokból: a `NightVision` `min` és `alap` exportja (azonos forrásból) elmosva csatornánként `min ≈ 0,50·alap + 6,7`. A fenti képlet `k = 0,5`, `b = −50` mellett `0,5·x + 6,75`-öt ad; a fordított sorrend `0,5·x − 18,25`-öt adna.

A `NightVision` maradék eltérése a **zaj mintázata**: elmosott képeken az `alap` eltérése csak 1,67, a zaj szórása egyezik (G 28,8 ↔ 27,5), a képpontonkénti véletlenmintázat nem. Ez külön kérdés.

*Bizonyítottsági fok: **megerősített**, utasításszinten, független újralevezetéssel (EGYEZIK) és a golden-méréssel.* Feltételes: a gyűjtő kezdőértéke felhasználói mátrix nélkül identitás (a `0x00c7d620` identitás-tábla, a `0xbc1860` csak `[this+0x24] ≠ 0` esetén ír). Balról állna, tehát a sorrendet nem befolyásolja.


#### ⛳ A `SimpleColorMatrix` és a `Tint` szürkítése is a FIXPONTOS alkalmazón fut — a lebegőpontos modell a Neon, a Lomo és a Holga maradéka (2026-09-29, 408. kör, #3950)

*Bizonyítottsági fok: **megerősített**, utasításszinten (a közös alkalmazó a #3930-ban kiolvasva), és a Picasa-exporttal a Neonon bitre egyezik. Független újralevezetés (#3950): EGYEZIK, ugyanazokkal a képpontértékekkel.*

A `SimpleColorMatrix` (és a `Tint` első lépése, a `ColorMatrix(s = −100)`) a kész lebegőpontos mátrixot (a fenti `M = S · C · B · X`) ugyanazon a közös alkalmazón futtatja, mint a `BW` (`0x00bc16b0` → `0x008f2500`; ld. „⛳ A színmátrix-alkalmazó fixpontos aritmetikája”, #3930):

```
c_ij = trunc(M_ij · 2048 ± 0,5)          b_i = trunc(eltolás_i · 4 ± 0,5) + 2     ; 0x008f21a0
ki_i = clamp( ( Σ_j ((c_ij · x_j) >> 9) + b_i ) >> 2 , 0, 255)                   ; 0x008f2640
```

**Példa — `Contrast = 50`** (az `EdgeDetectionB` előkészítő lépése a Neonban, `100 − detail`): `k = 2,0`, eltolás `(1 − k)·63,5 = −63,5`, tehát `c = 4096`, `b = −252`, `ki = (8x − 252) >> 2 = clamp(2x − 63)` (a kontraszt-tábla `T[50] = 1,0`, `0x00c7d688`; `f = (1·127 + 127)/127 = 2,0`, `0x008f2990`):

| `x` | 0 | 32 | 63 | 64 | 100 | 128 | 200 | 255 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| fixpontos | 0 | 1 | 63 | 65 | 137 | 193 | 255 | 255 |
| a mai kód (`rint(2x − 63,5)`) | 0 | 0 | 62 | 64 | 136 | 192 | 255 | 255 |

**A `Tint` szürkítése** Haeberli-súlyokkal: `c = 632 / 1248 / 168`, `b = 2` — a `Resaturate`-tábla indexe ez, nem a lebegőpontos `rint`.

**Mérve** (684-es mérőkészlet, a mi kimenetünket a Picasa-export saját kvantálótábláival tömörítve; minden golden-pár lefutott, csak a változók, romlás nincs):

| eset | a mai kód (lebegőpontos mátrix) | **fixpontos alkalmazó** |
|---|---:|---:|
| `neon__alap` | 0,280 | **0,000** |
| `lomo__alap` / `lomo__min` | 0,198 / 0,184 | 0,063 / 0,033 |
| `boost__alap` | 0,059 | 0,000 |
| `holga__alap` / `holga__min` | 0,060 / 0,034 | 0,010 / 0,003 |
| `crossprocess__alap` | 0,225 | **0,000** |
| `cinemascope__alap` | 0,354 | 0,307; a görbe-lánccal (#3941/#3942) együtt **0,000** |
| `picniktint__alap` | 0,019 | 0,000 |

*Kiegészítés (409. kör): az első felmérés foltozása a `glimmer_tone` modult nem érte el, ezért az Áttűnés (`CrossProcess`) kimaradt; minden modulban foltozva a táblázat többi sora változatlan, az Áttűnés bitre egyezik. A Lomo maradéka (0,063 / 0,033) mindhárom kiolvasott javítás mellett is megmarad — ez a lánc egy másik lépéséből jön.*

A Neonon a két lépés külön is mérve: csak a fixpontos kontraszt 0,280 → 0,016, a `Tint` fixpontos szürkítésével együtt 0,000.

**A mátrix-összefűzés pontossága:** a szorzó (`0x008f28d0`) x87-FPU-n megy, `G ← G × Ú`, az összegzés `l = 0…3` sorrendben, a gyűjtő kezdőértéke `0,0` (`[0xcf3a60]`), és minden részösszeg float32-be tárolódik (`fstp dword`): egy elem `acc = 0; l = 0…3: acc = f32(f64(acc) + f64(G[i,l])·f64(Ú[l,j]))`; ezért az eltolás nem `k·b + t` (az csak `S` soronkénti összege = 1 esetén pontos): `s = −100, c = −25, b = −75` → −40,374996 (`b = −159`), linked `s = −100, c = −100, b = −65` → `b = 180`.

**Nálunk:** `render/glimmer_ops.py::simple_color_matrix` (lebegőpontos, `to_uint8`) és `tint_luma_preserving` (`rint` Haeberli) → fejlesztés: #3951.

✅ **Megvalósítva (#3951):** a `simple_color_matrix`, a `tint_luma_preserving` és a `bw_tint` közös fixpontos alkalmazón fut (`glimmer_ops._fixpontos_szinmatrix`; `c = trunc(m·2048 ± 0,5)`, `b = trunc(eltolás·4 ± 0,5) + 2`, tagonként `>> 9`, összeg + `b`, `>> 2`, vágás). A telítettség-, kontraszt- és fényerő-mátrix a natív módján (`_szorzas_x87`, `M = S · C · B`, float32 részösszegek) szorzódik össze. Mérve (684-es mérőkészlet, a Picasa-export kvantálótábláival és mintavételezésével tömörítve, CIE76): `neon__alap` 0,280 → **0,000**; `lomo__alap` / `lomo__min` 0,198 / 0,184 → 0,063 / 0,033; `boost__alap` 0,059 → 0,000; `holga__alap` / `holga__min` 0,060 / 0,034 → 0,010 / 0,003; `crossprocess__alap` 0,225 → 0,000; `cinemascope__alap` 0,079 → 0,000 (a #3942 görbe-lánccal a mai mainen); `picniktint__alap` 0,019 → 0,000. Egyik golden-pár ΔE-je sem romlott.

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
k = kontraszt_szorzo(c);            // 0x008f2990 — a KÉSZ szorzót (k) adja, nem a görbét
if (abs(bits(k) - bits(1.0f)) < 8) return;   // 0x008f1c3b–0x008f1c4d: nincs teendő
t = (1.0f - k) * 127.0f * 0.5f;     // = (1-k) * 63.5
R' = k*R + t;  G' = k*G + t;  B' = k*B + t;
```

ahol a szorzó függvénye (a `0x008f2990` a KÉSZ szorzót adja vissza, nem a görbeértéket):

```c
// 0x008f2990
float kontraszt_szorzo(float c) {
    c = clamp(c, -100, 100);                          // 0x008f299c–0x008f29e1
    if (c == 0) return 1.0f;                          // 0x008f29f4 (fld1)
    double curve;
    if (c < 0) curve = c / 100.0;                     // double, NEM kerekül float32-re (0x008f2a05–0x008f2a09)
    else {
        float f = (float)(c - floor(c));              // 0x008f2a23–0x008f2a2b
        int   i = (int)c;                             // csonkítás, 0x008f2a32 (_ftol2_sse)
        if (abs(bits(f) - bits(0.0f)) < 8)            // 0x008f2a43–0x008f2a57: gyakorlatilag f == 0
            curve = T[i];
        else
            curve = (float)((1-f)*T[i] + f*T[i+1]);   // float32-re kerekítve, 0x008f2a7e
    }
    float szamlalo = (float)(curve*127.0 + 127.0);    // 0x008f2a92 (127,0 = [0x00cf3a28])
    return (float)(szamlalo / 127.0);                 // 0x008f2a96–0x008f2a9a
}
```

A `T[]` tábla a `0x00c7d688` címen (fájloffszet `0x87d688`), **101 darab
`float`**, 0,0-tól 10,0-ig, **kézzel hangolt, szakaszonként más lépésközzel**:

| csúszka | 0 | 10 | 20 | 30 | 40 | 50 | 60 | 70 | 80 | 90 | 100 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `T` | 0,00 | 0,12 | 0,25 | 0,44 | 0,71 | 1,00 | 1,60 | 2,37 | 4,00 | 7,30 | 10,00 |

A lépésköz szakaszonként változik; a natív motor a táblát olvassa, ezért a
megvalósításnak a táblapontokat kell átvennie, nem közelítő görbét illesztenie.
Teljes lista: `referencia/kontraszt-tabla.csv` (privát repó); a nyers bináris
értékek és a lekérdezés pontos szabálya az alábbi kiegészítésben szerepel.

#### ⭐ A kontraszttábla teljes tartalma és pontos lekérdezése (#626, 2026-10-02)

**A bináris adata.** A `0x008f2990` a 101 darab IEEE-754 `float32` elemet a
`0x00c7d688` címen olvassa (RVA `0x0087d688`, fájloffset `0x87d688`). Az alábbi
értékek az egyes float32 értékek legrövidebb, pontosan visszaalakítható decimális
alakjai; az index a `Contrast` egész része:

```text
  0–  9: 0, 0.01, 0.02, 0.04, 0.05, 0.06, 0.07, 0.08, 0.1, 0.11
 10– 19: 0.12, 0.14, 0.15, 0.16, 0.17, 0.18, 0.2, 0.21, 0.22, 0.24
 20– 29: 0.25, 0.27, 0.28, 0.3, 0.32, 0.34, 0.36, 0.38, 0.4, 0.42
 30– 39: 0.44, 0.46, 0.48, 0.5, 0.53, 0.56, 0.59, 0.62, 0.65, 0.68
 40– 49: 0.71, 0.74, 0.77, 0.8, 0.83, 0.86, 0.89, 0.92, 0.95, 0.98
 50– 59: 1, 1.06, 1.12, 1.18, 1.24, 1.3, 1.36, 1.42, 1.48, 1.54
 60– 69: 1.6, 1.66, 1.72, 1.78, 1.84, 1.9, 1.96, 2, 2.12, 2.25
 70– 79: 2.37, 2.5, 2.62, 2.75, 2.87, 3, 3.2, 3.4, 3.6, 3.8
 80– 89: 4, 4.3, 4.7, 4.9, 5, 5.5, 6, 6.5, 6.8, 7
 90– 99: 7.3, 7.5, 7.8, 8, 8.4, 8.7, 9, 9.4, 9.6, 9.8
100–100: 10
```

**A natív lekérdezés** (`0x008f2990`): a bemenet vágása `−100…100` (a hívó, a
`0x008f1bd0` is vág). Nullánál a függvény rögtön `k = 1,0`-t ad (`fld1`); negatív
`c`-nél `curve = c/100` (double, nem kerekül float32-re); pozitív `c`-nél
`i = floor(c)` (csonkítással, `_ftol2_sse`) és `f = c − floor(c)` (float32-ként a
`[esp+0x34]`-en).

A bitminta-összehasonlítás NEM `c`-t és `float32(i)`-t vet össze, hanem a tört részt
(`f`) a `0,0f`-fel (`fldz` → `fstp dword [esp+0x38]` → `sub eax, [esp+0x38]`,
`0x008f2a43`–`0x008f2a4b`). Ha `abs(bits(f)) < 8` (`cmp eax, 8` / `jae` a
`0x008f2a54`–`0x008f2a57`-nél), vagyis gyakorlatilag `f = 0`, akkor `curve = T[i]`,
különben `curve = (1−f)·T[i] + f·T[i+1]`. A kapu kimenetileg közömbös: `f = 0`-nál
az interpoláció is `T[i]`-t adna, csak a szorzást spórolja meg. (A valódi, 8 bitmintás
összehasonlítás idiómája az építőben van: `abs(bits(k) − bits(1.0f)) < 8`,
`0x008f1c3b`–`0x008f1c4d`.)

A függvény már `k`-t ad vissza. A számláló (`curve·127 + 127`, x87) a `0x008f2a92`-nél
float32-re kerekül, a `0x008f2a96` osztja 127,0-val (`0x00cf3a28`), a `0x008f2a9a`
float32-ként tárolja. A pozitív ágon a `curve` is float32-re kerekül (`0x008f2a7e`),
a negatívon nem. Algebrailag `k = 1 + curve`, de a float32-kerekítések miatt egész
`c`-n 19/100 pontban 1 ULP-val tér el a `float32(1 + T[i])`-től (pl. `T = 0,05` esetén
a natív `k` 1,0500000715, a sima 1,0499999523). Nincs további vágás, kerekítés vagy
előzetes átalakítás a függvényben.

**A lánc a pixelekig.** A `SimpleColorMatrix` objektum vtáblájának (`0x00ceffb4`)
6. slotja a `0x00bc16b0` (közös a `ColorMatrix` és a `MultiplyColorMatrix` vtábláival),
amely a virtuális 8. slotot hívja (`0x00bb6400`: az építő; a `Contrast` ágban
`0x008f1bd0` → `0x008f2990`, a `ContrastAndBrightnessLinked` jelzőnél `0x008f2040` →
`0x008f2990`). Utána `0x008f2500` → `0x008f21a0` (Q11 int16 mátrix, ×2048) → soronként
`0x008f2640` (a fixpontos képpont-alkalmazó: `movsx word × byte`, `sar 9`, eltolás,
`sar 2`, vágás 0…255).

**Független mérési ellenőrzés.** A helyi `684-merokeszlet` Boost-alap és
Boost-max exportján a natív értelmezéssel (`k = 1 + T`) újraszámolt kimenet
ΔE-je (CIE76, átlag) **0,145** és **0,095**; az alternatív `k = T` értelmezés
ugyanezeken **22,657** és **1,328**. A ΔE a TELJES Boost-láncra vonatkozik
(Brightness −20/−40 és Saturation +20/+40 mellett `Contrast = 40/80`), két egész
táblapontot igazol (`T[40] = 0,71`, `T[80] = 4,0`); ugyanez az eset a specben már
korábban 0,143 / 0,095 értékkel szerepelt (a 0,145 ugyanennek az újraszámolása, nem
új, független bizonyíték). A 101 táblapont forrása a bináris, nem a két mérési pontból
való illesztés. A tábla meglévő privát CSV-jében a 101 elem mindegyike 6 tizedesre
kerekítve egyezik a bináris float32 értékével.

**Futtatásos ellenőrzés (az eredeti gépi kód).** A `Picasa3.exe` `.text`, `.rdata` és
`.data` szakaszait az eredeti VA-kon térképező kis ELF-ből, `qemu-i386` alatt hívva a
`0x008f2990`-et (FPU vezérlőszó `0x027f`; az SSE2-jelzőket `[0xda1424]`/`[0xda1428]`
1-re állítva; az x87 tartalék ágat nem futtattuk) a natív kimenet 7168 bemeneten
(egészek −105…105, 1–9 ULP az egészek fölött és alatt, rács, 3000 véletlen, denormálisok)
bitre egyezik a fenti pszeudokóddal. A korábbi, `c` és `float32(i)` bitmintáját
összevető kapu 597/7168 bemeneten más kimenetet adna.

*Bizonyítottsági fok: **megerősített**. A út — a `0x008f2990` utasításszintű olvasása
(a tábla, a vágás, a negatív ág, a floor, az interpoláció, a `k`-számítás sorrendje és
konstansai); B út — az eredeti gépi kód futtatása 7168 bemeneten, bitre egyező
modellel, valamint a tábla nyers bájtjai (101 elem, a spec decimális listájával 0
eltérés) és két valódi Picasa-export (Boost-alap/-max) a helyes és a cáfoló
szorzóértelmezéssel. **Nem mért:** tört `Contrast` értékű valódi Picasa-export — a
natív függvény viselkedése tört értékre is bitre ismert, de ezt Picasa-golden nem
ellenőrzi.*

#### Együttes fényerő + kontraszt (`0x008f2040`) — a `ContrastAndBrightnessLinked` ág

```c
k = kontraszt_szorzo(kontraszt);                 // 0x008f2990 — ugyanaz a függvény és tábla
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
> `127.5 - k*127.5` szerepel, tehát nem fordítási artefaktum.

**Kompozit golden-kontroll (nem izolált mátrixmérés):** a szállított
`TwoTone`-minta (`effekt4_12_kettonusu_alap.jpg`, paraméter:
`TwoTone=1,0.000000,20.000000,0.000000,00004488,00ffff00;`) és a natív
export összevethető. Azonos `1200×1600×3` méreten a PicasaPy teljes
`apply_twotone` csővezetéke **22,4231 MAE**-t ad a natív exporthoz, míg az
érintetlen forrás–natív eltérés **59,5135 MAE**. Ez pozitív kontroll a teljes
TwoTone-útra, de nem választja le a linked mátrix hibáját a luma-/gradient-
és JPEG-hatástól; pixelazonosságot ebből nem állítok.

#### A natív golden csatorna-kontrollja — erős, de mintához kötött lelet

Ugyanezen a páron a natív kimenetet visszavetítettem a deklarált két szín
egyenesére (`#004488` → `#FFFF00`). Az így kapott 0…1 színkoordináta a bemenet
**első RGB-csatornáját** követi: a közvetlen, vörös-csatornából számolt kimeneti
kontroll MAE-je **6,3644** szint, csatornánként `[8,3348; 6,1246; 4,6337]`,
a korreláció **0,9950**. Az érintetlen forrás és a natív export eltérése
ugyanott **59,5135 MAE**.

Ez a kontroll kizárja, hogy a korábbi `22,4231`-es eltérés egyszerűen csak a
forrás változatlansága legyen, és jelzi, hogy a PicasaPy jelenlegi
`glimmer_tone.py:348–355`-ös Rec.601-luma-útja **nem tekinthető bizonyítottan
azonosnak** a natív csatornaútjával. Nem általánosítom a vörös-csatornás
olvasatot minden képre: a döntő nyitott rész a natív mátrix belső byte-/mátrix-
rendezése.

#### Bináris horgony a következő lépéshez

- A `filterdesc.xml:1377–1378` szerint a `TwoTone` előbb a
  `SimpleColorMatrix(ContrastAndBrightnessLinked=true, Saturation=0,
  Brightness, Contrast)` ágat, utána a `TwoToneImageOperation`-t futtatja.
- A linked mátrix-építő `0x008f2040` a `k`/`t` értékeket a közös mátrixépítőnek
  adja; a színmátrix-alkalmazó `0x00bc16b0` a `0x008f2640` byte-szintű
  alkalmazóba fut.
- A közös LUT-út `0x00bb7c80` → `0x00bcb2f0` a négy pixelbyte-ot külön LUT-
  rekeszekből (`+0x000`, `+0x400`, `+0x800`, `+0xc00`) olvassa, telítetten
  összeadja, majd ugyanazon byte-helyekre írja vissza (`0x00bcb3a0`–
  `0x00bcb4ba`). A `TwoTone` LUT-ját `0x00bb87b0` építi, a két megálló
  leképezését `0x00bb85b0` végzi.

**Következő bizonyító lépés — MEGVAN, a mátrix-alkalmazó nem csatornacserés.**

A `0x008f2640` (644 b, `void apply(coeffs* eax, pixel* ecx, int count edx, pixel* dst[ebp+0x10])`)
teljes diszasszemblátuma kiolvasva (`/tmp/picasapy-research-venv` capstone-nal,
fájloffszet `0x4f2640`). Fixpontos **Q9** szorzó-összeadó: minden `coeffs*eax`
szó (int16) `src_byte` értékkel szorozva `>>9`, a négy tag összeadva, `+bias`
(dword), végül `>>2` (⇒ teljes skálázás `/2048`), és `[0,255]`-re vágva.

**Az oszlop↔bájt leképezés MÉRVE, mind a négy kimeneti sorra azonos:**

| mátrix-oszlop (byte-eltolás a soron belül) | szorzott forrás-bájt |
|---|---|
| `+0x00` | `src[2]` |
| `+0x10` | `src[1]` |
| `+0x20` | `src[0]` |
| `+0x30` | `src[3]` |

A négy kimeneti sor (soronként 4×int16 + 1×int32 bias, sortávolság `0x04`,
biasz `0x40+4·sor`) ugyanazt az oszlopsorrendet használja, és a sorok
**pontosan a bemenetükkel azonos indexre** íródnak vissza: a `src[2]`-t
domináló sor a kimenet `+0`-ás bájtjára megy, a `src[1]`-t domináló a `+1`-re,
`src[0]` a `+2`-re, `src[3]` (alfa) a `+3`-ra. Ha a tároló BGRA (a Win32 GDI
szokása szerint: `src[0]=B, src[1]=G, src[2]=R, src[3]=A`), a mátrix-oszlopok
sorrendje **R, G, B, A** — a szokásos, matematikailag "helyes" színmátrix-
konvenció —, és az alkalmazó **nem cserél csatornát**: a bemeneti bájtindexet
és a kimeneti bájtindexet azonos leképezéssel kezeli.

**Következmény a nyitott kérdésre:** a `TwoTone` linked
`ContrastAndBrightnessLinked` ágának saját mátrixépítője (`0x008f2040`,
lásd fent: `R'=k·R+t; G'=k·G+t; B'=k·B+t`, **azonos** `k`/`t` mind a három
csatornán) ezért **csatorna-szimmetrikus** — nem tud R/B-cserét vagy
egyenlőtlen luma-súlyozást okozni, mert a diagonális mátrix minden
RGB-csatornán azonos együtthatót ír. A `0x008f28d0` (191 b) egy általános
**5×5 lebegőpontos mátrixszorzó** (`this[0x28..] = this[0..] × eax[0..]`,
homogén 5. sor/oszlop a biaszhoz) — ez a `SimpleColorMatrix` láncolási
mechanizmusa (több mátrix egymásba szorzása), nem csatorna-újrarendezés.

⇒ **A golden-mérésben látott "első RGB-csatornát követi" jelenség forrása
KIZÁRVA ebből a lépésből.** A színmátrix-alkalmazó és a linked
kontraszt/fényerő-mátrix egyaránt szimmetrikus a csatornákon.

#### A LUT-skalár MEGVAN — a `TwoTone` NEM lumát használ, hanem a NYERS piros csatornát

**Bizonyítottság: MEGERŐSÍTETT.** A `0x00bb87b0` (493 b, LUT-építő) és a
közös LUT-alkalmazó `0x00bcb2f0` (744 b) teljes diszasszemblátuma
megválaszolja a kérdést.

**A LUT-tábla négy 256 elemű "rekeszből" áll** (`base+0x000`, `+0x400`,
`+0x800`, `+0xc00`, egyenként 256×4 bájt), és a `0x00bcb2f0` mindegyiket a
MEGFELELŐ forrás-bájttal indexeli:

```
byte[src+2] → LUT[base+0x800 + byte·4]   (32 bites csomagolt szín)
byte[src+1] → LUT[base+0x400 + byte·4]
byte[src+0] → LUT[base+0x000 + byte·4]
byte[src+3] → LUT[base+0xc00 + byte·4]
```

A négy lekérdezett dword-ot bájtonként (0–7, 8–15, 16–23, 24–31 bit)
SZÉTBONTVA, telítetten összeadja, és ugyanarra a négy kimeneti bájt-helyre
írja vissza — ugyanaz a mechanizmus, amit a `0x008f2640` mátrix-alkalmazónál
már dokumentáltunk, csak LUT-tal, nem szorzással.

**A `0x00bb87b0` viszont a NÉGY rekeszből CSAK EGYET tölt fel.** A
két-megállós (fekete/fehér) esetben a `0xbb8931`–`0xbb8958` ciklus mind a
256 index `i` (0–255) értékre kiszámolja az interpolált ARGB32 színt
(`0x00bb85b0` hívásával, `pozíció = i`; két megállónál a munkavégző által
generált pozíciók 0 és 255, lásd az RGB-interpolációs levezetést lent), és
**KIZÁRÓLAG a `+0x800` rekeszbe** írja (`mov dword ptr [edx+ecx*4+0x800], eax`
a `0xbb8951` címen). A `+0x000` és `+0x400` rekeszt a függvény explicit
**NULLÁZZA** (`memset(esi, 0, 0x400)` és `memset(esi+0x400, 0, 0x400)`,
`0xbb895a`–`0xbb897f`); a `+0xc00` (alfa) rekeszt nem érinti (más helyen
töltődik fel: a `0xbcb270` az egész puffert nullázza, majd mind a négy rekeszt
bájtonként identitásra állítja, a `+0xc00` rekeszben a bájt 3 = `i`).

**Összerakva a `0x008f2640` mátrix-elemzés bájt-leképezésével**
(`src[2]` = a mátrix R-oszlopa, ha a tároló a szokásos Win32-BGRA): a
`+0x800` rekesz pontosan a **`src[2]` (piros csatorna) bájtjával**
indexelődik. A `+0x000`/`+0x400` rekeszek (kék/zöld csatorna) nullák ⇒
**nulla hozzájárulás**; a végeredmény a kimenetben **kizárólag a bemenő
(kontraszt/fényerő-korrigált) piros csatorna értékétől függ.**

⇒ **A `TwoTone` NEM lumát számol.** A munkafa jelenlegi
`glimmer_tone.py:apply_twotone` függvénye is a `SimpleColorMatrix` utáni
pixel nyers piros csatornáját veszi (`[..., 0:1]` RGB-ben), és a lentebbi
QEMU-összevetésben ez a natív LUT-kimenettel bájtra egyezik. A régebbi
Rec.601-lumára és a `MAE 6,3644`-re vonatkozó mondat elavult állapotot írt le;
nem a jelenlegi forráskódot.

#### TwoTone: paramétertől pixelmagig, natív QEMU-kontrollal (2026-10-04, #626)

**Bizonyítottság: megerősített a pixelmatematikára** — az utasításszintű
híváslánc és a natív függvények `qemu-i386`-futtatása egyezik. A valódi
`filterdesc.xml`-parser és a teljes `0x00bb7c80`/`0x00bd0700` külső
végrehajtó nem futott a mérőharnessben; ezeknek a teljes, parseren átmenő
end-to-end futása külön nincs igazolva.

**Paraméter- és hívásút.** A `filterdesc.xml:1365–1380` szerint a
`TwoTone` sorrendje `Brightness`, `Contrast`, `Fade`, fekete, fehér; a
Brightness tartománya −95…95, a Contrast 0…100, a Fade 0…100, az alapok
pedig 0, 20 és 0. A két szín alapértéke `#004488` és `#ffff00`. A leíró a
Fade-et `BlendAlpha = 1 − Fade/100` alakban adja át. A `0x00bc2760`
attribútum-beolvasó a két színből gradiensobjektumot készít a művelet
`+0x40` mezőjébe, majd a `0x00bb8710` útjára adja; a `0x00bb7c80` közös
alkalmazó a művelet 8. slotján keresztül a `0x00bb87b0` TwoTone-LUT-építőt
hívja, végül a `0x00bcb2f0` képponti LUT-alkalmazót. A `SimpleColorMatrix`
gyerek linked kontraszt/fényerő-ágát a `0x00bb6400` állítja elő; a
`0x008f21a0` alakítja fixpontos együtthatókká, a `0x008f2640` alkalmazza
őket a pixelekre. A linked mátrix képlete és a Q11-egész kerekítési lépései
a fenti 4.9-es szakaszban vannak rögzítve.

**Pixelmag.** A `0x00bb87b0` a két megadott színből 256 elemű LUT-ot épít a
`+0x800` rekeszbe. A `0x00bcb2f0` ennél a rekesznél a mátrixolt BGRA-pixel
`src[2]` bájtját olvassa, vagyis a nyers piros csatornát; ezután a négy
rekesz dword-ját bájtonként telítetten összeadja. A Fade ága a
`0x00bd0700` végrehajtóból a `0x009dc4b0` keverőt hívja. `Fade=50` esetén
`BlendAlpha=0,5`, belső súly `trunc(0,5·256)−1 = 127`. Páratlan sorhossznál
`0x00c33d60` a `0x009bbde0` eredményét (`AL=1`) a `0xd695d4` jelzőbe írja;
ez a `0x009dc646–0x009dc6fb` skalár farokágat választja. A kétutas
csomagolt pixelképlet ezért az utolsó oszlopra nem érvényes: ott a natív
képlet `ki = t + (((b − t) · w) >> 8)`.

**QEMU-mérés és kód-összevetés.** A harness az eredeti 32 bites natív
függvényeket futtatta `qemu-i386` alatt, 5 soros, 8 és 9 pixel széles
szintetikus BGRA-képen. A pixelek: `R=(13x+17y)&255`,
`G=(11x+5y)&255`, `B=(7x+3y)&255`, `A=255`. A mátrix builderét,
konverterét, pixelmagját, a TwoTone LUT-buildert és a közös LUT-alkalmazót
valódi gépi kód futtatta; a beolvasó gráfot kézzel épített objektumok, a
literál-kifejezéskiértékelőt pedig egy értékmásoló helyettesítette. A Fade
összevetés közvetlenül a natív `0x009dc4b0` függvényt hívta; az outer
`0x00bd0700` alfa-utókezelését statikusan ellenőriztük, amely a végső alfa-
csatornát `0xff`-re állítja.

| Beállítás (`Brightness`, `Contrast`, `Fade`) | 8 px: eltérő RGB-bájt / összes | 9 px: eltérő RGB-bájt / összes |
|---|---:|---:|
| `(0, 20, 0)` alap | `0/120` | `0/135` |
| `(+50, 20, 0)` | `0/120` | `0/135` |
| `(−50, 20, 0)` | `0/120` | `0/135` |
| `(0, 80, 0)` | `0/120` | `0/135` |
| `(0, 20, 50)` | `0/120` | `10/135` — 5 pixel, max. 1 szint, mind az utolsó oszlopban |

A mátrix és a piros LUT-skalár mind a tíz futásban bájtra egyezett; a Fade
páros szélességnél is egyezett. Páratlan szélesség és `Fade=50` esetén
kizárólag a sorvégi skalár ág tér el: a jelenlegi
`glimmer_ops.alpha_blend` minden pixelre a natív kétutas egészkeverési
képletet alkalmazza.
Az 5 sor 5 sorvégi pixelén összesen 10 RGB-bájt tér el, legfeljebb egy
szinttel. A natív kód útja igazolt; a teljes, parseren átmenő képkimenet
összevetése továbbra is nyitott.

#### Eredeti / nálunk / teendő — TwoTone

| Lépés | Eredeti | Nálunk | Teendő |
|---|---|---|---|
| linked Brightness/Contrast → fixpontos mátrix | `0x00bb6400` → `0x008f21a0` → `0x008f2640` | `simple_color_matrix(..., linked=True)` | A felsorolt natív esetek mind bájtra egyeznek; nincs mért eltérés. |
| fekete→fehér gradiens | `0x00bb87b0`; a `0x00bcb2f0` a nyers piros bájttal indexel | `apply_twotone` piros csatornás interpolációja | A vizsgált LUT-pixelértékek bájtra egyeznek; a korábbi Rec.601 állítás törlendő. |
| Fade páros szélességnél | `0x00bd0700` → `0x009dc4b0` | `glimmer_ops.alpha_blend` kétutas egészképlete | A `Fade=50` páros képeken bájtra egyezik. |
| Fade páratlan szélesség utolsó oszlopa | `0x009dc646–0x009dc6fb`: `t + (((b−t)·w)>>8)` | `glimmer_ops.alpha_blend` ugyanazt a kétutas képletet használja minden pozíción | Fejlesztői teendő: az odd-width sorvégi pixelre külön skalár farok, natív képlettel és előjeles aritmetikai `>>8`-cal; a jelenlegi 5×9 `Fade=50` kontrollban 5 pixel/10 RGB-bájt, max. 1 szint eltérés. |

**Cáfoló kontroll.** A nyers piros indexelés cáfolására a `Rec.601`-luma
alternatívát próbáltuk. A `qemu-i386` futtatás `(x=2,y=0)` mátrixolt
BGRA-ja `00 00 01 ff`, a natív kimenete `87 45 01 ff`, pontosan a `LUT[1]`;
a `LUT[0]` `88 44 00 ff`. A Rec.601-alternatíva ennél a pixelnél
`0,299/255` gradiensaránnyal és bájtra kerekítve `88 44 00` kimenetet adna.
A megfigyelt natív bájt ezt az alternatívát cáfolja, a nyers piros csatornát
erősíti meg; a diszasszemblálás ettől függetlenül ugyanezt mondja a
`src[2]` → `+0x800` indexeléssel.

#### Színárnyalat-forgatás (`0x008f1e70`)

**LEZÁRVA a G) szakaszban:** a korábbi dekompilátor-korlátot a helyi nyers
x86-diszasszemblálás és a PE-adatkonstansok kiolvasása feloldotta. A hue-
mátrix konkrét együtthatói, címei és numerikus kontrolljai a G) szakaszban
állnak; a korábbi „feltételes / valószínű Haeberli” megfogalmazás elavult.

#### `ColorMatrix` — 4×5 fixpontos pixelképlet; a `UseAlpha` külső határa nyitott (#626, 2026-10-04)

**Forrás:** a `ColorMatrix` 8. rése `0x00bc1860` (245 b), a közös alkalmazó
`0x00bc16b0` (428 b), a mátrix konverziója `0x008f21a0` (849 b), a pixelenkénti
kernel `0x008f2640` (644 b; skalár ág `0x008f2674`–`0x008f281e`, MMX/SSE2 ág
`0x008f281f`–`0x008f28c3`), a vektorregiszter-betöltő `0x008f25f0`, a kerekítő
segéd `0x00c29990` (28 b). A vtable és az attribútum-beolvasó címe a fenti
táblában áll.

A worker a `Matrix` tömb 20 double elemét float32-ként tárolja
(`0x00bc1860`: `fstp dword`), majd a közös alkalmazó 4×5 sorfolytonos
mátrixként adja át. A mátrix sorai és színoszlopai `R,G,B,A`; a pixelmemória
és a kimenet bájtsorrendje `B,G,R,A`. A 4. oszlop az alfa-bemenet súlya, az 5.
elem a sor eltolása.

Legyen `m[j,k]` a float32-re alakított együttható, `o[j]` az eltolás, és
`x=(R,G,B,A)` a forrás pixel. A `0x008f21a0` a mátrix együtthatóit Q11
int16-ba, a sor eltolását pedig dword biasba alakítja:

```text
round-away(v) = trunc(v + (v < 0 ? -0.5 : +0.5))
q[j,k]        = signed_int16(low16(round-away(2048 * m[j,k])))
b[j]          = round-away(4 * o[j]) + 2

acc[j] = wrap32(b[j] + Σ(k=R,G,B,A) sar32(q[j,k] * x[k], 9))
y[j]   = clamp(sar32(acc[j], 2), 0, 255)
```

`sar32` az x86 előjeles aritmetikai jobbra tolása, tehát negatív értéknél
lefelé kerekít; **minden szorzat külön** `>>9`-et kap, csak utána adódnak
össze. Az akkumulátor 32 bites (`wrap32`), a kernel a négy csatornát külön
sorral számolja, az alfa-sort is, és minden sor használhatja az alfa-oszlopot.
A végső `>>2` után történik a 0…255 vágás. A `q` tárolásakor az alsó 16 bit
marad meg, a kernel ezt előjeles int16-ként olvassa (`movsx`); a bias dword.

A `0x008f281f`-nél induló MMX/SSE2 ág ugyanezt a műveletsorrendet tartja:
`0x008f25f0` betölti a négy oszlop együttható-vektorát és a biasvektort; a
kernel a forrás minden bájtját `[bájt,0]` int16-párként rendezi, `pmaddwd`
után külön `psrad 9`-et végez az adott csatorna hozzájárulásán, majd az
összeget `psrad 2`-vel skálázza és telítetten bájtra csomagolja. A skalár és
vektor ág közti képletazonosságot az utasítássorrend, hat QEMU-minta pedig a
konkrét kimeneteken ellenőrzi.

**`UseAlpha`:** a `ColorMatrix` worker, a közös alkalmazó és a pixelkernel
nem olvassa és nem kapja meg ezt a jelzőt. Ezért a fenti pixelmag képlete
`UseAlpha=false` és `UseAlpha=true` mellett is azonos, ha azonos mátrixot és
forráspixelt kap: az alfa-sor és -oszlop a magban mindkét esetben aktív.
A leíró parser ettől külön olvassa a `UseAlpha` nevet (`0x009ca5e0`, a mező
írása `0x009cb45d`, `[objektum+0x20a]`). **NINCS MEG**, hogy ezt a külön
flaget a Glimmer-hívási lánc melyik magasabb rétege fogyasztja, illetve
`false`/`true` mellett változtat-e a mag bemenetén, utólagos alfa-kezelésén
vagy kompozitálásán. Emiatt a teljes, leíró-szintű `UseAlpha` szemantika
feltételes marad.

**QEMU-kontrollok.** Az eredeti ELF-kódrész futott `qemu-i386 -B
0x400000000000` alatt, `ulimit -v 8388608` és `timeout 60` korláttal. Mind a
hat kézi mátrix/pixel mindkét `0x00c29990` konverziós ágon és mindkét pixel-
kernel ágon (skalár, illetve az eredeti `0x008f25f0` által betöltött MMX/SSE2)
ugyanazt a bájtsort adta a közvetlen `0x008f21a0` + `0x008f2640` útban. A
`0x00bc1860` eredeti workerével futtatott külön próba szintén egyezett mindkét
konverziós ágon a skalár kernelhez; ez a worker-próba négy általános
XML-tömb-/double-olvasó és memória-kezelő segédfüggvényt shimelt, a ColorMatrix
worker, mátrixkonvertáló és pixelfüggvény az eredeti kód volt. Ez nem teljes
`filterdesc.xml`-betöltés, ezért a `UseAlpha` külső hatását nem méri. Az alábbi
`M` jelölés 4×5, soronként `R,G,B,A,eltolás`; a pixel és az eredmény BGRA
bájtok hexadecimális alakban:

| kontroll | `M` sorai | bemenet BGRA | eredmény BGRA |
|---|---|---|---|
| azonosság | `[1,0,0,0,0; 0,1,0,0,0; 0,0,1,0,0; 0,0,0,1,0]` | `0b16212c` | `0b16212c` |
| alfa-oszlop és alfa-sor | `[1,0,0,.25,3.5; 0,1,0,0,0; 0,0,1,0,0; .5,0,0,.5,1]` | `09111f50` | `09113739` |
| vágás és tört eltolás | `[2,0,0,0,-5; 0,.5,0,0,.125; 0,0,-.5,0,1; 0,0,0,2,-10]` | `ff011ec8` | `000137ff` |
| előjeles fél-együttható | `[2.5/2048,2.5/2048,0,0,0; -2.5/2048,-2.5/2048,0,0,25; 0,0,1,0,0; 0,0,0,1,0]` | `00ffffff` | `001801ff` |
| tört együttható-konverzió | `[.1234,0,0,0,0; 0,-.1234,0,0,41.25; 0,0,1,0,0; 0,0,0,1,0]` | `0080ffff` | `001920ff` |
| tagonkénti `sar 9` | `[1/2048,1/2048,1/2048,0,.25; 0,1,0,0,0; 0,0,1,0,0; 0,0,0,1,0]` | `ffffffff` | `ffff00ff` |

**Cáfoló kontroll:** az utolsó sorban a három első Q11 szorzat egyenként
`255 >> 9 = 0`, az eltolásból a bias `3`, ezért a piros kimenet
`(0+3)>>2 = 0`. Az alternatív, hibás „előbb összead, majd egyszer tol” modell
`(255+255+255)>>9 = 1` értéket adna, így a piros kimenet `1` lenne
(`ffff01ff`). A natív kimenet `ffff00ff` mindkét konverziós ágon; az eltérés
az utasításszintű, külön szorzatonkénti `sar 9`-cel is egyezik.

#### #626 leltár — `ColorMatrix` sor frissítése

| művelet | pixelképlet | `UseAlpha` | összesített állapot |
|---|---|---|---|
| `ColorMatrix` | **megerősített** a 4×5 pixelmag képletére | **nyitott** a leíró magasabb rétegén | **feltételes** |

Ez a frissítés a `ColorMatrix` pixelmatematikáját rögzíti; a flag fogyasztójának
és a többi #626 műveletnek a feltárását nem zárja le.

#### Eredeti / nálunk / teendő

| | Eredeti, mért | PicasaPy forrása | Teendő |
|---|---|---|---|
| 4×5 RGBA-mátrix | a fenti Q11/int16 + dword-bias képlet, `0x008f21a0` → `0x008f2640` | `src/picasapy/render/glimmer_ops.py:628–646` általános `n×3` RGB-képletet valósít meg; a `simple_color_matrix()` hívja, általános 4×5 `ColorMatrix`-út nem található | külön fejlesztési munka: általános RGBA-mátrix és bájtra ellenőrizhető minták |
| `UseAlpha` | a parser `[objektum+0x20a]` flaget ír; a pixelmag nem kapja meg | nincs `UseAlpha`-ággal kezelt általános `ColorMatrix` | előbb a magasabb szintű fogyasztót kell feltárni; a flag szemantikája nélkül ne rögzítsünk eltérő alfa-szabályt |

**Bizonyítottsági fok:** megerősített a pixelmag képletére — A) utasításszintű
olvasás a mátrixcsomagolótól a négy soros pixelenkénti kernelig; B) az eredeti
worker és pixelfüggvények futtatása qemu-i386 alatt, mindkét kerekítési ágon,
a fenti bájt-goldenekkel. A `UseAlpha` descriptor-szintű hatása nyitott:
a parser mezőjét nem sikerült azonosítani a Glimmer magot körülvevő fogyasztóval.

**Nyitott, blokkoló következő lépés:** `Ghidra-kör kell: 0x009ca5e0 — a
`UseAlpha` parser által `[objektum+0x20a]` helyre írt flag Glimmer-hívási
láncbeli fogyasztójának azonosítása, és annak eldöntése, hogy false/true
módosítja-e a ColorMatrix alfa-oszlopát, alfa-sorát vagy a mag előtti/utáni
alfa-kezelést [blokkoló]`.

#### #626 — `SimpleColorMatrix`: natív bájtszintű kontroll (2026-10-05)

Ez a mérés az előző, 4.9-es szakaszban rögzített mátrixépítőket és Q11-es
alkalmazót közvetlenül hasonlítja össze a `simple_color_matrix()` kimenetével.
Az értékforrás a Picasa 3.7 `runtime/filterdesc.xml`; mind a nyolc használatot
lefedi. A változó csúszkáknál a deklarált alapértéket és mindkét szélső pontot
is tartalmazó pontos rácsot használtuk.

| `filterdesc.xml`-használat | deklarált paraméterek és tartományok | natív próba |
|---|---|---|
| Boost (`:715`) | `Impact` 0…100, alap 50; `B=Impact×(−20/50)`, `S=Impact×(20/50)`, `C=Impact×(40/50)` | Impact = 0, 50, 100 |
| Cinemascope (`:760`) | `S=−25` | `S=−25`, `C=B=0` |
| CrossProcess (`:835`) | `C=10`, `B=10` | `C=B=10`, `S=0` |
| HeatMap (`:955`) | `S=0` | `S=C=B=0` |
| Holga (`:978`) | `C=25` | `C=25`, `S=B=0` |
| Lomo (`:1050`) | `S=20`, `C=35`, `B=5` | `S=20`, `C=35`, `B=5` |
| NightVision (`:1129–1138`) | `B,C` külön-külön −50…50, alap 0 | `B,C ∈ {−50, 0, 50}` teljes 3×3 rácsa |
| TwoTone (`:1372–1377`) | `ContrastAndBrightnessLinked=true`, `S=0`; `B` −95…95, alap 0; `C` 0…100, alap 20 | linked; `B ∈ {−95, 0, 95}` és `C ∈ {0, 20, 100}` teljes 3×3 rácsa |

A hiányzó, XML-ben nem deklarált paramétert a közvetlen builder-próbában a
semleges `0` értékkel adtuk meg. Ez nem az XML parser vagy a művelet
példányosításának mérése; a parser alapérték-beállítását a próba nem hívta.

**A út — utasításszintű levezetés.** A `0x00bb6400` a telítettség, kontraszt,
fényerő, hue és linked mezőket olvassa; a `0x008f1d00` a telítettséget építi,
a linked ág `0x008f2040`-et, a különálló ág `0x008f1bd0` kontrasztot, majd
`0x008f1af0` fényerőt épít, végül `0x008f1e70` a hue-t. A kész mátrix
Q11-konverziója `0x008f21a0`, a képpont-alkalmazó `0x008f2640`; a részletes
együttható- és kerekítési képletet a fenti 4.9 tartalmazza. A nyolc XML-helyet
és a csúszkák deklarációit a fenti sorszámok azonosítják.

**B út — az eredeti x86 kód QEMU-futtatása.** A CRT-shimmel futó harness az
eredeti mátrixépítőket, a `0x008f21a0` konverziót, a `0x008f25f0` vektoros
beállítást és a `0x008f2640`-et hívta; a mátrix kezdete 5×5 identitás volt,
a hue bemenete 0. A Python-oldalon a `simple_color_matrix()` szolgáltatta az
összevetést. A leíró parser és a `0x00bb6400` magasabb szintű műveleti útja
nem futott.
Forrás- és célképleíró külön rekordban volt, mindkettőben `+0x04` stride
pixelben, `+0x08` szélesség, `+0x0c` magasság, `+0x10` BGRA-adatmutató;
forrás-stride = `width+2`, cél-stride = `width+3`. A magasság 52, a szélesség
8 (páros) és 9 (páratlan). A bemeneti RGB minden pixelre
`R=(13x+17y)&255`, `G=(11x+5y)&255`, `B=(7x+3y)&255`; az alfa
`A=(x+y×width)&255`. A forrás- és célterület külön memóriában volt.

26 paraméterkészlet × 2 szélesség futott skalár és SSE2 módban. A 68 952 aktív
RGB-kimeneti bájt mindegyike egyezett a PicasaPy-kimenettel (eltérés 0, maximum
eltérés 0); a skalár és SSE2 teljes natív kimeneti puffere is bájtra egyezett.
22 984 natív alfa-bájt változatlan maradt, a 32 448 célkitöltő bájt pedig
érintetlen maradt. Az alfa-adat natív passthrough-ellenőrzés: a PicasaPy
`simple_color_matrix()` RGB `uint8` képet fogad (`curves.py:17–23`,
`glimmer_ops.py:656–675`), ezért nincs vele közvetlen RGBA-függvény-összevetés.

**Cáfoló kísérlet.** A natív eredménnyel szemben ellenőriztük az alternatív,
egyetlen lebegőpontos mátrixszorzás + egyszeri kerekítés modelljét. Az 52
beállítás/szélesség-párban 6 080 RGB-bájt tért el, legfeljebb 1 szinttel; az
első eltérés a Cinemascope, 8 széles esetben 313 bájt volt. Ez az alternatíva
nem magyarázza a natív kimenetet; a PicasaPy fixpontos útja egyezik vele. A
független statikus út is kizárja az egykörös modellt: `0x008f21a0` Q11-re
konvertál, a `0x008f2640` pedig tagonként `>>9`, majd `>>2` műveletet végez.

#### Eredeti / nálunk / teendő

| | Eredeti natív kód | PicasaPy | Teendő |
|---|---|---|---|
| `SimpleColorMatrix` RGB-kimenet | a 4.9-es mátrixépítők + `0x008f21a0` + `0x008f2640`; a fenti rácson natív QEMU-kimenet | `src/picasapy/render/glimmer_ops.py::simple_color_matrix` → `_szinmatrix_osszefuzve` → `_fixpontos_szinmatrix` | A mért beállításokon bájtra egyezik; nincs igazolt RGB-javítási teendő. |
| Alfa | vizsgált `SimpleColorMatrix` mátrixoknál az eredeti kernel átengedi az alfa-bájtot | az RGB API alfa-csatornát nem fogad | Natív passthrough igazolva; a PicasaPy-függvény alfa-viselkedése nem része ennek az összevetésnek. |

**Bizonyítottsági fok:** **megerősített** a statikusan levezetett mátrix- és
pixelút, valamint a fenti pontos paraméterpontok RGB-pixelmatematikája — A)
utasításszintű olvasat; B) független natív QEMU-kimenet és PicasaPy-bájtsor
összehasonlítása, egyező eredménnyel. A csúszkák köztes értékeit, az XML
betöltő/példányosító útját és a hiányzó attribútumok objektum-alapértékeit ez a
mérés nem vizsgálta.


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

~~**Amit a bináris NEM ad meg**~~ → **mind kiolvasva, ld. a következő szakaszt** (2026-09-27). Az eredeti szöveg (mérésből, a fenti golden páron illesztve):
a Sobel-válasz osztója a 128-as eltolás előtt (`4,0`), és a 10. lépés
keverési módja (`multiply` és `darken` egyaránt illeszkedik — a fehér alap
mellett gyakorlatilag megkülönböztethetetlenek).

~~A `quality="2"` a Flash `BitmapFilterQuality` szerint az elmosás
átfutásainak száma (4.5): két menet egy 2 képpont széles dobozszűrőből
pontosan a `[1, 2, 1]/4` háromszög-mag.~~ → **helyesbítve** (#3812): a
`quality` valóban menetszám, de a menet a natív, tört súlyú dobozszűrő
(`nativ_blur`), nem 2 képpont széles doboz; ld. a következő szakaszt.

#### ⭐ `EdgeDetectionB` — a „mérésből illesztett” tényezők a binárisból, és a natív elmosás (2026-09-27, 383. kör, #626)

*Bizonyítottsági fok: **megerősített**, utasításszinten, független újralevezetéssel (EGYEZIK) és golden-méréssel.*

A fenti lépéstábla három tényezőt „mérésből illesztettnek” jelölt. Mind a
három kiolvasható:

| tényező | eddig | a binárisból |
|---|---|---|
| a Sobel osztója | 4,0, illesztve | **4** — `0x00bb6895` `push 4`; `0x00bb732d` `cdq; idiv` |
| a 128-as eltolás | feltevés | az akkumulátor kezdőértéke **512** (`0x00bb6faa` `shl eax, 7` a 4-ből; `0x00bb71b9` `mov eax, [edx+8]`) |
| a `100 − detail` helye | „a kontraszt illeszkedett” | a gyerek `SimpleColorMatrix` **`+0x30` = contrast** mezője (`0x00bbce1b` `fsubr [0xcf3a08]` = 100,0; `0x00bbce24` `add eax, 0x30`) |
| a 10. lépés módja | `multiply` vagy `darken` | **5 = Multiply** (`0x00bbcd76` `mov ecx, 5` → `0x00bbf780`) |

**A Sobel egy csatornára:** `ki = clamp((512 + Σ kᵢ·pᵢ) idiv 4, 0, 255)` =
`clamp(128 + floor(Σ/4), 0, 255)`. A skalár ág (`0x00bb7140`) nulla felé
csonkol, a SIMD-ág (`0x00bb75a0`: `psrad` + `paddd [0x80…]`) lefelé kerekít;
negatív osztandónál mindkettő 0-ra vág, tehát a kettő azonos. A B, G és R
csatorna külön számol, az alfa 0xFF. A sarok- és élszakaszok külön
eltolástáblát kapnak (`0x00bb6d1e`–`0x00bb6f23`); hogy ezek pontosan melyik
forrásképpontot használják, a 2026-10-04-i QEMU-kontroll után nyitott kérdés.
A két mag:
`direction = 0` („horizontal”) `[−2 0 2; −4 0 4; −2 0 2]`, `direction = 1`
`[2 4 2; 0 0 0; −2 −4 −2]` (`0x00bb6729`–`0x00bb67fa`).

**Az 1. lépés elmosása a natív `BlurImageOperation(2, 2, quality = 2)`**
(`0x00bbcaa5` `fld [0xcf3a48]` = 2,0, `push 2`). A modul eddig egy `[1, 2, 1]/4`
háromszög-maggal közelítette („két menet egy 2 széles dobozból”). A natív
elmosás (`render/nativ_blur.blur_image_operation`, #3474/#3580) ettől
mérhetően eltér.

**Mérve** (`Neon` alap, 684-es készlet, ΔE a Picasa-exporthoz; minden más
változatlan):

| változat | ΔE |
|---|---:|
| ma (`[1,2,1]/4`, lebegőpontos Sobel) | 1,967 |
| natív elmosás | **0,493** |
| natív elmosás + egész Sobel (`512`, `idiv 4`) | 0,493 |
| … + a két Multiply csonkolva | 0,493 |
| … + Darken a 10. lépésben (kontroll) | 0,517 |
| a `100 − detail` a fényerőbe / telítettségbe (kontroll) | 4,362 / 5,870 |

A maradék 0,49-ből 0,20 a fekete háttéren, 0,29 az éleken van. A Picasa
exportja 4:4:4-es JPEG; a saját kimenetünk 95-ös minőségű, 4:4:4-es JPEG-je
önmagához képest ezen a képen **0,315** ΔE. A maradék tehát ennek a képnek a
JPEG-zajával egy nagyságrendben van. A `Neon` záró `Tint`-je már a natív
táblát használja (#3631).

**Nálunk (MÉRVE, #3812 után):** a `render/glimmer_edges.edge_detection_b`
az 1. lépésben a `nativ_blur.blur_image_operation(kép, 2.0, 2.0, quality=2)`-t
hívja, a Sobelt egész aritmetikával számolja (`(512 + Σ) // 4`, a peremen
ismétlődő képponttal, `[0, 255]`-re vágva), a 10. lépésben az 5-ös
(Multiply) móddal kever. A `Neon` alap a 684-es készleten **ΔE 0,493**
(előtte 1,967), a `Neon` max (`Fade 100`) 0,121 (változatlan). Az egész és
a lebegőpontos Sobel ezen a képen ΔE-ben nem válik el (mindkettő 0,493),
de bitre eltér: a `−2`-es összeg `floor`-ral 127, kerekítve 128 lenne. Őr:
`tests/render/test_neon_878.py` (független referencia + golden).

#### QEMU-pixelkontroll a Sobel gyermekműveleten (2026-10-04, #626)

*Bizonyítottsági fok: a belső Sobel-kernel képlete a belső képpontokra
**megerősített** (utasításszintű olvasat + közvetlen natív futtatás egyezik).
Az alábbi folytatás a peremszabályt is **megerősíti**; a teljes
`EdgeDetectionB`-csővezeték és a Fade-pár **nyitott**.*

A harness az eredeti i386 `0x00bb6620` Sobel-alkalmazót futtatta QEMU alatt,
kézzel épített művelet-objektummal és a leírt képleíróval: `+0x04` stride
képpontban, `+0x08` szélesség, `+0x0c` magasság, `+0x10` BGRA-adatmutató.
A BGRA-bemenet szorosan csomagolt, alfa=`0xff`; tesztkép 8×5 és 9×5,
mindkét irány (`direction=0/1`). Ez négy natív gyermekművelet-futtatás, nem a
teljes `EdgeDetectionB` és nem a `filterdesc.xml`-ből összeállított Neon:
annak leíró szerinti `detail=50` értéke nem része ennek a közvetlen Sobel-
hívásnak. A `detail=50` → `100−detail=50` kontrasztút (`0x00bbcdd0`) és a
közös fixpontos `ColorMatrix`-alkalmazó (`0x008f21a0` → `0x008f2640`) korábbi
utasításszintű és Neon-exportos bizonyítéka a 4.9-es szakaszban van; ezeket
ebben a közvetlen gyermekművelet-próbában nem futtattuk.

| natív irány | méret | eltérő bájt / BGRA-bájt | jobb felső: natív BGRA | jelenlegi modell BGRA |
|---:|---:|---:|---|---|
| 0 | 8×5 | 3 / 160 | `(122,119,123,255)` | `(142,150,154,255)` |
| 1 | 8×5 | 3 / 160 | `(116,109,89,255)` | `(122,118,94,255)` |
| 0 | 9×5 | 3 / 180 | `(122,119,123,255)` | `(142,150,154,255)` |
| 1 | 9×5 | 3 / 180 | `(116,109,89,255)` | `(122,118,94,255)` |

Mind a négy futásban az összes eltérés kizárólag a felső sor jobb szélső
képpontjának B/G/R csatornája; minden más képpont és minden alfa-bájt egyezik.
Az utasításszintű olvasat szerint a `0x00bb68d0` és `0x00bb6ce0` útvonalak
külön peremeltolás-táblákat építenek, majd a `0x00bb7140` skalár alkalmazó
csatornánként összegez, `idiv`-vel oszt, és 0…255 közé vág. Ez az első kör
a belső számítást megerősítette, de nem naplózta a teljes perem-eltolástáblát;
az akkori nyitott állapotot a következő, 2. körös alfejezet zárja le.

**Cáfoló kontroll:** jobb felső sarok körüli, 32 és 64 értékű kék egyképpontos
impulzusokkal ismételve a különbség továbbra is csak a jobb felső kimeneti
képpontban jelentkezett. Ez kizárja, hogy a fenti eltérést csak a gradiens
tesztkép értékei okozzák. A két amplitúdó mindkét szélességen ugyanazt az
egész együtthatót adta vissza a jobb felső kimeneti pixelben (`kimenet =
128 + együttható·bemenet/4`):

| forrás a jobb felső célpixelhez képest `(dx,dy)` | `direction=0`: edge-pad modell | `direction=0`: natív QEMU | `direction=1`: edge-pad modell | `direction=1`: natív QEMU |
|---|---:|---:|---:|---:|
| (−1, 0) | −6 | 0 | 2 | 4 |
| (0, 0) | 6 | −2 | 6 | 2 |
| (−1, 1) | −2 | 4 | −2 | 0 |
| (0, 1) | 2 | −2 | −6 | −6 |

Ez a jobb felső sarok **mért lokális térképe** 8×5 és 9×5 képen; a másik
három sarok és a négy él általános leképezése ebből nem következik.

**Fade-kontroll, csak az alacsony szintű keverőn:** a `0x009dc4b0` QEMU-futtatása
`BlendAlpha=0.5`-tel (`0x00bd0700` által átadott nyers súly 128, a keverőben
127-re csökkentve), 8×5 és 9×5 méreten a jelenlegi
`glimmer_ops.alpha_blend(..., 0.5)` RGB-kimenetével 0/120, illetve 0/135
eltérő bájtot adott. A belső keverő alfa-bájtja 254; a 9×5-ös skalár sorvégi
ág utolsó oszlopán 255. A `0x00bd0ae5` külső út 255-re állítja a kész kimenet
alfáját. A Fade 0 (`BlendAlpha=1`) teljes QEMU-futtatása nem történt meg; a
`0x00bd079a`–`0x00bd07b2` utasítások a BlendAlpha=1 közeli esetben a
`0x009dc4b0` meghívása előtt korai visszatérést eredményeznek.

**Fejlesztői következmény (az alábbi peremtérképpel pontosítva):** a mostani
`_sobel_direction()` `np.pad(..., mode="edge")` modellje a natív Sobel-
gyermekművelettől csak a jobb felső sarokban tér el; a teljes peremtérkép és
annak impulzus-kontrollja lent megvan. A teljes Blur → SimpleColorMatrix → két
Sobel/AdjustCurves → Multiply → Fade út natív QEMU-összevetése továbbra is
**NINCS MEG**; a két Fade-értékes láncmérés nem teljesült. A futtatásminták
nem a termékkód vagy tesztfájlok.

#### EdgeDetectionB — a teljes Sobel-peremtérkép (2026-10-04, #626, 2. kör)

*Bizonyítottsági fok: **megerősített** a `0x00bb68d0`/`0x00bb6ce0` perem-
eltolásaira és a Sobel-kimenetre: az utasításszintű táblaolvasat, a 88 natív
QEMU-impulzusfutás és a kimeneti képletek külön ellenőrzése egyezik. A teljes
EdgeDetectionB-lánc/Fade továbbra is nyitott.*

A `0x00bb6840` a `0x00d695d2` jelző alapján választ: nulla esetén
`0x00bb6ce0`, nem nulla esetén `0x00bb68d0` fut (`0x00bb688d`–`0x00bb68a5`).
Az első ág a Sobel-alkalmazót pixelről pixelre hívja; a második a belső
szakaszon vektorizál, a perempixeleket szintén a `0x00bb7140` dolgozza fel.
Mindkét út 9 előjeles, képpontban mért forráseltolást ad át. A
`0x00bb7140` az eltérést bájtra (`eltolás × 4`) váltja, csatornánként
összegez, `idiv 4`-gyel oszt, majd 0…255 közé vág (`0x00bb7150`–
`0x00bb7398`). Az alábbi táblában `S` a mért sorlépés képpontban; a QEMU-
képek szorosan csomagoltak, ezért `S = W` volt.

| kimeneti hely | 9 forráseltolás, sorfolytonos 3×3-as tábla |
|---|---|
| belső pixel | `[-S−1, −S, −S+1; −1, 0, 1; S−1, S, S+1]` |
| felső él, sarok nélkül | `[-1, 0, 1; −1, 0, 1; S−1, S, S+1]` |
| alsó él, sarok nélkül | `[-S−1, −S, −S+1; −1, 0, 1; −1, 0, 1]` |
| bal él, sarok nélkül | `[-S, −S, −S+1; 0, 0, 1; S, S, S+1]` |
| jobb él, sarok nélkül | `[-S−1, −S, −S; −1, 0, 0; S−1, S, S]` |
| bal felső sarok | `[0, 0, 1; 0, 0, 1; S, S, S+1]` |
| **jobb felső sarok** | **`[−1, 0, −1; 0, 0, S−1; S, S, 0]`** |
| bal alsó sarok | `[-S, −S, −S+1; 0, 0, 1; 0, 0, 1]` |
| jobb alsó sarok | `[-S−1, −S, −S; −1, 0, 0; −1, 0, 0]` |

A jobb felső tábla a `0x00bb6ce0` ágban a `0x00bb7044` hívás paramétere;
az értékeket a `0x00bb6d1e`–`0x00bb6f23` blokk állítja elő. A másik ág
megfelelő peremhívása a `0x00bb6be5`; az ott felépített tábla byte-ra azonos.
A `0x00bb7140` ugyanezeket a kilenc eltérést ugyanabban a sorrendben olvassa.
Ez az egyetlen perem, ahol a natív tábla nem `mode="edge"` ismétlés.

**Natív mérés:** a forrás- és célképleíró külön rekord volt. 64 futás
fedte le a négy sarkot és a négy él egy-egy belső pontját, `direction=0/1`,
8×6 és 9×7 méret, valamint a harness által külön-külön 0-ra és 1-re állított
`0xd695d2`-ág mellett; további 24 futás a jobb felső sarok 2×2-es
szomszédságának három külön impulzusát mérte.
Minden bemeneti impulzus egy szürke képpont volt (B=G=R=64, A=255). A két
`0xd695d2`-ág mind a 32 azonos beállítású párja byte-ra egyezett. Az
`np.pad(mode="edge")` mind a 64 alapesetből 8-ban tért el: kizárólag a jobb
felső forrássarok impulzusánál, csak a jobb felső kimeneti pixel B/G/R
csatornáján. A natív offsettáblából levezetett képlet a 64 alapesetet és a
24 szomszédsági kontrollt is byte-ra visszaadta. Minden kimeneti alfa 255.

**Cáfoló kísérlet:** a `mode="edge"` hipotézis a jobb felső forrássarok
impulzusánál mindkét irány kimenetére 224-et jósolt; a natív eredmény
`direction=0`-nál 96, `direction=1`-nél 160 volt. A jobb felső forráspixel
(az alapesetből) és a 2×2-es szomszédság további három külön impulzusa a
natív jobb felső kimeneti pixelben az alábbi együtthatókat adta vissza
(`128 + k·64/4`); mind egyezett a táblázat offsetjeiből levezetett
képlettel:

| forrás a jobb felső célpixelhez képest | `direction=0` natív `k` | `direction=1` natív `k` |
|---|---:|---:|
| `TL = (−1, 0)` | 0 | 4 |
| `C = (0, 0)` | −2 | 2 |
| `BL = (−1, 1)` | 4 | 0 |
| `B = (0, 1)` | −2 | −6 |

A jobb felső sarok 2×2-es szomszédságában legyen `TL = kép[0, W−2]`,
`C = kép[0, W−1]`, `BL = kép[1, W−2]`, `B = kép[1, W−1]`. A natív súlyozott
összeg ott:

| irány | jobb felső sarok natív összege `Σ` |
|---:|---|
| 0, `[-2 0 2; -4 0 4; -2 0 2]` | `4·BL − 2·B − 2·C` |
| 1, `[2 4 2; 0 0 0; −2 −4 −2]` | `4·TL + 2·C − 6·B` |

A `clamp((512 + Σ) idiv 4, 0, 255)` köré épülő jelenlegi NumPy-modellben
ehhez elég a szokásos edge-padded összeg jobb felső elemét felülírni
(minden tömb `int32`):

```python
if kernel_is_direction_0:
    total[0, -1] = 512 + 4 * bottom_left - 2 * bottom - 2 * corner
else:  # direction 1
    total[0, -1] = 512 + 4 * top_left + 2 * corner - 6 * bottom
```

ahol a négy lokális érték rendre `kép[1,−2]`, `kép[1,−1]`,
`kép[0,−2]` és `kép[0,−1]`, képcsatornánként. Ez a felülírás a natív
`3×3`-as vagy nagyobb képmérethez tartozik; a két natív függvény
`szélesség < 3` vagy `magasság < 3` esetén a feldolgozás előtt visszatér
(`0x00bb68e4`–`0x00bb6903`, `0x00bb6cf1`–`0x00bb6d06`).

**A teljes EdgeDetectionB-lánc mérése nem sikerült.** A `0x00bbca60`
XML-creator/felépítő QEMU-hívása a CRT locale-kezelő útján SIGSEGV-vel állt
meg (`0x00bf19e6` → `0x00bf19f5` → `0x00bf0583`); a harness CRT-shimje nem
inicializál valódi locale-állapotot. Nem született érvényes teljes
`Blur → SimpleColorMatrix → Sobel → AdjustCurves → Multiply` kimenet, ezért
a Fade 0/50 XML-paraméterezés bájt-összevetése **NINCS MEG**. A következő
út az eredeti CRT locale-állapotát is létrehozó kontrollált QEMU-belépő,
majd a teljes lánc két Fade-értéken; a korábbi önálló `BlendAlpha=0.5`
keverőpróba ezt nem helyettesíti.

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

##### A `SimpleBorder` pixelrácsa és alfája — natív QEMU-val (2026-10-04, #626)

Az `apply` (`0x00bbf4a0`) a négy attribútumot a `0x00bbf630`-on keresztül
olvassa, majd a `0x008eea90`-en egészre alakítja. **A megadott, nemnegatív
értéktartományban ez csonkítás 0 felé, nem kerekítés**: a konverzió a
vezérlőszó kerekítési módját `0xc00`-ra állítja (`0x008eeaa4`–`0x008eeabb`,
`0x008eeacf`–`0x008eeae6`). Az alkalmazó közvetlenül hozzáadja a kapott
egészeket a forrás szélességéhez és magasságához (`0x00bbf515`–`0x00bbf536`):

```text
L = trunc0(left)   R = trunc0(right)
T = trunc0(top)    B = trunc0(bottom)
W' = W + L + R    H' = H + T + B
```

Itt nincs képméretarányos tényező. A `0x00bbf4e0`–`0x00bbf510` az alfa-bájtot
`0xff`-re állítja; a teljes célképet ezután a `0x009a91a0` a keretszínnel
tölti ki, majd a `0x009aabf0` a forrást `(L,T)` helyre másolja. A másolási út
`0xbf2350`-et hívja. Nincs alfakeverés vagy sarokmaszk: a keret négy sarkában
is a kitöltőszín marad, a bemásolt képpontok négy BGRA-bájtja — köztük az
alfája — változatlan.

| Próba | Natív QEMU-kimenet | PicasaPy `add_border_sides()` |
|---|---|---|
| 3×2 BGRA, `L/R/T/B = 1/3/2/1`, `color=0x1280e040` | 7×5, stride 7; a keret BGRA `(64,224,128,255)`; a képrész alfái változatlanok | RGB-mátrix bájtra egyezik |
| 4×3 BGRA, `0.5/1.5/2.5/3.5` | csonkított oldalak `0/1/2/3`, kimenet 5×8 | `round()` után `0/2/2/4`, kimenet 6×9 |
| 4×3 BGRA, `1.9/2.1/0.9/3.9` | csonkított oldalak `1/2/0/3`, kimenet 7×6 | `round()` után `2/2/1/4`, kimenet 8×8 |

A QEMU-próba az eredeti `0x00bbf4a0` alkalmazót és a rajzoló/másoló útját
futtatta, `qemu-i386` és a `qemu_harness/hb.py` CRT-helyettesítőivel. A forrás
és a cél külön képleíró rekordot kapott (`+0x04` stride képpontban, `+0x08`
szélesség, `+0x0c` magasság, `+0x10` BGRA-mutató). Csak a `0x008ef520`
attribútum-kiértékelő kapott shimet, hogy a fenti konkrét értékeket adja vissza;
az `apply`, a konverzió, a célkitöltés és a képmásolás natív kódja változatlanul
futott.

**Két független út:** A) az `0x00bbf4a0`, `0x00bbf630`, `0x008eea90`,
`0x009a91a0` és `0x009aabf0` utasításszintű olvasata; B) a közvetlen natív
QEMU-futtatás. A méretképlet, a csonkítás, a teljesen fedő szögletes keret, a
forrás alfa-bájtjainak megőrzése és a `(L,T)` másolási pozíció egyezik.

**Cáfoló próba:** a képmérethez viszonyított keret hipotézise nem adná a
3×2-es bemenet mellett mért pontos `+1/+3/+2/+1` képpontot; a natív kimenet
ezt adta. A „pozitív törtet kerekít” hipotézist a `0.5/1.5/2.5/3.5` és az
`1.9/2.1/0.9/3.9` kontroll cáfolta. A félátlátszó és teljesen átlátszó
forráspixelek alfája a célban azonos maradt, tehát a forrás nem a keretszínnel
keveredik.

**Eredeti / nálunk / teendő:**

| Tulajdonság | Eredeti | PicasaPy ma | Teendő |
|---|---|---|---|
| Egység és méret | A nemnegatív oldalérték képpont; `W' = W+L+R`, `H' = H+T+B` | `add_border_sides()` pixelként kezeli | Egyezik. |
| Tört oldalérték | `trunc0()` a `0x008eea90` szerint | `int(round(v))` a `glimmer_frame_ops.py:46` sorban | Tört bemenetre eltér. A két ismert leíróhasználat előbb `Math.round()`-dal egész értéket képez (`filterdesc.xml`, `Cinemascope` és `Polaroid`), és mindkét PicasaPy-hívó egész oldalt ad át (`glimmer_creative.py:72`–`73`, `glimmer_frames.py:133`–`139`); ezeknél nincs mért kimeneti eltérés. Ha a segédfüggvény tört SimpleBorder-attribútumot is támogatni fog, a `round()`-ot csonkításra kell cserélni, és a fenti két tört QEMU-esethez rögzített ellenőrzés kell. |
| Szín, alfa, sarkok | A keret alfa-bájtja `0xff`; a forráspixel négy bájtja másolódik; négyzetes sarkok | `uint8 RGB` kimenet, konstansszínű négyzetes keret | Az RGB-művelet egyezik. Az alfa-paritás nincs a jelenlegi RGB-adattípusban reprezentálva; RGBA-út bevezetésekor a forrás alfáját meg kell őrizni, a keretét `0xff`-re kell állítani. |

**Bizonyítottsági fok: megerősített** a nemnegatív, leíróban használt értékekre:
az utasításszintű út és az eredeti függvény QEMU-kimenete egyezik. A negatív
oldalértékek viselkedését ez a mérés nem terjeszti ki; az ismert
`filterdesc.xml`-használatok egész, nemnegatív értéket állítanak elő.

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

#### ⭐ A `Border` sarka és feliratsávja — MÉRVE a Picasa-exporton (2026-09-27, 377. kör, #626)

*Forrás: `684-merokeszlet` `border__max` (`Border=1,100,100,40,00000000,00ffffff,60`, 960 × 640 → 1360 × 1103) · a dinamikus csúszka `0x00bbd3d0` · a feliratsáv egésszé alakítása `0x00bbe553` → `0x008f1490` → `0x008eea90`.*

**1. A feliratsáv magassága — float32-tartomány, csonkítva.** A dinamikus csúszka a `minimum` és a `maximum` kifejezést double-ként értékeli ki, de **float32-be menti** (`fstp dword` @ `0x00bbd40d`, `0x00bbd422`), és ebből vetít: `érték = min + (max − min) · t / 100`. A `captionheight`-et a `0x008eea90` **csonkítva** alakítja egésszé (`or eax, 0xc00` + `fistp`). 640-es képmagasságon: `f32(640/6) = 106,666664`, `· 60/100 = 63,9999985` → **63** képpont. A mi double-számításunk 64-et ad, ezért a kimenetünk **1 képponttal magasabb** (1104 ↔ 1103), és az elcsúszás önmagában ΔE 3,70-et okoz.

**2. A sarok — koncentrikus ívek, közös középponttal.** Soronként mérve (a bal felső sarok, az ív első világos képpontja):

| sor | export | kör, `R + belső = 228`, középpont (328, 328) |
|---:|---:|---:|
| 130 | 213 | 215 |
| 190 | 146 | 146,5 |
| 235 | 119 | 119 |

Az átlón a kép 239-nél kezdődik; az `R = 128` sugarú, ugyanilyen középpontú ívből 237,5 jön ki. ⇒ Az eredeti:
- a **vászon** sarka szögletes, külső színű;
- a **belső sáv** külső éle `R + belső` sugarú lekerekített téglalap, belső színnel;
- a **kép** sarka `R` sugarú, a kimaradó rész belső színű.

A felirat nélküli alsó sarkok ugyanígy viselkednek: a belső sáv téglalapja a feliratsáv fölött ér véget.

**A 2026-09-27-i mérés állapota:** a 4 × 4 almintás modell (`R = 128`, belső = külső = 100, felirat 63) a Picasa-exportot ΔE 0,097-tel adta vissza; a képpontok 0,11 %-a tért el 40 szintnél többel. Az akkori kódról szóló „két szögletes gyűrű” leírás elavult: a jelenlegi `draw_border()` már lekerekített sarokfoltokat épít 4 × 4 mintavételezéssel. A natív `0x00bbe570` rajzoló és a mostani implementáció közti közvetlen, kis képes összevetést az alábbi új szakasz tartalmazza.

*Bizonyítottsági fok: **megerősített** a kimeneti méretre és a koncentrikus geometria exporton mért alakjára; **feltételes** a tetszőleges méretű sarok pontos fedettségi képletére (ld. az alábbi `0x00aa1840` nyitott pontot).* Fejlesztési hivatkozás: #3768.

#### `DropShadowImageOperation` (`0x00bbb720`)

**Az árnyék eltolása** — polárkoordinátából, apró kerekítési igazítással:

> ⛔ **Helyesbítve (2026-09-27, #626):** a kerekítés **`floor`**, nem `round`
> (`0x00bcdece` `call 0x00c0b1e0`). Ld. „A Polaroid geometriája” szakaszt.

```c
dx = floor( (cosf(szog * π/180) + 6.7e-06f) * tavolsag + 0.001825f );
dy = floor( (sinf(szog * π/180) + 6.7e-06f) * tavolsag + 0.001825f );
```

A `6,7e−06` és a `0,001825` nem paraméter, hanem **lebegőpontos védelem**: a
valójában egész, de 2,9999… alakban kijövő szorzatot emeli az egész fölé,
mielőtt a `floor` lecsípné. Át kell venni őket, ha képpontra pontos egyezést
akarunk.

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

A két beállítás tehát két külön szerep: a `borderColor` a kimeneti vászon
háttérkitöltése (`0x00bc8134` → `0x009a91a0`), a `0x00bc832e`-n átadott `1`
pedig a wrapper `smoothing=true` jelzője (`0x00bcb602`). Forgatási mátrixnál
ez utóbbi az affine mintavételező útvonalon marad; nem választ `ytResampler`
módot és nem változtatja meg a háttérszínt.

> ⛔ **MEGDŐLT (2026-08-17; második helyesbítés 2026-10-04):** a Skia-olvasat
> téves volt, és a rá következő `ytResampler`-magyarázat is rossz ágra
> vonatkozott. A `0x00bc8060` forgatási mátrixánál a `0x00bcb5e0` a
> `0x009e6df0` általános transzformációs útját választja, majd a
> `0x009e7060` natív mintavevőt hívja `smoothing = 1` értékkel
> (`0x00bc832e`). A `ytResampler` 0/3-as ága tengelyhez igazított
> átméretezési út; nem a forgatás pixelmagja. A teljes mátrix- és
> mintavételezési levezetés, valamint a natív QEMU-próba lejjebb, „A
> Polaroid geometriája” szakaszban van. A régi Skia/`ytResampler`-értelmezést
> és az arra épülő lezárást ne használd Rotate-bizonyítékként.

#### `CropImageOperation` (`0x00bbdbd0`)

Egyszerű kivágás; a Polaroid a `min(szélesség, magasság)` méretű, **középre
igazított négyzetet** kéri (a képlet a `filterdesc.xml`-ben van).

##### Pixelmatematika (#626, 2026-10-04)

**Mértékegység.** A `filterdesc.xml` a `CropImageOperation` `x`, `y`,
`width`, `height` attribútumait az eredeti kép pixelméreteiből számítja:
`Cinemascope` a `origImageWidth`/`origImageHeight` és `cropWidth`/`cropHeight`
alapján (`filterdesc.xml:751–755`), a `Polaroid` a
`min(origImageWidth, origImageHeight)` alapján (`:1226–1234`). Ezek abszolút
képpont-koordináták és méretek, nem 0…1 arányok. Az attribútum-beolvasó a
négy kifejezést az objektum `+0x24`, `+0x2c`, `+0x34`, `+0x3c` mezőjébe teszi
(`0x00bbd9a0`). Az RTTI szerinti `glimmer::CropImageOperation::vftable`
címe `0x00cf05a0` (RVA `0x008f05a0`); a 6. slot az alkalmazó
`0x00bbdbd0` címre mutat.

**Kerekítés és határok.** A natív alkalmazó (`0x00bbdbd0`) a `x`/`y`
kifejezését `float32`-re alakítja, majd a `0x00c29990` segéddel egészre
csonkolja (`cvttsd2si`). A szélesség és magasság a `0x00bbda60` segéden át
`float32` lesz, majd `0x00529e10` → `0x00c090f0` kerekíti a legközelebbi
egészre, végül `0x00c29990` egészíti ki. A natív téglalap jobb és alsó
végpontja külön képződik: `trunc(x + round(width))` és
`trunc(y + round(height))`; tehát tört `x`/`y` esetén nem az egészre
csonkolt kezdőponthoz adja hozzá a kerekített méretet.

A `0x009a9080` a bal/felső élt nullára korlátozza, a jobb/alsó élt pedig a
bemeneti kép szélességére/magasságára vágja; a képpontokat ezután változatlan
BGRA-bájtokként másolja (`0x009aabf0`). Részben kilógó téglalapnál tehát a
képbe eső metszet készül el, kitöltés és újramintavételezés nélkül. Ha nincs
metszet, a natív hívás `0x4` visszatérési értéket ad, és a célrekord a
bemeneti képre mutató, változatlan méretű rekord marad; ez nem üres kép.

**Két független út.**

| út | eredmény |
|---|---|
| A — utasításszintű | `0x00bbd9a0`, `0x00bbda60`, `0x00bbdbd0`, `0x00529e10`, `0x00c090f0`, `0x00c29990` és `0x009a9080` kiolvasása: abszolút pixelparaméterek, kerekített méret, csonkolt kezdő- és végpont, képhatárra vágás. |
| B — natív QEMU | Az eredeti `0x00bbdbd0` futott a CRT-shimmel és külön forrás-/célrekorddal. A `0x8ef520` paraméterkiértékelő kapott tesztértékeket; a Crop vtable-segéd, képhatár-kezelő és bájtmásoló eredeti kód maradt. A `+0x04` mező stride képpontban, `+0x08/+0x0c` a szélesség/magasság, `+0x10` a BGRA-adatmutató; a belső `+0x14=1` a `0x009a9b30` heap-pufferes ágát választotta. |

A QEMU-kimenetek:

| bemenet | `(x, y; width, height)` | kimenet |
|---|---|---|
| `7×5` | `(1, 1; 3, 2)` | `3×2`, státusz `0`; első sor bájtjai: `0b162166 0c182467 0d1a2768` |
| `7×5` | `(1.75, 1.25; 3.75, 2.5)` | `4×3`, státusz `0` |
| `7×5` | `(1.5, 0.5; 2.5, 1.5)` | `3×2`, státusz `0`; a pozitív `2.5` és `1.5` félérték felfelé kerekült |
| `7×5` | `(-1.75, -0.75; 4, 3)` | `2×2`, státusz `0`; a forrás bal felső `2×2` metszete |
| `7×5` | `(-2, -1; 5, 4)` | `3×3`, státusz `0` |
| `7×5` | `(5, 3; 4, 4)` | `2×2`, státusz `0` |
| `7×5` | `(9, 6; 2, 2)` | státusz `0x4`; a célrekord az eredeti `7×5` képet tartja |
| `8×6` | `(1, 2; 5, 3)` | `5×3`, státusz `0` |

A második utat a nyers rekordméretekből és BGRA-sorokból, az első
utasításolvasatától külön értelmezve is ellenőriztem: a `1.75` kezdőérték az
1. oszlopból indul, a `2.5` szélesség 3 pixel, a részben kilógó esetek a
képen belüli metszetet adják. Ez egyezik az A úttal. Cáfoló kontrollként a
tört kezdőpontot, a pozitív félértékeket, mindkét oldali kilógást és a teljes
kép-kívüliséget választottam; egyik kimenet sem cáfolta a fenti képletet.

**PicasaPy-összevetés.** A `glimmer_frames.apply_polaroid`
(`src/picasapy/render/glimmer_frames.py:115–132`) az effekt konkrét
négyzetes vágását `min(H, W)` és egész `// 2` középeltolással végzi; ez
egyezik a `filterdesc.xml` Polaroid-képletével. A másik jelenlegi használat,
`glimmer_creative.apply_cinemascope`
(`src/picasapy/render/glimmer_creative.py:50–63`), a leíró `Math.round`
méretezését Python `round`-dal, a középeltolást egész `// 2`-vel valósítja
meg; a `cropHeight ≤ origImageHeight` feltétel miatt a `max(0, …)` nem módosítja
a leíró szerinti eredményt. Általános Glimmer
`CropImageOperation(x, y, width, height)` primitív viszont nincs. Az
`ops.apply_crop` (`src/picasapy/render/ops.py:69–90`) más szerződésű:
normalizált `Rect64`-et vesz át, a négy élt Python `round`-dal képpontra
képezi, és üres vágásnál kivételt dob. Ez nem helyettesíti a Glimmer Crop
pixelmatematikáját.

**Bizonyítottság: megerősített** a kért pixelmatematikára: az utasításolvasat
és az eredeti alkalmazó QEMU-kimenete egyezik. A közös, általános Crop
primitív nálunk hiányzik; a meglévő Polaroid-specifikus középvágás a saját
leírójának egész pixelparamétereire egyezik.

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
| `Crop` | `0x008f05a0` | `0x00bbd9a0` | `0x00bbdbd0` (227 b) | — | x@0x24, y@0x2c, width@0x34, height@0x3c *(teljes: H) pont)* |
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
| `SimpleBorder` | `0x008f06cc` | `0x00bbf280` | `0x00bbf4a0` (391 b) | — | left@0x24, right@0x2c, top@0x34, bottom@0x3c, color@0x44 *(teljes: H) pont)* |
| `SimpleColorMatrix` | `0x008effb4` | `0x00bb62c0` | `0x00bc16b0` (428 b) | `0x00bb6400` (296 b) | saturation@0x28, contrast@0x30, brightness@0x38, ContrastAndBrightnessLinked@0x48 |
| `Tint` | `0x008f0554` | `0x00bbd630` | `0x00bbf920` (6 b) | — | nincs saját tag: a `color` helyi változó → két gyerek (`ColorMatrix` s = −100 + `Resaturate`); ld. H) pont |
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
- ~~A `Tint`, a `Crop` és a `SimpleBorder` sora **hiányos**: a `red.cfg`
  több nevet sorol (`x`/`y`, illetve `top`/`left`), mint amennyit a minta
  megtalált.~~ → **LEZÁRVA (2026-09-26, #626):** mindhárom teljes, ld. „H) A `Tint` belseje” pont.
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

### Az `imageOperations` attribútumainak hiánya: objektum-kezdőállapot (#626, 2026-10-05)

Ez a tábla a natív műveletobjektum **létrehozása utáni, az attribútumolvasó
előtti mezőállapotot** rögzíti. Nem azonos azzal az értékkel, amit egy
képpont-végrehajtó hiányzó attribútumnál később használhat: egyes végrehajtók
külön, helyi alapértéket adnak a getternek (példák lentebb). `NULL` = nincs
eltárolt attribútum-/tömbcsomópont; `0` = nullázott skalármező; `0/NULL` = a
mező reprezentációja az adott tagtől függ, a kezdő bitminta nulla.

**A hiányzó attribútum útja.** A gyár (`0x00bb31f0`) a tag neve alapján
allokál és vagy a művelet konstruktorát hívja, vagy maga nullázza a mezőket.
Ezután virtuálisan hívja az attribútumolvasó 1. rését
(`0x00bb3c8c`–`0x00bb3c98`). A típusolvasók a `0x008eb160`-nal keresik a
nevet; hiányzó csomópontnál átugorják a tárolást, jelenlévőnél a
`0x008eb520`-szal vagy közvetlen mezőírással módosítanak. Így a hiányzó tag
kezdőállapota megmarad.

| XML-elem | Műveletsaját attribútummezők | Hiányzó attribútum: mező kezdete | Inicializáló út | Fok |
|---|---|---|---|---|
| `AdjustCurves` | `MasterCurve`, `RedCurve`, `GreenCurve`, `BlueCurve`; `ExposureAdjustmentStops` | görbepontok `NULL`; stops `0`; attribútum nélküli `+0x28=7` | `0x00bb9990` | Q |
| `AutoFix` | — | nincs XML-hez kötött műveletsaját mező; attribútum nélküli `+0x28=7` | `0x00bb31f0`, inline | S |
| `BW` | `filtercolor` | `NULL` | `0x00bb31f0`, inline | S |
| `Blur` | `xblur`, `yblur`, `quality` | `NULL` | `0x00bb31f0`, inline | S |
| `Border` | `outercolor`, `innercolor`, `cornerradius`, `innerthickness`, `outerthickness`, `captionheight` | `NULL` | `0x00bbdf10` | S |
| `CircularGradientImageMask` | `width`, `height`, `xCenter`, `yCenter`, `innerRadius`, `outerRadius`, `innerAlpha`, `outerAlpha` | `NULL` | `0x00bc29b0` | S |
| `ColorMatrix` | `Matrix`; `UseAlpha` | `Matrix=NULL`; a `UseAlpha` útját a típusolvasó nem kezeli | `0x00bc1570` | Q; `UseAlpha` nyitott |
| `Crop` | `x`, `y`, `width`, `height` | `NULL` | `0x00bbd880` | S |
| `DropShadow` | `distance`, `angle`, `blurX`, `blurY`, `strength`, `quality`, `shadowColor`, `shadowAlpha`, `backgroundColor` | `NULL` | `0x00bbb120` | Q |
| `EdgeDetectionB` | `detail` | `NULL` | `0x00bb31f0`, inline | S |
| `GetVar` | `Name` | `NULL` | `0x00bb31f0`, inline | S |
| `Glow` | `color`, `glowalpha`, `xblur`, `yblur`, `strength`, `quality`, `innerglow`, `knockout` | `NULL` | `0x00bb8a60` | S |
| `GradientMap` | `gradientArray` | tömbcsomópont `NULL`; attribútum nélküli `+0x28=7` | `0x00bb8690` | Q |
| `HSVGradientMap` | `gradientObjectArray`, `hueOffset` | tömbcsomópont `NULL`; `hueOffset=0`; attribútum nélküli `+0x28=7` | `0x00bbc0e0` | Q |
| `IR` | `greenglow`, `greenglowalpha`, `redweight` | `NULL` | `0x00bc3c40` | S |
| `LocalContrast` | `Radius`, `Strength` | `NULL` | `0x00bc40e0` | S |
| `MultiplyColorMatrix` | `Multiplier` | `NULL` | `0x00bb7680` | S |
| `Nested` | közös `Blend`-mezők; `id` | közös mezők 0/NULL; hiányzó `id` esetén nincs névvel ellátott regiszter | `0x00bb31f0`, inline | S |
| `Noise` | `randomSeed`, `low`, `high`, `channelOptions`, `grayScale` | `NULL` | `0x00bbed20` | S |
| `Pixelate` | `pixelWidth`, `pixelHeight`, `offsetX`, `offsetY` | `NULL` | `0x00bbcf30` | S |
| `QuantizePalette` | `Steps`, `Depth` | nyers tagmezők `0` | `0x00bb31f0`, inline | S |
| `RadialBlur` | `amount`; `x`, `y`, `Mask`, `ignoreObjects` | `amount=NULL`; a többi nem szerepel a típus attribútumtag-táblájában | `0x00bb31f0`, inline | S; a további mezők nyitottak |
| `Resize` | `width`, `height`, `smoothing`; `ignoreObjects` | a három művelettag 0/NULL; `ignoreObjects` nincs a típus tagtáblájában | `0x00bb31f0`, inline | S |
| `Rotate` | `radAngle`, `degAngle`, `borderColor`, `flipH`, `flipV`, `padBorder` | `NULL` | `0x00bb50f0` | S |
| `SetVar` | `Name` | `NULL` | `0x00bb31f0`, inline | S |
| `SimpleBorder` | `left`, `right`, `top`, `bottom`, `color` | `NULL` | `0x00bbf130` | S |
| `SimpleColorMatrix` | `Saturation`, `Contrast`, `Brightness`, `ContrastAndBrightnessLinked` | `NULL` | `0x00bb6150` | S |
| `TiledImageMask` | `tileWidth`, `tileHeight`, `scaleWidth`, `scaleHeight`, `paddingLeft`, `paddingTop`, `paddingRight`, `paddingBottom`, `offsetX`, `offsetY`, `alphaMin`, `alphaMax` | mind a 12 attribútumcsomópont `NULL` | `0x00bb9fd0` | Q |
| `Tint` | `Color` (lokális bemenet, nincs saját adattag) | a lokális csomópont `NULL`; ebből a belső `Resaturate` színének hiányzó-érték útja nyitott | `0x00bb31f0`, inline | S |
| `TwoTone` | `whiteColor`, `blackColor` | színcsomópontok `NULL`; attribútum nélküli `+0x28=7` | `0x00bc2720` | Q |

`S` = utasításszintű inicializáló- és attribútumolvasó-olvasat, `feltételes`;
`Q` = ugyanez egyezett az eredeti gépi kóddal végzett `qemu-i386`-próbában,
`megerősített` a konstruktor kezdőállapotára. A QEMU-próbák az objektummezőket
`0xA5` bájttal előtöltve futottak: `AdjustCurves` (`0x00bb9990`),
`ColorMatrix` (`0x00bc1570`), `DropShadow` (`0x00bbb120`),
`GradientMap` (`0x00bb8690`), `HSVGradientMap` (`0x00bbc0e0`), `TwoTone`
(`0x00bc2720`) és `TiledImageMask` (`0x00bb9fd0`). A vtable és a mezőminták
egyeztek a diszasszemblálással; a `+0x28=7` értéket az
`AdjustCurves`/`GradientMap`/`HSVGradientMap`/`TwoTone` konstruktorpróba is
visszaadta. Az `AutoFix` inline ágán ugyanezt az értéket a
`0x00bb31f0` utasításai állítják be. Ez a `+0x28` mező nem szerepel az XML
attribútumtáblában. Az inline inicializáló ágak QEMU-futtatása és a parser
teljes attribútumútja nem történt meg; azokra az `S` fok érvényes.

**Cáfoló próba (15.2).** A kezdeti állítás, hogy *minden objektummező*
nulláról indul, megdőlt: a `GradientMap` konstruktor `+0x28` mezője `7`.
Az eltérés nem XML-attribútum: a név szerinti attribútumtáblában nincs ehhez
a mezőhöz kulcs. Ugyanennek a cáfolatnak a kontrollja a négy QEMU-val mért
konstruktor: az `AdjustCurves`, `GradientMap`, `HSVGradientMap` és `TwoTone`
mind `+0x28=7`-et ad, az utasítások is ezt írják. A leszűkített állítás ezért
csak az XML-attribútumhoz rendelt mezőkre szól: azok 0/NULL kezdőállapotúak,
amennyiben az attribútumolvasó nem talál hozzájuk csomópontot. A hiányzó
`gradientArray` futásidejű olvasóját külön QEMU-ban nem hívtam meg; a
`0x00bb8710` jelenléti ága és a `0x00bb8690` `+0x40=0` kezdete ezt
utasításszinten támasztja alá, ezért ez az utolsó lépés `feltételes`.

**Közös `Blend`-attribútumok.** A műveletobjektumok közös mezői hiányzó
`BlendMode`, `BlendAlpha`, `Mask` és `maskWithSourceAlpha` mellett rendre
`0`, `0`, `NULL`, `false` kezdőállapotúak; a közös olvasó (`0x00bc4900`)
csak talált attribútumnál írja őket. A `BlendAlpha` mező nyers nullája nem a
képpontkeverő alapértéke: a végrehajtó hiányzó értéknél `1,0`-t használ
(`0x00bd0742`–`0x00bd0778`). A `dynamicParamsCachePriority` és
`dynamicAlphaCachePriority` a dinamikus csomópont metaadata; a közös olvasó
csak jelenlévő attribútumnál állítja (`0x00bc49dd`–`0x00bc4a2c`,
`0x00bc4a2f`–`0x00bc4a7e`).

**A nyers kezdőérték és a pixelvégrehajtó visszaesése külön adat.** Már
kimért példák: a `Blur` hiányzó `xblur`/`yblur` értékéhez a getter `1,0`-t
ad (`0x00bb4de0`); a `Resize.smoothing` nyers kezdete nulla, a végrehajtó
viszont `true`-t készít elő (`0x00bc36ac`); a `DropShadow` paraméterépítője
`shadowAlpha=1`, `angle=45`, fekete szín, `distance=4`, `strength=1`,
`blurX=blurY=4` alapértékekkel indul (`0x00bbb8d0`); a `QuantizePalette`
végrehajtó `Steps=255`, `Depth=2` értéket használ (`0x00bb5aed`,
`0x00bb5b1d`). Ezek nem a konstruktor nyers mezői.
Ugyanilyen különbség a `TiledImageMask`: az objektumtagok nulláról indulnak,
míg a paraméterépítő `0x00bba250` a `scaleWidth`/`scaleHeight` értékére
`0,8`-at, az `alphaMax`-ra `1,0`-t, a többi felsorolt mezőre nullát ad.

**A szín- és gradiensszöveg formátuma: csak a szállított alak bizonyított.**
A tényleges XML-ben a `GradientMap` listája `[0x000000,0x57cc29]`
(`filterdesc.xml:1135`), statikus színek `0xRRGGBB` alakban szerepelnek
(`Color="0xfcff00"`, `:836`; `SimpleBorder color="0xffffff"`, `:1235`),
és dinamikus ARGB-értékek explicit `0xff000000 + …` kifejezésből épülnek
(`DropShadow`, `:854`, `:1236`). `color="0"` is előfordul. A vizsgált
színattribútumok között `#RRGGBB` és nemnulla decimális szín nem szerepel;
ez a fájlban használt alakokat írja le, nem parser-elutasítási bizonyíték.
Az attribútumolvasók a `gradientArray` / `gradientObjectArray` csomópontot
adják tovább (`0x00bb8710`, `0x00bbc190`); a `0x008ef520` tényleges
kifejezéskiértékelőjét és a listaelemek szöveges színértelmezését ez a kör
nem futtatta. Ezért a `#RRGGBB`, a nemnulla decimális szín, a közvetlen
`0xAARRGGBB` literál elfogadása, valamint a `GradientMap` XML-stopok
RGB-bájtsorrendje **nyitott**. A `ColorMatrix.UseAlpha` (az XML-ben
`true`, `:797`, `:811`) típusolvasó-útja szintén nyitott.

**PicasaPy-összevetés.** A projektben nincs `filterdesc.xml`-ből
`imageOperations`-tagokat beolvasó futásidejű parser. A `registry.py` és
`registry_data.py` a csúszka-/effektregisztert a specből kézzel felvett
adatból építi; a `chain_glimmer_handlers.py` pozíciós `.picasa.ini`
`FilterOp`-paramétereket dolgoz fel, saját hiányzóparaméter-alapértékekkel.
Ezért nincs az XML műveletobjektum mezőire 1:1-ben összevethető betöltői
érték, és ebből a leletből nem következik termékkód-módosítás.

*Bizonyítottsági fok: **feltételes** az összes XML-elemre kiterjesztett
kezdőállapot-táblára (utasításszintű olvasat; hét konstruktor QEMU-val
ellenőrizve), **megerősített** a hét Q-val jelölt konstruktor nyers
mezőkezdeteire; **feltételes** a közös olvasó jelenléti kapujára; **nyitott** a teljes
XML-kiértékelésre, a szöveges szín/gradiens grammatikára és a felsorolt
végrehajtói fallbackoktól eltérő, még nem vizsgált getterekre.*

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

#### Pixelmag, közös alkalmazók és natív bájtmérés (#626, 2026-10-04)

A szállított paraméterezés a `Picasa3/runtime/filterdesc.xml:1002` sorban
explicit: `greenglow=5`, `greenglowalpha=0.25`, `redweight=-0.5`, a külső
`BlendAlpha = 1 − Fade/100`. A `Fade` csúszka tartománya 0…100, alapja 0
(`filterdesc-registry.md` 4.2). A `greenglow`, `greenglowalpha` és
`redweight` XML-értékei megegyeznek az `IRImageOperation` getterei elé tett
bináris alapértékekkel (`0x00bc3f5c` → `0x00cf3a58`, `0x00bc3f8a` →
`0x00c7c608`, `0x00bc3fae` → `0x00cf3ea0`).

Az eredeti konstruktor (`0x00bc3d80`) a belső `NestedImageOperation` alá
teszi a zöldcsatornás `ColorMatrix`-et és a `Blur`-t, a záró `ColorMatrix`
pedig közvetlen gyerek (`this+0x4c`); ebben az `IR`-csővezetékben nincs külön
LUT-gyerek. A blur gyártója `0x00bb4c40(5,5,3)`, vagyis `xblur=5`,
`yblur=5`, `quality=3`. Az alkalmazó (`0x00bc3f50`) a
`greenglowalpha` értéket a belső `BlendAlpha`-ba, az 5-öt mindkét blur
tengelyre írja; a záró mátrixot a `0x00bc14e0` mátrixbeállítóval adja át.
Az első mátrix műveleti kimenete `(0,G,0,A)`; a záró mátrix a fenti
`r, 2, −1−r` hármast alkalmazza.

A belső keverési módot a konstruktor `0x00bc3e49 push 7` utasítása adja át
az `0x008eedc0` beállítónak. A módnévtábla `0x00cf0e98` szerint a 7-es
`Screen`; a diszpécsertábla `0x008f4c48` 7. bejegyzése a Screen-maghoz
(`0x008f5d20`) vezet. Tehát a tényleges sorrend:

```text
ColorMatrix: (R,G,B,A) → (0,G,0,A)
Blur:        xblur = yblur = 5, quality = 3
Blend:       Screen az eredeti képre, BlendAlpha = 0.25
ColorMatrix: RGB = clamp(−0.5·R + 2·G − 0.5·B), A változatlan
Fade:        BlendAlpha = 1 − Fade/100
```

A Screen minden csatornára (az alfára is) alkalmazott egész képlete:
`⌊(65025 − (255−b)(255−t)) / 255⌋`; itt `b` az eredeti, `t` az elmosott
zöldréteg. A `/255` csonkol, a Fade súlyozott keverése pedig a következő,
ettől különálló lépés (`BlendInstruction`-szakasz C pont).

A két színmátrix a közös `ColorMatrix` utat járja (`0x00bc16b0` →
`0x008f2500` → `0x008f21a0` → `0x008f2640`). A Q11-egész konverzió,
csatornasorrend, szorzatonkénti `sar 9`, bias és telítés képlete a 4.9-es
`ColorMatrix`-szakaszban szerepel. A blur alkalmazója `0x00bb4de0`, a közös
blur-diszpécser `0x00bc5680`. A belső Screen-keverést és a külső Fade-et a
közös `BlendInstruction` (`0x00bd0700`) és pixelkeverő (`0x009dc4b0`)
végzi. A közös súly `w = trunc(256·alpha)`, majd ha `w>0`, `w−1`; a páros
pixelképlet `(b·(255−w)+t·w)>>8`, páratlan szélesség sorvégi skalárképlete
`t + ((b−t)·w >> 8)` (lásd `glimmer_ops.alpha_blend`, `0x00bd0700`,
`0x009dc4b0`). Így a belső `alpha=0.25` súlya 63; `Fade=50` esetén a külső
`alpha=0.5`, súlya 127; `Fade=0`-nál a végrehajtó az `alpha≈1` ágat másolja.

**Natív bájtmérés.** Az eredeti `Picasa3.exe` fenti konstruktorát,
alkalmazóit, blur- és blendkódját futtattam `qemu-i386` alatt. A harness a
kézzel épített IR-objektumhoz a fenti XML-értékekkel egyező natív
alapértékeket használta; az üres paraméterlistánál az eredeti getterek
ezeket olvasták ki. A Fade-kifejezés eredményét az eredeti
`BlendInstruction` kapta. A QEMU-képleíróban `+0x04=stride` pixelben,
`+0x08=szélesség`, `+0x0c=magasság`, `+0x10=BGRA-adatmutató`; az alfa minden
bemeneti pixelben 255. A determinisztikus bemenet:
`B=(17+31x+7y) mod 256`, `G=(29+23x+11y) mod 256`,
`R=(43+19x+13y) mod 256`, `A=255`, `x=0…W−1`, `y=0…1`.

| Méret | Fade | Eredeti natív kimenet, BGRA hex | Összevetés a `glimmer_creative.apply_ir`-ral |
|---:|---:|---|---:|
| 4×2, páros | 0 | `2d2d2dff464646ff5f5f5fff747474ff3d3d3dff545454ff6b6b6bff808080ff` | 0/32 eltérő bájt |
| 4×2, páros | 50 | `1e242bff3a3c41ff565457ff706a6bff2a323aff45494fff606064ff7a7678ff` | 0/32 eltérő bájt |
| 5×2, páratlan | 0 | `2f2f2fff464646ff5f5f5fff767676ffc0c0c0ff3d3d3dff545454ff6d6d6dff848484ffcececeff` | 0/40 eltérő bájt |
| 5×2, páratlan | 50 | `1f252cff3a3c41ff565457ff716b6cffa69c9bff2a323aff45494fff616165ff7b7779ffb1a9a9ff` | 0/40 eltérő bájt |

A közös első mátrix külön QEMU-kontrollja: BGRA `11 1d 2b 47` →
`00 1d 00 47`, vagyis csak a zöld csatorna és az alfa marad. A négy teljes
futtatás összesen 144 BGRA-bájtot adott; a jelenlegi aktív renderer
RGB-kimenetét BGRA-sorrendre alakítva mind a 144 egyezett.

**Cáfoló próba.** A korábbi `LIGHTEN` hipotézist ugyanazzal a 4×2-es
bemenettel és natív keverővel ellenőriztem: a módot a belső objektumban
7-ről 4-re állítottam. A táblában 4=`Lighten`, 7=`Screen`. Fade 0-nál a
Lighten-vezérlés `212121ff323232ff454545ff5a5a5aff2d2d2dff3e3e3eff515151ff666666ff`,
míg a konstruktor szerinti Screen-kimenet a fenti 4×2-es Fade 0 sor.
**24/32 bájt tér el, mind a 24 RGB-bájt, legfeljebb 26-tal**; az alfa
változatlan. A Python Lighten-kontroll a mód 4 natív kimenetével bájtra
egyezik, a Screen-kimenettel nem. Ez cáfolja a LIGHTEN olvasatot, és az
ellenpróbát ugyanazzal a natív bájtmércével igazolja.

**Bizonyítottsági fok: megerősített** a deklarált paraméterekkel, a
műveletsorrenddel és a négy mért konfiguráció kimenetével: A) utasításszintű
út az `IR` konstruktorától/alkalmazójától a ColorMatrix-, Blur- és
Blend-közös motorokig; B) az eredeti gépi kód teljes QEMU-futtatása és
bájt-egyezés az aktív rendererrel. A QEMU input-képek szintetikusak; nem
állítanak kimerítő, minden lehetséges 8 bites pixelt lefedő enumerálást, és
a teljes Picasa UI/XML-betöltőt sem futtatják.

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

#### Pixelmag, mátrixút és bájtmérés (#626, 2026-10-04)

**A mátrix eredete és a közös út.** A `0x00bb77a0` műveletépítő a
`multiplier` értékét float32-ként teszi a sorfolytonos 4×5 mátrix főátlójának
első három helyére; a negyedik átlóelem 1, a többi elem 0. A vtable 6. rése
`0x00bc16b0`; ez a közös alkalmazó a mátrix-építőt a vtable `+0x20` helyén
kéri le, majd a `0x008f2500` útján adja a mátrixot a `0x008f21a0`
Q11-konverternek és a `0x008f2640` pixelkernelnek. Nincs köztes mátrixszorzás:
a művelet az aktuális 8 bites képre alkalmazza a saját mátrixát. A ColorMatrix
azonos közös alkalmazót használja, de a saját builderével (`0x00bc1860`).

A konverzió és az alkalmazás képlete ezért a 4.9-es ColorMatrix pixelmagjának
szűk esete. `m32 = float32(multiplier)`, `x` pedig az adott RGB-bájt:

```text
q     = round-away(2048 * m32)                 ; 0x008f21a0, Q11 int16
ki    = clamp((sar32(q * x, 9) + 2) >> 2, 0, 255)  ; 0x008f2640
alfa  = x_alfa                                 ; q_alfa = 2048, eltolás = 0
```

`round-away(v) = trunc(v + (v < 0 ? -0,5 : +0,5))`; a `sar32` előjeles,
lefelé tolás. Ennél a diagonális, eltolás nélküli mátrixnál a Q11-konverzió
és a szorzatonkénti `sar 9`, majd a `+2` és a `sar 2` együtt alkotják a
pixelkerekítést. Az alfa-együttható 2048, így az alfa-bájt változatlan.

**Két független út.** A) Az eredeti bináris utasításainak célzott olvasása a
`0x00bb77a0` buildertől a `0x00bc16b0` alkalmazón és a `0x008f21a0`
konverteren át a `0x008f2640` pixelkernelig kiadja a fenti elemeket,
sorrendet és műveleteket. B) Az eredeti builder, alkalmazó, konverter és
pixelkernel `qemu-i386` alatt futott; az RGB bájtok kimenete egyezik a fenti
képlet közvetlen számításával. A tesztértéket az XML dinamikus
paraméter-kiolvasójának (`0x008ef520`) helyettesítője adta; a harness szükséges
CRT-shimjei mellett a mátrixépítő, a közös alkalmazó és a pixelfüggvény
eredeti bináriskód volt.

**Bájtmérés — az eredeti kontra a #4172 előtti helyi modell.** A `filterdesc.xml` LocalContrast csúszkája `1…3` tartományú,
`1,5` alapértékkel; a két MultiplyColorMatrix gyerek ugyanazt az értéket kapja
(`filterdesc.xml:1012–1029`). A tesztelt `1`, `1,5`, `2`, `3` értékből az
első, második és negyedik tehát a deklarált minimum, alapérték és maximum; a
`2` egy pontos, tartományon belüli próbaérték. Szintetikus, determinisztikus
BGRA-bemenet futott 2×2 és 3×2 méreten; `x=0…width−1`, `y=0…1` mellett
`B=(17+31x+7y) mod 256`, `G=(29+23x+11y) mod 256`,
`R=(43+19x+13y) mod 256`, `A=(71+17x+5y) mod 256`. A táblázat a három színcsatorna
összevetése; `eltérő/max` a nem egyező RGB-bájtok száma és a legnagyobb
abszolút bájtkülönbség. `Multiply` az eredeti műveletet hasonlítja a
`_szorzott_resz`-hez; `Fade 50` az eredeti `0x009dc4b0` keverőt a
`alpha_blend`-hez ugyanazzal a forrás- és Multiply-kimenettel; `együtt` a
a kétlépéses Python-részmodellt az eredeti két lépéssel.

| multiplier | méret | Multiply | Fade 50 önmagában | együtt, Fade 50 |
|---:|---:|---:|---:|---:|
| 1 | 2×2 | 0/12, max 0 | 0/12, max 0 | 0/12, max 0 |
| 1 | 3×2 | 0/18, max 0 | 6/18, max 1 | 6/18, max 1 |
| 1,5 | 2×2 | 4/12, max 1 | 0/12, max 0 | 0/12, max 0 |
| 1,5 | 3×2 | 6/18, max 1 | 5/18, max 1 | 5/18, max 1 |
| 2 | 2×2 | 0/12, max 0 | 0/12, max 0 | 0/12, max 0 |
| 2 | 3×2 | 0/18, max 0 | 6/18, max 1 | 6/18, max 1 |
| 3 | 2×2 | 0/12, max 0 | 0/12, max 0 | 0/12, max 0 |
| 3 | 3×2 | 0/18, max 0 | 6/18, max 2 | 6/18, max 2 |

Fade 0 a Multiply-oszlopnak felel meg: a külső keverés elhagyható. Fade 50-nél
a páratlan szélesség eltérései kizárólag minden sor utolsó oszlopára esnek.
A natív keverő páros pixelpár-képlete mellett az utolsó pixel skalárképlete
`T + ((B − T) * w >> 8)` (`0x009dc646`–`0x009dc6fb`); Fade 50-nél az alfa
`0,5`, a belső súly `w=127` (`trunc(0,5*256)=128`, majd a natív `−1`). A
Python `alpha_blend` jelenleg a páros képletet használja minden pixelre
(`glimmer_ops.py:151–170`). A LocalContrast XML-ben nincs Fade csúszka, ezért
ez a Fade 50 mérés a közös külső keverő izolált kontrollja, nem a teljes
LocalContrast effekt export-goldenje.

**Cáfoló kísérlet (a #4172 előtti modell).** A cáfolható hipotézis az volt, hogy a
float32-szorzás és `np.rint` bájtra reprodukálja a natív Multiply műveletet.
`multiplier=1,5` és a BGRA `[17,29,43,71]` pixel ezt cáfolja: a natív
`[26,44,65,71]` bájtokat ad, míg a PicasaPy RGB-kimenete `[64,44,26]` (a
natív RGB `[65,44,26]`). A csatornasorrendet a B és G egyezése, az alfa
átengedését az alfa-bájt egyezése ellenőrzi. A teszt ugyanazt a bájt- és
QEMU-mércét használja, mint a többi kontroll; az eltérés a félértéknél
ties-to-even `np.rint` és a natív Q11 + `+2`/`sar 2` kerekítés különbségét
mutatja.

**#4172 után:** a vektorizált helyi Q11-képlet a fenti, QEMU-val mért
pixelképletet használja. A byte-exact teszt a `1`, `1,5`, `2`, `3` szorzókat
2×2 és 3×2 RGB-képeken ellenőrzi; mind a nyolc esetben eltérés nélkül egyezik
a skalár referenciával. A 4/12 és 6/18 eltérés a fenti táblázatban a #4172
előtti `np.rint`-modellt írja le.

#### Eredeti / nálunk / teendő

| | Eredeti, mért | PicasaPy forrása | Teendő |
|---|---|---|---|
| MultiplyColorMatrix pixelmag | Q11: `round-away(float32(m)·2048)`, majd `((sar(q·x,9)+2)>>2)` és 8 bites vágás; alfa változatlan (`0x00bb77a0` → `0x00bc16b0` → `0x008f21a0` → `0x008f2640`) | `_szorzott_resz`, `src/picasapy/render/glimmer_ops.py`: vektorizált Q11-egész képlet; az aktuális 8 bites műveleti bemenetet szorozza | **#4172 kész:** a mért `1`, `1,5`, `2`, `3` esetek 2×2 és 3×2 méreten bájt-exakt teszttel fedettek. |
| Fade 50, páratlan szélesség | A sorvégi skalárpixel `T+((B−T)·w>>8)`, `w=127`; a teszt 3×2 méretén a hibák csak a 3. oszlopban vannak (`0x009dc646`–`0x009dc6fb`) | `alpha_blend`, `src/picasapy/render/glimmer_ops.py:151–170`, a páros képletet minden pixelre alkalmazza | A páratlan szélességű sor utolsó pixelét a natív skalárképlettel számolja; a 2×2 kontroll maradjon változatlan, és a fenti Fade 50 minták legyenek byte-goldenek. |

**Bizonyítottsági fok:** `megerősített` a MultiplyColorMatrix pixelmagjára,
mátrixára és közös alkalmazóútjára — A) utasításszintű olvasás, B) az eredeti
bináris futtatása qemu-i386 alatt, egyező pixelbájtokkal. A felsorolt
szintetikus mérések nem fedik le a teljes `filterdesc.xml` LocalContrast
láncot, annak blur-/blend-határait vagy export-goldenét; ez a nagyobb effekt
szintjén nyitott marad.

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

#### Az RGB-megállók interpolációja — képlet, LUT és perem (#4090, 2026-10-03)

*Forrás: `0x00bb8710`, `0x00bb87b0`, `0x00bb85b0`, `0x00bb84a0`,
`0x00c29990`; megerősítés az eredeti gépi kód futtatásával `qemu-i386` alatt.*

A `GradientMap` beolvasója (`0x00bb8710`) a `gradientArray`-t (`0x00cf010c`)
a művelet `+0x40` mezőjébe teszi. A munkavégző (`0x00bb87b0`) a megállók
színértékeit olvassa be, és a megállópozíciókat a darabszámból állítja elő.
`n ≥ 2` megállónál a tárolt float32 pozíciók:

```
p[0] = 0
p[n−1] = 255
p[k] = float32(k · 255 / (n−1)),  1 ≤ k < n−1
```

Az első pozíciót a `fldz`/`fstp dword` állítja elő (`0x00bb88cf`–`0x00bb88d3`),
a belső pozíciókat a `0x00cf39d0` double **255,0** konstanssal végzett
szorzás/osztás és float32 tárolás (`0x00bb88e4`–`0x00bb891b`), a záró
pozíciót a `0x00cf3a00` float **255,0** (`0x00bb8925`–`0x00bb892d`). Ezért
a `TwoTone` két színe a **0 és 255** indexhez tartozik; a korábbi 0 és 1
feltevés téves volt.

`0x00bb87b0` minden `i = 0…255` értékre meghívja a megálló-keresőt és
interpolátort (`0x00bb8931`–`0x00bb8958`), majd az eredmény dword-ot a
`base + 0x800 + 4·i` helyre írja (`0x00bb8951`; a `base` a munkavégző harmadik
argumentuma, `[ebp+0x10]`, a hívó `0x00bb7c80` 0x1000 bájtos LUT-puffere). A `cmp ebx, 0x100`
(`0x00bb894b`) zárja a ciklust: a gradiens-LUT **256 darab, 32 bites**
bejegyzés. Ez a piros bemeneti bájt LUT-rekesze; a négy rekesz és a
`src[2]` indexelés részleteit lásd fent, a TwoTone LUT-elemzésében.

A megálló-kereső (`0x00bb85b0`) `x` egész indexhez kiválasztja az utolsó
`p ≤ x` alsó és az első `p > x` felső megállót. Ha `x` az első megálló
előtt van, az első színt adja vissza; ha az utolsó megállón vagy utána van,
az utolsó színt (`0x00bb8603`–`0x00bb8624`). A keresőnek két közvetlen
megállóága van. Az alsó megállónál (`0x00bb863d`) a kód a `p_lo` és a
float32-ként tárolt `x` bitmintáját előjeles 32 bites kivonással veti össze,
abszolút értéket vesz (`cdq`/`xor`/`sub`), és ha az előjel nélkül vett érték
`< 8` (`jb`), az alsó megálló tárolt színét adja vissza. Ha nem, ugyanezt
végzi a felső megállóval (`0x00bb865a`, `p_hi`), és `< 8` esetén a felső
megálló tárolt színét adja. Az alsó kapu van elöl. 7 bitlépésnyi távolság még
megállószín, 8 már interpolált szín; a `cmp eax, 8` tehát float32 bitminták
távolságát méri, nem 8 indexnyi távolságot. A kapu a munkavégző által generált
LUT-ra nem hat (n = 2…256-ra mérve). Az interpolált ág alfája mindig `0xff`;
a közvetlen megálló- és peremágak a tárolt dword-ot változatlanul adják (a
munkavégző a tárolt színek alfáját `0xff`-re állítja, `0x00bb886f`).

Az `eax` bemenet egész és előjel nélküli indexként értelmeződik: negatív
értéknél a kód `2³²`-t ad hozzá a float32 konverzió előtt
(`0x00bb85c4`–`0x00bb85d6`, a konstans `0x00cf39e4 = 4294967296,0`). Ezért
a negatív bemenet a legutolsó megálló utáni tartományba esik és az utolsó
színt adja; a `0x00bb87b0` LUT-ciklusa ezzel szemben kizárólag 0…255-öt ad át.

Ha `p_lo ≤ x < p_hi`, a súly float32-re tárolt x87-hányados
(`0x00bb865f`–`0x00bb8677`):

```
w = float32((p_hi − x) / (p_hi − p_lo))   # alsó megálló súlya
```

Az RGB-csatornákat a `0x00bb84a0` külön-külön keveri, bájtonként, az alsó
bájttól (bit 0–7) a felsőig (bit 16–23). A `0x00c72150` értéke **0,5**; a `0x00c29990`-nél a CRT SSE2-jelző
`[0x00da1428] = 1` esetén `cvttsd2si` csonkít egészre. A kód a
végeredményt csatornánként 0…255 közé vágja; a pontos pixelképlet:

```
out_c = clamp(trunc(upper_c + w · (lower_c − upper_c) + 0,5), 0, 255)
```

Vagyis a pozitív RGB-csatornákon félértéknél felfelé kerekít; az eredmény
alfa-bájtja `0xff` (`0x00bb8586`–`0x00bb85a0`).

**Második, független út — gépi futtatás.** A `.text`, `.rdata` és `.data`
szakaszok az eredeti VA-kon futottak a mérési ELF-ben (`ImageBase=0x400000`),
`qemu-i386` alatt, `0x027f` x87 vezérlőszóval és `[0x00da1424]` /
`[0x00da1428] = 1` jelzőkkel. Négy bemeneten (`[10,200]`, `[0,255]`,
`[0; 127,5; 255]`, valamint az `x=10`-től két irányban pontosan 8 float32
bitlépésre levő megállópáron) a `0x00bb85b0` eredménye mind a **259**
vizsgált indexen (`−2…256`) bájtról bájtra egyezett a skalár modellel.
Példák (a `[10,200]` elrendezés színei: `0xff0a1433` a `p=10`, `0xffc96500`
a `p=200` megállón): az első megálló előtti `x=0` az első színt adta; a `p=200`
utáni `x=201` az utolsót; az `x=105` (w = 0,5) kimenete `0xff6a3d1a`; a pontosan
8 bitlépéses eset (színek: `0xff000000` és `0xffffffff`) `0xff808080` lett, nem
a megálló színe. A cáfoló változatok
közül a `+0,5` nélküli csonkolás **167/259** kimeneten eltért, a `< 8`
téves `≤ 8` olvasata pedig az utolsó kontrollon eltért.

**Független ellenőrzés (2026-10-03, másik ellenőr).** Saját ELF-harness
(`qemu-i386`, ugyanazok a beállítások) a `0x00bb85b0`-t 30 243 bemeneten
(1623 elrendezés: 2, 3, 5, 10 megálló, egyenletes és egyenetlen, duplikált
pozíció, n = 1, rendezetlen, véletlen; x = −2…256 és szélsőértékek) és a
`0x00bb84a0`-t 32 802 színpár × súly kombináción (a 0…1 tartományon kívüli
súlyokkal is) bájtra egyezőnek találta a fenti modellel (0 eltérés). A
kapu-rács (alsó/felső megálló 0…12 bitlépésre `x`-től, `x0 ∈ {0, 1, 2, 10, 64,
100, 127, 128, 129, 200, 254, 255}`): 7 bitlépés még kapuz, 8 és 9 már nem; a
`≤ 8` olvasat 142 helyen más kimenetet adna.

A **teljes munkavégzőt** (`0x00bb87b0`) is lefuttatta: az objektumokat (this,
gradientArray, vektor, elemek) a kód olvasása alapján kézzel építve, három
helyettesítővel (`0x00c0769f` az operator new → egyszerű foglaló; `0x00c07681` →
`ret`; a 7,8 KB-os `0x008ef520` kifejezés-kiértékelő → „a csomópont double
értékének másolása”), 78 megállótömbre (n = 2…64, 100, 128, 200, 255, 256, 300)
és 19 968 LUT-elemre bitre egyezett a modellel (a pozíciótömbök is). n = 2
pozíciói `0x00000000` és `0x437f0000` (0,0 és 255,0), n = 3: {0 ; 127,5 ; 255};
a `+0x000` és `+0x400` rekesz nulla, a `+0xc00` érintetlen, n < 2 esetén a LUT
érintetlen. Az elem 32 bites alakja a memóriában (little-endian): ch0, ch1, ch2,
`0xff`.

*Bizonyítottsági fok: **megerősített** az interpolációs képletre, a megállókon
túli peremre, a `< 8` ágra, a megállóhelyek generálására (0,
`float32((k · 255,0) / (n−1))`, 255) és a 256 elemű LUT-ra (`+0x800` rekesz;
`+0x000` és `+0x400` nullázott) — két úton: az utasításszintű levezetés és az
eredeti `0x00bb85b0`, `0x00bb84a0`, illetve (három helyettesítővel) a teljes
`0x00bb87b0` qemu-i386 futtatása egyezik. **Feltételes (nem futott):** a
megállók színének forrása (`0x008ef520`), a gradientArray tényleges
színkódolása (az R/B bájtsorrend a megállókban nem igazolt), a `0x00bb7e40`
valódi objektumon és a `TwoTone` beolvasójának (`0x00bc2760`) saját futtatása.
Az eredmények az FPU-vezérlőszó `0x027f` (53 bites pontosság) mellett igazak;
`0x007f` mellett 16/30 243 interpolált kimenet változna. A mérőadatban nincs
általános `GradientMap` export; a pixelmatematika kimeneti ΔE-hatásáról ebből
nem állítunk.*

**A `TwoTone` ugyanezt a munkavégzőt használja** (statikusan megerősítve): az
RTTI-vtáblák (`0x00cf0120`, `0x00cf085c`) 6. rése a közös alkalmazó
(`0x00bb7c80`), a 8. rése `0x00bb87b0`; a `0x00bb7c80` identitás-LUT-ot épít
(`0x00bcb270`), a 8. résen át hívja a munkavégzőt a LUT-bázissal, majd a
`0x00bcb2f0`-t; a `TwoTone` beolvasója (`0x00bc2760`) a `[this+0x40]`-be tesz
objektumot (`0x00bc2923`) és a `0x00bb8710`-et hívja (`0x00bc2949`).

#### Több megállós `GradientMap` — teljes natív pixelút (2026-10-04, #626)

**Bizonyítottsági fok: megerősített** a 2, 3 és 5 megállós, megadott
színértékekből épített LUT-ra, a 256 elemű táblára, az interpolációra és a
bemeneti csatornára. Az utasításszintű levezetés és a teljes natív
`qemu-i386` próba bájtra egyezik.

* **Pozíció és mértékegység:** az indexelt tartomány 0…255. `n ≥ 2` esetén
  `p[0] = 0`, `p[n−1] = 255`, a belső stop float32-re kerekített
  `p[k] = (k · 255,0) / (n−1)`. A 255,0 double konstans címe `0x00cf39d0`,
  a végpont 255,0 float konstansa `0x00cf3a00`; a belső értéket a kód
  `fstp dword`-dal tárolja (`0x00bb88e4`–`0x00bb892d`). Következésképp
  `n=3`: `{0; 127,5; 255}`, `n=5`:
  `{0; 63,75; 127,5; 191,25; 255}`.
* **Interpoláció és LUT:** a megállókereső (`0x00bb85b0`) a tárolt pozíciók
  közötti alsó/felső stopot adja; az x87-hányados float32 súlya
  `w = float32((p_hi−x)/(p_hi−p_lo))`. A `0x00bb84a0` mindhárom RGB
  csatornát külön keveri: `clamp(trunc(upper + w·(lower−upper) + 0,5),
  0, 255)`. Ez lebegőpontos, nem fixpontos interpoláció. A munkavégző
  `0x00bb87b0` az `i=0…255` indexek eredményét a
  `base+0x800+4·i` címre írja (`0x00bb8931`–`0x00bb8958`): pontosan 256
  dword a piros csatorna LUT-rekeszében.
* **Indexelt bemeneti csatorna:** a natív pixelalkalmazó
  `0x00bcb2f0` a BGRA-bemenet `+2` bájtját olvassa, és azzal indexeli a
  `+0x800` rekeszt (`0x00bcb3a0`–`0x00bcb3ab`); a `+1`, `+0`, `+3` bájt a
  külön `+0x400`, `+0`, `+0xc00` rekeszt indexeli. A `+2` a BGRA vörös
  csatornája. A gradiens bemenete tehát a nyers piros bájt, nem luma.

**Független natív futtatás.** A helyi `qemu_harness` a `0x00bb7c80` teljes
alkalmazót futtatta; az eredeti vtable-munkavégző (`0x00bb87b0`) és
képpontalkalmazó (`0x00bcb2f0`) is futott. A LUT-rögzítéshez ugyanebben a
futásban előbb külön meghívtuk a `0x00bb87b0`-t, majd ugyanazzal a művelet-
objektummal lefutott a teljes `0x00bb7c80` alkalmazó. A CRT-shim mellett
csak három célzott függvény kapott shimet: `operator new` (`0x00c0769f`) és `delete`
(`0x00c07681`) a determinisztikus foglaláshoz, valamint a 7,8 KB-os
kifejezéskiértékelő (`0x008ef520`), amely a kézzel felépített csomópont ismert
double értékét adta vissza. A megállókereső, pozíciószámítás, csatorna-kód,
LUT-építés és pixelalkalmazás eredeti bináriskód maradt; a `gradientArray`
XML-szöveg beolvasója (`0x00bb8710`) nem futott.
Mindhárom futás a harness `FPUCW=0x027f` beállításával ment; minden natív
kimeneti alfa-bájt `0xff` volt.

Mindhárom futásban külön forrás- és cél-Image rekord szerepelt: `+0x04`
stride=256 pixel, `+0x08` szélesség=256, `+0x0c` magasság=4, `+0x10`
BGRA-adatmutató. A négy forrássor piros csatornája egyaránt 0…255-ig futott;
`(G,B)` rendre `(0,0)`, `(255,255)`, `(255,0)`, `(0,255)` volt, az alfa
`0xff`. Így ugyanaz a piros érték négy különböző zöld/kék pár mellett is
szerepelt.

| próba | szintetikus `0xRRGGBB` stopértékek | QEMU LUT vs. `gradient_map` | QEMU-kép vs. `gradient_map` | azonos R, eltérő G/B |
|---|---|---:|---:|---|
| 2 stop | `0x132f71`, `0xe64908` | 0 / 768 bájt eltérés | 0 / 3072 RGB-bájt eltérés | 0 / 256 eltérő pixel mindhárom sorpárban |
| 3 stop | `0x0711e7`, `0xf08023`, `0x36cbb5` | 0 / 768 | 0 / 3072 | 0 / 256 mindhárom sorpárban |
| 5 stop | `0x0102fd`, `0x57b30d`, `0xf03189`, `0x34d2c7`, `0xe5a611` | 0 / 768 | 0 / 3072 | 0 / 256 mindhárom sorpárban |

A helyi `gradient_map` (`src/picasapy/render/glimmer_ops.py`) tehát a
megadott megállóértékekre és a teljes 256 indexre bájtra egyezik mind a
natív LUT-tal, mind a teljes natív alkalmazó kimenetével; nincs fejlesztői
eltérés ezen a függvényen. A négy G/B-ellenpróba cáfolta a luma-indexelést:
mindhárom palettán minden R-értéknél azonos RGB-kimenet született, miközben
az R szerint változó LUT nem konstans (a 2 stopos próbában 228 különböző
RGB-triplett volt). Ezt az ellenpróbát a független gépikód-út is ellenőrzi:
`[BGRA+2]` közvetlenül a `+0x800` táblába indexel.

**Határ:** ez a mérés a stopokat kész numerikus double értékként adta a
munkavégzőnek. A `gradientArray` szöveges attribútumának tényleges
kiértékelése, a valós XML-export stopjainak színkódolása/sorrendje, illetve
az `0x008ef520` eredeti kifejezéskiértékelője nincs ezzel mérve; ezek továbbra
is feltételesek. A helyi `filterdesc.xml` nem tartalmaz több-stopos
`gradientArray` export-goldent; ezért a mérés a pixelmatematikát, nem a
szöveges attribútum előállítását zárja le.

### 5. `ResizeImageOperation` — közös diszpécser, eltérő pixelág a forgatástól

Az alkalmazó (`0x00bc3650`, 407 b) tengelyenként `forrás / cél` léptéket
számol (`0x00bc3700`–`0x00bc3731`), majd a végén a **`0x00bcb5e0`**
segédfüggvénynek adja át a transzformációt és a `smoothing` kapcsolót
(harmadik argumentum, `0x00bc37d6`).

⭐ **Ez ugyanaz a `0x00bcb5e0` diszpécser, amit a `RotateImageOperation` hív**
a `0x00bc8060` transzformáción keresztül. Mérve (`xrefs`): a
`0x00bcb5e0`-nak négy hívója van, köztük mindkettő. A pixelág viszont eltér:
a Resize tengelyhez igazított mátrixot ad át, a Rotate forgatási mátrixát a
`0x009e6da0` az általános affine-ágra irányítja (a fenti Rotate-szakaszban
részletezve).

⇒ A Resize-re érvényes lezárás: tengelyhez igazított mátrix és
`smoothing=true` esetén a mintavételező a **`ytResampler`**, módja
**kicsinyítéskor és 1:1-nél 0-s doboz, csak nagyításkor 3-as Mitchell**
(ld. 5/c). **Nem bilineáris.** A Rotate nem bizonyíték a Resize pixelágára,
és fordítva.

**A `smoothing` attribútum:** tag `+0x34`, **alapértéke `true`**
(`0x00bc36ac` `mov byte ptr [esp+0x18], 1` a getter előtt, a
`FUN_00c29990` logikai átalakítóval).

> ✅ **Megvalósítva (#2227, 2026-09-04; helyesbítve #3805, 2026-09-28).** A
> `resize_image` (`src/picasapy/render/glimmer_ops.py`) az 5/c pont szerint
> dolgozik: a **vízszintes** cél/forrás lépték `≤ 1` → fixpontos doboz,
> egyébként Mitchell–Netravali `B = C = 0,4`, mindkét tengelyen ugyanaz a
> mód. A #2227 és a #3805 között tengelyenként döntött (1:1 → azonosság,
> egyébként lebegőpontos Mitchell) — ez volt a `Pixelate` ΔE 4,6-os
> eltérésének oka.

### 5/a. `smoothing=false`: legközelebbi szomszéd, nem dobozmód

A korábbi „NINCS MÉRVE” jelölés lezárult. A `ResizeImageOperation`
alkalmazója (`0x00bc3650`) a `smoothing` értékét a `+0x34` mezőből olvassa:
a hiányzó érték alapja `true` (`0x00bc36ac`), a kiolvasott érték pedig a
`0x00c29990` egészre alakítása után a `0x00bc36c5` `setnz` ágával lesz a
`bVar2` bájt. Ezt adja át a közös resampler-wrappernek
(`0x00bc37d6` → `0x00bcb5e0`).

A wrapper utasításszinten külön ágazik (`0x00bcb602` `test bl,bl`):

- **`smoothing=true`** esetén először a mátrixot vizsgálja
  (`0x00bcb61c` → `0x009e6da0`). Ha a két kereszt-együttható valamelyike
  nem nulla a vizsgált tűrésen belül, közvetlenül az általános affine-ágra
  ugrik (`0x00bcb623` → `0x00bcb6b8` → `0x009e6df0`); ez a `Rotate` útja.
  Csak tengelyhez igazított mátrixnál számol léptéket, és választ 1:1-nél
  0-s doboz-, egyébként 3-as Mitchell–Netravali módot (`0x00bcb63f`–
  `0x00bcb655`); ez a `Resize` útja.
- **`smoothing=false`** esetén közvetlenül a `0x009e6df0` affine-ágat hívja
  (`0x00bcb6b8`–`0x00bcb6ce`), `param_4=0`, `param_5=0` és `param_6=0x100`
  értékekkel (`0x00bcb6bf`, `0x00bcb6c4`, `0x00bcb6c6`, `0x00bcb6c9`). A
  `0x009e6df0` ebből a feltételből a `0x009e7420` rutint választja
  (`0x009e6ff0`–`0x009e6ffa`), amely fixpontos forráskoordinátát csonkol
  (`0x009e754d`, `0x009e7553`) és **egyetlen képpontot** olvas
  (`0x009e756d`). Ez a 9-es, legközelebbi-szomszéd mód.

⇒ `smoothing=false` esetén **nem** a 0-s dobozmód fut. 1:1 léptéknél is
ugyanez a legközelebbi-szomszéd ág fut; a kimenet ilyenkor természetesen a
forrás képpontjait adja vissza, de a választott mechanizmus nem a doboz.
Ez a `Rotate` hívásánál nem releváns: ott `smoothing=true`, és a forgatási
mátrix a fenti általános affine-ágat választja.

**Nálunk (ellenőrizve, 2026-10-04):** a `resize_image(...,
smoothing=False)` a `cv2.INTER_NEAREST`-et hívja (`src/picasapy/render/glimmer_ops.py`,
`resize_image`), de ez **nem bájtazonos** a Picasa-pixelúttal. A natív
koordinátalépés és a QEMU-összevetés a 5/d pontban szerepel; a korábbi
„mechanizmus egyezik” állítás itt visszavonva.

### 5/b. A mag kicsinyítéskor a léptékkel nyúlik — LEZÁRVA

A korábbi nyitott kérdés („a 3-as mód magja kicsinyítéskor szélesedik-e?”)
a célzott kiolvasással eldőlt: **igen**. Itt a bináris `scale` a
cél/forrás transzformációs lépték (`scale < 1` = kicsinyítés); a mi kódunk
ennek reciprokát, `be_meret / ki_meret` értéket használja. A `0x00a3f660`
súlyépítő a 3-as módnál előbb a `0x00a3f5b0`-t hívja
(`0x00a3f68c`–`0x00a3f6a3`), és a súlyépítő kritikus ágában a tartósugarat a
léptékkel osztja:

```asm
0x00a3f728  fcomp dword ptr [ecx + 0x30]
0x00a3f732  fld   dword ptr [esp + 0x70]
0x00a3f736  fld   dword ptr [ecx + 0x30]
0x00a3f739  fadd  qword ptr [0x00cf3db0]
0x00a3f73f  fdivp st(1)                 ; lépték / ([this+0x30] + 0,001)
0x00a3f745  fld   dword ptr [esp + 0x10] ; alap-tartósugár
0x00a3f74b  fdiv  dword ptr [esp + 0x70] ; alap-tartósugár / lépték
```

A `0x00a3f660` friss Ghidra-dekompilációja ugyanezt nevezi meg: a
`param_6` a lépték, amelyet `1,0` fölött 1,0-ra korlátoz, majd a
`0x00a3f74b` osztásban kerül a sugár nevezőjébe. Ezért `scale < 1` esetén a
forrástérbeli tartósugár **nő**; a mag nem marad fix kétpixeles. A
`0x00cf3db0` értékét ebben a körben nem adom át számszerűen: **NINCS MEG**
kiolvasva, de az összeadás helye és szerepe a binárisból megvan.

**Nálunk (MÉRVE, #3805 után):** a `_tengely_sulyok`
(`src/picasapy/render/glimmer_ops.py`) mindkét módra ugyanezt a szerkezetet
használja: `nyujtas = max(1, forrás/cél)`, a tartósugár doboznál
`0,5 · nyujtas`, Mitchellnél `2 · nyujtas`, a mag argumentuma
`(j + 0,5 − c) / nyujtas`. Kicsinyítéskor a Mitchell csak akkor fut, ha a
vízszintes tengely nagyít (5/c).

| | Eredeti | Nálunk (mért forrásállapot) | Teendő |
|---|---|---|---|
| `smoothing=true`, `scale < 1` | bináris `0x00a3f745`–`0x00a3f74b`: tartósugár / lépték | `_tengely_sulyok`: `max(1, scale)`-nyújtás | nincs teendő |
| `smoothing=true`, `scale = 1` | 0-s dobozmód, a `0x00bcb63f`–`0x00bcb655` ág szerint | 1:1-es doboz = azonosság (`(16383·p + 255) >> 14 = p`) | nincs teendő |
| kimeneti pixelazonosság eredeti exporttal | ld. 5/c (#3805) | `Pixelate` alap ΔE 0,098 | lezárva, 5/c |

**Bizonyítottsági fok: megerősített** a mechanizmusra (célzott Ghidra
utasítás- és dekompilációs kiolvasás); **NINCS MEG** a Picasa eredeti és a mi
Mitchell-kicsinyítésünk pixelazonossági golden-mérése.

**Nyitott kérdések mérlege:** 0 nyílt · 1 lezárva · 0 blokkolt · 0 hatókörön
kívül · 0 „csak nyitva”. A pixelazonossági golden nem ennek a bináris
mechanizmus-kérdésnek a nyitva maradt része, hanem külön fejlesztési/mérési
feladat; a kimeneti eltérés okát ebből a leletből nem állítom.
### 5/c. ⭐ Kicsinyítéskor DOBOZ, nem Mitchell — és a fixpontos súlyok (2026-09-27, 381. kör, #626)

*Bizonyítottsági fok: **megerősített**, utasításszinten, független újralevezetéssel (EGYEZIK) és golden-méréssel.*

*Forrás: `0x00bcb5e0` (`0x00bcb629`–`0x00bcb659`) · `0x00a3f660` (a 0-s ág `0x00a3fb03`, a súlynormálás `0x00a4031f`–`0x00a404a2`) · `0x00a426a0` (az alkalmazó `0x00a4273f`–`0x00a4283a`).*

⛔ **Helyesbítés az 5. ponthoz.** Az 5. pont szerint `smoothing=true` esetén
„lépték = 1 → 0-s doboz, egyébként 3-as Mitchell”. **Ez így téves.** A wrapper
a vízszintes léptéket veti össze 1,0-val:

```asm
0x00bcb629  fld   dword ptr [ebp]        ; m0 = forrás/cél (vízszintes)
0x00bcb62c  fld1
0x00bcb62e  fld   st(0)
0x00bcb630  fdivrp st(2)                 ; 1/m0 = cél/forrás
0x00bcb634  fstp  dword ptr [esp+0x10]
0x00bcb63f  fld1
0x00bcb641  fcomp dword ptr [esp+0x10]   ; 1,0 vs cél/forrás
0x00bcb647  test  ah, 5
0x00bcb64a  jp    0xbcb653               ; C0 = 0 → 1,0 ≥ cél/forrás
0x00bcb64c  mov   ecx, 3                 ; nagyítás → 3-as Mitchell
0x00bcb653  xor   ecx, ecx               ; kicsinyítés VAGY 1:1 → 0-s doboz
0x00bcb659  call  0xa3f490               ; ytResampler(ecx = mód)
```

1. **A mód:** ha a vízszintes cél/forrás lépték **legfeljebb 1** (kicsinyítés
   vagy 1:1), a **0-s doboz** fut, egyébként a 3-as Mitchell. A döntés
   **mindkét tengelyre** ugyanaz, és csak a vízszintes lépték dönti el.
   Ha a mátrixban forgatás vagy nyírás van (`|m1|` vagy `|m3|` > 0,0001,
   `0x009e6da0`, `[0x00cf3ab8]`), a wrapper a `0x009e6df0` általános utat
   hívja; a tiszta átméretezésnél ez nem fordul elő.
2. **A doboz:** sugara 0,5, és a kicsinyítés léptékével nyúlik (5/b). A csap
   súlya 1, ha `|x| < 0,5`, egyébként 0 (`0x00a3fb12` `fcomp [0xc7dafc]` = 0,5,
   `jp` → 0). A határon álló csap **nem** számít bele. A csap helye `j + 0,5`,
   a kimeneti képpont középpontja `c = (i + 0,5) · forrás/cél`, float32-ben.
3. **Egész súlyok:** `w_int = csonk(w · 16383 / Σw)`
   (`0x00a4031f` `[this+0x2c]` = 1,0 × `[0x00cf3b70]` = 16383,0;
   `0x00a4035d` `call 0xc29990` = `cvttsd2si`). A maradékot
   (`16383 − Σ w_int`) a `csonk(c)` indexű csaphoz adja, a csaptartományba
   szorítva (`0x00a40462`–`0x00a4049f`).
4. **Az alkalmazó:** a vízszintes menetben csatornánként
   `(Σ w_int · p + 255) >> 14`, telítéssel (`0x00a427b0`–`0x00a4283a`:
   `imul` az int16 súllyal, `add 0xff`, a `0x3fffff` fölötti és negatív
   összeg vágva, majd `>> 14`). A függőleges menet négyes főciklusa ugyanígy
   számol, de a sor utolsó `W mod 4` oszlopán a skalár és a SIMD farokútja
   nem ad hozzá `255`-öt (`0x00a40e40` és `0x00a413f0`, #4004). Az eredmény
   0..255-re szorítódik. Előbb a vízszintes menet fut, 8 bites köztes képpel,
   utána a függőleges. Ez gyakorlatilag **csonkolás**, nem kerekítés.

A 3. pont és a 4. pont főciklusa **módfüggetlen**: a nagyításkor futó
Mitchell-mag súlyai is így lesznek egésszé, és ugyanez az alkalmazó futtatja
őket (a Mitchell-mag határa kizáró: `|x| ≥ 2` → 0, `0x00a3fcde`). A
függőleges maradékág eltérő kerekítése az 5/c.1 pontban áll.

**Példa:** 960 → 48 képpont (lépték 20). A `c = 20i + 10`, a csapok
`20i … 20i + 19` (20 darab), mindegyik súlya `csonk(16383/20)` = 819, a
maradék 3 a `20i + 10`-es csapé (ott 822).

**Mérve** (684-es mérőkészlet, ΔE a Picasa-exporthoz; a kiolvasott
dobozmodell a mai Mitchell helyén, vízszintes menet elöl, minden más
változatlan):

| eset | ma (Mitchell) | **fixpontos doboz** |
|---|---:|---:|
| `Pixelate` alap (Impact 20) | 4,638 | **0,098** |
| `Pixelate` min (Impact 2, Add) | 0,783 | **0,128** |
| `Pixelate` max (Fade 100) | 0,121 | 0,121 |

A 48 × 32-es kicsinyített kép blokkjainak **94,4%-a bitre egyezik** a
Picasa-export blokkközepeivel (függőleges menet elöl: 93,3%). A terület-átlag
(`cv2.INTER_AREA`, kerekít) ΔE-je 0,276, az ismételt 2×-es felezésé 4,637. Az
eredeti tehát **egy lépésben** dobozol, felezés nélkül.

**Érintett leírók** (`filterdesc.xml`): `Pixelate` és `PicnikFocalPixelate`
(kicsinyítés, `imagewidth/Impact`); `Cinemascope` Letterbox-szal (a szélesség
nem változik, tehát a lépték 1: a függőleges 0,95-ös zsugorítás is
**dobozzal** fut). A Cinemascope mérőesete Letterbox nélküli, azon nincs
átméretezés; a `PicnikFocalPixelate` a `render/focal.py` saját
`cv2.INTER_AREA`-ját használja, arra a doboz-modellt nem mértem.

#### Eredeti / nálunk / teendő

| | eredeti | nálunk (`render/glimmer_ops.py`, `resize_image`, #3805 után) | teendő |
|---|---|---|---|
| módválasztás | vízszintes cél/forrás ≤ 1 → doboz, egyébként Mitchell | ugyanígy, mindkét tengelyre | — |
| a doboz | `\|x\| < 0,5`, a léptékkel nyújtva | ugyanígy (`_tengely_sulyok`) | — |
| súlyok | `csonk(w·16383/Σw)`, a maradék a `csonk(c)` csapé | ugyanígy, egész súlyok | — |
| kimenet | vízszintesen és függőlegesen a négyes főciklusban `(Σ w·p + 255) >> 14`; a függőleges sorvégi `W mod 4` oszlopban `(Σ w·p) >> 14` (#4004) | ugyanígy, vízszintes menet elöl | — |
| `PicnikFocalPixelate` | ugyanez a `Resize` | `render/focal.py` a közös `resize_image`-en | — |

**Nálunk (MÉRVE, #3805, 684-es készlet, ΔE a Picasa-exporthoz):**

| eset | előtte | utána |
|---|---:|---:|
| `Pixelate` alap (Impact 20) | 4,638 | **0,098** |
| `Pixelate` min (Impact 2, Add) | 0,783 | **0,128** |
| `Pixelate` max (Fade 100) | 0,121 | 0,121 |
| `PicnikFocalPixelate` alap (Impact 20) | 0,321 (`INTER_AREA`) | **0,231** |
| `PicnikFocalPixelate` min (Impact 2) | 0,162 (`INTER_AREA`) | **0,114** |
| `PicnikFocalPixelate` max (Fade 100) | 0,121 | 0,121 |

A `PicnikFocalPixelate`-nek tehát VAN exportja a készletben
(`picnikfocalpixelate__*`); a fenti „nem mértem” a doboz-modell előtti
állapotra szólt. Az őr: `tests/render/test_resize_mitchell_2227.py` (a jegy
960 → 48-as képlete, független ciklusos referencia bitre, golden).

⚠️ Nincs kimérve: (1) ha a dobozban egyetlen csap sincs (nagyításnál `c`
pontosan képponthatárra esik — dobozmódban csak függőleges nagyításnál
fordulhat elő), nálunk a teljes súly a `csonk(c)` csapé; (2) Mitchell-módban
a 1:1-es tengely is a Mitchell-magon megy át (a spec szerint a mód mindkét
tengelyre szól), ez enyhe elmosást ad; ezt Picasa-export nem igazolja;
(3) a képszélen a képen kívüli csap nem kerül a listába (nincs
peremismétlés) — a doboz egész léptéknél ettől független.

Fejlesztés: #3805.

### 5/c.1. Helyesbítés (#4004): a függőleges maradékág kihagyja a `+255`-öt

*Bizonyítottsági fok: **megerősített** — az utasításszintű olvasás és az
eredeti gépi kód QEMU-i386 futtatása egyezik. Külön Opus-modellolvasás ebben
a Codex-munkamenetben nem állt rendelkezésre.*

*Forrás: skalár `ytResampler` `0x00a40e40` (méret 1443 bájt); SIMD
`0x00a413f0` (méret 1565 bájt); a dispatch `0x00a426a0`; futtatott
QEMU-harness: `/home/sancho/picasapy-agent/eszkozok/qemu_harness/`.*

| út | négyes főciklus | függőleges maradékág |
|---|---|---|
| skalár (`0x00a40e40`) | `W & ~3` (`0x00a40f9f`); a három csatorna összege előtt `+0xff` (`0x00a4109f`, `0x00a4112f`–`0x00a4113b`) | a `W&~3` utáni őr (`0x00a412b1`–`0x00a412b7`) az `0x00a412c0`-ra lép; a `0x00a412c0`–`0x00a41389` összegzi, vágja és `>>14`-gyel ír, `+0xff` nélkül |
| SIMD (`0x00a413f0`) | `0xff` bias-regiszter (`0x00a41707`), `W & ~3` (`0x00a4170c`), majd `psrad 14` (`0x00a41863`–`0x00a41872`) | a maradékőr (`0x00a418a9`–`0x00a418b1`) az `0x00a418b7`-re lép; a `0x00a418b7`–`0x00a419b8` összegez, `psrad 14`-gyel ír, RGB-bias nélkül |

A dispatch (`0x00a426a0`) a skalár (`0x00a40e40`) és SIMD
(`0x00a413f0`) munkavégzőt is kiválaszthatja. A főciklus után mindkét út
`r = W mod 4` darab maradékoszlopot dolgoz fel; `r=0` esetén nincs
maradékág.

**Kimeneti képlet** — `S = Σ(w_int · p)`, a telítést a 8 bites tartományra
értve:

```text
négyes főciklus: clamp_0_255((S + 255) >> 14)
függőleges utolsó W mod 4 oszlopa: clamp_0_255(S >> 14)
```

A kerekítés nélküli eredmény legfeljebb 1 szinttel kisebb. Telítetlen,
nemnegatív `S` esetén pontosan akkor különbözik 1-gyel, ha
`S mod 16384 ≥ 16129` (`16384 − 255`); a telítési széleken a két kimenet
azonos maradhat.

**Független futtatás.** Az eredeti PE-ből kivett két függvény maradékágát
`qemu-i386` futtatta 32 esetben: skalár és SIMD, `W=4…11` (mind a négy
maradék kétszer), egy szintetikus, beállított veremkerettel és két sorral.
A `Σ=16128` próbában bias nélkül és `+255`-tel is 0 lett; a `Σ=4 177 665`,
`S mod 16384=16129` próbában a gépi maradékág 254-et, a `+255`-ös kontroll
255-öt adott. Mindkét út egyezett; a `W mod 4=0` esetekben a kimenetőr
változatlanul hagyta a maradékterületet. A harness a natív kódot a maradékág
belépési pontján indította, nem a teljes Resize-függvényhívást játszotta le.

**Exportminták.** A PicasaPy-lánc kimenetét egy ideiglenes, csak a függőleges
maradék `+255`-ét elhagyó változattal hasonlítottam össze: 34 kiválasztott
684-es Picasa-exportpár és 12 pár a helyi `research/testdata`-ból. A 684-es
készletben egyik vizsgált export utolsó három oszlopában sem volt változás;
`Pixelate` és `PicnikFocalPixelate` mindhárom csúszkaállásán a teljes
kimenet bitre egyezett. A max állások köztes szélessége 6, illetve 9, de
`Fade=100` miatt az effekt azonosság; az aktív alap/min szélességek 48/480,
mind 4-gyel oszthatók. A 34-ből 8 másik effektkimenet belső oszlopain
változott (legfeljebb 3 szinttel), de a végső 1–3 oszlopban nem.

A `research/testdata/PicasaPy-golden-kit/effekt5` Comicize párján a bemenet
1600 px széles (`dot=24`, `pixelate_centered` kicsinyített szélessége 67).
A teljes kimeneten 603 képpont változott, maximum 4 szinttel; az utolsó
három oszlopban 11 képpont, maximum 3 szinttel. A Picasa-exporthoz mért
utolsó három oszlop MAE-je a régi/új változattal 1,8429/1,8440 volt, tehát
ez a minta az utolsó három oszlopon nem javította a Picasa-exporthoz mért MAE-t.
A kiválasztott 684-es és tesztadatbeli mintákból két végső export szélessége
nem volt 4-gyel osztható (1090 és 1730); ezekre a kimenet bitre változatlan
maradt. A mérés tehát bizonyítja a hibát és egy belső Resize-láncon látható
végső hatást, de nem állít általános javulást a Picasa-exporthoz mért ΔE-ben.

**Fejlesztői teendő:** új fejlesztői jegy indokolt a
`src/picasapy/render/glimmer_ops.py` `_tengely_menten` függvényére. Függőleges
menetben a négyes prefix maradjon `(S+255)>>14`, az utolsó `W mod 4`
oszlopok pedig `S>>14` szerint készüljenek; a vízszintes menet maradjon
változatlan. A fejlesztés külön őrizze meg mind a négy szélesség-maradékot,
az 16128/16129 küszöb két oldalát, a Pixelate/FocalPixelate aktív és
Fade=100 eseteit, valamint a Comicize végső háromoszlopos mintáját.

### 5/d. ⭐ `smoothing=false`: középponthoz igazított, 16.16-os legközelebbi-szomszéd út (#626, 2026-10-04)

**Bizonyítottsági fok: megerősített.** Az utasításszintű út és az eredeti
Picasa-kód QEMU-futtatása egyezik. A smoothinges ág négy QEMU-esete a már
leírt 5/c súlyozott út kimenetét is bájtra egyezőnek találta a jelenlegi
`resize_image`-szel.

**A — utasítások.** A `ResizeImageOperation` alkalmazó (`0x00bc3650`)
float32-be menti a forrás/cél szélesség- és magasságarányt
(`0x00bc3700`–`0x00bc3735`). A `smoothing` hamis ága a wrapperben
(`0x00bcb5e0`, `0x00bcb602`–`0x00bcb614`) az általános affine-rutint hívja;
annak `smoothing=false` esete a `0x009e7420` egyképpontos munkavégzőre lép
(`0x009e6fb6`–`0x009e7001`).

`0x009e7420` a célpixel középpontját használja: a cél x/y koordinátához a
`0x00c72150` címen kiolvasott **0,5**-öt adja, majd a 6 elemű float32
transzformációval forráskoordinátát számol. A transzformált kezdő koordinátát
float32-re menti (`0x009e74c3`, `0x009e74f3`), majd a
`0x00cf3cb0` címen kiolvasott **65536,0**-val, azaz 16.16-os léptékkel alakítja
egésszé. A `0x00c0b1e0` tört részt elhagyó segéd és a `0x00c29990`
`cvttsd2si` konverzió csonkolást végez. Ugyanezzel az eljárással készül a
vízszintes fixpontos lépés (`0x009e7423`–`0x009e7439`); a belső ciklus ezt az
egész lépést ismételten hozzáadja (`0x009e7541`–`0x009e7549`). A forrásindex
a fixpontos érték aritmetikai 16 bites jobbra tolása
(`0x009e754d`, `0x009e7553`): pozitív koordinátán ez lefelé csonkolás.

Tiszta Resize-nél, ahol a kereszt-együtthatók és eltolások nullák, ugyanez
így írható fel. `s_x` és `s_y` a `0x00bc3650`-ben float32-re kerekített
forrás/cél arány; `trunc` a nulla felé csonkolást jelenti:

```text
q_x(0,y) = trunc(float32((0 + 0.5)·s_x) · 65536)
dx       = trunc(s_x · 65536)
q_x(i,y) = q_x(0,y) + i·dx                  # a gépi ciklus integer addja
q_y(y)   = trunc(float32((y + 0.5)·s_y) · 65536)
src_x    = q_x >> 16
src_y    = q_y >> 16
```

A `smoothing=false` ág nem oszt szét súlyt: érvényes forráskoordinátánál egy
teljes BGRA-dwordöt másol (`0x009e7562`–`0x009e7574`), tehát a kiválasztott
képpont súlya 1. Ha bármelyik index a forrás szélességén/magasságán kívülre
esik, az unsigned határ-összehasonlítás átugorja az írást
(`0x009e7556`–`0x009e7576`); a munkavégző nem clampel, nem ismétli a szélső
képpontot és nem ír nullát. A célpuffer előzetes értékét ezért a hívó adja.

**B — natív QEMU-futtatás.** Az eredeti függvények futottak a helyi
`qemu-i386` harnessben. A simított ág a `0x00bcb5e0`-tól indult; a hamis ág
közvetlenül a statikusan oda kiválasztott `0x009e7420` munkavégzőt futtatta,
explicit cél-recttel. A forrás és a cél külön képleíró rekord volt (`+0x04`
stride, `+0x08` szélesség, `+0x0c` magasság, `+0x10` BGRA-mutató); az RGB
csatornákat közvetlenül, az alfa-csatornát pedig háromszoros szürke RGB-sík
átméretezésével vetettük össze. A
`smoothing=true` a 5/c szerinti 0-s doboz- vagy 3-as Mitchell-úton futott; a
QEMU és a mi kimenetünk mind a négy méretpárnál bájtra egyezett. A
`smoothing=false` esetén az RGB-összevetésben jelzett kimeneti pixelek
eltértek, és az alfa összevetése sem egyezett:

| forrás → cél | próba | `smoothing=false`: eltérő RGB-pixelek | `smoothing=true` |
|---|---|---:|---|
| 5×3 → 3×2 | páratlan kicsinyítés | 5 / 6 | bájtra egyezik |
| 4×2 → 7×5 | párosból páratlan nagyítás | 11 / 35 | bájtra egyezik |
| 8×6 → 4×3 | páros kicsinyítés | 12 / 12 | bájtra egyezik |
| 5×3 → 8×6 | páratlanból páros nagyítás | 12 / 48 | bájtra egyezik |

Forráskoordinátára dekódolva az 5×3 → 3×2 legközelebbi-szomszéd próba `x=[0,2,4]`,
`y=[0,2]` mintákat adott. A 4×2 → 7×5 próba vízszintes sora
`[0,0,1,1,2,3,3]`, függőleges mintái `[0,0,1,1,1]`. Ez az utóbbi a
fixpontos lépés ismételt hozzáadását is elkülöníti attól, ha minden kimeneti
képpontnál újraszámítanánk az arányt: a `4/7` float32 léptékből `q0=18724`, `dx=37449`, ezért a
negyedik oszlop koordinátája `131071 >> 16 = 1`; a natív kimenet forrás-x=1-et
adott. A minden oszlopnál újraszámolt `(3+0.5)·4/7` koordináta 2 volna, tehát
ez a mérés azt az alternatívát is cáfolja. Ezek az egész értékek a fenti
konverzióval készülnek, nem illesztett paraméterek.

**Cáfoló próba / szélek.** A `0x009e7420`-nak adott affine eltolás `x=-1`,
3×1 célpuffer előtöltve `0x5a`-val. Az első forráskoordináta a képen kívülre
esett; a natív kimenet első BGRA-pixele `5a 5a 5a 5a` maradt, a másik kettő
pedig a forrás 0. és 1. pixele lett. Ez cáfolja a clampelt/peremismétlő
olvasatot. A specifikus Resize pozitív méretaránya ettől külön eset; a
szélen kívüli minta viselkedése itt a közös affine munkavégzőé.

#### Eredeti / nálunk / teendő

| | eredeti | nálunk (`render/glimmer_ops.py`, `resize_image`) | teendő |
|---|---|---|---|
| `smoothing=false` mintakoordináta | középpont + float32 → 16.16 csonkolás; az egész lépés ismételt hozzáadása; `sar 16` | `cv2.INTER_NEAREST`; a négy mért méretpárból négy eltér | az OpenCV-hívást cserélni a fenti, bájtra specifikált koordinátamenetre; a négy QEMU-eset legyen bitpontos referencia |
| `smoothing=false` súly | egy érvényes BGRA-pixel, súly 1 | egy legközelebbi pixel, de a koordinátatérkép eltér | azonos pixel kiválasztása a natív koordinátából |
| képen kívüli affine-minta | írás kihagyása, célpuffer változatlan | a tiszta Resize nem hoz létre ilyen koordinátát; ez a függvény nem vizsgálja az affine ági képszél-kitöltést | a hívói célpuffer-inicializálás vizsgálata, mielőtt általános affine-határviselkedést ugyanide emelünk |
| `smoothing=true` | 5/c: fixpontos doboz/Mitchell-súlyok | négy QEMU-méretpáron bájtra egyezik | nincs mért teendő |

Nincs mérve valódi Picasa-exportból származó külön Resize-golden; a fenti
pixelértékek a natív gépi kód QEMU-futtatásából és a PicasaPy-függvény
azonos bemeneteiből származnak.

### 6. ⭐ `AutoFixImageOperation` — TELJES: csatornánkénti min–max szinthúzás, vágás NÉLKÜL

A `red.cfg` **hat** effektje hívja, attribútum nélkül. A munkavégző
(`0x00bc2d70`, 217 b) három lépést tesz:

1. **Három hisztogram.** Három 256 dwordös puffert nulláz
   (`0x3fc` bájt `memset` + a 256. rekesz külön), majd a `0x00bc2e50`
   (231 b) képpontonként számol: `hist_R[bájt0]`, `hist_G[bájt1]`,
   `hist_B[bájt2]` — **egyszerű darabszám, semmilyen vágás vagy súlyozás
   nincs benne**.
2. **Ha a kép nagyobb 1000 képpontnál, egy kb. 1000 képpontos
   PONTMINTÁN számol** (`0x00bc2ea6` `cmp eax, 0x3e8`; a minta a
   `0x00bc2f40`-ben, a részletek a 6/a pontban). A tartományt (`lo`, `hi`)
   tehát a minta adja, nem a teljes kép.
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

### 6/a. ⭐ Az `AutoFix` mintája — kb. 1000 képpontos, legközelebbi szomszéd (2026-09-27, 380. kör, #626)

*Bizonyítottsági fok: **megerősített**, utasításszinten, független újralevezetéssel (EGYEZIK) és golden-méréssel.*

*Forrás: `0x00bc2e50` (231 b) · `0x00bc2f40` (550 b) · `0x0049fe60` · `0x009e6df0`.*

A 6. pont 2. lépése nyitva hagyta, hogyan kicsinyít a hisztogram-számoló.
Utasításszinten kiolvasva:

1. **A célméret.** `s = sqrt(1000,0 / (w·h))` float32-ben
   (`0x00bc2f6a` `fdivr [0x00cf3e10]` = 1000,0; a gyök a `0x0049fe60`, ami
   a `0x00c0b310` `sqrt`-burkolója). Utána
   `nW = csonk(w·s + 0,5)` és `nH = csonk(h·s + 0,5)`, mindkettő legalább 1
   (`0x00bc2fb5` `[0x00c72150]` = 0,5; a vezérlőszó `or 0xc00` = csonkolás;
   `cmp eax, 1` / `ja`). Egy 960 × 640-es képen `nW = 39`, `nH = 26`, azaz
   1014 mintaképpont.
2. **A mátrix.** Tiszta skálázás, float32 elemekkel: `m0 = w / nW`,
   `m4 = h / nH`, a többi 0, a sarok 1 (`0x00bc3077` `fdivp`,
   `0x00bc309f` `fdivp`). A `0x009e6340` egy egységmátrixszal veszi össze.
3. **A mintavétel pontminta.** A `0x009e6df0`-t `param_4 = 0`, `param_5 = 0`,
   `param_6 = 0x100` értékkel hívja (`0x00bc3132`–`0x00bc3154`). Ugyanezt
   az argumentumkészletet adja a `smoothing=false` átméretezés is, és ez
   a `0x009e7420` legközelebbi-szomszéd ágat választja: a mintaképpont
   közepét (`+0,5`) vetíti vissza a mátrixszal, 16.16 fixpontban, és
   **egyetlen** forrásképpontot olvas. Ld. az 5/a pontot és „A
   `QuantizePalette` teljes útja” szakaszt, ahol ugyanez a mintavevő fut.
4. **A hisztogram** ezen a mintán fut (`0x00bc2ec5`–`0x00bc2f21`); a LUT
   (`0x00bc3170`) viszont a **teljes** képre hat.

**Miért számít.** A ritka szélső képpontok (például egy vékony vonal) a
mintából kimaradnak. A tartomány így szűkebb, a húzás erősebb, mint teljes
képes min–max húzásnál. A `PencilSketch` min esetében a második `AutoFix`
bemenetének 2,5%-a (15 318 képpont) 162-es szintű, és legalább 0,5%-a ennél
sötétebb (az alsó 0,5%-os percentilis 152). A teljes kép tartománya 74–255, a 39 × 26-os
mintáé 162–255. Nálunk ezért 162 → 124 lett, az eredetiben 162 → 0.

**Mérve** (684-es mérőkészlet, ΔE a Picasa-exporthoz; a kiolvasott
mintavétel a mai teljes képes hisztogram helyén, minden más változatlan):

| effekt · eset | ma (teljes kép) | **1000 képpontos pontminta** |
|---|---:|---:|
| `PencilSketch` alap | 1,953 | **0,129** |
| `PencilSketch` min | 2,942 | **0,018** |
| `Cinemascope` alap | 1,367 | **1,097** |
| `Holga` alap / min | 0,890 / 0,678 | **0,750 / 0,500** |
| `Sixties` alap / min | 1,179 / 1,255 | **1,033 / 1,136** |
| `NightVision` alap / min | 4,626 / 3,673 | **4,595 / 3,663** |

A `max` esetek (Fade 100) változatlanok, egyik eset sem romlik.

*Mellékes lelet:* a `filterdesc.xml`-ben az `AutoFixImageOperation`-t a
`Cinemascope`, a `Holga`, a `NightVision`, a `Sixties` és (kétszer) a
`PencilSketch` hívja. A `HDR` leírója nem hívja; a mérésen a HDR-esetek
nem is mozdultak.

#### Eredeti / nálunk

| | eredeti | nálunk (`render/glimmer_ops.py`, `autofix`) |
|---|---|---|
| a hisztogram forrása | ≤ 1000 képpontnál a teljes kép, fölötte `nW × nH` pontminta | ✅ ugyanaz (`_autofix_hisztogram_forras`, `render/quantize_palette.py` `pontminta_racs`-ot hívja) |
| a LUT | a teljes képre | ✅ a teljes képre |
| a docstring | — | ✅ javítva (a „HDR-család” hivatkozás törölve) |

**Javítva (2026-09-27, #3797).** A pontminta a `render/quantize_palette.py`
`mintakep`-jével közös `pontminta_racs` függvényt hívja (ugyanaz a
`0x009e7420` mintavevő), csak más `nW`/`nH`/`lepes_x`/`lepes_y`
paraméterekkel. Mérve (684-merokeszlet, ΔE a Picasa-exporthoz, a fenti
táblázat szerint): `PencilSketch` alap 1,953 → 0,129, min 2,942 → 0,018,
`Cinemascope` alap 1,367 → 1,097, `Holga` alap/min 0,890/0,678 →
0,750/0,500, `Sixties` alap/min 1,179/1,255 → 1,033/1,136, `NightVision`
alap/min 4,626/3,673 → 4,595/3,663 — egyik eset sem romlott.

Fejlesztés: #3797.

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
tartalma, a `Resize` kicsinyítéskori
lépték-nyújtása, az `AutoFix` lekicsinyítő léptékének CRT-függvénye és az
`AdjustCurves` négy görbéjének SORRENDJE **nincsenek mérve**.*

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

## `HSVGradientMapImageOperation` — HSV-stopok és LUT pixelmatematikája (2026-09-04, #2211; bővítve 2026-10-04, #626)

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

### A HSV → RGB átalakítás — lebegőpontos, float32, CSONKOLVA (2026-09-28, 384. kör, #626)

*Bizonyítottsági fok: **megerősített**, utasításszinten, független újralevezetéssel (EGYEZIK) és golden-méréssel.*

A `0x00bbbe20` (cdecl, három float32 argumentum: h, s, v) a megállók közti
interpoláció után minden LUT-bejegyzést **közvetlenül** RGB-vé alakít:

1. `h` körbefordítása `[0, 360)`-ba, `±360`-as ciklusokkal (`0x00bbbe52`,
   `0x00bbbe65`–`0x00bbbe86`); `h = 360` → 0. Az `s` és a `v` `[0, 100]`-ra
   szorul, `S = s/100`, `V = v/100` (`0x00bbbe93`–`0x00bbbf06`).
2. `h6 = f32(f32(h/360) · 6)`, a szektor `i = csonk(h6)` (`0x00bbbf31`
   `or eax, 0xc00`, `0x00bbbf3e` `fistp`), a törtrész `f = h6 − i`.
3. `p = V(1 − S)`, `q = V(1 − f·S)`, `t = V(1 − S(1 − f))`; a szektorok
   (R, G, B): 0 (V, t, p) · 1 (q, V, p) · 2 (p, V, t) · 3 (p, q, V) ·
   4 (t, p, V) · 5 (V, p, q) (ugrótábla `0x00bbc0c4`).
4. Csatornánként `csonk(x · 255,0)` (`0x00bbc031` `fld [0xcf39d0]`, `or
   0xc00` + `fistp`). **Nincs +0,5.** A köztes értékek (h, S, V, h6, f,
   p, q, t) float32 cellákban vannak.

A `hueOffset` (`+0x44`) float32-ben adódik a keverés utáni színezethez
(`0x00bbc52f` `fadd`), a körbefordítást az 1. lépés végzi. Példa:
`(200°, 100, 100)` → `(0, 169, 255)`. A 169 a csonkolásból jön
(`0,6666665 · 255 = 169,99996`), kerekítéssel 170 volna.

**Nálunk** (#3814 óta) a `glimmer_ops.hsv_gradient_map` a fenti képlettel
építi a LUT-ot (`_hsv_rgb_lut_f32`): float32 köztes értékek, `±360`-as
körbefordítás, hatodolás és `csonk(x · 255)`, OpenCV nélkül. A `hueOffset`
float32-ben adódik az interpolált színezethez. Korábban az OpenCV 8 bites
HSV-jén ment át (`h/2`, `·2,55`, egészre kerekítve, `cv2.COLOR_HSV2RGB`) —
ez a kvantálás volt az 1,0–1,1-es eltérés oka. A javítás után mérve: alap
**0,548**, min **0,558**, max 0,121 (változatlan: a Fade 100 mellett a keverési
súly 0, a gradiens nem kerül a képre).

**Mérve** (`HeatMap`, 684-es készlet, ΔE a Picasa-exporthoz; a LUT a fenti
lebegőpontos képlettel, a kimeneti kerekítést változtatva):

| eset | ma (OpenCV HSV) | `rint` | **`csonk`** |
|---|---:|---:|---:|
| alap (Hue 0) | 1,014 | 0,673 | **0,554** |
| min (Hue −180) | 1,130 | 0,696 | **0,577** |

A maradék JPEG-zaj szintű: a saját kimenetünk 95-ös, 4:4:4-es JPEG-je
önmagához képest 0,467 / 0,469, a Picasához 0,39 / 0,47.

Fejlesztés: #3814.

### Az interpoláció — LINEÁRIS, a színezetben a RÖVIDEBB ÍVEN (2026-09-04, #2238)

A megálló-keresést és a keverést a `0x00bbbcf0` (302 b) és a `0x00bbbbf0`
(254 b) végzi.

**a) A megálló-keresés és a `position` koordinátája.** A worker a
`position` szövegét a `0x008f1460` konverzióval float32-be olvassa, és ezt a
pozíciótömbbe fűzi (`0x00bbc405`–`0x00bbc439`). A `0x00bbc510`–`0x00bbc568`
ciklus `x = 0, 1, …, 255` indexeken építi a LUT-ot; ezt az egész indexet a
`0x00bbbcf0` float32-be alakítja (`0x00bbbd0f`–`0x00bbbd1b`), majd közvetlenül
a stopok float32 `position` értékeivel hasonlítja össze. Ezért a `position`
az **0…255 LUT-index tengelyén** van: tört float32 pozíció is érvényes, a
mezőt a worker nem vágja 0…1-re, 0…255-re vagy fokokra. A tartományon kívüli
stopot maga a megálló-keresés végpontként kezeli.

Az eredeti worker QEMU-i386 futtatásánál a `[0.5,0°,100,100]` és
`[1.5,120°,100,100]` stoplista 0, 1, 2 indexeken `0000ffff`, `00ffffff`,
`00ff00ff` BGRA bájtokat adott: az `1` index a két tört pozíció között
interpolál. A `[300,0°,100,100]`, `[400,120°,100,100]` stoplista mind a
256 LUT-bejegyzésre az első stop színét adta. Ezeket az értékeket a QEMU-
próba kézzel épített stopobjektumai float32-ként adták át az eredeti
munkavégzőnek; a stopkereső és a LUT-építés natív gépi kód volt.

Független leíróbeli kontroll: a szállított `filterdesc.xml` HeatMap-effektje
(952. sor) a `position` értékekre `0`, `31.875`, `127.5`, `223.125`, `255`
értékeket ad meg. A recept tehát kifejezetten tört pozíciókat használ a
0…255 LUT-tengelyen; ez nem azt jelenti, hogy a bináris a mező minden
lehetséges értékét ezen a tartományon kívül is elfogadja.

A `0x00bbbcf0` megkeresi az utolsó `position ≤ x` (alsó) és az első
`position ≥ x` (felső) megállót. Ha a kettő egybeesik — vagy a keresett
érték bitmintája 8-nál közelebb van valamelyik megállóéhoz —, a megálló három
mezőjét (`h`, `s`, `v`) **változtatás nélkül** másolja ki. A megállók a
tömbben **hármasával** állnak (`lea ecx, [ecx + ecx*2]`, majd `*4` — három
float).

**b) A súly.** `0x00bbbdc0`–`0x00bbbdd7`:

```
t = (position[felső] − x) / (position[felső] − position[alsó])
```

⇒ `t` az **alsó** megálló súlya (1, ha `x` az alsón áll; 0, ha a felsőn).
Az osztás eredményét a stopkereső float32 dwordként tárolja
(`0x00bbbddc`–`0x00bbbde4`).

**c) A keverés.** A `0x00bbbbf0`-ben az `s` és a `v` **sima lineáris**
interpoláció:

```
S(x) = S_felső + t · (S_alsó − S_felső)
V(x) = V_felső + t · (V_alsó − V_felső)
```

Ez a `0x00bbbbf3`–`0x00bbbc22` x87 műveleti sorrendjének végpontokkal
feloldott alakja: az x87 köztes műveletek után az eredmény float32-be kerül.
A `hueOffset` hozzáadása külön float32-értékeken történik, a worker újra
float32-be tárolja az összeget (`0x00bbc52b`–`0x00bbc539`).

⭐ **A színezet NEM az:**

```
Δ = h_alsó − h_felső
ha |Δ| ≤ 180°: h_alsó* = h_alsó; h_felső* = h_felső
ha |Δ| > 180° és h_alsó < h_felső: h_alsó* = h_alsó + 360°
ha |Δ| > 180° és h_felső < h_alsó: h_felső* = h_felső + 360°
H(x) = h_felső* + t · (h_alsó* − h_felső*)
```

Az `|Δ|`-próba és a 180° konstans a `0x00bbbc36`–`0x00bbbc5a` úton van;
a rövidebb ívhez a kisebbik végpont `+360°` eltolását a
`0x00bbbc6e`–`0x00bbbca0` végzi. Pontosan 180° eltérésnél nem lép be az
eltolásos ágba. A végső HSV→RGB konverter (`0x00bbbe20`) `h`-t `[0,360)`-ra
forgatja. (A `0x0049f5c0` bizonyítottan `fabs`: 26 bájt, egyetlen `fabs`
utasítással.)

**d) LUT és indexcsatorna.** A közös motor először a `0x00bcb270`-nel 4096
bájton lenullázza a teljes négytáblás LUT-ot, majd komponensenként identitás-
táblákat állít elő: `+0x000` B, `+0x400` G, `+0x800` R, `+0xc00` A
rekeszben (`0x00bcb270`–`0x00bcb2e8`). A `0x00bbc260` ezután minden `x`-hez
a konvertált BGRA dwordöt a `LUT + 0x800 + 4*x` címre írja; a `+0x000` és
`+0x400` rekesz 1024-1024 bájtját lenullázza (`0x00bbc561`–`0x00bbc588`), a
`+0xc00` alfa-identitást meghagyja. A közös skalár pixelmotor a BGRA forrás
`src[2]` bájtját indexeli a `+0x800` rekeszben (`0x00bcb3a0`–`0x00bcb3a4`),
vagyis a **piros csatornából** választ stopot; a négy táblázat eredményeit
csatornánként összeadja és 255-re telíti (`0x00bcb3a0`–`0x00bcb4ba`).

Ezt az eredeti initializer → worker → pixelmotor QEMU-s próbája is
ellenőrizte. A BGRA `[255,64,127,1]` forrásból az eredmény `0000ffff`, ami
LUT[127]=`0000ffff`-tel egyezik, nem LUT[64]=`1500ffff`-tel vagy
LUT[255]=`002affff`-tel. A HSV-LUT alpha bájtja 255; a meghagyott alfa-
identitással összeadva is 255-re telítődik.

**Bizonyítottsági fok: megerősített** a `position` float32 LUT-tengelyére,
a komponensenkénti interpolációra, a hue rövidebb ívére, a `+0x800` LUT
felépítésére és a piros indexcsatornára: A út — célzott utasításszintű
követés a fenti címeken; B út — az eredeti munkavégző és a közös pixelmotor
QEMU-i386 futtatása kézi stoplistákkal, bájtra rögzített kimenettel. A
PicasaPy saját kimenetével végzett összevetés nem Picasa-export golden.

**Cáfoló próba:** megpróbáltam a `position` 0…1 normalizált skáláját és a
hue nyers lineáris keverését alátámasztó ellenpéldát találni. A `[0.5,1.5]`
pozíciójú próba az 1-es indexen a két stop köztes színét adta, ami cáfolja a
0…1-normalizálást; a 350°→10° QEMU-próba rövid úton a 0° környékén haladt,
nem a 180° környéki nyers interpoláció szerint. A valódi export-stoplista /
pixel-golden továbbra sincs mérve.

**PicasaPy-eltérés (#3814):** a `glimmer_ops.hsv_gradient_map` a `np.interp`
segítségével közvetlenül, nyers számtani hue-értékekkel kever; a fenti
350°→10° kézi stoplistán a 256 LUT-bejegyzésből **254 eltér** az eredeti
QEMU-LUT-tól (a végpontok egyeznek). A piros indexcsatorna viszont egyezik.
Fejlesztői teendő: az HSV hue LUT interpolációját a natív rövidebb
körívű algoritmus szerint számolja, a float32 végpont- és köztes kerekítési
sorrend megtartásával; az s/v maradjon lineáris. Bájtra ellenőrizhető próba:
stopok `[0,350,100,100]`, `[255,10,100,100]`; RGB LUT[0]=`ff002a`,
LUT[127]=`ff0000`, LUT[128]=`ff0000`, LUT[255]=`ff2a00` (natív BGRA:
`2a00ffff`, `0000ffff`, `0000ffff`, `002affff`).


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
kétséges~~. ~~**MOST MÉRVE (#2231):** a szállított szűrő kimenete
csatornánként EGYENLETES rácson ül, tehát a lineáris modell nem közelítés,
hanem a mért viselkedés; a hű oktree-újraépítés 100-szor nagyobb ΔE-t ad.~~
**⛔ HELYESBÍTVE (#3084):** a „mért viselkedés" a PicasaPy SAJÁT exportja
volt (PR #3440). A valódi Picasa-exportokon a kimenet képfüggő palettán ül,
és az oktree-út a binárisból kiolvasott mintavétellel és elmosással
0,34–0,91 ΔE-re egyezik — ld. a lap végi „✅ A `QuantizePalette` teljes
útja" szakaszt.

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

> ⛔⛔ **HELYESBÍTÉS (2026-09-21, #3084): ez a szakasz HAMIS referencián
> áll. Az `export-202608202231` NEM a Picasa exportja, hanem a PicasaPy
> v0.8.27 SAJÁT kimenete** — ezt a `docs/benchmarks/2026-08-24-1143-teljes-effekt-export.md`
> fejléce szó szerint kimondja („PicasaPy-export: v0.8.27 (`2026-08-20 22:31`)").
> Az alábbi 1. pont „0,268" egyezése tehát a mi rácsos modellünk és a mi
> régi kimenetünk egyezése — önmagunkhoz mértünk. A mappa a Picasa-exportokkal
> szemben kimérhetően más forrásból való:
>
> | jel | `export-202608151229` (Picasa) | 684-kit `export/` (Picasa, 09-18) | `export-202608202231` |
> |---|---|---|---|
> | EXIF a 178 fájlban | 178 | van | **0** |
> | átlagos luma-kvantáló (JPEG) | 3,45 | — | **1,00** (minden együttható 1) |
> | ΔE a 684-es exporthoz — `quantizepalette` `alap` / `min` | **0,38 / 0,07** | — | 16,72 / 39,78 |
> | ΔE a 684-es exporthoz — `heatmap` / `sixties` / `radtint` / `polaroid` `alap` | **4,10 / 1,01 / 1,48 / 0,20** | — | 24,13 / 17,20 / 9,46 / 22,95 |
>
> A két VALÓDI Picasa-export (08-15 és 09-18) egymással JPEG-zajszinten
> egyezik; a `2231` mindkettőtől eltér, a mai renderelőnktől viszont alig
> (`quantizepalette` `alap` 0,28, `radtint` 1,11). *(A projekt kanonikus
> ΔE-jével, `tools/golden/compare_render.delta_e_cie76`.)*
>
> **Következmény a Poszterizálásra.** A valódi Picasa kimenete **egyik**
> exportban sem ül egyenletes rácson (rács-illeszkedés 1,5% / 0,0% / 11,9%
> — mérőkép `alap` / `min` / a #2770 fotó). Az 1., 1/b és 1/c pont
> „két kép, két viselkedés" ellentmondása ezzel **megszűnik**: egyetlen
> viselkedés van, és az NEM a rácsos. A kanonikus ΔE a valódi exportokon:
>
> | eset | forrás ↔ Picasa | rácsos (mai) | oktree (a 2. pont hű újraépítése) |
> |---|---:|---:|---:|
> | mérőkép `alap` (8/80/0) | 16,04 | 16,73 | **15,21** |
> | mérőkép `min` (2/0/0) | 26,93 | 40,02 | **17,54** |
> | #2770 fotó (8/80/0) | 14,49 | 17,16 | **7,64** |
>
> Az oktree mindhárom valódi exporton jobb a rácsosnál, de **egyik sem
> hű**: a mértani mérőképen az oktree alig jobb a semmittevésnél
> (15,21 vs 16,04). A csere indoklása tehát a helyes referencia, nem a
> ΔE-mérő (egy korábbi, 2026-09-21-i megvalósítási kísérlet tévesen a
> mérőeszközt okolta — az a szál HAMIS). A hátralévő eltérés oka nyitott;
> ld. a #3084 jegyet.
>
> ⚠️ A `test_quantizepalette_racs_2231.py` őr *(törölve, #3084)* ugyanerre a hamis
> referenciára épül (a docstringje a `2231`-es mappát nevezi Picasa-exportnak).

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
átlagaként sem jön ki.

⛔ **A „képfüggetlen" állítás MEGDŐLT (2026-09-12, #2770).** Ez a szakasz
korábban azt is állította, hogy *„a leképezés ráadásul képfüggetlen: ugyanaz
a bemeneti szín ugyanazt a kimenetet adja más színeloszlású képben is"*. Erre
**nem volt mérés** — mind a három eset UGYANANNAK a mértani mezős képnek a
három beállítása volt. A tulajdonos leszállította a kért második, természetes
átmenetes képet, és a mérés az állítást **megdöntötte**. Ld. az 1/b pontot.

Őr: `tests/render/test_quantizepalette_racs_2231.py` *(törölve, #3084)* (28 állítás; a hű
oktree-modellel 27 bukik). ⚠️ Ez az őr a mérőszett képére igaz — a
természetes fotóra NEM, ld. lent.

### 1/b A MÁSODIK kép megdönti a képfüggetlenséget (2026-09-12, #2770)

Bemenet: a tulajdonos exportja (`My Pictures/2770-poszterizalas/`,
`original.t21.jpg` + `export.t21.jpg`, 2560 × 1696), természetes átmenetes
fotó, a kérés szerint gyári alapbeállítással (`Steps 8 · Smoothing 80 ·
Fade 0`).

**Előbb a proveniencia: az export tényleg poszterizált.** Átlagos
`|különbség|` az eredetihez **21,01** szint, a képpontok mindössze **0,91%-a**
változatlan (±2). Egy 64 × 64-es kivágat egyedi színei: eredeti **2861**,
export **353** — a kvantálás megtörtént.

**A rács viszont NINCS ott.** A spec 1. pontjának saját kontrollját
(a kimeneti csatornaértékek hány százaléka van ±2-n belül a
`round(i·255/(Steps−1))` rács egy pontjától) ugyanazzal a metrikával:

| kép | rács-illeszkedés (`Steps = 8`) |
|---|---:|
| az ELSŐ, mértani mezős export | **97,62%** |
| **a MÁSODIK, természetes export** | **11,94%** |
| kontroll: a második kép EREDETIJE | 21,21% |

Az export tehát **kevésbé** illeszkedik a rácsra, mint a saját eredetije.

**A „a simítás mozdította el" magyarázat is elesik.** Ha a simítás a
kvantálás UTÁN futna, a LAPOS területeken a rács megmaradna. A kép
**73,25%-a** lapos (helyi szórás < 1), és ott is csak **13,13%** az
illeszkedés (szórás < 0,5 mellett 13,36%). A rács a lapos területeken sem
létezik.

**Ami HELYETTE van: hét színű, KÉPFÜGGŐ paletta.** A lapos területek
(3 008 549 képpont) színeloszlása, 4-es raszterben:

| | eredeti | export |
|---|---:|---:|
| a 7 leggyakoribb szín fedése | — | **97,92%** |
| a 12 leggyakoribb szín fedése | 41,81% | 99,29% |
| eltérő színek száma | **720** | **138** |
| 1% felett álló csatorna-szintek (B / G / R) | 25 / 15 / 3 | **7 / 7 / 7** |

A csatorna-szintek a lapos területen:

```
B: 9 · 12 · 50 · 91 · 147 · 169 · 240
G: 13 · 18 · 98 · 171 · 219 · 220 · 252
R: 14 · 23 · 162 · 226 · 247 · 252 · 254
```

**Nem egyenletes** — a szomszédos szintek távolsága B-ben 3 · 38 · 41 · 56 ·
22 · 71 —, és a `0 · 36 · 73 · 109 · 146 · 182 · 219 · 255` rácshoz nem
illeszkedik.

**A hét szín egybeesik a bináris palettaméretével.** A 224. kör kiolvasta,
hogy a palettaépítő `Steps−1` = **7** színt épít (`0x00bb5dc4 add eax,-1`).
A mért kimenet lapos területeit **pontosan 7 szín** fedi 97,92%-ban. Ez
függetlenül, a kimenet oldaláról erősíti meg a palettás olvasatot.

⇒ **A #2746 kérdésének második fele volt a hibás premissza.** A kérdés így
szólt: *„miért nem az oktree-út eredménye kerül a képre, holott a bináris
oktree-t épít és a látható kimenet csatornánként egyenletes rácson ül?"* — a
látható kimenet **nem** ül egyenletes rácson. Az első mérőkép 97,62%-a annak
a képnek a sajátja, nem a szűrőé: mértani mezős képen a 7 színű paletta
elemei épp a rácspontok közelébe esnek.

### 1/c A KÉT export KÉT KÜLÖNBÖZŐ úton készült — SZÁMMAL (2026-09-15, #3084)

A #3084 megvalósítási köre elsőként a mért oktree-modellt építette újra, és
**mind a két mérőképen lemérte**. Az eredmény a fenti ellentmondást nem
oldja fel, hanem **élesíti**: számot ad rá, ΔE nélkül is.

**A bizonyíték: a `min` eset (`Steps = 2`).** Az oktree-út ilyenkor
`0x00bb5da8` szerint **2** levelet kap, tehát a kimenet legfeljebb **2**
különböző színt tartalmazhat. A mérés a Picasa saját exportján (a lapos
területek 97%-os fedéséhez szükséges színszám, 4-es raszter):

| export | `Steps` | az oktree-út felső korlátja | a MÉRT színszám |
|---|---:|---:|---:|
| mérőszett `min` (960 × 640, mértani) | 2 | **2** | **8** = 2³ |
| mérőszett `alap` (960 × 640, mértani) | 8 | 7 | **17** = 12 szürke lépcső + 4 mező + fehér |
| #2770 fotó (2560 × 1696, természetes) | 8 | 7 | 43 (de 7 szín fed 92,9%-ot) |

A `8 = 2³` és a `17 = 12 + 4 + 1` nem közelítés: pontosan az a színszám,
amit a **csatornánként független** rács ad a két kép saját színeire. Egy
2 levelű palettából 8 szín nem jöhet ki.

⇒ **A mérőszett exportja bizonyítottan NEM az oktree-út eredménye**, és ezt
most nem ΔE mondja, hanem egy megszámolható felső korlát.

**A másik irányban ugyanilyen éles.** A természetes fotó exportját a rácsos
modell **116 paraméter-kombinációval sem** közelíti: `Steps` 2…30 × négy
`Smoothing`-állás mellett a legjobb ΔE **26,31** — az érintetlen forrás
26,33-a mellett, azaz a modell ott semmit nem magyaráz. A mért oktree-modell
ugyanazon a képen **15,77**, és a palettájából hat szín ±8 szinten belül
egyezik az export hat leggyakoribb színével:

```
a mi oktree-palettánk        az export (8-as raszter)
(253, 220, 148)  10,8%   ↔   (248, 216, 144)   9,7%
(219, 167,  93)   8,8%   ↔   (224, 168,  88)   6,4%
(160, 101,  52)   7,9%   ↔   (160,  96,  48)   4,4%
(254, 251, 234)   5,6%   ↔   (248, 248, 240)   5,1%
(247, 218, 167)   4,8%   ↔   (240, 216, 168)   4,0%
(250, 215, 107)   2,0%   ↔   (248, 216, 104)   1,4%
( 34,  29,  22)  44,3%   ↔   (  8,   8,   8)  43,8%   ⚠️ EZ tér el
```

A hetedik, legsötétebb szín a mienknél **túl világos**, és ez a képpontok
44%-át érinti — innen a 15,77 nagy része.

**A színszám-ellentmondás viszont FELOLDVA:** az export 3685 színe (4-es
raszter) nem cáfolja a palettás olvasatot, mert a **JPEG maga** állítja elő:
a mi 12 színű oldalunk JPEG q95 után 2447, q85 után 6007 színt ad.

**Mérési javítás a modellen** (a bináris utasításszintjéről): a
`0x00bcb6f0` redukáló `N == 1` esetén **azonnal levélbe olvaszt**
(`0x00bcb70c` → `FUN_00bcb880`), nem rekurzál tovább. Az első
újraépítésem ezt kihagyta, és a hiba mérhető volt: a sötét ág keresése a
bejárási sorrend **utolsó** (világos, index 7) gyerekének átlagát adta a
teljes ág átlaga helyett (ΔE 16,02 → 15,77).

**A `return 4` korai ág LEZÁRVA** (a 4. pont 2. alkérdése): a
`0x00bb5edd`–`0x00bb5f02` a gyűjtő `+0x10` mezőjét nézi, és ha **nulla**,
összeolvaszt, felszabadít és `4`-et ad vissza. Ez **üres mintára** szóló
hibakód, **nem alternatív renderút**.

**A képponti alkalmazó is dekódolva** (`0x00bcb2f0`, 744 b): a
`0x00bcb4f2`-től induló ág **négy, 256 × 4 bájtos táblát** olvas a
csomagolt képpont négy bájtjára (`0x400` léptetés), és `paddusb`-vel
**telítéses bájtonkénti összeget** ad. Ez általános, csatornánkénti
LUT-alkalmazó; a 3-3-2 index OR-os használata ennek egy speciális esete. A
`0x00d695d2`/`0x00d695d3` bájtok a nem-SSE ágra váltanak — **a két ág
ugyanazt számolja**, tehát nem ez a kétféle út.

### ⛔ Ami ebből a MEGVALÓSÍTÁSRA következik: a csere NEM végezhető el

Egyik modell sem írja le mind a két exportot:

| | mérőszett `alap` | mérőszett `min` | #2770 fotó |
|---|---:|---:|---:|
| érintetlen forrás | 19,01 | 73,49 | 26,33 |
| **rácsos (a mai)** | **0,83** | **1,71** | 29,50 |
| **mért oktree** | 30,50 | 93,71 | **15,77** |

A mai modellre cserélni az oktree-t a mérőszett képén **36-szorosára**
rontaná a hibát. Ez nem paraméterezés-kérdés: a két export két különböző
viselkedést mutat, és a meglévő két minta a **képméretet és a képtartalmat
egyszerre** változtatja (960 × 640 mértani ↔ 2560 × 1696 természetes), ezért
a mérésből nem dönthető el, melyik a szétválasztó tényező.

⇒ A csere addig nem mehet ki, amíg egy olyan minta nincs, ami a két
tényezőt szétválasztja. A gépi út ehhez **kimerült**: egyetlen
`QuantizePaletteImageOperation` van (RTTI + `filterdesc.xml`), a `return 4`
ág hibakód, a képponti alkalmazó két ága azonos eredményt ad.

### Amit ez a MEGVALÓSÍTÁSRA jelent

A mai rácsos implementációnk (ΔE 0,268 a mérőszetten) **csak a mérőszett
képére hű**. Természetes fotón mérhetően más képet ad, mint az eredeti. A
csere önálló jegyet kíván, mert renderelő-cserét jelent, nem paraméterezést.

### Amit ez NEM mond meg

- A **beállításokat nem tudom igazolni** az exportból: a kérés a gyári
  alapot (8/80/0) adta meg, és a 7 színű paletta ezzel konzisztens
  (`Steps−1` = 7), de a csúszkák állását maga a fájl nem hordozza.
- Hogy a paletta **hogyan** épül (oktree-mélység, a vágás sorrendje), ez a
  mérés nem mondja meg — csak azt, hogy képfüggő és hét elemű.
- A `Smoothing` szerepét sem: a lapos/átmenetes szétválasztás csak azt
  zárta ki, hogy a rácsot utólagos simítás mosta volna el.

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

A `tests/render/test_quantizepalette_racs_2231.py` *(törölve, #3084)* docstringjében rögzített,
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

## ✅ A `NoiseImageOperation` véletlengenerátora: MT19937 nem szabványos magvetéssel (2026-09-27, 375. kör, #3736)

*Forrás: apply `0x00bbefa0` · munkavégző `0x00bce8c0` · magvetés `0x00aa28f0` · twist `0x00aa2930` · `mag01` tábla `0x00c782c0` · golden: `684-merokeszlet`.*

**Paraméterek.** Az attribútumok: `randomSeed` (+0x24, alapérték 0), `low` (+0x2c, 0), `high` (+0x34, 255), `channelOptions` (+0x3c, 7) és **`grayscale`** (+0x44, hamis; a binárisban kisbetűs „s”-sel). A `low` és a `high` előjel nélkül ≤ 255-re vágódik (`0x00bce8ce`–`0x00bce8ed`), a tartomány `r = high − low + 1`.

**A generátor: MT19937.** 624 szavas állapot, szabványos twist (`mag01 = {0, 0x9908B0DF}`, M = 397) és szabványos temperálás (`0x00bce9d2`–`0x00bce9f8`). **Egyetlen eltérés a magvetés** (`0x00aa28f0`):

```
s[0] = randomSeed
s[i] = 1664525 · (s[i−1] ^ (s[i−1] >> 30)) + i        (i = 1…623; a szabványos szorzó 1812433253)
index = 624   ⇒ az első húzás twistet vált ki
```

**Bejárás.** Képpontonként pontosan **egy** 32 bites húzás, sorfolytonosan: a puffer első sorától (y = 0…H−1), soron belül balról jobbra. A mérés szerint a puffer első sora a kép **teteje** (lent).

**Képpontérték** (`y` a temperált húzás, a képpont 0xAARRGGBB):

| ág | B | G | R | alfa |
|---|---|---|---|---|
| színes (`grayscale` hamis) | `(y & 0xFF) % r + low` | `((y>>8) & 0xFF) % r + low` | `((y>>16) & 0xFF) % r + low` | `(y>>24) % r + low` |
| szürke (`grayscale` igaz) | `y % r + low` — a TELJES 32 bites y-ból | ugyanaz | ugyanaz | `(y>>8) % r + low` |

Utána `(px & mask) | alphaOr`: a `channelOptions` 0. bitje az R-t, az 1. a G-t, a 2. a B-t tartja meg (a letiltott csatorna 0), a 3. bit a zajos alfát. Ha a 3. bit nincs beállítva, az alfa fixen 0xFF. A bemeneti képet a munkavégző nem olvassa; a keverést a lánc `BlendMode`/`BlendAlpha`-ja végzi.

**Mérve** (a kiolvasott generátor a mai `numpy`-zaj helyén, minden más változatlan; ΔE a Picasához):

| effekt · eset | a mai zaj | **Picasa-MT** |
|---|---:|---:|
| `NightVision` alap | 11,696 | **4,626** (a magasfrekvenciás korreláció G 0,985 · R 0,90 · B 0,82) |
| `NightVision` alap, alulról felfelé bejárva (kontroll) | — | 11,388 |
| `NightVision` min | 10,813 | 10,946 · **3,673** a #3735 mátrix-sorrendjével együtt |
| `Holga` alap | 1,476 | **0,890** |
| `Cinemascope` alap | 2,152 | **1,367** |
| `Sixties` alap / min | 1,289 / 1,443 | **1,179 / 1,255** |

A maradék képpontonként 3–5 szint, az átlagos eltérés −0,2 (torzítatlan). **A `PicnikGrain` is determinisztikus (mérve 2026-09-27, #3757).** A #907 „két alkalmazás független mintát ad” mérése a **natív, kisbetűs `grain`** szűrőre vonatkozott (`grain=1;` és `grain=1;grain=1;`, callback `0x008f88e0`). A Glimmer `PicnikGrain` leírója rögzített `randomSeed="1"`-et ad. A 684-es exporton a szürke ágú Picasa-MT `randomSeed = 1`-gyel és a leíró szerinti Multiply móddal (`BlendMode` 5):

| eset | a javítás előtti kód (véletlen mag, Darken) | Multiply + numpy-zaj | Darken + Picasa-MT | **Multiply + Picasa-MT** |
|---|---:|---:|---:|---:|
| alap (Grain 10) | 3,009 | 1,968 | 2,967 | **0,882** |
| max (Grain 50) | 18,634 | 9,645 | 9,167 | **1,380** |

Mindkét tényező kell, és a nagy ugrás csak a rögzített maggal jön: a zajminta tehát egyezik. A világosító ág (Screen, `BlendMode` 7) exportja nincs a készletben. Fejlesztés: #3757.

**Nálunk (#3757, #3444):** az `apply_picnik_grain` a natív generátort (`nativ_noise`) hívja a rögzített `randomSeed = 1`-gyel, és a módot a sorszámmal adja át (7 Screen / 5 Multiply). Újramérve a beépítés után (`analyze_validation_kit.mean_de`):

| eset | előtte | utána |
|---|---:|---:|
| 684 `picnikgrain__alap` (Grain 10) | 3,009 | **0,882** |
| 684 `picnikgrain__max` (Grain 50) | 12,21 ¹ | **1,380** |
| 684 `picnikgrain__min` (Grain 0) | 0,121 | 0,121 |
| merokit-2 `szemcse_04` (Grain 30, eredeti export `export-202608151438`) | 7,79 | **0,981** |

¹ A fenti táblázat 18,634-et ad a mai kódra; a beépítés előtti újramérés (három futás, véletlen maggal) 12,206–12,214-et adott, egyezésben a #3444 golden-nyilvántartásának 12,217-ével. Az eltérés oka nincs kiderítve; a javítás utáni értéket nem érinti.

A (kimenet − bemenet) különbség csatornánkénti átlaga és szórása (#3444) a `max` esetén: Picasa −33,75/−33,19/−32,97 ± 30,0/29,5/29,6; előtte −13,2/−12,2/−12,2 ± 26,1/25,1/25,3; utána −33,74/−33,19/−32,97 ± 29,95/29,30/29,28. Tesztek: `tests/render/test_picnik_grain_3757.py`. A világosító ág Picasa-exportja továbbra sincs; ott a független referenciához mért bekötés a bizonyíték.

*Bizonyítottsági fok: **megerősített**, utasításszinten, független újralevezetéssel (EGYEZIK) és a golden-korrelációval.*

## ✅ A `QuantizePalette` teljes útja — a minta, a keresés és az elmosás (2026-09-24, #3084)

A fenti szakaszok nyitva hagyták, hogyan áll elő az 50 × 50-es minta, és
mitől lett az oktree-újraépítés palettája „túl világos". Utasításszinten
kiolvasva:

| lelet | cím | mit mond |
|---|---|---|
| a minta **pontmintavétel** | `0x009e7420` (a `0x009e6df0` diszpécser `[a4]=[a5]=0` ága) | a mintaképpont KÖZEPE (`+0,5`, `[0x00c72150]`) a mátrixszal visszavetítve, 16.16 fixpontban (`×65536`, `[0x00cf3cb0]`, `floor` majd `ftol`), EGYETLEN forrásképpont; a léptetés soronként `floor(m0·65536)` |
| a lépték **mindkét irányban `W / 50`** | `0x00bb5bd0` `fild [ebp+8]` (a szélesség), `fdiv [0x00cf3bd8]` = 50,0; a mátrix float32 (`fstp dword`), `m0 = m4 = W/50` | fekvő képen a minta alsó sorai a képen KÍVÜL esnek |
| a képen kívüli mintaképpont **fekete** | `0x009a8d80` (a teljes képre `rep stosd` 0-val), a mintavevő határellenőrzése (`0x009e755a`/`0x009e7560`) | ezek is a fába kerülnek |
| a beszúrás **oszlopfolytonos**, szűrés nélkül | `0x00bb5d3b`–`0x00bb5d9d` | `x` külső, `y` belső ciklus; átlátszóság-vizsgálat nincs |
| a keresés helyettesítő testvére | `0x00bcb9f0`, a tábla `0x00cf0c48` (8 × 7 dword) | hiányzó gyereknél, ha a csomópont `+8` jelzője 0, a tábla sorának első LÉTEZŐ gyerekébe megy; a jelző a gyerekeknél mindig 1 (`0x00bcb9b8`), a gyökérnél csak `Steps == 2` esetén 0 |
| a csomópont-átlag | `0x00bcbaa0` | `floor(float32(összeg/darab))` |
| az elmosás a **natív dobozszűrő** | `0x00bb4de0` → `0x00bb4fc9 call 0x00bc5680` | ugyanaz a diszpécser, mint a DropShadow-é (`render/nativ_blur.py`, #3474), a sugár a `0x00bb5050` kvantálón át |

⚠️ **Következmény széles képeknél:** mivel a sorok is `W / 50`-nel lépnek, a
mintából `50 · H / W` sor esik a képre, a többi fekete. Egy 3:2-es fotónál ez
a minta kb. harmada, egy panorámánál a nagyobbik része — a paletta ilyenkor a
fekete felé húz, akkor is, ha a képen nincs fekete. Ez az EREDETI viselkedése
(a fenti mérés épp ezen múlik), nem regresszió.

A sugár-kvantáló (`0x00bb5050`, float32 konstansok `0x00cf3a44`–`0x00cf3a58`):
1 alatt 0; `2 < x < 2,065` → 2,065; `3 ≤ x < 3,0625` → 3,0625;
`4 < x < 4,13` → 4,13; `5 < x < 5,13` → 5,13; egyébként `x`. A
`BlurImageOperation` előtte tengelyenként 255-re vág.

### A mérés — a valódi Picasa-exportokon, kanonikus ΔE

| pár | forrás | rácsos (régi) | oktree, átlagoló minta | ez |
|---|---:|---:|---:|---:|
| mérőkép 8/80/0 (`3084-poszterizalas`) | 16,04 | 16,64 | 15,21 | **0,54** |
| természetes fotó 8/80/0 | 14,49 | 17,16 | 7,64 | **0,91** |
| mérőkép `min` 2/0/0 (`export-202608151229`) | 26,93 | 40,02 | 17,54 | **0,34** |

A Gauss-közelítésű elmosással a paletta ugyanez, de a ΔE 2,31 / 1,74 /
4,01 — a maradék tehát az elmosásé volt. A korábbi „a legsötétebb
palettaszín túl világos" tünet oka a fekete mintasorok hiánya volt.

Megvalósítás: `render/quantize_palette.py`,
`render/nativ_blur.blur_image_operation`; őr:
`tests/render/test_quantizepalette_paletta_3084.py`,
`tests/render/test_blur_image_operation_3084.py`.

**A többi Glimmer-effekt `BlurImageOperation`-je is a natív utat futtatja
(#3580).** Hívóhelyenként, a leíró értékeivel (`quality` mindenütt 3):

| effekt | `xblur` × `yblur` | a döntés forrása |
|---|---|---|
| `Soften` | `Impact·20/50` × ugyanaz | a csúszka-képlet (a 4.2 táblája); a nyers XML-sor ebben a repóban nincs idézve |
| `Orton` | `Bloom` × `Bloom` | a #317 mért σ-ja a Bloom FELE — a 3 menetes doboz szórása `≈ xblur/2`, tehát `xblur = Bloom` |
| `PencilSketch` | `Radius` × `Radius` | a 4.5 példa-receptje: `<BlurImageOperation xblur="{_sldrRadius.value}" …/>` |
| `Holga` | 18 × 20 | a 4.4: „a maszkolt elmosás (ami Blur)" |
| `Lomo` | 20 × 20 | ugyanaz |
| `IR` | `greenglow` × `greenglow` (5) | nem XML-sor: az `IRImageOperation` gyereke, a `+0x24`/`+0x2c` tag a `Blur`-é (ld. „`IRImageOperation` — szürkeárnyalatos mátrix") |
| `ReanimatedEyeColor` | `Blur` × `Blur` | `filterdesc.xml` 1269–1295: `<BlurImageOperation xblur="{Blur}" yblur="{Blur}" quality="3" BlendMode="{BlendMode.LIGHTEN}"/>` |

Nem `BlurImageOperation` (a jegy hét helyén kívül, **nem** érintett): a
`GlowImageOperation` saját sugár-skálázással (`0x00bb89b0`) és a
DropShadow (#3474) — ezek külön kódúton maradnak.

⚠️ **Golden-mérés nyitva:** a 684-es készlet a NAS-on van; az effektenkénti
ΔE (régi Gauss ↔ natív) a helyi körben mérendő, a jegybe írva. Ahol a
régi kód a nyers `xblur`-t σ-ként használta (Soften, PencilSketch, Holga,
Lomo, IR, ReanimatedEyeColor), a tényleges szórás a felére csökken — ez a
#545 (`LocalContrast`: σ = Radius/2) és a #317 (`Orton`: σ = Bloom/2)
mérésével egybevág, de effektenként még nincs goldenen igazolva.
Őr: `tests/render/test_glimmer_nativ_blur_3580.py`.

*Bizonyítottsági fok: **megerősített** — minden állítás mellett cím, és a
három valódi exporton a JPEG-újratömörítés zajszintjén egyezik.*

### ⛳ #626 — a `Steps`, `Smoothing` és `Fade` részletes ellenőrzése (2026-10-04)

A `filterdesc.xml:1244–1258` a `QuantizePalette` három csúszkáját,
alapértékét és a teljes műveletsort adja meg: `Steps` 2–30 (8), `Smoothing`
0–100 (80), `Fade` 0–100 (0), majd `BlurImageOperation` →
`QuantizePaletteImageOperation(Depth=4)` egy külső
`NestedImageOperation`-ben. A blur-sugár kifejezése mindkét tengelyen
`(100 − Smoothing)/10 + 0,1`; a külső `BlendAlpha` `1 − Fade/100`.

| rész | bináris út | qemu-i386 mérés |
|---|---|---|
| `Steps` konverzió | `0x00bb5ad0` az attribútumkifejezést értékeli, majd a `0x008eea90` helperrel egészre alakít; a helper x87 csonkoló kerekítést állít (`0x008eeaad`–`0x008eeab8`). A munkavégző `0x00bb5b60` `Steps == 2` esetén 2-t, máskor `Steps − 1`-et ad a redukálónak (`0x00bb5da8`–`0x00bb5dc8`). | `2,9 → 2`, `8,9 → 8`, `30,9 → 30`; a negatív kontrollok is nullához csonkolnak. A helper leletét megerősíti. |
| `Smoothing` | a leíró kifejezése a `BlurImageOperation` `xblur`/`yblur` értéke; az alkalmazó `0x00bb4de0` tengelyenként a `0x00bb5050` sugár-kvantálót, majd a `quality=3` értékkel a `0x00bc5680` natív elmosóutat hívja. | A leíró 0/80/100 csúszkaértékeiből kapott sugárpróba: `10,1 → 10,100000381469727`; `2,1 → 2,0999999046325684`; `0,1 → 0`; a `2,01`/`2,03 → 2,065000057220459`, `3,01`/`3,02 → 3,0625`, `4,01`/`4,05 → 4,130000114440918`, `5,01`/`5,06 → 5,130000114440918` küszöbpróbák ugyanezt a kvantálót erősítik. A skálár lelet egyezik; a teljes képes elmosás nem futott le. |
| `Fade` | a külső `NestedImageOperation` a bemenet másolatán futtatja a gyerekeket, majd a `BlendAlpha` szerint visszakeveri (4.5); a keverő `0x00bd0700` → `0x009dc4b0`. `w = trunc(α·256)`, majd `w>0` esetén `w−1`; páros szélességű SIMD-rész: `ki = (B·(255−w) + A·w) >> 8`. | Nincs teljes képpontos mérés. A natív függvény utasításolvasása adja a fenti képletet; páratlan szélesség utolsó pixelének skalárképlete különbözik: `ki = A + ((B−A)·w >> 8)` (`0x009dc646`–`0x009dc6fb`). |

**A Smoothing sugárának pixeles jelentése.** Az XML-beli érték a `BlurFilter`
`xblur`/`yblur` sugara, nem Gauss-σ (`0x00bb4de0`, `0x00bb5050`). A natív
út futóablakos, fixpontos dobozszűrő: a sugárhoz tartozó együtthatókat a
`0x00bc5360` készíti elő, a kimeneti menet egész osztással bájtot ír, a
határmintákat a kép szélére vágja/ismétli. `quality=3` esetén 3 vízszintes,
majd 3 függőleges menet fut (`0x00bc7540`, `0x00bc77b0`). A teljes
`(k,h,w,osztó)` súlyparaméterezés és a menetképlet a későbbi „A `DropShadow`
`quality=3` natív elmosása” és „Kiolvasva, emulátorral bitre igazolva”
szakaszban van dokumentálva (`0x00bc5360`, `0x00bc5480`, `0x00bc6590`); a
quantize-út ugyanezt a `0x00bc5680` diszpécsert hívja.

**A mi kódunkhoz képest.** A `glimmer_tone.apply_quantizepalette` a
`fade_alpha(fade)` értéket adja át; a segédfüggvény `1−Fade/100`-at ad, tehát
az alfa iránya egyezik a leíróval. A közös `alpha_blend` az SIMD-képletet
alkalmazza a többi oszlopra; páratlan szélességnél a sor utolsó pixelét a
natív skalárképlettel keveri (#4157). A palettaépítő
(`render/quantize_palette.py`, `kvantal`) a natív attribútumúthoz igazodva
csonkolja a `Steps` értékét: például közvetlen `Steps=8,9` hívásnál az eredmény
8 (#4157). A leíró csúszkájának egészértékű lépésköze nincs igazolva, ezért a
felületi hatás nyitott.

A szélességkülönbség ellenpéldája a natív képletből: `α=0,5` esetén
`w=127`; `B=0`, `A=255` mellett a SIMD-képlet 126-ot, az utolsó oszlop
skalárképlete 128-at ad. A mostani általános `alpha_blend` a 126-os ágat
alkalmazza az utolsó oszlopra is.

**Cáfoló próba.** A `qemu-i386` skalárpróba az `8,9 → 8` eredménnyel
cáfolja a kerekítés-paritást; a sugárpróba a fenti küszöb körüli bemenetekkel
ellenőrizte a disassemblyből olvasott ágakat. Az első teljesmunkavégző-próba
`R6030 - CRT not initialized` hibával állt le; a 2026-10-04-i második kör
heap-shimekkel túljutott ezen, de a képpontátalakítóban a futás
szegmentálási hibával végződött (az alábbi alfejezet). Egyik futás sem adott
pixel-goldent, és nem teljesíti a négy `Steps`/`Smoothing` kombinációs
elfogadást.

**Fejlesztői eltérés (megvalósítva #4157):** a `Steps` törtértékét a
`kvantal()` a natív csonkolással alakítja egészre; a közös Fade-keverő pedig
páratlan szélességnél a sor utolsó oszlopára a
`0x009dc646`–`0x009dc6fb` skalárképletet alkalmazza. A páros/páratlan
keverést és a `Steps=8,9 → 8` esetet bájtpontos regressziós teszt fedi.

*Bizonyítottsági fok: `Steps` csonkoló segédfüggvénye és a blur-sugár
kvantálója **megerősített** (utasításolvasás + független qemu-i386 futtatás);
a teljes `QuantizePalette`-kimenet és a `Fade` összetett képpontútja
**feltételes** (a teljes műveletet nem sikerült qemu alatt futtatni, és
nincs négykombinációs byte-golden).*

**Későbbi állapotfrissítés:** a következő első QEMU-próba valóban félbeszakadt;
az azt követő „A QuantizePalette képadat-leírója és a négy QEMU-pár” szakasz
rögzíti a javított descriptorral mért kimenetet, és felülírja ezt a nyitott
státuszt.

### A teljes munkavégző első QEMU-próbája — az akkori képadat-leíró hibás volt (2026-10-04, #626)

A helyi harness másolata a `.bt/harness-626q/` könyvtárban készült; a privát
`~/picasapy-agent/eszkozok/qemu_harness/` eredeti fájljaihoz nem nyúltam. A PE
belépési pont `0x00bef35e` a `___security_init_cookie`
(`0x00bf0b56`) után a `___tmainCRTStartup` (`0x00bef17e`) útjára tér; ez az
indítás hívja a `__heap_init` (`0x00bf0904`), `__mtinit` (`0x00bf0725`),
`__ioinit` (`0x00beffc8`) és `__cinit` (`0x00bef5d3`) rutinokat. A teljes
alkalmazásindítás helyett a harness másolata a `_malloc` (`0x00bf426f`),
`_free` (`0x00bf219e`), `__calloc_crt` (`0x00bf226c`), `__realloc_crt`
(`0x00bf22b4`), `__recalloc_crt` (`0x00bf22ff`) és a Picasa-allokátor
(`0x0097c5d0`) belépési pontjait egy futásonként új, determinisztikus
bump-arénára irányítja. A `free` no-op; a blokk mérete a `realloc`/
`recalloc` számára a blokk előtt tárolódik. Az IAT `InterlockedIncrement`/
`InterlockedDecrement` hívásai is lokális assembly-shimre mutatnak. A
`0x00d67838` globális dword négy bájtra nullázását a harness szintén
elvégzi; e globális változó szerepét külön nem izoláltam.

Az eredeti `R6030` üzenet a shimek telepítése után már nem jelent meg: a futás
elérte a `0x00bcb2f0` képpontátalakítót. A `q626-final` futás naplójának
utolsó állapota `EIP=0x00bcb399`, `EDI=0x50230000`; a következő utasítás
`0x00bcb3a0` a `[EDI+2]` bájtot olvassa. Ez a cím nem a wrapper által megadott
`0x10060000` bemeneti puffer vagy a shim `0x10100000`-tól induló arénája;
a mutató forrása nem azonosított.
Ugyanez a futás `qemu-i386` alatt `SIGSEGV`-vel tért vissza, kimeneti bájt
nélkül. Az utasítás és regiszterállapot binárisdisassemblyval, illetve a
QEMU-regiszternaplóval ellenőrizhető; a hibás képadat-objektum pontos
invariánsa és az, hogy melyik natív létrehozó út állítja elő a `0x50230000`
mutatót, **NINCS MEG**.

A `wq.py` diagnosztikai hívása közvetlenül a `0x00bb5b60` belső
kvantálómunkavégzőt hívta `Steps=8`, `Depth=4` értékkel, szintetikus
`32×24` BGRA képpel. A Glimmer külső `Blur`- és `Fade`-lépését nem futtatta;
ez a próba a teljes effekt összehasonlítására sem lett volna elegendő még
érvényes kimenet mellett sem.

A helyi user `systemd` scope nem volt elérhető, ezért a tesztfuttató közvetlen
`qemu-i386` fallbacket használt `timeout`-tal és
`RLIMIT_AS=(mem_mb+4096) MiB` értékkel. A 4 GiB ráhagyás a QEMU i386
vendégcímtér-leképezéséhez kellett; ez nem cgroup- vagy RSS-korlát. A
README-ben ez és a CRT-shim alkalmazása dokumentálva van a következő
kutatási szeleteknek.

**Eredmény és határ:** a heap-shim a CRT-inicializálási akadályt megkerüli,
de nem bizonyítja a natív kimenetet vagy az objektum inicializáltságát. A
legalább négy `Steps`/`Smoothing` pár, mindegyik `Fade=0` és `Fade=50` mellett,
nem futott le; ezért nincs bájtpontos összevetés, és nincs mérésből igazolt
új fejlesztői eltérés sem. A következő próbának előbb a `0x00bb5b60` által
várt képobjektumot a bináris valódi előállító útjával létrehoznia, majd
a `0x00bcb2f0` bemenő descriptorának `+4` pixelmutatóját és sorlépését kell
QEMU-ban ellenőriznie a dereferálás előtt.

*Bizonyítottsági fok: feltételes — a CRT-hookok célcímei és a futás
megállási címe binárisdisassemblyval és a QEMU-próbával alátámasztott;
pixelmatematika és renderelővel való egyezés nincs mérve.*

**Állapot:** ez az első, hibás bemeneti/kimeneti descriptorral futott kör
történeti jegyzete; az alábbi, azonos dátumú folytatás felülírja az akkori
„NINCS MEG” állapotot és a javasolt következő lépést.

### ✅ A QuantizePalette képadat-leírója és a négy QEMU-pár (2026-10-04, #626)

#### A valódi képadat-rekord és a `0x00bcb2f0` lokális nézete

A `0x00bb5b60` belépő képadat-rekordja nem azonos a képponti munkavégzőnek
átadott lokális descriptorral. Az elsőt a `0x00bb5f1a`–`0x00bb5f65`
utasítások olvassák; ugyanezt az elrendezést a másik képművelet-út
`0x009e7420` mintavételezője is használja:

| rekord | mező | jelentés |
|---|---:|---|
| Image record (`0x00bb5b60` bemenet) | `+0x04` | sorlépés, pixelben; bájtcímhez `×4` |
| | `+0x08` | szélesség pixelben |
| | `+0x0c` | magasság pixelben |
| | `+0x10` | képadat kezdőcíme |
| | `+0x18`, `+0x1c` | x/y origó |
| `0x00bcb2f0` bemenő view | `+0x04` | pixelbázis |
| | `+0x08` | ebben a futásban nulla; szerepe **NINCS MEG** |
| | `+0x0c`, `+0x10` | szélesség, magasság |
| | `+0x14` | sorlépés, pixelben; bájtcímhez `×4` |
| | `+0x18`, `+0x1c` | x/y origó |

A hívó a valódi image record `+0x10` adatmutatóját és `+0x04`
sorhosszát (`0x00bb5f30`–`0x00bb5f65`) a lokális view `+0x04` és
`+0x14` mezőibe másolja. A `0x00bcb2f0` `EBX=[EBP+0x0c]` pointeréből
veszi az input bázist (`mov edi,[ebx+4]`, `0x00bcb360`) és a stride-ot
(`imul ..., [ebx+0x14]`, `0x00bcb368`); a kimeneti bázist a harmadik
pointerargumentum `+0x04` mezőjéből, stride-ját annak `+0x14` mezőjéből
veszi (`0x00bcb37a`–`0x00bcb385`).
Így a korábbi hibás futás `EDI=0x50230000` értéke a `0x00bcb2f0`
`[input-view+0x04]` mezőjéből jött (`0x00bcb360`–`0x00bcb371`); a valódi
hívó e helyet a belépő image record `+0x10` adatmutatójából állítja elő.
A régi crashnél ezt a view-t nem naplóztuk, így maga a `0x50230000`-hez
vezető hibás rekordérték **NINCS MEG**. A javított mérésben ugyanennek a
mezőnek az értéke a megadott bemeneti puffer `0x10070000` volt.

**Csatornarend:** 4 bájt/pixel, memóriában BGRA. A `0x00bcb3a0`–
`0x00bcb422` a `[+2]` bájtot a vörös (`+0x800` LUT), `[+1]`-et a zöld
(`+0x400`), `[+0]`-t a kék (`+0`), `[+3]`-at az alfa (`+0xc00`) rekeszhez
viszi; a `0x00bcb4ae`–`0x00bcb4ba` ugyanilyen bájthelyekre ír vissza.
Az image-record pixelformátum-enum vagy az `+0x08` view-mező szemantikája
**NINCS MEG**; a vizsgált út bájtsorrendje és 32 bites pixele viszont
utasításszinten megvan.

Az első bcb-hívás helye `0x00bb5fe9`: a 51×49-es QEMU-futásban az input
view `+0x04=0x10070000`, a kimeneti view `+0x04=0x10107950`, méretük
51×49, stride-juk 51 volt. A második hívás `0x00bb6110` ugyanezt a belső
kimeneti view-t adja inputként és outputként, tehát in-place lépés.
Mindkét eredeti hívást a futás közben naplóztam. A korábbi hibás harness a
saját külső célpufferét olvasta, amelyet ez a belső kimeneti view nem használ;
ezért lehetett a worker sikeres visszatérése mellett az ottani puffer nulla.

#### Natív futás és byte-összevetés

A QEMU-harness-másolat a `.bt/harness-626q3/` alatt futtatta az eredeti
`0x00bb5b60` munkavégzőt, majd az eredeti `0x009dc4b0` alpha-blendert.
A tesztkép determinisztikus, szintetikus 51×49 BGRA volt; a négy egész
Steps/Smoothing pár a leíró szerinti elmosás után került a natív workerbe.
A Fade=50 blend súlya `w=127`: az assembly a `trunc(α×256)` értéket
pozitív esetben eggyel csökkenti (`0x00bd0a72`–`0x00bd0aaa`,
`0x009dc561`); a SIMD-képletet és az odd-width scalar ágat is közvetlenül
QEMU-ban futtattam.

| `Steps` | `Smoothing` | sugár | quant pixel-eltérés (RGB) | Fade 0 RGB-bájt eltérés | Fade 50 RGB-bájt eltérés 51×49-en | max. |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0 | 10,1 | 0/2 499 pixel | 0/7 497 | 36/7 497 | 1 |
| 8 | 80 | 2,1 | 0/2 499 pixel | 0/7 497 | 51/7 497 | 1 |
| 16 | 50 | 5,1 | 0/2 499 pixel | 0/7 497 | 63/7 497 | 2 |
| 30 | 100 | 0,1 | 0/2 499 pixel | 0/7 497 | 77/7 497 | 1 |

A négy natív quant-kimenet byte-ra egyezik a `kvantal()` kimenetével;
Fade=0-nál a `BlendAlpha=1` miatt a kvantált kép változatlanul kerül ki.
Fade=50-nél a natív blend-kimenet mind a négy beállításban byte-ra egyezik
az utasításokból számolt eredménnyel. A PicasaPy eltérés kizárólag a páratlan
szélesség utolsó oszlopában van. Cáfoló szélességkontroll: 50×49, 8/80;
Fade=0 és Fade=50 esetén is 0/7 350 RGB-bájt eltérés.
Például 16/50, `(x=50,y=22)`, vörös: eredeti `0`, kvantált `147`, natív
Fade50 `74`, PicasaPy `72`; ez a páratlan sorvégi skalárág két szintes
eltérését adja.

#### Független utak, cáfoló kontroll és más műveletek

**Két független út:** A) `0x00bb5b60` utasításai követik a forrás image
record stride- és adatmutatómezőit a lokális view-ig; a `0x009e7420`
független képművelet-út ugyanezeket a `+0x04/+0x08/+0x0c/+0x10` mezőket
olvassa. B) az eredeti `0x00bb5fe9`/`0x00bb6110` hívások QEMU-mezőnaplója
ugyanezt a layoutot mutatja, a kimeneti pointerről kiolvasott pixelek nem
nullák. A mezőszerepek egyeznek. A pixelmatematikánál az eredeti
`0x009dc4b0` QEMU-outputja mind a négy Steps/Smoothing esetben egyezik a
disassembly-képlettel.

**Cáfoló kísérlet:** az a hipotézis, hogy a külső harness-célpuffer `+0x04`
mezője a bcb végső kimenete, hamisnak bizonyult: a QEMU-hívásnál a valódi
output view `+0x04=0x10107950`, és annak pufferében nem nulla pixel van.
Az odd-width magyarázatot a páros 50×49 kontroll cáfolhatta volna; azon nem
volt eltérés, míg a páratlan 51×49 futásokban az eltérések mind a sorvégi
scalar ágra estek.

A ColorMatrix közvetlen QEMU-kontrollja a `0x008f2640` pixelkernelt
kézi BGRA pixel-dwordokkal futtatja; az nem a teljes `0x00bb5b60`
image record vizsgálata. A Border-próba (`0x00bbe570` → `0x00aa13b0`)
saját, kézzel összeállított 9×9 ARGB bitmapet használ, de annak record-offsetjei
nincsenek a jelenlegi mérésekben. Ezért a ColorMatrix kernel inputja nem
bizonyság az image-record azonosságára, a Border-descriptor byte-offsetű
egyezése pedig **NINCS MEG**.

#### Eltérés a jelenlegi rendererben

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `0x00bb5b60` quant-kimenete mind a négy egész Steps/Smoothing párnál | `glimmer_tone.apply_quantizepalette()` / `quantize_palette.kvantal()` | A mért paraméterpárokra nincs eltérés; nem igényel fejlesztést. |
| `0x009dc4b0`: 8 bájtos MMX-párok képlete `(B·(255−w)+T·w)>>8`; páratlan pixelszélesség maradék pixelje: `T+((B−T)·w>>8)` (`0x009dc646`–`0x009dc6fb`) | `glimmer_ops.alpha_blend()` az SIMD-képletet tartja meg a többi oszlopon, az odd-width sorvégi pixelen pedig a skalárképletet (#4157) | Megvalósítva; a bájtpontos páros/páratlan regressziós teszt a 72/74-es példát is ellenőrzi. |

**Bizonyítottsági fok:** `megerősített` a fenti record-mezőkre, byte-sorrendre,
négy kvantálóbeállításra és Fade=50 algoritmusra: az utasításszintű olvasat
és az eredeti QEMU-futtatás egyezik. **Nyitott:** a top-level `+0x14` és a
view `+0x08` szemantikája, formátum-enum értéke, valamint a Border harness
recordjának azonossága. Ez a szintetikus QEMU-worker-mérés nem oldja meg a
korábbi 4. szakasz kérdését, hogy a valódi Picasa-export miért nem az
oktree-út eredményét mutatja; a teljes `QuantizePalette` effekt összesített
bizonyítottsági foka ezért továbbra is **feltételes**.

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

⛔ **HELYESBÍTVE (2026-10-01, #3541): a „ÖT festhető effekt" és a „kettőt ismerünk az ötből" állítás a `Mask`-ot kapó szűrők HALMAZÁRA igaz (a `filterdesc.xml` öt sora), de FESTHETŐ csak EGY: a `ReanimatedEyeColor`.** A `cnt:PaintEffectCanvas` mód-táblázati értéke 0, ezért a `Boost`, `Pixelate`, `Soften`, `PicnikTint` `Mask="{_mctr.mask}"` hivatkozása nem oldódik fel, és az effekt az egész képre hat — ld. a `### 6.` szakaszt (lent). (A szakasz címe az `tests/render/test_festheto_maszk_ot_effekt_3055.py` kapaszkodója, ezért változatlan.)

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

⛔ **HELYESBÍTVE (2026-10-01, #3541): a `ReanimatedEyeColor`-ra ez TÉVES.** A festett vonások a lánc-elem vonáslistájában élnek, és a `filters=` sorba is kiíródnak, majd visszaolvasódnak — ld. a `### 6.` szakaszt. A másik négy effektnek (`Boost`, `Pixelate`, `Soften`, `PicnikTint`) pedig egyáltalán nincs festhető maszkja.

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
| tárolja-e a Picasa **máshol** (db3) | ✅ **NEM találtunk rá oszlopot** — ld. a következő szakaszt |
| milyen az ecset FELÜLETE | ✅ **MEGVAN** — ld. a következő szakaszt |

## ⛳ Az ecset-felület és a db3-tárolás — mindkettő mérve (2026-09-15, #1908)

*Forrás: `filterdesc.xml:1279`; `referencia/tre-eroforrasok/editpanel.tre:501`,
`:864`, `:866`, `:869`, `:961`, `:962`; `thumbui.tre:113`;
`referencia/stringres-en-hu.tsv`; `referencia/i18n/cs/stringres.xml:1530`;
`Picasa3.exe` `0x005d59f0` · `0x008e3bd0` · `0x008e3dd0` · `0x008fcfa0` ·
`0x008fe9b0`; három valódi db3-telepítés a `research/testdata/` alatt.*

### 1. A két család KÉT különböző ecset-felületet kap

| befoglaló | mit deklarál az ecsethez | melyik szűrők |
|---|---|---|
| **`eff:PaintOnEffectBase`** | `_nBrushHardness="0.15"` **és** `<BrushSizeAndEraserButton id="_brshbtn" startValueFactor="0.03" maximumFactor="0.2"/>`; az értéke `_cxyBrush = {_brshbtn.value}` | `ReanimatedEyeColor` |
| **`cnt:PaintEffectCanvas`** | **SEMMIT** — se ecsetméret, se keménység, se radír | `Boost`, `Pixelate`, `Soften`, `PicnikTint` |

⇒ A jegy „ami mérve van" táblája (`_nBrushHardness`, `startValueFactor`,
`maximumFactor`) **kizárólag a `PaintOnEffectBase`-re igaz**. A másik négy
szűrőnél ezek az értékek **nincsenek** a leírásban: az ecsetet a kanavász
adja, nem a szűrő.

### 2. Az ecset vezérlői és feliratai

A `BrushSizeAndEraserButton` **két** vezérlő egyben (méret + radír) — a
kötéseit a szűrőmotor nevezi meg (`0x008e3bd0`, `0x008e3dd0`):

| kötés | mi |
|---|---|
| `_brshbtn.value` | az ecsetméret |
| `_brshbtn.selected` | ecset **vagy** radír van kiválasztva |
| `_btnEraser.selected` | a radír-gomb állapota |
| `brushAlpha`, `brushRotation` | az ecsetnyom átlátszósága és forgatása |

| felirat-kulcs | EN | HU |
|---|---|---|
| `ImageFilters::BrushSize` · `CThumbUI::BrushSize` | *Brush Size* | **Ecsetméret** |
| `CThumbUI::EraserSize` | *Eraser Size* | **Radír mérete** |
| `ImageFilters::Eraser` | *Eraser* | **Radír** |
| `ImageFilters::BlurXY` | *Color Brush* | **Színes ecset** |

⚠️ **A `BlurXY` kulcs nem a nevét jelenti.** A kulcs *„Blur XY"-t* ígér, a
szöveg viszont *„Color Brush"* — és ez **az eredetiben van így**, nem a mi
táblánk hibája: a `referencia/i18n/cs/stringres.xml:1530` ugyanezen a
kulcson *„Barevný štětec"*-et (= színes ecset) ad. Kulcsnévből tehát itt sem
szabad jelentést következtetni.

### 3. Az ecset MEGJELENÍTÉSE: kör alakú kurzor, a mérettel skálázva

A `.tre` kimondja a teljes bekötést:

```
thumbui/circlecursor: root                                      (thumbui.tre:113)
brushslider/scaleslider: root                                   (editpanel.tre:866)
brushslider/thumb: brushslider/scaleslider                      (editpanel.tre:864)
editpanel/brushslider_container: editpanel/retouch_well         (editpanel.tre:869)
editpanel/eraserbutton: editpanel/editcontrol_well              (editpanel.tre:501)

Handler dragscale thumbui/circlecursor brushslider/scaleslider 100      (:961)
Handler retoucher thumbui/circlecursor brushslider/scaleslider
        editpanel/refining_label editpanel/preview                      (:962)
Property showtarget thumbui/circlecursor                                (:226)
Property hidetarget thumbui/circlecursor                                (:899, :911)
```

⇒ **A mutató alakja egy kör** (`thumbui/circlecursor`), amelynek átmérőjét a
**`brushslider/scaleslider`** csúszka állítja (`dragscale`-lel közvetlenül
húzva is, `100`-as léptékkel), és amelyet a `showtarget`/`hidetarget`
tulajdonság kapcsol be-ki. Nincs külön előnézeti réteg: a kör maga a
visszajelzés.

⚠️ **Hatókör:** ez a `.tre`-ben a **javítóecset** (`retouch_well`,
`Handler retoucher`) bekötése. Hogy a festhető-maszkos szűrők UGYANEZT a
csúszkát és kurzort kapják-e, vagy a szűrőmotor saját
`BrushSizeAndEraserButton`-ja rajzol, a `.tre` nem mondja meg — a
`_brshbtn` a `filterdesc.xml` oldalán él. **Ez marad nyitva**, és az
átvételhez nem szükséges: mindkét olvasat ugyanazt a felületet írja le
(kör alakú kurzor + méretcsúszka + radírgomb).

### 4. A db3-tárolás: NEM találtunk maszk-oszlopot

A 296. kör nyitva hagyott kérdése („tárolja-e a Picasa **máshol**, pl. a
`db3`-ban") — a teljes oszlop-leltár **három, egymástól független valódi
telepítésből**:

| korpusz | fájl | maszk-gyanús oszlop |
|---|---|---|
| `research/testdata/Picasa2/db3` | 78 | **nincs** |
| `research/testdata/Picasa2-arcok/Picasa2/db3` | 84 | **nincs** |
| `research/testdata/1557-masolat-mentese/db3-utana/db3` | 84 | **nincs** |

Egyik telepítésben sincs `mask`/`paint`/`brush` nevű `.pmp`, és a binárisban
a `mask`/`brush` nevű sztringek **mind** a szűrőmotorban ülnek
(`0x00bb31f0`–`0x00bcfff0`: `imageOperations:CircularGradientImageMask`,
`TiledImageMask`, `PaintEffectCanvas`, `_mctr.mask`, `maskWithSourceAlpha`) —
egyikük környékén sincs `.picasa.ini`, fájlútvonal vagy db3-oszlopnév.

⛔ **A hatókört kimondom:** ez **korpusz-negatívum + a szűrőmotor
sztringkészlete**, nem a bináris kimerítő pásztázása. A db3 oszlopnevei
ugyanis **nincsenek egyetlen regisztrálóban**: a `0x004127c0` 37
`imagedata`-oszlopot nevez meg, de a `crop64`, `tags`, `lat`, `geoview`,
`avgcolor`, `suppress` és `text` **nincs** köztük, pedig mind a három
korpuszban ott a fájljuk. Egy hiányzó oszlopnév tehát elvben átcsúszhat.
**A bizonyíték ereje:** három független telepítés, nulla találat.

⇒ **Termékdöntéshez elég:** a festett maszk **munkamenet-élettartamú**, ha a
Picasát vesszük mintának. Saját tárolás bevezetése a mi döntésünk, és nem
sérti az ini-kompatibilitást (a maszknak ott nincs mezője).

### 5. ⛳ Festés NÉLKÜL az egész képre hat — a szerkesztőben, a bélyegképen és az exportban is (2026-09-26, #3541)

⛔ **HELYESBÍTVE (2026-10-01, #3541): az alábbi „A mechanizmus a binárisból" és a „teljes fedésű alapmaszk" magyarázat TÉVES** — a `PaintEffectCanvas` mód-táblázati értéke 0, ezért a `0x00bb3ff0` a négy effektnél SOHA nem fut; a helyes olvasat a **6. szakasz** (lent). A mért (élő) tábla és a következtetés — festés nélkül az egész kép, a szerkesztőben, a bélyegképen és az exportban — helyes maradt, sőt a 6. szakasz ezt a négy effektre **általánosítja**: nem csak festés nélkül, hanem **egyáltalán** nem festhetők.

*Forrás: élő mérés, eredeti angol Picasa 3.9.141 (picasa-colab-jobs #56, #57; kulcsképek: `Colab EN 31 - Pixelate panel.png`, `Colab EN 32 - Pixelate mentes nelkul, belyegkep.png`) · `0x00bb3ff0` · `0x00bc06b0` · `0x00bc0770`.*

**A mechanizmus a binárisból.**
- A `PaintEffectCanvas` kezelője (`0x00bb3ff0`) egyetlen saját attribútumot olvas (`_nBrushHardness`, `0x00cefbd8`, alapérték 0,0). Ezután létrehozza a `glimmer::PaintMaskPlusImageMask` objektumot (`0x00bc06b0`, vtábla `0x00cf0750`), amely a `_mctr.mask` nevet hordozza (`0x00cf0740`). A `0x008ee120` ezt változóként jegyzi be.
- A maszk rajzolója (7. rés, `0x00bc0770`) a render-környezet `+0x28` objektumából dolgozik. Ha annak változat-mezője (`+0x9c`) 0, vagyis még nem festettek, a `+0x8c` alapmaszkot másolja (`0x00bc079d`–`0x00bc07a6`). Különben a festett réteget (`+0x64`) építi be (`0x00bc07d0`).
- A keverés a teljes `MaskInstruction` (ld. B) fent): `t·m + b·(255 − m)`.

**Élőben, a Pixelate-tel, egy részletgazdag képen:**

| lépés | eredmény |
|---|---|
| a panel | Pixel Size · Blend Mode · Fade · Apply · Cancel — **ecset-vezérlő nincs** |
| Pixel Size fel, festés nélkül | az **egész kép** pixeles |
| egy kattintás a képre | nem változik |
| Apply, majd Back to Library, **mentés nélkül** | a **bélyegkép** az egész képen pixeles |
| Export (Ctrl+Shift+S) | az **exportált fájl** az egész képen pixeles (800 × 800) |
| `.picasa.ini` | `filters=Pixelate=1,143.076019,9.000000,0.000000;`: csak a csúszkák, maszk nincs |

⇒ **Festetlen állapotban az alapmaszk teljes fedésű**: az effekt a szerkesztőben, a bélyegképen és az exportban egyformán az egész képre hat. A PicasaPy ugyanezt teszi: a festetlen maszk `None`, és a lánc a maszk nélküli úton fut (`app/paint_mask.py:109`–`120`).

⛔ **Helyesbítés:** az `app/paint_mask_controller.py` fejléce azt írja, hogy ezek az effektek „az eredetiben csak a BEFESTETT területre hatnak”. Festés nélkül ez nem igaz, a mérés szerint az egész képre hatnak.

**Ami NYITVA marad, megnevezett úttal:** a **befestett** állapot. Az eredetiben a festés egérhúzással történik a vásznon; a panelen nincs rá vezérlő. A Colab-végrehajtó ma csak kattintani tud, ezért ez nem mérhető → **picasapy-agent #161** (húzás lépés). Ugyanitt dől el, hogyan állít ecsetméretet az eredeti. Nálunk a panelen „Brush Size” csúszka van (`EditorParamPanel.qml:308`–`340`), az eredeti panelén nincs.

*Bizonyítottsági fok: megerősített* (a festetlen állapot: bináris + élő mérés, a szerkesztő, a bélyegkép és az export egyezik); a befestett állapot **NINCS MÉRVE**.

### 6. ⛳ HELYESBÍTÉS: négy effektnek NINCS festhető maszkja — csak a `ReanimatedEyeColor` festhető, és a vonásai a `filters=` sorban élnek (2026-10-01, #3541)

*Forrás: a kanavász-mód-tábla `0x00d261e0`–`0x00d26210` (kiolvasva a fájlból) · az olvasó `0x00bb4301` · a kezelő `0x00bb23d0` (`0x00bb23e5`–`0x00bb2401`) · `0x00bb3ff0` · `0x00bc06b0` · `0x00bc0770` · `0x00bc0a62`–`0x00bc0a7c` · `0x00bc0ee4` · `0x00bc4ae0` (`0x00bc4d20`…, `0x00bc4e0d`, `0x00bc4e4b`, `0x00bc5088`) · `0x008e3980` · `0x008e3c70` · `0x008f4810` · `0x008f7140` · a vonás-sorosítás `0x008fac40` (14. rés), `0x008fb120` (42. rés), `0x008fa8d0` (3. rés), `0x008fbf10` (22. rés), `0x009079b0` · a bélyegkép `0x0069f510` → `0x00907f30` · élő mérés: `picasa-colab-jobs` #56, #57 · mért export: #685, #688.*

**A kérdés (#3541):** mit mutat az eredeti a bélyegképen és az exportban, ha egy festhető-maszkos effekt MENTETLEN, és be van festve?

**Válasz — két, egymástól független olvasat egyezik a döntő pontban** (a második a specek és az első válasz nélkül, friss Opus-ügynök; az első olvasat a `0x00bb3ff0`-ból indult, a mód-táblát nem nézte — emiatt jutott ellentmondásra, amit a második olvasat oldott fel):

**1. A mód-tábla dönt, nem a kezelő.** A kanavász-tábla 12 bájtos elemekből áll (névtér, név, mód):

| név | mód | mit csinál a kezelő (`0x00bb23d0`) |
|---|---:|---|
| `cnt:EffectCanvas` | 0 | semmit (`0x00bb23f5` `jne 0x00bb24f5`) |
| **`cnt:PaintEffectCanvas`** | **0** | **semmit** — a `0x00bb3ff0` NEM fut |
| `cnt:CircularOverlayEffectCanvas` | 1 | az `xFocus`/`yFocus` ág (`0x00bb2406`) |
| **`eff:PaintOnEffectBase`** | **2** | **ez hívja a `0x00bb3ff0`-t** (`0x00bb2401`) — az egyetlen út, amely `glimmer::PaintMaskPlusImageMask`-ot épít |

A módot a `0x00bb4301` `mov eax, [eax*4 + 0x00d261e8]` olvassa; a kezelő a `0x00bb23e5`-nél `sub eax,1; je` (1-es mód) és `sub eax,1; jne 0x00bb24f5` (0: kilép), a 2-es mód esik át a `call 0x00bb3ff0`-ra. A `0x00bb3ff0`-nak egyetlen hívója a `0x00bb2401`, a `0x00bc06b0`-nak egyetlen hívója a `0x00bb4106` (indextől független teljes `.text`-pásztázás, a független olvasat).

**2. Mi következik ebből.**

| effekt | vászon · mód | festhető? | üresen (nincs vonás) | bélyegkép és export |
|---|---|---|---|---|
| `Boost` | `PaintEffectCanvas` · 0 | **NEM** | **egész kép** | egész kép (= a szerkesztő) |
| `Pixelate` | uo. | **NEM** | **egész kép** (élő: #56, #57) | egész kép (élő: a bélyegkép és az export mért) |
| `Soften` | uo. | **NEM** | **egész kép** (#685: ΔE 5,5) | egész kép |
| `PicnikTint` | uo. | **NEM** | **egész kép** (#685: ΔE 36,9) | egész kép |
| `ReanimatedEyeColor` („Vámpírszem") | `PaintOnEffectBase` · 2 | **IGEN** (`BrushSizeAndEraserButton`, `_nBrushHardness`) | **nincs effekt** (#688: ΔE 0,18) | a vonásokból újraépített maszk: **csak a festett terület** |

**Miért az egész kép a négy effektnél:** a `Mask="{_mctr.mask}"` hivatkozás nem talál semmit, mert a mód-0 vászon nem épít `_mctr.mask` nevű maszkot. A `glimmer::BlendImageOperation` maszk-rése (`0x00bc4ae0`) a „Mask" attribútumot név szerint keresi a leíró maszklistájában (`0x00bc4d20`…); ha talál, `MaskInstruction`-t tesz be (`0x00bc4e0d`), **ha nem talál: `0x00bc4e4b` → `0x00bc5088`, csak egy `PopInstruction`, maszk nélkül** ⇒ az effekt az egész képre hat. Ez magyarázza az élő mérést (a Pixelate panelén nincs ecset-vezérlő, és festés nélkül az egész kép pixeles), és a #688 mérését (`ReanimatedEyeColor` üresen változatlan, `PicnikTint`/`Soften` az egész képen).

**3. A festett réteg a `ReanimatedEyeColor`-nál.** A festés NEM a render-környezetben, hanem a lánc-elem (`CGenericFilter`) `+0x00bc` vonáslistájában él:
- az egérkezelő (22. rés `0x008fbf10`) a normalizált pontot (x/szélesség, y/magasság) a `0x008e3dd0`-val új vonásként a lista végére fűzi (`0x008e408e`), folytatás `0x008e4130`;
- a maszk-réteg (a `0x008e3c70` konstruktorú objektum `+0x64` tagja) **származtatott gyorsítótár**: a vonásokból lustán épül újra — a bemenet méretén foglal, **nullára törli** (`0x00bc0a62`–`0x00bc0a7c` → `0x009a8d80`), és vonásonként rárajzolja (`0x00bc0ee4` → `0x008ec3a0`); a bemenet változásakor eldobja (`0x00bc07d0`);
- a keverő (`0x008f4810`, SIMD) a maszk alfáját veszi: `effekt·a + alatta·(255 − a)` ⇒ a nulla réteg = **nincs effekt**;
- a `+0x8c`/`+0x9c` NEM „változat-mező / teljes fedésű alapmaszk" (az 5. szakasz olvasata téves): a `+0x8c` a maszk-művelet alatti (bemeneti) kép másolata, a `+0x9c` ennek adatmutatója, nulla csak az első rajzolás előtt.

**4. A vonások a `filters=` sorban vannak, és a bélyegkép/export onnan építi újra.**
- A lánc-szerializáló (`0x009079b0`) szűrőnként a `vtbl+0x38`-at hívja (`0x00907a2f`), formátum `"%s=%s%c"`; a szűrő 14. rése (`0x008fac40`) a csúszkák UTÁN **vonásonként** kiírja: `,%f:%g:%g:%d` + (új ecsetnél) `:%g:%g` + `:%g|%g|%g|…` (sztringek: `0x00cd0970`, `0x00cd0980`, `0x00cd097c`, `0x00cd0984`; ciklus `0x008faf93`–`0x008fb10e`; **nem feltételes**). A mért `Pixelate=1,143.076019,9.000000,0.000000;` ennek a vonás NÉLKÜLI kimenete.
- Az elemző (42. rés `0x008fb120`) a maradékot `:` mentén 5 vagy 7 részre (`0x008fb947`), a pontokat `|` mentén (`0x008fbbb1`) bontja, és hozzáfűzi a vonáslistához (`0x008fbb5e`). A klón (3. rés `0x008fa8d0`) mélymásolja.
- A bélyegkép (`0x0069f510` „filters" sor → `0x00907f30` → `0x008f7140`) és a renderfeladat (`0x006b2db2`) a láncot **sztringből** építi újra, új render-környezettel (`0x008f7140`) — tehát a vonásokat is. A render-környezetet kizárólag a `0x008f7140` hozza létre; a vonások mindkét úton (sztring, klón) megvannak.
- **Beégetés nincs**: ideiglenes képfájlt vagy a festett eredmény más tárolását nem találtunk; a tartós adat maga a vonáslista.
- A korpusz 23 `Boost=1,<érték>` sora mind vonás nélküli — ez egybevág azzal, hogy a `Boost` nem festhető. `ReanimatedEyeColor` a korpuszban nincs, ezért **valódi, befestett ini-sor nincs**.

**Válasz #3541-re:**
- **`Boost`, `Pixelate`, `Soften`, `PicnikTint`:** festett állapot **nincs** — az eredetiben ezek nem festhetők; a szerkesztőben, a bélyegképen és az exportban egyformán az **egész képen** látszik az effekt.
- **`ReanimatedEyeColor`:** a bélyegkép és az export a `filters=` sorból, a vonásokból építi újra a maszkot ⇒ **a szerkesztővel azonosan, csak a festett területen** látszik az effekt (mentés nem kell hozzá).

**Nálunk (mérve, olvasással — `origin/main`):**
- `PAINTABLE_MASK_OPS` ötelemű (`render/chain_glimmer_handlers.py:351`: `boost`, `pixelate`, `soften`, `picniktint`, `reanimatedeyecolor`), a `paintMaskSupported` (`app/paint_mask_controller.py`) bármelyiknél igaz ⇒ a négy effektnél is megjelenik a „Brush Size" csúszka (`EditorParamPanel.qml:308`–`340`) és a festés; a festett maszk csak a szerkesztő munkamenetében él (a mentés beégeti, #3462), a bélyegkép és az export maszk nélkül fut;
- a `paintable_mask_warning` a négy effektre „a Picasa ecsettel kijelölt területre hatna" szöveget ad — **téves**, az eredeti az egész képre hat;
- `EMPTY_MASK_DEFAULT_OPS = {reanimatedeyecolor}` (üres maszkkal indul) **helyes**.

**Amit NEM tudunk (megnevezett úttal):**
1. **A vonás-rekord mezői:** a mezőleképezés a #4046-ban részben feloldódott (lent). Nyitva maradt az ecsetméret képhez viszonyított alapja, több mező tényleges minimuma/maximuma, és a valódi, befestett ini-minta.
2. **Az Apply / Cancel / Back to Library kezelője** (ki hívja a `CGenericFilter` 11. és 12. rését) — nincs azonosítva; a vonások tartóssága az ini-sorra épül, ez nem kell hozzá.
3. **Az export renderútja** a `0x006952e0` vtábla-hívásain át nincs utasításig követve; a `0x008f7140` az egyetlen render-környezet-gyár, ezért a következtetés **erős**, nem megerősített.
4. **Élő minta** a befestett állapotról: a Colab-végrehajtó húzás-lépése kell (picasapy-agent #161).

*Bizonyítottsági fok: **megerősített** — a mód-tábla és a kezelő dispatchje (a mód-táblát és a kezelő elágazását a kör szerzője a fájlból közvetlenül is kiolvasta), hogy a négy effekt nem festhető, és a `0x00bb3ff0` egyetlen hívója; az üres maszk = nincs effekt (keverő); a vonás-sorosítás/elemzés/klón megléte (két olvasat). **Erős:** hogy a bélyegkép és az export a vonásokat visszaépíti (a betöltő- és renderfeladat-lánc megvan, az export vtábla-útja nem). **A mezők:** a #4046 mezőleképezését és korlátait lásd lent; **NINCS MEG** a valódi, befestett ini-sor és az ecsetméret képhez viszonyított mértéke.*

#### #4046 — a vonás-rekord mezői (2026-10-03)

*Forrás: eredeti `Picasa3.exe`, ImageBase `0x00400000`; `0x008fac40` író, `0x008fb120` olvasó, `0x008e3dd0` új vonás, `0x008e4130` folytatás, `0x008fbf10` egérkezelő, `0x008ec290` vonáskonstruktor, `0x008e4270` ecsetstílus-gyár, `0x008ec3a0` befoglaló téglalap, `0x008ec790`/`0x008eca20` maszkréteg-rajzoló; QEMU-i386 futtatás a lenti kontrollált bemenettel.*

Az objektumbeli vonás `0x28` bájtos (a `0x008e3b60` `0x28` bájtot foglal): az író `0x008fafb8`–`0x008fb002` a három első `float32` mezőt és a `+0x24` bájtot írja ki; az ecsetstílus mutatója a vonás `+0x18` mezőjében van. A pontpár-tömb mutatója `+0x1c`, a számláló `+0x20` — de a nyers érték `(n<<1) | jelzőbit`, nem `n` (nyers 5 = 2 pont; a vonáslista számlálója `F+0xc0` ugyanígy: nyers 3 = 1 vonás; egyezik a `0x008ec2e0` és `0x008e4015` hozzáadó kódjával; független ellenőrzés, 2026-10-03). Az olvasó `0x008fb978`–`0x008fb9d7` az első négy tokent visszaolvassa; az `_atof` eredményét `float32`-re szűkíti, a negyediket `_atol`-lal olvassa és bájtba teszi. A hét részes alak két további stílus-`float32`-et tartalmaz; a pontok szintén `float32` párok.

| Rekordrész | Jelentés és objektummező | Típus, alapérték, tartomány és normalizálás | Bináris bizonyíték |
|---|---|---|---|
| első `:%f` | `brushAlpha`, vonás-átlátszóság, vonás `+0x00` | `float32`; a létrehozó alapja `1.0`. A szerializáló és az olvasó nem korlátozza; megengedett tartomány: **NINCS MEG**. | `0x008e3e78` (`fld1`), név/kiolvasás `0x00cd02e0` / `0x008e3e83`–`0x008e3eb3`, első argumentum `0x008e3fdf`–`0x008e3feb`; író `0x008fafb8`, formátum `0x00cd0970`; olvasó `0x008fb978` |
| második `:%g` | `_nSpacing`, vonás `+0x04` | A spacing a képpontban mért stílusméret szorzója; bélyegköz = trunc(size-px) × spacing. A régi „NINCS MEG” tartomány-megjegyzés marad, a mért képletet lásd a #4096 táblában. | `0x008eca20`, `0x008ed1b0` → `0x00c29990`; QEMU bélyeghely-mérés; #4096 alább |
| harmadik `:%g` | `brushRotation`, vonás `+0x08` | A szög egysége **NINCS MEG**, mert a megnevezett raszterút nem olvassa a mezőt; lásd a #4096 célzott vizsgálatát. | `0x008eca20`, `0x008ec790`; #4096 alább |
| `:%d` | ecsetmód-bit, vonás `+0x24` | A raszterben 0 = festés, 1 = radírozás; a creator tartalékláncának pontos forrása továbbra is az utasításszintű kiolvasás szerinti. Lásd a #4096 kétutas ellenőrzését. | `0x008e3b60`, `0x008ec290`, `0x008ed280`; QEMU pixelmérés; #4096 alább |
| opcionális első `:%g` | ecsetméret, stílus `+0x0c` | A raszter bemenetén képpont-átmérő; sugár = size × 0.5. A `0.03`/`0.2` UI-faktorok nevezője **NINCS MEG**. Részletek és kontroll a #4096 alatt. | `0x008ed730`, `0xc72150`; QEMU-mérés; #4096 alább |
| opcionális második `:%g` | `_sldrHardness.value`, ecsetkeménység, stílus `+0x10` | Alapérték 0.15 a descriptorból; a creator dereferálja. A `h=1` natív alfa-profil 20/40 px-en QEMU-val mérve; a további profilok mintái a #4096 alatt. A megengedett min/max **NINCS MEG**. | `filterdesc.xml:1273`, `0x008e3e32`–`0x008e3e38`, `0x008ed730`; QEMU #4096 |
| pontlista | egymást követő `(x,y)` pontpárok, vonás `+0x1c` / `+0x20` | `float32` párok. Az egérkezelő `x/képszélesség` és `y/képmagasság` alakban normalizál, tehát a tengelyek külön nevezőt kapnak, nem a rövidebb oldalt. A beolvasó nem vizsgál külön koordinátatartományt; a megengedett határok: **NINCS MEG**. | osztás `0x008fbf85`–`0x008fbf9d`; ponttömb-bővítés `0x008ec2e0`; író `0x008fb064`–`0x008fb0f3`; olvasó `0x008fbbb1`–`0x008fbc14` |

**Az 5 és 7 részes alak nem verziójelölés.** Az író (`0x008fb01c`) az aktuális vonás `+0x18` ecsetstílus-mutatóját az előző vonás stílusmutatójával hasonlítja össze. Ha azonos: a méret/keménység mezőket kihagyja, ezért a rekord `alpha:spacing:rotation:flag:points` = **5 rész**. Ha eltérő — az első vonásnál az előző mutató null — kiírja a `size:hardness` párt, ezért **7 rész**. A `0x008e4270` azonos stílusértékeknél visszaadhatja a már meglévő stílusobjektumot; a szerializálási feltétel maga a mutatóazonosság, nem a felhasználói ecsetváltás vagy egy régi/új formátum. **Pontosítások (futtatva, 2026-10-03):** (a) az előző mutató kezdőértéke 0 (`0x008faf91`/`0x008faf9d`), minden vonás után frissül (`0x008fb05a`) — ha az ELSŐ vonás stílusmutatója is null, a két mutató azonos, és az első rekord 5 részes (az olvasó ezt elutasítja, ld. lent); (b) a feltétel a MUTATÓ azonossága, nem az érték: két külön, azonos értékű stílusobjektum 7 részes rekordokat ad; (c) pont nélküli vonásnál a rekord 4 vagy 6 részes (a pontlista üres), az olvasó ezt elutasítja.

**Írás PicasaPy-ban (levezethető szerializálási lépések):**

1. A szűrő meglévő `filters=` csúszkamezői után, a vonások listájának sorrendjében kezdd a rekordot vesszővel.
2. Írd ki `brushAlpha` értékét `%f`-nek megfelelően, majd `:` + `_nSpacing` `%g`, `:` + `brushRotation` `%g`, `:` + ecsetmód `0`/`1` alakban.
3. Ha az aktuális ecsetstílus eltér az előző rekord stílusától (az első rekordnál nincs előző), írd hozzá `:` + méret `%g` + `:` + keménység `%g`; egyező stílusnál ezt a két mezőt hagyd el.
4. Írd hozzá `:` + az első pont `x`; utána `|`-lel az első `y`, majd minden további pont `x` és `y` értékét. Az író `%g`-t használ a pontokra.

**Visszaolvasás (az eredeti parser sorrendje):** a vesszőnél választja szét a vonásokat (`0x008fb1a3`), kettőspontnál 5 vagy 7 részre (`0x008fb947`–`0x008fb961`), az első három értéket `_atof`-fal, a bitet `_atol`-lal olvassa; 7 résznél a méretet és keménységet is beolvassa; **5 résznél is meghívja a stílusgyárat** (`0x008e4270`): az előző stílus méretét és keménységét örökli, a módbitet a rekordból veszi, és eltérő módbitnél új stílust hoz létre. Az utolsó részt `|` mentén bontja (`0x008fbbb1`), és páronként építi vissza a pontokat (`0x008fbbd0`–`0x008fbc14`). **Az olvasó futtatásos oda-vissza próbája (független ellenőrzés, 2026-10-03):** a natív CString-et az eredeti `0x00985af0` építi, az olvasót (`0x008fb120`) az eredeti kód futtatja; 5 új mintázaton (AABBA, ABABA, AAAAA, ABCCA, CCCBB, konzisztens stílus+mód bemenettel) rc = 0, és a visszaolvasott vonásokból újraszerializált sor bájtra azonos a bemenettel; a stílusmutató-azonosság is helyreáll. Az olvasó csak az 5 és a 7 részes alakot fogadja (`0x008fb959`, `0x008fb95e`), minden mást elutasít (rc = −1, ld. az aszimmetriát lent); az `_atol` miatt a mód tokenjére `2`→1, `−1`→1, `1.9`→1, `0.9`→0; tartományt nem ellenőriz (`7.5:-3:1000:1:0.1:0.2:5|-6` változatlanul beolvasva). A stílusgyár a stílust újrahasznosítja, ha a mód egyezik és a méret és keménység `float32` bitmintája legfeljebb 7 ULP-nyire tér el.

**Futtatott cáfoló kontroll:** a QEMU-i386 harness az eredeti `0x008fac40` írót hívta meg három, kézzel felépített vonással. Az első és második rekord ecsetstílus-mutatója azonos, a harmadiké eltérő; a kimenet rendre 7, 5, 7 kettőspontmezőt adott, és a két pontpárt `|`-ekkel írta. Ez cáfolja, hogy az 5/7 alak verziót vagy pusztán a „legelső ecsetet” jelölné. A kutatói runner a sztringformázó/hozzáfűző segédeket (`0x0040ea90`, `0x0040eab0`) saját formázóval helyettesítette; az eredeti írót nem. A formázó ott nem a Windows-CRT volt, ezért az a futtatás a `%f`/`%g` tényleges kimenetéről nem tud állítani — ezt a független ellenőrzés pótolta (lent).

Kontrollált kimenet (a pontkoordináták a harness pontos, szintetikus bemenetei; nem Picasa-export):

```text
1,1.000000:0.25:0:0:0.03:0.15:0.125|0.25|0.5|0.75,1.000000:0.25:0:0:0.25|0.5,1.000000:0.25:0:1:0.2:0.15:0.125|0.875|0.75|0.25
```

**Cáfoló eredmény és fok:** a QEMU-futtatás a writer szerkezeti állításait (5/7 feltétel, mezősorrend, ponttagolás, `0`/`1` kiírás) a statikus út mellett megerősíti. A kontrollált rekordok értékeit kézzel adtuk meg, ezért nem független igazolása annak, hogy a UI-mapping minden mezőnél a várt jelentésű; a mezőnevek és a brush/eraser kapcsolat egyutas, utasításszintű levezetés marad. **Összesített fok: feltételes** (a kutatói kör szerint); a független ellenőrzés után lásd a következő blokkot.

**Átnézési korrekció és független ellenőrzés (2026-10-03, a hívó Sonnet-ellenőre):** saját harness, az eredeti `Picasa3.exe` kódja `qemu-i386` alatt; a sztring-hozzáfűzókat (`0x0040ea90`/`0x0040eab0`) lapos pufferbe író shim helyettesíti, a formázást az eredeti MSVC CRT `_vsnprintf` (`0x00c08769`) végzi (hamis `_tiddata`/TLS, az eredeti float-tábla-inicializáló `0x00c0d9bc` meghívva; minden más import csapda); az olvasóhoz bump-allokátor a `malloc`/`realloc`/`free` helyén; a `this`, a leíró (nulla, két csúszkával), a stílus és a vonás kézzel épült a kód olvasása alapján — **nem a valódi `filterdesc` leíró és nem a valódi szerkesztő-állapot fut**. Kódátírásos kontroll: a `0x008fb01c` `je` → `nop nop` után minden rekord 7 részes, `je` → `jmp` után minden 5 részes; a `0x008faffe` `setne` helyére `mov al,[esi+0x24]` → a nyers bájt (0,1,2,255,128,16) jelenik meg; az olvasó `0x008fb95b` átírása (`cmp esi,7` → `cmp esi,9`) rc = −1-et és 0 vonást ad. Eredmények (új, megkülönböztethető értékekkel):

- Stílusmutató-minta `A,A,B,B,A` → **7,5,7,5,7** részes rekordok; kontroll `A,B,A,B,A` → 7,7,7,7,7; `A,A,A,A,A` → 7,5,5,5,5; 1 vonás → 7; 0 vonás → csak `1`. Teljes sor (AABBA): `1,0.370000:0.11:17:1:0.07:0.31:0.1|0.2|0.3|0.4,0.610000:0.22:91:1:0.5|0.6,0.830000:0.33:45:0:0.13:0.77:0.7|0.8|0.9|0.95|0.15|0.25,0.500000:0.44:0:0:0.35|0.45|0.55|0.65,0.250000:0.55:180:1:0.07:0.31:0.05|0.06`.
- Formátum az eredeti CRT-vel: alpha `%f` 6 tizedessel (`0.370000`), a többi `%g` 6 értékes jeggyel és **3 jegyű kitevővel** (`1e-005`, `1.23457e+006`, `-0`). A szöveges alak **veszteséges**: 1e-7 alpha → `0.000000`; 1234567 forgatás → `1.23457e+006`; a 0.3333333 pont → `0.333333`. Ezért a „`float32` pontossággal veszteségmentes” csak a MODELL szintjén teljesíthető; bájt-egyezés célja: sor → modell → sor.
- **Aszimmetria:** az író kiadhat olyan rekordot is, amit az olvasó elutasít (0 pontú vonás: 4/6 részes; null stílusú első vonás: 5 részes első rekord) → rc = −1; az addig sikeresen beolvasott vonások megmaradnak, a hibás rekordtól kezdve minden elvész (7+4+5 részes sorozat: 1 vonás marad; az első 5 részes rekord: 0 vonás).
- A keménység alapértéke a létrehozóban NEM konstans: `0x008e3e32`–`0x008e3e38` a `**(float**)this`-ből veszi (`mov edx,[esp+0x54]`, `mov eax,[edx]`, `fld dword [eax]`); a fenti 0.15 a `filterdesc.xml`-ből való, **ezt a független ellenőrzés nem ellenőrizte**.
- Az `x/szélesség`, `y/magasság` osztás (`0x008fbf85`–`0x008fbf9d`, `fidiv`) mindkét nevezőt az `[ebx]` téglalapból veszi (`[ebx+8]−[ebx]`, `[ebx+0xc]−[ebx+4]`); hogy ez a téglalap a kép téglalapja, **nem igazolt** — a „nem a rövidebb oldal” állítás a kód alapján tartható, a nevező azonosítása nyitott.

**Fok a korrekció után:** a rekord SZERKEZETE (mezősorrend, formátum-sztringek és a CRT-kimenet, az 5/7 szabály a mutatóazonosságra, a `%d` normalizálása 0/1-re, az olvasó viselkedése és a sor → vonás → sor round-trip) **megerősített** — két független út: A) utasításszintű olvasás, B) az eredeti író és olvasó futtatása az eredeti CRT-vel, kódátírásos kontrollal. A mezők UI-jelentése (ecsetmód-bit szemantikája, ecsetméret képhez viszonyított alapja, a forgatás egysége, tartományok) **feltételes/nyitott**: élő minta kell (#161).

**Amihez élő minta kell:** a picasapy-agent #161 húzás-lépésből mentsünk ki egy eredeti `ReanimatedEyeColor` sort, ismert képpontmérettel, látható/ecsetelt beállítással, és külön rögzítsük az ecsetméretet, keménységet, módot, valamint a húzás kezdetét/végét. A faktor nevezőjének eldöntéséhez a maszk/kurzor pixelméretét is ugyanahhoz a képmérethez kell kötni. A helyi 859 `.picasa.ini`-s korpuszban nincs `ReanimatedEyeColor` sor; a mérőadat-tárban talált vonás nélküli fixture nem helyettesíti ezt a mintát.

#### #4096 — a mezők hatása a rajzolóban (2026-10-03)

Az alábbi megállapítások felülírják a fenti #4046 táblázat mód-, méret-, vonásköz- és keménység-megjegyzéseit.

| Mező | Megállapítás | Bizonyíték |
|---|---|---|
| Módbit (`stroke+0x24`, `style+8`) | `0` festés, `1` radírozás. A 0 ág uniót képez, az 1 ág a fedést megfordítja, majd a maszkot megszorozza. A creator ugyanazt a módértéket adja a style factorynek és a stroke konstruktorának. | `0x008e3b60`, `0x008ec290`/`0x008ec2d7`, `0x008e4270`, `0x008ed280`, `0x008edb7b`–`0x008edba8`, `0x008f4540`, `0x008f4400`; QEMU: 128 célfedés és 64 fedés → paint 159, erase 95. |
| Ecsetméret (`style+0x0c`) | A rasterizer ezt képpontban értelmezett átmérőként adja a `CircularBrush`-generátornak: sugár = méret × 0.5 (`0xc72150 = 0.5`). Nem szorozza kép szélességével, magasságával, rövidebb oldalával vagy vonás-befoglaló téglalappal. A `0.03`/`0.2` UI-faktorok saját nevezője továbbra is nyitott. | `0x008ed730`, `0x008ed765`–`0x008ed780`; `0x008ec3a0`; QEMU 120×80 és 240×160 bemeneteken azonos 12 px mérettel 12, illetve 24 bélyeghívás. |
| Vonásköz (`stroke+4`) | Bélyegköz = trunc(stílusméret képpontban) × `_nSpacing`; kisebb arány sűrűbb lerakást ad. Megengedett tartomány: **NINCS MEG**. | `0x008eca20`, `0x008ed1b0` → `0x00c29990`; QEMU: size 12, spacing .5 → 12 hely; spacing .25 → 24 hely; size 24, spacing .5 → 6 hely. |
| Forgatás (`stroke+8`) | Fok/radián nem dönthető el, mert a megnevezett `0x008eca20` elhelyező és `0x008ec790` rajzoló nem olvassa ezt a mezőt és nem továbbítja a style/brush hívásoknak. QEMU 0/90 futás: az elhelyezési hívások száma egyforma; végső pixelkép nem volt mérve. | `0x008eca20`, `0x008ec790`; QEMU bélyeghely-naplózó. Következő út: az eredeti `0x008ed730` ecsetfelület futtatása és az esetleges másik stroke-renderhívó célzott követése. |
| Keménység (`style+0x10`) | Az alap `0.15`: a `filterdesc.xml:1273` deklarálja, a creator `0x008e3e32`–`0x008e3e38` pedig az effect-példány első float mezőjét dereferálja alapértékként. A `h=1` alfa-profil 20/40 px-en QEMU-val mérve; más méreteken és keménységeken az általános görbe, valamint a min/max **NINCS MEG**. | `filterdesc.xml:1273`, `0x008e3e32`–`0x008e3e38`, `0x008e4270`, `0x008ed730`, `0x008f3290`, `0x008f3840`; QEMU #4096. |

**A út — utasításszintű olvasás.** A creator `setne`-vel képezi a módot a `_brshbtn.selected` → `_btnEraser.selected` → 0 láncból, majd átadja `0x008e3b60`-nak. A mode a style `+8` és stroke `+0x24` mezőbe is bekerül. A `0x008ed280` style mód alapján választja a festő uniót vagy a radír inverz-szorzást. A `0x008eca20` a pontokat külön kép-szélesség/kép-magasság skálával alakítja képpontra; a bélyegzők lépésközét a képpont-egészre csonkolt size és spacing adja. A `0x008ed730` a style méret feléből képez sugarat. A forgatást a felsorolt hívási út nem használja.

**B út — az eredeti x86 futtatása.** A már meglévő qemu_harness ELF-építő és az eredeti `Picasa3.exe` kód futott közvetlenül `qemu-i386` alatt; `systemd-run --user --scope` a user bus sandbox-tiltása miatt nem indítható, ezért a kézi ELF futtatás kapott 12 GiB címterület- és 30 s időkorlátot. A `0x008eca20` eredeti kódját kétpontos, kézzel épített stroke/style/vtable és 120×80, illetve 240×160 képméret kapta. A `0x008ec790` helyén bélyeghely-naplózó volt, így ez csak elhelyezésszám, nem végső maszk. QEMU eredmények: (120×80, size 12, spacing .5) 12 hívás; (240×160, azonos size/spacing) 24; (120×80, size 24) 6; (120×80, spacing .25) 24; rotation 0 és 90 mellett egyaránt 12. Kódátírásos kontrollban a natív `0x008ed1b0` size getter kétszerezése 12-ről 6-ra felezte a hívást. A natív `0x008f4540` és `0x008f4400` pixelmagok külön szintetikus négy-byte pufferrel: 128 célfedés + 64 bélyegfedés → unió 159; inverz-fedés 191 → szorzóág 95.

A `this`, a képtartó, a vonás, a style/vtable és a mérőpontok kézzel épültek; a size/spacing próbában a `0x008ec790` végpontot csak naplózó helyettesítette, a pixelpróbában pedig a bemeneti maszk lane-jei voltak szintetikusak. Nem futott valódi effect-példány, editor UI vagy teljes Picasa maszkfelület.

**Cáfoló kísérlet.** A méret-szorzó ellenhipotézist a képméret kétszerezésével próbáltuk cáfolni: ha a 12 px style méretet W/H/min(W,H) aránnyal szorozná, a bélyegköz is kétszereződne és a hívásszám nem nőne; az eredeti kód ehelyett 12-ről 24 bélyegre váltott. A módpolaritás ellenpróbájában az 1-es ág 128-ról 95-re vitte le a célfedést, tehát radírozott; a 0-s ág 159-re növelte. Ugyanazzal a mércével ellenőrizve: az első csak elhelyezésszámot mér, a második az eredeti pixelmagokat futtatja, nem a teljes canvasútvonalat.

**Bizonyítottsági fok:** mód, pixel-átmérő és bélyegköz **megerősített** (utasításszintű olvasás + eredeti gépi kód futtatása). A keménység 0.15-ös forrása **megerősített** (descriptor + creator dereferálás); a profil pontos pixelenkénti élessége **nyitott**. A forgatás egysége/hatása **nyitott**, mert a megnevezett raszterút nem fogyasztja a mezőt; folytatásként az eredeti brush-surface generátor QEMU-mérése és az alternatív stroke-hívó célzott ellenőrzése szükséges. A helyi ini-korpuszban nincs befestett `ReanimatedEyeColor` példa.

**Átnézési kiegészítés (2026-10-03, a hívó önálló utasításszintű olvasata):** a módbit útvonala a `0x008ed280` rajzoló függvényen belül: a `0x008ed4df` `cmp byte [eax+8], bl` után `je 0x008ed5ad` (mód 0) ágon a `0x008f5d20` → `0x008f4510` hívás indul (a `0x008f4540` „festő unió” kernel családja), a mód ≠ 0 ágon a `0x008f57a0` → `0x008f43d0` (a `0x008f4400` szorzó-kernel családja: `pmullw`, `psrlw 8`) — tehát az 1-es mód valóban a szorzós (radír) úton fut. Ráadásul a bélyeg alfa-polaritása is a módtól függ: a `0x008edb8c`–`0x008edba8` szakaszon `mód == 0` → `v = 255 − v` (invertált alfa az unióhoz), `mód ≠ 0` → `v` változatlanul a szorzáshoz (megfordított fedés). A kutatói QEMU-mérés a kerneleket szintetikus fedéssel futtatta, a bélyeggenerátor polaritását nem — ezt a fenti olvasat pótolja; a két út együtt a „0 = festés, 1 = radírozás” állítást **megerősítettnek** tartja. **Nyitva marad:** a forgatás egysége/fogyasztója és a keménység pontos alfa-profilja; ezekhez a `CircularBrush`-generátor (`0x008ed730`, `0x008f3290`, `0x008f3840`) célzott QEMU-futtatása és az alternatív stroke-hívó felkutatása a következő bináris irány (#4096 törzse).

#### #4096 — második bináris kör (2026-10-03)

**Keménységi profil — részleges, mért eredmény.** Az eredeti `0x008ed730` futása a `0x008edb30` hívásnál a `0x8f3290` eredeti interpolátort hívta; a mérő-wrapper az argumentumot és az `ST(0)` eredményt naplózta, majd az eredeti kód folytatódott. A mintaciklus a 15. elem után, a `0x008edc08` ponton állt meg: ekkor a `0x008edbee` által írt 15 darab `uint32` már a lokális pufferben volt (`[esp+0xa8]`). A táblák az interpolátor bemeneti `u` értékét és a puffer alsó bájtját adják; `u` a sugárparaméter, a méretből képzett sugár `size × 0.5` (`0x008ed765`–`0x008ed780`, konstans `0xc72150`).

| keménység | mért `u` bemenetek a `0x8f3290`-nek, méret 20 px |
|---:|---|
| 0 | `0`, `0.029239766`, `0.048274282`, `0.067308798`, `0.124412335`, `0.181515887`, `0.219584912`, `0.257653952`, `0.40993005`, `0.4860681`, `0.543171644`, `0.600275218`, `0.695447743`, `0.866758406`, `1` |
| 0.15 | `0`, `0.171069175`, `0.187322721`, `0.203576267`, `0.25233689`, `0.301097542`, `0.333604634`, `0.366111726`, `0.496140063`, `0.561154246`, `0.609914899`, `0.658675551`, `0.739943266`, `0.886225164`, `1` |
| 0.5 | `0`, `0.48120302`, `0.491375506`, `0.501547992`, `0.532065451`, `0.56258291`, `0.582927942`, `0.603272915`, `0.684652805`, `0.725342751`, `0.755860269`, `0.786377728`, `0.83724016`, `0.928792596`, `1` |

A puffer alsó bájtjai a fenti mintapontok sorrendjében:

| mód | mért 8 bites profilbájtok |
|---:|---|
| 1 | `0, 0, 0, 2, 12, 32, 50, 69, 155, 189, 208, 223, 240, 252, 255` |
| 0 | `255, 255, 255, 253, 243, 223, 205, 186, 100, 66, 47, 32, 15, 3, 0` |

Az A út utasításszintű: `0x008edb30` hívja a `0x008f3290`-t; a visszatérő értéket a `0x008edb35`–`0x008edb77` tartomány korlátozza, majd a `0x008edb96`–`0x008edba8` mód szerint változtatja (`0` esetén `255−v`, `1` esetén `v`), és a `0x008edbee` csomagolja a pufferbe. A B út az eredeti x86 futtatása és a `0x008edc08`-nál kiolvasott kész puffer. A módonkénti bájtpárok összege minden mintán 255; az utasításolvasat és a futási eredmény egyezik.

Keménység `0.15` esetén 20 és 40 px-es méreten, mindkét módban ugyanaz a 15 `u` és ugyanaz a 15 profilbájt jött ki. **Cáfoló kísérlet:** azt az ellenhipotézist vizsgáltuk, hogy a `CircularBrush` normalizált profilja a mérettel változik; a 20→40 px kétszerezés ezt a mintapuffernél cáfolta. Ez a próba a normalizált profilra vonatkozik, nem a képpontokban mért sugárra.

**A mérés határa és a helyettesítések.** A QEMU-harness a `0x00c0769f` heapkérést a `.bt`-beli bump arénába irányította, a felszabadítási hívásokhoz no-op stubokat adott, a `0x008edb30` hívást pedig olyan loggerre irányította, amely az eredeti `0x008f3290`-t hívta meg. A `0x008edc08` tap után a folyamat kilépett; nem állít elő teljes képméretű ecsetmaszkot. Az eredeti `_vsnprintf` nem volt a mért profil számítási útjában. Az ELF `qemu-i386` alatt, közvetlenül futott, `ulimit -v 12582912` és `timeout 30` korláttal; a Picasa3 bináris nem került a repóba.

A keménység `1.0` esetén a végrehajtás másik ágra lép, a `0x008edc08`-nál mért 15 pontos interpolációs puffert nem éri el; a próbafutás a harness nem kezelt `GetModuleFileNameA` importcsapdájánál (`0x00c40248`, import-index 28) állt meg. **NINCS MEG** a kemény kör pufferének mért profilja. Következő út: a `0x008ed730` keménykör ágának külön kimeneti pufferét azonosítani és a kész, raszterezett ecsetpuffert közvetlenül az ág visszatérése előtt kiolvasni; az interpolációs tap nem alkalmas erre az ágra.

**Forgatás (`stroke+8`) — a nevezett raszterútban nincs fogyasztó, általános negatív bizonyítás még nincs.** A `0x008ec290` konstruktor floatként eltárolja a mezőt. A `0x008eca20` vonásbejáró, a `0x008ec790` rajzoló és a `0x008ec3a0` befoglaló téglalap útvonala nem olvassa ezt a stroke-mezőt; az `0x008e4130` másik azonosított vonásbejáró a `0x008eca20` felé megy. A teljes szövegszakasz `paszta.py`-s pásztázásában sok általános `+8` tagjelölt volt, de önmagában ezek nem köthetők a stroke mutatójához. Az eredeti QEMU-hívásnaplóban forgatás 0 és 90 esetén egyaránt 12 bélyeghívás történt; ez a darabszám-egyezés nem koordináta- vagy képminta-egyezés. **Cáfoló kísérlet:** 0/90 fokkal próbáltuk cáfolni a „forgatás nincs hatással” hipotézist; hívásszám nem változott, de a használt mérő a bélyeghelyeket nem rögzítette, így koordináta-változást nem zár ki. Az egység ezért **NINCS MEG**, és a mező teljes raszterbeli fel nem használtsága sem bizonyított. Következő út: a `0x008ec290`-től a stroke-mutatót követve minden rajzoló hívót ellenőrizni, majd `0x008ec790` belépésénél a bélyegkoordinátákat 0 és 90 fokon naplózni.

**A `0.03`/`0.2` UI-faktorok nevezője — NINCS MEG.** A `0x00bb25f0` descriptor-olvasó a `startValueFactor` és `maximumFactor` mezőket külön kezeli. A `0x008e3bd0` `_brshbtn.value`-t olvas, hiányában `_sldrBrushSize.value`-t; az értéket egészre kerekíti. A `0x008e3dd0` ezt a méretet a `0x008e3b60`-on át a stílusgyárhoz adja. Ezen az utasítási útvonalon nincs képszélesség-, képmagasság- vagy nézetméret-szorzás: a szorzás, ha van, a vezérlő értékének előállításakor történik. A nevező nem olvasható ki sem a getterből, sem a descriptor-olvasóból. Következő út: az eredeti `BrushSizeAndEraserButton` QML/kontroll bindingjében megkeresni, mi állítja elő a két `value` property-t, majd ismert képméret és nézetméret mellett mindkét property-t és a `style+0x0c` értékét rögzíteni. A PicasaPy helyi `paint_mask` rövidebboldal-skálázása nem bizonyíték az eredeti nevezőjére.

**Bizonyítottsági fok ebben a körben:** a keménység 0/0.15/0.5 profilmintái és a módonkénti bájtpolaritás a megadott mintapontokra **megerősített** (utasításszint + eredeti kód futtatása). A 1.0-s keménykör-profil **nyitott**; a forgatás **nyitott** (a feltárt raszterút nem fogyasztja a mezőt, de a koordinátás ellenőrzés és a teljes fogyasztói lánc hiányzik); az UI-faktor nevezője **nyitott**.

**Fejlesztési következmény:** a mentett rekord stílusmérete képpont-átmérő, a spacing arány, a 1-es mód radír. A persistent rekordokból újraépített preview/export maszk fejlesztői jegye csak a forgatás fogyasztójának, a teljes keménységi profilnak és az UI-faktor nevezőjének lezárása után készíthető elő; ebben a körben még korai. Termékkódot ez a kutatási kör nem módosít.

⛔ **Önhelyesbítés:** az 5. szakasz „mechanizmus"-olvasatát (a `PaintEffectCanvas` kezelője építi a maszkot; `+0x9c` változat-mező; teljes fedésű alapmaszk) ez a kutatói szál írta egy körrel korábban, a kezelő függvény olvasásából, a hívóját és a mód-táblát nem nézve. A hibát az első olvasat ellentmondása (`maszk = 0` vs. az élő „egész kép") és a független olvasat együtt hozta felszínre.

#### #4096 — harmadik bináris kör (2026-10-03; h=1 kiegészítés: 2026-10-05)

**Keménység `1.0` — a teljes natív alfa-profil mért 20 és 40 px-en.** A `0x008ed74f` `fcomp` után a `0x008ed75c` `test ah, 0x41` és a `0x008ed75f` `jp 0x008ed863` választ ágat: `h=1.0` esetén a `0x008ed765` kemény ecsetág fut; `h=0.15` a `0x008ed863` ágra jut. A hívás előbb `0x00ffffff` színnel tölti a kimeneti felületet, majd a `0x00aa1840`-et hívja `0xff000000` színnel; a helper pixelírása `0x00aa1b1f`-en történik. A stílusméret fele a sugár (`0x00c72150 = 0.5`).

**A út — utasításszintű olvasás.** `0x008ed730` a `style+0x10` keménységet hasonlítja `1.0`-hoz, és a kemény ágon a `style+0x0c` méret felét állítja be. Érvényes célfelületnél, ha a `0x009a91a0` nullával tér vissza, a felület átlátszó fehér alapot kap, majd a `0x00aa1840` fekete kör-ecsetet rajzol; a helper minden kimeneti DWORD-ját a `0x00aa1b1f` írja vissza. Little-endian ARGB-ban a DWORD felső bájtja a fedettség.

**B út — az eredeti gépi kód futtatása.** A `0x008ed730` eredeti kódja `qemu-i386` alatt futott, a korábbi `GetModuleFileNameA` importcsapda helyére üres `xor eax,eax; ret` stub került, a CRT-foglalást pedig a helyi bump-heap shim szolgálta ki. A kimeneti képfelületet a `this+0x10` pointeren, a visszatérés után olvastuk ki. Mind a négy futás `rc=0`, stdout 16708 bájt, stderr 0 bájt; a méret/mód szerinti teljes felület SHA-256-a a két módban azonos.

| méret, mód | felület | középső sor alfa-bájtjai balról jobbra | teljes felület SHA-256 |
|---|---:|---|---|
| 20 px, festés (`mode=0`) | 21×21, stride 21 | `241`, `255` × 18, `225`, `0` | `238e13f70e224c8329b8259117ee152f23fc3190b633ee555398aff9304a7143` |
| 20 px, radírozás (`mode=1`) | 21×21, stride 21 | bájtról bájtra azonos a festéssel | azonos a festéssel |
| 40 px, festés (`mode=0`) | 41×41, stride 41 | `248`, `255` × 38, `232`, `0` | `74087f19c3ef28f4f14626353f1a873c47d4af43e4ca491ac787a20825917f95` |
| 40 px, radírozás (`mode=1`) | 41×41, stride 41 | bájtról bájtra azonos a festéssel | azonos a festéssel |

A 20 px-es felület mérete 1764 bájt, pointere `0x10100010`; a 40 px-esé 6724 bájt, ugyanilyen arénán belüli pointerrel. A középső sorban a fedettség bájtja az egyes 32 bites pixel `+3` bájtja. A hívás után megmaradó régi 15 elemű profilpuffer mind a 15 helyen nulla: `h=1` nem futtatja a 15 pontos LUT/interpolációs ágat. Ezért a jelentett profil az eredeti rasterizáló teljes, natív felbontású középső sora, nem a korábbi 15 LUT-mintapont; nem interpoláltunk vagy becsültünk hozzá értéket. A két módban egyező hash csak a `CircularBrush` generátor ezen kimenetére állítja, hogy a módnak nincs hatása; a későbbi stroke-raster ág módhatását nem zárja ki.

**A `0.03`/`0.2` UI-faktor nevezője — NINCS MEG.** A `0x00bb25f0` descriptor-olvasó a `startValueFactor` és `maximumFactor` attribútumokat külön propertyként parse-olja; a `0x00bbc8b0` konstruktor a három átadott `float`-ot a `+0x10/+0x14/+0x18` mezőkre másolja (`0x00bbc8d1`–`0x00bbc8f9`), osztást nem végez. A `0x008e3bd0` előbb a `_brshbtn.value`, ennek hiányában a `_sldrBrushSize.value` propertyt értékeli ki a `0x008ef520`-szal; a `0x008e3dd0` az így kapott méretet a `0x008e3b60` style-gyárnak adja át. Ezen a bináris útvonalon nincs képméret- vagy nézetméret-osztás. A két megnevezett függvény valós descriptorral/UI-állapottal való futtatása ebben a körben nem történt meg, és a tényleges `BrushSizeAndEraserButton` binding forrása nem volt elérhető; nevezőt nem következtetek ki. A döntéshez az eredeti vezérlő bindingjét kell megszerezni vagy futó vezérlőn, ismert kép- és nézetméretek mellett együtt rögzíteni a két `value` propertyt és a `style+0x0c` méretet.

**Cáfoló kísérlet:** azt próbáltuk cáfolni, hogy `h=1.0` is a 15 pontos interpolációs ágat futtatja. A QEMU-futásban a 15 elemű puffer mind nulla, miközben a `this+0x10` célfelület 21×21 / 41×41 méretű és teljes alfa-sort tartalmaz; ez a LUT-ág hipotézisét cáfolja. Második ellenpróba: festés és radírozás módban azonos méreten a teljes kimeneti felület hash-e és minden pixel egyezik (`20 px`: `238e…7143`; `40 px`: `7408…17f95`). Ez csak a generátor kimeneti felületére érvényes; nem cáfolja a későbbi módonkénti kompozitálást. A korábbi forgatásos próba továbbra is csak azonos bélyegszámot mért, koordinátát/képpuffert nem, ezért a forgatásra nem döntő cáfolat.

**Helyi eltérés.** A PicasaPy `src/picasapy/app/paint_mask.py` maszkja nem kap ecsetkeménységet a `Vonas` mezőiben, és állandó `PEREM_ARANY = 0.15` átmenetet számol. A natív `h=1` felület középső sorában a méret 20 esetén 18, 40 esetén 38 belső bájt teljes fedésű, majd a mért élértékek `225/0` és `232/0`; így a mostani fix lágy perem nem tudja ezt a kemény profilt előállítani. A nyitott UI-faktor és stroke-forgatás miatt ez még nem elég a preview/export maszk teljes fejlesztői jegyének lezárásához.

**Forgatás (`stroke+8`) — a megnevezett raszterút és a konstruktor további hívója.** A korábbi következtetés változatlan: a `0x008ec290` konstruktor vtable nélkül, egyszerű rekordként írja a harmadik float argumentumot `+8`-ra (`0x008ec2ad`–`0x008ec2b1`); a közvetlen hívóindex két hívót ad (`0x008e3b60`, `0x008fb120`). Az utóbbi a rekordot előállítja/tárolja, nem hívja a `0x008ec790` rajzolót; annak közvetlen hívói `0x008ec3a0` és `0x008eca20`. RTTI-osztálytag-térkép ezért a rekordhoz nincs, a korábbi `paszta.py` teljes `.text`-es `disp=8` találatlistája pedig önmagában nem köti a sok találatot ehhez a rekordhoz. A `0x008fb120` által előállított rekord alternatív megjelenítési fogyasztója továbbra sincs azonosítva; a mező teljes fel nem használtsága és a fok/radián egység **NINCS MEG**. Következő út: a tároló/olvasó hívási útján a rekordmutatót követni és minden közvetett rajzoló belépésnél ellenőrizni a `+8` olvasását; a teljes `.text`-pásztázást csak a `paszta.py` `memoria_kapu()` útján szabad újraindítani.

**Bizonyítottsági fok és készültség:** a `h=1.0` hard ág és az eredeti kimeneti felület `20/40 px` középső sorainak fedettségprofilja **megerősített** (utasításszintű kimenetértelmezés + az eredeti kód QEMU-futtatása, méretenként és módonkénti hash-kontrollal). A profil pontos értéke más méreteken, a megengedett keménységi min/max, a forgatás fogyasztója/egysége és az UI-faktorok nevezője **NINCS MEG**. A helyi maszk fix 0.15-ös pereme a natív `h=1` profilhoz eltér; a tárolt vonásokból teljes preview/export maszkot újraépítő egyetlen fejlesztői jegy csak a forgatás és az UI-faktor nevezőjének lezárása után írható ki. Termékkódot ez a kutatási kör nem módosít.

#### #4096 — negyedik helyi Codex-kör (2026-10-05)

**A `BrushSizeSlider` faktorai — a nevező megerősített.** A `filterdesc.xml:1279` a `BrushSizeAndEraserButton`-hoz `startValueFactor="0.03"` és `maximumFactor="0.2"` értéket ad. A `0x00bb25f0` ezeket külön propertyként olvassa, a `0x00bc39c0` pedig a `+0x28` start és a `+0x30` maximum faktort kiolvassa, majd a hányadosukat adja vissza. Az eredeti metódus QEMU-futtatása a két descriptorértéket adó getter-shimmel `0.149999994412` arányt adott (`variant_type=3`), azaz a kezdőérték-arány `0.03/0.2`.

A `0x00bc3a60` metódus az `origImageWidth` és `origImageHeight` propertyt kéri le, összeszorozza, a `0x00c0b310` négyzetgyököt számol belőle, majd a `maximumFactor`-ral szoroz. Az eredményt a `0x00cf3bd8` konstanssal osztja a `0x00529e10` segédfüggvény hívása előtt, utána ugyanazzal a konstanssal visszaszorozza, és a `0x00cf48e0`/`0x00cf48dc` értékekkel 250-re korlátozza. Így a kerekítősegéd előtti maximum-bemenet pontos képlete: `maximumFactor × sqrt(origImageWidth × origImageHeight) / 50`; a vezérlő a segéd kimenetét 50-es egységgel visszaskálázza, legfeljebb 250-ig. Ez a maximumtartomány belső képlete, nem állítás az élő QML-kötés által kiválasztott aktuális ecsetméretről.

| eredeti kép (px) | QEMU-val naplózott bemenet a `0x00529e10`-nek, `maximumFactor=0.2` | képlet szerinti érték |
|---:|---:|---:|
| 120×80 | `0.3919183612` | `0.2 × sqrt(120×80) / 50` |
| 240×160 | `0.7838367224` | `0.2 × sqrt(240×160) / 50` |
| 1000×800 | `3.5777087212` | `0.2 × sqrt(1000×800) / 50` |

**A út — utasításszintű olvasás:** `0x00bb25f0`, `0x00bc39c0`, `0x00bc3a60`, `0x00c0b310`; a nevező `0x00cf3bd8` memóriakonstansából 50, a visszaszorzás és a felső korlát ugyanabban a metódusban látható. **B út — eredeti gépi kód futtatása:** `0x00bc39c0` és `0x00bc3a60` eredeti kódja `qemu-i386` alatt futott; az előbbin a start/max faktorok hányadosát, az utóbbin a `0x00529e10` hívás argumentumát naplóztuk. A három szélesség/magasság-pár azonos képletet adott. A QEMU getterjei és propertytömbjei szintetikusak voltak, ezért ez a bináris metódust igazolja, nem egy élő Qt/QML szerkesztőállapotot.

**Cáfoló kísérlet:** ellenőriztük, hogy a nevező alapja nem a rövidebb képméret. A `min(W,H)` hipotézis ugyanilyen `maximumFactor=0.2` mellett rendre `0.32`, `0.64`, `3.2` bemenetet adna; az eredeti kód QEMU-futásában mért értékek ettől eltértek. A különálló utasításolvasat a `W×H` szorzást, négyzetgyököt és `/50` műveletet közvetlenül mutatja, tehát ugyanazzal a mércével alátámasztja a cáfolatot.

**Keménység — a „néhány méret/keménység-pár” profilja megvan, általános képlet nincs.** A második bináris kör a `h=0`, `0.15`, `0.5` 20 px-es ecsethez mérte ki a 15 interpolációs mintapont alfaértékeit, továbbá a `h=0.15` 40 px-en azonos normalizált mintákat; a harmadik kör `h=1.0` esetén a teljes 20 és 40 px-es natív középső alfa-sort kiolvasta. Ezek az adott párokra utasításszintű útolvasással és az eredeti `CircularBrush`-kód QEMU-futtatásával egyeznek. Ez nem ad minden keménységre/méretre zárt alfa-képletet, de a jegyben kért konkrét mintaprofilokat visszakereshetővé teszi.

**Forgatás (`stroke+8`) — továbbra is nyitott.** A teljes `.text`-pásztázás a kötelező `paszta.py`-n és annak `memoria_kapu()` kapuján keresztül futott: 2 884 879 utasítás; a sok általános `+8` találat között nem lett igazolt stroke-fogyasztó. A `0x008f3970` elsőre lehetséges olvasónak tűnt, de a `0x008edcfc` `lea edx,[esp+0x8c]` és a `0x008edd0a` hívás alapján az `EDX` a `0x008ed730` ecsetgenerátor verem-lokális transzformációjára mutat, nem a tárolt stroke rekordjára; ezt a jelöltet ezért elvetettük. A korábbi `0/90` QEMU-próba csak bélyeghívásokat számolt, nem koordinátát vagy teljes felületet, így sem a mező teljes fel nem használtságát, sem a fok/radián egységet nem bizonyítja. A mező alternatív megjelenítési fogyasztója és egysége **NINCS MEG**.

**Készültség:** a keménységprofil-minták és az UI-faktor maximumtartományának nevezője a fenti mért/bináris tartományban **megerősített**; a forgatási mező nyitottsága miatt a #4096 teljes „Kész, ha” feltétele még nem teljes. A tárolt vonásokból preview/export maszkot újraépítő fejlesztői jegyet ezért még nem javasoljuk.

## ⛳⛳ A `GlowImageOperation` SOSEM fut belső ragyogásként — az `innerglow` attribútum nem létezik a binárisban (2026-09-14, 306. kör, #2982)

*Forrás: `glimmer::GlowImageOperation::vftable` = `0x00cf0174` (RTTI), az
attribútum-olvasó `0x00bb8c40`–`0x00bb8d8f`, a konstruktor `0x00bb8a60`–
`0x00bb8ab0`, a névsztringek `0x00cbda84` · `0x00cf0144` · `0x00cefe84` ·
`0x00cefe8c` · `0x00cf0150` · `0x00cafa3c` · `0x00cf015c` · `0x00cf0164`,
a `filterdesc.xml` hat `GlowImageOperation` sora (`:788`, `:975`, `:1048`,
`:1066`, `:1082`, `:1084`).*

A #2948 kimérte, hogy a `Lomo` maradék **9,0–9,5 ΔE**-je nem a
paraméterekben van. Ez a kör a kernelhez indult — és útközben olyat talált,
ami az egész modellünket érinti.

### 1. A művelet attribútum-térképe, teljesen

Az olvasó (a vtábla **2.** rekesze) nyolc attribútumot ismer, mindegyiket egy
8 bájtos mezőbe téve:

| attribútum | mező | a literál címe |
|---|---|---|
| `color` | `+0x24` | `0x00cbda84` |
| `glowalpha` | `+0x2c` | `0x00cf0144` |
| `xblur` | `+0x34` | `0x00cefe84` |
| `yblur` | `+0x3c` | `0x00cefe8c` |
| `strength` | `+0x44` | `0x00cf0150` |
| `quality` | `+0x4c` | `0x00cafa3c` |
| **`inner`** | `+0x54` | `0x00cf015c` |
| `knockout` | `+0x5c` | `0x00cf0164` |

A vtábla **nyolc** rekeszes: a 9. szótól kezdve már ASCII adat áll
(`MasterCurve`, `Exposure`, `Adjust…`), nem kód.

### 2. ⛔ A `filterdesc.xml` `innerglow`-t ír — a bináris `inner`-t olvas

A leíró mind a hat helyen `innerglow="true"`-t ad meg. A bináris viszont a
**`inner`** literált keresi (`0x00cf015c`).

**A teljes képfájlon, nyers bájtkereséssel** (az indextől függetlenül):

| minta | első előfordulás |
|---|---|
| `innerglow` | **NINCS** |
| `inner\0` | `0x00c8f79f` (kontroll: létezik) |
| `knockout` | `0x00cf0164` (kontroll: a szomszéd attribútum) |

⇒ **Az `innerglow` sztring sehol nem szerepel a `Picasa3.exe`-ben**, tehát a
leíró attribútuma **nem illeszkedik semmire**, és némán elveszik.

### 3. A konstruktor alapértéke: `inner = 0`

A ktor (`0x00bb8a60`) minden mezőt kinulláz a `+0x04`-től a `+0x60`-ig
(`0x00bb8aa4 mov dword [eax+0x54], ecx`, `ecx = 0`). Mivel az attribútum
sosem illeszkedik, a mező **végig 0 marad**.

⇒ **Az eredeti Picasa mind a hat `GlowImageOperation`-t `inner = false`
móddal futtatja** — azaz **KÜLSŐ** ragyogásként, nem belsőként.

### 4. Nálunk MA

A `src/picasapy/render/glimmer_ops.py` `inner_glow()` docstringje szó
szerint így kezdődik: „`GlowImageOperation(innerglow=true)`: a kép
SZÉLÉTŐL befelé ható »izzás«" — vagyis a **belső** változatot valósítja meg,
a `Lomo`, `Holga`, `NightVision`, `Matte`, `Vignette` és `MuseumMatte`
láncában egyaránt. A sugarat a `clamp_glow_radius` 255-re vágja
(`GLOW_RADIUS_MAX`), mert korlát nélkül az eltérés 41,8-ra nő.

Ez megmagyarázza a #2982 táblázatának legfurcsább sorát is: az XML szerinti
**896** képpontos sugár a mi kernelünkkel 8,897 → **23,819** ΔE-re rontott.
Egy külső ragyogásnál a nagy sugár természetes; a belső modellünkben
értelmetlen.

### 5. ⛔ Amit ez NEM mond ki — és miért nem állítom, hogy ez a hiba oka

**A megfejtett mechanizmus nem diagnosztizált ok.** Azt mértem, hogy az
eredeti nem belső ragyogást futtat; azt **nem**, hogy a külső változatra
átállva csökken-e a mért ΔE. Ezt egy fejlesztői kör méri le a
`referencia/lomo/` hármason (ma 9,00 · 9,10 · 9,51), és a `Holga` sem
romolhat (ma 1,55–4,01).

Szintén nem mért:

- **hol fogyasztják** a `+0x54` mezőt: a Glow osztály saját kódsávjában
  (ktor, attribútum-olvasó, destruktor) egyetlen hely sem OLVASSA
  értékként — a fogyasztó egy általános kiértékelő lehet, azt ez a kör nem
  kereste meg;
- **a képpont-menet**: a 8. rekesz (`0x00bc51d0`, 230 b) csak **gyár** — egy
  16 bájtos objektumot foglal `0x00cf0f18` vtáblával és `[+0xc] = a
  művelet`; a tényleges rajzolás annak a vtáblájában van;
- **a `quality="3"` jelentése** ebben a műveletben (a `LocalContrast`-nál a
  #1607 háromszoros dobozelmosást talált — itt nincs igazolva);
- a `clamp_glow_radius` 255-ös korlátjának natív megfelelője.

## ⛳⛳ A Glimmer EGY UTASÍTÁSGÉP — a műveleti osztályokban NINCS pixelmatematika (2026-09-15, #626)

*Forrás: az RTTI-tábla mind a 34 `glimmer::…ImageOperation` vtáblája · a
`.text` teljes pásztázása utasítás-vtábla írására.*

### A lelet

A leltár eddig úgy fogalmazott, hogy „a művelet dekompilálva / nincs
dekompilálva", és 10-et számolt késznek ~30-ból. **Ez a tengely téves.**

A Glimmernek **saját utasításkészlete** van — tizenhárom `Instruction`
osztály, RTTI-vel:

| utasítás | vtábla | mire való (a névből) |
|---|---|---|
| `ApplyInstruction` | `0x00cf0f18` | egy művelet alkalmazása |
| `BlendInstruction` | `0x00cf0f00` | keverés |
| `MaskInstruction` | `0x00cf0f6c`, `0x00cf0f84` | maszkolás |
| `PartialMaskInstruction` | `0x00cf0f30` | részleges maszk |
| `MaskWithSourceAlphaInstruction` | `0x00cf0f48` | maszk a forrás alfájával |
| `DupeInstruction` | `0x00cf0d70` | verem: másolás |
| `PopInstruction` | `0x00cf0f90` | verem: levétel |
| `GetVarInstruction` | `0x00cf0d58` | változó olvasása |
| `SetVarInstruction` | `0x00cf0d88` | változó írása |
| `ClearVarInstruction` | `0x00cd0574` | változó törlése |
| `NamedVarInstruction` | `0x00cd05bc` | névvel hivatkozott változó |
| `OpInstruction` | `0x00cd058c` | művelet-utasítás |
| `ReExecutingInstruction` | `0x00cf0f60` | ismételt végrehajtás |

⇒ Verem (`Dupe`/`Pop`), változók (`Get`/`Set`/`Clear`/`Named`), kompozit
műveletek (`Blend`, három maszk-fajta) és ismétlés. Ez **gépezet**, nem
osztályonkénti képpontciklus.

### A bizonyíték: MIND a 34 vtábla ugyanazt a két függvényt hívja

A teljes `.text` pásztázva arra, hogy ki ír utasítás-vtáblát: **tíz**
függvény. Ezek közül kettő minden műveleti osztály vtáblájában ott van:

| függvény | mit épít | hány `…ImageOperation` vtáblában |
|---|---|---:|
| **`0x00bc4ae0`** | `Blend` · `Mask` · `MaskWithSourceAlpha` · `PartialMask` · `Pop` · `ReExecuting` | **33 / 34** |
| `0x00bc51d0` | `ApplyInstruction` | 28 |

A kivételek is beszédesek: az `ImageOperation` **alaposztály** (7 slot)
egyiket sem tartalmazza; a `GetVarImageOperation` az `Apply` helyett a
`0x00bbf810`-et (`GetVar`), a `Nested` és a `Tint` a `0x00bc12e0`-t
(`Dupe`) viszi; az `EdgeDetectionB`, az `IR` és a `LocalContrast` pedig
csak a `0x00bc4ae0`-t.

⛔ **HELYESBÍTÉS a 2026-09-12-i megállapításhoz.** Az akkori kör a
`0x00bc4ae0`-t (1660 b) „a vezérlőpontok beolvasása/tárolása"-ként írta le,
mert nincs benne lebegőpontos utasítás. A funkció valójában **utasításokat
gyárt** — hatféle `Instruction` vtábláját írja —, tehát **fordító**, nem
adatolvasó. A KÖVETKEZTETÉS viszont állt: a pixelmatematika nem a műveleti
osztályban van.

### Amit ez a #626 leltárán változtat

A kérdés nem az, hogy a ~30 műveletből hány van dekompilálva, hanem hogy a
**tizenhárom utasítás** gépezete megvan-e. A műveleti osztályok csak
**paraméterezik** az utasításokat.

⇒ **A következő gépi lépés:** az `ApplyInstruction` végrehajtója (vtábla
`0x00cf0f18`, öt slot: `0x00bd0ef0` · `0x00bd0ca0` · `0x00bd0cb0` ·
`0x00bd0cc0` · `0x00bd0ee0`), és hogy a `0x00bc4ae0` milyen adatot ad át
neki. Ez **egy** menet, ami után mind a 33 művelet ugyanazon a gépezeten
olvasható.

*Bizonyítottsági fok: **megerősített** — mind a 34 vtábla slotjai és a
teljes `.text`-pásztázás; a kivételek is tételesen.*

## ⛳⛳ Az `ApplyInstruction` végrehajtója — 40 bájtos veremelem, és HOL van a képpontciklus (2026-09-15, #626)

*Forrás: `FUN_00bd0cc0` (538 b, az `ApplyInstruction` vtáblájának negyedik
slotja) diszasszemblálása · mind a 34 `glimmer::…ImageOperation` vtábla
6. és 8. slotjának megoszlása · `FUN_00bb7c80` (435 b) és `FUN_00bb9d20`
(224 b) diszasszemblálása.*

### A végrehajtó

```
0x00bd0cce  test dword ptr [esi + 4], 0xfffffffe   ; üres verem → -1
0x00bd0d25  mov  eax, [esi + 4]
0x00bd0d2a  shr  eax, 1                            ; elemszám
0x00bd0d2c  lea  eax, [eax + eax*4]                ; ×5
0x00bd0d2f  lea  eax, [ecx + eax*8 - 0x28]         ; ×8, −40 ⇒ a legfelső elem
0x00bd0d33  mov  ecx, [edi + 0xc]                  ; a MŰVELET (ApplyInstruction+0x0c)
0x00bd0d36  mov  edx, [ecx]                        ; a művelet vtáblája
0x00bd0d42  mov  eax, [edx + 0x18]
0x00bd0d45  call eax                               ; ← a művelet vtbl+0x18 slotja
```

Két mért tény:

1. **A Glimmer-verem eleme 40 bájt** (`×5` majd `×8`, a legfelső elem
   `−0x28`). A veremmélység a `+0x04` mező felső 31 bitje (`shr eax, 1`).
2. Az `ApplyInstruction` a **`+0x0c`** mezőjében tartja a műveletet, és
   annak **`vtbl + 0x18`** slotját (6. index) hívja.

### A `vtbl+0x18` NEM osztályonkénti — CSALÁDONKÉNTI

A 34 műveleti osztály 6. slotjában **22 különböző** cím áll, tehát a
belépési pont osztálycsoportokra közös:

| `vtbl+0x18` | osztályok |
|---|---|
| **`0x00bb7c80`** | `AdjustCurves` · `AutoFix` · `Exposure` · `GradientMap` · `HSVGradientMap` · `PaletteMap` · `TwoTone` |
| `0x00bc16b0` | `BW` · `ColorMatrix` · `MultiplyColorMatrix` · `SimpleColorMatrix` |
| `0x00bbf920` | `GetVar` · `Nested` · `Tint` |
| `0x00c07709` | `Blend` · `ImageOperation` (alaposztály) |
| 18 további cím | egy-egy osztály (`Blur`, `Border`, `Crop`, `DropShadow`, `EdgeDetectionB`, `EdgeDetectionSobel`, `Glow`, `IR`, `LocalContrast`, `Noise`, `Pixelate`, `QuantizePalette`, `RadialBlur`, `Resize`, `Rotate`, `Shader`, `Sharpen`, `SimpleBorder`) |

⇒ A hét, `0x00bb7c80`-at osztó osztály pontosan a **képpontonként
leképező színműveletek** — ez a készlet „LUT-családja".

### A családi meghajtó és az osztály-specifikus slot

`FUN_00bb7c80` (a hét színművelet közös `vtbl+0x18`-a):

- `mov eax, 0x105c; call __alloca_probe` — **4188 bájt veremterület**;
- `mov eax,[edi]; mov eax,[eax+0x20]; call eax` — visszahív a **saját
  objektum `vtbl+0x20`** slotjára (8. index), ez az osztályonként eltérő
  rész (34 osztályra **10** különböző cím);
- ezután két puffer-leírót állít össze és a `FUN_00bcb2f0`-nak adja át,
  végül `_free`-vel takarít.

`AdjustCurvesImageOperation` `vtbl+0x20` = **`0x00bb9d20`**. Ez
**paraméter-előkészítő**, nem képpontciklus: az objektum **`+0x40`,
`+0x44`, `+0x48`, `+0x4c`** mezőit nézi, és mindegyik nem-nullára meghívja
a `FUN_00bb9e00`-t egy **négyelemű, 24 bájtos lépésközű** helyi tömbbe
(`[esp+0x18]`, `+0x30`, `+0x48`, `+0x60`), majd az egészet a
`FUN_00bcd1e0`-nak adja. ⇒ **négy görbecsatorna** leírója (a
`filterdesc` négy görbeparamétere: összevont + R + G + B), egyenként 24
bájton. A törzsben egyetlen lebegőpontos átalakítás van (egy `double` →
`float`, `0x00bb9d5d`), képpontciklus nincs.

### Mit erősít meg, és mit finomít

A #3206-ban rögzített következtetés — *„a pixelmatematika nem a műveleti
osztályban van"* — **megerősítve**: a művelet osztály-specifikus slotja
(`+0x20`) paramétert épít, a képpontokat a családi meghajtó (`+0x18`) és az
alatta hívott `FUN_00bcb2f0` mozgatja. A **finomítás**: a `vtbl+0x18` nem
egyetlen közös motor, hanem **családonkénti** belépési pont, és a művelet
mégis részt vesz — a saját `+0x20` slotjával, paraméterezőként.

⇒ **A következő gépi lépés (LEZÁRVA, ld. lejjebb):** a `FUN_00bcb2f0` (a két
puffer-leíró fogyasztója) — ez a közös képpont-futószalag; és a `FUN_00bb9e00`
24 bájtos görbeleíró-alakja, amiből a vezérlőpont-interpoláció aritmetikája
kiolvasható.

*Bizonyítottsági fok: **megerősített** — diszasszemblált törzsek és a teljes
vtábla-slot megoszlás; a családok tételesen felsorolva.*

### A közös képpont-futószalag (`FUN_00bcb2f0`, 744 b) — MEGVAN, KÉT PÁRHUZAMOS ÚTVONAL

**Bizonyítottság: MEGERŐSÍTETT.** A teljes diszasszemblátum megválaszolja a
„hol van a képpontciklus" kérdést: **a LUT-család mind a hét tagja
(`AdjustCurves`/`AutoFix`/`Exposure`/`GradientMap`/`HSVGradientMap`/
`PaletteMap`/`TwoTone`) UGYANEZT a futószalagot futtatja**, csak a saját
`vtbl+0x20` slotjával eltérő tartalmú LUT-ot épít bele.

A függvény a CPU-jelzőt vizsgálja (`0xd695d2`/`0xd695d3` — ugyanaz a pár,
amit a `0x008f2640` mátrix-alkalmazó is nézett) és két, **funkcionálisan
azonos** utat választ:

1. **Skalár út** (`0xbcb360`–`0xbcb4e7`, a lassabb ág): soronként,
   képpontonként — ez pontosan az a mechanizmus, amit a TwoTone-elemzés
   (fent, „A LUT-skalár MEGVAN") már dokumentált: 4 forrás-bájt → 4 LUT-
   rekesz (`+0x000`/`+0x400`/`+0x800`/`+0xc00`, 256×4 bájt), a 4 dword
   bájtonkénti szétbontása, egyenkénti összegzés, kézi `[0,255]`-vágás,
   visszaírás ugyanarra a 4 bájt-helyre.
2. **SSE2 út** (`0xbcb4f2`–`0xbcb5cd`, a gyors ág): **ugyanaz a négy
   LUT-lekérdezés**, de a 4 bájtot egyszerre, egy `movd xmm.,[LUT+idx*4]`
   utasítással tölti be, és **`paddusb`-vel** (packed unsigned byte add,
   BEÉPÍTETT telítéssel) összegzi — nincs kézi vágás, a művelet maga
   telít. A belső ciklus soronként a `dec eax; jne` — a sorok között
   pointert lépteti (`[ebp+0x10]`/`[ebp-0x18]`, előjelesen skálázva a
   kép szélességéhez és a LUT-elrendezéshez).

**Mindkét út bájt-pontosan ugyanazt az eredményt adja** (telített
összeadás — a skalár út kézi vágása és a `paddusb` telítése matematikailag
azonos), csak a CPU-képesség dönt, melyik fut. ⇒ **A LUT-alapú effektek
teljes pixel-matematikája ezzel LEZÁRT**: a hét osztály mindegyikének
„algoritmusa" abból áll, hogy a saját `+0x20` slotja milyen 4×256×4 bájtos
LUT-ot épít — ez már a `TwoTone`-nál (négy rekeszből egy töltve) és az
`AdjustCurves`-nél (a `+0x40..+0x4c` négy görbecsatorna-leíró, fent) is
dokumentálva van; a maradék öt osztály (`AutoFix`, `Exposure`,
`GradientMap`, `HSVGradientMap`, `PaletteMap`) LUT-tartalma egyenként
ugyanezzel a módszerrel olvasható ki a saját `vtbl+0x20` szerint.

⇒ **`FUN_00bb9e00` MÁR MEGVAN, kereszthivatkozás pótolva (2026-09-21).** A
függvény szerepe: a filterdesc.xml pontlistájának `x`/`y` attribútumú elemeit
járja be (a névsztringek — `0xcac5b4`="x", `0xcac5b8`="y" — a helyi
diszasszemblátumból közvetlenül kiolvashatók), és minden pontot a
`FUN_008f2c70` ponttárolóba fűz. **Ez maga NEM az interpolációs aritmetika**
— az a lentebbi „Az `AdjustCurves` ponttárolója és természetes spline-
cache-e" szakaszban (2026-09-18) teljes egészében megvan: `FUN_008f2c70`
ponttároló-rekord, `FUN_008f3290` bináris keresés + kiértékelés,
`FUN_008f33b0` tridiagonális természetes spline-megoldó, zárt képlettel. A
hetes LUT-család pixel-matematikája ezzel **teljesen lezárt**; a
fennmaradó apró nyitott rész (nem blokkoló) a görbepont-rekord **második
gyorsítótár-rekeszének** (`+0x10`/`+0x14`) azonosítatlan fogyasztója — ld.
ugyanott.

## 12. A SZŰRŐ KOORDINÁTA-HORGA: `CGenericFilter` `+0x84`, mátrix ÉS inverz (2026-09-16, #3169)

**A kérdés,** amire ez a szakasz válaszol: hol érvényesül a vágás a
szűrőláncban — a lánc elején, a végén, vagy a pozíciójában? A #3169 azért
tette fel, mert nálunk az `apply_filters` a vágást és a kereteket a lánc
**végére halasztja**, és emiatt az élő előnézet 18,2 átlagos eltérést ad a
mentett képhez a `crop64;Vignette` láncon.

**A válasz: egyik sem — az eredeti a KOORDINÁTÁKAT képezi le.**

### Az osztály és a két szomszédos slot

| tétel | cím | mi |
|---|---|---|
| `CGenericFilter::vftable` | `0x00cd184c` | a lánc op-osztálya, **43 slot** |
| `+0x80` | `FUN_008f6e40` (51 b) | **render**: a `[this+0xc]` render-callback hívása 4 argumentummal, majd `[this+0x64]`/`[this+0x68]` = `-1` (gyorsítótár-érvénytelenítés) |
| `+0x84` | `FUN_008f6e80` (146 b) | **a koordináta-leképezés átadása** |

⚠️ Az osztály **nem** az RTTI-táblából jött: ott a ≥34 slotos vtáblák mind
felületi osztályok. Bájtszintű pásztázás adta — 34-nél több egymást követő,
érvényes kódcím, ahol a **32.** slot a lánc-moduljába (`0x008f…0x0091…`)
esik. A teljes fájlban **két** ilyen jelölt van (a másik a
`CRetouchFilter::vftable`, `0x00cc1b0c`).

### Mit tesz a `+0x84`

1. **10 dwordöt** másol a paraméterből a `[this+0x6c]`-be: 9 float (3×3-as
   mátrix) + 1 jelzőbájt;
2. ha a paraméter `[+0x24]` jelzője áll, a `[+8]`/`[+0x14]` mezőt **negálva**
   épít mátrixot (a tisztán eltolásos eset inverze);
3. különben `FUN_00a4a140`: a 3×3-as **determináns** (`0x00a4a148`-tól
   `m11·m22 − m12·m21`…), nullára ellenőrizve ⇒ **mátrix-invertálás**;
4. az eredmény a `[this+0x94]`-be kerül.

⇒ Minden szűrő megkapja és eltárolja **a leképezést és annak inverzét**.

### Ki hívja, és mire

A szerkesztő `FUN_006ad860` (2590 b), ebben a sorrendben:

| lépés | cím | mit |
|---|---|---|
| 1 | `0x006ad8dd` | a lánc utolsó elemét veszi (`[obj+0x10c]` tömb, darab = `[obj+0x110] >> 1`) |
| 2 | `0x006ad943`, `…981`, `…9b9` | ha az utolsó `redeye` / `retouch` / `picnik`, kiveszi a listából (`FUN_00906fc0`, darab−1) és egy másik listába teszi (`[obj+0x15c]`) |
| 3 | `0x006adb2d` | a maradék utolsó elemét a **`crop64`**-hez méri |
| 4 | `0x006adbc1`–`…c3f` | **visszafelé** keresi az utolsó `crop64` indexét |
| 5 | `0x006adc84` | abból az opból **négy dwordöt** olvas (`+0x40`…`+0x4c`) — a téglalap |
| 6 | `0x006add5a` | `FUN_0090fcc0`: **forgatási mátrixot** épít (`sin`/`cos`, fok→radián a `0xcf4760`-on, a szög negálva) |
| 7 | `0x006add70`–`…d95` | a lánc **MINDEN tagján, 0-tól a darabszámig**, meghívja a `+0x84`-et a struktúra mutatójával |
| 8 | `0x006add97`–`…de2` | a téglalapot érvényesíti (`bal < jobb`, `fent < lent`), és `[obj+0x240…0x24c]`-be írja; érvénytelenre **nullázza** |

### Amit ez nálunk eldönt

* Az eredeti **sorrendben renderel**; a vágás nem ugrik se a lánc elejére, se
  a végére.
* A térben változó effektek (`Vignette`, elmosások) azért maradnak helyesek,
  mert a koordinátáikat a leképezésen át kapják.
* A mi lánc-szintű leképezésünk (#3166, `render/chain_geometry.py`) ennek a
  **lánc-szintű, render utáni** megfelelője — a hiányzó darab az op-szintű
  mátrix (és inverz). Ez a **#3229**.

*Bizonyítottsági fok: **megerősített** — diszasszemblált törzsek, címekkel; a
determináns-számítás és a fok→radián konstans közvetlenül olvasva. Amit NEM
mértem: hogy a `CRetouchFilter` (a másik jelölt) `+0x84`-e ugyanezt teszi-e.*

## ⛳ A `DropShadow` vászon-margója: `ceil(blur × 1,3501)`, és a `blur` KÉPPONT (2026-09-17, 319. kör, #626)

*A termékkódunkban két, egymásnak ellentmondó modell él ugyanarra a szűrőre —
a `render/glimmer_frame_ops.py:216` ezt maga mondja ki, és a #626-ra hivatkozik.
Ez a szakasz a binárisból dönti el.*

### A határoló doboz kiterjesztője: `0x00bcd760`

A `DropShadow` `apply`-ja (`0x00bbb720`) a kimeneti méretet ettől a
függvénytől kéri (`0x00bbb7ba`), majd a visszakapott téglalapból számol
szélességet és magasságot (`0x00bbb7c7`–`0x00bbb7d1`).

A kiterjesztő a **minőség-fokozatra** (`[objektum+0x1c]`) ágazik, és a két
elmosás-paramétert (`[+0x10]` = `blurX`, `[+0x14]` = `blurY`) szorozza:

| minőség | szorzó | cím |
|---:|---:|---|
| **1** | **0,25** (`0x00c7d9c8`) | `0x00bcd7e5` |
| **2** | **1,05** (`0x00cf4360`) | `0x00bcd7b1` |
| **3** | **1,3501** (`0x00cf4368`) | `0x00bcd78d` |
| bármi más | **nincs kiterjesztés** | `0x00bcd781 jne` |

A szorzat **felfelé kerekül**: a `0x00c090f0` hívás a CRT-leíró-tábla szerint
**`Math.ceil`** (a `0x00c7d85c`-en álló `{név, függvény}` pár neve
`0x00cd04ec` = `"Math.ceil"`; a szomszédai `Math.abs`, `Math.floor`,
`Math.round`, `Math.sqrt` — ez egyben a Flash-eredet újabb bizonyítéka).

⇒ **oldalanként `ceil(blurX · f)` vízszintesen és `ceil(blurY · f)`
függőlegesen** (`0x00bcd869`–`0x00bcd88d`: bal −, fent −, jobb +, lent +).

### A `distance` külön lépés, és a végeredmény UNIÓ

A kiterjesztett dobozt a `0x00bcdea0` által adott `(dx, dy)` **eltolja**
(`0x00bcd8a2`–`0x00bcd8ac`), majd a kód az **eredeti** dobozzal vett uniót
tartja meg (`0x00bcd8ae`, `0x00bcd8bd`, és a `0x00bcd8c1` visszaállító ág).

⇒ **A margó NEM `2 · blur + distance`.** Az elmosás `ceil(blur·f)`-fel tágít,
az eltolás pedig eltolja a dobozt; a kimenet a kettő uniója az eredetivel.

### A `blur` KÉPPONTBAN van — nincs sehol kép-mérethez kötés

A kiterjesztőben a `blurX`/`blurY` **egyetlen** szorzót kap (a fenti
minőség-faktort), és a kép szélessége/magassága ott **elő sem fordul**. A
paraméter-vágó (`0x00bcd640`) a két értéket `clamp(1, 255)`-re szorítja, a
minőséget pedig `min(q, 15)`-re (`0x00bcd73a`–`0x00bcd744`) — nem `0`-ra vagy
`15`-re állítja, ahogy a 4.12 korábbi jegyzete sugallta.

**A leíró ezt megerősíti** (`filterdesc.xml`): mindkét használat
`quality="{BitmapFilterQuality.HIGH}"`, és

- az önálló effekt: `blurX="{_sldrBlur.value}" blurY="{_sldrBlur.value}"` —
  a csúszka értéke **közvetlenül**, átváltás nélkül;
- a Polaroid: `blurX="8" blurY="8" distance="3" angle="{90−forgatás}"`.

A Flash `BitmapFilterQuality.HIGH` = **3** ⇒ a szorzó **1,3501**, tehát a
Polaroid árnyékának margója `ceil(8 · 1,3501)` = **11 képpont** oldalanként.

**A Polaroid keret színe és a forgatás iránya (#3420, 2026-09-23).** A leíró
`SimpleBorderImageOperation`-je a képkeretet rögzítetten **fehérre** festi
(`color="0xffffff"`); a színválasztó (`_cpkrOuter`, alap `E2E2E2`) csak az
árnyék `backgroundColor`-jába és a `RotateImageOperation` `borderColor`-jába
megy. A `RotateImageOperation degAngle` **pozitív értéknél az óramutató
járása szerint** forgat — a 684-es golden `Rotate = 5`-ös exportján a keret
felső éle jobbra lejt. A kettő átvezetése után a három golden-állás ΔE-je
22,46 / 18,65 / 22,68 → **2,58 / 0,69 / 1,10** (`min` / `alap` / `max`).

### ⛔ Amit ez a termékkódunkról mond

A `render/glimmer_frame_ops.py` önálló `DropShadow` útja a `blur`-t a
**rövidebb oldal százalékaként** veszi (`thickness_px`), és `2·blur_px +
distance` margót számol. **Mindkettő téves:**

| | eredeti (mérve) | nálunk (ma) |
|---|---|---|
| `blur` egysége | **képpont** | a rövidebb oldal százaléka |
| margó oldalanként | **`ceil(blur · 1,3501)`** (HIGH) | `2 · blur_px` |
| `distance` | a dobozt eltolja, majd unió | hozzáadódik a margóhoz |

A javítás a **#626** jegyen marad (ez a jegy a fejlesztői gazdája).

*Forrás: `0x00bbb720` (apply), `0x00bcd760` (a kiterjesztő, 467 b),
`0x00bcd640` (a vágó, 285 b), a konstansok `0x00c7d9c8` = 0,25 ·
`0x00cf4360` = 1,05 · `0x00cf4368` = 1,3501; a `Math.ceil` azonosítása a
`0x00c7d85c`-es CRT-leíró-párból; a leíró-attribútumok
`research/copy_Picasa_3_7/Picasa3/runtime/filterdesc.xml`.*

## ⛳ A Polaroid geometriája: az árnyék eltolása FLOOR, a margó unió, a forgatás képpontközépre (2026-09-27, 382. kör, #626)

*Bizonyítottsági fok: **megerősített**, utasításszinten, független újralevezetéssel (EGYEZIK) és golden-méréssel.*

A Polaroid három golden-állása a #3420 után 2,58 / 0,69 / 1,10 ΔE-vel tért
el (`min` / `alap` / `max`). A hibatérkép szerint az eltérés **geometriai**:
a tartalom 1–3 képponttal el volt tolva. Három ok együtt adja ki.

### 1. Az árnyék eltolása `floor`, nem `round` — helyesbítés

A `DropShadowImageOperation` szakasza (fent) `round`-ot írt, cím nélkül. Az
`0x00bcdea0` utasításai:

```asm
0x00bcdea3  fld   dword ptr [edi+4]        ; szög (fok)
0x00bcdea6  fmul  qword ptr [0xcf4080]     ; π
0x00bcdeac  fdiv  qword ptr [0xcf3d48]     ; 180,0
0x00bcdeb5  call  0xc29d20                 ; cos
0x00bcdeba  fadd  qword ptr [0xcf4078]     ; 6,7e-06
0x00bcdec3  fmul  dword ptr [edi]          ; × távolság
0x00bcdec5  fadd  qword ptr [0xcf4070]     ; 0,001825
0x00bcdece  call  0xc0b1e0                 ; floor
0x00bcded6  call  0xc29990                 ; → egész (csonkol)
            ...ugyanez sin-nel (0x00bcdee0 call 0xc285f0) a dy-ra
```

```
dx = floor( (cos(szög·π/180) + 6,7e−06) · távolság + 0,001825 )
dy = floor( (sin(szög·π/180) + 6,7e−06) · távolság + 0,001825 )
```

A `0x00c0b1e0` a `floor` (ld. „A kvótaosztás” sort a `QuantizePalette`
szakaszban). A két kis tag tehát nem döntetlen-eldöntő, hanem **lebegőpontos
védelem**: a 2,9999… alakú, valójában egész szorzatot emeli át az egészen,
mielőtt a `floor` lecsípné. A Polaroidnál (`távolság = 3`, `szög = 90 − forgatás`):

| forgatás | szög | `round` (a spec eddig) | **`floor`** |
|---:|---:|---|---|
| 5 | 85° | (0, 3) | **(0, 2)** |
| 10 | 80° | (1, 3) | **(0, 2)** |
| −10 | 100° | (−1, 3) | **(−1, 2)** |

A két kerekítés a (távolság 0–30, szög 0–360°) párok **71%-ánál** eltér; az
alapértelmezett 45° / 4-nél `(3, 3)` helyett `(2, 2)`. A DropShadow
golden-esetei (0°, 90°, 360°) ezt nem mutatják, mert tengelyirányú szögnél a
kettő egybeesik.

### 2. A vászon az eredeti és az eltolt-kiterjesztett doboz UNIÓJA

Ezt „A `DropShadow` vászon-margója” szakasz már leírta (`0x00bcd869`–
`0x00bcd924`, egész aritmetika): `unió(eredeti, eredeti ± ceil(8 · 1,3501) +
(dx, dy))`. Oldalanként: **bal `11 − dx`, fent `11 − dy`, jobb `11 + dx`,
lent `11 + dy`** (`|dx|, |dy| < 11`). Az önálló `DropShadow` kódunk ezt már
követi (`drop_shadow_padding`), a Polaroid-ág viszont mind a négy oldalra
11-et tesz.

### 3. A forgatás a képpontközepekre szimmetrikus

A `0x00bc8060` a cél → forrás mátrixot így rakja össze (`0x009e6340`,
balról szorozva): `T(sW/2, sH/2) · R · F · T(−dW/2, −dH/2)`. Itt `sW`, `sH`
a forrás, `dW`, `dH` a cél mérete (`0x00bc817f`–`0x00bc81d6`,
`0x00bc82c1`–`0x00bc8329`), `F` a tükrözés (±1, `0x00bc81e1`–`0x00bc8239`),
`R` pedig a forgatás. A mintavevő a képpont közepét (`+0,5`) vetíti vissza,
tehát a forrás középpontja **pontosan** a cél középpontjára esik. Nálunk a
`rotate_with_pad` a képet egész osztással (`//2`) teszi a vászonra, és az
OpenCV sarok-konvencióját használja, ami fél képpontokat tol el.

A forgatás a wrapperben (`0x00bcb5e0`) **nem** a `ytResampler`-re megy:
forgatásos mátrixnál (`0x009e6da0`: `|m1|` vagy `|m3|` > 0,0001) a
`0x009e6df0` általános út fut, `param_4 = smoothing = 1` értékkel
(`0x00bc832e` `push 1`), és ez a **`0x009e7060`**-at hívja (`0x009e6fda`).
Ez **8 bites súlyú, fixpontos bilineáris** mintavevő:

- soronként: `u = m0·(x + 0,5) + m1·(y + 0,5) + m2`, `U = fistp(u · 65536) − 32767`,
  tehát a forrás képpontközepe is `i + 0,5`-nél van (`[0x00cf3cb0]` = 65536,0,
  `add edx, 0xffff8001`); a lépés `fistp(m0 · 65536)`;
- képpontonként: `ix = U >> 16`, `fx = (U >> 8) & 0xFF` (ugyanígy `y`), és
  `lerp(a, b, f) = a + floor((b − a) · f / 256)`, előbb vízszintesen, aztán
  függőlegesen, mind a négy csatornán (`0x009e7233`–`0x009e725b`, MMX);
- a perem egy képpontos sávjában a kilógó szomszéd a szélső képpont
  (`0x009e7269`–`0x009e72dd`); azon kívül a célképpont érintetlen marad, ott a
  padBorder `borderColor`-ja áll.

A cél mérete padBorderrel `csonk(|W·cos θ| + |H·sin θ|)` × `csonk(|W·sin θ| +
|H·cos θ|)` (`0x00bc7ca0`); ez egyezik a kódunk `floor`-jával.

### Natív QEMU-próba (#626, 2026-10-04)

A `qemu-i386` alatt a natív `0x009e7060` mintavevőt hívtam meg közvetlenül
BGRA képleírókkal; a méretpróbában a natív `0x00bc7ca0` segédfüggvény futott.
Az input csatornái képpontonként `(x,y)`:
`B=(37x+11y)&255`, `G=(19x+43y)&255`, `R=(73x+7y)&255`,
`A=(91+13x+17y)&255`; a kitöltés `(17,91,233,255)`. A négy méret
`(4,3)`, `(5,4)`, `(4,6)`, `(5,5)` és a hat szög `0°`, `5°`, `−10°`,
`10°`, `−12°`, `30°` keresztszorzata **24 eset**. Mind a 24-ben a natív
mintavevő BGR-kimenete bájtra egyezett a `rotate_with_pad` kimenetével;
mind a 24 natív méretválasz egyezett a fenti csonkoló méretképlettel.
Ez a kimeneti BGR-csatornákat hasonlítja: a PicasaPy függvénye háromcsatornás
BGR-t fogad és ad, ezért a natív negyedik (alfa-)csatorna nem része az
egyezési állításnak.

**Cáfoló kontroll:** az aszimmetrikus `5×5`, `+30°` natív mintavételt a helyi
`−30°` kimenettel is összevettem: **94 BGR-bájt eltért**. Így a próbaminta és
az összevetés észleli az előjelcserét; a 24 egyezés nem szimmetrikus mintából
adódó ál-egyezés.

**A próba határa:** a QEMU-wrapper közvetlenül a pixelmagot és külön a
méretsegédet futtatta. A `0x00bb5640` teljes Glimmer-Apply útját (az XML
attribútum-beolvasástól a transzformmátrix felépítéséig) ebben a körben nem
futtattam; a szögkonverziót és mátrix-összeállítást az utasításszintű
levezetés támasztja alá (`0x00bb5730`, `0x00bc8060`, `0x009e6340`). Ezért a
natív pixelmag és a méretképlet megerősített, az integrált Apply-út bájtszintű
QEMU-goldenje **nincs meg**.

### Mérve

684-es mérőkészlet, ΔE a Picasa-exporthoz. A lépések egymásra épülnek, és
minden más változatlan:

| eset | ma | + `floor` | + unió-margó | **+ képpontközepes forgatás** |
|---|---:|---:|---:|---:|
| `Polaroid` alap (5°) | 0,694 | 0,673 | 0,354 | **0,149** |
| `Polaroid` max (10°) | 1,095 | 1,069 | 0,822 | **0,155** |
| `Polaroid` min (−10°) | 2,584 | 2,566 | 0,989 | **0,154** |
| `DropShadow` alap / max / min | 0,084 / 0,054 / 0,083 | változatlan | — | — |

A három ok közül egyik sem elég egyedül. A képpontközepes forgatást a
`cv2.INTER_LINEAR` bilineárisával mértük; a 8 bites fixpontos lerpet nem
modelleztük, a hatását ez a mérés nem mutatja.

A megvalósítás (#3809) a fixpontos mintavevőt is átvette. Vele a három eset
**0,118 / 0,131 / 0,131** (alap / max / min), a `DropShadow` három esete
változatlan (0,084 / 0,054 / 0,084). A fixpontos lerp tehát további
0,02–0,03-at hoz a `cv2.INTER_LINEAR`-hez képest.

#### Eredeti / nálunk

| | eredeti | nálunk (#3809 óta) |
|---|---|---|
| árnyék-eltolás | `floor(… + 0,001825)` | `math.floor(…)` (`glimmer_frame_ops.shadow_offset`) — minden DropShadow-ra |
| Polaroid-vászon | unió: bal `11 − dx`, fent `11 − dy`, jobb `11 + dx`, lent `11 + dy` | `drop_shadow_padding` → `pads` (`glimmer_frames.apply_polaroid`) |
| forgatás | a forrás közepe a cél közepére, képpontközéppel | ugyanez a mátrix (`glimmer_frame_ops.rotate_with_pad`) |
| mintavevő | 8 bites súlyú bilineáris, `a + floor((b − a)·f/256)` | ugyanez (`fixpontos_mintavevo.fixpontos_bilinearis`, #3846) |

Fejlesztés: #3809.

## ⛳ A `DropShadow` `quality=3` natív elmosása: hat egydimenziós menet (2026-09-22, #626)

### Mit ad ma a PicasaPy — mérve

A mai `draw_drop_shadow()` a `compose_drop_shadow()` útvonalon a
`gaussian_blur_f(shadow_layer, blur_px)` hívást használja
(`src/picasapy/render/glimmer_frame_ops.py:212–224`). A tesztkészlet ettől
függetlenül a jelenlegi geometriát ellenőrzi: a célzott körben
`tests/render/test_dropshadow_margo_3419.py` és
`tests/render/test_glimmer_frames.py` együtt **30 passed in 2,49 s**.
Ez a mérés nem bizonyít natív pixelazonosságot.

### A natív hívási lánc

A `DropShadowImageOperation` rajzolója (`0x00bcd940`) a blur-diszpécsert
(`0x00bc5680`) a két blur-paraméterrel és a minőségértékkel hívja
(`0x00bcd940` dekompilátum, a `FUN_00bc5680` hívása). A sorrend a rajzolóban:

1. az árnyék színű téglalap létrehozása (`0x00bcd940`),
2. a blur-diszpécser meghívása (`0x00bcd940`),
3. a forrás és az árnyék kompozitálása (`0x00bcd940`, végső
   `FUN_008f59d0` hívás).

A blur-paraméter-vágó (`0x00bc52c0`) a sugarakat `0…253` közé szorítja,
a `quality` értéket pedig `1…15` közé: a nulla **1**-re változik, a
nem nulla, legfeljebb **15** érték változatlan marad (`0x00bc52c0`). A
`quality=3` ezért a blur-meneten ténylegesen **3**-ként fut, nem vált át
másik minőségi számra.

### Mit jelent pontosan a `quality=3`

A diszpécser több optimalizált megvalósítási ágat választ a blur-sugár
és két futásidejű jelző alapján (`0x00bc5680`). Az elemzett binárisban a
két jelző kezdeti bájtja **0** (`0x00d695d2`, `0x00d695d3`); a `d695d2`
bájtját azonban induláskor a `0x00c33d56` írhatja, a `0x009bbd50` visszatérési
értékének **26. bitjéből** (`shr eax,0x1a` → `and al,1`). Ezért a
konkrét optimalizált kódút futásidő- és processzorkörnyezet-függő, de a
minőségi menet szerkezete közös.

A két tengelyt külön, egymás után dolgozza fel:

| tengely | natív megvalósítási családok | a `quality` ciklusa |
|---|---|---:|
| vízszintes | `0x00bc7540`, `0x00bc6920`, `0x00bc7300` | `param_3`-szor; `0x00bc7540: local_34 = param_3`, majd `local_34--` |
| függőleges | `0x00bc77b0`, `0x00bc6f30`, `0x00bc6b60` | `param_3`-szor; `0x00bc77b0: local_10 = param_3`, majd `local_10--` |

Következésképp `quality=3` esetén a normál, mindkét tengelyen aktív
út **3 vízszintes + 3 függőleges, összesen 6 egydimenziós menetet** fut.
A két puffer között menetenként vált (`0x00bc7540` / `0x00bc77b0` és a
vektoros megfelelőik); ez nem hat menet egyetlen közös pufferbejárásban,
hanem tengelyenként egymásra épülő menetek. Ha egy tengely sugara nem
aktív vagy a tartomány túl rövid, a kód másolási utat választ
(`0x00bc5960`); ez a `quality=3` hatmenetes esetét nem cáfolja, hanem a
határfeltétel külön ága.

### A menet magja és a kvantálás

A sugárhoz tartozó fixpontos együtthatókat a `0x00bc5360` állítja elő.
A dekompilátumban a lekerekített sugár (`FUN_00c29990`) alapján a belső
lépték 6-ról indul és feleződik, amíg 1 fölött marad; ezután a kód
`2^k`, `2^k−1`, a `(r−1)·2^(k−1)` lekerekített értéke, valamint bitmaszkok
segítségével képezi a menet három egész paraméterét
(`0x00bc5360`, `0x00bc5620`). A teljes leképezés tehát nem egy szabadon
illesztett Gauss-sugár.

A skalár kimeneti segéd (`0x00bc5480`) minden BGRA-bájtra egész aritmetikát
használ: a két mintavételi összeg és a futó akkumulátor kombinációját
szorzóval, balra tolással és egész osztással alakítja bájttá
(`0x00bc5480`). A határszakaszok külön ágai a szélső mintákat ismételten
használják (`0x00bc7540`, `0x00bc77b0`); a cél nem lebegőpontos Gaussian-
értékek kiírása.

### Eredeti / nálunk / teendő

| | Eredeti, mérve | PicasaPy, mérve | Teendő |
|---|---|---|---|
| minőségi ciklus | `quality=3` → 3 vízszintes + 3 függőleges menet (`0x00bc7540`, `0x00bc77b0`) | a `draw_drop_shadow()` egyetlen `gaussian_blur_f()` hívása (`glimmer_frame_ops.py:216`) | a natív hatmenetes út átvezetése |
| menet matematikája | futóablakos, fixpontos/integer út; sugárfüggő együttható-előkészítés (`0x00bc5360`, `0x00bc5480`) | lebegőpontos Gaussian-kernel | azonos puffer-, perem- és csonkolási szerződés megvalósítása |
| natív–PicasaPy pixel-golden | **NINCS MEG** ebben a körben | **NINCS MEG** | külön Windows/Picasa export–render golden-pár szükséges |

**Bizonyítottsági fok: megerősített** a `quality=3` ciklusszámára,
a vízszintes→függőleges sorrendre, a puffer-váltásra és az integer
kimeneti útra. A sugárhoz tartozó három együttható teljes jelentését és a
különböző optimalizált ágak bitre azonos megfelelését ebben a körben nem
mértem össze — ezekre nem adok át nem bizonyított kernel-táblát. *(A különböző ágak egyezése 2026-09-23-án lemérve: bájtra azonosak — ld. „A SIMD-ágak” szakaszt lent.)*

**A megfejtett mechanizmus hatása a PicasaPy eltérésére NINCS MÉRVE:** a
natív út leírása önmagában nem bizonyítja, hogy a hatmenetes csere egy
adott golden-páron javít; ehhez eredeti Picasa-export és ugyanazon bemenet
PicasaPy-kimenete kell.

*Forrás: `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`;
`0x00bcd940`, `0x00bc5680`, `0x00bc52c0`, `0x00bc5960`, `0x00bc6590`,
`0x00bc5360`, `0x00bc5480`, `0x00bc7540`, `0x00bc77b0`, valamint a
`626-drop-shadow-branches.log` célzott Ghidra-kimenete.*

### ✅ Kiolvasva, emulátorral bitre igazolva és átvezetve (2026-09-22, #3474)

*A fenti „NINCS MEG" / „nem mértem össze" pontok ezzel lezárultak. A natív
kódot unicorn-emulátorban (a PE szekciói a saját VA-jukon, a skalár ág
jelzőivel) futtattuk, és a PicasaPy-megvalósítást (`render/nativ_blur.py`)
ehhez mértük: **0 eltérő bájt** minden próbán.*

**`0x00bc5360` — sugár → `(k, h, w, osztó)`.** `n = _ftol2(r)` (nulla felé
csonkol), `k = 6`; ha `n > 1`: `k--`, `n >>= 1`, amíg `n > 1` és `k ≠ 0`.
- `k ≠ 0`: `v = chop((r − 1)·2^(k−1))`, `w = v & (2^k − 1)`,
  `h = (v >> k) + 1`, `osztó = 2^k + 2v`;
- `k = 0` (`n ≥ 64`): `v = chop(ceilf(r − 1) · −0,5)`, `w = 0`,
  `h = 1 − v`, `osztó = 2h − 1` (a `0x00529e10` a `ceilf`; `floor`-ral 5988
  sugáron eltér).
- Igazolva 16 142 sugáron (1…253, 1/64-es lépés + határesetek).

**`0x00bc5480` + `0x00bc7540`/`0x00bc77b0` — egy menet.** Csatornánként,
szélső minta ismétlésével:
`ki[i] = (w·(s[i−h] + s[i+h]) + 2^k · Σ_{j=i−h+1}^{i+h−1} s[j]) // osztó`
(előjel nélküli, csonkoló osztás). Előbb `quality` vízszintes, aztán
`quality` függőleges menet (`0x00bc6590`), két puffer között váltva; a
diszpécser a sugarat `0…253`-ra, majd `min(r, hossz·0,5)`-re vágja, és egy
tengely csak `r > 1` és `hossz ≥ 2` mellett mosódik. A négy csatorna
független, előszorzás nincs.

**A kompozitálás (`0x00bcd940`, `0x008f48b0`).** Az árnyékréteg egyenes
BGRA: a teljes vászon `árnyékszín | alfa 0`, a téglalap
~~`ROUND(shadowAlpha·255)`~~ → **`TRUNC(float32(shadowAlpha)·255)`** (helyesbítve lent, #3498) alfával ⇒ az elmosás gyakorlatilag csak az alfát
mossa. A keverés egész: `(S·α + D·(255 − α)) // 255` (3000 képpontpáron
0 eltérés). A sugár a mi `blur_px`-ünk (ugyanaz a két mező, amit a
`0x00bcd760` a margóhoz ×1,3501-gyel szoroz).

**Mérés valódi Picasa-exporton** (684-es golden, `EXIF Software = Picasa`),
átlagos ΔE a Picasa-exporttól, a régi Gauss-út → a natív út:
`alap` (Blur 10, Fade 30) **0,713 → 0,084**; `min` **0,279 → 0,083**;
`max` (Fade 100, nincs látható árnyék) 0,054 → 0,054.

*Nyitva marad (nem blokkol):* ~~(1) hogy a rajzoló `+0x0c` alfa-mezője a
`shadowAlpha` — a paraméterépítő (`0x00bbb8d0`) első lebegőpontos mezője
a `shadowAlpha` (alapértéke `fld1` = 1), a leképezés utasításszintű
végigkövetése hiányzik, a golden-mérés viszont ezt a leképezést igazolja;~~ → **LEZÁRVA lent**;
~~(2) a SIMD-ágak (`0x00bc6920`, `0x00bc7300`, `0x00bc6f30`, `0x00bc6b60`)
bitre azonossága a skalár úttal nincs mérve.~~ → **LEZÁRVA lent (346. kör): bájtra azonosak.**

### ⛳ A `shadowAlpha` útja utasításszinten — és az alfa-bájt CSONKOLT, nem kerekített (2026-09-22, 345. kör, #626)

A fenti „Nyitva marad" (1) pontja lezárva. A lánc:

| lépés | mit tesz | cím |
|---|---|---|
| paraméterépítő `0x00bbb8d0` | a helyi alapérték `fld1` (= 1,0), majd a getter (`0x008ef520`) a `[op+0x24]` = `shadowAlpha` attribútumot `double`-ként adja, és **float32**-be tárolja | `0x00bbb8d9`–`0x00bbb8f6` |
| ugyanott | a 0x24 bájtos rekord konstruktorának (`0x00bcd640`) a **4.** veremargumentuma ez a helyi | `0x00bbba5a`–`0x00bbba5e` |
| konstruktor `0x00bcd640` | `clamp(·, 0, 1)` (`fldz`/`fld1` + két `fcom`), majd `fstp dword [rec+0x0c]` | `0x00bcd654`–`0x00bcd68c` |
| rajzoló `0x00bcd940` | `fld dword [rec+0x0c]`, `fmul qword [0x00cf39d0]` (= 255,0), **`fnstcw` + `or eax, 0xc00` + `fldcw`** (kerekítési mód = nulla felé), `fistp`, majd `shl edx, 0x18` \| a szín (`and ecx, 0xffffff`, `0x00bcd9c6`) | `0x00bcda34`–`0x00bcda96` |

A konstruktor teljes rekordja (`ret 0x20`, 8 veremargumentum + `edx`):

| eltolás | mező | átalakítás |
|---|---|---|
| `+0x00` | `distance` | — |
| `+0x04` | `angle` | — |
| `+0x08` | `shadowColor` (ARGB egész) | — |
| `+0x0c` | **`shadowAlpha`** | `clamp(0, 1)` |
| `+0x10` | `blurX` | vágás `0` és `255,0` közé (`0x00cf39d0`, `0x00cf3a00`) ¹ |
| `+0x14` | `blurY` | ugyanaz ¹ |
| `+0x18` | `strength` | ugyanaz ¹ |
| `+0x1c` | `quality` (`edx`) | `< 0` → 0, `> 15` → 15 |
| `+0x20` | `inner` (bájt) | — |

¹ A három mező a veremen tartott `0`, `255,0` (`qword`) és `255,0` (`dword`) konstansokkal hasonlítódik; az egyes `fcom`-ágakat nem követtem végig egyenként, ezért a pontos vágási irány itt **nincs kimondva** — a kérdés (a `+0x0c`) ettől független.

⇒ **Az árnyék-téglalap alfája `TRUNC(float32(clamp(shadowAlpha, 0, 1)) · 255)`.**
A fenti szakasz `ROUND`-ot írt, és a kódunk (`glimmer_frame_ops.py`) is
kerekít, azzal az indoklással, hogy a `fistp` alapmódja a páros felé
kerekítés — de a rajzoló a `fistp` előtt kifejezetten csonkolásra állítja
a módot.

**Mekkora a különbség (számolva, nem becsülve):** a DropShadow szűrő
`shadowAlpha="{1-(_sldrFade.value/100)}"` (`filterdesc.xml` 854. sor); a
101 egész `Fade`-értékből **48-nál** a csonkolás 1-gyel kisebb alfát ad
(pl. Fade 2: 249 ↔ 250, Fade 50: 127 ↔ 128). A többszörös-20 értékeknél
(`2,55·f` egész) a float32 érték az egész fölé esik, ott nincs eltérés. A
Polaroid rögzített `shadowAlpha=".4"`-je (1236. sor) mindkét módon 102. A
684-es golden három állása (Fade 0 / 30 / 100) mind egyező értékre esik,
ezért a golden-mérés ezt nem láthatta. Képpontonkénti felső korlát:
`|árnyékszín − háttér| / 255 ≤ 1` szint.

*Bizonyítottsági fok: **megerősített** (utasításszintű kiolvasás). A
pixelgoldenen mért hatás: **NINCS MEG** — ehhez egy 48 érintett Fade-érték
egyikén készült eredeti export kellene; a javítás ettől függetlenül a
binárist követi. Fejlesztés: **#3498** — ✅ beépítve 2026-09-24 (`glimmer_frame_ops.teglalap_alfa`).*

### ⛳ A SIMD-ágak bájtra azonosak a skalár úttal — mert a vektoros út LEFELÉ kerekítésre állítja az FPU-t (2026-09-23, 346. kör, #626)

A fenti „Nyitva marad" (2) pontja lezárva. **Melyik ág fut egy valódi
gépen:** a diszpécser (`0x00bc5680`) a vektoros útra lép, ha a `0x00d695d2`
vagy a `0x00d695d3` bájt nem nulla (`0x00bc5794`–`0x00bc57a4`). A
`0x00d695d2`-t a `0x00c33d30` írja: `CPUID` 1-es levél (`0x009bbd50`,
`cpuid` a `0x009bbda6`-on), és a kimenetek veremkiosztása szerint az
**EDX 26. bitje** (`0x00c33d4d`–`0x00c33d56`) — az **SSE2** jelzőbitje.
⇒ Minden SSE2-es processzoron (gyakorlatilag minden gépen, amin a Picasa 3
fut) a **vektoros** út fut, nem a skalár, amelyet a #3474 átvett.

**Mit számol a vektoros menet** (`0x00bc7b80`/`0x00bc7c10`):
ugyanazt a számlálót, mint a skalár — `pslld` a `2^k`-val és `pmaddwd` a `w`
együtthatóval (`0x00bc7ba7`–`0x00bc7bb3`) —, az osztás viszont két
változatban megy:

| ág | osztás | cím |
|---|---|---|
| az osztó kettő-hatvány (`p2`: `H-simd` `0x00bc6920`, `V-simd2` `0x00bc6b60`) | `psrld` a kitevővel (a `0x00bc5620` számolja) → **csonkol** | `0x00bc5670`, `0x00bc5640`–`0x00bc5648` |
| minden más (`H-simd2` `0x00bc7300`, `V-simd` `0x00bc6f30`) | `cvtdq2ps` → `divps` az osztóval (float, `0x00bc5570` tölti) → `cvtps2dq` | `0x00bc5660`–`0x00bc5666` |

A második sor kerekítése az **MXCSR**-től függ. A vektoros út eleje
(`0x00bc57e0`: `mov eax, 2` → `0x009025c0`) elmenti a vezérlőszót, majd
`_controlfp(új, maszk)`-ot hív a 2-es táblaelemmel: `új = [0x00d333a4]` =
**`0x100` = `_RC_DOWN`**, `maszk = [0x00d333c0]` = `0x300` = `_MCW_RC`; a
diszpécser a végén visszaállítja (`0x00bc58d8`–`0x00bc58e1`). A `_controlfp`
(`0x00c0963e`) az MXCSR-t is átírja, ha a futtatókönyvtár SSE2-jelzője
(`0x00da1428`) 1 (`0x00c097af`) — ezt a `__get_sse2_info` (`0x00bf5fd5`)
írja induláskor ugyanabból a CPUID-bitből (`0x00bf6019`, `0x00bf603a`).
⇒ A vektoros út **lefelé kerekítő** `divps`-szel és `cvtps2dq`-val fut.

**Mérés (unicorn-emulátor, `eszkozok/nativ_emu/simd_verify.py` a privát
repóban):** a #3474 esetkészlete + kettő-hatvány és páratlan méretű esetek
(39 eset: téglalap, zaj, 223×211-es kép; sugár −2…300; `quality` 0…15),
mindhárom nem-nulla jelzőállásban, a futtatókönyvtár SSE2-jelzőjével és az
MXCSR-betöltő (`0x00c1344f`) horoggal: **0 eltérő bájt** a skalár úthoz
képest, és a skalár út **0 eltérő bájt** a `render/nativ_blur.py`-hoz. Mind
a négy vektoros menetfüggvény (`0x00bc6920`, `0x00bc7300`, `0x00bc6f30`,
`0x00bc6b60`) és a diszpécser négy vektoros változata (`0x00bc5a10`,
`0x00bc5cf0`, `0x00bc5fd0`, `0x00bc62b0`) lefutott; az MXCSR-írások `0x2000` (lefelé) és vissza.

⚠️ **Kontroll — miért kell a futtatókönyvtár állapota:** ha a `0x00da1428`
0 marad (indítás nélküli emulátor), a `_controlfp` nem ír MXCSR-t, a
`divps`/`cvtps2dq` a legközelebbire kerekít, és a vektoros út menetenként
legfeljebb +1-gyel, hat menet után +4-gyel tér el (39 esetben 878 059 bájt).
Ez **az emulátor hiánya volt, nem a Picasa viselkedése**; a kerekítő
változat csak akkor volna valós, ha a futtatókönyvtár nem észlelné az
SSE2-t — akkor viszont a `0x00c33d30` sem kapcsolná be a vektoros utat.

⇒ **A mi `render/nativ_blur.py`-unk a valódi gépen futó ágat is bitre
követi; nincs teendő.**

*Bizonyítottsági fok: **megerősített** — utasításszintű kiolvasás
(elágazás, CPUID-bit, `_controlfp`-tábla, MXCSR-út) és emulátoros mérés
39 × 3 esetben. A valódi CPU és az unicorn `divps`-e közti egyezést nem
mértem külön; a lefelé kerekítés mellett a hányados csonkolt egész része
mindkettőn IEEE-szerinti.*

## ⛳ A `TiledImageMask` mind a tizenkét TARTALÉKÉRTÉKE — `alphaMax = 1,0`, `alphaMin = 0,0` (2026-09-18, 320. kör, #2476)

*A 2026-09-12-i kör kimérte, hogy a pont profilja **lineáris radiális rámpa**
(két megálló, küszöb és felül-mintavételezés nélkül), és egy dolgot hagyott
nyitva: a rámpa **végpontjait** — az `alphaMax`-ot és a négy `padding`-et. Ez
a szakasz azokat adja meg.*

### Független helyi ellenőrzés (2026-09-18)

A leletet a helyi, indexelt binárison újraellenőriztem; a vizsgált
`Picasa3.exe` SHA-256-a `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az index RTTI-táblája a `glimmer::TiledImageMask::vftable` címet
`0x00cf02e8`-ként, a hozzá tartozó attribútum-olvasót
`FUN_00bba2e0`-ként (481 bájt) adja. Ennek string-xrefjei egymás után
azonosítják a teljes 12-es készletet: `tileWidth`, `tileHeight`,
`scaleWidth`, `scaleHeight`, `paddingLeft`, `paddingTop`, `paddingRight`,
`paddingBottom`, `offsetX`, `offsetY`, `alphaMin`, `alphaMax`.

A célzott diszasszemblálás három, egymástól független ponton egyezik:

- `FUN_00bba250` a `0x00c7dbc4`-ről betöltött `0,8`-at mindkét skála-mezőbe
  írja, `fldz`-zel nullázza az alfa-minimumot, `fld1`-gyel 1,0-ra állítja az
  alfa-maximumot, és nullázza a négy padding-mezőt;
- `FUN_00bbaa90` a két skála-mezővel külön-külön megszorozza a belső
  téglalap két tengelyét, az alfa-mezőket pedig a két megálló végpontjaiként
  használja;
- ugyanott a pozíciók `0x00` és `0xff`, a megállószám átadása
  `0x00bbacba: push 2`, majd a `0x008f3970` hívása. Ez lineáris radiális
  rámpát bizonyít, külön perem-sáv és külön élsimítási kapcsoló nélkül.

A mai kód kontrollja ugyanebben a munkafában: a célzott
`tests/render/test_comicize_569.py` futása **39 passed in 2,61 s**; a forrás
`DOT_SCALE = 0,8`, `_EDGE_SOFTNESS_PX = 1,0`, és az
`apply_comicize()` továbbra is a `halftone_branch()`-en át modulálja a pont
sugarát. Ez a teszt a jelenlegi implementációt ellenőrzi, nem natív
pixelazonossági goldent.

⚠️ **Helyesbítés (2026-09-19, #2476):** a „terméki átvezetés külön fejlesztési
munka" állítás elavult. A fenti rámpa a tónussal KÜSZÖBÖLVE pontosan a
`halftone_branch()` `0,8 · (1 − tónus)` sugarát adja (mind a 256 tónuson 0
eltérő képpont, elhangolt skálájú kontrollal 105 536) — a render-láncban nincs
mit átvezetni. Ami maradt, az a küszöb fedettségi profilja: **#3390**. Mérés:
`filters-decoded.md`, „A Comicize pontja: az ÁLLANDÓ maszk és a tónussal növő
sugár UGYANAZ"; őr: `tests/render/test_comicize_maszk_kuszob_2476.py`.

### A Tiled-művelet paraméterépítőjének alapértékei: `0x00bba250` (133 b)

A `0x00bba250` nem a műveletobjektum konstruktora: a Tiled-végrehajtás
paraméterrekordjához készít elő helyi alapértékeket. A tényleges objektumot a
gyár (`0x00bb31f0`) a `0x00bb9fd0` konstruktorral inicializálja; az
attribútumolvasó (`0x00bba2e0`) a megtalált csomópontokat az objektum
`+0x18`, `+0x20`, …, `+0x70` mezőibe teszi. A lenti eltolások a
paraméterrekord mezői, nem az objektumtagok:

| attribútum | paramétermező | **végrehajtói tartalékérték** | alapérték-képzés |
|---|---|---:|---|
| `tileWidth` | `+0x08` | **0** | `0x00bba281` |
| `tileHeight` | `+0x0c` | **0** | `0x00bba287` |
| **`scaleWidth`** | `+0x10` | **0,8** | `0x00bba261` |
| **`scaleHeight`** | `+0x14` | **0,8** | `0x00bba266` |
| `paddingLeft` | `+0x18` | **0** | `0x00bba28f` |
| `paddingTop` | `+0x1c` | **0** | `0x00bba293` |
| `paddingRight` | `+0x20` | **0** | `0x00bba297` |
| `paddingBottom` | `+0x24` | **0** | `0x00bba29b` |
| `offsetX` | `+0x28` | **0,0** | `0x00bba270` |
| `offsetY` | `+0x2c` | **0,0** | `0x00bba275` |
| **`alphaMin`** | `+0x30` | **0,0** | `0x00bba27d` |
| **`alphaMax`** | `+0x34` | **1,0** | `0x00bba28b` (`fld1`) |

A `0,8` a `0x00c7dbc4`-en álló `float` (kiolvasva: **0,800000011920929**), és a
paraméterépítő **ugyanazt az FPU-értéket** teszi mindkét skálamezőbe
(`fst` + `fstp`).

⭐ **Ez a mérés kontrollja:** a `scaleWidth`/`scaleHeight` = **0,8** az az
érték, amit a jegy és a termékkódunk (`render/halftone.py`, `DOT_SCALE`) már
tudott, és **pontosan azokon az eltolásokon** (`+0x10`/`+0x14`), amelyeket a
kódunk megjegyzése megnevez. Ha a struktúra-illesztésem hibás volna, ez nem
jönne ki.

### Amit ez a pont PROFILJÁRÓL kimond

A 2026-09-12-i mérés szerint a csemperajzoló **két megállót** ad át
(`0x00bbacba push 2`): a közép alfája `CSONK(alphaMax · 255)`, a szél alfája
`CSONK(alphaMin · 255)`. A most kiolvasott tartalékértékekkel, és mivel a
szállított `filterdesc.xml` két `TiledImageMask` példánya (`_mskColorSpots1/2`)
**egyiken sem adja meg** ezeket:

```
kozep  = TRUNC(1,0 · 255) = 255      (teljesen átlátszatlan)
szel   = TRUNC(0,0 · 255) =   0      (teljesen átlátszó)
```

⇒ **a pont TELJES kiterjedésében lineáris rámpa fut 255-től 0-ig** — nincs
külön „élsimítási sáv", és nincs kemény mag sem. A `padding*` mind **0**,
tehát a rámpa a csempe teljes, `0,8`-cal skálázott befoglalóját használja.

### ⛔ Amit ez a termékkódunkról mond

A `render/halftone.py:40` egy **kimondottan tippelt** értéket tart:

> *„A natív maszk antialiasingjának PONTOS alakja … az egyetlen nyitott
> részlet … Egy pixelnyi lineáris átmenet a szokásos"* → `_EDGE_SOFTNESS_PX = 1.0`

| | eredeti (mérve) | nálunk (ma) |
|---|---|---|
| a pont belseje | **lineáris rámpa 255 → 0 a teljes sugáron** | kemény mag |
| a perem | *nincs külön perem* | 1 képpontos lágyítás (tipp) |
| `alphaMax` / `alphaMin` | **1,0 / 0,0** | — |
| `padding*` | **mind 0** | — |

⇒ a javítás nem a perem szélességének finomítása, hanem a **maszk alakjának**
cseréje: kemény mag + 1 px perem helyett **egyetlen lineáris rámpa**. Ez
mérhető a `research/comicize-sweep/` 15 exportján a #1606 raszter-amplitúdó
módszerével — és irányában is egyezik a mért hibával (a mi profilunk „fennsík
nélkül monoton lejt", a referencia fennsíkos, ld. a 00-index 2026-09-05-i
bejegyzését).

*Forrás: `0x00bba250` (a paraméterépítő, 133 b) — az alapértékek `0x00bba261`,
`0x00bba266`, `0x00bba270`, `0x00bba275`, `0x00bba27d`, `0x00bba281`,
`0x00bba285` (`fld1`), `0x00bba287`, `0x00bba28b`, `0x00bba28f`,
`0x00bba293`, `0x00bba297`, `0x00bba29b`; a `0,8` konstans `0x00c7dbc4`; a
mezősorrend a beolvasóból (`0x00bba2e0`, 481 b).*

## ⛳ Az `AdjustCurves` ponttárolója és természetes spline-cache-e (2026-09-18, #626)

*A kör pontos kérdése az volt, hogyan kapcsolódik össze a négy görbe
paraméter-előkészítése, a ponttárolás és a már ismert természetes spline.
A válasz a binárisban egyetlen, visszakövethető lánc: négy 24 bájtos leíró →
8 bájtos `(x, y)` pontpárok → másodderivált-cache → 256 elemű LUT.*

### A négy leíróból a pontpárokig

A `AdjustCurvesImageOperation` 8. slotja (`FUN_00bb9d20`, **RVA
`0x007b9d20`, 224 bájt**) a négy görbetagot (`+0x40`, `+0x44`, `+0x48`,
`+0x4c`) külön, **24 bájtos lépésközű** helyi leíróba küldi a
`FUN_00bb9e00`-t (RVA `0x007b9e00`, **438 bájt**). A négy leíró sorrendje a
már lezárt attribútumtérkép szerint: `MasterCurve`, `RedCurve`, `GreenCurve`,
`BlueCurve`.

A `FUN_00bb9e00` a görbepont-vektort bejárja, a két numerikus pontértéket
kiolvassa, majd a `FUN_008f2c70`-vel tárolja. Az xref-index ezt a hívási láncot
függetlenül adja vissza:

```text
0x00bb9d20 → 0x00bb9e00  (4 hívás)
0x00bb9e00 → 0x008f2c70 (1 hívási hely, a pontbejárás törzsében)
```

A ponttároló (`FUN_008f2c70`, **RVA `0x004f2c70`, 299 bájt**) rekordja:

| mező | jelentés | bináris bizonyíték |
|---|---|---|
| `+0x00` | ponttömb mutatója; rekordonként 8 bájt | a célcím `bázis + index × 8` |
| `+0x04` | darabszám és alacsony flag-bit | `>> 1` = darabszám; íráskor `+2` |
| `+0x08` | a természetes spline másodderivált-tömbje | a fogyasztó `FUN_008f3290` innen olvas |
| `+0x0c` | a másodderivált-tömb darabszáma és flagje | a fogyasztó ezt ellenőrzi |
| `+0x10` | második gyorsítótár-rekesz mutatója | a pontbeszúrás érvényteleníti |
| `+0x14` | a második gyorsítótár-rekesz darabszáma és flagje | a pontbeszúrás érvényteleníti |

Új pont után a bináris **mindkét** cache-rekeszt felszabadítja és nullázza;
az append tehát nem hagyhat régi másodderiváltat az új pontkészlet mellett.
A második cache fogyasztóját ebben a körben nem azonosítottam — nem nevezem
meg találgatásból.

### A kiértékelés és a cache újraépítése

A `FUN_008f3290` (**RVA `0x004f3290`, 280 bájt**) a `[+0x00]` ponttömbön
**bináris kereséssel** választja ki azt a szakaszt, amelyre `x[j] ≤ x <
x[j+1]`. A `[+0x08]` tömb hiányzó vagy érvénytelen cache-e esetén meghívja a
`FUN_008f33b0`-t (**RVA `0x004f33b0`, 836 bájt). Ez a klasszikus
tridiagonális megoldást futtatja:

- a munkatömb első eleme és a `y2[0]` nulla;
- a belső pontokra `σ = (x[j]−x[j−1])/(x[j+1]−x[j−1])`, `p = σ·y2[j−1]+2`;
- a jobb oldalban a két szomszédos szakasz meredekségkülönbsége szerepel, `6`
  szorzóval;
- a visszahelyettesítés után `y2[n−1] = 0`.

Ez nem pusztán „spline-szerű" leírás: a természetes peremfeltételt és a
`2`/`6` konstansokat a konkrét függvény adja.

A szakaszban a natív képlet:

```text
h = x[j+1] − x[j]
A = (x[j+1] − x) / h
B = (x − x[j]) / h
y = A·y[j] + B·y[j+1]
   + ((A³−A)·y2[j] + (B³−B)·y2[j+1]) · h² / 6
```

A `FUN_008f3290` törzsében nincs külön határon kívüli clamp-ág; a
Picasa-szállításban használt görbék végpontjainak és a 0…255 LUT-tartomány
hatásának teljes, golden-alapú összevetése **NINCS MEG**. A jelenlegi
`curve_lut()` (`src/picasapy/render/curves.py:57–111`) a tartományon kívül a
szélső értéket tartja — ez terméki policy, nem a most kiolvasott natív ág
bizonyítéka.

### Eredeti / nálunk / teendő

| | Eredeti, mérve | PicasaPy, mérve | Teendő |
|---|---|---|---|
| görbepont-tárolás | 8 bájtos `(x,y)` rekord, `FUN_008f2c70` | `CurvePoints` és `curve_lut()` | nincs tárolási kompatibilitási feladat a jelenlegi render API-ban |
| spline | természetes köbös, `FUN_008f3290` + `FUN_008f33b0` | `_natural_spline_second_derivatives()` + vektorizált kiértékelés | a mechanizmus egyezik |
| csatornaösszetétel | master után R/G/B, a közös LUT-építőben (`FUN_00bcd1e0`, RVA `0x007cd1e0`, 376 bájt) | `adjust_curves()`: master LUT, majd csatorna-LUT-ok (`glimmer_ops.py:125–148`) | a sorrend egyezik |
| cache-életciklus | pontbeszúráskor két cache invalidálódik | a tiszta LUT-függvény nem hordoz natív cache-t | nincs pixelhatásra vonatkozó mérés; külön teljesítményfeladat csak mérés után indokolt |

**Bizonyítottsági fok: megerősített** a pontrekord, a cache-invalidálás, a
természetes spline és a LUT-lánc mechanizmusára. **NINCS MEG** a natív és a
PicasaPy közötti pixelazonosság golden-mérése a cache-hatékonyság és a
határon kívüli görbepontok esetére; ezek hatását nem tulajdonítom a
mechanizmusleletnek.

**Nyitott kérdések mérlege — e kör saját kérdései:** 0 nyílt · 1 lezárva ·
0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva". Az örökölt pixel-golden
mérés külön, nem átadott mechanizmus-kérdés.

*Forrás: `picasa3-index.sqlite` `functions`/`xrefs` táblák; a célzott
Ghidra-kimenet `FUN_00bb9d20`, `FUN_00bb9e00`, `FUN_008f2c70`,
`FUN_008f3290`, `FUN_008f33b0`, `FUN_00bcd1e0`; a kapcsolódó mai kód
`src/picasapy/render/curves.py:26–111`,
`src/picasapy/render/glimmer_ops.py:125–148`,
`tests/render/test_curves_spline_629.py:28–145`.*


## ⛳ Az `AdjustCurves` görbe-lánca: a mester-érték NEM kerekül és NEM vágódik, a spline a töréspontokon túl EXTRAPOLÁL (2026-09-29, 406. kör, #3941)

*Bizonyítottsági fok: **megerősített**, utasításszinten, és a Picasa-exporttal bitre egyezik. Független újralevezetés (#3941): EGYEZIK, ugyanazokkal a táblaértékekkel. A fenti 4.8 kompozíciós sorrendje áll; a köztes érték és a tartományon kívüli viselkedés eddig nem volt kiolvasva.*

A LUT-építő (`0x00bcd1e0`) mind a 256 bemenetre EGY menetben:

```
v   = f32( Master(i) )                      ; 0x00bcd226 → 0x00bcd360, NINCS kerekítés, NINCS vágás
R_i = clamp( trunc( Red(v)   + 0,5 ), 0, 255 )   ; 0x00bcd23a, 0x00bcd25b–0x00bcd270, [0xc72150] = 0,5
G_i = clamp( trunc( Green(v) + 0,5 ), 0, 255 )
B_i = clamp( trunc( Blue(v)  + 0,5 ), 0, 255 )   ; 0x00bcd282–0x00bcd28d
```

- **A görbe-kiértékelő** (`0x008f3290`) a Numerical Recipes `splint` alakja felezéses intervallum-kereséssel (`0x008f32e4`–`0x008f331a`). A töréspontokon **kívüli** bemenetre a szélső intervallumot adja, és annak köbös polinomját **extrapolálja** — nem vág és nem tartja a szélső értéket. Kettőnél kevesebb pontnál a bemenetet adja vissza (`0x008f329e`, identitás).
- **A mester-kiértékelő** (`0x00bcd360`): `y₀ = x`, `y_{k+1} = f(y_k)` összesen `n` lépésben, az eredmény `y_n + s · (f(y_n) − y_n)` (`0x00bcd364`–`0x00bcd396`), ahol `n = [+0x60]`, `s = [+0x64]`. A készlet konstruktora (`0x00bcd180`) `n = 1`-et és `s = 0`-t állít be, tehát alapesetben `v = f(x)`. Az `n`-t és az `s`-t csak az `ExposureAdjust` attribútum írja át (`0x00bcd4b0`: `n = trunc(|p|)`, `s = |p| − n`); a görbe-XML nem.
- **Üres görbe:** a kiértékelő a bemenetet adja vissza (identitás, `0x008f3295`–`0x008f32a8`).

**Hatókörön kívül** (egyik effekt sem használja, a `filterdesc.xml` 12 `AdjustCurves`-sorából egyik sem ad `ExposureAdjust`-ot, és mindegyikben van görbe): a négy üres görbe esete (az építő ekkor egy elemet sem ír, `0x00bcd202`) és az `ExposureAdjust` + `MasterCurve` együttes megadása.

**Példa — a 60-as évek kék csatornája** (Master `(0,0),(150,104),(243,255)`, Blue `(0,9),(126,98),(255,231)`):

| `i` | `v = Master(i)` | natív `B` | a mai kód |
|---:|---:|---:|---:|
| 240 | 249,6 | 225 | 225 |
| 245 | 258,6 | 235 | 231 |
| 250 | 267,6 | 245 | 231 |
| 255 | 276,6 | 255 | 231 |

**Mérve** (684-es mérőkészlet, a mi kimenetünket a Picasa-export saját kvantálótábláival tömörítve; minden golden-pár lefutott, csak a változók):

| eset | a mai kód (két LUT, köztes kerekítés és vágás, szélső érték tartva) | **natív lánc** |
|---|---:|---:|
| `sixties__min` | 0,433 | **0,000** |
| `sixties__alap` | 0,376 | **0,000** |
| `cinemascope__alap` | 0,354 | **0,079** |

A többi görbés effekt (kétpontos vagy tartományon belüli görbék) nem változik.

**Nálunk** (`render/glimmer_ops.py::adjust_curves`, `render/curves.py::curve_lut`): két egymás utáni 8 bites LUT, a görbe a tartományon kívül a szélső értéket tartja → fejlesztés: #3942.

✅ **Megvalósítva (#3942).** Az `adjust_curves` a natív egy-menetes képletre állt (`curves.evaluate_curve_extrapolated`, csak ezt az utat használja); a `curve_lut` (256 elemű, 0..255 indexű LUT) MINDEN MÁS hívónál változatlan — a tartományon kívül továbbra is a szélső értéket tartja, mert azoknak a töréspontjai a teljes 0..255 tartományt lefedik. Mérve (684-es kvantálótáblás ΔE):

| eset | előtte | utána |
|---|---:|---:|
| `sixties__min` | 0,433 | **0,000** |
| `sixties__alap` | 0,376 | **0,000** |
| `cinemascope__alap` | 0,354 | **0,079** |

A többi görbés effekt (`crossprocess`, `orton`, `pencilsketch`, `neon`, `reanimatedeyecolor`) ΔE-je nem romlott. A tábla bitre azonos maradt a régi és az új lánccal, kivéve az `orton` `brightness≠50` állásait: `brightness=25`-nél (`mid = 90,5`) 3 táblaelem 1 szinttel eltér — a `trunc(x + 0,5)` kerekítés a ,5-ös döntetlent felfelé viszi, a régi `rint` párosra —, a spec szerinti irányba (a `brightness=50` alapállás azonos).

## ⛳ A `Border` négy attribútumának EGYSÉGE — és a rejtett átméretezési tényező (2026-09-19, 325. kör, #626)

*A jegy 3. prioritása a `Border` (Border · MuseumMatte · RoundedEdges ·
Sixties). A kimeneti méret és a tageltolások korábban megvoltak; itt a
rajzolási lánc és az egységek jönnek.*

### A) A lánc — három függvény, mindegyiknek EGY hívója

```
0x00bbe320 (266 b, 6. rés = alkalmazó)
   ├── 0x00bbe430 (317 b)   ← a két VASTAGSÁG + a feliratsáv beolvasása
   └── 0x00bbe570 (1953 b)  ← a munkavégző (egyetlen hívója a fenti)
         ├── 0x00aa13b0 (1153 b, 6 hívó)   vászon-primitív
         ├── 0x00aa1840 (813 b, 7 hívó)    rajzoló-primitív
         ├── 0x009ab360 (176 b, EGYETLEN hívója ez)  ← csak a Borderé
         └── 0x008f4c80 (247 b, 4 hívó; a másik három a `0x00bd0f10`,
             `0x00bd1350`, `0x00bd1730` szűrő-támogató)
```

A `Border`-nek a 4.5 táblázatban nincs 8. rése — a rajzolás tehát **ebben a
láncban** történik, nem külön munkavégzőben.

### B) A színek: `double` attribútum, előjel-helyreállítással

Mindkét szín a `0x8ef520` → `0x8eea90` páron jön be `double`-ként, és ha az
érték **negatív**, a kód hozzáadja a `0x00cf39e4`-en álló `float`
konstanst — az értéke **2³² = 4 294 967 296**:

```
0x00bbe6d4  test eax, eax
0x00bbe6db  jge  …
0x00bbe6dd  fadd dword ptr [0xcf39e4]      ; + 2^32
```

⇒ ez nem paraméter, hanem **előjeles → előjel nélküli** helyreállítás: a
`0xff000000 + szín` alakú leíró-kifejezés `double`-ben negatívként jelenik
meg, és így lesz belőle újra ARGB. (A leíró tényleg így ír:
`outercolor="{0xff000000 + _cpkrOuter.liveColor}"`.)

### C) ⭐ A két VASTAGSÁG át van skálázva — a `captionheight` és a `cornerradius` NEM

A `0x00bbe430` először **kikeresi az `imageWidth` változót** a szűrő
változó-táblájából (a kulcs-sztring a `0x00cc44f8`-on: `imageWidth`; a
szomszédai `imageHeight`, `outputIndex`), majd elosztja a méret-rekord egy
egész mezőjével, és az így kapott **tényezővel szoroz**:

```
0x00bbe4a6  fild dword ptr [esi + 8]       ; a méret-rekord egész mezője
0x00bbe4b0  fdivr qword ptr [esp + 0x14]   ; imageWidth / ez  → tényező
0x00bbe4bd  call 0x8f1490                  ; innerthickness beolvasása
0x00bbe4d0  fmul dword ptr [esp + 0xc]     ; ← SKÁLÁZÁS
0x00bbe508  lea  ecx, [ebx + 0x44]         ; outerthickness
0x00bbe51b  fmul dword ptr [esp + 0xc]     ; ← SKÁLÁZÁS
0x00bbe553  call 0x8f1490                  ; captionheight — ⛔ NINCS fmul
```

A `cornerradius`-t nem is ez a segítő olvassa, hanem maga az alkalmazó
(`0x00bbe3b8`), szintén **szorzás nélkül**. Mindegyik érték `fldcw`-vel
váltott kerekítési módban megy `int`-be (csonkítás).

**Független megerősítés a szállított leíróból** — a csúszkák deklarációja
maga mondja meg az egységet:

| attribútum | csúszka tartománya | alap | ⇒ egység |
|---|---|---:|---|
| `outerthickness` | 0 … **100** | 20 | a **kép pixelében**, átméretezve (C) |
| `innerthickness` | 0 … **100** | 5 | ugyanaz |
| `cornerradius` | 0 … `min(imagewidth, imageheight)/2` | 0 | **képpont**, nyersen |
| `captionheight` | 0 … `imageheight/6` | 0 | **képpont**, nyersen |

A két „pixel" tartomány kép-méretből származik, a két vastagságé fix 0–100 —
és pontosan a két utóbbi az, amit a bináris átskáláz. **A két forrás
egymástól függetlenül ugyanazt adja.**

### D) Miért nem mond ez ellent a #317 exportjainak

A `render/glimmer_frame_ops.py` `add_ring()` megjegyzése hét valódi
MuseumMatte-exportra hivatkozik, amelyeken az oldalankénti ráadás **pontosan
`Outer + Inner` képpont** volt (0/50/100 külső, 0/100 belső állásokon). Ez
**összhangban van** a fentiekkel: teljes felbontású kimenetnél a C) pont
tényezője **1**, tehát a szorzás nem látszik. A tényező akkor tér el 1-től,
amikor a művelet **nem teljes felbontású** vásznon fut (előnézet, nagyítás).

⇒ Ebből egy **mérhető aszimmetria** következik: előnézeten a keret vastagsága
a vászonhoz skálázódik, a **feliratsáv és a sarok-lekerekítés viszont nem**.

### E) A korábbi iránykérdés — LEZÁRVA az F) szakaszban

~~A tényező iránya (`imageWidth / vászonszélesség` vagy fordítva) nyitott
kérdés volt: a méret-rekord (`[esi + 8]`, `[esi + 0xc]`) a vászon vagy az
eredeti méretét tartja.~~

Az F) szakasz ezt a kérdést a Crop-kontrollal és a változóasztal
argumentumláncával lezárta: a rekord a `fullResImageWidth` /
`fullResImageHeight` pár, a tényező pedig **`imageWidth /
fullResImageWidth`**. A korábbi nyitott kérdés ezért nem új kutatási tétel.
*(Fejlesztői oldal: **#3377**.)*

*A lezáró bizonyíték forrása: `0x00bbe320`, `0x00bbe430`, `0x00bbe570`,
`0x00bbdbd0`, `0x008e38a0` és az F) szakaszban felsorolt kulcs-/konstans-
címek.*

### F) ⭐ A skálázási tényező iránya — a második argumentum teljes felbontású rekordja (2026-09-19, #626)

A korábbi rés nyitva hagyta, hogy a `0x00bbe4b0` által képzett arány
`imageWidth / [esi+8]` a munkavászonhoz vagy annak reciprokához igazodik-e.
A kérdést a Crop-kontroll és a Glimmer-változóasztal közös argumentumlánca
méri ki; nem goldenből és nem feltételezésből.

#### 1. A műveleti argumentumok azonosítása

Az `ApplyInstruction` (`0x00bd0cc0`, az RTTI-vtábla `0x008f0f18` negyedik
slotja) a 40 bájtos verem legfelső rekordját adja az alkalmazónak első
argumentumként (`0x00bd0d41`), a hívó kontextusát második argumentumként
(`0x00bd0d3d`), és az új kimeneti rekordot harmadikként (`0x00bd0d3c`).

A `CropImageOperation` alkalmazója (`0x00bbdbd0`) az első argumentum
`+0x08`/`+0x0c` mezőjét olvassa (`0x00bbdc27`, `0x00bbdc34`), majd ezt a
40 bájtos képreceptort másolja a harmadik argumentumba (`0x009a8ca0`, hívás:
`0x00bbdc99`). Ez a pozitív kontroll: az első argumentum a pillanatnyi
munkakép rekordja, a harmadik a létrehozandó kimeneti rekord.

A `Border` alkalmazója (`0x00bbe320`) a második argumentum `+4`-ére mutató
kontextust tartja meg (`0x00bbe32b`, `0x00bbe338`); a `0x00bbe430` ebből az
`esi` rekordból olvassa a két méretmezőt (`0x00bbe4a6`, `0x00bbe4af`).

#### 2. A `+8/+0c` rekord szerepe

A változóasztal felépítője (`0x008e38a0`) a bemeneti méretpár két egészét a
kontextus `+0x08` és `+0x0c` mezőjébe másolja (`0x008e38ad`, `0x008e38b5`),
és ugyanebben az ágban a `fullResImageWidth` / `fullResImageHeight`
kulcsokat regisztrálja (`0x00cd0270`, `0x00cd0284`). Az `imageWidth` és
`imageHeight` külön kulcsfeloldó ágon szerepel (`0x008e45b0`, kulcsok:
`0x00cc44f8`, `0x00cc44ec`), vagyis a Border nevezője nem az aktuális
munkakép `+8/+0c` rekordja, hanem a teljes felbontás párja.

A Border utasításszintű aritmetikája ezért pontosan ez:

```text
skálázási tényező = imageWidth / fullResImageWidth
innerthickness'   = csonk(innerthickness × tényező)
outerthickness'   = csonk(outerthickness × tényező)
```

A fordított `fullResImageWidth / imageWidth` olvasatot a `0x00bbe4a6`
`fild [esi+8]` → `0x00bbe4b0` `fdivr` sorrendje kizárja. A magassági pár
ugyanezt a kontextust hordozza (`+0x0c`), bár a Border saját tényezője a
szélességből készül.

#### 3. Eredeti / nálunk / teendő

| | Eredeti, mérve | PicasaPy, mérve | Teendő |
|---|---|---|---|
| Border vastagság skálája | `imageWidth / fullResImageWidth`, `0x00bbe4a6`–`0x00bbe4b0`; a két `fmul` `0x00bbe4d0` és `0x00bbe51b` | `glimmer_frame_ops.py:102–118`: a `draw_border` a kapott vastagságokat közvetlenül adja át az `add_ring`-nek; nincs teljes felbontású tényező | külön fejlesztői jegy: **#3377** |
| captionheight / cornerradius | nyers képpont, nincs `fmul` (`0x00bbe553`, illetve `0x00bbe3b8`) | közvetlen képpont-paraméter | #3377-ben kezelendő |
| natív–PicasaPy exportpár | a 684-es `border__alap` és `border__max` Picasa-exportja | a `PicasaPy_meroszett/export-202608151229` megfelelő exportjai; azonos méret (1010×690, illetve 1360×1103) | mérve; a JPEG-ek nem bájtra azonosak |

**Bizonyítottsági fok: megerősített** a tényező irányára és a rekord
szerepére (SQLite RTTI/string/xref + célzott x86-diszasszemblálás).
A 684-es mérőkészlet Border-exportpárja megvan; annak keretsáv-összevetését
és a natív munkavégző közvetlen QEMU-pixelmintáját az alábbi szakasz rögzíti.

**Nyitott kérdések mérlege — e kör saját kérdései:** 0 nyílt · 1 lezárva ·
0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”. A #626 gyűjtőjegy nyitva
marad: a Rotate, Crop, SimpleBorder és az alkalmazási lánc további részei
külön kutatási tételek.

### A `Border` rajzolója (`0x00bbe570`) — méret, koncentrikus sarkok, ARGB-keverés (2026-10-04, #626)

Ez a szakasz a 4.12/F-ben már ismert vastagság-skálázás utáni munkavégzőt
zárja le. Az utasítások forrása `0x00bbe570` (1953 bájt), a képpont- és
fedettség-rutinoké `0x00aa13b0` (1153 bájt), illetve `0x00aa1840` (813 bájt).
Az eredeti függvény közvetlen futtatásához kézzel összeállított ARGB-képet
kapott a `qemu-i386`; a futás stubbelt importokat és bump-allokátort használ,
nem a valódi `filterdesc`-futtatást.

#### 1. Kimeneti méret és sávok

Legyen `T = innerthickness + outerthickness`, a már egészre alakított
pixelvastagságok összege. A munkavégző a forrás `W×H` méretéből ezt állítja
elő:

```text
W' = W + 2·T
H' = H + 2·T + captionheight
```

Az `0x00bbe576`–`0x00bbe5a8` sorozat összeadja az 5. és 6. stack-argumentumot,
kétszerezi, hozzáadja a forrás `+8/+0c` méretét, majd a 7. argumentumot csak a
magassághoz adja. A QEMU-aszimmetria-kontrollban a 3×2 forrás, `inner=1`,
`outer=2`, `caption=0` eredménye **9×8**; a felső és bal külső sáv 2 pixel,
a belső sáv 1 pixel. A 0 caption mellett a címkézett mérőkészlet
`Border=1,100,100,40,…,60` Picasa-exportja 960×640-ről 1360×1103-ra nőtt;
ez a korábbi §4.12/F mérésével egyezik.

#### 2. A kitöltés és a sarkok

- A kimeneti vászon először a megadott külső ARGB-színt kapja. A belső
  színű sáv erre kerül rá; a forráskép a `T` eltolással kerül a közepére.
- A belső sáv külső pereme `R + innerthickness` sugarú lekerekített
  téglalap; a forrásképet külön, `R` sugarú lekerekített maszk vágja.
  Ezt az `0x00bbe570` `0x00aa1840`-et hívó útja és a 5×5, `R=2`,
  `inner=outer=1` QEMU-minta együtt mutatja: a két külön ív közti sáv az
  inner színű marad.
- A vízszintes és függőleges egyenes sávokon a szín fedése egységes.
  A kerekített ív képpontjain viszont vannak köztes színek: a natív rajzoló
  **élsimít**, nem bináris „pixel bent/kint” maszkkal dolgozik.

#### 3. ARGB egészkeverés

Az `0x00aa13b0` teljes fedésű ága (`0x00aa1ae3`–`0x00aa1b1f`) a cél dword
négy byte-ját külön 8 bites fixpontos szorzással skálázza, majd a forrás
ARGB-dwordot **egyetlen 32 bites összeadásban** hozzáadja. `A = source >> 24`
esetén:

```text
inverse = 256 − A
scaled_destination[i] = floor(destination[i] × inverse / 256)  # i: mind a 4 byte
result_dword = scaled_destination_dword + source_argb_dword
```

A végső dword-összeadás **nem telít byte-onként**: a byte-határt átlépő
összeg átvitele a következő byte-ba jut. Ez nem szokásos, csatornánként
clampelt alpha-over képlet. A futtatásos cáfoló kontrollban
`outer=0x80ff0000`, `inner=0x40ff0000` mellett a belső sáv pixele
`0xa1be0000`: a vörös byte `0xbf + 0xff` összege `0x1be`, az átvitel az
alfa byte-ot `0xa0`-ról `0xa1`-re növeli. Az alfa 0 esetén a futtatott minta
nem módosította a vászon külső színét.

Részleges fedésnél az `0x00aa1a74`–`0x00aa1b1f` út külön 16.16-os szorzatból
képzi a fedési tényezőt `C`, abból `floor(A×C/256)`-ot számít, majd a cél és
a forrás byte-jait külön szorozza és a csatornákat packed dwordként adja
össze. Az `0x00aa1840` állítja elő a görbe menti per-pixel `C`-t. A helyi
diszasszemblálásból és a mintafutásokból **nem lett lezárva a C(x,y,R) teljes
általános képlete**, ezért a konkrét köztes pixelek mért értékei nem
általánosíthatók minden sugárra.

#### 4. Bájtra rögzített natív próba

Kézzel megadott 5×5-ös, egyszínű `0xff204060` forrás; külső szín `0xff000000`,
belső `0xffffffff`, `R=2`, mindkét vastagság 1, caption 0. A natív kimeneti
rekord 9×9, stride 9, a visszaírt pixelek (ARGB hex, soronként):

```text
ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
ff000000 ffb4b4b4 ffffffff ffffffff ffffffff ffffffff ffffffff ffa6a6a6 ff000000
ff000000 ffffffff ff6b8095 ff204060 ff204060 ff204060 ff798c9f ffffffff ff000000
ff000000 ffffffff ff204060 ff204060 ff204060 ff204060 ff2e4c6a ffffffff ff000000
ff000000 ffffffff ff204060 ff204060 ff204060 ff204060 ff204060 ffffffff ff000000
ff000000 ffffffff ff6b8095 ff204060 ff204060 ff204060 ff798c9f ffffffff ff000000
ff000000 ffb4b4b4 ffffffff ffbac4ce ff204060 ffbfc8d1 ffffffff ffa6a6a6 ff000000
ff000000 ff000000 ff868686 ffd9d9d9 ffffffff ffd6d6d6 ff7e7e7e ff000000 ff000000
ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
```

Ugyanennek a forrásnak a `draw_border()`-rel előállított PicasaPy RGB-képe
9×9; a natív RGB-részhez képest **29/81 pixel** eltér, az RGB-csatorna-MAE
20,506, a maximum 180. Például natív `(y=1,x=1)=180,180,180`, PicasaPy
`0,0,0`; natív `(1,2)=255,255,255`, PicasaPy `143,143,143`. A forráskód
`_sarok_fedes()`-e 4×4 almintát és `numpy.rint`-et használ, a natív út
`0x00aa1840`/`0x00aa13b0` fixpontos fedettségszámítását és packed ARGB
keverését nem.

#### 5. Export-összevetés és fok

A kibontott `684-merokeszlet` és `PicasaPy meroszett/export-202608151229`
JPEG-exportok mérete mindkét beállításnál egyezik. Csak a keretsávokon
mérve:

| export | keretsáv MAE / csatorna | 95. percentilis | 20-nál nagyobb pixelkülönbség | maximum |
|---|---:|---:|---:|---:|
| `border__alap`, 1010×690 | 0,109632 | 1 | 0 | 20 |
| `border__max`, 1360×1103 | 0,025101 | 0 | 0 | 13 |

Ezek a JPEG-eredmények a valós, nagy sugarú exportban erős egyezést mutatnak,
de nem fedik fel önmagukban a kis sugarú fedettségi eltérést, és nem
helyettesítik az alfa-csatornás QEMU-próbát.

**A/B út:** A) az `0x00bbe570`, `0x00aa13b0`, `0x00aa1840` utasításszintű
olvasása; B) ugyanennek a munkavégzőnek a közvetlen `qemu-i386` futtatása
szintetikus képekkel. A méret, a két koncentrikus ív, az élsimítás és a
packed dword-összeadás egyezik. A Picasa-exportpár harmadik, független
kontroll a ténylegesen használt beállításokra.

**Bizonyítottsági fok: feltételes.** A fenti méret-, geometria-, teljes
fedésű keverési és kiválasztott pixelállítások megerősítettek (utasítások +
natív futtatás). A művelet általános per-pixel fedettségfüggvénye, valamint a
forrás alfaértékének leképezése a görbe peremén még nyitott; ezért a teljes
`Border`-műveletet a `#626` leltárában nem emelem `megerősített` fokra.

**A #626 leltár Border-sora:** `Border | 4 effekt | feltételes |` kimeneti
méret, koncentrikus ívek, élsimítás és ARGB packed keverés két úttal igazolt;
az általános `C(x,y,R)` és a görbeszéli forrásalfa `0x00aa1840`/`0x00bbe570`
útja még nyitott.

#### Nyitott, célzott dekompilálás

Ghidra-kör kell: `0x00aa1840` — a sugárból és képpont-koordinátából a 16.16-os `C(x,y,R)` fedettség pontos levezetése [blokkoló]
Ghidra-kör kell: `0x00bbe570` — hogyan kerül a forrás ARGB-alfa a görbével levágott kép-sarok peremképpontjaira [blokkoló]

### G) ⭐ A `SimpleColorMatrix` hue-forgató mátrixa (2026-09-19, #626)

A `SimpleColorMatrix` ötödik mátrix-építője (`0x008f1e70`, 463 bájt) a
szögparamétert előbb **−180…+180 fokra vágja**, majd
`h / 180 · π` alakban radiánra váltja. A `180` konstans a `0x00cf3d48`, a
π-konstans a `0x00cf4298`; a `sin` és `cos` hívási útja rendre
`0x00c285f0` és `0x00c29d20`.

A nyers FPU-lánc a mátrix első sorát közvetlenül kiadja (`0x008f1f08`–
`0x008f1f66`), a további sorok ugyanebbe a 25 elemű mátrix-lokálisba kerülnek
(`0x008f1f6a`–`0x008f2028`), majd a közös mátrix-alkalmazó kapja
(`0x008f202c`, `FUN_008f28d0`). A kilenc színkonstans és címe:

| cím | érték |
|---|---:|
| `0x00cf4250` | 0,283 |
| `0x00cf4258` | 0,14 |
| `0x00cf4260` | 0,285 |
| `0x00cf4268` | 0,143 |
| `0x00cf4270` | 0,928 |
| `0x00cf4278` | 0,072 |
| `0x00cf4280` | 0,715 |
| `0x00cf4288` | 0,213 |
| `0x00cf4290` | 0,787 |

A kiolvasott 3×3 színmátrix — `C = cos(h/180·π)`,
`S = sin(h/180·π)` — ez:

```text
R' = (0,213 + 0,787·C − 0,213·S)·R
   + (0,715 − 0,715·C − 0,715·S)·G
   + (0,072 − 0,072·C + 0,928·S)·B

G' = (0,213 − 0,213·C + 0,143·S)·R
   + (0,715 + 0,285·C + 0,140·S)·G
   + (0,072 − 0,072·C − 0,283·S)·B

B' = (0,213 − 0,213·C − 0,787·S)·R
   + (0,715 − 0,715·C + 0,715·S)·G
   + (0,072 + 0,928·C + 0,072·S)·B
```

#### Független numerikus kontroll

Az explicit képletből számolva `h=0°` esetén az azonosságmátrix maximális
eltérése **0,0**, a `h ∈ {−180°, −90°, 0°, 90°, 180°}` kontrollpontokon a
legnagyobb sorösszeg-eltérés **2,22·10⁻¹⁶** (lebegőpontos zaj). A ±180°
ág ugyanazt a mátrixot adja, mert a szög előbb a határra vágódik.

**Bizonyítottsági fok: megerősített** a szögkorlátra, a fok→radián útra,
az állandók címére/értékére és a mátrix képletére (helyi x86
diszasszemblálás + PE-adatkiolvasás + numerikus kontroll). Ez nem pixel-
golden: natív és PicasaPy kimenet összevetése ebben a körben **NINCS MEG**.

**Nyitott kérdések mérlege — e kör saját kérdései:** 0 nyílt · 1 lezárva ·
0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva”. A `ContrastAndBrightnessLinked`
ág 127,5-ös képlete utasításszinten már korábban megvolt (`0x008f2040`),
de a natív export-golden továbbra is külön, meg nem mért ellenőrzés.

### H) ⭐ A `Tint` belseje: szürkítés + a `Resaturate` táblája — és három attribútum-sor kiegészítése (2026-09-26, #626)

*Forrás: `0x00bbd630` (`glimmer::TintImageOperation`, 1. rés) · `0x00bbd4a0` / `0x00bbd500` (`ResaturateImageOperation`) · `0x00bce2f0` (a táblaelem) · `0x00bbf280` (`SimpleBorder`, 1. rés) · `0x00bbd9a0` (`Crop`, 1. rés).*

#### 1. A három hiányos attribútum-sor — most teljes

A fenti „A teljes tábla” a `Tint`, a `Crop` és a `SimpleBorder` sorát hiányosnak jelölte. Az 1. rés (attribútum-beolvasó) minden `FUN_008eb160(leíró, név)` hívása kiolvasva:

| művelet | 1. rés | név → tagoffszet |
|---|---|---|
| `SimpleBorder` | `0x00bbf280` | `left`@0x24 (`0x00c939b0`) · `right`@0x2c (`0x00c939b8`) · `top`@0x34 (`0x00cc3468`) · `bottom`@0x3c (`0x00cc346c`) · `color`@0x44 (`0x00cbda84`) |
| `Crop` | `0x00bbd9a0` | `x`@0x24 (`0x00cac5b4`) · `y`@0x2c (`0x00cac5b8`) · `width`@0x34 (`0x00c80ac4`) · `height`@0x3c (`0x00c80acc`) |
| `Tint` | `0x00bbd630` | **nincs saját tagja**: a `color`-t (`0x00cbda84`) HELYI változóba olvassa, és két gyerekműveletet épít belőle (2. pont); a `dynamicColorCachePriority` (`0x00cf0534`) a második gyerek `+0x18` mezőjébe kerül (`0x00bbd819`) |

Mindhárom beolvasó a végén az ős beolvasóját hívja (`0x00bc4900`), tehát a `BlendAlpha`, a `BlendMode` és a `Mask` náluk is él.

#### 2. A `Tint` NEM önálló pixelművelet

A `Tint` 6. rése (az alkalmazó, `0x00bbf920`) 6 bájtos. A munkát a beolvasó által épített két gyerek végzi, ebben a sorrendben:

1. **`ColorMatrixImageOperation`** (vtábla `0x00cf0798`): a mátrixot a `0x008f19e0` (egységmátrix) és a telítettség-építő `0x008f1d00` adja, **`s = −100`** paraméterrel (`fld [0xcf4238]` = −100,0; `0x00bbd686`). Ez a 4.9 szakasz képlete szerint `k = 0`, vagyis minden csatorna a **Haeberli-szürke**: `0,3086·R + 0,6094·G + 0,0820·B`. A 20 `float` elem `double`-ként másolódik át (`0x00bbd6a0`–`0x00bbd6b1`), a gyerek a `0x00bc14e0`/`0x00bc1420` párossal kerül a láncba.
2. **`ResaturateImageOperation`** (vtábla `0x00cf0578`, építő `0x00bbd4a0`): a `color` szöveget a `+0x40` mezőbe teszi.
   - A 8. rés (`0x00bbd500`) a szöveget a `0x008ef520`-szal számmá, a `0x008eea90`-nel színné alakítja. Ha az átalakítás nem sikerül, az **alapszín `0xFFDDC9AE`** marad (a `0x00bbd51d`–`0x00bbd52c` négy bájtja).
   - Ezután **`i = 0 … 255`**-re `LUT[+0x800 + 4·i] = 0x00bce2f0(szín, (float)i)` (`0x00bbd560`–`0x00bbd588`); a `+0x000`, `+0x400` és `+0xc00` rekeszt kinullázza (`0x00bbd58a`–`0x00bbd5b8`, `memset` 0x400).
   - A 6. rés **`0x00bb7c80`**, ugyanaz az alkalmazó, mint a `TwoTone`-é. A 4.9-es TwoTone-lelet szerint a `+0x800` rekesz a bemenet **piros** csatornájával indexel. Az 1. lépés után a piros csatorna maga a Haeberli-szürke.

⇒ **`Tint(szín)` = `LUT_szín[ Haeberli-szürke(képpont) ]`**, és utána a `BlendAlpha`/`BlendMode`/`Mask` keverés a bemenettel (az ős beolvasója).

⛔ **Helyesbítés** a `picasa-native-filter-registry.md` 3. szakaszához: ott az áll, hogy a `ResaturateImageOperation` „egyetlen effektnek sem feleltethető meg”. A `0x00bbd630` a `glimmer::TintImageOperation` vtáblájának 1. rése (RTTI: `0x008f0554`, rések: `0x00bc1280;0x00bbd630;…`), tehát a `Resaturate` a **`Tint` gyereke**. Így négy effekt használja: `CrossProcess`, `Soften`, `ReanimatedEyeColor`, `PicnikTint` (`filterdesc.xml` 836., 1117., 1289., 1360. sor).

#### 3. A táblaelem: `0x00bce2f0(szín, L)` — fényesség-tartó színező, Haeberli-súlyokkal

A konstansok: `0,6094` (`0xcf4068`), `0,3086` (`0xcf4060`), `0,0820` (`0xcf4058`), `0,5` (`0xc72150`), `255,0` (`0xcf39d0`), és a három kiegészítő: `0,6914` (`0xcf4050`), `0,3906` (`0xcf4048`), `0,9180` (`0xcf4040`).

A váz, utasításszinten:

1. `Lc = round(0,3086·R + 0,6094·G + 0,0820·B + 0,5)`, 0…255-re szorítva (`0x00bce32d`–`0x00bce380`, a kerekítés a `0x00c29990`);
2. `d = L − Lc`; mind a három csatornához hozzáadja (`0x00bce388`–`0x00bce3b3`);
3. ha `d > 0`, a csatornákat `255 − x` alakra tükrözi, és ezt a végén visszafordítja (`bl` jelző, `0x00bce3ca`–`0x00bce3e6` és `0x00bce813`–`0x00bce832`);
4. a negatívba került csatornákat nullára húzza, és a hiányt a még szabad csatornákra osztja szét: egy csatornánál a saját súlyával, kettőnél a kiegészítő súllyal osztva (`0x00bce41e`–`0x00bce7a0`). A ciklus addig fut, amíg a csatornák float-bitmintája 8-nál kisebb különbséggel be nem áll (`sub eax, …; cmp eax, 8`);
5. a kimenet csatornánként **csonkolt** egész (`or 0xc00` + `fistp`, `0x00bce83a`–`0x00bce8b1`), `0xFFRRGGBB` alakban.

A 4. lépés ágait nem írom át képletre: a bitpontos igazsághoz nem kell. A táblát a natív kód maga adja emulátorból, bármely színre:

    PYTHONPATH=~/picasapy-agent/venv/lib/python3.13/site-packages \
      python3 ~/picasapy-agent/eszkozok/nativ_emu/tint_lut.py ki.json 0x80cfff

**Kiegészítés (#3631, a PR #3676 átnézése):** a 4. lépés képletre írva, az
emulátor kimenetével 54 színen × 256 szinten bitre egyezően
(`glimmer_ops._resaturate_table_entry`, golden:
`tests/support/native_filter_reference/tint_resaturate_3631.json`): az 1.
lépés `Lc = floor(W·c + 0,5)`; menetenként `over = Σ w·(−v)` a negatív
csatornákon, azokat 0-ra, majd a pozitívakon `v −= over / Σ w_szabad`. A
tükrözés (3. lépés) NEM hagyható el: a csonkolás a tükrözött térben történik,
a végén `255 − trunc(v)`.

#### 4. Kontroll a meglévő goldenen

A #878 `picniktint__alap.jpg` golden párjának három mért pontja (szín `0x80cfff`, a bemenet szürkéje → kimenet) és az emulált tábla:

| szürke | golden (medián) | emulált `0x00bce2f0` | nálunk (`tint_luma_preserving`) |
|---:|---|---|---|
| 16 | (0, 16, 65) | (0, 16, 64) | nem mérve ezen a ponton |
| 128 | (69, 147, 195) | (69, 148, 196) | (67, 146, 194) |
| 248 | (231, 255, 255) | (231, 255, 255) | nem mérve ezen a ponton |

Az eltérés a golden és az emulált tábla között legfeljebb 1 szint, ez a JPEG-zaj nagyságrendje. **A kiolvasott lánc tehát a valódi.**

#### 5. Eredeti / nálunk

Nálunk a `render/glimmer_ops.py::tint_luma_preserving` egy goldenből ILLESZTETT modell: Rec.601 fényesség plusz a szín krómája, iteratív levágás-kompenzációval. Szürke bemeneten (`R = G = B = i`, a szürkítés után a bináris is ezt látja), a teljes 0…255 tartományon mérve:

| szín | átlagos eltérés (szint) | legnagyobb eltérés (szint) |
|---|---:|---:|
| `0x80cfff` (PicnikTint alap) | 1,47 | 8 |
| `0xddc9ae` (a Resaturate alapszíne) | 0,95 | 6 |
| `0xff0000` | 1,34 | 9 |
| `0x00ff00` | 2,46 | 13 |
| `0x0000ff` | 4,27 | **71** |
| `0xffff00` | 4,27 | **71** |
| `0x202060` | 1,89 | 20 |
| `0x808080` | 0,00 | 0 |

Két különbség van: (a) a súlyok Rec.601 helyett **Haeberli**-súlyok, mind a szürkítésben, mind a táblában; (b) a levágás-kompenzáció más, telített kéknél és sárgánál ettől jön a 71 szint.

*Megfejtve, és a szürke rámpán mérve.* A valódi képekre gyakorolt hatás (a négy effekt goldenjén) NINCS mérve. A fejlesztői jegy (**#3631**) ezt kéri a „Kész, ha” pontjában.

*Bizonyítottsági fok: megerősített.* A lánc utasításszinten olvasva, a tábla a natív kódból emulálva, a golden három pontja 1 szinten belül egyezik.


### 🔁 Független újralevezetés
- **bíráló:** friss opus-ügynök (Agent, nem fork) (friss kontextus, a kutató magyarázata nélkül)
- **címek:** `0x00bbd630`, `0x00bbd4a0`, `0x00bbd500`
- **eredmény:** EGYEZIK
- **a bíráló tényei:** a két gyerek sorrendje (ColorMatrix, s=-100 a 0x00bbd686-on; majd Resaturate, vtábla 0xcf0578); a 8. rés 0x00bbd500 csak a +0x800 táblát tölti a 0x00bce2f0(szín,(float)i)-vel, a másik hármat nullázza; alapszín 0xFFDDC9AE. A 0x00bce2f0 második felét a bíráló nem vizsgálta — azt az emulált futtatás és a #878 golden három pontja igazolja.
- **költség:** 104054 token

### I) ⭐ A `Border` élsimított görbéjének fedése és alfája — qemu-kontrollal (2026-10-04, #626)

*Forrás: `0x00aa1840` (görbe-raszterező) · `0x00c29990` (lebegőpontos→egész konverter) · `0x00bbe570` (Border-munkavégző) · `0x009a91a0` (kitöltés) · `0x00aa13b0` (vászon-összeállító) · `0x009ab410` (forrás fölé kompozitor).*

#### 1. Az ív per-pixel fedése

A `0x00aa1840` a görbe belső és külső négyzetes távolságát (`rᵢ²`, `rₒ²`), valamint az aktuális pixel négyzetes távolságát (`q`) használja. `Δ = rₒ² − rᵢ²`; a `0x00cf4310` címen levő `double` pontosan `2²⁴`. A skálát a natív egészre-kerekítő út adja:

```text
q ≥ rₒ²:             nincs írás
q ≤ rᵢ²:             teljes fedés (a belső ágban 256-os súly)
rᵢ² < q < rₒ²:
    K = rounder(2²⁴ / Δ)
    C = ((rₒ² − q) · K) >> 16       ; C = 0…255
```

A `rounder` a `0x00c29990` útja: a bináris adatmező `0x00da1428` alapállapotban nulla, ezért a konverter a `0x00c299c6` ágra megy; a mért qemu-futtatásban az x87 vezérlőszó `0x037f` volt (legközelebbi, párosra kerekítés). A pixel súlya nem felülmintavételezés: a fenti 16 bites fixpontos szorzás közvetlenül az `0x00aa1a74`–`0x00aa1a7d` utasításokból jön.

Részleges fedésnél a forrás alfa-bájtja `A = color >> 24`; `Aₑ = (A·C) >> 8`, majd `I = 255 − Aₑ`. A packed x86-keverő csatornánkénti bájtszabálya:

```text
R, B = (D·I + S·C) >> 8
G, A = (D·I >> 8) + (S·C >> 8)
```

`D` a cél-, `S` a forráscsatorna; ez a különbség az `0x00aa1a9c`–`0x00aa1abb` (R/B) és `0x00aa1ab5`–`0x00aa1ae1` (G/A) utasításcsoportokból következik. Kontrollmérés: `A=0x20`, `C=175`, `D=0xff010101`, `S=0x20010101` esetén a natív részfedés `0xfe010001` — a zöld csatornán a két szorzat külön csonkolódik, vörösön/kéken az összeadás előtti shift nincs.

#### 2. Miért lett a görbe szélén az alfa `0xff`

`0x00bbe570` fő bitmapjét (`EBX`) a `0x009a91a0` tölti fel a külső színnel (`0x00bbe63d`); ugyanezt az `EBX`-et adja át célként az `0x00aa13b0`-nak (`0x00bbe6e8`). Ez az összeállító meghívja a görbe-raszterezőt (`0x00aa14f4`), majd az eredményt a `0x009ab410` kompozitorral erre a célra teszi (`0x00aa162e`). A munkavégző külön egy második lokális bitmapet is `0xff000000`-val tölt fel (`0x00bbe7a1` → `0x009a91a0`, hívás `0x00bbe7b1`), mielőtt a saját `0x00aa1840` hívását végrehajtja (`0x00bbe836`). A kompozitor részleges forrásnál az alfa útját így számolja: `outA = (dstA·(256−srcA) >> 8) + srcA`. `dstA=255` esetén ez bármely 8 bites `srcA`-ra **255**; a `0xaa1840` által a szélen csökkentett forrásalfa tehát a kompozit előtt megmarad, de az átlátszatlan cél fölötti végső alfa `0xff`.

#### 3. QEMU-futtatás — eredeti gépi kód, 9 × 9

A helyi qemu-harness az eredeti `0x009a91a0` → `0x00aa1840` → `0x009ab410` függvényeket futtatta 9 × 9-es bitképen, `center=(4.5, 4.5)`, `param=3.0`, forrás `0x20ffffff`, fekete `0xff000000` cél. Az ELF a `.bt` alatt készült; futtatás: `ulimit -v 6291456` és `timeout 30 qemu-i386`. A `0xffffffff` forrásalfás kontroll **mind a 324 bájtban azonos**; átlátszó céllal a perem alfája viszont `0x01`, `0x0f`, `0x09`, `0x15` értékeket is megtartja.

```text
ff000000 ff000000 ff000000 ff000000 ff0b0b0b ff000000 ff000000 ff000000 ff000000
ff000000 ff000000 ff787878 ffffffff ffffffff ffffffff ff6b6b6b ff000000 ff000000
ff000000 ff484848 ffffffff ffffffff ffffffff ffffffff ffffffff ff353535 ff000000
ff000000 ffaeaeae ffffffff ffffffff ffffffff ffffffff ffffffff ff9b9b9b ff000000
ff000000 ffaeaeae ffffffff ffffffff ffffffff ffffffff ffffffff ff9b9b9b ff000000
ff000000 ff484848 ffffffff ffffffff ffffffff ffffffff ffffffff ff353535 ff000000
ff000000 ff000000 ff787878 ffffffff ffffffff ffffffff ff6b6b6b ff000000 ff000000
ff000000 ff000000 ff000000 ff000000 ff0b0b0b ff000000 ff000000 ff000000 ff000000
ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000 ff000000
```

#### 4. Eredeti / nálunk / fejlesztői teendő

| | Eredeti, mérve | PicasaPy, olvasva | Teendő |
|---|---|---|---|
| Élsimítás | `C=((rₒ²−q)·rounder(2²⁴/Δ))>>16`; R/B és G eltérő egész kerekítési sorrendje fent; a 9 × 9 qemu-kimenet bájtszinten rögzítve | `glimmer_frame_ops.py::_sarok_fedes`: 4 × 4 középpontos részminta; a `draw_border()` RGB-t kever float32-vel, `np.rint`-tel | A `_sarok_fedes` 4 × 4 közelítését cserélje az eredeti 16 bites súlyra és packed-csatorna sorrendre. A 9 × 9 táblázat legyen az izolált rasterizer byte-golden; a lekerekített téglalap négy sarkára ugyanazt a `q`, `rᵢ²`, `rₒ²` rutint alkalmazza. |
| Alfa | A görbe részleges forrásalfája `Aₑ=(A·C)>>8`; az opaque black cél fölötti `0x009ab410` kompozit végeredménye `0xff` | `draw_border()` RGB-kimenetet ad, ezért alfát nem tárol | A belső maszkon/alapképen tesztelje külön `0x20` és `0xff` forrásalfával; opaque végkép alfája mindkettőnél `0xff`, a maszkréteg viszont őrizze meg a `C`-vel súlyozott alfát. |

**Bizonyítottsági fok: megerősített** a fedési képletre és az alfa útjára: az utasításszintű olvasás és az eredeti függvények qemu-futtatása egyezik. **NINCS MEG:** a teljes `Border`-export bájtpontos natív–PicasaPy golden. Ez a 9 × 9-es próba a natív görbe-raszterező és kompozitor izolált kontrollja; a korábbi `border__max` export JPEG-alapú geometriamérése marad az összhatás-kontroll.

**Cáfoló próba:** azt ellenőriztem, hogy a `0x00aa1840` maga állítja-e `0xff`-re a perem alfáját. Átlátszó céllal a qemu-kimenet részleges alfái megmaradnak; csak az opaque black cél fölötti `0x009ab410` után lesz minden kimeneti alfa `0xff`. A hipotézis cáfolva.

## A lánc SORRENDJE — goldennel eldöntve (2026-09-19, #3229)

*A 12. szakasz kimérte a binárisból, hogy az eredeti nem rendez át: a
`CGenericFilter` `+0x84` rekesze minden opnak átadja a koordináta-leképezést és
az inverzét, és a szerkesztő sorrendben renderel. Az átállítás viszont MINDEN
ilyen képen megváltoztatja a látványt, ezért a tulajdonos golden-exportot kért —
ez a szakasz azt zárja le.*

### A mérőkészlet és a döntő kép

`My Pictures\3229-lanc-sorrend`, négy kép, a beállítások a `.picasa.ini`-ben; az
`export/` az eredeti, windowsos Picasa kimenete.

Döntő: `01-keret-utan-szepia.jpg` —
`Border=1,20,5,0,00000000,00ffffff,0;sepia=1;`. A keret (a kimenet legkülső 1%-a)
átlagos RGB-je az eredetinél **(46, 37, 28)**: barnás, tehát a szépia a KERETRE
is ráment. Kontroll: `02-szepia-utan-keret.jpg` (`sepia;Border`) — ott a keret
**(0, 0, 0)**, azaz a keret a saját színén marad, ha utoljára kerül fel.

⇒ **Az eredeti a lánc sorrendjében dolgozik.** A `#330` „a keret a legvégén fut"
olvasata ezzel megdőlt.

### A két águnk ugyanazon a képen

| ág | a keret RGB-je | átlagos ΔE a referenciához |
|---|---|---:|
| a régi (halasztó) | 0, 0, 0 | 4,481 |
| **a mért sorrend** | **46, 37, 29** | **2,278** |

A `03-keret-utan-vignetta.jpg`-n mindkét ág feketét ad, mint a referencia (a
vignetta erőssége maga tér el: ΔE 29,4 → 26,9).

### ⚠️ A negyedik kép NEM mér

A `04-vagas-utan-vignetta.jpg` a vágást a `filters=` sorba írta
(`crop64=1,3c3c8c8c;…`), a Picasa viszont a képszekció **`crop=`** kulcsából vág
— ezért az exportja **vágatlan** (1600×1200), és a két águnk 376×659-es kimenete
nem hasonlítható hozzá. A vágás sorrendjét ezért a 12. szakasz bináris mérése és
a `tests/render/test_mert_sorrend_3229.py` próbái fedik, nem golden. Új
mérőkészlet NEM kell hozzá.

### Ami ebből a termékbe került

Az `apply_filters` alapértelmezése a mért sorrend (#3229 3. lépés), a halasztó
ág `mert_sorrend=False`-szal kontrollnak megmarad, és a szerkesztő lánc-prefix
gyorsítótára a koordináta-állapotot (`LancHelyzet`) is átadja a folytatásnak —
enélkül a kettévágott lánc mást adna, mint az egészben futtatott (a #3169 ezt
`crop64;Vignette` esetén 18,2-nek mérte). Őr:
`tests/render/test_lanc_sorrend_elesben_3229.py`.

## ⛳⛳ A `BlendInstruction`: tizenegy keverési mód, egész aritmetika — és két mért hiba nálunk (2026-09-21, 337. kör, #626)

*Forrás: a `BlendInstruction` vtáblája (`0x00cf0f00`) és végrehajtója
`FUN_00bd0700` (1040 b) · a mód-feloldó `FUN_00bd0b40` · a módonkénti
elosztó `FUN_008f4a60` és ugrótáblája (`0x008f4c48`) · a tizenegy kernel
és segédfüggvényeik (`0x008f41e0`–`0x008f6620`) · az átlátszóság-keverő
`FUN_009dc4b0` · a fordító (`0x00bc4ae0`) és az attribútum-beolvasó
(`0x00bc496f`/`0x00bc4999`) · az `IR` konstruktora (`0x00bc3d80`) · mérés a
684-es golden-szetten.*

### A) Honnan jön a mód és az átlátszóság

A műveleti objektum **ős-attribútumai**: `BlendMode` (`0x00cf0ab0`) → az
objektum `+0x04`, `BlendAlpha` (`0x00cf0abc`) → `+0x0c` (beolvasás
`0x00bc496f`, `0x00bc4999`; mindkét sztringre egyetlen hivatkozás, indextől
független pásztázással). A fordító (`0x00bc4c0f`–`0x00bc4c3c`) **csak akkor**
fűz a művelet után `BlendInstruction`-t, ha a kettő közül legalább az egyik
meg van adva; az utasítás `+0x0c`-je maga a művelet. Utána egy
`PopInstruction` jön **1-es mélységgel** (`0x00bc4f0e`, `0x00bc50a4`): a
`Pop` végrehajtója (`0x00bd1ff0`) a legfelső alatti `k`-adik elemet veszi ki
a veremből ⇒ a keverés után a **bemenet** esik ki, a keveréket hordozó
felső elem marad.

**A veremszerep tehát:** `B` = alsó elem (a művelet BEMENETE), `A` = felső
elem (a művelet KIMENETE). A végrehajtó az eredményt `A` helyére írja
(`0x009a8ca0` = `cél ← forrás`, a forrás az `eax`-ben, a cél a veremben).

### B) A mód-feloldó (`FUN_00bd0b40`) — a teljes névtábla

Előbb kifejezésként értékel (`0x008ef520`), és siker esetén a számot
egésszé alakítja (`0x008eea90`) — **a szám közvetlenül a mód sorszáma**.
Ha a kifejezés nem értékelhető ki, a nyers attribútum-szövegből levágja a
`BlendMode.` előtagot (`0x00cf0ef0`, 10 bájt), és a táblán megy végig
(`0x00cf0e98`, 11 × {érték, névmutató}) **`_strnicmp`**-pel, a táblabeli név
hosszával (`0x00bf6b22` — a CRT mintázata: locale-jelző `0x00d49bf4`,
`EINVAL`, `0x7fffffff` hibaérték). Ha nincs találat, a mód **−1** marad.

| sorszám | név | kernel | képpont-segéd (SSE2 · skalár) |
|---:|---|---|---|
| 0 | `Add` | `0x008f4d80` | `0x008f41e0` · `0x008f41f0` |
| 1 | `Darken` | `0x008f4fa0` | `0x008f4270` · `0x008f4280` |
| 2 | `Difference` | `0x008f51c0` | `0x008f42d0` · `0x008f42f0` |
| 3 | `Hardlight` | `0x008f5460` | tábla `0x00d7fc98`, építő `0x008f6540` |
| 4 | `Lighten` | `0x008f5580` | `0x008f4370` · `0x008f4380` |
| 5 | `Multiply` | `0x008f57a0` | `0x008f4400` · `0x008f4460` |
| 6 | `Overlay` | `0x008f5c00` | tábla `0x00d8fca8`, építő `0x008f65b0` |
| 7 | `Screen` | `0x008f5d20` | `0x008f4540` · `0x008f45c0` |
| 8 | `Subtract` | `0x008f6070` | `0x008f46c0` · `0x008f46d0` |
| 9 | `Normal` | `0x008f59d0` | `0x008f4780` · `0x008f48b0` |
| 10 | `Softlight` | `0x008f5f50` | tábla `0x00d6fc80`, építő `0x008f6620` |

⚠️ A sorszám **nem ábécérendű a végén**: a `Softlight` a 10-es, a `Normal` a
9-es. Minden `BlendMode="{…?7:5}"` és minden számot adó csúszka EZT a
sorszámot adja át.

### C) A képpont-képletek — `b` = alsó (bemenet), `t` = felső (kimenet)

Mind a négy bájtra (B, G, R **és alfa**) ugyanaz a képlet fut. A `÷255`
mindenütt **csonkoló** (`0x80808081`-es szorzás, `sar 7`, előjel-korrekció).

| mód | képlet | bizonyíték |
|---|---|---|
| Add | `min(b + t, 255)` | `paddusb` `0x008f41e0` |
| Darken | `min(b, t)` | `pminub` `0x008f4270` |
| Lighten | `max(b, t)` | `pmaxub` `0x008f4370` |
| Difference | `|b − t|` | két `psubusb` + `por` `0x008f42d0` |
| Subtract | `max(b − t, 0)` | `psubusb xmm0(b), xmm1(t)` `0x008f46c0` |
| Multiply | `⌊b·t / 255⌋` | skalár `0x008f446e`; SSE2: `(p + (p>>8) + 1) >> 8`, `0x00cd0520` = 1 |
| Screen | `⌊(65025 − (255−b)(255−t)) / 255⌋` = `b + t − ⌈b·t/255⌉` | skalár `0x008f45dc`; SSE2 `psubusw`, `0x00cd0530` = 254, `0x00cd0540` = 1 |
| Overlay | `f(b, t)` | tábla `T[t·256 + b] = f(b, t)` (`0x008f65d8`) |
| Hardlight | `f(t, b)` | tábla `T[t·256 + b] = f(t, b)` (`0x008f6568`) — CSERÉLT argumentum |
| Softlight | `t < 128`: `⌊t·(b′+128) / 255⌋`; különben `⌊(65025 − (382 − b′)(255 − t)) / 255⌋`, ahol **`b′ = b & 0xFE`** | `0x008f6640`–`0x008f667d` |
| Normal | `⌊(t·αₜ + b·(255 − αₜ)) / 255⌋` — a felső elem SAJÁT alfájával | `pshuflw/pshufhw 0xff` + `pandn` `0x008f4780`; skalár `0x008f48b0` |

Az `Overlay`/`Hardlight` közös alapfüggvénye (`0x008f53f0`, `x` = 1., `y` =
2. argumentum):

```
x ≤ 127:          ⌊2·x·y / 255⌋
x = y = 255:      255                         ← külön ág (0x008f5405)
különben:         ⌊(65024 − 2·(255−x)·(255−y)) / 255⌋
```

(A 65024 = 255² − 1; a külön ág nélkül 255/255-re 254 jönne ki.)

**A két útvonal bitre azonos** — mérve mind a 65 536 bájtpáron (Multiply,
Screen), a `Normal`-nál mind a 256 alfaértékre is. A CPU-jelző
(`0x00d695d2`/`0x00d695d3`) tehát nem befolyásolja a kimenetet.

A `Softlight` képletében a döntő operandus a **felső** elem, és az alsó
elem legalsó bitje eldobódik (`and al, 0xfe`, `0x008f6642`). Ezt a kód így
mondja — hogy szándékos-e, azt nem tudjuk; a Glimmer-leíró egyetlen
effektje sem hivatkozik a 10-es módra név szerint, a `Pixelate` csúszkája
pedig csak 0–9-ig megy.

### D) A végrehajtó menete (`FUN_00bd0700`)

1. `α = BlendAlpha` (hiányában **1,0**), **[0, 1]-re vágva** (`0x00bd0742`–
   `0x00bd0778`) — a `BlendAlpha="100"` (a `Boost`-ban) tehát 1.
2. Ha a mód **−1 vagy 9 (Normal)** és `α ≈ 1` → **semmi nem történik**, a
   felső elem változatlan (`0x00bd077e`–`0x00bd07b2`). ⚠️ A kifejezett
   `Normal` tehát teljes átlátszóságnál **nem** kompozitál a felső elem
   alfájával; `α < 1`-nél viszont igen (3. lépés).
3. Ha `α ≈ 0` → a felső elem helyére az alsó kerül (`0x00bd07d3`–`0x00bd07ec`).
4. Ha a mód 0–10 → a kernel a (felső, alsó) párból új képet ír, és az a
   felső elem helyére kerül (`0x00bd0934`, `0x00bd09b9`).
5. Ha `α` nem ≈ 1 → **átlátszóság-keverés** (`0x009dc4b0`), majd a
   kimenet **alfacsatornája 255-re áll** (`0x009a99c0`, `eax = 0xff`, teljes
   téglalap).

A „≈” mindkét helyen a float **bitmintáján** mér: `|bits(α) − bits(x)| < 8`
(ugyanaz a fogás, mint az `Exposure`-nél).

**Az átlátszóság-keverés** (`0x009dc4b0`):

```
w = trunc(α · 256)        ; 0x00cf39d8 = 256,0, csonkoló kerekítés (0x0c00 vezérlőszó)
w = w − 1, ha w > 0       ; 0x009dc561
ki = (b · (255 − w) + t · w) >> 8      ; MMX, 0x00c7c828 = 0x00FF
```

⚠️ **A súlyok összege 255, az osztó 256** — a keverék ezért egy szinttel
sötétebb lehet (két 255-ös bemenetből 254). Ez a kód viselkedése, nem
kerekítési hiba nálunk.

⚠️ **Páratlan szélességnél az utolsó oszlop MÁS képletet kap**
(`0x009dc646`–`0x009dc6fb`): `ki = t + ((b − t) · w >> 8)`, azaz a súly
ott az ALSÓ elemre esik. A közös keverő ezt az előjeles skalárképletet
alkalmazza a sorvégi pixelre (#4157); a bájtpontos 51×49-es teszt a 72/74-es
példán és a 50 széles páros kontrollon igazolja. A TwoTone natív QEMU-kontrollja
lent (`Fade=50`, 9 px szélesség) a #4157 előtti kóddal 5 pixel/10 RGB-bájt,
legfeljebb 1 szint eltérést mért ugyanezen a sorvégi ágon; az adott konfiguráció
Picasa-export goldenen még nincs ellenőrizve.


#### ⛳ A keverés tétlen műveletnél is lefut — a `Soften` 0-s erősségnél eggyel sötétít (2026-09-28, 396. kör, #3894)

*Bizonyítottsági fok: **megerősített**, utasításszinten, független újralevezetéssel és golden-méréssel.*

A végrehajtó a keverést a **mód és az `α`** alapján hagyja ki (2. és 3. lépés
fent), **nem** aszerint, hogy a művelet változtatott-e a képen. A `Soften`
leírója (`filterdesc.xml` 1348: `BlurImageOperation`, `xblur = yblur =
Impact·20/50`, `BlendAlpha = (100 − Fade)·0,8/100`) `Impact = 0`, `Fade = 0`
mellett 0-s sugarat és `α = 0,8`-et ad: az elmosás azonosság, de a
`0x009dc4b0` keverése lefut, `w = trunc(0,8·256) − 1 = 203` súllyal:

```
ki = (b·(255 − 203) + b·203) >> 8 = (255·b) >> 8 = b − 1   (b ≥ 1),   0 → 0
```

A 0-s sugarú `BlurImageOperation` nem lép ki: `0x00bb5050` 1 alatti sugárra 0-t ad, a `0x00bc5680` ilyenkor a `0x00bc5960` soronkénti másolását hívja. A keverés mód nélkül és `α = 0,8`-nál lefut (`0x00bd0816` `jae 0x00bd0a2a` → `0x00bd0aaa` `call 0x009dc4b0`). Páratlan szélességnél az utolsó oszlopot a skalár farok (`0x009dc646`–`0x009dc6fb`) `E + (((S − E)·w′) >> 8)` alakban számolja, ami `t = b`-nél pontosan `b`-t ad.

**Mérve** (684-es készlet, `soften__min`): az export minden csatornán
átlagosan −1,00 szinttel sötétebb a forrásnál; érték szerint 0 → 0,04,
1 → 0,03, 2 → 1,01, 128 → 127,01, 255 → 254,0.

| modell | ΔE a Picasa-exporthoz |
|---|---:|
| ma (0-s sugárnál a bemenet másolata) | 0,470 |
| **a fenti keverés** | **0,121** |
| zajszint (mi ↔ mi-JPEG95) | 0,083 |

⚠️ **A mérőeszköz vakfoltja.** A `tools/golden/analyze_validation_kit.py`
„tétlen” küszöbe `NOOP_DE = 1,0`; az egyenletes −1-es eltolódás (ΔE 0,47) ez
alá esik, ezért a sor „mindkettő tétlen” besorolást kapott, és a kód erre
hivatkozva hagyta ki a keverést. A 684-es készlet 56 „tétlen” sora közül
ilyen eltolódást a `soften__min` (−1,00) és a `dir_tint__min` (−0,50)
mutat, helyi, egyirányút pedig a `roundededges__alap` (+2,10, a sarkok
fehérje); a többinél az eltolódás legfeljebb 0,12.

Fejlesztés: #3895.

> ✅ **Megvalósítva (#3895, 2026-09-28).** Az `apply_soften` 0-s sugárnál is
> keveri a (változatlan) képet önmagával: `soften__min` ΔE 0,470 → **0,121**
> (`alap` 0,196, `max` 0,121 — változatlan). Az elemző `mean_shift`-je a
> `|átlagos előjeles eltolódás| ≥ 0,25` sort már nem sorolja tétlennek
> (JPEG-zaj ≤ 0,003, a legkisebb valódi jel a `dir_tint__min` −0,50-e): a
> `soften__min` a javítás nélkül `NEM_IMPLEMENTALT`, vele `JO`.
>
> A teljes 684-es készlet újramérve (előtte `main`, utána ez az ág;
> `docs/benchmarks/2026-09-19-golden-meroszett-684.md`): `JO` 113 → 115,
> `MINDKETTO_TETLEN` 56 → 53, `NEM_IMPLEMENTALT` 0 → 1, a többi változatlan.
> Három sor fordul át a „mindkettő tétlen”-ből: `soften__min` → `JO`
> (ΔE 0,470 → 0,121), `roundededges__alap` → `JO` (ΔE 0,143; a sarkok
> fehérje mindkét oldalon +2,1 szint), és `dir_tint__min` →
> **`NEM_IMPLEMENTALT`** (ΔE 0,296; a Picasa az átmenet vonala fölötti felet
> pontosan eggyel sötétíti — ugyanaz a `(255·b) >> 8` minta —, mi a
> bemenetet másoljuk). Ez utóbbi eddig rejtett eltérés; egy 0,5-ös küszöb
> (mért eltolódás −0,498) nem fogta volna meg.

### E) Két mért hiba nálunk — a bináris itt az OKOT is megadja

**1. Az `IR` zöld ragyogása SCREEN, nem LIGHTEN.** Az `IR` konstruktora a
ragyogás gyerekművelete (`glimmer::NestedImageOperation`, vtábla
`0x00cf0774`) mód-attribútumát **konstans 7-re** állítja: `0x00bc3e49
push 7` → `+0x04` → `0x008eedc0`. A 7 a fenti tábla szerint **Screen**.
A #3441 előtti kódállapot (`glimmer_creative.py`, `apply_ir`) LIGHTEN-t
használt, és a docstring ezt azzal indokolta, hogy „a `PicnikGrain`
deklarációja szerint a 7-es mód LIGHTEN” — **ez az olvasat téves**, a 7 a
Screen.

| `ir` eset | ΔE (Picasa vs. eredeti) | ΔE mi (akkori LIGHTEN) | ΔE mi (akkori SCREEN-modell) |
|---|---:|---:|---:|
| `alap` (Fade 0) | 18,131 | **6,039** | **1,280** |
| `max` (Fade 100) | — | 0,121 | 0,121 |

*A #3441 előtti összevetés: `684-merokeszlet`,
`tools/golden/compare_render.py` `delta_e_cie76` átlaga; a SCREEN-oszlop az
akkori lebegőpontos `_blend_screen`-modellt, az `apply_ir` többi részének
változatlanságát mutatja.* ⇒ a verdikt `ROSSZ` → `JO`; a későbbi natív
bájtmérést lásd az IR „Pixelmag, közös alkalmazók és natív bájtmérés”
szakaszában.

**2. A `Pixelate` `BlendMode` csúszkája (0–9) a natív sorszámot adja.** A mai
`apply_pixelate` docstringje szerint a csúszka jelentése „a
`filterdesc.xml`-ből NEM dekódolható”, ezért figyelmen kívül hagyjuk. A
fenti tábla dekódolja: 0 Add · 1 Darken · 2 Difference · 3 Hardlight ·
4 Lighten · 5 Multiply · 6 Overlay · 7 Screen · 8 Subtract · **9 Normal
(alapérték)**.

| `pixelate` eset | lánc | ΔE mi (ma) | ΔE mi (a natív móddal) |
|---|---|---:|---:|
| `min` | `Impact 2 · BlendMode 0 · Fade 0` | **23,307** | **0,783** (Add) |
| `alap` | `Impact 20 · BlendMode 9 · Fade 0` | 4,638 | 4,638 (Normal, α = 1 → no-op) |

Az `alap` maradék 4,6-ja tehát **nem** a keverésből jön — az a pixelesítés
saját eltérése, külön kérdés.

### F) A három „futásidőben változó” mód — feloldva

| effekt | kifejezés | mit ad |
|---|---|---|
| `PicnikGrain` | `{_radioLighten.selected?7:5}` | **7 = Screen** (világosító), **5 = Multiply** (sötétítő) — nálunk is (#3444, #3757) |
| `Pixelate` | `{_sldrBlendMode.value}` | a csúszka értéke = sorszám (E/2) |
| `PicnikTint` | `{_cbBlendMode.liveValue}` | a `_cbBlendMode` vezérlő **sehol nincs definiálva** a leíróban ⇒ a kifejezés nem értékelhető; a szöveges ág a `BlendMode.` előtag után a `liveValue}` maradékot hasonlítja ⇒ nincs találat ⇒ **mód −1**, csak átlátszóság-keverés. Összhangban a #884 mérésével (tiszta színezés, ΔE 1,50). |

A `{BlendMode.SCREEN}` alakú kifejezések (`PencilSketch`,
`ReanimatedEyeColor`) ugyanígy a szöveges ágon oldódnak fel: a `BlendMode`
szóra a binárisban csak az attribútumnév és az előtag hivatkozik (egy-egy
helyen), tehát a kiértékelőnek nincs ilyen szimbóluma; az előtag után a
`SCREEN}` a `Screen` név hosszán, kis/nagybetű nélkül illeszkedik ⇒ 7.

### G) Eredeti / nálunk / teendő

| | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| módok | 11 | 7 (`normal multiply screen overlay darken lighten add`) | `difference`, `hardlight`, `subtract`, `softlight` hiányzik |
| Add/Darken/Lighten | egész | **bitre azonos** (65 536 pár, 0 eltérés) | — |
| Multiply/Screen | csonkoló `÷255` | `rint` — 31 770 / 65 536 pár tér el, max 1 | csonkolás |
| Overlay | csonkoló, `255/255` külön ág | `rint` — 32 767 pár tér el, max 1 | csonkolás |
| átlátszóság | `(b·(255−w) + t·w) >> 8`, `w = trunc(256α) − 1` | lebegőpontos `b + α(t − b)` + `rint` — α ∈ {0,25; 0,5; 0,6; 0,75; 0,9}: 51 754–57 184 pár tér el, max **2** | egész képlet |
| alfa a keverés után | 255 | nem kezeljük (RGB-ben dolgozunk) | nincs teendő, amíg a lánc RGB |
| `IR` ragyogás | Screen | ✅ **Screen** (#3441, v0.8.555) | kész — ΔE 6,04 → 1,28, mérve |
| `Pixelate` csúszka | sorszám | ✅ **sorszám** (#3443, v0.8.556) — a Difference/Hardlight/Subtract lebegőpontosan | kész — `min`: ΔE 23,31 → 0,78, mérve; az egész képletek és a Softlight: #3442 |
| `PicnikGrain` | Screen / Multiply | ✅ **Screen / Multiply**, Picasa-MT `randomSeed = 1` (#3444, #3757) | kész — ΔE alap 3,01 → **0,88**, max 12,21 → **1,38**, merokit-2 Grain 30: 7,79 → **0,98**, mérve. A zaj NEM véletlen: a #907 a natív `grain` szűrőt mérte |

*Bizonyítottsági fok:* a tábla, a kernelek, a keverő és a végrehajtó menete
**megerősített** (diszasszemblátum + kimerítő bájtpáros próba); a veremszerep
**erős** (a `Pop` 1-es mélysége és a `cél ← forrás` másoló, a Dupe helye a
művelet saját fordító-slotjában nincs végigkövetve); az `IR` 7-ese
**megerősített** (konstans a mód-attribútumba) és **mérve** hat; a
`PicnikTint` −1-e **erős** (a vezérlő hiánya a leíróban ellenőrizve).

### H) Nyitott kérdések mérlege

- a páratlan szélesség utolsó oszlopának csomagolt átvitele — **HATÓKÖRÖN
  KÍVÜL** (egy oszlop, golden-mérés nélkül nem építjük; 337. kör döntése);
- a `Softlight` `& 0xFE`-je szándékos-e — **LEZÁRVA**: a kód ezt csinálja,
  utánépíteni így kell; a szándék nem kérdés a megvalósításhoz;
- a `PicnikGrain` hatása a mért eltérésre — **LEZÁRVA, pixelre mérve**
  (#3757): a mag NEM véletlen, a leíró `randomSeed = 1`-et ad (a #907 a
  natív `grain`-t mérte). A Screen/Multiply és a rögzített mag együtt: ΔE
  alap 3,01 → 0,88, max 12,21 → 1,38; a #3444 statisztikai próbája is
  teljesül (ld. G).

`0 nyílt · 2 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva`

### Amit KIZÁRTAM

- „a 7-es mód LIGHTEN” (`glimmer_creative.py` docstring) — a névtábla
  (`0x00cf0e98`) és az ugrótábla (`0x008f4c48`) egyaránt Screent ad, és a
  golden-mérés is azt igazolja;
- „a `Pixelate` csúszkája nem dekódolható” — a sorszám közvetlenül a
  módtábla indexe;
- „a `Normal` teljes átlátszóságnál is alfával kompozitál” — a végrehajtó
  `α ≈ 1`-nél a kernelt meg sem hívja.

## ⛳⛳ A három maszk-utasítás: egy közös képlet, három különböző maszk-forrás (2026-09-21, 338. kör, #626)

*Forrás: a `MaskInstruction` (`0x00cf0f6c`, másodlagos vtábla `0x00cf0f84`),
a `PartialMaskInstruction` (`0x00cf0f30`) és a
`MaskWithSourceAlphaInstruction` (`0x00cf0f48`) végrehajtója · a közös
maszkolt keverő `0x008f4c80` → `0x008f62a0` · a maszk-osztályok vtáblái
(RTTI) · a fordító választása (`0x00bc4dcb`–`0x00bc4fde`) · kimerítő
hármas-próba.*

### A) A közös képpont-képlet

Mindhárom utasítás ugyanazt a keverőt hívja: `0x008f4c80(felső, alsó,
maszk, cél, téglalap)` → `0x008f62a0`, és az a már ismert segédpárt
(`0x008f4810` SSE2 · `0x008f49a0` skalár — ld. a `BlendInstruction`
szakaszban a `Normal` módot). A különbség csak annyi, hogy itt a súly a
**harmadik kép alfacsatornája** (`psrld xmm5, 0x18`, `0x008f482c`), nem a
felső elemé:

```
m   = a maszk-kép képpontjának ALFA-bájtja (0…255)
ki  = ⌊(t·m + b·(255 − m)) / 255⌋        ; R, G, B
ki.alfa = 255                             ; 0x008f48a1–0x008f48aa, skalárban 0x008f4a45
```

`t` = a felső veremelem (a művelet kimenete), `b` = az alsó (a bemenete).
Az SSE2 út `(s + (s >> 8) + 1) >> 8`-cal oszt; **mind a 256 maszkértékre
bitre azonos** a skalár `⌊s/255⌋`-val (kimerítő próba).

### B) `MaskInstruction` — csak a festett ecsetmaszk kapja

A fordító (`0x00bc4dcb`) minden maszk-műveletre megkérdezi annak két
predikátumát (`vtbl+0x10`, `vtbl+0x0c`); **ha mindkettő igaz**, teljes
`MaskInstruction` jön (`+0x10` = a maszk-művelet, `+0x08` = 100), különben
`PartialMaskInstruction`. A predikátumok a vtáblákból:

| maszk-osztály | vtábla | `+0x0c` / `+0x10` | utasítás |
|---|---|---|---|
| `PaintMaskPlusImageMask` | `0x00cf0750` | `0x007a5240` → **1** / 1 | **`MaskInstruction`** |
| `ImageMask` | `0x00cf0d34` | `0x004bdeb0` → 0 / 0 | `PartialMask` |
| `TiledImageMask` | `0x00cf02e8` | `0x004bdeb0` → 0 / 0 | `PartialMask` |
| `ShapeGradientImageMask` | `0x00cf0e50` | `0x004bdeb0` → 0 / 0 | `PartialMask` |
| `CircularGradientImageMask` | `0x00cf0890` | `0x004bdeb0` → 0 / 0 | `PartialMask` |

A végrehajtó (`0x00bd16f0` → `0x00bd1730`, jelző = 0):

1. a maszk-művelet saját rajzoló slotja (`vtbl+0x1c`, `0x00bd1ae6`) a
   BEMENET méretére megrajzolja a maszkot egy helyi képbe;
2. egy üres, bemenet-méretű célképet foglal (`0x009a9c90`);
3. az A) képlettel a teljes képre kever;
4. a célképet **új elemként** a verem tetejére teszi (`0x00bd1f08`) — a
   verem eggyel nő; a fölösleget a fordító utána tett `Pop`-ja viszi el.

**Az 1-es jelzős ág** (`0x00bd1710`, a másodlagos vtáblán, azaz a
`ReExecutingInstruction`-felületen át) az ecsethúzás közbeni
**újraszámolás**: a verem tetejéről leveszi az ELŐZŐ futás eredményét
(`0x00bd179c`), azt használja célképnek, és a téglalapot a kontextus
`+0x28` objektumából veszi (`0x00bd1b68`–`0x00bd1ba5`), majd azt
**-1-re állítja** (elfogyasztja). ⇒ húzás közben csak a „piszkos”
téglalap számolódik újra.

### C) `PartialMaskInstruction` — a téglalapon kívül EGYETLEN szám dönt

A végrehajtó (`0x00bd0f10`):

1. megrajzolja a maszkot (`vtbl+0x1c`, `0x00bd0ff3`);
2. megkérdezi a maszk-művelet `vtbl+0x08` értékét (`0x00bd102c`), és ha az
   `≈ 1` (bitmintán `< 8` ULP), az **alap** a felső elem, különben az alsó
   (`0x00bd1045`–`0x00bd1058`);
3. ha a maszknak nincs befoglaló téglalapja (mind a négy −1), az eredmény
   **az alap maga**, keverés nélkül (`0x00bd10bd`–`0x00bd10cf` →
   `0x00bd12e8`);
4. különben az alapot a maszk téglalapjára másolja (`0x009a8fe0`), azon
   belül az A) képlettel kever, és az eredmény a **felső elem helyére**
   kerül (`0x00bd130c`) — a verem mérete nem változik.

A `vtbl+0x08` értéke:

| maszk-család | függvény | érték |
|---|---|---|
| `ImageMask`, `TiledImageMask`, `PaintMaskPlusImageMask` | `0x00bb9fc0` | **0,0** (`fldz`) ⇒ a téglalapon kívül az EREDETI marad |
| `ShapeGradient`, `CircularGradient` | `0x00bcfbf0` | az **`outerAlpha`** attribútum, [0,1]-re vágva, alapértéke 1,0 |

Az `outerAlpha` azonosítása: a színátmenetes maszk attribútum-beolvasója a
nevet a `0x00bcfd12`-n tölti be, és a `+0x38`-as tartóba teszi; a
`0x00bd02d0` ezt olvassa a rekord `+0x18`-ába (`0x00bd03ce`–`0x00bd03de`,
[0,1]-vágás `0x00bd03e8`–`0x00bd0408`), és a `0x00bcfbf0` ezt adja vissza
(`0x00bcfc57`).

⚠️ **Köztes `outerAlpha` nem kever a téglalapon kívül:** 0,5-nél a kívül
eső rész az EREDETI (mert `0,5 ≉ 1`). A `filterdesc.xml` minden
színátmenetes maszkja `outerAlpha = Reverse ? 0 : 1`-et ad (ld. fent a
`CircularGradientImageMask` sort), tehát a mai effektekben ez a határeset
nem fordul elő.

### D) `MaskWithSourceAlphaInstruction` — a forrás alfája a maszk

A végrehajtó (`0x00bd1350`) egy felső-méretű helyi képet **fehérre és
teljesen fedőre** tölt (`0x009a91a0`, érték `0xFFFFFFFF`, `0x00bd13dc`),
majd az A) keverőt így hívja: felső = a felső elem, alsó = ÉS cél = a fehér
kép, maszk = **az alsó veremelem** (a forrás). Az eredmény a felső elem
helyére kerül (`0x00bd1620`).

```
ki = ⌊(t·α_forrás + 255·(255 − α_forrás)) / 255⌋ ,  ki.alfa = 255
```

⇒ ahol a forrás átlátszó, ott a kimenet fehér; teljesen fedő forrásnál
(minden fénykép) a kimenet bitre a felső elem. A fordító akkor fűzi a
művelet után, ha a `maskWithSourceAlpha` attribútum igaz (`[op+0x20]`,
beolvasás `0x00bc4962`–`0x00bc496c`; kiírás `0x00bc4b23`–`0x00bc4b41`) — a
`filterdesc.xml`-ben két helyen: a `Cinemascope` zajrétegén (`:762`) és a
`PicnikGrain` beágyazott műveletén (`:923`).

### E) Eredeti / nálunk / teendő

| | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| maszkolt keverés | `⌊(t·m + b·(255−m))/255⌋`, `m` = a maszk ALFA-bájtja | `masked_blend`: lebegőpontos `b·(1−m) + t·m`, `rint` — **8 164 890 / 16 777 216 hármas (48,7%) tér el, max 1** | csonkoló egész képlet — a #3442 része |
| kimeneti alfa | 255 | RGB-ben dolgozunk | nincs teendő |
| `PartialMask` a téglalapon kívül | `vtbl+0x08 ≈ 1` ? felső : alsó | nem mérve (a maszkjaink teljes képet adnak) | nincs, amíg minden `outerAlpha` 0 vagy 1 |
| `MaskWithSourceAlpha` | fehérre kompozitál a forrás alfájával | nincs | nincs teendő fedő forrásnál (bitre no-op) |
| ecset-újraszámolás | csak a piszkos téglalap | — | teljesítmény-kérdés, nem pixel-kérdés |

*Bizonyítottsági fok:* a képlet, a három végrehajtó adatfolyama és a
fordító választása **megerősített**; az `outerAlpha` azonosítása **erős**
(a beolvasó és a `0x00bd02d0` ugyanazt a `+0x38` tartót használja — a két
függvény közös objektum-bázisát a hívási lánc nem bizonyítja közvetlenül).

### F) Nyitott kérdések mérlege

- a `PartialMask` köztes-`outerAlpha` viselkedése — **LEZÁRVA** (C);
- az 1-es jelzős ág szerepe — **LEZÁRVA**: újraszámolás a piszkos
  téglalapon (B);
- hogy a `MaskInstruction` `+0x08 = 100` mit jelent (gyorsítótár-prioritás?)
  — **HATÓKÖRÖN KÍVÜL**: a képpont-kimenetre nincs hatása (a végrehajtó nem
  olvassa); 338. kör döntése.

`0 nyílt · 2 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva`

⇒ **A #626 utasításgép-leltára ezzel teljes:** `Apply` (LUT- és
mátrix-család), `Blend` (11 mód), a három maszk, `Dupe`/`Pop` (verem),
`GetVar`/`SetVar` (változók). A #626 maradék, műveletenkénti kérdései a
fenti gépezeten már egyenként olvashatók.

### Amit KIZÁRTAM

- „a maszk a szürkeárnyalatos világosságával súlyoz” — a súly az ALFA-bájt
  (`psrld 0x18`);
- „a `PartialMask` a téglalapon kívül is a maszk értékével kever” — egyetlen
  küszöbölt szám dönt (felső vagy alsó).
