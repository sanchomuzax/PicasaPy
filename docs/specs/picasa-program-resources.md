# Picasa 3.9 — erőforrás- és formátum-leltár (gombok, web-export, runtime, plugin-ök)

> Forrás: eredeti Picasa 3.9 (Windows, 2015-ös build) programmappa, kizárólag
> olvasva. A dokumentum **nem** tárgyalja a `.fen` dialógusfájlokat és az
> `.exe`-ből kinyert stringeket — azokat külön ügynökök dokumentálják.

---

## 1. Gombcsomagok — a `buttons/*.pbz` formátum

### 1.1 Csomagformátum: PBZ = ZIP

A `buttons/` mappában két fájl van: `core-lh2.pbz` és `geotag.pbz`. Mindkettő
egy **közönséges ZIP-archívum** (átnevezve `.pbz` kiterjesztésre — Python
`zipfile` modullal simán megnyitható, jelszó és tömörítés-trükk nélkül).

A ZIP-en belül **`.pbf` fájlok** vannak, egyenként egy gombot leírva.
A fájlnév minden esetben egy **GUID** (pl. `{0B3F3356-4FA1-48ca-B972-2B7D20AC6FBF}.pbf`),
tehát a fájlnév maga nem hordoz jelentést — a gomb azonosítója a `.pbf` XML
tartalmán belüli `id` attribútum.

- `core-lh2.pbz` → 9 db `.pbf` fájl (az alap kimeneti sáv gombjai)
- `geotag.pbz` → 1 db `.pbf` **+ 1 db azonos nevű `.psd`** (a gomb ikonja!)

### 1.2 A `.pbf` fájl: sima XML

A `.pbf` fájlok **nem bináris formátumok**, hanem UTF-8 (néha BOM-mal) kódolt,
CRLF sortörésű XML dokumentumok. Gyökérelem: `<buttons format="1" version="1">`,
benne egyetlen `<button>` elemmel.

```xml
<?xml version="1.0" encoding="utf-8" ?>
<buttons format="1" version="1">
  <button id="custombutton/blogger" type="dynamic">
    <placement>6.0</placement>
    <icon name="outputlayout/blogger_icon" src="runtime"/>
    <label>BlogThis!</label>
    <tooltip>Post photos to your blog via Blogger</tooltip>
    <tooltip_da>Indsæt billeder i din blog med Blogger</tooltip_da>
    <!-- ... egy <tooltip_XX> elem nyelvenként (da, de, en-gb, es, fi, fr,
         it, ja, ko, nl, no, pl, pt-br, ru, sv, tr, zh-cn, zh-tw) ... -->
    <action verb="hybrid">
      <param name="url" value="https://photos.blogger.com/picasa-post.g"/>
    </action>
  </button>
</buttons>
```

**Mezők:**

| Elem/attribútum | Jelentés |
|---|---|
| `<button id="...">` | A gomb egyedi azonosítója. Kétféle névtér látható: `outputlayout/<name>` (beépített, "statikus" Picasa-gombok — a natív exe-kód rendeli hozzá a viselkedést) és `custombutton/<name>` (bővítmény-gombok, saját `action`-nel). |
| `type="static"` | A gomb viselkedését a Picasa natív kódja implementálja (nincs `<action>` elem); a `.pbf` csak az elhelyezést/felirat felülbírálását adja meg. |
| `type="dynamic"` | A gomb viselkedését a `.pbf`-ben deklarált `<action>` írja le — nincs natív kód mögötte. |
| `<placement>N.0</placement>` | Balról jobbra sorrend a gombsávban (lebegőpontos szám — a `.0` arra utal, hogy törtértékek is elférnének két gomb közé beszúráshoz). |
| `<label>` | A gomb felirata (nyelvfüggetlen alap — a tényleges lokalizált felirat valószínűleg az `.exe` string-táblájából jön, ha a `<label>` hiányzik). |
| `<icon name="..." src="...">` | Az ikon forrása. `src="runtime"` esetén az ikon a `runtime/` mappa `respack.yt` erőforráscsomagjában él, `name` az ottani logikai ikonnév (pl. `outputlayout/blogger_icon`). `src="pbz"` esetén az ikon **magában a PBZ-ben** van, `{GUID}.psd` néven, ahol a GUID megegyezik a gomb saját `.pbf`-jének fájlnevével — ez a `geotag.pbz` esetében látszik. |
| `<tooltip>` / `<tooltip_XX>` | Angol alap tooltip + nyelvkód-szuffixált (BCP-47-szerű, kisbetűs, pl. `pt-br`, `zh-cn`) fordítások, mind ugyanabban a `.pbf`-ben — tehát a PBZ-formátum saját magában hordozza az i18n-t, nem külön nyelvi fájlokban. |
| `<action verb="...">` | A dinamikus gomb művelete. Megfigyelt `verb` értékek: `"hybrid"` (böngészőben/beépített webnézetben megnyitandó URL — lásd `<param name="url" value="...">`) és `"geolocate"` (belső parancs, nincs paramétere — a natív Google Earth/térkép integrációt indítja). |
| `<param name="..." value="...">` | Az `action` tetszőleges számú kulcs-érték paramétere. |

### 1.3 Ikonformátum a PBZ-n belül

A `geotag.pbz`-ben talált ikon (`{9A42861F-...}.psd`) valódi **Adobe
Photoshop (.psd) fájl**, 50×40 px, RGBA, 4×8 bit csatorna — tehát a
gomb-ikonok natív PSD-ként vannak becsomagolva (rétegek nélkül, egyszerű
exportált bitmap), nem PNG/ICO.

### 1.4 A `core-lh2.pbz` gombjai (9 db)

