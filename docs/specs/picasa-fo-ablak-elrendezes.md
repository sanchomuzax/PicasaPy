# A Picasa fő ablakának elrendezése — a forrásból

> 📐 **A KÖTELEZŐ, teljes méretlista külön lapon:**
> [`konyvtar-ablak-meretek.md`](konyvtar-ablak-meretek.md) — mind a 156
> `thumbui`-elem, sávonként, megvalósítási ellenőrzőlistával. Ez a lap a
> szerkezetet és a levezetést adja, az pedig a számokat.

A `respack.yt`-ből kinyert **140 `.tre` elrendezés-forrásfájl** alapján. Ezek
a Picasa saját, kényszer-alapú (constraint) UI-leíró nyelvén íródtak, és nem
képernyőkép-mintavételből származnak — a számok **pontosak**.

Kinyerés:

```bash
python3 tools/picasa/respack.py tre \
    research/copy_Picasa_3_7/Picasa3/runtime/respack.yt <celkonyvtar>
```

## A legfelső szint — `panelroot.tre`

A gyökér **egymást váltó, teljes méretű panelekből** áll, nem egymásba
ágyazott dobozokból:

| panel | mikor látszik |
|---|---|
| `mainuipanel` | a normál könyvtár-nézet (ez az alapértelmezett) |
| `makemoviepanel` | filmkészítés |
| `collagepanel` | kollázs |
| `acquirepanel` | importálás |

Mindegyik `m_scaleX` (vízszintesen nyúlik) és `YConstraint 0,0,tabdiv` …
`YConstraint 1,1,0` — vagyis **a `tabdiv` alatti teljes területet elfoglalja**.
A váltás `showtarget`/`hidetarget` párokkal megy, a `globaltabs` sávról.

Minden panelhez tartozik egy `addtofocus` lista — ez adja meg a
**billentyűzet-fókusz sorrendjét**.

## A könyvtár-nézet — `thumbui.tre`

### A hiteles méretek

| konstans | érték | mit jelent |
|---|---|---|
| **`HLISTOFFSET2`** | **240** | **a bal panel szélessége képpontban** |
| `searchtop` | 35 | a felső sáv magassága |
| `publishbottom` | −105 | az alsó sáv magassága (az ablak aljától) |
| `RIGHTDRAWEROFFSET` | 0 | a jobb fiók szélessége (alapból behúzva) |
| `LEFTDRAWEROFFSET` | 0 | |
| `tabdiv` | 0 | a globális fülsáv magassága (alapból nincs) |

> **A bal panel FIX 240 képpont, nem százalék.** A `hlistsizer` elemen ott a
> `Handler hsplitoffset HLISTOFFSET2` — vagyis **húzható elválasztó**, ami ezt
> a változót írja át. Az ablak átméretezésekor a bal panel **nem skálázódik
> arányosan**: a rács nő, a panel marad.

### Az elrendezés

```
mainuipanel
├── (felül, 35 px)          fejléc / keresősáv
├── listdecrect             a bal panel kerete: x 0 … HLISTOFFSET2
│                           y 35 … alul −105
├── hlistsizer              a húzható elválasztó (x = HLISTOFFSET2 − 4)
├── albumsback              a rács háttere: x HLISTOFFSET2 … jobb −RIGHTDRAWEROFFSET
│                           y 35 … alul −105
├── right_drawer            jobb fiók (alapból rejtett)
└── (alul, 105 px)          a képtálca és a vezérlők sávja
```

### Gyökér szintű (az egész ablakra lebegő) elemek

`largethumbs` · `smallthumbs` · `acquirebutton` · `viewswitch` ·
`horizonadjust` · `prev` · `next` · `fit` · `morethumbs` · `lessthumbs` ·
`soloview` · `uploadmgr` · `histogram` · `visitweb` · `circlecursor`

Ezek **nem a panelhierarchia része** — közvetlenül a `root`-hoz kötöttek,
tehát a panelváltás nem érinti őket.

## Az alsó sáv — `basecontrolset` (2026-08-15, #455)

Az `ui-audit-mainwindow.md` 5. fejezete ezt a sávot **képernyőképből** írta
le, és ott is kimondja, hogy a kép **1030 px-nél levágva**, tehát a tálca alsó
pereme nem mérhető. A forrás ezt kiváltja: a `thumbui.tre` a teljes sávot
megadja.

A sáv gyökere `thumbui/basecontrolset` (a `mainuipanel` gyereke,
`m_offsetLRB` — balra, jobbra, alulra kifeszítve), magassága a `publishbottom`
szerint **105 px**.

### A szerkezeti kulcs: a 36,5 %-os osztópont

A sáv **két részre oszlik**, és az osztópont az ablakszélesség
**0,365-szöröse**. Ez a szám a fájlban **öt különböző elemnél** ismétlődik —
nem véletlen, hanem a sáv tartószerkezete:

| elem | X-kényszer | jelentés |
|---|---|---|
| `scratchback` (**a képtálca**) | `0, 0, 5` … `1, .365, -15` | bal széltől 5 px → 36,5 % − 15 px |
| `webupload_rect` (zöld feltöltés-gomb) | `0, .365, -5` … `1, .365, 140` | az osztóponttól **145 px széles** sáv |
| `outputs` (a műveletsor) | `0, .365, 140` … `1, 1, -10` | a zöld gomb után → jobb szél − 10 px |
| `separator` | `0, .365, -3` … `1, 1, -17` | y **50–52** px: 2 px vonal, csak a jobb oldalon |
| `bcenterright` | `0, .365, 0` | ugyanaz az osztópont |

**Vagyis a képtálca az alsó sáv bal harmadát kapja**, a maradékban pedig
először a zöld feltöltés-gomb ül (fix 145 px), és csak utána jön a
Nyomtatás/E-mail/Exportálás sor.

### A képtálcán belül

```
thumbui/scratchback                     a tálca kerete
├── thumbui/scratch                     a bélyegképsor
│      XConstraint 0, 0, 5              5 px belső margó balról
│      XConstraint 1, 1, -50            ← JOBBRÓL 50 px SZABADON MARAD
│      YConstraint 0, 0, 5 · 1, 1, -5   5-5 px fent és lent
├── thumbui/scratchpadbase
│   └── thumbui/scratchlabel            „Selection” — m_centerXY (KÖZÉPRE)
├── thumbui/scratchhold      (+ _icon)  m_offsetRT
├── thumbui/scratchclear     (+ _icon)  m_offsetRT
└── thumbui/addtobuttcon                m_offsetRT
       + dropup_icon + addto_arrow
       Property customwidth 200 · maxrows 0
```

A bélyegképsor jobb oldalán **50 képpont van fenntartva** a három gombnak —
ez a képernyőképen látott „3-gombos oszlop", és a forrás megadja a
szélességét is.

### A három gomb — IKON, felirat nélkül

A `thumbui_text.tre`-ben mindhárom gomb `Label` sora **ki van kommentelve**
(`#Label thumbui/scratchhold` / `#Hold`), csak a `Tooltip` él. A gombok tehát
az eredetiben is **csak ikonok**, buboréksúgóval:

| elem | buboréksúgó (angol) | funkció |
|---|---|---|
| `scratchhold` | *Hold selected items* | a kijelölés rögzítése (ne söpörje el a következő) |
| `scratchclear` | *Clear items from the selection* | a tálca ürítése |
| `addtobuttcon` | *Add selected items to an Album* | felfelé nyíló menü (`dropup_icon` + `addto_arrow`) |

A `scratchlabel` szövege **`Selection`**, és `m_centerXY` — vagyis üres
tálcánál a felirat **a tálca közepén** áll, nem a bal szélén.

### A jobb szél — `metadata_group` és `scale_group`

Mindkettő `m_offsetRT` a `basecontrolset`-en (jobb felső sarokhoz kötve):

- **`metadata_group`** — a négy kerek kapcsoló. A kötésekből a sorrend
  balról jobbra: **`people_toggle` · `places_toggle` · `tags_toggle`**
  (mind `m_offsetLT`), és jobbra zárva a **`properties_toggle`**
  (`m_offsetRT`). Ez pontosan a képernyőképen látott személy / hely /
  címke / infó négyes.
- **`scale_group`** — `loupehit` (nagyító) + `scalecontainer`
  (nagyítás-csúszka).

