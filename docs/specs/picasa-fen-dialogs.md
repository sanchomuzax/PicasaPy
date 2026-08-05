# Picasa 3.9 `.fen` dialógus-definíciók — teljes dokumentáció

**Forrás:** eredeti Picasa 3.9 (Windows, 2015) programmappa, `runtime/*.fen`
(46 fájl) és néhány kapcsolódó `runtime/*.html` fájl.

**Cél:** ez a dokumentum a Picasa saját, egyedi deklaratív UI-formátumát
(„FEN" — feltehetően *Form/Frame ENgine* vagy hasonló belső rövidítés, a
kiterjesztésen kívül erre utaló string a fájlokban nincs) írja le annyira
részletesen, hogy a PicasaPy fejlesztője az eredeti fájlok nélkül is
újraépíthesse az egyes dialógusokat (PySide6/QML formában), és megértse a
formátum általános szabályait.

A FEN egy egyszerű, kézzel írható **XML-dialektus**: minden fájl egyetlen
`<window>` gyökérelemből és beágyazott layout-/widget-elemekből áll. Nincs
XML deklaráció, nincs namespace, nincs séma — a fájlok kézzel szerkesztett,
kissé inkonzisztens (hol `title=`, hol nincs `title`, hol `os="win"` felbontás
stb.) natív erőforrás-fájlok, amiket a Picasa saját UI-frameworkje tölt be
futásidőben és fordít le natív Win32/Cocoa widgetekre.

---

## 1. Áttekintés — a 46 `.fen` fájl

Mind a 46 fájl a `runtime/` könyvtár gyökerében található (nincs `.fen` fájl
máshol a programfában). Az alábbi táblázat gyors áttekintést ad: mire való a
dialógus, és melyik PicasaPy fázishoz kapcsolódik.

| Fájl | Dialógus célja | PicasaPy fázis |
|---|---|---|
| `about.fen` | Névjegy ablak (verzió, jogi közlemények, licencek) | V1 |
| `addtogroup.fen` | Kapcsolat hozzáadása csoport(ok)hoz (Barátok/Család/Munkatársak) — **nem használt/legacy** minta a végleges kontaktkezelőhöz képest | — (legacy, ld. 5. fejezet) |
| `album.fen` | Album tulajdonságai: név, dátum, zene, helyszín, leírás | V1 |
| `auto_backup_prompt.fen` | „Automatikus Google Fotók mentés" felajánló felugró ablak | V3 (opcionális, felhő-funkció) |
| `autocomplete_errors.fen` | Vágólapról beillesztett kontaktnevek hibalistája | V3 |
| `cdchoose.fen` | CD/DVD írómeghajtó választása (több meghajtó esetén) | — (nem releváns, optikai lemez archiválás) |
| `compacting.fen` | Adatbázis-tömörítés folyamatjelző | V1 (SQLite VACUUM analógja) |
| `confirm.fen` | Általános Igen/Nem/Mégse megerősítő ablak (session-szintű "ne kérdezd újra") | V1 (alapinfrastruktúra) |
| `confirmsync.fen` | Album webes szinkronizálásának megerősítése (PicasaWeb) | V3 (felhő) |
| `contactmgr.fen` | **Kontaktkezelő** (People) — arcok/személyek adminisztrációja | V3 (arcok) |
| `customaspectratio.fen` | Egyéni képarány hozzáadása vágáshoz | V2 (szerkesztő) |
| `eula.fen` | Licencfeltételek elfogadása (első indításkor) | V1 (telepítő/első indítás) |
| `export.fen` | **Exportálás mappába** | V1 |
| `genericlogin.fen` | Általános Google-bejelentkezés | V3 (felhő) |
| `gpuploader_*.fen` (18 fájl) | A különálló „Google Photos Backup" segédalkalmazás (más `.exe`, nem a fő Picasa) dialógusai | — (külön termék, nem PicasaPy hatókör, ld. 6. fejezet) |
| `imageproperties.fen` | Kép tulajdonságai (EXIF-szerű lista, fájlnév, méret, dátum) | V1 |
| `importweb.fen` | Webalbumok importálása a számítógépre | V3 (felhő) |
| `input.fen` | Generikus egysoros szöveg-/jelszóbekérő ablak (belső segédeszköz) | V1 (alapinfrastruktúra) |
| `move_database.fen` | **Adatbázis áthelyezése** másik mappába | V1 |
| `moving_database.fen` | Adatbázis-áthelyezés folyamatjelzője | V1 |
| `newbackupset.fen` | Új CD/DVD vagy lemez-lemez biztonsági mentési készlet létrehozása | — (nem releváns, optikai/lemez archiválás) |
| `offsettime.fen` | Fényképek dátumának/idejének eltolása, tömeges korrekció | V1/V2 |
| `options.fen` | **Beállítások** (fő preferencia-dialógus, 9 fül) | V1 (részben), V2/V3 (fülönként) |
| `orderprintsprefs.fen` | Bejelentkezés fotónyomtatási szolgáltatáshoz | — (nem releváns, nyomtatásrendelés) |
| `poster.fen` | Poszter nyomtatási beállítások (nagyítás, papírméret) | — (nyomtatás, alacsony prioritás) |
| `quota.fen` | Alacsony tárhely figyelmeztetés (PicasaWeb kvóta) | V3 (felhő) |
| `refresh_contacts_progress.fen` | Online kontaktok frissítésének folyamatjelzője | V3 (arcok) |
| `rename.fen` | **Fájlok átnevezése** (tömeges, sablon alapján) | V1 |
| `reviewprint.fen` | Nyomtatás előtti felülvizsgálat (kis felbontású képek szűrése) | — (nyomtatás) |
| `webexport.fen` | Exportálás HTML weboldalként (sablon-alapú) | V2/V3 (alacsony prioritás) |
| `write_all_facetags.fen` | **Arc-címkék kiírása** a fájlokba (XMP/IPTC) | V3 (arcok) |
| `youtube.fen` | Videó feltöltése YouTube-ra | — (nem releváns) |

A `gpuploader_*` csoport (18 fájl) egy **különálló, önálló futtatható**
(„Google Photos Backup", korábban „Google+ Photos Uploader") UI-jai — ezek
technikailag ugyanabban a `runtime/` mappában vannak, de nem a fő Picasa.exe
dialógusai. Külön alfejezetben (6.) foglaltam össze, mert a FEN-formátum
szempontjából tanulságosak (pl. `mac_fontsize`/`win_fontsize` platform-specifikus
attribútumok, `hidden`/`visible` rejtett gombok), de PicasaPy szempontjából
csak érdekesség.

