# #6585 - A 30 eldöntetlen szűrőlánc újrabesorolása az új egyszűrős mérésekkel

**Mérés dátuma:** 2026-11-08  
**PicasaPy-kód:** `97933fe21226ccbbe1bc32117d574f6ba3b40b5b` (a render-kód azonos a jelenlegi `origin/main`-nel, attól csak a CHANGELOG, a verziószám és egy specifikációs lap tér el)  
**Kiinduló lapok:** `docs/benchmarks/2026-11-08-6585-differencialis-lanc-besorolas.md` (a 32 eltérő lánc, az a/b/c szabály), `docs/benchmarks/2026-11-08-6585-egyszuros-potmeres.md` (a 92 hiányzó egyszűrős eset, a 408-430. Colab-feladat)

## Eredmény dióhéjban

| Új besorolás | Db | Láncok |
|---|---:|---|
| **a** - legalább egy tag önállóan is eltér | 12 | `lanc-0022`, `lanc-0048`, `lanc-0067`, `lanc-0088`, `lanc-0095`, `lanc-0105`, `lanc-0115`, `lanc-0116`, `lanc-0124`, `lanc-0142`, `lanc-0175`, `lanc-0196` |
| **b** - minden tag egyezik, a lánc mégis eltér | 5 | `lanc-0005`, `lanc-0056`, `lanc-0089`, `lanc-0113`, `lanc-0178` |
| **c** - nem dönthető el, a szemcse-tag egyszűrős mérése hiányzik | 8 | `lanc-0010`, `lanc-0043`, `lanc-0060`, `lanc-0065`, `lanc-0117`, `lanc-0119`, `lanc-0140`, `lanc-0169` |
| **d** - adat-műtermék, a hex-színes `colorfix` okozza az eltérést | 5 | `lanc-0080`, `lanc-0101`, `lanc-0144`, `lanc-0186`, `lanc-0190` |
| **Összesen** | **30** | |

A "d" kategória új: a besoroló lap a/b/c szabálya nem számolt azzal, hogy az eredeti Picasa a hex-színnel kezdődő `colorfix`-et figyelmen kívül hagyja. A "d" láncok eltérését kizárólag ez okozza: a `colorfix` tagot elhagyva a lánc egyezik az eredetivel. Ezek nem renderelési hibák, és nem kölcsönhatások.

Fő megállapítások (mind mérésből):

1. **Két szűrő okozza az "a" eseteket.** A `PicnikFocalPixelate` 9 mért esetből 8-ban eltér (8 lánc), a `triple2` 7 mért esetből 5-ben (4 új lánc, plusz a már ismert `lanc-0052`). Másik szűrő a 92 pótmérésben nem tért el önállóan (a hex-színes `colorfix` kivételével, lásd a 2. pontot).
2. **A 8 hex-színes `colorfix` pótmérés mind eltér, de nem hiba.** Mind a 8 esetnél (és a korábbi `job-400/k02` esetnél is) az eredeti export pixelre azonos a szűrő nélküli forrásképpel (SSIM 1.00000, ΔE 0.000): az eredeti figyelmen kívül hagyja a szűrőt.
3. **A véletlen szemcse nem mérési akadály.** A 200 láncból 30 tartalmaz szemcsét (`grain`, `grain2`, `PicnikGrain`), és ebből 19 egyezik az eredetivel (közte `lanc-0007`: SSIM 1.00000, ΔE 0.000). A szemcse tehát legalább ezekben a láncokban pixelre reprodukálható: a "c" ok nem a véletlen, hanem a hiányzó egyszűrős szemcse-mérés, és ez 2 Colab-feladattal pótolható (lásd lent).
4. **A `lanc-0052` "a" marad, de más okból.** A korábbi bizonyíték egyik fele (`colorfix`) adat-műtermék volt; az "a" besorolást a `triple2` önálló eltérése (`job-403/k02`: SSIM 0.85067, ΔE 1.201) viszi. A `lanc-0045` "b" marad.

## Adat és módszer

**Forrásképek.** A k01-k10 a `sanchomuzax/picasa-colab-jobs` `kellekek` kiadásának `minta-kombinalt.tar.gz` fájlja (ez a `kombinalt` mintakészlet, amelyet a Colab-gép használ; a SHA256 egyezik a kiadás `SHA256SUMS` fájljával: `eaebec870e698433cb62a56c54e0c256c6752692de87101614ca403d071d5557`). A `meroadat.tar` ezeket nem tartalmazza. A névjegyzék a tíz kép nevéből és bájtméretéből készült.

**Rekordok.** Mindhárom csoport rekordjait a Colab-feladatok törzséből olvastam ki (`picasa_ini_be`), miután ellenőriztem, hogy minden feladat szerzője a saját GitHub-botunk. Az eredmény-állapotot a `colab_eredmeny.py` adta (mind a 380-430. feladat `kesz`), a képek a `job-<szám>` kiadások mellékletei (`export__k01.jpg`-`export__k10.jpg`).

| Csoport | Feladatok | Rekord | Tartalom |
|---|---|---:|---|
| `r6585i` | 380-399 | 200 | a 200 véletlen lánc (`lanc-0001`-`lanc-0200`) |
| `r6585f` | 400-406 | 64 | az egyszűrős alapmérés |
| `r6585p` | 408-430 | 92 | az egyszűrős pótmérés (`pot-<köteg>-<kép>`) |
| `r6585k` | (az `r6585i` eredeti exportjai) | 8 | a 8 hex-színes `colorfix`-es lánc a `colorfix` tag(ok) nélkül |

A rekordokat gépileg összevetettem a két kiinduló lap tábláival: a 32 eltérő lánc `filters=` értéke és a 92 pótmérés-eset (feladat, kép, pontos szűrősor) mind egyezik, 0 eltéréssel.

**Küszöb és összevetés.** Változatlanul a `tools/golden/compare_render.py` `Thresholds()` értéke (`pixel_tol=1`, `frac_tol=0.002`, `ssim_min=0.98`, `de_mean_max=2.0`), a saját kép az eredeti JPEG mintavételezésével és kvantálótábláival újrakódolva. Az `egyezik` a `pixelhű` vagy `közelítés` ítéletet jelenti.

