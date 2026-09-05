# A könyvtár-ablak — KÖTELEZŐ méretspecifikáció

**Ez a lap normatív.** A főablak (könyvtár-nézet) **pontosan** így nézzen ki.
A tulajdonos döntése (`../decisions/szerkeszto-bal-panel.md` 1. pontja
általánosan érvényes): *a felület pontosan úgy nézzen ki, mint az eredeti
Picasa.*

Testvérlapok: [`szerkeszto-panel-meretek.md`](szerkeszto-panel-meretek.md) ·
[`jobb-fiok-meretek.md`](jobb-fiok-meretek.md).

## 0. Forrás és módszer

Két forrás együtt:

1. **`thumbui.tre`** — a **futásidejű kényszerek** és a névvel ellátott
   konstansok (`HLISTOFFSET2`, `searchtop`, `publishbottom`);
2. **`respack.yt` rétegtéglalapjai** — a **méretek**
   ([`binaris-regeszet-modszertan.md`](binaris-regeszet-modszertan.md) 14/c).
   **156 elem** a `thumbui` névtérben.

### ⚠️ Itt az abszolút pozíció NEM használható

A szerkesztő-panellel ellentétben a könyvtár-ablak elemeit a `.tre`
**átméretezhető** kényszerekkel köti, ezért a csomag tervezővászon-értékei
(800 × 534) eltérnek a futásidőtől. A legszembetűnőbb:

| | csomag | futásidő |
|---|---:|---:|
| bal panel szélessége | 210 | **`HLISTOFFSET2` = 240** |

**Ezért ez a lap méreteket és MARGÓKAT ír elő, nem abszolút x/y-t.**

### A négy névvel ellátott konstans (`thumbui.tre`)

| konstans | érték | mit szab meg |
|---|---:|---|
| `HLISTOFFSET2` | **240** | a bal panel szélessége (húzható) |
| `searchtop` | **35** | a felső sáv magassága |
| `publishbottom` | **−105** | az alsó sáv magassága |
| `RIGHTDRAWEROFFSET` | 0 | a jobb fiók (alapból behúzva) |

---

## 1. Az ablak három vízszintes sávja

```
┌──────────────────────────────────────────────┐
│  felső sáv                            35 px  │
├────────────┬─────────────────────────────────┤
│ bal panel  │  a rács                         │
│   240 px   │                                 │
├────────────┴─────────────────────────────────┤
│  alsó sáv                            105 px  │
└──────────────────────────────────────────────┘
```

- a bal panel **FIX 240 px**, nem százalék, és átméretezéskor **nem
  skálázódik** — a rács nő, a panel marad;
- a **húzható elválasztó** (`hlistsizer`) **8 px** széles, és a panel jobb
  szélétől **4 px-rel balra** kezdődik (`XConstraint 0, 0, HLISTOFFSET2, -4`);
- a fogantyú (`hlisthandle_win`) **8 × 47**, függőlegesen középen.

> ⚠️ A `design-guide.md` „386 px ≈ 20 %, arányosan skálázandó" és a
> „210 px ≈ 26 %" értéke **egyaránt téves** volt — a #587 kijavította
> mind a kettőt. A `folderPaneWidth` alapértéke viszont **még 230**;
> a 240-re állítás a `FOLDER_PANE_WIDTH_DEFAULT`-ot (`app/controller.py`)
> és a `Main.qml` tartalék-értékét érinti.

---

## 2. A felső sáv (35 px)

| elem | méret | megjegyzés |
|---|---:|---|
| `albumview` / `fullview` (nézetváltó) | **132 × 29** | a bal panel fölött |
| `importbutton` (Importálás) | **111 × 22** | |
| `newalbum` | **29 × 22** | |
| `flatview` · `folderview` | **30 × 22** egyenként | egy `hviewtoggle` csoportban (**60 × 22**) |
| `folderviewpopup` (a nézet-legördülő nyila) | **22 × 22** | |
| `webcambutton` | **36 × 22** | |
| `sbutton` · `timelinebutton` | **132 × 28** | |
| `cdmode` | 132 × 28 | |
| **`searchcontainer`** (keresősáv) | **388 × 30** | |
| `backup` | 30 × 28 | |
| `gplushit` | 26 × 26 | |
| `activitycontainer` | 35 × 28 | jobb szélen |

