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
     a `Theme.qml` `monoFamily` tokenje) — az eredeti screenshoton az évszám ugyanaz a
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

*Forrás: `thumbui.tre:412` (`thumbui/flatview`) · `thumbui.tre:406` (`thumbui/folderview`) · `thumbui.tre:421` (`thumbui/folderviewpopup`).*

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

*Forrás: `scratch.tre:36` (`scratch/album`) · `thumbui.tre:724` (`thumbui/headerproto`).*

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
- ~~Mindkettő a natív Windows-króm (nem egyedi Picasa-stílus)~~ ⛔
  **HELYESBÍTÉS (2026-08-16): NEM natív.** A Picasának **saját
  görgetősáv-grafikája** van (`scrollart/`, 46 réteg a `respack.yt`-ban),
  Windows- ÉS Mac-változattal, és **négy** gombbal, nem kettővel — lásd
  „A görgetősáv SAJÁT vezérlő, négy gombbal" alább. — a
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
| Eszköztár magassága | ~38–39px | **35px** (#587 óta; előtte 34) | a forrásból vett sávhatár a `searchtop` = 35, ld. `konyvtar-ablak-meretek.md` 2. |
| Bal panel szélessége | ~236–243px @1920px | `SplitView.preferredWidth: 230` @1280px | a képernyőképes mérés a forrás **240 px fix** értékét erősíti meg (`thumbui.tre` `HLISTOFFSET2`) — nem arány. A `design-guide.md` régi 386px@1920/250px@1280 becslése téves volt, a #587 kijavította; az alapérték 240-re állítása még nyitva |
| Panel-sor magassága | ~22px (mérve a mappasorok között) | `height: 22` (`FolderPane.qml` delegate) | **egyezik** |
| Infó-csík magassága | ~13–14px | 20px | ld. 5.3/1 |
| Tálca magassága | **105px** (a `thumbui.tre` `publishbottom`-ja; a screenshot le volt vágva, a forrás kiváltja) | 52px (fő sáv) + 20px (infó) = 72px | **33px-szel kisebb nálunk**, és a tálca tartalma is más szerkezetű (#587 nyitva) |

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

*Forrás: `searchcontainer.tre:31` (`searchcontainer/filter_label`) · `searchcontainer.tre:86` (`searchcontainer/filterbase`) · `searchcontainer.tre:12` (`searchcontainer/search`) — és további 7 elem ugyanott.*

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

*Forrás: `searchcontainer.tre:49` (`searchcontainer/facesearch`) · `searchcontainer.tre:79` (`searchcontainer/geotagsearch`) · `searchcontainer.tre:59` (`searchcontainer/moviesearch`) — és további 2 elem ugyanott.*

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

*Forrás: `searchoptions.tre:97` (`searchoptions/dupesearch`) · `thumbui.tre:554` (`thumbui/searchgroupcontainer`).*

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

## ⛔ A görgetősáv SAJÁT vezérlő, négy gombbal (2026-08-16)

A 3.1 szakasz azt írta, hogy a görgetősáv **natív Windows-króm**. A
`respack.yt` ezt megcáfolja: a `scrollart/` **46 réteget** tartalmaz, a
`throttle/` pedig **22-t** — a Picasának **saját, két platformra rajzolt
görgetősáv-grafikája** van.

### Négy gomb, nem kettő

A `throttle` (a görgetősáv) felülről lefelé:

| # | elem | y | méret (win) | mit csinál |
|---:|---|---:|---|---|
| 1 | `prevalbum` | **0** | **16 × 24** | ugrás az **előző albumra** |
| 2 | `albumscrolltop` | **24** | **16 × 24** | görgetés **fel** |
| — | `tilebg` (sín) | 48 | 16 × 273 | csempézett háttér |
| — | `throttlethumb` | 219 | **16 × 64** | a fogantyú |
| 3 | `albumscrollbottom` | **321** | **16 × 24** | görgetés **le** |
| 4 | `nextalbum` | **345** | **16 × 24** | ugrás a **következő albumra** |

A teljes magasság a tervezővásznon **369**, a szélesség **16**
(Mac-változatban **15**).

> **Az album-ugró gombpár a Picasa saját találmánya.** Natív
> görgetősávon nincs ilyen: a felső ▲▲ az előző, az alsó ▼▼ a következő
> albumra ugrik — így egy hosszú, sokalbumos listában is gyorsan lehet
> navigálni.

### A lapozó félterek

*Forrás: `throttle.tre:9` (`throttle/pagedown`) · `throttle.tre:3` (`throttle/pageup`).*

```
throttle/pageup:  YConstraint 1, 0.5, 0      # a sín tetejétől a KÖZEPÉIG
throttle/pagedown: YConstraint 0, 0.5, 0     # a közepétől az ALJÁIG
```

A sín két fele **lapozó terület** (`pageup` / `pagedown`), egyenként
**16 × 184**. Mindkettő és **mind a négy gomb** `m_autorepeat` — nyomva
tartva ismétel.

A `pageup`/`pagedown` `Property normalcursor 1` — vagyis a sínen a
**normál egérmutató** marad (nem vált kéz- vagy szövegkurzorra).

### Két platform, három színvariáns

| utótag | mire |
|---|---|
| `_win` | Windows, **16** széles, gombok 16 × 24 |
| `_mac` | Mac, **15** széles, gombok 15 × 19 / 15 × 25 |
| `_mac_gray` | Mac szürke (grafit) rendszertéma |

A `decelev*` réteg-család (`decelevMacGraphite`, `decelevMacBlue`,
`decelevMacGray`…) a **pozíciójelző** (`throttleposition`, 16 × 3)
platform- és témaváltozatai.

Mind a négy gomb **három állapotképet** használ a szokásos
`(,<n>,<p>,<h>)` mintával — pl.
`button(,scrollart/up,scrollart/pressup,scrollart/hoverup): albumscrolltop_win`.

### ❌ Amiben eltérünk

| | eredeti | PicasaPy (`PicasaScrollBar.qml`) |
|---|---|---|
| szélesség | **16** (Mac 15) | 10 |
| gombok | **négy** (album ↑↑ · ↑ · ↓ · album ↓↓) | **nincs** |
| lapozó félterek | van, auto-ismétléssel | nincs |
| pozíciójelző | külön réteg (16 × 3) | nincs |
| stílus | **saját grafika**, két platformra | egyedi lapos sáv |

> A **10 px-es, gomb nélküli** sáv tudatos dizájndöntés volt
> (`design-guide.md`), és **maradhat** — de a mostani indoklás („az
> eredeti natív Windows-króm, tehát nem követendő") **téves**. Az
> eredeti saját, gondosan megrajzolt vezérlő volt, **album-ugró
> gombokkal**, amiknek nálunk nincs megfelelője.
>
> **Az album-ugrás funkciója külön mérlegelendő** — az nem stílus,
> hanem navigáció.

*Bizonyítottsági fok: megerősített* (a `scrollart/` 46 és a `throttle/`
22 rétege, plusz a `throttle.tre` teljes tartalma).

## ⛳ A keresősáv „ellenőrizni" pontjai SZÁMMAL — és a kétállású ikon EGYIRÁNYÚ (2026-09-12, 293. kör, #839)

A #839 táblájának utolsó sora *„a betűméret és az eltolás **ellenőrzése**"*
volt. „Ellenőrizni" nem szám: a fejlesztő abból nem tud betűt beállítani.
Ez a szakasz a hiányzó értékeket adja meg, forrásból.

### A „Szűrők" felirat — teljes leírás

```
searchcontainer/filter_label: thumbui/searchcontainer   (:31)
m_displayfont12                                          (:32)
m_offsetL                                                (:33)
YConstraint 0, 0, -4                                     (:34)
```

A makrók feloldva:

| makró | mit ad | érték |
|---|---|---|
| `m_displayfont12` | `fontname` | **Praxis Semi Bold/Heavy** |
| | `fontsize` | **12** |
| | `fontweight` | **400** |
| | `fonttrack` (betűköz) | **−1** |
| `m_offsetL` | `MaintainOffset left` | átméretezéskor a **bal** eltolás marad |
| `YConstraint 0, 0, -4` | függőleges | **−4** képpont |

⚠️ A `fontmacros_win.tre` és a `fontmacros_mac.tre` `m_displayfont12`-je
**bájtra azonos** — nincs platform-eltérés.

*Forrás: `searchcontainer.tre:31–34` · `fontmacros_win.tre:43–47` ·
`fontmacros_mac.tre:43–47` · `macros.tre:47–48`.*

### Az öt szűrőgomb — mind az öt BETŰRE azonos szerkezet

```
searchcontainer/<név>_icon_0: searchcontainer/<név>
searchcontainer/<név>_icon_1: searchcontainer/<név>
m_hidden                                   <- az icon_1-re vonatkozik
searchcontainer/<név>: searchcontainer/filterbase
m_offsetLT
Property mousedown 1
SharedHandler searchcontainer/tip hottip searchcontainer/filter_label
Property showtarget searchcontainer/<név>_icon_1
Property hidetarget searchcontainer/<név>_icon_0
```

A `<név>` sorrendben: `starsearch` (:39) · `facesearch` (:49) ·
`moviesearch` (:59) · `webview` (:69) · `geotagsearch` (:79).

### ⛔ A kétállású ikon a forrásból EGYIRÁNYÚ

A `showtarget`/`hidetarget` pár **csak a bekapcsolást** írja le: megmutatja
az `_icon_1`-et és elrejti az `_icon_0`-t. **Visszafelé nincs utasítás a
forrásban** — a kikapcsolás nem az erőforrásból jön, hanem kódból.

⇒ Aki a „két képállapot" sort pusztán ebből a `.tre`-ből valósítja meg,
**egyirányú kapcsolót** kap: a szűrő bekapcsol, és nem lehet kikapcsolni.
Ez a szakasz legfontosabb figyelmeztetése.

### A súgó helye — mind az ötnél ugyanaz

`SharedHandler searchcontainer/tip hottip searchcontainer/filter_label` ⇒ a
buboréksúgó szövege a **„Szűrők" felirat helyén** jelenik meg, nem lebegő
buborékban. Mind az öt gomb ugyanazt a `tip` kezelőt osztja.

*Forrás: `searchcontainer.tre:36–84` (az öt blokk), `:86`
(`searchcontainer/filterbase`).*

### Kontroll

A fájl **125 sor** — egyezik a #838 mérésével; a `searchcontainer/` előtagú
elemek száma **26**, köztük mind a tíz ikon (öt gomb × 2 állapot).

## ⛳ A görgetősáv NÉGY gombja: mind a négy EGY objektum négy vtábla-rekeszére megy (2026-09-12, 294. kör, #857)

A #857 „Ami NYITVA marad" szakasza egyetlen kérdést hagyott: **mit jelent az
„album" az ugrásnál.** A `.tre` csak a gombot adja meg, a viselkedést nem
— ez a szakasz a **működés** felé viszi a kérdést, és megadja a kezelők
pontos helyét.

### A szétosztó

Mind a négy gomb ugyanabban a névre illesztő láncban ül
(`0x005de13b`–`0x005de41c`), és mind a négy **paraméter nélküli
farokhívással** (`jmp eax`) megy tovább — ugyanarra az objektumra, a
gazdapanel **`+0x2a4`** tagjára:

| elem | a név címe | az összehasonlítás | a hívott vtábla-rekesz |
|---|---|---|---|
| `throttle/albumscrolltop` | `0x00c96818` | `0x005de176` | **`+0x20`** (8.) |
| `throttle/albumscrollbottom` | `0x00c96830` | `0x005de1e4` | **`+0x24`** (9.) |
| `throttle/nextalbum` | `0x00c9684c` | `0x005de334` | **`+0x3c`** (15.) |
| `throttle/prevalbum` | `0x00c96860` | `0x005de39a` | **`+0x40`** (16.) |

Mindegyik ág betűre azonos alakú:

```
lea ecx, [edx + 0x2a4]     ; a gazdapanel tagja
mov edx, [ecx]             ; a vtábla
mov eax, [edx + <rekesz>]
jmp eax                    ; FAROKHÍVÁS, argumentum nélkül
```

### Amit ez eldönt

1. **A négy gomb nem négy változata egy műveletnek.** A görgető pár (8., 9.)
   és az album-pár (15., 16.) a vtáblában **távol** van egymástól ⇒ külön
   interfész-metódusok, nem egy „lépj N-et" paraméterezett hívás.
2. **A művelet paraméter nélküli** — a cél-objektum tudja, mit kell tennie;
   a gomb csak jelez.
3. A gomb `m_autorepeat`-je (`throttle.tre`) ⇒ nyomva tartva **ismételt**
   hívás ugyanarra a rekeszre.

### ⛔ Amit ez NEM dönt el — a jegy kérdése NYITVA marad

Hogy a 16. rekesz **a listában a következő albumra** lép-e, vagy **a rács
következő szakaszfejlécére**, abból nem derül ki, hogy melyik rekeszt hívja.
Ehhez a `+0x2a4`-en ülő objektum **osztályát** kell azonosítani (RTTI a
vtáblájából), és a `+0x40` rekesz törzsét elolvasni.

**A következő gépi lépés:** a szétosztó gazdafüggvényének megkeresése
(`0x005de13b` körül), abból a `+0x2a4` tag írója, és onnan az RTTI.

### ⚠️ MÓDSZERTAN — a név MINŐSÍTETT, és ezen bukik a keresés

Az első pásztázásom **mind a hét elemnévre 0 találatot** adott — a
**kontroll-pozitívra is**, ezért egyetlen negatív állítást sem közöltem.
Az ok: a binárisban a név **minősítve** áll (`throttle/prevalbum`,
`0x00c96860`), a csupasz `prevalbum` pedig annak a **belsejébe** mutat
(`0x00c96869`), oda viszont semmi nem hivatkozik. A minősített címmel
mind a négy névre **3-3** találat jött.

*Forrás: a nevek `0x00c96818`–`0x00c96874` között, egy folytonos
névtáblában; a szétosztó `0x005de13b`–`0x005de41c`; a `.tre` oldala
`throttle.tre` (38 sor).*

## ⛳ A háttérművelet-jelző: gazda, megszakítás és geometria (2026-09-14, 304. kör, #3112)

*Forrás: a szövegtár `IBackgroundNotify::*` négy kulcsa
(`referencia/stringres-en-hu.tsv:1440–1443`), a megszakítás-kérdés
`0x00631d40`–`0x00631e3e`, a konstruktor `0x004197b0`, a lezáró
`0x004198a0`, a lekérdező `0x004198c0`, a `Cancel()` `0x00419970`, az
állapotjelzés hívóhelyei `0x00404b99` és `0x004197a1`, a felület
`activity.tre` + a `respack.yt` rétegfejlécei.*

A #2966 megépítéséhez hiányzott, hogy MI a jelző gazdája, mit tesz a
megszakítás, és hol ül pontosan. Mindhárom megvan, referencia-képernyőkép
nélkül.

### 1. Mit CSINÁL — a megszakítás valódi, nem látszat

A háttérműveletek közös ősosztálya (konstruktor `0x004197b0`, vtábla
`0x00c82988`) ezeket a mezőket tartja:

| eltolás | mit tárol | kezdőérték (`0x004197b0`) |
|---|---|---|
| `+0x48` | a művelet eseménykezelője | a konstruktor argumentuma |
| `+0x51` | **„megszakítást kértek"** jelző | `0` |
| `+0x52` | „a záró értesítés még hátravan" | `1` |
| `+0x54` | a felületi értesítő objektum | `0` (később kapja meg) |

**A megerősítő párbeszéd** (`0x00631d40`) mind a négy feliratot a
szövegtárból kéri (`0x00631d5e`, `0x00631db3`, `0x00631dd2`, `0x00631ded`),
majd `0x00631e17`-nél megnyitja a párbeszédet. A két ág:

```
0x00631e1f  test al, al
0x00631e23  mov byte [ebx+0x51], 1     ; IGEN  -> megszakítás kérve
0x00631e32  mov byte [ebx+0x52], 0     ; NEM   -> csak a záró jelzés törlődik
```

⭐ **A jelzőt a munkavégző tényleg OLVASSA:** a lekérdező rutin
(`0x004198c0`) a várakozás eredménye mellett a `+0x51`-et is vizsgálja
(`0x0041991c cmp byte [esi+0x51], al`), és ha az áll, „van tennivaló"
eredménnyel tér vissza. ⇒ **a megszakítás nem kozmetikai**: a
munkaciklus a jelzőn keresztül értesül róla. A `Cancel()` metódus
(`0x00419970`) ugyanezt a jelzőt állítja, miután a `+0x48` eseményt
elsütötte.

**A felületi értesítés** a `+0x54` objektum `vtbl+0x15c` rekeszén megy, egy
számmal:

| érték | hol | mit jelent |
|---|---|---|
| `0` | `0x00404b99` (közvetlenül egy `1,0`-s haladás-hívás után) | **indulás / megjelenés** |
| `2` | `0x004197a1` és `0x004198af`, mindkét helyen a `+0x52` törlésével | **vég / eltűnés** |

⛔ **Az `1`-es értékre nincs hívóhely ebben a három pontban** — hogy létezik-e
köztes „haladás" állapot, **nincs kimérve**.

### 2. A négy felirat — a magyar fordítás egyik sora GYANÚS

| kulcs | angol | magyar |
|---|---|---|
| `IBackgroundNotify::canceltitle` | Want to Cancel? | **Kilép?** |
| `IBackgroundNotify::cancel` | Do you want to cancel this operation? | Megszakítja ezt a műveletet? |
| `IBackgroundNotify::cancelyesbutton` | Cancel Operation | Művelet megszakítása |
| `IBackgroundNotify::cancelnobutton` | Don't Cancel | Megszakítás mellőzése |

⚠️ A címsor magyarul „Kilép?" — az angol „Want to Cancel?"-hez képest ez
**más jelentés** (kilépés vs. megszakítás). A saját fordításunkban ezt nem
kell átvenni.

### 3. Az elem-készlet és a geometria — a `respack.yt`-ból

*Forrás: `respack.yt:77330` (`docbounds`), `:77347` (`vbutton`), `:77364`
(`base`), `:77381` (`spinner`), `:80144` (`spinnermask`), `:81437`
(`thumbbounds`), `:81454` (`activitythumb`), `:3235550` (`thumbui/docbounds`),
`:3262712` (`thumbui/clip(activity)`); a jelzők `activity.tre:1–18`.*

A jelző **önálló dokumentum** (`activity/base: root`), amit a könyvtárnézet
`activitycontainer` néven ágyaz be. Hat eleme van:

| elem | x0 | y0 | x1 | y1 | méret | `.tre` jelzők |
|---|---:|---:|---:|---:|---|---|
| `activity/docbounds` | 0 | 0 | 35 | 28 | 35 × 28 | — |
| `activity/base` | 0 | 0 | 35 | 28 | 35 × 28 | gyökér |
| `activity/spinner` | 5 | 1 | 31 | 27 | **26 × 26** | `m_centerXY`, `m_hidden` |
| `activity/spinnermask` | 0 | 0 | 35 | 28 | 35 × 28 | `m_centerXY` |
| `activity/activitybutton` (`vbutton`) | 7 | 0 | 29 | 28 | **22 × 28** | `m_hidden` |
| `activity/thumbbounds` (`rect`) | 0 | 0 | 35 | 28 | 35 × 28 | — |
| `activity/activitythumb` (`bicubic`) | 0 | 0 | 35 | 28 | 35 × 28 | `m_centerXY`, `m_shadow`, `m_hidden` |

**A helye a könyvtárnézetben:** a `thumbui` tervezővászna **800 × 534**, és a
`thumbui/clip(activity): activitycontainer` réteg **x 760–795, y 5–33**.
⇒ a jelző a **jobb felső sarokban** ül, a felső széltől **5**, a jobb széltől
**5** képpontra, mérete **35 × 28**.

⭐ **Három elem alapból REJTETT** (`m_hidden`): a pörgő, a gomb és a
bélyegkép — csak a maszk és a keret látszik. ⇒ a jelző **nem üres helyet
foglal**: a `spinnermask` és a `thumbbounds` mindig ott van, a tartalom
jelenik meg.

⭐ **Van bélyegkép-eleme** (`activitythumb`, bikubikus, árnyékkal): a jelző
nem csak pörgőt mutat, hanem a feldolgozott elem képét is.

### 4. Testvér-példányok — ugyanez a dokumentum három helyen

*Forrás: `respack.yt:81752`–`:85893` (`activitycapture`), `:151238` és
`:185217` (a két felvevő-panel), `:850491` (`editpanel/clip`), `:884285`
(`editpanelactivity/docbounds`); a szűkített készlet `editpanelactivity.tre:1–9`.*

| dokumentum | hol ágyazódik be |
|---|---|
| `activity` | `thumbui/clip(activity)` — a könyvtárnézet |
| `activitycapture` | `capturemoviepanelpopup` és `canoncapturemoviepanelpopup` |
| `editpanelactivity` | `editpanel/clip(editpanelactivity)` |

Az `editpanelactivity` **szűkített**: csak `spinner` + `spinnermask`, se
gomb, se bélyegkép. ⇒ a szerkesztőben a jelző **nem megszakítható**.

### 5. ⛔ Amit ez NEM mond ki

- **Az `1`-es állapot** (ha van) hívóhelye nincs meg.
- **Melyik művelet regisztrálja magát** a jelzőre, nincs leltározva — a
  `+0x54` írói adnák meg, azt ez a kör nem pásztázta végig.
- A `spinner` rétegének **2763 bájtos** tartalma (fázisképek?) nincs
  kibontva; az animáció ütemét nem mértük.

## ⛳ Az album-ugró gombpár a KÖVETKEZŐ SZAKASZFEJLÉCRE ugrik (2026-09-15, 310. kör, #857)

A 294. kör (fent) kimérte, hogy mind a négy görgetősáv-gomb a gazdapanel
`+0x2a4` tagjának négy vtábla-rekeszére megy. Ez a kör megnyitotta a
rekeszeket, és ezzel a jegy nyitott kérdése (*„mit jelent az »album« az
ugrásnál"*) eldőlt.

### A `+0x2a4` tag: az `INavigation` részobjektum a `CThumbUI`-ban

A gazda konstruktora (`0x005643e0`) egymás után 26 interfész-vtáblát tölt
be; a mienk a **`0x005644b5`**-ös sor:

```
0x005644b5  c785a40200009c04c900   mov dword ptr [ebp+0x2a4], 0xc9049c
```

RTTI a vtábla `-4` rekeszéből (`RTTICompleteObjectLocator` → `TypeDescriptor`):

| vtábla | RTTI-név | hol íródik |
|---|---|---|
| `0x00c9049c` | **`.?AVINavigation@@`** | `0x005644b5` (ctor, tiszta virtuális) |
| `0x00c90754` | **`.?AVCThumbUI@@`** | `0x005645da` és `0x005653da` |

A négy rekesz tartalma a `0x00c90754` vtáblából kiolvasva:

| gomb | rekesz | cím |
|---|---|---|
| `throttle/albumscrolltop` | `+0x20` | `0x00578460` |
| `throttle/albumscrollbottom` | `+0x24` | `0x00578500` |
| `throttle/nextalbum` | `+0x3c` | **`0x00578920`** |
| `throttle/prevalbum` | `+0x40` | **`0x00578a90`** |

A törzsekben az `ecx` **a részobjektumra** mutat, nem a `CThumbUI` elejére.
Ez nem feltevés: mindkét album-ugró visszaigazítja, mielőtt `CThumbUI`-szintű
függvényt hív — `add ebp, 0xfffffd5c` (`0x00578a53`) és
`add edi, 0xfffffd5c` (`0x00578ae4`), ahol `0xfffffd5c = −0x2a4`.
Ebből: `[részobj+0x1c] = CThumbUI+0x2c0` (a sorlista) és
`[részobj+0xc0c] = CThumbUI+0xeb0` (a nézet-/görgetésmodell).
Kereszt-ellenőrzés: egy másik `CThumbUI`-metódus ugyanezt a listát
`mov eax, [edi+0x2c0]` alakban adja át ugyanannak a lekérőnek
(`0x005e03a8` → `call 0x004ae4e0`).

### A sorlista és a rekord

`0x004ae4e0(lista EAX-ben, index, &rekord)` — zárolt elemkérő:

| mező | hely | mérés |
|---|---|---|
| elemtömb | `[lista+0x158]` | lépésköz **56 bájt** (`lea edx,[ebp*8]; sub edx,ebp; lea esi,[eax+edx*8]`, `0x004ae541`) |
| elemszám | `[lista+0x15c] >> 1` | `0x004ae52b` |
| másoló | `0x004ae600` | `0x34` bájtot másol; `+0xc` és `+0x10` hivatkozásszámlált sztring |
| **típus** | **rekord `+0x30`** | ld. lent |

A nézetmodell (`CThumbUI+0xeb0`) mezői:

| mező | jelentés | mérés |
|---|---|---|
| `+0x2f8` | az **első látható sor** indexe | `0x009d2821`, `0x009d283f` |
| `+0x320` | a látható sorok **száma** | `0x00578943`, `0x00578b02` |
| `+0x298` | **2 × sorszám** (mindenhol `>> 1`) | `0x0057894f`, `0x00578a0c` |
| `+0x30c` | a beállított célsor | `0x00578a24` |

### A keresés — előre és hátra, tükörképben

```
nextalbum (0x00578920):  i = [+0x320] + [+0x2f8] + 1 ;  amíg i < [+0x298]>>1   (0x00578943–0x005789da)
prevalbum (0x00578a90):  i = [+0x320] + [+0x2f8] − 1 ;  amíg i >= 0            (0x00578b02–0x00578b85)
```

Mindkettő ugyanazt a **találati feltételt** használja a rekord `+0x30`
típusmezőjére:

```
típus == 1                      -> TALÁLAT                 (0x005789b5 / 0x00578b64)
típus ∈ {5, 6, 7} ÉS rekord+0x20 == 0 -> TALÁLAT           (0x005789ba–0x005789ce / 0x00578b69–0x00578b7d)
egyébként                       -> lépj tovább
```

Találatkor:

```
[nézet+0x30c] = újpozíció                       (0x00578a24)
call 0x009d2810(nézet, újpozíció, 1)            (0x00578a2a)
```

és `0x009d2810` a `[nézet+0x2f8]`-at, azaz az **első látható sort** állítja
az új értékre (`0x009d2821`, `0x009d283f`). Korlát: `0 ≤ újpozíció <
[+0x298]>>1` (`0x00578a12`–`0x00578a1a`).

### Mit jelent a `{1, 5, 6, 7}` típushalmaz — a független megerősítés

Pontosan ugyanezt a négy értéket vizsgálja a **`CAlbumList`** is, amikor a
ragadós (sticky) fejlécet rajzolja:

```
0x00762752  cmp eax, 1 / 5 / 6 / 7   -> egy közös ágra            (0x00762746: ugyanaz a 0x004ae4e0 lekérő)
```

és ugyanez a függvény (`0x00762540`) a típusokhoz **fejléc-grafikát**
rendel: `CAlbumList::liststicky2` (`0x00cb26a0`), `…sticky3`
(`0x00cb26b8`), `…sticky5` (`0x00cb26d8`), `…sticky6` (`0x00cb26f0`),
`…sticky7` (`0x00cb2708`) — a `.text`-ben ezek a nevek **kizárólag** ebben a
függvényben szerepelnek.

⇒ **A `{1, 5, 6, 7}` a fejléc-(szakasz-)sorok típuskészlete.** Az album-ugró
gombpár tehát nem egy külön albumlista indexét lépteti, hanem a saját
sormodelljében megkeresi a **következő/előző szakaszfejléc-sort**, és azt
görgeti a nézet tetejére.

### Kontroll-mérés

A másik két rekesz (`+0x20` és `+0x24`, azaz a sima fel/le görgetés)
**nem pásztáz sorokat**: a `0x00578460` és a `0x00578500` egy feltételvizsgálat
után a saját vtáblája `+0x28` / `+0x2c` rekeszét hívja `0` argumentummal
(`0x00578489`–`0x00578492`, `0x00578529`–`0x00578532`). Ha a módszerem a
típuspásztázást „mindenhová" belelátná, itt is látnia kellett volna — nem látja.

### Ami NYITVA marad

1. **A rekord `+0x20` mezője**, ami az 5/6/7 típusú fejléceket kapuzza
   (`== 0` kell a találathoz). A `0x004ae600` másoló sima dwordként viszi át
   (`0x004ae6b2`), tehát a jelentése a lista **feltöltőjéből** olvasható ki —
   ez a következő gépi lépés.
2. **A `prevalbum` előfeltétele.** Csak a hátrafelé ugrás előtt fut egy
   `0x0076a4b0` + `0xc29e1a` számítás, és az eredményt két konstanshoz méri:
   `0x00c7dd30 = 0.1` és `0x00cf3ad8 = 0.9` (`0x00578ac8`–`0x00578ae2`). Az
   FPU-státusz szerint **v ≤ 0.1 vagy v ≥ 0.9 esetén** indul a fenti
   fejléc-keresés; a `0.1 < v < 0.9` sávban helyette `0x006dcc40(CThumbUI)`
   fut.
   ✅ **Mindkettő azóta kimérve** (#3143) — ld. a következő szakaszt: a
   küszöbhöz hasonlított érték `fmod(v, 1.0)`, és a `0x006dcc40` a
   **webablakot** kezeli, nem görget.

---

## ⛳ Az album-ugrás két nyitott részlete: a `prevalbum` NEM tükörképe a `nextalbum`-nak (2026-09-15, #3143)

*Forrás: `FUN_0076a4b0` (327 b) teljes törzse · a hívó feltétel
`0x00578ac8`–`0x00578ae2` (`0x00c7dd30 = 0.1`, `0x00cf3ad8 = 0.9`) · a
sorrekord másolója `FUN_004ae600` (217 b).*

### 1. ⭐ Mit mér a `prevalbum` előfeltétele: HOL ÁLLUNK A SORON BELÜL

A `FUN_0076a4b0` végigmegy a lista sorain (`[this+0x300]` mutatótömb,
`[this+0x304]>>1` darabszám, `[this+0x30c]` a soronkénti 16 bájtos
téglalap-tömb), és megkeresi azt a sort, amelyik a **jelenlegi
görgetés-pozíciót** (`v_int`, a `[this+0x150]`-ből számolva) tartalmazza:

```c
// szűrés: nem üres téglalap, és a pozíció benne van
if (r.bal < r.jobb && r.fent < r.lent && r.fent <= v_int && v_int <= r.lent) {
    magassag = r.lent - r.fent;                 // 0x0076a596
    v = (magassag == 0) ? 1.0                   // 0x0076a5ad: fld1
                        : (v_int - r.fent) / magassag;   // 0x0076a5c5
    v = min(v, 1.0);                            // 0x0076a5c7 fcom st(1)
}
```

⇒ **`v` a nézet viszonyítási vonalának helye a JELENLEGI soron belül.**

⛔ **HELYESBÍTÉS (#3143, 2. kör): a `FUN_0076a4b0` NEM `[0,1]`-re normált
értéket ad.** A törzs a talált sor **indexét** is hozzáadja: `mov eax, ebx;
mov [esp+0x10], eax; fild dword ptr [esp+0x10]` (`0x0076a582`–`0x0076a58a`),
majd a végén `faddp st(1)` (`0x0076a5d6`). ⇒ **`v = sorindex +
soron_belüli_hányad`**, tehát a `0.1`/`0.9` küszöb önmagában csak a nulladik
sorban volna értelmes.

⭐ **A hiányzó lépés a hívóban van, és mérve van: `fmod`.** A
`fld1; call 0x00c29e1a` (`0x00578ac1`–`0x00578ac3`) a `_CIfmod` CRT-belső
függvény — a `0x00c29e1a` egy 10 bájtos thunk
(`mov edx, 0xd49170; jmp __cintrindisp2`), és a `0xd49170`-es diszpécser-tábla
első eleme a hossz-előtagos **`"fmod"`** literál (`04 66 6d 6f 64`, fájloffszet
`0x949170`). ⇒ a küszöbhöz hasonlított érték **`fmod(v, 1.0)`**, azaz `v`
**törtrésze** — a sorindex kiesik, és a `0,1`/`0,9` küszöb minden soron
ugyanazt jelenti.

### 2. ⇒ A feltétel jelentése: „sorhatáron állunk-e"

A hívó `v ≤ 0.1 || v ≥ 0.9` esetén indítja a fejléc-keresést, a
`0.1 < v < 0.9` sávban helyette a `FUN_006dcc40(CThumbUI)` fut.

| `v` | hol vagyunk | mi történik |
|---|---|---|
| `≤ 0,1` vagy `≥ 0,9` | a sor **tetején/alján**, azaz (majdnem) szakaszhatáron | ugrás az **előző** szakaszfejlécre |
| `0,1 … 0,9` | a sor **közepén** | `FUN_006dcc40` — más művelet |

⭐ Ez a **„zenelejátszó-viselkedés"**: a Vissza gomb előbb a JELENLEGI
szakasz elejére visz, és csak ha már ott vagyunk, ugrik az előzőre. A
`nextalbum`-nál ilyen feltétel **nincs** — a két gomb tehát **nem
tükörkép**, és a másolásuk hibás volna.

⛔ **HELYESBÍTÉS (#3143, 2. kör): a `FUN_006dcc40` NEM görgetés.** A
korábbi kör „összefér a »görgess a jelenlegi sor elejére« olvasattal"
megjegyzése téves irányba mutatott; a törzs kimérve mást csinál:

| lépés | cím | mit tesz |
|---|---|---|
| index | `0x006dcc57`–`0x006dcc66` | `i = [ui+0xeb0]+0x320 + [ui+0xeb0]+0x2f8`; `i == −1` ⇒ azonnali `0` |
| rekord | `0x006dcc7e`–`0x006dcccb` | a kimeneti rekordot `0xff`-fel tölti (`+0x00…+0x08`), a két sztringet **nullázza** (`+0x0c`, `+0x10`), majd `FUN_004ae4e0([ui+0x2c0], i, &rek)` |
| **webablak** | `0x006dcd08` | `FUN_009c2fc0("thumbui/webwindow")` — ha nincs ilyen vezérlő, kilép |
| böngésző | `0x006dcd73` | egy 16 bájtos objektumot hoz létre **`"about:blank"`** kezdőcímmel |
| **ugyanaz a kapu** | `0x006dce03`–`0x006dce12` | `típus ∈ {6,7}` **ÉS** `rekord+0x20 == 0` |
| szomszéd | `0x006dce19`–`0x006dce21` | `FUN_004ae6e0([ui+0x2c0], i, &rek)` |

És a `FUN_004ae6e0` (360 b) a **következő** rekordot csak akkor adja vissza,
ha annak `+0x10` sztringje **megegyezik** a jelenlegiével
(`FUN_00987030`, `0x004ae78e`, a hamis ágon azonnali kilépés) — tehát a
`+0x10` a sorok **csoportkulcsa**.

⇒ A `0,1 … 0,9` sávban a `prevalbum` a **webablakot** kezeli a felül álló
sor rekordja szerint, nem görget. A „zenelejátszó-viselkedés" olvasata
**ennyiben helyesbítendő**: a feltétel igaz ága (a fejléc-keresés) áll, a
hamis ága nem a jelenlegi szakasz elejére visz.

### 3. A sorrekord mezőkiosztása — a `+0x20` szomszédai

A másoló (`FUN_004ae600`) mezőnként visz át, ezért a rekord alakja
leolvasható róla:

| eltolás | méret | megjegyzés |
|---|---|---|
| `+0x00`, `+0x04` | dword | |
| `+0x08` | **word** | (a másoló `mov dx, [esi+8]` alakban viszi) |
| `+0x0c`, `+0x10` | dword | **hivatkozásszámlált sztring** (a másoló elengedi a régit) |
| `+0x14` | dword | |
| `+0x18`, `+0x19`, `+0x1a` | **bájt** | három logikai jelző |
| `+0x1c` | dword | |
| **`+0x20`** | **dword** | az ugrási cél kapuja (`== 0` ⇒ az 5/6/7 típus is cél) |
| `+0x24`, `+0x28`, `+0x2c` | dword | |
| **`+0x30`** | **dword** | a **TÍPUS** |
| — | — | a rekord **teljes mérete 56 bájt** (`0x38`); a `+0x34` kitöltés |

⛔ **HELYESBÍTÉS (#3143, 2. kör): a TÍPUS a `+0x30`, nem a `+0x08`.** A
korábbi tábla a másoló első word-mozgatását vette típusnak, és a `+0x30`-at
egyáltalán nem sorolta fel, pedig a másoló azt is átviszi
(`0x004ae6ca`/`0x004ae6cf`). Három független mérés:

1. `FUN_004ae6e0` a rekordot közvetlenül indexeli, és a típust a `+0x30`-on
   olvassa: `mov ecx, [eax+0x30]; cmp ecx, 6; je …; cmp ecx, 7`
   (`0x004ae74a`–`0x004ae755`);
2. ugyanott a **következő** rekord típusa `[eax+0x68]`
   (`0x004ae766`) — és `0x68 − 0x30 = 0x38 = 56`, azaz pontosan a lekérő
   lépésköze (`0x004ae541`);
3. a `FUN_006dcc40` verem-számtana: a kimeneti rekord az `esp+0x20`-on áll,
   a `+0x20` mező vizsgálata `cmp dword ptr [esp+0x40], 0` (`0x006dce0d`),
   a típusé pedig `[esp+0x50]` = rekord `+0x30` (`0x006dcdf6`, `0x006dce03`).

⚠️ **Két külön „+0x20" van a képben** — ne keverd őket. A **LISTA** `+0x20`
és `+0x24` mezője a konténer **újrabelépő zárja**: mindhárom listametódus
(`0x004ae290`, `0x004ae4e0`, `0x004ae6e0`) ugyanazzal a prológussal indul —
`call [0xc40284]` (a szál azonosítója), `[lista+0x20]`-hoz hasonlítás,
egyezésnél `[lista+0x24]++`. A **REKORD** `+0x20`-a ettől független mező.

⛔ **A rekord `+0x20`-ának JELENTÉSE továbbra is nyitott**, de a hatóköre
szűkült: a `FUN_006dcc40` **ugyanazt a kaput** használja
(`típus ∈ {6,7}` ÉS `rekord+0x20 == 0`, `0x006dce03`–`0x006dce12`), tehát a
mező nem az ugrás sajátja. A megszerzés útja változatlan: a
`[lista+0x158]` tömböt **feltöltő** függvény. ⛔ **Negatív lelet:** a
feltöltő NEM a lista saját metódusai közt van — a `+0x30`-ra `1/5/6/7`
immediate-et író függvényeket a teljes `.text`-en végigpásztázva egyetlen
találat sem esett a `0x0040…–0x0080` app-tartományba nem-verem bázissal,
tehát a rekord a **hívó vermén** épül, és onnan másolódik be.

## ⛳ Az album-ugrás két nyitott részlete: a `fmod`-os előfeltétel MEGVAN, a `+0x20` alapértéke −1 (2026-09-15, 313. kör, #3143)

*A 310. kör (fent) két kérdést hagyott nyitva: mi a sorrekord `+0x20` mezője,
és mit mér a `prevalbum` 0,1/0,9-es előfeltétele. A második LEZÁRULT, az első
szűkült — mindkettő mérve.*

### 1. A `prevalbum` előfeltétele: a soron belüli görgetés TÖRTRÉSZE

A lánc három lépése, mindegyik kiolvasva:

```
0x00578abc  call 0x0076a4b0      ; v0 = törtsor-pozíció (ld. lent)
0x00578ac1  fld1                 ; 1.0
0x00578ac3  call 0x00c29e1a      ; v = fmod(v0, 1.0)  -> a TÖRTRÉSZ
0x00578ac8  fcomp [0x00c7dd30]   ; 0,1
0x00578ad7  fcomp [0x00cf3ad8]   ; 0,9
```

**A `0x00c29e1a` = `fmod`, bizonyítva.** A stub (`mov edx, 0x00d49170; jmp …`)
egy CRT-leíróra mutat, amelynek első mezője a **hosszal előtagolt `"fmod"`**
név (`0x00d49170`: `04 'f' 'm' 'o' 'd'`), a `+0x10`-es mezője pedig a
megvalósításra (`0x00c29e24`) — az pedig a klasszikus `fprem`-hurok
(`0x00c29e2f fprem`, `0x00c29e3d jp`, `0x00c29e3f fstp st(1)`).

**Mit ad a `0x0076a4b0`** (327 b): végigmegy a `[esi+0x30c]`-en álló, 16 bájtos
téglalapokon (bal/fent/jobb/lent), megkeresi azt, amelyik a görgetési
eltolást tartalmazza, és visszaadja

```
v0 = sorindex + min(1, (eltolás − sor_teteje) / sor_magassága)
```

(`0x0076a582`–`0x0076a5d8`; az eltolás a `[esi+0x150]`-ből és a paraméterből
jön, `0x0076a4df`, egész értékre kerekítve a `0x00c29990` CRT-hívással).

⇒ **`v` = mennyire van „belegörgetve" a nézet az aktuális sorba (0…1).**

**A polaritás** (FPU-státuszból, `test ah,5; jp`): **`v ≤ 0,1` vagy `v ≥ 0,9`**
esetén indul a fejléc-keresés; a **`0,1 < v < 0,9`** sávban helyette
`0x006dcc40(CThumbUI)` fut.

**Mit tesz a `0x006dcc40`** — a mért része: ugyanazt a nézetmodellt olvassa,
mint a két album-ugró (`[this+0xeb0]`), és a **határsort** kéri le
(`i = [nézet+0x320] + [nézet+0x2f8]`, ±0 nélkül; `0x006dcc57`–`0x006dcc5d`),
ugyanazzal a `0x004ae4e0` lekérővel és ugyanazzal az alapértelmezett
rekorddal (`mov dword [esp+0x58], 0xa`, `0x006dccc3`) ⇒ az **aktuális** sorra
vonatkozik, nem a következő fejlécre.

⇒ **A két gomb tehát nem tükörkép:** a „előző album" először a sor közepéről
igazít, és csak a sor tetején/alján kezd fejlécet keresni. A „következő
album"-nak nincs ilyen előfeltétele.

### 2. A sorrekord `+0x20` mezője: alapértéke **−1**

A rekordnak két konstruktora van, mindkettő kiolvasva:

| konstruktor | mit állít |
|---|---|
| `0x004a06e0` (alap) | `[+0x00…+0x08] = 0xFF`, `[+0x09] = 0`, `[+0x0c] = [+0x10] = 0`, **`[+0x30] = 0x0A`** |
| `0x004a0720` (paraméteres) | ugyanaz a bájtsor, `[+0x0c]`/`[+0x10]` a két sztring, `[+0x14]`, `[+0x18]`, `[+0x19]`, `[+0x1a] = 0`, `[+0x1c] = 0`, **`[+0x20] = −1`**, `[+0x24] = 0`, `[+0x30]` = a típus-argumentum |

**Kontroll-mérés:** az alap-konstruktor `[+0x30] = 0x0A`-ja pontosan az az
érték, amit a 310. kör a hívói veremrekeszében látott
(`mov dword [esp+0x48], 0xa`, `0x0057898f`) — tehát a rekordot helyesen
azonosítottam.

⇒ A `+0x20` **alapértéke −1, nem 0**. Mivel az album-ugrás az 5/6/7 típusú
fejléceket csak `+0x20 == 0` mellett fogadja el, ezek a fejlécek
**alapértelmezés szerint NEM ugrási célok** — csak akkor azok, ha valaki a
felépítés után kifejezetten 0-ra állítja a mezőt.

### 3. Ami NYITVA marad

1. **Ki állítja a `+0x20`-at 0-ra.** A paraméteres konstruktornak
   **12 hívója** van, mind a `0x004b1acb`–`0x004b81fd` sávban (a lista-építő
   modul); az elsőnek átnézett hívóban (`0x004b2ab4`) a konstruktor után csak
   a `+0x0c`, `+0x14`, `+0x18`, `+0x1c` íródik, a `+0x20` nem. A megszerzés
   útja: a maradék 11 hívóhely ugyanilyen átnézése — a rekord a veremben áll,
   tehát a `+0x20` a `lea esi,[esp+N]` bázishoz képest `N+0x20`-on keresendő.
2. **A `0x006dcc40` teljes viselkedése** (912 b): a fenti lekérés után
   RTTI-s ágakon megy tovább (`0x006dcdb0 call 0x00c07db2`), és a függvény
   sztringjei közt `thumbui/webwindow` és `about:blank` is van — ezek egy
   MÁSIK ágé lehetnek. A megszerzés útja: a `0x006dc9a0` hívott függvény és a
   `0x006dcdcd` / `0x006dcde9` virtuális hívások célja.

*Forrás: `0x00578abc`, `0x00578ac3`, `0x00c29e1a`, `0x00d49170`, `0x00c29e24`,
`0x0076a4b0`, `0x006dcc40`, `0x004a06e0`, `0x004a0720`.*

## ⛳ Az album-ugrás gyakorlatilag CSAK az 1-es típusú sorokat találja meg (2026-09-16, 314. kör, #3143)

*A 313. kör kimérte, hogy a sorrekord `+0x20` mezőjének alapértéke **−1**, az
album-ugrás viszont az 5/6/7 típusú fejléceket csak `+0x20 == 0` mellett
fogadja el. Ez a kör azt kereste, ki írja 0-ra — és a válasz: a mérhető
utakon SENKI.*

### 1. A sorok típusa a konstruktor ELSŐ argumentuma

A paraméteres konstruktor (`0x004a0720`) az első argumentumot teszi a
`+0x30`-ba: `mov edx, [esp+0x10]` (`0x004a0776`) → `mov [esi+0x30], edx`
(`0x004a078d`); a veremeltolás a három prológ-`push`-sal (`ebx`, `ebp`, `edi`)
és a visszatérési címmel együtt pontosan az 1. argumentumra mutat.

Ebből a **12 hívóhely típus-leltára** (az utolsó `push` a hívás előtt):

| hívóhely | típus | hívóhely | típus |
|---|---:|---|---:|
| `0x004b1acb` | **8** | `0x004b3281` | *változó* (`ebp`) |
| `0x004b1eac` | **5** | `0x004b35a2` | **2** |
| `0x004b22ce` | **2** | `0x004b3886` | **2** |
| `0x004b2ab4` | **1** | `0x004b3b50` | **2** |
| `0x004b2f9a` | **3** | `0x004b3f4b` | **2** |
| `0x004b7f17` | **9** | `0x004b81fd` | **2** |

⇒ A tizenegy **konstans** hívóhely a `{1, 2, 3, 5, 8, 9}` típusokat gyártja;
**a 6-os és a 7-es egyiken sem szerepel.** (A `0x004b3281` egy futásidőben
számolt értéket ad át — az a függvény, `0x004b2e10`, az `ebp`-t
mutató-léptetésre is használja `add ebp, 0x38`-cal, ezért **ennek az egy
helynek a típusát nem mondom meg**; ez a nyitott rész.)

### 2. A `+0x20`-at a mérhető utakon senki nem írja

Három, egymástól független pásztázás, mindegyik **működő kontrollal**:

| # | mit néztem | eredmény | kontroll |
|---|---|---|---|
| 1 | mind a **12** konstruktor-hívóhely, a `lea esi,[esp+N]` bázishoz képest a hívás utáni 0x220 bájtos ablakban minden `[esp+…]` mezőírás | `+0x20`-ra **0 találat** | a `+0x0c`, `+0x14`, `+0x1c`, `+0x2c`, `+0x30` írásokat MEGTALÁLTA (pl. `0x004b2b13`, `0x004b2b30`, `0x004b2b4e`) |
| 2 | a lista-modul (`0x004ae000`–`0x004b8600`) **85** darab `[reg+0x20]`-írása | mind a **lista** objektumé, nem a rekordé — a `+0x20`/`+0x24` pár ott a szál-azonosító és a rekurzió-számláló (`0x004ae500`, `0x004ae521`, `0x004ae528`) | a `[reg+0x30]`-írások ugyanezzel a mintával előjönnek |
| 3 | a teljes `.text` **279** darab „×56-os lépésköz" helye (`lea r,[x*8]` + `sub r,x`), és mindegyik után 0x70 bájt | a rekord-listás helyeken **0 találat** `+0x20`-ra | a minta összesen **25** `+0x20`-írást talált (máshol), tehát nem vak |

⇒ **Mért következtetés: a `+0x20` a konstruktor −1-én marad**, tehát az
album-ugrás második ága (`típus ∈ {5,6,7} ÉS +0x20 == 0`) **a gyakorlatban
soha nem tüzel**, és a gombpár **csak az 1-es típusú sorokra** ugrik.

⚠️ **A negatív állítás hatóköre.** A pásztázások a rekord elérési útjait fedik
(konstruktor-hívóhely, lista-modul, 56-os lépésközű indexelés). Egy olyan
beállító, amely **csupasz `rekord*`-ot kap paraméterként**, nincs kizárva: a
`mov dword [reg+0x20], 0` alak önmagában **1831**-szer fordul elő a
`.text`-ben, ez a szám nem osztályozható. A megszerzés útja, ha valaki
folytatja: a **típus-5-öt gyártó egyetlen hely** (`0x004b1eac`) rekordjának
teljes élete — kinek adja át, és az mit hív rá.

### 3. A `prevalbum` sor-közepi ága NEM görget

A `0x006dcc40` (912 b) teljes törzsében **nincs** `[nézet+0x2f8]`-írás és
**nincs** `0x009d2810` hívás (a görgetés-beállító, amit a két album-ugró
használ). Amit csinál: ugyanabból a nézetmodellből (`[this+0xeb0]`) kiszámolja
a **határsort** (`[+0x320] + [+0x2f8]`, `0x006dcc57`–`0x006dcc5d`), lekéri a
`0x004ae4e0`-nal, majd a sorlistán (`[this+0x2c0]`) virtuális hívásokkal megy
tovább (`0x006dcdcd`, `0x006dcde9`, `0x006dcf47`).

⇒ A korábbi kézenfekvő olvasat („a sor tetejére igazít") **nincs
alátámasztva** — a függvény nem nyúl a görgetési pozícióhoz. A pontos hatása
NYITOTT; útja: a `0x006dc9a0` (`0x006dcdc1`) és a fenti három virtuális
hívóhely célja.


## A görgetősáv album-ugrói MEGÉPÜLTEK (2026-09-19, #857)

A #856 leletéből (négy gomb, mind `m_autorepeat`) a két **album-ugró** a
termékbe került: a rács sávjának tetején az előző, alján a következő mappára
ugrik, nyomva tartva ismételve. A fel/le nyílgomb, a lapozó féltér és a
pozíciójelző NEM épült meg, és a sáv 10 képpontos, lapos stílusa marad — a
döntés és az indoklása: `docs/decisions/gorgetosav-album-ugro.md` (ADR-015).

⚠️ A 3.1 szakasz egykori indoklása („natív Windows-króm, tehát nem követendő
minta") **megdőlt**; a stílusdöntés attól még áll, csak más okból: a mai
felület MINDEN sávja ilyen, és a 16 képpontos, három állapotképes rajz
visszahozása az egész króm szétszabdalásával járna.

## ⛳ R5 — a fő könyvtárnézet (`thumbui`) súgói: 15 egyezik, 4 eltér (2026-09-22, 341. kör, #656)

*Forrás: `referencia/ui-leltar.csv` (a `thumbui.tre` 31 buborék-súgója) ·
a hivatalos angol és magyar szöveg cél-azonosító szerint:
`referencia/i18n/enUS/tooltips.xml` és `referencia/i18n/hu/tooltips.xml`
(`<action type="Tooltip" target="thumbui/…">`) · a mi QML-forrásunk és a
`picasapy_hu.ts`, szó szerinti összevetéssel.*

### A) Szó szerint egyezik — angolul ÉS magyarul (15)

| eredeti elem | angol | magyar | nálunk |
|---|---|---|---|
| `addtobuttcon` | Add selected items to an Album | Kijelölt elemek hozzáadása albumhoz | `TrayBar.qml:960` |
| `flatview` | Set view to show flat folder structure | Egydimenziós mappanézet beállítása | `MainToolbar.qml:204` |
| `folderview` | Set view to show folder tree structure | Fastruktúrájú mappanézet beállítása | `MainToolbar.qml:231` |
| `importbutton` | Get photos from a camera, scanner, or other media | Fotók letöltése fényképezőgépről, képolvasóról vagy más eszközről | `MainToolbar.qml:110` |
| `newalbum` | Create a new album | Új album létrehozása | `MainToolbar.qml:163` |
| `rotateleft` / `rotateright` | Rotate counter-clockwise / Rotate clockwise | Forgatás balra / jobbra | `TrayBar.qml:1167` / `:1212` |
| `scratchclear` | Clear items from the selection | Elemek eltávolítása a kijelölésből | `TrayBar.qml:923` |
| `scratchhold` | Hold selected items | Kijelölt elemek megőrzése | `TrayBar.qml:899` |
| `single_action_return` | Go back to what you were editing | Visszatérés a szerkesztett elemhez | `TrayBar.qml:2167` |
| `startoggle` | Add/Remove Star | Csillag hozzáadása/eltávolítása | `TrayBar.qml:1107` |
| `people_toggle` · `places_toggle` · `tags_toggle` · `properties_toggle` | Show/Hide … Panel | Az … párbeszédpanel megjelenítése/elrejtése | `TrayBar.qml:1291`–`1300` (`sugo`) |

### B) Eltér (4)

| eredeti elem | eredeti (EN / HU) | nálunk (EN / HU) | mi a különbség |
|---|---|---|---|
| `loupehit` | *Click and drag over photos to magnify them* / **Ide kattintva és az egérmutatót a fotókra húzva kinagyíthatja a részleteket** | *Loupe — drag over the photos* / „Nagyító — húzd a képek fölött” (`TrayBar.qml:1446`) | más mondat, és a magyar **tegező** — az eredeti magázó |
| `folderviewpopup` | *View options* / **Megjelenítési beállítások** | *Folder view options* / „Mappanézet beállításai” (`MainToolbar.qml:267`) | más szöveg |
| `albumview` | felirat *Back To Library*, súgó *Return to organized thumbnails* / **Vissza a rendezett indexképekhez** | a „Back to Library” gombnak (`PhotoViewer.qml:840`) **nincs súgója** | hiányzó súgó |
| `single_action_close` | *Cancel "Get more"* / **A "Továbbiak" művelet megszakítása** | a magyar „A „Továbbiak” művelet megszakítása” (`TrayBar.qml:2183`) | csak az idézőjel: az eredeti egyenes `"…"`, nálunk tipográfiai `„…”` |

### C) A többi hat elem: nem látható vagy állapotfüggő — R6

Az R5-ben a `m_hidden`/`m_fakehidden` elemeket még „feltételesen megjelenőként”
kezeltük. Ez túl erős állítás volt: a `.tre`-forrás a **kezdeti
láthatóságot** adja, a bináris pedig külön választja az akciót attól, hogy a
vezérlő kirajzolódik-e. A hat név most külön le van vezetve.

#### Forrásból bizonyított kezdeti állapot

A `macros.tre:112–117` szerint:

- `m_hidden` = `Property setvisible 0`;
- `m_fakehidden` = `Property setvisible 0` **és** `Property hiddentimer 1`.

A hat cél a `thumbui.tre`-ben:

| elem | erőforrás-forrás | kezdeti állapot | további forrásjel |
|---|---|---|---|
| `sbutton` | `thumbui.tre:463–470` | `m_hidden` | a blokk címe: `these buttons are to be removed` |
| `timelinebutton` | `thumbui.tre:472–478` | `m_hidden` | ugyanebben az eltávolítási blokkban |
| `newfolder` | `thumbui.tre:378–382` | `m_hidden` | nincs aktív `showtarget` a módmakrókban |
| `backup` | `thumbui.tre:95–101` | `m_hidden` | a forrás megjegyzése: `currently not shown in UI` |
| `cdmode` | `thumbui.tre:480–489` | `m_hidden` | a `m_cdcontrolset_enable` mód ugyanitt kapcsolja a CD-sávot |
| `fullview` | `thumbui.tre:147–149` | `m_fakehidden` | a `m_enable_albummode` aktívan rejti (`macros.tre:196–203`) |

A módmakrók **nem teszik láthatóvá magukat a gombokat**: a
`m_cdcontrolset_enable` a `publish/presentation_group`-ot és a
`thumbui/cd_label`-t mutatja (`macros.tre:233–240`), a
`m_backupcontrolset_enable` pedig a `publish/backup_group`-ot és a
`thumbui/backup_label`-t (`macros.tre:245–252`). A `sbutton` és a
`timelinebutton` `showtarget` sorai (`macros.tre:230–231`) kikommentezettek;
a kapcsolódó `hidetarget` sorok is kikommentezettek (`macros.tre:242–278`).
Ez a forrás nem támasztja alá, hogy a főablakban bármelyik gombot a módváltás
kirajzolná.

#### A binárisban az akció él, a gomb nem következik belőle

A közös vezérlő-diszpécser (`0x005d9cc0`, 7153 bájt) mind az öt `m_hidden`
elemet név szerint felismeri, de ez csak parancskezelés:

| cél | diszpécser-ág | átadott kezelő | mit bizonyít |
|---|---|---|---|
| `thumbui/fullview` | `0x005da6d3–0x005da6d8` | `0x005683a0` | a megtekintési/szerkesztési nézet akciója |
| `thumbui/sbutton` | `0x005da740–0x005da743` | `0x005e8a70`, jelző `0` | a diavetítés akciója |
| `thumbui/timelinebutton` | `0x005da7ab–0x005da7ae` | `0x005e8a70`, jelző `1` | az Időrend akciója |
| `thumbui/newfolder` | `0x005da362–0x005da365` | `0x005e9bb0` | az új mappa akciója |
| `thumbui/cdmode` | `0x005db4bc–0x005db4d5` | `0x005675d0`, `0x006032f0`, `0x0067be30` lánca | a CD-mód indítása |
| `thumbui/backup` | `0x005db77c–0x005db7ee` | `0x006032f0`, majd `0x0067be30` | a mentési mód indítása |

A két publikáló út külön kontrollált: a `create_cd` parancs
`0x005e0f70:0x005e1167–0x005e116c` alatt a `thumbui/cdmode` célra kattint,
a Tools-menü mentési ága pedig `0x005cb990:0x005cbdee–0x005cbdf3` alatt a
`thumbui/backup` célra kattint. Ugyanígy a menü-diszpécser a
`thumbui/fullview` célra kattint (`0x005cb990:0x005cbd7a–0x005cbd7f`).
Ezek a hívások az aktiválást bizonyítják, nem a vezérlő látható állapotát.

A `fullview` valódi felhasználói útja külön is megvan: a gyorsbillentyű-ág
`0x005e60d0:0x005e624f–0x005e6254` aktiválja a célt; a jelenlegi termékben
ugyanezt a `Main.qml` `nezdEsSzerkeszd()` függvénye és a `Ctrl+3` kötése adja
(`Main.qml:178–185`, `829–835`).

#### Eredeti / nálunk / teendő

| elem | eredeti — mért lelet | nálunk — mért állapot | teendő |
|---|---|---|---|
| `sbutton` | főablaki erőforrásban rejtett, eltávolításra jelölt; a parancskezelő él | nincs kihelyezett főablaki QML-gomb; a vetítés menütétel külön él | nincs új főablaki gombfeladat; a rejtett erőforrás nem hiányzó gomb |
| `timelinebutton` | főablaki erőforrásban rejtett, eltávolításra jelölt; a parancskezelő él | `MainToolbar.qml:277–302` csak a korábbi gomb eltávolítását dokumentáló komment; a `PicasaMenuBar.qml:847–852` menütétel inaktív | a valódi animált Időrend külön terméki munka; a rejtett erőforrás önmagában nem indokol gombot |
| `newfolder` | `m_hidden`; külön parancskezelő-ág bizonyított | a fő eszköztárban nincs `newfolder` QML-elem; a jelenlegi forrásban külön `newalbum` van (`MainToolbar.qml:36–40`, `154–166`) | a mappa-létrehozás felületét külön terméki jegyben kell eldönteni; ez a kutatás nem bizonyít látható eredeti gombot |
| `backup` | `m_hidden`, a forrás szerint „currently not shown”; Tools-menüből a rejtett cél aktiválható | `PicasaMenuBar.qml:1824–1830` alatt külön `menuToolsBackup` menütétel és jel van | a főablaki gombot nem kell hozzáadni; a menüút nem azonos a rejtett gombbal |
| `cdmode` | `m_hidden`; a `create_cd` parancs a CD-sávot aktiválja | a `Create a Gift CD...` tétel jelenleg placeholder (`PicasaMenuBar.qml:1759–1762`) | a CD-kimenet meglévő terméki munkája; a rejtett főablaki gomb pótlása nem a bizonyított eltérés |
| `fullview` | `m_fakehidden`; a `hiddentimer 1` most már statikusan feloldva: külön eseménykapu-jelző, nem láthatóvá tevő timer; a `setvisible 1`-re váltó konkrét futásidejű esemény **NINCS MEG** | `Ctrl+3`/„Megjelenítés és szerkesztés” út megvan (`Main.qml:178–185`, `829–835`) | a rejtett gomb kirajzolási eseménye továbbra is **BLOKKOLT**; a célzott runtime-trace vagy valódi Picasa-mérés maradt |

### D) `fullview`: a `hiddentimer` eseménykapu, nem visszaszámláló — R7

Az R6 a `hiddentimer 1` futásidejű jelentését nyitva hagyta. A célzott
index- és diszasszemblálási kör ezt a részt most **megerősített** szinten
pontosítja, de nem állít láthatóvá válást olyan eseményre, amelyet a bináris
nem nevez meg.

#### A parser két külön műveletet kezel

A `Property`-parser a `setvisible` és a `hiddentimer` kulcsot külön ágon
kezeli:

- `setvisible`: a kulcsliterál `0x00c7ca40`, összehasonlítás
  `0x009caecf–0x009caf14`; nem nulla értéknél a cél virtuális
  `+0x6c` metódusát, nulla értéknél a `+0x68` metódusát hívja
  (`0x009caf2c–0x009caf47`). Ez a tényleges láthatósági művelet útja.
- `hiddentimer`: a kulcsliterál `0x00c7cbc4`, összehasonlítás
  `0x009cbdb0–0x009cbdf6`; az értéket a `0x009c7700` setterbe adja
  (`0x009cbdfd–0x009cbe00`). A két kulcs tehát nem ugyanazt a mezőt vagy
  műveletet jelenti.

#### Mit ír a `hiddentimer` setter?

A `0x009c7700` (51 bájt) a kapott értéket az elem `+0x22c` bájtjába írja
(`0x009c7713`). Ha az elem `+0x213` jelzője nulla, a `+0x244` alatt tárolt
szülőre is továbbírja (`0x009c771b–0x009c7725`), a
`0x009e3930` rekurzív propagálóval. A konstruktor a mezőt először nullázza
(`0x009dd800`, `0x009dda35`, az előtte nullázott `ebx`-szel), tehát a
`Property hiddentimer 1` egy **egybájtos állapotjelzőt** állít; nincs benne
visszaszámláló, időtartam vagy láthatósági érték.

A layout-/esemény-előkészítő `0x009e0ed0` ezt a jelzőt újra `1`-re állítja
(`0x009e0f04–0x009e0f27`) és a szülőre propagálja; a vizsgált ágban nem
nullázza. Ez kizárja azt az olvasatot, hogy a „timer” név önmagában egy
lejáró, majd láthatóvá tevő időzítőt bizonyítana.

#### A tényleges eseménykapu

A `0x009e4630` esemény-előkészítőben:

1. ha az elem `+0x20c` állapotjelzője nem nulla és a `+0x22c` hiddentimer-
   jelző is aktív (`0x009e464a–0x009e465b`),
2. akkor a `0x13` eseménykód kivételével az ág `0xf4241` értékkel tér vissza
   (`0x009e4663–0x009e466e`). A motorban `0xf4241` a „nem kezeltem, add
   tovább” érték, a `0x13` pedig találat-vizsgálat/kurzorkérés
   (`picasa-eger-es-kijeloles.md:330–340`, pozitív bináris kontrollok:
   `0x00860a31`).

Vagyis a binárisból bizonyítható hatás: a `hiddentimer` az események
feldolgozását kapuzza, miközben a találat-vizsgálati kivételt meghagyja.
Ebben az ágban nincs `setvisible 1` hívás, nincs időérték-összehasonlítás,
és nincs `+0x22c`-t nullázó feloldás.

#### Mi zárható le, és mi nem?

- **LEZÁRVA — kezdeti állapot:** a `fullview` `m_fakehidden` miatt
  `setvisible 0`-val épül fel (`thumbui.tre:147–149`, `macros.tre:115–117`).
- **LEZÁRVA — `hiddentimer` statikus jelentése:** egy elem- és szülő-
  propagálható eseménykapu-jelző; nem bizonyított láthatóvá tevő timer.
- **BLOKKOLT — a konkrét `setvisible 1` esemény:** a `.tre`-korpuszban
  nincs `showtarget thumbui/fullview`; a `m_fullviewButtons` más célokat
  mutat/rejt (`thumbuimacros_win.tre:1–8`), az `m_enable_albummode` pedig
  `hidetarget thumbui/fullview`-t tartalmaz (`macros.tre:196–203`). A
  statikus anyag ezért nem nevezi meg, mikor válna a `fullview` ténylegesen
  láthatóvá. Ezen a gépen nincs `wine`, ezért valódi Picasa-futtatásból
  származó képernyő- vagy settermérés **NINCS MEG**. A lezáráshoz Windowsos
  futásidejű trace kell a `fullview` objektum `setvisible` útjára, vagy a
  tulajdonos valódi Picasa-mérése.

*Bizonyítottsági fok: **megerősített** a kezdeti `setvisible 0`, a parser-
setter lánc és az eseménykapu; **BLOKKOLT** a láthatóvá válás konkrét
futásidejű kiváltója.*

#### Korábbi állítás helyesbítése és kérdésmérleg

Az R5 korábbi „mind a hat alapból rejtett, feltételesen megjelenő gomb”
mondata helyesbítve: a bizonyított állapot **rejtett kezdeti erőforrás +
élő parancsút**. Ez nem bizonyítja, hogy a kiadott főablakban hat látható
gombnak kell lennie. A `newfolder` és `fullview` esetében különösen nem
szabad a deklarált méretből látható UI-ra következtetni.

- a hat elem kezdeti `visible`-állapota és parancsútja — **LEZÁRVA**;
- a `fullview` `hiddentimer 1` statikus mechanizmusa — **LEZÁRVA**: a
  `+0x22c` eseménykapu-jelző és a `0x13` találatvizsgálati kivétel
  bizonyított;
- a `fullview` konkrét `setvisible 1` futásidejű eseménye — **BLOKKOLT**:
  nincs helyi Wine-futtatás; a megszerzéshez Windowsos runtime-trace vagy
  valódi Picasa-mérés kell;
- a R5 fennmaradó hat eleme (`smallthumbs`, `largethumbs`, `next`, `prev`,
  `visitweb`, `webcambutton`) — **HATÓKÖRÖN KÍVÜL** ebben a körben.

`0 nyílt · 2 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva`

Fejlesztői jegyek: a korábbi felirat-eltérések **#3476**; a CD-kimenet és az
Időrend csak a saját meglévő terméki jegyeikben folytatandó, új duplikált jegy
e körben nem nyílt.
