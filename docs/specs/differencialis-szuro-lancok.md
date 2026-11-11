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
| `PicnikGrain` Noise | Külön verembeli objektum, a leíró szerinti `randomSeed=1`; nem a triple3 globális objektuma. | `bináris (0x00bce8f2, 0x00bce90e)`; `mérés (filterdesc.xml, PicnikGrain leíró)` |

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
semleges becslés keletkezik. A `0x0090fbcd–0x0090fbf4` a két súlypontot
−32 és 32 közé szorítja, majd a `0x0090fc61–0x0090fc85` a két kimeneti
értéket 0 és 255 közé korlátozza. A `0x0090fc99` írja a csomagolt becslést.
A PicasaPy `estimate_illuminant` ugyanezt a nulla-ágat és ezeket a korlátokat
használja. Ez a lelet nem bizonyítja, hogy a teljes kétprogramos út minden
részlete azonos.

**Független ellenőrzés:** a bináris `0x0090fbb3–0x0090fca4` utasításait
QEMU i386 alatt izolált állapottal futtatva a (súlyösszeg, x-nyomaték,
y-nyomaték) = (0, 0, 0) a `0x00808080`, az (1, 28, −28) a `0x00f08044`
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
osztás, a 64×64-es binelés, a köbös Chebyshev-súlyozás és a súlypont
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
