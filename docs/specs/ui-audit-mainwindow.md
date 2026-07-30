# UI-audit — főablak (mappafa, eszköztár, tálca, görgetősáv, arányok)

**Dátum:** 2026-07-30
**Forrás (eredeti):** a felhasználó Picasa 3.9 magyar felületéről készült
screenshotjai, `research/testdata/screenshot/` alá tartozó gépen —
ebben az auditban a
`Képernyőkép 2026-07-18 144904/145027/145113/145523/150933.png` (fő
könyvtárnézet) és `…195038/195048/195059/195131.png` (szerkesztő-nézet,
csak a felső sáv és a tálca-minta miatt releváns) képeket használtam.
**Forrás (jelenlegi):** `src/picasapy/app/qml/PicasaPy/FolderPane.qml`,
`FolderTreeItem.qml`, `MainToolbar.qml`, `TrayBar.qml`,
`PicasaScrollBar.qml`, `LightboxFeed.qml`, `Main.qml` (csak olvasva —
más session épp ezeket írja, ez az audit NEM módosítja őket).
**Kapcsolódó dokumentum:** `docs/specs/design-guide.md` (a 2026-07-18-as
„Ismert hűség-hiányok" listája részben fedi az itt talált eltéréseket —
lásd az egyes szakaszok végén a kereszthivatkozást).

Módszer: a screenshotokból pixel-szintű kivágásokat és
színmintavételt is végeztem (`PIL`/Python), nem csak szemrevételezést —
a px-értékek ez alapján mérésekből, nem becslésből származnak.

---

## 1. Mappafa (bal oldali panel szerkezete) — A LEGFONTOSABB PONT

### 1.1 Eredeti (Picasa 3.9) — megerősített szerkezet

A `Képernyőkép 2026-07-18 145523.png` (Emberek-nézet, teljes fa látszik)
és a `…150933.png` (keresési nézet, több éves mappalista) képek együtt
egyértelműen igazolják a felhasználó leírását:

```
Albumok (1)                      ◀ gyűjtemény-fejléc (▼/▶ gomb)
  Legutóbb frissítve (1)         ◀ speciális/rendszer-album, mappaikon nélkül
Emberek (1)                      ◀ gyűjtemény-fejléc
  Keresés, 5% kész               ◀ arc-keresés folyamatban lévő "album"
Projektek (1)                    ◀ gyűjtemény-fejléc
  Képernyőfelvételek (1)
Mappák (25)                      ◀ gyűjtemény-fejléc (itt épp összecsukva: ▶)
Egyebek (1)                      ◀ gyűjtemény-fejléc
  tmp (4)
```

- **Gyűjtemény-szint** (Albumok / Emberek / Projektek / Mappák / Egyebek):
  önálló sáv, halvány szürke-bézs színátmenetes háttér (kb. `#e1e4e7` →
  `#eef0f2`), **félkövér** felirat + `(n)` darabszám, bal szélén egy
  **színes háromszög-gomb**: zöld ▼ = kinyitva, piros ▶ = összecsukva
  (ez valódi kattintható állapot, nem statikus ikon). Keresés-szűrt
  nézetben (150933.png) a háromszög helyén nagyító-ikon jelenik meg —
  jelezve, hogy a lista épp szűrt találatokat mutat.
  A felhasználó leírása pontos: **öt előre definiált gyűjtemény**
  (Albumok, Emberek, Projektek, Mappák, Egyebek), a Mappák az „alap"
  — ez az egyetlen, ami ÉVSZÁM szerint tagolt (a többi lapos lista).
  A felhasználó saját gyűjteményt is létrehozhat (ezt screenshoton nem
  sikerült megerősíteni, csak a dokumentált felhasználói leírásból tudjuk).
- **Évszám-elválasztó** (kizárólag a Mappák gyűjteményen belül, ha a
  mappák több évet fednek le): sima szürke szöveg (kb. `#7a776f`),
  **nincs mappaikon, nincs saját behúzás** — balra majdnem a gyűjtemény-
  fejléccel egy magasságban kezdődik —, és **jobb oldalán vékony
  vízszintes elválasztó-vonal fut a panel jobb szegélyéig** (lásd
  `150933_panel.png`: „2024 ────────", „2011 ────────" stb.). A mappák
  új évhez akkor kerülnek, ha a mappa dátuma (alapból a legrégebbi
  fotója) abba az évbe esik; a sorrend **csökkenő** (legújabb év felül:
  2024 → 2011 → 2009 → 2008 a mintában).
  **Fontos megfigyelés:** ha egy adott gyűjtemény-listában MINDEN mappa
  ugyanabba az évbe esik, a Picasa NEM rajzol évszám-fejlécet — a
  mappák közvetlenül a gyűjtemény-fejléc alá kerülnek (ez látszik a
  `145027.png`/`144904.png` teljes „Mappák (67)" listáján: az összes
  teszt-mappa azonos dátumú, nincs évszám-sor).
