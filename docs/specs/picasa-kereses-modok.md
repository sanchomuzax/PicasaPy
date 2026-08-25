# A keresési módok és a másodpéldány-kereső (`ID_DUPES`) — MŰKÖDÉS

*2026-08-25. A menü-leltár (#1397) 1. érdemi tétele.*

## 1. A legfontosabb: a másodpéldány-kereső NEM panel, hanem KERESÉSI MÓD

Az „Eszközök → Fájlok másodpéldányainak megjelenítése" (`eMenuTools::ID_DUPES`)
nem nyit párbeszédet. A hozzá tartozó felületi elem a
**`searchoptions/dupesearch`**, ami a **keresési sáv** egyik jelzője — és a
`.tre`-ben **`m_hidden`**, vagyis csak akkor jelenik meg, ha a mód aktív.

Hat függvény hivatkozza (`0x0040bf70`, `0x005cb990` — a főablak
parancs-diszpécsere —, `0x005d47e0`, `0x005d8810`, `0x005e60d0`,
`0x00660c80`).

## 2. A keresési sáv TELJES elemlistája — 6 élő, 13 HALOTT

`searchoptions.tre`. A `#` előtaggal kezdődő sorok **ki vannak kommentezve**,
tehát a 3.9-ben nem léteznek.

### Élő (6)

| elem | horgony / stílus | felirat |
|---|---|---|
| `searchoptions/searchbackground` | `root`, `m_offsetLTR` | a sáv maga |
| `searchoptions/searchcenter` | `m_offsetLT` | a középső tartó |
| `searchoptions/viewallbutton` (+`-label`) | `m_buttontypecolor3`, font12, középre | **„Back to View All"**, súgó: **„Exit Search Mode"** |
| `searchoptions/label_searchresult` | font12, **`m_hidden`** | **„Search Result:"** |
| `searchoptions/searchresult` | font12 | a találat-szöveg |
| `searchoptions/label_search1` | font12, `m_offsetRT` | jobbra igazított felirat |
| **`searchoptions/facesearch`** | `m_hidden` | az arckeresés jelzője |
| **`searchoptions/dupesearch`** | `m_hidden` | **a másodpéldány-keresés jelzője** |

### ⛔ HALOTT ebben a build-ben (13)

`searchbase` · `boxleft` · `boxright` · `digicam` · **`similarrect`** ·
**`similarthumb`** · **`similarclip`** · **`loadsim`**(+label) ·
**`clearsim`**(+label) · **`savetoalbum`** · `label_searchall` ·
`label_searchnewer` · `label_search2` · `timecontainer`

**Két következmény, amit ki kell mondani:**

1. **A „hasonló képek" keresés NEM LÉTEZIK a 3.9-ben.** A hozzá tartozó öt
   elem (`similarrect`, `similarthumb`, `similarclip`, `loadsim`, `clearsim`)
   mind kikommentezve. ⚠️ **Nálunk viszont VAN**
   (`src/picasapy/dedup/phash.py` dhash + `similar.py`) — ez tehát
   **többlet**, nem hiánypótlás. Nem hiba, de tudni kell róla: az eredetiben
   nincs megfelelője.
2. **A `savetoalbum` GOMB halott, de a MENÜPONT él** — az
   `eMenuTools::ID_SAVESEARCH` („Keresési eredmények mentése…") a leltárban
   szerepel. A keresés mentése tehát **menüből** megy, nem a sáv gombjáról.

## 3. A keresési szűrők családja — `searchcontainer/*`

A `0x00660c80` sztringkörnyezete kiadja a szűrő-kapcsolók készletét:

| elem | mire szűr |
|---|---|
| `searchcontainer/searchbutton` | maga a keresés-gomb |
| `searchcontainer/starsearch` | csillagozott |
| `searchcontainer/facesearch` | arcok |
| `searchcontainer/moviesearch` | videók |
| `searchcontainer/geotagsearch` | geocímkézett |
| `searchcontainer/webview` | webre feltöltött |

⇒ **Öt szűrő-kapcsoló van a sávon** — a **másodpéldány-mód NINCS köztük**,
azt kizárólag a menüpont kapcsolja be. Ugyanitt jelenik meg a `]hidden`
token is (a rejtett elemek szűrése).

## 4. Az importáláskori másodpéldány-ellenőrzés — külön, aszinkron

Ez **másik** mechanizmus, mint a keresési mód:

| elem | cím / bizonyíték |
|---|---|
| `AcquireDupeCheckThread` | `0x00513680` — a szál neve |
| `iCAcquireDupeChecker` | RTTI `0x00c89490` |
| `iCAcquireDupeCheckJob` | RTTI `0x00c89488` |
| `ytAsyncQueue<iCAcquireDupeCheckJob>` | RTTI `0x00c894b8` |
| `acquirepanel/excludedupesbutton` | `0x0051cd20`, `0x0051f600` — a „másodpéldányok kihagyása" kapcsoló |

A felhasználónak mutatott szövegek (szövegtár):
`CAcquireUI::WipeCardSingleDupe` — *„…nem lesz importálva, mert már
másodpéldány a Picasában."*, `WipeCardMultiDupes`, `WipeCardMultiExcluded`,
`WipeCardDupesNotDone`.

⇒ **Aszinkron feladatsor** dolgozik rajta importálás közben, nem a fő szálon.

## 5. Ami NYITVA marad

**Mi alapján dönt másodpéldányról?** A `0x00513680` szálnak a saját nevén
kívül nincs sztringje, és **az `originhash` szó a bináris szövegtárában nem
szerepel** (csak a `backuphash`, 8 helyen) — tehát a kulcs nem onnan jön.
A következő lépés az `iCAcquireDupeChecker` vtable-jének végigjárása
(`0x00c89490`).

*Bizonyítottsági fok: **megerősített** a keresési sáv élő/halott
elemlistájára, a szűrő-családra és az importáláskori ellenőrzés
osztályaira (`.tre` + RTTI + sztring-xref). **Nyitva**: a
másodpéldány-döntés kulcsa.*
