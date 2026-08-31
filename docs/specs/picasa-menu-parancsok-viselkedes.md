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

## 3. „Dátum és idő beállítása" — KÉT mód, és NEM fájlidő

`offsettime.fen`: bélyegkép-előnézet · „Current photo date" (dátum+idő) ·
„New photo date" (dátum+idő) · **rádiócsoport**:

- `relative` — *Adjust all photo dates by the amount* (**eltolás**)
- `absolute` — *Set all photos to the same date and time* (**abszolút**)

Több képre megy (`OffsetPhotoDate:Title` = „Fotó dátumának módosítása -
%d elem."), **háttérszálon** (`AdjustTimeThread::SettingDates`).

⛔ **A kezelői (`0x0077c7c0`, `0x0077cfd0`) NINCSENEK a `SetFileTime` nyolc
hívója között** ⇒ **a „fotó dátuma" nem a fájlrendszer ideje.**

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
**Indexkép-méret három:** `ID_VIEW_SMALLTHUMBNAILS` · `ID_VIEW_LARGETHUMBNAILS`
· `ID_VIEW_SMALL`.

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

## Ami még hátra van (20 tétel)

**Nézet (5):** `ID_VIEW_PICTURE` · `ID_VIEW_LIGHTBOXVIEW` · `ID_VIEW_EDIT` ·
`ID_VIEW_SEARCHVIEW` · `ID_VIEW_AUTO`
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

**„Kis képek" (`ID_VIEW_SMALL`):** **láthatósági szűrő**, nem méret. A
menüépítőben a „Keresési opciók" és a „Rejtett képek" között ül; a felirata
bekapcsolva **`IDS_INCLUDING_SMALL`** = *„A kisebb képeket is"*, a küszöb
kulcsa **`minsize`**. A Picasa alapból elrejti a küszöb alatti képeket.

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

### 20. A hat színcímke — `ID_S_RED` · `ID_S_ORANGE` · `ID_S_YELLOW` · `ID_S_GREEN` · `ID_S_BLUE` · `ID_S_PURPLE`

Névtér: **`eMenuTools`** (az **Eszközök** menü, nem a Nézet).

Mind a hat ugyanazt hívja (`0x005ccc41`–`0x005ccca2`), más tokennel:
`mov edx, "color:<szín>"; call 0x0065b7b0`.

A `0x0065b7b0` (131 b) **hat lépése**:

1. `ebx = [this+0xf48]` — a **keresőmező** ablakkezelője (`0x0065b7b4`)
2–3. a token **beírása a keresőmezőbe** (`0x0065b7ea`)
4. a `searchcontainer/searchbutton` megjelenítése
5. `SendMessage(mező, 0xB1 = EM_SETSEL, 0xFFFF, 0xFFFF)` — kurzor a végére (`0x0065b81d`)
6. `0x0065b840(this,0,0,1)` — a lista újraépítése

⇒ **A menüpont beírja a tokent a keresőmezőbe és elsüti a keresést** —
nincs külön szűrő-modell. Van **hetedik** kezelő (`color:black`,
`0x005ccca7`), de **nincs hozzá menüfelirat**. Jegy: **#1399**.

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
képpel?" (kérdés ⇒ igen/nem párbeszéd). Konstans: `0xc7dcc8` = **0,3**.
Jegy: **#1401**.

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

### `ID_BURNCD` — HATÓKÖRÖN KÍVÜL

A `0x0066fae0` (439 b) **négy fájlt** másol a lemezre: `PicasaCD.exe`
(windowsos önindító nézőprogram), `Picasa CD Slideshow.app` (macOS), és a
nézőprogram felületleírói (`cdgo.ui`, `cdgo.tre`).

⇒ Az Ajándék CD **nem fényképexport**, hanem egy **szállított
nézőprogram** lemezre égetése. Linuxon nem átvehető. Jegy: **#32**.

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
„Fájlok másodpéldányainak **megjelenítése**". Nálunk `DedupDialog`
nyílik. Jegy: **#1398**.

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
| 18 | `ID_ALBUM_FILTERFACES` | &Add name tags | — | ❌ `placeholder: true` (`:247`) — #26 |

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

**Nálunk (mérve):** a fotó-szintű `hidden` oszlop megvan
(`index/schema.py:225`), a `showHidden` beállítás is
(`app/controller.py:500`), sőt a lemezes elrejtés kérdése is
(`photo_ops_controller.py:105`, #459 — „Fájlok elrejtése"). **Mappa-szintű
elrejtés viszont sehol nincs** (`grep hide_folder|folder_hidden` a `src/`-ben:
üres), és a menütétel néma.

*Bizonyítottsági fok: **megerősített** a 18 tétel, a feliratok és a három
elrejtés-réteg. **Nincs mérve**, hogy a mappa elrejtése a `.picasa.ini`-be, az
adatbázisba vagy mindkettőbe ír-e — ehhez a `0x0040cd10` környékének
diszasszemblálása kell.*

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

### 34.2 A forgatás — és a `rotate=` bit jelentése (#1162 LEZÁRVA)

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

⇒ **#1162 kérdésének válasza: a `rotate` bit és a menü UGYANAZ a
mechanizmus** — a `rotate=rotate(N)` negyedfordulatot tárol, a szabad
forgatás nem ebbe a kulcsba való. A mi oldalunkon
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
| Reset Faces | sima = kijelölés (nincs kérdés); Ctrl/Shift = könyvtárszintű FIGYELEM-párbeszéd | mindig kérdez, ResetAllFaces-szöveg (#422 SAJÁT döntés) | a három ág megvalósítása vagy tudatos eltérés rögzítése |

### Nyitott kérdések mérlege (34.)

```
Nyitott kérdések: 0 nyílt · 4 lezárva · 0 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** #1162 (a rotate bit = negyedfordulat-tároló, a menüvel
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
| mentés-készletek könyve | **`backup.xml`** a Picasa adatmappájában (`0x00581920`, `0x0066f2b0` — ugyanaz a kezelő, mint a `contacts.xml`) |
| a mentés-motor | a **`il_BurnPanel`** (0x67xxxx tartomány): meghajtó-felderítés („Drive Type is %s on %s", `CD-R`/`DVD-R`… debug-sztringek, „No recordable drives detected") és a `backup.xml` kezelője (`0x0066f470`, nyolc hívóval) — a klasszikus Picasa-mentés **CD/DVD-re írás** |
| képenkénti könyvelés | `backuphash` ini-kulcs: a korpuszban **14 700 sor** (pl. `backuphash=50247`); a `-backuphash` alak a kulcs **levételét** jelzi — a #440-es „újrafuttatható, inkrementális készletek" pontosan ezen a két helyen könyvel |
| társprogram-promó | `0x0040d160`: `Software\Google\Google Photos Backup\Preferences` (`welcome_seen`, `SkipABPromo`, `LastABPromo`, `ABRepromptDays`) + `https://photos.google.com/apps` — a Picasa 3.9 végén a Google Fotók-Backup alkalmazást kínálta |

Jegy: **#440**. *(A `thumbui/backup` névparancs és a BurnPanel közötti
azonnali launcher-lépés a sztring-matcher esethatáránál nem
egyértelműen követhető — a motor és az állapothordozók viszont megvannak.)*

### Eredeti / nálunk / teendő — az öt parancsra

| parancs | nálunk (mérve) | teendő |
|---|---|---|
| Poszter készítése | **placeholder** a Létrehozás menüben (`PicasaMenuBar.qml:1210`) | #601 folytatja; új adat: papírméret-lista nyelvi feltétellel + `paper` megőrzés |
| Hozzáadás a képernyővédőhöz | **placeholder** (`:1218`) | #453/#32; a `saverlist.txt` + telepítés-ellenőrzés mintája rögzítve |
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
  megvalósítása; a `desk.cpl`-alapú képernyővédő-telepítés átvétele.

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
| **menüsáv ▸ Nézet** | `0x00559150` (menüsáv-építő) | `eMenuView::ID_VIEWBYDATE/RECENT/NAME/SIZE` | a négy sztring a menüsáv-építőben; a pipázója `0x00574b70`, ami **`GetSubMenu(GetMenu(hwnd), 2)`**-t vesz (`0x00574b81`–`0x00574b8a`) = a **harmadik** felső menü |
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
