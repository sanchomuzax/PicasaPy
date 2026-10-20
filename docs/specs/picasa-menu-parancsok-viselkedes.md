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

Három felirat: `Passport0` = „Nem találhatók arcok", `Passport1` = „Úgy
tűnik, több arc van a képen.", `Passportfail` = „Megpróbálkozik egy másik
képpel?" ~~(kérdés ⇒ igen/nem párbeszéd)~~ ⛔ **HELYESBÍTVE élő méréssel (2026-09-26, picasa-colab-jobs #49/#50):** a `Passportfail` a hibaablak **CÍME** („Try another picture?”); az ablakban hiba-ikon, a `Passport0`/`Passport1` szöveg („Can't find any faces”) és **egyetlen OK gomb** — nem igen/nem kérdés. Belépési pont: **Tools ▸ Experimental ▸ Passport photo…**, a Kísérleti almenü 6. tétele (a kilenc: Publish via FTP… (tiltva) · Show Duplicate Files · Search for ▸ · Save search results… · Show tag as album… · Passport photo… · Delete empty online albums… · Choose database location… · Write faces to XMP…). Jegy: **#1401**.

#### ⭐ A KIVÁGÁS GEOMETRIÁJA — kimérve (2026-09-12, #1401)

A jegy blokkolója az volt, hogy „a kivágási arány külön kérdés". Nem az: a
sikeres ág (`0x00531e50`-től) végig kiolvasható.

**1. Az arc-téglalap képpontra váltása.** A felismerő normalizált (0…1)
téglalapot ad; a kód a `+0x10`/`+0x14`/`+0x18`/`+0x1c` mezőket
(bal · fent · jobb · lent) a kép **szélességével** (bal, jobb) illetve
**magasságával** (fent, lent) szorozza (`0x00531e8a`–`0x00531ec4`). A
`fild` melletti `fadd [0xcf39e4]` a szokásos előjel nélküli javítás
(`0xcf39e4` **float** alakja `4294967296,0` = 2³²), nem geometria.

**2. Kerekítés kifelé.** `bal`-ból és `fent`-ből `−0,5`, `jobb`-hoz és
`lent`-hez `+0,5`, majd `fistp` (`0x00531efa`–`0x00531f5a`; a konstans
`0xc72150` = **0,5**).

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

#### Ami MÉG nincs mérve

Az `ePassport` **fizikai mérete** (mm/hüvelyk) és a lapelrendezés. A
névtábla csak nevet ad; a méretet a nyomtatási rajzoló (`0x00776180`,
1085 b — ugyanaz, ami a #1780 szegély/felirat beállításait fogyasztja)
vagy egy hozzá tartozó mérettábla adja. Ez a következő gépi lépés.

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

**Vagyis az elrejtés adatvédelmi funkció**, nem csak nézeti szűrő.

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
| jelszó | db3 `catdata` `Hidden Folders` sor `info` (hex MD5) | `QSettings` `view/hiddenPasswordHash`; a db3-átvétel (`pmpimport/`) a `catdata`-t nem olvassa |

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

Az `Add to Screensaver` (`0x00531900`) kétszintű:

1. **album-szintű kijelölésnél** megerősítés: `addtosaver::warning` —
   „Are you sure you want to add all of the selected album's images?";
2. a hozzáadás motorja (`0x00531a20`) — **minden állapot megnevezve:**

| elem | bizonyíték |
|---|---|
| tagság tokenje | `]screensaver` belső token (írás/törlés `0x531a3d`/`0x531a88`) — az ini-korpuszban `screensaver=` sor **nincs**: a tagság nem a `.picasa.ini`-ben él |
| a képernyővédő listája | **`saverlist.txt`** a **`#db3\`** mappában (`0x531a8d`–`0x531a93`) — ugyanott, ahol az adatbázis |
| telepítve van-e | `Software\Google\Google Photos Screensaver` → `AppPath` (registry, `0x531ae2`–`0x531aec`) |
| nincs telepítve | `CThumbUI::InstallScreensaver` → **`rundll32.exe desk.cpl,InstallScreenSaver %s`** (`ShellExecute`, „open" ige — `0x531bcf`–`0x531c0f`); hiba: `CImageOutput::noscr` = „A képernyővédő nem lett telepítve." |
| folyamat | `CImageOutput::scrprog` = „Hozzáadás a képernyővédőhöz" |
| konfigurálás | `Configure Screensaver` (`0x00531ac0`): ugyanabból a registryből indítja a képernyővédő beállítóját |

A Google Fotók-képernyővédő **külön telepítésű program** (#453) — a
`desk.cpl`-hívás Windows-specifikus. Jegy: **#453**, **#32**.

**Linuxos PicasaPy-változat (#4259, tulajdonosi döntés 2026-10-05):** a
Windowsos telepítés- és registry-út helyett a menüből nyitható saját
képernyővédő-beállító és előnézet készült. A források a kijelölt mappák,
albumok és a Létrehozás menüből hozzáadott képek; a beállításokat a QSettings
őrzi. Az effekt-, diaidő- és feliratbeállítás a helyi teljes képernyős
diavetítéshez tartozik. A vetítés egérmozgásra vagy billentyűre kilép.
Asztali környezeti tétlenségjelhez kötött automatikus indítás nincs benne; ez
külön integrációs feladat. A korábbi specifikáció az eredeti külön Windowsos
kiegészítő teljes beállítómezőit nem sorolta fel, ezért ez a Linuxos felület a
jegyen kért helyi forrásokra és a PicasaPy diavetítési beállításaira épül.

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
Nyitott kérdések: 0 nyílt · 5 lezárva · 0 blokkolt · 2 hatókörön kívül-javaslat · 0 csak-nyitva
```

- **LEZÁRVA** (mind címmel): a poszter papírméret-listája és nyelvi
  feltétele (35.2); a képernyővédő három állapothordozója (35.3); a
  TiVo-akció kerete (35.4); a 1000-es küszöb és gombfelirat (35.5); a
  mentés két állapothordozója (35.6).
- **HATÓKÖRÖN KÍVÜL-JAVASLAT** (tulajdonosi döntést kér): a TiVo-export
  megvalósítása; az operációs rendszer tétlenségi jeléhez kötött automatikus
  képernyővédő-indítás és az eredeti `desk.cpl` telepítőút átvétele.

### Amit KIZÁRTAM

- **„A screensaver-tagság a `.picasa.ini`-ben él"** — megdőlt: a
  `]screensaver` token a korpuszban nem jelenik meg kulcsként; a lista a
  `#db3\saverlist.txt`-ben él.
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

### 38.1 ⭐ „Rejtett képek" — a bekapcsolás JELSZÓT AJÁNL

Az állapot a `Preferences\ShowHidden` kulcsban él; az olvasó/író
`0x005c9300` (a `Preferences` ág, `ShowHidden` kulcs az egyetlen két
sztringje), amit a fő parancskezelő (`0x005cb990`) hív.

**Ami eddig sehol nem szerepelt nálunk:** ugyanez a parancskezelő
**kétszer** hívja a `0x005ee2a0`-t is, és az egy párbeszédet tesz fel, ha
a „Rejtett mappák" gyűjtemény **nincs jelszóval védve**:

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

⇒ **A „Rejtett képek megjelenítése" nem puszta szűrő-kapcsoló: a Picasa
az első bekapcsoláskor felajánlja a gyűjtemény jelszavas védelmét, és a
„ne kérdezd többet" választ külön kulcsban őrzi.**

*(Bizonyítottsági fok: **megerősített** a párbeszéd léte, szövegei,
gombjai és a két registry-kulcs; **feltételes** az, hogy pontosan a
BEkapcsoláskor kérdez — a `0x005cb990` két hívóhelye a be- és a kikapcsoló
ág is lehet. A gombfeliratok iránya („Add Password") viszont a
bekapcsolás felé mutat.)*

### 38.2 Idővonal — egy közös „bemutató-mód" kezelő

A `0x9ccc` a binárisban nem jelenik meg közvetlen összehasonlításban
(ugrótáblás ág), a viselkedés viszont a `0x005e8a70`-ből olvasható. Ez a
függvény **három bemutató-módot** kezel egy helyen:

| mód | sztringek |
|---|---|
| **Idővonal** | `CThumbUI::MakeTimeline` · **„Preparing timeline…"** |
| Flipbook | `CThumbUI::MakeFlip` · „Preparing flipbook…" |
| Nagy diavetítés | `BigSlideshow2` |

Közös őre az `IDS_MUST_SELECT`, és a függvény a `thumbui/fullview`,
`editpanel/preview`, `editpanel/only_1up_toggle`, `oneup/back`
csomópontokat is kezeli — vagyis a **teljes képernyős** útra vált át. A
`thumbui/timelinebutton` név szerinti parancsága is megvan a közös
`0x005d9cc0` diszpécserben (`0x005da7ab–0x005da7ae`), de a
`thumbui.tre:472–478` ugyanennek a főablaki elemnek `m_hidden`-t és az
eltávolítási blokkot adja. ⇒ Ez **akció-belépési pont**, nem bizonyíték arra,
hogy a kiadott főablakban látható Idővonal-gombnak kell lennie.

⇒ **Az Idővonal parancs egy előkészítő szöveget használó, `oneup` bemutató-útvonalat indít; nem a mai PicasaPy év/hónap-rács útvonala.** A teljes képernyős jelleg az útvonalból és a hozzá tartozó `oneup`/overlay erőforrásokból következik, a futó ablak tényleges megjelenése itt nincs megmérve.

#### 38.2.1 Az Időrend bemutató-útja és bizonyított határai (#4443 kutatás)

**A út — utasításszintű olvasat.** A billentyűkezelő `0x005e6279` ága
ellenőrzi a `0x005696c0` őrt, majd `1` argumentummal hívja a
`0x005e8a70`-et; a `Ctrl+5` menürekordja a `0x9ccc` parancsra mutat
(`picasa-gyorsbillentyuk.md` 10.6). A `thumbui/timelinebutton` diszpécserága
(`0x005da767–0x005da7ae`) ugyanezt a kezelőt hívja. A függvényben megtalálható
a Picture Tray hibaüzenete („You must have images in the Picture Tray to do
this.”), de a szöveg jelenléte önmagában nem azonosítja a Timeline bemenetét:
a függvény több bemutatóágat kezel.

Az Időrend ág `0x005e942e`-nél a `CThumbUI+0x2c0` mező által mutatott
gyűjteménytől kér elemszámot
(`0x004a0980`), majd `0`-tól a kapott elemszámig indexelve meghívja a
`CThumbUI` vtable `+0x90` metódusát (`0x005e9490–0x005e94f1`). Ez a metódus
`0x00562cc0`-n keresztül a `CThumbUI+0x2bc` szolgáltató `+0x20` virtuális
metódusának adja át az indexet. Ez bizonyítja az indexelt bemeneti sorozat
bejárását; a szolgáltató konkrét típusa, hogy az aktuális mappa/album, teljes
könyvtár vagy Picture Tray adatait adja-e, továbbá a bejárás előtti dátum-
rendezés és a képernyőn mutatott kártyák **NINCS MEG**.

`0x005e943d–0x005e944d` a `CThumbUI::MakeTimeline` és a „Preparing
timeline…” szöveget adja át a `0x009ae560` helpernek. A helper diszasszemblálása
nem azonosít megjelenítő- vagy folyamatjelző-vezérlőt: **a szöveg bizonyított,
a tényleges folyamatjelző NINCS MEG**. A bemutató-út később meghívja a
`0x008037e0`-et, amely a `oneup/timeline` és `oneup/transtype` csomópontokat
kéri le, majd a `0x007fb210` overlay-felépítőt. Utóbbi a
`overlays/left`, `right`, `mouse`, `rollovermouse`, `exit`, `timeline`,
`timelinedot`, `sliderthumb`, `startbutton` és `overlay` nevű rétegeket tölti
be. A `oneup/timeline` gomb `0x008032e0` kattintási ága meghívja a
`0x007fda00`-et; az állapotváltás időforrást kér, a `0x00802230` átmeneti
frissítőt indítja, és állapotjelzőket állít. Az átmenet pontos képi tartalma,
végpontjai és időtartama **NINCS MEG**.

Az `oneup/prev` és `oneup/next` kattintási ág a `0x00802980`/`0x008029f0`
képlista-indexet lépteti. A OneUpUI eseménykezelő `0x00803180` kezeli a
`0x20a` egérgörgő-eseményt előző/következő ismételt hívásokkal, illetve a
`0x319` esemény 1-es alparancsát ugyanarra a kilépési visszahívási útra küldi,
mint az `oneup/exit` gombot. A `WM_KEYDOWN` (`0x100`) és `WM_KEYUP` (`0x101`)
eseményhez ez a virtuális metódus nem rendel külön műveletet; az örökölt
`0x00a52890` kezelő tartományellenőrzése is a közös kilépő ágra küldi őket. Ez
csak a OneUpUI és örökölt eseményút olvasata: a főablak globális gyorsbillentyűi
és a tényleges, futó módbeli billentyűviselkedés külön futtatási próbát igényel.

Az `oneup/exit` kattintás a `0x008032e0`-ben a OneUpUI vtable `+0x24`
metódusával elkéri a `this+0x50` objektumot, majd annak vtable `+0x14`
metódusát hívja két nulla argumentummal. A visszahívás konkrét célobjektuma
és az utána látható nézet **NINCS MEG**; a statikus híváslánc nem bizonyítja,
hogy a kilépés pontosan melyik képernyőre tér vissza.

**B út — független `respack.yt`-erőforrás-leltár.** A helyi Picasa 3.7
telepítés `runtime/respack.yt` csomagjából kinyert teljes `oneup.tre` minden
elrendezési csomópontja csoportonként: kép/alap (`oneup`, `bicubiccontainer`,
`back`, `stripback`, `centergroup`, `caption`, `dtclip`); kilépés
(`exit_icon`, `bcklabel`, `bcklabel_base`, `exit`); Időrend (`timeline_icon`,
`tllabel`, `tllabel_base`, `timeline`); lapozás/lejátszás (`prev`, `next`,
`auto`, `auto_icon`, `auto2`); forgatás/csillag (`rotateleft`, `rotateright`,
`star`); átmenet/felirat (`transtype`, `caption_icon`, `caption_yesicon`,
`captionbutton`); kijelzési idő (`plusone_icon`, `plusone`, `minusone_icon`,
`minusone`, `tps`, `tpslabel`). A `prev`/`next` `mousedown` eseményre, a
kijelzési idő `plusone`/`minusone` gombjai automatikus ismétlésre vannak
állítva. A `oneuptext.tre` mindössze három feliratot ad meg: `Timeline`,
`Exit`, `Display Time`. Ebben a két elrendezésforrásban nincs mappanév-,
albumnév-, dátumkártya- vagy dátumfelirat-definíció; ez nem zárja ki a kódban
dinamikusan felépített tartalmat.

A csomag `overlays` rétegei között van egy vékony, vízszintes
`overlays/timeline` vonal (`0x00248b99`, forrás-rect
`(197,461,442,468)`, `245×7`), egy világos
`overlays/#timelinedot` pontgrafika (`0x0024898b`, `(215,459,222,470)`,
`7×11`), egy kék `overlays/timelinedot` pontgrafika (`0x00248a97`,
`(215,462,222,470)`, `7×8`), valamint egy kerek `sliderthumb`-grafika
(`0x00248be7`, `(260,457,285,480)`, `25×23`).
A háttérréteg forrás-rectje `0x002152fb`-nél `(0,0,640,480)`. Itt két
külön erőforrásról van szó: a `oneup/timeline` a `Timeline` gomb, az
`overlays/timeline` az alsó vízszintes vonal grafikája. Ezek a
640×480-as erőforrásvászon koordinátái; a `0x007fb210` kód az overlayek
x-koordinátáját futáskor skálázza. A képek igazolják a sávot és a két pont-
grafikát, de az erőforrásnevek és a rajzolat nem bizonyítják, hogy a sáv mit
időzít, vagy hogy a fogantyú húzással mit állít.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `0x005e8a70` indexelt szolgáltatói sorozatot jár be, majd a `0x008037e0` → `0x007fb210` oneup/overlay bemutatóútba lép. A teljes tartalom, forráshalmaz, dátumsorrend és kártyák **NINCS MEG**. | A `TimelineView.qml` év-/hónap-rács. A Nézet ▸ Időrend menüpont és `Ctrl+5` tiltott; a `timelineRequested` jelzésnek nincs bekötése, aktív eszköztárgomb nincs. | A rácsot ne tekintsük az eredeti bemutató megfelelőjének. A képek és sorrend implementációja előtt a szolgáltató típusát, a bemeneti halmazt és a dátum-/kártyamodellt kell azonosítani. |
| Az `oneup.tre` képnéző-, Exit/Timeline-, prev/next, automatikus lejátszás-, forgatás-, csillag-, átmenet-, felirat- és kijelzési idő vezérlőket sorol fel. Az overlay-rétegek között sáv, két pontgrafika és fogantyú van; a fogantyú szemantikus művelete **NINCS MEG**. | A jelenlegi rácsban nincs oneup bemutató-vezérlősáv vagy ilyen overlay. | A bizonyított vezérlők megjelenítése specifikálható; a timeline sáv tartalmát, a `sliderthumb` műveletét és a dátumkártyákat csak célzott kódkövetés vagy eredeti futtatási próba után szabad bekötni. |
| A `0x008032e0` a `timeline`, `exit`, `prev`, `next` gombokat kezeli. `0x00803180` a görgőt navigációra, az `0x319/1` eseményt az Exit útjára küldi; a sima `WM_KEYDOWN/UP`-hoz a OneUpUI út nem rendel műveletet. Az Exit konkrét visszatérési célja **NINCS MEG**. | A menü és a `Ctrl+5` tiltott; futó bemutató és teszt nincs. | A billentyűmátrixot eredeti futtatásban kell próbálni; az Exit célját a `this+0x50` objektum dinamikus típusának és callbackjének követésével kell igazolni. |
| A `thumbui/timelinebutton` akciónév létezik, de a csomagolt `thumbui.tre` rejtettnek jelöli (`m_hidden`); a súgó „Timeline view of all your photos”. | Nincs aktív főablaki Időrend-eszköztárgomb. | Az eredeti főablaki gomb láthatóságát ne következtessük ki a parancs létezéséből; ehhez futó Picasa-képernyőkép kell. |

**Cáfoló kísérlet.** Megpróbáltam cáfolni azt az értelmezést, hogy a `timeline`
sáv és a `sliderthumb` együtt fotó-/dátum-kereső csúszkát alkot. A teljes
`oneup.tre`/`oneuptext.tre` leltárban nincs hozzájuk esemény- vagy értékkötés;
a `0x007fb210` a rétegeket tölti be és az x-koordinátákat skálázza, míg
a vizsgált `0x00803180`/`0x008032e0` eseményutak azonosíthatóan a görgőt és a
megnevezett oneup-gombokat kezelik. Ez nem cáfolja, hogy közös alaposztályban
vagy másik függvényben van húzáskezelés, ezért a fogantyú funkciója nyitva
maradt. A korábbi „csak év/hónap-rács” magyarázatot a két független út
(`0x005e8a70`→oneup/overlay és az önálló erőforrás-leltár) cáfolja; ez viszont
nem dönti el a bemutató képkockáinak tartalmát.

**Bizonyítottsági fok: feltételes.** Az utasításolvasat és a `respack.yt`
leltár egyezik abban, hogy az Időrend egyedi oneup bemutatóút saját gombokkal
és alsó overlay-grafikákkal. A képi tartalom/rendezés, a sáv és fogantyú
viselkedése, a módbeli billentyűk és az Exit célja nem zárható le e két úttal.
Minden fent megadott cím, fájloffset, rect és méret bináris rekordból vagy
utasításból származik; becsült érték nincs. A `CTransTimeline` név a
film-/People Albums másik hívási láncában szerepel
(`picasa-create-features.md` 2038–2138); itt nem használtam Időrend-bizonyítékként.

**Nyitott — következő pontos lépés:**

- `Ghidra-kör kell: 0x005e8a70 — az indexelt szolgáltató konkrét típusa és forráshalmaza (mappa/album, teljes könyvtár vagy Picture Tray), a dátum szerinti rendezés, valamint a megjelenő dátum-/mappakártyák építése. [blokkoló]`
- `Ghidra-kör kell: 0x00a52890 — az örökölt UI-eseménykezelő hogyan irányítja a OneUpUI egérle/fel/mozgatás eseményeit; a sliderthumb réteghez vezet-e húzásos hit-test vagy értékkötés. [blokkoló]`
- `Ghidra-kör kell: 0x005e60d0 — a globális billentyűkezelő mely gyorsbillentyűi maradnak aktívak a OneUpUI megjelenésekor, és van-e külön billentyűút az Exithez vagy a lapozáshoz. [blokkoló]`
- `Ghidra-kör kell: 0x008032e0 — az oneup/exit által elért this+0x50 objektum konkrét típusa, a vtable +0x14 callback célja és a visszatérési nézet. [blokkoló]`
- `Ghidra-kör kell: 0x007fda00 — a Timeline gomb átmenetének tényleges vizuális tartalma, kezdő/végállapota és időzítése. [blokkoló]`
- A tényleges kártyakép, Timeline sáv állapota, a billentyűk és Exit célja: **NINCS MEG**. A statikus kör után az eredeti Picasa futó módjában célzott billentyű-/húzáspróba és képernyőkép kell; QEMU-harness csak akkor használható, ha a Picasa felületet ezen a képen megjeleníti és az inputot továbbítja.

#### 38.2.2 Futás közbeni megfigyelés, job-102 (#4443)

**Forrás:** a `job-102` 14 képernyőképe és `allapot.json`-ja (a mérőmappa nincs a repóban). Eredeti Picasa 3.9, 1280×1024, mappa: „PicasaTeszt" (24 kép, mappadátum 2026. október 6.). A felvétel lépéssora: az 1. kép után Ctrl+5, 8 mp várakozás, Right, Right, Left (3-3 mp), Space (6 mp), Escape (4 mp); minden lépés után egy kép.

**Módszer:** PIL-lel dolgoztam. A 01-02 kockát `ImageOps.autocontrast`-tal világosítottam. A 03-14 kockák legvilágosabb képpontja 8-9 a 255-ből, ezért a 03. és a 14. kockát fix, 32-szeres szorzóval is megnéztem (a `.meres-102/vilagos/` alá mentve). A kockák közötti eltérést pixelenként számoltam.

**Kockák:**

| kocka | mit mutat | eltérés az előzőhöz |
|---|---|---|
| 01 | főrács, 24 bélyeg; a bal panelen „Scanning, 71% complete" | - |
| 02 | a főrács ugyanaz; a bal panelen „Unnamed (6)" | 32 116 képpont. A bal panel változott; a rácsban is van eltérés (26 125 képpont), ennek okát nem azonosítottam. |
| 03 | fekete, teljes képernyős ablak (`qshow`): az Időrend-bemutató | a teljes kocka |
| 04-14 | a 03-mal pixelre azonos (fájlméretük is azonos: 10 017 bájt) | 0 képpont |

**A bemutató elrendezése (03. kocka, képpontban, a teljes kockán):**

- Cím: „PicasaTeszt", jobbra igazítva, `x 743-850`, `y 384-403`.
- Dátum: „October 2026", jobbra igazítva, nap nélkül, `x 762-849`, `y 417-431`.
- Bal oldali elforgatott bélyeg-halom, a cím alatt, balra; pontozott ív köti a címhez. A határait külön nem mértem le.
- Jobb oldali bélyeg: `x 797-870`, `y 583-666`. A szerepe nem ismert.
- Vezérlősáv: 4 gomb és egy csúszka.
  - Bal szélső: rács-vissza ikon, `x 348-391`, `y 676-704`.
  - Előző (bal nyíl): `x 569-596`, `y 677-705`.
  - Indító (kép és nyíl ikon): `x 619-662`, `y 676-704`.
  - Következő (jobb nyíl): a mért határoló téglalap `x 684-730`, `y 660-705`; a gomb valódi jobb szélét a szomszédos elemtől nem választottam el.
  - Csúszka: sáv `x 525-770`, `y 729-746`. A fogantyút a képről látom, `x` kb. 591-606, `y` kb. 729-745 körül; külön nem mértem.

**Sötétség:** a 03-14 kockák legvilágosabb képpontja (8, 8, 9) a 255-ből. Minden elem (cím, bélyegek, gombok, csúszka) csak a szorzott változatban látszik, az átlagfényesség 0,04 a 255-ből. A kockák között nincs változás, ezért az animáció időbeli lefutása ebből nem látszik.

**Billentyűk:**

- Egy billentyű hatása nem olvasható ki. A 03. kocka után 11 egyforma kocka van, a lépések (7 művelet) és a kockák (14) száma nem egyezik, az `allapot.json` pedig nem tartalmaz lépésfeliratot, így a kockák nem köthetők billentyűhöz.
- Escape: az utolsó (14.) kockán a `windows` listában még ott van a `qshow`. Ha az utolsó kocka az Escape után készült, az Escape nem zárta be az ablakot. A kockákból nem derül ki, hogy így volt-e, ezért ezt nem állítom.
- Aktív ablak: a 01-14 kockák mindegyikén `active.title` = „Picasa 3", a `qshow` megjelenése után is. A fókusz a főablakon maradt. Ez összhangban van azzal, hogy a billentyűk nem a bemutatóhoz érkeztek, de a kockák ezt nem bizonyítják.

**Nyitott, a következő mérés dönti el:**

1. A sötétség oka: beúszó vagy ragadt animáció (ekkor időben változna), Wine-renderelés, vagy rögzítési hiba.
2. Melyik billentyű mit csinál. Ehhez a `qshow` ablak fókuszát kell igazolni.
3. Bezárja-e az Escape a bemutatót.
4. Több mappánál mi történik (sorrend, cím, dátum). A felvétel egyetlen mappát mutat.
5. A jobb bélyeg és a fogantyú szerepe, a bal halom pontos határai.

### Eredeti | Nálunk | Teendő

| Eredeti (mért) | Nálunk (forrásból) | Teendő |
|---|---|---|
| Ctrl+5 külön, fekete `qshow` ablakot nyit; a 03. kockán az Időrend-bemutató látszik. | `Main.qml:1723-1727`: a `Ctrl+5` gyorsbillentyű `enabled: false` (1725. sor); a `toggleTimeline()` (`Main.qml:1687`) csak ebből hívódik. A menütétel (`PicasaMenuBar.qml:1160-1163`) szintén tiltott, a `timelineRequested` jelzésnek a QML-ben nincs fogadója. | A billentyű és a menü jelenleg semmit nem nyit. A bemutató megépítése után a bekötést újra kell tervezni. |
| Cím „PicasaTeszt" és „October 2026" (hónap és év, nap nélkül), jobbra igazítva. | `TimelineView.qml`: a fejléc „Timeline" felirat; a korszak-fejléc `címke (darab)` alakú. | Eltérő megjelenés és tartalom. A bemutató címe a mappanév és a dátum; nálunk nincs ilyen. |
| Bal bélyeg-halom (elforgatott), jobb bélyeg, pontozott ív. | Nincs: a `TimelineView` lapos GridView-rács. | A halmok szerepe, darabszáma és forgatása nem mért. |
| Vezérlősáv: rács-vissza, előző, indító, következő gomb; csúszka. | Nincs vezérlősáv. A `TimelineView` egy bezáró gombot (`timelineCloseButton`) és az Escape-et ismeri (`TimelineView.qml:32`). Az `onClosed` jelzés (`Main.qml:3082`) a rácsra visszaviszi a nézetet. | A gombok műveletei nem mértek; az Exit célja sem ismert. |
| Billentyűk: Right, Right, Left, Space, Escape. Egy billentyű hatása nem olvasható ki. | A `TimelineView` csak az Escape-et kezeli (`Keys.onEscapePressed`), nyíl- és szóköz-kezelés nincs. | A mérés előtt nem állítható, hogy a nyilak lapoznának. Ld. a következő mérést. |
| 03-14 kockák: sötét (átlag 0,04), változatlan. | Nincs bemutató-animáció. | Nyitott (ld. fent, 1. pont). |

**Következő mérés** (a fenti 1-5. pontot dönti el). Az A és a B a `PicasaTeszt` mintakészletet használja; a C-hez egy második mappa kell.

**A - időbeli sorozat és billentyűk.** Ctrl+5 után 1 mp-es sorozat (minden `var:1` után egy kép), majd kattintás a fekete háttér alsó részére a fókuszhoz, utána a billentyűk az eredeti sorrendben, végül Escape.

```json
[
  {"picasa": "indit"},
  {"var_ablak": "Picasa", "mp": 60},
  {"kattint": [340, 437]},
  {"var": 2},
  {"billentyu": "ctrl+5"},
  {"var_ablak": "qshow", "mp": 10},
  {"var": 1}, {"var": 1}, {"var": 1}, {"var": 1}, {"var": 1},
  {"var": 1}, {"var": 1}, {"var": 1}, {"var": 1}, {"var": 1},
  {"kattint": [640, 950]},
  {"var": 1},
  {"billentyu": "Right"}, {"var": 3},
  {"billentyu": "Right"}, {"var": 3},
  {"billentyu": "Left"}, {"var": 3},
  {"billentyu": "space"}, {"var": 6},
  {"billentyu": "Escape"}, {"var": 4}
]
```

**B - kontroll a sötétségre.** Ugyanaz az A-lépéssor, de `ctrl+4` (Slideshow) a `ctrl+5` helyett, és a sorozat után Escape. Ha a Slideshow kockái világosak, a sötétség a Timeline-hoz köthető. Ha ők is sötétek, a rögzítés vagy a Wine-renderelés a gyanús.

**C - több mappa.** Mintakészlet: a `PicasaTeszt` mellé egy második mappa más hónapból (javaslat: 2025. június, 5 kép). Lépéssor: `picasa indít`, `var_ablak Picasa 60`, `billentyu ctrl+5`, `var_ablak qshow 10`, `var 8`, `billentyu Escape`, `var 4`. Ebből látszik, melyik mappák jelennek meg, milyen sorrendben, és van-e dátumkártya.

Megjegyzés a végrehajtóhoz: a fenti `var` egysége (mp) és a `kattint` koordinátái (1280×1024) a végrehajtó kódjából ellenőrizendők a futtatás előtt; a kockák egyeztetéséhez a lépés sorszámát a végrehajtó naplójában rögzíteni kell. A `var_ablak` a `qshow` címét várja, a pontos ablakcímet az első kísérlet `allapot.json`-ja adja meg.

#### 38.2.3 Futó felmérés az eredeti Picasán (Colab #102) — mit mutat a bemutató (#4443)

**Horgony:** a mai megfelelő nézet `src/picasapy/app/qml/PicasaPy/TimelineView.qml:1`; a menüparancs `ID_VIEW_TIMELINE` (`0x9ccc`, 38.2).

**Forrás:** eredeti angol Picasa 3.9.141, Wine, 1280×1024; futás 2026-10-06 22:33 UTC. A `job-102` 14 képernyőképe és `allapot.json`-ja egy „PicasaTeszt” mappát (24 kép, október 6-i mappadátum) és egy `Recently Updated (24)` albumot tartalmaz. A koordináták a `kepernyo__03.png` képpontjaiból származnak; ez a fájl és az `allapot.json` nem található meg a helyi mérőadat-archívumban, az eredmények a korábbi kutatási ágból vannak átvéve.

| Eredeti (mért) | Nálunk (forrásból ellenőrizve) | Teendő |
|---|---|---|
| A `Ctrl+5` külön, teljes képernyős, fekete `qshow` ablakot nyit. A tartalom középre tett 640×480-as mezőben jelenik meg. | A `TimelineView.qml` az alkalmazásablakon belüli év/hónap-rács; a Nézet ▸ Időrend és a `Ctrl+5` inaktív. | A rács nem felel meg ennek a bemutató-módnak. |
| A mappanév („PicasaTeszt”, `x 743–849, y 384–405`) és a hónap/év („October 2026”, `x 759–849, y 414–430`) jobbra igazított, nap nélkül. | A rács csoportfejléce `2026. szeptember (1)` alakú. | A bemutató elemének címe a mappanév, alatta a mappadátum hónapja és éve. |
| A felirat alatti bal képhalom (`x 694–776, y 585–679`) enyhén elforgatott képekből áll; 10 pontból álló ív köti össze a felirattal (`x 740–843, y 452–564`). A jobb oldali halom (`x 796–869, y 583–665`) szerepe **NINCS MEG**. | Lapos bélyegképrács van, halom és pontozott ív nincs. | A halmok darabszámát, forgatását, ívét és a jobb halom szerepét nem szabad megbecsülni. |
| Az alsó vezérlők sorrendje: kilépés (`x 348–390, y 676–703`), előző (`x 569–595, y 677–704`), indítás (`x 619–661, y 676–703`), következő (`x 684–719, y 668–704`). | A bemutató vezérlősávja nincs meg. | A gombok megjelenése bizonyított; műveletük és visszatérési céljuk nem. |
| Az időskála vonala 245×7 px (`x 525–769, y 733–739`), a forrásgrafika 25×23 px; a látható fogantyú képpontjai `x 591–606, y 729–745`. A sáv 1:1-ben rajzolódik, a vászon `y=272` eltolásával. | Nincs időskála. | A vonal és fogantyú megjelenése bizonyított; húzásuk, a pontok jelentése és a skálavég-feliratok nem. |
| A 3–14. képkocka bájtra azonos és nagyon sötét (legvilágosabb RGB=9). | Nincs bemutató-animáció. | E felvétel nem bizonyít beúszást vagy más animációt; az animációt és időzítését külön kell mérni. |
| A `Right`, `Left`, `Space` és `Escape` próbák nem változtatták meg a képet, de az aktív ablak végig a `Picasa 3` maradt. | A bemutató billentyűviselkedése nincs tesztelve. | Ez a billentyűpróba fókuszhiba miatt érvénytelen; a módbeli billentyűk nyitottak. |
| A `thumbui/timelinebutton` parancság létezik, de a csomagolt `thumbui.tre` elrejti (`m_hidden`). | Nincs látható főablaki Időrend-eszköztárgomb. | A jegy eszköztárgombot kér, de az eredeti kiadott felületen való láthatóságára nincs bizonyíték; az eredeti erőforrás alapján ne adjunk hozzá látható gombot. |

**Bizonyítottság:** a `qshow` bemutatóablak, a felirat, a két halom és a pontozott ív, a négy gomb, valamint a sáv képi elrendezése méréssel igazolt. A `Right`/`Left`/`Space`/`Escape` eredménye érvénytelen fókusz miatt. A képkockák változatlansága nem zárja ki, hogy a felvétel az animáció előtt vagy egy Wine-korlát miatt készült.

**Nyitott, implementációt blokkoló kérdések:** a bemeneti mappák/albumok halmaza és időrendje; a kártyák teljes tartalma, a jobb halom és az időskála jelentése; a gombok műveletei és az Exit célja; a billentyűk; az animáció és a „Preparing timeline…” tényleges folyamatjelzője. A folytatáshoz a `qshow` ablakra fókuszált eredeti futtatási próba kell; eltérő dátumú második mappával a lapozás és a jobb halom is vizsgálható.

#### 38.2.4 Helyi statikus újraolvasás: qshow, vezérlők és nyitott szemantika (#4443, 2026-10-16)

Ez a kör az eredeti bináris utasításait és a helyi Picasa 3.7 telepítés
`runtime/respack.yt` erőforrásait olvassa össze. A Colab/Wine futás az első
qshow képkockán megállt, ezért abból billentyű-, kattintás-, csúszka- vagy
animációs viselkedést nem veszek át. A qemu-harness izolált függvények kézzel épített állapotú
futtatására való, nem Win32 ablak és billentyűfókusz tesztelésére; a qshow
interakciós útvonalhoz nem alkalmas.

**A qshow ablak útja.** A `CThumbUI::MakeTimeline` (`0x005e8a70`) a
`0x008037e0` bemutató-felépítőt hívja; ez létrehozza a `qshow` nevű ablakobjektumot
(`0x008038e7`, `0x00982bf0`) és meghívja az overlay-felépítőt
(`0x008039cc`, `0x007fb210`). A qshow megjelenítésekor a `0x0080398f` a
`0x00983fc0`-nak látható állapotot és `7` jelzőt ad. A helper a GWL_STYLE
mezőbe `0x96080000` értéket ír (`0x0098407e-0x0098408b`), majd a
`SetWindowPos` hívásban `HWND_TOPMOST` beszúrási pozíciót használ
(`0x009841d4-0x009841d7`). Ez keret nélküli, legfelül tartott bemutatóablak
útját bizonyítja. A `0x007fa730` a képernyő méreteit a `GetSystemMetrics`
segítségével kéri le, és a `0x280 × 0x1e0` logikai vászonméretet is beállítja
(`0x007fa73c-0x007fa767`). A képernyőn ténylegesen elfoglalt terület a
futásidejű geometria és módjelző függvénye; a helyi futás ezt nem mérte meg.

**Két, egymástól külön kezelt Időrend-elem.** A `oneup/timeline` a
`oneup.tre` gombja, felirata „Timeline”, és a `0x008032e0` kattintási ága a
`0x007fda00` állapotváltót hívja. Az `overlays/timeline` ezzel szemben az
alsó skála vonalának képe; mellette külön `timelinedot` és `sliderthumb`
rétegek vannak. A `0x007fb210` ezeket a grafikai rétegeket tölti be és
skálázza. A rétegnevek és a rajzolat nem adják meg, hogy a skála mappát,
albumot, hónapot vagy képet választ-e.

**A négy overlay-grafika.** A csomag rekordjai a következő forrás-recteket
adják meg:

| réteg | forrás-rect | mit mutat a grafika | bináris rekord |
|---|---:|---|---:|
| `overlays/exit` | `(8,404,51,432)` | bélyegkép/rács jellegű ikon és balra mutató nyíl | `0x0027ca41` |
| `overlays/left` | `(243,405,274,436)` | balra mutató nyíl | `0x0027da50` |
| `overlays/startbutton` | `(298,404,341,432)` | kép ikon és lejátszásjel | `0x0027f126` |
| `overlays/right` | `(366,405,397,436)` | jobbra mutató nyíl | `0x0027e5d4` |
| `overlays/timeline` | `(197,461,442,468)` | vízszintes skálavonal | `0x00248b99` |
| `overlays/sliderthumb` | `(260,457,285,480)` | kerek fogantyú | `0x00248be7` |

Ezek a csomag képpont-koordinátái, nem futásidejű ablakkoordináták. A
`overlays/exit`, `left`, `startbutton`, `right` sorrend a grafikák sorrendje;
a kattintási célokhoz való kötésük **NINCS MEG**. A `oneup/prev`, `next`,
`auto` és `exit` külön parancsnevek, ezért nem állítható, hogy a négy overlay
automatikusan ezeket a gombokat hívja.

**A bizonyított `oneup` parancsok.** A `oneup.tre` a `prev` és `next`
gombra `mousedown` tulajdonságot ad; a `oneup/auto` grafikai rekordja „Auto
Play” feliratú. A `0x008032e0` a `prev`/`next` nevet a
`0x00802980`/`0x008029f0` függvényre irányítja. Ezek a OneUpUI `+0x3f4`
indexét csökkentik/növelik; a következő elem elérésekor a `+0x3ec` listát és
a `+0x3f0` elemszámot használják. Tehát ez a két parancs az aktuális oneup
listában léptet. Hogy a lista eleme egy fotó, egy mappakártya vagy más csoport,
az indexelt szolgáltató típusának hiányában **NINCS MEG**.

A `oneup/auto` és `oneup/auto2` a `0x00803110` kapcsolót hívja. Ez megfordítja
a `+0x3bb` állapotjelzőt a `0x00801130` segéden keresztül, majd az
állapotfüggő frissítési útjára lép.
Ez alátámasztja, hogy a oneup sáv „Auto Play” gombja lejátszást kapcsol; nem
bizonyítja, hogy a külön `overlays/startbutton` ugyanide köt, és azt sem, hogy
a lejátszás egy kiválasztott mappát jár-e be. A `oneup/exit` a OneUpUI
visszahívási láncán lép ki (`0x008032e0`, `0x00803180`), de a visszahívás
célobjektuma és a visszaállított főablaki nézet **NINCS MEG**.

**Görgő és billentyűk.** A OneUpUI eseménykezelő `0x00803180` kezeli a
`0x20a` egérgörgő-eseményt: az iránytól függően a `0x00801210` vagy
`0x008011b0` útjára lép. Az alút a OneUpUI állapotjelzői alapján a
`0x007fd0c0` értékfrissítőt, a `prev`/`next` lapozást vagy az átmeneti
frissítést hívja. Ezért a görgő hatása módfüggő; a Timeline módban végzett
értékfrissítés jelentése **NINCS MEG**. A `0x00803180` nem rendel külön
műveletet az `Up`, `Down`, `Left`, `Right`, `Space`, `Home`, `End` vagy
`Escape` billentyűkódhoz. Az egyéb eseményeket az örökölt `0x00a52890` útjára
adja, így a származtatott kezelő olvasata önmagában nem zárja ki, hogy a
globális vagy az alap UI-út billentyűt kezeljen. A felsorolt billentyűk
qshow-beli hatása **NINCS MEG**.

**Tartalom és animáció.** A `0x005e8a70` a `CThumbUI+0x2c0` kollekciót
bejárja, a `CThumbUI` vtable `+0x90` metódusát hívva. A thunk `0x00562cc0`
a `CThumbUI+0x2bc` szolgáltató vtable `+0x20` metódusának adja át az indexet.
A konstruktor `0x005643e0` e mezőket paraméterből tölti, de a konkrét
szolgáltatótípus és a kollekció eredete nem azonosítható az itt olvasott
hívásláncból. A mappák/albumok halmaza, rendezése, a kártyanév és a dátum
forrása **NINCS MEG**. A „Preparing timeline…” karakterlánc a
`0x00c978f0` címen van; tényleges folyamatjelző-vezérlő nem azonosítható.
Az Időrend-váltás `0x007fda00` állapotváltót és `0x00802230` frissítőt hív,
de az animáció tartalma, iránya és időzítése **NINCS MEG**.

### Eredeti | Nálunk | Teendő

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `CThumbUI::MakeTimeline` qshow bemutatóablakot és overlay-rétegeket állít fel; a logikai vászon `640 × 480` (`0x007fa730`), a qshow ablak popup/topmost stílusú (`0x00983fc0`). | A `src/picasapy/app/qml/PicasaPy/TimelineView.qml` a főablakon belüli év/hónap bélyegképrács. | Az év/hónap rács nem az eredeti bemutató. A qshow jellegű, képernyőre illesztett felületet a nyitott méret- és tartalommodell után kell megépíteni. |
| A csomag külön Exit, bal, indító, jobb, timeline-sáv és fogantyú grafikát ad; a oneup `prev`/`next` az indexelt oneup listán léptet, az `auto` automatikus lejátszást kapcsol. | A `TimelineView.qml`-ben nincs ilyen vezérlősáv; bezárás és Escape van. | A gombok képi megjelenése ismert, a négy overlay kattintási célja, a fogantyú értéke és az Exit visszatérési nézete nyitott. Ne kösd az overlay `startbutton`-t a `oneup/auto` gombhoz bizonyíték nélkül. |
| A görgő OneUpUI eseményútja ismert, a felsorolt billentyűk qshow-beli hatása és a gyűjtemények/dátumkártyák forrása nem. | A `Main.qml` `Ctrl+5` parancsának `enabled` értéke hamis; a Nézet-menü Időrend eleme szintén letiltott, `timelineRequested` jelzésének nincs QML-fogyasztója. A `MainToolbar.qml` korábbi Időrend-gombját a #1903 eltávolította. Az eredeti `thumbui.tre` a `thumbui/timelinebutton` elemen `m_hidden`-t ad (`472-478`). | A menü és Ctrl+5 bekötés csak a teljes viselkedési modell után aktiválható. Az eredeti eszköztárgomb rejtett, ezért látható gomb hozzáadása eltér az eredeti felülettől. A valódi fókuszú eredeti qshow futás és képernyőkép továbbra is szükséges. |

**Bizonyítottsági fok: feltételes.** A kódút és a független erőforrás-leltár egyezik a külön oneup bemutató, a vezérlőgrafikák, a oneup listaindexelése és az Auto Play állításain. A tartalomforrás, a dátumozás/rendezés, az overlay callbackek, a billentyűk, a kilépési cél és az animáció nem dőlt el.

**Cáfoló kör.** Azt az értelmezést próbáltam cáfolni, hogy a `prev`/`next` közvetlenül hónapot vagy mappát léptet. A `0x00802980`/`0x008029f0` az indexelt oneup lista `+0x3f4` indexét módosítja, a `oneup.tre` pedig ugyanezekre a gombokra mousedown tulajdonságot ad. Ez cáfolja, hogy a gombkezelő közvetlenül naptári hónapindexet kezel; azt nem cáfolja, hogy a listaelemek mappakártyák lennének, mert a szolgáltató típusa továbbra is ismeretlen. A cáfoló eredmény ezért a teljes „mappa vagy hónap” kérdést nem zárja le.

**Nyitott, célzott következő lépések:**

- `Ghidra-kör kell: 0x004039f0 - a CThumbUI-konstruktor +0x2bc szolgáltató-argumentumának konkrét típusa, a +0x2c0 kollekció forráshalmaza és az upstream sorrend. [blokkoló]`
- `Ghidra-kör kell: 0x00a52890 - az örökölt billentyű/egér események, a négy overlay vezérlő hit-test/callback útja, és különösen a sliderthumb húzása. [blokkoló]`
- `Ghidra-kör kell: 0x005e60d0 - a globális billentyűút működése qshow fókuszában, beleértve a nyíl, szóköz, Home/End és Escape parancsokat. [blokkoló]`
- `Ghidra-kör kell: 0x008032e0 - a oneup/exit visszahívásának konkrét célja és visszatérési nézete, valamint hogy az overlay Exit ugyanide köt-e. [blokkoló]`
- `Ghidra-kör kell: 0x00802230 - a 0x007fda00 által indított Időrend-átmenet tényleges vizuális állapota, kezdő/végállapota és időzítése. [blokkoló]`

#### 38.2.5 Ghidra-köteg: a lista és a OneUp-parancsok határa (#4443, 2026-10-17)

**Elsődleges út - Ghidra C-kód.** A 2026-10-17-i köteg `FUN_005e8a70`
teljes dekompilálását adja (`referencia/ghidra/2026-10-17-qshow-diavetites.txt`,
`CÍM 0x005e942e`). Az Időrend bemutatóág lekéri az indexelt kollekció
elemszámát (`0x004a0980`), `0`-tól végigmegy rajta, és minden indexre a
`CThumbUI` vtable `+0x90` metódusát hívja. A qshow felépítőjének
(`0x008037e0`) átadja ezt a listát, valamint a `0x400` × `0x300` logikai
vászonértékeket. A `FUN_005e8a70` ezen ágában nem látszik dátummezőt olvasó
komparátor vagy rendezőhívás: a függvény az aktuális indexelt kollekció
sorrendjét fogyasztja; a kollekció upstream forrása és sorrendképzése nyitott.

**Második út - helyi diszasszembly és RTTI.** A `0x005e942e-0x005e94f1`
utasításai ugyanezt az elemszám → indexhurok → vtable `+0x90` láncot mutatják.
A `0x00562cc0` thunk a `CThumbUI+0x2bc` objektum vtable `+0x20` helyére
továbbít. Az RTTI szerint a `CThumbDB` vtable `+0x20` bejegyzése
`0x00423300`, és a Ghidra-köteg ezt a függvényt is indexparaméterrel működő
adatlekérdezőként dekompilálja. Ez a két út egyezik a szolgáltató-interfész
alakjában; nem bizonyítja, hogy az adott futásidejű `+0x2bc` példány maga
`CThumbDB`, és nem nevezi meg a képhalmazt.

**A léptető és az Auto Play.** A `0x008032e0` `oneup/prev` és `oneup/next`
ágai rendre a `0x00802980` és `0x008029f0` függvényeket hívják. Ezek az
OneUpUI `+0x3f4` indexét csökkentik/növelik, és a következő elemhez a
`+0x3ec` listát, illetve a `+0x3f0` elemszámot használják. A külön
`oneup.tre` erőforrás a két gombnak `mousedown` eseményt ad. Az `oneup/auto`
és `oneup/auto2` a `0x00803110` → `0x00801130` útvonalon a `+0x3bb` bájtot
0/1 között váltja, majd állapotfüggő frissítést indít; az erőforrás felirata
„Auto Play”. Az utóbbi két állítás kód- és erőforrás-útja egymástól külön
származik.

Az `oneup/exit` ág egy OneUpUI vtable `+0x24` hívásból kapott objektum
vtable `+0x14` metódusát hívja két nulla argumentummal. A callback célobjektuma
nem azonosítható az ág utasításaiból. A `overlays/exit` és a bal oldali
rács-vissza ikon hit-test/callback kötése sincs meg, ezért nem állítható, hogy
ez a `oneup/exit`-et hívja. A `oneup/oneup` elem neve szintén nem bizonyít
rács-vissza műveletet.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a qshow saját dátumsorrendet
épít. A teljes `FUN_005e8a70` dekompilált ágát és a megfelelő gépi kód
indexhurok-részét átnéztem dátummező-, komparátor- vagy rendezőhívásért; ilyen
lépés nincs a bemutatóágban. Ez csak a rendezés qshow-beli létrehozását
cáfolja, nem az upstream kollekció korábbi rendezését.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A qshow az aktuális CThumbUI indexelt kollekció sorrendjét járja be; a forráshalmaz, upstream sorrend, cím-/dátumkártyák nyitottak. A `prev`/`next` a oneup listán léptet, az Auto Play állapotot vált. | `TimelineView.qml` év/hónap rács, nem qshow; a menü és Ctrl+5 letiltott, a QML-ben nincs qshow-vezérlősáv. | A bemutatót külön, teljes képernyős módként kell specifikálni. A listát a bizonyított aktuális kollekcióból építsd; ne vezess be új dátumsorrendet a forrás tisztázása nélkül. A rács-vissza és Exit bekötését csak a callback céljának feltárása után add meg. |
| A parancsnév `thumbui/timelinebutton` megvan, de a `thumbui.tre` elem `m_hidden`; a 2026-10-17-i út nem igazolt látható fejlécgombot. | Nincs aktív Időrend-eszköztárgomb. | A menü és Ctrl+5 újraaktiválása megfelel a jegynek; látható eszköztárgomb az eredetivel való paritásban nem bizonyított, ezt termékdöntésként külön kell kezelni. |

**Bizonyítottsági fok: feltételes.** A kollekcióbejárás és a szolgáltató virtuális interfésze két eltérő vizsgálati úton egyezik. A parancsok egy része célzott diszasszemblyből és erőforrás-nevekből követhető, de a qshow billentyűi, az overlayek kattintási céljai, a rács-vissza, az Exit visszatérési nézete, a kártyák tartalma/sorrendje és a tényleges animáció továbbra sincs eldöntve.

**Nyitott:**

- `Ghidra-kör kell: 0x004039f0 - a CThumbUI-konstruktor +0x2bc szolgáltató-argumentumának konkrét típusa, a +0x2c0 kollekció forráshalmaza és upstream sorrendje. [blokkoló]`
- `Ghidra-kör kell: 0x00a52890 - az örökölt egér/billentyű eseményút, az overlay exit/left/startbutton/right hit-testje és a sliderthumb húzási értékkötése. [blokkoló]`
- `Ghidra-kör kell: 0x005e60d0 - a qshow láthatósága alatt elérhető globális gyorsbillentyűk és a Ctrl+5/nyilak/szóköz/Escape útja. [blokkoló]`
- `Ghidra-kör kell: 0x008032e0 - az oneup/exit callback konkrét célobjektuma és visszatérési nézete; az oneup/oneup rács-vissza szerepe. [blokkoló]`
- `Ghidra-kör kell: 0x00802230 - az Időrend-átmenet tényleges képi tartalma és időzítése. [blokkoló]`
- A mappák/albumok forráshalmaza és upstream sorrendje, a cím-/dátumkártyák, a futó billentyűviselkedés és az Exit utáni nézet: **NINCS MEG**.

#### 38.2.6 Második Ghidra-köteg: a 38.2.5 nyitott pontjainak mérése (#4443, 2026-10-17)

**Forrás és módszer.** A `referencia/ghidra/2026-10-17-qshow-2.txt` öt címe (`0x004039f0`, `0x00a52890`, `0x005e60d0`, `0x008032e0`, `0x00802230`) és az első köteg `FUN_005e8a70` dekompilátuma (`2026-10-17-qshow-diavetites.txt`). Két független úton ellenőriztem: (A) a `0x005e8a70` helyi diszasszemblálása (`annot_disasm.py`, a munkafa `.bt/` mappájában, a repón kívül), (B) a bináris-index (függvénytábla, RTTI, hívóélek), (C) a `Picasa3.exe` közvetlen olvasása (vtable-slotok, konstansok). A címek a `Picasa3.exe` virtuális címei.

##### 1. Lista forrása és sorrendje

- **Bizonyított: üres listánál nem indul a bemutató.** A `0x005e8a70` mód-1 ágában a `FUN_005d2a70()` és a `[this+0x2c0]+0x154` (0 vagy 1) ellenőrzése után, valamint a függvény végén, ha az összegyűjtött tömb (`uStack_d0`) üres, az `IDS_MUST_SELECT` üzenettel tér vissza. A `0x008037e0` (a qshow-építő) csak ezután hívódik, és egyetlen hívója van: a `0x005e8a70`. (dekompilátum + diszasszembly)
- **Bizonyított: a tömb CSAK a Flipbook + Ctrl + Shift ágban töltődik.** A feltételek: `Preferences\Flipbook` kulcs, `GetAsyncKeyState(0x11)` és `(0x10)`, valamint az aktív ablak (`DAT_00d67849`). A forrás `[this+0x2bc]` (a szolgáltató), az elemszám `[+0x4ec] >> 1`, a rekord elérése `+0xf8` (`0x004edf60`). A rekord típuskódja szerint szűr: 2, 3, 6, 7, 13, 14, 18, 22, 24, 26, 27, 28, 31 (a kódok jelentése **NINCS MEG**). A sorrend **fordított**: az elemszám-1 indextől 1-ig, a 0. elem kimarad. (dekompilátum + diszasszembly)
- **Ellentmondás (mérve):** Shift nélkül, a Flipbook beállítástól függetlenül, a tömb üres marad, tehát a mód-1 ág `IDS_MUST_SELECT`-re fut, nem qshow-ra. ⚠️ **HELYESBÍTVE (38.2.8):** ez téves: a `0x007164b0` Shift nélkül is tölt, a `[this+0xeac]` elemeiből. Az eredeti (téves) indoklás: a tömb-slotok (`[esp+0x2c]`, `[esp+0x30]`, `[esp+0x40]`, `[esp+0x44]`) íróhelyei ezt mutatják: a nullázás (`0x005e8dc1`-`0x005e8dcd`) után csak olyan írások vannak, amelyek a már üres `local_c0`-ból másolnak (`0x005e9178`-`0x005e929a`). **Ez nincs összhangban a 38.2.2 megfigyelésével** (job-102: Ctrl+5 után qshow látszott). Lehetséges magyarázat: a felvételen Shift volt lenyomva, ez nincs rögzítve.
- **Feltételes: a rács listája.** A `0x004039f0` a főablakot (`ytFrameWindow`, vtable `0x00cd95c0`) és egy 0x3710 bájtos objektumot hozza létre (konstruktor `0x005643e0`, paraméterei `param_1+0x1030` és `+0x1038`); a `FUN_0040bf70` tölti. Ez a CThumbUI-nak tűnik (a `0x005e8a70` `this`-e is ilyen, a `+0x2bc`/`+0x2c0` mezőkkel), de nem bizonyított. A rács lista-forrása ettől még nincs igazolva, a qshow-é pedig nincs.
- **Nyitott: a „Preparing timeline…” ciklus kimenete.** A ciklus (`0x005e8a70`, dekompilátum 1215-1259. sor) `FUN_004a0980()` elemszámon megy 0-tól felfelé, és minden indexre a `this->vt+0x90` hívást végzi, elemenként a `piStack_6c` folyamatjelző-objektumnak adva. Hogy ez-e a qshow listája, nincs igazolva.

##### 2. Vezérlők és billentyűk

- **`0x008032e0` (oneup esemény, kattintás = `0x8000004`): megerősített, tizenkét név.** A kód név-összehasonlítással választ: `captionbutton` (felirat-váltás, `0x009cd730` / `0x009cd760`), `plusone` / `minusone` (`0x00802ff0`, `+1,0` / `-1,0`; a `-1,0` a `0x00cf3ed0`-ban), `auto` / `auto2` (`0x00803110`, automatikus lejátszás), `timeline` (`0x00802be0`, majd `0x007fda00`), `exit` (lásd 3.), `prev` / `next` (`0x00802980` / `0x008029f0`, az indexet lépteti), `rotateright` / `rotateleft` (`0x00a60920` 1, illetve 0, vt+8 hívás, `0x00802e20`), `star` (vt+4 hívás a `[esi+0x359]` jelzővel).
- **Billentyűk: erős.** A `0x005e60d0` (a főablak billentyű-kapcsolója, a `0x005e6710` hívja) switch-listája: `0x0D` (Enter), `0x30`-`0x33`, **`0x34` és `0x35` (`4`, `5`) → `0x005e8a70(this, 0)`, illetve `(this, 1)`**, továbbá `0x36`, `0x38`, `0x39`, `0x41`-`0x59` (betűk), `0x75`-`0x78` (F6-F9). **Nincs eset** Esc (`0x1B`), Space (`0x20`), End/Home (`0x23`/`0x24`) és a nyilak (`0x25`-`0x28`) számára: a főablak kapcsolója ezekre nem ad műveletet. Ez egyezik a 38.2.2-es fókuszhibával.
- **Egér és görgő: megerősített.** A `0x00a52890` switchében nincs billentyű-eset (`0x100`/`0x101` nincs). Bal gomb (`0x201`): találat-kereső (`0x009e4630`) és `SetCapture`. Görgő (`0x20a`): a `0x00a516c0` a delta / 120 értéket kapja (`0x00cf4640` = 120, a WHEEL_DELTA). A OneUp saját kezelője (`0x00803180`, 38.2.4) léptet.
- **A `sliderthumb` húzása: NINCS MEG.** A találati elem kezelője a `0x0052d3c0` és a `0x009e4630` körül van, és nincs a kötegben.

##### 3. Exit és rács-vissza célja

- **Mechanizmus: megerősített (diszasszembly + vtable-olvasás).** `oneup/exit` → `this->vt+0x24()` → `0x00a6ccf0`: `mov eax,[ecx+0x50]; ret`, vagyis az objektum `[this+0x50]` mezőjét adja vissza → annak `vt+0x14(0, 0)` hívása. A `+0x50` mezőt a `vt+0x28` (`0x00a6cd00`: `mov [ecx+0x50], arg`) állítja. A CThumbUI vtable (`0x00c9052c`) +0x24 slotja ugyanez a getter.
- **Ha a tulajdonos CThumbUI, az Exit üres.** Ekkor a `vt+0x14` = `0x00b0d990`, amely csak `ret`. Vagyis az Exit ilyen tulajdonosnál nem végez műveletet. A tényleges tulajdonos osztálya **NINCS MEG**: a `vt+0x28` hívásai indirektek, az index nem látja őket. A `OneUpUI` vtable-jét (`0x00cbd5c4`) író konstruktort kell megkeresni.
- **Rács-vissza = `oneup/exit`: feltételes.** A bal alsó ikon (képernyő-x 348-391) az `overlays/exit` réteghez hasonlít (forrás-rect `(8,404,51,432)`, rács és nyíl), a `oneup.tre` kilépés-csoportja (`exit_icon`, `bcklabel`, `exit`) pedig ugyanerre a gombra utal. A kötés (hit-test) az `exit` elemhez a respack-geometria mérése nélkül nincs igazolva. A `oneup/oneup` nevet a `0x008032e0` nem kezeli: az a képalap elem.

##### 4. Átmenet

- **Időrend-váltás (`0x007fda00`): megerősített lépéssor (diszasszembly).** Kapuk: `[this+0x2d8]` (bájt) és `[this+0x538]` (mutató). Az aktuális index (`[this+0x3f4]`) negatív esetén 0. A QPC-érték a `[this+0x430]`-ba (double) kerül, majd **`0x00802230(this, 1)`** hívódik: a `param_2 = 1` nem animált ágat jelez. Végül `[+0x3b8]=1`, `[+0x3b9]=1`, `[+0x3ba]=0`, `[+0x3bb]=0`. A flagek jelentése **NINCS MEG**.
- **A `0x00802230` a következő elem ugrása véletlen eltolással: megerősített képlet.** Az elem `[this+0xfb][[this+0xfd]]`. Ha `([this+0xfc] >> 1) <= [this+0xfd]`, a visszatérés 4 (vége). Két `rand()` hívás (CRT, `0x00c08221`) ad egy-egy 15 bites `t = r / 32768` értéket. Az új eltolás: x = W · 0,15 · t_x, y = H · 0,5 · 0,15 · t_y, ahol W = `[this+0x11d]`, H = `[this+0x11e]` (a középre igazítás is ezekből számol). A konstansok a binárisban: `0,15` (`0x00cf4320`, double), `0,5` (`0x00c72150`, double). Az előző eltolás `[+0x102]`/`[+0x103]`-ban marad.
- **Nem animált ág (`param_2 ≠ 0`): a kódalak megvan, a viselkedés NINCS MEG.** Ekkor `local_58 = 0` és a `0x00802180` hívódik. Az animátor (`[+0xb8]+4`) viselkedése nincs megmérve. **Helyesbítve (38.2.7):** a `0x00802180` nem animációs ág, hanem a `Preferences\CarefulEnhance` beállítás frissítése.
- **Időtartam: NINCS MEG.** A `ROUND(_DAT_00d35808)` a `[+0xb9]` ágon van. A `0x00d35808` a `.data` szakaszban van (írható), a fájlban lévő bájtok nem fordítási idejű konstansok (f64-ként 7,18·10^-305). Az íróhely nincs az indexben: az `xrefs` táblában a hívások szerepelnek, adat-hivatkozás nem.
- **A véletlen seed-je: NINCS MEG** (a `srand` hívását nem vizsgáltam), így az eltolás nem reprodukálható.

##### Bizonyítottsági fok

| állítás | fok | alap |
|---|---|---|
| üres tömb → `IDS_MUST_SELECT`, nem qshow (mód-1, Shift nélkül) | megerősített | dekompilátum + diszasszembly (tömb-slotok) |
| a lista csak Flipbook + Ctrl + Shift ágban töltődik, fordított sorrend | megerősített | dekompilátum + diszasszembly |
| Ctrl+5 → qshow | **feltételes** (38.2.8) | a korábbi „Shift nélkül nem ad qshow-t” téves; a kód Shift nélkül is adhat qshow-t, ha K1/K2/K4 teljesül; a 38.2.2 megfigyelés összefér vele |
| billentyűtérkép (`0x005e60d0`) | erős | teljes switch-lista, nincs nyíl/Esc/Space eset |
| az Exit mechanizmusa (`this+0x50` → `vt+0x14`) | megerősített | diszasszembly + vtable-olvasás |
| az Exit célja (a tulajdonos osztálya) | NINCS MEG | indirekt `vt+0x28` hívások |
| rács-vissza = `oneup/exit` | feltételes | képi és névbeli egyezés, geometria nincs mérve |
| eltolás-képlet (0,15 · W; 0,5 · 0,15 · H; rand / 32768) | megerősített | dekompilátum + `pefile`-olvasott konstansok |
| időtartam, seed, animátor | NINCS MEG | futásidejű `.data` változó, nincs író az indexben |

**Két független út:** a lista-kapunál a dekompilátum és a helyi diszasszembly egyezik; az Exit-mechanizmusnál a diszasszembly és a vtable-olvasás; a konstansoknál a dekompilátum és a `pefile`-olvasás.

##### Cáfoló kísérletek

1. „A Ctrl+5 normál ága qshow-t nyit.” **Cáfolva a kódból** (a tömb üres, `IDS_MUST_SELECT`). Ez ellentmond a 38.2.2 megfigyelésének; a két állítás egyike téves, vagy Shift volt lenyomva. Ez nincs eldöntve.
2. „Az Exit a rácsnézetbe visz.” **Nem igazolt, részben cáfolt:** CThumbUI-tulajdonosnál a hívott `0x00b0d990` üres, így a visszatérés nem ebből az ágból jön.
3. „Az Időrend-váltás animált.” **Nem igazolt:** a `0x007fda00` `param_2 = 1`-gyel hívja a `0x00802230`-at, ami nem animált ágat jelez; az animátor viselkedése nincs megmérve.

##### Mérleg a 38.2.5 nyitott pontjairól

| 38.2.5 pont | állapot |
|---|---|
| lista forrása és sorrendje | **részben zárva**: a flipbook-ág forrása és sorrendje megvan; a normál ág ellentmond a 38.2.2-nek |
| vezérlők és billentyűk | **részben zárva**: név → művelet és billentyűtérkép megvan; a `sliderthumb` húzása nyitott |
| Exit és rács-vissza célja | **részben zárva**: a mechanizmus megvan; a célobjektum osztálya nyitott |
| átmenet | **részben zárva**: az eltolás-képlet és az Időrend-váltás lépései megvannak; az időtartam nyitott |

**Nyitott kérdések: 0 nyílt · 0 lezárva · 9 blokkolt · 0 hatókörön kívül · 0 csak-nyitva.** A 38.2.5 öt Ghidra-kérdéséből négy részben zárult; a maradék a lenti tételekben van.

##### Nyitott (a hívó futtatja, fontosság szerinti sorrendben)

- `Ghidra-kör kell: 0x00a52890 - a találati elem (sliderthumb) húzási kezelője: a 0x0052d3c0 eseményhívás és a 0x009e4630 találat-kereső célja, az értékkötés. [blokkoló]` **Részben (38.2.7):** a bal gombos ág és a `SetCapture` megvan; az értékkötés a `0x0052d430` alatt nyitott.
- `Ghidra-kör kell: 0x008037e0 - a qshow ablak létrehozása: WndProc, és melyik ablak kapja a billentyűket (nyíl, Esc). [blokkoló]` **Részben (38.2.7):** a fókusz a `obj+0x6c` HWND-re kerül; a WndProc a `0x00983670` alatt nyitott.
- ~~`Ghidra-kör kell: 0x00802180 - a 0x00802230 param_2 ≠ 0 (nem animált) ágának célja. [blokkoló]`~~ **LEZÁRVA (38.2.7):** nem animációs ág, a `Preferences\CarefulEnhance` beállítást olvassa.
- `Ghidra-kör kell: 0x004edf60 - a rekord típuskód-mezője (a 4. mező): a 13 kód (2, 3, 6, 7, 13, 14, 18, 22, 24, 26, 27, 28, 31) jelentése. [blokkoló]` **A mező olvasása kész (38.2.7); a kódok jelentése örökölt (paszta-kör).**
- ~~`Ghidra-kör kell: 0x00415500 - a Preparing ciklus folyamatjelző-objektuma (piStack_6c) és a vt+4 hívás célja: a ciklus kimenete. [blokkoló]`~~ **LEZÁRVA (38.2.7):** `ytProgress`-konstruktor; a ciklus a `0x005e8a70`-ben van.
- **Eredeti futtatás (Colab-gép, nem Ghidra):** Ctrl+5 Shift nélkül, a Preferences\Flipbook be- és kikapcsolva, a billentyű-állapot naplózva; rögzítendő a qshow vagy az `IDS_MUST_SELECT` üzenet. Ez dönti el a 38.2.2 ellentmondást. [blokkoló]
- **Paszta-kör (gépi, a teljes .text-keresés csak a `paszta.py`-n át):** (a) a `0x00cbd5c4` (OneUpUI vtable) írója, a konstruktor, amely megmondja a `+0x50` tulajdonos osztályát; (b) a `0x00d35808` íróhelye (az időtartam). [blokkoló]
- **Respack-kör (gépi):** az `overlays/exit` és az `oneup/exit` elemek geometriájának összevetése a képernyő-x 348-391 gombbal (rács-vissza kötés). [blokkoló]

#### 38.2.7 Harmadik Ghidra-köteg és a Ctrl+5 ellentmondása (#4443, 2026-10-17)

**Forrás és módszer.** A `referencia/ghidra/2026-10-17-qshow-3.txt` hat címe (`0x00a52890`, `0x008037e0`, `0x00802180`, `0x004edf60`, `0x00415500`, `0x0052d3c0`) és a `2026-10-17-qshow-diavetites.txt` (`FUN_005e8a70`) dekompilátuma. Két független úton ellenőriztem: (A) a dekompilátum, (B) a helyi diszasszembly (`annot_disasm.py`; a kimenet a munkafa `.bt/` mappájában volt, a repón kívül, a kör végén törölve). Kiegészítésként a billentyű-ugrótábla bájtjait (`pefile`) és a bináris-index hívóéleit néztem meg. A `Picasa3.exe` PE-verziója `3.9.141.259`, a fő verzió egyezik a Colab-gépen futó angol Picasáéval (3.9.141).

**Bizonyítottsági fok**

| állítás | fok | alap |
|---|---|---|
| a menü és a Ctrl+5 ugyanazt a `0x005e8a70(this, 1)` hívást indítja | megerősített | A + B + ugrótábla-bájtok |
| Shift nélkül nincs qshow (mód 1) | megerősített | A + B, írás-elemzés |
| a felvétel (Ctrl+5 kijelölés nélkül qshow) egyezik-e a kóddal | feltételes: összeférhető (38.2.8) | a 188-as kép nincs a munkafában |
| qshow-építő: mód-ág, fókusz-HWND | megerősített | A + B |
| `0x00802180` = `CarefulEnhance`-frissítés | megerősített | A |
| `0x00415500` = `ytProgress`, `0x0052d3c0` = `ytUIEvent` | megerősített | A |
| WndProc, csúszka értékkötés, rekord-típuskódok | nyitott | a kötegen kívül |

**1. Az útvonal.**
- A menü (`thumbui/timelinebutton`) és a billentyű ugyanazt a hívást indítja. A nevet a `0x005d9cc0` elosztó kezeli: a `thumbui/timelinebutton` ága `push 1` (`0x005da7ae`), a `thumbui/sbutton` ága `push 0`.
- A billentyűkapcsoló (`0x005e60d0`) ugrótábla-bejegyzése szerint a `4` a `0x005e625e` (mód 0), az `5` a `0x005e6279` (mód 1) ágra megy. A Ctrl+5 tehát mód 1.

**2. A mód-1 ág kapuja.**
1. `0x005d2a70()` nem nulla, és a `[this+0x2c0]+0x154` mező nem 0 és nem 1 (`0x005e8dd6`-`0x005e8dee`). Ha nem, IDS_MUST_SELECT (`0x005e983e`).
2. A tömb feltöltésének egyetlen útja: a Preferences\Flipbook igaz, az aktív ablak (`DAT_00d67849`) igaz, a Ctrl (`GetAsyncKeyState(0x11)`) és a Shift (`GetAsyncKeyState(0x10)`) egyszerre lenyomva (`0x005e8e28`-`0x005e8e6f`). Ekkor a rekordtár fordított sorrendű bejárása tölti a tömböt (`0x005e8e75` kezdettől).
3. A tömb elemszáma `[esp+0x30]` (`uStack_d0`). A qshow-építő (`0x005e9787`) csak akkor hívódik, ha ez legalább 1 (HELYESBÍTVE, 38.2.8: a kódolt érték 2·n + jelző, tehát n ≥ 1 elég): `0x005e95e6` `test [esp+0x30], 0xfffffffe`; különben IDS_MUST_SELECT (`0x005e97ce`).

**3. A nem-Flipbook ág nem tölt (megerősített, írás-elemzés).** A másolás forrása a `[esp+0x40]` lista-mutató, amelyet a mód-1 ág NULL-ra nulláz (`0x005e8dc1`). A másolási számlálót (`[esp+0x44]`) csak nullázás írja (`0x005e8dc5`, `0x005e8e09`). A Preferences-kulcsot felépítő `0x00407a20` a `[esp+0x50]` objektumba ír, a `0x009c84a0` pedig a `[esi+4]` és `[esi+8]` mezőket nullázza. A `[esp+0x30]` írói (`0x005e8f97`, `0x005e91a3`, `0x005e9274`) a Shift-ágban vagy számláló-függő ciklusokban vannak. Ellenpélda nincs: a Shift nélküli ág üres tömbbel IDS_MUST_SELECT-re fut.

**4. A mért ellentmondás.** A kód szerint Shift nélkül nincs qshow. A 38.2.2 (job-102) és a jegy 188-as Colab-felvétele szerint Ctrl+5 kijelölés nélkül qshow nyílik: mappanév és dátum jobbra fent, mappakártyák, alul rács-vissza, előző / lejátszás / következő, csúszka, és az Escape nem zárja be. A 188-as kép nincs a munkafában (a legfrissebb képtári fájl 2026. október 1-jei), ezért a leírást a kör feladatából vettem, a képet nem láttam.

**Ítélet.** ⚠️ **VISSZAVONVA (38.2.8):** a „Shift nélkül nincs qshow” állítás téves. A kód-olvasat többi része megerősített. A felvétel és a kód viszonyát a 38.2.8 rendezi: összeférhetők, a K1, K2 és K4 kapu futásidejű értékétől függően.

**5. A többi cím (Ghidra-köteg, 2026-10-17-qshow-3).**
- **`0x008037e0` (qshow-építő): megerősített.** A `Preferences\BigSlideshow2` kulcsot olvassa. A paraméter-struktúra 1. bájtja (a hívó módja, a `0x005e8a70` `[ebp+0xc]`-je) dönti el az ágat: mód 0 → `0x00801cf0`; mód 1 → `0x007fda00` (Időrend-váltás), majd `0x00802060`, ha `[obj+0x3bf] == 0` (`0x008039de`-`0x008039fb`). A billentyűfókuszt `SetFocus(obj+0x6c)` adja. A `+0x6c` mező HWND, ugyanez a mező az egérfogásban is (`SetCapture(param_1[0x14]+0x6c)`, `0x00a52890`). Az ablak osztálya és WndProc-ja nincs a kötegben: a `0x00982bf0` a `0x00983670`-et hívja, az a létrehozó hely.
- **`0x00802180`: LEZÁRVA. A 38.2.6 „nem animált ág" címke téves.** A `Preferences\CarefulEnhance` beállítást olvassa, beállítja az `obj+0x46c` mezőt (`0x009db610`), majd `0x00aa40a0` és `0x009ab410` hívásokat végez. Nem animációs ág. Az átmenet animátora (`0x00802230`) nyitott.
- **`0x004edf60` (rekordolvasó): a szerep LEZÁRVA, a típuskódok jelentése nyitott.** A `param_1[0xfc]` mutatótömbből olvas, és a 4. mezőt (`+0x18`) adja vissza. A `0x3e9` (1001) indirekció: a `+0x20` indexű rekordra ugrik, a `0xffffffff` azt jelenti, hogy nincs tovább. A 2, 3, 6, 7, 13, 14, 18, 22, 24, 26, 27, 28, 31 jelentését a rekordot író kód adja, az nincs a kötegben.
- **`0x00415500`: LEZÁRVA.** `ytProgress` (folyamatjelző) objektum konstruktora: vtable, számláló nullázása, a szöveg másolása (`0x00985ff0`), majd `0x00415380` hívása. A ciklus a `0x005e8a70`-ben van: az elemszám a `0x004a0980`-tól jön (`0x005e9434`), a szöveg `Preparing timeline...` (ASCII, három ponttal; bináris cím `0x00c978f0`, a hívó `0x005e9442`).
- **`0x0052d3c0`: LEZÁRVA.** `ytUIEvent` konstruktora; a paraméter az eseménytípus (a bal gombos lenyomás ága az `1`-et adja, `0x00a52890` `0x201`-ág). A találat-kereső (`0x009e4630`) visszatérése 1000000 (`0x000f4242`); a hívó ezt találatként kezeli.
- **`0x00a52890` (egér-kapcsoló): részben.** A `0x200`, `0x201`, `0x202`, `0x20a` ágak megvannak; találatkor a kattintott elem HWND-jére `SetCapture` kerül. A csúszka értékkötését az eseményt továbbító `0x0052d430` végzi, az nincs a kötegben.

**6. Cáfoló kísérletek.**
1. „Van más író, ami Shift nélkül tölti a tömböt." Megdőlt: a `[esp+0x30]` összes írója a Shift-ágban vagy számláló-függő ciklusban van; a Shift nélküli ágon a `[esp+0x40]` NULL, a `[esp+0x44]` nulla.
2. „A `copy_Picasa_3_7` mappanév miatt a bináris más verzió, mint a felvételen." Megdőlt: a PE-verzió 3.9.141.259, a fő verzió egyezik.
3. „A `0x00802180` az átmenet nem animált ága." Megdőlt: `CarefulEnhance`-frissítés.
4. „A `0x00415500` a Preparing-ciklus." Megdőlt: folyamatjelző-konstruktor, a ciklus a `0x005e8a70`-ben van.

**7. Kész, ha (a jegy pontjai).**
- ⛔ a spec leírja a bemutató működését, bizonyítékkal: **részben.** Megvan az indítási útvonal, a kapuk, a fókusz-HWND és az átmenet lépéssora. Nincs meg az ablak WndProc-ja, a billentyűk, a csúszka, az Exit célja, az időtartam és a kártyák tartalma.
- ⛔ Nézet ▸ Időrend és Ctrl+5 kattintásos teszttel: **nincs.** Ebben a körben kódot nem írtam (`src/`, `tests/` érintetlen).
- ⛔ képernyőkép az eredetivel összevetve: **nincs.** Nincs implementáció, és a 188-as kép nincs a munkafában.

**8. Codex-kész lista: nem adható.** A viselkedés nem dőlt el: a Ctrl+5 kiváltó feltétele ellentmondásos, a billentyűk, a csúszka és az Exit nincs megmérve. Egy fejlesztői lista most feltevésekre épülne. Előfeltételei: (a) a Ctrl+5 kettős olvasatának feloldása (188-as billentyű-napló), (b) a qshow WndProc-ja (`0x00983670`), (c) a csúszka kezelője (`0x0052d430`), (d) az Exit tulajdonos-osztálya (paszta).

**9. Nyitott (a hívó futtatja).**
- **Blokkolt:**
  - **Eredeti futtatás (Colab-gép, nem Ghidra):** a 188-as futás billentyű-naplójának ellenőrzése (volt-e Shift a Ctrl+5 pillanatában), vagy új Ctrl+5 futás Shift-naplóval, a Preferences\Flipbook be- és kikapcsolva. [blokkoló]
  - `Ghidra-kör kell: 0x00983670 - a qshow ablak létrehozása (CreateWindowEx) és az ablakosztály WndProc-ja: melyik HWND kapja a nyíl-, szóköz-, Home/End- és Escape-billentyűket. [blokkoló]`
  - `Ghidra-kör kell: 0x0052d430 - HELYESBÍTVE (38.2.8): nem továbbító, hanem `ytUIEvent`-vtábla-beállító; a csúszka-kezelést a `0x00a52890` vezérlőkezelő viszi tovább. [blokkoló]`
- **Örökölt (gépi, nem ebben a körben kérdezve; a munkasorba):** (a) a rekordtípus-kódok írója (`0x004edf60` rekordtára, paszta); (b) az Exit tulajdonos-osztályának írója, `0x00cbd5c4` (paszta); (c) az átmenet időtartamának íróhelye, `0x00d35808` (paszta); (d) az `overlays/exit` és `oneup/exit` geometriája (respack); (e) az átmenet animátora, `0x00802230` (Ghidra vagy diszasszembly); (f) a gyűjtemény forrása, `0x004039f0` (`+0x2bc` szolgáltató, Ghidra).

**Nyitott kérdések mérlege:** 6 nyílt (örökölt, a munkasorba) · 5 lezárva · 3 blokkolt · 0 hatókörön kívül · 0 csak nyitva.

Lezárva ebben a körben: a `0x00802180` szerepe; a `0x00415500` szerepe; a `0x0052d3c0` szerepe; a `0x008037e0` mód-ága és fókusz-HWND-je; a másolási számláló értéke a Shift nélküli ágon.

#### 38.2.8 Negyedik kör: a Ctrl+5 normál útja, a Shift-állítás visszavonva (#4443, 2026-10-17)

**Kérdés.** Melyik út vezet a `0x005e8a70` mód-1 ágához, és mely kapuk döntik el, hogy a Ctrl+5 megnyitja-e a qshow-t? A 38.2.6-38.2.7 szerint a Shift nélküli ág üres listával `IDS_MUST_SELECT`-re fut; a 188-as felvétel szerint kijelölés nélkül qshow nyílik.

**Forrás és módszer.** (A) A `0x005cb990` ID-switch táblái a `Picasa3.exe` PE-jéből olvasva (`pe_dis.read`, csak olvasás); a `0x005e60d0` billentyű-switch és a `0x005e8a70` teljes diszasszemblyje (`annot_disasm.py`; a munkafa `.bt/` mappájában, a kör végén törölve). (B) A bináris-index (`functions`, `xrefs`, `string_xrefs`) és a `paszta.py`-val végzett teljes `.text` pásztázás: `0x9ccc` és `0x9c..` immediate-ok, valamint a `+0xeac` mező írói. Nincs Ghidra-kör és nincs hálózat.

**1. A három belépés, egy cél (megerősített).**

| belépés | kód | hívás |
|---|---|---|
| menüparancs, ID `0x9ccc` (`Nézet ▸ Időrend`) | `0x005cb990`: `cmp esi,0x9c41` · `lea eax,[esi-0x9c42]` · `cmp eax,0xfa` · `movzx edx,byte ptr [eax+0x5cdb34]` · `jmp dword ptr [edx*4+0x5cd9fc]`. Az ID 0x9ccc → index 0x8a → bájt 47 → `0x005cbbdd`: `push 1` · `push ebx` · `call 0x005e8a70` | `(this, 1)` |
| billentyű `Ctrl+5` | `0x005e60d0` → `0x005e6279`: `push ebp` · `call 0x005696c0` · `jne 0x005e65f7` · `push 1` · `push ebp` · `call 0x005e8a70` | `(panel, 1)` |
| eszköztár-név `thumbui/timelinebutton` (a 38.2.7 kódolvasata, most nem mértem újra) | `0x005d9cc0` → `0x005da7ae` (`push 1`) | `(this, 1)` |

A menü és a billentyű ugyanabba a mód-1 ágba fut. A `this` a két ágban más objektum lehet (a billentyűnél a switch `ebp` argumentuma, a menünél az `ebx`); az azonosságuk nincs megmérve, de a K-kapuk mindkét esetben ugyanazt a kódot futtatják.

A „vizsgált ág nem a Ctrl+5 normál útja” hipotézis **cáfolva**: a `0x005e8a70` mód-1 ága a Ctrl+5 normál útja.

Módszertani megjegyzés: a `0x9ccc` literál egyetlen operandusként szerepel (`0x0055aa15`, a menütábla-építő tárolása). Az elosztó a `0x9c42` bázist vonja le (`lea eax,[esi-0x9c42]`), ezért a literálra keresés nem találja az esetet. A bázis-levonás a keresés kulcsa.

**2. A mód-1 ág kapui (megerősített, `0x005e8a70` diszasszembly).**

| kapu | cím | feltétel | ha nem |
|---|---|---|---|
| K1 | `0x005e8dd1` | `call 0x005d2a70` ≠ 0. A függvény a `[this+0x2bc]+0x760` (catdata, db3) soraiban keres olyat, ahol a `state` oszlop (`0x006a5e60`) ≠ 0 | `IDS_MUST_SELECT` (`0x005e983e`) |
| K2 | `0x005e8dde` | `test dword ptr [ecx+0x154], 0xfffffffe` ≠ 0, ahol `ecx = [this+0x2c0]`: a mező nem 0 és nem 1 | `IDS_MUST_SELECT` (`0x005e983e`) |
| K3 | `0x005e8df4`-`0x005e8e6f` | Flipbook-beállítás ∧ aktív ablak ∧ Ctrl ∧ Shift: Flipbook-lista a `[this+0x2bc]` rekordtárából, fordított sorrendben. Shift nélkül ugrás `0x005e907b`-re | nincs külön ág |
| K4 | `0x005e907d` | `call 0x005675d0` = 0. A függvény a `[this+0xeac]` láncot vizsgálja; ha nincs megfelelő csomópont, felszabadítja és újraépíti (`0x00717bb0`), és -1-et ad, ha az újraépítés nem sikerül | nem 0: a builder ezt az értéket adja vissza, qshow nem nyílik |
| L2 | `0x005e90a5` | `[this+0xeac]` ≠ 0: `call 0x007164b0`. Minden i-re: `item = vt+0xb8(i)`; ha `item[+0x5a] == 0`, az `item[+0xb4]` bekerül a listába | üres lista → K5 |
| L3 | `0x005e90b9` | `[this+0xe64] == -1`: a `0x005e92a0` ág, listaépítés a `0x00891110` függvénnyel | nem a fő út |
| K5 | `0x005e95e6` | `test dword ptr [esp+0x30], 0xfffffffe`: a kódolt számláló (2·n + jelző) ≠ 0, azaz n ≥ 1 | `IDS_MUST_SELECT` (`0x005e97ce`) |
| vége | `0x005e9787` | `call 0x008037e0` (a mód-1 qshow-építő) | nincs |

**3. Miért nem a kijelölés a lista forrása.** Az L2 lista a `[this+0xeac]` gyűjteményből épül, nem a kijelölésből. Ennek írója a `0x00662b20`, amelynek sztringjei (`faces`, `albums`, `Search results`, `pictures`) a nézetek neveire utalnak. Ebből az következik (feltételezés a sztringekből, nem mérve), hogy a `[this+0xeac]` a megjelenített nézet aktuális gyűjteménye. A `+0x5a` jelző jelentése nincs megmérve (rejtett-kép szűrő a gyanú).

**4. Cáfoló kísérletek.**

1. „A Shift nélküli ágban a tömb üres” (38.2.6, 38.2.7). **Cáfolva.** A `0x007164b0` a `lea esi,[esp+0x44]` mutatóján át tölti a hívó tömbjét. A `lea` a `push eax` után fut, így az `esp` 4-gyel le van húzva, és a `[esp+0x44]` a hívó `[esp+0x40]`-`[esp+0x44]` párját jelenti. A 38.2.7 „nem-Flipbook ág nem tölt” állítása csak a közvetlen írásokat nézte, a mutatón átadott írást nem.
2. „A qshow-kapu legalább 2 elemet kér”. **Helyesbítve.** A `[esp+0x30]` számláló 2·n + jelző kódolású (a `0x005e8f97` és a `0x005e9192`-`0x005e91a3` elemenként +2-t ad), a `0xfffffffe` maszk tehát n ≥ 1-et enged át.
3. „A Ctrl+5 nem a mód-1 ág”. **Cáfolva** (1. pont).
4. Megmaradó kérdés: K1, K2 és K4 futásidejű értéke. A statikus kód ezeket nem dönti el.

**5. Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| a Ctrl+5 billentyű és a menüparancs → `0x005e8a70(this, 1)` | megerősített | A: diszasszembly és PE-tábla; B: billentyű-switch |
| a Shift-ág (K3) Flipbook-listát ad, nem a normál listát | megerősített | A: diszasszembly |
| qshow-kapu: n ≥ 1 | megerősített | A: kódolás és maszk |
| a Shift nem feltétele a qshow-nak (L2 út) | feltételes | A; a K4 és K1/K2 futásidejű értékétől függ |
| felvétel ↔ kód | feltételes: összeférhető | A; K1/K2/K4 értéke nincs meg |
| `[this+0xeac]` = a nézet gyűjteménye | feltételezés | B: író sztringjei; nincs mérve |

**6. Helyesbítések a 38.2.6-38.2.7 állításaiban.**

- ⛔ „Shift nélkül nincs qshow”: **visszavonva** (L2 út).
- ⛔ „legalább 2 elem”: **helyesbítve**, n ≥ 1 (K5).
- ⛔ „a `0x0052d430` a bal gombos esemény továbbítója”: **helyesbítve**. A függvény `ytUIEvent`-vtábla-beállító (`mov dword ptr [ecx], 0xc8b4b0`, `[ecx+0x68] = 0`), nem továbbító.
- ✅ A `0x00983670` (qshow-ablak) dekompilátuma: `CreateWindowExA`-szerű hívás 12 argumentummal, osztálynév `"ytWindow"`. A HWND a `[obj+0x6c]`-be kerül, a szülő a `[obj+0x78]`. Stílus: az alapágban `0x00cb0000` (param_2 = 0) vagy `0x00cf0000` (param_2 ≠ 0); az 1. ágban ex-stílus `0x80`, stílus `0x84000000`; a 2. ágban stílus `0x84080000`; a 3. ágban `0x40000000`. A WndProc nincs ebben a függvényben.
- ✅ A `0x0052d3c0` `ytUIEvent`-konstruktor (az előző körből, újra megerősítve).

**7. Codex-kész lista: nem adható.** A viselkedés attól függ, hogy K1, K2 és K4 futásidejű értéke mi. Erre épülő fejlesztői lista feltevés volna. Már most eldönthető a fejlesztői következmény: a Ctrl+5-ös időrend nem Shift-függő (L2), és a listát a nézet gyűjteményéből (`[this+0xeac]`) kell építeni, nem a Flipbook-rekordtárból (K3).

**8. Nyitott kérdések (ennek a körnek).**

- Q-A: melyik a Ctrl+5 normál útja. **LEZÁRVA** (1. pont).
- Q-B: kell-e Shift. **LEZÁRVA, feltételesen** (4. pont; a K4 értéke a feltétel).
- Q-C: felvétel ↔ kód. **LEZÁRVA:** összeférhető, feltételes (5. pont).
- Q-D: a K1 catdata `state`-sorainak futásidejű értéke és a `state` jelentése. **BLOKKOLT**: paszta-kör kell (a `0x006a5e60` hívóinak és a helyi db3-mintának az olvasása, a hívó futtatja). [blokkoló]
- Q-E: a K2 `[this+0x2c0]+0x154` mezőjének jelentése és írói. **BLOKKOLT**: paszta-kör kell a `+0x154` írói az `[this+0x2c0]` típusában. [blokkoló]
- Q-F: a K4 (`0x005675d0`) -1-ága. `Ghidra-kör kell: 0x004ae180 - a 0x005675d0 -1-ágának feltétele: mit ad a 0x004ae180, és mikor ad -1-et. [blokkoló]` **Új állapot (38.2.9):** részben lezárva: a `0x004ae180` -1-et ad, ha az index ≥ darabszám (feltételes); a `0x005675d0` -1-ága nyitott.
- Q-G: az L3 ág (`0x00891110`). `Ghidra-kör kell: 0x00891110 - a listaépítő tartalma, ha a [this+0xe64] == -1. [nem blokkolja a fő utat]` **Új állapot (38.2.9):** részben lezárva: a `0x00891110` tömb-másoló, nem listaépítő (feltételes); az L3 forrása és célja nyitott.
- Q-H: a qshow-ablak WndProc-ja. `Ghidra-kör kell: 0x00983330 - a ytWindow-sztringet használó függvény: osztályregisztráció vagy WndProc (hívója a 0x00982d60); a billentyű-fókusz kezelése. [blokkoló]` **Új állapot (38.2.9):** részben lezárva: a `0x00983330` nem WndProc (elvetett); az ytWindow WndProc és a regisztráció nyitott.

**Nyitott kérdések mérlege (38.2.8): 0 nyílt · 3 lezárva · 5 blokkolt · 0 hatókörön kívül · 0 csak nyitva.** Az örökölt tételek (38.2.7 nyitott listája) változatlanul a munkasorban maradnak.

**9. A jegy „Kész, ha” pontjai (#4443).**

- ⛔ A spec leírja a bemutató működését bizonyítékkal: **részben.** Megvan az indítási út, a kapuk, a qshow-ablak létrehozása és az átmenet lépéssora. Nincs meg a WndProc, a csúszka, az Exit célja, az időtartam, a kártyák tartalma és a futásidejű K-értékek.
- ⛔ Nézet ▸ Időrend és Ctrl+5 kattintásos teszttel: **nincs.** Ebben a körben kódot nem írtam.
- ⛔ Képernyőkép az eredetivel összevetve: **nincs.** A 188-as kép nincs a munkafában, és nincs implementáció.

**10. Javasolt fejlesztői irány (feltételes, még nem Codex-kész).** A Ctrl+5 és a menüpont ugyanabba a mód-1 ágba fut. A lista forrása a nézet gyűjteménye (L2), nem a kijelölés. Mielőtt a fejlesztés ezt építi, a K1, K2 és K4 futásidejű értékét kell megmérni egy valódi Picasa-futtatásban (Ctrl+5, kijelölés nélkül, a catdata és a `[this+0x2c0]` állapotának naplózásával).

#### 38.2.9 Ötödik kör: a K4 kapu, a qshow-ablak és az Időrend-váltás C-kódja (#4443, 2026-10-17)

**Kérdés.** Három Q-pont és az Időrend-váltás (`0x007fda00`) C-kódja. Q-F: a `0x005675d0` (K4) -1-ága. Q-G: az L3 ág `0x00891110` függvénye. Q-H: a qshow-ablak WndProc-ja vagy osztályregisztrációja (`0x00983330`).

**Forrás és módszer.** Két fájl, csak olvasás. Nincs új Ghidra-futás és nincs hálózat.
- `2026-10-17-blokkolok-4443-4400.txt` (a `~/picasapy-agent/referencia/ghidra/` alatt): `0x004ae180`, `0x00983330`, `0x00891110`. A `0x00430610`, a `0x009e0660` (#4400) és a `0x00812470` (másik jegy) nincs vizsgálva.
- `2026-10-17-idorend-film-sav.txt` (ugyanott): `0x007fda00`.

(A) a dekompilált C-kód olvasata. (B) a korábbi diszasszembly-olvasat: a 38.2.6 Időrend-váltás lépéssora és a 38.2.7 mód-1 ága. A hívóéleket a HÍVÓK és HÍVOTTAK lista adja. A `0x00983670` és a `0x005e8a70` dekompilátuma más köteg fájlban van (`2026-10-17-qshow-ctrl5.txt`, `2026-10-17-qshow-diavetites.txt`). Ezt a kör nem olvasta be, csak a jelenlétüket nézte meg.

**Eredmények.**

*`0x004ae180` (Q-F).* Zárolt, indexelt olvasás. A `this` objektum `+0x150` mezőjének tömbjéből adja vissza az i-edik elemet (4 bájt). A darabszám a `+0x154` mező értékének a fele; az alsó bit jelző. Ha i ≥ darabszám, a visszatérési érték 0xFFFFFFFF. Más ág nem ad -1-et. Egy tömbelem is lehet 0xFFFFFFFF, és akkor a két eset nem különíthető el. A zár: ha a `+0x0C` bájt nulla, virtuális zárat hív (vtábla +0x18 és +0x1C), különben kritikus szakaszt (+0x28). A függvény újrabelépő: a tulajdonos szál a `+0x20`, a mélység a `+0x24` mezőben van.

A hívóhelyek száma 16. A `0x005675d0` (K4) a `0x0056763a` címen hívja.

*A K4 -1-ága (Q-F).* A `0x004ae180` nem a K4 -1-ága. Ez a `0x005675d0` egyik hívott függvénye. Hogy a `0x005675d0` mikor ad -1-et, az a saját kódjában dől el. Ez a kód nincs a kötegben, és a hívott index sem látszik.

*`0x00891110` (Q-G).* Nem listaépítő, hanem tömb-másoló. A forrás tömbjét változatlanul bemásolja a céltömbbe (EAX). Lépései:
1. Ha a cél és a forrás azonos, nem csinál semmit.
2. A forrás jelzőbitjétől függően hív egy függvényt (`0x0074cf40` vagy `0x009829f0`). Ezek nevét nem ismerjük.
3. Ha a forrás darabszáma 0, vagy 0x1FFFFFFF fölötti, a cél kiürül.
4. Különben igazítja a kapacitást (újrafoglal vagy felszabadít), beállítja a darabszámot, és darabszám × 4 bájtot másol.

A tartalom tehát a forrásé. Hogy mi a forrás és a cél az L3 ágban, azt a hívóhely dönti el (`0x005e92a9`, FUN_005e8a70). Ennek kódja a `2026-10-17-qshow-diavetites.txt`-ben van, ezt a kör nem olvasta be.

*`0x00983330` (Q-H).* Nem WndProc. Nincs benne billentyűkezelés, és osztályregisztráció sem látszik. Mit csinál:
1. Két osztálynevet ("ytWindow", "ytDialog") ad át egy függvénymutatón (`DAT_00d69538`) hívott műveletnek.
2. Egy másik függvénymutatóval (`DAT_00d69528`) lekérdez egy értéket az `uStack_14` ablakhoz (feltételezés: HWND), `-4` paraméterrel. A -4 (0xFFFFFFFC) a Win32 GWL_WNDPROC értéke, tehát a lekérdezés feltehetően a window procedure.
3. Az értéket három másik értékkel veti össze, köztük egy globálissal és egy fix címmel. Ha egyezik valamelyikkel, 1-et ad, különben 0-t.

A hívott függvények nevét a dekompilátum nem adja. Az `uStack_14` és a `puStack_3c` értékét a függvény nem állítja be, ezért az összevetés bemenete nincs igazolva. Hívói: `0x00982dc2` (FUN_00982d60) és `0x00a57325` (FUN_00a572f0).

*Az Időrend-váltás (`0x007fda00`).* A C-kód megerősíti a 38.2.6 lépéssorát. Két lépés hiányzott belőle:
1. Kapu: a `[this+0x2d8]` bájt és a `[this+0x538]` mutató nem nulla. Ha nem, a függvény nem csinál semmit.
2. A `[this+0x3f4]`, ha negatív, 0 lesz.
3. **Új:** hívja a `0x0097e510(0)` függvényt (nincs a kötegben).
4. **Új:** `[this+0x3be] = 1` (bájt, a jelentése nincs megnevezve).
5. A QueryPerformanceCounter értéke double-ként a `[this+0x430]` mezőbe kerül.
6. Hívja a `0x00802230(this, 1)` függvényt. Ez az animátor, nincs a kötegben.
7. `[this+0x3ba]` és `[this+0x3bb]` 0, `[this+0x3b8]` és `[this+0x3b9]` 1.

Billentyű-lekérdezés (GetAsyncKeyState) és Ctrl/Shift-ellenőrzés nincs benne. A függvény csak az átmenetet indítja. Vége, kártyái és kilépése nincs benne. Hívói: `0x007fde80`, `0x00802630`, `0x008032e0` és `0x008037e0`. A mód-1 hívás a `0x008037e0`-ban van (`0x008039e7`). Az első három szerepe nincs vizsgálva.

**Cáfoló kísérletek.**
1. „A `0x004ae180` a K4 -1-ága.” **Cáfolva:** a `0x005675d0` hívott függvénye.
2. „A `0x00983330` a ytWindow WndProc-ja.” **Cáfolva:** nincs benne üzenetkezelés, csak 1 vagy 0 értéket ad.
3. „A `0x00891110` listát épít.” **Cáfolva:** másol.
4. „Az Időrend-váltást Shift vagy Ctrl szűri.” **Cáfolva** ebben a függvényben. A Shift-kapu a `0x005e8a70`-ben van (38.2.8).
5. „A `param_2 = 1` nem animált ágat jelez” (38.2.6). **Visszavonva**, lásd a Helyesbítéseket.

**Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| `0x004ae180`: zárolt, indexelt olvasás; -1 pontosan akkor, ha index ≥ darabszám | feltételes | A (egy út) |
| `0x004ae180` a K4 -1-ága | elvetett | A: a `0x005675d0` hívottja |
| `0x00891110`: tömb-másolás | feltételes | A (egy út) |
| a 38.2.8 „listaépítés” neve a `0x00891110`-re | elvetett | A |
| `0x00983330` nem WndProc | elvetett | A |
| `0x00983330`: két osztálynév, `-4` lekérdezés, 1/0 visszatérés | feltételes | A; a hívott függvények nevei hiányoznak |
| `0x00983330` nem kezel billentyűfókuszt | elvetett | A |
| `0x00983330` hívói: `0x00982dc2`, `0x00a57325` | feltételes | A (HÍVÓK); a 38.2.8 Q-H sora a `0x00982d60` hívót említi, de az nem független út |
| `0x007fda00` lépéssora (1., 2., 5., 6., 7. pont) | megerősített | A (C) + B (38.2.6 lépéssor) |
| `0x007fda00` 3. és 4. lépése (`0x0097e510(0)`, `+0x3be = 1`) | feltételes | A; a B-listában nincs |
| `0x007fda00` nem néz billentyűt | megerősített | A + B (a 38.2.6 listában sincs) |
| `0x007fda00` mód-1 hívója a `0x008037e0` | megerősített | A (HÍVÓK) + B (38.2.7 mód-1 ága) |
| az átmenet időzített (a kezdőidő QPC-ből) | feltételes | A; az animátor (`0x00802230`) nincs a kötegben |

**Összefüggés (feltételezés, nem mérve).** A `0x004ae180` darabszám-mezője a `+0x154` eltolásban van. A 38.2.8 K2 ugyanezen az eltoláson (`[this+0x2c0]+0x154`) vizsgálja a „nem 0 és nem 1” feltételt. Ha a `[this+0x2c0]` objektum ugyanilyen tömb, a K2 feltétele azt jelenti, hogy a darabszám nem nulla. A `[this+0x2c0]` típusát nem láttuk. Ellenőrzés: a `+0x154` írói (Q-E, paszta).

**Helyesbítések.**
- A 38.2.8 K-tábla L3 sorában a „listaépítés a `0x00891110` függvénnyel” helyesbítve: a `0x00891110` másol, nem épít listát.
- A 38.2.8 Q-F előfeltétele („a `0x004ae180` a K4 -1-ága”) nem igaz: a `0x004ae180` a `0x005675d0` hívott függvénye.
- A 38.2.6 Időrend-váltás lépéssora kihagyta a `0x0097e510(0)` hívást és a `[this+0x3be] = 1` beállítást.
- A 38.2.6 cáfoló 3. pontja („`param_2 = 1` nem animált ágat jelez”) visszavonva. Alapja a „nem animált ág” címke volt, amelyet a 38.2.7 már visszavont. Az animátor viselkedése nyitott.
- A 38.2.2 kérése a `0x007fda00`-ra (az átmenet vizuális tartalma): részben válaszolva. A lépéssor kész, a vizuális tartalom a `0x00802230`-ban van.

**Nyitott kérdések (a hívó futtatja).**
- `Ghidra-kör kell: 0x005675d0 - a K4 -1-ága: melyik feltételnél ad -1-et, és mit kezd a 0x004ae180 visszatérésével (hívóhely: 0x0056763a). [blokkoló]` **Új állapot (38.2.10):** a -1 négy feltétele ismert; a futásidejű értékük nincs meg (Q-J).
- `Ghidra-kör kell: 0x00982d60 - a 0x00983330 hívója (0x00982dc2): mit tesz a 0/1 eredménnyel, és regisztrálja-e az ytWindow osztályt (lpfnWndProc). [blokkoló]` **Új állapot (38.2.10):** a 0x00982d60 nem regisztrál; a WndProc-ot az EDI adja. A regisztráció jelöltje a 0x00980670 (Q-K).
- `Ghidra-kör kell: 0x00802230 - az Időrend-átmenet animátora: a param_2 = 1 jelentése és az időzítés. [blokkoló]` A 38.2.5 és 38.2.6 kérése változatlan.
- `Ghidra-kör kell: 0x0097e510 - a 0x007fda00 első hívása, argumentum 0: mit csinál. [nem blokkolja a fő utat]` **Új állapot (38.2.10):** lezárva: ShowCursor-számláló (0 látható, -1 rejtett).
- Olvasás, nem Ghidra: a `FUN_005e8a70` 0x005e92a9 körüli L3 ága a `2026-10-17-qshow-diavetites.txt`-ben. Ebből derül ki a `0x00891110` forrása és célja. [nem blokkolja a fő utat] **Új állapot (38.2.10):** a 0x00891110 másol. A forrás és a cél a hívóhelyen van, az nincs a kötegben (Q-N). A kijelölés nélküli Ctrl+5 esetén ez blokkoló.
- A `0x00983670` (qshow-ablak létrehozása) a `2026-10-17-qshow-ctrl5.txt`-ben van. A WndProc-kérdést ott lehet olvasni; ezt a kör nem olvasta be. **Új állapot (38.2.10):** beolvasva; egyezik a K4 fájl változatával. A WndProc nincs benne.

**Nyitott kérdések mérlege (38.2.9):** 0 nyílt · 5 lezárva · 5 blokkolt · 0 hatókörön kívül · 0 csak nyitva.

**A Q-pontok új állapota.**
- **Q-F:** részben lezárva. A `0x004ae180` -1-et ad, ha az index ≥ darabszám (feltételes). A `0x005675d0` -1-ága nyitott.
- **Q-G:** részben lezárva. A `0x00891110` tömb-másoló (feltételes). Az L3 forrása és célja nyitott.
- **Q-H:** részben lezárva. A `0x00983330` nem WndProc. Az ytWindow WndProc és a regisztráció nyitott.

**Codex-kész lista: nem adható.** A K1, K2 és K4 futásidejű értéke nincs megmérve, a Q-F és a Q-H nyitott.

#### 38.2.10 Hatodik kör: a K4 -1-ága, az ytWindow regisztrációja és az L3 ág (#4443, 2026-10-17)

**Kérdés.** A 38.2.9 nyitott listájából négy pont: (a) a K4 (`0x005675d0`) mikor ad -1-et, és mit jelent ez kijelölés nélkül; (b) melyik függvény regisztrálja az ytWindow osztályt, mi a WndProc címe, és ki kezeli a billentyű-fókuszt; (c) mi a `0x0097e510` szerepe; (d) mi az L3 ág (`0x005e92a9`, a `0x00891110` hívása) forrása és célja. Végül: a K1, K2 és K4 alapján eldönthető-e, hogy a Ctrl+5 kijelölés nélkül qshow-t nyit-e.

**Forrás és módszer.** Csak olvasás. Nincs új Ghidra-futás és nincs hálózat. A fájlok a `~/picasapy-agent/referencia/ghidra/` mappában vannak:
- `2026-10-17-hog-qshow-k4.txt`: `0x005675d0`, `0x00982d60`, `0x0097e510`, `0x00983670`. A `0x0088c1a0` nincs vizsgálva (ez a #4194-hez tartozik).
- `2026-10-17-blokkolok-4443-4400.txt`: `0x004ae180`, `0x00983330`, `0x00891110`. A 38.2.9 forrása; az (a), (b) és (d) ponthoz kellett a törzsük.
- `2026-10-17-qshow-diavetites.txt`: `FUN_005e8a70`, két dekompilátum, ugyanaz a függvény. Az L3 ág és a farok. A sorszámok az első dekompilátumra vonatkoznak.
- `2026-10-17-qshow-ctrl5.txt`: `0x00983670` (2441-2541. sor), összevetve a K4 fájl változatával.
- `2026-10-17-idorend-film-sav.txt`: `0x007fda00`, a `0x0097e510(0)` hívás helye.

Nincs megnézve: `0x00980670`, `0x00717bb0`, `0x007164b0`, a `[this+0x2a4]` objektum +0x44 függvénye, és a `0x00982d60` hívóinak EDI-je. A `0x00802230` (animátor) a `2026-10-17-qshow-2.txt` fájlban van; ebben a körben nem olvastam.

**Eredmények.**

*(a) A K4 (`0x005675d0`).* A függvény a `[this+0xeac]` lánc csomópontjain megy végig. Ha az első olyan csomópont, amelynek `+0x213` bájtja nem nulla, a `+0x244` mezője is nem nulla, a K4 0-t ad, és nem épít újra. Minden más esetben a lánc felszabadul (vtábla `+8` hívás), és a függvény négy ponton ad -1-et:
1. `X = [P+0x2fc]`, ahol `P = [this+0xea0]`. Ha `X = 0`, -1.
2. Ha `[X+0x2c0] = 0`, -1.
3. Ha `FUN_004ae180([P+0x2f0]) = -1`, -1. Ez az index túllépése. Egy tárolt 0xFFFFFFFF elem is ide fut, a két eset nem különíthető el.
4. A `[this+0x2a4]` +0x44 függvényének hívása után `[this+0xeac] = 0`, -1. Ez a 38.2.8 „újraépítés nem sikerül" esete.

Ha az újraépítés (`0x00717bb0`) lefut, a K4 0-t ad. Ezért a -1-et adó K4 is törli a régi láncot.

Ctrl+5 esetén a -1 azt jelenti, hogy a `0x005e8a70` kilép: nincs qshow és nincs hibaüzenet. Hogy kijelölés nélkül a K4 -1-et ad-e, a kötegből nem dől el. A K4 törzse nem olvassa a `[this+0xe64]` mezőt (azt használja a szűrő és az L3 ág), de a négy feltétel mindegyike futásidejű értéktől függ.

Ha a K4 nem 0, a `0x005e8a70` azonnal visszaadja ugyanazt az értéket (332-336. sor). Nincs IDS_MUST_SELECT üzenet, és qshow sem nyílik.

*(b) Az ytWindow és a WndProc.* Az ytWindow-hoz tartozó három olvasott függvényben nincs olyan hívás, amely egy argumentumot kap, mint a RegisterClass. Ezek:
- `0x00983670` (qshow-ablak): a CreateWindowExA alakú függvényt hívja 12 argumentummal, a sorrend a CreateWindowExA-val egyezik. Osztálynév: `"ytWindow"`. Regisztrációt nem végez. Ha a hívás 0-t ad, meghívja a `0x00980670`-et, és utána a `[this+0x6c]` nem nulla értékét várja. Ez arra utal, hogy a `0x00980670` hwnd-t állíthat be, de ez feltételezés.
- `0x00983330`: a `DAT_00d69538`-at kétszer hívja, `"ytWindow"` és `"ytDialog"` névvel, három argumentummal. Ez GetClassInfo-alakú hívás. Utána a `DAT_00d69528`-cal (`-4`) lekérdez egy értéket. 1-et ad, ha ez egyezik a három összehasonlított érték egyikével, különben 0-t. Regisztrációt nem végez.
- `0x00982d60` (a `0x00983330` hívója): a `"ytWindow"` nevű `DAT_00d69538`-hívás lekérdezés. Utána a `DAT_00d69524` `(hwnd, -4, EDI)` hívásával a `[this+0x6c]` ablakon beállítja az EDI-t új WndProc-nak. A régi WndProc-ot a `[this+0x34]` őrzi. A `DAT_00d69524`-et 2 és 3 argumentummal is hívja, ezért az API neve (feltételezés: SetWindowLongA) nincs megerősítve.

Eredmény:
- **Regisztráció:** az olvasott kódban nincs. A következő jelölt a `0x00980670`. A teljes bináris-ban nem kerestem.
- **WndProc címe:** nincs meg. A `0x00982d60` az EDI-ből veszi. A hívói (`FUN_00982d00`, `FUN_007360b0`, `FUN_00736a50`, `FUN_00aa5100`) nincsenek a kötegben, így az EDI értéke sem ismert.
- **Billentyű-fókusz** (nyíl, szóköz, Home/End, Escape): nincs meg. Az olvasott függvények egyike sem kezel billentyű-üzenetet, a WndProc nincs a kötegben.

*(c) A `0x0097e510`.* ShowCursor-számlálót állít. Win32 szerint a 0 vagy annál nagyobb érték látható, a -1 rejtett. Ha az argumentum nagyobb, mint 0, a számlálót 0-ra viszi. Ha 0 vagy kisebb, -1-re. A `0x007fda00` az átmenet elején 0-val hívja (a `0x007fda2a` címen), tehát az átmenet alatt a kurzor rejtett. A 11 hívóból csak a `0x007fda00` van vizsgálva. A kurzor visszaállítása (1 argumentummal) nincs a kötegben.

*(d) Az L3 ág (`0x005e92a9`).* A C-ben a hívás argumentum nélkül látszik: `FUN_00891110();`. A `0x00891110` a célját az EAX-ben (`in_EAX`), a forrását az első verem-argumentumban (`param_1`) kapja. Másol: a forrás darabszám × 4 bájtját a célba (`_memcpy`), a cél méretét előbb igazítva. Listát nem épít. A cél alakja {mutató, darabszám << 1 | jelző}.

A forrás és a cél a hívóhelyen dől el. Az EAX és a verem értéke nincs a kötegben, ezért ez nincs igazolva. Erős feltételezés:
- **Cél:** a kimeneti pár, `iStack_d4` és `uStack_d0`. Ugyanez az alak (az első dekompilátum 444-447. sora), és a farok K5 ellenőrzése (532. sor) ezt olvassa. Ha a cél más lenne, az L3 ágban a K5 a 212. sorban nullázott értéket látná, és az L3 ág sosem nyitna qshow-t.
- **Forrás:** az L2-lista pár, `local_c0` és `local_bc`. A 38.2.8 szerint a `0x007164b0` ezt tölti, és a szűrő is ebből olvas (358. sor).

Így az L3 ág a teljes L2-listát másolja, szűrés nélkül. Ez azon a feltevésen áll, hogy a `[this+0xe64] == -1` azt jelenti: nincs kijelölt elem. A szűrő a `[this+0xe64]` értékű elemet keresi, ezért ez indokolt, de nincs igazolva.

Az L3 nem zsákutca. A `goto` után a közös farok fut: a K5, és ha a lista nem üres, a `0x008037e0` (qshow).

**Helyesbítés.** A 38.2.8 K4 sora szerint a -1 az újraépítés hibájából jön. Ez hiányos: a négy feltételből három a vtábla-hívás előtt van (1-3. pont).

**Megerősítés.** A 38.2.8 K3 és K5 sora helyes. A Shift-ág a 330. sorban a farokra ugrik, a K4 csak a Shift nélküli ágban fut. A `0x008037e0` hívása a K5 után áll (604. sor), nem Ctrl-feltételhez kötött. A `cStack_d9` blokk (455-483. sor) a flipbook-listát rajzolja. Ezt nem vizsgáltam tovább.

**Cáfoló kísérletek.**
1. „A K4 -1-e csak az újraépítés hibájától függ." **Cáfolva:** az 1-3. feltétel a vtábla-hívás előtt is -1-et ad.
2. „A K4 -1 után IDS_MUST_SELECT üzenet jelenik meg." **Cáfolva:** a 332-336. sor visszatér, nincs üzenet ebben a függvényben.
3. „A `0x00983330` vagy a `0x00982d60` regisztrálja az ytWindow-t." **Cáfolva** az olvasott kódban: csak lekérdezés és WndProc-csere van.
4. „A `0x008037e0` hívása Ctrl-feltételes." **Cáfolva:** a hívás a K5 else-ágában van (604. sor), nem a `cStack_d9` blokkban.
5. „Az L3 ág zsákutca." **Cáfolva:** a közös farok a K5 után a `0x008037e0`-t hívhatja.

**Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| K4: az 1-3. -1 feltétel (`X = 0`, `[X+0x2c0] = 0`, `0x004ae180 = -1`) | feltételes | A (C) |
| K4: a 4. -1 feltétel (a vtábla-hívás után `[this+0xeac] = 0`) | megerősített | A (C) + B (38.2.8 K4 sora) |
| K4 nem 0: a `0x005e8a70` azonnal visszatér, nincs IDS_MUST_SELECT | megerősített | A (332-336. sor) + B (38.2.8 K4 sora) |
| K4 futásidejű értéke kijelölés nélkül | nincs meg | - |
| a K4 törzse nem olvassa a `[this+0xe64]` mezőt | feltételes | A (a K4 teljes törzse; a hívott függvények nincsenek benne) |
| `0x0097e510`: argumentum > 0 → 0 (látható), egyébként -1 (rejtett) | feltételes | A (C) + ShowCursor importnév |
| `0x007fda00` az átmenet elején hívja a `0x0097e510(0)`-t | feltételes | A (C) |
| `0x00891110`: másolás, cél EAX, forrás verem-argumentum | feltételes | A (egy út) |
| L3 cél: a kimeneti pár (`iStack_d4`, `uStack_d0`) | feltételezés | C-ből következtetve; az EAX nincs meg |
| L3 forrás: az L2-lista pár (`local_c0`, `local_bc`) | feltételezés | C-ből következtetve; a verem-argumentum nincs meg |
| `0x00983670`: CreateWindowExA alak, `"ytWindow"` | feltételes | A (két dekompilátum, egy forrás) |
| `0x00983330`, `0x00982d60`: nincs ytWindow-regisztráció | feltételes | A (három argumentumos lekérdezés; az API neve nincs) |
| `0x00982d60`: a WndProc az EDI | feltételes | A |
| a WndProc címe, a billentyű-fókusz | nincs meg | - |
| `0x008037e0` a K5 után van, nem Ctrl-feltételes | megerősített | A (C) + B (38.2.8 K5 és „vége" sora) |

**Következtetés: Ctrl+5 kijelölés nélkül qshow-t nyit-e?** A kötegből nem dönthető el. A kód feltételes választ ad (a sorszámok az első dekompilátumra vonatkoznak):
- Ha K1 hamis, vagy a K2 feltétel nem teljesül: IDS_MUST_SELECT, nincs qshow (213-230. sor).
- Ha K4 = -1: a függvény csendben kilép. Nincs qshow és nincs üzenet.
- Ha K4 = 0: a lánc biztosan létezik, és az L2-lista épül. Ha a lista üres: IDS_MUST_SELECT (K5).
- Ha K1 ≠ 0, a K2 feltétel teljesül, K4 = 0, és a lista nem üres: qshow nyílik.

Ha a `[this+0xe64] == -1` valóban azt jelenti, hogy nincs kijelölt elem, a kijelölés nélküli eset az L3 ágra megy, és a teljes L2-lista kerül a qshow-ba. Ekkor nincs külön „nincs kijelölés" hibaág. Ez feltételezés, nem bizonyíték.

Hiányzik: K1 futásidejű értéke (Q-D), K2 `[this+0x2c0]+0x154` értéke (Q-E), a K4 négy feltételének értéke (Q-J), az L2-lista darabszáma (a `+0x5a` jelző jelentése nincs megmérve, 38.2.8), és az L3 forrása és célja (Q-N).

**Nyitott kérdések (38.2.10).**
- Q-I: a K4 -1 négy feltétele. **LEZÁRVA** (1-4. pont). A futásidejű értékük nincs meg (Q-J).
- Q-J: a K4 futásidejű értéke kijelölés nélkül. **BLOKKOLT:** `Ghidra-kör kell: 0x0056763a - a 0x004ae180 hívás előtti EAX (this): melyik objektum tömbjét olvassa a K4. [blokkoló]` Emellett paszta-kör kell a `[this+0x2a4]` +0x44 függvényére (a címe nincs a kötegben). [blokkoló]
- Q-K: az ytWindow regisztrációja. **BLOKKOLT:** `Ghidra-kör kell: 0x00980670 - a CreateWindowExA hibaágában hívott függvény: regisztrálja-e az ytWindow osztályt, és állít-e be hwnd-t a [this+0x6c]-be. [blokkoló]` **Új állapot (38.2.11):** részben lezárva: a `0x00980670` nem regisztrálja az ytWindow-t (feltételesen), a regisztráció helye nincs meg.
- Q-L: a WndProc címe és a billentyű-fókusz. **BLOKKOLT:** `Ghidra-kör kell: 0x00982d00 - a 0x00982d60 hívója (0x00982d48): mi van az EDI-ben a hívás előtt. [blokkoló]` **Új állapot (38.2.11):** a WndProc címe még nincs meg; az EDI forrása a `0x00982d00` két hívójánál van (`0x00735d96`, `0x00a70cb4`), és azok nincsenek a kötegben.
- Q-M: a `0x0097e510` szerepe. **LEZÁRVA** (c. pont). A visszaállító hívás helye nincs a kötegben, ez nem blokkol.
- Q-N: az L3 forrása és célja. **BLOKKOLT:** `Ghidra-kör kell: 0x005e92a9 - az L3 hívás előtti EAX (cél) és a verembe tett forrás-argumentum: melyik lista másolódik. [blokkoló]` A dekompilátum nem mutatja ezeket, ezért a 0x005e92a0-0x005e92a9 tartomány diszasszembly-olvasata kell.
- Q-O: Ctrl+5 kijelölés nélkül qshow-t nyit-e. **BLOKKOLT** (Q-D, Q-E, Q-J, Q-N).
- Q-P: a `0x00802230` (animátor). **HATÓKÖRÖN KÍVÜL** ebben a körben.

**Nyitott kérdések mérlege (38.2.10):** 0 nyílt · 2 lezárva · 5 blokkolt · 1 hatókörön kívül · 0 csak nyitva.

#### 38.2.11 Hetedik kör: az ytWindow regisztrációja és a WndProc (#4443, 2026-10-17)

**Kérdés.** Két pont a 38.2.10 nyitott listájából. (a) Regisztrálja-e a `0x00980670` az ytWindow osztályt, és állít-e hwnd-t a `[this+0x6c]`-be (ez a 38.2.10 feltételezése volt). (b) Milyen EDI-t ad a `0x00982d00` a `0x00982d60`-nak, vagyis mi a WndProc címe.

**Forrás és módszer.** Csak olvasás. Nincs új Ghidra-futás és nincs hálózat. A fájlok a `~/picasapy-agent/referencia/ghidra/` mappában vannak:
- `2026-10-17-hog-racs-ytwindow.txt` (1): a `0x00980670` és a `0x00982d00` szakasza (HÍVÓK, HÍVOTTAK, C-kód).
- `2026-10-17-hog-qshow-k4.txt` (2): a `0x00982d60` HÍVÓK-listája és C-kódja (306-376. sor).
- `2026-10-17-qshow-ctrl5.txt` (3): a `0x00983670` CreateWindowEx-alakú hívása és a hibaág (2524-2532. sor, keresési kivonat).

Nincs megnézve: a `0x00980670` által hívott `FUN_00512030`, `FUN_0097de80` és `FUN_009ae560` belseje; a `0x00982d00` két hívóhelye (`0x00735d96`, `0x00a70cb4`).

**Eredmények.**

*A `0x00980670` (Q-K).* Hibajelentő. Ha a `GetLastError` nem nulla, a `FormatMessageA` szöveget készít. Egy MessageBox-alakú hívás (`FUN_0097de80`) hibaablakot jelenít meg, a cím az `ytApp::ErrorTitle` kulcsú szöveg. Végül a `LocalFree` felszabadít. Ezután mindig meghívja a `FUN_00512030`-at. Nincs argumentuma, nem kap `this`-t, és nem ír a `[this+0x6c]` mezőbe. Nincs benne `RegisterClass`-alakú hívás. Kilenc hívója van; az egyik a `0x00983670` (`0x009837d2`).

*A `0x00983670` hibaága.* A CreateWindowEx-alakú hívás (indirekt, `DAT_00d695c8`, osztálynév `"ytWindow"`) 0-t ad, ekkor hívódik a `0x00980670`. A feltételes ág csak akkor fut, ha a `[this+0x6c]` a `0x00980670` hívása után sem nulla. A `0x00980670` nem írja a mezőt, ezért a feltétel a hibaágban hamis marad.

*A `0x00982d00` (Q-L).* Konstruktor-jellegű. Beállítja a `ytWindow::vftable`-t, és nullázza az EAX-ben kapott `this` mezőit. Ezután meghívja a `0x00982d60`-at (`0x00982d48`). A C-kódban nem állít be EDI-t. Hívói a `FUN_00735d90` (`0x00735d96`) és a `FUN_00a70cb0` (`0x00a70cb4`); ezek nincsenek a kötegben.

*A `0x00982d60` (WndProc-csere).* A C-kód szerint:
1. A hwnd-t (EAX) a `[this+0x6c]`-be írja. Ha ez nulla, visszatér.
2. Ha a `0x00983330` nem nulla értéket ad, és a `GetWindowLongA(hwnd, -21)` nem nulla, meghívja a `0x00982e60`-at, majd visszatér.
3. Ha a `[this+0x34]` nulla, a régi WndProc-ot (`DAT_00d69528(hwnd, -4)`) oda menti. Az osztályinfó-lekérdezés után, ha a régi eljárás megegyezik az EDI-vel vagy a `DAT_00983940` fix címmel, a mezőt nullázza.
4. A `DAT_00d69524(hwnd, -4, EDI)` hívás az EDI-t állítja be WndProc-ként. Az alakja SetWindowLongA-é, de a név nincs megerősítve.

*A regiszterek.* A `0x00982d00` a `this`-t EAX-ben kezeli, a `0x00982d60` a `this`-t ESI-ben és a hwnd-t EAX-ben. A két C-kód nem illeszkedik egymáshoz. A `0x00982d48`-as hívás előtti EAX, ESI és EDI értéke nincs megállapítva.

*A regisztráció helye.* Az olvasott részekben nincs. A `0x00982d60` GetClassInfo-alakú hívással csak lekérdezi az osztályt (`DAT_00d69538`, `"ytWindow"`). A teljes binárisban nem kerestük.

**Helyesbítés.** A 38.2.10 szerint a `0x00980670` hwnd-t állíthat be a `[this+0x6c]`-be. A C-kód szerint nem ír oda. A 38.2.10 többi állítása a `0x00982d60`-ról (EDI-ből veszi a WndProc-ot, a régi eljárás a `[this+0x34]`-ben) egyezik a C-kóddal, de feltételes marad.

**Cáfoló kísérletek.**
1. „A `0x00980670` regisztrálja az ytWindow osztályt.” **Cáfolva** a közvetlen C-kódban: nincs `RegisterClass`-alakú hívás, a közvetlen külső hívottak (`FormatMessageA`, `GetLastError`, `LocalFree`) nem regisztrálnak. Feltétel: a `FUN_00512030` belsejét nem néztük.
2. „A `0x00980670` hwnd-t állít be a `[this+0x6c]`-be.” **Cáfolva** a C-kódban: a függvény nem ír a mezőbe.
3. „A `0x00982d00` állítja be az EDI-t a `0x00982d60`-nak.” **Nem igazolódott:** a C-kód nem mutat EDI-írást. Ez a dekompilátum hiánya is lehet, ezért ez sem cáfolat, sem igazolás.
4. „A `0x00982d00` az ytWindow regisztrációja.” **Cáfolva:** vtable-írás és mezőnullázás van benne, osztályregisztráció nincs.

**Bizonyítottsági fok.**

A zárójeles számok a forrásfájlokat jelölik (lásd: Forrás és módszer).

| állítás | fok | alap |
|---|---|---|
| `0x00980670`: hibajelentő (`GetLastError`, `FormatMessageA`, hibaablak, `LocalFree`), utána `FUN_00512030` | feltételes | (1) C-kód; a HÍVOTTAK-lista ugyanebből a fájlból jön |
| `0x00980670` nem regisztrálja az ytWindow-t | feltételes | (1) C-kód; a `FUN_00512030` belseje nincs megnézve |
| `0x00980670` nem ír a `[this+0x6c]` mezőbe | feltételes | (1) C-kód |
| `0x00983670` a hibaágban hívja a `0x00980670`-et | megerősített | (3) C-kód, 2528. sor + (1) HÍVÓK: `0x009837d2` |
| `0x00983670`: CreateWindowEx-alakú hívás, osztálynév `"ytWindow"` | feltételes | (3) C-kód |
| `0x00982d00` hívja a `0x00982d60`-at (`0x00982d48`) | megerősített | (1) C-kód + (2) HÍVÓK: `0x00982d48` |
| `0x00982d00`: vtable-írás és mezőnullázás, osztályregisztráció nincs | feltételes | (1) C-kód |
| `0x00982d00` nem állít be EDI-t | feltételes | (1) C-kód (nincs regiszter-írás a C-ben) |
| `0x00982d60`: hwnd nulla esetén visszatér; a WndProc-csere az EDI-vel, `DAT_00d69524` (-4) | feltételes | (2) C-kód, 332-373. sor; a függvénynév nincs megerősítve |
| `0x00982d60`: a régi WndProc a `[this+0x34]` mezőben | feltételes | (2) C-kód, 364-366. sor |
| a `0x00982d00` és a `0x00982d60` regiszter-használata nem illeszkedik | feltételes | (1) és (2) C-kódja |
| a WndProc címe, a billentyű-fókusz | nincs meg | - |
| az ytWindow regisztrációjának helye | nincs meg | - |

**Következtetés.**
- A `0x00980670` nem regisztrálja az ytWindow osztályt (feltételesen). Hibajelentő.
- A WndProc címe nincs meg. A `0x00982d60` az EDI-t állítja be új WndProc-ként, ha a hwnd nem nulla, és a régi eljárást elmenti. Ez alosztályozásra utal, de nem dönti el, hogy az EDI az eredeti WndProc vagy egy alosztályozó eljárás.
- Az EDI értéke a `0x00982d48` előtt nincs megállapítva.
- A billentyű-fókusz nincs meg.

**Hiányzik.**
- A `0x00982d48` előtti EAX, ESI és EDI értéke.
- A `0x00735d96` és a `0x00a70cb4` körüli diszasszembly az EAX, az ESI és az EDI állapotához.
- Az `"ytWindow"` sztring xref-je, hogy a regisztráció helye megtalálható legyen.

Ghidra-kör a WndProc-ra most nem kérhető, mert a címe nincs meg. Ha a hívó kéri, a következő lépés a két hívóhely és az `"ytWindow"` xref-je.

**Nyitott kérdések (38.2.11).**
- Q-K1: regisztrálja-e a `0x00980670` az ytWindow-t. **LEZÁRVA**, feltételesen (1. cáfolat).
- Q-K2: állít-e a `0x00980670` hwnd-t. **LEZÁRVA** (2. cáfolat).
- Q-K3: hol van az ytWindow regisztrációja. **CSAK NYITVA.** Feltételesen nem blokkolja a billentyű-kérdést, mert a `0x00982d60` a saját WndProc-ot állítja be.
- Q-L: mi a WndProc címe, és ki kezeli a billentyű-fókuszt. **BLOKKOLT:** az EDI forrása hiányzik.

**Nyitott kérdések mérlege (38.2.11):** 0 nyílt · 2 lezárva · 1 blokkolt · 0 hatókörön kívül · 1 csak nyitva.

#### 38.2.12 Nyolcadik kör: a WndProc helye, és a qshow a Colab-környezetben (#4443, 2026-10-17)

**Kérdés.** A 38.2.11 után nyitott maradt, hol regisztrálják az ytWindow osztályt, mi a WndProc, és mit csinálnak a billentyűk a Ctrl+5-tel nyitott qshow ablakban.

**Forrás.**
- `referencia/ghidra/2026-10-17-ytwindow-hivatkozasok.txt`: az `"ytWindow"` sztring (`0x00c7f35c`) minden utasításbeli hivatkozása (Ghidra, konstans-keresés) és a tartalmazó függvények C-kódja.
- `referencia/ghidra/2026-10-17-ytwindow-wndproc.txt` és `referencia/ghidra/2026-10-17-ytwindow-uzenetek.txt`: a WndProc és a `OneUpUI` vtábla `+0x1c` bejegyzésének C-kódja.
- Colab-felvétel, picasa-colab-jobs job-189: alapállapot, Ctrl+5 kijelölés nélkül, majd Right, Right, Left, space, space, Home, End, Escape, lépésenként képernyőképpel és ablaklistával.
- Colab-felvétel, job-191: ugyanígy, majd kattintás a képernyő vezérlőire: következő (kétszer), előző, lejátszás (indítás, 10 mp, leállítás), egy kártya, rács-vissza.

**Eredmények.**
1. **Regisztráció (megerősített).** A `FUN_009838b0` kitölti a WNDCLASS-t: `style = 0x400b`, `lpfnWndProc = 0x00983940`, `cbWndExtra = 4`, ikon `IDI_APPLICATION` (`LoadIconA(0, 0x7f00)`), háttér `GetStockObject(0)`, osztálynév `"ytWindow"`, majd a `DAT_00d69530` mutatón át regisztrál. A konstans-keresés három hivatkozást talált: kettő a `0x00983670` (ablaklétrehozás), egy ez a függvény. Két független út: a sztring hivatkozásai és a WNDCLASS-mezők sorrendje.
2. **A WndProc (`0x00983940`) csak továbbít (megerősített a C-kódból).** A `GetWindowLongA(hwnd, -21)` (felhasználói adat) objektum vtáblájának `+0x1c` metódusát hívja az üzenettel. Ha az `0xf4241`-et ad vagy nincs objektum, a `DAT_00d69554` alapeljárás fut; az `1000000` visszatérés 1-re fordul. A billentyűkezelés tehát az ablakhoz kötött objektum osztályában van.
3. **A `OneUpUI` vtábla nem az ablakobjektumé (feltételes).** A `0x00cbd5c4 + 0x1c` bejegyzés a `0x0097b5f0`, amely csak egy kritikus szakaszt enged el. Az ablakhoz kötött objektum osztálya és vtáblája NINCS MEG; a `-21` mezőt író hívás a `0x00983670` körül keresendő.
4. **A bemenet mért hatása a Colab-környezetben (megerősített a felvételen, de a környezetre szól).** A Ctrl+5 után megjelenik a `qshow` ablak (az ablaklistában `['Picasa 3', 'qshow']`), de az aktív ablak végig a `Picasa 3` marad. A Right, Right, Left, space, space, Home, End és Escape után az egymást követő képek között **egyetlen képpont sem változik** (képpontonkénti összevetés, 8-as küszöb, 4.-22. kép), és a qshow nyitva marad. A job-191-ben a képernyő gombjaira kattintva (következő, előző, lejátszás, kártya, rács-vissza) **szintén egyetlen képpont sem változik** (5.-20. kép). Mivel a kattintás sem hat, a qshow ablak ebben a Wine-környezetben semmilyen bemenetre nem reagál (vagy nem rajzol újra). A mérés ezért **nem bizonyítja**, hogy az eredetiben a billentyűk hatástalanok.

**Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| ytWindow-regisztráció a `0x009838b0`-ban, WndProc `0x00983940` | megerősített | sztring-hivatkozások + WNDCLASS-mezők |
| a WndProc a `-21` objektum vtábla `+0x1c` metódusára továbbít | megerősített | C-kód + a `0x00982d60` alosztályozó mintája (38.2.11) |
| a Colab/Wine-környezetben a qshow sem billentyűre, sem kattintásra nem változik | megerősített | job-189 (18 kép) és job-191 (16 kép), nulla eltérés |
| az eredetiben (Windows) a billentyűk hatástalanok | NINCS MEG | a környezet a kattintást sem viszi át, ezért a felvétel nem dönt |
| a qshow nem kap billentyűfókuszt | feltételes | az ablaklista aktív ablaka; Wine alatt a fókusz kezelése eltérhet a Windowsétól (a 38.2.7 szerint a kód `SetFocus`-t hív) |

**Cáfoló kísérlet.** „A billentyűk hatnak, csak a kép lassan frissül.” Cáfolva: a lépések között 3-5 másodperc várakozás volt, és a 22. kép (az Escape után 3 másodperccel) is bitre egyezik a 4.-kel. „A környezet viszi a bemenetet a qshow-hoz.” Cáfolva: a job-191 kattintásai sem változtatnak a képen.

**Következtetés.** A Colab-végrehajtó a qshow ablakot csak megjeleníteni tudja, vezérelni nem: sem a billentyű, sem a kattintás nem jut el hozzá (vagy az ablak nem rajzol újra). A billentyűk és a gombok viselkedése ezért ebből a környezetből nem mérhető. Következő irány: a WndProc mögötti ablakobjektum osztályának megkeresése (a `-21` mezőt író hívás a `0x00983670` körül), és annak üzenetkezelője a binárisból.

**Nyitott kérdések mérlege (38.2.12):** 0 nyílt · 2 lezárva (regisztráció, WndProc-továbbítás) · 2 blokkolt (az ablakobjektum osztálya és üzenetkezelője; a billentyűk és gombok viselkedése, mert a Colab-környezet a bemenetet nem viszi át) · 0 hatókörön kívül.

#### 38.2.13 Kilencedik kör: a qshow ablakobjektuma (#4443, 2026-10-17)

**Kérdés.** A 38.2.12 szerint a WndProc (`0x00983940`) a `GetWindowLongA(hwnd, -21)` objektum vtábla `+0x1c` metódusára továbbít. Három kérdés: (a) melyik függvény írja a -21 mezőt, és mi kerül oda; (b) mi a qshow ablakobjektum vtábla-címe; (c) melyik `+0x1c` metódus kezeli a billentyűket és a gombokat.

**Forrás és módszer.** Csak olvasás. Nincs új Ghidra-futás, nincs bináris, nincs hálózat. A C-kódok a `~/picasapy-agent/referencia/ghidra/` mappában vannak:
- `2026-10-17-hog-qshow-k4.txt`: a `0x00983670` (147-253. sor) és a `0x00982d60` (306-377. sor).
- `2026-10-17-qshow-ctrl5.txt`: a `0x00983670` második példánya (2441-2541. sor).
- `2026-10-17-ytwindow-hivatkozasok.txt`: a `0x00982d60`, a `0x00983670` és a `0x009838b0` C-kódja, a `"ytWindow"` sztring hivatkozásai.
- `2026-10-17-ytwindow-wndproc.txt`: a WndProc (`0x00983940`).
- `2026-10-17-hog-racs-ytwindow.txt`: a `0x00982d00` (1286-1310. sor).
- `2026-10-17-qshow-2.txt`: a `0x004039f0`, a "Picasa 3" főablak építője (104-107. sor).
- `2026-10-17-qshow-3.txt`: a `0x008037e0`, a qshow építője (786-813. sor, és a függvény vége).

A mappa összes fájljában megkerestem a `-0x15` és a `0xffffffeb` előfordulásait, és a `0x00982bf0` hivatkozásait. A `0x00982bf0` C-kódja nincs a mappában.

**Eredmények.**

1. **A -21 mezőt két függvény írja (megerősített).** Mindkettő a `DAT_00d69524` függvénymutatón át hívja a `(hwnd, 0xffffffeb)` párost:
   - `0x00983670` (ablaklétrehozás): a `CreateWindowEx`-alakú hívás után, ha van hwnd. Hívója a `0x00982bf0` (`0x00982cf2`).
   - `0x00982d60` (WndProc-csere): a `-4` hívás után. Hívói a `0x00982d00` (`0x00982d48`), a `0x007360b0` (`0x00736497`), a `0x00736a50` (`0x00736abc`) és a `0x00aa5100` (`0x00aa5161`).
   Az alak SetWindowLongA-é, de a név nincs megerősítve.

2. **A CreateWindowEx nem adja a -21 értékét (megerősített).** A létrehozó hívás utolsó argumentuma (`lpParam`) a C-kódban `0`.

3. **Az érték nincs meg (NINCS MEG).** Mindkét `DAT_00d69524(hwnd, 0xffffffeb)` hívásnak csak két argumentuma látszik. A -4 hívásnak (`0x00982d60`, 373. sor) a harmadik argumentuma (`EDI`) látszik, a -21 hívásnak nem. Ez a dekompilátor hiánya is lehet, vagy egy regiszterből jövő érték. A C-ből nem dönthető el.

4. **A this és a jelölt objektum (feltételes).** A `0x00983670` és a `0x00982d60` `this`-e (`unaff_ESI`) a hwnd-t a `+0x6c`-ben tárolja, így a hwnd-ből vissza lehet rá találni. A `this` típusának neve nincs a C-kódban. Ismert mezői: `+0x00` vtábla-mutató, `+0x34` a régi WndProc, `+0x64` a `0x008037e0` által beállított másik objektum (`piVar5`, lásd 5.), `+0x6c` a hwnd, `+0x78` a szülő hwnd. Ha a -21 érték a `this`, akkor ez az objektum a jelölt. Ez nincs igazolva.

5. **A qshow ablakának objektuma: a `0x008037e0` piVar4-je (feltételes).** A `0x008037e0` két objektumot épít:
   - `piVar4` (0x88 bájt): a `0x00982bf0` visszatérési értéke. A `SetFocus((HWND)piVar4[0x1b])` (813. sor) a `+0x6c` hwnd-t használja, ezért ez feltételesen a qshow ablakának objektuma.
   - `piVar5` (0x890 bájt), a `0x007fa7f0` építi (C-kód nincs). A `piVar4[0x19] = piVar5` (808. sor) a `+0x64`-be írja, és a `(*piVar5 + 0x28)(piVar4)` hívás kapcsolja össze a kettőt.
   A -21 objektuma a `piVar4` és a `piVar5` közül bármelyik lehet. A C nem dönti el.

6. **A vtábla címe nincs meg (NINCS MEG).**
   - A `piVar4` vtábláját a `0x00982bf0` állíthatja be. Ennek C-kódja nincs a mappában. A `0x008037e0` nem ír vtáblát a `piVar4`-re.
   - A `0x004039f0` a `0x00982bf0` után írja be a `ytFrameWindow::vftable`-t (`qshow-2.txt` 107. sor). Ez a főablak, nem a qshow.
   - A `ytWindow::vftable` a `0x00982d00`-ban áll be (`*in_EAX = ytWindow::vftable`). A `0x00982d00` hívói között nincs a `0x00982bf0`, ezért nem bizonyított, hogy a qshow vtáblája ez. A szimbólum számértéke sincs a mappában.
   - A `piVar5` vtáblája a `0x007fa7f0`-ban áll be. Annak C-kódja sincs a mappában.

7. **A +0x1c üzenetkezelő címe nincs meg (NINCS MEG).** A cím a vtábla címéből számolható. A `vtábla + 0x1c` címen lévő 4 bájt (kis-endian, 32 bites binárisban) a metódus abszolút címe. A vtábla az objektum első 4 bájtja. Mivel a vtábla címe nincs meg, a bejegyzés címe sincs meg.

8. **A WndProc és a -21 olvasói (megerősített, a 38.2.12 kiegészítése).** A `0x00983940` a `GetWindowLongA(hwnd, -0x15)` eredményét használja. Ha van objektum, és a `+0x1c` hívás nem `0xf4241`-et ad, a függvény visszatér az eredménnyel (`1000000` esetén 1-gyel). Egyébként a `DAT_00d69554` alapeljárás fut. A `+0x1c` hívás három argumentumot kap: `msg`, `wParam`, `lParam`. A `this` a C-kódban nem látszik. A `0x00982d60` 357. sora is olvassa a -21 mezőt: ha van objektum, meghívja a `FUN_00982e60`-at, majd az objektum vtábla első slotját `1` argumentummal.

**Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| a -21 mezőt a `0x00983670` írja (létrehozás) | megerősített | (hog-qshow-k4) 244. sor; (qshow-ctrl5) 2532. sor |
| a -21 mezőt a `0x00982d60` írja (WndProc-csere) | megerősített | (hog-qshow-k4) 374. sor |
| az írás `DAT_00d69524`-en át, SetWindowLongA-alakú | feltételes | a C alakja; a név nincs megerősítve |
| a CreateWindowEx `lpParam`-ja `0`, a -21 értéke nem onnan jön | megerősített | (hog-qshow-k4) 236-237. sor |
| a -21-be kerülő érték (a harmadik argumentum) | NINCS MEG | a C-ben két argumentum látszik |
| a -21 objektuma a `this` (`unaff_ESI`) | feltételes (jelölt) | a hwnd a `+0x6c`-ben; az érték nincs |
| a qshow ablakának objektuma a `0x008037e0` `piVar4`-je | feltételes | (qshow-3) 813. sor: `SetFocus` a `+0x6c` hwnd-del |
| a qshow objektum vtáblája `ytWindow::vftable` | NINCS MEG | a `0x00982d00` nem hívója a `0x00982bf0`-nak |
| a `+0x1c` üzenetkezelő címe | NINCS MEG | a vtábla címe hiányzik |
| a WndProc a -21 objektum `+0x1c` metódusára továbbít | megerősített | (ytwindow-wndproc) C-kód |

**Cáfoló kísérletek.**
1. „A -21-et a CreateWindowEx `lpParam`-ja állítja be.” **Cáfolva:** a létrehozó hívás `lpParam` argumentuma `0`.
2. „A -21-et csak a `0x00983670` írja.” **Cáfolva:** a `0x00982d60` is ír rá (374. sor).
3. „A -21 objektuma `ytWindow::vftable`-t visel.” **Nem igazolódott:** a `0x00982d00` nem hívója a `0x00982bf0`-nak. Ez nem cáfolat, mert a `0x00982bf0` C-kódja hiányzik.
4. „A -21 objektuma a `this`.” **Nem cáfolható és nem igazolható:** a -21 értéke nincs a C-ben. A `piVar5` is jelölt marad.

**Következtetés.**
- A -21 mezőt a `0x00983670` (létrehozás) és a `0x00982d60` (WndProc-csere) írja. Ez megerősített.
- Hogy melyik objektum kerül oda, nincs megmérve. A jelöltek: a qshow ablakának `piVar4`-je vagy a `piVar5`.
- A vtábla címe nincs meg, ezért a `+0x1c` üzenetkezelő sincs meg. A billentyűk és gombok kérdése blokkolt.

**Hiányzik.**
- A `0x00982bf0` C-kódja: a vtábla-beállítás (`*this = ...`) és a `this` átadása a `0x00983670`-nek.
- A `0x00983670` `DAT_00d69524(hwnd, 0xffffffeb)` hívásának szerelése: a hívás előtti push-sor, vagyis a harmadik argumentum. A C-sorrend szerint a hívás a `0x009837d2`-es (`FUN_00980670`) hívás után van.
- A `0x007fa7f0` C-kódja, ha a `piVar5` lesz a jelölt.

**Ghidra-kör kell.** A kért sor (a vtábla +0x1c üzenetkezelője) most nem írható fel, mert a vtábla címe nincs meg. Helyette:

Ghidra-kör kell: 0x00982bf0 - a qshow ablakobjektum konstruktora (vtábla-beállítás, a `this` átadása a 0x00983670-nek) [blokkoló]

Szerelés kell: 0x00983670 - a `DAT_00d69524(hwnd, 0xffffffeb)` hívás előtti push-sor (a harmadik argumentum) [blokkoló]

Ha a vtábla címe megvan, a következő kör a `+0x1c` üzenetkezelőre szól: WM_KEYDOWN, WM_LBUTTONDOWN ága.

**Amit ez NEM jelent.** A qshow billentyű- és egérviselkedése Windowsban továbbra sincs megmérve. A 38.2.12 nyitott pontja nem zárult le, csak szűkült: az írók megvannak, az objektum nincs.

**Nyitott kérdések mérlege (38.2.13):** 0 nyílt · 2 lezárva (a -21 írói; a CreateWindowEx `lpParam`-ja kizárva) · 3 blokkolt (az érték; a vtábla címe; az üzenetkezelő) · 0 hatókörön kívül.

#### 38.2.14 Tizedik kör: a Ctrl+5 két belépési útja, a mód-bájt és a qshow-vezérlés (#4443, 2026-10-18)

**Kérdés.** (1) Melyik switch-ág hívja a `0x005e8a70`-et a `0x9ccc`-hez? (2) Milyen feltétellel nyit qshow-t a Ctrl+5 (job-188: kijelölés nélkül is nyit), milyen paraméterrel, és mi a különbség a Lejátszás (diavetítés) hívásához képest? (3) Mit olvasható ki a qshow-ablak létrehozásából (`0x00983670`) és a `0x0052d430`-ból a bemutató vezérléséről?

**Forrás és módszer.**
- (A) Helyi diszasszembly, csak olvasás: a `Picasa3.exe` PE-jéből, a munkafa ideiglenes `.bt/bt_kiolv.py` szkriptjével (a kör végén törölve). Vizsgált függvények: `0x005cb990` (WM_COMMAND-elosztó), `0x005e60d0` (billentyű-kezelő), `0x005e8a70`, `0x008037e0`, `0x005696c0` (kapu), `0x00559150` (menütábla-építő). Az ugrótábla-bejegyzést a PE-ből olvastam, nem a Ghidra-szövegből.
- (B) Azonosító-hozzárendelés: a menütábla-építő rekordjai és a `.rdata` feliratkulcsok (`eMenuView::ID_VIEW_TIMELINE` stb.) összevetése. A rekord `+0` mezője a `FUN_009ae560(kulcs)` eredményéből íródik (`mov [rekord], eax`), a `+0xa` a parancsazonosító.
- (C) A jelenlegi kód: `src/picasapy/app/qml/PicasaMenuBar.qml`, `src/picasapy/app/qml/Main.qml`, `MainToolbar.qml`, és a `01bb55264` commit (#1903).
- A függvényméreteket a bináris-index `functions` táblájából vettem. A vtábla-hívások nem látszanak az index `xrefs` táblájában, ezért a hívólista nem negatív állítás.

**Eredmények.**

1. **A `0x9ccc` hívási útja (megerősített; A + B).**
   - `0x005cb990`: `lea eax,[esi-0x9c42]` · `cmp eax,0xfa` · `ja 0x5cd979` · `movzx edx,byte ptr [eax+0x5cdb34]` · `jmp dword ptr [edx*4+0x5cd9fc]`.
   - `0x9ccc - 0x9c42` = index `0x8a`; a bájt (`0x5cdbbe`) értéke 47; az ugrótábla 47. bejegyzése (`0x5cdab8`) a `0x005cbbdd`-et adja.
   - `0x005cbbdd`: `push 1` · `push ebx` · `call 0x005e8a70` · `jmp 0x5cd9e6`. Vagyis `(this = ebx, mód = 1)`.
   - A `0x005cbbd1` ág (`push edi`, ahol `edi = 0`) a `0x9c6d` és a `0x9c9f` azonosítókat kapja: `(this, 0)`.
   - Az azonosítók (B): `0x9ccc` = `eMenuView::ID_VIEW_TIMELINE` (`Ti&meline`, rekord `0xd6e090`, a kulcs-mutató a `0x0055a9ed`-nél íródik). `0x9c9f` = `eMenuView::ID_VIEW_SLIDESHOW` („&Slideshow", rekord `0xd6e07c`, `0x0055a9a3`). `0x9c6d` = `eMenuLabelFolder::ID_ALBUM_SLIDESHOW` („&View Slideshow", rekord `0xd6e1d4`, `0x0055ae81`).
   - A `0x005e8a70` hívói (index, HÍVÓK): `005cbbd3`, `005cbbe0` (`FUN_005cb990`); `005da743`, `005da7ae` (`FUN_005d9cc0`, az eszköztár); `005e146f` (`FUN_005e0f70`, nem vizsgáltam); `005e626f`, `005e628a` (`FUN_005e60d0`, a billentyű).

2. **A Ctrl+5 két belépési útja.**
   - **E1, a menü.** A WM_COMMAND `0x9ccc` közvetlenül a `0x5cbbdd` ágra fut (1. pont). Az ágban nincs feltétel: a `0x005e8a70` `(this, 1)` paraméterrel hívódik. A gyorsbillentyű-hozzárendelés (accelerator-tábla) forrása NINCS MEG.
   - **E2, a billentyű.** A `0x005e60d0` a WM_KEYDOWN-t (`0x100`) kezeli. A `cmp word ptr [esi+8],0x11` · `je 0x5e6603` a Ctrl-billentyű SAJÁT lenyomását zárja ki; nem követeli meg a Ctrl meglétét. A `0x005e6279` ág (a „5"-ös): `push ebp` · `call 0x005696c0` · `test al,al` · `jne 0x5e65f7` (kilépés) · `push 1` · `push ebp` · `call 0x005e8a70`. A `0x005e625e` ág (a „4"-es) ugyanez `push 0`-val, vagyis mód 0.
   - **A kapu (`0x005696c0`, 91 bájt, `ret 4`).** `al = 1` pontosan akkor, ha: `[0x00d67914] != 0` ∧ a `0x009c2fc0(0x00c8ec30)` singleton nem 0 ∧ `[singleton+0x20c] == 0` ∧ `InterlockedCompareExchange([this+0x668], 0, 0) == InterlockedCompareExchange([this+0x99c], 0, 0)`. A `0x00c40328` IAT-slot a PE import-táblájából `KERNEL32!InterlockedCompareExchange`. A 0-ra való összehasonlítás nem ír (0 → 0), tehát a kapu tisztán olvas.
   - A billentyű-út a kapu HAMIS eredményénél nyit. A Ctrl+5 csak akkor éri el a `0x005e8a70`-et, ha a kapu 0 (például nincs singleton, vagy a két mező nem egyezik).
   - **A billentyű-út Ctrl-feltétele: NINCS MEG.** A látott kódban nincs `GetKeyState(VK_CONTROL)`-hívás. Lehet, hogy a Ctrl feltétele a `0x005e6710` hívóláncban van (lásd a nyitott pontokat).

3. **A `0x005e8a70` elágazása a móddal (megerősített a sorrend).**
   - Belépéskor: `call 0x005696c0` (`0x005e8acb`, `push ebx`). Ha ez 1, a `0x009cd8a0` hívás után `cmp eax,0xf4242` · `je 0x5e8b3d` (kilépés-jelölt ág).
   - `cmp byte ptr [0x00d67849],0` · `je 0x5e8b06`. Ha a globális nem 0: `push 0x10` · `call dword ptr [GetAsyncKeyState]` (Shift) · `jne 0x5e8d5d` (Shift lenyomva: a `0x5e8d5d` ág).
   - `0x005e8b06`: `cmp byte ptr [ebp+0xc],0` · `jne 0x5e8d5d`. **Mód 1 (Időrend)** a `0x5e8d5d` ágra megy; ebben vannak a K1-K4 kapuk (38.2.8). **Mód 0 (Lejátszás)** a `0x5e8b10` ágra megy. Ez a tartomány (`0x5e8b10`-`0x5e8d5c`) nem hívja a K1-et (`0x005d2a70`) és a K4-et (`0x005675d0`). Hívásai közül (részlet): `0x0052e8a0`, `0x0040fb50`, `0x004edf60`, `0x005c6710`, `0x00717bb0`, `0x00579330`, `0x009cd730`, `0x0052e2f0`, `0x005d1520`.
   - A mód-bájt a `0x005e9706`-ban íródik a qshow-struktúra 1. bájtjába (`mov cl,[ebp+0xc]` · `mov [esp+0x65],cl`). A `0x005e9787` (`call 0x008037e0`) az egyetlen hívóhely.

4. **A qshow-építő (`0x008037e0`) mód-ága (megerősített).**
   - `0x008039de`: `mov edx,[esp+0x6c]` · `cmp byte ptr [edx+1],0` · `je 0x8039fd`. Mód 0: `push esi` · `call 0x00801cf0` (sima diavetítés).
   - Mód nem 0: `call 0x007fda00` (Időrend-váltás) · `cmp byte ptr [esi+0x3bf],0` · ha 0, `call 0x00802060`.
   - A `0x008037e0` a `Preferences\BigSlideshow2` kulcsot olvassa (38.2.9).

5. **A qshow-ablak és a vezérlés (megerősített a létrehozás és a továbbítás; az objektum NINCS MEG).**
   - A `0x00983670` `CreateWindowExA`-alakú hívása az `"ytWindow"` osztályt használja (`.ghidra4443/2026-10-17-qshow-ctrl5.txt`, 2524. sor). Utána `(*DAT_00d69524)(hwnd, 0xffffffeb)` (2532. sor): a -21 (GWLP_USERDATA) mező írása. Az írt érték (a harmadik argumentum) NINCS MEG (38.2.13).
   - A WndProc (`0x00983940`) a -21 objektum `vt+0x1c` metódusára továbbít (38.2.12). Az objektum és a vtábla NINCS MEG (38.2.13).
   - **`0x0052d430` (23 bájt): NEM továbbító.** `push edi` · `lea edi,[ecx+0x68]` · `mov dword ptr [ecx],0x00c8b4b0` · `call 0x00401000` · `mov dword ptr [edi],0` · `pop edi` · `ret`. Vtábla-beállító (a 38.2.8 helyesbítését igazolja).
   - A főablak billentyű-kapcsolója (`0x005e60d0`) a 38.2.8 szerint nem kezel Escape-et, Space-t, nyilakat és Home/End-et. Ebben a körben ezt nem mértem újra. Ezek hatása a qshow-ablakban, a WndProc-objektumban van: NINCS MEG.
   - **Kilépés (Exit):** NINCS MEG ebben a körben (a 38.2.8 szerinti `this+0x50` / `vt+0x14` hívás nincs újramérve).

**Bizonyítottsági fok.**

| állítás | fok | alap |
|---|---|---|
| `0x9ccc` → `0x005cbbdd` → `0x005e8a70(this, 1)` | megerősített | A: PE-tábla és diszasszembly; B: rekord-kulcs |
| `0x9c9f` (Lejátszás) és `0x9c6d` (mappa-diavetítés) → `(this, 0)` | megerősített | A + B |
| menü (E1) és billentyű (E2) egyaránt mód 1 | megerősített | A |
| billentyű-kapu: IAT `InterlockedCompareExchange`, a feltételek szerkezete | megerősített | A + PE-import |
| a kapu futásidejű értékei (singleton, flag, a két mező) | NINCS MEG | statikusan nem mérhető |
| a Ctrl-feltétel a billentyű-útban | NINCS MEG | a látott kódban nincs Ctrl-ellenőrzés |
| mód 1 → `0x5e8d5d`, mód 0 → `0x5e8b10` | megerősített (elágazás) | A |
| a mód-0 ág listaépítése | NINCS MEG | nem követtem végig |
| qshow-építő: mód 0 → `0x801cf0`; mód ≠ 0 → `0x7fda00` + `0x802060` | megerősített | A |
| qshow-ablak: `CreateWindowExA`-alak, `"ytWindow"`, -21 írás | megerősített | Ghidra C (2524., 2532. sor) |
| `0x0052d430` = vtábla-beállító | megerősített | A |
| qshow billentyűi, Exit, vtábla | NINCS MEG | a WndProc-objektum hiányzik |

**Cáfoló kísérletek.**
1. „A Ctrl+5 nem jut a `0x005e8a70`-hez a `0x9ccc` switch-ágon át." **Cáfolva:** a `0x9ccc` egyedi indexe (`0x8a`) a `0x5cbbdd` ágra mutat, és ez az egyetlen ág, amely a `0x9ccc`-hez tartozik.
2. „A Lejátszás és az Időrend ugyanazt az ágat használja." **Cáfolva a szerkezetben:** mód 1 a `0x5e8d5d`-re, mód 0 a `0x5e8b10`-re ugrik, és csak mód 1 hívja a K1-et és a K4-et. A mód-0 ág listatartalmát viszont nem bizonyítottam.
3. „A `0x0052d430` a bal gombos esemény továbbítója." **Cáfolva** (23 bájt, vtábla-beállító).
4. „A kapu minden Ctrl+5-öt blokkol." **Cáfolva:** a kapu hamis eredménynél enged tovább, a futásidejű értékek viszont nem ismertek.

**Eredeti | Nálunk | Teendő**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Nézet ▸ Időrend (`0x9ccc`) → `0x005e8a70(this, 1)`, kijelölés nélkül is (job-188) | menüpont `enabled: false` (`PicasaMenuBar.qml:1160-1164`), Ctrl+5 `Shortcut` `enabled: false` (`Main.qml:1765-1773`), #1903 | Engedélyezés csak a valódi bemutató megépítése UTÁN, a menüpont és a billentyű együtt. |
| Ctrl+5 billentyű-út: `0x005e60d0` „5"-ös ága, a `0x005696c0` kapuval, `(this, 1)` | nincs | A kapu futásidejű értékei és a Ctrl-feltétel kell a fejlesztés előtt (lásd a nyitott pontokat). |
| Lejátszás (`0x9c9f`) és mappa-diavetítés (`0x9c6d`): `(this, 0)`, a qshow mód-0 ága (`0x801cf0`) | Ctrl+4 és a mappa-diavetítés megvan (a 29. tétel szerint) | Nincs teendő; a bemutató útja más, mint az Időrend-é. |
| Időrend-váltás (`0x007fda00`, `0x802060`) mód 1-ben | nincs | A lépéssort (38.2.9) a bemutató-váltásnál kell követni. |
| qshow-ablak: `ytWindow`, `CreateWindowExA`, `[this+0x6c]` HWND, -21 objektum | `TimelineView.qml`: év/hónap rács, az alkalmazásablakon belül | A rács nem az eredeti bemutató. A qshow-t külön, teljes képernyős módként kell megépíteni. |
| Eszköztár-gomb `thumbui/timelinebutton` (`m_hidden`, 38.2.4) | `MainToolbar.qml` gombja #1903-mal eltávolítva | Az eredeti gomb rejtett, nem kell visszaállítani. |
| Lista-forrás: a nézet gyűjteménye (`[this+0xeac]`, feltételezés) | nincs | Ha a bemutató a nézet képeit járja, a listát az aktuális gyűjteményből kell építeni, nem a Flipbook-rekordtárból (38.2.8). |
| qshow billentyűi (nyíl, Space, Esc, Home/End) és egérkezelése | nincs | NINCS MEG: a `-21` objektum vtáblájának `+0x1c` metódusa kell (38.2.13). |
| Kilépés (Exit) célja | nincs | NINCS MEG (a 38.2.8 `this+0x50` hívása nincs újramérve). |

**Nyitott kérdések mérlege (38.2.14).** 4 nyílt · 3 lezárva (a `0x9ccc` hívási útja; a `0x0052d430` helyesbítése; a mód-elágazás és a qshow-építő mód-ága) · 3 blokkolt · 0 hatókörön kívül.

Ghidra-kör kell: 0x005e6710 - a „5"-ös billentyű-ág (`0x005e6279`) hívóláncában van-e Ctrl- vagy Shift-ellenőrzés, és a Ctrl+5 billentyű-kötésének forrása (accelerator-tábla vagy a hívó). [blokkoló]

Eredeti futtatás kell (Colab, nem Ghidra): Ctrl+5 kijelölés nélkül, a kapu-értékek naplózásával (`[this+0x668]` és `[this+0x99c]` egyezése, a singleton `+0x20c` flagje, a `[0x00d67849]` értéke). Ez dönti el a job-188 és a kód viszonyát. [blokkoló]

Pásztázás kell (`paszta.py`, memóriakapuval): a `[0x00d67849]` globális neve (Flipbook-beállítás?) és írói. [blokkoló a Shift-ág értelmezéséhez]

Válasz [részben, 2026-10-18]: a `0x005e8b10` a `FUN_005e8a70(this, mode)` mód-0 ágának belépési pontja. A `cmp byte ptr [ebp+0xc], 0` (`0x005e8b06`) után, a `jne` nem ugrik, és a `test ebx, ebx` (`0x005e8b10`) a C 127-130. sorának `param_1[0x93]++` (`+0x24c`) ágát nyitja. **Gyűjtemény:** `FUN_004edf60(this[0xaf] + 0xf8, &lista)` tölti a listát a `this[0xaf]+0xf8` objektumból; ennek az objektumnak az azonossága NINCS MEG (a `FUN_004edf60` törzse nincs a dumpban). **K-kapu van, három:** (1) a belépő kapu (C 117-122: a `0x009c2fc0` oneup-keresés és a `this+0x332e` jelző, valamint a `0x005696c0` és a `0x009cd8a0 == 0xf4242` ellenőrzés) `-1`-gyel tér vissza; (2) a `this[0x3aa]` objektum `+0xb4` vtábla-hívása nullát ad, és a függvény `-1`-gyel tér vissza; (3) a `this+0x336c` jelzőt (C-ben `param_1 + 0xcdb`, mutató-indexelés) a `this+0x332f` és a típuskód-szűrő (8, 9, 10, 11, 12, 23, 29) adja. Lásd még a Shift-ág (`DAT_00d67849`) mellékágát. [nem blokkoló]

#### 38.2.15 A Ctrl+5 feltétele, a qshow vezérlője és kilépése (#4443, 2026-10-18)

**Kérdés és módszer.** Ez a kör a Ctrl+5 módosító-feltételét, az `ytWindow`-hez tartozó bemutatóvezérlőt, valamint az Escape kilépési útját követte. A függvények mérete a bináris-indexből származik; a helyi diszasszemblálás a `picasapy-agent` venv `annot_disasm.py` eszközével készült. A PE-erőforrásokat, importokat és vtáblákat `pefile`-lal olvastam. Futó Picasa-mérést ez a kör nem végzett; a korábbi Colab-próbán a qshow megfagyott.

**1. A Ctrl+5 feltétele.** A `0x005e6710` eseménykezelő `0x005e680f`-nél az esemény `+0x10` módosító-bájtját olvassa, majd `0x005e6812`-nél a `0x04` bitet teszteli. Ha be van állítva, a `0x005e69cc` ágon meghívja a `0x005e60d0` billentyűkezelőt. Annak „5” ága (`0x005e6279`) a `0x005696c0` kapu hamis eredménye esetén hívja a `0x005e8a70(this, 1)` bemutatóutat. A Ctrl-feltétel tehát az esemény módosító-bájtjának `0x04` bitjénél dől el, nem a `0x005e60d0`-ben végzett `GetKeyState`-lekérdezéssel. A `0x005e6710` saját `GetAsyncKeyState(0x10)` hívása a Shiftet vizsgálja. A külön `ytWindow`-út `0x00984970` kezelője a `0x00984f8f`-nél közvetlenül lekérdezi a `VK_CONTROL` (`0x11`) állapotát, és azt a módosító-bájt `0x04` bitjébe teszi (`0x00984fba`-`0x00984fcc`); ez függetlenül megerősíti a bit Ctrl-jelentését. A főablaki esemény `+0x10` mezőjének írója ebben a körben **NINCS MEG**.

`pefile`-lal a PE erőforrásjegyzékében (`.rsrc`, `0x00da2000`) nincs `RT_ACCELERATOR` (`9`) típus. A bináris importálja a `USER32!CreateAcceleratorTableA` (`0x00c406e4`) és `USER32!TranslateAcceleratorA` (`0x00c4071c`) függvényt is, ezért ebből önmagában csak a beágyazott erőforrás-tábla hiánya következik, minden futásidejű gyorsítótábla kizárása nem. A vizsgált Ctrl+5 út közvetlen, kézi `WM_KEYDOWN`-kezelőág.

**2. A qshow vezérlőobjektuma és billentyűi.** A `0x00982bf0` konstruktor a `ytWindow` vtábláját (`0x00cd87fc`) állítja be. A `0x00983670` létrehozza az ablakot, majd a `GWLP_USERDATA` (`-21`) helyre ugyanennek az objektumnak a mutatóját írja. A `ytWindow` vtábla PE-ből olvasott elemei: `+0x1c = 0x00984970` és `+0x20 = 0x00985550`. A WndProc a `+0x1c` üzenetkezelőt hívja; a `0x00984970` a billentyűüzenetből módosító-bájtot épít, majd a `+0x20` metóduson át továbbít. A `0x00985550` a `ytWindow+0x64` gyermekre küldi az eseményt annak `+0x30` virtuális metódusán.

A gyermek a `QDrawable`: a `0x007fa7f0` konstruktor a `0x00cbd66c` vtáblát állítja be. A `0x008037e0` ezt rendeli a `ytWindow+0x64` mezőhöz, majd meghívja a QDrawable `+0x28` metódusát. Ennek célja a `0x007fa480`, amely a szülő `ytWindow` mutatóját a QDrawable `+0x50` mezőjébe írja. A PE-ből olvasott QDrawable vtábla `+0x30` eleme `0x00801270`, ez kezeli a qshow `WM_KEYDOWN` eseményeit:

| Billentyű | Bináris ág | Megállapított művelet |
|---|---|---|
| Escape (`0x1b`) | `0x008012a7` → `0x007fb820` | A qshow-ablak bezárási útját indítja. |
| Balra (`0x25`), Fel (`0x26`) | `0x008012bf`-`0x008012c9` → `0x008011b0` | Előző elem. |
| Jobbra (`0x27`), Le (`0x28`) | `0x008012cf`-`0x008012d9` → `0x00801210` | Következő elem. |
| Szóköz (`0x20`) | `0x008012df`-`0x00801344` | A `QDrawable+0x3bb` automatikus lejátszás-jelzőjét váltja; az aktív állapot külön leállítási/frissítési ágon megy. |
| Ctrl+Szóköz | `0x008012e3`-`0x0080130d` | A `QDrawable+0x3ba` mezőt `1`-re állítja. A mező hatása **NINCS MEG**. |
| Home (`0x24`), End (`0x23`) | teljes `0x00801270` függvény | Nincs hozzájuk külön ág; a vezérlő nem kezeli őket saját navigációs billentyűként. Az ismeretlen billentyű visszatérési értéke az ablak alapértelmezett üzenetkezelőjéhez engedi tovább az eseményt. |

**3. Az Escape kilépési célja.** A `0x007fb820` az Escape-ág végén a QDrawable `+0x24` getterével (`0x00a6ccf0`, a `+0x50` mező visszaadása) elkéri a szülő `ytWindow`-t, majd annak vtable `+0x14` metódusát hívja két nulla argumentummal. A `ytWindow` vtábla `+0x14` eleme `0x00983270`. Nulla első argumentummal, ha a `[0x00d67858]` jelző nulla, a függvény a saját HWND-jére `PostMessageA(hwnd, WM_CLOSE, 0, 0)` üzenetet tesz (`WM_CLOSE = 0x10`, importcím `0x00c4080c`). Ha a jelző nem nulla, a kód a jelenlegi szál ablakait sorolja fel az `EnumThreadWindows` importtal (`0x00c40710`) és a `0x00982fa0` callbackkel; a callback bizonyos ablakoknak `SendMessageA(hwnd, WM_CLOSE, 0, 0)` üzenetet küld (`0x00c40884`). Az Escape tehát a qshow bezárását kezdeményezi; hogy a bezárás után pontosan melyik főnézet és fókuszállapot látszik, futó mérés nélkül **NINCS MEG**.

**A két független út.**

- **A út, utasításszintű lánc:** `0x00983670` → `0x00984970` → `0x00985550` → QDrawable `0x00801270`; innen az Escape `0x007fb820`-ba és a szülő `ytWindow+0x14` kilépő metódusába jut. A főablaki `0x005e6710` külön útja a `0x04` bitet vizsgálja, majd a `0x005e60d0` „5” ágához enged.
- **B út, PE-adatok és RTTI:** a vtáblák nyers PE-olvasása a `ytWindow+0x14/+0x1c/+0x20` célokat (`0x00983270/0x00984970/0x00985550`) és a QDrawable `+0x30` célját (`0x00801270`) adja; a bináris-index RTTI-je a `ytWindow` és a QDrawable vtable-címeit azonosítja. A PE-importtábla a `0x00c4080c` címet `USER32!PostMessageA` néven azonosítja. A qshow eseménykezelő `GetAsyncKeyState(VK_CONTROL)` lekérdezése és `0x04` bitbe írása külön igazolja a Ctrl-bit jelentését.

A két út a vezérlőobjektum, a billentyűkezelő és az Escape bezárási kérésének céljában egyezik. A kódból statikusan igazolt események futásidejű látható hatását ez nem méri meg.

**Cáfoló kísérlet.** Megpróbáltam cáfolni azt, hogy a Ctrl+5 az erőforrásban tárolt accelerator-táblából jön: a teljes PE-erőforrástípus-jegyzékben nincs `RT_ACCELERATOR`; a megvizsgált billentyűút ehelyett a `0x005e6812` módosítóbit-próbán halad át. A PE más helyen dinamikus accelerator API-kat importál, ezért a negatív eredmény nem általánosítható minden gyorsítótáblára. Azt is próbáltam cáfolni, hogy a Home/End saját előző/következő műveletet kap: a teljes, index szerint 604 bájtos `0x00801270` függvényben nincs ilyen VK-ág, és a nem kezelt esemény a WndProc alapértelmezett útjára kerül. Mindkét cáfoló eredményt ugyanazzal a mércével ellenőriztem: függvénytörzs, PE-erőforrásjegyzék és nyers vtable/importadatok.

**Bizonyítottsági fok: feltételes.** A Ctrl+5 bitkapuja, a qshow objektumlánca és az Escape által küldött bezárási kérés statikus bináris- és PE-adatokkal megerősített. Az eredeti ablakon a billentyűk látható hatása, a bezárás utáni fókusz és a `QDrawable+0x3ba` Ctrl+Szóköz-jelző szemantikája nem lett futásban megmérve.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A Ctrl+5 a CThumbUI esemény `+0x10` mezőjének `0x04` bitjén át jut a `0x005e60d0` „5” ágához, amely mód 1-ben indítja a `0x005e8a70`-et. A statikus PE-erőforrásban nincs `RT_ACCELERATOR`. | A Nézet ▸ Időrend és a Ctrl+5 a #1903 óta inaktív. | A Ctrl-feltételt a főablaki vezérlő visszaállításakor tartsuk meg; az eseménybit íróját ne találgassuk. |
| A qshow a külön `ytWindow` és QDrawable objektumpárt használja. Balra/Fel előző, Jobbra/Le következő, Szóköz automatikus lejátszás-váltó, Escape bezárási kérés. Home/End nem kap egyedi navigációt. | A `TimelineView.qml` az alkalmazásablakon belüli év-/hónap-rács; qshow vezérlő nincs. | A bemutató saját teljes képernyős ablakában a fenti billentyűút és objektumhatár szükséges. |
| Escape a `ytWindow+0x14` (`0x00983270`) útján `WM_CLOSE`-t tesz az ablakra; a visszatérő főnézet futásban nem lett megfigyelve. | Nincs qshow ablak és kilépési út. | A qshow bezárása után az eredeti könyvtárnézethez térjen vissza; a fókusz részletét eredeti futásban kell ellenőrizni. |
| A bemutató tényleges kártyatartalma, dátumsorrendje és átmenetének képi/időbeli paraméterei korábbi körök alapján továbbra is **NINCS MEG**. | A mostani rács nem az eredeti bemutató. | A teljes reprodukció fejlesztése előtt a 38.2.1 és 38.2.9 nyitott tartalmi és animációs pontjait kell lezárni; addig csak a vezérlőhéj specifikált. |

**Nyitott pontok.** A főablaki esemény `+0x10` módosító-bájtjának írója; a `QDrawable+0x3ba` Ctrl+Szóköz-jelző jelentése; a `[0x00d67858]` ág futásidejű értéke és az általa érintett ablak; a bezárás utáni tényleges nézet és fókusz; továbbá a korábban rögzített kártya-, dátumsorrend- és átmeneti adatok. Ezekhez a főablaki WM_KEYDOWN esemény létrehozójának célzott követése, a jelző mezőíróinak `paszta.py`-s pásztázása, illetve eredeti Picasa futás kell. Ghidra-kör ehhez a körben nem szükséges.

**Nyitott kérdések mérlege (38.2.15).** 5 nyílt (módosítóbit-író, Ctrl+Szóköz-jelző, `[0x00d67858]` ág, bezárás utáni fókusz, korábbi tartalom/átmenet) · 3 lezárt (Ctrl+5 bitkapu, qshow vtable és kért billentyűk, Escape bezárási hívás) · 0 blokkolt · 0 hatókörön kívül.

#### 38.2.16 A `0x9ccc` parancs közvetlen ága és módparamétere (#4443, 2026-10-19)

**Kérdés és módszer.** A korábbi Ghidra-kör a `0x005e8a70` hívói közül nem azonosította, melyik tartozik a Nézet ▸ Időrend parancshoz. A helyi index xrefjeit, az érintett függvények utasításait (`annot_disasm.py`) és az eredeti PE ugrótábla-adatait (`pefile`) vetettem össze. Futó Picasa-mérés és Ghidra-dekompilálás ebben a körben nem történt.

**Parancs → ág → bemutató.** A `0x005cb990` parancs-elosztó a `0x005cba5d` címen levonja a `0x9c42` alapazonosítót. A `0x9ccc` ezért a `0x8a` indexet adja; a PE `0x005cdbbe` bájtja `0x2f`, és a `0x005cd9fc + 4×0x2f` ugrótábla-bejegyzése (`0x005cdab8`) a `0x005cbbdd` ágra mutat. Itt `push 1` (`0x005cbbdd`), majd `push ebx` és `call 0x005e8a70` (`0x005cbbe0`) következik: a menüparancs a bemutatót **1-es módban** nyitja.

Az ellenőrizhető, indexben szereplő közvetlen hívási helyek:

| Hívó ág | Hívás | Mód | Azonosító / jelölő |
|---|---:|---:|---|
| `0x005cb990` | `0x005cbbd3` | 0 | `0x9c6d`, `0x9c9f` menüparancsok |
| `0x005cb990` | `0x005cbbe0` | 1 | `0x9ccc` Nézet ▸ Időrend |
| `0x005d9cc0` | `0x005da743` | 0 | `thumbui/sbutton` |
| `0x005d9cc0` | `0x005da7ae` | 1 | `thumbui/timelinebutton` |
| `0x005e0f70` | `0x005e146f` | 0 | `"play"` parancság |
| `0x005e60d0` | `0x005e626f` | 0 | „4” billentyűág |
| `0x005e60d0` | `0x005e628a` | 1 | „5” billentyűág, a `0x005696c0` kapu után |

Ez az indexben látott négy közvetlen hívófüggvény hét hívási helye; nem állítás a közvetett, például vtable-hívások teljességéről.

**Két független ellenőrzés.** **A út:** az utasításokból követhető az azonosító csökkentése, az ugrótábla elérése, a `0x9ccc`-hez tartozó ág és a `push 1` / célhívás. **B út:** a nyers PE-táblaolvasás a `0x2f → 0x005cbbdd` célpárt adja; az index a `0x005cb990` függvényt a `0x005e8a70` közvetlen hívójaként tartja nyilván (két hívással). A pontos `0x005cbbe0` call-site címet az utasítások azonosítják. Ettől külön, a `0x00559150` menüépítőben a `0x0055a9b0`-`0x0055aa15` utasítások az `eMenuView::ID_VIEW_TIMELINE` címkét, a `Ti&meline` feliratot, az „5” gyorsbillentyű-jelölőt és a `0x9ccc` azonosítót írják a menürekordba. Az utak a parancs azonosításában és a mód-1-es bemutatóhívásban egyeznek.

**Cáfoló kísérlet.** A lehetséges szomszédos mód-0 ágat ellenőriztem: a PE ugrótáblában `0x9c6d` és `0x9c9f` a `0x005cbbd1` címre vezet, ahol a `0x005cbbd3` hívás előtt `push 0` áll. Ezzel szemben a `0x9ccc` saját táblabejegyzése `0x005cbbdd`-re vezet, ahol `push 1` áll. A nyers táblabejegyzések és a tényleges hívóutasítások ugyanazt az eredményt adják; a szomszédos ág nem cáfolja, hanem kizárja az off-by-one téves azonosítást.

**Bizonyítottsági fok: megerősített** a szűk állításra, hogy a `0x9ccc` közvetlen menüútja `0x005e8a70(this, 1)`-et hív: az utasításszintű út és a nyers PE-adatok/xref egyeznek, a menüépítő pedig külön azonosítja a parancsrekordot. Ez nem dönti el a bemutató tartalmának, animációjának vagy futásidejű kapuinak viselkedését. A helyi mérési archívumban ehhez a körhöz nem volt qshow/job-188 felvétel; a kijelölés nélküli megnyitásról szóló korábbi közlés ezért ebben a munkamenetben **NINCS MEG** közvetlen mérési bizonyítékként.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `0x9ccc` → `0x005cbbe0` → `0x005e8a70(this, 1)`; a Ctrl+5 „5” ága is mód 1-es hívást tartalmaz (`0x005e628a`), külön kapuval. | A `TimelineView.qml` régi év-/hónap-rács; a Nézet ▸ Időrend és a Ctrl+5 inaktív, az eredeti qshow-bemutató nincs megépítve. | A visszaállítás a külön bemutató-módot és a mód-1-es eredeti utat kövesse. A kijelölés nélküli megnyitás feltételét, a tartalmat és az animációt eredeti futásban kell lezárni; ezt a statikus ág feltárása nem helyettesíti. |

**Nyitott kérdés mérlege (38.2.16).** A `0x9ccc` → mód 1 közvetlen hívási útja lezárt. A qshow futásidejű K-kapui, a kijelölés nélküli viselkedés, a teljes tartalom/sorrend és az animáció továbbra is nyitott; ezeket a 38.2.14-38.2.15 nyitott pontjai részletezik.

#### 38.2.17 Az Időrend bemutató futás közben, Wine virtuális asztalon (#4443, job-217, 2026-10-20)

**Forrás:** picasa-colab-jobs job-217, 12 képernyőkép és `xinfo.txt`. Eredeti Picasa 3.9, alapállapot (C:\PicasaTeszt, 24 kép), a Picasa a Wine virtuális asztalán (1280×1024, `wine_desktop`, #215). Lépések: Ctrl+5, majd Right, Right, Escape.

**A 38.2.2 fekete kockájának oka.** A job-102-ben a qshow ablak a sima X-kijelzőn fekete maradt, és bemenetet sem kapott. A virtuális asztalon ugyanez a parancs kirajzolódik, és a billentyűket is fogadja: a fekete kép a Wine ablakkezelésének következménye volt, nem a bemutató viselkedése.

**Amit a felvétel mutat (megerősített, képkockák):**

| kocka | mit mutat |
|---|---|
| 04 (Ctrl+5 után) | teljes képernyős fekete háttér, középen kb. 600×480-as bemutatópanel: szürke háttérgörbe, jobbra fent a mappa neve („PicasaTeszt”) és dátuma („October 2026”), alatta pontozott ív, az ív végén a mappa képeinek egymásra döntött bélyegei; alul vezérlősáv (bal szélen lista-ikon, mellette balra mutató nyíl, középen balra nyíl, lejátszás, jobbra nyíl), legalul dátumcsúszka a két szélén „October 2026” felirattal |
| 07-08 (Right után) | a panel a következő gyűjteményre vált: „Recently Updated”, „October 2026”, más háttérkép a görbe mögött; a csúszka gombja jobbra lép |
| 11 (Escape után) | teljesen fekete kocka (a kilépés átmenete) |
| 12 | visszatér a főablak |

**Következtetés.** A Ctrl+5 kijelölés nélkül is az Időrend bemutatót nyitja; a bemutató gyűjteményenként egy kártyát mutat (név, dátum, bélyegköteg), a Right a következő gyűjteményre lép, az Escape kilép. A panel a teljes képernyőn középre igazított, fix méretű terület, körülötte fekete.

**Billentyűk és kattintás (job-219, job-220, 2026-10-20, megerősített, képkockák).** A vezérlősávra adott egérkattintás (lejátszás 640,690; lista-ikon 366,690) a job-219-ben semmit nem változtatott, a billentyűk igen. A job-220-ban a **szóköz** az aktuális kártya gyűjteményét teljes képernyős diavetítésként indítja: az első kép (a szürke átmenet) fekete háttéren, nagyítva jelenik meg, majd kisebbre vált (6. és 12. kocka, a halvány „PicasaTeszt” felirattal); az End, Left és Home billentyűkre képről képre lép (13. kocka: a színtábla, 17. kocka: egy űrkép); az Escape kilép a főablakba (20-21. kocka).

**Nem dőlt el ebből a felvételből:** az átmenet animációja (a kockák 3 másodpercenként készültek), a lejátszás gomb automatikus léptetésének üteme, a lista-ikon funkciója és a csúszka húzásának hatása. Ezekhez a következő felvétel lépései: a lejátszás gomb és a lista-ikon megnyomása, 1 másodperces kockákkal.

#### 38.2.18 Az Időrend bináris újraellenőrzése (#5401, 2026-10-20)

**Kérdés.** A #5401 négy nyitott pontja: a bemutató képláncának forrása és sorrendje; a kártyák mozgásának képlete és időzítése; az alsó vezérlők és a dátumcsúszka működése; végül a diavetítésbe lépés és a visszatérés helye. Ez a kör csak helyi bináris- és indexadatot olvasott. A futásfelvételek korábbi, 38.2.17-ben dokumentált eredményeit nem tekintem újramért adatnak: a szükséges nyers képek nincsenek a helyi mérőadat-archívumban.

**1. Képlánc és forráshalmaz.** A `CThumbUI::MakeTimeline` (`0x005e8a70`) az Időrend ágban a `CThumbUI+0x2c0` kollekció darabszámát kéri le (`0x005e9434`, `0x004a0980`), majd 0-tól a darabszámig járja az indexet (`0x005e9490`). Minden elemnél a CThumbUI vtable `+0x90` metódusát hívja; a thunk (`0x00562cc0`) a `CThumbUI+0x2bc` szolgáltató vtable `+0x20` metódusának adja át az indexet. Ez egy indexelt külső sorozat bejárását bizonyítja, nem a sorozat eredetét. A szolgáltató típusa, a könyvtár/mappa/album/Picture Tray tagsága, a dátumrendezés mezője és iránya, valamint a gyűjteményenként megjelenített képek száma és azonossága **NINCS MEG**. A 38.2.17 job-217 leírása egy mappakártyát mutatott, a Right pedig a következő kártyára váltott; a nyers képek hiánya miatt ez itt csak korábbi, nem újraellenőrzött mérési feljegyzés.

**2. Átmenet, háttér és kártyarajz.** A Timeline-gomb útja (`0x007fda00`) ellenőrzi a `[this+0x2d8]` jelzőt és a `[this+0x538]` mutatót, QPC-értéket rögzít a `[this+0x430]` mezőbe, majd `0x00802230(this, 1)` hívással indít frissítést. A frissítő a `[this+0x3f0]` elemszámot, `[this+0x3f4]` indexet, `[this+0x3ec]` listát, valamint a `+0x400/+0x404` és `+0x474/+0x478` geometriai mezőket használja; a bináris konstansokat is beolvassa, de ezek jelentése és a mezők kapcsolata nincs biztonságosan feloldva. A pálya, a mozgás iránya, a pozíció/méret/forgatás/átlátszóság függvénye, a görbe és az átmenet hossza **NINCS MEG**. QEMU-s képletigazolás nem történt: a helyi `qemu-i386` nem ad qshow/Win32 felületet futtató próbapadot, a `qemu_harness` csak különálló függvényeket futtat kézzel felépített állapottal; Wine és `qemu-system-i386` nincs telepítve.

Az ismert `CTransTimeline` cím (`0x00816b00`) nem a qshow képkocka-frissítőjeként azonosítható: közvetlen utasításolvasata `<CTransTimeline>`, `<defaulttrans>` és ismételt `<trans>` XML-elemeket ír, benne filmátmenet-paraméterekkel. Hívásai a `0x006175c0`, `0x00618050`, `0x0061d020` és `0x00814250` körüli filmkészítő útban vannak; a `CTransTimeline` vtable írói `0x0080f395` és `0x0080f620`, UI-vtable írója `0x0080f3fa`. A qshow animációjának jelöltje a külön `0x00802230`, de annak képlete nyitott. A `0x007fb210` csak a `timeline`, `timelinedot`, `sliderthumb`, `startbutton`, `exit` és további overlay-erőforrásokat tölti be és skálázza; ez nem bizonyítja sem azok rajzolási képletét, sem kattintási műveletét. A fekete háttér és a kártya elemei kizárólag a korábbi job-217 feljegyzésből ismertek; a binárisból e körben nem sikerült a teljes rajzútjukat azonosítani.

**3. Vezérlők és időzítés.** A `0x008032e0` OneUpUI-ág kezeli a `oneup/timeline` kattintását, a `oneup/exit` visszahívását, valamint a külön `prev`/`next` parancsokat; ez önmagában nem köti az alsó overlay `startbutton`, `exit` vagy listaikon grafikáit ezekhez a parancsokhoz. A qshow billentyűkezelője (`0x00801270`) `WM_KEYDOWN`-on a Bal/Fel kódot előző elemre (`0x008011b0`), a Jobb/Le kódot következő elemre (`0x00801210`) irányítja. Escape a `0x007fb820` kilépési ágat hívja. A szóköz a `[this+0x3bb]` automatikus lejátszási jelző ágát váltja; ez statikusan egyezik az `Auto Play` vezérlő útjával, de nem azonosít önmagában teljes képernyős diavetítés-ablak létrehozását.

Az automatikus továbblépés küszöbe kiolvasható. A `0x00802060` a `0x009a51b0` helperrel számít eltelt időt: `QPC_now - QPC_start`, szorozva a `QueryPerformanceFrequency` reciprokával; a QPC-kezdőérték a `[this+0x520]` mezőben van. Ezután a `0x4019b0` getterrel beolvassa a `[this+0x760]` (`Preferences\SlideshowEffectTime`) értéket, egész másodpercként lebegőpontos értékké alakítja, és az eltelt QPC-másodperccel hasonlítja össze. Ha a beállított érték kisebb az eltelt időnél, a `0x00802630` léptető út fut. A `[this+0x760]` értékét a `0x00802ff0` `second`/`seconds` felirattal jeleníti meg, így a beállítás mértékegysége két külön kódútból is másodperc. A `0x007fa7f0` felépítő a `Preferences\SlideshowEffectTime` olvasóhívásnak 3-as kezdeti értéket ad át (`0x007facd3`-`0x007fad05`); az aktív felhasználói értéket ez nem rögzíti. A frissítő callback üteme, vagyis az ellenőrzés milyen időközönként fut le, **NINCS MEG**; így a beállítási küszöb ismert, a tényleges képkocka-/léptetési időpont nem. A callback címe a `ytCallback<QDrawable>::vftable` (`0x00cbd6c8`) `+0x04` elemében `0x00803ab0`; a vtable-t a `0x00803b00` állítja be. A QDrawable felépítő ezt a callback-objektumot a `0x007fae76` helyen átadja a `0x0097d150`-nek. Maga a callback (`0x00803ab0`) QPC-értéket ír, majd a `[QDrawable+0x3bf]` jelző nullás ágában meghívja a `0x00802060` frissítőt. A callback regisztrációs út egy része tehát megvan, de az eseménylista ütemezője és periódusa nincs feloldva.

A `timelinedot`, `sliderthumb`, `startbutton`, `exit` és listaikon pontos kattintási/húzási célja, a dátumcsúszka dátum- vagy képindexre vetítése, valamint az, hogy a listaikon melyik nézetet nyitja, **NINCS MEG**. A korábbi job-219 feljegyzés szerint a kattintási próba nem változtatott a képen; ez nem bizonyítja, hogy az eredeti Windows-felületen a gombok hatástalanok.

**4. Diavetítésbe lépés és visszatérés.** A korábbi job-220 feljegyzés szerint szóközre az aktuális kártya gyűjteménye teljes képernyős diavetítésként jelent meg, majd Escape a főablakba tért vissza. A nyers mérőadat hiányában ez most nem ellenőrizhető. A statikus `0x00801270` szóközága a qshow automatikus lejátszási jelzőjéhez vezet, nem látszik benne közvetlen új ablak létrehozása. Az Escape (`0x007fb820`) a szülő `ytWindow` bezárási visszahívását indítja. A teljes képernyős diavetítésre váltás pontos hívási lánca, a visszaállított gyűjtemény/képkocka és a fókusz ezért **NINCS MEG**.

**Két független út.** **A út:** a `0x00816b00` utasításszintű olvasata XML-szerializálót mutat; a `0x007fda00` → `0x00802230` híváslánc külön választja a qshow animációfrissítőjét. **B út:** a `0x00cbdcc4`/`0x00cbdcec` `CTransTimeline` vtable- és RTTI-adatai, az író konstruktorának/hívóinak filmkészítő xref-lánca, valamint a `picasa-create-features.md` 2.4. szakaszának független leírása ugyanazt a film-XML-szerializáló szerepet adja. A két út a szűk állításban egyezik: a `0x00816b00` a filmkészítés XML-szerializálója, nem a qshow frissítőfüggvénye. Ez nem zárja ki, hogy a film-átmenet típusa máshol közös adatot használjon.

Az automatikus időlépésre szintén két út áll rendelkezésre. **A út:** `0x00802060` és `0x009a51b0` QPC-időből másodpercet képez, majd a `+0x760` értékkel hasonlítja össze. **B út:** a külön `0x00802ff0` kód ugyanazt a `+0x760` mezőt olvassa és `second`/`seconds` szöveggel formázza. A mértékegység és a beállított küszöb szerepe egyezik; a callback ütemét és a konkrét futó értéket egyik út sem adja meg.

**Cáfoló kísérlet.** Megpróbáltam cáfolni, hogy a `CTransTimeline` (`0x00816b00`) számolja a qshow mozgását: a függvényt közvetlenül végigolvastam; XML-író hívásokat, csomópontneveket és filmátmenet-paramétereket ír. Ezután ettől függetlenül a `.text` utasításait a kötelező `paszta.memoria_kapu()` után streaming módban kerestem közvetlen hívásokra és vtable-címírásokra; a writer közvetlen hívói és a vtable-írók a filmkészítő útban vannak, míg a qshow felépítője a `0x007fda00`/`0x00802230` frissítőt hívja. Ez cáfolja, hogy a `0x00816b00` volna a qshow közvetlen animátorfüggvénye. A közvetett hívás vagy közös típus használatának teljes kizárására a pásztázás nem alkalmas, ezért ilyen negatív állítást nem teszek.

**Bizonyítottsági fok: nyitott.** A `CTransTimeline` szerializáló szerepe és a `SlideshowEffectTime`-küszöb szűk állításai két egymástól külön út egyezésével megerősítettek. A négy elfogadási pont közül egyik sem áll rendelkezésre teljesen: a forrás/rendezés, mozgásképlet, overlay-működés és a Space utáni visszatérési állapot nyitott. A korábbi Wine-képkockák csak megerősítő, itt nyers fájllal nem újraellenőrzött feljegyzések.

| állítás/érték | bizonyíték | fok |
|---|---|---|
| indexelt bemeneti sorozat és elemszám-bejárás | bináris `0x005e9434`, `0x005e9490`, thunk `0x00562cc0` | feltételes |
| gyűjtemények forráshalmaza, rendezési mező/sorrend, gyűjteményenkénti képlista | NINCS MEG | nyitott |
| átmenet-indítás és QPC-kezdőérték | bináris `0x007fda00`, `0x00802230` | feltételes |
| mozgás képlete, görbéje, iránya és időtartama | NINCS MEG | nyitott |
| `SlideshowEffectTime` beállított értéke a QPC-eltelt másodperchez hasonlítva | bináris `0x00802060`, `0x009a51b0`; második út: `0x00802ff0`, `0x007facd3` | megerősített (küszöb, nem frissítési ütem) |
| overlay kattintás/húzás, csúszka dátumleképezése, listaikon funkciója | NINCS MEG | nyitott |
| szóköz látható diavetítés-váltása és pontos visszatérési állapota | mérés: korábbi job-220 feljegyzés, nyers adat most NINCS MEG; bináris `0x00801270`, `0x007fb820` | nyitott |
| `CTransTimeline` (`0x00816b00`) film-XML-szerializáló | bináris `0x00816b00`; független RTTI/vtable/xref és `picasa-create-features.md` 2.4. | megerősített |

**Nyitott - következő pontos lépések.**

- `Ghidra-kör kell: 0x005e8a70 - a CThumbUI+0x2bc szolgáltató konkrét típusa, a +0x2c0 forráskollekciója, upstream rendezési mezője és sorrendje [blokkoló]`
- `Ghidra-kör kell: 0x00802230 - a qshow-átmenet képenkénti pozíció/méret/forgatás/átlátszóság függvénye, easingje, végpontjai és időtartam-mechanizmusa [blokkoló]`
- `Ghidra-kör kell: 0x00a52890 - a sliderthumb, timelinedot, startbutton, exit és listaikon hit-test/callback útja, valamint a csúszka dátum-/képlista-leképezése [blokkoló]`
- `Ghidra-kör kell: 0x0097d150 - a 0x007fae76 callback-objektum átadásának eseménylista-útja, a QPC-frissítés forrása és a pontos ütemezési periódus [blokkoló]`
- `Ghidra-kör kell: 0x00801130 - a szóköz/Auto Play ág teljes diavetítés-váltási útja, valamint a visszatéréskor megőrzött gyűjtemény és képpozíció [blokkoló]`

**A #5401 „Kész, ha” pontjai.** (1) Képlánc és forráshalmaz: ⛔ csak az indexelt lista bejárása ismert; a forrás, sorrend és elemlista nyitott. (2) Átmenet: ⛔ az indítóút és a QPC-kezdés ismert, a mozgásfüggvény nincs meg; QEMU-futtatás nem történt, mert nincs qshow-UI-harness. (3) Vezérlők: ⛔ a billentyűk statikus ága részben ismert, de az overlayek műveletei, csúszkaleképezés és frissítési periódus nyitott; a régi felvétel csak megerősítés. (4) Diavetítés és visszatérés: ⛔ a Space jelzőág és az Escape bezárási út ismert, a látható átmenet és a visszatérési pozíció nincs binárisan/futásban lezárva.

**Fejlesztési következmény.** A #5377 teljes animált bemutatójának folytatása továbbra is blokkolt. A fenti nyitott pontok lezárása előtt a képlista-, mozgásképlet-, vezérlőleképezés- vagy folytatási pozíció-értéket implementációban megadni becslés lenne.

#### 38.2.19 Az Időrend bináris feltárása, 2. kör: képlet, időzítés, Space, eseményút, vezérlők (#5401, 2026-10-20)

**Kérdés és hatókör.** A 38.2.18 öt nyitott tételét dolgoztuk fel: a mozgásképletet (1), az időzítést (2), a Space-ágat (3), az eseménylistát (4) és a vezérlőket (5). Bemenet: a két scratchpad-dekompilálás, a helyi bináris-index és a `pe_dis` diszasszemblálása. Futásfelvétel és QEMU-futtatás nem volt, mert a helyi környezetben nincs qshow-felületet futtató próbapad. Minden állításhoz bináris címet adunk. Ahol a dekompilált törzset nem diszasszemblálással ellenőriztük, ezt kimondjuk.

**Konstansok.** A típust a betöltő utasítás dönti el (`fld dword` float, `fld qword` double). Az értékek a `pe_dis` f32/f64 olvasásából származnak.

| bináris cím | betöltés | érték | szerep |
|---|---|---|---|
| `0x00cf4320` | `fld qword` (double) | 0,1499999761581421 | a `c` szorzó (a 0,15 float-pontossága) |
| `0x00c72150` | `fmul qword` (double) | 0,5 | a y-ág fele |
| `0x00cf39e4` | `fadd dword` (float) | 4294967296 (2^32) | negatív W előjel-korrekciója |
| `0x00cf3ac0` | `fadd qword` (double) | 4294967296 (2^32) | negatív H előjel-korrekciója |
| `0x00d35808` | `fld dword` (float) | 2276,5556640625; betöltés csonkolva: 2276 | csak a `p[0xb9]` ágban (0x008023bb); a csonkolást az RC=11 adja (0x008023c6-0x008023de) |

**1. Mozgásképlet (0x00802230).**

- Visszatérés `4`-gyel: ha `[this+0x3f0] >> 1 <= [this+0x3f4]`, vagyis a darabszám fele nem nagyobb az indexnél (0x00802299-0x008022b7).
- Az elem: `[this+0x3ec][index]` (0x008022ba-0x008022c0).
- Az előző eltolás mentése: `[this+0x400]` → `[this+0x408]`, `[this+0x404]` → `[this+0x40c]` (0x008022c3-0x008022d5). Vagyis `param_1[0x102]` és `param_1[0x103]`.
- Két egymás utáni véletlen szám: az első `rand()` (r1, 0x008022db) az y-ágat adja, a második (r2, 0x008022f2) az x-ágat.
- A `_rand` (0x00c08221) MSVC-féle lineáris kongruens generátor: állapot = állapot × 0x343fd + 0x269ec3, kimenet = (állapot >> 16) & 0x7fff. Tartomány: 0 és 32767 közötti egész.

**A float-trükk.** Az `(r + 0x3f8000) << 8` egészet a verembe írja (0x008022e6-0x008022ff), majd `fld dword`-del tölti vissza (r2: 0x00802306, r1: 0x00802353). Ez bitminta-újraértelmezés, nem számértékű átalakítás. A bitminta 0x3f800000 + r × 256, ami f = 1 + r / 32768 értéket ad, mert r × 256 kisebb 2^23-nál. Így f - 1 = r / 32768 pontosan, a tartománya [0; 0,99996948]. A Ghidra-dekompiláció `(float)` öntést mutat, ez félrevezető.

**x-eltolás (`param_1[0x100]`).**

x = fl32( c × W' × r2 / 32768 ), ahol c = 0,1499999761581421, W = `[this+0x474]` (`param_1[0x11d]`), és W' = W, ha W ≥ 0, különben W + 4294967296.

- W betöltése és előjel-korrekciója: 0x0080230d-0x0080233b.
- A c szorzó: 0x00802345-0x0080234b.
- Tárolás a verembe, majd `[this+0x400]`-ba: 0x0080234f, 0x0080238d-0x00802391.
- Tartomány: 0 ≤ x < 0,15 × W' (r2 legfeljebb 32767).

**y-eltolás (`param_1[0x101]`).**

y = fl32( c × 0,5 × H' × r1 / 32768 ), ahol H = `[this+0x478]` (`param_1[0x11e]`), H' ugyanúgy, mint W'.

- A H-ág: 0x00802353-0x0080237f (a 0,5 a 0x00802370 fmul-ban, az előjel-korrekció a 0x0080237f fadd-ban).
- A c szorzás: 0x00802397. Tárolás `[this+0x404]`-be: 0x0080239d-0x008023a1.
- Tartomány: 0 ≤ y < 0,075 × H'.

**W és H jelentése.** A két értéket (w, h) párként a `p[0xb8]` objektum +4-es metódusa kapja (dekompiláció 126. sor, `&local_60`), a középre igazítás pedig a méretkülönbség felét használja (dekompiláció 162-163. sor). Hogy ez a kép vagy a kártya mérete, **NINCS MEG**. A képlet a számokat ettől függetlenül adja.

**Visszatérési értékek.**

- `0` (0x0080260e): a képkocka elkészült.
- `4` (0x008022b7): az index kiesett a darabszámból, nem rajzol.
- `-1` (0xffffffff): a `p[0xb8]+4` callback nem nulla értéket adott (dekompiláció 126-130. sor).
- A hívó 0x00802630 nem nulla értéknél, ha a darabszám nem nulla, újrapróbálja (0x008026ee-0x008026fc, diszasszemblálva). Tehát a 4 és a -1 is újrapróbálást vált ki. A ciklus lezárását a 0x0080275b és a 0x00802765 ág adja; ezt nem vizsgáltuk: **NINCS MEG**.

**Az előző érték ([0x102], [0x103]).** A 0x00802230 törzsében csak írás van (dekompiláció 91-92. sor). Olvasót nem találtunk. Hogy a kártyák átmenete ezt használja-e: **NINCS MEG**. Olvasó kereséséhez teljes `.text` pásztázás kell (`paszta.py`), amit ebben a körben nem futtattunk.

**Mi nincs még.** A képlet nincs megfeleltetve a rajz geometriájának (a kártya helye a képkockán). Azt, hogy a rajzoló a `[this+0x400]` és `[this+0x404]` mezőkből milyen egységben olvas: **NINCS MEG**.

**2. Időzítés (0x00802060, 0x007fda00, 0x00803ab0, 0x009a51b0, 0x004019b0).**

- Eltelt idő: a `0x009a51b0` számítja: (QPC most - `[this+0x520]`) × (1/QPF), másodpercben. A reciprokot első híváskor tölti be, és `0x00d678e8`-ban tárolja (0x009a51c4-0x009a51ec).
- Küszöb: a `0x004019b0` a `[this+0x760]` objektumot olvassa. Ez registry-olvasó: a 0x004019ec és a 0x00401a1f címen a 0x009a4890 hívás KEY_ALL_ACCESS (0x000F003F), illetve KEY_READ (0x00020019) maszkot kap. A kulcs `Preferences\SlideshowEffectTime`: a sztring (0x00c8e5f4) a 0x007fa7f0 és a 0x005643e0 függvényből hivatkozott. Az objektumot a 0x007fa7f0 építi (0x007facdb-0x007facf2, a `Preferences` és a `SlideshowEffectTime` sztringekkel).
- A küszöb előjel nélküli 32 bites érték: negatív értéknél +2^32 (0x008020b9-0x008020c5).
- Alapérték: 3 (0x007facd3, `mov [esp+0x3c], 3`, az objektum építése előtt). **Feltételes**: a 0x00407a20 belső alapérték-kezelését nem vizsgáltuk. A felhasználó tényleges értéke a registryből jön, a binárisból nem olvasható ki: **NINCS MEG**.
- Összehasonlítás lebegőpontosan, nem egész másodpercre levágva. A 0x008020cb-0x008020d4 `fcomp qword` alapján a léptetés akkor fut, ha a küszöb kisebb az eltelt időnél. Ha nem, csak a `[this+0x3c1]` nem nulla esetén léptet (0x008020d6-0x008020dd). A dekompilált `(LONGLONG)` öntés a diszasszemblálásban nem jelenik meg.
- A léptetés-döntés sorrendje (0x00802060, diszasszemblálva):
  1. `[this+0x3bb] != 0`: visszatér `1`-gyel, nincs léptetés (0x00802066-0x00802078).
  2. `[this+0x3b8]` és a 0x00801cb0 hívás (0x0080207e-0x00802093).
  3. `[this+0x518] != 0`: azonnal léptet (0x00802095-0x0080209e).
  4. Egyébként: léptet, ha a küszöb kisebb az eltelt időnél, vagy ha `[this+0x3c1] != 0`.
  5. Sikeres léptetés után `[this+0x518] = 0` és `[this+0x520]` = most (0x008020f2-0x00802108).
- **A képkocka-frissítés is újraindítja az időt.** A 0x00802230 sikeres frissítésnél `[this+0x520]` = most (0x008025b9-0x008025cf). Egy köztes újrarajzolás ezért eltolja a következő léptetést. Hogy milyen gyakran fut a frissítés: **RÉSZBEN JAVÍTVA (38.2.20, 2. szakasz):** a `0x007fb540` 50 ms-os ciklus, és csak a `[this+0x51a]` jelzőre hív (legfeljebb 20 Hz). A jelző-beállítás gyakorisága **NINCS MEG**.
- **Periódus.** Ha nincs köztes újrarajzolás, a léptetési küszöb **S másodperc**, ahol S a `SlideshowEffectTime` értéke. **PONTOSÍTVA (38.2.20, 1. és 7. szakasz):** ez küszöb, nem periódus; a léptetés az első, küszöb feletti callback-hívásnál történik. A pontos ütem a callback hívási ritmusától függ: **NINCS MEG**.
- **A callback (0x00803ab0).** Ha `[callback+8]` (QDrawable) nulla, `-1`-et ad (0x00803abc-0x00803ac0). Egyébként a QPC-t `[callback+0x18]`-ba írja (double), és ha `[QDrawable+0x3bf] == 0`, meghívja a 0x00802060-at (0x00803ac2-0x00803ae0).
- **Az átmenet indítója (0x007fda00).** Ha `[this+0x2d8] != 0` és `[this+0x538] != 0`, a 0x00802230-at `1`-es jelzéssel hívja, az időt `[this+0x430]`-ban rögzíti, majd beállítja a `[this+0x3ba] = 0`, `[this+0x3bb] = 0`, `[this+0x3b8] = 1`, `[this+0x3b9] = 1` jelzőket (dekompiláció 384-396. sor).

**3. Space (0x00801270, 0x00801130, 0x00803110).**

- A billentyű-kezelő (0x00801270) csak WM_KEYDOWN-ra (0x100) reagál. A 0x102 (WM_CHAR) más ágra megy (0x0080128e-0x0080129e). A szóköz a VK 0x20 (0x008012df-0x008012e1).
- Ha a globális `[0xd67849]` nem nulla, és a Ctrl (VK 0x11) le van nyomva (a `[0xc406f8]` importtal kérdezve), `[this+0x3ba] = 1`, a visszatérés 0x000F4240 (0x008012e3-0x008012fb).
- Egyébként, ha `[this+0x3bb] == 0`: `0x00801130(this)` (0x00801317-0x00801334), a visszatérés 0x000F4241.
- Ha `[this+0x3bb] != 0`: `0x00803110([this+0x2dc])` (0x00801319-0x0080131f), a visszatérés 0x000F4241.
- **0x00801130 (váltás).** `[this+0x3bb] = ([this+0x3bb] == 0)` (`sete`, 0x00801134-0x0080113f). A 0x0097e510 az új értékkel hívódik (0x00801146). Célja: **NINCS MEG**.
  - Új érték `1`: `0x00802c20(this)` (0x00801159). Ha `[this+0x3ba] == 0`: `0x00aa6f40(this+0x58)` (0x00801167-0x0080116a). Mindkét függvény belseje: **NINCS MEG**. Ettől a léptetés (0x00802060) nem fut.
  - Új érték `0`: `0x00802230(this, 0)` (0x00801178), majd `0x009aabf0([this+0x444])` (dekompiláció 352. sor).
- **0x00803110 (második ág).** `esi = [edi+0x25c]`, ahol `edi = [this+0x2dc]`. Ha `[esi+0x3be] != 0`: `0x00801cf0(esi)` (0x0080311d-0x00803127). `[esi+0x518] = 1` (0x00803131), vagyis a következő tick azonnal léptet. A QPC → `[esi+0x520]` (0x00803138-0x00803150). `[esi+0x3b8] = 0` és `[esi+0x428] = 0` (0x00803142-0x00803149). Végül `0x00801130(esi)` (0x0080315c): az `esi` jelzőjét 1-ről 0-ra váltja, vagyis folytat. Hogy `esi` azonos-e a `this`-szel: **NINCS MEG** (a `[this+0x2dc]` objektum felépítése nincs feltárva).

**Összegzés (Space).** A szóköz a léptetést szünetelteti és folytatja a `[this+0x3bb]` jelzőn keresztül. A nem nulla jelző tiltja a léptetést. A 38.2.18 „automatikus lejátszási” jelzője ezért félrevezető lehet: a név a menüből jön, a viselkedés más. Teljes képernyős ablak létrehozását a közvetlen ágban nem találtunk; a két hívott függvény (0x00802c20, 0x00aa6f40) belseje **NINCS MEG**.

**Billentyű-ágak, amelyeket nem ellenőriztünk.** A 38.2.18 szerint a Bal/Fel a 0x008011b0-ra, a Jobb/Le a 0x00801210-re megy. A diszasszemblálás szerint a Bal és Fel a 0x008014bc, a Jobb és Le a 0x008014ac ágra ugrik (0x008012bf-0x008012d9). A 0x008011b0 és a 0x00801210 hozzárendelését ebben a körben nem ellenőriztük.

**4. Eseménylista (0x0097d150).**

- A függvény a tulajdonos-szálat (`DAT_00d3a568`) és a rekurziószámlálót (`DAT_00d3a56c`) kezeli. Zárolás: a `DAT_00d3a570` kritikus szakasz, vagy a `DAT_00d3a554` jelzőtől függően egy vtable-zár (dekompiláció 242-255. sor).
- `arg2 = 0`: hozzáfűzés a globális mutatótömbhöz (`DAT_00d69418`, darabszám: `DAT_00d6941c >> 1`, bit0 jelző). A növekedés 2-hatványonként történik 1 MiB-ig, utána 1024 elemenként (dekompiláció 256-290. sor).
- `arg2 != 0`: a `0x00982400(&arg1)` keresés. Találat esetén nincs új tétel, visszatér 4-gyel. Ha nincs találat, `0x0097d640`.
- Sikeres hozzáfűzés után is `0x0097d640` hívódik (dekompiláció 283-287. sor). A 0x0097d640 tehát a közös vég.
- Hívóhelyek száma: 26 (a dekompilált fájl fejléce). A qshow-építő 0x007fa7f0 a 0x007fae76 címen hívja `arg2 = 1`-gyel (0x007fae73-0x007fae76: `push 1`, `push eax`), miután a callback-objektumot a 0x00803b00 vtable-beállítással felépítette (0x007fae6a).
- **NINCS MEG**: a lista futtatója, vagyis a periodikus hívó. A 0x0097d640 két hívója a 0x0097d150 és a 0x0097d370. A 0x0097d370-nek 23 hívója van az indexben, köztük a 0x007fb5a0, aminek egyetlen hívója a 0x007fae90. **JAVÍTVA (38.2.20, 1. szakasz):** a `0x0097d370` nem a periodikus hívó, a futtató a `0x0097fc30` üzenethurok.

**5. Vezérlők és forráskollekció.**

- **0x005e8a70 (CThumbUI::MakeTimeline).** A név sztringből is igazolt: a `CThumbUI::MakeTimeline` és a `Preparing timeline...` sztring ide mutat (string_xrefs).
  - **Kapcsoló.** A `Preferences\BigSlideshow2` objektumot a 0x005e9409-0x005e9415 építi, alapértéke `1` (`mov [esp+0x44], 1`, feltételes: a belső alapérték-kezelés nincs feltárva). A 0x005e941e-nál a 0x004019b0 olvassa, és a 0x005e9425 `jne` nem nulla értéknél a 0x005e95cc-re ugrik. Mi van ott: **NINCS MEG**.
  - **Számlálás (nulla érték esetén).** A `[ebx+0x2c0]` objektumon (`this+0x2c0`, 0x005e942e) a `0x004a0980` a darabszámot adja (0x005e9434). Ezután ciklus: `(*this)[0x90](i)` minden `i`-re (dekompiláció 491-519. sor, nem diszasszemblálva). A kollekció típusa és a rendezés: **NINCS MEG**.
  - **Szolgáltató.** `[this+0x2bc]` (dekompiláció 136, 175, 246, 291, 461. sor). A Shift-ágban (`GetAsyncKeyState(0x10)`, dekompiláció 244-245. sor) a szolgáltató `[+0x4ec]` darabszámú listáját járja be, és 13 típuskód alapján szűr (dekompiláció 250-256. sor). A típuskódok jelentése: **NINCS MEG**.
- **0x007fb210 (overlay-betöltés).** A string_xrefs szerint itt töltődnek: `overlays/left`, `overlays/right`, `overlays/mouse`, `overlays/rollovermouse`, `overlays/exit`, `overlays/timeline`, `overlays/timelinedot`, `overlays/sliderthumb`, `overlays/startbutton`, `overlays/overlay`. A rajzolás és a kattintás: **NINCS MEG**.
- **0x00a52890 (üzenetkezelő, `__thiscall`).** A dekompilált `switch` egér-üzeneteket kezel: 0x201-0x208 és 0x20a (dekompiláció 1401-1653. sor). Használja a SetCapture/ReleaseCapture párost, a ScreenToClient-et és a SetCursor-t (`LoadCursorA(0, 0x7f00)`, dekompiláció 1885-1886. sor). A 0x121 ágban (dekompiláció 1383-1396. sor) a `FindWindowExA(..., "#32768")` után két `PostMessageA` megy: WM_KEYDOWN és WM_KEYUP, VK 0x0D-vel. A függvény hívottjai között van 0x00a516c0, 0x00a51740 és 0x00a517c0, de hogy melyik végez hit-testet: **NINCS MEG**. A kattintási cél és a dátumcsúszka leképezése is nyitott.

**Bizonyítottsági fok (38.2.19).**

| állítás | bizonyíték | fok |
|---|---|---|
| x és y képlete, a float-trükk | 0x008022db-0x008023a1, a konstansok diszasszemblálva | megerősített |
| W és H jelentése (kép vagy kártya) | dekompiláció 126-130, 162-163. sor | feltételes |
| visszatérés 4 és 0 | 0x008022b7, 0x0080260e | megerősített |
| visszatérés -1 | dekompiláció 126-130. sor | feltételes |
| előző érték írása | 0x008022c3-0x008022d5 | megerősített |
| előző érték olvasása | NINCS MEG | nyitott |
| eltelt idő, küszöb, léptetési feltétel | 0x009a51b0, 0x004019b0, 0x008020ae-0x008020dd | megerősített |
| alapérték 3 (SlideshowEffectTime) | 0x007facd3 | feltételes |
| felhasználói registry-érték | NINCS MEG | nyitott |
| léptetési periódus S másodperc | a képlet szerint; köztes frissítés és callback-ütem nélkül | feltételes |
| Space = szünet és folytatás | 0x00801130, 0x00803110, 0x008012e3-0x00801334 | megerősített |
| a 0x00801130 mellékhatásai | NINCS MEG | nyitott |
| eseménylista (0x0097d150) | dekompiláció 242-323. sor; hívó 0x007fae76 | megerősített (hozzáfűzés, keresés) |
| periodikus futtató | NINCS MEG | nyitott |
| BigSlideshow2 kapcsoló és számláló | 0x005e9409-0x005e9434 | megerősített (az ágválasztás); a nulla ág tartalma: nyitott |
| overlay-nevek | string_xrefs, 0x007fb210 | megerősített (betöltés); rajzolás: NINCS MEG |
| üzenetkezelő (0x00a52890) | dekompiláció 1401-1653. sor | megerősített (üzenetkódok); hit-test: NINCS MEG |

**Nyitott - következő Ghidra-körök.**

- ~~`Ghidra-kör kell: 0x00802180 - a 0x00802230 param_2 != 0 ágában hívódik, és a 0x0080275b, 0x00802765 ágak tartalma [blokkoló]`~~ **JAVÍTVA (38.2.20, 3. szakasz):** a `0x00802180` a `CarefulEnhance` beállítást alkalmazza, nem átmenet; a hívóhely `0x008025af` igazolt. A `0x0080275b` és `0x00802765` ágak tartalma: `Ghidra-kör kell: 0x00802630 - a 0x0080275b és 0x00802765 ágak tartalma [blokkoló]`.
- ~~`Ghidra-kör kell: 0x0097d370 és 0x007fae90 - a 0x0097d640 futtatójának és a periodikus hívónak az azonosítása [blokkoló]`~~ **JAVÍTVA (38.2.20, 1. szakasz):** a `0x0097d370` nem periodikus hívó, a tulajdonos szerinti törlő; a `0x0097d640` zárkezelő-vég; a léptetést a `0x0097fc30` üzenethurok hajtja.
- `Ghidra-kör kell: 0x007fb540 - a 0x00802230 hívóinak gyakorisága, mert ez tolja a léptetési időzítést [blokkoló]`
- ~~`Ghidra-kör kell: 0x005e95cc - a BigSlideshow2 nem nulla ága, amely az alapértelmezett 1 mellett fut [blokkoló]`~~ **JAVÍTVA (38.2.20, 4. szakasz):** a `0x005e95cc` közös pont a zéró-ág után, nem külön ág; a nem nulla ág a `uStack_d0` listát ellenőrzi, a `[this+0x3084]` objektumot építi és a `MP3SlideshowPath` értéket olvassa.
- `Ghidra-kör kell: 0x00a516c0, 0x00a51740, 0x00a517c0 - a 0x00a52890 hit-test függvényei és a kattintási cél [blokkoló]`
- ~~`Ghidra-kör kell: 0x00803110 - a [this+0x2dc] objektum felépítése, és hogy azonos-e a this-szel (a Space-visszatéréshez) [blokkoló]`~~ **JAVÍTVA (38.2.21, 4. szakasz):** `[this+0x2dc]` OneUpUI, és az `esi` azonos a `this`-szel.
- `Ghidra-kör kell: 0x00802c20, 0x00aa6f40 - a szüneteltetés mellékhatása [nem blokkoló] (a `0x0097e510` azonosítva: `ShowCursor`-váltás, 38.2.20, 7. szakasz)`
- `Ghidra-kör kell: 0x009a4890, 0x00407a20 - a registry-olvasó és az objektum-építő alapérték-kezelése (az alapértékek megerősítése) [nem blokkoló]`
- `Ghidra-kör kell: a [this+0x408] és [this+0x40c] olvasóinak pásztázása (paszta.py, teljes .text) [nem blokkoló]`

**Dekompiláló-hibák, amelyeket a diszasszemblálás felülírt.** A Ghidra-kimenet három helyen téved, és ezt a jövőbeli köröknek is tudniuk kell.

- 0x00802230, sor 102: `(float)((r + 0x3f8000) * 0x100)` bitminta-újraértelmezés (`fld dword`), nem számértékű öntés.
- 0x00802060, sor 434: `(LONGLONG)` öntés nincs a diszasszemblálásban; a bináris lebegőpontos összehasonlítást végez.
- 0x00802230, sor 135: `ROUND(_DAT_00d35808)` valójában csonkolás (RC=11), a betöltött érték 2276.

**A #5401 „Kész, ha” pontjai (2. kör).** (1) Képlánc és forráshalmaz: a kollekció számlálója és a bejárás ismert; a forrás típusa és rendezése nyitott, az alapértelmezett BigSlideshow2 mellett pedig a 0x005e95cc ág fut, nem a számláló ág. (2) Átmenet: a mozgásképlet és a léptetési feltétel bináris; a rajz-geometria megfeleltetése, a periódus pontos üteme és a felhasználói registry-érték nyitott. (3) Vezérlők: a Space-kapcsolás megerősített; a hit-test és a dátumcsúszka nyitott. (4) Diavetítés és visszatérés: a szüneteltetés és a folytatás megerősített; a teljes képernyős ablak és a visszatérési állapot nyitott.

**Fejlesztési következmény.** Ebben a körben terméki kódot nem írtunk. A mozgásképlet most bináris, de a fejlesztéshez még hiányzik a rajzoló geometriája, a periodikus hívó (0x0097d370) és a BigSlideshow2 nem nulla ága (0x005e95cc). A felhasználó registry-értékeit (SlideshowEffectTime, BigSlideshow2) nem ismerjük, és nem is becsültük.

#### 38.2.20 Az Időrend bináris feltárása, 3. kör: pumpa, lekérdező jelző, CarefulEnhance, BigSlideshow2, vezérlők, visszatérés (#5401, 2026-10-20)

**Kérdés és hatókör.** A 38.2.19 hat nyitott tétele: (1) ki hajtja a léptetést (0x0097d370, 0x007fae90); (2) a 0x007fb540 hívási gyakorisága a 0x00802230-ra; (3) a 0x00802180 param_2 != 0 ága; (4) a 0x005e95cc, vagyis a BigSlideshow2 nem nulla ág; (5) a 0x00a516c0, 0x00a51740, 0x00a517c0 találati vizsgálata és a dátumcsúszka; (6) a 0x00803110 és a diavetítésből való visszatérés pozíciója.

**Bemenet és eszközök.** A három Ghidra-kimenet (scratchpad: `idorend-1`, `idorend-2`, `idorend-3`), a helyi bináris-index olvasásban, és a `pe_dis` diszasszemblálása (capstone). Futásfelvétel és QEMU-futtatás nem volt. Terméki kódot nem írtunk.

**Módszer.** Ahol a cím után `diszasszembly` áll, a bájtokat a `pe_dis` adta. Ahol `dekompiláció` áll, csak a Ghidra-kimenetből származik. Ha a kettő eltért, a diszasszembly érvényes, és ezt kimondjuk. Az IAT-slotokat a PE import-táblából számoltuk, és ellenőriztük: Sleep = `0x00c402d0`, ShowCursor = `0x00c40700`, QueryPerformanceCounter = `0x00c40298`, PeekMessageA = `0x00c40844`; mind a négy megegyezik a kódban látott `mov reg,[slot]` hivatkozással. A vtable-ok típusát az RTTI-tábla adja: `0x00cbd66c` = `QDrawable::vftable`, `0x00cbd6c8` = `ytCallback<QDrawable>::vftable`. Független újralevezetés (#140) nem készült, ezért a bizonyítottsági fok a saját méréseinkből áll.

**Javítások a 38.2.19-ben.** Négy állítás a 38.2.19-ben tévesnek vagy elavultnak bizonyult; a 38.2.19 érintett sorai át vannak húzva és jelölve.

- `0x0097d370` **nem** periodikus hívó. A dekompiláció szerint a tulajdonos (`[elem+8]`) szerint töröl, és a törlő ág `vtable[0](1)` hívással szabadít. A 38.2.19 hipotézise (periodikus hívó) elvetve.
- `0x0097d640` **nem** futtató. Importjai (`EnterCriticalSection`, `LeaveCriticalSection`, `GetCurrentThreadId`) zárkezelő-vég. A futtató a `0x0097fc30` üzenethurok (1. szakasz).
- `0x00802180` **nem** átmenet vagy animáció. A törzsében nincs időbélyeg és nincs pozícióírás; a `CarefulEnhance` beállítást alkalmazza (3. szakasz).
- `0x005e95cc` **nem** önálló ág. A zéró-ág utáni egyesítési pont, és a nem nulla BigSlideshow2 ág ettől indul (4. szakasz).

**1. Ki hajtja a léptetést, és milyen periódussal?**

Bináris (diszasszembly), a `0x0097d370` és a `0x007fae90` **nem** hajtja a léptetést:

- `0x007fae90`: skaláris törlő dtor. Hívja a `0x007fb5a0`-t (`call 0x007fb5a0`, 0x007fae94), majd ha az argumentum bit 0 értéke 1, a `0x0097caf0`-t. Ez a `QDrawable::vftable` 0. slotja (`0x00cbd66c`).
- `0x0097d370`: a tulajdonos szerinti eltávolító (dekompiláció). Hívója a `0x007fb5a0` (`QDrawable` dtor), amelyet a `0x007fae90` hív.

A léptetés hajtója a **`0x0097fc30` üzenethurok** (diszasszembly, megerősített):

- `PeekMessageA` (IAT `0x00c40844`, betöltés `0x0097fc84`), a hurok többi ága a `DispatchMessageA`, `TranslateMessage`, `TranslateAcceleratorA`, `IsDialogMessageA` importokat is használja (index).
- `MsgWaitForMultipleObjects` (IAT `0x00c40720`), hívás `0x0098032a`: `nCount = [0xd69424] >> 1`; `pHandles = [0xd69420]`, ha `nCount != 0`; `fWaitAll = 0`; `dwMilliseconds` = a függvény első paramétere (`[ebp+8]`, `0x0098030f`); `dwWakeMask = 0x4FF` (QS_ALLINPUT).
- Csak akkor vár, ha az eltelt idő 0,005 s-nál kisebb (`0x009802f9-0x00980308`: `fcomp dword [0x00cf4b50]`, az érték f32 = 0,005; ha nem kisebb, a `jp 0x00980373` átugorja a várakozást). Az eltelt idő `((a - b) / QPF)`, ahol `a = [esp+0x38]`, `b = [esp+0x70]` (két QPC-érték). Az időbélyegek forrása **NINCS MEG**.
- Az időtúllépés a hívótól jön. Tíz hívóhely van (az utolsó `push` a `call` előtt, diszasszembly): **JAVÍTVA (38.2.21, 1. szakasz):** tizenegy van, a kimaradt `0x006fb417` 1 ms-os.
  - 1 ms: `0x0040e4b1` (`0x0040e410`), `0x005fff71` (`0x005ffc30`), `0x006fe680` (`0x006fe630`), `0x009d4dc6` (`0x009d4d10`);
  - 5 ms: `0x00405a55` (`0x004051b0`), `0x0059ec5e` (`0x0059e920`), `0x0074227c` (`0x007420f0`), `0x0074239c` (`0x007422d0`);
  - 10 ms: `0x0094ab72` (`0x0094aa00`), `0x0094ad8c` (`0x0094ace0`).
- A hurok a `0x00982270` bejárót hívja (`0x0097feac`, dekompiláció és diszasszembly), a zárolt szakaszon belül. A `0x00982270`-ben nincs közvetlen `call [reg+4]` (a callback slot+4 hívása), ezért a bejárás és a `0x00803ab0` callback közti lánc **NINCS MEG**. **JAVÍTVA (38.2.21, 1. szakasz):** a visszahívást a pumpa maga hívja, a `0x0097fff5`-nél (`call [vtable+4]`), a bejárón kívül.

**Válasz (1):** a léptetést a `0x0097fc30` üzenethurok hajtja (megerősített). Az Időrend alatt futó pumpa azonosítása (a tíz hívó közül melyik, a `0x0094aa00` vagy `0x0094ace0` a 10 ms-os jelölt) **NINCS MEG**, ezért a periódus is **NINCS MEG**. A 38.2.19 `S másodperc` értéke küszöb, nem periódus (lásd 7. szakasz).

**2. A 0x007fb540 hívási gyakorisága a 0x00802230-ra.**

Diszasszembly (`0x007fb540-0x007fb58f`, megerősített):

- Ciklus: a `vtable[1]` predikátum (`0x00408b30`: `InterlockedCompareExchange`-olvasás, a `[this+8] != 0` esetén igaz) ellenőrzése után, ha `[this+0x51a] != 0`, hívja a `0x00802230(this, 1)`-et, majd nullázza a jelzőt (`0x007fb571`). Ezután `Sleep(0x32)` (50 ms, `0x007fb57a`), és újra a predikátum.
- Egy iterációban legfeljebb egy hívás, és egy iteráció legalább 50 ms. Felső korlát: 20 hívás másodpercenként.
- A ciklus hívója a `QDrawable::vftable` 2. slotja (`0x00cbd674` = `0x007fb540`). A tényleges indirekt hívó **NINCS MEG**.
- A jelzőt a `0x00801c19` állítja (`mov byte [edi+0x51a], 1`, a `0x008018a0` függvényben). Ennek hívói: a `0x00801cb0` (ezt a `0x00802060` hívja `0x00802087`-nél, ha `[this+0x3b8] != 0`), valamint a `0x008037e0` és a `0x007fde80`. A beállítás gyakorisága **RÉSZBEN JAVÍTVA (38.2.21, 2. szakasz):** a hívók és a feltételeik megvannak.
- Sorrend-megfigyelés (diszasszembly): a jelzőt a hívás **után** törli, zár nélkül. A hívás alatti írást a törlés elveszti. Ez a bináris sorrend; a következménye csak párhuzamos íráskor számít (feltételes).

**Válasz (2):** a `0x00802230` hívása legfeljebb 20 Hz, és csak akkor, ha a `[this+0x51a]` jelző 1. A jelző beállításának gyakorisága **NINCS MEG**.

**3. A 0x00802180 param_2 != 0 ága.**

- Hívóhely: `0x008025af`. Előtte `0x008025a4`: `cmp byte [esp+0x8c], bl`, `je 0x008025b4`. A `bl` nulla, mert a `0x00802234` `xor ebx,ebx`. Tehát a hívás csak nem nulla `param_2`-nél történik (diszasszembly).
- `param_2 = 1` hívók: `0x007fb56c` (a 2. szakasz lekérdező ciklusa, diszasszembly `push 1`, `0x007fb569`) és `0x007fda4f` (`0x007fda00`, dekompiláció). `param_2 = 0` hívók: `0x00801d05` (`0x00801cf0`, diszasszembly `push 0`) és `0x00801178` (`0x00801130`, dekompiláció). A `0x008026e9` (a `0x00802630`-ból) `ebx`-et ad át; `ebx = 0` a `0x00802638`-nál, a köztes út nincs teljesen ellenőrizve.
- A törzs (dekompiláció, string-xref): a `Preferences` / `CarefulEnhance` kulcsot olvassa (`0x00802180` a sztring-hivatkozás). A getter (`0x004019b0`) alapértéke `_DAT_00cf3ed0` = `0xBF800000` (4 bájt; lebegőpontosként -1,0, a típust a `0x009db610` dönti el). Az eredményt a `this+0x46c` alobjektumra állítja (`0x009db610`), majd `0x00aa40a0`-t hív `_DAT_00c49618`-cel (`0x40400000`, lebegőpontosként 3,0), végül `0x009ab410`-et (`this+0x46c`, `this+0x648`, -1 négyszer).

**Válasz (3):** a `0x00802180` a `CarefulEnhance` beállítást alkalmazza. **Nem** átmenet vagy animáció: nincs QPC, nincs pozícióírás. Hogy a beállítás mit csinál a képpel, **NINCS MEG** (`0x009db610`, `0x009ab410`, `0x00aa40a0` nincs feltárva).

**4. A 0x005e95cc (BigSlideshow2 nem nulla ág).**

- `0x005e9409-0x005e9425` (diszasszembly): a `Preferences\BigSlideshow2` olvasása (alapérték 1), majd `test eax,eax; jne 0x005e95cc`.
- A `0x005e95cc` **közös pont**: a zéró-ág (`BigSlideshow2 == 0`, a kollekció-bejárás a `0x004a0980` darabszámmal és a `this+0x90` callbackkel) utáni `FUN_00401000(); piStack_b0 = 0; FUN_00401000();` sorok kezdete (dekompiláció, a törzs 533. sora). **JAVÍTVA (38.2.21, 5. szakasz):** a közös pont a 529-531. sor, az 533. sor az `IDS_MUST_SELECT` ágé. Nem nulla értéknél a zéró-ág kimarad.
- Utána (`0x005e95e6`): `test [esp+0x30], 0xfffffffe; je 0x005e97ce`. A `0x005e97ce` az `IDS_MUST_SELECT` ág (dekompiláció): üres kiválasztás hibát ad.
- Képforrás: a `uStack_d0` lista (dekompiláció, 212-285. sor). A Shift-ágban (`GetAsyncKeyState(0x10)`, dekompiláció 245. sor) a `[this+0xaf]+0x4ec` provider-listát járja be, és 13 típuskódra szűr: 2, 3, 6, 7, 13, 31, 14, 18, 24, 22, 27, 28, 26. A Ctrl (0x11) állapotát a `cStack_d9` jelző adja. A Ctrl és Shift nélküli alapút feltöltése (dekompiláció 350-447. sor) **NINCS MEG**.
- Rendezés: **NINCS MEG** (a rendezési mező és sorrend nincs feltárva).
- Utána (`0x005e95f4-0x005e961d`, diszasszembly): ha `[this+0x3084] == 0`, 8 bájtos objektum (`push 8`, `0x0097c5d0` foglalás), építés `0x0052e3c0`-lal, tárolás `[this+0x3084]`-be.
- Utána (`0x005e9628-0x005e964d`, diszasszembly): a `Preferences` / `MP3SlideshowPath` (sztring `0x00c97920`) kulcs olvasása (`0x00407630`, `0x004078e0`). A kulcs neve alapján a diavetítés zenéjének útvonala; a felhasználói érték **NINCS MEG**.

**Válasz (4):** a nem nulla ág a `uStack_d0` kiválasztott listát használja képforrásként (nem a kollekció teljes bejárását), üres listánál hibát ad. A Ctrl nélküli alapút feltöltése és a rendezés **NINCS MEG**. Az ág a `[this+0x3084]` objektumot hozza létre, és a `Preferences\MP3SlideshowPath` értéket olvassa.

**5. A három függvény és a vezérlők.**

- `0x00a516c0`, `0x00a51740` és `0x00a517c0` **nem** találati vizsgálat. Mindhárom az `ytUIEvent::vftable`-t írja a `[this]`-be, és az argumentumokból tölti a mezőket (dekompiláció). Eseménykonstruktorok:
  - `0x00a516c0` (float, pozíció, float, jelző): típus `0x0E + (jelző != 0)`, vagyis 14 vagy 15; pozíció a `+0x5C` / `+0x60` mezőkben. Hívó: `0x00a53707` (az üzenetkezelő `0x20a` / `0x5850534d` ága).
  - `0x00a51740` (pozíció): típus `0x10`. Hívó: `0x00a535f0` (a `0x8000009` ág).
  - `0x00a517c0` (téglalap, típus): típus az átadott érték (`0x11` vagy `0x12`). Hívók: `0x00a534e7` (`0x8000008`) és `0x00a53754` (`0x800000a`).
- A találatot az elosztás adja: `FUN_009e4630(esemény, &kimenet)`. Az üzenetkezelő az `1000000` (0xF4240) visszatérési értéket vizsgálja; ezt a konstanst a Space-ág is visszaadja. A `0x009e4630` belseje **NINCS MEG**.
- Vezérlők (`sliderthumb`, `timelinedot`, `startbutton`, `exit`, listaikon) kattintási célja és a dátumcsúszka leképezése **NINCS MEG**. A `0x007fb210` csak betölti az overlay-neveket (38.2.18), a rajz- és találati téglalapok nincsenek feltárva.

**Válasz (5):** a három függvény eseménykonstruktor, nem találati vizsgálat. Melyik vezérlő mire reagál, és a dátumcsúszka leképezése **NINCS MEG**.

**6. A 0x00803110 és a diavetítésből való visszatérés pozíciója.**

- Hívóhely (diszasszembly, `0x00801319-0x0080131f`): a `0x00801270` (a `QDrawable` Space-kezelője, a `QDrawable::vftable` tagja) `mov eax,[ebx+0x2dc]` után hívja a `0x00803110`-et. További hívók: `0x008032e0` (`OneUpUI`) a `0x00803486` és `0x008034c5` címen (dekompiláció, a 38.2.18 szerint).
- Törzs (a teljes `0x00803110-0x00803161`, diszasszembly): `X = eax` (`[this+0x2dc]`); `esi = [X+0x25c]`; ha `[esi+0x3be] != 0`, hívja a `0x00801cf0`-t; `[esi+0x518] = 1` (a következő léptetés azonnal fut); QPC a `[esi+0x520]`-ba; `[esi+0x3b8] = 0`; `[esi+0x428] = 0`; majd `0x00801130(esi)`, ami a `[esi+0x3bb]` jelzőt 1-ről 0-ra állítja (folytatás); végül `[X+0x50] != 0` esetén a `0x00802be0`.
- Pozíció: a `0x00803110` nem írja a `[esi+0x3f4]` indexet (a teljes törzs diszasszemblálva). A folytatásnál a `0x00802230(esi, 0)` a `[esi+0x3f8]`-ba írja az utolsó megjelenített indexet (dekompiláció). Tehát a visszatérés pozíciója a szüneteltetéskori index.
- `X` típusa és az `esi == this` azonosság **NINCS MEG**. `X`-et a `0x007fa7f0` építő írja (`0x007fae55`, `mov [ecx+0x2dc], eax`, bájt-keresés). Ha `esi != this`, a Space-ág a `this+0x3bb` jelzőt nem tudja visszaállítani, mert a folytatás az `esi` jelzőjét írja. Ez logikai következtetés, nem mért állítás.

**Válasz (6):** a visszatérés pozíciója a szüneteltetéskor érvényes `[esi+0x3f4]` index (a `0x00803110` nem írja). `X` típusa és az `esi == this` azonosság **NINCS MEG**.

**7. Új megfigyelések (38.2.20).**

- `0x0097e510` (diszasszembly, a `ShowCursor` IAT-ja `0x00c40700`): a paraméter 1 (szünet) esetén `ShowCursor(TRUE)` hívások a számláló 0-ig; 0 (folytatás) esetén `ShowCursor(FALSE)` a -1-ig. Szünetben a kurzor látszik, folytatáskor rejtett. A `0x007fda00` a diavetítés indításakor `0`-val hívja.
- A `QDrawable::vftable` (`0x00cbd66c`) 0. slotja a `0x007fae90`, 1. slotja a `0x00408b30`, 2. slotja a `0x007fb540`. A `ytCallback<QDrawable>::vftable` (`0x00cbd6c8`) 1. slotja a `0x00803ab0`.
- `0x00803ab0` (diszasszembly): a `[cb+0x18]`-ba írja a QPC-t (`fild qword`, `fstp qword`); ha `[QDrawable+0x3bf] == 0`, hívja a `0x00802060`-at a `[cb+8]` QDrawable-ra.
- `0x00802060` küszöb-összehasonlítása lebegőpontos (diszasszembly, `0x008020aa-0x008020d4`): az eltelt idő `fstp qword [esp+8]`-ba kerül (`0x009a51b0`), a küszöb `fild dword` (`0x004019b0`). A léptetés akkor fut, ha az eltelt idő nagyobb a küszöbnél. A Ghidra `LONGLONG` öntése a kimenet hibája, a bináris nem egész másodpercre vág.
- Léptetési lánc: `0x00802060` → `0x00801cb0` (ha `[this+0x3b8] != 0`) → `0x008018a0` (a jelző beállítása, 2. szakasz).

**8. Konstansok** (`pe_dis`, `f32` / `f64` / `int32`):

| bináris cím | típus | érték | szerep |
|---|---|---|---|
| `0x00cf4b50` | f32 | 0,005 | a pumpa 5 ms-os küszöbe (1. szakasz) |
| `0x00cf3ed0` | int32 | `0xBF800000` (-1082130432) | a `CarefulEnhance` getter alapértéke (3. szakasz) |
| `0x00c49618` | f32 bitminta | `0x40400000` = 3,0 | a `0x00aa40a0` argumentuma (3. szakasz) |
| `0x00cf4320` | f64 | 0,1499999761581421 | a `c` szorzó (38.2.19) |
| `0x00c72150` | f64 | 0,5 | a y-ág fele (38.2.19) |
| `0x00cf39e4` | f32 | 4294967296 (2^32) | negatív W előjel-korrekciója (38.2.19) |
| `0x00cf3ac0` | f64 | 4294967296 (2^32) | negatív H előjel-korrekciója; a `0x00802060` küszöbén is (38.2.19) |
| `0x00d35808` | f32 | 2276,5556640625 | a `p[0xb9]` ágban (38.2.19) |

**9. KIZÁRTAM (ne járják újra).**

- `0x0097d370` mint periodikus hajtó: a törlő ág nem léptet (1. szakasz).
- `0x0097d640` mint futtató: zárkezelő-vég (1. szakasz).
- `0x00802180` mint átmenet vagy animáció: a törzsében nincs időbélyeg, nincs pozícióírás (3. szakasz).
- `0x00a516c0`, `0x00a51740`, `0x00a517c0` mint találati vizsgálat: eseménykonstruktorok (5. szakasz).
- A `LONGLONG`-küszöbös léptetés (Ghidra): a diszasszembly lebegőpontos (2. és 7. szakasz).
- A `0x005e95cc` mint önálló nem nulla BigSlideshow2 ág: közös pont (4. szakasz).

**Bizonyítottsági fok (38.2.20).**

| állítás | bizonyíték | fok |
|---|---|---|
| `0x0097d370` nem periodikus, a tulajdonos szerinti törlő | dekompiláció `0x0097d370`; `0x007fae90` diszasszembly; RTTI | megerősített (szerep); a belső ciklus dekompiláció |
| `0x007fae90` skaláris törlő dtor, `QDrawable::vftable` 0. slot | diszasszembly `0x007fae90`, RTTI `0x00cbd66c` | megerősített |
| pumpa `0x0097fc30`: PeekMessageA, MsgWait, időtúllépés = paraméter | diszasszembly `0x0098030f-0x0098032a`; IAT-leképezés (4 slot ellenőrizve) | megerősített |
| 5 ms-os ág (`0x00cf4b50`) | diszasszembly `0x009802f9-0x00980308`, konstans | megerősített (feltétel); az időbélyegek forrása NINCS MEG |
| tíz hívóhely 1, 5 vagy 10 ms | diszasszembly (utolsó `push` a `call` előtt) | megerősített |
| pumpa hívja a bejárót (`0x00982270`) | diszasszembly `0x0097feac` | megerősített |
| bejáró hívja a 0x00803ab0 callbacket | nincs `call [reg+4]` a bejáróban | NINCS MEG |
| `0x007fb540`: 50 ms-os ciklus, `0x00802230(this,1)` a jelzőre | diszasszembly `0x007fb540-0x007fb58f` | megerősített |
| jelző-író `0x00801c19` (`0x008018a0`) | bájt-keresés, diszasszembly | megerősített (író); hívási gyakoriság NINCS MEG |
| `QDrawable` slot+8 hívója | indirekt hívás | NINCS MEG |
| `0x00802180`: CarefulEnhance, nem átmenet | `cmp bl` diszasszembly `0x008025a4`; string-xref; dekompiláció törzs | megerősített (hol és mit); vizuális hatás NINCS MEG |
| `0x005e95cc` közös pont, `uStack_d0` ellenőrzés | diszasszembly `0x005e9425`, `0x005e95e6`; dekompiláció 533. sor | megerősített |
| `MP3SlideshowPath` olvasása a nem nulla ágban | diszasszembly `0x005e9628-0x005e964d`; sztring `0x00c97920` | megerősített (a kulcs); felhasználói érték NINCS MEG |
| 13 típuskódos szűrő a Shift-ágban | dekompiláció 245-256. sor | feltételes (dekompiláció) |
| Ctrl nélküli képforrás, rendezés | **RÉSZBEN (38.2.21, 5. szakasz):** rendezés nincs, körforgatás van; a forrás NINCS MEG | nyitott |
| `0x0097e510` = ShowCursor-váltás | diszasszembly, IAT `0x00c40700` | megerősített |
| `0x00803110`: esi = `[X+0x25c]`, nincs írás `[+0x3f4]` | diszasszembly, teljes törzs | megerősített |
| `X` típusa, `esi == this` | **JAVÍTVA (38.2.21, 4. szakasz):** OneUpUI, és `[X+0x25c]` = this | megerősített |
| `0x00a516c0/0x00a51740/0x00a517c0` = eseménykonstruktor | dekompiláció (vftable-írás, mezők), hívóhelyek | feltételes (dekompiláció, nincs diszasszembly) |
| találati vizsgálat és vezérlő-leképezés, dátumcsúszka | NINCS MEG (`0x009e4630` belseje) | nyitott |

**Nyitott - következő Ghidra-körök.**

- `Ghidra-kör kell: 0x0097fc30 - a [esp+0x38] és [esp+0x70] időbélyegek forrása, a 0x00980373 utáni feldolgozó ág, és a 0x00982270 callback-hívása [blokkoló]` **RÉSZBEN JAVÍTVA (38.2.21, 1. szakasz):** a visszahívás nem a 0x00982270-ből hívódik, hanem a pumpából (`0x0097fff5`).
- ~~`Ghidra-kör kell: 0x0094aa00 és 0x0094ace0 - melyik a 10 ms-os pumpa, és fut-e az Időrend alatt [blokkoló]`~~ **SZŰKÍTVE (38.2.21, 1. szakasz):** mindkettő webböngésző-pumpa. Az Időrend-pumpa a `0x0097fc30` hívói közül **NINCS MEG** (`Ghidra-kör kell: 0x00983430, 0x00983fc0, 0x00982bf0 [blokkoló]`).
- `Ghidra-kör kell: 0x007fb540 slot+8 hívója (CreateThread / _beginthreadex hívóhelyek vagy QDrawable-futtató), és a 0x008018a0 hívóinak gyakorisága (0x007fde80) [blokkoló]` **RÉSZBEN JAVÍTVA (38.2.21, 2. szakasz):** a 0x008018a0 hívói: 0x007fde80 (0x007fe33e), 0x00801cb0 (0x00801ce5), 0x008037e0 (0x00803953). A 0x007fb540 közvetett hívója még NINCS MEG.
- `Ghidra-kör kell: 0x005e8a70 - a uStack_d0 lista feltöltése a Ctrl és Shift nélküli ágban (dekompiláció 350-447. sor), a rendezési mező [blokkoló]` **RÉSZBEN JAVÍTVA (38.2.21, 5. szakasz):** a 350-453. sor körforgatás, rendezés nincs; az Időrend-ág forrása NINCS MEG.
- `Ghidra-kör kell: 0x009e4630, 0x0052d3c0, 0x0052d430 - az ytUIEvent találati és elosztási útja, a csúszka és a gombok leképezése [blokkoló]` **RÉSZBEN JAVÍTVA (38.2.21, 3. szakasz):** az elosztó és a típusok megvannak; a csúszka és a gombok leképezése NINCS MEG.
- `Ghidra-kör kell: 0x007fa7f0 a 0x007fae55 körül - az [this+0x2dc] objektum típusa, és hogy [X+0x25c] == this [blokkoló]` **JAVÍTVA (38.2.21, 4. szakasz):** OneUpUI, és `[X+0x25c]` = this.
- `Ghidra-kör kell: 0x009db610, 0x009ab410, 0x00aa40a0 - a CarefulEnhance beállítás vizuális hatása [nem blokkoló]`
- `Ghidra-kör kell: 0x0097da20 - a 0xd69420 / 0xd69424 várakozási tömb tartalma; ha nCount = 0, a MsgWait csak időtúllépés és bemenet [nem blokkoló]`

**Fejlesztési következmény.** Terméki kódot nem írtunk. A léptetés periódusa (melyik pumpa, milyen időtúllépéssel) még nincs megállapítva, ezért nem implementálható. A CarefulEnhance vizuális hatása, a képforrás Ctrl nélküli ága és a dátumcsúszka leképezése is nyitott. Az 1, 5 és 10 ms pumpaidők nem tekinthetők az Időrend periódusának.

#### 38.2.21 Az Időrend bináris feltárása, 4. kör: üzenethurok és léptetési ütem, a jelző írói, találat és elosztás, OneUpUI, alapút (#5401, 2026-10-20)

**Kérdés és hatókör.** A 38.2.20 nyitott tételei öt kérdésben: (1) melyik üzenethurok fut az Időrend alatt, és mi a léptetési ütem; (2) ki és milyen gyakran állítja a `[this+0x51a]` jelzőt; (3) a `0x009e4630`, `0x0052d3c0` és `0x0052d430` találati és elosztási útja, a vezérlők és a dátumcsúszka; (4) a `0x007fa7f0` `[this+0x2dc]` objektuma, és teljesül-e `[X+0x25c] == this`; (5) a `0x005e8a70` alapútjának feltöltése és rendezése.

**Bemenet és eszközök.** A `2026-10-20-idorend-4.txt` kilenc függvénye, az `idorend-1` `0x005e8a70` és `0x008037e0` dekompilációja, a `pe_dis` diszasszemblálása (capstone), és a helyi index (`functions`, `rtti`). Futásfelvétel és QEMU-futtatás nem volt.

**Módszer.** Ahol egy állítás után `diszasszembly` áll, a bájtokat a `pe_dis` adta. Ahol `dekompiláció` áll, csak a Ghidra-kimenetből származik. A sorszámok a kimenetek fájlsorai (a dekompiláció törzse a fájl 69. sorától indul, így a 350-453. sor a `0x005e8a70` fájl 350-453. sora). A konstansok típusát a betöltő utasítás dönti el (`fcomp qword`, `fcomp dword`).

**Javítások a korábbi szakaszokban.** Az érintett sorok át vannak húzva és jelölve.
- 38.2.20 §1: a pumpának **tizenegy** közvetlen hívója van, nem tíz. A kimaradt `0x006fb417` `push 1`-gyel 1 ms-os.
- 38.2.20 §1: a visszahívást **nem** a `0x00982270` bejáró hívja. A pumpa hívja közvetlenül, a `0x0097fff5`-nél.
- 38.2.20 §1: a `0x0094aa00` és a `0x0094ace0` webböngésző-pumpa (`about:blank`, `ytCallback<WebBrowser>`), a tartalmuk szerint nem Időrend-specifikus.
- 38.2.20 §4: a közös pont a fájl 529-531. sora. Az 533. sor az `IDS_MUST_SELECT` ágé.
- 38.2.20 §6 és 38.2.19 §3: `X` **OneUpUI**, és `esi` azonos a `this`-szel (4. szakasz).
- Dekompiláció-hiba: a `0x007fe33e` hívása a dekompilációban argumentum nélkülinek látszik. A diszasszembly szerint EAX a `0x007fd800` kimeneti mezőjéből jön (2. szakasz).

**1. Üzenethurok és léptetési ütem.**

- **Hurok:** a `0x0097fc30` (megerősített: `PeekMessageA`, `MsgWaitForMultipleObjects`). Az Időrend alatti közvetlen hívója **NINCS MEG**. A tizenegy közvetlen hívó időtúllépése (diszasszembly, az utolsó `push` a `call` előtt):
  - 1 ms: `0x0040e4b1`, `0x005fff71`, `0x006fb417`, `0x006fe680`, `0x009d4dc6`;
  - 5 ms: `0x00405a55`, `0x0059ec5e`, `0x0074227c`, `0x0074239c`;
  - 10 ms: `0x0094ab72`, `0x0094ad8c`.
- **A 10 ms-os jelöltek:** a `0x0094aa00` `about:blank` lapot nyit (kimenet 404. sor), a `0x0094ace0` `ytCallback<WebBrowser>` objektumot hoz létre (501. sor). Az Időrend alatti futásukat nem zártuk ki, a tartalmuk alapján viszont nem Időrend-specifikusak. A hívóik: a `0x0094aa00`-nak három (`0x00593450`, `0x006fc7d0`, `0x006fcb60`), a `0x0094ace0`-nak tíz (441-451. sor). **NINCS MEG**, melyik fut az Időrend alatt.
- **Egy pumpa-kör (megerősített, kimenet és diszasszembly):**
  1. Üzenetkeret: legfeljebb 10 ms üzenetfeldolgozás. A `0x0097fe11` `fcomp qword` ellenőrzi a `0x00cf40b8` = 0,01 s értéket (kimenet 137-138. sor).
  2. A `0x00982270` összeállítja a bejegyzések listáját (`0x0097feac`, kimenet 168. sor).
  3. Minden bejegyzésre lejárat-ellenőrzés: `(most - [+0x18]) × (1/QPF) × 1000 >= [+0x20]` (kimenet 195-197. sor; `0x0097ff79` `fmul qword` a `0x00cf3e10` = 1000,0).
  4. Hívás: `mov edx,[esi]`, `mov eax,[edx+4]`, `call eax` (`0x0097ffe3-0x0097fff5`, diszasszembly). Ez a bejegyzés vtable-jének 1. slotja, `ecx = esi`, és argumentum a `(most - [+0x10]) / QPF` dupla szám. A `ytCallback<QDrawable>` vtable (`0x00cbd6c8`) 1. slotja a `0x00803ab0` (index-RTTI és a slot-érték egyezik).
  5. `0x00803ab0` (diszasszembly `0x00803ab0-0x00803aec`): ha `[+8]` (a QDrawable) nulla, `-1`. Egyébként `[+0x18] = QPC` (`0x00803ad4`), és ha `[QDrawable+0x3bf] == 0`, `0x00802060`. Egyébként `-1`.
  6. A visszatérés kezelése (kimenet 207-210. sor): `>= 0` → `[+0x20]` lesz az érték; `-2` → a kör többi lejárt bejegyzése kimarad; `-1` → a bejegyzés eltávolítása (kimenet 211-317. sor). A `0x00802060` soha nem ad `0`-t.
- **A léptetés döntése (`0x00802060`, diszasszembly `0x00802060-0x00802125`):**
  1. `[this+0x3bb] != 0` (szünet): visszatérés `1`.
  2. `[this+0x3b8] != 0`: `0x00801cb0` (`0x00802087`). Ha a jelző még nem nulla, az 5. pont.
  3. `[this+0x518] != 0`: léptetés.
  4. Egyébként léptetés, ha `S < (most - [this+0x520]) / QPF` másodpercben. Az `S` a `Preferences\SlideshowEffectTime` egész értéke (`0x004019b0`, `0x008020ae-0x008020b4`), negatív értéknél `+2^32` (`0x008020c5`). Az összehasonlítás `fcomp qword` (`0x008020cb`).
  5. Egyébként, ha `[this+0x3c1] != 0`: léptetés (`0x008020d6-0x008020dd`).
  6. Léptetés: `0x00802630` (`0x008020e1`). Nulla visszatérésnél `[this+0x518] = 0` és `[this+0x520] = most` (`0x00802101-0x00802108`). Nem nulla visszatérésnél `-1`.
  7. Nincs léptetés, vagy sikeres léptetés után: `0x00801f50` hívása, `[this+0x3fc] = 0`, és `-2` (`0x0080210e-0x0080211c`).
- **Ütem (következtetés):**
  - A léptetés legkorábbi időpontja `S` másodperc a `[this+0x520]` óta. Ez küszöb, nem periódus (a 38.2.20 7. szakasza megerősítve).
  - A tényleges időpont a pumpa-kör ritmusától függ. Üzenetmentes körben a pumpa az `MsgWaitForMultipleObjects`-nél vár `param_1` ezredmásodpercig, ha a kör 5 ezredmásodpercnél rövidebb volt (`0x009802fd`, `fcomp dword` a `0x00cf4b50` = 0,005). Üzenet azonnal felébreszti. A `param_1` a hívó időtúllépése (1, 5 vagy 10 ms). Hogy melyik hívó, **NINCS MEG**, ezért a pontos ütem sincs meg.
  - Szünet után a bejegyzés `[+0x20]` értéke 1 ms: a `0x00802060` `1`-et ad, a pumpa tárolja. Más írót a feltárt kódban nem találtunk. A teljes `.text` pásztázása nem futott.

**2. A `[this+0x51a]` jelző.**

- **Író: `0x008018a0` (diszasszembly).** A jelzőt csak akkor írja (`0x00801c19`, `mov byte [edi+0x51a], 1`), ha a bemeneti érték (EAX) eltér a `[this+0x50c]` mezőtől: `0x008018ac` `cmp [edi+0x50c], eax`, `0x008018b2` `je 0x801ca3`, ami átugorja a törzset. Az új értéket a `0x008018b8` tárolja.
- **Hívók, három (diszasszembly):**
  - a) `0x007fe33e`, a `0x007fde80` egéreseményében, a `0x201` (bal gomb) ágban, ha `[this+0x3b8] != 0` és a `0x007fd800` nullát ad (`0x007fe336`). EAX a `0x007fd800` kimeneti mezője (`mov eax,[esp+0x18]`, `0x007fe338`).
  - b) `0x00801ce5`, a `0x00801cb0`-ban. EAX = `[this+0x510]` (`0x00801ce1`), amelyet a `0x007fd8c0` írt (az `[this+0x510]` címét `0x00801cd5`-nél adja át). A `0x00801cb0` csak akkor fut, ha `[this+0x429] == 0` és a `0x007fd8c0` nem nullát ad (`0x00801cc6-0x00801cdf`). A `0x00801cb0`-t a `0x00802060` hívja, ha `[this+0x3b8] != 0` és nincs szünet (`0x00802087`).
  - c) `0x00803953`, a `0x008037e0` (`qshow`-építő) törzsében. EAX = `0` (`0x0080394f`), és a hívás csak akkor történik, ha `[ecx+4] & 0xfffffffe` nulla (`0x00803946-0x0080394d`).
- **Gyakoriság.** A jelző akkor lesz `1`, ha a bemeneti érték változik. Az a) eset egéresemény-szinten fut, az Időrend módban. A b) eset minden pumpa-körben fut, az Időrend módban és szünet nélkül, ha a találat változik. A c) eset egyszer, az építésnél, feltétellel. A `0x007fd800` és a `0x007fd8c0` kimenete a kurzor alatti elem indexe: **feltételes**, a jelentését Ghidra-kör igazolja.
- **Olvasó: `0x007fb540` (diszasszembly `0x007fb540-0x007fb58f`).** Ciklus: ha `[this+0x51a] != 0`, meghívja a `0x00802230(this, 1)`-et, majd törli a jelzőt (`0x007fb571`). Utána `Sleep(0x32)` (50 ms, `0x007fb57a`). Legfeljebb 20 újrarajzolás másodpercenként. A ciklust a `QDrawable::vftable` 2. slotja hívja (`0x00cbd674`); az indirekt hívó **NINCS MEG**.
- A `0x00802230` többi hívója a 38.2.19 szerint: `0x007fda00` (`1` jelzővel) és `0x00801130` (`0`-val, folytatáskor).

**Válasz (2):** a jelzőt a `0x008018a0` írja, és csak változáskor. Három hívója van. A `0x007fb540` 50 ezredmásodpercenként olvassa, ezért az újrarajzolás legfeljebb 20 Hz.

**3. Találat, elosztás, vezérlők.**

- **Win32 üzenet → típus.** A `0x00a52890` üzenetkezelő (dekompiláció). `0x200` → `2` és `3` (kimenet 1430, 1460. sor). `0x201` → `1` (1491. sor). `0x203` → `0xd` (1543. sor). `0x207` → `7` és `4` (1584, 1599. sor). `0x208` → `8` (1633. sor). A `0x202` és a `0x204` a `0x1c` ágba ugrik, ahol a `4` és az `5` van (1786, 1812. sor). `0x20a` → `0x00a516c0` (1686. sor). Az egyedi `0x8000008`, `0x8000009` és `0x800000a` üzenetek a 38.2.20 szerint a `0x00a517c0` (`0x11`, `0x12`) és a `0x00a51740` (`0x10`) függvényekhez tartoznak.
- **Konstruktor `0x0052d3c0` (dekompiláció, kimenet 1497-1523. sor):** a vtable `ytUIEvent::vftable`, a típus a `+8`-ban, a pozíciópár a `+0x5c` és `+0x60` mezőben, a negyedik paraméter a `+0x24`-ben. **Destruktor `0x0052d430` (1552-1554. sor):** a vtable visszaállítása, a `0x00401000` hívása (szerepe **NINCS MEG**), és `+0x68 = 0`.
- **Elosztó `0x009e4630` (dekompiláció, kimenet 1037-1467. sor):**
  - Típusvizsgálat (1376-1424. sor): `1` és `0xd` → a `0x4c` slot. Ha az elem `[+0x205]` nem nulla, és a hívás `1000000`-t ad, az elem a `*param_3` kimeneti mezőbe kerül. `2` és `3` → a `0x54` slot (kapu: `[+0x206]`). `4` → a `0x50` slot (`[+0x205]`). `0x13` → a `0x58` slot (`[+0x82]`).
  - Találat: a gyermekeken megy végig (1094-1095. sor, a `[+0x91]` láncon). A határoló téglalapot a `0x20` slot adja (1269. sor), és az esemény pozíciójával hasonlítja össze (1270. sor, `(iStack_c0 < iStack_b8) && (iStack_bc < iStack_b4)`).
  - Visszatérési kódok: `1000000` (kezelve), `0xf4242`, `0xf4243`. A rekurzió az 1295. és 1438. sorban van.
- **Slot-térkép** (index-RTTI, `OneUpUI::vftable`): `0x20` → `0x00a6cd10`; `0x4c` → `0x00a52820` (ez hívja a `0x009e4630`-t, kimenet 998. sor); `0x50` → `0x00401570`; `0x54` → `0x00803180`; `0x58` → `0x008032e0`; `0x74` → `0x00a54050`. A `QDrawable::vftable` 11. slotja (`0x00cbd698` = `0x00cbd66c + 0x2c`) a `0x007fde80` (diszasszembly).
- **A QDrawable egérkezelője (`0x007fde80`, 11. slot):**
  - `0x201` (bal gomb): ha `[this+0x3b8] == 0`, a `0x00801130` (szünet-váltás; diszasszembly `0x007fe1e6-0x007fe1f6`). Ha `[this+0x3b8] != 0`: a `0x007fda80` hívása, és ha az `1000000`, kilépés (`0x007fe202-0x007fe207`). Majd a `[+0x6c8]`-`[+0x72c]` mezőkből számolt tartománnyal való összevetés (kimenet 892-930. sor). Ha a pont a tartományban van, húzás indul (`[+0x429] = 1`, `0x007fdd00`), egyébként `[+0x428] = 1` (`0x007fe2b9-0x007fe31b`). Végül a `0x007fd800` és a `0x008018a0` (2. szakasz).
  - `0x202` (felengedés, kimenet 876-882. sor): ha `[+0x429]`, a `0x007fd770(this+0x514)`; majd `[+0x428] = [+0x429] = 0`.
  - `0x203` és `0x204` (dupla és jobb gomb, dekompiláció 855-875. sor): ha `[+0x3b8] == 0`, a `0x007fda00` (Időrend-váltás). Egyébként a `0x007fda80`, majd a `[+0x2e8]` objektum `vtable+0x18` hívása a `[+0x3ec][+0x3f8]` elemmel. Ezt az ágat a diszasszembly nem ellenőrizte.
  - A `0x201` blokkban van egy `0x203`-as ellenőrzés (`0x007fe346`, `cmp [edx+4], 0x203`, utána `[+0x3b8] = 0` és `[+0x428] = 0`). A blokkba csak `0x201` esemény léphet be (`0x007fe1d9-0x007fe1e0`), ezért ez az ág **nem fut** (kizárva).
  - Görgő (`0x20a`, kimenet 939-971. sor, dekompiláció): ha a `GetAsyncKeyState` szerint a `DAT_00d4a490` gomb lenyomva van, nem fut. Egyébként lépésenként a `0x008011b0` (pozitív) vagy a `0x00801210` (negatív) hívás.
- **Vezérlők.** A `sliderthumb`, `timelinedot`, `startbutton`, `exit` és a listaikon kattintása: **NINCS MEG**. A `0x007fb210` csak betölti az overlay-neveket (38.2.18), az elemekhez tartozó osztály és kattintás-kezelő nincs összekötve.
- **Dátumcsúszka: NINCS MEG.** A kódban csak egy lineáris skálázás van: az egérmozgás koordinátája (`0x007fde80`, kimenet 802-808. sor, dekompiláció): `x_logikai = x_kliens × ([+0x2d0] - [+0x2c8]) / kliens-szélesség`, az `y` hasonlóan `[+0x2d4] - [+0x2cc]` és a magasság szerint. Eltolás nincs. Ez a kurzor-koordináták skálája, nem a dátumcsúszka leképezése. A `[+0x2c8]`-`[+0x2d4]` mezőket a konstruktor (`0x007fa7f0`, kimenet 1582-1917. sor) nem írja.

**Válasz (3):** az elosztás megvan (`0x00a52890` → `0x0052d3c0` → `0x009e4630` → típus szerinti slot). A konstruktor és a destruktor megvan. A vezérlők kattintási célja és a dátumcsúszka leképezése **NINCS MEG**.

**4. A `[this+0x2dc]` objektum és `[X+0x25c] == this`.**

- `0x007fa7f0` (QDrawable konstruktor, kimenet 1899-1907. sor): a `0x0097c5d0(0x268)` foglalás és `memset` (diszasszembly `0x007fae32-0x007fae39`), majd `0x00802c60(X, this, [this+0x2e8])` (`0x007fae4a`: `push ecx`, `push ebp`, `push esi`). A visszatérés a `[this+0x2dc]`-be kerül (1907. sor).
- `0x00802c60` (diszasszembly `0x00802c60-0x00802d86`): az első argumentum `X` (az `ebx`-be kerül). `[ebx+0x25c] = eax` (`0x00802c79`), ahol az `eax` a második argumentum, vagyis `this`: a `0x00a518b0` hívás `ret 4`-gyel (`0x00a51bb2`) takarítja a saját argumentumát, így a `[esp+0x18]` a második argumentumra mutat. `[ebx+0x260] = ecx` (`0x00802c9d`) a harmadik argumentum, a `[this+0x2e8]`. Visszatérés: `X` (`0x00802d82`, `mov eax, ebx`, `ret 0xc`).
- Vtable: `[X] = 0xcbd5c4` (`0x00802c7f`), `[X+0x48] = 0xcbd650` (`0x00802c85`), `[X+0x58] = 0xcbd660` (`0x00802c8c`). Az index RTTI-ja mindhárom címre `OneUpUI::vftable`.
- **Válasz (4):** `[this+0x2dc]` egy **`OneUpUI`** objektum, mérete `0x268` bájt (megerősített: RTTI és foglalási méret). **`[X+0x25c] == this`: igen** (megerősített). `X` és `this` különböző objektum. Ezért a `0x00803110` `esi = [X+0x25c]` sora a QDrawable-re mutat, és a szünetből való visszatérés a `this` jelzőit állítja (38.2.19 §3).

**5. A `0x005e8a70` alapútja (kimenet 350-453. sor).**

- **A forrás.** A `local_c0` (forráslista) és a `local_bc` (darabszám) az Időrend-ágban (`param_2 = 1`) nullázódik (kimenet 209-210. sor). A `local_c0 = param_1` (127. sor) csak a `param_2 == 0` ágban van, és az a 192. vagy 195. sorban visszatér. A dekompiláció szerint tehát az Időrend-ágban a forrás üres. Ez ellentmond a 38.2.17 futásfelvételének (kártyák), ezért a dekompiláció vagy a változó-azonosítás hibás lehet. A forrás eredete **NINCS MEG**.
- **A feltöltés (ha a forrás nem üres).** Körforgatás: a `param_1[0x399]` (bájt-eltolás `0xe64`) értékével egyező első elemtől a forrás végéig (350-385. sor), majd a 0. elemtől a találatig (410-453. sor). Ha nincs találat, az eredeti sorrend. Ha `param_1[0x399] == -1`, a `0x00891110` hívás és üres lista (341. sor).
- **Rendezés: nincs.** A 350-453. sorban nincs rendező hívás. A hívások: `0x0097c810` (növelés) és `0x0097caf0` (felszabadítás).
- **Üres lista:** a 532. sor (`(uStack_d0 & 0xfffffffe) == 0`) az `IDS_MUST_SELECT` ágra visz.
- **A Ctrl- és Shift-ágak** (kimenet 231-330. sor) más úton töltik a listát (`0x0049e1e0`, a `piStack_b0` mutatóval, 313. sor); ez nem az alapút.
- **Válasz (5):** a rendezés nincs. A kiválasztott elem köré forgatás van. Az Időrend-ág forrása **NINCS MEG**, és a dekompiláció szerint üres.

**Nyitott kérdések mérlege.** A nyitva maradt tételek mind a 38.2.20-ból örököltek, ezért a munkasorba (`picasapy-agent`, `memory/nyitott-kerdesek-sor.md`) kerülnek; ezt a hívónak kell frissítenie. Saját, ebben a körben feltett kérdés nincs nyitva.

- Lezárva ebben a körben (7): (a) a visszahívás útja a pumpából (`0x0097fff5`); (b) a léptetési döntés (`0x00802060`); (c) a `[this+0x51a]` írói és hívói; (d) `X` típusa és `[X+0x25c] == this`; (e) a `0x203`-ág kizárása a `0x201` blokkban; (f) a `0x007fb540` ciklus és a 20 Hz felső korlát; (g) a MsgWait küszöb (5 ms) és az üzenetkeret (10 ms).
- Örökölt, nyitva (9): (1) az Időrend-pumpa azonosítása és a hívó időtúllépése; (2) a `0x00802630` léptetés-törzse és a nem nulla visszatérés; (3) a `0x007fd800` és a `0x007fd8c0` kimenetének jelentése; (4) a vezérlők kattintás-leképezése; (5) a dátumcsúszka leképezése; (6) az Időrend-ág alapút-forrása; (7) a `Preferences\SlideshowEffectTime` felhasználói értéke (mérés); (8) a `0x0094aa00` és a `0x0094ace0` hívói; (9) a `0x007fb540` közvetett hívója.

Nyitott kérdések: 9 nyílt (örökölt) · 7 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak nyitva (saját).

**Bizonyítottsági fok (38.2.21).**

| állítás | bizonyíték | fok |
|---|---|---|
| üzenethurok `0x0097fc30` | diszasszembly `0x0098030f-0x0098032a` (38.2.20) | megerősített |
| tizenegy közvetlen hívó, 1/5/10 ms | diszasszembly, az utolsó `push` | megerősített |
| az Időrend-pumpa azonosítása | NINCS MEG | nyitott |
| a 10 ms-os jelöltek webböngésző-jellegűek | dekompiláció 404, 501. sor | feltételes |
| visszahívás a pumpából, `call [vtable+4]` | diszasszembly `0x0097ffe3-0x0097fff5` | megerősített |
| a visszahívás a `0x00803ab0` | index-RTTI és `0xcbd6c8+4` | megerősített |
| a `0x00803ab0` visszatérései | diszasszembly `0x00803abc-0x00803aec` | megerősített |
| a `0x00802060` döntési sora | diszasszembly `0x00802066-0x00802125` | megerősített |
| léptetési küszöb: `S` másodperc | diszasszembly `0x008020b9-0x008020d4` | megerősített (küszöb) |
| az `S` felhasználói értéke | NINCS MEG | nyitott |
| szünet után az intervallum 1 ms | diszasszembly (`1` visszatérés), dekompiláció 207-209. sor | megerősített (író); más író NINCS MEG |
| a pumpa várakozása 5 ezredmásodpercnél rövidebb körben | diszasszembly `0x009802f9-0x00980308` | megerősített |
| a `[+0x51a]` írója és feltétele | diszasszembly `0x008018ac-0x008018b2`, `0x00801c19` | megerősített |
| a `[+0x51a]` három hívója | diszasszembly | megerősített |
| a hívók gyakorisága | a feltételek összevetése | feltételes |
| az olvasó 50 ms, legfeljebb 20 Hz | diszasszembly `0x007fb540-0x007fb58f` | megerősített |
| a `0x007fd800` kimenete EAX-ban | diszasszembly `0x007fe32f-0x007fe33e` | megerősített |
| `0x007fde80` a QDrawable 11. slotja | index-RTTI és `0xcbd698` olvasása | megerősített |
| a `0x203` ág a `0x201` blokkban nem fut | diszasszembly `0x007fe1d9-0x007fe346` | megerősített (kizárás) |
| ytUIEvent-konstruktor, destruktor, típustábla | dekompiláció 1376-1424, 1497-1554. sor | feltételes |
| slot-térkép (`0x4c`-`0x58`) | index-RTTI, `OneUpUI::vftable` | megerősített (a slot-szám); feltételes (az objektum) |
| vezérlők kattintása | NINCS MEG | nyitott |
| dátumcsúszka leképezése | NINCS MEG | nyitott |
| `[+0x2dc]` = `OneUpUI` | index-RTTI `0xcbd5c4`, foglalás 0x268 | megerősített |
| `[X+0x25c] == this` | diszasszembly `0x00802c79`, `0x00a51bb2`, `0x007fae4a` | megerősített |
| az alapút forrása az Időrend-ágban | dekompiláció 209-210. sor | feltételes (ellentmondás a 38.2.17-tel) |
| az alapút nem rendez | dekompiláció 350-453. sor, hívások | feltételes |

**Amit KIZÁRTAM (38.2.21).**
- A `0x0097fc30` időtúllépése nem az eltelt idő; a hívó adja.
- A `0x00982270` nem hívja a visszahívást.
- A `0x0094aa00` és a `0x0094ace0` a tartalmuk szerint nem Időrend-specifikus pumpa (a hívási kapcsolatot nem zártuk ki).
- `X` nem a QDrawable: külön, `0x268` bájtos OneUpUI objektum.
- A `0x007fe33e` hívásakor EAX nem a dekompiláció szerinti `0`, hanem a `0x007fd800` kimeneti mezője.
- A `0x203` ág a `0x201` blokkban nem fut.
- A `0x00802060` nem ad `0`-t.

**Fejlesztési következmény.** Terméki kódot nem írtunk. A léptetési ütem nem implementálható: hiányzik az Időrend-pumpa és a registry-érték. A `OneUpUI` és a `[this+0x2dc]` kapcsolat most már bináris. A kattintási cél és a dátumcsúszka leképezése nyitott, ezért a menüpont és a `Ctrl+5` bekötését a mostani ismeretek alapján nem lehet megírni.

**Következő Ghidra-körök.**

- ~~`Ghidra-kör kell: 0x00983430, 0x00983fc0, 0x00982bf0 - a qshow-ablak futtató hurka, és hogy a 0x0097fc30 11 hívója közül melyik fut az Időrend alatt, milyen időtúllépéssel [blokkoló]`~~ **RÉSZBEN JAVÍTVA (38.2.22, 1. szakasz):** a három függvény nem hurok (méret-értesítés, teljes képernyős váltás, `ytWindow` konstruktor). A futtató hívó és az időtúllépés **NINCS MEG**, lásd `Ghidra-kör kell: 0x005e6710` a 38.2.22 szakaszban.
- ~~`Ghidra-kör kell: 0x00802630 - a léptetés törzse, és a nem nulla visszatérés (-1, a bejegyzés eltávolítása) [blokkoló]`~~ **JAVÍTVA (38.2.22, 2. szakasz):** a léptetés törzse igazolt; a callee nem nulla visszatérése `3`, a hívó `0x00802060` ezt `-1`-re képezi.
- ~~`Ghidra-kör kell: 0x00982270 - a bejegyzés-lista felépítése és sorrendje [nem blokkoló]`~~ **JAVÍTVA (38.2.22, 1. szakasz):** a `0x00982270` a globális tömb rendezetlen másolata; a sorrend a hozzáfűzési sorrend.
- ~~`Ghidra-kör kell: 0x007fd800, 0x007fd8c0 - a találati index kimenete és a visszatérési érték jelentése [blokkoló]`~~ **RÉSZBEN JAVÍTVA (38.2.22, 3. szakasz):** a `0x007fd800` a kurzor alatti elem rekordjának `+0` mezőjét adja, vagy `-1`-et; a `0x007fd8c0` a 0,666 konstanshoz legközelebbi kártyát keresi. A `+0` mező és a `0x007fd770` visszatérésének jelentése **NINCS MEG**.
- ~~`Ghidra-kör kell: 0x007fda80 - a 0x201 Időrend-ág hívott függvénye és az 1000000 visszatérés [blokkoló]`~~ **JAVÍTVA (38.2.22, 4. szakasz):** a `0x007fda80` négy overlay-téglalap találati függvénye; az `1000000` a kezelt kattintás jele.
- ~~`Ghidra-kör kell: 0x007fb210 - az overlay-elemek rajz- és találati téglalapjai, és a sliderthumb, timelinedot, startbutton, exit, listaikon kattintás-kezelői [blokkoló]`~~ **RÉSZBEN JAVÍTVA (38.2.22, 5. szakasz):** az overlay-nevek és az objektumok összerendelése megvan; a négy találati téglalap a `startbutton`, `exit`, `right`, `left` overlay-eké. A rajz, a `sliderthumb` húzásának hatása és a többi overlay kattintása **NINCS MEG**.
- `Ghidra-kör kell: 0x00a6cd10, 0x00a52820, 0x00401570, 0x00803180, 0x008032e0 - az OneUpUI kattintás-kezelői és a határoló téglalap, és hogy a 0x009e4630 melyik objektumon fut [blokkoló]`
- `Ghidra-kör kell: 0x005e8a70 - a local_c0 és a local_bc írói az Időrend-ágban (kimenet 209-210. sor), és a forrás-lista eredete; diszasszembly-ellenőrzés [blokkoló]`
- `Ghidra-kör kell: 0x0094aa00 és 0x0094ace0 hívói (0x00593450, 0x006fc7d0, 0x006fcb60, és a 0x0094ace0 tíz hívója) - Időrend-e [nem blokkoló]`
- ~~`Ghidra-kör kell: 0x006f9cc0 - az 1 ms-os 0x0097fc30 hívó (0x006fb417) kontextusa, qshow-e [nem blokkoló]`~~ **RÉSZBEN (38.2.22, 1. szakasz):** statikus hívási úton a `0x008037e0`-tól 9 szinten nem érhető el; a kontextus **NINCS MEG**.
- `Ghidra-kör kell: 0x00a52890 - a típuskódok diszasszemblált ellenőrzése (1, 2, 3, 4, 5, 0xd, 7, 8) [nem blokkoló]`
- Mérés kell (nem Ghidra): a `Preferences\SlideshowEffectTime` felhasználói értéke a tulajdonos gépén (futó Picasa vagy a registry-kulcs) [blokkoló a léptetési ütem pontos értékéhez]

#### 38.2.22 Az Időrend bináris feltárása, 5. kör: hurok, léptetés, találat, négy téglalap, csúszka-sáv (#5401, 2026-10-20)

**Kérdés és hatókör.** A 38.2.21 „Következő Ghidra-címek” nyolc címét dolgoztuk fel: `0x00983430`, `0x00983fc0`, `0x00982bf0`, `0x00802630`, `0x007fd800`, `0x007fd8c0`, `0x007fda80`, `0x00982270`. Öt kérdés volt: (1) melyik futtató hurok és időtúllépés fut az Időrend alatt, és milyen a bejegyzés-lista sorrendje; (2) mit csinál egy léptetés, és mit jelent a nem nulla visszatérés; (3) mi a találati kimenet; (4) mi a `0x007fda80`, és mit jelent az `1000000`; (5) hogyan kattintanak a vezérlők, és hogyan képződik le a dátumcsúszka.

**Bemenet és módszer.** Az `idorend-5` nyolc Ghidra-blokkja, és az `idorend-1` a `0x007fb210` miatt. A bináris index (`functions`, `xrefs`) csak függvényszintű `call` éleket tartalmaz: 78 901 sor, vtable- és függvénymutató-hivatkozás nincs benne. A sorok `from_address` mezője a hívó függvény kezdőcíme (például `0x004051b0`), nem a hívóhely; a hívóhelyet a diszasszemblálás adja (például `0x0040e4b1`). A diszasszemblálás a `pe_dis` modulból jött (capstone). Futásfelvétel és QEMU-futtatás nem volt. Terméki kódot nem írtunk.

**1. Futtató hurok, időtúllépés, bejegyzés-sorrend.**

Három cím nem hurok. Mindhárom a qshow-építőből (`0x008037e0`) hívódik:

- `0x00982bf0` (hívóhely `0x008038ec`): a `ytWindow` konstruktora (a vtable `ytWindow::vftable`). Tárolja a cím szövegét (`0x00985ff0`), és meghívja a `0x00983670` függvényt (ablak létrehozása, belseje **NINCS MEG**).
- `0x00983430` (hívóhely `0x00803983`): `GetClientRect` a `[this+0x6c]` ablakra, majd `0x00983a60(szél, magasság)`. Ha a kliensterület nem üres és `[this+0x64]` nem nulla, a `[this+0x64]` objektum vtable `+0x20` slotját hívja `(-1, -1, -1, -1)` argumentumokkal. Méret-értesítés.
- `0x00983fc0` (hívóhelyek `0x0080398f` és `0x005e68c5`, utóbbi a `0x005e6710`-ben): teljes képernyős váltás. Nem nulla paraméternél: a menü eltávolítása (`SetMenu` NULL), a `[this+0x70]` ablak megszüntetése (`DestroyWindow`), a stílus beállítása `0x96000000` vagy `0x96080000` értékre a `(*DAT_00d69524)` függvénypointeren a `-16` (`GWL_STYLE`) indexszel, és a képernyő méretére állítás (`GetSystemMetrics` 0 és 1; ha `0x00983b50` nem nulla, a `DAT_00d678b0` pointeren át). Nulla paraméternél visszaállítás: `SetMenu`, `0x00982ee0`, vtable `+0x10`, és ha a 2-es bit be van állítva, `SetWindowPos`. A `DAT_00d69524` célját nem ellenőriztem.

Tehát a qshow-építő létrehozza az ablakot (`0x00982bf0`), értesíti a méretéről (`0x00983430`), és teljes képernyőre kapcsolja (`0x00983fc0`).

A futtató hurok a `0x0097fc30` (38.2.20 §1: `PeekMessageA`, `MsgWaitForMultipleObjects`). Közvetlen hívói (függvényszint) tizenegyen vannak:

- 1 ms: `0x0040e410`, `0x005ffc30`, `0x006f9cc0` (hívóhely `0x006fb417`), `0x006fe630`, `0x009d4d10`;
- 5 ms: `0x004051b0`, `0x0059e920`, `0x007420f0`, `0x007422d0`;
- 10 ms: `0x0094aa00`, `0x0094ace0` (webböngésző-pumpa, 38.2.21 §1).

**Melyik hívó fut az Időrend alatt: NINCS MEG.** A bináris index nem köti össze a hívókat a qshow-val:

- `0x008037e0` egyetlen közvetlen hívója `0x005e8a70` (`CThumbUI::MakeTimeline`). Ennek hívói: `0x005cb990`, `0x005d9cc0`, `0x005e0f70`, `0x005e60d0`. A `0x005d9cc0` és a `0x005e0f70` hívója `0x005de8e0`; a `0x005e60d0` hívója `0x005e6710`.
- A `0x005cb990`, `0x005de8e0` és `0x005e6710` láncának tetején nincs közvetlen hívó az indexben. Valószínűleg függvénymutatón vagy vtable-on keresztül indul; ezt nem igazoltam.
- Egyik pumpa-hívóból sincs közvetlen hívási út `0x005e8a70`-hez vagy `0x008037e0`-hoz 9 szinten. Fordítva: a `0x008037e0`-ból 9 szinten elért 971 függvény között nincs pumpa-hívó.
- A `0x005e6710` hívja a `0x005e60d0`-t és a `0x00983fc0`-t is. Ez jelölt az Időrend-parancs kezelőjének, nem igazolt.

Ezért az időtúllépés is **NINCS MEG**: a 38.2.21 szerinti 1, 5 és 10 ms közül nem tudjuk, melyik érvényes.

**Bejegyzés-lista sorrendje (megerősített).** A `0x00982270` (hívója a pumpa, `0x0097feac`) a globális `DAT_00d69418` tömböt (darabszám: `DAT_00d6941c >> 1`) másolja a helyi pillanatképbe `_memcpy`-vel. Rendezés nincs. A másoláson kívül csak a kapacitás-növelés (`0x0097c810`), a felszabadítás (`0x0097caf0`) és egy zárolás (`0x0074cf40` vagy `0x009829f0`, belseje **NINCS MEG**) van. A pumpa ebben a sorrendben hívja a bejegyzéseket. A globális tömb sorrendje a hozzáfűzés sorrendje (38.2.19 §4: `0x0097d150`, arg2 = 0). Egy elem törlése után a tömörítés módja **NINCS MEG**.

**Léptetési ütem: NINCS MEG.** A legkorábbi léptetés S másodperc az utolsó léptetés után (38.2.21 §1, `Preferences\SlideshowEffectTime`). A tényleges időpont a pumpa-hívó időtúllépésétől függ, ezért **NINCS MEG**.

**2. A léptetés törzse (`0x00802630`).** Megerősített (dekompiláció és diszasszemblálás: `0x00802696`, `0x00802765`, `0x008026e9`).

- Zárolás: `[this+0x0c]` nulla esetén a vtable `+0x18` hívása, egyébként `EnterCriticalSection([this+0x28])`. A tulajdonos szál a `[this+0x20]`, a rekurzió a `[this+0x24]` mezőben van.
- Darabszám `[this+0x3f0] >> 1`. Ha nulla (`0x0080263a`): `0x009a8a30`, `0x009a8ca0([this+0x160])`, `0x009a8bc0`, és visszatér `0`-val.
- Ha az index `[this+0x3f4]` nem kisebb a darabszámnál (lista vége):
  - `[this+0x3fd] != 0` (`0x00802696`): az index `-1`, majd +1 után `0`. Csendes körbefordulás, nincs hívás.
  - `[this+0x3fd] == 0`: ha `[this+0x3b9] == 0`, meghívja a `0x007fb820` függvényt (38.2.18 szerint ez az `Escape` kilépési ága), feloldja a zárolást, és visszatér `3`-mal. Ha `[this+0x3b9] != 0` (`0x00802765`): az index `0`, a `0x007fda00` átmenet-indítás, feloldás, visszatérés `0`-val.
- Egyébként az index +1 (`0x008026ac`), feloldás, majd `0x00802230(this, 0)` (`0x008026e9`). Ha ez `0`-t ad, a léptetés `0`-val tér vissza. Ha `4` vagy `-1`, a ciklus újra fut.

Jelentés: egy lépés a következő index kiválasztása, majd az új képkocka a `0x00802230` nulla paraméteres változatával (38.2.19 §1: új véletlen eltolás). A lépés nem hív átmenet-indítót. Az átmenet-indító (`0x007fda00`) csak a lista végi újraindításkor fut.

**Nem nulla visszatérés.** A dekompiláció szerint csak `3` jöhet létre. A hívó `0x00802060` (`0x008020e1`, diszasszemblálás): `test eax,eax`; nulla esetén a normál út (`0x008020f2`), nem nulla esetén `or eax,-1`, azaz `-1`. A pumpában a `-1` a bejegyzés eltávolítása (38.2.21 §1). A `mov eax,3` sort nem ellenőriztem diszasszemblálással.

**Következmény (megerősített).** A `0x007fda00` állítja `[this+0x3b9] = 1`-re (38.2.19 §2). Ezért Időrend módban a lista vége nem lépteti ki a futtatót: a `[this+0x3fd]` értékétől függően csendesen körbefordul, vagy újraindítja az Időrendet. A `[this+0x3fd]` írója **NINCS MEG**.

**3. Találati kimenet (`0x007fd800`, `0x007fd8c0`).**

- `0x007fd800` (hívó `0x007fde80`, `0x007fe32f`): a kurzor alatti elem keresése. Bemenet: a `[this+0x2f8]` alobjektum (`lea ecx,[edi+0x2f8]`), a pont két float értéke (`ebx`), és a kimeneti mutató (`[esp+0x18]`). Az indexlistán (`[+0x80]`, darabszám `[+0x84] >> 1`) megy végig. Az elem rekordja `[+0xb0] + i*0xf8`; a téglalap bal széle `+0xdc`, felső széle `+0xe0`, jobb széle `+0xe4`, alsó széle `+0xe8` (egész számok). Találat: bal <= x < jobb és felső <= y < alsó. Az első találatnál a kimenetre a rekord `+0` mezőjét írja, és visszatér a `0x007fd770(i)` értékével. Nincs találat: `0xffffffff`.
- A hívó csak nulla visszatérésnél folytat (`0x007fe334-0x007fe336`), és ekkor az `[esp+0x18]` értéket adja a `0x008018a0`-nak (`0x007fe338-0x007fe33e`).
- Jelentés: a kimenet a rekord `+0` mezője, nem a listaindex. Hogy ez azonosító vagy index, **NINCS MEG**. A `0x007fd770` visszatérése **LEZÁRVA (38.2.23 §6): 0**.
- `0x007fd8c0` (hívó `0x00801cb0`, `0x00801cd8`): nem egérkeresés. A `[this+0xb4] >> 1` darabszámon megy végig. Minden `i`-re x_i = `i` * `[this+0x30]` + `[this+0x20]` (mindkettő f64), meghívja a `0x007fbab0` függvényt (`ecx = this`, x_i argumentum), majd a `0x0049f5c0`-val (`fabs`, cdecl, `ret`) a |x_i - 0,666| értéket számolja. A 0,666 a `0xcf4860` f64 konstans, pontosan 0,6660000085830688. A legkisebb távolságú `i` marad: `[this+0]` = `i`, `*param_1` = a rekord `+0` mezője.
- Eltérés: a diszasszemblálásban a legkisebb-kereső összehasonlítása más verem-helyről olvas, mint ahová a kezdeti küszöb íródik (`0xcf4900` = 1000000,0). **LEZÁRVA (38.2.23 §6):** a min-tároló a verem E0+0xc helyén van, a dekompiláció helyes (legkisebb távolság, kezdeti küszöb 1000000).
- Visszatérés: **JAVÍTVA (38.2.23 §4):** a `0x009a5210` nem időablak-ellenőrzés, hanem eltelt idő (QPC). Az időablak-vizsgálat a `0x007fd8c0` belsejében van, a `[this+0x48]` rekordjain; a visszatérés jelentése **NINCS MEG**.
- A 0,666 szerepe (lejátszási pont vagy más) **NINCS MEG**. A kártya-sor rajzolása nincs igazolva.
- Lánc Időrend módban: a `0x00802060` hívja a `0x00801cb0`-t, ha `[this+0x3b8] != 0`; a `0x00801cb0` csak akkor fut tovább, ha `[this+0x429] == 0` és a `0x007fd8c0` nem nullát ad. Az eredmény `[this+0x510]`-be kerül, és a `0x008018a0` állítja a `[this+0x51a]` jelzőt (38.2.21 §2).

**4. A `0x007fda80` és az `1000000`.**

- Hívók a `0x007fde80`-ban: `0x007fe1fd` (a 0x201-ágban, ha `[this+0x3b8] != 0`; diszasszemblálva) és `0x007fe15f` (nem ellenőriztem).
- Bemenet: `x = [this+0x420]`, `y = [this+0x424]` (float). A függvény a `this`-t az ESI-ből olvassa (`unaff_ESI` a dekompilációban; `mov esi,edi` a `0x007fe1fb` címen).
- Négy téglalap. Az `X` az overlay-objektum alap-offsetje (5. szakasz):

| sorrend | X | overlay | bal, felső, szél, magasság | művelet | visszatérés |
|---|---|---|---|---|---|
| A | `0x738` | `startbutton` | `+0x750`, `+0x754`, `+0x740`, `+0x744` | `0x007fb820`, majd `[this+0x2e8]` vtable `+0x18` hívása `(-1, azonosító)` | `1000000` |
| B | `0x580` | `exit` | `+0x598`, `+0x59c`, `+0x588`, `+0x58c` | `0x007fb820` | `1000000` |
| C | `0x558` | `right` | `+0x570`, `+0x574`, `+0x560`, `+0x564` | `0x007fd150` | `1000000` |
| D | `0x530` | `left` | `+0x548`, `+0x54c`, `+0x538`, `+0x53c` | `0x007fd120` | `1000000` |
| - | - | - | - | nincs találat | `0xf4241` (1000001) |

- Azonosító: `[ [this+0x3ec] + [this+0x3f8]*4 ]`, ha `[this+0x3f8] >= 0`, egyébként `0`. Ez az utoljára megjelenített elem (`[this+0x3f8]` az utolsó megjelenített index, 38.2.19 és 38.2.21).
- Az `[this+0x2e8]` objektum osztálya **NINCS MEG**. A `0x007fa7f0` építő a harmadik paraméterként adja (38.2.20 §6).
- Az `1000000` jelentése: a kattintás egy négy overlay egyikébe esett, és a kezelő kész. A `0x007fde80`-ban `cmp eax,0xf4240` és `je 0x007fe441` (`0x007fe202-0x007fe207`); a `0x007fe441` ága `mov eax,0xf4240` és a függvény kilépése. Húzás nem indul. A `0xf4241` esetén a `0x007fde80` a húzás-ággal folytatja (`0x007fe20d`).

**5. Vezérlők és dátumcsúszka.**

- Overlay → X leképezés (megerősített, a `0x007fb210` diszasszemblálásából): a `0x00410fa0(X)` hívás előtt `lea edi,[esi+X]`, `push edi`, `mov edx, <sztring>` áll. A sztringek a `0x00cbd334`-től indulnak: `left` = `0x530`; `right` = `0x558`; `mouse` = `0x5a8`; `rollovermouse` = `0x5d0`; `exit` = `0x580`; `timeline` = `0x6c0`; `timelinedot` = `0x6e8`; `sliderthumb` = `0x710`; `startbutton` = `0x738`. A tizedik, `overlay`, helyi objektumon töltődik.
- Mezők (dekompiláció): `X+0x08` szél, `X+0x0c` magasság, `X+0x18` bal, `X+0x1c` felső. A bal mezőt a dekompiláció `_DAT_00d34040`-nel szorozza és kerekíti (`ROUND`), a felső mezőt nem. Hogy a felső mezőnek van-e más skálázása, **NINCS MEG**.
- Húzás-sáv (`0x007fde80` 0x201-ága, a 4. kimenet dekompiláció 892-915. sora): a sáv a `timeline` (X `0x6c0`): bal `[+0x6d8]`, szél `[+0x6c8]`. A csúszka-gomb a `sliderthumb` (X `0x710`): bal `[+0x728]`, felső `[+0x72c]`, szél `[+0x718]`, magasság `[+0x71c]`. A dekompiláció a csúszka helyét a sáv bal és jobb széle közé korlátozza; a pontos képlet **LEZÁRVA (38.2.23 §3)**: `[this+0x728]` = trunc(x_c - (floor(SW/2) + 3)); korábban csak dekompiláció volt, most diszasszembly is megerősíti.
- A `sliderthumb` kattintása nem tartozik a `0x007fda80` találati vizsgálatába; a húzás-ágon megy. A húzás indítását a 38.2.21 §3 írja (`0x007fdd00`), ezt nem ellenőriztem.
- **A dátumcsúszka leképezése (csúszka-hely -> dátum vagy képindex): RÉSZBEN (38.2.23 §3).** A csúszka-hely rekordsorszámot ad (i*); a dátum vagy képindex jelentése **NINCS MEG**.
- `timelinedot`, `mouse`, `rollovermouse` és `overlay`: a `0x007fda80` nem vizsgálja őket. Kattintási céljuk **NINCS MEG**.
- Listaikon: nem azonosítottam, melyik overlay. **NINCS MEG**.

**6. Javítások a korábbi szakaszokban.**

- 38.2.21 „Következő Ghidra-címek” első tétele: a `0x00983430`, `0x00983fc0`, `0x00982bf0` nem a futtató hurok (1. szakasz). A futtató a `0x0097fc30`.
- 38.2.21 §1: a `0x00802630` nem nulla visszatérése `3`; a `-1` a hívó (`0x00802060`) leképezése (2. szakasz).
- 38.2.21 §1: a `0x00982270` sorrendje igazolt: rendezetlen másolat (1. szakasz).
- 38.2.21 §3: a `0x007fe33e` hívó EAX-értéke a `0x007fd800` kimeneti mezője: megerősítve (`mov eax,[esp+0x18]`, `0x007fe338`).
- 38.2.21 §3: a `0x007fda80` a 0x201 Időrend-ág négy téglalapos találati függvénye (4. szakasz).

**Bizonyítottsági fok (38.2.22).**

| állítás | bizonyíték | fok |
|---|---|---|
| `0x00982bf0`, `0x00983430`, `0x00983fc0` nem hurok | dekompiláció; hívóhelyek `0x008038ec`, `0x00803983`, `0x0080398f`, `0x005e68c5` | megerősített |
| futtató hurok: `0x0097fc30` | 38.2.20 §1, diszasszemblálás | megerősített |
| az Időrend alatti pumpa-hívó | index: nincs közvetlen hívási út 9 szinten | NINCS MEG |
| az időtúllépés | a hívótól függ | NINCS MEG |
| bejegyzés-lista sorrendje | `0x00982270` `_memcpy`, rendezés nélkül; `0x0097d150` hozzáfűzés | megerősített |
| léptetés törzse | dekompiláció `0x00802630`; diszasszemblálás `0x00802696`, `0x00802765`, `0x008026e9` | megerősített |
| nem nulla visszatérés: `3`, a hívó `-1` | dekompiláció; `0x008020e1` diszasszemblálás | megerősített (`mov eax,3` nem ellenőrzött) |
| lista vége Időrend módban nem lépteti ki | `0x00802765` `cmp`; dekompiláció; `0x007fda00` állítja `[this+0x3b9]`-et | megerősített |
| `[this+0x3fd]` írója | NINCS MEG | nyitott |
| `0x007fd800` téglalap-találat, kimenet a `+0` mező | dekompiláció; `0x007fe32f-0x007fe338` diszasszemblálás; `0x007fd8c0` vége `mov [edx], ecx` | megerősített (a mező jelentése NINCS MEG) |
| `0x007fd8c0` legkisebb távolság | dekompiláció; diszasszembly (38.2.23 §4: a min-tároló E0+0xc) | megerősített |
| `0x0049f5c0` = `fabs` | diszasszemblálás (`fabs`, `ret`) | megerősített |
| `0x007fda80`: négy téglalap és az `1000000` | dekompiláció; `0x007fe202-0x007fe207`, `0x007fe441` | megerősített |
| overlay-nevek és az `X` objektumok | `0x007fb210` diszasszemblálás (`0x007fb228-0x007fb4af`) | megerősített |
| húzás-sáv (`timeline`, `sliderthumb`) | diszasszembly `0x007fdd00` (38.2.23 §3) | megerősített |
| dátumcsúszka-leképezés | NINCS MEG | nyitott |

**Nyitott - következő Ghidra-körök.**

- `Ghidra-kör kell: 0x005e6710 - a függvénymutató-hivatkozásai (vtable, parancstábla), és a 0x0097fc30 hívóig vezető lánc; az Időrend-pumpa és az időtúllépése [blokkoló]`
- `Ghidra-kör kell: 0x007fd120, 0x007fd150 - a left és right overlay műveleteinek törzse [blokkoló]`
- `Ghidra-kör kell: 0x007fdd00 - a sliderthumb húzásának hatása: csúszka-hely -> dátum vagy képindex [blokkoló]`
- `Ghidra-kör kell: 0x007fbab0 - a kártya x-pozíciójának képlete (this+0x50, this+0x54, this+0x58) [blokkoló a rajzoláshoz]`
- `Ghidra-kör kell: 0x007fa7f0, 0x00802c60 - a [this+0x2e8] objektum osztálya és a startbutton visszahívás célja [blokkoló]`
- `Ghidra-kör kell: 0x007fd770 - a 0x007fd800 találati ágának visszatérése [nem blokkoló]`
- `Ghidra-kör kell: 0x0074cf40, 0x009829f0, 0x0097d370 - a 0x00982270 zárolása és a törlés tömörítési módja [nem blokkoló]`
- `Ghidra-kör kell: 0x007fe15f - a 0x007fde80 második 0x007fda80 hívóhelyének ága [nem blokkoló]`
- `Ghidra-kör kell: 0x007fb820 - a kilépési ág törzse (Escape) [nem blokkoló]`
- `Ghidra-kör kell: [this+0x3fd] írói (teljes .text pásztázás, paszta.py) [nem blokkoló]`

**Nyitott kérdések mérlege (38.2.22).** `Nyitott kérdések: 11 nyílt · 9 lezárva · 5 blokkolt (a blokkolók a Ghidra-listában)`

- **LEZÁRVA:** (a) a három függvény nem hurok; (b) a `0x00802630` léptetés-törzse; (c) a nem nulla visszatérés `3`, a hívónál `-1`; (d) a bejegyzés-lista sorrendje; (e) a `0x007fd800` téglalap-találata; (f) a `0x0049f5c0` = `fabs`; (g) a `0x007fda80` négy téglalapja és az `1000000`; (h) az overlay → `X` leképezés; (i) Időrend módban a lista vége nem lép ki.
- **NYITVA:** a pumpa-hívó és az időtúllépés; a léptetési ütem; a `[this+0x3fd]` írója; a `0x007fd8c0` visszatérésének jelentése; a `+0` mező jelentése és a `0x007fd770`; a `0x007fd8c0` összehasonlító slotja (feltételes); a `timelinedot`, `mouse`, `rollovermouse`, `overlay` és listaikon kattintása; a dátumcsúszka-leképezés; az `[this+0x2e8]` osztálya; a felső mező skálázása.

**A #5401 „Kész, ha” pontjai (5. kör).** (1) Képlánc: változatlan. (2) Átmenet és ütem: részben. A lista-végi viselkedés és a nem nulla visszatérés igazolt; a pumpa-hívó és az ütem **NINCS MEG**. (3) Vezérlők: a négy találati overlay (`startbutton`, `exit`, `right`, `left`) műveletei igazoltak; a csúszka és a többi overlay műveletei **NINCS MEG**. (4) Diavetítés és visszatérés: változatlan.

**Fejlesztési következmény.** Terméki kódot nem írtunk. A léptetési ütem továbbra sem implementálható: hiányzik a pumpa-hívó, az időtúllépés és a `Preferences\SlideshowEffectTime` felhasználói érték. Az Időrend lista-vége viselkedése igazolt (nincs kilépés), a négy gomb műveleti leképezése igazolt, a dátumcsúszka leképezése nem.

#### 38.2.23 Az Időrend bináris feltárása, 6. kör: pumpa-lánc, `left` és `right`, csúszka, kártya-görbe, `startbutton`, kilépés (#5401, 2026-10-20)

**Kérdés és hatókör.** Hat kérdés a `2026-10-20-idorend-6.txt` nyolc címéről: (1) `0x005e6710`; (2) `0x007fd120` és `0x007fd150`; (3) `0x007fdd00`; (4) `0x007fbab0`; (5) `0x00802c60` és a `[this+0x2e8]` objektum; (6) `0x007fb820` és `0x007fd770`. A 38.2.22 kísérő címei közül a `0x007fd8c0` és a `0x009e6010` is kellett. Terméki kódot nem írtunk.

**Bemenet és módszer.** Diszasszembly a `pe_dis.cdis` (capstone) segítségével. Az ideiglenes mentések a `.bt/` alá kerültek, a kör végén törölve. Index: `functions`, `xrefs` (függvényszintű hívások), `data_symbols`, `string_xrefs`. A vtáblák bejegyzéseit közvetlenül a `Picasa3.exe` bájtjaiból olvastam. Minden konstansnál ellenőriztem a betöltés méretét (`fld qword` = f64, `fld dword` = f32). Futásfelvétel és QEMU-futtatás nem volt.

**1. `0x005e6710`: az Időrend-pumpa és az időtúllépés**

- **Azonosítás (megerősített).** A `0x005e6710` a `CThumbUI::vftable` 12. bejegyzése: `0x00c9052c` + 0x30 = `0x00c9055c`, ez a `DATA` hivatkozás. A bájtokból olvasva a slot értéke `0x005e6710`.
- **Mit csinál (megerősített).** A főablak billentyű- és parancs-előszűrője. Visszatérése `1000000` (0xf4240: a hívó elnyeli) vagy `0xf4241` (továbbadja). Ágak: `WM_KEYDOWN` (`0x100`) `F2` (`0x71`): `0x0057d430`, `0x00407610`, majd `1000000`. `F3` (`0x72`): `0x009cd8a0`, `0xf4241`. `F4` (`0x73`): `0x009cd110` és a vtábla +0x78 hívása, `0xf4241` ha a feltétel teljesül. `F5` (`0x74`): `0x004a46e0`, `0x00579480(0,1)`, `[this+0xb0]+0x166` = 1, `0x0065b840`, a végén `0xf4241`. `F11` (`0x7a`): `0x00983fc0` (teljes képernyő). `F1` (`0x70`): `0x005d0cd0` vagy `0x009cd8a0`. `WM_SYSKEYDOWN` (`0x104`) `Enter` (`0x0d`), ha `[this+0xd29] == 0`: `0x005c9740`, `1000000`. `F12` (`0x7b`), és ha a `(param_2+0x10)` 4-es bitje be van állítva: `0x005e60d0` (billentyű-kapcsoló), a visszatérése a hívó értéke. Ezek az ágak csak akkor futnak, ha `0x0056c420`, `0x0056c110`, `0x00562d00`, `0x005f2650` és `0x0057c430(4)` mind 0-t ad.
- **Esc, Space és a nyilak nincsenek ebben a függvényben (megerősített).** Ezeket a `0x00801270` kezeli (5. pont).
- **Hívó és pumpa (megerősített, negatív).** A `0x005e6710` nem hívja a `0x0097fc30`-at, és a függvényszintű indexben nincs közvetlen hívója: a vtábla-bejegyzés az egyetlen belépési pont. Előre 12 szintig bejárva a 11 közvetlen pumpa-hívóból egyik sem ér el `0x005e6710`, `0x005e60d0`, `0x005e8a70`, `0x008037e0`, `0x007fda00`, `0x007fb820`, `0x00802630`, `0x00801270`, `0x007fa7f0`, `0x007fda80` vagy `0x007fde80` címet. A bejárt csúcsok száma 100 és 4910 között volt. Ez csak a közvetlen hívási élekre igaz: a vtábla-hívásokat az index nem látja, ezért nem zárja ki az utat.
- **Pumpa-lánc a `0x0097fc30`-ig: NINCS MEG.** Ghidra-kör kell: `0x005e6710` hívóhelye, vagyis a `CThumbUI` vtábla +0x30 hívása (`call [reg+0x30]`) a `0x0097fc30` hívóinak láncában. [blokkolt]
- **Időtúllépés: NINCS MEG.** A pumpa-hívók 1, 5 vagy 10 ms-os túllépést adnak (38.2.22 §1), de az Időrend alatt futó hívó nincs azonosítva. Ugyanez a Ghidra-kör. [blokkolt]
- **Léptetési ütem: NINCS MEG.** Az ütemet a pumpa hívója és a `Preferences\SlideshowEffectTime` együtt adja (38.2.21 §1, 38.2.22 §2). Pumpa nélkül nem mérhető. [blokkolt]

**2. `0x007fd120` (`left`) és `0x007fd150` (`right`)**

- **Művelet (megerősített).** `left` = `0x007fd0c0(+S, 2,0)`, `right` = `0x007fd0c0(-S, 2,0)`, ahol S = `[this+0x30]` (f64, f32-re konvertálva), a 2,0 pedig f32 az `0xcf3a48` címen (`fld dword`). A `right` az előjelet a `fchs` utasítással adja. Hívóhely: `0x007fdcda` (`left`) és `0x007fdc4e` (`right`), mindkettő a `0x007fda80`-ban.
- **Mit csinál a `0x007fd0c0` (94 bájt, megerősített).** Az alap B: ha `[this+0x4c] >> 1` nulla, akkor `[this+0x40]` (f64). Egyébként az utolsó rekord `+0x10` mezője: rekordlista `[this+0x48]`, rekordméret 0x28, n = `[this+0x4c] >> 1`. Utána v = `0x009a5210()` (eltelt idő, lásd a helyesbítést), és egy négy dupla szerkezet készül: vtábla `0x0072df60`, B, B+dx, v, v+dy. Ezután `call 0x009e6010`, az EAX-ban a szerkezet címével. A `0x007fd0c0` `xor eax, eax`-szal tér vissza.
- **Mit léptet: JAVÍTVA (38.2.24 §1).** A `0x0072df60` nem vtábla, hanem a rekord `easing`-függvénye; a `0x009e6010` a 40 bájtos rekord hozzáfűzése. A B az animátor kurzora, nem kép vagy dátum. Bizonyított: B-t S-sel tolja el, a második koordinátát a `dy` értékkel (2,0 vagy 4,0) növeli.
- **Mennyit (részben).** A lépték S = `[this+0x30]`; a dy 2,0 a `left` és a `right` hívásban. S írója NINCS MEG (4. pont), a dy jelentése NINCS MEG.
- **Új, mért: a nyíl-billentyűk is ide jutnak.** A `0x00801270` WM_KEYDOWN ágán: `0x25` és `0x26` a `0x008014bc` ágra ugrik, onnan `0x008011b0` hívódik, amely `0x007fd0c0`-t hív. `0x27` és `0x28` a `0x008014ac` ágra ugrik, onnan `0x00801210`, amely szintén `0x007fd0c0`-t hív. **LEZÁRVA (38.2.24 §1):** `0x25` és `0x26` +S-et, `0x27` és `0x28` -S-et ad (`0x008012bf`-`0x008012d9`).

**3. `0x007fdd00`: a `sliderthumb` húzása (megerősített, diszasszembly `0x007fdd00`-`0x007fde73`)**

- **Befogás.** x a [L, L+W] közé szorítva. L = `[this+0x6d8]` (a `timeline` sáv bal széle), W = `[this+0x6c8]` (a sáv szélessége), egész számok f32-re konvertálva.
- **Normált pozíció.** t = (x - L) / W (f32 osztás).
- **Keresés.** Ha `[this+0x38c] >> 1` legalább 1, n = `[this+0x38c] >> 1`, és minden i < n-re d_i = |A[i] / A[n-1] - t|, ahol A = `[this+0x388]` (f64 tömb). Kezdeti küszöb 1e7 (f64 `0xcf3e88` = 10000000,0). i* = az első i, amelyre d_i szigorúan kisebb az addigi minimumnál.
- **Kimenet.** `[this+0x514]` = i*. `[this+0x510]` = a rekord `+0` mezője, ha i* < `[this+0x3ac] >> 1` (rekordlista `[this+0x3a8]`, rekordméret 0xf8), egyébként 0.
- **A gomb helye.** `[this+0x728]` = trunc(x_c - (floor(SW/2) + 3)), ahol x_c a befogott x, SW = `[this+0x718]` a gomb szélessége. `[this+0x72c]` (felső szél) változatlan marad. A csonkolást a `0x00c29990` végzi (lent).
- **Dátum vagy képindex?** A leképezés sorszámot ad (i*): a csúszka helyéhez a normált A[i]/A[n-1] sor legközelebbi tagját rendeli. Hogy A dátumsor-e (és így a csúszka dátumot ad), **NINCS MEG**, mert `[this+0x388]` írója nincs nyomon követve. Ghidra-kör kell: `[this+0x388]` és `[this+0x38c]` írói, teljes pásztázással (`paszta.py`). [blokkolt]
- **A `0x00c29990` (28 bájt).** Ha `[0xda1428]` nem nulla: `cvttsd2si` (csonkolás). Ha nulla: x87 ág (`fistp` és javítás), amely csak akkor csonkol, ha az FPU kerekítési módja csonkoló. A fájlban a jelző értéke 0, írója NINCS MEG. [blokkolt, csak a csonkolás részleteihez]

**4. `0x007fbab0` (kártya-görbe) és `0x007fd8c0` (a 0,666-hoz legközelebbi kártya)**

*Görbe (megerősített).* Négy pont az objektum mezőin (k = 0..3):
- X_k: `+0x50`, `+0x5c`, `+0x68`, `+0x74`; Y_k: `+0x54`, `+0x60`, `+0x6c`, `+0x78`; W_k: `+0x58`, `+0x64`, `+0x70`, `+0x7c`.
- Bernstein-súlyok t-ből: B0 = (1-t)^3, B1 = 3t(1-t)^2, B2 = 3t^2(1-t), B3 = t^3.
- Konstansok (mind f64, `fld qword`): 3,0 (`0xcf39f8`), 2,0 (`0xc7d9d0`), 0,5 (`0xc72150`), és az 1,0 `fld1`-gyel.
- Képlet: N_x = Σ B_k·X_k, N_y = Σ B_k·Y_k, D = Σ B_k·W_k. x_out = 0,5 + 0,5·(2·N_x - 1)/D; y_out = 0,5 + 0,5·(2·N_y - 1)/D; w_out = 1/D. A kimenet három f32 az EAX-ban adott pufferbe: x, y, w.
- Ellenőrzés: a konstansok, a `fdivr`, az `fld1` és a 0,5-ös szorzás-összeadás a diszasszemblálásban megvan. A teljes x87 műveleti sorrend végigkövetése nem készült el.

*Mezők írói: NINCS MEG.* A `0x007fa7f0` konstruktor `ebp`-n át nem ír a `+0x18`…`+0x7c` mezőkre (csak a `+0x48` vtábla-mutatót). A `0x007fbab0` hívói: `0x007fbce0` (`0x007fbd3a`), `0x007fc010` (`0x007fc100`), `0x007fd8c0` (`0x007fd91c`). Ghidra-kör kell: a három hívó `this`-e, és a `+0x50`…`+0x7c`, `+0x20`, `+0x30` mezők írói. [blokkolt]

*Legközelebbi kártya (`0x007fd8c0`, 304 bájt, megerősített).*
- Kezdeti küszöb: 1000000,0 (f32 `0xcf4900`).
- Ciklus i = 0..n-1, n = `[this+0xb4] >> 1`. t_i = i·S + O, ahol S = `[this+0x30]`, O = `[this+0x20]` (f64). Hívja a `0x007fbab0`-t t_i-vel, majd d_i = |x_out - 0,666|. A 0,666 f64 az `0xcf4860` címen (0,6660000085830688).
- Az első legkisebb d_i nyer (szigorú `<`). Az eredmény `[this+0]` = i*. A kimeneti mutató (első argumentum) a rekord `+0` mezőjét kapja (rekordlista `[this+0xb0]`, rekordméret 0xf8).
- A minimum-tároló a verem E0+0xc helyén van; a dekompiláció és a diszasszembly egyezik.

*Visszatérési érték (feltételes).* Ha |[this+0x18]| > 0,01·S (f64 `0xcf40b8` = 0,01), `al` = 0. Egyébként n2 = `[this+0x4c] >> 1`: n2 > 1 esetén 0; n2 = 0 esetén 1; n2 = 1 esetén, a = a rekord `+0x18`, b = a rekord `+0x20`: ha a = b, 1; egyébként (v - a)/(b - a) > 1,0 esetén 1, különben 0; v = `0x009a5210()`. A jelentése **NINCS MEG**.

*A 0,666 szerepe.* A ciklus azt a kártyát választja, amelynek görbe-x-e (x_out) a legközelebb van 0,666-hoz. Hogy ez az aktuális kártya-e, **NINCS MEG** (a `0x00801cb0` és `0x00801cd8` hívók nincsenek visszafejtve). [blokkolt]

**5. `0x00802c60`, `[this+0x2e8]`, és a `startbutton` visszahívása**

- **`0x00802c60` (297 bájt, megerősített).** A `OneUpUI` konstruktora (vtábla `0x00cbd5c4`). Paraméterei: az új objektum, `param_2` = `this` (a `+0x25c` mezőbe), `param_3` = `[this+0x2e8]` (a `+0x260` mezőbe). Az objektum 0x268 bájt: foglalás `0x0097c5d0`, nullázás `0xbf37c0` (`0x007fae32`-`0x007fae39`). A visszatérés `[this+0x2dc]`-be kerül (`0x007fae55`). Ez 38.2.21 §4-gyel egyezik.
- **`[this+0x2e8]` = `[X+0x8]` (megerősített).** A `0x007fa7f0` `mov edi, eax` sora az X-et veszi fel, és a `this`-t `mov ebp, [esp+0x34]`-gyel az új objektumból. X a `0x008037e0` (qshow-építő) `edi`-je, amelyet a `0x00803920` előtt `mov eax, edi` ad át. Hogy ez melyik objektum, **NINCS MEG**.
- **Osztály: NINCS MEG.** A `0x008037e0` egyetlen közvetlen hívója a `0x005e8a70` (`CThumbUI::MakeTimeline`, 38.2.22 §1), ezért X feltehetően a `MakeTimeline` tulajdonosa, de ez feltételes. Ghidra-kör kell: `0x008037e0` `edi`-forrása és `[X+0x8]` osztálya. [blokkolt]
- **A `startbutton` sorrendje (megerősített).** A `0x007fda80` `0x007fdb0a`-es hívása a `0x007fb820` (kilépési ág, 6. pont). Utána, ha `[this+0x2e8]` nem nulla: `mov ecx, [this+0x2e8]`, `mov eax, [edx+0x18]`, `call eax` (`0x007fdb3d`). Ez a vtábla +0x18 slotját hívja `(-1, azonosító)` argumentumokkal. Az azonosító `[[this+0x3ec] + [this+0x3f8]·4]` (38.2.22 §5, ebben a körben nem mértem újra).
- **A vtábla +0x18 célja: RÉSZBEN JAVÍTVA (38.2.24 §4).** A `OneUpUI` vtábla 6. slotja a `0x0097b5e0`: `add ecx, 0x28`, `push ecx`, `call [0xc4055c]`. Ha a `[this+0x2e8]` objektum ugyanabból az alaposztályból való, ugyanez a `thunk`; ezt nem igazoltam. **JAVÍTVA (38.2.24 §4):** a `[0xc4055c]` a KERNEL32 `EnterCriticalSection` IAT-rekesze (a PE-importtáblából; az index `imports.address` oszlopa a név RVA-ja, nem a rekesz címe). Így a thunk `EnterCriticalSection(this+0x28)`. Az X osztálya továbbra is nyitott, ezért a `startbutton` célja NINCS MEG (38.2.24 §4).
- **A diavetítés-indítási feltevés nem támogatott.** A gomb a kilépési ágat futtatja előbb, és csak utána értesíti a forrást `(-1, azonosító)`-val. Ez inkább „bezár, és az azonosítót visszaadja" mintát mutat. A forrás válaszának megfejtése nyitott.

**6. `0x007fb820` (kilépési ág) és `0x007fd770` (találati ág)**

- **`0x007fb820` (459 bájt, megerősített lépések).** ECX = `this`.
  1. `[this+0x3bf] = 1`.
  2. Ha `[this+0x3bb] == 0`:
     - `[this+0x3be] = 0`; `0x008001c0(this, this+0x46c, -1, -1, -1, -1)` (NINCS MEG); `[this+0x3b8] = 0`; `0x009ad280(this+0x46c)` (NINCS MEG).
     - Ha `[this+0x49c] == 0`: `0x009a8d80(...)`, különben `0x009a8ca0(...)` (NINCS MEG).
     - `QueryPerformanceCounter` → `[this+0x520]` (f64, a kezdő idő).
     - `old` = `0x004019b0([this+0x760])`: a `Preferences\SlideshowEffectTime` értéke. Majd `0x00401900([this+0x760], 2)`: a 2 íródik a registry-be és a gyorsítótárba (`[this+0x76c]`).
     - Várakozás: eltelt idő = (QPC - [this+0x520]) × (1/QPF), és küszöb = `0x004019b0([this+0x760])` × 0,6 (f64 `0xcf3a70`; negatív értéknél +2^32). Amíg thr > elapsed: `0x00801f50(this)` (NINCS MEG), majd újra.
     - `0x00401900([this+0x760], old)`: visszaállítás.
  3. Ha `vt+0x24(this)` nem nulla, annak az eredményén `vt+0x14(0,0)` hívódik. Ha nulla, és a `[this+0x2dc]` (`OneUpUI`) vt+0x24 hívása nem nulla, azon hívódik `vt+0x14(0,0)`. Egyébként visszatérés 0. A `vt+0x14` célja NINCS MEG.
  4. Visszatérés 0.
- **A várakozás értéke: 2 × 0,6 = 1,2 s (a kódútra megerősített).** A 2 kiírása után a `0x004019b0` a registry-ből olvas; ha az sikeres, 2-t kapunk, ha nem, a gyorsítótárban maradt 2 az érték. Ha a registry-írás hibázik, de a kiolvasás sikerül, a régi érték × 0,6 lenne. Futásidejű ágat nem mértem: NINCS MEG.
- **Az Escape-ág (megerősített).** A `0x00801270` (`OneUpUI` billentyű-kezelője) WM_KEYDOWN ágán (`0x0080129e`): `cmp al, 0x1b` (`0x008012a7`), `jne 0x008012bf`, különben `mov ecx, ebx` és `call 0x007fb820` (`0x008012b1`). Escape tehát közvetlenül ide vezet. A `0x007fb820` többi hívója: `0x007fdb0a` és `0x007fdbc2` (`0x007fda80`), `0x007fe171` és `0x007fe43c` (`0x007fde80`), `0x008005bb`, `0x008005e1`, `0x008007fe` (`0x008001c0`), `0x008027c8` (`0x00802630`).
- **`0x007fd770` (129 bájt, megerősített).** Argumentum: i. x = ([this+0x8] - (i·S + O)) - (B - v'), ahol v' = `0x009e5e70(0x009a5210())`, B mint a 2. pontban; dy = `+4,0` (f32 `0xc7e4a4`). Hívja a `0x007fd0c0`-t. **Visszatérés: 0**, mert a `0x007fd0c0` `xor eax, eax`-szal tér vissza, és a `0x007fd770` `ret 4` előtt az EAX-t nem írja. A dekompiláció `void`-ja ezt nem mutatja.
- A találati ág (`0x007fd800`) így 0-t ad, és a hívó (`0x007fde80`) nullának látja: ekkor az `[esp+0x18]` (a rekord `+0` mezője) folytatódik (38.2.22 §3). A `0x202` (felengedés) `0x007fd770(this+0x514)` hívása a húzás végén ugyanide visz (38.2.21 §3).

**Helyesbítések**

1. **38.2.22 §3, `0x007fd770`:** a „visszatérése NINCS MEG" **LEZÁRVA**: 0 (6. pont).
2. **38.2.22 §3, `0x009a5210`:** az „időablak-ellenőrzés" **TÉVES**. A `0x009a5210` eltelt idő: `QueryPerformanceCounter` (`call [0xc40298]`), a cache `[0xd678e8]` = 1/QPF (a `0x007fb820` is ezt használja). Az időablak-vizsgálat a `0x007fd8c0` belsejében van (4. pont).
3. **38.2.22 §3, legkisebb-kereső eltérés:** **LEZÁRVA**. A minimum-tároló a verem E0+0xc helyén van, a dekompiláció helyes.
4. **38.2.22 §5, húzás-sáv és csúszka:** a „feltételes" **MEGERŐSÍTETT**. A csúszka-gomb képlete (`[this+0x728]`) **LEZÁRVA** (3. pont). A dátum-leképezés **RÉSZBEN**: a csúszka x → rekordsorszám (i*) igazolt; a dátum jelentése NINCS MEG.
5. **38.2.18 és 38.2.22 (Escape):** az Escape-kilépés `0x007fb820`-ra megerősítve; az út közvetlen, a `0x00801270`-ból (5. pont).
6. **38.2.23 §2 (`0x009e6010`, `0x0072df60`):** JAVÍTVA: a `0x0072df60` `easing`-függvény, nem vtábla (38.2.24 §1).
7. **38.2.23 §2 (nyíl-billentyűk dx-előjele):** LEZÁRVA: `0x25`/`0x26` +S, `0x27`/`0x28` -S (38.2.24 §1).
8. **38.2.23 §5 (`[0xc4055c]`):** JAVÍTVA: KERNEL32 `EnterCriticalSection`, a „nincs import-név" állítás téves volt (38.2.24 §4). Az index `imports.address` oszlopa a név relatív címét (`RVA`) adja, nem a rekesz virtuális címét: rekesz-címhez a PE-importtáblát kell olvasni.

**Bizonyítottsági fok (38.2.23)**

| állítás | bizonyíték | fok |
|---|---|---|
| `0x005e6710` = `CThumbUI::vftable` +0x30 | vtábla-bájtok `0x00c9055c`; DATA-él | megerősített |
| `0x005e6710` ágai és visszatérése | dekompiláció és kapcsoló-ellenőrzés; Esc, Space, nyíl nincs | megerősített |
| pumpa-lánc a `0x0097fc30`-ig | index, 12 szint, 11 hívó: negatív; a vtábla-hívás nem látszik | NINCS MEG |
| `left` = +S, `right` = -S, dy = 2,0 | `fld qword [eax+0x30]`, `fchs`, `fld dword [0xcf3a48]` | megerősített |
| `0x007fd0c0` alap B és a négy dupla szerkezet | dekompiláció és diszasszembly `0x007fd0c0`-`0x007fd11b` | megerősített |
| `0x009e6010` szemantika | NINCS MEG | nyitott |
| csúszka: befogás, i*, `[this+0x728]` | diszasszembly `0x007fdd00`-`0x007fde73` | megerősített |
| csúszka: dátum vagy sorszám | `[this+0x388]` írói NINCS MEG | nyitott |
| `0x00c29990` ágai | diszasszembly `0x00c29990`, `0x00c299c6` | megerősített (a jelző írója NINCS MEG) |
| kártya-görbe képlete és konstansai | diszasszembly `0x007fbab0` (`fld1`, 2,0, 0,5, 3,0) | megerősített |
| görbe-mezők írói | a konstruktor nem írja; a többi NINCS MEG | nyitott |
| `0x007fd8c0`: i*, 1e6, 0,666 | diszasszembly `0x007fd8c0`-`0x007fd9ed` | megerősített |
| `0x007fd8c0` visszatérési érték | diszasszembly; jelentése NINCS MEG | feltételes |
| `0x00802c60` = OneUpUI, `[this+0x2dc]`, 0x268 | vtábla `0x00cbd5c4`; `0x007fae32`-`0x007fae55` | megerősített |
| `[this+0x2e8]` = `[X+0x8]` | `0x007fa7f0` `mov edi, eax`, `mov edx, [edi+8]` | megerősített |
| `[this+0x2e8]` osztálya | NINCS MEG | nyitott |
| `startbutton` sorrendje | `0x007fdb0a`, `0x007fdb3d` | megerősített |
| `[0xc4055c]` célja | NINCS MEG | nyitott |
| Escape közvetlen út | `0x00801270` `0x008012a7`-`0x008012b1` | megerősített |
| kilépési ág lépései | diszasszembly `0x007fb820`-`0x007fb9ea` | megerősített (az ismeretlen hívások NINCS MEG) |
| várakozás 1,2 s | `mov [esp+0x10], 2` és a `0x004019b0` olvasás | megerősített a kódútra; futásidőben feltételes |
| `0x007fd770` visszatérése 0 | `ret 4`, `xor eax, eax` a `0x007fd0c0`-ban | megerősített |

**Nyitott kérdések mérlege (38.2.23)**

Nyitott kérdések: 0 nyílt · 14 lezárva · 12 blokkolt · 0 hatókörön kívül · 0 csak nyitva.

A 38.2.24 mérlege a 38.2.24 végén van; a fenti tételek egy részét az ottani helyesbítések lezárják (6-8. pont a 38.2.23 helyesbítései között).

- **Lezárva (14):** (L1) `left` és `right` előjele és dy = 2,0; (L2) a nyíl-billentyűk a `0x007fd0c0`-ra; (L3) csúszka: befogás, i* és a gomb képlete; (L4) `0x00c29990` ágai; (L5) kártya-görbe képlete és konstansai; (L6) `0x007fd8c0` min-kereső és az eltérés; (L7) `0x00802c60` = OneUpUI, 0x268 bájt; (L8) `startbutton` sorrendje; (L9) Escape közvetlen út; (L10) kilépési ág lépéssora; (L11) 1,2 s várakozás a kódúton; (L12) `0x007fd770` visszatérése 0; (L13) `0x009a5210` javítása; (L14) pumpa-hívó negatív index-keresése 12 szinten (az index korlátaival).
- **Blokkolt (12):** (B1) pumpa-hívó és időtúllépés; (B2) léptetési ütem; (B3) `0x009e6010` és `0x0072df60`; (B4) S és O írói; (B5) `[this+0x388]` írói és a dátum jelentése; (B6) `[0xda1428]` írója; (B7) görbe-mezők írói; (B8) `0x007fd8c0` visszatérési értéke és a 0,666 szerepe; (B9) `[X+0x8]` osztálya és X; (B10) `[0xc4055c]` célja; (B11) kilépési ág ismeretlen hívásai; (B12) registry-írás sikertelenségének ága (futásidő).

**Amit KIZÁRTAM**

- A `0x005e6710` nem a pumpa; a pumpa a `0x0097fc30`, és a `0x005e6710` nem hív pumpát.
- A `left` nem `-S`-t ad: a `left` `+S`, a `right` `-S`.
- A `0x007fd770` nem ad nem-nulla visszatérést: mindig 0.
- A `0x009a5210` nem időablak-ellenőrzés: eltelt idő (QPC).
- Az Escape nem a `0x00802630` listavégi ágán megy; a `0x00801270` közvetlenül hívja a `0x007fb820`-t.
- A `startbutton` sorrendjében a diavetítés-indítás nem támogatott (lásd 5. pont).

**Következő Ghidra-címek**

- `Ghidra-kör kell: 0x005e6710 hívóhelye - a CThumbUI vtábla +0x30 hívása (call [reg+0x30]) a 0x0097fc30 hívóiban (0x0040e410, 0x005ffc30, 0x006f9cc0, 0x006fe630, 0x009d4d10, 0x004051b0, 0x0059e920, 0x007420f0, 0x007422d0, 0x0094aa00, 0x0094ace0); az Időrend-pumpa és időtúllépése [blokkolt]`
- `Ghidra-kör kell: 0x009e6010 és a 0x0072df60 vtábla - mit léptet a négy dupla szerkezet (B, B+dx, v, v+dy) [blokkolt]`
- `Ghidra-kör kell: [this+0x30] és [this+0x20] írói - a kártya-lépték (S) és eltolás (O) forrása [blokkolt]`
- `Ghidra-kör kell: [this+0x388] és [this+0x38c] írói - a csúszka-tömb: dátum vagy sorszám [blokkolt]`
- `Ghidra-kör kell: 0x007fbce0, 0x007fc010, 0x007fd8c0 this-hívói és a 0x007fbab0 +0x50..+0x7c mezőinek írói [blokkolt]`
- `Ghidra-kör kell: 0x008037e0 edi-forrása (X) és [X+0x8] osztálya [blokkolt]`
- `Ghidra-kör kell: 0x00c4055c - a 0x0097b5e0 thunk célja, a startbutton visszahívás végpontja [blokkolt]`
- `Ghidra-kör kell: 0x008001c0, 0x009ad280, 0x009a8d80, 0x009a8ca0, 0x00801f50 és a vt+0x24 / vt+0x14 célja - a kilépési ág lépései [blokkolt]`
- `Ghidra-kör kell: 0x007fd8c0 visszatérési értéke és a 0x00801cb0, 0x00801cd8 hívók [blokkolt]`
- `Ghidra-kör kell: [0xda1428] írója (az x87 vagy cvttsd2si ág) [blokkolt, csak a csonkolás részleteihez]`
- `Mérés kell (futásidő, nem Ghidra): a Preferences\SlideshowEffectTime írása sikeres-e a tulajdonos gépén (registry-próba) [blokkolt, az 1,2 s állításhoz]`

#### 38.2.24 Az Időrend bináris feltárása, 7. kör: animátor-rekord, nyíl-billentyűk, kártya-elrendezés, léptetés, `startbutton` (#5401, 2026-10-21)

**Kérdés és hatókör.** Négy kérdés a `2026-10-21-idorend-7.txt` nyolc címéről: (1) `0x009e6010` és `0x0072df60`: az animátor, a `left`/`right` és a nyíl-billentyűk; (2) `0x007fbce0`, `0x007fc010`, `0x008001c0`: a kártya-görbe mezői, az elrendezés és az `A` tömb; (3) `0x00801cb0` és `0x00801f50`: a körönkénti frissítés és az automatikus léptetés; (4) `0x0097b5e0`: a `startbutton` visszahívása. Terméki kódot nem írtunk.

**Bemenet és módszer.** Diszasszembly a `pe_dis.cdis` (capstone) segítségével; a függvényméretek az index `functions` táblájából valók. A `0x0072df60` nincs az indexben (a 7. Ghidra-futás hozta létre), ezért a diszasszembly a forrás. A PE-importtáblát közvetlenül a `Picasa3.exe` bájtjaiból olvastam (`FirstThunk` és ILT). Futásidejű próba és új Ghidra-futás nem volt. Az ideiglenes fájlok a `.bt/` alatt voltak, a kör végén törölve.

**Javítások a korábbi szakaszokban (a 38.2.23-ban is jelölve).**
1. A `0x0072df60` nem vtábla, hanem a rekord `easing`-függvénye (megerősített).
2. A `[0xc4055c]` nem „import-név nélküli" slot: a `KERNEL32` `EnterCriticalSection` rekesze.
3. A nyíl-billentyűk dx-előjele mérve: `0x25` és `0x26` +S, `0x27` és `0x28` -S.
4. Eszköz-tanulság: az index `imports.address` oszlopa a név relatív címét adja (`EnterCriticalSection`: `0x00921b04`), nem a rekesz virtuális címét (`0x00c4055c`). Rekesz-címhez a PE-importtáblát kell olvasni.

**1. Animátor: `0x009e6010`, `0x0072df60`, `left`/`right`, nyíl-billentyűk**

- **A rekord (megerősített).** A `0x007fd0c0` (94 bájt, `ret 8`) a veremben 40 bájtos rekordot épít, és a `0x009e6010`-zal (`call` a `0x007fd110`-nál) hozzáfűzi az animátor tömbjéhez. Az animátor a P objektumban van (P = `this+0x2f8`, a `0x007fd0c0` a P+0x38 alrészt használja): darabszám `[P+0x4c]>>1`, tömb `[P+0x48]`, gyorsítótárazott pozíció `[P+0x40]` (f64). A rekord mezői a verem-címekből: +0 függvénymutató (`0x0072df60`), +8 B (kezdőpozíció), +0x10 B+dx (végpozíció), +0x18 v (kezdő idő), +0x20 v+dy (végidő).
- **`0x009e6010` (236 bájt, megerősített).** Hozzáfűzés: 10 dword (40 bájt) másolása. A tömb kapacitása duplázódik 1 MiB-ig (`0x100000` bájt), azután 1024 rekordonként nő. Siker: 0; sikertelen lefoglalás: 4.
- **Easing: `0x0072df60` (megerősített, a `0x0072df60`-`0x0072e047` tartomány).** Bemenet u (f32). Ha u >= 1, az eredmény 1; ha u <= 0, 0. Különben y = 8·u (f64 `0xc7ea10` = 8,0), és:
  - ha y < 1: g(y) = y - 1 + E(-y);
  - ha y >= 1: g(y) = a + (1 - a)·(1 - E(-(y - 1))), ahol a = E(-1) (f32 `0xcf3ed0` = -1,0).

  Az eredmény K·g(y). E = `0x0040eac0`, amely a `0x00c29c6c` CRT-ugrót hívja (lásd B8). K = f64 `0xd337a8`, kezdetben 1,0 (őrszem): ha 1,0, a `0x009e5ac0` (96 bájt) beállítja K = 1 / g(8) értékre (a diszasszemblált `fdiv`). A g(8) számértéke a fenti konstansokból adódik; futtatott mérés nincs.
- **Folytonosság (erős érv, nem azonosítás).** g(1-) = E(-1) = a = g(1+). A deriváltak 1 - E(-1) és 1 - a, ezek egyeznek. Ez exp-re teljesül, más E-re általában nem (lásd B8).
- **Pozíció és Δ (megerősített).** A `0x009e5e70` (285 bájt): `pos(t) = B0 + Σ_j ease(u_j)·dx_j`, ahol u_j = (t' - v_j)/(end_j - v_j), dx_j = (B_j+dx_j) - B_j, t' = t + 0,02 (f64 `0xcf48a8` = 0,02), és B0 az első rekord B-je. Üres tömbnél a gyorsítótár az érték. A gyorsítótár `[P+0x40]` (`0x009e5f74`, `0x009e5eed`).
- **`0x009e5f90` (74 bájt, megerősített).** A visszatérés Δ = pos(t) - az előző gyorsítótár-érték, vagyis a kurzor előjeles elmozdulása az előző kiértékelés óta. Első híváskor a gyorsítótár az első rekord B-je.
- **`left` és `right` (megerősített).** `0x007fd120` = `0x007fd0c0(+S, 2,0)`, `0x007fd150` = `0x007fd0c0(-S, 2,0)`. S = `[P+0x30]` (f64, f32-re konvertálva), 2,0 = f32 `0xcf3a48`.
- **Nyíl-billentyűk (megerősített).** A `0x00801270` `WM_KEYDOWN` ága: `cmp al, 0x25` és `0x26` → `je 0x8014bc` → `0x8011b0` (`call 0x7fd0c0`, +S, 2,0); `cmp al, 0x27` és `0x28` → `je 0x8014ac` → `0x801210` (`fchs`, -S, 2,0). Mindkettő csak akkor animál, ha `[OneUp+0x3b8] != 0`; egyébként a `0x802980`/`0x802ae0` (a `0x8011b0`-ból), illetve a `0x8029f0`/`0x802a90` (a `0x801210`-ből) ágak futnak (NINCS MEG, mit csinálnak).
- **Időtartam (megerősített).** Nyíl és `left`/`right`: 2,0 s. Kattintás (`0x007fd770`, 129 bájt): dy = 4,0 (f32 `0xc7e4a4`). Az időegység a másodperc: `0x009a5210` = `QPC` · (1/`QPF`), a gyorsítótár `[0xd678e8]` (a `0x009a51b0` tölti ki `QueryPerformanceFrequency`-vel).
- **Mit mozgat (megerősített).** A `[P+0x40]` kurzort: ±S értékkel 2,0 s alatt, a fenti görbével. A kártyákat ennek Δ-ja tolja el (2. pont).
- **Mit jelent S (megerősített).** S a paraméter-lépköz a kártyák között: `t_i = i·S + O` (`0x007fc010`, `0x007fd8c0`, `0x007fd770`). Egy nyíl-lépés tehát egy kártyányi eltolás. S írója NINCS MEG (B1).

**2. Kártya-görbe, elrendezés, `0x007fbce0`, `0x007fc010`, `0x008001c0`, `A`**

- **Görbe `0x007fbab0` (559 bájt).** Bemenet t (f32), ECX = P. Olvassa P+0x50+12k (X_k), P+0x54+12k (Y_k), P+0x58+12k (W_k), k = 0..3 (`0x007fbab7`), Bernstein-súlyok, konstansok 3,0 / 2,0 / 0,5 / 1,0. Kimenet (x, y, w) az EAX-ban kapott pufferbe; az utolsó írás `0x007fbcaf` (`fstp dword [eax]`), a `ret 4` a `0x007fbcdc`-nél. A 38.2.23 §4 képlete a konstansokra és a fő lépésekre igaz (erős); a teljes x87-sorrend nincs végigkövetve.
- **P+0x20 és P+0x18 írói (megerősített, `0x007fc010`, 1191 bájt).** O = P+0x20: `0x007fc045` (`fst qword [ebp+0x20]`: O ← Δ + v + O régi), `0x007fc071` (felső korlát: O ← [P+8]), `0x007fc07e` (alsó korlát: O ← [P+8] - (n-1)·S). v = P+0x18: `0x007fc09e` (`fstp qword [ebp+0x18]`: v ← 0,95·v; f64 `0xcf40b0` = 0,95). Egy képkockán a sorrend: O ← Δ + v + O, korlátok, v ← 0,95·v.
- **Az S értéket a `0x007fc010` csak olvassa** (`[P+0x30]`); a többi írót lásd B1.
- **P+0x50..0x7c írói (NINCS MEG).** A `0x007fc010` ezeket nem írja: a `[esp+0x50]`…`[esp+0x68]` írások a verem helyi változói. Ghidra-kör kell (B2).
- **`0x008001c0` (megerősített, a dekompilált törzs alapján).** A `OneUpUI` renderelő függvénye. A saját zárolási mezőit írja (`[OneUp+0x20]` tulajdonos szál, `[OneUp+0x24]` beágyazás-számláló) és a `[OneUp+0x519]` jelzőt. P-mezőt nem ír. Figyelem: itt a `+0x20` a OneUp mezője, nem P+0x20.
- **Kártya-elrendezés (megerősített).** Minden i < n = `[P+0xb4]>>1` kártyára:
  - t_i = i·S + O, és (x, y, w) = görbe(t_i);
  - eltolás (x·W_r, y·H_r), ahol W_r = R[2] - R[0], H_r = R[3] - R[1], és R = `[OneUp+0x2c8]` (a `0x00801cb0` adja át); az R-hez viszonyított kezdőpont a mátrix-láncból nincs igazolva;
  - lépték = w · Z, Z = `[P+0x28]` (f64);
  - átlátszóság: a kártya-rekord +0xa0 mezője = `ROUND`((1 - f(z))·256), z = max(0, (1/w - 1)/9); f64 `0xcf3ef8` = 9,0, f64 `0xcf39d8` = 256,0; f = `0x005568e0` (NINCS MEG, B4);
  - látható lista: w > 0,1 (f64 `0xc7dd30` = 0,1); az indexek a `[P+0x80]` tömbben, darabszám `[P+0x84]>>1`; a rendezést a `0x00604480` végzi (NINCS MEG, B10).
- **Az elrendezés index-lineáris (megerősített).** A kártyák egyenlő t-lépésre állnak egymástól, i szerint. A dátum csak az `A` tömbön keresztül léphetne be (lásd alább).
- **`0x007fbce0` (166 bájt, megerősített).** t_i = i/10000 - 1 (f64 `0xcf42a8` = 10000,0), i = 0..19999 (`cmp esi, 0x4e20`), vagyis t ∈ [-1, 1) 0,0001-es lépéssel. Minden t_i-re hívja a `0x007fbab0`-t, és a kimeneti x-et veti össze 0,666-tal (f64 `0xcf4860`). A legkisebb |x - 0,666| adja t*-ot (az első i, szigorú `<` összehasonlítással). Visszatérés: t* (f32). Hívója a `0x007fbd90` (`0x007fbe74`); hogy mit kezd t*-gal, NINCS MEG (B12).
- **`A = [OneUp+0x388]` (NINCS MEG).** Olvasója a `0x007fdd00` (38.2.23 §3). Írói nincsenek nyomon követve, ezért a dátum vagy index kérdés nyitott (B3).

**3. Körönkénti frissítés és automatikus léptetés: `0x00801cb0`, `0x00801f50`, `0x00802060`, `0x00802630`**

- **`0x00802060` (198 bájt, megerősített ágak).** A körönkénti pumpa; `this` = OneUp. Első lépése `[0x3fc] = 1`. Ágak:
  1. `[0x3bb] != 0`: a `0x802121`-es ág (NINCS MEG, nem Időrend-frissítés).
  2. `[0x3b8] != 0` (animált mód): `call 0x801cb0` (`0x802087`). Utána, ha `[0x3c1] != 0`, léptetés (`0x802630`); különben `0x801f50` (`0x802110`).
  3. `[0x3b8] == 0`: ha `[0x518] != 0`, léptetés. Különben `elapsed` = `0x9a51b0([0x520])` (másodperc a `[0x520]` óta), `pref` = `0x4019b0([0x760])` (a `Preferences\SlideshowEffectTime` egész értéke, másodpercben); ha `elapsed > pref`, léptetés; ha `[0x3c1] != 0`, léptetés; különben `0x801f50`.
- **`0x00801cb0` (64 bájt, megerősített).** (1) `0x007fc010(P, &[OneUp+0x2c8])`: a kártya-elrendezés. (2) Ha `[OneUp+0x429] == 0` és a `0x007fd8c0(P, &[OneUp+0x510])` AL = 1, akkor `0x008018a0` fut (ECX = OneUp, EAX = `[OneUp+0x510]`). Az AL = 1 a 38.2.23 szerinti nyugalom-feltétel (feltételes jelentés).
- **`0x008018a0` (1029 bájt).** Belépéskor, ha `[OneUp+0x50c] == EAX`, visszatér (`0x801ca3`). Különben eltárolja az új értéket, és frissíti a nézetet. A hívott `0x004133e0`, `0x004b0190` és `0x0097caf0` szerepe NINCS MEG (B10).
- **`0x007fd8c0` (304 bájt, megerősített).** Kimenet: `[OneUp+0x510]`. AL = 1, ha a kiértékelés nyugalmat lát (38.2.23 szerint, feltételes).
- **`0x00801f50` (261 bájt, a hívások megerősítve).** Ha `[this+0x50]` nem nulla, `QPC`; `vt+0x40` ellenőrzés; ha `[this+0x3ba] != 0`: `GetClientRect` a `vt+0x24()` objektum `+0x6c` HWND-jén, `0x009b49c0(&rect)` (elrendezés), `vt+0x24(-1,-1,-1,-1)`, `0x009aa670`, `0x00800950(&rect)`. Különben `0x00aa6fb0` és `0x00aa6b70`. Hívói: `0x00802110` (a körönkénti pumpa) és `0x007fb981` (a kilépés 1,2 s-os várakozása). Vagyis képernyő-frissítés; a részletek NINCS MEG (B10).
- **Automatikus léptetés: `0x00802630` (500 bájt, megerősített lépések).** (a) Zárolás: `vt+0x18`, ha `[this+0xc] == 0`, különben `EnterCriticalSection(this+0x28)`. (b) Ismételt belépés: `GetCurrentThreadId` (import `0xc40284`) összevetése a `[this+0x20]`-szal. Ha ugyanaz a szál, `[this+0x24]` nő, és nincs új zárolás. Különben `[this+0x20]` = a szál, `[this+0x24]` = 0. (c) `[this+0x3f4]` += 1; a lista végén `[this+0x3fd]` dönt a körforgásról (0 esetén a `0x802765` ág). (d) Feloldás (`vt+0x1c`, illetve `LeaveCriticalSection(this+0x28)`), de csak ha a számláló 0. (e) Hívja a `0x00802230`-at (NINCS MEG, B5). (f) Ismétel, amíg a `0x00802230` nem nullát ad, és `[this+0x3f0] >> 1` elem van.
- **Az időzítő (megerősített tény, nyitott kérdés).** A `[0x520]` kezdőidőt a `0x007fb820` írja (38.2.23 §6), a `0x00802630` és a `0x00802060` nem. Ha a léptetés után nincs újraindítás, az `elapsed > pref` feltétel minden képkockán igaz lenne. Hogy ez hol áll le, NINCS MEG (B5).

**4. `0x0097b5e0` és a `startbutton` visszahívása**

- **`0x0097b5e0` (11 bájt, megerősített).** `add ecx, 0x28`; `push ecx`; `call dword ptr [0xc4055c]`; `ret`. A `[0xc4055c]` a `KERNEL32` `EnterCriticalSection` IAT-rekesze: a PE-importtáblában a `FirstThunk` rekesze ezen a virtuális címen van, és az ILT-bejegyzése ugyanazon az indexen a `EnterCriticalSection` nevet adja. Tehát a thunk `EnterCriticalSection(this+0x28)`, vagyis zárolás. A `0x00802630` ugyanezt a rekeszt hívja (`[0xc4055c]`), a `0x008001c0` pedig az `EnterCriticalSection`-t (a 7. futás szerint).
- **A visszahívás (megerősített, `0x007fdb0a`-`0x007fdb47`).** `call 0x007fb820` (a kilépési ág, 38.2.23 §6). Azután, ha `[this+0x2e8] = X` nem nulla: id = `[[this+0x3ec] + [this+0x3f8]·4]`, ha `[this+0x3f8] >= 0`, különben 0; `push id`; `push -1`; `call [vt(X)+0x18]` (ECX = X); a függvény `0xf4240` (1000000) értékkel tér vissza.
- **Ami NEM igazolt.** X osztálya NINCS MEG (38.2.23 B9), ezért a `vt(X)+0x18` célja sem igazolt. A `0x0097b5e0` csak akkor a célja, ha X vtáblája a OneUpUI-é. A visszahívás nem old fel: ebben az ágban nincs `vt+0x1c` vagy `LeaveCriticalSection` hívás. A `(-1, id)` argumentumokat a thunk nem olvassa; a verem takarítását a hívó végzi (`add esp, 0x14`, `0x007fdb44`).
- **Kimondva:** a `startbutton` visszahívás célja NINCS MEG. Két bináris tény van: (i) az aktuális elem azonosítóját adja át X-nek, (ii) X `vt+0x18` slotját hívja, és nem old fel. Ghidra-kör kell: X osztálya és `vt(X)+0x18` célja (B7).

**Bizonyítottsági fok (38.2.24)**

| állítás | bizonyíték | fok |
|---|---|---|
| 40 bájtos rekord, mezők +0/+8/+0x10/+0x18/+0x20 | `0x007fd0c0`: `0x007fd0e6`-`0x007fd10c` | megerősített |
| `0x009e6010` = hozzáfűzés | diszasszembly és dekompiláció, 236 bájt | megerősített |
| `0x0072df60` = `easing`, nem vtábla | diszasszembly `0x0072df60`-`0x0072e047` | megerősített |
| `easing` konstansok: C1 = 8,0, C2 = -1,0, K = 1 / g(8) | `0xc7ea10`, `0xcf3ed0`, `0xd337a8`, init `0x009e5ac0` | megerősített (a K számértéke futtatás nélkül) |
| E = exp | folytonosság y = 1-nél; a `0x00c29c6c` CRT-ugró | erős, nincs azonosítva (B8) |
| pos(t) és Δ | `0x009e5e70`, `0x009e5f90` | megerősített |
| `left`/`right` = +S/-S, dy = 2,0 | `0x007fd120`, `0x007fd150` | megerősített |
| nyíl: 0x25/0x26 +S, 0x27/0x28 -S | `0x008012bf`-`0x008012d9`, `0x008011b0`, `0x00801210` | megerősített |
| dy = 2,0 (nyíl), 4,0 (kattintás) | f32 `0xcf3a48`, `0xc7e4a4` | megerősített |
| S = P+0x30: olvasás | `0x008011b0`, `0x00801210`, `0x007fd770`, `0x007fc010` | olvasás megerősített, író NINCS MEG |
| O (P+0x20) és v (P+0x18) írói | `0x007fc045`, `0x007fc071`, `0x007fc07e`, `0x007fc09e` | megerősített |
| t_i = i·S + O, index-lineáris elrendezés | `0x007fc010`, `0x007fd8c0`, `0x007fd770` | megerősített |
| görbe `0x007fbab0` | 38.2.23 §4 (konstansok megerősítve) | erős |
| `0x007fbce0`: t_i = i/10000 - 1, 20000 minta | diszasszembly, f64 `0xcf42a8` = 10000 | megerősített |
| `0x00802060` ágai, `0x00801cb0` folyamata | diszasszembly `0x00802060`-`0x008020ed`, `0x00801cb0` | megerősített |
| léptetési jelzők (`[0x518]`, `[0x3c1]`) jelentése | az ágak megvannak, a jelentés nincs | feltételes / NINCS MEG |
| `[0xc4055c]` = `EnterCriticalSection` | PE-importtábla, `FirstThunk` | megerősített |
| `startbutton` célja | X osztálya nincs igazolva | nyitott |

**Nyitott kérdések mérlege (38.2.24)**

Lezárva (LEZÁRVA):
- (L1) `left`/`right` = +S/-S, dy = 2,0.
- (L2) Nyíl-billentyűk iránya (0x25/0x26 +S, 0x27/0x28 -S).
- (L3) 40 bájtos rekord, `0x009e6010` hozzáfűzés.
- (L4) `0x0072df60` `easing`, a konstansok és a K-init képlete.
- (L5) pos(t), Δ és a 0,02 s-os eltolás.
- (L6) Időtartam (2,0 s / 4,0 s) és az időegység (másodperc).
- (L7) O és v írói a `0x007fc010`-ban; a `0x007fc010` nem ír S-t.
- (L8) t_i = i·S + O, index-lineáris elrendezés.
- (L9) `0x007fbce0` keresés (t* = argmin |x - 0,666|).
- (L10) `0x00801cb0` és a `0x007fd8c0` AL-feltétele mint hívási lánc.
- (L11) `0x00802060` ágai.
- (L12) `0x0097b5e0` = `EnterCriticalSection(this+0x28)`; `[0xc4055c]` azonosítva.
- (L13) `0x00802630` zárolási, számlálós és léptetési lépései (a `0x00802230` és az időzítő kivételével).
- (L14) Kattintás `0x007fd770`: dy = 4,0.

Blokkolt (BLOKKOLT, Ghidra-kör vagy mérés kell):
- (B1) S = `[P+0x30]` írói.
- (B2) P+0x50..0x7c írói.
- (B3) `A = [OneUp+0x388]` írói, és hogy dátum-e vagy index.
- (B4) `0x005568e0`: az átlátszóság görbéje.
- (B5) `0x00802230` (a léptetés hatása) és az időzítő újraindítási helye (`[0x520]`).
- (B6) `[0x3b8]`, `[0x3bb]`, `[0x3c1]`, `[0x3fd]`, `[0x518]` jelzők jelentése és írói.
- (B7) X = `[OneUp+0x2e8]` osztálya és `vt(X)+0x18` célja (`startbutton`).
- (B8) E = `0x00c29c6c` azonosítása (exp?).
- (B9) `0x009e5b20` nem nulla ága: a `0x009e5e70` ilyenkor a visszatérési egész értéket adja pozícióként (`fild`); ennek jelentése NINCS MEG.
- (B10) `0x008018a0` nézetfrissítése, `0x00604480` rendezése és a `0x00801f50` rajzolási lépései.
- (B11) v = P+0x18 többi írója (húzás vagy sodródás kezelője).
- (B12) `0x007fbd90`: mit kezd a t*-gal.
- (B13) Mérés kell: a 2,0 s-os léptetés és a 0,02 s-os eltolás valós időzítése az eredeti Picasán (Colab-felmérő, nem Ghidra).

**Nyitott kérdések: 0 nyílt · 14 lezárva · 13 blokkolt · 0 hatókörön kívül · 0 csak nyitva.**

**Amit KIZÁRTAM**

- A `0x0072df60` nem vtábla.
- A `[0xc4055c]` nem import-név nélküli: `KERNEL32` `EnterCriticalSection`.
- A `left` nem -S: a `left` +S (ugyanígy a 38.2.23 L1 pontja).
- A kártya-elrendezés nem dátumsor-alapú a `t_i = i·S + O` képlet szerint: i szerint lineáris.
- A `0x009a51b0` nem sima időolvasó: a visszatérése (`QPC` - *arg) / `QPF`, az argumentum a kivonandó kezdőidő.
- A `0x007fc010` nem ír P+0x30-ra és P+0x50..0x7c-re.
- A `0x008001c0` nem ír P-mezőt.

**Következő Ghidra-címek**

- `Ghidra-kör kell: [P+0x30] (S, P = OneUp+0x2f8) írói, teljes .text pásztázás `paszta.py`-val [blokkolt]`
- `Ghidra-kör kell: P+0x50..0x7c (görbe-vezérlőpontok) írói [blokkolt]`
- `Ghidra-kör kell: [OneUp+0x388] (A) és [OneUp+0x38c] írói, dátum vagy index [blokkolt]`
- `Ghidra-kör kell: 0x005568e0 (átlátszóság görbéje, z = (1/w - 1)/9) [blokkolt]`
- `Ghidra-kör kell: 0x00c29c6c azonosítása (exp-e; CRT-ugrók: 0x00c2a190, 0x00c2a48e, 0x00c2a661) [blokkolt]`
- `Ghidra-kör kell: 0x00802230 (a léptetés hatása) és [OneUp+0x3f4] / [OneUp+0x3f8] szerepe [blokkolt]`
- `Ghidra-kör kell: [OneUp+0x518], [OneUp+0x3c1], [OneUp+0x3fd], [OneUp+0x520] írói (a léptetés feltétele és az időzítő újraindítása) [blokkolt]`
- Ghidra-kör kell: X = `[OneUp+0x2e8]` osztálya és `vt(X)+0x18` célja (`startbutton`) [blokkolt]
- `Ghidra-kör kell: 0x009e5b20 nem nulla visszatérési ága (a kiértékelő egész értéket ad vissza) [blokkolt]`
- `Ghidra-kör kell: 0x007fbd90 (t* felhasználása) [blokkolt]`
- `Ghidra-kör kell: P+0x18 (v) további írói (húzás vagy sodródás kezelője) [blokkolt]`
- `Ghidra-kör kell: 0x008018a0 nézetfrissítése (0x004133e0, 0x004b0190, 0x0097caf0), 0x00604480 rendezés, 0x00801f50 rajzolási lépései [blokkolt]`
- `Mérés kell (futásidő, nem Ghidra): a 2,0 s-os léptetés és a 0,02 s-os eltolás valós időzítése az eredeti Picasán (Colab-felmérő) [blokkolt]`

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
| `ID_VIEW_SHOWHIDDEN` (`0x9c9e`) | `Preferences\ShowHidden`; **plusz jelszó-ajánló párbeszéd** + `DoNotConfirmHiddenPwd` | a kapcsoló megvan és őrződik (`controller.py:506`–`519`, `view/showHidden`); a menütétel pipás (`PicasaMenuBar.qml:679`) | **a jelszó-ajánlat hiányzik** — de mögötte nincs rétegünk: a gyűjtemény-jelszó nálunk tudatosan `placeholder` (`CollectionContextMenu.qml:12`, #416). ⇒ a #416-hoz tartozik, nem önálló jegy |
| `ID_VIEW_TIMELINE` (`0x9ccc`) | A 38.2.3 szerint külön, fekete `qshow` bemutatóablak, mappanév + hónap/év, két képhalom, pontozott ív, négy vezérlő, 1:1 időskála és fogantyú. A billentyűk, gombműveletek, animáció és kilépési cél továbbra is **NINCS MEG**. | A legacy `TimelineView.qml` év/hónap-rács megmarad; a Nézet-menü és `Ctrl+5` tiltott, eszköztárgomb nincs. | A teljes megvalósítás előtt a 38.2.2 és a 38.2.3 nyitott kérdéseit mérni kell. A jegy eszköztárgomb-kérésével szemben a csomagolt `thumbui.tre` az eredeti gombot `m_hidden`-ként jelöli; látható gombot ne vegyünk át bizonyíték nélkül. |
| `ID_WALLPAPER` (`0x9cd2`) | BMP a `Picasa\Backgrounds`-ba, `SPI_SETDESKWALLPAPER`, majd három registry-érték; **középre** | **placeholder** (`PicasaMenuBar.qml:1236`, „Set as Desktop Background…") — a kollázs-oldalon van egy `wallpaper` jelző (`collage_save.py:490`), de a menüparancs halott | **ÚJ JEGY** |

### Nyitott kérdések mérlege (38.)

```
Nyitott kérdések: 1 nyílt · 4 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a három parancsazonosító (38. bevezető); a `ShowHidden`
  tárolása és a jelszó-ajánló párbeszéd teljes szövegkészlete (38.1); az
  Időrend `oneup`/overlay belépési útja (38.2.1); a háttérkép teljes írási
  lánca, a stílusértékekkel együtt (38.3).
- **NYITVA (`#4443`; a 2. Ghidra-köteg állapota a 38.2.6-ban):** a 38.2.3 futó mérése lezárta a képernyő képi
  összetételét. Nyitott maradt a bemeneti mappák/albumok halmaza és sorrendje,
  a jobb halom és időskála jelentése, a gombok művelete, a billentyűk, az
  animáció és a kilépés célja. Ezekhez fókuszált, eredeti Picasa-futtatás kell.
- **BLOKKOLT:** hogy a jelszó-ajánlat a BE- vagy a KIkapcsoláskor jön-e.
  A `0x005cb990` két hívóhelye statikusan nem különbözteti meg őket.
  **Mi kell hozzá:** egy megfigyelés élő Picasán — a „Nézet ▸ Rejtett
  képek" be-, majd kikapcsolása, és melyiknél jön a párbeszéd. Ez a
  #416 megvalósításáig **nem blokkol semmit**, ezért nem kér külön
  `felhasználóra-vár` jegyet.

### Amit KIZÁRTAM

- **„A »Rejtett képek« puszta szűrő-kapcsoló"** — megdőlt: jelszó-ajánló
  párbeszéd tartozik hozzá, saját „ne kérdezd többet" kulccsal (38.1).
- **„A háttérkép az eredeti képfájlra mutat"** — megdőlt: a Picasa
  **BMP-t ír** a saját `Backgrounds` mappájába, és arra mutat (38.3).
- **„A háttérkép nyújtva/csempézve kerül ki"** — megdőlt: mindkét
  registry-érték `"0"` ⇒ **középre** (38.3).
- **„A `timelineRequested` jelzésünknek van aktív fogyasztója”** — a jelenlegi
  QML-ben nincs ilyen bekötés: a `PicasaMenuBar.qml` deklarálja és kibocsátja,
  de `Main.qml` nem kapcsol rá kezelőt; a Nézet-tétel és `Ctrl+5` tiltott.
  *(A forráskeresésben csak a deklaráció és kibocsátás található.)*

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
| a panel | önálló `printoptions` párbeszéd, 22 vezérlővel | **nincs** — a `PrintDialog.qml` (383 sor) elrendezést, nyomtatót, lapra-illesztést és tájolást kínál, keret/felirat vezérlőt **egyet sem** | ÚJ JEGY |
| felirat/szegély a nyomaton | négyféle forrás, háromféle hely, szegély-négyes | a `printing/` csomagban (`layout.py`, `contact_sheet.py`) **nincs** felirat- vagy szegély-kód | ua. |
| tárolás | 11 tartós `Preferences`-kulcs | — | QSettings, ugyanezzel a bontással |
| indexképnél | a beállítások **tiltva**, saját magyarázó szöveggel | nincs mit tiltani | a szöveg átvehető |
| a Beállítások „Nyomtatás" füle | **külön panel** | megvan (`OptionsTabPrinting.qml`, 59 sor) | ne keverjük össze a kettőt |

### Nyitott kérdések mérlege (39.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a tizenegy kulcs és a teljes írás→olvasás lánc (39.1); a
  vezérlő-készlet csoportosítása (39.2); az indexkép-tiltás és a szövege (39.3).
- **HATÓKÖRÖN KÍVÜL:** a numerikus **alapértékek** (bordersize, textsize,
  szín-értékek) kiolvasása a betöltő veremkezeléséből. A betűtípusé mérve
  (`Arial`); a többinél a stack-slotokból való következtetés a 34.1-ben
  leírt elcsúszás-kockázatot hozná, és a megvalósításhoz nem kell: a
  szerződés a **kulcsnevek és a jelentésük**.

### Amit KIZÁRTAM

- **„A keret/felirat beállítás a nyomtatási munkához tapad"** — megdőlt:
  tizenegy tartós `Preferences`-kulcs, amit a rajzoló (`0x00776180`) minden
  nyomtatáskor újraolvas (39.1).
- **„A Beállítások »Nyomtatás« füle ugyanez a panel"** — megdőlt: két külön
  panel; a fül a nyomtató-oldali beállításoké, a `printoptions` a **nyomat
  kinézetéé**.

### 39.3 A három gomb VISELKEDÉSE — és hogy a Mégse VISSZATÖLT (2026-09-02)

A kezelő `0x0085e800`; a három ág **külön** viselkedik:

| elem | magyar | mit tesz | cím |
|---|---|---|---|
| `printoptions/cancel` | „Mégse" | **visszatölti mind a tizenegy beállítást** (`0x0085f7a0`), majd frissíti a nyomtatási előnézetet (`0x00745980`) és bezárja a panelt | `0x0085e8a1`–`0x0085e8e5` |
| `printoptions/apply` | „Alkalmaz" | **csak frissíti az előnézetet** (`0x00745980`) — a panel **nyitva marad** | `0x0085e937`–`0x0085e95d` |
| `printoptions/ok` | „OK" | `0x00745f50`, majd **bezárja** a panelt (`[panel+0x258]->vt[0x14](0,0)`) | `0x0085e9ab`–`0x0085e9c9` |

⭐ **Ebből következik, hogyan működik a panel:** minden vezérlő **azonnal**
kiírja a maga `Preferences`-kulcsát, ahogy a felhasználó rákattint (a
kezelő minden ága `GetPreference` + `SetPreference` párral zárul). Az
„Alkalmaz" ezért **nem ment** — csak újrarajzoltatja az előnézetet; a
„Mégse" pedig **nem eldob**, hanem **visszaolvassa** a korábbi értékeket.

⇒ **Ha a felhasználó a panelt az ablak X-ével zárja be, a módosításai
BENT MARADNAK.** A visszavonás egyedül a „Mégse" gombhoz kötött.

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
| **DPI-őr** | legkisebb DPI kiírása + „kicsik" száma + „Ellenőrzés" felszólítás | **nincs semmi** — a `PrintDialog.qml` 383 sorában nincs felbontás-ellenőrzés | **ÚJ JEGY** |
| nyomatméret-gombok | 3,5×5 · 4×6 · 5×7 · 8×10 · tárca | a `PrintDialog` „egy kép / indexkép + oszlopszám" bontást ad, **méretgombok nincsenek** | ua. |
| a méret megjegyzése | `Preferences\PrintLastSize` | nincs | ua. |
| példányszám fotónként | +/− gombpár | nincs | ua. |
| előnézet-lapozás | prev/next + „%d / %d" | a párbeszédben nincs lapozó előnézet | ua. |
| nyomtató-őr | „A printer must be installed…" | a nyomtatólista üres marad, saját üzenet nélkül | kis kiegészítés |
| szegély/szöveg gomb | a `printoptions`-t nyitja | — | a #1780 párja |
| `froogle` | megszűnt szolgáltatás | — | **hatókörön kívül** |

### Nyitott kérdések mérlege (40.)

```
Nyitott kérdések: 0 nyílt · 4 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
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

### 43.4 Három elem téves riasztás volt

`recent_checkbox`, `recent_checkbox_label`, `autofill` — mindhárom megvan
(`quickTagsReserveRecentCheck` 84., felirat 86., `quickTagsAutoFillCheck`
92. sor). A felirat egy szóban tér el („Reserve **the** top two
buttons…"), ezért nem párosult gépi úton. Felülbírálva.

### Eredeti / nálunk / teendő

*Forrás: `quicktagconfig.tre:87` (`quicktagconfig/autofill`).*

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| gyorscímke-helyek | **10** (`edit_0..9`, `cmp eax, 0xa`) | **10** (`quickTagField0..9`) | ✅ **KÉSZ** (#1788) |
| „felső kettő a legutóbbiaknak" | `quicktags::enable_recents` | megvan | — |
| automatikus kitöltés | `quicktagconfig/autofill` | megvan | — |
| tárolás | `Preferences\quicktags::tag%d` | QSettings | — |
| gombok | **OK + Mégse** (elvethető) | **OK + Mégse** (elvethető) | ✅ **KÉSZ** (#1788) |
### Nyitott kérdések mérlege (43.)

```
Nyitott kérdések: 0 nyílt · 4 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a megfeleltetési fájl átvilágítása — a `collagepanel` volt
  az egyetlen elavult sor (43.1); a gyorscímke-helyek száma két
  független forrásból (leltár + ciklushatár, 43.2); a tárolási kulcsok
  (43.2); a párbeszéd gombkészletének eltérése (43.3).

### Amit KIZÁRTAM

- **„Több elavult megfeleltetési sor is van"** — megdőlt: gépi
  ellenőrzés mind a 74 soron, nulla találat (43.1).
- **„A `makemoviepanel` sora is elavult"** — megdőlt: a QML-fában nincs
  filmkészítő panel, a sor állítása helyes; az a hiány valódi (43.1).
- **„A gyorscímke-helyek száma nyolc"** — megdőlt: az eredetiben tíz
  (43.2). *(A mi nyolcunk saját döntés volt, de sehol nem volt kimondva,
  hogy eltérés.)*

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
| `printoptions` | nálunk **nincs** a panel | még nincs megvalósítva — ez hiány, nem eltérés | #1780 |
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

⚠️ **Ami nyitva marad:** hogy a `[obj+0x68]` alapnév pontosan mit
tartalmaz (a forrásvideó neve? időbélyeg?) — a mezőt a hívó tölti, és a
függvényben nincs rá literál. **Megszerzés:** a `0x00591dd0` hívójának
dekompilációja (az index `xrefs` táblája nem tartalmazza — a hívás
közvetett). **A megvalósítást nem blokkolja:** a mappa, a kiterjesztés és
a sorszámozás megvan.


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
| `searchoptions` csoport | hasonlóság, másodpéldány, gép | nincs | **külön kör** (jelzés, ld. 59.3) |
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

### 60.1 A csoport öt vezérlője

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
| másodpéldány-keresés | `dupesearch`, menüből is | **megvan** — teljes motor (`dedup/`: `phash.py`, `similar.py`, sávos jelöltszűrés) + `DedupDialog.qml` | — |
| **hasonlóság-keresés MINTAKÉPPEL** | `similarthumb` + `loadsim`/`clearsim`, saját adatbázissal és eredmény-albummal | **nincs** — a mi `similar.py`-unk **csoportokat** keres, nem „ehhez hasonlót" | **ÚJ JEGY** |
| az indexépítés jelzése | „Updating similarity database…" | — | ua. |
| eredmény-album | „Similarity Search Results" | — | ua. |
| **gép szerinti szűrés** | `digicam` | **nincs** | ua. |
| „mindet mutasd" | `viewallbutton` | a szűrők kikapcsolása | — |

⚠️ **A `dedup` és a hasonlóság-keresés NEM ugyanaz.** A miénk azt
kérdezi: *„mely képek duplikátumai egymásnak?"* — a Picasáé azt:
*„mely képek hasonlítanak ERRE?"* A motor (dHash + Hamming) közös lehet,
a felhasználói kérdés más.

### Nyitott kérdések mérlege (60.)

```
Nyitott kérdések: 0 nyílt · 3 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a csoport öt vezérlője (60.1); a hasonlósági adatbázis és
  az eredmény-album (60.2); a `dupesearch` második belépési pontja (60.3).
- **BLOKKOLT:** a hasonlósági adatbázis **helye és formátuma** (a
  `0x007e95f0` — az egyetlen hívó — sztringjei az indexben üresek).
  **Mi kell hozzá:** célzott dekompiláció. **A jegyet nem blokkolja:** a
  mi `phash`-motorunk adja a tartalmat, a tárolás a mi döntésünk.

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

### 64.3 Nálunk: a TÁROLÁS megvan, a FUNKCIÓ nincs

**Mérve — és ez a lényeg:** a `moviestart` és `movieend` tokent a
rendszerünk **ismeri és megőrzi**:

| hol | mit tesz |
|---|---|
| `ini/filter_registry.py:148–149` | a két token a regiszterben |
| `render/registry_data.py:512–513` | „Start Point" / „End Point" néven |
| `render/chain.py:220` | a `_NOOP_MARKERS` közt — **átmegy a láncon, nem vész el** |

⇒ **A round-trip biztonságos**: ha egy Picasából örökölt videón van
vágás, azt nem töröljük ki. **Beállítani viszont nem tudjuk** — a
QML-fában nincs `setin`/`setout`/`trim` vezérlő, és képkocka-mentés sincs.

*(Ez a jó fajta állapot: a formátum-kompatibilitás megelőzte a
funkciót, tehát a funkció pótlása nem jár adatvesztés-kockázattal.)*

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
- **„A `moviestart`/`movieend` tokent nem ismerjük"** — megdőlt: a
  regiszterben és a render-láncban is ott van, megőrizve (64.3).

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
