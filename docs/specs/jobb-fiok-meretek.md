# A jobb oldali fiók („Metaadatok") — KÖTELEZŐ méretspecifikáció

**Ez a lap normatív.** A tulajdonos döntése szerint
(`../decisions/szerkeszto-bal-panel.md` 1. pont) a felület **pontosan** úgy
nézzen ki, mint az eredeti Picasa.

Testvérlapok:
[`szerkeszto-panel-meretek.md`](szerkeszto-panel-meretek.md) ·
[`konyvtar-ablak-meretek.md`](konyvtar-ablak-meretek.md).

## 0. Forrás

`rightdrawerpanel.tre` + a `respack.yt` rétegtéglalapjai
([`binaris-regeszet-modszertan.md`](binaris-regeszet-modszertan.md) 14/c).
**80 elem**: `rightdrawerpanel` (16) · `peoplepanel` (14) · `tagpanel` (28) ·
`geopanel` (18) · `propertiespanel` (4).

Ezek a panelek **fix szélességű, saját vásznon** vannak authorolva
(276 × 360), és a `.tre` csak beilleszti őket — **az abszolút pozíciók itt
használhatók**, nem úgy, mint a könyvtár-ablaknál.

---

## 1. ⚠️ A LEGFONTOSABB: EGY fiók, benne fülek — nem négy külön panel

Az eredetiben **egyetlen jobb oldali fiók** van, saját fejléccel, és a
négy tartalom **ugyanabban a fiókban vált**:

> ⚠️ **HELYESBÍTÉS (2026-08-16):** az alábbi ábra fülsávot mutat, de a
> kiadott csomagban **a fülsáv és mind a négy fül `#`-kal ki van
> kommentezva**. Lásd „⚠️ HELYESBÍTÉS: a fülsáv KI VAN KOMMENTEZVE"
> a lap végén. A **fiók mérete és a négy panel egymásra ültetése
> változatlanul érvényes.**

```
rightdrawerpanel/base_decrect            276 széles
├── header                    30 px      ┐
│   ├── size_toggle   14 × 14  (balra)   │ fejléc
│   ├── title_text   218 × 19  (KÖZÉPRE) │
│   └── close         14 × 14  (jobbra)  ┘
├── tab_container            273 × 25    ← a fülsáv
│   ├── tab1  89 × 25   (x 2..91)
│   ├── tab2  89 × 25   (x 94..183)
│   └── tab3 / tab4  89 × 25  (x 186..275 — UGYANAZ a hely!)
└── a tartalom  (y 31-től, x +4 / −2 behúzással)
    ├── peoplepanel      (Személyek)
    ├── geopanel         (Helyek)
    ├── tagpanel         (Címkék)
    └── propertiespanel  (Tulajdonságok)
```

- a fiók **szélessége 280** (`RIGHTDRAWEROFFSET -280`), a tartalom **276**;
- a fejléc **címe „Metaadatok"**, `m_centerXY` + `m_displayfont16` —
  **középre igazítva**, nem balra;
- **három fül látszik egyszerre**: a `tab3` és a `tab4` **ugyanazt a helyet**
  foglalja (x 186..275), tehát a negyedik a harmadikkal cserélődik;
- 3 × 89 + 2 × 3 px hézag = 273.

> ⚠️ **Nálunk ma négy KÜLÖN panel van**, mind saját `SplitView`-cellában és
> **mind más szélességgel**: `TagsPanel` **190**, `PlacesPanel` **320**,
> `PropertiesPanel` **210**, `PeoplePanel` **200**. Se közös fejléc, se
> fülsáv, se egységes szélesség. **Ez a fő szerkezeti eltérés.**

| gomb | méret | súgó |
|---|---:|---|
| `size_toggle` | **14 × 14** | „Váltás a kis és a nagy oldalpanel közt" |
| `close` | **14 × 14** | „Oldalpanel bezárása" |

A `size_toggle` létezése azt is elárulja, hogy a fióknak **két szélessége**
van (kicsi/nagy) — ez nálunk nincs meg.

---

## 2. Személyek (`peoplepanel`)

