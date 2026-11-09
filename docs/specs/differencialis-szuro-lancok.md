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
