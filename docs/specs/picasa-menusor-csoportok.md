# A Picasa 3 menüsora: sorrend, csoportok, szélesség — mérve

*2026-08-31 (#1774). Ez a lap a **tulajdonos képernyőmentéseiből** készült
(`\\DS215j\lemez\My Pictures\Picasa-3-menuk`, magyar Picasa 3.9, Windows,
100/125/150/175% DPI). Ami itt szerepel, azt a kép **mutatja** — nem
következtetés.*

A lap három olyan kérdésre felel, amire sem a szövegtár, sem a bináris nem
felel: **milyen sorrendben állnak a menük**, **hol vannak az elválasztók**,
és **mekkora a menük valós szélessége**. A tételek azonosítói és feliratai
a `picasa-menu-leltar.md`-ben (#1397) vannak; ez a lap nem ismétli meg őket.

---

## 1. A menüsor sorrendje

```
Fájl · Szerkesztés · Nézet · Mappa · Kép · Létrehozás · Eszközök · Súgó
```

Mind a nyolc mentés menüsávja ugyanezt a sorrendet mutatja (a mentések a
megnyitott menütől jobbra eső részt is látni engedik, így a sorrend
**minden képen** ellenőrizhető, nem csak az elsőn).

A szövegtár ábécérendben sorolja a nyolc gyökérkulcsot, ezért a sorrend
**belőle nem olvasható ki** — a jegy ezt a mai QML-sorrend igazolatlan
feltevéseként írta le. A mérés a feltevést **megerősíti**.

---

## 2. A csoportok (elválasztók)

A `·` a tételeket, a vízszintes vonal az elválasztót jelöli. `(i)` = a
mentésen inaktív (szürke) tétel — az inaktív tételek **láthatók**, tehát a
csoportszerkezet a mentésből hiánytalanul kiolvasható.

### Fájl — 19 tétel, 9 csoport

| # | tételek |
|---|---|
| 1 | Új album… `Ctrl+N` |
| 2 | Mappa hozzáadása a Picasához… · Fájl felvétele a Picasába… `Ctrl+O` · Importálás forrása… `Ctrl+M` · Importálás a Google Fotókból… |
| 3 | Fájl(ok) megnyitása szerkesztőben `Ctrl+Shift+O` (i) |
| 4 | Áthelyezés új mappába… (i) · Átnevezés… `F2` |
| 5 | Mentés `Ctrl+S` · Visszaállítás (i) |
| 6 | Mentés másként… · Másolat mentése · Kép exportálása mappába… `Ctrl+Shift+S` |
| 7 | Keresés a lemezen `Ctrl+Enter` · Törlés lemezről `Delete` |
| 8 | Nyomtatás… `Ctrl+P` · E-mail… `Ctrl+E` · Papírképek rendelése… |
| 9 | Kilépés |

### Szerkesztés — 11 tétel, 4 csoport

| # | tételek |
|---|---|
| 1 | Kivágás `Ctrl+X` (i) · Másolás `Ctrl+C` (i) · Beillesztés `Ctrl+V` (i) |
| 2 | Az összes effektus másolása (i) · Az összes effektus beillesztése (i) |
| 3 | Szöveg másolása (i) · Szöveg beillesztése (i) |
| 4 | Az összes kijelölése `Ctrl+A` · Csillagozottak kijelölése · Kiválasztás megfordítása `Ctrl+I` · Kijelölés törlése `Ctrl+D` (i) |

**Nincs „Visszavonás" tétel a menü élén.** A szövegtárban van
`eMenuEdit::ID_UNDO` és `ID_REDO`, a mentésen viszont **egyik sem
jelenik meg** — pedig a menü többi inaktív tétele igen. Vagyis a
Visszavonás/Ismétlés nem a menüsáv Szerkesztés menüjének állandó tétele.

### A Szerkesztés menü TELJES szerkezete — a binárisból (#1795)

A menüt ugyanaz a táblavezérelt függvény építi, mint az Eszközök menüt
(`0x00559150`). A Szerkesztés almenü **egyetlen rekord-tábla** a `.data`-ban:

- **a tábla kezdete `0x00d6db80`**, rekordméret **20 bájt**;
- **a darabszám-konstans `14`** (`push 0xe` a `0x00559c76`-on, a
  `0x00559c82` regisztráló hívása előtt, a gyerekmutatóval együtt:
  `push 0xd6db80`, `0x00559c7c`).

**14 = 11 tétel + 3 elválasztó.** Az elválasztó rekord mind a 20 bájtja
nulla; a három elválasztó a 3., 6. és 9. rekord (`0x00d6dbbc`,
`0x00d6dbf8`, `0x00d6dc34`), tehát a csoportosztás **3 | 2 | 2 | 4** —
pontosan az, amit a tulajdonos képernyőmentése mutat.

**Rekord-alak** (mind a 14-re azonos):

| eltolás | tartalom |
|---|---|
| `+0x00` | a honosított felirat mutatója (a kulcsból feloldva, `call 0x009ae560`) |
| `+0x04` | a gyorsbillentyű betűje (ASCII sztring) vagy `0` |
| `+0x08` | `word` — mind a 14 rekordon `0` |
| `+0x0a` | `word` — a **parancsazonosító** |
| `+0x0c`, `+0x10` | `0` |

**A tábla TELJES tartalma, kiolvasva:**

| # | cím | kulcs | eredeti EN felirat | HU felirat | gyorsb. | parancs |
|---|---|---|---|---|---|---|
| 0 | `0x00d6db80` | `eMenuEdit::ID_CUT` | `Cu&t` | `&Kivágás` | `X` | `0x9d39` (40249) |
| 1 | `0x00d6db94` | `eMenuEdit::ID_COPY` | `&Copy` | `&Másolás` | `C` | `0x9d3b` (40251) |
| 2 | `0x00d6dba8` | `eMenuEdit::ID_PASTE` | `&Paste` | `&Beillesztés` | `V` | `0x9d3c` (40252) |
| 3 | `0x00d6dbbc` | — | — | — | — | **elválasztó** |
| 4 | `0x00d6dbd0` | `eMenuEdit::ID_EDIT_COPYALLEFFECTS` | `C&opy All Effects` | `Az összes effektus más&olása` | — | `0x9d6f` (40303) |
| 5 | `0x00d6dbe4` | `eMenuEdit::ID_EDIT_PASTEALLEFFECTS` | `Paste All E&ffects` | `Az összes e&ffektus beillesztése` | — | `0x9d70` (40304) |
| 6 | `0x00d6dbf8` | — | — | — | — | **elválasztó** |
| 7 | `0x00d6dc0c` | `eMenuEdit::ID_EDIT_COPYTEXT` | `Copy Text` | `Szöveg másolása` | — | `0x9ded` (40429) |
| 8 | `0x00d6dc20` | `eMenuEdit::ID_EDIT_PASTETEXT` | `Paste Text` | `Szöveg beillesztése` | — | `0x9dee` (40430) |
| 9 | `0x00d6dc34` | — | — | — | — | **elválasztó** |
| 10 | `0x00d6dc48` | `eMenuEdit::ID_ALBUM_SELECTALLPICTURES` | `Select &All` | `Az ö&sszes kijelölése` | `A` | `0x9cb8` (40120) |
| 11 | `0x00d6dc5c` | `eMenuEdit::ID_SELECTSTAR` | `Select &Starred` | `&Csillagozottak kijelölése` | — | `0x9d5b` (40283) |
| 12 | `0x00d6dc70` | `eMenuEdit::ID_SELECT_INVERT` | `&Invert Selection` | `Kiválasztás &megfordítása` | `I` | `0x9c47` (40007) |
| 13 | `0x00d6dc84` | `eMenuEdit::ID_CLEAR_SELECTION` | `C&lear Selection` | `Kijelölés &törlése` | `D` | `0x9c90` (40080) |

⚠️ Két tételnek **nincs** aláhúzott betűje az eredetiben (`Copy Text`,
`Paste Text`), a `Select &Starred`-nek pedig **nincs gyorsbillentyűje** —
ezek nem elírások, hanem a mért állapot.

#### A `Copy Text` és `Paste Text` engedélyezése (#5877)

A két parancs frissítését a `CThumbUI` `0x0056e1c0` címen kezdődő
menüfrissítője végzi; a Szerkesztés-menü ága a kapcsolótábla 1. esete,
belépési címe `0x0056e742`. Az ág **két UI-állapot szerint eltérő
feltételrendszert** használ. A disassembly nem nevezi meg a `this` mezők
szemantikáját, ezért alább a bináris mezőeltolásai szerepelnek.

Jelölések az ágban:

- `P`: a `dword[0x00d67914]` nem nulla, az `editpanel/preview` objektum
  megtalálható, és az objektum `+0x20c` bájtja nulla
  (`0x0056e240`-`0x0056e265`).
- `D`: a `this+0x3094` vagy a `this+0x30a0` értéke nagyobb nullánál
  (`0x0056e30b`-`0x0056e322`).
- `F`: a `this+0x34a8` értéke. A `F & 0x4000` bitet a
  `0x0056e2e8`-`0x0056e2ef`, a `(F & 0x6) != 0` őrfeltételt a
  `0x0056e2f4`-`0x0056e306` vizsgálja.
- `T`: van kijelölt elem (`this+0xe64 != -1`), és a
  `0x006b1e80` segédfüggvény nem üres szöveget olvas ki az első kijelölt
  elemről (`0x0056e801`-`0x0056e873`, a kijelölési vektor előállítása:
  `0x0056e9cd`-`0x0056ea0a`). Több kijelölésnél ez az ág az első elem
  szövegét ellenőrzi.
- `C`: a `this+0xcc8` szövegpuffer nem üres: a mutató nem null, a
  `(dword[puffer] & 0xffffff00) != 0`, és a `byte[puffer+4] != 0`
  (`0x0056e931`-`0x0056e95b`, illetve `0x0056eb40`-`0x0056eb80`).
- `B`: a `this+0x34a4` értéke nulla.

Az ágak explicit állapotírásainál a kiszámított feltétel igazságakor az
átadott argumentum `0`, hamisságakor `1`. A binárislelet nem azonosítja
megbízhatóan a fogadó API mezőjének nevét/polaritását, ezért a táblázat a
nyers argumentumot rögzíti, nem nevezi önmagában „engedélyezettnek” vagy
„szürkének”.

| Útvonal | `Copy Text` állapotargumentuma | `Paste Text` állapotargumentuma |
|---|---|---|
| `P` igaz, `D` igaz | `1` (`0x0056e7b4`-`0x0056e7e5`) | `1` (`0x0056e7b4`-`0x0056e7e5`) |
| `P` igaz, `D` hamis | `0`, ha `T && B`; különben `1` (`0x0056e801`-`0x0056e873`) | ha `C` igaz: `0`, ha `B`, különben `1`; ha `C` hamis, ez az ág nem ír állapotot (`0x0056e92b`-`0x0056e95b`) |
| `P` hamis, `F & 0x4000` nem nulla | `1` (`0x0056e9c0`, `0x0056eba2`-`0x0056ebbe`) | `1` (`0x0056e9c0`, `0x0056eba2`-`0x0056ebbe`) |
| `P` hamis, `F & 0x4000` nulla | `1`, ha `(F & 0x6) != 0 && T && B`; különben `0` (`0x0056ea45`-`0x0056ea72`) | `1`, ha `(F & 0x6) != 0 && B && C`; különben `0` (`0x0056eb40`-`0x0056eb80`) |

**Mérés (`job-277`, a jegyben közölt lelet):** könyvtárnézetben egy
felirat nélküli kijelölt képnél mindkét tétel szürke, miközben
`Copy All Effects` és `Cut`/`Copy` engedélyezett. A leírás nem rögzíti a
`P`, `D`, `F`, `B` és `C` nyers állapotát, így ebből a mérésből a konkrét
bináris útvonal és a callback-argumentum polaritása nem ellenőrizhető. A
`P` igaz, üres vágólapos Paste-Text ág pedig nem ír állapotot, tehát ott a
korábbi/alapállapot marad érvényben.

**Bizonyítottság: feltételes.** Az UpdateUI ág utasításszintű olvasata
megadja a fenti nyers feltételeket; a külön parancskezelők (`0x005fecd0`,
`0x005fefc0`) ettől függetlenül igazolják, hogy a `Copy Text` a kijelölt
elem szövegét olvassa, a `Paste Text` pedig a `this+0xcc8` puffert használja.
Ez a job-277 megfigyelésével összhangban van. A callback mezőinek teljes
UI-szemantikája, az állapotargumentum UI-polaritása és a pozitív ág közvetlen,
kattintásos mérése nyitott marad.

#### ⛔ Visszavonás/Ismétlés a Szerkesztés menüben NINCS — és nem is lehet

A #1774 köre azt gyanította, hogy a menüépítő **feltételesen** teszi be a
visszavonást (van-e visszavonható lépés), és a mentés készítésekor épp nem
volt ilyen. **Ez megdőlt, két független mérésből:**

1. **A tábla statikus.** A 14 rekordot feltöltő kódblokk
   (`0x005598b2`–`0x00559c4c`) **pontosan 11 feltételes ugrást** tartalmaz,
   és mind a 11 ugyanaz: a felirat-feloldás `NULL`-ellenőrzése
   (`cmp eax, ebx` / `je`). **Állapotfüggő elágazás nincs benne**, tehát a
   menü darabszáma és tartalma futásidőben nem változik. (A blokk elején
   álló `test byte ptr [0xda03a8], al` / `jne` **egyszeri inicializálás**
   őre, nem tételválasztás.)
2. **A kulcs nem létezik a programban.** Az `eMenuEdit::ID_UNDO` és az
   `eMenuEdit::ID_REDO` literál a `Picasa3.exe` teljes fájljában
   **0 alkalommal** fordul elő — sem ASCII-ban, sem UTF-16LE-ben. A
   feliratok csak az erőforrás-szövegtárban élnek
   (`stringres-en-hu.tsv`: „Undo"/„Visszavonás", „Redo"/„Újra"), amit
   **semmi nem kér el** — ezek **halott erőforrás-bejegyzések**.

#### Hol VAN visszavonás az eredetiben — mind a négy hely

| hol | erőforrás / elem | felirat (EN / HU) |
|---|---|---|
| a szerkesztő panel gombja | `editpanel/filter_undo`, `CFilterStackUI::undolabel` / `undoname` | `Undo` / `Visszavonás`, illetve `Undo <effekt>` / `Visszavonás: <effekt>` |
| **Kép** menü | `eMenuPicture::ID_PICTURE_REVERT` | `Undo &All Edits` / `Összes szerkesztés vissz&avonása` |
| szövegmező helyi menüje | `Address::ID_UNDO`, a menüt a `0x007331e0` építi (7 tétel: Visszavonás · Kivágás · Másolás · Beillesztés · Törlés · Az összes kijelölése · Automatikus kitöltés) | `&Undo` / `&Visszavonás` |
| mentés-visszavonó párbeszéd | `CThumbUI::FileRevert::undosave` | `Undo Save` / `Mentés visszavonása` |

**Bizalmi fok: megerősített.** A tábla, a darabszám, az elválasztók, a
parancsazonosítók és az ugrás-számlálás közvetlen kiolvasásból; a
negatív eredmény teljes fájl-pásztázásból (két kódolás).

### Nézet — 19 tétel, 8 csoport

| # | tételek |
|---|---|
| 1 | Könyvtárnézet (i) |
| 2 | Kis indexképek `Ctrl+1` · **✓** Normál indexképek `Ctrl+2` · Szerkesztési nézet `Ctrl+3` |
| 3 | Tulajdonságok · Címkék `Ctrl+T` · Emberek · Helyek |
| 4 | **✓** Szerkesztési vezérlők megjelenítése (i) |
| 5 | Diavetítés `Ctrl+4` · Időrend `Ctrl+5` |
| 6 | Keresési opciók · **✓** Kis képek · Rejtett képek |
| 7 | Színkezelés használata · Megjelenítési mód ▸ |
| 8 | Indexkép felirata ▸ · Mappanézet ▸ |

A 2. csoport **rádiócsoport** (egy pipa a háromból), a 4. és a 6. csoport
pipái függetlenek.

### Mappa — 12 tétel, 6 csoport

| # | tételek |
|---|---|
| 1 | Leírás szerkesztése… · Diavetítés megtekintése `Ctrl+4` |
| 2 | Indexképek frissítése · Rendezés ▸ |
| 3 | Elrejtés · Megjelenítés (i) |
| 4 | Indexképek nyomtatása… `Ctrl+Shift+P` · Exportálás HTML-oldalként… |
| 5 | Keresés a lemezen `Ctrl+Enter` · Eltávolítás a Picasából… |
| 6 | Áthelyezés… · Törlés… |

**#4644 — az F2 „Átnevezés…” rekord nem a Mappa menü része.** A Mappa
főtömbje `0x00d6e1c0`-nál kezdődik, és `0x0055b28f` pontosan 17 rekorddal
adja át a `0x005590c0` menüépítőnek. A `0x00d6e318` című F2 rekord a tömbön
kívül van: a Kép menü „Csoportos szerkesztés” elemének `0x00d6e4b8`
gyermekmutatója erre a címre mutat, a gyerekszám pedig `0x13` (19). Tehát
az F2 a **Kép ▸ Csoportos szerkesztés** almenü első rekordja; a Mappa
főmenü 12 tétele + 5 elválasztója ezzel összhangban van.

A rekordot építő ágban a `0x0055b29c`–`0x0055b2a8` közötti
`[0x00da03a8] & 0x200` ellenőrzés egyszeri menüinicializálási kapu, nem
kijelölés- vagy nézetfeltétel. A rekord megjelenése az almenü
megnyitásához kötött; az aktivált/szürke állapot kijelölésfüggését ez a
vizsgálat nem állapítja meg.

### Kép — 7 tétel, 5 csoport

| # | tételek |
|---|---|
| 1 | Megjelenítés és szerkesztés `Ctrl+3` · Csoportos szerkesztés ▸ |
| 2 | Összes szerkesztés visszavonása |
| 3 | Elrejtés (i) · Megjelenítés (i) |
| 4 | Arcok alaphelyzetbe állítása |
| 5 | Tulajdonságok `Alt+Enter` |

### Létrehozás — 8 tétel, 3 csoport

| # | tételek |
|---|---|
| 1 | Beállítás háttérképként… (i) · Poszter készítése… |
| 2 | Képkollázs… · Hozzáadás a képernyővédőhöz… · Ajándék CD készítése… · Mozgófilm ▸ |
| 3 | Közzététel a Bloggeren… |

### Eszközök — 13 tétel, 5 csoport

| # | tételek |
|---|---|
| 1 | Mappakezelő… · Feltöltéskezelő… (i) · Személyek kezelése… |
| 2 | Fotómegjelenítő beállítása… · Képernyővédő konfigurálása… |
| 3 | Képek biztonsági mentése… · Csoportos feltöltés… · Dátum és idő beállítása… |
| 4 | Feltöltés ▸ · Geocímke ▸ · Kísérleti ▸ |
| 5 | Gombok konfigurálása… · Beállítások… |

A menü **nem tartalmaz** duplikátum- vagy arckereső tételt a felső szinten.
✅ **A Kísérleti almenü tartalma azóta KIMÉRVE** — ld. a következő szakaszt
(#1794): a `ID_DUPES` ott van, a második helyen.

### Az Eszközök menü TELJES szerkezete — a binárisból (#1794)

A menüt **egyetlen** függvény építi: `0x00559150` (15 495 b). Nem
`AppendMenuW`-vel — az egész függvényben **két** Win32-hívás van
(`0x00559169`, `0x0055cda7`) —, hanem egy `.data`-beli **rekord-táblát** tölt
fel mezőnként (`0x00d6e678`…`0x00d6e9a8`). Az `eMenuTools::` névtér mind a
**36** kulcsa ebben az egy függvényben szerepel.

A felépítés sorrendje adja a csoportosítást; a három almenü-cím (`Upload`,
`Geotag`, `Experimental`) rekordja egy **gyerek-mutatót** és egy
**darabszámot** kap.

#### A KÍSÉRLETI almenü — kilenc tétel

A `0x0055c91e` a gyerek-mutatót `0x00d6e798`-ra állítja, a `0x0055c928` pedig
a darabszámot **`9`-re** — konstansként. Pontosan kilenc tétel épül fel
összefüggő blokkban (`0x0055c295`…`0x0055c4c9`), a színblokk után és a
felső szintű blokk előtt:

| # | kulcs | angol | magyar |
|---|---|---|---|
| 1 | `ID_FTPWEB` | Publish via FTP... | Közzététel FTP-n keresztül... |
| 2 | **`ID_DUPES`** | **Show Duplicate Files** | **Fájlok másodpéldányainak megjelenítése** |
| 3 | `Searchfor` ▸ | Search for... | Keresés... |
| 4 | `ID_SAVESEARCH` | Save &search results... | Keresési eredmények &mentése... |
| 5 | `ID_SEARCHTOKEN` | Show &tag as album... | &Címke megjelenítése albumként... |
| 6 | `ID_PASSPORT` | &Passport photo... | Útle&vélkép... |
| 7 | `ID_DELETE_EMPTY_ALBUMS` | Delete empty online albums... | Üres online albumok törlése... |
| 8 | `ID_MOVE_DATABASE` | Choose database location... | Adatbázis helyének kiválasztása... |
| 9 | `ID_WRITE_XMP_FACES` | Write faces to XMP... | Arcinformációk írása XMP-adatokba... |

⇒ **A #1794 feltevése beigazolódott: a `ID_DUPES` a Kísérleti almenüben van**,
a második helyen.

#### A „Keresés…" ALMENÜ — hét tétel

A 3. tétel maga is almenü. A `Searchfor` rekord gyerekmutatója
`0x00d6e708` (`0x0055c36f`), a gyerekszám mezője pedig **7**
(`0x0055c379`). A `0x0055c078`-nál induló blokk az alábbi hét elemet építi,
ebben a sorrendben:

| kulcs | angol | magyar |
|---|---|---|
| `ID_S_RED` | &Red | &Piros |
| `ID_S_ORANGE` | &Orange | &Narancssárga |
| `ID_S_YELLOW` | &Yellow | &Sárga |
| `ID_S_GREEN` | &Green | &Zöld |
| `ID_S_BLUE` | &Blue | &Kék |
| `ID_S_PURPLE` | &Purple | &Lila |
| `ID_VIEW_BW` | &Black and White | &Fekete-fehér |

Az utolsó elem rekordja `0x00d6e780`, parancsazonosítója `0x9da9`;
közvetlenül a hat `ID_S_*` szín után áll. A feliratkulcs a Nézet
névteréből származik, de ebben a menüben a `color:black` keresést indítja
(részletek: [picasa-menu-parancsok-viselkedese.md](picasa-menu-parancsok-viselkedese.md) 20.).

#### A másik két almenü

| almenü | tételek |
|---|---|
| **Feltöltés** (`Upload`) | `ID_TOOLS_UPLOAD` (Feltöltés a Google Fotókba) · `ID_TOOLS_COLLAB` (Feltöltés közös szerkesztésű webalbumba) · `ID_TOOLS_YOUTUBE` (Feltöltés a YouTube webhelyre) |
| **Geocímke** (`Geotag`) | `ID_PICTURE_GEOTAG` (Geocímkézés a Google Earth programmal…) · `ID_VIEW_EARTH` (Megtekintés a Google Earth programban…) · `ID_PICTURE_GEOUNTAG` (Geocímkék törlése) · `ID_EXPORT_EARTH` (Exportálás Google Earth-fájlba) |

#### A felső szint

`0x0055c54c`…`0x0055c7b6`: `ID_TOOLS_INCLUDEEXCLUDEFOLDERS` ·
`ID_TOOLS_UPLOADMGR` · `ID_TOOLS_CONTACTMGR` · `ID_TOOLS_CONFIG_SLINGSHOT` ·
`ID_TOOLS_CONFIG_SCREENSAVER` · `ID_TOOLS_BACKUP` · `ID_TOOLS_BATCH_UPLOAD` ·
`ID_TOOLS_ADJUST_TIMESTAMP` · `ID_TOOLS_DOWNLOAD_FACES`; utána a három
almenü-cím, végül `ID_TOOLS_BUTTONMGR` és `ID_TOOLS_OPTIONS`.

Ez **fedi a tulajdonos képernyőmentését**, egy tétellel több:
`ID_TOOLS_DOWNLOAD_FACES` („Névcímkék letöltése a Picasa Webalbumokból") —
a mentésen nem látszik, valószínűleg feltételes.

#### ⛔ „Find Faces" — az EGÉSZ szövegtárban NINCS

Nem csak az `eMenuTools` névtérből hiányzik: a `stringres-en-hu.tsv`
**teljes** állományában nincs „Find Faces" felirat. A „duplicate/másodpéldány"
találatok mind máshova tartoznak (`CAcquireUI::…`, `CThumbUI::MoveFiles…`,
`ContactManagerDlg::DupFoundTitle`, `IDS_NORENAME`).

⇒ Az **arckeresés az eredetiben nem menüparancs**. A miénk tudatos eltérés.

**Bizalmi fok.** A tételek, a feliratok, a sorrend és a „Find Faces"
negatívum: **megerősített** (közvetlen kiolvasás, kimerítő keresés). Az,
hogy a kilenc elemű blokk a **Kísérleti** almenüé: **erős** — a
darabszám-konstans `9` egyedül erre a blokkra illik (a másik két almenü 3 és
4 elemű, és a darabszámuk regiszterből jön), de a rekord-tábla mezőkiosztását
nem fejtettem meg teljesen, tehát a hozzárendelés levezetés, nem közvetlen
olvasat.


### Súgó — 10 tétel, 4 csoport

| # | tételek |
|---|---|
| 1 | Súgó – tartalom és tárgymutató `F1` · Billentyűkódok |
| 2 | Picasa-fórumok · Online információ · Termékkiadási tájékoztató · Adatvédelmi irányelvek · Általános Szerződési Feltételek · A Picasa eltávolítása |
| 3 | Frissítések keresése |
| 4 | A Picasa névjegye |

---

## 3. Szélesség — nincs rögzített minimum

A mentések vágott képek, a menü bal szélétől a jobb széléig. A menük
szélessége **tételenként más**, és nincs közös alsó érték:

| menü | szélesség 100%-on (kp) |
|---|---|
| Fájl | 349 |
| Nézet | 315 |
| Mappa | 313 |
| Kép | 312 |
| Szerkesztés | 286 |
| Súgó | 272 |
| Létrehozás | 269 |
| Eszközök | 253 |

**A szélesség a DPI-vel arányosan nő** — a Fájl menü négy nagyításban:

| DPI | mért szélesség | a 100% szorosa |
|---|---|---|
| 100% | 349 | 1,00 |
| 125% | 433 | 1,24 |
| 150% | 520 | 1,49 |
| 175% | 604 | 1,73 |

Vagyis a szélességet **kizárólag a betűméret-arányos szövegméret** adja: a
leghosszabb felirat, plusz a bal oldali pipa-vályú, plusz a jobb oldali
gyorsbillentyű-oszlop. Rögzített képpontos minimum nincs benne — ha lenne,
az arány a kis nagyításoknál elromlana.

**Nálunk** a `PicasaMenu.qml` 200 képpontos alsó korlátot tart (#1740).
Ez a mérés szerint idegen elem, de **nem okoz csonkolást**, és a legszűkebb
mért eredeti menü is 253 képpont — a korlát a gyakorlatban sosem lép
életbe. Külön jegy nélkül nem bántjuk.

---

## 4. Amit ez a lap NEM dönt el

- a **Kísérleti**, **Feltöltés**, **Geocímke**, **Rendezés**, **Csoportos
  szerkesztés**, **Mozgófilm**, **Megjelenítési mód**, **Indexkép
  felirata** és **Mappanézet** almenük tartalma — a mentések nem nyitják ki
  őket (a Rendezés készletére a #1595 és a #1766 fut);
- a 4. menü **kontextusfüggő** címkéje (Mappa ↔ Album) — a mentés mappa-
  nézetben készült, tehát csak a „Mappa" alakot mutatja;
- ~~a **mnemonikok**~~ — **MEGVÁLASZOLVA (2026-09-03, #1795 köre).** A képen
  tényleg nem látszik az aláhúzás (a Windows elrejti, amíg az `Alt`-ot le
  nem nyomják), de a **szövegtár megadja**: 189 `eMenu*::` kulcsból 145-ben
  van angol és **142-ben magyar** mnemonik, és a magyar betű gyakran **nem**
  az angol (`Cu&t` → `&Kivágás`). A teljes leképzés kinyerve:
  `picasapy-agent/referencia/menu-mnemonikok.tsv` (248 sor). A Szerkesztés
  menü mind a 11 tételének mnemonikja a fenti táblában áll. Nálunk 144
  menütétel-feliratból **11**-en van mnemonik — átvezetés: **#2152**.