```sh
python3 scripts/differencialis_lanc.py sajat --be .bt/meres/<csoport> --nevjegyzek .bt/meres/kombinalt/nevjegyzek.json --kepek .bt/meres/kombinalt/kepek
python3 scripts/differencialis_lanc.py osszevet --be .bt/meres/<csoport> --eredeti .bt/meres/<csoport>/eredeti
```

Az `eredeti/koteg-NNN` mappák a megfelelő `job-<szám>` mappákra mutatnak (`r6585i`: 379+N, `r6585f`: 399+N, `r6585p`: 407+N).

**Kontrollmérés (ugyanazzal a kóddal újramérve).**

| Kontroll | Várt (a kiinduló lapról) | Mért |
|---|---|---|
| 200 lánc | 168 egyezik, 32 eltér | 168 egyezik, 32 eltér; mind a 200 sor SSIM-je, ΔE-je és ítélete azonos a lapéval |
| 64 egyszűrős eset | 61 egyezik, 3 eltér | 61 egyezik, 3 eltér (`job-400/k02` `colorfix`, `job-403/k02` `triple2`, `job-405/k03` `PencilSketch`) |

A 3 eltérő egyszűrős eset ugyanaz, mint a kiinduló lap `egy-001`, `egy-004`, `egy-061` azonosítójú sora (az SSIM és ΔE értékek egyeznek); ebben a lapban a feladatszámmal és a képpel hivatkozom rájuk (`job-<szám>/kNN`), mert a régi `egy-NNN` számozás nem rekonstruálható a feladat-törzsekből.

## A 92 pótmérés eredménye

A 92 esetből **72 egyezik, 20 eltér** (kihagyott, hibás vagy hiányzó: 0). Az eltérések:

| Szűrő | Eltérő eset | Megjegyzés |
|---|---:|---|
| hex-színnel kezdődő `colorfix` | 8 | adat-műtermék: az eredeti figyelmen kívül hagyja (lásd lent) |
| `PicnikFocalPixelate` | 8 | valódi eltérés, "a" |
| `triple2` | 4 | valódi eltérés, "a" |

## A 30 lánc új besorolása

A "Régi" oszlop mindenhol `c` (a besoroló lap szerint). A lánc SSIM-je és ΔE-je a kiinduló lapról való, a kontrollmérés szerint azonos az újramért értékkel.

| Lánc | Kép | Lánc SSIM | Lánc ΔE | Régi | Új | Indoklás |
|---|---|---:|---:|:---:|:---:|---|
| lanc-0005 | k05.jpg | 0.76627 | 29.271 | c | **b** | mind a 4 mért tag egyezik; a hex-színes `colorfix` nélkül is eltér (SSIM 0.97912, ΔE 1.006) |
| lanc-0010 | k10.jpg | 0.84817 | 2.624 | c | **c** | a többi tag egyezik; szemcse-tag egyszűrős mérése hiányzik: `grain2=1;` |
| lanc-0022 | k02.jpg | 0.93721 | 3.036 | c | **a** | `PicnikFocalPixelate` önállóan eltér (job-411/k02: SSIM 0.95955, ΔE 2.272) |
| lanc-0043 | k03.jpg | 0.76992 | 2.031 | c | **c** | a többi tag egyezik; szemcse-tag egyszűrős mérése hiányzik: `PicnikGrain=1,9.856920,1;`, `grain2=1;` |
| lanc-0048 | k08.jpg | 0.94329 | 2.260 | c | **a** | `PicnikFocalPixelate` önállóan eltér (job-408/k08: SSIM 0.94671, ΔE 2.150) |
| lanc-0056 | k06.jpg | 0.99329 | 2.636 | c | **b** | mind a 5 mért tag egyezik |
| lanc-0060 | k10.jpg | 0.86391 | 2.067 | c | **c** | a többi tag egyezik; szemcse-tag egyszűrős mérése hiányzik: `grain2=1;` |
| lanc-0065 | k05.jpg | 0.92529 | 2.177 | c | **c** | a többi tag egyezik; szemcse-tag egyszűrős mérése hiányzik: `grain2=1;` |
| lanc-0067 | k07.jpg | 0.90360 | 3.180 | c | **a** | `PicnikFocalPixelate` önállóan eltér (job-410/k07: SSIM 0.93147, ΔE 1.238) |
| lanc-0080 | k10.jpg | 0.80866 | 91.311 | c | **d** | a hex-színes `colorfix` nélkül egyezik (SSIM 1.00000, ΔE 0.000) |
| lanc-0088 | k08.jpg | 0.93046 | 1.515 | c | **a** | `PicnikFocalPixelate` önállóan eltér (job-413/k08: SSIM 0.95864, ΔE 2.259) |
| lanc-0089 | k09.jpg | 0.98587 | 2.142 | c | **b** | mind a 4 mért tag egyezik |
| lanc-0095 | k05.jpg | 0.65876 | 1.011 | c | **a** | `triple2` önállóan eltér (job-420/k05: SSIM 0.73324, ΔE 1.181) |
| lanc-0101 | k01.jpg | 0.97000 | 49.235 | c | **d** | a hex-színes `colorfix` nélkül egyezik (SSIM 0.99637, ΔE 0.554) |
| lanc-0105 | k05.jpg | 0.95417 | 3.585 | c | **a** | `triple2` önállóan eltér (job-424/k05: SSIM 0.96714, ΔE 1.815) |
| lanc-0113 | k03.jpg | 0.97662 | 0.824 | c | **b** | mind a 6 mért tag egyezik |
| lanc-0115 | k05.jpg | 0.88714 | 3.408 | c | **a** | `PicnikFocalPixelate` önállóan eltér (job-414/k05: SSIM 0.90572, ΔE 3.135) |
| lanc-0116 | k06.jpg | 0.76752 | 0.881 | c | **a** | `triple2` önállóan eltér (job-417/k06: SSIM 0.81518, ΔE 1.137) |
| lanc-0117 | k07.jpg | 0.95824 | 1.639 | c | **c** | a többi tag egyezik; szemcse-tag egyszűrős mérése hiányzik: `grain2=1;` |
| lanc-0119 | k09.jpg | 0.95999 | 1.077 | c | **c** | a többi tag egyezik; szemcse-tag egyszűrős mérése hiányzik: `grain=1;` |
| lanc-0124 | k04.jpg | 0.89940 | 11.270 | c | **a** | `PicnikFocalPixelate` önállóan eltér (job-409/k04: SSIM 0.94045, ΔE 2.993) |
| lanc-0140 | k10.jpg | 0.90142 | 2.564 | c | **c** | a többi tag egyezik; szemcse-tag egyszűrős mérése hiányzik: `grain=1;` |
| lanc-0142 | k02.jpg | 0.94643 | 2.437 | c | **a** | `PicnikFocalPixelate` önállóan eltér (job-408/k02: SSIM 0.97293, ΔE 2.150) |
| lanc-0144 | k04.jpg | 0.83592 | 62.688 | c | **d** | a hex-színes `colorfix` nélkül egyezik (SSIM 0.98691, ΔE 0.864) |
| lanc-0169 | k09.jpg | 0.91502 | 2.178 | c | **c** | a többi tag egyezik; szemcse-tag egyszűrős mérése hiányzik: `grain=1;` |
| lanc-0175 | k05.jpg | 0.97040 | 3.666 | c | **a** | `PicnikFocalPixelate` önállóan eltér (job-429/k05: SSIM 0.96717, ΔE 3.172) |
| lanc-0178 | k08.jpg | 0.99218 | 3.003 | c | **b** | mind a 4 mért tag egyezik |
| lanc-0186 | k06.jpg | 0.97919 | 1.075 | c | **d** | a hex-színes `colorfix` nélkül egyezik (SSIM 1.00000, ΔE 0.000) |
| lanc-0190 | k10.jpg | 0.98653 | 37.440 | c | **d** | a hex-színes `colorfix` nélkül egyezik (SSIM 0.99127, ΔE 1.061) |
| lanc-0196 | k06.jpg | 0.86683 | 0.473 | c | **a** | `triple2` önállóan eltér (job-424/k06: SSIM 0.85903, ΔE 1.099) |

