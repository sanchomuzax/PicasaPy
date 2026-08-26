# A másodpéldány-keresés olvasási költsége (#1481)

*Mérve 2026-08-26, a #1481 megvalósításakor. A cél annak eldöntése, mekkora
valódi nyereséget hoz a Picasa fej+farok tartalom-kulcsa (`dedup/fastkey.py`)
a teljes SHA-256-hoz képest.*

## 1. Ami a jegyben állt, és amit mértünk

A jegy (és a `docs/specs/picasa-tartalomkulcs.md`) **150-szeres** különbséget
ígért. Ez **fájlonként igaz**, de **egy keresési körre nem**: a
`dedup/exact.py` már a #31 óta **méret-előszűrőt** használ, tehát a teljes
hash eleve csak az azonos méretű jelöltekre futott le, nem minden képre.

## 2. Fájlonkénti költség — a 150× igazolva

60 valódi fénykép (`research/testdata/2025-05-xx`, átlag 4,88 MB), meleg
lapgyorstár, helyi SSD:

| | olvasott bájt | idő |
|---|---|---|
| gyors kulcs (`picasa_fast_key`) | 2,02 MB | 5,7 ms |
| teljes SHA-256 (`file_content_hash`) | 292,58 MB | 291,2 ms |
| **arány** | **144,8×** | **51,1×** |

Hálózati megosztáson (a felhasználó gyűjteménye NAS-on van) a bájt-arány a
mérvadó, mert ott az átvitel dominál, nem a CPU.

## 3. Egy teljes körre vetítve — jóval szerényebb

Ugyanaz a mérés korpuszonként, a pontos-duplikátum rétegre:

| korpusz | fájl | összméret | azonos méretű jelölt | MA olvas | gyorskulccsal | megtakarítás |
|---|---|---|---|---|---|---|
| `2025-05-xx` (valódi fényképek) | 235 | 936,7 MB | **0** | 0 MB | 0 MB | – |
| `PicasaPy-merokit` (szándékos másolatok) | 494 | 242,6 MB | 304 | 150,26 MB | 147,58 MB | 1,8 % |
| `golden-kit-result` | 494 | 247,5 MB | 330 | 157,74 MB | 140,09 MB | 11,2 % |

**Amit ez mond:** ahol a fájlok tényleg másodpéldányok (mérőkészletek), a
gyors kulcs nem segít — a teljes összevetés úgyis lefut, sőt fájlonként
~33 KB-tal többet olvasunk. Ahol azonos a méret, de eltér a tartalom, ott a
teljes olvasás **elmarad**, és ott jön elő a 2. pont 145-szörös aránya.
Egy tiszta, valódi fényképgyűjteményben (235 kép) **egyetlen** méret-ütközés
sem volt, tehát ott a pontos réteg ma is nulla bájtot olvas.

## 4. A felhasználó valódi gyűjteménye — 140 755 kép

A `research/testdata/Picasa2/db3/imagedata_originfast.pmp` (a felhasználó
saját Picasa-adatbázisa) tartalom-kulcs szerinti eloszlása:

| | darab |
|---|---|
| sor összesen | 140 755 |
| nem-nulla kulcs | 133 455 |
| **egyedi kulcs** | **130 966** |
| többször előforduló kulcs | 2 316 |
| az ezekhez tartozó sorok | 4 805 (**3,6 %**) |

Csoportméret-hisztogram: 2×2163, 3×138, 4×11, 5×3, 6×1.

Vagyis a gyűjtemény **96,4 %-a egyedi tartalmú** — ennyi képet a gyors kulcs
egyetlen 33 KB-os olvasással kizár, ha a keresés valaha kulcs szerint fut.

## 5. Ami a kör költségét MA valójában viszi: a dHash

A `dedup/find_duplicates` a pontos réteg után **minden** képre perceptuális
lenyomatot számol (`dedup/phash.py` → `cvimage.read_image_bytes`), ami a
fájl **teljes** beolvasása. Az első futásnál tehát a kör a gyűjtemény
100 %-át átolvassa, függetlenül attól, mit takarít meg a pontos réteg.
Ezt a #294 óta az index `photo_hashes` gyorstára enyhíti (a második futásnál
csak az új/megváltozott képeket dekódolja) — de a **pontos** rétegnek nincs
ilyen gyorstára.

**Következtetés:** a #1481 nem a kör főköltségét csökkenti. A gyors kulcs
valódi hozadéka (a) a méret-ütközéses esetek 145-szörös olcsóbbodása,
(b) hogy megvan a **Picasa-kompatibilis, tárolható tartalom-kulcs** — az
`imagedata_originfast` oszlop párja. A tárolás (indexséma) külön jegy.

## 6. Igazolás

A `picasapy.dedup.fastkey.picasa_fast_key` a felhasználó valódi `db3`-jának
`imagedata_originfast` oszlopával szemben **12/12** bitpontos egyezést adott
(169 KB – 1,88 MB, JPG és PNG). Ez a spec 10/10-es mérésének független
újrafuttatása, ezúttal a **kiadott** megvalósítással.
