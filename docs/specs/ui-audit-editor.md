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

## 2.9 A szerkesztő bal panelje — a BINÁRISBÓL, képpontra (2026-08-15)

> 📐 **A TELJES, kötelező méretlista külön lapon:**
> [`szerkeszto-panel-meretek.md`](szerkeszto-panel-meretek.md) — mind a 201
> bal-paneles elem (plusz a szöveg-eszköz 55 eleme), fülönként és
> eszköz-panelenként, megvalósítási ellenőrzőlistával. Az alábbi szakasz a
> rövid összefoglaló és az eltérés-táblázat.

**Nem képernyőkép-mérés.** A `respack.yt` minden rétegrekordja 13 bájtos
fejléccel indul, és abban ott a téglalap (`int16 x0, y0, x1, y1` —
[`picasa-respack-format.md`](picasa-respack-format.md) 3. szakasz). Ez a
Picasa saját, beégetett elrendezése. Kinyerés:

```python
import sys; sys.path.insert(0, "tools/picasa"); import respack
adat = open("research/copy_Picasa_3_7/Picasa3/runtime/respack.yt", "rb").read()
for e in respack.read_index(adat):
    if not e.is_tre:
        r = respack.decode_layer(adat, e)   # r.x0, r.y0, r.x1, r.y1
```

### A panel váza