- **Mappasor**: sárga mappaikon + név + `(darabszám)`, **nincs saját
  nyitó-nyíl** (a Mappák-lista lapos, nem rekurzív fa — egy mappa alatt
  nincsenek almappa-sorok). Kijelölt sor: teljes szélességű acélkék
  háttér (`#83a7bd`), fehér felirat.
- Egy adott gyűjteményen belüli, dátum nélküli elem (pl. `HS logo` a
  150933-as mintában) közvetlenül a gyűjtemény-fejléc alá kerül, évszám-
  csoport NÉLKÜL — tehát az évszám-sor csak a ténylegesen dátumozott
  mappákhoz tartozik.

### 1.2 Nálunk (`FolderPane.qml` + `FolderTreeItem.qml`)

- `FolderPane.qml` **csak két, kőbe vésett szekciót** rajzol: egy
  `"Albums"`-fejlécet (52–72. sor) és egy `"Folders"`-fejlécet
  (97–121. sor). **Nincs Emberek, nincs Projektek, nincs Egyebek
  szekció** — a felhasználó öt gyűjteményéből csak kettő létezik a mai
  kódban.
  - Az „Albums" fejléc darabszáma **hardkódolt szöveg: `"(1)"`**
    (67. sor: `qsTr("Albums") + " (1)"`), nincs valódi modellhez kötve.
  - A fejléc-háromszög (`"▼"`, 65./108. sor) **statikus szöveg**, nincs
    `MouseArea`/`TapHandler` — a szekció mindig „kinyitva" van, nem
    csukható össze, és nincs zöld/piros színkódolás (egységesen
    `Theme.panelHeaderText` szürke).
  - Van egy harmadik, **eredetiben nem létező** sor: „Starred photos"
    (★, 74–95. sor) az Albums-fejléc alatt, közvetlenül a Mappák-fejléc
    előtt. Az eredeti Picasában a csillagos szűrés a felső eszköztár
    Szűrők-sorának ★ ikonjával működik (ld. 2. szakasz), NEM önálló
    fa-sorként — ez tehát egy nálunk kitalált, az eredetitől eltérő
    UI-elem (funkcionálisan hasznos lehet, de nem Picasa-hű elhelyezés).
- **Évszám-elválasztó** (`FolderTreeItem`-től függetlenül, magában a
  `FolderPane.qml` `delegate`-jében, 166–176. sor) létezik és a
  megfelelő helyen (a Mappák-listában) jelenik meg — ez már implementált
  funkció (`#77`/dizájnkézikönyv 08. fejezet hivatkozással a
  kódkommentben). Két eltérés az eredetihez képest:
  1. **`font.family: Theme.monoFamily`** (`"IBM Plex Mono, monospace"`,
     Theme.qml 101. sor) — az eredeti screenshoton az évszám ugyanaz a
     arányos (nem monospace) betű, mint a többi UI-szöveg.
  2. **Nincs jobbra futó elválasztó-vonal** az évszám mellett — nálunk
     az évszám egy önálló `Text`, az eredetiben egy `Text` + egy vékony
     `Rectangle`-vonal a sor hátralévő szélességén.
  Az indentálás is szűkebb: nálunk az évszám `leftMargin: 6`, a
  mappasor `leftMargin: 12` — csak 6px különbség; az eredetin az évszám
  és a mappaikon között vizuálisan jóval nagyobb (kb. a mappaikon
  szélességének megfelelő, ~16–20px) a behúzás-különbség.
- **`FolderTreeItem.qml` NEM a főablak mappafájáé** — ez a komponens a
  „Mappakezelő" (`FolderManagerDialog`, `#231`) rekurzív
  fájlrendszer-böngészőjéhez tartozik (ott indokolt a valódi, saját
  nyitó-nyíllal rendelkező fa, mert a lemez tényleges könyvtár-
  hierarchiáját mutatja). A főablak mappafája (`FolderPane.qml`) egy
  lapos `ListView`, `kind: "year" | "folder"` sorokkal — ez helyes
  modellezés (az eredeti Mappák-lista sem rekurzív fa), csak fontos
  tudni feladatkiosztáskor, hogy a két fájl **két különböző UI-t** szolgál
  ki, nem ugyanazt.
