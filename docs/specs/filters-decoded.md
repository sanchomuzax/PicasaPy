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

## Nyitva a 4. körre

1. **autocolor modell** — célzott cast-próbák (különböző öntet-erősségek,
   fehérpont jelenléttel/nélkül) → csillapítási együttható
2. unsharp v1/v2 kernel (sakktábla-elemzés — export megvan az 1. körből)
3. térbeli effektek: Vignette/glow/radblur maszk- és kernel-modellek
4. tilt szög↔skála szemantika (mérhető a meglévő tilt-exportokból)
5. `tint` színparaméter-formátum; retouch/redeye régió-adatok; text overlay
