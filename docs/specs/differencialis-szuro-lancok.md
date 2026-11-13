# Differenciális szűrőláncok: a #6585 öt „b” esetének minimalizálása

**Mérés dátuma:** 2026-11-08. **Cél:** az öt, egyenként egyező tagú, de láncként eltérő eset lokalizálása.

## Módszer és mérési állapot

Az eredeti JPEG-exportok a picasa-colab-jobs 435-445. feladatának `job-NNN` kiadásmellékletei; a forrásképek a `kombinalt` mintakészletből jöttek. A 42 jelölt pontos `filters` sorát a `jeloltek.json` adta; a helyi render és összevetés a meglévő parancsokkal futott:

```sh
python3 scripts/differencialis_lanc.py sajat --be .tmp/meres/minimalizalas/futtatas --nevjegyzek .tmp/meres/minimalizalas/futtatas/kepek.json --kepek .tmp/meres/minimalizalas/forras
python3 scripts/differencialis_lanc.py osszevet --be .tmp/meres/minimalizalas/futtatas --eredeti .tmp/meres/minimalizalas/eredeti
```

Az összevetés a `tools/golden/compare_render.py` alapértelmezett `Thresholds()` értékeit használta: `pixel_tol=1`, `frac_tol=0.002`, `ssim_min=0.98`, `de_mean_max=2.0`. A saját RGB-rendert a megfelelő Picasa-JPEG mintavételezésével és kvantálótábláival újrakódolta, majd a dekódolt képet mérte. **42/42** jelölt renderelődött; **31 egyezik, 11 eltér**, 0 kihagyott szűrő, hiányzó vagy hibás export. Az `egyezik` a `pixelhű` vagy `közelítés` ítéletet jelenti.

Az öt teljes lánc kiinduló eredménye az [újrabesorolási mérés](../benchmarks/2026-11-08-6585-ujrabesorolas.md): 0005 `0.76627 / 29.271` (hex-színes, az eredeti által figyelmen kívül hagyott `colorfix`-szel), 0056 `0.99329 / 2.636`, 0089 `0.98587 / 2.142`, 0113 `0.97662 / 0.824`, 0178 `0.99218 / 3.003`. A `lanc-0005-teljes-colorfix-nelkul` jelölt külön kontroll a colorfix nélküli láncot méri: `0.97912 / 1.006`, továbbra is `eltér` az SSIM-küszöb miatt.

## Minden jelölt eredménye

Az „elhagyva” jelöltek a megadott tagot vették ki az eredeti sorrendből. A `pár` jelöltek csak a szomszédos tagpárt tartották meg. A `filters=` oszlop a PicasaPy által renderelt pontos sor; az értékeket nem szerializáltuk újra.

| Jelölt | Kihagyás / megtartott változat | `filters=` | SSIM | ΔE átlag | Ítélet |
|---|---|---|---:|---:|---|
| `lanc-0005-teljes-colorfix-nelkul` | teljes aktív lánc (`colorfix` nélkül) | `radblur=1,0.889652,0.000892,-0.990090,-0.303163;LocalContrast=1,13.446470,1.197972;rainbow=1,229.438578;Holga=1,63.516887,91.816275,29.159809;` | 0.97912 | 1.006 | eltér |
| `lanc-0005-nelkul-1` | elhagyva: `radblur` | `LocalContrast=1,13.446470,1.197972;rainbow=1,229.438578;Holga=1,63.516887,91.816275,29.159809;` | 0.98633 | 0.936 | egyezik (közelítés) |
| `lanc-0005-nelkul-2` | elhagyva: `LocalContrast` | `radblur=1,0.889652,0.000892,-0.990090,-0.303163;rainbow=1,229.438578;Holga=1,63.516887,91.816275,29.159809;` | 0.97790 | 1.047 | eltér |
| `lanc-0005-nelkul-3` | elhagyva: `rainbow` | `radblur=1,0.889652,0.000892,-0.990090,-0.303163;LocalContrast=1,13.446470,1.197972;Holga=1,63.516887,91.816275,29.159809;` | 0.99970 | 0.009 | egyezik (közelítés) |
| `lanc-0005-nelkul-4` | elhagyva: `Holga` | `radblur=1,0.889652,0.000892,-0.990090,-0.303163;LocalContrast=1,13.446470,1.197972;rainbow=1,229.438578;` | 0.99295 | 1.586 | egyezik (közelítés) |
| `lanc-0005-par-12` | megtartott pár: `radblur → LocalContrast` | `radblur=1,0.889652,0.000892,-0.990090,-0.303163;LocalContrast=1,13.446470,1.197972;` | 0.99987 | 0.008 | egyezik (közelítés) |
| `lanc-0005-par-23` | megtartott pár: `LocalContrast → rainbow` | `LocalContrast=1,13.446470,1.197972;rainbow=1,229.438578;` | 0.99375 | 1.244 | egyezik (közelítés) |
| `lanc-0005-par-34` | megtartott pár: `rainbow → Holga` | `rainbow=1,229.438578;Holga=1,63.516887,91.816275,29.159809;` | 0.98613 | 0.916 | egyezik (közelítés) |
| `lanc-0056-nelkul-1` | elhagyva: `gamma` | `TwoTone=1,-27.961551,76.839183,9.626150,00227d84,003194d5;linblur=1,0.466086,0.005391,9.064718;rainbow=1,244.890456;triple=1,-0.207838,-0.406449,0.214067;` | 0.99423 | 2.758 | eltér |
| `lanc-0056-nelkul-2` | elhagyva: `TwoTone` | `gamma=1,0.480449;linblur=1,0.466086,0.005391,9.064718;rainbow=1,244.890456;triple=1,-0.207838,-0.406449,0.214067;` | 0.99565 | 0.653 | egyezik (közelítés) |
| `lanc-0056-nelkul-3` | elhagyva: `linblur` | `gamma=1,0.480449;TwoTone=1,-27.961551,76.839183,9.626150,00227d84,003194d5;rainbow=1,244.890456;triple=1,-0.207838,-0.406449,0.214067;` | 0.98812 | 2.442 | eltér |
| `lanc-0056-nelkul-4` | elhagyva: `rainbow` | `gamma=1,0.480449;TwoTone=1,-27.961551,76.839183,9.626150,00227d84,003194d5;linblur=1,0.466086,0.005391,9.064718;triple=1,-0.207838,-0.406449,0.214067;` | 0.99818 | 0.195 | egyezik (közelítés) |
| `lanc-0056-nelkul-5` | elhagyva: `triple` | `gamma=1,0.480449;TwoTone=1,-27.961551,76.839183,9.626150,00227d84,003194d5;linblur=1,0.466086,0.005391,9.064718;rainbow=1,244.890456;` | 0.98729 | 4.684 | eltér |
| `lanc-0056-par-12` | megtartott pár: `gamma → TwoTone` | `gamma=1,0.480449;TwoTone=1,-27.961551,76.839183,9.626150,00227d84,003194d5;` | 1.00000 | 0.000 | egyezik (pixelhű) |
| `lanc-0056-par-23` | megtartott pár: `TwoTone → linblur` | `TwoTone=1,-27.961551,76.839183,9.626150,00227d84,003194d5;linblur=1,0.466086,0.005391,9.064718;` | 0.99993 | 0.007 | egyezik (közelítés) |
| `lanc-0056-par-34` | megtartott pár: `linblur → rainbow` | `linblur=1,0.466086,0.005391,9.064718;rainbow=1,244.890456;` | 0.99488 | 0.842 | egyezik (közelítés) |
| `lanc-0056-par-45` | megtartott pár: `rainbow → triple` | `rainbow=1,244.890456;triple=1,-0.207838,-0.406449,0.214067;` | 0.99411 | 0.610 | egyezik (közelítés) |
| `lanc-0089-nelkul-1` | elhagyva: `IR` | `radsat=1,0.935702,0.276913,-0.462013,0.789662;warm=1;triple2=1,0.127180,0.190318,0.055157;` | 0.99252 | 1.397 | egyezik (közelítés) |
| `lanc-0089-nelkul-2` | elhagyva: `radsat` | `IR=1,6.505770;warm=1;triple2=1,0.127180,0.190318,0.055157;` | 0.98457 | 2.188 | eltér |
| `lanc-0089-nelkul-3` | elhagyva: `warm` | `IR=1,6.505770;radsat=1,0.935702,0.276913,-0.462013,0.789662;triple2=1,0.127180,0.190318,0.055157;` | 0.98932 | 0.223 | egyezik (közelítés) |
| `lanc-0089-nelkul-4` | elhagyva: `triple2` | `IR=1,6.505770;radsat=1,0.935702,0.276913,-0.462013,0.789662;warm=1;` | 0.99697 | 0.447 | egyezik (közelítés) |
| `lanc-0089-par-12` | megtartott pár: `IR → radsat` | `IR=1,6.505770;radsat=1,0.935702,0.276913,-0.462013,0.789662;` | 0.99759 | 0.261 | egyezik (közelítés) |
| `lanc-0089-par-23` | megtartott pár: `radsat → warm` | `radsat=1,0.935702,0.276913,-0.462013,0.789662;warm=1;` | 0.99998 | 0.018 | egyezik (közelítés) |
| `lanc-0089-par-34` | megtartott pár: `warm → triple2` | `warm=1;triple2=1,0.127180,0.190318,0.055157;` | 0.99357 | 1.267 | egyezik (közelítés) |
| `lanc-0113-nelkul-1` | elhagyva: `radsat` | `glow2=1,0.938053,7.426568;HeatMap=1,-166.268420,33.668530;Sixties=1,24.277937,00831e27,0;HDR=1,25.214587,5.596100,24.480760;warm=1;` | 0.99985 | 0.064 | egyezik (közelítés) |
| `lanc-0113-nelkul-2` | elhagyva: `glow2` | `radsat=1,0.495786,0.199929,0.644282,0.226320;HeatMap=1,-166.268420,33.668530;Sixties=1,24.277937,00831e27,0;HDR=1,25.214587,5.596100,24.480760;warm=1;` | 0.98677 | 0.630 | egyezik (közelítés) |
| `lanc-0113-nelkul-3` | elhagyva: `HeatMap` | `radsat=1,0.495786,0.199929,0.644282,0.226320;glow2=1,0.938053,7.426568;Sixties=1,24.277937,00831e27,0;HDR=1,25.214587,5.596100,24.480760;warm=1;` | 0.99012 | 0.484 | egyezik (közelítés) |
| `lanc-0113-nelkul-4` | elhagyva: `Sixties` | `radsat=1,0.495786,0.199929,0.644282,0.226320;glow2=1,0.938053,7.426568;HeatMap=1,-166.268420,33.668530;HDR=1,25.214587,5.596100,24.480760;warm=1;` | 0.98794 | 0.632 | egyezik (közelítés) |
| `lanc-0113-nelkul-5` | elhagyva: `HDR` | `radsat=1,0.495786,0.199929,0.644282,0.226320;glow2=1,0.938053,7.426568;HeatMap=1,-166.268420,33.668530;Sixties=1,24.277937,00831e27,0;warm=1;` | 0.99716 | 0.216 | egyezik (közelítés) |
| `lanc-0113-nelkul-6` | elhagyva: `warm` | `radsat=1,0.495786,0.199929,0.644282,0.226320;glow2=1,0.938053,7.426568;HeatMap=1,-166.268420,33.668530;Sixties=1,24.277937,00831e27,0;HDR=1,25.214587,5.596100,24.480760;` | 0.97586 | 0.850 | eltér |
| `lanc-0113-par-12` | megtartott pár: `radsat → glow2` | `radsat=1,0.495786,0.199929,0.644282,0.226320;glow2=1,0.938053,7.426568;` | 0.99941 | 0.097 | egyezik (közelítés) |
| `lanc-0113-par-23` | megtartott pár: `glow2 → HeatMap` | `glow2=1,0.938053,7.426568;HeatMap=1,-166.268420,33.668530;` | 0.99990 | 0.027 | egyezik (közelítés) |
| `lanc-0113-par-34` | megtartott pár: `HeatMap → Sixties` | `HeatMap=1,-166.268420,33.668530;Sixties=1,24.277937,00831e27,0;` | 1.00000 | 0.000 | egyezik (pixelhű) |
| `lanc-0113-par-45` | megtartott pár: `Sixties → HDR` | `Sixties=1,24.277937,00831e27,0;HDR=1,25.214587,5.596100,24.480760;` | 1.00000 | 0.000 | egyezik (pixelhű) |
| `lanc-0113-par-56` | megtartott pár: `HDR → warm` | `HDR=1,25.214587,5.596100,24.480760;warm=1;` | 1.00000 | 0.000 | egyezik (pixelhű) |
| `lanc-0178-nelkul-1` | elhagyva: `triple3` | `triple2=1,0.218250,0.303895,0.317896;dir_sat=1,0.037718,-0.414407;colortemp=1,-0.389167,0.612947;` | 0.99554 | 2.158 | eltér |
| `lanc-0178-nelkul-2` | elhagyva: `triple2` | `triple3=1,0.218352,0.361045,0.311731;dir_sat=1,0.037718,-0.414407;colortemp=1,-0.389167,0.612947;` | 0.99750 | 1.406 | egyezik (közelítés) |
| `lanc-0178-nelkul-3` | elhagyva: `dir_sat` | `triple3=1,0.218352,0.361045,0.311731;triple2=1,0.218250,0.303895,0.317896;colortemp=1,-0.389167,0.612947;` | 0.99229 | 3.030 | eltér |
| `lanc-0178-nelkul-4` | elhagyva: `colortemp` | `triple3=1,0.218352,0.361045,0.311731;triple2=1,0.218250,0.303895,0.317896;dir_sat=1,0.037718,-0.414407;` | 0.99325 | 2.827 | eltér |
| `lanc-0178-par-12` | megtartott pár: `triple3 → triple2` | `triple3=1,0.218352,0.361045,0.311731;triple2=1,0.218250,0.303895,0.317896;` | 0.99348 | 2.866 | eltér |
| `lanc-0178-par-23` | megtartott pár: `triple2 → dir_sat` | `triple2=1,0.218250,0.303895,0.317896;dir_sat=1,0.037718,-0.414407;` | 0.99664 | 1.958 | egyezik (közelítés) |
| `lanc-0178-par-34` | megtartott pár: `dir_sat → colortemp` | `dir_sat=1,0.037718,-0.414407;colortemp=1,-0.389167,0.612947;` | 1.00000 | 0.000 | egyezik (pixelhű) |
## Lokalizálás és önálló szűrők

Az alábbi önálló eredmények azonos forrásképen, az adott lánc paramétereivel készültek (a [korábbi pótmérés teljes táblája](../benchmarks/2026-11-08-6585-ujrabesorolas.md)). Minden tag `pixelhű` vagy `közelítés`; egyik sem `eltér`. Ezért a b-láncok nem önálló szűrőhibát bizonyítanak. A ΔE értékek CIE76 átlagok.

| Lánc / kép | Önálló mérés: szűrő: SSIM / ΔE | Minimalizálási lelet |
|---|---|---|
| `lanc-0005` / k05.jpg | `radblur` 0.99988 / 0.007; `LocalContrast` 1.00000 / 0.000; `rainbow` 0.98329 / 1.312; `Holga` 1.00000 / 0.000 | Nem izolálható egy szűrő. A kis ΔE mellett a SSIM épp a küszöb alatt van; a 4-szűrős interakció és az egyedi közelítések összeadódása egyaránt lehetséges. a négyszűrős lánc colorfix nélkül 0.97912 / 1.006 (SSIM küszöb alatt); `LocalContrast` elhagyása továbbra is eltér (0.97790 / 1.047), a másik három egyedi elhagyása és mindhárom szomszédos pár egyezik |
| `lanc-0056` / k06.jpg | `gamma` 1.00000 / 0.000; `TwoTone` 1.00000 / 0.000; `linblur` 0.99985 / 0.018; `rainbow` 0.99428 / 0.853; `triple` 0.99306 / 0.469 | A mérés `TwoTone` és `rainbow` jelenlétéhez való érzékenységet mutat, de a két nem szomszédos szűrő önálló párosa, illetve a köztes három- és négyszűrős részláncok nincsenek elszigetelve. Nincs egyedi bűnös. a kiinduló ötös lánc 0.99329 / 2.636; a jelöltekben `TwoTone` vagy `rainbow` elhagyásakor egyezik, a többi egyedi elhagyáskor eltér; mind a négy szomszédos pár egyezik |
| `lanc-0089` / k09.jpg | `IR` 0.99763 / 0.291; `radsat` 0.99999 / 0.018; `warm` 1.00000 / 0.000; `triple2` 0.99442 / 1.195 | A háromszűrős sorrend gyanús, önálló szűrőhiba nem igazolódott. A `triple2` a legnagyobb egyedi eltérés, de `közelítés` ítéletű; #6690 utáni újramérés szükséges. a kiinduló négyes lánc 0.98587 / 2.142; `IR → warm → triple2` (a `radsat` elhagyásával) 0.98457 / 2.188 eltér, miközben a többi egyszűrős elhagyás és mindhárom szomszédos pár egyezik |
| `lanc-0113` / k03.jpg | `radsat` 0.99950 / 0.078; `glow2` 0.99999 / 0.008; `HeatMap`, `Sixties`, `HDR`, `warm` egyenként 1.00000 / 0.000 | Határeset: a ΔE alacsony, az SSIM a 0.98-as küszöb alatt marad. A `warm` önmagában pixelhű, és az elhagyása nem oldja meg; a jelöltek láncszintű felhalmozódást mutatnak, nem azonosítanak bűnös szűrőt. a kiinduló hatos lánc 0.97662 / 0.824; a `warm` nélküli ötös lánc is eltér (0.97586 / 0.850), minden más egyedi elhagyás és mind az öt szomszédos pár egyezik |
| `lanc-0178` / k08.jpg | `triple3` 0.99806 / 1.085; `triple2` 0.99664 / 1.976; `dir_sat` és `colortemp` egyenként 1.00000 / 0.000 | A legszűkebb jelölt a `triple3 → triple2` sorrendű pár. Mindkét tag külön egyezik, de a `triple2` már önmagában is a ΔE-tűrés közelében van; az egyedi hiba és a láncbemenet hatása itt nem választható szét. a kiinduló négyes lánc 0.99218 / 3.003; a `triple3 → triple2` pár önmagában 0.99348 / 2.866 eltér; `triple2` elhagyásával a háromszűrős lánc egyezik (0.99750 / 1.406) |

### Mit mondanak a jelöltek