Összesen **46 `.fen` fájl** lett feldolgozva (100%).

---

## 2. A FEN formátum — elem- és attribútumreferencia

### 2.1 Alapszerkezet

Minden fájl egyetlen `<window>` gyökérelemmel kezdődik, amely tetszőleges
mélységű layout-csoportokat (`<group>`, `<labelgroup>`, `<buttongroup>`,
`<radiogroup>`, `<tabs>`/`<tab>`) és „levél" widgeteket tartalmaz. Nincs
explicit zárás-önzáró következetesség — önzáró elemek `<label .../>` formában,
szülő elemek `<group>...</group>` formában szerepelnek.

Illusztratív, teljes példa (`customaspectratio.fen`, a legkompaktabb, minden
alapvető mintát bemutató fájl):

```xml
<window title="Add Custom Aspect Ratio" width="fit">
  <group layout="column">
    <labelgroup title="Dimensions:" width="fill">
      <group layout="row">
        <edit width="3em" name="width"/>
        <label title="  x  "/>
        <edit width="3em" name="height"/>
      </group>
    </labelgroup>
    <labelgroup title="Name:" width="fill">
      <edit width="13em" name="title"/>
    </labelgroup>
    <labelgroup title="Example:" width="fill">
      <label title="   4 x 6   Small print"/>
    </labelgroup>
  </group>
  <buttongroup width="fill">
    <button title="OK" type="accept" name="ok"/>
    <button title="Cancel" type="cancel" name="cancel"/>
  </buttongroup>
</window>
```

### 2.2 Elemreferencia

| Elem | Szerep | Fontosabb megfigyelt attribútumok |
|---|---|---|
| `<window>` | Gyökér, a teljes dialógus | `title`, `mac_title`/`win_title` (platformfüggő cím), `width`/`height` (`fit`, `fill`, `Nem`, `N%`, `winN` px), `name`, `focus` (melyik widgetre kerüljön a fókusz induláskor, pl. `focus="name"`), `layout` (`row`/`column`, ritkán a windowon is), `os` (nincs rá példa a window szinten, csak beágyazva) |
| `<group>` | Generikus konténer/layout-doboz | `layout` (`row` — alapértelmezett vízszintes, `column` — függőleges), `width`/`height` (`fit`, `fill`, `Nem`, konkrét px), `align` (`start`/`center`/`end`/`top`), `name` (script-hivatkozáshoz), `os` (`win`/`mac` — feltételes megjelenítés) |
| `<labelgroup>` | Címkével ellátott mezőcsoport (a klasszikus "Label: [mező]" sor/blokk) | `title` (a felirat szövege, kettősponttal), `width`, `name` |
| `<buttongroup>` | Gombsor (jellemzően a dialógus alján) | `align` (`end` = jobbra, `center`), `default` (`accept`/`cancel` — melyik gomb reagáljon Enterre), `width`, `name` |
| `<radiogroup>` | Rádiógombok logikai csoportja (kizárólagos választás) | `name` (a kiválasztott index/érték kulcsa), `layout`, `align`, `width` |
| `<tabs>` / `<tab>` | Fül (tab) konténer és egyes fülek | `<tabs name="...">`; `<tab title="..." name="...">` |
| `<label>` | Statikus szöveg | `title`, `text-align` (`left`/`center`/`right`), `align` (a konténeren belüli pozíció), `width`/`height` (`fit`, `fill`, `Nli` = N sor magas), `size` (`small`), `fontweight` (`bold`), `win_fontsize`/`mac_fontsize` (platformfüggő betűméret), `name` |
| `<edit>` | Egysoros vagy többsoros szövegbeviteli mező | `name`, `width`, `height` (`Nli` = N sor → többsoros), `filter` (`filename`, `digits` — bemenet-validáció), `title` (kezdőérték), `scroll` (`v`) |
| `<password>` | Jelszómező (elrejtett bevitel) | `name`, `width` |
| `<check>` | Jelölőnégyzet | `title`, `name`, `width`, `os` |
| `<radio>` | Egy rádiógomb-opció (radiogroup-on belül) | `title`, `name`, `width` |
| `<button>` | Nyomógomb | `title`, `type` (`accept`/`cancel`/`other` — szemantikus szerep, l. 2.3), `name`, `align`, `hidden`/`visible` (rejtett, de funkcionális gomb, pl. Escape-hez), `mac_minsize` (`"szélesség,magasság"` px Mac-en) |
| `<popup>` | Legördülő lista (combobox) | `name`, `width`, gyerekelemként `<item title="..."/>` bejegyzések |
| `<item>` | Egy `<popup>` opció | `title` |
| `<list>` | Táblázat/lista nézet | `name`, `width`, `height` (`Nli`), `max-height`/`max-width` (`fill`), `scroll` (`v`, `h`, `hv`), `header` (`show`/`hide`), `checkboxes` (`true` — jelölőnégyzetes lista), gyerekelemként `<column>` |
| `<column>` | Egy oszlop egy `<list>`-en belül | `title`, `width` (`Nem`, `fill`, `0` = auto-méretezés), `type` (`check`), `name` |
| `<slider>` | Csúszka | `min`, `max`, `ticks` (osztásjelek száma), `width`, `name` |
| `<progress>` | Folyamatjelző sáv | `name` |
| `<separator>` | Vízszintes elválasztó vonal | `width` |
| `<spacer>` | Üres kitöltő/térköz | `amount` (`1em`, `indent`, `0`, `Nli`), `height`/`width` (`fill` — nyújtható térköz), `mac_amount`/`win_amount` (platformfüggő méret) |
| `<image>` | Statikus kép/ikon | `name`, `width`, `height`, `align`, `mac_width`/`win_width` stb. |
| `<appicon>` | Az alkalmazás ikonja (rendszer-specifikus, automatikus) | `align` |
| `<link>` | Kattintható hivatkozás (böngészőben nyílik meg) | `title`, `url`, `name`, `align`, `text-align`, `size` |
| `<browse>` | Fájl-/mappa-tallózó gomb + útvonal | `title`, `name`, `prompt` (tallózó ablak felirata), `win_filter`/`mac_filter` (fájltípus-szűrő, `"Leírás|*.ext1;*.ext2"` szintaxis) |
| `<pathbox>` | Csak megjelenítésre szolgáló útvonal-mező (nem szerkeszthető szöveg, elé/mögé vágható) | `name`, `title`, `width` |
| `<date>` | Dátumválasztó widget | `name` |
| `<time>` | Időválasztó widget | `name` |
| `<printpreview>` | Kép-előnézet/miniatűr terület | `name`, `width`, `height`, `align` |
| `<bind>` | **Deklaratív adatkötés/feltétel** — másik widget állapotától teszi függővé egy attribútumot | `source` (a figyelt widget `name`-je), `attr` (melyik attribútumot módosítja: `enabled`, `title`, `value`), `format` (`"%s pixels"` string-sablon), `list` (érték-tábla, pipe-szeparált: `"320|480|640|800|1024"` — pl. csúszka pozíció → konkrét szám leképezés), `transform` (`not` — logikai tagadás) |
| `<multi>` | Több gyerek közül egyet jelenít meg a `<bind>` `source` értéke alapján (index-váltás, pl. popup-index → leíró szöveg/slider váltás) | gyerekként `<bind>` + a választható elemek listája |

