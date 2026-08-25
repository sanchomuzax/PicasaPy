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
| alsó sáv | 105 px | 20 + 52 = **72 px** | ❌ **nyitva** — a magasság önmagában holt sávot adna: a tálca-tartalom (36,5 %-os osztópont, 81 px-es képtálca) is átépítendő |

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