## Az "a" esetek szűrőnként

### `PicnikFocalPixelate` (8 lánc, 9 mért esetből 8 eltér)

Paraméterek az ini sorrendjében: Center X, Center Y, Impact, Radius, Edge Hardness, Fade, Reverse (a Radius, Edge Hardness és Fade az ini-ben 0-100 skálán áll). Kód: `src/picasapy/render/focal.py`, `effects_artistic.py`.

| Lánc | Feladat/kép | Center X | Center Y | Impact | Radius | Edge Hardness | Fade | Rev. | SSIM | ΔE átlag | Eredmény |
|---|---|---:|---:|---:|---:|---:|---:|:---:|---:|---:|---|
| lanc-0142 | job-408/k02 | 0.698914 | 0.945061 | 42.726991 | 31.797369 | 60.493888 | 63.244677 | 0 | 0.97293 | 2.150 | eltér |
| lanc-0048 | job-408/k08 | 0.754539 | 0.257084 | 5.226035 | 44.746379 | 30.137856 | 45.902113 | 0 | 0.94671 | 2.150 | eltér |
| lanc-0124 | job-409/k04 | 0.457857 | 0.092015 | 36.231898 | 86.737197 | 46.345083 | 4.704272 | 0 | 0.94045 | 2.993 | eltér |
| lanc-0067 | job-410/k07 | 0.379377 | 0.280311 | 5.110434 | 52.012805 | 56.186495 | 22.578563 | 0 | 0.93147 | 1.238 | eltér |
| lanc-0022 | job-411/k02 | 0.596101 | 0.315251 | 38.262959 | 67.621441 | 30.602824 | 38.221530 | 0 | 0.95955 | 2.272 | eltér |
| lanc-0088 | job-413/k08 | 0.257873 | 0.777093 | 18.371648 | 16.955073 | 83.975403 | 36.162119 | 0 | 0.95864 | 2.259 | eltér |
| lanc-0115 | job-414/k05 | 0.734580 | 0.362004 | 35.565019 | 64.583751 | 83.643288 | 11.843983 | 0 | 0.90572 | 3.135 | eltér |
| lanc-0175 | job-429/k05 | 0.423806 | 0.517357 | 68.995914 | 38.741837 | 79.479973 | 40.691224 | 0 | 0.96717 | 3.172 | eltér |
| lanc-0190 | job-403/k10 | 0.188181 | 0.532512 | 6.176970 | 4.362248 | 97.625661 | 23.072798 | 0 | 0.99282 | 0.683 | egyezik |

Az eltérő 8 esetben az SSIM 0.90572-0.97293, a ΔE átlag 1.238-3.172. Az egyetlen egyező eset (`job-403/k10`, `lanc-0190`) Radius paramétere a legkisebb (4.36 az ini 0-100 skáláján), ott az effekt a kép kis részére hat, ezért ez az egyezés gyenge bizonyíték arra, hogy a szűrő kis sugárral helyes. Az Impact, a Radius és az Edge Hardness mintában nem különíthető el, melyik paraméter okozza az eltérést: ehhez célzott paramétersöprés kell (egyszerre egy paraméter változik).

### `triple2` (Lighting Fixes v2, 4 új lánc és a `lanc-0052`; 7 mért esetből 5 eltér)

Paraméterek: Fill Light, Black Point, White Point. Kód: `src/picasapy/render/chain_native_handlers.py` (`apply_triple2_op`).

| Lánc | Feladat/kép | Fill Light | Black Point | White Point | SSIM | ΔE átlag | Eredmény |
|---|---|---:|---:|---:|---:|---:|---|
| lanc-0052 | job-403/k02 | 0.246858 | 0.780767 | 0.172505 | 0.85067 | 1.201 | eltér |
| lanc-0116 | job-417/k06 | 0.500244 | 0.837205 | 0.579954 | 0.81518 | 1.137 | eltér |
| lanc-0095 | job-420/k05 | 0.613640 | 0.987095 | 0.051496 | 0.73324 | 1.181 | eltér |
| lanc-0105 | job-424/k05 | 0.794439 | 0.822413 | 0.416504 | 0.96714 | 1.815 | eltér |
| lanc-0196 | job-424/k06 | 0.632434 | 0.867620 | 0.690895 | 0.85903 | 1.099 | eltér |
| lanc-0178 | job-411/k08 | 0.218250 | 0.303895 | 0.317896 | 0.99664 | 1.976 | egyezik |
| lanc-0089 | job-412/k09 | 0.127180 | 0.190318 | 0.055157 | 0.99442 | 1.195 | egyezik |

