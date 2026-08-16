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

Az eredetiben **egyetlen jobb oldali fiók** van, saját fejléccel és
fülsávval, és a négy tartalom **ugyanabban a fiókban vált**:

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
