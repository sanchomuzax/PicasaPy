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

##### A blur ÁTVÁLTÓJA (`0x00bb89b0`) — a gyakorlatban AZONOSSÁG

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

**A gyakorlatban ez azonosság.** Reális blur-értékre `p < 255`, tehát
`k = 1` és `X = 100/p`; a `X > 3` feltétel ekkor `p < 33,33`. A
`filterdesc.xml` Glow-hívásainak blur-értékei ennél jóval kisebbek ⇒
**a függvény pontosan `1,0`-t ad vissza, a képmérettől FÜGGETLENÜL.**

| tartomány | visszatérés |
|---|---|
| `p < 33,33` | **1,0** ← minden filterdesc-beli Glow ide esik |
| `33,33 ≤ p < 255` | `100 / (3·p)` |
| `p ≥ 255` | `k = 255/p`, `X = ((100+d) − d·k)/p`, majd a fenti feltétel |

⇒ A maszképítőbe érkező `b` érték a **hívó saját blur-paraméterével**
arányos, nem a képmérettel — a méretfüggést tehát **nem itt** kapja meg.

**Bizalmi fok: megerősített** (a függvény mind a 165 bájtja elolvasva, mind
az öt konstans kiolvasva). ⚠️ Amit ez **nem** mond meg: hogy a
`0x00bb914d` / `0x00bb9167` második szorzásában szereplő két bemenő
paraméter a hívási lánc melyik szintjéről jön — az a `0x00bb8f70` hívóinak
kérdése, nem ezé a lapé.

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
> A fenti lánc szerint ott nem lehetne jelvény. Ez **nyitott ellentmondás**,
> jegy: **#2125**.

**Bizalmi fok:** a `mode`→egész tábla, a `FilterDesc+4` írása, a jelvény
feltétele és a 36 elemű csempe-tábla **megerősített** (közvetlen kiolvasás).
A „három jelvény, mind az 1. effekt-fülön" **következtetés** a fentiekből —
a negyedik megfigyelés ellentmondása feloldatlan.

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

**Amit ez NEM mond meg:** hogy a `rainbow` ALT-os ágát őrző globális
kapcsoló (`cmp byte ptr [0xd67849]`, `0x005d672b`) mikor nem nulla. Amíg ez
nincs kimérve, a `rainbow` elérhetősége **feltételes** — a mondat
pontosítását ez nem érinti (a `radtint` és az `autobacklight` önmagában is
megcáfolja a kizárólagos tagadást), de a felhasználónak szóló „hogyan hívd
elő" leírás ezen múlik. Nyitott kérdés.

**Bizalmi fok: megerősített** a három út és a kétféle módosító
(közvetlen kiolvasás + diszasszemblálás); **nyitott** a `0x00d67849`
kapcsoló feltétele.

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
- A `QuantizePalette` alapértékei viszont **mérve vannak**: `Steps` = 255,
  `Depth` = 2 (`0x00bb5aed`, `0x00bb5b1d`) — a tényleges kvantálást a
  `0x00bb5b60` (1510 b) végzi, az még feltáratlan.

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

## ⭐ NÉGY Glimmer-művelet KIMÉRVE — `IR`, `MultiplyColorMatrix`, `EdgeDetectionB`, `TwoTone` (2026-09-03, #2211)

Az előző szakasz horgonyt adott mind a 34 művelethez. Ez a szakasz **négyet
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

**Ami NINCS mérve:** mit csinál a gyerekművelet a `100 − detail` értékkel.

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

*Bizonyítottsági fok: **megerősített** mind a négy leletre (kiolvasott
utasítások és beolvasott konstansok); az `EdgeDetectionB` gyerekműveletének
tartalma és a `TwoTone` megálló-pozíciói **nincsenek mérve**.*
