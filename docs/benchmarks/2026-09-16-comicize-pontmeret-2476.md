# A Comicize pontmérete: a MÉRT 0,8-as skála (#2476)

**Mérőkészlet:** `research/comicize-sweep/` — 15 eredeti Picasa-export három
csúszkára (BlurXY · DotContrast · DotFade, öt-öt állás), 1600 × 1200, csempe 24.

**Két mérőszám, mindkettő kimondva:**

* **átlag ΔE** (CIE76, Lab) a mi kimenetünk és a Picasa-export között;
* **raszter-amplitúdó**: a CSEMPÉN BELÜLI fázisprofil szórása (minden képpont
  fázisa `x mod csempe`, `y mod csempe`; a profil az adott fázis átlagos
  lumája). Ez a raszter ERŐSSÉGÉT méri — a ΔE erre keveset mond, mert a
  fázis-eltolást is büntetné.

## A változás: `radius = 1 − tónus` → `radius = 0,8 · (1 − tónus)`

A `TiledImageMask` `scaleWidth`/`scaleHeight` mezője (`+0x10`/`+0x14`) a
konstruktorban **0,8**, és a szállított `filterdesc.xml` két példánya egyiken
sem adja meg — tehát mindkettő az alapértéket használja. A rajzoló a mezőt a
tengely méretével szorozza, így a pont átmérője `0,8 · csempe`, a sugara a
beírt kör 0,8-a.

## Az eredmény — 15/15 kép

| | átlag ΔE | átlag amplitúdó-hiba |
|---|---:|---:|
| a #2476 előtt (skála 1,0) | 6,5132 | 2,2519 |
| **ma (skála 0,8)** | **5,9326** | **1,3909** |

A ΔE **mind a 15 álláson** javult, az amplitúdó-hiba 12-en. A raszter
amplitúdója 5,70 → 4,75 (a referencia 3,77), tehát a túl-erősség a felére
csökkent.

⭐ **A szám ELŐRE megjósolta a hibát:** a festékes terület a sugár
négyzetével nő, és `1 / 0,8² = 1,5625` — pontosan az a ~1,5-szeres
túl-erősség, amit a korábbi körök mértek (5,70 vs. 3,77 = 1,51×).

## ⛔ Amit ez a kör KIZÁRT: „a pont sugara állandó"

A jegy CÍME azt állította, hogy nálunk a tónus a sugarat modulálja, az
eredetiben viszont a pont **állandó**, és a tónus csak a fedettséget adja.
Ezt lemértük — a raszter-ág `ink = maszk(0,8) · (1 − tónus)` alakjával:

| modell | átlag ΔE | amplitúdó (mi) | amplitúdó-hiba |
|---|---:|---:|---:|
| sugár-moduláció, skála 0,8 (**ez a kör**) | 5,9326 | 4,75 | **1,3909** |
| **állandó sugár, tónus = fedettség** | 5,3345 | **0,29** | 3,4210 |

Az állandó sugarú modell ΔE-ben látszólag jobb — **de nem rajzol rasztert**: az
amplitúdója 0,29, a referenciáé 3,77. Ez ugyanaz a metrika-csapda, amit a
#1606 már megnevezett (az ágankénti küszöb SSIM-je is „javult", miközben
elnyelte a rasztert). ⇒ **A cím hipotézise ebben a formában kizárva**; a
sugár igenis a tónussal nő, csak a mért 0,8-as skálával.

## Ami NYITVA marad — megnevezve

A `DotContrast` válaszgörbéje továbbra is **meredekebb** a referenciáénál:

| DotContrast | 0 | 25 | 50 | 75 | 100 |
|---|---:|---:|---:|---:|---:|
| a mi amplitúdónk | 0,41 | 1,53 | 4,75 | 7,58 | 9,35 |
| a referencia | 1,66 | 2,86 | 3,77 | 4,46 | 5,04 |

A méret javítása a görbét arányosan lehúzta, de nem lapította ki: a referencia
a két végén (0 és 100) **négyszer kevésbé** tér el a közepétől, mint nálunk. Ez
NEM a pontméret kérdése — a következő irány a küszöbgörbe (`90 + DotContrast·1,5`
mozgó töréspont) és a pont-alfa viszonya, amihez a `filterdesc.xml`
`_opColorSpots` blokkjának alfa-kötését kell kiolvasni a binárisból.