- Mappasor: van egy `"▸"` nyílglifa minden mappasor előtt (183–189. sor)
  — ez az eredetiben **nincs jelen** (a mappasorok nem nyithatók,
  nincs almappa-szint, tehát nyíl sem indokolt rajtuk).

### 1.3 Eltérés-összefoglaló (mappafa)

| # | Jelenség | Eredeti | Nálunk | Súlyosság |
|---|---|---|---|---|
| 1 | Gyűjtemény-szintek száma | 5 (Albumok, Emberek, Projektek, Mappák, Egyebek) | 2 (Albums, Folders) | **nagy** — ez a fő panasz oka |
| 2 | Gyűjtemény-fejléc csukható? | igen, zöld▼/piros▶ | nem, statikus `"▼"` | közepes |
| 3 | „Albums (1)" darabszám | valódi | hardkódolt `"(1)"` | kicsi (kozmetikai bug) |
| 4 | „Starred photos" sor a fában | nincs (a Szűrőn van) | van, extra sor | kicsi–közepes (UX-döntés kérdése) |
| 5 | Évszám-elválasztó jelenléte | igen (Mappák, ha >1 év) | igen, megvalósítva | — (megegyezik) |
| 6 | Évszám betűtípus | UI-alap (arányos) sans | monospace (IBM Plex Mono) | kicsi |
| 7 | Évszám melletti elválasztó-vonal | van (vékony vonal a sor végéig) | nincs | kicsi |
| 8 | Mappasor nyílglif | nincs | van (`▸` minden sor előtt) | kicsi |
| 9 | `FolderTreeItem.qml` viszonya a főablakhoz | — | ez a Mappakezelő dialógusé, NEM a főablak fájáé | (tisztázás, nem hiba) |

---

## 2. Bal panel ↔ rács elválasztó (splitter)

**Eredeti:** a screenshotokon a bal panel és a jobb oldali rács között
egy vékony, kettős bevágású („groove") sáv fut (`145027.png`,
x≈236–243px mérve), vizuálisan olyan, mint egy fix keret — kurzor-
viselkedést (húzható-e) állóképből nem lehet megállapítani, de a
Picasa 3.9 natív Windows-ablaka valódi húzható splitter volt.

**Nálunk:** `Main.qml` 456–464. sor — a `SplitView` komponens ténylegesen
húzható splittert ad a `FolderPane` és a rács közé
(`SplitView.preferredWidth: 230`, `SplitView.minimumWidth: 160`) — ez
**megfelel** az eredeti viselkedésnek, sőt explicit minimum-szélességgel
kényelmesebb, mint egy natív Win32-splitter. **Nincs eltérés** ezen a
ponton — érdemes csak megjegyezni, hogy a mért eredeti panel-szélesség
(≈236–243px egy 1918px széles ablakban) és a nálunk beállított
230px @ 1280px ablaknál arányaiban **szélesebb** a mienk (lásd 5. pont).

---

## 3. Görgetősáv (scrollbar)

### 3.1 Eredeti

- **Mappafa (bal panel):** klasszikus, keskeny (kb. **16px** széles)
  Windows-görgetősáv — fel/le nyílgomb a sín tetején/alján, világosszürke
  sín, szürke fogantyú. **Mindig látszik**, amikor van mit görgetni
  (67 mappás listánál igen) — ld. `145027_panel.png`.
- **Rács (fényképrács):** ugyanolyan szélességű (~16px), natív
  Windows-görgetősáv, szintén fel/le nyílgombokkal, halványkék
  kiemeléssel a fogantyún (`145027_gridscroll2.png`).
- Mindkettő a natív Windows-króm (nem egyedi Picasa-stílus) — a
  dizájnkézikönyv 06. fejezete szerint a cél-szín `#CDCDCD` egy vékony,
  lapos sávhoz (ld. `docs/specs/design-guide.md`), tehát a natív
  megjelenés **nem** követendő minta, csak dokumentált tényállapot.

### 3.2 Nálunk (`PicasaScrollBar.qml`)

- Egyedi (nem natív) `ScrollBar`, **10px** vastag fogantyú+sín
  (`barThickness: 10`), lekerekített (`radius: width/2`) szürke
  fogantyú, nyílgombok **nélkül** — ez szándékos, dizájnkézikönyv-hű
  minimalista stílus, nem az eredeti Windows-króm másolata.