### 2.3 Kiemelt / szokatlan attribútumok és minták

- **`type="accept"` / `type="cancel"` / `type="other"`** a `<button>`-ön: ez a
  Picasa szemantikus gomb-szerepe — `accept` az alapértelmezett/Enter-gomb
  (zöld pipa-jellegű, "OK"/"Igen"/"Mentés" stb.), `cancel` az Escape-re is
  reagáló gomb, `other` egy harmadik, semleges lehetőség (pl. `confirm.fen`
  "No" gombja `other` típusú, mert nem zárja be feltétlenül az ablakot úgy,
  mint a Cancel). Ez közvetlenül megfeleltethető a Qt `QDialogButtonBox`
  `AcceptRole`/`RejectRole`/`ActionRole` szerepeinek.
- **`os="win"` / `os="mac"`**: feltételes megjelenítés platform szerint —
  ugyanaz a logikai mező néha két, szinte azonos `<check>`/`<labelgroup>`
  elemként szerepel, csak más `title` felirattal vagy más fájltípus-listával
  (pl. `options.fen` "File Types" fülén Windows és Mac külön blokkban sorolja
  fel a támogatott kiterjesztéseket). PicasaPy Linux-first stratégiájához ez
  azt jelenti, hogy egy harmadik `os="linux"` ághoz hasonló feltételt kell(ene)
  bevezetni, vagy — mivel PicasaPy egyetlen célplatformra készül — egyszerűen
  el lehet hagyni ezt a fajta elágazást, és csak az egyik változatot kell
  megtartani.
- **`win_*` / `mac_*` attribútum-párok**: sok helyen (`width`, `height`,
  `fontsize`, `amount`, `title`, `minsize`) van platform-specifikus felülbírálás
  a generikus attribútum helyett/mellett — pl. `win_fontsize="24"
  mac_fontsize="16"`. Ez arra utal, hogy a Windows és Mac natív widget-metrikák
  jelentősen eltértek, ezért kézzel finomhangolták fájlonként.
- **`width`/`height` speciális értékei**: `"fit"` (tartalomhoz igazodó,
  minimális méret), `"fill"` (a rendelkezésre álló hely kitöltése — flex-like
  nyújtás), `"Nem"` (em-alapú, betűméret-relatív szélesség, pl. `"24em"`),
  `"Nli"` (line-alapú magasság, "N line" rövidítése, pl. `height="3li"`
  háromsoros szövegmezőhöz), konkrét pixelszám (`width="300"`,
  `mac_width="336"`).
- **`filter="filename"` / `filter="digits"`** az `<edit>`-en: kliensoldali
  bemenet-validáció — a `filename` szűrő valószínűleg tiltja az OS számára
  érvénytelen karaktereket (`\/:*?"<>|`), a `digits` csak számjegyeket enged.
- **`<bind>` elem**: a formátum legkifinomultabb, deklaratív "reaktív" eleme.
  Két fő mintája van:
  1. **Feltételes engedélyezés** (`attr="enabled"`, opcionális
     `transform="not"`): egy gomb/mező csak akkor aktív, ha egy másik
     jelölőnégyzet be van pipálva (pl. `album.fen`: a zeneböngésző gomb csak
     akkor engedélyezett, ha `usemusic` be van kapcsolva).
  2. **Érték-leképezés kijelzéshez** (`attr="title"`, `format`, `list`): egy
     csúszka (`<slider>`) numerikus pozícióját (0–N) egy `list="160|320|..."`
     pipe-szeparált táblázat alapján konkrét, ember által olvasható szövegre
     fordítja egy másik widget feliratában — ez lényegében egy kliensoldali
     "lookup table" binding, amit modern GUI-kban egy signal/slot vagy
     property-binding old meg (Qt-ban: `QSlider.valueChanged` → látszó
     `QLabel.setText` lambdában, vagy QML `property`/`Binding`).
- **`<multi>` elem**: a `<popup>` (combobox) kiválasztott indexéhez rendel
  különböző, egymást kizáró tartalmat (pl. `export.fen`
  "Image quality" popup 5 opciójához 4 statikus magyarázó `<label>` és egy
  `<slider>` tartozik — a kiválasztott index dönti el, melyik jelenjen meg).
  Ez egy `QStackedWidget`/QML `StackLayout` + index-binding párnak felel meg.
- **`hidden="true"` / `visible="false"` gomb** (`gpuploader_download.fen`,
  `gpuploader_debug.fen`): funkcionálisan létező, de vizuálisan elrejtett
  `cancel` típusú gomb kizárólag azért, hogy az Escape billentyű/rendszer
  bezárás-gomb működjön egy olyan dialógusban, ahol egyébként nincs "igazi"
  Mégse gomb (a fejlesztői kommentár ezt explicit meg is magyarázza a fájlban).
- **XML escape-elt speciális karakterek**: `&amp;`, `&gt;`, `&lt;`,
  `&quot;` — pl. `gpuploader_manage_devices.fen`-ben `&gt;&gt;`/`&lt;&lt;`
  mozgatógombok feliratként, `gpuploader_filestatus.fen`-ben `&lt;File
  Status&gt;` minta-placeholder szövegek.
- **HTML-szerű összekötő karakterlánc-formázók** (`%1$s` — pozíciós
  string-formátum): `gpuploader_about.fen`: `title="Google Photos Backup
  version %1$s"` — futásidőben behelyettesített dinamikus szöveg, printf-stílusú
  paraméterezéssel.
