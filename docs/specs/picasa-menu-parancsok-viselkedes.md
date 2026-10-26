# A menüparancsok VISELKEDÉSE — a #1434 feltárása

*2026-08-25. A #1397 leltár a **hiányzó** tételeket fedte le; ez a lap a
„nálunk megvan"-ként jelölt, de **viselkedésében soha nem vizsgált**
parancsokról szól. Jegy: **#1434** (38 érdemi tétel).*

> **Mérés:** a 161 `ID_*` menüparancsból **54** egyetlen spec-lapon sem
> szerepelt. Ebből **16 triviális** (vágólap, Kilépés, Súgó-hivatkozások),
> **38 érdemi**. Ez a lap az utóbbiakat gyűjti, adagonként.

## 1. ⭐ A LEGGYORSABB ÚT: a `.fen` párbeszédleírók

A `Picasa3/runtime/` alatt **46** `.fen` fájl van, és a legtöbb hiányzó
párbeszédhez **van** leíró. Egy `.fen` **egy lépésben** adja a teljes
párbeszédet: vezérlők, feliratok, elrendezés, gombok.

| parancs | `.fen` |
|---|---|
| `ID_TOOLS_ADJUST_TIMESTAMP` | `offsettime` |
| `ID_MOVE_DATABASE` | `move_database` + `moving_database` |
| `ID_WRITE_XMP_FACES` | `write_all_facetags` |
| `ID_PICTURE_PROPERTIES` | `imageproperties` |
| `ID_FILE_RENAME` | `rename` |
| `ID_TOOLS_OPTIONS` | `options` |
| `ID_TOOLS_CONTACTMGR` | `contactmgr` |
| `ID_FILE_EXPORTASWEBPAGE` | `webexport` |
| `ID_FILE_EPROCESS` | `orderprintsprefs` |
| `ID_HELP_ABOUT` · `ID_HELP_TERMS` | `about` · `eula` |

## 2. A vágólap-parancsok — az effektus NEM a rendszer-vágólapon megy

A Picasa használja a Windows-vágólapot (`OpenClipboard` 6, `SetClipboardData`
2, `GetClipboardData` 2), de **egyetlen** egyedi formátumot regisztrál
(`RegisterClipboardFormatA`, 1 hívó: `0x005378e0`), és az a **héj-formátumok**
készlete (`Shell IDList Array`, `FileGroupDescriptor`, `FileContents`, …) —
vagyis a **húzás-ejtésé**.

⇒ **„Az összes effektus másolása" belső pufferbe dolgozik.** Két
Picasa-példány között nem működik; más program nem látja.

A **szöveg**-beillesztés viszont a rendszer-vágólapról jön, **lecseréli** a
feliratot, megerősítést kér (`CTextEditNode::confirm`, gomb: `Replace`), és
kimondja: **„(Ez a művelet nem vonható vissza)"** (`IDS_REPLACE_CAPTION`).

## 3. „Dátum és idő beállítása” — KÉT mód; feltételes EXIF-írás

`offsettime.fen`: bélyegkép-előnézet · „Current photo date" (dátum+idő) ·
„New photo date" (dátum+idő) · **rádiócsoport**:

- `relative` — *Adjust all photo dates by the amount* (**eltolás**)
- `absolute` — *Set all photos to the same date and time* (**abszolút**)

Több képre megy: az ablakcím szó szerint **`Adjust Photo Date - %d items`**
(`0x00cb40ac`, xref: `0x0077c7c0`); a futásjelzés **`Setting photo dates`**
(`0x00cb4120`, xref: `0x0077cfd0`, `AdjustTimeThread::SettingDates`).

### A worker és a forrásfájl írása (2026-10-08, #4646)

A két dátumfeldolgozó út (`0x00490580`, `0x00490c10`) egyaránt a `0x37`
metaadat-tulajdonságot állítja be (`0x004906f7`/`0x004906fe` és
`0x00490d3c`/`0x00490d43`). A tulajdonságtábla szerint a `0x37` az EXIF
`DateTimeOriginal` (`0x9003`), ld. `picasa-metaadat-tulajdonsagok.md`, §3.
Ezután mindkét worker a `[esp+0xac] == 2` feltételt vizsgálja
(`0x0049070a`, `0x00490d4f`). A `[esp+0xac]` a worker keretében `0`-ról indul
(`0x00490602`, `0x00490c92`), és közvetlen írás nincs rá más helyen. A `2`
a `[esp+0x94]`-es kimeneti szerkezet `+0x18` mezőjéből jöhet: a `0x00490cc6`–
`0x00490cd2` hívás a `[obj+0x48]` objektum vtable-jának `+0xc4` metódusát
hívja ezzel a címmel. Ez a metódus nincs azonosítva, ezért a `2` jelentése
**nyitott**. Ha teljesül, meghívja a `0x009ed330` íróutat;
annak nullától eltérő visszatérése a fallback nélküli worker-ágra visz
(`0x00490725`–`0x00490736`, `0x00490d69`–`0x00490d7b`), de a visszatérési
kódok jelentését a disassembly nem nevezi meg. A `2` érték C++-oldali
jelentése szintén nincs meg; ezért itt a nyers feltétel rögzíthető.

Az `0x009ed330` hívja a `0x009eb290`-et, amelynek tempfájlos íróágán a
kiválasztott
képfájl útvonalát olvassa, `.tmp` fájlt ír (`"r+b"`/`"wb"`,
`0x009eb3e0`, `0x009eb5c8`), majd a `0x00994400` útján lecseréli a forrásfájlt
(`0x009eb70b`). A worker által előzőleg beállított `0x37` így a forrásfájl
EXIF `DateTimeOriginal` mezőjébe kerül.

A sikeres csere a fájlrendszer-időket is kezeli. A `0x009eb290` előbb
elmenti mindhárom időt (`0x00ab3320` → `0x00ab3350` → `GetFileTime`). Ha a
metaadat-objektumban olvasható és dátummá alakítható a `0x1c` tulajdonság
(EXIF `DateTime`, `0x0132`; `0x009eb34b`–`0x009eb37d`), a `0x00ab35e0` az
eredeti `FILETIME`-szerkezetben a hozzáférési és utolsó módosítási idő mezőket
erre az értékre állítja (`or [edi+0x18], 6`, `+8`, `+0x10`); a
létrehozási idő mezője érintetlen marad. A `0x00994400` fájlcsere-segéd
sikeres visszatérése után a worker a `0x009eb4af` ágra jut, amely a
`0x009eb4c1` címen hívja a `0x00ab34d0`-t; a cserehibás ág is megpróbálja ezt
a visszaírást (`0x009eb738`). Ha a `DateTime` hiányzik vagy nem alakítható
dátummá, a szerkezetben mindhárom eredeti idő marad, így a kód az eredeti
hármast próbálja visszaírni. A `0x00ab35e0`-ban a két időkonverziós API
visszatérését, a `0x00ab34d0`-ban pedig a `SetFileTime` eredményét nem kezeli
helyreállítással; a tényleges fájlrendszer-állapot ezért a fájlcsere és az
API-hívások sikerétől is függ.

Ha a `[esp+0xac] == 2` feltétel nem teljesül, vagy a `0x009ed330` nullát ad
vissza, a worker a fallback-ágra jut: az első workerben a `0x004908cd`-n át,
a másodikban a `0x00490f0d`-n át a `0x00992780` hívásához (`0x00490900`,
`0x00490f40`); a `0x004908cd`–`0x00490900` közti átmenet nincs végig követve. Ez a segéd a `SetFileTime`-ot hívja
(`0x009927f9`, import-slot `0xc40474`; a korábbi `0x0092234c` cím téves volt:
a `.text` közepébe esik, nem hívás). A hívóhelyek `push 0`-val adják át a
jelzőt (`bl` = 0), így a `SetFileTime` argumentumai: létrehozási idő = az új
dátum (`SystemTimeToFileTime`, `0x009927e3`), hozzáférési és utolsó írási idő
= NULL (`neg bl` / `sbb` / `and` maszk, `0x009927e9`–`0x009927f7`). Ebben az ágban tehát a fájl létrehozási idejét
a beállított új dátumra állítja; a hozzáférési és utolsó módosítási időt ez a
hívás nem adja át, így azokat nem módosítja.

⭐ **2026-10-11 (#4591) — a nem-EXIF ág a katalógust is írja.** A
`[esp+0xac]` a `thumbindex`-rekord másolatának `+0x18` mezője, a **fájltípus**
(a másoló: `IThumbDB` `+0xc4` → `0x0043c3f0` → `0x004edf60`); a `== 2` tehát
„JPEG". Minden más típusnál (videó: 8/10/11) a `SetFileTime` mellett a
`0x004ef3c0` (eltolás) ill. `0x004ef5a0` (abszolút) a rekord **1. FILETIME-ját**
is átírja és piszkosnak jelöli. Részletek és mérés: `pmp-database.md` 15.1–15.2.

A teljes `.text` indexfüggetlen pásztázása (`paszta.py`,
`memoria_kapu()`-val indítva; 2 884 879 utasítás) a `.picasa.ini`-re mutató
adat-hivatkozásokat a program más részein találta, nem a fenti worker/EXIF-író
hívásláncban. E művelet nem ír `.picasa.ini`-kulcsot. Ez nem állítás a Picasa
program egészének `.picasa.ini`-írásairól.

### PicasaPy tárolási döntése (#4332)

A dátummódosító a kijelölt fotók dátumát az SQLite-index `photos.taken_at_override`
mezőjébe írja. A `.picasa.ini`-t nem hozza létre és nem módosítja. *(A #4693 ELŐTTI állapot:)* A PicasaPy
forrásfájl EXIF-szegmensét nem írta át: a forrás JPEG `DateTimeOriginal` mezője
érintetlen maradt; exportált JPEG-en viszont a `DateTimeOriginal` az indexben
felülírt dátumot kapja, a #451 Colab-mérésével egyezően. Ez a #4646 által
feltárt eredeti viselkedéstől eltér. A rács, a dátum szerinti rendezés és a
Tulajdonságok panel a felülírt értéket mutatta.

**A PicasaPy megvalósítása (#4693):** A művelet `.picasa.ini`-kulcsot nem ír. A PicasaPy a forrásképen módosítja az
EXIF `DateTimeOriginal` értékét, és a sikeres írás után a mappát újraolvassa,
hogy az index, a rácssorrend és a Tulajdonságok-panel az új EXIF-értéket
mutassa. A korábbi, #4332-es indexfelülírásos út ettől eltért; a jelenlegi
menüparancs JPEG-nél már nem hoz létre `taken_at_override` értéket.
Ha az EXIF-írás nem sikerül (videó, nem-JPEG, hibás vagy írásvédett JPEG), a
dátum a `taken_at_override`-ba kerül (#4885), Windowson emellett a fájl
létrehozási ideje is; hibás vagy írásvédett JPEG-nél ez csendes, katalógusbeli
dátum.

### Kérdés-válasz és összevetés (#4646, 2026-10-12)

A lenti állításokat a `Picasa3.exe` disassembly-je és a címekre épülő
imm32-keresés igazolja (eszközök: `pefile`, `capstone`, nincs indexfüggő
lépés). Ahol a bináris nem dönt el valamit, ott **NYITOTT** áll.

**Mit ír az eredeti, és mikor**

| kérdés | válasz | bizonyíték | állapot |
|---|---|---|---|
| EXIF-mező | `0x37` = `DateTimeOriginal` (`0x9003`), az új dátumra | `push 0x37` + a `0x0049c640` setter: `0x004906f7`, `0x00490d3c` | igazolt |
| EXIF-fájlírás | a forrásfájl `.tmp`-n át íródik, csere a `0x00994400`-zal | `r+b` (`0x009eb3e5`), `wb` (`0x009eb5c8`), csere `0x009eb70b`; hívás: `0x009ed39a` → `0x009eb290` | igazolt (a csere belseje nincs) |
| az EXIF-ág feltétele | `[esp+0xac] == 2` **és** a `0x009ed330` nem nullát ad | `0x0049070a`, `0x00490d4f`, `0x00490734`–`0x00490736` | a `2` jelentése NYITOTT |
| hozzáférési és utolsó írási idő | a worker-objektumban nincs `0x1c` (EXIF `DateTime`), ezért a `0x009f05c0` keresés nem talál → nincs `0x00ab35e0`-hívás → a mentett eredeti hármas íródik vissza (nincs eltolás) | `0x009eb34b`–`0x009eb37d` (`eax = 9`, `jne 0x9eb382`); `0x00ab34d0` a jelzőket (`-1`) használja | igazolt (statikus; natív futtatás nincs) |
| létrehozási idő az EXIF-ágban | **érintetlen** (mentve, visszaírva) | `0x00ab35e0` nem írja a `+0x00`-t | igazolt |
| fallback (nem EXIF, vagy íráshiba) | csak a létrehozási idő := az új dátum; hozzáférés és írás NULL | `push 0` a hívóknál (`0x00490900`, `0x00490f40`); `SetFileTime` `0x009927f9` | igazolt |
| `.picasa.ini` | a láncban nincs hivatkozás | sztring `0x00c80a6c`; kb. 70 imm32-találat a `.text`-ben, egyik sincs a láncban | csak a láncra igaz |
| JPEG / nem-JPEG / videó | a láncban nincs formátum-ellenőrzés; a `2` lehet a formátum-osztály | — | NYITOTT |

**A mentett rekord és a visszaírás.** `0x00ab3320` a rekordot nullázza, a
jelzőket `-1`-re állítja (`0x00ab3325`), majd `0x00ab3350` a `GetFileTime`-mal
tölti (`0x00ab3495`). A rekord: `+0x00` létrehozás, `+0x08` hozzáférés,
`+0x10` utolsó írás, `+0x18` jelzőbitek (1 = létrehozás, 2 = hozzáférés,
4 = írás). A visszaírás `0x00ab34d0`-ban a jelzőbitek alapján választja ki, mely
időt adja át a `SetFileTime`-nak (`0x00ab3582`–`0x00ab35a7`).

**A `0x1c` kérdés (2026-10-12, statikusan feloldva).** A `0x009ed330` 1.
argumentuma (P) a worker keretének lokális hash-táblája (`0x00490580`:
`[esp+0x74]`; a táblamezők nullázása `0x004906b8`–`0x004906ce`), amelybe
egyetlen beszúrás érkezik: a `0x37` (`0x004906fe`; a `0x00490c10`-ben
`0x00490d43`). A bucket-szám és a fej beállítását az első beszúrásnál a
`0x0049e810` végzi (ezt nem követtem végig; a getter csak a bucket-számot,
a bucketeket és a csomópont-kulcsot olvassa). Más beszúrás a láncban nincs, és P-t a `0x009ed330` csak
átadja. A `0x009eb290` `0x1c`-t keres P-ben (`0x009eb34b`, `0x009f05c0`);
mivel a `0x1c` nincs a táblában, a getter `eax = 9`-et ad (nem talált ág
`0x009f0600`), a `jne 0x9eb382` átugorja a `0x00ab35e0`-t. Tehát a
DateTime **sem a régi, sem az új** értéke nem kerül be a láncba: a
„hiányzik" ág érvényes. Ebben az ágban a sikeres EXIF-csere után a
`0x00ab34d0` a `0x00ab3320` által `-1`-re állított jelzőkkel mindhárom
mentett eredeti időt visszaírja (létrehozás, hozzáférés, utolsó írás), tehát
a fájl időbélyegei nem változnak. A `0x0077d05a` és a `0x0077d07e` hívóhelyek a
`0x0077cfd0`-kezdetű függvényben vannak (a spec szerint ez a SettingDates szál);
innen csak a két workert hívják, `0x1c`-t nem állítanak.
A teljes `.text` `0x1c` immediate-jeiből a `push 0x1c` + `0x009efe80` + `0x009ed330`
mintázat még négy helyen fordul elő (`0x004386ee`, `0x00456440`,
`0x00478399`, `0x004854e8`); ezek más függvények, és nem a dátumszál közvetlen
hívásai. Azt nem igazoltam, hogy más úton nem érhetők-e el. A PicasaPy-nak
ezek a helyek nem változtatják meg a fenti következtetést.

**A fallback-ág.** `0x00992780` a `bl` jelzőt a `[esp+0x34]`-ről veszi. A
megnyitás a `[0xd69520]` indirekt hívással történik, argumentumai egy
`CreateFileW`-hívásra utalnak (hozzáférés `0x100` = FILE_WRITE_ATTRIBUTES,
megosztás 3, OPEN_EXISTING, `0x2000000` = BACKUP_SEMANTICS). A cél címe
futásidőben töltődik, importtal nem igazolt.

**Összevetés a PicasaPy kutatáskor vizsgált kódjával** (`src/picasapy/app/timestamp_controller.py`,
`_adjust_photo_file_date`):

| pont | eredeti (bináris) | PicasaPy | eltérés |
|---|---|---|---|
| EXIF DateTimeOriginal | `0x37` az új dátumra | `_write_exif_datetime_original`, `.tmp`-csere (JPEG) | nincs (JPEG) |
| hozzáférési és írási idő EXIF-írás után | **eredeti** (nincs eltolás; a `0x1c` nincs a worker-objektumban) | a régi fájlidő + (új − `read_exif_details(...).datetime_modified`), `os.utime` | **van** (igazolt, statikus): az eredeti nem tolja el a `atime`/`mtime`-ot |
| létrehozási idő EXIF-írás után | érintetlen | visszaírja a régi `st_ctime`-ot (csak Windows) | nincs |
| fallback (íráshiba) | létrehozási idő := új dátum | `_set_creation_time_ns(source, target)` — csak `win32`, POSIX-on nincs hatás | **van** Linuxon (#4885) |
| `.picasa.ini` | nem írja (a láncban) | nem írja | nincs |
| nem-JPEG | fallback (creation) | `_jpeg_segments` → `ValueError` → fallback | a feltétel nincs igazolva |

A kutatás idején meglévő tesztek: `tests/app/test_timestamp_controller_4693.py` (a sikeres
ágnál az `atime`/`mtime` eltolását rögzíti, nem a `DateTime`-értéket),
`tests/app/qml_functional/test_adjust_timestamp_4332.py`,
`tests/index/test_datum_feluliras_megmarad_4332.py`. A jegy által nevezett
`tests/app/test_adjust_timestamp_4332.py` nincs a fában.

**Kész, ha (a megvalósításhoz, #4646 és #4885)**

- [ ] **Windows-mérés** (mért, nem becsült): egy JPEG-en, amelynek ismert a
  `ftCreation` / `ftLastAccess` / `ftLastWrite` értéke és ismert az EXIF
  `DateTime` és `DateTimeOriginal`, a párbeszéd után kiolvasni a három időt és
  az EXIF-mezőket. Ebből eldől, hogy a fájlidő a `DateTime`-ból vagy az új
  dátumból jön. Az eredmény táblázatban kerüljön ide.
- [ ] Ugyanez nem-JPEG-en (ha a Picasa engedi), a `2` feltétel igazolásához.
- [x] A bináris (2026-10-12) szerint a sikeres EXIF-ágban a `atime`/`mtime`
  az eredeti marad (nincs `DateTime`-alapú beállítás). Az `os.utime`-eltolás
  megszűnt; a `tests/app/test_timestamp_controller_4693.py`
  `test_sikeres_exif_iras_utan_a_fajlidok_valtozatlanok` már a változatlanságot
  rögzíti. A mérce a binárisból levezetett viselkedés; a Windows-mérés (fent)
  kiegészítő ellenőrzés, nem kapu.
- [ ] Linux: a creation-only fallback ne legyen hallgatólagos no-op. Vagy ír
  valamit, vagy a felület kimondja a korlátot (#4885).
- [ ] A jegy hivatkozásai frissítendők: a menüpont most
  `PicasaMenuBar.qml:2385`–`2388` (a `:2022` elavult); a tesztnév a fentiek szerint.

**Nyitott pontok, és honnan szerezhető meg**

1. A `0x1c` forrása: bináris úton feloldva (2026-10-12): a worker-láncban nincs
   `0x1c`, ezért a „hiányzik" ág él. A Windows-mérés (fent) a végső megerősítés.
2. A `[esp+0xac] == 2` jelentése: a `[obj+0x48]` vtable `+0xc4` metódusának
   azonosítása (a `0x00490cc6`–`0x00490cd2` hívás célja).
3. A `0x00994400` (csere) és a `0x009eb820` belső hatása: nincs végig bejárva.
4. A `[0xd69520]` cél: futásidőben töltődik, importtal nem igazolt.

### Megvalósítási állapot (#4646, 2026-10-12)

A PicasaPy sikeres EXIF-írási ága már nem tolja el az `atime`/`mtime` értéket:
az írás előtt elmenti őket, a mappa újraszkennelése (`sync_tree`, amely relatime
alatt olvassa a fájlokat) UTÁN állítja vissza. Windows alatt a korábban
elmentett létrehozási időt is visszaírja. A hibaág továbbra is csak Windows
alatt tudja az új dátumra állítani a létrehozási időt; a Linux viselkedés a
#4885 hatóköre.

Linuxon mérve (2026-10-12, három egymás utáni futás): zöld a
`tests/app/test_timestamp_fajlidok_sorrend_4646.py` (a sorrendet GUI nélkül,
valódi indexszel méri; fordított sorrendnél piros), a
`tests/app/test_timestamp_controller_4693.py` és a valódi menüből futó
`tests/app/qml_functional/test_adjust_timestamp_4332.py`. A menüs teszt az
`atime`-ot nem méri: a módosítás után a nézet újratölti a képet, és ez a
relatime alatt az `atime`-ot az EXIF-írástól függetlenül frissíti. A
Windows-specifikus létrehozásiidő-ág és a natív Picasa Windows-mérés itt nem
volt futtatható, ezért ezek ellenőrzése nyitott marad.

### A teljes felhasználói út és a #5699 összevetése (2026-10-23)

Az alábbi összevetés a helyi `Picasa3.exe` PE-verziómezője szerint 3.9-es
binárison (`FileVersionMS=0x00030009`), a `runtime/offsettime.fen`
párbeszédleírón és a jelenlegi forráskódon alapul. A bináris cím nélküli
állításnál ezt külön jelölöm; a függvényindex negatív találatát nem használom
bizonyítékként.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| **Menü.** `Tools` → `Adjust Date and Time...`, parancsazonosító `0x9e0e` (`docs/specs/picasa-menu-parancsok.csv:123`). **Bináris kezelőcím: NINCS MEG**; megszerzés: a parancsazonosító diszpécserének cím-atlasza és célzott disassembly, majd natív Picasa-próba kijelölés nélkül, egy képpel, több képpel és megnyitott nézővel. | `PicasaMenuBar.qml` ugyanazt a menücímkét mutatja, `libraryPhotoActionsEnabled` mellett; ez a könyvtárnézetben legalább egy kijelölt képet követel, a nézőben letiltja (`Main.qml:2075-2077`). | **NINCS MEG**, hogy a Picasa mikor engedélyezi a parancsot; a menü elérhetőségének egyezése nem állítható. A megszerzés útja az előző oszlopban. |
| **Párbeszéd vezérlői.** `0x0077c7c0` a `currentdate`, `currenttime`, `newdate`, `newtime`, `thumb` és `adjust_type` elemeket keresi. Az `offsettime.fen` két dátum/idő-csoportot, előnézeti bélyegképet, relatív/abszolút rádiókat és OK/Mégse gombot ír le; az ablak szélessége `fit`. | Az `AdjustTimestampDialog.qml` tartalmaz bélyegképet, jelenlegi és új dátumot/időt, a két módot és OK/Mégse gombot, de a jelenlegi értéket egyetlen szövegmezőként mutatja, az új dátum naptárgombbal, az idő szerkeszthető SpinBox-szal módosítható; az ablak szélessége rögzített. | **Eltérés** a vezérlők megjelenítési szerkezetében és az ablak méretezésében. Ha a cél a natív párbeszéd követése, a mezőcsoportok és a méretezés igazítandó; natív pixelméretet a `fit` önmagában nem határoz meg. |
| **Cím.** `0x0077c803`-nál az elemszám `1`-gyel összevetődik; `1` vagy kevesebb esetén a kód átugorja a `0x00cb40ac` (`Adjust Photo Date - %d items`) formázását, és az `offsettime.fen` alapcíme (`Adjust Photo Date`) marad. | A QML címe minden elemszámnál `Adjust Photo Date - %1 items` (`AdjustTimestampDialog.qml:22`). | **Eltérés:** egy kijelölt képnél az elemszám elhagyandó. Több képnél az elemszámos cím **EGYEZIK**. |
| **Alapérték és induló dátum.** A `0x0077c670` a hívótól kapott `FILETIME` két DWORD-ját a párbeszéd `[+0xc8]/[+0xcc]` mezőjébe másolja (`0x0077c6a0`-`0x0077c6c6`); a `0x0057d7f0` a hívó által lekért objektum `+0x6c` mezőjéből kapott párt adja át (`0x0057d894`-`0x0057d923`). A `0x0077c7c0` ugyanezt a párt `Fen::Value::ValueHolder<_FILETIME>`-ként köti a jelenlegi és új dátum/idő vezérlőkhöz. **A bizonyított adatfolyam:** mind a négy vezérlő a hívótól kapott azonos `FILETIME`-ból indul. Hogy a hívó objektum `+0x6c` mezője melyik rekordmező és ez minden kijelölési esetben a kijelölt fotó dátuma-e, **NINCS MEG**. A rádió alapértéke szintén **NINCS MEG**: a `0x0077c670` belső `[+0xdc]=1` értéke és a `relative`/`absolute` rádió közti megfeleltetést a dekompilátum nem nevezi meg; az `offsettime.fen` sem jelöl checked/default attribútumot. | `openForRows()` az első sor előnézeti dátumát adja a jelenlegi és az új dátum mezőnek, az új időt is ebből tölti, majd a relatív módot jelöli ki (`AdjustTimestampDialog.qml:48-66`). | A hívótól kapott induló `FILETIME` mind a négy vezérlőhöz való kötése **megerősített**; mezőjének szemantikája és a rádió alapértékével való egyezés **nyitott**. |
| **A két mód viselkedése.** A `0x0057d7f0` a kiszámított különbséget (`0x0077cf70`) az `AdjustTimeThread` `+0x80/+0x84` mezőibe, a közvetlen cél-`FILETIME`-ot a `+0x78/+0x7c` mezőkbe írja (`0x0057d9cb`-`0x0057da08`). A `0x0077cfd0` az előbbi különbségmezőkkel a `0x00490580` workerhez, az utóbbi célmezőkkel a `0x00490c10` workerhez megy. Az `offsettime.fen` címkéi ezek jelentését eltolásként, illetve egységes célidőként írják le. Hogy a `adjust_type` virtuális getterének értéke a két rádió közül melyikhez tartozik, **NINCS MEG**. | A relatív mód az első kép régi és új dátuma közti különbséget minden kijelölt kép saját dátumához adja; az abszolút mód minden képre ugyanazt írja (`timestamp_controller.py:245-268`). | A worker-pár jelentése **megerősített** (különbség → `0x00490580`, cél-`FILETIME` → `0x00490c10`); a Picasa rádióazonosító→worker kötése **nyitott**. |
| **Futásjelzés.** A `0x0077cfd0` a `0x00cb4134` (`AdjustTimeThread::SettingDates`) és `0x00cb4120` (`Setting photo dates`) szöveget adja át; a `0x00564250` progress callback a `0x00c8e564` (`AdjustTime:Progress`) és `0x00c8e550` (`Setting image time`) jelzést használja. | A dátummódosítás a soros `_run_photo_writes()` háttérúton fut; ez képenként frissíti az adatot, de nem ad dátumművelethez tartozó számlálót vagy állapotfeliratot (`photo_ops_controller.py:390-424`; `timestamp_controller.py:308`). | **Eltérés:** a dátumművelet saját futásjelzése hiányzik; a felületnek jeleznie kell a feldolgozás folyamatát. A bináris callback pontos képernyő-geometriája és a kijelzett számláló formája nincs meg. |
| **Sikeres JPEG-kimenet.** A két worker a `0x37` tulajdonságot állítja (`0x004906f7`, `0x00490d3c`); ez a `DateTimeOriginal` (`0x9003`). A `0x009eb290` tempfájlos ága a `0x00994400` cserével írja vissza a forrásképet. | A PicasaPy a forrás JPEG `DateTimeOriginal` mezőjét `.tmp` fájlon át frissíti (`timestamp_controller.py:74-123`), majd újraindexel. | **EGYEZIK** a sikeres JPEG-írás kimeneti mezője és a forrásfájl módosítása. |
| **Fájlidők sikeres JPEG-írás után.** A `0x009eb290` menti, majd a `0x00ab34d0` visszaírja az eredeti fájlidőket; a részleteket lásd fent, a #4646 táblázatában. | A PicasaPy az újraindexelés után visszaállítja a mentett atime/mtime értékeket, Windowson a létrehozási időt is (`timestamp_controller.py:197-208, 311-326`). | **EGYEZIK** a sikeres írás utáni megőrzés célja. A natív Windows-mérés továbbra sincs meg. |
| **Tartalékág.** A `0x00490900`/`0x00490f40` útján a `0x00992780` a létrehozási időt az új dátumra állítja; a nem JPEG/video út a `0x004ef3c0`/`0x004ef5a0` címen a `thumbindex` első FILETIME-ját is frissíti (részletek: `pmp-database.md` §15.1-15.2). | Sikertelen EXIF-írásnál a PicasaPy a `photos.taken_at_override` értéket tárolja; Windowson a létrehozási időt is beállítja, POSIX rendszeren fájlidőt nem ír (`timestamp_controller.py:131-176, 179-194, 281-303`). | **Eltérés** a tartalék kimenet tárolási helyében és POSIX fájlidő-hatásában. A katalógus dátuma megmarad, de a fájlrendszer létrehozási ideje POSIX-on nem változik; a #4885 Linux-tartalékot kell ehhez igazítani vagy a korlátot jelezni. |
| **`.picasa.ini`.** A `0x0077cfd0` → `0x00490580`/`0x00490c10` worker- és íróút nem ír `.picasa.ini`-kulcsot; ez a hívási láncra vonatkozó állítás, nem a program egészére. | A PicasaPy útvonal SQLite-felülírást vagy EXIF-et ír, `.picasa.ini`-t nem (`timestamp_controller.py:245-308`). | **EGYEZIK** a művelet szintjén. |

**Bizonyítottsági fok: feltételes.** A nyitáskori `FILETIME` forrását a `0x0057d7f0` hívóút, a `0x0077c670` mezőmásolása és a `0x0077c7c0` vezérlőkötése egymástól elkülönülő kódrészletek támasztják alá; a workerhez adott különbség/célérték megfeleltetést a `0x0057d7f0` és `0x0077cfd0` út egymástól függetlenül mutatja. A rádió alapértéke és a rádióazonosító→worker megfeleltetés viszont nem következik a meglévő Ghidra-kimenetből. A JPEG-írásnál a bináris worker/íróút és a jelenlegi Python-íróút egyezik.

**Cáfoló próba.** Megpróbáltam cáfolni azt az olvasatot, hogy a Picasa minden esetben elemszámot ír a címbe. A `0x0077c803` feltételes ugrása az `1`-es elemszámot a formázó ág megkerülésére viszi; a `0x00cb40ac` sztring hivatkozása és az `offsettime.fen` alapcíme ezt külön ellenőrzi. A cáfoló kísérlet tehát megdöntötte az „mindig elemszámos” állítást, és megerősítette az egyelemű eltérést.

**A #5739 célzott Ghidra-kiegészítése (2026-10-24).** A `0x0077c7c0` dekompilátuma a négy dátum/idő vezérlőhöz ugyanazt a `FILETIME`-értékpárt adja; a `0x0077c670` létrehozó és a `0x0057d7f0` hívóút külön igazolja az adatátadást a hívó objektum `+0x6c` mezőjéből, de e mező fotódátum-szemantikáját nem. A `0x0077cfd0` dekompilátuma és a hívó `0x0057d7f0` disassembly-je egyezik: a kiszámított különbség `0x00490580`-hoz, a cél-`FILETIME` `0x00490c10`-hez kerül. **Cáfoló kísérlet:** ellenőriztem, hogy a `.fen` rádiósorrendje vagy a konstruktor `[+0xdc]=1` kezdőértéke önmagában megnevezi-e az induló rádiót. Nem: nincs checked/default attribútum, a belső flag jelentését pedig az `adjust_type` virtuális getter feloldása nélkül nem lehet a `relative`/`absolute` felirathoz kötni. Ezt az ellenpróbát a `0x0077cee0` visszaolvasó callback disassembly-je is megerősíti: a rádiócsoport állapotát virtuális metódusból olvassa, de a konkrét rádióazonosító nincs közvetlenül a függvényben.

**Nyitva.** A rádió induló kijelölése és a rádióazonosító→worker kötés pontos feloldásához a `Fen::RadioGroup` getter célját kell azonosítani; a már meglévő `0x0077c7c0` és `0x0077cfd0` dekompilátum ezt nem nevezi meg. A parancs menüengedélyezési feltétele továbbra is nyitott.

- `Ghidra-kör kell: 0x0077cee0 - az adjust_type RadioGroup virtuális +0x0c getterének értéke a relative vagy absolute rádiót jelöli-e, és hogyan képezi a callback ezt a [dialog+0xdc] flagre? A meglévő 0x0077c7c0/0x0077cfd0 kimenet csak a dinamikus hívást, illetve a flag workerhez jutását mutatja. [blokkoló]`

**Fejlesztési következmény.** Bizonyított eltérés az egyelemű cím, a párbeszéd vezérlőinek megjelenítési szerkezete, a dátumművelet futásjelzése és a tartalékág POSIX fájlidő-hatása. A `Main.qml:2301` `#4332` megjegyzése elavult: csak indexfelülírásról ír, miközben a jelenlegi sikeres út EXIF-et ír, és csak a tartalékág használja az indexfelülírást. A cím/felület/futásjelzés egy UI-jegyben, a POSIX tartalék pedig a meglévő #4885-ben kezelhető; a QML-megjegyzés is frissítendő. A rádió alapértékét és rádióazonosító→worker kötését a `0x0077cee0` getter céljának feloldásáig ne tekintsük eltérésnek.

## 4. A menüsor ALMENŰ-szerkezete — kilenc almenü

| menü | almenük |
|---|---|
| **Eszközök** | Kísérleti · Geocímke · **Keresés** · Feltöltés |
| **Nézet** | **Megjelenítési mód** · **Mappanézet** · Indexkép felirata · Gyorsbillentyűk |
| **Létrehozás** | Film |

A képernyőkép-alapú audit (`ui-audit-menus.md`) **egyet sem** rögzített.
A Nézet két almenüje visszaigazolja a #1409-et (11 megjelenítési mód) és a
#1407-et (3 mappanézet).

**Az „Indexkép felirata" almenü négy módja:** `ID_CAPNONE` (Nincs) ·
`ID_CAPFILE` (Fájlnév) · `ID_CAPFULL` (Képfelirat) · `ID_CAPRES` (Felbontás).
**Indexkép-méret kettő:** `ID_VIEW_SMALLTHUMBNAILS` ·
`ID_VIEW_LARGETHUMBNAILS`. Az `ID_VIEW_SMALL` külön, láthatósági szűrő;
nem méret-előbeállítás (lásd alább).

## 5. A Beállítások párbeszéd — nyolc fül, ~78 vezérlő

`options.fen` (11 754 b): **General · E-Mail · File Types · Slideshow ·
Printing · Network · Web Albums · Name Tags**.

Öt lelet, ami más jegyeinket érinti:

1. **„Detect duplicates while importing"** — a #1398 dupe-szűrésének kapcsolója
2. **„Store name tags in photo"** — a #1403 XMP-írásának *automatikus* párja
3. **„Enable face detection" + „Enable suggestions:" + két csúszka** — az arcfelismerés küszöbei
4. **A nyomtatás újramintavételezője NEVESÍTVE: „General (Lanczos-3)" és „Extra sharp (Lanczos-8)"**, plusz „Compatible (half-res)" / „High Quality (full-res)"
5. **Formátumlista:** `.BMP .GIF .PNG .TGA .TIF/.TIFF` **`.WEBP`** `.PSD` **RAW** · mozgóképek · QuickTime

Emellett **két megerősítés-kikapcsoló** (lemezről törlés, albumból eltávolítás).

## 6. Személyek kezelése és HTML-export

**`contactmgr.fen`** — kétoszlopos: kereső + **17 soros** kontaktlista +
„New Person"/„Delete Person"; jobb oldalt 32×32 bélyegkép, `Name:`,
`Email(s):` (3 sor) + „Sync Face Tags with Web Albums", és **hat
csak-olvasható azonosító**: **`Album ID`**, **`Contact ID`**, `Focus ID`,
`Subject ID`, `Focus Obfuscated GAIA ID`, `Mobile Obfuscated GAIA ID`.

⭐ Az első kettő **pontosan a `picasa-arcfelismeres.md` személy-modelljének
két azonosítója** (`]facealbum:<N>` és a `contacts.xml id=`); a négy GAIA-mező
az online páros — hatókörön kívül.

**`webexport.fen`** — **sablon-alapú**: öt export-méret (`Original Size` ·
1024 · 800 · 640 · 320, célmegjelöléssel), mozgókép-mód (első kocka / teljes),
oldalcím, célmappa, **sablonlista + leírás + élő előnézet**, „Export".

### 6.1 `webexport.fen` — a méretválasztó és a mozgókép-mód (#4610)

Források: a helyi telepítés (`research/copy_Picasa_3_7/Picasa3/`)
`runtime/webexport.fen`, `web/templates/*`, `web/documentation/index.html`,
a hivatalos magyar katalógus (`referencia/i18n-hu/webexport.xml`), és a
`Picasa3.exe` diszasszemblátuma (`eszkozok/binaris/picasa_dis.py`).

**Egy méretválasztó van, nem kettő.** A párbeszédnek egyetlen
`popup name="sizeradio"` vezérlője van („Export pictures at:",
`webexport.fen` 2–10. sor), és ez a **nagy kép** méretét adja. Bélyegkép-
méret választó **nincs**: a bélyegkép méretét a sablon `define
thumbnailWidth`/`thumbnailHeight` sora szabja meg (`greyfrm/index.tpl`
38–39. sor: 120; `whitefrm/index.tpl` 36–37.: 120; a `*bg` sablonokban a
sor ki van kommentezve, pl. `blackbg/index.tpl` 38–39.).

| index | `webexport.fen` elem | hivatalos magyar felirat (`webexport/itemN`) | képpont | `WebExportSize` érték |
|---|---|---|---|---|
| 0 | `Original Size` (4. sor) | Eredeti méret (`item4`) | 0 = eredeti | 0 |
| 1 | `1024 pixels (for large monitors)` (5.) | 1024 képpont (nagy képernyőkhöz) (`item5`) | 1024 | 5 |
| 2 | `800 pixels (for large Web pages)` (6.) | 800 képpont (nagyméretű weboldalakhoz) (`item6`) | 800 | 4 |
| 3 | `640 pixels (for Web pages)` (7.) | 640 képpont (weboldalakhoz) (`item7`) | 640 | 3 |
| 4 | `320 pixels (for email)` (8.) | 320 képpont (e-mailhez) (`item8`) | 320 | 1 |

- **Alapérték: 640 képpont (3. index).** A párbeszéd-init (`0x007f52b0`) a
  `Preferences\WebExportSize`-t **3-as alapértékkel** olvassa
  (`0x007f5310 mov [esp+0x20], 3` → `0x007f5318 call 0x407a20`), a tárolt
  érték → index leképezés az ugrótábla `0x7f5bf0` (`0x007f55a6`): 0→0, 1→4,
  3→3, 4→2, 5→1, minden más (2, >5) → 0. A mentés (`0x007f5e80`) a fordítottja
  (`0x7f61f8`: index 0→0, 1→5, 2→4, 3→3, 4→1), és mindkét kulcsot a
  `Preferences` alá írja (`0x007f5ffe`, `0x007f6020`) — a választás tehát
  **megmarad** a következő megnyitásig.
- **A sablon felülírhatja.** A `define imageWidth/imageHeight` a
  felhasználó választását írja felül (`blackbg/index.tpl` 31–34. sor
  megjegyzése; `web/documentation` „Command Variables"). A képgeneráló
  (`0x0086bce0`) a változótáblából olvas, és ha a sablon nem adta meg:
  `imageWidth`/`imageHeight` = a párbeszéd választása (`[exp+0xae0]`/
  `[exp+0xae4]`, `0x0086c207`–`0x0086c222`; a mentés ide írja,
  `0x007f6070`–`0x007f6089`), **`thumbnailWidth`/`thumbnailHeight` = 144**
  (`0x0086c125 push 0x90`, `0x0086c136 push 0x90`), `shadowedThumbnails` = 1
  (`0x0086c117`).
- **Árnyék-jelölőnégyzet nincs.** A `webexport.fen` egyetlen jelölőnégyzetet
  vagy kapcsolót sem tartalmaz az árnyékoláshoz: a bélyegképek árnyéka a
  sablon `define shadowedThumbnails` sorából jön (alapérték 1), a képeké a
  `shadowedImages`-ből (alapérték 0, `web/documentation` „Command
  Variables"). A PicasaPy ezért nem kínál árnyék-választót (#4849).

**A mozgókép-mód** — `popup name="moviesradio"` („Export movies using:",
`webexport.fen` 11–16. sor), két elem: **`First frame`** („Első képkocka",
`item11`) és **`Full movie`** („Teljes mozgófilm", `item12`); a csoport
címkéje „Mozgófilmek exportálása:" (`labelgroup9`).

- **Alapérték: Első képkocka.** `Preferences\WebExportMovie` alapértéke 0
  (`0x007f5355 mov [esp+0x20], esi`, ahol `esi = 0` a `0x007f52e9` óta); a
  mentés nem nulla indexre 1-et ír (`0x007f5f67`–`0x007f5f75`).
- **Mit jelent:** a mentés a választást az exportáló objektum `+0xae8`
  bájtjába teszi (`0x007f60aa`–`0x007f60b9`: `[dlg+0xbb0]` = `[exp+0xae8]`,
  mert `exp = dlg+0xc8`, `0x007f6076`). A sablonfeltételek ebből és a
  fájltípusból jönnek (`0x0086db20`); film = a hét filmkód egyike (8, 9, 10,
  11, 12, 0x17, 0x1D — ugyanaz a lista, mint az `export-parbeszed.md`-ben):
  - `isImage` = **nem film, VAGY Első képkocka** (`0x0086efe6`–`0x0086f043`);
  - `isSimpleEmbed` = film ÉS Teljes mozgófilm ÉS típuskód 10
    (`0x0086ee82`–`0x0086eec9`);
  - `isExtendedEmbed` = film ÉS Teljes mozgófilm ÉS típuskód ≠ 10
    (`0x0086ef36`–`0x0086ef73`).

  A gyári sablonok `targetlistelement.html`-je (mind a hat HTML-sablon,
  pl. `blackbg/targetlistelement.html` 8–25. sor) az `isSimpleEmbed` ágon
  `<embed src="<%itemLargeImage%>">`-et, az `isExtendedEmbed` ágon Windows
  Media Player `<OBJECT>`-et, az `isImage` ágon `<img>`-et ad ⇒ **Teljes
  mozgófilmnél az `itemLargeImage` maga a filmfájl**, Első képkockánál a film
  állóképként szerepel a galériában.

**Nyitott:**

- melyik kiterjesztés a 10-es típuskód (tehát melyik film kap `<embed>`-et
  és melyik `<OBJECT>`-et). Nálunk minden teljes film `isSimpleEmbed`
  (termékdöntés: a mai böngészőkben az ActiveX `<OBJECT>` nem játszik le,
  az `<embed>` igen) — ez NEM az eredeti leképezése;
- a teljes film bélyegképe és a filmfájl kimeneti neve az `image/` alatt
  (a fájlokból nem olvasható ki); nálunk a bélyegkép az első kocka, a film
  bájthű másolat;
- hogy a `moviesradio` tiltott-e film nélküli kijelölésnél (a `webexport`
  init-jében nem kerestük; az `export.fen`-é igen, ld. `export-parbeszed.md`).
- a gyári sablonok al-sablonjainak `define`-jai (pl. `blackbg/imagetarget.tpl`
  29–30. sor `define imageWidth 600`, `greyfrm/framebase.tpl` 31–32. sor
  `define thumbnailWidth 120`) **nálunk hatástalanok** a képgenerálásra: a
  képek a futtatás előtt készülnek, és csak az `index.tpl` saját `define`-jait
  olvassuk ki előre (`webexport/sizes.py`). Hogy az eredetiben ezek hatnak-e
  a képméretre, a fájlokból nem dönthető el.

## 7. Színkezelés — és a beállítások TÁROLÁSI HELYE

`ID_VIEW_COLOR_MANAGED` kapcsolója: **`EnableColorManagement`**, és
**beállításkulcs**. A `0x00541b30` (284 b) sztringkörnyezete kiadja a
tárolási ágat is:

> **`SOFTWARE\Google\Picasa\Picasa2\Preferences\`**

⇒ **Minden `Preferences\…` kulcs a registryben él, nem fájlban.** Ez
visszamenőleg megmagyarázza, miért nem találtunk fájlt a #1409
megjelenítési módjaihoz. *(Ugyanitt az `AppLocalDataPath` is — a #1402
adatbázis-útvonala.)*

Bekapcsolva: **monitor ICM-profil** (`GetICMProfileA`, 1 hívó) + a képbe
**ágyazott ICC-profil** (`Embedded ICC profile: %s`) + sRGB-felismerés
(`ytImageMetadata::sRGB`); a RAW-ágnak külön kamera-profilja van
(`icc_camera_profile`, `icc_camera_to_tone_matrix`).

---

## Ami még hátra van (19 tétel)

**Nézet (4):** `ID_VIEW_PICTURE` · `ID_VIEW_LIGHTBOXVIEW` · `ID_VIEW_EDIT` ·
`ID_VIEW_AUTO`
**Fájl (4):** `ID_FILE_EMAIL` · `ID_FILE_EPROCESS` · `ID_FILE_OPEN` ·
`ID_FILE_OPENINANEDITOR`
**Eszközök (4):** `ID_TOOLS_BUTTONMGR` · `ID_TOOLS_CONFIG_SCREENSAVER` ·
`ID_TOOLS_CONFIG_SLINGSHOT` · `ID_TOOLS_UPLOADMGR`
**Egyéb (3):** `ID_REFRESH_THUMB` · `ID_PICTURE_VIEW` · `ID_PICTURE_HIDE_TEXT`
**+ a fenti adagok maradék-kérdései (4)**

*Bizonyítottsági fok: a `.fen`-ből származó szerkezetek **megerősítettek**
(szállított fájl közvetlen olvasása); a sztring- és import-alapú leletek
(vágólap, fájlidő, színkezelés, registry-ág) **megerősítettek**; a
`SMALL` ↔ `SMALLTHUMBNAILS` különbség és a Printing fül öt `title` nélküli
legördülője **nem vizsgált**.*

---

# ⚠️ HELYESBÍTÉS ÉS A MENÜSORUNK MÉRT ÁLLAPOTA (2026-08-25, ugyanaznap)

## A „nálunk" oszlopok tévesek voltak — a mérés

A fejlesztői szál jelezte, hogy *a felvett jegyek felénél a mérés mást
mondott, mint a jegy*. Felmértem a menüsorunkat
(`app/qml/PicasaPy/PicasaMenuBar.qml`):

| | darab |
|---|---:|
| **működő** menütétel (sima `MenuItem`) | **67** |
| nem működő (`PicasaMenuItem`) | 55 |
| — **helyfoglaló** (`placeholder: true`, „még nincs bekötve") | **45** |
| — **nyugdíjazott** (`retired: true`, megszűnt szolgáltatás) | **10** |
| menü / almenü | 18 |

> A `PicasaMenuItem` **kizárólag** a nem működő tételekre való — ezt a
> komponens fejléce mondja ki (`enabled: !placeholder && !retired`).

### Amit tévesen „hiányzónak" írtam — pedig MŰKÖDIK

`Find Duplicates...` · `Move Database...` · `Compact Database...` ·
`Copy All Effects` · `Paste All Effects` · a **négy** indexkép-felirat mód
(`None`/`Filename`/`Caption`/`Resolution` — nálunk **öt**, `Tags`-szel) ·
`Options...` · `Export as HTML Page...` · `Folder Manager...` ·
`Refresh Thumbnails` · `Library View` · `Small`/`Normal Thumbnails` ·
`Properties` · `Export to Google Earth File` · a **kilenc** rendezési tétel ·
a **hét** gyorsjavítás · `Picture Collage...` · `New Movie...`

### ⇒ A hátralévő munka nagy része BEKÖTÉS, nem új menüpont

A 45 helyfoglaló között ott van a feltárt tételek nagy része. A teendő
ezért **„kösd be a meglévő, szürke menüpontot"**, nem „vedd fel a menübe" —
lényegesen olcsóbb feladat.

### A #1397 lefedettségi száma is félrevezető volt

A „150/189 megvan (79%)" **felirat-egyezésen** alapult, és a bekötetlen
helyfoglalókat is „megvan"-nak számolta. **A lefedettséget csak MŰKÖDŐ
tételre szabad számolni.**

## További leletek a 8–10. adagból

**Gombkezelő** (`buttonmgr.tre` + `_text.tre`): két lista
(`Available Buttons:` ↔ `Current Buttons:`), kilenc gomb (`Add >>`,
`<< Remove`, `Move Up`, `Move Down`, `Reset to Defaults`,
**`Find buttons online...`**, `Done`, `OK`, `Cancel`). A működési szabály az
útmutató szövegéből: **a jobb lista fentről-lefelé sorrendje = a gombok
balról-jobbra sorrendje** az alsó sávban. A „Find buttons online…"
magyarázza a `buttons/*.pbz` **letölthető gomb**-formátumot.

**Képernyővédő** (`CScrPrefs::*`) és **Fotómegjelenítő** (`slingshot::*`,
30 szöveg): **külön Windows-komponensek** saját beállítóval —
**hatókörön kívül**; a fogalmak (képernyővédő-album, fájltársítás)
átvehetők.

**„Fájl(ok) megnyitása szerkesztőben"**: **HÁROM** belépési pont
(`eMenuFile`, `AlbumPhoto`, `OneUp`), **eltérő feliratokkal**. ⛔ **Nincs
beállítható szerkesztő-útvonal** — `ShellExecuteA` (8 hívó) adja át a
rendszer társításának. Linuxon ez az `xdg-open` (nálunk már létező fogalom,
ld. #1104).

**„Megjelenítés és szerkesztés"**: **KÉT** belépési pont (Kép menü + a fotó
helyi menüje).

**Szöveg elrejtése/megjelenítése**: **két külön parancs**
(`ID_PICTURE_HIDE_TEXT` / `ID_PICTURE_SHOW_TEXT`), nem egy kapcsoló.

**`ID_VIEW_AUTO`**: ~~nem sikerült besorolni~~ — 🟢 **LEZÁRVA 2026-08-27
(#1409):** igenis tagja a kizáró tömbnek, méghozzá az **első** eleme
(`0x9d1f`, `0x005756e0`), és ő az **alapértelmezett** megjelenítési mód.
Ld. [picasa-megjelenitesi-modok.md](picasa-megjelenitesi-modok.md).

---

## A 11–15. adag leletei (2026-08-25, este)

**`ID_VIEW_AUTO`** a „Megjelenítési mód" almenü **első** tétele (a
menüépítőben közvetlenül a 24 bites előtt).

> 🔴 **Az itt korábban állt két állítás MEGDŐLT (2026-08-27, #1409):**
> „a menüben 12 tétel, a kizáró tömbben 11, az Automatikus nincs benne" —
> **mindkét fele téves**. Mérve: az almenü-tömb **15 rekord** (11 tétel +
> 4 elválasztó, `mov dword ptr [0xd6e12c], 0xf`), a kizáró tömb **11
> elemű**, és az `ID_VIEW_AUTO` (`0x9d1f`) **az első eleme**
> (`0x005756e0`).

**A parancsazonosító-térkép kétszer megbukott — harmadszorra sikerült
(2026-08-27, #1409),** de csak a Megjelenítési mód almenüre, és nem
szabály-alkalmazással, hanem **viselkedésből visszafelé**. A helyes
társítási horgony nem a `push "…kulcs"`, hanem a `mov dword ptr [<cím>],
eax` (ez adja a rekord kezdőcímét); a `+0x0a` ahhoz tartozik. Négy
független szemantikai ellenőrzéssel igazolva — ld.
[picasa-megjelenitesi-modok.md](picasa-megjelenitesi-modok.md) 3. szakasz.
🟢 **Kontroll-mérve, 4/4:** épp azt a négy horgonyt
(`ID_VIEW_MYPICTURES` `0x9db7` · `ID_VIEW_FOLDERS` `0x9db6` ·
`ID_VIEW_ALL` `0x9db9` · `ID_VIEW_WATCHED` `0x9db8`), amelyen a korábbi
szabály **1/4**-et adott, a javított horgony **mind a négyet** eltalálja
(`0x0055a26d`, `0x0055a385`, `0x0055a3cf`, `0x0055a671`). ⇒ **a leképezés
NEM szabálytalan** — rossz horgonyt használtunk.

**Az egész menüsorra kiterjedő kinyerést viszont nem futtattam le**: a
szabály ellenőrzött, az oszlop nem. Aki más menüre kér azonosítót,
ugyanígy horgonyozza le egyenként.

**A `Shortcuts` valószínűleg nem almenü**, hanem gyűjtő-fejléc a
gyorsbillentyűs nézet-tételekhez — a utána épülő négy tétel közül a
`ID_VIEW_WATCHED` bizonyítottan a **mappanézet** hármasába tartozik, tehát
nem lehet a `Shortcuts` tartalma.

**A Nyomtatás fül öt névtelen legördülője** = az **öt gyors nyomtatási
méret**, `PrintSize1`…`PrintSize5` néven, a **17 tételes** `ytPrintSizes`
listából választva. A fül többi kulcsa: `PrintProxyPreview`,
`PrinterQuality` *(`os="win"` — Windows-specifikus)*,
**`PrintResamplerQuality`** (`General (Lanczos-3)` / `Extra sharp
(Lanczos-8)`), és a `Preferences\PrinterData` blob.

**`ID_VIEW_SMALL` ≠ `ID_VIEW_SMALLTHUMBNAILS`.** Az angol felirat dönt:
„Small **Pictures**" vs „S&mall **Thumbnails**"; a menüépítőben 190 sor
választja el őket. Négy külön dolog van: az indexképek **láthatósága**
(`ID_VIEW_THUMBNAILS`), a **méret-pár** (`SMALL`/`LARGETHUMBNAILS`), és a
külön „Kis képek".

## A 16–18. adag — a jegy lezárása (38/38)

**Gombtárolás:** a letölthető gombok a profil **`buttons\`** almappájába
kerülnek; a `.pbz` a **`PicasaButtonFiles`** fájltípus-társításon át
importálódik (*„Launch Picasa and import buttons?"*, hibánál *„Sorry, the
file is not a recognized button file format."*). A szállított gombok külön:
`Picasa3/buttons/*.pbz`. **A beállított SORREND tárolási helye nem
található** — nincs hozzá `Preferences` kulcs.

**Shell-ige:** a „Fájl(ok) megnyitása szerkesztőben" a sima **`open`**
igével megy (`ShellExecuteW`, `0x0050a740`). Az **`edit` ige a binárisban
NEM létezik** — ahogy az `explore`/`runas`/`openas` sem. ⇒ nincs külön
„szerkesztésre megnyitás", és **nem kell szerkesztő-beállítás**.

**„Keresési opciók" (`ID_VIEW_SEARCHVIEW`, `eMenuView`, parancsazonosító `0x9d2b`, #4641):**
a `searchcontainer/searchbutton` gombot aktiválja (`0x005cbb50` → `0x009cd8a0`),
vagyis a keresőmező melletti gomb **opciócsoportját nyitja és zárja**. A
találati sávot **nem** kapcsolja (a korábbi `0x9c8f` párosítás hibás: az a
`thumbui/fullview` kezelője). A pipa a nyitott állapotot követi. Nálunk: a
`menuViewSearchOptions` a `MainToolbar.qml` `searchOptionsPopup`-ját kapcsolja.

**„Kis képek" (`ID_VIEW_SMALL`, `eMenuView`, parancsazonosító `0x9cd8`):**
**láthatósági kapcsoló a CThumbUI könyvtári bélyegképnézetének Nézet
menüjében**, nem indexképméret-választó. A menüépítő `0x005c90f0` a
„Keresési opciók" és a „Rejtett képek" közé teszi (`0x005c918f`), a
`Preferences\Show only big images` állapotát pedig fordítva jeleníti meg:
bekapcsolt tétel = a kisebb képeket is mutassa (`0x005c9157`–`0x005c9195`).
Az akciókezelő `0x005c94e0` ezt az 1/0 beállítást kapcsolja, majd frissíti a
menüt és újraépíti a bélyegképnézetet (`0x005c9528`–`0x005c9540`).

A külön szűrőfogyasztó (`0x0065d010`) alapból szintén `Show only big images`
értéket olvas (`1`, `0x0065f155`–`0x0065f199`); bekapcsolt szűrésnél a
`Preferences\BigPictureThreshold` alapértéke **`0xEA60` = 60 000**
(`0x0065f1cb`–`0x0065f1ee`). A kód a kép szélességét és magasságát
összeszorozza, és ezt a területet hasonlítja a küszöbhöz
(`0x0065f521`–`0x0065f52f`): **60 000 képpontnyi terület az alapküszöb**, nem
60 000 képpont szélesség vagy magasság, és a parancs nem választ új
képméretet. A szűrő további, külön ágai a **3,0** és **0,33333** képarányt
(`0x00c49618`, `0x00cf4fd8`) és a **200** képpontos méretet
(`0x0065f553`–`0x0065f561`) is vizsgálják; ezért a küszöb önmagában nem a
teljes láthatósági predikátum.

⚠️ **Helyesbítés:** a korábbi `minsize` kulcs-hozzárendelés téves volt. A
`minsize` sztring hivatkozása a `.tre` deklaratív tulajdonság-olvasójába
vezet (`0x00ccd300` → `0x008d1450`), míg a fényképszűrő a külön
`BigPictureThreshold` kulcsot olvassa. A `minsize` és az `ID_VIEW_SMALL`
között nincs bizonyított kapcsolat.

**XMP arcrégió (#1403):** `mwg-rs:Regions/mwg-rs:RegionList[last()]` ⇒
**hozzáfűz**, nem felülír; a régió `mwg-rs:Area` (`stArea` típus), és a
koordináták a kiírt **`mwg-rs:AppliedToDimensions`**-höz viszonyulnak. A
`normalized` és a `pixel` mértékegység-sztring is jelen van.

## A 19–22. adag (2026-08-27) — a `menu-lefedettseg.md` „soron következő"-jéből

### 19. A vágólap-család — `ID_CUT` · `ID_COPY` · `ID_PASTE` · `ID_EDIT_COPYTEXT` · `ID_EDIT_PASTETEXT` · `ID_EDIT_COPYALLEFFECTS` · `ID_EDIT_PASTEALLEFFECTS`

**Két névtérben ülnek**: `eMenuEdit` (főmenü) és **`Address`** — utóbbi egy
**hét tételes szövegmező-helyimenü** (`0x007331e0`, 662 b):
`ID_UNDO`, `ID_CUT`, `ID_COPY`, `ID_PASTE`, `ID_DELETE`, `ID_SELECTALL`,
**`ID_AUTOCOMPLETE`** (kikapcsolható automatikus kitöltés).

**Mit ír a vágólapra:** a `0x005378e0` (115 b, hívó `0x0040cd10`, indítás)
**nyolc** formátumot regisztrál: `Shell IDList Array`, `Net Resource`,
`FileGroupDescriptor`, `UniformResourceLocator`, `FileContents`,
`FileName`, **`Preferred DropEffect`**, `Embedded Object` — az
azonosítók a `[+0x08]`…`[+0x16]` mezőkben.

⇒ **fájlokat** tesz a vágólapra (nem képadatot), és a Kivágás/Másolás
különbségét a `Preferred DropEffect` hordozza. Jegy: **#1526**.

### 20. A Keresés… almenü hét színkeresője — hat `ID_S_*` és `ID_VIEW_BW`

Névtér: **`eMenuTools`** (az **Eszközök** menü, nem a Nézet).

A `Searchfor` rekord hét gyerekre mutat: a mutató `0x00d6e708`
(`0x0055c36f`), a darabszám **7** (`0x0055c379`). Az első hat elem a
`ID_S_RED` · `ID_S_ORANGE` · `ID_S_YELLOW` · `ID_S_GREEN` · `ID_S_BLUE` ·
`ID_S_PURPLE`; mind ugyanazt a kezelőt hívja (`0x005ccc41`–`0x005ccca2`),
más tokennel:
`mov edx, "color:<szín>"; call 0x0065b7b0`.

| gyerek | feliratkulcs / alapfelirat | parancs | hatás |
|---|---|---:|---|
| 7. | `eMenuView::ID_VIEW_BW` / `&Black and White` (`&Fekete-fehér`) | `0x9da9` | `color:black` |

A `0x0065b7b0` (131 b) **hat lépése**:

1. `ebx = [this+0xf48]` — a **keresőmező** ablakkezelője (`0x0065b7b4`)
2–3. a token **beírása a keresőmezőbe** (`0x0065b7ea`)
4. a `searchcontainer/searchbutton` megjelenítése
5. `SendMessage(mező, 0xB1 = EM_SETSEL, 0xFFFF, 0xFFFF)` — kurzor a végére (`0x0065b81d`)
6. `0x0065b840(this,0,0,1)` — a lista újraépítése

⇒ A hét menüpont beírja a saját `color:<szín>` tokenjét a keresőmezőbe és
elsüti a keresést; nincs külön szűrő-modell. A hetedik rekord a
`0x00d6e780` címen áll, parancsa `0x9da9`. A diszpécser táblája
(`0x005cde04`, `0x005cdc30`) ezt a parancsot a `0x005ccca7` kezelőre
irányítja; az `0xc950fc` címen tárolt `color:black` tokent adja át a közös
`0x0065b7b0` keresőmező-kezelőnek. **Helyesbítés (#4642):** a korábbi
„nincs hozzá menüfelirat” állítás téves volt; a bináris `ID_VIEW_BW`
feliratkulcsa és `&Black and White` alapfelirata ezen a rekordon is jelen
van. Jegy: **#1399**, kutatási helyesbítés: **#4642**.

### 21. A mentés-család — `ID_FILE_SAVEAS` · `ID_FILE_SAVEACOPY` · `ID_FILE_EXIT`

A mentés **háttérszálon** fut: **`CFileSaveThread`** (`0x0053a790`, 2880 b).

| mit | kulcs / érték |
|---|---|
| megerősítés | „Lemezre menti a módosításokat?" (`CThumbUI::FileSave::message`) |
| egy fájl / több fájl | `messagetag1` / `messagetagX` — **külön mondat** |
| „többé ne kérdezd" | **`DoNotAskFileSave`** beállításkulcs |
| folyamatjelzés | `progfile` / `progfiles` — **századpontos** százalék, egyes/többes |
| hiba 1 | névütközés (`filesaveerr2`) |
| hiba 2 | fájlformátum (`filesaveerr3`) |
| hiba 3 | lemezhiba, **fájlnévvel és hibakóddal** (`filesaveerr-win`) |

#### A `Mentés másként…` és a `Másolat mentése` KÜLÖNBSÉGE (mérve, 2026-08-26)

A 2026-08-24-i kör ezt „nem mértem"-ként hagyta nyitva. A bináris-index
`xrefs` táblája és a helyi diszasszemblálás
(`referencia/eszkozok/binaris/annot_disasm.py`) eldönti:

* a parancs-diszpécser (`0x005cb990`) **ugyanazt** a `0x005e6a20`
  függvényt (1757 b) hívja **mindkét** menüpontra (`call_count = 2`);
* a függvény egyetlen bájt-paraméterre ágazik:
  `0x005e6b6a  cmp byte ptr [esp+0x14d4], bl` → `je 0x5e6bb1`.

| ág | viselkedés |
|---|---|
| param **== 0** — `ID_FILE_SAVEAS` | szűrőlistát épít: `CThumbUI::SaveAsFilterJPG` / `*.jpg`, és ha a forrás WebP (`[esp+0x44] == 0x1f`), `SaveAsFilterWebP` / `*.webp`; **fájlválasztót nyit** (`0x0097f1d0`, sztringjei: `"SaveFile"`, `"ytApp::JPEGFilter"`, `"Preferences"`); a megszakítás korai kilépés; ha a cél **azonos a forrással**, `IDS_CANT_SAVE_TO_SAME` („A képet nem lehet kicserélni. Próbálja újra másik fájlnévvel."); a létezés-ellenőrzés `0x00992ed0` (`"Exists"`) |
| param **!= 0** — `ID_FILE_SAVEACOPY` | `call 0x00993650`, aminek EGYETLEN sztringje **`%s-%03lu`**, majd **`jmp 0x5e6f24`**: átugorja a fájlválasztót ÉS az azonosság-ellenőrzést |

⇒ a **`Mentés másként…`** kérdez (ezért végződik a felirata pontokra:
`Save &As...`), a **`Másolat mentése`** nem (`Save a Cop&y`, ellipszis
nélkül), és a célnév `kep.jpg` → **`kep-001.jpg`**, ütközésnél `-002`.

Mindkét ág a cél mappájának `.picasa.ini`-jén (`0x005e6f33`) és a KÖZÖS
hibaüzeneten (`CThumbUI::FileSaveCopy:err`) fut át.

**Nem mértük:** hogy a cél `.picasa.ini`-jébe MELY kulcsok kerülnek — a
`0x005aafd0` (293 b) nem tartalmaz kulcsnevet. Nálunk ez dokumentált
döntés (`picasapy.edit.save_copy`): a másolat `redo=` + `originhash`
könyvelést kap, a forrás bejegyzése érintetlen marad. Eldöntené: egy
valódi Picasa 3.9-cel készített „Másolat mentése" mellé exportált
`.picasa.ini`.

Jegy: **#1527**.

### 22. `ID_HELP_KEYBOARD_SHORTCUTS`

**Böngészőt nyit**, nem párbeszédet: `HelpURL::Keyboard` =
`…support/bin/answer.py?answer=`**`11139`** (a diszpécser `0x005cb990`
használja). Felirat: **„Billentyűkódok"** — **nem** azonos az
`eMenuView::Shortcuts` / `AlbumList::Shortcuts` „Gyorsbillentyűk"
tételekkel.

⚠️ A `0x009a16b0` (208 b) a **`runtime\shortcuts.xml`**-t nyitná meg, és a
hívója **a menüsor építője** (`0x00559150`) ⇒ **adatvezérelt
gyorsbillentyű-út létezik**, de a fájl **nincs mellékelve** (két
ellenőrzés: `ls` és rekurzív `find`, nulla találat). Jegy: **#442**.

## A 23–26. adag (2026-08-27, második menet)

### 23. `ID_VIEW_SEPIA` · `ID_VIEW_BW` — ⚠️ NEM megjelenítési módok

**Helyesbítés**: a 2026-08-26-i kör tíz „megjelenítési módot" említett;
ebből **kettő effektust alkalmaz**.

> ⚠️ **Pontosítás 2026-08-27-én (#1409):** a `ID_VIEW_BW` / `ID_VIEW_SEPIA`
> **fordítási kulcs** két külön parancson ül. A Kép menüben (`0x9d4c`,
> `0x9d4a`) valóban **effektust** alkalmaz — ez az alábbi leírás. A
> `Nézet ▸ Megjelenítési mód` almenüben ugyanez a kulcs **más
> azonosítóval** (`0x9d1c`, `0x9d1b`) szerepel, és ott **valódi
> megjelenítési mód** (képsoronkénti átalakító, nem ír a `.picasa.ini`-be).
> Ld. [picasa-megjelenitesi-modok.md](picasa-megjelenitesi-modok.md). Ez magyarázza, hogy az `ID_VIEW_BW`
**három** menüpozícióban van, és hogy a `&Szépia` felirat **két**
parancshoz tartozik (`ID_PICTURE_SEPIA`, `ID_VIEW_SEPIA`).

A diszpécser (`0x005cca47`–`0x005cca8e`) **kétágú**:

```
call 0x00579330            ; nyitva a szerkesztő? (37 b, "editpanel/preview")
je   <2. ág>
; 1. ÁG: mov edx,"editpanel/tab3"; call 0x009cd8a0  ⇒ a 3. FÜLRE VÁLT, ott alkalmaz
; 2. ÁG: mov eax,"sepia"; call 0x005fe370           ⇒ KÖTEGELT a kijelölésre
```

A kötegelt applikátor `0x005fe370` (1662 b) a **`filters`** ini-kulcsot
írja, és két hibaüzenete van: `IDS_NEEDS_SELECTION` („Ehhez a művelethez
képek kijelölésére van szükség.") és `IDS_SOME_EDITS_FAILED_TYPE`
(„…**mozgóképekre nem lehet effektusokat alkalmazni**."). Ugyanezt a
mintát követi az `unsharp`/`unsharp2` is. Jegy: **#1409**.

### 24. `ID_PASSPORT` — pontosan EGY arc

`0x00531c60` (1032 b). A feltétel mérve:

```
0x00531d8c  call 0x0047ae90       ; arcfelismerés
0x00531d95  and ecx, 0xfffffffe   ; ytVector méret = darab*2 | jelző
0x00531d98  cmp ecx, 2            ; ⇐ pontosan EGY arc
```

Három erőforráskulcs ismert: `Passport0` = „Can't find any faces",
`Passport1` = „There appear to be multiple faces.”, `Passportfail` = „Try
another picture?”. A `0x00531c60` visszafejtett hibaága a
`Passportfail` címet és a `Passport0` törzsszöveget adja át; ebben az
ágban nincs `Passport1`-re választás. **Élő mérés (#49/#50, 2026-09-26):**
a nulla arcú eset címe „Try another picture?”, szövege „Can't find any
faces”, egyetlen OK gombbal. A többarcú eset élő szövege még nincs külön
mérve. Belépési pont: **Tools ▸ Experimental ▸ Passport photo…**, a
Kísérleti almenü 6. tétele (a kilenc: Publish via FTP… (PicasaPy kihagyja) ·
Show Duplicate Files · Search for ▸ · Save search results… · Show tag as
album… · Passport photo… · Delete empty online albums… · Choose database
location… · Write faces to XMP…). Jegy: **#1401**.

#### ⭐ A KIVÁGÁS GEOMETRIÁJA — kimérve (2026-09-12, #1401)

A jegy blokkolója az volt, hogy „a kivágási arány külön kérdés". Nem az: a
sikeres ág (`0x00531e50`-től) végig kiolvasható.

**1. Az arc-téglalap képpontra váltása.** A felismerő normalizált (0…1)
téglalapot ad; a kód a `+0x10`/`+0x14`/`+0x18`/`+0x1c` mezőket
(bal · fent · jobb · lent) a kép **szélességével** (bal, jobb) illetve
**magasságával** (fent, lent) szorozza (`0x00531e8a`–`0x00531ec4`). A
`fild` melletti `fadd [0xcf39e4]` a szokásos előjel nélküli javítás
(`0xcf39e4` **float** alakja `4294967296,0` = 2³²), nem geometria.

**2. A kerekítés utasításai.** `bal`-ból és `fent`-ből `-0,5`, `jobb`-hoz
és `lent`-hez `+0,5`, majd `fistp` (`0x00531efa`-`0x00531f5a`; a konstans
`0xc72150` = **0,5**). A `fistp` pontos kerekítését félúton meghatározó
futásidejű FPU kerekítési mód **NINCS MEG**; ezért a kivonás/hozzáadás
önmagában nem bizonyít „kifelé kerekítést”. Megszerzése: a konverziót
befolyásoló FPU-vezérlőszó visszakövetése a Passport-hívásig, vagy ismert
félpixel- és egészpixel-koordinátájú bemenetek élő futtatása.

**3. A függőleges ráhagyás — ez volt a hiányzó arány:**

```
arcMagassag = lent − fent
kivagasFent = kerek(fent − arcMagassag / 3,0)      ; 0xcf39f8 = 3,0
kivagasLent = kerek(lent + arcMagassag · 0,6)      ; 0xcf3a70 = 0,6
```

⇒ **felül az arcmagasság harmada, alul a hat tizede** — fejtér fent,
váll lent. A kivágás magassága így `arcMagassag · (1 + 1/3 + 0,6)` =
**1,9333 · arcMagassag**.

**4. A kivágás NÉGYZET, az arc közepére igazítva** (`0x00531faa`–
`0x00531fc7`):

```
kozepX      = (bal + jobb) / 2                      ; elojeles, nulla fele kerekitve
fel         = (kivagasLent − kivagasFent) / 2
kivagasBal  = kozepX − fel
kivagasJobb = kozepX + fel
```

**5. Levágás a kép határaira:** a bal és a fent alsó korlátja **0**
(`0x00531fcf`–`0x00531fe5`), a jobb a kép szélességére, a lent a
magasságára korlátozódik (`0x00531fe9`–`0x00531ffd`).

**A `0xc7dcc8` = 0,3 NEM ebben az ágban van** — a korábbi jegyzet ezt a
kivágás arányának sejtette. A sikeres ág nem hivatkozik rá; a
kivágás arányait a **3,0** és a **0,6** adja.

### 24/b ⭐ A kimenet NYOMTATÁSI MUNKA — és a mérete `ePassport` (2026-09-15, #1401)

A kivágás után következő lánc (`FUN_0056b5c0` → `FUN_006b0200` →
`FUN_00579910(2)` → **`FUN_00744d00(0xf)`**) harmadik kérdése eldőlt: a
**`FUN_00744d00`** sztringjei mondják ki, mi ez.

| sztring | hol | mit árul el |
|---|---|---|
| `IDS_PRINT_PREP_MSG` · **`Preparing to print`** | `0x00744d00` | ez a **nyomtatási** út |
| `outputlayout/pbutton` | `0x00744d00` | a **kimeneti elrendezés** panelé |

⇒ **Az Útlevélkép nem fájlt ír és nem a szerkesztőbe visz: nyomtatási
munkát készít elő.** A `FUN_00579910('editpanel/preview')` `2`-es
argumentuma ezt megelőző nézetváltás.

#### A `0xf` = `ytPrintSizes::ePassport` — az UGRÓTÁBLÁBÓL

A `FUN_00775ce0` (510 b) a nyomtatási méretek NÉVTÁBLÁJA:
`cmp eax, 0x11` / `jmp dword ptr [eax*4 + 0x775ee0]`. A **valódi**
index↔név megfeleltetést az ugrótábla adja (fájleltolás `0x375ee0`):

| index | kulcs | angol | **magyar** |
|---:|---|---|---|
| 0 | `eFullPage` | FullPage | Teljes oldal |
| 1 | `e4x6` | 4 x 6 | — |
| 2 | `e3x5` | 3.5 x 5 | — |
| 3 | `e5x7` | 5 x 7 | — |
| 4 | `e8x10` | 8 x 10 | — |
| 5 | `eWallet` | Wallet | Zsebméret |
| 6 | `e3x4` | 3 x 4 | — |
| 7 | `e4x5` | 4 x 5 | — |
| 8 | `e5x8cm` | 5 x 8 cm | — |
| 9 | `e9x13cm` | 9 x 13 cm | — |
| 10 | `e10x15cm` | 10 x 15 cm | — |
| 11 | `e13x18cm` | 13 x 18 cm | — |
| 12 | `e15x20cm` | 15 x 20 cm | — |
| 13 | `e20x25cm` | 20 x 25 cm | — |
| 14 | `eCDSize` | CD Cover Size | — |
| **15** | **`ePassport`** | **Passport** | **Útlevél** |
| 16 | `eContact` | Contact Sheet | — |
| 17 | — | (alapeset: nincs név) | — |

⇒ a `FUN_00744d00`-nak átadott **`0xf` pontosan az `ePassport`**.

⛔ **A SZTRINGCÍM-SORREND FÉLREVEZET.** A `.rdata`-ban a `3 x 4` és a
`4 x 5` a tábla VÉGÉN áll, és ott a `Passport` a 14. helyre esne. Az
ugrótábla viszont a 6./7. helyre teszi őket, a `Passport`-ot pedig a
15.-re. A szomszédosság itt sem bizonyíték — az **ugrótáblát** kell
olvasni.

#### A legördülő SORRENDJE is megvan — a `FUN_006e5d70` leképezésén át

A nyomtatópanel (`0x00743700`) a listapozíciót **előbb átfordítja**
(`mov eax, [edi]; call 0x6e5d70`, `0x0074380c`), és csak az eredményt adja
a névtáblának. A `FUN_006e5d70` egy veremre épített, 16 elemű
keresőtábla (`0x006e5d76`–`0x006e5ded`; `index ≥ 0x10` ⇒ `1`):

| listapozíció | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | **14** | 15 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| enum | 5 | 2 | 1 | 3 | 4 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | **15** | 16 |
| név | Wallet | 3.5 × 5 | 4 × 6 | 5 × 7 | 8 × 10 | 3 × 4 | 4 × 5 | 5 × 8 cm | 9 × 13 cm | 10 × 15 cm | 13 × 18 cm | 15 × 20 cm | 20 × 25 cm | CD | **Útlevél** | Indexkép |

⇒ Két következmény: a **`FullPage` (0) NINCS a listában** — az külön mód —,
és az **Útlevél a lista 15. eleme** (0-tól számolva a 14.).

*Bizonyítottsági fok: **megerősített** — az ugrótábla és a keresőtábla is
a `.rdata`/`.text` bájtjaiból olvasva, nem sorrendi következtetés.*

#### A fizikai méret és az oldalkiosztás lezárva

Az `ePassport` mérete **2 × 2 hüvelyk**, a példányszám induló értéke 1, és
a lapra rendezés/laptörés is feltárt; a részletes bináris bizonyítékot és
az élő Picasa-mérést lásd a [`picasa-nyomtatas.md`](picasa-nyomtatas.md)
17. szakaszának #1401/#3646 részeiben. A #5658 összevetése következik.

### 24/c: #5658: az eredeti útlevélkép és a PicasaPy tételes összevetése

Az EXE PE-verzióadata: **Picasa 3.9.141.259**. Fontos címjavítás:
`0x00c89994` (`CThumbUI::Passportfail`) és `0x00c899c4`
(`CThumbUI::Passport0`) adatszöveg-kulcsok, nem függvénybelépési pontok;
a tényleges kezelő `0x00531c60`.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| **Menü és diszpécser.** Bináris: `0x00559150` (menüépítő), `0x00c8de18` (`eMenuTools::ID_PASSPORT`), `0x00c8de30` (`&Passport photo...`), `0x005cb990` (`0x9def` ág → `0x00531c60`). | `PicasaMenuBar.qml` ugyanazt a Tools ▸ Experimental menüpontot és feliratot adja, majd a `Main.qml` a passport vezérlőnek adja át. **EGYEZIK.** | Lezárható. A címjegyzékben a `0x00c89994`/`0x00c899c4` értékeket adatkulcsként, ne belépési pontként hivatkozzuk. |
| **Bemeneti kép.** Bináris: `0x00531c60` a `this+0x399` képre futtatja az arcellenőrzést; a `-1` index korai visszatérés. | `Main.qml` a `photoActionRows()` első sorát adja át. Egyetlen kijelölt képnél **EGYEZIK**. Több kijelölt képnél az eredeti kiválasztási sorrend/viselkedés **NINCS MEG**; megszerzés: Picasa 3.9-ben két kijelölt képpel indítsd a menüpontot, rögzítsd melyik képre fut. | Egyképes út lezárható; több kijelölésre ne állítsunk egyezést az élő ellenőrzésig. |
| **Arcok száma.** Bináris: `0x00531d8c` hívja a `0x0047ae90`-et; `0x00531d95`-`0x00531d98` a tárolt arcdarabszámot pontosan egyre vizsgálja. | `classify_face_count()` csak az egy arcot engedi tovább. A darabszám-feltétel **EGYEZIK**. | Lezárható a döntési feltétel; az érzékelők kimenetének egyezése külön nyitott pont. |
| **Arcfelismerő motor.** A `0x0047ae90` dekompilátuma és disassembly-je a `param_1+0x48` objektum vtable-jának `+0xd0` slotját hívja, `param_2` bemenettel és két kimeneti címmel (`0x0047aead`-`0x0047aecf`). A hívás visszatérési értékétől függően folytatja a geometria feldolgozását, de a konkrét célosztályt, modellt/adatot, küszöböt és normalizált arcdobozt **NINCS MEG**. A `0x00531c60` hívó igazolja, hogy a visszaadott arcdarabszámot a kezelő pontosan egyre vizsgálja (`0x00531d8c`-`0x00531d98`); ez nem nevezi meg a dinamikus implementációt. | `FaceDetectorYN` YuNet `face_detection_yunet_2023mar.onnx` modellt használ; score 0,9, NMS 0,3, topK 5000, legnagyobb detektálási méret 960 px (`faces/detector.py`). | **Bizonyítottsági fok: feltételes.** A hívási felület és az egyarcú kapu címmel igazolt; a motor részlete és eredményparitása a konkrét vtable-cél feloldása, majd azonos, címkézett képkészleten végzett eredeti/PicasaPy-mérés nélkül nem állítható. |
| **Sikertelen arcellenőrzés.** Bináris: `0x00531c60` nem-egy-arc ága a `CThumbUI::Passportfail` címet és a `CThumbUI::Passport0` törzset adja át. Élő mérés (#49/#50): nulla arcnál „Try another picture?” / „Can't find any faces” / egy OK. | Nulla arcnál ugyanez a cím, szöveg és OK gomb. Több arcnál a QML `Passport1`-et („There appear to be multiple faces.”) mutat. Az eredeti handler visszafejtett ága ott is `Passport0`-t ad át, tehát a szöveg **ELTÉR**. | A többarcú PicasaPy-hiba törzsszövege kövesse az eredeti `Passport0`-t; élő többarcú eredeti UI-val még erősítsük meg. |
| **Kivágási arány és alak.** Bináris: `0x00531efa`-`0x00531f5a` arc-téglalap; `0x00cf39f8` = 3,0, `0x00cf3a70` = 0,6; `0x00531faa`-`0x00531ffd` négyzetesítés és képszélre korlátozás. | A `faces/passport.py` ugyanazt az 1/3 felső és 0,6 alsó ráhagyást, középre igazított négyzetet és független szélső korlátokat alkalmazza. **EGYEZIK** az arány/alak szabálya. | Lezárható az arány- és határszabály. |
| **Kivágási kerekítés.** Bináris: `0x00531efa`-`0x00531f5a` félpixeles eltolásokat és `fistp`-t használ; a futásidejű FPU-kerekítési mód **NINCS MEG**. | A `passport_crop_rect()` a kezdeti arcéleknél `floor`/`ceil`, a további határoknál Python `round()` műveletet használ. Az utasítássor **ELTÉR**; a pixelkülönbség konkrét képen **NINCS MEG**. A forrás docstringjének „legfeljebb egy képpont” állítása nincs méréssel igazolva. Megszerzés: eredeti és Py kimenet összevetése ismert tört/egész határeseteket és képszéli arcokat lefedő címkézett mintákon. | A PicasaPy eredményét a bináris kerekítési menetéhez kell igazítani; készre csak a FPU-mód tisztázása és bájtszinten egyező kivágási aranyminták után jelentsük. |
| **Sikeres kimenet útja és mérete.** Bináris: `0x00531c60` → `0x0056b5c0` → `0x006b0200` → `0x00579910(2)` → `0x00744d00(0xf)` nyomtatási munkát indít; `0x00775ce0` enumtábla szerint `0xf` = `ePassport`, fizikai mérete `0x00775660` → `0x00cf3a48` = 2 × 2 hüvelyk. | A kivágás a gyorsítótár `passport.png` fájljába kerül, majd a PicasaPy nyomtatási előnézetét nyitja `PASSPORT` (2 × 2 hüvelyk) mérettel. Nincs külön szerkesztőbe ugrás vagy végleges képfájl-mentés. **EGYEZIK** a felhasználói kimenet fő útja és mérete. | Lezárható a nyomtatási út és fizikai méret; az ideiglenes fájl reprezentációja nem felhasználói kimenet. |
| **Friss nyomtatási beállítások.** Bináris: az új beállításcsomag `0x00860f60`/`0x00860f78` szerint 1 példány; a Passport-kezelő (`0x00744d00`) nem írja felül a már létező példányszámot. Élő mérés (#54): Crop to Fit, 1 példány, nincs gyorsméret-előválasztó. | A nyomtatási nézet Passport módban `fill` (Crop to Fit), 1 példány, a Passport nem gyorspreset. **EGYEZIK** friss állapotban. | Lezárható a friss belépési állapot. |
| **Meglévő példányszám.** Bináris: a nyomtatási munka újrahasznált állapotában a `0x00744d00` nem írja felül a `numberprints` mezőt; új csomagnál az alap 1 (`0x00860f60`-`0x00860f78`). | A `PrintDialog.qml` Passport módba váltáskor mindig `copies = 1` értéket állít be, az előző általános értéket csak a Passport módból kilépésre menti el. **ELTÉR** a már nyitott/újrahasznált munka példányszámának megtartásában. | A meglévő nyomtatási munka példányszámát Passport-belépéskor is az eredeti viselkedés szerint kezeljük; a friss munka maradjon 1. |
| **Szegély/felirat 11 alapértéke.** Bináris: `text=0` (`0x0085f8c7`), `textplacement=0` (`0x0085f8fa`), `textfont=Arial` (`0x0085f9db`), `textsize=12` (`0x0085f963`), `textcolor=0` (`0x0085f994`), `wrap=0` (`0x0085f927`), `border=0` (`0x0085f7b2`), `bordersize=10` (`0x0085f7f0`), `bordercolor=0` (`0x0085f827`), `borderedge=0` (`0x0085f85a`), `evenborder=1` (`0x0085f88d`). | `PrintOptions` alapértékei ugyanezek (`printing/options.py`). **EGYEZIK.** | Lezárható; a feliratforrás és elhelyezés kódjai a §317-ben vannak. |
| **Példányok papírlapra rendezése.** Bináris: `0x00778640` cellákat sorfolytonos rácsba rendez, `0x00778190` választ tájolást; a nyomtató papírján történő tördelést a #55 PDF-mérés is igazolta. | Az `app/print_controller.py` `_grid_for_job()` és `grid_layout` cellarácsot, lapváltást és sorfolytonos példánysorrendet valósít meg. A fő rács/laptörés-szabály **EGYEZIK**; a Py által renderelt Passport-lap azonos nyomtatón történő teljes geometriai egyezése **NINCS MEG**. Megszerzés: ugyanaz a kép, példányszám, nyomtató és papír az eredetiben és a PicasaPy-ban, előnézet/PDF-oldalméretek és pixelek összevetésével. | A rácsviselkedés lezárható forráskódszinten; képi egyezést ne állítsunk az azonos eszközös összehasonlításig. |
| **Felirat tartalma saját metaadatokkal.** Bináris: hogy a Passport-út a `usecaption`/`usefilename`/`useexif` módokhoz pontosan mely képrekordot adja, **NINCS MEG**. Megszerzés: `0x00744d00`-tól a `printoptions::text` fogyasztóig visszakövetni, majd mindhárom módot élő eredeti képen mérni. | A Py által létrehozott ideiglenes `PhotoRecord` neve `passport.png`, `caption=None`, `taken_at=None` (`print_controller.py::_passport_record`). | Nincs igazolt eltérés, amíg az eredeti szövegforrása nem bizonyított. A fenti kódkülönbség lehetséges hatását célzott eredeti/Py mintán kell eldönteni. |
| **Nyomtató/cél alapértelmezése.** Bináris: az első Passport-nyomtatási panelen kiválasztott nyomtató és alapcél **NINCS MEG**. Megszerzés: Picasa 3.9 tiszta profillal, telepített alapértelmezett és PDF-nyomtató mellett mérd a panel induló választását. | A Py listáján a PDF-cél az első és alapértelmezett választás. | Az eltérés mértékét az eredeti élő mérés után állapítsuk meg; ne állítsunk egyezést. |

**Bizonyítottsági fok: feltételes.** A menü→diszpécser→kezelő→nyomtatási munka lánc, a crop-szabály és az enum/2 hüvelykes méret bináris útja a jelenlegi forrással egyezik; az arcdetektor kimenete, a félpixeles crop eredménye, a kiválasztási él-esetek és a teljes nyomati képazonosság nincs megmérve. A #5739 dekompilátuma megerősíti, hogy a `0x0047ae90` virtuális diszpécser, de nem azonosítja a vtable konkrét célját.

**Két független út.** A: a meglévő Ghidra-visszafejtés és a célzott utasításszintű olvasás ugyanazt a `0x00531c60` arc- és hibaágat, majd a `0x00744d00` nyomtatási ágat adja. B: az SQLite sztring-xrefjei a `0x00559150` menüépítőt, a `0x005cb990` diszpécsert és a `0x00744d00` Passport-feliratokat külön mutatják; a független élő #49/#50 és #54 mérések igazolják a no-face panelt, illetve a Crop to Fit/1 példány indulást. A két út ezekben a pontokban egyezik; a detektor- és teljes renderelési egyezésre nem adnak választ.

**Cáfoló próba.** Megpróbáltam igazolni azt a korábbi feltevést, hogy több arc esetén az eredeti kezelő `Passport1`-et ad át. A `0x00531c60` Ghidra-kimenetének nem-egy-arc ága és a helyi disassembly ugyanezt cáfolja: a hibaág a `CThumbUI::Passport0` kulcsot tölti be. A `Passport1` erőforrás létezik, de ebből a függvényből nincs hozzá hivatkozás; globális használatáról nem teszek negatív állítást.

**A #5739 célzott Ghidra-kiegészítése (2026-10-24).** A meglévő `0x0047ae90` dekompilálást és a címzett függvény teljes célzott disassembly-jét összevetettem azzal a feltevéssel, hogy maga ez a wrapper rögzíti a modellt vagy küszöböt. Cáfoló eredmény: a hívási cél futásidőben, a `[param_1+0x48]` vtable `+0xd0` slotjából jön; az utasításfolyam nem ad közvetlen célcímet vagy modell-/küszöbkonstanst. Ez csak a wrapperről szól, a konkrét implementációban lévő értékeket nem cáfolja. A független hívóút (`0x00531c60`) a visszatérő arcdarabszámot pontosan egyre szűri, de a modellt és a normalizálást nem oldja fel.

#### Nyitva

- `Ghidra-kör kell: 0x0047ae90 - mely konstruktor vagy állapot írja a detektorobjektum vftábláját a [param_1+0x48] mezőbe, és mi a +0xd0 slot konkrét célja? A 2026-10-24-i dekompilátum a dinamikus hívást mutatja, de nem nevezi meg az implementációt, ezért modell/küszöb/arcdoboz sem nyerhető ki belőle. [blokkoló]`
- Eredeti/Py azonos képkészletes arcdetektor-paritás: mérj az eredeti és a `FaceDetectorYN` által elfogadott arcok számával és téglalapjaival; mérőadat-archívumban releváns minta nem volt.
- A PicasaPy félpixeles crop eredménye, a többarcú eredeti párbeszéd tényleges szövege, több kijelölt kép sorrendje, a felirat-metaadat forrása, az eredeti kezdőnyomtató és az azonos nyomtatón készült teljes Passport-lap képi egyezése a táblázatban megadott módszerrel szerezhető meg.

#### Javasolt jegytörzs-bővítés (#5658)

Az összevetés igazolt eltérései és a lezárható pontok a fenti táblázatban állnak. A kivágási kerekítés, a többarcú hibaüzenet és a meglevő nyomtatási munka példányszámának kezelése fejlesztést indokol; a még nyitott detektor-, metaadat- és nyomtatócél-kérdésekhez ne rendeljünk becsült eredményt.

### 25. `ID_PICTURE_GEOUNTAG`

A `geotag` ini-kulcs eltávolítása. **Nálunk a képesség kész és bekötött**
(`geo_controller.py:99` → `PlacesPanel.qml:99`) — kizárólag a
**menü-belépési pont** hiányzik a `Geotag` almenüből. Felirat:
„Geocímkék törlése". Jegy: **#1404**.

### 26. `ID_SEARCHTOKEN`

`0x005d8330` (869 b) — bekérő párbeszéd. **Három** külön szöveg:
a menüfelirat „&Címke megjelenítése albumként…", a párbeszéd címe
`ThumbUI::addsearchtoken` = „Keresési címke hozzáadása", a felszólítás
`CAlbumState::addsearchprompt` = „Írja be az albumként megjelenítendő
címkét". Jegy: **#1406**.

*(`ID_DELETE_EMPTY_ALBUMS` — „Üres **online** albumok törlése…" ⇒ Picasa
Web, **hatókörön kívül**; a `menu_lefedettseg.py` kizáró listájára került.)*

## A 27. adag — a Megjelenítési mód nyolc tétele (2026-08-27)

> ⚠️ **Előzmény:** hét kizárt irány után arra jutottam, hogy „valószínűleg
> nincs megvalósítva", és azt javasoltam, ne építsük meg. **A tulajdonos
> élesben megcáfolta** („tökéletesen működik, a két gamma is külön-külön").
> A tanulság a `binaris-regeszet-modszertan.md`-ben.

### A mechanizmus: cserélhető képpont-transzformáció

```
0x00575670(ecx = FÜGGVÉNYMUTATÓ)     ; 292 b
   [view+0x254] = ecx                 ; a transzformáció eltárolása
   or [view+8], 7                     ; piszkos jelzők → újrarajzolás
```

A diszpécser **tíz kis kernelt** telepít ide, **tizenegy** menüparancsból
(8 összefüggő: `0x005cbc40`–`0x005cbcc5`, plusz `0x005cc746`, `0x005cc757`).
A Megjelenítési mód almenü **11 tételes** ⇒ egyhez nincs kernel, kézenfekvően
az **„Automatikus"** (törli a felülbírálást) — **feltevés**.

### A kernelek — a TARTALMUKBÓL azonosítva

| kernel | mit csinál | bizonyíték |
|---|---|---|
| `0x9e8810` | a **tiszta fehér** képpontot (`&0xFFFFFF==0xFFFFFF`) `0xFFFF7F7F`-re cseréli | `0x009e8829`–`0x009e8831` ⇒ **túlcsordulás-jelzés** |
| `0x9e8b80` | beolvassa a képernyő **színmélységét** (`[0xd33958]`, forrás: `GetDeviceCaps(BITSPIXEL)` a `0x0097e030`-ban) | ⇒ **színmélység-ág** |
| `0x9e8b40`, `0x9e8b60` | **gamma 2,2** (`0xcf4140`) + `0x00aa3f80` | ⇒ **gamma-ág** |
| `0x9e8850`, `0x9e89a0` | zöld-súly **151/256** (`imul …, 0x97`) | ⇒ **monokróm-jellegű** |
| `0x9e8a10` | csatorna-skálázás `0xdc` (220) | színtranszformáció |
| `0x9e8a70`, `0x9e8ad0`, `0x9e8b90` | nem jellemezve | — |

**Nem tartós**: nincs beállításkulcs (két eltérő alakú lekérdezés), nincs
pipa-frissítő (mind a 13 `CheckMenuItem`-hívó megnézve).

⚠️ **A menüpont↔kernel párosítást NEM adom ki** — ahhoz a
parancsazonosítók kellenének, ami a projektben tiltott. A megvalósítói
kör mérje ki. Jegy: **#1409**.

## A 28. adag (2026-08-27) — Google Earth és a kontextusfüggő album-feliratok

### `ID_VIEW_EARTH` — kiírja a KML-t ÉS megnyitja

Két külön tétel van az `eMenuTools`-ban: az `ID_EXPORT_EARTH`
(„Exportálás Google Earth-fájlba") **csak kiírja**, az `ID_VIEW_EARTH`
(„Megtekintés a Google Earth programban…") **kiírja és megnyitja**.

Hiányzó program esetén a `0x005ff930` (376 b) párbeszédet nyit, **két
külön ággal**: `InstallEarth:message_install` („telepítenie kell") és
`message_update` („frissítenie kell"). Cím: „Figyelmeztetés"; gombok:
**„További információ…"** (→ `http://earth.google.com`) és **„Mégse"**.
Jegy: **#1589**.

### `ID_ALBUM_DELETE` · `EDITCAPTIONS` · `SELECTALLPICTURES` · `LOCATEONDISK` — KONTEXTUSFÜGGŐ felirat

Ugyanaz a parancsazonosító **más feliratot** kap névtér szerint:

| parancs | `Folder::` | `Album::` | `PplAlbum::` | `eMenuLabelFolder::` |
|---|---|---|---|---|
| `ID_ALBUM_DELETE` | Mappa törlése… | Album törlése | Az Emberek album törlése | Törlés… |
| `ID_ALBUM_EDITCAPTIONS` | Mappaleírás szerk.… | Albumleírás szerk.… | Az Emberek album szerk.… | Leírás szerk.… |
| `ID_ALBUM_SELECTALLPICTURES` | — | Az összes kép kijelölése | Az összes kijelölése | — |
| `ID_ALBUM_LOCATEONDISK` | Keresés a lemezen (`FolderWin::`) | — | — | — |

*(Macen az `ID_ALBUM_LOCATEONDISK` = „Megjelenítés a Finder alkalmazásban" — hatókörön kívül.)*

A helyi menük építői: `0x007319f0` (mappa), `0x00732160` (album),
`0x007359e0` (Emberek album), `0x00733a40`.

✅ **Nálunk 11/13 felirat HELYES** (gépi összevetés a `stringres`-szel):
a `FolderContextMenu`, `AlbumContextMenu` és `PeopleAlbumContextMenu`
mind a saját alakját használja. **Nincs teendő.**

### `ID_FILE_PRINTCONTACTSHEET` — „Indexképek nyomtatása…"

Az `eMenuLabelFolder` 13 tételéből az **egyetlen**, ami nálunk sehol
nincs. Az indexkép-**elrendezés** viszont kész
(`collage/contact_sheet.py`), a nyomtatás pedig a **#1472** előfeltétele.
Jegy: **#1590**.

## A 29. adag (2026-08-27) — Ajándék CD, kollázs, diavetítés, kijelölés, címke-felirat

### `ID_BURNCD` — RÉSZBEN hatókörön kívül (helyesbítve 2026-09-03)

A `0x0066fae0` (439 b) **négy fájlt** másol a lemezre: `PicasaCD.exe`
(windowsos önindító nézőprogram), `Picasa CD Slideshow.app` (macOS), és a
nézőprogram felületleírói (`cdgo.ui`, `cdgo.tre`).

> ⛔ **HELYESBÍTÉS.** Itt eddig ez állt: *„Az Ajándék CD **nem
> fényképexport**, hanem egy **szállított nézőprogram** lemezre égetése."*
> Ez **túl szűk**, és a megvalósítást rossz irányba vitte volna.
> **Amit a mérés mond** ([`ajandek-cd-kimenet.md`](ajandek-cd-kimenet.md)
> 3. és 10. szakasz): a lemezre a nézőprogram mellett **teljes
> fényképexport** kerül, **tizenhat beállítással** — felső képméret-korlát,
> JPEG-minőség (mérve: **85**), bélyegkép-méret, eredeti fájl,
> `.picasa.ini`, manifeszt (felirattal, fájlidővel), HTML-galéria,
> nem-JPEG konvertálása, filmek megőrzése. Ugyanaz a csővezeték, mint a
> biztonsági mentésé.
>
> ⇒ **Hatókörön kívül csak a windowsos/macOS nézőprogram és az
> `autorun.inf`**; a **fényképexport fele átvehető**, és a #440 mentés-ágával
> közös. A parancs a **Létrehozás** menüben ül (`eMenuCreate::ID_BURNCD`),
> és összesen **öt** belépési pontja van, kettő kikommentezve.

Jegy: **#32** · a kimenet lapja: [`ajandek-cd-kimenet.md`](ajandek-cd-kimenet.md).

**Amit MÁSHOVA ad:** az Ajándék CD és a **Biztonsági mentés** ugyanazt a
panelt használja (`il_BurnPanel`) — a mentés tizenkét hivatalos magyar
felirata a **#440**-hez került, köztük a `BackupCopy::1` =
„Fájlok másolása (**%2$d/%1$d**)", **fordított** argumentumsorrenddel.

### `ID_COLLAGEMAKER` — a parancs egy menüben, de KÉT belépési pont

A parancsazonosító csak az `eMenuCreate`-ben van („&Képkollázs…"), de a
kollázs **gombbal** is indul: **`outputlayout/collage`** (`0x00574100`,
`0x005d9cc0`). A `0x005d9cc0` az **alsó műveletsáv** vezérlő-listája —
ugyanott van a `makemovie`, `sharewith`, `save`, `orderbutton` és
`action/createmovie` is. Jegy: **#1006**.

### `ID_ALBUM_SLIDESHOW` vs `ID_VIEW_SLIDESHOW` — KÉT külön parancs

| parancs | menü | felirat |
|---|---|---|
| `eMenuView::ID_VIEW_SLIDESHOW` | Nézet | **&Diavetítés** |
| `eMenuLabelFolder::ID_ALBUM_SLIDESHOW` | mappa helyi menüje | **&Diavetítés megtekintése** |

✅ **Nálunk mindkettő megvan**, helyes felirattal és **Ctrl+4**-gyel
(`PicasaMenuBar.qml:433` és `:787`). **Nincs teendő.**

### `ID_CLEAR_SELECTION` — NÉGY névtér, azonos jelentés

`Album::`, `Folder::`, `PplAlbum::` → „&Kijelölés törlése";
`eMenuEdit::` → „Kijelölés &törlése" *(a gyorsbillentyű-aláhúzás más
betűn — a menüsávban a `t`, a helyi menükben a `K`)*.

✅ **Nálunk mind a négy helyen megvan** (`PicasaMenuBar`,
`AlbumContextMenu`, `FolderContextMenu`, `PeopleAlbumContextMenu`),
Ctrl+D-vel. **Nincs teendő.**

*(A szomszédos `ID_SELECTSTAR` = „Csillagozottak kijelölése" szintén
megvan nálunk — `selection.js:62`, #426.)*

### `ID_CAPTAG` — az indexkép-felirat „Címkék" módja

Az `eMenuView::ID_CAPTAG` = „&Címkék" a **felirat-mód** ötös
rádiócsoport tagja (`captionmode` beállításkulcs, ld. a 22. adagot).
✅ **Nálunk megvan és tartós** (`controller.py:481`, `view/thumbCaption`).
**Nincs teendő.**

## A 30. adag (2026-08-27) — másodpéldány-szűrő, arc-filmek, és a KÉT rendezés-készlet

### ⚠️ Helyesbítés: az `eMenuLabelFolder` a MAPPA FŐMENÜ

A 28. adagban „label-mappa helyi menüjének" neveztem. **Téves.** A
`stringres` szerint a felirata **`&Folder` / `&Mappa`** — a nyolc
menüsáv-tétel egyike: `&Fájl`, `Sz&erkesztés`, `&Nézet`, **`&Mappa`**,
`&Kép`, `&Eszközök`, `&Létrehozás`, `&Súgó`.

### ⛔ KÉT rendezés-készlet, és nem cserélhetők fel

| | parancsok | tételek | felirat | hol |
|---|---|---:|---|---|
| **A** | `ID_DATESORT`, `ID_NAMESORT`, `ID_SIZESORT`, `ID_REVERSESORT` | **4** | **rövid**: &Dátum · &Név · &Méret · &Fordított sorrend | **Mappa menü**, `Folder::SortFolderBy`, `Album::SortAlbumBy` |
| **B** | `ID_VIEWBYDATE/NAME/SIZE/RECENT`, `ID_VIEWREVERSE` | **5** | **hosszú**: „Rendezés létrehozási dátum alapján" … | **Nézet menü**, bal hasáb (`AlbumList::`) |

⇒ A **„legutóbbi változtatások"** CSAK a B készletben létezik.

Ugyanaz a parancs a két helyen **más feliratot** kap:
`eMenuView::ID_VIEWBYDATE` = „Rendezés **létrehozási** dátum alapján",
`AlbumList::ID_VIEWBYDATE` = „Rendezés **dátum** alapján".

Nálunk a **Mappa menü a B készletet használja** (hiba, **#1595**), a
`FolderContextMenu` viszont **helyesen** az A-t.

### `ID_DUPES` — SZŰRŐ, nem párbeszéd

A kezelő (`0x005ccc14`–`0x005ccc3c`) három lépés, egyik sem nyit ablakot:
megjeleníti a **keresősávot** (`searchcontainer/searchbutton`), bekapcsolja
a **másodpéldány-opciót** (`searchoptions/dupesearch`), és **újraépíti a
listát** (`0x0065b840` — ugyanaz, amit a színkeresés is hív).

⇒ A találatok a **fő rácsban** jelennek meg. A felirat is ezt mondja:
„Fájlok másodpéldányainak **megjelenítése**". **Nálunk 2026-09-10 óta
ugyanígy** (#1398): a menüpont a `dupes` nézet-módot kapcsolja
(`app/dupe_search_controller.py`), a `DedupDialog` — ami a MI bővítésünk
(#287) — külön, saját jelölésű menüpontról nyílik.

### `ID_FACES` · `ID_FACESRANDOM` — a Film almenü két arc-tétele

Névtér: **`eMenuCreateMovie`** (a `Létrehozás ▸ Film` almenü).

| parancs | magyar | bemenet |
|---|---|---|
| `ID_FACES` | „A kijelölésben lévő arcokból…" | az aktuális **kijelölés** |
| `ID_FACESRANDOM` | „Az Emberek albumból…" | az **Emberek albumok** |

⚠️ A `RANDOM` utótag **nem a felirat része**; hogy a válogatás
véletlenszerű-e, **nem mérve**. Jegy: **#1408**.

### `ID_EXPORT_SENDTOBLOGGER` — HATÓKÖRÖN KÍVÜL

„Közzététel a Bloggeren…" — a szolgáltatás halott. A
`menu_lefedettseg.py` kizáró listájára került.

---

## 31. tétel — a Fájl menü öt parancsa (2026-08-27)

A menü-lefedettségi mérés determinisztikus sorából a következő öt:
`ID_FILE_EXPORTTOFOLDER`, `ID_FILE_IMPORTPICTURE`, `ID_FILE_LOCATEONDISK`,
`ID_FILE_NEWFOLDER`, `ID_FILE_NEWLABEL`.

### 31.1 A feliratok — két azonosító FÉLREVEZET

| azonosító | angol felirat | magyar (hivatalos) |
|---|---|---|
| `ID_FILE_EXPORTTOFOLDER` | `Export Pi&cture to Folder...` | Kép e&xportálása mappába… |
| `ID_FILE_IMPORTPICTURE` | `&Import From...` | &Importálás forrása… |
| `ID_FILE_NEWFOLDER` | **`Mo&ve to New Folder...`** | **Áthel&yezés új mappába…** |
| `ID_FILE_NEWLABEL` | **`&New Album...`** | **Ú&j album…** |
| `eMenuFileWin::ID_FILE_LOCATEONDISK` | `&Locate on Disk` | &Keresés a lemezen |
| `eMenuFileMac::ID_FILE_LOCATEONDISK` | `Show in Finder` | Megjelenítés a Finder alkalmazásban |

⚠️ **A `NEWFOLDER` nem mappát hoz létre**, hanem a kijelölt képeket
**áthelyezi** egy új mappába. A `NEWLABEL` pedig **albumot** csinál (a
Picasa belső neve az albumra: „label"). Az azonosítóból egyik jelentés sem
olvasható ki — ez a `[[menufelirat-nem-funkcio]]` csapdájának a fordítottja:
itt a *név* félrevezet, nem a felirat.

⚠️ **A `LOCATEONDISK` felirata PLATFORMFÜGGŐ** (`Win` / `Mac` utótagú
kulcsok). Linuxra az eredeti nem ad feliratot — ez döntést igényel.

### 31.2 A „Keresés" HÁROMTÉTELES ALMENÜ, nem egy parancs

> ⛔ **HELYESBÍTVE (2026-09-22, #3456):** az almenü **KÉT** tételes (Fájl a lemezen · Eredeti a lemezen), és **feltételes** — csak egyetlen, visszaállítható (`revertable`) kép kijelölésekor cseréli be a közös utófeldolgozó; a „Keresés a Picasában” NEM tagja. Részletek: `ui-audit-context-menus.md` **D.2**.

A rács helyi menüjében (`CThumbUI`, `0x0056c5a0` / `0x0056e1c0`) a
`CThumbUI::locatemenu` = **„Keresés"** egy almenü, három gyerekkel:

| kulcs | felirat | mit csinál |
|---|---|---|
| `CThumbUI::locateondiskmenu` | `&Fájl a lemezen\tCtrl+Enter` | a fájlt mutatja meg a fájlkezelőben |
| `CThumbUI::locateorigondiskmenu_win` | `Eredeti &a lemezen` | **az EREDETIT** (`.picasaoriginals`) mutatja meg |
| `IDS_LOCATE_SOURCE_IMAGE` | `Keresés a Picasában` | album-nézetből a kép **valódi mappájára** ugrik |

Mac-en a második `CThumbUI::locateorigondiskmenu_mac` = „Eredeti fájlok
megjelenítése a Finder alkalmazásban".

Ezen felül **külön parancs** van a mappára/albumra:
`FolderWin::ID_ALBUM_LOCATEONDISK` (`0x007319f0`, `0x00733a40`).

**Öt belépési pont** hordozza az `ID_FILE_LOCATEONDISK`-et: a Fájl menü és
négy helyi menü (`FolderPhotoWin` ×3, `AlbumPhotoWin` ×2).

### 31.3 Nálunk (mérve, 2026-08-27)

| parancs | nálunk | állapot |
|---|---|---|
| `EXPORTTOFOLDER` | él, `Ctrl+Shift+S` bekötve (`Main.qml:661`) | ✅ |
| `NEWLABEL` | menütétel él; a hirdetett **`Ctrl+N` NINCS bekötve** | ⚠️ |
| `IMPORTPICTURE` | `placeholder: true` (`PicasaMenuBar.qml:236`), a `Ctrl+M` sincs — **pedig az `ImportSourceDialog` létezik és az eszköztárból működik** (`MainToolbar.qml:65`) | ❌ |
| `NEWFOLDER` | `placeholder: true` (`PicasaMenuBar.qml:244`) | ❌ |
| `LOCATEONDISK` | **egyetlen, lapos tétel** négy felületen; nincs almenü, nincs „Eredeti a lemezen", nincs „Keresés a Picasában" | ❌ |

*Bizonyítottsági fok: **megerősített** — minden felirat a hivatalos
`stringres-en-hu.tsv`-ből, minden cím a bináris indexből; a „nálunk" oszlop
mind mérve.*

---

## 32. tétel — a MAPPA helyi menüje, mind a 18 tétel (2026-08-27)

Forrás: `0x007319f0` **szűretlen** sztringlistája + `stringres-en-hu.tsv`.

> ⚠️ **Módszertani figyelmeztetés.** Az első lekérdezésem `LIKE` szűrővel ment
> (`'%folder%'`, `'%Remove%'`, `']%'`), és **13 tételt** adott — a valóság 18.
> A szűrt lekérdezés NEM elemlista. A skill „teljes elemlista, nem minta"
> követelménye pontosan ezért van.

### 32.1 A teljes lista

| # | azonosító | angol | magyar (hivatalos) | nálunk |
|---|---|---|---|---|
| 1 | `ID_HIER_FOLDER_EXPAND` | Expand All | Az összes részletes nézete | ✅ `FolderHierarchyView.qml:180` |
| 2 | `ID_HIER_FOLDER_COLLAPSE` | Collapse All | Az összes kicsinyítése | ✅ `FolderHierarchyView.qml:185` |
| 3 | `ID_ALBUM_EDITCAPTIONS` | &Edit Folder Description… | &Mappaleírás szerkesztése… | ✅ `:69` |
| 4 | `ID_ALBUM_SELECTALLPICTURES` | Select &All Pictures | — | ✅ `:78` (`Ctrl+A`) |
| 5 | `ID_CLEAR_SELECTION` | &Clear Selection | &Kijelölés törlése | ✅ `:83` (`Ctrl+D`) |
| 6 | `ID_SELECT_INVERT` | &Invert Selection | — | ✅ `:88` (`Ctrl+I`) |
| 7 | `ID_ALBUM_MOVETOCOLLECTION` | Mo&ve to Collection | Át&helyezés gyűjteménybe | ✅ `:108` |
| 8 | `ID_REFRESH_THUMB` | Refresh &Thumbnails | &Indexképek frissítése | ✅ `:118` |
| 9 | `SortFolderBy` | S&ort Folder By | Mappa r&endezésének alapja | ✅ `:139`–`:176` |
| 10 | `ID_HIDEENTIREALBUM` | &Hide Folder | Mappa e&lrejtése | ❌ **`placeholder: true`** (`:191`) |
| 11 | `ID_UNHIDEENTIREALBUM` | &Unhide Folder | Mappa m&egjelenítése | ❌ ugyanaz a tétel, váltakozó felirattal |
| 12 | `ID_ALBUM_LOCATEONDISK` | &Locate on Disk | &Keresés a lemezen | ✅ `:199` |
| 13 | `ID_MANAGE_ALBUM` | **&Remove from Picasa…** | **&Eltávolítás a Picasából…** | ✅ `:204` |
| 14 | `ID_MOVEFOLDER` | &Move Folder… | &Mappa áthelyezése… | ✅ `:216` |
| 15 | `ID_ALBUM_DELETE` | &Delete Folder… | &Mappa törlése… | ❌ **`placeholder: true`** (`:222`) |
| 16 | `ID_ONLINE_ACTIONS` | Online Actions (almenü) | — | ⚠️ nálunk laposan, csoport nélkül |
| 17 | `ID_ALBUM_MAKE_WEB` | E&xport as HTML Page… | — | ✅ `:241` (#534 szerint a funkció hiányzik) |
| 18 | `ID_ALBUM_FILTERFACES` | &Add name tags | — | ✅ a kiválasztott mappa képein indít név-címkézést (#4535) |

Az `Online Actions` almenü alatt: `ID_UPLOAD_ALBUM_TO_GOOGLE_PLUS_PHOTOS`,
`ID_UPLOAD_ALBUM_TO_LIGHTHOUSE`, `ID_ALBUM_MAKE_WEB`. Nálunk az `AlbumContextMenu.qml:107`
ismeri az „Online Actions" csoportot, a MAPPA menüjében viszont nincs meg.

### 32.2 Két félrevezető azonosító

| azonosító | amit sugall | amit TÉNYLEG jelent |
|---|---|---|
| `ID_MANAGE_ALBUM` | album kezelése | **„Eltávolítás a Picasából…"** — a mappa kikerül a figyelésből, a fájlok a lemezen maradnak |
| `ID_MOVEFOLDER` | egy felirat | **kettő**: `Folder::` felületen „Mappa áthelyezése…", `eMenuLabelFolder::` felületen csak „Áthelyezés…" |

Ez a 31.1 tanulságának folytatása: **az azonosítóból soha ne állíts jelentést,
ha van hozzá `stringres` felirat.**

### 32.3 A „Mappa elrejtése" TÖBB, mint egy jelölő

A binárisból három, egymásra épülő réteg olvasható ki:

1. **`]hidden` token** — 11 függvény hivatkozik rá (`0x0041c340`, `0x00422ce0`,
   `0x004a51f0` és mások). Ez a rejtett elemek jelölése.
2. **„Rejtett mappák" gyűjtemény** (`IDS_HIDDEN` = `Hidden Folders`,
   6 hivatkozás: `0x00402f90`, `0x004a1560`, `0x004a8b10`, `0x00537fb0`,
   `0x005ec130`, `0x005ee2a0`) — a rejtett mappák ide kerülnek, nem tűnnek el.
3. **Jelszavas védelem** — `IDS_PROMPT_HIDDEN_PWD_MESSAGE` /
   `IDS_WARN_NO_HIDDEN_PWD`: *„A »Rejtett mappák« gyűjteményt jelenleg nem védi
   jelszó. Szeretne most megadni egy jelszót?"*

Továbbá a `ShowHidden` beállítás (`0x00440af0`, `0x005643e0`, `0x005c9300`,
`0x0067bda0`) kapcsolja a megjelenítést.

**Vagyis az elrejtés gyűjteménybe sorolás és felületi hozzáférési kapu**,
nem fájltitkosítás: a PicasaPy figyelmeztetése és a képfájlok lemezen
maradása a 32.3.1 / #5700 mérésével egyezik.

**Nálunk (#4597 kódvizsgálat):** a fotó-szintű `photos.hidden` mellett a
mappa-szintű `folders.hidden` is létezik (`index/schema.py:377`, `:501–515`).
A `toggleFolderHidden` ezt az SQLite-mezőt olvassa és írja
(`app/controller.py:897–914`); a láthatóságot a `showHidden` kapcsoló vezérli.
A mező alapértéke új indexben `0`, ezért a jelenlegi rejtés nem rendelkezik
az indexen kívüli forrással.

*Bizonyítottsági fok: **megerősített** a menüleltár, a feliratok és a három
elrejtés-réteg. A mappaszintű Hide/Unhide tartós tárolója a 32.3.1 szerint
**megerősített** (bináris, két független úton): `.picasa.ini`
`[Picasa] P2category=Hidden Folders`.*

### 32.3.1. ✅ #4597 — a mappa elrejtése a `.picasa.ini` `[Picasa] P2category=Hidden Folders` sora (2026-10-11)

**Következtetés.** Az eredeti a „Mappa elrejtése" parancsra **nem külön
jelölőt** ír, hanem a mappát átsorolja a **`Hidden Folders` gyűjteménybe**:
a mappa saját `.picasa.ini`-jének `[Picasa]` szakaszába
`P2category=Hidden Folders` kerül. A „Mappa megjelenítése" ugyanezt a kulcsot
`P2category=Folders on Disk`-re írja vissza. A `P2category`-t az eredeti a
mappa beolvasásakor szó szerint gyűjteménynévként veszi át, tehát az
elrejtés **túléli az adatbázis újraépítését**, és a mappával együtt költözik.
A db3-ban ennek csak a **származtatott másolata** van (`albumdata_category` →
`catdata` sorindex). A jelszó viszont NEM az ini-ben van, hanem a db3
`catdata` táblájában (ld. alább).

#### Az írási lánc (A út), címekkel

| lépés | cím | kiolvasott tény |
|---|---|---|
| menü | `0x007319f0` | `&Hide Folder` → parancs **`0x9c72`** (`0x00731d7a`: `mov word [esp+0x11e], 0x9c72`, a `push` miatt eltolt veremmel a Hide-tétel azonosítómezője); `&Unhide Folder` → **`0x9cd0`** (`0x00731dea`) |
| diszpécser | `0x005cb990` | ugrótábla `0x005cdb34`/`0x005cd9fc`, alap `0x9c42`: a **`0x9c72` → `0x005cc054`**, a **`0x9cd0` → `0x005cc069`** (a táblát a binárisból kiolvasva) |
| a két ág | `0x005cc054` / `0x005cc069` | `push 1` ill. `push edi` (=0), majd `call 0x005ee2a0` — **egy** rutin, a harmadik argumentum az irány |
| gyűjtemény kiválasztása | `0x005ee2c1`–`0x005ee327` | ha az irány 1: `"Hidden Folders"` (`0x00c7ecb4`), különben `"Folders on Disk"` (`0x00c7ec78`); a név → `catdata`-sorindex a `0x00452a30`-cal |
| átsorolás | `0x005ee352` | `call 0x00445b80(db, album, gyűjtemény, 1)` — a negyedik argumentum (1) kapcsolja az ini-írást |
| ini-írás kapuja | `0x00445ea4` | `cmp byte [esp+0x34], 0` — csak ha a 4. argumentum igaz |
| a gyűjtemény neve | `0x00445ebf` | `call 0x00453c00` — sorindex → név |
| a mappa ini-útja | `0x00445eff` | `call 0x004543e0` (ugyanaz az út-feloldó, mint a mappadátumnál, `pmp-database.md` 12.1); nem nulla visszatérésnél **nincs** írás |
| **a kiírás** | `0x00446012`–`0x00446017` | `push "P2category"` (`0x00c809e8`) · `call 0x0045c0a0` |
| a közös `[Picasa]`-beállító | `0x0045c0a0` | `.picasa.ini` (`0x00c80a6c`) megnyitása, majd `0x0045c127`: `push "Picasa"` · `call 0x005ab210` (szakasz, kulcs, érték); a régi `Picasa.ini` (`0x00c8644c`) név ágát is kezeli |

#### Az olvasási lánc (B út) — miért éli túl az újraépítést

| lépés | cím | kiolvasott tény |
|---|---|---|
| `[Picasa]`-olvasó | `0x00441ed0` | `0x004420d3`: `P2category` kérése; **ha üres**, `0x004420fd`: visszaesés a régi **`category`** kulcsra |
| gyűjtemény feloldása | `0x00452bd0` | nem üres névnél egyenesen `0x00452cdb`-re ugrik: `0x00453970` név szerinti keresés, hiánynál `0x00452ad0` **létrehozza** a gyűjteményt. Alapértéket (`Folders on Disk` / `Other Stuff` / iPhoto) **csak üres** kategóriánál ad |
| hívók | `0x0047c560`, `0x004ada80` | a `0x0047c560` a betöltő (`0x0041ee10`, `0x0041fa3a`) és `0x0041ba40` alól minden ismert mappára (`0x00441cd0` találat + `0x00992ed0`) újraolvassa a `[Picasa]` szakaszt (`0x0047c732`); a `0x004ada80` az új album (`CAlbumState::newalbum`) útja |

⇒ Az ini a mérvadó: a `Hidden Folders` érték a következő beolvasáskor
visszaállítja a gyűjteménytagságot, adatbázistól függetlenül.

#### A db3 oldala — mérve valódi adatbázison

A `0x00415790` oszlopregisztráló a `catdata` táblát a `CThumbDB+0x760`-ra
teszi (`0x00415861`–`0x0041586d`: `push "catdata"` · `lea esi,[ebp+0x760]`).
A helyi minta (`research/testdata/Picasa2/db3`, `read_pmp_column`):

- `catdata_name.pmp` — 20 sor; a beépítettek sorrendje: `Labels`,
  `Projects (internal)`, `Folders on Disk`, `Web Albums`, `Web Drive`,
  `Exported Pictures`, `Other Stuff`, **`Hidden Folders` (7. index)**,
  `People`, utánuk a felhasználói gyűjtemények;
- `catdata_state.pmp` (20 sor), `catdata_catpri.pmp` (18 sor);
- `albumdata_category.pmp` — 2371 sor, az érték `catdata`-sorindex; a 7-es
  érték **0-szor** fordul elő.

Ez egyezik a korpusszal: a 859 `.picasa.ini` egyikében sincs
`P2category=Hidden Folders` — a mintagazdának nincs rejtett mappája. A
gyűjteménytagság tehát a db3-ban is megvan, de onnan **nem** kell átvenni:
az ini hordozza.

#### A „Rejtett mappák" jelszava — a `catdata` `info` mezője

A `0x005eb910` jelszóút a lenyomatot (`0x00a4d420`, 32 jegyű kisbetűs hex
MD5 — `picasa-mappakezelo.md`, a jelszó-szakasz) a
`0x005ebc52`–`0x005ebc58`: `push "info"` (`0x00c812cc`) ·
`call 0x006a63f0(CThumbDB+0x760, …)` hívással a **`catdata`** tábla
`info` oszlopába írja, a `Hidden Folders` sorába; üres jelszónál
(`0x005eba5e`–`0x005eba68`) ugyanide üres értéket. A `0x005ee2a0`
elrejtéskor (`0x005ee4f9`–`0x005ee537`) az `info`-t olvassa vissza, és ha
nem üres, a `catdata` `state` mezőjét állítja.

⇒ A jelszó a **db3-ban** él, nem az ini-ben: a db3 törlésével elvész, a
Picasa-átvétel pedig a `catdata` `Hidden Folders` sorának `info` értékéből
veheti át. A helyi mintában `catdata_info.pmp` nincs (jelszót sosem
állítottak be), ezért a fájl neve a `<tábla>_<oszlop>.pmp` konvencióból
következik, mintán nem látott — ld. a nyitott pontot alább.

#### Egy viselkedési részlet, ami könnyen elcsúszik

A megjelenítés **nem** az elrejtés előtti gyűjteménybe tesz vissza: a
`0x005ee300` ág feltétel nélkül `Folders on Disk`-et ír. Egy `Other Stuff`
vagy egyéni gyűjteményből elrejtett mappa tehát megjelenítés után a
**Mappák** között lesz.

#### Kizárt jelöltek (ne járja újra a következő kör)

- A `hidden=yes` (`0x00710080`, `0x00456610`) **képszintű** — a korpusz
  mind a hat előfordulása képszakaszban áll (`[<fájl>.JPG]` alatt).
- A `0x0040cd10` a sérült képek `Hide Files` párbeszéde
  (`CThumbUI::GetBadImages`), nem mapparejtés.
- Registry: a láncban (`0x005ee2a0` → `0x00445b80` → `0x0045c0a0`) nincs
  `Reg*` hívás; az egyetlen beállítás-olvasás a `Preferences\DoNotConfirmHiddenPwd`
  (`0x005ee3af`), ami a jelszó-felajánló párbeszéd „ne kérdezze újra"
  jelölője, nem a rejtés állapota.

#### Nálunk ma — az eltérés

| | eredeti | PicasaPy (`5ea930822`) |
|---|---|---|
| rejtés tárolója | `.picasa.ini` `[Picasa] P2category=Hidden Folders` | csak SQLite `folders.hidden` (`index/queries.py` `set_folder_hidden`, `app/controller.py` `toggleFolderHidden`) |
| újraépítés után | megmarad | **elvész** (`folders.hidden` alapértéke 0) |
| megjelenítés | `P2category=Folders on Disk` | `folders.hidden=0` |
| Picasában rejtett mappa nálunk | — | a `P2category=Hidden Folders` mappát az `is_custom_collection_category` **egyéni gyűjteménynek** sorolja (a `Hidden Folders` nincs a `_BUILTIN_CATEGORIES`-ban), tehát **látható** „Hidden Folders" nevű egyéni gyűjteményként jelenik meg |
| `category=` visszaesés | `P2category` üresnél a `category` kulcs | a `read_folder_category` csak a `P2category`-t olvassa |
| jelszó | db3 `catdata` `Hidden Folders` sor `info` (hex MD5) | `QSettings` `view/hiddenPasswordHash`; a Picasa-import a rejtett mappa `catdata.info` értékét átveszi (`picasa_import_controller.py`), felhasználói gyűjteményekét nem |

#### Nyitott kérdések mérlege (32.3.1)

- **LEZÁRVA** — a mappa rejtésének tárolója: `.picasa.ini`
  `[Picasa] P2category=Hidden Folders` (A és B út, fent).
- **LEZÁRVA** — túléli-e az újraépítést: igen, a `0x00441ed0` →
  `0x00452bd0` olvasó a nevet adatbázistól függetlenül veszi át.
- **LEZÁRVA** — a jelszó helye: db3 `catdata` `info` oszlop, a
  `Hidden Folders` sorában (`0x005ebc52`, `0x00415866`).
- **NYITOTT (örökölt, nem blokkoló)** — a jelszóoszlop fájlneve mintán:
  `catdata_info.pmp` a konvenció szerint; megszerzés: egy Colab-futás az
  eredeti Picasával (mappa elrejtése + jelszó megadása, utána a `db3`
  fájllistája és a `catdata_info.pmp` tartalma).
- **NYITOTT (örökölt, nem blokkoló)** — hiányzó `.picasa.ini` esetén a
  `0x0045c0a0` létrehozza-e a fájlt (a `0x00410610` megnyitó `cl=1`
  argumentuma nincs értelmezve); megszerzés: ugyanaz a Colab-futás egy
  ini nélküli mappán.
- **LEZÁRVA** — a gyűjtemény-név keresése (`0x00453970`) **csak az ASCII
  betűkre kis-nagybetű-tűrő**: `0x00453a46`–`0x00453a5c` az `A`–`Z`
  tartományt `+0x20`-szal kisbetűsíti mindkét oldalon, majd bájtonként
  hasonlít, a hossznak egyeznie kell (`0x00453a6b`–`0x00453a85`); vágás
  (szóköz-eltávolítás) a hasonlítóban nincs. ⇒ `hidden folders` is a
  `Hidden Folders` gyűjteménybe sorol.

- **Ismert maradék kockázat (PicasaPy-oldal, #4597):** index újraépítése és
  egyúttal tartósan olvashatatlan `.picasa.ini` esetén a mappa rejtett jelölése
  nem állítható vissza az ini-ből, ezért a mappa látható marad, amíg az ini
  olvashatóvá nem válik (a szinkron addig minden körben újrapróbálja).

- **Ismert maradék kockázat (PicasaPy-oldal, #4597):** az 1-es jelölésű (az
  ini-ben már `Hidden Folders`) mappa, amelynek az ini-je kívülről eltűnt,
  áthelyezéskor elveszíti a rejtést, mert csak a 2-es jelölés költözik az új
  útvonalra.

### 32.4 Negatív eredmények — ezeket NE járja újra a következő kör

A determinisztikus sor három tétele mérés után rendben találtatott:

| parancs | eredeti felirat | nálunk (mérve) |
|---|---|---|
| `ID_FILE_REVERT` | Rever&t / Vissz&aállítás | ✅ **él** — `PicasaMenuBar.qml:322` (`menuFileRevert`), a jelet a `Main.qml:785`, `:1009`, `:1898` fogadja, mindhárom a `saveDialogs.openRevert`-re megy. Az eredetiben négy belépési pont van (Fájl menü + három `AlbumPhoto::` helyi menü) — nálunk is több felületről elérhető. |
| `ID_PICTURE_AUTO_COLOR` | &Auto Color / &Automatikus szín | ✅ **él** — `PicasaMenuBar.qml:998-1003` (`menuBatchAutoColor`) → `batchApplyEffectRequested("autocolor")`; az effekt regisztrálva: `render/registry_data.py:134`. |
| `ID_FILE_DELETEFROMDISK` | &Delete from Disk… | ✅ **feltárva** — a viselkedése a `picasa-gyorsbillentyuk.md` 5. szakaszában van (nézetfüggő parancs), a megvalósítás a #1608/#1619 után háromágú. |

### 32.5 Egy szerkezeti eltérés, jegy nélkül

Az eredetiben az `ID_ONLINE_ACTIONS` **almenü** fogja össze a három online
parancsot (Google Fotók feltöltés, Lighthouse, HTML-oldal). Nálunk ezek a
mappa-menüben **laposan** állnak; az `AlbumContextMenu.qml:107` viszont ismeri
az „Online Actions" csoportot. Ez apró, önmagában nem indokol jegyet —
**a következő kör, amelyik a mappa-menühöz nyúl, vigye át** a csoportosítást
az album-menü mintájára.

---

## 33. tétel — a KÉP menü: a „Csoportos szerkesztés" kilenc parancsa + a GEOTAG (2026-08-30)

A menü-lefedettségi mérés determinisztikus sora a `ID_PICTURE_*` ötöst adta
(`AUTO_LIGHTING`, `AUTO_REDEYE`, `ENHANCE`, `FILM_GRAIN`, `GEOTAG`). A
feltárás közben a **teljes Kép-menü** parancsazonosító-térképe kijött
(16 tétel + az almenü), ezért itt a teljes leképezés szerepel — a
`?`-ként megjelölt „néma" tétel kivételével („Auto RedEye", ld. 33.4).

### 33.1 A parancs-térkép — cmd → kezelő, mind címmel

**Forrás:** a menüépítő `0x00559150` rekordhorgonya (a felirat-írás címe =
rekord kezdete, a `+0x0a` = parancsazonosító, a #1581 javított horgonya) +
a főablak-diszpécser (`0x005cb990`) két index/ugrótábla-párja
(`0x5cde04`→`0x5cdc30` az `0x9d44..0x9e3b` tartományra).

| tétel (eMenuPicture) | felirat-horgony | cmd | kezelő |
|---|---|---|---|
| `ID_PICTURE_AUTO_COLOR` | „&Auto Color" | `0x9d48` | `0x5cc949` |
| `ID_PICTURE_AUTO_LIGHTING` | „A&uto Contrast" | `0x9d49` | `0x5cc917` |
| *(a Kép menü „&Sepia")* | „&Sepia" | `0x9d4a` | `0x5cca47` |
| `ID_PICTURE_SHARPEN` | „S&harpen" | `0x9d4b` | `0x5cc9ad` |
| *(a Kép menü „&Black and White")* | „&Black and White" | `0x9d4c` | `0x5cca71` |
| `ID_PICTURE_WARMIFY` | „&Warmify" | `0x9d4d` | `0x5cca9e` |
| `ID_PICTURE_FILM_GRAIN` | „&Film Grain" | `0x9d4e` | `0x5ccacb` |
| `ID_PICTURE_ENHANCE` | „I'm Feeling &Lucky" | `0x9d5e` | `0x5cc97b` |
| `ID_PICTURE_AUTO_REDEYE` | „Auto Red Eye Correction" | `0x9df1` | `0x5ccb36` |

⚠️ **Két tétel cmd-je megdönti a #1434 31.–32. tételeinek egy régi
feltevését** — a „Kép menübeli Szépia/Fekete-fehér" (`0x9d4a`/`0x9d4c`)
**külön parancsok a Batch Edit almenüben**, nem a Megjelenítési mód
rádiócsoportjának a tagjai (azok `0x9d1b`/`0x9d1c`, #1409). Mindkettő
kezelője a szokásos batch-mintát követi.

A **Geotag almenü** (az Eszközök menüben, `eMenuTools::Geotag`):

| tétel | felirat | cmd | kezelő |
|---|---|---|---|
| `ID_PICTURE_GEOTAG` | „Geotag With Google Earth..." | `0x9db4` | `0x5cc825` → `0x600580` |
| `ID_VIEW_EARTH` | „View in Google Earth..." | `0x9d9e` | `0x5cc831` → `0x600670` |
| `ID_PICTURE_GEOUNTAG` | „Clear Geotags" | `0x9db5` | `0x5cc831` → `0x600670` |
| `ID_EXPORT_EARTH` | „Export to Google Earth File" | `0x9db0` | `0x5ccce6` |

*(A `0x5cc825` és a `0x5cc831` a diszpécserben két szomszédos törzs —
a `0x600580`/`0x600670` a tényleges kezelők.)*

### 33.2 A „Csoportos szerkesztés" KÖZÖS KÉTÁGÚ MINTA

A négy+ batch kezelő ugyanazt a mintát járja be:

```
call 0x579330          ; a „szerkesztő-előnézet nyitva és szabad" vizsgáló
test al, al
je   <batch-ág>
; SZERKESZTŐ-ÁG — a parancs a SZERKESZTŐPANELBE navigál:
mov edx, "editpanel/tab1" | "editpanel/tab3"     ; a fül
call 0x9cd8a0
mov edx, "editpanel/autolighting" | ...          ; a vezérlő (ahol van)
call 0x9cd8a0
; BATCH-ÁG — a kijelölés MINDEN képére alkalmaz:
mov eax, "<effekt-kulcs>"
call 0x5fe370
```

- **A `0x579330` vizsgáló** (`0x00579330`): igaz, ha a `0xd67914`
  (a szerkesztő fő állapota) nem nulla, a `editpanel/preview` panel létezik
  (`0x9c2fc0`), és annak `+0x20c` javaslóflagje 0. ⟹ **„most a szerkesztőben
  dolgozunk"**.
- **Szerkesztő-ág:** a parancs NEM alkalmaz — a szerkesztőpanel megfelelő
  fülére (tab1 = Gyakori javítások, tab3 = Fény) és a konkrét vezérlőre vált
  (`editpanel/autolighting`, `editpanel/autocolor`, `editpanel/enhance`).
  Tehát az eredeti **menüből a szerkesztő vezérlőjét nyitja meg** — nem
  duplikálja a batch-et.
- **Batch-ág:** `0x5fe370` („<effekt-kulcs>"): a kijelölt képek `filters=`
  láncára fűzi az effektet; a kulcsok: `autolight`, `autocolor`, `enhance`
  (a `0x5cc93f`/`0x5cc96c`/`0x5cc99e`-ben betöltve), `unsharp` (`0x5cc9e2`
  közös cél), `warm` (`0x5cc9e8`? — a `0x9d4d` kezelője), és a `grain`/
  `grain2` pár (33.3). A 0xF4242-es visszatérés = hiba (nincs kijelölés).

### 33.3 ⭐ A FILM_GRAIN kulcsválasztása: SHIFT-tel „grain", különben „grain2"

A FILM_GRAIN kezelője (`0x5ccacb`) a batch-ágban:

```
cmp byte ptr [0xd67849], 0
je   <grain2>
push 0x10
call GetAsyncKeyState        ; a [0xc406f8] import = USER32 GetAsyncKeyState
shr  eax, 0xf
and  al, 1                   ; a 15. bit = „a billentyű lenyomva"
mov  eax, "grain"
jne  <alkalmaz(grain)>
<grain2>: mov eax, "grain2"
<alkalmaz>: call 0x5fe370
```

- A **`0x10` = VK_SHIFT** — tehát ha a Shift lenyomva, az effekt-kulcs a
  régi `grain`, egyébként a `grain2`. **A `0xd67849` jelző meghatározza, hogy
  a shift-ág él-e egyáltalán** (0-nál mindig `grain2`).
- A `0xd67849` mért képe: globális `.data`-jelző, ~445 olvasó, két író
  (`0x576419` = 1, `0xa52e66` = al). Az írók a főablak-aktiváló/blokk
  környékén vannak — a pontos jelentése **nem megerősített** (erős:
  „a főablak/szerkesztő fókusz-állapota").
- **Nálunk:** a `menuBatchFilmGrain` MINDIG `grain2`-t hív
  (`PicasaMenuBar.qml`), a `batch_effect_controller` is csak a `grain2`-t
  ismeri a `_APPEND_NAMES`-ben. A `grain` (v1) kulcsunk nincs — a shift-ág
  nem reprodukálható, és **nincs is rá felhasználói eset** (a Shift-et a
  rács-kijelölés használja) → ld. a mérleget.

### 33.4 Az AUTO_REDEYE külön útja — nem a `0x5fe370`-es batch

*Forrás: `editpanel.tre:1059` (`editpanel/preview`).*

Az `Auto Red Eye Correction` kezelője (`0x5ccb36`) nem a közös batch-tel
megy:

```
xor ecx, ecx
mov eax, 0x5f39d0        ; a delegált kezelő
push ecx
push eax
mov eax, ebx
call 0x602100            ; a közös „kijelölésen végrehajtás" keret
```

- **A `0x602100`**: beolvassa az `AllowReadOnlyEdits` Preferences-kapcsolót,
  majd a kijelölés körét (`0x541fc0`) — a keret, amin a delegált fut.
- **A `0x5f39d0`**: az Auto RedEye kezelője; a törzse a szerkesztő-előnézet
  függvényét is használja (`editpanel/preview` + a `0x20c` flag, ugyanaz a
  minta, mint a `0x579330`-ban) — az Auto RedEye az **előnézeten** dolgozik.
- A `redeye` **string-kulcs a batch-rendszerben nem él** (a `0x5fe370`-es
  hívásokban nincs `redeye`) — a vörösszem-javítás a függvény-úton megy,
  nem a `filters=` láncon.
- **Nálunk:** `menuBatchAutoRedeye` → `batchApplyEffectRequested("redeye")`,
  a `batch_effect_controller` `toggle()`-ként kezeli (a `filters=` láncon).
  Ez a mért viselkedéssel összeegyeztethető (mindkettő a kijelölésre hat),
  az eltérés a belső út — a dev számára nincs teendő, hacsak a szerkesztő-
  előnézetes ágat nem akarjuk (33.6).

### 33.5 A Geotag almenü — Google Earth-függőség mérve

**GEOTAG** (`0x9db4` → `0x5cc825` → `0x600580`):

1. a kijelölést a `[edi+0xea4]`-ről veszi;
2. **`0x703980(0)` = a Google Earth telepítés-ellenőrzés**: a
   `CLSID\{8097D7E9-DB9E-4AEF-9B28-61D82A1DF784}\LocalServer32`
   registry-kulcsot vizsgálja (a Google Earth COM-objektum EL):
   a `0x703980` sztringjei a CLSID-t és az `InstallEarth:*` kulcsokat tartják;
3. ha nincs Google Earth → **`0x5ff930` = az InstallEarth figyelmeztető
   párbeszéd**: *„In order to use the geotagging features in Picasa, you
   will need to install/upgrade to the latest version of Google Earth.
   Click 'Learn More...' to go to the Google Earth home page."* —
   gombok: Cancel · Continue/Launch · Learn More... → `http://earth.google.com`
   (`InstallEarth:message_install` a hiányra, `InstallEarth:message_update`
   a frissítésre);
4. ha megvan → a geotag-objektum (`[edi+0xdb0]`) inicializálása
   (`0xc0769f`, `0x6fe800`) és a kijelölt képek továbbítása.

**GEOUNTAG** (`0x9db5` → `0x600670`): **megerősítő párbeszéd** a
`ClearGeoTag::warn` kulccsal (Igen/Nem), utána törlés.

**Nálunk (mérve):** a Geotag almenü (`PicasaMenuBar.qml`, „#530" blokk) az
`Export to Google Earth File` és a `View in Google Earth...` tételeket
tartja (a #530/#1589 szerint, saját `export/kml.py` motorral). **A „Geotag
With Google Earth..." és a „Clear Geotags" tétel hiányzik** — a törlés
tételét a #1404 már jegyzi. A Google Earth-függő belépés (CLSID-ellenőrzés +
InstallEarth-párbeszéd) Linuxon nem reprodukálandó — hatókörön kívül.

### 33.6 Eredeti / nálunk / teendő (mind mérve)

| parancs | az EREDETI (a binárisból) | nálunk (mérve) | teendő |
|---|---|---|---|
| `AUTO_LIGHTING` | szerkesztő-navigáció **vagy** batch `autolight` | `menuBatchAutoContrast` → `applyEffectMany("autolight")` — **mindig batch** | a szerkesztő-ág hiányzik — nincs teendő addig, amíg a Kép menü a szerkesztőben is él (lásd alább) |
| `AUTO_REDEYE` | `0x602100(0x5f39d0)` keret, előnézet-mintával | `menuBatchAutoRedeye` → `"redeye"` toggle | egyik irányba sem kell most |
| `ENHANCE` | szerkesztő-navigáció **vagy** batch `enhance` | `menuBatchEnhance` → `"enhance"` | ua. |
| `FILM_GRAIN` | batch `grain`/`grain2`, Shift-függő | `menuBatchFilmGrain` → **mindig** `grain2` | a `grain` (v1) nincs nálunk; a shift-ág kihagyása hatókörön kívül (nincs felhasználói út) |
| `GEOTAG` | Google Earth-ellenőrzés + InstallEarth-párbeszéd | **nincs tétel** | hatókörön kívül (Linux, a Google Earth-integráció halott); a meglévő `kml`-exportunk #530/#1589 marad |
| `GEOUNTAG` | megerősítés + törlés | **nincs tétel** | **#1404** — a megerősítő-kulcs (`ClearGeoTag::warn`) most már ismert |

**A szerkesztő-ág (33.2) eldöntéséhez mérni kell, hogy a Kép menü él-e a
szerkesztőnézetben nálunk** (a `photoActionsEnabled` + a `PicasaMenuBar`
láthatósága a `PhotoViewer`-rel) — ez a **#1502-es frissítés** dolga, nem
külön jegy addig, amíg az élő menü-eltérés nem látszik a képernyőn.

### 33.7 Nyitott kérdések mérlege

```
Nyitott kérdések: 0 nyílt · 9 lezárva · 0 blokkolt · 2 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA** (mind címmel): a 8 parancs cmd→kezelő térképe (33.1); a
  kétágú mintázat (33.2); a FILM_GRAIN shift-ág (33.3); az AUTO_REDEYE
  keret-útja (33.4); a GEOTAG Google Earth-ellenőrzése és a GEOUNTAG
  megerősítése (33.5).
- **HATÓKÖRÖN KÍVÜL:** a `grain` (v1) shift-ág reprodukciója (33.3) —
  nincs felhasználói út; a GEOTAG InstallEarth-párbeszéd (33.5) — Linuxon
  értelmét vesztett Google Earth-integráció. *A döntés a lelet alapján
  kézenfekvő, tulajdonosi jóváhagyást a #1404-gyel együtt kér.*

### Amit KIZÁRTAM

- **„Az 'Auto RedEye' a 0x5fe370-es batch-rendszerrel megy"** — megdőlt:
  a `redeye` kulcs a `0x5fe370` hívásláncában nincs; az út a `0x602100`
  kereten át vezet (33.4).
- **„A 0x5cc561 a GEOTAG kezelője"** — megdőlt: a táblafeloldás (1. táblás
  számolás) szerint a GEOTAG a `0x5cc825`, a `0x5cc561` a `0x9d53`-hoz
  tartozik (a táblázat téves kézi olvasása).

## 34. tétel — az öt KÉP-parancs: forgatás, visszavonás, elrejtés, arcok (2026-08-31)

A lefedettségi mérés determinisztikus sora: `ID_PICTURE_RESET_FACES`,
`ID_PICTURE_REVERT`, `ID_PICTURE_ROTATECLOCKWISE`,
`ID_PICTURE_ROTATECOUNTERCLOCKWISE`, `ID_PICTURE_UNHIDE`. Mindegyik
kezelője a főablak-diszpécserből (`0x005cb990`) olvasható — az esetek
**magát a viselkedést** adják, a menü-azonosítót pedig a 33.1-es
„javított horgony" módszere (a fordítás-eredmény írási címe = rekord
alapja, a `+0x0a` = parancsazonosító).

### 34.1 A parancs-térkép — mind hívólánccal, mind címmel

| parancs | cmd | eset | kezelő | viselkedés |
|---|---|---|---|---|
| `ROTATECLOCKWISE` („F&orgatás jobbra") | `0x9ca2` | `0x5cbd35` | `0x005eef30` | forgatás **+90°**, háttérmunkaként |
| `ROTATECOUNTERCLOCKWISE` („Forgatás &balra") | `0x9ca3` | `0x5cbd42` | `0x005eef30` | forgatás **270°** (−90°) |
| `REVERT` („Összes szerkesztés vissz&avonása") | `0x9d2d` | `0x5cbd78` | `0x005ef3e0` | megerősítés, majd az edit-tokenek törlése |
| `UNHIDE` („&Megjelenítés") | `0x9ca4` | `0x5cbd52` | `0x005e7d90` | `hidden` kulcs **törlése**, frissítés |
| *(párja:)* `ID_PICTURE_HIDE` („&Elrejtés") | `0x9ca5` | `0x5cbd5f` | `0x005e7d90` | `hidden` kulcs **írása**, frissítés |
| `RESET_FACES` („Ar&cok alaphelyzetbe állítása") | `0x9e11` | `0x5cc83c` | **módosító-gomb szerint három ág** | ld. 34.4 |

A második, helyi-menübeli pár is megvan: a menüépítő ugyanezeket a
tételket kétszer építi — egy második azonosító-párral (`HIDE`=`0x9c72`,
`UNHIDE`=`0x9cd0`, esetükben `0x5cc054`/`0x5cc069` → `0x005cb180(ebx,
1|0)`, ugyanannak a művelet másik keretből hívott változata).

> **A horgony-módszer határa (következő köröknek):** a hat kulcsból ötnél
> a javított horgony a diszpécserrel BIZTOSAN egyezik (`0x9ca2`/`0x9ca3`/
> `0x9d2d`/`0x9e11` + a második pár), de a HIDE/UNHIDE második (b)
> rekordpárját fordítva társította (`HIDE`→`0x9ca4`, holott a diszpécser
> szerint `0x9ca4` = törlés = Unhide). Az azonosító-mező mindig a
> **diszpécser-oldalról** is ellenőrizendő: a kezelő-paraméter
> (írás/törlés, 90/270) dönt, nem a menüépítő blokkja.

### 34.2 A forgatás — és a `rotate=` KULCS jelentése

A menü-forgatás a `0x005eef30`-ra fut (a `thumbui/rotateright`/
`rotateleft` névparancsok is ide érkeznek: `0x5dafcd` → `push 0x5a`,
`0x5db03c` → `push 0x10e`):

- **jobbra = 90, balra = 270** — ugyanaz a motor, fix szög;
- **háttérszálon** fut (a függvény munkaobjektumot gyárt,
  `EnterCriticalSection` + szál-id jelölés);
- őr: `IDS_MUST_SELECT_TO_ROT` („Must have selected images to rotate."),
  hiba: `IDS_ROT_TYPEFAILED` („One or more images could not be rotated
  because of the file type.").

A `rotate=` kulcs a **negyedfordulat** tárolója: a 864 ini-es korpuszban
2426 `rotate=` sor, értéke kizárólag `rotate(0)`…`rotate(3)` (1735/451/
213/27) — **szabad szög sehol**. A szabad egyenesítés (Straighten) a
`crop64` dőlése, nem a `rotate=`.

⇒ **A fotó-forgatás és a `rotate=` kulcs UGYANAZ a mechanizmus** — a
`rotate=rotate(N)` negyedfordulatot tárol, a szabad egyenesítés nem ebbe a
kulcsba való.

⛔ **ÖNHELYESBÍTÉS (2026-09-09, #1162): ez a szakasz NEM a #1162 kérdésére
válaszol.** A jegy a **kollázs téma-képesség-maszkjának** `rotate` bitjéről
szól (`collage/themes.py` 7. bit, a #1151 Keret-almenü párja), nem a
fotó-forgatás `rotate=` ini-kulcsáról. A két dolog neve egyezik, a
mechanizmusuk nem: az egyik a `.picasa.ini` negyedfordulat-tárolója, a másik
a kollázs-témák képesség-bitje. A #1162 ezen a szakaszon **nem záródott le** —
a maszkbit jelentése a `kollazs-panel-ui-spec.md`-ben áll; azt 2026-09-12-én
mértük ki (a bit a kollázs SZÓRÁSOS elhelyezését kapuzza, a fix igazítást
nem), a fokozat ott már **megerősített**.
*(Tanulság: a névegyezés nem funkcióegyezés — a lezárás előtt a jegy TÖRZSÉT
kell elolvasni, nem a kulcsszót keresni.)* A mi oldalunkon
(`photo_ops_controller.py` `_rotate_many`) a `rotate({steps})` 0..3-ig
**egyezik**; egyetlen eltérés: a videókat hallgatólagosan kihagyjuk
(#103), az eredeti `IDS_ROT_TYPEFAILED`-et ad vegyes kijelölésnél.

### 34.3 A visszavonás (Undo All Edits) — `0x005ef3e0`

1. **film** esetén külön kérdés: `CThumbUI::UndomovieEdits`
   („Remove all movie edits?");
2. **egy képre**: `IDS_CONFIRMREVERT` — „This will remove all edits you
   have made to the current picture.  Do you want to continue?", gomb:
   `Remove Edits`;
3. **több képre**: `IDS_CONFIRMREVERT_MULTIPLE` + saját gomb
   (`IDS_CONFIRMREVERT_MULTIPLE_YES_BUTTON`);
4. jóváhagyás után képenként a **különleges régió-tokenek** törlése —
   `redeye` · `retouch` · `picnik` (`0x5ef6e1`–`0x5ef877`, a `filters=`
   láncból), majd az `editpanel/preview` frissítése.

**Futásidejű mérés (job-254, #5836):** a könyvtárnézet Kép menüjéből,
EGY kijelölt képpel indítva az eredeti a **többes** szöveget mutatja
(„This will remove all edits you have made to ALL of the selected
pictures.  Do you want to continue?”), az ablakcím **„Confirm”**, a
gombok **„Remove Edits”** (alapértelmezett) és **„No”**, „Do not ask
again” jelölő nincs. A könyvtárnézetből tehát egy képnél sem a 2. pont
egyes számú szövege jön; a nézőből indított ágat nem mértük, arra a 2. pont
statikus olvasata marad érvényes. Jóváhagyás után a kép
szakaszából a `filters=` törlődik, és `backuphash=` kerül bele (job-254:
`backuphash=37968`, más kulcs nincs).

*(Megkülönböztetendő a fájlszintű Revert-től: a
`CThumbUI::FileRevert`-család (`0x0053b2e0`, „Revert to original version
of file?") az eredeti fájl visszaállítása, az Undo All Edits pedig az ini
szerkesztés-tokenjeit veszi le — két különböző művelet.)*

### 34.4 Az arcok alaphelyzetbe állítása — HÁROM ág módosító-gomb szerint

Az `0x9e11` esete (`0x5cc83c`) a billentyű-állapotot is olvassa
(`GetKeyState`):

| módosító | kezelő | mit tesz | szöveg |
|---|---|---|---|
| **sima kattintás** | `0x0057daa0` | a **kijelölés** arc-téglalapjait törli (`faces=` kulcs, `0x448560`/`0x484820`/`0x47bfd0`) | **nincs megerősítés** |
| **Ctrl+kattintás** | `0x006038b0` | `CThumbUI::RemoveAllFaceData` — MINDEN arc-adat törlése + teljes újra-arcfelismerés | „FIGYELEM! Ez a művelet TÖRLI az összes, arcokra vonatkozó adatot, a személyi albumokat, és újrakeresi az arcokat az összes fotón. A művelet egyúttal ELTÁVOLÍTHATJA a szinkronizált webalbumokban lévő névcímkéket is. Ezt szeretné tenni?" |
| **Shift+kattintás** | `0x00603a20` | `CThumbUI::ResetAllFaces` — a személyi albumok törlése, az arcok a Név nélküliek közé | „FIGYELMEZTETÉS! Ez a művelet TÖRLI az összes személyi albumot, és a Név nélküliek albumba helyezi át az arcokat. A művelet a szinkronizált webalbumokból is ELTÁVOLÍTHATJA a névcímkéket. Ezt szeretné tenni?" |

A két könyvtárszintű ág a `peoplepanel/resetfaces` névparancsot ereszti
(`0x6038b0`/`0x603a20`).

> **Helyesbítés a #422-höz:** a korábbi megfigyelés („az eredeti
> FIGYELMEZTETÉSSEL kérdez, mert az egész könyvtárra hat") az **a
> Shift/Ctrl-ágat** írta le. A sima menüpont a **kijelölésen** dolgozik,
> és a binárisban nincs figyelmeztető szövege. A mi
> `resetFacesConfirm`-ünk (mindig kérdez, könyvtárszintű szöveggel) a
> Shift-ágat másolta le — dokumentált SAJÁT döntés maradhat, de az
> eredeti három ágát a jegy rögzíti.

A felület 2026-10-08 óta a táblázat szerinti három ágat követi (#4627).

### 34.5 Az elrejtés/megjelenítés — a `hidden` kulcs

A `0x005e7d90(param)` ágai: `param=1` (Hide) a `]hidden` belső tokenet
**írja** (vtable+0x8c), `param=0` (Unhide) **törli**; utána frissítés
(`0x65b840`), és ha a szerkesztő-előnézet él, annak lezárása.

A `]`-prefix a bináris **belső token-névtere** (mint `]star`,
`]revertable`) — az ini-kulcs a korpusz szerint **`hidden=yes`**
(66563–66581. sorok), tehát a mi `photo_ops_controller.py`
(`with_value("hidden","yes")` / `with_removed`) **egyezik**.

A HIDE-oldalhoz online-album megerősítés tartozik (`0x005e7e80`):
`Sync::SimpleConfirm` („Remove online copies of these files?") /
`Sync::MultiConfirm` („Some selected files may be in multiple online
albums. Remove all online copies?"), gomb: „Remove Online Copies" —
webalbum nélkül nálunk nincs miről átvenni.

### Eredeti / nálunk / teendő — az öt parancsra

| parancs | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| Forgatás jobbra/balra | fix 90/270°, háttérszálon; nincs kijelölés → őr-szöveg; típus-hiba → üzenet | `_rotate_many`: `rotate(0..3)`, videó hallgatólagosan kihagyva | vegyes kijelölésnél az `IDS_ROT_TYPEFAILED` üzenet (kis jegy) |
| Undo All Edits | megerősítés (egy/több/film külön szöveg), régió-tokenek + `filters=` törlés | `openRevert` → `revertConfirmDialog`, `filters=` törlés | az egy/több szövegkülönböztetés a párbeszédben |
| Unhide/Hide | `hidden` kulcs írása/törlése + frissítés | **egyezik** (`hidePhotosByIds`, `with_removed`) | — |
| Reset Faces | sima = kijelölés (nincs kérdés); Ctrl = `RemoveAllFaceData`; Shift = `ResetAllFaces` | a három ág az eredeti szerint, mindkét könyvtárszintű művelet megerősítéssel és ini-/index-frissítéssel | — |

### Nyitott kérdések mérlege (34.)

```
Nyitott kérdések: 0 nyílt · 4 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **NEM ez zárta le a #1162-t** (az a kollázs-maszk bitje — ld. az
  önhelyesbítést a 34.2-ben; a jegy a `kollazs-panel-ui-spec.md` 15.
  szakaszán zárult, 2026-09-12): a `rotate=` kulcs = negyedfordulat-tároló, a menüvel
  azonos mechanizmus); a forgatás két szöge és szövegei (34.2); a
  revert szöveg-hármasa és régió-tokenjei (34.3); a Reset Faces
  három ága (34.4).
- **HATÓKÖRÖN KÍVÜL:** a `Sync::Simple/MultiConfirm` átvétele —
  webalbum-feltöltés nélkül nincs tárgya.

### Amit KIZÁRTAM

- **„A menü-forgatás a szabad forgatást írja a rotate= bitbe"** —
  megdőlt: a korpuszban kizárólag `rotate(0..3)`, a motor fix
  90/270-et kap (34.2).
- **„A Reset Faces menüpont mindig figyelmeztet"** — részben dőlt meg:
  a sima ág kijelölés-szintű és szöveg nélküli; a figyelmeztetés a
  Ctrl/Shift ágaké (34.4).
- **„A HIDE/UNHIDE az `]hidden` ini-kulcsot írja"** — pontosítva: a
  `]`-prefix belső token-név; az ini-kulcs `hidden=yes` (korpusz).

## 35. tétel — Poszter, képernyővédő, TiVo, keresés-mentés, biztonsági mentés (2026-08-31)

A lefedettségi mérés következő ötöse: `ID_POSTER`, `ID_SAVESEARCH`,
`ID_SCREENSAVER`, `ID_TIVO`, `ID_TOOLS_BACKUP` — mindegyik ugyanazzal a
módszerrel (menüépítő javított horgonya → diszpécser-eset → kezelő), plusz
a bónusz `ID_TOOLS_CONFIG_SCREENSAVER`.

### 35.1 A parancs-térkép

| menü | tétel | felirat | cmd | eset | kezelő |
|---|---|---|---|---|---|
| Létrehozás | `ID_POSTER` | „&Poszter készítése..." | `0x9d30` | `0x5cc150` | `0x00530c10` → `0x7387c0` |
| Létrehozás | `ID_SCREENSAVER` | „Hozzáadás a &képernyővédőhöz..." | `0x9d5c` | `0x5cce78` | `0x00531900` |
| LétrehozásWin *(csak Windows)* | `ID_TIVO` | „&Exportálás TiVo(r) DVR-re..." | `0x9d61` | `0x5cce6e` | `0x00536f70` → `ytITivo` akció |
| Eszközök | `ID_SAVESEARCH` | „Keresési eredmények &mentése..." | `0x9d52` | `0x5cc7ab` | `0x005d86a0` |
| Eszközök | `ID_TOOLS_BACKUP` | „&Képek biztonsági mentése..." | `0x9d38` | `0x5cbdee` | **névparancs** `thumbui/backup` |
| Eszközök *(bónusz)* | `ID_TOOLS_CONFIG_SCREENSAVER` | „Configure Screensaver..." | `0x9dc9` | `0x5ccc0a` | `0x00531ac0` |

### 35.2 Poszter — a papírméret-lista NYELVI beállítás szerint változik

A `0x00530c10` a kijelölésről felépíti a poszter-párbeszédet
(`0x7387c0`, „poster"); maga a `CPosterDlg` (`0x738800`) a
**papírméret-választót kétféle készlettel tölti** — a Windows
nyelvi/területi beállítását lekérdezve (`GetLocaleInfo`-típusú hívás,
`0x73895a`):

| területi beállítás | méret 1 | méret 2 |
|---|---|---|
| **metrikus** | **`10x15`** (beégetett sztring) | **`20x25`** (beégetett sztring) |
| **amerikai** | `CPosterDlg::size1` = **„4x6"** (fordítható) | `CPosterDlg::size2` = **„8.5x11"** (hu: **„8,5x11"**) |

A párbeszéd egy **`paper`** beállítást is olvas (utolsó választás
megőrzése — `0x73883e`–`0x738862`). A „Make Poster" a Képtálcán is
self-álló gomb: `buttonlabel:{FF04B854-3029-46ff-B762-FB9AF417F93F}` =
„Poszter készítése" (#455). Jegy: **#601**.

### 35.3 Képernyővédő — a `saverlist.txt` és a telepítés-ellenőrzés

Az eredeti Létrehozás ▸ `Add to Screensaver` parancs (`ID_SCREENSAVER`,
`0x9d5c`) a `0x00531900` kezelőhöz vezet. Album kijelölésekor megerősítést
kér (`addtosaver::warning`); elfogadás után a `0x00531a20` hozzáadja a
képeket, majd a hívó `1` argumentuma miatt a Windows képernyővédő-telepítő
útját is meghívja. A Tools ▸ `Configure Screensaver...` (`ID_TOOLS_CONFIG_SCREENSAVER`,
`0x9dc9`) ugyanerre a `0x00531ac0` kezelőre vezet.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| **Menüpont és felirat egyezik.** `0x00559150` menüfeliratai: `Add to &Screensaver...` és `Configure Screensaver...`; a `0x005cb990` diszpécser a `0x9d5c` / `0x9dc9` esetet a `0x00531900` / `0x00531ac0` címre irányítja. | `PicasaMenuBar.qml:2285-2288` és `2386-2388`: ugyanezek a menük és feliratok. | **EGYEZIK**: a felirat és a menühely lezárható. |
| **Album-megerősítés.** `0x00531900`; szövegcím `0x00c89880`: „Are you sure you want to add all of the selected album's images?". | `Main.qml:716-722`, `2900-2917`: album nézetben ugyanilyen megerősítő szöveg. | **EGYEZIK**: az albumra vonatkozó kérdés lezárható. |
| **Tagság és lista.** `0x00531a20` kezeli a `]screensaver` tokent (`0x00c811dc`) és a `#db3\saverlist.txt` fájlt (`0x00c81ae4`); ugyanezt a listaírót (`0x004755f0`) használja a `0x0041ba40` és a `0x004a82d0` is. A `0x004755f0` `%s\n` formátummal, `w` módban ír. A mért profilmappában a `saverlist.txt` **0 bájt**, ezért nem üres fájlból a sorok tartalmát nem igazolja. | `screensaver_controller.py:41-46, 65-102, 289-305`: a forrásválasztás és a menüből hozzáadott képek a PicasaPy QSettings-be (`screensaver/sources`, `screensaver/photoPaths`) kerülnek; a közvetlen hozzáadás bekapcsolja a `photos:selected` forrást. | **ELTÉR.** Ha az eredeti Picasa-állapot átvétele cél, külön importáló feladat kell. A `saverlist.txt` nem üres mintáját egy képernyővédőhöz legalább egy képet hozzáadó Picasa 3.9-profilból kell megszerezni. |
| **Az INI-kulcs kapcsolata.** A `0x004a51f0` dekompilált `CAlbumState` figyelő a `]screensaver` tokent `screensaver` kulcsra képezi (`0x00c811dc` → `0x00c81868`), majd bejegyzést keres/frissít a `0x004dd290`/`0x004dd600` állapotútján. A `0x00456610` külön metaadat-olvasó ismeri ugyanezt a kulcsot. A dekompilátum nem követi az állapotsegédeket a tényleges `.picasa.ini`-íróig, és nem igazolja, hogy a menüparancs ezt az utat kiváltja. | A PicasaPy menüútja a fenti QSettings-mezőket írja; `.picasa.ini`-kulcsot ez a kódút nem állít. | **Bizonyítottsági fok: feltételes.** A bináris kulcsleképezése igazolt; a fájlba írás és a menüút kapcsolata nyitott. Egy nem üres képszakasz `screensaver` kulcsát kell művelet előtt/után mérni, vagy a `0x004dd290`/`0x004dd600` láncot az INI-íróig követni. |
| **Hozzáadás utáni telepítés.** `0x00531900` igaz argumentummal hívja a `0x00531a20`-at; az `0x00531a20` ezután meghívja a `0x00531ac0`-at. Ez a `HKLM\Software\Google\Google Photos Screensaver\AppPath` értéket keresi, majd `rundll32.exe desk.cpl,InstallScreenSaver %s` parancsot indít; hiányzó telepítésnél „The screensaver hasn't been installed." üzenetet ad. | `Main.qml:709-714`: hozzáadás után csak „Added %1 pictures to Screensaver.” visszajelzés jelenik meg. | **ELTÉR.** Ha Windows-kompatibilitás cél, a külön telepített képernyővédő OS-útját platformfüggően kell kezelni. |
| **Konfigurálás.** A Tools-parancs diszpécsere (`0x005cb990`) a `0x00531ac0`-at hívja; az utóbbi az előző sorban leírt Windows `desk.cpl` telepítő/beállító belépést indítja. A képernyővédő saját beállítómezői nem követhetők ebből a hívásból. | `Main.qml:2135`, `2890-2897`: a saját `ScreensaverDialog.qml` nyílik meg. | **ELTÉR.** A helyi QML-beállító nem az eredeti Windows-rendszerút. Az eredeti külön program mezőihez lásd az alábbi `NINCS MEG` sort. |
| **Az eredeti képernyővédő beállításai, alapértékei és képi kimenete: NINCS MEG.** A `0x00531ac0` az `AppPath` értékhez irányít, de az érték által mutatott program nincs a kutatási példányban. Megszerzés: egy működő Picasa 3.9 Windows-profilból olvasd ki ezt az `AppPath` értéket, szerezd meg az általa mutatott külön programot, majd tiszta Windows-felhasználói profilon rögzítsd a beállító ablak mezőit, kezdőértékeit és a futó kimenetet. | **Mérés a PicasaPy-forráskódban:** `ScreensaverDialog.qml:22-28, 40-59, 171-237`; `screensaver_controller.py:105-117, 179-193`; `screensaver_idle.py:39-41`. Effektusok `Cut`, `Dissolve`, `Dissolve through black`, `Dissolve through white`, `Pan and Zoom`; 1-30 mp, alap 3 mp; felirat alapból be; tétlenség 1-120 perc, alap 10 perc. Első forrásválasztáskor a figyelt gyökerek, ezek hiányában az összes nem üres mappa indul kijelölve (`screensaver_controller.py:105-117`). | **NINCS MEG**: a külső program és tiszta profilos mérés nélkül eredeti értéket nem szabad átvenni vagy becsülni. |
| **Régi profil migrációja.** A `0x0040e180` a `Preferences\SaverUpgradedTo25` jelzőt ellenőrzi, feloldja az `IDS_SCREENSAVERFOLDER` erőforrást, majd a `0x004f7fc0`-t hívja. A `0x004f7fc0` null/üres bemeneti út esetén `4`-et ad vissza; nem üres úton a kimeneti gyűjteményt építi és `0` státusszal tér vissza. A `0x0040e180` nulla státusznál hívja a `0x00531a20`-at; ez nem üres gyűjteménynél a `0x004755f0` listaírónak adja át a `#db3\saverlist.txt` fájlt és a `]screensaver` kulcsot. Ha a `0x00531a20` is nullával tér vissza, a hívó beállítja a migrációs jelzőt. A mappából kiválasztott rekordok pontos tartalma **NINCS MEG**. | A képernyővédő forrásait a fenti PicasaPy QSettings és az index adja; megfelelő régi profil-migráció nincs. | **Bizonyítottsági fok: feltételes.** A státusz- és íróág címmel követhető; a gyűjtemény elemeinek pontos kiválasztási feltétele és az élő migráció eredménye nincs megmérve. |
| **Automatikus indítás/kimenet.** A `desk.cpl`-út Windows képernyővédő-telepítést indít; az eredeti program idle-küszöbe, alapértéke és vetítési viselkedése **NINCS MEG** (megszerzés az előző AppPath-programmal és a Windows beállítófelületén). | `ScreensaverWindow.qml:9-47` teljes képernyős, fekete ablakot és ismétlődő, zene nélküli vetítést indít. A `SlideshowView.qml:248-260, 687-723, 907-936` **250 ms** után egér- vagy billentyűbevitelre kilép (`mérés` a forráskódban: `screensaverInputTimer.interval`, `SlideshowView.qml:687-692`). A `swayidle`-alapú tétlenségindítás csak támogatott wlroots Wayland-asztalon érhető el; saját autostart-bejegyzés nélkül alapból ki van kapcsolva (`screensaver_idle.py:36-55, 88-101, 284-293`). | **NYITOTT.** Az eredeti külső program futó kimenetével és a Windows képernyővédő-beállításaival kell összevetni. |

**Bizonyítottsági fok: feltételes.** A `0x004a51f0` token→kulcs állapotfrissítése és a `0x0040e180` migrációs státuszút a 2026-10-24-i dekompilálással, a `0x00531a20`/`0x004755f0` célzott disassembly-jével pontosabb lett; a tényleges INI-írás, a migrált rekordok pontos halmaza, valamint a külön képernyővédő-program beállításai/alapértékei/vetítése nyitott.

**Két független út:** (A) `0x00531900` → `0x00531a20` utasításszintű nyomvonala megnevezi a tokent, a listát és az utólagos `0x00531ac0` hívást; (B) a `0x0041ba40` / `0x004a82d0` külön perzisztencia-út ugyanazt a `0x004755f0` listaírót használja, a `0x00439a80` pedig a `]screensaver` tokent külön albumnévhez köti. Az utak a DB-token/lista szerepében egyeznek.

**Cáfoló kör:** azt az állítást próbáltam megdönteni, hogy a tagság csak a DB-listában létezik, `.picasa.ini`-kapcsolata nincs. A `0x004a51f0` a tokent `screensaver` kulcsra képezi, tehát a kizáró állítás megdőlt. A cáfolat ellenőrzése ugyanazzal a bizonyítási mércével: ez a binárisban látható kulcsválasztást igazolja, de az élő fájlba írást és a menüparancs azon keresztüli hatását nem; ezek nyitva maradnak.

**A #5739 migrációs ellenpróbája (2026-10-24).** Megpróbáltam cáfolni azt az olvasatot, hogy a `0x004f7fc0` nulla visszatérése azt jelenti: talált legalább egy átveendő képet. A dekompilátum a null/üres bemeneti út külön `4` státuszát mutatja, míg a `0x00531a20` disassembly-je a kimeneti gyűjtemény hosszát külön vizsgálja a listaírás előtt. Az üres gyűjtemény tehát nem azonos a helper hibastátuszával; a `0x0040e180` sikerág ettől még eljuthat a migrációs jelző beállításáig. Ez cáfolja a „nulla = talált elem” értelmezést, de az átkerülő rekordok pontos körét nem dönti el.

**A #5661-hez tartozó nyitott utak:** a külön AppPath-program tiszta profilos megszerzése; a `saverlist.txt` nem üres mintája; a migrációból kiválasztott rekordok és a hozzájuk írt sorok pontos tartalma; valamint az INI-figyelő tényleges fájlírási útja. A meglévő `picasa-ini-format.md` és `picasa-create-features.md` állításai ennek megfelelően különválasztják a felismerhető `screensaver` INI-kulcsot a bizonyított DB-listaúttól.

A Google Fotók-képernyővédő **külön telepítésű program** (#453) — a
`desk.cpl`-hívás Windows-specifikus. Jegy: **#453**, **#32**.

**Linuxos PicasaPy-változat (#4259, tulajdonosi döntés 2026-10-05):** a
Windowsos telepítés- és registry-út helyett a menüből nyitható saját
képernyővédő-beállító és előnézet készült. A források a kijelölt mappák,
albumok és a Létrehozás menüből hozzáadott képek; a beállításokat a QSettings
őrzi. Az effekt-, diaidő- és feliratbeállítás a helyi teljes képernyős
diavetítéshez tartozik. A vetítés egérmozgásra vagy billentyűre kilép.
Asztali környezeti tétlenségjelhez kötött automatikus indítás csak a
PicasaPy-ban támogatott wlroots Wayland-asztalokon érhető el. Az eredeti
külön Windowsos kiegészítő beállítómezői és alapértékei továbbra is nyitottak;
a fenti #5661-összevetés megadja a megszerzés útját.

### 35.4 TiVo-export — Windows-only menü, akció-kereten át

Az `Export to TiVo(r) DVR...` a `eMenuCreateWin` névtérből jön — **a
menü csak Windowson épül fel** (a Mac-névtérben külön kulcs él). A
kezelő (`0x00536f70`, 42 bájt) az akció-kezelőből kéri a **`ytITivo`**
akciót (`ytIAction` interfésznévvel), amelyet a `0x0069ac10`
valósít meg: regisztráció induláskor, futás közben két szövegű
folyamat-párbeszéd — `ytITivo::exportprog` („Tivo exportálás") és
`ytITivo::copyprog` („Fájlok másolása: %d%"). A TiVo-protokoll
(hálózati felderítés, .tivo-átvitel) ennél a körnél nem lett mélyebben
kibontva.

### 35.5 Keresési eredmények mentése — a 1000-es küszöb pontosan

A `0x005d86a0` (362 bájt): az aktív keresés találatánál, ha az
**1000 felett van**, megerősítést kér:

- szöveg: `CThumbUI::SaveSearchBig` — „This will create an album with
  more than 1000 images.  Do you want to continue?"
- gomb: `CThumbUI::SaveSearchBigBtn` — **„Create Album"**

1000 alatt csendben létrehozza az albumot a keresés tartalmából. Ez a
#1405-ben már ismert viselkedés — új elemek: a **gombfelirat** és a
küszöb **feltétele** (csak afelett kérdez). A menütétel nálunk hiányzik
(#428).

### 35.6 Biztonsági mentés — `backup.xml` és `backuphash`

A `Back Up Pictures...` névparancsot ereszti (`thumbui/backup`). A
mentés állapota két, eddig nem rögzített helyen él:

| elem | bizonyíték |
|---|---|
| mentés-készletek könyve | **`backups.xml`** (TÖBBES SZÁM) a `…\Google\Picasa2\**db3**\` mappában — író `0x006759c0` (1723 b), olvasó `0x00676910` (223 b). Ld. `biztonsagi-mentes.md` 1.1 |
| a mentés-motor | a **`il_BurnPanel`** (0x67xxxx tartomány): meghajtó-felderítés („Drive Type is %s on %s", `CD-R`/`DVD-R`… debug-sztringek, „No recordable drives detected") — a klasszikus Picasa-mentés **CD/DVD-re írás** |
| a mentés **beállításai** | `0x0066f470` (923 b, **8 hívóval**) — a `Preferences` alatti **16 `option_*` kulcs** (`option_backup`, `option_manifest`, `option_convertnonjpeg`, `option_noautoruninf`, …). Teljes lista: `ajandek-cd-kimenet.md` |
| képenkénti könyvelés | `backuphash` ini-kulcs: a korpuszban **14 700 sor** (pl. `backuphash=50247`); a `-backuphash` alak a kulcs **levételét** jelzi — a #440-es „újrafuttatható, inkrementális készletek" pontosan ezen a két helyen könyvel |
| társprogram-promó | `0x0040d160`: `Software\Google\Google Photos Backup\Preferences` (`welcome_seen`, `SkipABPromo`, `LastABPromo`, `ABRepromptDays`) + `https://photos.google.com/apps` — a Picasa 3.9 végén a Google Fotók-Backup alkalmazást kínálta |

> ⛔ **HELYESBÍTÉS (2026-09-04) — ennek a szakasznak két állítása MEGDŐLT.**
>
> 1. **A `backup.xml` NEM a mentés-készletek könyve.** A `0x0066f2b0`
>    (438 b, **egyetlen** hívóval: `0x0066f58c`) a **névjegyzéket** írja:
>    a sztringjei `contacts.xml` (`0x00c90e74`) és `backup.xml`
>    (`0x00c90e94`), közte az elválasztó `\` (`0x00c80910`) ⇒ a
>    `backup.xml` a `contacts.xml` **előző példánya** ugyanabban a
>    mappában (`…\Google\Picasa2\contacts\backup.xml`, ld. ugyanennek a
>    lapnak a mentés-fejezetét). A **készletek** a `backups.xml`-ben
>    vannak, a `db3\` alatt — a `0x006759c0` sztringjei: `backups.xml`,
>    `replicates.xml`, `Picasa2Backups` (gyökérelem), `setname`,
>    `diskroot`, `bkallfiles`, `bkonlypics`, `bkonlyexif`.
> 2. **A `0x0066f470` NEM a `backup.xml` kezelője**, hanem a **beállítás-
>    tár**: a 16 `option_*` kulcs olvasója/írója. A „nyolc hívó" szám
>    helyes volt, csak rossz szerephez tartozott.
>
> A tévedés forrása a névhasonlóság (`backup.xml` ↔ `backups.xml`) és az,
> hogy mindkét függvény a `0x0066fxxx` tartományban ül.

Jegy: **#440**. *(A `thumbui/backup` névparancs és a BurnPanel közötti
azonnali launcher-lépés a sztring-matcher esethatáránál nem
egyértelműen követhető — a motor és az állapothordozók viszont megvannak.)*

### Eredeti / nálunk / teendő — az öt parancsra

| parancs | nálunk (mérve) | teendő |
|---|---|---|
| Poszter készítése | **placeholder** a Létrehozás menüben (`PicasaMenuBar.qml:1210`) | #601 folytatja; új adat: papírméret-lista nyelvi feltétellel + `paper` megőrzés |
| Hozzáadás a képernyővédőhöz | **működik** (`PicasaMenuBar.qml`, `Main.qml`) | #4259: kiválasztott képek hozzáadása QSettings-alapú helyi forráshoz |
| Exportálás TiVo DVR-re | nincs menütétel | **HATÓKÖRÖN KÍVÜL-javaslat** (Windows-only névtér, TiVo-hardver nélkül nincs haszna) — tulajdonosi jóváhagyást kér |
| Keresési eredmények mentése | a menü **tétel hiányzik** | #1405/#428; a 1000-es küszöb és a „Create Album" gombfelirat most rögzítve |
| Képek biztonsági mentése | **placeholder** (`:1267`) | #440; az állapothordozók (`backup.xml` + `backuphash`) most rögzítve |

### Nyitott kérdések mérlege (35.)

```
Nyitott kérdések: 1 nyílt · 4 lezárva · 0 blokkolt · 2 hatókörön kívül-javaslat · 0 csak-nyitva
```

- **NYÍLT**: az eredeti képernyővédő külön programjának beállításai,
  alapértékei, kimenete, valamint az INI-figyelő fájlírása (35.3).
- **LEZÁRVA** (mind címmel): a poszter papírméret-listája és nyelvi
  feltétele (35.2); a TiVo-akció kerete (35.4); a 1000-es küszöb és
  gombfelirat (35.5); a
  mentés két állapothordozója (35.6).
- **HATÓKÖRÖN KÍVÜL-JAVASLAT** (tulajdonosi döntést kér): a TiVo-export
  megvalósítása; az operációs rendszer tétlenségi jeléhez kötött automatikus
  képernyővédő-indítás és az eredeti `desk.cpl` telepítőút átvétele.

### Amit KIZÁRTAM

- **„A screensaver-tagságot kizárólag a `.picasa.ini` tárolja": nincs
  igazolva:** a vizsgált korpuszban nincs `screensaver=` minta, és a
  `#db3\saverlist.txt` külön listája ismert; ugyanakkor a `0x004a51f0`
  callback a `]screensaver` tokent `screensaver` INI-kulcsra képezi. A
  tényleges fájlírás és a menüút kapcsolata nyitott (35.3).
- **„A `0x6032f0` a backup-kezelője"** — megdőlt: az a jobbfiók-átváltó
  (`RIGHTDRAWEROFFSET`); a `thumbui/backup` matchelőágának ugrása a
  sztring-lánc matcher esethatárára esik — a valódi motor a `il_BurnPanel`
  (35.6).

## 36. tétel — Névcímke-letöltés, Mappakezelő-kapu és a LISTA-RENDEZÉS (2026-08-31)

A lefedettségi mérés következő öte: `ID_TOOLS_DOWNLOAD_FACES`,
`ID_TOOLS_INCLUDEEXCLUDEFOLDERS`, `ID_VIEWBYNAME`, `ID_VIEWBYRECENT`,
`ID_VIEWBYSIZE`. Mindhárom rendezés-parancs ugyanahhoz a
**bal hasáb-lista rendezéséhez** tartozik, ezért egy jelenségként megy.

### 36.1 ⛔ `ID_TOOLS_DOWNLOAD_FACES` — HALOTT tétel: a Picasa maga veszi ki

Az Eszközök menü `WM_INITMENU`-építője (`FUN_0056e1c0`, a menüfogantyú
`esi = [esp+0x38]`) a szomszédos tételeket `EnableMenuItem`-mel
engedélyezi/szürkíti — a névcímke-letöltést viszont **eltávolítja**:

```
0x0056f68d  push edi          ; az előző tétel (0x9df7/0x9df9) engedélyezése
0x0056f68e  push 0x9df9
0x0056f693  push esi
0x0056f694  call ebx          ; EnableMenuItem   [0xc40818]
0x0056f696  push 0            ; MF_BYCOMMAND
0x0056f698  push 0x9e10       ; ID_TOOLS_DOWNLOAD_FACES
0x0056f69d  push esi
0x0056f69e  call [0xc408b0]   ; RemoveMenu
```

A hívás **feltétel nélküli**: a `0x0056f554`–`0x0056f69e` blokkba
egyetlen ugrás vezet (`0x0056f550 jmp 0x0056f554`), és a blokkon belül
minden elágazás a közvetlenül következő címkére megy. Vagyis a
3.9.141.259-es build **minden menünyitáskor kiveszi** a
„Névcímkék letöltése a Picasa Webalbumokból" tételt.

⇒ **A tétel a binárisban megvan, a felhasználó soha nem látja.** A
Picasa Web Albums 2016-os megszűnésével a funkciónak amúgy sincs
kiszolgálója. *(Bizonyítottsági fok: **megerősített** — a
diszasszemblátum és az importfeloldás: `0xc408b0` → `USER32!RemoveMenu`,
`0xc40818` → `EnableMenuItem`, `0xc40810` → `CheckMenuItem`.)*

A `RemoveMenu` mind a kilenc hívóhelye (`0x56cf78` = `0x9ca5` Elrejtés,
`0x56cfa4` = `0x9ca4` Megjelenítés, `0x56d990` = `0xa0b5`, `0x56db44` és
`0x56dfc9` = `0xa0cb`, `0x56f69e` = `0x9e10`, `0x5e7a69` = `0x9de1`) —
csak a `0x9e10` áll elágazás nélküli úton.

### 36.2 `ID_TOOLS_INCLUDEEXCLUDEFOLDERS` — a kapu, ami szürkíti

A Mappakezelő teljes viselkedése (`watchedfolders.txt`,
`frexcludefolders.txt`, `scanlist.txt`, a `+`/`-` sorformátumok) a
`picasa-mappakezelo.md`-ben van; ide az **engedélyezési feltétel**
kerül, ami eddig sehol nem szerepelt:

```
0x0056f543  cmp ecx, edx              ; ecx = [edi+0x34a4], edx = 0
0x0056f547  cmp byte [esp+0x13], 0
0x0056f54e  mov al, 1                 ; engedélyezve
...
0x0056f562  sete dl                   ; dl = (al==0) → MF_GRAYED
0x0056f566  push 0x9caa               ; ID_TOOLS_INCLUDEEXCLUDEFOLDERS
0x0056f56c  call ebx                  ; EnableMenuItem
```

- `[esp+0x13]` forrása (`0x0056e240`–`0x0056e265`): a **`editpanel/preview`**
  csomópont keresése (`0x9c2fc0`, névsztring `0xc88a2c`), majd
  `sete [esp+0x13]` a `byte [csomópont+0x20c] == 0` feltételre.
  ⇒ **a Mappakezelő és a „Mappa hozzáadása…" SZÜRKE, amíg a
  szerkesztő-előnézet aktív állapotban van.** Ugyanez a kapu szürkíti a
  `0x9d38`, `0x9d3a`, `0x9d9d`, `0x9daf`, `0x9df0`, `0x9dc9` tételeket is.
- `[edi+0x34a4]` **ebben a buildben mindig 0**: a teljes fájlban egyetlen
  írása van, a konstruktorban (`0x00564c6e`, `mov [ebp+0x34a4], ebx`,
  ahol `ebx = 0`); sem `mov imm`, sem más regiszteres írás nem létezik rá.
  ⇒ **kikapcsolt (korlátozott módú) jelzőbit** — a rá épülő
  `jne`-ágak sosem futnak. *(Bizonyítottsági fok: **megerősített** — a
  `.text` teljes bájtmintás átvizsgálása a `C7 8x A4 34 00 00` és
  `89 8x A4 34 00 00` alakokra.)*

A két belépési pont (Fájl ▸ „Mappa hozzáadása a Picasához…" és
Eszközök ▸ „Mappakezelő…", mindkettő `0x9caa`) a
`picasa-mappakezelo.md`-ben már rögzítve van.

### 36.3 ⭐ A lista-rendezés HÁROM állapota a REGISTRYBEN — és a 4/c
### nyitott kérdésének lezárása

A `docs/specs/picasa-konyvtar-eszkoztar-viselkedes.md` 4/c pontja a
pipa-forrásokat mezőnévvel adta meg (`[+0x2c0+0xd8]`, `+0xdc`, `+0x165`),
de **nem mondta meg, hol él az állapot két indítás között**. Megvan: a
`Preferences` registry-ág három kulcsa.

**Betöltő** — `0x004a1560` (a lista-osztály konstruktora),
`GetPreference` = `0x00407a20`, a `Preferences` sztring `0xc7eafc`:

| kulcs | sztring-cím | betöltés | célmező |
|---|---|---|---|
| **`datesort`** | `0xc83078` | `0x004a195f`–`0x004a1991` | `[obj+0xd8]` — a **lista-rendezés módja** |
| **`peoplesort`** | `0xc83084` | `0x004a198c`–`0x004a19bd` | `[obj+0xdc]` — a **személy-lista rendezése** |
| **`albumlistflip`** | `0xc83090` | `0x004a19d5`–`0x004a1a05` | `[obj+0x165]` (bájt, `setne`) — a **megfordítás** |

**Mentő** — `0x004a3790`, ugyanaz a három kulcs, ugyanabban a sorrendben,
a mezőkből visszaírva (`0x004a379e`, `0x004a37e8`, `0x004a3835`).

> ⚠️ A `datesort` kulcsnév **félrevezető**: nem logikai „dátum szerint"
> kapcsoló, hanem a **teljes módszám** tárolója (0/1/2/5).

**A `0x9e18` / `0x9e19` / `0x9e38` rejtélye ezzel LEZÁRVA.** A 4/c pont
azt írta róluk: „a menüsáv-építőben nincsenek… a ▾ menü harmadik
csoportjának 1–3. tétele", a pipa forrása `[+0x2c0+0xdc] == 0/1/2`. A
`+0xdc` = `peoplesort` ⇒ ezek a **személy-lista rendezésének** tételei,
és a feliratuk is megvan (`0x00733480`):

| cmd | `[obj+0xdc]` | felirat |
|---|---|---|
| `0x9e18` | 0 | **Sort &People by Name** |
| `0x9e19` | 1 | **Sort People by &Amount** |
| `0x9e38` | 2 | **Sort People by Top &10** |

### 36.4 A rendező hasonlítója — a „méret" BÁJT, nem darabszám

A hasonlító `0x004a7e80`-tól olvasható (ugyanaz az osztály):

- **`mode == 1` (legutóbbi változtatás):** kétszer hívja a `0x004ae0d0`-t,
  és az eredményt **`double`-ként** hasonlítja (`fld`/`fucom`) — időbélyeg.
- **`mode == 5` (méret):** a `[obj+0xc4]` táblából a `0x004507e0`
  kétszeri hívásával kér egy **kétszavas (64 bites)** értéket
  (`[eax]` + `[eax+4]`), és **magas–alacsony szó szerint** hasonlítja
  (`0x004a7f2e`–`0x004a7f54`). Darabszámhoz 64 bit nem kellene.
  ⇒ **a „Rendezés méret alapján" a mappa/album ÖSSZES BÁJTJA.**
- **A megfordítás a hasonlítón belül van:** mindkét kimeneti ág
  `cmp byte [edi+0x165], al` + `sete`/`setne` + `lea eax,[eax+eax-1]`
  (azaz ±1) — a `albumlistflip` nem külön menetben fordítja meg a listát.

### 36.5 A rendezés-tételek HÁROM menüben élnek

| menü | építő | kulcs-névtér | bizonyíték |
|---|---|---|---|
| **menüsáv ▸ Nézet** | `0x00559150` (menüsáv-építő) | `eMenuView::ID_VIEWBYDATE/RECENT/NAME/SIZE` | a négy sztring a menüsáv-építőben; a pipázója `0x00574b70`, ami **`GetSubMenu(GetMenu(hwnd), 2)`**-t vesz (`0x00574b81`–`0x00574b8a`) = a **harmadik** felső menü ⚠️ **de a menün BELÜLI helyet ez nem mondja meg** — ld. 49.1 |
| **bal hasáb ▾ előugró** | `0x005e2000` (`folderviewpopup`) | `AlbumList::ID_VIEWBY*` (feliratok: `0x00733480`) | a 4/c pont táblája |
| **album/címke helyi menü ▸ „Sort By"** | `0x00559150` | `eMenuLabelFolder::ID_DATESORT/NAMESORT/SIZESORT/REVERSESORT` + `eMenuLabelFolder::SortBy` | a hat sztring ugyanabban az építőben |

> **Megerősítés a #1595-höz, és helyesbítés a `PicasaMenuBar.qml:926`
> megjegyzéséhez.** A #1595 már kimondta, hogy **két külön rendezés-készlet**
> van (A = `ID_*SORT`, négy rövid felirat, a **Mappa** menüben; B =
> `ID_VIEWBY*`, öt hosszú felirat, a **Nézet** menüben és a bal hasábon).
> Ez a kör **független bizonyítékot** ad a B készlet menüsáv-beli helyére:
> a pipázója (`0x00574b70`) a `GetMenu(hwnd)` **2. indexű almenűjét** veszi
> (`0x00574b81`–`0x00574b8a`) — az a harmadik felső menü, a **Nézet**.
> A `PicasaMenuBar.qml:926` megjegyzése („a bal hasábé a saját menüje")
> ezért **féligazság**: a Mappanézet hármasa (`0x9db6/0x9db9/0x9db8`)
> valóban nem rendezés, de a B készlet a menüsáv Nézet menüjében **is**
> ott van. Nálunk a menüsáv Nézet menüjéből ez az öt tétel hiányzik.

### Eredeti / nálunk / teendő

| parancs | eredeti | nálunk (**mérve**) | teendő |
|---|---|---|---|
| `ID_TOOLS_DOWNLOAD_FACES` | a menüből **feltétel nélkül eltávolítva** (36.1); a kiszolgáló 2016 óta nincs | nincs se menütétel, se kód (`grep`: 0 találat) | **semmi** — hatókörön kívül, rögzítve |
| `ID_TOOLS_INCLUDEEXCLUDEFOLDERS` | két belépési pont; **szürke**, amíg a szerkesztő-előnézet aktív | mindkét belépési pont bekötve (`PicasaMenuBar.qml:405` és `:1268` → `folderManagerRequested`); **engedélyezési kapu nincs** | a szerkesztő-előnézet alatti szürkítés (kis jegy) |
| `ID_VIEWBYNAME` (`0x9c8c`, mód 2) | `Preferences\datesort=2`, kis-nagybetű-független név | `view/paneSort="name"`, `casefold()` (`models.py:267`) | — |
| `ID_VIEWBYRECENT` (`0x9cbd`, mód 1) | `datesort=1`, `double` időbélyeg | `view/paneSort="changed"` (`models.py:271`) | — |
| `ID_VIEWBYSIZE` (`0x9dc8`, mód 5) | `datesort=5`, **64 bites bájtösszeg** | `view/paneSort="size"`, `COALESCE(SUM(p.size),0)` (`models.py:50`) — **egyezik** | — |
| `ID_VIEWREVERSE` (`0xa0cf`) | `albumlistflip`, a **hasonlítón belül** | `view/paneSortReverse` (`controller.py:409`) | — |
| a három tétel helye | menüsáv Nézet + ▾ előugró + album helyi menü (36.5) | **csak** a bal hasáb helyi menüje (`FolderListContextMenu.qml`) | a menüsáv `Nézet` menüjébe is (jegy) |
| személy-rendezés (`0x9e18/19/38`) | `Preferences\peoplesort` 0/1/2, három tétel | **nincs** — a Személyek panelen nincs rendezés-menü | új jegy |

### Nyitott kérdések mérlege (36.)

```
Nyitott kérdések: 0 nyílt · 6 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a `DOWNLOAD_FACES` sorsa (36.1); a Mappakezelő
  engedélyezési kapuja és a `+0x34a4` holt jelzőbit (36.2); a rendezés
  három registry-kulcsa (36.3); a `0x9e18/0x9e19/0x9e38` azonosítása —
  a 4/c pont utolsó nyitott tétele (36.3); a „méret" mértékegysége és a
  megfordítás helye (36.4); a rendezés-tételek három menüje (36.5).
- **HATÓKÖRÖN KÍVÜL:** `ID_TOOLS_DOWNLOAD_FACES` megvalósítása — az
  eredeti maga veszi ki a menüből, a kiszolgáló megszűnt.

### Amit KIZÁRTAM

- **„A `datesort` egy logikai kapcsoló (dátum szerint igen/nem)"** —
  megdőlt: a betöltő az egész módszámot (`0/1/2/5`) írja a `+0xd8`-ba
  (36.3).
- **„A `Rendezés méret alapján` a képek DARABSZÁMA"** — megdőlt: a
  hasonlító 64 bites értéket vet össze (36.4).
- **„A `0x9e18/0x9e19/0x9e38` egy fel nem tárt harmadik mappanézet"** —
  megdőlt: a `peoplesort` három módja (36.3).
- **„A rendezés csak a bal hasáb saját menüjében van"** (#1454
  megjegyzése) — megdőlt: a menüsáv Nézet menüjében is (36.5).
- **„A `[edi+0x34a4]` futásidejű állapot"** — megdőlt: egyetlen írása a
  konstruktorban, értéke mindig 0 (36.2).

## 37. tétel — a jobb fiók NÉGY LAPJA: rádiócsoport, és egy névütközés (2026-08-31)

A lefedettségi sor következő tételei: `ID_VIEW_PROPERTIES`,
`ID_VIEW_PEOPLE`, `ID_VIEW_PLACES` — és velük egy jelenségként a
negyedik lap, az `ID_CAPTAG`. Eddig **csak a `jobb-fiok-meretek.md`
geometria-lapjának felirat-táblájában** szerepeltek, viselkedés nélkül.

### 37.1 A parancsazonosítók — és a KERESZT-ELLENŐRZÉSÜK

A menüsáv-építőből (`0x00559150`) a 33.1-es „javított horgony"
módszerével (a `mov dword ptr [<rekordcím>], eax` a rekord kezdete, a
`+0x0a` word a parancsazonosító):

| kulcs | rekord | cmd |
|---|---|---|
| `eMenuView::ID_VIEW_PROPERTIES` | `0xd6e004` | **`0x9d71`** |
| `eMenuView::ID_CAPTAG` (a fiók Címkék lapja) | `0xd6e018` | **`0x9d2c`** |
| `eMenuView::ID_VIEW_PEOPLE` | `0xd6e02c` | **`0x9d6c`** |
| `eMenuView::ID_VIEW_PLACES` | `0xd6e040` | **`0x9d6d`** |

A négy rekord a tömbben **egymás után** áll (`0x14` bájtos lépésköz) —
egyetlen menücsoport.

⭐ **A társítás FÜGGETLENÜL is igazolva.** A 34.1 pont figyelmeztet, hogy a
horgony-módszer elcsúszhat. Itt nem kellett hinni neki: a `0x0065ab50`
függvény ugyanezt a négy számot **kódban** párosítja a névparancsokkal
(ld. 37.2). Két, egymástól független forrás, ugyanaz a négy szám.

### 37.2 ⛔ `ID_CAPTAG` KÉTSZER szerepel, KÉT KÜLÖNBÖZŐ azonosítóval

| előfordulás | rekord | cmd | mit csinál |
|---|---|---|---|
| **Nézet ▸ Címkék** (a jobb fiók lapja) | `0xd6e018` | **`0x9d2c`** | a fiók Címkék lapjára vált |
| **Nézet ▸ Indexkép felirata ▸ Címkék** | `0xd6de04` | **`0x9de4`** | az indexkép feliratát állítja |

⇒ **Aki csak a kulcsnevet nézi, a rossz parancsot köti be.** A `0x9de4`
az indexkép-felirat pipázójában bukkan fel (`0x00574b07`), a `0x9d2c` a
fiók-hídban (`0x0065ab98`) — a két azonosítónak semmi köze egymáshoz.

### 37.3 A híd: menüparancs → NÉVPARANCS (`0x0065ab50`)

A négy menüparancs nem közvetlenül kapcsol panelt: mindegyik egy
**névparancsot** ereszt, és mind a `0x005d9760` vezérlőt hívja
(`0x0065ab88`).

| cmd | névparancs | cím |
|---|---|---|
| `0x9d71` | `thumbui/properties_toggle` | `0x0065ab51` |
| `0x9d2c` | `thumbui/tags_toggle` | `0x0065ab98` |
| `0x9d6c` | `thumbui/people_toggle` | `0x0065aba6` |
| `0x9d6d` | `thumbui/places_toggle` | `0x0065abb4` |
| *(bónusz)* `0x9d6e` | **`editpanel/toggle_left_drawer`** | `0x0065abc2` |

Az ötödik ág ugyanennek a hídnak a része, de a **BAL** fiókot billenti —
külön parancs, külön fiók.

⇒ **Belépési pontok:** a négy menütétel **és** a négy névparancs
(vagyis a fiók fejlécének kapcsológombjai), plusz a fiók egészét
billentő `thumbui/toggle_right_drawer`.

### 37.4 ⭐ A NÉGY LAP KIZÁRÓ RÁDIÓCSOPORT — nem független kapcsoló

A vezérlő (`0x005d9760`, 1369 b) a `people_toggle` ágon
(`0x005d98ba`–`0x005d998b`) **pontosan ezt** teszi, ebben a sorrendben:

1. **elrejti a másik hármat** — `geopanel` (`0xc7ff04`), `tagpanel`
   (`0xc7fec8`), `propertiespanel` (`0xc7fea4`); mindegyik a vtable
   **`+0x68`** metódusán át;
2. **kikapcsolja a másik három fejléc-gombot** — `places_toggle`,
   `tags_toggle`, `properties_toggle` értéke `0` (`0x9cd8f0` hívások);
3. **bekapcsolja a sajátját** — `people_toggle` = `1`;
4. **megjeleníti a `peoplepanel`-t** — vtable **`+0x6c`**.

A másik három ág ugyanez a minta, felcserélt szereplőkkel.

⇒ **Egyszerre PONTOSAN EGY lap látszik.** A fiók nem tud „két lapot
nyitva" tartani, és a négyből egy mindig aktív, amíg a fiók nyitva van.

### 37.5 A `Preferences\active_metadata_tab` — HÁROM olvasó, NULLA író

A vezérlő a **belépéskor** kiolvassa a `Preferences` ág
`active_metadata_tab` kulcsát (`0x005d9781`–`0x005d9793`; kulcs-sztring
`0xc801f4`, ág-sztring `0xc7eafc`, olvasó `0x00407630`). Ugyanezt teszi a
főablak-építő (`0x0040d7ea`) és a `0x005c982f`.

**Író nincs.** Ezt két, egymástól független lekérdezés mondja ki:

1. az index `string_xrefs` táblája **három** függvényt ad
   (`0x0040d3c0`, `0x005c9740`, `0x005d9760`), mindhárom a `0x00407630`
   olvasót hívja, kétparaméteres (ág + kulcs) alakban — érték nélkül;
2. a **teljes fájl bájtmintás átvizsgálása** a kulcs-sztring címére
   (`0x00c801f4` mint 32 bites immediate) **pontosan három** találatot
   ad: `0x40d7eb`, `0x5c9830`, `0x5d9782` — vagyis nincs negyedik,
   író hivatkozás.

⇒ **A Picasa NEM jegyzi meg, melyik lap volt nyitva.** Az
`active_metadata_tab` **kézzel állítható rejtett beállítás**: a program
olvassa, de sosem írja.

*(Bizonyítottsági fok: **megerősített** a három olvasó és az író hiánya;
**feltételes** az, hogy a kulcs értékkészlete a négy lap neve — az
alapértelmezett ág értékét nem futtattuk le.)*

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| a négy menütétel | megvan, `0x9d71`/`0x9d2c`/`0x9d6c`/`0x9d6d` | mind a négy megvan (`PicasaMenuBar.qml:625/632/640/647`), `checkable`, pipás | — |
| **a lapok viszonya** | **kizáró rádiócsoport** (37.4) | **négy FÜGGETLEN kapcsoló**: `Main.qml:825/827/829/833` mind `x = !x`, és négy külön `visible:` kötés (`:1525/1556/1571/1590`) ⇒ **mind a négy nyitva lehet egyszerre, és mind a négy zárva is** | **jegy** — a rádió-viselkedés átvétele |
| a fiók fejléc-gombjai | négy névparancs (`*_toggle`) ugyanarra a vezérlőre | a menün kívül más belépési pont **nincs** mérve | a fejléc-gombok bekötése ugyanarra az útra |
| a fiók egészének billentése | `thumbui/toggle_right_drawer` | — | — |
| a lap megjegyzése | **NINCS** — olvassa, de nem írja (37.5) | nálunk sem őrzi (a `window.*PanelOpen` alapértéke `false`) | **egyezik**, ne vezessünk be tárolást |
| `ID_CAPTAG` névütközés | két azonosító, két menü (37.2) | a két tételünk külön objektumnév alatt van (`menuViewTags` és `menuViewThumbCaptionTags`) ⇒ **nem estünk bele** | — |

### Nyitott kérdések mérlege (37.)

```
Nyitott kérdések: 0 nyílt · 5 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a négy parancsazonosító, két független forrásból (37.1);
  az `ID_CAPTAG` névütközése (37.2); a menü→névparancs híd és a belépési
  pontok teljes listája (37.3); a lapok kizáró viszonya (37.4); az
  `active_metadata_tab` szerepe és az író hiánya (37.5).
- A 36. körben felvetett saját részkérdés — „a `0x00574b70` View-pipázó
  nem pipázza a négy lapot, akkor hol pipázódnak?" — **itt zárul**: nem a
  menü-pipázóban, hanem a **fiók fejléc-gombjainak** állapotában
  (`0x9cd8f0` hívások, 37.4); a menütétel pipája ebből következik.

### Amit KIZÁRTAM

- **„A négy lap négy független kapcsoló"** — megdőlt: minden ág elrejti a
  másik hármat (37.4). *(Ez a mi mai megvalósításunk feltevése volt.)*
- **„A Picasa megjegyzi az utoljára nyitott lapot"** — megdőlt: az
  `active_metadata_tab` kulcsnak **nincs írója** a binárisban (37.5).
- **„Az `ID_CAPTAG` egyértelműen a fiók Címkék lapja"** — megdőlt: két
  menüben két KÜLÖNBÖZŐ azonosítóval szerepel (37.2).

## 38. tétel — Rejtett képek (jelszó-ajánlattal), Idővonal, Háttérkép (2026-08-31)

A lefedettségi sor utolsó három tétele: `ID_VIEW_SHOWHIDDEN`,
`ID_VIEW_TIMELINE`, `ID_WALLPAPER`. A parancsazonosítókat a 33.1-es
javított horgony adta a menüsáv-építőből (`0x00559150`):

| kulcs | rekord | cmd |
|---|---|---|
| `eMenuView::ID_VIEW_TIMELINE` | `0xd6e090` | **`0x9ccc`** |
| `eMenuView::ID_VIEW_SHOWHIDDEN` | `0xd6e0e0` | **`0x9c9e`** |
| `eMenuCreate::ID_WALLPAPER` | `0xd6e5b0` | **`0x9cd2`** |

*(A `ID_WALLPAPER` névtere `eMenuCreate` — a **Létrehozás** menüé, nem a
Nézeté.)*

### 38.1 ⭐ „Mappa elrejtése": a művelet jelszót ajánl

Az `ID_VIEW_SHOWHIDDEN` nézeti állapot a `Preferences\ShowHidden` kulcsban
él; az olvasó/író `0x005c9300`-t a fő parancskezelő (`0x005cb990`) hívja.
Ez külön működés a következő, Hide/Unhide parancs után futó jelszóajánlattól.

**A `0x005cb990` parancskezelő két külön műveletből hívja** a
`0x005ee2a0`-t: a `0x9c72` „Hide Folder" ág `1`-et, a `0x9cd0` „Unhide
Folder" ág `0`-t ad át. A `0x005ee2a0` az `1` ágon választja a `Hidden
Folders` gyűjteményt, és csak akkor ajánl jelszót, ha annak `catdata.info`
mezője üres. A `0` ág `Folders on Disk`-re sorol vissza, és nem futtatja a
jelszóajánlatot. **Tehát a felajánlás a Mappa elrejtése művelethez tartozik,
nem a „Rejtett képek" nézeti kapcsoló bekapcsolásához.**

Az ajánlat párbeszédének elemei:

| elem | sztring |
|---|---|
| cím | `IDS_PROMPT_HIDDEN_PWD_TITLE` |
| üzenet | `IDS_PROMPT_HIDDEN_PWD_MESSAGE` — *„The \"Hidden Folders\" collection is not currently password protected. Would you like to add a password now?"* |
| igen-gomb | `ThumbUI::HiddenPassword::YesButton` = **„Add Password"** |
| nem-gomb | `ThumbUI::HiddenPassword::NoButton` = **„Don't Add Password"** |
| jelölőnégyzet | **„Do not ask me again."** → `Preferences\DoNotConfirmHiddenPwd` |

A függvény a `Preferences` ág mellett a `Folders on Disk`, `Hidden
Folders` és `state` sztringeket is használja — vagyis a gyűjtemény
állapotát nézi meg, mielőtt kérdez.

⇒ **A „Mappa elrejtése" művelet jelszó nélküli rejtettmappa-gyűjteménynél
felajánlja a jelszavas védelmet, és a „ne kérdezd többet"
választ külön kulcsban őrzi.** A „Rejtett képek" nézeti kapcsoló önmagában
nem indítja el ezt a felajánlást.

*(Bizonyítottsági fok: **megerősített** a parancság, a feltétel, a párbeszéd
szövegei/gombjai és a beállítás olvasása/írása. A `DoNotConfirmHiddenPwd`
hiányzó kulcsa melletti tényleges pipa-alapállapot **NINCS MEG**: a
`0x00407a20` ugyan a `0x00c7f514` címen álló `*` karaktert adja át a
beállításolvasónak, de ennek az effektív logikai értéke nem következik a
kiolvasott utasításokból.)*

### 38.2 Idővonal — egy közös „bemutató-mód" kezelő

A teljes Időrend-leírás külön lapon van: [picasa-idorend-viselkedes.md](picasa-idorend-viselkedes.md).

### 38.3 ⭐ „Beállítás asztali háttérképként" — mit ír, hova, milyen stílussal

A munkát a `0x0057aa10` (1143 b) végzi. **MÉRVE, teljes lánc:**

1. **Fájlt ír**: `picasabackground.bmp` (`0xc8ffe8`) a `Picasa`
   (`0xc7f0fc`) / `Backgrounds` (`0xc8ffc0`) mappába — a mappát a
   `CThumbUI::BackgroundsFolder` erőforrás nevezi meg. ⇒ **BMP-vé
   alakítja**, nem az eredeti fájlra mutat.
2. **Azonnal érvényesít**: `SystemParametersInfoW(0x14 /* SPI_SETDESKWALLPAPER */,
   0, <útvonal>, 0)` — `0x0057aca1`, import `0xc408d0`. Az utolsó
   paraméter **0**, tehát se `SPIF_UPDATEINIFILE`, se `SPIF_SENDWININICHANGE`.
3. **Maga írja a registryt** — `HKEY_CURRENT_USER` (`0x80000001`),
   ág: **`Control Panel\Desktop\`** (`0xc90000`), három érték:

   | érték | mit kap | cím |
   |---|---|---|
   | `Wallpaper` | a BMP teljes útvonala | `0x0057acaf` |
   | `WallpaperStyle` | **`"0"`** | `0x0057acfe` |
   | `TileWallpaper` | **`"0"`** | `0x0057ad67` |

   A `"0"` mindkettőnél a `0xc7fe6c` egykarakteres sztring.

⇒ **A háttérkép KÖZÉPRE kerül: nem csempézve (`TileWallpaper=0`) és nem
nyújtva (`WallpaperStyle=0`).** Ez a Windows „Középre" beállítása.

### Eredeti / nálunk / teendő

| parancs | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| `ID_VIEW_SHOWHIDDEN` (`0x9c9e`) | `Preferences\ShowHidden`; a nézeti kapcsoló önmagában **nem** indít jelszóajánlatot. Az ajánlat a `0x9c72` Hide Folder parancs után fut (`0x005cb990` → `0x005ee2a0`, 38.1). | A kapcsoló megvan és őrződik; zárolt állapotban feloldást kér. A jelszavas menütétel aktív a Rejtett mappáknál, de felhasználói gyűjteményeknél placeholder; automatikus jelszóajánlat és `DoNotConfirmHiddenPwd` megfelelő nincs. | **ELTÉR:** pótolni a Hide Folder utáni ajánlatot és a külön letiltási beállítást; az általános gyűjteményjelszó a #416-hoz tartozó fejlesztési bővítés. |
| `ID_VIEW_TIMELINE` (`0x9ccc`) | A 38.2.3 és 38.2.61-81 szakaszok; a job-239 képsora a `2009_majus` → `2014_november` → `2019_marcius` → `2021_eltero_fajlido` sorrendet és hónap/év-feliratot mutatja, majd `PicasaTeszt` és `Recently Updated` (38.2.81). A 2021-es címke az EXIF-hónappal egyezik a 2023-as fájlidő helyett. A részmozgásképletek QEMU-val ellenőrzöttek; pontos animációhossz és teljes képkocka-lánc nincs meg. | **#5377:** a `TimelineController` minden indexelt, nem rejtett képet `folder_path` szerint csoportosít, kártyánként a legkorábbi `record_date`-et és legfeljebb négy bélyeget adja; csak mappakategóriát épít. A QML Right/Left váltása 2000 ms, a csúszka felengedése 4000 ms; Space mappaszűrt diavetítést kér, Escape bezárja a nézetet (`src/picasapy/app/timeline_controller.py:161-252`; `TimelineView.qml:85-109,210-223`). Ez forrásleolvasás, nem futásmérés. | A négy fixture-mappa neve, darabszáma és látható időrendje a #5377 követelményeibe rögzíthető. A qshow teljes forráslistája/tokenje, a csúszka dátumértéke, az automatikus ütem, a Space utáni visszatérő kép és a teljes mozgás nyitott; ezekről a #5377 nem állíthat ismeretlen nélküli paritást a #5401 újabb futásidejű mérése előtt. |
| `ID_WALLPAPER` (`0x9cd2`) | BMP a `Picasa\Backgrounds`-ba, `SPI_SETDESKWALLPAPER`, majd három registry-érték; **középre** | **placeholder** (`PicasaMenuBar.qml:1236`, „Set as Desktop Background…") — a kollázs-oldalon van egy `wallpaper` jelző (`collage_save.py:490`), de a menüparancs halott | **ÚJ JEGY** |

### Nyitott kérdések mérlege (38.)

```
Nyitott kérdések: 2 nyílt · 4 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a három parancsazonosító (38. bevezető); a `ShowHidden`
  tárolása, a Hide Folder jelszóajánlatának hívási feltétele és teljes
  szövegkészlete (38.1); az
  Időrend `oneup`/overlay belépési útja (38.2.1); a háttérkép teljes írási
  lánca, a stílusértékekkel együtt (38.3).
- **NYITVA (`#4443`; a 2. Ghidra-köteg állapota a 38.2.6-ban):** a 38.2.3 futó mérése lezárta a képernyő képi
  összetételét. Nyitott maradt a bemeneti mappák/albumok halmaza és sorrendje,
  a jobb halom és időskála jelentése, a gombok művelete, a billentyűk, az
  animáció és a kilépés célja. Ezekhez fókuszált, eredeti Picasa-futtatás kell.
- **NYITVA:** a `DoNotConfirmHiddenPwd` hiányzó kulcsa mellett a pipa
  tényleges alapállapota. **Mi kell hozzá:** friss Windows-profilon, e kulcs
  nélkül Hide Folder parancs, a pipa kezdeti állásának és a mentett értéknek
  rögzítése; a `0x00407a20` `*` alapkaraktere önmagában nem mondja meg a
  jelölő állapotát.

### Amit KIZÁRTAM

- **„A Rejtett képek kapcsoló indítja a jelszó-ajánlatot"**: megdőlt:
  azt a Hide Folder (`0x9c72`) parancs indítja; Unhide (`0x9cd0`) és a
  `ID_VIEW_SHOWHIDDEN` ág nem (38.1).
- **„A háttérkép az eredeti képfájlra mutat"** — megdőlt: a Picasa
  **BMP-t ír** a saját `Backgrounds` mappájába, és arra mutat (38.3).
- **„A háttérkép nyújtva/csempézve kerül ki"** — megdőlt: mindkét
  registry-érték `"0"` ⇒ **középre** (38.3).
- **„A `timelineRequested` jelzésünknek van aktív fogyasztója”**: ez a
  2026-08-31-i forrásállapotban igaz volt; a #5377 óta a `Main.qml` a
  `toggleTimeline()`-t hívja rá, a Nézet-menü és `Ctrl+5` pedig aktív.

## 39. tétel — a `printoptions` panel: TIZENEGY beállítás-kulcs (2026-08-31)

*Ez az első kör az **UI-lefedettségi** axisról (#1778): a menüparancs-sor
138/138-cal kiürült, a következő forrás az eredeti felület elemleltára.
Választott panel: `printoptions` — 22 hiányzó elem, a rangsor 8. helye,
és **önmagában lezárható** (szemben az `editpanel`-lel, ami a szerkesztő
egésze).*

### 39.1 ⭐ MIT CSINÁL: tizenegy `Preferences`-kulcsot ír

A panel nem a nyomtatási munkára hat közvetlenül, hanem **tizenegy
beállítást** ír a `Preferences` registry-ágba:

| kulcs | sztring-cím | mire vonatkozik |
|---|---|---|
| `printoptions::text` | `0xcb3d14` | a felirat **forrása** (nincs / képfelirat / fájlnév / Exif) |
| `printoptions::textplacement` | `0xcb3dc4` | a felirat **helye** (kép alatt / képen / szegélyen) |
| `printoptions::textfont` | `0xcb3e10` | betűtípus — **alapérték `Arial`** (`0xc80a64`) |
| `printoptions::textsize` | `0xcb3de0` | betűméret |
| `printoptions::textcolor` | `0xcb3df8` | szövegszín |
| `printoptions::wrap` | `0xcb3db0` | szöveg tördelése |
| `printoptions::border` | `0xcb3d28` | van-e szegély |
| `printoptions::bordersize` | `0xcb3d40` | szegélyvastagság |
| `printoptions::bordercolor` | `0xcb3d5c` | szegélyszín |
| `printoptions::borderedge` | `0xcb3d78` | „csak alul" (`bottomonly_checkbox`) |
| `printoptions::evenborder` | `0xcb3d94` | „egyenletes szélességű szegély" |

**Négy függvény érinti mind a tizenegyet:**

| cím | méret | szerep |
|---|---:|---|
| `0x0085e800` | 1444 b | **az OK/Alkalmaz kezelője** — innen írja ki a rádió- és jelölő-értékeket |
| `0x0085f7a0` | 1230 b | **betöltő** — a panel megnyitásakor olvassa be mind a tizenegyet |
| `0x0085f3a0` | — | a párja (mentés/visszaállítás) |
| **`0x00776180`** | 1085 b | **a FOGYASZTÓ: a nyomtatási rajzoló** — a `printing` címtartományban, a `Preferences` mellett `Arial`/`Tahoma` betűnevekkel |

⇒ **A lánc teljes:** panel → `Preferences\printoptions::*` → a nyomtatási
rajzoló olvassa ki. A beállítás tehát **nem a nyomtatási munkához tapad**,
hanem globális és tartós.

### 39.2 A vezérlők — két rádiócsoport és négy jelölőnégyzet

A kezelő (`0x0085e800`) csomópontnevei alapján:

| csoport | tagok |
|---|---|
| **felirat forrása** (rádió) | `usenotext` · `usecaption` · `usefilename` · `useexif` |
| **felirat helye** (rádió) | `textbelowimage` · `textonimage` · `textonborder` |
| **jelölőnégyzet** | `border_checkbox` · `wrap_checkbox` · `bottomonly_checkbox` · `evenwidth_checkbox` |
| gomb | `ok` · `cancel` · `apply` |

A leltár hivatalos magyar feliratai: „Nincs szöveg" · „Képfeliratok" ·
„Exif-adatok" · „A kép alatt" · „A képen" · „A szegélyen" · „Szegély színe"
· „Csak alul" · „Egyenletes szélességű szegély" · „Szöveg tördelése" ·
„Betűtípus" · „Méret" · „Alkalmaz".

⚠️ **A `usefilename` (fájlnév) vezérlőnek a leltárban NINCS felirata** — a
kezelőben viszont ott a csomópont. A négyes rádiócsoport tehát teljes, a
felirat-leltár hiányos; a felirat a `printoptionstext.xml`-ből jön
(`0x0085d550`).

### 39.3 A tiltó állapot — indexképnél nem használható

A panelnek van saját tiltó felirata:

> `disabled_label` — *„Sorry, but these options cannot be used when printing
> contact sheets."* / **„Ezek a beállítások indexképek nyomtatásakor nem
> használhatók."**

⇒ **Indexkép-nyomtatásnál (contact sheet) a keret/felirat beállítások
kikapcsolódnak.** Ez a mi `printing/contact_sheet.py`-unkat közvetlenül
érinti.

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| a panel | önálló `printoptions` párbeszéd, 22 vezérlővel | **megvan** külön `PrintOptionsPanel.qml` panelként; az elrendezés nem az eredeti 22 vezérlő egy-az-egyben másolata | a PicasaPy-panel létezése **EGYEZIK**; teljes geometriája és nyomtatási kimenetének azonossága a #5663-ban nyitott |
| felirat/szegély a nyomaton | négyféle forrás, háromféle hely, szegély-négyes | megvan a `PrintOptionsPanel.qml` vezérlőiben és a `printing/options.py` tizenegy tartós mezőjében | a #5663 táblája összeveti az alapértékeket; a kimeneti raszter azonossága nincs mérve |
| tárolás | 11 tartós `Preferences`-kulcs | megvan 11 QSettings-kulccsal (`printing/options.py:43-77`) | a tárolt kulcsok és alapértékek **EGYEZNEK**; a Cancel nettó, tartós visszaállítási hatása nyitott |
| indexképnél | a beállítások **tiltva**, saját magyarázó szöveggel | a PicasaPy panel `contactSheet` módban letiltja a szerkesztést | funkcionális korlátozás **EGYEZIK**; a magyarázó szöveg pontos UI-paritása nincs mérve |
| a Beállítások „Nyomtatás" füle | **külön panel** | megvan (`OptionsTabPrinting.qml`); ez a nyomtató/minőség-beállítások helye, nem a `PrintOptionsPanel` | a két felület szétválasztása **EGYEZIK** |

### Nyitott kérdések mérlege (39.)

```
Nyitott kérdések: 1 nyílt · 4 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a tizenegy kulcs és a teljes írás→olvasás lánc (39.1); a
  vezérlő-készlet csoportosítása (39.2); az indexkép-tiltás és a szövege (39.3).
- **LEZÁRVA:** a tizenegy numerikus és szöveges alapérték kiolvasása, a
  39.5-ös bináris alapérték-táblával és a #5663 PicasaPy-összevetésével.
- **NYITOTT:** a „Mégse” utáni tartós érték-visszaállítás nettó hatása;
  lásd a 39.3 helyesbítését.

### Amit KIZÁRTAM

- **„A keret/felirat beállítás a nyomtatási munkához tapad"** — megdőlt:
  tizenegy tartós `Preferences`-kulcs, amit a rajzoló (`0x00776180`) minden
  nyomtatáskor újraolvas (39.1).
- **„A Beállítások »Nyomtatás« füle ugyanez a panel"** — megdőlt: két külön
  panel; a fül a nyomtató-oldali beállításoké, a `printoptions` a **nyomat
  kinézetéé**.

### 39.3 A három gomb VISELKEDÉSE: a Mégse visszaolvassa a beállításokat (2026-09-02; helyesbítve #5663)

A kezelő `0x0085e800`; a három ág **külön** viselkedik:

| elem | magyar | mit tesz | cím |
|---|---|---|---|
| `printoptions/cancel` | „Mégse" | **visszatölti mind a tizenegy beállítást** (`0x0085f7a0`), majd frissíti a nyomtatási előnézetet (`0x00745980`) és bezárja a panelt | `0x0085e8a1`–`0x0085e8e5` |
| `printoptions/apply` | „Alkalmaz" | **csak frissíti az előnézetet** (`0x00745980`) — a panel **nyitva marad** | `0x0085e937`–`0x0085e95d` |
| `printoptions/ok` | „OK" | `0x00745f50`, majd **bezárja** a panelt (`[panel+0x258]->vt[0x14](0,0)`) | `0x0085e9ab`–`0x0085e9c9` |

⭐ A bináris utasításai szerint a beállításvezérlők kezelője a saját
`Preferences`-kulcsát olvassa/írja, az „Alkalmaz” frissíti az előnézetet,
bezárás nélkül, a „Mégse” pedig meghívja a `0x0085f7a0` betöltőt, frissíti az
előnézetet és bezár. Ez **a beolvasási hívást bizonyítja, nem a tartós
visszaállítást**: ha a vezérlők korábban már kiírták az új értéket, a
betöltő ugyanazt az új értéket olvashatja vissza.

**NINCS MEG:** a „Mégse” ténylegesen visszaállítja-e a korábbi, tartós
értékeket, és az ablak X-e milyen eredményt hagy. Megszerzési út: eredeti
Windows futásban módosíts egy kulcsot, kattints a Mégse gombra, majd olvasd vissza a
`Preferences` értékét; az X-es esetet külön futásban ellenőrizd. A
PicasaPy ezzel szemben a panelnyitáskor snapshotot készít, majd Mégsére ezt
állítja vissza (`PrintOptionsPanel.qml:104-112,139-144`).

### 39.4 A két rádiócsoport ÉRTÉKKÉSZLETE — mérve

**`printoptions::text`** (a felirat forrása) — a csoport szülője
`printoptions/text_source`, az író `0x0085ebc3`:

| elem | magyar felirat | érték | cím |
|---|---|:--:|---|
| `printoptions/usenotext` | „Nincs szöveg" | **0** | `0x0085ebc1` |
| `printoptions/usecaption` | „Képfelirat" | **1** | `0x0085ec3a` |
| `printoptions/usefilename` | „Fájlnév" | **2** | `0x0085ec73` |
| `printoptions/useexif` | „Exif-adatok" | **3** | `0x0085ecaf` |

**`printoptions::textplacement`** (a felirat helye) — szülő
`printoptions/text_placement`, az író `0x0085eced`:

| elem | magyar felirat | érték | cím |
|---|---|:--:|---|
| `printoptions/textbelowimage` | „A kép alatt" | **0** | `0x0085eceb` |
| `printoptions/textonimage` | „A képen" | **1** | `0x0085ed4a` |
| `printoptions/textonborder` | „A szegélyen" | **2** | `0x0085ed83` |

> ⛔ **HELYESBÍTÉS a 39.2-höz.** Ott ez állt: *„A `usefilename` (fájlnév)
> vezérlőnek a leltárban NINCS felirata."* **Megdőlt:** a
> `referencia/ui-leltar.csv` tartalmazza a
> `printoptions/usefilename_label` sort `File name` felirattal, a
> `panel-feliratok-hu.tsv:850` pedig a magyar **„Fájlnév"** alakot. A
> négyes rádiócsoport **és** a felirat-leltár egyaránt teljes.

### 39.5 A tizenegy kulcs ALAPÉRTÉKE — a betöltőből (`0x0085f7a0`)

| kulcs | alapérték | cím |
|---|---:|---|
| `printoptions::text` | **0** (nincs szöveg) | `0x0085f8c6` |
| `printoptions::textplacement` | **0** (a kép alatt) | `0x0085f8f9` |
| `printoptions::textfont` | **`Arial`** | `0x0085f9db` |
| `printoptions::textsize` | **12** | `0x0085f962` |
| `printoptions::textcolor` | **0** | `0x0085f993` |
| `printoptions::wrap` | **0** | `0x0085f926` |
| `printoptions::border` | **0** | `0x0085f7b1` |
| `printoptions::bordersize` | **10** | `0x0085f7ef` |
| `printoptions::bordercolor` | **0** | `0x0085f826` |
| `printoptions::borderedge` | **0** (nem csak alul) | `0x0085f859` |
| `printoptions::evenborder` | **1** ⭐ | `0x0085f88c` |

⭐ **Az `evenborder` az EGYETLEN, ami 1-gyel indul** — az „Egyenletes
szélességű szegély" alapból **be van kapcsolva**.

**Független megerősítés a `.tre`-ből:** a `printoptions.tre` a
kezdőállapotot is rögzíti, és **négy vezérlőnél pontosan egyezik** a
mérttel:

| elem | `.tre` | a kulcs alapértéke | egyezik? |
|---|---|---|:--:|
| `printoptions/usenotext` | `setpressed=1` | `text = 0` | ✅ |
| `printoptions/textbelowimage` | `setpressed=1` | `textplacement = 0` | ✅ |
| `printoptions/bottomonly_checkbox` | `setpressed=0` | `borderedge = 0` | ✅ |
| `printoptions/evenwidth_checkbox` | `setpressed=1` | `evenborder = 1` | ✅ |
| `printoptions/wrap_checkbox` | `setpressed=1` | `wrap = **0**` | ❌ **ELTÉR** |

⚠️ **Az ötödik eltér, és a beállítás nyer:** a panel megnyitásakor a
betöltő (`0x0085f7a0`) minden vezérlőt a `Preferences`-ből állít be, tehát
a `.tre` `setpressed=1` értéke csak addig él, amíg a betöltő le nem fut.
Első indításkor a „Szöveg tördelése" **kikapcsolva** jelenik meg.
*Bizonyítottság: **erős** — a két forrás egymásnak ellentmond, a
sorrendet (`.tre` felépítés → betöltő) a `0x0085d550` és a `0x0085f7a0`
hívási sorrendje adja.*

### 39.6 A maradék vezérlők — a panelépítőből (`0x0085d550`, 2500 b)

| elem | mi ez | forrás |
|---|---|---|
| `printoptions/fontfamily` | betűtípus-legördülő, **`maxrows=7`** | `ui-leltar.csv` |
| `printoptions/sizelist` | betűméret-legördülő, **`maxrows=7`** | ugyanott |
| `printoptions/colorpicker_bevel` · `printoptions/colorcircle` | a **szövegszín** választója (`all_text_options` alatt) | ugyanott |
| `printoptions/text_picker_panel` | a szövegszín-paletta, **kezdetben rejtett** (`m_hidden`, `palette=0`) | ugyanott |
| `printoptions/bordercolorpicker_bevel` · `printoptions/bordercolorcircle` | a **szegélyszín** választója | ugyanott |
| `printoptions/border_picker_panel` | a szegélyszín-paletta, **kezdetben rejtett** | ugyanott |
| `printborderslider/scaleslider` (+ `/thumb`) | a **szegélyvastagság** csúszkája, `slider=2` | ugyanott |
| `printoptions/border_options` · `printoptions/all_border_options` · `printoptions/all_options` · `printoptions/all_text_options` · `printoptions/printborderslider_container` | csoport-tartók (felirat nélkül) | ugyanott |
| `printoptions/disabled_label` | **„Ezek a beállítások indexképek nyomtatásakor nem használhatók."** — a `.tre`-ben szülő nélküli, csak szöveg | `panel-feliratok-hu.tsv:861` |

**A betűméret-lista működése** (`0x0085df30`, 2165 b): a lista tartalma
**dinamikus tömb** a panelen (`[panel+0x2b4]`, elemszám `[panel+0x2b8] >> 1`),
`%d` formátummal kiírva (`0x00c81844`); a kiválasztott elem értéke megy a
`printoptions::textsize` kulcsba (`0x0085e5a2`–`0x0085e5af`). Az induló
kijelölés a **6. sor** (`0x0085d95e`), kivéve ha valamelyik elem egyezik a
tárolt mérettel (`0x0085d9a5`).

✅ **NEGATÍV eredmény:** a lista **NEM** a filmkészítő statikus
betűméret-táblájából (`0x00c7e4f0`, 8…96) jön — a `0x0085d***`–`0x0085f***`
tartomány **egyetlen** függvénye sem hivatkozik arra a címre (a teljes
tartomány diszasszemblálva ellenőrizve). A feltöltés forrása most megvan:
a panelépítő (`0x0085d8a9`) a `panel+0x2b4` tömb címét a `0x008261c0`
segédnek adja, amely a bináris `0x00c7dab8` címen lévő 16 dwordot másolja a
tömbbe (39.10).

### 39.7 Nyitott kérdések mérlege (a 39. tételre)

`0 nyílt · 7 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| mit ír a panel | **LEZÁRVA** — tizenegy `Preferences`-kulcs (39.1) |
| mi a két rádiócsoport értékkészlete | **LEZÁRVA** — 0–3 és 0–2 (39.4) |
| mik az alapértékek | **LEZÁRVA** — 39.5, `.tre`-vel keresztmérve |
| mi a különbség OK / Alkalmaz / Mégse közt | **LEZÁRVA** — 39.3 |
| van-e felirata a `usefilename`-nek | **LEZÁRVA (helyesbítés)** — van, „Fájlnév" (39.4) |
| mi a `bordersize` skálája | **LEZÁRVA** — `0 … 1024`, a csúszka `0 … 1`-ének 1024-szerese, **csonkolva** (39.9) |
| **honnan jön a betűméret-lista tartalma** | **LEZÁRVA** — a panelépítő `0x0085d8a9` a `panel+0x2b4` tömböt a `0x008261c0` segédnek adja; ez a `0x00c7dab8` címen lévő 16 dwordos táblát másolja be. A konkrét értékek: `8, 10, 12, 14, 16, 18, 20, 22, 26, 30, 36, 48, 60, 72, 84, 96` (39.10). |

### 39.8 A FELIRAT-RÉTEG és a szegélycsúszka — az i18n XML-ből (2026-09-03)

> **Bizonyítottság: megerősített** — `.tre` fájl + sor, illetve a
> `referencia/i18n-hu/printoptionstext.xml` (4202 bájt, 27 bejegyzés).

#### (a) A panel feliratai KÜLÖN FÁJLBÓL jönnek — és a fájl megvan

A panelépítő (`0x0085d550`) az **`i18n\printoptionstext.xml`**-t olvassa. Ez
a fájl **kicsomagolva ott van a kutatási anyagban**:
`referencia/i18n-hu/printoptionstext.xml`. Huszonhét bejegyzés: 24 felirat és
**3 buboréksúgó**.

**Három felirat, amit a lefedettségi lista nem nevezett meg:**

| elem | hivatalos magyar |
|---|---|
| `printoptions/border_size_label` | **„Szegély szélessége"** |
| `printoptions/border_none_label` | **„Egyik sem"** |
| `printoptions/border_max_label` | **„Maximális"** |
| `printoptions/caption_color_label` | **„Szöveg színe"** |

#### (b) ⭐ A szegélyvastagság CSÚSZKA, nem számmező

A `border_none_label` / `border_max_label` páros végpont-felirat — és a `.tre`
meg is erősíti:

```
printoptions.tre:34   printborderslider/thumb: printborderslider/scaleslider
printoptions.tre:36   printborderslider/scaleslider: root
printoptions.tre:38   Property slider 2
printoptions.tre:39   printoptions/printborderslider_container: printoptions/all_border_options
```

⇒ **`printoptions::bordersize` egy csúszka értéke** („Egyik sem" … „Maximális"),
nem beírt szám. A 39.5 az alapértékét (**10**) már kimérte; a vezérlő TÍPUSA
eddig nem volt kimondva. A csúszkának **saját névtere** van
(`printborderslider/*`), a `root` alatt — nem a panel gyereke.

#### (c) A két legördülő RUNTIME töltődik — a nyitott kérdés szűkítve

```
printoptions.tre:183  printoptions/fontfamily: printoptions/all_options
printoptions.tre:184  Property itempadding 2 2 10 2
printoptions.tre:185  Property maxrows 7
printoptions.tre:188  printoptions/sizelist: printoptions/all_options
printoptions.tre:190  Property maxrows 7
```

Mindkettő **legfeljebb 7 sort** mutat, és **egyik sem hordoz tételeket**: sem a
`.tre`-ben, sem a `printoptionstext.xml`-ben nincs egyetlen betűméret vagy
betűtípusnév sem. ⇒ a 39.7 kérdése két forrásra nézve negatív: nem a
felületleíróból és nem az i18n-fájlból. A `sizelist` tényleges forrását a
`0x008261c0` segéd és a `0x00c7dab8` tábla adja (39.10).

### 39.9 ⭐ A szegélycsúszka SKÁLÁJA — `0 … 1024` (2026-09-15, #1780)

*Forrás: a panelépítő `0x0085dc30`–`0x0085dc5a` (betöltés) és a kezelő
`0x0085e659`–`0x0085e68f` (visszaírás) · a két konstans a `.data`-ból
kiolvasva.*

A `bordersize` kulcs **nem közvetlenül** a csúszka értéke: a kettő között
egy 1024-es skálázás áll, és a két irány a két konstanssal pontosan
egymás inverze.

| irány | hol | mit tesz |
|---|---|---|
| beállítás → csúszka | `0x0085dc46` | `csúszka = bordersize × ` **`0.0009765625`** (`0xcf3f68`) = `bordersize / 1024` |
| csúszka → beállítás | `0x0085e65d` | `bordersize = csúszka × ` **`1024.0`** (`0xcf4218`) |

⇒ **A `bordersize` értékkészlete `0 … 1024`**, a csúszka pedig a szokásos
`0 … 1` normált vezérlő. Ez adja meg a `border_none_label` („Egyik sem") és
a `border_max_label` („Maximális") két végét is.

Az alapérték **10** (39.5) tehát a skála **~0,98 %**-án áll — vékony
szegély, nem a közepe.

#### (a) A visszaírás CSONKOL, nem kerekít — és ki is van mondva a kódban

A `fistp` (`0x0085e67e`) **elé** a fordító kiteszi a vezérlőszó-állítást:

```
0x0085e668  fnstcw  word ptr [esp+0xc]      ; a régi mód elmentése
0x0085e671  or      eax, 0xc00              ; kerekítés = NULLA FELÉ
0x0085e67a  fldcw   word ptr [esp+0x10]
0x0085e67e  fistp   qword ptr [esp+0x10]
0x0085e68b  fldcw   word ptr [esp+0xc]      ; a régi mód visszaállítása
```

⇒ `bordersize = trunc(csúszka × 1024)`. Ez a C-cast mintája — pontosan az,
aminek a **hiányából** a #956 arra következtetett, hogy a `0x0090e9d0`
viszont a legközelebbi egészre kerekít. A két lelet egymást erősíti: ahol a
Picasa csonkolást akar, ott **látszik** a vezérlőszó-állítás.

#### (b) A csúszka NULLÁJA kapcsolja ki a szegély-opciókat

Közvetlenül a visszaírás után (`0x0085e686`–`0x0085e694`):

```
cmp esi, ebx        ; esi = az új bordersize, ebx = 0
sete al
push eax
call 0x9cd7e0       ; a `printoptions/border_options` csoport engedélyezése
```

⇒ A „nincs szegély" állapotot **maga a nulla csúszkaállás** jelenti; nem
kell külön kikapcsoló. Fordítva is igaz: a betöltéskor, ha a `border`
bájtja (`+0x271`) nulla, a csúszka **`fldz`**-vel nullára áll
(`0x0085dc64`), függetlenül a tárolt `bordersize`-tól.

⚠️ A `bordersize` tehát **megőrzi** a régi értéket kikapcsolt szegélynél is
— a felület mutatja nullának. Aki a két mezőt egyben kezeli, elveszti a
felhasználó korábbi vastagságát.

#### (d) ⚠️ HIBÁS HIVATALOS SZÖVEG — ne vegyük át

*Forrás: `printoptions.tre:236` (`printoptions/apply`) · `printoptions.tre:242` (`printoptions/ok`).*

| elem | a hivatalos magyar buboréksúgó |
|---|---|
| `printoptions/apply` | „A kijelölt beállítások alkalmazása **a Google Fotókra**" |
| `printoptions/ok` | „A kijelölt beállítások alkalmazása **a Google Fotókra**, és a párbeszédpanel bezárása" |

Egy **nyomtatási** párbeszédben ez értelmetlen. A mondat a
`panel-feliratok-hu.tsv`-ben **csak ezen a két helyen** szerepel, tehát nem
másik panelről átvett fordítómemória-találat.

⚠️ **Amit NEM tudunk:** hogy a hiba a fordításban van-e, vagy az angol eredeti
is ezt írja. **Angol i18n-csomag nincs a kutatási anyagban** (a
`research/copy_Picasa_3_7/Picasa3/i18n/` csak `uninstall_*.html`-eket
tartalmaz) ⇒ **NINCS MEG**. A megszerzés útja: az angol `printoptionstext.xml`
kibontása a `Picasa3i18n.dll`-ből.

**A gyakorlati következmény független ettől:** a szolgáltatás megszűnt, tehát
**ezt a két buboréksúgót nem vesszük át** — nálunk a nyomtatásra kell
vonatkozniuk. A többi 25 bejegyzés változatlanul átvehető.

### 39.10 A `textsize` lista panel-ágának keresztellenőrzése (2026-09-17, #1780)

*Az értéklista már le van zárva a `picasa-ini-format.md` 8.6. szakaszában
(#2287). Ez a szakasz a `printoptions` panel saját feltöltési láncát méri
hozzá, nem új értéklistát vezet be.*

A `sizelist` listadoboz tartalmát a panelépítő nem a `.tre`-ből és nem az
i18n-erőforrásból olvassa. A `panel+0x2b4` tömb címét átadja a
`0x008261c0` segédnek. A segéd a tömb kapacitását a `[panel+0x2b8]` mezőből
kezeli, majd a `0x00c7dab8` címen lévő **16 darab, 32 bites egész** értéket
`0x40` bájton keresztül bemásolja a tömbbe:

```
0x008262b0  mov ecx, dword ptr [eax + 0xc7dab8]
0x008262b6  mov edx, dword ptr [esi]
0x008262b8  mov dword ptr [eax + edx], ecx
0x008262bb  add eax, 4
0x008262be  cmp eax, 0x40
```

A nyers PE-adatblokk (kis endian, 64 bájt) értékei:

```
8, 10, 12, 14, 16, 18, 20, 22, 26, 30, 36, 48, 60, 72, 84, 96
```

Ezután a panel `0x0085d97e`–`0x0085d991` ciklusa minden értéket `%d`-ként
formáz a listába; a kiválasztott érték a `0x0085e5a2`–`0x0085e5af` ágon a
`printoptions::textsize` kulcsba kerül. A listának tehát 16 eleme van, a
felületen egyszerre legfeljebb 7 látható (`maxrows 7`).

**Bizonyítottság:** megerősített — a célzott dekompiláció és a
`0x00c7dab8` 64 bájtos nyers PE-kiolvasása ugyanazt a 16 értéket adja.
## 40. tétel — a `printpanel`: DPI-ŐR, példányszám és a megjegyzett méret (2026-08-31)

*Második kör az UI-lefedettségi axisról (#1778). Panel: `printpanel` —
26 hiányzó elem, a rangsor 6. helye; a `printoptions` (39.) természetes
folytatása, és önmagában lezárható.*

### 40.1 ⭐ A LEGFONTOSABB: a panel FIGYELMEZTET a kis felbontásra

A `0x00745980` (1484 b) az előnézet **állapotsorát** építi, és ebben egy
olyan viselkedés lakik, amiről nálunk semmi nincs:

| sztring | erőforrás | mikor |
|---|---|---|
| **„Smallest picture: %d pixels/inch."** | `ThumbUIPrint::Smallest` | mindig — a kijelölés **legrosszabb** effektív felbontása |
| **„%d small %s found."** + **„Please review before printing."** | `ThumbUIPrint::ReviewPrompt` | ha van „kicsi" kép |
| **„You are ready to print."** | — | ha nincs |
| „picture" / „pictures" | `ThumbUIPrint::picture` / `::pictures` | egyes/többes szám a fenti mondatban |
| `%d of %d` | — | az előnézet lapszáma |
| `IDS_COPIES` | `ThumbUIPrint::PrintCount` | a példányszám-kijelzés |

⇒ **A Picasa a választott nyomatmérethez kiszámolja minden kép effektív
DPI-jét, megszámolja a „kicsiket", és nyomtatás előtt ELLENŐRZÉSRE
szólít fel.** Ez magyarázza a leltár két `reviewnowbutton` („Ellenőrzés")
gombját is.

A számot (`edi`, `[esp+0x40]`) a függvény **paraméterként kapja** — a
küszöb a hívóláncban dől el (ld. a mérleget).

### 40.2 A méretválasztó és a MEGJEGYZETT méret

Méret-gombok (`0x00743700` és `0x00743980`): `3x5button` · `4x6button` ·
`5x7button` · `8x10button` · `walletbutton` („Tárcaméret") — a
leltárban a `3.5 x 5`, `4x6`, `5x7`, `8x10` feliratokkal.

A választás **tartós**: a `0x00743980` és a `0x00744a00` egyaránt a
`Preferences` ág **`PrintLastSize`** kulcsát kezeli. ⇒ **a legutóbbi
nyomatméret két indítás közt is megmarad.**

### 40.3 A példányszám és a nyomtató-őr

- **Példányszám fotónként** (`printpanel/copieslabel`): `printpanel/addprintsbutton` /
  `printpanel/subprintsbutton` gombpár — buboréksúgójuk *„Add another copy of each
  Photo to be printed"* / *„Subtract a copy…"*. ⇒ **képenkénti**
  példányszám, nem összesített.
- **Nyomtató-őr** (`0x00744a00`): `IDS_MUST_INSTALL_PRINTER` —
  *„A printer must be installed in order to print."*
- **Előnézet-lapozás**: `prevbutton` / `nextbutton` + `previewnumber`
  (`%d of %d`).
- **Átjáró a 39. tételhez**: `captionoptionsbutton`, buboréksúgó
  *„Configure borders and text for Photos to be printed"*, felirata
  **„Szegély- és szövegopciók"** ⇒ **ez nyitja a `printoptions` panelt.**

### 40.5 ⭐ A vágás/kicsinyítés PÁR — és hogy MELYIK az alapértelmezett (2026-09-02)

A `printpanel.tre` 152–175. sora szerint a `croptoggle` és a `printpanel/fittoggle`
ugyanannak a `cropcontainer`-nek a gyereke — **két állapotú választás**,
és a `croptoggle`-ön ott áll:

```
printpanel/croptoggle: printpanel/cropcontainer
m_offsetLT
Property setpressed 1        <<<
m_hit_childlabel
```

⇒ **az alapértelmezés a „Kép méretre vágása" (Crop to Fit)** — az eredeti
Picasa alapból **levágja** a képet a nyomatarányra, nem kicsinyíti bele.
A `fittoggle`-ön nincs `setpressed`.

**A választás NEM tartós.** Két lekérdezés-alak: nyers bájtkeresés a teljes
`Picasa3.exe`-ben a `PrintCrop` / `PrintFit` / `PrintShrink` /
`PrintQuality` / `PrintOptimize` mintákra → **0 / 0 / 0 / 0 / 0** találat;
a `PrintLastSize`-ra ugyanígy → **1** (pozitív kontroll). ⇒ **csak a
nyomatméret marad meg két indítás közt; a vágás-mód és a minőség nem.**

**A váltás ÉRVÉNYTELENÍTI az előnézetet.** Az állapotsor-építő
(`0x00745980`) a `0x00745aa4`-nél kikeresi a `croptoggle` állapotát, és:

```
mov  ecx, [ebp+0xec4]
cmp  byte ptr [ecx], al      ; a TÁROLT állapottal veti össze
je   tovabb
mov  byte ptr [ecx+1], 1     ; „megváltozott" jelző
mov  byte ptr [ecx], al      ; az új állapot
```

⇒ a vágás-mód váltása **piszkosnak jelöli** az előnézetet, tehát az
újraszámolódik (és vele a DPI-figyelmeztetés is).

### 40.6 A méret- és minőség-gombok teljes készlete

A 40.2 négy méretgombot sorolt fel; a leltár és a `tooltips.tre` szerint a
készlet ennél bővebb:

| elem | felirat | buboréksúgó |
|---|---|---|
| `3x5button` | 3.5 x 5 | Print photos as a standard 3.5x5 size |
| `printpanel/4x6button` | 4 x 6 | Print photos as a standard 4x6 size |
| `printpanel/5x7button` | 5 x 7 | Print photos as a standard 5x7 size |
| `printpanel/8x10button` | 8 x 10 | Print photos as a standard 8x10 size |
| **`walletbutton`** | **Wallet** | **Print wallet-sized photos** |
| `printpanel/fullbutton` | Full Page | Print photos the same size as paper |
| **`photoindexbutton`** | *(a leltárban felirat nélkül)* | — |

És egy **minőség-pár**, ugyanabban a függvényben, mint a `PrintLastSize`
(`0x00744a00`): **`normalbutton`** és **`optimizebutton`**. Az
`optimizebutton` buboréksúgója a `tooltips.tre` 77–78. sorában **ki van
kommentezve**:

```
#Tooltip printpanel/optimizebutton
#Highest quality, uses your printer's resolution. Test on inexpensive paper first.
```

⇒ a „legjobb minőség, a nyomtató saját felbontásával" opció **létezik**, de
a súgója ebben a kiadásban ki van kapcsolva. *(Hogy maga a gomb él-e, ez a
kör nem mérte — a `0x00744a00` mindkettőt hivatkozza.)*

### 40.7 ⭐ A „Nyomtatás előtti ellenőrzés" PÁRBESZÉD (2026-09-02, a tulajdonos felvételéről)

A 40.1 azt írta le, hogy a panel **figyelmeztet** a kis felbontásra. A
tulajdonos futó Picasa 3-ból készített felvétele
(`#1953-nyomtatas-kep-kicsi.jpg`) megmutatja, hogy ez **egy teljes
párbeszéd**, nem csak egy mondat — és hogy a kiváltó gomb **nem ott van**,
ahol a 40.1 nyomán feltételeztük.

#### A gomb helye — HELYESBÍTÉS

Az „Ellenőrzés" gomb a panel **jobb alsó gombsorában** áll, a
**„Nyomtatás"** és a **„Mégse"** mellett, és **figyelmeztető háromszöget**
visel. Nem a „Legkisebb kép: … képpont/hüvelyk" állapotszöveg mellett.
A három gomb balról jobbra: **Ellenőrzés ⚠ · Nyomtatás ✔ · Mégse ✖**.

#### A párbeszéd tartalma

| elem | szövegtár-kulcs | magyar |
|---|---|---|
| magyarázat | `CPrintDlg::toosmall` | **„Néhány kép túl kicsi a jó minőségű nyomtatáshoz. Ezeket a képeket eltávolíthatja, kinyomtathatja, vagy visszavonhatja és módosíthatja a nyomtatási méretet."** |
| a lista sorai | `ThumbUIPrint::ReviewLow` (`Low Quality: %s`) | **„Alacsony minőség: %s"** |
| a kiválasztott elem minősítése | `CPrintDlg::badqual` | **„Rossz minőség (%d képpont/hüvelyk)"** |
| ha nincs kifogásolt kép | `CPrintDlg::ready` | *All of your pictures are ready to print.* |
| ha mindet eltávolították | `CPrintDlg::noneleft` | *There are no pictures left to print.* |

A párbeszéd **négy** gombja: **„Kijelölt elemek eltávolítása"** ·
**„Gyenge minőségű képek eltávolítása"** · **OK** · **Mégse**. Jobb oldalt a
kijelölt kép **előnézete**, alatta a minősítés a mért DPI-vel.

⇒ **Az ellenőrzés nem passzív:** a felhasználó a párbeszédből **ki tudja
venni** a rossz képeket a nyomtatásból — egyesével vagy egy gombbal az
összeset.

#### HÁROM minőségi fokozat, nem kettő

A minősítés `0x0085cff0` (781 b) szerint egy **tárolt bájtból** jön
(képenkénti rekord, 20 bájt lépésköz, a mező a rekord `+0x10`-én):

| a bájt értéke | szövegtár-kulcs | angol | **magyar** |
|---:|---|---|---|
| **2** | `CPrintDlg::bestqual` | Best quality (%d pixels/inch) | **„Legjobb minőség (%d képpont/hüvelyk)"** |
| **1** | `CPrintDlg::goodqual` | Good quality (%d pixels/inch) | **„Jó minőség (%d képpont/hüvelyk)"** |
| egyéb | `CPrintDlg::badqual` | Bad quality (%d pixels/inch) | **„Rossz minőség (%d képpont/hüvelyk)"** |

(`0x0085d1dd`: `cmp eax, 2` → best; `0x0085d1ee`: `cmp eax, 1` → good;
különben bad.)

#### A `[rekord+0x10]` bájt írása és a küszöbképlet (2026-10-05, #4280)

A két helper a DPI-értéket egész küszöbhöz hasonlítja: `0x0085c1e0`
`Preferences\DPIWarning` alapértéke `0x96` = **150** (`0x0085c1fa`),
`0x0085c270` `Preferences\DPISevere` alapértéke `0x64` = **100**
(`0x0085c28a`). Mindkét helper `fild threshold; fcomp qword ptr [DPI]`
utasítássorral hasonlít, majd `test ah, 0x41` / `jp` alapján akkor ad igazat,
ha `DPI >= threshold`; az egyenlőség is igaz.

`0x007451a0` mindkét helper eredményét összeadja (`0x0074523c`–`0x00745248`).
Az összeg a `[esp+0x4c]` lokális változóba kerül (`0x00745248`). A rekord
hozzáadásakor három átmeneti push miatt (`0x007454e6`, `0x007454e7`,
`0x007454fe`) az ESP `0x0c`-vel alacsonyabban áll; ezért a `0x00745513`-nál
beolvasott `[esp+0x58]` **ugyanaz az összeg** (`0x58 − 0x0c = 0x4c`), és
`CL`-ként átmegy a `0x0085c640` függvénybe.
A segéd a CL bájtot az átmeneti rekord `+0x10` mezőjébe teszi
(`0x0085c665`); a `0x0085d300` a forrás `+0x10` bájtot a cél rekord
`+0x10` mezőjébe másolja (`0x0085d38b`–`0x0085d38f`).

A tároló és az olvasó azonosságát a vtable is megerősíti: a konstruktor
`0x0085c300` a másodlagos vtable-t a `this+0xbc` helyre írja
(`0x0085c33b`); a `0x00cc37b8` RTTI/vtable sora a `0x0085cff0` metódust
tartalmazza. Az olvasó másodlagos `this+0x48` mezője így a teljes objektum
`+0x104` vektorára esik, ahová az append út ír. A `0x0085d1dd`/`0x0085d1ee`
ág a `+0x10` bájtot `2` → Best, `1` → Good, egyébként Bad értékre oldja.

| tárolt bájt | binárisbeli képződés | `CPrintDlg` felirat |
|---:|---|---|
| `2` | mindkét küszöb-helper igaz (`DPI >= 150` alapértéken) | Best |
| `1` | csak a 100-as helper igaz (`100 <= DPI < 150` alapértéken) | Good |
| `0` | egyik helper sem igaz (`DPI < 100` alapértéken) | Bad |

Ez a `CPrintDlg`-bájt út **ugyanazokat a 0/1/2 kategóriákat** adja, mint a
`ThumbUIPrint::Review*` sorcímkéi, de a két feliratcsalád külön marad:
`ReviewLow` és `CPrintDlg::badqual` nem ugyanaz a szöveg. A beállítható
küszöbök, a Review-címkék és a két bizonyítéki út összefoglalója a
[`picasa-nyomtatas.md`](picasa-nyomtatas.md) lapon van.

### 40.8 A nyomatméretek: TIZENHÉT tétel, és a magyar felület METRIKUS

A `ytPrintSizes::` szövegcsalád teljes (a `stringres` 3478–3494. sora):

| kulcs | angol | magyar |
|---|---|---|
| `e3x4` · `e3x5` · `e4x5` · `e4x6` · `e5x7` · `e8x10` | 3 x 4 … 8 x 10 | 3x4 … 8x10 |
| `e5x8cm` · `e9x13cm` · `e10x15cm` · `e13x18cm` · `e15x20cm` · `e20x25cm` | 5 x 8 cm … 20 x 25 cm | **5x8 cm … 20x25 cm** |
| `eWallet` | Wallet | **Tárcaméret** |
| `ePassport` | Passport | **Útlevél** |
| `eCDSize` | CD Cover Size | **CD-borító mérete** |
| `eContact` | Contact Sheet | **Indexképek** |
| `eFullPage` | FullPage | FullPage |

**A tulajdonos magyar Picasáján a panel a METRIKUS hatost mutatja:**
5x8 · 9x13 · 10x15 · 13x18 · 20x25 cm · Teljes oldal. Ez egybevág a #876
leletével (a nyomatméretek metrikus/angolszász ágra oszlanak).

### 40.9 ⛔ A magyar felület FELCSERÉLI a lapszámlálót

`ThumbUIPrint::PrintCount` = `%1$d of %2$d` → magyarul **`%2$d / %1$d`**.

A felvételen az előnézet lapozója **`8 / 1`**-et mutat, miközben az **első**
lapon állunk nyolcból. Vagyis magyarul a sorrend **összes / aktuális**.

⇒ Ez utólag megmagyarázza a kék infó-sáv korábban rögzített `(5 / 3)`
olvasatát is (ötképes mappa, a harmadik kép kiválasztva) — ugyanaz a
felcserélés.

### 40.4 Hatókörön kívüli elem a panelen

`froogle` — *„Search Froogle for Supplies"* / „Tartozékok keresése a
Froogle-en". A Froogle a Google 2007-ben átnevezett, majd megszűnt
termékkereső szolgáltatása. **Nem építjük meg**; a #1778 hatókör-szűrője
alá tartozik, de mivel egyetlen elem egy egyébként érvényes panelen, itt
elég kimondani.

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| **DPI-őr** | minőségi sávok és ellenőrzési állapot; számoló `0x0085c060`, panelfrissítő `0x00745980` | megvan a minőségi felülvizsgálat (`PrintDialog.qml:269-289`); a 150/100 küszöb **EGYEZIK** (`printing/dpi.py:32-55`) | az osztályozási alapértékeken nincs teendő; az összes Low eltávolítási kérdés a #5663 eltérés |
| nyomatméret-választó | 17 méret (`0x00776e20`), hat gyorsgombhely a `0x00743700` képernyőépítőben | méretlista és öt menthető gyorsgomb + Full Page (`PrintDialog.qml:652-705`); a teljes 17-es katalógus hiányos | lásd #5663 fejlesztői jegytörzs; CD méret **NINCS MEG**, megszerzés: `0x00776f0a` táblája |
| a méret megjegyzése | `Preferences\PrintLastSize`, írás `0x00744ba8`-`0x00744bba` | a `PrintController.printSize()`/`setPrintSize()` a méretet tartósan kezeli (`print_controller.py:373-398`) | **EGYEZIK** a tartós méretválasztás; nincs külön teendő |
| példányszám fotónként | +/- gombpár; alapérték `0x00860f78` | van képenkénti darabszám, alap 1 (`PrintDialog.qml:104-108`; vezérlők a párbeszédben) | **EGYEZIK** a példányszám-alapállapot és a képenkénti jelentés |
| előnézet-lapozás | `previewnumber`, `prevbutton`, `nextbutton`; `0x00745980` | lapozható előnézet és lapszám (`PrintDialog.qml:109-119`, `:466`, navigációs gombok) | **EGYEZIK** funkcionálisan; pixelpontos felület nincs mérve |
| nyomtató-őr | eredeti panel tartalmazza a telepített nyomtató nélküli figyelmeztetést | PicasaPy PDF célpontot mindig kínál; a hardvernyomtató nélküli eredeti/PicasaPy felületi válasz **NINCS MEG** | megszerzés: eredeti Windows futásban nyomtató nélküli állapot és PicasaPy azonos állapotának képernyőképe |
| szegély/szöveg gomb | a `printoptions` panelt nyitja; `0x00743980` | a párbeszéd `PrintOptionsPanel.qml`-t nyit | a panel nyitása **EGYEZIK**; tartalmi/raszter-paritás: lásd #5663 |
| `froogle` | kellékkereső belépés `0x00744750` | nincs megfelelő szolgáltatás | **hatókörön kívül** |

### Nyitott kérdések mérlege (40.)

```
Nyitott kérdések: 1 nyílt · 4 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a DPI-őr létezése, szövegei és a hozzá tartozó „Ellenőrzés"
  gombok (40.1); a `PrintLastSize` tartós méret (40.2); a képenkénti
  példányszám és a nyomtató-őr (40.3); a `captionoptionsbutton` →
  `printoptions` átjáró (40.3).
- **BLOKKOLT:** **mennyi DPI alatt számít egy kép „kicsinek".** A
  `0x00745980` a darabszámot paraméterként kapja; a küszöb a hívóláncban
  (`0x007451a0` / `0x00746170`) van, és nem egész-összehasonlítás — a
  megvizsgált konstansok mind sztring-kezelési határok (`0x7f`/`0x80`/`0xff`).
  **Mi döntené el:** (a) egy célzott dekompilációs kör a hívóláncra, vagy
  (b) élő megfigyelés — egy kis felbontású kép 8×10-re állítva, és leolvasni,
  hány DPI-nél vált át a mondat „ready to print"-ről „review"-ra.
  **Nem blokkolja a megvalósítást:** a mechanizmus (legkisebb DPI kiírása +
  „kicsik" számlálása + felszólítás) átvehető, a küszöböt magunk is
  választhatjuk, ha kimondjuk, hogy saját döntés.
- **HATÓKÖRÖN KÍVÜL:** a `froogle` gomb (40.4).

### Amit KIZÁRTAM

- **„A nyomtatási panel csak elrendezést és nyomtatót választ"** — megdőlt:
  van benne **minőség-ellenőrzés** (DPI-őr), képenkénti példányszám és
  lapozható előnézet (40.1, 40.3).
- **„A nyomatméret a nyomtatási munka része"** — megdőlt: a
  `Preferences\PrintLastSize` **tartósan** őrzi (40.2). *(Ugyanaz a minta,
  mint a 39.-nél: amit „a művelethez tapad"-nak hinnénk, az globális.)*
- **„A `0x00745980`-ban van a DPI-küszöb"** — megdőlt: a darabszámot
  paraméterként kapja.

## 41. tétel — az `acquirepanel`: a „22 hiány" nagy része TÉVES RIASZTÁS (2026-08-31)

*Harmadik kör az UI-lefedettségi axisról (#1778). Panel: `acquirepanel`
(22 hiány). **A kör legfontosabb eredménye nem az eredetiről szól, hanem
rólunk:** a mérés a funkciót meglévőnek nem látja, mert a mi
megvalósításunk **párbeszéd**, nem bal oldali panel, és az elemek
nevenként nem párosulnak.*

### 41.1 Az eredeti importálás — MIT ÍR és HOVA

| kulcs / erőforrás | mit tárol | hol |
|---|---|---|
| `Preferences\AcquirePath` | az importálás **célútvonala** | `0x00513830`, `0x006e3990` |
| `Preferences\LastImport%x` | a **korábbi célmappák listája**, indexelt kulcsokkal | `0x00516180` |
| `Preferences\acquireUseSubFolder` | almappába importáljon-e | `0x00514180`, `0x00524730` |

A cél-választó menü (`import_folder_menu`, `0x00516180`) három szakaszból
áll, elválasztókkal: **korábbi importok** (`-seperator-before-LastImports-`)
· **alapértelmezett hely** (`-seperator-before/after-default_location-`) ·
**„Choose…"** (`Acquire::ChooseFolder`).

### 41.2 ⭐ Az almappa elnevezésének HÁROM módja

A `0x005181b0` a `subfolder_menu` kezelője, és pontosan három feliratot ad:

| erőforrás | felirat | jelentés |
|---|---|---|
| `iCAcquireUI::SubFolder` | **„Enter Folder Title"** | kézzel megadott cím |
| `iCAcquireUI::AutoDate` | **„Date Taken (YYYY-MM-DD)"** | a felvétel dátuma szerint, külön mappákba |
| `iCAcquireUI::TodayDate` | **„%s (Today)"** | a mai dátum |

⇒ **A dátum-formátum kimondva `YYYY-MM-DD`.**

### 41.3 A kártya-törlés és a másodpéldány-szűrés

- **Másodpéldány-szűrés saját szálon**: `AcquireDupeCheckThread`
  (`0x00513680`); üzenete *„… will not be imported because it is a
  duplicate already in Picasa."* (egyes és többes szám külön).
- **Kártya-törlés import után** (`0x00519720`): *„%d files will be erased
  after import."* · *„An unknown number of files will be erased…"* ·
  megerősítés: **„Are you sure you want to remove the imported files from
  your card? This cannot be undone."** (`CAcquireUI::WipeCardWillBeImported`
  / `WipeCardNotImported`).
- **Hibaágak**: *„An error has occurred while attempting to import. Either
  the source is unavailable or the destination is full or read only."* ·
  *„A file error has occurred while importing files. Cancelling Import."*
  (`0x0070b1e0`, `0x0070bdd0`).

### 41.4 ⚠️ A MI OLDALUNK — a mérés téved, a funkció nagyrészt megvan

Az `ImportSourceDialog.qml` **684 sor**, és a leltár „hiányzó" elemeinek
nagy részét **megvalósítja**, csak más néven és más elrendezésben:

| eredeti elem | nálunk (mérve) |
|---|---|
| `rotate1button` / `rotate2button` | `importRotateRight:<i>` / `importRotateLeft:<i>` (397., 410. sor) |
| `startoggle` | `importStar:<i>` (424. sor) |
| `excludetoggle` | `importSourceToggle:<i>` + „Exclude All" / „Include All" (335., 340., 453.) |
| `subfolder_menu` | **mind a három mód**: kézi cím · „Import into separate folders for each date taken" · „Import into folder with today's date" (503., 521., 528.) |
| `delete_menu` | hármas rádió: „Leave card alone" · „Delete only copied photos" · „Delete everything on card" (548., 555., 562.) |
| `searchstatus` | folyamatjelző + darabszám + üres-üzenet (304., 311., 319.) |
| `import_selected` / `anowbutton` / `acancelbutton` | Import / Include All / Close (629., 341., 638.) |
| másodpéldány-szűrés | „Exclude Duplicates" + *„%n of those are duplicates already in Picasa"* (267., 287.) |

⇒ **Tíz elem téves riasztás volt.** A `ui-lefedettseg-elemek.csv`
felülbírálásai ebben a körben bekerültek, bizonyítékkal (fájl + sor).

**A valódi hiány ehhez képest kettő:**

1. **A korábbi CÉLMAPPÁK listája.** Nálunk a „Recent sources" a **forrást**
   jegyzi meg (208. sor), a **célt** nem — az eredeti a `LastImport%x`
   kulcsokban tartja, és menüben kínálja.
2. **Feltöltés/megosztás blokk** (`upload_checkbox`, `share_with_label`,
   `add_groups_button`, `selected_groups_label`, `sync_options_button`) —
   **hatókörön kívül**: a Picasa Web Albums 2016 óta nincs.

*(Az egyképes előnézet next/previous lapozása helyett nálunk bélyegkép-rács
van — funkcionálisan egyenértékű, tudatos eltérés; nem hiány.)*

### Nyitott kérdések mérlege (41.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a három tárolási kulcs és a cél-menü szerkezete (41.1); az
  almappa-elnevezés három módja a `YYYY-MM-DD` formátummal (41.2); a
  kártya-törlés és a másodpéldány-szűrés szövegkészlete (41.3).
- **HATÓKÖRÖN KÍVÜL:** a feltöltés/megosztás blokk (megszűnt szolgáltatás).

### Amit KIZÁRTAM

- **„Az `acquirepanel` 22 eleme nálunk hiányzik"** — megdőlt: tíz elem
  megvan, csak más néven; a mérés a párbeszéd↔panel eltérés miatt jelezte
  hiánynak (41.4). **Ez a lecke az egész UI-axisra érvényes: a
  „hiányzik" oszlop JELÖLT, nem ítélet — minden panelnél előbb a mi
  oldalunkat kell megmérni.**

## 42. tétel — a `collagepanel`: EGY ELAVULT SOR 38 elemet rejtett el (2026-08-31)

*Negyedik kör az UI-lefedettségi axisról (#1778). Panel: `collagepanel`
(36 hiány). A 41. kör leckéjét alkalmazva — **előbb a mi oldalunkat
mérjük** — a kör nem az eredetiről, hanem a MÉRÉSRŐL talált leletet.*

### 42.1 ⛔ A panel-megfeleltetés sora ELAVULT volt, és hazudott

A `docs/specs/ui-lefedettseg-megfeleltetes.csv` `collagepanel` sora
**egyetlen** QML-fájlra mutatott (`CreateDialogs.qml`), a megjegyzése
pedig ezt állította:

> *„Csak a kollázs-létrehozó párbeszéd van meg; interaktív
> kollázs-szerkesztő panel nincs"*

**Ez ma nem igaz.** A mérés: **23 `Collage*.qml`** fájl van a fában, köztük
`CollagePanel.qml`, `CollageCanvas.qml`, `CollageSettingsTab.qml`,
`CollageClipsTab.qml`, `CollageZOrderColumn.qml`, `CollageSnapColumn.qml`,
`CollageActionRow.qml`, `CollageContextMenus.qml`, `CollageFormatMenu.qml`,
`CollageThemePopup.qml` — vagyis az interaktív szerkesztő **megvan**.

Mivel az eszköz csak a sorban felsorolt fájlokban keres, a panel
**mind a 36 eleme hiánynak látszott.**

**A sor javítása után** (mind a 23 fájl felsorolva) a hiány **36 → 14**,
és a teljes tábla:

| | a kör előtt | a sor javítása után | + elem-felülbírálások |
|---|---:|---:|---:|
| párosítva | 87 | 125 | **132** |
| hiányzik | 425 | 404 | **397** |

⇒ **Egyetlen elavult sor 38 helyesen megvalósított elemet rejtett el.**

### 42.2 A bekötés LÁNCÁT mértem, nem a végpontokat

A `collage_controller.py` metódusai önmagukban nem bizonyítanak semmit
(ld. a „mérd a bekötés láncát" tanulságot). Ezért mindegyikre
megnéztem, hogy a QML **tényleg hívja-e**:

| eredeti elem | controller-metódus | a hívó QML |
|---|---|---|
| `select_all` / `select_none` | `selectAllNodes` / `selectNoNodes` | `CollageCanvas` · `CollageActionRow` · `CollageContextMenus` |
| `remove_node` | `removeSelectedNodes` | ua. |
| `move_top` / `move_up` / `move_down` / `move_bottom` | `moveSelectionTop/Up/Down/Bottom` | `CollageZOrderColumn` · `CollageContextMenus` |
| `snap_12` / `snap_3` / `snap_6` / `snap_9` | `snapRotation(command)` | `CollageSnapColumn` · `CollageContextMenus` |

Mind a tizenegy **bekötve**, két belépési ponttal (saját oszlop + helyi menü).

### 42.3 Hét további elem: felirat-eltérés, nem hiány

Ezek megvannak, csak a szövegük nem betűre egyezik, ezért gépi úton nem
párosultak. Mind bekerült a `ui-lefedettseg-elemek.csv`-be, fájllal és
sorszámmal:

| elem | nálunk | miért nem párosult |
|---|---|---|
| `makedesktop` | „Desktop Background" gomb | a buboréksúgó majdnem szó szerint az eredetié, de nem betűre |
| `sharebutton` | „Create Collage" gomb | ua. |
| `tab2` | „Clips (%1)" fül | a darabszám miatt nem egyezik a „Clips"-szel |
| `deleteclips` | „Remove the selected pictures from the tray" | az eredeti „…selected clips…" |
| `caption_checkbox` | `collageCaptionCheckbox` | felirat nélküli vezérlő |
| `portrait` / `landscape` | `collagePortraitButton` / `collageLandscapeButton` | ikonos gombok, felirat nélkül |

### 42.4 Ami valóban nyitva marad

A maradék hét tétel mind **`bizonytalan`** osztályú (felirat nélküli,
szerkezeti elem): `tabs`, `tabpanel1`, `tabpanel2`, `picker_panel`,
`previewroot`, `previewinset`, `view_and_edit`. Ezek **tartók**, nem
vezérlők; gépi úton nem értékelhetők, és önmagukban nem jelentenek
funkcióhiányt.

⇒ **A `collagepanel`-hez ebben a körben NEM nyílik jegy** — nincs mérhető
funkcióhiány. *(A skill szabálya szerint a negatív eredmény is eredmény:
a jegy hiánya itt lelet, nem mulasztás.)*

> ⚠️ **HELYESBÍTÉS (45. tétel, 2026-09-01):** ez a mondat **szűkebben
> igaz**, mint ahogy leírtam. A mérés **elem-jelenlétet** vizsgál; a
> **csoportosztásra, sorrendre és elrendezésre VAK** (az elválasztókat
> `rajzolo`-ként ki is dobja). „Nincs mérhető funkcióhiány" tehát azt
> jelenti: *nincs hiányzó VEZÉRLŐ* — nem azt, hogy a panel elrendezése
> egyezik. Ld. **45.1**.

### Nyitott kérdések mérlege (42.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a megfeleltetési sor elavultsága és a javítás hatása (42.1);
  a tizenegy vezérlő bekötési láncának ellenőrzése (42.2).
- **HATÓKÖRÖN KÍVÜL:** a hét `bizonytalan` szerkezeti elem gépi értékelése
  (42.4) — az eszköz osztályozása szerint sem dönthető el.

### Amit KIZÁRTAM

- **„A kollázs-szerkesztő panel nincs meg nálunk"** — megdőlt: 23
  `Collage*.qml`, a vezérlők bekötve, két belépési ponttal (42.1–42.2).
  A megfeleltetési fájl állítása **elavult** volt.
- **„A 36 hiány funkcióhiány"** — megdőlt: 22 elem megvan, 7 felirat-eltérés,
  7 szerkezeti tartó.

### ⚠️ Amit ez az egész axisra jelent

A 41. kör azt mutatta, hogy az **elem**-párosítás téved. Ez a kör azt, hogy
a **panel-megfeleltetés maga is elavulhat** — és az sokkal drágább, mert
egy sor az egész panelt hiánynak jelzi. **Minden UI-kör első lépése ezért:
nézd meg a panel megfeleltetési sorát, és hasonlítsd össze a mai
QML-fával**, mielőtt bármit hiánynak neveznél.

## 43. tétel — a megfeleltetések átvilágítása, és a gyorscímkék TÍZ helye (2026-08-31)

*Ötödik kör az UI-lefedettségi axisról (#1778). A 42. kör után előbb
**az egész megfeleltetési fájlt** átvilágítottam, csak utána vettem
panelt.*

### 43.1 A megfeleltetések átvilágítása — a `collagepanel` volt az EGYETLEN elavult sor

A 42. körben kiderült, hogy egy elavult megfeleltetési sor egy egész
panelt hiánynak tud jelezni. Kézenfekvő volt a kérdés: **hány ilyen sor
van még?**

Gépi ellenőrzés mind a 74 soron (nem létező fájlra mutató hivatkozás;
illetve tagadó megjegyzés úgy, hogy a névhez illő QML mégis létezik):

| eredmény | darab |
|---|---:|
| nem létező QML-fájlra mutató sor | **0** |
| tagadó megjegyzés, de létező QML | **0** (a `collagepanel` javítása után) |

A gyanúsnak látszó `makemoviepanel` sor (49 hiány, **egyetlen** listázott
fájl, „interaktív filmkészítő panel nincs") **helyes**: a QML-fában nincs
egyetlen `Movie*`/`Film*` fájl sem. Az a hiány valódi, és a #432/#452
jegyekhez tartozik.

⇒ **A `collagepanel` egyedi eset volt.** Ez fontos negatív eredmény: a
tábla maradék számai ettől nem torzulnak tovább, tehát a 42. körben
kimondott „felfelé torzít" figyelmeztetés a **megfeleltetés** szintjén
LEZÁRUL; az **elem** szintjén (41.) továbbra is él.

### 43.2 ⭐ A gyorscímke-beállító TÍZ helyet ad — nálunk is (LEZÁRVA)

> ✅ **2026-09-02 — a szakasz „nálunk" oszlopa ELAVULT volt.** A leírás a
> megírása napján (2026-08-31, `4fcbfa19`) igaz volt; **másnap** a #1788
> megépítette a tíz helyet és az elvethető szerkesztést (`a6daab4c`,
> 2026-09-01). A mai kód: `_QUICK_TAG_SLOTS = 10`
> (`keywords_controller.py:26`), a QML pedig „EXPLICIT tíz példány"-t mond
> (`QuickTagsConfigDialog.qml:78`). **Az eredetiről szóló mérés
> változatlanul érvényes**, csak a mi oldalunk változott meg.

A `quicktagconfig` panel elemleltára `edit_0` … **`edit_9`** — tíz
szövegmező. A binárisban a kezelő (`0x0083ea00`, 2063 b) ciklushatára
ezt megerősíti:

```
0x0083efa2  cmp eax, 0xa      ; 10 hely
```

~~**Nálunk nyolc van.**~~ — **2026-09-02: már tíz.** A
`QuickTagsConfigDialog.qml` (144 sor) ma azt mondja: *„a tíz szövegmező
közös viselkedése — EXPLICIT tíz példány (nem Repeater)"*, és a mezők
`quickTagField0` … `quickTagField9` néven élnek.

Tárolás (`0x0063a5e0`, `0x0083ea00`): a `Preferences` ág
**`quicktags::tag%d`** kulcsai a címkék, a **`quicktags::enable_recents`**
a „felső két gomb lefoglalása" kapcsoló. A gyorscímke-gombok a
felületen a `quicktag_%d` / `%s/quicktag_%1d` csomópontnevek alatt élnek
(`0x0063c120`, `0x0063c7d0`).

### 43.3 A párbeszéd gombjai: OK / Mégse — nálunk is (LEZÁRVA)

Az eredeti `quicktagconfig/ok` és `quicktagconfig/cancel` vezérlőkkel
zár, tehát a **Mégse eldobja** a szerkesztést.

~~Nálunk `standardButtons: Dialog.Close` (17. sor) — egyetlen gomb.~~ —
**2026-09-02: már nem.** A #1788 átállította:
`standardButtons: Dialog.Ok | Dialog.Cancel`
(`QuickTagsConfigDialog.qml:36`), tehát a szerkesztés **elvethető**, mint
az eredetiben. **Nincs eltérés.**

### 43.4 Három elem szerepel az erőforrásban; a működésük külön ellenőrzendő

`recent_checkbox`, `recent_checkbox_label`, `autofill`: mindhárom vezérlő
megvan nálunk (`quickTagsReserveRecentCheck`, `QuickTagsConfigDialog.qml:127-142`;
`quickTagsAutoFillCheck`, `:144-158`). A felirat egy szóban tér el
(„Reserve **the** top two buttons…”), ezért nem párosult gépi úton. A
vezérlők puszta jelenléte **nem** bizonyít viselkedési egyezést: a #5659
összevetése szerint a Legutóbbiak beállítás alapértéke és a két gomb megjelenítése
egyezik, de kikapcsolt állapotban az előzményfrissítő út eltér; az Autofill
is eltér (43.2.1).

### 43.2.1 ⭐ Teljes út és viselkedés (#5659, 2026-10-23)

Az eredeti belépés a **Nézet → Címkék** panel (`0xd6e018`, parancs
`0x9d2c`, menüsáv-építő `0x00559150`; híd `0x0065ab50`). A panel
`quick_config` eleme nyitja a `QuickTagConfigDlg` ablakot (`0x00639c00`,
`0x0063d840`). A `quicktagconfig` erőforrás tíz szerkesztőt (`edit_0..9`),
„Reserve top two buttons for recently used tags” jelölőt, „Autofill empty
boxes above with commonly used tags” műveletet, OK és Cancel vezérlőt ír
le. Az `0x0083ea00` a tíz mezőt olvassa/kezeli; az `0x0083f3f0` a
`quicktags::tag%d` kulcsokat olvassa `]empty` alapértékkel.

| Eredeti | Nálunk (statikus forráskód-olvasás) | Teendő |
|---|---|---|
| **Belépés:** Nézet → Címkék (`0xd6e018`, cmd `0x9d2c`, `0x00559150` → `0x0065ab50`); a panel gyors beállítása `quick_config` (`0x00639c00`, `0x0063d840`). | Nézet → Tags / Ctrl+T (`PicasaMenuBar.qml:1071-1076`, `Main.qml:3948-3952`); a fogaskerék nyitja a párbeszédet (`TagsPanel.qml:234-248`). | **EGYEZIK**: ugyanaz a panel és beállítóút. |
| **Mezők:** tíz címke (`edit_0..9`; `0x0083efa2`, `cmp eax, 0xa`); üres kulcs alapértéke `]empty` (`0x0083f3f0`). | Tíz `quickTagField0..9` mező; a hiányzó beállítás üres sztringekkel egészül ki (`QuickTagsConfigDialog.qml:83-124`, `keywords_controller.py:235-244`). | **EGYEZIK**: 10 szerkeszthető hely, üres alapérték. |
| **Legutóbbiak:** `Preferences\quicktags::enable_recents`, hiányzó kulcsnál `1` (`0x0063c7d0`, `0x00639c00`); bekapcsolva az első két gomb a `recent0/1`-et mutatja (`0x0063c7d0`, `0x0063c120`). | `quickTags/reserveRecentForTop2`, hiányzó kulcsnál `True`; a gomblista első két elemét írja felül (`keywords_controller.py:298-307`, `:320-331`). | **EGYEZIK**: az alapérték és a két látható hely egyezik. |
| **Előzményfrissítő út:** a címke-hozzáadó (`0x0063bed0`) csak bekapcsolt `quicktags::enable_recents` mellett hívja a `0x0063c120` frissítőt (`0x0063c05a-0x0063c08a`); ez a segéd a `recent%d` értékeket beolvassa és a panel két előzményhelyét frissíti (`0x0063c303-0x0063c371`, ciklushatár: `0x0063c578-0x0063c57e`). **A tartós `recent%d`-írás hatása nincs igazolva.** | Az `addKeywordToRows` minden érvényes címkénél meghívja a `_record_recent_quick_tag`-et a beállítástól függetlenül; ez QSettings-listát ír, míg a beállítás csak a gombok megjelenítését kapuzza (`keywords_controller.py:149-162`, `:250-261`, `:320-331`). | **ELTÉRÉS a kikapcsolt állapot útjában:** nálunk az előzménylista frissül, az eredeti kihagyja a frissítő hívást. A bináris későbbi/persistált látható eredménye **NINCS MEG**; ne állítsunk róla többet. |
| **Autofill:** egyszeri kitöltő művelet; a `0x0083f580` a közös címkelistából az üres szerkesztőmezőkbe ír, meglévő címkét/duplikátumot átugrik, és a Legutóbbiak kapcsolótól függően a 0. vagy 2. mezőtől indul. A párbeszéd a `quicktagconfig/autofill` vezérlőt köti be (`0x0083ea00`); ehhez nem olvas/ír tartós Autofill-beállítást. Felirat: `quicktagconfig_text.tre`, `0x0083ea00`. | Tartós `quickTags/autoFillFrequent` jelölőnégyzet, alapértéke `False`; bekapcsolva a `quickTagButtons` minden lekéréskor dinamikusan tölti az üresen maradt gombokat az index gyakorisági sorrendjéből (`QuickTagsConfigDialog.qml:144-158`, `keywords_controller.py:309-342`). | **ELTÉRÉS:** a jelölőnégyzet helyett egyszeri kitöltés írja be az üres konfigurációs mezőket; az eredményt a felhasználó az OK-val menti. |
| **Gyorscímke kimenete:** a `quicktag_%d` esemény a `0x0063bed0` hozzáadási útjára jut (`0x0063a5e0` → `0x0063bed0`). A címke a `CThumbUI::IKeywordUpdate` `+0x284` interfész `+0x14` slotján (`0x00c906d8` → `0x0065b4b0`) a `0x005c76b0` kijelölési/listaépítő útba kerül. A tényleges fájl-/adatbázis-író és az IPTC Keywords mezőn belüli beszúrási irány továbbra is **NINCS MEG**; a `0x005c7710` indirekt callbacket kell feloldani, majd eredeti JPEG-et mérni. | A kijelölt sorokra ad címkét; JPEG-nél IPTC Keywords írás, íráshiba vagy más formátum esetén `.picasa.ini` `keywords=` fallback és index-frissítés (`keywords_controller.py:149-162`, `:176-231`). | **NINCS DÖNTÉS** az írási paritásról: a bináris fájlíró út és az eredeti JPEG mezősorrendje még hiányzik. |
| **Párbeszéd:** OK / Cancel; a tíz `quicktags::tag%d` mező és a `quicktags::enable_recents` értékét kezeli/menti (`0x0083ea00`, `0x0083f3f0`, `0x0083f2f0`). | OK / Cancel; a mezők és kapcsolók QSettings-be íródnak, Mégse megnyitáskori állapotra állít vissza (`QuickTagsConfigDialog.qml:36`, `:60-75`). | **EGYEZIK**: a mentés és elvetés látható eredménye egyezik. |

**Autofill-cáfoló kör.** A `quicktagconfig/autofill` ugyanazt a `tag_group`
szülőt és `m_hit_childlabel` jelölést kapja, mint a `recent_checkbox`, ezért
elsőre kapcsolónak is tűnhet (`quicktagconfig.tre:15-17`, `:83-89`). Ezt
ellenőriztem az eseménykezelővel: az `0x0083f580` a mezők setterét hívja,
nem tárolókulcsot; az `0x0083ea00` csak a vezérlő meglétét/állapotát rendezi.
A vizsgált kattintási eseménykezelőben és a párbeszéd betöltő/mentő útjában
nincs tartós Autofill-beállítás olvasása vagy írása. A következtetés ezért az
eseménykezelő, a párbeszédépítő és az erőforrás egymástól külön ellenőrzött
nyomára épül, nem pusztán a feliratra.

**A Legutóbbiak cáfoló köre.** A kezdeti értelmezés szerint a `0x0063c120` két
`recent%d` rekordot ír. Ezt a segédfüggvény utasításszintű ellenőrzése
cáfolta: a vizsgált út `Preferences`-ből olvassa ezeket a kulcsokat, majd a
panel két előzményhelyét kezeli; közvetlen írás nem látható. Ettől
függetlenül a `0x0063bed0` feltételes hívása és a `0x0063c7d0` betöltő
ágazása egyaránt igazolja, hogy a kikapcsolt jelző mellett az eredeti nem
hívja a frissítőt és nem használja a `recent%d` értékeket a két gombon.
A későbbi/persistált látható hatás nyitott marad.

**Nyitott részletek:** az `0x0063d260` által kapott közös címkelista pontos
forrása és sorrendje **NINCS MEG**. Megszerzés: a `0x0063c7d0`-ban az
`[this+0x268]` listát előállító hívás és a `0x0063d260` bemenetének
adatútját végigkövetni, majd kontrollált címkekészleten megfigyelni az
Autofill sorrendjét. Az Autofill-vezérlő pontos vizuális típusa/állapotjelzése
is **NINCS MEG**: a `.tre` kattintható elemet jelez, az építő állapotjelző bájtot
állít, de a statikus adat nem dönti el a widget megjelenését. Megszerzés:
elszigetelt Picasa-profilban nyisd meg a panelt, rögzítsd a vezérlőt kattintás
előtt és után, és figyeld meg a képernyőn maradó állapotot. A bináris
gyorscímke-kimenet fájlíró útja is nyitott, ld. a táblázat sora.

### Javasolt jegytörzs-bővítés (#5659)

#### A. Eredeti Autofill-művelet

**Eredeti:** az „Autofill empty boxes above with commonly used tags” egyszeri
művelet, amely az üres konfigurációs mezőket tölti ki; a Legutóbbiak kapcsoló
bekapcsolt állapotában az első két helyet kihagyja.

**Nálunk:** a párbeszédben tartós jelölőnégyzet van; bekapcsoláskor a
gyorscímke-gombok dinamikusan, indexelt gyakorisági lista alapján jelennek
meg. A konfigurációs mezők nem telnek meg ettől.

**Teendő:** a tartós automatikus megjelenítést cserélni egyszeri „üres
mezők kitöltése” működésre; a vezérlő pontos vizuális formáját csak az
eredeti felület kontrollált megfigyelése után rögzíteni. A művelet ne írja
felül a kézzel beállított értékeket vagy a fenntartott legfelső két mezőt.

**Kész, ha:**

- [ ] a művelet csak üres mezőket tölt ki;
- [ ] bekapcsolt Legutóbbiak mellett a 0-1. hely érintetlen marad, kikapcsolt
  Legutóbbiak mellett a kitöltés a 0. helytől indul;
- [ ] a megjelenített címkék megegyeznek a konfigurációba írt mezőkkel, és
  OK után tartósak;
- [ ] a vezérlő képernyőn látható formája és kattintás utáni állapota a
  bináris izolált profilban végzett megfigyelés alapján van megvalósítva;
- [ ] a pontos jelöltlista/sorrend a bináris további vizsgálata után van
  rögzítve; amíg ez nyitott, nem kerül bele becsült rendezési szabály.

#### B. A Legutóbbiak kikapcsolásakor az előzmény ne változzon

**Eredeti:** `quicktags::enable_recents=0` mellett a hozzáadási út kihagyja
a `0x0063c120` előzményfrissítő hívását; a segédfüggvény közvetlen tartós
írása és a későbbi visszakapcsolás eredménye nincs meg.

**Nálunk:** a `quickTagsReserveRecent` állapotától függetlenül frissítjük a
QSettings-ben tárolt előzménylistát; a gombok megjelenítését külön kapuzzuk.

**Teendő:** a binárisban igazolt hívási feltétellel összhangban a legutóbbiak listáját
csak bekapcsolt „felső két hely a legutóbbiaknak” állapotban frissíteni.

**Kész, ha:**

- [ ] kikapcsolt állapotban végzett címkézés nem hívja meg és nem írja át az
  előzményfrissítő listát;
- [ ] bekapcsolt állapotban a friss címke az első helyre kerül, duplikáció
  nélkül.

### Nyitott kérdések mérlege (43.)

```
Nyitott kérdések: 4 nyílt (az Autofill jelöltlistája és vezérlőjének vizuális/állapot-viselkedése; a bináris fájlíró útja; a legutóbbiak frissítőjének későbbi/persistált látható hatása) · 4 lezárva · 2 megerősített fejlesztési eltérés
```

- **LEZÁRVA:** a megfeleltetési fájl átvilágítása — a `collagepanel` volt
  az egyetlen elavult sor (43.1); a gyorscímke-helyek száma két
  független forrásból (leltár + ciklushatár, 43.2); a tárolási kulcsok
  és az OK/Cancel viselkedés (43.2-43.3). A #5659 két, forráskóddal is
  összevetett eltérést igazolt (Autofill; kikapcsolt Legutóbbiak beállítás melletti
  frissítőhívás). A Legutóbbiak későbbi, tartós látható hatása nyitott.

### Amit KIZÁRTAM

- **„Több elavult megfeleltetési sor is van"** — megdőlt: gépi
  ellenőrzés mind a 74 soron, nulla találat (43.1).
- **„A `makemoviepanel` sora is elavult"** — megdőlt: a QML-fában nincs
  filmkészítő panel, a sor állítása helyes; az a hiány valódi (43.1).
- **„A gyorscímke-helyek száma nyolc"**: megdőlt: az eredetiben és a mai
  kódban is tíz van (`0x0083efa2`, `QuickTagsConfigDialog.qml:115-124`). A
  korábbi PicasaPy-állapot nyolc helye a #1788-cal megszűnt (43.2).

## 44. tétel — a `buttonmgr`: a Picasa gombsávja BŐVÍTHETŐ VOLT (2026-08-31)

*Hatodik kör az UI-lefedettségi axisról (#1778). Panel: `buttonmgr`
(13 hiány, `nincs-megfeleltetes`). Nálunk a menütétel **placeholder**
(`PicasaMenuBar.qml:1361`), a párbeszéd nem létezik.*

### 44.1 MIT CSINÁL: két registry-kulcs és egy bővítmény-mappa

| tároló | mit tart | cím |
|---|---|---|
| `Preferences\Buttons\UserConfig` | a felhasználó gombsáv-összeállítása | `0x00758390`, `0x00758d30` |
| `Preferences\Buttons\Exclude` | a kihagyott gombok | `0x00758390`, `0x007592f0` |
| **`#buttons\`** mappa | a **telepített gombok** adatkönyvtára | `0x005f97f0`, `0x007599b0` |

A `#`-előtag a Picasa adatmappán belüli útvonalak jelölése (ugyanaz a
minta, mint a `#db3\saverlist.txt`-nél, 35.3).

### 44.2 ⭐ A gombsáv BŐVÍTMÉNY-RENDSZER volt

A panelen ott a **„Find buttons online…"** gomb (`buttonmgr/browse`),
és a mögötte álló cím a `0x007e14e0`-ben:

```
http://picasa.smo/buttons
```

Ehhez tartozik egy **importáló ág** is: *„Launch Picasa and import
buttons?"* (`0x004bbaf0`) — vagyis a letöltött gombcsomagot a rendszer
héja adta át a Picasának, ami rákérdezett, mielőtt telepítette. A
`CustomButtons` (`0x0097a390`) és a `Buttons::DidHideAll` (`0x0075b1c0`)
ugyanennek a rendszernek a részei.

⇒ **A gombsáv nem fix készlet volt: a felhasználó gombokat tölthetett
le és telepíthetett.** A `picasa.smo` kiszolgáló nem létezik, tehát a
**letöltés-ág hatókörön kívül** — a **testreszabás** viszont nem az.

### 44.3 A párbeszéd szerkezete — klasszikus kétlistás választó

**A TELJES elemlista, elemnévvel** (a listakezelők a `0x007e2980` és a
`0x007e2470` címen; a bővítmény-ág a `0x007e14e0`):

| elem | felirat | **hivatalos magyar** |
|---|---|---|
| `buttonmgr/leftlist_text` | *(felirat a lista fölött)* | **„Rendelkezésre álló gombok:"** |
| `buttonmgr/leftlist` | a választható gombok listája | — |
| `buttonmgr/rightlist_text` | *(felirat a lista fölött)* | **„Jelenlegi gombok:"** |
| `buttonmgr/rightlist` | a gombsáv aktuális összeállítása | — |
| `buttonmgr/add` | Add >> | **„Hozzáadás >>"** |
| `buttonmgr/remove` | << Remove | **„<< Eltávolítás"** |
| `buttonmgr/moveup` | Move Up | **„Mozgatás felfelé"** |
| `buttonmgr/movedown` | Move Down | **„Mozgatás lefelé"** |
| `buttonmgr/usedefaults` | Reset to Defaults | **„Visszaállítás alapértelmezettre"** |
| `buttonmgr/ok` | OK | **„OK"** |
| `buttonmgr/cancel` | Cancel | **„Mégse"** |
| `buttonmgr/done` | Done | **„Kész"** |
| `buttonmgr/browse` | Find buttons online… | **„Gombok keresése az interneten…"** — **hatókörön kívül** (44.2) |

⚠️ **Miért kellett ide a TELJES elemlista** (2026-09-02): a szakasz eddig
prózában sorolta fel a vezérlőket („közte »Add >>« és »<< Remove«"), a
lefedettségi mérő viszont a **teljes elemnévre** (`buttonmgr/add`) keres.
Emiatt a tizenhárom elemből **tizenkettő „feltáratlan"-nak**, azaz kutatói
kört igénylőnek látszott — pedig a 44.1–44.3 mindent leír róluk (tárolás,
bővítmény-ág, szerkezet). Az elemnevek kiírásával a mérő **`lekutatva`**-ként
sorolja be őket: **fejlesztői kör kell rájuk, nem kutatói.** A lelet
általánosítható: *egy spec-szakasz csak akkor számít bizonyítéknak, ha az
elemet a TELJES nevén nevezi meg.*

*(A `0x007e2980` és `0x007e2470` a listák egér- és
fogd-és-vidd-eseményeit kezeli — `lb_selected`, `b_drop`, `lb_rightclick`,
`lb_predouble` —, tehát a listák **húzással is** rendezhetők voltak.)*

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| a párbeszéd | kétlistás választó, sorrendezéssel | **nincs**; a menütétel `placeholder` (`PicasaMenuBar.qml:1361`) | ÚJ JEGY |
| a testreszabás tárolása | `Preferences\Buttons\UserConfig` + `…\Exclude` | nincs | QSettings |
| alapértelmezettre állítás | „Reset to Defaults" | nincs | ua. |
| gombok letöltése | `http://picasa.smo/buttons` | — | **hatókörön kívül** (a kiszolgáló nem létezik) |
| gombcsomag-telepítés | „Launch Picasa and import buttons?" | — | **hatókörön kívül** |
| a `#buttons\` mappa | telepített gombok | — | csak akkor kell, ha a bővítményt is megépítjük |

### Nyitott kérdések mérlege (44.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 0 blokkolt · 2 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a két registry-kulcs és a `#buttons\` mappa (44.1); a
  bővítmény-rendszer léte és a hozzá tartozó cím (44.2); a párbeszéd
  szerkezete és a húzásos rendezés (44.3).
- **HATÓKÖRÖN KÍVÜL:** a gombletöltés (`picasa.smo` megszűnt) és a
  gombcsomag-telepítő ág.

### Amit KIZÁRTAM

- **„A Picasa gombsávja fix készlet"** — megdőlt: bővítmény-rendszer volt,
  letölthető gombokkal és saját adatmappával (44.2).
- **„A »Configure Buttons…« csak sorrendet állít"** — megdőlt: a
  **kihagyást** külön kulcs tárolja (`Buttons\Exclude`), tehát a gombok
  el is rejthetők, nem csak átrendezhetők (44.1).


### 44.4 ⭐ A „Visszaállítás alapértelmezettre" kimenete — GUID-lista, KÓDBÓL (2026-09-15, #1792)

*Forrás: `FUN_00757560` (1628 b), `0x00757577`–`0x00757621`.*

A `Buttons\UserConfig` kulcs **alapértéke a `"0"` sztring**
(`0x00c7fe6c`, `0x00758700`), nem gomblista — azaz „nincs saját
összeállítás". A tényleges alapértelmezett készletet **kód építi**, és
most megvan, hogyan:

```
FUN_007592f0(...)            ; a Buttons\Exclude beolvasása; hiba -> kilép
append {45EF212C-84AB-46c5-A42E-95023ED50C76}     ; 0x00757589
append {1FC0FA62-3412-4466-B485-B7CB97D3714B}     ; 0x007575a2
append {4D139EF7-47A3-4da4-9A00-AF35AAEC17D1}     ; 0x007575c1
append {0B3F3356-4FA1-48ca-B972-2B7D20AC6FBF}     ; 0x007575e0
if ([obj+0xdb5] == 0)
    append {3C09A978-42C4-4437-85CA-D326872B424D} ; 0x0075760a
```

Az `append` mindannyiszor a `FUN_007580d0`, a sztringet a `FUN_00985ff0`
készíti (hossz `0x26` = 38 karakter, a kapcsos zárójelekkel együtt).

⇒ Három megállapítás:

1. **A gombokat GUID azonosítja**, nem név. A leíró-formátumot a
   `FUN_00755190` (4712 b) olvassa: `version` · `value` · `action` ·
   `format` · `buttons` · `button` mezőnevekkel.
2. **Az alapkészlet négy fix + egy feltételes gomb.** Az ötödiket egy
   objektum-jelző (`+0xdb5`) kapuzza — ez a mérésből nem derül ki, mit
   jelent; a „Kész, ha" listájának ezzel kell számolnia.
3. **A hatodik GUID (`{B9012CB2-DD50-49a5-B4CB-009344BBA285}`,
   `0x00cb20b0`) NEM tagja az alapkészletnek**: a törzs csak
   ÖSSZEHASONLÍTÁSRA használja (`cmp eax, 0xcb20b0`, `0x00757691` és
   `0x0075772d`) — külön eset, nem alapértelmezett gomb.

⛔ **Amit ez NEM ad meg:** a GUID→gombnév megfeleltetést. Az a
bővítmény-leírókból jönne (`#buttons\` adatmappa), ami a mentésünkben
nincs meg. A megvalósításnak tehát a SAJÁT gombjaink azonosítóit kell
használnia; az eredeti GUID-ek csak a szerkezetet bizonyítják.

*Bizonyítottsági fok: **megerősített** a listára, a sorrendre és a
feltételes ötödikre (a törzs utasításai) · **nincs mérve**, mit jelent a
`+0xdb5` jelző, és melyik GUID melyik gomb.*


## 45. tétel — a mérés HATÁRAI és a tudott eltérések táblája (2026-09-01)

*Hetedik kör az UI-lefedettségi axisról. Nem panel: a **módszer** köre —
egy testvér-munkamenet menüsor-mérése rámutatott egy vakfoltra, ami a
saját korábbi következtetéseimet is érinti.*

### 45.1 ⚠️ A mérés VAK a csoportosztásra, a sorrendre és az elrendezésre

Az `ui_lefedettseg.py` három osztályba sorolja az elemeket
(`feliratos` / `vezerlo` / `rajzolo`), és **csak azt kérdezi, hogy egy
elem MEGVAN-e**. Amit nem kérdez:

| amit nem lát | miért |
|---|---|
| **elválasztók, csoporthatárok** | a `separator` a `rajzolo` névminták közt van (`ui_lefedettseg.py:64`) — ki is dobja az értékelésből |
| **sorrend** | az összevetés halmaz-alapú |
| **elrendezés, méret, pozíció** | a `.tre`/`respack` geometriát az eszköz nem olvassa |
| **hierarchia** | melyik elem melyik csoportban ül |

⇒ **A „hiányzik = 0" NEM azt jelenti, hogy a panel egyezik.** Azt
jelenti: *minden vezérlő megvan valahol.*

**Miért fontos ez most:** egy testvér-kör a felső menüsor
**csoportosztását** mérte ki a tulajdonos képernyőmentéseiből
(`docs/specs/picasa-menusor-csoportok.md`), és a **nyolc menüből hatban**
talált eltérést — miközben a korábbi, **felirat-szintű** audit
(`ui-audit-menus.md`) mindet átengedte. A hiba **szerkezeti** volt, nem
feliratbeli. Ugyanez a vakfolt az én axisomon is fennáll.

⇒ **A 42.4 pont mondata ezért helyesbítve** (ld. ott): a `collagepanel`
esetében *hiányzó vezérlő* nincs; a **csoportosztása nincs mérve.**

### 45.2 Amit ebből minden UI-kör csináljon másképp

1. A záró mondat legyen **pontos**: „nincs hiányzó vezérlő", ne „nincs
   funkcióhiány".
2. Ha a panelről van **képernyőmentés**, a csoportosztást is nézd meg —
   a mentéseken az **inaktív tételek is látszanak**, tehát ha egy elem
   nincs a képen, akkor tényleg nincs a panelen. *(Ez a testvér-kör
   bizonyítéka; erős elv, mert az inaktivitás nem rejti el a tételt.)*
3. Ha nincs mentés, **mondd ki**, hogy a csoportosztás nincs mérve —
   ne csendben maradjon.

### 45.3 ⭐ TUDOTT ÉS INDOKOLT ELTÉRÉSEK — a kimondatlanság ellen

A projekt visszatérő kára: egy **szándékos** eltérés kimondatlanul marad,
és egy későbbi kör hibának nézi, újra levezeti, esetleg „javítja". A
#416/#422 és a #1454 mind ilyen volt.

Az alábbi tábla az UI-axis eddigi köreiben talált eltéréseket sorolja.
**Ami itt szerepel, az tudatos; ami nem szerepel és mégis eltér, az
hiba.**

| panel | eltérés | indok | jegy |
|---|---|---|---|
| `acquirepanel` | nálunk **párbeszéd**, az eredetiben bal oldali panel | a párbeszéd ugyanazt a funkciót adja; a panel-forma átvétele nagy szerkezeti munka, önálló haszon nélkül | — |
| `acquirepanel` | egyképes előnézet next/prev helyett **bélyegkép-rács** | a rács egyszerre mutatja a készletet; funkcionálisan erősebb | — |
| `quicktagconfig` | **8** hely az eredeti **10** helyett | eredetileg saját döntés, **indoka nincs rögzítve** ⇒ a jegy kéri a pótlást | #1788 |
| `quicktagconfig` | csak **Bezárás**, nincs OK/Mégse | a párbeszéd azonnal ír; **kimondatlan volt** ⇒ a jegy döntést kér | #1788 |
| `printoptions` | külön `PrintOptionsPanel.qml` panelként megvan, a tizenegy alapérték egyezik; a teljes geometria és kimeneti raszter nincs mérve | a „nincs megvalósítva” állítás elavult; lásd a #5663 tábláját és nyitott kérdéseit | #5663 |
| `buttonmgr` | a **gombletöltés** nem készül el | a `picasa.smo` kiszolgáló megszűnt | #1792 |
| `acquirepanel` | a **feltöltés/megosztás** blokk nem készül el | Picasa Web Albums megszűnt | — |
| `printpanel` | a **`froogle`** gomb nem készül el | a Froogle megszűnt | #1782 |

*(A tábla nyitott: minden további UI-kör ide írja, amit tudatos
eltérésként hagy.)*

### Nyitott kérdések mérlege (45.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** mire vak a mérés, és mit jelent pontosan a „hiányzik = 0"
  (45.1); a tudott eltérések helye és szabálya (45.3).

### Amit KIZÁRTAM

- **„A `hiányzik = 0` azt jelenti, hogy a panel egyezik az eredetivel"** —
  megdőlt: a mérés elem-jelenlétet néz, a csoportosztásra és a sorrendre
  vak (45.1). **Ez a saját 42.4 pontom helyesbítése.**

## 46. tétel — a `faceheaderpanel`: a JAVASLAT-MUNKAFOLYAMAT négy parancsa (2026-09-01)

*Nyolcadik kör az UI-lefedettségi axisról (#1778). Panel:
`faceheaderpanel` (12 hiány) — a névvel ellátott arc-album fejléce.*

### 46.1 A fejléc egy PARANCSKÉSZLET, közös kezelővel

A `0x005e0f70` az album-fejlécek **névparancs-kezelője** — ugyanaz szolgálja
ki a mappa- és az arc-album fejlécét. A benne felsorolt nevek:

| csoport | parancsok |
|---|---|
| **javaslat-munkafolyamat** | `selectsug` · **`confirmsug`** · **`sug_filter`** · **`moresug`** |
| nézet | **`face_zoom`** ↔ **`picture_zoom`** |
| láthatóság | `showunknown` · `showignored` |
| kijelölés | `select_faces` · `select_star` |
| létrehozás | `create_collage` · `create_movie` · `create_cd` |
| online *(halott)* | `pwa_button` · `share` · `view_online` · `ebsync0/1` · `sync_options` |

### 46.2 ⭐ „További javaslatok keresése" = ÚJRA-KLASZTEREZÉS

A `moresug` saját kezelője a `0x0074cc00`, és a sztringjei elárulják, mit
csinál:

```
rightdrawerpanel/peoplepanel · peoplepanel/update · moresug · cluster · showall
```

⇒ A gomb **klaszterezést** futtat (`cluster`), majd **frissíti a
Személyek panelt** (`peoplepanel/update`). Nem szűrő, hanem **munka**:
az eddig nem javasolt arcokra keres egyezést.

A `confirmsug` („Az összes jóváhagyása") ezzel szemben a **meglévő**
javaslatokat fogadja el egy lépésben; a `sug_filter` pedig csak
**megjelenítési szűrő** („Show only suggestions (when toggled on)").

⇒ **Három különböző dolog, három gomb** — a felirataikból ez nem
látszik, a kezelőikből igen.

### 46.3 A nézet-váltó pár

`face_zoom` („View zoomed in to the face") ↔ `picture_zoom` („View zoomed
out to the full picture") — a bélyegkép **az arcra vagy a teljes képre**
nagyít. Kizáró pár, a fejlécben.

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| javaslat-munkafolyamat (4 parancs) | `selectsug`/`confirmsug`/`sug_filter`/`moresug` | **nincs** — a „suggestion" szó a QML-ben csak a **vágás**-javaslatokra utal (`EditorCropPanel.qml:237`) | a #26 része |
| arc ↔ kép nagyítás | kizáró pár a fejlécben | nincs | ua. |
| `showunknown` / `showignored` | láthatóság-kapcsolók | nincs | ua. |
| „Eltávolítás" (`removesel`) | a fejlécben | a helyi menüben van (`PeopleAlbumContextMenu.qml`) | elhelyezés-kérdés |
| „Beállítás indexképként" | `set_thumbnail` | nincs személy-album indexkép | ua. |
| kollázs / film / arcfilm gomb | három Létrehozás-gomb | a fejlécben nincs | ua. |
| lejátszás | `play` | **megvan** (`LightboxHeader.qml:131`, `headerPlayButton`) | — |
| `pwa_button` · `share` · `view_online` | Picasa Web Albums | — | **hatókörön kívül** |

### 46.4 Miért NEM nyílik önálló jegy

A javaslat-munkafolyamat **nem valósítható meg önállóan**: javaslat csak
ott van, ahol **arcfelismerő motor** fut, és a projektben az még nem
készült el (`feature-map.md`, 3. fázis). A lelet ezért a **#26**
(„Arcfelismerés + Emberek") jegyre került kommentként, a négy parancs
szétválasztásával — az a jegy tudja majd felhasználni.

*(Ez a `gyujtojegy-nem-eleg` szabály másik oldala: ha a lelet önmagában
NEM megvalósítható, akkor a meglévő jegy a helyes cím.)*

### Nyitott kérdések mérlege (46.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a fejléc parancskészlete és közös kezelője (46.1); a
  `moresug` valódi működése — újra-klaszterezés, nem szűrés (46.2); a
  nagyítás-pár (46.3).
- **HATÓKÖRÖN KÍVÜL:** `pwa_button` · `share` · `view_online` ·
  `ebsync0/1` · `sync_options` — Picasa Web Albums.

*(Záró mondat a 45.1 szerint pontosan: ebben a panelben **van** hiányzó
vezérlő; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A »További javaslatok keresése« egy szűrő"** — megdőlt: klaszterezést
  futtat és frissíti a Személyek panelt (46.2).
- **„A javaslat-kezelés egyetlen gomb"** — megdőlt: négy külön parancs,
  három különböző jelentéssel (46.1–46.2).

## 47. tétel — a `choose_mail`, és egy NÉMA BEÁLLÍTÁS nálunk (2026-09-01)

*Kilencedik kör az UI-lefedettségi axisról (#1778). Panel: `choose_mail`
(13 hiány) — a levelezőprogram-választó párbeszéd.*

### 47.1 Az eredeti párbeszéd — két út, és egy „ne kérdezd többet"

A párbeszéd kérdése: *„Válassza ki, hogyan szeretné e-mailben elküldeni
fotóit."* Két választás:

| vezérlő | felirat |
|---|---|
| `mail1` / `mail1a` (`mymail`) | **„LEVELEZŐPROGRAM"** — „Az alapértelmezett levelezőprogram használata" |
| `mail2` / `mail2a` (`gsender`) | **„Google Mail"** — „A Gmail-fiók vagy a Google Fiók használata" |

Mellette `gmailsignup1` („Nincs Gmail-fiókja? Nyisson egy fiókot ingyen."),
`help`/`helpbutton`, `mailcancel`, és a **`remember`** jelölőnégyzet:
*„Jegyezze meg ezt a beállítást, ne jelenítse meg a párbeszédpanelt
újra."*

**Tárolás** (`0x0084f6b0`): a `Preferences` ág **`EmailPrepType`**
(melyik utat választotta) és **`DoNotPromptForEmailPref`** (a „ne
kérdezd többet" jelölés).

A tágabb e-mail beállítás-készlet (`0x006e1100`): `EmailSinglePicture` ·
`EmailMovie` · `EmailExportSize` · `UseHTMLMailer` · `mailprog` ·
`defaultmail` · `IDS_EMAILCLIENTRADIO`.

⇒ **A Google Mail-ág hatókörön kívül** (a Picasa saját Gmail-integrációja
megszűnt). **A választó-párbeszéd maga viszont nem az**, mert nálunk a
Beállítások ígéri.

### 47.2 ⛔ TÖRTÉNETI LELET (2026-09-01): „Let me choose each time”

**A lent következő lelet a 2026-09-01-i kódállapotra vonatkozik.** A #1798/#4135 után a levélküldés lánca megváltozott; a mai állapotot a 47.3 szakasz írja le.

A `OptionsTabEmail.qml` (99 sor) két rádiógombot kínál:

```qml
:33  optionsMailDefaultRadio  „Use this computer's default email program”
:43  optionsMailChooseRadio   „Let me choose each time I send a picture”
```

A választás **tárolódik** (`email_controller.py:63`,
`mail/useDefaultClient`), és a felület helyesen jelzi vissza.

**De a küldés nem olvassa el.** Az `email_controller.py:255`
`sendRows()` metódusa **feltétel nélkül** az `xdg-email`, illetve annak
hiányában a `mailto:` útra megy — a `useDefaultClient` értéket
**sehol nem kérdezi meg** (a kulcs a fájlban csak az olvasó/író
tulajdonságban szerepel: `:132`, `:182`, `:184`).

⇒ **A „Let me choose each time I send a picture" gomb kiválasztható,
megmarad, és NEM CSINÁL SEMMIT.** Ugyanaz a hibaosztály, mint a #936
(néma jelzés) és a #1638 (néma menütétel).

*(Az eredetiben ehhez a választáshoz tartozik a `choose_mail`
párbeszéd — nálunk az nincs meg, ezért nincs mit megjeleníteni.)*

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| választó-párbeszéd | `choose_mail`, két úttal | **nincs** | ÚJ JEGY |
| „ne kérdezd többet" | `DoNotPromptForEmailPref` | nincs | ua. |
| a választás tárolása | `EmailPrepType` | `mail/useDefaultClient` — **tárolva, de nem használva** | ua. |
| „minden küldéskor kérdezz" beállítás | a párbeszéd megjelenik | **néma** (`sendRows` nem nézi) | ua. |
| Google Mail-ág | `gsender`, `gmailsignup1` | — | **hatókörön kívül** |
| méret/film/HTML beállítások | `EmailExportSize`, `EmailMovie`, `UseHTMLMailer` | **megvannak** (`OptionsTabEmail.qml:54/64/78/85/93`) | — |

### Nyitott kérdések mérlege (47.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a párbeszéd két útja, a „ne kérdezd többet" kulcs és a
  tárolás (47.1); a mi néma beállításunk bizonyítása (47.2).
- **HATÓKÖRÖN KÍVÜL:** a Google Mail-ág.

*(Záró mondat a 45.1 szerint: ebben a panelben **van** hiányzó vezérlő —
az egész párbeszéd hiányzik; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A `choose_mail` teljes egészében halott szolgáltatás"** — megdőlt:
  csak a **Google Mail-ág** az; a választó-párbeszéd maga él, és nálunk a
  Beállítások ígéri is (47.2).
- **„A `mail/useDefaultClient` beállításunk hat a küldésre”**: ezt a 47.2
  lelet tévesnek mérte, mert a `sendRows()` akkor még nem olvasta a kulcsot.

### 47.3 Frissítés (2026-10-17): a levelezési mód beállítása bekötött

A 47.2 lelet történeti. A mai lánc a forrásban végigkövethető: a Beállítások rádiógombja a `mail/useDefaultClient` értéket írja (`OptionsTabEmail.qml:54-77`, `email_controller.py:366-384`). A `sendRows()` `mailChoiceRequested` jelzést küld (`email_controller.py:507-519`), a `Main.qml` ebből megnyitja a párbeszédet (`Main.qml:2622-2631`), majd az `EmailChoiceDialog.qml:34-43` a tárolt érték szerint a `compose` vagy `choose` panelt mutatja. A „Let me choose each time I send pictures” ezért nem néma beállítás. A küldés mindkét módban a rendszer alapértelmezett levelezőprogramját használja; a Google Mail ág továbbra is letiltott.

## 48. tétel — a NÉMA BEÁLLÍTÁS mint önálló hibaosztály (2026-09-01)

*Tizedik kör az UI-lefedettségi axisról. Nem panel: a 47. körben talált
hiba **osztályának** felmérése — és annak bizonyítása, hogy a meglévő
őreink NEM fogják meg.*

### 48.1 A negyedik állapot

A projektnek két gépi őre van erre a hibacsaládra:

| őr | mit fog meg |
|---|---|
| `eszkozok/nema_jelzesek.py` | **kimenő**: kibocsátott jelzés, aminek nincs fogadója |
| `eszkozok/nema_slotok.py` | **bejövő**: `@Slot`/`@Property`, amit senki nem hív |

A 47. körben talált hiba **egyikbe sem fér bele**:

> a QML **hívja** a settert · az érték **eltárolódik** · a QML **vissza is
> olvassa** (a rádiógomb helyesen mutatja) — csak az **üzleti logika**
> nem kérdezi meg soha.

⇒ **Negyedik állapot:** *„a beállítás él, csak nem hat."*

**Mérve, nem feltételezve:** a `nema_slotok.py` a mai fán 565 tagot
vizsgál, 16-ot jelöl némának — és a `useDefaultClient` / `setUseDefaultClient`
**nincs köztük** (0 találat). Az őr helyesen működik; a hiba csak
kívül esik a hatókörén.

### 48.2 Miért nem elég a grep

Kézi felmérést futtattam mind az **52** `QSettings`-kulcsra. A puszta
„hány fájlban fordul elő" mérőszám **nem használható**: a kulcsok
nagy része szándékosan egyetlen `*_prefs.py` modulban él, és onnan
tulajdonságon át terjed. Példa az ellenkező irányra: az
`export/addnumbers` és az `export/watermarktext` **végig van kötve**
(`ExportDialogs.qml:240–242` → `export_controller.py:333` →
`exporter.py:234`), pedig a kulcs egyetlen fájlban szerepel.

⇒ **A kulcs–hatás lánc csak nyomkövetéssel dönthető el**, ezért ez a
kör **nem** állítja, hogy a mail-eset volt az egyetlen. Amit állít: a
`view/*`, `collage/*` és `export/*` családból a végigkövetett tételek
rendben vannak, és az osztály **gépi őr nélkül** van.

### 48.3 Amit a meglévő őr közben talált — 16 néma tag

A `nema_slotok.py` mai futása **16** olyan `@Slot`/`@Property` tagot
jelöl, amit sem QML-ből, sem Pythonból nem hív senki (pl.
`copyEffects`, `undoPasteEffects`, `hasEffectsClipboard`,
`setFolderDescription`, `movePhoto`, `setTrayUsed`, `locationOfRow`).

⚠️ **Ez a lista NEM hibalista**: az őr saját kimenete átvizsgálást
igényel (lehet köztük teszt-célú vagy szándékosan tartalék tag). A kör
**nem** minősíti őket — csak rögzíti, hogy az őr fut és van kimenete,
amit senki nem néz át rendszeresen.

### Nyitott kérdések mérlege (48.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a negyedik állapot megnevezése és az, hogy a két meglévő
  őr nem fogja meg (48.1, mérve); hogy a puszta előfordulás-számlálás
  nem alkalmas őrnek (48.2).
- **BLOKKOLT:** *hány további néma beállítás van?* Gépi őr nélkül nem
  dönthető el, kézzel mind az 52 kulcs végigkövetése egy kör alatt nem
  fér bele. **Mi kell hozzá:** a 48.1-ben leírt harmadik őr (jegy
  nyílt rá). Addig a válasz **nem** „nincs több", hanem „nincs megmérve".

### Amit KIZÁRTAM

- **„A meglévő néma-őrök megfogják a 47. kör hibáját"** — megdőlt: a
  `nema_slotok.py` 16 találata közt nincs ott (48.1).
- **„Az `export/*` beállítások is némák"** — megdőlt: a végigkövetett
  export-lánc rendben van (48.2).


## 49. tétel — KÉT SAJÁT HELYESBÍTÉS (2026-09-01)

*Nem új kutatás: két korábbi körömet egy testvér-munkamenet mérése
javította ki. Mindkettő olyan hiba, amit a saját szabályaim tiltanak —
ezért kerül külön tételbe, nem lábjegyzetbe.*

### 49.1 ⚠️ „A Nézet menühöz tartozik" ≠ „a Nézet menü FELSŐ SZINTJÉN van"

A 36.5 pontban azt írtam, hogy a `ID_VIEWBY*` ötös a menüsáv Nézet
menüjében ül, és ebből nyílt a **#1766**. A bizonyíték: a pipázó
(`0x00574b70`) a `GetSubMenu(GetMenu(hwnd), 2)`-t veszi, ami a harmadik
felső menü.

**Ez a bizonyíték a menü-HOVATARTOZÁST igazolja, a menün belüli HELYET
nem.** Egy almenü tételei ugyanannak a felső menünek a fogantyúja alatt
pipázódnak.

A tulajdonos képernyőmentése (#1774) szerint a Nézet menü **felső
szintjén nincs** rendezés-tétel — és ezeken a mentéseken **az inaktív
tételek is látszanak**, tehát a hiány valódi hiány, nem elrejtett tétel.

⇒ **A #1766 leállítva, `felhasználóra-vár` állapotban**: egy mentés kell
a kinyitott **Nézet ▸ Mappanézet** almenüről. Ha ott vannak, a jegy
hatóköre az almenüre szűkül.

**Amit ebből tanulni kell:** a `GetSubMenu(…, N)` a **fogantyút** adja
meg, nem a pozíciót. Aki ebből helyre következtet, egy szinttel téved.

### 49.2 ⛔ A #1798-nál a lánc MÁSIK vége volt elvágva

A 47. körben kimutattam, hogy a `sendRows()` nem olvassa a
`mail/useDefaultClient` beállítást — **igaz volt**. A megvalósító kör
viszont a saját szabályomat („előbb a mi oldalunkat mérd") elvégezte, és
mélyebb okot talált:

> **A `sendRows()`-nak EGYETLEN hívója sem volt** — sem QML-ből, sem
> Pythonból. A tálca „E-Mail" gombja engedélyezve volt és kattintható,
> de a `TrayBar.emailRequested()` jelzést senki nem fogta el. (A
> testvérei — export, nyomtatás, kollázs, film — mind be voltak kötve.)

⇒ **A rádiógomb nem azért volt néma, mert a küldés rosszul olvasta a
beállítást, hanem mert küldés nem volt.**

**A hibám:** a láncnak csak a **végét** mértem (olvassa-e a beállítást),
és nem kérdeztem meg, hogy a lánc **eleje** létezik-e. Ha a jegy „Kész,
ha" pontjait valaki szó szerint teljesíti, a gomb **ma is néma maradna,
csak „helyesen" néma**.

**Szabály, ami ebből következik, és a 48. tételt kiegészíti:**

> Néma vezérlő leleténél **a teljes láncot** kell megmérni, mindkét
> irányból: (1) van-e **hívó** — a jelzést elfogja-e valaki; (2)
> elér-e a hívás a **műveletig**; (3) olvassa-e a művelet a
> **beállítást**. A három közül bármelyik szakadása ugyanolyan némaságot
> okoz, és a leletből nem derül ki, melyik.

*(A projekt „mérd a bekötés LÁNCÁT, ne a végpontokat" tanulsága ez —
és ebben a körben ÉN sértettem meg, miközben más köröknél épp erre
hivatkoztam.)*

### 49.3 A közös minta a két helyesbítésben

Mindkét hiba ugyanaz: **a bizonyíték igaz volt, a belőle levont
következtetés tágabb.**

| amit mértem | amit állítottam | ami hiányzott |
|---|---|---|
| a pipázó a 3. felső menü fogantyúját veszi | „a Nézet menü felső szintjén vannak" | a fogantyú nem pozíció |
| a `sendRows()` nem olvassa a beállítást | „ezért néma a gomb" | a `sendRows()`-nak nincs hívója |

⇒ **Az állítás hatóköre soha ne legyen tágabb, mint a mérésé.** Ha a
mérés a hovatartozást adja, ne írj pozíciót; ha a lánc egy szemét
méred, ne írj okot az egész láncra.

### Nyitott kérdések mérlege (49.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a `GetSubMenu` bizonyítóerejének határa (49.1); a #1798
  valódi oka és a belőle következő lánc-szabály (49.2).
- **BLOKKOLT:** hol állnak pontosan a `ID_VIEWBY*` tételek a Nézet
  menüben. **Mi kell hozzá:** képernyőmentés a kinyitott
  **Nézet ▸ Mappanézet** almenüről. A kérés a #1766-on áll,
  `felhasználóra-vár` címkével — nem az én köröm zárja le.

### Amit KIZÁRTAM

- **„A `GetSubMenu(…, 2)` megadja a tétel helyét a menüben"** — megdőlt:
  a fogantyút adja meg; almenü-tételek ugyanoda tartoznak (49.1).
- **„A #1798 oka a beállítás olvasásának hiánya"** — megdőlt: a
  `sendRows()`-nak nem volt hívója (49.2).

## 50. tétel — a `publish`: HÁROM panel egy névtérben, és a Picasa WINE-tudata (2026-09-01)

*Tizenegyedik kör az UI-lefedettségi axisról (#1778). Panel: `publish`
(30 hiány). A (d) szabály próbája: a leltár leírása szerint
„Biztonsági mentés / Ajándék-CD / webre töltés — nincs nálunk", ami
egyben csábítás is, hogy az egészet halott szolgáltatásnak minősítsük.*

### 50.1 ⛔ NEM egy panel: három, és csak az EGYIK halott

A `publish` névtér elemei három, egymástól független funkcióhoz
tartoznak:

| csoport | elemek | állapot |
|---|---|---|
| **biztonsági mentés** | `backup_go/cancel/eject/help`, `backupcdheader2`, `backuptext2/3`, **`newbackupset` · `editbackupset` · `deletebackupset`**, `selectall`, `selectnone` | **ÉL** → #440 |
| **Ajándék-CD** | `presentcd_go/cancel/eject/help`, `giftcdtext`, `addmore`, `picsizemenu` | **ÉL** (lemezre írás) → #32 |
| **webre töltés** | `rpoptionbox1/2/3` + feliratok, `uploadallsync`, `upgradestorage`, `webpublish_cancel`, `replicate_*` | **HALOTT** (Picasa Web Albums) |

⇒ Ha a panelt egyben zárnánk le „megszűnt szolgáltatás" címén, **két élő
funkció veszne el** vele. *(Ez a 47. kör `choose_mail`-csapdájának
ismétlődése — most már szabályként fogtuk meg.)*

### 50.2 ⭐ A mentés-KÉSZLET első osztályú fogalom

> ⭐ **2026-09-02 — a MŰKÖDÉS oldala külön lapon:**
> [`biztonsagi-mentes.md`](biztonsagi-mentes.md). Ez a szakasz a *fogalmat*
> és a *felületet* adja; hogy mit ír a lemezre (`backups.xml` négy mezővel,
> három tartalom-mód, `files.txt` a célmappában, honosított mappanév,
> lemezhely-ellenőrzés), az ott áll.

A 35.6 pont a `backup.xml`-t és a `backuphash` ini-kulcsot rögzítette. A
panel ennél többet mond: a mentés **nevesített készletekbe** szerveződik,
teljes életciklussal.

| művelet | bizonyíték |
|---|---|
| **új készlet** | `publish/newbackupset` · `il_BurnPanel::bksetname` |
| **szerkesztés** | `publish/editbackupset` · **„Edit Backup Set"** párbeszéd (`0x00678e80`), címe `il_NewBkDialog::EditTitle`, gombja `il_NewBkDialog::EditOKButton` („Change") |
| **átnevezés hibája** | *„Unable to rename Backup Set"* (`0x00679ca0`) |
| **törlés** | `publish/deletebackupset` + megerősítés: ***„Are you sure you want to delete the backup set \"%s\"?"*** |
| **alapértelmezett név** | **„My Backup Set"** (`0x006706d0`) |
| **melyik volt az utolsó** | `Preferences\LastBkSet` |
| **futás közbeni állapot** | *„Updating Backup Set"* (`0x00672f50`) |

**A CD-oldali beállítások** (ugyanott, `0x006706d0`):
`Preferences\CDEraseFirst` · `CDLimitSize` · `CDSlideshow` ·
`CDSlideshowInclSetup` · `UploadAllSize`, és a lemezre kerülő
**`setup.exe`** — ez zárja a kört a 35.6-ban említett „szállított
nézőprogram" megfigyeléssel.

### 50.3 ⭐ A Picasa MAGA tudott a Wine-ról

A mentés-készlet szerkesztője (`0x00678e80`) mellékesen elárul valamit,
ami eddig sehol nem szerepelt nálunk:

| bizonyíték | mit jelent |
|---|---|
| **`wine_get_unix_file_name`** (`0x00403640`, `kernel32`-ből feloldva) | a bináris **futásidőben megkérdezi a Wine-t**, mi a Windows-út UNIX-megfelelője |
| **`Preferences\ShowUnixPaths`** — **hét** függvényben (`0x00672380`, `0x00678e80`, `0x006befa0`, `0x00738c00`, `0x0073a140`, `0x00749ba0`, `0x007e3210`) | kapcsoló: a felület **UNIX-útvonalakat** mutasson-e Windows-osak helyett |
| `%s (wine)` (`0x00990ee0`) | a Wine jelenléte megjelenik egy megjelenített szövegben |
| `runtime\winedisable.txt` (`0x006e0670`) | szállított fájl a Wine-specifikus viselkedés kikapcsolására |

⇒ **A Picasa 3.9 nem „véletlenül futott Wine alatt": felismerte, és a
felületét is igazította hozzá.** Ez a hivatalos „Picasa for Linux"
csomag Wine-alapú voltának bizonyítéka a binárisból.

**Miért érdekes nekünk (Linux-first projekt):** a `ShowUnixPaths` hét
helyen hat, tehát az útvonal-megjelenítés **kereszmetsző** kérdés volt
náluk is. Nálunk ez nem kérdés (natívan UNIX-utakat mutatunk) — de a
`.picasa.ini`-kompatibilitásnál érdemes tudni, hogy az **eredeti is
kétféle útvonal-alakot ismert**.

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| mentés-készletek (új/szerkeszt/töröl) | teljes életciklus, megerősítéssel | a menütétel **placeholder** (35.6) | a **#440** kapja meg |
| `LastBkSet`, `My Backup Set` | tartós állapot + alapnév | nincs | ua. |
| Ajándék-CD | lemezre írás, `setup.exe`-vel | nincs | **#32** |
| CD-beállítások (`CDEraseFirst`, `CDLimitSize`, `CDSlideshow*`) | négy kulcs | nincs | ua. |
| webre töltés | `rpoptionbox*`, `upgradestorage` | — | **hatókörön kívül** |
| `ShowUnixPaths` | hét helyen ható kapcsoló | nálunk tárgytalan | — (tudás, nem teendő) |

### Nyitott kérdések mérlege (50.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a panel háromfelé bontása és annak eldöntése, melyik ága
  halott (50.1); a mentés-készlet mint első osztályú fogalom, teljes
  szövegkészlettel (50.2); a Picasa Wine-tudata (50.3).
- **HATÓKÖRÖN KÍVÜL:** a webre töltés ága.

*(Záró mondat a 45.1 szerint: ebben a panelben **van** hiányzó vezérlő;
a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A `publish` panel egészében halott szolgáltatás"** — megdőlt: három
  funkció lakik benne, kettő él (50.1).
- **„A biztonsági mentés egyetlen művelet"** — megdőlt: **nevesített
  készletek**, létrehozás/szerkesztés/törlés életciklussal (50.2).
- **„A Picasa nem tudott róla, hogy Wine alatt fut"** — megdőlt:
  `wine_get_unix_file_name`, `ShowUnixPaths` hét helyen, `%s (wine)`,
  `winedisable.txt` (50.3).

## 51. tétel — a `thumbui`: a hiányok nagy része ESZKÖZTÁRGOMB, és egy valódi hiányzó eszköz (2026-09-01)

*Tizenkettedik kör az UI-lefedettségi axisról (#1778). Panel: `thumbui`
(41 hiány) — a fő könyvtárnézet. A „nézd meg a testvéreket" fogással.*

### 51.1 A hiányok fő mintája: menüben megvan, eszköztáron nincs

Nyolc elem **megvan nálunk**, csak **más helyen**: az eredetiben
eszköztárgomb, nálunk menütétel vagy helyi menü. Mindegyik felvéve a
`ui-lefedettseg-elemek.csv`-be, fájllal és sorszámmal:

| eredeti (eszköztár) | nálunk |
|---|---|
| `smallthumbs` / `largethumbs` | Nézet menü, `thumbSizePreset(96)` / `(144)` (`PicasaMenuBar.qml:301/306`) |
| `rotateleft` / `rotateright` | Kép menü + fotó helyi menü |
| `scratchhold` / `scratchclear` | képtálca `trayHold` / `trayClear` (`TrayBar.qml`) |
| `newalbum` | bal hasáb (`FolderPane.qml`, `AlbumsSection.qml`) |
| `thumbui/newfolder` | Fájl menü „Áthelyezés új mappába…" |

Hatás a táblán: párosítva 135 → **143**, hiányzik 396 → **388**.

⇒ **Ez nem funkcióhiány, hanem ELHELYEZÉS-kérdés**, és a fő eszköztár
hiányzó vezérlőit már a **#853** tartja számon. Ide nem nyílik új jegy.

### 51.2 A négy fiók-kapcsoló: itt is, ott is

`people_toggle` · `places_toggle` · `properties_toggle` · `tags_toggle` —
a 37. tételben már feltárt jobb fiók-lapok, de itt **eszköztárgombként**.
A menü-oldaluk nálunk megvan (37.), az eszköztár-oldaluk nem — ugyanaz az
elhelyezés-kérdés, ugyanaz a jegy (**#853**), és a kizáró viszonyuk a
**#1773**.

### 51.3 ⭐ Ami VALÓBAN hiányzik: a nagyító (`loupe`)

> `loupehit` — buboréksúgó: **„Click and drag over photos to magnify
> them"**

Egy **nagyító**, amit a bélyegkép-rács fölött húzva a képek nagyítva
jelennek meg. Saját felületi csomópontjai vannak (`loupe`,
`loupe/loupe_sm`, kezelő `0x0077be10`), és a `thumbui/loupe` néven a
rács vezérlőihez kapcsolódik (`0x005733f0`).

**Nálunk mérve: nincs.** A „nagyít"/`magnif`/`loupe` keresés a
QML-fában csak a kollázs-csomópontra, a szerkesztő effekt-fülére, a
bélyegkép-delegáltra és a fő eszköztárra ad találatot — **egyik sem
rács-nagyító**.

> ⚠️ **ELAVULT (2026-09-02).** Ez a bekezdés a megírása napján (2026-08-31,
> `50c61fdd`) igaz volt; **másnap** a #1808 megépítette a nagyítót
> (`3070080c`), majd a #1911 kivette a bekapcsoló gombját. A mai állapot:
> a rajz és a húzás-kezelés **megvan** (`LightboxFeed.qml:787–878`,
> `Main.qml:88`), **a gomb hiányzik**. A teljes feltárás — alak, méret,
> áttűnés, és hogy külön egérmutató **nincs** — az új lapon:
> [`racs-nagyito.md`](racs-nagyito.md).

⇒ Ez **önálló, felhasználónak látszó funkció**, nem elhelyezés-kérdés.

### 51.4 A többi valódi hiány, besorolva

| elem | mi ez | hova tartozik |
|---|---|---|
| `webcambutton` | webkamerás felvétel | **#853** (a négy hiányzó eszköztár-vezérlő egyike) |
| `visitweb` („Internetes nézet") · `backup` · `cdmode` („Ajándék CD") | eszköztár-gombok | `visitweb` **hatókörön kívül**; `backup` → #440; `cdmode` → #32 |
| `single_action_*` hármas | a „Get more" mód üzenetsávja: *„Jelölje ki… majd a »Vissza« gombra kattintva térjen vissza a projekthez"* | a kollázs/film **klip-gyűjtő módja** — a projektpanelekhez tartozik |
| `lightbox_esolo_button` / `_text` | *„Nincs találat ebben az albumban"* + **„Keresés mindenhol"** gomb | ⛔ **2026-09-02: HALOTT az eredetiben** — nyers bájtkeresésre 0 találat a teljes `Picasa3.exe`-ben, és `showtarget`/`hidetarget` sincs rájuk. **NE épüljön meg.** A helyette élő üres-állapot: [`racs-ures-allapot.md`](racs-ures-allapot.md), jegy **#1945** |
| `flatview` · `folderview` · `folderviewpopup` | a bal hasáb nézetváltói | a 36./4c körökben feltárva; **#1407**, **#853** |

### Eredeti / nálunk / teendő

| | eredeti | nálunk (**mérve**) | teendő |
|---|---|---|---|
| rács-nagyító | húzásra nagyít | **nincs** | **ÚJ JEGY** |
| kis/nagy indexkép, forgatás, tálca, új album/mappa | eszköztáron | **megvan**, máshol | — (elhelyezés: #853) |
| négy fiók-kapcsoló | eszköztáron | menüben megvan | #853 + #1773 |
| webkamera | eszköztárgomb | nincs | #853 |
| „Nincs találat… / Keresés mindenhol" | **halott vezérlő** | nincs | **nem építjük** — helyette a `lightbox_bgtext` (#1945) |

### Nyitott kérdések mérlege (51.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a hiányok fő mintája (elhelyezés, nem funkció — 51.1–51.2);
  a nagyító léte és a mi oldalunk hiánya (51.3).
- ~~**BLOKKOLT:** a nagyító **viselkedési részletei**~~ — **2026-09-02:
  nagyrészt LEZÁRVA** ([`racs-nagyito.md`](racs-nagyito.md)): a `loupe_sm`
  **51 × 51**, a 103 × 103-as lencse **belső** rétege; a nagyító a kurzor
  **közepére** ül; a megjelenés **áttűnéses** (0,4 be / 1,2 ki, alfa
  1…256); és **nincs saját egérmutató**. **Marad blokkolt:** csak a
  **nagyítás mértéke** — a megszerzés útja a `0x0077bb10` rajzoló ág.
- **HATÓKÖRÖN KÍVÜL:** `visitweb` („Internetes nézet").

*(Záró mondat a 45.1 szerint: **van** hiányzó vezérlő; a csoportosztás
nincs mérve.)*

### Amit KIZÁRTAM

- **„A `thumbui` 41 hiánya 41 hiányzó funkció"** — megdőlt: nyolc elem
  megvan más helyen, négy a jobb fiók már feltárt lapja, több pedig
  meglévő jegyekhez tartozik (51.1–51.4).
- **„A nagyító nálunk is megvan valamilyen alakban"** — megdőlt: a
  QML-fában nincs rács-nagyító (51.3).

## 52. tétel — a KÉTKÉPES összevetés, és a „melyik szerkesztést tartsuk meg?" (2026-09-01)

*Tizenharmadik kör az UI-lefedettségi axisról (#1778). Az `editpanel`
(83 hiány) **egy szelete**: a kép-nézet vezérlői. A teljes szerkesztő
nem egy kör munkája — a 42. kör tanulsága szerint félbehagyva többet
ártana —, ezért a négy összevetés/nagyítás-vezérlő önálló egységként.*

### 52.1 A négy vezérlő

| elem | buboréksúgó |
|---|---|
| `1to1` | „Display Photo at actual size" (**1:1 nagyítás**) |
| `fit` | „Fit Photo inside viewing area" (**ablakhoz illesztés**) |
| **`aa_2up_toggle`** | **„View the same image twice"** |
| **`ab_2up_toggle`** | **„View two different images"** |

⇒ Két külön kétképes mód: **A-A** (ugyanaz a kép kétszer) és **A-B**
(két különböző kép).

### 52.2 ⭐ Az A-A mód nem csak nézet: KÉT KÜLÖN SZERKESZTÉS

A kilépéskori megerősítő (`0x0056aad0`) elárulja, mire való valójában:

| elem | szöveg |
|---|---|
| cím | **„Choose Edits"** (`CThumbUI::Confirm2upEditTitle`) |
| üzenet | ***„The same image has two different edits. Which one would you like to keep?"*** (`…EditMsg`) |
| gombok | **Top** · **Bottom** · **Left** · **Right** (`Confirm2upTop/Bottom/Left/Right`) + Mégse |
| jelölőnégyzet | **„Don't ask again, always use the selected image"** (`…EditDontAsk`) → `Preferences\DoNotAskOnEnd2Up` |

⇒ **Az A-A módban a két példány KÜLÖN szerkeszthető**, és kilépéskor a
Picasa megkérdezi, melyiket tartsd meg. Ez nem összehasonlító nézet,
hanem **próbálgatós szerkesztés**: két változatot viszel párhuzamosan,
és a végén választasz.

⇒ **A Top/Bottom ÉS a Left/Right gombpár egyaránt létezik** ⇒ az osztás
**vízszintes és függőleges is lehet**, és a megerősítő a tényleges
elrendezéshez igazítja a gombfeliratokat.

### 52.3 Nálunk: háromgombos placeholder

A `PhotoViewer.qml:590` kimondja:

```qml
// #6: A/AB/AA összehasonlító nézetek — placeholder (a
// szerkesztő-összevetés a 2. fázisban élesedik)
PicasaButton { objectName: "compareButtonA";  text: "A";  enabled: false }
PicasaButton { objectName: "compareButtonAB"; text: "AB"; enabled: false }
```

⇒ A gombok **léteznek, de `enabled: false`** — vagyis nem néma
vezérlők (a szürkítés őszinte), csak nincs mögöttük funkció. A
`1to1` / `fit` nagyítás-vezérlőkre a QML-fában **nincs találat**.

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| A-A mód | ugyanaz a kép kétszer, **külön szerkeszthető** | `compareButtonA`, szürke placeholder | **#6** kapja meg |
| A-B mód | két különböző kép | `compareButtonAB`, szürke placeholder | ua. |
| kilépéskori választás | „Choose Edits" párbeszéd, 4 irány-gombbal | nincs | ua. |
| „ne kérdezd többet" | `Preferences\DoNotAskOnEnd2Up` | nincs | ua. |
| 1:1 nagyítás · ablakhoz illesztés | két külön vezérlő | **nincs** a QML-fában | ua. |

### 52.4 Miért a #6 kapja, és nem új jegy

A négy vezérlő **egyetlen funkcióhoz** tartozik (a szerkesztő
összevetés-módja), amire **már van jegy** (#6), és amit a kódunk
kommentje is nevesít. Új jegy csak szétszórná a tudást. *(A
„gyűjtőjegy nem elég" szabály itt nem sérül: a lelet nem önálló,
hanem épp annak a jegynek a tartalma, amire a placeholder hivatkozik.)*

### Nyitott kérdések mérlege (52.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a négy vezérlő szerepe (52.1); az A-A mód valódi célja és
  a kilépéskori választás teljes szövegkészlete (52.2); a mi
  placeholder-állapotunk (52.3).
- **BLOKKOLT:** mikor **vízszintes** és mikor **függőleges** az osztás
  (a gombfeliratok mindkettőt kínálják, a választás szabálya nincs
  mérve). **Mi kell hozzá:** képernyőmentés a kétképes módról, vagy
  célzott dekompiláció a `0x0056b130`-ra. **A #6-ot nem blokkolja**: a
  megvalósítás választhat egy irányt, ha kimondja, hogy saját döntés.

### Amit KIZÁRTAM

- **„Az A-A mód puszta előtte/utána összehasonlítás"** — megdőlt: a két
  példány **külön szerkeszthető**, és a kilépés választást kér (52.2).
- **„A kétképes mód gombjai nálunk némák"** — megdőlt: `enabled: false`,
  tehát szürkék és őszinték (52.3). *(Ellentétben a #1798 esetével, ahol
  a vezérlő kattintható volt és nem csinált semmit.)*

## 53. tétel — az `editpanel` HÁROM eszköz-füle: mind megvan (2026-09-01)

*Tizennegyedik kör az UI-lefedettségi axisról (#1778). Az `editpanel`
(83 hiány) második szelete: a **vágás**, a **retus** és a **vörösszem**
fül. A 42. kör tanulsága szerint a szerkesztőt fülenként visszük.*

### 53.1 Tíz elem — mind TÉVES RIASZTÁS

A három fül tíz jelölt eleméről a mérés azt mondja: **megvan nálunk**,
csak más néven vagy más megfogalmazásban. Mind felvéve a
`ui-lefedettseg-elemek.csv`-be, fájllal és sorszámmal:

| eredeti | nálunk (`EditorCropPanel.qml`) |
|---|---|
| `editpanel/croptext` | „Choose a size below, then drag on the picture to…" (56. sor) |
| `crop_aspect_menu` | `cropAspectCombo` (81.) + `cropAspectList` (109.) |
| `editpanel/crop_delete_custom` | `cropAspectDelete<i>` (164.), **megerősítéssel** („Delete this custom aspect ratio?", 186.) |
| `editpanel/cropsug_preview1/2/3` | `cropSuggestion0/1/2` (270–272.), a „Suggested crops" sorban (237.) |

| eredeti | nálunk (retus / vörösszem) |
|---|---|
| `retouch_label` · `editpanel/retouchtext` | `EditorRetouchPanel.qml:47` · `:56` |
| `editpanel/redeye_label` · `editpanel/redeyetext` | `EditorRedeyePanel.qml:55` · `:64` |

Hatás a táblán: párosítva 143 → **153**, hiányzik 388 → **382**,
bizonytalan 158 → **154**.

### 53.2 Amit a mi oldalunk TÖBBET tud

A mérés a hiányt keresi, a többletet nem mutatja. Három tétel, amit a
QML-fa ad, és az eredeti elemleltárában nincs megfelelője:

| nálunk | mi ez |
|---|---|
| `cropStraightenWarning` (`EditorCropPanel.qml:67`) | figyelmeztetés, ha a kép tájolását az **egyenesítés** módosította |
| `cropAspectAddRow` + „Add Custom Aspect Ratio…" (203., 210.) | egyéni képarány **hozzáadása** — az eredetiben csak a **törlés** (`crop_delete_custom`) van nevesítve |
| `quickCropTopleft` · `quickCropLandscape` (280., 285.) | gyors-vágás gombok |
| „Regions selected: %1" (`EditorRetouchPanel.qml:89`) | a retusált régiók **számlálója** |
| „Picasa has found and corrected red eye(s)." / „No red eye was found automatically." (`EditorRedeyePanel.qml:79–80`) | az automatikus vörösszem-keresés **visszajelzése** |

⇒ **A három fül nálunk nem szegényebb, hanem helyenként gazdagabb.**
*(A „gazdagabb" itt nem érdem, hanem tény: a 45.3 eltérés-tábla
szempontjából ezek **tudatos többletek**, nem hiányok — és nem is
eltérések az eredetitől, mert az eredeti sem tiltja őket.)*

### 53.3 Az eredeti útmutató-szövegei — a fogalmazás átvehető

Az eredeti három útmutatója a hivatalos magyar fordítással megvan a
leltárban, és **pontosabb**, mint a miénk egy ponton: a retus-szövege
kimondja a **Ctrl+húzás pásztázást** is —

> *„…Megjegyzés: a Ctrl billentyűt nyomva tartva az egér húzásával
> pásztázhat."*

A mi `EditorRetouchPanel.qml:56` szövege ezt **nem említi**. Ha a
pásztázás nálunk működik, a mondat átvehető; ha nem működik, az külön
kérdés.

⇒ Ez **nem hiányzó vezérlő**, hanem **szöveg-pontosítás** — nem jegy,
hanem a 45.3 tábla „tudott eltérés" sora, amíg valaki meg nem méri, hogy
a Ctrl+húzás nálunk működik-e.

### Nyitott kérdések mérlege (53.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a tíz elem téves riasztás volta (53.1); a mi többletünk
  leltára (53.2).
- **BLOKKOLT:** működik-e nálunk a **Ctrl+húzás pásztázás** a retus-fülön.
  Ez a mi kódunk kérdése, nem a binárisé; egy dev-kör grep-pel eldönti.
  **Nem nyitok rá jegyet**, mert a válasz nélkül nem lehet megmondani,
  hogy szöveg-hiány vagy funkció-hiány — a 45.3 táblába viszont bekerül.

*(Záró mondat a 45.1 szerint: ebben a három fülben **nincs hiányzó
vezérlő**; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„Az `editpanel` 83 hiánya mind valódi"** — megdőlt: az első két
  szeletben (kép-nézet, 52. tétel; három eszköz-fül, most) tíz elem
  téves riasztás volt, és a kép-nézetnél is csak a kétképes mód hiányzik
  valóban.
- **„A vágás-javaslatok nálunk nincsenek"** — megdőlt: `cropSuggestion0/1/2`
  (53.1). *(Ez a 46. körben tett saját megjegyzésem pontosítása is: ott
  azt írtam, hogy a „suggestion" szó nálunk csak a vágásra utal — igaz
  volt, de úgy hangzott, mintha kevés lenne; valójában ez a vágás-fül
  teljes értékű funkciója.)*

## 54. tétel — a szöveg-fül és a FELIRAT két hiányzó vezérlője (2026-09-01)

*Tizenötödik kör az UI-lefedettségi axisról (#1778). Az `editpanel`
harmadik szelete: a **szöveg-fül** és a hozzá tartozó **felirat**-vezérlők.*

### 54.1 A szöveg-fül nálunk teljes

Az `EditorTextPanel.qml` (22 feliratos vezérlő) a szövegráírás teljes
készletét adja: szövegmező (`textContentField`), **„Copy Caption"**
gomb („Add text based on the picture's caption"), betűtípus- és
méretválasztó, **félkövér / dőlt / aláhúzott**, és **három igazítás**
(bal / közép / jobb).

⇒ Az `edittextpanel` és az `edittextghost` jelöltek **téves riasztások**
(szerkezeti tartók, felirat nélkül; a 45.1 szerint a mérés ezeket nem
tudja értékelni).

### 54.2 ⛔ Ami VALÓBAN hiányzik: a felirat két vezérlője

| eredeti | buboréksúgó | nálunk (**mérve**) |
|---|---|---|
| **`captionbutton`** | **„Show/Hide Caption"** | **nincs** |
| **`captiontrash`** | **„Delete this caption"** | **nincs** |
| `showtextcheckbox` | „Toggle to show or hide text on a photo" | **nincs** |

Nálunk a `PhotoViewer.qml:1536` `captionField`-je **szerkeszthető
felirat-mező**, de:

- **nincs mód elrejteni** a feliratot (a mező mindig ott van);
- **nincs egy mozdulatos törlés** — a szöveget kézzel kell kijelölni és
  kitörölni.

*(Mérve: a `show.*text` / `hide.*text` / `delete.*caption` / `clearCaption`
keresés a QML-fában és az `app/`-ban **nulla** találat.)*

### 54.3 ⭐ A felirat láthatósága TARTÓS ÁLLAPOT

A `captionbutton` nem pillanatnyi kapcsoló: az állapota **túléli a
programindítást**.

| bizonyíték | mit jelent |
|---|---|
| **`Preferences\LastCaptionButton`** (`0x00576a20`, a `Preferences` és az `editpanel/captionbutton` mellett ugyanabban a függvényben) | a felirat-sáv **utolsó állapota** |
| ugyanez a kulcs a **főablak-építőben** is (`0x0040bf70`) | induláskor **visszaállítja** |
| szomszédja: `LastNerdView` | ugyanaz a minta a „nerd" (EXIF-részletes) nézetre |

⇒ **Ha egyszer elrejtetted a feliratot, a Picasa legközelebb is
elrejtve indul.**

### 54.4 KÉT belépési pont — a szerkesztőben és az egyképes nézetben

A `captionbutton` **két névtérben** él:

| névtér | hol |
|---|---|
| `editpanel/captionbutton` | a szerkesztő panelen (`0x0040bf70`, `0x00565cf0`, `0x00566a70`, `0x00568010`, `0x00576a20`) |
| **`editoneup/captionbutton`** | az **egyképes nézetben** (`0x0075eac0`, `0x0075f430`, `0x00760240`) |

⇒ A felirat-kapcsoló **mindkét nézetben** ott van, és a `0x0057bb50`
kezelő a `captionbutton` · `caption` · `captiontrash` hármast együtt
kezeli.

*(Ez a 2/b szabály 1. pontja élesben: egy vezérlő több belépési ponttal —
ha csak az egyiket építjük meg, a másik nézetben hiányozni fog.)*

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| szövegráírás (betű, stílus, igazítás) | teljes | **teljes** (`EditorTextPanel.qml`) | — |
| „Copy Caption" | a felirat átemelése szövegként | **megvan** (`:58`) | — |
| felirat **elrejtése** | `captionbutton`, két nézetben | **nincs** | ÚJ JEGY |
| felirat **törlése** | `captiontrash` | **nincs** | ua. |
| az elrejtés **megjegyzése** | `Preferences\LastCaptionButton` | nincs | ua. |
| szöveg elrejtése a fotón | `showtextcheckbox` | nincs | ua. |

### Nyitott kérdések mérlege (54.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a szöveg-fül teljessége nálunk (54.1); a két hiányzó
  felirat-vezérlő és a mi mérésünk (54.2); a láthatóság tartóssága és a
  két belépési pont (54.3–54.4).

*(Záró mondat a 45.1 szerint: ebben a szeletben **van** hiányzó vezérlő —
kettő; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A szöveg-fül nálunk hiányos"** — megdőlt: a teljes készlet megvan,
  a jelölt két elem szerkezeti tartó (54.1).
- **„A felirat-kapcsoló pillanatnyi állapot"** — megdőlt:
  `Preferences\LastCaptionButton`, a főablak-építő visszaállítja (54.3).
- **„A felirat-kapcsoló csak a szerkesztőben van"** — megdőlt: az
  egyképes nézetben is (`editoneup/captionbutton`, 54.4).

## 55. tétel — a finomhangolás és az effekt-fülek: négy téves riasztás, egy valódi hiány (2026-09-01)

*Tizenhatodik kör az UI-lefedettségi axisról (#1778). Az `editpanel`
**negyedik szelete**: a finomhangolás-fül és az effekt-fülek vezérlői.*

### 55.1 A finomhangolás nálunk teljes

Az `EditorFinetunePanel.qml` a teljes készletet adja: **Fill Light** ·
**Highlights** · **Shadows** + „One-click lighting fix" varázspálca ·
**Color Temperature** · **Neutral Color Picker** (mintaszín + pipetta) +
„One-click color fix".

A `droppertoggle` buboréksúgója az eredetiben *„Allows you to pick a
neutral gray or white part of the Photo to remove color cast"*; nálunk
*„Pick a neutral gray or white area of the photo to…"* (`:211`) —
ugyanaz a tartalom, más megfogalmazás, ezért nem párosult gépi úton.

### 55.2 Négy elem felülbírálva

| eredeti | nálunk | fájl:sor |
|---|---|---|
| `filllight_icon` | „Fill Light" + `finetuneFillSlider` | `EditorFinetunePanel.qml:105`, `:108` |
| `droppertoggle` | `finetuneNeutralPicker` | `:208`, `:211` |
| `editpanel/faces_button` | `facesToggleButton` + `facesVisible` | `PhotoViewer.qml:1490`, `:165–166` |
| `filter_name` | `effectParamTitle` (az aktív effekt neve) | `EditorParamPanel.qml:191` |

Tábla: párosítva 153 → **157**, hiányzik 382 → **380**, bizonytalan
154 → **152**.

*(Az `editpanel/editcircle1`, `editpanel/editcircle1_well`, `editcontrol_well`,
`editcheckbox1/2` **felirat nélküli szerkezeti tartók** — a 45.1 szerint
a mérés ezeket nem tudja értékelni, és önmagukban nem jelentenek
funkcióhiányt.)*

### 55.3 Ami valóban hiányzik: `editslideshow` — „Edit Movie"

> `editslideshow` — **„Edit Movie"** / **„Mozgófilm szerkesztése"**

Egy gomb a szerkesztő panelen, amivel a **filmkészítőbe** lehet átlépni.
Nálunk mérve **nincs** (`grep -i "Edit Movie|film szerkeszt"` a
QML-fában: nulla találat).

⇒ **Nem nyílik rá új jegy:** a filmkészítő panel egésze hiányzik, és az
a **#432 / #452** jegyekhez tartozik — ez a gomb annak a **belépési
pontja**, nem önálló funkció. *(A „gyűjtőjegy nem elég" szabály másik
oldala, ugyanaz, mint a 46. körben.)*

### 55.4 A `edithelpbutton` — hatókör-kérdés, nem hiány

> `edithelpbutton` — buboréksúgó: „Help"

Az eredeti szerkesztő-paneljén súgógomb ül, ami a Picasa
súgórendszerébe visz. **A súgórendszer egésze hatókörön kívül**
(`HATOKORON_KIVUL` a menü-metrikában: `ID_HELP_*` parancsok), ezért ez
sem hiány, hanem **szándékos elhagyás** — bekerül a 45.3 táblába.

### Eredeti / nálunk / teendő

| | eredeti | nálunk (**mérve**) | teendő |
|---|---|---|---|
| finomhangolás (derítőfény, csúcsfény, árnyék, hőmérséklet, pipetta, két varázspálca) | teljes | **teljes** | — |
| aktív effekt neve | `filter_name` | `effectParamTitle` | — |
| arcok kapcsolója | `faces_button` | `facesToggleButton` | — |
| **„Edit Movie" gomb** | belépés a filmkészítőbe | **nincs** | **#432 / #452** |
| súgógomb | a Picasa súgójába visz | nincs | **hatókörön kívül** |

### Nyitott kérdések mérlege (55.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a finomhangolás teljessége (55.1); a négy téves riasztás
  (55.2); az `editslideshow` besorolása (55.3).
- **HATÓKÖRÖN KÍVÜL:** a súgógomb — a súgórendszer egésze az (55.4).

*(Záró mondat a 45.1 szerint: ebben a szeletben **nincs önállóan
megvalósítható hiányzó vezérlő** — az egyetlen valódi hiány egy másik
jegy belépési pontja; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A finomhangolás-fülünk hiányos"** — megdőlt: a teljes készlet
  megvan, két elem csak a fogalmazás miatt nem párosult (55.1–55.2).
- **„Az `editslideshow` önálló funkció"** — megdőlt: a filmkészítő
  belépési pontja, tehát a #432/#452-höz tartozik (55.3).

## 56. tétel — a `headerpanel`: fele halott, fele valódi hiány (2026-09-01)

*Tizennyolcadik kör az UI-lefedettségi axisról (#1778). Panel:
`headerpanel` (10 hiány) — az album- és mappafejléc a rács fölött.*

### 56.1 A tíz elem KÉTFELÉ oszlik

| csoport | elemek | állapot |
|---|---|---|
| **élő** | `save_edits` · `select_star` · `create_collage` · `create_movie` · `play` | 5 |
| **halott** | `sync_label` · `sync_options` · `view_online` · `websync0` · `websync1` | 5 (Picasa Web Albums) |

⇒ A (d) szabály próbája megint: a panel **fele** megszűnt szolgáltatás, a
másik fele nem. Egyben lezárva öt élő vezérlő veszne el.

### 56.2 Ami nálunk megvan, és ami nem

| eredeti | nálunk (**mérve**) |
|---|---|
| `play` („Play Fullscreen Slideshow") | **megvan** — `headerPlayButton` (`LightboxHeader.qml:131`) |
| `create_collage` · `create_movie` | **megvan, de a TÁLCÁN** (`TrayBar.qml`), nem a fejlécben ⇒ elhelyezés-kérdés (#853) |
| **`save_edits`** („Save edited photos to disk") | **nincs** |
| **`select_star`** („Select starred photos") | **nincs** |
| album cím + leírás | **megvan** (`folderTitleText`, `folderDescriptionField`) | 

*(Mérve: a `save_edits` / `Save.*disk` / `select_star` / `csillagozott`
keresés a `LightboxHeader.qml`-ben és a `TrayBar.qml`-ben **nulla**
találat.)*

### 56.3 ⭐ A fejléc-gombok SZÁMLÁLÓT mutatnak

A gomb-erőforrások **kétféle alakban** léteznek — sima és `%d`-s:

```
albumbutton_save    ·  albumbutton_save%d
albumbutton_sstar   ·  albumbutton_sstar%d
albumbutton_sall    ·  albumbutton_sall%d
albumbutton_album   ·  albumbutton_album%d
albumbutton_cd      ·  albumbutton_cd%d
albumbutton_menu    ·  albumbutton_menu%d   (+ `albumbutton_menu%d %x`)
albumbutton_pubaction · albumbutton_pubaction%d
```

⇒ **A fejléc gombjai kiírják, hány elemre hatnának** („Mentés (3)"), és
a felirat üres kijelölésnél másik alakra vált. *(A `%x` változat a
`menu`-nál egy második, hexadecimális mezőt is kap — nem mérve, mire.)*

### 56.4 A fejléc mezői és a tartós állapot

A kezelő (`0x00749ba0`) a fejléc szerkeszthető mezőit is nevesíti:
`album_title` · `album_description` · `info_text`; mellettük egy tartós
kulcs: **`Preferences\LastUserESState`**.

*(A `LastUserESState` jelentése **nem mérve** — a `Last*` minta szerint
tartós felület-állapot, de a rövidítés feloldása nélkül nem állítok
róla többet. Ugyanaz a család, mint a `LastCaptionButton` és a
`LastNerdView`, 54.3.)*

### Eredeti / nálunk / teendő

| | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| **szerkesztések mentése lemezre** | `save_edits`, számlálós felirattal | **nincs** | ÚJ JEGY |
| **csillagozottak kijelölése** | `select_star`, számlálós felirattal | **nincs** | ua. |
| diavetítés | `play` | **megvan** | — |
| kollázs / film | a fejlécben | a **tálcán** | #853 (elhelyezés) |
| cím + leírás | `album_title`, `album_description` | **megvan** | — |
| webes szinkron (5 elem) | Picasa Web Albums | — | **hatókörön kívül** |

### Nyitott kérdések mérlege (56.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a panel kettéosztása (56.1); a mi oldalunk mérése (56.2);
  a számlálós gombfeliratok (56.3).
- **BLOKKOLT:** a `LastUserESState` jelentése. **Mi kell hozzá:** a
  rövidítés feloldása egy célzott dekompilációval, vagy egy futó
  Picasa registry-ének összevetése. **Semmit nem blokkol** — csak ne
  találgassunk róla.
- **HATÓKÖRÖN KÍVÜL:** az öt webes szinkron-elem.

*(Záró mondat a 45.1 szerint: ebben a panelben **van** hiányzó vezérlő —
kettő; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A `headerpanel` webes szinkron-panel, tehát halott"** — megdőlt: a
  tíz elemből öt élő, köztük két valódi hiány (56.1).
- **„A fejléc gombjai statikus feliratúak"** — megdőlt: minden gombnak
  van `%d`-s, **számlálós** változata is (56.3).

## 57. tétel — a `compose_mail`: hatókörön kívül, DE két élő részlettel (2026-09-01)

*Huszadik kör az UI-lefedettségi axisról (#1778). Panel: `compose_mail`
(10 hiány) — a Picasa **saját levélszerkesztője**. A (d) szabály próbája:
mielőtt „megszűnt szolgáltatás" címén lezárnám, meg kell nézni, van-e
élő ága.*

### 57.1 A panel a GMAIL/Web Albums úthoz tartozik — bizonyítva

A kezelő (`0x00850030`) sztringjei nem hagynak kétséget:

| sztring | mit mond |
|---|---|
| `GMail` · `ChooseMail::GmailName` | a Gmail-ág neve |
| `ChooseMail::GPhotoName` · `ChooseMail::GPhotoShare` („Share Photos") | Google Fotók-megosztás |
| `Web Albums` · `CChooseEmailDialog::albumshare` („Ready to share an album") | Picasa Web Albums |
| `changeuser` („Change User") | Google-fiók váltása |

⇒ **A beépített levélszerkesztő a `choose_mail` (47. tétel) Gmail-ágának
a felülete.** A 47. körben rögzítettük, hogy az az ág halott; ez a panel
vele együtt **hatókörön kívül**.

*(Ez NEM ellentmond a 47. tétel figyelmeztetésének: ott azt mondtam ki,
hogy a **választó-párbeszédet** nem szabad halottnak nyilvánítani, mert a
másik ága él. A `compose_mail` viszont **kizárólag** a halott ághoz
tartozik — ezt most külön megmértem, nem feltételeztem.)*

### 57.2 ⭐ Két élő részlet, ami NEM a Gmail-ághoz kötődik

| bizonyíték | mit jelent | hova tartozik |
|---|---|---|
| **`Preferences\EmailAutocomplete`** | a **címzett-kiegészítés** kapcsolója | általános e-mail viselkedés → **#1798** |
| **„Preparing attachments…"** (`CChooseEmailDialog::infoprepare`) | folyamatjelző, amíg a **mellékletek átméretezése** tart | ua. |

⇒ Az eredeti **jelez, amíg a mellékleteket készíti** — nagy képeknél ez
másodpercekig tart, és a mi küldésünk (`sendRows`) ma **némán** dolgozik
alatta. Ez a két tétel a `choose_mail`-jegyre (#1798) megy, nem
veszik el a panel hatókörön kívülre tételével.

### Eredeti / nálunk / teendő

| | eredeti | nálunk (**mérve**) | teendő |
|---|---|---|---|
| beépített levélszerkesztő (Címzett/Tárgy/Szöveg/Küldés/Elvetés) | a Gmail-ághoz | nincs | **hatókörön kívül** |
| `changeuser`, `preview`, `discardimage` | ua. | nincs | ua. |
| **címzett-kiegészítés** | `Preferences\EmailAutocomplete` | nincs | → #1798 |
| **„mellékletek előkészítése" jelző** | folyamatjelző | **nincs** (néma) | → #1798 |

### Nyitott kérdések mérlege (57.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** hogy a panel a Gmail-ághoz tartozik (57.1, mérve, nem
  feltételezve); a két élő részlet kiemelése (57.2).
- **HATÓKÖRÖN KÍVÜL:** a beépített levélszerkesztő egésze.

*(Záró mondat a 45.1 szerint: ebben a panelben a hiányzó vezérlők
**hatókörön kívüliek**; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A `compose_mail` általános levélszerkesztő, tehát kellene"** —
  megdőlt: a kezelője a Gmail / Web Albums / Google Fotók sztringeket
  hivatkozza (57.1).
- **„Ha a panel halott, minden eleme halott"** — megdőlt: a
  címzett-kiegészítés és a melléklet-előkészítés jelzője **általános**
  viselkedés, és a #1798-ra tartozik (57.2).

## 58. tétel — a webkamera-panel: KÉT rögzítési mód, külön hang- és képforrás (2026-09-01)

*Huszonegyedik kör az UI-lefedettségi axisról (#1778). Panel:
`capturemoviepanelpopup` (11 hiány). A leltár egy mondata — „Webkamerás
videofelvétel" — kevesebbet mond, mint amit a kezelők adnak.*

### 58.1 KÉT rögzítési mód, nem egy

A `0x006274f0` kezelő névparancsai közt **két külön** rögzítés van:

| név | mit rögzít |
|---|---|
| `capture` (felirata **„Record"**) | **videoklip** |
| **`snapshot`** | **állókép** |

⇒ A panel nemcsak filmet vesz fel: **pillanatképet is készít**. A
leltár feliratai (`video_label` „Videoklip" · `live_video`
„Fényképezőgép") ezt visszaigazolják — a két címke **két módot** jelöl,
nem egy eszköz két nevét.

### 58.2 Külön KÉP- és HANGFORRÁS

`/videosrc` · `/audiosrc` (`0x006274f0`) + a `camchange` („Beállítások")
gomb, hozzá `settings_apply` / `settings_cancel`.

⇒ **A kamera és a mikrofon külön választható**, saját beállítás-lappal,
külön Alkalmaz/Mégse gombbal. A leltár `audio_label` („Hang") és
`size_label` („Méret") címkéi ehhez a laphoz tartoznak.

### 58.3 A felvett klip VISSZAJÁTSZHATÓ a panelen

`capturevbar/moviecontrols/play` · `moviecontrols/playicon` · `…/pause` ·
`moviecontrols/pauseicon` (`0x00626640`), mellettük `/next` · `/prev` és a
`/movieparent` konténer.

⇒ A rögzítés után **a panelen belül** meg lehet nézni a klipet, és
lépegetni lehet a felvételek közt — nem kell hozzá kilépni.

### 58.4 Tartós állapot

**`Preferences\capturemoviesize`** (mindkét kezelőben) — a választott
**felvételi méret** két indítás közt megmarad. *(Ugyanaz a `Preferences`
minta, mint a `PrintLastSize`, `datesort`, `LastCaptionButton`.)*

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| videofelvétel (`capture`, `pause`, `/stop`) | megvan | **nincs** | **#853** |
| **állókép** (`snapshot`) | megvan | nincs | ua. |
| külön kép- és hangforrás | `/videosrc`, `/audiosrc` | nincs | ua. |
| beállítás-lap Alkalmaz/Mégse gombbal | `camchange` + `settings_apply/cancel` | nincs | ua. |
| a klip visszajátszása a panelen | `capturevbar/moviecontrols/*` | nincs | ua. |
| a méret megjegyzése | `Preferences\capturemoviesize` | nincs | ua. |

*(A `webcambutton` a fő eszköztáron — „Capture photos or video from a
webcam or other video device" — ennek a panelnek a **belépési pontja**;
az 51. tételben már a #853-hoz soroltuk. Ez a kör a panel **tartalmát**
adja hozzá.)*

### Nyitott kérdések mérlege (58.)

```
Nyitott kérdések: 0 nyílt · 4 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a két rögzítési mód (58.1); a külön kép- és hangforrás
  (58.2); a panelen belüli visszajátszás (58.3); a tartós méret (58.4).

*(Záró mondat a 45.1 szerint: ebben a panelben **minden vezérlő
hiányzik** nálunk; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A panel csak videót vesz fel"** — megdőlt: a `snapshot` **állóképet**
  készít (58.1).
- **„A `video_label` és a `live_video` ugyanannak az eszköznek két neve"** —
  megdőlt: **két módot** jelölnek (58.1).

### 58.5 ⭐ MIT ÍR — a célmappa, a fájlnév és a sorszámozás (2026-09-02)

*Az 58.1–58.4 a panel VEZÉRLŐIT adta; azt nem, hogy a felvétel hova
kerül. Ez a szakasz azt méri ki. Minden cím a `Picasa3.exe` 3.9-é,
image base `0x00400000`.*

#### A célmappa — `<Képek>\Picasa\Rögzített videoklipek`

A `0x00627160` (906 b) **pontosan ugyanazt a hármas láncot** építi, mint a
filmkészítő `0x0061cf20`-a (`picasa-create-features.md` 2.6/c):

| # | lépés | cím |
|---|---|---|
| 1 | `0x009966a0` → a **`My Pictures`** gyökér | `0x00627176` |
| 2 | hozzáfűzve a **`Picasa`** közbülső szint (`0x00c7f0fc`) | `0x0062718d` |
| 3 | hozzáfűzve a **honosított** mappanév: kulcs `CCaptureMoviePanel::CaptureFolder`, angolul `Captured Videos`, magyarul **„Rögzített videoklipek"** (`0x00c9dc00` / `0x00c917f8`) | `0x006271bd`–`0x006271f3` |
| 4 | `0x00992ed0` (`Exists`); ha nincs, `0x009a3db0` létrehozza | `0x00627205`, `0x00627210` |

**A mappa `.picasa.ini`-t is kap.** A `0x00627271` a `0x00445a30`-at
hívja — ugyanazt, amelyik a `[Picasa] P2category=Projects (internal)`
sort írja (`biztonsagi-mentes.md`-ben és a filmnél is ez a függvény).
⚠️ **Csak létrehozáskor:** ha a mappa már létezik, a `0x00627205`
`Exists`-ellenőrzése **átugorja** a létrehozást ÉS az ini-írást is.

**ÉLŐ BIZONYÍTÉK a tulajdonos gyűjteményéből** (`ini-korpusz`): a
`/mnt/photo/Picasa/` alatt egyszerre áll a **`Captured Videos`** és a
**`Rögzített videoklipek`** mappa — pontosan a `project_folder_names.py`
(#1131) által kezelt nyelvi kettőzés.

#### Az állókép fájlneve — `snapshot.jpg`, ütközésnél `-001`

A `snapshot` ágat a `0x00628ec0` (1071 b) viszi:

| lépés | mit tesz | cím |
|---|---|---|
| 1 | a `[panel+0x2a0]` célmappa másolása | `0x0062902d` (`0x004089e0`) |
| 2 | hozzáfűzve a **`snapshot.jpg`** név (`0x00c9ddcc`) | `0x00629032`–`0x00629039` (`0x009a37b0` = PathAppend) |
| 3 | **egyediesítés**: `0x00993650` | `0x0062905f` |

⭐ **Az egyediesítő MÁS mintát használ, mint a kollázsé és a filmé:**

| funkció | minta | eredmény |
|---|---|---|
| kollázs · mozgófilm | `%s%lu` (`0x00993030`) | `nev1.jpg`, `nev2.jpg` |
| **webkamera-pillanatkép** | **`%s-%03lu`** (`0x00cd8d64`, `0x00993650`) | **`snapshot-001.jpg`**, `snapshot-002.jpg` |

A `0x00993650` a **kiterjesztést leválasztva** dolgozik (`0x009a3c70`,
`0x009a3b50`, majd `0x009a3620` teszi vissza), és a számlálót
**`0x1000` = 4096**-ig emeli (`0x00993a1a`); addig `0x00992ed0`
(`Exists`) a ciklusfeltétel.

⇒ **A sorszám kötőjeles és háromjegyű, nullákkal feltöltve.** Aki a
kollázs `output_path()`-át emeli át ide, **rossz nevet fog adni**.

#### A panel filmszalagja EZT a mappát mutatja

A panelépítő `0x00626640` maga hívja a `0x00627160`-at, és tőle kapja a
`capturemoviepanelpopup/filmstrip` tartalmát; a `/next` és a `/prev`
ezen a listán lépked (58.3).

#### A VIDEÓ-KÉPKOCKA ugyanide megy — és négy állapotszöveget ad

A `0x00591dd0` (927 b) a videóból mentett képkocka (`capture_frame`,
64. tétel) útja, és **ugyanazt a mappát** használja: kulcsa
`CCaptureFrame::CaptureFolder`, értéke szintén `Captured Videos` /
**„Rögzített videoklipek"**.

| kulcs | angol | **magyar** |
|---|---|---|
| `CCaptureFrame::captureframeprog1` | Capturing frame... | **„Képkocka rögzítése..."** |
| `CCaptureFrame::captureframeprog2` | Saving to Captured Videos | **„Mentés a Rögzített videoklipek albumba"** |
| `CCaptureFrame::captureframeprog3` | Saved %s to Captured Videos | **„A(z) %s mentve a Rögzített videoklipek albumba"** |
| `CCaptureFrame::captureframeprog4` | Failed to capture frame | **„Nem sikerült a képkocka rögzítése"** |

⇒ **Két külön funkció (webkamera + videó-képkocka) osztozik egy
mappán.** Aki bármelyiket megvalósítja, a másik helyét is eldönti.

**A képkocka-mentés négy állapota:** előbb „Capturing frame...",
aztán „Saving to Captured Videos"; sikerre a mentett fájl nevét mutatja,
hibára „Failed to capture frame" jelenik meg. A magyar alakok a fenti
`CCaptureFrame::captureframeprog1..4` táblában állnak.

**A képkocka-fájl NEVE is megvan** (`0x00591fa6`–`0x0059203c`):

| lépés | mit tesz | cím |
|---|---|---|
| 1 | a honosított mappanév hozzáfűzése | `0x00591fae` (`0x009a38a0`) |
| 2 | `Exists`; ha nincs → létrehozás **és** `.picasa.ini` (`0x00445a30`) | `0x00591fc5`, `0x00591fd5`, `0x00591ff0` |
| 3 | az **alapnév** hozzáfűzése — a `[obj+0x68]` mezőből | `0x0059200a` (`0x009a37b0`) |
| 4 | a kiterjesztés: **`.jpg`** (`0x00c80a50`) | `0x0059200f` (`0x009a3620`) |
| 5 | **ugyanaz a `%s-%03lu` egyediesítő**, mint a pillanatképnél | `0x0059203c` (`0x00993650`) |

⇒ A képkocka **JPEG**, ugyanabban a mappában, **ugyanazzal a kötőjeles
háromjegyű sorszámozással**. A mappa `.picasa.ini`-je itt is **csak
létrehozáskor** íródik.

**JPEG-minőség: 85.** A `0x00592033`-`0x00592067` út a `0x009d6010`
írófüggvényt hívja `{1, 4, 0x55}` beállításblokkal; a `0x00ad3b30` a
`0x55` értéket 85-ként erősíti meg. A `4` opció jelentése nincs megállapítva.

⚠️ **Ami nyitva marad:** hogy a `[obj+0x68]` alapnév pontosan mit
tartalmaz (a forrásvideó neve? időbélyeg?) — a mezőt a hívó tölti, és a
függvényben nincs rá literál. A `0x005952d0` `capture_frame` ága
(`0x0059578f`) a `[ebp+0x3098]` mezőt adja át a `0x00592170` konstruktornak;
az tárolja `[obj+0x68]`-on, amelyet a `0x00591dd0` felhasznál. **Megszerzés:**
célzott Ghidra-adatfolyam-vizsgálat a `0x005952d0`-ban. A meglévő
`2026-10-21-koteg-1021b.txt` csak a diszpécserből induló hívást sorolja, a
mező eredetét és jelentését nem mutatja. **A megvalósítást nem blokkolja:** a
mappa, a kiterjesztés és a sorszámozás megvan.


#### A panel állapotszövegei — a hivatalos magyar fordítással

| kulcs | **magyar** |
|---|---|
| `CCaptureMoviePanelPopup::title` | **„Rögzítés"** |
| `CCaptureMoviePanel::connecting` | **„Csatlakozás a kamerához"** |
| `CCaptureMoviePanel::connected` | **„Előnézet megjelenítése"** |
| `CCaptureMoviePanel::connecterr` | **„Sikertelen kapcsolódás"** |
| `CCaptureMoviePanel::unavail` | **„Nem érhető el"** |
| `CCaptureMoviePanel::live` | **„Élő videokép"** |
| `CCaptureMoviePanel::snap` | **„Pillanatkép"** |
| `CCaptureMoviePanel::size` | **„Méret: %s"** |
| `CCaptureMoviePanel::xxpixels` | **„%1$dx%2$d képpont"** |

Az állapotokat a `0x0062a720` (kapcsolódás, élő kép, pillanatkép,
`activitycapture/spinner`) és a `0x00629960` (elérhetetlenség, méret)
kezeli.

#### 58.6 A panel TELJES elemlistája — teljes névvel

*(A 58.1–58.4 a vezérlőket panel-előtag nélkül sorolta; a lefedettségi
mérő a teljes névre keres, ezért itt teljes alakban állnak. Kezelők:
`0x006274f0` (3690 b) és `0x00626640` (1095 b).)*

| elem | magyar felirat | mit tesz |
|---|---|---|
| `capturemoviepanelpopup/capture` | „Felvétel" | **videoklip** rögzítése |
| `capturemoviepanelpopup/live_video` | „Fényképezőgép" | az élő kép módja |
| `capturemoviepanelpopup/video_label` | „Videoklip" | a videó-mód címkéje |
| `capturemoviepanelpopup/audio_label` | „Hang" | a hangforrás címkéje |
| `capturemoviepanelpopup/size_label` | „Méret" | a felvételi méret címkéje |
| `capturemoviepanelpopup/camchange` | „Beállítások" | átvált a beállítás-lapra |
| `capturemoviepanelpopup/settings_apply` | „Alkalmaz" | a beállítás-lap véglegesítése |
| `capturemoviepanelpopup/settings_cancel` | „Mégse" | a beállítás-lap elvetése |
| `capturemoviepanelpopup/done` | „Kész" | a panel bezárása |
| `capturemoviepanelpopup/next` | — | a következő felvételre lép |
| `capturemoviepanelpopup/prev` | — | az előzőre lép |

Panel-szintű nevek ugyanitt: `capturemoviepanelpopup/basepanel`,
`capturemoviepanelpopup/settingspanel`,
`capturemoviepanelpopup/filmstrip`, valamint a névparancsok
`snapshot`, `pause`, `/stop`, `/videosrc`, `/audiosrc`, `/outputsize`,
`/activitycontainer`, `/capture_bgtext` (teljes néven
`capturemoviepanelpopup/capture_bgtext`), `/movieparent`.

#### Bizonyítottsági fok (58.5–58.6)

**Megerősített** (utasításszinten olvasva): a hármas mappalánc és a
honosított név, a `.picasa.ini` írása **csak létrehozáskor**, a
`snapshot.jpg` név, a `%s-%03lu` egyediesítő és a 4096-os korlát, a
kiterjesztés leválasztása, a filmszalag forrása, a képkocka-rögzítés
közös mappája, a kilenc állapotszöveg.

**Élő mintával megerősítve:** a `Captured Videos` és a
`Rögzített videoklipek` együttállása a tulajdonos gyűjteményében.

#### Nyitott kérdések mérlege (58.5–58.6)

`0 nyílt · 6 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| hova kerül a felvétel | **LEZÁRVA** — `<Képek>\Picasa\Rögzített videoklipek` |
| kap-e a mappa `.picasa.ini`-t | **LEZÁRVA** — igen, `P2category=Projects (internal)`, csak létrehozáskor |
| mi az állókép fájlneve | **LEZÁRVA** — `snapshot.jpg` |
| hogyan sorszámoz ütközésnél | **LEZÁRVA** — `%s-%03lu`, kötőjeles háromjegyű, max. 4096 |
| hova megy a videóból mentett képkocka | **LEZÁRVA** — **ugyanabba** a mappába |
| mi a képkocka kiterjesztése és sorszámozása | **LEZÁRVA** — `.jpg` + ugyanaz a `%s-%03lu` |
| **mit tartalmaz a képkocka ALAPNEVE (`[obj+0x68]`)** | **BLOKKOLT** — a mezőt a hívó tölti, literál nincs rá; az index `xrefs`-e a közvetett hívást nem tartalmazza. **Megszerzés:** a `0x00591dd0` hívójának dekompilációja. A megvalósítást nem blokkolja. |
| **a videoklip fájlneve és formátuma** | **HATÓKÖRÖN KÍVÜL** — a rögzítés DirectShow-eszközlánccal megy (`CTranscodeCaptureLoad`, `0x00626030`), ami Windows-specifikus; a **#853 döntése szerint** a webkamera-felvétel szándékosan kimarad. A célmappa és a képkocka-ág viszont ÉLŐ (a `capture_frame` a #452-höz tartozik). |

## 59. tétel — a keresősáv HÁROM hiányzó szűrője (2026-09-01)

*Huszonkettedik kör az UI-lefedettségi axisról (#1778). Panel:
`searchcontainer` (4 hiány) — a keresősáv és a szűrőgombjai.*

### 59.1 Az eredeti szűrő-készlet: hat gomb

*Forrás: `thumbui.tre:550` (`timeslider/scaleslider`).*

A `searchcontainer` kezelője hat szűrőt sorol fel egy helyen:

| gomb | buboréksúgó | nálunk (**mérve**) |
|---|---|---|
| `starsearch` | csillagozottak | **megvan** (a `MainToolbar.qml` ★ jele) |
| `geotagsearch` | geocímkézettek | **megvan** (`geoFilter`, `:135`) |
| **`facesearch`** | **„Show only photos with faces"** | **nincs** |
| **`moviesearch`** | **„Show movies only"** | **nincs** |
| `webview` | „Show uploads to web albums only" | **hatókörön kívül** |
| `timecontainer_label` + `timeslider/scaleslider` | **„Filter by date range"** | **nincs** |

⇒ **Három valódi hiány**, egy hatókörön kívüli, kettő megvan.

*(A `starsearch` és a `geotagsearch` felülbírálásai korábbi körből
származnak — nem ez a kör találta őket.)*
### 59.2 ⭐ A dátum-szűrő CSÚSZKA, nem dátumválasztó

*Forrás: `thumbui.tre:550` (`timeslider/scaleslider`).*

A `timecontainer_label` mellett a kezelő a
**`timeslider/scaleslider`**-t is hivatkozza — ugyanabban a
`…/scaleslider` alakban, mint a filmkészítő négy csúszkája (2.9).

⇒ A dátum-tartomány szűrése az eredetiben **csúszkával** történik, nem
két dátumválasztó mezővel. *(A felirat — „Filter by date range" — ezt
nem árulja el; ez megint a „a felirat nem a funkció" eset.)*

### 59.3 A keresés MÁSODIK vezérlőcsoportja: `searchoptions`

A `0x005d8810` egy külön, eddig nem dokumentált csoportot ad:

| elem | mit sejtet |
|---|---|
| **`dupesearch`** | másodpéldány-keresés — a **főablak-építőben** és a **fő parancskezelőben** is szerepel (`0x0040bf70`, `0x005cb990`), tehát menü-belépési pontja is van |
| **`similarthumb`** · `loadsim` · `clearsim` | **hasonlóság-keresés**: minta-bélyegkép betöltése és törlése |
| `digicam` | fényképezőgép szerinti szűrés |
| `viewallbutton` | „mindet mutasd" visszaállító |

⇒ A keresősáv mögött **egy második, gazdagabb szűrő-réteg** áll:
hasonló képek keresése mintakép alapján, másodpéldány-keresés és
gép szerinti szűrés.

⚠️ **Ez a szakasz JELZÉS, nem kész feltárás:** a `searchoptions` panel
**nincs benne** a mai UI-lefedettségi leltárban (a `.tre`-ből kinyert
2020 elem közt nem szerepel önálló panelként), tehát a mérés soha nem
fogja kiadni. A viselkedését egy külön kör tárja fel — a `dupesearch`
egyébként a **#1398** (másodpéldány-szűrés) témája.

### Eredeti / nálunk / teendő

*Forrás: `thumbui.tre:550` (`timeslider/scaleslider`).*

| | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| csillag- és geo-szűrő | megvan | **megvan** | — |
| **arcos képek szűrője** | `facesearch` | **nincs** | ÚJ JEGY |
| **csak filmek szűrője** | `moviesearch` | **nincs** | ua. |
| **dátum-tartomány (csúszka!)** | `timeslider/scaleslider` | **nincs** | ua. |
| webalbum-szűrő | `webview` | — | **hatókörön kívül** |
| `searchoptions` csoport | `similarthumb`/`loadsim`/`clearsim`, `dupesearch`, `digicam` (`0x005d8810`; vezérlő-xref: `0x005d8280`) | mintaképes hasonlóság és másodpéldány-keresés **megvan**; a gép szerinti szűrés ezen a körön kívül | hasonlóság: a #5660 összevetése a 60.4. szakaszban; másodpéldány: #1398; `digicam`: külön feltárandó |
### Nyitott kérdések mérlege (59.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a hatos szűrő-készlet és a mi oldalunk mérése (59.1); a
  dátum-szűrő csúszka volta (59.2).
- **BLOKKOLT:** a `searchoptions` csoport viselkedése (59.3). **Mi kell
  hozzá:** önálló kör, mert a panel nincs a leltárban, tehát a mérés nem
  vezet rá. **A jegyet nem blokkolja** — a három szűrő tőle függetlenül
  megvalósítható.
- **HATÓKÖRÖN KÍVÜL:** a `webview` szűrő.

*(Záró mondat a 45.1 szerint: **van** hiányzó vezérlő — három; a
csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A dátum-szűrő két dátumválasztó mező"** — megdőlt: a kezelő a
  `timeslider/scaleslider`-t hivatkozza, tehát **csúszka** (59.2).
- **„A keresősáv szűrői kimerülnek a hat gombbal"** — megdőlt: van egy
  második, gazdagabb `searchoptions` réteg (59.3).

## 60. tétel — a `searchoptions`: a keresés MÁSODIK rétege (2026-09-01)

*Huszonharmadik kör az UI-lefedettségi axisról (#1778). **Nem a
leltárból**: az 59.3 jelezte, hogy a `searchoptions` csoport a
`.tre`-leltárban nem szerepel önálló panelként, tehát a mérés soha nem
adja ki. A binárisból (`0x005d8810`, `0x005e60d0`).*

### 60.1 A `searchoptions` csoport deklarációi

| elem | mit csinál |
|---|---|
| **`similarthumb`** | a **minta-bélyegkép** — „keress ehhez hasonlót" |
| **`loadsim`** · **`clearsim`** | a minta **betöltése** és **törlése** |
| **`dupesearch`** | másodpéldány-keresés |
| `digicam` | **fényképezőgép** szerinti szűrés |
| `viewallbutton` | „mindet mutasd" visszaállító |

### 60.2 ⭐ A hasonlóság-keresésnek SAJÁT ADATBÁZISA van

| bizonyíték | mit jelent |
|---|---|
| **„Updating similarity database (will be fast next time)"** (`CSimSearch::updating`, `0x007ead60`) | van **hasonlósági adatbázis**, ami **első használatkor épül fel**, utána gyors |
| **„Similarity Search Results"** (`CAlbumState::SimSearchResults`, `0x004ad4e0`) | az eredmény **virtuális albumként** jelenik meg, saját néven |

⇒ **Nem szűrő, hanem külön keresési mód**: kiválasztasz egy mintaképet,
és a program megmutatja a hozzá hasonlókat egy **saját albumban**. Az
első futás lassú (indexépítés), és a program **meg is mondja**.

### 60.3 A `dupesearch` menü-belépési pontja

A `searchoptions/dupesearch` a **főablak-építőben** (`0x0040bf70`) és a
**fő parancskezelőben** (`0x005cb990`) is szerepel ⇒ nemcsak a
keresősávból érhető el, hanem **menüből** is. *(A menütétel az
`ID_DUPES` — a #1398 és a menü-leltár szerint nálunk „megvan".)*

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| másodpéldány-keresés | `dupesearch` (`0x0040bf70`, `0x005cb990`, `0x005d47e0`) | **megvan**: teljes motor (`dedup/`: `phash.py`, `similar.py`, sávos jelöltszűrés) + `DedupDialog.qml` | ezen a jegyen kívül |
| **hasonlóság-keresés mintaképpel** | `similarthumb`, `loadsim`, `clearsim`; aktív keresőút (`0x005d8810` → `0x007ea000`) | **megvan**: `SimilarityMixin`, egy kiválasztott képből indul; a dHash/Hamming-motor nem az eredeti rekordformátum | a részletes eltéréseket és nyitott kérdéseket lásd a 60.4. szakaszban |
| indexépítés jelzése | „Updating similarity database (will be fast next time)" (`0x007ead60`) | ugyanaz a felirat a QML-ben; csak hiányzó dHash esetén jelenik meg | **EGYEZIK a felirat**; az eredeti kiváltási feltétel külön ellenőrzendő |
| eredményfelirat | „Similarity Search Results" / `CAlbumState::SimSearchResults` (`0x004ad4e0`) | ugyanaz a felirat a hasonlósági eredménysávon; belső nézetmódunk különbözik | **EGYEZIK a felirat**; a keresőmag rangsora ismert (60.4.1), a tényleges találati tagság és végső sorrend teljes paritása nyitott |

⚠️ **A `dedup` és a mintaképes hasonlóság-keresés NEM ugyanaz.** A
duplikátum-csoportosítás azt kérdezi: *„mely képek duplikátumai egymásnak?"*;
a mintaképes keresés azt: *„mely képek hasonlítanak ERRE?"* A PicasaPy-ban
mindkettő megvan, de a #5660 összevetése külön algoritmust és adattárolást
igazol: az eredeti 380 bájtos rekordokat használ, a PicasaPy 64 bites
dHash-t és Hamming-távolságot. A #5736 feltárta az eredeti keresőmag rangját
és a `RankMax` vágását; a teljes viselkedési azonosság továbbra sincs
bizonyítva az eltérő előfeldolgozás és az utórendezés mezőjének nyitott
jelentése miatt.

### 60.4 #5660: a hasonlóság-keresés teljes útja és a PicasaPy-eltérések (2026-10-23)

**A vizsgált eredeti:** a helyi `Picasa3.exe` PE-verziója 3.9.141.259.
Az alábbi címek a bináris RVA-címei. A `searchoptions` erőforrás kivonata a
megadott `runtime/respack.yt` fájlból, memóriában készült; a bináris nem
került a repóba.

| Eredeti: cím vagy `NINCS MEG` | Nálunk | Teendő |
|---|---|---|
| **Keresés indítása:** `Ctrl+F7` → `searchoptions/loadsim`, parancsazonosító `0x15` (`0x005e62e8`); a kezelő `0x005d8810`, a keresőútban `0x007ea000` fut. | `Main.qml` `Ctrl+F7`-re a kijelölés első sorát adja a `showSimilarTo()`-nak. | **EGYEZIK** az indító billentyű és az egy mintaképes kérdés. A több kijelölt kép eredeti kezelése **NINCS MEG**; megszerzés: a `0x005d8810` célzott dekompilálása és a `0x005d8810`-hez tartozó kijelölési ág visszakövetése. |
| **Minta törlése:** `Ctrl+F8` → `searchoptions/clearsim`, parancsazonosító `0x16` (`0x005e631d`). | `Ctrl+F8` és látható „Clear Sample” gomb hívja a `clearSimilarity()`-t. | **EGYEZIK** a törlés művelete; nálunk a törlés gomb látható. |
| **Menübelépés:** a vizsgált menüleltárban és a `searchoptions` erőforrásban nem találtunk hasonlóság-kereső menüpontot. Ez nem bizonyítja a hiányát. **NINCS MEG**; megszerzés: a `0x005cb990` menüparancs-kezelő és a menüépítő teljes parancs-hozzárendelésének visszakövetése, valamint a menü-erőforrások cím szerinti ellenőrzése. | A `PicasaMenuBar.qml`-ben nem találtunk külön menüparancsot; a belépés a `Ctrl+F7`. | **Nyitott**; menühiányra nem nyitunk fejlesztési jegyet, amíg az eredeti parancs-hozzárendelés nincs lezárva. |
| **Keresősáv/párbeszéd:** `searchoptions/similarthumb` hivatkozásai `0x005d8280` és `0x005d8810`; a `tre:searchoptions` kivonatában a `similarrect`, `similarthumb`, `similarclip`, `loadsim` és `clearsim` sora komment. Külön modális hasonlóság-párbeszédet nem azonosítottunk. **NINCS MEG**, hogy van-e másik erőforrásból épített párbeszéd; megszerzés: az összes `.fen`/`.tre` erőforrás cím szerinti átnézése, majd a `0x005d8810` teljes vezérlőhívás-láncának célzott követése. | Nincs külön keresőpárbeszéd: a kijelölésből indul a keresés, a minta és a „Clear Sample” az eredménysávon látható. | A felület elhelyezése eltér. A kívánt termékviselkedést a paritásjegy határozza meg; a párbeszéd kérdése nyitott. |
| **Nincs minta őr:** a `0x005d8810` ág a `[edi+0xe64] == -1` értéknél kilép (`0x005d8b85`-`0x005d8b95`). | Nincs kijelölésnél a `keressHasonlot()` visszatér; kijelölésnél az első sort használja. | **EGYEZIK** a „kijelölés nélkül nincs keresés” viselkedés. Az eredeti többes kijelölésre vonatkozó szabály nyitott (lásd az első sort). |
| **Rejtett beállítás: eredményhatár:** a `Preferences\RankMax` értéket a `0x005d90c6` olvassa; hiányában a `0x005d90de` 1000-et ad át. A `0x005d90fa` a rendezett lista hosszát hasonlítja hozzá; ha nagyobb, a vektor méretét `RankMax`-ra állítja (`0x005d9136`-`0x005d9242`), tehát az aktuális sorrend **első N elemét** tartja meg. A végső rendezés kulcsát és a levágást a 60.4.1 bontja ki. | A `SimilarityMixin` nem olvas `RankMax`-ot, és nem alkalmaz találatszám-korlátot. | **ELTÉR:** az eredeti legfeljebb `RankMax` elemet ad vissza (alap 1000); a PicasaPy nem korlátoz. |
| **Rejtett beállítás: átméretezés:** `Preferences\ResampleFilter2`, alapérték 6 (`0x00a3f507`, `0x00a3f51c`); a hasonlóság-frissítési lánc hivatkozik az értékre. A 6-os mód Lanczos-4-ként szerepel a `filters-decoded.md`-ben. | A dHash a `cv2`-vel redukáltan dekódolt szürke képet 9×8-ra kicsinyíti `INTER_AREA`-val; nem olvassa ezt a Picasa-beállítást. | **ELTÉR** az előfeldolgozás és a kapcsolódó beállítás. Az egyezés céljához a Picasa előfeldolgozásának pontos átültetése szükséges. |
| **Hasonlósági adatbázis:** a fájlnév `distims.db` a `0x005d8bbe` címen jelenik meg; a tároló `CBlockFile`, a fix rekord 380 bájt (`0x007eb652`-`0x007eb661`; részletek a fenti #447 szakaszban). A teljes fájlút **NINCS MEG**; megszerzés: a `0x005d8810`-ből a fájlnév feloldásának követése és a `CBlockFile` megnyitási paramétereinek dekompilálása. | Az SQLite index `photo_hashes` táblája útvonal/mtime/méret kulcsú 64 bites dHash-t tárol. | **ELTÉR** a belső tárolási formátum. Ennek átültetése csak akkor indokolt, ha a termék célja a Picasa-találatokkal való viselkedési paritás. |
| **Összehasonlító jellemző és rangsor:** a `0x007e95f0` három rekordterületből képez távolságot: `[+0x002..+0x081]` RGB565 8×8 minta, `[+0x082..+0x159]` 216 bájtos vektor, `[+0x15c..+0x17b]` nyolc float (`0x007e9e60`-`0x007e9f8d`). A `0x007ea000` a három távolság külön növekvő rangját összegzi, majd az összeg szerint rendez; a magban **nincs távolságküszöb**. A `0x005d8810` a hasonlósági rangot és a minta-jelölt helyi időérték-eltérésének rangját kombinálja; a disassembly szerint az időrang kétszer kerül az akkumulátorba (`0x005d8fb5`-`0x005d9085`). A `0x0098b650` FILETIME-ból helyi SYSTEMTIME-ot képez, majd az `OLEAUT32.Ordinal_184`-et hívja; az ordinal neve/skálája **NINCS MEG**. A pontozóban nincs forrásazonosító szerinti önkizárás, de hogy a mintarekord benne van-e az adott adatbázisban, futásidejű adat nélkül **NINCS MEG**. Részletek és állításonkénti bizonyítottsági fok: 60.4.1. | A `SimilarityMixin` dHash-t számol és Hamming-távolságot használ; a saját `HASONLOSAG_KUSZOB = 14` értéke forráskódban rögzített saját döntés. A mintát is visszaadja (önmagától mért távolsága 0), a találatokat az index lekérdezési sorrendjében adja. | **ELTÉR:** az eredeti rekordmezőket és rangösszegeket, utórendezést és `RankMax`-ot használ; nálunk Hamming-küszöb és adatbázis-sorrend van. A 14 nem eredeti Picasa-érték. A helyi időérték pontos mértékegységének azonosítása további bizonyítékot igényel. |
| **Folyamatjelzés:** „Updating similarity database (will be fast next time)”, `CSimSearch::updating` (`0x007ead60`). | Ugyanez a felirat, a háttérszámítás állapotához kötve; csak hiányzó dHash esetén jelenik meg. | **EGYEZIK** a felirat. Az eredeti megjelenítési feltétel és az üres/adathibás képek hatása **NINCS MEG**; megszerzés: `0x007ead60` célzott dekompilálása és a frissítő visszahívásainak követése. |
| **Kimeneti név:** „Similarity Search Results” és `]sim` albumtoken (`0x004ad4e0`). | Az eredménysáv ugyanazt a „Similarity Search Results” feliratot mutatja; saját `similar` nézetmód. | **EGYEZIK** a látható név; a virtuális album tokenjének és a találati listának a teljes megfeleltetése **NINCS MEG**. Megszerzés: `0x004ad4e0` és a `0x005d8810`-ból eredő albumállapot dekompilálása. |

#### 60.4.1 #5736 - a keresőmag képlete, rangja és `RankMax` (2026-10-24)

**A rekordmezők és a képletek.** A `0x007e95f0` a 380 bájtos rekordban a `+0x002` címtől olvas 64 darab RGB565 szót, a `+0x082` címtől 216 bájtot, valamint a `+0x15c`-`+0x17b` tartomány nyolc floatját. Ha a rekord `+0xb0` bájtja nulla, mindhárom pontszámvektorba a `0x00cf5064` float sentinel (`99999997952.0`) kerül (`0x007e9e48`-`0x007e9e55`, `0x007e9f90`-`0x007e9f96`); a bájt szemantikai jelentése **NINCS MEG**, a jelöltet ez az ág nem távolítja el. A sentinel nem távolságküszöb.

| komponens | binárisból kiolvasott képlet | bizonyíték | bizonyítottsági fok |
|---|---|---|---|
| RGB565 | `D_rgb = (1/64) × Σ[p=0..63]((ΔR5)²+(ΔG6)²+(ΔB5)²)`; a szómezők 64, 16 bites RGB565 mintaszót tartalmaznak | `0x007e9f2b` hívja a `0x007ebaf0`-t; csatornakivonás `0x007ebb0f`-`0x007ebd5d`; `0x00cf3fc0` double = `1/64`; QEMU: vörös `15.015625`, zöld `62.015625`, kék `15.015625` | **megerősített** - utasításolvasás + eredeti kód QEMU-mérése |
| 216 bájtos leíró | `D_216 = (1/216) × Σ[i,j,k=0..5] w(i,j,k) × (Δv_ijk)²`, ahol `w=max(i,j,k)-min(i,j,k)+1` (1..6) | a `0x007ebf90`-`0x007ebfc7` a 6×6×6 súlytáblát a `0x00d6fb38`-`0x00d6fc0f` tartományba írja; a `0x0064df40` maxot, `0x006c1830` min-t ad; `0x00cf42f0` double = `1/216` | **feltételes** - statikus utasítás-/dekompilálás és konstans |
| nyolc float | `D_8 = Σ[k=0..7](q_k-r_k)²`; nincs négyzetgyök vagy normalizáló osztás | rekord `+0x15c,+0x160,+0x164,+0x168,+0x16c,+0x170,+0x174,+0x178`; kivonások `0x007e9e60`-`0x007e9eb5`, négyzetek/összeg `0x007e9ebb`-`0x007e9f27`; `0x00cf3a60` double = `0` | **feltételes** - statikus utasításolvasás és konstans |

**Rangsor és küszöb.** A `0x007ea000` mindhárom távolságvektorra külön meghívja a `0x00604480` rendezőt (`0x007ea31a`, `0x007ea35e`, `0x007ea3a2`), a jelöltenkénti három rangpozíciót összeadja (`0x007ea4a7`-`0x007ea579`), majd az összeg szerint növekvően rendez (`0x007ea596`). A `0x007ea000` teljes utasításszintű útjában nincs távolsághatárt vizsgáló eldobó ág; minden rekord pontozott vagy a fenti sentinel értéket kapja. **Fok: feltételes** (teljes célfüggvény statikus negatív vizsgálata; nincs teljes keresési futtatás).

**A kezelő végső rangja.** A `0x005d8810` a minta és minden jelölt `+0xf8` objektummezőjéből `0x004edf60`-nel FILETIME-ot állít elő, majd `0x0098b650`-nel konvertálja (`0x005d8ceb`-`0x005d8d0a`, jelöltek: `0x005d8eb3`-`0x005d8edb`). A `0x0098b650` nem nulla FILETIME esetén `FileTimeToSystemTime` → `SystemTimeToTzSpecificLocalTime` → `OLEAUT32.Ordinal_184` útvonalat hív; az ordinal neve és a double pontos időskálája **NINCS MEG**. A kezelő a minta-jelölt érték abszolút különbségét tárolja (`fsub`, `fabs`, `0x005d8edb`-`0x005d8eec`).

A nullázott rangakkumulátorhoz (`_memset`, `0x005d8f9d`) először egyszer hozzáadja a `0x007ea000`-ból kapott hasonlósági lista pozícióját (`0x005d8fb5`-`0x005d8fdc`), majd a `0x00604480`-nal a FILETIME-alapú abszolút eltérés szerint rendezett indexlista pozícióját **kétszer** hozzáadja (`0x005d8ffb`, `0x005d9010`-`0x005d903b`, `0x005d9043`-`0x005d906e`). A végső kulcs így `R = r_sim + 2 × r_time`, és a `0x005d9085` ezt növekvően rendezi. A `0x00604480` növekvő rendezését a QEMU-próba `[3,1,2] → [1,2,0]` eredménye is alátámasztja. **Fok: feltételes** - a súlyozott összetétel közvetlen disassemblyből következik, a teljes kezelőt nem futtattuk QEMU-ban. A helyi időátalakítás ténye megerősített a Ghidra-dekompilálás és a közvetlen hívási út egyezésével; az ordinal szemantikája nyitott.

**`RankMax`.** A `0x005d90c6` olvassa a `Preferences\RankMax` értéket; ha nincs beállítva, a `0x005d90de` 1000-et állít be. A `0x005d90fa` a végső rendezés (`0x005d9085`) után hasonlítja össze a találatszámot az értékkel; `count <= RankMax` esetén nincs vágás, `count > RankMax` esetén a `0x005d9136`-`0x005d9242` az elemszámot csökkenti, a már rendezett vektor első N elemét tartva meg. Ez maximális elemszám, nem távolságküszöb. **Fok: feltételes** - utasításszintű ág és Ghidra-kimenet egyezik, futásidejű `RankMax`-teszt nem készült.

**Mintakép.** A pontozó teljes bemenetén végigiterál, és a `0x007e95f0`/`0x007ea000` útban nincs forrásazonosító szerinti önkizárás; a `0x005d8810` pedig a kapott CBlockFile-adatbázist adja át a keresőnek (`0x005d8cbf`). Ha a forrás rekordja szerepel benne, érvényes (`+0xb0 != 0`) és friss jellemzőket tartalmaz, önmagához képest a három jellemzőtávolság nulla; az időeltérése is nulla. **A tényleges adatbázisbeli tagság NINCS MEG**: a mérőadat-csomagban nem volt futtatható `distims.db`-minta, ezért a saját rekord biztos találatként való visszaadása dinamikusan nem bizonyított. **Fok: feltételes** (statikus önkizárás-hiány + feltételes rekordtagság).

**Független utak és fok.** (A) a bináris közvetlen utasításolvasása, Ghidra-dekompilálása és PE-konstansai; (B) az eredeti célfüggvények QEMU-mérése. Az RGB565-képlet és a `0x00604480` növekvő iránya **megerősített**. A 216 bájtos és nyolc float képlete, a háromrang-összeg, a távolságküszöb hiánya, a kezelő `r_sim + 2 × r_time` súlyozása, a `RankMax` levágása, valamint a mintarekord adatbázisbeli jelenléte nem kapott teljesen független, a teljes úton végzett mérési kontrollt; ezek **feltételesek**, illetve a tagság **nyitott**. A 216 bájtos helper közvetlen QEMU-próbája SIGSEGV-vel végződött; az abból származó számértéket nem használom bizonyítékként.

**Cáfoló kísérlet.** A rendezőnél a csökkenő sorrend hipotézisét próbáltam cáfoló bemenettel: `[3,1,2]` csökkenő eredménye `[0,2,1]` volna, a QEMU-mérés viszont `[1,2,0]` lett, tehát a csökkenő hipotézis megbukott. A vörös/zöld/kék egyetlen-bites próbák a másik irányból is ellenőrizték a RGB-képlet `/64` skáláját. A `r_sim + 2 × r_time` teljes kezelőkulcsra nem készült QEMU-teszt; ezt a két egymás utáni, azonos akkumulátorba író disassembly-hurok alapján **feltételesnek** hagyom.

**Bizonyítottsági fok: vegyes.** A RGB565-képlet és a rendező növekvő iránya **megerősített** (utasításolvasás + QEMU); a többi algoritmikus állítás **feltételes** (utasításolvasás/Ghidra és konstansok, teljes futási kontroll nélkül); a mintarekord tényleges adatbázisbeli tagsága és az `Ordinal_184` export/számérték jelentése **nyitott**. Teljes keresési futtatást nem állítok.

#### Fejlesztési jegyjavaslat a #5736 által igazolt eltérésekre

A #5736 a keresőmag képletét, rangösszegét és a `RankMax` vágását
utasításszinten feltárta, az RGB565-képletet és a rendezési irányt QEMU-val is
mérte. Ez már bizonyítja a dHash/Hamming-megvalósítástól való szerkezeti
eltérést. Az `OLEAUT32.Ordinal_184` pontos exportja/skálája, a rekordfrissítés
paritása és a mintarekord adatbázisbeli jelenléte még nyitott; a fejlesztési
jegy a megállapítható algoritmikus eltéréseket rögzíti, a hiányzó részekhez
pedig mérést kér.

**Cím:** A mintaképes hasonlóság-keresés Picasa 3.9-paritása

**Eredeti:** A Picasa 3.9.141.259 `distims.db` adatbázist és 380 bájtos
rekordot használ (`0x005d8bbe`, `0x007eb652`). Három jellemző külön rangját
összegzi; a kezelő végső kulcsa `r_sim + 2 × r_time`, ahol `r_time` a minta és
a jelölt FILETIME-alapú abszolút időérték-eltérésének rangja. A
`Preferences\RankMax` a végső rendezés prefixét korlátozza (60.4.1).

**Nálunk:** A mintaképes keresés dHash/Hamming-alapú, saját 14 bites
küszöbbel; nincs `RankMax` találatkorlát és nem használja az eredeti
`ResampleFilter2` beállítást.

**Teendő:** Paritáscél esetén cseréld le a dHash/Hamming-küszöböt az eredeti
három jellemző rangösszegére, majd alkalmazd a mért `r_sim + 2 × r_time`
végső rangot és a `RankMax` prefixkorlátot. Az időskálát és a forrásrekord
tagságát kontrollált Picasa-futásban mérd meg, mielőtt a mezőt és a saját
mintatalálatot specifikálod. A látható „Clear Sample” gomb maradjon külön,
tudatos termékdöntés.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `tre:searchoptions` minta- és törlővezérlői kommenteltek, miközben a `Ctrl+F7`/`Ctrl+F8` parancs aktív (`0x005e62e8`, `0x005e631d`). | A gyorsbillentyűk mellett látható „Clear Sample” gomb van az eredménysávon. | A gomb legyen dokumentált, tudatos felületi többlet; a paritásmódosítás ne tüntesse el véletlenül. |
| 380 bájtos rekord: RGB565, 216 bájtos leíró, nyolc float (`0x007e95f0`); három komponensrang összege (`0x007ea000`); a kezelő végső rangja `r_sim + 2 × r_time`, utána `RankMax` prefixvágás (`0x005d8810`). | `photo_hashes.dhash`, 64 bit, Hamming-küszöb 14; nincs `RankMax`. | Paritáscél esetén az eredeti rangsort és korlátot bevezetni; az időkulcs exact skáláját azonosítani az `OLEAUT32.Ordinal_184` export helyi feloldásával vagy kontrollált runtime-méréssel, majd rögzített képkészleten összevetni. |
| `Preferences\ResampleFilter2`, alapérték 6 (`0x00a3f507`, `0x00a3f51c`) | saját redukált dekódolás és `INTER_AREA`; a beállítást nem használja | A Picasa előfeldolgozásával való összehasonlítás alapján paritás esetén átvenni a módot és alapértéket. |
| `Preferences\RankMax`, alapérték 1000; a rendezett vektor első N elemét tartja meg (`0x005d90fa`, `0x005d9136`-`0x005d9242`). | nincs ilyen beállítás vagy eredménykorlát | Bevezetni a beállítást és azonos prefixkorlátot. |

**Kész, ha:**

- a `0x007e95f0`, `0x007ea000` és `0x005d8810` mért lelete dokumentált, és
  az `OLEAUT32.Ordinal_184` export neve/skálája ismert vagy kontrollált
  mérésből rögzített;
- a PicasaPy ugyanazon rögzített képkészleten azonos mintaképet, találati
  tagságot, sorrendet és találatszámot ad, vagy a termékdöntés név szerint
  rögzíti az elfogadott eltéréseket;
- a `ResampleFilter2` alapértéke és hatása egyezik a dokumentált eredeti
  viselkedéssel, vagy a tudatos eltérés felhasználói dokumentációba kerül;
- egy rögzített rang-fixture igazolja a `r_sim + 2 × r_time` sorrendet; például
  `A=(r_sim 0, r_time 2) → 4`, `B=(r_sim 3, r_time 0) → 3`, ezért B álljon
  A elé (szintetikus rangteszt, nem Picasa-mérés);
- `RankMax=2` és három, előre rendezett tesztjelölt esetén pontosan a sorrend
  első két eleme maradjon meg, távolságküszöb szerinti eldobás nélkül;
- a mintarekord szereplését kontrollált eredeti futás eredményével egyeztesd,
  mert a binárisból az önkizáró ág hiánya, nem az adatbázisbeli tagság bizonyult;
- a meglévő `Ctrl+F7`, `Ctrl+F8`, eredményfelirat és üres kijelölés viselkedés
  nem romlik, és a látható „Clear Sample” többletvezérlő tudatosan megmarad
  vagy egy termékdöntés dokumentálja a változtatását.

#### Bizonyítottság, cáfoló kör és fennmaradó kérdések

**Bizonyítottsági fok: feltételes.** A 60.4.1 a keresőmag képletét, rangsorát
és `RankMax`-ját külön tárgyalja. Két külön út megerősíti, hogy a
hasonlóság-keresés nem pusztán kikommentezett rajz: (A) az utasításszintű
útvonal az aktív `Ctrl+F7` ágat a `0x005d8810` kezelőhöz, onnan a
`0x007ea000` keresőhöz vezeti; (B) az indexelt string-xref-ek külön a
`searchoptions/similarthumb` vezérlőhivatkozásait és a
`CAlbumState::SimSearchResults` kimeneti függvényt (`0x004ad4e0`) azonosítják,
amelyet a keresőkezelő hív. A pontos erőforrás-kivonat megerősíti, hogy a
felületi sorok közben ki vannak kommentezve. A PicasaPy-oldali billentyű,
minta, küszöb és eredménysáv külön ellenőrizhető a QML/Python-forrásban. A
keresőmag és a korlát statikus útja a 60.4.1-ben áll. Az
`OLEAUT32.Ordinal_184` export/skálája, a többes kijelölés és a frissítés
feltételei még nyitottak; a mintarekord adatbázisbeli jelenléte futásidejű
kérdés.

**Cáfoló kísérlet:** a „kommentelt vezérlők ⇒ a funkció nem létezik” állítást
az aktív `Ctrl+F7`-ág és a `0x005d8810` → `0x007ea000` → `0x004ad4e0`
keresési/eredménylánc cáfolja. A cáfoló saját kontrollja: a tényleges
`tre:searchoptions` kivonat igazolja, hogy a felületi vezérlők valóban
kommenteltek. Így a pontosított állítás az, hogy **a vezérlők rejtettek, a
bináris funkció pedig parancsúton aktív**.

**Nyitott:**

- `Ghidra-kör kell: 0x007ead60 - a meglévő dekompilálás a 380 bájtos rekord blokkos írását mutatja, de nem nevezi meg, melyik előkészítő ág állítja a pontozó által vizsgált rekord+0xb0 bájtot, és mit jelöl ez az állapot.`
- **NINCS MEG:** az `OLEAUT32.Ordinal_184` export pontos neve és a `0x0098b650` visszatérési double időskálája. Megszerzés: a Picasa által használt OLEAUT32 ordinal-táblája vagy ismert FILETIME-okra végzett kontrollált runtime-mérés.
- **NINCS MEG:** hogy a kiválasztott forrásrekord az adott futásban szerepel-e a `distims.db` jelöltvektorában. Megszerzés: eredeti programmal, előtte-utána mentett `distims.db`-vel vagy azonos adatokkal feltöltött QEMU-harnessben végzett, mintaképre visszakereső próba.
- `Ghidra-kör kell: 0x005d8810 - a több kijelölés kezelése és a külön párbeszéd/panel megnyitásának útja. Ez kívül esik a #5736 hatókörén.`
- `Ghidra-kör kell: 0x007ead60 - pontosan mikor indul és milyen feltételekkel áll le az adatbázis-frissítés/felirat. [blokkoló]`
- A külön menüparancs vagy modális párbeszéd megléte nincs lezárva; a megszerzési út a fenti táblázatban áll.

### Nyitott kérdések mérlege (60.)

```
Nyitott kérdések: 2 nyílt · 4 lezárva · 3 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a `searchoptions`-ban deklarált elemek és a kikommentezett
  vezérlők elkülönítése (60.1, #5660); a `distims.db`-hez tartozó
  380-bájtos rekord és a `Similarity Search Results` kimeneti név (60.2,
  #447/#5660); a `dupesearch` második belépési pontja (60.3); a keresőmag
  képlete, rangösszege, távolságküszöb-hiánya és a `RankMax` prefixvágása
  (60.4.1, #5736).
- **NYÍLT:** van-e külön menübelépés (a #5660 táblázata megadja a megszerzés
  útját), és mit jelöl a rekord `+0xb0` bájtja (`0x007e95f0`).
- **BLOKKOLT:** az `OLEAUT32.Ordinal_184` export/skála feloldása, a mintarekord
  tényleges adatbázisbeli tagsága, a többes kijelölési és felületnyitási ág,
  valamint a frissítés pontos feltételei. **Mi kell hozzá:** helyi ordinal-tábla
  vagy kontrollált időmérés; eredeti futásban mentett `distims.db` vagy
  megfelelő QEMU-adat; a többi kérdés célzott bináris-út. A keresőképletek,
  rangösszegek és `RankMax`-vágás a 60.4.1-ben állnak.

*(Záró mondat a 45.1 szerint: ez a csoport a leltárban nem szerepel,
ezért „hiányzó vezérlő" mérőszáma sincs — a hiányt a fenti tábla mondja
meg.)*

### Amit KIZÁRTAM

- **„A `dupesearch` és a hasonlóság-keresés ugyanaz"** — megdőlt: két
  külön vezérlő, más felhasználói kérdéssel; a hasonlóságnak **saját
  adatbázisa és eredmény-albuma** van (60.2).
- **„A `searchoptions` a keresősáv része"** — megdőlt: külön csoport,
  ami a `.tre`-leltárban nem is szerepel (59.3, 60. bevezető).

## 61. tétel — a „rejtett vezérlőcsoportok" keresése: NEGATÍV eredmény, egy kivétellel (2026-09-01)

*Huszonnegyedik kör az UI-lefedettségi axisról (#1778). A 60. tétel
tanulsága volt, hogy a `searchoptions` csoport a `.tre`-leltárban nem
szerepel, tehát a mérés nem adja ki. Kézenfekvő kérdés: **hány ilyen
csoport van még?** Ez a kör azt méri meg — és a válasz **jó hír**.*

### 61.1 A módszer

Gépi összevetés: minden `panel/vezérlő` alakú sztring a binárisból,
kiszűrve a `.tre`-leltár (2020 elem / 74 panel) panelnevei. Ami marad:
olyan csoport, amit a mérés **szerkezetileg nem lát**.

### 61.2 Az eredmény: tíz csoport, és szinte mind RAJZOLÓ erőforrás

| csoport | vezérlőnév | mi ez valójában |
|---|---:|---|
| `icons` | 49 | **ikon-atlasz** |
| `globalbuttons` | 15 | **gomb-grafikák** (ld. 61.3) |
| `adorners` · `overlays` | 12 · 12 | rárajzolt díszítések, fedvények |
| `notifier` | 10 | a lebegő értesítősáv — **már feltárva** (`picasa-lebego-ertesito.md`) |
| `scrollart` · `arrows` · `progbase` | 7 · 5 · 3 | görgetősáv-, nyíl- és folyamatjelző-grafika |
| `text` · `action` | 3 · 3 | általános névterek |

⇒ **A `searchoptions` kivétel volt, nem szabály.** A leltárból hiányzó
csoportok nagy része **grafikai erőforrás**, nem funkció — és az egyetlen
valódi funkciós csoport (`notifier`) **már fel van tárva** egy korábbi
körben.

**Ez negatív eredmény, és mint ilyen, eredmény:** a következő köröknek
**nem érdemes** ezt a keresést megismételni. *(A skill szabálya szerint
az elvetett irányt ugyanúgy le kell írni, mint a megtaláltat — enélkül
egy következő kör újra végigjárja.)*

### 61.3 ⭐ Melléklelet: a gombok HÁROM állapotúak

A `globalbuttons` nevei **hármas készletekben** állnak:

```
globalbuttons/small_ok_n · small_ok_h · small_ok_p
globalbuttons/small_cn_n · small_cn_h · small_cn_p
globalbuttons/mk_root_n  · mk_root_h  · mk_root_p
globalbuttons/square_close_n · _h · _p
globalbuttons/ob1_decrect_n · _h · _p
```

⇒ **`_n` = normál · `_h` = rámutatott (hover) · `_p` = lenyomott.** A
binárisban **1252** ilyen végződésű erőforrásnév van — vagyis ez a
Picasa **általános gombkonvenciója**, nem néhány gombé.

**Miért érdekes nekünk:** a mi gombjaink Qt-stílusból veszik az
állapotokat. Ahol az eredeti kinézetét pontosan követjük (a
`docs/decisions/szerkeszto-bal-panel.md` szerint ez az alapértelmezés),
ott **három** állapotot kell megadni, nem kettőt — a rámutatás külön
grafikát kapott, nem csak világosítást.

*(A `globalbuttons/#chip_*` nevek — `chip_public`,
`chip_extended_network`, `chip_x_blue`, `chip_x_green` — a webalbum-
megosztás láthatóság-jelzői: **hatókörön kívül**.)*

### Nyitott kérdések mérlege (61.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** hány rejtett vezérlőcsoport van (61.2 — gyakorlatilag
  nincs több); a gombok háromállapotú konvenciója (61.3).
- **HATÓKÖRÖN KÍVÜL:** a `#chip_*` megosztás-jelzők.

*(Záró mondat a 45.1 szerint: ez a kör nem panelt vizsgált, hanem a
mérés vakfoltját — „hiányzó vezérlő" mérőszáma nincs.)*

### Amit KIZÁRTAM

- **„A `searchoptions`-hoz hasonló rejtett funkciós csoportok tömegével
  vannak"** — megdőlt: tíz csoportból kilenc grafikai erőforrás vagy
  általános névtér, a tizedik (`notifier`) már feltárva (61.2).

## 62. tétel — a névtelen és mellőzött arcok fejléce: két téves riasztás, egy elhelyezés-eltérés (2026-09-01)

*Huszonötödik kör az UI-lefedettségi axisról (#1778). Két kis panel egy
jelenségként: `unknownfaceheaderpanel` (3) és `peoplepanel` (3) — a
**névtelen és mellőzött arcok** munkafolyamata.*

### 62.1 Két elem megvan nálunk

| eredeti | nálunk (**mérve**) |
|---|---|
| `ignore` („Kijelöltek mellőzése") | `ignoreFacesButton` (`UnnamedFacesView.qml:117`), buboréksúgóval; **párja** az `unignoreFacesButton` („Stop ignoring", `:109`) |
| `manual_add` („Személy kézi hozzáadása") | `addNameButton` („Add a name", `:128`) |

*(A `manual_add::instructions` négylépéses gesztus-utasítását egy
**korábbi** kör már rögzítette — a `FacesOverlay.qml:283` név szerint
hivatkozza. Nem ez a kör találta.)*

### 62.2 Elhelyezés-eltérés: fejléc-gomb helyett ALBUM

`showignored` („Mellőzött arcok megjelenítése") és `showunknown`
(„Vissza ide: Név nélküliek") az eredetiben **fejléc-gombok**: a
névtelen és a mellőzött nézet közt váltanak.

Nálunk ugyanez **két albumon** át megy: a bal hasáb „Névtelenek" és
„Mellőzött emberek" gyűjteménye (`FolderPane.qml:50–59`,
`ignoredFacesActive`), az `UnnamedFacesView` pedig a
`window.facesAlbumMode` szerint vált (`Main.qml:1644`).

⇒ **Funkcionálisan egyenértékű, elhelyezésben eltér.** A 45.3
eltérés-táblába való, nem jegybe.

*(A `UnnamedFacesView.qml:20–21` docstringje ezt már ki is mondja: „az
eredetiben ez két ALBUM volt" — vagyis a döntés tudatos volt, csak az
eltérés-tábla még nem létezett, amikor megszületett.)*

### 62.3 A `peoplepanel` maradék eleme

`status_label` — „Select a folder to display faces". Nálunk a
`PeoplePanel.qml` a kijelöléshez igazodó feliratokat használ („In this
photo:", „People in these photos:"), üres állapotra saját szöveggel.
**Nem hiány**, hanem más állapotkezelés; a mérés a szó szerinti egyezést
kereste.

### Eredeti / nálunk / teendő

| | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| kijelöltek mellőzése | `ignore` | **megvan** (+ a visszavonás párja) | — |
| személy kézi hozzáadása | `manual_add` | **megvan** | — |
| váltás névtelen ↔ mellőzött | **fejléc-gomb** | **album** a bal hasábon | tudatos eltérés → 45.3 |
| üres állapot felirata | `status_label` | saját szövegek | — |

### Nyitott kérdések mérlege (62.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a két téves riasztás (62.1); az elhelyezés-eltérés
  besorolása (62.2); a `status_label` kérdése (62.3).

*(Záró mondat a 45.1 szerint: ebben a két panelben **nincs hiányzó
vezérlő**; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A névtelen/mellőzött váltás hiányzik nálunk"** — megdőlt: albumon
  át megvan, tudatos eltéréssel (62.2).

## 63. tétel — a címke-panel és a geocímke-párbeszéd: négy téves riasztás (2026-09-01)

*Huszonhatodik kör az UI-lefedettségi axisról (#1778). Két kis panel:
`tagpanel` (3) és `gedialog` (2).*

### 63.1 A címke-panel nálunk teljes

| eredeti | nálunk (**mérve**) |
|---|---|
| `add_tag_label` („Írjon be egy hozzáadandó címkét:") | `tagInput` + „Add a tag…" helyőrző (`TagsPanel.qml:87`, `:91`) |
| `addtag` („Add tag to the currently selected items") | `tagAddButton` (`:97`) |
| `quick_config` („Configure Quick Tags") | `quickTagsGearButton` (`:201`) — a `QuickTagsConfigDialog`-ot nyitja |

Mellettük **nálunk van többlet is**: címke-lista eltávolító gombokkal
(`tagList`, `tagRemove-<címke>`, `:117`, `:151`), gyorscímke-rács
(`quickTagsGrid`, `:219`), és üres kijelölésre saját szöveg („Select
pictures to tag them.", `:108`).

### 63.2 A geocímke-párbeszéd: a `tagall` MEGVAN, más alakban

Az eredeti `gedialog` a **Google Earth**-integráció párbeszéde
(filmszalaggal, `next`/`prev` lapozással). A Google Earth asztali
integráció **megszűnt** — a `docs/specs/` ezt korábbi körből már
rögzítette.

**A `tagall` („Az összes geocímkézése") viszont NEM a Google Earth-höz
kötődik**, hanem magához a geocímkézéshez: egy hely a **teljes
kijelölésre**.

Nálunk mérve: a `PlacesPanel.qml:109` a
`controller.setGeotagRows(appWindow.selectedIndexes, latitude,
longitude)`-t hívja — vagyis **egy koordináta az egész kijelölésre**.
Ugyanaz a művelet, más felületen (térkép-panel a párbeszéd helyett).

⇒ **Téves riasztás**, felülbírálva. *(Ez a (d) szabály ötödik esete: a
párbeszéd halott, a benne lévő művelet nem.)*

### 63.3 A maradék `gedialog`-elemek

**`gedialog/done`** (`gedialog.tre:50`) · **`gedialog/next`** ·
**`gedialog/prev`** · **`gedialog/filmstrip`** — a Google Earth-párbeszéd
saját navigációja. **Hatókörön kívül** a párbeszéddel együtt; a mi
térkép-panelünk a kijelölésen dolgozik, nem képenként lapozva.

> ⭐ **2026-09-06 (#2529): a `done` kezelője kimérve, hogy a besorolás ne
> feltevés legyen.** Mind a négy elem a párbeszéd parancs-elosztójában ül
> (**`0x00853990`**, 694 b); a `done` saját kezelője a **`0x00854080`**
> (94 b): előbb egy időzítő-kapun megy át (`GetTickCount` vs. `[this+0x264]`,
> `0x00854095`), majd a `0x00853f90`-t hívja, végül — ha a `0x006ff6d0`
> igazat ad — **magát a `gedialog/done` elemet aktiválja** (`0x009cd8a0`,
> `0x008540bd`). ⇒ a párbeszéd lezárása, adatot nem ír. A besorolás
> (hatókörön kívül) változatlan, de most mérésen nyugszik.

### Eredeti / nálunk / teendő

| | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| címke beírása + hozzáadás | `add_tag_label`, `addtag` | **megvan** | — |
| gyorscímkék beállítása | `quick_config` | **megvan** | — |
| az összes geocímkézése | `tagall` | **megvan** (`setGeotagRows` a kijelölésre) | — |
| Google Earth-párbeszéd navigációja | `done`/`next`/`prev`/`filmstrip` | — | **hatókörön kívül** |

### Nyitott kérdések mérlege (63.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a címke-panel teljessége (63.1); a `tagall` megléte más
  alakban (63.2).
- **HATÓKÖRÖN KÍVÜL:** a Google Earth-párbeszéd navigációja (63.3).

*(Záró mondat a 45.1 szerint: ebben a két panelben **nincs hiányzó
vezérlő**; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A `gedialog` egésze halott, mert a Google Earth-integráció az"** —
  megdőlt: a `tagall` művelete él, és nálunk meg is van (63.2).

## 64. tétel — a VIDEÓ-SZERKESZTŐ: vágás be-/kimeneti ponttal, és képkocka-mentés (2026-09-01)

*Huszonhetedik kör az UI-lefedettségi axisról (#1778). Panel:
`video_control_bar` (3) — és a mögötte álló `movieeditpanel`.*

### 64.1 ⭐ A videó VÁGHATÓ — be- és kimeneti ponttal

| elem | buboréksúgó |
|---|---|
| **`video_control_bar/setin`** | **„Create a new starting point"** |
| **`video_control_bar/setout`** | **„Create a new ending point"** |
| `video_control_bar/trimslider` | a vágás-csúszka |
| `video_control_bar/moviemode1` | „Play full screen" |

A kezelő (`0x005952d0`) a **`moviestart`** és **`movieend`** neveket
hivatkozza ⇒ **a vágáspontok a `.picasa.ini` `filters=` láncába
kerülnek**, ugyanoda, ahová a képszerkesztés tokenjei.

### 64.2 A `movieeditpanel` további három művelete

Ugyanaz a kezelő (`0x005952d0`):

| elem | mit csinál |
|---|---|
| **`movieeditpanel/reset_trim`** | a vágás **visszaállítása** |
| **`movieeditpanel/capture_frame`** | ⭐ **állókép mentése a videóból** |
| `movieeditpanel/export_movie` · `movieeditpanel/export_youtube` | export (a YouTube-ág **hatókörön kívül**) |

⇒ A videó nem csak lejátszható: **vágható**, és **képkocka menthető
belőle**.

### 64.3 Nálunk: a 2026-09-01-i hiányállapot azóta megváltozott (#1838)

A fenti 2026-09-01-i mérés a funkció beépítése előtti állapotot rögzíti.
A mai kódban a vágás, annak visszaállítása és a képkocka mentése is elérhető.
A teljes képkocka-mentési út és a binárissal való összevetés a **64.5**
szakaszban áll.

| művelet | nálunk, a jelenlegi kódban | bizonyíték |
|---|---|---|
| `setin` / `setout` / `trimslider` | megvan; a kiválasztott időpontokat a vezérlő `moviestart` / `movieend` tokenként írja | `app/movie_trim_controller.py`; `app/qml/PicasaPy/VideoPlayerView.qml`; `app/qml/PicasaPy/PhotoViewer.qml` |
| `reset_trim` | megvan | `app/movie_trim_controller.py`; `app/qml/PicasaPy/VideoEditPanel.qml` |
| `capture_frame` | megvan; a videó jelenlegi lejátszási pozíciójából ment képkockát | `app/frame_capture_controller.py`; `movie/frame_capture.py`; `app/qml/PicasaPy/VideoEditPanel.qml` |
| a `moviestart` / `movieend` round-trip | a tokenek megmaradnak, és a vezérlő írni is tudja őket | `ini/movie_trim.py`; `ini/filter_registry.py`; `app/movie_trim_controller.py` |
| YouTube-export | nincs | a megvalósítás hatóköre továbbra is a #432 / #2529 alatt áll |

### 64.4 A maradék kis panelek

*Forrás a `panelroot` sorához: `panelroot.tre` — pl. a
`panelroot/makemovietab` a `panelroot.tre:75`, a
`panelroot/capturemovietab` a `panelroot.tre:91`, a `panelroot/globaltabs`
a `panelroot.tre:95` sorban áll.*

| panel | elem | állapot |
|---|---|---|
| `rightdrawerpanel` | `rightdrawerpanel/close` · `rightdrawerpanel/size_toggle` („Switch between small/large side panel", `rightdrawerpanel.tre:21`) · `rightdrawerpanel/title_text` („Metaadatok", `rightdrawerpanel.tre:8`) | a fiók **méret-váltója** nálunk nincs — kis eltérés, a #1773-hoz tartozik |
| `panelroot` | `panelroot/makemovietab` („Movie Maker") · `panelroot/capturemovietab` („Rögzítés") · `panelroot/globaltabs` · `panelroot/youtab` | a **felső lapok**; a filmkészítő és a rögzítés a #432 / #853 alatt |
| `instructionpanel` | `instructionpanel/close` · **`instructionpanel/learn_more`** („Learn more…" / „További információ…", `instructionpanel.tre:29`) | ⭐ **2026-09-06 (#2529): a cél KIMÉRVE** — a kezelő a `0x0074c760`, és a `http://picasa.google.com/support/bin/answer.py?hl=%s&answer=156272` címet nyitja meg (`%s` = a nyelv kódja). A Picasa súgószolgáltatása megszűnt ⇒ **hatókörön kívül**. A kezelő a **puszta** nevet hasonlítja, ezért a minősített névre keresés nem találja. |
| `video_control_bar2` | `1to1` („Show actual movie size (don't stretch)") · `fullscreen` · `scaleslider` · `volumeslider` | a **2.7** szakaszban már feltárva — nem ez a kör találta |

### Eredeti / nálunk / teendő

| | eredeti | nálunk (**mérve**) | teendő |
|---|---|---|---|
| videó **vágása** (be/ki pont) | `setin` · `setout` · `trimslider` | **nincs** — a tokent megőrizzük, de nem állítjuk | **ÚJ JEGY** |
| a vágás **visszaállítása** | `reset_trim` | nincs | ua. |
| **képkocka mentése** | `capture_frame` | nincs | ua. |
| a vágás **tárolása** | `moviestart` / `movieend` a `filters=`-ben | **ismerjük és megőrizzük** | — |
| YouTube-export | `export_youtube` | — | **hatókörön kívül** |

### Nyitott kérdések mérlege (64.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a vágás vezérlői és tárolása (64.1); a `movieeditpanel`
  három további művelete (64.2); a mi round-trip állapotunk (64.3).
- **BLOKKOLT:** a `moviestart`/`movieend` **értékformátuma** (képkocka?
  ezredmásodperc?). A korpuszban nem találtam mintát; a
  `binary-index/README` szerint a sorosítójuk a `0x00463fd0`.
  **Mi kell hozzá:** célzott dekompiláció **vagy** egy vágott videó
  `.picasa.ini`-je a tulajdonostól. **A jegyet részben blokkolja** —
  ezért a jegy `blocked` + `felhasználóra-vár` címkét kap.
- **HATÓKÖRÖN KÍVÜL:** a YouTube-export és a súgó-hivatkozás.

*(Záró mondat a 45.1 szerint: **van** hiányzó vezérlő — a vágás három
vezérlője és a képkocka-mentés; a csoportosztás nincs mérve.)*

### Amit KIZÁRTAM

- **„A videóhoz csak lejátszás tartozik"** — megdőlt: vágás be-/kimeneti
  ponttal, visszaállítással és képkocka-mentéssel (64.1–64.2).
- **„A `moviestart`/`movieend` tokent nem ismerjük”**: megdőlt: a
  regiszterben és a render-láncban is ott van, megőrizve (64.3).

### 64.5 #5710: a képkocka-mentés teljes útja és a mai összevetés

**Bizalmi fok: feltételes.** Két független út megerősíti, hogy a megadott
`snapshot` címek a kamerához, a `movieeditpanel/capture_frame` pedig a
videónézőhöz tartozik. A további eredeti részletek címzett diszasszemblálásból,
a maiak a forrásból vagy megnevezett mérésből jönnek; nem mindegyik értéket
ellenőriztem második, független módszerrel. Az eredeti fájlnév-tő értéke, a
`4` íróopció jelentése és a dekódolt képkocka pixelpontos egyezése nincs meg.

Az eredeti videóképkocka-művelet neve `movieeditpanel/capture_frame`
(`0x00c91ecc`), kezelője a `0x005952d0`; a `0x0059578f` ága a
`0x00592170`-en át indítja a `CCaptureFrame` munkát, amelyet a
`0x00591dd0` végez el. Ez **panelgomb**, nem menüparancs. A megadott
`snapshot` címek egy másik művelethez, a webkamera-pillanatképhez tartoznak:

| Eredeti | Nálunk | Teendő |
|---|---|---|---|
| `0x00c9dc50` `snapshot` → `0x006274f0`: webkamera-panel, külön állókép-rögzítési parancs | `CaptureMoviePanelPopup.qml`, külön kamerafunkció | Ne keverjük a videóból mentett képkockával. |
| `0x00c9ddcc` `snapshot.jpg` → `0x00628ec0`: a webkamera-pillanatkép rögzített fájlneve | A kamerakód `snapshot` kimenete; a videókocka-kód nem ezt a literált használja | **Nem** a videó-képkocka eredeti fájlneve. |
| `0x00c9df04` `/snapshot` → `0x0062a720`: webkamera-panel eseménye | Külön a videónéző `capture_frame` jelzésétől | Ne keverjük a két útvonalat. |
| `0x00c91ecc`; kezelő `0x005952d0`, ág `0x0059578f`: videónéző paneljén „Take Snapshot”; a jelenlegi lejátszási pozícióból indít mentést | `VideoEditPanel.qml:39-46`; `VideoPlayerView.qml:48-56`; `PhotoViewer.qml:2231-2234, 3382-3386` | **EGYEZIK**: ugyanaz a panelművelet és a pillanatnyi pozíció. |
| `0x005952d0` → `0x00592170` → `0x00591dd0`: a gomb háttérben futó mentéshez vezet; nincs fájlválasztó párbeszéd vagy képkocka-specifikus `Preferences`-kapcsoló ezen az ágon | A QML a vezérlőnek adja át a sort és az aktuális pozíciót; nincs mentési párbeszéd vagy külön képkocka-beállítás | **EGYEZIK**; a kamera `Preferences\\capturemoviesize` értéke a kamerás felvételi méret, nem ez a művelet. |
| `0x00591f5f`-`0x00591f7b`, `0x00c91808` `CCaptureFrame::CaptureFolder`: `<Képek>/Picasa/<honosított Captured Videos>`; magyar név „Rögzített videoklipek” | `frame_capture_controller.py:35-49`: `pictures_dir()/Picasa`, a meglévő ismert nyelvű mappa nyer, különben a mai nyelv szerinti `CAPTURED_VIDEOS` mappa | **EGYEZIK** új mappánál. Ha csak más nyelvű mappa létezik, **ELTÉR** az eredetitől; ez a #1131-ben dokumentált, szándékos újrafelhasználási szabály. |
| `0x00591fc5`, `0x00591fd5`, `0x00591ff0` → `0x00445a30`: új célmappánál `[Picasa] P2category=Projects (internal)` sort ír a `.picasa.ini`-be; létező mappát nem jelöl újra | `frame_capture.py:92-101` csak a mappát hozza létre és a JPEG-et írja; nem jelöli a mappát | **ELTÉR**: új célmappánál a projektjelölő hiányzik; fejlesztési teendő. |
| `0x00592003`-`0x0059200a`, `0x005921a6`-`0x005921aa`: a fájlnév-tő a konstruktor `[obj+0x68]` mezőjéből jön, értéke nem literál | `frame_capture_controller.py:98-100`, `movie/frame_capture.py:48-55`: a videófájl törzse, üres/tiltott névnél `frame` | **NINCS MEG**, honnan jön és mit tartalmaz az eredeti tő. Megszerzés: célzott Ghidra-adatfolyam-vizsgálat `0x005952d0`-ban. A `2026-10-21-koteg-1021b.txt` csak a diszpécserhívást sorolja, a mező jelentését nem. |
| `0x00993650` (`%s-%03lu`), számlálóhatár `0x1000`: kötőjeles, legalább háromjegyű sorszám, felső határ 4096 | `frame_capture.py:58-75`: `alapnév.jpg`, majd `alapnév-001.jpg` … `alapnév-4096.jpg` | **EGYEZIK** a sorszámozási szabály; a névtő egyezése nyitott. |
| `0x0059200f` (`.jpg`), `0x00592033`-`0x00592067` → `0x009d6010`: JPEG; íróblokk `{1, 4, 0x55}`. A harmadik érték 85-ös minőségi paraméter (`0x00ad3b30`; másik hívóút: `picasa-kollazs-felulet.md`, 1642. sor) | `frame_capture.py:35-36, 98-101`: `.jpg` kódolás `cv2.imencode`-del, minőségi paraméter nélkül. A helyi OpenCV 4.10.0 implicit DQT-táblája eltér az explicit 85-ösétől (**mérés**) | A kiterjesztés **EGYEZIK**; a JPEG-konfiguráció **ELTÉR**: a 85-ös minőség nincs explicit megadva. A `4` opció hatása nyitott. |
| `0x00591e78`-`0x00591f35`, `0x00591f30`, `0x00592091`, `0x00592115`: négy állapot: rögzítés, mentés, siker, hiba | `frame_capture_controller.py:82-86, 102-116`; `PhotoViewer.qml:3395-3440`: csak a végső siker/hiba jelzése jut el a felületre | **ELTÉR**: a két köztes állapotjelzés hiányzik. |

**Kimeneti mappa és besorolás.** Az eredeti mappajelölő csak akkor íródik,
amikor a könyvtár újonnan jön létre. Nálunk a képkocka mentője közvetlenül
`mkdir`-t és fájlírást végez, ezért az új mappa `P2category=Projects
(internal)` nélkül marad. A projektgyűjtemény besorolását a `.picasa.ini`
`P2category` mezője adja (`app/project_folder_names.py:34-35`,
`index/project_folders.py:1`). A javításnak az `ini/` csomag meglévő író API-ját
kell használnia.

**A fájlnév nyitott része.** A diszasszemblálás megmutatja az adatfolyamot:
`0x005952d0` átadja a `CThumbUI` `[ebp+0x3098]` mezőjét a `0x00592170`
konstruktornak; az `[obj+0x68]` mezővé válik, amelyet a `0x00591dd0` a
`.jpg` kiterjesztés elé fűz. Ez nem bizonyítja, hogy a tő a videó fájlneve.
Ezért a jelenlegi videótő nem minősíthető sem egyezőnek, sem eltérőnek.

**Kimeneti minőség.** Az eredeti `{1, 4, 85}` paraméterblokkja binárisból
igazolt; a harmadik mező 85-ös JPEG-minőségét a közös író másik hívóútja
erősíti meg. A PicasaPy kódja nem ad át minőségi paramétert. A helyi mérést
ugyanazon 16×16×3 `uint8` képkockán végeztem: OpenCV 4.10.0 implicit DQT-je
eltért az explicit 85-ös hívás DQT-jétől. Ez **mért helyi eltérés**, nem állítás
minden telepített OpenCV-verzióról. A bináris `{1,4,85}` blokk `4` mezőjének
szemantikája és a teljes JPEG-bájtsor PicasaPy-val való egyezése **NINCS MEG**;
a `0x009d6010` íróút célzott Ghidra-vizsgálata, illetve azonos videóból készült
eredeti és PicasaPy-képkocka golden-párja dönti el.

**A pontos képkocka.** Az eredeti a lejátszó pozícióját 100 ns-os értékből
másodpercre alakítja (`0x005957f3`, `0x0059581b`-`0x00595825`, konstans:
`0x00cf3e88`); nálunk a QML `media.position` ezredmásodpercet ad át, amit a
vezérlő a dekódernek továbbít (`VideoPlayerView.qml:54-56`,
`frame_capture_controller.py:88-109`). A két kódút ugyanazt a felhasználói
pozíciót célozza, de a kiválasztott dekóderképkocka azonossága **NINCS MEG**.
Megszerezhető azonos videófájl mindkét programban rögzített pozíciójának
mentésével és a két képkocka összevetésével; a helyi mérőarchívumban és a
`research/testdata/` alatt nincs videóminta. A jelen jegy név/hely/formátum
hatókörét ez nem módosítja.

#### Bizonyítékutak és cáfoló kör

- **A út: utasításszint:** a `0x005952d0` panelparancs `capture_frame` ága →
  `0x00592170` objektumkonstruktor → `0x00591dd0` munkafüggvény; ebből jön a
  pozíció, útvonal, `.jpg`, egyediesítés, projektjelölő és írónak adott blokk.
- **B út: független adat- és forrásoldal:** a `string_xrefs` külön a
  `0x00c91ecc` videóparancsot rendeli a `0x00593880`, `0x00594820` és
  `0x005952d0` függvényekhez; a három ticketben megadott `snapshot`-sztring
  ezzel szemben rendre a `0x006274f0`, `0x00628ec0`, `0x0062a720` kameraútjára
  mutat. A jelenlegi QML ugyanezt a kettéválást valósítja meg:
  `VideoEditPanel.qml` vs. `CaptureMoviePanelPopup.qml`. A két út egyezik.
- **Cáfoló próbálkozás:** azt próbáltam igazolni, hogy a `snapshot.jpg` és a
  `/snapshot` a videónéző mentési útjának része. A sztringhivatkozások és a
  `0x005952d0` videóparancs diszasszemblálása ezt megcáfolja: a `snapshot.jpg`
  a `0x00628ec0` kamera-állókép mentője; a videó worker dinamikus
  `[obj+0x68]`-ból és `.jpg` literálból épít nevet. A cáfolatot ugyanazzal a
  címszintű ellenőrzéssel ellenőriztem; nem maradt ellenpélda.

#### Nyitott kérdések

- **BLOKKOLT (örökölt):** az eredeti képkocka fájlnév-töve. Ghidra-kör kell:
  `0x005952d0`: a `0x00592170` harmadik argumentumaként átadott
  `[ebp+0x3098]` érték eredete és pontos tartalma [blokkoló].
- **BLOKKOLT (örökölt, a `picasa-create-features.md` írókérdésének
  kiegészítése):** Ghidra-kör kell: `0x009d6010`: a képkocka `{1,4,85}`
  blokkjában a `4` opció jelentése és az író pontos JPEG-adatútja. A meglévő
  kimenet a `{1,4,90}` poszterhívás minőségi mezőjét azonosítja, de a `4`
  opciót nem fejti meg.
- **BLOKKOLT (mérés):** a dekóder által kiválasztott képkocka egyezése; kell
  hozzá azonos forrásvideó és rögzített lejátszási pozíció mindkét programban.
- **LEZÁRVA:** gomb és feldolgozási út; mentési párbeszéd/beállítás hiánya;
  célmappa és `.jpg`; sorszám; hiányzó `.picasa.ini` jelölő; helyi JPEG-DQT
  eltérés; a két köztes állapotüzenet hiánya.

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 3 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

## 65. tétel — a KETTŐS NÉZET (2-up) NEM összehasonlítás, hanem KÉT SZERKESZTÉS (2026-09-01)

**Bizalmi fok: megerősített.** A megfejtést a bináris sztringtára és a
hivatalos magyar fordítás együtt adja; a tárolás helye a hívási környezetből.

### A lelet egy mondatban

A `2up` mód, amit eddig „összehasonlító nézetnek" neveztünk, valójában
**párhuzamos SZERKESZTŐ munkamenet**: ugyanazt a képet **kétféleképpen**
lehet megszerkeszteni egymás mellett, és kilépéskor a Picasa **megkérdezi,
melyik változatot tartsuk meg**. Ez nem nézegetés, hanem szerkesztési
munkafolyamat — a #434 eddigi keretezése („nézet") félrevezető volt.

### A döntő bizonyíték — a kilépési párbeszéd, hivatalos magyar szöveggel

| erőforrás-kulcs | angol | hivatalos magyar |
|---|---|---|
| `CThumbUI::Confirm2upEditTitle` | „Choose Edits" | „Szerkesztett változatok kiválasztása" |
| `CThumbUI::Confirm2upEditMsg` | „The same image has two different edits.  Which one would you like to keep?" | „A képnek két szerkesztett változata van. Melyiket szeretné megtartani?" |
| `CThumbUI::Confirm2upEditDontAsk` | „Don't ask again, always use the selected image" | „Ne kérdezzen újra, mindig használja a kijelölt képet" |
| `CThumbUI::Confirm2upLeft` / `…Right` | „Left" / „Right" | „Bal" / „Jobb" |
| `CThumbUI::Confirm2upTop` / `…Bottom` | „Top" / „Bottom" | „Fent" / „Lent" |

Forrás: `referencia/stringres-en-hu.tsv`. A párbeszédet felépítő függvény:
**`0x0056aad0`** — ugyanaz érinti mind a hét kulcsot, a `Cancel`-t és a
`Preferences` sztringet.

**A négy irány-felirat magyarázza a `swap_2up_layout`-ot:** a választást a
Picasa **pozíció szerint** kínálja, tehát vízszintes elrendezésnél
„Bal/Jobb", függőlegesnél „Fent/Lent". A két elrendezés nem díszítés — a
kilépési párbeszéd feliratai függenek tőle.

### TARTÓS állapot: a „ne kérdezzen újra" a registrybe kerül

A `DoNotAskOnEnd2Up` kulcsot **kizárólag** a `0x0056aad0` érinti, és ugyanez
a függvény hivatkozik a `Preferences` sztringre ⇒ a kulcs a
`SOFTWARE\Google\Picasa\Picasa2\Preferences` alatt él, a többi `Last*`/
kapcsoló-beállítás mintájára. Bekapcsolva a párbeszéd elmarad, és a
**kijelölt** oldal szerkesztése marad meg némán.

### A vezérlőcsalád HAT tagú (nem három, és nem is öt)

*Forrás: `editpanel.tre:1201` (`editpanel/layout_2up_group`).*

| elem | buboréksúgó | mit csinál |
|---|---|---|
| `only_1up_toggle` | „View only one image" | vissza egyképes nézetbe |
| `ab_2up_toggle` | „View two different images" | **két különböző** kép egymás mellett |
| `aa_2up_toggle` | „View the same image twice" | **ugyanaz a kép kétszer** — ez a két-szerkesztés mód |
| `swap_2up_focus` | „Switch which image has focus" | melyik oldal az **aktív** (oda mennek a szerkesztések) |
| `swap_2up_layout` | „Switch between horizontal and vertical layout" | vízszintes ↔ függőleges osztás |
| **`wipe_2up_toggle`** | *(nincs kimért felirat)* | **hatodik vezérlő** — törlő/függöny-átmenet a két oldal közt |

Csoport-tároló: `editpanel/layout_2up_group`.

### A két megjelenítő-felület a binárisban is kettő

A kapcsolókat kezelő függvények (`0x0056a260`, 1046 b; `0x0056a680`, 785 b)
**párban** hivatkoznak a felületekre: `editpanel/preview` ↔
`editpanel/previewimage2`, és `editpanel/previewclip` ↔
`editpanel/previewclip2`. A `0x0056a680` ezen felül a **`previewx0`** és
**`previewy0`** kulcsokat is érinti (a második felületnek külön
`preview2_x0` / `preview2_y0` párja van) ⇒ a két nézet **pásztázási pozíciója
külön tárolódik**.

### Az egyképes visszaváltás LEZÁRJA a futó eszközöket

Az `only_1up_toggle` kezelője (`0x00565fd0`, 660 b) ugyanabban a
függvényben hivatkozik a `editpanel/cropcancel`, `redeyecancel`,
`edittextcancel` és `manual_cancel` vezérlőkre ⇒ az egyképes nézetre váltás
**megszakítja a nyitott vágást / vörösszem-javítást / szövegbeírást /
kézi retust**. Ez viselkedés, nem elrendezés — a #434 megvalósításakor
kötelező.

### Amit KIZÁRTAM

- **„A 2up puszta nézegetés."** Megdőlt: a kilépési párbeszéd
  *szerkesztett változatokról* kérdez, nem megjelenítésről.
- **„A layout-váltó kozmetikai."** Megdőlt: a kilépési párbeszéd feliratai
  (Bal/Jobb vs. Fent/Lent) tőle függenek.
- **„Öt vezérlő."** Megdőlt: a `wipe_2up_toggle` a hatodik.

### Ami NYITVA marad (örökölt, a #434-be)

A `wipe_2up_toggle` **pontos viselkedése** — a felirata nincs a kimért
szövegtárban, és a `0x005d59f0` a teljes elemnév-tábla, nem kezelő. Ehhez
célzott dekompiláció kellene; a jegyben rögzítve.

## 66. tétel — az EFFEKT-CSEMPÉK: háromrétegű csempe, és a rács elrejtése (2026-09-01)

**Bizalmi fok: megerősített** a szerkezetre és a rejtési mechanizmusra;
**BLOKKOLT** arra, hogy az előnézet a felhasználó képét mutatja-e.

### A csempe HÁROM rétegből áll, nálunk kettőből

*Forrás: `editpanel.tre:299` (`editpanel/fx1`) · `editpanel.tre:295` (`editpanel/fx1_adorn`) · `editpanel.tre:297` (`editpanel/fxlabel1`) · `editpanel.tre:293` (`editpanel/fxpreview1`) · `editpanel.tre:428` (`editpanel/fxthumbs`).*

Az `editpanel.tre` mind a 12 csempét azonos szerkezettel írja le
(293–299. sor, `#--FX1`-től `#--FX12`-ig):

```
editpanel/fxpreview1: editpanel/fx1     m_offsetLT     <- előnézeti kép
editpanel/fx1_adorn:  editpanel/fx1     m_fxadorner    <- DÍSZÍTŐ RÉTEG
editpanel/fxlabel1:   editpanel/fx1     m_fxlabel      <- felirat
editpanel/fx1:        editpanel/fxthumbs               <- maga a csempe
```

| réteg | eredeti | nálunk (`ToolTile.qml`) |
|---|---|---|
| előnézet | `fxpreviewN` | `Image`, **statikus SVG**: `source: "icons/" + iconFile + ".svg"`, 44×30 (:76–88) |
| **díszítő** | `fxN_adorn`, saját `m_fxadorner` osztály | **NINCS semmilyen alakban** |
| felirat | `fxlabelN`, `m_fxlabel` | `Text` (:91) |
| aktív jelzés | *(nem a díszítőn keresztül dokumentált)* | háttérszín + **1 képpont keret** (:54, :61) |

A 12-es darabszám **egyezik**: az `EditorEffectsTab1.qml` pontosan 12 csempét
sorol fel (`effectUnsharp` … `effectDirTint`, :53–130). **A hiány nem a
darabszámban van, hanem a csempe szerkezetében.**

### A rács ELTŰNIK, amikor egy eszközt választasz

Az eszközgombok deklaratív tulajdonságai (`editpanel.tre:128–132`):

```
Property setpressed 1
Property mousedown 1
Property showtarget editpanel/tabpanel1
Property hidetarget editpanel/filter_name
Property hidetarget editpanel/fxthumbs
```

⇒ egy eszköz megnyitása **elrejti az effekt-rácsot** (`fxthumbs`) **és** a
szűrőnevet (`filter_name`), és megjeleníti a hozzá tartozó lapot. Ugyanezt a
kódoldal is megerősíti: a **`0x00750ff0`** (1702 b) egyetlen függvényben
érinti a `fxthumbs`-ot, az `editslider%d_container`-t, a `colorwheel%d`-t, az
`editlabel%d`-t, a `filter_name`-et, az `ok`/`cancel` gombokat és a
`finetune` / `finetune2` / `colorfix` neveket.

⚠️ A `setpressed 1` / `mousedown 1` = a vezérlő **LENYOMÁSRA** sül el, nem
felengedésre. **Ezt egy korábbi kör már feltárta és jegyre vitte: #885**
(49 vezérlő) — itt csak megerősítés, nem új lelet.

### A csempék tab- és módfüggők

A `0x005d7c20` (1614 b) a `fxpreview1`, `fxlabel%d`, `fx%d`, `fx%d_adorn` és
`fxthumbs` mellett a **`_tab%d`** és **`_mod%s`** utótagokat is formázza ⇒ a
csempekészlet a **fül** és egy **módosító** szerint változik. A módosító
konkrét jelentése nincs feltárva.

### Elhelyezés: a két varázsgomb NEM az effekt-fülön van

`editpanel/magic_color` és `editpanel/magic_lighting` szülője a
**`tabpanel2`** (`editpanel.tre:259`, `:265`), nem az effektrács. A
`greybalancelabel` és a `filllightlabel` ugyanitt, `m_fxlabel2` stílussal —
tehát az `m_fxlabel2` **közös felirat-osztály**, nem effekt-specifikus.

### ~~NYITOTT (blokkolt): élő előnézet-e a `fxpreview`?~~ ✅ LEZÁRVA (2026-09-04)

**Igen, élő előnézet — sőt a szerkesztési lánc AKTUÁLIS tetején.** A
tulajdonos hat képernyőképe (`research/#2061-effekt-latszik/`, három
független ELŐTTE/UTÁNA pár három effekt-fülön) eldöntötte: a 12 csempe a
megnyitott fényképet mutatja effektenként, és amikor a képre Fekete-fehér
kerül, **az összes csempe alapja is szürkévé válik**.

A teljes levezetés, a csempe-újraépítés kimerítő hívó-leltárával együtt:
`ui-audit-editor.md`, „Az effekt-csempe ELŐNÉZETÉNEK betöltési lánca".
Jegyek: **#2061** (lezárva), **#2273** (a megvalósítás), **#1869**.

*(Az itt korábban álló „a `respack.yt` nincs meg ebben a checkoutban"
megjegyzés a kérdés eldöntéséhez már nem kell; a fenti bizonyíték nem
erőforrás-alapú.)*

---

## 67. tétel — a mappalista-rendezés HIÁNYZÓ darabjai: a 0. mód, a 4. mód és a negyedik belépési pont (2026-09-04, #2304)

> ⛔ **ÖNHELYESBÍTÉS.** Ennek a tételnek az első változata (ugyanaznap)
> **négy állítást tartalmazott, ami a 36. tételben MÁR BENNE VOLT**, egyet
> pedig **tévesen** „NINCS MEG"-nek jelölt. A hiba oka: nem olvastam el a
> saját lapunk 36. tételét, mielőtt írtam. A helyesbítés:
>
> | az első változat állítása | valójában |
> |---|---|
> | „a `datesort` mód-szám, nem logikai érték" | **a 36.3 már kimondta** (2026-08-31) |
> | „a fordítás a komparátoron belül érvényesül" | **a 36.4 már kimondta** |
> | „a parancsok **két** menüben élnek" | **HIBÁS** — a 36.5 szerint **három**, és ez a kör talált egy **negyediket** |
> | „a **Méret** mód-száma **NINCS MEG**" | **HIBÁS** — a 36.4 szerint **5**, és a mértékegysége is megvan (64 bites bájtösszeg) |
>
> Az emiatt nyitott **#2320** jegy tárgytalan, lezárva.
> **Ami ténylegesen új, az alább áll.**

### 67.1 ⭐ A NEGYEDIK belépési pont — a könyvtár-nézet két rendezőgombja

A 36.5 három menüt sorolt fel (menüsáv ▸ Nézet · bal hasáb ▾ előugró ·
album helyi menü ▸ „Sort By"). Van egy **negyedik**, nem menü, hanem két
**gomb** a könyvtár-nézetben — a kezelőjük `FUN_005d9cc0`:

| elem | cím | átadott mód (`edx`) |
|---|---|---|
| `thumbui/datesort` | `0x005db26d` (`xor edx, edx`) | **0** |
| `thumbui/namesort` | `0x005db207` (`mov edx, 2`) | **2** |

⇒ ez adja a **0. mód** felhasználói jelentését, amit a 36.3 mód-listája
(`0/1/2/5`) tartalmazott ugyan, de vezérlőhöz nem kötött: **a 0. mód a
„dátum"**.

### 67.2 ⭐ Van egy NEGYEDIK mód is — `4`

A komparátor (`FUN_004a7890`) `0x004a7e2a`-nál **`cmp edx, 4`**, és a
`0x004a7e2f` ágban a `0x004502e0([this+0xc4], tétel, &ki)`-t hívja kétszer,
**double**-ként hasonlítva. A 36.3 mód-listája ezt **nem tartalmazta**.

**A komparátor teljes ágtáblája** (a 36.4 kiegészítése):

| `[this+0xd8]` | ág | kulcs | vezérlő |
|---|---|---|---|
| **0** | `0x004a7d95` | a tétel saját **double** kulcsa (`fld qword`) | `thumbui/datesort` |
| 1 | `0x004a7e89` | `0x00450bd0(…)` → double | `ID_VIEWBYRECENT` (36.) |
| **4** | `0x004a7e2f` | `0x004502e0(…)` → double | ⚠️ **nincs hozzá ismert vezérlő** |
| 5 | `0x004a7efe` | `0x004507e0(…)` → 64 bites bájtösszeg (36.4) | `ID_VIEWBYSIZE` (36.) |
| **minden más** (köztük 2) | `0x004a7f5f` | a tétel **nevének sztringje** (`+0x5c`) | `ID_VIEWBYNAME`, `thumbui/namesort` |

### 67.3 ⭐ A szempontváltás NEM nullázza a fordítást

A beállító `FUN_004b07c0` (75 b) **egyszerre** veszi a módot és a fordítást:

```
0x004b07c4  cmp [lista+0xd8], edx      ; ugyanaz a mód?
0x004b07cc  cmp [lista+0x165], cl      ; és ugyanaz a fordítás?
            -> ha mindkettő, nincs változás (0xF4242)
0x004b07dc  mov [lista+0x165], cl
0x004b07e2  mov [lista+0xd8], edx      ; egyébként MINDKETTŐT beállítja
            -> majd újrarendez (0x006dc4c0)
```

A két rendezőgomb a **jelenlegi** fordítás-értéket adja tovább
(`mov cl, byte ptr [eax+0x165]`, `0x005db200` és `0x005db266`) ⇒ **a
rendezési szempont váltása megtartja a fordított sorrendet.** *(A 36.4 azt
mondta meg, HOL érvényesül a fordítás; ez azt, hogy szempontváltáskor mi
történik vele.)*

### 67.4 A mi oldalunk — MÉRVE, és HELYES

`src/picasapy/app/photo_sort.py` + `folder_photo_sort_controller.py`:

| tétel | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| a fordítás tárolása | **külön** kulcs (`albumlistflip`) | **külön** beállítás (`view/folderPhotoSortReverse`, `photo_sort.py:27`) | — |
| szempontváltáskor | a fordítás **megmarad** | `setFolderPhotoSort()` (`folder_photo_sort_controller.py:70`) **nem nyúl** a reverse-hez | — |
| név-kulcs | sztring | `r.name.casefold()` (`photo_sort.py:75`) | — |
| dátum-kulcs | **egyetlen** double | `(photo_date(r), r.name.casefold())` — **másodlagos kulcs is** (`:71`) | eldöntendő: az eredetinek nincs másodlagos kulcsa |

⇒ **A fordítás függetlensége nálunk MÁR HELYES** — ez a kör ezt igazolta,
nem hibát talált.

### 67.5 ⛔ NINCS MEG: a 4. mód vezérlője

A `{0, 1, 2, 5}` mind meg van feleltetve vezérlőnek (36. + 67.1); a **4.**
módhoz **nem ismert** felhasználói vezérlő. Nem zárható ki, hogy belső
(programból állított) rendezés. **Megszerzés:** a `FUN_004b07c0` összes
hívója (`edx = 4`-gyel). Jegy: **#2320**.

---

## 68. tétel — a mappalista-rendezés TELJES mód-készlete, és egy ASCII-only névhasonlítás (2026-09-04, #2320)

> **Bizonyítottság: megerősített** — kimerítő hívó-pásztázás és kiolvasott
> konstansok. Ez a tétel a **36.** és a **67.** lezárása: a mód-készlet
> ettől kezdve teljes.

### 68.1 A `+0xd8` mód-mezőnek KÉT írója van, és mindkettő elszámolt

| író | mit ír | hívói |
|---|---|---|
| `FUN_004a1560` `0x004a1991` | a **nyers registry-értéket** (`Preferences\datesort`), **validálás nélkül** | indulás |
| `FUN_004b07c0` (75 b) | `edx`-et | **pontosan 3** hívó |

`FUN_004b07c0` három hívója (kimerítő `e8`-pásztázás a `.text`-en):

| hívó | átadott mód |
|---|---|
| `0x005db20c` (`FUN_005d9cc0`) | **2** — `thumbui/namesort` |
| `0x005db26f` (`FUN_005d9cc0`) | **0** — `thumbui/datesort` |
| `0x005d3127` (`FUN_005d30f0`) | *öröklött* `edx` — továbbadó |

`FUN_005d30f0` **hat** hívója, mind a `FUN_005cb990` parancs-diszpécserben:

| cím | `edx` | jelentés |
|---|---|---|
| `0x005cbbf6` | `xor edx, edx` → **0** | dátum |
| `0x005cbc2d` | `mov edx, 1` | legutóbbi változtatás |
| `0x005cbc10` | `mov edx, 2` | név |
| **`0x005cd5f2`** | **`mov edx, 3`** | ⭐ **ÖTÖDIK mód — a 36.3 listája (`0/1/2/5`) ezt sem tartalmazta** |
| `0x005cc703` | `mov edx, 5` | méret |
| `0x005cd61c` | `edx = [obj+0xd8]` **változatlan**, `cl = !cl` (`test cl,cl` + `sete cl`) | **a fordítás kapcsolója** |

⇒ **A felületről elérhető mód-készlet: `{0, 1, 2, 3, 5}`**, plusz a
fordítás-váltó.

### 68.2 ⛔ A 4. mód a felületről ELÉRHETETLEN — negatív eredmény

A 67.2 talált a komparátorban egy `cmp edx, 4` ágat (`0x004a7e2a`). A fenti
kimerítő pásztázás szerint **egyetlen hívó sem ad át 4-et**:

- a `+0xd8`-nak két írója van, mindkettő elszámolt (68.1);
- a `FUN_004b07c0` 3 hívója és a `FUN_005d30f0` 6 hívója **mind** felsorolva.

⇒ A 4. mód **csak akkor lép működésbe, ha a `Preferences\datesort` registry-érték
literálisan 4** — a betöltő ugyanis **nem validál**. Ez tehát vagy **örökölt
(korábbi verzióbeli) érték**, vagy fejlesztői kapcsoló. **Nem megépítendő.**

*(A 4. mód kulcsa a `0x004502e0`-ból jön — a `[this+0xc4]` adatforráson, mint
az 1. és az 5. mód kulcsai.)*

### 68.3 ⭐ A 3. mód a NÉV-ággal azonos viselkedésű

A komparátor (`FUN_004a7890`) csak a `0`, `1`, `4`, `5` értékre ágazik el;
**minden más — tehát a 2 ÉS a 3 is — a sztring-ágra esik** (`0x004a7f5f`).
A 3. mód ezek szerint **ugyanazt a rendezést adja, mint a 2.**; a
megkülönböztetése (ha van) nem ebben a komparátorban van.

### 68.4 ⭐ A névhasonlítás ASCII-ONLY kisbetűsítést végez

A sztring-ág (`0x004a7fd2`–`0x004a7ff5`) **beágyazott**, bájtonkénti
hasonlítás, és a kisbetűsítése **kizárólag az `A`–`Z` tartományra** hat:

```
0x004a7fda  cmp cl, 0x41       ; 'A'
0x004a7fdd  jl  …
0x004a7fdf  cmp cl, 0x5a       ; 'Z'
0x004a7fe2  jg  …
0x004a7fe4  add cl, 0x20       ; -> kisbetű
```

⇒ **Az ékezetes nagybetűk NEM esnek egybe a kisbetűs párjukkal.** A
`Á` és az `á` két különböző érték marad, és a rendezésben a bájtértékük
dönt — az ASCII-tartomány (`a`–`z` = 0x61–0x7A) **mindig megelőzi** őket.

⚠️ **Nálunk ez MÁSKÉPP van** (mérve): `models.py:347` a mappalistában
`f[0].casefold()`, `photo_sort.py:74` a képeknél `r.name.casefold()` — a
Python `casefold()` **Unicode-tudatos**, tehát az `Á` és az `á` nálunk
egybeesik. Magyar mappa- és fájlneveknél ez **eltérő sorrendet ad**.

*(Ez a #2304 „a 3. sortól más a sorrend" tételének egy lehetséges,
önállóan ellenőrizhető oka — de **ok-okozatilag nincs bizonyítva**: a
mechanizmus mérve van, a mért eltérésre gyakorolt hatása NINCS mérve.)*

### 68.5 Eredeti / nálunk / teendő

| tétel | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| mód-készlet | `{0,1,2,3,5}` + fordítás-váltó; a **4** elérhetetlen | `("name","size","changed", dátum)` (`models.py:344`) | — |
| a 3. mód | a névvel azonos viselkedés | nincs külön | **nem kell** megépíteni |
| a 4. mód | csak kézzel írt registry-értékkel | nincs | **nem kell** megépíteni |
| névhasonlítás | **ASCII-only** kisbetűsítés (`A`–`Z`) | `casefold()` — **Unicode** | eldöntendő (#2304) |


## 69. tétel — a „Mappa rendezésének alapja ▸ Dátum" KULCSA: a `thumbindex` első időbélyege (2026-09-04, #2304)

> **Bizonyítottság: erős.** A választ **mérés** támasztja alá a tulajdonos
> valódi katalógusán, két független próbával; bit-pontos újrajátszás
> (a teljes eredeti sorrend) nem készült, ezért nem „megerősített".

A #2304 első kérdése: **melyik mezőt használja az eredeti a mappán belüli
„Dátum" rendezéshez?** A jegy megfigyelése szerint a Picasa 3 és a
PicasaPy **első 18 képe azonos**, utána szétválik: az eredeti
összefésüli a `_<hexa>` és a `DALL·E …` nevű fájlokat, nálunk viszont a
`DALL·E` fájlok **egy tömbben** jönnek.

### A mérés

Anyag: a tulajdonos 2026-08-22-i `Picasa2` adatmappa-mentése; a szóban
forgó mappa **88 képe** a `thumbindex.db`-ből, a saját
`pmpimport.thumbindex` olvasónkkal. A `thumbindex` rekordja **két**
FILETIME mezőt tárol (`+0x00` és `+0x08`).

**1. próba — a jegyben rögzített első 18 fájlnév sorrendje.** Hány
egyezik elölről, megszakítás nélkül?

| rendezőkulcs | egyező előtag |
|---|---:|
| a rekord **1.** FILETIME-ja | **10 / 18** |
| a rekord **2.** FILETIME-ja | **10 / 18** |
| **fájlnév** (kisbetűsen) | **0 / 18** |

⇒ **A név mint kulcs KIZÁRVA.** A tárolt időbélyeg viszont a jegyben
felsorolt első tíz nevet **pontosan abban a sorrendben** adja vissza.
*(A 11. elemtől eltér — a mentés 2026-08-22-i, a képernyőkép későbbi.)*

**2. próba — a jegy legbeszédesebb jele: összefésülődnek-e a névcsoportok?**
A 88 kép három névcsoportba esik (`DALL·E …` 12, `_<hexa>` 23, egyéb 53);
megszámolva, hányszor VÁLT a csoport a rendezett listában:

| rendezőkulcs | csoportváltás | a `DALL·E` fájlok |
|---|---:|---|
| a rekord **1.** FILETIME-ja | **7** | **szétszórva**, a `_<hexa>`-k közé fésülve |
| a rekord **2.** FILETIME-ja | 6 | **egy tömbben** (12 egymás után) |
| fájlnév | 4 | egy tömbben |

⇒ Az **1. FILETIME** adja azt a képet, amit a tulajdonos az eredetiben
lát; a 2. FILETIME és a név ugyanazt a „`DALL·E` egy tömbben" alakot adja,
mint a mi mai kimenetünk.

### Eredeti / nálunk / teendő

| | eredeti | nálunk (mérve) |
|---|---|---|
| a „Dátum" kulcsa | a `thumbindex` rekord **1. FILETIME**-ja (a Picasa saját, beolvasáskor rögzített fájlideje) | `taken_at` (EXIF), ha van; **egyébként a fájl MAI `mtime`-ja** (`app/photo_sort.py:56–64`) |
| holtverseny | nem mérve | fájlnév kisbetűsen (`photo_sort.py:71`) |

⇒ **Ez magyarázza a jelenséget.** Az EXIF nélküli (letöltött, generált)
képeknél mi a mai fájlidőre esünk vissza; ha a fájlok egyszerre kerültek a
lemezre, az érték **azonos**, és a holtversenyt a NÉV dönti el — innen a
„`DALL·E` egy tömbben". Az eredeti ezzel szemben egy **beolvasáskor
rögzített, fájlonként eltérő** időt használ.

✅ **LEZÁRVA (2026-09-05, #2304):** hogy az 1. FILETIME a fájl létrehozási
vagy módosítási ideje-e a forrásrendszeren, és hogy a Picasa frissíti-e
újraolvasáskor. **Egyik sem:** a kép **metaadat-dátuma**, a beolvasás
pillanatában rögzítve (beolvasáskori író: `0x004eeb10`, egyetlen hívó:
`0x00427898`; ⛔ 2026-10-11, #4591: a Dátum és idő beállítása nem-JPEG ága
is írja — `0x004ef3c0`/`0x004ef5a0`, `pmp-database.md` 15.1), és a pásztázó **soha nem frissíti** — az csak a 2. mezőt
(a fájl **módosítási** idejét) és a méretet írja felül. A teljes levezetés
és a mérés: `pmp-database.md` 10. szakasz.

> ⛔ **Helyesbítés az alábbi táblához.** A „nálunk" oszlop azt sugallta,
> hogy a mi **tartalék-szabályunk** tér el (EXIF hiányában a mai `mtime`).
> Nem tér el: az eredeti is a fájl módosítási idejére esik vissza, ha a
> képnek nincs metaadat-dátuma (mérve, `pmp-database.md` 10.4). A valódi
> különbség a **rögzítettség** — az eredeti a beolvasáskori értéket
> tárolja, mi minden rendezéskor élőben olvassuk a `mtime`-ot.

*A saját megfelelőnk nem az `mtime` pillanatnyi értéke kell legyen, hanem
egy **indexeléskor rögzített** időmező — különben a sorrend a fájlok
másolásakor megváltozik.*

## 23. adag (2026-09-06) — az `Address::ID_AUTOCOMPLETE` VISELKEDÉSE, végig

*A 19. adag megnevezte a hét tételes szövegmező-helyimenüt, és az
`ID_AUTOCOMPLETE`-ről annyit mondott: „kikapcsolható automatikus kitöltés".
Hogy **mit** kapcsol, **hova** menti, és **mi az alapértéke**, nem volt
mérve. Ez a szakasz azt pótolja. Jegy: **#1526**.*

### 23.1 A három függvény

| cím | méret | szerep |
|---|---|---|
| `0x007331e0` | 662 b | a menüt **építi** (a hét `Address::ID_*` erőforrás-kulcs feloldása) |
| `0x008518e0` | 622 b | a menüt **kiteszi és kiértékeli** (tiltás · pipa · `TrackPopupMenu` · parancs-szétosztás) |
| `0x00851b50` | 120 b | az `ID_AUTOCOMPLETE` **kapcsolója** |

A hívási lánc: `0x00850770` → `0x008518e0` → `0x007331e0`.

### 23.2 A hét tétel parancsazonosítója és a végrehajtott üzenet

Mind a hét a szerkesztőmező (`[this+0x324]`) ablakkezelőjének küld egy
Windows-üzenetet, `SendMessageA`-val (`0x00c40884`):

| # | erőforrás-kulcs | parancsazonosító | üzenet | cím |
|---|---|---|---|---|
| 1 | `Address::ID_UNDO` (`0x00cae700`) | `0x9d7f` | `WM_UNDO` (`0xc7`) | `0x00851a6c` |
| 2 | `Address::ID_CUT` (`0x00cae6e8`) | `0x9d39` | `WM_CUT` (`0x300`) | `0x00851a8f` |
| 3 | `Address::ID_COPY` (`0x00cae6cc`) | `0x9d3b` | `WM_COPY` (`0x301`) | `0x00851ab2` |
| 4 | `Address::ID_PASTE` (`0x00cae6b8`) | `0x9d3c` | `WM_PASTE` (`0x302`) | `0x00851ad2` |
| 5 | `Address::ID_DELETE` (`0x00cae69c`) | `0x9c56` | `WM_CLEAR` (`0x303`) | `0x00851af2` |
| 6 | `Address::ID_SELECTALL` (`0x00cae678`) | `0x9d7e` | `EM_SETSEL` (`0xb1`), `wParam=0`, `lParam=-1` | `0x00851b12` |
| 7 | `Address::ID_AUTOCOMPLETE` (`0x00cae64c`) | `0x9d82` | **nem üzenet** — `call 0x00851b50` | `0x00851b28` |

⚠️ **Hatókör.** Ezek az `Address::` névtér azonosítói. A `0x9d39` ugyanaz a
szám, mint a **Szerkesztés** menü Kivágás-parancsa (`picasa-menusor-csoportok.md`),
a `0x9d7f` / `0x9d7e` / `0x9d82` viszont **csak itt** fordul elő. A
`picasa-gyorsbillentyuk.md` `Ctrl+X`/`Ctrl+C`/`Ctrl+V` sorainak
„mikor tiltott" cellája az `eMenuEdit` névtérre vonatkozik — azt ez a
mérés **nem** dönti el, ezért ott marad a „nincs mérve".

### 23.3 Mikor TILTOTT — mind a négy feltétel kimérve

A menü kitétele előtt (`0x008518ed`–`0x008519cd`) négy vizsgálat fut, és
mindegyik `EnableMenuItem`-mel (`0x00c40818`) szürkít, `MF_GRAYED` (`1`)
jelzővel:

| tétel(ek) | a vizsgálat | cím | tiltás, ha |
|---|---|---|---|
| Visszavonás | `EM_CANUNDO` (`0xc6`) | `0x00851902` | a visszaadott érték **0** |
| **Kivágás + Másolás + Törlés** (mind a három EGYÜTT) | `EM_GETSEL` (`0xb0`) | `0x0085193c` | a kezdő- és a végpozíció **egyenlő** (nincs kijelölés) |
| Beillesztés | `OpenClipboard(NULL)` → `GetClipboardData(1)` → `CloseClipboard` | `0x0085196e`–`0x0085197e` | a vágólapon **nincs `CF_TEXT`** |
| Az összes kijelölése | `WM_GETTEXTLENGTH` (`0xe`) | `0x0085199f` | a mező **üres** |

Az **Automatikus kitöltés soha nem tiltott** — nála a `CheckMenuItem`
(`0x00c40810`) fut, `MF_CHECKED` (`8`) vagy `MF_UNCHECKED` (`0`) jelzővel,
a `[this+0x5b8]` bájt szerint:

```
0x008519b3  cmp byte ptr [esi + 0x5b8], 0
0x008519ba  je  0x8519c0
0x008519bc  push 8                       ; MF_CHECKED
0x008519be  jmp 0x8519c2
0x008519c0  push 0                       ; MF_UNCHECKED
0x008519c2  push 0x9d82
0x008519c7  push ebx
0x008519c8  call dword ptr [0xc40810]    ; CheckMenuItem
```

⇒ **pipás menütétel**, nem gomb. A menü `TrackPopupMenu`-val (`0x00c407c4`,
`0x00851a45`) jön fel, `TPM_RETURNCMD | TPM_RIGHTALIGN | TPM_RIGHTBUTTON`
(`0x10a`) jelzőkkel — tehát a parancsazonosítót a hívás **visszaadja**, és a
szétosztás a fenti `cmp`-lánccal helyben történik.

### 23.4 MIT csinál a kapcsoló — a tároló, a kulcs, az alapérték

A `0x00851b50` teljes törzse:

```
0x00851b53  cmp  byte ptr [esi + 0x5b8], 0
0x00851b5b  sete al                          ; INVERTÁL
0x00851b5e  mov  byte ptr [esi + 0x5b8], al
0x00851b67  push 0xcc2640                    ; "EmailAutocomplete"
0x00851b6c  push 0xc7eafc                    ; "Preferences"
0x00851b80  call 0x00407a20                  ; beállítás-objektum
0x00851b98  call 0x00401900                  ; ÍRÁS
0x00851b9d  mov  al, byte ptr [esi + 0x5b8]
0x00851ba7  mov  byte ptr [esi + 0x3e0], al  ; másodpéldány
```

| | mérve |
|---|---|
| tároló | `HKEY_CURRENT_USER\SOFTWARE\Google\Picasa\Picasa2\Preferences\EmailAutocomplete` (a kulcsnév `0x00cc2640`, a szekció `0x00c7eafc`; az útvonal összeszerelése: 6.1 szakasz, `picasa-email-kuldes.md`) |
| mikor íródik | **azonnal**, a menütétel megnyomásakor — nincs OK-gomb, nincs kilépéskori mentés |
| memóriabeli állapot | `[this+0x5b8]` bájt, és vele azonos értékkel `[this+0x3e0]` |
| **alapérték** | **1 (bekapcsolva)** — az építőben `mov byte ptr [edi+0x5b8], 1` (`0x0084fe43`), és a registry-olvasás alapértéke is `1` (`edi = 1`, `0x0085021a`; átadás: `mov dword ptr [esp+0x20], edi`, `0x008503e6`) |
| honnan jön INDULÁSKOR | `0x008503d1`–`0x00850405`: ugyanaz a kulcs, `0x00407a20` + `0x004019b0` (olvasás), majd `mov [ebp+0x5b8], al` és `mov [ebp+0x3e0], al` |

⇒ **A kulcs neve `EmailAutocomplete`** — vagyis az `Address` névtér az
**e-mail-címmező**, és az automatikus kitöltés a korábban használt
címeket ajánlja. Ez összeér a `picasa-email-kuldes.md` beállítás-készletével
(`EmailPrepType`, `DoNotPromptForEmailPref`, `EmailExportSize`).

### 23.5 Az írók és olvasók TELJES készlete (kimerítő pásztázás)

A `.text` teljes szakaszán (fájloffset `4096`, `8646656` bájt) végigfutó,
indextől független bájt-hozzáférés-keresés a `+0x5b8` és a `+0x3e0`
eltolásra (`mov`/`cmp`/`movzx`/`movsx`, `mod=10`, SIB és `ebp`-lokálisok
kizárva):

| eltolás | találat | cím | mi |
|---|---|---|---|
| `+0x5b8` | 1 | `0x0084fe43` | ÍRÓ — az építő alapértéke (`= 1`) |
| `+0x5b8` | 2 | `0x008503ff` | ÍRÓ — a registryből olvasott érték |
| `+0x5b8` | 3 | `0x008519b3` | OLVASÓ — a pipa kirakása |
| `+0x5b8` | 4 | `0x00851b53` | OLVASÓ — a kapcsoló invertálása |
| `+0x5b8` | 5 | `0x00851b5e` | ÍRÓ — a kapcsoló |
| `+0x5b8` | 6 | `0x00851b9d` | OLVASÓ — a másodpéldány feltöltése |
| `+0x3e0` | 1 | `0x00850405` | ÍRÓ — indulás |
| `+0x3e0` | 2 | `0x00851ba7` | ÍRÓ — a kapcsoló |

⚠️ **ELAVULT JELÖLÉS (2026-09-10, #2825):** a #2524 **lezárva** — a mező
gazdája a **`CEmailAutoComplete`** (a `ComposeDialog+0x26c`-en, RTTI-vtábla
`0x00cc2f90`), tehát `ComposeDialog+0x3e0` = **`CEmailAutoComplete+0x174`**;
a teljes levezetés a lap **24. adagjában** áll (PR #2527). A pásztázás alábbi
negatív eredménye érvényes marad — épp azt magyarázza meg, miért kellett az
RTTI-út. A bekezdés szövege történeti okból marad.

⚠️ ~~**NYITOTT, és nevén nevezve:**~~ a `+0x3e0` mezőnek **egyetlen bájt-szintű
olvasója sincs** ebben a pásztázásban — csak a két írója. Ez **nem** jelenti,
hogy halott: a fordító a `bázis + tag` konstanst összevonhatja (ezt a
`facerect`-körben már mértük), ezért az olvasó egy másik bázisregiszterrel,
más eltolással is állhat. **A tényleges kitöltő-logika (mit ajánl fel a mező,
honnan veszi a korábbi címeket) tehát NINCS MEG** — a megszerzés útja: a
`+0x3e0`-t tartalmazó objektum azonosítása RTTI-ből, majd az azt olvasó
`WM_CHAR`/`EN_CHANGE`-kezelő. Külön jegy: **#2524**.

### 23.6 MIT ADUNK MA — mérve

| | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| a hét tétel megléte és sorrendje | `0x007331e0` | **megvan**, azonos sorrendben (`app/qml/PicasaPy/TextFieldContextMenu.qml`) | — |
| Automatikus kitöltés | **pipás** tétel, állapota a `+0x5b8` | `PicasaMenuItem` **helyfoglaló**, `checkable` nincs, `onTriggered` nincs | pipás tétellé kell tenni |
| az állapot tárolása | registry `Preferences\EmailAutocomplete`, azonnal | **nincs** | `QSettings`-kulcs, azonnali mentés |
| alapérték | **1 (be)** | — | `true` |
| Kivágás tiltása | kijelölés nélkül szürke | `menu.editable && menu.hasSelection` — **egyezik** | — |
| Másolás tiltása | kijelölés nélkül szürke | `menu.hasSelection` — **egyezik** | — |
| Törlés tiltása | kijelölés nélkül szürke | `menu.editable && menu.hasSelection` — **egyezik** | — |
| Beillesztés tiltása | `CF_TEXT` hiányában szürke | `menu.target.canPaste` — **egyezik** (a Qt is a vágólap szövegét nézi) | — |
| Az összes kijelölése tiltása | **üres mezőnél** szürke | `menu.target.length > 0` — **egyezik** | — |
| Visszavonás tiltása | `EM_CANUNDO` = 0 | `menu.target.canUndo` — **egyezik** | — |

⇒ **A tiltási feltételek mind a hat tiltható tételnél egyeznek** — ezt eddig senki nem
mérte, most igazolt. Egyedül az **Automatikus kitöltés** üres nálunk.

### 23.7 Megvalósítás (#4636, 2026-10-08)

A 23.6 táblázat a 2026-09-06-i állapotot rögzíti. A #4636 ezt követően
bekötötte a pipás menütételt az e-mail címzett mezőbe: a beállítás a
`mail/EmailAutocomplete` QSettings-kulcsban marad meg, alapértéke `true`.
Az eredeti mérés szerint ez a beállítás a pipát és az értéket tárolja, a
javaslómotort nem vezérli; a keresőmező külön `SearchSuggestions` útja ezért
független marad.

## 24. adag (2026-09-06) — az automatikus kiegészítés FORRÁSA, és a kapcsoló, amit SENKI NEM OLVAS

*A 23. adag kimérte, mit **kapcsol** az `ID_AUTOCOMPLETE` és hova menti; nyitva
maradt, hogy a `+0x3e0` mezőt ki olvassa, és honnan jönnek a felajánlott címek.
Ez a szakasz mindkettőt lezárja. Jegy: **#2524**.*

### 24.1 A mező gazdája: `CEmailAutoComplete`

| | cím | bizonyíték |
|---|---|---|
| a `ComposeDialog` `+0x26c` tagja | `0x0084fd3a` `lea eax, [edi + 0x26c]` → `0x0084fd5e` `call 0x00858480` | az építő |
| az osztály | **`CEmailAutoComplete`** | RTTI-vtábla `0x00cc2f90` (és `0x00cc2fbc`), az építő `0x00858480` írja: `0x008584a8`, `0x008584ae` |
| második bázis | **`INotifyContactsDownload`** a `+0x15c`-en | `0x0085849c` `mov [esi+0x15c], 0xcad758` → `0x008584e6` `mov [esi+0x15c], 0xcc3070` |

⇒ **`ComposeDialog + 0x3e0` = `CEmailAutoComplete + 0x174`** (`0x3e0 − 0x26c = 0x174`),
és a mezőnek **saját alapértéke is 1**: `0x0085850e` `mov byte ptr [esi + 0x174], 1`
— az építő tagkezdő blokkjában, a `+0x160`…`+0x17c` mezők között.

### 24.2 ⛔ NEGATÍV, KIMERÍTŐ: a kapcsolónak nincs OLVASÓJA

Három, egymástól független pásztázás, mindegyik a `.text` teljes szakaszán
(fájloffset `4096`, `8646656` bájt), indextől függetlenül:

| pásztázás | mit keresett | találat |
|---|---|---|
| a | `disp32 = 0x174` MINDEN utasításalakban (a közvetlen operandusúakat is beleértve) | 24 — egy sem olvasó ebben az osztályban; a `0x0085850e` az egyetlen, ami ide tartozik, és ÍRÓ |
| b | `disp32 = 0x3e0` | 45 — a tartományban csak `0x00850405` és `0x00851ba7`, **mindkettő ÍRÓ** |
| c | `disp32 = 0x128` (a `+0x15c` második bázisra vetített alak: `0x174 − 0x15c + 0x110`… illetve a `this2+0x18` eltolás) | 6 — egy sem az osztályban |

Ezen felül a **teljes osztály-törzs** (`0x00857d00`–`0x0085a2d0`, ~8,7 KB)
utasításonként átnézve: bájt-hozzáférés csak a `+0x4`, `+0x8`, `+0xc`, `+0xd`,
`+0x68` eltolásokra van — `+0x174`-re és a rövidített `+0x18` alakra **egy sem**.

⇒ **Az „Automatikus kitöltés" menütételnek HÁROM írója és NULLA olvasója van**
(a `ComposeDialog+0x5b8` párját is beleértve, aminek egyetlen olvasója a pipa
kirakása és a kapcsoló saját invertálása). A Picasa 3.9.141.259-ben a kapcsoló
**eltárolja a beállítást és átállítja a pipát — de a javaslómotor soha nem
kérdezi meg.** Bizalmi fok: **megerősített** (kimerítő negatív pásztázás,
tartománnyal és mintával megnevezve).

### 24.3 A javaslatlista a memóriában

| mező | szerep | bizonyíték |
|---|---|---|
| `+0x160` | a javaslattömb adatmutatója | `0x00858d00` `mov ecx, [ecx + 0x160]` |
| `+0x164` | **elemszám × 2** | `0x00858cc0` `mov edx, [ecx+0x164]` → `0x00858cca` `shr edx, 1` |
| elem-lépésköz | **24 bájt** | `0x00858d06` `lea eax, [eax + eax*2]` → `0x00858d0d` `lea ecx, [ecx + eax*8]` |
| `+0x168` / `+0x16c` | a **letöltött** névjegyek tömbje (adat / méret\|birtoklás-bit) | a `0x00857d00` ezekbe másol |

A `0x00858cb0` az `i`. javaslat szövegét adja vissza; tartományon kívüli
indexre üres sztringet (`0x00c7f979`) és `−1`-et (`0x00858cb9`).

### 24.4 HONNAN jönnek a címek — két forrás, mindkettő mérve

**(1) Online — a Google Contacts adatfolyam.** A letöltést az
`INotifyContactsDownload` egyetlen metódusa veszi át: **`0x00857d00`**
(a `0x00cc3070` vtábla egyetlen rekesze), és a thunk a
`0x00857d0d` `lea esi, [ebx - 0x15c]` sorral igazítja vissza a `this`-t.
A lekérdezés címe:

```
%sm8/feeds/contacts/%s/full?max-results=10000     (0x0078fe50)
```

⇒ GData `m8` névjegy-adatfolyam, **egy menetben legfeljebb 10 000** névjegy.
A névjegykezelő felülete: `/c/ui/ContactManager` (`0x0085a1a0`), a felirata
`Google Contacts` / `ContactManagerDlg::GoogleContacts` (`0x0085a120`).

**(2) Helyben — a `.picasa.ini` `[Contacts2]` szakasza.** Az író `0x00586e20`,
az olvasó `0x00587110`; az utóbbi hívója a `0x0045a9d0`, aminek egyetlen
sztringje `.picasa.ini`.

### 24.5 A `[Contacts2]` érték PONTOS formátuma

| | mérve |
|---|---|
| szekció | `Contacts2` (`0x00c9105c`) |
| kulcs | a névjegy 64 bites azonosítója, `%I64x` (`0x00c82fcc`) |
| érték | `%s;%s;%s` (`0x00c91104`), az elválasztó `;` (`0x00c81320`) |
| a három mező | **`full_name` ; `email` ; `gaia_id`** |
| **kötelezően három token** | `0x00587203` `and eax, 0xfffffffe` → `0x00587206` `cmp eax, 6` a (token×2) alakon ⇒ token = **3** |
| ha nem három | a bejegyzés **eldobódik**: *„Cannot restore .ini entry for contact, %llx, unexpected number of tokens in string."* (`0x00587110`) |

A mezőnevek és a sorrend nem a naplószövegből következtetés: az író
(`0x00586e20`) a `%s;%s;%s`-t a `0x0058705d`–`0x00587060` sorokon
`push edi; push esi; push eax` sorrendben tölti fel, és ugyanezek a
regiszterek mennek a `Persisting contact to INI: %s, contact ID="%llx",
Full Name="%s", email="%s", gaia_id="%s"` naplóformátumba (`0x00c910a8`,
a hívás `0x00586f9d`–`0x00586fb1`) `FullName = eax-forrás`,
`email = esi`, `gaia_id = edi` megfeleltetéssel — ugyanabból a két
kiolvasó blokkból (`[esp+0x34]`, illetve `[esp+0x1c]`).

### 24.6 MIT ADUNK MA — mérve

| | eredeti | nálunk (mérve) | teendő |
|---|---|---|---|
| `[Contacts2]` írása | `full_name;email;gaia_id` | `f"{name};;"` — **három token, egyezik** (`src/picasapy/ini/contacts.py:53`) | — |
| a két extra mező jelentése | `email`, `gaia_id` | névtelen `extra: tuple[str, ...]` (`contacts.py:20`) | nevesíteni |
| token-szám ellenőrzése | **pontosan 3, különben eldobja** | `name, *extra = value.split(";")` — **bármennyit elfogad** (`contacts.py:28`) | a hármas szabályt átvenni |
| a nyers mezők megőrzése | — | `extra` nyersen megmarad ⇒ round-trip biztonságos | — |
| online névjegy-letöltés | GData `m8` adatfolyam | **nincs** (online funkció, hatókörön kívül) | — |
| az „Automatikus kitöltés" kapcsoló hatása | **semmi** — nincs olvasója | halott helyfoglaló | a kapcsoló épüljön meg (#1526), de **ne kapuzzon semmit** |

⇒ **A #1526-hoz tartozó fontos negatívum:** ne írjunk olyan megvalósítást,
amelyben a kapcsoló kikapcsolása letiltja a javaslatokat vagy a gyűjtést — az
eredetiben nem tesz semmi ilyet. A hűséges megfelelő: pipás menütétel, ami a
beállítást tárolja, alapból bekapcsolva.

Jegyek: **#2524** (ez a szakasz), **#1526** (a kapcsoló megépítése),
**#2526** (a `[Contacts2]` mezőnevek és a hármas token-szabály nálunk).

## ⛳ `ID_MOVE_DATABASE` — az adatbázis áthelyezése, a kilenc pont szerint (2026-09-12, 295. kör, #1402)

A #1402 azt kérte, hogy a **működés** legyen feltárva, a módszertan
sorrendjében. A válasz nagy része a **`.fen` párbeszédleírókból és a
szövegtárból** jött — dekompiláció nélkül.

### 1. MI AKTIVÁLJA

Az **Eszközök** menü `ID_MOVE_DATABASE` tétele; magyar felirata
**„Adatbázis helyének kiválasztása…"**. A parancs a `0x00600983`-on nyitja
a párbeszédet (`push 0xc94e40` = `move_database`, majd a `.fen`-megnyitó
`0x009a5540`).

⚠️ **Nem mértem ki**, hogy van-e más belépési pontja (gyorsbillentyű,
helyi menü) — a `move_database` névre a `.text`-en **egyetlen** hivatkozás
van, de ez a névre szól, nem a parancsazonosítóra.

### 2. MIT INDÍT EL — `move_database.fen`

| vezérlő | név | mit ad |
|---|---|---|
| útvonal-mező (csak olvasás) | `current_location` | a **mostani** hely |
| útvonal-mező, 25 em | `new_location` | az **új** hely (a fókusz is ezen indul) |
| gomb | `changeloc` | „Browse…" |
| gomb | `defaultloc` | „Default" — az alapértelmezett helyre állít |
| elfogadó gomb | `move` | **„Move on next restart"** |
| mégse | — | „Cancel" |

A párbeszéd **két figyelmeztetést** ír ki:

> „You will need to restart Picasa for the changes to take effect."
>
> „Please Note: You should backup your database before trying out this
> **experimental** feature. **NEVER** move the database to a network,
> removable, or external drive, or you may lose data."

⇒ maga a Picasa **kísérletinek** nevezi, és kimondja a hálózati/cserélhető/
külső meghajtó tilalmát.

### 3–4. MIT ÍR és MIKOR

Az elfogadó gomb felirata és a figyelmeztetés együtt dönt: a művelet **a
KÖVETKEZŐ INDÍTÁSKOR** fut le, nem az OK-ra. A párbeszéd tehát csak
**szándékot rögzít**.

✅ **LEZÁRVA (2026-09-19, #3413): a szándék a `Preferences` blokk
`AppLocalDataPathCopy` kulcsában áll** — a részletek a lap „A `MoveDatabase`
két kulcsa" szakaszában. ⛔ A korábbi „nincs sztring a `MoveDatabase`-re"
megállapítás **téves volt**: a név létezik, csak összetett diagnosztikai
címkék belsejében (`MoveDatabase::Success` stb.), ezért a szótöredékre
keresés nem találta meg.

### 5. MI TÖRTÉNIK A MEGLÉVŐ ADATTAL — KÉT mappa, és LOMTÁR

A hibaüzenetek nevezik meg, mi mozog:

| üzenet-kulcs | angol | magyar |
|---|---|---|
| `MoveDatabase::MoveDbFailed` | Picasa failed to send old **database** to the trash. | A Picasa nem tudta a kukába helyezni a régi adatbázist. |
| `MoveDatabase::MoveAlbumsFailed` | Picasa failed to send old **albums folder** to the trash. | A Picasa nem tudta a kukába helyezni a régi albumok mappáját. |

⇒ **két külön dolog** költözik (az adatbázis és az **albumok mappája**), és
a régi példány **a Lomtárba** kerül — nem törlődik véglegesen.

### 6. MI FUT LE UTÁNA

A tényleges másolás alatt a **`moving_database.fen`** folyamatjelző
párbeszéd látszik („Picasa is moving the database.", `progress` sáv). A
burkolója a **`0x00404c30`** (`push 0xc7eb48` = `moving_database`,
`push 0xc85fdc` = `progress`). Siker esetén
`MoveDatabase::Success` — „A Picasa-adatbázis áthelyezése sikerült."

### 7. HIBAESETEK — a bináris mind a hármat megnevezi

| kulcs | mikor |
|---|---|
| `MoveDatabase::LocalDriveOnly` | a cél nem **írható helyi merevlemez** — „No changes will be made" |
| `MoveDatabase::Failure` | a másolás elbukott — „make sure the destination is **empty** and try again" |
| `MoveDbFailed` / `MoveAlbumsFailed` | a régi példányt nem sikerült a Lomtárba tenni |

⇒ a cél-könyvtárnak **üresnek** kell lennie, és a meghajtó-ellenőrzés
**megelőzi** a műveletet (nem részleges állapotot hagy).

### 8. HONNAN JÖN INDULÁSKOR

⛳ **MEGVAN (2026-09-15, 308. kör).** A szándék a **`Preferences`**
tárolóban, az **`AppLocalDataPathCopy`** kulcs alatt áll — az élő útvonal
neve `AppLocalDataPath`, a szándéké ugyanaz `Copy` utótaggal.

A kulcsnévre a teljes `.text`-ben **pontosan két** kódbeli hivatkozás van
(indextől független pásztázás; kontroll: az `AppLocalDataPath`-ra **hét**):

| cím | szerep |
|---|---|
| `0x007d1936` | az **ÍRÓ** — a párbeszéd „Move on next restart" ága |
| `0x00404d97` | az **OLVASÓ** — az indulási kód |

Mindkét helyen ugyanaz a két push áll: `0xc7eafc` = `Preferences`,
`0xc7eef0` = `AppLocalDataPathCopy`, majd a tároló-elérés
(`call 0x00407630`).

**Az író oldala** (`0x007d1900`): a `MoveDatabase::LocalDriveOnly`
ellenőrzés UGYANEBBEN a függvényben van, tehát a **meghajtó-vizsgálat
megelőzi a kulcs beírását** — a `0x007d1952 call 0x00407760` az értékadás.

**Az olvasó oldala** (`0x00404d60`-tól): `0x00404db5 call 0x00407b50` →
`test al, al` → `je 0x00405161`, azaz **ha a kulcs nincs beállítva, az
indulás átugorja** az egész áthelyezést. Ha be van állítva, ugyanez a
függvény hozza fel a `moving_database` folyamatjelzőt (`0x00404c30`), és a
végén **az élő `AppLocalDataPath` kulcsot írja át** az új útvonalra
(`0x00404fd3` / `0x00405007` az elérés, `0x00405025` az írás).

⇒ A 295. kör következtetése („a `0x00404c30` indulási kód, a szándék-tároló
olvasója vele egy hívóláncban lesz") **igazolódott**: a kettő **ugyanaz a
függvény**.

⛔ **Amit nem mértem:** hogy a sikeres áthelyezés **törli-e** az
`AppLocalDataPathCopy` kulcsot. A vizsgált `0x00404df0`–`0x00405170`
ablakban nincs rá törlés-hívás; ha nem törlődik, az „egyszer fut le"
garanciát az adja, hogy a két kulcs egyenlővé válik — ez **nincs
igazolva**.

#### Nálunk (2026-09-17, #3214)

A séma átvéve, ugyanezzel a két lépéssel:

| lépés | nálunk |
|---|---|
| a szándék | `data-location-pending.txt` a konfig-mappában (`app/data_location.py`) |
| az író | `RelocateController.startRelocate` — a cél ELLENŐRZÉSE után, fájlmozgás nélkül |
| az olvasó + a költöztető | `app/startup_relocate.py`, a tárhely-előkészítés ELŐTT hívva (`application.py`) |
| a haladásjelző | `qml/StartupRelocateWindow.qml` (a `moving_database.fen` megfelelője) |
| az élő útvonal átírása | `write_data_root`, az integritás-ellenőrzés után (`on_verified`) |

⚠️ A szándék TÖRLÉSE — amit a bináris nem árult el — nálunk **saját,
kimondott döntés**: sikeres ÉS sikertelen költözés után is elfogy. Ok: egy
elérhetetlenné vált cél különben minden indulást megfogna, és a felhasználó
a saját gépén nem tudná megkerülni. A hiba nem vész el: az indulás kiírja,
a program pedig a RÉGI helyről indul tovább.

### 9. Geometria

A `.fen` `width="fit"`, a `new_location` mező `25em`; a többi a
`.fen`-szerkezetből adódik. Ikon nincs.

### A jegy CÍMÉNEK három állítása — mind IGAZOLT

| állítás | forrás |
|---|---|
| „két mappa" | `MoveDbFailed` + `MoveAlbumsFailed` |
| „Lomtár" | mindkét üzenet „send … to the **trash**" |
| „csak helyi írható lemez" | `MoveDatabase::LocalDriveOnly` |

### Nyitott kérdések mérlege (295. → 308.)

`0 nyílt · 9 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva"`

A 295. kör egyetlen nyílt kérdése — **hol tárolódik az áthelyezési szándék**
— a 308. körben lezárult: `Preferences\AppLocalDataPathCopy`, író
`0x007d1936`, olvasó `0x00404d97`.

*Forrás: `research/copy_Picasa_3_7/Picasa3/runtime/move_database.fen` és
`moving_database.fen`; `referencia/stringres-en-hu.tsv:2038–2042` és
`:2707`; a binárisban `0x00600983`, `0x00404c30`–`0x00404c4d`.*

## ⛳ A `printoptions` TIZENEGY kulcsának ALAPÉRTÉKE — binárisból, két független forrásból (2026-09-16, 316. kör, #1780)

*A 39. tétel kimondta, hogy a numerikus alapértékek „nincsenek mérve", és
hogy ésszerű értéket választani szabad. ⛔ Ez a kutatói kör alapszabályába
ütközik (*becsült érték soha*), ezért ez a szakasz kiméri őket.*

### A módszer és a kontrollja

A beállítás-olvasó (`0x00407a20`) **alapértéke a hívás előtti veremrekeszben**
áll (a módszert a 311. kör igazolta). A tizenegy kulcsot **két külön
függvény** is végigolvassa:

| függvény | méret | a nulla forrása |
|---|---:|---|
| `0x0085f3a0` | 1010 b | `xor ebp, ebp` (`0x0085f3ba`) |
| `0x0085f7a0` | 1230 b | `xor ebx, ebx` (`0x0085f7c3`) |

⭐ **A két függvény ugyanazokat az alapértékeket adja** — ez a mérés belső
kontrollja. A külső kontroll a `textfont`: a 39. tétel szerint `Arial`, és a
módszer pontosan azt adja vissza (ld. lent).

### A tizenegy alapérték

| kulcs | alapérték | a kiolvasás helye (`0x0085f7a0`) |
|---|---:|---|
| `printoptions::text` | **0** | `0x0085f8c7` |
| `printoptions::textplacement` | **0** | `0x0085f8fa` |
| `printoptions::textfont` | **`"Arial"`** | `0x0085f9db` (sztring-ág) |
| `printoptions::textsize` | **12** (`0xc`) | `0x0085f963` |
| `printoptions::textcolor` | **0** | `0x0085f994` |
| `printoptions::wrap` | **0** | `0x0085f927` |
| `printoptions::border` | **0** | `0x0085f7b2` |
| `printoptions::bordersize` | **10** (`0xa`) | `0x0085f7f0` |
| `printoptions::bordercolor` | **0** | `0x0085f827` |
| `printoptions::borderedge` | **0** | `0x0085f85a` |
| `printoptions::evenborder` | **1** | `0x0085f88d` |

⇒ Az **egyetlen bekapcsolt** alapértelmezés az `evenborder` (egyenletes
szélességű szegély); szegély és felirat alapból **nincs**.

**A `textfont` külön úton megy:** nem a `0x00407a20` számos olvasója viszi,
hanem a sztring-változat (`0x00407630`), és az alapértelmezett nevet egy
`.rdata`-beli sztringből építi: `0x00c80a64` = **`"Arial"`**
(`0x0085f9c6 push 0xc80a64`). Ez egyben a mérés külső kontrollja: a 39. tétel
ugyanezt mondja, más forrásból.

### A felirat-forrás enum NÉGY értékű — a fogyasztó is ezt mutatja

A nyomtatási rajzoló (`0x00776180`) a `printoptions::text` kiolvasott értékét
a **0**, az **1** és a **3** ellen hasonlítja (`0x007761cc cmp esi, 1`,
`0x007761d2 cmp esi, 3`, `0x007761d8 cmp esi, ebx`) ⇒ az érték legalább
négyállású, ami egybevág a 39. tétel **négytagú** rádiócsoportjával
(`usenotext` · `usecaption` · `usefilename` · `useexif`).

### Ami NYITVA marad

1. **Melyik enum-érték melyik rádiótaghoz tartozik.** A fenti három
   összehasonlítás a számosságot igazolja, a hozzárendelést nem. Út: a
   `0x0085e800` író névre illesztő elágazásai (a vezérlő elemneve → a beírt
   szám), pl. a `0x0085ebc3` (`text`) körüli ág.
2. **A két szín-kulcs kódolása** (`textcolor`, `bordercolor`): a fogyasztóban
   `0x0077625d` és `0x00776527` környékén `0x80`/`0xff` maszkolás áll — a
   csatorna-sorrend ebből olvasható ki.
3. **A `bordersize` egysége** (képpont, ezredhüvelyk vagy pont): a fogyasztó
   szorzója dönti el.

⚠️ Ezekre **nem adok becsült értéket**; a megvalósítás a fenti alapértékeket
veheti át, a hozzárendelést pedig a fenti utak zárják le.

*Forrás: `0x0085f3a0` és `0x0085f7a0` (a tizenegy `GetPreference`-hívás
alapérték-operandusa), `0x00407630` + `0x00c80a64` (a betűtípus),
`0x00776180` (a fogyasztó összehasonlításai). A kulcsnevek címei:
`0x00cb3d14`, `0x00cb3d28`, `0x00cb3d40`, `0x00cb3d5c`, `0x00cb3d78`,
`0x00cb3d94`, `0x00cb3db0`, `0x00cb3dc4`, `0x00cb3de0`, `0x00cb3df8`,
`0x00cb3e10`.*

## ⛳ A `printoptions` két rádiócsoportjának SZÁMKÓDJAI — kiolvasva (2026-09-17, 317. kör, #1780)

*A 316. kör három kérdést hagyott nyitva. Ez a szakasz az elsőt — a
legfontosabbat — lezárja, a másik kettőt pedig ÉLESEBB úttal adja tovább.*

### 1. A felirat FORRÁSA (`printoptions::text`)

Az OK/Alkalmaz kezelője (`0x0085e800`) elemnévre illeszt, és a találati ágon
konstanst tesz a kiírandó értékbe:

| érték | vezérlő (teljes elemnév) | a magyar felirat (39. tétel) | hol |
|---:|---|---|---|
| **0** | `printoptions/usenotext` (`0x00cc38b0`) | „Nincs szöveg" | `0x0085ebc1 xor esi, esi` |
| **1** | `printoptions/usecaption` (`0x00cc38c8`) | „Képfeliratok" | `0x0085ec3a mov esi, 1` |
| **2** | `printoptions/usefilename` (`0x00cc38e0`) | *(fájlnév)* | `0x0085ec73 mov esi, 2` |
| **3** | `printoptions/useexif` (`0x00cc38fc`) | „Exif-adatok" | `0x0085ecaf mov esi, 3` |

⭐ Ez **független megerősítése** a 316. kör melléklelének: a fogyasztó
(`0x00776180`) épp a **0**, **1** és **3** ellen mér — a `2` azért hiányzik
onnan, mert a fájlnév-ág máshol dől el, de a készlet négyes.

### 2. A felirat HELYE (`printoptions::textplacement`)

| érték | vezérlő | felirat | hol |
|---:|---|---|---|
| **0** | `printoptions/textbelowimage` (`0x00cc3914`) | „A kép alatt" | `0x0085eceb xor esi, esi` |
| **1** | `printoptions/textonimage` (`0x00cc3930`) | „A képen" | `0x0085ed4a mov esi, 1` |
| **2** | `printoptions/textonborder` (`0x00cc394c`) | „A szegélyen" | `0x0085ed83 mov esi, 2` |

⇒ A 316. kör alapértékei ezzel **jelentést kapnak**: `text` = 0 → *nincs
felirat*, `textplacement` = 0 → *a kép alatt*.

### Kontroll: a jelölőnégyzetek NEM konstanst írnak

A `printoptions/border_checkbox` ágában (`0x0085ea07`) nincs
`mov esi, <konstans>`: a kód a vezérlő állapotát kérdezi le
(`0x0085ea38 call 0x009cd9a0`, majd `movsx eax, al`), és azt írja ki. ⇒ a
módszer **megkülönbözteti** a rádió-konstanst a logikai vezérlőtől — ha
mindenhová konstanst látna bele, ez a kontroll megbukott volna.

### Melléklelet: két eddig nem szereplő elemnév

A vezérlő-készlet blokkjában a hét rádiótag és a négy jelölőnégyzet közt
még két név áll, hivatkozásokkal:

| elemnév | hivatkozás |
|---|---|
| `printborderslider/scaleslider` (`0x00cc3968`) | `0x0085e601`, `0x0085e631` |
| `printoptions/border_options` (`0x00cc3988`) | `0x0085e664` |

⇒ a szegélyvastagság **csúszka** (a 39. tétel „Méret" választója), és van egy
`border_options` gyűjtő is.

### 3. A színkódolás — LEZÁRVA (2026-09-17, #1780)

A `printoptions::textcolor` és `printoptions::bordercolor` értéke egyetlen
32 bites, **`0xAARRGGBB` alakú** dword. A bizonyíték két független lépésből áll:

1. A `CPrintOptionsDialog` színírója (`0x0085f2b0`) a négy bemeneti bájtot
   változtatás nélkül, `b3 << 24 | b2 << 16 | b1 << 8 | b0` alakban csomagolja;
   ugyanaz az ág írja a `textcolor`-t (`0x0085f31d`–`0x0085f32b`) és a
   `bordercolor`-t (`0x0085f346`–`0x0085f368`). Nincs csatornacsere vagy
   szorzás.
2. A rajzoló `textcolor`-fogyasztója (`0x008623c0`) a beállítás-objektum
   `+0x74` mezőjét változtatás nélkül továbbadja (`0x008629b1`–`0x008629c8`)
   a `0x009a9a70` képpuffer-segédnek. A segéd minden képpontnál a felső
   bájtot megőrzi (`and 0xff000000`), az alsó 24 bitet pedig közvetlenül
   beírja (`or edi`, `0x009a9aa1`–`0x009a9aab`). A nyomtatási puffer mért
   bájtsorrendje BGRA, ezért a tárolt dword numerikusan `0xAARRGGBB`.

**Implementációs jelentés:** a PicasaPy-nek a két preferenciaértéket dwordként,
`0xAARRGGBB` numerikus alakban kell tartania; a Qt- vagy platformszínobjektum
bemeneti alakját ezen a határon explicit módon erre kell konvertálni. A
csatornasorrend most már nem nyitott kérdés.

### 4. A `bordersize` egysége és skálája — LEZÁRVA (2026-09-17, #1780)

A `bordersize` nem képpont-, DPI- vagy pontérték: a panel egy normalizált
csúszkájának **0…1024-es egész skálára kvantált** beállítása.

- Betöltéskor a tárolt dword (`CPrintOptionsDialog +0x278`) lebegőpontosan
  `0,0009765625`-tel, azaz `1/1024`-gyel szorzódik
  (`0x0085dc30`–`0x0085dc53`, konstans `0x00cf3f68`). Az eredmény a
  `printborderslider/scaleslider` vezérlőbe kerül a `0x009ddc90` segéden át.
- Mentéskor a csúszka lebegőpontos értékét a `0x009ddd00` olvassa ki
  (`0x009ddd23`–`0x009ddd2f`), majd `1024,0`-gyel szorozza
  (`0x0085e659`–`0x0085e663`, konstans `0x00cf4218`) és csonkoló `fistp`-vel
  egész dwordként írja vissza (`0x0085e668`–`0x0085e682`).
- A két konstans értéke a bináris `.rdata`-jából közvetlenül kiolvasva:
  `0x00cf3f68 = 0,0009765625`, `0x00cf4218 = 1024,0`.
- A csúszka nullája kikapcsolja a szegély-opciókat (`0x0085e682`–
  `0x0085e6b9`), de a korábbi tárolt `bordersize` érték megmarad; betöltéskor
  ezért a `border` logikai állapot és a vastagság külön kezelendő.

Az alapérték **10**, tehát a tárolt skálaérték `10/1024`; a tárolt értéket
nem szabad közvetlen képpontként vagy fizikai nyomtatási egységként kezelni.

*Forrás: a panel-frissítő `0x0085d550`, a panel-esemény/mentési ág
`0x0085df30`, a slider getter/setter `0x009ddd00`/`0x009ddc90`, valamint a
`0x00cf3f68` és `0x00cf4218` `.rdata` konstansok.*


## ⛳ A `MoveDatabase` KÉT kulcsa — a szándék az `AppLocalDataPathCopy`-ban áll (2026-09-19, 334. kör, #3413)

*A 3–4. pont kimondta, hogy a „Move on next restart" párbeszéd csak
szándékot rögzít, és nyitva hagyta, hogy hol. Megvan.*

### A két beállítás-kulcs

| kulcs (a `Preferences` blokkban) | sztring címe | szerep |
|---|---|---|
| `AppLocalDataPath` | `0x00c7ef0c` | a **mostani, élő** adatgyökér |
| **`AppLocalDataPathCopy`** | `0x00c7eef0` | a **szándék**: hova kell mozgatni |

Mindkettőt ugyanaz a beállítás-elérő pár olvassa, amit a lap más pontjai is
használnak: `0x00407630` (szekció + kulcs) majd `0x004078e0`.

- a **párbeszéd** (`0x007d14f0`, 444 b — elemnevei `current_location`,
  `new_location`) az `AppLocalDataPath`-ot olvassa ki, és azzal tölti fel a
  „mostani hely" mezőt (`0x007d15c9`–`0x007d15e2`);
- a **végrehajtó** (`0x00404d60`, 1094 b) **először** az
  `AppLocalDataPathCopy`-t kérdezi meg (`0x00404d97`), és a törzs későbbi
  szakaszában kétszer nyúl az `AppLocalDataPath`-hoz (`0x00404fd3`,
  `0x00405007`).

### Hogy tényleg INDULÁSKOR fut

A hívási lánc mindhárom tagjának **egyetlen** indexelt hívója van:

```
0x00401060  →  0x004051b0 (2533 b)  →  0x00404d60 (1094 b)
```

A középső törzs sztringjei azonosítják az indulási utat: `Picasa2NoLaunch`,
`Picasa2Installing`, `SOFTWARE\Google\Picasa\`, `Google\Picasa2`,
`IDS_MIN_RES_MSG`, `IDS_MMX_MSG`. ⇒ a mozgatás **a program indulásakor**
történik, nem az OK-ra — pontosan ahogy a gomb felirata ígéri.

### A végrehajtó saját diagnosztikai címkéi

`MoveDatabase::MoveDbFailed` · `MoveDatabase::MoveAlbumsFailed` ·
`MoveDatabase::Success` · `MoveDatabase::Failure` (címek: `0x00c7ef54`,
`0x00c7efa8`, `0x00c7efec`, `0x00c7f06c`).

⛔ **Helyesbítés:** a 3–4. pont korábbi jelölése szerint a `MoveDatabase`
névre „nincs sztring". A név **megvan** — csak nem önálló tokenként, hanem
ezekben az összetett címkékben. *(Módszertani tanulság: a „nincs sztring"
állítás csak akkor érvényes, ha a keresés részszóra is lefutott.)*

A hozzájuk tartozó, felhasználónak látszó szövegek a régi adatbázis és a
régi albumok mappa **lomtárba** küldéséről beszélnek, valamint a cél
elérhetőségéről — ez független megerősítése az 5. pontnak (KÉT mappa +
lomtár).

### ✅ Az ÍRÓ is megvan (2026-09-20, 335. kör)

Lásd a következő szakaszt: a `0x007d1900` írja a kulcsot, és egy
írható-helyi-lemez ellenőrzés előzi meg.

*Forrás: `0x007d14f0` (444 b), `0x00404d60` (1094 b), `0x004051b0`
(2533 b); a kulcs-sztringek `0x00c7ef0c` és `0x00c7eef0`; a szekció
`Preferences` (`0x00c7eafc`); a hívási lánc a bináris index `xrefs`
táblájából.*


## ⛳ A `Copy` kulcs ÍRÓJA és a lemez-ellenőrzés (2026-09-20, 335. kör, #3413)

*Az előző kör az xref-INDEXRE hivatkozva azt írta, hogy az
`AppLocalDataPathCopy` sztringre egyetlen hivatkozás van. Index-független
pásztázás ezt megjavítja.*

### A) A pásztázás — a sztring CÍME mint 4 bájtos konstans

| sztring | cím | hivatkozási helyek |
|---|---|---|
| `AppLocalDataPathCopy` | `0x00c7eef0` | `0x00404d98` (a végrehajtó **olvasása**) · **`0x007d1937`** (ÚJ) |
| `AppLocalDataPath` | `0x00c7ef0c` | `0x00404fd4`, `0x00405008`, `0x00405457`, `0x004073a9`, `0x00541bb7`, `0x00541d65`, `0x007d15ca` |

⛔ A `0x007d1937`-es helyet az xref-index **nem** kötötte a `Copy` kulcshoz —
ezért állt a lapon, hogy csak egy hivatkozás van. A kontroll teljesült: az
előző körben mért olvasási hely (`0x00404d98`) a pásztázásban is előjött.

### B) Az író: `0x007d1900` (168 b)

```
0x007d1907  call dword ptr [0xc403b4]      ; import (a nevét az index nem oldja fel)
0x007d190d  lea  ebx, [esi + 0xbc]         ; az ÚJ hely szövege (ugyanaz a mező, amit
0x007d1913  push ebx                       ;   a párbeszéd-kezelő is használ)
0x007d1914  call 0x6db040                  ; ellenőrzés → al
0x007d1919  test al, al
0x007d191b  je   0x7d1968                  ; ha HAMIS → hibaág, és NEM ír semmit
…
0x007d191e  push 0xc7f979                  ; üres sztring (a cél objektum kezdőértéke)
0x007d1936  push 0xc7eef0                  ; 'AppLocalDataPathCopy'
0x007d193b  push 0xc7eafc                  ; 'Preferences'
0x007d1948  call 0x407630                  ; szekció + kulcs megnyitása
0x007d1952  call 0x407760                  ; ← ÍRÁS
```

A hibaág a `MoveDatabase::LocalDriveOnly` címkét (`0x00cb8b80`) és a hozzá
tartozó üzenetet használja, amely kimondja, hogy csak **írható helyi
merevlemezre** engedi a mozgatást, és hogy ilyenkor **semmit nem módosít**. Ez
a párbeszéd saját figyelmeztetésének (hálózati/cserélhető/külső meghajtó
tilalma) a **gépi betartatása** — tehát nem csak tanács.

⇒ **`0x006db040`** (1175 b) az „írható helyi lemez-e" ellenőrzés; a
szándék csak akkor kerül a registrybe, ha ez igazat ad.

A `0x007d1900`-nak **nincs indexelt hívója** ⇒ mutatón át hívott
gombkezelő — ugyanaz a minta, mint a párbeszéd többi kezelőjénél.

### C) ⭐ A beállítás-API három függvénye — ezt minden további kör használhatja

| cím | méret | hívók | szerep |
|---|---:|---:|---|
| `0x00407630` | 302 b | 125 | szekció + kulcs **megnyitása** (a két sztring a két argumentum) |
| `0x004078e0` | 307 b | 96 | **olvasás** (ezt használja a párbeszéd és a végrehajtó) |
| **`0x00407760`** | 369 b | 68 | **írás** (ezt használja az OK-ág) |

A hármas ugyanaz minden `Preferences`-kulcsnál; az olvasás és az írás
**kizárólag** a második hívásban tér el. *(Módszertani haszon: egy kulcsnál
mostantól a második hívás címéből egyből látszik, hogy olvasó vagy író
helyet találtunk.)*

### D) Amit a 168 bájt NEM mond meg

Az érték **pontos alakját** (van-e záró `\`, idézőjel, környezeti változó).
A törzs egy üres sztringből (`0x00c7f979`) indul és a `[esi + 0xbc]` mező
tartalmát adja tovább, tehát a formázás — ha van — a mező feltöltésekor
történik, nem itt. Ez a `changeloc`/`defaultloc` kezelőben (`0x007d16b0`,
590 b) olvasható ki; nem becsülöm meg.

*Forrás: index-független bájtpásztázás a `0x00c7eef0` és `0x00c7ef0c`
címekre; `0x007d1900` (168 b), `0x006db040` (1175 b); a beállítás-hármas
`0x00407630` / `0x004078e0` / `0x00407760`, hívószámok a bináris index
`xrefs` táblájából.*
## ⛳ `FolderPhoto::ID_PICTURE_SPLITALBUMHERE` — „Mappa felosztása itt…”: mit csinál az adattal (2026-10-12, #4534)

*Forrás: a mappa-nézet helyi menüjének építője `0x00730790` (a felirat
`0x00730a5e`/`0x00730a63`) · a főablak-diszpécser `0x005cb990` bájttérképe
(`0x005cdb34`) és ugrótáblája (`0x005cd9fc`) · a kezelő `0x005e8570`
(1272 b) · a „Mappa tulajdonságai” párbeszéd (`CEditAlbum`, vtábla
`0x00ca9544`): `0x006dc030`, `0x006db4e0`, `0x008496c0`, `0x00849750`,
`0x00849dc0` · a név- és útképzés `0x009946f0`, `0x00993bb0`, `0x009a3b50`,
`0x009a3db0` · a mozgatás `0x005ea420` → `0x00479870` → `0x00478780` · a
szürkítés `0x0056c5a0` (`0x0056d8f6`–`0x0056d962`) → `0x004ac8f0`.
Mérés (Colab) NINCS: a végrehajtó az áthelyező menüpontot elutasítja
(skill 1/d), ezért minden állítás utasításszintű.*

### 1. A parancsazonosító és a kezelő

A rekordtábla csúszás-szabálya szerint (a rekord kezdete a felirat
`mov dword ptr [REK], eax` címe, a `+0x0a` mezőt a KÖVETKEZŐ blokk írja):

| felirat | rekord (`esp+…`) | cmd | írás helye | ág a diszpécserben | kezelő |
|---|---|---|---|---|---|
| Áthelyezés új mappába… (`FolderPhoto::ID_ALBUM_NEW`) | `0xe8` | **`0x9cb6`** | `0x00730a77` | `0x005cbce0` | `0x005e9bb0` (`push 0`) |
| **Mappa felosztása itt…** (`FolderPhoto::ID_PICTURE_SPLITALBUMHERE`) | `0xfc` | **`0x9ca6`** | `0x00730ac9` | `0x005cbd6d` | **`0x005e8570`** |

**Független kontroll:** (1) a `0x9cb6` ága a `0x005e9bb0`, amit a
`ui-audit-mainwindow.md` a `thumbui/newfolder` akciójaként ismer — tehát a
párosítás nem csúszott el; (2) ugyanaz a táblaolvasás a 34.1 ismert
értékeit adja vissza (`0x9ca2`→`0x005cbd35`, `0x9ca5`→`0x005cbd5f`).
A tétel **csak a mappa-nézet** (`0x00730790`, kontextus `0x70`) menüjében
van; az album-nézet építője (`0x00731050`) nem tartalmazza
(`ui-audit-context-menus.md` D.1).

### 2. A lépéssor — a `0x005e8570` sorrendjében

| # | mit tesz | cím |
|---|---|---|
| 1 | ha a nézetnek nincs aktuális mappa-csomópontja (`[this+0xea8]` = 0) → semmi | `0x005e859b` |
| 2 | köteg kezdete, felület-frissítés elnyomva (`[0xd6793c]`++) | `0x005e85b3`, `0x005e85b8` |
| 3 | a kijelölt elemek listája (`0x005c76b0` → `0x007166c0`: a csomópont elemein **sorban** halad, és a kijelölt, nem elnyomott elemek azonosítóját gyűjti) | `0x005e85d3` |
| 4 | **üres kijelölés → csendes kilépés** (nincs üzenet) | `0x005e862f` |
| 5 | a csomópont **teljes kijelölésének törlése** (`0x00718a50`) | `0x005e8692` |
| 6 | **új kijelölés: a 3. lépés ELSŐ eleme és a lista VÉGE között** — `0x00716ae0(csomópont, első, −1, 1)`; a tartomány azonosítói egy kimeneti tömbbe is kerülnek | `0x005e86d1` |
| 7 | a rács újrarajzolása (`0x00a54b70(this,1,1,0.0,{−1…},1)`) — **a felhasználó a párbeszéd előtt LÁTJA, mely képek mennek át** | `0x005e8702` |
| 8 | üres tartomány → kilépés | `0x005e8707` |
| 9 | a vágópont-kép (a tartomány első eleme) **dátuma** (`0x005c6460` → `0x004edf60` + `0x0098b650`); ha a képrekordnak nincs érvényes dátuma, a függvény `−1`-et ad, és a kezelő **csendben kilép** | `0x005e873c`, `0x005e8753` |
| 10 | új mappa-leíró: név = `IDS_DEFAULT_ALBUM_NAME` (**„Untitled” / „Névtelen”**), dátum = a 9. lépés dátuma (`0x0055ce70`, a név `0x0055cea7`, a dátum `+0x28`) | `0x005e8778` |
| 11 | a JELENLEGI mappa elérési útja (`[this+0xeac]` → album-azonosító `+0x3c0` → `[[db+0x48]]+0x14`), majd annak **szülőmappája** (`0x009a3b50`: a záró `\` levágása után az utolsó `\` előtti rész) | `0x005e87af`, `0x005e87df` |
| 12 | **„Mappa tulajdonságai” párbeszéd** — `0x006dc030(leíró, 0, 1)`; a 2. argumentum `0` a `CEditAlbum+0xcc`-be kerül (`0x008496e1`), és ez választja a címet: `CEditAlbum::folderTitle` = **„Folder Properties” / „Mappa tulajdonságai”** (`0x0084978f`–`0x008497a8`). Mezők az `album.fen` szerint: Név · Dátum (+ „Automatikus dátum”) · Zene · Felvétel helye · Leírás (`picasa-fen-dialogs.md` 3.2). **Mégse → semmi nem jön létre**, a 7. lépés kijelölése viszont megmarad | `0x005e8869`, `0x005e8870` |
| 13 | a mappanév: a párbeszéd Név-mezője a **fájlnév-tisztítón** át (`0x009946f0`, ld. 3.); ha a tisztított név üres, a tartalék a `CThumbUI::albumname` = **„album”** (angolul és magyarul is) | `0x005e88b9`–`0x005e88fb` |
| 14 | **egyedi út a szülőmappában** (`0x00993bb0`, ld. 3.), majd **mappa létrehozása** (`0x009a3db0`); csak siker esetén lesz az út a mozgatás célja | `0x005e891f`, `0x005e892e` |
| 15 | a cél-tároló azonosítójának kikérése (`0x005eb660`); hiba → kilépés | `0x005e896f` |
| 16 | az új mappa felvétele a katalógusba (`0x0055d120(leíró, út, 0, 0)`); hiba → kilépés | `0x005e89b9` |
| 17 | újrarajzolás-jelző (`[[this+0x2c0]+0x166]` = 1, `picasa-konyvtar-eszkoztar-viselkedes.md` 6.5) | `0x005e89df` |
| 18 | **a tartomány minden képének áthelyezése** az új mappába (`0x005ea420`, ld. 4.) — csak ha a 14. lépés mappát hozott létre | `0x005e89f3` |
| 19 | könyvtárnézet-frissítés (`0x0065b840(this,0,0,1)`), majd a `[this+0x2a4]` felület `+0x44` rekesze az új mappa azonosítójával (`1,1,0`) — ugyanez a hívás zárja az „Áthelyezés új mappába…” kezelőjét is (`0x005e9e57`) | `0x005e89fd`, `0x005e8a1b` |

⇒ **A „Mappa felosztása itt…” az „Áthelyezés új mappába…” testvére**: a
kettő ugyanazt a láncot hívja (leíró `0x0055ce70` → párbeszéd `0x006dc030` →
tisztító `0x009946f0` → egyedi út `0x00993bb0` → `0x009a3db0` → `0x005eb660`
→ `0x0055d120` → `0x005ea420`; az utóbbinál a `0x005ea770`-ben,
`0x005ea7c9`–`0x005eaa63`). **Az egyetlen különbség a képkészlet:** a
felosztás nem a kijelölést viszi, hanem **az első kijelölt képtől a mappa
végéig mindent**.

### 3. A név és a hely — pontosan

**Hely: a jelenlegi mappa TESTVÉRE** (a szülőmappájában jön létre, nem
almappaként) — 2. táblázat 11. sor. Az „Áthelyezés új mappába…” ugyanígy
számol (`0x005e9d3d call 0x009a3b50`).

**A név-tisztító `0x009946f0`:**

1. a vezető szóközök kimaradnak; minden szóköz-jellegű karakter és az
   U+3000 egy sima szóközre cserélődik (`0x009947ba`);
2. a 0x20 alatti vezérlőkarakterek és a `\ / : * ? " < > |` halmaz
   (`0x00cd8d24`) **kimarad** (nem cserélődik);
3. az elejéről a `.` és a szóköz, a végéről a szóköz és a `.` levágódik
   (`0x009947d6`–`0x00994820`);
4. ha semmi nem maradt → `−1`, és a kimenet a hívó tartaléka marad
   (itt: „album”);
5. a fenntartott nevek — `aux`, `con`, `nul`, `prn` (`0x00cd8d80`–
   `0x00cd8d8c`, kis-nagybetű-független) — **`_` utótagot** kapnak
   (`0x009949dc`).

**Az egyediesítő `0x00993bb0(szülő, kimenet)`:**

1. ha a szülőmappa nem létezik → `−1` (`0x00993bcc`);
2. az **alapnév** a név, a végéről levágva egy `_<nem nulla egész>`
   utótagot (`0x00986600` utolsó `_`, `atol` ≠ 0 → csonkítás, `0x00993c57`–
   `0x00993c92`);
3. első jelölt: **a név változatlanul**; ha az út létezik, sorban
   `<alap>_1`, `<alap>_2`, … (`"%s_%d"`, `0x00cd8d78`), **legfeljebb
   4095-ig** (`cmp ebx, 0x1000`, `0x00993d19`), utána `−1`.

⇒ Példa: a párbeszédben hagyott „Névtelen” név mellett, ha a szülőben már
van `Névtelen`, az új mappa `Névtelen_1` lesz. **Ütközés miatt nincs
hibaüzenet és nincs újrakérdezés.**

**A mappa saját metaadata** a párbeszédből jön (név, dátum = a vágópont-kép
dátuma, ha a felhasználó nem írta át, hely, leírás, zene). A régi mappa
mappaszintű `[Picasa]` kulcsai **nem** másolódnak át — a kezelő semmilyen
régi-mappa-leírót nem olvas, csak az útját.

### 4. A képek mozgatása és a `.picasa.ini` — `0x005ea420`

1. a cél útja az új album-azonosítóból; üres vagy nem létező → `9`-es hiba
   (`0x005ea4a0`);
2. folyamatjelző: `CThumbUI::MoveProgress` = **„Moving Files” / „Fájlok
   áthelyezése”** (`0x005ea50d`), a darabszám a tartomány hossza;
3. képenként: rekord (`0x004edf60`); ha a forrásfájl nem létezik → átugorja
   (`0x005ea5e5`); a célnév a fájlnév a célmappához fűzve (`0x009a37b0`), az
   egyediesítő (`0x00993030`, `%s%lu` minta) nem nullát ad → átugorja;
   különben **`0x00479870(db, azonosító, 0, 0, folyamat)`** — a 3. argumentum
   `0` = **áthelyezés, nem másolás**;
4. a `0x00479870` csak média-rekordtípust mozgat (`0x00479905`–`0x00479940`:
   2, 3, 6–0x12, 0x15–0x18, 0x1a, 0x1b–0x1d, 0x1f, 0x3e9), és a
   `0x00478780`-at hívja, amely **mindkét mappa `.picasa.ini`-jét megnyitja**
   (`0x0047886b`, `0x004788ee`), a kép szakaszát a forrásból a célba írja
   (`0x0063e5b0`, `0x005ab100`), és — csak az áthelyezés-ágon (`[esp+0x2994]`
   = 0, `0x0047896f`) — a forrás-inin is dolgozik (`0x00478993 call
   0x005aafd0`), ami a szakasz eltávolításának felel meg. Ugyanez a
   függvény hivatkozik a **`.picasaoriginals`** mappára (`0x00479108`) és
   a 8-as és 0x12-es rekordtípusnál a **`.THM`** kísérőfájlra (`0x004789c3`).

⇒ **A kép teljes szakasza (csillag, szerkesztések, arcok, `albums=`
tokenek) a képpel költözik**, az albumtagság tehát megmarad. *(Bizalmi fok:
erős — a két ini megnyitása, a szakaszmásolás és a forrás-törlés hívása
címmel megvan; a mezőszintű másolást nem követtem végig.)*

### 5. Mi NEM mozdul

- **Nem kép fájlok** (szöveg, kísérőfájl, ismeretlen típus): a tartomány
  a mappa-csomópont **elemeiből** áll (`0x00716ae0`), abban csak a katalógus
  elemei vannak — a többi fájl a régi mappában marad. A `.THM` kísérőfájl
  kivétel (4. pont).
- **A régi mappa** a lemezen és a katalógusban is megmarad, akkor is, ha
  kiürült (a kezelőben nincs törlő hívás). Ha a vágópont a mappa ELSŐ képe,
  **minden kép átkerül**, a régi mappa üres lesz — ez ellen nincs őr.
- Elnyomott (`+0x5a`) elemek: a tartomány-mag ezeket **nem szűri** ki a
  kimeneti tömbből (`0x00716bba`–`0x00716bc8`) — hogy a felületen mi számít
  elnyomottnak, ld. a nyitott kérdéseket.

### 6. Megerősítés, szürkítés, visszavonás

- **Külön megerősítő ablak nincs** — a „Mappa tulajdonságai” párbeszéd OK-ja
  maga a jóváhagyás, a Mégse a visszalépés.
- **Szürke**, ha az aktuális mappa egy **iPhoto- vagy Apple Photos-könyvtár**
  `Masters`/`Originals` ágában van: a menü utófeldolgozója a kontextus
  `0x70`/`0x8a` ágán `EnableMenuItem(…, MF_GRAYED)`-et hív (`0x00c40818`
  `USER32!EnableMenuItem`) **három** parancsra egyszerre — `0x9c9a` (Törlés a
  lemezről), `0x9cb6` (Áthelyezés új mappába), `0x9ca6` (Mappa felosztása) —,
  ha a `0x004ac8f0` igazat ad; az utóbbi a mappa útját az
  `iPhoto Library` / `Photos Library` útvonalaihoz méri (`0x0047cea0`,
  `0x0047cfc0` → `0x0099bce0`/`0x0099bf40`, előtag-teszt `0x00987030`).
  Windowson/Linuxon ilyen könyvtár nincs ⇒ **a gyakorlatban mindig aktív**;
  az üres kijelölést nem szürkítés, hanem csendes kilépés kezeli (2./4. sor).
- **Visszavonás nincs**: a programban nincs könyvtár-szintű Visszavonás
  (`eMenuEdit::ID_UNDO` halott bejegyzés, `picasa-menusor-csoportok.md`,
  #1795), és a kezelő sem rögzít visszaállítási adatot. Visszacsinálni csak
  kézi visszamozgatással lehet.

### 7. Eredeti / nálunk / teendő

**Nálunk (mérve, 2026-10-12):** `PhotoContextMenu.qml:316–319` —
`PicasaMenuItem { objectName: "contextMenuSplitFolder"; placeholder: true }`:
szürke helyfoglaló, `onTriggered` nélkül, és **minden** helyi-menü
kontextusban látszik (album- és személy-nézetben is). A `src/` alatt
`splitFolder`/`split_folder` nincs. A testvérparancs nálunk:
`FileOpsController.moveSelectionToNewFolder` (`fileops_controller.py`,
#1614) — csak nevet kér, a célt a kijelölés első képének mappája ALÁ teszi,
ütközésnél hibát ad.

| szempont | eredeti | nálunk | teendő |
|---|---|---|---|
| belépési pont | csak a mappa-nézet képének helyi menüje | helyfoglaló, album-/személy-nézetben is | bekötni; album- és személy-kontextusban elrejteni |
| képkészlet | az első kijelölt képtől (a rács sorrendjében) a mappa végéig, a kijelölt is | — | ugyanígy, a rács aktuális rendezése szerint |
| előnézet | a tartomány a párbeszéd ELŐTT kijelölődik | — | ugyanígy |
| párbeszéd | „Mappa tulajdonságai”: Név „Névtelen”, Dátum = vágópont-kép dátuma, hely, leírás | — | ugyanez a párbeszéd, mappa-címmel |
| hely | a jelenlegi mappa **testvére** | (a testvérparancs: almappa) | testvér |
| név | tisztítás (3.), üresen „album”, ütközésnél `_1`, `_2`… | (a testvérparancs: hiba ütközésnél) | a 3. szabályai |
| ini | a képszakaszok átköltöznek, a forrásból törlődnek | `fileops.move.move_photo` már ezt teszi | a meglévő mozgató útját használni |
| nem kép fájl | marad | — | marad |
| megerősítés / visszavonás | nincs külön / nincs | — | nincs külön / nincs |

### 8. Bizonyítottsági fok

- cmd és kezelő (1.): **megerősített** (két független kontroll).
- a lépéssor, a képkészlet, a testvér-hely, a név- és ütközésszabály, a
  párbeszéd címe (2.–3.): **erős** (utasításszint, minden lépés címmel).
- az ini-átköltözés (4.): **erős** a hívási mintára, **feltételes** a
  mezőszintű részletekre.
- a szürkítés (6.): **erős**.

### 9. Nyitott kérdések mérlege

| kérdés | állapot | a megszerzés útja |
|---|---|---|
| a 9. lépés dátuma EXIF-felvételi idő vagy fájlidő? | **NYITOTT** | a `0x004edf60` kimeneti rekord `+0x04` mezőjének írója; a gyakorlatban a rács dátum-rendezésének kulcsa (69. tétel: `thumbindex` 1. FILETIME) a jelölt |
| az új mappa `.picasa.ini`-jébe a párbeszéd mely mezői kerülnek (`name=`, `date=`, `location=`, `description=`)? | **NYITOTT** | a `0x0055d120` → `0x0055d320` ág követése a `date=%f` íróig (`0x0068ac80`) |
| a `+0x5a` „elnyomott” elem melyik felületi állapot (rejtett kép, szűrő)? | **NYITOTT** | a `+0x5a` írói (`tagkereso.py 0x5a`) |
| a `[this+0x2a4]+0x44` rekesz pontos hatása (az új mappára ugrik-e a nézet) | **NYITOTT** | a `CMultiAlbumNode` második táblájának `+0x44` eleme (`picasa-eger-es-kijeloles.md` 12.1 táblázat bővítése) |
| a `[.album:<token>]` definíciós szakaszok sorsa (ha a régi mappa ini-jében vannak) | **NYITOTT** | a `0x00478780` szakasz-másolójának teljes olvasása |

Mérleg: 5 nyitott · 0 blokkolt · 0 hatókörön kívül. Egyik sem akadálya a
megvalósításnak: a #4534 „Kész, ha” pontjai a 2.–6. szakasz megerősített és
erős állításaira épülnek; a nyitottak a meglévő saját mechanizmusainkkal
(rács-dátum, mappaszintű `[Picasa]` írás, mozgató) helyettesíthetők.

### 10. Amit KIZÁRTAM

- **„A kijelölt kép a RÉGI mappában marad”** — kizárva: a tartomány a
  kijelölt képpel KEZDŐDIK (`0x00716ae0`, `idA` = első kijelölt, és az
  elem a tartomány része).
- **„Fájlnév vagy dátum szerint vág”** — kizárva: a csomópont elemsorrendjén
  halad (`0x007166c0`, `0x00716ae0` a `+0xb4`/`+0xb8` rekeszeken), vagyis a
  rácsban látott sorrend szerint.
- **„Almappát hoz létre”** — kizárva: a cél a szülőmappa alá kerül
  (`0x009a3b50`).
- **„Külön megerősítést kér”** — kizárva: a kezelő egyetlen párbeszéde a
  `CEditAlbum`.

### 11. ⚠️ Melléklelet — két korábbi állítás, amit ez a kör megkérdőjelez

1. **`picasa-konyvtar-eszkoztar-viselkedes.md` 2./6.:** „a gomb egy Névtelen
   albumot hoz létre azonnal, párbeszéd nélkül”. A `0x006dc030` az új
   leírónál (`+0x08` = −1, `0x0055ce7f`) **mindig** felépíti és megnyitja a
   `CEditAlbum` párbeszédet (`0x006dc07d`, `0x006dc09d`, majd a
   párbeszéd-objektum `+0x40` virtuális hívása `0x006dc0d5`), és csak a
   `[esp+0xb0]` = 0 ágon (OK) ad igazat; az `Új album` hívása
   (`…, 1, 0`) a `+0xcc` = 1 ágon az **„Album tulajdonságai”** címet kapja.
   ⇒ az „Új album” is párbeszédet nyit, „Névtelen” előtöltéssel.
2. **„Áthelyezés új mappába…” (#1614):** az eredeti a jelenlegi mappa
   **testvérét** hozza létre a „Mappa tulajdonságai” párbeszéddel és
   `_N`-es ütközéskezeléssel (`0x005e9d3d`, `0x005ea770`); nálunk almappa,
   csak névvel, ütközésnél hiba.

Mindkettő külön jegy tárgya; itt csak a bizonyíték áll.

## ⛳ #5709: Közzététel FTP-n: eredeti út és PicasaPy-eltérések (2026-10-23)

### Következtetés

A Picasa 3.9 binárisban az Eszközök → Kísérleti → Közzététel FTP-n keresztül
parancs végig van kötve: a közös HTML-export párbeszédből FTP-módba lép, mentett
fiókot választ, majd fájlokat tölt fel és távoli fájlokat takarít. A PicasaPy
HTML-exportja helyi weboldalt készít, de FTP-menüpontja, fiókkezelője és
feltöltője nincs. A bináris útja megerősített; a teljes fiókpárbeszéd mezőinek
képernyőn látható neve, a `secure` mező jelentése és a `webUrl` végső felhasználása
nyitva marad.

Vizsgált bináris: a megadott Picasa3.exe PE-verzióadata szerint
FileVersion 3.9.141.259 (mérés: PE FileVersion).

### Eredeti felhasználói út

1. A 0x00559150 menüépítőben a 0x0055c295 környezetében szerepel az
   eMenuTools::ID_FTPWEB kulcs (0x00c8df04), a felirat pedig a
   0x00c8df1c címen áll: Publish via FTP... A menürekord parancsazonosítója
   0x9d54; a Kísérleti almenü első tétele.
2. A 0x005c90a0 regisztrálja a 0x9d54 parancsot. A 0x005cb990 parancságában
   a 0x9d54 eset a 0x005e7490(1) hívásra fut. Ha nincs kijelölt mappa vagy
   album, a 0x005e7490 a „You must select a Folder or Album to export”
   üzenetet adja; egyébként a szokásos webexport.fen párbeszédet nyitja
   (0x007f4be0), és az FTP-jelzőt adja át a callbacknek (0x007f6cc0).
3. A közös webexport párbeszéd tartalmazza a címmezőt, célmappa-választót,
   sablonlistát, leírást és előnézetet, továbbá az öt képméretet és a
   mozgókép-módot. A méret és film mód részletes, címekkel igazolt
   megfeleltetése a lap 6.1. szakaszában van.
4. FTP-módban a 0x007f6d50 callback a 0x005e7370 fiókválasztóhoz lép
   (AMgrSelect). A fiókválasztás/fiókkezelés a 0x005cfff0 környékén kezeli
   a hozzáadást, szerkesztést, törlést és kapcsolat-ellenőrzést. A bináris
   üzenetei többek között: `Please specify a name!`, `This user name already exists!`,
   `You have successfully verified the connection!` és
   `Unable to verify the connection. Please check your settings.`
5. A 0x007f6d50 a kiválasztott profillal a 0x00957630 FTP-szinkronizálót
   indítja. A WinINet-hívások között FtpOpenFileA, InternetWriteFile,
   FtpCreateDirectoryA, FtpSetCurrentDirectoryA, FtpFindFirstFileA,
   FtpDeleteFileA és FtpRemoveDirectoryA szerepel. A státuszszövegek:
   `Initializing connection…`, `Uploading images…` és
   `Cleaning up remote files…`. A feltöltő a webexportból létrehozott helyi
   weboldal fájljait használja; az elavult távoli fájlok törlésének pontos
   feltétele nyitott.

### Beállítások és alapértékek

| Beállítás | Eredeti, a binárisban | PicasaPy |
|---|---|---|
| Képméret | EGYEZIK: 0 = eredeti, 1024, 800, 640, 320; alapérték Preferences\WebExportSize = 3, vagyis 640 px (0x007f5310). | EGYEZIK: ugyanezek a választások és 640 px alapérték; QSettings-kulcs: webexport/size (WebExportController, sizes.py). |
| Mozgókép mód | EGYEZIK: Első képkocka / Teljes mozgófilm; alapérték Preferences\WebExportMovie = 0, vagyis Első képkocka (0x007f5355). | EGYEZIK: ugyanezek a módok és alapérték; QSettings-kulcs: webexport/movieFull. |
| Célmappa | A 0x007f52b0 a Preferences\WebExportPath értéket olvassa és a 0x007f5e80 menti. Hiányzó értéknél a 0x00996230 által feloldott Personal mappához a bináris 0x00cbc7f8 `Picasa HTML Exports` nevet fűzi a 0x007f53a7 útvonalon. | Eltér: a rendszer Képek mappája / „Picasa HTML exportok” az alap (webexport_controller.py); a célmappa nincs QSettings-be mentve, csak a párbeszéd objektumában marad meg. |
| Sablon | A Preferences\WebExportTemplate kulcsot a 0x007f52b0 olvassa és a 0x007f5e80 menti; üres tárolt értéknél a párbeszéd alapindexe 0. | Részben egyezik: az alapindex 0, de a sablonválasztást a PicasaPy nem menti QSettings-be; a templateIndex a párbeszéd kezdeti állapota. |
| Sablon-előnézet | A webexport.fen sablonlistát, leírást és élő előnézetet ír le (a helyi telepítés erőforrása, 1-16. sor). | Sablononkénti leírás és a sablon saját `preview.svg` képe látszik; az előnézet sematikus, élő sablonból renderelt változat nincs (#5909, WebExportDialog.qml). |
| FTP-fiókok | AccountMGR alatt a kulcsok: ftpUser (0x00cb9ecc), ftpPass (0x00cb9ed4), ftpDomain (0x00cb9edc), ftpRoot (0x00cb9ee8), webUrl (0x00cb9ef0), secure (0x00cb9ef8). A hiányzó szövegértékek alapja az üres 0x00c7f979; a secure mező alapértéke 0 (0x007e8340). | NINCS MEG: nincs FTP-fiók- vagy beállítási réteg a src/picasapy alatt. |
| Fióktárolás | A kulcsok olvasása/írása a HKCU beállítási rétegen át történik, AccountMGR névtérrel (0x007e8340, 0x007e89e0, 0x007e8f80; olvasó segéd: 0x00407630). A teljes fizikai registry-útvonal NINCS MEG; megszerzés: a 0x00407630/0x00407ea0 registry-kulcs-összeállításának célzott követése. | NINCS MEG: nincs megfelelő fióktároló. |
| Fiókpárbeszéd pontos mezőcímkéi és elrendezése | NINCS MEG: a helyi runtime FEN-leírók között nincs FTP/AMgr párbeszéd. Megszerzés: Windows alatt az AMgr hozzáadás/szerkesztés párbeszéd megnyitása és a mezők/feliratok rögzítése, vagy az AMgr erőforrás célzott kibontása. | NINCS MEG: nincs megfelelő párbeszéd. |
| Oldalcím induló értéke | NINCS MEG: a webexport.fen edit mezőt mutat, de a futáskor előtöltött szöveget a fájl nem rögzíti. Megszerzés: a webexport párbeszéd megnyitása a Picasa 3.9-ben, kijelölt mappával és albummal. | HTML-módban megnyitáskor a jelenlegi mappa nevére áll (#5909); FTP-módban a párbeszéd korábbi értéke marad. |
| FTP-kiszolgáló és távoli gyökér | ftpDomain és ftpRoot értékek kerülnek a CFtpSync kapcsolat/útvonal-ellenőrzésébe; címek: 0x00958a00 (Verifying Domain…, Verifying root path…) és 0x00967c00 (InternetConnectA). | NINCS MEG: FTP-kapcsolat és távoli útvonalkezelés nincs. |
| FTP-port | Az InternetConnectA hívás 0x00967c35 címen a 0x15 portértéket adja át, azaz 21; a fiókkulcsok között külön portbeállítás nincs. | NINCS MEG: nincs FTP-kapcsolat vagy portbeállítás. |
| webUrl és secure mező jelentése | NINCS MEG: a webUrl végső felhasználása és a secure fiókmező FTP-műveletre gyakorolt hatása nem bizonyított. Megszerzés: az AccountMGR objektummező fogyasztóinak célzott követése a 0x007e81b0 és 0x007f6d50 körül, majd Windowsos fiókpárbeszéd-mérés. | NINCS MEG: ezeknek nincs megfelelője. |
| Kimenet | FTP-módban a helyi HTML-webexport fájljai kerülnek a kiválasztott fiók ftpRoot könyvtárába; az FTP-réteg könyvtárat hozhat létre, fájlt ír és távoli fájlokat takarít (0x00957630; importok a bináris-index imports táblájában). | Eltér: csak a helyi HTML-galéria jön létre; FTP-feltöltés nincs a webexport motorban vagy menüben. |

### Tételes összevetés: Eredeti | Nálunk | Teendő

| Eredeti | Nálunk | Teendő |
|---|---|---|
| **Menüpont és parancs.** 0x00559150 / 0x0055c295; szöveg 0x00c8df1c; parancs 0x9d54; diszpécser 0x005cb990. | PicasaPy-ban nincs FTP-menüelem; a QML-ben csak a kihagyást jelző megjegyzés található. | A termékjegy döntse el és valósítsa meg az FTP-módú menüpont bekötését a meglévő HTML-export párbeszédbe. |
| **Méret és film mód.** Alap: 640 px és Első képkocka; mindkettő megmarad a következő indításra (0x007f5310, 0x007f5355, 0x007f5e80). | EGYEZIK: alapérték és felhasználói választás megőrzése megvan. | Nincs teendő. |
| **Célmappa és sablon megőrzése.** Preferences\WebExportPath és Preferences\WebExportTemplate (0x007f52b0, 0x007f5e80); alapút `Personal/Picasa HTML Exports`. | Célmappa Képek/Picasa HTML exportok; a cél és a sablonválasztás nincs újraindítások között megőrizve. | Külön paritásjegyben állítsa helyre a célmappa- és sablonválasztás megőrzését, és döntse el, hogy az alapútvonal egyezzen-e a Personal/Picasa HTML Exports útvonallal. |
| **FTP-fiók és feltöltés.** AccountMGR 0x00cb9ec0, fiókválasztó 0x005e7370, fiókkezelő 0x005cfff0, CFtpSync 0x00957630; távoli gyökérrel és az InternetConnectA 0x00967c35 címen átadott 21-es porttal. | Nincs fiókkezelő vagy FTP-feltöltés. | Valósítsa meg a fiókválasztás/kezelés és a webexport-fájlok FTP-szinkronizálásának útját. A mezőcímkéket, a secure működését és a webUrl használatát ne következtesse ki a mezőnevekből; előbb zárja le a nyitott bizonyítást. |
| **Élő sablon-előnézet.** A párbeszéd építője 0x007f4be0; mérés: a szállított runtime/webexport.fen 1-16. sora. | #5909 óta sablononként a saját `preview.svg` látszik; ez sematikus, nem a sablonból renderelt élő előnézet. | Ha a teljes élő előnézet is cél, a sablont renderelve kell megjeleníteni. |

### A két független út

**A: utasítás-/hívásút:** a 0x0055c295 menürekordtól a 0x005cb990
0x9d54 ágán át a 0x005e7490(1), 0x007f6cc0, 0x007f6d50, 0x005e7370 és
0x00957630 függvényekig. Ez bizonyítja a menüparancs, a közös párbeszéd,
az account-választó és az FTP-szinkron kapcsolatát.

**B: külön WinINet-/sztringút:** a bináris-index imports táblája a 0x00957630
függvényhez rendeli az FtpDeleteFileA és FtpRemoveDirectoryA importokat; a
CFtpSync állapotüzenetek ugyanott az `init`/`uploading`/`cleanup` lépéseket nevezik
meg. A 0x00967d30 az FtpOpenFileA és InternetWriteFile hívásokat, a 0x00967f70
a FtpCreateDirectoryA hívást, a 0x009680e0 a FtpSetCurrentDirectoryA hívást
tartalmazza. A két út egyezik: ez tényleges feltöltő/szinkronizáló, nem csupán
kapcsolat-ellenőrző párbeszéd.

### Cáfoló kör

1. **Feltevés:** az FTP csak egy elhagyott vagy letiltott menüfelirat. **Cáfolat:**
   az egész .text-en, kizárólag a paszta.memoria_kapu() hívása után végigfuttatott
   pásztázás megtalálta a 0x9d54 kódhivatkozást a 0x005c90dc címen; a meglévő
   Ghidra-kimenet a 0x005cb990 dispatchertől a 0x005e7490(1) hívásig mutat.
   Ezzel a „csak halott felirat” feltevés megdőlt. Ez nem bizonyítja a menü
   minden futásállapotában látható/engedélyezett voltát.
2. **Feltevés:** a CFtpSync csak fiók-ellenőrzésre szolgál. **Cáfolat:**
   a 0x007f6d50 az FTP-jelző ágában kiválasztott fiókkal a 0x00957630
   szinkronizálót hívja; ettől független importút igazolja a fájlírást és
   távoli törlést. A két bizonyíték egyezik.

### Nyitott kérdések

- NINCS MEG: a fiókpárbeszéd mezőinek pontos felirata, sorrendje, a jelszó
  maszkolása és az esetleges secure jelölőnégyzet látható neve. Megszerzés:
  Picasa 3.9 Windowsos példányán az AMgr Add/Edit ablak rögzítése vagy a
  kapcsolódó erőforrás célzott kibontása.
- NINCS MEG: a secure profilmező tényleges hatása az FTP-kapcsolatra, illetve
  a webUrl felhasználása feltöltés után. Megszerzés: a profilrekord fogyasztóinak
  célzott visszakövetése a 0x007e81b0/0x007f6d50 útvonalon és kontrollált
  Windows-mérés.
- NINCS MEG: az elavult távoli fájlok törlésének pontos egyezési/törlési
  szabálya. Megszerzés: a 0x00957630 cleanup ág és a 0x00956c70 távoli
  fájllistázó összevetése a 0x00967d30 feltöltővel; ha az adatszerkezet
  diszasszemblálással nem válik egyértelművé, célzott Ghidra-kör.
- NINCS MEG: az eredeti és a PicasaPy webexport-címmezőjének azonos-e az
  induló értéke. Megszerzés: Picasa 3.9-ben külön kijelölt mappával és
  albummal megnyitni a párbeszédet, és rögzíteni a mezőt.

### Bizonyítottsági fok

**Megerősített:** a menüparancs → közös HTML-export → mentett FTP-fiók →
WinINet-feltöltés/takarítás útja két, egymástól független bináris útból
igazolható. **Feltételes:** a teljes, képernyőn látható fiókbeállítások és a
secure/webUrl szemantikája runtime/erőforrás-bizonyíték nélkül nem zárható le.