**A gombikonok mérete 14–17 px** (`albumview_icon` 17 × 15,
`newalbum_icon` 19 × 14, `importbutton_icon` 27 × 14,
`webcambutton_icon` 24 × 17, `folderview_arrow` 7 × 4).

> ✅ #587: a `MainToolbar.qml` magassága **35** (előtte 34).

### A keresés kibontott sávja

`searchgroup` / `searchgroupcontainer`: **25 px** magas, a keresősáv alatt
(y 38..63), és a bal panel fölött **nem** ér át (x 223-tól).

---

## 3. A bal panel (240 px)

| elem | méret / margó |
|---|---|
| a lista (`albums_win` / `albums_mac`) | a panelen belül **bal 9 px**, **jobb 5 px** margó |
| a lista teteje | a fejléc alatt (`y 75` a vásznon, a fejléc 51..72) |
| `listbox_title` („Könyvtár" felirat) | **80 × 14**, bal margó 16 |
| `listbox_title_button` | 24 × 14 |
| `newfolder` | **29 × 22**, a panel jobb széléhez |
| `newfolder_icon` | 19 × 14 |
| `headerproto` (gyűjtemény-fejléc sorsablon) | **199 × 17** |

> **Amit a csomag NEM ad meg:** a mappafa **sormagasságát és behúzását** —
> a lista `listbox` típusú, a sorait kódból rajzolja. Ez negatív eredmény,
> ld. [`ui-audit-mainwindow.md`](ui-audit-mainwindow.md) 1.4.

---

## 4. A rács fölött lebegő gombok — 14 × 14, egymás alatt

A `root`-hoz kötött, a rács jobb szélén függőlegesen sorakozó gombok
**mind 14 × 14 képpontosak**, és **15 px-enként** követik egymást. Mind a
tizennyolc **`vbutton`** (rajz nélküli, láthatatlan találati terület); a
téglalapok a `respack.yt` tervezővásznáról valók, `x = 375…389`
(`respack.yt:3280882`-től, 17 bájtos bejegyzések).

⚠️ **Tervezővászon-koordináták**, nem futásidejű hely. A sorrend és az
osztásköz megbízható, az abszolút y nem.

| sorrend | elem (teljes név) | y (vásznon) |
|---|---|---:|
| 1 | `thumbui/largethumbs` | 76 |
| 2 | `thumbui/smallthumbs` | 91 |
| 3 | `thumbui/acquirebutton` | 106 |
| 4 | `thumbui/viewswitch` | 121 |
| 5 | `thumbui/horizonadjust` | 136 |
| 6 | `thumbui/prev` | 151 |
| 7 | `thumbui/next` | 166 |
| 8 | `thumbui/fit` | 181 |
| 9 | `thumbui/1to1` | 196 |
| 10 | `thumbui/morethumbs` | 211 |
| 11 | `thumbui/lessthumbs` | 226 |
| 12 | `thumbui/soloview` | 241 |
| 13 | `thumbui/replicate` | 256 |
| 14 | `thumbui/publishswitcher` | 286 |
| 15 | `thumbui/uploadmgr` | 301 |
| 16 | `thumbui/histogram` | 316 |
| 17 | `thumbui/visitweb` | 331 |
| 18 | `thumbui/makealbum` | 346 |

**Az osztásköz egyenletesen 15 px** (14 px gomb + 1 px hézag); a 13.→14.
között 30 px, tehát ott **csoporthatár** van.

`throttlegroup` (a jobb szélen futó sáv): **16 px** széles.

### 4.1 `thumbui/prev` és `thumbui/next` — NINCS nyomva-tartásra ismétlés

Buboréksúgójuk „View the next Photo" / „View the previous Photo"
(`thumbui_text.tre:168` és `thumbui_text.tre:171`), a deklarációjuk pedig
`thumbui.tre:43` és `thumbui.tre:48`.

Mindkettőnek **ki van kommentezve** a két viselkedés-tulajdonsága:

```
thumbui/prev: root
#Property mousedown 1
#Property setautorepeat 5
m_render_offscreen
```

A `#` a `.tre`-ben **megjegyzés** — ez mérve van: a `collagepanel.tre`
25–69. sorain teljes elemblokkok állnak `#`-kel (`#collagepanel/border_label0:
collagepanel/border0`), és ezek az elemek **sem a leltárban, sem a
`respack.yt` élő rétegei közt nincsenek** (a respack a nevükben megőrzi a
`#`-et: `layer:collagepanel/#rect: border_preview0`). Kivétel csak a
`#include` / `#includeonce` preprocesszor-utasítás, aminek a kikapcsolt
alakja `##include`.

⇒ **A két nyíl nyomva tartva NEM léptet tovább**, egy kattintás egy kép.
Ez szándékos különbség: a közvetlen szomszédjaik, a
`thumbui/morethumbs` és a `thumbui/lessthumbs` `Property setautorepeat 5`
sora **`#` nélkül** áll, tehát náluk az ismétlés él
([`picasa-eger-es-kijeloles.md`](picasa-eger-es-kijeloles.md) 7. szakasz).

> *Bizonyítottsági fok: **megerősített*** — a `.tre` sorai és a `respack.yt`
> bejegyzései kiolvasva.

---

## 5. Az alsó sáv (105 px) — `basecontrolset`

> ✅ **Képernyőképen VISSZAMÉRVE (#1420, 2026-08-26.)** —
> `research/testdata/screenshot/Képernyőkép 2026-07-18 145027.png`
> (1918 × 1030; az ablak alja 2 képponttal le van vágva, ezért látszik a
> sáv 105 helyett 103 képpontja). A sáv teteje y = 927.
>
> | elem | kényszerből várt | a képen mérve |
> |---|---|---|
> | `infotext` | y 0…14 | y 927…943 (kék csík) |
> | `scratchback` | x 5 … .365·W−15 = 685 · **81 px magas** | **x 5…684**, **y 947…1027** |
> | `separator` | x .365·W−3 = 697 … W−17 = 1901, y 50…52 | **x 697…1902, y 977…978** |
> | `webupload` | 141 px, .365·W−5 körül | **x 697…837 = 141**, y 988…1022 = **35** |
> | `outputs` | .365·W+140 = 840 | az 1. gomb közepe **867,5** = 840 + 55/2 |
> | `startoggle`/`rotate*` | 36 × 22, .365·W-tól | **697…732 · 738…773 · 775…810**, y 947…968 |
> | három tálca-gomb | 34 széles, egymás alatt | **x 644…677**, y 952…973 · 973…993 · 1001…1022 |
>
> ⚠️ **Egy eltérés a respack rétegfejlécétől:** a kimeneti gombok a képen
> **55 képpontos osztásközzel** követik egymást (a három felirat közepe
> 867,5 · 922,5 · 977,5), nem 59-cel. A `docs/specs/picasa-keptalca.md`
> 11. pontja a cellát 59 × 40-nek, a gombot 55 × 36-nak méri — a ténylegesen
> KIRAJZOLT sorban tehát a cellák nem a saját szélességükkel követik
> egymást, hanem a gomb 55 képpontjával. A PicasaPy ma (a #1345 óta) 59-es
> osztásközt használ; ez 4 képponttal szellősebb az eredetinél. A #1420
> ezt SZÁNDÉKOSAN nem változtatta meg (a #1345 őreinek területe), de a
> lelet itt rögzítve marad.
>
> ✅ **ELDŐLT (2026-09-05, #1504): az 55 nyer, és megvan az OKA.** Az
> elrendező (`0x00597f80`) a kurzort a gyerek elrendezés utáni, **tényleges**
> szélességével lépteti (`0x0059883e`–`0x00598863`: `x1 − x0`, majd
> akkumulátorhoz adás) — az pedig a gomb saját respack-doboza, **55**. A
> `59 × 40` a `docbounds` cella-grafika mérete, nem osztásköz. A konténer
> `Property cellwidth 50`-et deklarál (`outputlayout.tre`), amit a
> `0x00597390` a `+0x274` tagba tesz és a `0x0059862c` olvas — de a
> léptetésben ez az érték nem jelenik meg. Levezetés:
> `picasa-keptalca.md`, „A kimeneti sor LÉPTETÉSE".


### 5.1 A szerkezeti kulcs: a 36,5 %-os osztópont

A sáv két részre oszlik, az ablakszélesség **0,365-szörösénél**. Ez öt
elemnél ismétlődik (`thumbui.tre`):

| elem | X-kényszer |
|---|---|
| `scratchback` (a képtálca) | `0, 0, 5` … `1, .365, -15` |
| `webupload_rect` (zöld gomb) | `0, .365, -5` … `1, .365, 140` |
| `outputs` (a műveletsor) | `0, .365, 140` … `1, 1, -10` |
| `separator` | `0, .365, -3` … `1, 1, -17`, y 50..52 |
| `bcenterright` | `0, .365, 0` |

### 5.2 Az infó-csík

`infotext` / `infotext_clip`: **14 px** magas, a sáv **legtetején**
(y 429..443), és 20-20 px margóval a két szélén.

> A mai `TrayBar.qml` `infoBar` **20 px** — ez **szándékos és dokumentált**
> eltérés (olvashatóság, `design-guide.md`). Marad, és a 105-be pontosan
> beleillik: 20 (csík) + 81 (képtálca) + 4 (alsó hézag) = 105 (#1420).

### 5.3 A képtálca (bal oldal)

| elem | méret |
|---|---:|
| `scratchback` / `scratchpadbase` | **81 px magas** (a sáv tetejétől 20, aljától 4) |
| `scratch` (bélyegképsor) | 5 px belső margó, **jobbról 50 px** a gomboknak |
| `scratchlabel` („Kijelölés") | **205 × 19**, `m_centerXY` — **középre** |
| `scratchhold` | **34 × 22** |
| `scratchclear` | **34 × 20** |
| `addtobuttcon` | **34 × 22**, `popuplist` (felfelé nyíló) |
| `scratchhold_icon` | 9 × 12 |
| `scratchclear_icon` | 11 × 11 |
| `dropup_icon` + `addto_arrow` | 16 × 18 + 7 × 4 |

A három gomb **egymás alatt**, a bélyegképsor jobbján fenntartott 50 px-ben.

### 5.4 A középső gombok

| elem | méret |
|---|---:|
| `startoggle` (csillag) | **36 × 22** |
| `rotateleft` · `rotateright` | **36 × 22** egyenként |
| `startoggle_icon0/1` | 17 × 17 |
| `rotateleft_icon` · `rotateright_icon` | 11 × 15 |

Osztásköz **37 px** (330 → 367), a csillag után 5 px hézag.

### 5.5 A nagyító és a nagyítás-csúszka

| elem | méret |
|---|---:|
| `scale_group` | **159 × 27** |
| `loupehit` | **25 × 19** |
| `loupe` (ikon) | 23 × 16 |
| `scalecontainer` (a csúszka) | **127 × 27** |

### 5.6 A négy kerek kapcsoló (jobb szél)

`metadata_group`: **240 × 24**, benne **négy, egyenként 60 × 24** gomb,
hézag nélkül:

| sorrend | elem | ikon |
|---|---|---|
| 1 | `people_toggle` | 19 × 17 |
| 2 | `places_toggle` | 14 × 19 |
| 3 | `tags_toggle` | 19 × 15 |
| 4 | `properties_toggle` | 17 × 18 |

> A mai `TrayBar.qml`-ből **hiányzik** ez a négyes; a funkciók a menüből
> érhetők el.

### 5.7 A zöld feltöltés-gomb és a műveletsor

| elem | méret |
|---|---:|
| `webupload_rect` | **147 × 44** (a hely) |
| `webupload` (maga a gomb) | **141 × 35** |
| `webupload_icon` | 18 × 14 |
| `outputs` (Nyomtatás / E-mail / Exportálás sor) | **424 × 29** |
| `separator` | **497 × 2** |

### 5.8 A „Továbbiak…" klip-gyűjtő mód üzenetsávja

⚠️ **HELYESBÍTÉS (2026-09-02):** ez a szakasz korábban *„az »egy művelet«
sáv (haladásjelzés)"* néven futott. **Nem haladásjelzés** — a kollázs és a
filmkészítő **klip-gyűjtő módjának** üzenetsávja, és a `single_action_container`
**mérete sem fix**, mert négy kényszere van. A működés és a levezetés:
[`getmore-klipgyujto-mod.md`](getmore-klipgyujto-mod.md).

| elem | méret | státusz |
|---|---:|---|
| `single_action_container` | (502 × 40 a tervezővásznon) | **NEM normatív** — kényszer-vezérelt, ld. a hivatkozott lap 3.1 |
| `single_action_group` | **481 × 30** | fix |
| `single_action_message` | **335 × 26** | fix, jobbra igazított |
| `single_action_return` | **109 × 43** | fix |
| `single_action_close` | **18 × 18** | fix |

### 5.9 Egyéb

*Forrás: `thumbui.tre:130` (`thumbui/size`).*

| elem | méret |
|---|---:|
| `toggle_right_drawer` | **15 × 16** |
| `thumbui/size` (méretfogantyú) | 20 × 20, jobb alsó sarok |
| `output_label` | 502 × 13 |

---
## 6. Megvalósítási ellenőrzőlista

- [ ] bal panel **240 px** fix (ma 230 — integrátori lépés), de a **nem
      skálázódik** rész ✅ megvan és mérve van (#587)
- [ ] elválasztó **8 px**, fogantyú **8 × 47**
- [x] felső sáv **35 px** ✅ (#587)
- [x] alsó sáv **105 px** ✅ (#1420) — 20 (infó-csík) + 85; a
      tálca-tartalom a magassággal EGYÜTT épült át, holt sáv nélkül
- [ ] a nézetváltó gombok **132 × 29 / 132 × 28**
- [x] `importbutton` **111 × 22** ✅ (#587)
- [ ] `newalbum` / `newfolder` **29 × 22**, `flatview` / `folderview`
      **30 × 22**, `folderviewpopup` **22 × 22** (a gombok még hiányoznak)
- [x] keresősáv **388 × 30** ✅ (#587)
- [ ] a bal panel listája **9 px** bal, **5 px** jobb margóval
- [ ] a rács melletti lebegő gombok **14 × 14**, **15 px** osztásközzel
- [x] az alsó sáv a **36,5 %**-os pontnál válik ketté ✅ (#1420)
- [x] képtálca **81 px** magas, a bélyegképsor jobbján **50 px** a három
      gombnak, a „Kijelölés" felirat **középen** ✅ (#1420)
- [x] `startoggle` / `rotateleft` / `rotateright` **36 × 22** ✅ (#1420)
- [~] nagyítás-csúszka **127** ✅ (#1420); a nagyító (`loupehit` 25 × 19)
      még hiányzik
- [ ] a négy kerek kapcsoló **60 × 24** egyenként, hézag nélkül (ma hiányzik)
- [x] zöld gomb **141 × 35** egy **147 × 44**-es helyen ✅ (#1420)
- [x] `separator` **2 px**, a 36,5 %-tól jobbra ✅ (#1420)

**Kirajzolt teszt kötelező** (`tests/app/qml_functional/` minta), és a
javítás nélkül el kell buknia.

---

*Bizonyítottsági fok: megerősített* a méretekre (a `respack.yt` 156
`thumbui`-eleme) és a négy konstansra (`thumbui.tre` 443–519. sor).
**Nem** normatív az abszolút x/y — ott a `.tre` kényszerei nyernek.

## A fő eszköztár — mért geometria (`respack.yt`, 2026-08-16)

A `ui-audit-mainwindow.md` 4.1 szakasza az eszköztárat **képernyőképről**
olvasta ki. Itt a `respack.yt` nyers koordinátái állnak — **normatív**.

### A sáv

| elem | pozíció | méret |
|---|---|---|
| `rect: buttonbarsets` | (0, **4**) | **800 × 37** |
| `rect(0, searchcontainer): searchcontainer` | (**323**, 4) | **388 × 30** |
| `clip(searchoptions): searchgroupcontainer` | (223, **38**) | **577 × 25** |

### A KÖNYVTÁR-sor gombjai (y = 9, magasság 22)

| # | elem | x | méret | felirat / súgó |
|---:|---|---:|---|---|
| 1 | `importbutton` (+ ikon 27 × 14) | **6** | **111 × 22** | **Import** — *Get photos from a camera, scanner, or other media* |
| 2 | `newalbum` (+ ikon 19 × 14) | **124** | **29 × 22** | — *Create a new album* |
| 3 | `hviewtoggle` (tartó) | **160** | 60 × 22 | |
| 3a | ├ `flatview` | **160** | **30 × 22** | *Set view to show flat folder structure* |
| 3b | └ `folderview` | **190** | **30 × 22** | *Set view to show folder tree structure* |
| 4 | `folderviewpopup` (+ `folderview_arrow` 7 × 4) | **225** | **22 × 22** | *View options* |
| 5 | `webcambutton` (+ ikon 24 × 17) | **254** | **36 × 22** | *Capture photos or video from a webcam or other video device* |

A jobb szélen: `librarylabel_button` (**725**, 24 × 25) és a
`gplushit` / `gplus` Google+-gomb (**733**, 26 × 26 / 22 × 22, y = 6).

### A MÓD-sor gombjai (y = 5, magasság 28–29, mind 132 széles)

| elem | x | méret | felirat | súgó |
|---|---:|---|---|---|
| `fullview` | **5** | **132 × 29** | **Edit photos** | *Edit your photos* |
| `albumview` | **5** | **132 × 29** | — | *Return to organized thumbnails* |
| `sbutton` (+ ikon 16 × 14) | **142** | **132 × 28** | **Slideshow** | *Watch a slideshow of photos in the selected Folder or Album* |
| `timelinebutton` (+ ikon 26 × 9) | **279** | **132 × 28** | **Timeline** | *Timeline view of all your photos* |
| `cdmode` (+ ikon 20 × 15) | **416** | **132 × 28** | **Gift CD** | *Create a CD with built-in slideshow for friends and family* |
| `activitycontainer` | **760** | 35 × 28 | — | |

A `fullview` és az `albumview` **ugyanazon a helyen** (x 5) van — a kettő
egymást váltja. Mind a kettő a `globalbuttons/b132_*` képcsaládot használja
(**132 × 29**).

### Négy gomb, amit ELHAGYTAK

A csomagban `#`-kal kikommentezve:

| elem | pozíció | méret |
|---|---|---|
| `#navback` (+ ikon) | (145, 50) | 26 × 22 |
| `#navfw` (+ ikon) | (173, 50) | 26 × 22 |
| `#listbox_title` / `#listbox_title_button` | (16, 51) | 80 × 14 / 24 × 14 |

Vagyis a mappalistának eredetileg **előre/vissza navigációja** és külön
**„Library" felirata** lett volna. A kiadott változatban helyettük a
`newfolder` gomb áll (**174**, 50, **29 × 22**).

### ❌ Amiben eltérünk

A `MainToolbar.qml` a `ui-audit-mainwindow.md` 4.2 szakasza szerint
hiányolja a `newalbum`-ot és a nézetváltókat. A mért méretek most
megvannak:

| | eredeti | PicasaPy |
|---|---|---|
| sáv magassága | **37** (a `buttonbarsets` háttérképe; a sávhatár a `searchtop` = 35) | **35** ✅ (#587) |
| Import gomb | **111 × 22**, x 6 | **111 × 22** ✅ (#587) |
| új album (`newalbum`) | **29 × 22**, x 124 | **hiányzik** |
| nézetváltó pár | **2 × 30 × 22**, x 160 és 190 | **hiányzik** |
| nézet-beállítások (▾) | **22 × 22**, x 225 | **hiányzik** |
| webkamera | **36 × 22**, x 254 | **hiányzik** |
| keresősáv | **388 × 30**, x **323** | **388 × 30** ✅ (#587) |

*Bizonyítottsági fok: megerősített* (a `respack.yt` nyers rectjei; a
feliratok és súgók a `thumbui_text.tre`-ből).

> Ez a szakasz csak a **geometriát** adja. A mind az öt gomb teljes
> **viselkedése** (mit ír, mit aktivál, milyen feltétellel engedélyezett,
> menüegyenérték) a
> [`picasa-konyvtar-eszkoztar-viselkedes.md`](picasa-konyvtar-eszkoztar-viselkedes.md)
> lapon van.
