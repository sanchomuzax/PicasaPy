# `filterdesc.xml` — a Picasa hivatalos szűrő-regisztere

**Forrás:** `research/copy_Picasa_3_7/Picasa3/runtime/filterdesc.xml`
(63 KB, 1408 sor) — Picasa **3.9.141.259**. Feltárva: 2026-08-06.

Ez a fájl **a Picasa saját, gépi olvasásra szánt szűrő-definíciója**: mind a
**84 szűrő** azonosítója, UI-neve, üzemmódja, csúszkáinak *neve,
tartománya, eltolása és alapértéke*, valamint a 33 „Glimmer" (Picnik-örökös)
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
| `tint` színparaméter-anomália (Nyitva 4) | `tint` = `colorwheel version="0"`, `ansel` = `version="1"` — **két külön színkódolás** |

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
| `PicnikFocalPixelate` | Focal Pixelate | effect | fullres | ld. 4. pont | — | puck |
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
`dir_tint` `ffffffff` (8 hex). A két szűrő `colorwheel` **verziója
különbözik** (`version="0"` vs `version="1"`) — ez a legerősebb eddigi nyom
a `filters-decoded.md` „Nyitva 4" (tint R=0 anomália) ügyében: a v0-s
színkerék más kódolással ír. A parszernek **változó hosszú** hex-színt kell
elfogadnia.

## 4. Glimmer-effektek — a teljes csővezeték

A 33 „Glimmer" effekt (a Picnik-felvásárlásból örökölt réteg) `<effect>`
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
  a natív szűrők mintájára; a `PicnikFocalPixelate`-ra nincs valós mintánk.

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
| `LocalContrast` | Radius 1,3–40 (15), Contrast 1–3 (1,5) |
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
| `ReanimatedEyeColor` | Blur 0–30 (6), Fade 0–100 (20) + ecset (festhető maszk) |
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

- **`Vignette`** és **`Matte`**: ugyanaz a művelet (`GlowImageOperation`
  `innerglow=true`), csak fekete vs fehér színnel és más alapértékekkel.
  `xblur = yblur = Blur · 0,02 · max(W,H) / 4`, `strength = Strength`.
  **Ez a `filters-decoded.md` „Nyitva 2" pontjának megoldása** — a korábban
  csak *mért* radiális profil mögötti tényleges modell.
- **`HDR`** = `LocalContrastImageOperation(Radius, Strength)` — semmi más.
  A `LocalContrast` effekt ugyanezt bontja ki explicit lépésekre:
  `orig − blur(r)`, `× Strength`, visszaadás — klasszikus unsharp-jellegű
  helyi kontraszt.
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

### 4.5 A művelet-készlet — mind a 31 `imageOperations:` művelet

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
