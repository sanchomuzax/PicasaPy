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

### `fill` — MEGOLDVA (analitikus gamma-LUT), 2026-08-18-án KIMÉRVE eredeti exportokhoz

20 lépéses s-sweep lemérve (`luts3.json: fill2d`); szomszéd-görbék közti
lineáris interpoláció max hibája **1,25/255** → tetszőleges s-re ±1 pontosságú
implementáció LUT-interpolációval. A `finetune2` p1 ugyanez a LUT.

**A mai megvalósításunk nem interpolál, hanem a natív képletet futtatja**
(`tone.py:112`): `gamma = 1/((1−s)·0,7 + 0,3)`,
`kitevő = 1/(gamma·0,7 + 0,3)`, `LUT[i] = 255·pow(i·gamma/255, kitevő)`,
majd `apply_fill` **árnyék-súlyozott keveréssel** viszi rá (a súly a
képpont `luma4`-jével fordított).

#### Mérés eredeti Picasa-exportokhoz (2026-08-18)

A privát repó `referencia/deritofeny/` mappájában **hat valódi Picasa-export**
van ugyanarról a képről (0 / 10 / 25 / 50 / 75 / 100 %). Eddig **egyetlen
mérés sem használta**. A mai kódunk ezekhez mérve:

| csúszka | ΔE átlag | ΔE max |
|---|---|---|
| 10 % | **1,20** | 7,35 |
| 25 % | **1,77** | 16,16 |
| 50 % | **1,33** | 18,79 |
| 75 % | 4,76 | 35,19 |
| 100 % | **1,58** | 70,71 |

Vagyis a `fill` a mérőszett „1,03–6,56" verdiktjénél **lényegesen jobb**:
öt pontból négyen 1,2–1,8 között van.

**A 75 %-os kilógás magyarázata:** `s = 0,80`-nal ugyanerre a képre a hiba
**4,76 → 2,02**-re esik. Egyetlen kilógó pont, aminek a két szomszédja
illeszkedik, sokkal valószínűbben **pontatlan csúszkaállás** az exportban
(a Picasa csúszkáját egérrel húzzák), mint modellhiba. **Nem nyitottunk rá
hibajegyet.**

> ⚠️ **Negatív eredmény, hogy a következő kör ne járja újra.** A
> `0x0090ac20` verem-követéséből 2026-08-18-án egy **fordított** képlet jött
> ki (`i·D/255` alap és `D/(0,7D+0,3)` kitevő, ahol `D = 0,7(1−s)+0,3`).
> A golden párokon mérve ez **11–127 szint** hibát adott, tehát megdőlt.
> A helyes alak a **reciprok**, ahogy a `tone.py:119` írja. Tanulság: az
> `fdivr`/`fdivrp` iránya kézzel könnyen elcsúszik — mérés nélkül nem
> szabad ilyen képletet kiadni.

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
  (RMSE 2,2/255 valódi fotón). A pontos kernel finomítása **továbbra is nyitva**
  (nem tökéletesen Gauss) — jegy: **#762**, a diszpécser (`0x00a42c20`) fel van
  térképezve, a konvolúció a `0xa43230`/`0x9e6340`-ben van. B/W teszteknél
  figyelem: telített értékeken a túllövés klippel.

### `Vignette=1,35.0,1.4,0.0,00000000` — maszk lemérve

Multiplikatív radiális maszk: közép 1,000 · r≈0,25: 0,994 · r≈0,45: 0,729 ·
r≈0,65: 0,328 · sarok: 0,250. (r = képmérettel normált távolság a középponttól.)
~~A paraméterek (35=belső sugár %, 1,4=erősség?) → analitikus illesztés nyitva~~
→ **ELAVULT JELÖLÉS (2026-08-16).** Az analitikus modell **megvan**:
[`filterdesc-registry.md`](filterdesc-registry.md) 4.3 — belső ragyogás,
`sugár = Blur · 0,02 · max(W,H) / 4`, az erősség a 2. paraméter. A mért
radiális profil ettől függetlenül érvényes kontroll marad.

### `autocolor` — csillapított lineáris fehéregyensúly (részleges)

Csatornánkénti lineáris korrekció (ki = a·be + c, |c|<1,5):
warmcast: R×0,936 / G×1,021 / B×1,058; bluecast tükörképe (R×1,032 / B×0,936).
A gainek a teljes szürkevilág-korrekció ~60–90%-a.

