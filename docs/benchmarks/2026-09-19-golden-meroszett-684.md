# A 180 képes golden-mérőszett kiértékelése (2026-09-19, #684)

*A tulajdonos 2026-09-18-án exportálta a `684-merokeszlet` mappát az eredeti,
windowsos Picasával. Ez a lap a kiértékelés EREDMÉNYE — minden szám mérés.*

## A módszer

Minden képre két kérdés (`tools/golden/analyze_validation_kit.py`):

1. **csinált-e bármit a Picasa?** — az export vs. az érintetlen mérőkép;
2. **ugyanazt csináltuk-e mi?** — az export vs. a mi renderünk.

A kettőből jön a verdikt. A két legfontosabb eset az, amit egy puszta ΔE-szám
elrejtene: `NEM_IMPLEMENTALT` (a Picasa változtatott, mi nem) és `FOLOSLEGES`
(a Picasa nem, mi igen).

## Az eredmény — 180 lánc

| verdikt | darab | mit jelent |
|---|---:|---|
| `JO` | 72 | pixelhű egyezés (ΔE ≤ 2) |
| `MINDKETTO_TETLEN` | 56 | egyik oldal sem változtatott — a lánc az adott állásban tétlen |
| `KOZELITO` | 17 | ugyanabba az irányba hat, de nem pixelhűen |
| `ROSSZ` | 26 | érdemben mást csinálunk |
| `NEM_IMPLEMENTALT` | 8 | a Picasa változtatott, mi nem nyúltunk a képhez |
| `HIANYZO_EXPORT` | 1 | a képhez nincs export |

⇒ a 180-ból **128** rendben van
(72 pixelhű + 56 egyformán tétlen), **17**
közelít, és **34** tétel valódi eltérés.

⚠️ A `MINDKETTO_TETLEN` NEM siker-igazolás: azt jelenti, hogy az adott
csúszkaállásban egyik oldal sem hatott. Ezek a sorok azt mutatják meg, hol
nem mér semmit a szett — nem azt, hogy jó a szűrőnk.

## `ROSSZ` — érdemben mást csinálunk (26 tétel)

| effekt | eset | ΔE (Picasa vs. eredeti) | ΔE (mi vs. Picasa) | más a MÉRET? |
|---|---|---:|---:|---|
| `boost` | max | 21.967 | 13.071 | nem |
| `crossprocess` | alap | 22.976 | 8.885 | nem |
| `dropshadow` | alap | 15.279 | 36.529 | **IGEN** |
| `dropshadow` | max | 42.419 | 28.368 | **IGEN** |
| `finetune` | max | 54.348 | 44.277 | nem |
| `finetune2` | alap | 32.503 | 52.284 | nem |
| `finetune2` | max | 56.224 | 43.229 | nem |
| `focalzoom` | alap | 7.572 | 14.748 | nem |
| `heatmap` | alap | 104.801 | 20.932 | nem |
| `heatmap` | min | 96.352 | 21.28 | nem |
| `ir` | alap | 18.131 | 6.039 | nem |
| `nightvision` | alap | 51.283 | 14.52 | nem |
| `nightvision` | min | 48.738 | 11.951 | nem |
| `picnikgrain` | max | 14.237 | 12.203 | nem |
| `pixelate` | min | 23.322 | 23.307 | nem |
| `polaroid` | alap | 37.644 | 18.847 | nem |
| `polaroid` | max | 38.491 | 22.825 | nem |
| `polaroid` | min | 40.467 | 22.596 | nem |
| `quantizepalette` | alap | 16.035 | 16.732 | nem |
| `quantizepalette` | min | 26.931 | 40.015 | nem |
| `radsat` | alap | 8.172 | 6.468 | nem |
| `radtint` | alap | 32.061 | 8.913 | nem |
| `radtint` | min | 36.347 | 11.786 | nem |
| `sixties` | alap | 20.342 | 15.811 | nem |
| `sixties` | min | 25.853 | 20.056 | nem |
| `twotone` | alap | 65.8 | 9.236 | nem |

## `NEM_IMPLEMENTALT` — a Picasa hatott, mi nem (8 tétel)

| effekt | eset | ΔE (Picasa vs. eredeti) | ΔE (mi vs. Picasa) | más a MÉRET? |
|---|---|---:|---:|---|
| `hdr` | min | 1.12 | 1.12 | nem |
| `museummatte` | min | 1.483 | 0.842 | nem |
| `picnikfocalpixelate` | alap | 2.889 | 2.889 | nem |
| `picnikgrain` | alap | 3.053 | 3.009 | nem |
| `radsat` | max | 3.657 | 3.657 | nem |
| `roundededges` | max | 3.164 | 2.833 | nem |
| `unsharp` | alap | 1.117 | 0.359 | nem |
| `unsharp2` | alap | 1.117 | 0.359 | nem |