- **Kommentek**: sima XML-kommentek (`<!-- ... -->`) elszórtan, néha
  fejlesztői magyarázattal (l. fent a rejtett gomb esete), néha kikommentezett
  logikai csoport-jelölés (pl. `options.fen`: `<!-- Stats Reporting -->`,
  `<!-- AutoUpgradeCheck + AutoUpgradeAsk -->` — a mögöttes belső
  konfigurációs kulcsokra utalnak).
- **`name` mezők mint script-/adatkötés-kulcsok**: szinte minden interaktív
  widgetnek van `name` attribútuma — ez egyrészt a `<bind source="...">`
  hivatkozás célja, másrészt feltehetően közvetlenül megfeleltethető a
  `.picasa.ini`/registry beállításkulcsoknak (pl. `options.fen`
  `name="UITransitions"`, `name="autoexclude"`, `name="DoNotConfirmDeleteFromDisk"`
  — ezek valószínűleg 1:1 leképezhetők PicasaPy saját beállítás-sémájára).

### 2.4 Widget-fa mélysége és stílus

A legtöbb dialógus 2–4 szintnyi beágyazást használ:
`window → group(layout=column) → labelgroup → group(layout=row) → widget`.
A `labelgroup` a "Címke: [mező]" mintát kapszulázza — ez PySide6/QML-ben
`QFormLayout` egy sorának, illetve QML-ben egy `RowLayout`+`Label`+kontroll
kombinációnak feleltethető meg. A `buttongroup` mindig a dialógus alján, jobbra
igazítva jelenik meg (implicit `align="end"`, kivéve, ha explicit felül van
írva, pl. `contactmgr.fen`-ben `width="fill"` a bal oldali extra gombok
(Manage Online Contacts, Refresh Contacts) és a jobb oldali OK/Cancel
szétválasztásához).

---

## 3. Dialógusok részletes widget-fája (V1/V2/V3 releváns fájlok)

Ez a fejezet a PicasaPy V1–V3 fázisokhoz releváns dialógusokat írja le
tömör, de teljes widget-fa formában (a nem releváns — nyomtatás, CD-írás,
YouTube, gpuploader — dialógusok a 4–6. fejezetben, rövidebb formában
szerepelnek).

### 3.1 `about.fen` — Névjegy (V1)

- Ablak: `title="About Picasa"`, `width="300"`
- `appicon` (középre igazítva)
- `spacer` (1em)
- `label name="appname"` — "Picasa", középre igazított, kitöltött szélesség
- `label name="version"` — üres induláskor (futásidőben töltik ki), kicsi betű
- `label name="trademarks"` — védjegy-közlemény, kicsi betű
- `label name="notices"` — IJG (Independent JPEG Group) jogi közlemény
- `label name="copyright"` — üres induláskor, kicsi betű
- `button name="licenses"` — "Third-party licenses...", kicsi, középre

### 3.2 `album.fen` — Album tulajdonságai (V1)

- Ablak: `width="fit"`
- `labelgroup title="Name:" name="namelabel"` → `edit name="name" filter="filename"`
- `labelgroup title="Date:"` → `group layout="row"`: `date name="date"` + `button name="autodate"` ("Automatic date")
- `labelgroup title="Music:"`:
  - `check name="usemusic"` — "Use music for Slideshow and Movie presentation:"
  - `group layout="row" width="fill"`: `spacer amount="indent"` + `browse name="music"` (`win_filter="Music files|*.mp3;*.wma"`, `mac_filter="Music files|*.mp3;*.m4a"`), **`<bind attr="enabled" source="usemusic">`** — csak akkor aktív, ha a zene-jelölőnégyzet be van pipálva
- `labelgroup title="Place taken (optional):"` → `edit name="location"`
- `labelgroup title="Description (optional):"` → `edit name="caption" height="3li"` (többsoros)
- `buttongroup`: `button "OK" type="accept" name="ok"`, `button "Cancel" type="cancel"`

### 3.3 `confirm.fen` — Általános megerősítő ablak (V1, alapinfrastruktúra)

Ez egy **generikus, sablon jellegű dialógus**, amit a Picasa feltehetően
számos helyen újrahasznosít futásidőben behelyettesített szöveggel — ezért
PicasaPy-ban is érdemes egy közös `ConfirmDialog` komponensként megvalósítani.

- Ablak: `width="fit"`, `focus="buttons"` (alapból a gombsorra kerül a fókusz)
- `group`: `appicon` + `group layout="column"`:
  - `label name="message" width="24em" title="Message"` — a tényleges kérdés szövege (placeholder)
  - `check title="Don't ask again" name="remember"` — "ne kérdezze újra" opció
- `buttongroup name="buttons"`:
  - `button "Yes" type="accept" name="yes"`
  - `button "No" type="other" name="no"` — **megjegyzés:** `other` típus, nem `cancel`! Fontos szemantikai különbség.
  - `button "Cancel" type="cancel" name="cancel"`

### 3.4 `input.fen` — Generikus szöveg-/jelszóbekérő (V1, alapinfrastruktúra)

Minimalista, egysoros bemenetkérő; a `<password>` mező jelenléte arra utal,
hogy ugyanazt a sablont jelszóhoz is használják (a nem használt mező
feltehetően futásidőben rejtve van).

- `label title="Prompt:" name="prompt"` (placeholder felirat)
- `edit name="value" width="20em" max-width="fill"`
- `password name="password" width="20em" max-width="fill"`
- `buttongroup default="accept"`: `button "OK" type="accept"`, `button "Cancel" type="cancel"`

### 3.5 `rename.fen` — Fájlok tömeges átnevezése (V1)

- `label width="fill"` — "1 file(s) selected for rename.", `<bind format="%s file(s) selected for rename." source="files" attr="title">` — dinamikus darabszám-behelyettesítés
- `spacer amount="0"`
- `label title="Please enter a new name for these files:"`
- `edit width="25em" name="newname" filter="filename"`
- `group align="center"`:
  - `labelgroup title="Include in filename:"`: `check title="Date" name="date"`, `check title="Image resolution" name="size"`
- `label title="Example:" width="fill" height="2li" name="sample"` — élő előnézet a végleges fájlnévről
- `buttongroup`: `button "Rename" type="accept" name="rename"`, `button "Cancel" type="cancel"`

### 3.6 `move_database.fen` — Adatbázis áthelyezése (V1)