- **`#323` explicit döntés a kódkommentben**: a sáv nyugalmi
  állapotban is látszik, ha van mit görgetni (`barVisible`), tehát ez
  a pont — „a rács/mappafa görgetősávja mindig látszik-e" — **direkt
  szándékosan** implementált, és megegyezik az eredeti viselkedéssel
  (mindig látszik, nem csak hoverre/görgetéskor villan fel).
- Alkalmazva: `FolderPane.qml` 207. sor (`ScrollBar.vertical:
  PicasaScrollBar {}` a mappa-`ListView`-n) és a keresési
  csoport-listán (`Main.qml` 656. sor) — de a **fő fényképrács
  (`LightboxFeed.qml`) elején nem találtam explicit
  `ScrollBar.vertical` kötést** az első 120 sorban; érdemes
  ellenőrizni (más session dolgozik rajta), hogy a `grid` `ListView`
  ténylegesen a `PicasaScrollBar`-t használja-e, vagy a Qt-alap
  görgetősávra esik vissza.

### 3.3 Eltérés-összefoglaló (görgetősáv)

| # | Jelenség | Eredeti | Nálunk | Súlyosság |
|---|---|---|---|---|
| 1 | Szélesség | ~16px, nyílgombokkal | 10px, nyílgomb nélkül | kicsi (tudatos stílusdöntés) |
| 2 | Mindig látszik-e (van tartalom esetén) | igen | igen (`#323` szerint szándékos) | — (megegyezik) |
| 3 | Fő rács kötése | — | nem ellenőrizhető az olvasott részletből, utánanézendő | ellenőrzendő |

---

## 4. Eszköztár (felső sáv)

### 4.1 Eredeti

Egyetlen sor (~38–39px magas, mérve `145027.png`-n y≈41–80), balról
jobbra:
1. **Importálás** gomb — kamera-ikon + lejátszás-háromszög + „Importálás"
   felirat.
2. **`+📁`** kis gomb (új album/mappa-gyűjtés) — kék mappaikon zöld
   plusszal.
3. Két **nézetváltó** ikon (lista / részletes-lista).
4. Egy lenyíló nyíl (▾) — feltehetően nézet-beállítások.
5. Jobb oldali blokk: **„Szűrők"** felirat fölötte, alatta 5 ikon
   (csillag ★, fel-nyíl, alak/személy, rács/kollázs, cimke/pin) + egy
   csúszka (thumb méret vagy dátum-tartomány).
6. **Keresőmező** — fehér, nagyítóval, jobb szélén villogó frissítés-
   ikon (szinkron-jelző).
7. Jobb felül, a menün kívül: „Bejelentkezés Google Fiókkal" hivatkozás
   (ez a menüsorban van, nem az eszköztárban).

### 4.2 Nálunk (`MainToolbar.qml`)

- `height: 34` — az eredeti mért ~38–39px-hez közeli, kicsit alacsonyabb.
- Sorrend: **Import** gomb (100×24px) → nyújtható térköz → „Filters"
  felirat + 4 ikon (★, ☺, ⚲, ▤) + csúszka → keresőmező (300×24px,
  saját rajzolt nagyítóval és törlő ✕ gombbal) → verziószám-felirat
  jobb szélen.
- **Hiányzik**: a `+📁` gyors-album gomb és a két nézetváltó ikon +
  lenyíló nyíl (4.1/2–4. pont) — ezek a mai `MainToolbar.qml`-ben
  nincsenek jelen.
- A négy szűrő-ikon közül csak a ★ (csillag) és a ⚲ (geo) aktív
  ténylegesen (`TapHandler`-rel bekötve); a ☺ (arc-szűrő, 3. fázisra
  utalva a kódkommentben) és a ▤ (méret/mozgókép) `opacity: 0.45`,
  vizuálisan inaktívak — ez tudatos, fázisokra bontott hiányosság
  (dokumentálva a kódban), nem hűség-hiba.
- A verziószám-felirat (`versionLabel`) az eredetiben nem létezik —
  fejlesztői/debug célú kiegészítés, nem Picasa-elem.
- A „Bejelentkezés Google Fiókkal" hivatkozás (menüsor jobb széle,
  eredetiben jelen van) a `MainToolbar.qml`-ben nincs — ez várható,
  hiszen a PicasaPy nem Google-fiókhoz kötött szolgáltatás.

### 4.3 Eltérés-összefoglaló (eszköztár)

