# A szerkesztő FELSŐ SÁVJA (`editpanel/oneup_controls`)

**Ez a lap normatív.** A szerkesztő fejléce **pontosan** így nézzen ki
(`../decisions/szerkeszto-bal-panel.md`: *„a felület PONTOSAN úgy nézzen ki,
mint az eredeti Picasa"*). Testvérlap a bal hasábról:
[`szerkeszto-panel-meretek.md`](szerkeszto-panel-meretek.md).

Kiváltó jegy: **#1905** (a tulajdonos egymás mellé tett felvétele).

## 0. Forrás és módszer

Két, egymástól független forrás — és a lap azért erős, mert **a kettő
egymást igazolja**:

1. **`respack.yt` rétegtéglalapok** — `int16 x0, y0, x1, y1` a 13 bájtos
   rekordfejlécben ([`picasa-respack-format.md`](picasa-respack-format.md) 3.).
   A kötések az `editpanel.tre`-ből.
2. **A tulajdonos felvétele** — `research/Picasa3-vs-PicasaPy-fejlec-elteresek/`,
   1920×1080, a Picasa 3 ablaka az `x = 962…1918` sávban. A vezérlők
   vízszintes kiterjedése képpontra mérve (PIL, oszloponkénti maximális
   eltérés a sáv medián színétől, küszöb 40).

```python
import struct, sys; sys.path.insert(0, "tools/picasa"); import respack
adat = open("research/copy_Picasa_3_7/Picasa3/runtime/respack.yt", "rb").read()
for e in respack.read_index(adat):
    if not e.is_tre and e.name.startswith("layer:editpanel/"):
        x0, y0, x1, y1 = struct.unpack("<hhhh", adat[e.offset:e.offset + 8])
```

### A két forrás egyezése — ez a lap alapja

| elem | mért (felvétel) | tervezővászon (`respack`) |
|---|---:|---:|
| `albumview` („Vissza a könyvtárhoz") | 971…1093 = **122** | **122** |
| `quickupload` | 1222…1256 = **34** | **34** |
| `sbutton` („Lejátszás") | 1329…1423 = **94** | **94** |
| `prev` (kör alakú ◀) | 1440…1470 = **30** | **29** |
| `next` (kör alakú ▶) | 1692…1721 = **29** | **29** |
| `layout_2up_group` (`A`/`AB`/`AA`) | 1733…1848 = **115** | **116** |

⇒ **A tervezővászon méretei a futásidejű képpontméretek.** Nincs skálázás.
(A ±1 az élsimítás és a JPEG-tömörítés.)

## 1. A sáv váza

| elem | méret | horgony (`editpanel.tre`) |
|---|---:|---|
| `oneup_controls` | **520 × 37** | `insetleft`, `m_offsetT` + **`m_centerX`** |
| `insetleft` | — | `root`; bal él `root.bal + LEFTDRAWEROFFSET` (alap **279**), jobb él `root.jobb + RIGHTDRAWEROFFSET`, alsó él `root.alsó − 92` |

**A sáv a képterület fölött vízszintesen KÖZÉPEN áll**, nem az ablak
közepén — a bal fiók 279 képpontja ki van véve belőle.

*Igazolás a felvételen:* `insetleft` = 1241…1918, közepe **1579,5**; az
`oneup_controls` bal éle a mért `sbutton`-ból visszaszámolva **1319**, a
jobb 1319 + 520 = **1839**, közepe **1579** ✓.

## 2. A vezérlők — teljes lista, eltolás az `oneup_controls` bal élétől

A tervezővászon `oneup_controls`-a `x = 280…800`, `y = 0…37`; az alábbi
eltolások ebből számoltak. **A méret és az eltolás KÖTELEZŐ.**

| elem | méret | Δx a sáv bal élétől | y | alapból |
|---|---:|---:|---:|---|
| `upload_buttons_container` | 34 × 22 | **−97** | 9…31 | látszik |
| ↳ `quickupload` | 34 × 22 | −97 | 9…31 | `m_hidden` |
| ↳ `quickupload-icon` | 23 × 15 | −91 | 12…27 | |
| `weblink` | 43 × 22 | −53 | 9…31 | `m_hidden` |
| `editcollage` / `editslideshow` | 128 × 22 | −138 | 9…31 | `m_hidden` |
| `sbutton` („Lejátszás") | **94 × 22** | **+10** | 9…31 | látszik |
| ↳ `sbutton_icon` | 11 × 11 | +16 | 15…26 | |
| `filmcontainer` | **288 × 33** | **+114** | 3…36 | `m_centerX` |
| ↳ `filmcontainer_overlay_L` | 20 × 33 | +114 | 3…36 | |
| ↳ `filmcontainer_overlay_C` | 248 × 33 | +134 | 3…36 | |
| ↳ `filmcontainer_overlay_R` | 20 × 33 | +382 | 3…36 | |
| ↳ `prev` | **29 × 30** | +119 | 6…36 | `m_offsetLT`, **`m_autorepeat`** |
| ↳ `filmclip` / `filmstrip` | **214 × 28** | +151 | 6…34 | `m_offsetLRB` |
| ↳ `indicator` | **28 × 28** | — | 6…34 | **`m_centerX`** |
| ↳ `next` | **29 × 30** | +371 | 6…36 | `m_offsetRT`, **`m_autorepeat`** |
| `uploadchanges` | 34 × 22 | +423 | 9…31 | `m_hidden` |
| ↳ `uploadchanges_icon` | 24 × 17 | +429 | 12…29 | |
| `layout_2up_group` | **116 × 24** | **+413** | 8…32 | jobbra igazítva |
| ↳ `only_1up_toggle` (`A`) | 39 × 24 | | 8…32 | `Property setpressed 1` |
| ↳ `ab_2up_toggle` (`A B`) | 39 × 24 | | 8…32 | |
| ↳ `aa_2up_toggle` (`A A`) | 39 × 24 | | 8…32 | |
| ↳ `swap_2up_focus` | 36 × 22 | | 9…31 | `m_hidden` |
| ↳ `swap_2up_layout` | 36 × 22 | | 9…31 | `m_hidden` |

**A `layout_2up_group` NEM az `oneup_controls` gyereke geometriailag** — a
mért helye 1733…1848, az `oneup_controls` jobb éle 1839: a hármas
**túlnyúlik** a sávon 9 képponttal, és a bal éle 106 képponttal a sáv jobb
éle előtt van. Ugyanez a tervezővásznon: 693…809 a 280…800-as sávban
(−107 … +9). **A tervezővászon eltolása érvényes futásidőben is.**

### A „Vissza a könyvtárhoz" gomb NEM a sáv gyereke

`editpanel/albumview: root` — az ABLAKHOZ horgonyzott, nem a sávhoz:
**122 × 22, `x = root.bal + 10`, `y = 9…31`**, ikonja (`albumview_icon`)
**17 × 15** a bal szélen (`m_buttoniconleft`), a felirata `Back to Library`
= **„Vissza a könyvtárhoz"**, buboréksúgója `Return to organized thumbnails`.
A felvételen mérve: 971…1093, az ablak tartalmi bal éle 961 ⇒ +10 ✓.

A `.tre` ki is mondja: `Property alias thumbui/albumview` — a szerkesztő
ugyanazt a gombot használja, amit a könyvtár fejléce. Ugyanígy a
`sbutton`: `Property alias thumbui/sbutton`.

## 3. A vezérlők SORRENDJE

Balról jobbra, ahogy a felvételen mérve áll:

```
[albumview 122]  …  [quickupload 34]  …  [sbutton 94]
     …  [prev 29][filmstrip 214][next 29]  …  [A|AB|AA 116]
```

`971…1093` · `1222…1256` · `1329…1423` · `1440…1470` · `1499…1656` ·
`1692…1721` · `1733…1848`.

## 4. A „paletta-ikonos gomb" = **`editpanel/quickupload`** (#1905/2)

A #1905 „paletta-ikonos gombnak" nevezte. **Nem paletta:** a 23 × 15-ös
ikon egy **hármas fénykép-pakli, előtte zöld FELFELÉ nyíllal** — a
`respack.yt` `layer:editpanel/quickupload-icon` rétege képpontra ugyanaz,
mint a felvételen (`x 1222…1256`).

| | |
|---|---|
| elem | `editpanel/superbutton(listheader_button): quickupload` |
| buboréksúgó (`editpaneltext.tre`) | **„Upload to your Web Albums Drop Box"** |
| parancsazonosító | **`OneUp::ID_QUICKUPLOAD`** (`0x00cae564`, hivatkozza `0x007327a0`) |
| értesítés-tokenek | `QuickUploader::progress` (`0x00cb7144` → `0x007b3cb0`), `QuickUploader::errorMsg` (`0x00cb7170` → `0x007b3d70`) |
| kötés | `0x00567a00` (elemnév-feloldás), `0x005d59f0` (elemnév-tábla) |

**A párja ugyanabban a tárolóban:** `editpanel/uploadchanges`, ikonja
kör-nyilas fénykép-pakli, buboréksúgója **„Update online copy with this
version"**. Mindkettő `m_hidden` alapból, mindkettő `m_offsetRT` az
`upload_buttons_container`-ben ⇒ **egymást kizárva, ugyanazon a helyen**
jelennek meg.

*A `0x007327a0` a `OneUp::` névtér parancstáblája: `ID_FILE_SAVE`,
`ID_FILE_OPENINANEDITOR`, `ID_PICTURE_HIDE`, `ID_PICTURE_ROTATECLOCKWISE`,
`ID_QUICKUPLOAD`, `ID_VIEWALBUM`.*

## 5. A filmszalag VISELKEDÉSE (#1905/3)

### 5.1 Pontosan HÉT férőhely — és a képlet kijön egészre

| | mért |
|---|---:|
| bélyegkép | **28 × 28** (felvétel: `x 1503…1531`, `y 57…85`) |
| osztásköz | **31** (1503 · 1534 · 1565 · 1596 · 1627) |
| rés két kép közt | **3** |
| `filmclip` szélessége (`respack`) | **214** |

`7 × 28 + 6 × 3 = 214` — **pontosan a `filmclip` szélessége.** Nem
kerekítés: a nyolcadik férőhely 245 lenne, a hatodik 183.

⇒ **A szalag hét férőhelyes, fix.** Nem zsugorodik kevesebb képnél.

### 5.2 Az AKTUÁLIS kép mindig a KÖZÉPSŐ férőhelyen áll

Az `indicator` kötése `m_centerX` a `filmstrip`-ben (`editpanel.tre:1129`)
— a kijelölés-keret a szalag közepén rögzített, tehát **a szalag mozog
alatta**, nem a keret.

*Mérve:* a mappában **öt** kép van, az aktuális a **harmadik**. A képek a
2…6. férőhelyen állnak, az 1. és a 7. üres; az aktuális bélyegkép közepe
**1578,5**, a `filmclip` közepe **1577**. Ha a szalag balról töltene, a
harmadik kép a 3. férőhelyre esne — nem oda esik.

### 5.3 A kijelölés-keret (`indicator`) rajza

28 × 28, a közepe **átlátszó** (24 × 24 = 576 képpont), kerete **két
képpont**: kívül **`#009EFF`** (108 képpont = 1 képpont vastag gyűrű),
belül **`#D4D4D4`** (100 képpont). A felvételen mért szín `(0, 158, 254)`
— a JPEG-tömörítés egy egységnyi eltérése.

### 5.4 A két léptetőnyíl

Kör alakúak (`globalbuttons/lfs_*`, `globalbuttons/rfs_*`), **29 × 30**, a
`filmcontainer` bal és jobb szélén (`m_offsetLT` / `m_offsetRT`), és
**mindkettőn `m_autorepeat`** ⇒ **nyomva tartva folyamatosan léptetnek.**

### 5.5 ⛔ Amit a kattintásról NEM tudunk

Hogy a **bélyegképre kattintás** kiválasztja-e azt a képet, **NINCS
mérve.** Az olcsó lánc kimerült: az `editpanel.tre` a `filmstrip`-re
egyetlen `m_scaleXY`-t ad és **semmilyen `Handler`/`Property` sort**; a
szövegtárban nincs rá felirat; a sztring-xref öt függvényt ad
(`0x00566a70` = az infósor-építő, `0x00567820`, `0x00579360`,
`0x00579550`, `0x005de8e0`), egyikben sem kattintás-szemantika.

**A megszerzés útja:** a `CFilmstrip::vftable` (`0x00c9359c`,
RVA `0x0089359c`) egérkezelő rekesze — célzott Ghidra-kör
(`picasa-x86-research`).

*A centrírozás (5.2) ettől függetlenül MÉRT: ha a kattintás kijelöl,
a szalag szükségszerűen újraközepez.*

## 6. Eredeti / nálunk / teendő

A „nálunk" oszlop **mérés** a mai `main`-en
(`src/picasapy/app/qml/PicasaPy/PhotoViewer.qml`, `6047135a`).

| | eredeti (mért) | nálunk (mért) | teendő |
|---|---|---|---|
| sáv magassága | **37** | `height: 46` (:556) | 37 |
| „Vissza a könyvtárhoz" | ikon (17 × 15) + kétsoros felirat, **122 × 22**, ablak bal éle + 10 | `"◀ " + qsTr(...)`, csak szöveg (:562) | ikon + kétsoros, 122 × 22 |
| feltöltés-gomb | `quickupload` 34 × 22, zöld nyilas fénykép-pakli | **nincs** | új vezérlő → **#1935** |
| „Lejátszás" | `sbutton` **94 × 22**, ikon balra | `"▶ " + qsTr("Play")` (:597) | 94 × 22 |
| `A`/`AB`/`AA` | a szalag **UTÁN**, jobb szélen, 3 × **39 × 24** | a szalag **ELŐTT**, 28/32/32 (:616–:640) | sorrend + méret |
| léptetőnyilak | **kör alakúak**, 29 × 30, `m_autorepeat` | szögletes `◀`/`▶`, 30 széles, nincs autorepeat (:641, :709) | kör alak + autorepeat |
| szalag szélessége | **fix 214** (7 férőhely) | `Math.min(7, mappaDarab) * 44` (:685) | fix 214 |
| bélyegkép | **28 × 28**, osztásköz **31** | delegate **42 × 38**, osztásköz 44 (:691) | 28 × 28 / 31 |
| aktuális kép helye | **mindig a középső férőhely** | `currentIndex` a lista elején is lehet | középre |
| kijelölés-keret | 28 × 28, `#009EFF` + `#D4D4D4`, 1-1 képpont | tömör `Theme.thumbSelection` háttér (:692) | kétszínű keret |
| szalag forrása | a mappa képei | **a mappa képei** ✓ (`d745446c`, #1905/1) | kész |
| hisztogram-doboz | alsó éle **`root.alsó − 95`** (`nerdview_container`, `editpanel.tre:1028`) | `anchors.bottom: parent.bottom`, `bottomMargin: 95` — de a **bal fiók** aljához (:1043) | az ABLAK aljához |

### A hisztogram-doboz (#1905/3) — mért bizonyíték

A felvételen az eredeti doboz fejléc-felirata `y 779…792`, a
hisztogram-rajz `y 798…857` (**59 magas** = a `nerdview/histoback`
`213 × 59`-e ✓). A doboz alja így a kék infó-csík fölé, `y ≈ 927`-re esik.

Nálunk: fejléc `y 691…704`, rajz `y 712…782` (**70 magas**) ⇒ a doboz
**mintegy 96 képponttal feljebb** ül, mert a bal fiók aljához horgonyzott,
és a fiók az alsó tálca fölött ér véget.

## 7. Nyitott kérdések mérlege

`0 nyílt · 6 lezárva · 1 blokkolt · 0 hatókörön kívül · 0 csak-nyitva`

| kérdés | állapot |
|---|---|
| a fejléc képpontos geometriája | **LEZÁRVA** — 1–3. szakasz |
| a „paletta-ikonos" gomb funkciója | **LEZÁRVA** — 4. szakasz |
| hány bélyegkép fér ki a szalagon | **LEZÁRVA** — 7, 5.1 |
| mit tesz a két nyíl | **LEZÁRVA** — léptet, `m_autorepeat`, 5.4 |
| hol áll az aktuális kép | **LEZÁRVA** — mindig középen, 5.2 |
| a hisztogram-doboz horgonya | **LEZÁRVA** — `root.alsó − 95`, 6. |
| mi történik a bélyegképre KATTINTVA | **BLOKKOLT** — célzott Ghidra-kör a `CFilmstrip::vftable`-re (`0x00c9359c`), 5.5 |

## 8. Amit KIZÁRTAM

- **„A `respack.yt` abszolút koordinátái nem használhatók."** Ezen a
  panelen **használhatók**: hat vezérlő szélessége képpontra egyezik a
  felvétellel, és a sáv középre igazítása is a tervezővászonból jön ki.
  A [`picasa-respack-format.md`](picasa-respack-format.md) figyelmeztetése
  a `.tre`-vel való ütközésre vonatkozik — itt nincs ütközés.
- **„A gomb paletta."** Nem az: fénykép-pakli + zöld felfelé nyíl, a
  buboréksúgó kimondja, hogy feltöltés.
- **„A szalag a képek számához igazodik."** Nem: fix 214 képpont, hét
  férőhely; kevesebb képnél a szélső férőhelyek üresen maradnak (mérve).

*Bizonyítottsági fok: **megerősített** a geometriára (két független
forrás egyezik), a `quickupload` azonosítására és a hét férőhelyre;
**erős** a centrírozásra (a kötés + egy mért eset); a kattintás
szemantikája **nincs mérve**.*