Az 5 eltérő esetben az SSIM 0.73324-0.96714, miközben a ΔE átlag csak 1.099-1.815: a különbség nem globális színeltolás, hanem szerkezeti (a hatás a kép egy részén jelentkezik). Az eltérő esetekben a Fill Light 0.247-0.794 és a Black Point 0.78-0.99; a két egyező esetben a Fill Light 0.127-0.218 és a Black Point 0.19-0.30. A két paraméter a mintában együtt jár, ezért a mérés nem dönti el, melyik okozza az eltérést. Az egyező két eset is csak `közelítés` (ΔE 1.976 és 1.195), nem `pixelhű`.

A `PencilSketch` egyik mért esete (`job-405/k03`, SSIM 0.97095, ΔE 0.982) szintén eltér, de ez nem tagja egyik eldöntetlen láncnak (a két láncbeli `PencilSketch` más paraméterrel `közelítés` szinten egyezik), ezért nem szerepel az "a" listában.

## A hex-színes `colorfix` (adat-műtermék)

A `colorfix=1,<hex szín>,<hőmérséklet>` alak a #6617 előtti sorrend. A besoroló lap szerint az eredeti ezt figyelmen kívül hagyja, a PicasaPy régi mentésként beolvassa és alkalmazza. Ezt most közvetlenül mértem: az eredeti export összevetése a **szűrő nélküli** forrásképpel (ugyanaz az összevetés, mint máshol):

| Feladat/kép | Szűrő | PicasaPy az eredetihez képest: SSIM / ΔE | Szűrő nélküli forrás az eredetihez képest | Lánc |
|---|---|---:|---|---|
| job-400/k02 | `colorfix=1,ffca3cff,-0.164578;` | 0.74630 / 115.147 | pixelhű (SSIM 1.00000, ΔE 0.000) | lanc-0052 |
| job-408/k01 | `colorfix=1,ff2739b2,-0.326245;` | 0.96972 / 61.217 | pixelhű (SSIM 1.00000, ΔE 0.000) | lanc-0101 |
| job-408/k04 | `colorfix=1,ff3de652,0.486719;` | 0.83952 / 71.099 | pixelhű (SSIM 1.00000, ΔE 0.000) | lanc-0144 |
| job-408/k05 | `colorfix=1,ff680664,-0.249688;` | 0.13656 / 143.314 | pixelhű (SSIM 1.00000, ΔE 0.000) | lanc-0005 |
| job-408/k10 | `colorfix=1,ff773aed,0.352651;` | 0.82572 / 92.261 | pixelhű (SSIM 1.00000, ΔE 0.000) | lanc-0080 |
| job-409/k05 | `colorfix=1,ffc0ea7e,-0.140316;` | 0.99682 / 38.285 | pixelhű (SSIM 1.00000, ΔE 0.000) | lanc-0005 |
| job-409/k10 | `colorfix=1,ffccfb8f,-0.256467;` | 0.99729 / 44.622 | pixelhű (SSIM 1.00000, ΔE 0.000) | lanc-0190 |
| job-411/k04 | `colorfix=1,ff50b5af,-0.481740;` | 0.94525 / 43.216 | pixelhű (SSIM 1.00000, ΔE 0.000) | lanc-0124 |
| job-411/k06 | `colorfix=1,ff789687,0.154606;` | 0.99613 / 17.717 | pixelhű (SSIM 1.00000, ΔE 0.000) | lanc-0186 |

