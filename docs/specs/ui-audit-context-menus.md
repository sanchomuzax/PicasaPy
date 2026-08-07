# UI-audit: jobbklikk-kontextusmenük (2026-08-07)

Forrás: a felhasználó **magyar nyelvű Picasa 3.9**-éről készült 5 célzott
képernyőkép a jobbklikk-menükről. Ez az első **rendszeres** felmérés a
témában — a `ui-audit-menus.md` eddig csak egy „bónusz észrevétel"
szakaszban, két véletlen képernyőképből, 4 tételt említett.

Összevetés a jelenlegi implementációval:
`src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml` és
`FolderContextMenu.qml`.

## 0. Összegzés egy mondatban

A Picasában **öt különböző** kontextusmenü él, összesen **~40 egyedi
paranccsal**; a PicasaPy ebből kettőt valósít meg, **9 paranccsal**. A menük
nem díszítés: az eredetiben több funkció **kizárólag** innen érhető el.

| kontextus | eredeti tételszám | nálunk | állapot |
|---|---|---|---|
| mappa fejléce / a rács üres területe | 15 | 2 | súlyosan hiányos |
| bal panel: mappa-sor | 15 (**azonos** a fentivel) | 2 | súlyosan hiányos |
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

## 6. Nyitva

- Album-nézetben az indexkép-menü feltehetően bővül („Eltávolítás az
  albumból"), és a mappa-menü Album-változatra vált — ehhez további
  képernyőkép kell.
- Több kijelölt képnél a menü feliratai többes számba válthatnak
  („Tulajdonságok" vs „…"), ez sem ismert.
- A „Társítás ▸" és a „Mappa rendezésének alapja ▸" almenük tartalma
  nincs lefényképezve.