⭐ **A KETTŐ SORRENDJE (#2305):** a lenti koordináta-táblából **545 > 525**,
vagyis a `scale_group` (366…525) **megelőzi** a `metadata_group`-ot
(545…785). Balról jobbra tehát: **nagyító → csúszka → négy panelkapcsoló**.
A számok eddig is itt álltak, de a sorrend nem következett belőlük
olvasásra, és a QML fordítva rakta ki őket — a tulajdonos képernyőmentése
mutatta meg. A gombok emellett **kizárólag ikonosak**: a `buttcon_*`
típusnevek ikon-gombot jelölnek, és a 60 × 24-es cellába a felirat csak
levágva férne. Nálunk a felirat a buboréksúgóba és az akadálymentesítési
névbe került (`Accessible.name`).

*Bizonyítottsági fok: megerősített* — a `thumbui.tre` 300–350. és 620–700.
sorai, a feliratok a `thumbui_text.tre` 94–121. soraiból. A `m_offset*`
makrók jelentése (a kötési oldal) a kényszerekből egyértelmű, a hozzájuk
tartozó **alapértelmezett margók számértéke viszont nem szerepel a
`.tre`-ben** — ahol számot írok fent, az mind explicit `XConstraint`/
`YConstraint`.

## Eltérés a PicasaPy-tól

A „nálunk" oszlop **kirajzolva mérve** (#587, a teljes `Main.qml`
1280/1600/1920 px-es ablakban — a mérő őr:
`tests/app/qml_functional/test_fo_ablak_elrendezes_587.py`):