> ⚠️ **ELAVULT JELÖLÉS (2026-08-16):** *„a pontos csillapítási szabály
> (gray-world vs fehérpont-alapú) még nyitott"* — a becslő azóta
> **visszafejtve**: se nem szürkevilág, se nem fehérpont, hanem egy
> **64 × 64-es kétdimenziós hisztogram** az `R/G` és `B/G`
> kiegyensúlyozatlanságból, köbös Csebisev-súlyozással és súlyponttal.
> Ld. „Az `autocolor` becslője VISSZAFEJTVE" szakaszt. A csatornánkénti
> lineáris alak is **pontatlan**: az alkalmazó 3 × 3-as mátrix (#759).

## 5. kör — a 4–5. effekt-fül `filters=` kulcsai AZONOSÍTVA ✅ (#190)

A felhasználó Windows-os Picasa 3.9-éből, az effekt-kit alap-alkalmazásaiból
(2026-07-23). Minden effekt ini-alapú; a színparaméterek formátuma
`00RRGGBB` hex.

> ⚠️ **ELAVULT JELÖLÉS (2026-08-16):** *„a paraméterek JELENTÉSE
> (csúszka-leképezés) még nyitott — a 2. kör deríti fel előre írt
> ini-variánsokkal"* — erre **nem kellett** mérőkör: a `filterdesc.xml`
> (2026-08-06) minden csúszka **nevét, min–max tartományát és alapértékét**
> megadja ([`filterdesc-registry.md`](filterdesc-registry.md) 4.1–4.2), és a
> levezetett ini-sorrend mind a 8 valós mintán stimmel.

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
| `autocolor` | pixelhű→közelítés (0.00–1.55) | ✅ **teljes képlet MEGVAN** (#759): `M · diag(g) · M⁻¹` + csonkoló egész-osztás a becslőben, mérve **0,614** |
| `autolight` | mind közelítés (0.20–0.74) | ✅ kész |
| `glow` | közelítés (1.85 → **0,15–1,06** #668) | ✅ kész |
| `enhance` | közelítés, színöntetnél eltér (0.49–3.02) | ✅ jó (az autocolor-komponens húzza) |
| `sat` | negatív jó, pozitív romlik (0.70–12.71) → **0,74** (#693) | ✅ **kész** — a pozitív ág csatornánkénti gammája megvan ÉS be van kötve (`saturation_positive.py`) |
| `finetune2` | h/s alacsony jó, hő-extrém eltér (0.94–24.9) | ✅ **a Csúcsfények+Árnyékok EGY közös LUT — javítva (#879, 2026-08-18)**, a kompozit eltérés 217 szintről 0-ra · ⚠️ a hőmérséklet-tengely nyitva marad (a mai modell a mért görbékhez jobban illik, de a mérés vak a kereszt-tagokra) |
| `fill` | csak gyenge erősségnél jó (1.03–6.56) → **eredeti exportokhoz mérve 1,20–1,77** (2026-08-18) | ✅ jó — a 6,56 túlbecsülte |
| `glow2` | eltér (2.68) → **közelítés (0,18–1,19)** (#668) | ✅ kész |
| `radblur` | eltér (3.18) → **közelítés (0,09–0,68)** (#668) | ✅ kész |
| `Vignette` | eltér (4.65) | ✅ analitikus modell MEGVAN · **a zóna ELLIPSZIS — eredeti exportokkal igazolva (2026-08-18)** |
| `ansel` | eltér (5.60) → **fehér szűrővel 0,53** (#317) | ✅ fehérre kész · ⚠️ SZÍNES szűrőre nincs export |
| `dir_tint` | eltér (9.36) | ❌ |
| `tint` | eltér (13.6 a mai mérésben) | ❌ **a fő ok MEGVAN** (#872): a `preserve` skálája −1…255, plusz hiányzó szinthúzás és gamma |

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
| **MEGFEJTVE a filterdesc.xml-ből (#381)** | a lépéssorrend és a számértékek a Picasa saját `filterdesc.xml` `<effect>` csővezetékéből jönnek — nem golden-méréssel „visszafejtett" közelítés, hanem a Picasa TÉNYLEGES lépéssora (az alacsony szintű kernelek, pl. Gauss-elmosás, a szokásos megfelelőjükkel) | `Vignette`, `Matte`, `HDR`, `LocalContrast`, `Invert`, `CrossProcess`, `Sixties`, `Cinemascope`, `Orton`, `PencilSketch`, `HeatMap`, `NightVision`, `Holga`, `Lomo`, `Boost`, `Soften`, `Pixelate`, `QuantizePalette`, `TwoTone`, `Border`, `RoundedEdges`, `DropShadow`, `MuseumMatte`, `Polaroid`, `PicnikGrain` |
| **MEGFEJTVE A FILTERDESC + NATÍV KÓDBÓL ÉS VÉGIGMÉRVE (#878)** | a `filterdesc.xml` receptje mellé a natív `glimmer::EdgeDetectionBImageOperation` (`0x00bbca60`) TELJES belső lépéssora is megvan, és a `TintImageOperation` pixelmatematikája golden párból MÉRVE (fényesség-tartó színezés); a #685 mérőszettjén ΔE 113,89 → **4,72**, SSIM −0,002 → **0,866** | `Neon` |
| **MEGFEJTVE A FILTERDESC-BŐL ÉS VÉGIGMÉRVE (#884)** | a művelet a #878-ban megfejtett, FÉNYESSÉG-TARTÓ `TintImageOperation` (a `Neon` záró lépésével közös): a bemenet Rec.601 lumáját bájtra megőrzi, és csak a szín krómáját cseréli. A korábbi modell tömör színréteget kevert a képre, tehát `Fade = 0`-nál egyszínű felületet adott (ΔE 33,45 / SSIM 0,63); most **ΔE 1,50 / SSIM 0,9991** = JPEG-zaj szint. Ecset-eszköz híján továbbra is a TELJES KÉPRE fut, amit a #685 exportja igazol | `PicnikTint` |
| **MEGFEJTVE A BINÁRISBÓL (#566)** | a `filterdesc.xml` csak a paraméterNEVEKET és a FIX konstansokat adja, de a `Picasa3.exe` statikus visszafejtése a teljes belső kernelt feltárta (`glimmer::IRImageOperation`, RTTI/vtable `0xcf0a14`, ctor `0xbc3d80`, feldolgozás `0xbc3f50`) | `IR` |
| **MEGFEJTVE, DE ECSET-MASZK NÉLKÜL (#381)** | a csővezeték/paraméterezés egzakt, és az effekt TELI maszkkal indul: a #685 exportján a Picasa maga is a teljes mérőképre vitte fel (`PicnikTint` ΔE 36,9, `Soften` ΔE 5,5), ezért nálunk is a TELJES KÉPRE fut (jelezve a `ChainReport.range_warnings`-ban) | `Soften` |
| **MEGFEJTVE, DE ÜRES ECSET-MASZKKAL INDUL (#688)** | a pixel-matematika egzakt, de az effekt **befestés nélkül nem csinál semmit**: a #685 exportján a Picasa a `min` és az `alap` álláson egyaránt érintetlenül hagyta a mérőképet (ΔE 0,18 = JPEG-zaj), miközben a korábbi, teljes képes modellünk ΔE 57,5 / 54,6 mértékben átfestette. Maszk nélkül tehát AZONOSSÁG; a `mask` paraméterrel a visszafejtett csővezeték lefut | `ReanimatedEyeColor` |
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
eszköz híján a `PicnikTint` a TELJES KÉPRE fut, a `ReanimatedEyeColor`
pedig — **#688 óta** — változatlanul hagyja a képet (üres maszkkal indul).
A kalibráció (a maradék KÖZELÍTŐ effektekhez
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

> ⚠️ **MÉRVE (#1142): a 3.9.141.259 a `PicnikFocalPixelate`-et sem futtatja
> le.** A `merokit-2` szettben mindkét alak — a hétparaméteres
> `PicnikFocalPixelate=1,0.500000,0.500000,40.000000,60.000000,50.000000,0.000000;`
> és a négyparaméteres `PicnikFocalPixelate=1,40.000000,60.000000,50.000000,0.000000;`
> — **a forrást adta vissza** (0,164 eltérés = a JPEG-újratömörítés
> zajszintje), miközben a PicasaPy 29,19-es eltérést okozott. A lánc ezért
> a #1142 óta NEM futtatja (`chain.MEASURED_NOT_RUNNING_OPS`); a fenti
> csővezeték maga megmarad (`render/focal.py`), csak nem hívjuk.
>
> Hogy az OK a névregisztráció hiánya vagy a paraméterszám, a mérés nem
> dönti el: mindkét paraméterszám egyformán tétlen maradt. Azt sem tudjuk,
> hogy a tag **elvágja-e** mögötte a láncot (#1140) — a szettben egyik
> esetben sem áll mögötte másik tag.

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

#### A Feather affin leképezése — MEGFEJTVE A KÓDBÓL (2026-08-15, #317)

**Nem kellett golden-pár.** A `radtint` callbackje (`0x008f8730`) a
munkafüggvényt (`0x0090b370`) hívja, az pedig a **közös radiális
maszképítőt** (`0x0090aeb0`) — ugyanazt, amit a `radsat` és a `radblur` is
használ:

```c
// FUN_0090aeb0(elesseg, sugar_param), a maszktabla 1024 elemu
r  = min((x1-x0)/2, (y1-y0)/2) * (sugar_param + 1.0f);
r2 = r*r;  shift = 0;
while (r2 > 1024.0f) { r2 *= 0.5f; shift++; }        // a shift a hivonak megy

for (i = 0; i < 1024; i++) {
    t = sqrtf(i * (1.0f/1024.0f) * (1024.0f/r2));
    v = 0.5f + (1.0f/(1.0f - elesseg*0.99f)) * (t - 0.5f);
    v = 1.0f - clampf(v, 0.0f, 1.0f);
    tabla[i] = lroundf((3.0f - 2.0f*v) * v * v * 255.0f);   // smoothstep
}
```

**A döntő részlet:** a `radtint` hívása szó szerint `FUN_0090aeb0(0, param_6)`
— az **élesség argumentuma nulla, beégetve**. Nullánál `1/(1 − 0·0,99) = 1`,
tehát `v = t`, és az élesség-tag **teljesen kiesik**. A `radsat`/`radblur`
ugyanide nem nullát ad át (`FUN_0090aeb0(param_7, param_5)`, ill.
`FUN_0090aeb0(fVar9, param_7)`), tehát ez nem a dekompiláló tévedése, hanem
a `radtint` sajátja.

Marad tehát **egyetlen** paraméter, és annak leképezése egyenes:

> **`sugár = min(szélesség, magasság)/2 × (Feather + 1)`**

A `filterdesc.xml` szerint a Feather tartománya `[0..1]`, alapértéke `0,25` —
vagyis a sugár a fél-kisebbik-oldal **1,0-szeresétől 2,0-szereséig** megy,
alapértelmezésben **1,25-szörös**. A `param_6` a paraméterblokk `+0x28`
rekesze, ami a többi effektnél is az **első csúszka** (a `tint`-nél ugyanez a
rekesz az erősség).

**Ezzel elesik a korábbi, dokumentált feltételezésünk** (átmeneti sáv
`(0,5 ± feather/2)·r_max` között): a valóságban nincs külön „sáv", a
smoothstep a `sqrt`-tel skálázott sugáron fut végig, és a Feather **magát a
sugarat** nyújtja.

*Bizonyítottsági fok: megerősített* (a hívási hely és a táblaépítő is
visszafejtve; a `sqrt` azonosítása `0x0049fe60 → 0x00c0b310` alapján erős).
A golden-pár innentől **validáció**, nem felfedezés.

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
  - a hisztogram a kép **90% × 90%-os, vízszintesen BALRA IGAZÍTOTT**
    ablakáról készül (#721 pontosította — ld. lent az `enhance` szakaszt),
  - a vágási küszöb a **teljes kép képpontszámának 1/200-a**, mindkét
    végén **azonosan** (az aszimmetrikus változatok a mérésen rosszabbak),
  - ~~a nyújtás bemeneti tartománya nem mehet **58 szint alá**
    (`_MIN_STRETCH_SPAN`)~~ — **törölve a #721-ben**: az az 58 nem korlát
    volt, hanem a vágópont-keverés lenyomata (ld. lent),
  - a vágópontok **30%-ban a közös `[loMin, hiMax]` felé keverednek**
    (`enhance`), illetve teljesen közösek (`autocontrast`) — #721.

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

> ⚠️ **Ez a két zárt képlet csak KÜLÖN-KÜLÖN érvényes.** Ha mindkét csúszka
> nem nulla, az eredeti **nem** futtatja őket egymás után, hanem egyetlen
> közös leképezést számol: `ki = clip( (be − 255·s) / ((1−h) − s) )`. A
> különbség a maximumon 217 szint. Részletek: „A `finetune2` SZERKEZETE"
> szakasz (#879).

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

1. ~~autocolor pontos gain-képlete~~ — **MEGVAN** (2026-08-16): a becslő a
   `0x0090f8f0`, az alkalmazó `M · diag(g) · M⁻¹`; ld. az „Az `autocolor`
   MÁTRIX-ÉPÍTŐJE VISSZAFEJTVE" szakaszt és a **#759**-et. Egyetlen kép
   (`Empty Space`) marad, ott a **becslő** téved, nem az alkalmazó.
2. ~~Vignette analitikus modell~~ — **MEGVAN** (`filterdesc-registry.md`
   4.3): belső ragyogás, `sugár = Blur·0,02·max(W,H)/4`. A `glow`/`radblur`
   analitikus modellje **is MEGVAN (#668)** — natív IIR-mag + mért
   előgörbe/maszk, ld. lent a #668 szakaszt. (A `glow` sugara valóban a
   logaritmikus leképezés eredménye: `<log>250.0</log>`, és képpontban
   értendő.)
3. unsharp kernel finomítás (dekonvolúciós illesztés)
4. ~~`tint` színparaméter-formátum (ffff → R=0 anomália)~~ → **LEZÁRVA
   (2026-08-16): saját tesztadat-artefaktum, ld. lent.** Az eredeti jegyzet: valós adatban a
   `tint` 4 hex jegyet ír (`ffff`), a másik kettő 8-at (`ffffffff`). A
   parszernek változó hosszú hex-színt kell tűrnie. **A korábbi „két külön
   színkódolás" nyom (colorwheel version) 2026-08-15-én megdőlt**; a
   render-oldal viszont teljes, és a szín `0x00RRGGBB` sorrendű.
5. ~~retouch/redeye régió-adatok~~ — **LEZÁRVA (2026-08-16), NEGATÍV
   eredménnyel: a `.picasa.ini` NEM tartalmaz régió-adatot hozzájuk**, lásd
   „A `redeye` és a `retouch` sosem hordoz régiót" alább. A text overlay
   (`text=`) formátuma a #371-ben megfejtve.
6. ~~**Összehasonlító harness** (PicasaPy render vs golden, SSIM/ΔE)~~ —
   KÉSZ (#115): `tools/golden/compare_render.py`, ld. lent.
7. ~~a 4–5. effekt-fül paraméter-jelentései (#190 2. kör)~~ — **MEGOLDVA
   (2026-08-06)**: a `filterdesc.xml` minden effekt minden csúszkájának
   nevét, min–max tartományát és alapértékét megadja, és a levezetett
   ini-sorrend mind a 8 valós mintán stimmel
   ([`filterdesc-registry.md`](filterdesc-registry.md) 4.1–4.2). A
   `make_param_sweep.py` találgatott tartományai lecserélhetők a pontos
   értékekre; a sweep innentől **ellenőrzés**, nem felfedezés.
   ~~Nyitva maradt: a `Cinemascope` jelölőnégyzet polaritása és a
   `PicnikFocalPixelate` puck-sorrendje.~~ → **MINDKETTŐ LEZÁRVA
   (2026-08-16)**, ld. lent. — az eredeti jegyzet:
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
9. ~~**`finetune` v1 ↔ `finetune2` v2 hőmérséklet: 2× skála-hipotézis**~~ →
   **MEGDŐLT (2026-08-16), ld. lent.** Az eredeti jegyzet: A `filterdesc.xml` szerint a v1 tartománya `[−0,5..0,5]`, a
   v2-é `[−1..1]`; ha a görbe azonos, akkor `v2_érték = 2 · v1_érték`
   pontosan reprodukálja a v1 kimenetét. Egy meglévő golden-párral (v1
   `0,25` vs v2 `0,5`) olcsón ellenőrizhető — igazolás esetén a v1-hez
   **nem kell külön LUT**, és a 8. pont „finetune2-hő" tétele is olcsóbb
   lesz.
10. **`fullres` / `slow` / `resize` jelzők beépítése a renderelőbe.**
    ⚠️ **RÉSZBEN KÉSZ (2026-08-16):** az ADAT megvan és ki is számoljuk
    (`render/registry.py:156` `chain_flags`, a `ChainReport` hordozza), de
    **egyetlen fogyasztója sincs** — lásd „A sáv-jelzőknek nincs
    fogyasztója" alább. Az eredeti jegyzet: A
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

### `ansel` — a SÚLYOZÁS igazolva: a mag NORMALIZÁL az összeggel (2026-08-23, #939)

A #939 azt rögzítette, hogy a szűrőszín **súlyozó** szerepe
„következtetés", mert az egyetlen exportunk fehér szűrős, ahol minden
súlyozási modell ugyanazt adja — és ezért a jegy **felhasználói exportra
várt**. **A kód viszont eldönti**, export nélkül is.

**1. A visszahívás (`0x008f8410`) három nyers súlyt képez** a `+0x50`
szűrőszín három bájtjából, mindet **ugyanazzal az osztóval**:

```asm
0x008f8461  fld   qword ptr [0xcf39d0]   ; K
0x008f846b  fdiv  st(1), st(0)           ; bájt2 / K
0x008f8489  fdiv  st(1)                  ; bájt1 / K
0x008f8493  fdivrp st(1)                 ; bájt0 / K
0x008f84b1  call  0x0090e680             ; a három súly átadva
```

`[0xcf39d0]` **mérve: `255.0`** → a nyers súlyok `c/255`. Eddig ez volt
ismert — és **önmagában félrevezető**, mert így fehér szűrőnél
`(1, 1, 1)` jönne ki, ami túlcsordulna.

**2. A mag (`0x0090e680`) ELSŐ dolga: normalizálás az ÖSSZEGGEL.**

```asm
0x0090e6b7  fld  [ebp+0xc]      ; w1
0x0090e6c1  faddp st(2)         ; w1+w2
0x0090e6c8  faddp st(3)         ; w1+w2+w3          <- ÖSSZEG
0x0090e6ca  fld1
0x0090e6cc  fdivrp st(3)        ; 1 / összeg
0x0090e6de  fstp [ebp+0xc]      ; w1 := w1 / összeg
0x0090e6e3  fstp [ebp+0x10]     ; w2 := w2 / összeg
0x0090e6e8  fstp [ebp+0x14]     ; w3 := w3 / összeg
```

majd mindhármat **256,0**-lal (`[0xcf39d8]`) szorozva egészre kerekíti
(`0x00c29990`) a fixpontos csatornasúlyokhoz.

> ✅ **Ez pontosan a mi képletünk.** A `/255` a normalizálásban **kiesik**,
> így a natív számítás azonos a
> `szürke = Σ(szín_c · c) / Σ szín_c` alakkal
> (`src/picasapy/render/tinting.py`, `apply_ansel`).
>
> ⇒ **A súlyozás NEM következtetés többé, hanem megerősített.** A színes
> szűrős export a *képlet eldöntéséhez* **nem szükséges**; legfeljebb
> végponttól végpontig tartó visszaigazolás lenne — az viszont a
> **tónusgörbét** ellenőrizné, ami a színtől független, és fehér szűrővel
> már 0,53-on áll.

*Bizonyítottsági fok: **megerősített** — mindkét konstans a fájlból
kiolvasva (`255.0`, `256.0`), a normalizálás lépésről lépésre a
lebegőpontos veremműveletekből.*

### `tint`

A `+0x50`-es színt használja, a keverési arány `256 − round(amount)`, és
figyelembe veszi a `Preferences/CarefulEnhance` beállítást.

### Ami maradt

- a `sat` luminancia-súlyainak csatorna-hozzárendelése (5:1:2);
- ~~az `ansel` hisztogram utáni lépése~~ — a mért tónusgörbe
  (`_ANSEL_ANCHOR_CURVE`) fehér szűrővel **0,53**-ra viszi az eltérést
  (volt 6,11);
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
| `autocontrast` | `0x008f89d0` → `0x009db610` | **KÖZÖS** (`keverés = 1,0`) — ld. lent | 90 % × 90 %, balra igazítva (#721) |
| `enhance` („Jó napom van") | `0x008f8840` → `0x009db610` | **30 %-ban közös** (`keverés = 0,30`) — ld. lent | 90 % × 90 %, balra igazítva (#721) |

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

*(Az `enhance` sora a #721 keverés-lelete ELŐTTI állapot; a bevezetés után
**0,57** — ld. a következő szakasz végén a mérést.)*

~~**NYITVA marad az `enhance` kiugró képe**~~ („Utopic Unicorn", 13,3): ott a
Picasa által ténylegesen alkalmazott bemeneti tartomány két csatornán
**szélesebb, mint magának a csatornának a teljes értékkészlete** (zöld:
12–47 helyett 18,2–76,3), tehát *semmilyen* darabszám-küszöb nem adhatja ki.
Ebből született a `_MIN_STRETCH_SPAN = 58` mért korlát — **a #721 keverése
zárta le: nem gain-korlát volt, hanem magának a keverésnek a lenyomata**
(ld. a következő szakasz végét). Amit ez a kör kizárt: az
`autolight`+`enhance` bármely sorrendű összetétele (5,97–6,07), az
azonossággal való erősség-keverés, a 252-es korlát, és minden 1/100–1/400
közötti vágási osztó (a legjobb így is 2,56).

### ⚠️ MEGVAN A KÉT ELVESZETT FLOAT — és megdől a „mindkettő csatornánként vág" (#721, 2026-08-16)

A `0x009db610` **diszasszemblálva**, utasításszinten (nem dekompilátumból):
a függvény **nem** „csatornánkénti", és nem is „uniós" — a kettő **között**
áll, és a keverés mértékét a **hívó adja át float paraméterként**.

#### A függvény valódi működése

```c
// 1) A KÉT PARAMÉTER (0x009db610 prológusa)
float keveres = param_float;                    // [esp+0xc30]
if (keveres == -1.0f) keveres = 0.30f;          // 0xcf3ed0 = -1.0f (jelző)
                                                // 0xc7dcc8 = 0.30f (alapérték)
if (param_bool /*[esp+0xc2c]*/) { skala = 0.5f; felso = 252; }   // 0xc7dafc = 0.5f
else                            { skala = 1.0f; felso = 255; }

// 2) AZ ELEMZŐ ABLAK  (0x009db6ac-0x009db714)
y0 = 5*H/100;  y1 = 95*H/100;      // FÜGGŐLEGESEN középre  → 0,9·H sor
x0 = 5*W/100;  x1 = 95*W/100;      // a DARABSZÁM 0,9·W ...
// ...de a sor-mutató a SOR ELEJÉRŐL indul (`mov eax, esi`, 0x009db712),
// az x0 eltolás SOHA nem kerül hozzá  →  az ablak [0 .. 0,9·W)

// 3) HÁROM KÜLÖN hisztogram (3 × 256 × 4 bájt), BGRA sorrendben:
//    [px+2]=R → 0x34, [px+1]=G → 0x434, [px+0]=B → 0x834

// 4) A KÜSZÖB — a TELJES kép területére (0x009db765)
kuszob = max(1, (W*H) / 200);      // előjeles imul 0x51eb851f + sar 6

// 5) CSATORNÁNKÉNTI vágópontok
lo_ch = az a szint, ahol alulról a kumulált szám eléri a küszöböt
hi_ch = ugyanez felülről (255-től lefelé)

// 6) A KÖZÖS pontok
hiMax = max(hi_R, hi_G, hi_B);
loMin = min(lo_R*skala, lo_G*skala, lo_B*skala);

// 7) ⭐ A KEVERÉS — ez a lényeg (0x009db8b7-0x009db935)
hi_ch' = hi_ch + keveres * (hiMax - hi_ch);
lo_ch' = lo_ch + keveres * (loMin - lo_ch);

// 8) fixpontos gain
gain_ch = (felso << 16) / (hi_ch' - lo_ch');
```

`keveres = 0` → tiszta csatornánkénti · `keveres = 1` → teljesen közös (uniós).

#### Amit a hívók átadnak — ez választja szét a két szűrőt

| szűrő | belépő | float | bool | jelentés |
|---|---|---|---|---|
| **`enhance`** | `0x008f8840` | `-1.0` → **0,30** (`0x008f8892`) | a **`CarefulEnhance`** beállítás (`Preferences`-ből olvasva, `0x008f884b`) | **30 %-ban közös**, 70 %-ban csatornánkénti |
| **`autocontrast`** | `0x008f89d0` | **`1.0`** (`fld1`, `0x008f89fd`) | fixen **0** (`push 0`, `0x008f8a03`) | **teljesen közös** vágópont |

További három hívó (`0x00802180`, `0x008f92d0`, `0x008f9630` = `tint`)
szintén a `-1.0` jelzőt adja át, tehát a **0,30-as alapértéket** használja.

#### Következmény — két állításunk dől meg

1. **Az `autocontrast` NEM csatornánként vág**, hanem **közös** `[loMin, hiMax]`
   tartományra — vagyis megőrzi a színegyensúlyt. A fenti táblázat javítva.
2. **Az `enhance` sem tisztán csatornánkénti**: a csatornánkénti pontokat
   **30 %-kal a közös felé húzza**. A mai `apply_enhance` és
   `apply_autocontrast` (`render/ops.py`) egyaránt **tiszta csatornánkéntit**
   (`keveres = 0`) számol, és a kettőt **azonosnak** tekinti — a docstring ezt
   ki is mondja. Ez a natív kód szerint téves.

*Miért nem látszott a #685 szürke rámpáján:* ott mindhárom csatorna azonos,
tehát `lo_ch = loMin` és `hi_ch = hiMax` — a keverés **bármilyen** értéknél
ugyanazt adja. A rámpa a keverést elvileg sem tudja mérni; **valódi, színes
képpár kell hozzá** (a `referencia/imfeellucky/` 12 párja pont ilyen).

#### A `CarefulEnhance` hatása is megvan

A bool ág **nem csak** a 252-es felső korlátot kapcsolja: a **feketepontokat
0,5-tel szorozza** a közös minimum képzése előtt (`0x009db845`,
`0xc7dafc = 0.5f`). A korábbi „252-es korlát kizárva" mérés tehát csak a
felső korlátot vizsgálta, a felezést nem.

*Bizonyítottsági fok: megerősített* — utasításszinten visszakövetve
(`0x009db610` prológus, `0x009db6ac`–`0x009db714` geometria, `0x009db765`
küszöb, `0x009db876`–`0x009db935` keverés), a konstansok a `.rdata`-ból
kiolvasva (`0xcf3ed0 = -1.0f`, `0xc7dcc8 = 0.30f`, `0xc7dafc = 0.5f`), a
hívók paraméterei a hívási helyekről.

#### ✅ A modell MÉRVE — és a `_MIN_STRETCH_SPAN = 58` rejtélye megoldva

A visszafejtett modellt lefuttattam a **12 golden-páron**
(`referencia/imfeellucky/`, mérőszkript:
`referencia/eszkozok/721-enhance/enhance_model.py`):

| modell | átlagos eltérés |
|---|---:|
| tiszta csatornánkénti, korlát nélkül | 5,799 |
| **a mai kódunk** (csatornánkénti + `_MIN_STRETCH_SPAN = 58`) | **2,480** |
| **visszafejtett: keverés 0,30, korlát NÉLKÜL** | **0,727** |
| teljesen közös (keverés 1,0) | 4,808 |

**A keverés-söprésnek éles minimuma van pontosan a binárisból kiolvasott
0,30-nál** — 0,25-nél 1,115, 0,30-nál **0,727**, 0,35-nél 1,131. A kódból
olvasott konstanst tehát a mérés **függetlenül megerősíti**.

Képenként **egyetlen kép sem romlik**, és a kiugró eset megszűnik:

| kép | mai modell | visszafejtett |
|---|---:|---:|
| **Utopic Unicorn** | **13,03** | **0,72** |
| Sunny Autumn | 4,90 | 1,27 |
| Redes de hilo | 3,11 | 1,03 |
| Music – tomasino.cz | 2,30 | 0,71 |
| a többi nyolc | 0,20–1,49 | 0,20–0,97 |

#### A `_MIN_STRETCH_SPAN = 58` NEM korlát — a keverés mellékhatása

A #539 azt mérte, hogy „a ténylegesen alkalmazott bemeneti tartomány
legkisebb értéke mind a 36 csatornán 58,1, és a Picasa sosem megy alá".
Ebből egy beégetett gain-korlátra következtettünk. **Nincs ilyen korlát** —
a `0x009db610` alkalmazó ciklusa (`0x009db9d0`–`0x009dba21`) csak a
KIMENETET vágja `[0, felső]`-re, a gainre semmilyen felső határ nincs.

A jelenség a keverésből jön. A kiugró képen a nyers csatorna-tartományok:

```
nyers:            [79, 26, 26]
keverés 0,30 után [96, 59, 59]     ← innen a „soha nem megy 58 alá”
keverés 1,0 után  [135, 135, 135]
```

A keverés minden csatornát a közös `[loMin, hiMax]` felé húz, ami a **szűk**
csatornákat kiszélesíti. Az „58" tehát ennek a mérőkészletnek a véletlene,
nem konstans. A modellben a korlát **fölösleges**: vele és nélküle a 12 páron
bájtra azonos az eredmény (0,727 mindkettő).

*Bizonyítottsági fok: megerősített* (kódból ÉS méréssel, egymástól
függetlenül).

**Ami ezzel lezárult:** a #539 „a `_MIN_STRETCH_SPAN` mért, nem visszafejtett
viselkedés" megjegyzése tárgytalan — a konstans **elhagyható**.

#### ✅ MEGVALÓSÍTVA (#721, `render/ops.py`)

A keverés `blend` paraméterként bekerült az `apply_channel_levels_stretch`-be
(`_blend_clip_points`); az `enhance` **0,30**-cal, az `autocontrast` **1,0**-del
hívja — **a kettő ezzel szétvált**, korábban ugyanaz a függvény volt. A
`careful` kapcsoló a felezett feketepontokat és a 252-es korlátot adja.
A `_MIN_STRETCH_SPAN = 58` a kódból **törölve** (a fenti levezetés szerint
fölösleges).

**A megvalósítás mérése pontosít egy részletet:** a kevert vágópontok egésszé
alakítása **csonkolással** történik (a C `float → int` cast), nem kerekítéssel
— és ez mérhető. Ugyanazon a 12 páron:

| | átlagos eltérés |
|---|---:|
| kerekítve | 0,727 |
| **csonkolva (ez a megvalósított)** | **0,572** |

A fenti kutatói táblázat 0,727-es sora tehát a kerekített változaté; a
kódban a csonkolt, 0,572-es modell fut. A kiugró kép (Utopic Unicorn)
13,035 → **0,521**. A `CarefulEnhance` ága a referencia-exportból ezzel
**kizárva** (2,366 ≫ 0,572).

**Ami NYITVA marad:** a 0,572 maradékának forrása (JPEG-újratömörítés kontra
modell-hiba) nincs szétválasztva.

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
  pontosan teljesül. ~~**Az eltérés oka nyitott** — a #317 dolga eldönteni,
  hogy a dekompilált konstans olvasata pontatlan-e, vagy a natív hívás
  máshonnan kapja a szélességet.~~ → **A KÉT ÁG KÖZÜL AZ EGYIK LEZÁRVA
  (2026-08-16), ld. lent.**

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

#### A `preserve` SKÁLÁJA: `w = 256 − p`, csonkítva (2026-08-16, #872)

A „Color Preservation" csúszka tartománya a `filterdesc.xml` szerint
**`[-1..255]`** — nem 0…100. A bináris ezt egészre **csonkítja**, és a
telítetlenítés súlya `256 − p`:

```asm
0x008f96b2  fld   dword ptr [ecx + 0x28]   ; a preserve (float)
0x008f96a9  or    eax, 0xc00                ; FPU: CSONKÍTÁS nulla felé
0x008f96bc  fistp qword ptr [esp + 0x20]    ; egészre
0x008f96c4  cmp   ecx, 0x100                ; == 256 ?
0x008f96ce  je    0x8f96f7                  ;   → a lépés KIMARAD
0x008f96e9  mov   edx, 0x100
0x008f96ee  sub   edx, ecx                  ; w = 256 − preserve
0x008f96f2  call  0x9a9550                  ; telítetlenítés
```

Vagyis **`p = 256` a tétlen eset**, `p = −1` a legerősebb (teljes szürke).
Az éles `tint=1,79.842102,ffff` esetnél `w = 177` → **31 % króma marad**;
a mai kódunk `keep = 0,798`-cal **80 %-ot** hagy meg, és 100 fölött vág,
ezért nála a 127-es és a 255-ös beállítás **azonos** képet ad.

*Bizonyítottsági fok: megerősített* (a bináris és a `filterdesc.xml`
egymástól függetlenül).

#### A `tint` SZINTHÚZÁSSAL kezd — megerősítve (2026-08-16)

A `0x008f9630` a telítetlenítés ELŐTT beolvassa a `"CarefulEnhance"`
beállítást (`0x008f9661`), és `-1,0f`-fel — az „alapértelmezett keverés"
jelzőjével (`0xcf3ed0`) — meghívja a **`0x009db610`**-et (`0x008f9698`),
ugyanúgy, mint az `enhance`.

A `0x009db610`-nek **öt** hívója van, ebből négy szűrő-callback:

| hívó | szűrő |
|---|---|
| `0x008f8840` | `enhance` |
| `0x008f89d0` | `autocontrast` |
| `0x008f92d0` | `rainbow` |
| **`0x008f9630`** | **`tint`** |
| `0x00802180` | (nem szűrő) |

**És felhasználja: a `0x009db610` HELYBEN módosítja a képet.**

```asm
0x009dba0b  sub   ecx, dword ptr [esp + 0x2c] ; (be − feketepont)
0x009dba0f  imul  ecx, dword ptr [esp + 0x24] ; × erősítés (16.16)
0x009dba14  sar   ecx, 0x10
0x009dba17  jns / xor ecx, ecx                 ; alsó vágás
0x009dba1d  jle / mov ecx, ebx                 ; felső vágás
0x009dba21  mov   byte ptr [edx], cl           ; ← VISSZAÍRÁS
0x009dba3c  jb    0x9db9b0                      ; sor-ciklus
```

A függvény **1084 bájt, egyetlen kilépési ponttal** (`0x009dba4e`) — nincs
korai visszatérés, tehát a szinthúzás **mindig lefut**; kimeneti mutatója
nincs, a visszatérési értéke konstans 0 (`0x009dba45`). A két paramétere:
a `CarefulEnhance` (BE → 0,5-ös tényező és 252-es fehérpont, KI → 1,0 és
255) és a vágópont-keverés (`-1,0f` → az alapértelmezett **0,30**).

Vagyis a `tint` **hat lépésből** áll:

| # | lépés | cím |
|---:|---|---|
| 1 | előkészítés | `0x9aabf0` (`0x008f965b`) |
| **2** | **szinthúzás helyben**, 0,30-as keveréssel | `0x9db610` (`0x008f9698`) |
| 3 | telítetlenítés `w = 256 − preserve`-vel | `0x9a9550` (`0x008f96f2`) |
| 4 | a szín ICC-átvezetése (rendszerint `NULL`) | `ctx->vtbl[2]` (`0x008f972d`) |
| 5 | telítettségfüggő gamma-LUT, kitevő `1/k` | `0x00aa40a0` |
| 6 | szorzó keverés, `max`-ra normálva | `0x009db4f0` |

Ugyanez érvényes a **`rainbow`**-ra és az **`autocontrast`**-ra is (mindkettő
hívja a `0x009db610`-et) — nálunk egyik sincs renderelve.

*Bizonyítottsági fok: megerősített.*

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

// 2) a színezőszín átvezetése a virtuális átalakításon   (ELHAGYHATÓ — #872:
//    a lánc-kontextus [ctx+8] mezője, a szokásos úton nem áll be)

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

#### A `colorwheel version="0"` vs `="1"` — nem a színkódolás különbsége

Az `editpanel.tre` elrendezés-erőforrás és az `editpaneltext.tre` feliratai
eldöntik: a szerkesztőpanelen **két színválasztó kerék** van,
`editpanel/colorwheel0` és `editpanel/colorwheel1`, közös
`editpanel/colorwheel_container`-ben, mindkettőhöz saját `slidercircle{0,1}`
körkörös csúszka (`Property buddy`) és saját felirat — **mindkettő szövege
„Pick Color"**. A kódban a névsablon `editpanel/colorwheel%d`
(`0x00c86f2c`, hivatkozók közt `0x007518e0`, `0x005fa770`).

**A döntő cáfolat viszont a saját adatunkból jön**, nem a keresésből: a
[`filterdesc-registry.md`](filterdesc-registry.md) 3. táblázata szerint a
`dir_tint` és a `radtint` **szintén `version="0"`**, és mindkettő **8 hex
jegyet** ír (`ffffffff`) — ugyanúgy, mint a v1-es `ansel`. A `version` és a
hex-hossz tehát **nem korrelál**; a „v0 = más színkódolás" feltevés a saját
mérési adatunkon bukik el. *Bizonyítottsági fok: megerősített (cáfolat).*

Amit **helyette** valószínűsítünk, de nem bizonyítottunk: a `version` a
**vezérlő-példány sorszáma** (0 vagy 1) — ezt támogatja, hogy a panelen
pontosan két kerék van, a `filterdesc` külön elemtípust használ a
színkorongra (`<colorcircle id="0"/>`), és hogy az `ytColorWheelNode`
visszafejtett slotjai (`0x00a63280`, `0x00a63340`, `0x00a64c20`,
`0x00a61f90`) mind **elrendezés és találatvizsgálat** — sehol nincs
kerék-koordináta → RGB leképezés. *Bizonyítottsági fok: feltételes.*

**Következmény:** a `ffff` magyarázatát máshol kell keresni. A legvalószínűbb
prózai ok: az író **elhagyja a vezető nullákat** (`0x0000ffff` → `ffff`), és
a `tint` alapértelmezett színe tényleg R=0 (ciános). Ezt **golden-párral**
kell eldönteni, nem kódolvasással (#679).

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

## `warm`, `grain`, `unsharp`, `blur` — natív visszafejtés (2026-08-15, #317)

Egy kör (`DecompileKalibralatlan.java`, gyökerek a natív callback-regiszterből:
`0x008f8930` warm, `0x008f88e0` grain, `0x008f8520`/`0x008f9bf0` radblur,
`0x008f8f70` glow, `0x008f8f30` unsharp, `0x008f89a0` blur; mélység 2).

### `warm` (Melegítés) — PIXELPONTOS, beégetett LUT ✅

A `warm` **nem képlet, hanem egy fordítási idejű, 256 elemű tábla**
(`DAT_00d33b70`, RVA `0x933b70`, a `.data` szekcióban). A ciklus
(`FUN_0090c040`):

```c
out.B = (tabla[in.B]      ) & 0xff;
out.G = (tabla[in.G] >>  8) & 0xff;
out.R = (tabla[in.R] >> 16) & 0xff;
out.A = 0xff;                          // az alfa mindig telitodik
```

Mindhárom csatorna **ugyanabból** a táblából olvas, csak más bájtot vesz ki —
tehát valójában három, egymásba fésült csatorna-LUT. Csúszkája nincs: a
`warm` fix transzformáció.

**Hogy ez tényleg konstans, és nem futásidőben épül:** a `.text`-ben pontosan
**három** hivatkozás mutat rá (`0x0090c0ab`, `0x0090c0b2`, `0x0090c0cb`),
mind a három ugyanennek a ciklusnak az **olvasása** — írója nincs; a tábla a
lemezen nem nulla, monoton tartalommal áll.

> **Ezt a táblát a projekt már ismerte.** A #611 ugyanezt kinyerte, és
> `src/picasapy/render/warmify_lut.py` néven **be is került a kódba**. A mai
> kör független újrakinyerése **bájtra azonos** eredményt adott (256×3 érték),
> tehát ez nem új felfedezés, hanem a meglévő tábla **független
> megerősítése** — ami önmagában is ér annyit, hogy a `warm` biztosan nem
> szorul kalibrációra. A privát repóban `referencia/warm-lut.md` a kinyerés
> módszerével; a #611-es forrás-CSV ugyanott
> `referencia/dekompilalt-576/warmify-lut.csv`.
*Bizonyítottsági fok: megerősített, két független kinyeréssel.*

### `unsharp` / `unsharp2` — a sugár BEÉGETETT 1,5 ✅

```c
FUN_0090c4a0(dst, src, /*sigma*/ 1.5f, /*amount*/ *(p + 0x28));
// 1) elmosas ugyanabba a cel-pufferbe (a kozos elmosomotor, 2-es mod)
// 2) pixelenkent:
out.A = src.A;
out.C = clamp0_255( ((src.C - blur.C) * k >> 8) + src.C );
```

Vagyis a klasszikus életlen maszk: **`ki = be + erősség · (be − elmosott)`**.
A sugár (`0x3fc00000` = `1.5f`) **argumentumként beégetve** érkezik — nem
csúszka, nem képarányfüggő. Az `unsharp` és az `unsharp2` **ugyanaz a
callback**; a `filterdesc.xml` szerint csak az Amount felső korlátja tér el
(1,0 vs 3,0), ami ezzel a képlettel konzisztens.
*Bizonyítottsági fok: megerősített* (a képlet és az 1,5).
~~**Nyitva:** magának az elmosómagnak a pontos alakja (a `FUN_00a42c20` mögötti
objektum 2-es módja) — ehhez egy mélyebb kör kell.~~

> ⚠️ **HELYESBÍTÉS (2026-08-16): a `FUN_00a42c20` NEM elmosómag.** Az RTTI
> szerint ez a **`ytResampler::vftable` 9. bejegyzése**, vagyis egy
> **átméretező** (resampler) virtuális metódusa — a binárisban **17**
> egymástól független helyről hívják (indexkép, export, nyomtatás,
> szerkesztő). Az `unsharp` elmosása tehát az **átméretezőn** keresztül
> készül, nem a Picasa IIR-elmosóján. Részletek: „Az `unsharp` elmosása
> az ÁTMÉRETEZŐBŐL jön" alább.

### `blur` — a csúszka a KÜSZÖB, nem a sugár (helyesbítve: #1142)

```c
FUN_0090cf60(dst, src, /*kuszob*/ *(p + 0x28), /*skala*/ 1.0f);
```

A munkafüggvény `(h+1)·(w+1)` darab **16 bites** akkumulátort foglal — ez
összegzőtábla/dobozszűrő-jellegű megvalósításra utal, nem Gauss-konvolúcióra.

> ⚠️ **HELYESBÍTÉS (#1142): a harmadik argumentum NEM sugár.** A szakasz
> korábbi címe („a csúszka a sugár") megdőlt. A `filterdesc.xml` a `blur`
> egyetlen csúszkáját `Threshold`-nak nevezi (`[-0,5; 0,5]`, alapérték
> `0,1`), a [`picasa-native-filter-workers.md`](picasa-native-filter-workers.md)
> 4.2.3 dekompilátuma pedig élmegőrző, HÁROM LÉPTÉKŰ simítást ír le, ahol a
> paraméter az él-küszöb (`ΔR² + ΔG² + ΔB² > küszöb / n²` → „fal").

**Mérés (`PicasaPy merokit-2`, 2026-08-15-i eredeti export, 960×640-es
tesztábra; a JPEG-újratömörítés zajszintje ebben a szettben 0,240):**

| lánc | eltérés a forrástól | legjobb illesztés |
|---|---|---|
| `blur=1;` (alapérték, 0,1) | 0,240 | tétlen |
| `blur=1,0.500000;` (a csúszka teteje) | 0,562 | tétlen (σ ≤ 0,3) |
| `blur=1,2.000000;` (tartományon KÍVÜL) | 17,317 | **σ = 4,00 Gauss**, 0,552 maradék |

A σ optimuma éles (3,90 → 0,650; 4,10 → 0,692), és minden más próbált mag
rosszabb: a Picasa saját IIR-elmosója (`iir_blur`, a legjobb sugarán) 3,49;
a háromléptékű `[1,2,1]` dilatált lánc (n = 1, 2, 4) 2,03; a legjobb
háromdobozos lánc 0,72. A sugár tehát **nem függ a paramétertől** — ami
összefér a dekompilátummal: a küszöb azt dönti el, HOL simíthat, nem azt,
mekkora sugárral.

*Bizonyítottsági fok: a két véglet MEGERŐSÍTETT (eredeti export, képenként).
Ami NYITVA marad: a küszöb → falképzés leképezése a 0,5 és a 2,0 közötti
sávban — erre nincs mérési pontunk. A PicasaPy modellje
(`src/picasapy/render/blur.py`) a váltást a csúszka tetejére teszi, mert az
a legnagyobb mérten tétlen érték; a sáv kimérése önálló kutatói kör.*

### `grain` / `grain2` — MSVC `rand()`, majd vízszintes simítás

A callback konstans `0.5f`-fel hív (`FUN_0090a2e0(dst, 0.5f)`), amiből
`keveres = round(256 − 0,5·256) = 128`. A zajmező az **MSVC szabványos
`rand()`-jából** jön (LCG: `seed = seed*0x343fd + 0x269ec3`, kimenet
`(seed >> 16) & 0x7fff`), **három bemelegítő hívás** után. A nyers zajra
ezután egy 1:3 súlyú, soronként balról jobbra futó simítás megy:

```c
uj = (3 * kovetkezo + jelenlegi) >> 2;     // csatornankent
```

Ez adja a szemcse „csomós" jellegét — fehér zajból nem jönne ki.
*Bizonyítottsági fok: erős* (a `rand()` azonosítása megerősített; a simítás
iránya és a 128-as keverés a dekompilátumból olvasva).

#### A mag kérdése LEZÁRVA: a szemcse képenként MÁS (2026-08-15)

**Ez volt a szakasz nyitott pontja, és eldőlt — méréssel és kódból is.**

**A mérés a döntő.** Az öt `grain2=1;` golden-pár (`golden-kit/05-tone` →
`golden-kit-result/export/05-tone`) különbségmezőit összevetve:

| összevetés | korreláció |
|---|---:|
| `photo01` vs `photo04` (**mindkettő 1920×1080**) | **−0,0012** |
| `chart_color` vs `chart_ramp` (**mindkettő 1600×1200**) | **+0,0019** |
| a többi hét páros | −0,017 … +0,002 |

**Az azonos méretű párok a döntők:** ott a zajmező elhelyezése is azonos
lenne, tehát rögzített mag mellett a két különbségmezőnek **egyeznie kellene**.
A korreláció nulla.

Hogy ez nem mérési zaj, azt a kontroll adja: a `00-base` mappa
**effekt nélküli** exportjain a puszta JPEG-újratömörítés szórása
**0,27–1,35** szint, a `grain2`-párokén **4,0–5,4** — a szemcse tehát
bőven kiemelkedik a zajból, mégsem korrelál.

**A kód ugyanezt mondja.** Az MSVC `rand()` (`0x00c08221`) a magot a
**szálankénti** CRT-blokkból veszi (`[ptd + 0x14]`, LCG:
`mag = mag·0x343fd + 0x269ec3`, kimenet `(mag >> 16) & 0x7fff`). Az `srand`
(`0x00c08214`: `_getptd(); ptd[0x14] = arg`) az egész binárisban **10 helyről**
hívódik, és **egyik sem a szemcse-munkafüggvény** (`0x0090a2e0`) — az csak
`_rand`-ot hív. A generátor tehát **nem áll vissza képenként**: a folyam megy
tovább, és minden kép a sorozat más szakaszát kapja.

*Bizonyítottsági fok: megerősített* (a mérés önmagában eldönti) · a pontos ok
(folytatódó folyam vs. máshol beültetett mag) **erős**, de nem elkülönített.

> ⚠️ **Következmény a tesztelésre: a `grain`/`grain2` kimenete elvileg sem
> reprodukálható bájtra.** Golden-összevetésben ezeket **statisztikailag** kell
> mérni (szórás, sávonkénti erősség), nem képpontonként. Aki képpont-egyezést
> vár tőlük, olyan tesztet ír, ami sosem lesz zöld.

#### A szemcse JELLEGE — amit utánozni kell (mérve, 5 golden-páron)

| tulajdonság | mért érték |
|---|---|
| **monokróm** | ugyanaz az érték mindhárom csatornán: `σ(R,G,B)` = 4,81/5,00/4,77 (`chart_color`), a csatornák közti korreláció **0,75–1,00** |
| **erősség** | teljes szórás **4,0–5,4** szint |
| **világosságfüggés** | a középtónusban a legerősebb (σ ≈ 5–6,4), a két végén visszaesik (σ ≈ 3–3,8) |
| **szomszéd-korreláció** | vízszintes **+0,23…+0,31**, függőleges **+0,24…+0,32** |

⚠️ **Az utolsó sor ellentmond a dekompilátumból olvasott, csak vízszintes
1:3 simításnak.** Egy soronként balról jobbra futó szűrőnek a vízszintes
korrelációt érdemben a függőleges FÖLÉ kellene emelnie; a mérés szerint a
kettő egyenlő (0,01-en belül). Lehetséges magyarázatok: a szemcse nem teljes
felbontáson készül és skálázódik, vagy az export JPEG-je mossa el a
különbséget. *Bizonyítottsági fok: feltételes* — ez a szakasz új nyitott
pontja.

Egy kilógó minta: a `chart_detail` szórása mindössze **1,31** (a többi 4–5),
és nála a függőleges korreláció a nagyobb (0,46 vs 0,36). Nem magyarázott.

### Amit ez a négy jelent a #317-re

A `warm` **lezárult, pixelpontosan**, kalibráció nélkül. Az `unsharp` legfőbb
ismeretlene (a sugár) eldőlt. A `blur` és a `grain` modellje a helyére került,
mindkettőnél egyetlen, jól körülírt részlet maradt — és egyik sem igényel
windowsos exportot a **megfejtéshez**, csak a validáláshoz (#684).

### `sat` pozitív ág — a natív mag teljesen visszafejtve (2026-08-15, #693)

**Nem kellett új Ghidra-kör**: mindkét cím megvolt a korábbi naplókban
(`referencia/dekompilalt-pakolo/script-Decompile317.log`).

**Elsőként egy ágtévesztés javítása.** A callback (`0x008f8ff0`) így ágazik:

```c
if (*(float *)(param_1 + 0x28) < 0.0)
    FUN_0090e200(dst, amount + 1.0f);   // NEGATÍV ág (telítetlenítés)
else
    FUN_0090b930(dst, src, amount);     // POZITÍV ág
```

Tehát a pozitív ág magja a **`0x0090b930`**; a `0x0090e200` a negatívé.

#### A teljes algoritmus

```c
s = amount * 3.0f;

// harom KULON, 2048 elemu tabla — csatornankent MAS kitevovel
for (i = 0; i < 2048; i++) {
    x = i * 8.0f / 2048.0f;                      // 0 .. 8
    LUT_R[i] = lround(powf(x, 1.0f + 0.3f*s) * 256);
    LUT_G[i] = lround(powf(x, 1.0f + 0.7f*s) * 256);
    LUT_B[i] = lround(powf(x, 1.0f + 0.9f*s) * 256);
}

// pixelenkent
Y = (5*G + 1*B + 2*R) >> 3;                      // NEM a szokasos suly
if (Y != 0) {
    k = (256*256 - 1) / Y;                       // DAT_00d3a148 = 256 → 65535/Y
    R' = (LUT_R[min((k*R) >> 8, 2047)] * Y) >> 8;
    G' = (LUT_G[min((k*G) >> 8, 2047)] * Y) >> 8;
    B' = (LUT_B[min((k*B) >> 8, 2047)] * Y) >> 8;
}
m = max(R', G', B');
if (m > 255) { f = 65280 / m; R'|=..., mindharom: C'' = (f * C') >> 8; }
```

A `DAT_00d3a148 = 256` a binárisból kiolvasva (fájloffszet `0x93a148`), és a
`.text`-ben **egyetlen** hivatkozás mutat rá (`0x0090bb1a`) — a fenti sor.

#### Miért telítődik a mért erősítés — a #693 kulcskérdése

A művelet **nem erősítés**, hanem a `csatorna / luma` aránynak adott
**csatornánkénti gamma**:

```
C' ≈ Y · pow( C/Y , 1 + e·s )        e ∈ {0,3 · 0,7 · 0,9}
```

Ez **önmagában korlátozó**: ahol a csatorna a lumához közeli (`C/Y ≈ 1`), ott
`pow(1, bármi) = 1`, tehát a csúszka **akármekkora is, nem mozdít**. Csak a
lumától távoli csatornák mozdulnak, és azok is egyre kisebb hozadékkal. Ezért
fut a mért erősítés 1,15 → 1,95 helyett a lineáris modell 3,6-jáig.

**Ablációval ellenőrizve** (szintetikus színfoltokon, a fenti algoritmus
Python-mása): a telítődést **sem** a `2047`-es indexvágás, **sem** a záró
`65280/m` maxnormálás okozza — mindkettőt kikapcsolva a görbe alakja
gyakorlatilag változatlan. A telítődés a hatványgörbe sajátja.

| csúszka | teljes | maxnorm nélkül | indexvágás nélkül |
|---|---|---|---|
| 0,100 | 1,071 | 1,070 | 1,071 |
| 0,375 | 1,194 | 1,172 | 1,194 |
| 0,625 | 1,254 | 1,225 | 1,254 |
| 0,875 | 1,288 | 1,259 | 1,288 |

*(A saját telítettség-metrikám és a #693 mért „erősítése" nem ugyanaz a szám,
ezért az abszolút értékek nem vethetők össze — a **görbe alakja** igen.)*

#### Amit ez a modellezésről kimond

- **Egyetlen skalár erősítés semmilyen luma-súllyal nem illeszthető rá** —
  összhangban azzal, amit a #693 mérése már kizárt.
- A három kitevő **különbözik**, tehát a hatás **színárnyalat-függő**: a piros
  felé eső csatorna a leggyengébben (0,3), a kék a legerősebben (0,9) mozdul.
  Egy csatornafüggetlen modell ezt sem tudja visszaadni.
- A luma súlyai itt **`(2·R + 5·G + 1·B)/8`**, ami eltér a `sepia`/`radsat`/
  `tint` `(77·R + 151·G + 28·B) >> 8` képletétől — **közös segédfüggvényt
  kivonni tilos**.

*Bizonyítottsági fok: megerősített* (a teljes ciklus és a konstans is
visszakeresve). A golden-kit3 `12-sat-sweep` kilenc csúszkaállása innentől
**validáció**: a fenti algoritmus közvetlenül visszamérhető rá.

## `enhance` — a LEGGYAKRABBAN használt szűrő, és eltér (mérve, 2026-08-15)

A valódi ini-korpusz szerint az `enhance` a **leggyakoribb** szerkesztés:
**3 045 lánc** az 5 658-ból tartalmazza
([`picasa-ini-format.md`](picasa-ini-format.md), korpusz-szakasz). Ezért
minden más effektnél többet számít a pontossága.

### A mérés

A #685 mérőszettjének szürke rámpáján (0…255, teljes tartomány) az
eredeti Picasa-export és a mi renderünk átviteli görbéje illesztve:

| szűrő | forrás | átvitel | fekete-vágás | fehér-vágás | illesztés szórása |
|---|---|---|---:|---:|---:|
| `autolight` | Picasa | `1,0325·be − 4,64` | **4,5** | **251,5** | 0,11 |
| `autolight` | mi | `1,0321·be − 4,59` | **4,4** | **251,5** | 0,28 |
| `autocolor` | Picasa | `1,0000·be + 0,00` | — | — | 0,00 |
| `autocolor` | mi | `0,9997·be + 0,00` | — | — | 0,11 |
| **`enhance`** | **Picasa** | **`1,1136·be − 7,19`** | **6,5** | **235,4** | 0,29 |
| **`enhance`** | **mi** | **`1,1487·be − 21,19`** | **18,4** | **240,4** | 0,29 |

### Amit ez kimond

1. **Mindkét oldal tiszta lineáris szinthúzást végez.** A Picasa görbéje
   gyakorlatilag hibátlan egyenes (illesztési szórás 0,29 a 0–255
   tartományon) — nincs benne gamma, nincs S-görbe.
2. **Az `autolight` és az `autocolor` nálunk PONTOS.** A vágási pontok
   tizedre egyeznek. Ezeken nincs mit javítani.
3. **Az `enhance` viszont eltér, és a hiba az ÁRNYÉKOKBAN a legnagyobb:**
   a fekete-vágásunk **18,4**, a Picasáé **6,5** — közel **12 szint**
   árnyékrészletet vágunk le fölöslegesen. A fehér végén 240,4 vs 235,4,
   itt mi vagyunk a kevésbé agresszívak.
4. **Az `enhance` NEM az `autolight` és az `autocolor` egyszerű
   összefűzése.** A Picasa `enhance`-e ugyanazon a képen jóval erősebben húz
   (6,5…235,4), mint az `autolight` (4,5…251,5) — más küszöbbel dolgozik.

*Bizonyítottsági fok: megerősített* az eltérés ténye és iránya (azonos
bemenet, valódi Picasa-export, két független illesztés 0,3 alatti
szórással). **Feltételes** a konkrét számok általánosíthatósága: a vágási
pontok hisztogram-függők, tehát képenként mások — a mérés azt bizonyítja,
hogy **azonos bemeneten eltérünk**, nem azt, hogy a vágás mindig 6,5.

### MEGOLDVA: nem a küszöb más, hanem az elemzőABLAK helye (#721)

Az eredeti gyanú — hogy nagyobb százalékot vágunk a sötét oldalon —
**téves volt**: a küszöb (`(W·H)/200`) jó. Ami eltért: **hol van a
hisztogram-elemzés ablaka.**

**1. Amit maga a rámpa-mérés kimond.** Az `autolight` ugyanezen a képen
4,5-től 251,5-ig lát — ez a rámpa két vége, mert az `autolight` a TELJES
képet elemzi. A Picasa `enhance`-e viszont 6,5-nél vág feketét: a rámpa
hosszának **~1 %-ánál**. Egy vízszintesen KÖZÉPRE igazított, 90 %-os ablak
a rámpa 5 %-ánál kezdődik, tehát a fekete-vágása geometriailag nem lehet
12,75 alatt — a miénk pontosan ott, **18,4**-nél volt. **Az ablak
vízszintesen tehát nem középre igazított.** A fehér végén ugyanez fordítva
látszik: a Picasa 235,4-nél vág, mi 240,4-nél — a Picasa ablaka a világos
oldalon rövidebb.

**2. Amit a dekompilátum mond.** A `0x009db610` hisztogram-ciklusa
függőlegesen tényleg beljebb kezd, a VÍZSZINTES eltolás viszont hiányzik
belőle — a vízszintes peremet csak a képpontok DARABSZÁMÁHOZ használja:

```c
uVar12 = (W * 5) / 100;   uVar10 = (W * 95) / 100;   // csak a DARABHOZ
pbVar11 = base + stride * ((H * 5) / 100) * 4;       // sor-eltolás: megvan
do {
  iVar8  = uVar10 - uVar12;   // 0,9·W képpont…
  pbVar2 = pbVar11;           // …de a sor ELEJÉRŐL, nem a peremtől
```

Az ablak tehát `[0 .. 0,9·W)` × `[0,05·H .. 0,95·H)`: a bal perem **benne
van**, a jobb 10 % marad ki. Ez a Picasa saját, elejtett eltolása.

**3. Amit a 12 valódi képpár mond.** A `referencia/imfeellucky/` készleten
négy ablak-változatot végigmérve, átlagos abszolút csatorna-eltérés a
valódi Picasa-kimenettől:

| elemzőablak | átlagos eltérés | legrosszabb kép |
|---|---:|---:|
| **balra igazított 90 % × 90 %** (ez lett a megvalósítás) | **2,48** | 13,03 |
| középre igazított 90 % × 90 % (a korábbi) | 2,61 | 13,34 |
| teljes kép | 2,68 | 12,53 |
| bal felső 90 % × 90 % | 2,74 | 13,35 |
| *az érintetlen kép* | *10,35* | *38,10* |

*(Ez a táblázat a vágópont-KEVERÉS bevezetése előtti modellel készült.
A kevert (mai) modellel újramérve a döntés nemhogy áll, hanem sokkal
élesebb: balra igazított **0,572**, bal felső 0,782, középre igazított
0,964, teljes kép 1,730.)*

A három bizonyíték **egy irányba mutat**, és egyik sem illesztés: a
dekompilátum betű szerinti olvasata egyben a mérésen is a legjobb.

*Bizonyítottsági fok: megerősített* az ablak vízszintes horgonya (a
rámpa-mérés geometriai érve + a 12 képpár + a dekompilált
mutató-aritmetika). ~~**Nyitva marad** az ablak pontos SZÉLESSÉGE~~ —
**LEZÁRVA (2026-08-16)**, utasításszinten: lásd „Az elemzőablak szélessége
utasításszinten" alább. Az eredeti jegyzet: a `0,9·W` a dekompilátumból
jön, a rámpa fehér vége (235,4) viszont egy hajszálnyival szélesebb
ablakhoz (~0,94·W) illene jobban.

Megvalósítás: `picasapy.render.ops._analysis_region`; regressziós őr:
`tests/render/test_ops.py::TestEnhanceVagasiPontok721`. Ugyanez hat az
`autocontrast`-ra és a Glimmer-effektek belső `AutoFix` lépésére is (közös
mag: `apply_channel_levels_stretch`).

## Az `autocolor` becslője VISSZAFEJTVE (`0x0090f8f0`, 2026-08-16)

Eddig az `autocolor` „szürkevilág-becslés a semleges képpontokra" modellel
futott (#541), 2,35-ös mért eltéréssel a 12 páron, és a `render/ops.py`
docstringje kimondta: *„a pontos becslő-képlet továbbra is nyitott"*.
**Most megvan, utasításszinten.**

### A hívási lánc

```
autocolor callback   0x008f82a0        (a natív regiszterből)
   → 0x0090f8f0      a BECSLŐ  (965 b)   — visszaad három bájtnyi erősítést
   → 0x0090eda0      az ALKALMAZÓ (1731 b)
```

Az `autocolor` tehát **nem** a szinthúzó elemzőt (`0x009db610`) használja —
teljesen külön út, ezért ad a szürke rámpán azonosságot (nincs színöntet).

### 1. Melyik képpont számít „semlegesnek"

```c
G = px.g;  R = px.r;  B = px.b;
if (G < 32 || G > 224) skip;          // (G-32) unsigned > 192  → 0x0090f9b6
if (2*R <= G) skip;                   // 0x0090f9c7
if (2*G <= R) skip;                   // 0x0090f9d2
if (2*B <= G) skip;                   // 0x0090f9de
if (2*G <= B) skip;                   // 0x0090f9e6
```

Vagyis: **a zöld 32 és 224 közt van**, és **egyik csatorna sem több a másik
kétszeresénél** (a zöldhöz viszonyítva). Nincs benne se telítettség-, se
világosság-számítás — öt egész összehasonlítás.

### 2. Egy 64 × 64-es KÉTDIMENZIÓS hisztogram

```c
rg = clamp(32*(R-G) / min(R,G) + 32, 0, 63);     // 0x0090f9ee-0x0090fa2c
bg = clamp(32*(B-G) / min(B,G) + 32, 0, 63);
H[bg][rg] += 1;                                   // 0x0090fa6b
```

A tengelyek a **vörös/zöld** és a **kék/zöld** kiegyensúlyozatlanság, 32-es
fixponton, a semleges pont a `(32, 32)`.

### 3. Köbös súlyozás a semleges pont köré

```c
tav = max(|x-32|, |y-32|);            // Csebisev-távolság
w   = ((32 - tav)^3) >> 5;            // 0x0090fab5-0x0090faca
H[y][x] = (w > 0) ? (H[y][x]*w) >> 8 : 0;
```

A **köbös** esés miatt a valóban semleges képpontok sokszorosan nyomnak
többet; a 31-es távolságnál a vödör nullázódik.

### 4. Súlypont → két erősítés

```c
dx = clamp(sum((x-32)*H) / sum(H), -32, 32);      // 0x0090fb08-0x0090fbf9
dy = clamp(sum((y-32)*H) / sum(H), -32, 32);

k(d) = (d >= 0) ? (32+d)*4 : 16384 / ((32-d)*4);  // k(0) = 128 = EGYSÉG
csomag = (k(dx) << 16) | 0x8000 | k(dy);          // 0x0090fc8a-0x0090fc99
```

A csomagolt visszatérési érték **három bájt**: `kR`, **128** (a zöld fixen
egység), `kB`. Az egység tehát **128**, a tartomány `[0 … 255]`, azaz
kb. `0…2,0×`.

### 5. Az irány: OSZTÁS — méréssel eldöntve

A kódból nem dőlt el, hogy az alkalmazó szoroz vagy oszt (a `k` a **mért
színöntettel nő**). A 12 golden-páron (`referencia/autocolor/AutoColor`)
mindkét irányt kimérve:

| | átlagos eltérés |
|---|---:|
| `ki = be · k/128` (szorzás) | **10,126** |
| **`ki = be · 128/k` (osztás)** | **2,364** |
| érintetlen kép | 5,287 |

A szorzás **rosszabb az érintetlennél** — az osztás a helyes irány.
*Bizonyítottsági fok: megerősített (mérés).*

### 6. ⚠️ A becslő NEM a szűk keresztmetszet — negatív eredmény

| modell | eltérés |
|---|---:|
| a mai kódunk (szürkevilág-becslés, #541) | 2,35 |
| **a visszafejtett becslő** | **2,364** |
| orákulum (a MÉRT erősítésekkel) | 1,08 |

A kettő **gyakorlatilag azonos**, és ugyanazon a három képen tér el
(Night Seascape, Sunny Autumn, Golden leaves). **A maradék hiba tehát nem a
becslőben van** — a becslő cseréje önmagában semmit nem javítana.

> ⚠️ **Helyesbítés (2026-08-18): ez csak a csatornánkénti alkalmazóval igaz.**
> A mátrix-alkalmazóval a becslő pontossága nagyon is számít: a fenti
> pszeudokód `/` jelei **C-osztások**, tehát nulla felé csonkolnak — Pythonban
> `//`-val átírva (padló) 1,370 az eltérés, csonkolással **0,614**. Ld. „Az
> `autocolor` TELJESEN LEZÁRVA (2026-08-18)".

### 7. Ahol a maradék van: az alkalmazó egy 3 × 3-as SZÍNMÁTRIX

A `0x0090eda0` a legelső dolgaként **kilenc float konstanst** másol egy
kilenc elemű tömbbe (`rep movsd`, `ecx = 9`), majd meghívja a `0xa4a140`-et:

|  |  |  |
|---:|---:|---:|
| **1,9044** | 0,4508 | −0,3826 |
| −0,0532 | **1,8018** | 0,1995 |
| 0,0491 | −0,3057 | **1,8576** |

*(`0x00cf47d0` … `0x00cf47b0`, betöltési sorrendben)*

Vagyis az `autocolor` **nem három független csatorna-erősítés**, hanem egy
**3 × 3-as színmátrix**, amibe a becsült erősítések beépülnek. Ez magyarázza,
miért nem megy 2,35 alá semmilyen csatornánkénti modell — a kereszt-tagok
hiányoznak belőle.

*Bizonyítottsági fok:* **megerősített** az 1–5. pontra (utasításszinten
visszakövetve, a mérés az irányt eldönti) · **erős** a 7. pontra (a kilenc
konstans és a `rep movsd ecx=9` egyértelmű, de a mátrix sorrendje és a
becsült erősítések beépülésének módja a `0x0090eda0` alkalmazó ciklusából és
a `0xa4a140`-ből derül ki — **ez a következő kör**).

Mérőszkript: `referencia/eszkozok/721-enhance/autocolor_model.py` (privát repó).

### Az `autocolor` ALKALMAZÓJA — mérve, és két hipotézis megdőlt (#759, 2026-08-16)

#### Amit az utasítások mondanak

A `0x0090eda0` képpont-ciklusa (`0x0090f360`–`0x0090f3bd`) **16.16 fixpontos
3 × 3 mátrixszorzás**:

```asm
ebx = px[0] (B) ; esi = px[1] (G) ; edi = px[2] (R)
eax = m[0x30]*R + m[0x34]*G + m[0x38]*B ; sar eax,16
edx = m[0x3c]*R + m[0x40]*G + m[0x44]*B ; sar edx,16
ecx = m[0x48]*R + m[0x4c]*G + m[0x50]*B ; sar ecx,16
```

*Bizonyítottsági fok: megerősített.*

#### ⚠️ Önkorrekció a PR #758-hoz

A #758 azt írta, hogy „az alkalmazó a kilenc float konstansból 3 × 3-as
mátrixot épít". **Ez túlzás volt.** A kilenc konstans a `rep movsd`-vel a
`[esp+0xcc]` pufferbe megy (és onnan a `0xa4a140` használja), a képpont-mátrix
viszont a `[esp+0x30 … 0x50]` rekeszekben áll. **A kettő nem ugyanaz a puffer**,
és a köztük lévő kapcsolat nincs igazolva.

#### A mátrix-modell HELYES — orákulum-illesztéssel

A 12 golden-páron csatornánként legkisebb négyzetes 3 × 3-at illesztve
(20 000 mintapont/kép):

| | átlagos eltérés |
|---|---:|
| **a legjobb 3 × 3 mátrix (orákulum)** | **0,97** |
| a mai csatornánkénti modellünk | 2,35 |
| érintetlen kép | 5,29 |

**0,97 = a JPEG-újratömörítés zaja** — vagyis egy 3 × 3 mátrix a Picasa
kimenetét gyakorlatilag hibátlanul megmagyarázza. A modell alakja tehát
bizonyítottan mátrix, nem három független csatorna-erősítés.

Az illesztett mátrixok **közel átlósak**, a keresztágakkal ±0,05 körül —
egyetlen kivétellel: a „Night Seascape" (erős kék öntet) mátrixa
`−0,508` és `+0,528` keresztágakat tartalmaz. Ez az a kép, amit a
csatornánkénti modell **elvileg** sem tud lekövetni.

#### ❌ MEGDŐLT: a kilenc konstans NEM adaptációs tér

Kézenfekvő hipotézis volt, hogy a kilenc konstans (`C`) egy „élesített"
színteret ad, és a becsült erősítések ott hatnak — a klasszikus von Kries-alak.
Mindkét sorrendet kimérve a 9 nem-triviális páron:

| modell | átlagos eltérés |
|---|---:|
| `diag(128/kR, 1, 128/kB)` (puszta átlós) | **3,10** |
| `C⁻¹ · D · C` | 3,51 |
| `C · D · C⁻¹` | 3,60 |
| orákulum | 0,97 |

**Mindkét adaptációs alak ROSSZABB a puszta átlósnál.** A kilenc konstans
tehát nem így épül be. *Bizonyítottsági fok: megerősített (cáfolat).*

#### Ami ebből következik a megvalósításra

1. A `128/k` **túl erős**: a puszta átlós modell 3,10-et ad, a mai,
   csillapított becslőnk 2,35-öt. A tényleges átló a `128/k` és az 1,0
   **között** van.
2. A cél a **0,97** — és ehhez **keresztágak kellenek**. Csatornánkénti
   modellel a „Night Seascape" típusú képek nem javíthatók.
3. ~~A következő lépés a `0x0090eda0` **mátrix-építő** szakasza
   (`0x0090ee28`–`0x0090f31c`) és a `0xa4a140`~~ — **MEGVAN**, ld. a
   következő szakaszt.

Mérőszkript: `referencia/eszkozok/721-enhance/autocolor_model.py`.

## Az `autocolor` MÁTRIX-ÉPÍTŐJE VISSZAFEJTVE (`0x0090ee28`–`0x0090f31c`)

**Ez zárja le a „Nyitva 1"-et: az `autocolor` teljes képlete megvan.** A
modell a 12 golden-páron **1,370** átlagos eltérést ad a mai 2,35 helyett, és
**három képen bitre azonos** a Picasa kimenetével.

> ⏭️ **A maradék 1,370-et azóta lecsökkentettük 0,614-re** — ld. „Az
> `autocolor` TELJESEN LEZÁRVA (2026-08-18)" szakaszt: a becslő
> egész-osztásai nulla felé csonkolnak, nem a padló felé.

### A kilenc konstans EGY mátrix, és a helyben INVERTÁLÓDIK

A `0x00cf47b0 … 0x00cf47d0` kilenc `float`-ja sor-folytonosan:

|  |  |  |
|---:|---:|---:|
| **1,9044** | 0,4508 | −0,3826 |
| −0,0532 | **1,8018** | 0,1995 |
| 0,0491 | −0,3057 | **1,8576** |

A betöltés **csökkenő címsorrendben** történik (`0xcf47d0` → 0. rekesz …
`0xcf47b0` → 8. rekesz), ezért a fenti a helyes, sor-folytonos alak. Nevezzük
`M`-nek.

```asm
0x0090edda  lea      esi, [esp + 0x30]     ; forrás: a kilenc konstans
0x0090ede2  lea      edi, [esp + 0xcc]     ; cél: másolat
0x0090edef  lea      edx, [esp + 0x30]     ; ← a 0xa4a140 KIMENETE
0x0090ee1f  rep movsd                       ; M  →  [esp+0xcc]
0x0090ee21  lea      ecx, [esp + 0xcc]
0x0090ee28  call     0xa4a140               ; edx = inverz(ecx)
```

**A `0xa4a140` egy 3 × 3-as mátrixinvertáló** (`ecx` = forrás, `edx` = cél):
a `0x00a4a143`–`0x00a4a181` a Sarrus-szabállyal determinánst számol, és ha az
**pontosan nulla**, egységmátrixot ír vissza (`0x00a4a190`–`0x00a4a1ab`);
egyébként `0xa4a0a0`-val az adjungáltat osztja a determinánssal.

Vagyis a hívás után **`[esp+0x30 … 0x50]` = `M⁻¹`**, a `[esp+0xcc]`-beli
másolat pedig már halott — a fordító a rekeszeit később skalároknak
használja újra.

> ⚠️ **Helyesbítés a PR #759-hez.** Az előző kör azt írta: *„a kilenc konstans
> a `[esp+0xcc]` pufferbe megy, a képpont-mátrix viszont a `[esp+0x30 … 0x50]`
> rekeszekben áll — **a kettő nem ugyanaz a puffer**, és a köztük lévő
> kapcsolat nincs igazolva."* **A kapcsolat megvan:** a `rep movsd` forrása
> maga a `[esp+0x30]`, a `0xa4a140` célja pedig szintén az — ugyanaz a puffer,
> előbb `M`, utána `M⁻¹`.

### A becsült erősítésekből átlós mátrix — LUMINANCIA-MEGŐRZÉSSEL

```asm
0x0090ee6b  movzx    ecx, byte ptr [esp+0xfe]   ; kR  (a csomag 2. bájtja)
0x0090ee75  movzx    eax, bh                     ; kG  (fixen 0x80 = 128)
0x0090ee78  movzx    edx, bl                     ; kB
   mindhárom:  ha 0, akkor 1                     ; 0x0090ee7d/ee86/ee8f
0x0090ee94  imul     ecx, ecx, 0x4d              ; kR · 77
0x0090ee97  imul     eax, eax, 0x97              ; kG · 151
0x0090ee9f  lea      ecx, [edx*8] ; sub ecx,edx ; lea eax,[eax+ecx*4]
                                                 ; + kB · 28
0x0090eeab  shr      eax, 8                      ; L
0x0090eeae  imul     eax, eax, 0x10101           ; (L,L,L) egy dwordben
```

**`L = (77·kR + 151·kG + 28·kB) >> 8`** — a súlyok összege pontosan 256, és a
`77/151/28` a **Rec. 601 luma** egész közelítése (0,3008 / 0,5898 / 0,1094).

Ezután **két mátrix-vektor szorzás** ugyanazzal az `M⁻¹`-gyel:

```
P = M⁻¹ · (L, L, L)ᵀ        → [esp+0x78 … 0x80]   (0x0090eefa–0x0090ef73)
Q = M⁻¹ · (kR, kG, kB)ᵀ     → [esp+0x60 … 0x68]   (0x0090ef9a–0x0090effe)
g = P ⊘ Q   (elemenként)     → [esp+0xcc], [esp+0xdc], [esp+0xec]
                                                   (0x0090f002–0x0090f02b)
```

### A végleges mátrix: `A = M · diag(g) · M⁻¹`

A `0x0090f032`–`0x0090f159` a `diag(g) · M⁻¹` szorzatot építi, a
`0x0090f160`–`0x0090f2ac` pedig balról **`M`-mel** szoroz. Itt `M` kilenc
eleme **`double` konstansként, előjel nélkül** áll a `0x00cf4768 …
0x00cf47a8` címeken — az előjelek magukba az `fadd`/`fsub` utasításokba
égtek:

| cím | érték | ez `M` melyik eleme |
|---|---:|---|
| `0x00cf4778` | 1,9044 | (0,0) |
| `0x00cf4770` | 0,4508 | (0,1) |
| `0x00cf4768` | 0,3826 | (0,2), **negatívan** (`fsubrp`) |
| `0x00cf47a0` | 0,0532 | (1,0), **negatívan** |
| `0x00cf47a8` | 1,8018 | (1,1) |
| `0x00cf4798` | 0,1995 | (1,2) |
| `0x00cf4790` | 0,0491 | (2,0) |
| `0x00cf4788` | 0,3057 | (2,1), **negatívan** |
| `0x00cf4780` | 1,8576 | (2,2) |

Végül 16.16 fixpontra:

```asm
0x0090f2f8  fld   qword ptr [0xcf3cb0]          ; 65536.0
0x0090f2fe  fld   dword ptr [esp + esi + 0x8c]  ; A elemei (float)
0x0090f305  fmul  st(1)
0x0090f307  call  0xc29990                       ; ftol — CSONKÍT nulla felé
0x0090f30c  mov   dword ptr [esp + esi + 0x30], eax
0x0090f313  cmp   esi, 0x24                      ; 9 elem
```

### Miért pont ez a képlet — önellenőrzés

A szerkezetből **egy sorban** következik, mi az `autocolor` szándéka:

```
A · k = M · diag(g) · M⁻¹ · k = M · diag(P/Q) · Q = M · P = (L, L, L)
```

Vagyis a mátrix a **becsült megvilágítás színét (`k`) pontosan a vele azonos
világosságú semleges szürkére (`L, L, L`) képezi le**. Ez a fehéregyensúly
tankönyvi definíciója, és megmagyarázza a luma-súlyokat is: a korrekció
**nem világosít és nem sötétít**, csak a színöntetet veszi ki.

### A mérés

12 golden-pár (`referencia/imfeellucky/ImFeelLucky-noeffect` →
`referencia/autocolor/AutoColor`), átlagos abszolút csatornaeltérés:

| modell | átlag | nem-triviális 9 |
|---|---:|---:|
| érintetlen kép | 5,287 | 6,971 |
| a mai kódunk (csatornánkénti, #541) | 2,35 | — |
| `M⁻¹ · diag(g) · M` (fordított sorrend) | 2,650 | 3,454 |
| **`M · diag(g) · M⁻¹`** | **1,370** | **1,748** |
| orákulum (a legjobb illesztett 3 × 3) | 0,97 | — |

A három semleges becslésű képből (`kR = kB = 128`) **kettő bitre azonos**
(`0,000`) — a harmadik (`Utopic Unicorn`, 0,709) az érintetlen képen is
0,709-et ad, tehát ott a Picasa mást is csinált. A bitazonosság a
**csonkítást és a fixpontos kerekítést is igazolja**.

> ⚠️ **Float32-ben kell számolni.** A bináris minden köztes eredményt
> `fstp dword ptr`-rel, tehát **`float`-ként** tárol. `double`-ben az
> egységmátrix `0,99999999`-re jön ki, a csonkítás `65535`-öt ad `65536`
> helyett, és minden képpont eggyel sötétebb lesz (0,67 átlagos hiba a
> semmiből).

*Bizonyítottsági fok: **megerősített*** — az utasításszintű visszakövetés, az
algebrai önellenőrzés (`A·k = (L,L,L)`) és a három bitazonos golden-pár
egymástól függetlenül ugyanazt adja.

Mérőszkript: `referencia/eszkozok/721-enhance/autocolor_matrix.py`.

## Az `autocolor` TELJESEN LEZÁRVA (2026-08-18) — a maradék hiba egyetlen egész-osztás volt

Két dolgot zár le ez a kör: az utolsó nyitott becslő-kérdést (`Empty Space`)
és azt, hogy az alkalmazó alakja **referenciakép nélkül, pusztán a kódból**
is eldönthető.

### 1. A becslő egész-osztásai NULLA FELÉ csonkolnak (C-szemantika)

A `0x0090f8f0` két helyen oszt előjelesen, **futásidőben változó osztóval**
(tehát a fordító nem tudja eltolássá alakítani — valódi `idiv`):

| hol | kifejezés | cím |
|---|---|---|
| a hisztogram tengelyei | `32*(R−G) / min(R,G)` és `32*(B−G) / min(B,G)` | `0x0090f9ee`–`0x0090fa2c` |
| a súlypont | `Σ(x−32)·H / ΣH` és `Σ(y−32)·H / ΣH` | `0x0090fb08`–`0x0090fbf9` |

Mindkét számláló lehet **negatív** (vörös-hiányos képpont, kék felé húzó
súlypont). A C `/` ilyenkor **nulla felé csonkol**, a Python `//` viszont a
**padló felé kerekít** — a kettő negatív számoknál pontosan 1-gyel tér el.
A visszafejtett modellünk `//`-t használt, és ez volt a teljes maradék hiba:

| változat | átlagos csatorna-eltérés a 12 páron |
|---|---:|
| mindkettő `//` (padló) — az eddigi modell | 1,370 |
| csak a tengely-osztás csonkol | 1,021 |
| csak a súlypont-osztás csonkol | 0,841 |
| **mindkettő csonkol (a natív viselkedés)** | **0,614** |

Összehasonlításul: a mai kódunk **2,352** (ma újramérve), az érintetlen kép
5,287, és a korábban „elméleti alsó korlátnak" hitt orákulum 0,974.
**A modell tehát az orákulum ALÁ ment** — vagyis nem közelítés többé.

Hogy ez mennyire nem véletlen: az `Empty Space` volt az egyetlen kép, ahol a
becslőnk korrekciót kért (`kR = 120`) olyan képre, amit a **Picasa
érintetlenül hagyott**. A csonkítással a becslő pontosan `kR = 128`-at ad, és
a kimenetünk **azonos a bemenettel** — ugyanaz a döntés, mint az eredetié.
A 12-ből 10 kép javul, egy sem romlik.

A maradék 0,614 a **JPEG-újratömörítés zaja**: a két képen, amit a Picasa nem
változtatott meg, az érintetlen kép és a Picasa kimenete közti eltérés
0,671 és 0,709 — ugyanez a nagyságrend.

*Bizonyítottsági fok: **megerősített**.* A hipotézist a kód adta (futásidejű
osztó + előjeles számláló), a mérés pedig egyértelműen eldöntötte.

### 2. Az `M⁻¹` iránya a KÓDBÓL eldől — mérés nélkül

Korábban a `M · diag(g) · M⁻¹` és a `M · diag(g) · M` közti választás
mérésre hivatkozott (81,70 vs 0,45). **Erre nincs szükség**, a dekompilátum
és egy sornyi számolás elegendő:

1. A `0x00a4a140` **3 × 3-as invertáló**: Sarrus-szabállyal determinánst
   számol, nulla determinánsnál **egységmátrixot** ír a célba, egyébként az
   adjungáltat osztja (`0x00a4a0a0`), majd 9 dwordöt másol. A forrás `ECX`,
   a **cél `EDX`** (`referencia/dekompilalt/hivasi-fa.c:2320`).
2. A hívó a kilenc konstanst egy veremtömbbe teszi, arról **másolatot**
   készít (`rep movsd`, `ecx = 9`), és a hívás után **ugyanabból a tömbből**
   olvas tovább — miközben a záró balszorzás a kilenc konstanst
   **közvetlen operandusként** használja (`1.9044`, `1.8018`, … a
   dekompilátumban is így látszik). Ha a tömb a hívás után is `M` volna, a
   fordítónak nem lett volna miért két külön forrásból dolgoznia.
3. **A döntő érv, kép nélkül:** semleges becslésnél `k = (128,128,128)`, és
   `L = (77+151+28)·128 >> 8 = 128`, tehát `g = (1,1,1)` **pontosan**.
   - ha a tömb `M⁻¹`: `A = M·I·M⁻¹ = I` — és `float32`-ben a 16.16-os mátrix
     **pontosan** `diag(65536)` lesz, a kimenet bájtra azonos a bemenettel;
   - ha a tömb `M`: `A = M² `, aminek az átlója 3,16…3,58 — a középszürke
     `(128,128,128)` képpontból `(255,255,255)` lesz, `(64,64,64)`-ből
     `(189,255,255)`. Vagyis **minden kép fehérre égne**.

   Egy „automatikus színkorrekció", ami a semleges képet fehérre égeti,
   nem lehetséges olvasat. `det(M) = 6,567`, tehát az invertáló
   nulla-determináns ága sem sül el.

Ez a három pont együtt **kép nélkül** rögzíti az alakot; a golden-párok már
csak a végeredményt hitelesítik.

### 3. Kép nélkül futtatható önellenőrzések

A modell két invariánsa **bemeneti kép nélkül** ellenőrizhető, tehát
egységtesztnek való:

| invariáns | miért igaz |
|---|---|
| `k = (128,128,128)` → a 16.16-os mátrix **pontosan** `diag(65536)`, a kimenet bájtra azonos | `g = 1` pontosan, `M·I·M⁻¹ = I` |
| tetszőleges `k`-ra `(A·k) >> 16 == (L,L,L)` **±1-en belül** | `A·k = M·diag(P/Q)·Q = M·P = (L,L,L)` |

A második a képlet algebrai önellenőrzése: a mátrix a becsült megvilágítás
színét a vele **azonos világosságú** semleges szürkére viszi.

### 4. A `k` értékkészlete `[68 … 240]` — a `clip(k, 0, 255)` halott ág

A becslő pszeudokódjában szereplő `clamp(k(d), 0, 255)` soha nem sül el:

- a köbös súly `w = ((32 − táv)³) >> 5` **nullázza** a vödröt, ha
  `32 − táv ≤ 3` (mert `3³ = 27 < 32 ≤ 64 = 4³`);
- tehát csak a `táv ≤ 28`-as vödrök élnek túl, és a súlypont sem eshet
  ezen kívülre: `dx, dy ∈ [−28, +28]`, nem `[−32, +32]`;
- ebből `k(d) ∈ [16384/(60·4), (32+28)·4] = **[68 … 240]**`.

A 12 mérőképen a tényleges tartomány `kR ∈ [97, 148]`, `kB ∈ [78, 156]`.
Így a bájtba csomagolás túlcsordulásával (`k = 256`) sem kell számolni.

## A „Nyitva 7" két maradéka LEZÁRVA (2026-08-16)

### 1. A `Cinemascope` jelölőnégyzet polaritása — alapból BE

```xml
<mx:CheckBox id="cbLetterbox" selected="true"/>
```

A jelölő **alapértéke bekapcsolt**, és a bekapcsolt állapot jelenti a
mozivászon-sávokat. A `filterdesc.xml` képletei ezt egyértelműsítik:

| | `cbLetterbox` BE | `cbLetterbox` KI |
|---|---|---|
| vágási magasság | `min(round(W/1.7), H)` | `H` (a teljes kép) |
| felső/alsó szegély | `round(cropHeight · 0,15)` | **0** |
| átméretezés | `cropHeight · 0,95` | `cropHeight · 1,0` |

Vagyis **bekapcsolva** 1,7 : 1-re vág, 15-15 %-os fekete sávot tesz alá-fölé,
és 95 %-ra zsugorít; **kikapcsolva** csak a szín-/görbe-/zaj-lánc fut, geometria
nélkül. A `Cinemascope`-nak **nincs `<presets>` blokkja** — a jelölő az egyetlen
paramétere.

**A mai kódunk helyes:** `render/glimmer_creative.py` `apply_cinemascope(image,
letterbox: bool = True)` — az alapérték és a jelentés is egyezik.
*Bizonyítottsági fok: megerősített.*

### 2. A `PicnikFocalPixelate` (és a `FocalZoom`) puck-sorrendje

A puck (a képre kattintva mozgatható fókuszpont) koordinátái a **preset-lista
3. és 4. rekeszében** állnak, `0…1` közé normálva, alapértéken középen:

| rekesz | `PicnikFocalPixelate` | `FocalZoom` | jelentés |
|---:|---:|---:|---|
| 0 | 8,0 | 99,0 | `_sldrImpact` |
| 1 | 20,0 | 20,0 | `_sldrRadius` |
| 2 | 90,0 | 99,0 | `_sldrHardness` |
| **3** | **0,5** | **0,5** | **puck X** |
| **4** | **0,5** | **0,5** | **puck Y** |

A `_sldrFade` **nem szerepel** a preset-listában (az a lánc szokásos záró
paramétere).

**Keresztellenőrzés a régi szűrővel:** a Glimmer előtti `focalpixelate`
(674. sor) szintén `cursor type="puck"`, de a **presetjei csak 0…3**
(Pixel Size, Focal Size, Edge Hardness, Fade) — **puck-rekesz nincs bennük**.
A puck-koordináták tehát a **Glimmer-változatok** sajátja, és ott a három
csúszka UTÁN jönnek, x majd y sorrendben.

*Bizonyítottsági fok: megerősített* (két Glimmer-szűrő azonos alakja + a régi
szűrő ellenpéldája).

## A „`tint` 4 hex jegyet ír" — SAJÁT TESZTADAT-ARTEFAKTUM (2026-08-16)

A „Nyitva 4" maradéka ez volt: *„valós adatban a `tint` 4 hex jegyet ír
(`ffff`), a másik kettő 8-at. A parszernek változó hosszú hex-színt kell
tűrnie."* **A `tint` valójában szintén 8-at ír.**

### A binárisban EGYETLEN hex-darabka van

A lánc-szerializáló darabkái egymás mellett állnak a `.rdata`-ban
(`0x00c8d9c0` környéke, a `filter_%s_label0` előtt):

```
%c      ,%d      ,%f      ,%08x      :%d      :%g      |%g      %08x
```

**Nincs `,%04x` és nincs `,%x`** — a teljes binárison végigkeresve sem
(`grep -abo`). A színparaméter tehát **mindig `%08x`**: nyolc jegy,
nullákkal feltöltve.

*(Kivétel a `desat`, aminek saját, bespoke formátuma van:
`"%c,%f,%f,%f"` — abban nincs is szín.)*

### A valós korpusz ezt igazolja

A NAS 859 `.picasa.ini`-jéből kiszedve minden `tint`-szerű bejegyzést:

```
tint=1,0.000000,fffccc01
tint=1,0.000000,ff1afe4a
dir_tint=1,…,ffbba6a2      (9 db)
```

**Mind a tizenegy 8 jegyet ír**, a `tint` is.

### Honnan jött akkor a `ffff`

A **saját golden-kitünkből**:

```
research/golden-kit/…/.picasa.ini:   tint=1,79.842102,ffff
```

Ez egy **kézzel írt mérőfájl** — a `79.842102` a `tint` csúszkatartományán
is kívül van. Vagyis a „4 jegyes szín" nem a Picasa viselkedése, hanem a mi
tesztadatunk.

**Ebből következik a 192. sor „R=0 anomáliája" is:** az `ffff` parszolva
`0x0000FFFF`, tehát R=0, G=255, B=255 — pontosan az, amit egy 4 jegyes érték
ad. Az anomáliát **mi állítottuk elő**, nem a Picasa.

### Mit jelent ez a parszerre

A változó hosszú hex tűrése **robusztussági kényelem**, nem
Picasa-kompatibilitási követelmény — a Picasa sosem ír 8-nál kevesebbet.
Megtartani nem hiba, de **nem szabad rá modellt építeni** (pl. „a `tint`
16 bites színt használ").

*Bizonyítottsági fok:* **megerősített** az író oldalra (a binárisban egyetlen
hex-darabka van, `,%08x`) · **erős** a korpuszra (11 valós bejegyzés, mind
8 jegyes — a `tint`-ből mindössze kettő van).

## A `finetune` v1 ↔ v2 hőmérséklet 2×-skála hipotézise MEGDŐLT (2026-08-16)

A „Nyitva" lista 9. pontja ezt vetette fel: *„a `filterdesc.xml` szerint a v1
tartománya `[−0,5..0,5]`, a v2-é `[−1..1]`; ha a görbe azonos, akkor
`v2_érték = 2 · v1_érték` pontosan reprodukálja a v1 kimenetét"* — és ha
igazolódik, a v1-hez **nem kell külön LUT**.

### A premissza helyes, a következtetés nem

A `filterdesc.xml` szerint a két szűrő **ugyanaz a négy csúszka, azonos
sorrendben**; egyedül a 3. (Color Temperature) tartománya tér el:

| | `range` | `offset` | tengely |
|---|---|---|---|
| `finetune` (v1) | 1.0 | 0.5 | `−0,5 … +0,5` |
| `finetune2` (v2) | 2.0 | 1.0 | `−1 … +1` |

Tehát az 5. ini-rekesz **mindkettőben** a hőmérséklet — a hipotézis
tesztelhető.

### A mérés (golden-kit `04-finetune1` vs `03-finetune2`)

| kép | **v1(+0,5) vs v2(+1,0)** | kontroll: v1(+0,5) vs v2(+0,5) | v1(+0,5) vs érintetlen |
|---|---:|---:|---:|
| chart_color | 23,09 | 26,26 | 32,40 |
| chart_ramp | 16,70 | 17,78 | 20,64 |
| **átlag** | **15,82** | 16,43 | 17,76 |

**Ha a hipotézis igaz volna, az első oszlop ~0 lenne.** Ehelyett alig jobb a
„azonos számérték" kontrollnál, és mindkettő közel az érintetlen képhez mért
távolsághoz. *Bizonyítottsági fok: megerősített (cáfolat).*

### És az ELLENKEZŐ irányba tér el

Az érintetlen képhez mérve:

| kép | v1 −0,5 | v1 +0,5 | v2 −0,5 | v2 +0,5 | v2 +1,0 |
|---|---:|---:|---:|---:|---:|
| chart_color | 29,66 | 32,40 | 15,35 | 6,45 | 9,97 |
| chart_ramp | 18,82 | 20,64 | 8,46 | 3,82 | 6,13 |

A **v1 a saját maximumán (±0,5) 3–5-ször erősebben hat, mint a v2 a saját
maximumán (±1,0)**. Ez a 2× *tágítás* várakozásával ellentétes irányú: a
tengely szélesebb lett, a hatás mégis gyengébb. A két változat **más görbét**
használ, nem ugyanazt más skálán.

**Következmény:** a v1-hez **saját LUT kell**; a 9. pont „olcsó nyereség"
ígérete nem áll.

### ⚠️ Mérőanyag-figyelmeztetés: a `chart_detail` a v1-hez használhatatlan

A `chart_detail` képen a **teljes v1 lánc no-op**: az érintetlenhez mért
eltérés `u−05` = 0,39 · `u+05` = 0,24 · **`b050` (Fill Light) = 0,26**, és a
`u−05` ↔ `u+05` különbség **0,23**. Vagyis a Picasa ezen a képen a
`finetune`-t **egyáltalán nem alkalmazta** — nem csak a hőmérsékletet.

Ugyanezen a képen a v2 rendben lefutott (5,3–7,8).

**A `chart_detail`-t v1-mérésből ki kell hagyni**, és a v1 golden-anyagot
érdemes újraexportálni. *Bizonyítottsági fok: megerősített (mérés).*

### Az `autocolor` mátrix-építője — struktúra megvan, három alak megdőlt (2026-08-16)

#### ⚠️ Helyesbítés: a PR #760 önkorrekciója MAGA is téves volt

A #758 azt írta, hogy az alkalmazó a kilenc konstansból építi a mátrixot; a
#760 ezt „túlzásnak" minősítette azzal, hogy a konstansok egy **másik**
pufferbe (`[esp+0xcc]`) mennek. **Ez a helyesbítés hibás volt.**

A prológus a kilenc konstanst **`[esp+0x30] … [esp+0x50]`-be** teszi
(`0x0090edcb`–`0x0090ee1b`), és a `rep movsd` innen **másolatot** készít
`[esp+0xcc]`-be a `0xa4a140` számára. Az **eredetiek a helyükön maradnak**, és
a képpont-ciklus később **ugyanezeket a rekeszeket** olvassa — de már
**egészként** (`mov eax, dword ptr [esp+0x38]`, `0x0090f36c`).

**Vagyis a rekeszkészletet a köztes float-szakasz írja felül a végleges,
fixpontos mátrixszal.** A #758 eredeti állítása volt a helyes.

#### Az első lépés: a fehérpont a C-térben

A három becsült erősítés (`[esp+0xfe]` = kR, `bh` = 128, `bl` = kB) floattá
alakul (`[esp+0x18]`, `[esp+0x1c]`, `[esp+0x20]`), majd
`0x0090eefa`–`0x0090ef73`:

```
[esp+0x78] = C00*g0 + C01*g1 + C02*g2
[esp+0x7c] = C10*g0 + C11*g1 + C12*g2
[esp+0x80] = C20*g0 + C21*g1 + C22*g2
```

Vagyis **`v = C · g`** — az erősítés-vektor a kilenc konstans terébe
transzformálva. Ez a klasszikus kromatikus adaptáció első lépése.

Ezt követi egy **második menet** (`mov ecx, 9`, `0x0090efa2`), ami a végleges
mátrixot állítja elő — **ez még nincs kiolvasva**.

#### ❌ Három adaptációs alak megdőlt

A 9 nem-triviális golden-páron (`referencia/autocolor/`):

| modell | átlagos eltérés |
|---|---:|
| **orákulum** (a legjobb 3 × 3) | **0,974** |
| puszta átlós `diag(128/k)` | 3,100 |
| `C⁻¹ · diag(v₁/v) · C` | 9,661 |
| `C⁻¹ · diag(1/v) · C` | 43,504 |
| `C⁻¹ · diag(v) · C` | 52,976 |

**Mindhárom rosszabb a puszta átlósnál** — a `v = C·g` nem így épül be.
*Bizonyítottsági fok: megerősített (cáfolat).*

#### A következő lépés pontosan

A `0x0090efa2`-től induló **kilenc elemű ciklus** — az írja a végleges
fixpontos mátrixot a `[esp+0x30 … 0x50]` rekeszekbe. Amíg ez nincs meg,
minden „kézenfekvő" adaptációs alak **kimérendő, nem feltételezhető**: eddig
öt jelöltet mért ki két kör, és mind rosszabb a puszta átlósnál.

## „Nyitva"-átvilágítás (2026-08-16) — mi elavult és mi él még

A lapon szétszórt „nyitott" jelölések egy része **a saját későbbi munkánk
óta tárgytalan**, de a jelölés bennmaradt — és egy következő kör
végigjárhatta volna ugyanazt. Ez az átvilágítás ezt zárja ki.

### Elavult jelölések (a válasz máshol már megvan)

| jelölés | hol a válasz |
|---|---|
| `Vignette` analitikus illesztése | `filterdesc-registry.md` 4.3 — belső ragyogás, `sugár = Blur·0,02·max(W,H)/4` |
| a 4–5. fül csúszka-leképezése | `filterdesc.xml` (2026-08-06): név, min–max, alapérték mind a 12 csúszkára |
| `autocolor` csillapítási szabálya (gray-world vs fehérpont) | **egyik sem** — 64 × 64-es 2D hisztogram + köbös súlyozás, ld. „Az `autocolor` becslője VISSZAFEJTVE" |
| `finetune2` utolsó paramétere | `picasa-ini-format.md` — a **színhőmérséklet**, `−1 … +1` |
| `tint` 4 jegyes hex „anomáliája" | saját tesztadat-artefaktum, ld. a megfelelő szakaszt |
| `desat` negyedik `0,333`-as mezője | **nem létezik**, `picasa-native-filter-registry.md` |
| `_MIN_STRETCH_SPAN = 58` mint gain-korlát | **nem korlát** — a csatorna-keverés mellékhatása |
| a `finetune` v1 ↔ v2 2×-skála | **megdőlt**, saját LUT kell |

### Ami TÉNYLEG nyitott (jeggyel)

| kérdés | jegy |
|---|---|
| az elmosó mag pontos alakja (`unsharp`, `blur`) | **#762** |
| az `autocolor` 3 × 3-as mátrixának összeállítása | **#759** |
| az `enhance` keverés bevezetése a kódba | **#721** |
| a `radblur` sugár-hányada: `0,009` (mért) vs `0,01` (dekompilátum) | #317 |
| a `Comicize`/`FocalZoom`/`PicnikFocalPixelate` mintavételezési peremszabálya | #569/#570 |

> **A tanulság:** a „nyitott" jelölés **karbantartást igényel**. Ha egy kör
> megválaszol valamit, a MÁSIK lapon lévő jelölést is le kell venni —
> különben a bizonyíték megvan, de a következő kör nem találja meg.

## A `radblur` sugár-konstansa: a dekompilátum olvasata PONTOS (2026-08-16)

A nyitott kérdés két ágra oszlott: *„a dekompilált konstans olvasata
pontatlan-e, VAGY a natív hívás máshonnan kapja a szélességet."*
**Az első ág kizárva.**

### A konstans bájtra kiolvasva

A `radblur` callbackjében (`0x008f8520`):

```asm
0x008f85b0  fld  dword ptr [ebx + 0x2c]      ; a csúszka-paraméter
0x008f85b9  call 0x9a8fe0                    ; (kép-másolás, a FPU-verem érintetlen)
0x008f85ce  fmul qword ptr [0xcf40b8]        ; ← a konstans
```

A `.rdata`-ból:

```
0x00cf40b8 = 7b 14 ae 47 e1 7a 84 3f   →  double  0.01
```

**Pontosan `0,01`, és `double` pontosságon** (`fmul qword`, nem `dword`).
A dekompilátum tehát jól olvasta; a mért `0,009`-es optimum **nem** a
konstansból jön.

### Ami ebből következik

A `0,9 ×` eltérés forrása **az, amit a `0,01` szoroz** — vagyis a natív
oldal olyan méret-mértéket használ, ami az általunk feltételezett
képszélességnek kb. 0,9-szerese. Kézenfekvő jelöltek (mérésre, nem
feltételezésre):

| jelölt | 4:3 arányú képen a szélesség hányada |
|---|---:|
| `(W + H) / 2` | 0,875 |
| `√(W · H)` | 0,866 |
| a **teljes felbontású** kép mérete kicsinyített előnézet helyett | képfüggő |

A `fmul qword` további részlete, hogy a **sugár-számítás dupla pontosságú** —
ha a mi modellünk `float`-on számol, a kerekítés is eltérhet.

*Bizonyítottsági fok: megerősített* a konstansra (a `.rdata` bájtjai) ·
**nyitott** arra, hogy mit szoroz.

**A #317 teendője ezzel szűkült:** nem a konstanst kell újraolvasni, hanem a
`0x008f85e2`–`0x008f8617` közti szakaszt (`[esp+0x20]`, `[esp+0x24]`,
`[esp+0x28]` feltöltését), illetve mérni a fenti három jelöltet a
`referencia/blur-meres/` anyagon.

### Az `autocolor` mátrix-építő SZERKEZETE: von Kries a C-térben (2026-08-16)

#### ⚠️ Előbb egy önkorrekció: a „von Kries megdőlt" ELHAMARKODOTT volt

A PR #760 és #770 összesen öt adaptációs alakot mért ki, és mind rosszabb
volt a puszta átlósnál — ebből azt írtuk, hogy „a kilenc konstans nem
adaptációs tér". **A kód szerint DE IGEN az** — csak mindegyik korábbi
próba rossz *behelyettesítéssel* dolgozott. A **forma** von Kries; a
cáfolat a *paraméterezésre* vonatkozott, nem a formára.

#### A kód, amiből ez látszik

```asm
0x0090efb8  rep movsd (ecx=9)      ; a kilenc konstans → [esp+0xcc] (3×3 puffer)
...                                 ; v2 = C · g2  →  [esp+0x60/0x64/0x68]
0x0090f002  fld [esp+0x78] ; fdiv [esp+0x60] ; fstp [esp+0xcc]
0x0090f011  fld [esp+0x7c] ; fdiv [esp+0x64] ; fstp [esp+0xdc]
0x0090f020  fld [esp+0x80] ; fdiv [esp+0x68] ; fstp [esp+0xec]
```

- `[esp+0x78/0x7c/0x80]` = **`v1 = C · g1`** (az előző szakaszból);
- `[esp+0x60/0x64/0x68]` = **`v2 = C · g2`** (egy második erősítés-vektorból);
- a **hányadosuk** a `[esp+0xcc]`, `[esp+0xdc]`, `[esp+0xec]` rekeszekbe megy.

**A három céloffszet a 9 dwordös puffer 0., 4. és 8. eleme — vagyis pontosan
a 3 × 3 mátrix ÁTLÓJA.** Ez betű szerint a von Kries-alak:

```
d = (C · g1) / (C · g2)        elemenként
M = C⁻¹ · diag(d) · C          (a záró összeállítás)
```

*Bizonyítottsági fok: megerősített* a szerkezetre (a három osztás és a
célrekeszek offszetjei).

#### Ami NYITVA marad: MELYIK két erősítés-vektor

Három behelyettesítést mértem ki a 9 nem-triviális golden-páron:

| modell | átlagos eltérés |
|---|---:|
| **orákulum** (a legjobb 3 × 3) | **0,974** |
| puszta átlós `diag(128/g)` | 3,100 |
| `diag((C·1)/(C·g))` | 3,718 |
| `C⁻¹ · diag((C·1)/(C·g)) · C` | 3,786 |
| `C⁻¹ · diag((C·g)/(C·1)) · C` | 13,419 |

Egyik sem veri a puszta átlóst. **A `g1` és `g2` tehát nem az, aminek
gondoltam** — a `0x0090eedf`–`0x0090ef96` közti szakasz **kétszer** tölti
fel a `[esp+0x18/0x1c/0x20]` hármast, és a két feltöltés forrása eltér; ezt
regiszter-szinten kell végigkövetni.

**A következő kör pontosan itt folytassa:** `0x0090eedf`–`0x0090ef96`, a
`[esp+0x18]`, `[esp+0x1c]`, `[esp+0x20]` két egymást követő feltöltésének
forrása.

#### Amit ez a kör KIZÁRT

- `diag((C·1)/(C·g))` és mindkét `C⁻¹ diag(...) C` változata a fenti
  behelyettesítéssel;
- (a korábbi körökből) `C⁻¹ diag(1/v) C`, `C⁻¹ diag(v) C`,
  `C⁻¹ diag(v₁/v) C`, `C⁻¹ D C`, `C D C⁻¹` — **összesen nyolc alak**.

### Az elmosó út PIRAMIS-alapú — két jelölt kizárva (#762, 2026-08-16)

#### A lelet

A `0x00a42c20` diszpécser két, közvetlenül hívott függvénye **nem** a
konvolúció: az egyik egy **felező kicsinyítő** (mipmap), a másik egy
**2D affin transzformáció-összefűző**. Ebből viszont kiderül, hogy az elmosó
út **képpiramison** dolgozik — ez magyarázza, miért csúszik el egy sima
Gauss-modell nagy sugárnál.

#### Bizonyíték

**`0x00a43230` (336 b) — 2 × 2-es dobozkicsinyítő.** A cél mérete a forrás
fele (`sar esi,1` / `sar eax,1`, `0x00a43255`), és két szomszédos sorból
olvas (`lea ebx, [edi + edx*8]` = 2 sornyi lépés, `0x00a4329b`). A belső
ciklus a klasszikus SWAR-trükkel átlagol négy képpontot:

```asm
0x00a432c8  and eax, 0xff00ff      ; a páros bájtok (B, R)
0x00a432d7  shr ecx, 8
0x00a432e4  and ecx, 0xff00ff      ; a páratlan bájtok (G, A)
...                                 ; négy képpont összege csatornánként
```

**`0x009e6340` (321 b) — 2D affin transzformáció összefűzése.** Hat float
mezőt szoroz-összegez (`[eax+0..0x20]` × `[ecx+8..0x14]`), az `a·e + b·f`
mintában — ez `[a b c; d e f]` alakú transzformációk kompozíciója, nem
képszűrés.

#### Ami NYITVA marad — és hol folytassa a következő kör

A tényleges konvolúció a diszpécser **virtuális hívásában** van
(`mov eax,[edi]; mov edx,[eax+8]; call edx` — `0x00a42c38`, `0x00a42c5c`,
`0x00a42c7c`), nem a közvetlen hívottak közt. **A vtable-t kell feloldani:**
melyik osztály példánya érkezik a diszpécserbe az `unsharp`
(`0x0090c556`) hívási helyén.

#### Amit ez a kör KIZÁRT

- `0x00a43230` mint elmosó mag — **kicsinyítő**;
- `0x009e6340` mint elmosó mag — **transzformáció-összefűző**.

#### Mit jelent a piramis a mi modellünkre

Ha a natív út kicsinyít → szűr → nagyít, akkor **nagy sugárnál a mi
egylépéses Gauss-unk elvileg sem tud egyezni**: a piramis a magas
frekvenciákat a kicsinyítéskor levágja, és a visszanagyítás
interpolációs jelleget visz a képbe. A `referencia/blur-meres/` öt
csúszkaállásán mért 0,48–1,63 szintes él-profil-hiba ezzel konzisztens.

*Bizonyítottsági fok: megerősített* a két kizárásra és a kicsinyítő
azonosítására · **feltételes** arra, hogy a teljes út piramis (a
kicsinyítő létezése erősen valószínűsíti, de a szűrő-lépést még nem láttuk).

### A `glimmer::TiledImageMask` vtable feltérképezve (a `Comicize` pontmaszkja, 2026-08-16)

A `Comicize` nyitott pontja: *„a natív pontmaszk pontos antialiasingja és
peremkerekítése"*. Ez a kör **térképet** ad hozzá, nem megfejtést — a
raszterizáló mélyebben van, de innentől nem kell újra keresni.

#### A két maszk-osztály vtable-je

| osztály | vtable | rekeszek |
|---|---|---:|
| `glimmer::TiledImageMask` | `0x00cf02e8` | 8 |
| `glimmer::CircularGradientImageMask` | `0x00cf0890` | 10 |

#### A `TiledImageMask` rekeszei

| # | cím | méret | mi ez |
|---:|---|---:|---|
| 0 | `0x00bba030` | 30 | konstruktor/pusztító körüli |
| 1 | `0x00bba250` | 133 | |
| 2 | `0x00bb9fc0` | 5 | triviális visszatérő |
| 3–4 | `0x004bdeb0` | 3 | közös üres slot |
| **5** | `0x00bba2e0` | 481 | **attribútum-olvasó** — **12** ismétlődő `call 0x8eb160` / `call 0x8eb520` pár |
| **6** | `0x00bba4d0` | 169 | **12 × `call 0x8f1500`** — ugyanarra a 12 attribútumra |
| **7** | `0x00bba580` | 234 | **a maszk előállításának belépője** → `0x00bba670` (762 b) |

A tényleges raszterizálás még mélyebben: `0x00bba980`, `0x00bbb070`,
`0x00bbace0` (763 b).

#### Amit ez már most elárul

**A maszknak 12 attribútuma van.** A `filterdesc.xml` `Comicize`-a ennél
lényegesen kevesebbet állít be — a többi tehát **beégetett alapértékkel**
működik, és épp ezek közt lesz az antialiasing/peremkerekítés kapcsolója.
Ez magyarázza, miért nem lehetett a `filterdesc`-ből kiolvasni.

#### Ami NYITVA marad — és hol folytassa a következő kör

1. a 12 attribútum **neve**: a `0x00bba2e0`-ben a `call 0x8eb160` elé tolt
   sztring-mutatókból (az annotált diszasszemblálás kiírja őket);
2. a raszterizáló ciklus: `0x00bba670` → `0x00bba980` / `0x00bbb070`.

*Bizonyítottsági fok: megerősített* a vtable-feloldásra és a rekeszek
szerepére · **nyitott** az antialiasing szabályára.

> A `CircularGradientImageMask` vtable-je ugyanígy fel van oldva — a
> `Vignette` / `Focal*` család analitikus modelljéhez az lesz a belépő.

#### A `TiledImageMask` TIZENKÉT attribútuma — kiolvasva (2026-08-16)

A `0x00bba2e0` attribútum-olvasójában a hívások elé tolt sztringek:

| # | attribútum | mire való |
|---:|---|---|
| 1–2 | `tileWidth` · `tileHeight` | a csempe mérete (a pont rácsa) |
| 3–4 | `scaleWidth` · `scaleHeight` | a csempe tartalmának skálázása |
| 5–8 | `paddingLeft` · `paddingTop` · `paddingRight` · `paddingBottom` | a csempén belüli üres perem — **ez adja a pont méretét** |
| 9–10 | `offsetX` · `offsetY` | a rács eltolása (a második maszk fél csempével) |
| **11–12** | **`alphaMin` · `alphaMax`** | **a maszk alfa-tartománya — ez a keresett „antialiasing"** |

#### Amit a `Comicize` ténylegesen beállít

```xml
<TiledImageMask tileWidth="{_nDotSize}" tileHeight="{_nDotSize}"
                alphaMin="0.0" width="{imagewidth}" height="{imageheight}"
                id="_mskColorSpots1"/>
<TiledImageMask … offsetX="{_nDotSize/2}" … id="_mskColorSpots2"/>
```

Vagyis a tizenkettőből **hármat**: `tileWidth`, `tileHeight`, `alphaMin`
(a másodikon `offsetX` is). **A maradék kilenc beégetett alapértékkel megy.**

#### Ami ebből következik

1. **Az `alphaMin = 0.0` explicit** — a maszk alfa alulról 0-ig fut, tehát a
   pont közepe teljesen átlátszó. Az `alphaMax` **nincs megadva**, vagyis az
   alapértéke (feltehetően 1,0) érvényes.
2. **A pont mérete nem külön paraméter:** a `padding*` négyese szabja meg a
   csempén belül, és a `Comicize` **egyiket sem állítja** — a pont/csempe
   arány tehát **beégetett**, nem a felhasználó állítja. Ez magyarázza, miért
   nem találtuk a `filterdesc`-ben.
3. **A második maszk eltolása `offsetX = _nDotSize/2`** — a doksi „fél
   csempével eltolt" megfogalmazása ezzel **kódból is igazolt**, és
   **csak vízszintesen** tolódik (`offsetY` nincs megadva).

*Bizonyítottsági fok: megerősített* az attribútum-névsorra (a `.rdata`
sztringjei az olvasó-hívások előtt) és arra, hogy a `Comicize` melyik hármat
állítja · **nyitott**: a kilenc beégetett alapérték számszerű értéke — az a
konstruktorban (`0x00bba030` / `0x00bba250`) lesz.

#### ⚠️ A „kilenc beégetett alapérték" NEM az objektumban van (2026-08-16)

Az előző kör azt írta, hogy a `Comicize` által nem állított kilenc
`TiledImageMask`-attribútum „beégetett alapértékkel megy", és a következő
lépésként a konstruktort jelölte meg. **A konstruktor viszont nem tartalmaz
alapértéket.**

`0x00bb9fd0` (96 bájt) — a teljes objektum nullázása:

```asm
xor ecx, ecx
mov dword ptr [eax + 4], ecx      ; …és így tovább, 4-esével
mov dword ptr [eax], 0xcf02e8     ; a vtable-mutató
…
mov dword ptr [eax + 0x74], ecx   ; a +0x04 … +0x74 tartomány MIND nulla
```

Egyetlen `fld` vagy numerikus konstans sincs benne.

**A pusztító (`0x00bba050`, 510 b) elárulja, MIÉRT:** tizenkét
**sztring-objektumot** szabadít fel (`+0x20`, `+0x28`, … `+0x70`, nyolcasával
lépve, mindegyik „mutató + jelző" pár). Az attribútumok tehát **kifejezés-
szövegként** tárolódnak (a `filterdesc.xml` `{...}` kötései), nem parszolt
számként.

**Következmény:** egy be nem állított attribútum **üres sztring**, és a
tartalék értéket a **fogyasztó** adja — a raszterizáló, amikor üres
kifejezést kap. Az alapértékek tehát **nem az osztályban**, hanem a
maszk-előállító kódban vannak.

*Bizonyítottsági fok: megerősített (cáfolat)* — a konstruktor teljes
tartalma és a pusztító felszabadítási mintája.

**A következő kör belépési pontja ezzel változik:** nem a konstruktor, hanem
a raszterizáló (`0x00bba580` → `0x00bba670` → `0x00bba980` / `0x00bbb070`) —
ott kell megnézni, mit tesz üres `padding*` / `alphaMax` / `scale*` esetén.

### A `CircularGradientImageMask` HÉT attribútuma — és egy, amit sosem állítunk (2026-08-16)

A radiális maszkot a `glimmer::CircularGradientImageMask` adja (vtable
`0x00cf0890`). Ezt használja a **`Vignette`, `Holga`, `Lomo`,
`PicnikFocalPixelate`, `FocalZoom`** — a teljes „körkörös" család.

Az attribútum-olvasójából (`0x00bcfc70`, 291 b) a `.rdata`-sztringek:

| attribútum | cím | mire való |
|---|---|---|
| **`aspectRatio`** | `0xcf0d9c` | **a gradiens kör vagy ellipszis alakja** |
| `innerRadius` | `0xcf0da8` | a védett zóna sugara |
| `outerRadius` | `0xcf0db4` | a teljes hatás sugara |
| `innerAlpha` | `0xcf0dc0` | alfa a belső sugáron |
| `outerAlpha` | `0xcf0dcc` | alfa a külső sugáron |
| `xCenter` · `yCenter` | `0xcf0dd8/e0` | a középpont |

#### ⚠️ Az `aspectRatio`-t a `filterdesc.xml` EGYSZER SEM állítja be

A csomag mind a **négy** `CircularGradientImageMask` használata csak
`width`, `height`, `xCenter`, `yCenter`, `innerRadius`, `outerRadius`,
`innerAlpha`, `outerAlpha` attribútumokat ad meg. Az `aspectRatio` tehát
**mindig a tartalék értékén** fut.

**Ez fontos, mert épp ez dönti el, hogy a maszk nem négyzetes képen kör-e
vagy ellipszis.** A mai `circular_gradient_mask()`
(`render/glimmer_ops.py:475`) `np.hypot(x−cx, y−cy)`-t számol, azaz
**képpont-egységben kört** — ha a natív tartalék az `aspectRatio`-t a
kép oldalarányára állítja, akkor az eredeti **ellipszist** rajzol, és a
sarkoknál mérhetően eltérünk.

#### Eredeti / nálunk / teendő

| | eredeti | nálunk |
|---|---|---|
| a gradiens alakja | `aspectRatio` attribútum (be nem állított → tartalék) | **fix kör** (`hypot`) |
| `innerAlpha`/`outerAlpha` | külön attribútum, a `filterdesc` állítja | a maszk fixen 0→1 |

Az `innerAlpha`/`outerAlpha` nálunk **nincs paraméterezve**: a
`circular_gradient_mask` mindig 0-ból 1-be megy. A `filterdesc` viszont a
`PicnikFocalPixelate`-nél megfordítja őket
(`outerAlpha="{_chkReverse.selected?0:1}"`), tehát a **Fordított** jelölő
ezen keresztül hat.

#### Ami NYITVA marad

Az `aspectRatio` **tartalék értéke** — ugyanaz a kérdés, mint a
`TiledImageMask` kilenc be nem állított attribútumánál: a fogyasztóban van,
nem az objektumban (a konstruktor mindent nulláz). Belépési pont a
`CircularGradientImageMask` maszk-előállítója: `0x00bcfe10` (392 b) és
`0x00bc2a50` (734 b).

*Bizonyítottsági fok: megerősített* az attribútum-névsorra és arra, hogy a
`filterdesc` egyszer sem állítja az `aspectRatio`-t · **nyitott** a tartalék
értéke.

## Az `unsharp` elmosása az ÁTMÉRETEZŐBŐL jön (2026-08-16)

### A korábbi jelölés téves volt

A lap eddig azt írta, hogy az `unsharp` elmosómagja a `FUN_00a42c20`
mögötti objektum „2-es módja", és ezt nyitott kérdésként tartotta nyilván.
**A `0x00a42c20` nem elmosómag.**

| bizonyíték | mit mond |
|---|---|
| RTTI: `ytResampler::vftable` (`0x008e3fb4`) | a 9. bejegyzése **pontosan `0x00a42c20`** |
| a hívói | **17** független hely a binárisban (`0x00425210`, `0x0042f430`, `0x00551b30`, `0x005550d0`, `0x005b0730`, `0x007e95f0`, `0x007ead60`, `0x007fb210`, `0x008cd360`, `0x0090c4a0`, `0x009ecdb0`, `0x00a50990`, `0x00a61040`, `0x00a61340`, `0x00a9f070`, `0x00bcb5e0`, `0x00425f60`) |
| a hívottjai | `0x009a8a30`, `0x009a8bc0`, `0x009ae130`, `0x009e6340`, `0x009e6df0`, `0x009e75a0`, `0x00a40a50`, `0x00a43230` — **egyik sem** a Picasa elmosómagja |

Egy elmosómagot nem hív a nyomtatás és az indexkép-készítés. Egy
**átméretezőt** igen.

### A Picasa elmosója MÁSHOL van, és már meg van fejtve

A `0x009dd0d0` a Picasa általános elmosója (kétmenetes elsőrendű IIR) —
`picasa-native-filter-workers.md` 4.2.1. Nyolc hely hívja:
`0x0076f0f0`, `0x008f8520` (`radblur`), `0x008f9090` (`dir_sharp`),
`0x0090b050` (sugaras maszk), `0x0090d3e0`, `0x0090d4b0` (`glow`),
`0x0090de10`, `0x009e8c30`.

**Az `unsharp` útvonala (`0x0090c4a0`) nincs köztük**, és a
`0x00a42c20` hívottjai között sem szerepel a `0x009dd0d0`.

### Amit ez jelent: két KÜLÖNBÖZŐ elmosás

| szűrő | mivel mos el |
|---|---|
| `glow`, `glow2`, `radblur`, `dir_sharp`, sugaras maszk | `0x009dd0d0` — kétmenetes IIR |
| **`unsharp`, `unsharp2`** | **`ytResampler`** (`0x00a42c20`), 2-es móddal |

Az `unsharp` hívása (`0x0090c4a0`) 1,0/1,0 léptéket és 0/0 eltolást ad át
(`fld1`/`fldz`, `0x0090c528`–`0x0090c53f`), a vizsgálati téglalap pedig a
két kép **közös** metszete (`min(w₁,w₂)`, `min(h₁,h₂)`,
`0x0090c4f2`–`0x0090c528`). Vagyis **1:1 arányú újramintavételezés**, aminek
az egyetlen hatása a **szűrőmag elkenése** — a `1,5f` az így kapott mag
szélessége.

### ⚠️ Nálunk ez ma Gauss

`src/picasapy/render/sharpen.py:31` — `cv2.GaussianBlur(kép, (0,0), 1.0)`,
majd `erősség × 1,21`:

| | eredeti Picasa | PicasaPy ma |
|---|---|---|
| az elmosás fajtája | **átméretező szűrőmag** (`ytResampler`, 2-es mód) | Gauss |
| a mag szélessége | **1,5** | σ = **1,0** |
| az erősség szorzója | nincs (nyersen a csúszka) | **× 1,21** |

A `σ = 1,0` és az `1,21` **illesztett** értékek: a golden-párokra hangolt
közelítései egy 1,5 szélességű, más alakú magnak. Ez magyarázza, miért
maradt az `unsharp` a „finomítandó" listán.

*Bizonyítottsági fok:* **megerősített** arra, hogy a `0x00a42c20` a
`ytResampler` metódusa és nem elmosómag (RTTI + a hívói köre) ·
**megerősített** arra, hogy az `unsharp` nem a `0x009dd0d0`-t használja
(mindkét hívási lista kiolvasva) · **erős** az „1:1 újramintavételezés"
olvasatra (a lépték- és eltolás-argumentumok a kódból).

~~**Nyitva marad:** a `ytResampler` 2-es módjának **konkrét magja** (súlyok
vagy analitikus alak).~~ → **MEGVAN** (#762): a 2-es mód a **köbös
B-spline**, tartósugár 2, és az `unsharp` a `this+0x30` szórásszorzóval
(beégetett `1,5f`) **3 képpontra szélesíti**. Ld. „A `ytResampler` KILENC
szűrőmagja" szakaszt.

### A 10-es mód: MMX-es bilineáris interpoláció (2026-08-17, #871)

A `0x009e75a0` → **`0x00aa5fb0`** (451 b) a második gyorsút: tetszőleges
affin transzformáció, **bilineáris** mintavétellel, a súlytábla
megkerülésével.

```asm
0x00aa60a0  movzx ecx, ch           ; fy — a függőleges tört, 8 bit
0x00aa60dc  movzx edx, dh           ; fx — a vízszintes tört
0x00aa6107  movd mm0, [eax]         ; P(x0,y0)
0x00aa610a  movd mm1, [eax+4]       ; P(x1,y0)
0x00aa6117  movd mm2, [eax]         ; P(x0,y1)   (egy SORRAL lejjebb)
0x00aa611a  movd mm3, [eax+4]       ; P(x1,y1)
0x00aa6130  psubw / pmullw / psrlw 8 / paddb      ; felső sor × fx
0x00aa6133  ugyanez az alsó sorra                  ; alsó sor × fx
0x00aa614e  psubw / pmullw mm5 / psrlw 8 / paddb  ; a kettő között × fy
0x00aa615b  packuswb                               ; vissza 8 bitre, telítéssel
```

**A súlyok 8 bitesek, az osztás `>> 8`** — tehát a maximális súly 255/256,
nem 1,0. Aki `/255`-tel írja újra, rendszeres sötétedést kap.

**Ezzel a `ytResampler` mind a tizenegy módja megvan** (0–8 a súlytáblás
magok, 9 a legközelebbi szomszéd, 10 a bilineáris).

### A `ytResampler` felezőlépése: sima 2×2 doboz-átlag (2026-08-16)

Az előző szakasz nyitva hagyta a `ytResampler` magját. Az első lépés
megvan: a `0x00a43230` (336 bájt) **kettes osztású kicsinyítés**, és a
mag **sima 2×2 doboz-átlag** — se Gauss, se Lanczos, se súlyozás.

#### A célméret

```asm
0x00a43243  mov  eax, dword ptr [ecx + 8]    ; forrás szélesség
0x00a43255  sar  esi, 1                       ; /2
0x00a43257  sar  eax, 1                       ; /2  (magasság)
0x00a43259  cmp  ebp, esi                     ; min(cél_szél, forrás_szél/2)
0x00a4326b  cmp  ebx, eax                     ; min(cél_mag,  forrás_mag/2)
```

#### A mag: négy képpont átlaga, SWAR-ral

Négy szomszédos képpontot olvas (`[ebx]`, `[ebx+4]` — a felső sor;
`[edi]`, `[edi+4]` — az alsó), és a két csatornapárt **külön** összegzi:

```asm
and  eax, 0xff00ff        ; a PÁROS csatornák (R és B)
shr  ecx, 8
and  ecx, 0xff00ff        ; a PÁRATLAN csatornák (G és A)
...                        ; mind a négy képpont hozzáadva
0x00a4332a  shl  ecx, 6    ; (páratlan összeg / 4) << 8
0x00a4332d  shr  eax, 2    ; páros összeg / 4
0x00a43330  xor  eax, ecx  ; a két mező diszjunkt → összefésülés
```

`shl ecx, 6` = `(összeg >> 2) << 8`, tehát **mindkét összeg néggyel
osztódik**. A `xor` azért működik összefésülésként, mert a két mező nem
fed át.

> **Csonkoló osztás, nincs kerekítés.** A `shr` lefelé kerekít; a Picasa
> nem ad hozzá 2-t a felezéshez.

#### Amit ez jelent

1. **Az `unsharp` elmosása doboz-átlagokból épül**, nem Gauss-magból. Ez
   magyarázza, miért csak illesztéssel (σ = 1,0 és ×1,21) tudtuk közelíteni.
2. **A Picasa kicsinyítése lépcsős**: ismételt 2× felezés, nem egyetlen
   tetszőleges arányú újramintavételezés.
3. **Nálunk a kicsinyítés `cv2.INTER_AREA`** (`src/picasapy/cvimage.py:87`).
   Pontosan 2× arányban ez ugyanaz a doboz-átlag — de **kerekít**, míg a
   Picasa csonkol; nem 2-hatvány arányban pedig egészen más utat jár be.

*Bizonyítottsági fok: megerősített* (a teljes aritmetika kiolvasva, a
maszkok és a két eltolás egyértelmű).

~~**Nyitva marad:** a felezés utáni **utolsó** lépés (a nem 2-hatvány
maradék kezelése) — `0x00a42c20` további hívottjai: `0x009e6340`,
`0x009e6df0`, `0x009e75a0`.~~ → **MEGVAN**, ld. a következő szakaszt.

## A `ytResampler` KILENC szűrőmagja — a teljes katalógus (2026-08-16)

**Az átméretező nem egy algoritmus, hanem egy szűrőcsalád**, és a tagot egy
**beállítás** választja ki. Ez zárja le a `ytResampler` magjának kérdését — és
egyben megmagyarázza, honnan jön az `unsharp` elmosása.

### A mód a `ResampleFilter2` beállításból jön — az alapérték 6

A konstruktorban (`0x00a3f490`), ha a hívó `-1`-et ad (mindenki azt adja):

```asm
0x00a3f4a0  mov   dword ptr [esi], 0xce3fb4      ; ytResampler::vftable
0x00a3f507  push  0xce3fa0                        ; "ResampleFilter2"
0x00a3f50c  push  0xc7eafc                        ; "Preferences"
0x00a3f51c  mov   dword ptr [esp + 0x18], 6       ; ← az ALAPÉRTÉK
0x00a3f524  call  0x407a20                        ; beállítás-olvasás
0x00a3f536  mov   dword ptr [0xd9fdf4], eax       ; gyorsítótár (egyszer olvas)
0x00a3f57a  mov   dword ptr [esi + 0x28], ecx     ; [this+0x28] = a mód
```

A `[this+0x28]` tehát a **szűrőmód**, és a hívó felül is írhatja — az
`unsharp` pontosan ezt teszi (`0x0090c4fa`: `mov [esp+0x58], 2`, ami a
`this+0x28`).

### A kilenc mag, ugrótáblából

A súlytáblát a `0x00a3f660` (3811 b) építi, két ugrótáblával, mindkettő a
móddal indexelve:

- **`0xa40550`** — a szűrő **tartósugara** (`0x00a3f6c2`);
- **`0xa40574`** — maga a **súlyfüggvény** (`0x00a3fafc`).

| mód | sugár | a mag | az ág címe | bizonyíték |
|---:|---:|---|---|---|
| 0 | **0,5** | **doboz** (`\|x\| ≤ 0,5 → 1`, egyébként 0) | `0xa3fb03` | `fcomp [0xc7dafc]`=0,5 |
| 1 | **1** | **háromszög** (bilineáris), `1 − \|x\|` | `0xa3fb37` | `fld1; fsubrp`, abs |
| 2 | **2** | **köbös B-spline** (ld. lent) | `0xa3fb82` | a négy szakasz konstansai |
| 3 | **2** | **Mitchell–Netravali, B = C = 0,4** (ld. lent) | `0xa3fc91` | tíz konstans a `0x00a3f5b0`-ban |
| 4 | **3** | **háromlebenyes köbös konvolúció** (ld. lent) | `0xa3fd25` | tíz konstans, `0xcf4180`…`0xcf41c0` |
| 5 | **3** | **Lanczos-3** | `0xa3fdf5` | két `sin` (`0xa3fe43`, `0xa3fe8f`) |
| **6** | **4** | **Lanczos-4** ← **ALAPÉRTELMEZÉS** | `0xa3feed` | két `sin` (`0xa3ff3b`, `0xa3ff87`) |
| 7 | **6** | **Lanczos-6** | `0xa3ffe5` | két `sin` (`0xa4002f`, `0xa4007b`) |
| 8 | **8** | **Lanczos-8** | `0xa400c6` | két `sin` (`0xa40114`, `0xa40164`) |
| 9 | — | affin warp, **legközelebbi szomszéd** | `0x9e6df0` → `0x9e7420` | ld. lent |
| 10 | — | soronkénti gyorsút | `0x9e75a0` → `0xaa5fb0` | — |

A 9-es és a 10-es mód **kikerüli a súlytáblát** (`0x00a42f50`: `cmp eax,9` /
`cmp eax,0xa` → `je 0xa43051`); a 0–8 a `vtbl+0x1c` (`0x00a40a90`) és
`vtbl+0x20` (`0x00a426a0`) virtuális párján át fut.

### A Lanczos-4, betű szerint (a `0xa3feed` ág)

```c
x = fabs(x);                       // 0x49f5c0
if (x > 4.0f) return 0;            // 0xc7e4a4 = 4.0
a = x * PI;                        // 0xcf4168 = 3,14159265358979
s1 = (a == 0) ? 1 : sin(a)/a;      // 0xc285f0 = sin
b = (x * 0.25) * PI;               // 0xc7d9c8 = 0.25 = 1/4
s2 = (b == 0) ? 1 : sin(b)/b;
return s1 * s2;                    // w(x) = sinc(πx) · sinc(πx/4)
```

Ez a **tankönyvi Lanczos, a = 4**. A 7-es és 8-as mód ugyanez `1/6`-tal,
illetve `1/8`-cal.

### A 3-as mód magja — Mitchell–Netravali, B = C = 0,4 (2026-08-17, #871)

```
|x| < 1:     ( (12 − 9B − 6C)|x|³ + (−18 + 12B + 6C)|x|² + (6 − 2B) ) / 6
1 ≤ |x| < 2: ( (−B − 6C)|x|³ + (6B + 30C)|x|² + (−12B − 48C)|x| + (8B + 24C) ) / 6
|x| ≥ 2:     0
```

Az együttható-számoló (`0x00a3f5b0`, 162 b) konstansai **betűre a
Mitchell-készlet**: `6,0` · `1/6` · `12,0` · `18,0` · `9,0` · `8,0` ·
`24,0` · `−12,0` · `48,0` · `30,0`.

**A paraméter mindkét helyre ugyanaz a 0,4** (`0x00a3f691`: `fld
[0xc7c838]` = 0,4, majd `fst [esp+4]` **és** `fstp [esp]`) — vagyis
**B = C = 0,4**, nem a klasszikus 1/3.

| x | 0 | 0,5 | 1 | 1,5 | 2 |
|---|---:|---:|---:|---:|---:|
| **w(x)** | **+0,866667** | +0,541667 | +0,066667 | **−0,041667** | 0 |

**Számszerű kontroll a kódból:** a `w(0)` konstans tagja
`(6 − 2B)/6` = **0,8666667** (`0x00a3f5b0`–`0x00a3f5cc`), és a
súlyok összege **minden fázisban pontosan 1,0**.

> ⭐ **Ezt a magot használja a FORGATÁS** — ld. lent.

### A `RotateImageOperation` a `ytResampler`-t használja, NEM a Skiát (2026-08-17)

> ⚠️ **Helyesbítés a `filterdesc-registry.md` 1195. sorához**, ami azt
> állította, hogy „a mintavételező a Skia… az algoritmust nem kell
> visszafejteni". **Téves.**

A `0x00bcb5e0` (263 b) közvetlen hívottai: `0x009e6da0` · `0x009e6df0` ·
**`0x00a3f490`** (a `ytResampler` konstruktora) · **`0x00a42c20`** (a
diszpécsere) · `0x00425160`. **Skia-hívás nincs köztük.**

A módot **explicit** adja át — nem az alapértelmezettet:

```asm
0x00bcb63e  fld1
0x00bcb640  fcomp dword ptr [esp+0x10]   ; a LÉPTÉK == 1,0 ?
0x00bcb64a  jp   0xbcb653                ;   igen →
0x00bcb64c  mov  ecx, 3                  ;   nem  → 3-as mód (Mitchell)
0x00bcb653  xor  ecx, ecx                ;   igen → 0-s mód (doboz)
0x00bcb659  call 0xa3f490                ; ytResampler(ecx = mód)
```

| a forgatás léptéke | mód | mag |
|---|---:|---|
| **pontosan 1,0** | 0 | **doboz** (nincs mit interpolálni) |
| bármi más | 3 | **Mitchell–Netravali, B = C = 0,4** |

**A 46 statikusan befordított Skia-osztály önmagában nem bizonyíték** —
a Picasa használja a Skiát, de **ezen az útvonalon nem**.

### A 4-es mód magja — háromlebenyes köbös konvolúció (2026-08-17, #871)

`x = |x|`, három szakasz, minden együttható nevezője **11 vagy
209 = 11 × 19**:

| tartomány | súly |
|---|---|
| `0 ≤ x < 1` | `x·( x·(13/11·x − 453/209) − 3/209 ) + 1` |
| `1 ≤ x < 2` | `t·( t·(270/209 − 6/11·t) − 156/209 )`, `t = x − 1` |
| `2 ≤ x < 3` | `u·( u·(1/11·u − 45/209) + 26/209 )`, `u = x − 2` |
| `x ≥ 3` | `0` |

**Két független ellenőrzés igazolja az olvasatot:**

1. **Folytonos** a szakaszhatárokon — `w(1) = w(2) = w(3) = 0` **pontosan**,
   és `w(0) = 1`.
2. **Egységfelbontás** — a súlyok összege **minden fázisban pontosan 1,0**
   (0,00 · 0,25 · 0,50 fázison mérve).

Ha az együtthatók olvasata rossz lenne, egyik sem jönne ki. A mag
**interpoláló**, és **két negatív lebenye** van (`w(1,5) = −0,118`) — tehát
élesít.

### A köbös B-spline (a 2-es mód, amit az `unsharp` használ)

Négy szakasz, `x = |x|` után (`0xa3fb82`–`0xa3fc8c`):

| tartomány | súly | cím |
|---|---|---|
| `x ≥ 2` | 0 | `0xa3fb97` |
| `1 ≤ x < 2` | `(2 − x)³ / 6` | `0xa3fc5b` |
| `0 ≤ x < 1` | `(4 − 6x² + 3x³) / 6` | `0xa3fc23` |
| (negatív ág, szimmetrikusan) | ugyanaz | `0xa3fbeb`, `0xa3fbbb` |

*(konstansok: `0xcf39f8`=3,0 · `0xcf3ec8`=−6,0 · `0xcf3d30`=4,0 ·
`0xc7d9d0`=2,0)*

Ez a **köbös B-spline** — és nem interpoláló: `w(±1) = 1/6 ≠ 0`. **Ezért mos
el 1 : 1 arányban is**, míg a Lanczos ugyanott pontos másolatot adna. Ez volt
a hiányzó láncszem az `unsharp`-nál.

### A mag SZÉLESSÉGE: a `[this+0x30]` szórásszorzó

```asm
0x00a3f728  fcomp dword ptr [ecx + 0x30]     ; a lépték vs. [this+0x30]
0x00a3f736  fld   dword ptr [ecx + 0x30]
0x00a3f739  fadd  qword ptr [0xcf3db0]       ; + 0,001
0x00a3f73f  fdivp st(1)                       ; lépték / ([this+0x30] + 0,001)
0x00a3f745  fld   dword ptr [esp + 0x10]      ; a sugár
0x00a3f74b  fdiv  dword ptr [esp + 0x70]      ; sugár / lépték  ← a mag szélessége
```

A konstruktor `[this+0x30]`-at **1,0**-ra állítja (`0x00a3f553` `fld1`,
`0x00a3f556` `fst [esi+0x30]`). Az `unsharp` hívása viszont a harmadik
argumentumát — a beégetett **`1,5f`**-et — pontosan ide írja
(`0x0090c4e2`–`0x0090c4e8`, `[esp+0x60]` = `this+0x30`). Vagyis az
`unsharp` szűrőmagja **másfélszeresre szélesedik**: köbös B-spline,
2 × 1,5 = **3 képpont tartósugárral**.

Az így kapott 1D súlyok (`w(k) = B₃(k/1,5)`, normálva):

| eltolás | −2 | −1 | 0 | +1 | +2 |
|---|---:|---:|---:|---:|---:|
| súly | 0,0328 | 0,2459 | **0,4426** | 0,2459 | 0,0328 |

Ennek a szórása **σ ≈ 0,87**, nem 1,0 — vagyis a mai `cv2.GaussianBlur(σ=1,0)`
egy hajszállal **túl erősen** mos.

### Amit ez a kör HELYESBÍT

1. A 2-es mód **tényleg létezik és tényleg az `unsharp`-é** — a korábbi
   „2-es mód" megfogalmazás helyes volt, csak a mező nem volt beazonosítva
   (`[this+0x28]`).
2. A `0x00a43230` **2 × 2 doboz-átlaga** nem az `unsharp` magja: az a
   **piramis-felezés**, ami csak ≥ 2× kicsinyítésnél fut (`0x00a42ec9`),
   és utána a `0x00a42c20` **önmagát hívja rekurzívan** kétszeres léptékkel
   (`0xc7d9d0` = 2,0, `0x00a42f35` `call edx` a `vtbl+0x24`-en át, ami maga
   a `0x00a42c20`).

### A 9-es mód: legközelebbi szomszéd

A `0x009e7420` teljes magja **egyetlen képpont kiolvasása**:

```asm
0x009e754d  sar  edx, 0x10          ; forrás x = fixpont >> 16 (CSONKÍTÁS)
0x009e7553  sar  ecx, 0x10          ; forrás y
0x009e756d  mov  ecx, dword ptr [edx + ecx*4]   ; EGY képpont
0x009e7574  mov  dword ptr [edx], ecx
```

A forráskoordináta 16.16 fixpontban lépked (`0x009e7543`, `0x009e7549`), a
mintavétel **képpontközépen** történik (`0xc72150` = 0,5, `0x009e7492`), és a
képen kívülre eső képpont **kimarad** (`jae 0x9e7576`) — a célpuffer ott
érintetlen marad, nem szegélyt ismétel.

*Bizonyítottsági fok: **megerősített*** a mód-táblákra, a Lanczos-4-re, a
B-splinera és a legközelebbi szomszédra (mind utasításszinten kiolvasva) ·
**erős** a 4-es mód pontos alakjára (az együtthatók megvannak, a szakaszok
összeillesztése nincs végigvezetve) és az `unsharp` súlyaira (a
`[this+0x30]` szemantikája levezetett, golden-párral nem mérve).

## A sáv-jelzőknek nincs fogyasztója (2026-08-16)

A „Nyitva 10" pont a `filterdesc.xml` három jelzőjének beépítését kérte.
**Az adat oldala kész, a viselkedés oldala nem.**

### Ami megvan

| réteg | állapot |
|---|---|
| a jelzők a regiszterben | ✅ `render/registry_data.py:41` — `full_res`, `slow`, `resizes` oszlop |
| láncszintű összegzés | ✅ `render/registry.py:156` — `chain_flags(keys) → (full_res, slow, resizes)` |
| a jelentésbe kerül | ✅ `render/chain.py:774`, a `ChainReport.full_res` / `.slow` / `.resizes` mezőben |

Számokban: **19** szűrő `fullres`, **13** `slow`, és **6** `resizes`
(`border`, `cinemascope`, `dropshadow`, `museummatte`, `polaroid`,
`roundededges`).

### Ami HIÁNYZIK

A `render/` csomagon **kívül egyetlen hivatkozás sincs** a három mezőre.
Az előnézet (`app/edit_preview.py:28`) meghívja az `apply_filters`-t, meg is
kapja a `ChainReport`-ot, de a jelzőket **eldobja**.

Három következmény:

1. **19 szűrő csak teljes felbontáson helyes** (`fullres`), és mi mindegyiket
   a kicsinyített előnézeten futtatjuk. A felhasználó ezeknél mást lát az
   előnézetben, mint a mentett képen.
2. **13 szűrő drága** (`slow`), és mind a felület szálán fut. Ezeknél
   akadozik a szerkesztő.
3. **6 szűrő megváltoztatja a kép méretét** (`resizes`), és a downstream
   geometria — vágás, arckeretek, szövegréteg-pozíció — ezt nem veszi
   figyelembe.

> A #382 a jelzőket **adatként** vezette be, és ez helyes volt. A
> viselkedés bekötése külön munka, amit a jelen kör nyitott jegyre tesz.

*Bizonyítottsági fok: megerősített* (a hivatkozások teljes keresése a
`src/picasapy/` alatt; a `full_res`/`.resizes` mezőre a `render/` csomagon
kívül nulla találat).

## A `redeye` és a `retouch` sosem hordoz régiót (2026-08-16)

A „Nyitva 5" pont a `retouch`/`redeye` régió-adatait kereste. **Nincsenek
a `.picasa.ini`-ben** — két, egymástól független bizonyíték zárja le.

### 1. A valós korpusz: 310 bejegyzés, mind paraméter nélküli

859 valós `.picasa.ini`-ben:

| bejegyzés | előfordulás | változat |
|---|---:|---|
| `redeye=1` | **228** | **egyetlen** alak, paraméter nélkül |
| `retouch=1` | **82** | **egyetlen** alak, paraméter nélkül |

Nulla olyan bejegyzés, amiben bármi állna az `1` után.

### 2. A bináris: a lánc-szerializáló LITERÁLKÉNT tartalmazza őket

A `0x00463fd0` (2 495 bájt) a `filters=` lánc szerializálója. A hivatkozott
sztringjei egy helyen:

```
moviestart   rotate(-1)   rotate(%d)   redeye=1;   retouch=1;   picnik=1;
rotate(0)    rect64(      moviestart=  movieend=   rect64(%I64x)
```

**Ez a döntő.** Ugyanaz a függvény, ami a forgatást `rotate(%d)`-vel és a
vágást `rect64(%I64x)`-szel **formázza**, a vörösszemet és a retusálást
**kész sztringként** írja ki: `redeye=1;`, `retouch=1;`. Nincs bennük
formátum-jel, tehát **nincs mit beléjük írni**.

*(A `picnik=1;` ugyanígy literál — összhangban azzal, hogy jelző, nem adat.)*

### Ami ebből következik

A vörösszem-javítás és a retusálás **a képpontokba sül**, az eredeti fájl
pedig a `.picasaoriginals` mappában marad meg. A `redeye=1` / `retouch=1`
csak azt jelzi, **hogy** történt ilyen művelet — nem azt, **hol**.

A régió-adat helye a központi adatbázis (`db3`), lásd **#371**.

> ⚠️ **A PicasaPy `retouch` régió-kiterjesztése** (`ini/retouch.py`) ezért
> **marad PicasaPy-saját**, és a Picasa sosem fogja értelmezni. Ez tudatos
> döntés volt (#148, #445); most már bizonyított, hogy nem is lehetett
> volna másképp.

*Bizonyítottsági fok: megerősített* — a korpusz 310 bejegyzése és a
szerializáló sztring-táblája egymástól függetlenül ugyanazt mondja.

## Az elemzőablak szélessége utasításszinten (2026-08-16)

A `0x009db610` elemzőablakának **szélessége** nyitott kérdés volt: a
dekompilátum `0,9·W`-t adott, a #685 rámpa fehér vége viszont
~`0,94·W`-hez illett volna jobban. **A nyers utasítások eldöntik.**

### A négy határ kiszámítása

A `0x51eb851f` a **100-zal osztás** bűvös konstansa (felső szorzat, majd
`>> 5`):

```asm
0x009db6ac  lea  edx, [ecx + ecx*4]   ; 5·W
0x009db6af  imul ecx, ecx, 0x5f       ; 95·W
0x009db6b7  mul  edx                  ; ×0x51eb851f
0x009db6e5  shr  edi, 5               ; edi = (5·W)/100    = 0,05·W
0x009db6e8  shr  ebx, 5               ; ebx = (95·W)/100   = 0,95·W
0x009db6dc  shr  ecx, 5               ; ecx = (95·H)/100   = 0,95·H
0x009db6df  shr  edx, 5               ; edx = (5·H)/100    = 0,05·H
```

### A sorok: a peremet TÉNYLEG használja

```asm
0x009db6ef  mov  eax, dword ptr [ebp + 4]   ; sorlépés
0x009db6f9  imul eax, edx                    ; × (5·H)/100
0x009db705  lea  esi, [esi + eax*4]          ; a kezdő sor-mutató
0x009db703  sub  ecx, edx                    ; sorok száma = 0,9·H
```

### Az oszlopok: a peremet ELEJTI

```asm
0x009db710  cmp  edi, ebx
0x009db712  mov  eax, esi        ; ← a sor ELEJÉRŐL indul, NEM edi-től
0x009db716  mov  edx, ebx
0x009db718  sub  edx, edi        ; darabszám = (95·W)/100 − (5·W)/100
0x009db720  …                    ; hisztogram, eax += 4, edx−−
```

Az `edi` (`0,05·W`) **kizárólag a darabszámban** szerepel; a mutató a
`0.` oszlopról indul. Ez a Picasa saját, elejtett eltolása — nem
egyszerűsítés a mi oldalunkon.

### A pontos képlet — két KÜLÖN csonkítással

```
oszlopok = (95·W) // 100  −  (5·W) // 100
```

Ez **nem azonos** a `(90·W) // 100`-zal. Például `W = 13`:
`(1235)//100 − (65)//100 = 12 − 0 = 12`, míg `(1170)//100 = 11`. A két
külön egész osztás bizonyos szélességeknél **egy képpontnyi** többletet
ad.

> ✅ A megvalósításunk (`render/ops.py::_analysis_region`) betű szerint ezt
> csinálja: `width * 95 // 100 - width * 5 // 100`.

### Amit ez a rámpa-eltérésről mond

A kód nem hagy szabadságot: **a szélesség pontosan a fenti képlet**. A
#685 rámpa fehér végén mért ~`0,94·W`-nyi hatás tehát **nem** az ablak
szélességéből jön — máshol kell keresni (a keverés, a küszöb vagy a
rámpa saját peremhatása).

*Bizonyítottsági fok: megerősített* (a négy határ kiszámítása és mindkét
ciklus feje nyers utasításszinten).

### A vignetta zónája ELLIPSZIS — az eredeti exportjaival igazolva (2026-08-18)

A `#859` azt állította, hogy a mi vignettánk ellipszist rajzol, míg az
eredetié kör. **A Picasa saját exportjai ezt megcáfolják.**

A privát repó `referencia/vignette/` mappájában **nyolc** eredeti export
van ugyanarról a képről (2560 × 1702 — erősen nem négyzetes, tehát a
kérdés jól mérhető). A próba geometria-független: minden képpontra
kiszámoltuk a **megfigyelt erősítést** (kimenet/bemenet), sugár szerint
rekeszekbe raktuk, és megnéztük a **rekeszen belüli szórást**. Amelyik
geometria a valódi, abban a szórásnak el kell tűnnie.

| export | szórás ELLIPSZIS sugárral | szórás KÖR sugárral |
|---|---|---|
| Vignette default | **0,0485** | 0,0775 |
| Vignette fade mid | **0,0331** | 0,0452 |
| Vignette size max | **0,0407** | 0,0754 |
| Vignette strenght max | **0,0628** | 0,1042 |
| Vignette strenght mid | **0,0514** | 0,0830 |
| Vignette strenght min | **0,0378** | 0,0583 |

Mind a hat informatív exportnál az **ellipszis** magyarázza jobban a
mérést, nagyjából **40 %-kal kisebb szórással**. A mai
`_radius_grid(…, 0.5, 0.5)` (tengelyenként külön normálás) tehát **helyes**.

> **Két export nem informatív:** a `Vignette fade max` és a
> `Vignette size min` **bájtra azonos a bemenettel** — vagyis maximális
> elhalványításnál és minimális méretnél a Picasa vignettája
> **nem csinál semmit**. Ez a paramétertartomány kalibrálásához hasznos.

*Bizonyítottsági fok: **megerősített** — eredeti Picasa-exportokból,
geometria-független módszerrel.*

## A `finetune2` SZERKEZETE — a csúcsfény és az árnyék EGY közös LUT (2026-08-18, #879)

A `native-filter-registry.json` szerint a `finetune2` callbackje a
**`0x008f7ee0`**. Végigolvasva a kompozit szerkezete ez:

```
p_fill = [szűrő+0x28]
h      = max(1 − [szűrő+0x2c], 0,001)        ; 0xcf3da0 / 0xc7999c = 0,001
s      = [szűrő+0x30]
n      = [szűrő+0x3c]                        ; skalár
c      = [szűrő+0x40]                        ; csomagolt szín

1. ha (p_fill != 0):   0x0090ac20(cél, forrás, p_fill, 1,0)      ; DERÍTŐFÉNY
2. ha (h != 1,0 VAGY s != 0):
                       0x0090c430(…, a0, a1, a2)                 ; CSÚCSFÉNY + ÁRNYÉK
3. ha (n != 0):
      ha ((c & 0xffffff) != 0):  0x0090eda0(cél, forrás, c)      ; a színmátrix-alkalmazó
                                 0x0090e9d0(…, n)                ; a hőmérséklet
```

### 1. A derítőfény-hívás AZONOS az önálló `fill`-ével

Az önálló `fill`/`backlight` callback (`0x008f8970`) ugyanezt a magot
ugyanígy hívja: `0x0090ac20(cél, forrás, p1, 1,0)` — ugyanaz a `+0x28`
mező, ugyanaz a `fld1`. **A derítőfény tehát nem lehet a `finetune2`
eltérésének oka**, és a mérésünk is ezt mondja: az önálló `fill` eredeti
exportokhoz mérve 1,20–1,77.

### 2. A csúcsfény és az árnyék EGYETLEN LUT — ez a valódi eltérés

A `0x0090c430` (104 b) három lépés:

```
0x0090c46c  call 0x0090c1e0(a0, a1, a2)   ; 256 × uint16 TÁBLA ÉPÍTÉSE
0x0090c478  call 0x0090be70(kép, tábla)   ; EGYETLEN menetben alkalmazza
```

A táblaépítő (`0x0090c1e0`, 211 b):

```
E     = 1 / a2                                  ; 0x0090c1ec
skála = (a1 != a0) ? 1/(a1 − a0) : 1,0          ; 0x0090c206–0x0090c217
alap  = a0 × 65280                              ; 0xcf4200 = 65280,0 (0x0090c221)
minden i = 0…255:
    v = pow(i/255, E) × 65280                   ; 0xcf4138 = 1/255
    v = (v − alap) × skála
    LUT16[i] = clamp(rint(v), 0, 0xFF00)        ; fistp, 0x0090c27f–0x0090c296
```

Két korábbi pontatlanság javítva (2026-08-18, utasításszintű újraolvasás):
az `alap` **nem** `pow(a0, E)`, hanem maga az `a0` szorozva (a `pow` csak a
ciklusban fut), a kerekítés pedig **`fistp`**, azaz a lebegőpontos
kerekítési mód szerint **a legközelebbi egészre** — nem csonkolás. (A
csonkolás a KIMENETI oldalon van: az alkalmazó `>> 8`-cal veszi ki a nyolc
bitet.)

**A hívó egy irodalmi `fld1`-et is átad** (`0x008f7fa2`), tehát a
kitevő `E = 1/1 = 1` — a görbe **lineáris**, és a művelet egyetlen
**affin fekete-/fehérpont-leképezés**. Ezért illeszkedik a mért
egy-vezérlős modellünk.

### A három argumentum — utasításról utasításra levezetve (2026-08-18)

A verembe pakolás a `0x008f7f7a`-nál kezdődik. Az FPU-verem ekkor
`st0 = s`, `st1 = h`, `st2 = 1,0`:

```asm
0x008f7f7d  fxch st(2)         ; st0 = 1,0   st1 = h   st2 = s
0x008f7f7f  fstp [esp+8]       ; a2 = 1,0                 → GAMMA
0x008f7f83  fstp [esp+4]       ; a1 = h = max(1 − p2, 0,001)  → FEHÉRPONT
0x008f7f87  fstp [esp]         ; a0 = s = p3                  → FEKETEPONT
0x008f7f8a  call 0x90c430
```

Vagyis **`a0` = Árnyékok (p3), `a1` = 1 − Kiemelések (p2), `a2` = 1,0** —
ugyanaz a hozzárendelés, amit a `triple3` burkolója (`0x008f8ce0`) is
használ, és amit a mért egy-vezérlős görbék adnak (0,48-as állásban a mért
meredekség 1,9235/1,9244, a képlet 1,9231).

**A natív oldal a két paramétert NEM vágja** a `filterdesc.xml`-beli
`[0..0.48]` tartományra; az egyetlen védelem a fehérpont `0,001`-es padlója
(`0x008f7f05`, konstans `0xcf3da0`/`0xc7999c`). Élesben ez nem számít: a
859 valódi `.picasa.ini`-ből álló korpusz **mind az 566** Finomhangolás-
láncában a két érték a tartományon belül van (a mért maximum 0,222 és
0,328), ezért a mi `[0..0.48]`-as vágásunk minden valódi láncon no-op.
A tartományon KÍVÜLI viselkedés (degenerált `a1 == a0` → 1,0-s skála,
illetve `a1 < a0` → negatív skála, azaz invertálás) így ma nincs kimérve.

### ⚠️ Amiben a mi megvalósításunk ELTÉRT — JAVÍTVA (2026-08-18, #879)

Mi **két külön menetben** csináltuk (`apply_highlights`, majd
`apply_shadows`). Amíg csak az egyik vezérlő aktív, a kettő egy szinten
belül azonos. Amint **mindkettő** nem nulla, szétmegy:

| h | s | max eltérés | átlag | hány szinten |
|---|---|---|---|---|
| 0,48 | 0,48 | **217** | 29,3 | 69 / 256 |
| 0,30 | 0,40 | 73 | 15,3 | 106 / 256 |
| 0,24 | 0,24 | 26 | 7,6 | 147 / 256 |
| 0,48 | 0 | 1 | 0,24 | 62 / 256 |
| 0 | 0,48 | 1 | 0,23 | 60 / 256 |

**Nem a közbenső 8 bites vágás okozta.** Vágás nélkül, folytonosan
számolva ugyanez az eltérés jön ki (0,48/0,48-nál 216 vs 217) — a vágás
tehát gyakorlatilag no-op, mert az árnyék-lépés a 255-öt fixpontként viszi.
A valódi ok a **kétféle affin leképezés**:

```
mi (két lépés):  ki = ((be/(1−h)) − 255·s) / (1−s)
eredeti (1 LUT): ki = (be − 255·s) / ((1−h) − s)
```

h = s = 0,48-nál a meredekség **3,70 vs 25,0**, a feketepont **63,6 vs
122,4**. Egy vezérlővel a két képlet algebrailag azonos, ezért maradt
rejtve.

**Mennyit számít élesben:** a valódi ini-korpusz 566 Finomhangolás-láncából
**124 (22 %) kompozit** — mindkét csúszka nem nulla. Ezeken a régi modell
legrosszabb esete 17 szint (átlag 5,3), a medián 2 szint, és 15 lánc (a
kompozitok 12 %-a) tévedett legalább 5 szintet.

**A javítás** (`render/tone.py`, `finetune_level_lut`): a két csúszka
EGYETLEN `native_level_lut()` táblát épít, és egy menetben (`>> 8`)
alkalmazódik — ugyanaz a mag, amit a `triple2`/`triple3` már használt. Az
`apply_highlights`/`apply_shadows` innentől ennek az elfajult esete. A
mért egy-vezérlős görbéken ez háromnál javult (0,51→0,35 · 0,61→0,35 ·
0,42→0,32), egynél romlott (0,64→0,87, a `kiemelesek_mid`) — mind a négy az
adott eset JPEG-zajszintje alatt, mert a natív alkalmazó `>>8`-cal csonkít,
mi viszont (szándékosan) nem ditherelünk.

*Bizonyítottsági fok: **megerősített** a szerkezetre, a hívási azonosságra,
a táblaépítőre, a numerikus eltérésre ÉS (2026-08-18, capstone-os
újraolvasás) az `a0`/`a1`/`a2` ↔ (feketepont, fehérpont, gamma)
hozzárendelésre — a veremre pakolás sorrendje utasításról utasításra
levezetve, és a mért egy-vezérlős görbékkel egybevágó.*

⚠️ **Amit ez NEM bizonyít:** a kompozit viselkedésre **nincs mérésünk** —
eredeti Picasa-export, amelyben a Csúcsfények ÉS az Árnyékok is nem nulla,
nem áll rendelkezésre (#951). A javítás a dekompilált képletet követi, a
mérés az egy-vezérlős eseteket fedi.

## A színhőmérséklet TELJES 3×3 mátrix — a binárisból, számokkal (2026-08-18, #956)

A #956 azt kérdezte, van-e kereszt-tag a színhőmérséklet-operátorban.
**A választ nem kell méréssel becsülni: a kódban ott áll.**

### A hőmérséklet-ág teljes kódja (`0x0090e9d0`, 54 bájt)

```asm
0x0090e9d7  fmul qword ptr [0xcf47e0]      ; × 37,0
0x0090e9dd  fadd qword ptr [0xcf4610]      ; + 55,0
0x0090e9eb  fistp dword ptr [esp+0xc]      ; i = (int)(temp·37 + 55)
0x0090e9f3  mov  eax, [eax*4 + 0xc7cf98]   ; k = FEKETETEST_TÁBLA[i]
0x0090e9fd  call 0x90eda0                  ; a SZÍNMÁTRIX-ALKALMAZÓ
```

A `0x0090eda0` az `autocolor` mátrix-alkalmazója (#759): felépíti az
`A = M · diag(g) · M⁻¹` mátrixot, és **teljes 3×3-ként** alkalmazza.
Vagyis a kérdés eldőlt a hívásnál: **a művelet mátrix, a kereszt-tag a
szerkezetéből következik**, nem statisztikai lelet.

### A tényleges mátrixok, a bináris tábláját behelyettesítve

`M`, `L` és `g` a #759 szerint; `k` a `0x00c7cf98`-as feketetest-tábla
`i`-edik bejegyzése:

| temp | i | k (R,G,B) | L | max\|átlón kívül\| / átló |
|---:|---:|---|---:|---:|
| −1,0 | 18 | (255, 173, 94) | 189 | **0,1176** |
| −0,8 | 25 | (255, 196, 137) | 207 | 0,0843 |
| −0,5 | 36 | (255, 221, 190) | 227 | 0,0459 |
| 0,0 | 55 | (255, 249, 253) | 251 | **0,0063** |
| +0,5 | 74 | (221, 230, 255) | 230 | 0,0201 |
| +0,8 | 85 | (208, 222, 255) | 221 | 0,0285 |
| +1,0 | 92 | (202, 218, 255) | 217 | 0,0323 |

Példa a hideg végről (`temp = −1,0`, sorfolytonosan):

```
A = [ 0,8074   0,0184  −0,2134
      0,0044   1,0391   0,0863
     −0,0222   0,1394   1,8144 ]
```

**A kereszt-tag a hideg végen a legnagyobb (11,8 %), a meleg végen 3,2 %,
és `temp = 0`-nál sem nulla (0,63 %)** — mert a `temp = 0` bejegyzés
(255, 249, 253) maga sem semleges.

### Mit jelent ez a modellünkre

A mai `apply_color_temperature` (`tone.py:94`) **csatornánkénti erősítés**
csomópont-interpolációval. Ez **szerkezetileg** nem tud kereszt-tagot
előállítani — nem hangolási kérdés.

Ugyanezért **érvénytelen az a mérés, amivel a natív modellt elvetettük**:
csatornánkénti mért görbékhez hasonlított, amelyek a kereszt-tagot maguk
sem tudják ábrázolni.

> ⚠️ **Helyesbítés a saját, egy nappal korábbi számunkhoz.** Egy
> statisztikai illesztés (teljes 3×3 vs. csak-átlós, a golden párokon)
> a hideg végre **0,292**-es átlón kívüli arányt adott. A binárisból
> számolt valódi érték **0,1176** — a lineáris illesztés a modell
> nem-linearitását is az átlón kívüli tagokba nyelte, és ezzel
> **túlbecsülte** azokat. A trend (hideg ≫ meleg) mindkét úton
> ugyanaz, de a **szám a binárisból való**.

*Bizonyítottsági fok: **megerősített** — a hívási lánc a
diszasszemblátumból, a mátrixok a bináris tábláját behelyettesítve a
#759-ben már igazolt képletbe.*

## A `dir_tint` (Graduated Tint) visszafejtve (2026-08-16, #874)

**Az átmenet FORGATHATÓ, fokban megadott irányú** — nem függőleges. Ez a
`dir_tint` ROSSZ verdiktjének (9,45 alap / **49,41 max**) a fő oka.

### A callback (`0x008f9880`, 306 b) paraméter-térképe

| mező | jelentés | cím |
|---|---|---|
| `[szűrő+0x28]` | **Feather** (0. csúszka), **minimum 0,001** | `0x008f990b`–`0x008f9929` (küszöb `0xcf3db0` = 0,001, pótérték `0xc7999c` = 0,001) |
| `[szűrő+0x2c]` | **Shade** (1. csúszka) | `0x008f9958` |
| `[szűrő+0x50]` | a szín (csomagolt dword) | `0x008f98dd` |
| `[szűrő+0xc4]` | **az irány, FOKBAN**; `-1` → 0 | `0x008f992d`–`0x008f9938` |
| `[ebp+0x10]+0x1c` | a kép **tájolása** — az irány ehhez képest relatív | `0x008f993f` |

```asm
0x008f9942  test al, 1                 ; az irány PARITÁSA választ:
0x008f9946  fld  dword ptr [esp+0x18]  ;   páratlan → az y a középpont
0x008f994c  fld  dword ptr [esp+0x14]  ;   páros    → az x
0x008f9968  fsub qword ptr [0xc72150]  ; − 0,5
0x008f9975  fmul qword ptr [0xcf3ed8]  ; × 30,0
0x008f998b  fld1 / fsubrp              ; a magba 1 − Shade megy
0x008f99a3  call 0x90f470              ; a munkafüggvény
```

### A munkafüggvény (`0x0090f470`, 1151 b)

```asm
0x0090f543  fmul qword ptr [0xcf48d0]  ; szög × π/180  → az irány FOKBAN
0x0090f557  call 0xc285f0              ; sin
0x0090f56f  call 0xc29d20              ; cos
0x0090f5a5  fld  qword ptr [0xcf3cb0]  ; 65536,0 → 16.16 fixpontos lépésvektor
0x0090f5c3  test ebx, ebx / xchg        ; páratlan negyed → x ↔ y csere
0x0090f5d4  and  ecx, 3 / neg           ; negyed szerinti előjelváltás
0x0090f623  call 0x90ecd0               ; a tónusgörbe-LUT feltöltése
```

### A tónusgörbe-LUT (`0x0090ecd0`, 200 b) — 256 × `uint16`

```asm
0x0090ecd0  fld  dword ptr [0xcf47d8]   ; a görbeparaméter felső korlátja 99,9
0x0090ece9  fld  dword ptr [0xcf47d4]   ;   alsó korlátja 0,01
0x0090ed2b  fmul qword ptr [0xcf4138]   ; i × 1/255
0x0090ed3c  call 0x90ec40                ; az átmenet-görbe
0x0090ed41  fmul qword ptr [0xcf3b78]   ; × 65535,0
0x0090ed53  or   eax, 0xc00              ; CSONKÍTÁS nulla felé
0x0090ed80  mov  word ptr [edi + esi*2], ax
```

A képpont-ciklus a LUT **felső bájtját** olvassa, csatornánként, a
**forrásérték** szerint indexelve, majd **szoroz** a színnel:

```asm
0x0090f7da  movzx esi, byte ptr [ecx]                  ; forrás B
0x0090f7e1  movzx esi, byte ptr [esp + esi*2 + 0x1c9]  ; LUT16[B] felső bájtja
0x0090f810  movzx ebx, byte ptr [esp + 0x3ea]          ; a szín egy bájtja
0x0090f818  imul  ebx, ecx                              ; SZORZÁS
```

Vagyis a `dir_tint` — a `radtint`-hez hasonlóan — **szorzó** színezés, nem
lineáris keverés a szín felé.

### Az átmenet-görbe (`0x0090ec40`, 134 b) — MEGFEJTVE (2026-08-18)

**A két „nem azonosított" segédfüggvény UGYANAZ: a négyzetgyök.**
A `0x0049fe60` mindössze egy `float`-os burkolat — betölti a verem-
argumentumot és továbbadja a `0x00c0b310`-nek (`0x0049fe6c`), ami az FPU
`sqrt`-intrinsic. Ezzel a görbe teljesen kiolvasható.

Jelölje `x` a bemenetet (0…1) és `p` a paramétert:

```
ha p == 1,0        →  y = x                     (azonosság, 0x0090ec50)

egyébként:
    A = sqrt(1/p)                               ; 0x0090ec5c–0x0090ec5e
    B = sqrt(p)                                 ; 0x0090ec6b–0x0090ec6e
    y = ( 1 / ( (1−x)·(B−A) + A ) − A ) / (B − A)
```

**A képlet önmagát hitelesíti.** Mivel `A·B = 1` azonosan, a végpontok
pontosan `y(0) = 0` és `y(1) = 1` — a görbe normalizált. És `p = 1`-nél
`B − A = 0`, vagyis **nullával osztás lenne**: pontosan ezért van a
kódban külön azonosság-ág erre az egy értékre. Két független jel mondja
ugyanazt.

Ez a klasszikus **reciprok (hiperbolikus) torzítógörbe**: `p > 1` az
egyik vég felé húzza a tónusokat, `p < 1` a másik felé, `p = 1` semleges.

### A paraméter útja: a Shade csúszkából

```
callback (0x008f998b):  arg = 1 − Shade
munkafüggvény (0x0090f470):
    q = clamp(arg, 0,01, 99,9)                  ; 0x0090f484–0x0090f4cd
    p = 1 / q                                   ; 0x0090f5e7–0x0090f5f8
LUT-építő (0x0090ecd0):  y = görbe(i/255, p) × 65535, csonkítva
```

Tehát **`p = 1 / clamp(1 − Shade, 0,01, 99,9)`**. Shade = 0-nál `p = 1`,
azaz **azonosság** (nincs tónusformálás); Shade → 1-nél `p → 100`, azaz
maximálisan torzított átmenet. A `0,01`-es padló az, ami a `p`-t 100-nál
megfogja.

*Bizonyítottsági fok: megerősített* a paraméter-térképre, a fokos szögre, a
`Feather` 0,001-es padlójára, az `1 − Shade`-re, a `× 30`-as
középpont-skálára, a LUT felépítésére, a szorzó színezésre **és
(2026-08-18) a görbe alakjára** · **erős** a negyed-kezelés pontos
szemantikájára.

## A három „automatikus" szűrő HÁROM külön algoritmus (2026-08-17)

Független újraolvasás a callbackekből — a mai megvalósításunk megerősítve.

| szűrő | callback | mit hív | keverés | `CarefulEnhance` |
|---|---|---|---|---|
| **`enhance`** | `0x008f8840` (147 b) | `0x009db610` | **−1,0f → 0,30** | a **beállításból** |
| **`autocontrast`** | `0x008f89d0` (68 b) | `0x009db610` | **1,0** (`fld1`, `0x008f89fd`) | **fixen 0** (`push 0`, `0x008f8a03`) |
| **`autolight`** | `0x008f80c0` (468 b) | `0x00a4b960` + `0x00a4bfd0` | — | — |

**Az `enhance` és az `autocontrast` UGYANAZ a szinthúzó, két
paraméterrel.** A különbség emberi nyelven:

- **`enhance`** a csatornánkénti vágópontokat csak **30 %-ban** közelíti a
  közös értékhez → a **színöntetet is korrigálja**;
- **`autocontrast`** **100 %-ban** közös vágópontot használ → **csak a
  kontrasztot húzza szét, a fehéregyensúlyt nem mozdítja**.

**Az `autolight` ezzel szemben teljesen más út:** a hisztogram-felvevőn
(`0x00a4b960`) keresztül dolgozik, nem a szinthúzón.

> ⚠️ **Ne vonj össze közös segédfüggvényt a három alá.** A `0x009db610`
> közös az első kettőnek, de a paraméterezés adja a jelentést; az
> `autolight` pedig más kódúton van.

*Bizonyítottsági fok: megerősített* (mindhárom callback hívási listája az
indexből, a két konstans utasításszinten).

## A szűrők TÉNYLEGES gyakorisága éles gyűjteményben (2026-08-17, #484)

Eddig a mérőszett ΔE-értékei rangsoroltak. **A másik tényező is megvan:**
mi fordul elő valódi `.picasa.ini`-kben.

Forrás: `referencia/ini-korpusz/korpusz.txt` (privát repó) — **859
`.picasa.ini` fájl**, ebből **317 tartalmaz `filters=` sort**, összesen
**9147 lánc-tag, 28 féle szűrő**. A feldolgozás a saját
`canonical_filter_name` és `effective_param_count` függvényünkkel futott.

| szűrő | előfordulás | | szűrő | előfordulás |
|---|---:|---|---|---:|
| **`enhance`** | **3045** | | `autocolor` | 54 |
| **`autolight`** | **2612** | | `unsharp2` | 27 |
| **`fill`** | **1089** | | `Boost` | 22 |
| **`crop64`** | **801** | | `radblur` | 18 |
| **`finetune2`** | **561** | | `sepia` | 14 |
| `redeye` | 228 | | `bw` | 10 |
| `Vignette` | 219 | | `dir_tint` | 10 |
| `warm` | 118 | | `Lomo` | 6 |
| `sat` | 110 | | `HDR`, `glow2` | 4, 4 |
| `tilt` | 102 | | `Holga`, `moviestart`, `movieend`, `tint` | 2 |
| `retouch` | 82 | | `Cinemascope`, `CrossProcess`, `Sixties` | 1 |

**Öt szűrő adja a tagok 88 %-át**: `enhance` · `autolight` · `fill` ·
`crop64` · `finetune2`.

### Két negatív eredmény ugyanebből a mérésből

| kérdés | eredmény |
|---|---|
| hány tag visel **fölös paramétert**? | **0** a 9147-ből |
| hány tag **nem kanonikus** írásmódú? | **0** |

Vagyis a Picasa a saját maga írta fájlokban **mindig** pontos
paraméterszámot és kanonikus nevet használ. A `filter_registry.py`
megengedő olvasása **elméleti** védelem (kézzel szerkesztett ini ellen),
nem napi szükséglet — és a #910-es render-hiba éles fájlon nem sül el.

### Amit a rangsorban átrendez

- **`finetune2`**: 561 előfordulás **és** 55,94 ΔE — a gyűjtemény
  legnagyobb tényleges hatású render-hibája (#879).
- A `#880` tíz „nem megvalósított" effektjéből a korpuszban **egyik sem**
  fordul elő.
- A `neon` (113,89 ΔE, #878) szintén **nulla** előfordulású.

> ⚠️ **Korlát:** a korpusz **egy** felhasználó gyűjteménye, tehát az ő
> szokásait tükrözi. Más felhasználónál más lehet — de ez az egyetlen
> **mért** adatunk, és sokkal jobb a becslésnél.

*Bizonyítottsági fok: megerősített* (teljes korpusz, gépi feldolgozás).

## A `finetune2` színhőmérséklete: feketetest-tábla + az `autocolor` mátrixa (2026-08-17, #879)

**A hőmérséklet-csúszka nem csatorna-szorzókat állít, hanem kiválaszt egy
megvilágítás-színt, és a kép azt semlegesíti** — ugyanazzal a
színmátrixszal, amit az `autocolor` használ.

### A képlet

```c
// 0x0090e9d0 (54 b) — a finetune2 hőmérséklet-ága
i = (int)(temp * 37.0 + 55.0);        // 0xcf47e0 = 37,0 · 0xcf4610 = 55,0
k = TABLA[i];                          // 0x00c7cf98, csomagolt 0x00RRGGBB
0x0090eda0(dst, src, k);               // ← AZ AUTOCOLOR ALKALMAZÓJA (#759)
```

A `0x0090eda0` teljes leírása fent, „Az `autocolor` MÁTRIX-ÉPÍTŐJE
VISSZAFEJTVE" szakaszban: `L = (77·kR + 151·kG + 28·kB) >> 8`,
`g = (M⁻¹·(L,L,L)) ⊘ (M⁻¹·k)`, `A = M · diag(g) · M⁻¹`.

### A tábla — feketetest-sugárzás Kelvinben

| index | RGB | Kelvin |
|---:|---|---:|
| 0 | (255, 56, 0) | 1000 K |
| 18 | (255, 173, 94) | **2800 K** ← a csúszka alsó vége |
| 36 | (255, 221, 190) | 4600 K |
| **55** | **(255, 249, 253)** | **6500 K — a csúszka KÖZEPE** |
| 70 | (227, 233, 255) | 8000 K |
| 92 | (202, 218, 255) | **10200 K** ← a csúszka felső vége |

**`Kelvin = 1000 + 100·i`**, tehát a csúszka jelentése:

```
Kelvin = 6500 + 3700 · temp        temp ∈ [−1 … 1]  →  2800 K … 10200 K
```

⚠️ **A `temp = 0` NEM azonosság:** az 55. bejegyzés (255, 249, 253)
minimálisan meleg, tehát a mátrix egy hajszálnyit hűt.

### A neutrális pipetta UGYANEZ a gépezet

A callback (`0x008f7ee0`) **két egymás utáni** mátrix-menetet futtat:

```asm
0x008f7fe8  test edi, 0xffffff   ; a p4 (pipettával vett szín) nem nulla?
0x008f7ffd  call 0x90eda0        ; 1. menet: a KIVÁLASZTOTT szín semlegesítése
0x008f8010  call 0x90e9d0        ; 2. menet: a hőmérséklet-táblából vett szín
```

A `finetune` (v1) ugyanígy épül, csak a `0x0090ea10`-et hívja a
`0x0090e9d0` helyett.

*Bizonyítottsági fok: megerősített* a hőmérséklet-ágra, a két konstansra,
a tábla tartalmára és a `0x0090eda0` azonosságára · **erős** a
Kelvin-leképezésre (két független illeszkedés: 1000 K és 6500 K).

### A tábla TELJESEN kiolvasva — és a modell KIMÉRVE (2026-08-18, #879)

A `0x00c7cf98` tábla mind a 130 kiolvasott bejegyzése egybevág a fenti hat
mintával, és a `Kelvin = 1000 + 100·i` leképezéssel: `i = 0` → (255, 56, 0),
`i = 55` → (255, 249, 253), `i = 92` → (202, 218, 255). A csúszka indexe
`i = (int)(temp·37 + 55)`, **nulla felé csonkolva** (C-cast), tehát
`temp = −1 → i = 18` (2800 K) és `temp = +1 → i = 92` (10200 K).

**A modellt lemértük a mért színhőmérséklet-görbéken** (a valódi Picasa
kimenetéből desztillált `measured_luts.json`, hat csúszkaállás):

| eset | temp | JPEG-zajszint | mai (csatorna-szorzós) | natív (tábla + mátrix) |
|---|---:|---:|---:|---:|
| `szinho_0` | −1,0 | 4,43 | **2,26** | 2,90 |
| `szinho_10` | −0,8 | 2,63 | **1,12** | 1,67 |
| `szinho_25` | −0,5 | 1,27 | **0,48** | 1,15 |
| `szinho_75` | +0,5 | 0,88 | 0,38 | **0,36** |
| `szinho_90` | +0,8 | 1,05 | **0,54** | 0,79 |
| `szinho_100` | +1,0 | 1,11 | **0,54** | 0,62 |

**A natív modell hatból ötben rosszabb — ezért NEM cseréltük le.** Két
dolgot viszont ki kell mondani, mert a szám önmagában félrevezet:

1. **Mindkét modell a zajszint alatt van** mind a hat esetben, tehát ez a
   mérés egyiket sem cáfolja.
2. **Ez a mérés szerkezetileg vak a különbségre.** A `measured_luts.json`
   csatornánkénti görbéket tárol (bemeneti szint → átlagos kimeneti szint
   ugyanazon a csatornán). Egy 3×3-as mátrix KERESZT-TAGJAI ebbe a
   formába nem férnek bele — a mérés csak a diagonálist látja. Ráadásul a
   mai csatorna-szorzóink ÉPPEN EZEKRE a görbékre lettek illesztve, tehát a
   saját tanulóadatukon versenyeznek.

**Amíg nincs olyan mérés, ami a kereszt-tagokat is látja** (eredeti
Picasa-export erős hőmérséklet-állással, KÉPPONTONKÉNT összevetve, nem
csatorna-LUT-ként), a csere sem nem igazolható, sem nem cáfolható. A
korábbi kör ezt a Planck-sugárzásból SZÁMOLT táblával próbálta — a mostani
mérés a binárisból olvasott, VALÓDI táblával fut, és ugyanoda jut. A hiányzó
mérés a **#956** jegy tárgya.

## A `finetune2` hőmérséklet-tengelye — KÉPPONTONKÉNTI MÉRÉS (2026-08-21, F1)

A #956 azt kérte, ami eddig hiányzott: **képpontonkénti** összevetés, nem
csatorna-LUT. Megvan, és **egyértelmű**.

### A mérőanyag — és miért ez a legjobb, amink valaha volt

`referencia/finomhangolas/original.jpg` + `referencia/szinhomerseklet/`
hét exportja (`percent 0…100`), mind **2560 × 1702**.

> **A `percent 50` BITRE AZONOS az `original.jpg`-vel** (átlag |Δ| = 0,000,
> max = 0). Vagyis a `temp = 0` állás a Picasánál **valódi no-op**, és
> ezért ennek a készletnek **NINCS JPEG-zajszintje** — minden eltérés
> tisztán a modell hibája.

Ez lényegesen erősebb alap, mint a #879 mérése, ahol a 4,43-as
„JPEG-zajszint" mindkét modellt elnyelte.

### Az eredmény — a natív modell 6/6-ban jobb

| percent | temp | MAI (csatorna-szorzó) | **NATÍV** (tábla + mátrix) | javulás |
|---:|---:|---:|---:|---:|
| 0 | −1,0 | 5,082 | **1,230** | **4,1×** |
| 10 | −0,8 | 2,831 | **1,005** | 2,8× |
| 25 | −0,5 | 1,328 | **1,065** | 1,25× |
| 75 | +0,5 | 0,909 | **0,696** | 1,3× |
| 90 | +0,8 | 1,113 | **0,801** | 1,4× |
| 100 | +1,0 | 1,170 | **0,707** | 1,65× |

*(átlagos abszolút csatornaeltérés, 2560 × 1702 × 3 képpontcsatornán)*

**Ez az ellenkezője a #879 eredményének** („hatból ötben rosszabb") — és
a #956 pontosan megjósolta, miért: az akkori mérés **csatorna-LUT-okon**
futott, amelyek **szerkezetileg vakok** a 3×3-as mátrix kereszt-tagjaira,
márpedig épp azok a különbség.

### A mérés menete (reprodukálható)

1. A feketetest-tábla kiolvasva a binárisból (`0x00c7cf98`, 130 elem,
   csomagolt `0x00RRGGBB`). Ellenőrzés: `i=18 → (255,173,94)`,
   `i=55 → (255,249,253)`, `i=92 → (202,218,255)` — egyezik a fenti
   táblázattal.
2. `temp = (percent − 50) / 50`, `i = (int)(temp·37 + 55)`.
3. A natív mátrix a **saját** `render/autocolor_matrix.py`
   `autocolor_matrix_16_16(kR, kG, kB)`-jével, alkalmazva
   `apply_autocolor_matrix`-szal — tehát nem külön, ad-hoc kód.
4. A mai modell: `render/tone.py` `apply_color_temperature`.

### Egy melléklelet: a tábla-index ±1 bizonytalansága

A legjobban illeszkedő index állásonként:

| percent | csonkolt `i` | a spec táblája | a MÉRT legjobb |
|---:|---:|---:|---:|
| 0 | 18 | 18 | **18** |
| 10 | 25 | 25 | **25** |
| 25 | 36 | 36 | **37** |
| 75 | 73 | 74 | **74** |
| 90 | 84 | 85 | **85** |
| 100 | 92 | 92 | **92** |

A két végpont (±1,0) **mindhárom oszlopban egyezik**. A köztes
állásoknál ±1 az eltérés — a legvalószínűbb ok, hogy a `percent`
címkék a **csúszka-pozíciók** a tulajdonos jelölésével, és a tényleges
`temp` nem pontosan `(p−50)/50`. **Az exportokhoz nincs `.picasa.ini`**,
így a valódi paraméter nem visszakereshető. *A mérés következtetését ez
nem érinti: a natív modell mind a hat állásban nyer, bármelyik szomszédos
indexszel.*

**Bizonyítottsági fok: megerősített** — zajszint nélküli, képpontonkénti
mérés, hat állásban, a saját kódunk két ágával.

## A `TiledImageMask` peremszabálya — MEGVAN, és NEM beégetett kód (2026-08-24)

A lap eddig azt mondta a `Comicize`/`FocalZoom`/`PicnikFocalPixelate`-ról,
hogy *„egyedül a mintavételezés perem-/interpolációs szabálya vár
golden-összevetésre"*. A `Comicize` felére ez **már nem igaz**.

### A maszk TELJES paraméterkészlete — a binárisból

A `glimmer::TiledImageMask` paraméterolvasója (`0x00bba2e0`, 481 b) tizenkét
nevesített paramétert vesz át, mindegyiket saját mezőbe:

| paraméter | mező | | paraméter | mező |
|---|---|---|---|---|
| `tileWidth` | `+0x18` | | `paddingRight` | `+0x48` |
| `tileHeight` | `+0x20` | | `paddingBottom` | `+0x50` |
| `scaleWidth` | `+0x28` | | `offsetX` | `+0x58` |
| `scaleHeight` | `+0x30` | | `offsetY` | `+0x60` |
| `paddingLeft` | `+0x38` | | `alphaMin` | `+0x68` |
| `paddingTop` | `+0x40` | | `alphaMax` | `+0x70` |

⇒ **A perem viselkedése paraméter, nem beégetett szabály.** Nincs
`clamp`/`wrap`/`mirror` nevű sztring a binárisban — mert nincs is ilyen
üzemmód: négy oldalankénti `padding` van helyette.

### Amit a `Comicize` ténylegesen kér — `filterdesc.xml` 781–782. sor

```xml
<Variable id="_nDotSize" val="{Math.round(imagewidth/70)+1}"/>

<imageOperations:TiledImageMask id="_mskColorSpots1"
    tileWidth="{_nDotSize}" tileHeight="{_nDotSize}" alphaMin="0.0"
    width="{imagewidth}" height="{imageheight}"/>

<imageOperations:TiledImageMask id="_mskColorSpots2"
    tileWidth="{_nDotSize}" tileHeight="{_nDotSize}" alphaMin="0.0"
    width="{imagewidth}" height="{imageheight}"
    offsetX="{_nDotSize/2}" offsetY="{_nDotSize/2}"/>
```

**Egyik maszk sem ad meg SEMMILYEN `padding` értéket** ⇒ mind a négy
alapértelmezett (0).

> **A peremszabály tehát:** a csemperács **pontosan a kép méretére** van
> kifeszítve (`width`/`height` = a kép mérete), a `(0,0)` + `offset` pontból
> indul, és **nincs semmilyen szegély-kiterjesztés**. A jobb és alsó szélen
> részlegesen kilógó csempéket egyszerűen **levágja a kép határa**. Nincs
> tükrözés, nincs ismétlés, nincs szélső képpont-nyújtás.

A második fázis fél csempével eltolt — és a **pixelesítés is**: a 793. sor
`PixelateImageOperation`-je eltolás nélküli, a 807. soré viszont
`offsetX = offsetY = _nDotSize/2`. A két ág tehát **a maszkban ÉS a
pixelesítésben is** el van tolva.

`alphaMin="0.0"` kimondott; az `alphaMax` hiányzik → alapértelmezett.

### ⚠️ Ami EZUTÁN is nyitva marad: a `FocalZoom` sugaras elmosásának pereme

A `FocalZoom` a leíró szerint **nem** nagyítás, hanem
`RadialBlurImageOperation` egy `CircularGradientImageMask` alatt
(`filterdesc.xml` 888. sortól) — ezt a megvalósításunk helyesen követi
(`src/picasapy/render/focal.py`, halmozott nagyító-menetek).

A halmozás **perem-módja** viszont a natív magban (`0xbcf4b0`) van, nem a
leíróban. Nálunk ma `cv2.BORDER_REPLICATE` (`focal.py:141`) — **dokumentált
feltevés**, nem mérés. Ez marad nyitva.

*Bizonyítottsági fok: a paraméterkészlet és a mezőeltolások **megerősítettek**
(diszasszemblálva); a `Comicize` peremszabálya **megerősített** (a szállított
`filterdesc.xml` közvetlen olvasása). A `FocalZoom` perem-módja
**feltételes** — nincs se dekompilálva, se mérve.*

### A `FocalZoom` perem-módja — LEZÁRVA MÉRÉSSEL: NEM SZÁMÍT (2026-08-24)

Az előző szakasz nyitva hagyta a `FocalZoom` halmozott nagyító-meneteinek
perem-módját, azzal, hogy a natív magban (`0xbcf4b0`) van. **Nem kellett
visszafejteni: a kérdés geometriailag el van döntve, és mérés igazolja.**

#### A geometriai érv

A halmozás **kizárólag nagyít** (`zoom ≥ 1`) egy `C` fókuszpont körül. Egy
`p` kimeneti képponthoz tartozó forráspont `C + (p − C) / zoom`, ami mindig
**`C` és `p` között** van. Ha tehát `C` és `p` is a képen belül van, a minta
is belül esik ⇒ **a perem-mód sosem kerül szóba**.

#### A mérés — 240 × 360 zajkép, négy perem-mód, négy fókuszpont, három erősség

Maximális |Δ| a `BORDER_REPLICATE`-hez képest:

| fókuszpont | Impact | `CONSTANT(0)` | `REFLECT` | `WRAP` |
|---|---|---|---|---|
| (0,5 · 0,5) | 10 / 50 / 100 | **0,000000** | **0,000000** | **0,000000** |
| (0,02 · 0,02) | 10 / 50 / 100 | **0,000000** | **0,000000** | **0,000000** |
| (0,98 · 0,5) | 10 / 50 / 100 | **0,000000** | **0,000000** | **0,000000** |
| **(0,0 · 1,0)** — pontosan a sarokban | 10 | 5,60 | **0,00** | 4,80 |
| | 50 | 25,43 | **0,00** | 20,70 |
| | 100 | 43,97 | **0,00** | 30,30 |

⇒ **A képen belüli fókuszpontra a négy mód bitre azonos kimenetet ad.**
Csak akkor tér el bármi, ha a fókuszpont **pontosan a képhatáron** ül (ott
az interpoláció fél képponttal kilóg) — és **ott is egyezik a `REPLICATE` a
`REFLECT`-tel**.

> **A mai `cv2.BORDER_REPLICATE` (`src/picasapy/render/focal.py:141`)
> helyes, és a választás nem befolyásolja az eredményt.** A korábbi
> „dokumentált feltevés" megjelölés levehető.

#### Mellékleletek: a natív mag IGAZOLJA a két képletünket

A `0x00bcf4b0` (1238 b) eleje:

```asm
0x00bcf4d2  mov  eax, 0x51eb851f      ; magic: osztás 200-zal
0x00bcf4d7  mul  edx                  ;  edx = szélesség * Impact
0x00bcf4dd  shr  edi, 6               ;  -> edi = szélesség · Impact / 200
0x00bcf4e0  lea  eax, [ecx + 5]       ;  Impact + 5
0x00bcf4e3  cmp  eax, 0x1e            ;  30
0x00bcf4f5  ja   0xbcf4fb             ;  -> min(Impact + 5, 30)
```

Ez **bitre egyezik** a mi `zoom_max_offset` (`floor(width · Impact / 200)`)
és `zoom_sample_count` (`min(trunc(Impact) + 5, 30)`) függvényeinkkel
(`focal.py:80–87`). A #570 ezeket helyesen mérte ki.

*Bizonyítottsági fok: **megerősített** — a perem-mód közömbössége mérve (12
esetből 9-ben bitre azonos, a maradék háromban a `REFLECT` is azonos), a két
képlet a natív magból diszasszemblálva.*

### A `TiledImageMask` beégetett alapértékei — a KÖTŐ függvény (2026-08-25)

A `#785` nyitott pontja: *„a 12 attribútum megvan, a beégetett alapértékek
nincsenek."* A kötő függvény megvan, az **értékek** megvannak, a
**hozzárendelés** nem.

#### Hol vannak: vtable 7. rekesz — `0x00bba580` (234 b)

Ugyanaz a szerkezeti hely, mint a `CircularGradientImageMask`-nál
(`0x00bcfe10`): az attribútum-**olvasó** az 5. rekeszben (`0x00bba2e0`),
a **kötő** — ami a tartalékokat verembe állítja — a 7.-ben.

```asm
0x00bba589  fld  dword ptr [0xc7dbc4]   ; = 0.8f
0x00bba590  fst  [esp+0x18]             ;  -> 1. float rekesz
0x00bba595  fstp [esp+0x20]             ;  -> 2. float rekesz
0x00bba59b  fldz                        ; 0.0
0x00bba5a1  fst  [esp+0x38]             ;  -> 3.
0x00bba5a5  fst  [esp+0x3c]             ;  -> 4.
0x00bba5ac  fstp [esp+0x40]             ;  -> 5.
0x00bba5b1  fld1                        ; 1.0
0x00bba5b7  fstp [esp+0x48]             ;  -> 6.
;  + nyolc EGÉSZ nulla ([esp+0x14] … [esp+0x38])
0x00bba5b3  lea  esi, [esp+0x14]        ;  a blokk bázisa
```

**A hat lebegőpontos tartalék, sorrendben: `0.8`, `0.8`, `0.0`, `0.0`,
`0.0`, `1.0`.**

#### Melyik attribútum fut tartalékon — a `Comicize`-nál HÉT

A leíró (`filterdesc.xml` 781–782) ezeket **megadja**: `tileWidth`,
`tileHeight`, `alphaMin`, `offsetX`, `offsetY`, `width`, `height`.

⇒ **Tartalékon fut:** `scaleWidth`, `scaleHeight`, `paddingLeft`,
`paddingTop`, `paddingRight`, `paddingBottom`, `alphaMax` — **hét darab**.

#### ⚠️ Amit NEM sikerült: a hozzárendelés

**Hét** tartalékon futó attribútum áll szemben **hat** lebegőpontos
tartalékkal ⇒ a blokk **nem 1:1** a nem beállított attribútumokkal, tehát a
sorrendből nem lehet leolvasni, melyik melyiké.

A `CircularGradientImageMask`-nál volt keresztellenőrzés (a `FocalZoom`
**fölöslegesen** kiírta az `innerAlpha="0"` / `outerAlpha="1"` értékeket,
épp a tartalékokat) — **itt nincs ilyen**: a `Comicize` egyetlen redundáns
attribútumot sem ad meg.

**Az is kizárva, hogy a konstansból következtessünk:** a `[0xc7dbc4]`
(`0.8f`) **általános, megosztott** konstans — **14 helyen** hivatkozzák a
`.text`-ben (`0x609599`, `0x782be8`, `0x7f848c`, `0x83a13e`, `0x868b1f` …),
tehát nem hordoz attribútum-specifikus jelentést.

**A következő lépés:** a kötő két hívottja — `0xbbace0` és `0xbbafe0` —
másolja a blokkot az objektum mezőibe; ott derül ki a leképezés.

*Bizonyítottsági fok: **megerősített** a kötő helye, a hat érték és a
`Comicize` hét tartalékon futó attribútuma; **nyitva** a hozzárendelés.*