- **`lanc-0005`:** a colorfix nélküli teljes lánc és a `radblur;LocalContrast`-ot tartalmazó háromtagú lánc a SSIM-küszöb miatt eltér, miközben `LocalContrast` elhagyása is eltér, a másik három egyedi elhagyás és mindhárom szomszédos pár egyezik. Nincs izolált szűrő vagy pár; a kis SSIM-határátlépés és az összeadódó, egyenként elfogadott eltérések lehetségesek.
- **`lanc-0056`:** `TwoTone` vagy `rainbow` elhagyása egyező láncot ad, más egyedi elhagyások továbbra is eltérnek; mind a négy szomszédos pár egyezik. A két szűrő együttállása jelölt, de a nem szomszédos `TwoTone → rainbow` pár és a köztes részláncok nincsenek külön mérve; konkrét javítandó szűrő nem azonosítható.
- **`lanc-0089`:** a `radsat` nélküli `IR → warm → triple2` háromtagú sorrend eltér (`0.98457 / 2.188`), noha a három tag önállóan és mindhárom szomszédos pár egyezik. Ez a legerősebb megfigyelt láncjelölt; önálló `triple2`-hiba nem áll fenn ezen a képen. A `triple2`-t érintő két láncot (#0089, #0178) a #6690 módosítása után újra kell mérni.
- **`lanc-0113`:** az eredeti hatos lánc és az utolsó `warm` nélküli öttagú változat is eltér, miközben a többi egytagú elhagyás és mind az öt szomszédos pár egyezik. Mindkét esetben alacsony a ΔE (`0.824`, illetve `0.850`), a SSIM pedig a `0.98` küszöb alatt van (`0.97662`, `0.97586`); ez láncszintű, küszöbérzékeny eltérés, nem egyetlen bűnös.
- **`lanc-0178`:** a `triple3 → triple2` kétfilteres pár is eltér (`0.99348 / 2.866`), és a `triple2` nélküli háromtagú lánc egyezik (`0.99750 / 1.406`). Ez a legszűkebb reprodukáló minta; a `triple2` külön `0.99664 / 1.976` értéke már közel van a ΔE-határhoz. A pár adatai nem választják el az egyedi közelítés felhalmozódását a megváltozott bemenet hatásától.

## Következtetés és következő lépés

A minimális jelöltek nem igazoltak új, egyértelműen javítható algoritmushibát. A `triple2` bináris burkolójának dekompilált leírása (`FUN_008f8b90`, `referencia/dekompilalt/natív-szűrők.c`) a Derítőfényt a szinthúzás előtt alkalmazza; a PicasaPy útja ugyanezt a sorrendet követi. A mostani láncmérések sem neveznek meg eltérő natív képletet, ezért kódot és golden-tesztet nem módosítottunk, meglévő tesztet sem gyengítettünk.

Következő mérés: a #6690 `triple2` javítása után újrafuttatni az `lanc-0089` és `lanc-0178` releváns láncait, majd a `lanc-0056` esetén külön mérni a `TwoTone → rainbow` nem szomszédos párt, a `lanc-0005` esetén pedig a hiányzó háromtagú részláncokat. Ha ezek után egy részlánc továbbra is eltér, annak köztes renderelt képével kell folytatni a szűrőállapot lokalizálását.

**Fájlforrás:** az eredeti Colab-exportok és `jeloltek.json` a helyi, nem verziózott `.tmp/meres/minimalizalas/` adatcsomag részei. A fenti teljes táblázat ezek 2026-11-08-i mérési eredményét őrzi.

## Folytatás: a teljes láncok és a `lanc-0056` pármérése (2026-11-09)

### Módszer

A teljes `lanc-0056`, `lanc-0089` és `lanc-0178` láncot, valamint a `TwoTone → rainbow` párt a PicasaPy `apply_filters` útvonalán rendereltem. A k06, k09 és k08 forrásfájlokat a `minimalizalas/forras/` könyvtárból párosítottam. A teljes láncok eredetije a `teljes-458/export__kNN.jpg`, a páré a `teljes-459/export__k06.jpg`. A két korábbi kihagyásos kontrollt is újrarendereltem, az eredetijük a `minimalizalas/eredeti/min-01` és `min-03` könyvtárban van. Mind a hat saját render elkészült, kihagyott szűrő nélkül, az összevetett képek mérete egyezett.

A helyi PNG-t a megfelelő Picasa JPEG mintavételezésével és kvantálótábláival kódoltam újra. Ezután mindkét dekódolt RGB-képre `cv2.GaussianBlur(..., (0, 0), sigmaX=2.5, sigmaY=2.5)` került. Az SSIM és CIE76 ΔE számítása a `tools/golden/compare_render.py` meglévő megvalósításával történt. Az ítélet a korábbi küszöböt használja: SSIM ≥ 0.98 és ΔE ≤ 2.0.

### Eredmények

| Lánc | Picasa referencia | Nyers SSIM / ΔE | Gauss σ=2.5 SSIM / ΔE | Ítélet |
|---|---|---:|---:|---|
| `lanc-0056` teljes | `teljes-458/export__k06.jpg` | 0.99326 / 2.635 | 0.99814 / 2.536 | eltér |
| `lanc-0056-nelkul-1` (`gamma` nélkül) | `minimalizalas/eredeti/min-01/export__k06.jpg` | 0.99423 / 2.758 | 0.99827 / 2.661 | eltér |
| `lanc-0056-nelkul-3` (`linblur` nélkül) | `minimalizalas/eredeti/min-03/export__k06.jpg` | 0.98812 / 2.442 | 0.99819 / 2.315 | eltér |
| `TwoTone → rainbow` | `teljes-459/export__k06.jpg` | 0.98416 / 4.746 | 0.99525 / 4.604 | eltér |
| `lanc-0089` teljes | `teljes-458/export__k09.jpg` | 0.98564 / 2.136 | 0.99830 / 0.683 | egyezik |
| `lanc-0178` teljes | `teljes-458/export__k08.jpg` | 0.99225 / 2.977 | 0.99921 / 0.725 | egyezik |

Az újramért kihagyásos kontrollok ítélete megegyezik az előző körével. A σ=2.5-ös értékek az előző jelentés számaitól legfeljebb 0.00002 SSIM-mel és 0.015 ΔE-vel térnek el; a két eset besorolása változatlan.

### Lokalizálás és következő mérés

A `lanc-0056` teljes lánc, a `gamma` nélküli és a `linblur` nélküli változat is eltér. A `TwoTone → rainbow` önmagában is eltér, nagyobb ΔE-vel. A meglévő egyszűrős kontrollban a `TwoTone` pixelhű (SSIM 1.00000, ΔE 0.000), a `rainbow` közelítés (0.99428, 0.853). A legkisebb mért reprodukáló eset így a két szűrő egymásutánja; a külön-külön kapott eredmények alapján a rainbow lépése vizsgálandó elsőként.

Érintett PicasaPy-fájl: `src/picasapy/render/rainbow.py`. A natív callback `0x008f92d0`; az útvonal a szinthúzó `0x009db610` és a sávszínező `0x009db4f0` munkafüggvényt is hívja. A `TwoTone` kontrollja a `0x00bb87b0` Glimmer-munkavégző. A teljes kimeneti mérés nem választja szét, hogy a rainbow ezen belül melyik lépése, vagy a két lépés közötti állapotátadás okozza az eltérést. Ezért egyértelmű kerekítési, vágási vagy sorrendi hibát nem állapítottam meg, és renderkódot, golden referenciát vagy tesztet nem módosítottam.

**Következő mérés:** k06-on a Colabban exportálni a Picasa `TwoTone=1,-27.961551,76.839183,9.626150,00227d84,003194d5` eredményét. Ezt a Picasa-exportált képet azonos bemenetként használva külön alkalmazni a `rainbow=1,244.890456` szűrőt az eredeti Picasában és a PicasaPy `apply_rainbow` útján, majd ugyanazzal a JPEG-egyeztetéssel és σ=2.5 mércével összevetni. Ez eldönti, hogy a rainbow önállóan tér-e el a TwoTone által előállított színtartományon; ha egyezik, a következő mérés az eredeti lánc köztes pufferének veszteségmentes kinyerése és a rainbow lépéssorrendjének összevetése.

## Utómérés: Rainbow javítása (#6743, 2026-11-09)

A fenti következő mérés a #6743-ban elkészült. Az első elkülönített eredmény alapján a hibát nem a gradiens iránya vagy a sávok fázisa okozta: a `0x008f92d0` callback a `Preferences/CarefulEnhance` beállítást olvassa, a #461 eredeti Rainbow-export pedig a kikapcsolt ággal egyezett. A PicasaPy addig feltétel nélkül a bekapcsolt ágat használta, ami a vörös csatornán átlagosan `+11,3` eltérést adott. Emellett a `244.890456` színmegőrzési paramétert a natív callback `ROUND` függvénnyel kerekíti, ezért az értéke `245`, nem `244`.

Az izolált mérést a #460 Picasa TwoTone-exportján futtattam, és a #461 `export__k06tt.jpg` Rainbow-exportjával vetettem össze. A saját render a kikapcsolt CarefulEnhance-ágat és `p=245` értéket használta. A PicasaPy képet a referencia JPEG mintavételezésével és kvantálótábláival kódoltam újra; a σ=2.5 értékek előtt mindkét dekódolt képre `cv2.GaussianBlur(..., sigmaX=2.5, sigmaY=2.5)` került. A meglévő `tools/golden/compare_render.py` mércéje:

| Mérce | Nyers | Gauss σ=2.5 |
|---|---:|---:|
| SSIM | 0.996303 | 0.998929 |
| CIE76 ΔE átlag | 0.964923 | 0.819804 |
| CIE76 ΔE 99. percentilis | 3.419133 | 2.280455 |

A teszt referenciája a #461 exportból vágott 208×597 képpont, így reprodukálható, kis golden mintát ad az eredeti #460 bemenethez.

A javítás után a `lanc-0056` teljes láncot újramértem a `minimalizalas/forras/k06.jpg` bemeneten, a `teljes-458/export__k06.jpg` eredeti referenciával, minden szűrő kihagyása nélkül. A PicasaPy render újrakódolása és az összevetés ugyanazt a JPEG-egyeztetést és Gauss-mércét használta:

| Mérce | Nyers | Gauss σ=2.5 |
|---|---:|---:|
| SSIM | 0.996036 | 0.998966 |
| CIE76 ΔE átlag | 0.582303 | 0.487303 |
| CIE76 ΔE 99. percentilis | 2.540715 | 1.798259 |

A javítás után a lánc a meglévő SSIM ≥ 0.98 és Gauss utáni ΔE ≤ 2.0 küszöb szerint egyezik. A sávok vízszintes iránya, fázisa és szorzókeverése nem változott.

## #6746 - sötétkék eltérés az `IR → warm → triple2` láncban (2026-11-10)

### Bináris út: a láncpuffer és a triple2 magja

A `FUN_00907f30` láncvégrehajtó a filter render-slotját (`+0x80`) hívja az aktuális képleíróval és egy kimeneti képleíróval (`0x00908077`-`0x00908087`, a kimeneti leíró előkészítése: `0x00908235`-`0x00908240`). A `CGenericFilter` render-slot `0x008f6e40` az objektum `+0x0c` callbackjét hívja. A `0x008f8b90` triple2-callback a láncban így ugyanazon képpuffer API-n kapja az előző tag kimenetét.

A `0x008f8b90` a Derítőfényt (`0x0090ac20`), majd az aktív fekete-/fehérpont-ágat futtatja. A `0x0090c430` a `0x0090c1e0` LUT-építőt, majd a `0x0090be70` pixelmagot hívja. A mag a képleíró `+0x10` pointeréről byte-ként olvassa a B, G, R csatornát (`0x0090bed0`-`0x0090bee4`), képpontonként 4 bájtot lép, és BGRA dwordöt ír vissza ugyanabba a pufferbe (`0x0090beb3`-`0x0090beb9`, `0x0090c002`). Ezen a láncúton a triple2 tehát **8 bites csatornánkénti BGRA pixeleket** fogyaszt és állít elő; nincs 16 bites vagy lebegőpontos pixelközi felületre utaló művelet. A LUT ettől különbözik: 257 darab 16 bites, 8.8 fixpontos értéket tartalmaz.

### A szinthúzás kerekítése és ditherje

A paraméterek `triple2=1,0.127180,0.190318,0.055157`. A fekete pont nagyobb a fehér pontnál, ezért a LUT csökkenő szakaszt is tartalmaz. A pixelmag képlete a `0x0090beed`-`0x0090bfe8` utasítások szerint:

```text
r = MT19937_next() & 0xff
delta = LUT[c + 1] - LUT[c]
v = LUT[c] + ((delta * r) >>> 8) - (delta >>_aritmetikai 1)
out = clamp(v >>_aritmetikai 8, 0, 255)
```

Nincs `+128` kerekítőtag: a pixelenkénti 8 bites eredmény 8.8 fixpontos értékből aritmetikai jobbra tolással és végső vágással készül. A csökkenő delta szorzata viszont **előjel nélkül** tolódik (`shr`), míg a fél-delta és a végső osztás előjeles (`sar`); a csökkenő szakaszon ez a natív telítési viselkedés része, nem helyettesíthető szokásos kerekítéssel. A 16 bites LUT bejegyzés előállításában `fistp` szerepel (`0x0090c27f`), ezért annak eredményét az x87 vezérlőszava is befolyásolja. Az eredeti alkalmazás e hívás előtti x87 vezérlőszava **NINCS MEG**.

A mag képpontonként egy mintát olvas a folyamat-globális MT19937 állapotból: az index `0x00d67f74`, az állapottömb `0x00d67f7c` (`0x0090beed`-`0x0090bf25`). Ugyanazt a mintát használja mindhárom csatornához. A minták fázisa ezért a korábban feldolgozott képpontoktól függ; ezt a #3092 viselkedést és a PicasaPy rögzített hívásonkénti mintájának korlátját a `picasa-native-filter-workers.md` 2.2/d szakasza részletezi.

### QEMU-mérés és független ellenőrzés

A harness az eredeti `0x008f8b90` callbacket futtatta 1331 sötétkék bemeneti pixelre (`R=20…30`, `G=55…65`, `B=120…130`) a fenti paraméterekkel. Az alapértelmezett skalár QEMU-CPU és a `-cpu max` kimenete 5324 bájton bitre azonos volt; a célzott callback, LUT-építő, pixelmag és MT-twist diszasszemblálásban nincs MMX/SSE vektorutasítás.

| Összevetés | Eredmény |
|---|---|
| Natív LUT vs. PicasaPy LUT; QEMU x87 vezérlőszó `0x037f` | 256/256 bejegyzés egyezik |
| Natív Derítőfény utáni puffer vs. `apply_fill` | 1331/1331 pixel egyezik |
| Natív workerből rögzített LUT és dither-sorozat mellett natív vs. PicasaPy `triple2` | 1331/1331 pixel egyezik; max. csatornaeltérés 0 |
| PicasaPy saját, hívásonként inicializált mintasorával a natív callback kimenete | 1324/1331 pixel egyezik; a 7 eltérés a vörös csatornán van, rendszeres színeltolás nélkül |

Ez két külön bizonyítási út: **A)** az utasításszintű olvasás megadja a bájtos pixelműveletet, a fixpontos képletet és a dither globális állapotát; **B)** a QEMU-ban futó natív callback rögzített köztes pufferével, LUT-jével és mintasorozatával a PicasaPy kimenete képpontosan azonos. A mag algoritmikus egyezése ezen a bemeneti rácson **megerősített**. A hét eltérés a saját mintasorral nem cáfolja ezt: a natív RNG-fázist nem azonosítja, és egyik csatornán sem ad rendszeres eltérést.

**Cáfoló kísérlet:** az azonos bemenet/LUT/mintasorozat próba eltérést mutatott volna, ha a PicasaPy pixelképlete más lenne; nem mutatott. Az első instrumentált QEMU-összevetés visszaugró kódrészlete felülírta az EAX mintaregisztert, ezért azt a kimenetet elvetettem. A regisztermegőrző `push célcím; ret` visszaugrással megismételt próba adja a fenti mérési eredményeket.

### Következtetés a teljes láncról és a #6746 kész-feltételéről

A fenti bizonyíték **nem igazol PicasaPy `triple2` képlethibát**, így a mag javítása nem indokolt. A teljes lánc eltérésének eredete viszont **nyitott**: nincs veszteségmentes mérés az eredeti Picasa tényleges, triple2 előtti BGRA pufferéről és a `0x00d67f74` + `0x00d67f7c` dither-állapotáról. A #462/#463 lépésenkénti JPEG út nem helyettesíti ezt: a jegyben rögzített mérés szerint az eredeti Picasa teljes lánca és a saját, JPEG-exporttal szétválasztott útja a sötétkék tartomány kék csatornáján átlagosan 10,3 szinttel tér el.

| #6746 kész-feltétel | Állapot és bizonyíték |
|---|---|
| Teljes lánc: SSIM ≥ 0,98 | ✅ #436, Gauss σ=2,5 után SSIM 0,99785 |
| Teljes lánc: Gauss utáni átlagos ΔE ≤ 2,0 | ✅ #436, σ=2,5 után ΔE átlag 0,720 |
| Sötétkék foltok p99 ΔE < 3 | ⛔ #436, σ=2,5 után p99 6,28; 3,2% pixel ΔE>4 |
| Golden a Colab-exportból vágott kis mintával | ⛔ E kutatási körben új minta/golden nem készült |

**Következő döntő mérés:** az eredeti Picasa teljes `IR → warm → triple2` futásában és a PicasaPy megfelelő futásában veszteségmentesen rögzíteni ugyanazt a triple2 előtti BGRA puffert, valamint közvetlenül a `0x0090be70` hívás előtt a `0x00d67f74` indexet és a `0x00d67f7c` 624 szavas állapotot. A puffer egyezése és eltérése a mintasorral szétválasztja a bemeneti képkülönbséget az RNG-fázistól. A QEMU LUT mérés x87 módja `0x037f`; az eredeti alkalmazás módját külön kell leolvasni, ha a LUT-re kiterjedő pixelhű bizonyítás szükséges.

## #6822 - a triple3 és a szemcseszűrők véletlenállapota (2026-11-11)