⚠️ Az első háromnál (`hdr` min 1,12 · `museummatte` min 1,48 · `unsharp`/
`unsharp2` alap 1,12) a Picasa változása alig a JPEG-zaj fölött van — ezek
inkább „a szett nem mér ott" esetek, mint valódi hiányok. A `radsat` max
(3,66), a `roundededges` max (3,16), a `picnikgrain` (3,05) és a
`picnikfocalpixelate` (2,89) viszont valódi hiány.

## `HIANYZO_EXPORT`

Az `unsharp__max.jpg` nincs az exportban (179 kép jött vissza a 180-ból). Ez
nem a tulajdonos hibája — a Picasa a kimaradt képnél hibát jelezhetett, ahogy
a kérés is számolt vele („a hiányzó kép is eredmény").

## Amit ez a lap NEM mond meg

* **Miért** tér el, amelyik eltér — a ΔE csak a tényt adja.
* A `JO` sorok sem jelentenek teljes hűséget: a szett effektenként 1–3
  csúszkaállást mér, nem a teljes tartományt.
* A méret-eltérés (`dropshadow`) külön súlyos: ott nem a színek térnek el,
  hanem a kimenet GEOMETRIÁJA.

## Az eltolódás-szabály után (#3895)

*Mérve 2026-09-28-án, ugyanazon a 180 láncon.* Az elemző új szabályt kapott:
a „tétlen” sor átlagos **előjeles** eltolódása (`mean_shift`, szintben) sem
érheti el a `SHIFT_LEVEL = 0,25`-öt, különben a sor művelet, akkor is, ha a
ΔE 1 alatt marad. A küszöb indoka: a JPEG-újratömörítés zaja előjelesen
kiegyenlítődik (≤ 0,003), a legkisebb valódi jel a `dir_tint__min` −0,50-e.
A szett legnagyobb küszöb alatti eltolódása 0,12
(`picnikfocalpixelate__min`, a Picasánál és nálunk egyformán).

„Előtte” = a `main` elemzője és renderje (`562c571d`); „utána” = a #3895-ös
ág (elemző + a Lágyítás 0-s erősségű keverése).

| verdikt | előtte | utána |
|---|---:|---:|
| `JO` | 113 | 115 |
| `MINDKETTO_TETLEN` | 56 | 53 |
| `KOZELITO` | 10 | 10 |
| `NEM_IMPLEMENTALT` | 0 | **1** |
| `HIANYZO_EXPORT` | 1 | 1 |

**Az átforduló sorok — mind a három:**

| sor | előtte | utána | ΔE Picasa↔eredeti | ΔE mi↔Picasa (előtte → utána) | eltolódás Picasa / mi (utána) |
|---|---|---|---:|---:|---:|
| `soften__min` | `MINDKETTO_TETLEN` | `JO` | 0,470 | 0,470 → 0,121 | −0,996 / −0,999 |
| `roundededges__alap` | `MINDKETTO_TETLEN` | `JO` | 0,935 | 0,143 → 0,143 | +2,096 / +2,080 |
| `dir_tint__min` | `MINDKETTO_TETLEN` | **`NEM_IMPLEMENTALT`** | 0,296 | 0,296 → 0,296 | −0,498 / 0,000 |

* A `soften__min` a #3895 javítása: a Picasa −1-es keverését most mi is
  elvégezzük.
* A `roundededges__alap`-nál a sarkok fehérje mindkét oldalon ugyanúgy
  világosít (+2,1 szint): a sor eddig rejtetten volt jó, most látszik, hogy az.
  Nem `FOLOSLEGES`, mert a Picasa is ugyanannyit mozdít.
* A `dir_tint__min` **eddig rejtett eltérés.** A Picasa-export felső fele
  (az átmenet vonala, `y = 0,5` fölött) pontosan eggyel sötétebb (sávátlag
  −0,995), az alsó fele változatlan (−0,001); érték szerint 0 → 0,08,
  1 → 0,03, 2 → 1,00, 128 → 127,62 — a `soften__min`-ből ismert
  `(255·b) >> 8` minta. A mi renderünk a bemenet másolata (ΔE 0,000). Egy
  0,5-ös küszöb ezt a sort (−0,498) épp nem fogta volna meg.

A 0,5-ös és a 0,25-ös küszöb között a szett egyetlen sorban tér el: a
`dir_tint__min`-ben.