- Ablak: `title="Move Database"`, `width="fit"`, `focus="new_location"`
- Két figyelmeztető `label` (újraindítás szükséges; ne hálózati/cserélhető
  meghajtóra helyezze át, mert adatvesztés kockázata van)
- `labelgroup title="Current Database location:"` → `pathbox name="current_location"` (csak olvasható)
- `labelgroup title="New Database location:"` → `pathbox name="new_location" width="25em"` + `button "Browse..." name="changeloc"` + `button "Default" name="defaultloc"`
- `buttongroup`: `button "Move on next restart" type="accept" name="move"`, `button "Cancel" type="cancel"`

Ez közvetlenül megfelel a PicasaPy döntési dokumentumban rögzített
"ismételhető migráció" koncepciónak (`CLAUDE.md` 7. döntés) — érdemes a
PicasaPy megfelelőjében is explicit figyelmeztetést adni hálózati/NAS célútvonal
esetére, bár a PicasaPy-nál a NAS pont a normál használati eset (a `.picasa.ini`
fájlok NAS-on maradnak), tehát ez a figyelmeztetés-szöveg **nem** másolható át
változtatás nélkül.

### 3.7 `moving_database.fen` — Áthelyezés folyamatjelzője (V1)

- `title="Moving Database"`, `width="fit"`, `focus="progress"`
- `label` — "Picasa is moving the database."
- `progress name="progress"`

### 3.8 `compacting.fen` — Adatbázis tömörítése (V1)

- `title="Compacting"`, `width="fit"`
- `appicon` + magyarázó `label` (20em) + `label name="status" title="Compacting..."` (behúzva, `spacer amount="indent"`)
- `buttongroup`: egyetlen `button "Cancel" type="cancel"`

### 3.9 `imageproperties.fen` — Kép tulajdonságai (V1)

- `labelgroup title="Filename:"` → `label name="name" title="photo.jpg"` (placeholder)
- `labelgroup title="Location:"` → `pathbox name="path"`
- `labelgroup title="Size:"` → `group`: `label name="size" title="120k" width="6em"`, `label "Date:"`, `label name="date"`
- `list name="list" width="fill" height="20li" max-height="fill"`: két oszlop — `column "Property" width="15em"`, `column "Value" width="15em"` — ez egy kulcs-érték táblázat (feltehetően EXIF-mezők)
- `group align="center" name="nav"`: `button "Prev" name="prev"`, `label "x of x files" name="navlabel"`, `button "Next" name="next"` — lapozás több kijelölt kép között
- `buttongroup align="center" default="cancel"`: egyetlen `button "OK" type="cancel"` — **érdekesség:** az "OK" gomb `type="cancel"`-ként van jelölve (valószínűleg mert ez egy tisztán informatív, nem-módosító dialógus, Escape és Enter is ugyanúgy zárja).

### 3.10 `export.fen` — Exportálás mappába (V1)

A legrészletesebb "hagyományos" exportdialógus, jó minta a `<bind>`/`<multi>`
mintákra.

- Ablak: `title="Export to Folder"`, `width="fit"`, `focus="name"`
- `labelgroup title="Export location:"` → `group`: `pathbox name="location"` + `button "Browse..." name="changeloc"`
- `labelgroup title="Name of exported folder:"` → `edit name="name" filter="filename" width="fill"` + `check name="addnumbers" title="Add numbers to file names to preserve order"`
- `labelgroup title="Image size:"`:
  - `radiogroup name="sizeradio"`: `radio "Use original size"`, `radio "Resize to:"`
  - `group width="fill"` (**`<bind attr="enabled" source="sizeradio">`** — csak akkor aktív, ha "Resize to" van kiválasztva):
    `spacer indent` + `edit name="sizetext" width="4em" filter="digits"` (benne `<bind source="size" attr="title" list="320|480|640|800|1024|1200|1600">` — a csúszka pozíciójából számolt px-szám) + `label "pixels"` + `slider name="size" min="0" max="6" ticks="7" width="fill"`
- `labelgroup title="Image quality:"`:
  - `popup name="quality" width="10em"`: 5 `item` (Automatic/Normal/Maximum/Minimum/Custom)
  - `multi` (**`<bind source="quality" attr="value">`** index-vezérelt váltás): 4 magyarázó `label` + `slider name="qualslider" min="0" max="20" ticks="21"` (az utolsó, "Custom" opcióhoz)
- `labelgroup title="Export movies using:"` → `radiogroup name="movies"`: `radio "First frame"`, `radio "Full movie (no resizing)"`
- `labelgroup title="Watermark:"`:
  - `check name="usewatermark" title="Add watermark"`
  - `group layout="column" width="fill"`: `edit name="watermark"` (**`<bind attr="enabled" source="usewatermark">`**) + kis magyarázó `label`
- `buttongroup`: `button "Export" type="accept" name="export"`, `button "Cancel" type="cancel"`

### 3.11 `options.fen` — Beállítások (V1/V2/V3, 9 fül)

A legnagyobb `.fen` fájl (262 sor). Fülönként bontva:

| Fül | Tartalom (röviden) |
|---|---|
| **General** | UI: speciális effektek, tooltip/help tag (OS-függő felirat), egy kattintásra kilépés szerkesztőből. Fájlok: duplikátum-észlelés importáláskor, gyorsítótár törlése, törlés/eltávolítás megerősítés nélkül. Anonim statisztika küldése + "Privacy..." link. Automatikus frissítés popup (csak Win), nyelv popup (csak Win), kamera-akció popup (csak Mac). Importált képek célmappája (`browse`). |
| **E-Mail** | Levelezőprogram választása (radiogroup), többképes/egyképes méret (slider + `bind`/`list` leképezés px-re), videó küldési mód, HTML-es levél (csak Win). |
| **File Types** | JPEG mellett megjelenítendő formátumok — Windows- és Mac-ágban **külön, majdnem duplikált** checkbox-listával (BMP/GIF/PNG/TGA/TIFF/WEBP/PSD/RAW/Movies/QuickTime), a RAW mellett külső "Supported Formats" link. |
| **Slideshow** | Diavetítés hurkolása, MP3 lejátszás bekapcsolása + zenei mappa `browse` (`bind enabled` a checkbox-tól függ). |
| **Printing** | 5 db nyomtatási méret `popup`, nagy felbontású előnézet checkbox, nyomtatóminőség (csak Win, radiogroup), átméretező algoritmus minősége (radiogroup: Lanczos-3/Lanczos-8). |
| **Network** | Proxy felhasználónév/jelszó (csak Win), automatikus hálózati beállítás-felismerés, hálózati naplózási szint (`popup`, 5 fokozat), naplófájl útvonal (`pathbox`). |
| **Web Albums** | Alapértelmezett feltöltési méret popup, "csíkozott" (progresszív) feltöltés checkbox (`bind` a mérettől függ, `transform="not"`), JPEG-minőség megőrzése checkbox, csak csillagozott fotók szinkronizálása, szinkron-megerősítés kikapcsolása (`name="confirmsync::disable"` — **figyelemre méltó, más dialógust vezérlő kulcs!**), névcímkék feltöltése, vízjel hozzáadása + szöveg. |
| **Name Tags** | Arcfelismerés engedélyezése, javaslatok engedélyezése, javaslat-küszöb és klaszter-küszöb csúszkák (`bind`/`list` 50–95 tartomány), névcímkék mentése a fájlba, kontakt-fotók feltöltése Google Contacts-ba. |

