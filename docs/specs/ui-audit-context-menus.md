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
