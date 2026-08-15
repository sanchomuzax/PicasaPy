# Szűrő-visszafejtés — golden-elemzés eredményei

Forrás: **Picasa 3.9.141 Build 255** (Windows 10) golden-exportok a
`tools/golden/make_golden_kit.py` kitből; elemzés:
`tools/golden/analyze_goldens.py` + `analyze_goldens2.py` →
LUT-ok: `research/golden-analysis/luts.json`.

Módszertan: szintetikus chartok (0–255 szürke rámpa, RGB rámpák, színmező,
sakktáblák) + valódi fotók; a Picasa exportja („Use Original Size / Maximum")
gyakorlatilag veszteségmentes (újratömörítési alapzaj: |Δ|≈0,04).

## 1. kör — MEGFEJTVE ✅

### `crop` renderelési szabály (KRITIKUS spec-javítás)

A `filters=crop64=1,<hex>;` **önmagában NEM vág** — csak a szerkesztési
történet része. A tényleges vágást a képszekció külön kulcsa hajtja:

```
[kep.jpg]
crop=rect64(<hex>)
filters=crop64=1,<hex>;...
```

A PicasaPy-nak íráskor MINDKETTŐT írnia kell; olvasáskor a `crop=` az érvényes.
(A tilt ezzel szemben a filters-láncból közvetlenül renderelődik.)

### `bw` = Rec.601 luma

Mért súlyok az RGB rámpákból: R **0,3005**, G **0,5877**, B **0,1102**
(Σ=0,998) → a szabványos Rec.601 együtthatók (0,299 / 0,587 / 0,114).
Implementáció: `gray = 0.299·R + 0.587·G + 0.114·B`, csatornánként visszaírva.

### `finetune2=1,p1,p2,p3,p4,p5` — mind az 5 paraméter azonosítva

| # | Paraméter | Bizonyíték |
|---|---|---|
| p1 | **Fill light** (0..1) | LUT-ja *azonos* az önálló `fill` szűrőével (b025≡fill025 stb.) |
| p2 | **Highlights** (0..1) | 1,0-nál a teljes rámpa fehérbe csap |
| p3 | **Shadows** (0..1) | 1,0-nál a teljes rámpa feketébe nyomódik |
| p4 | **Semleges szín pipetta** (AARRGGBB hex) | meleg-szürke (ffccc6b2) megadásakor kékkel kompenzál (ΔB +11,4, ΔR −5,4) |
| p5 | **Színhőmérséklet-csúszka** (előjeles!) | −0,5: ΔB +20/ΔR −16 (hűtés); +1,0: ΔB −20/ΔR +7 (melegítés) |

Buchinger „brightness"-nek hitte a p1-et — valójában fill light; a p5-öt
(color temp) pedig ő nem azonosította.

### `finetune` (v1) viszonya a v2-höz

- p1 (fill): **bitre azonos** a v2-vel (max|Δ|=0).
- p5 (temp): eltér (max|Δ|≈10 a ±0,5 sweepnél) — a v1 temp-skálája más.
  → külön LUT/együttható kell a v1-hez.

### `fill=1,s` — fill light görbecsalád

Árnyék-emelő, fehérpont-tartó görbék (ki(255)=255 mindig):

| s | ki(32) | ki(128) | ki(224) |
|---|---|---|---|
| 0,25 | 45,7 | 145,6 | 228,6 |
| 0,50 | 69,7 | 168,6 | 234,6 |
| 0,75 | 107,7 | 194,0 | 240,0 |
| 1,00 | 162,7 | 218,0 | 243,0 |

A pontos analitikus alak illesztése hátravan (LUT-ok mentve); addig a mért
LUT-interpoláció is használható implementációként.

### `autolight` / `autocolor` algoritmus-típus megerősítve

A teljes tartományt (0–255) lefedő, semleges szürke rámpán MINDKETTŐ
**no-op** (Δ=0,0) →
- `autolight` = hisztogram-végpont széthúzás (full-range bemeneten nincs dolga);
- `autocolor` = fehérpont-alapú színkorrekció (semleges bemeneten nincs dolga).
A pontos paraméterek (percentilek, klip-küszöbök) a 2. körben, korlátozott
tartományú chartokkal mérendők.

### `enhance` (I'm Feeling Lucky)

Full-range rámpán is aktív: enyhe, csúcsfény-súlyozott emelés
(Δ@32=+2, Δ@128=+9, Δ@224=+15) → nem csak hisztogram-széthúzás; additív
tónusgörbe-komponense van. Pontos modell: 2. kör.

### `sat=1,s` — telítettség (előjeles)

HSV S-arányok a színmezőn: −0,333→0,742× · +0,25→1,232× · +0,5→1,390× ·
+1,0→1,583× — nem lineáris szorzó, telítődő görbe; illesztés a 2. körben.

## 2. kör — MEGFEJTVE ✅ (fix-kit + további elemzés)

### crop pixel-kerekítési szabály (fix-kit exportokból igazolva)

```
x0 = round(left · W)    x1 = round(right · W)    szélesség = x1 − x0
y0 = round(top · H)     y1 = round(bottom · H)   magasság  = y1 − y0
```

Mindhárom crop-variáns és a 3 valódi lánc (chainB/D/E) kimeneti mérete
pixelre egyezik e szabállyal. Láncban a crop koordináták mindig az EREDETI
képméretre vonatkoznak (tilt után is).

### `sepia` — mért csatornagörbe

Szürke bemenetre (g) nem-lineáris, csatornánként eltérő görbe (a teljes
LUT mentve; közelítő lineáris szakasz):

- sepia: R≈0,82g+58 · G≈0,86g+35 · B≈0,90g+15 (sötétben széttart,
  fehér felé összezár) — implementáció: mért 3-csatornás LUT.

### `warm` — beégetett tábla, PONTOS (#611)

A `warm` NEM mérés — a natív `0x0090c040` munkafüggvény beégetett,
256×3 elemű csatornánkénti táblájából (`0x00d33b70`, PE-fájloffszet
`0x933b70`) a bináris visszafejtésével kinyert, pixelpontos leképezés
(ld. `docs/specs/picasa-native-filter-workers.md` 2.8. pont). Szürke
bemenetre (g) a durva közelítése R≈0,89g+19 · G≈0,88g+1 · B≈0,93g−16 volt —
ezt a #611 óta a pontos tábla váltotta fel.

### `grain2` — sztochasztikus, pixelhűen NEM reprodukálható

Átlagban identitás (meredekség 1,000, eltolás −2,7), zérus körüli additív
zaj véletlen maggal. Elfogadási teszt: statisztikai (zaj-σ, spektrum),
nem pixel-diff. A round-trip elvet nem érinti (a filters-sztring őrzendő).

### `sat` — gain-tábla (HSV S-térben, klippeletlen pixeleken mérve)

| s | −0,333 | +0,25 | +0,5 | +1,0 |
|---|---|---|---|---|
| gain | 0,683 | 1,399 | 1,729 | 2,241 |

Nem 1+s; valószínűleg nem HSV-térben dolgozik (YCbCr-chroma gain gyanú) —
pontosítás a 3. körben.

### `fill` — negatív eredmények (fontosak!)

- NEM adaptív-gamma család (legjobb illesztés RMSE 14,5/255 — elvetve).
- NEM önkompozíciós (fill025∘fill025 ≠ fill050, max|Δ|=10).
- NEM egyetlen mestergörbe s^β keveréke (átlagban s^1,26 stimmel, de
  pontonként max|Δ|=22 — elvetve).
- → **Megoldás: sűrű s-sweep a 3. kit-körben** (s=0,05..1,0, 20 lépés,
  csak chart_ramp) → 2D LUT (s×256), köztes s-re interpoláció.
  A finetune2 p1 = fill s=1,0-nál bitre azonos (max|Δ|=0) → közös 2D LUT.

## 3. kör — MEGFEJTVE ✅ (sweep-kit; elemzés: `analyze_goldens3.py`)

### `autolight` — TELJESEN MEGFEJTVE

**Globális min–max lineáris széthúzás**, minden csatornára KÖZÖS
transzformációval (a színegyensúly megmarad):

```
gmin = min(kép összes csatornája)   gmax = max(...)
ki = clip( (be − gmin) · 255 / (gmax − gmin) )
```

Mind a 4 korlátozott rámpán pontos (ki(min)=0, ki(max)=255, közép lineáris);
a cast-rámpák csatorna-deltái tizedre igazolják a közös (nem csatornánkénti)
skálázást. Percentil-klippelés a szintetikus chartokon nem volt megfigyelhető.

### `enhance` (I'm Feeling Lucky) — SZERKEZETE MEGFEJTVE

```
enhance(kép) = fixLUT( autolight_stretch( autocolor(kép) ) )
```

A fix tónusgörbe (reziduál) chart-függetlenül azonos (max|Δ|=2–3/255, átlag
0,6 — JPEG-zajon belül); mentve: `research/golden-analysis/enhance_residual.json`.
Minták: 16→18,7 · 64→71,3 · 128→142,7 · 192→214 · 240→255 (enyhe világosítás,
csúcsfény-emelés). Hátralévő függés: az autocolor pontos modellje (ld. lent).

### `fill` — MEGOLDVA (2D LUT)

20 lépéses s-sweep lemérve (`luts3.json: fill2d`); szomszéd-görbék közti
lineáris interpoláció max hibája **1,25/255** → tetszőleges s-re ±1 pontosságú
implementáció LUT-interpolációval. A `finetune2` p1 ugyanez a LUT.

### `autocolor` — RÉSZBEN (csillapított fehéregyensúly)

Semleges rámpán no-op; öntetes rámpán a színcsatornákat a szürke felé húzza,
de NEM teljesen (pl. warmcast közép (135,142,157)→(141,145,146)). Csillapított
szürkevilág/fehérpont-korrekció; pontos modell (súlyozás, csillapítás) a 4.
körben mérendő célzott próbákkal.

### highlights / shadows / színhő sweep-ek — LUT-ok mentve

- h/s: 6-6 görbe (`luts3.json: hs`) — interpolációs implementációhoz elég
  sűrű; jelleg: highlights = fehérpont-húzás (h040-nél 192→255), shadows =
  feketepont-húzás.
- színhő (p5): erősen **aszimmetrikus** — hűtés (−1: ΔB+91/ΔR−50) sokkal
  erősebb, mint melegítés (+1: ΔB−20/ΔR+8); csatorna-eltolások mentve.

### Effektek a rámpán (nyers mérések)

- `tint` (szín=ffff): R-csatorna nullázódik, B=G marad → a 16 bites
  színparaméter értelmezése tisztázandó.
- `ansel`: semleges (B=G=R), enyhe középemelés — B/W + tónusgörbe.
- `glow` v1/v2: középemelés (144/151) — térbeli komponens elemzése hátravan.
  **Felülírva (#668):** a 144/151 a Gauss-modellhez tapadt; a `chart_color`
  golden sík szürke foltjain a VALÓDI érték **128 → 141,9 (v1)** és
  **128 → 148,9 (v2)**, és a térbeli komponens is megvan (natív IIR-mag).
- `Vignette`: átlagos sötétedés a sávban — térbeli maszk elemzése hátravan.

## 4. kör — MEGFEJTVE ✅ (elemzés: `analyze_goldens4.py`)

### `tilt=1,p,skála` — TELJESEN MEGFEJTVE

- **Szög: θ = p · 0,2 radián** (= p·11,459°) — négy paraméterértéken
  ellenőrizve (mért arány 11,46–11,50°/egység). Pozitív p = a kép tartalma
  az óramutató járásával ellentétesen fordul (ORB-mérés szerint −θ affin).
- **Autoskála: s = cos θ + (W/H)·sin θ** (fekvő képnél; a keret kitöltéséhez) —
  mérve: p=0,2 → 1,0702 (számított 1,0704), p=0,05 → 1,0178 (1,0178). A kimeneti
  képméret változatlan. A 2. ini-paraméter (skála) a teszteinkben 0 volt;
  szerepe további mérést igényel, ha nem-nulla értékkel találkozunk.

### `unsharp` / `unsharp2` — MEGFEJTVE (közelítő modell)

- **`unsharp=1` (v1, param nélkül) = `unsharp2=1,0.600000`** — bitre azonos
  kimenet (átlag|Δ|, max, szórás egyezik). Ismételt alkalmazás kumulatív.
- Modell: Gauss-alapú unsharp mask, **σ ≈ 1,0 px**, erősítés ≈ **1,21·s**
  (RMSE 2,2/255 valódi fotón). A pontos kernel finomítása nyitva (nem tökéletesen
  Gauss); B/W teszteknél figyelem: telített értékeken a túllövés klippel.

### `Vignette=1,35.0,1.4,0.0,00000000` — maszk lemérve

Multiplikatív radiális maszk: közép 1,000 · r≈0,25: 0,994 · r≈0,45: 0,729 ·
r≈0,65: 0,328 · sarok: 0,250. (r = képmérettel normált távolság a középponttól.)
A paraméterek (35=belső sugár %, 1,4=erősség?) → analitikus illesztés nyitva;
addig a mért radiális profil használható.

### `autocolor` — csillapított lineáris fehéregyensúly (részleges)

Csatornánkénti lineáris korrekció (ki = a·be + c, |c|<1,5):
warmcast: R×0,936 / G×1,021 / B×1,058; bluecast tükörképe (R×1,032 / B×0,936).
A gainek a teljes szürkevilág-korrekció ~60–90%-a — a pontos csillapítási
szabály (gray-world vs fehérpont-alapú) még nyitott.

## 5. kör — a 4–5. effekt-fül `filters=` kulcsai AZONOSÍTVA ✅ (#190)

A felhasználó Windows-os Picasa 3.9-éből, az effekt-kit alap-alkalmazásaiból
(2026-07-23). Minden effekt ini-alapú; a színparaméterek formátuma
`00RRGGBB` hex. A paraméterek JELENTÉSE (csúszka-leképezés) még nyitott —
a 2. kör deríti fel előre írt ini-variánsokkal, gépi úton.

### 4. fül (zöld ecset)

| Magyar UI-név | Kulcs | Alapértelmezett minta |
|---|---|---|
| Infravörös film | `IR` | `IR=1,0.000000;` |
| Lomo-szerű | `Lomo` | `Lomo=1,50.000000,0.000000;` |
| Holga-szerű | `Holga` | `Holga=1,70.000000,30.000000,0.000000;` |
| HDR-szerű | `HDR` | `HDR=1,20.000000,3.000000,0.000000;` |
| Kinemaszkóp | `Cinemascope` | `Cinemascope=1,0;` |
| Orton-szerű | `Orton` | `Orton=1,25.000000,50.000000,0.000000;` |
| 60-as évek | `Sixties` | `Sixties=1,20.000000,00ffffff,0;` |
| Színinvertálás | `Invert` | `Invert=1;` |
| Hőtérkép | `HeatMap` | `HeatMap=1,0.000000,0.000000;` |
| Áttűnés | `CrossProcess` | `CrossProcess=1,0.000000;` |
| Poszterizálás | `QuantizePalette` | `QuantizePalette=1,8.000000,80.000000,0.000000;` |
| Kéttónusú | `TwoTone` | `TwoTone=1,0.000000,20.000000,0.000000,00004488,00ffff00;` |

### 5. fül (kék ecset)

| Magyar UI-név | Kulcs | Alapértelmezett minta |
|---|---|---|
| Felpörgetés | `Boost` | `Boost=1,50.000000;` |
| Lágyítás | `Soften` | `Soften=1,50.000000,50.000000;` |
| Képpontnagyítás | `Pixelate` | `Pixelate=1,20.000000,9.000000,0.000000;` |
| Fókusznagyítás | `FocalZoom` | `FocalZoom=1,0.500000,0.500000,50.000000,50.000000,50.000000,0.000000;` |
| Ceruzarajz | `PencilSketch` | `PencilSketch=1,2.000000,100.000000,0.000000;` |
| Neon | `Neon` | `Neon=1,0.000000,00ff0000;` |
| Képregény | `Comicize` | `Comicize=1,20.000000,50.000000,50.000000;` |
| Szegély | `Border` | `Border=1,20.000000,5.000000,0.000000,00000000,00ffffff,0.000000;` |
| Árnyékvetés | `DropShadow` | `DropShadow=1,4.000000,90.000000,10.000000,00000000,00ffffff,30.000000;` |
| Múzeumi matt | `MuseumMatte` | `MuseumMatte=1,25.000000,40.000000,001a0e03,00f0eae4;` |
| Polaroid | `Polaroid` | `Polaroid=1,5.000000,00e2e2e2;` |

Megfigyelések: a `FocalZoom` első két paramétere 0.5,0.5 — valószínűleg
képarányos középpont (x,y), a redeye/crop régiókkal rokon minta; a
`Cinemascope` és `Sixties` utolsó `0` paramétere tizedesjegyek nélküli
(eltér a szokásos `%.6f` formátumtól — a round-trip ezt is bitre őrzi).
Round-trip tesztek a valódi mintákkal: `tests/ini/test_filters.py`
(`TestEffektFulKulcsok190`).

## Golden-verdiktek (#115/#279, 2026-07-23) — mely szűrő mennyire pixelhű

**VÉGLEGES mérés** a `compare_render.py --luts` futásából a kit3 **saját,
eredeti Picasa-exportjai** ellen (amikből a `luts3.json` készült; a
felhasználó megtalálta: `research/testdata/golden-kit3`). 0 „hiányzik",
75 összevetés. Összegzés: **pixelhű 4 · közelítés 32 · eltér 39.** A
verdikt sok szűrőnél a paraméter erősségével romlik (a LUT-közelítés a
végpontok felé tér el).

| Szűrő | Eredmény (dE_átlag tartomány) | Állapot |
|---|---|---|
| `autocolor` | pixelhű→közelítés (0.00–1.55) | ✅ kész (színöntetnél kis eltérés → Nyitva 1) |
| `autolight` | mind közelítés (0.20–0.74) | ✅ kész |
| `glow` | közelítés (1.85 → **0,15–1,06** #668) | ✅ kész |
| `enhance` | közelítés, színöntetnél eltér (0.49–3.02) | ✅ jó (az autocolor-komponens húzza) |
| `sat` | negatív jó, pozitív romlik (0.70–12.71) | ⚠️ pozitív telítés pontosítandó |
| `finetune2` | h/s alacsony jó, hő-extrém eltér (0.94–24.9) | ⚠️ hőmérséklet-tengely pontosítandó |
| `fill` | csak gyenge erősségnél jó (1.03–6.56) | ⚠️ 2D-LUT az erősséggel driftel |
| `glow2` | eltér (2.68) → **közelítés (0,18–1,19)** (#668) | ✅ kész |
| `radblur` | eltér (3.18) → **közelítés (0,09–0,68)** (#668) | ✅ kész |
| `Vignette` | eltér (4.65) | ❌ analitikus modell (Nyitva 2) |
| `ansel` | eltér (5.60) | ❌ |
| `dir_tint` | eltér (9.36) | ❌ |
| `tint` | eltér (20.63) — legnagyobb | ❌ színparaméter-formátum (Nyitva 4) |

(Geometria/él/tónus — `crop64`, `tilt`, `unsharp/2`, `bw` — a `chart_detail`
kontroll-méréseiben pixelhű; ezek a kit3-ban nem szerepelnek.)

**Módszertani zárás (#279):** a kit3 exportjai megvannak
(`research/testdata/golden-kit3/export`), a mérés a valódi kalibrációs
goldenek ellen futott. A harness (#115) és a LUT-os validálás (#279)
lezárva; a fenti „eltér"/„⚠️" szűrők render-pontosítása a Nyitva-listán,
súlyosság szerint (tint → dir_tint → sat+ → finetune2-hő → fill → …).

## Implementációs státusz — MIT MENNYIRE HISZÜNK (2026-07-30, #329/#330/#332)

A felhasználó jogos kifogása után („Kizárt, hogy minden effekt kalibrált"):
ez a tábla **őszintén** megmondja, melyik effekt mögött áll mérés, és melyik
mögött csak szakirodalmi közelítés. A UI egyik effektnél sem sugallja, hogy
Picasa-hű lenne.

| minőség | mit jelent | effektek |
|---|---|---|
| **MÉRT** | golden-kitből mért LUT/paraméter, pixelhű vagy közelítés-verdikttel | `crop64`, `tilt`, `bw`, `enhance`, `autolight`, `autocolor` (részleges), `fill`, `finetune`/`finetune2`, `unsharp`/`unsharp2`, `sepia`, `sat`, `grain2` (statisztikai) |
| **MÉRT, DE ELTÉR** | van mérés, de a verdikt „eltér" — javítandó | `tint` (ΔE 20,6), `dir_tint` (9), `ansel` (5,6) |
| **MEGFEJTVE a filterdesc.xml-ből (#381)** | a lépéssorrend és a számértékek a Picasa saját `filterdesc.xml` `<effect>` csővezetékéből jönnek — nem golden-méréssel „visszafejtett" közelítés, hanem a Picasa TÉNYLEGES lépéssora (az alacsony szintű kernelek, pl. Gauss-elmosás, a szokásos megfelelőjükkel) | `Vignette`, `Matte`, `HDR`, `LocalContrast`, `Invert`, `CrossProcess`, `Sixties`, `Cinemascope`, `Orton`, `PencilSketch`, `HeatMap`, `NightVision`, `Holga`, `Lomo`, `Neon`, `Boost`, `Soften`, `Pixelate`, `QuantizePalette`, `TwoTone`, `Border`, `RoundedEdges`, `DropShadow`, `MuseumMatte`, `Polaroid`, `PicnikGrain` |
| **MEGFEJTVE A BINÁRISBÓL (#566)** | a `filterdesc.xml` csak a paraméterNEVEKET és a FIX konstansokat adja, de a `Picasa3.exe` statikus visszafejtése a teljes belső kernelt feltárta (`glimmer::IRImageOperation`, RTTI/vtable `0xcf0a14`, ctor `0xbc3d80`, feldolgozás `0xbc3f50`) | `IR` |
| **MEGFEJTVE, DE ECSET-MASZK NÉLKÜL (#381)** | a csővezeték/paraméterezés egzakt, de a Picasa ecsettel kijelölt régióra hatna — a PicasaPy-nak nincs ecset-eszköze, ezért a TELJES KÉPRE fut (jelezve a `ChainReport.range_warnings`-ban) | `PicnikTint`, `ReanimatedEyeColor` |
| **KÖZELÍTŐ (mérés nélkül) — #381 után is maradt** | a hatás jellege alapján, szakirodalomból — sem golden-mérés, sem filterdesc-pontosítás nincs még bekötve | — |
| **MEGFEJTVE A FILTERDESC + NATÍV KÓDBÓL, EGY RÉSZLET NYITVA (#569, #570)** | a csővezeték (lépések, paraméter-sorrend, képletek, keverési módok) egzakt; egyedül a mintavételezés perem-/interpolációs szabálya vár golden-összevetésre | `Comicize`, `FocalZoom`, `PicnikFocalPixelate` |
| **KÖZELÍTŐ (másik, mért v2-modell újrahasznosítva) — #347 lezáró audit (2026-08-06)** | a filterdesc szerint a v1/v2 pár paraméter nélküli, azonos "oneclick" család (nincs csúszka/szín, ami megkülönböztetné őket) — a v1-re önmagára nincs golden-mérés, ezért a már mért v2-modellt futtatjuk rá | `grain` (v1, a `grain2` modelljét használja) |
| **PONTOS** | matematikailag egyértelmű, mérés sem kell, vagy a natív kódból kinyert beégetett tábla | `Invert` (255−x, #381 óta a `glimmer_ops.invert_curve`-ön át), `warm` (256×3 beégetett tábla a `0x0090c040`/`0x00d33b70`-ből kinyerve, #611 — ld. `docs/specs/picasa-native-filter-workers.md` 2.8) |
| **NEM EFFEKT — no-op jelző-token** | a lánc érvényes tagja, de nem képi művelet, csak metaadat (szerkesztési előzmény/mozi-vágás), a `_NOOP_MARKERS`-en át csendben elnyelődik, round-trip megőrzött | `picnik=1;` (Creative Kit-szerkesztés jelölője), `redeye=1;`/`retouch=1;` (history-jelzők) |
| **MEGFEJTVE A BINÁRISBÓL, EGY PARAMÉTER KALIBRÁLATLAN (#565)** | az algoritmuscsalád és a pixelművelet a natív kód visszafejtéséből egzakt, egyetlen csúszka affin leképezése maradt feltételezés | `radtint` (radiális **szorzó**-tint köbös smoothstep maszkkal; a Feather affin leképezéséhez golden-pár kell) |
| **MEGFEJTVE A BINÁRISBÓL (#623)** | a natív mag EGÉSZ aritmetikája képpontra reprodukálva (hurkos referencia-újraírással hitelesítve) — nincs benne feltételezett skalár | `dir_sat` (`0x0090dbb0`), `dir_brite` (`0x0090d8b0`) |
| **MEGFEJTVE A BINÁRISBÓL ÉS VÉGIGMÉRVE (#668)** | a natív elmosó mag (`0x009dd0d0`) alá állítva, és MINDEN szabad skalár valódi Picasa-exportból mérve — 12 golden-párból 12 „közelítés", átlagos ΔE 0,09…1,19 | `glow`/`glow2` (`0x0090d4b0`: négyzetre emelő előgörbe → IIR-elmosás → screen, súly = Intenzitás), `radblur` (`0x008f8520`: IIR-elmosás + natív smoothstep sugaras maszk) |
| **MEGFEJTVE A BINÁRISBÓL, EGY SKALÁR KALIBRÁLATLAN (#623)** | a pixelművelet, a geometria és a súlytáblák a natív kódból egzaktak; egyetlen skalár az x87-veremen ment át, ezért a dekompilátum nem őrizte meg — a helyére INDOKOLT feltevés került, mérés írja majd felül (#317) | `dir_sharp` (`0x0090d600`; a rámpa horgonya `k = round((\|a\|+\|b\|)·256)` — a két natív `ABS` hívásból következtetve), `linblur` (`0x0090de10`; a „Mennyiség" → elmosási sugár leképezés a testvér `radblur` burkolójának mintájára) |

Vagyis a Glimmer-effektek (33) többsége #381 óta a `filterdesc.xml` EGZAKT
csővezetékén fut — a `RoundedEdges`, `Matte`, `NightVision` a korábbi
„exe-ből ismert, nincs mérés" kategóriából ide léptek elő. Három effekt
(egy sem) maradt KÖZELÍTŐ (a
`fullResImageWidth/Height`-explicit radiális elmosás, ill. a többágú
pontraszter-csővezeték #381 hatókörén kívül esett — ld. a jegy jelentését).
Az `IR` a **#566** óta MEGFEJTVE — nem a paraméternevekből következtetve,
hanem a natív kernel visszafejtéséből. A csővezeték: (1) színmátrix, amely
csak a ZÖLD csatornát (és az alfát) hagyja meg, (2) `x = y = 5` elmosás,
(3) a zöld glow **LIGHTEN** módban (nem SCREEN!) az EREDETI képre,
`alpha = 0,25`, (4) záró monokróm mátrix
`Y = clamp(−0,5·R + 2,0·G − 0,5·B)` — a KÉK súlya is negatív —, végül
(5) a közös Fade-keverés. A
`PicnikTint`/`ReanimatedEyeColor` egzakt csővezetéket kapott, de ecset-
eszköz híján a TELJES KÉPRE fut. A kalibráció (a maradék KÖZELÍTŐ effektekhez
és a golden-pixel-összevetéshez) a **#317**-es jegyben fut tovább.

**#347 lezáró audit (2026-08-06):** a jegy eredeti hét neve közül HAT
mostanra rendezett — `glow` (v1) golden-mérve MÉRT, `RoundedEdges`/`Matte`/
`NightVision` a #381 filterdesc-csővezetéken MEGFEJTVE, `picnik` no-op
jelzőként azonosítva, `grain` (v1) a `grain2` mért modelljét újrahasznosítva
renderel. A hetedik, `radtint` a **#565**-ben rendeződött: nem golden-mérésből,
hanem a natív kód visszafejtéséből (regisztrációs render callback `0x8f8730`,
feldolgozó mag `0x90b370`, maszk-LUT segédfüggvény `0x90aeb0`). Ezzel a #347
mind a hét neve renderel.

### `FocalZoom` és `PicnikFocalPixelate` (#570)

A #381 az XML-csővezetéket rögzítette; a natív
`glimmer::RadialBlurImageOperation` (vtable `0xcf07fc`, wrapper `0xbc24e0`,
mag `0xbcf4b0`) visszafejtése adta hozzá a hiányzó részleteket — köztük egy
VALÓDI HIBÁT is.

**Paramétersorrend:** `x, y, Impact, Radius, Hardness, Fade`. A fókuszpont
után tehát az **Impact** jön, a `Radius` **nem** a harmadik numerikus mező —
a korábbi kód innen olvasta, ezért a két csúszka hatása fel volt cserélve.

**Közös körmaszk** (mindkét effekt ugyanazt használja), teljes felbontásra
visszaskálázott sugárral:

    inner = Radius · (imageWidth / fullResWidth) · Hardness/101
    outer = Radius · (imageWidth / fullResWidth) · (2 − Hardness/101)

Belül alfa 0 (a hatás nem éri el: éles marad), kívül 1. A 101-es osztó
szándékos: `Hardness = 100` mellett is marad egy hajszálnyi átmenet. Záró
keverés: `1 − Fade/100`.

**`FocalZoom` natív kernel:** `N = min(trunc(Impact) + 5, 30)` zoomminta, a
legnagyobb zoomeltolás `floor(width · Impact / 200)` pixel.

**`PicnikFocalPixelate`:** lekicsinyítés `W/Impact × H/Impact` méretre, majd
visszanagyítás `W × H`-ra **`smoothing = false`** módban (legközelebbi
szomszéd, nem interpoláció) — ettől élesek a blokkok.

A kisbetűs, régi `focalpixelate` **nem** ez: ahhoz a vizsgált buildben nincs
natív regisztráció (#567).

**Nyitott:** a pontos perem-/interpolációs szabály a mintavételezésnél —
golden-összevetéssel rögzíthető (#317).

### `Comicize` — nyomdai féltónusos raszter (#569)

A korábbi modell **posterizálással és Canny-élkereséssel** közelítette. Ez
tévedés volt: a Picasa `Comicize`-a **nem** élkiemelő képregényszűrő, hanem
**két, egymáshoz képest fél csempével eltolt pontmaszkból** épített nyomdai
raszter (`filterdesc.xml` + a natív `glimmer::TiledImageMask`).

A csővezeték:

1. `dotSize = round(imageWidth / 70) + 1` — a csempeméret a kép
   **szélességéből** (nem a rövidebb oldalból);
2. elő-elmosás `radius = 1 + 20·BlurXY/100`, `quality = 3`, **DARKEN** módban
   visszakeverve;
3. küszöbgörbe, amelynek a **felső kontrollpontját** a `DotContrast` mozgatja:
   `90 + DotContrast·1,5`;
4. pixelesítés a csempeméretre + BW — ez adja a pontonkénti festéksűrűséget;
5. két csempézett pontmaszk-ág, `(0, 0)` és `(dotSize/2, dotSize/2)`
   eltolással; az ágak **DARKEN**-nel egyesülnek;
6. blokk-alfa: `0,5 − DotFade/200`;
7. a kész raszter **DARKEN** jelleggel az eredeti képre.

A pont sugara a tónussal nő: fekete területen a csempe tömören fedett (a
sarkokat a másik, fél csempével eltolt ág fedi le), fehéren nincs festék.

**Nyitott:** a natív pontmaszk pontos antialiasingja és peremkerekítése — a
PicasaPy egy pixelnyi lineáris átmenetet használ (`halftone._EDGE_SOFTNESS_PX`).
Ez a raszter jellegét nem befolyásolja, de a pixelhű egyezéshez
golden-összevetés kell (#317).

### `autobacklight` és a kisbetűs `focalpixelate` (#567)

Az effekt-regisztrációs tábla visszafejtése két korábbi feltételezést
pontosít:

- **`autobacklight`** — a render callback (`0x8f7cc0`) ugyanazt a
  Derítőfény-magot (`0x90ac20`) hívja, mint a `backlight`/`fill`, **fix**
  `0.25` és `1.0` argumentummal. Ez tehát **nem** adaptív automatikus
  képelemzés, hanem rögzített 25%-os derítőfény — a kikommentezett UI-súgó
  is ezt mondja: „Increases ambient lighting by 25%." A PicasaPy ezért a
  meglévő `apply_fill` primitívet hívja fix 0,25-tel; semmilyen hisztogram-
  vagy fényesség-vizsgálat nem fut.
- **kisbetűs `focalpixelate`** — a pre-Glimmer `filterdesc`-bejegyzéshez a
  3.9.141.259 build natív regisztrációs táblájában **nincs render callback
  és nincs névregisztráció**. Halott, konfigurációs maradvány, ami **nem
  azonos** az élő `PicnikFocalPixelate` Glimmer-effekttel. A lánc külön
  kulcson tartja a kettőt, a kisbetűs nevet pedig a
  `ChainReport.legacy_warnings` kimondottan halottként jelenti — ez más ok,
  mint a „még nincs modellünk".

### `radtint` — radiális szorzó-tint (#565)

A visszafejtett csővezeték:

1. a puck-kal megadott fókuszpont körül **normalizált** (tengelyenként külön
   normált, tehát elliptikus) távolság számolódik minden pixelre;
2. a fókuszpont környékén a kép **változatlan**;
3. kifelé haladva egy **1024 elemű LUT** adja a keverési súlyt; a LUT köbös
   smoothstep: `t*t*(3-2*t)`;
4. a teljes tint csatornánként `tinted = source * tint / 256` — **szorzás**,
   nem a szín FELÉ keverés (ez a lényegi különbség a `dir_tint`-hez képest),
   az alfa érintetlen;
5. az átmeneti sávban lineáris keverés fut az eredeti és a szorzott kép
   között.

**Nyitva:** a Feather csúszka pontos affin leképezése. A PicasaPy jelenlegi,
DOKUMENTÁLT feltételezése: a feather az átmeneti sáv szélessége, a
fókuszponttól mért legnagyobb távolság (`r_max`) felénél középpontosan — a
sáv `(0,5 − feather/2)·r_max`-nál kezdődik és `(0,5 + feather/2)·r_max`-nál
ér véget. Így `feather = 0` éles határt ad a fél sugárnál, `feather = 1`
végig lágy átmenetet; a fókuszpont mindig érintetlen, a legtávolabbi sarok
mindig teljes tintet kap. A pontosításhoz golden-pár kell (#317).

## 6. kör — a Picasa SAJÁT szűrő-definíciója előkerült ✅ (2026-08-06)

A `research/copy_Picasa_3_7/Picasa3/runtime/**filterdesc.xml**` a Picasa
gépi olvasásra szánt szűrő-regisztere: mind a 84 szűrő azonosítója, UI-neve,
üzemmódja, **csúszkánként a név / tartomány / eltolás / alapérték**, és a 33
Glimmer-effekt **teljes képfeldolgozó-csővezetéke** (görbék, keverési módok,
csúszka→paraméter képletek).

**Teljes feldolgozás: [`filterdesc-registry.md`](filterdesc-registry.md).**
Ami ebből közvetlenül ide tartozik:

- A `.picasa.ini`-be a **`[−offset .. range−offset]`** tartományú érték
  kerül. Ezért `sat`, `tilt`, `finetune2`-hőmérséklet előjeles `[−1..1]`;
  `finetune` (v1) hőmérséklete viszont `[−0,5..0,5]` — **a v1/v2 eltérés
  tehát puszta skálakülönbség (2×), nem külön algoritmus.** (Mérési
  megerősítés: 9. Nyitva-pont.)
- `highlights`/`shadows` valódi UI-tartománya **0..0,48**, nem 0..1 — a
  sweepjeink ezen túlnyúltak.
- `unsharp` (v1) Amount felső korlátja 1,0, `unsharp2`-é **3,0**.
- A `Vignette` (és a vele azonos motorú `Matte`) modellje: **belső ragyogás**
  (`GlowImageOperation innerglow`), `sugár = Blur·0,02·max(W,H)/4`,
  `strength` = a 2. paraméter, `alfa = 1 − Fade/100`.
- ~~A `tint` `colorwheel version="0"`, az `ansel` `version="1"` — két külön
  színkódolás~~ — **MEGCÁFOLVA (2026-08-15)**: a `version` a szerkesztőpanel
  **színválasztó kerekének sorszáma** (`editpanel/colorwheel0` / `…1`), nem
  színkódolás. Ld. lent a `tint` szakaszt.
- A Glimmer-effektek ini-sorrendje: **numerikusok (max 3) → színek →
  maradék numerikus → jelölőnégyzetek egész számként**; a jelölőnégyzet
  magyarázza a korábban rejtélyes „tizedesjegy nélküli `0`" paramétert
  (`Cinemascope`, `Sixties`).

## 7. kör — `enhance`/`autofix` ÚJRAMEGFEJTVE, a 3. kör modellje ELVETVE (#535, 2026-08-10)

A 3. körben leírt `enhance = fixLUT(autolight_stretch(autocolor(kép)))`
szerkezet **tévesnek bizonyult**: egy 12 kép-páros, vegyes jellegű
referenciakészleten (alul-/túlexponált, fakó, éjszakai, napfényes —
`sanchomuzax/picasapy-agent` privát repó `referencia/imfeellucky/`) mérve
az akkori `apply_enhance` átlagosan **17,59** csatorna-eltérésre volt a
valódi Picasa-kimenettől.

**A helyes modell** (mind a 36 csatornára — 12 kép × 3 — R² = 0,9995–1,0000
illesztéssel igazolva): **csatornánként KÜLÖN** lineáris szinthúzás,
**nem** a 3. körben feltételezett `autocolor`+`autolight`+reziduál-LUT
lánc:

```
ki = (be − lo) · 255 / (hi − lo)        csatornánként külön lo/hi
```

Pontosan lineáris — nincs benne gamma, S-görbe, helyi kontraszt vagy
árnyék-/csúcsfény-emelés (a 3. kör „enyhe, csúcsfény-súlyozott emelés"
megfigyelése tehát a hibás modell műterméke volt, nem valódi Picasa-jegy).
Fontos tulajdonságok:

- **Azonosság-eset**: ha egy csatorna már kihasználja a teljes
  tartományt (`lo=0`, `hi=255`), a Picasa NEM nyúl hozzá (mért: „Night
  Seascape" mindhárom csatornája meredekség 1,000, eltolás 0,0).
- A vágási pontok **nem** fix percentilek — a Picasa a hisztogramban
  **darabszám-küszöbbel** keresi a fekete-/fehérpontot (a mért végpontok
  0%-tól 16%-ig szóródnak). A #539 óta az implementáció
  (`picasapy.render.ops` `apply_channel_levels_stretch`) a natív
  `0x009db610` geometriáját futtatja:
  - a hisztogram a kép **középső 90% × 90%**-áról készül (a perem kimarad),
  - a vágási küszöb a **teljes kép képpontszámának 1/200-a**, mindkét
    végén **azonosan** (az aszimmetrikus változatok a mérésen rosszabbak),
  - a nyújtás bemeneti tartománya nem mehet **58 szint alá**
    (`_MIN_STRETCH_SPAN`) — ez a natív `gain` felső korlátja.

  A 12 referencia-páron ez **2,68 → 2,61**-re viszi az átlagos eltérést;
  a vágópontok maguk pedig a mérttel egyeznek (fehérpont-eltérés átlaga
  3,85, feketeponté 2,05 szint, 36 csatornán).
- Az `AutoFix` (a Glimmer-effektek — Holga, NightVision, PencilSketch,
  Sixties, Cinemascope — belső újrahasznált lépése) **ugyanezt a modellt**
  kapta, az `autocolor`+`autolight` páros helyett.

**Amit ez NEM érint:** az `autolight` (globális, KÖZÖS min-max
széthúzás — „Auto Contrast" menüpont) és az `autocolor` (csillapított
szürkevilág-korrekció — „Auto Color" menüpont) önálló szűrőkként
VÁLTOZATLANOK maradtak; ezekhez továbbra sincs pontosabb mérés, mint a
3–4. körben rögzített. Csak az `enhance`/`AutoFix` BELSŐ szerkezete
(hogy micsoda a lánc) bizonyult tévesnek.

## 8. kör — a négy Finomhangolás-csúszka VALÓDI fotón újramérve (#551, 2026-08-11)

Forrás: a tulajdonos referencia-készletei (`sanchomuzax/picasapy-agent`:
`referencia/deritofeny/`, `referencia/szinhomerseklet/`,
`referencia/finomhangolas/`) — **egy valódi fotó**, csúszkánként több
állásban, a valódi Picasa 3.9 kimenetével. Ez döntő különbség a korábbi
körökhöz képest, ahol a mérés SZINTETIKUS SZÜRKE RÁMPÁKON folyt: szürke
rámpán a pixel világossága megegyezik a csatorna-értékkel, így egy
világosság-vezérelt művelet **csatornánkénti tónusgörbének látszik**. Ez
vezetett félre a `fill` 2D-LUT modelljénél (3. kör).

Átlagos csatorna-eltérés a Picasa kimenetétől (a JPEG-zaj szintje ~1):

| csúszka | korábbi modell | mért modell |
|---|---|---|
| Kiemelések (max) | 23,15 | **1,06** |
| Kiemelések (fél) | 10,77 | **1,11** |
| Árnyékok (max) | 19,41 | **0,76** |
| Árnyékok (fél) | 11,76 | **0,92** |
| Derítőfény (max) | 18,10 | **5,89** |
| Derítőfény (50%) | 6,65 | **3,64** |
| Színhőmérséklet (leghidegebb) | 20,94 | **5,08** |
| Színhőmérséklet (legmelegebb) | 4,43 | **1,17** |

### Kiemelések / Árnyékok — zárt képlet

A nevük félrevezető: egyik sem csúcsfény-mentés vagy árnyék-emelés, hanem a
**fehér- illetve feketepont mozgatása**. A mért meredekség 0,48-as állásnál
1,9235 / 1,9244; a képlet 1/(1−0,48) = 1,9231.

```
Kiemelések(h): ki = clip( be / (1 − h) )
Árnyékok(s):   ki = clip( (be − 255·s) / (1 − s) )
```

Ez egyben megmagyarázza a `filterdesc.xml` furcsa **`[0..0.48]`**
paramétertartományát mindkét csúszkánál: a paraméter azt mondja meg, a
szélső pont a skála hány százalékával mozdul el. A PicasaPy csúszkái is
eddig futnak, hogy a mentett ini-érték Picasa-azonos legyen.

### Derítőfény — világosság-vezérelt hozzáadás, NEM tónusgörbe

`ki = clip( be + d(világosság) )`, ahol a világosság a három csatorna
**számtani átlaga**, és `d` a mért görbe. Bizonyíték: egy-egy
világosság-sávon belül a három csatorna szorzója gyakorlatilag megegyezik
(max állásban 11,12 / 11,54 / 11,41 a legsötétebb sávban, 1,31 / 1,35 /
1,43 a világosban) — az azonos bemeneti szinthez tartozó csatornánkénti
eltérés csak abból ered, hogy ott más-más világosságú pixelek keverednek.

Modell-választás mérve (max állás, átlagos eltérés): additív világosság-görbe
**5,56** · multiplikatív világosság-görbe 11,95 · a korábbi csatornánkénti
tónusgörbe 18,10. Világosság-definíciók: számtani átlag **5,56** ·
0,30/0,59/0,11 5,95 · Rec.709 6,21 · max 9,38 · min 11,04.

**Következmény a GPU-útra (#22):** a Derítőfény így NEM fejezhető ki
csatornánkénti LUT-tal, ezért nem nulla `fill` mellett a `finetune2` GPU
pontonkénti előnézete tilos — `EditSession.gpu_finetune_prefix()` ilyenkor
`None`-t ad, és a `build_finetune2_lut()` kivételt dob.

### Színhőmérséklet — csatornánkénti KONSTANS szorzás

A világosság-függő változat nem javított rajta (5,00 vs 5,09 a leghidegebb
állásban), tehát egyszerű szorzás. A hűtés jóval erősebb, mint a melegítés —
épp ezt hibázta el a korábbi (szimmetrikusnak vett) közelítés.

| p5 | R | G | B |
|---|---|---|---|
| −1,0 | 0,6580 | 1,1102 | 1,8713 |
| −0,8 | 0,7843 | 1,0574 | 1,4740 |
| −0,5 | 0,8956 | 1,0225 | 1,1739 |
| 0,0 | 1,0000 | 1,0000 | 1,0000 |
| +0,5 | 1,0298 | 1,0010 | 0,8929 |
| +0,8 | 1,0455 | 0,9966 | 0,8550 |
| +1,0 | 1,0546 | 0,9974 | 0,8430 |

(A szorzók a nem túlvezérelt pixelekre illesztve; a leghidegebb állás
maradék 5,08-as hibája nagyrészt a kék csatorna kivágásából jön.)

### Ami ebből a körből nyitva maradt

- A **pipetta** (p4) modellje változatlan közelítés — a `referencia/
  finomhangolas/alapszínválasztás példa.jpg` egyetlen mintája a szabályt
  (mi választja a három szorzót) nem dönti el.
- A **két varázspálca** és az **Automatikus kontraszt/szín** gomb egyetlen
  fotón mért — a szabály (nem a modell) további, eltérő színezetű fotókat
  igényel; ld. a #551 jegy kommentjeit.

## Nyitva (5. kör / implementáció közben)

1. autocolor pontos gain-képlete (célzott cast-sweep kellene)
2. ~~Vignette analitikus modell~~ — **MEGVAN** (`filterdesc-registry.md`
   4.3): belső ragyogás, `sugár = Blur·0,02·max(W,H)/4`. A `glow`/`radblur`
   analitikus modellje **is MEGVAN (#668)** — natív IIR-mag + mért
   előgörbe/maszk, ld. lent a #668 szakaszt. (A `glow` sugara valóban a
   logaritmikus leképezés eredménye: `<log>250.0</log>`, és képpontban
   értendő.)
3. unsharp kernel finomítás (dekonvolúciós illesztés)
4. `tint` színparaméter-formátum (ffff → R=0 anomália): valós adatban a
   `tint` 4 hex jegyet ír (`ffff`), a másik kettő 8-at (`ffffffff`). A
   parszernek változó hosszú hex-színt kell tűrnie. **A korábbi „két külön
   színkódolás" nyom (colorwheel version) 2026-08-15-én megdőlt**; a
   render-oldal viszont teljes, és a szín `0x00RRGGBB` sorrendű.
5. retouch/redeye régió-adatok, text overlay — régió-alapúak, 2. fázisban
6. ~~**Összehasonlító harness** (PicasaPy render vs golden, SSIM/ΔE)~~ —
   KÉSZ (#115): `tools/golden/compare_render.py`, ld. lent.
7. ~~a 4–5. effekt-fül paraméter-jelentései (#190 2. kör)~~ — **MEGOLDVA
   (2026-08-06)**: a `filterdesc.xml` minden effekt minden csúszkájának
   nevét, min–max tartományát és alapértékét megadja, és a levezetett
   ini-sorrend mind a 8 valós mintán stimmel
   ([`filterdesc-registry.md`](filterdesc-registry.md) 4.1–4.2). A
   `make_param_sweep.py` találgatott tartományai lecserélhetők a pontos
   értékekre; a sweep innentől **ellenőrzés**, nem felfedezés. Nyitva
   maradt: a `Cinemascope` jelölőnégyzet polaritása és a
   `PicnikFocalPixelate` puck-sorrendje. — az eredeti jegyzet:
   a generátor szkript ELKÉSZÜLT: `tools/golden/make_param_sweep.py` (teszt:
   `tests/golden/test_make_param_sweep.py`) minden paraméteres kulcshoz
   előre megírt `.picasa.ini`-variánsokat készít, a fő erősség-paramétert
   a feltételezett tartományán 5 ponton (min/negyed/fél/háromnegyed/max)
   végigléptetve — a feltételezett tartományok és a fixen tartott
   paraméterek indoklása a szkript `ParamSweep.megjegyzes` mezőiben és a
   generált `UTMUTATO.md`-ben áll. A TÉNYLEGES csúszka↔paraméter
   leképezés a felhasználó tömeges exportjának feldolgozásával derül ki
   (még nyitott, ez a kör csak a generátort zárta le).
8. render-pontosítás a VÉGLEGES golden-verdiktek szerint (#115/#279,
   kit3-mérés) — súlyossági sorrendben, külön render-jegy(ek):
   `tint` (dE 20, formátum: Nyitva 4) → `dir_tint` (9) → `sat` pozitív
   ág (12) → `finetune2` hőmérséklet-tengely (25 extrémnél) → `fill` 2D-LUT
   erősség-drift (6.5) → `ansel` (5.6) → `Vignette` (4.6, Nyitva 2) →
   ~~`radblur` (3.2)~~ → ~~`glow2` (2.7)~~ — mindkettő **KÉSZ (#668)**:
   a natív elmosó magra állítva a 12 golden-párból mind a 12 „közelítés".
9. **`finetune` v1 ↔ `finetune2` v2 hőmérséklet: 2× skála-hipotézis
   mérése.** A `filterdesc.xml` szerint a v1 tartománya `[−0,5..0,5]`, a
   v2-é `[−1..1]`; ha a görbe azonos, akkor `v2_érték = 2 · v1_érték`
   pontosan reprodukálja a v1 kimenetét. Egy meglévő golden-párral (v1
   `0,25` vs v2 `0,5`) olcsón ellenőrizhető — igazolás esetén a v1-hez
   **nem kell külön LUT**, és a 8. pont „finetune2-hő" tétele is olcsóbb
   lesz.
10. **`fullres` / `slow` / `resize` jelzők beépítése a renderelőbe.** A
    `filterdesc.xml` minden szűrőnél megmondja, hogy csak teljes
    felbontáson helyes-e, drága-e, illetve **méretváltó-e** (`Border`,
    `MuseumMatte`, `Polaroid`, `Cinemascope`, `DropShadow`,
    `RoundedEdges`). Ez utóbbi a geometria-láncot érinti (vágás, arcok,
    tilt utáni méretek) — implementáció előtt tisztázandó, hova kerül a
    méretváltó effekt a sorrendben.

## Összehasonlító harness (#115) — `tools/golden/compare_render.py`

A PicasaPy renderjét (`picasapy.render.apply_filters`) a valódi Picasa-exportok
ellen méri: SSIM + ΔE (CIE76) + toleranciás pixel-diff, soronkénti ítélettel
(**pixelhű / közelítés / eltér**), állítható küszöbökkel, JSON- és terminál-
riporttal. Futtatás a fejlesztői gépen (ahol a golden-kitek élnek):

A parancsok EGY sorban írandók (PowerShellben a `\` sortörés nem működik),
és a `<kit-mappa>` a saját, ténylegesen létező kit-mappa (pl.
`research/golden-kit` a Pi-n, vagy a Windowson frissen generált kit):

```
# teljes kit (make_golden_kit.py-szerkezet, exportok a kit/export/ alatt):
python3 tools/golden/compare_render.py kit <kit-mappa> --luts research/golden-analysis --json riport.json

# egyetlen pár:
python3 tools/golden/compare_render.py pair eredeti.jpg golden.jpg --filters "fill=1,0.500000;bw=1;"
```

A `--luts` elhagyható (beépített közelítések futnak). A kit bármely gépen,
fotókönyvtár nélkül is legenerálható (#115):
`python3 tools/golden/make_golden_kit.py <kimenet_dir>` — kevés/hiányzó
fotónál szintetikus fotó-alapképekkel pótol.

Küszöbök (alapértékek; CLI-ből felülírhatók):

| ítélet | feltétel | alap |
|---|---|---|
| pixelhű | max|Δ| ≤ `--pixel-tol` VAGY a tűrésen túli pixelek aránya ≤ `--frac-tol` | 1/255 ill. 0,2% (JPEG-alapzaj) |
| közelítés | SSIM ≥ `--ssim-min` ÉS átlag ΔE ≤ `--de-mean-max` | 0,98 ill. 2,0 |
| eltér | minden más (méret-eltérés is) | — |

Opcionális mért LUT-ok: ha a `--luts` könyvtárban van `luts3.json`
(`analyze_goldens3.py` kimenete — gitignore-olt, csak a fejlesztői gépen él),
a mért 2D fill-LUT és a h/s/temp LUT-ok a beépített közelítések HELYETT
futnak (`fill`, `finetune/finetune2`); hiányuk tiszta kihagyás, sosem hiba.
A harness logikája szintetikus adatokkal tesztelt
(`tests/golden/test_compare_render.py`), golden-kitek nélkül is fut.

## A kalibrálatlan natív szűrők — VISSZAFEJTVE (2026-08-14, #317)

A #317 abból indult, hogy ezekhez **golden-mérés kell a felhasználó
Picasájával**. Kiderült, hogy nem: a natív szűrő-regiszter minden szűrőhöz
megad egy callback-címet, és onnan a pixelmatematika kibontható. Egy kör
(9 gyökér, 3 szint) a legtöbbet megadta.

### `sat` — ez magyarázza a legnagyobb ismert hibát

A golden-verdikt szerint a `sat` a pozitív oldalon **12,7 ΔE-ig** romlott. Most
látszik, miért: **nem lineáris keverés a szürkével**, hanem **csatornánként
eltérő kitevőjű hatványfüggvény**.

```c
s = amount * 3.0f;                       // a csúszka HÁROMSZOROSA
for (i = 0; i < 2048; i++) {
    x = i / 256.0f;                      // 0…8 tartomány
    LUT_R[i] = round(powf(x, s*0.3f + 1.0f) * 256);
    LUT_G[i] = round(powf(x, s*0.7f + 1.0f) * 256);
    LUT_B[i] = round(powf(x, s*0.9f + 1.0f) * 256);
}
```

Behelyettesítve (`a` = a csúszka): a kitevők **R: 1 + 0,9·a**, **G: 1 + 2,1·a**,
**B: 1 + 2,7·a**. A három csatorna tehát **eltérő erősséggel** telítődik — egy
lineáris modell ezt sosem adja vissza, és a hiba a csúszka végén nő meg.

Negatív csúszkánál egy külön előlépés fut (`0x0090e200`, `amount + 1.0`).

#### A `sat` TELJES algoritmusa (2026-08-15, a csatorna-hozzárendelés lezárva)

A képpontok **BGRA** sorrendben állnak (`p[0]=B`, `p[1]=G`, `p[2]=R`), ezért a
korábban bizonytalan `5:1:2` súlyozás egyértelműen feloldható:

```c
s = amount * 3.0f;                          // a csúszka HÁROMSZOROSA

// három 2048 elemű LUT, csatornánként MÁS kitevővel:
for (i = 0; i < 2048; i++) {
    x = i / 256.0f;                         // 0…8
    LUT_R[i] = lroundf(powf(x, 1.0f + 0.3f*s) * 256);
    LUT_G[i] = lroundf(powf(x, 1.0f + 0.7f*s) * 256);
    LUT_B[i] = lroundf(powf(x, 1.0f + 0.9f*s) * 256);
}

// képpontonként:
B = p[0]; G = p[1]; R = p[2];
Y = (5*G + 1*B + 2*R) >> 3;                 // gyors egész luma
if (Y != 0) {
    k = 65535 / Y;                          // (256*256 - 1) / Y
    R2 = (LUT_R[min((k*R) >> 8, 2047)] * Y) >> 8;
    G2 = (LUT_G[min((k*G) >> 8, 2047)] * Y) >> 8;
    B2 = (LUT_B[min((k*B) >> 8, 2047)] * Y) >> 8;

    // ZÁRÓ LÉPÉS: túlcsordulásnál ARÁNYOS visszaskálázás, nem vágás
    m = max(R2, G2, B2);
    if (m > 255) {
        k2 = 65280 / m;                     // 0xff00 / m
        R2 = (k2*R2) >> 8;  G2 = (k2*G2) >> 8;  B2 = (k2*B2) >> 8;
    }
}
```

**Három dolog, amit egy naiv megvalósítás elront:**

1. **A telítés arány-térben történik**: minden csatornát elosztunk a
   luminanciával, átvisszük a hatványgörbén, majd visszaszorozzuk vele. Ettől
   luminancia-megőrző — egy szürkével keverő lineáris modell nem az.
2. **A kitevők csatornánként mások** (`a` = a csúszka):
   **R: 1 + 0,9a · G: 1 + 2,1a · B: 1 + 2,7a**.
3. **Túlcsordulásnál mind a három csatorna arányosan skálázódik vissza**, nem
   csatornánként vágódik. A vágás színárnyalatot tolna el.

A luma-súlyok `R:2/8 · G:5/8 · B:1/8` — a Rec.601 (0,299/0,587/0,114) klasszikus
egész közelítése.

**Bizonyítottsági fok: megerősített.** Címek: `0x008f8ff0` (callback) →
`0x0090b930` (mag), a skálázó állandó `DAT_00d3a148` = 256 (statikus, egyetlen
hivatkozással).

### `unsharp` / `unsharp2` — a sugár FIX

```c
FUN_0090c4a0(dst, src, 1.5f, amount);
```

A `0x3fc00000` = **1,5** — vagyis az élesítés sugara/szórása **állandó**, csak
az erősség jön a csúszkáról. Ez eddig „a kernel pontos alakja" néven nyitott volt.

### `grain` / `grain2` — fix erősség

```c
FUN_0090a2e0(dst, 0.5f);
```

A szemcse erőssége **beégetett 0,5**; a `grain` és a `grain2` **ugyanaz a
callback** (`0x008f88e0`), tehát a két token azonos hatású. Ez megerősíti a
korábbi feltevést, hogy a v1/v2 pár paraméter nélküli.

### `ansel` — szűrős fekete-fehér

A `+0x50` mezőből vett **szűrőszínt** bontja három 0…1 súlyra
(`r/255`, `g/255`, `b/255`), és ezekkel készít **súlyozott szürkeárnyalatot**
16 bites fixpontban (`Y = w_r·R + w_g·G + w_b·B`, `0…0xffff`-re vágva), majd
**256 rekeszes hisztogramot** épít belőle a további feldolgozáshoz.

### `tint`

A `+0x50`-es színt használja, a keverési arány `256 − round(amount)`, és
figyelembe veszi a `Preferences/CarefulEnhance` beállítást.

### Ami maradt

- a `sat` luminancia-súlyainak csatorna-hozzárendelése (5:1:2);
- az `ansel` hisztogram utáni lépése;
- `dir_tint`, `radsat` számszerű feldolgozása (a nyers kimenet megvan).

**Ezekhez már nem a felhasználó Picasája kell**, hanem a meglévő
dekompilátum feldolgozása vagy egy tetszőleges mintaképes ellenőrzés.

## A szinthúzás vágási pontjai — MEGFEJTVE (#539, 2026-08-14)

A `autolight` (`0x008f80c0`) a vágási pontokat **hisztogram-darabszám
küszöbbel** keresi, nem percentilissel:

```c
N = szelesseg * magassag;
if (lepes != 0) N = N / (lepes * lepes);   // a MINTAVÉTELEZETT képpontszám
kuszob = (int)roundf((float)N * 0.005f);   // a 0.005 a hívási helyen: 0x3ba3d70a
if (kuszob == 0) kuszob = 1;

// alsó vágás csatornánként
i = 0; sum = 0;
do { sum += hist[i]; i++; } while (i <= 255 && sum < kuszob);
lo = i - 1;

// felső vágás csatornánként
i = 255; sum = 0;
do { sum += hist[i]; i--; } while (i >= 0 && sum < kuszob);
hi = i + 1;

// a globális vágás a három csatorna UNIÓJA:
lo = min(lo_R, lo_G, lo_B);
hi = max(hi_R, hi_G, hi_B);
```

**Miért nem percentilis:** a küszöb abszolút darabszám. Erős, egyenetlen
hisztogramnál egyetlen szint már átlépi, ezért a tényleges vágási pont
0%-tól 16%-ig szóródhat — ezt a #535 mérése is kimutatta, és fix
százalékkal elvileg sem reprodukálható.

**Három részlet, ami számít:**

1. **Off-by-one:** a ciklus a léptetés *után* ellenőriz, ezért `lo = i − 1`
   és `hi = i + 1`.
2. **A küszöb a képmérettel skálázódik** (`N / lepes²`), nem abszolút.
3. **A globális vágás a csatornák uniója** (min/max) — a csatornánkénti
   értékek külön is rendelkezésre állnak.

Címek: `0x008f80c0` → `0x00a4bfd0` → `0x00a4be40`. Nyers kimenet:
`referencia/dekompilalt-612/` (privát repó).

### KÉT KÜLÖN ÚT: az unió az `autolight`-é, az `enhance` csatornánként vág

A #539 megvalósítási köre kiderítette, hogy a fenti uniós kód **nem** minden
automatikára érvényes. A natív szűrő-regiszter
(`referencia/native-filter-registry.json`) címei alapján:

| ini-név | belépő | vágás | elemzett terület |
|---|---|---|---|
| `autolight` (Auto Contrast gomb) | `0x008f80c0` → `0x00a4bfd0` | a csatornánkénti pontok **UNIÓJA**, egyetlen közös `lo`/`hi` | a **teljes** kép |
| `autocontrast` | `0x008f89d0` → `0x009db610` | **csatornánként külön** | a középső 90 % × 90 % |
| `enhance` („Jó napom van") | `0x008f8840` → `0x009db610` | **csatornánként külön** | a középső 90 % × 90 % |

A `0x009db610` a küszöböt `(W·H)/200` egész osztással számolja (ugyanaz a
0,5 %), és a leképezést **fixpontosan** végzi:

```c
gain = (max << 16) / (hi - lo);      // egész osztás, LEFELÉ kerekít
ki   = ((be - lo) * gain) >> 16;     // aritmetikai eltolás
ki   = min(max, max(0, ki));         // max = 255, „CarefulEnhance"-nél 252
```

Két bájtra látszó következménye van: a felezőpont lefelé kerekedik, és maga a
fehérpont sem feltétlenül éri el a 255-öt (100 széles sávnál 254 lesz).
`lo = 0`, `hi = 255` esetén viszont a gain pontosan 65536, tehát az
**azonosság-eset bájtra pontos**.

### Mérés a 12-12 referencia-páron (privát repó)

Csatornánkénti átlagos abszolút eltérés a valódi Picasa-kimenettől:

| művelet | készlet | régi modell | **#539** | érintetlen kép |
|---|---|---|---|---|
| `autolight` | `referencia/autocontrast/` | 0,62 | **0,41** | 7,49 |
| `enhance` | `referencia/imfeellucky/` | 2,61 | **2,61** | 10,35 |

Az `autolight` javulása az uniós vágópontból (a korábbi, három csatornát EGY
hisztogramba öntő közelítés helyett) és a fixpontos átvitelből jön; a 12
képből 5 azonosság-esete bájtra pontos maradt. A `CarefulEnhance` 252-es
kimeneti korlátja **kizárva**: mérve 3,41 a 2,61 helyett.

**NYITVA marad az `enhance` kiugró képe** („Utopic Unicorn", 13,3): ott a
Picasa által ténylegesen alkalmazott bemeneti tartomány két csatornán
**szélesebb, mint magának a csatornának a teljes értékkészlete** (zöld:
12–47 helyett 18,2–76,3), tehát *semmilyen* darabszám-küszöb nem adhatja ki.
A natív gain-korlát léte ezzel bizonyított, de a dekompilátumban még nem
találtuk meg (a Ghidra a `0x009db610` két float paraméterét elveszti), ezért
a `_MIN_STRETCH_SPAN = 58` továbbra is **mért**, nem visszafejtett viselkedés.
Amit ez a kör kizárt: az `autolight`+`enhance` bármely sorrendű összetétele
(5,97–6,07), az azonossággal való erősség-keverés, a 252-es korlát, és minden
1/100–1/400 közötti vágási osztó (a legjobb így is 2,56).
## Az irányított család megvalósítva — `dir_sat`, `dir_brite`, `dir_sharp`, `linblur` (#623)

A #568 visszafejtésének eredménye kódba került. Modulok:
`render/directional.py` (a közös rámpa + a három `dir_*`),
`render/linear_blur.py` (`linblur`), `render/iir_blur.py` (a KÖZÖS elmosó
mag, `0x009dd0d0`). Mind a négy elérhető a `filters=` láncból, és a
„Régi effektek" fülön (#571) is aktív.

**Paraméter-alakok:**

| szűrő | ini-alak | honnan |
|---|---|---|
| `dir_sat` | `dir_sat=1,balról-jobbra,felülről-lefelé` | a burkolók (`0x008f8fb0`, `0x008f9050`, `0x008f9090`) a két csúszkát KÖZVETLENÜL adják tovább; a korong csak beállítja őket (közös `0x008f9bc0` visszahívás) |
| `dir_brite` | `dir_brite=1,balról-jobbra,felülről-lefelé` | ” |
| `dir_sharp` | `dir_sharp=1,balról-jobbra,felülről-lefelé` | ” |
| `linblur` | `linblur=1,korong-x,korong-y,Mennyiség` | itt a korong VALÓDI pozíció (`0x008f9bf0`), ezért a puck-os szűrők általános sorrendje érvényes (`filterdesc-registry.md` 3. pont) — valódi ini-mintánk nincs rá |

**A közös elmosó mag (`0x009dd0d0`)** most kapott először megvalósítást:
kétmenetes, elsőrendű IIR, 9.7 fixpontos állapottal, a 4.2.5-ben MÉRT
`k = round(65536·(1 − exp(−1/R)))` együtthatóval. A `dir_sharp` burkolója
`min(W, H)/8` sugárral hívja (tehát a hatás **helyi kontraszt**, nem finom
részlet-élesítés), a `linblur` burkolója pedig **kétszer** futtatja le.

**Ami közelítés maradt** (a docstringek is kimondják):

1. `dir_sharp` — a globális horgony (`k`). A natív kód a két csúszka
   abszolút értékéből számolja, de x87-veremen; a `k = round((|a|+|b|)·256)`
   feltevés mellett szól, hogy a két `ABS` hívás pontosan a rámpa
   maximumához (`max s = |a|+|b|`) kell, hogy az `amount` a képen
   nemnegatív legyen, és hogy 0 csúszkaállásnál a kép változatlan.
2. `linblur` — a „Mennyiség" → sugár leképezés (a testvér `radblur`
   burkolójának alakjával: `W/100·(Amount+1) + 0,001`).
3. `linblur` — a súlytábla utolsó rekeszei. A natív
   `round((1−2f)·255,9999)` **bájtba** kerül, így `i ≥ 338`-tól 256-ot
   tárolna, ami 0-ra fordul körbe: a teljesen éles tartomány egy sávjában
   50%-os homályt adna. A 255,9999-es szorzó a **csonkolás** klasszikus
   idiómája, ezért 255-re vágunk — referencia-export döntheti el.

Mindhármat a **#317** (effekt-kalibráció) írhatja felül; a hatás JELLEGE
(hol erős, milyen irányú, milyen az átmenet) ettől függetlenül egzakt.

## A `glow`/`glow2` és a `radblur` a natív magon — VÉGIGMÉRVE (#668)

A #623 bevitte a közös elmosó magot, de a `glow`-t és a `radblur`-t
szándékosan a régi Gauss-közelítésen hagyta, mert a golden-verdiktjük ahhoz
volt kalibrálva. A #668 elvégezte a mérést, és a mérés **támogatta** a
cserét: mind a 12 golden-pár javult, egy sem romlott.

### A felhasznált referencia-anyag

| forrás | mi van benne | mire jó |
|---|---|---|
| `referencia/blur-meres/export/…-sugar-percent-{0,25,50,75,100}` | szintetikus éllépcső + a windowsos Picasa **Ragyogás**-exportja öt sugárállásban, Intenzitás maximumon | a TÉRBELI komponens (a 4.2.5 mérés forrása) |
| `golden-kit/09-effects` | `chart_color`, `photo01`, `photo04` × `glow1`, `glow2`, `radblur` — valódi Picasa-exportok | tónus + térbeli, fotón és mérőtáblán |
| `golden-kit3/16-effects-ramp` | `chart_ramp` × `glow1`, `glow2`, `radblur` | tónus, sík szürke lépcsőfokokon |

A `blur-meres/export/blur-meres-LagyFokusz_ellenorzes` **nem** Lágy fókusz
(a neve félrevezető): a kimenete vízszintesen és függőlegesen is egyenletes,
tehát a 4.2.5 „a sugár abszolút" ellenőrzésének 1600 képpontos `glow`-ja.
**Valódi `radblur`-export tehát csak a két golden-kitben van** (négy pár,
két Amount-értékkel) — több sugaras beállítást a #317 mérhet.

### A `glow` megfejtett modellje

```
elő = be² / 255                                  ← MULTIPLY önmagával
hom = iir_blur(elő, R, R)                        ← a natív mag (0x009dd0d0)
ki  = be + Intenzitás · (255 − be) · hom / 255   ← SCREEN
```

- **Sugár:** a tárolt (log-leképezett) paraméter **képpontban**, változtatás
  nélkül. A `blur-meres` öt csúszkaállásán az él-profil átlagos hibája
  0,48–1,63 szint (a régi Gauss-modellé 0,68–10,19).
- **Előgörbe:** a sík foltok tónusemelése `(255−c)·c²` alakú, nem
  `(255−c)·c`. A kitevő illesztése **éles minimumot ad 2,0-nál** (1,9-nél és
  2,1-nél az átlagos hiba a kétszeresére nő). Ez fedi a natív burkoló
  puffer-előkészítő lépését (`FUN_009aabf0` + `FUN_00aa40a0`).
- **Súly:** maga az Intenzitás — nincs illesztett szorzó. (A korábbi modell
  0,565-ös konstansa a hibás előgörbét kompenzálta.)

A sík szürke foltok mért és modellezett értéke (a `chart_color` goldenről,
`glow1` = `1,0.432749,2.469705`, `glow2` = `1,0.65,3.0`):

| bemenet | glow1 golden | glow1 modell | glow2 golden | glow2 modell |
|---:|---:|---:|---:|---:|
| 64 | 69,54 | 69,13 | 71,70 | 71,72 |
| 96 | 105,69 | 105,76 | 110,57 | 110,62 |
| 128 | **141,92** | 141,78 | **148,86** | 148,74 |
| 160 | 175,95 | 176,20 | 184,03 | 184,17 |
| 192 | 207,43 | 207,45 | 215,29 | 215,20 |

> A 3. kör „128 → 144 / 151" horgonya tehát **téves volt** — a Gauss-modell
> saját kimenetét rögzítette, nem a goldenét. A tesztek javítva.

### A `radblur` megfejtett modellje

Natív elmosó mag + a 4.2.4 sugaras smoothstep-maszkja
(`render/radial_mask.py`), a korong közepén az EREDETI képpel, a peremen az
elmosottal. Két illesztett skalár:

- **`Sharpness = 0`** — a `radblur`-nak nincs „Élesség" csúszkája; a négy
  golden-pár illesztési minimuma egybehangzóan a 0-nál van (0,1-től monoton
  romlik).
- **a sugár képszélesség-hányada `0,009`** — a 4.2.4 dekompilátum `0,01`-et
  olvas, de mind a négy pár (két Amount-érték, három kép) minimuma
  következetesen a `0,9 ×` értéknél van, és az `(Amount+1)` arányosság
  pontosan teljesül. **Az eltérés oka nyitott** — a #317 dolga eldönteni,
  hogy a dekompilált konstans olvasata pontatlan-e, vagy a natív hívás
  máshonnan kapja a szélességet.

> Az `Amount = 0` **NEM azonosság** — a korábbi kód annak vette. A
> `golden-kit` `radblur=1,0.411585,0.611111,0,0` exportján a kép átlagosan
> 12,5 (photo01) és 26,4 (photo04) szintnyit tér el a forrástól.

### A mérés eredménye — régi vs. új

Átlagos ΔE (CIE76) a teljes render-láncon, valódi Picasa-exportok ellen:

| golden-pár | régi (Gauss) | **új (natív)** | ítélet |
|---|---:|---:|---|
| `chart_color` glow1 | 3,00 | **0,69** | eltér → közelítés |
| `chart_color` glow2 | 4,25 | **0,62** | eltér → közelítés |
| `chart_color` radblur | 1,92 | **0,50** | közelítés → közelítés |
| `photo01` glow1 | 1,74 | **0,15** | közelítés → közelítés |
| `photo01` glow2 | 2,54 | **0,18** | eltér → közelítés |
| `photo01` radblur | 5,02 | **0,09** | eltér → közelítés |
| `photo04` glow1 | 2,32 | **1,06** | eltér → közelítés |
| `photo04` glow2 | 3,31 | **1,19** | eltér → közelítés |
| `photo04` radblur | 11,88 | **0,68** | eltér → közelítés |
| `chart_ramp` glow1 | 1,85 | **0,25** | közelítés → közelítés |
| `chart_ramp` glow2 | 2,68 | **0,24** | eltér → közelítés |
| `chart_ramp` radblur | 3,18 | **0,26** | eltér → közelítés |

Összegzés: **4 közelítés + 8 eltér → 12 közelítés, 0 eltér.** A maradék hiba
JPEG-zaj nagyságrendű; „pixelhű" ítélet veszteséges goldenen nem érhető el.

### Ami NEM változott

A **`radsat`** („Fókuszos FF") a régi közelítésen maradt: ugyanezt a natív
maszkot használja, de **nincs hozzá egyetlen mért kimenet sem**, és a
projekt szabálya szerint a natív mag megléte önmagában nem indok. A #317
kalibrálhatja, ha készül hozzá referencia-export.

### `radsat` („Telítetlenít egy középpont körül") — TELJES (2026-08-15, #317)

Sugárirányban telítetlenítő effekt: a középpont közelében megmarad a szín,
kifelé haladva szürkébe megy át. Callback `0x008f8680`, mag `0x0090b660`,
a lecsengés-tábla építője `0x0090aeb0`.

#### Előkészítés — 1024 elemű lecsengés-tábla

```c
// a téglalap a hatásterület (a callback a +0x94 mezőből olvassa)
r  = min((jobb - bal)/2.0f, (also - felso)/2.0f) * (sugar + 1.0f);
r2 = r * r;
shift = 0;
while (r2 > 1024.0f) { r2 *= 0.5f; shift++; }   // hogy a sugárnégyzet beférjen

k = 1.0f / (1.0f - 0.99f * sqrtf(elesseg));      // az él meredeksége

for (i = 0; i < 1024; i++) {
    t = sqrtf(i / r2);                           // normalizált sugár (0…1)
    v = clampf(0.5f + k * (t - 0.5f), 0.0f, 1.0f);
    v = 1.0f - v;
    tabla[i] = (uint8_t)lroundf((3.0f - 2.0f*v) * v * v * 255.0f);   // SMOOTHSTEP
}
```

#### Képpontonként

```c
idx = ((x - cx)*(x - cx) + (y - cy)*(y - cy)) >> shift;
Y   = (77*R + 151*G + 28*B) >> 8;                // ld. lent
if (idx < 1024) {
    w = 256 - tabla[idx];
    R' = R + (((Y - R) * w) >> 8);               // lineáris keverés a szürke felé
    G' = G + (((Y - G) * w) >> 8);
    B' = B + (((Y - B) * w) >> 8);
} else {
    R' = G' = B' = Y;                            // a körön KÍVÜL teljesen szürke
}
```

A középpont `cx = round(W · px)`, `cy = round(H · py)` — a két csúszka
**képarányos** koordinátát ad, nem képpontot.

#### Három részlet, ami számít

1. **A lecsengés SMOOTHSTEP** (`3v² − 2v³`), nem lineáris és nem koszinuszos.
2. **Az él meredekségét `k = 1/(1 − 0,99·√élesség)` adja** — az élesség
   csúszka végén `k = 100`, azaz gyakorlatilag éles körvonal; nullánál `k = 1`,
   azaz egyenletes átmenet.
3. **A körön kívül nincs keverés, hanem teljes szürke** — külön kódág.

#### A luma-súlyok: KERESZT-MEGERŐSÍTÉS

`Y = (77·R + 151·G + 28·B) >> 8` — **pontosan ugyanaz a három együttható**,
amit a szépia algoritmusánál (#619) mértünk ki. Két, egymástól független
effekt ugyanazt a szürkeárnyalat-képletet használja; ez megerősíti mindkét
korábbi olvasatot.

> Figyelem: ez **nem** azonos a `sat` luma-súlyaival (ott `R:2/8 · G:5/8 ·
> B:1/8` egész közelítés). A Picasa **két különböző** luma-képletet használ,
> effektcsaládtól függően.

**Bizonyítottsági fok: megerősített.**

### `dir_tint` (irányított színezés) — TELJES (2026-08-15, #317)

Lineáris színátmenet mentén színez, adott irányban. Callback `0x008f9880`,
mag `0x0090f470`, a lecsengés-tábla ugyanott épül.

#### A csúszkák leképezése (a callbackből)

```c
szelesseg = clampf(*(float*)(p + 0x28), 0.001f, ...);   // alsó korlát 0.001
szog_fok  = (poz - 0.5f) * 30.0f;                        // ±15° tartomány
halvanyitas = 1.0f - *(float*)(p + 0x2c);
irany = (p[0xc4] == -1) ? 0 : p[0xc4] - kep_forgatas;    // 0…3, a képforgatással korrigálva
```

Az `irany` alsó két bitje adja a négy fő irányt: a `& 1` felcseréli a
vízszintes/függőleges tengelyt (és a `sin`/`cos` szerepét), a `& 3 == 2`
illetve `== 3` pedig előjelet vált. **A képforgatás beleszámít** — az irány a
megjelenített képhez igazodik, nem a fájlhoz.

#### A lecsengés-tábla — 384 elem, szakaszos harmadfokú

A magban `w = 1/szelesseg` (a `szelesseg` előbb `[0,01 … 99,9]`-re vágva),
majd `t` `1/256`-os lépésekkel:

```c
if      (t >  1.5f)  f = 0.0f;
else if (t < -1.5f)  f = 1.0f;
else if (t >  0.5f)  f = 0.5625f - (t*1.125f + (t³/6 - 0.75f*t²));
else if (t > -0.5f)  f = 0.5f    - (t*0.75f  - t³/3);
else                 f = (-t³/6 - 0.75f*t²) - t*1.125f + 0.4375f;

tabla[i] = lroundf((1.0f - 2.0f*f) * 255.9999f);     // i = 0 … 383
```

> **Az együtthatók pontosak** (a dekompilátumból). Az alak egy **harmadfokú
> B-spline-integrál** jellegű S-görbe; ezt az azonosítást **erősnek** jelölöm,
> nem megerősítettnek — a képlet viszont szó szerint átvehető, azonosítás
> nélkül is.

#### Képpontonként

A vetület `p = (dy·sin + dx·cos)` inkrementálisan halmozódik 8 bites
fixpontban, és `p >> 8` indexeli a táblát (0…383 tartományra vágva). A tábla
értéke a színezés erőssége az adott képpontban.

#### Miben tér el a `radsat`-tól

| | `radsat` | `dir_tint` |
|---|---|---|
| geometria | **sugárirányú** (r² alapján) | **lineáris** vetület adott irányban |
| lecsengés | **smoothstep** (`3v²−2v³`) | **szakaszos harmadfokú** S-görbe |
| tábla | 1024 elem | 384 elem |

**A két effekt tehát NEM közös segédfüggvényre épül** — külön geometria, külön
átmenetgörbe. Aki egy közös „gradiens-modult" ír alájuk, mindkettőt elrontja.

**Bizonyítottsági fok: megerősített** (a leképezések és az együtthatók),
**erős** (a görbe B-spline-ként való azonosítása).

### `tint` — a színparaméter feldolgozása (2026-08-15, a „Nyitva 4" részleges megoldása)

A `tint` a **legnagyobb mért eltérésű** effekt (20,63 ΔE). A callback
(`0x008f9630`) visszafejtése megmutatta, hogy a színt **nem nyersen** használja:

```c
szin = *(uint*)(p + 0x50);

// 1) VIRTUÁLIS SZÍNÁTALAKÍTÁS, ha van kontextus
ctx = *(int*)(param_4 + 8);
if (ctx) (*(void(**)(void*,uint*,uint*,int))(*(int*)ctx + 8))(ctx, &szin, &szin, 1);

// 2) normalizálás a legnagyobb komponensre
R = szin & 0xff;  G = (szin>>8) & 0xff;  B = (szin>>16) & 0xff;
mx  = max(R, G, B);
sum = (R + G + B) * 85;                  // 85*3 = 255 → sum = 255 * átlag
k   = ((mx * 255.0f) / sum - 1.0f) * 0.5f + 1.0f;
skala = lround(16711680.0 / (mx * 255.0));   // 0xFF0000 / (mx*255)

if (k != 1.0f) <extra igazítás: 0x00aa40a0>(k, 0);
<színezés a feldolgozott színnel>(dst, szin, …);
```

#### Amit ez megmagyaráz

A `k` tényező **a szín telítettségétől függ**: szürke árnyalatnál
`mx == átlag`, tehát `k = 1` és nincs korrekció; erősen telített színnél
`k > 1`. **A nyers RGB-vel színezve ez a korrekció kimarad** — szisztematikus,
a szín telítettségével növekvő eltérést okoz, ami illeszkedik a mért 20,63-hoz.

#### Ami NYITVA maradt

1. **Mi a virtuális átalakítás** (`ctx->vtbl[2]`). A `ctx` a callback 4.
   argumentumából jön; statikusan nem követtük vissza. Ugyanezt a mintát
   használja az `ansel` is (`0x008f8410`) — tehát **közös** lépés.
2. **A `colorwheel version="0"` vs `="1"` különbsége.** A `filterdesc.xml`
   szerint `tint`/`dir_tint`/`radtint` = v0, `ansel` = v1. Az RTTI-ben van
   `ytColorWheelNode` osztály; a verzió szerinti eltérés feltehetően a
   kerék-koordináta → RGB leképezésben van, de ezt **nem igazoltuk**.

**Bizonyítottsági fok:** megerősített (a fenti képletek és a hívási sorrend) ·
**nyitott** (a virtuális átalakítás tartalma és a wheel-verzió jelentése).

#### A TELJES csővezeték (2026-08-15, kiegészítés)

A három segédfüggvény is előkerült a meglévő naplókból, és ezzel a `tint`
**öt lépésből** áll — a mai megvalósításunk jó eséllyel csak az utolsót
csinálja:

```c
// 1) SZÍNMEGŐRZÉS: telítetlenítés szürke felé      (0x009a9550)
w = 256 - szinmegorzes;
Y = (77*R + 151*G + 28*B) >> 8;
C = C + (((Y - C) * w) >> 8);

// 2) a színezőszín átvezetése a virtuális átalakításon   (még NYITOTT)

// 3) telítettségfüggő tényező
mx  = max(tR, tG, tB);
sum = (tR + tG + tB) * 85;
k   = ((mx * 255.0f) / sum - 1.0f) * 0.5f + 1.0f;

// 4) GAMMA-LUT, kitevő 1/k                          (0x00aa40a0)
for (i = 0; i < 256; i++) LUT[i] = lroundf(powf(i/255.0f, 1.0f/k) * 255.0f);
// (a 0,0 és 2,2 kitevőjű táblák gyorsítótárazva vannak)

// 5) SZORZÓ keverés, a legnagyobb komponensre normalizálva   (0x009db4f0)
skala = 65536 / mx;
C' = min(255, (C * tC * skala) >> 16);        // ≈ C * tC / mx
```

> **Ez magyarázza a 20,63 ΔE-t.** Egy naiv „szorozd meg a színnel" megoldásból
> hiányzik a szín­megőrzés-lépés, a telítettségfüggő **gamma**, és a
> `mx`-normalizálás. Mindhárom a szín telítettségével arányos hibát okoz.

#### A luma-súlyok — HARMADIK független megerősítés

`Y = (77·R + 151·G + 28·B) >> 8` — ugyanaz a három együttható, mint a
**szépiánál** (#619) és a **`radsat`-nál**. Három, egymástól függetlenül
visszafejtett effekt ugyanazt a képletet használja.

#### A 2. lépés MEGFEJTVE: színkezelés (ICC), nem az algoritmus része (2026-08-15)

Célzott dekompilálás (`DecompileTint.java`; gyökerek: `0x008f9630` tint,
`0x008f8410` ansel, `0x008f8730` radtint, mélység 2) mindhárom callbackben
**szó szerint ugyanazt a két sort** hozta:

```c
if ((*(uint*)(param_4 + 4) & 0xfffffffe) != 0) FUN_00a3f2f0();   // 0x00a3f2f0
ctx = *(int*)(param_4 + 8);
if (ctx) (**(code**)(ctx + 8))(ctx, &szin, &szin, 1);            // EGYETLEN pixel
```

`FUN_00a3f2f0` (`0x00a3f2f0`) egy **ICC-profillánc** alapján épít/gyorsítótáraz
transzformot: `in_EAX[0]` a profilmutatók tömbje, `in_EAX[1] >> 1` a darabszám,
és ha **kevesebb mint 2 profil van, vagy a lánc két vége azonos**, meghívja a
felszabadítót (`FUN_00a3f110`) és **`ctx` marad 0**.

**Következtetés:** ez nem a `tint` algoritmusának lépése, hanem a felhasználó
által választott **színezőszín átvezetése a színkezelésen** (monitor-/munkatér-
profil), pontosan 1 pixelnyi adaton. Alapértelmezett konfigurációban (nincs
külön profil, vagy forrás == cél) **identitás**. A PicasaPy tehát a kiválasztott
színt nyersen használhatja; ez nem forrása a 20,63 ΔE-nek.
*Bizonyítottsági fok: megerősített* (a `ctx == 0` ág explicit a kódban).

#### Bájtsorrend: a színparaméter `0x00RRGGBB` — a korábbi olvasat javítva

A fenti pszeudokód `R = szin & 0xff` sora **fordítva volt**. Két független
bizonyíték:

- az `ansel` (`0x008f8410`) a `(szin>>16)&0xff` értéket adja át **első**
  float-argumentumként, a `&0xff`-et harmadikként;
- a szorzó keverés (`0x009db4f0`) a `szin & 0xff`-et a pixelpuffer **0. bájtjára**
  szorozza, a `>>16`-ot a 2.-ra — a Windows 32 bites pufferben az a **B**, ill.
  az **R**.

Tehát: **R = (szin>>16)&0xff, G = (szin>>8)&0xff, B = szin&0xff.** A `mx`/`sum`
képletekre ez nem hat (szimmetrikusak), az ini-beolvasásra viszont igen.

#### A `colorwheel version="0"` vs `="1"` — NEM verzió, hanem sorszám

Az `editpanel.tre` elrendezés-erőforrás és az `editpaneltext.tre` feliratai
eldöntik: a szerkesztőpanelen **két színválasztó kerék** van,
`editpanel/colorwheel0` és `editpanel/colorwheel1`, közös
`editpanel/colorwheel_container`-ben, mindkettőhöz saját `slidercircle{0,1}`
körkörös csúszka (`Property buddy`) és saját felirat — **mindkettő szövege
„Pick Color"**. A kódban a névsablon `editpanel/colorwheel%d`
(`0x00c86f2c`, hivatkozók közt `0x007518e0`, `0x005fa770`).

A `filterdesc.xml` `version` attribútuma tehát azt mondja meg, **melyik
kerékhez** kötődik a paraméter, nem azt, hogy más a szín kódolása. Az
`ytColorWheelNode` visszafejtett slotjai (`0x00a63280`, `0x00a63340`,
`0x00a64c20`, `0x00a61f90`) mind **elrendezés és találatvizsgálat**, sehol
nincs kerék-koordináta → RGB leképezés — összhangban ezzel.

**Ezzel elesik a korábbi legerősebb nyomunk a `tint` `ffff`-anomáliájára**
(fentebb, a „két külön színkódolás" feltevés): a `version` nem színkódolás.
A négy hex jegy magyarázatát máshol kell keresni (valószínűbb: rövidebb,
16 bites írásformátum az ini-ben).
*Bizonyítottsági fok: megerősített* (erőforrás-szöveg + kódbeli névsablon).

#### Ami továbbra is nyitott

Csak a `tint` ini-beli `ffff` (4 jegy) vs. 8 jegyű írásmód. A render-oldali
csővezeték öt lépése ezzel **teljes**.

### `ansel` (Szűrős fekete-fehér) — a hisztogram-lépés (2026-08-15, #317 utolsó szála)

A callback (`0x008f8410`) a választott **szűrőszínt** bontja három 0…1 súlyra
(`r/255`, `g/255`, `b/255`), és ezekkel készít súlyozott szürkeárnyalatot
16 bitben (`0…0xffff`-re vágva) — ez már ismert volt. Ami most került elő: a
mag (`0x0090e680`) **hisztogramot épít, és abból automatikus
középtónus-kiemelést számol**.

#### 1. Hisztogram

A 16 bites szürkeértékből `Y >> 8` indexeli a **256 rekeszes** hisztogramot.

#### 2. Súlyozott összeg — parabola-súlyokkal

```c
sum = 0;
for (j = 0; j < 256; j++)
    sum += hist[j] * (((255 - j) * j) >> 6);
```

A súly `(255−j)·j / 64` — **parabola, a középtónusnál (j ≈ 128) a legnagyobb,
a két végén nulla**. Vagyis a `sum` azt méri, **mennyi középtónusos tartalom
van a képen**.

#### 3. Képpontonkénti kiemelés

```c
v = v + ((((0xffff - v) * v >> 14) * k) >> 8);   // v 16 bites
v = clamp(v, 0, 0xffff);
kimenet = v >> 8;
```

Az `(0xffff − v)·v` ismét **parabola**: a középtónusokat mozdítja a
legjobban, a fekete és a fehér pontot nem. Vagyis ez egy **S-görbés
kontrasztemelés**, aminek az erősségét a 2. lépésben mért `k` adja.

> **Bizonyítottsági fok:** a **szerkezet megerősített** (mindkét parabola és a
> hisztogram-építés a dekompilátumból). Ami **nyitott**: a `sum → k` közti
> skálázás, mert a köztes számítás az FPU-veremben megy, és a dekompilátor
> csak a záró `__ftol`-t (`0x00c29990`) látja.
>
> **Ez méréssel olcsón pótolható:** két-három golden-pár elég a `k` arányának
> illesztéséhez, mert a görbe alakja már ismert.
