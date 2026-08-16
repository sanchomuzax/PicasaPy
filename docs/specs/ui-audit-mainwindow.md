# UI-audit — főablak (mappafa, eszköztár, tálca, görgetősáv, arányok)

> 📐 A **méretek** kötelező listája:
> [`konyvtar-ablak-meretek.md`](konyvtar-ablak-meretek.md). Ez a lap
> képernyőkép-alapú audit; ahol a kettő eltér, **a méretlap az igazság**.

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
- **Mappasor**: sárga mappaikon + név + `(darabszám)`, ebben a nézetben
  **nincs saját nyitó-nyíl**. Kijelölt sor: teljes szélességű acélkék
  háttér (`#83a7bd`), fehér felirat.

  > ⚠️ **HELYESBÍTÉS (2026-08-15).** A korábbi szöveg azt állította, hogy „a
  > Mappák-lista lapos, nem rekurzív fa". **Ez téves általánosítás volt:** a
  > lapos lista csak az EGYIK a két nézetmód közül. A Picasának van valódi,
  > kibontható **fanézete** is — ld. a lenti 1.4 szakaszt. A tévedés oka,
  > hogy az akkor rendelkezésre álló képernyőképek mind lapos nézetben
  > készültek.
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

## 1.4 A MÁSIK nézetmód: valódi mappafa (2026-08-15)