A `Web Albums` és `Name Tags` fülek egyértelműen V3 (felhő/arcok) hatókörűek,
a `General`/`Slideshow`/`File Types` V1/V2, a `Printing`/`Network` alacsony
prioritású.

**Fontos minta:** a `confirmsync::disable` érték (a `check` `name`
attribútumában) valószínűsíthetően a `confirmsync.fen` dialógus
elnémítására szolgáló globális kulcs — vagyis a FEN `name` mezők legalább
néhány esetben nem csak "ez a widget értéke", hanem egy **cél-akció/dialógus
azonosítót** kódolnak `::` szeparátorral. Érdemes ezt a mintát tovább keresni
a Picasa forráskódjában/registry-dumpban, ha elérhető.

### 3.12 `poster.fen`, `reviewprint.fen`, `webexport.fen`, `orderprintsprefs.fen`, `youtube.fen`, `newbackupset.fen`, `cdchoose.fen`

Ezek a nyomtatás-, CD-írás- és YouTube-funkciókhoz tartoznak, PicasaPy
hatókörén (V1–V3) kívül esnek, csak a teljesség kedvéért, tömören:

- **`poster.fen`**: poszter nagyítás (`popup`, 200–1000%), papírméret `popup`, "Overlap tiles" checkbox.
- **`reviewprint.fen`**: két oszlopos layout (`layout="row"` a window-on!) — bal oldalt lista+törlés gombok, jobb oldalt `printpreview` + info + OK/Cancel.
- **`webexport.fen`**: exportméret/mozgókép-mód popupok, cím `edit`, célmappa `pathbox`+Browse, sablon-lista + élő `printpreview` előnézet.
- **`orderprintsprefs.fen`**: bejelentkezés nyomtatási szolgáltatáshoz + album név.
- **`youtube.fen`**: cím/leírás/kategória/tag mezők, "Make public" checkbox, jogi szövegek.
- **`newbackupset.fen`** / **`cdchoose.fen`**: CD/DVD és lemez-lemez biztonsági mentés beállításai — ez a funkció (optikai lemez archiválás) elavult, PicasaPy-ban valószínűleg nem lesz megfelelője.

### 3.13 `eula.fen` — Licencfeltételek (V1, első indítás)

- `title="Please review the license terms before using Picasa"`, `width="32em"`
- Szöveg + két `link` (Terms of Service, Privacy Policy)
- `check name="sendstats"` — anonim statisztika küldése
- `buttongroup`: `button "I Agree" type="accept" name="ok"`, `button "Cancel" type="cancel"`

---

## 4. V3 (arcok/kontaktok/felhő) releváns dialógusok

### 4.1 `contactmgr.fen` — Kontaktkezelő / "People" (V3, 80 sor, a második legnagyobb fájl)

Kétoszlopos fő elrendezés (`group layout="row"`):

**Bal oszlop** (`group layout="column"`):
- `labelgroup title="Search:"` → `edit name="search" width="fill"`
- `labelgroup title=""` → `list name="contacts" width="250" height="17li" scroll="v" header="hide"`, egy oszlop (`column width="fill"`) — a kontaktnevek listája
- `group align="end"`: `button "Delete Person" name="delete"`, `button "New Person" name="create"`

**Jobb oszlop** (`group layout="column"`) — a kiválasztott kontakt részletei:
- Üres `labelgroup`+`label` (feltehetően nagy előnézeti kép helye — ld. lejjebb `thumb`)
- `group`: `printpreview width="32" height="32" name="thumb"` (kontakt-miniatűr) + `group layout="column"`: `label name="count"` (hány fotón szerepel) + `label name="online_contact" title="Online Contact" width="100"`; jobbra `printpreview width="16" height="16" align="end" name="gplus"` (Google+ ikon)
- `labelgroup title="Name:"` → `edit name="fullname" width="250"`
- `labelgroup title="Email(s):"` → `edit name="emails" height="3li" scroll="v" width="fill"` + `check name="sync" title="Sync Face Tags with Web Albums" width="fill"`
- Négy azonosító-sor, mindegyik `labelgroup` + csak-olvasható `label`, saját `name`-mel a `labelgroup`-on is (feltehetően feltételes elrejtéshez):
  - `labelgroup title="Album ID:" name="album_id_group"` → `label name="album_id"`
  - `labelgroup title="Contact ID:" name="contact_id_group"` → `label name="contact_id"`
  - `labelgroup title="Focus ID:" name="focus_id_group"` → `label name="focus_id"`
  - `labelgroup title="Subject ID:" name="subject_id_group"` → `label name="subject_id"`
  - `labelgroup title="Focus Obfuscated GAIA ID:" name="focus_obfuscated_gaia_id_group"` → `label name="focus_obfuscated_gaia_id"`
  - `labelgroup title="Mobile Obfuscated GAIA ID:" name="mobile_obfuscated_gaia_id_group"` → `label name="mobile_obfuscated_gaia_id"`
- `group align="end"`: `label name="status" width="fill" text-align="right"` + `button "Revert" name="revert"`

**Alsó sáv:**
- `separator`
- `group`: `button "Manage Online Contacts" name="online"`, `button "Refresh Contacts" name="refresh_contacts"`, `buttongroup width="fill"`: `button "OK" type="accept" name="ok"`, `button "Cancel" type="cancel" name="cancel"`

