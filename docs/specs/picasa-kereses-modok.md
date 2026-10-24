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

## 2. A keresési sáv TELJES elemlistája: 6 élő, 13 kommentelt

`searchoptions.tre`. A `#` előtaggal kezdődő sorok **ki vannak kommentezve**,
tehát ezekből az erőforrásból nem épül fel vezérlő. Ez a felületi elemre
vonatkozó állítás; önmagában nem bizonyítja, hogy az adott művelethez nincs
aktív parancs vagy másik felületi út.

### Élő (6)

*Forrás: `searchoptions.tre:97` (`searchoptions/dupesearch`) · `searchoptions.tre:93` (`searchoptions/facesearch`) · `searchoptions.tre:74` (`searchoptions/label_search1`) — és további 5 elem ugyanott.*

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
### A `searchoptions` erőforrásban kikommentezett elemek (13)

`searchbase` · `boxleft` · `boxright` · `digicam` · **`similarrect`** ·
**`similarthumb`** · **`similarclip`** · **`loadsim`**(+label) ·
**`clearsim`**(+label) · **`savetoalbum`** · `label_searchall` ·
`label_searchnewer` · `label_search2` · `timecontainer`

**Két következmény, amit külön kell választani:**

1. A felsorolt hasonlósági **vezérlők nem jönnek létre a
   `searchoptions.tre` erőforrásból**, mert a soraik kommentek. Ez önmagában
   nem bizonyítja, hogy a funkció hiányzik a binárisból: a `Ctrl+F7` ág
   (`0x005e62e8`, `searchoptions/loadsim`, parancsazonosító `0x15`) a
   `0x005d8810` kezelőhöz jut; a törlés `Ctrl+F8`-on (`0x005e631d`,
   `searchoptions/clearsim`, azonosító `0x16`) aktív. A keresőút a
   `0x007ea000` függvényt hívja, majd az eredményt a
   `0x004ad4e0` („Similarity Search Results") állapotban jeleníti meg.
   ⚠️ **Tehát a Picasa 3.9-ben a mintaképes hasonlóság-keresés létezik, de a
   felsorolt panelvezérlők ebben az erőforrásban rejtettek.** A PicasaPy-ban
   is van egyképes hasonlóság-keresés (`app/similarity_controller.py`); a
   motor és a találati viselkedés összevetését a menüparancs-specifikáció
   60.4. szakasza tartalmazza.
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

*Forrás: `thumbui.tre:550` (`timeslider/scaleslider`).*

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

*Forrás: `searchcontainer.tre:92` (`searchcontainer/timecontainer`) · `searchcontainer.tre:89` (`searchcontainer/timecontainer_label`) · `thumbui.tre:550` (`timeslider/scaleslider`).*

A `string_xrefs` táblában **egyetlen** találat sincs sem a
`searchcontainer/timecontainer`, sem a `searchcontainer/timecontainer_label`
névre. Csak a `timeslider/scaleslider` szerepel a kódban. A két konténer-elem
tehát tisztán a felületleíró dolga: a `_label` a `.tre`-ben **csak a
buboréksúgót hordozza** (`SharedHandler searchcontainer/tip hottip`), a
`timecontainer` pedig a `timeslider` panel **kivágása**
(`layer:searchcontainer/clip(timeslider): timecontainer`).

### Geometria — a `respack.yt`-ből

*Forrás: `searchcontainer.tre:92` (`searchcontainer/timecontainer`) · `searchcontainer.tre:89` (`searchcontainer/timecontainer_label`) · `thumbui.tre:550` (`timeslider/scaleslider`) — és további 1 elem ugyanott.*

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

## ⭐ A HASONLÓSÁG-ADATBÁZIS: 380 bájt képenként, `CBlockFile`-ban (#447, 2026-09-03)

A `searchoptions/similarthumb` (a 2. szakasz elemlistája) mögötti
hasonlóság-keresésnek **saját, tartós adatbázisa** van. Ez a szakasz a
tárolását és az előállítás láncát írja le. Az itt következő #447-es
kutatási állapotot a #5742 (2026-10-24) lentebb pontosítja: a három
jellemző helper-szintű képlete megfejtve; a dekóder előtti színút és három
kitöltetlen rekordbájt továbbra is nyitott.

### Mit CSINÁL — a lánc

| lépés | cím | mit tesz |
|---|---|---|
| indítás | `0x007e95f0` (2569 b) | az egyetlen hívó |
| frissítő | `0x007ead60` (2888 b) | `CSimSearch::updating`; folyamatjelző: „Updating similarity database (will be fast next time)" |
| átméretezés | `0x00a3f490` → `Preferences\ResampleFilter2` | célméretek: 56×56, 32×32, 16×16 és 8×8; alapértelmezett szűrő: 6 (Lanczos-4) |
| jellemző-kinyerés | `0x007ea650` (1802 b) | négy méretenként két skalár; `+4` sorköz (×4 ⇒ 32 bites képpont), `+8` szélesség, `+0xc` magasság |
| kvantálás | `0x007eb8c0` | a 8×8-as kép 64 pixelét RGB565-re írja a rekord `+0x002` mezőjébe |
| hisztogram-normalizálás | `0x007ebd90` (446 b; `ret 4` a `0x007ebf4e` címen) | 216 floatból 216 bájtot ír a rekord `+0x082` mezőjébe |
| tárolás | `0x007eb685` → `0x006b75f0` | `CBlockFile::Write` (a keret: `pmp-database.md` 8.2) |
| visszaolvasás | `0x007eb22c` → `0x006b6a50` | `CBlockFile::Read` |

### A rekord mérete FIX: 380 bájt

```
0x007eb652   push 0x17c                        ; 380
0x007eb659   mov dword ptr [esp+0x74], 0x17c   ; a leíró méret-mezője
0x007eb661   call 0x00bf2350                   ; memcpy(dest, ebx, 0x17c)
```

és visszaolvasáskor:

```
0x007eb235   cmp eax, 0x17c
0x007eb23a   jne 0x007eb279                    ; ⇒ újraszámolás
```

⇒ **Nincs verziómező és nincs változó hossz.** Egy 380-tól eltérő méretű
bejegyzést a Picasa érvénytelennek tekint, és újraszámolja. Egy olvasónak
tehát elég a méretre szűrnie.

### A képpont-kvantálás: RGB565, BGRA sorrendből

```
0x007eb8dc   movzx eax, byte ptr [edi + 2]     ; R
0x007eb8e0   movzx ebx, byte ptr [edi + 1]     ; G
0x007eb8e4   shr al, 3                         ; R → 5 bit
0x007eb8eb   shl ax, 6
0x007eb8ef   shr bl, 2                         ; G → 6 bit
0x007eb8f6   or  ax, bx
0x007eb8f9   movzx ebx, byte ptr [edi]         ; B
0x007eb8fc   shl ax, 5
0x007eb900   shr bl, 3                         ; B → 5 bit
```

⇒ `index = (R>>3) << 11 | (G>>2) << 5 | (B>>3)` — **RGB565**, 65 536 rekesz.
A bájtsorrend **BGRA** (`+0`=B, `+1`=G, `+2`=R), egyezően a `respack.yt`
rétegeivel (`picasa-respack-format.md`).

### ⚠️ Helyesbítés a 66. körből: a `0x007ea650` NEM a vektor építője

A szakasz első kiadása a `0x007ea650`-t „jellemző-kinyerésként" írta le,
mintha az adná a vektort. **A hívási helyek megcáfolják.** A függvény
**három** paramétert kap — `(kép-leíró, kimenet1, kimenet2)` —, és
**két skalárt** ad vissza hívásonként:

| hívás | cím | kép-leíró | kimenet1 | kimenet2 |
|---|---|---|---|---|
| 1. | `0x007eb50e` | `esp+0x74` | `esp+0xAC` | `esp+0xB4` |
| 2. | `0x007eb52e` | `esp+0x130` | `esp+0xB0` | `esp+0xA0` |
| 3. | `0x007eb54e` | `esp+0x108` | `esp+0xA8` | `esp+0xA4` |
| 4. | `0x007eb56b` | `esp+0xE0` | `esp+0x9C` | `esp+0x70` |

⇒ **Négy KÜLÖNBÖZŐ képre** fut (a négy átméretezés eredményére), és
összesen **nyolc skalárt** ad. Hogy ez a nyolc hova kerül, az alábbi
szakasz mondja meg.

### A memóriabeli vektor 216 elem — a TÁROLT rekord kisebb

A normalizáló (`0x007ebd90`) hurka:

| cím | mit ad |
|---|---|
| `0x007ebd9f` | `lea ecx, [ebx + 8]` — a kezdőpont |
| `0x007ebda2` | `mov edx, 0x24` — **36 iteráció** |
| `0x007ebdb0`…`0x007ebe4f` | iterációnként **hat** `float`: `[ecx-8]`, `[ecx-4]`, `[ecx]`, `[ecx+4]`, `[ecx+8]`, `[ecx+0xc]` |
| `0x007ebe6f` | `add ecx, 0x18` — a lépés 24 bájt = 6 × `float` |

⇒ **36 × 6 = 216 `float` = 864 bájt** a memóriában, szemben a tárolt
**380** bájttal. A 216 float normalizálója a `+0x082` mezőbe 216 bájtot
ír; a kvantálás pontos képlete a #5742 alábbi szakaszában áll.

### A találatok helye

| mi | cím | érték |
|---|---|---|
| eredmény-album | `0x004ad4e0` | „Similarity Search Results" / `CAlbumState::SimSearchResults` |
| felületi elem | `0x005d8280`, `0x005d8810` | `searchoptions/similarthumb` |

### Az akkori nyitott állapot (#447, 2026-09-03; #5742 feloldotta)

Akkor még **NEM** volt ismert, hogyan lesz a 216 memóriabeli `float`
értékből a 380 bájtos rekord. A #5742 alábbi szakasza azonosította a
RGB565 bélyegképet, a 216 bájtos normalizált hisztogramot és a nyolc
skalárt. A rekord három további bájtjának jelentése továbbra is nyitott.

*Bizonyítottsági fok: a **tárolás, a méret, a kvantálás és a lánc
megerősített** (címenként kiolvasva); a **vektor jelentése akkor NINCS MEG (a státuszt a #5742 alábbi szakasza felülírja)**.*

### Melléklelet: a `makemoviecache.db` blobja ezen a hívási helyen 4 bájt

A `CBlockFile` harmadik ismert fogyasztója a filmkészítő gyorstára
(`0x0080f830`, `makemoviecache\` / `makemoviecache.db`). Az egyetlen ott
található író hívás leírója **4 bájtos** blobot ad át
(`0x0080f9a5`: `mov dword ptr [esp+0x10], 4`). Hogy ez mit jelöl, **NINCS
MEG**; más írási helyet ehhez a fájlhoz nem találtam.

## ⭐ A 380 bájtos rekord SZERKEZETE — két rész, pontos határral (#447, 2026-09-03)

Az előző kör a rekord **méretét** mérte ki. Ez a kör a **belső határát** — a
rekordot összeállító kód a `0x007eb5c4`–`0x007eb5f6` szakaszon áll, és
maradék nélkül megmagyarázza a 380 bájtot.

### Az összeállítás

```
0x007eb5c4   fld dword ptr [esp + 0xac]     ; az első skalár az FPU-veremre
0x007eb5cb   mov ecx, 0x5f                  ; 95
0x007eb5d0   lea esi, [esp + 0x264]         ; forrás: a munkapuffer
0x007eb5d7   mov edi, ebx                   ; cél: a rekord
0x007eb5d9   rep movsd                      ; 95 dword = PONTOSAN 380 bájt
0x007eb5db   fstp dword ptr [ebx + 0x15c]   ; …majd a nyolc skalár FELÜLÍRJA a végét
```

⇒ A rekord **egy darabban** másolódik a `esp+0x264`-nél álló munkapufferből
(`rep movsd`, `ecx = 0x5F` = 95 dword = 380 bájt), és **utána** nyolc
`float`-tárolás felülírja az utolsó 32 bájtot.

### A rekord két része

```
+0x000 … +0x15B   348 bájt (87 dword)  — a munkapufferből másolt rész
+0x15C … +0x17B    32 bájt  (8 float)  — a négy 0x007ea650-hívás nyolc skalárja
                                          ⇒ a rekord vége 0x17C = 380
```

### A nyolc skalár — teljes, ZÁRT megfeleltetés

| rekord-eltolás | forrás | melyik hívásból |
|---|---|---|
| `+0x15C` | `esp+0xAC` | 1. hívás, kimenet1 |
| `+0x160` | `esp+0xB4` | 1. hívás, kimenet2 |
| `+0x164` | `esp+0xB0` | 2. hívás, kimenet1 |
| `+0x168` | `esp+0xA0` | 2. hívás, kimenet2 |
| `+0x16C` | `esp+0xA8` | 3. hívás, kimenet1 |
| `+0x170` | `esp+0xA4` | 3. hívás, kimenet2 |
| `+0x174` | `esp+0x9C` | 4. hívás, kimenet1 |
| `+0x178` | `esp+0x70` | 4. hívás, kimenet2 |

**A megfeleltetés zárt:** a négy hívás nyolc kimeneti címe **pontosan
egyszer** szerepel a nyolc tárolás forrásaként, és a sorrend a hívási
sorrendet követi. Ez egyben a hívási hely-táblát is hitelesíti.

⚠️ *A `+0x178` forrása a rövid `fld dword ptr [esp+0x70]` kódolású
(`d9 44 24 70`), nem a hosszú `d9 84 24 …` alak. Egy csak a hosszú alakot
ismerő olvasó itt megismételné az előző forrást — a kettősség maga a
jelzés, hogy a dekódolás hiányos.*

### Mi maradt nyitva — SZŰKÜLT

Nem a 380 bájt, hanem a **348 bájtos első rész**. Amit tudunk róla:

- a `esp+0x264`-nél álló munkapufferből származik;
- a puffert az **RGB565-kvantáló** tölti (`0x007eb8c0`), amelyet
  `ecx = esp+0xE4` objektummal, `esp+0x266` paraméterrel hívnak, és előtte
  `[esp+0x268] = 1` állítódik be (`0x007eb5a3`);
- a rekord **első két bájtja** (`+0x000`, `+0x001`) tehát a
  `esp+0x264`…`esp+0x265` tartományból jön, azaz **a kvantáló paraméterén
  KÍVÜLRŐL** — ez a két bájt külön kérdés.

⛔ **Mintafájl továbbra sincs** (a tulajdonos sosem futtatta a funkciót),
tehát adatoldali ellenőrzés nincs. A következő lépés: a `0x007eb8c0`
(549 b) kimeneti elrendezésének kiolvasása.

*Bizonyítottsági fok: a **rekord kétrészes szerkezete és a nyolc skalár
megfeleltetése megerősített** (a másoló és a nyolc tárolás címről címre
kiolvasva, a megfeleltetés zárt); a **348 bájtos rész jelentése NINCS
MEG**.*

## ⭐ A rekord eleje: 8×8 RGB565 BÉLYEGKÉP (#447, 2026-09-03)

Az előző kör a rekordot két részre bontotta, és nyitva hagyta a 348 bájtos
elejét. Ebből most **130 bájt megvan**, és a rekord kezdete is **rögzítve**.

### A kvantáló kimenete: 8 sor × 8 képpont

A `0x007eb8c0` (549 b) egy **kibontott** kettős ciklus. Soronként **nyolc**
`uint16`-ot ír, majd 16 bájtot lép:

| cím | mit tesz |
|---|---|
| `0x007eb90a` | `mov word ptr [esi-4], ax` |
| `0x007eb94a` | `mov word ptr [esi-2], ax` |
| `0x007eb98a` | `mov word ptr [esi], ax` |
| `0x007eb9c9` | `mov word ptr [esi+2], ax` |
| `0x007eba09` | `mov word ptr [esi+4], ax` |
| `0x007eba49` | `mov word ptr [esi+6], ax` |
| `0x007eba89` | `mov word ptr [esi+8], ax` |
| `0x007ebac9` | `mov word ptr [esi+10], ax` |
| `0x007ebacd` | `add edx, 1` |
| `0x007ebad0` | `add esi, 16` |
| `0x007ebad3` | `cmp edx, 8` |
| `0x007ebad6` | `jb 0x007eb8d0` |

⇒ **8 sor × 8 érték × 2 bájt = 128 bájt.** A képpontok a bemeneti kép
egy-egy sorának **első nyolc** eleméből jönnek
(`edi = [ecx+0x10] + sor·[ecx+4]·4`, majd `+0`, `+4`, `+8`, …), az érték
pedig a már leírt **RGB565** kód (`0x007eb8e4`–`0x007eb900`).

⇒ **A rekord elején egy 8×8-as, RGB565-be kvantált bélyegkép áll.**
Ez a Picasa hasonlósági ujjlenyomatának első fele.

### A rekord KEZDETE rögzítve

Mindkét közbenső hívás **callee-cleanup** (`ret 4`), tehát a hívó verme
visszaáll, és a `rep movsd` forráscíme ugyanabban a keretben van, mint a
kvantáló előtti jelzőbájt:

| cím | mit ad |
|---|---|
| `0x007eb8c0` vége | `c2 04 00` = `ret 4` |
| `0x007ebf4e` | `ret 4` — a normalizáló vége |
| `0x007eb5a3` | `mov byte ptr [esp+0x268], 1` — egy `push` UTÁN, azaz a keretben `+0x264` |
| `0x007eb59b` | a kvantáló paramétere a keretben `+0x266` |
| `0x007eb5d0` | `lea esi, [esp+0x264]` — a `rep movsd` forrása |

⇒ A `+0x264` mindhárom helyen **ugyanaz a cím**, tehát:

```
+0x000        uint8   = 1          ; jelzőbájt (0x007eb5a3 állítja be)
+0x001        —                    ; egyik lépés sem írja
+0x002 …+0x081  64 × uint16        ; 8×8 RGB565 bélyegkép (128 bájt)
+0x082 …+0x15B  218 bájt           ; ISMERETLEN (ld. lentebb)
+0x15C …+0x17B   8 × float         ; a négy 0x007ea650-hívás skalárjai
                                   ; ⇒ 0x17C = 380
```

### A 218 bájtos rész — amit tudunk róla

A normalizáló hívása előtt (`0x007eb5b8`) `lea edi, [esp+0x2ea]` fut, ami
ugyanabban a keretben **pontosan `+0x2E6` = a rekord `+0x082`** — azaz az
ismeretlen tartomány **kezdete**. Az `edi` tehát a normalizáló
**regiszter-paramétere**, és a függvény a végén `mov eax, edi`-vel
vissza is adja.

⛔ **HELYESBÍTVE (2026-09-03, ld. a következő szakaszt): a normalizáló
IGENIS ide ír.** A szakasz első kiadása azt állította, hogy „egyetlen
`edi`-célú írás sincs" — ez **téves** volt: a mintaillesztéses keresésem
csak a közvetlen `[edi+eltolás]` alakokat ismerte, az írás viszont
**SIB-alakú** (`mov byte ptr [esi + edi - 1], al`, `0x007ebf39`). A teljes
törzs diszasszemblálása megtalálta.

### Melléklelet: a függvényindex mérete itt RÖVID

A `functions` tábla a normalizálót **442** bájtosnak mondja, de a `ret 4`
a **446.** bájtnál áll (`0x007ebf4e`). Aki a törzset az indexbeli méretre
vágja, **levágja a függvény végét** — épp azt a részt, ahol a skálatényező
kiszámolása történik.

### Akkor nyitva maradt (#447, 2026-09-03; #5742 feloldotta)

A `+0x082`–`+0x15B` 218 bájtos tartományának felosztása akkor még nem
volt ismert. Az `edi` célmutató és a memóriabeli 216 elemű `float`-vektor
mérete ismert volt, de a „216 bájt + 2 bájt” felosztást nem mértük ki.
A #5742 azonosította a `+0x082`–`+0x159` 216 normalizált bájtot; a három
maradék bájt jelentése továbbra is nyitott.

*Történeti bizonyítottsági fok (2026-09-03): a 218 bájt tartalma akkor
NINCS MEG volt; a #5742 a 216 bájtot feloldotta.*
## ⭐ A 216 BÁJTOS vektor — a rekord közepe megfejtve (#447, 2026-09-03)

Az előző kör a rekord `+0x082`-től induló 218 bájtját nyitva hagyta, és
tévesen zárta ki a normalizálót íróként. **A normalizáló írja** — 216
bájtot, elemenként egyet.

### A hurok

```
0x007ebeb2   fld dword ptr [ebx + esi*4]   ; a vektor i-edik float eleme
0x007ebeb9   call 0x0049fe60               ; elemenkénti átalakítás (ld. lentebb)
0x007ebebe   fmul dword ptr [esp + 0xc]    ; szorzás a skálatényezővel
0x007ebee2   fcom qword ptr [0x00cf39d0]   ; összevetés 255,0-val
0x007ebf04   fld dword ptr [0x00cf3a00]    ; a vágott érték: 255,0
0x007ebf0e   add esi, 1
0x007ebf1e   or eax, 0xc00                 ; FPU-kerekítés → CSONKÍTÁS
0x007ebf2d   fldcw word ptr [esp + 0xc]
0x007ebf31   fistp dword ptr [esp + 0xc]   ; float → egész, csonkítva
0x007ebf35   mov al, byte ptr [esp + 0xc]  ; az alsó bájt
0x007ebf39   mov byte ptr [esi + edi - 1], al   ; ⇐ IDE ír
0x007ebf23   cmp esi, 0xd8                 ; 216
0x007ebf41   jl 0x007ebeb2
```

⇒ **216 iteráció, elemenként egy bájt**, `edi`-től kezdve — és `edi` a
hívónál (`0x007eb5b8`) pontosan a rekord **`+0x082`**-je.

### A skálatényező és a védelmek

| cím | konstans | szerep |
|---|---|---|
| `0x00cf3db0` | **0,001** (`double`) | ha a 216 elem maximuma ennél nem nagyobb… |
| `0x00c7999c` | **0,001** (`float`) | …akkor ezt használja helyette (nulla-védelem) |
| `0x00cf39d0` | **255,0** (`double`) | a felső vágás összehasonlító értéke |
| `0x00cf3a00` | **255,0** (`float`) | a vágott érték |
| `0x007ebf1e` | `or eax, 0xC00` | a kerekítés **csonkításra** állítva |

### ⛔ Akkor nyitott volt: az elemenkénti átalakítás (#5742 feloldotta)

A `0x0049fe60` (29 b) csak burkoló: `fld [ebp+8]` → `call 0x00c0b310`
(20 b) → az pedig `call 0x00c14398`. Ez a lánc egy **CRT-matematikai
függvényhez** vezetett; a bájtérték képlete akkor `NINCS MEG` volt. A
#5742 alábbi új szakasza az átalakítást és a skalárképleteket is rögzíti.

### A rekord MAI állása — 380-ból 377 elszámolva

```
+0x000        uint8 = 1        ; jelzőbájt (0x007eb5a3)
+0x001        1 bájt           ; a tartalma és írója is NINCS MEG (#5742)
+0x002 …+0x081  64 × uint16    ; 8×8 RGB565 bélyegkép
+0x082 …+0x159  216 × uint8    ; a normalizált vektor, csonkítva, 255-re vágva
+0x15A …+0x15B  2 bájt         ; ISMERETLEN
+0x15C …+0x17B   8 × float     ; a négy 0x007ea650-hívás skalárjai
                               ; ⇒ 0x17C = 380
```

### ⚠️ Módszertani helyesbítés — MÁSODSZOR ugyanaz a csapda

Az előző kör azért zárta ki tévesen a normalizálót, mert a keresés
**mintaillesztéses** volt, és csak a közvetlen `[edi+eltolás]` alakokat
ismerte. A tényleges írás **SIB-alakú** (`88 44 3e ff` =
`mov byte ptr [esi + edi - 1], al`), ahol az `edi` **index**, nem bázis.

Ez ugyanaz a hiba, mint a 66. körben (a rövid `fld` kódolás kimaradása).
⇒ **Regiszter-használatot ne mintaillesztéssel keress.** Diszasszembláld a
TELJES törzset, és a kapott szövegben keress a regiszter nevére. Ha a
törzs hosszabb, mint amennyit a dekódoló egy hívásban ad, **darabold**.

*Történeti bizonyítottsági fok (2026-09-03): a `+0x082` normalizálás és az
átalakítás képlete akkor nyitott volt. A #5742 ezt feloldotta; a `+0x001`,
`+0x15A`, `+0x15B` bájtok továbbra is NINCS MEG.*

## ⭐ #5742 — a három hasonlósági-jellemző előállítása (#5742, 2026-10-24)

Ez a szakasz a #447 korábbi „NINCS MEG” megállapításait felülírja a három
jellemző helper-szintű előállítására. A rekord `+0x001`, `+0x15A` és `+0x15B` bájtjának
jelentése továbbra sincs megállapítva.

### Rekordíró és átméretezett bemenetek

A `CSimSearch` frissítője `0x007ead60`; közvetlen hívása a
`0x007e95f0` függvényből, a `0x007e9a3a` címen van. A writer a `0x17c`
(380) méretet a `0x007eb652` és `0x007eb659` címeken adja meg, majd
`0x007eb661`-nél másol. A mezőírók: a 8×8 kvantáló `0x007eb8c0`, a
hisztogram-normalizáló `0x007ebd90`, a nyolc skalárt előállító
`0x007ea650` négy hívása. A teljes `.text`-pásztázás `paszta.py`-val
egy közvetlen `call 0x007ead60`-at talált, a hívás helye `0x007e9a3a`.
Az eltérés-alapú találatlista sok veremeltolás-egyezést is ad, ezért
abból nem következtettem más mezőíró hiányára; az alábbi írásokat a
célmutató- és híváslánc követésével azonosítottam.

A frissítő a 56×56, 32×32, 16×16 és 8×8 célméretű képleírókat készíti
el (`0x007eb431`, `0x007eb472`, `0x007eb4b3`, `0x007eb4f4`). A
`0x00a3f490` a `Preferences\ResampleFilter2` értékét olvassa; a bináris
alapértéke 6 (`0x00a3f51c`), és a 6-os ág a `0x00a3feed` címen a Lanczos-4
szűrőt választja. A `0x00a42c20` nagy kicsinyítéskor 2×2-es box
előfelezést is végez (`0x00a43230`), mielőtt a kiválasztott szűrővel
befejezi az átméretezést. A beállítás felhasználói értéke felülírhatja a
6-os alapértéket.

**Színtér-határ:** a három jellemző függvénye három bájtos csatornákat
olvas; a kvantáló szerint `+0`=B, `+1`=G, `+2`=R, az alfát nem olvassa.
Ezekben a függvényekben nincs ICC-, gamma-, HSV- vagy YUV-átalakítás.
Ez csak a bemenő képleíró csatornáinak kezelését bizonyítja; hogy a
dekóder a leíró elkészítése előtt alkalmaz-e ICC/gamma-konverziót, nyitott.

### 1. A `+0x002` mező: 64 RGB565 képpont

A `0x007eb8c0` a 8×8-as leíró 64 képpontját alakítja át, és a rekord
`+0x002` címétől ír. Bemeneti byte-sorrend: B,G,R,(alpha); az alpha
kimarad. Minden csatorna alsó bitjeit egyszerű eltolás dobja el, kerekítés
nincs:

```text
pixel = ((R >> 3) << 11) | ((G >> 2) << 5) | (B >> 3)
```

A képpontok sorfolytonosan kerülnek a 64 darab 16 bites helyre. A
rekordot visszaolvasó `0x007ebb1b`–`0x007ebb3d` kód külön bontja ki az
5/6/5 bites R/G/B mezőket; ez a writer kvantálásától független
fogyasztói út.

### 2. A `+0x082` mező: 6×6×6 színhisztogram és bájtos normalizálás

A `0x007ec210` a 56×56-as leíró mind a 3136 pixelét feldolgozza.
Csatornánkénti súlyozásból 216 darab float32 binszámláló készül. A
lapos index a leíró byte-sorrendjében:

```text
t_k = 5 * C_k
i_k = t_k >> 8
f_k = t_k & 255
a_k = 256 - f_k
j = 36 * i_2 + 6 * i_1 + i_0
```

ahol `C_0`=B, `C_1`=G, `C_2`=R, `i_k` a 0…4 alsó bin, `f_k` a
maradék. A `0x007ec280` rutin egy pixelből az alábbi súlyokat írja
(`A=a_2`, `B=a_1`, `C=a_0`, `u=f_2`, `v=f_1`, `w=f_0`):

| célbin | hozzáadott súly |
|---|---|
| `j` | `A*B*C` |
| `j+1` | `A*B*w` |
| `j+6` | `A*v*C` |
| `j+7` | `A*v*w` |
| `j+36` | előbb `u*B*C`, majd külön hozzáadásként `u*v*C` |
| `j+37` | előbb `u*B*w`, majd külön hozzáadásként `u*v*w` |

A felső `i_2` ág nem léptet `+36`-ról `+42`-re, illetve `+37`-ről
`+43`-ra: a két-két súly ugyanabba a két binbe adódik össze. Nincs
`256^3`-mal történő osztás. A két külön hozzáadást a bináris két
utasítássorozatban végzi; bitpontos utánzáshoz a sorrend számít.

A `0x007ebd90` a maximumot keresi. Ha `max <= 0.001`, a skálázáshoz
`0.001`-et használ (`0x00cf3db0`, double összehasonlítás; `0x00c7999c`,
float pótlóérték). Egyébként `scale = float32(255.99 / sqrt(max))`
(`0x00cf42f8` a double 255.99 konstans). Minden kimeneti byte:

```text
out[i] = clamp(0, 255, trunc(sqrt(hist[i]) * scale))
```

A négyzetgyök CRT-útja `0x00c0b32d` (`fsqrt`), a konverzió `0x00c29990`;
a kerekítési mód csonkítás (`0x007ebf1e`). A 216 bájt a rekord
`+0x082`–`+0x159` tartományába kerül. A függvény tényleges vége a
`0x007ebf4e` címen levő `ret 4`; ez 446 bájt, nem az index 442 bájtos
mérete.

### 3. A `+0x15c` mező: négy felbontás vízszintes és függőleges éle

A `0x007ea650` minden leíróhoz egy X és egy Y floatot ír vissza. A writer
az eredményeket a `0x007eb5db` (`+0x15c`), `0x007eb5e8` (`+0x160`),
`0x007eb5f5` (`+0x164`), `0x007eb602` (`+0x168`), `0x007eb60f` (`+0x16c`),
`0x007eb61c` (`+0x170`), `0x007eb629` (`+0x174`) és `0x007eb633`
(`+0x178`) címeken tárolja. A `W×H` leíró és három csatornája esetén a
belső második különbség négyzete:

```text
dx(x,y,c) = 2*C(x,y,c) - C(x-1,y,c) - C(x+1,y,c)
dy(x,y,c) = 2*C(x,y,c) - C(x,y-1,c) - C(x,y+1,c)
Sx = sum(dx(x,y,c)^2), x=1..W-2, y=0..H-1, c=0..2
Sy = sum(dy(x,y,c)^2), x=0..W-1, y=1..H-2, c=0..2
X = sqrt(Sx / ((W-2) * H * 786432))
Y = sqrt(Sy / (W * (H-2) * 786432))
```

A 786432 double konstans a `0x00cf4300` címen van (`3 * 512^2`). A
függvény a kiszámolt értékeket 32 bites floatként adja át. A rekord
sorrendje:

| rekordeltolás | leíró | érték |
|---|---:|---|
| `+0x15c`, `+0x160` | 56×56 | X, Y |
| `+0x164`, `+0x168` | 32×32 | X, Y |
| `+0x16c`, `+0x170` | 16×16 | X, Y |
| `+0x174`, `+0x178` | 8×8 | X, Y |

### Független ellenőrzés és cáfoló próba

A statikus út a `0x007ead60` teljes írófüggvényétől követte a leírókat,
az íróhívásokat, a mezőcímeket és a képletek utasításait. A második út
az eredeti EXE közvetlen helper-hívása volt QEMU-ban, kézzel épített
kép-leírókkal (`hb.py`); az alábbi értékek pontos mérések.

| QEMU-mérőadat | mért eredmény |
|---|---|
| 1×1 pixel, `(C0,C1,C2,alpha)=(100,120,140,255)`, `0x007ec210` nyers hisztogram | nem nulla: `(85,137088)`, `(86,2787456)`, `(91,71808)`, `(92,1460096)`, `(121,577536)`, `(122,11743232)`; összeg `16777216 = 256^3` |
| ugyanaz a hisztogram a `0x007ebd90` normalizálása után | nem nulla: `(85,27)`, `(86,124)`, `(91,20)`, `(92,90)`, `(121,56)`, `(122,255)` |
| 5×5 pixel, `C0=x²`, `C1=y²`, `C2=x²+y²`, alpha=255, `0x007ea650` | `Sx=Sy=120`; X=Y=`0.0031894398853182793` |

A cáfoló próba a kézenfekvő teljes 8-szomszédos trilineáris hisztogram
volt: abból a mérőpixelnél a `j+42` és `j+43` binnek is nemnullának
kellett volna lennie. A bináris felső ágak azonban a `j+36`/`j+37`
címeket írják újra, és QEMU-ban pontosan hat bin volt nemnulla. A
mért binsúlyok összege `256^3`; így a mérési adat maga is konzisztens a
hat célbines súlyozással. A cáfoló ellenőrzése ugyanazon eredeti
helper futtatásával történt, nem a statikus kódból számoltuk vissza.

A két út a helper-szintű képleteknél egyezik. Ezért azok
**megerősítettek**; a teljes dekóder→feature színút **feltételes**, mert
a forrásleíró előtti profilkezelés nincs lezárva. A QEMU-mérések
szintetikus leírókat használtak, tehát nem igazolják a teljes Picasa
betöltési út viselkedését. A `+0x001`, `+0x15A`, `+0x15B` bájtok
tartalma és írója ebben a körben **NINCS MEG**.

**Nyitott — színút:** `Ghidra-kör kell: 0x006b67c0 — a forrásleíró létrehozása előtt melyik dekóder-/profilút fut, és módosítja-e a három színcsatornát ICC- vagy gamma-konverzió? [blokkoló]` A már létező Ghidra-kimenetek a `0x006b67c0` hívását/xrefjét mutatják, a függvény törzsét és a decoder/profile műveleteket nem.

**Nyitott — három bájt:** kövesd az `0x007ead60` rekordpufferének inicializálását a `0x007eb5d9` 95 dwordos másolásáig, majd ellenőrizd a `+0x001`, `+0x15A`, `+0x15B` fogyasztóit; a jelenlegi writer- és fogyasztónyomok nem állapítják meg ezek értékét vagy jelentését.
