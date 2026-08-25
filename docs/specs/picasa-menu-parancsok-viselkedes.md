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

**`ID_VIEW_AUTO`**: **nem sikerült besorolni** — nem tagja a tizenegyes
megjelenítési-mód tömbnek, és nem illik az „Indexkép felirata" négyeséhez.
Nyitva marad.

---

## A 11–15. adag leletei (2026-08-25, este)

**`ID_VIEW_AUTO`** a „Megjelenítési mód" almenü **első** tétele (a
menüépítőben közvetlenül a 24 bites előtt) ⇒ a menüben **12** tétel, a
kezelő kizáró-tömbjében **11**; az „Automatikus" nincs a tömbben.

**A parancsazonosító-térkép MÁSODSZOR is megbukott.** A rekord felirata a
saját kulcsától jön, az azonosítója a **következő** kulcs pushja után —
ebből egy „az előző kulcsé" szabály következne, de az független horgonyon
**1/4**-et adott. **A leképezés szabálytalan; ne legyen harmadik
próbálkozás.**

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
