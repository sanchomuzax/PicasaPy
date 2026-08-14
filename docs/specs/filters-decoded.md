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

### `sepia` és `warm` — mért csatornagörbék

Szürke bemenetre (g) nem-lineáris, csatornánként eltérő görbék
(a teljes LUT-ok mentve; közelítő lineáris szakasz):

- sepia: R≈0,82g+58 · G≈0,86g+35 · B≈0,90g+15 (sötétben széttart,
  fehér felé összezár) — implementáció: mért 3-csatornás LUT.
- warm: R≈0,89g+19 · G≈0,88g+1 · B≈0,93g−16 — mért LUT.

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
| `glow` | közelítés (1.85) | ✅ jó |
| `enhance` | közelítés, színöntetnél eltér (0.49–3.02) | ✅ jó (az autocolor-komponens húzza) |
| `sat` | negatív jó, pozitív romlik (0.70–12.71) | ⚠️ pozitív telítés pontosítandó |
| `finetune2` | h/s alacsony jó, hő-extrém eltér (0.94–24.9) | ⚠️ hőmérséklet-tengely pontosítandó |
| `fill` | csak gyenge erősségnél jó (1.03–6.56) | ⚠️ 2D-LUT az erősséggel driftel |
| `glow2` | eltér (2.68) | ❌ közelítő modell |
| `radblur` | eltér (3.18) | ❌ |
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
| **MÉRT** | golden-kitből mért LUT/paraméter, pixelhű vagy közelítés-verdikttel | `crop64`, `tilt`, `bw`, `enhance`, `autolight`, `autocolor` (részleges), `fill`, `finetune`/`finetune2`, `unsharp`/`unsharp2`, `sepia`, `warm`, `sat`, `grain2` (statisztikai), `glow` (v1, ΔE 1,85 — ld. Golden-verdiktek fent) |
| **MÉRT, DE ELTÉR** | van mérés, de a verdikt „eltér" — javítandó | `tint` (ΔE 20,6), `dir_tint` (9), `ansel` (5,6), `radblur` (3,2), `glow2` (2,7) |
| **MEGFEJTVE a filterdesc.xml-ből (#381)** | a lépéssorrend és a számértékek a Picasa saját `filterdesc.xml` `<effect>` csővezetékéből jönnek — nem golden-méréssel „visszafejtett" közelítés, hanem a Picasa TÉNYLEGES lépéssora (az alacsony szintű kernelek, pl. Gauss-elmosás, a szokásos megfelelőjükkel) | `Vignette`, `Matte`, `HDR`, `LocalContrast`, `Invert`, `CrossProcess`, `Sixties`, `Cinemascope`, `Orton`, `PencilSketch`, `HeatMap`, `NightVision`, `Holga`, `Lomo`, `Neon`, `Boost`, `Soften`, `Pixelate`, `QuantizePalette`, `TwoTone`, `Border`, `RoundedEdges`, `DropShadow`, `MuseumMatte`, `Polaroid`, `PicnikGrain` |
| **MEGFEJTVE A BINÁRISBÓL (#566)** | a `filterdesc.xml` csak a paraméterNEVEKET és a FIX konstansokat adja, de a `Picasa3.exe` statikus visszafejtése a teljes belső kernelt feltárta (`glimmer::IRImageOperation`, RTTI/vtable `0xcf0a14`, ctor `0xbc3d80`, feldolgozás `0xbc3f50`) | `IR` |
| **MEGFEJTVE, DE ECSET-MASZK NÉLKÜL (#381)** | a csővezeték/paraméterezés egzakt, de a Picasa ecsettel kijelölt régióra hatna — a PicasaPy-nak nincs ecset-eszköze, ezért a TELJES KÉPRE fut (jelezve a `ChainReport.range_warnings`-ban) | `PicnikTint`, `ReanimatedEyeColor` |
| **KÖZELÍTŐ (mérés nélkül) — #381 után is maradt** | a hatás jellege alapján, szakirodalomból — sem golden-mérés, sem filterdesc-pontosítás nincs még bekötve | — |
| **MEGFEJTVE A FILTERDESC + NATÍV KÓDBÓL, EGY RÉSZLET NYITVA (#569, #570)** | a csővezeték (lépések, paraméter-sorrend, képletek, keverési módok) egzakt; egyedül a mintavételezés perem-/interpolációs szabálya vár golden-összevetésre | `Comicize`, `FocalZoom`, `PicnikFocalPixelate` |
| **KÖZELÍTŐ (másik, mért v2-modell újrahasznosítva) — #347 lezáró audit (2026-08-06)** | a filterdesc szerint a v1/v2 pár paraméter nélküli, azonos "oneclick" család (nincs csúszka/szín, ami megkülönböztetné őket) — a v1-re önmagára nincs golden-mérés, ezért a már mért v2-modellt futtatjuk rá | `grain` (v1, a `grain2` modelljét használja) |
| **PONTOS** | matematikailag egyértelmű, mérés sem kell | `Invert` (255−x, #381 óta a `glimmer_ops.invert_curve`-ön át) |
| **NEM EFFEKT — no-op jelző-token** | a lánc érvényes tagja, de nem képi művelet, csak metaadat (szerkesztési előzmény/mozi-vágás), a `_NOOP_MARKERS`-en át csendben elnyelődik, round-trip megőrzött | `picnik=1;` (Creative Kit-szerkesztés jelölője), `redeye=1;`/`retouch=1;` (history-jelzők) |
| **MEGFEJTVE A BINÁRISBÓL, EGY PARAMÉTER KALIBRÁLATLAN (#565)** | az algoritmuscsalád és a pixelművelet a natív kód visszafejtéséből egzakt, egyetlen csúszka affin leképezése maradt feltételezés | `radtint` (radiális **szorzó**-tint köbös smoothstep maszkkal; a Feather affin leképezéséhez golden-pár kell) |

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
- A `tint` `colorwheel version="0"`, az `ansel` `version="1"` — **két külön
  színkódolás**, ez a legerősebb nyom a `tint` `ffff`-anomáliára.
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
   analitikus modellje továbbra is nyitott (a `glow` sugara logaritmikus
   leképezésű: `<log>250.0</log>`).
3. unsharp kernel finomítás (dekonvolúciós illesztés)
4. `tint` színparaméter-formátum (ffff → R=0 anomália) — **új nyom**: a
   `tint` `colorwheel version="0"`, az `ansel`/`dir_tint` `version="1"`,
   és valós adatban a `tint` 4 hex jegyet ír (`ffff`), a másik kettő 8-at
   (`ffffffff`). A parszernek változó hosszú hex-színt kell tűrnie.
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
   `radblur` (3.2) → `glow2` (2.7).
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

A luminancia súlyozása 5 : 1 : 2 / 8 alakú egész szorzás
(`(x*5 + y + z*2) >> 3`); a csatorna-hozzárendelés a dekompilátumból nem
egyértelmű, **golden-ellenőrzést érdemel**.

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