| elem | méret | pozíció |
|---|---:|---|
| `status_label` | **213 × 14** | x 10, y 6 |
| `addname` (Név hozzáadása) | **163 × 20** | x 0, y 0 |
| `ignore` (Mellőzés) | **163 × 17** | x 0, y 26 |
| `suggestion_yes` | **27 × 22** | x **68** |
| `suggestion_no` | **27 × 22** | x **100** — osztásköz **32 px** |
| `peoplelist` | **260 × 322** | x 8..268 |
| `manual_frame` | **239 × 145** | x 18..257, y 105 |
| `manual_instructions` | 221 × 86 | x 27..248 |
| `manual_cancel` | **98 × 28** | x 89..187, y 210 |
| `manual_add` | **259 × 21** | x 8..267, y 331 |

A javaslat-elfogadó/elutasító pár **27 × 22**, egymás mellett 32 px
osztásközzel — nem szöveges gombok.

---

## 3. Címkék (`tagpanel`)

| elem | méret | pozíció |
|---|---:|---|
| `add_tag_label` | **213 × 14** | x 8, y 6 |
| `input_group` (a beviteli keret) | **266 × 39** | x 5..271, y 23 |
| `taginput` (maga a mező) | **212 × 17** | x 19..231, y 36 |
| `taginput_base` (a mező kerete) | 220 × 22 | x 13..233 |
| `addtag` (+ gomb) | **28 × 28** | x 237..265, y 29 |
| `add_icon` | 16 × 17 | |
| `tag_info` | **255 × 14** | x 8..263, y 65 |
| `taglist` / `taglist_group` | **260 × 123** | x 8..268, y 83..206 |
| `quick_label` | 220 × 14 | y 245 |
| `quick_config` | **12 × 13** | x 249..261 |

### A tíz gyorscímke-gomb — 2 · 3 · 2 · 3 elrendezés

**Minden gomb 21 px magas.**

| sor | gombok | szélesség | y |
|---|---|---:|---:|
| 1. | `quicktag_0` · `quicktag_1` | **128 / 129** | 262 |
| — | `divider` | 242 × **3** | 286 |
| 2. | `quicktag_2` · `quicktag_3` · `quicktag_4` | **85** | 292 |
| 3. | `quicktag_5` · `quicktag_6` | 128 / 129 | 315 |
| 4. | `quicktag_7` · `quicktag_8` · `quicktag_9` | 85 | 338 |

A **kettes** sorok gombjai 128–129 px szélesek (2 px hézag), a **hármas**
sorokéi 85 px (2 px hézag). A `quicktag_group` **266 × 98**.

---

## 4. Helyek (`geopanel`)

| elem | méret | pozíció |
|---|---:|---|
| `places_icon` | 14 × 21 | x 4, y 7 |
| `geo_info` | **243 × 14** | x 18..261 |
| `map_menu` (`popuplist`) | **104 × 19** | x 169..273, y 5 |
| `geolist` | **260 × 60** | x 8..268, y 28..88 |
| `geolist_group` (kerettel) | 260 × 66 | y 25..91 |
| **`mapnode`** (maga a térkép) | **264 × 284** | x 6..270, y 28..312 |
| `loading_base` | 264 × 284 | ugyanott |
| `loading_title` | 213 × 25 | y 117 |
| `loading_icon` | 64 × 52 | y 153 |
| `search_label` | **213 × 14** | y 314 |
| `search_group` | **258 × 28** | x 10..268, y 328 |
| `searchinput` | **212 × 17** | x 19..231 |
| `search` (gomb) | **28 × 28** | x 237..265 |
| `search_icon` | 17 × 17 | |

A keresőmező pontosan ugyanaz a minta, mint a Címkék paneljén:
**212 × 17 mező + 28 × 28 gomb**, 220 × 22-es kerettel.

---

## 5. Tulajdonságok (`propertiespanel`)

**Négy elem, ennyi az egész:**

| elem | méret | pozíció |
|---|---:|---|
| `properties_info` | **253 × 28** | x 11..264, y 4 |
| `propertieslist` | **260 × 234** | x 8..268, y 32..266 |

Se gomb, se beviteli mező — csak egy fejléc-szöveg és egy lista.

---

## 6. Visszatérő minták a fiókban