| # | Jelenség | Eredeti | Nálunk | Súlyosság |
|---|---|---|---|---|
| 1 | Magasság | ~38–39px | 34px | kicsi |
| 2 | `+📁` gyors-album gomb | van | nincs | közepes |
| 3 | Nézetváltó ikonpár + lenyíló nyíl | van | nincs | közepes |
| 4 | Szűrő-ikonok száma/típusa | 5 ikon (★ ⬆ 👤 ▤ 🏷) + csúszka | 4 ikon (★ ☺ ⚲ ▤) + csúszka, 2 inaktív | kicsi (fázis-döntés) |
| 5 | Keresőmező | fehér, nagyító, natív | fehér, saját rajzolt nagyító+törlés | — (megfelel) |
| 6 | Verziófelirat | nincs | van | (szándékos extra) |

---

## 5. Alsó tálca (kijelölés-tálca)

### 5.1 Eredeti

Két rétegű sáv a rács alatt (`145027.png`, y≈930-tól a kép aljáig, a
screenshot 1030px-nél levágva, tehát a tálca alsó pereme nem
látszik teljesen):
1. **Kék infó-csík** (~13–14px, `#568fb7`-hez közeli tömör kék, mérve
   y≈930–943): a kijelölés/mappa adatai — pl. „7 képek 2026. július 8.,
   szerda 248 KB/lemez", ill. egyetlen kép kijelölésekor fájlnév,
   dátum, méret, KB.
2. **Világosszürke tálca-sáv** (a kép aljáig legalább ~85px, ténylegesen
   valószínűleg tovább, screenshot-vágás miatt nem mérhető pontosan):
   - bal szélen: a kijelölt képek **filmszalag-szerű kis
     bélyegképsora** (itt kb. 20×20px téglalapok), alatta/mellette
     „Kijelölés" felirat (ha nincs kijelölés) — ld. `145523.png`
     „Nincs kijelölés" állapot.
   - mellette egy 3-gombos oszlop: zöld pin/tű ikon, piros kör-ikon
     (tiltás/törlés), kék könyv+nyíl ikon lenyíló nyíllal.
   - ★ csillag / ↺ visszavonás / ↻ újra gombkör.
   - nagy **zöld „Feltöltés a Google Fotókba"** gomb.
   - **E-mail / Nyomtatás / Exportálás** — ikon a felirat fölött,
     középre igazítva.
   - jobb oldalon: kép-ikon + nagyítás-csúszka.
   - legjobbra: 4 kerek gombcsoport — személy (👤), hely (📍, piros),
     címke (🏷), infó (ⓘ, kék kör).

### 5.2 Nálunk (`TrayBar.qml`)

- **`infoBar`**: `height: 20` — az eredeti (~13–14px) helyett nagyobb,
  ez **szándékos**: a kódkomment szerint „nálunk 20px (olvashatóság)"
  (ld. `design-guide.md` 68. sor is ezt rögzíti). Van egy extra,
  eredetiben nem létező **„busy sweep" fény-animáció** a háttérmunka
  (indexelés) jelzésére (`#70`) — ez tudatos UX-kiegészítés.
- **Fő tálca**: `height: 52`, `Theme.trayBg` (`#f8f8f8`).
  - Kijelölés-tálca: `Item { Layout.preferredWidth: 200 }`, `Flow`-ban
    20×20px bélyegképek, „Selection" placeholder-szöveg üres
    kijelölésnél — **megfelel** az eredetinek (filmszalag + „Kijelölés"
    felirat üresen).
  - **Hiányzik a 3-gombos oszlop** (zöld pin / piros tiltás-kör / kék
    könyv+nyíl+lenyíló, ld. `145027_traybar_mid.png`) — ezek a
    Picasa „kijelölés rögzítése / kijelölés törlése / gyűjteménybe
    mentés" funkciói, a mai `TrayBar.qml`-ben nincs megfelelőjük.
  - ★ csillag + ↺/↻ forgatás gombok — **megvan**, sorrendben és
    funkcióban egyezik.
  - Nagyítás-csúszka **−/+ jelekkel** — megvan (`174–181`. sor),
    egyezik.
  - **E-mail / Print gomb `enabled: false`** (183–184. sor) — vizuálisan
    jelen van, de funkcionálisan tiltott (fázis-döntés, dokumentált).
  - **Export gomb** — megvan, működik.
  - **Zöld „Upload to Google Photos" gomb** — jelen van, de
    **`enabled: false`** (196–199. sor, `accent: Theme.picasaGreen`) —
    a PicasaPy nem Google-fiókos szolgáltatás, ez a gomb vélhetően
    csak vizuális hűség/placeholder, nem tervezett működő funkció.
  - **Hiányzik a jobb szélen a 4 kerek ikongomb-csoport** (személy /
    hely / címke / infó) — a `TrayBar.qml`-ben ennek nincs nyoma;
    ezek a funkciók (Emberek-panel, Helyek-panel, Címkék-panel,
    Tulajdonságok-panel) `Main.qml`-ben **léteznek**, csak nem a
    tálcáról, hanem a menüsorból/gyorsbillentyűkkel (Ctrl+T,
    Alt+Enter) nyithatók — tehát funkcionálisan megvan, de **nem a
    Picasa-hű helyen** (tálca jobb széle) van elérve.

