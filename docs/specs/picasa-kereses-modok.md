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

## 5. A duplikátum-áthelyezés (`moveOthersToDuplicatesFolder`) is a MI TÖBBLETÜNK

*2026-08-28, #1697 (a #1539 kiegészítése).*

A `DedupDialog` nem-destruktív feloldása — a csoport nem megtartandó tagjai
a forrásmappa `Duplikátumok` alkönyvtárába kerülnek
(`app/dedup_controller.py:DedupController.moveOthersToDuplicatesFolder`) —
**szintén a mi kiegészítésünk, nem a Picasa viselkedésének másolása.** Ahogy
az 1. pont leszögezi: az eredeti `ID_DUPES` **SZŰRŐ**, a találatok a fő
rácsban jelennek meg — az eredeti **semmilyen fájlműveletet nem végez** a
másodpéldányokon. A gyűjtőmappába áthelyezés tehát önálló döntés, aminek
NINCS mihez igazodnia a binárisban; egy jövőbeli kör ezért **ne keressen**
hozzá bináris mintát.

**A `Duplikátumok` mappa SZÁNDÉKOSAN nincs kizárva a beolvasásból**
(`scanner/name_filters.py`) — ellentétben a Picasa saját generált
mappáival (`.picasaoriginals`, `.Picasa3Temp`), amiket az eredeti kizár. Ha
kizárnánk, a `Duplikátumok` mappában futtatott duplikátum-keresés (ami
ott ténylegesen hasznos: oda kerülhetnek másodpéldányok több forrásmappából
is) többé nem találna semmit. A kizárás helyett a védelem az ÁTHELYEZÉS
műveletébe került: ha a forrásmappa NEVE (kis-nagybetű-függetlenül, ld.
#1682) már a gyűjtőmappáé, az áthelyezés a fájlt helyben hagyja, és a
felhasználó egyértelmű üzenetet kap — a néma beágyazás (`Duplikátumok/
Duplikátumok`) éppúgy hiba lenne, mint a néma hatástalanság.

## 6. Ami NYITVA marad

**Mi alapján dönt másodpéldányról?** — **MEGFEJTVE Ghidrával (2026-08-30, #1398).**
A `iCAcquireDupeCheckJob` (`0x00513730`) a **fájl `originfast`-ját** számolja
ki (`FUN_00a4d210` — a #1481 MD5-képlete), és ezt a **64 bites értéket**
keresi a meglévő másodpéldány-listában. A `FUN_00436980` = a gyűjtemény-kereső:
`(param_3, param_4)` párt veti össze a lista `(piVar8[0], piVar8[1])`
elemeivel. A találat → dupe-jelölés.

⇒ **A döntés az `originfast` (tartalmi MD5) — NEM a `backuphash`, NEM a
fájlnév.** Ez **MEGDŐLTI** a korábbi állítást („a kulcs nem onnan jön, mert az
`originhash` szó nincs a szövegtárban") — a tévedés: a job az **`originfast`**-ot
használja, nem az `originhash`-t, és az `originfast` a #1481-ben már MD5-ként
ismert.

*Bizonyítottsági fok: **megerősített** (Ghidra-C, `0x00513730` +
`0x00436980`).*

### Kiegészítés — az `iCAcquireDupeChecker` vtable 9 slotja (2026-08-30, olcsó lánc)

A lezárás után az olcsó lánc (string_xrefs + az annotált diszasszemblálás)
**függetlenül megerősíti** a fenti képet, és teljes vtable-térképet ad:

| slot | cím | szerep (diszasszemblálva) |
|---|---|---|
| 0 | `0x005291e0` | destruktor (a `0x00528300` törzsre) |
| 1 | `0x00408b30` | CRITICAL_SECTION zárás a `+0x8`-on |
| 2 | `0x00528420` | **a job-feldolgozó (~872 b)** — a `[+0x6c]` job-listán lépked, `QueryPerformanceCounter`-al időzít |
| 3 | `0x0097b4b0` | queue-limit / beállítás hurok |
| 4 | `0x00513680` | **`AcquireDupeCheckThread`** — szálnév-sztring, 6 bájt („a saját nevén kívül nincs sztringje" ⇒ tényleg csak név) |
| 5 | `0x0060d610` | járulékos feldolgozó (~162 b, ugyanaz a minta) |
| 6/7 | `0x0097b5e0` / `0x0097b5f0` | CRITICAL_SECTION lock/unlock-párok a `+0x28`-on |
| 8 | `0x006cc940` | vtable-küldő (delegált hívás) |

A `0x00513680` **6 bájtos** volta (szószerint `mov eax, "AcquireDupeCheckThread";
ret`) a lap korábbi megállapítását („a szálnak a saját nevén kívül nincs
sztringje") **bájtról-bájtra igazolja** — a tényleges hash-számítás a
`0x00528420` / `0x0060d610` job-feldolgozókban és azok `0x00a4d210`
fájl-olvasójában történik, amit a #1398 Ghidra-bontása már meg is fejtett.

## A `searchoptions/dupesearch` — a keresősáv HETEDIK eleme (#2169, 2026-09-03)

A keresősáv elem-kötője (`0x005d47e0`) hét nevet old fel; a hetedik
(`searchoptions/dupesearch`, `0x00c7ff20`) más névtérben van, mint a hat
`searchcontainer/*` szűrő. **Mit csinál — most kimérve.**

### Milyen vezérlő

**Értékkel rendelkező kapcsoló** — ugyanazon az API-n át, mint a jobb fiók
lap-gombjai (`0x009cd8f0(elemnév, érték)`), és **induláskor REJTETT**:

| hol | mit tesz | cím |
|---|---|---|
| főablak-építő (`0x0040bf70`) | feloldja, majd vtable **`+0x68`** = **elrejti** | `0x0040c8c9`–`0x0040c8de` |
| `Ctrl+F6` ága | feloldja, majd vtable **`+0x6c`** = **megjeleníti** | `0x005e62c8`–`0x005e62e1` |
| parancs-diszpécser | `0x009cd8f0(dupesearch, 1)` = **bekapcsolja** | `0x005ccc23`–`0x005ccc2a` |

⇒ A `dupesearch` **nem a hat szűrőgomb egyike**, hanem egy alapból
elrejtett kapcsoló, amit a duplikátum-keresés bekapcsolása tesz láthatóvá.

### ⭐ AZONOS a Kísérleti almenü „Fájlok másodpéldányainak megjelenítése"
tételével — bizonyítva

A bekapcsoló ág (`0x005ccc14`) a parancs-diszpécser magas azonosítójú
táblájából érhető el (`0x005cc4a6`: indextábla `0x005cde04`, ugrótábla
`0x005cdc30`, `eax = cmd − 0x9d44`), és a hozzá tartozó
**parancsazonosító `0x9d57` (40279)**.

Ugyanez a szám áll az `eMenuTools::ID_DUPES` menürekordban:

```
0x0055c2bd  push 0xc8ded4                       ; "eMenuTools::ID_DUPES"
0x0055c2fa  mov dword ptr [0xd6e7ac], eax       ; a rekord felirata
0x0055c31e  mov word ptr [0xd6e7b6], 0x9d57     ; a rekord PARANCSAZONOSÍTÓJA
```

⇒ **A menütétel és a keresősáv-kapcsoló ugyanaz a funkció.**

### Mit CSINÁL a parancs

```
0x005ccc14  push 1 ; mov edx, 0xc8f448 ; call 0x9cd8f0   ; searchcontainer/searchbutton = 1
0x005ccc23  push 1 ; mov edx, 0xc7ff20 ; call 0x9cd8f0   ; searchoptions/dupesearch    = 1
0x005ccc32  push 1 ; push 0 ; push 0 ; push panel
0x005ccc37  call 0x0065b840                              ; a keresés ÚJRAFUTTATÁSA
```

⇒ **Bekapcsolja a keresőt ÉS a duplikátum-módot, majd újrafuttatja a
keresést.** Nem párbeszédet nyit: a **találati rács** mutatja az
eredményt.

### A kattintás ugyanezt teszi

A keresőbeállítás-panel kezelője (`0x005d8810`) a kiváltó elem nevét
`repe cmpsb`-vel veti össze a beállítás-nevekkel — `digicam`
(`0x00c964a4`), **`dupesearch`** (`0x00c7ff20`, `0x005d94c1` és
`0x005d94d3`, hossz `0x19` = 25 bájt), `viewallbutton` (`0x00c88a54`) —,
és egyezés esetén mind a **`0x005d95af`** ágra megy:

```
0x005d95af  push 1 ; push 0 ; push 0 ; push panel
0x005d95b4  call 0x0065b840
```

⇒ **Ugyanaz a hívás, mint a menüparancs tailje.** A kapcsoló
átbillentése és a menüparancs **bitre azonos** műveletet indít.

### Nálunk (mérve, 2026-09-03)

| | eredeti (mérve) | nálunk ma (mérve) |
|---|---|---|
| a duplikátum-keresés **helye** | a **keresősáv** módja (`searchoptions/dupesearch`) | önálló **párbeszéd** (`Main.qml:1123`, `Find Duplicates...`, `PicasaMenuBar.qml:1480`) |
| az eredmény **hol jelenik meg** | a **találati rácsban**, a keresés újrafuttatásával | a párbeszéd saját listájában |
| a keresősáv szűrői nálunk | `starsearch`, `facesearch`, `moviesearch`, `webview`, `geotagsearch`, `dupesearch` | `facesearch`, `moviesearch`, geo (`MainToolbar.qml:324/370/403`) — **dupesearch nincs** |
| a mag | – | megvan: `src/picasapy/dedup/` (`exact.py`, `similar.py`) |

⇒ A **mag megvan**, a **felületi bekötés más**: nálunk párbeszéd, az
eredetiben keresési mód. Jegy: **#2174**.

### Bizonyítottsági fok

**Megerősített** — a vezérlő fajtája, a rejtés/megjelenítés, a
parancsazonosító egyezése, a menürekord és a közös `0x0065b840` hívás
mind közvetlen kiolvasásból; a mi oldalunk grepből.

---

## ⭐ Az idő-csúszka: NEM tartomány, hanem KOR-szűrő — a teljes képlet (#1830, 2026-09-03)

A keresősáv `timeslider/scaleslider` vezérlője **egyfogantyús**, és a felirata
(„Filter by date range" / „Szűrés dátumtartomány szerint") **félrevezet**.
A mért viselkedés: a csúszka egyetlen értéke egy **maximális KORT** ad meg —
„legfeljebb N napos/hetes/hónapos/éves képek".

### A négy felirat, amit a program megjelenít

| kulcs | angol | magyar |
|---|---|---|
| `CThumUI::searchpicsdaysold` | `Pictures up to %d days old.` | **Legfeljebb %d napos képek.** |
| `CThumUI::searchpicswksold` | `Pictures up to %d weeks old.` | **Legfeljebb %d hetes képek.** |
| `CThumUI::searchpicsmosold` | `Pictures up to %d months old.` | **Legfeljebb %d hónapos képek.** |
| `CThumUI::searchpicsyearsold` | `Pictures up to %d years old.` | **Legfeljebb %d éves képek.** |

(`referencia/stringres-en-hu.tsv` 586–589. sor; a binárisba fordított angol
alapértékek: `0x00ca2c6c`, `0x00ca2ca4`, `0x00ca2ce0`, `0x00ca2d1c`.)

### A KÉPLET — a binárisból kiolvasva

A csúszka nyers értéke egy `float`, jelöljük `s`-sel. A napok száma:

```
ha s == 0        →  NINCS kor-szűrés (a szűrő ki van kapcsolva)
egyébként        →  napok = 2 ^ (13 · (1 − s)) + 1
```

Két, egymástól **független** helyen áll ugyanez a képlet — és ez a lényeg:

| hol | cím | mit csinál vele |
|---|---|---|
| a találati fejléc | `0x0066345c`–`0x006634ac` | a fenti négy felirat egyikét írja ki |
| **a tényleges szűrő** | `0x0065ee3f`–`0x0065eeaa` (a `0x0065d010` keresés-végrehajtóban) | `vágópont = MOST − napok`, és eszerint szűr |

⇒ A csúszka **nem csak feliratot** állít: valóban szűkíti a találatokat.

Az utasítás-szintű bizonyíték (a szűrő oldaláról):

```
0x0065ee3f  fld   dword ptr [edx + 0x24]      ; s — a keresési állapot csúszka-mezője
0x0065ee49  fld1
0x0065ee57  fsubrp st(1)                      ; 1 − s
0x0065ee6e  fmul  qword ptr [0xcf4c08]        ; × 13.0
0x0065ee80  fld   dword ptr [0xcf3a48]        ; 2.0
0x0065ee89  call  0x005568e0                  ; pow(2.0, 13·(1−s))
0x0065ee8e  fadd  qword ptr [0xc7e328]        ; + 1.0      → napok
0x0065ee9f  call  0x0098b6e0                  ; MOST (a rendszeridő, nap-egységű double)
0x0065eeaa  fsub  qword ptr [esp + 0x38]      ; vágópont = MOST − napok
```

A négy kiolvasott konstans: `0x00cf4c08` = **13.0** (qword), `0x00cf3a48` =
**2.0** (dword), `0x00c7e328` = **1.0** (qword) — és a `0x005568e0` az a
kétparaméteres lebegőpontos burkoló, ami a `0x00c0b410` hatványozót hívja.

A „most mínusz N nap" **nap-egységű `double`** aritmetika — ugyanaz az
ábrázolás, amit a `.picasa.ini` `date=` kulcsa is használ (OLE-dátum, napok
1899-12-30 óta).

### A MÉRTÉKEGYSÉG megválasztása — a mért szabály

A `0x006634b0`–`0x006635fd` szakasz **csonkolt** (nulla felé kerekített)
egészekkel dönt:

```
napok  = trunc(napok)
hetek  = trunc(napok / 7)        ; 0x00cf4800 = 7.0
hónap  = trunc(napok / 30)       ; 0x00cf3ed8 = 30.0
év     = trunc(napok / 365)      ; 0x00cf50a8 = 365.0

ha napok < 30            → „Legfeljebb <napok> napos képek.”
különben ha hetek < 10   → „Legfeljebb <hetek> hetes képek.”
különben ha hónap ≤ 12
        VAGY év == 0     → „Legfeljebb <hónap> hónapos képek.”
különben                 → „Legfeljebb <év> éves képek.”
```

### A csúszka VÉGPONTJAI és a menete

| csúszka `s` | napok | a kiírt felirat |
|---:|---:|---|
| 0,00 | — | *(nincs kor-szűrés)* |
| 0,02 | 6842,0 | Legfeljebb 18 éves képek. |
| 0,10 | 3328,0 | Legfeljebb 9 éves képek. |
| 0,20 | 1352,2 | Legfeljebb 3 éves képek. |
| 0,30 | 549,7 | Legfeljebb 1 éves képek. |
| 0,40 | 223,9 | Legfeljebb 7 hónapos képek. |
| 0,50 | 91,5 | Legfeljebb 3 hónapos képek. |
| 0,60 | 37,8 | Legfeljebb 5 hetes képek. |
| 0,70 | 15,9 | Legfeljebb 15 napos képek. |
| 0,80 | 7,1 | Legfeljebb 7 napos képek. |
| 0,90 | 3,5 | Legfeljebb 3 napos képek. |
| 1,00 | 2,0 | Legfeljebb 2 napos képek. |

**A skála logaritmikus**, és **fordított**: a bal vég (`s`→0) enged át
mindent (≈22,4 év a 0-hoz tetszőlegesen közel), a jobb vég (`s`=1) a
**2 napnál frissebbekre** szűkít. A mértékegység-váltás pontos helyei:
`s ≈ 0,3382` (év→hónap, 390 nap), `s ≈ 0,5302` (hónap→hét, 70 nap),
`s ≈ 0,6263` (hét→nap, 30 nap).

### Hol tárolódik, és hogyan indul

A csúszka értéke a **keresési állapot-struktúra `+0x24`** `float` mezője.
A `0x00660c80` (a keresősáv állapotgyűjtője) tölti fel:

```
0x00660e9a  fldz
0x00660ea3  fstp dword ptr [ebx + 0x24]   ; alapérték 0.0 = nincs szűrés
0x00660eab  mov edx, 0xc95f58             ; "timeslider/scaleslider"
0x00660eb0  call 0x009c2fc0               ; elem feloldása
0x00660ebb  call 0x009ddd00               ; ÉRTÉK-OLVASÓ (vtable +0x18) → [ebx+0x24]
```

Ha az elem nem oldható fel, a mező **0.0 marad** — vagyis a hiányzó csúszka
nem szűr, nem pedig „mindent kizár". Induláskor a keresősáv-kötő
(`0x005d47e0`, a 7. eleme) ugyanígy **0.0-ra** állítja
(`0x005d4914`: `fldz … call 0x009ddc90` — az érték-BEÁLLÍTÓ, vtable +0x14).

### Mi történik a fogantyú mozgatásakor

Az eseménykezelő a `0x005de8e0` nagy állapotfüggvényben ül
(`0x005dfd20`–`0x005dfd85`): az érkező elemnevet 23 bájton összeveti a
`"timeslider/scaleslider"`-rel, és ha egyezik **és** az esemény típusa nem
`0x8000001`, meghívja a `0x0065b840`-et — ugyanazt az általános
nézet-/keresés-frissítőt, amit a keresési módok is használnak. A kezelő
`0xf4240`-nel tér vissza („lekezeltem").

### ⛔ NEGATÍV: a `timecontainer` és a `timecontainer_label` a kódból SOHA nem hivatkozott

A `string_xrefs` táblában **egyetlen** találat sincs sem a
`searchcontainer/timecontainer`, sem a `searchcontainer/timecontainer_label`
névre. Csak a `timeslider/scaleslider` szerepel a kódban. A két konténer-elem
tehát tisztán a felületleíró dolga: a `_label` a `.tre`-ben **csak a
buboréksúgót hordozza** (`SharedHandler searchcontainer/tip hottip`), a
`timecontainer` pedig a `timeslider` panel **kivágása**
(`layer:searchcontainer/clip(timeslider): timecontainer`).

### Geometria — a `respack.yt`-ből

| réteg | téglalap | méret |
|---|---|---|
| `searchcontainer/timecontainer_label` (`vbutton`) | (133,12)–(237,28) | **104 × 16** |
| `searchcontainer/timecontainer` (a `timeslider` kivágása) | (133,12)–(237,28) | 104 × 16 |
| `timeslider/docbounds` | (0,0)–(97,13) | 97 × 13 |
| `timeslider/sliderbase` (a vályú) | (0,3)–(97,10) | **97 × 7** |
| `timeslider/scaleslider` (a fogható sáv) | (5,0)–(93,13) | **88 × 13** |
| `timeslider/thumb` (a fogantyú) | (26,0)–(36,13) | **10 × 13** |

A `sliderbase` és a `thumb` **rajzolt** rétegek (658, illetve 653 bájt RLE),
nem tömör kitöltések.

*(A `searchoptions/#clip(scaleslider,timeslider): timecontainer` — (260,44)–(387,75),
127 × 31 — a **másik**, gazdagabb keresőbeállítás-panel saját idő-konténere;
az a #1398 hatóköre.)*

### ⚠️ A felirat az EREDETIBEN is félrevezet — ne „javítsuk ki"

A buboréksúgó „dátumtartomány szerinti" szűrést ígér, a vezérlő viszont
egyfogantyús kor-szűrő. Ez **az eredeti sajátja**, nem fordítási hiba: a
`searchcontainer.tre` 101–102. sora az angol forrásban is
`Filter by date range`. A projekt döntése szerint a felület pontosan úgy
nézzen ki, mint az eredeti (`docs/decisions/szerkeszto-bal-panel.md`), ezért
a magyar súgó **„Szűrés dátumtartomány szerint"** marad
(`referencia/i18n-hu/tooltips.xml` 786.).

*Bizonyítottsági fok: **megerősített** — a képlet két független helyen
azonos, a konstansok kiolvasva, a mértékegység-szabály utasításról
utasításra követve.*

Jegy: **#1830**.