| minta | méret | hol |
|---|---:|---|
| lista szélessége | **260** (x 8..268) | mind a négy panelen |
| szakaszcím-felirat | **213–220 × 14** | `status_label`, `add_tag_label`, `search_label`, `quick_label` |
| beviteli mező + gomb | **212 × 17** + **28 × 28** | Címkék, Helyek |
| fejléc-gomb | **14 × 14** | `size_toggle`, `close` |
| „párban álló" gomb | **98 × 28** | `manual_cancel` |

**A 260 px-es listaszélesség a fiók egyik jellegadó mérete** — a 276-os
tartalomban 8-8 px margóval.

---

## 7. Megvalósítási ellenőrzőlista

- [ ] **EGY fiók**, nem négy külön panel: közös fejléc + fülsáv, a négy
      tartalom ugyanott vált
- [ ] a fiók **280 px** széles (tartalom 276) — mind a négy nézetnél azonos
      (ma 190 / 320 / 210 / 200)
- [ ] fejléc **30 px**, a cím **„Metaadatok"**, **középre** igazítva
- [ ] `size_toggle` és `close` **14 × 14**, bal, illetve jobb szélen
- [ ] fülsáv **273 × 25**, **három látható fül**, egyenként **89 px**
- [ ] a negyedik fül a harmadikkal **azonos helyen** vált
- [ ] minden lista **260 px** széles (8-8 px margó)
- [ ] Címkék: beviteli mező **212 × 17**, hozzáadás-gomb **28 × 28**,
      címkelista **260 × 123**
- [ ] Címkék: **tíz** gyorscímke-gomb, **2-3-2-3** elrendezésben,
      **21 px** magasan, elválasztóval a 1. és 2. sor közt
- [ ] Helyek: térkép **264 × 284**, helylista **260 × 60**, keresősor a panel
      alján (**212 × 17** + **28 × 28**)
- [ ] Személyek: javaslat-gombok **27 × 22**, **32 px** osztásközzel;
      lista **260 × 322**
- [ ] Tulajdonságok: fejléc-szöveg **253 × 28**, lista **260 × 234**

**Kirajzolt teszt kötelező**, és a javítás nélkül el kell buknia.

---

*Bizonyítottsági fok: megerősített.* A `respack.yt` 80 rétegtéglalapja
(`rightdrawerpanel`, `peoplepanel`, `tagpanel`, `geopanel`,
`propertiespanel`), a `rightdrawerpanel.tre` kötései, és a magyar feliratok
a `panel-feliratok-hu.tsv`-ből.

## ⚠️ HELYESBÍTÉS: a fülsáv KI VAN KOMMENTEZVE (2026-08-16)

A lap eleje azt írja, hogy a fiók **fülsávval** vált a négy tartalom
között. A `respack.yt` nyers olvasata szerint **a fülsáv és mind a négy
fül `#`-kal ki van kommentezva** a kiadott csomagban:

```
#buttcontainer: tab_container            (  2,  5)  273x25
#superbutton(drawer_tab, tab1): tab1     (  2,  5)   89x25
#superbutton(drawer_tab, tab2): tab2     ( 94,  5)   89x25
#superbutton(drawer_tab, tab3): tab3     (186,  5)   89x25
#superbutton(drawer_tab, tab4): tab4     (186,  5)   89x25
```

A `#` az erőforrásnyelvben a kikommentezés jelölése — ugyanaz, mint a
`.tre`-ben és a `picnik` gombnál (`ui-audit-editor.md`).

### Ami a kiadott változatban TÉNYLEG ott van

| elem | pozíció | méret | mi ez |
|---|---|---|---|
| `rect: base` / `docbounds` | (0, 0) | **276 × 388** | a fiók |
| `decrect(insetleft2): base_decrect` | (0, 0) | 276 × 388 | a beljebb húzott keret |
| `header` | (24, 0) | 3 × 30 | a **30 px magas** fejlécsáv |
| `size_toggle` | (**8**, 10) | **14 × 14** | szélesség-váltó (bal/jobb nyíl) |
| `text: title_text` | (**29**, 5) | **218 × 19** | a **cím** |
| `close` | (**255**, 10) | **14 × 14** | bezárás |
| `propertiespanel` | (0, **31**) | **276 × 357** | Tulajdonságok |
| `tagpanel` | (0, **31**) | **276 × 357** | Címkék |
| `peoplepanel` | (0, **31**) | **276 × 357** | Emberek |
| `geopanel` | (0, **31**) | **276 × 357** | Helyek |