A `triple3` callbackje (`0x008f8ce0`) az aktív ágon a `0x0090c430`-on át
hívja a `0x0090be70` LUT-magot (`0x008f8d8b`, `0x0090c478`). A mag a
folyamat globális MT-objektumának `0x00d67f74` indexét és `0x00d67f7c`
állapottömbjét használja, és egy képpontonkénti húzást oszt meg a három
csatorna között (`0x0090beed`-`0x0090bf7a`). A fenti #6746 szakaszban
szereplő, azonos mintasorral végzett natív QEMU-összevetés a közös mag
képletét külön is ellenőrizte; az ottani mérés nem a #6822 exportja.
Forrás: `bináris (0x008f8ce0, 0x0090c430, 0x0090be70)`;
`mérés (#6746 QEMU, 1331 pixel azonos LUT-tal és mintákkal)`.

A globális objektum magját az indulási táblából hivatkozott `0x00c32520`
állítja elő: három egymást követő CRT `_rand` hívás eredménye `r1`, `r2`,
`r3`, a mag pedig `r3 XOR ((r2 XOR (r1 << 12)) << 12)`, 32 bites
aritmetikával. A `0x00c416b0` táblabejegyzés a `0x00c32520`-ra mutat;
a magot a `0x00aa28f0` bontja ki. A kezdőérték `0x2d8228be` **akkor**,
ha a szál CRT-állapota 1 és ez az első három húzás: a CRT kezdőállapota
`0x00bf0474`-nél 1, a léptetés `0x00c08221`-nél történik. A korábbi
indulási tábla-auditot a `picasa-native-filter-workers.md` 2.2 szakasza
rögzíti. Az adott export előtti tényleges MT-állapot ettől még nem ismert:
a korábbi húzások megváltoztatják. Forrás: `bináris (0x00c416b0,
0x00c32520, 0x00bf0474, 0x00c08221, 0x00aa28f0)`; `NINCS MEG
(a #6822 exportjában a triple3 előtti MT-állapot)`.

A `0x00aa28f0` kiterjesztése `s[0]=seed`,
`s[i]=(0x0019660d * (s[i-1] XOR (s[i-1] >> 30)) + i) mod 2^32`
`i=1..623` mellett, az index 624. Ez eltér a szabványos magkiterjesztéstől;
az azonos seed átadása önmagában nem igazolja a NumPy MT19937 azonos
állapotát. A `0x6c078965` közvetlen utasításoperandusra végzett teljes
`.text` pásztázás nem talált találatot; pozitív kontroll a `0x00aa290b`
`0x0019660d` operandusa. A pásztázás nem zárja ki a másképp előállított
konstansokat vagy a közvetett hívásokat. Forrás: `bináris (0x00aa28f0,
0x00aa290b)`; `mérés (paszta.py .text utasításpásztázás)`.

| Út | Állapot és mag | Forrás |
|---|---|---|
| `triple3` LUT | Folyamat-globális; a magvetés nem a pixelmagban történik. | `bináris (0x00c32520, 0x0090beed)` |
| `grain2` / `grain` | Külön verembeli objektum minden workerhíváson; három CRT `_rand` eredményéből új mag. Ugyanaz a magkiterjesztő és twist, de más állapot. | `bináris (0x008f8918, 0x0090a349, 0x0090a366, 0x0090a3e8)` |
| `PicnikGrain` Noise | A worker saját veremterületén hozza létre az MT-állapotot: a callback seed argumentuma a `0x00bce904`-nél kerül kiolvasásra, a helyi állapot címe `0x00bce90e`-nél megy a `0x00aa28f0` magkiterjesztőnek; a pixelenkénti húzás a helyi tömböt lépteti (`0x00bce9be` → `0x00aa2930`). A leíró fix seedje 1; ez pszeudovéletlen algoritmus, nem a folyamat közös véletlenállapota. | `bináris (0x00bbee70, 0x00bbefa0, 0x00bce904, 0x00bce90e, 0x00bce9be, 0x00aa28f0, 0x00aa2930)`; `mérés (684 PicnikGrain export, #3757; CIE76 ΔE 0,882)` |

**Cáfolat:** a közös twistfüggvény nem bizonyít közös állapotot: a grain2
indexét a `0x0090a391` és `0x0090a47b` veremmezőből olvassa, illetve oda
írja, a triple3 a `0x0090bf0f` és `0x0090bf1f` címen a globális indexet.
Ez az inicializálás célcímétől különálló ellenőrzés, de ugyanabból a diszasszemblált útból származik. Forrás:
`bináris (0x0090a391, 0x0090a47b, 0x0090bf0f, 0x0090bf1f)`.

**Határ:** a `glow`, `autocolor` és `dir_brite` teljes, közvetett hívásokat
is magába foglaló véletlenállapot-hatása és a #6819 eltérésének oka nincs
bizonyítva. A #6822 Colab-leszűkítése a triple3 eltérését és a HeatMap-pel
növekvő eltérést méri, de önmagában nem igazolja, hogy kizárólag az
MT-fázis okozza. Pixelpontos következtetéshez ugyanazon eredeti exportban
rögzíteni kell a triple3 előtti dekódolt bemenetet, a LUT-ot, az MT teljes
állapotát és indexét, majd azonos feltételekkel a kimenetet összevetni.
Forrás: `mérés (picasa-colab-jobs #529-#532, #538-#540, #546, jegyben
közölt értékek)`; `NINCS MEG (export előtti puffer, LUT és MT-állapot)`.

*Bizonyítottsági fok: **feltételes** a grain2 és triple3 külön állapota,
mert két külön utasításcsoport támasztja alá, de független futás közbeni
állapotmérés itt nem történt; **feltételes** a kezdőmag konkrét értéke az
említett kezdeti és sorrendi feltételek mellett; **nyitott** a
#6822 eltérésének pontos oka és a konkrét export pixelhű reprodukciója.*

## `lanc-0132`: az autocolor becslésének érzékenysége (2026-11-11, #6585)

A k02.jpg bemeneten az r6830 eredeti 004 exportja a
`colorfix=1,0.049146,ff2af3a5;rainbow=1,151.657621;autocolor=1;`
lánchoz tartozik. A PicasaPy aktuális `apply_filters` kimenete bájtra
megegyezik a meglévő saját 004 PNG RGB-képpontjaival. A mérés a saját képet a
referencia JPEG mintavételezésével és kvantálótábláival kódolja, majd a
`tools/golden/compare_render.py` CIE76 és SSIM mércéjét használja.

| Saját változat a 004 eredeti exporthoz | SSIM | Átlagos CIE76 ΔE |
|---|---:|---:|
| `colorfix;rainbow;autocolor` | 0.927504 | 47.759275 |
| `colorfix;rainbow` | 0.989601 | 1.275051 |

**Mérés:** az automatikus színkorrekció a saját köztes képen az eltérést
nagymértékben növeli. A kis eltérés az autocolor nélkül **nem bizonyítja**,
hogy a két program köztes RGB-puffere azonos, vagy hogy az eredetiben az
autocolor biztosan tétlen volt: csak a végső JPEG áll rendelkezésre.

A `0x008f82fa` a `0x0090f8f0` becslőt hívja, majd a `0x008f8313`
a `0x0090eda0` mátrixalkalmazót. A `0x0090f9b6` és `0x0090f9e8`
közötti szűrés a zöld értéket és az RGB csatornák arányát vizsgálja;
a `0x0090fa6b` kétdimenziós hisztogramot tölt. A `0x0090fae1` szorzás
után a `0x0090fae4` cellánként nyolc bittel jobbra tol, a
`0x0090fbc2` és `0x0090fbc9` előjeles osztás. Az autocolor útja tehát
becslés és 3×3-as színmátrix, a `0x009db610` szinthúzó a rainbow útján
szerepel. A saját megfelelő a `render/autocolor_matrix.py`
`estimate_illuminant` és `render/ops_levels.py` `apply_autocolor`.

A saját köztes képen, független hisztogram-újraszámítással: 15 899 képpont
felel meg az RGB-feltételeknek, de a cellánkénti egész súlyozás összege csak
1. Az egyetlen nem nulla cella `(kék/zöld=4, vörös/zöld=60)`: darabszáma
144, súlya 2, így `(144*2)>>8 = 1`. A súlypont `(28,-28)`, az ebből kapott
becslés `(kR,kB)=(240,68)`; a `colorfix` után, a rainbow előtt `(220,220)`.
Az RGB csatornák közül a vöröshöz mindenütt 1-et hozzáadva a súlyozott
összeg 0 és a becslés `(128,128)`. Ez kontrollált saját bemeneti perturbáció,
nem az eredeti puffer rekonstrukciója. A JPEG-kódolt saját köztes képen a
súlyozott összeg 145 és a becslés `(136,91)`: az export JPEG-je nem
helyettesíti veszteségmentesen a lánc köztes pufferét.

A 32 bites szorzási túlcsordulás ellenőrzése ezen a képen: a legnagyobb
cellaszorzat 288, túlcsorduló cellák száma 0; a natív 32 bites szorzat
újrajátszása ugyanazt az `(240,68)` becslést adta. A becslő a
`0x0090f99d` és `0x0090f9b0` között csak az RGB bájtokat bontja ki,
az alfa nem szerepel a kiválasztásban. A PicasaPy mindkét előző szűrőt
255-ös alfaosztályba sorolja; a natív alfaosztályt a
[filterdesc-registry](filterdesc-registry.md) rögzíti. Ez nem zár ki
más, a szűrőlánc pufferével kapcsolatos eltérést.

**Cáfoló kontroll:** az eredeti 001 és 002 exporttal, azonos
JPEG-egyeztetéssel, a teljes saját kontroll ΔE-je 1.095706 és 0.170866;
az autocolor elhagyásával 25.925625 és 41.611907. Az általános
„autocolor mindig ki van kapcsolva” feltevés ezekre a kontrollokra nem áll.
E kontrollok `shadow` tagot is tartalmaznak, a 004 pedig nem, tehát nem a
hármas mindhárom tiszta kéttagú részhalmazát mérik.

**Bizonyítottság: feltételes.** A saját hisztogram törékenységét a független
újraszámítás és a natív súlyozó utasítások alátámasztják; a tényleges
kétprogramos eltérés oka és a javítandó szűrő még nem bizonyított. Az eredeti
köztes puffer és az eredeti gain értéke **NINCS MEG**. A javításhoz nem
szabad új minimum-mintaszámot vagy becsült küszöböt bevezetni.

**Következő célzott mérés:** ugyanazon k02 forráson és azonos Picasa-export
beállítással egymás mellett exportálandó a
`colorfix=1,0.049146,ff2af3a5;rainbow=1,151.657621;` és a fenti teljes
hármas, `shadow` nélkül. A két eredeti export különbsége ellenőrzi az eredeti
autocolor tényleges hatását. A döntő mérés az eredeti `0x0090f8f0`
bemeneti RGB-pufferének és a `0x0090fc99` által írt gainnek a kinyerése
ugyanabban a futásban; ezt a saját köztes pufferrel és becsléssel kell
összevetni. Ha csak JPEG-export szerezhető, abból az eredeti memóriabeli
gain nem következtethető pontosan.

### Az autocolor kis súlyösszegének kapuja (2026-11-11)

**Megerősített a vizsgált becslőágon:** a `0x0090fb32` és `0x0090fb77`
között a súlyozott cellák összege a `[esp+0x14]` változóba gyűlik. A
`0x0090fbb5` ezt **nullával** hasonlítja össze; a `0x0090fbb9` csak
nullánál kerüli el a két súlypont-osztást (`0x0090fbc2`, `0x0090fbc9`).
Pozitív minimumösszeg miatti korai kilépés ezen az úton nincs: az 1-es
összeggel is oszt. Nulla összegnél az addig felhalmozott nullás nyomatékokból
semleges becslés keletkezik. A `0x0090fbcd-0x0090fbf4` a két súlypontot
-32 és 32 közé szorítja, majd a `0x0090fc61-0x0090fc85` a két kimeneti
értéket 0 és 255 közé korlátozza. A `0x0090fc99` írja a csomagolt becslést.
A PicasaPy `estimate_illuminant` ugyanezt a nulla-ágat és ezeket a korlátokat
használja. Ez a lelet nem bizonyítja, hogy a teljes kétprogramos út minden
részlete azonos.

**Független ellenőrzés:** a bináris `0x0090fbb3-0x0090fca4` utasításait
QEMU i386 alatt izolált állapottal futtatva a (súlyösszeg, x-nyomaték,
y-nyomaték) = (0, 0, 0) a `0x00808080`, az (1, 28, -28) a `0x00f08044`
csomagot adja. A második tehát `(kR,kB)=(240,68)`, nem semleges. Ez a
kódrészlet végrehajtása, nem a teljes becslő vagy Picasa-export mérése.
A saját becslővel külön, 144 képpontos fekete képen 127 darab RGB
`(60,32,17)` képpont `(128,128)`-at, 128 darab `(240,68)`-at adott:
a súlyozott összeg a 2-es cellasúly és a cellánkénti 8 bites eltolás miatt
0-ról 1-re vált. A nem nulla összegre feltételezett kaput ez a célzott
ellenpélda cáfolja; más minőségvizsgálatot a teljes láncra nem zár ki.

**Új eredeti exportmérés:** a k02 `colorfix;rainbow` és
`colorfix;rainbow;autocolor` JPEG-ek dekódolt RGB-átlaga rendre
`(162,441590; 90,369685; 93,576364)`, illetve
`(161,475699; 90,390607; 92,591095)`. Közvetlen összevetésük SSIM-je
`0,988790`, átlagos CIE76 ΔE-je `1,102313` (további JPEG-kódolás nélkül).
Ez kis exportkülönbség, nem bizonyítja a belső puffer vagy a mátrix pontos
azonosságát. A fenti becslőágra vonatkozó eredmény **megerősített**; a
`lanc-0132` eltérésének oka továbbra is **nyitott**.

**Következő döntő mérés:** ugyanabban az eredeti futásban a
`0x008f82fa` hívásakor a becslő bemeneti RGB-pufferét és méretét, a
`0x0090fbb5` ponton a súlyösszeget és két nyomatékot, valamint a
`0x0090fc99` által kiírt becslést kell rögzíteni; ugyanezen a nyers
pufferen kell a PicasaPy becslőjét futtatni. A JPEG köztes export erre
nem alkalmas a fent kimutatott újrakódolási érzékenység miatt. A belső
puffer és a natív becslés jelenleg **NINCS MEG**, ezért új küszöb vagy
fejlesztési javítás nem vezethető le.

### A teljes becslő ugyanazon a RGB-pufferen (2026-11-12)

**Megerősített ezen a pufferen:** a `colorfix=1,0.049146,ff2af3a5;`
`rainbow=1,151.657621;` lánc utáni, `720×1280×3` RGB `uint8` kép SHA-256
lenyomata `1883825cbad6136e31b1f3e6239f5a88982bb4c22c09345393db974fb9002367`.
Ezt a változatlan képet adtam a PicasaPy `estimate_illuminant` függvényének
és az eredeti `0x0090f8f0` becslőnek QEMU i386 alatt. A natív bemeneti
szerkezet stride-ja 1280 pixel, szélessége 1280, magassága 720; a pixel
DWORD-ok `0x00RRGGBB` alakban ugyanazokat az RGB-bájtokat tartalmazták.
Az eredeti hívó `0x008f82a0` a képszerkezetet EAX-ban adja át a
`0x008f82fa` híváskor.

| Érték vagy állítás | Forrás |
|---|---|
| A `0x0090f8f0` függvény indexelt mérete 965 bájt | bináris (`0x0090f8f0`, függvényrekord és diszasszemblálás) |
| A két becslő gainje: `kR=240`, `kB=68`; a mátrix zöld gainje 128 | mérés, ugyanazon RGB-puffer, natív QEMU és PicasaPy |
| A `0x0090fc99` által írt becslőcsomag `0x00f08044` | mérés, eredeti Picasa-becslő QEMU i386 alatt |
| A becslés előtti szűrésen átment pixelek és a nyers hisztogram összege: 15899 | mérés, eredeti QEMU-hisztogram |
| A 4096 hisztogramcellából eltérő cellák száma a natív és a PicasaPy hisztogram között: 0 | mérés, cellánkénti összevetés |
| Súlyozott összeg: 1; nyomatékok: `(28,-28)` | mérés, eredeti QEMU-becslő belső állapota |
| A nem nulla súlyozott cella `(B-bin=4,R-bin=60)`: nyers darabszám 144, súly 2, kimenő súly 1 | mérés, QEMU-hisztogram és külön egész-aritmetikájú újraszámítás |
| Az eredeti Picasa tényleges, autocolor előtti RGB-puffere a 004 futásban | NINCS MEG |

Az A út a `0x0090f8f0` utasításainak olvasása: a szűrés, a két előjeles
osztás, a 64×64-es cellákba sorolás, a köbös Chebyshev-súlyozás és a súlypont
kiszámítása. A B út a teljes eredeti becslő QEMU-futtatása az előállított
képen; a natív nyers hisztogram mind a 4096 cellában egyezik a PicasaPy
hisztogramjával. Egy külön, a `cv2.remap` táblájától független egész
képletes újraszámítás ugyanezt a hisztogramot, súlyösszeget, nyomatékokat
és gainpárt adta. A két út egyezik.

**Következtetés:** a becslő nem okoz eltérést ezen az azonos bemeneten.
A korábbi export-összevetésben a PicasaPy autocolor előtti képe az eredeti
004 exporthoz `SSIM=0.989601`, átlagos CIE76 `ΔE=1.275051` értékkel
egyezett, míg a teljes PicasaPy lánc `SSIM=0.927504`, `ΔE=47.759275`
értéket adott. A feladat feltételes ágával összhangban a további vizsgálat
az eredeti `colorfix` utáni `rainbow` kimenetére, vagyis az autocolor
bemeneti pufferére kerül. A 004 JPEG a lánc utáni, veszteséges export;
ebből nem állapítható meg pontosan, hogy a `colorfix` vagy a `rainbow`
egyenként melyik bájtban tér el. Egyikhez sem vezethető le javítás.

**Következő célzott mérés:** az eredeti Picasa teljes 004 futásában a
`0x0090f8f0` belépésekor rögzíteni kell a stride-ot, a méreteket és a teljes
RGB-puffert, valamint a `0x0090fc99` becslőcsomagját. A veszteségmentes
natív puffert kell összehasonlítani ezzel a PicasaPy-pufferrel. Ha az
egyedi `colorfix` és `rainbow` lépések közti felelősséget is meg kell
nevezni, mindkét lépés eredeti kimenetét külön kell rögzíteni. A 004 JPEG
ehhez nem elég.

## Eredeti Picasa veszteségmentes kimeneti utak vizsgálata a végrehajtóhoz (2026-11-13, #6585)

### Cél és kontextus

