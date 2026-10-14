# UI-audit: jobbklikk-kontextusmenük (2026-08-07)

Forrás: a felhasználó **magyar nyelvű Picasa 3.9**-éről készült 5 célzott
képernyőkép a jobbklikk-menükről. Ez az első **rendszeres** felmérés a
témában — a `ui-audit-menus.md` eddig csak egy „bónusz észrevétel"
szakaszban, két véletlen képernyőképből, 4 tételt említett.

Összevetés a jelenlegi implementációval:
`src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml` és
`FolderContextMenu.qml`.

> 🔑 **A helyi menük gyorsbillentyűi bináris bizonyítékkal** (építő-
> függvény, rekordcím, `cmd`-azonosító, a módosító-jelzőbájt bitjei):
> [picasa-gyorsbillentyuk.md](picasa-gyorsbillentyuk.md) **4.** szakasz
> (#1154). Két billentyű **csak** helyi menüben létezik: az `Esc`
> (visszatérés a könyvtárhoz) és a `Ctrl+H` (megtartás a tálcán).

## 0. Összegzés egy mondatban

A Picasában **öt különböző** kontextusmenü él, összesen **~40 egyedi
paranccsal**; a PicasaPy ebből kettőt valósít meg, **9 paranccsal**. A menük
nem díszítés: az eredetiben több funkció **kizárólag** innen érhető el.

| kontextus | eredeti tételszám | nálunk | állapot |
|---|---|---|---|
| a rács üres területe | 15 | 2 | súlyosan hiányos |
| bal panel: mappa-sor | 15 (**azonos**) | 2 | súlyosan hiányos |
| a rács tetején a mappa-fejléc | 15 (**azonos**) | 0 | hiányzik
| indexkép a rácsban | 19 | 7 | hiányos |
| kép a szerkesztőben / nézőben | 17 | **0** | teljesen hiányzik |
| bal panel: gyűjtemény-fejléc („Mappák (n)") | 3 | **0** | teljesen hiányzik |

## 1. Mappa-kontextus — a rács üres területe ÉS a bal panel mappa-sora

**Fontos megfigyelés: a kettő UGYANAZ a menü.** A felhasználó két külön
képernyőképe (rács üres területe, illetve a bal panelen az „AI (88)" mappa)
bájtra azonos listát ad. Egy implementáció, két megnyitási pont.

A „nálunk" oszlop **mérve 2026-09-20-án** a
`src/picasapy/app/qml/PicasaPy/FolderContextMenu.qml` forrásából (tétel,
sorrend, kezelő) és a `FolderPane.qml` 1121–1212. sorából (a jelek
fogadása). A menüt a **#422** építette meg, a sorrendjét a
`tests/app/test_folder_context_menu_320.py::
test_all_fifteen_original_commands_are_present_in_order` őrzi.

| # | eredeti felirat | gyorsbillentyű | van-e nálunk |
|---|---|---|---|
| 1 | Mappaleírás szerkesztése… | — | **igen** |
| — | *elválasztó* | | |
| 2 | Az összes kép kijelölése | `Ctrl+A` | **igen** |
| 3 | Kijelölés törlése | `Ctrl+D` | **igen** |
| 4 | Kiválasztás megfordítása | `Ctrl+I` | **igen** |
| 5 | Áthelyezés gyűjteménybe ▸ | — | **igen** |
| — | *elválasztó* | | |
| 6 | Indexképek frissítése | — | **igen** |
| 7 | Mappa rendezésének alapja ▸ | — | **igen** (öt rendezés + fordított sorrend) |
| — | *elválasztó* | | |
| 8 | Mappa elrejtése | — | **igen** (#1637) |
| — | *elválasztó* | | |
| 9 | Keresés a lemezen | `Ctrl+Enter` | **igen** |
| 10 | Eltávolítás a Picasából… | — | **igen** |
| — | *elválasztó* | | |
| 11 | Mappa áthelyezése… | — | **igen** |
| 12 | Mappa törlése… | — | **igen** (#1638 — a lomtárba) |
| — | *elválasztó* | | |
| 13 | Feltöltés a Google Fotókba… | — | tétel megvan, **`retired`** (a szolgáltatás megszűnt, véglegesen szürke) |
| — | *elválasztó* | | |
| 14 | Exportálás HTML-oldalként… | — | **igen** |
| 15 | Névcímkék hozzáadása | — | **megvan és működik** (#4535; a mappa képein indít arckeresést) |

Vagyis mind a 15 tétel megvan, a mért sorrendben; a megszűnt szolgáltatás
szándékosan szürke. A „Mappa
dátumának beállítása…" — amely az eredetiben **nincs** ebben a menüben —
azóta kikerült; a helye a Mappaleírás-dialógus, és ezt a
`test_folder_date_item_is_gone` őrzi.

⚠️ Ez az oszlop **2026-09-19-ig „nem"-eket mutatott** egy elavult
felmérésből, és emiatt született a #3363 jegy egy már elkészült
munkára. Aki ezt a táblát olvassa: a „nálunk" oszlop mérés, nem
feltevés — használat előtt vesd össze a forrással.

### 1.b Harmadik megnyitási pont: a mappa-fejléc a rácsban

A rács tetején ülő **mappa-fejlécre** (nagy mappa-ikon + mappanév + dátum +
műveletsor) jobbklikkelve **ugyanez a 15 tételes menü** jön elő. Tehát a
mappa-menünek **három** megnyitási pontja van, bájtra azonos tartalommal:

1. a rács üres területe (indexképek között),
2. a bal panel mappa-sora,
3. a rács tetején a mappa-fejléc.

Implementációs következmény: **egy** komponens, három `MouseArea`/
`TapHandler` hívóval — nem három külön menü.

Nálunk így is van (mérve 2026-09-20): egyetlen `FolderContextMenu`
példány él a `FolderPane.qml` 1121. sorában, és mind a három hívó a
`FolderPane.openFolderContextMenu(path)` függvényen megy át — a bal panel
mappa-sora (`FolderPane.qml` 616., 876., 998. sor), a rács üres területe
és a rács tetején a mappa-fejléc (`LightboxFeed.qml` 641. és 722. sor).

## 2. Indexkép-kontextus (kép a rácsban)

| # | eredeti felirat | gyorsbillentyű | van-e nálunk |
|---|---|---|---|
| 1 | **Megjelenítés és szerkesztés** (félkövér = alapértelmezett) | `Enter` | nem |
| 2 | Hozzáadás az albumhoz ▸ | — | **igen** |
| — | *elválasztó* | | |
| 3 | Forgatás jobbra | `Ctrl+R` | nem |
| 4 | Forgatás balra | `Ctrl+Shift+R` | nem |
| — | *elválasztó* | | |
| 5 | Összes szerkesztés visszavonása | — (**inaktív**, ha nincs szerkesztés) | nem |
| — | *elválasztó* | | |
| 6 | Elrejtés | — | **igen** |
| — | *elválasztó* | | |
| 7 | Áthelyezés új mappába… | — | **igen** („Move to Folder…") |
| 8 | Mappa felosztása itt… | — | nem |
| — | *elválasztó* | | |
| 9 | Fájl megnyitása | `Ctrl+Shift+O` | nem |
| 10 | Társítás ▸ | — | nem |
| — | *elválasztó* | | |
| 11 | Mentés | `Ctrl+S` (**inaktív**) | nem |
| 12 | Visszaállítás | — (**inaktív**) | nem |
| — | *elválasztó* | | |
| 13 | Keresés a lemezen | `Ctrl+Enter` | **igen** („Locate on Disk") |
| 14 | Törlés a lemezről | **`Ctrl+Törlés`** | **igen** |
| 15 | Teljes elérési út másolása | — | nem |
| — | *elválasztó* | | |
| 16 | Feltöltés a Picasa Webalbumokba… | — | nem |
| 17 | Feltöltés tiltása | — | nem |
| — | *elválasztó* | | |
| 18 | Arcok alaphelyzetbe állítása | — | nem |
| — | *elválasztó* | | |
| 19 | Tulajdonságok | `Alt+Enter` | nem |

Nálunk van, de az eredetiben **nincs** ebben a menüben: „Átnevezés…"
(Rename…) és „Eltávolítás az albumból" — utóbbi feltehetően csak
album-nézetben jelenik meg az eredetiben, ez ellenőrzendő.

## 3. Néző-/szerkesztő-kontextus (a nagy képen)

Majdnem azonos a 2. ponttal, **négy szisztematikus eltéréssel** — ezek
mutatják, hogy a Picasa nem egy menüt használ két helyen, hanem tudatosan
kettőt:

| eltérés | rácsban (2.) | nézőben (3.) |
|---|---|---|
| első, félkövér tétel | **Megjelenítés és szerkesztés** — `Enter` | **Visszatérés a könyvtárhoz** — `Esc` |
| mappa-műveletek | „Áthelyezés új mappába…" + „Mappa felosztása itt…" | **nincs** (a nézőben nincs értelme) |
| törlés | „Törlés a lemezről" — **`Ctrl+Törlés`** | „Törlés lemezről" — **`Delete`** |
| feltöltés | „Feltöltés a Picasa Webalbumokba…" | „**Gyors feltöltés**" |

A törlés-gyorsbillentyű eltérése **szándékos**: a rácsban a puszta `Delete`
más jelentésű (eltávolítás az albumból), ezért ott a lemezről törléshez
`Ctrl` is kell; a nézőben nincs ütközés, elég a `Delete`.

A néző-menü teljes tételsora: Visszatérés a könyvtárhoz `Esc` · Hozzáadás az
albumhoz ▸ · Forgatás jobbra `Ctrl+R` · Forgatás balra `Ctrl+Shift+R` ·
Összes szerkesztés visszavonása *(inaktív)* · Elrejtés · Fájl megnyitása
`Ctrl+Shift+O` · Társítás ▸ · Mentés `Ctrl+S` *(inaktív)* · Visszaállítás
*(inaktív)* · Keresés a lemezen `Ctrl+Enter` · Törlés lemezről `Delete` ·
Teljes elérési út másolása · Gyors feltöltés · Feltöltés tiltása · Arcok
alaphelyzetbe állítása · Tulajdonságok `Alt+Enter`.

## 4. Gyűjtemény-kontextus (a bal panel „Mappák (n)" fejléce)

A legrövidebb, és nálunk **teljesen hiányzik**:

| # | eredeti felirat | van-e nálunk |
|---|---|---|
| 1 | Gyűjtemény átnevezése… | nem |
| 2 | Gyűjtemény eltávolítása | nem |
| 3 | Jelszó megadása/módosítása… | nem |

A **jelszavas gyűjtemény** eddig egyáltalán nem szerepelt a specjeinkben. Az
`.exe` string-táblája megerősíti: „Please enter a password to open this
collection" (`CAlbumState::passprompt`), „Password Entry"
(`CAlbumState::passtitle`) — tehát valódi, működő funkció volt.

## 5. Szerkezeti tanulságok az implementációhoz

1. **Az inaktív tétel is tétel.** A Picasa nem rejti el a nem elérhető
   parancsot (Mentés, Visszaállítás, Összes szerkesztés visszavonása), hanem
   **szürkén megjeleníti** — így a menü magassága és a tételek helye
   állandó, az izommemória működik. Ez egyezik a `design-guide.md` „inaktív
   menüpont szándékos" elvével, és a kontextusmenükre is érvényes.
2. **A csoportosítás jelentéshordozó.** Minden menü szűk, 1–4 tételes
   blokkokra oszlik elválasztókkal: kijelölés · nézet · rejtés · lemez ·
   áthelyezés/törlés · megosztás · export. Ezt a csoportbontást érdemes
   átvenni, nem csak a tételeket.
3. **A félkövér első tétel az alapértelmezett dupla­kattintás-művelet.**
   Rácsban „Megjelenítés és szerkesztés" (`Enter`), nézőben „Visszatérés a
   könyvtárhoz" (`Esc`).
4. **Ugyanaz a menü két helyről.** A mappa-menü a rács üres területéről és a
   bal panel mappa-sorából is azonos — egy komponens, két hívó.
5. **Kontextusfüggő gyorsbillentyű.** Ugyanaz a parancs más billentyűvel
   fut más nézetben (törlés: `Ctrl+Delete` vs `Delete`).
6. **Örökölt névkeveredés az eredetiben:** a mappa-menü már „Feltöltés a
   **Google Fotókba**…", az indexkép-menü még „Feltöltés a **Picasa
   Webalbumokba**…" — a Google félbehagyta az átnevezést. A PicasaPy-nak
   nem kell ezt a következetlenséget örökölnie.

## 6. ~~Nyitva~~ → LEZÁRVA a binárisból (2026-08-16)

Mindhárom pont **képernyőkép nélkül** eldőlt: a `Picasa3i18n.dll`
szövegtáblája (`stringres-en-hu.tsv`) menüosztályonként tartalmazza a
feliratokat, tehát nem kellett lefényképezni semmit.

### 6.1 Album-nézet: MEGVAN, és pont az, amit vártunk

Az `AlbumPhoto::` osztály **maga az album-nézeti indexkép-menü**, és
tartalmazza:

```
AlbumPhoto::ID_FILE_DELETEFROMDISK   Remove from Album   Eltávolítás az albumból
```

A mappa-menü album-változata pedig az **`eMenuLabelFolder::`** osztály
(„Törlés…", „Leírás szerkesztése…", „Áthelyezés…", „Eltávolítás a
Picasából…", „Diavetítés megtekintése", „Exportálás HTML-oldalként…",
„Indexképek nyomtatása…", „Indexképek frissítése").
*Bizonyítottsági fok: megerősített.*

### 6.2 Többes szám: NINCS — a feliratok változatlanok

Az `AlbumPhoto::`, `Folder::` és `AlbumList::` osztályok **egyetlen**
felirata sem tartalmaz `%d`-t, „pictures"-t vagy egyéb darabszám-helyőrzőt.
A kontextusmenü szövege tehát **több kijelölt képnél sem változik**.
*Bizonyítottsági fok: megerősített (negatív eredmény).*

### 6.3 A két almenü

**„Társítás ▸"** = `AlbumPhoto::ID_FILEOPENWITH` → **„Open With"**. A
tartalmát a **Windows héj** tölti fel (a fájltípushoz társított
alkalmazások), ezért **nincs és nem is lehet** az erőforrásban. Nincs mit
lefényképezni. *Bizonyítottsági fok: megerősített.*

**„Mappa rendezésének alapja ▸"** = `Folder::SortFolderBy`. A négy tétel
csupasz felirata csak az `eMenuLabelFolder::` osztályban létezik:

| parancs | angol | magyar |
|---|---|---|
| `ID_NAMESORT` | Name | **Név** |
| `ID_DATESORT` | Date | **Dátum** |
| `ID_SIZESORT` | Size | **Méret** |
| `ID_REVERSESORT` | Reverse order | **Fordított sorrend** |

*Bizonyítottsági fok: erős* — a szülő-felirat a `Folder::` osztályban van, a
négy csupasz tétel viszont csak itt; más jelölt készletben („Rendezés a
legutóbbi változtatások alapján" az `AlbumList::`/`eMenuView::` alatt) nincs
„Fordított sorrend".

**A menü HATÓKÖRE: a mappa TARTALMA (#1436).** A négy tétel a mappa KÉPEIT
rendezi, nem a mappákat — ez a menü neve („Mappa rendezésének alapja") mellett
abból is látszik, hogy a `Size` egyetlen mappára nézve csak a képek
fájlméretét jelentheti, és hogy a mappa-listát rendező parancsoknak SAJÁT
osztályuk van (`AlbumList::`, a bal panel menüje, ahol a negyedik szempont a
„legutóbbi változtatás" — ez a `Sort` osztályban nincs). A tulajdonos éles
összevetése szerint a `Date` **növekvő**: a legrégebbi kép elöl, a legújabb a
végén; a `Reverse order` fordítja meg. Nálunk a menü eddig tévesen a rács
MAPPA-sorrendjét állította (`setFolderSort`, #321) — a #1436 kötötte át a
mappa képsorrendjére (`setFolderPhotoSort`).

> **Módszertani megjegyzés.** Mindhárom pont azt kérte, hogy „további
> képernyőkép kell". A válasz mindhárom esetben a **szövegtáblában** volt —
> érdemes ott kezdeni, mielőtt a tulajdonostól kérünk képet.
> (Ld. [`binaris-regeszet-modszertan.md`](binaris-regeszet-modszertan.md) 1.
> és 14/b.)

---

# FÜGGELÉK: a Picasa TELJES menü-parancstáblája (a binárisból, 2026-08-07)

A képernyőképek csak azt mutatják, ami épp látszott. A `Picasa3i18n.dll`
string-táblája viszont **név szerint tartalmazza az összes menüparancsot**,
menüosztályonként csoportosítva — angolul és magyarul egyszerre.
**418 menüparancs**, `<menüosztály>::<ID_PARANCS>` kulcsokkal. Az `&` a
feliratokban a billentyű-gyorsjelölés (Alt-aláhúzás) helye.

## A.1 A menüosztályok = a kontextusmenük

| osztály | tételszám | mi ez |
|---|---|---|
| `Folder` + `FolderWin` | 11 + 1 | **mappa-kontextus** (1., 4., 6. képernyőkép) |
| `FolderPhoto` + `FolderPhotoWin` | 4 + 1 | a mappában lévő **képre** vonatkozó többlet-tételek |
| `AlbumPhoto` + `…Win`/`…Mac` | 16 + 2/3 | **indexkép-kontextus** (2. képernyőkép) |
| `Album` | 13 | **album-kontextus** (a mappa-menü album-változata) |
| `OneUp` | 6 | **néző/szerkesztő-kontextus** (3. képernyőkép) |
| `Collection` | 3 | **gyűjtemény-kontextus** (5. képernyőkép) |
| `AlbumList` + `…Win`/`…Mac` | 12 + 3/3 | **a bal panel saját menüje** — eddig NEM ismertük |
| `Sort` | 4 | a „Mappa rendezésének alapja ▸" **almenü** — eddig nem volt lefényképezve |
| `Tags` | 3 | **címke-kontextus** (jobbklikk egy címkén) — eddig NEM ismertük |
| `Tray` | 2 | **képtálca-kontextus** — eddig NEM ismertük |
| `PplAlbum` + `PplAlbumPhoto` | 4 + 4 | **Emberek-album** kontextusmenüi |
| `Import` + `ImportGroups` | 4 + 1 | az importáló képernyő kontextusmenüi |
| `Address` | 7 | szövegmező-kontextus (Kivágás/Másolás/Beillesztés…) |
| `Slingshot` | 8 | **a Windows Intéző héj-menüje** (Picasa shell-integráció) |
| `Publish`, `Border`, `MMFilm`, `CollageS/D`, `Rotate`, `SyncOpts`, `ImpULOpts`, `AcqDevList`, `BtnConf`, `HierFolder`, `Dev` | 1–15 | további panel-specifikus menük |
| `eMenuFile/Edit/View/Picture/Create/Tools/Help` (+Win/Mac) | 143 | a **felső menüsáv** (ld. `ui-audit-menus.md`) |

## A.2 Amit a képernyőképek nem mutattak — új felfedezések

**`Sort` — a „Mappa rendezésének alapja ▸" almenü teljes tartalma:**
Dátum · Név · Méret · Fordított sorrend.

**`AlbumList` — a bal panel saját kontextusmenüje (11 tétel):** Rendezés
dátum / név / méret / legutóbbi változtatások alapján · Rendezés
megfordítása · Személyek rendezése név / mennyiség / toplista alapján ·
**Egyszerűsített fanézet** · Indexképek megjelenítése a könyvtárban ·
Asztal. Windowson még: **Sajátgép · Dokumentumok · Képek** (gyors
gyökér-váltás).

**`Tags` — címke-kontextus (3 tétel):** A címke hozzáadása a teljes kijelölt
részhez · Az ilyen címkével ellátott elemek keresése · A címke eltávolítása.

**`Tray` — képtálca-kontextus (2 tétel):** Kijelölés megtartása · Kijelölés
eltávolítása.

**Állapotfüggő felirat-váltás (nem külön tétel!):** `ID_HIDEENTIREALBUM`
„Mappa elrejtése" ↔ `ID_UNHIDEENTIREALBUM` „Mappa megjelenítése";
`ID_PICTURE_HIDE` „Elrejtés" ↔ `ID_PICTURE_UNHIDE` „Megjelenítés".

**Mappa-fanézet parancsai:** `ID_HIER_FOLDER_EXPAND` „Az összes részletes
nézete" · `ID_HIER_FOLDER_COLLAPSE` „Az összes kicsinyítése" ·
`ID_MOVEHIERFOLDER` „Mappa áthelyezése…".

**Album-változat (`Album`, 13 tétel)** — a mappa-menü párja albumra: Album
törlése · Albumleírás szerkesztése… · Névcímkék hozzáadása · Exportálás
HTML-oldalként… · Az összes kép kijelölése · Kijelölés törlése · Kiválasztás
megfordítása · **Online műveletek** · Indexképek frissítése · Feltöltés a
Google Fotókba… / a Picasa Webalbumokba…

**Emberek-album (`PplAlbum`, `PplAlbumPhoto`):** Az Emberek album törlése /
szerkesztése… · Az összes kijelölése · Kijelölés törlése; képen: Eltávolítás
az Emberek albumból · Hozzáadás az Emberek albumhoz · **Áthelyezés új
személyhez…** · Beállítás az Emberek album indexképeként.

> ⛔ **HELYESBÍTVE (2026-10-12, #4645):** a `PplAlbum::` névtér négy kulcsa
> NEM a teljes menü. Az építő (`0x007359e0`) hét tételt tesz ki, ebből hármat
> más névtérből kölcsönöz: **Kiválasztás megfordítása** (`Album::ID_SELECT_INVERT`),
> **Indexképek frissítése** (`Album::ID_REFRESH_THUMB`) és **Album
> rendezésének alapja ▸** (`Album::SortAlbumBy`). A sorrend sem a fenti:
> a szerkesztés az első, a törlés az utolsó. Részletek: **F**.

**`Slingshot` — Windows Intéző héj-menü (8 tétel):** Szerkesztés a
Picasában · Másolás · E-mail · Blog · Nyomtatás · Keresés a lemezen · Gyors
feltöltés · Képfeliratok megjelenítése. Ez az az integráció, amitől a Picasa
az Intézőből is elérhető volt — nálunk nincs megfelelője.

## A.3 Miért fontos ez a táblázat

1. **Nem kell többé képernyőképre várni** egyetlen menühöz sem: a
   parancskészlet teljes, hivatalos magyar felirattal.
2. Az `ID_*` nevek **kanonikus parancsazonosítók** — érdemes ezeket használni
   a PicasaPy `Action`-jeinek belső neveként, mert így a menüsáv, a
   kontextusmenük és a gyorsbillentyűk **egyetlen, az eredetivel egyező
   parancstáblára** hivatkoznak. Egy parancs több menüben is megjelenhet
   (pl. `ID_FILE_LOCATEONDISK` négy helyen) — ez a modell ezt természetesen
   kezeli.
3. A `&` gyorsjelölések átvehetők, így az Alt-navigáció is egyezik.

## A.4 A tételsor végigvezetése menünként (2026-08-15)

A #422 elfogadási feltétele — „menünként a tételsor hiánytalanul megvan" —
menüosztályonként végigvezetve, **a string-táblához**, nem a
képernyőképekhez mérve. A képernyőkép csak azt mutatja, ami az adott
nézetben épp látszott; a string-tábla a teljes parancskészletet hozza.

| menüosztály | eredeti | nálunk | állapot |
|---|---|---|---|
| `Folder` + `FolderWin` | 12 | 12 | **teljes** (a fanézet két parancsa nélkül, ld. lent) |
| `AlbumPhoto` + `…Win` | 18 | 18 | **teljes** |
| `FolderPhoto` + `…Win` | 5 | 5 | **teljes** |
| `OneUp` | 6 | 6 | **teljes** |
| `Album` | 13 azonosító / 12 felirat | 12 | **teljes** (a `SortAlbumBy`-jal, #757) |
| `AlbumList` | 12 | 12 | **teljes** (a Win/Mac gyökérváltók nélkül; #757) |
| `Collection` · `Sort` · `Tags` · `Tray` · `Address` | 3 · 4 · 3 · 2 · 7 | ua. | **teljes** |
| `PplAlbum` · `PplAlbumPhoto` | 4 · 4 | 4 · 4 | **teljes** |

A végigvezetés **négy** olyan tételt talált, amit sem a képernyőképek, sem
a fenti szöveges felsorolások nem hoztak elő:

1. **`AlbumPhoto::ID_FILE_LOCATEINPICASA` — „Keresés a Picasában".** A
   „Keresés a lemezen" párja *befelé*: album-nézetből a kép saját mappájára
   ugrik a könyvtárban. A 2. szakasz képernyőképe mappa-nézetben készült,
   ahol nincs értelme — ezért maradt ki onnan.
2. **`PplAlbumPhoto::ID_PEOPLEALBUMS` — „Hozzáadás az Emberek albumhoz".**
   Az A.2 négy `PplAlbumPhoto`-parancsot említ, de a felsorolásában ez
   összemosódott az „Áthelyezés új személyhez…"-zel. Az angol forrás `Move
   to People Album`, a hivatalos magyar viszont „Hozzáadás…" — a két nyelv
   itt szándékosan mást mond.
3. **`Album::ID_UPLOAD_TO_LIGHTHOUSE` — „Feltöltés a Picasa
   Webalbumokba…".** Ez oldja fel az A.2 „13 tétel, de csak 11 nevesítve"
   ellentmondását: a 13-ból **négy** feltöltés-azonosító
   (`ID_UPLOAD_ALBUM_TO_GOOGLE_PLUS_PHOTOS`, `ID_UPLOAD_ALBUM_TO_LIGHTHOUSE`,
   `ID_UPLOAD_TO_GOOGLE_PLUS_PHOTOS`, `ID_UPLOAD_TO_LIGHTHOUSE`), és ezek
   mindössze **két** különböző feliratot adnak. Vagyis 11 különböző felirat
   van, nem 13 — nincs két „elveszett" tétel.
4. **`Folder::ID_UNHIDEENTIREALBUM` — „Mappa megjelenítése".** Az A.2
   kimondja, hogy ez *nem külön tétel*, hanem a „Mappa elrejtése"
   állapotfüggő felirat-váltása. Nálunk a sor addig egyetlen, rögzített
   feliratú helyfoglaló volt.

### Ami szándékosan kimaradt

- **`Folder::ID_HIER_FOLDER_EXPAND` / `ID_HIER_FOLDER_COLLAPSE`** („Az
  összes részletes nézete" / „Az összes kicsinyítése") és a `HierFolder`
  osztály: ezek a **hierarchikus (fa) mappanézethez** tartoznak. A bal
  panelen a Mappák-lista nálunk — az eredetihez hűen, ld.
  `ui-audit-mainwindow.md` 1.3/8 — **lapos**, almappa-szint és nyílglif
  nélkül; fanézet csak a Mappakezelő dialógusban van. Amíg nincs
  fa-mappanézet a bal panelen, ezeknek a parancsoknak nincs hova
  kerülniük. Nem kontextusmenü-hiány, hanem hiányzó nézet.
- **`AlbumListWin` / `AlbumListMac`** (Sajátgép · Dokumentumok · Képek ·
  Dokumentumok): platformspecifikus gyökérváltók, a PicasaPy Linux-first.
- **`Slingshot`** (Intéző héj-menü), **`Import`/`ImportGroups`**,
  **`CollageS`/`CollageD`/`Border`/`MMFilm`/`Dev`/`SyncOpts`/`BtnConf`**: a
  hozzájuk tartozó panel/integráció megvalósításakor esedékesek.


## A.5 Utólagos helyesbítés (2026-08-16, #757)

A bal hasáb mérő köre két hibát talált a fenti számokban, mindkettőt
UGYANAZ az ok magyarázza: a végigvezetés csak az `ID_`-előtagú kulcsokat
számolta meg, a string-táblában viszont **almenü-CÍMEK is vannak**, előtag
nélkül (`Folder::SortFolderBy`, `Album::SortAlbumBy`, `AlbumList::Shortcuts`).

1. **`AlbumList` = 12 tétel, nem 11.** A tizenkettedik az
   `AlbumList::Shortcuts` = „&Shortcuts" / „&Gyorsbillentyűk", és az
   `ui-audit-mainwindow.md` 1.7 szerint ez ALMENÜ CÍME: alatta ültek a
   gyökérváltók („a `Shortcuts` almenüben `AlbumListWin::ID_VIEW_ALL` =
   »My &Computer«"). Nálunk a három Windows-specifikus gyökérváltó kimarad,
   egyedül az Asztal maradna — egy egytételes, réteg nélküli almenü csak
   üres kattintást adna, ezért mindkettő lapos helyfoglaló sor. Az A.1 és az
   A.4 táblázata javítva.
2. **`Album` = 12 felirat, nem 11.** A tizenkettedik az `Album::SortAlbumBy`
   = „Sort &Album By" / „&Album rendezésének alapja…" — a mappa-menü „Mappa
   rendezésének alapja ▸" almenüjének album-párja.

Harmadikként a **feliratok** kerültek szó szerinti alakra: a menük addig a
saját, szabadon fogalmazott angol szövegüket használták (kilenc eltérés,
pl. „Reverse Sort Order" vs. `Re&verse sort`), és az öt menüfájlban
**egyetlen `&`-mnemonik sem** volt — vagyis az A.3 3. pontjában elvárt
Alt-navigáció nem működött. A `PicasaMenuItem` saját `contentItem`-je emiatt
sima `Text`-ről `IconLabel`-re cserélődött: az hozza a Qt mnemonik-tudatos
címkéjét, különben az ampersand nyersen látszana a menüben.

## B. ⛳ A helyi menük EGYETLEN menüből készülnek — kivonással (2026-09-14, 307. kör, #886)

*Forrás: a belépési pont `0x005e7c20`–`0x005e7ca3`, a táblavezérelt építő
`0x0056c5a0`, az első kapu ugrótáblája `0x0056e05c` + `0x0056e064`, a második
diszpécseré `0x0056e09c` + `0x0056e0b4`, az ágak `0x0056c665` · `0x0056c67d` ·
`0x0056c692` · `0x0056c6b3` · `0x0056c6d4` · `0x0056c6f8`, a törlő import
`[0x00c408b0]`.*

A #886 döntése után ez maradt nyitva: **melyik helyi menü melyik
felületrészhez tartozik**. A válasz szerkezeti, és megfordítja a kérdést.

### B.1 A lánc: 14 hívóhely → egy belépési pont → egy építő

| lépés | cím | mérés |
|---|---|---|
| a felületrészek | 14 hívóhely | `call 0x005e7c20` |
| a belépési pont | `0x005e7c20` | a **menüből** olvassa ki az azonosítót |
| az építő | `0x0056c5a0` | **pontosan két** hívója van, az egyik a fenti (`0x005e7c99`) |

A belépési pont nem kap kontextus-számot: a `[0x00c407bc]` importtal lekérdezi
a menütétel adatait, és a **`wID` szóból** veszi az azonosítót
(`0x005e7c8f movzx edx, word ptr [esp+0x2c]`), majd ezzel hívja az építőt.

### B.2 Az építő KILENC azonosítót enged tovább

Az első kapu (`0x0056c600`–`0x0056c62d`, ugrótábla `0x0056e05c`) a
`0x70`–`0xa4` tartományból **ötöt** enged a menüépítő ágra — `0x70`, `0x77`,
`0x8a`, `0x8b`, `0xa4` —, a többi 48 érték a kilépésre megy. Ezen felül
külön ág van a `0xa6`, a `0x127`, a `0x13d` és a `−1` értékre.

A második diszpécser (`0x0056c657`, ugrótábla `0x0056e09c`) **öt**
kontextus-specifikus ágat és egy közöset ad:

| ág | azonosító |
|---|---|
| `0x0056c665` | `0x77` |
| `0x0056c67d` | `0xa6` |
| `0x0056c692` | `0xa4` |
| `0x0056c6b3` | `0x70` |
| `0x0056c6d4` | `0x8a` |
| `0x0056c6f8` | minden más (közös ág) — ide esik a `0x8b` is |

### B.3 ⭐ A mechanizmus KIVONÓ, nem összeállító

Mind az öt ág ugyanazt teszi: a **már meglévő** menüből **töröl** tételeket.
A törlő a `[0x00c408b0]` import, három argumentummal — a `0x400` jelző a
`MF_BYPOSITION`:

| ág (azonosító) | törölt parancsazonosítók | törölt pozíció |
|---|---|---|
| `0x77` | `0x9d97` *(Feltöltés a Google Fotókba… — ALBUM)* | `0x0e` |
| `0xa6` | `0x9d97` *(ugyanaz)* | `0x15` |
| `0xa4` | `0x9d96` *(Feltöltés… — a kijelölt KÉP)*, `0xa09f` *(Megtekintés online)* | `0x14` |
| `0x70` | `0x9d96`, `0xa09f` | `0x16` |
| `0x8a` | `0x9d96`, `0xa09f` | `0x13` |

*(A nevek forrása és bizonyítéka: **B.5**.)*

⇒ **Az eredetiben nincs négy külön helyi menü.** Egy közös felugró menü van,
és a kontextus azt szabja meg, **mit vesznek ki belőle**. A mi négy külön
QML-menünk (`AlbumContextMenu`, `FolderContextMenu`, `CollectionContextMenu`,
`FolderListContextMenu`) ezért **szerkezetileg** tér el — a tételkészletek
karbantartása nálunk négy helyen történik, ott egy helyen plusz öt kivonás.

### B.4 ⛔ Amit ez NEM mond ki

- **A három parancsazonosító NEVE** (`0x9d96` = 40342, `0x9d97` = 40343,
  `0xa09f` = 41119) nincs meg: a `Picasa3.exe`-ben **nincs `RT_MENU`
  erőforrás** (az erőforrás-könyvtár típusai között a 4-es nem szerepel),
  tehát a menü kódból épül, és a feliratok a szövegtárból, azonosító szerint
  jönnek. A megnevezés útja: a `0x00730e65`, `0x007316b2`, `0x0073200c` és
  `0x0073244c` helyeken a `MENUITEMINFO.wID`-be írt azonosítók köré épülő
  `InsertMenuItem`-hívások felirat-forrása.
- **Melyik felületrész melyik azonosítót adja:** ✅ **LEZÁRVA** a **C.3**-ban
  — nem a hívóhelyek felől, hanem az azonosító ÍRÓJA felől
  (`SetMenuInfo`/`MIM_MENUDATA`, 25 menüépítő). Az alábbi, hívóhely-alapú
  terv ezért nem kell; a 14 cím itt marad, mert a menüépítés előzményét
  máshoz még adja: a 14 hívóhely
  (`0x0059606d`, `0x005d41f4`, `0x005d43a4`, `0x005e77b2`, `0x005e7b54`,
  `0x005e7be5`, `0x005e7d44`, `0x00622381`, `0x0063840c`, `0x0063b56b`,
  `0x0074626d`, `0x0082fbec`, `0x0082fcbb`, `0x0082fda9`) azonosítása
  külön kör — az azonosító nem a hívó argumentuma, hanem a menütételből jön,
  tehát a hívóhelyek menüépítő előzményét kell végigkövetni.

*(Mindkét pont MÉRVE a **B.5**-ben: az első megvan, a második a hívóhely →
menüépítő megfeleléssel együtt sem dőlt el — a jelölt magyarázat MEGDŐLT.)*

### B.5 ⭐ A három törölt parancs NEVE — megvan (2026-09-15, #3124)

#### A rekord-alak ebben az öt helyi-menü-építőben

A helyi menük ugyanazzal a gépies sablonnal épülnek, mint a menüsor, de a
rekord **más eltolásokkal**:

| eltolás | tartalom |
|---|---|
| `+0x00` | felirat (a fordított sztring) |
| `+0x04` | gyorsbillentyű-szöveg |
| `+0x0c` | módosítómaszk (szó) |
| **`+0x0e`** | **parancsazonosító (szó)** |
| lépésköz | **`0x14`** |

⚠️ **Ugyanaz a csúszás-csapda érvényes, mint a menüsornál** (#1409, a
`picasa-menu-parancsok.csv` fejléce): a fordító a rekord mezőit a
**KÖVETKEZŐ** rekord feliratának betöltése **után** írja ki, tehát a
`push "<kulcs>"` és az utána álló `mov word ptr […], 0x…` **NEM tartozik
össze**. A horgony itt is a rekord kezdőcíme: a `call <fordító>` UTÁNI
`mov dword ptr [<REK>], eax`.

**Kontroll (két, egymástól független ismert érték):**

| kulcs | a fenti szabállyal kiolvasva | a `picasa-menu-parancsok.csv`-ben |
|---|---|---|
| `AlbumPhoto::ID_PICTURE_VIEW` | `0x9ca0` | `0x9ca0` ✅ |
| `Album::ID_ALBUM_EDITCAPTIONS` | `0x9c69` | `0x9c69` ✅ |

#### A három név

| azonosító | felirat-kulcs | EN | HU | hol mérve |
|---|---|---|---|---|
| **`0x9d96`** (40342) | `Album::ID_UPLOAD_TO_LIGHTHOUSE` ⟋ `Album::ID_UPLOAD_TO_GOOGLE_PLUS_PHOTOS` | *Upload to &Picasa Web Albums…* ⟋ *Upload to Google &Photos…* | **Feltöltés a &Picasa Webalbumokba…** ⟋ **Feltöltés a Google Fotókba…** | `0x00730e65` (rek. `esp+0x1ec`) · `0x007316b2` (rek. `esp+0x1c4`) |
| **`0x9d97`** (40343) | `Album::ID_UPLOAD_ALBUM_TO_LIGHTHOUSE` ⟋ `…_GOOGLE_PLUS_PHOTOS` | ugyanaz | ugyanaz | `0x0073200c` (rek. `esp+0x1c4`) · `0x0073244c` (rek. `esp+0xe4`) |
| **`0xa09f`** (41119) | `CThumbUI::showinlh` | *View Online* | **Megtekintés online** | `0x0056c4c9` (`mov ecx, 0xa09f` a `0x00a6b120` tételhozzáfűző elé) |

Három megjegyzés, amit ez kimond:

1. **A `0x9d96` és a `0x9d97` ugyanaz a parancs, más hatókörrel**: az egyik a
   kijelölt **képe(ke)t**, a másik a teljes **albumot** tölti fel. A felirat
   mindkettőnél azonos, ezért pusztán a feliratból nem lettek volna
   megkülönböztethetők.
2. **A felirat futásidőben ágazik** (Lighthouse ⟋ Google+ Photos): ugyanaz a
   rekord két felirat-kulcs közül kapja az egyiket, a `je` ág dönt
   (`0x00730e03`, `0x007323f4`). A magyar szövegtár a `…GOOGLE_PLUS_PHOTOS`
   és a `…ALBUM_TO_*` kulcsokat **azonos** magyar mondatra fordítja
   (`Feltöltés a Google Fotókba…`); a „Picasa Webalbumok" csak a
   `Album::ID_UPLOAD_TO_LIGHTHOUSE` kulcson marad meg.
3. **A `0xa09f` másik sablonnal épül**: a `0x0056c450` (az *Online Actions*
   almenü építője) nem rekord-tömböt tölt, hanem tételenként hív —
   `push "<kulcs>" · mov eax, "<EN>" · call <fordító> · lea ecx, [tétel] ·
   push ecx · mov ecx, <azonosító> · call 0x00a6b120`. Itt az azonosító és a
   felirat **ugyanannak a hívásnak** az argumentuma, tehát nincs csúszás.
   Ugyanez a blokk adja a szomszédait is: `0xa0b3` = `CThumbUI::copyurl`
   (*Co&py URL*), `0xa0b4` = `CThumbUI::updateonline`
   (*Update Online Photo*).

⇒ **A kivonás értelme megvan:** az öt ág mindegyike az **online feltöltést**
(és ahol van, a *Megtekintés online*-t) veszi ki a közös menüből — azokban a
kontextusokban, ahol a kijelölt elem nem tölthető fel.

#### A 14 hívóhely menüépítője — MEGVAN mind a 14

| hívóhely | gazdafüggvény | menüépítő | az építő ELSŐ rekordja |
|---|---|---|---|
| `0x0059606d` | `0x00595fe0` | `0x007327a0` | `OneUp::ID_VIEWALBUM` = `0x9cc6` |
| `0x005d41f4` | `0x005d3290` | `0x007325a0` | `Publish::ID_CHECKALL` = `0x9d40` |
| `0x005d43a4` | `0x005d3290` | `0x00732160` | `Album::ID_ALBUM_EDITCAPTIONS` = `0x9c69` |
| `0x005e77b2` | `0x005e7650` | `0x007319f0` | `Folder::ID_HIER_FOLDER_EXPAND` = `0x9dc0` |
| `0x005e7b54` | `0x005e7830` | `0x00730790` | `AlbumPhoto::ID_PICTURE_VIEW` = `0x9ca0` |
| `0x005e7be5` | `0x005e7830` | `0x007339a0` | `BtnConf::ID_TOOLS_BUTTONMGR` = `0x9daf` |
| `0x005e7d44` | `0x005e7d10` | `0x00732ee0` | `AlbumPhoto::ID_PICTURE_VIEW` = `0x9ca0` |
| `0x00622381` | `0x00622320` | `0x00734a80` | `MMFilm::ID_MAKEMOVIE_INSERT` = `0x137` |
| `0x0063840c` | `0x00637fa0` | `0x00638990` | `PropertiesPanel::edit_keywords` (`push 0x9d2c`) |
| `0x0063b56b` | `0x0063b430` | `0x00735480` | `Tags::ID_APPLYTHISTAGTOSELECTION` = `0xa0b8` |
| `0x0074626d` | `0x00746170` | helyben épít (`0x00a6b120`) | — |
| `0x0082fbec` | `0x0082fab0` | `0x007344b0` | `CollageS::ID_COLLAGE_REMOVE` = `0x9dd3` |
| `0x0082fcbb` | `0x0082fc10` | `0x007347a0` | `CollageS::ID_COLLAGE_REMOVE` = `0x9dd3` |
| `0x0082fda9` | `0x0082fce0` | `0x007348f0` | `CollageD::ID_COLLAGE_SELECT_ALL` = `0x9ddd` |

#### ⛔ A kilenc kontextus-azonosító NEM dőlt el — és a jelölt magyarázat MEGDŐLT

A kézenfekvő olvasat az volt, hogy a belépési pont (`0x005e7c20`) a felugró
menü **első tételének** `wID`-jét olvassa ki, tehát a kilenc érték
(`0x70`, `0x77`, `0x8a`, `0x8b`, `0xa4`, `0xa6`, `0x127`, `0x13d`, `−1`) az
építők első rekordja volna. **A fenti táblázat ezt megcáfolja:** a 14 építő
első rekordja `0x9c69`…`0x9ddd` és `0x137` — a kilenc érték közül **egyik
sem** szerepel köztük.

Amit a struktúra-olvasás ad: a `[0x00c407bc]` hívás előtt a program a `0x1c`-t
és a `8`-at a *hívás előtti* `esp+0x24`, illetve `esp+0x28` rekeszbe írja, a
kiolvasás pedig a hívás utáni `esp+0x2c`-ről történik. Ez **nem áll össze**
szabványos `MENUITEMINFOW`-vá (annak `cbSize`-a `0x30`, a régi alaké `0x2c`;
a `0x1c` egyiké sem), tehát **maga az import-azonosítás sem biztos**.

⚠️ **Egy hamis nyom, hogy más ne járja újra:** mind a nyolc szám előfordul
`mov eax, <érték>; ret` alakban a `0x00633210`-ben — de az egy **EXIF-címke
név → szám** leképező (321 sztringje `ImageWidth`, `ExposureTime`, `FNumber`
és társai). Kis konstansoknál a puszta bájtegyezés nem lelet.

**A megnevezett következő lépés:** a `0x00c4xxxx` mutatótáblát induláskor egy
feloldó tölti fel (ugyanaz a tábla adja a `[0x00c406f8]`-at, amit a 3. szakasz
`GetKeyState`-ként azonosít). Ennek a feloldónak a név-táblájából kell
kiolvasni, mi a `[0x00c407bc]` — utána a mezőeltolás újraszámolható, és a
kilenc érték jelentése eldől.


## C. ⛳ A félkövér alapértelmezett tétel — és a kontextus-azonosító FORRÁSA (2026-09-18, #886)

*Forrás: az import-tábla saját parszolása (`SetMenuDefaultItem` →
`[0x00c408bc]`, `GetMenuInfo` → `[0x00c407bc]`, `SetMenuInfo` →
`[0x00c407c0]`, `RemoveMenu` → `[0x00c408b0]`), a két hívóhely
`0x0056dbd0` és `0x0056dbf6`, a beállító `0x00a6ae90` és annak 25 hívója.*

### C.1 Két alapértelmezett tétel van, és PARANCS szerint van kijelölve

A `SetMenuDefaultItem`-nek **egyetlen** hívó függvénye van, a táblavezérelt
menüépítő (`0x0056c5a0`), abban **két** hívóhely:

```
0x0056dbc8  push 0            ; fByPos = 0  ->  MF_BYCOMMAND
0x0056dbca  push 0x9cc6
0x0056dbd0  call dword ptr [0xc408bc]

0x0056dbee  push 0
0x0056dbf0  push 0x9ca0
0x0056dbf6  call dword ptr [0xc408bc]
```

- **`MF_BYCOMMAND`** (a harmadik argumentum `0`): az alapértelmezett tételt a
  **parancsazonosító** jelöli ki, nem a pozíció — a menü sorrendje nem
  befolyásolja.
- A választás a kontextus-azonosítón (`[esp+0xdc]`, az építő 2. argumentuma)
  múlik: `0x8a` → `0x9cc6`; `0xa4`, `0x70`, `0x8b` → `0x9ca0`; **minden más
  azonosító alapértelmezett tétel nélkül marad** (`0x0056dbb9 jne`).
- A blokknak **kapuja** van: a 4. argumentum (`[esp+0xe4]`) nullán az egészet
  átugorja. A helyi menü belépési pontja (`0x005e7c99`) `1`-et ad át, az
  építő másik hívója (`0x0056f418`) `0`-t — az utóbbi `-1` azonosítóval jön,
  tehát a **menüsor-úton eleve nincs** alapértelmezett tétel.

A két parancs feliratát a [`picasa-gyorsbillentyuk.md`](picasa-gyorsbillentyuk.md)
adja: `0x9ca0` = „Megjelenítés és szerkesztés" (`Enter`), `0x9cc6` =
„Visszatérés a könyvtárhoz" (`Esc`).

### C.2 ⛔ HELYESBÍTÉS: a `fMask = 8` **MIM_MENUDATA**, nem `MIM_STYLE`

A B.1 úgy fogalmazott, hogy a belépési pont „a menütétel adatait kérdezi le",
az ADR-013 és a [`picasa-gomb-es-menu-rendszer.md`](picasa-gomb-es-menu-rendszer.md)
pedig azt állította, hogy a `GetMenuInfo` egyetlen hívása **csak a stílust
olvassa**. Mindkettő téves, és a `WinUser.h` értékei döntik el:

| jelző | érték |
|---|---|
| `MIM_MAXHEIGHT` | `0x01` |
| `MIM_BACKGROUND` | `0x02` |
| `MIM_HELPID` | `0x04` |
| **`MIM_MENUDATA`** | **`0x08`** |
| `MIM_STYLE` | `0x10` |

A `MENUINFO` szerkezete `0x1c` bájt (`cbSize`, `fMask`, `dwStyle`, `cyMax`,
`hbrBack`, `dwContextHelpID`, `dwMenuData`), tehát a `dwMenuData` a `0x18`
eltoláson áll. A belépési pont a struktúrát `esp+0x14`-re teszi, és a hívás
után pontosan onnan olvas: `0x005e7c8f movzx edx, word ptr [esp+0x2c]` =
`0x14 + 0x18`. ⇒ **a kontextus-azonosító a menü `dwMenuData` mezője**, nem
egy menütétel `wID`-je. Ez egyben feloldja a B.6 kételyét is: a
`[0x00c407bc]` import-azonosítás helyes (`GetMenuInfo`), csak a `0x1c`/`8`
párost olvastuk `MENUITEMINFOW`-ként.

Az írói oldal ugyanezt mutatja. A `0x00a6ae90` (65 bájt) egy szűk beállító:
kinullázza a `MENUINFO`-t, a **szó méretű argumentumát** a `0x18`
eltolásra írja, `cbSize = 0x1c`, `fMask = 8`, majd `SetMenuInfo`:

```
0x00a6aea5  movzx eax, word ptr [esp + 0x20]   ; az azonosító
0x00a6aead  mov   dword ptr [esp + 0x18], eax  ; MENUINFO.dwMenuData
0x00a6aeb5  mov   dword ptr [esp + 8], 0x1c    ; cbSize
0x00a6aebd  mov   dword ptr [esp + 0xc], 8     ; MIM_MENUDATA
0x00a6aec5  call  dword ptr [0xc407c0]         ; SetMenuInfo
```

### C.3 ⭐ A B.4 második nyitott pontja LEZÁRVA: felületrész → azonosító

A B.4 azt mondta, hogy „melyik felületrész melyik azonosítót adja" külön kör,
mert az azonosító a menütételből jön. A C.2 után a kérdés más helyen dől el:
**minden menüépítő maga állítja be a saját azonosítóját** a `0x00a6ae90`-en
át. Annak **25 hívója** van, mindegyik egyetlen konstanssal:

| építő | azonosító | melyik menü | alapértelmezett tétel |
|---|---|---|---|
| `0x00730790` | `0x70` | mappa-nézetbeli **kép** | **`0x9ca0`** |
| `0x00731050` | `0xa4` | album-nézetbeli **kép** | **`0x9ca0`** |
| `0x00732ee0` | `0x8b` | **képtálca** | **`0x9ca0`** |
| `0x007327a0` | `0x8a` | **néző** (OneUp) | **`0x9cc6`** |
| `0x007319f0` | `0xa6` | **mappa** | — |
| `0x00732160` | `0x77` | **album** | — |
| `0x00733a40` | `0x127` | gyűjtemény/mappalista | — |
| `0x007355c0` | `0x13d` | **Emberek**-album képe | — |
| `0x007359e0` | `0x13c` | **Emberek**-album | — |
| `0x007325a0` | `0xa5` | **Publish** kijelölésmenü (`Select All` / `Select None`) | `Publish::ID_CHECKALL`, `Publish::ID_UNCHECKALL` |
| `0x00732680` | `0x88` | **Gyűjtemény** helyi menüje | `Collection::ID_*` |
| `0x007331e0` | `0xd8` | **Szöveg-/címmező** helyi menüje | `Address::ID_*` |
| `0x00733480` | `0x86` | **AlbumList / bal oldali könyvtárnézet** menüje | `AlbumList::ID_VIEW*`, `AlbumList::Shortcuts` |
| `0x007339a0` | `0x126` | **Gombok konfigurálása** menüje | `BtnConf::ID_TOOLS_BUTTONMGR` |
| `0x00733c70` | `0x128` | **Importálás: fájl be-/kihagyása** menüje | `Import::ID_IMPORT_INCLUDE*` |
| `0x00733e00` | `0x13f` | **Importcsoportok kezelése** menüje | `ImportGroups::ID_IMPORT_MANAGE_GROUPS` |
| `0x00733ea0` | `0x13e` | **Feltöltési/szinkronizálási opciók** menüje | `ImpULOpts::ID_*`, `SyncOpts::ID_*` |
| `0x007344b0` | `0x12f` | **Kollázs: egy kijelölt kép** menüje | `CollageS::ID_COLLAGE_*` |
| `0x007347a0` | `0x130` | **Kollázs: több kijelölt kép** menüje | `CollageS::ChangeBorder`, `CollageS::AlignRotation` |
| `0x007348f0` | `0x131` | **Kollázs: elrendezési műveletek** menüje | `CollageD::ID_COLLAGE_*` |
| `0x00734a80` | `0x136` | **Film: dia helyi menüje** | `MMFilm::ID_MAKEMOVIE_*` |
| `0x00734bc0` | `0x13a` | **Online album szinkronizálási** menüje | `SyncOpts::ID_*` |
| `0x00735480` | `0x13b` | **Címke** helyi menüje | `Tags::ID_*` |
| `0x007a60a0` | `0x64` | **Feltöltési kép-méret** almenüje | `UploadOptionMenu::usesize*` |
| `0x007a6590` | `0x65` | **Feltöltési láthatóság** almenüje | `UploadOptionMenu::onlyou`, `private`, `public` |

A „melyik menü" oszlop most már **mind a 25 íróra** ki van töltve. A hat
korábban ismert főmenü mellett a maradék 19 is azonosítható a saját
menüosztály-neveiből és feliratkészletéből; a `dwMenuData` értéke nem a menü
első tételének `wID`-je, hanem a menüépítő által beállított kontextusrekesz.
A tábla ezért a fő helyi menük mellett a menüosztályhoz tartozó műveleti és
almenü-építőket is felsorolja.

### C.4 Mit változtatott ez nálunk

A „Megjelenítés és szerkesztés" (`PhotoContextMenu`) és a „Visszatérés a
könyvtárhoz" (`ViewerContextMenu`) már félkövér volt. Új a **képtálca**
menüje: a `0x8b` azonosító miatt ott is félkövér az első tétel
(`trayMenuViewAndEdit`, ugyanaz a `0x9ca0` parancs). Fordítva is őrizzük: a
mérés szerint a Picasa **soha** nem jelöl más parancsot alapértelmezettnek,
tehát a többi helyi menünkben nem lehet félkövér tétel.

⛔ **Amit ez NEM ad meg:** a félkövér betűkép képpontos egyezését az
XP-menüével. Az ADR-013 kimondja, hogy az XP-menü metrikái sem a binárisból,
sem mai képernyőképből nem szerezhetők meg.

Őr: `tests/app/qml_functional/test_felkover_alapertelmezett_886.py`.

### C.5 A 25-ös térkép független ellenőrzése (#3364)

A lelet nem csak a korábbi kommentek átírása:

- **PE-minta:** a vizsgált `Picasa3.exe` SHA-256 értéke
  `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`;
- **SQLite-index:** a `xrefs` táblában a `0x00a6ae90` írófüggvénynek **25
  különböző hívója** van; a `0x005e7c20` belépési pontnak **12 hívója**,
  amelyek összesített `call_count` értéke **14**;
- **független bájtpásztázás:** a `.text`-ben a relatív `E8` hívásokból
  **25** vezet a `0x00a6ae90`-re, **14** a `0x005e7c20`-re és **2** a
  `0x0056c5a0`-ra. Az import-hivatkozás alakja (`FF 15 <cím>`) a
  `0x005e7c89` helyen a `GetMenuInfo`, a `0x00a6aec5` helyen a `SetMenuInfo`
  hívását adja;
- **célzott diszasszemblálás:** a `0x005e7c20` törzse `cbSize = 0x1c`,
  `fMask = 8` után a `MENUINFO` `dwMenuData` mezőjét olvassa, és a
  `0x005e7c99` helyen átadja a `0x0056c5a0` építőnek. A 25 hívó törzsében a
  `call 0x00a6ae90` közvetlen előzménye minden esetben a táblázatban szereplő
  `push <azonosító>`;
- **saját oldal:** a forrásfában jelenleg tíz `*ContextMenu.qml` komponens
  van: `Photo`, `Album`, `Folder`, `Collection`, `Viewer`, `Tray`,
  `FolderList`, `PeopleAlbum`, `Tag` és `TextField`. Ez nem négy eredeti
  kontextus összevonását támasztja alá: a Picasa 25 írója több főmenü- és
  almenüosztályt különböztet meg, a mi komponenseink pedig ezeknek csak a
  jelenleg felvett felületi szeletét fedik.

**Következtetés:** a #3364 kérdése binárisan **lezárva**: minden
`dwMenuData`-értékhez megvan a menüosztály és a felületi jelentés. A négy QML-
menü összevonása ebből nem következik; új fejlesztői jegyet erre a leletre
nem nyitunk. A hiányzó tételek és bekötések külön fejlesztői jegyek tárgyai.

## D. ⛳ Az indexkép helyi menüje a binárisból: a „Keresés” almenü FELTÉTELES, és csak KÉT tétele van (2026-09-22, 340. kör, #3456)

*Forrás: a két rekordtábla-építő (`0x00730790` mappa-nézet, `0x00731050`
album-nézet) felirat-kulcsainak sorrendje · a közös utófeldolgozó
`0x0056c5a0`, `0x0056d664`–`0x0056d8f0` · a kijelölési állapotmaszk
`0x00562c10` → `0x005cb1a0` · az oszlop-mutatók betöltője `0x004a6ba6`–
`0x004a6bb2` · `stringres-en-hu.tsv` · `picasa-imagedata-rekord.md`
eltolás-táblája.*

### D.1 A rekordtábla tételsora — szó szerint

A `0x00730790` (kontextus `0x70`, mappa-nézetbeli kép) felirat-kulcsai
sorrendben (a gyorsbillentyű-szöveg kulcsa zárójelben):

| # | kulcs | magyar felirat |
|---:|---|---|
| 1 | `AlbumPhoto::ID_PICTURE_VIEW` (`CMenuBar::Enter`) | Megjelenítés és szerkesztés |
| 2 | `AlbumPhoto::ID_LABELS` | **Hozzáadás az albumhoz** |
| 3 | `OneUp::ID_PICTURE_ROTATECLOCKWISE` | Forgatás jobbra |
| 4 | `AlbumPhoto::ID_PICTURE_ROTATECOUNTERCLOCKWISE` | Forgatás balra |
| 5 | `FolderPhoto::ID_PICTURE_REVERT` | Összes szerkesztés visszavonása |
| 6–7 | `AlbumPhoto::ID_PICTURE_HIDE` / `…_UNHIDE` | Elrejtés / Megjelenítés |
| 8 | `FolderPhoto::ID_ALBUM_NEW` | Áthelyezés új mappába… |
| 9 | `FolderPhoto::ID_PICTURE_SPLITALBUMHERE` | Mappa felosztása itt… |
| 10 | `OneUp::ID_FILE_OPENINANEDITOR` | Fájl megnyitása |
| 11 | `AlbumPhoto::ID_FILEOPENWITH` | Társítás |
| 12–13 | `AlbumPhoto::ID_FILE_SAVE` / `…_REVERT` | Mentés / Visszaállítás |
| 14 | `FolderPhotoWin::ID_FILE_LOCATEONDISK` (`CMenuBar::Enter`) | **Keresés a lemezen** — lapos tétel, `cmd 0x9c99` (a csúszás-szabály szerint a `0x00730d10`-nél íródik) |
| 15 | `FolderPhoto::ID_FILE_DELETEFROMDISK` (`CMenuBar::Delete`) | **Törlés a lemezről** |
| 16 | `AlbumPhoto::ID_COPY_PATH` | Teljes elérési út másolása |
| 17 | `Album::ID_UPLOAD_TO_…` | Feltöltés … |
| 18 | `Album::ID_ONLINE_ACTIONS` | (online műveletek almenü, `0x0056c450`) |
| 19 | `AlbumPhoto::ID_SUPPRESS` | Feltöltés tiltása |
| 20 | `AlbumPhoto::ID_PICTURE_RESET_FACES` | Arcok alaphelyzetbe állítása |
| 21 | `AlbumPhotoWin::ID_PICTURE_PROPERTIES` (`CMenuBar::Enter`) | Tulajdonságok |

Az album-nézet építője (`0x00731050`, kontextus `0xa4`) ugyanez, **két
eltéréssel**: nincs „Mappa felosztása itt…”, és a „Keresés a lemezen” UTÁN
egy **külön, lapos** tétel áll: `AlbumPhoto::ID_FILE_LOCATEINPICASA` =
**„Keresés a Picasában”** (`0x007314f7`). A törlés kulcsa itt
`AlbumPhoto::ID_FILE_DELETEFROMDISK`, magyarul **„Eltávolítás az
albumból”**.

⇒ **Hasonlóság-keresés egyik építőben sincs.** A `loadsim` a keresősáv
parancsa (`searchoptions/loadsim`, `Ctrl+F7` — `picasa-gyorsbillentyuk.md`),
helyi menüből nem érhető el.

### D.2 ⭐ A „Keresés” almenü: az utófeldolgozó FELTÉTELESEN cseréli be

A rekordtábla lapos „Keresés a lemezen” tételt épít. A közös utófeldolgozó
(`0x0056c5a0`) a `0x0056d821`–`0x0056d8e0` sávban **lecseréli** egy
„Keresés” almenüre — de csak így:

```
kontextus ∈ { 0x70 mappa-kép · 0xa4 album-kép · 0x8a néző · 0x8b képtálca }
ÉS  maszk & 0x200 == 0          ; 0x0056d842 — NEM több kép van kijelölve
ÉS  maszk & 0x80  != 0          ; 0x0056d84e — a kijelölt kép VISSZAÁLLÍTHATÓ
⇒  CreatePopupMenu ([0x00c408f0])
     + „&Fájl a lemezen\tCtrl+Enter”   cmd 0x9c99  (CThumbUI::locateondiskmenu, 0x0056d887)
     + „Eredeti &a lemezen”           cmd 0xa0aa  (CThumbUI::locateorigondiskmenu_win, 0x0056d8b3)
   → a 0x9c99 tétel helyére „Keresés” (CThumbUI::locatemenu, 0x0056d8db)
```

**Az almenünek KÉT tétele van**, nem három: a „Keresés a Picasában”
(`IDS_LOCATE_SOURCE_IMAGE`) NEM tagja.

A két maszkbit forrása (`0x005cb1a0`, a kijelölésre számolva, a nézet
`+0x34a8`-as gyorsítótárában):

| bit | feltétel | bizonyíték |
|---|---|---|
| `0x200` | a kijelölt képek száma **> 1** | `0x005cb2a9` `cmp edi,1` → `0x005cb2ae` |
| `0x80` | legalább egy kijelölt kép **`revertable`** oszlopa nem nulla | `0x005cb3cf`/`0x005cb53f` → `0x005c6250` |

A `revertable` azonosítása: a `0x005c6250` a `[obj+0x2c4]` `CColumn`-ból
olvas egy **bájtot** a kép indexével (`0x005c62b3`–`0x005c62d1`). Az
objektum oszlopmutatóit a `0x004a6ba6`–`0x004a6bb2` tölti be a gazdából:
`+0x2c0` = gazda+`0x1838`, **`+0x2c4` = gazda+`0x1898`**, `+0x2cc` =
gazda+`0x114c`. Az `imagedata`-gyűjtemény a gazda `+0xf20`-án ül, tehát ezek
a gyűjtemény `+0x918` (`edited`), **`+0x978` (`revertable`, i8)** és
`+0x22c` (`filetype`) oszlopa (`picasa-imagedata-rekord.md`, 21–22. és 3.
sor).

⇒ **Az almenü csak akkor jelenik meg, ha EGY kép van kijelölve, és annak
van visszaállítható eredetije** — épp ezért kínálja az „Eredeti a lemezen”-t.
Minden más esetben a lapos „Keresés a lemezen” marad.

### D.3 A felirat-cserék a néző és az album-kép menüjében

Ugyanitt (`0x0056d664`–`0x0056d7c5`) a `0x8a` (néző) és a `0xa4`
(album-kép) kontextusban a maszk `0x10` bitje szerint két felirat cserélődik:
a törlésé (`cmd 0x9c9a`) `IDS_REMOVE_FROM_LABEL` / `IDS_DELETE_FROM_DISK`,
és — **csak a nézőben** (`0xa4`-nél a `0x0056d705` átugorja) — a keresésé
(`cmd 0x9c99`) `IDS_LOCATE_SOURCE_IMAGE` („Keresés a Picasában”) /
`IDS_LOCATE_ON_DISK`. A rács (mappa-kép, `0x70`) menüjét ez nem érinti.

### D.4 A törlés gyorsbillentyűjének szövege

A rekord gyorsbillentyű-szövege a `CMenuBar::Delete` kulcs (`0x00c8c494`),
magyarul **„Törlés”**; az előtagot a módosítómaszk adja, szintén honosítva
(`ytMenu::CtrlPrefix` = „Ctrl+”, `picasa-gyorsbillentyuk.md` 3.2) ⇒ a
magyar felületen **„Ctrl+Törlés”**. A billentyű maga `Ctrl+Delete` — a #1418
döntése (helyi menüben `Ctrl+Delete`, menüsávban `Delete`) **helyes**; csak a
kiírt szövegnek kell honosítottnak lennie.

### D.5 Eredeti / nálunk / teendő (mai PhotoContextMenu.qml, #4462 mérés)

| tétel | eredeti | nálunk | állapot |
|---|---|---|---|
| 2. felirat | Hozzáadás az albumhoz | Hozzáadás az albumhoz (picasapy_hu.ts) | megvan és a hivatalos fordítással egyezik |
| Keresés | Lapos Keresés a lemezen, kivéve egy visszaállítható kép kijelölését; akkor kéttételes Keresés almenü: Fájl a lemezen és Eredeti a lemezen | Lapos Locate on Disk alapállapotban; egyetlen visszaállítható kép esetén pontosan kéttételes Locate almenü; a szülőmenü nem marad látható | megvan; a feltétel és mindkét almenütétel egyezik |
| Keresés a Picasában | Album-nézetben külön, lapos tétel a Keresés a lemezen után | Külön, lapos Locate in Picasa tétel az album- és Emberek-nézetben | az albumtétel megvan; az Emberek-nézet a jelenlegi kód többlete |
| Keresés hasonló képekre | Nincs ebben a menüben; a keresősávban Ctrl+F7 | Nincs a PhotoContextMenu.qml-ben | megfelel |
| Törlés felirata | Törlés a lemezről | Törlés a lemezről (picasapy_hu.ts) | megvan és a hivatalos fordítással egyezik |
| Törlés billentyűszövege | Ctrl+Törlés | Ctrl+Törlés (honosított Ctrl+Delete fordítás) | megvan |

A korábbi D.5 „nálunk” oszlop a #3468 előtti állapotot rögzítette; a fenti oszlop a #4462 idején olvasott forráskódot tükrözi, az eredeti oszlop marad a mérce.

⛔ **Helyesbítés** a `picasa-menu-parancsok-viselkedes.md` 31.2-höz (és a
#1613-hoz): az almenü **nem háromtételes**, és **nem mindig** jelenik meg —
ld. D.2. A „Keresés a Picasában” a `0x0056c5a0`-ban csak a néző
feliratcseréjeként (D.3), az album-nézet rekordtáblájában pedig külön
tételként (D.1) szerepel.

*Bizonyítottsági fok:* a tételsor, az almenü-feltétel és a két bit
**megerősített**; a `revertable` azonosítása **erős** (az oszlopmutató
betöltése és a bájtos elemolvasás egyezik az eltolás-táblával; hogy a
`0x005c6250` `obj`-ja ugyanaz az osztály, mint a `0x004a66e0`-é, azt a
nézet `+0x2c0` mezőjén át közvetlenül nem követtük végig).

### D.6 Nyitott kérdések mérlege

- a menü tételsora, a „Keresés” almenü, a hasonlóság-keresés helye —
  **LEZÁRVA** (D.1, D.2);
- a „Hozzáadás az albumhoz” felirat — **LEZÁRVA** (D.1);
- a törlés billentyűnevének honosítása — **LEZÁRVA** (D.4);
- a maszk `0x10` bitjének pontos jelentése (a D.3 feliratcseréje) —
  **HATÓKÖRÖN KÍVÜL**: a rács menüjét nem érinti, és a mi nézőnk helyi
  menüje nem tárgya a jegynek (340. kör döntése).

`0 nyílt · 3 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva`

### D.8 ⭐ A Csillagozott fotók (`]star`) gyűjteményben a törlés a CSILLAGOT veszi le, a fájl marad (2026-10-11, #4883)

*Előzmény: a #4621 D.7 szakasza (a néző `Ctrl+Delete`-je; a `0x9c9a`
kezelője `0x005cbaef` → az ágválasztó `0x005c9b00`). A D.7 a Csillagozott
sort csak **következtette** az ágtáblából; ez a szakasz utasításszinten
végigköveti. Forrás: `0x005c9b00` (`0x005c9bce`–`0x005c9d4d`,
`0x005c9de4`–`0x005c9e3a`, `0x005c9ec7`–`0x005ca07a`) · `0x0045ecf0` ·
`0x004da1d0` · `0x0044db30` (`CThumbDB` vtábla `0x00c81fa4`, `+0x28`) ·
az ini-betöltő `0x00456610` (`0x00458c53`–`0x00458d17`) · a címke-figyelő
`0x004a51f0` (`CAlbumState::vftable` `0x00c836b4`) · `0x005ed240` · mérés:
`research/testdata/Picasa2/db3/albumdata_*.pmp` · szövegek:
`stringres-en-hu.tsv`.*

#### D.8.1 A Csillagozott album nem kap külön ágat — az eltávolító ágra esik

**Indextől független pásztázás** (a `]star` literál `0x00c811d4` mint
4 bájtos operandus, és közvetlen `call rel32` a két `]star`-predikátumra,
`0x004acaf0` és `0x004aa0b0`, a teljes `.text`-en):

| tartomány | `]star`-literál | `]star`-predikátum hívása |
|---|---:|---:|
| `0x005c9930`–`0x005cb170` (szövegező + ágválasztó) | 0 | 0 |
| `0x005cb990`–`0x005cdd00` (parancsdiszpécser) | 0 | 0 |
| `0x005fd160`–`0x005fe090` (megerősítő ablak, szövegezők) | 0 | 0 |

A predikátumok egyetlen közvetlen hívója `0x006644c8` (a „Hozzáadás az
albumhoz” almenü építője) és `0x005666e5` (`CStarSync`, lásd D.8.6). ⇒ A
törlés útján **sehol nincs `]star`-specifikus elágazás**; a Csillagozott
album sorsát a D.7.2 általános feltételei döntik el:

| feltétel | cím | a `]star` albumra | bizonyíték |
|---|---|---|---|
| mappa-e (`0x004461a0` = üres útvonal → album) | `0x005c9bd5` | **album** | mérés: a valódi `albumdata_filename.pmp` 0. sora (token `]star`) üres; ugyanígy a `]search` sora (2366.), amelyet a kód épp ezen az ágon belül vizsgál · bináris: a `0x005ed240` a `]star`-vizsgálatát (`0x005ed2dc`) szintén a `0x004461a0` igaz ága (`0x005ed278 jne`) mögött végzi |
| `]ignoreface`? | `0x005c9c17` | nem | literál-összevetés |
| `]search`? | `0x005c9c5c` | nem | literál-összevetés |
| ⇒ | `0x005c9c8d je 0x005c9d4b` | **eltávolító ág** | — |

#### D.8.2 A megerősítés — ugyanaz, mint bármely albumnál

Az eltávolító ág a 3. argumentumra (a `0x005cbb0e`-n `1`) megerősít:
`0x005c9930(ui, lista, 0, albumid, 1, 1, 0, &dlg)` (`0x005c9e2f`), majd
`0x005fd670` (`0x005c9e3a`). A `0x005c9930` két felülírója:

| felülíró | mit vizsgál | `]star`-ra |
|---|---|---|
| `0x00448c90` → fajta 2 (Emberek) | az album 64 bites kapcsolat-azonosítója (`db+0x2748` tábla, `0x00449020`) ≠ 0 | hamis — mérés: a valódi `albumdata_albumcontactids.pmp` **0 sort** tartalmaz (erős: a `db+0x2748` ↔ pmp-oszlop megfeleltetés nincs utasításszinten igazolva) |
| `0x00448a10` → fajta 3 (Névtelen emberek) | a token egyezik-e a `db+0x2e98` / `db+0x2e94` sztringgel (a `]unknownface`-ág ugyanezeket használja, `0x005c9fa6`) | hamis |

A `0x005c9930` hívásai között (`0x00448c90`, `0x00448a10`, `0x00926c20`,
`0x005fd160`, `0x005fd1c0`, `0x005fdc30`) nincs más token-vizsgálat. ⇒
**fajta 1 (album)**, a D.7.3 albumsora:

| elem | érték (hivatalos magyar) | kulcs |
|---|---|---|
| cím | Elemek eltávolítása | `DeleteMessage::RemoveItemsTitle` |
| kérdés, egy kép | *Biztosan eltávolítja a kijelölt képet a jelenlegi albumból?* | `DeleteMessage::RemoveSingle` |
| kérdés, több kép | *Biztosan eltávolítja a kijelölt %d képet a jelenlegi albumból?* | `DeleteMessage::RemoveMultiple` |
| igen-gomb | Kép eltávolítása / Képek eltávolítása | `RemoveSingleYesButton` / `RemoveMultipleYesButton` |
| jelölőnégyzet | *Ne kérdezzen újból, mindig távolítsa el* | `Preferences\DoNotConfirmRemoveFromAlbum` (változat 5, D.7.3) |

A szöveg tehát „a jelenlegi albumból” beszél — **nem** említi a csillagot.

#### D.8.3 Az eltávolítás maga: a `]star` CÍMKE levétele = a csillag levétele

Megerősítés után (`0x005c9ec7`): `0x00448c90` hamis → `0x00448a10` hamis
(`0x005c9f10 je 0x005c9fd1`) → `0x00717140` a kijelölés-csomóponton →
**`0x0045ecf0(db, &lista, albumid)`** (`0x005c9fe9`).

1. **A `0x0045ecf0` az album TOKENJÉT veszi kulcsnak.** A `db+0xaf0` tábla
   `+0x58` → `+0x48` tömbjéből olvas `albumid` indexszel (`0x0045ed44`,
   `0x0045ee5e`–`0x0045ee61`). Ugyanezt a tömböt olvassa a `CThumbDB`
   `+0x28` slotja, a `0x0044db30` (`[this+0xaa8]`, ahol `this = db+0x48`;
   `0x0044db32`, `0x0044db8b`–`0x0044db8e`) — és ez az a slot, amelyből a
   `0x005c9b00` a `]ignoreface`/`]search` tokent kapja (`0x005c9bf5`). A
   Csillagozott albumnál a kulcs tehát **`]star`**.
2. **A címke levétele:** `0x004da1d0(eax = &kulcs, db+0x68, lista, 1)`
   (`0x0045ef25`–`0x0045ef31`): a `db+0x68` címketábla hasítójában
   megkeresi a kulcsot (`0x004da26d`–`0x004da2a9`), és a tagtömbből kiveszi a
   kijelölt képeket (`0x004da390`–`0x004da3f1`).
3. **A `]star` címke = a csillag.** Az ini-betöltő ugyanezt a hívást
   használja a `star` kulcsra: `star=yes` (kis-nagybetű-független,
   `0x00458c73`–`0x00458cbe`) → `0x004d9aa0(&"]star", db+0x68, …)`
   (`0x00458cc4`–`0x00458ce9`), egyébként → `0x004da1d0(&"]star", db+0x68,
   …)` (`0x00458cf4`–`0x00458d17`). Visszafelé a címke-változás figyelője,
   a `0x004a51f0` (`CAlbumState`) a `]star` tokent a **`star`** ini-kulcsra
   képezi (`0x004a5333`–`0x004a5347`; ugyanígy `]hidden` → `hidden`,
   `]screensaver` → `screensaver`).
4. A `CThumbDB` vtábla `+0xc8` slotja (`0x004744d0`, a csillag beállítója) is
   a `]star` címkén dolgozik (`0x00474520 mov edx, 0xc811d4` →
   `0x00475250`), a `+0xcc` slot (`0x004755d0`) a lekérdezője — a
   csillag a binárisban **mindenütt** ez a címke.

Utána: a `0x004aca00(albumid)` (= a token nem `]album:`/`]facealbum:`,
`0x004aca3c`/`0x004aca50`) a `]star`-ra igaz, ezért a `CThumbDB` `+0xec`
slotja (`0x00451ff0`) **kimarad** (`0x005c9ffc jne`); a felület frissül
(`0x0065b840(ui, 0, 0, 1)`, `0x005ca074`–`0x005ca07a` → `0x005c9dc7`).

⇒ **A Csillagozott fotók albumban a törlés-parancs leveszi a kijelölt képek
csillagát** (a `star=yes` kikerül a `.picasa.ini`-ből); a fájl a lemezen
marad, és a kép kiesik a Csillagozott albumból. Lemezes törlés
(`0x009929b0`) ezen az úton nincs. A Shift **nem számít** (a 2. argumentumot
csak a lemezes ág olvassa, D.7.5).

*Bizonyítottsági fok:* az ágválasztás, a token-kulcs azonossága, a
`0x004da1d0` címke-levétele és az ini-betöltő `star` ↔ `]star` megfeleltetése
**megerősített** (utasításszinten, a literálok programmal kiolvasva). A
`]star` album üres útvonala **mérés** (valódi `albumdata_filename.pmp`). A
figyelő (`0x004a51f0`) ini-írását a kulcsválasztásig követtem, a tényleges
fájlírásig nem — **erős**.

#### D.8.4 Rács, néző, menüsáv — egyformán

A D.7.1 szerint a menüsáv `Delete`-je (Fájl ▸ Törlés), a rács és a néző
helyi menüjének törlés-tétele és a `Ctrl+Delete` **ugyanazt** a
`0x005c9b00(ui, !Shift, 1, 1)` hívást váltja ki; a felület nem számít. Az
egyetlen különbség a kijelölés-csomópont: ha a kép **a Csillagozott albumból**
van kijelölve vagy megnyitva (`+0xea8 == +0xeac`), az eltávolító ág fut; ha a
**tálcáról** (`+0xea8 = +0xea4 ≠ +0xeac`), a lemezes ág (`0x005c9b55`) — ez a
D.7-tel azonos, nem `]star`-függő.

A felirat ugyanezt mutatja: a maszk `0x10` bitje (D.7.4) a `]star` albumra
beáll (album, és nem `]search`), tehát a néző és az album-kép menüjében
**„Eltávolítás az albumból”** (`IDS_REMOVE_FROM_LABEL`), nem „Törlés a
lemezről”.

#### D.8.5 Ha maga az album a cél: „A csillagozott fotók albuma nem törölhető.”

Ha nincs kép kijelölve, és a 4. argumentum nem nulla (maga a gyűjtemény a
kijelölés, D.7.2 `0x005c9b70`–`0x005c9b98`), a `0x005ed240` (album-törlés)
fut. Ez a `]star` tokent **külön** vizsgálja (`0x005ed2dc`–`0x005ed30d`), és
törlés helyett üzenetet ad: `CThumbUI::DeleteStarAlbum` (`0x005ed30f`,
`0x00980700`) — *„A csillagozott fotók albuma nem törölhető.”* —, majd
kilép (`0x005ed61a`).

#### D.8.6 Mellékleletek, és ami nyitva marad

- **`CStarSync`** (`vftable 0x00c90b40`): a 2. slot (`0x00563580`) `4`-et
  ad, ha a jelenlegi gyűjtemény (`+0xeac`) a `]star` album (`0x005666b0` →
  `0x004aa0b0`), különben `8`-at. Hogy a felületen mit vezérel, **NYITOTT
  KÉRDÉS** — megszerzése: a `CStarSync` példányát létrehozó kód
  (`find_data_refs.py 0x00c90b40`) és a `+0x8` slot hívóhelyének követése.
  A törlés útját nem érinti (D.8.1 pásztázás).
- **A keresősáv ★ szűrője (`searchcontainer/starsearch`) MÁS állapot**,
  mint a Csillagozott album: az eredetiben szűrő, nem gyűjtemény-választás.
  Hogy szűrő közben mi a jelenlegi gyűjtemény (`+0xeac`: a kiválasztott
  mappa/album, vagy a `]search`), és ezért ott a törlés lemezes-e,
  **NYITOTT KÉRDÉS** — megszerzése: a `0x00660c80` `starsearch`-kezelőjének
  (`]star` hivatkozás `0x006615db`) követése a `+0xea8`/`+0xeac` írókig
  (D.7.6 öt írója), vagy Colab-végrehajtós viselkedési próba
  (`tipus:behavior`): szűrő be, mappa kiválasztva, `Delete`, az ablak címe.

#### D.8.7 Nálunk (2026-10-11, a `main`-en)

A PicasaPy **egyetlen** `("starred", "")` nézetmóddal szolgálja ki a bal
hasáb „Csillagozott fotók” bejegyzését (`Main.qml` `onStarredChosen`) **és**
a keresősáv ★ szűrőjét (`MainToolbar.qml` `starFilter`) —
`controller.showStarred`. A `currentAlbumToken` itt üres
(`controller.py` `currentAlbumToken`: csak `"album"` módban nem üres), ezért:

| belépő | mit tesz ma a Csillagozottban | az eredeti (D.8.3–D.8.4) |
|---|---|---|
| menüsáv `Delete` / Fájl ▸ (`PicasaMenuBar.activateDeleteCommand`, #1608) | `deleteRequested` → **lemezről töröl (Lomtár)** | csillag le, fájl marad |
| rács `Ctrl+Delete` és helyi menü (`contextMenuDelete`) | „Törlés lemezről” → **lemezről töröl** | „Eltávolítás az albumból” → csillag le |
| néző `Ctrl+Delete` és helyi menü (a #4621 után) | `deleteRemovesFromAlbum` hamis → **lemezről töröl** | „Eltávolítás az albumból” → csillag le |
| megerősítés | a lemezes törlés ablaka (`fileOpsDialogs.openDelete`) | „Elemek eltávolítása” / `RemoveSingle`, `DoNotConfirmRemoveFromAlbum` |
| nincs kijelölt kép, album-törlés | nincs ilyen út (a „Csillagozott fotók” sornak nincs helyi menüje, `AlbumsSection.qml` `starredMouse`) | „A csillagozott fotók albuma nem törölhető.” |

⇒ **Eltérés, adatvesztés-jellegű**: a mi Csillagozott nézetünk a fájlt
Lomtárba teszi, az eredeti csak a csillagot veszi le. Megvalósítás: #4883
(„Kész, ha” pontok a jegyen). A ★ szűrő viselkedése a D.8.6 nyitott kérdéséig
**nem változik** — ehhez a két belépőt a nézetmódban szét kell választani.

#### D.8.8 Nálunk a #4883 után

| belépő | megvalósítás |
|---|---|
| Bal hasáb „Csillagozott fotók” (`AlbumsSection.qml` `starredItem`) | Külön `starred_album` mód; a `currentAlbumToken` értéke `]star`. A menüsáv Delete-je, a rács Delete-je és a néző Ctrl+Delete-je az albumeltávolító ágat hívja. |
| Rács- és néző-helyi menü | „Remove from Album” (`picasapy_hu.ts`: „Eltávolítás az albumból”); nincs lemezes törlési tétel. |
| Megerősítés | „Remove Items” / `RemoveSingle`; a „Ne kérdezzen újból, mindig távolítsa el” beállítás változatlanul érvényes (`DoNotConfirmRemoveFromAlbum`). |
| Művelet | A `removeRowsFromAlbum` a `]star` tokennél a `star` kulcsot távolítja el az `ini` API-n keresztül; a fájl megmarad és kiesik a Csillagozott albumból. |
| Eszköztári ★ szűrő | A korábbi `starred` módot használja, üres albumtoken-nel; a D.8.6 nyitott kérdéséig a viselkedése változatlan. |

Az új felületi regresszióteszt mindhárom fő belépőt végigviszi, a fájl
megmaradását `Path.exists()`-szel, a csillag levételét pedig az ini-modellen
ellenőrzi. A `kep-4883.png` a Csillagozott néző-helyi menüjét és a
megerősítőt mutatja offscreen renderben.

## F. ⛳ Az Emberek-album helyi menüje a binárisból: VAN „Kiválasztás megfordítása”, mindig engedélyezett (2026-10-12, #4645)

*(A szakasz szándékosan az E. előtt áll: az E. táblázatát a
`tests/app/test_paritas_gyorsbillentyu_helyi_menuk_4462.py` a fejezetcímtől
a fájl végéig olvassa, így az utána álló táblák is beleszámítanának.)*

*Forrás: az építő `0x007359e0`–`0x00735c89` · a tételhozzáfűző `0x00a6aee0`
és az elválasztó-ág `0x00a6b120` · a közös rendezés-almenü `0x007318a0` · a
hívó `0x005e7650` · a belépési pont `0x005e7c20` · az utófeldolgozó
`0x0056c5a0` · a parancs-szétosztó `0x005cb990` · a kezelő `0x005e5370` · a
megfordító mag `0x00716600` · a menüsáv-előkészítő `0x0056e1c0` és
`0x005628c0`. Minta: a C.5-ben azonosított `Picasa3.exe` (3.9.141.259).*

**A kérdés (#4645):** a gyorsbillentyű-lap (`picasa-gyorsbillentyuk.md` 4.)
szerint a `0x007359e0` három billentyűs rekordot ír (Ctrl+A, Ctrl+D,
Ctrl+I), a `PplAlbum::` névtérben viszont nincs megfordító kulcs. Van-e
tehát „Kiválasztás megfordítása” a menüben, mit fordít meg, és mikor
engedélyezett?

### F.1 A rekordtábla — globális címeken, csúszás nélkül

Ez az építő a menüsáv-építőhöz hasonlóan **globális** rekordtömböt tölt
(`0xd6f9a8`-tól, lépésköz `0x14`), és a végén `0x00a6aee0(hMenu,
0xd6f9a8, 0x0a)`-val **tíz** rekordot ad át (`0x00735c69`–`0x00735c75`).
Mivel minden mező saját abszolút címre íródik, a B.5-ben leírt
„következő rekord blokkjában írja ki” csúszás itt nem téveszt: a mező
a címe alapján tartozik a rekordhoz. A rekord-alak a
`picasa-eger-es-kijeloles.md` 11.1-é (`+0x00` felirat, `+0x04`
gyorsbillentyű-betű, `+0x0a` parancs, `+0x0c` almenü-tábla, `+0x10`
almenü-darabszám).

| # | rekord | felirat-kulcs (cím) | EN alapértelmezés | HU (`stringres-en-hu.tsv`) | billentyű `+0x04` | parancs `+0x0a` |
|---:|---|---|---|---|---|---|
| 1 | `0xd6f9a8` | `PplAlbum::ID_ALBUM_EDITCAPTIONS` (`0xcaf334`) | &Edit People Album... | Az &Emberek album szerkesztése... | — | `0x9c69` (`0x00735a56`) |
| 2 | `0xd6f9bc` | **nincs** (`0x00735a5f`: `mov [0xd6f9bc], esi`, `esi = 0`) | — | — | — | elválasztó |
| 3 | `0xd6f9d0` | `PplAlbum::ID_ALBUM_SELECTALLPICTURES` (`0xcaf30c`) | Select &All | Az ö&sszes kijelölése | `"A"` (`0xc8c878`) | `0x9cb8` (`0x00735aaa`) |
| 4 | `0xd6f9e4` | `PplAlbum::ID_CLEAR_SELECTION` (`0xcaf2ec`) | &Clear Selection | &Kijelölés törlése | `"D"` (`0xc7eae0`) | `0x9c90` (`0x00735af8`) |
| 5 | `0xd6f9f8` | **`Album::ID_SELECT_INVERT`** (`0xcae188`) | &Invert Selection | **Kiválasztás &megfordítása** | **`"I"`** (`0xc8c818`) | **`0x9c47`** (`0x00735b5a`) |
| 6 | `0xd6fa0c` | **nincs** (`0x00735b63`) | — | — | — | elválasztó |
| 7 | `0xd6fa20` | `Album::ID_REFRESH_THUMB` (`0xcae414`) | &Refresh Thumbnails | Indexképek &frissítése | — | `0x9c5e` (`0x00735baa`) |
| 8 | `0xd6fa34` | `Album::SortAlbumBy` (`0xcae43c`) | Sort &Album By | &Album rendezésének alapja... | — | almenü: `+0x0c` = `0x007318a0` visszatérése (`0x00735bea`), `+0x10` = `4` (`0x00735c0f`) |
| 9 | `0xd6fa48` | **nincs** (`0x00735c19`) | — | — | — | elválasztó |
| 10 | `0xd6fa5c` | `PplAlbum::ID_ALBUM_DELETE` (`0xcaf2b8`) | &Delete People Album | Az Emberek &album törlése | — | `0x9d44` (`0x00735c4c`) |

Három rész-mérés zárja a táblát:

- **Az üres felirat elválasztó.** A `0x00a6aee0` a `[rekord+0] == 0`
  esetben (`0x00a6af04`–`0x00a6af20`) a `0x00a6b120`-at hívja `0xffff`
  azonosítóval, az pedig szöveg nélkül `fMask = 0x10`, `fType = 0x800`
  értéket ír (`0x00a6b140`–`0x00a6b148`) — ez a `MIIM_TYPE` +
  `MFT_SEPARATOR`.
- **A 8. rekord almenü.** Nem nulla `+0x0c` esetén a `0x00a6aee0` új
  felugró menüt kér (`[0xc408f0]`, `0x00a6af3c`), és önmagát hívja a
  `+0x0c` tömbre `+0x10` darabszámmal (`0x00a6af5c`). A `0x007318a0`
  a `0xd6ead8` tömböt adja vissza (`0x007319e2`), benne négy rekorddal:
  `Sort::ID_NAMESORT` `0x9cd3` · `Sort::ID_DATESORT` `0x9cd4` ·
  `Sort::ID_SIZESORT` `0x9cd5` · `Sort::ID_REVERSESORT` `0xa0d0`, ebben a
  sorrendben. Ugyanezt a függvényt hívja a mappa-menü (`0x00731cea`) és az
  album-menü (`0x00732338`) is — független `E8`-pásztázás, pontosan három
  hívó —, tehát ez **ugyanaz** a rendezés-almenü, mint az album
  „Album rendezésének alapja ▸” tétele.
- **A parancsazonosítók** egyeznek a `picasa-menu-parancsok.csv`
  soraival: `0x9cb8` = `ID_ALBUM_SELECTALLPICTURES`, `0x9c90` =
  `ID_CLEAR_SELECTION`, `0x9c47` = `ID_SELECT_INVERT`, `0x9d44` =
  `ID_ALBUM_DELETE`, `0x9c69` = `ID_ALBUM_EDITCAPTIONS`, `0x9cd3`/`0xa0d0` =
  `ID_NAMESORT`/`ID_REVERSESORT`.

⇒ **A menü hét tétele** (három elválasztóval): Az Emberek album
szerkesztése… · ― · Az összes kijelölése `Ctrl+A` · Kijelölés törlése
`Ctrl+D` · **Kiválasztás megfordítása `Ctrl+I`** · ― · Indexképek
frissítése · Album rendezésének alapja ▸ (Név · Dátum · Méret · Fordított
sorrend) · ― · Az Emberek album törlése.

A „Kiválasztás megfordítása” **nem saját `PplAlbum::` kulcs**, hanem az
`Album::ID_SELECT_INVERT` kölcsönzése — ezért nem látszott az A.2-es
névtér-leltárban. A felirat tehát az album-menüével azonos.

### F.2 Melyik menü ez — a hívó és a kontextus

A `0x007359e0`-t két hely hívja (független `E8`-pásztázás: `0x005d4366`
és `0x005e76f2`). A `0x005e7650`-ben az ág választása:

```
0x005e76d3  call 0x4461a0      ; hamis → 0x005e7731 call 0x7319f0  (mappa-menü)
0x005e76e5  call 0x448c90      ; hamis → 0x005e771e call 0x732160  (album-menü)
0x005e76f2  call 0x7359e0      ; igaz  → Emberek-album menü
```

A `0x00448c90` a személy-album kérdezője (`picasa-arcfelismeres.md` 9/e:
`0x0064d1ab call 0x448c90 ; nem személy-album`). Az építő a C.3 szerint a
`0x13c` kontextust írja (`0x00735c7a push 0x13c` → `0x00a6ae90`). A
három menü tehát ugyanabból a hívóból, az album fajtája szerint
választva épül.

### F.3 Mit fordít meg — a kezelő és a mag

A kiválasztott parancs a `0x005e77dc`–`0x005e7800` helyen `WM_COMMAND`-ként
(`0x111`) megy tovább, a nézet-objektum vtáblájának `+0x5c` rekeszén át.
Ez a rekesz a `0x005cb990`: a konstruktor `0x00564507`-nél a `0x00c9052c`
vtáblát írja az objektumba, és a `0x00c9052c + 0x5c = 0x00c90588` rekesz
tartalma a fájlban `0x005cb990` (a `0x005cb990` egyetlen abszolút
előfordulása a PE-ben). A rács parancs-szétosztója (`0x005cb990`,
`picasa-eger-es-kijeloles.md` 11.2) a `0x9c47 − 0x9c42 = 5` indexet a
`0x005cdb34` bájttérképen át az `1`-es ágra viszi, az ugrótábla
(`0x005cd9fc`) célja `0x005cbd03`: `push ebx · call 0x005e5370`.
*(Kontroll ugyanezzel az olvasóval: a `0x9cb8` → 118. bejegyzés → 39. ág
→ `0x005cbcec`, ahogy a 11.2 is írja.)*

A kezelő (`0x005e5370`):

```
0x005e5377  mov esi, [ebx + 0xeac]   ; ugyanaz a csomópont, mint a Ctrl+A / Ctrl+D kezelőjénél
0x005e5382  call 0x716600            ; megfordítás
0x005e53ad  call 0xa54b70            ; egyetlen teljes-felület érvénytelenítés
```

A mag (`0x00716600`) az `[esi+0x32c]` elemtömbön megy végig
(`[esi+0x330] >> 1` darab):

| az elem állapota | mit tesz | cím |
|---|---|---|
| kijelölt (`+0x5d ≠ 0`) | `+0x5d = 0`; a `+0x59` változásjelző csak ha `+0x5a == 0`; „volt levétel” jelző be | `0x00716631`–`0x00716644` |
| nem kijelölt | `+0x5d = 1`; a `+0x59` csak ha `+0x5a == 0`; a horgony `[esi+0x390]` = az elem `+0xb4` azonosítója | `0x00716648`–`0x00716668` |
| üres rekesz (`NULL`) | kihagyja | `0x00716626` |

Utána a megfigyelőket (`[esi+0x31c]`, `vt[1]`) **csak akkor** értesíti,
ha volt levétel (`0x0071667c test dl, dl`) — a hívó teljes-felület
érvénytelenítése ettől függetlenül lefut.

Három, ebből következő tény:

1. **A hatókör azonos az „Az összes kijelölése” tételével**: mindkét
   kezelő a `[CThumbUI+0xeac]` csomópont elemtömbjén dolgozik
   (`0x005e5070` → `0x00716f40`, `0x005e5370` → `0x00716600`), és mindkettő
   a `+0x5d` kijelölésbájtot írja. Ugyanabban a menüben a megfordítás tehát
   pontosan azt a halmazt fordítja meg, amit a Ctrl+A kijelöl — azaz az
   Emberek-album rácsban látható elemeit, nem külön arc- vagy
   személy-listát.
2. **Eltérés a Ctrl+A-tól:** a `0x00716f40` a `+0x5a` jelzős elemet
   **soha** nem jelöli ki (11.3), a `0x00716600` viszont a `+0x5a`-t csak
   a `+0x59` írásánál nézi, a `+0x5d`-t nem — vagyis megfordításkor az
   ilyen elem is kijelölt lesz. A `+0x5a` jelentése **örökölt nyitott
   kérdés** (`picasa-kollazs-felulet.md`, „a `+0x5a` jelentését NEM nevezem
   meg biztosnak”); a PicasaPy kijelölési modelljében nincs megfelelője, a
   megvalósítást nem érinti.
3. **A horgony az UTOLSÓ újonnan kijelölt elem** — a ciklus minden
   kijelöléskor felülírja a `[esi+0x390]`-t. (A Ctrl+A az elsőt teszi
   horgonnyá, 11.3.)

### F.4 Mikor engedélyezett — mindig

A menü megjelenítése előtt a `0x005e7c20` a `0x0056c5a0` utófeldolgozót
hívja (`0x005e7c99`), kontextusként a menü `dwMenuData`-jával (`0x13c`):

```
0x0056c5d0  call [0xc408c4]          ; tételszám
0x0056c5e0  push 0x400 / push esi / push hMenu
0x0056c5e9  call [0xc40818]          ; EnableMenuItem(hMenu, i, MF_BYPOSITION|MF_ENABLED) — MINDEN tétel
0x0056c5f6  cmp ebp, 0xa6 ; ja       ; 0x13c > 0xa6
0x0056c61a  cmp ebp, 0x127 / 0x13d / -1  ; egyik sem
0x0056c62d  jne 0x56e04a             ; → xor eax, eax ; ret — semmi további
```

A visszatérő `0` miatt a `0x005e7c20` nem lép ki (`0x005e7c9e cmp eax,
0xf4242`), és a menüt `TrackPopupMenu` (`[0xc407c4]`, `0x005e7cd7`) teszi
ki. A `0x13c` kontextusban tehát **minden tétel engedélyezve**, semmi nem
szürkül és semmi nem törlődik — a kijelölés állapotától függetlenül.

**A tiltó ág kizárása, indextől függetlenül:** a teljes `.text`
bájtpásztázása a `0x9c47` minden előfordulását megadja (32 és 16 bites
közvetlen érték): menüsáv-építő `0x00559bfa`, mappa-menü `0x00731bde`,
album-menü `0x007322a2`, Emberek-menü `0x00735b5b`, és **két szürkítő**
hely, mindkettő a `0x0056e1c0`-ban: `0x0056e781` (egy négyes
tételcsoport `EnableMenuItem`-je `MF_GRAYED`-del) és `0x0056ebea`
(`[edi+0x34a4] ≠ 0` esetén szürkít). A maradék két találat nem utasítás
része (`0x004b9af5` egy `call` eltolása, `0x00bd9cdb` egy `0x00bd9c47`
mutató). A `0x0056e1c0` azonban **nem a felugró menüt** szerkeszti: a
menüfogantyút a `0x005628c0`-tól kapja, ami
`GetSubMenu(GetMenu([0xd67850]), n)` — ugyanaz a `[0xc408dc]` /
`[0xc408cc]` importpár, amit a `picasa-menu-parancsok-viselkedes.md` a
`0x00574b81`–`0x00574b8a` helyen `GetMenu`/`GetSubMenu`-ként azonosít —,
vagyis a **menüsáv** Szerkesztés menüjét. A felugró menü fogantyúját maga
az építő kéri (`0x00735c63 call [0xc408f0]` = `CreatePopupMenu`), és az
csak a `0x005e7c20`-ba jut tovább, a `0x0056e1c0`-ba nem.

⇒ **Az Emberek-album helyi menüjének „Kiválasztás megfordítása” tétele
mindig engedélyezett.** (A menüsáv Szerkesztés ▸ Kiválasztás megfordítása
szürkítése külön kérdés, ez a szakasz nem dönti el.)

### F.5 Eredeti / nálunk / teendő

Mai `PeopleAlbumContextMenu.qml` (`origin/main`, 2026-10-12): Az Emberek
album törlése · Az Emberek album szerkesztése… · ― · Az összes kijelölése
· Kijelölés törlése — billentyűfelirat nélkül.

| eltérés | eredeti | nálunk |
|---|---|---|
| **Kiválasztás megfordítása** | megvan, `Ctrl+I`, mindig engedélyezett, a Ctrl+A hatókörén | **hiányzik** |
| Indexképek frissítése | megvan (`0x9c5e`) | hiányzik |
| Album rendezésének alapja ▸ | megvan, a közös négytételes almenü | hiányzik |
| billentyűfeliratok | `Ctrl+A`, `Ctrl+D`, `Ctrl+I` | nincs |
| sorrend | szerkesztés első, törlés utolsó, három elválasztó | törlés első, egy elválasztó |

A PicasaPy oldalon a hatókör már adott: a `Main.qml` `invertSelection()`
és `selectAll()` ugyanazt a `_groupRows()` halmazt használja, tehát a
megfordítás bekötése ugyanaz, mint az album-menüé (`FolderPane.qml`,
`onInvertSelectionRequested`).

**A megvalósítandó eltérés — „Kész, ha”** (fejlesztési jegy tárgya):

- [ ] Az Emberek-album helyi menüjében a tételsor az F.1 szerinti: Az
      Emberek album szerkesztése… · ― · Az összes kijelölése · Kijelölés
      törlése · Kiválasztás megfordítása · ― · Indexképek frissítése ·
      Album rendezésének alapja ▸ · ― · Az Emberek album törlése.
- [ ] A három kijelölő tétel mellett a billentyűfelirat `Ctrl+A`,
      `Ctrl+D`, `Ctrl+I` (a `FolderContextMenu.qml` mintájára).
- [ ] A „Kiválasztás megfordítása” mindig engedélyezett, és ugyanazt a
      halmazt fordítja meg, amit ugyanebben a menüben az „Az összes
      kijelölése” kijelöl — valódi kattintásos QML-próba bizonyítja egy
      részleges kijelölésen (előtte/utána kijelölt sorok).
- [ ] Az „Indexképek frissítése” és az „Album rendezésének alapja ▸” vagy
      működik az album-menü megfelelőjével azonos módon, vagy — ha ott sincs
      mögötte réteg (E. táblázat: `Album::SortAlbumBy` **hiányzik**) — a
      jegy kimondja, és a tétel ugyanúgy viselkedik, mint az album-menüben.
- [ ] Az E. táblázat `PplAlbum` sorai kiegészülnek a három új tétellel, és
      a `test_paritas_gyorsbillentyu_helyi_menuk_4462.py` várt darabszáma
      `PplAlbum: 7`-re nő; az A.2-re hivatkozó
      `tests/app/test_stage4_context_menus_422.py` tételsora is az F.1-et
      követi.

### F.6 Nyitott kérdések mérlege

- van-e „Kiválasztás megfordítása”, mi a billentyűje — **LEZÁRVA** (F.1:
  van, `Ctrl+I`, `0x9c47`, kölcsönzött `Album::` kulcs);
- mit fordít meg — **LEZÁRVA** (F.3: a Ctrl+A-val azonos csomópont
  elemtömbjét);
- engedélyezett-e mindig — **LEZÁRVA** (F.4);
- a teljes tételsor és sorrend — **LEZÁRVA** (F.1);
- a `+0x5a` jelző jelentése — **örökölt**, nem e kör kérdése
  (`picasa-kollazs-felulet.md`).

`0 nyílt · 4 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