**A négy panel PONTOSAN egymáson ül** — azonos pozíció, azonos méret;
egyszerre csak egy látszik.

### Mit jelent ez a megvalósításra

A **lényeg változatlan**: **egyetlen, 276 × 388-as fiók**, közös 30 px-es
fejléccel, és a négy tartalom **ugyanabban a fiókban vált**. A mai négy
külön `SplitView`-panel (190 / 320 / 210 / 200) ettől továbbra is eltér.

**Ami változik:** a váltás **nem fülsávval** történik. A fejlécben csak
három elem van — a szélesség-váltó, a **cím**, és a bezárás. A tartalmat
máshonnan kell váltani (menü vagy a bal panel), és a **cím jelzi**, melyik
van elöl.

> A tervezés során **volt** fülsáv (3 × 89 + 2 × 3 hézag = 273), és a 4.
> fül a 3. helyére került volna. A kiadás előtt kivették.

*Bizonyítottsági fok: megerősített* (a `respack.yt` mind a 16 bejegyzése
a `rightdrawerpanel` alatt; a `#` előtag a kikommentezés jelölése).

## Hogyan vált a felhasználó a négy tartalom között (2026-08-16)

Az előző szakasz nyitva hagyta, honnan vált a felhasználó, ha nincs fülsáv.
**A Nézet menüből.**

### A négy menütétel — hivatalos magyar felirattal

| erőforrás | EN | HU |
|---|---|---|
| `eMenuView::ID_VIEW_PROPERTIES` | Properties | **Tulajdonságok** |
| `eMenuView::ID_CAPTAG` | &Tags | **&Címkék** |
| `eMenuView::ID_VIEW_PEOPLE` | &People | **&Emberek** |
| `eMenuView::ID_VIEW_PLACES` | &Places | **&Helyek** |

A négy panelazonosítót (`rightdrawerpanel/propertiespanel`, `…/tagpanel`,
`…/peoplepanel`, `…/geopanel`) **hét függvény** hivatkozza, köztük a
menü-kezelő `0x005cb990` és a panelváltó `0x0056e1c0` (5 936 bájt).

### A fejléc CÍME a panel neve

A `title_text` (29, 5, 218 × 19) tartalma a panel saját címe:

| panel | erőforrás | HU |
|---|---|---|
| `propertiespanel` | `PropertiesPanel::title` | **Tulajdonságok** |
| `tagpanel` | `TagPanel::tags` | **Címkék** |
| `peoplepanel` | `PeoplePanel::title` | **Emberek** |
| `geopanel` | `GeoPanel::title` | **Helyek** |

**Ugyanaz a szöveg, mint a menütételé** — a cím és a menü egy nyelvet
beszél.

### A fiók nyitása/zárása és a 280 képpont

`thumbui.tre:696`:

```
thumbui/toggle_right_drawer: thumbui/basecontrolset
m_fakehidden
Property setpressed 0
Property showtarget thumbui/right_drawer
Handler varbutton RIGHTDRAWEROFFSET -280 0 1 editpanel/previewimage editpanel/previewimage2
```

| érték | jelentés |
|---|---|
| `RIGHTDRAWEROFFSET = -280` | a fiók **nyitva** |
| `RIGHTDRAWEROFFSET = 0` | a fiók **zárva** |

**A fiók 280 képponttal tolja be a tartalmat** — a panel maga 276 széles,
plusz a 4 képpontos keret. A kapcsoló **két elemet is értesít**
(`editpanel/previewimage`, `editpanel/previewimage2`), hogy az előnézet
átméreteződjön.

Az `m_fakehidden` azt jelenti, hogy a kapcsoló **nem látszó**
kattintható terület — a fiók szélén.

*Bizonyítottsági fok: megerősített* (a négy menütétel erőforrása, a
panelváltó függvény, és a `.tre` kapcsoló-definíciója).
