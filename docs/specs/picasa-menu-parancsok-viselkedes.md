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