### 5.3 Eltérés-összefoglaló (tálca)

| # | Jelenség | Eredeti | Nálunk | Súlyosság |
|---|---|---|---|---|
| 1 | Infó-csík magassága | ~13–14px | 20px | kicsi (szándékos) |
| 2 | 3-gombos oszlop (pin/tiltás/könyv) | van | nincs | közepes |
| 3 | ★/↺/↻ gombok | van | van | — (megegyezik) |
| 4 | E-mail/Nyomtatás/Exportálás | van, működik | van, E-mail+Print tiltva | kicsi (fázis-döntés) |
| 5 | Zöld „Feltöltés" gomb | van, működik (Google-fiók) | van, tiltva | (szándékos, terméklogika) |
| 6 | Jobb szélen 4 ikongomb (személy/hely/címke/infó) | tálcán | máshol (menü/gyorsbillentyű) | közepes (elhelyezés) |

---

## 6. Ablak-arányok

Mérve az eredeti screenshoton (`145027.png`, 1918×1030px, gyakorlatilag
teljes 1920×1080-as kijelző, tálca alja levágva a képernyő aljával):

| Elem | Eredeti (mérve) | Nálunk (kód szerint) | Megjegyzés |
|---|---|---|---|
| Ablak alap-méret | 1920×1080 (maximalizált) | `Main.qml`: `width: 1280; height: 800` (alap, nem maximalizált) | eltérő tesztfelbontás, nem hűség-kérdés |
| Menüsor magassága | ~23px | natív Qt-menüsor (nem mérhető innen) | — |
| Eszköztár magassága | ~38–39px | 34px | ld. 4.3/1 |
| Bal panel szélessége | ~236–243px @1920px (≈12,3%) | `SplitView.preferredWidth: 230` @1280px (≈18%) | **arányaiban szélesebb nálunk** kisebb ablakban; `design-guide.md` 386px@1920/250px@1280 becslése is ezt támasztja alá |
| Panel-sor magassága | ~22px (mérve a mappasorok között) | `height: 22` (`FolderPane.qml` delegate) | **egyezik** |
| Infó-csík magassága | ~13–14px | 20px | ld. 5.3/1 |
| Tálca magassága | legalább ~85–100px (screenshot levágva) | 52px (fő sáv) + 20px (infó) = 72px | valószínűleg kisebb nálunk, de az eredeti nem mérhető pontosan a vágás miatt |

---

## 7. Összegzés — mit érdemes elsőként javítani

Súlyozás szerint (nagy → kicsi):

1. **Mappafa öt gyűjteménye** (1.3/1): Emberek, Projektek, Egyebek
   szekció hiányzik a `FolderPane.qml`-ből — ez a felhasználói panasz
   gyökere, és ez a legnagyobb szerkezeti eltérés a teljes auditban.
2. Gyűjtemény-fejlécek csukhatósága + zöld/piros háromszög-jelzés
   (1.3/2).
3. Eszköztár hiányzó `+📁` gomb és nézetváltó ikonpár (4.3/2–3).
4. Tálca hiányzó 3-gombos oszlop és a jobb szélen a négy ikongomb
   Picasa-hű elhelyezése (5.3/2, 5.3/6).
5. Kisebb, kozmetikai pontok: „Albums (1)" hardkód, évszám-sor
   betűtípusa/elválasztó-vonala, mappasorok felesleges `▸` nyila,
   panel-szélesség aránya kisebb ablaknál.

Nem talált hiba / megfelelő: a splitter (SplitView, húzható,
230px), a görgetősáv „mindig látszik" viselkedése (`#323`, tudatosan
implementálva), az évszám-elválasztó funkció megléte és helyes
elhelyezése a Mappák-listában, a ★/↺/↻ gombok és a nagyítás-csúszka a
tálcán.