A #6585 differenciális láncméréseiben (különösen a `lanc-0132` autocolor-becslésénél) a lánc köztes RGB-pufferének kinyerése szükséges, mert a végső JPEG-export veszteséges és a kvantálási zaj megváltoztatja az autocolor hisztogramját. A vizsgálat tárgya, hogy az eredeti `Picasa3.exe` (3.9.141.259) biztosít-e bármilyen automatizálható felhasználói felületi utat veszteségmentes RGB kimenet előállítására:
1. Megőrzi-e a forráskép formátumát a `File > Save`, `Save a Copy` vagy `Export`, ha a bemenet PNG, TIFF vagy BMP?
2. Tartalmaz-e az Export dialógus formátumválasztót (pl. PNG vagy eredeti formátum)?
3. Milyen formátumot helyez a vágólapra a `Ctrl+C` / `Edit > Copy` (`CF_DIB` vagy `CF_BITMAP`), és az mekkora felbontású?

### 1. Forrásformátum megőrzése a mentési és exportálási műveletekben

A bináris visszafejtése igazolja, hogy a Picasa sem a `File > Save` (`&Save`, `0x9d68`), sem a `File > Save As` / `Save a Copy` (`Save a Cop&y`, `0xe103`), sem pedig az Export művelet során **nem őrzi meg** a nem JPEG formátumú (PNG, TIFF, BMP) forrásképek formátumát.

- **`File > Save` (`0x9d68`):** A `CThumbUI` parancskezelő (`0x005cb990` ág `0x9d68`) a `FUN_005e9940`-en át a `CFileSaveThread` indítót (`FUN_0053a790`, vtable: `0x00c8bbd8`) hívja. A `0x0053a790` ellenőrzi a forrásfájl kiterjesztését: nem JPEG fájl esetén a dialógus explicit figyelmeztetést jelenít meg a konverzióról (`typechange1`: `0x00c8a634` szöveg: `"This file will be saved as JPEG."`; több fájl esetén `typechangeX`: `0x00c8a4d8` szöveg: `"Non-JPEG files will be saved as JPEG. Click Skip to leave these files alone."`). A tényleges mentési szálban (`CFileSaveThread::Run`, `FUN_00539020`) a `FUN_00467ca0` mentőrutin a `0x0046b9cf` címen feltétel nélkül a `0x009d63f0` IJG JPEG kódolót hívja. Forrás: `bináris (0x005cb990, 0x005e9940, 0x0053a790, 0x00c8a634, 0x00c8a4d8, 0x00539020, 0x0046b9cf, 0x009d63f0)`.
- **`File > Save As` / `Save a Copy` (`0xe103`):** A `FUN_005e6a20` dialóguskezelő a `0x005e6afb` ponton vizsgálja a forrástípust: kizárólag a `0x1f` belső típuskódú WebP fájloknál ajánlja fel a `SaveAsFilterWebP` szűrőt (`0x00c976c0`: `*.webp`). Minden más képtípusnál (JPEG, PNG, TIFF, BMP) a dialógus szűrője kizárólag `SaveAsFilterJPG` (`0x00c97690`: `*.jpg;*.jpeg`), és a fájlnév végéhez a `0x005e6b48` utasítás a `.jpg` kiterjesztést fűzi hozzá. Az írás a `0x0045c430` objektumon át szintén a JPEG csővezetékbe torkollik. Forrás: `bináris (0x005e6a20, 0x005e6afb, 0x00c976c0, 0x00c97690, 0x005e6b48)`.
- **PNG/TIFF/BMP kódolók hiánya:**
  - *PNG:* A `Picasa3.exe` `.text` szekciójában található befordított libpng (`0x00b10000-0x00b20000`) kizárólag dekódoló rutinokat tartalmaz (`png_read_*`, `png_create_read_struct` `0x00b14c30`). A könyvtár `PNG_NO_WRITE_SUPPORTED` konfigurációval készült: a `png_create_write_struct` és az összes `png_write_*` kódoló függvény teljesen hiányzik a binárisból. A Picasa3.exe fizikailag képtelen PNG fájlt írni. Forrás: `bináris (0x00b10000-0x00b20000, 0x00b14c30)`.
  - *TIFF:* A libTIFF `TIFFClientOpen` (`0x00b4d410`) függvényét a `ytTIFFFileContainer` (`0x00a4f900`, `0x00a4f9d0`) kizárólag olvasási módban (`"r"`) hívja; mentési TIFF író hívás nincs a programban. Forrás: `bináris (0x00b4d410, 0x00a4f900, 0x00a4f9d0)`.
  - *BMP:* A program egyetlen helyen ír BMP fájlt: a Háttérkép beállítása funkcióban (`0x0057aa10` -> `FUN_009ad2d0`), ahol a `0x009ad382` címen `picasabackground.bmp` néven menti a képet `BM` fejléccel (`0x42 0x4d`), a képernyő felbontására méretezve. Mentési vagy exportálási menüből elérhető BMP kimenet nem létezik. Forrás: `bináris (0x0057aa10, 0x009ad2d0, 0x009ad382)`.

### 2. Export dialógus beállításai (`export.fen`, `CExportPrefsDialog`)

Az Export funkció (`Ctrl+Shift+S` vagy menü `0x9d6b`) felülete és végrehajtó kódja nem tartalmaz formátumválasztó opciót:
- **UI definíció:** A `runtime/export.fen` deklarációjában kizárólag a célmappa (`Location`), mappa elnevezése (`Export folder name`), méretezés (`Original size` vagy `Resize to:` pixelcsúszka), JPEG minőség (`Image quality:` `Automatic`, `Normal`, `Maximum`, `Minimum`, `Custom`), videó beállítások (`Movies`) és vízjel (`Watermark`) szerepel. Nem létezik formátumválasztó vezérlőelem (PNG, TIFF vagy eredeti formátum rádiógomb vagy legördülő menü). Forrás: `bináris (runtime/export.fen erőforrás és lefordított FENC tábla)`.
- **Végrehajtási ág:** Az export dialógus vezérlője a `CExportPrefsDialog` (vtable: `0x00c8b764`, parancskezelő: `0x005312b0`). A háttérben futó motor a `CImageOutput::Execute` (`FUN_0073f320`, mérete 9396 bájt), amely fényképek esetén a `0x00740a0f` címen feltétel nélkül a `FUN_009d63f0` IJG JPEG tömörítőt hívja (`0x009d6280`, `0x009d5080`, `0x00ad0f70`). Nincs elágazás más képformátum felé. Forrás: `bináris (0x00c8b764, 0x005312b0, 0x0073f320, 0x00740a0f, 0x009d63f0)`.

### 3. Vágólapra másolás formátuma és felbontása (Edit > Copy / Ctrl+C)

A vágólapra másolás menüparancsa `eMenuEdit::ID_COPY` (`0x9d39`):
- **Hívási lánc:** A `CThumbUI` parancskezelő `0x9d39` esetén meghívja a `FUN_005fe9f0(1)` függvényt. Ha az aktív nézet az `editpanel/preview` szerkesztő előnézet, a vezérlés a `FUN_0069b000` (mérete 565 bájt) függvénynek adódik át, amely az előnézeti felület eszközleírójából kimásolja a képet a `0x00a706f0` hívásával. Forrás: `bináris (0x005cb990, 0x005fe9f0, 0x0069b000, 0x00a706f0)`.
- **Vágólap formátum:** A `USER32.DLL!SetClipboardData` API-nak az egész binárisban mindössze 2 hívása található:
  1. `0x00a70610`: Szövegmásolás (`uFormat = 0x0000000d`, azaz `CF_UNICODETEXT`).
  2. `0x00a706f0`: Képmásolás (`uFormat = 0x00000002`, azaz `CF_BITMAP`).
  A `0x00a706f0` a `CreateCompatibleDC` és `CreateCompatibleBitmap` segítségével GDI DDB bitképet hoz létre, átmásolja a képpontokat a `0x009aa720` rutinnal, majd meghívja a `SetClipboardData(CF_BITMAP = 2, hBitmap)` függvényt a `0x00a70716` címen. Forrás: `bináris (0x00a70610, 0x00a706f0, 0x00a70716)`.
- **DIB kompatibilitás és lekérdezés:** A Windows és a Wine vágólap-alrendszere a `CF_BITMAP` formátumból kérésre automatikusan és szintetikusan előállítja a `CF_DIB` (`8`) és `CF_DIBV5` (`17`) formátumokat a kiolvasó folyamat számára. Így a külső folyamat (pl. a Colab végrehajtó Python szkriptje) veszteségmentes 24/32 bites DIB-ként képes kinyerni a pixeleket.
- **Felbontási korlát:** A `FUN_0069b000` a képet az `editpanel/preview` megjelenítő DC-jéből olvassa ki. Ha a kép a szerkesztőablakhoz van igazítva ("Fit to screen"), a vágólapra másolt bitmap mérete az előnézeti ablak méretéhez van méretezve, nem az eredeti kép méretéhez. A vágólap kizárólag akkor tartalmazza a teljes felbontású veszteségmentes képet, ha az előnézet 100%-os nagyításban áll ("Actual size", 1:1 nézet), vagy ha a forráskép kisebb a megjelenítő ablaknál és nem méreteződik át.

### 4. Két független bizonyítási út és cáfoló kísérletek

| Kérdés | Út A (Vezérlési gráf és hívások) | Út B (Erőforrás és könyvtáraudit) | Cáfoló kísérlet |
|---|---|---|---|
| **1. Forrásformátum megőrzése** | `0x0053a790` nem JPEG esetén figyelmeztet (`0x00c8a634`), `0x0046b9cf` és `0x005e6b48` kizárólag a `0x009d63f0` JPEG kódolót hívja. | A libpng (`0x00b10000-0x00b20000`) nem tartalmaz író rutint (`PNG_NO_WRITE_SUPPORTED`); a libTIFF (`0x00b4d410`) csak olvas (`"r"`). | Ha létezne PNG mentési ág, a binárisban szerepelnie kellene a `png_write_*` API hívásnak; a teljes `.text` pásztázás 0 találatot ad. |
| **2. Export dialógus opciók** | `FUN_0073f320` (`CImageOutput::Execute`) a `0x00740a0f` címen feltétel nélkül a `0x009d63f0` JPEG kódolót indítja el. | Az `export.fen` UI leíróban kizárólag méret, JPEG minőség és vízjel opció van, formátumválasztó nincs. | Ha lenne rejtett PNG export beállítás, a `FUN_0073f320` elágazna a formátumkód szerint; a vezérlési gráfban nincs alternatív képíró hívás. |
| **3. Vágólap formátum** | A `0x00a706f0` függvény a `0x00a70716` címen fix `push 2` paraméterrel hívja a `SetClipboardData(CF_BITMAP, hBitmap)`-ot. | A `USER32.DLL!SetClipboardData` import táblás hívásai között a képmásolásra egyetlen hely van (`0x00a706f0`), DIB formátumkód (`8`) közvetlenül nem szerepel. | Ha a Picasa közvetlenül `CF_DIB`-et írna, a `SetClipboardData` argumentumaként a `0x00000008` értéknek kellene megjelennie; a diszasszemblálás ezt kizárja. |

### 5. Konkrét felhasználói / automatizálási lépéssorrend a végrehajtónak

Mivel a Picasa nem támogat veszteségmentes fájlmentést és fájlexportot, a Colab végrehajtó nem tud közvetlen fájlírással (File > Save vagy Export) veszteségmentes köztes képet generálni. A végrehajtó két megvalósítható utat használhat a köztes RGB puffer megszerzésére:

#### A módszer: Vágólap kiolvasása 1:1 nézet mellett (UI automatizálással)
1. **Előkészítés:** A tesztkép és a szűrőlánc `.picasa.ini` fájljának elhelyezése a könyvtárban.
2. **Megnyitás:** A Picasa elindítása és a kép megnyitása a szerkesztő előnézetben (`editpanel/preview`).
3. **1:1 nagyítás beállítása:** Az előnézeti ablakban az 1:1 ("Actual size", 100%) zoom aktiválása (hogy a megjelenítő felület ne méretezze le a képet az ablakhoz). Kisebb tesztképeknél (pl. 720×1280-nál kisebb vagy akkora, amely a teljes virtuális kijelzőn méretezés nélkül elfér) az alapértelmezett nézet is elegendő.
4. **Vágólapra másolás:** `Ctrl+C` (vagy `Alt+E` -> `C`, parancskód `0x9d39`) elküldése az aktív szerkesztőablaknak.
5. **Vágólap lekérdezése:** A Colab Python segédfolyamatából a Windows/Wine vágólap megnyitása (`OpenClipboard`) és az automatikusan szintetizált `CF_DIB` (formátumkód `8`) lekérdezése (`GetClipboardData(8)`).
6. **Kép kibontása:** A kapott memóriaterületből a `BITMAPINFOHEADER` fejléc (szélesség, magasság, bitmélység) és a 24/32 bites BGR pixeltömb kiolvasása, majd elmentése veszteségmentes PNG formátumban.

#### B módszer: QEMU / GDB hook a belső memóriapufferre (ajánlott, determinisztikus)
1. Mivel az UI automatizálás ablakméret- és fókuszfüggő, a determinisztikus szűrőlánc-kutatáshoz a legmegbízhatóbb út a `0x0090f8f0` (autocolor becslő) vagy a láncvégrehajtó `FUN_00907f30` (`0x00908077`) belépési pontján elhelyezett töréspont.
2. A belépéskor az EAX-ban átadott képszerkezetből a nyers 24/32 bites RGB képpuffer és dimenziók közvetlenül kiolvashatók memóriából, megelőzve bármilyen ablakméretezést és a végső JPEG kódolást.

## #6585 - 200 láncos újrafuttatás, r6611 mag (2026-11-13)

### Módszer és adat-azonosítás

A mérést a `89b1e5475` revízió PicasaPy-kódjával végeztem. A k01-k10 forrásképek helyi `kombinalt` készlete a `.meres-6585/minimalizalas/forras/` könyvtárban volt; a fájlméret a tízrekordos névjegyzékkel egyezett. A fájlok méretét és SHA-256-át rögzíti ez a táblázat:

| Kép | Bájt | SHA-256 |
|---|---:|---|
| `k01.jpg` | 371575 | `0bffd7c55ba1abaa9cd036ff086f9443c49b3f043927e942b2b418aef34dd526` |
| `k02.jpg` | 290970 | `c90a3a7bc984b9c9bdc4fd1520a69332f394a14a6e730c2b043651988cb8af6e` |
| `k03.jpg` | 161680 | `a7d74f17df8ec7b6a11d6152c2a52ec4064c1ca927f7239bf2338ec6eaa8c354` |
| `k04.jpg` | 284501 | `1900ed7dcdef42f02116b54c6ad9fb5249e0e8423d0ec5c0cedb427a8d6daff9` |
| `k05.jpg` | 417584 | `8d0b84ab46a63879d6cd3dd4c4e585f3be2f584adedbb971f234e1a2e05a38f0` |
| `k06.jpg` | 133894 | `64953e7c24f1237549c2d60881c95fd41f325a37178f561c81d1d7a90a57fa63` |
| `k07.jpg` | 243178 | `12962454b615e46f43059942a25b6e4c45ddc634cbc58e0b7454435ce176033d` |
| `k08.jpg` | 478825 | `206a0cced72af538f5f925ce96f8f94be8e1908e15ff54e757313d2e8a56d866` |
| `k09.jpg` | 412632 | `34d41fe1d175a72fbd06d47df0e05b707f37489f6bc5b99e56edf2b487e369d5` |
| `k10.jpg` | 329555 | `d963fc0bf5d8223ae698b6264350b5decd91beb235bf81c3fa02d06706cc37b5` |

A Picasa eredeti exportpárjai a 496-515-ös Colab-feladatok kimenetei: `koteg-001` → 496, …, `koteg-020` → 515; mind a 200 `export__kNN.jpg` megvolt és dekódolható volt. A megadott `6585-r6611-eredeti/` könyvtárban csak letöltési naplók voltak, ezért a meglévő exportokat a helyi `6585-eredeti/job-<szám>/job-<szám>/` könyvtárakból olvastam. A fájlokat nem másoltam a repóba.

