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

| # | eredeti felirat | gyorsbillentyű | van-e nálunk |
|---|---|---|---|
| 1 | Mappaleírás szerkesztése… | — | nem |
| — | *elválasztó* | | |
| 2 | Az összes kép kijelölése | `Ctrl+A` | nem (menüsávban igen) |
| 3 | Kijelölés törlése | `Ctrl+D` | nem |
| 4 | Kiválasztás megfordítása | `Ctrl+I` | nem |
| 5 | Áthelyezés gyűjteménybe ▸ | — | **igen** |
| — | *elválasztó* | | |
| 6 | Indexképek frissítése | — | nem |
| 7 | Mappa rendezésének alapja ▸ | — | nem |
| — | *elválasztó* | | |
| 8 | Mappa elrejtése | — | nem |
| — | *elválasztó* | | |
| 9 | Keresés a lemezen | `Ctrl+Enter` | nem |
| 10 | Eltávolítás a Picasából… | — | nem |
| — | *elválasztó* | | |
| 11 | Mappa áthelyezése… | — | nem |
| 12 | Mappa törlése… | — | nem |
| — | *elválasztó* | | |
| 13 | Feltöltés a Google Fotókba… | — | nem |
| — | *elválasztó* | | |
| 14 | Exportálás HTML-oldalként… | — | nem (#351 készül) |
| 15 | Névcímkék hozzáadása | — | nem |

Nálunk ma ebből: „Áthelyezés gyűjteménybe ▸" és a „Mappa dátumának
beállítása…" — utóbbi az **eredetiben nincs is** ebben a menüben (a
Mappaleírás-dialógusban lakik).

### 1.b Harmadik megnyitási pont: a mappa-fejléc a rácsban

A rács tetején ülő **mappa-fejlécre** (nagy mappa-ikon + mappanév + dátum +
műveletsor) jobbklikkelve **ugyanez a 15 tételes menü** jön elő. Tehát a
mappa-menünek **három** megnyitási pontja van, bájtra azonos tartalommal:

1. a rács üres területe (indexképek között),
2. a bal panel mappa-sora,
3. a rács tetején a mappa-fejléc.

Implementációs következmény: **egy** komponens, három `MouseArea`/
`TapHandler` hívóval — nem három külön menü.

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