A panelnek **két, egymást kizáró nézetmódja** van, és eddig csak az egyiket
auditáltuk. Az elrendezés-erőforrás egyértelmű (`thumbui.tre`, „listview
toggle group"):

```
thumbui/folderview: thumbui/hviewtoggle
thumbui/flatview:   thumbui/hviewtoggle
thumbui/hviewtoggle: thumbui/buttonbarsets
```

A `thumbui_text.tre` buboréksúgói mondják meg, melyik mit csinál:

| elem | buboréksúgó |
|---|---|
| `thumbui/flatview` | „Set view to show **flat** folder structure" |
| `thumbui/folderview` | „Set view to show folder **tree** structure" |
| `thumbui/folderviewpopup` | „View options" |

Mivel közös `hviewtoggle` szülő alatt ülnek, **egyszerre csak az egyik
aktív** — ez a két lapos ikon a keresőmező bal oldalán.

### Amit a fanézet mutat (a tulajdonos képernyőképéről)

A fanézet **nem** ugyanaz a lista más rendezésben, hanem **valódi
fájlrendszer-hierarchia**:

```
Mappák (53)
  Sajátgép (1 072)
    ▷ DS215j (227)
    ▲ Képek (842)
        ▷ Picasa (691)
        ▷ AI (92)
        ▲ wallpapers (51)
             space (7)
             LEGO (5)
             Star Trek (4)      ◀ kijelölve
             sailing (5)
             Ubuntu 14.10 (12)
        lake (8)
    Videók (3)
```

Megfigyelt eltérések a lapos nézethez képest:

- **behúzás szintenként**, kibontó háromszöggel (`▷` csukott, `▲` nyitott);
- a mappaikon helyett a bejegyzett almappáknál **bélyegkép-ikon** jelenhet meg
  (a képen a `space`, `LEGO`, `Star Trek`, `sailing` sorok ikonja a mappa egy
  fotójának kicsinyítése, nem sárga mappa);
- **nincs évszám-tagolás** — az csak a lapos nézet sajátja;
- a gyűjtemény-fejléc darabszáma a fában az **összes** mappát számolja
  (`Mappák (53)`), nem csak a legfelső szintűeket;
- a kijelölt soron jobb oldalt kis **görgető-fogantyú** jelenik meg.

*Bizonyítottsági fok: megerősített* (elrendezés-erőforrás + buboréksúgó +
képernyőkép).

### A sormagasság és a behúzás — NEGATÍV eredmény (2026-08-15)

A `respack.yt` rétegtéglalapjai a felület nagy részére képpontra megadják a
geometriát (`binaris-regeszet-modszertan.md` 14/c). **A mappafa sorára
NEM.** Végignézve a csomagot:

- a bal panel listája `thumbui/albums_win` / `albums_mac`, típusa **`listbox`**
  (x 9..205, y 75..412 a tervezővásznon) — csak a **keret**, sorsablon nélkül;
- az egész csomagban **egyetlen** `proto` (sorsablon) van,
  `thumbui/headerproto` (199 × 17), és az a **rács** fejlécsora, nem a fa;
- a `scratch.tre` `scratch/album*` elemei a **képtálca** elemsablonját adják
  (a fájl saját kommentje mondja ki: „the tray can get so small that there's
  no room for text"), nem a mappafáét.

**Következtetés:** a `listbox` a sorait **kódból** rajzolja, a sormagasság és
a behúzás nem elrendezés-erőforrás. Ahhoz a rajzoló rutint kellene
visszakövetni — ez a kérdés árához képest drága, és a sor magassága a
`design-guide.md`-ből amúgy is szabadon választható (a mi listánk működik).

*Bizonyítottsági fok: elvetve* — nem cáfolva, hanem **nem ebből a forrásból
kideríthető**. A következő körnek ne kelljen újra végigjárnia.

### Amit a csomag viszont megad — a bal panel fejléc-elemei

Ezek **méretek**, tehát a tervezővászon-csapda (14/c) nem érinti őket:

| elem | méret | mi ez |
|---|---|---|
| `albumview` | **132 × 29** | „Vissza a könyvtárhoz" |
| `newalbum` | **29 × 22** | új album |
| `newfolder` | **29 × 22** | új mappa |
| `folderview` | **30 × 22** | nézetváltó (fa/lapos) |
| `folderviewpopup` | **22 × 22** | a nézet-legördülő nyila |
| `listbox_title` | 80 × 14 | a „Könyvtár" felirat |
| `hlistsizer` | **8** széles | a húzható elválasztó |

## 1.5 A „View options" legördülő — teljes tartalom a binárisból

A `thumbui/folderviewpopup` gomb (a két nézetváltó ikon melletti nyíl) nyitja.
A menü **teljes tétellistája** a felépítő rutinból (`0x00733480`, 1311 bájt)
kiolvasva — nem képernyőképről:

| tétel | parancsazonosító |
|---|---|
| `Sort by &Date` | `AlbumList::ID_VIEWBYDATE` |
| `Sort by &Recent Changes` | `AlbumList::ID_VIEWBYRECENT` |
| `Sort by &Size` | `AlbumList::ID_VIEWBYSIZE` |
| `Sort by &Name` | `AlbumList::ID_VIEWBYNAME` |
| `Re&verse sort` | `AlbumList::ID_VIEWREVERSE` |
| `Sort &People by Name` | `AlbumList::ID_PEOPLEBYNAME` |
| `Sort People by &Amount` | `AlbumList::ID_PEOPLEBYAMOUNT` |
| `Sort People by Top &10` | `AlbumList::ID_PEOPLEBYAMOUNTTOP10` |
| `&Shortcuts` (almenü) | `AlbumList::Shortcuts` |
| `Show &Thumbnails in Library` | `AlbumList::ID_VIEW_THUMBNAILS` |
| `&Simplified Tree View` | (a `SimplifiedHierarchy` beállításkulcs) |

A `Shortcuts` almenü tételei ugyanebből a rutinból: `My &Computer`
(`AlbumListWin::ID_VIEW_ALL`), `My &Pictures` (`…::ID_VIEW_MYPICTURES`),
`My Do&cuments` (`…::ID_VIEW_MYDOCS`), `&Desktop`
(`AlbumList::ID_VIEW_DESKTOP`).

> **KIEGÉSZÍTÉS (2026-08-15, #702).** A korábbi szöveg úgy zárult, hogy az
> `AlbumList::ID_VIEW_WATCHED` felirata „nem ebben a rutinban van".
> Megvan: a `Picasa3i18n.dll` string-táblájában
> `AlbumList::ID_VIEW_WATCHED` = `&Simplified Tree View` /
> `&Egyszerűsített fanézet` (a fenti táblázat utolsó sora) — a rutin a
> feliratot és az azonosítót külön sztringként hivatkozza, ezért tűnt
> párosítatlannak. A teljes kifejtés az 1.7 szakaszban.

**Két, egymástól független kapcsoló, amit ne keverjünk össze:**

- **`Simplified Tree View`** — a `SimplifiedHierarchy` beállításkulcsot
  állítja (hivatkozók: `0x00574b70`, `0x00575130`, `0x005cb990`,
  `0x005e2000`). Ez a fanézeten belül **rövidíti a láncot**: az egygyermekes,
  köztes mappaszinteket összevonja.
- **`Show Thumbnails in Library`** — a listasorok ikonját cseréli
  mappaikonról bélyegképre. Ez magyarázza a fanézeti képernyőképen látott
  fotó-ikonokat.

A rendezés-tételek elé a Picasa **pipát** rajzol az aktív állapotnál (a képen
`Sort by Date` és `Sort People by Name`), a `Sort People by Top 10` pedig
**szürkített** — vagyis a People-rendezés tételei kontextusfüggően tilthatók.

*Bizonyítottsági fok: megerősített* (a feliratok és azonosítók egyetlen
rutinból; a pipa/szürkítés képernyőképről).

## 1.6 Teljes UI-leltár — 2020 elem, 74 panel

A `.tre` erőforrások **deklaratívan** írják le az eredeti teljes felületét.
Az `eszkozok/tre_leltar.py` (privát repó) ebből gépi leltárt épít:
elem → panel → szülő → felirat → buboréksúgó → makrók → tulajdonságok.
Kimenet: `referencia/ui-leltar.csv` (privát repó).

Ez **2020 UI-elem 74 panelen** — vagyis az audit innentől nem
képernyőkép-vadászat, hanem egy zárt lista végigdolgozása.

| panel | elem | ebből feliratos |
|---|---:|---:|
| `editpanel` | 312 | 78 |
| `thumbui` | 140 | 35 |
| `publish` | 125 | 27 |
| `makemoviepanel` | 111 | 39 |
| `collagepanel` | 108 | 47 |
| `printpanel` | 73 | 31 |
| `acquirepanel` | 67 | 16 |
| `upload` | 61 | 7 |
| `buzzupload` | 55 | 7 |
| `compose_share` | 49 | 12 |
| `printoptions` | 49 | 23 |
| `canoncapturemoviepanelpopup` | 45 | 1 |
| `capturemoviepanelpopup` | 45 | 10 |
| `edittextpanel` | 45 | 17 |
| `compose_mail` | 41 | 8 |
| `faceheaderpanel` | 39 | 13 |
| `editoneup` | 34 | 2 |
| `oneup` | 33 | 2 |
| `quicktagconfig` | 33 | 3 |
| `foldermgr` | 32 | 10 |
| `outputlayout` | 31 | 9 |
| `headerpanel` | 30 | 11 |
| `buttonmgr` | 29 | 9 |
| `searchcontainer` | 25 | 8 |
| `choose_mail` | 24 | 9 |
| `tagpanel` | 24 | 4 |
| `video_control_bar` | 24 | 3 |
| `collab` | 23 | 3 |
| *(további 46 panel)* | 313 | — |


**Amiért ez fontos:** eddig minden UI-hiba **felhasználói szemrevételezéssel**
derült ki. A leltárral megfordítható a sorrend: minden panelre kikereshető,
hány eleme van az eredetinek, és abból mi hiányzik nálunk. A `PicasaPy` ma
99 QML-fájlt tartalmaz — a fenti 74 panelhez képest ez önmagában is megmutatja,
hol lesznek fehér foltok.

**Következő lépés (jegyre való):** panelenkénti lefedettség-tábla, az
`ui-leltar.csv` és a QML-fák összevetéséből, gépi úton.

## 1.7 A fanézet parancsai és beállításkulcsa — a #702 három kérdése

A #702 három kérdést nevezett meg, amit kódírás előtt meg kellett
válaszolni. Mindhárom a `Picasa3i18n.dll` string-táblájából és a
`Picasa3.exe` bináris indexéből válaszolható, felhasználói mérés nélkül.
A hivatkozott függvénycímek a `Picasa3.exe` image-base 0x00400000-hoz
tartozó abszolút címei (`referencia/binary-index/picasa3-index.sqlite`,
`meta.json`: SHA-256 `644b7bec…93ddc96`).

### (1) Külön nézet, vagy a laposat váltja fel? → **váltja**, HÁROM módban

A **`View ▸ Folder View`** almenü (`eMenuView::FolderView` = „&Folder View" /
„&Mappanézet") a menüsort felépítő `FUN_00559150` (0x00559150, 15 495 bájt)
rutinból, a szomszédos tételekkel együtt kiolvasva:

| parancsazonosító | angol felirat | magyar felirat |
|---|---|---|
| `eMenuView::ID_VIEW_FOLDERS` | `&Flat Folder View` | `&Egyszerű mappanézet` |
| `eMenuView::ID_VIEW_ALL` | `&Tree View` | `&Fanézet` |
| `eMenuView::ID_VIEW_WATCHED` | `&Simplified Tree View` | `&Egyszerűsített fanézet` |

Ugyanez a tételkészlet ül a `thumbui/folderviewpopup` legördülőben is
(`FUN_00733480`, ld. 1.5) — csak ott a „Tree View"/„Flat Folder View"
pár nem menütétel, hanem a mellette álló **két váltógomb**
(`thumbui/folderview` / `thumbui/flatview`, közös `thumbui/hviewtoggle`
szülő alatt, ld. 1.4). Vagyis: **a fa nem külön nézet, hanem a bal hasáb
egyik megjelenítési módja**, és a menüsorból ugyanúgy elérhető, mint az
eszköztárból.

Fontos részlet: az `ID_VIEW_ALL` azonosító **két feliratot** visel a
felület két helyén — a Nézet menüben „&Tree View", a `Shortcuts`
almenüben `AlbumListWin::ID_VIEW_ALL` = „My &Computer". Ez nem
ellentmondás: a fanézet gyökere maga a Sajátgép. Megerősíti a két
gyökér-felirat is:

| azonosító | angol | magyar |
|---|---|---|
| `ViewRoot::AllFolders` | `Default View` | `Alapértelmezett nézet` |
| `ViewRoot::All` | `My Computer` | `Sajátgép` |

Az 1.4 képernyőképén a fa gyökérsora tényleg `Sajátgép (1 072)`.

*Bizonyítottsági fok: megerősített* (string-tábla + két menüépítő rutin +
képernyőkép).

### (2) A `HierFolder` menüosztály teljes tételsora → **egyetlen tétel**

A string-tábla teljes `HierFolder::` névtere **egy** bejegyzés:

| azonosító | angol | magyar | mnemonik |
|---|---|---|---|
| `HierFolder::ID_MOVEHIERFOLDER` | `&Move Folder...` | `&Mappa áthelyezése...` | M |

A két kinyitó/összecsukó parancs **nem** a `HierFolder`, hanem a `Folder`
osztályba tartozik:

| azonosító | angol | magyar |
|---|---|---|
| `Folder::ID_HIER_FOLDER_EXPAND` | `Expand All` | `Az összes részletes nézete` |
| `Folder::ID_HIER_FOLDER_COLLAPSE` | `Collapse All` | `Az összes kicsinyítése` |

A menü, amit a `HierFolder` név takar, a **fa KÖZTES csomópontjának**
csökkentett helyi menüje — a `FUN_00733a40` (0x00733a40, 548 bájt) rutin
pontosan öt tételt épít:

1. `Expand All` — `Folder::ID_HIER_FOLDER_EXPAND`
2. `Collapse All` — `Folder::ID_HIER_FOLDER_COLLAPSE`
3. `&Locate on Disk` — `FolderWin::ID_ALBUM_LOCATEONDISK`
4. `&Remove from Picasa...` — `Folder::ID_MANAGE_ALBUM`
5. `&Move Folder...` — `HierFolder::ID_MOVEHIERFOLDER`

Összevetésül a TELJES mappa-menü (`FUN_007319f0`, 1 900 bájt) 20+ tételes,
és ott a mozgatás a `Folder::ID_MOVEFOLDER` (azonos felirattal) — a
`HierFolder` tehát a `Folder` menü szűkített változata, nem külön funkció.
A két `HIER_FOLDER` parancs **mindkét** menüben szerepel.

*Bizonyítottsági fok: megerősített* (a teljes tételsor egy-egy rutinból;
a feliratok a string-táblából).

### (3) Van-e beállításkulcs? → **igen, kettő, és egy csapda**

| kulcs | mi | hivatkozó rutinok |
|---|---|---|
| `SimplifiedHierarchy` | az „Egyszerűsített fanézet" állapota | 0x00574b70, 0x00575130, 0x005cb990, 0x005e2000 |
| `LastViewRoot`, `LastViewRoot2` | melyik gyökérből néz a hasáb (Alapértelmezett nézet / Sajátgép / Képek / Dokumentumok / Asztal) | 0x0040d3c0, 0x00576660 |

Mindkettő a `Preferences` szomszédságában áll a string-táblában, a
`LastAlbumSelected`, `RIGHTDRAWEROFFSET`, `mainwinpos`, `Thumbscale`
kulcsok között (`LastViewRoot` RVA 0x00880238, `SimplifiedHierarchy`
RVA 0x0088fd00) — vagyis valódi, tárolt beállítások.

**Csapda:** a `Hierarchy_p` (RVA 0x008835d0) **NEM** nézetmód-beállítás.
Egyetlen hivatkozó rutinja (0x004b9d80) összesen négy sztringet érint:
`StarredPhotosTotal`, `HiddenPhotosTotal`, `GeotaggedPhotosTotal` és
`Hierarchy_p` — vagyis darabszám-mezők társaságában áll, nem a
`Preferences` kulcsok között. Aki pusztán a névből következtet, a
nézetmódot rossz helyre köti.

*Bizonyítottsági fok: megerősített* (string-szomszédság + hivatkozó
rutinok).

~~**Nyitva (a):** a `SimplifiedHierarchy` és a `LastViewRoot` alapértéke
friss telepítésen — ehhez a Picasa első indítás utáni registry-állapota
kellene.~~ **MEGVÁLASZOLVA (2026-08-16)**, registry nélkül, a binárisból —
lásd „A fanézet HÁROM beállítása és az alapértékük" alább.

~~**Nyitva (b):** mire szolgál pontosan a `Hierarchy_p` számláló (a fenti
csak annyit mond ki, hogy NEM a nézetmód kulcsa).~~ **MEGVÁLASZOLVA
(2026-08-16)**: névtelen **használati statisztika** (telemetria) — lásd
„A `Hierarchy_p` telemetria, nem beállítás" alább.

### Amit ebből a PicasaPy megvalósít (#702, első szelet)

`src/picasapy/app/folder_hierarchy.py` (tiszta fa-építés),
`folder_hierarchy_controller.py` (állapot: nyitott ágak, egyszerűsítés) és
`qml/PicasaPy/FolderHierarchyView.qml` (a kirajzolt fa + a fenti ötös
helyi menü). A darabszám a részfa összege, a gyökérsor felirata
`qsTr("My Computer")`. A **nézetmód-váltó** (a két `hviewtoggle` gomb, a
`View ▸ Folder View` almenü és a `LastViewRoot` megőrzése) **még nincs
meg** — az a `Main.qml`/`FolderPane.qml` bekötésével jár, külön jegy.

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

> 📐 **Az alábbi 5.1 képernyőképből készült, és a kép 1030 px-nél levágva —
> a tálca alsó pereme nem látszik.** A pontos geometriát azóta a Picasa saját
> elrendezés-forrása adja meg:
> [`picasa-fo-ablak-elrendezes.md`](picasa-fo-ablak-elrendezes.md) →
> „Az alsó sáv — `basecontrolset`" (#455). Ahol a kettő eltér, **a forrás az
> igazság**. A legfontosabb, amit a képernyőkép nem adott meg:
> a sáv a **36,5 %-os osztópontnál** válik ketté (bal oldalt a tálca), a
> bélyegképsor jobbján **50 px** van fenntartva a három gombnak, és a zöld
> feltöltés-gomb **fix 145 px**.

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

### A fanézet HÁROM beállítása és az alapértékük (2026-08-16)

Az előző szakasz „Nyitva" pontja azt kérdezte, mi a `SimplifiedHierarchy` és
a `LastViewRoot` **alapértéke friss telepítésen**, és úgy tűnt, ehhez a
Picasa registry-állapota kellene. **Nem kell** — a bináris megadja.

#### A beállítás-hármas

| kulcs | cím | típus | mit tárol |
|---|---|---|---|
| `SimplifiedHierarchy` | `0x00c8fd00` | logikai | egyszerűsített ↔ teljes fa |
| `LastViewRoot` | `0x00c80238` | szöveg | a legutóbbi nézet-gyökér |
| **`LastViewRoot2`** | `0x00c80248` | szöveg | a **második** legutóbbi nézet-gyökér |

Mindhárom a `Preferences` (`0x00c7eafc`) kulcs alatt él, azaz
`HKEY_CURRENT_USER` (`0x00407a20` `0x80000001`-gyel nyitja).

**A `LastViewRoot2` eddig sehol nem szerepelt a specjeinkben.**

#### `SimplifiedHierarchy` — az alapérték: **kikapcsolva**

Négy hely olvassa: `0x00574b70`, `0x00575130`, `0x005cb990`, `0x005e2000`.
**Mind a négy azonos mintát használ:**

```asm
mov     dword ptr [esp + ...], 0    ; a helyi változó ELŐRE nullázva
push    0xc8fd00                    ; "SimplifiedHierarchy"
push    0xc7eafc                    ; "Preferences"
xor     eax, eax
call    0x407a20                    ; registry-olvasó
call    0x4019b0                    ; sztring → logikai
```

Ha a registry-érték hiányzik vagy üres, a `0x004019b0` üres sztringet kap,
és a helyi változó a **0**-n marad (`0x005751c5`: `mov byte ptr [esp+0x1f], 0`).

**Vagyis friss telepítésen a fa NEM egyszerűsített, hanem teljes.**

#### `"flat"` — foglalt gyökérnév

A `0x00c80258`-on álló `"flat"` sztring **nem mappaútvonal**, hanem a lapos
mappanézet foglalt gyökérneve. A nézetbeállító (`0x00575130`) második
argumentuma különbözteti meg a kettőt:

| hívás | 2. argumentum | jelentés |
|---|---|---|
| `push 0; push <mentett útvonal>` (`0x0040dc30`) | **0** | valódi mappa-útvonal |
| `push 1; push "flat"` (`0x0040dc35`, `0x005cc62c`) | **1** | különleges (lapos) nézet |

#### Indításkor mi történik

```asm
0x0040dab0  ; LastViewRoot   beolvasása
0x0040dae7  ; LastViewRoot2  beolvasása
...
0x0040dc1e  test edi, edi
0x0040dc1e  je   0x40dc43        ; nincs mentett gyökér → kihagyás
0x0040dc20  cmp  byte ptr [edi], 0
0x0040dc23  jne  0x40dc30        ; nem üres → visszaállítás
0x0040dc25  jmp  0x40dc43        ; ÜRES → kihagyás, nincs visszaállítás
```

Tehát **üres `LastViewRoot` esetén a program nem állít be nézet-gyökeret** —
nem esik vissza a `"flat"`-re. A `"flat"` ága máshonnan érkezik.

A hármast a `0x00576660` **együtt írja ki** a `LastAlbumSelected` mellé
(a `0x00407630` a registry-író) — vagyis a kilépéskori nézetállapot egy
csomagban mentődik.

*Bizonyítottsági fok:* **megerősített** a kulcsok létére, helyére és az írás
csomagolására · **erős** a `SimplifiedHierarchy` alapértékére (mind a négy
olvasóhely nullázza a helyi változót, és az üres-sztring ág 0-t hagy).

~~**Nyitva marad:** honnan ugrik a `0x0040dc35` (`"flat"`) ág — vagyis mikor
indul a program lapos nézetben~~ — **MEGVÁLASZOLVA (2026-08-16)**, lásd
„Indításkor a LAPOS nézet az alapértelmezés" alább. **Nyitva marad** a
`LastViewRoot2` pontos szerepe (feltehetően nézetmódonként külön gyökér, de
ezt nem igazoltuk).

### A `Hierarchy_p` telemetria, nem beállítás (2026-08-16)

A fenti „Nyitva (b)" azt kérdezte, mire szolgál a `Hierarchy_p`. A választ a
hivatkozó rutin (`0x004b9d80`, 323 bájt) és **annak hívója** adja meg.

#### A hívó azonosítja a szándékot

A `0x004b9d80`-at egyetlen hely hívja: **`0x0057d460`**, és ez a függvény a
`ScreenWidth`, `ScreenHeight`, `UniqueAccounts` mezőket is összeállítja.
Vagyis ez a **névtelen használati statisztika** (a `Preferences ▸
ReportStats` kapcsolóhoz tartozó jelentés) összeállítója.

#### Mit gyűjt a `0x004b9d80`

| mező | cím | hogyan |
|---|---|---|
| `StarredPhotosTotal` | `0x004b9dc8` | végigmegy egy bájttömbön, a nem-nulla elemeket számolja |
| `HiddenPhotosTotal` | `0x004b9e10` | ugyanígy, másik tömbön |
| `GeotaggedPhotosTotal` | `0x004b9e5b` előtt | ugyanígy, harmadik tömbön |
| **`Hierarchy_p`** | `0x004b9e74` | **nem számol semmit** |

A három `…Total` mező **darabszámot** küld (`0x0097a410(jelentés, db, 0)`).
A `Hierarchy_p` viszont más úton megy:

```asm
0x004b9e5b  cmp   byte ptr [ebp + 0x9d], 0   ; a főablak egy logikai jelzője
0x004b9e62  je    0x4b9ebc                   ; ha hamis → SEMMIT nem küld
0x004b9e64  push  0x18
0x004b9e66  call  0xc0769f                   ; 24 bájtos rekord foglalása
0x004b9e74  mov   edi, 0xc835d0              ; "Hierarchy_p"
0x004b9e87  mov   dword ptr [esi + 8], 4     ; TÍPUS = 4
0x004b9eb0  mov   dword ptr [esi + 0x14], 1  ; az érték: 1
```

Vagyis **jelenlét-jelző**: ha a főablak logikai jelzője igaz, a jelentés egy
`Hierarchy_p = 1` bejegyzést kap; ha hamis, a mező **ki sem kerül**. Se
darabszám, se beállítás — egy „ez a felhasználó használja" ping.

#### Amit ebből a PicasaPy csinál: SEMMIT

A PicasaPy **nem küld telemetriát**. A `Hierarchy_p` tehát nem
implementálandó, és nem is szabad összekeverni a nézetmód-beállításokkal
(`SimplifiedHierarchy`, `LastViewRoot`, `LastViewRoot2`) — azok a
`Preferences` alatt élnek, ez pedig soha nem íródik ki a gépre.

*Bizonyítottsági fok: megerősített* (a gyűjtő rutin teljes egészében
kiolvasva, és a hívója a `ScreenWidth`/`UniqueAccounts` mezőkkel azonosítja
a jelentést).

### Indításkor a LAPOS nézet az alapértelmezés (2026-08-16)

Az előző szakasz nyitva hagyta, honnan ugrik a `0x0040dc35` (`"flat"`) ág.
A `0x0040db85`–`0x0040dbb2` szakasz megadja:

```asm
0x0040db85  mov  edi, dword ptr [esp + 0xc]    ; az egyik mentett gyökér
0x0040db89  mov  esi, dword ptr [esp + 0x14]   ; a másik
0x0040db8d  test esi, esi
0x0040db8f  je   0x40dc35                      ; NINCS      → "flat"
0x0040db95  test dword ptr [esi], 0xffffff00
0x0040db9b  je   0x40dc35                      ; ÜRES       → "flat"
0x0040dba1  add  esi, 4                        ; a sztring a +4 eltoláson
0x0040dba4  cmp  byte ptr [esi], 0
0x0040dba7  je   0x40dc35                      ; ÜRES sztring → "flat"
0x0040dbad  push 1
0x0040dbaf  push esi
0x0040dbb2  call 0x575130                      ; SetView(mentett, 1)
```

és a cél:

```asm
0x0040dc35  push 1
0x0040dc37  push 0xc80258                      ; "flat"
0x0040dc3e  call 0x575130                      ; SetView("flat", 1)
```

**Három ág vezet ugyanoda:** ha a mentett gyökér hiányzik, a hossza nulla,
vagy a sztring üres — a program a **lapos mappanézettel** indul.

> **Friss telepítésen tehát a lapos nézet az alapértelmezés**, mert a
> beállítás még nem létezik.

#### ⚠️ Helyesbítés: a második argumentum NEM „különleges nézet"

Az előző kör azt írta, hogy a nézetbeállító (`0x00575130`) második
argumentuma különbözteti meg a valódi útvonalat (`0`) a különleges nézettől
(`1`). **Ez téves volt.** Itt a **mentett, valódi útvonal is `1`-gyel** megy
(`0x0040dbad`), ugyanúgy, mint a `"flat"`.

A helyes olvasat: a második argumentum azt választja ki, **melyik
nézet-rekeszbe** kerül a gyökér — a két mentett gyökérnek (`LastViewRoot`,
`LastViewRoot2`) két rekesze van. Az `1`-es ág az elsődleges.

Ezt a `0x0040dc30` ága erősíti meg: ott `push 0; push <a másik gyökér>` áll,
tehát a másik mentett útvonal a `0`-s rekeszbe megy.

~~**Nyitva marad**, melyik `Preferences`-kulcs melyik rekeszbe tartozik~~ —
**MEGVÁLASZOLVA (2026-08-16)**, lásd „Melyik kulcs melyik nézet-rekeszbe
tartozik" alább.

*Bizonyítottsági fok:* **megerősített** a lapos alapértelmezésre (mindhárom
ág kiolvasva) és arra, hogy a második argumentum nem a „különleges nézetet"
jelöli · **nyitott** a két rekesz és a két kulcs megfeleltetése.

### Melyik kulcs melyik nézet-rekeszbe tartozik (2026-08-16)

Az előző szakasz nyitva hagyta, hogy a `LastViewRoot` és a `LastViewRoot2`
közül melyik kerül az `1`-es, melyik a `0`-s nézet-rekeszbe. **A verem
végigkövetése eldönti.**

#### A két olvasás célja

```asm
0x0040dabe  lea esi, [esp + 0x9c]   ; ← a LastViewRoot kimenete
0x0040dac5  call 0x407630           ;   (a "LastViewRoot" kulccsal)

0x0040daf5  lea esi, [esp + 0x2c]   ; ← a LastViewRoot2 kimenete
0x0040daf9  call 0x407630           ;   (a "LastViewRoot2" kulccsal)
```

#### A két kicsomagolás

```asm
0x0040db03  lea  ecx, [esp + 0x94]  ; a LastViewRoot burkolója (a payload +8)
0x0040db0a  call 0x4078e0
0x0040db3c  lea  edi, [esp + 0x18]  ; → a sztring a [esp+0x14]-be kerül
0x0040db40  call 0x985ff0

0x0040db45  lea  ecx, [esp + 0x24]  ; a LastViewRoot2 burkolója
0x0040db49  call 0x4078e0
0x0040db7c  lea  edi, [esp + 0x10]  ; (push edx után → a [esp+0xc]-be)
0x0040db80  call 0x985ff0
```

#### A hozzárendelés

```asm
0x0040db85  mov  edi, dword ptr [esp + 0xc]    ; edi = LastViewRoot2
0x0040db89  mov  esi, dword ptr [esp + 0x14]   ; esi = LastViewRoot
0x0040db8d  test esi, esi
0x0040db8f  je   0x40dc35                       ; üres → SetView("flat", 1)
0x0040dbad  push 1
0x0040dbaf  push esi                            ; SetView(LastViewRoot, 1)
0x0040dbb2  call 0x575130
0x0040dbb7  test edi, edi                       ; …majd a LastViewRoot2
0x0040dc30  push 0
0x0040dc32  push edi                            ; SetView(LastViewRoot2, 0)
```

| kulcs | nézet-rekesz | mi történik, ha üres |
|---|:---:|---|
| **`LastViewRoot`** | **1** (elsődleges) | a `"flat"` lép a helyébe, szintén `1`-gyel |
| **`LastViewRoot2`** | **0** (másodlagos) | **kimarad** — nincs helyettesítés |

#### Amit ez jelent

A program **két nézet-gyökeret** tart nyilván, és **csak az elsődlegesnek
van tartaléka**. Ha a másodlagos hiányzik, a hozzá tartozó rekesz üresen
marad — a program nem esik vissza semmire.

*Bizonyítottsági fok: megerősített* (a két olvasás célcíme, a két
kicsomagolás és a hozzárendelés végigkövetve).

## A keresősáv teljes eleme-listája a forrásból (2026-08-16)

A 4.1 szakasz a keresősávot **képernyőképről** olvasta ki. Most megvan a
**forrásadat**: `searchcontainer.tre` (125 sor), és a felületkód
(`0x00660c80`, 5 524 bájt; `0x005d47e0`) ugyanezt a hét azonosítót
hivatkozza.

### A sáv elemei

| elem | horgony | megjegyzés |
|---|---|---|
| `searchcontainer/searchbase` | bal-fent-jobbra | a háttér |
| `searchcontainer/search` | bal-fent-jobbra | a beviteli mező |
| `searchcontainer/search_icon` | bal-fent | a nagyító |
| `searchcontainer/searchclr` | **jobb**-fent | törlés — alapból **rejtett** |
| `searchcontainer/searchautocomplete` | a mező alatt (X: `−25 … +28`, Y: `0 … 100`) | a javaslat-lista — alapból **rejtett** |
| `searchcontainer/searchbutton` | **jobb**-fent | a keresési beállítások — alapból **rejtett** |
| `searchcontainer/filter_label` | bal, Y `−4` | a **„Szűrők"** felirat, `m_displayfont12` |
| `searchcontainer/filterbase` | bal-fent | az öt szűrőgomb alapja |
| `searchcontainer/timecontainer_label` | bal-fent | a dátumsáv felirata |
| `searchcontainer/timecontainer` | bal-fent | a **dátum-tartomány** csúszka |

### Az ÖT szűrőgomb — sorrendben

| # | azonosító | buboréksúgó (angolul a forrásban) |
|---:|---|---|
| 1 | `searchcontainer/starsearch` | Show starred photos only |
| 2 | `searchcontainer/facesearch` | Show only photos with faces |
| 3 | `searchcontainer/moviesearch` | Show movies only |
| 4 | `searchcontainer/webview` | Show uploads to web albums only |
| 5 | `searchcontainer/geotagsearch` | Show only photos with geotag |

Mindegyik gomb **két ikont** tart: `<név>_icon_0` (kikapcsolt, látszik) és
`<név>_icon_1` (bekapcsolt, alapból rejtett). A kattintás a `showtarget` /
`hidetarget` párral cseréli őket — vagyis a be/ki állapot **két külön kép**,
nem szín- vagy átlátszóság-váltás.

Mind az öt `Property mousedown 1`, és mind az öt ugyanazt a
`SharedHandler searchcontainer/tip hottip searchcontainer/filter_label`
sort viseli: **egérrel fölé húzva a „Szűrők" felirat helyén jelenik meg a
súgó** — nem lebegő buborékban.

### ⚠️ A súgók NINCSENEK lefordítva — és a Google is tudta

A fájl végén, közvetlenül a súgók előtt egy **fejlesztői megjegyzés** áll:

```
#-----------------------------------------------------------
# Move below to external resource for i18n
#-----------------------------------------------------------
```

Vagyis a keresősáv hét szövege (öt súgó + a „Filters" felirat + két további
súgó) **soha nem került át** a fordítható erőforrásokba. Ugyanez a helyzet a
videó vezérlősávjánál (`video_control_bar.tre`).

| erőforrás | angol szöveg | javasolt magyar |
|---|---|---|
| `filter_label` (Label) | Filters | **Szűrők** |
| `starsearch` | Show starred photos only | **Csak a csillagozott fotók** |
| `facesearch` | Show only photos with faces | **Csak az arcot tartalmazó fotók** |
| `moviesearch` | Show movies only | **Csak a videók** |
| `webview` | Show uploads to web albums only | **Csak a webalbumba feltöltöttek** |
| `geotagsearch` | Show only photos with geotag | **Csak a helyadattal ellátott fotók** |
| `timecontainer_label` | Filter by date range | **Szűrés dátumtartomány szerint** |
| `searchclr` | Clear your search | **Keresés törlése** |

### A másodpéldány-keresés NEM ezek egyike

A `searchoptions/dupesearch` a **keresési beállítások** felugró paneljében
él (`thumbui/searchgroupcontainer`, amit a `searchbutton` nyit meg), nem a
szűrő-ikonok között. A menütétele: `eMenuTools::ID_DUPES` → **„Fájlok
másodpéldányainak megjelenítése"**.

### A sáv magassága

```
Handler varbutton searchtop 62
#Handler varbutton searchtop 114      ← kikommentezve
```

A `searchtop` változó a keresési beállítások panelének megnyitásakor
**62**-re vált (a kikommentezett `114` egy korábbi, nagyobb panelé).

### ❌ Nálunk négy szűrő van, nem öt

A `MainToolbar.qml` négy ikont mutat (★, ☺, ⚲, ▤); a **`webview`**
(webalbumba feltöltöttek) hiányzik. Ez védhető — a Picasa Webalbumok
szolgáltatás halott —, de **a sorrend is más**: az eredeti
★ · arc · videó · web · geo, nálunk ★ · arc · geo · méret.

*Bizonyítottsági fok: megerősített* (a `searchcontainer.tre` teljes
tartalma, és a felületkód két helyen ugyanezt a hét azonosítót hivatkozza).
