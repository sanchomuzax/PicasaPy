# A Finomhangolás KOMPOZIT esete — vég-a-véghez mérve (#951)

| mező | érték |
|---|---|
| dátum | 2026-09-12 14:54 (helyi idő) |
| commit | `99516169` |
| gép | Raspberry Pi 5, **4 mag**, 16 GB |
| terhelés a mérés alatt | `9,69 / 10,75 / 9,37` — **magasan terhelt** |
| mit futtatott még a gép | párhuzamos munkamenetek tesztjei |
| futások | 1 (a mérés determinisztikus: azonos bemenet → azonos kimenet) |

⚠️ A terhelés itt **nem befolyásolja az eredményt**: a mérőszám képpontok
eltérése, nem eltelt idő. A sort a `00-hogyan-merunk.md` szerint akkor is
kiírjuk, ha nem számít — így nem kell utólag találgatni.

## Mit mértünk

A #951 az **első kompozit esetünk**: a Finomhangolás két csúszkája
(Csúcsfények és Árnyékok) egyszerre, nem nullán. A tulajdonos leszállította
az eredeti + Picasa-export párt:

```
My Pictures/951-kiemelesek-arnyekok-fel-allas/
    original.jpg   + .picasa.ini
    export/original.jpg
```

A mentett lánc szó szerint:

```
filters=finetune2=1,0.000000,0.241404,0.238596,00000000,0.000000;
                     ^derítő  ^csúcsf. ^árnyék            ^színpálca
```

⭐ A két érték **nem azonos** (0,241404 vs 0,238596) — a korábbi
LUT-szintű kompozit eseteink (`kompozit_mid`, `kompozit_max`) ugyanazt az
értéket adták mindkét csúszkának. Ez tehát nem ugyanannak a mérésnek az
ismétlése.

## A menet

A lánc a **termék kódútján** futott (`ini.filters.parse_filters` →
`render.chain.apply_filters`), nem külön újraírt képleten — a kihagyott
szűrők listája üres, tehát a `finetune2` tényleg lefutott.

## Az eredmény

| összevetés | átlagos `\|eltérés\|` | max |
|---|---:|---:|
| **a mi renderünk vs a Picasa exportja** | **0,591** | 36 |
| kontroll: a nyers eredeti vs az export | 27,082 | 75 |
| kontroll: a Picasa exportjának JPEG-újrakódolása (q=90 / 95 / 98) | 1,183 / 1,007 / **0,882** | ~116 |

⇒ **A mi hibánk (0,591) a JPEG-újrakódolás saját zaja ALATT van** (a
legszigorúbb, q=98-as esetben is 0,882). A két kép különbsége tehát nem
mérhető ki élesben: a kompozit eset reprodukciója a mérés felbontásán belül
pontos.

A nyers kontroll (27,082) mutatja, hogy a hatás erős — nem arról van szó,
hogy a szűrő alig csinál valamit, és ezért „egyezik".

## Amit ez igazol

A #879 a Kiemelések/Árnyékok modelljét a natív szinthúzó LUT-ra állította
át, és **azt jósolta**, hogy a kompozit eset hibája „217 szintről nullára
esik". Ez most **vég-a-véghez, valódi fotón is** igazolt — eddig csak
LUT-szinten, szintetikus létraképen volt mérve.

## Amit ez NEM mond meg

- **A szélső állást nem méri.** A jegy eredetileg két beállítást kért
  (félutas és maximum); a félutas jött meg. A félutas eredménye alapján a
  szélsőt **nem kérjük be**: ha a modell a lánc közepén a zajszint alatt
  van, a szélsőnél sincs okunk mást várni — de ez **következtetés**, nem
  mérés.
- **Nem lett belőle őr-teszt.** A képpár a NAS-on él, a CI nem éri el; egy
  környezetfüggő skip nem őr. A LUT-szintű kompozit eseteket a
  `tests/render/test_tone_reference_551.py` továbbra is őrzi
  (`kompozit_mid` 0,74 · `kompozit_max` 0,55).