Ez a fájl a fő kimeneti sáv (az album-nézet alján/tetején megjelenő
"mit csinálj a kijelölt képekkel" gombsor) alap gombkészletét írja le.
`outputlayout/*` azonosítójú, `type="static"` gombok — vagyis a tényleges
funkciót a Picasa natív kódja adja, a `.pbf` csak sorrendet/felirat-felülbírálást ad:

| # | id | placement | label (felülbírálás) | Feltételezett funkció |
|---|---|---|---|---|
| 1 | `outputlayout/webupload` | 1.0 | — | Feltöltés Picasa Webalbumokba |
| 2 | `outputlayout/ebutton` | 2.0 | — | E-mailben küldés |
| 3 | `outputlayout/pbutton` | 3.0 | — | Nyomtatás |
| 4 | `outputlayout/folderbutton` | 4.0 | — | Mappába exportálás / mappa megnyitása |
| 5 | `outputlayout/orderbutton` | 5.0 | "Shop" | Fotónyomtatás rendelése (print-szolgáltatás) |
| 6 | `custombutton/blogger` (dinamikus) | 6.0 | "BlogThis!" | Blogger-be posztolás (`action verb="hybrid"`, URL: `https://photos.blogger.com/picasa-post.g`) |
| 7 | `outputlayout/collage` | 7.0 | "Collage" | Kollázs készítése |
| 8 | `outputlayout/makemovie` | 8.0 | "Movie" | Diavetítés/film készítése a kijelölt képekből |
| 9 | `outputlayout/sharewith` | 9.0 | "Hello" | Megosztás ("Hello" feltehetően a Google Hello/IM-integráció maradványa, vagy csak egy generikus felirat-placeholder) |

### 1.5 A `geotag.pbz` gombja (1 db)

| id | placement | label | ikon | action |
|---|---|---|---|---|
| `custombutton/geolocate` | 10.0 | "Geo-Tag" | `{9A42861F-...}/earth_icon`, `src="pbz"` (a csomagba ágyazott PSD) | `verb="geolocate"` (paraméter nélkül — natívan feldolgozott parancs, ami a Google Earth-glóbuszra helyezi a képeket) |
| Tooltip | — | "Place pictures on the Google Earth globe" | | |

**PicasaPy tanulság:** a `buttons/*.pbz` egy nyitott, bővíthető, deklaratív
plugin-mechanizmus — új gomb hozzáadása annyi, hogy egy ZIP-be teszünk egy
XML-t (+ opcionális PSD ikont). Egy Python-újraírásban ez triviálisan
JSON/YAML + PNG kombinációra cserélhető, megőrizve a `static`/`dynamic`
megkülönböztetést és a `verb`/`param` akció-modellt.

---

## 2. Web-export sablonrendszer (`web/templates/`, `web/documentation/`)

### 2.1 Áttekintés

Amikor a felhasználó egy albumot "Weboldal exportálása" funkcióval statikus
HTML-lé exportál, a Picasa a `web/templates/<sablonnév>/` mappák valamelyikét
dolgozza fel. A hivatalos dokumentáció (`web/documentation/index.html`,
"The Picasa Web Templating System") **teljes egészében megtalálható** a
programmappában — az alábbi alfejezetek ennek tömör, magyar összefoglalói,
kiegészítve a tényleges sablonfájlokból kiolvasott adatokkal.

Az exportálás menete:
1. A kijelölt képekből bélyegkép- és nagyméretű másolatok készülnek a cél
   könyvtár `thumbnail/` ill. `image/` almappáiba.
2. A sablon gyökérfájlja — mindig `index.tpl` — feldolgozásra kerül, a benne
   szereplő parancsok sorban lefutnak.
3. A `loop` és `targetloop` parancsok képenként ismétlik a hivatkozott
   include-fájlt, feltöltve a kép-hurok változóit.

### 2.2 Sablonmappa-szerkezet

Minden sablon egy önálló alkönyvtár a `web/templates/` alatt, tipikusan:

```
<sablonnév>/
  index.tpl              # kötelező belépési pont, .tpl parancsfájl
  header.html / footer.html
  imagelistheader.html / imagelistelement.html / imagelistfooter.html
  targetlistheader.html / includedtarget.html
  itemheader.html / targetlistelement.html    # per-kép cél-oldal tartalma
  imagetarget.tpl         # a targetloop által képenként feldolgozott al-sablon
  style.css
  preview.jpg              # a sablonválasztó előnézeti képe
  assets/                  # statikus erőforrások (pl. style.css), a "copy" paranccsal másolva
  xLifescape.ini           # csak a keretes (…frm) sablonoknál, ld. lentebb
```

A ténylegesen szállított 6 sablon:

| Mappa | Jellemző | Megjegyzés |
|---|---|---|
| `whitebg/` | Fehér hátterű, index + külön "target" oldalak | `verboseimagelistelement.html` is van (bővebb képleírás-változat) |
| `blackbg/` | Fekete hátterű, egyébként `whitebg` szerkezete | |
| `greybg/` | Szürke hátterű | |
| `whitefrm/`, `blackfrm/`, `greyfrm/` | **Keretes (frame-based)** elrendezés: bal oldalon görgethető bélyegkép-lista, jobbon a nagy kép — `frameset.htm` helyett `frameIndex.html`, `framebase.tpl`, `frameImageSet.tpl`, `framecaption.tpl`, `thumbnails.tpl` és egy `xLifescape.ini` konfigurációs fájl tartozik hozzájuk. Ezek klasszikus HTML-frame (`<frameset>`) alapú, egyoldalas galériát generálnak. |
| `xml/` | Nem HTML, hanem **nyers XML** kimenetet generáló sablon ("Raw XML-formatted text for further translation") — külső feldolgozásra szánt gépi export, `header.xml`/`footer.xml`/`imagelistheader.xml`/`imagelistelement.xml`/`imagelistfooter.xml` fájlokkal. |

