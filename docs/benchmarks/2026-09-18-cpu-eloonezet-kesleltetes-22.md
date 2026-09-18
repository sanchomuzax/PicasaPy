# A hat GPU-képes szűrő CPU-ideje az előnézeten (RPi5) — #22

**Mérve:** 2026-09-18 · **gép:** Raspberry Pi 5 Model B Rev 1.1, aarch64,
4 mag · **szkript:** `scripts/gpu_cpu_kesleltetes_meres.py`

## A kérdés

A #22 hatóköre 2026-09-17-én mérve lett: **hat** szűrőnk fejezhető ki három
csatornánkénti 256-os LUT-tal, tehát a meglévő shader fogadná őket. Az
akkori mérés kimondta, hogy az áttérés **csak akkor indokolt, ha egy mérés
kimutatja, hogy a mai (CPU-s) út valahol tényleg akadozik**.

Ez a lap az a mérés — a **célgépen**, a szerkesztő előnézeti felbontásán.

## Módszer

- próbakép: **2560 × 1707** (az `edit_preview.py` 2560 képpontos élhosszra
  méretez dekódoláskor), véletlen RGB a **80…170** tartományban;
- mért érték: a `render/chain.apply_filters` fal-ideje, 7 ismétlés mediánja;
- memóriaplafon alatt (`systemd-run … MemoryMax=2400M`);
- küszöb: **100 ms** — e fölött a válasz már nem azonnali (UX-alapelv 4).

### Két csapda, amit a mérés maga fog meg

1. **A nem kanonikus szűrőnevet a `parse_filters` NÉMÁN kihagyja.** Az első
   futás így az `invert`-re 0,1 ms-ot mért — a szűrő el sem indult. A
   szkript ezért a `CANONICAL_FILTER_NAMES`-ből veszi az alakot.
2. **A teljes tartományú véletlen kép hisztogramja már kifeszített**, ezért
   az `autocontrast` rajta nem csinál semmit (mérve: 0 megváltozott
   képpont). A próbakép ezért szűk sávú — egy valódi fotó sem feszíti ki a
   teljes tartományt. A szkript minden szűrőre kiírja, **hány képpontot
   változtatott meg**; a nulla lelet, nem apróság.

## Eredmény

| szűrő | medián | min | max | változtat | verdikt |
|---|---:|---:|---:|---:|---|
| `autocontrast` | **146 ms** | 137 | 167 | 4096/4096 | akadozik |
| `colortemp` | **702 ms** | 534 | 1030 | 4096/4096 | akadozik |
| `crossprocess` | **863 ms** | 793 | 1948 | 4096/4096 | akadozik |
| `enhance` | **174 ms** | 146 | 249 | 4096/4096 | akadozik |
| `invert` | **5,6 ms** | 4,6 | 5,8 | 4096/4096 | azonnali |
| `warm` | **104 ms** | 92 | 120 | 4096/4096 | akadozik |

⇒ **Hatból öt lépi át a 100 ms-os küszöböt**, a `colortemp` és a
`crossprocess` hétszeresen–nyolcszorosan. A #22 gátló feltétele tehát
**teljesült**: a mai út a célgépen mérhetően akadozik.

## Amit ez NEM mond ki

- **A GPU-út idejét.** Ahhoz működő `ShaderEffect` kellene; a #3070 mérése
  szerint a tesztkörnyezetünkben a shader **el sem indul**, tehát a
  nyereség itt nem mérhető, csak becsülhető — és a projekt szabálya szerint
  becsült értéket nem adunk át.
- **Hogy a felhasználó mindig megvárja-e.** A lassú effektek egy része a
  #514 háttérszálán fut, és a lánc-prefix gyorsítótárazott (#140); a mért
  idő az az eset, amikor a szűrő tényleg lefut.
- **Az `invert`-et.** Az 5,6 ms-mal a küszöb alatt van bőven — rá a
  GPU-áttérés mérhető felhasználói nyereséget nem hoz.

## Következmény a jegyre

A #22 „Kész, ha" listája erre az **öt** szűrőre írható: `autocontrast`,
`colortemp`, `crossprocess`, `enhance`, `warm` — a `finetune2` meglévő
GPU-útjának mintájára. Az `invert` kimarad, indokkal.
