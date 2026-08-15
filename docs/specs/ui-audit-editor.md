# UI-audit — a Picasa 3.9 szerkesztőpanele és a kapcsolódó dialógusok (#315, #316, #318)

Forrás: a felhasználó **eredeti, magyar nyelvű Picasa 3.9**-ének
képernyőképei (`research/testdata/screenshot/` gyűjtemény újabb darabjai,
2026-07-18/19, gitignore-olt — személyes tartalom!). A jelen audithoz
felhasznált 9 kép közül ténylegesen **kettő** mutatja magát a
szerkesztőpanelt (`Képernyőkép 2026-07-18 195113.png`,
`…195123.png`, 351×515 ill. 308×421 képpont — kicsinyített ablak, nem 1:1
képernyőfelvétel), egy a hozzá tartozó **Egyéni méretarány hozzáadása**
mini-dialógust (`…195907.png`), a többi (Nézet-menü, PicasaPy saját
mappalista/névjegy nézetei, Mappakezelő dialógus, indexkép-rácsok) nem a
szerkesztőpanelről szól, vagy már a PicasaPy-t mutatja — ezeket csak a
teljesség kedvéért, röviden érintem a 7. szakaszban.

**Korlát, amit fontos előre leszögezni:** a két hasznos kép **kizárólag a
vágás-fület (1. fül, csavarkulcs) mutatja megnyitva**. A másik négy fül
(Finomhangolás, és a három ecset-fül) tartalmáról **nincs képi bizonyíték**
ebben a csomagban — az alábbi effekt-leltár a fülcímkék/ikonok
(képi tény) és a projekt már meglévő, korábbi képcsomagból származó
kutatási eredménye (`docs/specs/filters-decoded.md`, 5. kör, #190) alapján
áll össze. Ahol a forrás a mostani screenshot, ott ▶**KÉP**; ahol a korábbi
kutatás, ott ▶**KUTATÁS (#190)** jelzi.

> **KIEGÉSZÍTÉS (2026-08-15, a #700/#703/#704 előkészítése).** A fenti korlát
> **részben megszűnt.** A `research/testdata/screenshot/` gyűjtemény **korábbi,
> 2026-07-17-i sorozata** (35 db teljes képernyős, **1920×1080-as, 1:1
> nagyítású** felvétel — nem kicsinyített ablak!) **mind az öt fület megnyitva
> mutatja**, ezen belül a 2., 3., 4. és 5. fül teljes tartalmát:
>
> | Fájl | Mit mutat |
> |---|---|
> | `2026-07-17 20 56 36.png` | 1. fül — Gyakori javítások |
> | `2026-07-17 20 56 42.png` | 2. fül — Finomhangolás (4 csúszka + színpálca) |
> | `2026-07-17 20 56 45.png` | 3. fül — effekt-rács (12 csempe) |
> | `2026-07-17 20 56 50.png` | 4. fül — effekt-rács (12 csempe) |
> | `2026-07-17 20 56 55.png` | 5. fül — effekt-rács (12 csempe) |
>
> Mind az öt kép **ugyanazt a szerkesztetlen fotót** mutatja (a nagy előnézet
> átlagszíne mind az ötben azonos: RGB 75,4 / 84,8 / 71,7 a 700–900 × 400–500-as
> mintaterületen), tehát összehasonlíthatók. Az ezekből nyert új anyag a
> **3. és 4. szakaszban** van; az 5–8. szakasz az eredeti, 2026-07-18-i
> auditból származik, változatlanul.
>
> Ezen kívül két új, képtől független forrás nyílt meg azóta:
> ▶**ERŐFORRÁS** = a Picasa saját elrendezés-erőforrásai
> (`~/picasapy-agent/referencia/tre-eroforrasok/`, ld.
> `docs/specs/picasa-respack-format.md`) és ▶**BINÁRIS** = a bináris
> sztring-index (`~/picasapy-agent/referencia/binary-index/`, image base
> `0x00400000`).

## 1. A fülrendszer — megerősítve: **5 ikonos fül, nem 3**

▶**KÉP.** A panel tetején, a „Vissza a könyvtárhoz" gomb alatt egy 5 elemű,
egyenlő szélességű ikonsáv fut végig (a wrench balra igazítva, a többi
egyenlő osztásban jobbra):

| # | Ikon | Feltételezett fül-cím | Tartalom (ez a csomag / korábbi kutatás) |
|---|---|---|---|
| 1 | 🔧 csavarkulcs — **AKTÍV** a képeken | Alapvető javítások | Vágás (jelen doc 5. szakasza), Kiegyenesítés, Vörösszem, Jó napom van, Automatikus kontraszt/szín, Retusálás, Szöveg, gyors Derítőfény-csúszka (`docs/specs/design-guide.md` korábbi screenshot-mintáiból) |
| 2 | ☀️ nap/csillag | Finomhangolás (Tuning) | Derítőfény, Fények, Árnyékok, Színhőmérséklet, Semleges szín pipetta (`finetune2` 5 paramétere, `filters-decoded.md` 1. kör) — **a tartalom a 2026-07-17-i felvételen látszik**, ld. 4.2–4.5 |
| 3 | 🖌️ sima ecset (nincs alatta szín-minta) | Effektek | 12 törzs-effekt (2. szakasz táblázata + a 2026-08-15-i helyesbítés) |
| 4 | 🖌️ ecset **zöld tájkép-mintával** | 4. effekt-fül | 12 effekt — kulcsok `#190`-ből azonosítva (2. szakasz), a rács a `…20 56 50.png`-n látszik |
| 5 | 🖌️ ecset **kék ég-mintával** | 5. effekt-fül | 12 effekt (a `Vignette`-tel együtt) — kulcsok `#190`-ből azonosítva (2. szakasz), a rács a `…20 56 55.png`-n látszik |

Ez **megerősíti a kiinduló megfigyelést**: nem 3, hanem **5 fül** van, és a
2–3–4. fül valóban mind „ecset" ikonos — de nem azonosak: a 3. fül önálló
(sima) ecset, a 4. és 5. fülnek pedig a saját ikonjuk **be van színezve**
egy kis táj-/ég-mintával, feltehetően hogy vizuálisan is jelezze „ez már
kreatív/hangulati effekt-csomag, nem alap-effekt". A `docs/specs/
filters-decoded.md` 5. körének (#190) kutatása **már névvel és
`filters=` kulccsal azonosította** a 4. és 5. fül tartalmát — csak eddig
nem volt hozzá kötve a fülsorrendhez/ikonokhoz; ez az audit adja meg ezt a
hiányzó kapcsot.

**Jelenlegi PicasaPy-implementáció** (`EditorPanel.qml`, 244–299. sor):
**3 szöveges fül** — „Gyakori javítások" (`activeTab=0`), „Finomhangolás"
(`activeTab=1`), „Effektek" (`activeTab=2`). A 4–5. fül **teljesen
hiányzik** — nincs QML-komponens, nincs `activeTab` érték, nincs
fülgomb. Ez a gyökere a felhasználó „MINDEN EFFEKTET KÉREK" panaszának:
a Picasa 3.9-ben **36 effekt-gomb** van (3 effekt-fülön elosztva), a
PicasaPy-ban **13**.

## 2. Effekt-leltár

Az „eredeti Picasa effekt" oszlop magyar felirata a 3. fülnél a jelenlegi
PicasaPy angol forrásfeliratának magyar fordításából (`picasapy_hu.ts`)
származik (a valódi Picasa feliratát ezen a képcsomagon nem látjuk — a 3.
fül tartalma se látszik közvetlenül, csak a render-oldali `filters=` nevek
és a korábbi (screenshot nélküli) implementációs kör címkéi). A 4–5. fülnél
a magyar UI-név a `filters-decoded.md`-ből (#190, a felhasználó valódi
exportjaiból mért `filters=` kulcsok melletti UI-név) származik — **ez
képi/exportált bizonyítékkal alátámasztott**, csak a fül-hovatartozás
(4. vagy 5.) volt eddig nem összekötve a látott ikonokkal.

### 3. fül — Effektek (sima ecset) — törzs-effektek

| Magyar UI-felirat (PicasaPy) | `filters=` kulcs | UI-gomb van? | Render-implementáció van? | Csúszkával paraméterezhető? |
|---|---|---|---|---|
| Élesítés (Sharpen) | `unsharp`/`unsharp2` | ✅ | ✅ (Gauss unsharp, σ≈1,0) | ❌ egygombos, nincs erősség-csúszka |
| Szépia (Sepia) | `sepia` | ✅ | ✅ (mért 3-csatornás LUT) | ❌ |
| Fekete-fehér (B&W) | `bw` | ✅ | ✅ (pixelhű, Rec.601) | ❌ |
| Melegítés (Warmify) | `warm` | ✅ | ✅ (mért LUT) | ❌ |
| Filmszemcse (Film Grain) | `grain2` | ✅ | ✅ (statisztikai, nem pixelhű — sztochasztikus) | ❌ |
| Árnyalás (Tint) | `tint` | ✅ | ⚠️ implementálva, de **legrosszabb golden-egyezés (ΔE 20,6)** — a színparaméter-formátum tisztázatlan (Nyitva 4) | ❌ (a színt gomb nem kínálja fel, csak alapértelmezett) |
| Telítettség (Saturation) | `sat` | ✅ | ⚠️ negatív irány jó, pozitív irány romlik (ΔE 0,7–12,7) | ❌ |
| Lágy fókusz (Soft Focus) | `radblur` | ✅ | ⚠️ eltér (ΔE 3,2) | ❌ |
| Ragyogás (Glow) | `glow`/`glow2` | ✅ | ⚠️ közelítő (ΔE 1,9–2,7) | ❌ |
| Szűrt FF (Filtered B&W) | `ansel` | ✅ | ⚠️ eltér (ΔE 5,6) | ❌ |
| Fókuszos FF (Focal Saturation/B&W) | `radsat` | ✅ | ⚠️ nincs önálló golden-mérés (radblur-hez hasonló modell) | ❌ |
| Színátmenet (Graduated Tint) | `dir_tint` | ✅ | ⚠️ eltér (ΔE 9,4) | ❌ |
| **Vignette** *(nincs magyar fordítás — angolul jelenik meg a magyar UI-ban!)* | `Vignette` (nagybetűs ini-kulcs) | ✅ | ⚠️ eltér (ΔE 4,7), analitikus modell nyitva | ❌ |

> **HELYESBÍTÉS (2026-08-15, ▶KÉP + ▶ERŐFORRÁS, megerősített).** A fenti
> táblázat **13 sora közül a `Vignette` nem a 3., hanem az 5. fülön van.** Az
> eredeti 3. fül **pontosan 12 csempét** mutat (`2026-07-17 20 56 45.png`), az
> 5. fül szintén 12-t, és a „Vignetta" ott, a 3. helyen szerepel
> (`2026-07-17 20 56 55.png`). Ezt az elrendezés-erőforrás is megerősíti: az
> `editpanel.tre` **pontosan `fx1`…`fx12` csempehelyet** definiál, tizenharmadik
> nincs. Az összesítő 36-os végösszeg tehát helyes (12+12+12), csak a
> fülhovatartozás tolódik el eggyel. Részletek a 3. szakaszban.

**13/13 gomb megvan, 13/13 van render-handler** (`chain.py` `_HANDLERS`) —
ez a fül **funkcionálisan teljes**, de a `filters-decoded.md` „golden
verdiktek" táblája szerint **7 a 13-ból csak „eltér"/gyenge közelítés**
(Tint, Sat+, Soft Focus, Glow, Filtered B&W, Graduated Tint, Vignette) —
ezek pixelhűsége még nem éri el a Picasa-referenciát. Egyik effekt sem
kap saját erősség-csúszkát a UI-n, holott a `filters=` kulcsok szinte
mindegyike paraméteres (pl. `sat=1,s` erősség, `radblur` x/y/méret/erősség)
— ez külön hiányosság a „mindent kérek" panasztól függetlenül.

### 4. fül — zöld ecset (▶KUTATÁS #190, UI-hovatartozás ezen az auditon került hozzá az ikonhoz)

| Magyar UI-név | `filters=` kulcs | UI-gomb van? | Render-implementáció van? | Csúszkával paraméterezhető? |
|---|---|---|---|---|
| Infravörös film | `IR` | ❌ | ❌ | — |
| Lomo-szerű | `Lomo` | ❌ | ❌ | — |
| Holga-szerű | `Holga` | ❌ | ❌ | — |
| HDR-szerű | `HDR` | ❌ | ❌ | — |
| Kinemaszkóp | `Cinemascope` | ❌ | ❌ | — |
| Orton-szerű | `Orton` | ❌ | ❌ | — |
| 60-as évek | `Sixties` | ❌ | ❌ | — |
| Színinvertálás | `Invert` | ❌ | ❌ | — |
| Hőtérkép | `HeatMap` | ❌ | ❌ | — |
| Áttűnés | `CrossProcess` | ❌ | ❌ | — |
| Poszterizálás | `QuantizePalette` | ❌ | ❌ | — |
| Kéttónusú | `TwoTone` | ❌ | ❌ | — |

**0/12 gomb, 0/12 render** — a `chain.py` `_HANDLERS` szótárban egyik kulcs
sem szerepel; a `filters=` sztringben előforduló `IR=…`/`Lomo=…` stb.
bejegyzések a jelenlegi renderelő **némán kihagyja** (ismeretlen névként) —
tehát ha egy Windows-os Picasával szerkesztett kép ilyen effektet kapott,
a PicasaPy előnézete ma **effekt nélkül** mutatja (csak a `filters=`
sztring őrződik meg érintetlenül, a round-trip elv szerint — vizuálisan
viszont hiányzik).

### 5. fül — kék ecset (▶KUTATÁS #190, UI-hovatartozás ezen az auditon került hozzá az ikonhoz)

| Magyar UI-név | `filters=` kulcs | UI-gomb van? | Render-implementáció van? | Csúszkával paraméterezhető? |
|---|---|---|---|---|
| Felpörgetés | `Boost` | ❌ | ❌ | — |
| Lágyítás | `Soften` | ❌ | ❌ | — |
| Képpontnagyítás | `Pixelate` | ❌ | ❌ | — |
| Fókusznagyítás | `FocalZoom` | ❌ | ❌ | — |
| Ceruzarajz | `PencilSketch` | ❌ | ❌ | — |
| Neon | `Neon` | ❌ | ❌ | — |
| Képregény | `Comicize` | ❌ | ❌ | — |
| Szegély | `Border` | ❌ | ❌ | — |
| Árnyékvetés | `DropShadow` | ❌ | ❌ | — |
| Múzeumi matt | `MuseumMatte` | ❌ | ❌ | — |
| Polaroid | `Polaroid` | ❌ | ❌ | — |

**0/11 gomb, 0/11 render.**

> **HELYESBÍTÉS (2026-08-15, ▶KÉP, megerősített).** Ez a fül is **12 effektet**
> tartalmaz: a `Vignette` (magyarul **„Vignetta"**) a lista **3. eleme**,
> a `Soften` után és a `Pixelate` előtt (`2026-07-17 20 56 55.png`, 1. sor
> 3. csempéje). A sorrend egyébként szó szerint egyezik a fenti táblázattal.
> A magyar felirat tehát **létezik** — a 6. szakasz „a Vignette angolul jelenik
> meg" megállapítása **a PicasaPy hiányossága**, nem az eredetié.

### Összesítő szám

| Fül | Effektek száma | UI-gomb | Render-handler |
|---|---|---|---|
| 3. (sima ecset) | 12 | 12 | 12 (ebből 6 pontatlan/eltérő) |
| 4. (zöld ecset) | 12 | 0 | 0 |
| 5. (kék ecset) | 12 | 1 (Vignette) | 1 (Vignette, pontatlan) |
| **Összesen** | **36** | **13 (36%)** | **13 (36%)** |

*(A 2026-08-15-i helyesbítés előtt ez a bontás 13/12/11 volt; a végösszeg és a
lefedettségi arány változatlan, csak a `Vignette` került át a 3. fülről az
5.-re — ld. a fenti két helyesbítő dobozt.)*

Ez pontosan igazolja a feladat kiinduló becslését (~36 effekt, 3×~12
felül). A hiány nem részleges: a teljes 4. és 5. fül (**23 effekt, a
teljes katalógus 64%-a**) UI-gomb és render-handler nélkül áll — ez adja a
„MINDEN EFFEKTET KÉREK" panasz számszerű magyarázatát.

*(A táblázatokon kívül: a Finomhangolás/2. fül tartalma — Derítőfény,
Fények, Árnyékok, Színhőmérséklet, Semleges pipetta — a PicasaPy-ban MÁR
megvan 4 csúszkával (`finetuneColumn`, `EditorPanel.qml` 404–520. sor),
csak a pipetta-eszköz hiányzik. Ez a fül tehát nem effekt-hiány, hanem
más jellegű — nem szerepel a fenti 36-os számban.)*

## 3. Az effekt-csempe rács (3–5. fül) — pixelre mért felépítés

Forrás: `research/testdata/screenshot/2026-07-17 20 56 45.png` (3. fül),
`…20 56 50.png` (4. fül), `…20 56 55.png` (5. fül). Mindhárom **1920×1080,
1:1 nagyítás, teljes képernyős Windows-felvétel** (nem kicsinyített ablak),
tehát a lenti képpontértékek közvetlenül átvehetők 100%-os DPI mellett.
Kiegészítő forrás: `~/picasapy-agent/referencia/tre-eroforrasok/editpanel.tre`,
`macros.tre`, `fontmacros_win.tre`.

### 3.1 Van-e szekció-fejléc a rács fölött? — **NINCS** (megerősített)

▶**KÉP.** A `…20 56 45.png` bal paneljén függőlegesen mérve (x = 40 oszlop):

| Sáv | y-tartomány | Tartalom |
|---|---|---|
| fülsáv (5 ikonos fül) | **83–112** (30 px magas) | homokszínű színátmenet, RGB 213,209,202 → 167,163,156 |
| üres panelháttér | **113–125** (13 px) | egyenletes RGB 232,232,232 — **semmilyen szöveg, keret vagy elválasztó nincs benne** |
| 1. csempesor teteje | **126** | a csempe 1 képpontos kerete (RGB 187,187,187) |

Tehát a fülsáv és az első csempesor között **13 képpontnyi üres panelháttér**
van, felirat nélkül. ▶**ERŐFORRÁS** ezt megerősíti: az `editpanel.tre`-ben a
rács konténere közvetlenül a fül-lapra lóg, saját fejléc-elem nélkül:

```
editpanel/fxthumbs: editpanel/tabpanel3
XConstraint 0, 0, LEFTDRAWEROFFSET
YConstraint 0, 0, -20
```

**Következmény a PicasaPy-ra:** a jelenlegi 22 képpontos, „Kreatív" /
„Effektek" feliratú szekciósáv **nincs az eredetiben** — el kell hagyni. A
fül-tooltip hordozza ugyanezt az információt (▶ERŐFORRÁS,
`panel-feliratok-hu.tsv`): `editpanel/tab3` → „Hasznos képszerkesztési
lehetőségek", `tab4` → „További hasznos képszerkesztési lehetőségek",
`tab5` → „Még további hasznos képszerkesztési lehetőségek".

### 3.2 A rács geometriája (megerősített)

Mérés a `…20 56 45.png`-n, oszlop- és sorátmenetek keresésével:

| Jellemző | Érték | Hogyan mérve |
|---|---|---|
| Rács | **3 oszlop × 4 sor = 12 hely** | csempekeretek x = 6/94/182, y = 126/197/268/339 |
| Csempehely-szám (fix!) | **12** (`fx1`…`fx12`) | ▶ERŐFORRÁS `editpanel.tre`: 12 db `editpanel/fxN`, `fxlabelN`, `fxpreviewN`, `fxN_adorn` blokk, több nincs |
| Csempe mérete | **86 × 69 px** (kerettel együtt) | x 6–91, y 126–194 |
| Osztásköz | **88 × 71 px** | egymást követő bal keretek: 6 → 94 → 182 |
| Térköz csempék között | **2 px** | 91 → 94 |
| Csempekeret | **1 px, RGB 187,187,187** (#BBBBBB) | mind a 12 csempén azonos |
| Csempe kitöltése | **RGB 237,237,237 → 236,236,236** (finom függőleges átmenet) | a bélyegkép körüli sáv |
| Panel háttere | **RGB 232,232,232** | a csempéken kívül |
| Rács vízszintes helye | tartalom-oszlop **x = 6…267**; a panel jobb széle x ≈ 282 | a 3. oszlop jobb kerete 267 |

**A csempe belső felépítése** (az 1. csempén mérve):

| Elem | Pozíció / méret | Bizonyíték |
|---|---|---|
| Bélyegkép | **78 × 48 px**, a csempe keretének bal-felső sarkától **+4 / +4** (abszolút x 10–87, y 130–177) | oszlop- és sorszórás-profil |
| Felirat doboza | teteje = **csempe alja − 18 px** | ▶ERŐFORRÁS `fontmacros_win.tre` `#define m_fxlabel` → `YConstraint 0, 1, -18` |
| Felirat betűi | glifák y **180–188**, vízszintesen **középre zárva** | mérés + `Property textalign center` |
| Felirat betűtípusa | **11 px, fontweight 700** (félkövér), `fonttrack -1`, `fontleading 10`, oldalanként 4 px behúzás | ▶ERŐFORRÁS `m_fxlabel` teljes definíciója |
| Felirat **színe** | **RGB 51,51,51** (#333333) | a felirat-sáv legsötétebb képpontja |

A feliratszöveg forrása a `filter_<Kulcs>_label0` sztringerőforrás —
ugyanaz, ami a paraméter-alpanel címét is adja (ld. 4.1). Bizonyíték:
a 4. fül 1. sorának 3. csempéjén **„Holga-szerű"** olvasható, és a
`~/picasapy-agent/referencia/stringres-en-hu.tsv` 2808. sorában
`filter_Holga_label0` → EN „Holga-ish" / HU „Holga-szerű". *(megerősített)*

A rács alatt, a 4. sor alatt közvetlenül a **„Visszavonás" / „Újra"**
gombpár fut végig (y ≈ 418–440); mindkettő **letiltott** ezen a felvételen
(▶ERŐFORRÁS `editpanel/filter_undo` / `filter_redo`).

### 3.3 Az „alkalmazva" jelvény (`fx%d_adorn`)

**A bináris visszakeresés eredménye — MEGVAN** ▶**BINÁRIS.** A
`~/picasapy-agent/referencia/binary-index/string_xrefs.csv` 7016–7017. sora
(image base `0x00400000`):

| Sztring | Cím (VA) | RVA / fájl-eltolás | Hivatkozó függvény |
|---|---|---|---|
| `editpanel/fx%d_adorn` | `0x00C96304` | `0x00896304` | `FUN_005d7c20` (RVA `0x001d7c20`, 1614 bájt) |
| `editpanel/fx%d` | `0x00C9631C` | `0x0089631C` | ugyanaz |
| `editpanel/fxlabel%d` | `0x00C962EC` | `0x008962EC` | ugyanaz |
| `editpanel/fxpreview1` | `0x00C962C4` | `0x008962C4` | ugyanaz |
| `editpanel/fxthumbs` | `0x00C902B8` | `0x008902B8` | ugyanaz |
| `_tab%d` | `0x00C962DC` | `0x008962DC` | ugyanaz |
| `_mod%s` | `0x00C962E4` | `0x008962E4` | ugyanaz |

Tehát **egyetlen függvény** (`0x005d7c20`) építi föl az egész csempesort:
a csempét, az előnézetet, a feliratot és a jelvényt, `_tab%d` / `_mod%s`
gyorsítótár-kulcsokkal. *(megerősített)*

**Helye — az erőforrás és a mérés egyezik** *(megerősített)*:

▶**ERŐFORRÁS**, `macros.tre` 301–303. sor:

```
#define m_fxadorner
XConstraint 1, 1, -6
YConstraint 1, 1, -19
```

vagyis a jelvény **jobb széle = a csempe jobb széle − 6 px**, **alja = a
csempe alja − 19 px**. Mivel a felirat doboza a csempe aljától 18 px-re
kezdődik, a jelvény alja pontosan **a bélyegkép alsó élére simul**, annak
**jobb alsó sarkába**.

▶**KÉP**, mérés a Szépia-csempén (`…20 56 45.png`, 1. sor 2. csempe,
csempe x 94–179, y 126–194; bélyegkép x 98–175, y 130–177):

| Jellemző | Mért érték | Erőforrásból várt |
|---|---|---|
| Jelvény befoglaló doboza | **x 162–174, y 165–176** | — |
| Méret | **13 × 12 px** | — |
| Jobb szél | 174 | 179 − 6 = 173 (1 px eltérés, élsimítás) |
| Alsó szél | 176 | 194 − 19 = 175 (1 px eltérés) |
| Kitöltés (uralkodó szín) | **RGB 55,159,253** (#379FFD) | — |
| Alak | **negyed-korong**: csak a **bal felső** sarka lekerekített, a jobb és az alsó éle egyenes (a bélyegkép sarkába simul) | — |
| Szám | fehér, félkövér **„1"**, a jelvény jobb oldalán | — |

**Melyik csempén van jelvény?** (kék képpontok automatikus keresésével,
majd szemrevételezéssel ellenőrizve):

| Fül | Jelvényes csempe | Szám |
|---|---|---|
| 3. | Szépia (1/2), Fekete-fehér (1/3), Melegítés (2/1) | mind **1** |
| 4. | Színinvertálás (3/2) | **1** |
| 5. | — | — |

*(A 3. fül „Árnyalás" csempéje a gépi keresésben álpozitív volt: annak a
bélyegképe maga kék; szemrevételezésre nincs rajta jelvény.)*

### 3.4 Mit jelent a jelvényen a szám? — **részben eldöntve, részben nyitva**

**ELVETVE: nem a lánc sorszáma.** ▶KÉP. A `…20 56 45.png`-n **három
csempén egyszerre** van jelvény, és **mindhármon „1"** áll. Ha a szám a
szerkesztési láncban elfoglalt sorrendet jelölné, 1-et, 2-t és 3-at kellene
mutatniuk. *(megerősített cáfolat)*

**A kézenfekvő „hányszor van alkalmazva" olvasat sem áll meg ezen a képen.**
Ugyanez a felvétel három egymást erősítő bizonyítékkal mutatja, hogy a
fotón **egyáltalán nincs szerkesztés**:

1. a **„Visszavonás" és az „Újra" gomb egyaránt letiltott** (kiszürkült
   felirat, `…20 56 45.png`, y ≈ 418–440);
2. a **nagy előnézet szerkesztetlen** — teljesen színes tájkép; ha a
   Szépia + Fekete-fehér + Melegítés lánc valóban aktív lenne, monokróm
   lenne (és mind az öt fül-felvételen **azonos** az előnézet átlagszíne);
3. a **csempe-előnézetek** is a szerkesztetlen képből számolnak (az
   „Élesítés" csempe teljesen színes).

Tehát a jelvény ezen a képen **nem a jelenlegi fotó láncát tükrözi**.

**Ami feltűnő, de nem elég bizonyíték** *(feltételes, nem szabad rá építeni)*:
a négy jelvényes effekt — `sepia`, `bw`, `warm`, `Invert` — pontosan azok,
amelyeknek a `filterdesc.xml` szerint **nincs paraméterük és nincs
lassú/teljes felbontású jelzőjük** (`docs/specs/filterdesc-registry.md`
124–188. sor). A `grain2` (Filmszemcse) szintén `oneclick`, de
`fullres+slow` — és **nincs** rajta jelvény. Ez az egyezés lehet
véletlen is; négy megfigyelés kevés.

**Mi hiányzik a döntéshez, és mi a következő lépés:**

1. **Célzott képernyőkép-kérés a felhasználótól** (a legolcsóbb): a
   windowsos Picasában (a) egy friss fotón alkalmazni **kétszer** a Szépiát,
   és lefényképezni a 3. fület — ha a jelvény **„2"**-re vált, a
   darabszám-olvasat bizonyított; (b) egy szerkesztett fotóról egy
   szerkesztetlenre váltani, és megnézni, eltűnik-e a jelvény — ha nem, akkor
   a mostani felvételen látott jelvények **beragadt (gyorsítótárazott)
   állapotot** mutatnak.
2. **A `FUN_005d7c20` (VA `0x005d7c20`, RVA `0x001d7c20`, 1614 bájt)
   dekompilálása** — ez a függvény írja a jelvény szövegét, tehát
   egyértelműen eldönti a kérdést. (Ehhez Ghidra-kör kell; ebben a körben
   nem futott.)

**A PicasaPy-nak addig is:** a jelvény **helye, mérete, alakja és színe
megerősített** — ez implementálható; csak a **számérték forrását** kell
egyelőre a legvédhetőbb olvasattal (a hatóelem előfordulásainak száma a
`filters=` láncban) megvalósítani, és a fenti kísérlet után felülvizsgálni.

## 4. Az effekt-paraméter alpanel (csúszkás panel)

Ebben a képcsomagban **nincs olyan felvétel, amelyen egy effekt
paraméter-alpanelje nyitva volna** — mind az 56 kép átnézve. A szakasz ezért
két, egymást ellenőrző forrásból épül fel: az elrendezés-erőforrásokból
(▶ERŐFORRÁS) és a **2. fül (Finomhangolás) felvételéből** (▶KÉP,
`2026-07-17 20 56 42.png`) — az alábbi 4.2 pont mutatja meg, hogy a kettő
**ugyanaz a vezérlőkészlet**, tehát a 2. fül képe érvényes pixelbizonyíték az
alpanelre is.

### 4.1 A panel címe — honnan jön a szöveg (megerősített)

A cím elemének neve ▶ERŐFORRÁS `editpanel.tre` 585–588. sor:

```
editpanel/filter_name: editpanel/edittabbase
m_offsetLT
m_hidden
m_displayfont18_Reg
```

- **Alapból rejtett**, és minden fülgomb kifejezetten elrejti
  (`Property hidetarget editpanel/filter_name` — a `tab1`…`tab5` és minden
  eszközgomb blokkjában); csak akkor jelenik meg, amikor egy paraméteres
  effektet választunk.
- **Nincs hozzá beégetett felirat**: a `editpaneltext.tre`-ben nincs
  `Label editpanel/filter_name` sor (ellentétben pl. a `crop_label`-lel) —
  **futásidőben kapja meg a kiválasztott szűrő nevét**.
- Az a név a `filterdesc.xml` `<label>`-jén keresztül a
  **`filter_<Kulcs>_label0` sztringerőforrásra** mutat.
  Bizonyíték, `~/picasapy-agent/referencia/stringres-en-hu.tsv` **2808. sor**:

  ```
  filter_Holga_label0	Holga-ish	Holga-szerű
  ```

  és a 2809. sorban a hozzá tartozó elemleírás:
  `filter_Holga_tooltip0` → „Make your photo look like it was taken with a
  plastic camera" / „Olyanná alakítja a fotót, mintha műanyag
  fényképezőgéppel készítették volna". Ugyanez a név szerepel a
  `docs/specs/filterdesc-registry.md` 168. sorában (`Holga` → *Holga-ish*).

**Tehát:** az angol felületen a cím **„Holga-ish"**, a magyaron
**„Holga-szerű"** — és **ugyanez a szöveg** áll a 4. fül csempéje alatt is
(▶KÉP, `…20 56 50.png`). A PicasaPy jelenlegi **„holga"** címe a belső
kulcsot mutatja: a javítás **nem fordítás kérdése**, hanem annyi, hogy a
címet és a csempefeliratot **ugyanabból a névtáblából** kell venni.
*(megerősített)*

**Tipográfia:** `m_displayfont18_Reg` = **Praxis LT Regular, 18 pt,
fontweight 400**, `fonttrack -1` (▶ERŐFORRÁS `fontmacros_win.tre` 79–83).
Elhelyezés: `m_offsetLT`, tehát **balra-felülre igazítva** az
`editpanel/edittabbase` konténerben — **nem középre**. Ez pontosan ugyanaz a
betűmakró, amit a vágás-panel „Fotó vágása" címe használ
(`editpanel/crop_label`, `editpanel.tre` 754–756), tehát a két
panelcím tipográfiailag azonos. *(megerősített)*

### 4.2 Az alpanel és a Finomhangolás fül UGYANAZT a vezérlőkészletet használja

Ez a szakasz kulcsa. ▶**ERŐFORRÁS**, `editpanel.tre`:

- a 2. fül gombja megjeleníti a közös vezérlő-tárolót:
  `editpanel/tab2` → `Property showtarget editpanel/editcontrol_well`;
- és **minden** csúszka, jelölőnégyzet, színkorong, pipetta, radír, valamint
  az **Alkalmaz/Mégse** gomb ennek a `editcontrol_well`-nek a gyermeke
  (501–660. sor).

A készlet **teljes leltára** (ez egyben a paraméter-alpanel felső korlátja):

| Elem | Darab | Erőforrás-név |
|---|---|---|
| Csúszka + fölötte felirat | **4** | `editslider1..4` + `editpanel/editslider1..4_container`, `editpanel/editlabel1..4` |
| Jelölőnégyzet + felirat | **2** | `editpanel/editcheckbox1..2`, `editpanel/editlabel5..6` |
| Színkorong + felirat + körcsúszka | **2** | `editpanel/colorwheel0..1`, `colorwheel_label0..1`, `slidercircle0..1` |
| Színpipetta-kapcsoló | 1 | `editpanel/droppertoggle` |
| Radír (maszkoláshoz) | 1 | `editpanel/eraserbutton` |
| Alkalmaz / Mégse | 1+1 | `editpanel/ok`, `editpanel/cancel` |

**Keresztellenőrzés (erős):** ez a keret pontosan lefedi a
`filterdesc-registry.md` 276–307. sorában felsorolt legnagyobb
paraméter-alakzatokat is — a `Border` (2 szín + 4 szám) és a `DropShadow`
(2 szín + 4 szám) éppen kimeríti a „4 csúszka + 2 színkorong" keretet, a
`Sixties`/`PicnikGrain`/`Cinemascope` jelölőnégyzete pedig az
`editcheckbox1`-et. Négynél több számot egyetlen szűrő sem kér.

**Következmény:** a `2026-07-17 20 56 42.png` (2. fül) **ugyanazokat a
csúszkapéldányokat mutatja**, amelyeket a paraméter-alpanel is használ —
tehát a lenti geometria közvetlen mérésből származik. *(erős)*

### 4.3 A csúszka geometriája (mérés a 2. fül felvételén)

`2026-07-17 20 56 42.png`, 1920×1080, 1:1:

| Jellemző | Érték |
|---|---|
| Csúszkák függőleges osztásköze | **53 px** (sávtetők: y 162 / 215 / 268 / 321) |
| Sáv (track) magassága | **9 px** (y 162–170) |
| Sáv vízszintes kiterjedése | **x 44–230**, azaz **187 px** |
| Sáv középvonala | x = **137** — a panel tartalom-oszlopának (6–267) közepe 136,5 → **a csúszka a panelben középre van igazítva** (▶ERŐFORRÁS: `editpanel/editsliderN_container` → `m_centerXY`) |
| Sáv színe | hideg szürkéskék, RGB 202,213,229 alap, 175,192,216 belső árnyék |
| Fogantyú (thumb) | **16 × 26 px**, **álló, lekerekített kapszula** (ovális) — x 44–59, y 155–180, függőlegesen a sávra központozva |

### 4.4 A paraméter-felirat igazítása — **a csúszka FÖLÖTT, KÖZÉPEN** (megerősített)

▶**KÉP.** Mért felirat-középpontok a 2. fülön (a betűk befoglaló doboza
alapján), szemben a sáv középvonalával (x = 137):

| Felirat | Betűk x-tartománya | Középpont |
|---|---|---|
| Derítőfény | 115–161 | **138** |
| Színhőmérséklet | 100–176 | **138** |

*(A „Kiemelések" és az „Árnyékok" sorát a jobb szélen ülő
varázspálca-gomb rontja el a gépi mérésben; a két tiszta sor elég.)*

Függőlegesen: a felirat betűi y **141–148**, a sáv teteje y **162** — tehát
a felirat **a csúszka fölött**, kb. **14 px-rel** a sáv fölött ül.

▶**ERŐFORRÁS** ugyanezt mondja ki: `editpanel/editlabel1..4` mind
`m_fxlabel2`-t használ, ami (`fontmacros_win.tre` 291–295):

```
#define m_fxlabel2
Property fontname Praxis Semi Bold/Heavy
Property fonttrack -1
Property fontsize 12
Property fontweight 400
Property textalign center
```

— **Praxis Semi Bold/Heavy, 12 pt, fontweight 400, középre zárva.**

### 4.5 Kiírja-e az eredeti a számértéket? — **NEM** (megerősített)

▶**KÉP.** A 2. fül mind a négy csúszkája mellett/fölött/alatt **kizárólag a
szöveges felirat** áll; sehol nincs szám, százalék vagy mértékegység
(`2026-07-17 20 56 42.png`). ▶**ERŐFORRÁS** ezt megerősíti: a
`editcontrol_well` gyermekei között **nincs** értékkijelző elem — a csúszka
mellett csak `editlabelN` van, és annak sincs futásidejű szám-formátuma az
`editpaneltext.tre`-ben.

**Következmény a PicasaPy-ra:** a szám kiírása **eltérés az eredetitől**.
(Ha ergonómiai okból mégis megtartjuk, azt tudatos, dokumentált eltérésként
kell kezelni, nem véletlenként.)

### 4.6 A gombsor — és összevetés a vágás-panel gombjaival

▶**ERŐFORRÁS**, `editpanel.tre` 603–630:

```
editpanel/ok_icon: editpanel/ok
m_buttoniconright
editpanel/ok-label: editpanel/ok
m_buttonfontLC
editpanel/ok: editpanel/editcontrol_well
m_buttontypecolor
m_hidden
XConstraint 0.5, 0.5, -52
m_offsetT
```

és ugyanígy `editpanel/cancel`, csak `XConstraint 0.5, 0.5, 52` +
`Property escapekey 1`.

| Kérdés | Válasz | Bizonyíték |
|---|---|---|
| Igazítás | **középre igazított gombpár**, a panel közepétől **∓52 px** (104 px-es középtávolság) | `XConstraint 0.5, 0.5, ∓52` |
| Ikon helye | a gomb **jobb szélétől 9 px-re, függőlegesen középen** | `m_buttoniconright` = `XConstraint 1,1,-9` + `YConstraint 0.5,0.5,0` (`macros.tre` 153–155) |
| Felirat | balra igazított, függőlegesen középen, **Praxis Semi Bold/Heavy 12 pt** | `m_buttonfontLC` (`fontmacros_win.tre` 122–130) |
| Feliratszöveg (EN/HU) | **Apply / Alkalmaz**, **Cancel / Mégse** | `editpaneltext.tre` 187–197; `panel-feliratok-hu.tsv` |
| Elemleírás (tooltip) | „Apply Changes" / **„Módosítások alkalmazása"**, „Cancel Changes" / **„Változások visszavonása"** | ugyanott |
| Esc billentyű | a Mégse gombra van kötve | `Property escapekey 1` |

**Ugyanaz a gombtípus, mint a vágás-panelen? — IGEN** *(megerősített).*
A vágás-panel gombjai **külön példányok** (`editpanel/cropapply`,
`editpanel/cropcancel`, `editpanel.tre` 805–826 (`cropcancel` 805–815, `cropapply` 817–826)), de **pontosan ugyanazt a
három makrót** kapják: `m_buttoniconright` + `m_buttonfontLC` +
`m_buttontypecolor`. A különbség kizárólag az **elhelyezés** és a
**szöveg**:

| | Paraméter-alpanel | Vágás-panel |
|---|---|---|
| Elem | `editpanel/ok` / `editpanel/cancel` | `editpanel/cropapply` / `editpanel/cropcancel` |
| Szülő | `editpanel/editcontrol_well` | `editpanel/crop_well` |
| Elhelyezés | középre, ∓52 px | `m_offsetLT` (az alaprajz saját eltolásai) |
| Elemleírás | „Módosítások alkalmazása" | **„Vágási szerkesztések alkalmazása"** |

Ez utóbbi egyben **visszaigazolja az 5. szakasz** (korábbi 3. szakasz)
képről olvasott tooltipjét, immár erőforrás-szinten is.

**Következmény a PicasaPy-ra:** a zöld pipa / piros X **ikon**, nem
Unicode-karakter, és a **felirat jobb oldalán**, a gomb jobb szélétől 9
px-re ül — ugyanúgy a vágás-panelen és a paraméter-alpanelen. A két helyen
**egyetlen közös gombkomponenst** érdemes bevezetni.

## 5. A vágás-panel („Fotó vágása") pontos felépítése

▶**KÉP**, `…195113.png` (dropdown nyitva) és `…195123.png` (arány
kiválasztva, gombok láthatók). A panel szélessége a screenshoton kb.
**270–290 képpont** (a kicsinyített ablak ~78–94%-a — ez összhangban van
a `design-guide.md` „Néző eszközpanel ~280px széles" bejegyzésével,
1920×1080 alapon).

### Fejléc

- Kis fotó-ikon (40×30 körüli) + **„Fotó vágása"** cím, nagyobb (kb.
  Theme.fontSize+3-nak megfelelő) betűvel.
- Alatta szürke leíró szöveg, 3 sorba tördelve: *„Válasszon az alábbi
  méretek közül, majd a fogd és húzd módszerrel jelölje ki a képnek azt a
  részét, amelyiket ki szeretné vágni."*
  — a PicasaPy jelenlegi angol forrásszövege ennek jó fordítása
  (`EditorPanel.qml` 678–679. sor: *„Choose a size below, then drag on the
  picture to select the area you want to keep."*), tartalmilag egyezik.

### Méretarány-legördülő — TELJES lista (`…195113.png`-ből pixelre olvasható)

A legfelső sor a kombó **aktuális értéke** (itt: `Kézi: 504 x 622` —
konkrét, aktuálisan kijelölt pixelméret, nem csak „Kézi"), utána a
lenyíló lista:

| # | Felirat | Megjegyzés |
|---|---|---|
| 1 | **Kézi: 504 x 622** | szabad arány, a jelenlegi kijelölés mérete a névben |
| 2 | Jelenlegi méretarány: 928×1232 | a kép saját (eredeti) arányát rögzíti |
| 3 | 5x8 | |
| 4 | 9x13: Kisméretű nyomat | |
| 5 | 10x15: Nagyméretű nyomat | |
| 6 | 13x18 | |
| 7 | 20x25 | |
| 8 | A4: Teljes oldal | |
| 9 | Négyzet: CD-borító | |
| 10 | 4:3: Normál képernyő | |
| 11 | 16:10: Szélesvásznú képernyő | |
| 12 | 16:9: HDTV | |
| 13 | 5:3: Szélesvásznú képkocka | |
| 14 | **Egyéni méretarányok** *(vastagon — szakaszcím, nem választható sor)* | |
| 15 | Egyéni méretarány hozzáadása… | dialógust nyit (ld. lent) |

A kombó jobb szélén egy kis **kuka-ikon** ül (nem választógomb!) —
`…195123.png` nagyítva mutatja: a kiválasztott (beépített) aránynál
**inaktív/szürke** (feltehetően csak egyéni, felhasználó által felvett
arányoknál engedélyezett — törlésre).

**PicasaPy-egyezés** (`aspectPresets`, `EditorPanel.qml` 96–110. sor): a
3–13. sor (a 11 fix méretarány) **szó szerint egyezik** a screenshottal —
ez a lista korábban már pontosan lett portolva. **Hiányzik**: az 1–2. sor
motívuma (a „Kézi" felirat a screenshoton az AKTUÁLIS kijelölés méretét is
mutatja, pl. „Kézi: 504 x 622" — a PicasaPy-ban a felirat statikus
`"Manual"`), valamint **teljesen hiányzik a 14–15. sor**: nincs „Egyéni
méretarányok" szakasz, nincs „Egyéni méretarány hozzáadása…" opció, nincs
kuka/törlés-ikon — az egyéni arányok funkciója **0%-ban implementált**.

### Egyéni méretarány hozzáadása — dialógus

▶**KÉP**, `…195907.png`. Kis, központi modális ablak:

- Cím: **„Egyéni méretarány hozzáadása"** (ablakcím-sávban, bezáró ×-szel)
- **Méretek:** felirat, mellette **két számmező** `x` elválasztóval (üres
  állapotban placeholder nélkül, csak keret — a bal mező kék kerettel
  aktív/fókuszált állapotban a képen)
- **Név:** felirat, alatta egysoros szövegmező
- Élő **példa-sor**: *„Példa: 4x6 kisméretű nyomat"* — feltehetően a
  begépelt számokból/névből élőben frissül
- **OK** gomb (a képen **inaktív/szürke** — üres mezőknél letiltva) és
  **Mégse** gomb, jobbra lent

Ennek a PicasaPy-ban **nincs megfelelője** — sem a menüpont, sem a
dialógus nem létezik.

### Bélyegkép-sor, gyors-vágások

▶**KÉP**, `…195123.png`. A legördülő alatt **3 bélyegkép** (nem szöveges
gomb!) — a kiválasztott aránnyal (itt 4:3) a fotó három eltérő
kivágás-javaslata: bal = felül/szűkebb kivágás, közép = a teljes jelenet
(legszélesebb), jobb = az állófigurára közelebb húzott kivágás. Ez a
PicasaPy jelenlegi **„Bal-felső" / „Fekvő" / „Álló" (topleft/landscape/
portrait) feliratos szövegdoboz-hármasának** felel meg funkcióban
(darabszám: 3 = 3 egyezik), de **vizuálisan más**: az eredeti élő
fotó-bélyegképet mutat (a tényleges kivágást előnézve), a PicasaPy jelenleg
csak feliratos gombokat rajzol előnézet nélkül.

### Gombsor a bélyegképek alatt

▶**KÉP**. Sorban, felülről lefelé:

1. **„Forgatás"** / **„Előnézet"** — egy sorban, két egyenlő gomb
   (PicasaPy: `cropRotateButton`/`cropPreviewButton`, „Rotate"/„Preview" —
   funkció és elhelyezés egyezik)
2. **„Alaphelyzet"** — önálló, teljes szélességű gomb, középen
   (PicasaPy: `cropResetButton`, „Reset" — de csak 120px széles és
   középre igazított, NEM teljes szélességű, mint az eredetiben)
3. **„Alkalmaz"** (zöld pipa-ikon a felirat jobb szélén, kör alakú zöld
   jelvényben) / **„Mégse"** (sötétvörös X-ikon, kör alakú jelvényben) —
   egy sorban, két gomb
   (PicasaPy: `cropApplyButton`/`cropCancelButton`, felirat + Unicode
   „✔"/„✘" karakter a szöveg UTÁN fűzve — vizuálisan **jóval
   szegényesebb**, mint az eredeti kör-jelvényes, színes ikon: nincs zöld
   kör/piros kör háttér, a Unicode-glyph betűtípusfüggő, esetleg hiányzik)
4. Egérrel az **„Alkalmaz"** fölé állva klasszikus sárgás **tooltip**
   jelenik meg: **„Vágási szerkesztések alkalmazása"** — ennek nincs
   PicasaPy-megfelelője (nincs tooltip-szöveg definiálva a crop-gombokon).

## 6. Egyéb megfigyelt hiányosság: hiányzó magyar fordítás

A `picasapy_hu.ts` fájlban (ellenőrizve, `grep`) **nincs bejegyzés** a
„Sharpen" és a „Vignette" forrásfeliratokhoz — ez a két effekt-gomb a
magyar felületen is **angolul** jelenik meg, holott az összes többi 3.
füles effekt-gombnak van magyar fordítása. Apró, de a `Kicsi, sok fájl`
elv szerinti gyors javítás (fordítási bejegyzés hozzáadása) — nem
architektúra-kérdés.

## 7. Más látott dialógus — Mappakezelő (kontextus, nem #315/#316/#318 fókusz)

▶**KÉP**, `…155818.png` — csak a teljesség kedvéért, mivel a csomagban
volt: az eredeti **Mappakezelő** ablak mappafánézettel (bal), és jobbra
egy adott mappára vonatkozó **rádiógomb-hármas** („Keresés egyszer" /
„Eltávolítás a Picasából" / „Keresés mindig"), alatta egy „Arcfelismerés
bekapcsolva" kapcsoló, lent egy „Figyelt mappák" lista, és OK/Mégse/Súgó
gombsor. A PicasaPy saját `FolderManagerDialog.qml`-je ma checkbox-fás
mappalistát ad rádiógomb-hármas helyett — **strukturálisan eltérő
paradigma**, de mivel ez nem a szerkesztőpanel/#315-316-318 tárgyköre,
külön auditot érdemel, itt csak jelzésként szerepel.

## 8. Összegzés — mi hiányzik, prioritási sorrendben

1. **A 4. és 5. effekt-fül teljes hiánya (23 effekt, UI + render egyaránt
   nulla)** — ez adja a felhasználói panasz 64%-át számszerűsítve. Már
   csak a `filters=` kulcsnevek és paraméterminták is megvannak
   (`filters-decoded.md` #190) — a csúszka↔paraméter leképezés (mit
   csinál pontosan az `IR`, a `Lomo` erősség-mezője stb.) még nyitott
   kutatási kérdés (a `make_param_sweep.py` generátor már kész hozzá,
   de a tényleges leképezés a felhasználó tömeges exportjából még
   feldolgozandó — `filters-decoded.md` „Nyitva" 7. pont).
2. **5-fülű fejléc bevezetése 3 helyett** — ma az `activeTab` 0–2 tartományú
   és a QML-ben nincs helye 2 új fülnek; ez architekturális előfeltétele
   az 1. pontnak (előbb ez, aztán tölthető fel a 4–5. fül gombrácsa).
3. **A 3. fülön belüli render-pontosság** — 7 effektnél (Tint, Saturation+,
   Soft Focus, Glow, Filtered B&W, Graduated Tint, Vignette) a golden-mérés
   szerint a kimenet **eltér** a valódi Picasától (ΔE 3–20) — ez már
   most is látható/kattintható effekt, csak nem pixelhű; a `filters-
   decoded.md` „Nyitva" 8. pontja szerinti sorrend követhető
   (tint → dir_tint → sat+ → …).
4. **Egyéni méretarányok** (14–15. legördülő-sor + „Egyéni méretarány
   hozzáadása" dialógus + kuka-ikon) — kisebb, önmagában lezárható
   feladat, jól specifikált ezen az auditon (2. és 5. szakasz).
5. **Kozmetikai/kisebb tételek**: „Alkalmaz"/„Mégse" színes kör-ikonjai
   Unicode-karakter helyett; „Alaphelyzet" gomb teljes szélessége; a
   3 gyorsvágás élő fotó-bélyegképként (nem csak felirat); Alkalmaz-gomb
   tooltip szövege; „Sharpen"/„Vignette" hiányzó magyar fordítás; a
   „Kézi" arány-felirat dinamikus mérete.
6. ~~**Nyitott kutatási igény**: ehhez az audithoz nem állt rendelkezésre
   képi bizonyíték a 2., 4. és 5. fül TARTALMÁRÓL…~~ — **LEZÁRVA
   (2026-08-15).** A `2026-07-17 20 56 36…55.png` ötös sorozat mind az öt
   fület megnyitva mutatja; az ebből nyert anyag a 3. és a 4. szakasz.

### Ami a 3–4. szakasz után nyitva maradt (2026-08-15)

| # | Nyitott kérdés | Bizalmi fok | Mi kell a lezáráshoz |
|---|---|---|---|
| N1 | Mit jelent a szám az „alkalmazva" jelvényen? A **lánc-sorszám olvasat elvetve**; a „hányszor van alkalmazva" olvasat viszont ellentmond annak, hogy a felvételen a fotón nincs szerkesztés (3.4) | feltételes | (a) célzott képernyőkép: ugyanazt az effektet **kétszer** alkalmazva mutat-e „2"-t; (b) fotóváltás után eltűnik-e a jelvény; (c) a `FUN_005d7c20` (VA `0x005d7c20`) dekompilálása |
| N2 | Az effekt-paraméter alpanel **tényleges** képernyőképe | — | egy felvétel bármelyik paraméteres effekt (pl. Holga-szerű) megnyitott alpaneléről — a 4. szakasz jelenleg az erőforrásokból + a 2. fül azonos vezérlőiből következtet |
| N3 | A csempék elemleírása (tooltip) megjelenik-e a rácsban, és a `filter_<Kulcs>_tooltip0` szövege-e | feltételes | egérrel egy csempe fölött készített felvétel |
| N4 | A csempe **kijelölt / egér alatti** állapotának megjelenése (keret, kitöltés) | nincs adat | felvétel egérmutatóval a csempe fölött |
| N5 | A rács **görgethető-e** 12 csempénél többnél (a `fx1…fx12` fix — de a `picnik_fx` gomb létezik a rács alján, rejtetten) | feltételes | `editpanel/picnik_fx` szerepének tisztázása |