A `web/documentation/examples/` egy **hetedik, tanpélda-sablont** tartalmaz
(`TestWebExport`, `TestConditional1` feliratokkal) — kifejezetten a fenti
dokumentáció illusztrálására, nem terjesztett sablon.

### 2.3 A `.tpl` parancsnyelv

Az `index.tpl` (és az általa hívott al-`.tpl` fájlok, pl. `imagetarget.tpl`)
egy egyszerű, soronkénti, `#` megjegyzés-jelet használó parancsnyelv.
Minden ilyen fájl `#templatefile -v "verzió" -n "név" -d "leírás"` fejléccel
kezdődik (a `-n`/`-d` a sablonválasztó UI-ban jelenik meg).

Parancsok:

| Parancs | Paraméterek | Jelentés |
|---|---|---|
| `define` | `variableName variableValue` | Belső változó definiálása; a fájl teljes további feldolgozása során minden `<%variableName%>` erre cserélődik. Csak az utolsó `define` érvényes (felülírja a korábbiakat). |
| `include` | `fileName` | HTML/sablonfájl beillesztése; a változó-helyettesítés a beillesztés pillanatában történik. |
| `loop` | `perImageFile [columnCount rowStartInclude rowEndInclude]` | A megadott fájlt egyszer-per-kép illeszti be, eközben aktívvá válnak a "kép-hurok" változók. **A `columnCount`/`rowStartInclude`/`rowEndInclude` a hivatalos doksi szerint még nincs megvalósítva** (`notImplemented` jelölés). |
| `targetloop` | `targetTemplateFile targetIncludeFile [...]` | Képenként **külön fájlt** exportál (`targetTemplateFile` alapján, sorszámozva: `index0.html`, `index1.html`, …), és a jelenlegi fájlba beilleszti `targetIncludeFile`-t képenként, `<%targetPath%>` változóval a generált fájl relatív útjára mutatva. Keretes/lapozható galériákhoz. |
| `copy` | `source [destination]` | Statikus erőforrás (pl. `assets\`) rekurzív másolása a célkönyvtárba; záró backslash kötelező a könyvtárspecifikációnál. |

### 2.4 Változó- és feltétel-szintaxis a HTML/XML include-fájlokban

- Változóhelyettesítés: `<%valtozoNev%>`
- Feltétel: `<%if valtozoNev%>...tartalom...<%endif%>` — a `!` előtaggal
  negálható: `<%if !valtozoNev%>...<%endif%>`

**"Parancs-változók"** (export-vezérlők, `define`-nal állíthatók, és a
HTML-ben is felhasználhatók):

| Változó | Jelentés |
|---|---|
| `exportFileName` | A generált fájl neve (targetloopnál ehhez fűződik a sorszám: `index0.html`, `index1.html`, …). |
| `imageWidth` / `imageHeight` | A nagyméretű exportált kép max. szélessége/magassága (`0` = eredeti méret). |
| `thumbnailWidth` / `thumbnailHeight` | A bélyegkép max. mérete (`0` = eredeti méret). |
| `bgColor` | A bélyegképek árnyékának színe (alapért. `#FFFFFF`). |
| `shadowedThumbnails` | `true`/`1`: árnyék a bélyegképeken (alapért. `1`). |
| `shadowedImages` | `true`/`1`: árnyék a nagy képeken (alapért. `0`). |

**Album-szintű változók** (minden oldalon elérhetők):

`albumNumber`, `albumName`, `albumCaption`, `albumDate` (hó/év), `albumItemCount`

**Kép-hurok változók** (`loop`/`targetloop` belsejében, az album-változókon felül):

`itemNumber`, `itemName`, `itemOriginalPath`, `itemWidth`, `itemHeight`,
`itemSize` (KB-ban, az **eredeti** fájlra), `itemThumbnailImage`,
`itemLargeImage`, `isNextImage`/`isPrevImage`, `nextImage`/`prevImage`,
`nextThumbnail`/`prevThumbnail`. A ténylegesen szállított sablonokban emellett
`itemCaption`, `itemThumbnailWidth`/`itemThumbnailHeight`, `itemNameOnly`,
`isFirstImage`/`isLastImage`, `firstImage`/`lastImage`,
`firstThumbnail`/`lastThumbnail` változók is előfordulnak (ezek a
dokumentációból hiányoznak, de az `xml/imagelistelement.xml` sablon
ténylegesen használja őket).

**Cél-oldal (`targetloop` által generált fájl) változói** — az album- és
kép-hurok változókon felül: `referrer`, `isNextTarget`/`isPrevTarget`,
`isFirstTarget`/`isLastTarget`, `nextTarget`/`prevTarget`,
`firstTarget`/`lastTarget`, `outputIndex`.

**Tartalmazó oldalon a `targetloop` hurok belsejében**: `targetPath` (a
generált cél-fájl relatív útja).

### 2.5 Példa (a `whitebg` sablonból)

```
index.tpl:
  define exportFileName index.html
  include header.html
  include imagelistheader.html
  include targetlistheader.html
  targetloop imagetarget.tpl includedtarget.html
  include footer.html
  copy assets\

imagelistelement.html:
  <a href="<%itemLargeImage%>"><img src="<%itemThumbnailImage%>"
     width="<%itemThumbnailWidth%>" height="<%itemThumbnailHeight%>"
     title="<%itemCaption%>" border="0"></a>

includedtarget.html:
  <a href="<%targetPath%>"><img src="<%itemThumbnailImage%>" ...></a>
```

**PicasaPy tanulság:** ez egy teljesen dokumentált, egyszerű, saját
sablonnyelv (nem Jinja2/Mustache) — egy Python újraírásban vagy egy kis
saját parser (fenti táblázat = teljes spec), vagy pragmatikusan egy Jinja2
"kompatibilitási réteg" építhető rá, amely a `<%var%>`/`<%if%>` szintaxist
Jinja2 `{{ var }}`/`{% if %}` formára fordítja át az örökölt sablonok
befogadásához.

---

## 3. Runtime konfigurációs fájlok (`runtime/`)

### 3.1 `filters.txt` — a mappa-beolvasás kizárási listája

Tartalma (teljes fájl, 4 szekció, üres sorokkal elválasztva):

```
DirectoryFilters
windows
winnt
temp
Program Files
Originals

DirectoryIncludes

FileFilters

FileIncludes
```

**Szemantika:** a fájl négy, fejléc-sorral kezdődő szekcióból áll:

- `DirectoryFilters` — könyvtárnév-minták, amelyeket a lemez-beolvasó
  (scanner) **kihagy**, ha a mappa neve tartalmazza/megegyezik ezekkel
  (`windows`, `winnt`, `temp`, `Program Files`, `Originals`). Az
  `Originals` bejegyzés a Picasa saját "nem-destruktív szerkesztés"
  biztonsági mentési almappája — ezt direkt nem indexeli újra, hogy ne
  duplázza a fotókat.
- `DirectoryIncludes` — kivétel-lista a fenti kizárásokhoz (üres — nincs
  gyári kivétel).
- `FileFilters` — fájlnév-minták, amelyeket kizár a beolvasásból (üres a
  gyári telepítésben — a kiterjesztés-alapú szűrés máshol, feltehetően az
  `.exe`-ben van hardkódolva).
- `FileIncludes` — kivétel-lista a fájlszűréshez (üres).

Ez **közvetlenül releváns a PicasaPy scanner-modulra**: a `.picasa.ini`
kompatibilitás mellett érdemes ugyanezt a négyszekciós, kibővíthető
kizárási sémát követni (könyvtár/fájl × filter/include).

### 3.2 `fliprtl.txt` — RTL-tükrözési lista

Sima szöveges lista, soronként egy ikon-azonosító (pl. `arrows/right`,
`globalbuttons/left_p`, `compose_mail/rtl_icon`). Ezek azok a `respack.yt`-beli
ikon-nevek, amelyeket a UI **jobbról-balra (RTL) nyelvi módban** (arab, héber
stb.) vízszintesen tükrözve kell megjeleníteni — tipikusan navigációs
nyilak és irányfüggő ikonok. ~150+ bejegyzés.

### 3.3 `winedisable.txt` — funkció-letiltási lista Wine alatt

Sima szöveges lista, soronként egy szám (pl. `40225`, `40192`, …) —
feltehetően belső erőforrás-/parancs-azonosítók (menüpont- vagy
funkció-ID-k), amelyeket a program **letilt, ha Wine alatt fut** (Linuxon/
macOS-en, natív Windows API hiányában). Ez közvetve megerősíti, hogy a
Picasa fejlesztői tudatosan számoltak a Wine-kompatibilitással — ami a
PicasaPy "Linux-first" célkitűzését történeti szempontból alátámasztja.

### 3.4 `respack.yt` — bináris erőforráscsomag → **MEGFEJTVE (2026-08-06)**

`runtime/respack.yt` (3,7 MB) és `runtime/slingshot/respack.yt` (372 KB)
saját, dokumentálatlan bináris formátum volt — **azóta teljesen
visszafejtve**, 2769/2769 rétegen hibátlan kicsomagolással.

Teljes leírás: **[`picasa-respack-format.md`](picasa-respack-format.md)**;
kicsomagoló: `tools/picasa/respack.py`.

Röviden: névindex a fájl végén (`uint32` eltolás a 0. bájton), rekordonként
13 bájtos fejléc (`int16` határoló doboz + kódolásbájt), az adat vagy tömör
RGBA-kitöltés, vagy **soronkénti RLE** `(darab, R, G, B, A)` ötösökkel. A
csomag **2909 bejegyzést** tartalmaz: 2769 rajzi réteget (ezek adják a
`.pbf` gombfájlok `src="runtime"` és a `fliprtl.txt` ikonneveit) és
**140 `.tre` UI-elrendezés-forrásfájlt** — vagyis a Picasa fő ablakának és
szerkesztőjének teljes elrendezés-forráskódját.

### 3.5 `.ytf` fájlok — saját betűtípus-formátum

A `runtime/*.ytf` fájlok (pl. `HelveticaNeue Condensed-20-1.000000-400-0.ytf`)
**nem** szabványos TrueType/OpenType fájlok — a `file` eszköz nem ismeri fel
őket (egy kivétellel "GLS_BINARY_LSB_FIRST" jelzést ad, ami egy általános
bináris-szerializációs jelzőre utal, nem betűtípus-specifikus). A fájlnév
maga kódolja a paramétereket: `<családnév>-<méret>-<skálázás>-<súly>-<stílus>.ytf`
(pl. `Praxis Semi Bold-Heavy-14-1.000000-700-0.ytf` = 14 pt, 1.0 skála,
700 = bold súly, 0 = normál stílus). Ez arra utal, hogy a Picasa **előre
renderelt, fix méretű raszter- vagy útvonal-glyph-gyorsítótárat** tárol
fájlonként egy adott betűtípus/méret/súly kombinációhoz (feltehetően a
saját `.fen` UI-renderelő motorjához, GLS = "Google/Generic Layout System"
jellegű belső könyvtár). Nem használható közvetlenül Qt/QML alatt — a
PicasaPy-nak natív rendszerbetűtípusokat vagy szabvány TTF/OTF fájlokat kell
használnia helyette.

#### A fejléc megfejtve

A korábbi „nem tudjuk, mi van benne" álláspont **túl óvatos volt**: a fejléc
egyszerű, little-endian `uint32` mezőkből áll, és minden mezője
**visszaellenőrizhető a fájlnévből** — ez adja a megfejtés bizonyítékát.

| eltolás | típus | jelentés | ellenőrzés |
|---|---|---|---|
| `0x00` | u32 | `100` — formátumjelző (mind a 12 fájlban azonos) | — |
| `0x04` | u32 | **pontméret** | = a fájlnév mérete (11/12/13/14/16/18/20/28) ✅ |
| `0x08` | u32 | **súly** | = a fájlnév súlya (400 / 700) ✅ |
| `0x0c` | u32 | **dőlt** (0 = nem) | = a fájlnév utolsó mezője ✅ |
| `0x10` | u32 | 3–6, a mérettel nő (sorköz/alávágás?) | — |
| `0x14` | f32 | **skála** (`1.0`) | = a fájlnév `1.000000` mezője ✅ |
| `0x18` | u32 | eltolás a fájlon belül (mindig < fájlméret) | 44092 / 87722 / 164870 ✅ |
| `0x1c` | u32 | `256` — a glyph-tábla mérete | — |
| `0x20` | u32 | `256` | — |
| `0x24` | u32 | családfüggő (125 / 173) — a két HelveticaNeue-változatnál azonos | — |
| `0x28` | u32 | **a családnév hossza** | = a rákövetkező sztring hossza, bájtra ✅ |
| `0x2c` | bájtok | **a családnév** (`"Praxis Semi Bold/Heavy"`, `"HelveticaNeue MediumCond"`) | — |

A név után **4 × `int16` rekordok** táblája következik
(pl. `(98, 44, −2, −1)`, `(121, 44, −4, −1)`, `(85, 46, −1, −1)`) — a
mintázat egy glyph-atlasz koordinátáira és igazítási eltolásaira vall, de
**ez még nem bizonyított**; a rekordszerkezet pontos jelentése nyitott.

**Miért érdekes mégis:** a fájlkészlet önmagában megadja a Picasa felületének
**hiteles tipográfiáját** — két család (`Praxis Semi Bold/Heavy` és
`HelveticaNeue Condensed`/`MediumCond`), nyolc méret (11, 12, 13, 14, 16, 18,
20, 28) és két súly (400, 700). Ez a `constants.ui` betűtípus-hivatkozásainak
(`alabel_buttfont_win` = Praxis Semi Bold/Heavy 12) a **teljes** listája, és a
felületi hűséghez a glyph-adatok megfejtése nélkül is használható.

### 3.6 Egyéb runtime-fájlok — rövid jegyzetek

| Fájl | Típus | Megjegyzés |
|---|---|---|
| `missing.jpg` | JPEG (96×72) | Helyettesítő kép hiányzó/nem elérhető fájlokhoz (pl. levált hálózati meghajtó esetén). |
| `favicon.ico` | Windows ICO, 9 méret/színmélység-variáns (48×48…, 16 szín, 4 bpp) | A beépített webnézet/HTML-export favicon-ja. |
| `bezier.txt` | Szöveges, numerikus | 4 sornyi Bézier-görbe vezérlőpont (x, y, súly hármasok), feltehetően UI-animációs "easing" görbék definíciója; több alternatív görbekészlet ki van kommentezve (`#`). |
| `defaults.ini` | Szöveges INI | `[LifeScapeUpdater]` szekció: frissítés-ellenőrző URL-ek (`updates.picasasoftware.com`), olvasnivaló blog-feed, nyomtató-szolgáltatás URL-ek; `[Track]` szekció: `name=public` (kiadási csatorna/frissítési sáv jelzése). |
| `constants.ui` | Szöveges INI (`[Picasa2]` szekció) | UI-elrendezési konstansok (méretek, színek hexában, betűtípus-nevek/méretek) az album-lista, album-címke, thumbnail-kijelölés és "publish to web" UI-elemekhez — platform-specifikus variánsokkal (`_win`/`_mac` szuffix). |
| `properties.xml` | XML | A "Kép tulajdonságai" panel mezőlistája (FilePath, EXIF-mezők, GPS, Keywords, Regions/arcok, XMP stb.) — néhány mező `hide="1"` attribútummal rejtett/belső. |
| `geotag.kml` | XML (Google Earth KML sablon) | Placeholder-tokenekkel (`%<FOR_EACH_IMAGE>%`, `%UID%`, `%IMAGE_ROLL%`, `$[description]`) — a geotag export ebből generálja a fényképeket a Google Earth glóbuszra helyező `.kml` fájlt. |
| `xhairs.png`, `splashbk.jpg`, `picasaweb_logo.gif` | Kép | UI-grafikák (célkereszt geotaghez, indítóképernyő-háttér, Picasa Webalbumok logó). |
| `pwconfirm.html` | HTML | Picasa Webalbumok-feltöltés megerősítő beépített weboldala. |

---

## 4. Plugin-ök (`plugins/`)

| Elem | Valódi típus | Funkció |
|---|---|---|
| `Red.dll` | Windows PE32 DLL | **Nem csak vörösszem: ez a Picasa teljes gépi látás motorja.** A vörösszem-osztályok (`vrd_RedEyeCorrector`/`Detector`) mellett a szimbólumtábla tartalmazza a **`CNevenVisionDLL::IFace`** interfészt és egy teljes arcdetektáló készletet: `vbf_Cascade`, `vbf_BoostedClassifier` (`enn_BoostedClassifier`), `vde_LocalPoseDetector`, `vde_LocalDetectorSequence`, `erf_SlantDetector`, `vcf_PrecisionDetector`, `epi_PoseEst` (póz-becslés), `enn_MlpNet` (többrétegű perceptron). Vagyis a Picasa arcfelismerése a Google által **2006-ban felvásárolt Neven Vision** motorján fut, és ugyanez a DLL adja a vörösszem-detektálást is. |
| `red.cfg` | **Bináris adat**, NEM szöveges konfiguráció a fájlnév ellenére | 2,28 MB. A `Red.dll` futásidőben betöltött **tanított modellje** — boosted cascade detektorok + MLP-súlyok. Ez magyarázza az `.exe`-ben talált arcadat-formátumot is: `conf(%.3f),pan(%.3f),leye(%.3f,%.3f),reye(%.3f,%.3f),mouth(%.3f,%.3f)` — megbízhatóság, fejfordulás (pán-szög) és három arcpont (bal/jobb szem, száj), pontosan az a kimenet, amit egy Neven Vision-féle póz- és jellegzetespont-detektor ad. Ld. `picasa-ini-format.md`. |
| `ytITivo.yti` | Windows PE32 DLL (a `.yti` kiterjesztés ellenére futtatható kód) | **TiVo Desktop export plugin.** Stringek: `SOFTWARE\TiVo\Desktop\Beacon`, `TiVo Desktop\Photos\`, "Tivo Export" — képek exportálása/megosztása egy helyi TiVo Desktop-kiszolgáló felé (házimozi-integráció, kb. 2008–2015 korabeli funkció). |
| `CDVDR/CDVDR.yti` | Windows PE32 DLL | **CD/DVD-R (lemezre írás) export plugin** — a fájlnév ("CD/DVD-Recordable") és a szimbólum (`ytICDVDR`) alapján a "Mentés CD/DVD-re" funkciót valósítja meg (ez hívja elő a `cdautorun/` alatti autorun-alkalmazásokat, ld. 5. pont). |
| `expwebsites/expwebsites.yti` | Windows PE32 DLL, **beágyazott XML/i18n string-tábla** | **JAVÍTVA (2026-08-07):** NEM a `web/templates/` HTML-exportot vezérli, hanem egy **általános, futásidőben letöltött XML-protokollal irányított partner-feltöltő motor** (fotónyomtató-oldalak és webalbum-partnerek közös kerete). Bizonyíték: `CUploadProgram::StartSite/Login/XMLDownloadFailed`, „Photo Printer Site:", `XmlOverride`/`UrlOverride` felülbíráló kulcsok, album-név-validáció, kvóta- és cookie-ellenőrzés, telemetria-végpont. A HTML-sablonrendszert a főprogram maga dolgozza fel. |
| `expwebsites/expwebsites.psd` | Adobe Photoshop kép (32×31, RGBA) | A plugin ikonja/UI-grafikája. |

Mind a négy `.yti` fájl azonos `.pdb` build-útvonal-mintát hordoz
(`…\picasa39-stable\build\plugins\…`), tehát ezek a Picasa build-rendszerén
belül külön fordított modulok, amelyeket a főprogram futásidőben dinamikusan
tölt be — ez egy klasszikus **plugin-DLL architektúra**, csak a kiterjesztés
(`.yti` = "YT Interface"? — a `.yt`/`respack.yt` névkonvencióhoz hasonló
belső jelölés) van elrejtve a szokásos `.dll`-hez képest.

---

## 5. `cdautorun/` — CD-lemez autorun és Mac visszaállító alkalmazások

Ez a mappa a "Mentés CD/DVD-re" funkció kimenetének kiegészítője: amikor a
Picasa fényképeket éget lemezre, ezt a mappát is ráírja, hogy a lemez
Windowson autorun-nal, Mac OS X-en pedig egy natív `.app`-pal legyen
megnyitható/visszaállítható.

| Elem | Típus | Szerep |
|---|---|---|
| `PicasaCD.exe`, `PicasaRestore.exe` | Windows PE32 GUI EXE | Autorun diavetítő ill. "állítsd vissza a képeket a lemezről" segédprogram. |
| `Picasa CD Slideshow.app/`, `Picasa Restore.app/` | macOS alkalmazáscsomag (`Info.plist` + `PkgInfo` + `Resources`/`Frameworks`/`MacOS`) | Ugyanaz macOS-en. A `Info.plist` az alkalmazást "Picasa 2.0.5.322 Labs, © 2007-2009 Google Inc."-ként azonosítja — vagyis ez a két Mac-alkalmazás **jóval régebbi build**, mint a Picasa 3.9 fő programja, és változatlanul öröklődött verzióról verzióra. |
| `cdgo.ui` | **Valójában Adobe Photoshop (.psd) fájl**, 800×600 RGB, `.ui` kiterjesztéssel elrejtve | Az autorun-képernyő grafikai háttere/layoutja — a `.ui` kiterjesztés itt félrevezető, tartalma szerint kép, nem UI-leíró. |
| `cdgo.tre` | **Sima szöveges UI-elrendezési fájl** (nem bináris) | Egy `#define`-alapú makrónyelv (`m_offsetLT`, `m_centerX`, `m_hidden` stb.), majd elem-per-elem `XConstraint`/`YConstraint`/`MaintainOffset`/`Property` direktívák (pl. `cdgo/grad: root`, `XConstraint 0, -0.1, 0`). Ez a Picasa saját, rugalmas (relatív/horgonyzott) UI-elrendezés-leíró nyelve — hasonló családba tartozik, mint a `.fen` dialógusformátum, de kifejezetten a `cdgo` (CD-autorun-képernyő) UI-fájának pozicionálására. A fájl végén `#i18n--` jelzés látható (a további tartalom valószínűleg nyelvi feliratokat vezet be — ezt a terminológiai ügynök dolgozza fel). |
| `Download Picasa.url` | Windows internetes parancsikon (INI-szerű) | `URL=http://www.google.com/picasa` — egyszerű böngésző-hivatkozás a lemezről. |
| (a `hu.lproj` és társai a `.app` csomagokon belül) | macOS lokalizációs `.xml`/`.strings` | Külön ügynök dolgozza fel (terminológia). |

### 5.1 A `.lproj` lokalizáció — 37 nyelv, sima szövegben

A `.app`-csomagokban nyelvenként egy `i18n/` mappa van, benne **egyszerű,
UTF-8 XML** (nem `.strings`, a kiterjesztés ellenére):

| fájl | tartalom |
|---|---|
| `cdgo.xml` | `<tooltips>` / `<action type= target=>` — a felületi feliratok |
| `cdgo_stringres.xml` | `<resources>` / `<stringres id=>` — 88 sztring |
| `cdgo_resexport.xml` | egyetlen `<Win32Res/>` elem (üres) |

**Ez a séma bájtra ugyanaz, mint a `Picasa3i18n.dll`-be ágyazott két
erőforrás-fajta** — vagyis a DLL megfejtését egy **független, sima szöveges
forrás igazolja vissza.**

A magyar készlet néhány közvetlenül hasznosítható eleme:

| azonosító | magyar érték | megjegyzés |
|---|---|---|
| `il_FormatBigB` … `TB` | `%.0f bájt`, `%.0f KB`, `%.1f MB`, `%.1f GB` | a fájlméret-kiírás hiteles alakja: **„bájt"** kisbetűvel, MB-tól egy tizedes |
| `WinSystemPaths::MyPictures` | `Képek` | |
| `WinSystemPaths::MyVideos` | `Videók` | de a Mac-változat `Mozgófilmek` — a Picasa **önmagával sem volt következetes** |
| `CDGo::advanceslide` | `%1$s (%3$d / %2$d)` | a diavetítés állapotsora |
| `ytFileUtils::CopyProgress` | `%2$s / %1$s` | másolás-folyamat |

> **Figyelemre méltó:** a dátum/idő formátumok a magyar fájlban **nincsenek
> lefordítva** — `ytDateTime::Format1 = "%1$s %2$d, %3$d"` (hónap nap, év) és
> `Format3 = "%1$d:%2$02d:%3$02d %4$cM"` (12 órás, AM/PM). Ez az **angol**
> sorrend és óraformátum. A PicasaPy-ban ezt **nem kell másolni** — a helyes
> magyar alak (`ÉÉÉÉ. hónap N.`, 24 órás idő) a jó; ezt tudatos eltérésként
> érdemes kezelni, nem hűtlenségként.

---

## 6. `licenses/` — harmadik féltől származó komponensek

A mappa mindössze **két** licencfájlt tartalmaz — ez a teljes, hivatalosan
elismert harmadik féltől származó függőséglista a Picasa 3.9-ben:

| Fájl | Komponens | Licenc | Szerepe a Picasában |
|---|---|---|---|
| `adobe_xmp_toolkit.txt` | **Adobe XMP Toolkit** (© 1999–2010 Adobe Systems) | BSD License | XMP-metaadatok (Adobe-szabványos, RDF/XML-alapú képmetaadat) olvasása/írása a képfájlokban — ez magyarázza, hogy a Picasa miért tud XMP-t exportálni/importálni a `.picasa.ini` mellett. |
| `lcms.txt` | **Little CMS (lcms)**, © 1998–2010 Marti Maria Saguer | MIT-szerű engedékeny licenc | Színprofil-kezelés / ICC-színkonverzió (a `properties.xml`-ben is szereplő `ICC` mező feldolgozásához). |

**Mérnöktörténeti érdekesség:** a Picasa csapata mindössze két nyílt forráskódú
függőséget vállalt fel hivatalosan (a többi, pl. a saját `e*_`/`vrd_`
képfeldolgozó keretrendszer és a betűtípus-/UI-motor, zárt, házon belüli
kód) — ez arra utal, hogy a metaadat- (XMP) és színkezelés (lcms) volt az
egyetlen terület, ahol tudatosan iparági szabványkönyvtárra támaszkodtak,
minden más (képdekódolás, vörösszem-javítás, UI) saját fejlesztés volt. A
PicasaPy-nál mindkét terület (XMP, ICC-színprofilok) ma is jól lefedett,
karbantartott Python-könyvtárakkal kiváltható (pl. `python-xmp-toolkit`
vagy közvetlen XML-kezelés az XMP-hez; `littlecms`/`lcms2` Python-kötések
vagy `Pillow` beépített ICC-támogatás a színkezeléshez).

---

### 6.1 A licencfájlok mellett: egy harmadik, licenc nélküli komponens

A `licenses/` csak kettőt sorol fel (XMP Toolkit, Little CMS), de a
`Picasa3.exe` sztringjei egy harmadikat is elárulnak:

```
dcraw v9.19
```

A **dcraw** (Dave Coffin nyers-dekódere) közkincs jellegű, ezért nem igényelt
licencfájlt — de ott van a binárisban, és ez adja a Picasa RAW-támogatását.
A binárisból kiolvasható a kezelt formátumkészlet:

`.arw` · `.cr2` · `.dng` · `.mrw` · `.nef` · `.orf` · `.pef` · `.raf` ·
`.rw2` · `.srw` · `.x3f`

valamint tömörítés-változatok („Nikon NEF Compressed", „Sony ARW Compressed",
„Pentax PEF Compressed"), a `DNG Version:` mező és a
`Number of raw images: %d` (egy nyers fájl **több** képet is tartalmazhat).

**A színkezelés a Little CMS-en át teljes**: a binárisban ott a leképezési
szándékok teljes készlete — `Perceptual`, `Relative colorimetric`,
`Absolute colorimetric`, valamint a „preserving black ink/plane" változatok —,
továbbá `Embedded ICC profile: %s` és `AdobeRGB 1998 built-in` /
`AdobeRGB 1998 virtual profile`. A felületen ehhez tartozik a
„Színkezelés használata (ICC)" kapcsoló (`ui-audit-menus.md`).

Ez a két dolog összetartozik: a nyers fájlban **nincs** beégetett színtér, a
dekóder nyers RGB-t ad, amit profilozni kell — a Picasa erre használta az
lcms-t és a beépített AdobeRGB profilt.

**Objektív-adatbázis:** a binárisban **265 objektívnév** van (Canon EF…,
Sigma, Tamron, Tokina) — a Picasa a MakerNote objektív-azonosítóját emberi
névre oldotta fel a tulajdonságok panelen.

> **Következmény a PicasaPy-ra (#528):** a `scanner/filetypes.py` ma
> felismeri a nyers kiterjesztéseket, de a betöltés `cv2.imdecode`, aminek
> nincs RAW-dekódere — a nyers fájlok bekerülnek az indexbe, de nem jelenik
> meg belőlük kép. A dcraw utódja a **LibRaw** (`rawpy`); a bélyegképhez a
> beágyazott JPEG-előnézet (`extract_thumb`) elég.

---

## 7. Egyéb fájlok — egysoros jegyzetek

| Fájl | Típus | Szerep |
|---|---|---|
| `update/LifeScapeUpdater/currentVersion.ini` | Szöveges INI | A telepített build verziószáma (`versionID=3.9.141.259`) és a letöltendő frissítő-csomag neve (`downloadURL=update.exe`) — ezt hasonlítja össze a program a `runtime/defaults.ini`-ben megadott távoli `currentversion.ini`-vel a frissítés-kereséskor. |
| `i18n/uninstall_*.html` (29 fájl) | Statikus HTML | Az eltávolító (`uninstall.exe`) által megjelenített, nyelvenként lefordított "Biztosan eltávolítod a Picasát?" képernyők (angol alap + `bg, ca, cs, da, de, el, es, fi, fr, hi, hr, hu, id, it, ja, ko, lt, lv, nl, no, pl, pt-BR, ro, ru, sk, sl, sr, sv, th` nyelvi változatok). A `uninstall_hu.html` a magyar verzió. |
| `MovieThumb.exe` | Windows PE32 GUI EXE | **Videó-bélyegkép KÜLÖN FOLYAMATBAN.** Saját DirectShow-filtergráfot épít (null-renderer + memóriapuffer), a kinyert képkockát beágyazott libjpeg-gel kódolja; a QuickTime-fájlokat is ezen a gráfon át kezeli. Kapcsolói: `/savemovie`, `/playmovie`, `/resamplefile`. **Az elkülönítés oka feltehetően az izoláció**: a kodek-függő gráf-építés összeomolhat, és így nem viszi magával a főprogramot (következtetés, nem string-bizonyíték). |
| `Picasa3i18n.dll` | Windows PE32 DLL (~26,9 MB — a legnagyobb DLL a csomagban) | A teljes UI-szöveg lokalizációs erőforrás-DLL-je (minden támogatott nyelv string-táblája egy fájlban) — méretéből ítélve ez tartalmazza az összes nyelvi fordítást, amit az `.exe` futásidőben tölt be. |
| `qtsupport.dll` | Windows PE32 DLL | **Apple QuickTime-híd** — vékony közvetítő réteg (`CQuickTimeInterface`), maga NEM dekódol: dinamikusan betölti és hívja a rendszerre telepített `QuickTime.qts`-t a Component Manageren át. A tényleges dekódolást a `MovieThumb.exe` DirectShow-gráfja végzi. |
| `npPicasa3.dll` (a gyökérben) | Windows PE32 DLL, NPAPI-bővítmény | **Csak DETEKTÁLÁS.** MIME-típusa `application/x-picasa-detect`; mindössze a három kötelező NPAPI-belépőpontot exportálja, JavaScript-API (`invoke`/`hasMethod`/`NPObject`) NINCS benne. Egyetlen célja, hogy egy weboldal megkérdezhesse: *van-e telepítve Picasa?* |

---

## 8. Összegzés — mi hasznosítható közvetlenül a PicasaPy-ban

1. **`buttons/*.pbz` formátum** — egyszerűen portolható deklaratív
   plugin-mechanizmus (ZIP + XML + opcionális PSD-ikon); a `static`/`dynamic`
   gomb-megkülönböztetés és a `verb`/`param` akció-modell átvehető egy
   modern (JSON/YAML alapú) gomb-bővítmény rendszerhez.
2. **A web-export sablonnyelv (2. fejezet)** teljes egészében
   dokumentált és egyszerű — közvetlenül újraírható Pythonban (saját
   mini-parser vagy Jinja2-alapú kompatibilitási réteg), és az eredeti
   6 sablon (`whitebg`, `blackbg`, `greybg`, `whitefrm`, `blackfrm`,
   `greyfrm`, `xml`) tartalma megőrizhető/áthozható.
3. **`filters.txt` szemantikája** (4 szekció: könyvtár/fájl ×
   kizárás/kivétel) közvetlen mintaként szolgálhat a PicasaPy
   mappabeolvasó-szűrőjéhez.
4. ~~A **`respack.yt` bináris formátum**~~ — **MEGOLDVA** (2026-08-06),
   ld. [`picasa-respack-format.md`](picasa-respack-format.md): a formátum
   teljesen dekódolt, az eredeti UI-grafika és a 140 `.tre`
   elrendezés-forrás kinyerhető. A **`.ytf` betűtípus-formátum** továbbra
   is dokumentálatlan — de nem is kell: a PicasaPy natív
   rendszerbetűtípusokkal dolgozik.
5. **Licenc-lista** (XMP Toolkit, lcms) megerősíti, hogy a PicasaPy-nak
   ugyanezen a két területen (XMP-metaadat, ICC-színkezelés) kell jól
   dokumentált, karbantartott Python-könyvtárt választania a
   kompatibilitáshoz.
