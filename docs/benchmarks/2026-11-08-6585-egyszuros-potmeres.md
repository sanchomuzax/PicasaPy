# #6585 - Egyszűrős pótmérés a 30 eldöntetlen lánchoz

**Dátum:** 2026-11-08  
**Kiinduló dokumentum:** `docs/benchmarks/2026-11-08-6585-differencialis-lanc-besorolas.md` (a 32 eltérő lánc besorolása)

## Mi ez

A besorolás 30 láncot "c"-be tett, mert a láncot alkotó szűrők egyenkénti, eredeti Picasával készült renderje hiányzik. Ez a lap azt rögzíti, hogy a hiányzó egyszűrős eseteket feladtuk a Colab-végrehajtónak: melyik feladat melyik esetet méri, és melyik issue-szám alatt fut. Az eredmények még nem érkeztek meg, a besorolás nem változott.

## Hogyan állt össze a lista

1. **Forrás:** a "c" besorolású 30 lánc `filters=` értéke a besoroló lapról, tagokra bontva.
2. **Már mért tagok kiszűrve:** a `picasa-colab-jobs` 400-406. issue-ja (a `r6585f` 64 egyszűrős esete) minden `(kép, pontos szűrősor)` párját beolvastam. Egy tag akkor "mért", ha ugyanazon a képen ugyanazzal a paraméterezéssel már van egyszűrős eredeti render. A 407. issue (#6617, `colorfix`-változatok) más paraméterekkel készült, ezért egyik láncbeli tagot sem fedi le.
3. **Véletlen szemcse kizárva:** `grain`, `grain2`, `PicnikGrain` tagot nem kértem, mert a besorolás is kizárja őket a pixelmérésből, a véletlen szemcse miatt nem lehet képpontosan besorolni.
4. **Ellenőrzés:** a fenti szabállyal mind a 32 eltérő láncra pontosan ugyanazt a hiányzó-tagszámot és kizárt-szemcseszámot kaptam, mint a besoroló lap "Egyszűrős bizonyíték" oszlopa.
5. **Egyediség:** a hiányzó tagok között nincs két azonos `(kép, szűrősor)` pár, ezért nem kellett összevonni.

| Mennyiség | Db |
|---|---:|
| "c" besorolású lánc | 30 |
| a láncok tagjai, amelyekhez már van azonos bemenetű egyszűrős mérés (nem kértem újra) | 23 |
| kizárt véletlen szemcse-tag | 12 |
| **hiányzó tag, vagyis feladott eset** | **92** |
| ebből hex-színnel kezdődő `colorfix` (lásd lent) | 8 |
| Colab-feladat (köteg) | 23 |

A "b" (`lanc-0045`) és az "a" (`lanc-0052`) lánc minden tagja már mért, ezekhez nem kellett eset.

## Miért 23 feladat, ha csak 92 eset van

Egy feladatban az ini képenként egyetlen `filters=` sort hordozhat, a mintakészletben pedig csak a `k01.jpg`-`k10.jpg` képek vannak. Egy feladat tehát legfeljebb 10 esetet visz, képenként egyet. A leggyakoribb kép, a `k05.jpg`, 23 hiányzó esetet kér, így legalább 23 feladat kell. A többi kép esetei (k06: 17, k10: 10, k08 és k09: 8-8, k02 és k07: 7-7, k03 és k04: 5-5, k01: 2) ugyanebbe a 23 feladatba oszlanak szét.

Az eseteket képenként úgy sorrendeztem, hogy a kevés hiányzó taggal bíró láncok előbb teljessé váljanak: a koteg-001 után 2, a koteg-003 után 11 lánc összes hiányzó tagja mérve van. A feladatok `lepesek`, `kimenet`, `keret` (30 perc), `indulas` és `mintakeszlet` mezője azonos a 400-406. issue-ban használttal (gépileg összevetve mind a hét feladattal); a feladatban nem szereplő képeknek nincs `filters=` sora, azokat nem értékeljük.

## A feladott feladatok

Minden feladat: `colab-job`, `tipus:ui_capture`, `allapot:varakozik` címkékkel nyílt, `v: 3`, `indulas: alapallapot`, `mintakeszlet: kombinalt`, cím: `#6585 egyszűrős pótmérés koteg-NNN`. A feladatfájlok a munkafában a `.bt/r6585p/koteg-NNN.job.json` és `.ini` alatt vannak (a `.bt` nincs verziókezelve).

| Köteg | Issue | Esetek | Képek |
|---|---:|---:|---|
| koteg-001 | 408 | 10 | k01, k02, k03, k04, k05, k06, k07, k08, k09, k10 |
| koteg-002 | 409 | 10 | k01, k02, k03, k04, k05, k06, k07, k08, k09, k10 |
| koteg-003 | 410 | 9 | k02, k03, k04, k05, k06, k07, k08, k09, k10 |
| koteg-004 | 411 | 9 | k02, k03, k04, k05, k06, k07, k08, k09, k10 |
| koteg-005 | 412 | 9 | k02, k03, k04, k05, k06, k07, k08, k09, k10 |
| koteg-006 | 413 | 7 | k02, k05, k06, k07, k08, k09, k10 |
| koteg-007 | 414 | 7 | k02, k05, k06, k07, k08, k09, k10 |
| koteg-008 | 415 | 5 | k05, k06, k08, k09, k10 |
| koteg-009 | 416 | 3 | k05, k06, k10 |
| koteg-010 | 417 | 3 | k05, k06, k10 |
| koteg-011 | 418 | 2 | k05, k06 |
| koteg-012 | 419 | 2 | k05, k06 |
| koteg-013 | 420 | 2 | k05, k06 |
| koteg-014 | 421 | 2 | k05, k06 |
| koteg-015 | 422 | 2 | k05, k06 |
| koteg-016 | 423 | 2 | k05, k06 |
| koteg-017 | 424 | 2 | k05, k06 |
| koteg-018 | 425 | 1 | k05 |
| koteg-019 | 426 | 1 | k05 |
| koteg-020 | 427 | 1 | k05 |
| koteg-021 | 428 | 1 | k05 |
| koteg-022 | 429 | 1 | k05 |
| koteg-023 | 430 | 1 | k05 |

### Esetek feladatonként

| Köteg | Issue | Kép | Szűrő (pontos paraméterekkel) | Lánc |
|---|---:|---|---|---|
| koteg-001 | 408 | k01.jpg | `colorfix=1,ff2739b2,-0.326245;` | lanc-0101 |
| koteg-001 | 408 | k02.jpg | `PicnikFocalPixelate=1,0.698914,0.945061,42.726991,31.797369,60.493888,63.244677,0;` | lanc-0142 |
| koteg-001 | 408 | k03.jpg | `TwoTone=1,-34.649025,42.816806,49.327950,00cc1cd3,00f3ee8e;` | lanc-0043 |
| koteg-001 | 408 | k04.jpg | `colorfix=1,ff3de652,0.486719;` | lanc-0144 |
| koteg-001 | 408 | k05.jpg | `colorfix=1,ff680664,-0.249688;` | lanc-0005 |
| koteg-001 | 408 | k06.jpg | `rainbow=1,244.890456;` | lanc-0056 |
| koteg-001 | 408 | k07.jpg | `Holga=1,27.444017,76.630990,12.639445;` | lanc-0067 |
| koteg-001 | 408 | k08.jpg | `PicnikFocalPixelate=1,0.754539,0.257084,5.226035,44.746379,30.137856,45.902113,0;` | lanc-0048 |
| koteg-001 | 408 | k09.jpg | `autocolor=1;` | lanc-0169 |
| koteg-001 | 408 | k10.jpg | `colorfix=1,ff773aed,0.352651;` | lanc-0080 |
| koteg-002 | 409 | k01.jpg | `unsharp=1,0.559595;` | lanc-0101 |
| koteg-002 | 409 | k02.jpg | `QuantizePalette=1,26.866748,28.222955,86.942047;` | lanc-0142 |
| koteg-002 | 409 | k03.jpg | `unsharp=1,0.429447;` | lanc-0043 |
| koteg-002 | 409 | k04.jpg | `PicnikFocalPixelate=1,0.457857,0.092015,36.231898,86.737197,46.345083,4.704272,0;` | lanc-0124 |
| koteg-002 | 409 | k05.jpg | `colorfix=1,ffc0ea7e,-0.140316;` | lanc-0005 |
| koteg-002 | 409 | k06.jpg | `triple=1,-0.207838,-0.406449,0.214067;` | lanc-0056 |
| koteg-002 | 409 | k07.jpg | `LocalContrast=1,18.977791,2.424472;` | lanc-0067 |
| koteg-002 | 409 | k08.jpg | `autolight=1;` | lanc-0048 |
| koteg-002 | 409 | k09.jpg | `autolight=1;` | lanc-0169 |
| koteg-002 | 409 | k10.jpg | `colorfix=1,ffccfb8f,-0.256467;` | lanc-0190 |
| koteg-003 | 410 | k02.jpg | `triple3=1,0.554400,0.413470,0.290744;` | lanc-0142 |
| koteg-003 | 410 | k03.jpg | `HDR=1,25.214587,5.596100,24.480760;` | lanc-0113 |
| koteg-003 | 410 | k04.jpg | `autocontrast=1;` | lanc-0124 |
| koteg-003 | 410 | k05.jpg | `rainbow=1,229.438578;` | lanc-0005 |
| koteg-003 | 410 | k06.jpg | `ansel=1,ff3758f3;` | lanc-0186 |
| koteg-003 | 410 | k07.jpg | `PicnikFocalPixelate=1,0.379377,0.280311,5.110434,52.012805,56.186495,22.578563,0;` | lanc-0067 |
| koteg-003 | 410 | k08.jpg | `colortemp=1,-0.389167,0.612947;` | lanc-0178 |
| koteg-003 | 410 | k09.jpg | `IR=1,6.505770;` | lanc-0089 |
| koteg-003 | 410 | k10.jpg | `PencilSketch=1,3.844177,163.752261,80.619866;` | lanc-0010 |
| koteg-004 | 411 | k02.jpg | `PicnikFocalPixelate=1,0.596101,0.315251,38.262959,67.621441,30.602824,38.221530,0;` | lanc-0022 |
| koteg-004 | 411 | k03.jpg | `HeatMap=1,-166.268420,33.668530;` | lanc-0113 |
| koteg-004 | 411 | k04.jpg | `colorfix=1,ff50b5af,-0.481740;` | lanc-0124 |
| koteg-004 | 411 | k05.jpg | `Boost=1,36.252043;` | lanc-0065 |
| koteg-004 | 411 | k06.jpg | `colorfix=1,ff789687,0.154606;` | lanc-0186 |
| koteg-004 | 411 | k07.jpg | `CrossProcess=1,1.191213;` | lanc-0117 |
| koteg-004 | 411 | k08.jpg | `triple2=1,0.218250,0.303895,0.317896;` | lanc-0178 |
| koteg-004 | 411 | k09.jpg | `radsat=1,0.935702,0.276913,-0.462013,0.789662;` | lanc-0089 |
| koteg-004 | 411 | k10.jpg | `backlight=1,0.015514;` | lanc-0010 |
| koteg-005 | 412 | k02.jpg | `dir_sat=1,0.570065,0.531207;` | lanc-0022 |
| koteg-005 | 412 | k03.jpg | `warm=1;` | lanc-0113 |
| koteg-005 | 412 | k04.jpg | `radsat=1,0.466994,0.173746,0.209913,0.696717;` | lanc-0124 |
| koteg-005 | 412 | k05.jpg | `ansel=1,ff25d557;` | lanc-0065 |
| koteg-005 | 412 | k06.jpg | `unsharp2=1,1.569590;` | lanc-0186 |
| koteg-005 | 412 | k07.jpg | `HeatMap=1,-101.723152,46.384101;` | lanc-0117 |
| koteg-005 | 412 | k08.jpg | `PencilSketch=1,2.433558,9.770045,31.821444;` | lanc-0088 |
| koteg-005 | 412 | k09.jpg | `triple2=1,0.127180,0.190318,0.055157;` | lanc-0089 |
| koteg-005 | 412 | k10.jpg | `DropShadow=1,20.235157,164.620360,83.506034,007d27c2,009d04a2,3.158258;` | lanc-0060 |
| koteg-006 | 413 | k02.jpg | `enhance=1;` | lanc-0022 |
| koteg-006 | 413 | k05.jpg | `shadow=1,0.764285,0.655234,0.163184;` | lanc-0065 |
| koteg-006 | 413 | k06.jpg | `CrossProcess=1,22.173648;` | lanc-0116 |
| koteg-006 | 413 | k07.jpg | `glow=1,0.943897,17.486931;` | lanc-0117 |
| koteg-006 | 413 | k08.jpg | `PicnikFocalPixelate=1,0.257873,0.777093,18.371648,16.955073,83.975403,36.162119,0;` | lanc-0088 |
| koteg-006 | 413 | k09.jpg | `Comicize=1,97.076368,83.882062,99.079918;` | lanc-0119 |
| koteg-006 | 413 | k10.jpg | `Vignette=1,48.277238,1.527099,84.880421,00c7828a;` | lanc-0060 |
| koteg-007 | 414 | k02.jpg | `unsharp2=1,1.889519;` | lanc-0022 |
| koteg-007 | 414 | k05.jpg | `PicnikFocalPixelate=1,0.734580,0.362004,35.565019,64.583751,83.643288,11.843983,0;` | lanc-0115 |
| koteg-007 | 414 | k06.jpg | `Soften=1,81.679116,95.722213;` | lanc-0116 |
| koteg-007 | 414 | k07.jpg | `radblur=1,0.195302,0.408240,-0.055610,-0.967370;` | lanc-0117 |
| koteg-007 | 414 | k08.jpg | `radtint=1,0.113828,0.081816,0.197103,ffe11e1b;` | lanc-0088 |
| koteg-007 | 414 | k09.jpg | `Pixelate=1,72.192947,3.126227,5.346142;` | lanc-0119 |
| koteg-007 | 414 | k10.jpg | `HDR=1,65.299969,1.626753,76.860461;` | lanc-0140 |
| koteg-008 | 415 | k05.jpg | `glow=1,0.240375,86.608439;` | lanc-0115 |
| koteg-008 | 415 | k06.jpg | `glow=1,0.220319,29.085845;` | lanc-0116 |
| koteg-008 | 415 | k08.jpg | `unsharp=1,0.811594;` | lanc-0088 |
| koteg-008 | 415 | k09.jpg | `whitept=1,ff12141f;` | lanc-0119 |
| koteg-008 | 415 | k10.jpg | `backlight=1,0.832331;` | lanc-0140 |
| koteg-009 | 416 | k05.jpg | `unsharp2=1,0.890722;` | lanc-0115 |
| koteg-009 | 416 | k06.jpg | `sepia=1;` | lanc-0116 |
| koteg-009 | 416 | k10.jpg | `dir_sharp=1,-0.397475,0.968720;` | lanc-0140 |
| koteg-010 | 417 | k05.jpg | `ansel=1,ff06c7fb;` | lanc-0095 |
| koteg-010 | 417 | k06.jpg | `triple2=1,0.500244,0.837205,0.579954;` | lanc-0116 |
| koteg-010 | 417 | k10.jpg | `warm=1;` | lanc-0140 |
| koteg-011 | 418 | k05.jpg | `dir_sharp=1,-0.767675,0.017529;` | lanc-0095 |
| koteg-011 | 418 | k06.jpg | `unsharp2=1,0.973675;` | lanc-0116 |
| koteg-012 | 419 | k05.jpg | `sepia=1;` | lanc-0095 |
| koteg-012 | 419 | k06.jpg | `CrossProcess=1,28.019592;` | lanc-0196 |
| koteg-013 | 420 | k05.jpg | `triple2=1,0.613640,0.987095,0.051496;` | lanc-0095 |
| koteg-013 | 420 | k06.jpg | `QuantizePalette=1,8.678893,3.935281,52.351552;` | lanc-0196 |
| koteg-014 | 421 | k05.jpg | `Holga=1,49.395584,4.298524,95.564966;` | lanc-0105 |
| koteg-014 | 421 | k06.jpg | `ansel=1,ff2580a0;` | lanc-0196 |
| koteg-015 | 422 | k05.jpg | `IR=1,58.632346;` | lanc-0105 |
| koteg-015 | 422 | k06.jpg | `blur=1,0.471994;` | lanc-0196 |
| koteg-016 | 423 | k05.jpg | `contrast=1,0.357453;` | lanc-0105 |
| koteg-016 | 423 | k06.jpg | `dir_sharp=1,-0.326623,0.790902;` | lanc-0196 |
| koteg-017 | 424 | k05.jpg | `triple2=1,0.794439,0.822413,0.416504;` | lanc-0105 |
| koteg-017 | 424 | k06.jpg | `triple2=1,0.632434,0.867620,0.690895;` | lanc-0196 |
| koteg-018 | 425 | k05.jpg | `CrossProcess=1,58.866455;` | lanc-0175 |
| koteg-019 | 426 | k05.jpg | `LocalContrast=1,2.946479,1.789300;` | lanc-0175 |
| koteg-020 | 427 | k05.jpg | `Matte=1,20.730945,1.532521,86.826862,005f3295;` | lanc-0175 |
| koteg-021 | 428 | k05.jpg | `Neon=1,9.673465,00d24fdc;` | lanc-0175 |
| koteg-022 | 429 | k05.jpg | `PicnikFocalPixelate=1,0.423806,0.517357,68.995914,38.741837,79.479973,40.691224,0;` | lanc-0175 |
| koteg-023 | 430 | k05.jpg | `whitept=1,ff58c424;` | lanc-0175 |

## Láncok szerinti lefedettség

Melyik lánc melyik hiányzó tagját melyik issue méri. A láncon belül minden tag külön feladatba kerül, mert a lánc minden tagja ugyanazon a képen van.

| Lánc | Kép | Hiányzó tag | Már mért tag | Kizárt szemcse | Issue-k | Teljes ennyi köteg után |
|---|---|---:|---:|---:|---|---:|
| lanc-0005 | k05.jpg | 3 | 3 | 0 | 408, 409, 410 | 3 |
| lanc-0010 | k10.jpg | 2 | 0 | 1 | 410, 411 | 4 |
| lanc-0022 | k02.jpg | 4 | 0 | 0 | 411, 412, 413, 414 | 7 |
| lanc-0043 | k03.jpg | 2 | 0 | 2 | 408, 409 | 2 |
| lanc-0048 | k08.jpg | 2 | 0 | 0 | 408, 409 | 2 |
| lanc-0056 | k06.jpg | 2 | 3 | 0 | 408, 409 | 2 |
| lanc-0060 | k10.jpg | 2 | 0 | 1 | 412, 413 | 6 |
| lanc-0065 | k05.jpg | 3 | 0 | 1 | 411, 412, 413 | 6 |
| lanc-0067 | k07.jpg | 3 | 0 | 0 | 408, 409, 410 | 3 |
| lanc-0080 | k10.jpg | 1 | 1 | 0 | 408 | 1 |
| lanc-0088 | k08.jpg | 4 | 0 | 0 | 412, 413, 414, 415 | 8 |
| lanc-0089 | k09.jpg | 3 | 1 | 0 | 410, 411, 412 | 5 |
| lanc-0095 | k05.jpg | 4 | 0 | 0 | 417, 418, 419, 420 | 13 |
| lanc-0101 | k01.jpg | 2 | 4 | 0 | 408, 409 | 2 |
| lanc-0105 | k05.jpg | 4 | 0 | 0 | 421, 422, 423, 424 | 17 |
| lanc-0113 | k03.jpg | 3 | 3 | 0 | 410, 411, 412 | 5 |
| lanc-0115 | k05.jpg | 3 | 0 | 1 | 414, 415, 416 | 9 |
| lanc-0116 | k06.jpg | 6 | 0 | 0 | 413, 414, 415, 416, 417, 418 | 11 |
| lanc-0117 | k07.jpg | 4 | 0 | 1 | 411, 412, 413, 414 | 7 |
| lanc-0119 | k09.jpg | 3 | 0 | 1 | 413, 414, 415 | 8 |
| lanc-0124 | k04.jpg | 4 | 0 | 1 | 409, 410, 411, 412 | 5 |
| lanc-0140 | k10.jpg | 4 | 0 | 1 | 414, 415, 416, 417 | 10 |
| lanc-0142 | k02.jpg | 3 | 0 | 1 | 408, 409, 410 | 3 |
| lanc-0144 | k04.jpg | 1 | 3 | 0 | 408 | 1 |
| lanc-0169 | k09.jpg | 2 | 0 | 1 | 408, 409 | 2 |
| lanc-0175 | k05.jpg | 6 | 0 | 0 | 425, 426, 427, 428, 429, 430 | 23 |
| lanc-0178 | k08.jpg | 2 | 2 | 0 | 410, 411 | 4 |
| lanc-0186 | k06.jpg | 3 | 0 | 0 | 410, 411, 412 | 5 |
| lanc-0190 | k10.jpg | 1 | 3 | 0 | 409 | 2 |
| lanc-0196 | k06.jpg | 6 | 0 | 0 | 419, 420, 421, 422, 423, 424 | 17 |

## Hex-színnel kezdődő `colorfix` esetek

A besoroló lap "Adatminőségi megjegyzés" szakasza szerint a #6617 előtti `colorfix=1,<hex szín>,<hőmérséklet>` alakot az eredeti Picasa figyelmen kívül hagyja, a PicasaPy régi mentésként alkalmazza. Ezekhez a tagokhoz is kértem egyszűrős mérést, hogy a besorolás a pontos paraméterre is mérésből álljon, de az eredményüket ennek tudatában kell olvasni: a #6617 mérése (job-407) szerint az eredeti ezt az alakot figyelmen kívül hagyja.

| Issue | Kép | Szűrő | Lánc |
|---:|---|---|---|
| 408 | k01.jpg | `colorfix=1,ff2739b2,-0.326245;` | lanc-0101 |
| 408 | k04.jpg | `colorfix=1,ff3de652,0.486719;` | lanc-0144 |
| 408 | k05.jpg | `colorfix=1,ff680664,-0.249688;` | lanc-0005 |
| 408 | k10.jpg | `colorfix=1,ff773aed,0.352651;` | lanc-0080 |
| 409 | k05.jpg | `colorfix=1,ffc0ea7e,-0.140316;` | lanc-0005 |
| 409 | k10.jpg | `colorfix=1,ffccfb8f,-0.256467;` | lanc-0190 |
| 411 | k04.jpg | `colorfix=1,ff50b5af,-0.481740;` | lanc-0124 |
| 411 | k06.jpg | `colorfix=1,ff789687,0.154606;` | lanc-0186 |

## Amit nem kértem, és miért

- **Véletlen szemcse-tagok (12 db):** `grain`, `grain2`, `PicnikGrain`. A besorolás őket a pixelmérésből eleve kizárta (véletlen szemcse), ezért nem kértem újra. Az érintett láncok: lanc-0010 (1), lanc-0043 (2), lanc-0060 (1), lanc-0065 (1), lanc-0115 (1), lanc-0117 (1), lanc-0119 (1), lanc-0124 (1), lanc-0140 (1), lanc-0142 (1), lanc-0169 (1).
- **Már mért tagok (23 db):** a 400-406. issue azonos képen, azonos paraméterrel mért eseteit nem ismételtem.
- **A 407. issue (#6617) `colorfix`-sorai:** más paraméterű változatok, láncbeli taghoz nem tartoznak.

## Következő lépés

Amikor a 408-430. issue `allapot:kesz` lesz, az `export/` mellékleteket a `job-<szám>` kiadásokból le kell tölteni (`eszkozok/colab_eredmeny.py`), az egyes tagokat a PicasaPy jelenlegi kódjával ugyanazon a forrásképen, ugyanazzal a szűrősorral renderelni, és a `tools/golden/compare_render.py` küszöbeivel összevetni. Utána a 30 lánc "c" besorolása újraértékelhető: ha minden mért tag egyezik, de a lánc eltér, az "b" (kölcsönhatás); ha valamelyik tag önállóan eltér, az "a".