**Megjegyzés PicasaPy-nak:** ez a dialógus jól mutatja a Picasa belső
kontakt-adatmodelljét — a "Contact ID", "Focus ID", "Subject ID" és a két
"Obfuscated GAIA ID" mező arra utal, hogy a Picasa PicasaWeb/Google+ kontakt-
összekapcsoláshoz több különböző azonosítót tárol egy személyhez (ez fontos
lehet a `contacts.xml` import tervezésekor, ld. `docs/specs/pmp-database.md`).

### 4.2 `write_all_facetags.fen` — Arc-címkék kiírása (V3)

- `title="Write Face Tags"`, `width="fit"`, `focus="onlyselection"`
- Figyelmeztető szöveg (hosszú művelet lehet, ajánlott kijelentkezni közben)
- `buttongroup` (nincs explicit `accept`/`cancel` a fő három műveletgombon —
  mindhárom sima `button`, csak a negyedik "Cancel" `type="cancel"`):
  - `button "Write Selected" name="onlyselection"`
  - `button "Write Faces" name="allwithfaces"`
  - `button "Write All" name="allfiles"`
  - `button "Cancel" type="cancel"`

### 4.3 `refresh_contacts_progress.fen` — Kontaktfrissítés folyamatjelzője (V3)

- `title="Refreshing Contacts"`, `width="fit"`, `focus="ok"`
- `label` — "Picasa is refreshing online contact information."
- `progress name="progress"`
- `buttongroup align="center"`: `button "Refresh in Background" type="accept" name="ok"` — **érdekesség:** ez nem megszakítja, hanem háttérbe küldi a műveletet.

### 4.4 `autocomplete_errors.fen` — Kontakt-beillesztési hibák (V3)

- `title="Autocomplete Errors"`
- `label` — magyarázó szöveg
- `list name="errorlist" scroll="v" height="5li" header="show" width="fill"`: 3 oszlop — `Contact` (12em), `Error` (24em), `Status` (8em)
- `buttongroup width="fill"`: `button "OK" type="accept" name="ok"`

### 4.5 `genericlogin.fen` — Google bejelentkezés (V3)

- `title="Login"`, `width="fit"`
- `label name="status"` (állapotszöveg helye)
- `labelgroup title="Email:" name="emaillabel"` → `edit name="username"` + `link name="createlink" title="Create an account..."`
- `labelgroup title="Password:"` → `password name="password"` + `link name="forgotlink" title="Forgot your password?"` + `group`: `check name="savepassword" title="Save Password"` + `label "Login secured by SSL"`
- `buttongroup`: `button "Log in" type="accept" name="accept"`, `button "Cancel" type="cancel"`

### 4.6 `confirmsync.fen` — Album szinkronizálás megerősítése (V3)

- `title="Sync Album to Web"`, `width="fit"`
- `label name="msg"` — "Upload this album to Web Albums and keep it in sync?"
- `label "Current settings:"`
- `group layout="row" width="fill"`: behúzás (`spacer 3em`) + `group layout="column"`:
  - `labelgroup title="Size:"` → `label name="size"`
  - `labelgroup title="Visibility:"` → `label name="visibility" title="Unlisted"`
  - `label name="starred" title="Sync starred photos only"`
- `check name="dontask" title="Don't ask me again (always use current settings)"`
- `group layout="row" width="fill"`: `button "Change Settings..." name="change"` (bal) + `buttongroup` (jobb): `button "Sync" type="accept"`, `button "Cancel" type="cancel"`

### 4.7 `quota.fen` — Alacsony tárhely figyelmeztetés (V3)

- `width="fit"`, `focus="buttons"`, `title="Low Storage"`
- `appicon` + `group layout="column"`: `label name="message"` + `link name="learnmore"` + `check name="remember" title="Don't warn me about this in the future."`
- `buttongroup name="buttons"`: `button "Upgrade" type="accept" name="upgrade"`, `button "OK" type="cancel" name="ok"` — **érdekesség:** itt az "OK" a `cancel` típus (mert ez az elutasító/"most nem" válasz).

### 4.8 `importweb.fen` — Webalbumok importálása (V3)

- `title="Import Albums from Web Albums"`, `width="fit"`
- Magyarázó `label` + `label name="albumcount" title="You have 100 web albums online."` (placeholder szám)
- `radiogroup name="importall"`: `radio "Import all albums"`, `radio "Import selected albums:"`
- `group layout="row" width="fill"` (**`<bind attr="enabled" source="importall">`**): behúzás + `list name="albums" max-width="fill" height="6li" scroll="v" checkboxes="true"`: 2 oszlop (Name 15em, Date 15em)
- Záró magyarázat: csak az új képek töltődnek le
- `buttongroup`: `button "OK" type="accept" name="ok"`, `button "Cancel" type="cancel"`

### 4.9 `auto_backup_prompt.fen` — Google Fotók automatikus mentés felajánlása (V3, opcionális)

- `title="Google Photos Backup"`, `width="30em"`
- Bal oldalt ikon (`image` 72×72), jobb oldalt cím (`fontweight="bold"`, platformfüggő betűméret) + magyarázó szöveg
- `buttongroup align="end" default="accept"`: `button "Get Google Photos Backup" type="accept" name="yesbutton"`, `button "No Thanks" type="cancel" name="ignorebutton"`

---

## 5. `addtogroup.fen` — legacy/tervezet minta (nem építendő újra)

Ez a fájl feltűnően eltér a `contactmgr.fen`-től: statikus, kódolt "Friends /
Family / Coworkers" checkbox-lista, miközben a végleges kontaktkezelő
(`contactmgr.fen`) egy teljesen más, dinamikus, kereshető listás UI-t használ.
Ez arra utal, hogy `addtogroup.fen` egy **korai tervezet vagy elhagyott
funkció** maradványa (talán egy korábbi, statikus csoport-koncepció, amit a
végleges "People" arc-alapú modell váltott fel). PicasaPy tervezésekor ezt a
fájlt informatívnak, de **nem követendő mintának** kell tekinteni — a
`contactmgr.fen` a mérvadó.

---

## 6. `gpuploader_*.fen` — a különálló "Google Photos Backup" segédalkalmazás (nem PicasaPy hatókör)

18 fájl tartozik ide: `gpuploader_about`, `_advoptions`, `_confirm`, `_debug`,
`_download`, `_file_errors`, `_filestatus`, `_instructions`,
`_manage_devices`, `_onboard`, `_prefs`, `_quota_error1`, `_quota_error2`,
`_storage_notify`, `_welcome`. Ezek egy **külön, önálló futtatható**
alkalmazás (a Google Fotók asztali automatikus feltöltő kliens, ami külön
tálca-alkalmazásként futott, nem a fő `Picasa.exe` UI-jaként) FEN-fájljai,
csak azért kerültek a `runtime/` mappába, mert ugyanazt a FEN-motort
használták.

