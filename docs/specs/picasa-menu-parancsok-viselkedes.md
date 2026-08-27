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