| | eredeti | nálunk | állapot |
|---|---|---|---|
| bal panel szélessége | **240 px fix**, húzható | `folderPaneWidth`, alap **230** | ❌ **nyitva** — az alapérték a `FOLDER_PANE_WIDTH_DEFAULT`-ban (`app/controller.py`) és a `Main.qml` tartalék-értékében él |
| a bal panel viselkedése átméretezéskor | **nem skálázódik** | nem skálázódik (mérve: 230 mindhárom ablakszélességen) | ✅ |
| felső sáv | 35 px | **35 px** (#587 előtt 34) | ✅ |
| `importbutton` | 111 × 22 | **111 × 22** (#587 előtt 100 × 24) | ✅ |
| `searchcontainer` | 388 × 30 | **388 × 30** (#587 előtt 300 × 24) | ✅ |
| alsó sáv | 105 px | 20 + 85 = **105 px** | ✅ (#1420) — a magassággal EGYÜTT a tálca-tartalom is átépült: 36,5 %-os osztópont, 81 px-es képtálca, 141 × 35-ös zöld gomb |
| a sáv belső osztása | 36,5 % | **36,5 %** | ✅ (#1420) — képtálca \| zöld gomb \| műveletsor |

> **A `design-guide.md` két, egymásnak ellentmondó értéket tartalmazott**
> (386 px ≈ 20 %, illetve 210 px ≈ 26 %), és azt írta, hogy „arányosan
> skálázandó". **Mindkettő téves volt**: a forrás szerint 240 px, fix,
> húzható elválasztóval. A képernyőkép-mintavételből származó becslést itt
> a forráskód felülírja. **A #587 mindkét helyet kijavította** — a
> `design-guide.md` mostantól a forrásra mutat, és a fix/skálázódó
> megkülönböztetést is kimondja.

## Elérhető, még fel nem dolgozott elrendezések

A 140 fájlból eddig a `foldermgr`, a `panelroot` és a `thumbui` van
feldolgozva. További, közvetlenül hasznos források:

`editpanel` (szerkesztő) · `oneup` (nagy nézet) · `headerpanel` ·
`peoplepanel` · `tagpanel` · `searchoptions` · `printpanel` ·
`collagepanel` · `makemoviepanel` · `slideshowctrls` · `moviecontrols` ·
`video_control_bar` · `propertiespanel` · `nav` · `rightdrawerpanel`

Mindegyik ugyanígy pontos geometriát ad.

## A beállítás-nyilvántartó és a 39 alapérték (`0x006e0cb0`, 2026-08-16)

Egyetlen 590 bájtos függvény regisztrálja a Picasa **globális
beállításait** az alapértékükkel együtt. A minta végig azonos:

```asm
push  <alapérték>
push  esi                        ; a beállítás-nyilvántartó
mov   eax, <"kulcs">
call  0x006e0a70                 ; regisztrálás
```

Ez az **igazságforrás az alapértékekre**: ezek lépnek életbe, ha a
registryben nincs érték.

### Logikai beállítások

| kulcs | alapérték | mit kapcsol |
|---|:---:|---|
| `AutoUpgradeCheck` | **1** | frissítés-ellenőrzés |
| `AutoUpgradeAsk` | **0** | rákérdezés frissítés előtt |
| `AutoInfoCheck` | **1** | információ-ellenőrzés |
| `UITransitions` | **1** | felületi átmenetek (animáció) |
| **`ShowTooltips`** | **1** | **buboréksúgók** |
| `SingleClickExit` | **0** | egykattintásos kilépés |
| `disposepreviews` | **0** | előnézetek eldobása |
| `DoNotConfirmDeleteFromDisk` | **0** | „ne kérdezz lemezről törléskor" |
| `DoNotConfirmRemoveFromAlbum` | **0** | „ne kérdezz albumból eltávolításkor" |
| `autoexclude` | **1** | automatikus kizárás |
| `PrintProxyPreview` | **1** | nyomtatási előnézet proxyval |
| `PWAStarred` | **0** | webalbum: csillagozottak |
| `PWASyncOrder` | **1** | webalbum: sorrend szinkronizálása |
| `PWAStriped` | **0** | webalbum: csíkozott |
| `PWAUseHiQualityJPEG` | **0** | webalbum: jó minőségű JPEG |
| `LoopSlideshow` | **0** | diavetítés ismétlése |
| `PlayMP3Tracks` | **1** | MP3-sávok lejátszása |
| `BgFaceDetectThread` | **1** | háttér-arcfelismerés |
| `FRAddSuggesetions` | **1** | arcjavaslatok *(a **név elgépelve** az eredetiben!)* |
| `FREnableUploads` | **1** | arcfelismerés: feltöltés |

### Támogatott fájltípusok

| kulcs | alapérték |
|---|:---:|
| `SupportTIF` | **1** |
| `SupportWEBP` | **1** |
| `SupportBMP` | **1** |
| `SupportPSD` | **1** |
| `SupportRAW` | **1** |
| **`SupportGIF`** | **0** |
| **`SupportPNG`** | **0** |
| `SupportTGA` | **0** |
| `SupportAudio` | **0** |
| `SupportMovies` | *(számított)* |

#### ⚠️ MÉRÉS a tulajdonos valódi katalógusán — és egy MEGDŐLT állítás a saját kódunkban (2026-09-04, #2344)

A fenti kapcsolók **nem elméletiek**: a tulajdonos 2026-08-22-i
katalógusában (2776 valódi fotósor) a kiterjesztések megoszlása

| kiterjesztés | darab |
|---|---:|
| `jpg` | 2416 |
| `bmp` | 206 |
| `png` | 125 |
| `mp4` | 17 |
| `jpeg` | 8 |
| `tif` | 3 |
| **`webp`** | **1** |

⇒ **A Picasa 3.9 INDEXELI a WebP-t.** A bizonyíték háromszoros:

1. a **`SupportWEBP` alapértéke 1** (a fenti tábla, `0x006e0cb0`);
2. a bináris ismeri a kiterjesztést: `.webp` (`0x00467ca0`),
   `*.webp;` a szűrőlistában (`0x00520220`), `*.webp` (`0x005e6a20`);
   a `SupportWEBP` kulcs **hat** függvényben szerepel, köztük a
   beállítás-nyilvántartóban és a Beállítások-kezelőben (`0x006e1100`);
3. a tulajdonos valódi `thumbindex.db`-jében **ott van egy `.webp` fájl**
   — tehát a Picasa a gyakorlatban is beolvasta.

⛔ **Ezzel MEGDŐLT a saját kódunk állítása.** A
`src/picasapy/scanner/filetypes.py` fejléce ezt írja:

> *„A WebP szándékosan hiányzik — a Picasa nem támogatta; felvétele
> későbbi, tudatos bővítés lehet."*

A `PHOTO_EXTENSIONS` valóban nem tartalmazza a `.webp`-t (`:12–14`),
tehát a szkennerünk **nem is látja** ezeket a fájlokat. Jegy: **#2344**.

⚠️ **Amit ez NEM mond meg:** a `SupportGIF` és a `SupportPNG` alapértéke
**0**, a katalógusban mégis **125 PNG** van. Vagyis a kapcsoló vagy be lett
kapcsolva, vagy nem a beolvasást vezérli — **ez NINCS mérve**, és a
`filetypes.py` feltétel nélküli szűrőjével együtt külön kérdés (a jegy
külön pontja).

#### A `Support*` kapcsolók HATÓKÖRE — mérve (2026-09-04, #2344)

A fenti kérdés első fele eldőlt: **hol olvassa a program ezeket a
kulcsokat?** Négy olvasó van, mindegyik megnevezve:

| olvasó | hány kapcsolót olvas | mi ez a függvény — a SAJÁT sztringjei alapján |
|---|---:|---|
| **`0x00520220`** (2938 b) | 10 | a **fájlmegnyitó szűrője**: `CAcquireUI::picsfilter`, `CAcquireUI::picsmovfilter`, `CAcquireUI::allfilesfilter`, és a kiterjesztés-csoportok (`*.jpg;*.jpe;*.jpeg;`, `*.bmp;`, `*.psd;`, `*.tif;*.tiff;`, **`*.webp;`**, `*.gif;`, `*.png;`, `*.tga;`, a videós lista) |
| **`0x0051ceb0`** (901 b) | 10 | kapcsoló-maszkot épít; **hívói:** `0x0051d270` (`import_share`) és `0x0070b050` (`acquirepanel/importstatus1`/`2`) ⇒ az **importálás** ága |
| **`0x004e04a0`** (1256 b) | 12 (`SupportTXT`-vel) | hívója `0x004183c0` |
| **`0x004183c0`** (1390 b) | 7 | **indulási/adatbázis-ág**: `Other Stuff`, `#db3\`, `dbVersion`, `RootPath`, `Filters`; hívója `0x00402f90`, a gyűjtemény-nevek helye (`Folders on Disk`, `Hidden Folders`, …) |

A kulcsnevek adatcímei: `SupportBMP` `0x00c80fd4` · `SupportPSD`
`0x00c80fe0` · `SupportTIF` `0x00c80fec` · **`SupportWEBP` `0x00c80ff8`** ·
`SupportPNG` `0x00c81004` · `SupportGIF` `0x00c81010`.

⇒ **Mind a négy olvasó az IMPORTÁLÁS/megnyitás vagy az indulás ágán van.**
Ez egybevág a mérési ellentmondással: a `SupportPNG` alapértéke **0**, a
tulajdonos katalógusában mégis **125 PNG** van — a kapcsoló tehát nem
egyszerűen „ez a formátum bekerül-e a katalógusba" jelentésű.

⚠️ **Ami NYITVA marad (örökölt, a munkasorba került):** hogy a **figyelt
mappák pásztázása** egyáltalán megnézi-e ezt a maszkot. Ehhez a pásztázó
ágat kell azonosítani, és megmutatni, hogy nem hívja a `0x0051ceb0`-t (vagy
hívja). **A négy olvasó közt nincs pásztázó függvény** — de ez negatív
állítás egy nem kimerítő listán, ezért nem elég.

**Következmény a mi oldalunkra (a #2344-hez):** a szűrőnk feltétel
nélküli, és a tulajdonos katalógusa szerint az eredeti is **indexeli** a
PNG-t és a BMP-t az alapérték ellenére ⇒ **NE építsünk kapcsolókat** a
`filetypes.py`-ba emiatt; a #2344 hatóköre marad a `.webp` felvétele.
| `SupportQuicktime` | *(számított)* — `0x006e0e1c`: egy vizsgálat eredménye (`setne al`), tehát **„van-e telepítve QuickTime"** |

> ⚠️ **A PNG és a GIF alapból KI van kapcsolva.** Ez ellentmond a
> megérzésnek, de a kód egyértelmű: `0x006e0e83 push 0` → `SupportPNG`,
> `0x006e0e76 push 0` → `SupportGIF`.

### Számértékek

| kulcs | alapérték | cím |
|---|---:|---|
| `PWADefaultSize` | **1600** (`0x640`) | `0x006e0d7a` |
| `PWADefaultSizeES` | **2048** (`0x800`) | `0x006e0d8d` |
| `FRSuggestionThreshold` | **85** (`0x55`) | `0x006e0ed5` |
| `FRSortThreshold` | **85** (`0x55`) | `0x006e0eed` |

### Külön kezelt

`ytHLocal::lang` (nyelv), `PrinterQuality`, `PrintResamplerQuality`,
`PWAShareAccess` — ezek nem a logikai regisztrálón mennek át; az
alapértékük külön ágban dől el.

### Amit ebből a PicasaPy visz

A **fájltípus-kapcsolók** és a **megerősítés-kihagyó** beállítások
közvetlenül átvehetők. A webalbumos (`PWA*`) és a frissítés-ellenőrző
kulcsok nálunk értelmezhetetlenek.

*Bizonyítottsági fok: megerősített* (a regisztráló hívások mind a 39-re
kiolvasva, az alapérték minden esetben a hívás előtti `push`).

## A Beállítások párbeszéd kezelője és a kulcsai (`0x006e1100`, 2026-08-16)

A 9 494 bájtos `0x006e1100` a **Beállítások (Opciók) párbeszéd** kezelője —
az osztálynév a sztringjeiből azonosítható: `CGeneralPrefsPage`. A 79
hivatkozott sztringje megadja, **melyik vezérlő melyik beállítás-kulcsot
írja**.

### A vezérlő-azonosítók (a `.fen`/`.tre` oldalról)

`web_albums_tab` · `enablefruploads` · `tags_group` ·
`uploadcontactphotos` · `usagestats` · `privacy` · `autoupdate` ·
`importdest` · `mailprog` · `picsize` · `defaultmail` · `haswatermark` ·
`enablefacedetection` · `enablefacesuggestions` · `persistfacetofile` ·
`facethresh0` · `facethresh1` · `autoProxy` · `loglevel` · `print%d`

### Tizenöt kulcs, ami a REGISZTRÁLÓBAN nincs benne

A `0x006e0cb0` (az előző szakasz) 39 kulcsot regisztrál alapértékkel. A
párbeszéd ezeken felül **további tizenötöt** ír:

| kulcs | melyik fül |
|---|---|
| `ReportStats` | Általános — használati statisztika |
| `PersistFaceToFile` | Névcímkék |
| `confirmsync::disable` | Általános |
| `MP3SlideshowPath` | Diavetítés |
| `PWAWatermark` | Google Fotók |
| `EmailSinglePicture` | E-mail |
| `EmailMovie` | E-mail |
| `UseHTMLMailer` | E-mail |
| `EmailPrepType` | E-mail |
| `DoNotPromptForEmailPref` | E-mail |
| `EmailExportSize` | E-mail |
| `ProxyUser` | Hálózat |
| `ProxyPass` | Hálózat |
| `Conn:ProxyMethod` | Hálózat |
| `LogLevel` | Hálózat |

> ⚠️ A `ProxyUser` / `ProxyPass` **jelszót tárol**. A PicasaPy-nak ezt nem
> kell átvennie; ha valaha mégis, akkor **nem** a beállításfájlba.

### A feltöltési méret öt választása — pontos feliratokkal

| erőforrás-kulcs | EN | HU |
|---|---|---|
| `CGeneralPrefsPage::Original` | Original size (slowest upload) | **Eredeti méret (leglassabb feltöltés)** |
| `CGeneralPrefsPage::2048` | Best for web sharing (2048px) | **Ideális internetes megosztáshoz (2048 képpont)** |
| `CGeneralPrefsPage::1600` | Recommended: 1600 pixels (…) | **Ajánlott: 1600 képpont (nyomatokhoz, képernyővédőkhöz és megosztáshoz)** |
| `CGeneralPrefsPage::1024` | Medium: 1024 pixels (for sharing) | **Közepes: 1024 képpont (megosztáshoz)** |
| `CGeneralPrefsPage::800` | Small: 800 pixels (for blogs and webpages) | **Kicsi: 800 képpont (blogokhoz és weboldalakhoz)** |

Az alapérték a `PWADefaultSize` = **1600** (az előző szakasz) — vagyis az
**„Ajánlott"** tétel a kiválasztott.

### Két járulékos lelet

1. **A „Google Fotók" fül** (`CGeneralPrefsPage::WebAlbumsTabEs` → „Google
   Photos" / **„Google Fotók"**) — a webalbum-fül a késői kiadásokban ezt a
   nevet viseli, nem „Picasa Webalbumok".
2. **Nyelvváltás megerősítése**: `CGeneralPrefsPage::LangChange` —
   „Módosítja a Picasa kezelőfelületének nyelvét?\n\nA változás a program
   következő megnyitásakor lép érvénybe."

*Bizonyítottsági fok: megerősített* (a függvény mind a 79 hivatkozott
sztringje, és a feliratok a `*text.tre` szövegforrásból).

---

## A MEGŐRZÖTT elrendezés-állapot — mit ír ki a Picasa, hova, mikor (2026-09-03)

> **Bizonyítottság: megerősített.** Minden állítás mellett cím vagy
> `.tre` fájl + sor. Az egyik állítás **kimerítő negatív** — három
> egymástól független lekérdezéssel.

### 1. A főablak pozíciója és mérete

| kulcs | szakasz | formátum | cím |
|---|---|---|---|
| `mainwinpos` | `Preferences` | **`rect(%ld %ld %ld %ld)`** | `0x00575f50` (visszaállítás), `0x005760e0` (mentés) |
| `mainwinismax` | `Preferences` | maximalizált-jelző | ugyanott |

A maximalizált állapot **külön kulcs**, nem a téglalapba kódolva — a
normál geometria így megmarad a maximalizálás visszavonásához.

### 2. ⛔ `HLISTDIV` és `VLISTDIV` — BEÍRVA, de SOHA NEM OLVASVA

Az induló kód (`0x00565920`, 969 bájt) két `resvars`-változót vet be:

```asm
0x00565974  push 0xc8e67c   ; "HLISTDIV"
0x00565979  push 0xc7fe64   ; "resvars"
0x0056598c  call 0x407630   ; kiolvasás
…                            ; üres/hiányzó?
0x00565a02  push 0xc8e688   ; "0.216406"   <- ALAPÉRTÉK
0x00565a20  call 0x407760   ; beírás
0x00565a2a  push 0xc8e694   ; "VLISTDIV"
0x00565ab3  push 0xc8e6a0   ; "0.1"        <- ALAPÉRTÉK
```

| változó | alapérték | hol |
|---|---|---|
| `HLISTDIV` | **`0.216406`** | `0xc8e67c` / `0xc8e688` |
| `VLISTDIV` | **`0.1`** | `0xc8e694` / `0xc8e6a0` |

A beírás **feltételes**: csak akkor, ha a kulcs hiányzik vagy üres
(`0x005659ee` állítja a jelzőt, `0x00565a00` ágazik el rajta).

**És ezzel vége — semmi nem olvassa őket.** Három, egymástól független
lekérdezés:

1. **`string_xrefs` index:** mindkét névre pontosan **egy** hivatkozó
   függvény, a `0x00565920`.
2. **Nyers bájtminta a teljes PE-n** a sztringek CÍMÉRE (`0xc8e67c`,
   `0xc8e694`, és a két alapérték-sztringé is): szekciónként végigpásztázva
   **1–1 hivatkozás**, mind a `0x00565920`-ban.
3. **Mind a 141 `.tre` erőforrás** végiggrepelve: **0 találat** — egyetlen
   felületleíró sem hivatkozik rájuk.

Nincs dinamikusan összerakott név sem: a teljes fájlra futtatott
`[ -~]{0,12}LISTDIV[ -~]{0,12}` reguláris keresés **pontosan a két
literált** adja, `%sLISTDIV`-szerű formátumsztring nincs.

⇒ **Elsőindulási maradék. NE valósítsuk meg.**

> ⚠️ **Miért került ide külön szakasz:** a `0.216406` első ránézésre a bal
> panel **arányos** szélességének látszik (a lap fenti táblája viszont fix
> **240 képpontot** mond). A negatív eredmény ezt a csapdát zárja le: a
> `HLISTDIV` nem a könyvtár osztóvonala. A könyvtár osztója a
> `HLISTOFFSET2`, ahogy eddig is állt:
>
> ```
> thumbui.tre:517   XConstraint 0, 0, HLISTOFFSET2=240, -4
> thumbui.tre:518   Handler hsplitoffset HLISTOFFSET2
> ```
>
> **A lap eddigi állítása („FIX 240 képpont, nem százalék") tehát
> MEGERŐSÍTVE**, nem cáfolva.

### 3. Az induláskori felület-állapot alkalmazója — `0x0040bf70`

A 3486 bájtos függvény a `Preferences`-t és a `resvars`-t olvassa, és
ebből állítja be **név szerint** a felületi elemek láthatóságát. Az általa
érintett elemek és kulcsok (a `string_xrefs` teljes listája erre a
függvényre):

| kulcs / változó | érintett elem |
|---|---|
| `RIGHTDRAWEROFFSET` | `thumbui/right_drawer`, `thumbui/rightdrawerpanel` |
| `LEFTDRAWEROFFSET`, `left_drawer_open` | `editpanel/toggle_left_drawer` |
| `LastCaptionButton` | `editpanel/captionbutton` |
| `EnableScreenCap` | — |
| `hosting`, `UIFolder` | a webes szolgáltatások megléte |
| — | `thumbui/webcambutton`, `thumbui/visitweb`, `thumbui/uploadmgr`, `thumbui/webmode` |
| — | `searchoptions/webview`, `searchoptions/label_webview`, `searchoptions/dupesearch` |
| — | `rightdrawerpanel/propertiespanel` · `/tagpanel` · `/peoplepanel` · `/geopanel` |
| — | `printpanel/nextbutton`, `printpanel/prevbutton` |
| — | `editpanel/picnik`, `editpanel/adorner_container`, `publish/picsizemenu`, `thumbui/addtobuttcon`, `thumbui/albums` |

⇒ **A megszűnt webes szolgáltatásokhoz kötött gombok (`visitweb`,
`uploadmgr`, `webmode`, `webcambutton`) nem külön ágon, hanem EBBEN az
egy függvényben kapcsolódnak ki-be.**

### 4. `hviewtoggle` — nem vezérlő, hanem a nézetváltó pár TARTÓJA

A lefedettségi mérés `thumbui/hviewtoggle`-t „bizonytalan"-ként hozta. A
forrás egyértelmű:

```
thumbui.tre:406   thumbui/folderview: thumbui/hviewtoggle
thumbui.tre:407-408                   (#Property showtarget leftindent/rightindent — kikommentelve)
thumbui.tre:409   Property prenotify 1
thumbui.tre:412   thumbui/flatview:   thumbui/hviewtoggle
thumbui.tre:415   thumbui/hviewtoggle: thumbui/buttonbarsets
```

⇒ **`hviewtoggle` a `buttonbarsets`-ben ülő csoport**, két gyerekkel:
`folderview` és `flatview`. A mappanézet ↔ egyszerű nézet váltás tehát az
eredetiben **eszköztár-gombpár**, nem csak menütétel. A két gomb mérete a
#587 mérése szerint 2 × 30 × 22; a hiányuk a **#1421**-ben van
nyilvántartva.

### 5. Nálunk — MÉRVE (2026-09-03)

| | eredeti | nálunk | állapot |
|---|---|---|---|
| főablak-geometria | `Preferences/mainwinpos` = `rect(l t r b)` + `mainwinismax` | `QSettings` `window/x·y·width·height·maximized`, virtuális asztalhoz igazítva (`app/window_geometry.py`, #192) | **megvan** |
| bal panel szélessége | `HLISTOFFSET2 = 240`, húzható (`Handler hsplitoffset`) | alap **240**, húzható `SplitView`, `QSettings` `view/folderPaneWidth` (`app/controller.py:86`) | **megvan** |
| a húzás korlátai | **NINCS fix korlát** (ld. 6.) | 160 … 600 (`_clamp_folder_pane_width`, `controller.py:91`) | a miénk **saját kiegészítés**, nem mért érték |
| mappanézet ↔ egyszerű | eszköztár-gombpár (`hviewtoggle`) | csak a Nézet menüben (#1454) | **hiányzik** → #1421 |
| `HLISTDIV` / `VLISTDIV` | beírva, sosem olvasva | nincs | **helyesen nincs** |

### 6. A húzható osztó kezelője — és a 240 MÁSODIK, független előfordulása

A `.tre` `Handler hsplitoffset` sora egy gyártó-osztályra mutat:

| lépés | cím |
|---|---|
| a névadó csonk (`"hsplitoffset"`) | `0x0040aa80` → `0xc7fbd0` |
| `HSplitOffsetCreator::vftable` | `0x0060cbd0` · `0x0040aa80` · **`0x009da130`** · `0x00401570` |
| a gyártó `Create` metódusa | **`0x009da130`** (113 b) |
| a létrehozott kezelő | `ytSplitterOffsetHandler`, **`0x009d9d80`** (712 b) |

A `Create` a `0x009c9de0`-nal olvassa ki a `resvars`-változót, foglal egy
`0x1c` bájtos objektumot, és **beleteszi a `240.0f`-ot**:

```asm
0x009da164  fld  dword ptr [0xcf48b0]   ; 240.0f
0x009da16e  fstp dword ptr [eax + 0x18]
```

⇒ **A 240 kétszer, egymástól függetlenül van rögzítve:** a
`thumbui.tre:517` (`HLISTOFFSET2=240`) és a `0xcf48b0` kódkonstans.

**A korlátokról — kimerítő negatív:** a `ytSplitterOffsetHandler` teljes
712 bájtos törzsében **nincs egyetlen abszolút című lebegőpontos konstans
sem**, és nincs `cmp <reg>, <immediate>` sem; az egyetlen immediate-
összehasonlítás az esemény-típusé (`cmp dword ptr [esi+8], 0x1b`). Az
összes lebegőpontos összehasonlítás a konstruktorban eltárolt
`[obj+0x18]`-ra és futásidejű értékekre megy.

⇒ **Az eredetiben nincs beégetett alsó/felső határ a bal panel
szélességére.** A mi `160 … 600` korlátunk (`controller.py:91`) tehát nem
egy mért eredeti érték átvétele, hanem **saját kiegészítés**. Ez nem
feltétlenül baj — de ne hivatkozzunk rá úgy, mintha az eredetiből jönne.

---

## A könyvtár-nézet alsó sávjának JOBB SZÉLE — teljes elemlista és három mért NEGATÍV eredmény (2026-09-04, #2305)

> **Bizonyítottság: megerősített.** Minden állítás forrása a `respack.yt`-ból
> kicsomagolt `thumbui.tre` / `thumbui_text.tre`, illetve a rétegfejlécek
> `int16 x0,y0,x1,y1` mezői. A tulajdonos 2026-09-04-i képernyőmentése
> (`Picasa 3`, 1920 × 1200) mindhárom állítást megerősíti.

### A teljes sorrend, mért koordinátákkal

Mindkét csoport `m_offsetRT` a `basecontrolset`-en (jobb felső sarokhoz kötve,
`thumbui.tre:283` és `thumbui.tre:297`), tehát **a sáv jobb szélén** ülnek,
ebben a sorrendben. A koordináták a `respack.yt` rétegfejléceiből
(`respack.yt:3241330` `scale_group`, `respack.yt:3243743` `metadata_group`):

| # | elem | x | szélesség | y | magasság |
|---|---|---|---|---|---|
| 1 | `thumbui/scale_group` | 366…525 | 159 | 448…475 | 27 |
| 1a | └ `thumbui/loupehit` (`m_offsetLT`) | 366…391 | **25** | 451…470 | 19 |
| 1b | └ └ `thumbui/loupe` (ikon) | 368…391 | 23 | 452…468 | 16 |
| 1c | └ `thumbui/scalecontainer` (`m_offsetLT`) | 398…525 | **127** | 448…475 | 27 |
| 2 | `thumbui/metadata_group` | 545…785 | 240 | 448…472 | 24 |
| 2a | └ `people_toggle` (`m_offsetLT`) | 545…605 | 60 | 448…472 | 24 |
| 2b | └ `places_toggle` (`m_offsetLT`) | — | 60 | — | 24 |
| 2c | └ `tags_toggle` (`m_offsetLT`) | — | 60 | — | 24 |
| 2d | └ `properties_toggle` (**`m_offsetRT`**) | — | 60 | — | 24 |

⇒ **A nagyítás-csúszka MEGELŐZI a négy panelkapcsolót** (525 < 545). Ez eddig
is benne volt a lapban számként, de a **sorrend** nem következett belőle
olvasásra; most ki van mondva.

### ⛔ NEGATÍV 1 — a négy kapcsolónak NINCS felirata

A `thumbui_text.tre` 55–65. sorában mind a négy elemnek **kizárólag `Tooltip`
sora van**, `Label` sora egyiknek sincs. *(Kontroll: közvetlenül alatta
`Label thumbui/timelinebutton` áll, tehát a fájl ismeri a `Label` kulcsszót;
és a `#Tooltip thumbui/addkeywords` mutatja, hogy a kikommentelt sor is
felismerhető alak.)*

A `thumbui.tre` 255–281. sora szerint mindegyik kapcsoló egyetlen gyereket
tartalmaz — a saját `_icon` rétegét, középre kényszerítve
(`m_centerX`/`m_centerY`, illetve `XConstraint 0.5, 0.5, 1…2`). **Szövegelem
nincs bennük.**

Az angol buboréksúgók (`thumbui_text.tre`), a hivatalos magyarral
(`referencia/panel-feliratok-hu.tsv` 5150–5153):

| elem | angol | magyar |
|---|---|---|
| `people_toggle` | Show/Hide People Panel | Az Emberek párbeszédpanel megjelenítése/elrejtése |
| `places_toggle` | Show/Hide Places Panel | A Helyek párbeszédpanel megjelenítése/elrejtése |
| `tags_toggle` | Show/Hide Tags Panel | A Címkék párbeszédpanel megjelenítése/elrejtése |
| `properties_toggle` | Show/Hide Properties Panel | A Tulajdonságok párbeszédpanel megjelenítése/elrejtése |

⚠️ **A típusnév NEM bizonyíték — épp az ellenkezőjét sugallja.** A négy gomb
sminkje `buttcon_LS_text_RC` / `_MS_text_RC` / `_RS_text_RC`, tehát a **neve
tartalmazza a `text` szót**. A sminkfájl megnyitva viszont
(`referencia/tre-eroforrasok/buttcon_LS_text_RC.tre`) csak három
állapot-képet és a `button_buttcon` tulajdonságot deklarálja — **feliratelemet
nem**. A `text` a fájlnévben a szegmens-grafika változatát jelöli
(a másik változat a `thin_*`), nem a feliratot. Ezt az irányt nem kell újra
végigjárni.

### ⛔ NEGATÍV 2 — a csúszka mellett NINCS `−` és `+` gomb

A `scale_group` **159** képpont széles, és pontosan kitölti a két gyereke:
`loupehit` 25 + a köztük lévő 7 képpontos rés + `scalecontainer` 127 = **159**.
A csoport jobb széle (525) egybeesik a csúszka jobb szélével ⇒ **fizikailag
sincs hely** további gombnak, és a `respack.yt` listájában a `scale_group` és a
`metadata_group` között csak `loupehit`, `loupe`, `infotext_clip`, `infotext` és
a kikommentelt `#addkeywords` áll — nagyítás/kicsinyítés gomb nincs.

### ⛔ NEGATÍV 3 — a két nagyítás-gomb NEM ebbe a sávba való

A „Beillesztheti a fotót a megjelenítési területbe" és a „Fotó megjelenítése
tényleges méretben" buboréksúgójú gombok elemneve **`editpanel/fit`** és
**`editpanel/1to1`** — vagyis a **szerkesztő (egyképes) nézet** alsó sávjáé,
nem a könyvtár-nézeté. A könyvtár-nézet sávjában az eredetiben sincsenek ott.
Részletes leírásuk: [`ui-audit-editor.md`](ui-audit-editor.md), „A szerkesztő
nagyítás-hármasa".

### Egy viselkedési részlet: `Property mousedown 1`

Mind a négy kapcsoló — és a szerkesztő `fit`/`1to1` gombja is — **lenyomásra**
sül el, nem felengedésre (`thumbui.tre` 258–281., `editpanel.tre` 1315./1322.).

## A KÖNYVTÁR OSZTÓSÁVJA — `ytSplitterOffsetHandler`, 240-es alsó ÉS felső korlát, és hogy MIÉRT nem őrzi meg (2026-09-04, #2329)

> **Bizonyítottság: megerősített.** Minden szám cím + kiolvasott érték. A
> záró negatív eredmény kimerítő: a teljes PE-t végigpásztázza.
>
> Ez a szakasz a fenti „MEGŐRZÖTT elrendezés-állapot" 2. pontját folytatja:
> ott az dőlt el, hogy a `HLISTDIV` **nem** az osztóvonal; itt az, hogy
> **mi az**, hogyan viselkedik húzás közben, és hogy induláskor honnan jön.

### 1. Az osztósáv KÉT elem, nem egy

```
thumbui.tre:512   thumbui/hlisthandle: thumbui/hlistsizer
thumbui.tre:513                        m_centerY
thumbui.tre:514                        m_alignL
thumbui.tre:516   thumbui/hlistsizer:  thumbui/mainuipanel
thumbui.tre:517                        XConstraint 0, 0, HLISTOFFSET2=240, -4
thumbui.tre:518                        Handler hsplitoffset HLISTOFFSET2
thumbui.tre:519                        YConstraint 0, 0, searchtop
thumbui.tre:520                        YConstraint 1, 1, publishbottom
```

- **`hlistsizer`** — a húzható sáv. Bal széle a `HLISTOFFSET2` **−4**
  képponton áll, tehát a fogási zóna 4 képponttal a határvonal ELŐTT
  kezdődik. Függőlegesen a keresősor aljától (`searchtop`) a publikálósáv
  tetejéig (`publishbottom`) ér.
- **`hlisthandle`** — a sávon belüli fogantyú-rajz: **függőlegesen
  középre** (`m_centerY`), **balra igazítva** (`m_alignL`).

### 2. Mit mozgat egyszerre a húzás

A `HLISTOFFSET2` **három további elem** vízszintes rögzítése is:

| elem | `.tre` sor | mit köt hozzá |
|---|---|---|
| `thumbui/listdecrect` | `thumbui.tre:441–443` | a bal hasáb kerete (`XConstraint 1, 0, HLISTOFFSET2`) |
| `thumbui/albumsback` | `thumbui.tre:506–508` | a rács háttere (`XConstraint 0, 0, HLISTOFFSET2`) |
| `thumbui/searchgroup` | `thumbui.tre:558–561` | a keresőcsoport bal széle |

⇒ Az osztósáv húzása **egyetlen változón át** mozgatja a hasáb keretét, a
rácsot és a keresőcsoportot — nincs külön szinkronizálás.

### 3. A kezelő osztálya és az alapérték

| mi | érték | cím |
|---|---|---|
| kezelő neve a `.tre`-ben | `hsplitoffset` | sztring: `0x00c7fbd0` |
| a név-visszaadó tonk | `mov eax, 0xc7fbd0 / ret` | `0x0040aa80` |
| a beállító tábla sora | 20 bájtos rekord | `0x00c8072c`–`0x00c8073c` |
| **gyártó függvény** | 0x1c bájtos objektum | **`0x009da130`** |
| vtábla | 13 bejegyzés | `0x00cda7e8` |
| RTTI típusnév | **`.?AUytSplitterOffsetHandler@@`** | `0x00d4734c` |
| **az objektum `+0x18` mezője** | **`240.0`** (float) | a konstans: **`0x00cf48b0`**, betöltés: `0x009da166` |

A **függőleges** osztó (`vsplitoffset`, gyártó `0x009da1b0`) **ugyanezt az
osztályt és ugyanezt a `240.0` konstanst** használja (`0x009da1e7`); csak
két bájt-jelzőben tér el (`+0x14`/`+0x15`: `1,1` vízszintesnél,
`0,1` függőlegesnél).

### 4. ⛔ A 240 nem csak alapérték — ez az ALSÓ KORLÁT, és a felső is belőle jön

A húzást a vtábla eseménykezelője végzi (`0x009d9d80`, esemény-azonosító
`0x1b`). A korlátozás két lépésben, `0x009d9df4`–`0x009d9e56`:

```asm
0x009d9df4  fld dword ptr [eax]        ; a JELENLEGI eltolás
0x009d9df6  fld dword ptr [ebx+0x18]   ; 240.0
0x009d9df9  fcompp                     ; 240 < jelenlegi ?
0x009d9dfd  test ah, 0x41 / jne …      ; ha igen: nincs teendő
0x009d9e06  fld dword ptr [ebx+0x18]   ; különben: 240.0 …
0x009d9e0e  fstp dword ptr [edx]       ; … BEÍRÁS az eltolásba
```

```asm
0x009d9e21  mov edx, [esp+0x28]
0x009d9e25  sub edx, [esp+0x20]        ; a szülő téglalap SZÉLESSÉGE (jobb − bal)
0x009d9e2d  fild dword ptr [esp+0x14]
0x009d9e31  fsub dword ptr [ebx+0x18]  ; szélesség − 240
0x009d9e34  fld dword ptr [eax]        ; a jelenlegi eltolás
0x009d9e36  fcomp st(1)                ; jelenlegi > (szélesség − 240) ?
0x009d9e50  fstp dword ptr [eax]       ; ha igen: BEÍRÁS (szélesség − 240)
```

⇒ **A bal hasáb szélessége `240` és `(a főpanel szélessége − 240)` közé
van szorítva** — ugyanaz a konstans mindkét oldalon. Tehát:

- **soha nem lehet keskenyebb 240 képpontnál**;
- a jobb oldal (a rács) sem szorítható 240 alá;
- a felső korlát **nem fix szám**, hanem az ablak méretével együtt mozog.

A téglalapot a szülő panel adja (`0x009d9dc5`, a szülő 0x30-as
vtábla-bejegyzése); ha az eltolás a húzás végén nem változott, a kezelő
`0x009d9e72`-nél jelzi a „nincs változás" ágat.

### 5. ⛔ KIMERÍTŐ NEGATÍV: az osztósáv állása NEM őrződik meg

A `HLISTOFFSET2` **nem szerepel a bináris egyetlen sztringjében sem**,
tehát semmilyen kód nem tudja néven olvasni vagy kiírni:

| név | előfordul a PE-ben? | hol |
|---|---|---|
| `HLISTOFFSET` (bármely alak) | **0** | csak `thumbui.tre` (5 sor) |
| `RIGHTDRAWEROFFSET` | 1 | `0x00c7fe08` |
| `LEFTDRAWEROFFSET` | 1 | `0x00c7fe50` |
| `HLISTDIV` | 1 | `0x00c8e67c` (az elsőindulási maradék, ld. fent) |
| `hsplitoffset` | 1 | `0x00c7fbd0` — és **pontosan egy** kódhivatkozás rá: a saját név-visszaadója, `0x0040aa81` |

Módszer: a teljes PE nyers pásztázása a nevekre ÉS a sztringcímek
mutató-előfordulásaira, szekciónkénti cím-visszafejtéssel; valamint a
`string_xrefs` index. Ez ugyanaz az eljárás, amivel a `HLISTDIV`
negatívja készült.

⇒ **A fiókok eltolása (`RIGHTDRAWEROFFSET`, `LEFTDRAWEROFFSET`) MEGŐRZŐDIK**
— ezeket a `0x0040bf70` induló függvény név szerint olvassa (ld. a fenti
szakasz 3. pontját) —, **a könyvtár osztósávjáé viszont NEM.** Az eredeti
Picasa minden indításkor **240 képponton** kezdi.

### 6. Eredeti / nálunk / teendő

| | eredeti (mért) | nálunk (mért) | eltérés |
|---|---|---|---|
| alapértelmezett szélesség | **240** (`0x00cf48b0`) | **240** (`controller.py:87`) | ✅ egyezik |
| **legkisebb** szélesség | **240** (`0x009d9df6`) | **160** (`controller.py:88`) | ❌ 80 képponttal keskenyebbre engedjük |
| **legnagyobb** szélesség | **panelszélesség − 240** (`0x009d9e31`) | **600** rögzítve (`controller.py:89`) | ❌ fix szám az ablakfüggő helyett |
| fogási zóna | a határvonal **−4** képponttól (`thumbui.tre:517`) | a `SplitView` alapértelmezett fogantyúja | nem mérve |
| megőrzés újraindításkor | **nincs** (5. pont) | **van**: `view/folderPaneWidth` (`controller.py:524`) | tudatos eltérés |

**Ajánlás:** a megőrzést **tartsuk meg** (a #322 kifejezetten ezt kérte, és
a felhasználónak kényelmesebb), a **korlátokat viszont igazítsuk** az
eredetihez: alsó korlát 240, felső korlát a rendelkezésre álló szélesség
mínusz 240. Jegy: #2329.

## A `varbutton` KEZELŐ — a felület EGYETLEN ki-be kapcsoló mechanizmusa (2026-09-04, #754)

> **Bizonyítottság: megerősített.** A nyelvtan a bináris formátumsztringjéből
> és a beolvasó kódból jön; a jelentést **két, egymástól független
> felhasználás** (jobb és bal fiók) erősíti meg.

A `.tre`-kben tizenegy helyen áll `Handler varbutton …`. Eddig egyik sem
volt megfejtve — pedig **ez az a mechanizmus, amivel a Picasa felülete
minden ki-be kapcsolható részét mozgatja**: a jobb oldali fiókot, a
szerkesztő bal panelét, a teljes képernyős módot, a publikálósávot és a
kereső sávot is.

### 1. A nyelvtan

| mi | érték | cím |
|---|---|---|
| a kezelő neve | `varbutton` | sztring `0x00c7fc00`, név-visszaadó `0x0040aab0` |
| gyártó | `0x009da240` | tábla-rekord `0x00c80764`–`0x00c80778` |
| **feldolgozó formátum** | **`%s %f %f %d %s %s`** | `0x00cda73c` |
| elfogadott mezőszám | **2 … 6** | `0x009da2a3` (`lea eax,[ebp-2] / cmp eax,4 / ja`) |
| objektum | 0x48 bájt, vtábla `0x00cda77c` | `0x009d7b30` |
| RTTI típusnév | **`.?AUytVarButtonHandler@@`** | a `0x00cda778` COL-on át |

```
Handler varbutton <változó> <lenyomott> [<felengedett>] [<animál>] [<cél1>] [<cél2>]
```

**A két elhagyható érték alapértéke a binárisból, nem találgatásból:**

| mező | alapérték | hol állítja be |
|---|---|---|
| `<felengedett>` (2. `%f`) | **−1000.0** | `0x009da25f` tölti a cél-rekeszbe (`0x00cf4da4`) |
| `<animál>` (`%d`) | **1** | `0x009da294` (`mov dword ptr [esp+0x28], 1`) |

A rekesz-azonosítás a `lea`/`push` sorozat visszaszámolásából: a 2. `%f`
és az `%d` pontosan azokra a helyekre ír, amelyeket a függvény előre
feltöltött.

### 2. Mit jelentenek az értékek

Az objektum mezői: `+0x2c` = a lenyomott érték, `+0x30` = a felengedett,
`+0x34` = az **emlékezett eredeti**, `+0x38` = az animálás-jelző.

A kapcsolás (`0x009d7d5d`–`0x009d7dac`), a gomb `+0x359`-es lenyomott-jelzője
szerint:

- **lenyomva** → a változó a **`+0x2c`** (1. `%f`) értéket veszi fel; ha
  `+0x34` még a **−1000** őrszem (`0x00cf4ce8`), előbb **elteszi a
  változó AKKORI értékét** — ezt fogja visszaadni elengedéskor;
- **elengedve** → a **`+0x30`** (2. `%f`); de ha az a −1000 őrszem, akkor
  a `+0x34`-ben eltett **eredeti** érték jön vissza.

⇒ **A második érték elhagyása azt jelenti: „engedéskor állítsd vissza
oda, ahol volt".** Erre épül a keresősáv (`searchcontainer.tre:27`), ahol
csak egyetlen érték áll.

**Az animálás:** ha a jelző nem 0, a változó **0,4 másodperc** alatt
mozog át (`0x009d7dc1` ág; az időtartam a `0x00cf4ce0`-as dupla pontosságú
`0.4`, a `0x009a5210` által adott aktuális időhöz adva). `0` esetén ugrik.

A záró két `%s` **további elemeket** nevez meg, amelyeket a mozgás
együtt érint (`0x009da349` a 6. mezőre) — a szerkesztő előnézeti képe így
nyúlik a fiókkal együtt.

### 3. Mind a tizenegy felhasználás — jelentéssel

| hely | változó | lenyomva | elengedve | animál | együtt mozog |
|---|---|---|---|---|---|
| `thumbui.tre:700` | `RIGHTDRAWEROFFSET` | **−280** | 0 | **igen** | `editpanel/previewimage`, `…image2` |
| `editpanel.tre:1413` | `LEFTDRAWEROFFSET` | 0 | **−279** | **igen** | `editpanel/previewimage` |
| `editpanel.tre:1404` | `editbackmargin` | 4 | 0 | nem | — |
| `editpanel.tre:1405` | `previewx0` | 5 | 0 | nem | — |
| `editpanel.tre:1406` | `previewx1` | −5 | 0 | nem | — |
| `editpanel.tre:1407` | `previewy0` | 5 | 0 | nem | — |
| `editpanel.tre:1408` | `previewy1` | −25 | 0 | nem | — |
| `editpanel.tre:1409` | `movieparenty` | −39 | 0 | nem | — |
| `panelroot.tre:59` | `tabdiv` | 29 | 0 | *(alap: igen)* | — |
| `thumbui.tre:85` | `publishbottom` | −105 | −212 | *(alap: igen)* | — |
| `searchcontainer.tre:27` | `searchtop` | 62 | *(−1000 = vissza az eredetire)* | *(alap: igen)* | — |

**A `fullscreenswitcher` hat változót kapcsol egyszerre** (`editpanel.tre:1404–1409`,
`Property setpressed 1`): a teljes képernyős mód nem külön ablak, hanem a
margók **nullázása** — és mind a hat **animálás nélkül**, egyszerre ugrik.

### 4. A két fiók iránya — mert a puszta szám félrevezet

| | `.tre` bizonyíték | mit jelent |
|---|---|---|
| **jobb fiók** | `thumbui.tre:534` `XConstraint 0, 1, RIGHTDRAWEROFFSET`, a kapcsoló `Property setpressed 0` | 0 = **csukva** (nulla széles), −280 = **280 képpont széles, nyitva**; induláskor csukva |
| **bal fiók (szerkesztő)** | `editpanel.tre:1228` `LEFTDRAWEROFFSET=0`, `:1421` a szomszéd `LEFTDRAWEROFFSET, 279`, a kapcsoló `Property setpressed 1` | 0 = **nyitva** (279 széles), −279 = **kicsúszva balra**; induláskor nyitva |

⇒ Mindkettőnél a **lenyomott állapot = látszik a fiók**. A jobb fiók
szélessége **280**, a bal **279** — a `.tre`-ből, nem becslésből.

### 5. Eredeti / nálunk / teendő

| | eredeti (mért) | nálunk (mért) | eltérés |
|---|---|---|---|
| jobb oldali panel | **EGY fiók, 280 képpont** | **négy külön hasáb**: Címkék 190, Helyek 320, Tulajdonságok 210, Emberek 200 (`Main.qml:1977/2014/2029/2048`) | ❌ szerkezet és méret is |
| nyitás/csukás | **0,4 s animáció** | `visible` átbillentés, animáció nélkül | ❌ |
| induló állapot | csukva (`setpressed 0`) | csukva (`activeDrawerTab: ""`, `Main.qml:100`) | ✅ |
| megőrzés | **igen**, `RIGHTDRAWEROFFSET` (ld. a „MEGŐRZÖTT elrendezés-állapot" 3. pontját) | `utolsoFiokLap` (`Main.qml:143`) | eltérő tárolás, nem mérve, hogy túléli-e az újraindítást |

Jegy: **#754** (a négy hasáb → egy fiók). A 0,4 másodperces animáció és a
280-as szélesség ott, kommentben.

## A FŐABLAK MÓD-GÉPE és a „képernyőn kívülre rakott" elemek (2026-09-04, #440 / #2074)

> **Bizonyítottság: megerősített.** Minden állítás `.tre` fájl + sor. A
> „soha nem látszik" állítás **kimerítő**: mind a 141 erőforrás-fájlt
> végigpásztázza.

Két, egymással összefüggő szerkezeti dolog derült ki, és mindkettő **a
lefedettségi mérésünk pontosságát is érinti**.

### 1. `macros.tre` „MODE MACROS" — a módok teljes leírása egy helyen

A `macros.tre` 192–300. sora egy külön, `# MODE MACROS` felirattal jelölt
blokk. Minden mód egy makró, és a makró **felsorolja, mely paneleket
mutatja és melyeket rejti el**. A módváltás tehát nem kódba égetett
láncolat, hanem erőforrás-adat.

| makró | melyik vezérlő viseli | mit MUTAT | mit REJT |
|---|---|---|---|
| `m_enable_albummode` (`macros.tre:196`) | `acquirepanel/anowbutton` (`acquirepanel.tre:264`) | `mainuipanel`, `infowell`, `secretcoinclip` | `acquirepanel`, `printpanel`, `editpanel`, `fullview` |
| `m_albumtoggle` (`macros.tre:205`) | `thumbui/viewswitch` (`thumbui.tre:36`) | `editpanel`, `1to1`, `fit` | `albumsback`, `throttlegroup`, `listdecrect`, `listbutton`, `hlistsizer`, `searchgroup`, `searchcontainer` |
| `m_basecontrolset_enable` (`macros.tre:224`) | `thumbui/publishswitcher` (`thumbui.tre:81`) | `basecontrolset`, `importbutton`, `buttongroup1`, `activitycontainer` | — |
| `m_cdcontrolset_enable` (`macros.tre:233`) | `thumbui/cdmode` (`thumbui.tre:484`) | `controlsettop`, `publishcontrolsets`, `publish/presentation_group`, `cd_label` | `searchcontainer`, `bottombevel_base`, `logo` |
| `m_backupcontrolset_enable` (`macros.tre:245`) | `thumbui/backup` (`thumbui.tre:96`) | `controlsettop`, `publishcontrolsets`, `publish/backup_group`, `backup_label` | `searchcontainer`, `bottombevel_base`, `logo` |
| `m_replicatecontrolset_enable` (`macros.tre:257`) | `thumbui/replicate` (`thumbui.tre:76`) | `controlsettop`, `publishcontrolsets`, `publish/replication_group`, `replication_label` | `searchcontainer`, `bottombevel_base`, `logo` |
| `m_acquire_enable` (`macros.tre:281`) | `thumbui/importbutton` (`thumbui.tre:452`), `thumbui/acquirebutton` (`thumbui.tre:32`) | `panelroot/acquiretab` (+ `downtarget`) | — |
| `m_print_enable` (`macros.tre:285`) | `outputlayout/pbutton` (`outputlayout.tre:38`) | `thumbui/printpanel` | `acquirepanel`, `editpanel`, `mainuipanel`, `infowell`, `secretcoinclip` |

### 1/b A Biztonsági mentés gombja a KIADOTT felületen nem látszik

```
thumbui.tre:95    ###currently not shown in UI###
thumbui.tre:96    thumbui/backup: thumbui/globalmode
thumbui.tre:100   m_hidden
```

A `thumbui/backup` — a `m_backupcontrolset_enable` módot viselő gomb —
**`m_hidden`**, és a forrás saját megjegyzése is kimondja. A mód tehát
LÉTEZIK és teljesen le van írva, de a kiadott 3.9-es felületen a
belépési pontja nincs kirakva. *(Hogy a menüből elérhető-e, ez a kör nem
mérte — a `Property uptarget searchcontainer/searchbutton` sora szerint a
gomb a keresőgombhoz kapcsolódik.)*

⇒ **A három publikáló mód (Ajándék CD · Biztonsági mentés · Replikáció)
pontosan ugyanazt a hármat rejti el**: a keresősávot, az alsó
él-díszítést és a logót. Ez **normatív**: ha ezeket a módokat megépítjük,
a keresősávnak el kell tűnnie.

⛔ **Három mód-makró DEFINIÁLVA VAN, de egyetlen `.tre`-elem sem viseli:**
`m_webcontrolset_enable` (`macros.tre:269`), `m_collage_enable`
(`macros.tre:296`), `m_search_disable` (`macros.tre:221`). *(Hatókör: a 141 erőforrás-fájlban nincs
használójuk. Hogy a program KÓDBÓL elvégzi-e ugyanezt a mutat/rejt sort —
a `0x0040bf70` induló függvény név szerint kapcsolgat elemeket —, ez a kör
NEM mérte.)*

### 2. `m_render_offscreen` — 20 elem, amely SOHA nem látszik

```
macros.tre:7   #define m_render_offscreen
macros.tre:8   XConstraint 0, 0, -9999
macros.tre:9   YConstraint 0, 0, -9999
```

Ez nem elrejtés (`m_hidden` = `setvisible 0`), hanem **a vászonon kívülre
helyezés**. Az így megjelölt elem létezik, célozható, van buboréksúgója —
de **nem rajzolódik oda, ahol a felhasználó láthatná**.

Mind a **20** előfordulás, fájl + sor szerint:

| fájl:sor | elem |
|---|---|
| `editpanel.tre:112` | `editpanel/writetodisk` |
| `editpanel.tre:1358` | `editpanel/edithelpbutton` |
| `makemoviepanel.tre:549` | `makemoviepanel/viewedit` |
| `printpanel.tre:239` | `printpanel/phelpbutton` |
| `printpanel.tre:250` | `printpanel/statustext` |
| `thumbui.tre:26` | `thumbui/largethumbs` |
| `thumbui.tre:29` | `thumbui/smallthumbs` |
| `thumbui.tre:32` | `thumbui/acquirebutton` |
| `thumbui.tre:40` | `thumbui/horizonadjust` |
| `thumbui.tre:43` | `thumbui/prev` |
| `thumbui.tre:48` | `thumbui/next` |
| `thumbui.tre:53` | `thumbui/fit` |
| `thumbui.tre:56` | `thumbui/1to1` |
| `thumbui.tre:59` | `thumbui/morethumbs` |
| `thumbui.tre:64` | `thumbui/lessthumbs` |
| `thumbui.tre:69` | `thumbui/soloview` |
| `thumbui.tre:76` | `thumbui/replicate` |
| `thumbui.tre:88` | `thumbui/uploadmgr` |
| `thumbui.tre:103` | `thumbui/visitweb` |
| `thumbui.tre:106` | `thumbui/makealbum` |

**A `thumbui`-beliek a `root` gyerekei** (a `makealbum` a
`buttonbarsets`-é; a `writetodisk`, `viewedit`, `phelpbutton`,
`statustext` a saját paneljüké), és egyiknek sincs második,
látható definíciója — a `thumbui/next`, `prev`, `fit`, `1to1`,
`smallthumbs`, `largethumbs`, `visitweb`, `uploadmgr`, `soloview`,
`replicate`, `morethumbs`, `lessthumbs`, `horizonadjust`, `acquirebutton`,
`makealbum` **egyszer** szerepel a fájlban, azzal az egy blokkal.

⇒ **Parancs-proxik**: a menü, a gyorsbillentyű és a `showtarget`/`uptarget`
hivatkozások ezeket célozzák; a látható vezérlő máshol, más néven ül.
Erre a legjobb bizonyíték a **nagyítás-hármas**: a látható gombok az
`editpanel/fit` és `editpanel/1to1` (mért geometria: `ui-audit-editor.md`),
miközben a `thumbui/fit` és `thumbui/1to1` a `−9999`-en áll.

### 3. Következmény a saját lefedettségi mérésünkre

A `docs/specs/ui-lefedettseg-elemek.csv` és a belőle számolt „fehér
foltok" ezt a 20 elemet **hiányzó felületi elemként** kezelhetik, pedig
soha nem is látszottak. A `thumbui/acquirebutton` sora ezért ebben a
körben megkapta a magyarázatot; a többi már korábban `megvan`/`lekutatva`
besorolást kapott, tehát a számot nem torzítja.

*(A többi panel `m_render_offscreen`-es eleme — `writetodisk`,
`edithelpbutton`, `phelpbutton`, `statustext`, `viewedit` — nincs a
lefedettségi táblában feltáratlanként, tehát nem kell átsorolni.)*
