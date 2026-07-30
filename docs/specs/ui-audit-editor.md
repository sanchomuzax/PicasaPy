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
teljesség kedvéért, röviden érintem az 5. szakaszban.

**Korlát, amit fontos előre leszögezni:** a két hasznos kép **kizárólag a
vágás-fület (1. fül, csavarkulcs) mutatja megnyitva**. A másik négy fül
(Finomhangolás, és a három ecset-fül) tartalmáról **nincs képi bizonyíték**
ebben a csomagban — az alábbi effekt-leltár a fülcímkék/ikonok
(képi tény) és a projekt már meglévő, korábbi képcsomagból származó
kutatási eredménye (`docs/specs/filters-decoded.md`, 5. kör, #190) alapján
áll össze. Ahol a forrás a mostani screenshot, ott ▶**KÉP**; ahol a korábbi
kutatás, ott ▶**KUTATÁS (#190)** jelzi.

## 1. A fülrendszer — megerősítve: **5 ikonos fül, nem 3**

▶**KÉP.** A panel tetején, a „Vissza a könyvtárhoz" gomb alatt egy 5 elemű,
egyenlő szélességű ikonsáv fut végig (a wrench balra igazítva, a többi
egyenlő osztásban jobbra):

| # | Ikon | Feltételezett fül-cím | Tartalom (ez a csomag / korábbi kutatás) |
|---|---|---|---|
| 1 | 🔧 csavarkulcs — **AKTÍV** a képeken | Alapvető javítások | Vágás (jelen doc 3. szakasza), Kiegyenesítés, Vörösszem, Jó napom van, Automatikus kontraszt/szín, Retusálás, Szöveg, gyors Derítőfény-csúszka (`docs/specs/design-guide.md` korábbi screenshot-mintáiból) |
| 2 | ☀️ nap/csillag | Finomhangolás (Tuning) | Derítőfény, Fények, Árnyékok, Színhőmérséklet, Semleges szín pipetta (`finetune2` 5 paramétere, `filters-decoded.md` 1. kör) — tartalom NEM látszik ezen a screenshoton |
| 3 | 🖌️ sima ecset (nincs alatta szín-minta) | Effektek | 13 törzs-effekt (2. szakasz táblázata) |
| 4 | 🖌️ ecset **zöld tájkép-mintával** | 4. effekt-fül | 12 effekt — kulcsok `#190`-ből azonosítva (2. szakasz) |
| 5 | 🖌️ ecset **kék ég-mintával** | 5. effekt-fül | 11 effekt — kulcsok `#190`-ből azonosítva (2. szakasz) |

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

### Összesítő szám

| Fül | Effektek száma | UI-gomb | Render-handler |
|---|---|---|---|
| 3. (sima ecset) | 13 | 13 | 13 (ebből 7 pontatlan/eltérő) |
| 4. (zöld ecset) | 12 | 0 | 0 |
| 5. (kék ecset) | 11 | 0 | 0 |
| **Összesen** | **36** | **13 (36%)** | **13 (36%)** |

Ez pontosan igazolja a feladat kiinduló becslését (~36 effekt, 3×~12
felül). A hiány nem részleges: a teljes 4. és 5. fül (**23 effekt, a
teljes katalógus 64%-a**) UI-gomb és render-handler nélkül áll — ez adja a
„MINDEN EFFEKTET KÉREK" panasz számszerű magyarázatát.

*(A táblázatokon kívül: a Finomhangolás/2. fül tartalma — Derítőfény,
Fények, Árnyékok, Színhőmérséklet, Semleges pipetta — a PicasaPy-ban MÁR
megvan 4 csúszkával (`finetuneColumn`, `EditorPanel.qml` 404–520. sor),
csak a pipetta-eszköz hiányzik. Ez a fül tehát nem effekt-hiány, hanem
más jellegű — nem szerepel a fenti 36-os számban.)*

## 3. A vágás-panel („Fotó vágása") pontos felépítése

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

## 4. Egyéb megfigyelt hiányosság: hiányzó magyar fordítás

A `picasapy_hu.ts` fájlban (ellenőrizve, `grep`) **nincs bejegyzés** a
„Sharpen" és a „Vignette" forrásfeliratokhoz — ez a két effekt-gomb a
magyar felületen is **angolul** jelenik meg, holott az összes többi 3.
füles effekt-gombnak van magyar fordítása. Apró, de a `Kicsi, sok fájl`
elv szerinti gyors javítás (fordítási bejegyzés hozzáadása) — nem
architektúra-kérdés.

## 5. Más látott dialógus — Mappakezelő (kontextus, nem #315/#316/#318 fókusz)

▶**KÉP**, `…155818.png` — csak a teljesség kedvéért, mivel a csomagban
volt: az eredeti **Mappakezelő** ablak mappafánézettel (bal), és jobbra
egy adott mappára vonatkozó **rádiógomb-hármas** („Keresés egyszer" /
„Eltávolítás a Picasából" / „Keresés mindig"), alatta egy „Arcfelismerés
bekapcsolva" kapcsoló, lent egy „Figyelt mappák" lista, és OK/Mégse/Súgó
gombsor. A PicasaPy saját `FolderManagerDialog.qml`-je ma checkbox-fás
mappalistát ad rádiógomb-hármas helyett — **strukturálisan eltérő
paradigma**, de mivel ez nem a szerkesztőpanel/#315-316-318 tárgyköre,
külön auditot érdemel, itt csak jelzésként szerepel.

## 6. Összegzés — mi hiányzik, prioritási sorrendben

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
   feladat, jól specifikált ezen az auditon (2. és 3. szakasz).
5. **Kozmetikai/kisebb tételek**: „Alkalmaz"/„Mégse" színes kör-ikonjai
   Unicode-karakter helyett; „Alaphelyzet" gomb teljes szélessége; a
   3 gyorsvágás élő fotó-bélyegképként (nem csak felirat); Alkalmaz-gomb
   tooltip szövege; „Sharpen"/„Vignette" hiányzó magyar fordítás; a
   „Kézi" arány-felirat dinamikus mérete.
6. **Nyitott kutatási igény**: ehhez az audithoz nem állt rendelkezésre
   képi bizonyíték a 2., 4. és 5. fül TARTALMÁRÓL (csak a fülcím-ikonokról
   és — a 4–5. fülnél — a korábbi #190-es exportkutatásból ismert
   kulcsnevekről). Egy következő screenshot-kör, amely mind az 5 fület
   megnyitva mutatja (különösen a 4–5. effekt-fül gombrácsát és a
   Finomhangolás csúszkáit), tovább pontosítaná ezt a dokumentumot.