## E. #4462 — helyi menük: eredeti tétel → mai kód

A táblázat a fenti specifikáció eredeti feliratait és menüosztályait tekinti mércének. A rejtett/állapotfüggő tételeket külön sorban tartja, akkor is, ha a felületen ugyanazt a sort használják. Az album osztály eredeti 13 parancsazonosítója 12 különböző feliratot ad; a két feltöltési felirat több azonosítón osztozik, ezért a táblázat látható tételeket sorol.

Az Indexkép §2 összesítője 19 tételt mond, a részletes D.1 rekordlista 21 sort sorol (benne az Elrejtés/Megjelenítés állapotpárral és az online műveletek almenüjével). Az E. táblázat a részletes D.1-et követi, és a feltételes kereső almenü két gyermekét külön számolja.

| kontextus | eredeti tétel / forrás | eredeti művelet | nálunk: QML-azonosító | állapot | bizonyíték / hiány oka |
|---|---|---|---|---|---|
| AlbumList | AlbumList::SortAlbumByDate | Rendezés dátum szerint | objectName=folderListMenuSortByDate | **megvan és működik** | tests/app/test_stage3_context_menus_422.py |
| AlbumList | AlbumList::SortAlbumByName | Rendezés név szerint | objectName=folderListMenuSortByName | **megvan és működik** | tests/app/test_stage3_context_menus_422.py |
| AlbumList | AlbumList::SortAlbumBySize | Rendezés méret szerint | objectName=folderListMenuSortBySize | **megvan és működik** | tests/app/test_stage3_context_menus_422.py |
| AlbumList | AlbumList::SortAlbumByChanged | Rendezés legutóbbi változás szerint | objectName=folderListMenuSortByChanged | **megvan és működik** | tests/app/test_stage3_context_menus_422.py |
| AlbumList | AlbumList::SortReverse | Fordított rendezés | objectName=folderListMenuSortReverse | **megvan és működik** | tests/app/test_stage3_context_menus_422.py |
| AlbumList | AlbumList::SortPeopleByName | Emberek rendezése név szerint | objectName=folderListMenuSortPeopleByName | **megvan és működik** | tests/app/test_stage3_context_menus_422.py |
| AlbumList | AlbumList::SortPeopleByAmount | Emberek rendezése mennyiség szerint | objectName=folderListMenuSortPeopleByCount | **megvan és működik** | tests/app/test_stage3_context_menus_422.py |
| AlbumList | AlbumList::SortPeopleByTop10 | Emberek rendezése Top 10 szerint | objectName=folderListMenuSortPeopleByTopList | **megvan és működik** | tests/app/test_stage3_context_menus_422.py |
| AlbumList | AlbumList::SimplifiedTreeView | Egyszerűsített fanézet | objectName=folderListMenuSimplifiedTree | **megvan és működik** | tests/app/qml_functional/test_mappalista_paritas_4462.py |
| AlbumList | AlbumList::ShowThumbnailsInLibrary | Indexképek megjelenítése a könyvtárban | objectName=folderListMenuShowThumbnails | **megvan és működik** | tests/app/qml_functional/test_mappalista_paritas_4462.py |
| AlbumList | AlbumList::Shortcuts | Gyors gyökérváltók almenüje | objectName=folderListMenuShortcuts | **megvan és működik** | tests/app/qml_functional/test_mappalista_paritas_4462.py |
| AlbumList | AlbumList::Desktop | Asztal gyökér kiválasztása | objectName=folderListMenuDesktop | **megvan és működik** | tests/app/qml_functional/test_mappalista_paritas_4462.py |
| AlbumList | AlbumListWin::MyComputer | Sajátgép gyökér | Nincs, a Windows-tétel kimarad | **nem cél — Windows-only** | A.2 és A.4 szerint Windows-specifikus |
| AlbumList | AlbumListWin::Documents | Dokumentumok gyökér | Nincs, a Windows-tétel kimarad | **nem cél — Windows-only** | A.2 és A.4 szerint Windows-specifikus |
| AlbumList | AlbumListWin::Pictures | Képek gyökér | Nincs, a Windows-tétel kimarad | **nem cél — Windows-only** | A.2 és A.4 szerint Windows-specifikus |
| Indexkép | AlbumPhoto::ID_PICTURE_VIEW | Megjelenítés és szerkesztés | objectName=contextMenuOpen | **megvan és működik** | tests/app/qml_functional/test_enter_megnyit_1417.py |
| Indexkép | AlbumPhoto::ID_LABELS | Hozzáadás az albumhoz almenü | objectName=contextMenuAddToAlbum | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | OneUp::ID_PICTURE_ROTATECLOCKWISE | Forgatás jobbra | objectName=contextMenuRotateRight | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | AlbumPhoto::ID_PICTURE_ROTATECOUNTERCLOCKWISE | Forgatás balra | objectName=contextMenuRotateLeft | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | FolderPhoto::ID_PICTURE_REVERT | Összes szerkesztés visszavonása | objectName=contextMenuUndoAllEdits | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | AlbumPhoto::ID_PICTURE_HIDE | Elrejtés állapotfüggő sor | objectName=contextMenuHide | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | AlbumPhoto::ID_PICTURE_UNHIDE | Megjelenítés állapotfüggő sor | objectName=contextMenuHide | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | FolderPhoto::ID_ALBUM_NEW | Áthelyezés új mappába | objectName=contextMenuMove | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | FolderPhoto::ID_PICTURE_SPLITALBUMHERE | Mappa felosztása itt | objectName=contextMenuSplitFolder | **hiányzik — javasolt jegycím: A kijelölt képnél lehessen új mappára bontani a mappát** | A parancs jelenleg letiltott helyfoglaló; nincs megfelelő vezérlőművelet |
| Indexkép | OneUp::ID_FILE_OPENINANEDITOR | Fájl megnyitása | objectName=contextMenuOpenFile | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | AlbumPhoto::ID_FILEOPENWITH | Társítás almenü | objectName=contextMenuOpenWith | **hiányzik — javasolt jegycím: A kép helyi menüje listázza a társított alkalmazásokat** | A rendszer alapértelmezett megnyitása létezik, de az alkalmazáslista nem |
| Indexkép | AlbumPhoto::ID_FILE_SAVE | Szerkesztés mentése | objectName=contextMenuSave | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | AlbumPhoto::ID_FILE_REVERT | Visszaállítás | objectName=contextMenuRevert | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | FolderPhotoWin::ID_FILE_LOCATEONDISK | Keresés a lemezen; eredeti állapotban lapos sor, egy visszaállítható képnél feltételes almenü | objectName=contextMenuLocate vagy objectName=contextMenuLocateMenuTetel | **megvan és működik** | tests/app/test_kereses_almenu_1613.py |
| Indexkép | CThumbUI::locateondiskmenu | A feltételes almenü Fájl a lemezen tétele | objectName=contextMenuLocateFile | **megvan és működik** | tests/app/test_kereses_almenu_1613.py |
| Indexkép | CThumbUI::locateorigondiskmenu_win | A feltételes almenü Eredeti a lemezen tétele | objectName=contextMenuLocateOriginal | **megvan és működik** | tests/app/test_kereses_almenu_1613.py |
| Indexkép | FolderPhoto::ID_FILE_DELETEFROMDISK | Törlés a lemezről; album-nézetben eltávolítás az albumból | objectName=contextMenuDelete vagy objectName=contextMenuRemoveFromAlbum | **megvan és működik** | tests/app/qml_functional/test_torles_billentyu_felulet_1418.py |
| Indexkép | AlbumPhoto::ID_COPY_PATH | Teljes elérési út másolása | objectName=contextMenuCopyFullPath | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | Album::ID_UPLOAD_TO_LIGHTHOUSE | Feltöltés a Picasa Webalbumokba | objectName=contextMenuUploadToWebAlbums | **nem cél — megszűnt online szolgáltatás** | A jegy kifejezetten kizárja a Picasa Web Albums szolgáltatást |
| Indexkép | Album::ID_ONLINE_ACTIONS | Online műveletek almenü | Nincs, a szolgáltatások megszűntek | **nem cél — megszűnt online szolgáltatás** | A részletes D.1 ezt az online műveleti csoportot sorolja |
| Indexkép | AlbumPhoto::ID_SUPPRESS | Feltöltés tiltása | objectName=contextMenuBlockUpload | **nem cél — megszűnt online szolgáltatás** | A jegy kifejezetten kizárja az online szolgáltatásokat |
| Indexkép | AlbumPhoto::ID_PICTURE_RESET_FACES | Arcok alaphelyzetbe állítása | objectName=contextMenuResetFaces | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Indexkép | AlbumPhotoWin::ID_PICTURE_PROPERTIES | Tulajdonságok | objectName=contextMenuProperties | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| Album | Album::ID_DELETEALBUM | Album törlése | objectName=albumMenuDelete | **megvan és működik** | megerősítés utáni törlés minden érintett mappa ini-jéből; `tests/app/qml_functional/test_album_torles_menu_4598.py` |
| Album | Album::ID_EDITALBUMDESCRIPTION | Album leírásának szerkesztése | objectName=albumMenuEditDescription | **megvan és működik** | tests/app/test_stage4_context_menus_422.py |
| Album | Album::ID_ALBUM_FILTERFACES | Névcímkék hozzáadása | objectName=albumMenuAddNameTags | **megvan és működik** (#4535) | tests/app/qml_functional/test_nevcimke_kereses_4535.py |
| Album | Album::ID_SELECTALL | Összes kép kijelölése | objectName=albumMenuSelectAll | **megvan és működik** | tests/app/test_stage4_context_menus_422.py |
| Album | Album::ID_CLEARSELECTION | Kijelölés törlése | objectName=albumMenuClearSelection | **megvan és működik** | tests/app/test_stage4_context_menus_422.py |
| Album | Album::ID_INVERTSELECTION | Kiválasztás megfordítása | objectName=albumMenuInvertSelection | **megvan és működik** | tests/app/test_stage4_context_menus_422.py |
| Album | Album::ID_REFRESHTHUMBNAILS | Indexképek frissítése | objectName=albumMenuRefreshThumbnails | **megvan és működik** | tests/app/test_stage4_context_menus_422.py |
| Album | Album::SortAlbumBy | Album rendezésének alapja almenü | objectName=albumMenuSortAlbumBy | **hiányzik — javasolt jegycím: Az album saját rendezése változtassa meg az album képeinek sorrendjét** | A mappaképek rendezője nem azonos az album rendezőjével |
| Album | Album::ID_ONLINE_ACTIONS | Online műveletek | objectName=albumMenuOnlineActions | **nem cél — megszűnt online szolgáltatás** | A jegy kifejezetten kizárja az online szolgáltatásokat |
| Album | Album::ID_UPLOAD_TO_GOOGLE_PLUS_PHOTOS | Feltöltés a Google Fotókba | objectName=albumMenuUploadToGooglePhotos | **nem cél — megszűnt online szolgáltatás** | A jegy kifejezetten kizárja a Google+ és Picasa online szolgáltatásokat |
| Album | Album::ID_UPLOAD_TO_LIGHTHOUSE | Feltöltés a Picasa Webalbumokba | objectName=albumMenuUploadToWebAlbums | **nem cél — megszűnt online szolgáltatás** | A jegy kifejezetten kizárja a Picasa Web Albums szolgáltatást |
| Album | Album::ID_EXPORTASHTML | Exportálás HTML-oldalként | objectName=albumMenuExportAsHtml | **megvan és működik** | tests/app/test_stage4_context_menus_422.py |
| OneUp | OneUp::ID_VIEWALBUM | Visszatérés a könyvtárhoz | objectName=viewerMenuBackToLibrary | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | AlbumPhoto::ID_LABELS | Hozzáadás az albumhoz almenü | objectName=viewerMenuAddToAlbum | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | OneUp::ID_PICTURE_ROTATECLOCKWISE | Forgatás jobbra | objectName=viewerMenuRotateRight | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | AlbumPhoto::ID_PICTURE_ROTATECOUNTERCLOCKWISE | Forgatás balra | objectName=viewerMenuRotateLeft | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | FolderPhoto::ID_PICTURE_REVERT | Összes szerkesztés visszavonása | objectName=viewerMenuUndoAllEdits | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | AlbumPhoto::ID_PICTURE_HIDE / ID_PICTURE_UNHIDE | Elrejtés vagy megjelenítés | objectName=viewerMenuHide | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | OneUp::ID_FILE_OPENINANEDITOR | Fájl megnyitása | objectName=viewerMenuOpenFile | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | AlbumPhoto::ID_FILEOPENWITH | Társítás almenü | objectName=viewerMenuOpenWith | **hiányzik — javasolt jegycím: A kép helyi menüje listázza a társított alkalmazásokat** | A rendszer alapértelmezett megnyitása létezik, de az alkalmazáslista nem |
| OneUp | AlbumPhoto::ID_FILE_SAVE | Szerkesztés mentése | objectName=viewerMenuSave | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | AlbumPhoto::ID_FILE_REVERT | Visszaállítás | objectName=viewerMenuRevert | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | FolderPhotoWin::ID_FILE_LOCATEONDISK | Keresés a lemezen; eredeti állapotban lapos, visszaállítható képnél almenü | objectName=viewerMenuLocate vagy objectName=viewerMenuLocateMenuItem | **megvan és működik** | tests/app/qml_functional/test_viewer_original_locate_4462.py |
| OneUp | CThumbUI::locateondiskmenu | A feltételes almenü Fájl a lemezen tétele | objectName=viewerMenuLocateFile | **megvan és működik** | tests/app/qml_functional/test_viewer_original_locate_4462.py |
| OneUp | CThumbUI::locateorigondiskmenu_win | A feltételes almenü Eredeti a lemezen tétele | objectName=viewerMenuLocateOriginal | **megvan és működik** | tests/app/qml_functional/test_viewer_original_locate_4462.py |
| OneUp | FolderPhoto::ID_FILE_DELETEFROMDISK | Törlés a lemezről | objectName=viewerMenuDelete | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | AlbumPhoto::ID_COPY_PATH | Teljes elérési út másolása | objectName=viewerMenuCopyFullPath | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | OneUp::QuickUpload | Gyors feltöltés | objectName=viewerMenuQuickUpload | **nem cél — megszűnt online szolgáltatás** | A jegy kifejezetten kizárja az online szolgáltatásokat |
| OneUp | AlbumPhoto::ID_SUPPRESS | Feltöltés tiltása | objectName=viewerMenuBlockUpload | **nem cél — megszűnt online szolgáltatás** | A jegy kifejezetten kizárja az online szolgáltatásokat |
| OneUp | AlbumPhoto::ID_PICTURE_RESET_FACES | Arcok alaphelyzetbe állítása | objectName=viewerMenuResetFaces | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| OneUp | AlbumPhotoWin::ID_PICTURE_PROPERTIES | Tulajdonságok | objectName=viewerMenuProperties | **megvan és működik** | tests/app/qml_functional/test_viewer_context_menu.py |
| PplAlbum | PplAlbum::ID_DELETEALBUM | Emberek-album törlése | objectName=peopleAlbumMenuDelete | **megvan és működik** | Megerősítés és tényleges törlés: tests/app/qml_functional/test_people_album_context_menu_4587.py |
| PplAlbum | PplAlbum::ID_EDITALBUM | Emberek-album szerkesztése | objectName=peopleAlbumMenuEdit | **megvan és működik** | A People Manager a kattintott személyt jelöli ki: tests/app/qml_functional/test_people_album_context_menu_4587.py |
| PplAlbum | PplAlbum::ID_SELECTALL | Összes kijelölése | objectName=peopleAlbumMenuSelectAll | **megvan és működik** | tests/app/test_stage4_context_menus_422.py |
| PplAlbum | PplAlbum::ID_CLEARSELECTION | Kijelölés törlése | objectName=peopleAlbumMenuClearSelection | **megvan és működik** | tests/app/test_stage4_context_menus_422.py |
| PplAlbum | Album::ID_SELECT_INVERT | Kiválasztás megfordítása | objectName=peopleAlbumMenuInvertSelection | **megvan és működik** | tests/app/qml_functional/test_people_album_menu_4645.py |
| PplAlbum | Album::ID_REFRESH_THUMB | Indexképek frissítése | objectName=peopleAlbumMenuRefreshThumbnails | **megvan és működik** | tests/app/qml_functional/test_people_album_menu_4645.py |
| PplAlbum | Album::SortAlbumBy | Album rendezésének alapja almenü | — | **hiányzik — a #4599 után kötjük be** | A #4599 része; ebben a körben a tétel kimarad |
| PplAlbumPhoto | PplAlbumPhoto::ID_DELETEFROMPEOPLEALBUM | Eltávolítás az Emberek albumból | objectName=contextMenuRemoveFromPeopleAlbum | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| PplAlbumPhoto | PplAlbumPhoto::ID_PEOPLEALBUMS | Hozzáadás egy meglévő Emberek-albumhoz | objectName=contextMenuAddToPeopleAlbum | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| PplAlbumPhoto | PplAlbumPhoto::ID_MOVETONEWPERSON | Áthelyezés új személyhez | objectName=contextMenuMoveToNewPerson | **megvan és működik** | tests/app/qml_functional/test_photo_menu_commands.py |
| PplAlbumPhoto | PplAlbumPhoto::ID_SETASPEOPLEALBUMTHUMBNAIL | Beállítás az Emberek album indexképeként | objectName=contextMenuSetAsPeopleAlbumThumbnail | **a sor jelen van, de letiltott helyőrző** | PicasaPy-ban nincs tartós személy–fotó választás |

Az állapotok ismételhető ellenőrzése a tests/app/test_paritas_gyorsbillentyu_helyi_menuk_4462.py fájlban fut. A két új valódi kattintásos QML-próba az AlbumList bélyegkép-kapcsolóját és Asztal almenüjét, valamint a OneUp „Eredeti a lemezen” útját ellenőrzi.

## 1022. tétel részletezése — személy-album indexképe (#4536)

Állapot: 2026-10-12, a `research/4536-szemely-indexkep` ágon mért. Csak
kutatás, kód nem változott. A mai kódban a menüsor jelen van, de letiltott
helyőrző; a funkció hiányzik.

### Mai kód (mért)

- `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:248–251` — a helyőrző
  indoklása: személyenkénti indexkép-tároló nincs.
- `PhotoContextMenu.qml:253–267` — `contextMenuSetAsPeopleAlbumThumbnail`,
  `placeholder: true` (267), látható csak `personName !== ""` mellett (265).
  A `PicasaPy/PicasaMenuItem.qml:19,67` miatt szürke és nem kattintható.
- A QML-ben más „Set as … Thumbnail" tétel nincs (grep: `Set as`). A jegy
  törzsének „Arcfelismerés-rész: Set as Thumbnail megvan" állítása a kódban
  nem igazolódik.
- `src/picasapy/app`, `src/picasapy/index`, `src/picasapy/ini`: nincs
  személyenkénti indexkép-író vagy -olvasó. `people_controller.py` nem hívja
  a `set_thumbnail`-t. Az `ini/person_album_thumbnail.py` csak a
  `fix/4536-codex` ágon (`b74647c22`) van meg, `main`-en nincs.

### Eredeti: bináris-index (helyi, `referencia/binary-index/`)

Forrás: Picasa 3.9.141.259, SHA-256 `644b7bec…` (`meta.json`); Ghidra 12.1.2.

- A `set_thumbnail` string `0x00c96fc8`; hivatkozó függvények: `0x005e0f70`
  (leveles elosztó), `0x0074ad40` (panel-építő), `0x0074bcc0` (panel-építő).
- A kezelő: `0x00603660` (342 b). A `xrefs.csv` szerint a `0x005e0f70` és a
  `0x005cb990` is hívja.
- A kezelő közvetlen hívásai: `0x00603420` (Preferences /
  `PeopleAlbumUseFaceSrc`), `0x0074c110` (`albumheader/%x/%d/faceicon`),
  `0x007166c0`, `0x004af790`, `0x00407610`, `0x004115c0`, `0x0097caf0`,
  `0x009a8a30`, `0x009a8bc0`, `0x009d2c80`.
- A közvetlen hívások között nincs string-alapú íróhívás. Ez NEM negatív lelet:
  az xref-index nem látja a vtábla-hívásokat (ld. a kutatási módszertant).
- `PeopleAlbumUseFaceSrc` nyolc függvényben szerepel (`0x005704d0`,
  `0x0057a4f0`, `0x005c7830`, `0x005cb1a0`, `0x005e5290` face_zoom/picture_zoom,
  `0x005e8a70`, `0x00603420`, `0x00787d70`). Ez globális beállítás, nem
  személyenkénti tároló.
- **Spec-gyanú (nem mért ellentmondás):** a 23. (`create_face_movie`) és a 24.
  (`set_thumbnail`) sor ugyanazt a címet (`0x00603660`) adja. A kezelő
  hívásai között nincs filmkészítő, a `create_movie` (`0x0057cb60`) másik
  kezelő. Vagy a kezelő belül ágazik, vagy a 23. sor téves. Ellenőrizendő.

### Tárolási jelöltek — állapot

| jelölt | bizonyíték | állapot |
|---|---|---|
| `.picasa.ini` arc-sor / `[Contacts2]` | `picasa-arcfelismeres.md` 3.x: a `faces=` és a `[Contacts2]` névcímkéé | NYITOTT — a kezelőnek nincs mért ini-írása |
| `contacts.xml` | `picasa-arcfelismeres.md` 3.5: `id`, `name`, `modified_time`, `local_contact` | NEM VALÓSZÍNŰ — a mért alakban nincs képmező |
| db3 `albumdata` | mért oszlopok: name, date, category, filename, token, inisync, hascollage, albumpeoplechecksum, albumcontactids, unread | NYITOTT — nincs mért borító-oszlop |
| db3 `imagedata` (`personalbumid`) | `picasa-arcfelismeres.md` 3.4/b: albumsor-index | NYITOTT — nincs mért borító-jelző |
| registry `Preferences\PeopleAlbumUseFaceSrc` | nyolc kezelő, globális | NEM valószínű személyenkénti tárolóként; az írása nincs mérve |
| `albums_0.db` (indexkép-gyorsítótár) | `pmp-database.md`: gyorsítótár, nem választás | KIZÁRVA mint választás tárolója |

### Nyitott kérdés (a megvalósítás előtt)

Mit ír a `0x00603660`, és hová (db3-mező, ini-kulcs vagy registry)?

Megszerzés útja:
1. Célzott utasításszintű olvasat és natív futtatás a `picasa-x86-research`
   skillel (a bináris helyben elérhető a kutatói munkakönyvtárban). A kérdés:
   a `0x00603660` és a `0x00603420` vtábla-hívásainak célja és írói.
2. Futásidejű mérés (a bot 2026-10-09-i kommentje javasolja): személy-albumban
   indexképet váltani, előtte–utána diff a `.picasa.ini`-re, a `contacts.xml`-re
   és a db3-ra.

Addig nem írunk új ini-szakaszt (a `[PicasaPy]` kiterjesztés csak bizonyított
eredeti hely esetén jöhet szóba).

### Kész, ha (a tárolási döntés után)

- [ ] `PhotoContextMenu.qml:253–267`: a `placeholder: true` megszűnik; a tétel
      a személy-fotó menüjében aktív. Az `objectName` marad.
- [ ] A kattintás jelzést küld (pl. `setPeopleAlbumThumbnailRequested`),
      `people_controller.py`-ban bekötve; az író a felderített helyre ír.
- [ ] Visszaolvasás: a személy-album fejléce és a People Manager a mentett
      indexképet mutatja, újraindítás után is.
- [ ] Teszt: `tests/app/qml_functional/test_photo_menu_commands.py` (1019–1021.
      sor objectName-listája), `test_emberek_almenu_3464.py`, plusz a tároló-
      és a visszaolvasás-teszt, és egy kattintásos QML-próba.
- [ ] A menüszöveg nem változik; ha változna, a `picasapy_hu.ts` forró fájl
      (szerializálás).

### 2. kör (2026-10-12): utasításszintű olvasat — a tárolás helye NINCS bizonyítva

Módszer: capstone-os szétszedés a PE-ből (`pefile`+`capstone`, külön venv a
`/tmp/claude-1000/kd-r4536/` alatt); a vtábla-hívásokat a szétszedésből
olvastam ki, nem az xref-indexből. Natív QEMU-futtatás NEM történt (ld. lent).

#### Dispatch (mért)

- `0x005e0f70` — parancsnév-szerinti elosztó (`repe cmpsb`).
- `set_thumbnail` (`0x00c96fc8`, 14 bájt): egyezés a `0x005e1806–0x005e1836`
  blokkban, majd `call 0x603660` a `0x005e183d`-on. A hívás argumentuma a
  dispatcher `[esp+0x14]`-e (a `this`-objektum).
- **Eltérés a táblától (ld. a 1022. tétel 23. sorát):** `create_face_movie`
  (`0x00c96fb4`, 18 bájt) egyezése a `0x005e17c5–0x005e17fa` blokkban van, és
  az ág `push 0x9d59` → `0x005e11da`-ra megy, **nem** a `0x603660`-ra. Az xref-
  index a `create_face_movie` sztringet a `0x005e0f70` és a `0x0074bcc0` alól
  listázza, de a 23. sor címe (`0x00603660`) a kódban nem igazolódik. A sort a
  tulajdonos dönti el; ebben a körben nem javítottam a táblát.

#### `0x00603660` (set_thumbnail kezelő, mért)

- `stdcall`, egy stack-argumentum (`ret 4`), ez a `this` (`ebp`).
- **Ebben a függvényben nincs vtábla-hívás** (`call reg`/`call [reg+…]`): minden
  hívása közvetlen. A vtábla-hívások a `0x603420`-ban vannak (lent).
- Mezők: `[this+0xeac]` (alobjektum; a `+0x3c4` bájtja a feltétel, a `+0x3c0`
  dword a `0x4115c0`-nak átadott tárkulcs-érték), `[this+0x2bc]` (alobjektum, `+0x2428`,
  `+0xf8`, `+0x4c`), `[this+0xea0]`, `[this+0x2c0]`, `[this+0xeb0]` (X).
- Sikeres ág (`0x60372d` és azután): `0x4115c0` → `0x74c110` →
  `0x9d2c80`.
  - `0x4115c0`: pixelpuffer-foglaló, `w·h·4+8` bájt (`[esi+8]·[esi+0xc]`,
    `0x97c5d0` a foglaló).
  - `0x74c110`: a `albumheader/%x/%d/faceicon` kulcsot formázza
    (`0xcb1218`), és ezután kép-előállító/-lekérő kódot futtat (többek közt
    `call edx`, `call eax`). **Ez a kulcs gyorsítótár-kulcs, nem mentési
    hely**: a függvény a kép elkészítésére és lekérésére szolgál. A tárolási
    végpontja nincs mérve.
  - `0x9d2c80` (X): `X[+0x294][idx·8+4] |= 1`, `X+0x291 = 1`, `X+8 |= 2`; ha az argumentum
    alsó bájtja nem nulla, `|= 0x1000` is. **Az argumentum forrása nem egyértelmű**
    (a `[ebp+0xeac]` mutatóját látszik átadni, ez valószínűleg nem szándékolt);
    ezt a jelzést ne vegyük függőségnek, amíg nincs újraolvasva.

#### `0x00603420` (a Preferences-olvasó; mért)

- `stdcall`, `ret 8`; a kapcsoló neve: `Preferences` (`0xc7eafc`) +
  `PeopleAlbumUseFaceSrc` (`0xc8f570`), a `0x407a20` hívással.
- **Vtábla-hívások (ezek a kérdésben szereplő „vtábla-hívások”):**
  - `0x6034d3`: `call edx`, a cél `[[this+0x2bc]+0x4c]` vtábla `+8` slotja;
    argumentumok: a `fistp qword` érték (a `0xd35808` float-konstansból),
    `esi` (kimeneti objektum), `edi`.
  - `0x6034ed`: `call edx`, ugyanazon objektum `+0` slotja (akkor, ha a kimenet
    `[esi+8] == 0`).
  - A visszatérési érték: `0` ha `[esi+8] ≠ 0`, különben `9`.
- Az objektum osztálya és a slotok célja **nincs igazolva** (nincs RTTI-
  megfeleltetés; a `[this+0x2bc]+0x4c` objektum konstruktorát nem követtem).
- A kapcsoló a `0x603420`-ban olvasásnak látszik (`0x4019b0` után `sete bl`);
  írása a `0x603660`-ból nincs, és az írási irány a `0x407a20`-on belül sem
  igazolt.

#### Tárolási jelöltek — az eredmény

| jelölt | mit mutat a kód | állapot |
|---|---|---|
| `albumheader/%x/%d/faceicon` | a `0x74c110` kulcsa; kép-előállító/lekérő függvény | **gyorsítótár-kulcs**; a mentési végpontja nincs mérve |
| X (`[this+0xeb0]`) rekordtömbje (`+0x294`, 8 bájt/rekord, `+0x291` jelző) | `0x9d2c80` rekordbitet állít; a `0x9d1555` elrendezéskor törli a `+0x291` jelzőt | `+0x291` **elrendezési jelző**, nem mentési ciklus; a rekordbit jelentése nyitott |
| `Preferences\PeopleAlbumUseFaceSrc` | csak olvasás látszik a `0x603420`-ban | **nem** a választott kép tárolója |
| `albums.db` (`Picasa2/db3/albums_0.db` + `albums_index.db`) | a `0x603660` → `0x4115c0` a `+0x2428` tárba ír, a fejlécépítő és a Személyek-panel ugyanonnan olvas | **lemez-cache bizonyított; a beállító és olvasó kulcsának azonossága nyitott** |
| `.picasa.ini`, `contacts.xml`, db3 `imagedata`/`albumdata` | a választott fotó személyhez rendelését ezen mezőkbe nem igazoltam | NYITOTT — az `albums.db` kulcskapcsolatát kell eldönteni; nincs becslés |

X-osztály: a `0x9d1xxx`–`0x9d2cxx` tartomány azonos mezőkiosztást használ
(`+0x284`, `+0x288`, `+0x290/0x291`, `+0x294/0x298`, `+0x2ac`, `+0x328`,
`+0x350/0x358`). Az azonos offset még nem azonos osztály; RTTI-vel nincs
igazolva. A 2. körben „mentési ciklusnak” nevezett hívottak (`0x9a5210`,
`0x40a050`, `0x9e5e70`, `0x9e5e20`, `0x9e02a0`, `0x9d1130`) nem bizonyítják a
rekordtábla fájlba mentését; a 3. kör a `0x9d1555`-öt elrendezési jelzőként
cáfolta.

#### Nyitott kérdés (a tárolási döntés előtt)

Ugyanaz-e a `0x603660` által a `0x4115c0`-nak átadott `[this+0xeac]+0x3c0`
kulcs és a `faceheaderpanel` `0x4114e0`-olvasójának `[header+0x2a0]` kulcsa;
így a kiválasztott fotó újraindítás után is a személy-album indexképe-e?

Megszerzés útja (sorrendben):
1. Ghidra-körben a `0x603660` és `0x74ad40` mezőinek/argumentumainak
   szemantikai azonosítása: a beállító- és visszaolvasó-kulcs összekötése.
2. Eredeti Picasa-profilon indexkép-beállítás előtti/utáni diff az
   `albums_0.db` és `albums_index.db` fájlokon, majd Picasa-újraindítás utáni
   képellenőrzés. Az ehhez szükséges próbaadat ebben a körben NINCS MEG.

Addig nincs „Kész, ha” lista a tárolási döntés alapján: a fenti 1022. tétel
„Kész, ha” listája a tárolási hely bizonyítása után érvényes.

### 3. kör (2026-10-12): a `0x9d1555` NEM mentési ciklus — tárolási hely még nincs bizonyítva

Módszer: a bináris SHA-256 egyezik a 2. körrel (`644b7bec…`). Capstone-os
szétszedés és címzett pásztázás a `.text`-en; a hívási gráf a közvetlen
`call`-okból épül. Natív QEMU-futtatás NEM történt (ld. lent, miért). A
szkriptek: `/tmp/claude-1000/kd-r4536/t/` (takarítandó a kör végén).

⚠️ **Módszertani buktató (mért):** a capstone `disasm` generátora az első
érvénytelen bájtnál **csendben megáll**. A naiv `.text`-pásztázás a 31 helyett
4 találatot adott. A pásztázónak át kell lépnie az érvénytelen bájtot.

#### A premissza: a `0x9d1555` nem mentés

- A `0x9d1555` (`mov byte ptr [esi+0x291], 0`) a `0x9d1150` függvényben van
  (törzs: `0x9d1150`–`0x9d1691`, `ret` a `0x9d1691`-en). Ez **képernyő-elrendezés**:
  a `QueryPerformanceCounter`-t használó `0x9a5210` időzítő, a `0x9e5e20`/`0x9e5e70`
  lebegőpontos geometria, a `0x9d1130` a szülő-láncon (`[this+0x330]`) lép.
- A `0x9d1150` *belépéskor* olvassa a `[esi+0x291]`-et (`0x9d124e`), és a
  végén (`0x9d1555`) törli. A `0x290`/`0x291` tehát **újrarajzolás/-elrendezés
  kérő-jelző**, nem mentési jelző.
- **Teljes pásztázás (literál `+ 0x291]` offset, a teljes `.text`):** 31 találat.
  Egy olvasás (`0x9d124e`, a `0x9d1150`-ben), egy törlés (`0x9d1555`), egy
  írás regiszterből (`0x9cfaa2`, `mov [esi+0x291], bl`) és 28 írás konstans `1`-gyel
  (pl. `0x9d2c80`-ban, és a `0x9d24fb`–`0x9d2cc2` jelölőkben). **Egyetlen olvasó
  van, és az elrendezés.** Mentési útvonal nem olvassa.
- Hiányosság: a pásztázás csak a literál eltolást látja. Struktúra-másolás vagy
  számolt bázis (`base+0x291`) nem jelenik meg benne.

#### Az X rekordtáblájának mért kezelője

- `0x9d2c80` (21 utasítás), `stdcall`, egy argumentum (`ret 4`):
  `X[+0x294][idx·8+4] |= 1`; ha az argumentum alsó bájtja nem nulla, a
  `|= 0x1000` is; utána `X[+0x291] = 1` és `X[+8] |= 2`. A jelölés tehát
  **rekordonkénti bit**, a `0x1000` a „választott” jelző lehet, de ez
  **nincs igazolva** (nincs név, nincs olvasó, ami a 0x1000-t mentésként
  értelmezné).
- A 2. kör állítása (a `0x9d2c80` a rekordot jelöli, a dirty-jelző
  `+0x291`) **megerősítve**. A „dirty = mentésre váró” értelmezés
  **megdőlt**.
- A 0x9d1150 hívási gráfjának mélység-2 szintjén nincs fájl-API (`CreateFile*`,
  `WriteFile`, `fopen`). Három vtábla-hívás (`call reg`) nem oldható fel
  statikusan; az ezekre épülő útvonal kizárva NINCS.

#### Fájl-sztringek és xrefjeik (mért)

| sztring | VA | xref-függvény | mit mutat |
|---|---|---|---|
| `personalbumid`, `suggestionpersonalbumid`, `facerect`, `facerectdata`, `personalbumrecs`, `personalbumrecvalues`, `personalbumrecs2`, `personalbumrecvalues2`, `peoplealbumchecksum` | `0xc80b84`–`0xc80c30` | rekord-leíró konstruktor `0x4127c0` (`imagedata` osztály, `vtbl=0xc82494`) | **db3 `imagedata` sor mezői**, nem ini-kulcsok |
| `albumdata`, `catdata`, `catpri`, `token` | `0xc80d5c` | `0x4156f0` | db3 `albumdata` leíró |
| `contacts.xml` | `0xc90e74` | `0x57fae0` (kiírás: `contacts`, `contact`, `name`, `modified_time`, `profile_photo_url`, `google_plus_id`, `gaia_id`, `email%d`, `local_contact`, `person_id2`, `focus_ids`, `sync_enabled`, `hidden_contact`); `0x581975` (olvasó `0x5817c0`) | Google-kontakt szinkron; **nincs képazonosító-mező** (csak `profile_photo_url`, egy URL) |
| `faceicon` | `0xcb1190` | `0x74ad40` → `0x74c110` | a gyorsítótár-kulcs (2. kör) |
| `picasa.ini`, `.db3`, `albums_0` | `0xc80a6d` | nincs xref | a név másként épül (nem egy sztring) |

Megjegyzés: a `personalbumrecs`/`personalbumrecvalues` a `imagedata` sor
mezője. A db3 **mezőnként** író a `0x4127c0` osztályból; az író ismeretlen.

#### Tárolási jelöltek — a 3. kör eredménye

| jelölt | állapot |
|---|---|
| `0x9d1555` mentési ciklus | ⛔ **MEGDŐLT**: elrendezés; a `+0x291`-nek egyetlen olvasója van, és az elrendezés |
| `contacts.xml` | ⬇️ **gyengült**: a kiírt mezők között nincs képazonosító |
| db3 `imagedata.personalbumrecs` / `…recvalues` | NYITOTT — az íróját nem találtam; a személy-album rekordjainak perzisztált alakja lehet, nem bizonyított |
| db3 `albumdata` | NYITOTT — a leíró nem tartalmaz borító-mezőt (a 2. körben mért lista sem) |
| `faceicon` gyorsítótár | KIZÁRVA mint tároló (2. kör) |
| `.picasa.ini` | NYITOTT — nincs sztring-xref |

#### Nyitott kérdés (a tárolási döntés előtt)

Melyik függvény írja a `imagedata` sor `personalbumrecs`/`personalbumrecvalues`
mezőit (a `0x4127c0` osztály mezőkiíró ciklusa), és a választott indexkép
azonosítója ebben a mezőben van-e?

Megszerzés útja (sorrendben):
1. A `0x4127c0` osztály mezőinek eltolása (a `lea eax,[esi+X]` a
   `call 0x494c50` előtt) és a mezőt író függvény keresése az
   eltolás-pásztázással (nem az xref-indexszel).
2. A `0x9d1150` három feloldatlan vtábla-hívásának célja (RTTI vagy a
   konstruktor), hogy a gráf zárt legyen.
3. Csak 1–2 után natív QEMU-futtatás a `qemu_harness/hb.py`-val (a
   rekordtábla és a `this` kézzel épül; a futtatás eredményét ki kell mondani).
4. Futásidejű mérés (2026-10-09-i kommentben javasolt diff): indexkép-váltás
   személy-albumban, előtte–utána diff a `.picasa.ini`-re, `contacts.xml`-re
   és db3-ra.

Addig a 1022. tétel „Kész, ha” listája NEM érvényes: a tárolási hely nincs
bizonyítva. A megvalósítás nem indulhat.

#### Megjegyzések a 2. körhöz

- A 2. kör „mentési ciklus” hívottjainak listájában (`0x9a5210`, `0x40a050`,
  `0x9e5e70`, `0x9e5e20`, `0x9e02a0`, `0x9d1130`) a `0x9a5210` időzítő
  (`QueryPerformanceCounter`), a `0x9e5e20`/`0x9e5e70` lebegőpontos geometria. A
  listából egyik sem fájlírás.
- A 2. kör `0x603660` → `0x9d1555` láncát a 3. kör nem erősíti meg: a
  `0x9d1555` nem a mentés utáni törlés.
- A `0x603634` (`mov byte ptr [edi+0x291], 1`) egy olyan függvényben van, amely
  a `0x603660` előtt ér véget; ezt nem vizsgáltam.

### 4. kör (2026-10-12): lemezre írt `albums.db`-adat megvan, a személy–fotó-kulcs kapcsolata nyitott

Módszer: a bináris-indexből vett függvényhatárok célzott diszasszemblálása a
kutatói venv Capstone-jával; teljes `.text`-pásztázás nem történt. A bináris
SHA-256-a változatlan: `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Natív Picasa-futtatás és előtte–utána profil-diff nem történt.

#### A beállító útja: a kép bájtjai eljutnak a lemezre

- A `0x00603660` sikeres ágában a `0x60373d`–`0x60374c` argumentum-előkészítés
  és hívás a
  `0x004115c0`-nak átadja a `[this+0x2bc]+0x2428` tárolót, a
  `[this+0xeac]+0x3c0` értéket és nullát; az EAX-ban átadott képleíróból a
  `0x4115c0` képpuffer-másolatot készít, majd `0x006b75f0`-et hív.
- A `0x00415790` konstruktor `+0x2428` tagjához az `albums.db` nevet rendeli
  (`pmp-database.md` 6.1). A `0x4115c0 → 0x6b75f0 → 0x6b6620 → 0x6b71b0`
  útban a `0x6b71b0` hívja a `0x99df20` fájlíró burkot; annak utasítása a
  `WriteFile` importot hívja (`[0xc40240]`). A `0x6b6620` a
  `FlushFileBuffers` importot is meghívja (`[0xc40468]`). Ez a lánc a kép
  bájtjainak perzisztens `albums.db`-tárba írását igazolja.
- A tároló nem a `contacts.xml` vagy a `.picasa.ini`: az itt követett adatút
  a `CThumbDB` album-bélyegkép tárába megy. A menükezelő más közvetlen hívásai
  korábban már fel lettek sorolva; ez a pozitív lelet nem állítja, hogy az
  egész programban más formátumú út nincs.

#### A visszaolvasó út: a személy-album felület ugyanebből a tárból kér

- A `0x004114e0` a `0x006b6a50` olvasóba lép. A lemezről olvasó ág a
  `ReadFile` importot hívja (`[0xc4042c]`).
- A `0x0074ad40` fejlécépítő a `faceheaderpanel` ágnál a fejléc tulajdonosának
  `[+0x2bc]+0x2428` tárából hívja a `0x4114e0`-et a
  `[header+0x2a0]` kulccsal (`0x74b692`–`0x74b6ac`), majd a `faceicon`
  elemet építi fel. Ez a fejléc megnyitásakor rendelkezésre álló lemez-cache
  olvasási út.
- A másik fogyasztó, a `0x0064ae90` Személyek-panel építő, albumrekordonként
  ugyancsak a `+0x2428` tárból olvas a `0x4114e0`-en át
  (`0x64b5d0`–`0x64b5e2`). Ez a fejlécútvonaltól különálló fogyasztói út.

#### A választás újraindítás utáni fennmaradása: még nincs bizonyítva

A kulcskapcsolatot nem sikerült bizonyítani: a beállító a
`[this+0xeac]+0x3c0` értéket adja át a `0x4115c0`-nak, a fejléc-visszaolvasó
viszont `[header+0x2a0]`-t, a Személyek-panel pedig a rekordlistából kapott
`esi` értéket. A célzott utasításolvasat nem igazolja, hogy ez a három érték
azonos, illetve hogy melyik az albumsor-index és melyik a fotóazonosító.
Tehát bizonyított a kép-bájtok `albums.db`-be írása és e tárból való
személy-fejléc olvasás, de **nem bizonyított**, hogy a kijelölt fotó ugyanazzal
a személykulccsal kerül be és jön vissza újraindítás után.

#### Cáfoló kísérlet

Az ellenhipotézis az volt, hogy a `0x4115c0` hívás csak egy általános,
újraépíthető album-borító cache-t tölt, és nem perzisztál személyenkénti
választást. A `pmp-database.md` 6.3–6.4 szakasza szerinti, külön albumlista-út
(`0x00423300` → `0x00423500`) ugyanebbe a `+0x2428` tárba menti a fotókból
összeállított borítót; a visszaolvasás előtt az albumtartalomból számolt
érvényességi bélyeget ellenőrzi (`0x6c9d60`). Ez igazolja, hogy a tár
tartós, de önmagában nem választás-adatbázis. A személy-fejléc út is ugyanazt
a tárat olvassa, ám a beállító és olvasó kulcsainak azonossága hiányzik.
Ezért a cáfoló eredménye: a „csak memória” feltevés megdőlt a képadatokra;
a „választás is megmarad” állítás nem igazolódott.

#### Mai PicasaPy és mintaadat

- `PhotoContextMenu.qml` továbbra is `placeholder: true`; a
  `PicasaMenuItem.qml` letiltja. A `people_controller.py` `PersonRecord`
  alakja név és képszám, a `peopleOfRows` az aktuális sorokból választ
  ideiglenes `thumbUrl`-t, és nem olvas mentett személy-album borítót.
- A megadott mérőadat-archívumban nincs People/db3/contacts mintaelem;
  ehhez a vizsgálathoz nem bontottam ki fájlt, `.bt` sem keletkezett.
- Wine nem érhető el. A helyi QEMU-harness egyedi függvények kézzel épített
  bemenettel való futtatására szolgál; a teljes Picasa felhasználói
  munkafolyamatát és újraindításos profilmérést nem futtattam vele.

#### Bizonyítottság és további lépés

- **Feltételes** a célállításra: a lemezre írás és a fejlécből való
  visszaolvasás külön utakon igazolt, de a kulcsok azonossága és a kiválasztás
  újraindítás utáni visszaállása nincs meg.
- A cáfoló ellenőrzés mércéje is teljesül: a tár tartós volta pozitív
  `WriteFile`/`ReadFile` utasításokból jön, az ellenpélda pedig egy másik,
  szabályos albumborító-képző hívási út; az ellenpélda nem cáfolja, hogy
  személy-album is használhatja ugyanazt a tárat.
- A döntő következő mérés egy eredeti Picasa-profilon: az indexkép
  beállítása előtt és után a `Picasa2/db3/albums_0.db` és
  `albums_index.db`, a személyalbum-fejléchez használt kulcs, valamint az
  újraindítás utáni visszaolvasott kép rögzítése. Ezt a mérőadat-archívum
  hiánya miatt ez a helyi kör nem tudta elvégezni.

Így a 1022. tétel tároló-megállapítása pontosítva van: az `albums.db` a
bizonyított lemez-cache, a `.picasa.ini`/`contacts.xml`/`imagedata` mezők
közötti választástárolási állítás nyitott marad. A fejlesztői „Kész, ha”
lista és a kattintásos teszt a kulcsazonosság és az újraindításos mérés
igazolásáig nem zárható le.

#### Nyitott

Ghidra-kör kell: 0x00603660 — a `[this+0xeac]+0x3c0` érték szemantikai azonosítása, és annak megállapítása, hogy az `albums.db` kulcsa a személy albumsor-indexe-e [blokkoló]

Ghidra-kör kell: 0x0074ad40 — a `faceheaderpanel` olvasó `[header+0x2a0]` kulcsának szemantikai azonosítása, és összevetése a beállító kulcsával [blokkoló]

Mérés kell: eredeti Picasa-profilon előtte/utána fájldiff és újraindításos
ellenőrzés; az érintett próbaadat NINCS MEG.

### 5. kör (2026-10-13): a `0x603420` vtábla `CThumbDB`; a választási kulcs nyitott

Módszer: az indexben rögzített függvényméretek szerinti célzott Capstone-
diszasszemblálás, RTTI/vtábla-adat ellenőrzés, valamint a `+0x4c` vtáblatárolók
teljes `.text`-beli keresése kizárólag a `paszta.py`-val, első műveletként
`paszta.memoria_kapu()`-val. A pásztázás mért csúcs-RSS-e 100.8 MiB. A bináris
SHA-256-a változatlan (`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`).
Natív Picasa-futtatás és profil-diff nem történt.

#### A `0x603420` virtuális hívásai — az osztály és a célok azonosítva

- **A út — utasítás és konstruktor:** a `0x00603420` a kezelő
  `[this+0x2bc]` objektumának `+0x4c` mezőjében lévő vtáblát olvassa; a
  `0x6034ac` a `+8` slotot, a `0x6034e4` az alap (`+0`) slotot tölti be. A
  hívás ECX-je az objektum `+0x4c`-re eltolt alobjektuma (`0x6034af`). A
  `paszta.py` találata szerint a `0x00415790` konstruktor `0x0041580b` címen
  `0x00c820a8` értéket ír a `[this+0x4c]` mezőbe; az elsődleges vtábla címe
  ugyanitt `0x00c81f78`.
- **B út — RTTI és vtábla-adat, az A út feltételezése nélkül:** az index
  RTTI-rekordja a `0x00c820a8` címet `CThumbDB::vftable`-ként nevezi meg; a
  rekord taglistája `0x00424640` és `0x00424b10` címeket tartalmaz. A bináris
  vtábla közvetlen dword-kiolvasása megerősíti, hogy a `+0` cél `0x00424640`,
  a `+8` cél pedig `0x00424b10`. A két független út tehát egyezik: a
  `0x603420` eltolással kapott `CThumbDB` alobjektum vtábláján hív.
- A célok utasításolvasata olvasási irányt mutat: a `0x00424640` ága
  `0x004290e0`-n át a `0x006b6a50` olvasóhoz és `ReadFile`-hoz vezet; a
  `0x00424b10` meghívja a `0x006b67c0`-t, amely szintén a `0x006b6a50`
  olvasóhoz jut. Ez a két virtuális cél nem azonosítja a kiválasztott fotó
  mentését; a mentő ág továbbra is a 4. körben leírt `0x4115c0` út.

#### A tár neve és a személyválasztás kulcsa külön kérdés

- A konstruktor `0x00415790` a `CThumbDB` `+0x2428` tagjához `albums.db`
  logikai alapnevet regisztrálja (ld. `pmp-database.md` 6.1). A
  `0x006b6070` az `_index` utótagot, a `0x006b61e0` a `_%d` blokksorszámot
  képezi. A mintában mért fizikai fájlpár `albums_index.db` és
  `albums_0.db` (`pmp-database.md` 5. tárolóleírás). Ez a logikai név és a
  blokktár fizikai fájlneve közti feloldás; nem ellentmondás, és önmagában
  nem bizonyít személyenkénti választásrekordot.
- A `0x0074ad40` fejlécépítő `0x74b490`–`0x74b4a5` között összeveti a
  `[header+0x2a0]` értéket a `[header+0x2b4]+0x3c0` mezővel, majd eltéréskor
  oda másolja. A `faceheaderpanel` olvasója a `[header+0x2a0]` kulccsal kér a
  `+0x2428` tárból (`0x74b692`–`0x74b6ac`). A `set_thumbnail` esemény
  diszpécsere (`0x005e0f70`, `0x5e1838`–`0x5e183d`) viszont a
  `0x00603660`-at hívja; az a `[this+0xeac]+0x3c0` értéket adja át a
  `0x4115c0`-nak. Az utasítások különböző bázismutatókat mutatnak. Nem
  bizonyított, hogy a `[header+0x2b4]` és a `[this+0xeac]` ugyanaz az objektum,
  ezért a két `+0x3c0` érték azonossága sem állítható.
- Következésképp továbbra is csak az bizonyított, hogy a képbájtok a
  `CThumbDB` lemez-cache-ébe kerülnek, és a személy-fejléc ugyanebből a
  cache-ből olvas. **A kiválasztott fotó személyhez rendelése, e választás
  újraindítás utáni visszaállítása, illetve ennek esetleges külön adatbázis-,
  ini- vagy registry-helye nincs meg.**

#### Cáfoló kör és mérleg

Megpróbáltam cáfolni azt a feltevést, hogy a `0x603420` virtuális hívásai
írják le a kiválasztott képet: mindkét vtábla-cél utasításait a fenti RTTI-
azonosítástól függetlenül követtem, és mindkettő a `ReadFile`-os olvasóhoz
jut, míg a `WriteFile`-os út a `0x4115c0`-ból indul. Ez cáfolja, hogy e két
virtuális cél közvetlenül a megfigyelt mentő hívás lenne; nem bizonyítja, hogy
az általuk hívott segédek semmilyen más állapotot nem módosítanak. Ellenőrző
mérceként a `ReadFile` és `WriteFile` importcélokat a bináris utasításaival
vetettem össze, ugyanazzal a címalapú módszerrel.

A kulcsazonosság ellenpróbájában a két `+0x3c0` mezőnél az objektum-bázisokat
is követtem: a fejlécfrissítő `esi=[ebx+0x2b4]` bázisra ír, a kezelő pedig
`[this+0xeac]` bázist olvas. A közös mezőeltolás nem teszi azonossá a két
objektumot. A vizsgálat nem tudta kizárni, hogy a mutatók végül közös
objektumra mutatnak; ez a kapcsolat nyitott marad.

- **Bizonyítottsági fok:** feltételes a jegy célállítására. Két független út
  megerősíti a `0x603420`-ból elért `CThumbDB` vtáblát és a slotcélokat;
  egyik sem igazolja a kiválasztás kulcsazonosságát vagy újraindítás utáni
  visszaállását.
- **Következő döntő lépés:** Ghidra-körben a `0x00603660` kulcsának és a
  `0x0074ad40` fejléc-kulcsának szemantikai azonosítása, a két mutató
  kapcsolatának követése; utána eredeti Picasa-profilon előtte/utána db3-
  diff és újraindításos képernyőmérés. A rendelkezésre álló mérőadat-archívum
  nem tartalmazott ehhez használható People/db3 profilmintát; Wine nem
  érhető el, teljes natív munkafolyamatot nem futtattam.

#### Nyitott

Ghidra-kör kell: 0x00603660 — a `[this+0xeac]+0x3c0` érték szemantikai azonosítása, és annak követése, hogy a `0x005e0f70` eseményhívásban ez hogyan kapcsolódik a személyhez [blokkoló]

Ghidra-kör kell: 0x0074ad40 — a `[header+0x2a0]` olvasókulcs, a `[header+0x2b4]+0x3c0` másolat és a beállító kulcsának objektum-/értékazonossága [blokkoló]

Mérés kell: eredeti Picasa-profilon előtte/utána `Picasa2/db3` fájldiff és újraindításos visszaolvasás; az érintett próbaadat NINCS MEG.

### 6. kör (2026-10-13): a kulcsút összeér; a képadat lemezre kerül

Módszer: célzott, index szerinti Capstone-diszasszemblálás; RTTI/vtábla-
ellenőrzés; teljes .text-pásztázás kizárólag paszta.py-val,
paszta.memoria_kapu() első műveletként. A bináris SHA-256 változatlan:
644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96.
Eredeti Picasa-profilon újraindításos próba nem történt.

#### A beállító és a fejléc kulcsa azonos

A korábbi kör nyitva hagyta, hogy a két +0x3c0 ugyanaz-e. A teljes
objektum- és eseményút követése összeköti őket:

1. A 0x005e0f70 set_thumbnail ága a 0x00603660 kezelőt hívja
   (0x005e1838–0x005e183d). A kezelő az arg+0xeac mező CAlbumSelectionNode
   objektumának +0x3c0 kulcsát adja át a 0x004115c0 írónak
   (0x00603669–0x00603677, 0x0060372d–0x0060374c).
2. Az objektumtípust a 0x0056bc10 dinamikus castja azonosítja:
   CSelectionNode → CAlbumSelectionNode; a forrás- és cél-típusleíró
   címe 0x00d3e720 és 0x00d3db90. A CThumbUI ezt az objektumot tárolja
   +0xeac-ban (0x0056bc43–0x0056bc52, 0x0056bd2e–0x0056bd50).
3. A faceheaderpanel selectedbyheader útja a fejléc +0x2a0 kulcsát
   továbbítja a CThumbUI +0x2a4 alobjektuma +0x44 virtuális helyére
   (0x005df245–0x005df26b). A CThumbUI konstruktor a +0x2a4 mezőhöz
   0x00c90754 vtáblát ír (0x005645da és 0x005653da); a RTTI-lista
   +0x44 slotja a 0x006dc190.
4. A 0x006dc190 a kapott kulcsot esi-be veszi, az aktuális
   CAlbumSelectionNode +0x3c0 mezőjével hasonlítja össze, és eltéréskor
   ugyanezt az esi-t adja a 0x00766860-nak (0x006dc199–0x006dc1a0,
   0x006dc24b–0x006dc266). A 0x00766860 ebből készít CAlbumLabel-t;
   a 0x00746ef0 a kulcsot a címke +0x2a0 mezőjébe írja (0x00746fa6).
5. A 0x0074ad40 a címke +0x2a0 kulcsát a hozzá tartozó
   CAlbumSelectionNode +0x3c0 mezőjébe írja (0x0074b490–0x0074b4a5),
   majd ugyanezzel a +0x2a0 kulccsal olvas a +0x2428 albumtárból
   (0x0074b692–0x0074b6ac). A címke selected eseményében szereplő
   CAlbumSelectionNode a 0x005de8e0 selected ágán át kerül vissza a
   CThumbUI +0xeac mezőjébe.

Rövid, nyers utasításleletek:

| cím | diszasszemblált művelet |
|---|---|
| 0x005df245–0x005df24b | mov eax, [ebp+8]; mov ecx, [eax+0x24]; mov eax, [ecx+0x2a0] |
| 0x005df255–0x005df26b | mov ecx, [esp+0x10]; mov edx, [ecx+0x2a4]; call [edx+0x44] |
| 0x006dc24b–0x006dc266 | cmp [eax+0x3c0], esi; eltéréskor mov eax, esi; call 0x00766860 |
| 0x0074b490–0x0074b4a5 | mov esi, [ebx+0x2b4]; mov edi, [ebx+0x2a0]; mov [esi+0x3c0], edi |
| 0x0060372d–0x0060374c | mov edx, [ebp+0xeac]; mov eax, [edx+0x3c0]; call 0x004115c0 |
| 0x0074b692–0x0074b6ac | mov ecx, [ebx+0x2a0]; call 0x004114e0 |

Ez esemény- és típuskapcsolat, nem pusztán azonos eltolás. A személy-
album fejléc kulcsa állítja be a CThumbUI aktuális albumkiválasztását;
a beállító ennek a CAlbumSelectionNode-nak a +0x3c0 mezőjét írja, a
fejléc pedig a címke +0x2a0 mezőjéből ugyanazzal a kulccsal olvas.

#### A kulcs a személy-album sorindexe; a képadat tartós cache-be kerül

A picasa-arcfelismeres.md 3.4/b mérésében a ]facealbum:N N értéke az
albumdata saját sorindexe, és az imagedata_personalbumid is ezt az
indexet használja. Ez az eseményúttól független adatmodell-bizonyíték;
egyezik a fejléc és a beállító kulcsával.

A 0x00603660 a CAlbumSelectionNode +0x3c0 kulcsot és a CThumbDB
+0x2428 albumtárat adja a 0x004115c0-nak. A kép a
0x006b75f0 → 0x006b71b0 → 0x0099df20 útvonalon WriteFile-hívással
kerül a blokktárba; a 0x006b6620 FlushFileBuffers-t hív. A
0x00415790 a +0x2428 mezőhöz az albums.db logikai tárat rendeli; a
fizikai blokktár neve albums_index.db és albums_0.db.

A fejléc ugyanazon CThumbDB-ből, ugyanazon kulccsal olvas:
0x0074ad40 → 0x004114e0 → 0x006b6a50 → ReadFile. A feltárt pozitív
útban a kiválasztott fotó képbájtjai kerülnek a személy-album sorindexéhez
rendelt cache-slotba; külön választásrekordot ez az út nem mutat. A bináris
tartós lemezírást és azonos kulcsú visszaolvasást tartalmaz. Más tárolási
út meglétét ez a kör nem zárta ki.

#### Cáfoló kör: általános albumborító-újraépítés

Az ellenhipotézis az volt, hogy az automatikus borító-ellenőrzés a kézi
képet érvényteleníti. A 0x00423300 általános albumborító-út a tárolt
bélyeget az albumból számított értékkel hasonlítja össze, eltéréskor a
0x00423500 újraépítést hívja. A set_thumbnail harmadik argumentuma
nulla; a 0x006b75f0 ezt a CThumbDB +0x54 bélyegvektorába írja,
a 0x006b66c0 pedig ugyanezt a vektort olvassa. Ha a 0x00423300 út
ugyanazt a személyalbum-sort dolgozná fel, a cache újraépülhetne.

A személy-fejléc és a Személyek panel (0x0064ae90) viszont közvetlenül
a 0x004114e0 olvasót hívja, és nem futtatja a 0x00423300 ellenőrzést.
Nem találtam bizonyítékot arra, hogy ez az általános újraépítő út
személyalbum-sort dolgoz fel; a mintaprofil és a natív újraindításos
mérés hiánya miatt a lehetséges háttér-újraépítés nincs kizárva. Ezért
a bináris a tartós tárolási útvonalat megerősíti, a tényleges
újraindítás utáni képernyőeredmény feltételes marad.

#### Mai PicasaPy és fejlesztési követelmény

- A PhotoContextMenu.qml sor letiltott placeholder.
- A PersonRecord csak nevet és képszámot tárol; a peopleOfRows az aktuális
  sorokból választ ideiglenes photo_id/thumbUrl értéket. Nincs tartós
  személy–fotó hozzárendelés.
- Az eredeti Picasa tárhelye `albums.db`. A PicasaPy-implementáció javasolt
  helye a tartós SQLite index, az `index/` API-ján keresztül; az `app/`
  csak az API-t használja, a `.picasa.ini`-t ne bővítsük nem szabványos
  kulccsal. A jelenlegi `PersonRecord`-nak nincs tartós azonossága: csak
  név és képszám van benne, a személyek összesítése név szerint történik.
  A mappánként eltérő `[Contacts2]` ID és a Picasa album-sorindexe sem
  használható globális tartós kulcsként. Előbb a személy stabil kulcsát
  kell megtervezni az `index/` rétegben; a fotóazonosító újraindítás és
  újraindexelés utáni feloldhatóságát szintén rögzíteni kell. Új tábla,
  kulcs vagy rekordalak még nincs meghatározva.

#### Bizonyítottság és a jegy „Kész, ha” pontjai

- **Bizonyítottsági fok: feltételes a teljes újraindításos viselkedésre.**
  Az író- és olvasóút ugyanarra a `CThumbDB`-tárra, valamint azonos
  `albumheader/%x/%d/faceicon` kulcsformára mutat. A független újraolvasás
  a kulcsnév egyezését megerősítette, de a két út formázófüggvényének
  numerikus argumentum-azonosságát nem; a sorindex-szemantika ezért nem
  tekinthető két független úttal megerősítettnek. Profil-diff és
  újraindításos képernyőmérés nem történt, az általános cache-újraépítő
  lehetséges hatása nincs lezárva.
- A korábbi 0x00603660 és 0x0074ad40 kulcsazonossági Ghidra-kérések
  lezárhatók a fenti statikus eseményúttal; a 0x00763150 útvonal kérdése
  külön nyitott marad.
- ⛔ A választás újraindítás után látszik: az eredeti bináris adatútja
  megvan, de PicasaPy menüje letiltott, tényleges újraindításos próba nincs.
- ✅ A tárolási hely kutatása dokumentált: eredetiben `albums.db`,
  PicasaPy-ban javasoltan a tartós SQLite index `index/` API-ja; a konkrét
  rekord és stabil személy/fotó kulcs még tervezendő.
- ⛔ Kattintásos teszt: nem futott, mert ez kutatási kör volt, kód nem változott.

PicasaPy fejlesztői készfeltételek:

1. A fotó helyi menüje a kiválasztott photo_id-t és a jelenlegi
   személy-kulcsot adja át.
2. Az index API a választást tartós SQLite rekordba menti; az új
   személy-fejléc ugyanebből a rekordból tölti be a választott fotót.
3. A mentés után a fejléc azonnal frissül; az alkalmazás újraindítása
   után ugyanaz a fotó jelenik meg. Hiányzó fotónál a megjelenítés a
   meglévő elsőfotó-tartalékra tér vissza.
4. Kattintásos teszt ellenőrzi a menüpontot, a megjelenített fotót és
   az újraindítás utáni visszaállást.

#### Nyitott

Mérés kell: eredeti Picasa-profil előtte/utána Picasa2/db3 diff és
újraindításos faceheaderpanel-ellenőrzés; az érintett minta NINCS MEG.

Ghidra-kör kell: 0x00763150 — a CAlbumList általános borítóútja
feldolgozza-e a ]facealbum sort, és újraépítheti-e a nullás bélyegű
kézi képet [blokkoló].

### 7. kör (2026-10-14): a mai menüsor letiltott, az eredeti újraindításos eredménye nyitott

Módszer: a mai QML- és Python-forrás célzott olvasata; a bináris-index
függvényméreteivel célzott `annot_disasm.py` diszasszemblálás; független
újraolvasás egy másik elemzővel, a korábbi spec és a mai forrás megmutatása
nélkül. Teljes `.text`-pásztázás nem történt. A mérőadat-archívumhoz nem
találtam People/db3 mintát; fájlt nem bontottam ki, a korábban létrejött
`.bt` könyvtár üres maradt. Wine nem érhető el, eredeti Picasa-profilon
újraindításos mérés nem történt.

#### A jegyben leírt mai állapot — helyesbítve

- `PhotoContextMenu.qml:250–270`: a `contextMenuSetAsPeopleAlbumThumbnail`
  tétel ténylegesen jelen van; `personName` mellett látható, de
  `placeholder: true`. A `PicasaMenuItem.qml:67` emiatt letiltja. Nincs
  `onTriggered` és nincs személy-indexkép mentésére szolgáló jelzés.
- `people.py:34–40`: a `PersonRecord` mezői `name` és `photo_count`; tartós
  személyazonosítója nincs. A `people.py` modulösszesítése a mappák közötti
  `[Contacts2]` azonosítók helyett név szerint gyűjt.
- `people_controller.py:630–694`: a `peopleOfRows` az aktuális kijelölt
  sorokból állítja elő a `photo_id`, arc-rect és `thumbUrl` értékeket; az
  első érintett fotó adja az ikont. A PeoplePanel ezt a `thumbUrl`-t rajzolja
  (`PeoplePanel.qml:295–304`). Ez a kijelölt sorokból képzett pillanatnyi
  kép, nem mentett személy-album választás.
- A célzott `app/` és `index/` keresésben nem találtam tartós
  személy–fotó választási mezőt vagy API-t. Így a jegy „Nálunk ma” része
  két külön dolgot mosott össze: a menüpont helyőrzőként létezik; a
  személyenkénti tárolás valóban hiányzik. Az Arcfelismerés-specifikáció
  „megvan” megállapítása az eredeti Picasa parancsára vonatkozik, nem a
  PicasaPy aktív kattintási útjára.

#### Két út, és a független ellenőrzés határa

**A út — a parancs és a lemezíró.** A `set_thumbnail` literál
(`0x00c96fc8`) a `0x005e0f70` diszpécserben a `0x00603660` kezelőre visz
(`0x005e1838–0x005e183d`). A sikeres ág a `CAlbumSelectionNode +0x3c0`
kulcsát és a `CThumbDB +0x2428` tárat adja a `0x004115c0`-nak. A hívási
lánc a `0x006b75f0 → 0x006b71b0 → 0x0099df20` fájlíró burkon át a
`WriteFile` importot éri el; a `0x006b6620` a `FlushFileBuffers`-t hívja.
A `0x00415790` a `+0x2428` tagot `albums.db`-ként regisztrálja; a
`WriteFile` és `FlushFileBuffers` importhelye rendre `[0xc40240]` és
`[0xc40468]`.

**B út — a fejléc olvasója.** A külön `0x0074ad40` faceheader-építő a
fejléc `+0x2a0` kulcsával a `+0x2428` tárból hívja a `0x004114e0`-et;
az olvasólánc `0x006b6a50`-en át a `[0xc4042c]` `ReadFile` importot hívja.
A helyi diszasszemblálás a `0x00cb1218` címen lévő
`albumheader/%x/%d/faceicon` kulcsformát is megmutatja. Az
eredeti adatréteg specifikációjának mért modellje szerint a
`]facealbum:<N>` N-je az `albumdata` saját sorindexe; a `[Contacts2]` ID és
ez a sorindex telepítés-/újraindexelés-függő, nem globális PicasaPy-kulcs
(`picasa-arcfelismeres.md` 3.4/b).

Az első út a fájlba írást, a második külön fogyasztói úton a fájlból
olvasást igazolja. A független újraolvasás külön is megtalálta a diszpécser
és a faceheader `albumheader/%x/%d/faceicon` kulcsformáját, de nem bizonyította,
hogy a két formázóhívás numerikus argumentumai azonosak. Ezért a
kulcsformátum és a lemez-cache használata alátámasztott; a kiválasztott
személy-sor kulcsának két független úttal való azonossága és a felhasználó
által látott újraindításos eredmény nem megerősített.

#### Cáfoló kísérlet

Az ellenhipotézis: az általános album-borító-ellenőrzés újraépíti a kézi
képet, ezért az újraindítás után nem marad kiválasztottként. A
`0x00423300` általános út bélyeget számol az album tartalmából, eltérésnél
`0x00423500`-at hív; a közvetlen faceheader- és Személyek-panel-olvasó
viszont `0x004114e0`-et hív, nem ezt az ellenőrzőt. Ez a cáfoló azt mutatja,
hogy az ismert közvetlen fejléc-olvasás nem építi újra a képet. Azt nem
zárja ki, hogy az indulás vagy a `CAlbumList` más útja ugyanezt megtegye;
az ellenhipotézis ezért nem dőlt meg teljesen. A cáfoló mércéje bináris
utasításolvasat és a `pmp-database.md` 6.3–6.4 útvonala; teljes `.text`
negatív keresés nem történt.

#### PicasaPy-tárolási hely és fejlesztési követelmény

Az eredetiben a kiválasztott kép bájtjai a `CThumbDB` `albums.db`
lemez-cache-ébe kerülnek; ez nem bizonyítja, hogy a cache önmagában
felhasználói beállításként túléli az összes induláskori újraépítő utat.
PicasaPy-ban a javasolt adattár a tartós SQLite index, módosítása csak az
`index/` API-ján keresztül. Az új rekord/tábla még nincs meghatározva. A
fejlesztés előtt az `index/` rétegben stabil személy-kulcsot kell
meghatározni; a mappánként eltérő `[Contacts2]` ID és a Picasa
`albumdata`-sorindex nem alkalmas erre. A fotóhoz is olyan index-azonosító
kell, amelyet az alkalmazás újraindításkor fel tud oldani; a mostani
`photo_id` tartósságát nem bizonyítottam. A `.picasa.ini` nem bővítendő
nem szabványos választáskulccsal.

#### Bizonyítottság és a jegy „Kész, ha” pontjai

- **Bizonyítottsági fok: feltételes.** A bináris megerősíti, hogy a
  `set_thumbnail` út képbájtokat ír a fájl-alapú `albums.db` tárba, és a
  faceheader külön útja ugyanebből a tárból olvas. A keresztút kulcsának
  numerikus azonosságát az önálló második olvasat nem erősítette meg; az
  újraindítás utáni UI-eredményről nincs natív mérés.
- **A két független út:** A = parancs/kezelő → `WriteFile` az `albums.db`
  tárhoz; B = faceheader → `ReadFile` ugyanabból a tárból, azonos
  kulcsformátummal. Egyeznek a tár és a kulcs alakjában; az argumentumok
  azonossága és a látható újraindításos eredmény nyitott.
- **Cáfoló kísérlet:** az ismert általános újraépítő út képes a cache
  tartalmát újraszámolni; a közvetlen faceheader-út ezt nem hívja. A teljes
  indulási/albumlista-út nincs kizárva, tehát a cáfoló nem zárja le a
  kérdést.
- ⛔ A személy-album indexképe választható és újraindítás után megmarad:
  a PicasaPy menüsora letiltott, nincs tároló és nincs natív
  újraindításos mérés.
- ✅ A tárolás helye a specifikációban kutatva: eredetiben `albums.db`;
  PicasaPy-ban javaslatként a tartós SQLite index `index/` API-ja szerepel.
  Az új séma és a stabil kulcsok még nincsenek megtervezve.
- ⛔ Kattintásos teszt: nincs aktív kattintási út; ebben a kutatói körben
  nem módosult kód, teszt nem futott.

PicasaPy fejlesztői készfeltételek:

1. Az `index/` réteg adjon tartós személy-kulcsot és újraindításkor
   feloldható fotóazonosítót; egyik se legyen a mappánkénti `[Contacts2]`
   ID vagy a Picasa `albumdata`-sorindex.
2. Az index API mentse és olvassa a személy–fotó választást; a QML csak a
   controlleren át kérdezze és módosítsa.
3. A helyi menü aktív tételének kattintása mentse a kiválasztott fotót,
   majd frissítse a személy-album fejlécét.
4. Kattintásos próba ellenőrizze a mentést, az azonnali megjelenést és az
   alkalmazás-újraindítás utáni visszaállást.

#### Nyitott

Mérés kell: eredeti Picasa-profilon választás előtti/utáni `Picasa2/db3`
diff, majd újraindítás után a faceheader tényleges képének ellenőrzése; a
megfelelő mérőadat NINCS MEG, Wine nem érhető el.

Ghidra-kör kell: 0x00763150 — a CAlbumList általános borítóútja feldolgozza-e
a `]facealbum` sort, és az induláskori cache-ellenőrzés lecserélheti-e a
kézi indexképet [blokkoló].