Mind a 9 esetben az eredeti export pontosan a szűretlen kép. A PicasaPy ezzel szemben alkalmazza a szűrőt, innen a nagy eltérés. Ez a kettő közötti szándékos eltérés (régi mentések beolvasása, #6617), nem renderelési hiba; hogy ez így marad-e, termékdöntés, nem ennek a lapnak a tárgya.

**A 8 érintett lánc a `colorfix` tag(ok) nélkül.** A `colorfix` tagok elhagyásával (és csak azzal) újrarenderelt lánc az eredeti lánc-exporttal összevetve:

| Lánc | Eredeti lánc: SSIM / ΔE | `colorfix` nélkül: SSIM / ΔE | Ítélet | Besorolás |
|---|---:|---:|---|:---:|
| lanc-0005 | 0.76627 / 29.271 | 0.97912 / 1.006 | eltér | b |
| lanc-0052 | 0.41064 / 139.805 | 0.85688 / 1.153 | eltér | a |
| lanc-0080 | 0.80866 / 91.311 | 1.00000 / 0.000 | pixelhű | d |
| lanc-0101 | 0.97000 / 49.235 | 0.99637 / 0.554 | közelítés | d |
| lanc-0124 | 0.89940 / 11.270 | 0.92972 / 1.951 | eltér | a |
| lanc-0144 | 0.83592 / 62.688 | 0.98691 / 0.864 | közelítés | d |
| lanc-0186 | 0.97919 / 1.075 | 1.00000 / 0.000 | pixelhű | d |
| lanc-0190 | 0.98653 / 37.440 | 0.99127 / 1.061 | közelítés | d |

Öt lánc a `colorfix` nélkül egyezik ("d"). A `lanc-0005` a `colorfix` nélkül is eltér ("b"), a `lanc-0052` és a `lanc-0124` pedig a `triple2`, illetve a `PicnikFocalPixelate` miatt ("a").

## A "b" esetek

A "b" a lap szabálya szerint: minden tag önállóan egyezik, a lánc mégis eltér, tehát a mérés kölcsönhatást támaszt alá. Fontos korlát: az "egyezik" tűréssel értendő (`közelítés`: SSIM >= 0.98 és ΔE <= 2.0), ezért a tagonkénti kis eltérések a láncban összeadódhatnak. A tájékoztató oszlop a tagok mért ΔE-inek számtani összegét mutatja (nem korlát, a ΔE nem additív): ha a lánc ΔE-je ennél nagyobb, az összeadódás önmagában kevésbé valószínű magyarázat.

| Lánc | Lánc SSIM / ΔE | Leggyengébb tag | Tagok ΔE-összege | Megjegyzés |
|---|---:|---|---:|---|
| lanc-0005 | 0.97912 / 1.006 (a hex-színes `colorfix` nélkül mérve) | `rainbow` (job-410/k05: SSIM 0.98329, ΔE 1.312) | 1.319 | az összeadódás nem zárható ki |
| lanc-0056 | 0.99329 / 2.636 | `rainbow` (job-408/k06: SSIM 0.99428, ΔE 0.853) | 1.340 | a lánc ΔE-je meghaladja a tagok összegét |
| lanc-0089 | 0.98587 / 2.142 | `triple2` (job-412/k09: SSIM 0.99442, ΔE 1.195) | 1.504 | a lánc ΔE-je meghaladja a tagok összegét; `triple2` tagot tartalmaz, a `triple2` javítása után újramérendő |
| lanc-0113 | 0.97662 / 0.824 | `radsat` (job-400/k03: SSIM 0.99950, ΔE 0.078) | 0.086 | a lánc ΔE-je meghaladja a tagok összegét |
| lanc-0178 | 0.99218 / 3.003 | `triple2` (job-411/k08: SSIM 0.99664, ΔE 1.976) | 3.061 | az összeadódás nem zárható ki; `triple2, triple3` tagot tartalmaz, a `triple2` javítása után újramérendő |

A `lanc-0045` (az eredeti "b") tagjai mind `pixelhű` egyezést adtak, a lánc ΔE-je 93.951: ez a legerősebb kölcsönhatás-bizonyíték. A fenti öt új "b" gyengébb: a `lanc-0005` és a `lanc-0178` esetében a tagonkénti tűrés összege eléri a lánc eltérését.

## A "c" esetek: mi hiányzik

A 8 "c" lánc mindegyike tartalmaz szemcse-tagot (`grain`, `grain2`, `PicnikGrain`), amelynek egyszűrős mérését a pótmérésből szándékosan kihagytuk a "véletlen szemcse" feltevés miatt. Ez a feltevés nem áll: a 200 láncból 30 tartalmaz szemcsét, ebből 19 egyezik az eredetivel, közte `lanc-0007` (kétműveletes, `PicnikGrain`: SSIM 1.00000, ΔE 0.000), `lanc-0053`, `lanc-0078`, `lanc-0085`, `lanc-0138`, `lanc-0198` (mind SSIM 1.00000, ΔE 0.000). A magas frekvenciás zaj szórása (a kép és a σ=3 px-szel elmosott változata különbségének szórása) a saját és az eredeti képen azonos: a saját/eredeti arány a 8 "c" láncnál 0.999-1.001, a 168 egyező láncnál 0.975-1.011.

| Lánc | Kép | Lánc SSIM | Lánc ΔE | Egyező képpont | 2 szintnél nem nagyobb eltérés | 8 szintnél nagyobb eltérés | Elmosott kép ΔE | Szemcse-tag |
|---|---|---:|---:|---:|---:|---:|---:|---|
| lanc-0010 | k10.jpg | 0.84817 | 2.624 | 2.9% | 21.4% | 28.8% | 0.723 | `grain2=1;` |
| lanc-0043 | k03.jpg | 0.76992 | 2.031 | 3.9% | 28.4% | 17.1% | 0.692 | `PicnikGrain=1,9.856920,1;`, `grain2=1;` |
| lanc-0060 | k10.jpg | 0.86391 | 2.067 | 32.1% | 42.9% | 23.8% | 0.558 | `grain2=1;` |
| lanc-0065 | k05.jpg | 0.92529 | 2.177 | 8.7% | 32.8% | 22.1% | 0.321 | `grain2=1;` |
| lanc-0117 | k07.jpg | 0.95824 | 1.639 | 12.0% | 51.4% | 4.8% | 0.879 | `grain2=1;` |
| lanc-0119 | k09.jpg | 0.95999 | 1.077 | 18.6% | 69.4% | 2.0% | 0.497 | `grain=1;` |
| lanc-0140 | k10.jpg | 0.90142 | 2.564 | 3.7% | 22.9% | 24.9% | 0.673 | `grain=1;` |
| lanc-0169 | k09.jpg | 0.91502 | 2.178 | 3.7% | 28.1% | 16.1% | 0.753 | `grain=1;` |

Az elmosott (σ=3 px) kép ΔE-je a "c" láncoknál 0.321-0.879, a 168 egyező láncnál a medián 0.052, a maximum 0.865. Olvasat (nem bizonyíték): a durva szerkezet és a zaj szórása egyezik, de hat lánc képpontjainak 16-29%-a több mint 8 szinttel tér el, vagyis a szemcse mintázata vagy a szemcse és a szomszédos szűrő kölcsönhatása tér el. A mérés a szemcse önálló hibáját és a kölcsönhatást nem választja szét.

**Következő, felvehető irány:** a szemcse-tagok egyszűrős mérése. A 8 láncban 9 szemcse-tag van, ebből 7 egyedi (kép, szűrő) pár, mert a feladatban képenként egyetlen `filters=` sor lehet, ez 2 Colab-feladat:

| Feladat | Kép | Szűrő | Láncok |
|---|---|---|---|
| A | k03.jpg | `PicnikGrain=1,9.856920,1;` | lanc-0043 |
| A | k05.jpg | `grain2=1;` | lanc-0065 |
| A | k07.jpg | `grain2=1;` | lanc-0117 |
| A | k09.jpg | `grain=1;` | lanc-0119, lanc-0169 |
| A | k10.jpg | `grain2=1;` | lanc-0010, lanc-0060 |
| B | k03.jpg | `grain2=1;` | lanc-0043 |
| B | k10.jpg | `grain=1;` | lanc-0140 |

(9 szemcse-tag, 7 egyedi pár; a `lanc-0010` és a `lanc-0060` közös `grain2=1;` esete a `k10`-en, a `lanc-0119` és a `lanc-0169` közös `grain=1;` esete a `k09`-en egyszer mérendő.) Ezt a lap nem adta fel; a feladás a hívó dolga.

## A korábbi "a" és "b" lánc

| Lánc | Besorolás | Változás |
|---|:---:|---|
| `lanc-0045` | b | nem változott: mind a 4 tag `pixelhű`, a lánc eltér (SSIM 0.43336, ΔE 93.951) |
| `lanc-0052` | a | megmaradt, de a bizonyíték megváltozott: a `colorfix` tag (`job-400/k02`) adat-műtermék, az "a" besorolást a `triple2` (`job-403/k02`: SSIM 0.85067, ΔE 1.201) viszi |

## Tagonkénti mérés

A 30 lánc minden tagja. A szemcse-tagoknak nincs egyszűrős mérésük.

| Lánc | Kép | Tag | Feladat/kép | Ítélet | SSIM | ΔE átlag |
|---|---|---|---|---|---:|---:|
| lanc-0005 | k05.jpg | `radblur=1,0.889652,0.000892,-0.990090,-0.303163;` | job-404/k05 | egyezik (közelítés) | 0.99988 | 0.007 |
| lanc-0005 | k05.jpg | `colorfix=1,ffc0ea7e,-0.140316;` | job-409/k05 | eltér (adat-műtermék) | 0.99682 | 38.285 |
| lanc-0005 | k05.jpg | `colorfix=1,ff680664,-0.249688;` | job-408/k05 | eltér (adat-műtermék) | 0.13656 | 143.314 |
| lanc-0005 | k05.jpg | `LocalContrast=1,13.446470,1.197972;` | job-405/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0005 | k05.jpg | `rainbow=1,229.438578;` | job-410/k05 | egyezik (közelítés) | 0.98329 | 1.312 |
| lanc-0005 | k05.jpg | `Holga=1,63.516887,91.816275,29.159809;` | job-406/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0010 | k10.jpg | `PencilSketch=1,3.844177,163.752261,80.619866;` | job-410/k10 | egyezik (közelítés) | 0.99714 | 0.466 |
| lanc-0010 | k10.jpg | `grain2=1;` | - | szemcse, nem mért | - | - |
| lanc-0010 | k10.jpg | `backlight=1,0.015514;` | job-411/k10 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0022 | k02.jpg | `PicnikFocalPixelate=1,0.596101,0.315251,38.262959,67.621441,30.602824,38.221530,0;` | job-411/k02 | **eltér** | 0.95955 | 2.272 |
| lanc-0022 | k02.jpg | `dir_sat=1,0.570065,0.531207;` | job-412/k02 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0022 | k02.jpg | `unsharp2=1,1.889519;` | job-414/k02 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0022 | k02.jpg | `enhance=1;` | job-413/k02 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0043 | k03.jpg | `unsharp=1,0.429447;` | job-409/k03 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0043 | k03.jpg | `PicnikGrain=1,9.856920,1;` | - | szemcse, nem mért | - | - |
| lanc-0043 | k03.jpg | `grain2=1;` | - | szemcse, nem mért | - | - |
| lanc-0043 | k03.jpg | `TwoTone=1,-34.649025,42.816806,49.327950,00cc1cd3,00f3ee8e;` | job-408/k03 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0048 | k08.jpg | `autolight=1;` | job-409/k08 | egyezik (közelítés) | 0.99925 | 0.318 |
| lanc-0048 | k08.jpg | `PicnikFocalPixelate=1,0.754539,0.257084,5.226035,44.746379,30.137856,45.902113,0;` | job-408/k08 | **eltér** | 0.94671 | 2.150 |
| lanc-0056 | k06.jpg | `gamma=1,0.480449;` | job-400/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0056 | k06.jpg | `TwoTone=1,-27.961551,76.839183,9.626150,00227d84,003194d5;` | job-401/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0056 | k06.jpg | `linblur=1,0.466086,0.005391,9.064718;` | job-402/k06 | egyezik (közelítés) | 0.99985 | 0.018 |
| lanc-0056 | k06.jpg | `rainbow=1,244.890456;` | job-408/k06 | egyezik (közelítés) | 0.99428 | 0.853 |
| lanc-0056 | k06.jpg | `triple=1,-0.207838,-0.406449,0.214067;` | job-409/k06 | egyezik (közelítés) | 0.99306 | 0.469 |
| lanc-0060 | k10.jpg | `Vignette=1,48.277238,1.527099,84.880421,00c7828a;` | job-413/k10 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0060 | k10.jpg | `grain2=1;` | - | szemcse, nem mért | - | - |
| lanc-0060 | k10.jpg | `DropShadow=1,20.235157,164.620360,83.506034,007d27c2,009d04a2,3.158258;` | job-412/k10 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0065 | k05.jpg | `Boost=1,36.252043;` | job-411/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0065 | k05.jpg | `shadow=1,0.764285,0.655234,0.163184;` | job-413/k05 | egyezik (közelítés) | 0.99966 | 0.163 |
| lanc-0065 | k05.jpg | `grain2=1;` | - | szemcse, nem mért | - | - |
| lanc-0065 | k05.jpg | `ansel=1,ff25d557;` | job-412/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0067 | k07.jpg | `PicnikFocalPixelate=1,0.379377,0.280311,5.110434,52.012805,56.186495,22.578563,0;` | job-410/k07 | **eltér** | 0.93147 | 1.238 |
| lanc-0067 | k07.jpg | `Holga=1,27.444017,76.630990,12.639445;` | job-408/k07 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0067 | k07.jpg | `LocalContrast=1,18.977791,2.424472;` | job-409/k07 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0080 | k10.jpg | `colorfix=1,ff773aed,0.352651;` | job-408/k10 | eltér (adat-műtermék) | 0.82572 | 92.261 |
| lanc-0080 | k10.jpg | `unsharp=1,0.385234;` | job-400/k10 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0088 | k08.jpg | `PicnikFocalPixelate=1,0.257873,0.777093,18.371648,16.955073,83.975403,36.162119,0;` | job-413/k08 | **eltér** | 0.95864 | 2.259 |
| lanc-0088 | k08.jpg | `unsharp=1,0.811594;` | job-415/k08 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0088 | k08.jpg | `PencilSketch=1,2.433558,9.770045,31.821444;` | job-412/k08 | egyezik (közelítés) | 0.99242 | 0.517 |
| lanc-0088 | k08.jpg | `radtint=1,0.113828,0.081816,0.197103,ffe11e1b;` | job-414/k08 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0089 | k09.jpg | `IR=1,6.505770;` | job-410/k09 | egyezik (közelítés) | 0.99763 | 0.291 |
| lanc-0089 | k09.jpg | `radsat=1,0.935702,0.276913,-0.462013,0.789662;` | job-411/k09 | egyezik (közelítés) | 0.99999 | 0.018 |
| lanc-0089 | k09.jpg | `warm=1;` | job-402/k09 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0089 | k09.jpg | `triple2=1,0.127180,0.190318,0.055157;` | job-412/k09 | egyezik (közelítés) | 0.99442 | 1.195 |
| lanc-0095 | k05.jpg | `sepia=1;` | job-419/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0095 | k05.jpg | `ansel=1,ff06c7fb;` | job-417/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0095 | k05.jpg | `triple2=1,0.613640,0.987095,0.051496;` | job-420/k05 | **eltér** | 0.73324 | 1.181 |
| lanc-0095 | k05.jpg | `dir_sharp=1,-0.767675,0.017529;` | job-418/k05 | egyezik (közelítés) | 0.99974 | 0.187 |
| lanc-0101 | k01.jpg | `IR=1,54.049313;` | job-400/k01 | egyezik (közelítés) | 0.99811 | 0.595 |
| lanc-0101 | k01.jpg | `colorfix=1,ff2739b2,-0.326245;` | job-408/k01 | eltér (adat-műtermék) | 0.96972 | 61.217 |
| lanc-0101 | k01.jpg | `Soften=1,95.657333,30.076586;` | job-401/k01 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0101 | k01.jpg | `unsharp=1,0.559595;` | job-409/k01 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0101 | k01.jpg | `dir_tint=1,0.176344,0.148523,0.298786,0.227118,ff2d5a0f;` | job-402/k01 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0101 | k01.jpg | `autocontrast=1;` | job-403/k01 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0105 | k05.jpg | `IR=1,58.632346;` | job-422/k05 | egyezik (közelítés) | 0.99911 | 0.506 |
| lanc-0105 | k05.jpg | `contrast=1,0.357453;` | job-423/k05 | egyezik (közelítés) | 0.99740 | 0.813 |
| lanc-0105 | k05.jpg | `triple2=1,0.794439,0.822413,0.416504;` | job-424/k05 | **eltér** | 0.96714 | 1.815 |
| lanc-0105 | k05.jpg | `Holga=1,49.395584,4.298524,95.564966;` | job-421/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0113 | k03.jpg | `radsat=1,0.495786,0.199929,0.644282,0.226320;` | job-400/k03 | egyezik (közelítés) | 0.99950 | 0.078 |
| lanc-0113 | k03.jpg | `glow2=1,0.938053,7.426568;` | job-401/k03 | egyezik (közelítés) | 0.99999 | 0.008 |
| lanc-0113 | k03.jpg | `HeatMap=1,-166.268420,33.668530;` | job-411/k03 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0113 | k03.jpg | `Sixties=1,24.277937,00831e27,0;` | job-402/k03 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0113 | k03.jpg | `HDR=1,25.214587,5.596100,24.480760;` | job-410/k03 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0113 | k03.jpg | `warm=1;` | job-412/k03 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0115 | k05.jpg | `glow=1,0.240375,86.608439;` | job-415/k05 | egyezik (közelítés) | 0.99996 | 0.030 |
| lanc-0115 | k05.jpg | `grain=1;` | - | szemcse, nem mért | - | - |
| lanc-0115 | k05.jpg | `PicnikFocalPixelate=1,0.734580,0.362004,35.565019,64.583751,83.643288,11.843983,0;` | job-414/k05 | **eltér** | 0.90572 | 3.135 |
| lanc-0115 | k05.jpg | `unsharp2=1,0.890722;` | job-416/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0116 | k06.jpg | `Soften=1,81.679116,95.722213;` | job-414/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0116 | k06.jpg | `glow=1,0.220319,29.085845;` | job-415/k06 | egyezik (közelítés) | 0.99998 | 0.028 |
| lanc-0116 | k06.jpg | `triple2=1,0.500244,0.837205,0.579954;` | job-417/k06 | **eltér** | 0.81518 | 1.137 |
| lanc-0116 | k06.jpg | `CrossProcess=1,22.173648;` | job-413/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0116 | k06.jpg | `unsharp2=1,0.973675;` | job-418/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0116 | k06.jpg | `sepia=1;` | job-416/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0117 | k07.jpg | `grain2=1;` | - | szemcse, nem mért | - | - |
| lanc-0117 | k07.jpg | `glow=1,0.943897,17.486931;` | job-413/k07 | egyezik (közelítés) | 0.99993 | 0.025 |
| lanc-0117 | k07.jpg | `HeatMap=1,-101.723152,46.384101;` | job-412/k07 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0117 | k07.jpg | `CrossProcess=1,1.191213;` | job-411/k07 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0117 | k07.jpg | `radblur=1,0.195302,0.408240,-0.055610,-0.967370;` | job-414/k07 | egyezik (közelítés) | 0.99976 | 0.016 |
| lanc-0119 | k09.jpg | `whitept=1,ff12141f;` | job-415/k09 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0119 | k09.jpg | `grain=1;` | - | szemcse, nem mért | - | - |
| lanc-0119 | k09.jpg | `Comicize=1,97.076368,83.882062,99.079918;` | job-413/k09 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0119 | k09.jpg | `Pixelate=1,72.192947,3.126227,5.346142;` | job-414/k09 | egyezik (közelítés) | 0.99858 | 0.106 |
| lanc-0124 | k04.jpg | `colorfix=1,ff50b5af,-0.481740;` | job-411/k04 | eltér (adat-műtermék) | 0.94525 | 43.216 |
| lanc-0124 | k04.jpg | `PicnikFocalPixelate=1,0.457857,0.092015,36.231898,86.737197,46.345083,4.704272,0;` | job-409/k04 | **eltér** | 0.94045 | 2.993 |
| lanc-0124 | k04.jpg | `autocontrast=1;` | job-410/k04 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0124 | k04.jpg | `radsat=1,0.466994,0.173746,0.209913,0.696717;` | job-412/k04 | egyezik (közelítés) | 0.99993 | 0.026 |
| lanc-0124 | k04.jpg | `grain2=1;` | - | szemcse, nem mért | - | - |
| lanc-0140 | k10.jpg | `HDR=1,65.299969,1.626753,76.860461;` | job-414/k10 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0140 | k10.jpg | `dir_sharp=1,-0.397475,0.968720;` | job-416/k10 | egyezik (közelítés) | 0.99976 | 0.327 |
| lanc-0140 | k10.jpg | `backlight=1,0.832331;` | job-415/k10 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0140 | k10.jpg | `warm=1;` | job-417/k10 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0140 | k10.jpg | `grain=1;` | - | szemcse, nem mért | - | - |
| lanc-0142 | k02.jpg | `PicnikFocalPixelate=1,0.698914,0.945061,42.726991,31.797369,60.493888,63.244677,0;` | job-408/k02 | **eltér** | 0.97293 | 2.150 |
| lanc-0142 | k02.jpg | `QuantizePalette=1,26.866748,28.222955,86.942047;` | job-409/k02 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0142 | k02.jpg | `triple3=1,0.554400,0.413470,0.290744;` | job-410/k02 | egyezik (közelítés) | 0.99617 | 0.489 |
| lanc-0142 | k02.jpg | `PicnikGrain=1,16.060125,1;` | - | szemcse, nem mért | - | - |
| lanc-0144 | k04.jpg | `rainbow=1,157.860004;` | job-400/k04 | egyezik (közelítés) | 0.98749 | 0.915 |
| lanc-0144 | k04.jpg | `HDR=1,18.018149,2.319506,99.392683;` | job-401/k04 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0144 | k04.jpg | `sat=1,-0.245977;` | job-402/k04 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0144 | k04.jpg | `colorfix=1,ff3de652,0.486719;` | job-408/k04 | eltér (adat-műtermék) | 0.83952 | 71.099 |
| lanc-0169 | k09.jpg | `autolight=1;` | job-409/k09 | egyezik (közelítés) | 0.99880 | 0.400 |
| lanc-0169 | k09.jpg | `autocolor=1;` | job-408/k09 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0169 | k09.jpg | `grain=1;` | - | szemcse, nem mért | - | - |
| lanc-0175 | k05.jpg | `LocalContrast=1,2.946479,1.789300;` | job-426/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0175 | k05.jpg | `whitept=1,ff58c424;` | job-430/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0175 | k05.jpg | `CrossProcess=1,58.866455;` | job-425/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0175 | k05.jpg | `Neon=1,9.673465,00d24fdc;` | job-428/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0175 | k05.jpg | `Matte=1,20.730945,1.532521,86.826862,005f3295;` | job-427/k05 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0175 | k05.jpg | `PicnikFocalPixelate=1,0.423806,0.517357,68.995914,38.741837,79.479973,40.691224,0;` | job-429/k05 | **eltér** | 0.96717 | 3.172 |
| lanc-0178 | k08.jpg | `triple3=1,0.218352,0.361045,0.311731;` | job-405/k08 | egyezik (közelítés) | 0.99806 | 1.085 |
| lanc-0178 | k08.jpg | `triple2=1,0.218250,0.303895,0.317896;` | job-411/k08 | egyezik (közelítés) | 0.99664 | 1.976 |
| lanc-0178 | k08.jpg | `dir_sat=1,0.037718,-0.414407;` | job-406/k08 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0178 | k08.jpg | `colortemp=1,-0.389167,0.612947;` | job-410/k08 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0186 | k06.jpg | `colorfix=1,ff789687,0.154606;` | job-411/k06 | eltér (adat-műtermék) | 0.99613 | 17.717 |
| lanc-0186 | k06.jpg | `ansel=1,ff3758f3;` | job-410/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0186 | k06.jpg | `unsharp2=1,1.569590;` | job-412/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0190 | k10.jpg | `autocolor=1;` | job-401/k10 | egyezik (közelítés) | 0.99900 | 0.614 |
| lanc-0190 | k10.jpg | `radtint=1,0.886560,0.666967,0.816773,ffb6ba2a;` | job-402/k10 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0190 | k10.jpg | `colorfix=1,ffccfb8f,-0.256467;` | job-409/k10 | eltér (adat-műtermék) | 0.99729 | 44.622 |
| lanc-0190 | k10.jpg | `PicnikFocalPixelate=1,0.188181,0.532512,6.176970,4.362248,97.625661,23.072798,0;` | job-403/k10 | egyezik (közelítés) | 0.99282 | 0.683 |
| lanc-0196 | k06.jpg | `ansel=1,ff2580a0;` | job-421/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0196 | k06.jpg | `blur=1,0.471994;` | job-422/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0196 | k06.jpg | `QuantizePalette=1,8.678893,3.935281,52.351552;` | job-420/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |
| lanc-0196 | k06.jpg | `dir_sharp=1,-0.326623,0.790902;` | job-423/k06 | egyezik (közelítés) | 0.99930 | 0.285 |
| lanc-0196 | k06.jpg | `triple2=1,0.632434,0.867620,0.690895;` | job-424/k06 | **eltér** | 0.85903 | 1.099 |
| lanc-0196 | k06.jpg | `CrossProcess=1,28.019592;` | job-419/k06 | egyezik (pixelhű) | 1.00000 | 0.000 |

## Korlátok

- A lánc-eltérések (SSIM, ΔE) a 200 láncos futásból valók; a kontroll szerint ugyanazzal a kóddal újramérve azonosak a kiinduló lapéval.
- A "b" besorolás tűréssel egyező tagokra épül; a mérés nem választja szét a valódi kölcsönhatást a tagonkénti tűrések összeadódásától.
- A "c" láncok eldöntéséhez 2 új Colab-feladat kell (7 egyedi szemcse-eset); ezt a lap nem adta fel.
- A pótmérés a 10 képen (k01-k10) és az adott paraméterekkel áll: a `PicnikFocalPixelate` és a `triple2` hibája egy-egy paraméterre szűkítéséhez további, célzott mérés kell.
- Az újrabesorolás segédszkriptjei (rekordépítés a feladat-törzsekből, tag-megfeleltetés, a `colorfix` nélküli láncok, a szemcse-kontroll) a munkafa ideiglenes mappájában készültek, a repóba nem kerültek; a használt parancsokat és szabályokat ez a lap rögzíti.
- Az eredeti Picasa-exportok JPEG-ként állnak rendelkezésre; az összevetés az újrakódolással együtt értendő, ahogy a kiinduló lap is rögzíti.
