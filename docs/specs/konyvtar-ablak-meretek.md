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
> „210 px ≈ 26 %" értéke **egyaránt téves**. A mai
> `Main.qml` `folderPaneWidth` alapértéke **230** — legyen **240**.

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

> A mai `MainToolbar.qml` magassága **34** — legyen **35**.

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
**mind 14 × 14 képpontosak**, és **15 px-enként** követik egymást:

| sorrend | elem | y (vásznon) |
|---|---|---:|
| 1 | `largethumbs` | 76 |
| 2 | `smallthumbs` | 91 |
| 3 | `acquirebutton` | 106 |
| 4 | `viewswitch` | 121 |
| 5 | `horizonadjust` | 136 |
| 6 | `prev` | 151 |
| 7 | `next` | 166 |
| 8 | `fit` | 181 |
| 9 | `1to1` | 196 |
| 10 | `morethumbs` | 211 |
| 11 | `lessthumbs` | 226 |
| 12 | `soloview` | 241 |
| 13 | `replicate` | 256 |
| 14 | `publishswitcher` | 286 |
| 15 | `uploadmgr` | 301 |
| 16 | `histogram` | 316 |
| 17 | `visitweb` | 331 |
| 18 | `makealbum` | 346 |

**Az osztásköz egyenletesen 15 px** (14 px gomb + 1 px hézag); a 13.→14.
között 30 px, tehát ott **csoporthatár** van.

`throttlegroup` (a jobb szélen futó sáv): **16 px** széles.

---

## 5. Az alsó sáv (105 px) — `basecontrolset`

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
> eltérés (olvashatóság, `design-guide.md`). Marad.

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

### 5.8 Az „egy művelet" sáv (haladásjelzés)

| elem | méret |
|---|---:|
| `single_action_container` | **502 × 40** |
| `single_action_group` | 481 × 30 |
| `single_action_message` | 335 × 26 |
| `single_action_return` | **109 × 43** |
| `single_action_close` | **18 × 18** |

### 5.9 Egyéb

| elem | méret |
|---|---:|
| `toggle_right_drawer` | **15 × 16** |
| `thumbui/size` (méretfogantyú) | 20 × 20, jobb alsó sarok |
| `output_label` | 502 × 13 |

---

## 6. Megvalósítási ellenőrzőlista

- [ ] bal panel **240 px** fix (ma 230), **nem** skálázódik átméretezéskor
- [ ] elválasztó **8 px**, fogantyú **8 × 47**
- [ ] felső sáv **35 px** (ma 34)
- [ ] alsó sáv **105 px** (ma 20 + 52 = 72)
- [ ] a nézetváltó gombok **132 × 29 / 132 × 28**
- [ ] `importbutton` **111 × 22**, `newalbum` / `newfolder` **29 × 22**,
      `flatview` / `folderview` **30 × 22**, `folderviewpopup` **22 × 22**
- [ ] keresősáv **388 × 30**
- [ ] a bal panel listája **9 px** bal, **5 px** jobb margóval
- [ ] a rács melletti lebegő gombok **14 × 14**, **15 px** osztásközzel
- [ ] az alsó sáv a **36,5 %**-os pontnál válik ketté
- [ ] képtálca **81 px** magas, a bélyegképsor jobbján **50 px** a három
      gombnak, a „Kijelölés" felirat **középen**
- [ ] `startoggle` / `rotateleft` / `rotateright` **36 × 22**
- [ ] nagyítás-csúszka **127 × 27**, nagyító **25 × 19**
- [ ] a négy kerek kapcsoló **60 × 24** egyenként, hézag nélkül (ma hiányzik)
- [ ] zöld gomb **141 × 35** egy **147 × 44**-es helyen
- [ ] `separator` **2 px**, a 36,5 %-tól jobbra

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
| sáv magassága | **37** (a `buttonbarsets`) | 34 |
| Import gomb | **111 × 22**, x 6 | 100 × 24 |
| új album (`newalbum`) | **29 × 22**, x 124 | **hiányzik** |
| nézetváltó pár | **2 × 30 × 22**, x 160 és 190 | **hiányzik** |
| nézet-beállítások (▾) | **22 × 22**, x 225 | **hiányzik** |
| webkamera | **36 × 22**, x 254 | **hiányzik** |
| keresősáv | **388 × 30**, x **323** | 300 × 24 |

*Bizonyítottsági fok: megerősített* (a `respack.yt` nyers rectjei; a
feliratok és súgók a `thumbui_text.tre`-ből).

> Ez a szakasz csak a **geometriát** adja. A mind az öt gomb teljes
> **viselkedése** (mit ír, mit aktivál, milyen feltétellel engedélyezett,
> menüegyenérték) a
> [`picasa-konyvtar-eszkoztar-viselkedes.md`](picasa-konyvtar-eszkoztar-viselkedes.md)
> lapon van.