Tartalmuk röviden: onboarding/köszöntő képernyők, eszközkezelés
(fehér-/feketelista mappákhoz és eszközökhöz, kettős lista + mozgatás
`>>`/`<<` gombokkal), feltöltési méret rádiógombok (magas minőség vs.
eredeti), kvóta-figyelmeztetések, hibalisták, egy fejlesztői
"debug"/"trace" ablak fülekkel és rejtett/trükkös gombokkal, valamint egy
`gpuploader_filestatus.fen` nevű **belső fejlesztői diagnosztikai ablak**
(fájl-metaadatok, upload-állapot placeholder-szövegekkel, pl. `<DirEntry.Size()>`).

**PicasaPy szempontból nem releváns** (a projekt döntése szerint a felhős
PicasaWeb-funkciók alacsony prioritásúak, és ez egy teljesen külön
alkalmazás volt) — csak formátum-referenciaként érdemes megtartani, mert
platform-specifikus finomhangolás (`win_fontsize`/`mac_fontsize`,
`mac_minsize`) és néhány szokatlan minta (`hidden`/`visible` gomb,
`checkboxes="true"` lista, `%1$s` string-formázás) itt a leggazdagabb.

---

## 7. `runtime/*.html` fájlok szerepe

A `.fen` fájlok mellett néhány `.html` fájl is UI-t definiál, de más
technológiával (natív böngésző-vezérlő beágyazása, nem a FEN-motor):

| Fájl | Szerep |
|---|---|
| `runtime/pwconfirm.html` | A PicasaWeb-album letöltésének megerősítő oldala — natív HTML/CSS sablon, `%PLACEHOLDER%` stílusú szerver-oldali (vagy Picasa saját sablon-motoros) string-behelyettesítéssel (`%WEBALBUMDOWNLOAD%`, `%ALBUMTITLE%`, `%IMAGECOUNT%`, `%THUMBURL%` stb.) és `<FOREACHIMAGE>` egyedi ciklus-taggel a képek felsorolásához. A gombok HTML `<form action="...">` submitokkal küldenek vissza egyedi "akció-URL"-eket (`%CONFIRMLINK%`, `confirm::deny`) a natív alkalmazásnak — ez egy klasszikus "beágyazott webview mint natív dialógus" minta, hasonlóan a `contactmgr.fen` `online`-gombjához kapcsolódó "Manage Online Contacts" böngésző-felugráshoz. |
| `runtime/geotag/geopanelscript.html`, `geopanelscript_v3.html` | A geocímkézés (térkép) panel — egy beágyazott Google Maps JavaScript-integráció (`map_canvas`, keresés, hibakezelő overlay divek). Ez a Picasa térkép-alapú helymeghatározás UI-ja, külső Google Maps API-hívásokkal — mivel élő Google Maps API kulcsot igényel és a szolgáltatás azóta megváltozott, PicasaPy-ban ez ma már más térképszolgáltatóval (pl. OpenStreetMap/Leaflet) váltandó ki, nem másolható át. |
| `i18n/uninstall*.html` (34 nyelvi változat) | A Windows-os eltávolító (uninstaller) végén megjelenő HTML-oldal, nem alkalmazás-dialógus — telepítő-infrastruktúra, PicasaPy-nak nem releváns. |
| `web/templates/*/`, `web/documentation/*` | A "Export as HTML Page" (`webexport.fen`) funkció exportálási sablonjai (4 stílus: blackbg/blackfrm/greybg/greyfrm/whitebg/whitefrm) és a sablon-készítési dokumentáció — ezek nem alkalmazás-UI-k, hanem a generált statikus weboldal-exportok HTML-sablonjai. Csak akkor relevánsak, ha PicasaPy megvalósítja a "webes galéria exportálása" funkciót (alacsony prioritás). |

Összefoglalva: a `.fen` fájlok a **natív alkalmazás-dialógusok**, a `.html`
fájlok pedig vagy **beágyazott webview-tartalmak** (`pwconfirm.html`,
`geopanelscript*.html` — ezek élő, interaktív, natív gombokkal integrált felületrészek),
vagy **kimeneti sablonok/telepítő-kísérő oldalak**, amelyek nem futásidejű
alkalmazás-UI-k.

---

## 8. Összefoglaló javaslat a PicasaPy fejlesztőjének

1. A FEN elem-/attribútum-táblázat (2. fejezet) alapján egy egyszerű
   PySide6/QML fordító séma felállítható: `window`→`QDialog`/QML `Popup`,
   `group[layout=row|column]`→`QHBoxLayout`/`QVBoxLayout` vagy QML
   `RowLayout`/`ColumnLayout`, `labelgroup`→`QFormLayout` sor vagy
   `Label`+kontroll pár, `buttongroup`→`QDialogButtonBox` (az `accept`/
   `cancel`/`other` típusok közvetlenül megfeleltethetők), `bind`→Qt
   property-binding/signal-slot vagy QML deklaratív binding.
2. **V1-hez azonnal hasznos** dialógus-készlet: `about`, `album`, `confirm`,
   `input`, `rename`, `move_database`, `moving_database`, `compacting`,
   `imageproperties`, `export`, `eula`, valamint az `options.fen` "General"/
   "File Types"/"Slideshow" fülei.
3. **V2-höz** (szerkesztő): `customaspectratio`, `offsettime`, továbbá az
   `options.fen` nyomtatási/hálózati fülei alacsonyabb prioritással.
4. **V3-hoz** (arcok/felhő): `contactmgr` (a legfontosabb, legösszetettebb),
   `write_all_facetags`, `refresh_contacts_progress`, `autocomplete_errors`,
   `genericlogin`, `confirmsync`, `quota`, `importweb`, `auto_backup_prompt`,
   valamint az `options.fen` "Web Albums"/"Name Tags" fülei.
5. A `gpuploader_*`, nyomtatás-, CD-írás- és YouTube-dialógusok
   dokumentálva vannak, de fejlesztési sorrendben **nem prioritásosak** —
   ha a felhasználó (a projekt tulajdonosa) ezekre igényt jelez, ez a
   dokumentum már tartalmazza a szükséges widget-fát az újraépítéshez.