| elem | téglalap | méret |
|---|---|---|
| `editpanel/albumview` („Vissza a könyvtárhoz") | x 10..132, y **9..31** | 122 × 22 |
| `editpanel/tabs` (a fülsáv) | x 3..279, y **45..70** | 276 × **25** |
| `editpanel/edittabbase` · `editcontrols` · `fxthumbs` | x **3..279**, y 40..391 | **276** × 351 |
| `editpanel/tabpanel1` (az 1. fül lapja) | x 3..276, y 79..356 | 273 × 277 |
| `editpanel/insetleft` (a képnézet bal széle) | x **280**..800 | — |

**A bal panel tartalom-oszlopa tehát 276 képpont, a képnézet x = 280-nál
kezdődik.** Ez egybevág a `.tre` `LEFTDRAWEROFFSET` alapértékével (**279**,
`editpanel.tre` `toggle_left_drawer` és `insetleft`).

> A „Vissza a könyvtárhoz" gomb a felső **0–40 px**-es sávban ül, és
> **rajta kívül semmi más nincs ott**. A szerkesztőben az eredeti Picasa
> nem tart fenn alkalmazás-szintű eszköztárat.

### ÖT fül, amik pontosan kitöltik a panelt

| fül | x | szélesség |
|---|---|---|
| `tab1` | 3..58 | 55 |
| `tab2` | 58..113 | 55 |
| `tab3` | 113..169 | 56 |
| `tab4` | 169..224 | 55 |
| `tab5` | 224..279 | 55 |

**5 × 55 = 275 ≈ a 276 px-es sáv.** A fülek hézag nélkül, pontosan
kitöltik a panelt — a fülek száma tehát nem szabadon bővíthető: hatodik
fültől vagy a fülek zsugorodnak, vagy a panel szélesedik.

### Az 1. fül („Gyakori javítások") csempe-rácsa

Mind a nyolc eszközgomb **44 × 30 képpont**:

| sor | y | elemek (x = 37 · 118 · 198) |
|---|---|---|
| 1. | **91..121** | `crop` · `horizonadjust` · `redeye` |
| 2. | **155..186** | `enhance` · `autolighting` · `autocolor` |
| 3. | **223..253** | `retouch` · `edittext` · `picnik` |

- **oszlopköz: 81 px** (37 → 118 → 198)
- **sorköz: 64, illetve 68 px** (91 → 155 → 223)
- a felirat külön elem, a csempe ALATT (`m_buttonfontCbelow`,
  `YConstraint 0, 1, 0`)

### A Derítőfény-sor

| elem | téglalap | méret |
|---|---|---|
| `filllight_icon` | x 37..81, y **290..320** | 44 × 30 |
| `filllightlabel` | x 94..235, y **283..297** | 141 × 14 |
| `backlight_container` (a csúszka) | x 101..228, y **294..321** | **127** × 27 |

A kis kép **ugyanakkora, mint egy eszközcsempe** (44 × 30), és a
csempe-rács első oszlopával **azonos x-en** áll (37). A felirat és a csúszka
tőle jobbra, egymás alatt.

### Visszavonás / Újra

`filter_undo` x 7..139, `filter_redo` x 144..276, mindkettő y **361..389** —
**132 × 28** képpont, 5 px hézaggal, a panel teljes szélességét kitöltve.

### Keresztellenőrzés: a 3–5. fül rácsa

A bináris ugyanazt adja, amit a 3.2 szakasz képernyőképből mért:
`fxlabel1..12` x = 9 / 97 / 185 (**szélesség 86, osztásköz 88**),
y = 158 / 229 / 300 / 371 (**osztásköz 71**). A két, egymástól független
módszer **betűre egyezik** — a 3.2 mérés ezzel megerősítve.

*Bizonyítottsági fok: megerősített* (a bináris erőforráscsomag
rétegtéglalapjai).

### Eltérés a PicasaPy-tól — a bal sáv „szétesésének" okai

**Állapot: a #741 javítása után.** A „MOST" oszlop értékei a KIRAJZOLT
fából mértek (`tests/app/qml_functional/test_editor_panel_geometry_741.py`),
nem a forrásból olvasottak.

| # | jellemző | eredeti (bináris) | #741 ELŐTT | MOST | hol |
|---|---|---|---|---|---|
| 1 | **fülek száma** | **5** | 7 | **7 — tudatos kivétel**, `39·39·40·39·40·39·40 = 276` | `EditorTabBar.qml` |
| 2 | tartalom-oszlop | **276** | 260 | **276** | `EditorPanel.qml` (`tabBar`, `tabArea` margói) |
| 3 | fülsáv magassága | **25** | 38 | **25** | `EditTabButton.qml` |
| 4 | fülikon magassága | **16–19** | 22 | **18** | `EditTabButton.qml` |
| 5 | **eszközcsempe sorköze** | **64** | **104** (94 + 10) | **64** | `ToolTile.qml`, `EditorTabCommonFixes.qml` |
| 6 | csempe-kép mérete | **44 × 30** | 54 × 36 | **44 × 30** | `ToolTile.qml` |
| 7 | csempe-oszlopköz | **81** | 88 | **81** (cella 80 + 1 térköz) | `EditorTabCommonFixes.qml` |
| 8 | Derítőfény kis képe | **44 × 30**, x 37 | 54 × 36, a rácstól elcsúszva | **44 × 30**, a rács 1. oszlopával egy vonalban | `EditorTabCommonFixes.qml` |
| 9 | Derítőfény-csúszka | **127 × 27** | 200 × 14 | **127 × 27** | `EditorTabCommonFixes.qml` |
| 10 | Visszavonás / Újra | **132 × 28**, 5 px hézag | 127 × 24, 6 px | **132 × 28**, 5 px | `EditorPanel.qml` |
| 11 | Finomhangolás csúszkái | **191 × 27**, ~53 osztásköz | 230–260 × 14, 42 | **191 × 27**, ~55 | `EditorFinetunePanel.qml` |
| 12 | párban álló gombok | **98 × 28** | 127–151 × 24 | **98 × 28** | crop · redeye · szöveg panel |
| 13 | retusálás gombjai | **118 × 28** | 82–127 × 24 | **118 × 28** | `EditorRetouchPanel.qml` |
| 14 | legördülők magassága | **21** | 22 / 24 / 30 | **21** | crop · szöveg panel |
| 15 | felső sáv a szerkesztőben | **nincs** (csak a 122 × 22-es „Vissza a könyvtárhoz") | a `MainToolbar` végig látszik | **NYITVA** | `Main.qml` `header: MainToolbar` |

**A függőleges nyúlás fő oka az 5. sor volt:** három csempesor × 40 px
többlet ≈ **120 képpont**, amit a panel aljáról vett el — ezért csúszott
szét a Derítőfény-sor és a gombok.

A 3–5. effekt-fül rácsa ezzel szemben **már a #741 előtt is jó volt**
(`EditorEffectsTab1.qml`, `columnSpacing: 2`, `rowSpacing: 2`, csempe 86 —
a #704-ben a mért értékekre állítva). A 276-ra bővült tartalom-oszlop miatt
a fülek margója igazodott (bal 5, jobb 9), hogy a rács továbbra is **88
képpontos osztásközzel** álljon.

> ⚠️ **A 15. sor NYITVA marad.** A felső sáv elrejtése a `Main.qml`-t
> érinti, ami a #741 munkájából ki volt zárva — külön körben kell
> elvégezni.

#### A Visszavonás/Újra sor függőleges helye — TUDATOS eltérés

A bináris szerint a gombsor a panel **aljához** van kötve. Ez az eredetire
igaz, ahol a panel FIX méretű: ott „a panel alja" és „a tartalom alatt"
ugyanaz a hely. Nálunk a panel NYÚLIK, és a #616 pontosan azt javította,
hogy 1920 × 1080-as ablakban a 832 képpont magas panel alján a gombok több
száz képponttal a tartalom alatt, egy üres mező túloldalán ültek. A #741
ezért a gombok **méretét** (132 × 28) és a **hézagot** (5 px) veszi át, a
függőleges helyet nem: a sor a tartalom alja + kis rés, de sosem lejjebb a
látható terület aljánál (`EditorPanel.qml`, `globalUndoRow.y`).

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

### 4.x Kicsomagolt bitkép-mérések (#700)

A #700 megvalósítási köre a `respack.py`-vel **ki is csomagolta** az érintett
rétegeket; három számszerű adat innen való, és egy korábbi állítást helyesbít:

| réteg | kép | mért adat |
|---|---|---|
| `editpanel/ok_icon` | tömör kör, fehér pipa | domináns szín **`#4E904A`** (zöld) |
| `editpanel/cancel_icon` | tömör kör, fehér X | domináns szín **`#524BA1`** (**indigó**) |
| `editslider/sliderbase` | 191x27 | a vájat a 8.-16. képpontsorban fut -> **9 képpont magas sín** |
| `editslider/thumb` | **16x26** | **álló, magas téglalap** fogantyú (nem kör) |

FIGYELEM - **helyesbítés:** a dokumentum máshol "sötétvörös X-ikon"-t ír - az
képernyőképről olvasott benyomás. A kicsomagolt bitkép szerint **indigó**, és
ugyanaz a két kép szolgálja ki a vágás-panelt is.

Összehasonlításul a felület MÁSIK csúszka-sablonja (nagyítás, derítőfény,
retusáló ecset - `scaleslider`): sín 121x9, fogantyú 16x22. A paraméter-alpanel
csúszkája tehát **szándékosan más arányú**, nem a közös vezérlő.

### 4.y A csúszka-FELIRAT honnan jön — LEZÁRVA (2026-08-15)

A #700 nyitva hagyta, hogy a Holga első csúszkája „Méret" vagy
„Élhomályosítás": a `filterdesc.xml` azonosítója `_sldrBlur`, a szótár
`ImageFilters::Blur`-je „Size"/**Méret**, a bejelentő képernyőképén viszont
**Élhomályosítás** áll.

**Mindkettő igaz.** A feliratot nem az azonosító önmagában dönti el: a
`Picasa3.exe` `FUN_008fcfa0` (VA `0x008fcfa0`) **négy csúszkánál a szűrő
azonosítójára is elágazik**, és felülírja az alapértelmezést —
`Holga`/`Lomo` → *Blur Edges*, `Pixelate` → *Pixel Size*, `HDR` és
`PencilSketch` → *Strength*, `FocalZoom` → *Zoominess* / *Focal Size*,
`Soften` → *Softness*, `Boost` → *Strength*.

A teljes tábla, a dekompilált bizonyíték és a Picasa saját elvarratlan szála
(`FocalPixelate` vs. `PicnikFocalPixelate`):
`docs/specs/picasa-effekt-feliratok.md` „Szűrőnkénti felülírás" szakasza.
A PicasaPy oldalán az `app/effect_params.py` és a
`tests/app/test_effect_param_labels_600.py` vezeti át.

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
| ~~N5~~ | ~~A rács **görgethető-e** 12 csempénél többnél~~ → **LEZÁRVA (2026-08-16)**: nem görgethető, és a `picnik_fx` nem rács-bővítő, hanem a megszűnt **Picnik** online szerkesztő indítógombja — lásd „A `picnik_fx` a megszűnt Picnik gombja" alább | megerősített | — |

### Amit a #704 ebből megvalósított, és hol tér el TUDATOSAN

| Jellemző | Eredeti (mért) | PicasaPy a #704 után | Megjegyzés |
|---|---|---|---|
| Szekciófejléc | nincs | **nincs** | a 22 px-es „Effektek" / „Kreatív" / „Művészi" / „További effektek" / „Régi effektek" sáv törölve mind az öt fülről |
| Rács | 3 × 4 = 12 | 3 oszlop, fülenként 12 csempe | a `Vignette` a #704 óta az 5. fülön (a #422 tévesen a gyűjtőfülre tette) |
| Térköz | 2 px | **2 px** | korábban 6 |
| Bélyegkép | 78 × 48 | doboz-magasság **48** (szélesség a rácsból) | korábban 56 |
| Csempe | 86 × 69 | ~86 széles, **~90 magas** | ⚠️ TUDATOS ELTÉRÉS: a felirat nálunk KÉT sort foglal (`PanelButton.qml`), amit a **#422** kért kifejezetten — a hosszabb nevek nem vágódhatnak, és a rács sorai nem csúszhatnak szét. Az eredeti egysoros, 18 px-es feliratsávjához visszatérni csak a #422 visszavonásával lehetne; az külön döntés |
| Felirat | 11 px, félkövér, középre zárt, #333333 | félkövér, középre zárt, `Theme.textDark` | a fix #333333 helyett témafüggő token, hogy sötét témában is olvasható legyen |
| Jelvény helye / mérete / színe / alakja | bélyegkép jobb alsó sarka, 13 × 12, #379FFD, negyed-korong | **ugyanaz** | a `PanelButton.qml` `appliedCount` tulajdonsága vezérli; a kék ma fix hexa a komponensben — `Theme.badgeBlue` néven a témába való (integrációs igény) |
| Jelvény **száma** | ~~jelentése NYITOTT (N1)~~ → **NINCS SZÁMA** (2026-08-16, lásd „A jelvényen nincs szám" alább) | a szűrő előfordulásainak száma a láncban (`EditController.effectChainCounts`) | ❌ **ELTÉRÉS**: az eredetiben a jelvény néma grafika, csak látszik vagy nem. A számot mi tettük rá |

Az őrök: `tests/app/qml_functional/test_effect_tile_grid_704.py` (fejléc,
jelvény-geometria, csempeszám, egységes feliratszín).

**Amit a #704 NEM oldott meg:** a bejelentésben szereplő „kék és narancs
csempe-feliratok". A kódban egyetlen feliratszín van (`PanelButton.qml`,
`Theme.textDark`, tiltottnál `Theme.textGray`); effektenkénti szín sehol
nincs, tehát a jelenség a mai forrásból nem állítható elő. A legvalószínűbb
magyarázat, hogy a megfigyelés a színezett effekt-ELŐNÉZETEKRE vonatkozott
(a Szépia melegbarna, a Színezés kék bélyegképe). Ha a jelenség tényleg a
feliratokon van, új képernyőkép kell hozzá.

## A Vörösszem-panel (Redeye Repair) — teljes felépítés (2026-08-15, #371)

Forrás: a tulajdonos képernyőképe (angol felület), `editpanel.tre`,
`editpaneltext.tre` és a `stringres-en-hu.tsv` magyar fordításai.

### Elrendezés

A panel a **1. fül** (Gyakori javítások) alpanelje, gyökere
`editpanel/redeye_well`. Elemei:

| elem | szerep |
|---|---|
| `redeye_icon2` + `redeye_label` | szem-ikon + cím: **„Redeye Repair"** |
| `redeyetext` | állapotfüggő magyarázó szöveg (ld. lent) |
| `redeyeauto` | **Auto** — „Reapply auto redeye corrections" |
| `redeyepreview` | **Preview** — „Preview changes without square outlines" |
| `redeyediscard` | **Reset** — „Undo Red-Eye changes" |
| `redeyeapply` | **Apply** (zöld pipa) — „Apply effect and exit Red-Eye repair" |
| `redeyecancel` | **Cancel** (piros X) — „Exit Red-Eye repair without applying effect" |

A képernyőképen az **Auto letiltott** (szürke), mert az automatikus javítás
épp lefutott — újra-alkalmazni nincs mit. A gombsor kiosztása:
`Auto | Preview` egy sorban, alatta középen `Reset`, legalul
`Apply | Cancel`.

### A detektálás jelölése a képen

A felismert szemek körül **négyzetes keret** jelenik meg a nagy előnézeten.
A képernyőképen két keret látszik, eltérő állapotban (az egyik zöld, a másik
halvány) — a **Preview** gomb súgója szerint a keretek elrejthetők
(„Preview changes without square outlines"), tehát a keret **szerkesztési
segédlet**, nem a kimenet része.

### Három állapotüzenet, nem egy

A `redeyetext` tartalma a helyzettől függ (erőforrás-kulcsokkal):

| kulcs | mikor | magyar szöveg (rövidítve) |
|---|---|---|
| `RedEye::AutoFixedMessage` | az automatika **talált** javítanivalót | „A Picasa vörösszem-effektusokat talált a képen, és kijavította őket." |
| `RedEye::DragToSelectMessage` | nincs automatikus találat | „Az egérgomb nyomva tartásával külön-külön jelölje ki a szemeket…" |
| `RedEye::AutoFixRedoMessage` | Reset után | ugyanaz + „Az »Automatikus« gombra kattintva ismételten alkalmazhatja…" |

Mindháromban ott a kulcsmondat: **a keretbe kattintva visszavonható az adott
változás** — tehát a keretek a szerkesztés alatt **egyedileg törölhetők**.

### ⚠️ Ez oldja fel a látszólagos ellentmondást a tárolással

A [`picasa-ini-format.md`](picasa-ini-format.md) bizonyítja, hogy a
vörösszem-foltok koordinátái **sehol nem őrződnek meg** (sem az ini-ben, sem
a `db3` 36 oszlopában), és hogy a javítás a mentett képbe van égetve.

A panel viszont **keretekkel dolgozik** — tehát a koordináták a **szerkesztési
munkamenet alatt léteznek**, csak az `Apply` után eldobódnak.

**A Picasa saját szövegei ezt ki is mondják:**

- `IDS_CONFIRM_UNDO_REDEYE` — „A vörösszemjavítások **nem állíthatók helyre**
  ismételt alkalmazással. Biztosan visszavonja a műveletet?"
- `IDS_CONFIRM_REDEYE_REVERT` — „…Ha eltávolít minden szerkesztést, a
  vörösszemjavításokat **később nem lehet újra alkalmazni**."
- `IDS_UNABLETOREDEYEREADVOLUME` — „**Írásvédett meghajtókon** található
  képeken nem lehet vörösszem-eltávolítást végezni." (Mert a művelethez
  **írni kell a képet** — ez önmagában is a beleégetést bizonyítja.)

*Bizonyítottsági fok: megerősített*, három egymástól független forrásból:
pixelösszevetés, a tárolók kimerítő átvizsgálása, és a Picasa saját
figyelmeztető szövegei.

### Egy interakciós buktató, amit dokumentálni kell

`IDS_WARN_REDEYE_ACCURACY`: ha a képet a **Kiegyenesítés** eszköz elforgatta,
a vörösszem-keretek kijelölése pontatlan lehet. A Picasa ilyenkor azt
javasolja, hogy a felhasználó vonja vissza a kiegyenesítést, végezze el a
vörösszem-javítást, majd egyenesítsen újra. Ez **sorrendfüggőség** a láncban —
a PicasaPy-nak legalább ismernie kell.

## Az effekt-csempék TÁBLÁJA a binárisból (`0x00c7e5a0`, 2026-08-16)

A három effekt-fül rácsa eddig **képernyőképekből** volt kiolvasva. Most
megvan a **forrásadat**: egy 36 rekordos tábla a `.rdata`-ban, amit a
`editpanel/fx%d` / `editpanel/fxlabel%d` felületkód olvas
(`0x005d7c20`, a `[esi+esi+0xc7e5a0]` indexeléssel — 12 bájtos rekordok).

```
struct FxTile {         // 12 bájt
    const char *token;   // +0  az elsődleges filters= kulcs
    const char *token2;  // +4  a MÁSODIK kulcs (mód/jelölőnégyzet), vagy 0
    uint32_t    _0;      // +8  mindig 0
};
```

**36 rekord = 3 fül × 12 csempe** — pontosan az `editpanel.tre`
`fx1`…`fx12` csempehelyeivel egyezik.

### 3. fül (rekord 1–12)

| # | token | 2. token | magyar UI-név |
|---:|---|---|---|
| 1 | `unsharp2` | `unsharp` | Élesítés |
| 2 | `sepia` | — | Szépia |
| 3 | `bw` | — | Fekete-fehér |
| 4 | `warm` | — | Melegítés |
| 5 | `PicnikGrain` | `grain` | Filmszemcse |
| 6 | `PicnikTint` | `tint` | Árnyalás |
| 7 | `sat` | — | Telítettség |
| 8 | `radblur` | — | Lágy fókusz |
| 9 | `glow2` | `glow` | Ragyogás |
| 10 | `ansel` | — | Szűrt FF |
| 11 | `radsat` | — | Fókuszos FF |
| 12 | `dir_tint` | `radtint` | Színátmenet |

### 4. fül (rekord 13–24)

`IR` · `Lomo` · `Holga` · `HDR` · `Cinemascope` · `Orton` · `Sixties` ·
`Invert` · **`HeatMap`** (2. token: `NightVision`) · `CrossProcess` ·
`QuantizePalette` · `TwoTone`

### 5. fül (rekord 25–36)

`Boost` · `Soften` · **`Vignette`** (2. token: `Matte`) · **`Pixelate`**
(2. token: `PicnikFocalPixelate`) · `FocalZoom` · `PencilSketch` · `Neon` ·
`Comicize` · **`Border`** (2. token: `RoundedEdges`) · `DropShadow` ·
`MuseumMatte` · `Polaroid`

### ✅ A képernyőképes audit MINDHÁROM fülön betűre igazolódott

A fenti sorrend **független forrásból** ugyanaz, mint amit a 2026-07-17-i
képernyőképekből olvastunk ki — beleértve a 2026-08-15-i helyesbítést is,
hogy a **`Vignette` az 5. fül 3. eleme**, nem a 3. fülé. A tábla 27.
rekordja pontosan ott áll.

Ez az audit legjobban alátámasztott állítása: **kép + `.tre` + bináris
tábla, három egymástól független forrás.**

### 🔑 A MÁSODIK token megfejti a „dekódolatlan" szűrőneveket

Kilenc csempének van második tokenje. Mindegyik pár **ugyanannak a
csempének a másik üzemmódja** (jelölőnégyzet vagy választó), nem külön
effekt:

| csempe | alap token | 2. token | mit kapcsol |
|---|---|---|---|
| Élesítés | `unsharp2` | `unsharp` | régi/új változat |
| Filmszemcse | `PicnikGrain` | `grain` | régi/új változat |
| Árnyalás | `PicnikTint` | `tint` | régi/új változat |
| Ragyogás | `glow2` | `glow` | régi/új változat |
| Színátmenet | `dir_tint` | `radtint` | **lineáris ↔ sugaras** |
| Hőtérkép | `HeatMap` | **`NightVision`** | színpaletta-választó |
| Vignetta | `Vignette` | **`Matte`** | keret üzemmódja |
| Képpontnagyítás | `Pixelate` | `PicnikFocalPixelate` | teljes ↔ fókuszos |
| Szegély | `Border` | **`RoundedEdges`** | sarok lekerekítése |

**Ez zárja le a `picasa-ini-format.md` „dekódolatlan" jelölését a
`RoundedEdges`, a `Matte` és a `NightVision` tokenre**: nem önálló,
ismeretlen szűrők, hanem egy meglévő csempe másik üzemmódja.

A `dir_tint` ↔ `radtint` pár független megerősítést is kap: a natív
szűrő-táblában (`picasa-native-filter-registry.md`) **mindkettőnek saját
kezelője** van (`0x008f9880`, illetve `0x008f8730`), de **ugyanaz a
paraméter-értelmezője** (`0x008f9bf0`) — vagyis tényleg egy csempe két
üzemmódja.

*Bizonyítottsági fok:* **megerősített** a tábla tartalmára és sorrendjére
(nyers `.rdata`, minden rekordhoz cím; három forrás egyezik) · **erős** a
második token „üzemmód" értelmezésére (mind a kilenc pár illeszkedik, és a
`dir_tint`/`radtint` külön is igazolja).

### A második tokent a SHIFT billentyű kapcsolja (2026-08-16)

Az előző szakasz nyitva hagyta, **melyik vezérlő** kapcsolja a csempe
második tokenjét. A válasz: **egyik sem — a Shift billentyű.**

```asm
0x005d7c86  call    0xa67be0
0x005d7c91  push    0x10                 ; VK_SHIFT
0x005d7ca3  call    dword ptr [0xc406f8] ; USER32!GetAsyncKeyState
0x005d7cbb  shr     eax, 0xf
0x005d7cbe  and     al, 1
0x005d7cc0  mov     byte ptr [ecx + 0x33a8], al   ; a panel „shift" jelzője
```

és a csempe-kirakó ezt olvassa:

```asm
0x005d7d63  cmp     byte ptr [ebx + 0x33a8], 0
0x005d7d6a  je      0x5d7e07             ; nincs shift → marad az alap token
0x005d7d70  mov     esi, dword ptr [esi + 0xc7e5a4]   ; a rekord +4 mezője
0x005d7d76  test    esi, esi
0x005d7d78  je      0x5d7e07             ; nincs 2. token → marad az alap
                                          ; különben a 2. token lép a helyére
```

A `0x00c406f8` import feloldva: **`USER32.dll!GetAsyncKeyState`**, az
argumentum `0x10` = **`VK_SHIFT`**.

#### Újrarajzolás billentyűváltásra

Az effekt-panel figyeli a billentyű állapotát, és **csak változáskor**
rajzol újra:

```asm
0x005e6754  push    0x10                 ; VK_SHIFT
0x005e6756  call    dword ptr [0xc406f8]
0x005e675c  shr     eax, 0xf
0x005e675f  and     al, 1
0x005e6761  cmp     byte ptr [edi + 0x33a8], al
0x005e6767  je      0x5e6776             ; nem változott → nincs teendő
0x005e6771  call    0x5d7c20             ; a csempe-rács újrarajzolása
```

#### Amit ez jelent

**A Shift lenyomva tartása mind a kilenc kétmódú csempét egyszerre
átváltja** a másodlagos effektjére — nem csempénkénti jelölőnégyzet, hanem
**egyetlen, globális billentyű-módosító**:

| csempe | Shift nélkül | Shifttel |
|---|---|---|
| Élesítés | `unsharp2` | `unsharp` |
| Filmszemcse | `PicnikGrain` | `grain` |
| Árnyalás | `PicnikTint` | `tint` |
| Ragyogás | `glow2` | `glow` |
| Színátmenet | `dir_tint` | `radtint` |
| Hőtérkép | `HeatMap` | `NightVision` |
| Vignetta | `Vignette` | `Matte` |
| Képpontnagyítás | `Pixelate` | `PicnikFocalPixelate` |
| Szegély | `Border` | `RoundedEdges` |

A csempe **felirata és bélyegképe is** ehhez igazodik: az erőforrás-nevet a
`_mod%s` utótaggal képzi (`0x005d7df4`).

> **Helyesbítés az előző szakaszhoz.** Ott „jelölőnégyzet vagy választó"
> szerepelt a második token kapcsolójaként. **Ez téves volt** — a
> visszafejtés szerint egyetlen, panelszintű `GetAsyncKeyState(VK_SHIFT)`
> vizsgálat kapcsolja mind a kilencet. A tévedést a `0x33a8` eltolás
> írás/olvasás helyeinek végigkeresése döntötte el (a teljes `.text`-ben
> **három** hivatkozás van rá, mindhárom itt).

*Bizonyítottsági fok: megerősített* (import feloldva, mindkét oldal
— beállítás és olvasás — kiolvasva, címekkel).

### A kilenc Shift-változat TELJES paraméterlistája (2026-08-16)

Az előző kör „nyitva" hagyta négy Shift-változat csúszkáit. **Fölöslegesen:**
mind a négy megvan a `filterdesc-registry.md` 4. pontjában. Ez a szakasz a
kilenc párt **egymás mellé** teszi, hogy a paraméterpanel egy helyről
építhető legyen.

| # | csempe | alap változat + paraméterei | **Shift-változat + paraméterei** |
|---:|---|---|---|
| 1 | Élesítés | `unsharp2` — Mennyiség | **`unsharp`** — Mennyiség (fix 1,5-ös sugár) |
| 2 | Filmszemcse | `PicnikGrain` — Grain 0–50 (10), Világosítás jelölő (ki) | **`grain`** — **nincs csúszkája** |
| 3 | Árnyalás | `PicnikTint` — szín (#80cfff), Fade 0–100 (0) + festhető maszk | **`tint`** — Színek megőrzése |
| 4 | Ragyogás | `glow2` — Intenzitás, Sugár | **`glow`** — Intenzitás, Sugár |
| 5 | Színátmenet | `dir_tint` | **`radtint`** — Lágy perem |
| 6 | Hőtérkép | `HeatMap` — Hue −180–180 (0), Fade 0–100 (0) | **`NightVision`** — Fényerő −50–50 (0), Kontraszt −50–50 (0), Fade 0–100 (0) |
| 7 | Vignetta | `Vignette` — Blur 0–50 (**35**), Strength 1–2 (**1,4**), szín (**#000**), Fade 0–100 (0) | **`Matte`** — Blur 0–50 (**40**), Strength 1–2 (**1,2**), szín (**#fff**), Fade 0–100 (0) |
| 8 | Képpontnagyítás | `Pixelate` — Impact 2–150 (20), BlendMode 0–9 (9), Fade 0–100 (0) | **`PicnikFocalPixelate`** — Impact 2–100 (20), Radius 10–min(W,H)/2 (közép), Hardness 0–100 (50), Fade 0–100 (0), Fordított jelölő (ki) |
| 9 | Szegély | `Border` — szín Outer (#000), OuterThickness 0–100 (20), szín Inner (#fff), InnerThickness 0–100 (5), CornerRadius 0–min(W,H)/2 (0), CaptionHeight 0–H/6 (0) | **`RoundedEdges`** — szín Outer (**#fff**), CornerRadius 0–min(W,H)/2 (**min(W,H)/10**) |

### Három szerkezeti tanulság

**1. A `Vignette` és a `Matte` paraméterei BETŰRE azonos szerkezetűek** —
négy mező ugyanabban a sorrendben, csak az alapértékek térnek el, és a szín
fekete ↔ fehér. A `filterdesc-registry.md` 316. sora is ezt mondja: ugyanaz
a művelet (`GlowImageOperation`). A Shift tehát itt **a sötétítést
világosításra váltja**.

**2. A Shift-változat NEM feltétlenül szegényebb.** A `NightVision` három
csúszkát kap a `HeatMap` kettő helyett, a `PicnikFocalPixelate` ötöt a
`Pixelate` háromja helyett. A paraméterpanelt tehát **újra kell építeni**
váltáskor, nem elég átcímkézni.

**3. A `RoundedEdges` a `Border` szűkített változata** — hat mező helyett
kettő (külső szín + saroksugár), és a saroksugár alapértéke **nem nulla**
(`min(W,H)/10`), szemben a `Border` nulla alapértékével.

### Módszertani megjegyzés

Ez a kör azért indult, mert az előző „nyitva" jelölést tett oda, ahol a
válasz **egy másik spec-lapon** már megvolt. A `00-index.md` pont ezért
készült — de az összekapcsolás csak akkor működik, ha a kör **átnézi a
rokon lapot**, mielőtt nyitottnak jelöl valamit.

*Bizonyítottsági fok: megerősített* (a `filterdesc.xml` a Picasa saját
szűrő-regisztere; a nevek a `*text.tre` szövegforrásból).

### A jelvényen NINCS szám (2026-08-16) — az N1 lezárva

A csempe „alkalmazva" jelvényének (`editpanel/fx%d_adorn`) jelentése eddig
nyitott volt (N1). **Két, egymástól független forrás zárja le.**

#### 1. Az elrendezés-erőforrás: a jelvény néma

`macros.tre` (a `#define m_fxadorner` blokk) a teljes definíció:

```
#define m_fxadorner
XConstraint 1, 1, -6
YConstraint 1, 1, -19
```

**Két megkötés, semmi más.** Nincs benne szövegkötés, nincs betűtípus,
nincs tartalom-tulajdonság — pusztán elhelyezés a szülő csempe **jobb
széléhez −6**, illetve **alsó széléhez −19** képponttal. Egy ilyen elem
nem tud számot mutatni.

#### 2. A felületkód: csak megmutatja vagy elrejti

`0x005d7c20`, a csempe-kirakó:

```asm
0x005d7eb9  mov   edx, dword ptr [eax + 0x14]   ; vtbl[5]
0x005d7ebc  call  edx                            ; állapot lekérdezése
0x005d7ec2  cmp   eax, 1
0x005d7eca  sete  byte ptr [esp + 0x64]          ; látszik-e a jelvény
...
0x005d80d4  push  0xc96304                       ; "editpanel/fx%d_adorn"
0x005d8108  cmp   byte ptr [esp + 0x64], 0
0x005d8111  mov   eax, dword ptr [edx + 0x6c]    ; vtbl[27]  (megmutat)
0x005d8116  mov   eax, dword ptr [edx + 0x68]    ; vtbl[26]  (elrejt)
0x005d8119  call  eax
```

A jelvényen **egyetlen művelet** történik: megmutatás vagy elrejtés. Semmi
nem ír bele értéket.

> A `vtbl[6]` (`[eax+0x18]`), amit közvetlenül utána hív, **sztringet** ad
> vissza (a visszatérés `strlen`-nel és sztring-értékadással megy tovább,
> `0x005d7ee0`–`0x005d7ef2`) — tehát az sem szám.

#### A feltétel: `állapot == 1`

A jelvény akkor látszik, ha a `vtbl[5]()` **pontosan 1-et** ad vissza.
Ez állapotkód, nem darabszám: `0` = nincs alkalmazva, `1` = alkalmazva.

#### ❌ Amiben eltérünk

| | eredeti Picasa | PicasaPy ma |
|---|---|---|
| a jelvény tartalma | **néma grafika** | **szám** (`appliedCount.toString()`, `PanelButton.qml:227`) |
| mikor látszik | `állapot == 1` | `appliedCount > 0` |
| igazítás | a **csempéhez**: jobb −6, alsó −19 | a **bélyegkép-dobozhoz**, margó nélkül |

A szám a mi hozzátételünk volt — a `#704` „ideiglenes olvasat"-ként jelölte
is. Most bizonyított, hogy az eredetiben nincs ott.

*Bizonyítottsági fok: megerősített* (a `macros.tre` teljes makródefiníciója
és a felületkód mindkét ága kiolvasva).

### A `picnik_fx` a megszűnt Picnik gombja — az N5 lezárva (2026-08-16)

Az N5 azt kérdezte, görgethető-e az effekt-rács 12 csempénél többnél, és
mi az a `picnik_fx` gomb a rács alján. **Mindkettőre megvan a válasz.**

#### A gomb definíciója (`editpanel.tre` 412–426)

```
#--Picnik fx button
editpanel/picnik_fx_label: editpanel/picnik_fx
Property textalign right
XConstraint 1, 0, -5
YConstraint 0.5, 0.5, 0
m_hidden
editpanel/picnik_fx_icon: editpanel/picnik_fx
XConstraint 0, 0, 10
YConstraint 0.5, 0.5, 0
m_hidden
editpanel/picnik_fx: editpanel/fxthumbs
m_buttontypecolor
XConstraint 0.5, 0.5, 0
m_offsetT
m_hidden
```

Vízszintesen **középre igazított**, színes típusú gomb, bal oldalt ikonnal
(+10), jobbra zárt felirattal (−5). Mindhárom elem **`m_hidden`**.

#### A felirata megmondja, mi ez

```
filter_picnik_label0   Creative Kit   Kreatív készlet
```

A **Picnik** a Google online fotószerkesztője volt; a Picasa
„Kreatív készlet" gombja oda töltötte fel a képet. A bináris tele van a
kiszolgáló-oldali maradványaival: `picnikurl`,
`http://www.picnik.com/service/`, `picnikdoneurl`, `Picnik::UploadProgress`,
`Picnik::UploadError`, `Picnik::SaveToPicasa`, `PicnikWarn`,
`editpanel/picnikwin`, `editpanel/picnikapply`, `editpanel/picnikcancel`,
`runtime\picnik_effects\`.

> A **Picnik 2012-ben megszűnt.** A gomb tehát halott funkció maradványa.

#### Egy árulkodó nyom: a szabály KI VAN KOMMENTEZVE

Az `editpanel.tre` 290. sora:

```
#Property hidetarget editpanel/picnik_fx
```

A `#` miatt ez **nem hatályos**. A fejlesztők tehát a gomb kezelését a
kiadás előtt kivették — összhangban azzal, hogy a szolgáltatás megszűnt.

#### A két válasz

1. **A rács NEM görgethető.** Fülenként pontosan `fx1`…`fx12` van, és
   tizenharmadik csempehely nincs definiálva.
2. **A `picnik_fx` nem rács-bővítő**, hanem egy külső, ma már nem létező
   szolgáltatás indítógombja.

#### Amit ebből a PicasaPy csinál: SEMMIT

A gombnak nincs értelmes megfelelője — a mögötte álló szolgáltatás nem
létezik. A rács alján **nem kell** gomb.

*Bizonyítottsági fok: megerősített* (az elrendezés-erőforrás teljes blokkja,
a felirat szövegforrása, és a bináris tizennégy Picnik-hivatkozása).
