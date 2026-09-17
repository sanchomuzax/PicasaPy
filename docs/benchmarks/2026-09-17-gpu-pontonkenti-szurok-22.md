# Mely szűrőink fejezhetők ki GPU-shaderrel? — a #22 mért hatóköre

**Dátum:** 2026-09-17 · **Jegy:** #22 · **Mérő:**
`scripts/gpu_pontonkenti_meres.py`

## A kérdés

A #22 („GPU-renderpipeline, shader-lánc") 2026 tavaszán nyílt, egyetlen
mondattal: *„A CPU-referencia átültetése GPU-ra (QML ShaderEffect / RHI),
ping-pong textúrákkal"*. Azóta a GPU-út **egy** esetre megépült (a
`finetune2` pontonkénti LUT-ja, `GpuPointFilterPreview.qml`), és közben a
`filters-decoded.md` ki is mondta, hogy a **Derítőfény NEM fejezhető ki
csatornánkénti LUT-tal**. A jegy hatóköre tehát tisztázatlan volt.

Ez a mérés megmondja, **hány szűrő jöhet egyáltalán szóba**.

## A módszer

Egy szűrő **pontonkénti**, ha a kimeneti pixel csak a bemeneti pixeltől függ.
A próbakép 64×64: a felső fele véletlen RGB, az alsó fele **ugyanazok a
pixelek véletlen permutációban** — így minden bemeneti érték több, egymással
**nem szimmetrikus** helyen áll. Ha a kimenet minden előfordulásnál azonos, a
szűrő pontonkénti; ha ezen felül minden kimeneti csatorna csak a SAJÁT
bemeneti csatornájától függ, akkor **három 256-os LUT-tal** kifejezhető — ez
az, amit a mai shaderünk tud.

⚠️ **Az első próbakép tükrözve ismételte a felső felet, és ez HAMIS
eredményt adott**: a sugaras effektek (`vignette`, `radtint`) épp erre a
tengelyre szimmetrikusak, tehát a tükörpár ugyanazt a súlyt kapta, és a mérés
pontonkéntinek mondta őket. A permutációval mindhárom átkerült a helyes
csoportba (és velük az `unsharp`/`unsharp2` is).

## Az eredmény (84 regiszter-bejegyzés)

| csoport | darab | nevek |
|---|---|---|
| **csatornánkénti LUT-tal kifejezhető** (a mai shader tudja) | **6** | `autocontrast`, `colortemp`, `crossprocess`, `enhance`, `invert`, `warm` |
| pontonkénti, de a csatornák keverednek (3×3 mátrix vagy több bemenet kell) | 13 | `ansel`, `autobacklight`, `backlight`, `boost`, `bw`, `heatmap`, `picniktint`, `radsat`, `redeye`, `sat`, `sepia`, `tint`, `twotone` |
| **NEM pontonkénti** (környezet, hely vagy geometria) | 35 | `cinemascope`, `comicize`, `contrast`, `dir_brite`, `dir_sat`, `dir_sharp`, `gamma`, `glow`, `glow2`, `grain`, `grain2`, `hdr`, `holga`, `ir`, `linblur`, `localcontrast`, `lomo`, `matte`, `museummatte`, `neon`, `nightvision`, `orton`, `pencilsketch`, `picnikgrain`, `pixelate`, `polaroid`, `quantizepalette`, `radblur`, `radtint`, `sixties`, `soften`, `triple`, `unsharp`, `unsharp2`, `vignette` |
| nem mérve | 30 | 6 szín-paraméteres (`border`, `dropshadow`, `focalzoom`, `dir_tint`, `finetune`, `finetune2` — a #3229 óta ismert: a csúszka-INDEX nem paraméter-POZÍCIÓ), 7 a láncból kihagyott (`colorfix`, `crop64`, `debug`, `focalpixelate`, `picnikfocalpixelate`, `rainbow`, `whitept`), 17 pedig az alapértékén **nem változtat** a képen |

## ⛔ Amit ez NEM mond ki

- **A verdikt az ALAPÉRTELMEZETT paraméterekre szól.** Egy szűrő lehet az
  alapértékén pontonkénti, más állásban viszont hely-függő (a `radsat` a
  legvalószínűbb ilyen jelölt).
- Nem mondja meg, hogy **érdemes-e** GPU-ra vinni: azt a mért idő dönti el.
  A mai CPU-út a lassú effekteknél háttérszálra megy (#514) és
  lánc-prefixet gyorsítótáraz (#140), tehát a felület ezektől ma sem fagy be.

## Következtetés a #22 hatóköréről

A „az egész lánc GPU-ra" megfogalmazás **mérésből nem tartható**: a 84
bejegyzésből **6** az, amit a mai shader-út egyáltalán fogadni tud, további
13-hoz **csatorna-keverő** shader kellene, 35 pedig elvileg sem pontonkénti.
A jegy helyes alakja ezért egy **megnevezett, szűk lista** (a fenti hat, majd
esetleg a tizenhárom), nem a teljes lánc.