A GitHubon tárolt feladat-törzseket ebben a körben nem olvastam. A 200 pontos láncot a feladatban rögzített `r6611`/6611 maggal, a `scripts/differencialis_lanc.py` determinisztikus generátorával állítottam elő. A generátor a `d07bb6038` (#6649, 2026-11-07) óta nem változott. A második generálásban mind a 200 rekord, mind a 20 INI és a 20 feladat-JSON bájtra egyezett; a `lancok.json` SHA-256 mindkét alkalommal `c6ccc6b768000368835395ec2de4a5e9821a890196d72338fcdb2dca38021d11` volt. Ez a helyi mag-reprodukálhatóság bizonyítéka, nem a GitHub-feladat-törzsek külön ellenőrzése.

Az egyparancsos futás:

```sh
python3 scripts/differencialis_lanc.py futtatas --mag 6611 --db 200 \
  --nevjegyzek <kombinalt/nevjegyzek.json> --kepek <kombinalt/kepek> \
  --mintakeszlet kombinalt --ki <kimeneti-konyvtar> --eredeti <r6611-exportok>
```

A pármásító a meglévő `tools/golden/compare_render.py` mércéjét használja: `pixel_tol=1`, `frac_tol=0.002`, `ssim_min=0.98`, `de_mean_max=2.0`. A PicasaPy PNG-t az eredeti JPEG mintavételezésével és kvantálótábláival kódolja újra az összevetés előtt. A külön `sajat` + `osszevet` futás és az egyparancsos `futtatas` azonos 200 láncot, mérőszámot és ítéletet adott; mind a 200 saját PNG bájtra egyezett a két futás között.

### Összesített eredmény és besorolás

| Végső besorolás | Lánc | A nyers összevetésből egyezik | A nyers összevetésből eltér |
|---|---:|---:|---:|
| Véletlenállapot-függő: grain, grain2, triple3 | 37 | 27 | 10 |
| Dokumentált dither: triple2 (#6746/#3092) | 11 | 9 | 2 |
| Egyéb determinisztikus (ebből 1 valódi eltérés) | 152 | 151 | 1 |
| Összes lánc | 200 | 187 | 13 |

A `grain`, `grain2` és `triple3` szűrők 37 láncban szerepelnek; ezek 27 nyers mérése egyezik, 10 tér el. Ezeket jelöli az összevető `veletlenfuggo` mezője. A `triple2` további 11, velük diszjunkt láncban jelenik meg; 9 egyezik és 2 tér el. A két eltérés (`lanc-0006`, `lanc-0092`) a már dokumentált, folyamat-globális árnyalási fázis esete, ezért besorolásuk `dokumentált`, nem új véletlenállapot-jelölés: a #6746-ban leírt `0x00d67f74`/`0x00d67f7c` állapot és a `0x0090beed`-`0x0090bf25` árnyalási út támasztja alá (#3092). A `PicnikGrain` szintén pszeudovéletlen zajt számol, de a `0x00bce8c0` worker lokális MT-állapotát a `0x00bbee70` attribútum-parserhez kötött, `runtime/filterdesc.xml:925`-ben rögzített `randomSeed=1` indítja; ezért nem folyamatállapot-függő és nem kerül a véletlenállapot-függő szűrők listájába.

A 13 nyers eltérésből 10 véletlenállapot-jelölésű láncban van; 2 a `triple2` árnyalási (dither) fázisát érinti (`lanc-0006`, `lanc-0092`). Az egyetlen másik eltérés a `lanc-0196` / `k06.jpg`:

```text
radtint=1,0.226147,0.991993,0.840316,ff0315bf;
glow=1,0.282406,77.572966;
PicnikGrain=1,5.192805,1;
triple=1,0.766429,-0.177472,0.655993;
```

Mért SSIM: **0.97879**; átlagos ΔE: **0.762**. A meglévő ítélet-küszöbök közül az SSIM marad alatta a 0.98-nak; új küszöböt nem vezettem be. A pontos eltérő szűrő nincs lokalizálva.

### Független bizonyítékutak és cáfoló kísérlet

| Út | Bizonyíték | Eredmény |
|---|---|---|
| A - a Noise worker állapota | A teljes `0x00bce8c0` függvényben a seed argumentum a `0x00bce904`-nél kerül a regiszterbe; a helyi MT-tömb címe `0x00bce90e`-nél kerül a `0x00aa28f0`-nak; a ciklus a `0x00bce9be`-nél a helyi állapotot twisteli a `0x00aa2930`-mal. A callback 696 bájtját az index adja. | A zajgenerátor állapota callbackenként lokális, tehát önmagában nem a folyamat CRT/MT-fázisától függ. |
| B - az attribútum és a kimenet | A `0x00bbee70` parser a `randomSeed` mezőt a `+0x24`-re tölti; a `0x00bbefa0` apply-függvény ezt az értéket továbbadja a workernek. A független leíróforrás `runtime/filterdesc.xml:915-927`, ahol `PicnikGrain` `randomSeed="1"`-et ad. A 684-es eredeti exporttal végzett mérés (forrás/export: tar tagok `684-merokeszlet/picnikgrain__alap.jpg` és `684-merokeszlet/export/picnikgrain__alap.jpg`) átlagos CIE76 ΔE-je 0,882; két helyi render pixelazonos. | A leíró fix magja és a worker helyi állapota egymástól külön úton igazolja, hogy a `PicnikGrain` nem processzállapot-függő. |
| C - a többi állapotút | `grain`/`grain2` külön verembeli MT-állapota és CRT-magja: `0x008f8918`, `0x0090a349`, `0x0090a366`, `0x0090a3e8`; `triple3` folyamat-globális MT: `0x008f8ce0`, `0x0090bf0f`, `0x0090bf1f`; `triple2` globális dither: `0x008f8b90`, `0x0090beed`, `0x00d67f74`, `0x00d67f7c` | A 10 grain/grain2/triple3 eltérés véletlenállapot-függő; a 2 triple2 eltérés dokumentált ditherfázis. A triple2 képletét külön QEMU-mérés igazolta: rögzített puffer/LUT/mintasor mellett 1331/1331 pixel egyezik (#6746). |

**Cáfoló kísérlet.** Azt a hipotézist próbáltam cáfolni, hogy a `PicnikGrain` a `grain`/`grain2`/`triple3`-hoz hasonlóan a folyamat közös véletlenállapotából kap mintát. A teljes, indexből méretezett `0x00bce8c0` callback diszasszemblálásában közvetlen hívásai kizárólag a nullázó rutin (`0x00bf37c0`), a lokális magkiterjesztő (`0x00aa28f0`) és a lokális twist (`0x00aa2930`); a CRT `_rand` címe `0x00c08221`, amely a globális MT seed útban szerepel, nem callback-cél. A callback a `0x00d67f74`/`0x00d67f7c` globális mezőket sem használja. Ezt az ellenhipotézist a független descriptor/parser út is cáfolja: `randomSeed="1"` → `0x00bbee70` `+0x24` → `0x00bbefa0` → `0x00bce8c0`. A #3757 mérése az eredeti 684-es exporthoz 0,882 CIE76 ΔE-t adott, a két helyi render pixelazonos volt. A cáfolat tehát ugyanazzal a mércével ellenőrizve is fennmarad.

### Minimalizáló jelöltek és hátralévő eredeti mérések

A `minimalizal` parancs 3 jelöltet állított elő a `lanc-0006`-hoz, 6-ot a `lanc-0092`-höz és 4-et a `lanc-0196`-hoz. A két `triple2`-es lánc a #6746/#3092 alapján dokumentált ditherfázis. A `lanc-0196` négy egytagú elhagyását helyben újrarendereltem; az alábbi mérés mindegyiket az eredeti, teljes négytagú Picasa-exporthoz hasonlítja, ezért csak a helyi kihagyás hatását méri, nem a jelölt saját Picasa-kimenetéhez való egyezést.

| Eredeti lánc | Jelölt | Megtartott szűrőlánc |
|---|---|---|
| `lanc-0006` | `minimal-lanc-0006-001` | `PencilSketch=1,4.755893,138.441716,38.106939;<br>Matte=1,36.605066,1.037901,35.407827,006a56c5;<br>` |
| `lanc-0006` | `minimal-lanc-0006-002` | `triple2=1,0.353929,0.561445,0.669098;<br>Matte=1,36.605066,1.037901,35.407827,006a56c5;<br>` |
| `lanc-0006` | `minimal-lanc-0006-003` | `triple2=1,0.353929,0.561445,0.669098;<br>PencilSketch=1,4.755893,138.441716,38.106939;<br>` |
| `lanc-0092` | `minimal-lanc-0092-001` | `Holga=1,22.614409,4.438738,43.835078;<br>bw=1;<br>Vignette=1,20.932422,1.309737,44.312252,007ad4f0;<br>triple2=1,0.715390,0.972654,0.166040;<br>Sixties=1,1.063431,00b4487b,0;<br>` |
| `lanc-0092` | `minimal-lanc-0092-002` | `FocalZoom=1,0.200816,0.335034,57.693561,72.470265,45.311039,46.400651;<br>bw=1;<br>Vignette=1,20.932422,1.309737,44.312252,007ad4f0;<br>triple2=1,0.715390,0.972654,0.166040;<br>Sixties=1,1.063431,00b4487b,0;<br>` |
| `lanc-0092` | `minimal-lanc-0092-003` | `FocalZoom=1,0.200816,0.335034,57.693561,72.470265,45.311039,46.400651;<br>Holga=1,22.614409,4.438738,43.835078;<br>Vignette=1,20.932422,1.309737,44.312252,007ad4f0;<br>triple2=1,0.715390,0.972654,0.166040;<br>Sixties=1,1.063431,00b4487b,0;<br>` |
| `lanc-0092` | `minimal-lanc-0092-004` | `FocalZoom=1,0.200816,0.335034,57.693561,72.470265,45.311039,46.400651;<br>Holga=1,22.614409,4.438738,43.835078;<br>bw=1;<br>triple2=1,0.715390,0.972654,0.166040;<br>Sixties=1,1.063431,00b4487b,0;<br>` |
| `lanc-0092` | `minimal-lanc-0092-005` | `FocalZoom=1,0.200816,0.335034,57.693561,72.470265,45.311039,46.400651;<br>Holga=1,22.614409,4.438738,43.835078;<br>bw=1;<br>Vignette=1,20.932422,1.309737,44.312252,007ad4f0;<br>Sixties=1,1.063431,00b4487b,0;<br>` |
| `lanc-0092` | `minimal-lanc-0092-006` | `FocalZoom=1,0.200816,0.335034,57.693561,72.470265,45.311039,46.400651;<br>Holga=1,22.614409,4.438738,43.835078;<br>bw=1;<br>Vignette=1,20.932422,1.309737,44.312252,007ad4f0;<br>triple2=1,0.715390,0.972654,0.166040;<br>` |
| `lanc-0196` | `minimal-lanc-0196-001` | `glow=1,0.282406,77.572966;<br>PicnikGrain=1,5.192805,1;<br>triple=1,0.766429,-0.177472,0.655993;<br>` |
| `lanc-0196` | `minimal-lanc-0196-002` | `radtint=1,0.226147,0.991993,0.840316,ff0315bf;<br>PicnikGrain=1,5.192805,1;<br>triple=1,0.766429,-0.177472,0.655993;<br>` |
| `lanc-0196` | `minimal-lanc-0196-003` | `radtint=1,0.226147,0.991993,0.840316,ff0315bf;<br>glow=1,0.282406,77.572966;<br>triple=1,0.766429,-0.177472,0.655993;<br>` |
| `lanc-0196` | `minimal-lanc-0196-004` | `radtint=1,0.226147,0.991993,0.840316,ff0315bf;<br>glow=1,0.282406,77.572966;<br>PicnikGrain=1,5.192805,1;<br>` |

| Helyi változat | Kihagyott szűrő | SSIM a teljes Picasa-exporttal | ΔE | Nyers ítélet |
|---|---|---:|---:|---|
| Teljes `lanc-0196` | - | 0.97879 | 0.762 | eltér |
| `minimal-lanc-0196-001` | `radtint` | 0.70651 | 51.517 | eltér |
| `minimal-lanc-0196-002` | `glow` | 0.96979 | 2.749 | eltér |
| `minimal-lanc-0196-003` | `PicnikGrain` | 0.75560 | 5.281 | eltér |
| `minimal-lanc-0196-004` | `triple` | 0.41130 | 46.968 | eltér |

Ezek a mérések nem nevezik meg a hibás szűrőt: az eltávolított műveletet tartalmazó teljes Picasa-export a jelölteknek nem megfelelő referencia. A négy jelölt saját eredeti Picasa-exportja **NINCS MEG**, ezért a `lanc-0196` minimalizált formája és kiváltó effektje továbbra is nyitott. A célzott bináris utak: `radtint` `0x008f8730` → `0x0090b370`; `glow` `0x0090d4b0`; `PicnikGrain` Noise worker `0x00bce8c0`, magargumentum `0x00bce904`, lokális state `0x00bce90e`; `triple` callback `0x008f8a60`, amely a `0x0090ac20` Derítőfényt és a `0x0090c2c0` kontrasztmagot hívja. Ezek a hivatkozások a vizsgálandó utak, nem bizonyítják, melyik szűrő okozza a mért eltérést.

**A #6585 elfogadási pontjai:**

- ✅ 200 lánc lefutott mindkét oldalon, 0 helyi hiba és 0 hiányzó export; a táblázat lánconként tartalmazza a szűrősorokat, SSIM-et, ΔE-t és besorolást.
- ⛔ A jegy szó szerinti feltétele („Minden eltérésnek van minimalizált formája és saját jegye”) nem teljesült: a 10 nyers véletlenállapot-függő és 2 dokumentált `triple2` dithereltérés besorolása megvan, de ezekhez nincs ebben a kötegben lánconkénti minimalizált alak és saját jegy bizonyítva. A determinisztikus `lanc-0196`-hoz négy helyi egytagú jelölt készült, de saját Picasa-exportjuk hiányzik, ezért sem a minimum, sem a kiváltó szűrő nem bizonyított, és nincs saját fejlesztői jegye. Ha a feltétel csak a javítható determinisztikus eltérésre vonatkozik, ez az egy lánc a fennmaradó akadály.
- ✅ Egyparancsos, 6611-es magú futás megismételhető: a két futás mind a 200 rekordban, képkimenetben, SSIM/ΔE értékben és ítéletben azonos.

**Besorolás:** a 200 láncos futás és az egyparancsos ismétlés mérési úton megerősített; a `grain`/`grain2`/`triple3` véletlenállapot-út és a `triple2` globális ditherút bináris címmel dokumentált. A `PicnikGrain` külön workerének lokális, fix seedű állapota két független úton ellenőrzött. A `lanc-0196` valódi, determinisztikus mérési eltérés; gyökere nyitott. A jegy **nem zárható le**: legalább ehhez a lánchoz hiányzik a saját Picasa-exportokon igazolt minimális alak és a fejlesztői jegy. A szó szerinti elfogadási feltétel szerint a 12 besorolt, de lánconként nem minimalizált nyers eltérés elfogadottságát is tisztázni kell.

### A 200 lánc teljes mérési táblája

Az „Nyers ítélet” a meglévő golden-mérce szerinti egyezés/eltérés. A „Végső besorolás” oszlop külön jelöli az egyező láncokat, a véletlenállapot-függő eseteket, a #6746/#3092 alapján dokumentált, `triple2` árnyalási fázisú láncokat és az egyetlen valódi, determinisztikus eltérést. A triple2 és a grain/grain2/triple3 csoport diszjunkt.

| Lánc | Kép | Szűrőlánc | SSIM | ΔE átlag | Nyers ítélet | Végső besorolás |
|---|---|---|---:|---:|---|---|
| `lanc-0001` | `k01.jpg` | `filters=colortemp=1,-0.186619,0.170393;<br>blur=1,-0.075875;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0002` | `k02.jpg` | `filters=colorfix=1,0.398832,ffd83252;<br>enhance=1;<br>rainbow=1,160.259020;<br>` | 0.99147 | 1.101 | egyezik | egyezik |
| `lanc-0003` | `k03.jpg` | `filters=glow2=1,0.176488,90.006316;<br>bw=1;<br>` | 0.99997 | 0.004 | egyezik | egyezik |
| `lanc-0004` | `k04.jpg` | `filters=grain2=1;<br>unsharp2=1,1.459082;<br>radtint=1,0.032885,0.828506,0.574604,ff37e882;<br>CrossProcess=1,60.165014;<br>Border=1,97.349100,0.199461,80.797266,0035b870,00020889,87.496687;<br>` | 0.99924 | 0.037 | egyezik | véletlenállapot-függő |
| `lanc-0005` | `k05.jpg` | `filters=Boost=1,79.437285;<br>sat=1,-0.344986;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0006` | `k06.jpg` | `filters=triple2=1,0.353929,0.561445,0.669098;<br>PencilSketch=1,4.755893,138.441716,38.106939;<br>Matte=1,36.605066,1.037901,35.407827,006a56c5;<br>` | 0.94413 | 1.091 | eltér | dokumentált |
| `lanc-0007` | `k07.jpg` | `filters=linblur=1,0.694407,0.208896,8.668856;<br>glow=1,0.100760,1.547072;<br>` | 0.99967 | 0.031 | egyezik | egyezik |
| `lanc-0008` | `k08.jpg` | `filters=sepia=1;<br>colorfix=1,0.348107,ff551d60;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0009` | `k09.jpg` | `filters=dir_brite=1,0.510349,-0.977812;<br>ansel=1,ffd18d0a;<br>gamma=1,0.513673;<br>unsharp2=1,0.893193;<br>Boost=1,45.559630;<br>dir_sat=1,-0.115902,-0.159805;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0010` | `k10.jpg` | `filters=Sixties=1,88.119383,00593181,0;<br>rainbow=1,52.797603;<br>backlight=1,0.688268;<br>` | 0.99202 | 0.788 | egyezik | egyezik |
| `lanc-0011` | `k01.jpg` | `filters=Vignette=1,49.382959,1.041341,74.879321,00aa4b68;<br>colorfix=1,-0.386481,ff07c907;<br>DropShadow=1,13.326314,140.694265,6.561351,00a1851f,004fc1bb,29.233509;<br>unsharp2=1,0.187959;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0012` | `k02.jpg` | `filters=QuantizePalette=1,22.763772,24.292920,74.028879;<br>QuantizePalette=1,6.195182,99.324529,22.388031;<br>Vignette=1,14.494114,1.129295,25.362371,00a11b23;<br>PicnikGrain=1,30.668119,1;<br>IR=1,83.778311;<br>` | 0.99589 | 0.427 | egyezik | egyezik |
| `lanc-0013` | `k03.jpg` | `filters=colortemp=1,0.409859,0.276916;<br>colorfix=1,-0.386505,ff8f5cf9;<br>warm=1;<br>Holga=1,66.068542,43.915118,91.526892;<br>ansel=1,ff780153;<br>Border=1,86.490755,31.149465,32.170307,0054a3ee,00560e6c,40.816450;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0014` | `k04.jpg` | `filters=autocontrast=1;<br>gamma=1,0.489594;<br>tint=1,119.682738,ffdeb531;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0015` | `k05.jpg` | `filters=Neon=1,69.630938,003eeceb;<br>triple2=1,0.724372,0.596087,0.496682;<br>` | 0.99093 | 1.232 | egyezik | dokumentált |
| `lanc-0016` | `k06.jpg` | `filters=tint=1,236.184001,ff848341;<br>HeatMap=1,-137.793466,78.923172;<br>unsharp2=1,2.816710;<br>autocontrast=1;<br>radblur=1,0.962068,0.464613,-0.500600,0.863510;<br>RoundedEdges=1,79.998300,00821966;<br>` | 0.99792 | 0.143 | egyezik | egyezik |
| `lanc-0017` | `k07.jpg` | `filters=linblur=1,0.007809,0.476395,2.884600;<br>bw=1;<br>` | 0.9999 | 0.007 | egyezik | egyezik |
| `lanc-0018` | `k08.jpg` | `filters=PicnikGrain=1,1.053352,0;<br>radsat=1,0.460831,0.925161,-0.466514,0.326360;<br>colorfix=1,0.326998,ffdea543;<br>` | 0.99997 | 0.046 | egyezik | egyezik |
| `lanc-0019` | `k09.jpg` | `filters=Vignette=1,27.325321,1.415134,36.959126,002e9072;<br>colorfix=1,0.078963,ffa3bbd4;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0020` | `k10.jpg` | `filters=unsharp2=1,1.474926;<br>shadow=1,0.837726,0.933272,0.690145;<br>Lomo=1,83.520942,41.007033;<br>DropShadow=1,5.325084,342.489311,48.790589,002800f8,0049f93e,77.183200;<br>bw=1;<br>` | 0.99747 | 0.122 | egyezik | egyezik |
| `lanc-0021` | `k01.jpg` | `filters=grain=1;<br>dir_sharp=1,0.939847,-0.019565;<br>warm=1;<br>gamma=1,0.484542;<br>enhance=1;<br>DropShadow=1,12.709516,251.903988,30.300114,00c56795,00b92aec,81.597921;<br>` | 0.99958 | 0.263 | egyezik | véletlenállapot-függő |
| `lanc-0022` | `k02.jpg` | `filters=whitept=1,ff427af7;<br>colorfix=1,0.377496,ff304cf2;<br>PicnikTint=1,98.583230,001ff925;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0023` | `k03.jpg` | `filters=autocolor=1;<br>LocalContrast=1,16.644942,1.894741;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0024` | `k04.jpg` | `filters=enhance=1;<br>radsat=1,0.140026,0.243661,0.830321,0.149435;<br>Polaroid=1,-1.924407,00f73a24;<br>LocalContrast=1,3.989427,2.633172;<br>` | 0.99439 | 0.387 | egyezik | egyezik |
| `lanc-0025` | `k05.jpg` | `filters=LocalContrast=1,18.281001,2.434497;<br>autocontrast=1;<br>radblur=1,0.052432,0.623006,-0.257613,0.394909;<br>` | 0.99889 | 0.12 | egyezik | egyezik |
| `lanc-0026` | `k06.jpg` | `filters=dir_sat=1,0.761099,-0.474789;<br>enhance=1;<br>colortemp=1,0.029381,0.432989;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0027` | `k07.jpg` | `filters=sat=1,-0.509702;<br>tint=1,153.852601,ff8fa1d2;<br>radtint=1,0.234644,0.554567,0.097081,ff93882f;<br>HDR=1,56.244098,4.390564,57.764370;<br>` | 0.99495 | 0.809 | egyezik | egyezik |
| `lanc-0028` | `k08.jpg` | `filters=radsat=1,0.594856,0.874318,0.914568,0.556115;<br>backlight=1,0.249480;<br>` | 0.99996 | 0.067 | egyezik | egyezik |
| `lanc-0029` | `k09.jpg` | `filters=HDR=1,74.444218,4.874307,59.080544;<br>grain2=1;<br>Pixelate=1,17.528033,7.822953,92.572618;<br>unsharp=1,0.281053;<br>grain2=1;<br>radtint=1,0.635906,0.570768,0.323622,ff6cd4b0;<br>` | 0.92937 | 2.912 | eltér | véletlenállapot-függő |
| `lanc-0030` | `k10.jpg` | `filters=glow2=1,0.988967,53.077548;<br>Vignette=1,48.118760,1.271834,15.610695,008e9607;<br>PicnikGrain=1,49.273716,1;<br>` | 0.99965 | 0.06 | egyezik | egyezik |
| `lanc-0031` | `k01.jpg` | `filters=unsharp2=1,2.705823;<br>PicnikTint=1,80.497143,0039fe11;<br>TwoTone=1,47.848031,44.812250,91.460769,00107e2b,000a1716;<br>autocontrast=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0032` | `k02.jpg` | `filters=NightVision=1,41.469555,-4.042923,85.199158;<br>dir_tint=1,0.814029,0.977772,0.563173,0.424376,ff091917;<br>MuseumMatte=1,59.123649,58.298264,00a83687,00d97d21;<br>backlight=1,0.314711;<br>glow2=1,0.942782,46.843069;<br>` | 0.99969 | 0.035 | egyezik | egyezik |
| `lanc-0033` | `k03.jpg` | `filters=RoundedEdges=1,9.896305,001a564f;<br>gamma=1,0.533075;<br>ansel=1,ff959937;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0034` | `k04.jpg` | `filters=whitept=1,ff2c7d1d;<br>dir_sat=1,-0.822760,0.936165;<br>PicnikTint=1,71.949966,0095b1f2;<br>warm=1;<br>Soften=1,95.039224,62.947873;<br>Vignette=1,0.591138,1.331890,41.763294,00e02922;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0035` | `k05.jpg` | `filters=triple3=1,0.575456,0.443872,0.428327;<br>DropShadow=1,16.198111,206.657105,39.004230,00f24f24,00bc2c74,73.095673;<br>Boost=1,45.120193;<br>HeatMap=1,68.817307,15.886127;<br>` | 0.95529 | 2.443 | eltér | véletlenállapot-függő |
| `lanc-0036` | `k06.jpg` | `filters=PicnikFocalPixelate=1,0.325967,0.547827,16.876859,24.286039,33.031128,18.666656,0;<br>Comicize=1,11.078660,79.899687,18.999972;<br>dir_sat=1,0.609193,0.005104;<br>DropShadow=1,22.105014,31.742711,18.297244,00aa82ad,002add15,52.890761;<br>` | 0.99967 | 1.324 | egyezik | egyezik |
| `lanc-0037` | `k07.jpg` | `filters=DropShadow=1,14.449592,263.792550,21.631741,002afed1,0021adbf,57.873494;<br>contrast=1,-0.340556;<br>dir_sharp=1,0.620125,-0.138905;<br>Pixelate=1,8.682883,3.724332,56.400080;<br>triple=1,-0.141159,-0.275231,0.111294;<br>Vignette=1,26.104794,1.469297,22.956791,00099f55;<br>` | 0.9901 | 0.507 | egyezik | egyezik |
| `lanc-0038` | `k08.jpg` | `filters=IR=1,58.524869;<br>TwoTone=1,70.398690,19.022712,45.538209,00fabc40,0087d330;<br>backlight=1,0.576684;<br>CrossProcess=1,17.006476;<br>LocalContrast=1,10.254913,1.303263;<br>` | 0.99322 | 0.472 | egyezik | egyezik |
| `lanc-0039` | `k09.jpg` | `filters=gamma=1,-0.886429;<br>gamma=1,0.337171;<br>Pixelate=1,121.919674,0.881240,23.509121;<br>autolight=1;<br>autocolor=1;<br>` | 0.99147 | 0.861 | egyezik | egyezik |
| `lanc-0040` | `k10.jpg` | `filters=PicnikFocalPixelate=1,0.938932,0.055666,63.899952,40.246119,24.778142,86.140656,1;<br>whitept=1,ff60b7cc;<br>Lomo=1,63.253099,9.219628;<br>dir_brite=1,0.209511,0.704375;<br>tint=1,196.064428,ff340374;<br>` | 0.99309 | 0.96 | egyezik | egyezik |
| `lanc-0041` | `k01.jpg` | `filters=Invert=1;<br>shadow=1,0.127168,0.020700,0.644804;<br>Matte=1,21.701463,1.829720,1.774741,00e383bf;<br>PencilSketch=1,4.691083,72.153865,61.065989;<br>blur=1,-0.488803;<br>triple3=1,0.994651,0.255145,0.453340;<br>` | 0.99895 | 0.085 | egyezik | véletlenállapot-függő |
| `lanc-0042` | `k02.jpg` | `filters=Holga=1,19.807420,28.588641,14.358908;<br>PencilSketch=1,3.751142,178.333242,97.622923;<br>Holga=1,62.417468,80.648239,54.566616;<br>unsharp2=1,0.211557;<br>radtint=1,0.304685,0.053998,0.619155,ff6cd848;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0043` | `k03.jpg` | `filters=Comicize=1,64.436887,51.799444,5.979713;<br>PencilSketch=1,3.019305,112.212946,82.858829;<br>Pixelate=1,14.817655,7.275165,79.646640;<br>` | 0.99114 | 0.309 | egyezik | egyezik |
| `lanc-0044` | `k04.jpg` | `filters=Invert=1;<br>FocalZoom=1,0.694063,0.262598,95.724781,44.534093,31.701896,95.248516;<br>` | 0.99881 | 0.552 | egyezik | egyezik |
| `lanc-0045` | `k05.jpg` | `filters=Lomo=1,46.582506,11.216901;<br>bw=1;<br>Matte=1,41.108009,1.812336,15.609063,00117c9a;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0046` | `k06.jpg` | `filters=colorfix=1,0.253484,ff31fc39;<br>colorfix=1,-0.457186,ff7ecc1b;<br>glow2=1,0.302164,49.440935;<br>NightVision=1,-21.289610,-46.210878,56.175546;<br>` | 0.99961 | 0.037 | egyezik | egyezik |
| `lanc-0047` | `k07.jpg` | `filters=radtint=1,0.549170,0.266124,0.875778,ff7a7d44;<br>NightVision=1,-35.698271,8.943954,73.415050;<br>whitept=1,ff7b537c;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0048` | `k08.jpg` | `filters=ansel=1,ffc01823;<br>autocolor=1;<br>dir_sharp=1,-0.762359,0.594174;<br>` | 0.99961 | 0.097 | egyezik | egyezik |
| `lanc-0049` | `k09.jpg` | `filters=HDR=1,17.668737,4.425134,78.980889;<br>Border=1,28.091795,41.467039,13.263953,00ef3929,0082b27d,48.492351;<br>autobacklight=1;<br>dir_sat=1,-0.086724,0.619416;<br>autocontrast=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0050` | `k10.jpg` | `filters=Border=1,74.824396,10.412875,0.521946,003ef087,00affbff,80.716473;<br>triple2=1,0.874882,0.784122,0.690043;<br>dir_brite=1,-0.743387,0.782761;<br>colorfix=1,0.353365,ff61032b;<br>triple=1,0.367237,-0.007519,0.422926;<br>Pixelate=1,38.833704,3.415533,5.483465;<br>` | 0.99284 | 0.909 | egyezik | dokumentált |
| `lanc-0051` | `k01.jpg` | `filters=FocalZoom=1,0.077289,0.421118,21.400003,70.874339,89.812199,84.420614;<br>QuantizePalette=1,23.205642,34.650819,81.322322;<br>` | 0.99465 | 1.113 | egyezik | egyezik |
| `lanc-0052` | `k02.jpg` | `filters=Sixties=1,47.629366,00af6e4b,0;<br>dir_sharp=1,0.223114,0.104421;<br>autobacklight=1;<br>radsat=1,0.270388,0.689820,0.754140,0.978410;<br>` | 0.9997 | 0.171 | egyezik | egyezik |
| `lanc-0053` | `k03.jpg` | `filters=autolight=1;<br>linblur=1,0.358548,0.277092,0.447239;<br>autocontrast=1;<br>tint=1,94.721920,ff795b46;<br>blur=1,-0.136316;<br>LocalContrast=1,15.310596,1.454819;<br>` | 0.99057 | 0.938 | egyezik | egyezik |
| `lanc-0054` | `k04.jpg` | `filters=sepia=1;<br>TwoTone=1,15.050712,32.066127,84.788489,006afc1e,00456e88;<br>enhance=1;<br>shadow=1,0.453241,0.986129,0.182770;<br>` | 0.9965 | 0.816 | egyezik | egyezik |
| `lanc-0055` | `k05.jpg` | `filters=unsharp=1,0.180873;<br>grain2=1;<br>` | 1.0 | 0.0 | egyezik | véletlenállapot-függő |
| `lanc-0056` | `k06.jpg` | `filters=radsat=1,0.004965,0.169563,0.343860,0.101761;<br>Holga=1,71.579133,3.799396,9.551394;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0057` | `k07.jpg` | `filters=radsat=1,0.735464,0.738734,-0.211450,0.598905;<br>Invert=1;<br>grain=1;<br>blur=1,-0.117007;<br>` | 0.95089 | 1.303 | eltér | véletlenállapot-függő |
| `lanc-0058` | `k08.jpg` | `filters=HeatMap=1,-95.454065,74.387229;<br>Vignette=1,39.684043,1.780374,90.916046,006abb0d;<br>MuseumMatte=1,58.978275,95.555406,00d3a0e3,00a15a95;<br>colorfix=1,0.026159,ff2e73ac;<br>linblur=1,0.420774,0.449352,2.322630;<br>triple3=1,0.218011,0.013600,0.340147;<br>` | 0.99586 | 0.522 | egyezik | véletlenállapot-függő |
| `lanc-0059` | `k09.jpg` | `filters=LocalContrast=1,29.624208,1.730939;<br>Orton=1,28.391390,41.995517,4.608204;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0060` | `k10.jpg` | `filters=Comicize=1,57.309708,96.025824,48.305213;<br>PicnikTint=1,76.715298,005794c3;<br>` | 0.99555 | 0.169 | egyezik | egyezik |
| `lanc-0061` | `k01.jpg` | `filters=sepia=1;<br>gamma=1,0.485504;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0062` | `k02.jpg` | `filters=warm=1;<br>MuseumMatte=1,94.004278,16.909435,004b3f61,00c58cd4;<br>` | 0.99999 | 0.0 | egyezik | egyezik |
| `lanc-0063` | `k03.jpg` | `filters=dir_sharp=1,0.341694,-0.901783;<br>dir_sat=1,0.431447,0.554167;<br>tint=1,39.381757,ffe4d8c1;<br>HDR=1,42.615138,2.077074,73.749620;<br>dir_tint=1,0.604912,0.439915,0.322617,0.962073,fffa139a;<br>glow2=1,0.628683,25.945404;<br>` | 0.99927 | 0.171 | egyezik | egyezik |
| `lanc-0064` | `k04.jpg` | `filters=dir_tint=1,0.266459,0.602924,0.220792,0.227975,ff54e088;<br>autocolor=1;<br>whitept=1,ffce54e4;<br>Vignette=1,22.773701,1.003194,93.882663,0038b25d;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0065` | `k05.jpg` | `filters=radblur=1,0.634522,0.530281,0.001572,-0.340606;<br>RoundedEdges=1,12.430211,00cac3a8;<br>` | 0.99802 | 0.137 | egyezik | egyezik |
| `lanc-0066` | `k06.jpg` | `filters=autocolor=1;<br>PicnikTint=1,90.707356,005af3cd;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0067` | `k07.jpg` | `filters=autocolor=1;<br>blur=1,0.092719;<br>autolight=1;<br>LocalContrast=1,2.314701,1.711496;<br>` | 0.99211 | 1.244 | egyezik | egyezik |
| `lanc-0068` | `k08.jpg` | `filters=radsat=1,0.147149,0.682910,-0.962590,0.056384;<br>triple3=1,0.308177,0.076961,0.447830;<br>` | 0.99563 | 0.448 | egyezik | véletlenállapot-függő |
| `lanc-0069` | `k09.jpg` | `filters=grain=1;<br>colorfix=1,-0.204620,ff61dfd9;<br>` | 1.0 | 0.0 | egyezik | véletlenállapot-függő |
| `lanc-0070` | `k10.jpg` | `filters=Matte=1,43.036882,1.409950,22.784051,00abc070;<br>HDR=1,25.435701,3.109675,49.457830;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0071` | `k01.jpg` | `filters=triple2=1,0.751494,0.633503,0.072571;<br>Pixelate=1,36.373476,5.100198,34.634811;<br>MuseumMatte=1,40.500032,45.036044,009c1cdd,0017956c;<br>whitept=1,ffb32a58;<br>LocalContrast=1,17.626335,1.712306;<br>` | 0.98717 | 1.099 | egyezik | dokumentált |
| `lanc-0072` | `k02.jpg` | `filters=Neon=1,27.888531,00f44a8c;<br>sepia=1;<br>radtint=1,0.495077,0.070368,0.194451,ffc2efa6;<br>tint=1,25.784540,fff21c55;<br>autobacklight=1;<br>` | 0.99153 | 1.004 | egyezik | egyezik |
| `lanc-0073` | `k03.jpg` | `filters=grain2=1;<br>dir_tint=1,0.451068,0.994271,0.661627,0.652435,ff24555b;<br>radblur=1,0.452994,0.534516,0.215277,-0.576678;<br>contrast=1,0.021479;<br>dir_tint=1,0.002464,0.051349,0.698818,0.253998,ff1001db;<br>` | 0.99582 | 0.127 | egyezik | véletlenállapot-függő |
| `lanc-0074` | `k04.jpg` | `filters=PicnikTint=1,92.856441,00fe1261;<br>HDR=1,61.209235,1.203615,41.429394;<br>PencilSketch=1,2.710372,83.968245,97.670746;<br>Neon=1,71.771591,003c92ae;<br>Matte=1,35.866303,1.740946,8.910922,002ec6ad;<br>autocontrast=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0075` | `k05.jpg` | `filters=Border=1,0.244813,83.007688,70.532595,009bd318,0022d675,43.354191;<br>triple3=1,0.937262,0.170279,0.347552;<br>PicnikGrain=1,42.220420,1;<br>Matte=1,28.923819,1.628437,37.186762,007df9cc;<br>` | 0.98953 | 0.877 | egyezik | véletlenállapot-függő |
| `lanc-0076` | `k06.jpg` | `filters=colortemp=1,-0.114578,0.389401;<br>autolight=1;<br>triple3=1,0.536479,0.140103,0.412692;<br>RoundedEdges=1,33.937980,00162477;<br>radsat=1,0.190647,0.088770,0.394116,0.337420;<br>Boost=1,62.006413;<br>` | 0.98158 | 0.547 | egyezik | véletlenállapot-függő |
| `lanc-0077` | `k07.jpg` | `filters=grain=1;<br>unsharp2=1,1.895622;<br>dir_tint=1,0.249216,0.054589,0.790091,0.085632,ff1124d7;<br>radblur=1,0.274454,0.678176,-0.667834,0.232408;<br>autolight=1;<br>` | 0.98355 | 0.795 | egyezik | véletlenállapot-függő |
| `lanc-0078` | `k08.jpg` | `filters=TwoTone=1,52.336282,63.980415,41.369130,0042a855,001c22d2;<br>Sixties=1,67.185764,003bafba,1;<br>dir_sat=1,0.264882,0.709889;<br>radsat=1,0.936997,0.292826,0.614907,0.871632;<br>autobacklight=1;<br>glow2=1,0.973086,9.494977;<br>` | 0.99849 | 0.08 | egyezik | egyezik |
| `lanc-0079` | `k09.jpg` | `filters=dir_sat=1,0.121218,0.449628;<br>gamma=1,-0.568502;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0080` | `k10.jpg` | `filters=unsharp2=1,2.116445;<br>backlight=1,0.546945;<br>Pixelate=1,34.418023,3.546385,70.464209;<br>triple3=1,0.699664,0.454836,0.128945;<br>` | 0.99928 | 0.481 | egyezik | véletlenállapot-függő |
| `lanc-0081` | `k01.jpg` | `filters=Holga=1,49.729156,74.628857,9.940621;<br>ansel=1,ff510944;<br>Vignette=1,4.836830,1.181470,63.806994,005ef84f;<br>FocalZoom=1,0.236839,0.265735,3.302379,98.080891,56.864523,32.227949;<br>` | 0.9918 | 0.528 | egyezik | egyezik |
| `lanc-0082` | `k02.jpg` | `filters=LocalContrast=1,27.841660,2.256558;<br>triple=1,-0.836161,0.403197,0.707818;<br>HeatMap=1,-16.878155,94.554776;<br>` | 0.9963 | 0.869 | egyezik | egyezik |
| `lanc-0083` | `k03.jpg` | `filters=PicnikFocalPixelate=1,0.117342,0.847775,50.862020,47.419030,0.972985,12.611679,1;<br>blur=1,0.008589;<br>Polaroid=1,9.476483,008d677b;<br>` | 0.99815 | 0.094 | egyezik | egyezik |
| `lanc-0084` | `k04.jpg` | `filters=PicnikTint=1,57.590501,000b1c41;<br>colortemp=1,-0.134458,0.098014;<br>glow=1,0.217580,61.862442;<br>` | 0.99993 | 0.041 | egyezik | egyezik |
| `lanc-0085` | `k05.jpg` | `filters=autolight=1;<br>grain=1;<br>Orton=1,47.026292,91.586354,32.138141;<br>Lomo=1,42.752624,35.285741;<br>` | 1.0 | 0.0 | egyezik | véletlenállapot-függő |
| `lanc-0086` | `k06.jpg` | `filters=radtint=1,0.820725,0.198905,0.465700,ffa3bf10;<br>colorfix=1,0.484123,ff588399;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0087` | `k07.jpg` | `filters=backlight=1,0.190072;<br>HeatMap=1,60.359788,50.780396;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0088` | `k08.jpg` | `filters=blur=1,0.211686;<br>NightVision=1,34.476475,-30.583760,54.241052;<br>MuseumMatte=1,59.336619,79.627640,0015817e,00cd42ac;<br>FocalZoom=1,0.462048,0.735506,55.764868,66.501548,72.409227,92.861890;<br>` | 0.9958 | 0.686 | egyezik | egyezik |
| `lanc-0089` | `k09.jpg` | `filters=radblur=1,0.192093,0.721804,0.816671,0.644799;<br>triple=1,-0.432082,0.274334,0.927490;<br>unsharp=1,0.651966;<br>triple3=1,0.428081,0.444463,0.273824;<br>Neon=1,85.170523,00d548c2;<br>` | 0.98381 | 1.482 | egyezik | véletlenállapot-függő |
| `lanc-0090` | `k10.jpg` | `filters=RoundedEdges=1,16.825869,00350c47;<br>blur=1,0.414862;<br>Soften=1,14.538445,22.413000;<br>DropShadow=1,20.732581,100.901328,20.126229,00d42b63,0015b4f7,72.080971;<br>Soften=1,92.181292,24.029232;<br>PencilSketch=1,2.254321,0.014576,38.300863;<br>` | 0.99877 | 0.024 | egyezik | egyezik |
| `lanc-0091` | `k01.jpg` | `filters=PicnikTint=1,89.782854,0030eae3;<br>backlight=1,0.893395;<br>PicnikTint=1,12.522028,00219eb9;<br>LocalContrast=1,2.363508,2.919084;<br>QuantizePalette=1,10.161109,83.153363,12.622502;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0092` | `k02.jpg` | `filters=FocalZoom=1,0.200816,0.335034,57.693561,72.470265,45.311039,46.400651;<br>Holga=1,22.614409,4.438738,43.835078;<br>bw=1;<br>Vignette=1,20.932422,1.309737,44.312252,007ad4f0;<br>triple2=1,0.715390,0.972654,0.166040;<br>Sixties=1,1.063431,00b4487b,0;<br>` | 0.67054 | 1.251 | eltér | dokumentált |
| `lanc-0093` | `k03.jpg` | `filters=dir_sat=1,0.500580,-0.069807;<br>Border=1,77.368990,93.365340,3.111345,002df253,0028264e,33.006449;<br>colorfix=1,-0.277594,ff2a9b42;<br>ansel=1,ff5af404;<br>whitept=1,ff99b26c;<br>triple=1,-0.795455,-0.431099,0.589727;<br>` | 0.99722 | 0.124 | egyezik | egyezik |
| `lanc-0094` | `k04.jpg` | `filters=blur=1,0.348537;<br>autocolor=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0095` | `k05.jpg` | `filters=triple2=1,0.977394,0.985204,0.913084;<br>radtint=1,0.101773,0.070526,0.159662,ff985046;<br>enhance=1;<br>radtint=1,0.322443,0.591657,0.722392,ff2f0b88;<br>autocontrast=1;<br>whitept=1,ff323d79;<br>` | 0.99434 | 0.355 | egyezik | dokumentált |
| `lanc-0096` | `k06.jpg` | `filters=HDR=1,47.530953,2.643169,27.983436;<br>IR=1,33.913880;<br>` | 0.9951 | 0.408 | egyezik | egyezik |
| `lanc-0097` | `k07.jpg` | `filters=autolight=1;<br>dir_sat=1,-0.442611,0.858774;<br>ansel=1,ff892ecc;<br>autobacklight=1;<br>PicnikGrain=1,3.811999,1;<br>` | 0.99649 | 0.226 | egyezik | egyezik |
| `lanc-0098` | `k08.jpg` | `filters=Sixties=1,86.284666,008b2e52,0;<br>dir_brite=1,0.080014,0.714708;<br>shadow=1,0.820737,0.553513,0.813182;<br>` | 0.99966 | 0.175 | egyezik | egyezik |
| `lanc-0099` | `k09.jpg` | `filters=triple=1,0.402226,-0.108694,0.395994;<br>Matte=1,17.903133,1.000207,10.562091,00bd4991;<br>` | 0.99668 | 0.559 | egyezik | egyezik |
| `lanc-0100` | `k10.jpg` | `filters=ansel=1,ff2d647f;<br>dir_brite=1,-0.362811,0.034694;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0101` | `k01.jpg` | `filters=rainbow=1,102.829573;<br>PicnikTint=1,91.940153,00d5aa08;<br>PicnikGrain=1,47.719807,0;<br>PicnikTint=1,44.575169,002a06ca;<br>Neon=1,61.016254,0029d5d8;<br>` | 0.98245 | 1.616 | egyezik | egyezik |
| `lanc-0102` | `k02.jpg` | `filters=Comicize=1,53.002734,19.463167,67.017613;<br>glow2=1,0.137947,88.803976;<br>` | 0.99525 | 0.247 | egyezik | egyezik |
| `lanc-0103` | `k03.jpg` | `filters=glow2=1,0.477382,97.296613;<br>dir_sharp=1,0.005954,-0.648156;<br>NightVision=1,26.758011,-26.609838,78.016563;<br>HDR=1,12.004037,1.518650,13.483688;<br>Orton=1,8.609542,27.595026,32.963553;<br>glow2=1,0.405521,46.738079;<br>` | 0.9984 | 0.217 | egyezik | egyezik |
| `lanc-0104` | `k04.jpg` | `filters=linblur=1,0.002077,0.426368,5.022735;<br>radblur=1,0.283328,0.537484,0.165870,-0.388287;<br>TwoTone=1,-16.371435,44.041512,20.212408,00dfb23c,00a494e5;<br>PicnikTint=1,41.678529,0075fca0;<br>` | 0.99975 | 0.029 | egyezik | egyezik |
| `lanc-0105` | `k05.jpg` | `filters=Lomo=1,62.193788,23.078117;<br>colortemp=1,0.184312,0.479961;<br>grain=1;<br>` | 1.0 | 0.0 | egyezik | véletlenállapot-függő |
| `lanc-0106` | `k06.jpg` | `filters=QuantizePalette=1,21.821944,28.031246,22.214528;<br>sepia=1;<br>Comicize=1,76.856965,18.514897,94.632968;<br>colorfix=1,-0.170145,ff75764a;<br>glow=1,0.350047,35.483288;<br>` | 0.99944 | 0.039 | egyezik | egyezik |
| `lanc-0107` | `k07.jpg` | `filters=PencilSketch=1,2.890384,125.895417,17.502960;<br>autocolor=1;<br>autobacklight=1;<br>grain=1;<br>` | 0.93369 | 1.689 | eltér | véletlenállapot-függő |
| `lanc-0108` | `k08.jpg` | `filters=Comicize=1,48.979264,62.410183,54.225728;<br>whitept=1,ff55560e;<br>PencilSketch=1,3.662248,197.952245,17.124480;<br>CrossProcess=1,24.445353;<br>grain2=1;<br>PencilSketch=1,4.778448,130.637178,96.252777;<br>` | 0.97247 | 2.413 | eltér | véletlenállapot-függő |
| `lanc-0109` | `k09.jpg` | `filters=backlight=1,0.537520;<br>Lomo=1,87.327042,48.125560;<br>autocontrast=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0110` | `k10.jpg` | `filters=Holga=1,63.217569,68.383497,82.119395;<br>whitept=1,ff4fd433;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0111` | `k01.jpg` | `filters=autobacklight=1;<br>sat=1,0.378336;<br>backlight=1,0.771463;<br>radtint=1,0.337150,0.694252,0.979118,ffc68897;<br>linblur=1,0.353643,0.454785,9.497090;<br>Pixelate=1,103.026267,2.269109,52.057766;<br>` | 0.99963 | 0.046 | egyezik | egyezik |
| `lanc-0112` | `k02.jpg` | `filters=unsharp=1,0.574220;<br>blur=1,0.467323;<br>Invert=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0113` | `k03.jpg` | `filters=HeatMap=1,-167.564551,4.583239;<br>grain=1;<br>radblur=1,0.225255,0.279990,0.557131,0.912554;<br>FocalZoom=1,0.753570,0.152405,92.256554,45.434352,28.965832,33.037030;<br>radblur=1,0.499015,0.976279,0.933596,-0.547261;<br>LocalContrast=1,34.137018,2.444671;<br>` | 0.99048 | 0.828 | egyezik | véletlenállapot-függő |
| `lanc-0114` | `k04.jpg` | `filters=triple2=1,0.673702,0.380546,0.736546;<br>Polaroid=1,6.565031,007de8a1;<br>colortemp=1,-0.236509,0.555121;<br>HeatMap=1,-154.949494,63.990709;<br>` | 0.99509 | 0.477 | egyezik | dokumentált |
| `lanc-0115` | `k05.jpg` | `filters=Border=1,83.107871,34.041940,75.831317,0054a025,00472735,2.793135;<br>Neon=1,35.967674,0064382b;<br>NightVision=1,48.530631,-29.153966,52.208983;<br>grain=1;<br>RoundedEdges=1,23.786901,0061d484;<br>` | 0.80781 | 3.083 | eltér | véletlenállapot-függő |
| `lanc-0116` | `k06.jpg` | `filters=contrast=1,-0.026145;<br>sepia=1;<br>dir_tint=1,0.181573,0.759010,0.805303,0.978608,ff83ba8b;<br>` | 0.9964 | 0.226 | egyezik | egyezik |
| `lanc-0117` | `k07.jpg` | `filters=Border=1,18.820280,92.540396,14.043837,00793153,00b860c6,6.857768;<br>autolight=1;<br>glow=1,0.652167,58.162093;<br>grain2=1;<br>glow2=1,0.870641,87.844489;<br>` | 0.87352 | 1.61 | eltér | véletlenállapot-függő |
| `lanc-0118` | `k08.jpg` | `filters=PicnikFocalPixelate=1,0.570139,0.303871,65.502747,29.889485,79.851686,58.485355,1;<br>Sixties=1,58.149782,004e2418,0;<br>Sixties=1,95.533591,0008562f,1;<br>IR=1,2.477761;<br>triple2=1,0.593991,0.345194,0.865557;<br>Comicize=1,19.880555,25.176466,12.686009;<br>` | 0.98837 | 0.818 | egyezik | dokumentált |
| `lanc-0119` | `k09.jpg` | `filters=autolight=1;<br>HDR=1,38.039515,1.007130,56.674364;<br>ansel=1,ff37cf67;<br>glow=1,0.847481,97.348443;<br>FocalZoom=1,0.988473,0.945075,43.150981,60.061246,78.799623,82.578574;<br>` | 0.99654 | 0.501 | egyezik | egyezik |
| `lanc-0120` | `k10.jpg` | `filters=blur=1,0.089756;<br>NightVision=1,35.193892,-26.692907,88.652686;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0121` | `k01.jpg` | `filters=tint=1,107.468750,fffc2e33;<br>Sixties=1,12.042187,001aed2c,1;<br>bw=1;<br>` | 0.99922 | 0.009 | egyezik | egyezik |
| `lanc-0122` | `k02.jpg` | `filters=bw=1;<br>tint=1,167.996045,ff499670;<br>` | 0.99779 | 0.987 | egyezik | egyezik |
| `lanc-0123` | `k03.jpg` | `filters=Soften=1,22.524007,67.787358;<br>warm=1;<br>DropShadow=1,2.884807,99.386845,55.365584,00cf4b7a,00380d5a,78.241227;<br>enhance=1;<br>grain=1;<br>` | 1.0 | 0.0 | egyezik | véletlenállapot-függő |
| `lanc-0124` | `k04.jpg` | `filters=TwoTone=1,22.078217,24.936855,48.318500,009335c6,00679967;<br>tint=1,126.261061,ff5bcce8;<br>Holga=1,77.842933,24.427262,65.935104;<br>HeatMap=1,134.614065,69.984497;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0125` | `k05.jpg` | `filters=enhance=1;<br>whitept=1,ff617e3b;<br>shadow=1,0.643246,0.975699,0.826039;<br>` | 0.99977 | 0.295 | egyezik | egyezik |
| `lanc-0126` | `k06.jpg` | `filters=LocalContrast=1,10.503457,1.502163;<br>enhance=1;<br>colortemp=1,0.395659,0.038673;<br>glow=1,0.303107,88.592376;<br>rainbow=1,129.429968;<br>` | 0.9949 | 0.899 | egyezik | egyezik |
| `lanc-0127` | `k07.jpg` | `filters=PencilSketch=1,3.350568,18.469305,97.845413;<br>PicnikFocalPixelate=1,0.882145,0.030518,28.120586,25.410542,56.039169,76.738879,0;<br>` | 0.99999 | 0.0 | egyezik | egyezik |
| `lanc-0128` | `k08.jpg` | `filters=autobacklight=1;<br>triple=1,0.427837,0.491590,0.157399;<br>sepia=1;<br>Vignette=1,0.286008,1.942848,26.393628,009c6cd8;<br>Border=1,26.917185,14.040804,28.637248,00154a51,008b6493,50.441477;<br>Orton=1,38.801713,38.368173,65.842503;<br>` | 0.99714 | 0.579 | egyezik | egyezik |
| `lanc-0129` | `k09.jpg` | `filters=dir_tint=1,0.597502,0.956281,0.486391,0.091361,ff684eac;<br>tint=1,47.017510,ff0c5ac7;<br>Polaroid=1,4.579077,00f3abba;<br>` | 0.99997 | 0.006 | egyezik | egyezik |
| `lanc-0130` | `k10.jpg` | `filters=unsharp=1,0.107505;<br>LocalContrast=1,2.681458,1.449198;<br>Pixelate=1,148.359007,8.309297,48.148066;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0131` | `k01.jpg` | `filters=CrossProcess=1,80.466223;<br>enhance=1;<br>HDR=1,15.432845,3.257561,8.625912;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0132` | `k02.jpg` | `filters=glow=1,0.426473,53.473941;<br>grain2=1;<br>whitept=1,ffd43637;<br>CrossProcess=1,30.213442;<br>Lomo=1,45.937788,59.838698;<br>dir_sharp=1,0.060732,0.749168;<br>` | 0.99785 | 0.372 | egyezik | véletlenállapot-függő |
| `lanc-0133` | `k03.jpg` | `filters=DropShadow=1,29.387149,243.368529,73.752287,00882368,00d5530a,96.568129;<br>autocolor=1;<br>grain=1;<br>autolight=1;<br>Vignette=1,20.123096,1.797758,59.605003,0038d1a9;<br>PencilSketch=1,4.679736,83.857915,57.157334;<br>` | 0.47741 | 4.003 | eltér | véletlenállapot-függő |
| `lanc-0134` | `k04.jpg` | `filters=linblur=1,0.227748,0.768455,7.745909;<br>radtint=1,0.056810,0.351219,0.972598,ff850fff;<br>colorfix=1,-0.464902,ffa2f6da;<br>autocolor=1;<br>` | 0.99968 | 0.056 | egyezik | egyezik |
| `lanc-0135` | `k05.jpg` | `filters=tint=1,34.613092,ff0838eb;<br>Pixelate=1,127.374144,0.940867,33.061301;<br>Polaroid=1,-2.368757,003e56b9;<br>` | 0.99504 | 0.441 | egyezik | egyezik |
| `lanc-0136` | `k06.jpg` | `filters=rainbow=1,16.638687;<br>Polaroid=1,9.963217,00f33461;<br>PicnikTint=1,63.092020,00b6453d;<br>Lomo=1,96.291715,77.119015;<br>` | 0.99699 | 0.384 | egyezik | egyezik |
| `lanc-0137` | `k07.jpg` | `filters=autobacklight=1;<br>autolight=1;<br>ansel=1,ff9c6687;<br>colorfix=1,-0.122915,ff57bb0f;<br>gamma=1,0.509083;<br>` | 0.99399 | 0.583 | egyezik | egyezik |
| `lanc-0138` | `k08.jpg` | `filters=unsharp2=1,1.604803;<br>IR=1,10.078440;<br>Sixties=1,43.834782,00a9f026,1;<br>` | 0.99668 | 0.734 | egyezik | egyezik |
| `lanc-0139` | `k09.jpg` | `filters=NightVision=1,38.498292,-47.881696,14.296349;<br>grain2=1;<br>PicnikTint=1,36.274887,0050b2e0;<br>Comicize=1,74.597173,90.480256,46.141521;<br>dir_brite=1,-0.033864,-0.179948;<br>shadow=1,0.427676,0.777232,0.498716;<br>` | 0.8733 | 1.817 | eltér | véletlenállapot-függő |
| `lanc-0140` | `k10.jpg` | `filters=gamma=1,-0.226360;<br>HDR=1,67.022746,1.880201,35.314422;<br>autocolor=1;<br>whitept=1,ffea7fa9;<br>dir_sat=1,-0.482389,-0.602165;<br>PicnikFocalPixelate=1,0.370734,0.929889,16.009128,44.560560,53.088054,66.479213,0;<br>` | 0.9957 | 1.163 | egyezik | egyezik |
| `lanc-0141` | `k01.jpg` | `filters=autocontrast=1;<br>Polaroid=1,-9.417467,003329a5;<br>triple2=1,0.180398,0.399518,0.209985;<br>IR=1,18.743152;<br>` | 0.99639 | 0.17 | egyezik | dokumentált |
| `lanc-0142` | `k02.jpg` | `filters=Lomo=1,19.084741,18.082591;<br>Polaroid=1,9.358237,006eb0f4;<br>whitept=1,ff6b34cf;<br>dir_brite=1,-0.447979,0.868494;<br>HDR=1,15.858350,5.975047,8.604460;<br>Border=1,27.569301,55.975825,25.152724,00dd43e0,002354d1,88.543545;<br>` | 0.99892 | 0.103 | egyezik | egyezik |
| `lanc-0143` | `k03.jpg` | `filters=triple3=1,0.829784,0.193065,0.096314;<br>QuantizePalette=1,6.379768,55.020738,96.927215;<br>dir_tint=1,0.040732,0.616582,0.725131,0.870289,ff248134;<br>Border=1,81.737421,7.989234,87.881972,00a9cb1b,00cd4cd6,98.086045;<br>` | 0.99638 | 0.406 | egyezik | véletlenállapot-függő |
| `lanc-0144` | `k04.jpg` | `filters=triple2=1,0.294475,0.929007,0.810569;<br>TwoTone=1,-82.244496,26.832091,26.279816,00c4fc4a,00bb5b4f;<br>` | 0.99044 | 0.31 | egyezik | dokumentált |
| `lanc-0145` | `k05.jpg` | `filters=unsharp2=1,1.316192;<br>contrast=1,-0.034145;<br>PicnikFocalPixelate=1,0.403176,0.093445,56.307747,88.066085,66.720871,49.095551,0;<br>radsat=1,0.492366,0.242841,-0.431101,0.965719;<br>LocalContrast=1,16.778629,2.252890;<br>` | 0.99493 | 0.694 | egyezik | egyezik |
| `lanc-0146` | `k06.jpg` | `filters=triple=1,-0.083917,-0.424422,0.426464;<br>Matte=1,38.279647,1.899157,11.007161,00efb0ec;<br>Vignette=1,25.939828,1.344267,98.401145,00c8728e;<br>` | 0.99689 | 0.237 | egyezik | egyezik |
| `lanc-0147` | `k07.jpg` | `filters=RoundedEdges=1,9.346326,0094d76b;<br>triple=1,0.395350,0.109854,0.759835;<br>linblur=1,0.202295,0.198064,0.541507;<br>triple=1,0.725546,-0.255809,0.250268;<br>` | 0.99596 | 0.229 | egyezik | egyezik |
| `lanc-0148` | `k08.jpg` | `filters=Boost=1,17.623024;<br>sat=1,0.508971;<br>rainbow=1,7.018529;<br>PicnikGrain=1,48.007983,0;<br>enhance=1;<br>Pixelate=1,91.041898,4.304207,49.760979;<br>` | 0.98979 | 1.391 | egyezik | egyezik |
| `lanc-0149` | `k09.jpg` | `filters=radtint=1,0.649217,0.526600,0.676260,ff145904;<br>Matte=1,6.771324,1.606128,97.093794,00759fad;<br>grain=1;<br>Boost=1,55.422704;<br>autocolor=1;<br>CrossProcess=1,69.372257;<br>` | 1.0 | 0.0 | egyezik | véletlenállapot-függő |
| `lanc-0150` | `k10.jpg` | `filters=autolight=1;<br>radsat=1,0.681361,0.042875,0.944229,0.554756;<br>HDR=1,5.781388,2.261596,44.413159;<br>dir_brite=1,-0.483416,-0.551794;<br>` | 0.99356 | 0.718 | egyezik | egyezik |
| `lanc-0151` | `k01.jpg` | `filters=grain2=1;<br>grain=1;<br>` | 1.0 | 0.0 | egyezik | véletlenállapot-függő |
| `lanc-0152` | `k02.jpg` | `filters=unsharp2=1,1.853794;<br>Holga=1,26.618282,92.640758,46.107641;<br>colortemp=1,0.494007,0.938106;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0153` | `k03.jpg` | `filters=radblur=1,0.494008,0.082974,-0.888442,0.034542;<br>FocalZoom=1,0.750122,0.104745,18.441160,28.199444,34.428294,55.597503;<br>` | 0.9986 | 0.487 | egyezik | egyezik |
| `lanc-0154` | `k04.jpg` | `filters=HeatMap=1,-109.085653,45.020651;<br>TwoTone=1,-45.681064,86.415392,65.220250,00d158c0,00931d9e;<br>Pixelate=1,53.379350,3.550046,63.697880;<br>PencilSketch=1,3.916828,109.742377,26.946581;<br>MuseumMatte=1,23.843484,31.047840,002a815d,00901989;<br>` | 0.99999 | 0.0 | egyezik | egyezik |
| `lanc-0155` | `k05.jpg` | `filters=rainbow=1,242.549949;<br>Pixelate=1,71.288839,8.522303,16.807013;<br>Lomo=1,48.774592,56.118331;<br>dir_sat=1,0.989128,-0.715107;<br>triple3=1,0.265162,0.234791,0.142612;<br>` | 0.99442 | 0.814 | egyezik | véletlenállapot-függő |
| `lanc-0156` | `k06.jpg` | `filters=backlight=1,0.630098;<br>RoundedEdges=1,64.152718,00e5c7a7;<br>dir_sharp=1,-0.120370,-0.198385;<br>CrossProcess=1,53.551600;<br>` | 0.99968 | 0.109 | egyezik | egyezik |
| `lanc-0157` | `k07.jpg` | `filters=radblur=1,0.348826,0.679802,0.895369,0.555718;<br>glow2=1,0.947960,19.673239;<br>unsharp2=1,1.717967;<br>Sixties=1,30.803468,00e1f035,1;<br>` | 0.99537 | 0.369 | egyezik | egyezik |
| `lanc-0158` | `k08.jpg` | `filters=glow=1,0.588447,34.675659;<br>autocolor=1;<br>dir_brite=1,0.049276,0.120488;<br>PicnikGrain=1,33.385588,1;<br>grain2=1;<br>` | 0.97554 | 0.352 | eltér | véletlenállapot-függő |
| `lanc-0159` | `k09.jpg` | `filters=warm=1;<br>autolight=1;<br>unsharp=1,0.881298;<br>Matte=1,38.688205,1.172672,48.750540,002f3384;<br>linblur=1,0.869924,0.933092,4.372152;<br>tint=1,203.648290,ffb95935;<br>` | 0.9926 | 1.094 | egyezik | egyezik |
| `lanc-0160` | `k10.jpg` | `filters=DropShadow=1,10.175169,303.774441,77.350138,00a08928,0096c3aa,83.921586;<br>linblur=1,0.038453,0.177768,0.590216;<br>TwoTone=1,-14.149403,9.586968,66.875895,00ebd14d,0038d2d4;<br>Lomo=1,48.126143,75.240891;<br>Holga=1,66.945434,27.451267,58.996830;<br>HDR=1,16.539998,3.203571,2.958095;<br>` | 0.98976 | 0.481 | egyezik | egyezik |
| `lanc-0161` | `k01.jpg` | `filters=radblur=1,0.575918,0.999132,-0.250248,0.658479;<br>colortemp=1,0.144981,0.352283;<br>PicnikGrain=1,31.783788,1;<br>` | 0.99972 | 0.047 | egyezik | egyezik |
| `lanc-0162` | `k02.jpg` | `filters=colorfix=1,0.016340,ffeb3ada;<br>unsharp2=1,2.941654;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0163` | `k03.jpg` | `filters=gamma=1,0.213975;<br>CrossProcess=1,13.301430;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0164` | `k04.jpg` | `filters=Border=1,64.228463,32.477676,67.377246,006905cb,002a32b7,30.712981;<br>radblur=1,0.072132,0.799782,-0.004010,-0.619240;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0165` | `k05.jpg` | `filters=sat=1,-0.309262;<br>CrossProcess=1,46.893183;<br>radblur=1,0.392630,0.709184,0.627087,-0.568238;<br>TwoTone=1,-70.564806,73.569362,59.137118,0039c6b2,0029bcee;<br>grain2=1;<br>` | 0.99702 | 0.205 | egyezik | véletlenállapot-függő |
| `lanc-0166` | `k06.jpg` | `filters=radtint=1,0.169580,0.091019,0.243270,ffd8a699;<br>triple=1,-0.132755,0.319256,0.392346;<br>` | 0.99367 | 0.617 | egyezik | egyezik |
| `lanc-0167` | `k07.jpg` | `filters=gamma=1,-0.407891;<br>CrossProcess=1,7.189856;<br>backlight=1,0.968314;<br>Border=1,86.160347,62.126076,35.432989,00aca6a9,003d655e,28.766615;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0168` | `k08.jpg` | `filters=sepia=1;<br>autobacklight=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0169` | `k09.jpg` | `filters=FocalZoom=1,0.231292,0.030722,64.839026,20.876131,56.888839,65.970317;<br>warm=1;<br>PencilSketch=1,2.557226,123.521235,45.325735;<br>` | 0.98424 | 1.727 | egyezik | egyezik |
| `lanc-0170` | `k10.jpg` | `filters=PicnikTint=1,7.897839,00df41c3;<br>FocalZoom=1,0.678583,0.733869,4.884051,49.565772,85.367773,90.776949;<br>dir_tint=1,0.221620,0.113738,0.286956,0.467963,ff9a44c5;<br>` | 0.99753 | 0.786 | egyezik | egyezik |
| `lanc-0171` | `k01.jpg` | `filters=RoundedEdges=1,47.967665,00c1f78a;<br>shadow=1,0.237672,0.328389,0.429039;<br>Boost=1,3.368642;<br>` | 0.99838 | 0.166 | egyezik | egyezik |
| `lanc-0172` | `k02.jpg` | `filters=Invert=1;<br>CrossProcess=1,2.994937;<br>Polaroid=1,-5.573939,006afeac;<br>ansel=1,ff89dead;<br>grain=1;<br>Comicize=1,13.600407,90.921501,19.654694;<br>` | 0.99473 | 0.144 | egyezik | véletlenállapot-függő |
| `lanc-0173` | `k03.jpg` | `filters=autobacklight=1;<br>gamma=1,-0.742750;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0174` | `k04.jpg` | `filters=backlight=1,0.429840;<br>CrossProcess=1,95.430099;<br>warm=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0175` | `k05.jpg` | `filters=PencilSketch=1,3.865349,171.434389,83.760823;<br>backlight=1,0.526650;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0176` | `k06.jpg` | `filters=MuseumMatte=1,36.705002,95.295122,00409ab1,007ecb21;<br>contrast=1,0.373943;<br>Invert=1;<br>Pixelate=1,13.279354,0.908453,48.052519;<br>radsat=1,0.441543,0.616197,0.038360,0.392892;<br>` | 0.99402 | 0.293 | egyezik | egyezik |
| `lanc-0177` | `k07.jpg` | `filters=dir_brite=1,-0.213017,0.166480;<br>RoundedEdges=1,79.660556,00aa7143;<br>backlight=1,0.337020;<br>IR=1,45.875590;<br>gamma=1,0.283687;<br>` | 0.99338 | 0.367 | egyezik | egyezik |
| `lanc-0178` | `k08.jpg` | `filters=Soften=1,89.526244,32.706619;<br>NightVision=1,11.411457,-5.147594,44.475679;<br>autocontrast=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0179` | `k09.jpg` | `filters=unsharp=1,0.754556;<br>RoundedEdges=1,95.019111,0063f37f;<br>colorfix=1,0.133871,fff117ba;<br>HDR=1,20.873567,3.986179,96.210489;<br>HDR=1,15.025893,5.691053,83.790317;<br>CrossProcess=1,93.550100;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0180` | `k10.jpg` | `filters=Lomo=1,37.438993,65.504192;<br>Vignette=1,15.554688,1.312923,44.025296,00ecf6cd;<br>Pixelate=1,56.099545,2.548775,28.283579;<br>ansel=1,ffd61a77;<br>PicnikGrain=1,31.687466,0;<br>dir_sharp=1,-0.061106,0.362714;<br>` | 0.99942 | 0.051 | egyezik | egyezik |
| `lanc-0181` | `k01.jpg` | `filters=triple2=1,0.183129,0.390338,0.524030;<br>blur=1,0.041315;<br>autolight=1;<br>autolight=1;<br>Orton=1,4.199582,89.592253,45.045435;<br>` | 0.9973 | 0.759 | egyezik | dokumentált |
| `lanc-0182` | `k02.jpg` | `filters=Matte=1,29.856802,1.690616,6.903452,009d1f9e;<br>unsharp2=1,0.393750;<br>unsharp2=1,0.936083;<br>shadow=1,0.590633,0.870541,0.900120;<br>Boost=1,26.309041;<br>` | 0.99895 | 0.235 | egyezik | egyezik |
| `lanc-0183` | `k03.jpg` | `filters=RoundedEdges=1,50.666563,00502efb;<br>backlight=1,0.705493;<br>autolight=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0184` | `k04.jpg` | `filters=sepia=1;<br>warm=1;<br>QuantizePalette=1,14.308023,32.530711,53.769752;<br>colorfix=1,0.227874,ff77a429;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0185` | `k05.jpg` | `filters=PicnikFocalPixelate=1,0.726969,0.724564,73.617064,55.738357,52.776628,15.013006,1;<br>linblur=1,0.714371,0.611661,0.385216;<br>triple3=1,0.063782,0.342484,0.460105;<br>QuantizePalette=1,24.984700,8.861646,38.197561;<br>TwoTone=1,-92.688497,5.188784,84.017468,00fd5ad1,0095dd13;<br>` | 0.99103 | 0.654 | egyezik | véletlenállapot-függő |
| `lanc-0186` | `k06.jpg` | `filters=Lomo=1,8.801846,25.727846;<br>Matte=1,46.833914,1.263393,73.382507,0070b5f5;<br>Soften=1,85.834370,12.543771;<br>NightVision=1,37.303894,-26.143230,34.579635;<br>Pixelate=1,83.188482,8.849027,35.157954;<br>dir_brite=1,0.067795,0.870580;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0187` | `k07.jpg` | `filters=rainbow=1,217.763018;<br>Sixties=1,53.035377,0034f761,1;<br>autocolor=1;<br>sepia=1;<br>` | 0.98995 | 0.431 | egyezik | egyezik |
| `lanc-0188` | `k08.jpg` | `filters=enhance=1;<br>TwoTone=1,-86.216131,21.728519,91.882866,0071c867,003caf1e;<br>Sixties=1,59.383471,00d02dfa,0;<br>dir_brite=1,0.145394,-0.550836;<br>glow=1,0.730631,82.172197;<br>` | 0.99944 | 0.182 | egyezik | egyezik |
| `lanc-0189` | `k09.jpg` | `filters=PicnikFocalPixelate=1,0.318785,0.522958,30.270889,25.862045,59.858212,86.229073,0;<br>tint=1,137.018821,ffbc0e38;<br>radsat=1,0.214808,0.875271,0.708405,0.057078;<br>contrast=1,-0.063603;<br>` | 0.98316 | 0.742 | egyezik | egyezik |
| `lanc-0190` | `k10.jpg` | `filters=DropShadow=1,12.907294,77.553248,76.148281,00449bc7,0093f4c4,65.375914;<br>Lomo=1,27.749642,77.564432;<br>sat=1,-0.901066;<br>DropShadow=1,6.092959,108.091720,97.169899,003a68b5,00f3dc3a,18.820604;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0191` | `k01.jpg` | `filters=PicnikTint=1,88.738718,00a284b1;<br>HDR=1,77.510832,1.323908,92.450943;<br>Orton=1,29.151244,53.625934,94.944230;<br>Orton=1,42.491468,75.338435,33.705802;<br>enhance=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0192` | `k02.jpg` | `filters=blur=1,-0.211527;<br>dir_sharp=1,-0.195335,-0.142651;<br>contrast=1,-0.384842;<br>Vignette=1,6.376597,1.012258,66.881471,00bfa13c;<br>` | 0.99436 | 0.465 | egyezik | egyezik |
| `lanc-0193` | `k03.jpg` | `filters=Holga=1,12.460874,10.810442,19.431562;<br>Polaroid=1,-7.597223,00e82fa0;<br>HeatMap=1,26.599467,58.701132;<br>CrossProcess=1,97.050858;<br>` | 0.99999 | 0.002 | egyezik | egyezik |
| `lanc-0194` | `k04.jpg` | `filters=whitept=1,ffc283dc;<br>RoundedEdges=1,62.474178,00bf1f52;<br>bw=1;<br>` | 1.0 | 0.0 | egyezik | egyezik |
| `lanc-0195` | `k05.jpg` | `filters=gamma=1,-0.033228;<br>RoundedEdges=1,9.536488,004db832;<br>Polaroid=1,5.818960,0037a4cf;<br>` | 0.99995 | 0.01 | egyezik | egyezik |
| `lanc-0196` | `k06.jpg` | `filters=radtint=1,0.226147,0.991993,0.840316,ff0315bf;<br>glow=1,0.282406,77.572966;<br>PicnikGrain=1,5.192805,1;<br>triple=1,0.766429,-0.177472,0.655993;<br>` | 0.97879 | 0.762 | eltér | valódi eltérés |
| `lanc-0197` | `k07.jpg` | `filters=TwoTone=1,74.128258,44.423883,73.040359,00604867,0096174e;<br>grain2=1;<br>warm=1;<br>` | 1.0 | 0.0 | egyezik | véletlenállapot-függő |
| `lanc-0198` | `k08.jpg` | `filters=Lomo=1,80.453835,86.032911;<br>sepia=1;<br>enhance=1;<br>linblur=1,0.372141,0.139999,1.387239;<br>Vignette=1,7.254361,1.121988,43.171119,000462b3;<br>` | 0.99968 | 0.061 | egyezik | egyezik |
| `lanc-0199` | `k09.jpg` | `filters=blur=1,0.226091;<br>rainbow=1,131.865968;<br>triple3=1,0.924245,0.309268,0.398991;<br>` | 0.98592 | 1.55 | egyezik | véletlenállapot-függő |
| `lanc-0200` | `k10.jpg` | `filters=dir_tint=1,0.301511,0.002263,0.945116,0.752011,ff4c719f;<br>IR=1,2.809521;<br>Pixelate=1,134.953681,0.740484,36.911635;<br>CrossProcess=1,46.307995;<br>dir_brite=1,-0.794832,0.751788;<br>` | 0.99518 | 0.358 | egyezik | egyezik |
