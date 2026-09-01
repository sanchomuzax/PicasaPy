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
csomópontokat is kezeli — vagyis a **teljes képernyős** útra vált át. Van
saját gomb-belépési pontja is: **`thumbui/timelinebutton`**
(`0x005d9cc0`).

⇒ **Az Idővonal nem nézet-kapcsoló, hanem egy előkészítő lépéssel induló,
teljes képernyős bemutató-mód** („Preparing timeline…" folyamatjelzővel).

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
| `ID_VIEW_TIMELINE` (`0x9ccc`) | teljes képernyős bemutató-mód, „Preparing timeline…" előkészítéssel; gomb-belépési pont is (`thumbui/timelinebutton`) | menütétel + **valódi bekötés**: `Main.qml:823` → `toggleTimeline()` → `timelineController.reload()` + `timelineOpen` (`Main.qml:611`) | a **gomb**-belépési pont és az előkészítés-jelző hiányzik (kis jegy, ha kell) |
| `ID_WALLPAPER` (`0x9cd2`) | BMP a `Picasa\Backgrounds`-ba, `SPI_SETDESKWALLPAPER`, majd három registry-érték; **középre** | **placeholder** (`PicasaMenuBar.qml:1236`, „Set as Desktop Background…") — a kollázs-oldalon van egy `wallpaper` jelző (`collage_save.py:490`), de a menüparancs halott | **ÚJ JEGY** |

### Nyitott kérdések mérlege (38.)

```
Nyitott kérdések: 0 nyílt · 4 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a három parancsazonosító (38. bevezető); a `ShowHidden`
  tárolása és a jelszó-ajánló párbeszéd teljes szövegkészlete (38.1); az
  Idővonal bemutató-mód jellege és belépési pontjai (38.2); a háttérkép
  teljes írási lánca, a stílusértékekkel együtt (38.3).
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
- **„A `timelineRequested` jelzésünknek nincs fogyasztója"** — a mérés
  megcáfolta: `Main.qml:823` bekötve. *(Ez a kör saját, ellenőrzés előtti
  feltevése volt — a grep döntötte el, nem a benyomás.)*

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

- **Példányszám fotónként** (`copieslabel`): `addprintsbutton` /
  `subprintsbutton` gombpár — buboréksúgójuk *„Add another copy of each
  Photo to be printed"* / *„Subtract a copy…"*. ⇒ **képenkénti**
  példányszám, nem összesített.
- **Nyomtató-őr** (`0x00744a00`): `IDS_MUST_INSTALL_PRINTER` —
  *„A printer must be installed in order to print."*
- **Előnézet-lapozás**: `prevbutton` / `nextbutton` + `previewnumber`
  (`%d of %d`).
- **Átjáró a 39. tételhez**: `captionoptionsbutton`, buboréksúgó
  *„Configure borders and text for Photos to be printed"*, felirata
  **„Szegély- és szövegopciók"** ⇒ **ez nyitja a `printoptions` panelt.**

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

### 43.2 ⭐ A gyorscímke-beállító TÍZ helyet ad, nálunk NYOLC van

A `quicktagconfig` panel elemleltára `edit_0` … **`edit_9`** — tíz
szövegmező. A binárisban a kezelő (`0x0083ea00`, 2063 b) ciklushatára
ezt megerősíti:

```
0x0083efa2  cmp eax, 0xa      ; 10 hely
```

**Nálunk nyolc van.** A `QuickTagsConfigDialog.qml` (98 sor) a saját
kommentjében ki is mondja: *„a 8 szövegmező közös viselkedése — EXPLICIT
8 példány (nem Repeater)"*, és a mezők `quickTagField0` … `quickTagField7`
néven élnek.

Tárolás (`0x0063a5e0`, `0x0083ea00`): a `Preferences` ág
**`quicktags::tag%d`** kulcsai a címkék, a **`quicktags::enable_recents`**
a „felső két gomb lefoglalása" kapcsoló. A gyorscímke-gombok a
felületen a `quicktag_%d` / `%s/quicktag_%1d` csomópontnevek alatt élnek
(`0x0063c120`, `0x0063c7d0`).

### 43.3 A párbeszéd gombjai: OK / Mégse — nálunk csak „Bezárás"

Az eredeti `quicktagconfig/ok` és `quicktagconfig/cancel` vezérlőkkel
zár, tehát a **Mégse eldobja** a szerkesztést. Nálunk
`standardButtons: Dialog.Close` (17. sor) — **egyetlen** gomb, vagyis a
változtatás azonnal érvényes, és nincs elvetés.

*(Ez nem feltétlenül hiba: a mi párbeszédünk azonnal ír. De **eltérés**,
és eddig sehol nem volt kimondva.)*

### 43.4 Három elem téves riasztás volt

`recent_checkbox`, `recent_checkbox_label`, `autofill` — mindhárom megvan
(`quickTagsReserveRecentCheck` 84., felirat 86., `quickTagsAutoFillCheck`
92. sor). A felirat egy szóban tér el („Reserve **the** top two
buttons…"), ezért nem párosult gépi úton. Felülbírálva.

### Eredeti / nálunk / teendő

| | eredeti (mérve) | nálunk (**mérve**) | teendő |
|---|---|---|---|
| gyorscímke-helyek | **10** (`edit_0..9`, `cmp eax, 0xa`) | **8** (`quickTagField0..7`) | **ÚJ JEGY** |
| „felső kettő a legutóbbiaknak" | `quicktags::enable_recents` | megvan | — |
| automatikus kitöltés | `quicktagconfig/autofill` | megvan | — |
| tárolás | `Preferences\quicktags::tag%d` | QSettings | — |
| gombok | **OK + Mégse** (elvethető) | csak **Bezárás** (azonnal ír) | dokumentált eltérés vagy átvétel |

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

`leftlist` („Rendelkezésre álló gombok:") ↔ `rightlist` („Jelenlegi
gombok:"), közte **„Add >>"** és **„<< Remove"**; a jobb listán
**„Move Up" / „Move Down"** sorrendezés; alul **„Reset to Defaults"**,
és **OK / Mégse / Kész** hármas.

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

### 47.2 ⛔ NÁLUNK NÉMA BEÁLLÍTÁS: „Let me choose each time"

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
- **„A `mail/useDefaultClient` beállításunk hat a küldésre"** — megdőlt:
  a `sendRows()` nem olvassa (47.2).

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
| `newfolder` | Fájl menü „Áthelyezés új mappába…" |

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

⇒ Ez **önálló, felhasználónak látszó funkció**, nem elhelyezés-kérdés.

### 51.4 A többi valódi hiány, besorolva

| elem | mi ez | hova tartozik |
|---|---|---|
| `webcambutton` | webkamerás felvétel | **#853** (a négy hiányzó eszköztár-vezérlő egyike) |
| `visitweb` („Internetes nézet") · `backup` · `cdmode` („Ajándék CD") | eszköztár-gombok | `visitweb` **hatókörön kívül**; `backup` → #440; `cdmode` → #32 |
| `single_action_*` hármas | a „Get more" mód üzenetsávja: *„Jelölje ki… majd a »Vissza« gombra kattintva térjen vissza a projekthez"* | a kollázs/film **klip-gyűjtő módja** — a projektpanelekhez tartozik |
| `lightbox_esolo_button` / `_text` | *„Nincs találat ebben az albumban"* + **„Keresés mindenhol"** gomb | keresési üres-állapot — **kis jegy értéke lehet** |
| `flatview` · `folderview` · `folderviewpopup` | a bal hasáb nézetváltói | a 36./4c körökben feltárva; **#1407**, **#853** |

### Eredeti / nálunk / teendő

| | eredeti | nálunk (**mérve**) | teendő |
|---|---|---|---|
| rács-nagyító | húzásra nagyít | **nincs** | **ÚJ JEGY** |
| kis/nagy indexkép, forgatás, tálca, új album/mappa | eszköztáron | **megvan**, máshol | — (elhelyezés: #853) |
| négy fiók-kapcsoló | eszköztáron | menüben megvan | #853 + #1773 |
| webkamera | eszköztárgomb | nincs | #853 |
| „Nincs találat… / Keresés mindenhol" | üres-állapot | nem mérve | megfontolandó |

### Nyitott kérdések mérlege (51.)

```
Nyitott kérdések: 0 nyílt · 2 lezárva · 1 blokkolt · 1 hatókörön kívül · 0 csak-nyitva
```

- **LEZÁRVA:** a hiányok fő mintája (elhelyezés, nem funkció — 51.1–51.2);
  a nagyító léte és a mi oldalunk hiánya (51.3).
- **BLOKKOLT:** a nagyító **viselkedési részletei** (nagyítás mértéke,
  követi-e az egeret, mekkora a `loupe_sm`). A sztringtár erről nem ad
  többet, a kezelő (`0x0077be10`) két csomópontnévnél egyebet nem
  hivatkozik. **Mi kell hozzá:** célzott dekompiláció vagy egy
  képernyőmentés működés közben. **A jegyet nem blokkolja**: a funkció
  léte és belépési pontja megvan.
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
| `croptext` | „Choose a size below, then drag on the picture to…" (56. sor) |
| `crop_aspect_menu` | `cropAspectCombo` (81.) + `cropAspectList` (109.) |
| `crop_delete_custom` | `cropAspectDelete<i>` (164.), **megerősítéssel** („Delete this custom aspect ratio?", 186.) |
| `cropsug_preview1/2/3` | `cropSuggestion0/1/2` (270–272.), a „Suggested crops" sorban (237.) |

| eredeti | nálunk (retus / vörösszem) |
|---|---|
| `retouch_label` · `retouchtext` | `EditorRetouchPanel.qml:47` · `:56` |
| `redeye_label` · `redeyetext` | `EditorRedeyePanel.qml:55` · `:64` |

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
| `faces_button` | `facesToggleButton` + `facesVisible` | `PhotoViewer.qml:1490`, `:165–166` |
| `filter_name` | `effectParamTitle` (az aktív effekt neve) | `EditorParamPanel.qml:191` |

Tábla: párosítva 153 → **157**, hiányzik 382 → **380**, bizonytalan
154 → **152**.

*(Az `editcircle1`, `editcircle1_well`, `editcontrol_well`,
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

## 59. tétel — a keresősáv HÁROM hiányzó szűrője (2026-09-01)

*Huszonkettedik kör az UI-lefedettségi axisról (#1778). Panel:
`searchcontainer` (4 hiány) — a keresősáv és a szűrőgombjai.*

### 59.1 Az eredeti szűrő-készlet: hat gomb

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
