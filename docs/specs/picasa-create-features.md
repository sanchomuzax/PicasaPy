# A „Létrehozás" menü funkciói — az eredeti működés (2026-08-07)

Forrás: a Picasa 3.9.141.259 telepítése — a `respack.yt`-ből kinyert `.tre`
elrendezés- és szövegforrások (`tools/picasa/respack.py`), a `Picasa3.exe`
string-táblája és a `Picasa3i18n.dll` feliratai.

Eddig ezekről a funkciókról **csak a menüpont neve** volt meg
(`ui-audit-menus.md`, 6. Létrehozás). Itt a tényleges működés.

## 1. Képkollázs (`ID_COLLAGEMAKER`)

### 1.1 Hat kollázs-típus

Az `.exe` `collage::*_desc` sztringjeiből, a belső kulcsokkal együtt:

| kulcs | név | leírás (eredeti) |
|---|---|---|
| kulcs (`theme`) | UI-név (angol / magyar) | leírás | belső osztály |
|---|---|---|---|
| **`picturepile`** | Picture Pile / **Képkupac** | „Looks like a pile of scattered pictures" | `CPileTheme` |
| **`picturegrid`** | Mosaic / **Mozaik** | „Automatically fit pictures into the page" | `CGridTheme` |
| **`framegrid`** | Frame Mosaic / **Képkockamozaik** | „A mosaic with a prominent center picture" | `CFrameGridTheme` |
| **`regulargrid`** | Grid / **Rács** | „Arrange pictures into regular rows and columns" | `CRegularGridTheme` |
| **`contactsheet`** | Contact Sheet / **Indexkép** | „Thumbnails with an informative header" | `CContactSheetTheme` |
| **`multiexp`** | Multiple Exposure / **Többszörös exponálás** | „Superimpose pictures over one another" | `CMultiExposureTheme` |

**Forrás (2026-08-07, célzott keresés):** az `.exe` string-táblájában a kilenc
téma-kulcs **egyetlen összefüggő tömbben** áll:

```
polaroid | whiteborder | noborder | picturepile | picturegrid |
regulargrid | multiexp | contactsheet | framegrid
```

Az első három a **keret**-téma, a maradék hat a **kollázs-típus**. A hozzárendelést
a C++ osztálynevek (RTTI) erősítik meg: `CPileTheme`, `CGridTheme`,
`CRegularGridTheme`, `CFrameGridTheme`, `CMultiExposureTheme`,
`CContactSheetTheme`, valamint `NoBorderTheme`, `WhiteBorderTheme`,
`PolaroidBitmapTheme` — plusz egy `DimmedBitmapTheme` (a „tompított" háttér-mód)
és a `CollageThemeList` gyűjtő.

> **⚠️ Csapda a nevekben:** a UI-beli **„Mozaik"** kulcsa `picturegrid`, a
> **„Rács"**-é viszont `regulargrid` — vagyis a „grid" szó a *rossz* helyen áll
> ahhoz képest, amit az ember tippelne. Aki a UI-névből következtet, elhibázza.
> A `regulargrid` ↔ Rács a leírásból egyértelmű („**regular** rows and columns"),
> a `framegrid` ↔ Képkockamozaik pedig az ikonnévből (`#frame_grid_icon`); a
> `picturegrid` ↔ Mozaik kizárásos alapon adódik, és ez az egyetlen tétel, amit
> egy mentés még megerősíthetne.
>
> A tömb sorrendje **nem** a UI-sorrend — a felületen Képkupac · Mozaik ·
> Képkockamozaik · Rács · Indexkép · Többszörös exponálás a sorrend.

### 1.2 Három képkeret-stílus

| kulcs | név | leírás |
|---|---|---|
| `noborder` | (nincs) | „Just the picture without a border" |
| `whiteborder` | Fehér szegély | „A plain white border" |
| `polaroid` | Polaroid | „Looks like a familiar brand of instant camera" |

A **Polaroid keretnél** külön képfelirat-lehetőség van: *„Show captions as
text on pictures with an »Instant Camera« border"* — vagyis a felirat csak
ennél a keretnél jelenik meg a képen.

### 1.3 Beállítások (a `collagepanel` feliratai)

- **Két fül:** `Settings` (Beállítások) és `Clips` (Klipek).
- **Grid Spacing** csúszka (`None` … `Max.`).
- **Draw Shadows** jelölő — árnyékrajzolás.
- **Show Captions** jelölő (ld. fent).
- **Background Options:** `Solid Color` · `Use Image` · `Use selected`
  (a kijelölt kép legyen a háttér). Az `.exe`-ben a háttér-módok:
  `solid`, `dimmed`, és a **`collage::avgcolor`** — vagyis a kollázs
  háttere lehet a képek **átlagszíne** (ugyanaz az `avgcolor`, amit a
  `color:` keresés is használ, ld. `picasa-ini-format.md`).
- **Page Format:** oldalarány-választó (`Portrait` / `Landscape` + arány-
  lista), és **egyéni oldalarány** felvehető — ehhez tartozik a
  `runtime/customaspectratio.fen` dialógus. A listában szerepel a
  **„Current display"** (a képernyő aktuális mérete).
- **Randomizálók:** `Shuffle Pictures` (sorrend) és `Scramble Collage`
  (elrendezés).

### 1.4 Kép-szintű műveletek a vásznon

Rétegsorrend: `Move to the top of the pile` · `Move picture up` ·
`Move picture down` · `Move to the bottom`. Továbbá `Set as Background`,
`Set as Frame Center`, `Remove` (Del), `Select All` (Ctrl-A),
`Select None` (Ctrl-D).

**Forgatás-illesztés (snap):** a `snap_12` / `snap_3` / `snap_6` / `snap_9`
gombok az óralap szerint ~~0° / 90° / 180° / 270°~~ **0° / +90° / +180° /
−90°**-ra igazítanak. *(2026-08-17-i helyesbítés: a `snap_9` a binárisban
`−90.0f`-et ad át — `0xcf50d0`, `0x0082e25f` —, nem 270°-ot. Rajzban
ugyanaz, tárolásban nem. A „270 fok" a helyi menü felirata
[`Rotate::ID_COLLAGE_ALIGN_270`], nem a tárolt érték.)*
Vonszolás közben a kijelzett értékek formátuma: `Angle: %d` és
`Scale: %d%%` (`collage::angle_format`, `collage::scale_format`) — a szöget
a kiírás előtt a Picasa **negálja** (`0x00868947`).

> **A vászon teljes viselkedése — a gyűrű (mozgatás, forgatás+méretezés,
> módosítók), a három helyi menü, a témánkénti panelkép, az oldalformátum-
> lista és a kimenet — külön lapon:
> [`picasa-kollazs-felulet.md`](picasa-kollazs-felulet.md).**

### 1.5 Mentés, projektfájl, automatikus mentés

- **Kimenet:** JPG a **„Collages"** albumba, a **Projektek** gyűjteményen
  belül (`CCollageManager::CollagesFolder` = `Collages`, tooltip: *„Save as
  a JPG image in the Collages album (within the Projects collection)"*).
- **Projektfájl: `.cxf`** — a kollázs szerkeszthető állapota. Mentéskor
  `.jpg.tmp` és `.cxf.tmp` átmeneti fájlok készülnek.
- **Automatikus mentés + helyreállítás:** `CAutosaveCollageThread`,
  `autosave.cxf`, és a `collage::recoveredautosave` / `lastautosave`
  üzenetek — a Picasa összeomlás után felajánlotta a visszaállítást.
- A kimeneti mappa mellé **`.picasa.ini` készül**. ⛔ **HELYESBÍTVE
  (2026-09-05):** a lap korábban azt állította, hogy `[encoding] utf8=1` és
  `[Picasa] name=…` szekciókkal — **az állítás SZTRING-SZOMSZÉDSÁGBÓL
  következett** („az `.exe`-ben közvetlenül az `autosave.cxf` után állnak
  ezek a format-sztringek"), és **téves**. Ezeket a formátumsztringeket a
  `FUN_0068ac80` használja, amelynek a hívási lánca RTTI-vel feloldva a
  **`PrepareCollection`** / **`AlignedImageCollection`** osztályokhoz vezet
  — az **export/előkészítés** ága, nem a kollázs-mentés. A valódi kimenet a
  felhasználó gyűjteményében `[Picasa]` + `P2category=Projects (internal)`,
  és a korpuszban **egyetlen** `[encoding]` szekció sincs (#1050). Részletek:
  [`picasa-ini-format.md`](picasa-ini-format.md), „a `[encoding]` fejléc".

### 1.6 A `.cxf` formátum — MEGFEJTVE valódi mintából (2026-08-07)

A felhasználó a Windows-os Picasával készített egy kollázst, és csatolta a
projektfájlt (#436). A formátum: **UTF-8 XML, CRLF sorvégekkel.**

```xml
<?xml version="1.0" encoding="utf-8" ?>
<collage version="2" format="15:10" orientation="portrait" theme="picturepile"
         shadows="1" captions="1" albumUID="a4ef8e0fd2dbb152d25d79eb2bd2a28b">
 <albumTitle>AI</albumTitle>
 <albumDate>2023. november</albumDate>
 <background type="solid" color="FFFFFFFF"/>
 <spacing value="0.000000"/>
 <node x="0.297852" y="0.248047" w="0.274210" h="0.219401"
       theta="-0.009167" scale="337.000000">
  <theme>polaroid</theme>
  <src>$My Pictures\AI\38ae21c1-….png</src>
  <uid>129d7730c524d5240000000000000000</uid>
 </node>
 …
</collage>
```

| mező | jelentés |
|---|---|
| `version="2"` | formátumverzió |
| `format="15:10"` | **oldalarány szövegként**, `SZ:M` alakban |
| `orientation` | `portrait` / `landscape` — az arány ehhez képest forog |
| `theme` (gyökér) | a **kollázs-típus** kulcsa (ld. 1.1); a mintában `picturepile` |
| `shadows`, `captions` | `0`/`1` kapcsolók |
| `albumUID` | 32 hex — ugyanaz az album-token, mint a `[.album:<token>]` szekcióké |
| `<albumTitle>`, `<albumDate>` | a Contact Sheet fejlécéhez és a mentett album nevéhez |
| `<background type="solid" color="FFFFFFFF"/>` | **ARGB hex**. A `type="image"` alakja MÁS — ld. 1.6/e alább |
| `<spacing value="…"/>` | 0..1 float (a Grid Spacing csúszka) |

#### 1.6/e A KÉPHÁTTÉR alakja — golden-mintából (2026-08-19, #1009)

A `type="image"` **nem** az egyszínű alak `<src>`-cel kiegészítve: a Picasa
ilyenkor a `color` attribútumot **el is hagyja**, és a képet gyerekelemben
adja meg. Két valódi mintából (`AI2.cxf`, `AI5.cxf` a golden-készletben),
karakterre:

```xml
 <background type="image">
  <src>$My Pictures\AI\2a655925-cb0c-4fc0-828c-6d0107a9ba20.png</src>
 </background>
```

Két további megfigyelés ugyanerről a két mintáról:

1. A `<background><src>` **ugyanaz az útvonal**, mint a fájl valamelyik
   `<node><src>`-e: a háttér a kollázs SAJÁT képeinek egyike. Ezt a bináris
   is megerősíti — az előnézetet a `0x00830a00(this, index)` tölti fel, és
   `index == -1` esetén kilép (`0x00830a8b`), tehát a hivatkozás **index**,
   nem szabad útvonal.
2. Mindkét mintában a háttér a csomópontlista **első** eleme (9 kép közül).
   Ez *erős, de nem megerősített* jel arra, hogy a módváltás alapból az
   elsőt választja — nem zárható ki, hogy a felhasználó választotta. A
   PicasaPy ezért **alapértelmezésként** veszi (#1009), amit a kijelölés
   felülír.

A háttérként használt kép a `<node>`-ok között is ott marad, a saját
keretével (a mintákban `polaroid`, illetve `noborder`) — a `dimmed` téma
egyik mintában sem fordul elő.

**Kép-csomópontok (`<node>`):**

| attribútum | jelentés |
|---|---|
| `x`, `y` | a kép bal-felső sarka, **a vászon arányában** (0..1) |
| `w`, `h` | a kép mérete ugyanígy, arányosan |
| `theta` | **forgatás radiánban** (a mintában −0,14…+0,001 ≈ −8°…0°) |
| `scale` | képpont (a mintában 337 / 303 / 280 / 263 / 249 / 238) — a forrás vetített szélessége |
| `<theme>` | **a keret KÉPENKÉNT állítható** (`polaroid`), nem csak globálisan! |
| `<src>` | útvonal **változó-behelyettesítéssel**: `$My Pictures\…`, Windows-os fordított perjelekkel |
| `<uid>` | 32 hex, de csak az első 16 nem nulla — a kép 64 bites azonosítója 128 bitre töltve |

**Két meglepetés:**

1. **A keret képenkénti** (`<theme>` a `<node>`-on belül) — a UI globálisnak
   mutatja, de az adatmodell megengedi a vegyes kollázst.
2. **A pozíció és méret arányos (0..1), a `scale` viszont képpontban van** —
   vagyis a fájl felbontásfüggetlenül tárolja az elrendezést, de megőrzi az
   eredeti vetítési méretet is.

**A kimeneti mappa `.picasa.ini`-je** mindössze ennyi:

```ini
[Picasa]
P2category=Projects (internal)
```

Vagyis a **Projektek gyűjteménybe sorolást a `P2category` kulcs végzi** —
ezt a `picasa-ini-format.md` eddig csak „webalbumból letöltött album"
jelentéssel ismerte. Ez a kulcs tehát általánosabb: **gyűjtemény-hovatartozás**.

### 1.6/b A `theme` és a szegély azonosítói — MEGVANNAK a binárisból (2026-08-13)

A `.cxf` `theme` attribútum hat lehetséges értéke egy tömbben áll az `.exe`-ben
(`0x00829df0`, `0x0082e8b0`, `0x00841550` — mindhárom ugyanazt a sorrendet
használja, tehát ez a **kanonikus sorrend** is):

| `theme=` | magyar név | leírás (`collage::*_desc`) |
|---|---|---|
| `picturepile` | Képkupac | szétszórt képek hatását kelti |
| `picturegrid` | Mozaik | a képek automatikus illesztése az oldalra |
| `regulargrid` | Rács | szabályos sorokba és oszlopokba rendezés |
| `multiexp` | Többszörös exponálás | képek egymás tetejére helyezése |
| `contactsheet` | Indexkép | miniatűr tájékoztató fejléccel |
| `framegrid` | Képkockamozaik | mozaik hangsúlyos központi képpel |

Az **alapértelmezés `picturepile`** (`0x008342b0`, ugyanott a cím
alapértelmezése `CollageSpec::Untitled` → „Névtelen").

A szegély-azonosítók a `0x00835610` leképezőben: **`noborder` · `whiteborder`
· `polaroid` · `dimmed`**. (A `dimmed` a felületen nem választható külön
stílusként — a háttérként használt képre alkalmazza a program, ld. 1.9.5.)

A háttérnél a `solid` érték a writer (`0x008347b0`) szótárában szerepel.

Még nyitott: az `$My Pictures` mellett milyen további **útvonal-változók**
léteznek, és a képi háttér pontos attribútumai.

### 1.6/c Az eredeti mezőnév-lista (az `.exe`-ből, összevetésül)

Az `.exe` egy tömbben tartalmazza a kollázs-specifikáció mezőneveit:

```
orientation · portrait · landscape · theme · shadows · captions
albumUID · albumID · theta · scale · background · spacing
albumTitle · albumDate
```

Olvasat: a specifikáció **képenként** tárolja a `theta` (forgatás) és
`scale` (méret) értéket — ezért tud a „kupac" típus pontosan visszaállni —,
album-szinten pedig a témát, tájolást, árnyékot, feliratot, hátteret és
térközt. A `%d:%d` formátum **az oldalarányé** (`format="15:10"`), nem a
háttérszíné — az ARGB hexaként megy ki. A `CollageSpec` alapértelmezései a
binárisból (`0x008342b0`): cím „Névtelen", téma `picturepile`, oldalarány
**4:3**, háttér **`0xFF000000` (átlátszatlan fekete**).

### 1.6/d A `.cxf` ÍRÓJA a binárisból — a mintát kiegészítve (2026-08-16)

Az 1.6 egy valódi mintából olvasta ki a formátumot. A **writer**
(`0x008347b0`, 3023 b) most utasításszinten is megvan, és ez **eldönti a
mintából nem látszó eseteket**.

**Három szerializáló hívás — ez adja meg, mi attribútum és mi gyerekelem:**

| hívás | mit csinál | példa |
|---|---|---|
| `0x009bfed0(szülő, név)` | **gyerekelem** létrehozása | `collage`, `background`, `spacing`, `node` |
| `0x009c0330(elem, név, érték)` | **attribútum**, formázott értékkel | `version`, `format`, `x`, `theta` |
| `0x009c0640(elem, név, szöveg)` | **gyerekelem szöveges tartalommal** | `albumTitle`, `theme`, `src`, `uid` |

A valódi minta (1.6) mind a három besorolást igazolja — a mintában pontosan
azok az attribútumok, amiket a `0x009c0330` ír, és pontosan azok a
szöveges gyerekelemek, amiket a `0x009c0640`.

**Az írás sorrendje, ahogy a writer végigmegy:**

```
collage                                        ← 0x009bfed0
  version    = "%d"        → 2                 ← 0x008347e8
  format     = "%d:%d"     → SZ:M              ← 0x0083483c  (x1−x0 : y1−y0)
  orientation = portrait | landscape           ← 0x0083487b  ([spec+0x20]==1 → portrait)
  theme      = <a hat típus kulcsa>
  shadows    = "%d"
  captions   = "%d"
  albumUID   = <32 hex>
  <albumTitle>…</albumTitle>                   ← 0x009c0640
  <albumDate>…</albumDate>                     ← 0x009c0640
  background                                   ← 0x009bfed0
     type  = "solid"   color = "%08X"          ← ARGB, nagybetűs hex
     — VAGY —
     type  = "image"   <src>…</src>            ← 0x009c0640
  spacing                                      ← 0x009bfed0
     value = …
  node                            (képenként EGY)
     x = "%f"  y = "%f"  w = "%f"  h = "%f"
     theta = "%f"   scale = "%f"
     <theme>…</theme>   <src>…</src>   <uid>…</uid>
```

**Amit ez az 1.6-hoz képest ÚJ:**

1. **A képi háttér alakja megvan** — az 1.6 még azt írta, hogy *„a `type` más
   értékei további mintából derülnek ki"*. Nem kell minta: a writer szótárában
   **pontosan két érték** van, `solid` és `image`, és a képi ágban `color`
   helyett egy **`<src>` szöveges gyerekelem** áll (`0x00834877`–`0x008348a8`).
2. **Nincs harmadik háttértípus.** A felület „a képek átlagszíne" választása
   (`collage::avgcolor`) **`solid`-ként** íródik ki, a kiszámolt színnel — a
   fájlban nem marad nyoma, hogy átlagszínből jött.
3. **A `format` a vászon két oldalának KÜLÖNBSÉGÉBŐL** számolódik
   (`[spec+0x1c]−[spec+0x14]` és `[spec+0x18]−[spec+0x10]`), tehát a
   specifikáció téglalapként tárolja, nem arányként.
4. **A színformátum `%08X` — NAGYBETŰS** nyolc jegy, nullákkal feltöltve.

*Bizonyítottsági fok: megerősített* (a writer utasításai + a valódi minta
mint kereszt-ellenőrzés).

### 1.6/e A `<node>` mértékegységei — a mintából KISZÁMOLVA (2026-08-18)

Az 1.6 táblázata a `scale`-t „a forrás vetített szélességeként" olvasta, és
nem mondta ki, hogy az `x/y/w/h` **tengelyenként** arányos-e. A #960
bekötéséhez ezt el kellett dönteni; a minta első csomópontja eldönti.

Álló, `format="15:10"` lapon (a lap 1024 × 1536 lapegység, `0xcf3f68 =
1/1024`):

| a fájlban | átszámolva |
|---|---|
| `x=0,297852` | 0,297852 · 1024 = **305,0** lapegység (egész!) |
| `y=0,248047` | 0,248047 · 1536 = **381,0** lapegység (egész!) |
| `w=0,274210` | 0,274210 · 1024 = 280,8 |
| `h=0,219401` | 0,219401 · 1536 = **337,0** |
| `scale=337,0` | = a doboz **nagyobbik** oldala |

Három, egymástól független szám esik egybe:

1. a `scale` pontosan a doboz nagyobbik oldala (nem a szélessége);
2. a 280,8 × 337,0 doboz egy **négyzetes** fotó polaroid-kerete
   (280,8/1,145 = 245,2 és 337,0/1,374 = 245,3 — a két arány az 1.9.5
   dekompilált konstansa), és a keret alsó feliratsávja miatt épp ez a
   „közel négyzetes kivágás", amit az 1.9.5 külön megjegyez;
3. a 337 egyben a Képkupac `pile_size`-ja is (0,33 · 1024).

Ebből: **`x` és `w` a lap szélességéhez, `y` és `h` a lap magasságához
arányos**, a `scale` pedig a csomópont befoglaló négyzetének oldala
képpontban. A leképezést a `picasapy.collage.draft` valósítja meg.

✅ **A korábbi eltérés a pakolónkhoz képest RENDEZVE (#1053).** Ez a
szakasz azt írta, hogy az eredeti a KERETES csempét illeszti a `pile_size`
négyzetbe, mi viszont a FOTÓT, és a keret azon kívül nő. A #1053 a 18
polaroid golden csomóponton kimérte a szabályt, és a `_pile_nodes` azóta a
KÜLSŐ dobozt illeszti a négyzetbe.

⚠️ **Önhelyesbítés (#973, 2026-09-09):** a fenti „rendezve" a POLAROID ágra
volt igaz. A **fehér szegély** ágán a fotó maradt a négyzetben, és a szegély
azon kívül nőtt — mérve `pile_size = 337`-nél 371×371 / 207×355 / 359×247,
azaz +5…10%. A `.cxf` írónk így a SAJÁT `scale` mezőjének (a befoglaló
négyzet oldala) mondott ellent. A `_pile_nodes` azóta a
`nodes.fit_outer_inside`-ot hívja, ami a keretes csempét illeszti a
négyzetbe mindhárom kerettel; `noborder`-nél a növekmény nulla, tehát ott a
viselkedés változatlan.

Fehér szegélyes Képkupac-mintánk NINCS (a mért 49 csomópont polaroid és
keret nélküli), tehát ez nem új mérés, hanem a meglévő mért szabály
következetes alkalmazása — ezt az őr (`tests/collage/test_pile_keretes_csempe_973.py`)
ki is mondja.

*Bizonyítottsági fok: erős következtetés* (egyetlen valódi mintán mért,
háromszorosan egybevágó számtan; a writer a `scale` FORRÁSÁT nem mondja ki).

### 1.6/f A `<node>` mezői TÉMÁNKÉNT — mérve 12 golden fájlon (2026-08-25, #1036)

Az 1.6/e egyetlen Képkupac-mintából vezette le a mértékegységeket, és
hallgatólagosan **minden témára** kiterjesztette. A tulajdonos tizenkét
`.cxf`-jén (89 csomópont, mind a hat téma) végigmérve kiderült, hogy a
kiterjesztés a `scale`-re **nem áll**.

#### A `scale`

| téma | a `scale` jelentése | minta | egyezés |
|---|---|---|---|
| `picturepile` | a csomópont-doboz **befoglaló négyzetének** oldala lapegységben | AI, AI1, AI2, AI8, AI9, AI10 | 49/49, `|Δ| ≤ 0,09` |
| `picturegrid` | a **kirajzolt cella SZÉLESSÉGE** (a térköz UTÁN), az 1024 képpont széles lapon | AI3 | 9/9 |
| `framegrid` | ugyanaz | AI4 | 9/9 |
| `regulargrid` | ugyanaz | AI5 | 9/9 |
| `multiexp` | **1,0** | AI7 | 4/4 (#1248) |
| `contactsheet` | **mérve 313, levezetve nincs** — a `0x00888210` layout a node `+0x2c`-be `1,0`-t ad, de **ugyanezt teszi a `regulargrid` layoutja is** (ld. 1.6/g), tehát ebből nem következik semmi | AI6 | nyitva (#1412) |

A megkülönböztető eset az **álló cella**: az `AI3` első cellája
219,5 × 288,1 lapegység, és a fájlban `scale="216"` áll — a **szélesség**,
nem a 288-as nagyobbik oldal. Ugyanaz a doboz Képkupacban 288-at adna. A
két szabály tehát nem hozható közös nevezőre.

Az `AI3` szomszédos, **azonos méretű** cellái (`216` és `214`, illetve
`289` és `287`) először képfüggésnek látszottak. Nem azok: a lap szélét
érintő él a TELJES hézagot kapja, a belső él felet-felet (1.9.3), és a két
cella ebben tér el. A számolást az 1024 képpontos lapon elvégezve mind a
kilenc érték **pontosan** kijön.

#### Az `x`, `y`, `w`, `h`

Mind a hat témán ugyanaz: a kirajzolt csempe tengelyirányú doboza a
**forgatás ELŐTT**, tengelyenként a lap saját oldalához arányosítva. A
Képkupacra képpontra ellenőrizve: az `AI10.jpg` legfelső (tehát takaratlan)
csempéjének mind a négy éle **két képponton belül** van ott, ahova a `w`/`h`
mutat — 1515 képpontos csempe, 5120 képpontos lap.

> ⚠️ **Mérési csapda, amibe már kétszer beleestünk.** A Képkupac csempéi
> fedik egymást, és a 0. index van legalul. Egy takart csempe **látható**
> része a valódinál kisebb; az így mért „~930 × 1010" indította el a #1036-ot
> azzal a téves lelettel, hogy a Képkupac dobozai rosszak. Képpontot csak a
> legfelső csempén szabad mérni.

Az, hogy MELYIK doboz kerül a fájlba, viszont témánként más:

| téma | a `<node>` doboza |
|---|---|
| `picturepile` | a kirajzolt csempe KÜLSŐ doboza (a kerettel együtt) |
| `picturegrid`, `framegrid` | a pakolási cella a térköz **ELŐTT** — a téglalapok 0,0-t és 1,0-t érintenek, és élben csatlakoznak |
| `regulargrid` | a cella a térköz **UTÁN** — az `AI5` téglalapjai között ott a hézag |
| `contactsheet` | a cellába illesztett **FOTÓ** doboza, a fehér szegély NÉLKÜL |
| `multiexp` | a teljes lap (`0 0 1 1`) |

⚠️ **Két nyitott pont** (mérésünk van rá, levezetésünk nincs):

1. **Az Indexkép `scale`-je (`313`).** Lap-szintű állandó: a két különböző
   méretű csomópont (242 × 302,6 és 155 × 276,6 lapegység) ugyanazt kapja.
   Sem a `k` cellaél (300), sem a cella magassága (359), sem a `k` 8%-os
   ráhagyásával csökkentett cella (311) nem adja ki. A 2026-08-30-i
   „vetítés/render-scale" magyarázat **MEGDŐLT** — az okot és a helyette
   érvényes bizonyítékokat az **1.6/g** szakasz írja le (#1412 nyitva).
2. **A rácsos témák térköz ELŐTTI téglalapja.** A `picturegrid` és a
   `framegrid` a pakolási téglalapot írja ki, a `regulargrid` a hézagosat;
   mi mind a hármat hézagosan írjuk. Térköz nélkül a kettő egybeesik, ezért
   a hiba csak bekapcsolt „Rács vastagsága" mellett látszik — az `AI4`
   0,3825-ös térközénél a `w` 0,350 helyett 0,337 lenne. A javítás nem a
   `.cxf`-írón múlik: a vászon-csomópont (`nodes.CollageNode`) ma nem
   hordozza a térköz előtti cellát, és kézi átrendezés után nem is
   létezik.

*Bizonyítottsági fok: mért* (12 valódi Picasa-projekt, 89 csomópont; a
Képkupac dobozai a golden JPEG képpontjain is ellenőrizve).

### 1.6/g A `scale` MEZŐ a binárisban — mérve, és egy megdőlt magyarázat (2026-09-02, #1412)

> **Bizonyítottság: megerősített** a mezőleképezésre és a negatív eredményre;
> a `313` levezetése **továbbra is NYITOTT**.

#### A `.cxf`-író mezőleképezése — pontosan

A `<node>` sorait a **`0x008347b0`** írja (egyetlen hívója a mentés-szervező
`0x00834700`, `0x00834777`). A csomópontok **56 bájtos (0x38) tömbben**
állnak; a bázis a `[ebx+0x48]`, az eltolás `index × 56`
(`0x00834c30`–`0x00834c3d`: `lea eax,[ecx*8]; sub eax,ecx; add eax,eax ×3`).

| mező | eltolás | hol olvassa | az attribútum neve |
|---|---|---|---|
| `x` | `+0x18` | — | — |
| `y` | `+0x1c` | `0x00834d26` | — |
| `w` | `+0x20` | `0x00834e09` | — |
| `h` | `+0x24` | `0x00834eec` | — |
| `theta` | `+0x28` | `0x00834fcf` | `0xcbf804` (`0x00834fb3`) |
| **`scale`** | **`+0x2c`** | **`0x008350b2`** | `0xcbf80c` (`0x00835096`) |

A mentés-szervező a hívás előtt **semmilyen csomópont-előkészítést nem
végez** (`0x00834700`, 174 bájt: sztringkezelés és a `0x008347b0` hívása) —
tehát a `+0x2c` már a szerkesztés/elrendezés végén tartalmazza a végleges
értéket.

#### ⛔ MEGDŐLT: „a layout `1,0`-t ír, tehát a 313-at a render-scale adja"

A 2026-08-30-i kör helyesen olvasta ki, hogy a **contactsheet layout
`1,0`-t** tesz a `+0x2c`-be (`0x008885ac` `fld1` → `0x008885bc`
`fstp dword [ebx+eax+0x2c]`) — ezt most diszasszemblálásból is megerősítettük.
A **következtetés** viszont nem áll, mert:

> a **`regulargrid` csomópont-elhelyezője ugyanezt teszi**: `0x0088520d`
> `fld1` → `0x0088522d` `fstp dword [eax+esi+0x2c]`
> (a `0x00885060`-at a `0x00884040` és a `0x008844d0`, azaz a
> `CRegularGridTheme` vtable 0. és 2. rekesze hívja).

A `regulargrid` fájlbeli `scale`-je **nem** `1,0`, hanem a kirajzolt cella
szélessége (AI5, 9/9 — 1.6/f). Ugyanez a `framegrid`en 280 / 319 / 127
(AI4). **Az `1,0` beírása tehát a NORMA, nem a contactsheet különössége** —
belőle a `313` eredetére semmi nem következik. A „vetítés/render-scale"
irányt ez a lap ezennel visszavonja.

#### Kimerítő negatív pásztázás — hol NINCS a `+0x2c` írója

A teljes `.text`-et végigpásztáztuk a `+0x2c`-be író utasításokra
(2026-09-02):

| alak | találat az EGÉSZ binárisban | ebből a kollázs-sávban (0x820000–0x895000) |
|---|---|---|
| `fstp dword [bázis+index+0x2c]` | 5 függvény | **2** — `0x00885060` és `0x00888210`, **mindkettő `1,0`-t ír** |
| `mov dword [bázis+index+0x2c], r32` | — | **0** |
| `movss [… +0x2c], xmm` (SSE) | **0** | 0 |
| disp32-alak (`mod=10`, eltolás `0x2c`) | **0** | 0 |
| `fstp`/`mov` **mutatós** alak (`[reg+0x2c]`) | — | 37 függvény, ebből **34** a `+0x28`-at is írja |

⛔ **MEGDŐLT (2026-09-06, #1412) — ez a tábla és a belőle vont
következtetés is hibás.** A `+0x2c` eltolású írások túlnyomó többsége
**`[esp + 0x2c]` lokális változó**, nem struktúramező; a fenti pásztázás ezt
hol beszámolta, hol nem. Helyes szűrővel (SIB-nél `base != 100b`, mutatós
alaknál `rm ∉ {100b, 101b}`) a kollázs-sávban **47** valódi `+0x2c`-író van,
és **float**-ot csak **hat** ír: `0x00822230` és `0x00823620` (egy általános
geometria-segéd, nem a csomópont), `0x008341b0` (a csomópont `operator=`),
`0x0087b830` (másolás), valamint a két elrendező — `0x00885060`
(`regulargrid`) és `0x00888210` (`contactsheet`) —, **mindkettő állandó 1,0**.
Rajtuk kívül a **beolvasó** (`0x00832830`) ír `scale`-t, közvetlenül a
csomópontba: `0x008332b7  fstp dword ptr [ebx + 0x68]` (a `theta` a
`0x00833240`-en, `+0x64`; a burkolóban a csomópont a `+0x3c`-nél kezdődik).

⇒ **A kollázs-sávban a `scale`-t senki nem SZÁMOLJA** — a két elrendező
állandót ír, a beolvasó a fájl értékét hozza vissza, a többi másol.
A részletek, a pozitív kontroll (`multiexp` = 1,0 végig) és a következő
lépés: `kollazs-eletciklus.md` **17.7–17.10**.

#### ✅ A MEZŐ AZONOSSÁGA az ÍRÓ oldaláról is megerősítve (2026-09-05)

A lap eddig a `+0x2c`-t a **layout** oldaláról azonosította a `scale`-lel
(mindkét téma `1,0`-t ír bele). Most a **`.cxf`-író** oldaláról is megvan,
tehát a mezőazonosság **két független forrásból** áll:

```
0x00835096  push 0x00cbf80c          ; az attribútum neve: "scale"
0x008350ab  mov  ecx, [ebx + 0x48]   ; a csomópont bájt-eltolása
0x008350ae  mov  edx, [esp + 0x24]   ; a csomópont-tömb bázisa
0x008350b2  fld  dword ptr [edx + ecx + 0x2c]   ; ← AZ ÉRTÉK: float a +0x2c-en
0x008350bd  fstp qword ptr [esp]
0x008350c0  push 0x00c817c0          ; a formátum: "%f"
0x008350c9  call 0x0040eab0
```

Az író `FUN_008347b0` (3023 b) — ugyanaz, amelyik az `albumTitle`,
`albumDate`, `orientation`, `shadows`, `theta` attribútumokat is kiírja.

⛳ **Kontroll a valódi fájlon:** a formátum `%f` ⇒ **hat tizedes**, és a
mintáink pontosan így néznek ki (`scale="337.000000"`, `scale="1.000000"`).
Ez zárja ki, hogy egy másik függvény írná az attribútumot.

⇒ **Az érték semmilyen átalakításon nem megy át íráskor**: a fájlban álló
`313` **pontosan** az, ami a csomópont `+0x2c` mezőjében van a mentés
pillanatában. A kérdés tehát változatlanul az, **ki írja felül** a layout
`1,0`-ját — nem az, hogy az író számol-e valamit.

⚠️ **Ez a kör NEM vezette le a 313-at.** A `+0x2c` íróinak pásztázását
újrafuttatva a 2026-09-02-i eredmény **reprodukálódott** (indexelt, SSE- és
disp32-alakú író nincs; a mutatós alakúak közül a kollázs-sávban a
`0x0087b895`–`0x0087b898` csak **másol** két csomópont közt:
`fld [edi+0x2c]` → `fstp [esi+0x2c]`). A lenti „következő lépés" tehát
érvényben marad.

#### A KÖVETKEZŐ lépés (2026-09-06-ban átírva)

⛔ Az itt korábban álló két pont a megdőlt 37-es listára épült; a
`0x0088e4e0` ráadásul **nem is a csomópontot** másolja (más 56 bájtos
osztály: float a `+0x20`/`+0x24`/`+0x30`/`+0x34`-en, dword a `+0x28`/`+0x2c`-n).

1. **A kollázs-sávon KÍVÜL** kell keresni az írót, a helyes szűrővel, a
   csomópont-alakra (egy függvényben `+0x28` ÉS `+0x2c` float-írás).
2. **Vagy mutatón át ír:** a sávban **10** `lea r, [r+0x2c]` hely van
   (`0x00823c21`, `0x008300dc`, `0x0083198a`, `0x00834af3`, `0x00860032`,
   `0x00879909`, `0x00879b7b`, `0x00879d18`, `0x0087e0cd`, `0x008831c8`,
   `0x0088ab66`) — az eltolás-alapú pásztázás ezeket nem látja.
3. Csak ha ez sem dönt: futó Picasán adatfigyelő a csomópont `+0x2c`-jén.

#### A MÉRÉSI oldal máshol van — és ez a lap elavult hozzá képest

A `scale` **mérési** feltárása a
[`kollazs-eletciklus.md` 17. szakaszában](kollazs-eletciklus.md) áll
(2026-09-01): mind a hat téma `scale / (w × 1024)` aránya, a
⭐ **`scale` = a RAJZOLT méret, nem a befoglaló dobozé** felismerés, az
1024-es vízszintes egységrendszer, és az, hogy a **313 nem beégetett
konstans** (a `.text` bájtmintás átvizsgálása a `313` négy immediate-alakjára
**nulla** találatot ad) ⇒ **számított** érték.

Ez a lap (`1.6/f`) 2026-08-30 óta a megdőlt „vetítés/render-scale"
magyarázatot hordozta — a jelen szakasz vonja vissza. **A két lap közül a
mérési kérdésekben a `kollazs-eletciklus.md` 17. az irányadó**, ez a szakasz
pedig a `.cxf`-író bináris oldaláé.

#### Mi dönti el — és kitől kell

A 17.4 szerint egyetlen olcsó lépés zárná le: egy **FEKVŐ tájolású**
Indexkép-`.cxf` a windowsos Picasából (a meglévő AI6 álló). Ha ott is `313`
áll, a szám fix; ha más, a lapmérettel skálázódik, és a két érték hányadosa
megadja a képletet. **Jegy: #1412** (`blocked` + `felhasználóra-vár`).

### 1.10 A kollázs-panel TELJES felülete — 156 elem (2026-08-16)

*Forrás: `panelroot.tre:35` (`panelroot/collagepanel`).*

A `respack.yt` `collagepanel/*` bejegyzései a **tervezővászon tényleges
koordinátáit** adják. A panel a főablak tartalomterületét tölti ki:
`panelroot/collagepanel` **(0, 29) 800 × 505**, a fül a fülsávban
`panelroot/…: collagetab` **(390, 8) 125 × 21**.

⚠️ A `#`-tel kezdődő nevek a `respack`-ben **kikommentezett** rétegek —
ezek a Picasa 3.9-ben **nem látszanak** (régi eszközsáv, ikonok, chiclet-ek).

⚠️ **Ezek a számok a TERVEZŐVÁSZON koordinátái, nem a futásidejű hely.**
A `collagepanel.tre` kényszerei szerint a bal hasáb **fix méretű**, a
vászon-oldal viszont **nyúlik**, a vászon körüli négy gombcsoport pedig
magához a **laphoz** tapad. A teljes méretezési törvény:
`kollazs-panel-ui-spec.md` **2.** szakasz — az abszolút x/y-t csak addig
használd, amíg az ablak 800 × 534.

#### 1.10.1 A panel váza

| elem | pozíció | méret |
|---|---|---|
| `docbounds` / `rect: base` | (0, 0) | 800 × 534 |
| `rect: rightcontainer` | (289, 20) | 501 × 504 |
| `decrect(tabbase): tabbase` | (3, 20) | 276 × 387 *(tervezői; futásidőben **386**: a `YConstraint 1, 0, 406` az alsó élt 406-ra köti, a felső 20 — ld. `kollazs-panel-ui-spec.md` 2.2)* |
| `buttcontainer: tabs` | (3, 25) | 276 × 25 |
| `buttcon(tab1…)` — **Beállítások** | (3, 25) | 92 × 25 |
| `buttcon(tab2…)` — **Képek** *(statikus címke; futásidőben a `collageUI::tab2_title` „Klipek (%d)"-je felülírja — ld. `picasa-kollazs-felulet.md` 8.)* | (95, 25) | 92 × 25 |
| `rect: tabpanel1` (Beállítások lap) | (13, 55) | 266 × 351 |
| `rect: tabpanel2` (Képek lap) | (13, 55) | 256 × 352 |

**A négy alsó gomb** (a bal hasáb alján, két sorban):

| gomb | felirat (HU) | pozíció | méret |
|---|---|---|---|
| `makedesktop` | Asztali háttérkép | (10, 415) | 127 × 28 |
| `sharebutton` | **Kollázs létrehozása** | (147, 415) | 133 × 28 |
| `resetbutton` | Alaphelyzet | (10, 448) | 127 × 28 |
| `cancelbutton` | Bezárás | (147, 448) | 133 × 28 |

#### 1.10.2 „Beállítások" lap (`tabpanel1`)

| elem | pozíció | méret | megjegyzés |
|---|---|---|---|
| `popuplist: theme_popup` | (13, 63) | 266 × 56 | a **hat kollázs-típus** választója |
| `text(borders_label)` — **Képszegélyek** | (16, 122) | 239 × 15 | |
| `clip: borders_group` | (13, 122) | 266 × 89 | |
| `button: border0/1/2` | (47/116/185, 143) | 62 × 62 | három szegélygomb, **69 px osztás** |
| `leftdivider` | (13, 209) | 256 × 3 | elválasztó vonal |
| `text(bkg_settings_title)` — **Háttér beállításai** | (16, 214) | 239 × 15 | |
| `buttcontainer: background_types` | (19, 233) | 127 × 55 | két rádiógomb |
| rádió — **Egyszínű** | (19, 234) | 24 × 24 | felirat (44, 237) 101 × 24 |
| rádió — **Kép használata** | (19, 261) | 24 × 24 | felirat (44, 264) 101 × 24 |
| `decrect(insetbevel): bkg_decrect` | (147, 235) | 49 × 49 | a színminta kerete |
| `current_background` | (153, 241) | 37 × 37 | a jelenlegi háttér mintája |
| `bkg_from_selection` — **A kijelölt elemek használata** | (198, 241) | 71 × 37 | |
| `colorpickerpanel(…, bkgcolorpick)` | (61, 64) | 218 × 178 | a **felugró** színválasztó |
| `rect: colorcircle` + `dropper_icon` | (153, 241) / (193, 253) | 37 × 37 / 24 × 14 | pipetta |
| `text(format_title)` — **Oldalformátum** | (16, 290) | 239 × 15 | |
| `popuplist(format_menu)` | (16, 310) | 243 × 21 | a méretarány-lista (ld. #876) |
| `button: delete_custom_aspect` | (262, 314) | 14 × 14 | **kuka**, az egyéni arány törlésére |
| `buttcontainer: orientation_container` | (101, 335) | 74 × 22 | |
| tájolás — fekvő / álló | (101 / 138, 335) | 37 × 22 | `landscape_icon` (109,340) 23×12 · `portrait_icon` (149,338) 11×16 |
| `shadow_checkbox` — **Árnyékok rajzolása** | (18, 358) | 14 × 14 | felirat (35, 357) 109 × 24 |
| `caption_checkbox` — **Képfeliratok megjelenítése** | (17, 383) | 14 × 14 | felirat (35, 382) 109 × 24 |
| `set_frame_center` — **Beállítás képkockaközéppontként** | (150, 365) | 124 × 30 | csak `framegrid`-nél |

**A „Rács vastagsága" csúszka** külön csoportban ül, és a szegély-csoporttal
**azonos helyen** — vagyis a kettő **egymást váltja** a típus szerint:

| elem | pozíció | méret |
|---|---|---|
| `clip: spacing_group` | (19, 123) | 250 × 81 |
| `text(spacing_label)` — **Rács vastagsága** | (34, 131) | 225 × 21 |
| `clip(bigslider, spacing_slider)` | (48, 153) | 191 × 27 |
| `text(None)` — **Egyik sem** | (48, 180) | 83 × 14 |
| `text(Max.)` — **Maximális** | (153, 180) | 86 × 14 |

#### 1.10.3 „Képek" lap (`tabpanel2`)

| elem | pozíció | méret | felirat (HU) |
|---|---|---|---|
| `solo` (a képtálca) | (17, 91) | 247 × 311 | |
| `getmoreclips` | (19, 60) | 166 × 28 | **Továbbiak...** |
| `back_icon` | (22, 67) | 17 × 15 | |
| `addclips` (+) | (214, 60) | 28 × 28 | *rejtett* — a felirata `#`-es |
| `deleteclips` (–) | (247, 60) | 28 × 28 | *rejtett* |

#### 1.10.4 A vászon és a rajta lévő vezérlők

| elem | pozíció | méret |
|---|---|---|
| `decrect(insetbevel): previewcontainer` | (280, 13) | 507 × 508 |
| `clip/rect/srect: preview*` | (280, 61) | 475 × 349 |
| `rect: action_group` | (318, 36) | 445 × 28 |
| `select_all` — **Az összes kijelölése** | (319, 37) | 100 × 26 |
| `select_none` — **Az összes kijelölés megszüntetése** | (422, 37) | 100 × 26 |
| `remove_node` — **Eltávolítás** | (525, 37) | 100 × 26 |
| `set_background` — **Beállítás háttérként** | (628, 37) | 134 × 26 |
| `rect: rand_group` | (346, 475) | 354 × 28 |
| `rand_placement` — **Véletlenszerű kollázs** | (347, 476) | 115 × 26 |
| `rand_order` — **Képek összekeverése** | (465, 476) | 116 × 26 |
| `view_and_edit` — **Megjelenítés és szerkesztés** | (584, 476) | 115 × 26 |

**A forgatás-igazító gombsor** a vászon fölött lebeg, függőlegesen:

| elem | pozíció | méret | jelentés |
|---|---|---|---|
| `rect: snap_rotation_group` | (383, 230) | 17 × 65 | |
| `snap_3` | (384, 247) | 15 × 15 | 90° jobbra |
| `snap_6` | (384, 263) | 15 × 15 | 180° jobbra |
| `snap_9` | (384, 279) | 15 × 15 | 270° jobbra |

*(A `snap_12` — „Forgatás igazítása egyenesre" — feliratként létezik, de a
`respack`-ben nincs saját rétege: a csoport első, 231-es y-ján ül.)*

**A folyamatjelző overlay** (kollázs készítése közben):

| elem | pozíció | méret |
|---|---|---|
| `decrect(overlaydecrect): collageprog_base` | (409, 220) | 224 × 80 |
| `text(collageprog_title)` | (414, 226) | 213 × 14 |
| `collageprog_spinner` | (509, 244) | 29 × 31 |
| `text(collageprog_status)` | (414, 280) | 213 × 14 |

Szövegei (`stringres`): „Kollázs létrehozása... inicializálás" ·
„Kollázs létrehozása - %d%%" · „Kollázs létrehozása... leállítás" ·
**„A kollázs kész (kattintson ide)"**.

#### 1.10.5 Belépési pontok a kollázsba

| honnan | elem | pozíció | méret |
|---|---|---|---|
| fülsáv | `panelroot/…: collagetab` | (390, 8) | 125 × 21 |
| fejléc-sáv | `headerpanel/…: create_collage` | (44, 53) | 29 × 27 |
| arc-fejléc | `faceheaderpanel/…: create_collage` | (115, 55) | 29 × 27 |
| szerkesztőpanel | `editpanel/…: editcollage` | (142, 9) | 128 × 22 |
| kimeneti sáv | `outputlayout/button(collage)` | (2, 2) | 55 × 36 |

#### 1.10.6 A feliratok és buboréksúgók — mind az 52, hivatalos magyarral

Forrás: `respack.yt` `tre:collagepaneltext` (angol) +
`referencia/i18n-hu/collagepaneltext.xml` (magyar).

| kulcs | angol | **hivatalos magyar** |
|---|---|---|
| `tab1` | Settings | **Beállítások** |
| `tab2` | Clips | **Képek** |
| `getmoreclips` | Get more... | **Továbbiak...** |
| `shadow_checkbox_label` | Draw Shadows | **Árnyékok rajzolása** |
| `caption_checkbox_label` | Show Captions | **Képfeliratok megjelenítése** |
| `set_frame_center-label` | Set as Frame Center | **Beállítás képkockaközéppontként** |
| `spacing_label` | Grid Spacing | **Rács vastagsága** |
| `min_spacing_label` | None | **Egyik sem** |
| `max_spacing_label` | Max. | **Maximális** |
| `bkg_settings_title` | Background Options | **Háttér beállításai** |
| `borders_label` | Picture Borders | **Képszegélyek** |
| `format_title` | Page Format | **Oldalformátum** |
| `color_bg_label` | Solid Color | **Egyszínű** |
| `bitmap_bg_label` | Use Image | **Kép használata** |
| `bkg_from_selection` | Use selected | **A kijelölt elemek használata** |
| `rand_order-label` | Shuffle Pictures | **Képek összekeverése** |
| `rand_placement-label` | Scramble Collage | **Véletlenszerű kollázs** |
| `view_and_edit-label` | View and Edit | **Megjelenítés és szerkesztés** |
| `select_all` | Select All | **Az összes kijelölése** |
| `select_none` | Select None | **Az összes kijelölés megszüntetése** |
| `remove_node` | Remove | **Eltávolítás** |
| `set_background` | Set as Background | **Beállítás háttérként** |
| `cancelbutton-label` | Close | **Bezárás** |
| `resetbutton-label` | Reset | **Alaphelyzet** |
| `makedesktop-label` | Desktop Background | **Asztali háttérkép** |
| `sharebutton-label` | Create Collage | **Kollázs létrehozása** |

**Buboréksúgók:**

| kulcs | **hivatalos magyar** |
|---|---|
| `addclips` | Kijelölt klipek felvétele a kollázsba |
| `deleteclips` | A kijelölt képek eltávolítása a tálcáról |
| `getmoreclips` | További képek beolvasása a könyvtárból |
| `caption_checkbox` | Képfeliratok szövegként való megjelenítése „Polaroid fényképezőgép" szegélyű képeken |
| `portrait` | Álló: A kollázs függőleges tájolása |
| `landscape` | Fekvő: a kollázs vízszintes tájolása |
| `format_menu` | Kijelölheti a kollázs viszonylagos szélességét és magasságát |
| `delete_custom_aspect` | A jelenlegi méretarány törlése |
| `cancelbutton` | A Kollázs lap bezárása |
| `makedesktop` | JPG formátumban mentheti a képet a Kollázsok albumba, majd beállíthatja az asztalra háttérképként |
| `resetbutton` | Az összes módosítás visszavonása |
| `sharebutton` | Mentés JPG formátumban a Kollázsok albumba (a Projektek gyűjteménybe). |
| `rand_order` | A képek sorrendjének véletlenszerűsítése |
| `rand_placement` | A kollázs elrendezésének összekeverése |
| `select_all` | Az összes kép kijelölése (Ctrl+A) |
| `select_none` | Az összes kép kijelölésének megszüntetése (Ctrl+D) |
| `remove_node` | Kijelölt elemek eltávolítása a kollázsból (Del) |
| `set_background` | A kijelölt kép használata háttérként |
| `move_top` | Kép elhelyezése a kupac tetején |
| `move_up` | Kép feljebb helyezése a kupacban |
| `move_down` | Kép lejjebb helyezése a kupacban |
| `move_bottom` | Kép elhelyezése a kupac alján |
| `snap_12` | Forgatás igazítása egyenesre |
| `snap_3` | Forgatás igazítása 90 fokra (jobbra) |
| `snap_6` | Forgatás igazítása 180 fokra (jobbra) |
| `snap_9` | Forgatás igazítása 270 fokra (jobbra) |

⚠️ **A „Scramble Collage" hivatalos magyarja „Véletlenszerű kollázs"** a
panelen, de a **helyi menüben** ugyanez a parancs „Képek szétszórása"
(`CollageD::ID_COLLAGE_RANDOMIZE_PLACEMENT`). A két felirat **szándékosan
eltér** — mindkettőt úgy kell átvenni, ahogy van.

#### 1.10.7 Vászon-visszajelzés vonszolás közben

`collage::angle_format` = **„Szög: %d"** · `collage::scale_format` =
**„Méretarány: %d%%"** (`stringres`). Ezek a kép húzása/forgatása közben
jelennek meg.

### 1.7 Figyelmeztetések (átvehető viselkedés)

- **„Format Mismatch Warning"** — ha az asztali háttérképnek mentesz, de a
  kollázs oldalaránya nem egyezik a képernyőével: *„…This may result in a
  desktop background that does not look as expected. (TIP: Choose »Current
  display« in the Page Format dropdown menu…)"* — gombok: `Set Anyway` /
  `Don't Set`.
- **„Selection Required"** — a Frame Mosaic középső képéhez: *„Please select
  the single image you want to place in the center of the collage BEFORE
  pressing this button."*
- **„Save Skipped"** — ha minden képet eltávolítottál: *„The collage cannot
  be saved because all of the pictures have been removed."*

### 1.8 Menük

`CollageS` (kép a vásznon): Legfelülre / Legalulra helyezés · Beállítás
háttérként · Beállítás képkockaközéppontként · Eltávolítás · Megjelenítés és
szerkesztés. `CollageD` (vászon): Képek összekeverése · Képek szétszórása ·
Az összes kijelölése / kijelölés megszüntetése. `Border`: Egyik sem · Fehér
szegély · Polaroid fényképezőgép. (Ld. `ui-audit-menus.md` K.9.)

### 1.9 Az elrendezés-algoritmusok — DEKOMPILÁLVA (2026-08-13)

**Futás:** Ghidra 12.1.2, `Picasa3.exe` (SHA-256-kötött index), 35 gyökér
(a téma-osztályok vtable-slotjai), 2 szint, **237 dekompilált függvény**.
Nyers kimenet: `referencia/dekompilalt-kollazs/` (privát repó).

Eddig ez a szakasz csak a felületet írta le; a hat elrendezés **matematikája**
most került elő. A megbízhatósági szintek jelölve.

#### 1.9.1 Közös építőelemek

**Illeszkedés a kereten belülre** (`0x009b4aa0`) — mindenütt ez adja a
képméretet:

```c
s  = min((dstW + 0.499f) / srcW, (dstH + 0.499f) / srcH);
w  = round(s * srcW + 1e-5f);
h  = round(s * srcH + 1e-5f);
```

A `+0.499` és a `+1e-5` nem elírás: a Picasa így kerekít **felfelé** a
határesetben, ezért egy képpontnyi eltérés adódhat a naiv `round(s*w)`-hez
képest.

**Véletlenszám** — az MSVC `_rand()` (a `holdrand * 0x343fd + 0x269ec3` LCG,
0…32767). Egyenletes lebegőpontos értékre a bináris a klasszikus bittrükköt
használja, a dekompilátor ezt írja ki `((rand + 0x3f8000) * 0x100) - 1.0`
alakban; ez valójában:

```c
u = bitcast_float(0x3f800000 | (rand() << 8)) - 1.0f;   // u ∈ [0,1)
```

**A szórás vezérlése:** a „Képek összekeverése" (`rand_order`) egy külön
lépés — az elemekhez `rand()` kulcsot rendel, majd kulcs szerint rendez
(`CPileTheme` 3. slot, `0x0087d410`); a „Véletlenszerű kollázs"
(`rand_placement`) az elrendezést futtatja újra más maggal.

#### 1.9.2 Képkupac (`picturepile`) — a magja megvan

**Méret.** A képek nem egyformák: a **sorrendben hátrébb lévő kisebb**.
Az `i`-edik kép (1-alapú) alapmérete a lap szélességének 33%-a, egy
lecsengő szorzóval (`0x0087bcb0`):

```c
float pile_scale(int i) {              // i = 1, 2, 3, …
    if (i <= 1) return 1.0f;
    float s = 1.0f / sqrtf(sqrtf((float)i) - 1.0f);
    return s > 1.0f ? 1.0f : s;        // felül 1.0-ra vágva
}
meret_i = round(pile_scale(i) * 0.33f * lapSzelesseg);
```

| `i` | 1–4 | 5 | 10 | 20 | 50 | 100 |
|---|---|---|---|---|---|---|
| szorzó | 1,00 | 0,90 | 0,68 | 0,54 | 0,41 | 0,33 |

> ✅ **A képletet a felhasználó valódi `.cxf`-mintája igazolja** (1.6). Az ott
> szereplő `scale` értékek — 337 / 303 / 280 / 263 / 249 / 238 képpont —
> a 337-hez viszonyítva 1,0000 / 0,8991 / 0,8309 / 0,7804 / 0,7389 / 0,7062,
> a képlet pedig `i = 1…4` / 5 / 6 / 7 / 8 / 9-re 1,0000 / 0,8995 / 0,8306 /
> 0,7795 / 0,7395 / 0,7071. A legnagyobb eltérés **0,31 képpont** — kerekítési
> nagyságrend, öt egymást követő indexen. Ezzel a belső `sqrt` is megerősített:
> más függvény nem adná vissza ezt a sorozatot. (A hívott CRT-függvénynek —
> `0x00c0b310`, 20 bájt — továbbra sincs neve a binárisban.)
>
> A mintában `337 = 0,33 · lapszélesség`, tehát a lap ≈ 1021 képpont széles volt.

**Forgatás.** Képenként egy véletlen szög, amit a kép **vízszintes helyzete
modulál** (`0x0087dcd0`):

```c
u  = uniform01();                          // ld. 1.9.1
x  = kep_kozeppont_x / teruletSzelesseg;   // 0…1
fok = -36.0f * u * (0.1f - (x - 0.5f) * 0.5f);   // = u * (18*x - 12.6)
theta = fok * 0.017453292f;                       // RADIÁNBAN tárolva
```

Vagyis a szög **balra nagyobb** (a bal szélen 0…−12,6°, kb. 70%-nál nulla,
a jobb szélen 0…+5,4°) — nem szimmetrikus szórás, hanem enyhe legyezőhatás.
A `.cxf` `theta` mezője radiánban van; a felület a `collage::angle_format`
(„Szög: %d") felirathoz `theta * 57.29578` (= 180/π) átváltással jut.

**Pozíció.** A számított hely a kép **közepére** hivatkozik, és a lap
koordinátáira normalizálódik:

```c
X = (lap.jobb - lap.bal) * (x - kepSzelesseg * skala * 0.5f) / teruletSzelesseg;
Y = (lap.also - lap.felso) * (y - kepMagassag * skala * 0.5f) / teruletMagassag;
```

Animált átrendezéskor ugyanez az `AnimPlacementHandler` objektumba kerül
(pozíció, szög, méret; a `0x3f4ccccd` = **0,8 s** animációhossz).

#### 1.9.3 Mozaik (`picturegrid`) és Képkockamozaik (`framegrid`) — a térköz szabálya

A `CGridTheme` **normalizált téglalapokban** dolgozik: minden képnek egy
`(x0, y0, x1, y1)` négyese van a `[0,1]²` egységnégyzetben; a pakolás ezeket
állítja elő, a rajzolás pedig ebből számol képpontot. A „Rács vastagsága"
csúszka (`spacing`, 0…1) így hat (`0x00880e30`):

```c
m   = min{ minden téglalap szélessége és magassága };
hez = spacing * 0.45f * m;      // teljes hézag, normalizált egységben
fel = hez * 0.5f;
a   = lapSzelesseg / lapMagassag;

x0px = round((r.x0 + (r.x0 == 0.0f ? hez : fel)) * W);
x1px = round((r.x1 - (r.x1 == 1.0f ? hez : fel)) * W);
y0px = round((r.y0 + a * (r.y0 == 0.0f ? hez : fel)) * H);
y1px = round((r.y1 - a * (r.y1 == 1.0f ? hez : fel)) * H);
```

Két nem nyilvánvaló következmény, amit át kell venni:

1. **A lap szélét érintő él a TELJES hézagot kapja, a belső élek felet-felet.**
   Így két szomszédos kép között is pontosan egy hézagnyi rés lesz, és a
   külső margó ugyanakkora, mint a belső rés — ettől néz ki egyenletesnek.
2. **A függőleges hézagot a lap oldalaránya szorozza** (`a = W/H`), tehát a
   rés **képpontban négyzetes**, nem a normalizált térben.

> ✅ **MEGMÉRVE valódi Picasa-kimeneten (2026-08-19).** A tulajdonos két
> eredeti Mozaik-kollázsán (a privát repó
> `referencia/kollazs-golden/2014-naptar.zip`-jében), ellentétes
> tájolásban — ez a mérés **megkülönbözteti** a képletet az `a` szorzó
> nélküli változattól:
>
> | fájl | lap | vízszintes rés | a képlet jóslata függőlegesen | `a` NÉLKÜL lenne | **mért** |
> |---|---|---|---|---|---|
> | fekvő | 5120 × 4546 (`a` = 1,126) | 27 px | **27,00 px** | 23,97 px | **27 px** |
> | álló | 3752 × 5120 (`a` = 0,733) | 8 px | **8,00 px** | 10,92 px | **8 px** |
>
> A két esetben az `a` szorzó **ellentétes irányba** téríti el az
> eredményt (fekvőnél nagyobbra, állónál kisebbre), és a mérés mindkétszer
> a képletet igazolja. Az 1. következmény is mérve: a fekvő lapon a bal
> margó, a belső rés és a jobb margó **egyaránt 27 px**.
>
> *(A mérés mellékesen azt is megmutatja, hogy ezen a két kollázson az
> árnyék KI volt kapcsolva és a keret `noborder` volt: a rések teljes
> szélességükben tiszta fehérek — árnyékkal a résekben színátmenet
> volna. Az árnyék-paraméterek (9/b) tehát **továbbra sincsenek mérve**.)*

A `framegrid` ugyanezt a rajzolót örökli, csak a pakolót írja felül
(`0x00888e60`) — a kijelölt kép kerül a hangsúlyos középső cellába.

> ~~A pakoló algoritmus maga (mely kép melyik cellát kapja, hogyan darabolódik
> a négyzet) **még nincs megfejtve**~~ → a Mozaiké megvan (1.9.7–1.9.10), a
> Képkockamozaik **helyre-kényszerítő** pakolója pedig az **1.9.14**-ben.

#### 1.9.4 Rács (`regulargrid`), Indexkép (`contactsheet`), Többszörös exponálás (`multiexp`)

- **`regulargrid`** — szabályos sorok/oszlopok (**a sor/oszlop-szám képlete az
  1.9.8-ban**); a 3. slot
  (`0x00885750` → `0x008857a0`) **nem** elrendezés, hanem a sorrend
  megfordítása/keverése (két indextömb rendezése, majd páronkénti csere).
- **`contactsheet`** — a fejléc két sorból áll. A
  `collage/contactsheet/title` és `.../subtitle` a két **szövegcsomópont
  neve**, nem a kiírandó szöveg: a felső sor a projekt `albumTitle` mezője,
  az alsó a képszám és az `albumDate`, a
  `CContactSheetTheme::subtitle_format` mintájával. A valódi `AI6.cxf` /
  `AI6.jpg` közvetlen bizonyítéka: `albumTitle="AI"`,
  `albumDate="2023. november"`, 9 csomópont → **„AI"** és
  **„9 kép, 2023. november"**. A címsor
  betűmérete `round(f * 0.04 * lapMagassag)`, ahol `f = 1,0`, ha a panel
  méretaránya nagyobb 1-nél, különben **0,75**. A fejléc jobbról-balra író
  nyelveken tükröződik (a kód a `DAT_00d678d4` jelzőre előjelet vált).
  A képrács bal/felső kezdete **6% / 15%**, hasznos területe **88% × 79%**;
  a cella befoglalójának mind a négy éle `round(0,08·k)` értékkel beljebb
  lép (`k` a 9/b.3-ban levezetett cellaél). Ez az `AI6.cxf` első helyét és
  osztását ezredes pontossággal visszaadja. A pontos betűcsalád továbbra
  sincs azonosítva; a tartalom, méret, hely és adaptív szín igen.
- **`multiexp`** — minden kép a **teljes lapra** kerül, oldalarányhoz
  igazítva (`0x00841860`), és egymásra keveredik (`0x00409ea0` `1.0f, 1.0f`
  súlyokkal). Nincs pozíciószámítás.

#### 1.9.5 A három képkeret — teljesen megvan

**Polaroid** (`0x00889790` / `0x00889820`). A keret a fotóhoz képest:

```
kulsoSzelesseg = round(fotoSzelesseg * 1.145)
kulsoMagassag  = round(fotoMagassag  * 1.374)
margo          = round(fotoSzelesseg * 0.0725)      // (1.145 - 1) / 2
papirszin      = 0xFFD9D9D9                          // RGB(217, 217, 217)
```

A fotó a keretben `margo` távolságra van balról, jobbról és **felülről** —
a maradék alul jelenik meg vastag sávként, ahová a képfelirat kerül. Ezek a
számok a valódi Polaroid-arányok (3,5×4,25 hüvelykes lap, 3,1×3,1 hüvelykes
képmező → 1,129 és 1,371) másfél ezreléken belüli közelítései.

**Fehér szegély** (`0x00889a20`):

```
b   = round(min(szelesseg, magassag) * 0.05)   // a RÖVIDEBB oldal 5%-a
szin = 0xFFEEEEEE                               // RGB(238, 238, 238) — nem tiszta fehér
```

**Nincs szegély** (`0x00889bc0`) — csak a kép, semmilyen díszítés.

**Dimmed** (`0x00889da0`) — a háttérként használt képre alkalmazott
sötétítés: fényerő **−0,15**, kontraszt **1,0** (`0xbe19999a` és `0x3f800000`
lebegőpontos bitminták), hogy a rátett képek olvashatók maradjanak.

**Keret nélküli illeszkedés** (`0x00889ce0`): a hosszabbik oldal kapja a
megadott célméretet, a rövidebbet arányosan számolja.

#### 1.9.6 A vtable-slotok jelentése (mind a hat témára ellenőrizve)

A kör egyik mellékeredménye, hogy a téma-osztályok slotkiosztása kiderült —
ez korábban félrevezetett minket, mert a „3. slot" nem elrendezés:

| slot | mit csinál |
|---|---|
| 0 | **elrendezés/rajzolás** — a dokumentum téglalapjaiból képpontot számol |
| 1–2 | méret- és oldalarány-lekérdezés |
| **3** | **a sorrend/elhelyezés összekeverése** (`rand_order` / `rand_placement`) — minden témában `_rand()` kulcsokkal rendez, **nem** elrendezés |
| 6–8 | a téma neve, ikonja, leírása (erőforráskulcsok) |
| **11** | **a pakolás** — a `CGridTheme`-nél (`0x00882100`) ez hívja a pakolófát (1.9.7) |

Az osztályok és a vtable-jeik (RTTI-ből): `CPileTheme` `0x00cbf5ac`,
`CGridTheme` `0x00cbf5dc`, `CRegularGridTheme` `0x00cbf610`,
`CMultiExposureTheme` `0x00cbf640`, `CContactSheetTheme` `0x00cbf670`,
`CFrameGridTheme` `0x00cbf6a0`; keretek: `PolaroidBitmapTheme` `0x00cbf91c`,
`WhiteBorderTheme` `0x00cbf928`, `NoBorderTheme` `0x00cbf934`,
`DimmedBitmapTheme` `0x00cbf940`.

#### 1.9.7 A Mozaik pakolója — MEGFEJTVE (2026-08-14)

**Futás:** három további Ghidra-kör (170 + 132 + 89 = **391 dekompilált
függvény**), nyers kimenet: `referencia/dekompilalt-pakolo/` (privát repó).

Az 1.9.6-ban leírt keresés helyes volt: a pakolás nem a téma-osztályokban van.
A `CGridTheme::Layout` (`0x00880e30`) a **11. vtable-slotot** hívja
(`0x00882100`), az pedig egy külön, ~15 kB-os könyvtárat a `0x0088c1a0` és
`0x0088ff70` között. Ez a könyvtár RTTI-vel azonosított osztályokból áll:

```
CPackingTree            ← alaposztály        vtable 0x00cc51ac
 ├─ CFullSearchTree                          vtable 0x00cc51fc
 ├─ CGravityTree                             vtable 0x00cc522c
 └─ CLocationTree                            vtable 0x00cc525c
CBinaryTree<CImageLocation*> / CPackingTreeNode / CGravityTreeNode / CLocationTreeNode
```

Vagyis a Mozaik egy **bináris pakolófa** (guillotine-felosztás): a lapot
rekurzívan két részre vágja, a levelek a képek cellái.

##### Melyik stratégia fut

A `0x0088e2b0` választ (a `filterdesc`-hez hasonló, de kódba égetve):

| feltétel | osztály |
|---|---|
| **14-nél kevesebb kép** és nincs kényszerített mód | `CFullSearchTree` |
| mód = 1 | `CGravityTree` |
| mód = 2 | `CLocationTree` |

Utána minden példány ugyanazt a két paramétert kapja:

```c
tree.limit     = 3000;      // +0x28 — a keresési ág képszám-küszöbe
tree.timeLimit = 0.5f;      // +0x30 — MÁSODPERCBEN
```

Ha a Képkockamozaik középső képe ki van jelölve, annak téglalapja
kényszerként kerül a fába (`+0x18…+0x24`), különben mind a négy mező `-1`.

##### A keresés — időkorlátos, véletlen sorrendekkel

A `CPackingTree::Pack` (`0x0088e9d0`) magja:

```c
best     = FaEpites(lapArany, kepek_eredeti_sorrendben);
bestKtsg = Koltseg(best);
t0 = QueryPerformanceCounter();
while ((QueryPerformanceCounter() - t0) / frekvencia < 0.5f) {   // 0,5 másodperc
    sorrend = VeletlenKeveres(kepek);        // rand() % n, Fisher–Yates (0x0088fcf0)
    jelolt  = FaEpites(lapArany, sorrend);
    if (Koltseg(jelolt) < bestKtsg) { best = jelolt; bestKtsg = Koltseg(jelolt); }
}
return best;
```

> ⚠️ **Ebből következik, hogy a Mozaik nem determinisztikus.** Ugyanaz a
> képhalmaz ugyanazokkal a beállításokkal **kétszer futtatva más elrendezést
> adhat** — a keresés valós időhöz kötött (`QueryPerformanceCounter`), és
> `_rand()`-ot használ. Ezért menti a Picasa a végeredményt képenként a
> `.cxf`-be, és ezért mutat százalékos előrehaladást
> („Kollázs létrehozása – %d%%"). A mi megvalósításunknak **nem szabad** ezt
> reprodukálhatónak ígérnie, viszont a `.cxf`-ből visszatöltésnek pontosnak
> kell lennie.

A `CFullSearchTree` ágán (kevés kép) egy második, finomító kör is fut
(`0x0088ed40`): 100 véletlen **csere-jelöltet** értékel ki (két csomópont
képének felcserélése), rendezi őket költség szerint, és a legjobbat tartja
meg, ha jobb a kiindulónál.

##### A költségfüggvény — a kihasználatlan terület

`CPackingTreeNode` 9. slot (`0x00893570`), rekurzívan a fán:

```c
double Koltseg(csomopont, kenyszerTeglalap) {
    if (csomopont.bal == NULL && csomopont.jobb == NULL) {      // LEVÉL = egy kép
        w = cella.x1 - cella.x0;
        h = cella.y1 - cella.y0;
        if (kenyszerTeglalap ervenyes) {          // a FrameGrid középső területe
            w *= (kenyszer.x1 - kenyszer.x0);
            h *= (kenyszer.y1 - kenyszer.y0);
        }
        a = kep.szelesseg / kep.magassag;         // a kép oldalaránya (0x0088e650)
        if (w / a <= h) { illW = w;      illH = w / a; }   // szélességre illeszt
        else            { illW = a * h;  illH = h;     }   // magasságra illeszt
        veszteseg = |w*h - illW*illH|;            // A CELLÁBAN ÜRESEN MARADÓ TERÜLET
        return veszteseg < 1e-5 ? 0.0 : veszteseg;
    }
    return Koltseg(bal, kenyszer) + Koltseg(jobb, kenyszer);
}
```

**Olvasat:** a pakoló azt minimalizálja, hogy összesen mennyi terület vész el,
amikor minden képet a saját oldalarányával a neki jutott cellába illesztünk.
Ez pontosan az, amit a súgó ígér: *„Mozaik: a képek automatikus illesztése az
oldalra."* A képek tehát **nem torzulnak** — a cella marad üres, és ezt az
ürességet bünteti a költség.

##### Megbízhatóság

Az osztálynevek **RTTI-ből** származnak, nem következtetés. A költségfüggvény,
az időkorlát (0,5 s), a küszöb (3000) és a 14-es határ közvetlenül a
dekompilált kódból van. Ami **következtetés**: a `CGravityTree` és a
`CLocationTree` pontos szerepe (mikor kapcsol rájuk a program) — a módválasztó
mező írója még nincs megtalálva; az alapértelmezés a `CFullSearchTree`.

#### 1.9.8 A Rács sor- és oszlopszáma — MEGFEJTVE (2026-08-14)

A `regulargrid` nem a pakolófát használja: saját, zárt képlettel választ
sor/oszlop-osztást (`0x00885b00`, a `CRegularGridTheme::Layout` alatt).

```c
// N = a képek száma, lapSzel/lapMag a rendelkezésre álló terület
atlagArany = 0;
for (kep : kepek) atlagArany += kep.szelesseg / kep.magassag;
atlagArany /= N;                                  // ÁTLAGOS oldalarány

legjobbSor = -1;  legjobbKtsg = +FLT_MAX;
for (sor = 1; sor <= N && sor < 1000; sor++) {
    oszlop = ceil(N / sor);                        // felfelé kerekítő egész osztás
    if (oszlop == 0) break;
    cellaArany = (lapSzel / oszlop) / (lapMag / sor);
    q = cellaArany / atlagArany;
    if (q < 1.0f) q = 1.0f / q;                    // szimmetrikus eltérés, mindig >= 1
    ktsg = q * 1.7f + (float)(sor * oszlop - N);   // + az ÜRESEN MARADÓ CELLÁK száma
    if (ktsg <= legjobbKtsg) { legjobbSor = sor; legjobbKtsg = ktsg; }
}
sorok   = legjobbSor;
oszlopok = ceil(N / legjobbSor);
```

**Olvasat:** két dolgot mérlegel egymás ellen — mennyire tér el a cella
oldalaránya a képek átlagos oldalarányától (`q`, `1.7`-es súllyal), és hány
cella marad üresen (`sor·oszlop − N`, súly 1). Vagyis **egy üresen maradó cella
körülbelül annyit „ér", mint 0,59-nyi relatív oldalarány-eltérés.**

Két apróság, ami különben eltérést okoz:

- Az összehasonlítás `<=`, tehát **döntetlennél a NAGYOBB sorszám nyer**.
- A ciklus 1000 sornál megáll (a fordító háromszorosan kibontotta, de a
  logika ez).

#### 1.9.9 A pakolófa építése — MEGFEJTVE (2026-08-14)

A negyedik kör (`referencia/dekompilalt-pakolo/script-DecompilePacker4.log`)
lezárta az utolsó darabot is. A `CPackingTreeNode` 13. slotja (`0x00891fc0`),
amit a keresés minden sorrendre meghív, **négy különböző faépítőt futtat le, és
a legkisebb költségűt tartja meg**:

```c
legjobbKtsg = 1000000.0f;
for (epito : { 0x00894470, 0x00894940, 0x00893da0, 0x00894bd0 }) {
    fa = epito(lapArany, kepek, kenyszer);
    if (Koltseg(fa) < legjobbKtsg) { legjobb = fa; legjobbKtsg = Koltseg(fa); }
}
```

Vagyis a Mozaik **két szinten keres**: kívül 0,5 másodpercig véletlen
sorrendeket próbál (1.9.7), belül minden sorrendre négyféle felosztást.

##### A négy faépítő

Mind a négy ugyanabból a képlistából épít fát; a különbség az **összevonás
sorrendje**. A kiválasztás mindig a költség (1.9.7) alapján történik.

| # | cím | stratégia |
|---|---|---|
| 1 | `0x00894470` | **cikcakk páros összevonás**: minden szinten a szomszédos elemeket párosítja — az egyik szinten elölről, a következőn hátulról, váltakozva. Páratlan elemszámnál az utolsó változatlanul lép a következő szintre. |
| 2 | `0x00894940` | **költségvezérelt páros összevonás**: szintenként párosít, de négynél több elemnél mind a **16 vágásirány-kombinációt** kipróbálja (2⁴), költséget számol mindegyikre, és a legolcsóbbat választja (`0x00894d50`). |
| 3 | `0x00893da0` | **kettőhatványra igazítás**: addig von össze párokat, amíg a szint elemszáma pontosan `2^k` nem lesz, onnantól tökéletesen kiegyensúlyozott bináris fa. |
| 4 | `0x00894bd0` | **rekurzív guillotine** (lent részletesen) — a legtisztább, önmagában is működő megvalósítás. |

##### A rekurzív guillotine-építő (`0x00894bd0`)

```c
Csomopont* Epit(celArany, lista, lo, hi) {
    if (lo >= hi) return NULL;
    n = hi - lo;
    if (n == 1) return Level(lista[lo]);            // egy kép

    kozep = lo + n/2;
    if ((kozep & 1) != 0 && n > 2) kozep++;          // PÁROS határra igazít

    a1 = AtlagArany(lista, lo,    kozep);            // a bal/felső fél átlagos oldalaránya
    a2 = AtlagArany(lista, kozep, hi);               // a jobb/alsó félé

    irany = VagasIrany(celArany, a1 + a2, a1*a2/(a1+a2));
    t     = Kiigazitas(celArany, a1, a2, irany);

    csomopont.bal   = Epit(a1 + t, lista, lo,    kozep);
    csomopont.jobb  = Epit(a2 + t, lista, kozep, hi);
    return csomopont;
}
```

##### A vágásirány (`0x00893b10` + `0x00893c20`)

Két jelöltet hasonlít össze — ez a két érték a geometria alapazonossága:

| ha a két blokkot… | a keletkező blokk oldalaránya |
|---|---|
| **egymás mellé** tesszük (azonos magasság) | `a1 + a2` |
| **egymás alá** tesszük (azonos szélesség) | `a1·a2 / (a1 + a2)` |

**Az alapszabály: azt az irányt választja, amelyik oldalaránya közelebb esik a
cella kívánt arányához** (`|jelolt − celArany|` minimuma).

Ezt egészíti ki négy peremeset-ág: ha az egyik jelölt „átbillenne" az 1,0-s
határon — vagyis álló cellából fekvő blokkot vagy fordítva csinálna —, akkor
a **tájolást megőrző** jelölt nyer, akkor is, ha numerikusan távolabb van.

> ⚠️ A négy peremeset-ág olvasata részben **következtetés**: a dekompilátor
> ezen a helyen FPU-jelzőbit-manipulációként adja vissza a `bool` értéket
> (`(ushort)(x<y)<<8 | …`), ami nehezen olvasható. Az általános ág (a
> minimális eltérés) és a két jelölt képlete viszont egyértelmű.

##### A kiigazítás (`0x00893b80`) — másodfokú egyenlet

A gyerekek nem a nyers `a1`, `a2` célaránnyal épülnek tovább, hanem `a1 + t`,
`a2 + t` értékkel, ahol `t` az a korrekció, amivel a két gyerek **együtt
pontosan a kívánt `A` arányt adná ki**:

```c
// VÍZSZINTES vágás:  (a1+t) + (a2+t) = A
t = ((A - a1) - a2) * 0.5f;

// FÜGGŐLEGES vágás:  (a1+t)(a2+t) / ((a1+t)+(a2+t)) = A
b = (a1 + a2) - 2*A;
t = ( sqrtf(b*b - 4*(a1*a2 - A*a2 - A*a1)) - b ) * 0.5f;
```

A második eset a szokásos másodfokú megoldóképlet a fenti egyenletre.

> ✅ **Ez egyben a `0x00c0b310 = sqrt` azonosítás második, független
> megerősítése**: egy másodfokú megoldóképlet diszkriminánsán csak
> négyzetgyök állhat. (Az első a Képkupac-képlet illesztése a valódi
> `.cxf`-mintára, ld. 1.9.2.)

#### 1.9.10 Melyik pakolóstratégia mikor fut — LEZÁRVA (2026-08-14)

Az 1.9.7 még nyitva hagyta, mikor lép be a `CGravityTree` és a
`CLocationTree`. A módmező (`+0x24`) íróit végigkövetve a válasz egyértelmű:

| mód | osztály | mikor | ki állítja be |
|---:|---|---|---|
| 0 | **`CFullSearchTree`** | Mozaik, **14-nél kevesebb** kép | alapállapot (`0x0088d860` minden pakolás előtt nullázza) |
| 0 | **`CPackingTree`** (alaposztály) | Mozaik, **14 vagy több** kép | ugyanaz az ág, más konstruktor (`0x0088d7b0`) |
| 2 | **`CLocationTree`** | **Képkockamozaik** (`framegrid`) | `CFrameGridTheme` 11. slot (`0x00888ec0` → `0x0088db10`) |
| 1 | `CGravityTree` | **soha** | a beállítója (`0x0088d990`) **halott kód** — a binárisban egyetlen hivatkozás sem mutat rá |

**Két átvehető következtetés:**

1. A **`CLocationTree` a Képkockamozaik pakolója** — a neve is beszédes: ez az,
   ami a kijelölt képet a megadott *helyre* (a hangsúlyos középső cellába)
   kényszeríti, és a többit köré rendezi. Ezért kerül a kényszer-téglalap a fa
   `+0x18…+0x24` mezőibe (1.9.7).
2. A **`CGravityTree` sosem fut** a Picasa 3.9-ben. Egy megvalósításnak nem
   kell foglalkoznia vele; nyilván egy korábbi vagy tervezett elrendezés maradt
   a kódban.

#### 1.9.11 A kollázs megőrzött beállításai (`Preferences`)

A kollázs-munkamenet indításakor (`0x0087dcd0`) a program a `Preferences`
szekcióból tölti vissza az előző beállításokat:

| kulcs | mit őriz |
|---|---|
| `collage::theme` | az utolsó kollázs-típus (alapértelmezés `picturepile`) |
| `collage::format` | az oldalformátum (alapértelmezés 4:3) |
| `collage::orientation` | álló / fekvő |
| `collage::bgcolor` | a háttérszín |
| `collage::avgcolor` | a háttér „a képek átlagszíne" kapcsolója |
| `collage::shadows` | árnyékok rajzolása |
| `collage::showcaptions` | képfeliratok megjelenítése |

> A `collage::avgcolor` **megválaszolja az 1.6/b nyitott kérdését**: a
> `<background>` harmadik módja az **átlagszín**, és a képenkénti átlagszínt a
> program az adatbázisból veszi (`avgcolor` mező, ld. `0x00880580` — minden
> kollázs-csomópont eltárolja a saját képének átlagszínét).

#### 1.9.12 A Képkupac kezdeti szórása — MEGFEJTVE (2026-08-14)

Ez volt az utolsó hiányzó darab. A szórás a `0x0087cb70`-ben van (a `CPileTheme`
0. slotja alatt), és **nem egyszerű egyenletes véletlen**: a Picasa
**„legjobb jelölt" mintavételezést** (Mitchell best-candidate) használ.

```c
N = a kollázsban lévő képek száma;
s = pile_scale(N);                    // ugyanaz, mint a méretnél: min(1, 1/sqrt(sqrt(N)-1))
sav    = 1.0f - s * 0.495f;           // a hasznos tartomány szélessége (0…1-ben)
eltol  = (1.0f - sav) * 0.5f;         // középre igazítás — a szélektől tartott margó

for (kep : kepek) {
    legjobbTav = 0.0f;
    for (probal = 0; probal < 5; probal++) {          // ÖT jelölt képenként
        x = (sav * uniform01() + eltol) * teruletSzelesseg;
        y = (eltol + uniform01() * sav) * teruletMagassag;

        d2 = +1e6f;
        for (p : mar_elhelyezett_pontok)              // a LEGKÖZELEBBI szomszéd
            d2 = min(d2, (x-p.x)*(x-p.x) + (y-p.y)*(y-p.y));

        if (d2 > legjobbTav) { legjobbTav = d2; legjobbX = x; legjobbY = y; }
    }
    elhelyez(legjobbX, legjobbY);       // a legmesszebb eső jelölt nyer
    mar_elhelyezett_pontok.push(legjobbX, legjobbY);
}
```

**Miért fontos ez?** Tiszta egyenletes véletlennel a kupac csomós lenne — egyes
képek egymásra torlódnának, máshol lyukak maradnának. Az öt jelöltből a
legtávolabbi kiválasztása **kvázi-egyenletes, „kék zajos" eloszlást** ad: a
képek lazán, de szabályosság nélkül töltik ki a lapot. Ez a Képkupac
jellegzetes megjelenésének a kulcsa, és egy naiv `rand()`-alapú megvalósítás
**szemmel láthatóan másképp néz ki**.

A margó a képszámmal együtt szűkül: sok képnél `s` kicsi, így a `sav` közel 1,0
— vagyis a szórás majdnem a teljes lapra kiterjed. Kevés képnél (`s = 1`) a sáv
`0,505`, a középpontok tehát a lap középső felében maradnak.

A pozíció innen megy tovább az 1.9.2 képleteibe (középre igazítás és a lap
koordinátáira normalizálás), a forgatás pedig a vízszintes helyzetből számolódik.

**Ezzel a Képkollázs mind a hat elrendezése, mindhárom kerete, a `.cxf`
formátum és a megőrzött beállítások teljesen feltárva.**

#### 1.9.14 A Képkockamozaik helyre-kényszerítő pakolója (`CLocationTree`) — 2026-08-16

A 1.9.10 megállapította, hogy a `framegrid` pakolója a **`CLocationTree`**,
de az algoritmusa nem volt leírva. Most megvan a váza.

##### Mi a „kényszer" adatszerkezete

Minden képhez (a pakoló bemeneti tömbjében) tartozik:

| eltolás | tartalom |
|---|---|
| `+0x38 … +0x44` | négy `float`: a kép **rögzített téglalapja** (`x0, y0, x1, y1`) |
| **`+0x48`** | **1 bájt: „van már helye"** |

Ha `+0x48 == 0`, a kép szabadon pakolható, és a kód egy
`(−1, −1, −1, −1)` helyőrzővel dolgozik (`0x00890774`, `0x00890a4f`,
`0x00890a9b`, … tíz helyen). Ha `+0x48 != 0`, a `+0x38`-as téglalap
**kényszer**: a keresésnek olyan elrendezést kell adnia, amiben a kép oda
kerül.

A `CLocationTreeNode` gyártója (`0x008910b0`, a fa 8. vtable-slotja) egy
**0x38 bájtos** csomópontot foglal, `0xcc5364` vtable-lel, és a
`+0x20 … +0x2c` négy `float`-ot **−1,0-ra** állítja (`0xcf3ed0`) — ez a
csomópont saját kényszer-téglalapja, alapban „nincs kényszer". A `+0x34`
szintén −1,0.

> ⚠️ **Helyesbítés az 1.9.7-hez:** ott a kényszer-téglalap `+0x18 … +0x24`
> néven szerepel. A `CLocationTreeNode`-ban **`+0x20 … +0x2c`** — a
> `0x008910b0` inicializálása egyértelmű.

##### A keresés: időkorlátos, véletlen újrapróbálkozásokkal

A pakoló belépési pontja a fa **7. vtable-slotja**: `0x008906e0` (2412 b).
A ciklusa (`0x00890bf0`–`0x00890cf5`):

```asm
0x00890bf8  call [0xc40298]        ; QueryPerformanceCounter → most
0x00890c0e  fld  qword [0xd678e8]  ; 1/frekvencia, gyorsítótárazva
0x00890c29  call [0xc404a0]        ;   ha még nincs: QueryPerformanceFrequency
0x00890c4b  fsub qword [esp+0x90]  ; most − kezdet
0x00890c52  fmulp                  ; × (1/frekvencia)  → eltelt másodperc
0x00890c54  fld  dword [ecx+0x30]  ; a fa IDŐKORLÁTJA
0x00890c57  fcompp / jne 0x890f41  ;   ha túlléptük → kilép
0x00890c88  call 0x8912b0          ; a legjobb csomópont KLÓNOZÁSA
   …a +0x18 … +0x34 mezők átmásolása (a kényszer-téglalappal együtt)…
0x00890ce1  call 0x88fcf0          ; fa-építés, 2-es móddal
0x00890ce6  add  dword [esp+0x44], 1   ; próbálkozás-számláló
```

Ugyanaz a séma, mint a Mozaik teljes keresésénél (1.9.7): **véletlen
sorrendekkel újrapróbálkozó, órára kötött keresés**, nem determinisztikus
algoritmus. Az időkorlát a fa `+0x30` mezője.

##### A zárás: mindenki „elhelyezett" lesz

A ciklus után (`0x00890f50`–`0x00890f88`) a nyertes elrendezés téglalapjai
**visszaíródnak** minden képbe, és a jelző bebillen:

```asm
0x00890f6a  mov  [eax+0x38], esi   ; x0
0x00890f71  mov  [eax+0x3c], edi   ; y0
0x00890f7e  mov  [eax+0x40], ebx   ; x1
0x00890f81  mov  [eax+0x44], esi   ; y1
0x00890f84  mov  byte ptr [eax+0x48], 1   ; ← "van már helye"
```

Ez magyarázza a **Beállítás képkockaközéppontként** gomb viselkedését: a
kijelölt kép megkapja a hangsúlyos középső cellát `+0x48 = 1`-gyel, és
onnantól minden újrapakolás megőrzi.

##### Ha nem sikerül: visszaesés az alap pakolóra

A függvény végén `0x00891032  call 0x88e9d0` — ez a **`CPackingTree` 7.
slotja**, vagyis a szokásos (kényszer nélküli) pakoló. A `CLocationTree`
tehát **nem helyettesíti**, hanem **kiegészíti** az alap algoritmust.

##### Melyik metódusokat írja felül

| slot | `CPackingTree(Node)` | **`CLocationTree(Node)`** |
|---:|---|---|
| fa 7 | `0x0088e9d0` | **`0x008906e0`** — a fenti keresés |
| fa 8 | `0x0088ed00` | **`0x008910b0`** — csomópont-gyártó, −1-es kényszerrel |
| csomópont 1 | `0x0088e720` | `0x0088e7e0` |
| csomópont 5 | `0x00892f20` | `0x0089a5d0` (679 b) |
| csomópont 6 | `0x00893010` | `0x0088e830` (20 b) — a `+0x20`-as téglalapot adja tovább a `0x89a880`-nak |
| csomópont 10 | `0x008936c0` | `0x0089b160` (551 b) |
| csomópont 12 | `0x00891f70` | **`0x00897af0` (8479 b)** |
| csomópont 16 | `0x008938b0` | `0x0089a3d0` (504 b) |
| csomópont 17 | — | `0x00899c40` (538 b) — ÚJ slot |

##### A kényszeres vágó MAGJA (2026-08-17)

A `0x00897af0` (8479 b) **levél-csomópontnál** ezt teszi:

```c
if (csomopont->bal == NULL && csomopont->jobb == NULL) {   // 0x00897b1c, 0x00897b25
    kep = csomopont->kep;                                  // [esi+8]
    if (kep != NULL) {
        r = kep->vanHelye ? kep->teglalap                  // [kep+0x48] ? [kep+0x38..0x44]
                          : alapertelmezes(0x88e6c0);
        if (r.x0 != -1 && r.x1 != -1 && r.y1 != -1 && r.y0 != -1) {
            elfogad(r);            // 0x891fc0(..., 0x100)
            csomopont->frissit();  // vtbl +0x1c
            csomopont->kesz = 1;   // [esi+0x31] = 1
            return;                // ← NEM darabol tovább
        }
    }
    if (darabszam == 1) { … }      // 0x00897bf4
}
```

**Egy mondatban:** ha a képnek már van **érvényes** (nem −1-es)
téglalapja, a fa **változatlanul átveszi**, és abban az ágban **nem
darabol tovább**. A `−1`-et **mind a négy koordinátára** külön ellenőrzi
(`0x00897b6b` `fld [0xcf3ed0]` = −1,0, majd `0x00897b71`, `0x00897b7a`,
`0x00897b84`, `0x00897b8e`) — a „nincs kényszer" állapotot tehát a
**teljes téglalap** jelöli, nem egy jelzőbit.

**A teljes 8479 bájt mindössze HÁROM lebegőpontos konstanst olvas:**
`−1,0` (`0xcf3ed0`) · `2,0` (`0xc7d9d0`) · `0,5` (`0xc72150`). Nincs
benne illesztett szám — a vágás **tisztán geometriai** (felezés és
középpont).

##### A rekurzív darabolás MEGERŐSÍTVE (2026-08-30, olcsó diszasszemblálás)

A `0x00897af0` két konstansát eddig a vágás jeleként említettük; a
teljes törzs végighaladva a **nem-levél (belső) ág** is tételes:

| ág | cím | tartalom |
|---|---|---|
| levél | `0x00897b1c` | kényszeres kép → `elfogad` (`0x891fc0`), `vtbl+0x1c` frissítés, `[+0x31]=1` — a spec fenti levél-ág |
| egyszeres | `0x00897bf4` (`edx==1`) | a kép beszúrása a gyerekbe a csomópont saját category-slotján át (`vtbl+0x44`), majd frissítés |
| **rekurzív** | `0x00897c2b` | `call 0x89e140` (8524 b: a **cella-vágás és gyerek-beszúrás** — `[edi+0xc]/[edi+0x10]` levél-vizsgálat, `0x89b790` a vágás); a darabszám **felezése** (`0x00897c5c shr ebx,1`); `0x00897c62 jne` — a maradéktól függően egy- vagy kétvágás; a bal/jobb gyerekekbe `push 2` („2. mód", `0x00897ce6`) |

A három konstans szerepe a törzsben:

| konstans | ahol dönt | szerep |
|---|---|---|
| `−1,0` (`0xcf3ed0`) | `0x00897b6b`–`0x00897b8e` | a kényszer-téglalap „nincs" állapota |
| `0,5` (`0xc72150`) | `0x008983ae` (`fdiv` szél/mag, majd `fcomp`) | **a kép keskenyebb, mint a cella fele** → keskeny-illesztés ága |
| `2,0` (`0xc7d9d0`) | `0x00898849` (ugyanaz a képlet) | **a kép szélesebb, mint a cella kétszerese** → széles-illesztés ága |

Azaz a beillesztés arány-vizsgálata a < 0,5 és > 2,0 tartományokkal
választ ágat — ugyanaz a logika, amit a célfüggvény (`0x00893570`) az
illesztésnél használ.

*Bizonyítottsági fok: **megerősített** a levél-ágra és a rekurzív ágra,
a konstans-szerepekre és az egyszeres esetre — a törzs szó szerinti
átfésülésével.*

##### A hangsúlyos kép TÉGLALAPJA — MEGVAN (2026-09-11, helyi diszasszemblálás)

Eddig a keresés adatszerkezete volt leírva, a **kényszer-téglalap forrása**
nem. Két tévhitet is oszlat a mérés:

1. **A gomb nem téglalapot állít.** A „Beállítás képkockaközéppontként"
   (`0x0083d520`) mindössze ennyit tesz: `[téma+0x50] = 1`,
   `[téma+0x54] = a kijelölt kép azonosítója` (`0x0083d599`–`0x0083d59d`),
   majd `vtbl+8`-cal újrapakolást kér. Sem koordináta, sem méret.
2. **A téglalapot a téma pakolója számolja** (`CFrameGridTheme` 11. slot,
   `0x00889185`–`0x00889241`), a kép betöltött oldalarányából:

```asm
0x00829d8c  fstp dword [eax+0x58]  ; a GYÁRTÓ: 0,5  (0xc7dafc)  ← a méret
0x00889192  fstp [esp+0x18]        ; s·A        (A = a lap SZÉLESSÉGE)
0x008891a4  fstp [esp+0x10]        ; s·A/a      (a = a KÉP oldalaránya)
0x008891b1  jne 0x8891d7           ; ha a < 1 (ÁLLÓ kép), csere:
0x008891ba  fstp [esp+0x10]        ;   s·B      (B = a lap MAGASSÁGA)
0x008891c2  fstp [esp+0x18]        ;   a·s·B
0x008891e6  fld  qword [0xc72150]  ; 0,5 — a fél oldalak
0x00889216  mov  [eax], edx        ; x0 = 0,5 − félszélesség
```

A mozgó kapu megnevezése is megvan: a `[téma+0x54]` a **−1** kezdőértéket a
gyártóban kapja (`0x00829d99`), és a pakoló a listát úgy rendezi, hogy a
hangsúlyos kép az **első** elem legyen (`0x00888f60` körül) — innen jön a
`**(float**)(téma+0x1c)` mint „az első kép aránya".

**A képlet, `P = A/B` lapoldalaránnyal és `s = 0,5`-tel:**

| a kép | a cella a lap közepén |
|---|---|
| fekvő (`a ≥ 1`) | szélesség `s`, magasság `s·P/a` |
| álló (`a < 1`) | magasság `s`, szélesség `s·a/P` |

Mindkét ág ugyanazt mondja: a cella **képpontban a kép oldalarányát tartja**
(a hangsúlyos kép nem torzul), és a **nagyobb oldala a lap fele**.

⚠️ **Ez döntötte el a #916-ot.** A korábbi megvalósításunk a hangsúlyos
képet a `(0,25 … 0,75)` téglalapba tette — ami a képlet **határesete**,
pontosan akkor helyes, ha a kép oldalaránya éppen a lapé (`P/a = 1`). Egy
16:9-es kép 4:3-as lapon ennél **kétszer alacsonyabb** cellát kap.

*Bizonyítottsági fok: **mért** — a gyártó konstansa (`0xc7dafc` = 0,5), a
gomb törzse és a képlet utasításonként kiolvasva.*

*Ami továbbra sincs meg:* a maradék terület felosztása
(`0x0089e140`, 8524 b) — a megvalósításunk ott saját, kimondott szerkezetet
használ (négy sáv a cella körül), a MÉRT célfüggvénnyel választva.

##### ~~Ami NYITVA marad~~ → MEGVÁLASZOLVA (2026-08-18)

> A kérdés az volt: **melyik részfába irányítja a vágó a
> kényszer-téglalapot**, ha a fa több szinten mélyül.
>
> **A válasz: sehova — nincs irányítás.** A kényszer nem a fán vándorol
> lefelé, hanem **képenként, kívülről** kerül a saját csomópontjába.

A három gyanúsított tisztázva:

| függvény | mi valójában |
|---|---|
| `0x0088e4e0` (113 b, 8×) | **struktúra-másolás**: a kép 0x50 bájtos leírója, a kényszer-téglalappal (`+0x38…+0x44`) és a „van helye" jelzővel (`+0x48`) együtt — a bemeneti lista részlistákra osztásához |
| `0x008a9a20` / `0x008a9c00` (466–466 b) | **összefésülő rendezés**, két külön hasonlítóval (`0x008a9f20` az elsőé); a hatványkettes ciklus és az ideiglenes puffer egyértelmű |
| `0x00891c70` (133 b) | a permutált index szerinti elem kikeresése a másoláshoz |

Vagyis a fa felépítése a **rendezett/permutált lista kettévágása** —
ugyanaz, mint a kényszer nélküli pakolónál. A kényszernek ebben nincs
szerepe.

##### A kényszer átadása: a keresés stempeli be, körönként

A keresőciklusban (`0x008906e0`), amikor egy jelölt **jobb pontszámot**
ad az eddigi legjobbnál (`0x00890d6d` `fcomp` + `jne`), a kód végigmegy a
képeken (`0x00890d8f`–`0x00890dc4`), és mindegyik **saját
csomópontjának** `+0x20…+0x2c` mezőjébe beírja:

```
ha (kep[0x48] != 0)  forras = kep + 0x38      ; a kényszer-téglalap
egyébként            forras = (−1, −1, −1, −1) ; 0xcf3ed0
csomopont[0x20 … 0x2c] = forras négy float-ja
```

A levélszabály (fentebb, `0x00897af0`) pedig ezt olvassa vissza: érvényes
(nem −1-es) téglalapnál **változatlanul átveszi és nem darabol tovább**.

**Ezért nincs szükség irányításra.** Hogy a kényszeres kép a *megfelelő*
helyre kerüljön, azt nem egy okos elosztás dönti el, hanem az **időkorlátos,
véletlen újrapróbálkozásos keresés**: a Picasa addig sorsol új
sorrendeket, amíg a pontszám javul, és ha az időkorláton belül nem sikerül,
**visszaesik a kényszer nélküli pakolóra** (`0x00891032` → `0x0088e9d0`).
Elutasításos mintavétel, nem konstrukció.

##### A pakoló CÉLFÜGGVÉNYE — `0x00893570` (2026-08-18)

A keresés `node->vt[0x24]`-et hívja pontszámért (`0x00890d67`). Ez a
`0x00893570` (328 b), és **mindkét fa ugyanazt használja** — a
`CPackingTreeNode` 9. slotja is `0x00893570`, tehát ez a **Mozaik, a
Képkockamozaik és a Rács közös célfüggvénye**.

Rekurzív: belső csomópontnál a két gyerek pontszámának összege
(`0x00893673`-tól). **Levélnél:**

```
w = cella.x1 − cella.x0                  ; [csp[8]+0x20] − [csp[8]+0x18]
h = cella.y1 − cella.y0

ha (p != NULL és p NEM mind −1) {         ; a kényszer-téglalap
    w *= (p.x1 − p.x0)                    ; egész szélesség
    h *= (p.y1 − p.y0)
}

cella_terulet = w · h                     ; [esp+0x20]
arany         = 0x0088e650(kep)           ; a KÉP oldalaránya (szél/mag,
                                          ;   két 64 bites mezőből)
…a képet a cellába illeszti az arány megtartásával…
pontszam = | cella_terulet − beillesztett_terulet |     ; fsubr + fabs
ha (pontszam < 1e−5f) pontszam = 0        ; 0xcf3a10
```

**Egy mondatban: a pontszám az ELPAZAROLT TERÜLET** — mennyi marad üresen
(vagy lóg ki), ha a képet a saját oldalarányával illesztjük a neki jutott
cellába. A keresés ezt **minimalizálja**, 1e−5-ös holtsávval.

> **Ez a legfontosabb szám az egész pakolóból.** Eddig a mi
> megvalósításunk saját heurisztikát használ; ha valaha „miért máshova
> tette a Picasa ezt a képet" kérdés merül fel, a válasz ebben a
> célfüggvényben van.

*Bizonyítottsági fok: **megerősített** a kényszer-átadásra, a rendezésre,
a másolásra és arra, hogy a célfüggvény közös. A levélszintű pontszám
**„elpazarolt terület"** olvasata **erős**: a `fsubr` + `fabs` páros és a
`0x0088e650` aránya egyértelmű, de a köztes szorzás-sorrendet nem
vezettük le lépésről lépésre.*

*Bizonyítottsági fok: **megerősített** az adatszerkezetre (`+0x38…+0x48`), a
keresés időkorlátos szerkezetére, a visszaírásra és a vtable-eltérésekre ·
**megerősített** a `0x00897af0` vágási szabályára (a levél-, az egyszeres és
a rekurzív ágra) a 2026-08-30-i törzs-átfésüléssel (ld. a fenti új
szakaszt).*


#### 1.9.13 Ami még nyitott

- ~~A **Képkupac kezdeti (x, y) szórása**~~ — **MEGVAN, az 1.9.12-ben**
  („legjobb jelölt" mintavételezés, képenként öt próbálkozással). Ez a
  jelölés elavult volt; a 2026-08-17-i átvilágítás vette le.
- A **Képkockamozaik kényszeres vágási szabálya** — `0x00897af0` (8479 b),
  ld. 1.9.14. A körülötte lévő adatszerkezet és keresés már megvan.

## 2. Film készítése (`ID_MAKEMOVIE`, `eMenuCreateMovie`)

### 2.1 Átmenetek — a teljes lista, belső kulccsal

| kulcs | név |
|---|---|
| `cut` | (vágás, átmenet nélkül) |
| `dissolve` | Dissolve |
| `dissolveblack` | Dissolve through black |
| `dissolvewhite` | Dissolve through white |
| `wipeleft` / `wiperight` / `wipeup` / `wipedown` | Wipe – left / right / top / bottom |
| `diagwipeul` / `diagwipeur` / `diagwipedl` / `diagwipedr` | Wipe – up left / up right / down left / down right |
| `pushleft` / `pushright` / `pushtop` / `pushdown` | Push – left / right / top / bottom |
| `circlein` / `circleout` | Circle – inwards / Circle |
| `kenburns` | **Pan and Zoom** (Ken Burns-effekt) |
| `kenburnsaoi` | **Pan and Zoom – face** (arcra fókuszáló Ken Burns) |
| `timelapse` | Time Lapse |
| **`rect`** | **Rectangle** — „Négyszög" *(2026-09-03-i kiegészítés)* |

A `kenburnsaoi` külön említést érdemel: a Picasa az **arcfelismerés
eredményét** használta a Ken Burns-mozgás célpontjául.

> ⛔ **SZÁMHELYESBÍTÉS (2026-09-03).** A fenti tábla eddig **21** átmenetet
> sorolt, a #432 címe pedig **18**-at mondott. **A tényleges szám 22**, és a
> kimaradt tétel a **`rect`**.
>
> **Bizonyíték — két, egymástól független forrás:**
>
> | forrás | eredmény |
> |---|---|
> | `referencia/stringres-en-hu.tsv` | `CTransitions::*` kulcsok száma: **22** |
> | az átmenet-nyilvántartó `0x00771a10` (934 b) | **mind a 22** kulcsra hivatkozik, a `rect`-re is (`CTransitions::rect`) |
>
> ⇒ a `rect` **élő** átmenet, nem maradék sztring. A hivatalos magyar neve
> **„Négyszög"**.

#### A 22 átmenet HIVATALOS MAGYAR neve (2026-09-03)

A fenti tábla az **angol** neveket adta meg. A `referencia/stringres-en-hu.tsv`
`CTransitions::*` sorai a **hivatalos magyar** fordítást is tartalmazzák —
ezek nélkül a legördülő magyar felületen angolul jelenne meg:

| erőforrás-kulcs | angol | **hivatalos magyar** |
|---|---|---|
| `CTransitions::cut` | Cut | **Kivágás** |
| `CTransitions::dissolve` | Dissolve | **Szétoszlás** |
| `CTransitions::dissolveblack` | Dissolve through black | **Szétoszlás feketén át** |
| `CTransitions::dissolvewhite` | Dissolve through white | **Szétoszlás fehéren át** |
| `CTransitions::wipeleft` | Wipe - left | **Törlés - balra** |
| `CTransitions::wiperight` | Wipe | **Törlés** |
| `CTransitions::wipeup` | Wipe - top | **Törlés - felfelé** |
| `CTransitions::wipedown` | Wipe - bottom | **Törlés - lefelé** |
| `CTransitions::diagwipeul` | Wipe - up left | **Törlés - balra fel** |
| `CTransitions::diagwipeur` | Wipe - up right | **Törlés - jobbra fel** |
| `CTransitions::diagwipedl` | Wipe - down left | **Törlés - balra le** |
| `CTransitions::diagwipedr` | Wipe - down right | **Törlés - jobbra le** |
| `CTransitions::pushleft` | Push - left | **Tolás - balra** |
| `CTransitions::pushright` | Push | **Tolás** |
| `CTransitions::pushtop` | Push - top | **Tolás - felfelé** |
| `CTransitions::pushdown` | Push - bottom | **Tolás - lefelé** |
| `CTransitions::circlein` | Circle - inwards | **Kör - befelé** |
| `CTransitions::circleout` | Circle | **Kör** |
| `CTransitions::kenburns` | Pan and Zoom | **Pásztázás és nagyítás** |
| `CTransitions::kenburnsaoi` | Pan and Zoom - face | **Pásztázás és nagyítás - arc** |
| `CTransitions::timelapse` | Time Lapse | **Gyorsítás** |
| `CTransitions::rect` | Rectangle | **Négyszög** |

⚠️ **Négy fordítás megtévesztő, ha valaki az angolból indul:**

1. **`wiperight` = „Törlés"**, nem „Törlés - jobbra" — az angol is csak
   „Wipe" (az alapirány kap rövid nevet). Ugyanígy **`pushright` = „Tolás"**
   és **`circleout` = „Kör"**.
2. **`timelapse` = „Gyorsítás"**, nem „Időzített felvétel".
3. **`cut` = „Kivágás"** — a magyar szó a szerkesztő „kivágás" műveletére is
   használt; itt **vágás** értelemben áll (átmenet nélküli váltás).
4. A **`kenburnsaoi`** magyarul is jelzi az arcot: „**- arc**".

#### ⚠️ NE keverd össze: a `CThemePrefs::` MÁSIK, TÍZ elemű készlet

A binárisban van egy második, hasonló nevű család. **Nem** a filmkészítőé:

| kulcs | angol | magyar |
|---|---|---|
| `CThemePrefs::checkerboard` | Checkerboard | Sakktábla |
| `CThemePrefs::circle` | Circle | Kör |
| `CThemePrefs::collage` | Collage | Kollázs |
| `CThemePrefs::crossfade` | Cross Fade | Egymásra helyezés |
| `CThemePrefs::diagonal` | Diagonal | Átlós |
| `CThemePrefs::gadgets` | Google Gadgets | Google Modulok |
| `CThemePrefs::panzoom` | Pan and Zoom | Pásztázás és nagyítás |
| `CThemePrefs::push` | Push | Tolás |
| `CThemePrefs::rect` | Rectangle | Négyszög |
| `CThemePrefs::wipe` | Wipe | Törlés |

Négy név **azonos** a két készletben (`Kör`, `Pásztázás és nagyítás`,
`Négyszög`, `Tolás`), de a `CThemePrefs` **tíz** elemű, és van benne olyan,
ami a filmkészítőben nincs (`Sakktábla`, `Kollázs`, `Google Modulok`).
⇒ **Ha egy kör tíz átmenetet talál, rossz családot néz.**

#### A választó vezérlő és a szomszédjai — hivatalos magyar feliratokkal

| elem (teljes név) | **hivatalos magyar** | forrás |
|---|---|---|
| `makemoviepanel/transtype_label` | **„Képváltási stílus"** | `panel-feliratok-hu.tsv:590` |
| `makemoviepanel/transtype` · `transtype_listbox` | *(a legördülő maga)* | `0x00613b50`, `0x0061b560`; a lista `0x006223b0` |
| `makemoviepanel/transitionslider_label` | **„Átfedés"** | `panel-feliratok-hu.tsv:572` |
| `makemoviepanel/tab1` | **„Mozgófilm"** | `:577` |
| `makemoviepanel/tab2` | **„Dia"** | `:591` |
| `makemoviepanel/tab3` | **„Klipek"** | `:592` *(az angol „Options"-szel szemben)* |

#### `makemoviepanel/rewind` — „Vissza a kijelölt diához"

**Felirat:** `panel-feliratok-hu.tsv:565` — **„Vissza a kijelölt diához"**.

**Amit MÉRTÜNK:** a panel frissítő blokkja (`0x0061681e`) **megjeleníti és
teljesen átlátszatlanná teszi** az elemet:

```
0x0061681e  mov edx, "makemoviepanel/rewind"
0x00616823  call 0x9c2fc0            ; elem keresése NÉV szerint
0x00616844  mov byte [eax+0x210], 1  ; látható/engedélyezett := 1
0x00616851  mov dword [eax+0x248], 0xff  ; átlátszatlanság := 255
```

Ugyanez a blokk kezeli a `makemoviepanel/export_youtube` és a
`makemoviepanel/tabpanel2` elemet is.

**Amit NEM tudunk: mit csinál KATTINTÁSRA.** Az olcsó lánc kimerült:

- a `makemoviepanel/rewind` sztring a binárisban **egyszer** fordul elő, és
  az a fenti megjelenítő hely;
- a parancsdiszpécserben (`publish/%s_go`-mintájú összerakott név) **nincs**;
- a `.tre` csak a szülőt adja meg, viselkedés-tulajdonság nincs rajta.

⇒ **NINCS MÉRVE.** **Megszerzés:** a panel egérkezelőjének célzott
dekompilációja, VAGY egy windowsos Picasa-próba (a felirat egyértelmű, de a
mérce a mérés).

> ⛔ **ELVETETT hipotézis — a `rewind` NEM feltételes funkció.** A
> megjelenítő blokkot egy globális őrzi (`cmp dword [0xd67914], 0`), és
> kézenfekvő volt szolgáltatás-kapcsolónak hinni. **Nem az:** a globálisnak
> **egyetlen** írója van (`0x009c3a36`, a felületi keret indítójában —
> `0x009c3860`, ami a `Preferences\UIFolder`-t és a `runtime\` mappát
> olvassa), és **1712** olvasója, mind `cmp …, 0` alakú. ⇒ Ez a
> **felületi fa gyökérmutatója**, a hivatkozások null-ellenőrzések.
> A `rewind` tehát mindig látszik, ha a felület betöltődött.

> *Bizonyítottsági fok: **megerősített** a feliratokra és a megjelenítő
> blokkra; **NINCS MÉRVE** a kattintás hatására.*

### 2.2 Beállítások

- **Slide Duration** csúszka — kiírás: `Slide Duration: %s Sec`.
- **Total Photos** csúszka — `Total Photos: %s`.
- **Overlap** (átmenet-hossz) csúszka.
- **Idő-szűrő:** „Don't filter by time taken" … `Remove Photos Taken Within %s`
  — sorozatfelvételek ritkítása.
- **Dimensions** (kimeneti méret), **Show Captions**, **Show Dates**,
  **Full frame photo crop**, **Remove Low Resolution Faces**.
- **Diasorrend:** `Best Transitions` (okos) · `Album Order` · `Chronological`.
- **Hangsáv:** `Load…` / `Clear` + `Options`.

### 2.3 Szöveges dia — 12 stílus (a teljes lista, 2026-09-03)

> ⛔ **SZÁMHELYESBÍTÉS.** A szakasz eddig **11 stílust** mondott, és kilencet
> nevezett meg „(+ további kettő)" megjegyzéssel. **A tényleges szám 12**
> (`textstyle0` … `textstyle11`), és **három** volt megnevezetlen, nem kettő.

| # | kulcs | angol | **hivatalos magyar** |
|---|---|---|---|
| 0 | `textstyle0` | Centered | **Középre igazított** |
| 1 | `textstyle1` | I'm Feeling Lucky | **Jó napom van** |
| 2 | `textstyle2` | Caption | **Képfelirat** |
| 3 | `textstyle3` | Caption - Classic | **Képfelirat – Klasszikus** |
| 4 | `textstyle4` | Gradient - Black | **Színátmenet – fekete** |
| 5 | `textstyle5` | Gradient - White | **Színátmenet – Fehér** |
| 6 | `textstyle6` | Transparent - Black | **Átlátszó – fekete** |
| 7 | `textstyle7` | Transparent - White | **Átlátszó – fehér** |
| 8 | `textstyle8` | Scrolling Credits | **Gördülő stáblista** |
| 9 | `textstyle9` | Music Video - Left | **Zenei videoklip – bal** |
| 10 | `textstyle10` | Music Video - Right | **Zenei videoklip – jobb** |
| 11 | `textstyle11` | Caption - Typewriter | **Képfelirat – Írógép** |

*(Forrás: `referencia/stringres-en-hu.tsv`, `CMakeMoviePanel::textstyle*` —
12 kulcs, hézag nélkül 0-tól 11-ig.)*

Betűbeállítás: család, méret, `Bold`, `Italic`, és **„Automatic Outline
(like movie subtitles)"**.

### 2.3/b A SZÖVEGES DIA fülének MŰKÖDÉSE — a 11 stílus mellé a többi vezérlő (2026-09-02)

*A 2.3 a tizenegy stílus NEVÉT adta. Ez a szakasz a `makemoviepanel`
2. fülének (a szöveges diáé) **összes** vezérlőjét megnevezi, és
megmondja, **melyik `.mxf`-mezőt** írja. A parancsok ugyanabban a közös
kezelőben ülnek (`0x0061df10`), mint a hangsáv (2.6/b) és a kimenet
(2.6/c). Image base `0x00400000`.*

#### A) A dia beszúrása — „Szöveges dia beszúrása" (`insert_slide`)

| lépés | mit tesz | cím |
|---|---|---|
| 0. | **kapu:** ha a `[panel+0x4f2]` bájt nem nulla, a gomb más ágra megy | `0x0061ec18` |
| 1. | új dia-rekord, **`<type>` = 2** (ez a szöveges dia típuskódja) | `0x0061ec34`, `0x0061ec5d` |
| 2. | a szövege a honosított `CMakeMoviePanel::sampletext` = `Text` / **„Szöveg"** | `0x0061ec39` |
| 3. | **hova kerül:** ha van kijelölt dia (`[panel+0x388]` ≠ −1) és a `0x00610b90` igazat ad → `[panel+0x388] + 1`, azaz **a kijelölt dia UTÁN**; különben a **lista elejére** (index 0) | `0x0061ec56`–`0x0061ec8f` |
| 4. | beszúrás | `0x0061c4c0` |
| 5. | **átvált a 2. fülre** (`makemoviepanel/tab2` névparancs) | `0x0061eca5` |
| 6. | a fül tartalmát az új diához igazítja (`0x00621240`), majd négy frissítő hívás | `0x0061ecb2`–`0x0061ecdb` |
| 7. | `SendMessageA(hwnd, 7, hwnd, 0)` — a **7 = WM_SETFOCUS** (az import `0x00c40884`) | `0x0061eceb` |
| 8. | végül a **`makemoviepanel/inputtext`** mezőre teszi a fókuszt | `0x0061ed28` |

⇒ **Egy kattintás után a felhasználó azonnal gépelhet:** a panel átvált a
szövegdia-fülre, a beviteli mező kap fókuszt, és a placeholder „Szöveg".

A törlés (`remove_slide`) egyetlen hívás: `0x006214e0(panel, 0, 0)`
(`0x0061edc5`).

#### B) A három betűstílus-kapcsoló — mind ugyanaz a séma

Mindhárom (`bold`, `italic`, `outline`) pontosan három lépés:

1. **beolvassa** az aktuális dia szövegparamétereit — `0x00611320(projekt+0x48, &rekord, [panel+0x388], 1)`
2. **lekérdezi** a kapcsoló állását — `0x009cd9a0(<elemnév>)`
3. **visszaírja** a rekordot — `0x0061c7f0` (közös farok, `0x0061fca4`)

| kapcsoló | `.mxf` mező | rekord-eltolás | érték | cím |
|---|---|---|---|---|
| `makemoviepanel/bold` | **`<weight>`** | +0x44 (dword) | **400** (normál) / **700** (félkövér) | `0x0061fb5b`–`0x0061fb6a` |
| `makemoviepanel/italic` | **`<italic>`** | +0x40 (bájt) | 0 / 1 | `0x0061fc03` |
| `makemoviepanel/outline` | **`<outline>`** | +0x41 (bájt) | 0 / 1 | `0x0061fc9c` |

⭐ **A 400/700 a GDI `LOGFONT.lfWeight` szokásos két értéke** — a bináris
`neg al; sbb eax,eax; and eax,0x12c; add eax,0x190` idiómával számolja
(0x12c = 300, 0x190 = 400). A `.mxf` `<weight>` mezője tehát **nem
logikai**, hanem súlyszám.

#### C) A három legördülő — mit ír, és hova

| legördülő | `.mxf` mező | rekord-eltolás | mit ír | cím |
|---|---|---|---|---|
| `makemoviepanel/fontfamily_listbox` | **`<fontname>`** | +0x28 | a `[panel+0x2a8]` tömb `index`-edik betűtípusneve | `0x006226d8`–`0x0062270a` |
| `makemoviepanel/sizelist_listbox` | **`<size>`** | +0x2C | a **`0x00c7e4f0`** statikus tábla `index`-edik eleme | `0x006227eb`–`0x006227f8` |
| `makemoviepanel/templatelist_listbox` | **`<styleid>`** | +0x3C | **magát az indexet** (a 2.3 tizenegy stílusa) | `0x006228cd`–`0x006228ea` |

Mindhárom a `−1`-es (nincs kiválasztás) indexnél **kilép** anélkül, hogy
bármit írna (`0x006226ae`, `0x006227c1`, `0x006228a3`).

**A betűméret-lista TELJES tartalma** (`0x00c7e4f0`, `−1`-gyel lezárva —
tizenhat érték):

```
8 · 10 · 12 · 14 · 16 · 18 · 20 · 22 · 26 · 30 · 36 · 48 · 60 · 72 · 84 · 96
```

**A betűtípus-választás preferenciába is bekerül:** a
`Preferences\`**`makemovie::textfont`** kulcsba (`0x00622731`–`0x00622743`).
⇒ A következő szöveges dia ezzel a betűtípussal indul, nem a
gyárival.

#### D) A két színválasztó

A `0x00621d40` (242 b) **előtag szerint** dönt:

| a névelőtag | melyik vezérlő adja a színt | a szín helye |
|---|---|---|
| **`text_`** | `makemoviepanel/txcolorcircle` | a vezérlő `[+0x268]` mezője |
| **`bkg_`** | `makemoviepanel/bgcolorcircle` | ugyanott |

A két panel neve `makemoviepanel/text_picker_panel` és
`makemoviepanel/bkg_picker_panel`; a keretük a respackben
`makemoviepanel/txcolorpicker_bevel` és
`makemoviepanel/bgcolorpicker_bevel`, a közös tartó
`colorpickerpanel` (ez a respack rétegneve, a leltárban nincs ilyen elem).

#### E) A fül feliratai — a hivatalos magyar fordítással

*Forrás: `makemoviepanel.tre:369` (`makemoviepanel/back_color_label`) · `makemoviepanel.tre:282` (`makemoviepanel/font_label`) · `makemoviepanel.tre:292` (`makemoviepanel/size_label`) — és további 3 elem ugyanott.*

| elem | magyar |
|---|---|
| `makemoviepanel/templatetext` | **„Sablon:"** |
| `makemoviepanel/font_label` | **„Betűtípus:"** |
| `makemoviepanel/size_label` | **„Méret:"** |
| `makemoviepanel/style_label` | **„Stílus:"** |
| `makemoviepanel/text_color_label` | **„Szöveg színe"** |
| `makemoviepanel/back_color_label` | **„Háttér színe"** |

*(Forrás: `panel-feliratok-hu.tsv` 594–599. sor. A `font_label`,
`size_label`, `style_label` NEM a `.tre`-ből jön — a `respack.yt`
`layer:makemoviepanel/text(...)` rétegei hordozzák.)*

A fül ikonjai a respackben: `bold_icon`, `italic_icon`, `makemoviepanel/outline_icon`,
`makemoviepanel/inserticon`, `makemoviepanel/removeicon`.
#### F) NEGATÍV EREDMÉNY — a `titleoption_listbox` ága HALOTT

A `0x006223b0` kezel egy `makemoviepanel/titleoption_listbox` nevű listát
is (`0x00622918`), és a választást a **projekt** objektum `[+0x2c0]`
mezőjébe írja (`0x0062295f`) — tehát **nem diánkénti** beállítás volna.

**Két, egymástól független lekérdezés mondja, hogy ez a lista a 3.9-ben
nem jön létre:**

1. a panelépítő `0x00613b50` a `moviesize`, `templatelist`, `fontfamily`
   és `sizelist` legördülőt hozza létre — **`titleoption`-t nem**;
2. a `makemoviepanel/titleoption_listbox` sztringre a **teljes binárisban
   egyetlen** hivatkozás van, és az maga a kezelő (`0x006223b0`).

⇒ **Nem kell megépíteni.** *(A respack hiánya itt NEM bizonyíték: a
legördülők felugró listái közül **egy sem** szerepel a `respack.yt`-ben —
ezt külön ellenőriztem, a `_listbox` végű nevekre nulla találat. A
negatív eredmény a fenti két lekérdezésen áll, nem a respackon.)*

#### Bizonyítottsági fok

**Megerősített** (utasításszinten olvasva): a beszúrás nyolc lépése és a
`<type> = 2`, a fókusz a beviteli mezőre, a három kapcsoló séma és a
400/700 súly, a három legördülő cél-mezője és a `−1` kilépés, a
tizenhat betűméret, a `makemovie::textfont` preferencia, a színválasztók
előtag-dönése, a hat felirat magyar alakja, és a `titleoption`-ág
halottsága.

**Erős**: a rekord-eltolások (`+0x28`, `+0x2C`, `+0x3C`, `+0x40`,
`+0x41`, `+0x44`) — a helyi puffer `[esp+0x68]` bázisából számolva; a
mezőnevekhez a 2.4/b írója rendeli őket.

### 2.4 Projektfájl és automatikus mentés

`autosave.mxf` (`MakeMoviePanel::autosave` / `recoveredautosave`) — a
kollázs `.cxf`-jének megfelelője a filmhez: **`.mxf` a film-projektfájl**.

### 2.4/b Az `.mxf` formátum — MEGFEJTVE a binárisból (2026-08-16)

Az `.mxf`-ről eddig **csak a fájlnév** volt meg. A projektfájlt ugyanaz a
generikus XML-szerializáló írja, mint a `.cxf`-et (1.6/d), tehát a
szerkezet a writerből **teljesen kiolvasható** — mintára nincs szükség.

**Két író függvény:**

| cím | mit ír |
|---|---|
| `0x00816b00` (1935 b) | a gyökér és az album-szintű beállítások |
| `0x00816440` (1722 b) | **egy átmenet-bejegyzés** — a `defaulttrans`-ra és minden `trans`-ra meghívva |

**A szerkezet:**

```
CTransTimeline                                  <- gyokerelem (0x00816b08)
  <curresolution>%d</curresolution>
  <musicfile>...</musicfile>
  <audiooption>...</audiooption>
  <facemovie>%d</facemovie>
  <showcaption>%d</showcaption>
  <cropfit>%d</cropfit>
  <showdates>%d</showdates>
  <removelowresfaces>%d</removelowresfaces>
  <ordering>%d</ordering>
  <burstmodethresh>%d</burstmodethresh>
  <albumid>%d</albumid>
  defaulttrans                                  <- az ALAPERTELMEZETT atmenet
     ...ugyanaz a tartalom, mint lent...
  trans                             (diankent EGY)
     <transition>%d</transition>                <- az atmenet tipusa (2.1)
     <advanceinterval>...</advanceinterval>     <- a dia ideje
     <transitiontime>...</transitiontime>       <- az atmenet hossza
     <blacktime>...</blacktime>                 <- fekete szunet
     src                                        <- a dia forrasa (al-elem)
        <type>%d</type>                         <- kep / szoveges dia / video
        <bkcolor>%d</bkcolor>
        <index>%d</index>
        <text>...</text>                        <- a szoveges dia szovege
        <filename>...</filename>
        <showflags>%d</showflags>
        textparm                                <- a szoveges dia betuparameterei
           <fontname>...</fontname>
           <size>%d</size>      <color>%d</color>
           <weight>%d</weight>  <italic>...</italic>
           <outline>...</outline> <styleid>%d</styleid>   <- a 11 stilus (2.3)
           <facerectx0>%d</facerectx0>  <facerecty0>%d</facerecty0>
           <facerectx1>%d</facerectx1>  <facerecty1>%d</facerecty1>
           <facemoviesrc>%d</facemoviesrc>      <- az "Film arcokbol" adatai (2.5)
```

**Négy dolog, amit érdemes kiemelni:**

1. **Minden mező gyerekelem, nem attribútum** — a writer végig a
   `0x009c0640`-et hívja (a `.cxf`-fel ellentétben, ahol a geometria
   attribútumként megy ki). A két formátum tehát **nem ugyanazt a stílust**
   követi.
2. **A `defaulttrans` és a `trans` UGYANAZT a szerkezetet írja** (közös író),
   vagyis a diánkénti bejegyzés felül tudja írni az album-szintű
   alapértelmezést. Ez magyarázza, hogy a Picasában a diaidő és az átmenet
   képenként is állítható.
3. **Az arc-téglalap (`facerect*`) minden dián ott van**, nem csak
   arc-filmnél — az arc-film a szokásos dia-rekordot használja, és a
   kivágást ezekkel a mezőkkel rögzíti.
4. A `blacktime` **külön mező** az átmenet hossza mellett: a Picasa a
   diák közé fekete szünetet is tud tenni.

**A fájl helye:** `Movies/autosave.mxf` (`0x0068a4b0`: a mappa a
`CMakeMoviePanel::SlideshowFolder` kulcsból = `Movies`, a fájlnév
`autosave.mxf`, a kimenet `.wmv`).

*Bizonyítottsági fok: **megerősített** a mezőnevekre, a sorrendre és a
gyerekelem/attribútum besorolásra (a writer utasításai) · **erős** a
fájl-szintű keretre (XML-fejléc, sorvégek) — azt a `.cxf` mintájából
következtetjük, mert ugyanaz a szerializáló írja.*


### 2.5 „Film arcokból"

Az `eMenuCreateMovie` két tétele: **A kijelölésben lévő arcokból…**
(`ID_FACES`) és **Az Emberek albumból…** (`ID_FACESRANDOM`). Az
alapértelmezett cím: „People Movie". Az arc-film külön képfelbontással
dolgozik (`facemakemovieres` vs `makemovieres`).

**#4339 záró pontosítás — bemeneti lista és nyitott timeline-belső:** az
`ID_FACESRANDOM` kezelője (`0x0057cb60`, `0x0057cc72`–`0x0057cc7a`)
a filmpanel `+0x4f1` módjelzőjét állítja; a `0x00618050` ezt 6-os
módlekérésként használja a `panel+0x4b4` objektum 0. vtable-slotján
(`0x00618236`), az eredményt pedig a `+0x4b8` mezőbe teszi.

A mód 6 konkrét listája most azonosított. A `0x00699cd0` módválasztó
a 6-os értéknél 1-es ágválasztót ad a `0x00824090`-nek
(`0x0069a305`–`0x0069a310`, Capstone). A `0x00824090` így a
`0x008226e0` listafeldolgozót hívja; a nulla jelzős, album-kijelölésen
alapuló ág külön a `0x008223e0` (`0x008240e9`–`0x00824114`). A People/
Face mód tehát nem ezt a kiválasztottalbum-ágat használja.

A `0x008226e0` a `+0x2bc` (`+700`) objektum `0x00449a90`-nel lekért
azonosítólistáját járja végig (`0x00822715`); minden azonosítóhoz a
`+0x2c0` objektumon kér alsó listát (`0x0082274f`–`0x0082275a`), és
csak nem üres alsó listánál fűzi az elemet a kimenethez
(`0x0082275f`–`0x00822775`). A forráslista indexe növekszik
(`0x008229f0`–`0x008229fb`); a függvényben rendező hívás/ág nem látszik,
ezért a kimenet a szűrt bemenet sorrendjét őrzi. A `0x008223e0` az
eltérő, nulla jelzős ág album-azonosítóit építi.

A `0x006175c0` továbbra is a `+0x4bc` filmmodellt építi újra: átveszi a
`+0x4b8` listát a modell `+0x2d8` mezőjébe és iterál rajta; nem ez
választja ki a People/Face bemeneti ID-kat. A `0x00616940` olvassa a
`cropfit` beállítást és az arcmód felbontási kulcsát; a `0x0080fea0`
általános modellmezőket/node-okat inicializál.

#### A modell átadása és a klip arcmezői — #4400

A `0x00619010` a `+0x4bc` filmmodell címét adja át a `0x00555a30`-nak
(`0x006190ae`). A `0x00555a30` a `CTransTimeline` szolgáltatásnak
`.set` hívást küld a modellmutatóval; a `0x0074e710` setter ezt
dereferálja, majd a `0x0074d8a0` a szolgáltatás `+0x308` mezőjébe
menti (`0x0074d8b1`). A `0x00555a30` és a `0x0074d8a0` vizsgált
utasításai nem számítanak arckivágást. A timeline későbbi rajzolóágában a
`0x00813330` `0x00813c50`-et hívja; ez az arc-keretező számítás. A klip
`+0x18…+0x24` mezőit ez a helper közvetlenül nem olvassa: a staging-rekord
`+0x8` selectorával a modell `+0x2d8` forrásobjektumának vtable-ján kér
méretet és arctéglalapot. A helper képlete most megvan; a virtuális getterek
konkrét implementációját, a forrás-rect mezőjét és a staging selector
klipmezőhöz vezető útját a 4. kör alább feloldja.

A kliprekordok a modell `+0x48` listájában vannak; a `0x00611320`
rekordlépése `0x006113cf` szerint **0xf8 bájt**. A `0x00816440` XML
író a rekord következő mezőit írja ki (a mezőneveket a `.mxf` parser
`0x008152f0` is használja):

| rekordmező | `.mxf` név | író utasítás | amit a bizonyíték megenged |
|---|---|---|---|
| `+0x14` (előjeles bájt) | `facemoviesrc` | `0x00816aa6` | a szerializáló kiírja; az író `0x00814fe5` a jogosult kliprekordban `1`-re állítja, ezért ez az útvonalon jelző, nem arcazonosító |
| `+0x18` | `facerectx0` | `0x00816976`; beíró: `0x0081510a` | a kiválasztott arcrekord első dwordje változtatás nélkül kerül ide; **képpont**, a forráskép bal széle felől |
| `+0x1c` | `facerecty0` | `0x008169c2`; beíró: `0x00815110` | a második dword változatlan másolata; **képpont**, a forráskép felső széle felől |
| `+0x20` | `facerectx1` | `0x00816a0e`; beíró: `0x00815116` | a harmadik dword változatlan másolata; **képpont**, a forráskép bal széle felől |
| `+0x24` | `facerecty1` | `0x00816a5a`; beíró: `0x00815120` | a negyedik dword változatlan másolata; **képpont**, a forráskép felső széle felől |

**A `CTransTimeline` arckeretező képlete — statikus dekódolás és QEMU (#4400, 4. kör).**

A `0x00813330` a `0x008135c7` címen hívja a `0x00813c50`-et, ha a
timeline-mód `+0x28c == 0x14`. A `0x00813c50` csak akkor futtatja az arcágat,
ha a `+0x1a8` staging-rekord első dwordja `3`, és a `+0x8` selector nem
`-1` (`0x00813c91`–`0x00813ca0`). A modell `+0x2d8` objektumának vtable
`+0x58` slotja két kimeneti mutatóba adja a forráskép szélességét és
magasságát; a `+0xa0` slot a selectorhoz tartozó `x0,y0,x1,y1` arctéglalapot
adja vissza (`0x00813caa`–`0x00813cef`). A helper a bal/felső koordinátát
legalább 0-ra, a jobb/alsót legfeljebb a forráskép szélességére/magasságára
korlátozza (`0x00813cef`–`0x00813d35`), majd az üres téglalapot elutasítja.

Jelölések: `Vw,Vh` a hívótól kapott keretméret, `Iw,Ih` a `+0x58` getter
forrásképmérete, `R` pedig a `+0xa0` getter által visszaadott téglalap. A
bináris `0x00cf48f8` qword konstansa
`δ = 0.49900001287460327`; a kód ezt mindkét `V` mérethez hozzáadja.
`cropfit` a modell `+0x2c5` bájtja (`0x00813d3b`–`0x00813d46`). Az első,
egységes képskála:

```
cropfit != 0: s = max((Vw + δ) / Iw, (Vh + δ) / Ih)
cropfit == 0: s = min((Vw + δ) / Iw, (Vh + δ) / Ih)
```

A két ág rendre a `0x0049fae0` max- és `0x0049fab0` min-segédet hívja
(`0x00813dd0`, `0x00813e5e`). A `cropfit != 0` ág a teljes képet a kerethez
igazító cover/crop téglalapot a `0x009b4b60`-nal számítja; a nulla ág a
contain/fit téglalapot a `0x009b4aa0` és `0x009b49c0` segítségével. Mindkét
út középre teszi a képet, majd ugyanazzal az `s` skálával viszi át az arc
téglalapját. Az igazítás egész koordinátáját ezek a segédek állítják elő;
az x87 `FISTP` és a középre osztó előjeles `SAR 1` része a bináris
viselkedésnek (`0x009b49c0`, `0x009b4aa0`, `0x009b4b60`).

A skálázott, középre igazított arctéglalap mérete legyen `Bw × Bh`. A helper
az `r = min((Vw + δ)/Bw, (Vh + δ)/Bh)` arányból választ végső zoomot
(`0x00813fac`–`0x00813fe6`; a `0x0049fab0` minimumsegéd). A pontos
ágfeltétel és konstansok (`0x00813fef`–`0x00814027`):

```
r > 4.0:       z = r / 3.0
r <= 4.0:      z = min(r, 1.2999999523162842)
```

A `4.0`, `3.0` és `1.2999999523162842` értékek rendre a
`0x00c7e4a4` float, a `0x00cf39f8` qword és a `0x00c7e4ac` float tartalma.
A végső téglalap középpontja a skálázott arctéglalap közepe; a fél szélesség
és magasság rendre `Bw*z/2` és `Bh*z/2`. Ezután a bal/felső szélt 0-ra, a
jobb/alsó szélt `Vw`/`Vh`-ra korlátozza (`0x0081402b`–`0x00814149`). A
téglalap oldalankénti többlete a középre igazított esetben pontosan
`(z-1)/2`-szerese az arctéglalap adott méretének; a faktor nem minden
méretnél állandó: `r>4` esetén `r/3`, `r<=1.3` esetén pedig `r`.

**QEMU-ellenőrzés.** A `0x00813c50` eredeti kódja futott a helyi QEMU-
harnessben, `x87 CW=0x027f` mellett. A `+0x58` és `+0xa0` virtuális slotot
szintetikus válaszadók helyettesítették, ismert képmérettel és
arctéglalappal; ez a helper számtanát méri, nem a teljes paneltől a
videókockáig tartó adatutat.

| Bemenet (`Vw×Vh`, `Iw×Ih`, `cropfit`, `R`) | mért kimeneti téglalap | ellenőrzött ág |
|---|---|---|
| `1024×768`, `1024×768`, `1`, `[200,200,500,400]` | `[155.10072326660156,170.11045837402344,545.3541259765625,430.27935791015625]` | `s` float32-bitek: `0x3f80154a`; `z` float32-bitek: `0x3fa66666` |
| `1024×768`, `1024×768`, `1`, `[100,100,200,200]` | `[22.0142822265625,22.0142822265625,278.1806335449219,278.1806335449219]` | `r>4`, `z` float32-bitek: `0x4023d70b`, a `r/3` ág; cáfolja az állandó `1.3` zoomot |
| `1024×768`, `2000×1000`, `cropfit=1/0`, `[800,400,1200,600]` | `cropfit=1`: `[312.68927001953125,284.3446350097656,712.3087768554688,484.1543884277344]`; `cropfit=0`: `[341.49969482421875,298.7498474121094,682.99932861328125,469.4996643066406]` | a cropfit 1-es max- és 0-s min-skálaválasztása |

A QEMU-számítás és az utasításszintű képlet egyezik a visszaadott arctéglalap
és képméretek mellett. A `0x00813c50` a `+0xa0` getter által visszaadott
négyszög közepéhez igazít. A getter teljes rect-adatútja és a landmarkokra
vonatkozó bizonyítás határa alább szerepel; a QEMU-próba a gettereket
szintetikus válaszadókkal helyettesítette.

**A forrásobjektum, getterek és a klip-selector útja — #4400, 4. kör.**

Az objektum típusa nem csak a gettercímekből következik. A mód-6 gyárág a
`0x00824090`-ben hívja a `0x006999c0` konstruktorát (`0x008240dc`); a
konstruktor a `this` első dwordjába `0x00ca7d8c`-t ír (`0x006999d8`). A
bináris RTTI ezt az `AlignedImageCollection::vftable` címeként nevezi meg.
A panel `+0x4b8` forrásmutatóját a filmmodell `+0x2d8` mezője veszi át
(`0x00616957`). A vtable nyers bejegyzései:

| slot | bináris célfüggvény | szerep a hívási láncban |
|---|---|---|
| `AlignedImageCollection::vftable +0x58` | `0x0068f900` | a kiválasztott elem szélességét és magasságát kéri le |
| `AlignedImageCollection::vftable +0xa0` | `0x0068f980` | a kiválasztott elem arctéglalapját kéri le |
| `AlignedImageCollection::vftable +0x60` | `0x0068f710` | csoport- és elemsorszám alapján adja vissza a kiválasztott elemet |

A `0x00813c50` mindkét getternek a 0. csoportot és a staging `+0x8`
értékét adja (`0x00813cba`–`0x00813ccd`, `0x00813cd9`–`0x00813ced`). A
`0x0068f900` és `0x0068f980` egyaránt a `+0x60` slotot használja az elem
feloldásához. A `0x0068f710` az első argumentumot a csoportlistában, a
másodikat az adott csoport gyermeklistájában ellenőrzi, majd a gyermeklista
megfelelő dwordját adja vissza (`0x0068f710`–`0x0068f73c`). Így a klip `+0x8`
mezője ezen az úton **0-tól számozott lista-selector**, nem kontakt- vagy
személyazonosító.

A selector klipről stagingbe jutása is követhető. A `0x00610d30` az időponthoz
tartozó rekordot a `+0x48` kliplistából, `0xf8` bájtos lépésközzel választja
ki (`0x00610e16`–`0x00610e25`). A `0x006123d0` rekordmásoló a forrás `+0x8`
dwordját változatlanul továbbviszi (`0x006123ed`–`0x006123f1`); a
`0x00812470` ezután a kiválasztott mintát a modell `+0x1a8` stagingrészébe
másolja a `0x00612350`-nel (`0x00812578`–`0x00812580`). A
`0x00813330` ugyanennek a `model+0x1a8` címnek az első argumentumát adja a
`0x00813c50`-nek (`0x008134b5`, `0x008135c7`). A szerializáló oldalán a
`0x00814f30` a klip `+0x8` értékével hívja a `0x0081e2d0`-t, amely a modell
`+0x4e8` leképezőlistáján keresztül választ rectrekordot. A két út ugyanazt
a klipből másolt selectorértéket használja; a writer maplistájának és a
getter `AlignedImageCollection`-listájának kiválasztott adatelemei közötti
azonosságot ez a kör nem állapítja meg.

**A getter alap-rectje, utófeldolgozása és a landmarkok.** A
`0x0068f980` ugyanazzal a `+0x60` selectorral választ elemet, majd a
`0x0047a390`-en keresztül hívja a `0x00446610` imagedata-olvasót
(`0x0068f9a5`–`0x0068f9c3`, `0x0047a3a8`–`0x0047a3af`). A közvetlen
alap-rectforrás a kiválasztott sor 64 bites `imagedata_facerect` mezője:
a `0x00446610` két dwordként olvassa, packed `rect64`-ként értelmezi, majd a
`0x009b93f0`-en át képpontra váltja (`0x004467b2`–`0x004467dc`,
`0x004468dd`). A mezőt az imagedata-rekord leírása u64-ként regisztrálja
`facerect` néven (`+0xdc0`); a külön `facerectdata` sztringmező `+0xee8`
(`picasa-imagedata-rekord.md`, mezőtábla).

`0x0047a390` visszatérési rectje azonban nem feltétlenül ez a nyers
alap-rect. A `0x0068f980` az `AlignedImageCollection` objektum `+0x94`
mezőjéből kiolvasott `CThumbDB` mutatót adja át a bridge-nek
(`0x0068f9a5`), valamint `1` flaget (`0x0068f9ab`); a bridge ennek az
objektumnak a `+0x14d0` per-index recttábláját használja a
`0x00429dc0` hívásban (`0x0047a3be`–`0x0047a3da`). Ha a hívás sikeres, a
`0x0047a3de`–`0x0047a419` utasítások metszik az alap-rectet a táblából
kapott recttel. A `+0x94`-beli objektum osztálya a 6. kör szerint
`CThumbDB`; a második recttábla filmkészítés előtti konkrét íróhívása és
az arcrekordhoz való példányszintű kapcsolata nincs feloldva. Ezután a
`0x0042c830` a `rotate(%d)` mezőt
olvassa (`0x00c81474`), a `0x00430610` a `filters` mezőt (`0x00c80b04`),
majd a `0x00a4a240` affín módon transzformálja a rect négy sarkát; a bridge
az eredményt visszaírja (`0x0047a41c`–`0x0047a484`). A `rotate` és
`filters` adatok pontos numerikus hatását és a transzformáció mérhető
bemeneti tartományát ebben a körben nem mértem. Így a
`imagedata_facerect` a közvetlen alapforrás, nem bizonyítottan a getter
egyetlen rectforrása vagy utófeldolgozás nélküli kimenete.

A külön `facerectdata` mező a `conf`, `pan`, `leye`, `reye`, `mouth`
adatokat tárolja. A vizsgált getter/crop utasításláncban ennek a mezőnek vagy
a szemkoordinátáknak közvetlen olvasása nem látszik; a `0x00813c50` a
transzformált getter-rect közepéhez igazít. Mivel a `+0x14d0` recttábla
előállításának forrása nincs feltárva, **nem dönthető el**, hogy a szemadat
közvetve részt vett-e ennek a táblának a létrehozásában. Ez az állítás
feltételes; a teljes `+0xa0` út QEMU-mérése nem történt meg.

**Független ellenőrzés és QEMU-mérés.** A) a mód-6 konstruktorút a
`0x006999c0` függvényen át a `0x00ca7d8c` vptr-hez vezet; B) a nyers
vtable-adat és az RTTI ugyanazt az `AlignedImageCollection` osztályt és a
`+0x58/+0xa0/+0x60` slotcímeket adja. Ez a két út az osztály- és
slotazonosítást egymástól függetlenül alátámasztja. A klip `+0x8` → staging
`+0x8` másolását utasításszintű adatfolyam, a listaindex-szerepet pedig ez
és a QEMU-harness egyezése támasztja alá. A QEMU-futásban a `0x0068f710`
szintetikus, egycsoportos/kételemű listán a `selector=0` első,
`selector=1` második elemet adta vissza; `selector=2` és `group=1` esetén
`0xffffffff`-et adott. A `0x0068f900` ugyanebben a harnessben a második
elemhez rendelt szintetikus méretgetterből `1920×1080` értéket adott vissza.
Ez a QEMU-próba nem futtatta a `+0xa0` rectolvasó-láncot.

Az alap-rectmező, a `+0x14d0`-beli második rect, annak upstream forrása és a
landmarkmező hiányzó olvasása ebben a körben egyetlen statikus
utasításláncból következik; a vptr/RTTI út és a QEMU-próba ezeket nem méri
függetlenül. Ezek ezért feltételes megállapítások, nem megerősített
rectforrás- vagy landmarkeredet-állítások.

**Cáfoló próbák.** A teljes `.text`-en a `paszta.py` streaming pásztájával
kerestem az indirekt `+0x58/+0xa0` hívásokat és a rect/landmark mezők
olvasóit. Azt az első feltevést, hogy a getter kimenete változatlanul a
`facerect`, a `0x0047a390` utófeldolgozásának célzott diszasszemblálása
cáfolta: van `+0x14d0`-beli recttel vett metszet és rotate/filter alapú affín
transzformáció. A talált adatfolyamot ugyanazzal a címszintű mércével
ellenőriztem: `0x0047a390` közvetlenül hívja a `0x00446610` alap-rect
olvasót, majd az adott flag-ágban a leírt második rectet és transzformokat
alkalmazza. További, azonos sloteltolású hívások is előkerültek (például
`0x00618aa2`, `0x00618ed8`), de ezek a panel `+0x4a0` illetve a panel `this`
vtable-ján futnak, nem a filmmodell `+0x2d8` objektumán; ezért nem cáfolják a
fenti vptr-azonosítást. A getter- és rectolvasó-függvények utasításszintű
ellenőrzésében a `facerectdata`/szemlandmark mezőre vezető közvetlen olvasás
nem jelent meg; ez a negatív eredmény csak a vizsgált utasításláncra
vonatkozik, a `+0x14d0` tábla előállítását nem fedi le. A `.picasa.ini`
`faces=` sor és az imagedata `facerect` oszlopa közötti betöltési kapcsolat
ettől még **nincs bizonyítva**.

**A `rect64` → pixel-rect út és a még nem bizonyított `faces=` kapcsolat.**
Külön megfigyelt `.picasa.ini`-út, hogy a `0x00456610` kódterületén
sztringhivatkozás van a `faces` (`0x00c81884`) és `rect64`
(`0x00c81460`) kulcsra; a `0x0045a9d0` `.picasa.ini`-útból hívott
`0x0049d560` feldolgozó `rect64(%I64x)` alakot olvas, dekódolja a négy
16 bites komponenst (`0x009b9190`), majd pixelkonvertert hív
(`0x009b93f0`, `0x0049d6f4`). Ettől külön az imagedata `facerect`-olvasója
(`0x00446610`) az u64-mezőből kapott komponenseket a kép `width`/`height`
értékével a `0x009b93f0` függvényen keresztül **képpontra váltja**
(`0x004467bf`, `0x00446859`, `0x004468dd`). A modellbetöltő `0x0081fc30`
ezt az olvasót hívja (`0x00820bac`), majd a 14 dwordös rekordot a `+0x4e0`
táblába másolja (`0x00820f01`–`0x00820f0a`); ezen a bizonyított ágon a tábla
első négy dwordje pixel-rect. A `0x0081e2d0` selectorja ezeket adja tovább
a klipnek. **A `faces=` ág és az imagedata `facerect` mezője közötti pontos
adat-/hívási kapcsolat nincs bizonyítva**, ezért a teljes
`.picasa.ini faces=` → `+0x4e0` lánc állítása nyitott.

**Pontos `rect64` → pixel képlet a Picasa 3.9 binárisban:** a skálázási
konstans a `0x00cf3b78` qword **65535.0** (bájtsor: `00000000e0ffef40`).
Előbb a bal/jobb és felső/alsó végpontot növekvő sorrendbe teszi
(`0x009b9454`–`0x009b9461`), majd a tényezőket egyszeres pontosságú floatként
állítja elő: `sx = float32(width / 65535.0)`, `sy = float32(height / 65535.0)`
(`0x009b9414`–`0x009b9449`). A végpontok:

```
x0 = clamp(FISTP(float32(u0 * sx)), 0, width  - 1)
y0 = clamp(FISTP(float32(u1 * sy)), 0, height - 1)
x1 = clamp(FISTP(float32(u2 * sx)), 1, width)
y1 = clamp(FISTP(float32(u3 * sy)), 1, height)
```

`FISTP` az aktuális x87 kerekítési módot használja; a terméket a kód
előbb float32-re kerekíti (`0x009b9464`–`0x009b950b`). Ha a végpontok a
kerekítés után összeérnek vagy kereszteződnek, a kód a bal/felső értéket a
jobb/alsó mínusz 1-re állítja (`0x009b950b`–`0x009b9522`).

Ez a kiíró a rekordból olvas és `%d`-ként szerializál; önmagában nem
bizonyítja, hogy a négy érték képpont vagy végső crop. Az íróút most
feltárt: a `0x00814f30` a `+0x48` kliplistát `0xf8` lépésközzel járja;
az `+0x0 == 3` rekordnál a `+0x8` értéket a `0x0081e2d0` selector
paramétereként használja, és a rekord `+0x14` bájtját `1`-re állítja
(`0x00814fe5`). A `0x0081e2d0` a selectorral indexeli a modell
`+0x4e8` maplistáját, a kapott rectindexet ellenőrzi a `+0x4e4` counttal,
majd a `+0x4e0` táblából, `0x38` bájtos lépésközzel kiválasztott rekord
első négy dwordjét másolja a kimenetbe (`0x0081e2d5`–`0x0081e31c`).
Érvénytelen selector vagy rectindex esetén mind a négy kimeneti dword 0.
Ezeket a dwordöket a `0x00814f30` közvetlenül a klip `+0x18…+0x24`
mezőibe teszi; ezen az úton nincs margó-, képarány- vagy szemigazítási
számítás. A `+0x8` mező tehát maplistabeli selector; személy- vagy
kontaktazonosítóval való azonossága **nincs meg**.

**Független futáspróba a másolásra:** a
`picasa-arcfelismeres.md` ismert példájából
(`faces=rect64(27c00680d8ffdb3f),ffffffffffffffff`) a már dokumentált
`rect64` bitelrendezés szerinti `[0x27c0, 0x0680, 0xd8ff, 0xdb3f]`
dwordöket adtuk a `0x0081e2d0`-nak QEMU-harnessben, egy szintetikus
`0x38`-as táblaelemen keresztül. A kimenet ugyanez a négy dword lett
(`c027000080060000ffd800003fdb0000`). Ez a helper nyers másolását
megerősíti, de **nem** futtatja az INI-betöltéstől a timeline-ig vezető
teljes utat, és nem igazolja a dwordök koordináta-jelentését. A statikus
utasításolvasás és a QEMU-eredmény egyezése a másolásra
**megerősített** bizonyíték; a forrásrekord pixel-egységét a fenti
betöltési lánc igazolja, a lejátszási crop továbbra is nyitott.

**QEMU-futáspróba a skálázási nevezőre:** a harness közvetlenül hívta a
`0x009b93f0`-et `x87 CW=0x027f` mellett. Bemenet: rect64-kód
`[1,1,100,100]`, kép `32768×32768`; mért kimenet: pixel-rect
`[1,1,50,50]` (stdout little-endian: `01000000010000003200000032000000`).
Ez a minta elválasztja a bináris `65535.0` nevezőt a régi `/65536` leírástól:
utóbbi ugyanebben a kerekítési módban bal/felső koordinátára `0`-t ad.
Ez a helper izolált futása, nem a teljes `.picasa.ini` → timeline → render
út futtatása.

**A `+0x14d0`-es crop-tábla eredete és szerepe — #4400, 5. kör.**

A kért filmútban a `0x0068f980` az `AlignedImageCollection` `+0xa0`
getterje, amely a `+0x60` sloton át feloldott selectorhoz hívja a
`0x0047a390` bridge-et (`0x0068f9a5`–`0x0068f9c3`). A getter a saját `+0x94`
mezőjéből származó objektummutatót és `1` flaget ad át (`0x0068f9a5`,
`0x0068f9ab`); a bridge ennek az objektumnak a `+0x14d0` recttáblájából kér
indexelt bejegyzést a `0x00429dc0`-nál (`0x0047a3be`–`0x0047a3d5`). A
`0x0047a390` először a `0x00446610`-tól kéri le a kiválasztott elem
`imagedata_facerect` alap-rectjét (`0x0047a3a8`–`0x0047a3aa`), majd a
`0x00429dc0`-tól az adott index crop-rectjét. Ha az accessor talál cropot,
a filmút komponensenként metszi a két képpont-rectet:
`x0=max(face.x0,crop.x0)`, `y0=max(face.y0,crop.y0)`,
`x1=min(face.x1,crop.x1)`, `y1=min(face.y1,crop.y1)`
(`0x0047a3de`–`0x0047a419`). Ezután a `rotate(%d)` értékét a `0x0042c830`
olvassa, a `0x00430610` filter-utat, majd a `0x00a4a240` affinképzést hívja
(`0x0047a41c`–`0x0047a470`). A klip renderelése tehát az arc-rectet a
forrás cropjával metszi; a `+0x14d0` bejegyzése crop-rect, nem
szemlandmark-koordináták sora. Ez önmagában nem zárja ki, hogy valamelyik
upstream írója landmarkból számítsa ki a crop-rectet.

A `0x0042b370` a feloldott crop-író: a `0x0042b000` segítségével elforgatja
és határolja a kapott rectet, a `0x009b9290`-nal 64 bites `rect64` értékké
normalizálja, a `0x00cd9554` formátummal `rect64(%I64x)` alakban formázza,
majd a `0x00c812f8` (`crop`) kulcs alá írja (`0x0042b3e0`–`0x0042b3f5`,
`0x0042b499`–`0x0042b530`). A `this+0x14d0` mezőn belüli vektor
`+0x58/+0x48` címen levő 8 bájtos elemeket index szerint frissíti
(`0x0042b535`, `0x0042b747`–`0x0042b785`); ugyanilyen indexelt olvasást
végez a filmútban a `0x00429dc0` (`0x00429dce`, `0x00429e22`–`0x00429e43`).
A `0x00429dc0` által visszaadott elem tehát az adott kiválasztott elemhez
tartozó crop-rect, nem `leye`/`reye` koordinátákat tároló tábla.
Ugyanakkor a `0x0042b370` receiverének és a getter `+0x94` mezője által
mutatott objektumnak az azonosságát a vtable/RTTI nem nevezi meg; a
`0x0042b370` ezért a táblával azonos elrendezésű crop-író jelölt. A
következő, 6. kör a `+0x94` célosztályát azonosítja; ez önmagában még nem
bizonyítja, hogy minden `0x0042b370`-hívó ugyanazt a példányt kapja. Közvetlen
hívóhelyei:

| hívóhely | hívófüggvény | bizonyított környezet |
|---|---|---|
| `0x00531e21` | `0x00531c60` | Passport-ág; a függvény stringjei: `CThumbUI::Passport0`, `Can't find any faces` (`0x00c899c4`, `0x00c899ac`) |
| `0x006b0253` | `0x006b0200` | általános rect-/crop-író segéd; hívói közt a `0x005d4b60`, amelynek stringjei az `editpanel/cropselection` és az `editpanel/cropdiscard` (`0x00c95ae4`, `0x00c95fe8`) |
| `0x006b3cd9` | `0x006b39b0` | további rect-író út; a transzformációs rekord `esi+ebp+0x40` rectmutatóját adja át; hívója `0x006abae0` |

**A `+0x94` célosztálya és a filmkocka geometriája - #4400, 6. kör.**

Az `AlignedImageCollection+0x94` célja **`CThumbDB`**. A példány a film
üzemmód kiválasztása előtt létrejön: a `0x00402f90` út a `0x00415790`
konstruktort hívja, majd az eredményt az alkalmazás `+0x1034` mezőjébe
teszi (`0x00402faf`-`0x00402fdc`). Az inicializálás az alkalmazás
`+0x1034` mutatóját a `CThumbUI+0x2bc` mezőbe másolja
(`0x00403dae`-`0x00403db6`, `0x005643f0`-`0x00564616`). A mód-6
gyárág (`0x00824090`) a `CThumbUI+0x2bc` értékét adja a
`0x006999c0` konstruktornak (`0x008240d3`-`0x008240dc`); a konstruktor
`0x0068c880`-on át inicializálja az `AlignedImageCollection`-t, és a
kapott mutatót annak `+0x94` mezőjébe írja (`0x006999c3`-`0x006999c7`,
`0x0068c8ff`).

Két, egymástól független út azonosítja az osztályokat. **A)** a fenti
utasításszintű mutató-adatfolyam az induláskor tárolt `CThumbDB` példányt
köti a mód-6 kollekció `+0x94` mezőjéhez. **B)** a `0x00415790` konstruktor
`0x00c81f78` vptr-értéket ír (`0x004157fd`), amelyet az RTTI
`CThumbDB::vftable`-ként nevez meg; a `0x006999c0` a `0x00ca7d8c`
vptr-értéket írja (`0x006999d8`), amelyet az RTTI
`AlignedImageCollection::vftable`-ként azonosít. A `+0x94` mező tehát
adatbázisobjektumra mutat, nem a három jelölt egyikének újonnan felépített
ideiglenes objektumára.

| jelölt | közvetlenül bizonyított szerep | következtetés a filmkészítésre |
|---|---|---|
| `0x00531c60` | Passport/útlevélkép ág (`CThumbUI::Passport0`, `Passportfail`, „Can't find any faces”); a `0x00531e1b` hívás `CThumbUI+0x2bc` mutatójával hívja a `0x0042b370` crop-írót | a közös `CThumbDB` `+0x14d0` tábláját írhatja ebben a Passport-ágban; ez nem az objektum konstruktora, és nem bizonyít filmkészítéskori hívást |
| `0x006b0200` | a `+0x15` jelzőtől függően helyi szerkesztési rectet ír vagy a `+0x0c` mutatóval hívja a `0x0042b370`-et; hívói közt Passport- és szerkesztőút is van | crop-adatot írhat, de a filmkészítéskori példány/hívás nincs igazolva |
| `0x006b39b0` | szerkesztési rekord `+0x40` rectjét adja a `0x0042b370`-nek a `+0x0c` mutatón keresztül; közvetlen hívója `0x006abae0` | szerkesztési crop-visszaíró út, nem a `+0x94` objektum konstruktora; a filmkészítési hívás nincs igazolva |

**A crop-író receiverének kötése az `AlignedImageCollection+0x94` mezőhöz - #4400, 7. kör.**

A három vizsgált közvetlen hívó közül a `0x00531c60` receiveréről bizonyítható,
hogy ugyanaz a `CThumbDB`-példány, amelyet a filmút az
`AlignedImageCollection+0x94` mezőjébe tesz. Az alkalmazás a `CThumbDB`
mutatóját a saját `+0x1034` mezőjében tartja; a `0x005643e0` ezt a mutatót
a `CThumbUI+0x2bc` mezőbe másolja (`0x00564616`). A Passport-ágban a
`0x00531e1b` tölti `ECX`-be ezt a `CThumbUI+0x2bc` mutatót, majd a
`0x00531e21` hívja a `0x0042b370`-et. A film mód-6 gyárága a
`CThumbUI+0x2bc` értékét adja a
`0x006999c0` kollekciókonstruktornak (`0x008240d3`-`0x008240dc`); a
`0x0068c880` ezt a kapott mutatót írja az `AlignedImageCollection+0x94`
mezőjébe (`0x0068c8ff`). Az `0x00415790` és `0x006999c0` konstruktor
vptr-értékeit a RTTI rendre `CThumbDB::vftable`-ként
(`0x00c81f78`) és `AlignedImageCollection::vftable`-ként (`0x00ca7d8c`)
azonosítja. A két külön adatfolyam ugyanahhoz a tárolt mutatóhoz vezet;
ez nem következtetés pusztán a mezőeltolás egyezéséből.

A másik két hívó (`0x006b0200`, `0x006b39b0`) a `0x0042b370` előtt a
saját `EDI+0x0c` mezőjét tölti `ECX`-be (`0x006b024f`, `0x006b3cd0`).
Ezeknek a receivermezőknek az alkalmazás `+0x1034` mezőjével való
azonossága nincs bizonyítva; az aliasolásuk sincs kizárva. A
`0x00531c60` tehát a **közös példányhoz kötött íróút**, de maga a függvény
Passport-műveletet végez. Nincs bizonyíték arra, hogy a Film arcokból
indításakor vagy renderelésekor meghívná. A `0x0042b370` a rectet a
`this+0x14d0` indexelt táblába írja és a `.picasa.ini` `crop` kulcsát is
frissíti (`0x0042b370`, `0x0042b535`, `0x0042b747`-`0x0042b785`); ebből
következik, hogy a film a közös adatbázisban korábban tárolt cropot
olvashatja, de a konkrét film-selectorhoz tartozó bejegyzést nem futás
közben figyeltük meg.

**Cáfoló próba - a transzformáció és metszés sorrendje.** A lehetséges
ellenhipotézis az volt, hogy a getter előbb forgatja/transzformálja az
arctéglalapot, és csak utána metszi a crop-recttel. A célzott
utasításolvasás ezt cáfolja: `0x0047a3a8`-`0x0047a3aa` lekéri az alap
`facerect`-et, `0x0047a3d5` a cropot, `0x0047a3de`-`0x0047a419` elvégzi a
komponensenkénti metszést, majd `0x0047a429` hívja a forgatási segédet,
`0x0047a45c` a filter-segédet, és `0x0047a46c` a négy sarok affín
transzformációját. A friss kontextusú, önálló bináris újralevezetés ugyanezt
a sorrendet adta. A másik két íróreceiver ellenpróbája nem cáfolta a
lehetséges aliasolást: náluk `ECX=[EDI+0x0c]`, így az azonosságuk továbbra
sem állítható.

A film crop-olvasó útja `0x00813c50` → az `AlignedImageCollection`
`+0xa0` vtable-slotja (`0x0068f980`) → `0x0047a390`. A getter kiolvassa
a `+0x94`-beli `CThumbDB` mutatót (`0x0068f9a5`), lekéri az alap
`imagedata_facerect` rectet (`0x0047a390` → `0x00446610`), és a
`+0x14d0` táblából kapott crop-recttel komponensenként metszi
(`0x0047a3be`-`0x0047a419`). A vizsgált olvasólánc egyik jelölt írót sem
hívja. Ez a közvetlen lánc egyikét sem teszi a filmkészítési adat előállítójává;
közvetett callback vagy a film indítása előtti korábbi szerkesztés szerepe
ettől még nincs kizárva.

A kiválasztott filmfelbontás a cropképlet `Vw,Vh` keretméretét a
`model+0x2e0` objektum alap-geometriáján keresztül éri el. A
`0x00616940` a `facemakemovieres` felbontási indexét keresi ki
(`0x00616b42`-`0x00616b64`), majd a kiválasztott indexet a
`0x0080fea0`-nak adja (`0x00616be0`-`0x00616be4`). A `0x0080fbc0`
`12 × index` eltolással olvassa a `0x00c7db50` táblából a szélességet és
magasságot (`0x0080fc11`-`0x0080fc1f`), létrehozza a `ytDrawNode`-ot,
és a `model+0x2e0`-ba teszi (`0x0080fc51`-`0x0080fc68`). A
`0x00512220` az alap-rectet `[0,0,W,H]`-ként írja a node-ba
(`0x0080fc6e`-`0x0080fc8e`, `0x00512254`-`0x0051227b`).

A `ytDrawNode` `+0x20` virtuális getterje `0x009e0660` (vptr
`0x00cda8cc`, RTTI alapján); a `0x00813330` ezen a sloton kéri le a
téglalapot, majd a jobb-bal és alsó-felső különbséget adja tovább
`Vw,Vh`-ként a `0x00813c50`-nek (`0x008133c4`-`0x008133d6`,
`0x0081356b`-`0x008135c7`). A getter transzformációs bemenetet is fogad,
ezért a képlet **a getter által visszaadott** `Vw,Vh`-t használja; a
statikus lánc az alap-rect és a felbontási sor kapcsolatát bizonyítja, nem
azt, hogy minden futásban a transzformált méret változatlanul egyezik a
tábla nyers `W,H` értékével. A kiválasztott sorok pontos méretei a 2.8/b
táblájában szerepelnek: az 5-ös és 6-os sor `1280×720`, illetve
`1920×1080` (16:9); a 0-4-es sorok `320×240`, `640×480`, `800×600`,
`1024×768`, `1600×1200` (4:3). Az arc-film alapértelmezett indexe 3,
azaz `1024×768` (`0x00616b50`).

A 2.5-ben fent megadott `0x00813c50` képletben `Vw,Vh` mind a kezdő
képskála `s`, mind az arczoom `r` nevezőiben szerepel. Így a 16:9/4:3
felbontás a keretszélesség és -magasság arányán keresztül befolyásolja a
cropot; a visszaadott crop az arc `Bw:Bh` arányát tartja meg az élhatárokra
vágásig, nem kényszeríti a téglalapot a videó képarányára. A középre
igazított, előjeles oldalankénti félméret-változás pontosan
`(z-1)·Bw/2`, illetve `(z-1)·Bh/2`; ha `z<1`, ez szűkítés, nem pozitív
margó. Keretbe vágáskor a látható oldalankénti érték eltérhet. E képletet a korábbi
QEMU-mérés ismert `[200,200,500,400]` arctéglalapon és `1024×768`
kereten igazolta; a táblázat az elszigetelt helper futását dokumentálja, nem
a teljes film-exportot.

A teljes `.text`-pásztázás külön jelöltje a `0x00421bf0`: ez is az
`arg+0x14d0` mező `+0x58/+0x48` indexelt vektorába ír 8 bájtos elemet
(`0x00421f10`–`0x00421f38`), a `0x00425f60` két hívóhelyéről
(`0x00427835`, `0x00427ec1`). Ez ugyanazt a vektorelrendezést és
normalizálót használja; a bináris RTTI nem nevezi meg a hívó és a film által
olvasott `+0x94` objektum azonosságát, ezért nem állítható, hogy a
`0x00425f60` bármely útja ugyanazt a példányt módosítja. A `0x00439a80` és `0x004860e0`
`+0x14d0` találatai más objektum-/vektorútvonalak; az offset-egyezés önmagában
nem azonosítja őket ennek a crop-táblának az íróiként.

**A crop-rect külön `.picasa.ini` parserútja.** A `.picasa.ini`-t említő
`0x006b52d0` a `0x0042a570`-et hívja (`0x006b576e`); ez a parser a
`width`, `height`, `rotate` és `rect64` kulcsokat kezeli (`0x00c80ac4`,
`0x00c80acc`, `0x00c80ad4`, `0x00c81460`), a `rect64(%I64x)` értéket
`0x00cd9554` formátummal olvassa, majd a `0x009b93f0` konverterrel
képpont-rectet állít elő (`0x0042a6b6`–`0x0042a707`). A hívó a négy
koordinátát a saját `+0x240…+0x24c` állapotába másolja
(`0x006b5796`–`0x006b57b6`). Ez független bizonyíték arra, hogy a crop
rect64-ből képpont-rect lesz; **a parser ezen hívása nem írja közvetlenül a
`+0x14d0` vektort**, és a teljes `.picasa.ini` parser → `+0x14d0` writer
példányszintű kapcsolat nincs bizonyítva.

**QEMU-mérés a crop-segédek geometriájára.** A harness a két bináris
segédfüggvényt közvetlenül futtatta; ezek egész koordinátás, szintetikus
bemenetű mérések, nem a teljes filmút futtatásai.

| bináris függvény | mérés | kimenet |
|---|---|---|
| `0x009b4960` metszés | `A=[-10,20,200,300]`, `B=[0,0,100,250]` | `[0,20,100,250]` |
| `0x009b4960` cáfoló eset | `A=[110,5,130,15]`, `B=[0,0,100,100]` | `[110,5,100,15]`; a helper a végpontokat metszi, de önmagában az üres téglalapot nem utasítja el vagy zsugorítja |
| `0x009b4c80` 90°-os lépés | határok `[0,0,640,480]`, rect `[10,20,110,120]`, lépésszám `1` | `[360,10,460,110]` |
| `0x009b4c80` 180° | ugyanaz, lépésszám `2` | `[530,360,630,460]` |
| `0x009b4c80` 270° | ugyanaz, lépésszám `3` | `[20,530,120,630]` |

A `0x009b4c80` egy lépéses utasításképlete:
`[height-y1, x0, height-y0, x1]`, ahol kezdetben
`width=bounds.x1-bounds.x0` és `height=bounds.y1-bounds.y0`; minden lépés
után felcseréli a `width` és `height` értékét (`0x009b4cb0`–`0x009b4cee`).
Így a következő lépés az előző szélességet használja magasságként. A
függvényt a crop-író `0x0042b000` forgatási ága hívja (`0x0042b0e2`); a
`0x0047a390` filmút viszont a `0x00430610` filter-/affin útját használja.
A QEMU-eredmény ezért a crop írósegéd forgatását igazolja, nem a teljes
filmszál filtereit; a filmhíd saját metszése közvetlenül az
`0x0047a3de`–`0x0047a419` utasításokban látható, nem ezt a QEMU-segédet hívja.

**Szem-landmark kapcsolatának határa.** A filmút a `0x00446610`
`facerect`-eredményét és a `0x00429dc0` crop-rectjét metszi. A
`0x0042b370` rectmutatót kap; a vizsgált íróutasításai nem olvassák a
`leye`/`reye` mezőket. Ettől független adatút, hogy a `0x0081fc30` a
`facerectdata` karakterláncból külön mezőkbe parsolja a `conf`, `pan`,
`leye`, `reye` és `mouth` adatokat (`0x00820c88`); ez a parser a
`0x00446610`-től külön kezeli őket. A két út azt támasztja alá, hogy a
film crop-olvasója és a crop-tábla írója közvetlenül nem használ
szemlandmarkot. Azt viszont nem dönti el, hogy a még fel nem oldott
`+0xa0` virtuális getter hogyan állítja elő a `0x00813c50`-nek adott
arctéglalapot; így a landmark közvetett hatása az arckiválasztásra nyitott.

**Bizonyítottság.** A táblához vezető olvasó/író híváslánc és a rect64
adatértelmezés utasításszintű, címzett binárislelet; önmagában ez
**feltételes**. A `0x009b4960` metszés és `0x009b4c80` forgatás képlete
utasításolvasással és ettől független QEMU-kimenettel egyezett, ezekre
**megerősített**. A QEMU nem hajtotta végre a táblát író hívókat vagy a
film teljes renderelését.



**A 0x38-as forrás arcrekord további mezői:** a `0x0081fc30` a
`"conf(%f),pan(%f),leye(%f,%f),reye(%f,%f),mouth(%f,%f)"` formátummal
olvassa az arc-részletadatot (`0x00820c88`). Ehhez a **forrás arcrekordhoz**
képest a `conf` a `+0x10` float mezőbe kerül, a `pan` `+0x14`-be, a két
szem és a száj koordinátái pedig `+0x18…+0x2c`-be. A loader a confidence
nullaságát vizsgálja, és az egyik ágon hívja a landmark-transzformálót
(`0x00820ca4`–`0x00820cc0`). A `0x00822230` a landmarkokat a kép geometriájához transzformálja
(`0x008222a9`–`0x008223ca`), és a betöltő további értékeket tesz a rekord
`+0x30/+0x34` mezőibe. **A klipíró a recttábla első négy dwordjét másolja**,
nem ezeket a landmark-mezőket; a clip-selector esetleges
landmark-felhasználása a renderútban nincs bizonyítva.

A gyökérmodell `+0x2c7` bájtja a `facemovie`, `+0x2c8` bájtja a
`removelowresfaces`, `+0x2c5` bájtja a `cropfit` értéke; a
`0x00816b00` ezeket a gyökérelembe írja. A `0x006175c0` a
`removelowresfaces` értéket ötödik paraméterként adja át a
`0x0081b800`-nak (`0x00617810`): az opció forrása a
`makemoviepanel/remove_low_res_faces` beállítás (`0x00617704`), panelbeli
bájtja `+0x359` (`0x0061778b`), és a modell `+0x2c8` mezőjébe is ez kerül
(`0x0061790a`). Ha az ötödik paraméter nem nulla, a `0x0081b800` meghívja
a `0x0081b150` szűrőt (`0x0081b8b2`–`0x0081b8b9`). A szűrő a
`+0x4e0` táblában levő képre több, `0xe0` lépésközű csoportot jár be;
csoportonként a négy `0x38`-as rekordot a `+0x00`, `+0x38`, `+0x70`,
`+0xa8` helyeken vizsgálja. Minden rectnél a pontos nyers feltétel:

| vizsgált rectmező | pontos feltétel | kimeneti maszkbájt |
|---|---|---|
| `dword[rect+8] - dword[rect]` | az egész szélességet floatként `136.5`-tel hasonlítja; ha `< 136.5` (egész szélességnél legfeljebb `136`) | `1` |
| `dword[rect+0x10]` | csak ha az előző feltétel nem teljesült; floatként `0.0`-val egyenlő | `1` |
| a fenti kettő közül egyik sem | szélesség `>= 136.5` és a `+0x10` float nem nulla | `0` |

A küszöb konstansa `0x00cf49f4`, binárisból kiolvasott IEEE-754
single értéke **136.5**; a `+0x10` mező a betöltő által beolvasott
`conf` confidence float.
A QEMU-harness a szűrőt közvetlenül hívta szintetikus rectrekordokkal:
`(136,1.0) → 1`, `(137,1.0) → 0`, `(137,0.0) → 1`,
`(136,0.0) → 1` (kimeneti hex: `01000101`). A diszasszemblálás és a
QEMU-mérés egyezik, ezért a küszöb és a maszkfeltétel
**megerősített**. A szűrőút önmagában nem nevezi meg a `+0x10` mezőt;
ettől függetlenül a modellbetöltő formátum-karakterlánca ezt `conf`
confidence értékként azonosítja.

Az arcfilm kimeneti felbontásának kulcsa és alapértéke a 2.8/b szerint
`facemakemovieres`, indexe `3`, alapértéke **1024×768**; a modell
`+0x2a8/+0x2ac` mezője adja át a szélességet/magasságot. Ez a kimeneti
felbontás, nem a forrás arctéglalap cropképlete.

Nyitott, blokkoló visszafejtési kérdések:

**A getter osztálya/slotjai és a klip-selector útja feloldva; a crop-tábla olvasása és írása részben nyitott.**
Az `AlignedImageCollection+0x94` célja `CThumbDB`; a
`+0x14d0`-beli per-index rect crop-olvasása és az alap-
`imagedata_facerect` recttel való metszése azonosított. A három vizsgált
közvetlen íróhívó közül a `0x00531c60` receiveréről most már bizonyított,
hogy ugyanaz a példány, de az egy Passport-ág; a másik két receiver
azonossága, a Film arcokból indításakor ténylegesen végrehajtott íróhívás,
valamint a klip selectorának és a konkrét `+0x14d0` bejegyzésnek a
futásidejű megfelelése **NINCS MEG**. A `0x00813c50` közvetlenül a getter
által visszaadott rect közepéhez igazít, és nem olvas `leye`/`reye`
landmarkot; a getter ismert útja sem olvassa közvetlenül a
`facerectdata` landmarkmezőit. A landmark közvetett szerepe a crop-tábla
feltöltésekor ettől még nyitott. Nyitott marad, hogy a `.picasa.ini`
`faces=` ág pontosan hogyan tölti az imagedata `facerect` oszlopát. A
`+0x4e0` filmmodell-tábla pixel-rectjeinek imagedata-olvasóig vezető
útja azonosított. A filmkeret alap-geometriája a kiválasztott felbontási
sorból ered; a getter által a képletnek visszaadott transzformált `Vw,Vh`
egy konkrét filmfutásban **NINCS MEG**.

**Cáfoló keresés a mezőeltolásos találatokra:** a `paszta.py` streaming
`.text`-pásztája talált `+0x18…+0x24` olvasót a `0x00819f50` címen, de az
`0x38`-as arcrekord landmark-floatjait transzformáló HOG-geometriai
segédfüggvény; hívója `0x00873cb0`, RTTI-je a
`HOGSimilarityComputer::vftable`-hez tartozik, nem a `0xf8` timeline-klip
bejárója. A `0x007fd8c0` jelölt `0xf8` lépést és `+0x18/+0x20` hivatkozást
is tartalmaz, de az időintervallum-rekord double mezőit olvassa. Mindkettő
hamis pozitív, ezért az offset-egyezés vagy a lépésköz önmagában nem
azonosítja a cropfogyasztót.

Ghidra-kör kell: 0x0049d560 - kösd össze a `.picasa.ini` `faces=` ágának
`rect64`-feldolgozását azzal az `imagedata_facerect` oszloppal, amelyet a
`0x00446610` olvas; döntsd el, hogy a `0x0049d560` parserút írja-e ezt az
oszlopot. [blokkoló]
**Válasz [részben] (#4400, 2026-10-18, 10. Ghidra-kör):** a `0x0047a390` (híd) a `0x00430610`-et a `0x0047a45c`-nél **nulla téglalappal** hívja: a `0x0047a43a-0x0047a44a` utasítások négy dwordot nullázva a verembe tesznek. A `0x00430610` szerint, ha `param_5 <= param_3` vagy `param_6 <= param_4` (C-dump: `if ((param_5 <= param_3) || (param_6 <= param_4))`; diszasszembly: `0x004306df-0x004306f1`), a téglalap a **teljes keret** lesz: `(0, 0, [param_2+0x10], [param_2+0x14])`. Tehát a híd által átadott téglalap a négy sarokra **nem hat**; a kimenet a teljes keret, és ezt kapja a `0x0090ff50` is. Bizonyítottsági fok: **megerősített** (Ghidra-C és capstone-diszasszembly, két eszköz, egyező eredmény). A `[param_2+0x10]`/`[+0x14]` értéke a híd `esp+0x30` blokkjából jön; ennek feltöltése nincs megnézve. Az `+0xa0` getter azonosítása (`0x0068f980`) nincs ebben a körben ellenőrizve: a törzse (136 bájt) a `this` vtábla `+0x60` slotját hívja, majd a hídnak adja a `this+0x94` mezőt, az eredményt és az `1` értéket. **Nyitott:** a `0x00430610` kimeneti objektumának (a C-dumpban `local_54`, a verem `[esp+0x10]`-tól) írási mérete; a 88 bájtos terület vége a `param_1` verem-argumentumnál van (`[esp+0x68]`). A spec korábbi `local_80` nevéhez nem találtam megfelelést a jelen dumpban.
Ghidra-kör kell: 0x00907cd0 - a `0x00430610` kimeneti objektumának (`local_54`, `[esp+0x10]`) írási mérete: ír-e 88 bájton túl, azaz a `param_1` verem-argumentumra [blokkoló]
Ghidra-kör kell: 0x0042c830 - a híd `esp+0x30` blokkjának feltöltése (a `+0x10`/`+0x14` mezők, amelyek a teljes keret méretét adják) [blokkoló]
Ghidra-kör kell: 0x009e0660 - határozd meg a `model+0x2e0` keret-getterének transzformációs feltételeit és a `0x00813c50`-nek ténylegesen átadott `Vw,Vh` értékeket az arcfilm alapútján. [blokkoló]
- **NINCS MEG:** a `.picasa.ini faces=` → `imagedata_facerect` betöltési
  kapcsolat; a film indításakor ténylegesen hívott `+0x14d0` író és a
  kiválasztott selectorhoz tartozó bejegyzés; a landmark esetleges
  upstream szerepe; a `rotate`/`filters` út pontos numerikus hatása; a
  getter transzformált `Vw,Vh` értéke egy konkrét filmfutásban; valamint
  az eredeti paneltől a kész filmkockáig tartó élő viselkedésmérés. Az
  íróhívás példányszintű rögzítéséhez QEMU-harness call-trace kell; a
  teljes kép-render-export eredményhez a #4426 lépéssora kellene, de a
  Wine alatti eredeti program ezt a funkciót nem támogatja.

**Bizonyítottsági határ:** a klipmezők nyers másolása, a low-res maszk
képlete és a `0x00813c50` cropképlete megerősített: utasításszintű
dekódolásukhoz független QEMU-kimenet egyezik. A getterek RTTI/vtable-
felbontása, a selectorlista indexelése, a `+0x94` receiverazonosság és a
`+0xa0` út metszés→forgatás→filter→affin sorrendje megerősített a
vtable-adat/RTTI, a külön adatfolyamok, a célzott disassembly és a friss
kontextusú újralevezetés alapján. A klip `+0x8` → staging `+0x8` másolása
utasításszinten bizonyított. Az `imagedata_facerect` közvetlen alapforrás
nem bizonyítja a `.picasa.ini faces=` eredetét; a film-selectorhoz tartozó
élő `+0x14d0`-bejegyzés sincs megfigyelve. A landmarkok közvetlen hiányzó
olvasása csak a vizsgált láncra vonatkozó feltételes negatív állítás. A
`faces=`-től az imagedata oszlopig tartó forrásút, a transzformációk
numerikus hatása, a futásidejű keretméret és a teljes videókocka-renderelés
továbbra is nyitott.

**A getterek C-kódja - #4400, 8. kör (2026-10-17).**

**Kérdés.** A 7. kör három C-kódot kért: `0x0049d560`, `0x00430610` és `0x009e0660`. Három kérdésre kellett válasz: (a) milyen transzformációt végez a `0x00430610` a négy sarokra, és milyen mezőkből; (b) a `0x009e0660` milyen feltételek mellett ad más keretméretet, és mit kap a `0x00813c50` `Vw,Vh`-ként; (c) mi a `0x0049d560` szerepe a láncban. A 7. kör a `0x00430610`-t a film `+0xa0` getterének filter-transzformációjaként nevezte meg. Az 5. és 6. kör szerint a getter a `0x0068f980` (vtable-slot `+0xa0`). Ez a `0x0047a390` hidat hívja, a `0x00430610` pedig a híd filter-segédje (hívás: `0x0047a45c`). A C ezt megerősíti, lásd (a).

**Forrás.** `referencia/ghidra/2026-10-17-film-2.txt`: a három függvény C-kódja, hívói és hívottjai. A `0x0047a390`, `0x00813330`, `0x00a4a240`, `0x00a4a520`, `0x0090ff50`, `0x00907cd0`, `0x0069f510` és `0x0045a9d0` törzse nincs a fájlban. Az alábbi állítások ezért a látott C-re vonatkoznak.

**Eredmények.**

*(a) A `0x00430610` szűrő-segéd. Nincs benne affín transzformáció a négy sarokra.*

- Bemenet: `param_1` (objektum; a `+0x31f4` alatt keresi a `filters` kulcsot), `param_2` (objektum; `+0x30` a szűrt mező, `+0x8`/`+0xc` a méret, `+0x10`/`+0x14` a visszaállító téglalap határa), és a téglalap `param_3..param_6`: `[x0, y0, x1, y1]`, négy egész. Nem sarokpontok.
- Kimenet: csak a státusz (`iVar1`). A téglalap nem jut vissza a hívónak.
- Lépések a C szerint:
  1. `param_2 == 0` esetén `4`. Ha a `FUN_00430540` nullától eltérő értéket ad, a függvény azt adja vissza.
  2. Szálzár a helyi `FilterArray` körül.
  3. `FUN_0069f510(param_1+0x31f4, "filters")`. Ha ez nem nulla, a téglalap-blokk akkor is lefut, a szűrő nem.
  4. Ha a lookup nulla, a `FUN_00907cd0` a `FilterArray`-t és a `param_2+0x30` mezőt kapja, méretekkel `param_2+0x8` és `+0xc`. Ha ez nem nulla, a téglalap-blokk kimarad.
  5. Téglalap-blokk: üres téglalapnál (`x1 <= x0` vagy `y1 <= y0`) a téglalap `[0, 0, param_2+0x10, param_2+0x14]` lesz. Utána `FUN_0090ff50(&téglalap)`.
- Metszés: valódi metszés nincs a C-ben. Csak az üres-téglalap visszaállítás látszik.
- Forgatás: nincs a függvényben.
- Filter: van (3-4. lépés). A hatása NINCS MEG.
- Affín: nincs a függvényben. A spec szerint az affín transzformáció a `0x00a4a240`-hez köthető, a film-hídban, a filter után (`0x0047a41c`-`0x0047a470`; az 5. kör szerint itt affín leképezés épül). A 7. kör `0x0047a46c` címe ennek a hívásnak a helye lehet. Ezt a `0x0047a390` C-je dönti el.
- A filmút sorrendje a spec szerint: metszés → forgatás → filter (`0x00430610`) → affín (`0x00a4a240`). A C a filter-lépést és a `filters` kulcsot megerősíti. A többi lépés csak a spec szerint van meg.
- A `0x0090ff50` az egyetlen téglalap-művelet. Ha az affín a `0x00a4a240`, a `0x0090ff50` valószínűleg nem affín. Ez feltételes.
- Ha a `0x0090ff50` nem ír globális területre, a szűrő-lépés nem módosítja a hívó téglalapját.
- Nem film-specifikus: kilenc kódhívása van. A crop-író `0x0042b000` kétszer hívja (`0x0042b13d`, `0x0042b32f`); a híd hívása (`0x0047a45c`) csak egy a kilencből. Ez új tény.
- Nincs DATA (vtable) hivatkozás rá. A 2.5 szakasz korábbi „filter-/affin útja" megnevezése ezért pontosítandó: a `0x00430610`-ben csak szűrő van.

*(b) A `0x009e0660` ytDrawNode `+0x20` getter (`__thiscall`; `this` = `param_1`, kimenet = `param_2`, második bemenet = `param_3`).*

- Csak adatreferencia mutat rá: 44 DATA-hivatkozás, kódhívás nincs. A `0x00cda8ec` a `0x00cda8cc + 0x20` vtable-helyen áll, ez egyezik a spec vptr-jével. A slot-hely megerősített (xref-adat és a spec utasításolvasata). Az osztályazonosítás (ytDrawNode) RTTI-alapú, ez egy út: feltételes.
- Nulla téglalap (`[0,0,0,0]`): ha `[this+0x20f] == 0`, és (`[this+0x190] <= [this+0x188]` vagy `[this+0x194] <= [this+0x18c]`). A `this+0x188..+0x194` a csomópont saját `[x0, y0, x1, y1]` téglalapja. Ha a jelzőbájt nem nulla, ez az ellenőrzés kimarad.
- Egyébként a kimenet négy dword másolata: `FUN_00a4a520()`, ha `[param_3+0x24] == 0`, különben `FUN_00a4a240(param_3)`.
- A getter törzse nem transzformál: másol, és forrást választ. A `param_3` a `0x00a4a240`-nek megy. Mivel az affín transzformáció a spec szerint a `0x00a4a240`-hez köthető, a nem nulla bájt ága transzformált téglalapot adhat. Ez egy út: feltételes.
- Más keretméretet tehát két eset ad: a nulla téglalap, és a `0x00a4a240` ága. A `0x00a4a520` ágának forrása NINCS MEG.
- Mit kap a `0x00813c50` `Vw,Vh`-ként: a C ezt nem mondja meg. A 7. kör utasításolvasata szerint a `0x00813330` a visszaadott téglalap `x1-x0` és `y1-y0` értékét adja tovább. Ez egy út: feltételes. A `0x00813330` C-je kell.
- Nulla téglalapnál `Vw = Vh = 0`. A spec szerint ezek a `0x00813c50` képletének nevezőjében vannak. Hogy a `0x00813330` kezeli-e ezt, NINCS MEG.

*(c) A `0x0049d560` a `faces=` tételek parser-je, pixel-rekordokba.*

- Egyetlen hívója a `0x0045a9d0` (`0045b8f7`). A kulcsnév (`faces`) nincs a C-ben. A spec szerint a `.picasa.ini` útjáról hívódik.
- Bemenet: `;`-vel elválasztott tételek, tételenként két `,`-vel elválasztott mező. Az első mező `rect64(%I64x)` alakú. A második mező nincs felhasználva. A `rect64` olvasás és a `0x009b93f0` konverter használata egyezik a 7. kör `0x0042a570` olvasatával: két út, megerősített.
- Kimenet: a `*param_1` tömb 32 bájtos rekordjai (nyolc dword). Az első hat dword a `local_24`: ebből az első négy a képpont-téglalap, az 5-6. a C szerint nullázva. Utána a `local_c` két dwordja (`_DAT_00c7ccf8`).
- A tömb minden híváskor felszabadul és üresre áll. A bit0 jelző a törlésen túl megmarad. A C-ben nincs olyan utasítás, ami bit0-t beállítana. Ha be van állítva, az első érvényes arcnál a függvény `4`-gyel kilép.
- Hibás tétel: kimarad, a függvény nem áll meg. Hibák: nem `rect64`; a `FUN_009b9190` nem nulla; a konverter nem nulla; `x1 <= x0` vagy `y1 <= y0`; a `FUN_0092c450` nem nulla.
- Visszatérési érték: `-1`, ha a határ üres (`param_1[2..5]`); `4`, ha a lista zárt, vagy foglalási hiba van; egyébként `0`.
- Képhatár: a `0x0049d560` törzsében nincs metszés; a határ csak az üres-ellenőrzésben szerepel. A metszés a konverterben van (a spec korábbi, QEMU-val mért olvasata): `x0` a `[0, w-1]`, `x1` az `[1, w]` közé szorul.
- A konverter argumentum nélkül hívódik. A spec szerint a kép szélességét és magasságát és a rect64 értéket kapja. Ezek forrása NINCS MEG. A `param_1[2..5]` határ egy lehetséges forrás, bizonyíték nélkül.
- Az `imagedata_facerect`: a `0x00446610` rect64 (u64) mezőt olvas a spec szerint. A `0x0049d560` pixel-rekordot ír. Ha az oszlop rect64 marad, ez a lista nem a közvetlen író, hacsak a hívó vissza nem kódolja. Ezt a `0x0045a9d0` dönti el.

**Bizonyítottsági fok.**

- Megerősített (két út egyezik):
  - A `0x00430610` nem a `+0xa0` getter. A C-ben nincs DATA-hivatkozás, a getter vtable-ből jön; a spec szerint a getter a `0x0068f980`, a `0x0047a390` pedig a híd.
  - A `0x00430610`-ben nincs affín transzformáció a négy sarokra. A C-ben nincs affín-kód; a spec szerint az affín a `0x00a4a240`-hez köthető.
  - A `0x00430610` a `filters` kulcsot keresi: a C-literál és a spec (`0x00c80b04`) egyezik.
  - A `0x009e0660` a `0x00cda8cc` vtable `+0x20` slotja: xref-adat és spec-olvasat.
  - A `0x0049d560` `rect64` olvasása és a `0x009b93f0` konverter használata egyezik a 7. kör `0x0042a570` olvasatával.
- Feltételes (egy útra épül):
  - a `0x009e0660` nulla-ága (C);
  - a `0x009e0660` kimenete nem a saját téglalap (C);
  - a `0x00a4a240` ágának affín jellege (spec, a C csak a hívást mutatja);
  - a `Vw,Vh` a visszaadott téglalap mérete (7. kör, utasításolvasata);
  - a szűrő-lépés nem módosítja a hívó téglalapját (C, a `0x0090ff50` törzse nélkül);
  - a `0x0049d560` listája nem az imagedata-oszlop írója (C és a formátum-eltérés);
  - a `0x0049d560` törzse nem metsz (C);
  - a `0x00430610` nem film-specifikus (hívólista, egy forrás).

**Cáfoló kísérletek.**

1. *A `0x00430610` mint `+0xa0` getter.* A getter vtable-ből érkezik, a `0x00430610`-nek nincs DATA-hivatkozása. A cáfolat sikerült.
2. *A `0x0090ff50` mint négy sarokra ható affín.* A `0x0090ff50` egy téglalapot kap, nem sarokpontokat, az affín pedig a spec szerint a `0x00a4a240`. A cáfolat részben sikerült: affínként nincs alátámasztva, de a törzse hiányzik.
3. *A `0x00430610` visszaadja a téglalapot.* Nincs kimeneti téglalap, csak `iVar1`. A cáfolat sikerült a C szintjén; a globális írás lehetősége a `0x0090ff50`-től függ.
4. *A `0x0049d560` metsz a kép határára.* A törzsben nincs metszés, a metszés a konverterben van. A cáfolat részleges: a metszés nem ebben a függvényben van.
5. *A `0x0049d560` az imagedata-oszlopba ír.* A rekord pixel-rekord, az oszlop a spec szerint rect64. A cáfolat részleges: a hívó visszakódolhatja.
6. *A `0x009e0660` alap-méretnél nulla keretet ad.* A spec szerint a csomópont téglalapja `[0,0,W,H]` (7. kör). W és H pozitív esetén a nulla-ág nem fut, feltéve, hogy ez a téglalap a `+0x188..+0x194` mezőbe kerül. A visszaadott téglalap szélessége és magassága (W, H) még nincs igazolva.

**NINCS MEG (8. kör után).**

- A `faces=` lista célja (`0x0045a9d0` dönti el). A `0x0049d560` önmagában nem ír imagedata-oszlopot.
- A bit0 jelző beállítója.
- A `0x009b93f0` konverter implicit bemenetei (rect64 érték, kép-méret).
- A `0x00430610` szűrő-hatása a képre (`0x00907cd0`): képi, nem geometriai.
- A `0x0090ff50` hatása a téglalapra.
- A `0x0047a390` teljes törzse (metszés, forgatás, affín hívás címe: `0x0047a46c`?), és a `0x0047a4a0` (hívás: `0x0047a576`) szerepe.
- A `0x00a4a240` és a `0x00a4a520` törzse, így a `0x009e0660` visszaadott téglalapjának forrása.
- A `Vw,Vh` képzése és a nulla téglalap kezelése (`0x00813330`).
- Zárva a C szerint: a `0x0049d560` második mezőjének sorsa (nem olvassa), és a `0x00430610` négy sarokra ható affínja (nincs benne).
- Változatlan: a `0x00813c50` kapott `Vw,Vh` értéke egy konkrét filmfutásban; a landmark upstream szerepe; a `+0x14d0` író és a selector bejegyzés; a rotate/filter numerikus hatása; az élő viselkedésmérés.

**Válasz [részben] (#4400, 2026-10-18):** a híd (`0x0047a390`, 261 bájt, diszasszembly) lépéssora: (1) `0x0047a3aa`: `call 0x446610`; (2) ha a 2. stack-argumentum alsó bájtja nulla, `0x0047a487`-nél 0-val tér vissza, és nem ír kimenetet (`0x0047a3b1-0x0047a3b8`); (3) `call 0x429dc0` (`0x0047a3d5`): ha igaz, a kimeneti téglalap (`[esi..esi+0xc]`) metszete a `0x429dc0` által adott téglalappal: bal és felső szél = max, jobb és alsó szél = min (`0x0047a3de-0x0047a419`); (4) `call 0x42c830` és `call 0x4147d0`; (5) `call 0x430610` (`0x0047a45c`, nulla téglalappal, lásd fent); (6) **`call 0x00a4a240` a `0x0047a46c`-nél**: a spec `?`-jelölt affin hívás címe **megerősítve**; az eredményt a kimenetbe másolja (`0x0047a471-0x0047a484`). Bizonyítottsági fok: a lépéssor **megerősített** (diszasszembly; a C-dump nincs). A `+0x14d0` metszés és a `rotate` hívás azonosítása **NINCS MEG**: a `0x00429dc0` forrása nincs megnézve. A `0x0068f980` (`+0xa0` getter) a `this+0x94` mezőt és a vtábla `+0x60` hívásának eredményét adja át a hídnak.
Ghidra-kör kell: 0x00429dc0 - a híd metszőtéglalapjának forrása: a `+0x14d0` rekord-e, és mit ad vissza a bool [blokkoló]
Ghidra-kör kell: 0x00446610 - a híd első hívása (`0x0047a3aa`): mit ír a metszés bemeneti objektumába [nem blokkoló]

**Válasz (#4400, 2026-10-18, bizonyított):** a `0x0090ff50` **nem módosítja** a téglalapot. A törzs a téglalapot csak olvassa (`[ebp+0]`, `[ebp+4]`, `[ebp+8]`, `[ebp+0xc]`): szélesség = x1-x0, magasság = y1-y0 (`0x00910232-0x00910252`), és a `[ebp+*]` célú tárolás a törzsben nincs. **Globális területre közvetlenül nem ír**: a tárolásai a veremre (`[esp+*]`) és a `this`-re mennek. A `this` = `edi` = a hívó `param_2+0x58` alobjektuma; a `0x009e6340` ezen írja a `[eax+8]` és `[eax+0x14]` mezőket (`0x009e634f`, `0x009e6358`). A film-objektum `+0x30` alobjektumát (`0x009e6340` második operandusa) olvassa, a forgatás és tükrözés a `[esi+0x28]` és `[esi+0x2c]` bitjeitől függ, a szög egész-többszörös `π/2`. PE-olvasású konstansok: `0xcf4760` = 1,5707963267948966; `0xc72150` = 0,5; `0xcf3ed0` = -1,0; `0xcf39e4` = 2^32. Bizonyítottsági fok: **megerősített** a téglalap-olvasásra és a közvetlen globális írás hiányára (diszasszembly; a `0x00430610` C-hívása `FUN_0090ff50(&param_3)`, a `0x0090ff50` C-dumpja nincs a 2026-10-18-i dumpban). **Nyitott** (helyi diszasszemblálással még nem zárva): a `0x00c29d20` és `0x00c285f0` (79-79 bájtos burkolók, belül `0x00c14398`) írásai; a globális írás kizárása csak a `0x0090ff50` közvetlen törzsére áll.

Ghidra-kör kell: 0x00813330 - a `Vw,Vh` képzése a `0x009e0660` visszaadott téglalapjából, és a nulla téglalap kezelése. [blokkoló]

Ghidra-kör kell: 0x00a4a240 - a `[param_3+0x24] != 0` ág: az affín transzformáció bemenete és kimenete. [blokkoló]

Ghidra-kör kell: 0x00a4a520 - a `[param_3+0x24] == 0` ág forrása: a csomópont saját téglalapja, vagy más. [blokkoló]

Ghidra-kör kell: 0x0045a9d0 - az egyetlen hívó: hova kerül a `0x0049d560` tömbje (imagedata-oszlop, vagy más), és mi állítja a bit0 jelzőt. [blokkoló]

Nem blokkoló további címek: `0x00907cd0` (a szűrő képi hatása), `0x0069f510` (a `filters` lookup visszatérési jelentése), `0x009b93f0` (a konverter implicit bemenete).

A 7. kör „Következő célzott Ghidra-kör" listája (`0x0049d560`, `0x00430610`, `0x009e0660`) ezzel lezárult: mindhárom C megvan. A lezáráshoz a fenti hat cím kell.

**A film-getterek hídja - #4400, 9. kör (2026-10-17).**

**Kérdés.** A 8. kör hat blokkoló címe: a híd (`0x0047a390`) metszése, forgatása, filtere és affín transzformációja; a `0x0090ff50` művelete; a `Vw,Vh` képzése (`0x00813330`); az affín ág bemenete és kimenete (`0x00a4a240`); a `0x00a4a520` ág forrása; és a `0x0049d560` tömbjének helye (`0x0045a9d0` hívja). Ahol a C nem dönt, kimondjuk, mi hiányzik.

**Forrás.** `referencia/ghidra/2026-10-17-film-hog-kor.txt`, a hat `CÍM` szakasz. A sorhivatkozások ennek a fájlnak a sorai. A `0x00c29cca` és a `0x00c0b310` szakaszt nem használtuk, mert a #4194-hez tartoznak. A `0x00446610`, `0x00429dc0`, `0x0042c830`, `0x004147d0`, `0x00430610`, `0x00812aa0`, `0x00813c50`, `0x0049d560`, `0x0049c2b0` és `0x004841f0` törzse ebben a fájlban nincs. A `0x00430610` működését a 8. kör összefoglalójából vettük át, újra nem olvastuk. A `0x00c72150` (0,5) konstans a korábbi .rdata-olvasatból való. A `0x00cf4160` a spec egy másik szakasza szerint 0,499; ezt ebben a körben nem ellenőriztük.

**Eredmények.**

*(a) A híd (`0x0047a390`).* A `+0xa0` getter (`0x0068f980`) hívja, a spec szerint 1 jelzővel. A kimenet négy dword, az ESI-ben. Lépések a C szerint:

1. `0x00446610` az alap-rectet az ESI-be írja (29. sor).
2. Jelző nélkül a híd itt véget ér (30. sor).
3. Metszés: `0x00429dc0` crop-rectet ad. Ha sikeres, x0 és y0 a maximum, x1 és y1 a minimum (35-57. sor). Üres-ellenőrzés nincs.
4. `0x0042c830(param_2, &local_84, 0)` (59. sor). A `local_84` a kimeneti címe. A 2.5 szakasz korábbi olvasata szerint ez a `rotate` mező. A C később nem olvassa a `local_84`-et. A rect nem megy be ebbe a hívásba, ezért ez nem rect-forgatás.
5. `0x004147d0()` (60. sor). Argumentum nélkül. A hatása NINCS MEG.
6. `0x00430610(param_1, local_80, 0, 0, 0, 0)` (61. sor): szűrő. A rect nulla. A `local_80` a hívás előtt nincs feltöltve. A visszatérési értéket nem használják. A 8. kör szerint a nulla rect a `local_80` +0x10/+0x14 mezőit használná határnak.
7. `0x00a4a240(local_28)` (62. sor): affín befoglaló téglalap. A négy dword az ESI-be kerül (63-66. sor), és **felülírja** a metszett értéket.

Ebből következik: a metszés csak akkor hat a végső rectre, ha a `0x00a4a240` bemenete (EDX) az ESI-ről érkezik. A C ezt nem mutatja.

*(b) A `0x0090ff50`.* Nincs argumentuma. Az ESI-objektum mezőit olvassa: +0x18, +0x1c, +0x20, +0x24, +0x28, +0x2c. Ha x0 < x1 és y0 < y1, hív egy `0x009e6340` függvényt. A többi ág csak hívásokat tesz (`0x009e6340`, `0x00c29d20`, `0x00c285f0`). Közvetlen írás az objektumba nincs. Négy hívója van (`0x00430610`, `0x00430790`, `0x00463cd0`, `0x006ab020`), ezért nem film-specifikus. Mivel +0x18-tól olvas, ha az ESI a négy dwordos helyi téglalapra mutat, ezek az olvasások a téglalapon kívül esnek.

*(c) A `Vw,Vh` (`0x00813330`).* A `model+0x2e0` ytDrawNode getterétől (vtable +0x20) kapott rectet a `local_1a8` helyre írja (207. sor). Utána (244-245. sor):
`0x00812aa0(this, this+0x1a8, this+0x7ec, local_1a8 - iStack_1b0, iStack_1a4 - iStack_1ac, 0)`.
A pár tehát a `0x00812aa0`-nak megy, feltétel nélkül, a korai kilépések után. A `0x00813c50` a `this+0x28c == 0x14` ágon fut (248. sor), argumentum nélkül. Nulla-kezelés a C-ben nincs.

*(d) Az affín ág (`0x00a4a240`).* `__fastcall`: ECX = kimeneti négy egész, EDX = bemeneti rect (x0, y0, x1, y1), a veremben hat float mátrix (m0-m5).

- Sarkok: x' = m0·x + m1·y + m2, y' = m3·x + m4·y + m5 (428-439. sor).
- Befoglaló téglalap: min x, min y, max x, max y. Minden értékből `ROUND(érték - C)`, ahol `C = 0x00cf4160` (484-487. sor).
- Kimenet: `[minX, minY, maxX, maxY]`. A visszatérési érték az ECX.
- A `0x0047a390` hívásában (62. sor) csak az ECX (`local_28`) látszik. Az EDX és a verem-argumentum forrása NINCS MEG.
- Hívók: 52, köztük a crop-író `0x0042b000` (`0x0042b342`) és a `0x009e0660` getter. Nem film-specifikus.

*(e) A `0x00a4a520`* (a `0x009e0660` getter 0 jelzőjű ága). ECX = bemeneti rect, EAX = mátrix, ESI = kimenet. A rectet mindkét irányban `0,5`-tel kitágítja (530-538. sor). A sarkokat ugyanazzal a mátrix-képlettel transzformálja. A C csak a maximumot számolja (maxX, maxY; 543-560. sor). A négy kimeneti egész forrása NINCS MEG: a C négy `0x00c29990` hívást mutat, az értékeik nem látszanak. Hívók: 11.

*(f) A `0x0049d560` tömbje (`0x0045a9d0`).*

- Kép-méret: a `0x0042a440` adja, ha a jelző be van kapcsolva és a hívás sikeres. Egyébként a `+0xd4` vtable-hívás (1176-1179. sor). Ha a méret nulla, nincs írás.
- A-ág (1181-1244. sor): az A-slot (`local_f4`) rekordjait a `0x0049d560` tölti (1191. sor). Ez az ág fut, ha a B-slot hiányzik vagy érvénytelen, vagy nincs ini-mutató (`+0x2c5c`).
- B-ág (1245-1397. sor): érvényes B-slot és ini-mutató esetén a `0x0049c2b0` tömbjéből 32 bájtos rekordok épülnek, ini-olvasással (`0x00586040`, `0x005835d0`).
- Mindkét ágban a feldolgozott tömb a `0x004841f0(this, &tömb, 0)` hívásba megy (1236. és 1384. sor). Ez a tárolás. A célja NINCS MEG.
- Az A-ágban, ha van ini-mutató, a rekordok 4-5. dword-jét a `0x00587110` kapja a `.picasa.ini` objektummal (1223-1231. sor). A 8. kör szerint a `0x0049d560` nullázza ezt a két dword-öt. Ha ez igaz, minden rekord (0, 0) párt kap.
- Bit0: az A-ágban a `uStack_b0` csak `>> 1` alakban olvasódik (1192. sor). A bit0-t ez a függvény nem állítja be. A beállító a `0x0049d560` vagy a `0x0049c2b0` törzsében lehet. Ezek nincsenek a fájlban.
- A `0x0045a9d0` hívója egy: `0x0047e470` (`0047e77e`).

**Bizonyítottsági fok.**

- Megerősített (a C-ből közvetlenül látszik):
  - A híd hívássorrendje: alap-rect, metszés, `0x0042c830`, `0x004147d0`, `0x00430610`, `0x00a4a240`. A kimenet a `0x00a4a240` pointere.
  - A metszés komponensenként max és min.
  - A `0x0042c830` nem kap rectet. A `local_84` a C-ben később nincs olvasva.
  - A `0x00430610` visszatérési értékét a híd nem használja.
  - A `0x0090ff50` nem ír közvetlenül az ESI-objektumba. Nem film-specifikus.
  - A `0x00a4a240` befoglaló téglalapot számol, és a kimenet sorrendje.
  - A `0x00a4a520` csak maximumot számol.
  - A `0x0045a9d0` két ágra oszlik, és mindkettő a `0x004841f0`-nak ad tömböt.
  - A `Vw,Vh`-jellegű pár a `0x00812aa0`-nak megy.
- Feltételes (egy útra épül):
  - A metszés hatása a végső rectre (az EDX = ESI feltevés).
  - A mátrix forrása a forgatás-értékből.
  - A `0x00587110` (0, 0) párja: a 8. kör nullázási állításától függ.

**Cáfoló kísérletek.**

1. *A metszés adja a végső rectet.* Részben cáfolva: a `0x00a4a240` kimenete felülírja az ESI-t (63-66. sor).
2. *A `0x0042c830` forgatja a rectet.* Cáfolva: a rect nem megy be a hívásba.
3. *A `0x0090ff50` módosítja a téglalapot.* Cáfolva: nincs közvetlen írás az objektumba. A hívott függvények hatása NINCS MEG.
4. *A `0x00430610` ad vissza téglalapot.* Cáfolva: a visszatérési értéket nem használják.
5. *A `Vw,Vh` a getter rectjének x1-x0 és y1-y0 értéke.* Nem igazolt. A C más kifejezést mutat, és a kivonandók (`iStack_1b0`, `iStack_1ac`) nincsenek beállítva.
6. *A `0x00a4a520` is befoglaló téglalapot számol.* Cáfolva a C-ben: csak maximum látszik.
7. *A `0x0049d560` tömbje az imagedata-oszlopba megy.* Nem cáfolható és nem igazolható: a tárolás a `0x004841f0`-n át megy, amelynek törzse hiányzik.

Korábbi állítások javítása:

8. A 8. kör `0x0047a4a0` hívása `0x0047a576`-nál van. A C szerint a `0x00a4a240` hívása `0x0047a58b`-nél áll.
9. A 7. kör szerinti „forgatási segéd” a `0x0047a429`-nél: a C-ben a forgatási helyen a `0x0042c830` áll, ami a `rotate` értéket olvassa. Rect-t nem forgat.
10. A 7. kör szerinti x1-x0 és y1-y0 a `0x00813c50`-nek: a C szerint a pár a `0x00812aa0`-nak megy. A `0x00813c50` argumentum nélkül hívódik.
11. A 8. kör szerint „a getter törzse nem transzformál”: ez a getter saját kódjára igaz. A `0x00a4a520` ága viszont transzformál.
12. A 8. kör `FUN_0090ff50(&téglalap)` állítása: a függvény az ESI-objektum +0x18 mezőitől olvas.

**Ghidra-kör kell (9. kör):**

- Ghidra-kör kell: 0x004841f0 - a `0x0045a9d0` tömbjének tárolója: hova ír (imagedata-oszlop vagy más). [blokkoló]
- Ghidra-kör kell: 0x00812aa0 - a `0x00813330` 4-5. argumentumának (`Vw,Vh`-jellegű pár) felhasználása, és a nulla téglalap kezelése. [blokkoló]
- Célzott utasításolvasat kell, nem hívólista: 0x0047a3f0-0x0047a46c - az EDX és a verem-argumentum beállítása a `0x00a4a240` hívás előtt, és a `local_84` (forgatás-érték) felhasználása. [blokkoló]

**Következtetés a további hívólistákról.** A 9. kör nem kér újabb hívót. A hívólisták megvannak: `0x0047a390` (1 hívó), `0x0090ff50` (4), `0x00a4a240` (52), `0x00a4a520` (11), `0x0045a9d0` (1). Egy újabb hívó a fenti eredményt nem változtatja meg. A maradékot ezek döntik el:

- **Natív QEMU-mérés** a `0x0068f980` → `0x0047a390` láncon, ismert facerect, crop-rect, rotate-érték és mátrix bemenettel. Ez dönti el: (1) hat-e a metszés a végső rectre, (2) hogyan hat a rotate-érték a kimenetre, (3) a `0x00812aa0` előtti `Vw,Vh` számértéke.
- **Colab-felvétel** (eredeti Picasa 3.9, Wine alatt). Ez a `.picasa.ini` `faces=` és `crop` kulcsainak valódi írását mutatja, ha a kiváltó művelet Wine alatt lefut. A teljes film-render Wine alatt nem támogatott (a 7. kör szerint), ezért a keretméretre nem dönt.

**Fejlesztési következmény.** Nincs. A cropképlet és a keretméret együtt még nem írható le megvalósítható formában. A `Vw,Vh` képzése hiányzik, a híd mátrixa és bemenete nincs a C-ben, és a metszés hatása a végső rectre nem látszik.

**NINCS MEG (9. kör után).**

- A `0x00a4a240` mátrixának (verem-argumentum) és bemeneti rectjének (EDX) forrása a `0x0047a46c` hívásnál.
- A metszés hatása a végső rectre (az EDX = ESI feltevés).
- A forgatás-érték (`local_84`) felhasználása: a mátrixban van-e, és hogyan.
- A `0x00430610` szűrő képi hatása (`0x00907cd0`), és a `local_80` tartalma a hívás előtt.
- A `0x0090ff50` mellékhatásai (`0x009e6340`, `0x00c29d20`, `0x00c285f0`), és az ESI-objektum azonosítása.
- A `Vw,Vh`-pár felhasználása a `0x00812aa0`-ban, és a nulla téglalap kezelése.
- A `0x00a4a520` négy kimeneti egészének forrása (a min-értékek és a `0x00c29990` hívások).
- A `0x0045a9d0` tömbjének tárolója (`0x004841f0`), és hogy ez imagedata-oszlop-e.
- A bit0 jelző beállítója (`0x0049d560` vagy `0x0049c2b0`).
- A kép-méret (`local_e4`, `local_e0`) átadása a `0x0049d560`-nak és a konverternek.
- A kép-méretet adó `0x0042a440` és a `+0xd4` vtable-hívás: melyik adja.
- A `0x0045a9d0` kiváltó lánca (`0x0047e470` és feljebb), és a B-slot forrása.

**A film-tároló és a Vw,Vh - #4400, 10. kör (2026-10-17).**

**Kérdés.** A 9. kör két blokkoló címe: `0x004841f0` (a `0x0045a9d0` tömbjének tárolója) és `0x00812aa0` (a `Vw,Vh`-jellegű pár felhasználása). Mindkettőre a 9. kör kérdését kell megválaszolni a C-kódból. A kérdés: a híd metszése, forgatása, filtere és affin transzformációja; a `0x0090ff50` téglalap-művelete; a `Vw,Vh` képzése (`0x00813330`); az affin ág bemenete és kimenete (`0x00a4a240`); a `0x0049d560` tömbjének helye. Ahol a C nem dönt, ki kell mondani, mi hiányzik.

**Forrás.** `referencia/ghidra/2026-10-17-film-tarolo.txt` (a privát `picasapy-agent` repóban): a két `CÍM` szakasz; a sorhivatkozások ennek a sorai. Emellett a 9. kör fájlja, `referencia/ghidra/2026-10-17-film-hog-kor.txt`: a `0x00813330` getter-hívása (207. sor), a `Vw,Vh` képlete és a `0x00812aa0` hívása (244-245. sor), a `0x0045a9d0` hívóhelyei (1191, 1226, 1236, 1384. sor). A 8. kör fájlja, `referencia/ghidra/2026-10-17-film-2.txt`: a `0x0049d560` eleje és a `local_24` írói. A `0x0047a390`, `0x0090ff50`, `0x00a4a240` és `0x00a4a520` törzse ebben a körben nem szerepelt, ezért az ezekre vonatkozó állítások a 9. körből maradnak.

**Eredmények.**

*(a) A `0x004841f0`: a rekordtömb feldolgozója.*

- Hívók: három. Kettő a `0x0045a9d0`-ban (`0045b85c`, `0045ba5c`), egy a `0x00644900`-ban (`00644b94`). A `0x00644900` C-je nincs meg.
- A `0x0045a9d0` két helyen hívja: `FUN_004841f0(param_1, &iStack_b4, 0)` (1236. sor) és `FUN_004841f0(param_1, &ppuStack_d0, 0)` (1384. sor). Az `iStack_b4` a `0x0049d560` kimeneti listája (1191. sor). A `ppuStack_d0` a `0x00587110` kimeneti címe (1226. sor).
- Hívási alak: a törzs a 3. argumentumot (`param_3`) már a 77. sorban olvassa (`param_3[1]`), a hívás viszont 0-t ad. A 2. argumentum egyszerre lista és objektum: a 140. sor ciklushatára `param_2[1] >> 1`, a 66. sor viszont `param_2[0xb17]`-et olvas (ez a `0x0045a9d0` `this+0x2c5c` ini-mutatója). A dekompilált prototípus és a hívás nem illeszkedik. A lista argumentuma a C-ből nem dönthető el.
- Rekord: a törzs a rekord +0x10 és +0x14 szavát olvassa (83-84. sor), és a kettőt együtt kezeli. A +0 ... +0xc pixel-téglalapot nem olvassa.
- Párok: `(-1, -1)` külön ágat indít (85-96. sor). `(0, 0)` esetén az egész ág kimarad (97. sor). Egyébként `FUN_005863f0` keres (100. sor). Ha nincs találat, `FUN_00476460` vagy `FUN_00412440` próbálkozik (121, 130. sor). A talált indexet `FUN_004844f0(*puVar8, index, param_3)` kapja (125, 130-132. sor).
- Ismeretlen személy: ha nincs találat, a név részeként a `CThumbDB::UnknownPerson` sztring szerepel (69-74. és 104-118. sor).
- Bit0: a 0x004841f0 nem állítja be. A 93. sorban csak egy helyi változó bit0-ját maszkolja. A `0x0049d560` elején csak megőrzi (`param_1[1] & 1`).
- Írás: a törzs közvetlenül nem ír a rekordba. A rekord módosítása, ha van, a `FUN_004844f0`-ban lehet.

*(b) A `0x00812aa0`: a Vw,Vh fogadója.*

- Paraméterek: `param_1` a hívó objektum (`this`); `param_2` a tétel (`this+0x1a8`), a típusa `*param_2`: 2, 3 vagy 4; `param_3` a kimeneti objektum (`this+0x7ec`, +8 a szélesség, +0xc a magasság); `param_4` = Vw; `param_5` = Vh; `param_6` a jelző. A 0x00813330 hívásában a jelző 0.
- Hívók: hat. A 0x00813330 hívása (`00813588`) feltétel nélkül fut a 244-245. sorban.
- A Vw,Vh használata a C-ben:
  1. Ha a kimeneti objektum mérete (+8, +0xc) nem egyezik Vw,Vh-val, `FUN_009a9c90(param_3)` fut (267-268. sor). Törzse nincs meg.
  2. Típus 3 vagy 4: a képszolgáltató (`this+0x2d8`, vtable +0x5c) kapja Vw,Vh-t (304-306, 323-325. sor). A visszakapott kép méretét összeveti Vw,Vh-val (310-311. sor). Eltérésnél munkát sorol (318. sor).
  3. Típus 4 és jelző 0: a 289-298. sor nem használja a Vw,Vh-t. Színnel tölt (`0xffaaaaaa`), vagy egy objektum vtable +0x28 hívását végzi, és 0-val tér vissza.
  4. Típus 2: nincs képszolgáltató-hívás. A kitöltés színe `param_2[1]` (465-467. sor).
  5. Kimeneti téglalap: ha `local_10c == Vw` és `local_108 == Vh` (498. sor), akkor x1 - x0 = local_10c, y1 - y0 = local_108. Egyébként (505-518. sor) mind a négy érték -1, és a kitöltés 0xff000000 (fekete).
  6. Jelző nem nulla: a 478-492. sor `ROUND(Vh * FUN_0080c510() / this[0x2ac])` értéket ad a `this+0x564` objektum vtable +8 hívásának. A 0x00813330 ezt nem használja.
- Nulla-kezelés: nincs. A C-ben nincs Vw = 0 vagy Vh = 0 elágazás, és az osztónál (`this[0x2ac]`) sincs nullavizsgálat. A 0 értéket a képszolgáltató kapja.

*(c) A `Vw,Vh` képzése (`0x00813330`).*

- A getter (vtable +0x20, a `*(this+0x2e0)` objektumon) a `&local_1a8` kimeneti területre ír (207. sor). A `0x00812aa0` hívás első két argumentuma: `local_1a8 - iStack_1b0` és `iStack_1a4 - iStack_1ac` (244-245. sor).
- Helyesbítés a 9. körhöz: ott az állt, hogy a kivonandók nincsenek beállítva. A C-ben valóban nincs értékadásuk, de a getter a címen keresztül ír. Az `iStack_1ac` és az `iStack_1b0` a négy dwordos kimeneti területen belül vannak, ezért a getter írhatja őket.
- A képlet szerint Vw = `out[0] - out[2]`, Vh = `iStack_1a4 - out[1]` (az `out` a getter kimenete `local_1a8`-tól). Ha az `out` mezői [x0, y0, x1, y1] lennének, a Vw negatív szélesség lenne, a Vh első tagja pedig a kimeneten kívül esne. A kivonás értelme ezért nem igazolt.

*(d) A 9. kör kérdéseinek állapota a két címből.*

- Híd metszése, forgatása, filtere, affin transzformációja: nem szerepelt a két címben. NINCS MEG.
- `0x0090ff50`: nincs új adat.
- `Vw,Vh` képzése: a forrás pontosítva (c), a kivonás értelme nincs megadva.
- Affin ág (`0x00a4a240`) bemenete és kimenete: nincs új adat.
- `0x0049d560` tömbjének helye: a `&iStack_b4` lista a `0x004841f0` hívásába megy. A C alapján ez nem közvetlen pixel-oszlop-író; a végső cél a `FUN_004844f0`-ban lehet, és az nincs meg.

**Bizonyítottsági fok.**

- Megerősített (a C-ből közvetlenül):
  - A `0x0049d560` listája (`&iStack_b4`) a `0x004841f0` hívásába megy (hog 1191, 1236. sor).
  - A `0x004841f0` a rekord +0x10/+0x14 szavát olvassa, a pixel-téglalapot nem (83-84. sor).
  - `(0, 0)` párnál a `0x004841f0` kihagy minden tételt (97. sor).
  - A `0x004841f0` nem állítja be a bit0-t.
  - A dekompilált prototípus és a hívás ellentmond egymásnak: a 3. argumentum a hívásban 0, a törzs mégis dereferálja (77. sor).
  - A `0x00812aa0` a Vw,Vh-t a képszolgáltató kért méreteként és a kimeneti méret ellenőrzésében használja (267-268, 304-306, 310-311, 323-325. sor).
  - A `0x00813330` a `0x00812aa0`-t feltétel nélkül hívja, jelző 0-val (244-245. sor).
  - A `0x0049d560` tételenként nullázza a `local_24[4]` és `local_24[5]` mezőket (film-2, 66-67. sor), és a 8. kör fájljában nincs további írás rájuk.
- Feltételes:
  - A `(0, 0)` pár a rekordban marad a `0x004841f0` hívásáig. Ehhez a `0x0049d560` másoló-ágának törzse kellene (film-2, 144. sor: `piVar9 = local_24`).
  - Ha a pár nulla, a `0x0045a9d0` `0x00587110`-hívása is (0, 0) párral fut (hog 1226. sor). Ez a C alapján nem tűnik szándékoltnak; a másoló törzse dönti el.
  - Ha a `local_10c` és `local_108` 0 marad, a `0x00812aa0` egyezés-ága (498. sor) csak Vw = Vh = 0 esetén fut. Ez feltételes, mert a `&local_114`-et kapó hívások (`FUN_009a91a0`, `FUN_009a8ca0`, `FUN_009a9c90`) felülírhatják a két változót.

**Cáfoló kísérletek.**

1. *A `0x004841f0` pixel-oszlopba ír.* Részben cáfolva: a törzsben nincs írás a +0 ... +0xc mezőkbe. A `FUN_004844f0` törzse nincs meg, ott lehet a tényleges írás.
2. *A `0x004841f0` a faces= rect64-et olvassa.* Cáfolva: a törzs a +0x10/+0x14 párt olvassa, a pixel-téglalapot nem.
3. *A `Vw,Vh` a film-keret mérete.* Nem igazolt: a `0x00812aa0` a kért képméretként használja. Hogy ez a film-keret is, a `0x00813330` képzésén múlik, és az nincs igazolva.
4. *A `Vw,Vh` nulla értéke adja az egyezés-ágat.* Nem igazolt (lásd a feltételes pontot).
5. *A `0x00813330` kivonandói nincsenek beállítva (9. kör).* Cáfolva: a getter a kimeneti területen belül írja őket.

**Korábbi állítások javítása.**

- A 9. körben a `0x004841f0(this, &tömb, 0)` hívás szövege helyes, de a „tömb" azonosítása nem igazolt (lásd a hívási alak ellentmondását).
- A 9. körben „a kivonandók nincsenek beállítva" nem pontos (c).
- A 9. körben „a `0x0049d560` tömbjének célját a `0x004841f0` dönti el" csak félig igaz: a `0x004841f0` a pár-keresést és a `FUN_004844f0` hívását tartalmazza; a cél a `FUN_004844f0`-ban van.

**NINCS MEG (10. kör után).**

- A `0x004841f0` belépési alakja: melyik argumentum a lista, és mit jelent a 3. argumentum (0 a hívásban).
- A `puStack_7c` (rekordonkénti dword-tömb) forrása: a C-ben nincs hozzárendelés.
- A `FUN_004844f0` törzse: a talált index és a lista hogyan kerül a rekordba.
- A `0x0049d560` másoló-ágának törzse (film-2, 144. sor), vagyis a rekord-pár végső értéke.
- A `0x00587110` kimenete (`ppuStack_d0`) és a `local_10c` (hog 1226. sor): mit tartalmaznak.
- A bit0-t beállító függvény.
- `FUN_009a9c90`, `FUN_009a91a0`, `FUN_009a8ca0`, `FUN_009aabf0` törzse: a kimeneti méret és a -1 értékek jelentése, és a `local_10c`, `local_108` írói.
- A típus (`this+0x1a8`: 2, 3, 4) jelentése.
- A képszolgáltató (`this+0x2d8`, vtable +0x5c) visszaadott méretének forrása.
- A `0x009e0660` getter kimenetének mezőjelentése, és így a Vw,Vh képlet értelme.
- A `0x0090ff50` hatása; a híd metszése, forgatása, filtere; az affin mátrix és EDX-bemenet forrása (`0x0047a3f0-0x0047a46c`): változatlanul a 9. körből.
- A `0x00a4a520` négy kimeneti egészének forrása: változatlan.

**Következtetés a további kérésekről.** Ez a kör nem kér újabb hívólistát: a `0x004841f0` három, a `0x00812aa0` hat hívója már megvan. A maradék belépési és futásidejű kérdés: a hívási alak, a rekord-pár értéke, a Vw,Vh és a híd mátrixa. Ezt natív QEMU-mérés dönti el, a korábbi (4-5. körös) QEMU-mérés módján. A `0x0068f980` → `0x0047a390` láncot kell futtatni ismert facerect, crop-rect, rotate-érték és mátrix-bemenettel, és ki kell olvasni:

- a `0x0047a58b` (affin hívás) előtt az EDX és a verem-argumentumok értékét;
- a `0x00812aa0` belépésén a `param_4`, `param_5` (Vw, Vh) és a `param_6` értékét;
- a `0x004841f0` belépésén az ECX-et, a két stack-argumentumot, és a rekord +0x10/+0x14 párját.

A Colab-felvétel (eredeti Picasa 3.9, Wine alatt) a `faces=` és a crop-kulcsok eredetét mutatja, a keretméretre nem dönt (a 9. kör szerint).

**Fejlesztési következmény.** Nincs. A cropképlet és a keretméret még nem írható le megvalósítható formában: a `Vw,Vh` értelme, a híd mátrixa és a `0x004841f0` belépési alakja nincs igazolva.

Az aktuális PicasaPy People-film útja a személyalbumok fotóinak rendezett
forrás-URL-jeit adja át (`Main.qml:728–734`,
`people_controller.py:81–89`, `index/people.py:170–198`). A
`CreateDialogs.qml:502–517,712–735` ezeket a normál
`exportMovie` útvonalon használja; a `create_controller.py:553–629`
teljes képfájl-forrásokra épülő `MxfForras` rekordokat készít, és nem
állít be `facemovie` vagy `facerect*` értékeket (`movie/mxf.py:82–86,120`:
az arcmezők alapértéke 0, a `facemovie` alapértéke hamis). A klip tehát
nem arcra vágott forrásból készül; az általános `cropfit` ettől még
működhet, de arcazonosítót/arckivágást nem ad át. A paritási összesítést
és a fejlesztői elfogadási feltételeket lásd a `paritas-ellenorzes.md`
#4339 szakaszában.

A #4331 „Kijelölésben lévő arcokból” belépője a `personMovieMode` állapotot
bekapcsolja és az arcfilm felbontásindexét állítja be
(`CreateDialogs.qml:41-47`), de az exporthívás csak a képek URL-jeit, a
méretet és az általános filmopciókat adja át (`CreateDialogs.qml:1011-1037`,
`create_controller.py:880-919`). A `MovieSettings` nem hordoz arcfilm- vagy
face-selector mezőt (`movie/slideshow.py:54-82`); az export a képeket a
`prepare_photo_frame` teljes képes cropfit/letterbox útján dolgozza fel
(`movie/slideshow.py:605-625`). Ez statikus kódáttekintés: nem mért
kimeneti paritás. A #4331 jelen állapotában tehát a menüpont és a méretmód
megvan, a #4400 szerinti arckivágás még nincs bekötve.

**A film-crop lánc lezárása: a híd, a Vw/Vh-pár és a konstansok - #4400, 11. kör (2026-10-18).**

*(A kör sorszáma 11: a 6-10. kör már a fenti szakaszokban van. A 10. kör végén kért Ghidra-kérdések egy része itt asm-szinten megválaszolódott.)*

**Kérdés.** (1) Melyik a három közvetlen író közül (`0x00531c60`, `0x006b0200`, `0x006b39b0`) az, amelyik a film `AlignedImageCollection+0x94` objektumát (`CThumbDB`) írja, és fut-e a film indításakor? (2) A klip rajzolásakor a `facerect`-ből hogyan lesz a végső kivágás: milyen szorzók és konstansok, címmel és kiolvasott értékkel?

**Forrás.** Kizárólag a helyi bináris: diszasszembly (`annot_disasm.py`), a `.rdata` konstansai a PE-ből (csak olvasás), és a hívási gráf a bináris-indexből (`xrefs`). Dekompilátumot nem használtam. A 7-10. kör állításait nem vettem át gépiesen: ahol a friss asm mást mutatott, ott javítom.

**Eredmények.**

*(a) Javítás: a `0x00813c50` argumentumokkal hívódik.* A 9. kör „argumentum nélkül" állítása az asm szerint téves (egy út, lásd (i)). A hívási hely (`0x008135bf`-`0x008135c7`): `push edx` (Vh), `push eax` (Vw), `push ebx` (this), `mov eax, esi` (a tétel-rekord), `edi` a kimeneti négy dword (`lea edi,[esp+0x54]`). A prológus a verembe tolt értékeket veszi át: `ebx` = Vw (`0x00813c5a`, `[esp+0x70]`), `ebp` = Vh (`0x00813c77`, `[esp+0x78]`). A hívás csak `this+0x28c == 0x14` esetén fut (`0x00813593`).

*(b) Vw és Vh: a ytDrawNode-téglalap szélessége és magassága.* A `0x00813330` a `0x009e0660` getterét hívja (a `this+0x2e0` objektum vtábla `+0x20` slotján, `0x008133d6`). A getter négy dwordot ír a `[E+0x58]` címre (a `lea ecx,[esp+0x5c]` a `push eax` után fut, ezért a cím +0x58). Ebből:
- Vh = out[3] - out[1] = y1 - y0 (`[esp+0x64]-[esp+0x5c]`),
- Vw = out[2] - out[0] = x1 - x0 (`[esp+0x60]-[esp+0x58]`).
Mindkét ágban ugyanez áll (`0x0081356b`-`0x00813577` a `0x00812aa0` hívás előtt, `0x008135ac`-`0x008135ba` a `0x00813c50` hívás előtt). A 10. kör „Vw = out[0] - out[2]" olvasata téves volt; a kivonás előjele a szokásos. Feltétel: a getter-hívás és a `0x0081356b` közötti esp-egyensúly nincs soronként végigolvasva.

*(c) A híd (`0x0047a390`) sorrendje, argumentumokkal.*
- Argumentumok (a `0x0068f980` hívása, `0x0068f9a5`-`0x0068f9c3`): arg1 = `CThumbDB` (`[esi+0x94]`), arg2 = a 0-tól számozott elem-index (a `+0x60` slot visszatérése, `eax`), arg3 = jelző = 1 (`push 1`).
- Alap-téglalap: `0x00446610(CThumbDB, elem-index, esi)`; a 3. argumentum a `push esi` (a `0x00446610` `ret 0xc`-vel vesz le három argumentumot). A négy dword az `imagedata_facerect`-ből kerül az `esi`-be (a 8. kör C-je szerint; a `0x00446610` törzsét ebben a körben nem olvastam újra).
- Metszés (`0x0047a3be`-`0x0047a419`): `0x00429dc0(CThumbDB, elem-index, &crop)`. Sikeres hívásnál `x0 = max(x0, cx0)`, `y0 = max(y0, cy0)`, `x1 = min(x1, cx1)`, `y1 = min(y1, cy1)`, az `esi` négy mezőjébe. Ha a hívás nullát ad (`0x0047a3da`), az alap-téglalap marad. Üres-ellenőrzés nincs.
- Forgatás (`0x0047a41c`-`0x0047a429`): `0x0042c830(this = CThumbDB, elem-index, &rot, 0)`; a `rotate` a `[esp+0x1c]` dword-ba kerül (javítva 2026-10-18: a `[esp+0x20]` a `0x0047a42e` által átadott objektum kezdete, lásd a 3168. sort).
- Szűrő (`0x0047a45a`-`0x0047a45c`): `0x00430610`, a négy rect-argumentum nulla. A visszatérési értékét a híd nem használja, és a `[esp+0x30]` tömböt a híd később nem olvassa.
- Affin (`0x0047a466`-`0x0047a46c`): **EDX = esi**, vagyis az affin bemenete a METSZETT rect. ECX = négy egész kimenet (`lea ecx,[esp+0x10]`), a verembe a 6 floatos mátrix címe kerül (`lea ecx,[esp+0x78]`, `0x0047a461`). A visszatérő mutatót a híd EAX-ből olvassa (`0x0047a471`), és `0x0047a473`-`0x0047a484` visszamásolja az `esi`-be. (A 9. kör a visszatérést ECX-ként írta; ezt a `0x00a4a240` végén nem ellenőriztem.)

→ Következmény: a metszés hatása a végső rectre **feltételes**. Egy út (az asm) mutatja az EDX = esi-t; a 9. kör C-je nem mutatja, ezért második úttal (pl. QEMU) kell megerősíteni. Ha igaz, a híd végső rectje: `befoglaló(M · metszett rect)`, ahol M a 6 floatos mátrix, amelynek forrása NINCS MEG.

*(d) Kerekítés, és két névleg azonos konstans.* A `0x00a4a4a3`-`0x00a4a4ff` sorokban `fsub qword [0x00cf4160]` és `fistp` váltja: `ROUND(érték - C)`, ahol a kiolvasott `C` = **0.499** (double, bájtok `560e2db29defdf3f`). Ez lezárja a 9. kör „0,499?" kérdőjelét. ⚠️ A crop-képlet `δ`-ja (`0x00cf48f8`, bájtok `000000c09defdf3f`) **nem** ugyanaz: float32(0.499), kiterjesztve double-lé, értéke 0.49900001287460327. Két külön konstans; a megvalósításban nem cserélhetők fel.

*(e) A `0x00813c50` konstansai, a PE-ből kiolvasva.*

| cím | típus | kiolvasott érték | szerep (asm-hely) |
|---|---|---|---|
| `0x00cf48f8` | double | 0.49900001287460327 | δ, `fld qword` (`0x00813d60`, `0x00813dee`) |
| `0x00cf39e4` | float | 4294967296.0 (2^32) | tízszer `fadd` (`0x00813d5a`-`0x00813e4b`); szerepe NEM ellenőrzött |
| `0x00c7e4a4` | float | 4.0 | r > 4 elágazás (`0x00813fef`) |
| `0x00cf39f8` | double | 3.0 | `z = r / 3.0` (`0x00814007`, `fdiv qword`) |
| `0x00c7e4ac` | float | 1.2999999523162842 | `z` felső korlátja (`0x00814016`) |
| `0x00c72150` | double | 0.5 | `fld qword` (`0x00814030`); a félméret-számításban, pontos szerep nincs igazolva |
| `0x00cf3ed0` | float | -1.0 | belépő `fld` (`0x00813c53`, `0x0081358d`); szerepe feltételes |

A z-ágak sorrendje egyezik a 4. kör képletével: `r > 4`: `z = r/3`; egyébként `z = min(r, 1.2999999523162842)`. A kör konstansai bináris eredetűek; a `0x00813c50` `δ`-ja és a 4. kör képlete egyezik.

*(f) A `0x00cf39e4` (2^32) szerepe NINCS MEG.* A tízszeri `fadd` valószínűleg egész-kivonási/kerekítési trükk, de ezt a `0x00813d5a` környékén végig kell olvasni; ebben a körben nem tettem.

*(g) Az 1. kérdés: a három író és a film.* Az indexből, csak közvetlen `call` élekkel, mélység 6-ig felfelé járva:
- `0x006b0200`: 8 elérhető függvény; közvetlen hívói `0x00531c60`, `0x005d4b60`, `0x005f3ee0`.
- `0x006b39b0`: 13 elérhető függvény; közvetlen hívója `0x006abae0`.
- `0x00531c60`: 1 elérhető függvény; közvetlen hívója `0x005cb990`.
A film-belépők (`0x00824090`, `0x006999c0`, `0x0068c880`, `0x00402f90`, `0x00619010`, `0x00616940`, `0x00813330`, `0x0068f980`, `0x0047a390`, `0x00813c50`) közül egyik sem érhető el. ⚠️ Ez **pozitív élekből** nem negatív állítás: az index nem látja a vtábla-hívásokat (`binaris-regeszet-modszertan.md`, 14. szakasz). A film-idejű hívás kizárásához indextől független pásztázás kellene; ezt nem végeztem el. Ezért a kérdés NYITOTT.
A receiverek: a `0x00531c60` receivere a `CThumbDB` (7. kör, változatlan), de Passport-ágban fut. A `0x006b0200` és a `0x006b39b0` receivere (`EDI+0x0c`) továbbra sincs a `CThumbDB`-hez kötve.

*(h) Cáfoló kísérletek (15.2).*
1. „A `0x00813c50` argumentum nélkül hívódik" (9. kör): **cáfolva** (hívási hely és prológus).
2. „`Vw = out[0] - out[2]`" (10. kör): **cáfolva** (előjel; a helyes: Vw = out[2] - out[0]).
3. „A metszés nem hat a végső rectre, mert az affin felülírja az `esi`-t": **cáfolva**, az affin bemenete (EDX) az `esi`, vagyis a metszett rect.
4. „A `0x00430610` szűrő módosítja a rectet": **nincs bizonyíték** rá. A rect-argumentumai nullák, a visszatérési értéke és a `[esp+0x30]` tömb nincs felhasználva a híd további részében.
5. „A `Vw,Vh` a keret mérete": **feltételes**. A getter rectjének mérete; keret akkor, ha a csomópont rectje `[0,0,W,H]` és a jelző 0 (8. kör).

*(i) Bizonyítottsági fok.*
- **Megerősített** (két út egyezik): a híd sorrendje és argumentumai (9. kör C-je és az asm); a metszés max/min képlete (8. kör C-je és az asm); a `ROUND(érték - 0.499)` kerekítés (9. kör C-je és az asm); a konstansok értékei (PE-olvasás) és használatuk címe (asm).
- **Feltételes** (egy út, az asm): a `0x00813c50` argumentumai (a 9. kör C-je más hívási alakot adott, lásd (a)); Vw és Vh a getter kimenetének két különbsége és az előjelük; az affin EDX-bemenete a metszett rect; az esp-egyensúly a Vw/Vh-olvasás előtt; a `0x00cf39e4` szerepe (nincs út); a `0x00a4a240` visszatérő mutatója (EAX vagy ECX).
- **Nyitott**: a 6 floatos mátrix forrása; a `rotate` hatása a mátrixra; a film-idejű író.

*(j) Válasz a két kérdésre.*
1. A film `+0x94` objektuma a `CThumbDB` (`0x0068f9a5`; a 6. kör két útja szerint megerősített). Hogy a három író közül melyik fut a film indításakor: **NYITOTT**.
2. A kivágás lépései: alaprect (`imagedata_facerect`) → metszés a `+0x14d0` crop-rectjével (`max`/`min`) → rotate-olvasás → szűrő (eredménye nélkül) → affin befoglaló M szerint → kerekítés `-0.499`-cel. A cropképlet (`s`, `z`, margó) változatlan (2.5, 4. kör), és a konstansai most mind bináris eredetűek. A rotate → M kapcsolat és M forrása **NINCS MEG**.

*(k) A #4331-hez.* A jegytörzs-bővítés még nem írható. Az M (6 float) forrása és a rotate-érték hatása hiányzik. A metszés-láncra és a Vw és Vh értékére van már bizonyíték, de egy valódi filmfutáshoz az M kell.

Válasz [megerősített, két út; 2026-10-18]: a `0x0042c830` a rotate értéket a hívó **`[esp+0x1c]`** dword-jába írja (nem `[esp+0x20]`-ba). Asm-út: a `0x0047a41c` `push ebx` után a `lea ecx,[esp+0x20]` (`0x0047a41d`) már a `esp-4`-hez képest számol, így a kimeneti mutató `E0+0x1c` (E0: a hívás előtti `esp`). C-út (a film-hog dump hídja): a `local_84` (= `E0+0x1c`) és a `local_80` (= `E0+0x20`) egymás után áll, és a `local_84` a `0x0042c830` argumentumán kívül nincs olvasva. A `0x0042c830` nem ír a mátrixba (C: csak `*param_3`). **Nincs memóriakapcsolat a rotate és a 6 floatos mátrix között**: a rotate-dword a hívás után nem olvasódik sem a híd törzsében, sem a `0x00430610` vagy a `0x00a4a240` argumentumában.

Válasz [a rotate-hatásra megerősített; a mátrix-identitás feltételes; 2026-10-18]: a `0x0047a42e` `lea eax,[esp+0x20]` után a `0x004147d0`-t hívja, tehát `EAX` = `E0+0x20`, a `local_80` objektum (nem a rotate). A `0x004147d0` (sima `ret`, 106 bájt) ezt az objektumot alapértelmezettre írja: nullák; `1.0` a `+0x30`, `+0x40`, `+0x50`, `+0x58`, `+0x68`, `+0x78` mezőkön; `1` bájt a `+0x54` és `+0x7c` helyen. A rotate-dword (`E0+0x1c`) a reset kezdete előtt van, a reset **nem írja felül**. Hatás a rotate-ra: nincs. Hatás a mátrixra: a 6 floatos mátrix (`+0x58`..`+0x6c` = `E0+0x78`..`E0+0x8c`) **identitás**: `[1, 0, 0; 0, 1, 0]`. Feltétel: a `0x00430610` szűrő kimenete a `local_80` (88 bájt, a C szerint), ami a mátrix címe (`E0+0x78`) előtt végződik; ezt nem olvastam végig, ezért feltételes. C-út: `FUN_004147d0()` a `local_80` után, a mátrix a C-ben a `local_28` (`FUN_00a4a240(local_28)`).

Válasz [megerősített, C és asm; 2026-10-18]: a `0x00a4a240` `__fastcall`, `ret 4`: ECX = a négy egész típusú kimenet, EDX = a bemeneti rect `[x0, y0, x1, y1]`, a verem egyetlen argumentuma a 6 floatos mátrix címe. A mátrix sorfolytonos 2×3: `X' = m0·x + m1·y + m2`, `Y' = m3·x + m4·y + m5` (az `m2` és `m5` az eltolás). A 4 sarokpont képe után a befoglaló téglalap min/max értékei, a kimenet `[minX, minY, maxX, maxY]`, mindegyik `ROUND(érték - c)`-vel, ahol `c` a `0x00cf4160` double-értéke (0.499). A C `(float)` konverziót mutat, az asm `fsub qword`-öt; a két konverzió különbsége ~1e-8, a kerekítési határ átbillenését nem vizsgáltam. **Visszatérés:** a C `return param_1` (ECX), tehát EAX = ECX; a híd `mov edx, [eax]` (`0x0047a471`) ezt használja. Az „EAX vagy ECX" kérdés így eldőlt: EAX = ECX. A 9. kör ECX-ként írt olvasatát helyesbítem. Megjegyzés: a 3121. sor `lea ecx,[esp+0x10]` a `push ecx` után áll, ezért a kimenet a `E0+0x0c`..`E0+0x1b`; a `E0+0x1c` rotate-dword ettől szabad.

Nem Ghidra-kérdés, a következő körben: a film-idejű író (pásztázás, indextől független, lásd (g)); a `0x00cf39e4` szerepe (`0x00813d5a` környéke).

**A film-crop lánc: a 12. kör (2026-10-19, #4400): a `0x00907cd0`, a `0x0042c830` és a `0x00429dc0` válasza, és a híd `esp+0x30` blokkja.**

*Forrás:* `.ghidra11/2026-10-19-ghidra-11.txt` (C-törzsek és hívólisták); a `Picasa3.exe` helyi diszasszemblálása (`annot_disasm.py`: `0x00430610` 378 bájt, `0x0047a390` 261 bájt, `0x0042c830` 335 bájt, `0x004147d0` 106 bájt); a `.rdata` és a double-olvasat (`pefile`, nem kódsor).

*(a) `0x00907cd0`: a kimeneti írás mérete.* A `0x00430610` `0x004306cb` sorában `lea edx,[ebp+0x30]` áll, és a `0x004306d4` hívás második argumentuma ez a cím. A `0x00907cd0` **10 dword-öt (40 bájtot)** ír ide (C: a `*param_2 = *puVar4` ciklus, tíz iteráció), tehát a `+0x30`-`+0x57` tartományt, és a `+0x58` (88) határnál véget ér. **Nem ír a 88 bájton túl.** Az írt értékek: `1.0` a `+0x30`, `+0x40`, `+0x50` mezőn, `0` a `+0x34`-`+0x3c` és `+0x44`-`+0x4c` mezőn, `1` bájt a `+0x54`-en. Ez egyezik a `0x004147d0` alapértékes töltésével (`fst [eax+0x30]`, `[eax+0x40]`, `[eax+0x50]` = 1.0; `mov byte [eax+0x54], cl`, `cl` = 1): a két út (a reset-rutin asm-je és a `0x00907cd0` C-je) ugyanazt adja.
- A `0x00907cd0` többi írása a verem (`local_f4`, `local_cc`), illetve a zárolt állapot az első argumentumon (`param_1`, a `0x00430610` verem-lokálisa), nem az objektumban. A lista-elemek vtbl `+0x74`/`+0x78` hívásainak törzsét nem olvastam (a dump nem tartalmazza).
- **Feltétel:** a hívás nem feltétel nélküli. A `0x004306bd` `test eax,eax` / `jne 0x4306df` átugorja a `0x907cd0` hívást, ha a `0x0069f510(…, "filters")` nem nulla. A `+0x30`-`+0x57` tehát csak akkor íródik, ha a `filters` keresés `0`-t ad. A `0x0069f510` visszatérésének jelentése a 12. kör alatt van (részben megválaszolva).

*(b) `0x0042c830`: NEM tölti a `esp+0x30` blokkot.* A függvény (`__thiscall`, a `this` = ECX = `CThumbDB`) memóriaírása egyetlen 4 bájtos hely: `*param_3` (`mov [eax],0` a `0x0042c848`-nál, `mov [esi],edx` a `0x0042c93c`-nél). A többi írás a veremre (a sztring-mutató, `[esp+0x14]`) és a `this+0x1470` zárobjektumra megy. A híd `0x0047a429` hívása a `&rot = E0+0x1c` címre mutat (lásd a 11. kört), tehát a `0x0042c830` nem ír W-t vagy H-t.
- A C-kód `else` ágában a `FUN_005c2100()` hívás kimenete hiányzik. Az asm (`0x0042c8af`: `lea eax,[esp+0x14]`, `call 0x5c2100`) megmutatja: a sztring-mutatót a `0x005c2100` írja a `[esp+0x14]`-be, a `this+0x58` lista `[+0x48]` tömbjének `index`-edik elemétől. Ez a `rotate(%d)` sztring forrása a tartományon belüli indexre.

*(c) W és H: a blokk nullázódik, a híd nem ír Vw/Vh-t.* A `0x0047a42e` `lea eax,[esp+0x20]` után a `0x0047a432` `call 0x4147d0` az `E0+0x20` objektumot nullázza (`mov [eax+0x0..0x2c], ecx`, `ecx` = 0). Ez ugyanaz a cím, mint a `0x0047a454` `lea edx,[esp+0x30]` (a `sub esp,0x10` a `lea` előtt áll, a `0x0047a437`-nél). Így **W = `[O+0x8]` = 0 és H = `[O+0xc]` = 0**. A híd utasításai között nincs más írás erre a blokkra (a `[esp+0x38]` / `[esp+0x3c]` írása hiányzik).
- A `0x00430610` ezt a blokkot `ebp`-ként kapja (`0x00430615`: `mov ebp,[esp+0x64]` a `push`-ok után, a második argumentum). Olvassa: `[ebp+0x8]` és `[ebp+0xc]` a `0x907cd0` argumentumaként (`0x004306c1`-`0x004306c4`), `[ebp+0x10]` és `[ebp+0x14]` a rect-alapként (`0x004306f3`-`0x004306f6`). Ezek mind nullák. **(W,H) = (0, 0), bináris (0x004147d0).**
- Pontosítás a 3120. és 3154. sorhoz: a híd nem olvassa a `[esp+0x30]` blokkot, de a `0x00430610` igen, az `ebp` argumentumon át. A nulla W,H a reset eredménye, nem a híd írása.

*(d) `0x00429dc0`: a metszőtéglalap forrása NEM a `+0x14d0`.* A kimenet négy dword (a híd `[esp+0xc]`-`[esp+0x18]`, a híd előre nullázza ezt a területet a `0x0047a3c5`-`0x0047a3d1` soron). A két 16 bites pár az `uVar13` (`[0]`, `[1]`) és az `uVar11` (`[2]`, `[3]`) felbontása.
- **Forrás:** a `this+0x1528` lista (elem: `[+0x48] + index*8`, darabszám: `[+0x4c] >> 1`). Ha nincs lista, vagy az index túl nagy, az alapérték a `this+0x1530` és `this+0x1534`. Mindkettő a `this`-en belül van, nem a `+0x14d0`-ban.
- A `this+0x14d0` a listát védő zárobjektum (`piVar14`): a `this+0x14dc` jelzőtől függően vtbl `+0x18` vagy `EnterCriticalSection(this+0x14f8)`, és a későbbi listaágú zárolás argumentuma (`local_10`). Nem rect-mező.
- **Nyitott:** a nem üres ágban a `this+0x48` objektum vtbl `+0xd4` hívása (C: `(param_2, &local_24, &param_1)`) a második rect-forrás (az elem metszete). A `+0xd4` célja NINCS MEG (vtbl-hívás, a dump nem tartalmazza).

*Bizonyítottsági fok.* (a) **feltételes**: a méret (40 bájt, `+0x30`-`+0x57`) asm és C szerint megerősített, a `0x0069f510` feltétel nyitott, ezért a tényleges írás nem dőlt el. (b) **megerősített**: asm szerint egyetlen rect-író (`*param_3`). (c) **megerősített**: W = H = 0 (reset-asm, a híd nem ír, a `0x00430610` olvasása asm-ben), két úton: a `0x004147d0` asm-je és a híd `0x0047a432`-`0x0047a45c` hívássora, amely a `0x00430610`-nek ugyanezt a blokkot adja. (d) **megerősített**, hogy a `+0x14d0` nem rect-mező; a nem üres ág `+0xd4` része **nyitott**.

*Cáfoló kísérlet.* (c) azt feltételeztem, hogy a W,H a `0x0042c830` kimenete: cáfolva, mert a függvény asm-je csak `*param_3`-at ír. (d) azt feltételeztem, hogy a `+0x14d0` a rect-forrás: a C-ben csak zár és argumentum, cáfolva a dump alapján.

*Fejlesztési következmény.* Nincs új teendő a bizonyított részből. A `0x0069f510` feltétele nélkül a `+0x30`-`+0x57` írás nem zárható le.

- **A `"filters"` keresés 0-ja (12. kör, #4400, részben megválaszolva).** A `0x004306a0`-`0x004306b8` sorok a `"filters"` sztringet (`0xc80b04`) adják a `0x0069f510`-nek. Ez a `0x006a46c0`-t hívja (`0x0069f58a`), és a visszatérését `cmp eax,9` után (`0x0069f58f`) a 9-ről 0-ra írja (`0x0069f598`; a C szerint `param_3 = 0`). A `0x006a46c0` (362 bájt, végigolvasva) kódjai: `-1` (`0xffffffff`), ha a `0x006a41e0` (nem dekompilált) nullától különböző értéket ad (`0x006a46e7`-`0x006a4705`); `0`, ha az `[ebp+0xc]` index a lista (`[edi+0x4c]>>1`) alatt van, és az elem lekérése megtörtént (`0x006a4761`, `0x006a47eb`, `0x006a4821`); `9`, ha az index a lista végén van, vagy a zár már a saját szálon foglalt (`0x006a477a`, `0x006a47b6`, `0x006a479f`).
  - **Következmény:** a `0x00907cd0` a `0x004306bd` `test eax,eax` után csak akkor marad ki, ha a `0x006a41e0` hibázott (`-1`). Egyébként fut, mert a 0 és a 9-ből leképezett 0 is a hívást engedi.
  - **Nyitott:** a 0 kétféle jelentésű (megtalált elem, vagy a 9-ből 0-ra írt „nincs ilyen index”), és a `"filters"` kulcs melyik esetet adja, a `0x006a41e0`-tól függ (a kulcs indexre oldása). A `0x0069f510` EAX-be töltő visszatérési ágát nem követtem végig (a `ret 8` előtti `mov eax,ebx` sorok), ezért a leképezett érték visszatérési útja feltételes.
  - **Bizonyítottsági fok:** a `-1` / `0` / `9` kódok és a 9→0 leképezés: **feltételes** (diszasszembly, egy út; a C egyezik). A 0 jelentése: **nyitott**, a `0x006a41e0` nélkül nem dönthető el.
  - **0x006a41e0 (13. kör, #4400): a visszatérési szerződés megerősített; a `"filters"` konkrét kimenete NYITOTT.** Forrás: `.ghidra/2026-10-20-ghidra-13.txt` (C, a munkafában, nem a változtatások között), `annot_disasm.py` (`0x006a46c0`, 362 bájt; `0x0069f510`, 501 bájt).
    - **Szerződés (C).** `3`: a kulcs `NULL`, vagy `param_5 != 0` és `param_3 == 0x1331ffff` (C: 54-56. sor). `0`: a kulcs megvan a `param_1[0x16]` listában, és nem a `FUN_006a7090` ágon áll (C: 73-137. sor), vagy nincs meg, de a `FUN_006a6ff0` betöltése 0-t ad (C: 187-216. sor). `9`: nincs meg, és `param_5 == 0`, vagy `FUN_006a84e0() != 0` (C: 141-154. sor). `4`: nincs meg, és a `FUN_006a85c0` létrehozás 0-t ad (C: 162-179. sor). Minden más: a `FUN_006a6ff0` hibakódja (C: 187-201. sor).
    - **A hívó (asm).** A `0x006a46c0` a `0x006a46e0`-n hívja. `param_1` a `0x0069f510` `eax+0xf20` címe (`0x0069f57b`-`0x0069f581`). `param_3 = 0x13320000` (`0x006a46d3`), ez nem az őrszem `0x1331ffff`. `param_5 = 1`: a `0x0069f584` `mov al, 1` állítja be, és a `0x006a46c0` az `al`-t adja tovább a 5. argumentumként.
    - **Következmény a `"filters"`-re.** A kulcs nem `NULL`, a `param_3` nem őrszem, ezért a `3`-as ág ide nem jön. `param_5 = 1` miatt a `9` csak akkor jön, ha `FUN_006a84e0()` nem nulla. Egyébként a hiányzó kulcs betöltődik, és a visszatérés a `FUN_006a6ff0` kódja (0 a sikerhez). Tehát `0` a megtalált vagy sikeresen betöltött kulcsra, `9` a „nincs betöltés” predikátum mellett, `4` és egyéb kód a létrehozási vagy betöltési hibára. Hogy a `"filters"` melyik ágon áll, a lista tartalmától és a `FUN_006a84e0`-tól függ.
    - **Bizonyítottsági fok.** A szerződés (`0`, `3`, `4`, `9`, egyéb kód): **megerősített** (C és asm: két út, a visszatérési ágak C-ből, a hívó argumentumai asm-ből). A `"filters"` konkrét eredménye: **feltételes**, a `FUN_006a84e0` és a `FUN_006a6ff0` nélkül nem dönthető el.
    - **Cáfoló kísérlet.** Azt feltételeztem, hogy a hívó `param_5 = 0`-val hív, és így a `9` a végső „nincs ilyen kulcs” ág. Cáfolva: a hívó `mov al, 1`-et ír. A `param_3 = 0x13320000` azt is mutatja, hogy a hívás nem az őrszem-ágon megy.
  - **15. kör (2026-10-20, #4400): a `9`-es predikátum és a `"filters"` betöltése.**
    - **`0x006a84e0` (predikátum): megerősített (asm és C, két út).** A `0x006a42e7` hívja `EAX`-ben a kulccsal (a `0x006a41e0` 2. argumentumával). **Helyesbítve (17. kör):** a `0x009946f0` nem névtáblát keres, hanem névtisztító (lásd a 17. kört). A `0x006a84e0` tiszta-név predikátum: `0`, ha a tisztított név egyezik a kulccsal kis-nagybetű-érzéketlenül, egyébként nem nulla.
    - **A `9` ága (az ugrások asm-ből, a `9` kódja a 13. kör C-jéből):** a `0x006a41e0` `0x006a42d7`-`0x006a42ee` sora. A kulcs nincs a `param_1[0x16]` listában, és (az 5. argumentum nulla: `0x006a42df` → `0x006a45f5`) vagy (`0x006a84e0() != 0`: `0x006a42ee` → `0x006a45f5`). Ha a kulcs a névtáblában megvan, a függvény nem a 9-re megy.
    - **`0x006a6ff0` (megerősített, C és asm): NEM a `"filters"` betöltője, hanem rekordinicializáló.** `+0x8 = 2`, `+0x10 = param_3`, a kulcs másolata `+0xc`-be (`0x00985ff0`), a régi `+0xc` felszabadítása. Két hívója van: `0x006a453d` (a `0x006a41e0`-ban: `EDX` = a kulcs, `ECX` = a 3. argumentum) és `0x006a2ff9` (a `0x006a2f00`-ban: `EDX = ebx`, a 3. argumentum `[edi+0x314]`).
    - **A `"filters"` értéke (megerősített, asm):** a `0x006a46c0` a `0x006a46d3`-ban `push 0x13320000`-t tesz a `0x006a41e0` 3. argumentumának, és az 5. argumentum `al = 1`. A `"filters"` betöltése tehát `+0x10 = 0x13320000` értékű rekordot ír, a kulcs `+0xc`-be másolva.
    - **Feltételes:** a `0x006a453d` hívó ág és a 0 kimenet összekötése. A `0x006a42f4`-`0x006a4500` szakaszt ebben a körben nem diszasszemblálták, ezért az átcsorgó (feltétel nélkül továbbfutó) út nincs végigkövetve.
    - **Megválaszolva (17. kör):** a `"filters"` kimenete `0` (lásd alább a 17. kört). A `0x006a6ff0` betöltési visszatérése (siker = `0`) feltételes, mert a törzse nincs végigkövetve.
- Ghidra-kör kell: 0x00429dc0 - a nem üres rect-ág: a `this+0x48` objektum vtbl `+0xd4` slotjának célja (az elem metszete) [nem blokkoló]
  - **17. kör (2026-10-20, #4400): a `0x009946f0` névtisztító, nem névtábla-feltöltő; a `"filters"` kimenete `0`.** Helyesbíti a 15. kör „névtábla-keresés” állítását.
    *Forrás:* `.ghidra/2026-10-20-ghidra-16.txt` (C: `0x009946f0`); `annot_disasm.py` (`0x009946f0`, 808 bájt; `0x006a84e0`, 218 bájt); a `0x006a41e0` C-je: `.ghidra/2026-10-20-ghidra-13.txt` 1-219. sor.
    - **`0x009946f0` (megerősített, C és asm).** A kapott sztringet tisztítja: eldobja a `\/:*?"<>|` karaktereket (`_wcschr`, `0x00c0c186`), a vezető és záró szóközt és pontot levágja, a szóköz-jellegű karaktereket (`_iswspace`, és `0x3000`) szóközre cseréli, végül a `aux`, `con`, `nul`, `prn` foglalt eszköznevekhez `_` utótagot fűz (`push 0x5f`, `0x00985c00`, négy kis-nagybetű-érzéketlen összehasonlítás). Visszatérés: `0`, ha van név; `-1` (`0xffffffff`), ha a kulcs üres, vagy minden karaktere kiesett. Nincs benne táblabejárás.
    - **`0x006a84e0` (megerősített, asm; a C egyezik).** Meghívja a `0x009946f0`-t a kulccsal. Ha az `0`, összehasonlítja a tisztított nevet a kulccsal kis-nagybetű-érzéketlenül, és `0`-t ad, ha egyeznek; minden más esetben nem nulla. Vagyis `0x006a84e0(kulcs) == 0` pontosan akkor, ha a kulcs már tiszta név.
    - **A `"filters"` kimenete: `0` (feltételes).** A `0x006a41e0` a `9`-et csak akkor adja, ha a kulcs nincs a listában, és (az 5. argumentum `0`, vagy `0x006a84e0(kulcs) != 0`) (C: 141-154. sor; asm: `0x006a42d7`-`0x006a42ee`). A `"filters"` hívásban az 5. argumentum `1` (`al = 1`, `0x0069f584`), és `0x006a84e0("filters") == 0`, tehát a `9`-ág nem választódik. Ha a kulcs megvan a listában, a `0`-ág (megtalált elem); ha nincs, a `0x006a6ff0` betöltés kódja, amely siker esetén `0`. Így a kimenet `0`, a névtábla tartalmától függetlenül. A betöltés sikerességét nem követtük végig.
    - **Két különböző `9`.** A `0x006a46c0` saját `9`-e (lista végi index, zár a saját szálon) nem a `0x006a41e0` predikátuma; a `0x0069f510` ezt `0`-ra képezi (`param_3 = 0`).
    - **Bizonyítottsági fok.** A `0x009946f0` szerepe és visszatérési kódjai: **megerősített** (C és asm; a két út ugyanabból a bináris-tartalomból jön, de más reprezentációban, ezért a második út az asm-kulcspontok). A `"filters"` kimenete `0`: **feltételes** (a predikátum-ág és az 5. argumentum asm-ből, a betöltés visszatérése nincs végigkövetve).
    - **Cáfoló kísérlet.** A 15. kör állítását (névtábla-keresés) a C-törzs cáfolja: nincs táblabejárás, csak karakter- és névszűrés. A `9` elérését a `"filters"`-re a `0x006a84e0` `0` eredménye zárja ki.

### 2.5/b A CMakeFaceMoviePanel működése — a „recompute" megerősítője (#1408)

*A 2.5 csak két mondat volt; az arc-film PANEL-jének működése eddig nem
volt feltárva. Ez a szakasz a `0x0061df10` (12 420 b, az arc-film-panel
fő művelet-kezelője) diszasszemblálásából adja a teljes képet.*

**A panel belépési parancsai** (a `0x0061df10` első switch-e): `recompute`,
`render`, `cancel` (+ a fül- és gomb-vezérlők). A `recompute` (a
`makemoviepanel/recompute` gomb) az **újraszámolás** — és ez az egyetlen,
amely MEGERŐSÍTÉST kér:

| lépés | mit tesz | bizonyíték |
|---|---|---|
| 1. | `Preferences\CMakeFaceMoviePanel::askapplyconfirm` **olvasása** (`GetPreference`, `0x407a20`), alap **0** | `0x0061dfa9`–`0x0061dfc2` |
| 2. | ha **0** (még nem „ne kérdezz újra") → a **`CMakeFaceMoviePanelApplyDialog`** felépítése és megjelenítése | `0x0061e073` |
| 3. | a párbeszéd szövege: **„This will generate a new movie removing all the text slides you added. Are you sure?"** | `0x0061e078` (`0xc9d0b8`, EN sor) |
| 4. | a párbeszéd címe: **„Please Confirm..."** (`CCollageUI::ConfirmCloseTitle`) | `0x0061e097` |
| 5. | **„Do not ask again"** pipa (`CMakeFaceMoviePanelRememberDialog`) | `0x0061e002` |
| 6. | Igen + pipa → a választ `SetPreference` (`0x401900`) rögzíti a `askapplyconfirm` kulcsba (`1`) | `0x0061e0f7`–`0x0061e12c` |
| 7. | Igen → `vt[0xa0]` hívás (a tényleges újraszámolás indítása) | `0x0061e14e` |

A `recompute` eredménye a filmkészítő a **3. fül** (`makemoviepanel/tab3`) —
a művelet a `makemoviepanel/edittabbase` + `previewimage` (2.4/i-ből)
paneljeit érinti.

**Két következmény a #1408-as jegyhez:**

1. A „Film arcokból" **újraszámolása elveszi a felhasználó szöveges diáit**
   (a párbeszéd szövege kimondja) — a megvalósításnak ezt a kockázatot
   ugyanígy jeleznie kell.
2. A beállítás **tárolódik** (`Preferences\CMakeFaceMoviePanel::askapplyconfirm`)
   — a „ne kérdezz újra" a párbeszéden állítható, mint a kollázs egyéb
   konfirmálóinál.

### 2.5/c Az „Opciók" fül és a KLIPTÁLCA — MŰKÖDÉS (2026-09-02)

*A 2.5/b csak a „recompute" megerősítőjét adta. Ez a szakasz a fül összes
vezérlőjét megnevezi, megmondja **melyik `.mxf`-mezőt** állítja, és
levezeti a **két csúszka képletét**. Minden cím a `Picasa3.exe` 3.9-é,
image base `0x00400000`.*

> ⚠️ **Helyesbítés a 2.5/b-hez:** ott a `0x0061df10` „az arc-film-panel
> fő művelet-kezelője"-ként szerepel. Pontosabban: **a filmkészítő panel
> KÖZÖS kezelője** — a 2.6/b (hangsáv) és a 2.6/c (kimenet) parancsai is
> ebben ülnek. Az arc-film nem külön kezelőt kap, hanem külön ágakat.

#### A) A kliptálca négy gombja

| elem | parancs | mit tesz | cím |
|---|---|---|---|
| `makemoviepanel/addclips` | `addclips` | átvált a **könyvtárra** (`panelroot/picasatab` névparancs), és bekapcsolja a **klipgyűjtő módot** „Vissza a Mozgófilmkészítés párbeszédpanelhez" sávval (`panelroot/makemovietab`) | `0x0061f62f`–`0x0061f69d` |
| `makemoviepanel/addtomovie` | `addtomovie` | a kijelölt klipeket a lista **VÉGÉRE** fűzi (`push -1` = beszúrási index) | `0x0061f727`–`0x0061f7b9` |
| `makemoviepanel/deleteclips` | `deleteclips` | a kijelölteket **eltávolítja** a tálcából (elemenként `vt[0x94]`) | `0x0061f9c5`–`0x0061fa1d` |
| `makemoviepanel/solo` | — | **nincs parancs-ága** a közös kezelőben; az elemet a `0x00616d40` (975 b) kezeli külön | — |

**Előfeltételek (`addtomovie`, `0x0061f72b`–`0x0061f76a`):** ha a tálca
(`[panel+0x470]`), a forrás (`[panel+0x4b8]`) vagy a projekt
(`[panel+0x4bc]`) bármelyike hiányzik, **vagy nincs kijelölés**, a gomb
némán nem csinál semmit. A kijelölés-lista elemenként **két duplaszó**
(`shr esi,1` a darabszámhoz).

**A törlés után az előnézet CSAK akkor számolódik újra**, ha nincs
függőben lévő Opciók-módosítás (lásd F) — `0x0061fa2b`–`0x0061fa43`.
Ellenkező esetben a klip eltűnik a tálcáról, de az előnézet a régi marad.

#### B) A három rendezés-rádiógomb → az `.mxf` `<ordering>` mezője

| rádiógomb | `<ordering>` | bizonyíték |
|---|---|---|
| `makemoviepanel/smart_order_radio` | **0** | `0x006177a3`–`0x006177a7` |
| `makemoviepanel/album_order_radio` | **1** | `0x006177a9`–`0x006177b3` |
| `makemoviepanel/chronological_order_radio` | **2** | ugyanott: a „egyik sem" eset |

Az érték a `[ctrl+0x359]` bejelölt-bájtból jön. A `chronological`
állapotát a beolvasó **meg sem kérdezi** — az a maradék eset.

⚠️ **A rádió-viselkedés kézzel van megvalósítva.** A parancs-ág mind a
három gomb bejelöltségét **explicit beállítja**, és a hívás harmadik
paramétere mindenütt **0** (nincs értesítés):

| kattintás | smart | album | chronological | cím |
|---|:--:|:--:|:--:|---|
| `smart_order_radio` | 1 | 0 | 0 | `0x00620132`–`0x00620152` |
| `album_order_radio` | 0 | 1 | 0 | `0x006201c0`–`0x006201e0` |

⇒ **A kattintás önmagában NEM számol újra** (a kezelő azonnal `0xf4240`-nel
tér vissza) — csak megjelöli a fület nem-alkalmazottként.

#### C) A többi Opciók-vezérlő és a mezője

| vezérlő | `.mxf` mező | megjegyzés |
|---|---|---|
| `makemoviepanel/remove_low_res_faces` | `removelowresfaces` | a `[ctrl+0x359]` bájt, `0x0061778b` |
| `makemoviepanel/show_captions` | `showcaption` | |
| `makemoviepanel/crop_to_fit` | `cropfit` | |
| **„Dátumok megjelenítése"** (`CMakeMoviePanel::show_dates_label`, EN `Show Dates`) | `showdates` | a `0x00618050` a `crop_to_fit_label` **mellett/helyett** teszi ki — ez a mező eddig SEHOL nem volt megnevezve vezérlőként |
| `burstslider/scaleslider` | `burstmodethresh` | lásd **D** |
| `lengthslider/scaleslider` | — (a felhasznált képek száma) | lásd **D** |

A beolvasó a `0x006175c0` (2691 b); a mezőnevek az `.mxf` írójából és
olvasójából jönnek (2.4/b, illetve az **olvasó** `0x008152f0`, 4081 b,
amely mind a 30 mezőt ismeri).

#### D) A két csúszka képlete — MÉRVE

```
burstmodethresh = ⌊ s² × 60 × 60 × 24 ⌋  =  ⌊ s² × 86 400 ⌋   [másodperc]
```

- `s` a csúszka értéke, a `0x009ddd00` olvassa ki (a vezérlő `vt[0x18]`-a, float)
- a konstansok: `0x00cf4020` = **60.0**, `0x00cf3ef0` = **24.0** (`0x006176e3`–`0x006176ed`)
- **`s` normalizált (0..1) — ez MÉRT, nem feltevés:** ugyanez a
  `scaleslider`-érték a hangerőnél `× 1000.0` szorzóval
  (`0x00cf3e10`, `0x00623e38`) megy a `Preferences\movievolume` kulcsba,
  amelynek tartománya a 2.6 szerint **0..1000**
- ⇒ a szűrő **maximuma pontosan 24 óra**, a görbe **négyzetes** (a csúszka
  alsó felén jóval finomabb a felbontás)
- `s = 0` → a felirat `CMakeMoviePanel::movieburstzero` = **„Ne legyen
  szűrés a készítés ideje alapján"**; egyébként `movieburst` = **„Az
  utolsó időszak képeinek eltávolítása: %s"** (`0x0061ac70`)

```
felhasznált képek = ⌊ t² × N ⌋
```

- `N = [panel+0x48c]`, a panel indulásakor a forrás `vt[0x38]`-ából
  (`0x0061843f`)
- **`N` azonossága MÉRT:** ugyanez az érték megy a `0x0061adf0`-ba
  (`0x0061855e`), az pedig a `0x0061abb0`-on át a
  `CMakeMoviePanel::movielength` = **„Összes fotó: %s"** feliratot rajzolja
- a negatív érték előjel nélkülire javítódik (`+ 4294967296.0`,
  `0x00cf39e4`, `0x006177ec`) ⇒ a mező **unsigned**

#### E) Az újraszámolás ÖT bemenete

```
0x0081b800( [panel+0x4b8],  hossz,  ordering,  burstmodethresh,  removelowresfaces )
```

`0x00617810`. Ez az egyetlen hely, ahol a fül négy beállítása egyszerre
átmegy a film-előállítóhoz — **a fül minden más vezérlője csak eddig jut.**

#### F) A „nem alkalmazott módosítások" kapu — ÚJ, a 2.5/b-ben NINCS benne

A `render` útja (2.6/c) a **`0x006204ec`**-nél megnézi a
`[panel+0x4f0]` / `[panel+0x4f1]` jelzőket; ha bármelyik áll, meghívja a
`vt[0xb0]`-t, azaz a **`0x0061dcf0`**-et (539 b).

| lépés | mit tesz | cím |
|---|---|---|
| 1. | ha egyik jelző sem áll → **1**-gyel tér vissza | `0x0061dd00`–`0x0061dd12` |
| 2. | megkeresi a `makemoviepanel/recompute` gombot; ha nincs, vagy a `[ctrl+0x20e]` bájtja nem nulla → **1** | `0x0061dd22`–`0x0061dd54` |
| 3. | beolvassa a `Preferences\`**`CMakeFaceMoviePanel::askapplyswitchconfirm`** kulcsot; ha **nem nulla** → **1** | `0x0061dd5a`–`0x0061dd9b` |
| 4. | különben párbeszéd: cím = `CMakeFaceMoviePanel::UnapliedChanges` (**„Opciók"**), szöveg = `CMakeFaceMoviePanelUnappliedDialog` (**„Még nem alkalmazott módosítások vannak az Opciók lapon. Alkalmazza őket?"**), gombok **Igen / Nem / Mégse**, plusz **„Ne kérdezze meg újra"** pipa | `0x0061ddaa`–`0x0061de9d` |
| 5. | ha a pipa be volt jelölve → a kulcsba **1** kerül (`SetPreference`, `0x00401900`) | `0x0061dead`–`0x0061dedf` |

**A visszatérési érték a `render`-ágban** (`0x00620510`–`0x00620568`):

| érték | jelentés | mi történik |
|:--:|---|---|
| **0** (a konkrét gombcímke-eredménykód leképezés **NINCS MEG**) | `recompute` | átvált a `makemoviepanel/tab3`-ra és elsüti a `recompute` parancsot: **a film nem készül el most** |
| **2** (a konkrét gombcímke-eredménykód leképezés **NINCS MEG**) | kilépés | a művelet elmarad |
| egyéb (a konkrét gombcímke-eredménykód leképezés **NINCS MEG**, vagy a kapu kihagyása) | menj tovább | a render/export folytatódik |

⛔ **A „Ne kérdezze meg újra" itt NEM azt jelenti, hogy alkalmaz.** A kapu
ilyenkor **1**-et ad (`0x0061defe`), ami a fenti tábla harmadik sora:
a Mozgófilm létrehozása **némán eldobja** a fülön elvégzett, nem
alkalmazott módosításokat.

⚠️ **Ez MÁSIK kulcs, mint a 2.5/b-beli.** Kettő van, és külön-külön
állítható: `askapplyconfirm` (a *recompute* megerősítője) és
**`askapplyswitchconfirm`** (a *nem alkalmazott módosítások* kérdése).

**A két jelző jelentése:** `[panel+0x4f0]` / `[panel+0x4f1]` = **függőben
lévő, még nem alkalmazott Opciók-állapot**. Ugyanez a kettő váltja a panel
forrás-módját **5**-re, illetve **6**-ra a szokásos 1–4/7 helyett
(`0x00618209`–`0x00618223`), és a `[panel+0x4f3]` bájt tárolja, hogy
bármelyik áll-e (`0x0061823c`). *Bizalmi fok: **erős** — a jelentést a
rájuk épülő kapu szövege adja, a jelzők nevét nem olvastuk ki.*

> ⚠️ **2026-10-13 (G/3, 2. pont):** a `0x618050` dekompilátuma szerint a mód-7
> építés maga is 1-re állítja a `+0x4f0` bájtot. Ezért a „függőben lévő módosítás”
> jelentés nem egyedül áll: a `+0x4f0` a mód-7 utáni újraépítés kiválasztója is.
> A fok **feltételes**, amíg utasításszinten nincs megerősítve (G/3, 6. pont, 1. tétel).

#### G) A készítési idő küszöbe: szomszédos csoportosítás, ordering-függő kiválasztás (#4194)

**2026-10-07, 4. kör — a kiválasztási ág azonosítva; a paraméternevek
helyesbítve.** A `0x006175c0` hívó utasításai és az öt argumentumot takarító
`ret 0x14` alapján a `0x0081b800` argumentumai: `param_1` = gyűjtemény,
`param_2` = hossz, `param_3` = `.mxf` `ordering`, `param_4` =
`burstmodethresh`, `param_5` = `removelowresfaces`. Tehát a lentebbi korábbi
„mode” azonosítás **helyesbítendő**: az ágakat az `ordering` választja,
`param_5` nem kiválasztási mód.

⚠️ **2026-10-17 (G/4, 1. pont):** a 4. paraméter a dekompilátumban MUTATÓKÉNT szerepel (`FUN_0081ae10(param_4)` csak `param_4 != 0` esetén), ezért a „4. = burstmodethresh" azonosítás pontosítandó: a hívó a küszöböt vagy egy mutatót ad át, ezt a hívóoldal (`0x00617810`, `0x006175c0`) dönti el: **NINCS MEG**.

- `ordering=0` a `0x0081c9b0` jelöltpontozóhoz vezet. A jelöltek pontszáma a
  regisztrált getterek eredményeinek súlyozott összege; a kód a legkisebb
  összeget választja, szigorú összehasonlítással, ezért holtversenyben az
  előbb bejárt jelölt marad. Nincs érvényes pontozott jelöltnél az első
  jelölt a tartalék. A regisztrációban a HOG getter (`0x00873e40`) súlya
  `1.0`; a `Preferences\SmartMultiPersonTrans` engedélyezésekor a Neven
  getter (`0x008742a0`) súlya a bináris `0x00c7c838` értéke, `0.4f`.
  Ezen az ágon a regisztrált pontszám tehát `1.0f × HOG +
  (preferencia bekapcsolva ? 0.4f × Neven : 0)`.
  A minimumdöntés két úton igazolt; a HOG/Neven nevesítése és súlyainak
  regisztrációja csak az utasításszintű útból következik, ezért **feltételes**.
  „Legjobb minőségű kép” ebből **nem** következik: a kiválasztó a getterek
  számait minimalizálja, a mérőszámok képi jelentése nyitott.
- `ordering=1` és `ordering=2` a gráfépítő és útvonalválasztó ágra vezet
  (`0x00875ee0` / `0x00874e40`, majd `0x00877c50`). A kiválasztás a
  `0x008781a0` reducer szerint kimeneti kulcsonként a legkisebb összesített
  élköltségű út; egyenlő költségnél a korábban bejárt előd marad. A HOG és
  az engedélyezett Neven getter itt is részt vesz az értékelési útban, de az
  élköltség teljes képzésének és a gráfindexek fotórekordokra vetítésének
  pontos szabálya **NINCS MEG**.

**A rekordeltolások igazolt használata, szemantikus nevük nyitott.** A
`+0x34` dword a csoportosító dátumlekérdezésének kulcsa (`0x004edf60`-nak
adja át); a HOG getter útja a `+0x30` és `+0x34` mezőket is olvassa. A
Neven getter mindkét rekord `+0x30` értékét olvassa. Kiválasztás után a
`+0x30` dword a kimenetbe másolódik, a `+0x34` pedig virtuális metódusnak
megy át (`0x0081c7b6`–`0x0081c83f`). Ezek az eltolások **nem** bizonyítják,
hogy a mező képszámot, arcot vagy minőséget jelent. A tényleges rekordíró,
a két mező adattípusa/szemantikája és a konkrét bemeneti fotóhoz tartozó
kiválasztott index **NINCS MEG**.

**Két független út:** A) a friss Ghidra-dekompilátum
(`.codex-ghidra-0081b800.c`, `.codex-ghidra-00874320.c`) megmutatja a nulla
`ordering` közvetlen scorerágát, a nem nulla gráfágat és a rekordmezők
használatait; B) az eredeti EXE utasításszintű olvasata, beleértve a hívó
argumentum-feltöltését, a `0x0081c9b0` minimum-összehasonlítását, a
getter-regisztrációt és a `0x008781a0` reducerét, ugyanezt adja. A
paramétertérkép és az ágak egyeznek; a HOG/Neven nevesítését és súlyait csak
a B út támasztja alá, ezért ezek feltételesek. A mezők szemantikájára és a
konkrét fotóindexre egyik út sem ad választ. A dekompilátum unreachable-blokk
figyelmeztetései miatt az utasítás az irányadó, eltérés nincs.

**Cáfoló kör:** az „mindig az első képet tartja meg” hipotézis ellenőrzésekor
a `0x0081c9b0` utasításai azt mutatják, hogy a pontozott ág szigorú minimum
esetén későbbi jelöltre is frissít; az első csak holtversenyben vagy
tartalékként marad. A pontszámot felcserélő korábbi szintetikus QEMU-hám nem
jutott el a végső fotóindexig, ezért dinamikus cáfoló mérés **NINCS MEG**.
Az állítás itt az utasításolvasat szintjén feltételes; a két független út az
ág- és minimummechanikát megerősíti, nem az ismeretlen rekordindexet.

A `burstmodethresh` nem közvetlenül választ képet. A `0x0081b800` csak
nem nulla küszöbnél hívja a `0x0081ae10` csoportosítót (`0x0081b8be`–
`0x0081b8ca`). A csoportosító a `[obj+0x4e0]` lista `0x38` bájtos
rekordjain, azok `+0x34` dátumkulcsán halad végig; a dátumot a
`0x004edf60` olvassa ki. A FILETIME-ot `+5 000 000` (`0x4c4b40`) után
`10 000 000`-rel (`0x989680`, `0x00c13b70`) osztja, tehát egész másodpercre
kerekíti.

Az első rekord csoportazonosítója **0** (`0x0081afac`). Minden következő
rekordnál az aktuális, kerekített időt az **előző listaelem** idejéhez méri:

```
delta = t[i] - t[i-1]
delta < burstmodethresh  → ugyanaz a csoportazonosító
delta >= burstmodethresh → következő csoportazonosító
```

A `delta`-t a ciklus minden elemnél az aktuális időre frissíti
(`0x0081b0b1`–`0x0081b0f3`); nem az előző megtartott elemhez viszonyít.
Ez a `[obj+0x4e0]` **bemeneti sorrendje**, nem bizonyítja, hogy a lista
időrendben van rendezve.

**Független natív QEMU-mérés:** az eredeti `0x0081ae10` futott; csak a
`0x004edf60` dátumlekérdezését helyettesítő hám adott meg pontos
FILETIME-értékeket. Küszöb: `T=3600` másodperc.

| Bemeneti másodpercek | Csoportazonosítók | Mit különböztet meg |
|---|---|---|
| `[0, 3240, 6480]` | `[0, 0, 0]` | láncszerű: az utolsó az előzőtől 3240-re van, ezért együtt marad; az első megtartotthoz mérő szabály itt új csoportot adna |
| `[0, 3600, 7200]` | `[0, 1, 2]` | az egyenlőség már új csoportot kezd (`>=`, nem `>`) |
| `[0, 3240, 7200]` | `[0, 0, 1]` | az utolsó szomszédos rés 3960, ezért új csoport kezdődik |

**Bizonyítottság:** a küszöb alatti szomszédos csoportosítás és a
`delta >= T` határ **megerősített**: A) a `0x0081ae10` utasításszintű
olvasata; B) a fenti, pontosan megadott időbélyegű natív QEMU-futás.
Az első mérősor cáfolja az „előző megtartotthoz mér” alternatívát.

**Az eddigi bizonyíték nem támaszt alá minden orderingre érvényes
„első/utolsó/jobb minőségű kép” szabályt.** A `0x0081b800` az `ordering`
értékétől függően két kiválasztási utat követ; az időküszöb
által készített csoportazonosítók jelölteket korlátoznak, de önmagukban nem
mondják meg, hogy a bemeneti képek közül melyik kerül a kimenetbe.

**`ordering == 0`: súlyozott jelöltminimum.** A `0x0081b925`→`0x0081c925` ág a
`0x0081c9b0`-be vezet. A már kizárt jelöltek után az aktuális jelölt
csoportazonosítójával egyező képet is kihagyja (`0x0081d41d`–`0x0081d428`).
A `[obj+0x504]` metrikaobjektumok `0x00873170`-en át jelöltenként értéket
adnak; ezeket a `[obj+0x50c]` súlyokkal összeadja
(`0x0081d730`–`0x0081d78c`). A legkisebb összegű, ténylegesen összegyűjtött
jelöltet választja (`0x0081d7b0`–`0x0081d7c4`); szigorú összehasonlítása
miatt egyenlőségnél a korábban bejárt jelölt marad. Ha nincs érvényes
nyertes, az első jelöltre esik vissza (`0x0081d7d5`–`0x0081d7d9`). Ez a
szabály nem állítja, hogy minden küszöbcsoportból pontosan egy kép marad: a
kód az aktuális kép csoportját zárja ki, nem az összes korábban kiválasztott
kép csoportját.

**`ordering != 0`: költségminimumú útvonal.** A `0x0081b800` a
`0x00875ee0` vagy `0x00874e40` gráfépítő útját hívja; ezek a normál
élképzésben kihagyják az azonos csoportú jelöltet
(`0x00875051`–`0x00875060`, illetve `0x00876223`–`0x00876236`). A
`0x00877c50` lépésenként minimális összköltségű útvonalat épít a
`0x008781a0` reducerrel: a bázisköltséghez hozzáadja az él `+8` floatját
(`0x00878291`–`0x0087829e`), majd kimeneti kulcsonként szigorú minimumot
választ (`0x008782a2`–`0x008782be`). Azonos költségnél az elsőként bejárt
előd marad. A `0x008773d0` elérhetetlenség esetén nulla költségű pótló élt
is létrehoz (`0x00877562`–`0x0087757d`), ezért a normál élszűrésből nem
következik abszolút, kivétel nélküli „egy csoportból legfeljebb egy” szabály.

**Az ágak bizonyítottsága: megerősített, a fotóindexé nyitott.** A nulla
`ordering` súlyozott jelöltminimumát és a nem nulla `ordering`
költségminimumú útját a dekompilátum és az utasításszintű olvasat egymástól
függetlenül mutatja. A teljes `0x0081b800`-as képlistás futás egyik ágon sem
adott végső fotóindexet.

**Független natív QEMU-mérés a reduceren:** a `0x008781a0` eredeti kódját
kézzel felépített, két jelöltet és egy kimeneti kulcsot tartalmazó bemenettel
futtattuk. A `+8` itt kizárólag a reducer 12 bájtos segédrekordjának mezője;
ez a mérés nem köti azt a képlista `0x38` bájtos rekordjának egyik mezőjéhez
sem.

| Jelölt 0: bázis + `+8` | Jelölt 1: bázis + `+8` | Mért kimeneti jelölt |
|---|---|---:|
| `0 + 1` | `0 + 2` | `0` |
| `0 + 2` | `0 + 1` | `1` |
| `0 + 1` | `0 + 1` | `0` |
| `5 + 0` | `0 + 1` | `1` |

A mérés tehát a teljes összeget hasonlítja, nem önmagában a `+8` értéket;
egyezésnél a korábban bejárt jelölt marad. A teljes `0x0081b800`-as utat ismét
natív QEMU alatt futtattuk, de a jelenlegi hám nem érte el a kiválasztót.
Pontos futtatási bemenet: `ORDERING=2`, `N=3`, `T=3600` másodperc és
`[0,1000,2000]` másodperces FILETIME-értékek; a gyűjteményobjektum, a vtable
és a getter szintetikus volt. A trace szerint a `0x0081bbac` hívja a
`0x00874e40`-et, amely a `0x00874e70` helyen a `0x00874320`-at hívja. Ez a
segéd a harmadik stack-argumentumként kapott, `0x408023c0` című lokális
vektor fejlécéből `data=0x10100050`, kódolt elemszámként `4` (két elem),
adattartalomként pedig `[0,2]` értéket olvasott. A `0x00874320`
utasításszintű olvasata ezt az adattömböt címeket tartalmazó listaként járja
be: az első `0` elem után a `0x00874aa8` utasítás a `0+0` címen próbál bájtot
írni, és a QEMU SIGSEGV-vel leáll. Ez a mérés a kézzel felépített bemenet
hibáját rögzíti; nem igazolja, hogy a valódi gyűjtemény ugyanezt a vektort
tartalmazza, és nem bizonyítja a fotóválasztási szabályt. A `0x0081bd62` →
`0x00877c50` kiválasztóhívásig, illetve a `0x00877dc7` reducerhívásig a futás
nem jutott el; fotórekord-mezőt nem változtattunk.

Egy külön, közvetlen `0x0081c9b0`-próba ugyancsak szintetikus objektumot,
csoportazonosítókat és metrikaértékeket adott meg. A scorerig eljutott, de a
`0x0081d298` körüli jelöltlista-építésben a `0x0081d310`/`0x0081d4d8`
ciklusnál 30 másodperc után időtúllépéssel leállt; nem adott vissza végső
fotóindexet. Ez a sikertelen hámpróba nem független mérés a végső
kiválasztási szabályra.

**#4194 2. kör — a jelöltciklus és a hám hibahatára (2026-10-06).** A
`0x0081d310`–`0x0081d4e9` ciklust utasításszinten újraolvasva a
visszaugrásnál nincs scorer- vagy `0x004edf60` dátumlekérdező-hívás. A
`0x0081c9f5`–`0x0081c9fb` a scorer-objektum `+0x0c` értékét teszi a helyi
`[esp+0x24]` határba; a ciklus a jelöltpuffer elemszámát növeli, majd a
`0x0081d4e4`–`0x0081d4e9` ponton `(EBX & ~1)` értékét hasonlítja `0xc8`-hoz.
Egy tárolt jelölt `EBX`-et kettővel növeli (`0x0081d4be`–`0x0081d4c7`),
így a visszaugrás akkor marad aktív, ha még nincs összegyűjtve 100 jelölt.
A scorer `0x00873170` hívása később,
`0x0081d74d`-nél van; a dátumlekérdezés a csoportosítóban, a kiválasztás
előtt fut.

**Célzott QEMU-hámpróba:** két rekorddal, `SCORE+0x0c=2` határral,
felcserélt `(1.0, 2.0)` / `(2.0, 1.0)` scorerértékkel és a ciklus
belépését naplózó horggal futott. Mindkét futásban a jelöltpuffer mérete
`2` maradt (egy összegyűjtött jelölt); a hám a hatodik visszaugrás után
mesterségesen a cikluskilépési ágra irányította a futást, amely így eljutott
a `0x00873170` scorerhívásig. A pontszámcsere a naplózott ciklusállapotot
nem változtatta meg. A folytatás a szintetikus gyűjteményobjektum későbbi
kimeneti útján SIGSEGV-vel állt le; egyik futás sem adott vissza végső
fotóindexet. Ez nem természetes cikluskilépés és nem bizonyít kiválasztási
eredményt.

A hámellenőrzés egy címütközést is talált a **mostani lokális próbában**:
az `H_CODE+0x2000`-tól használt mockkód ugyanott kezdődött, ahol az
`H_STUB` importcsonkjai (`H_STUB=H_CODE+0x2000`), ezért a mock nem a
szándékolt kódra mutatott. A próbában a mockokat az importcsonkoktól és az
adatpufferektől elkülönített címre helyezte át, és a `0x0081d22a` virtuális
hívás két stack-argumentumához tartozó hám-visszatérést `ret 8`-ra javította.
Ezek után is megmaradt a jelöltciklus eredmény nélküli útja. A QEMU
naplózott visszaugrásai és az utasításszintű olvasat ezért egyezik abban,
hogy a scorer vagy a dátumlekérdező visszatérése **nem a ciklus közvetlen
kilépési feltétele**. A korábbi timeout pontos oka a teljes, helyesen
felépített gyűjteményobjektum nélkül **NINCS MEG**; a `ordering != 0` ágon
ebben a körben nem futott kétrekordos natív próba.

**Új teljesfüggvény-próba (#4194, 2026-10-06; eredmény nélkül):** a natív
`0x0081b800` hívás `length=2`, `ordering=0`, `burstmodethresh=3600`,
`removelowresfaces=0` értékeket kapott; a négy rekord dátumlekérdezése a
`[0, 1000, 3600, 4600]` másodperces FILETIME-listát adta. A collection,
a `0x00873170`-hez beállított, `1.0`-t visszaadó scorer, a dátumlekérdező
és az allokátorhám szintetikus volt. A futás belépett a `0x0081c9b0`
kiválasztóba, majd 12 másodperces QEMU-időtúllépéssel megállt a
`0x0081d310` jelöltlista-ciklusban; a `0x00873170` getterig nem jutott el,
végső fotóindexet nem adott. Ez a futás a kiválasztási eredményre nem
bizonyíték.

A kiválasztás utáni `0x0081b800` kód a jelöltindexet `[obj+0x4f0]`
leképezőtáblán át használja `[obj+0x4e0] + index*0x38` fotórekord
kiválasztására (`0x0081c7b6`–`0x0081c83f`). Ez bizonyítja a rekordhoz vezető
leképezés módját, de nem azt, hogy a teljes út mely fotórekord-indexet adja
az egyes reducerjelöltekhez, illetve milyen fotómezőből képzi a segédrekord
`+8` floatját.

**A `0x00873170` +8 virtuális getterei — implementáció azonosítva, tartalom
részben nyitott (2026-10-05, #4194 folytatás).** A `0x00873170`
`0x008733df`–`0x008733f8` között az objektum vtable-jának `+8` slotját hívja,
és a visszaadott `float`-ot jelöltenkénti eredményként eltárolja. A
`0x0081c9b0` `0x0081d73d`–`0x0081d74d` szakasza a `[obj+0x504]` objektumlistából
adja át az elemet ennek a getternek; a `0x0081fab0` regisztráló a pointereket
ugyanezen lista `+0x504/+0x508` mezőibe, a súlyokat pedig a külön
`+0x50c/+0x510` listába teszi.

Két, a regisztráló útban létrehozott implementáció van azonosítva:

| RTTI-osztály | objektum vptr-beállítása | vtable `+8` | rekordmezők, amelyekhez a getter útja hozzáfér |
|---|---|---|---|
| `HOGSimilarityComputer` | `0x00819680`: `[this]=0x00cbdec4` | `0x00873e40` | a `0x00873e40` a két jelölt `0x38` bájtos rekordját címezi, majd a `0x00873cb0` feature-építő út a rekord `+0x30` és `+0x34` mezőjét olvassa |
| `NevenSimilarityComputer` | `0x00819850`: `[this]=0x00cbded4` | `0x008742a0` | a `0x008742a0` mindkét jelölt rekordjából a `+0x30` dwordöt olvassa, és ezeket a `0x0048c440` segédnek adja át |

**Független ellenőrzés:** A) az `0x008733f6` virtuális hívás, a két
konstruktor vptr-írása és a `0x00824090` regisztráló hívásai az
utasításszintű adatutat adják; B) az eredeti EXE közvetlen vtable-adatai
`0x00cbdec4`-nél `0x00819720, 0x00873510, 0x00873e40`, illetve
`0x00cbded4`-nél `0x00819890, 0x00874010, 0x008742a0` értékeket tartalmaznak.
A két út egyezik, ezért a két `+8` implementáció **megerősített**. A
`+0x30/+0x34` rekordeltolások elérése **feltételes**: ezeket az utasítások
bizonyítják, de a mezők szemantikus neve/tartalma és a teljes kiválasztóút
még nincs valódi fotórekorddal natívan megmérve. A mezők tartalma
**NINCS MEG**; „minőség”, „pontszám” vagy más szemantikus címke nem
következtethető ki az eltolásból.

**A rekordmezők íróinak pásztázása — a korábbi `0x00823620` jelölt
visszavonva (2026-10-12, #4194 6. kör).** A 2026-10-05-i olvasat azt
állította, hogy a `0x00823620` a rekord `+0x30/+0x34` mezőit tölti. A teljes
utasításszintű újraolvasás ezt nem támasztotta alá: a `0x00823620` 0x38
bájtos elemeket mozgató vektor-assign, de benne nincs rekordbázishoz
viszonyított `+0x30` hozzáférés; a talált `0x30` displacementek
`%esp`-relatívak. A korábbi mezőírás-állítás ezért **helyesbítve**:
`0x00823620` nem igazolt írója a Filmkészítő rekordmezőknek.

A `[obj+0x4e0]` vektorhoz tartozó lehetséges előkészítő út a
`0x00824090` (`0x824164`–`0x824181`), amely a `0x00823620` vektor-assignet
hívja; a teljes rekordtartalom forrását és a `+0x30/+0x34` mezők íróját
azonban ez nem zárja le. A korábbi `0x004e41f0` találat egy beágyazott,
0x38 bájtos alobjektum mezőinek nullázása (`0x4e438c`–`0x4e43cd`), nem
bizonyított Filmkészítő-rekordírás. A rekordíró és a mezők szemantikája
**NINCS MEG**; az eltolás- vagy listaméret-egyezés önmagában nem azonosít
rekordtípust.

**A `0x00874320` hívási adatai — a két út mezői azonosítva, az elemek
jelentése nyitott (2026-10-05, #4194 folytatás).** A `0x0081b800` két
gráfépítő útja ugyanazt a segédet azonos közvetlen gyűjteménymezőkkel hívja.
A) a `0x0081bbac` hívja a `0x00874e40`-et (`0x00874e70`), B) a
`0x0081bb3c` hívja a `0x00875ee0`-t (`0x00875f22`). Mindkét úton a
`0x00874320` az `EAX`-on a `[obj+0x504]` objektumot, az `ECX`-ben a
`[obj+0x6cc]` vagy `[obj+0x6d4]` vektort kapja, és a `[obj+0x744]`
vektorfejlécbe ír (A: `0x874e4c`–`0x874e70`; B: `0x875ee6`–`0x875f22`).
Mindkét hívás az adott `[obj+0x6dc]` vagy `[obj+0x6e4]` értéket is átadja
a `0x00877370` hívásának (`0x874331`–`0x874338`, illetve
`0x875ee6`–`0x875f22`). A második út a `[obj+0x6f8]` vektort a
`0x00874320` után is használja. A két út egyezése megerősíti a közös
hívómező-térképet, de önmagában nem nevezi meg a vektorelemeket.

A `0x00874320` az `ECX`-beli vektor méretét és utolsó dwordjét olvassa
(`0x87433d`–`0x874348`), 8 bájtos elemeket foglal/másol (`0x8743dc`–
`0x87441b`, `0x874450`–`0x874470`) és az eredményt a kapott kimeneti
vektorfejlécbe írja (`0x874335`, `0x874351`, `0x8745e8`). Az `EAX`-on
kapott `[obj+0x504]` objektum virtuális metódusát is meghívja
(`0x874328`–`0x874338`). Az operandustérkép
megadja, mely gyűjteménymezők vesznek részt a két hívásban, de nem
azonosítja a nyolcbájtos kimeneti elemek jelentését, a hivatkozott
képindexeket vagy a `0x00877c50` bemenetéhez szükséges teljes
adatszerkezetet. A `[obj+0x708]` további bemenet a `0x00874e40` úton; az
`0x0081e5a0` dátumvektort, az `0x0081e3a0` a `[obj+0x6f8]` vektort kezeli.
A többi mező szemantikája és tartalmuk teljes visszakövetése **NINCS MEG**.

A korábbi QEMU-próba a szintetikus `[0,2]` adattartalmú bemeneti vektorral nullcímre írt
és SIGSEGV-vel megállt, mielőtt elérte volna a `0x00877c50`-et. Ez nem
valódi gyűjteményrekord-indexekkel végzett futás, ezért nem igazolja a
vektorelemeket vagy a megtartott fotót.

**Bizonyítottsági határ:** a `0x008781a0` reducer minimum- és
döntetlenszabálya **megerősített**: A) utasításszintű olvasat; B) külön
natív QEMU-futtatás. A küszöb alatti csoportosítás szintén
**megerősített** a `0x0081ae10` utasításai és a pontos időbélyegű QEMU-mérés
alapján. A megtartási utak mechanikája viszont **feltételes**: az
`ordering=0` súlyozott getter-minimumát és az `ordering=1/2`
minimális-költségű útját a diszasszembly, illetve a hívási/RTTI/vtable
visszakötés ugyanabba az irányba mutatja, de a teljes képlista egyik útja
sem adott vissza fotóindexet. A konkrét kép, a rekordmezők jelentése és a
gráfélek pontos költségképzése **NINCS MEG**. Ezért nem bizonyított, hogy a
valódi Picasa egy adott küszöbcsoportból melyik képet tartja meg; az
„első”, „utolsó” vagy „jobb minőségű” általános szabály sem állítható.

**Fejlesztési átvezetés a #4182-höz:**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Az eredeti bináris a szomszédos, egész másodpercre kerekített idők között `delta >= T` esetén új csoportot kezd (megerősített). A kiválasztási utak statikus mechanikája `ordering`-függő, de a tényleges fotóindex **NINCS MEG**; a getterek képi jelentése, a rekordíró és a gráf-élek teljes költsége nyitott. | A `burstmodethresh` csúszkaérték tárolódik és átadódik, de nincs képszűrési fogyasztó (`CreateDialogs.qml:70–80, 496–497, 1035`; `create_controller.py:727–729, 806–807, 872`; `mxf.py:125–126, 202–203, 322–323`). `slideshow.py:624–637`: `ordering=0` színátlag-közelségű lánc, `ordering=1` bemeneti sorrend, `ordering=2` `st_mtime`-rendezés. | **#4182:** implementáld a bizonyított csoportosítást: csak `T>0` esetén, a bemeneti lista szomszédos elemei között, egész másodpercre kerekített időkkel, `delta >= T` határral. A megtartási algoritmust ne jelöld eredetihűnek és ne igazítsd a statikus minimumleíráshoz addig, amíg a #181 szerinti eredeti Picasa-kimenet nem ad fotóindex-etalonokat, és egy attól független bináris/QEMU-út nem egyezik velük. `Kész, ha`: (1) `T=0` nem csoportosít; (2) a `[0,3240,6480]→[0,0,0]`, `[0,3600,7200]→[0,1,2]` és `[0,3240,7200]→[0,0,1]` pontos etalonok teljesülnek; (3) a tényleges képmegtartás csak eredeti Picasa-méréssel és függetlenül egyező bináris/QEMU-eredménnyel kerül eredetihűként elfogadásra. |

Nyitott: melyik konkrét fotórekord-index felel meg egy kiválasztott
jelöltnek; ki írja a Filmkészítő `[obj+0x4e0]` rekordlistáját; mit jelentenek
a `+0x30/+0x34` mezők; hogyan áll elő a `ordering=1/2` gráf minden élének
költsége. Célzott következő kör:
`Ghidra-kör kell: 0x00824090 - a Filmkészítő [obj+0x4e0] lista rekordforrása, valamint a +0x30/+0x34 mezőket előállító upstream írók [blokkoló]`
`Ghidra-kör kell: 0x00874320 - a nyolcbájtos kimeneti elemek mezői/indexei hogyan kötődnek a fotórekordokhoz, és mi a 0x00877c50 teljes bemeneti szerződése? [blokkoló]`
**Megválaszolva részben (23. kör, G/11):** a `0x00877c50` rétegenkénti legolcsóbb-út ciklus, a végpont-feltétel `cost[param_3] < 1e8` és `rétegszám ≥ param_4`. A 24. körben (G/12) a két cím megválaszolódott: a rétegenkénti relaxálás és a visszakövetés szerződése megvan. Az élköltség forrása és a végső fotóindex-leképezés nyitott, lásd G/12.

#### G/2. A megtartott kép kiválasztása `ordering = 0`-n — utasításszintű olvasat (2026-10-12, #4194 5. kör)

**Módszer és határ.** A kör a `0x0081b800`–`0x0081d9e0` tartományt
utasításszinten olvasta (capstone-szétszedés az eredeti EXE-ből, a
`ghidra-kimenet/2026-10-07/` dekompilátumával összevetve). Az
`ordering = 0` ág mechanikája ezúttal részletesen megvan; a **getterek
jelentése és a két horgony (ablakhatár, anchor) írója nyitott**. **Natív
QEMU-futtatás ebben a körben NEM történt** (lásd lent az okát). A
`ordering = 1/2` ágra ez a szakasz nem terjed ki; ott a G szakasz áll.

**Hívási lánc (0x0081b800).**

- A csoportosító (`0x0081ae10`) csak akkor fut, ha a `burstmodethresh`
  nem nulla (`0x0081b8be`–`0x0081b8ca`). Nulla küszöbnél a csoportazonosító
  nincs, a kizárás csak a kiválasztottakra vonatkozik.
- A kimenet darabszáma `K = clamp(hossz, 2, N)` (`uStack_30` a
  dekompilátum 26–40. során), `N = [obj+0x139] >> 1`.
- `ordering = 0` esetén `0x0081c9b0(gyűjtemény, K, zárt-jelzők, csoportok, 0)`
  fut (`0x0081b925`→`0x0081c925`; dekompilátum 83–99. sor), és az
  utómunka az `0x0081b800` 780. sorától a `0x0081c980` címkére ugrik.
  Az `ordering = 0` ág ezért nem használja a `0x00874320` gráfépítőt.

**A horgony (első kiválasztott kép) — deterministikus, nem pontszám.**
`0x0081c9b0` első lépése (`0x0081ca05`–`0x0081ca33`): ha `[obj+0x738] ≠ -1`,
a horgony az a rekord, amelynek `+0x30` mezője egyezik vele (ciklus a
`[obj+0x4e0]` listán, 0x38 bájtonként); különben a horgony a 0. elem. A
horgonyt a `[esp+0x48]` kiválasztott-tömbben `1`-re állítja (`0x0081caaf`),
és ő lesz az aktuális középpont (`[esp+0x14]`, `0x0081cab3`).

**Egy kiválasztási lépés (`0x0081d298`–`0x0081d4e9`, `0x0081d730`–`0x0081d7db`,
pick-zárás `0x0081d803`–`0x0081d8a0`).**

1. **Jelöltlista — kifelé haladó spirál a középpont körül.** Az eltolások
   sorrendje `+1, −1, +2, −2, +3, −3, …` (a `[esp+0x28]` számláló
   előjelváltása `0x0081d4ca`–`0x0081d4d8`). Egy `j` jelölt, ha
   (a) `0 ≤ j < N`; (b) még nincs kiválasztva (`[esp+0x48][j] = 0`,
   `0x0081d400`–`0x0081d408`); (c) a `[obj+0x10]`-ből hivatkozott
   zárt-jelző tömbben `0` (`0x0081d40e`–`0x0081d417`); (d) **a csoportja
   különbözik a középpont csoportjától** (`0x0081d41d`–`0x0081d428`, a
   csoporttömb `[obj+0x14]`). A lista legfeljebb **100** jelöltet tartalmaz
   (`(EBX & ~1) == 0xc8`, `0x0081d4e4`); az oldalhatárok és az oldal-kimerülés
   kilépési ágai `0x0081d3xx`–`0x0081d4ef`. A pontszám a ciklusba nem szól
   bele (a korábbi megállapítás marad).
2. **Pontszám — elemenként súlyozott összeg.** A regisztrált getterek
   (`[obj+0x504]` lista, `[obj+0x508]` darabszám) jelöltenként egy-egy
   floatot adnak (`0x0081d74d`, `call 0x873170`); a súlyok `[obj+0x50c]`.
   Elemenként: `pont[i] += súly[g] · getter_g[i]` (`0x0081d730`–`0x0081d78c`).
   Ez a teljes összeg, nem egyetlen getter eredménye.
3. **Választás — szigorú minimum, 1e8 küszöbbel.** A kezdő legjobb érték
   a `0xc7da00` konstans: **100 000 000,0** (`0x0081d792`). Egy jelölt
   csak akkor nyer, ha pontszáma **szigorúan kisebb** a legjobbnál
   (`0x0081d7b0`–`0x0081d7c4`, `fcompp` + `test ah,0x41`). Egyenlőségnél a
   korábban bejárt marad. **Ezért a 1e8-nál nagyobb vagy azzal egyenlő
   pontszámú jelölt soha nem nyer.**
4. **Tartalék.** Ha nincs nyertes (az összes jelölt ≥ 1e8, vagy a
   `[esp+0x3c]>>1` darabszám 0), a nyertes a **jelöltlista első eleme**
   (`0x0081d7d5`–`0x0081d7d9`) — vagyis a spirál első találata, nem „az első
   kép” a bemeneti sorrendben. Üres lista esetén a kód nincs ellenőrizve
   (az olvasás a `[esp+0x30]` nullmutatón menne; ezt a futtatás nem mérte).
5. **Pick-zárás.** A nyertes `j` jelölve (`[esp+0x48][j] = 1`); a `+0x30`
   dword a kimeneti tömbbe kerül (`0x0081d832`), a `+0x34` dword egy
   virtuális hívásnak megy (`0x0081d873`); az új középpont `j`
   (`0x0081d8a0`). Az irányjelző (`[esp+0x10]`) a `j` oldalától függően
   törlődik (`0x0081d7e0`–`0x0081d7fe`). A ciklus `[obj+0x500] == K`-ig
   (`0x0081d8bf`) fut; a horgony ebbe a számlálóba beleszámít-e, a
   kilépés pontos egyenlőségi feltétele ebben a körben **nincs
   visszaellenőrizve**.

**Igazolt, a G szakasz eddigi leírásán túl (utasításszint):**

- **1e8 küszöb** (új): a 1e8 feletti jelölt sosem választódik; a
  tartalék a spirál első eleme.
- **Spirál-sorrend** (új): a holtverseny és a tartalék is a spirál
  sorrendjéhez kötődik, nem a bemeneti sorrendhez.
- **Csoportkizárás a középponthoz képest** (megerősít): a következő
  kiválasztás csak az **előző kiválasztott kép** csoportját zárja ki; a
  korábbi csoportok újra választhatók.
- **Horgony** (új): az első kiválasztott kép nem pontszámmal dől el.

**NYITOTT (ebben a körben nem lezárható):**

- a `[obj+0x720]` / `[obj+0x728]` táblák írója (a `0x0081d2c1`–`0x0081d2e5`
  ágban a spirál oldalhatárait adják a középponttól függően) és a
  `[obj+0x738]` írója — ez adja a horgonyt;
- a getterek **jelentése** (a HOG és a Neven getter fotómezői; a `+0x30`
  / `+0x34` szemantikája). A „legkisebb összeg” ezért **nem nevezhető**
  „legjobb minőségnek”;
- a `0x0081c9b0` 5. argumentumának (`[ebp+0x18]`, mode-0 hívásban `0`) és
  a `[obj+0x13e]` indirekciónak a szerepe;
- a kimeneti darabszám pontos lezárása (a horgony a `K`-ba beleszámít-e).

**Natív QEMU-út — NEM futtatva.** Az `ordering = 0` spirálciklus kilépése a
`[obj+0x720]`/`[+0x728]` ablaktáblától és a `[obj+0x738]` horgonytól függ.
Egyik korábbi szintetikus próba sem töltötte fel ezeket valódi
rekordokkal; a 2. körben a futás a `0x0081d310` ciklusban elakadt. Egy
értelmes második út előfeltétele tehát a táblák írójának visszakötése
(Ghidra-kör), nem újabb futtatás. Ez nyitott kérdés, nem bizonyíték.

**CPU-jelzők (`0xd695d0` MMX, `0xd695d4` SSE).** A fenti függvények és a
hozzájuk tartozó segédek tartományai (`0x008773d0`, `0x00877820`,
`0x008781a0`, `0x00877370`, `0x0081b150`, `0x0081e220`, `0x0081e3a0`,
`0x0081e5a0`, `0x00873e40`, `0x008742a0`, `0x00873cb0`, `0x00873170`,
`0x0081fab0`, `0x00824090`, `0x004edf60`, `0x0048c440`) szétszedésében
nincs `0xd695xx` hivatkozás. A tartományok végei nem függvényhatárok (nem
ellenőriztük), ezért ez csak annyit állít: ezekben a tartományokban a
CPU-jelzőtől való ágazás nem látszik. Ha a lánc mégis ágazik, a valódi
MMX/SSE-ágat a valódi gépen kell mérni — ez nem történt meg.

**Bizonyítottsági fok (G/2):** a spirál, a szigorú minimum, az 1e8 küszöb,
a tartalék és a pick-zárás **feltételes**: ezekhez egyetlen, utasításszintű
út készült; független natív eredmény nem volt. A getterek jelentése, a
horgony forrása és a darabszám-lezárás akkor még **NYITOTT** volt; a G/2c
ezek közül több pontot pontosít, de a kiválasztott fotóindexet továbbra sem
méri.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A készítési idő szerinti csoportosítás: szomszédos delta, `delta >= T` új csoport, egész másodpercre kerekítve; csak nem nulla küszöbnél fut (G, megerősített). | `burstmodethresh` csak tárolódik és átadódik (`src/picasapy/movie/slideshow.py:75`, `mxf.py:126`, `app/create_controller.py:728`, `:807`). A `src/` alatt nincs csoportosító vagy szűrő (`grep -i burst` a `movie/` alatt). | #4182: a szomszédos csoportosítás implementálható (a QEMU-s három esetet tesztnek). |
| `ordering = 0` (sima sorrend, rádió: `smart_order_radio`): horgony, spirál-jelöltlista a középponttól, csoportkizárás, súlyozott getter-összeg, szigorú minimum 1e8 küszöbbel, tartalék a spirál első eleme. | `slideshow.py:626`–`637`: a következő, színátlagban legközelebbi kép (`np.linalg.norm`). Nincs horgony, spirál, csoport, getter. | **Eltér**: a szín-alapú láncolás nem az eredeti szabály. A szabályhoz a getter-semantika (HOG/Neven) kell; addig nem implementálható hitelesen. A jelenlegi színes ág jelölendő „nem eredeti”-ként. |
| `ordering = 1` (album, `album_order_radio`): `0x0875ee0` (ha `[obj+0x1da]` nulla), jelölt-indirekció `[obj+0x13e]`-n át. | `slideshow.py`: a bemeneti (album) sorrend marad, nincs kiválasztó (nincs rendezés). | A szabály nyitott (graph-út nem visszafejtett); a jelenlegi album-sorrend egyezhet a kimenettel, de ezt nem igazolta semmi. |
| `ordering = 2` (időrend, `chronological_order_radio`): a `0x0874e40` gráfút (nem időrendezés). | `slideshow.py:624`–`625`: `st_mtime` szerinti rendezés. | **Eltér**: a fájl-mtime nem az eredeti kulcs, és a kiválasztás sem időrend. A graph-út visszafejtése (`0x00877c50`) a teendő. |
| Alapérték: a rádió-csoport kézi kezelése, az `.mxf` `<ordering>` mezőjéhez. | `movie/mxf.py:125` alapja `0`, `movie/slideshow.py:74` alapja `1`. | **Egyeztetni** a két alapértéket az eredeti rádió-alapjával (a UI-alapértelmezés ebben a körben nincs visszaellenőrizve). |

#### G/2b. A 6. kör (2026-10-12): a költségfüggvény, az írók és ami még hiányzik

**Módszer.** A teljes `.text` szétszedése `llvm-objdump`-pal (az `objdump`
ezen a gépen csak arm/aarch64 célt tud; a `llvm-objdump` x86-ot és PE-t olvas).
A képcím ImageBase `0x400000`, a `.text` VA `0x401000`; a címek egyeznek a
Ghidra-kötegével. A függvényhatárokat MSVC `int3`-kitöltésből becsültük, nem
Ghidra-határból. Hívóhelyekhez a teljes `.text` végigolvasása, íróhelyekhez
displacement-keresés (`0x4e0`, `0x720`, `0x728`, `0x738`) és az indexelt
írások keresése (`(%reg,%reg,4)`). Natív futtatás nem történt.

**1. A `0x00874320` NEM költségfüggvény.** Utasításszinten vektor- és
tömbméretezés: az MSVC-s `max_size`-határok (`0x7fffffff`, `0x2492492`), elemenként
8 bájtos inicializálás (`0x4010e0`, `push 8`), a végén bájtmaszk-írás
(`movb $1,(%edx,%esi)`). Lebegőpontos művelet csak az egész→float konverzió
(`fildl`/`fadds 0xcf39e4`, ahol a mért konstans 2^32) és a 2-hatvány kerekítés
(`shrl $0x17`). Költségre utaló `fmul`/`fadd` nincs. Hívói: `0x874e70` (a
`0x874e40` gráfútból) és `0x875f22` (a `0x875ed9` utáni függvényben, amelyet
nem olvastunk végig). A `0x00874320` „költségfüggvény” címkéje az
összefoglaló #22/#24 pontjában tehát téves.

**Mode ≠ 0 lánc (mért).** A `0x81b925` `cmpl $0,0x4c(%esp)` után `je 0x81c925`
(mode = 0 → `0x81c9b0`, ez a G/2 eredeti állítása). A nem-nulla ág a
fall-through-ban van: `0x81bbac calll 0x874e40`, a `0x504`-es getter-listával
és további `0x6f8`/`0x708`/`0x744` argumentumokkal. A `0x81b930`–`0x81bbac`
közti ágazást nem követtük végig. **A mode ≠ 0 költségképzése tehát a
`0x874e40`-ben van, nem a `0x874320`-ban.**

**A `0x00874e40` (4249 bájt, `0x874e40`–`0x875ed9`) mért részei:**
- `calll 0x873170` (`0x875653`) egy getter-hívás a `0x504`-listáról;
- a float-tömb `rep stosl 0x3f800000` kitöltése (1,0f) alapértékkel
  (`0x87562f`–`0x875634`);
- elemenként `flds (%edx,%eax,4)`, majd bájtflag (`cmpb $0,(%ecx,%edx)`) mellett
  `fmull 0xcf4968`. A konstans a `.rdata`-ból kiolvasva: **−1,0842·10⁻¹⁹
  (= −2⁻⁶³)**. Hogy ez miért szorzó, és mit jelent a flag, **NYITOTT**: költség-
  szorzónak nem természetes, lehet kiolvasási vagy kódolási hiba is;
- `calll 0x878760` (3×) a rekordpárokra és `calll 0x874ac0` (2×);
- időkülönbség nem látszik a függvényben (csak az int→float konverzió).

**2. Az írók (mért).**

| Mező | Ki írja (cím, mit) | Megjegyzés |
|---|---|---|
| `[obj+0x4e0]` — 56 bájtos rekordvektor | `0x823620` vektor-assign (`pushl $0x38`, `addl $0x38`, darabhatár `0x2492492`); hívja `0x824090` a `0x82417d`-nél. | A `0x823620`-ban **nincs** rekord `+0x30`-hoz való hozzáférés (a `0x30(` találatok mind `%esp`-relatívak). Az összefoglaló #24 „+0x30-at másol egész-tömbbe" állítása ezzel nem igazolódott; ezt a spec nem veszi át. A `+0x30` olvasása a `0x81c9b0`-ban és `0x81d2xx`-ben van. Közvetlen pointer-író még: `0x6999ec` (ctor `0x6999c0`), `0x81a439` (`0x81a130`), `0x820793`/`0x820ed1` (`0x81fc30`), `0x821ec1` (`0x8218a0`); ezek törzsét nem olvastuk végig. |
| `[obj+0x4e8]` — rekordindex-tömb | `0x81c9b0` `0x81d88a`: `movl %eax,(%edx,%ecx,4)`, `edx=[obj+0x4e8]`, `ecx=[obj+0x500]`, `eax=[obj+0x4f0][j]`. Újraallokáció `0x81d05a`–`0x81d1f1`. | — |
| `[obj+0x70]` — kimeneti azonosító-puffer | `0x81c9b0` `0x81d832`: `movl %edx,(%edi,%ecx,4)`, `edx=[0x4e0][j].+0x30`. | Megerősíti a G/2 állítását, hogy a kimenet a `+0x30` azonosító. |
| `[obj+0x738]` — horgony | **Egyetlen direkt író a teljes `.text`-ben:** `0x824090` `0x8242f0`: `movl %edx,0x738(%ebp)`, `edx=[esp+0x40]`. A `[esp+0x40]` kezdőértéke `-1` (`0x8240f6`); a `0x8223e0` vagy `0x8226e0` írja out-paraméterként (`leal 0x40(%esp)`, `leal 0x14(%esp)`). | A két writer törzsét nem olvastuk végig. A horgony-keresés megerősítve: `[obj+0x738] ≠ -1` esetén a `0x4e0` rekordjain (0x38-as lépés) a `+0x30`-at egyezteti (`0x81ca05`–`0x81ca33`), és az egyezés **indexét** (nem azonosítóját) menti; `-1` esetén index 0. |
| `[obj+0x720]`, `[obj+0x728]` — int-tömbök (méret: `[+0x724]`/`[+0x72c]` = 2n\|jelző) | `0x81e5a0` új elemeket tölt: `0x720 ← -1` (`0x81f026`), `0x728 ← n` (`0x81f1e8`), `0x718 ← n` (`0x81ee68`); a pointer-csere displacement-íróval (`0x81ee9e`–`0x81f1bb`). A ctor `0x6999c0` a kezdőértéket (`0x699ae7`, `0x699af3`) állítja. `0x81a130`: `0x81a1f6` (0x728), `0x81a215` (0x720) pointer-csere. | **Nem-sentinel (ablakhatár-indexű) értéket író utasítást nem találtunk.** Az indexelt-írás keresés a `0x81c9b0`, `0x81e220`, `0x81e5a0`, `0x824090` és `0x81a130` függvényekben csak a `-1`/`n` kitöltést és a rekordindex-írást adta. `rep movs/stos` a vizsgált függvényekben nincs. |

**3. A „melyik kép marad” szabály: mi új és mi hipotézis.**

- *Megerősített (mért):* a `0x81c9b0` ordering=0 magja a G/2 szerint működik:
  a horgony-keresés, a `0x720[pos]`/`0x728[pos]` olvasás (`0x81d2b2`–`0x81d2e5`,
  sentinel `-1` és `n` összehasonlítással), a pick-zárás (`0x81d803`–`0x81d8a0`),
  a `+0x34`-es virtuális hívás (`0x81d873`), a `[obj+0x500] == K` feltétel
  (`0x81d8bf`), és a `0xc7da00` = **100 000 000,0** (a 1e8 küszöb).
- *Hipotézis (nem bizonyíték):* mivel a `0x720`/`0x728` táblák csak sentinelre
  íródnak, a spirál oldalhatárai alapértelmezésben a teljes listát fedik. Ezt csak
  az írók megtalálása vagy egy valódi rekordokkal végzett mérés dönti el.
- *Nyitott, de mért nyom:* a `0x81e5a0` farkában a `+0x34` mezőt 64 bites
  értékként kezeli (`adcl`), a `0x4c4b40` (5 000 000), a `0x989680`
  (10 000 000) és a `0x15180` (86 400) konstansokkal. Ez összhangban lehet a G
  egész-másodperces csoportosításával, de nem bizonyított. A `0xc7ccf8` double
  konstans mért értéke 949998.0; szerepe nyitott.
- *Nyitott:* a `0x81c9b0` `0x81c9d3` ágában, ha a `0x504`-lista egy eleme null,
  a függvény `0x81e0f2`-re ugrik (korai kilépés). Az ág értelmét nem olvastuk
  végig.

**4. Mi maradt nyitva.**
1. A `0x720`/`0x728` nem-sentinel értékeinek írója (ha nincs, a 3. pont
   hipotézise igaz).
2. A getterek jelentése: `0x873170`, `0x878760`, `0x4edf60`, `0x98b650` törzse
   nincs olvasva.
3. A `0xcf4968` (−2⁻⁶³) szorzó és a bájtflag szerepe a `0x874e40`-ben.
4. A horgony forrása: a `0x8223e0` és `0x8226e0` törzse.
5. A `0x81c9b0` 5. argumentuma (mode) és a `0x81b930`–`0x81bbac` ágazás.
6. Natív mérés: nem történt; a 2. kör állapota változatlan.

**Bizonyítottsági fok (G/2b):** a fenti, egyetlen utasításszintű útra épülő
állítások **feltételesek**, amíg nincs velük egyező független mérés vagy
adatút. A getterek, a `+0x34` mező és a horgony forrásának pontosítását a
G/2c tartalmazza; a `0x720`/`0x728` teljes íróútja és a nem-nulla mód
költsége továbbra is nyitott.

#### G/2c. Getterek, horgony és a megtartás szabálya (2026-10-12, 7. kör)

**Módszer és határ.** Célzott Capstone-olvasat készült az eredeti EXE
`0x0081c9b0`, `0x0081e220`, `0x0081e5a0`, `0x00824090`, `0x00873e40`,
`0x00873cb0`, `0x008742a0`, `0x00873170`, `0x00878760`, `0x0048c440`,
`0x004edf60`, `0x0098b650`, `0x00448fb0` és `0x00448c90` címein. A külön
út az RTTI-adatbázis, a vtable-slotok, a hívási xrefek/importok, valamint a
`0x0081b800`, `0x008223e0`, `0x008226e0` és `0x00824090` korábban készült
Ghidra-dekompilátumainak olvasata volt. A teljes `.text`-et ebben a körben
nem pásztáztam.

**A megtartás `ordering = 0` esetén.** A küszöb nem azt mondja meg, hogy a
csoportból időben az első vagy az utolsó kép maradjon. A `0x0081c9b0` előbb
horgonyt választ: ha `[obj+0x738]` nem `-1`, a `[obj+0x4e0]` rekordok
`+0x30` kulcsai között keresi; ha `-1`, a 0. rekordot használja
(`0x0081ca05`–`0x0081ca33`). Utána minden új választás az aktuális középpont
körül, `+1, −1, +2, −2, …` eltolásokkal bejárt jelöltekből indul
(`0x0081d298`–`0x0081d4e9`). Jelölt csak akkor kerülhet a pontozásba, ha
nincs kiválasztva, nincs lezárva, és csoportja eltér az aktuális középpont
csoportjától (`0x0081d400`–`0x0081d428`). A lista legfeljebb 100 jelöltet
tartalmaz (`0x0081d4e4`). Ez nem külön-külön „legjobb kép csoportonként”
eljárás: minden lépés csak az előző középpont csoportját zárja ki.

A jelöltek pontja a regisztrált getterek eredményének súlyozott összege;
`0x0081fab0` regisztrálja a mérőobjektumot és a súlyt, `0x00824090` pedig
HOG-ot `1.0` súllyal, továbbá a `SmartMultiPersonTrans` beállítás igaz
ágában Neven-mérőt a `0x00c7c838` bináris float-konstanssal. A választó a
legkisebb pontot keresi, de csak a `0x00c7da00` konstansnál szigorúan kisebb
érték nyer; az egyenlőség a korábban bejárt jelöltnél marad
(`0x0081d730`–`0x0081d7c4`). Ha a nem üres jelöltlistán nincs ilyen pont,
a spirál első jelöltje a tartalék (`0x0081d7d5`–`0x0081d7d9`). A nyertes
lesz az új középpont (`0x0081d8a0`), és a folyamat a kért darabszámig fut.
Az objektum létrehozásakor `[obj+0x500] = 1` (`0x00699b95`), az
`0x0081e220` pedig minden további választásnál növeli; tehát a horgony
**beleszámít** a kimeneti darabszámba.

**Mit mérnek a getterek.** Az RTTI két külön mérőosztályt és a
`vtable+8`-slotokat azonosítja: `HOGSimilarityComputer` → `0x00873e40`,
`NevenSimilarityComputer` → `0x008742a0`. A `0x00873170` közös diszpécser,
amely a mérőobjektum slotját hívja; nem önálló képjellemző. A HOG-út a
rekord `+0x30` és `+0x34` mezőjét adja át a jellemzők lekérésének
(`0x00873e40`, `0x00873cb0`), majd ezekből párértéket számít. A Neven-út
`+0x30` kulcsokat ad a `0x0048c440` segédnek, és 0/1 floatot képez a
segéd logikai eredményéből (`0x008742a0`). Az igaz eredmény és az egyező,
nem-null cache-kulcs 0-t, a hamis eredmény 1-et ad. A segéd logikai
eredményének pontos fotórekord-jelentése, valamint a `+0x30/+0x34` mezők
emberi/formatumbeli neve **NINCS MEG**; ezért az összeg nem nevezhető
„képminőségnek”.

A korábban nyitott `0x00878760` nem getter: 12 bájtos elemeket fűz egy
vektorhoz. A `0x004edf60` kulcs alapján metaadatot olvas; a
`0x0081e5a0` a rekord `+0x34` értékét átadja neki, majd a kapott két dwordöt
a `0x0098b650`-nek adja. Utóbbi az importtábla szerint
`FileTimeToSystemTime`-ot hív. Ez alátámasztja, hogy a `+0x34` a
készítési-idő/metaadat-útban is szerepel, de a konkrét metaadatnév továbbra
sem azonosított.

**A horgony forrása.** A `0x006999c0` konstruktor `[obj+0x738]` kezdőértéke
`-1`; a célzottan olvasott direkt író a `0x00824090` (`0x008242f0`). Az
író egyedisége ebben a körben nem lett teljes bináris-pásztázással
újraellenőrizve. Ennél a hívó flagjétől függően a
`0x008223e0` írja a `+0x40` out-paramétert, vagy a `0x008226e0` egy külön
vektorkimenetet tölt. Az első úton kapott érték kerül a horgonyba; a második
úton a `-1` marad, ezért a selector a rekord 0-t választja. A `0x008223e0`
`0x00448c90`/`0x00448a10` ellenőrzéseket használ; a `0x00448fb0` a
`[obj+0x2748]` indexelt 8 bájtos párját vagy a `+0x60/+0x64` tartalékpárt
adja. Hogy e két bemeneti ág melyike felel meg a Filmkészítő adott
felhasználói állapotának, és milyen képet jelöl a visszaadott kulcs, **NINCS
MEG**.

**Két út és fok.**

- **A — utasításszintű út:** a `0x0081c9b0` jelöltbejárása, súlyozása,
  minimuma és pick-zárása; a gettertörzsek és az `0x0081e220` darabszámíró.
- **B — független visszakötés:** a Ghidra-dekompilátum a `0x0081b800`-ban
  megerősíti, hogy `ordering=0` a `0x0081c9b0`-ba jut; az RTTI/vtable és a
  ctor/hívóút külön azonosítja a HOG/Neven slotokat, a horgony beállítását
  és a dátum-metaadat hívásláncát. Ez az út az osztály- és horgonyadatokkal
  egyezik, de önmagában nem méri meg, melyik jelölt nyer.
- A natív QEMU-próba szintetikus rekordokkal a `0x0081c9b0` jelöltvizsgáló
  részéig jutott, majd `SIGSEGV`-vel megállt `0x0081d404`-nél. A hám a
  `0x00873170` pontozó diszpécsert szándékosan stubolta, és az objektum
  jelöltmaszkja nem volt hitelesen felépítve; kimeneti fotóindex nem keletkezett.
  Ez **nem** független megerősítő mérés. A mérőadat-csomagban nem volt
  `4194`-hez címkézett natív próba; eredeti Picasa UI-mérés nem történt.

**Kiegészítő közvetlen QEMU-próba (2026-10-13; érvénytelen hám, nincs
kiválasztási eredmény).** A lokális harness közvetlenül hívta a
`0x0081c9b0`-at szintetikus, négy rekordos objektummal (`K=2`, csoportok
`[0,0,1,1]`), majd a `0x00873170` helyére konstans pontszámot visszaadó
helyettesítőt tett. Mindhárom próbaváltozat (későbbi alacsonyabb pont,
holtverseny, 1e8 feletti tartalék) eljutott a helyettesítőig, de az a
hívás negyedik argumentumát `0x10`-nek olvasta pontozókimeneti mutatóként,
és saját írásánál `SIGSEGV`-vel leállt. Ez a helyettesítő hívási szerződését
nem utánozta; a crash a hám hibája, nem a Picasa választóé. A próba ezért
nem szolgáltat pontszámcserés cáfoló eredményt, jelöltindexet vagy független
viselkedési bizonyítékot. Pontos pontszám-/rekord-hozzárendelés és a
selector natív kimenete **NINCS MEG**.

| Állítás/érték | Forrás |
|---|---|
| Horgony-keresés, spirál és aktuális csoport kizárása | bináris (`0x0081c9b0`, `0x0081d298`–`0x0081d428`) |
| Jelöltlista legfeljebb 100 eleme | bináris (`0x0081d4e4`, `0xc8` darabszámjelző) |
| Súlyozott összeg, szigorú minimum és tartalék | bináris (`0x0081d730`–`0x0081d7d9`) |
| Minimumhatár `100000000.0` | bináris (`0x00c7da00`) |
| HOG / Neven vtable-slot | bináris (RTTI `0x00cbdec4` / `0x00cbded4`; slotok `0x00873e40` / `0x008742a0`) |
| Horgony kezdőértéke és növekvő kiválasztásszám | bináris (`0x00699b95`, `0x0081e220`) |
| `+0x34` metaadat- és FileTime-út | bináris (`0x0081f270`–`0x0081f2a9`, import `FileTimeToSystemTime` `0x0092210a`) |
| QEMU-hám leállásának címe | mérés (szintetikus objektum: `SIGSEGV` `0x0081d404`; 2026-10-13-i hibás scorer-helyettesítő: írás `0x10` címre; kiválasztott index egyikből sem jött létre) |
| Eredeti Picasa által megtartott konkrét fotóindex | NINCS MEG |
| `+0x30/+0x34` formátumbeli mezőnév és a Neven-logika fotószemantikája | NINCS MEG |

**Cáfoló kísérlet.** Azt a feltevést próbáltam cáfolni, hogy az első
bemeneti kép mindig nyer. Az utasításút ellenpéldát ad a statikus
mechanikára: ha egy későbbi, bejárt jelölt pontja szigorúan kisebb az
aktuális minimumnál, a `0x0081d7b0`–`0x0081d7c4` ág lecseréli a nyertest.
A dinamikus ellenpróbához három szintetikus esetet futtattam (későbbi
alacsonyabb pont, holtverseny, 1e8 feletti tartalék); a hibás scorer-
helyettesítő `0x10` címen összeomlott, mielőtt pontszámot adott volna.
Ugyanazzal a bizonyítási mércével ez a QEMU-próba **nem** érvényes cáfoló
mérés: nincs kimeneti fotóindex vagy mért győztes. A „mindig első” állítás
statikus selector-mechanikai szinten cáfolt, a tényleges Picasa-kimenet
továbbra is **NINCS MEG**.

**Bizonyítottsági fok (G/2c):** a `ordering=0` választó **feltételes** — a
mechanika egy utasításszintű úton megvan, a második út a hívási szerződést,
a getterosztályokat és a horgony felállítását erősíti meg, de a valódi
jelöltkimenetet nem. A küszöbön belüli konkrét megtartott képek,
`+0x30/+0x34` rekordjelentése és a horgony felhasználói állapot szerinti
forrása **NYITOTT**.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `ordering=0`: horgony, kifelé spirál, aktuális csoport kizárása, súlyozott getter-minimum, szigorú `0x00c7da00` határ és spirálelső tartalék. | A `slideshow.py` színátlagos legközelebbi képet választ; nincs igazolt HOG/Neven-megfeleltetés vagy azonos horgonyforrás. | **#4182:** a csoportosítás külön implementálható a G szerinti etalonokkal. A megtartási algoritmust ne jelöljük eredetihűnek a getterek, a horgonyforrás és legalább egy eredeti Picasa-mérőmappa lezárásáig; ezután valós fotóindex-etalonokkal implementáljuk a fenti `ordering=0` lépéseket. `Kész, ha`: (1) 4–6 ismert időbélyegű fotón, legalább két csúszkaállásban egyezik az eredeti Picasa kimeneti fotóindexe; (2) a döntetlen/tartalék esetek is a spirálsorrendet adják; (3) az anchor a Picasából visszanyert bemenettel egyezik. |

**Nyitott.**

- `Ghidra-kör kell: 0x00824090 - a [obj+0x4e0] rekordlista forrása és a +0x30/+0x34 mezők tényleges upstream írói [blokkoló]`
- `Ghidra-kör kell: 0x008223e0 - a +0x738 horgonyként visszaadott kulcs forrása, és mely Filmkészítő állapotból ered [blokkoló]`
- `Ghidra-kör kell: 0x008226e0 - a második horgony-előkészítő ág kimeneti vektorának viszonya a +0x738 horgonyhoz [blokkoló]`
- `Ghidra-kör kell: 0x0048c440 - a Neven getter 0/1 értékének fotórekord-szemantikája [blokkoló]`
- Az eredeti Picasa Colab UI-futtatása 4–6 ismert készítési idejű képen, legalább két csúszkaállással; a konkrét nyertes fotóindex **NINCS MEG**. A hozzáférési út a jegy szerint a #181 videó-visszaadása.
- A `[obj+0x720]/[obj+0x728]` határtáblák nem-sentinel írói és a `ordering=1/2` költségút külön nyitottak maradnak.

**Új kutatási jegyjavaslatok:** nincs; a nyitott pontok a #4194 és a már jelzett #181 natív UI-mérés folytatásai.

#### G/3. Módválasztás, horgonyforrás és a Neven-kapu — a hívási gráf és a dekompilátum (2026-10-13, #4194 8. kör)

**Módszer és határ.** Az EXE nincs a gépen, ezért utasításszintű újraolvasás
nem futott (a Codespace hálózatot igényelne). Három adatforrás:
(a) a bináris index `xrefs.csv` **pozitív** közvetlen hívási élei (a
vtábla-hívások nem látszanak, negatív találatra nem építek); (b) a
`ghidra-koteg-2026-10-06b/` `00618050.c`, `00699cd0.c`, `00824090.c`,
`008223e0.c` dekompilátuma; (c) a `ghidra-koteg-2026-10-12c/008226e0.c`.
A (b) és (c) egyetlen dekompilátumforrás, ezért a horgony **utasításszintű**
íráslánca (`0x8242f0`) önálló második útként **nem** számít.

**1. Hívási élek (`xrefs.csv`, pozitív).**

| hívó → hívott | megjegyzés |
|---|---|
| `0x006175c0` → `0x0081b800` | az egyetlen közvetlen hívó; a G-ben szereplő `0x617810` hívóhely ennek a függvénynek a belsejében van |
| `0x00699cd0` → `0x00824090`, `0x00699cd0` → `0x006999c0` | a `0x699cd0` módkiosztó ágai |
| `0x00824090` → `0x008223e0`, `0x00824090` → `0x008226e0`, `0x00824090` → `0x006999c0` | mindhárom közvetlen él |

A `0x618050` → `0x699cd0` él vtábla-hívás (a `+0x4b4` objektum 0. slotja),
ezért az indexben nem látszik; a dekompilátum adja (b).

**2. A mód kiválasztása (`0x618050`, dekompilátum 96–125. sor; ⚠️ egy forrás).**
A `param_1` `int *`, ezért `param_1[0x13c]` a `+0x4f0` bájt, `(int)param_1 + 0x4f1`
a `+0x4f1`. Az alapmód 1 vagy 4 (`+0x134 ≠ -1`), vagy 7 (`FUN_00617110`, ha a
`+0x135` objektum szerint igaz). Ezután: `+0x4f0 ≠ 0` → **5**; különben
`+0x4f1 ≠ 0` → **6**. Mellékhatás: ha az alapmód 7 és `+0x4f1 = 0`, a
`+0x4f0` bájt **1-re áll** (`00618050.c` 124. sor), és ez a
következő építéseknél megmarad.

- `0x699cd0(1..4)` → `0x68c880` (0x498 bájtos objektum);
- `0x699cd0(7)` → `0x6999c0` (0x770 bájtos objektum, ctor, a horgony kezdőértéke `-1`);
- `0x699cd0(5|6)` → `0x824090` (listaépítő, a horgonyág ide tartozik).

⚠️ **Ütközés a 2.5/F-fel:** a 2.5/F szerint a `+0x4f0`/`+0x4f1` „függőben lévő,
még nem alkalmazott Opciók-állapot”. A dekompilátum szerint a mód-7 építés
maga is beállítja a `+0x4f0`-t, tehát a „függőben” jelentés nem egyedül áll.
Ezt utasításszinten kell megerősíteni (nyitott).

**3. A horgony (`0x824090` / `0x8223e0` / `0x8226e0`, dekompilátum).**
- A `0x824090` `param_2` bájtja szerint: `0` → `0x8223e0`, nem nulla → `0x8226e0`.
  Ezt a bájtot a `0x699cd0` hívóhelye adja át; a dekompilátum argumentum nélkül
  mutatja a hívást, ezért a flag forrása **nyitott**.
- A `0x8223e0` 2. argumentuma `[+0xeac] → +0x3c0`, az album-azonosító (alap `-1`).
  A horgony-lokálist (`param_1`, a `0x824090` 44. sora) a `0x8223e0` a saját
  kimeneti vektorának **0. elemével** tölti (`*param_3 = *puVar3`,
  `008223e0.c` 122–123. sor); üres vektornál a `-1` marad (`uVar6 >> 1 == 0`).
- A `0x8226e0` nem tölti a horgony-lokálist; a `&local_28` vektort adja. A
  horgony így `-1`, azaz a 0. rekord.
- A `0x824090` dekompilátumában a horgony-lokál **csak íródik**, olvasása nem
  látszik. Az a `0x8242f0` `movl %edx,0x738(%ebp)` íráson át jut a `0x81c9b0`-ba,
  és ezt a dekompilátum nem mutatja (G/2c, utasításszint).

**4. A Neven-kapu (új a G/2c-hez képest).** A `0x824090` dekompilátuma szerint
a Neven-súly (`_DAT_00c7c838`) akkor kerül be, ha (i) a
`Preferences\SmartMultiPersonTrans` igaz, **és** (ii) a `+0x6f4` bájt
(`piVar6[0x1bd]`) nem nulla. A `+0x6f4` csak akkor lesz 1, ha a `0x448c90` /
`0x448a10` ellenőrzés hamis (a találatnál korai `goto` kihagyja), vagy a
`0x8226e0` ágon fut. A G/2c csak az (i) feltételt említi. ⚠️ Egy dekompilátumon alapul.

**5. Mit ad ez a kiválasztási szabályhoz.** Fotóindex nem jött ki; a
„melyik marad” kérdés változatlan. Feltételes hipotézisek (nem bizonyítékok):
- mód-7 első építésnél a horgony `-1`, a spirál a 0. rekordtól indul (a
  `0x6999c0` ctor kezdőértékére támaszkodva; a rekordlista feltöltése nincs olvasva);
- mód-5 `flag = 0` esetén a horgony az album-vektor 0. eleme, ha az nem üres.

**6. Nyitott — a következő konkrét kör.**
1. A `0x699cd0` hívóhelye a `0x824090` flag-argumentumával (melyik horgonyág fut).
2. A `0x6999c0` törzse: a `0x4e0` lista feltöltése, a `+0x738 = -1` kezdőérték, és hogy a 7-es mód ezt használja-e.
3. A `0x618050` 96–125. sorának utasításszintű megerősítése: íródik-e a `+0x4f0` a mód-7 ágban (2.5/F ütközés).
4. A `0x8242f0` körüli utasítások és a `0x81c9b0` `+0x738`-olvasása: a horgonykapcsolat utasításszintű igazolása.

**Bizonyítottsági fok (G/3):**

| Állítás | Forrás | Fok |
|---|---|---|
| A `0x6175c0` → `0x81b800`, `0x699cd0` → `0x824090`/`0x6999c0`, `0x824090` → `0x8223e0`/`0x8226e0` élek | bináris index (pozitív élek) | **megerősített** |
| A mód 5/6/7 kiosztása és a `+0x4f0` mód-7 általi beállítása | dekompilátum (`00618050.c`) | **feltételes** (egy forrás); ellentmond a 2.5/F „függőben” jelentésének |
| A horgony a `0x8223e0` vektorának 0. eleme, üres/`0x8226e0` esetén `-1` | dekompilátum (`008223e0.c`, `008226e0.c`) | **feltételes**; a `0x738` lépés csak utasításszinten |
| A Neven-súly a `+0x6f4` kapuval is feltétel | dekompilátum (`00824090.c` 52–79. sor) | **feltételes** |
| A `0x824090` flag-argumentuma | — | **NYITOTT** |
| A konkrét megtartott fotóindex | — | **NYITOTT** |

#### G/3b. A 9. kör (2026-10-13): utasításszintű olvasat az eredeti EXE-n — módválasztás, horgony, hívóhely (#4194)

**Helyesbítés a G/3-hoz.** A G/3 azt írta, hogy az EXE nincs a gépen. Ez téves:
a `~/Documents/PicasaPy/research/copy_Picasa_3_7/Picasa3/Picasa3.exe` megvan
(10 160 456 bájt, PE32/i386, ImageBase `0x400000`, SHA-256 kezdete
`644b7bec89a2e4d5`). Ezért most utasításszintű olvasat készült: a `0x699cd0`,
`0x618050`, `0x824090`, `0x8223e0`, `0x81c9b0` törzsét capstone 5.0.7-tel
(a `~/picasapy-agent/venv`) disassemblálva olvastam. A segédszkriptek a
munkafán kívül, a scratchpadban vannak; a repóba nem kerültek.

**Módszer.** (a) E8/E9 közvetlen hívóhely-pásztázás a `.text`-re (nem az
xref-indexből); (b) a vtábla-hívások azonosítása a `.rdata` és a konstruktorok
`mov dword ptr [reg+X], imm32` alakú vtábla-beállításainak bájt-keresésével;
(c) a `+0x738`, `+0x4f0`, `+0x4f1` mezők íróinak bájt-pásztázása a teljes
`.text`-en (index-független). A `0x81c9b0` spirálja és pontozó ciklusa a
G/2c szerint maradt; ebben a körben a horgonykeresést és a minimumot újra
olvastam.

**1. A hívóhely és a flag-argumentum.**

- A `0x699cd0`-ra nincs közvetlen E8/E9 hívás. A hívóhely a `0x618247`
  (`call eax`, `eax = [[ecx]]`, `ecx = [panel+0x4b4]`), a mód a `push esi`.
- A `[panel+0x4b4]` másodlagos interfész. A `0x69830d`-es konstruktor a
  `[obj+0x14]` helyre tölti a `0xca7b7c` vtáblát, amelynek 0. slotja a
  `0x699cd0`. A `this` tehát az objektum `+0x14` címe: másodlagos vtábla =
  eltolt this. A primer vtábla (`0xca7b38`) 0. slotja más (`0x6996d0`, dtor),
  ezért a hívás nem azon megy. ⚠️ A gyári hívás (`0x618191`, a
  `0xd49f68` objektum +0x14 vtáblaslotja) visszatérési értékét nem követtem
  végig; a `+0x14` következtetés a vtábla-kép és a konstruktor alapján áll.
- A `0x699cd0` mód-ágai: mód 5 és 6 a `0x69a305` / `0x69a308` ágon mennek:
  `edx = [this+0x10]`, `cl = (esi == 6)`, majd `call 0x824090`. Tehát
  `arg1 = [this+0x10]`, `arg2 = (mód == 6)`. A `0x824090`-ben ezt igazolja
  az `arg1` (`[esp+4]` a belépéskor, `mov ebx,[esp+0x34]` a `push ebx` után)
  és az `arg2` (`cmp byte ptr [esp+0x44],0` a négy `push` után).
- A `0x824090` 0x8240e9. sora: `arg2 == 0` → `call 0x8223e0` (horgony-
  vektor), `arg2 != 0` → `call 0x8226e0`. **A flag forrása tehát: a mód
  (6 → 1, 5 → 0).** A G/3 „nyitott” pontja ezzel lezárva.
- A `0x824090` maga építi a `0x770` bájtos objektumot (0x8240b4–0x8240e1:
  foglalás + `0x6999c0`), és `mov eax, ebp`-pel ezt adja vissza. A `0x618247`
  eredménye a `[panel+0x4b8]`-ba kerül.

**2. A mód kiválasztása (`0x618050`, 0x618209–0x618247).**

| `[panel+0x4f0]` | `[panel+0x4f1]` | mód | `arg2` a `0x824090`-nek | horgony-út |
|---|---|---|---|---|
| ≠ 0 | – | 5 | 0 | `0x8223e0` |
| 0 | ≠ 0 | 6 | 1 | `0x8226e0` |
| 0 | 0 | alap: `0x617110` igaz → 7; különben `[panel+0x4d0] == -1` → 1, egyébként 4 | – | 7: nincs `0x824090`; 1/4: a `0x699cd0` 1–4 ága (nem olvastam) |

- A `0x618209`–`0x618223` sorok a mód-választás; a 0x4f0/0x4f1 bájtok az
  `ebp`-hez, vagyis a `0x618050` panel-objektumhoz tartoznak (nem az
  `[panel+0x4b4]` objektumhoz).
- **Mellékhatás (megerősítve):** a `0x618259`–`0x618270` sorokban, ha a
  dispatch után `esi == 7` és `[panel+0x4f0] == 0` és `[panel+0x4f1] == 0`,
  akkor `[panel+0x4f0] := 1`. Az első mód-7 építés után a következő
  építés már mód 5. Ez árnyalja a 2.5/F „függőben lévő, még nem alkalmazott”
  értelmezését: a bájt a tényleges építés után is beáll.

**3. A horgony (`0x824090` belseje).**

- A `[obj+0x738]` kezdőértéke `-1` (konstruktor, `0x699b9b`).
- A `0x824090` `[esp+0x40]` lokálisa a horgony-kimenet; `0x8240f6`-ban `-1`.
  Mód 5-nél a `0x8223e0` ezt az out-paramétert kapja (`lea ecx,[esp+0x40]`).
- A `0x8242f0`: `mov dword ptr [ebp+0x738], edx`, ahol `edx = [esp+0x40]`
  (a `0x8242e4`-ben). Ez a `+0x738` egyetlen közvetlen írása a `0x824090`
  családon belül.
- A `0x8223e0` horgony-írása (`0x822668`–`0x822675`): ha az `esi` (a
  `0x8225cb`-es `call ebp` eredménye) nem nulla, akkor `*anchor = [[edi]]`, vagyis
  a kimeneti vektor 0. eleme; ha nulla, az `-1` marad (`0x82265d` `je
  0x8226c0`). A `call ebp` függvénye (`[0xc40284]`, a `.rdata`-ban) nincs
  azonosítva.
- A `0x8226e0`-nak csak a `this = ebx` és a `&[esp+0x14]` kimenet adódik
  át (`0x824104`–`0x824106`); a `[esp+0x40]` nem írható belőle. Mód 6-nál a
  horgony tehát `-1`.
- A `0x824144`-ben a lista-kitöltő ág csak akkor fut, ha a `[esp+0x18]`
  feltétel teljesül (`test dword ptr [esp+0x18], 0xfffffffe`; `je 0x824296`).
  A `[esp+0x18]` jelentése nincs dekódolva; ezért a „üres kimenet → nincs
  lista” olvasat feltételes.

**4. A kiválasztó bemenete (`0x81c9b0`, újraolvasva).**

- Korai kilépés `0x81e0f2` (lokálisok felszabadítása, `ret 0x14`, nincs
  kiválasztás): ha `[obj+0x508] >> 1 == 0`, vagy a `[obj+0x504]` vektor
  valamely eleme 0, vagy az első elem `+0xc` mezője ≤ 1 (`0x81c9d3`–`0x81c9ff`).
- Horgony (`0x81ca05`–`0x81ca33`): `[obj+0x738] == -1` → 0. index. Különben
  a `[obj+0x4e0]` rekordok (elemméret `0x38`) `+0x30` kulcsai között az első
  egyezés indexe; egyezés nélkül a 0. index.
- Minimum (`0x81d7b0`–`0x81d7d9`): `fcompp` + `ah & 0x41`; csak szigorú
  `<` cserél, így holtversenyben a korábban bejárt jelölt marad; ha egyik
  sem nyer a kezdőértékhez képest, a spirál első eleme a tartalék.
- Kimenet (`0x81d832`): a nyertes rekord `+0x30` kulcsa kerül a kimeneti
  vektorba; a nyertes index az új középpont (`0x81d8a0`).

**5. Írók (bájt-pásztázás, index-független).**

- `+0x738`: a `0x699cd0`-osztály objektumán belül két író van: a konstruktor
  (`0x699b9b`, `-1`) és a `0x8242f0` (anchor). A `0x7a9375` és a `0x7a97f3`
  más osztály (vtábla `0xcb6e98`, `+0x6bc`/`+0x53c` mezők): nem ez az
  objektum. A címet vevő (`lea`) hivatkozások osztálya (például `0x412a6b`,
  `0x413155`, `0x7faca4`, `0x7fb6d9`, `0x7ffed5`) nincs azonosítva, ezért
  a pointeres írás nem zárható ki.
- `+0x4f0` és `+0x4f1`: a bájt-pásztázás zajos (sok osztály használ ilyen
  eltolást). A `0x618050`-hez tartozó írások: a `0x618270` (`+0x4f0 := 1`,
  mód-7) és a `0x612aa4`/`0x612aaa` (`+0x4f0 := bl`, `+0x4f1 := bl`, egy
  nullázó/init-rutinban, a `bl` a `0x6129f2` `xor ebx,ebx`-ből 0). A
  `0x612860`-as rutin és a `0x618050` ugyanazé-e az osztálya: nincs
  igazolva. A `0x618209`-es olvasás `+0x4f1`-forrása ezért csak
  „init-nullázás + nem azonosított írók” szinten áll.

**6. A kérdés: melyik fotó marad meg.** A mechanizmus most már utasításszinten
áll; a konkrét fotó nem.

- A kiválasztás rekordkulcsokon (`+0x30`) fut, a kimenet ezek listája.
- Kezdő középpont: mód 5-nél, ha az album-vektor nem üres és `esi ≠ 0`, az
  album-vektor 0. kulcsának rekordja; egyébként (mód 6, vagy üres vektor)
  a `[obj+0x4e0]` lista 0. eleme.
- A spirál (+1, −1, +2, −2 …, legfeljebb 100 jelölt, a G/2c szerint) csak
  a középponttól eltérő csoportból vesz jelöltet; a pontszám a regisztrált
  getterek súlyozott összege; szigorú minimum, döntetlennél a korábbi;
  a nyertes az új középpont.
- Következmény: a küszöbön belüli csoportban **a megtartott kép nem
  „az első” és nem „az utolsó” általános szabállyal**. A döntő a
  `[obj+0x4e0]` lista sorrendje (a feltöltő `0x823620` még nincs olvasva) és
  a getter-pontszámok iránya.
- **Visszavont hipotézis (G/3 5. pont):** „mód-7 első építésnél a horgony
  `-1`, a spirál a 0. rekordtól indul”. A mód-7 ág nem hívja a `0x824090`-et,
  így a `[obj+0x4e0]` lista ott üres (a konstruktor nullázza), és a
  `0x81c9b0` korai kilépéssel tér vissza. Más feltöltő nincs azonosítva;
  ezért a mód-7 kiválasztás „nincs kimenete” olvasat feltételes.

**Bizonyítottsági fok (G/3b):**

| Állítás | Forrás | Fok |
|---|---|---|
| A `0x6999c0` ctor: `+0x738 = -1`, `+0x500 = 1`, `+0x4e0..0x4fc = 0` | utasítás | **megerősített** |
| A `0x699cd0` hívóhelye: `0x618247`, a `0xca7b7c` másodlagos vtábla 0. slotja | utasítás + `.rdata` + konstruktor-immediátum | **megerősített** (a gyári visszatérés követése: feltételes) |
| Mód-választás: `[+0x4f0] ≠ 0 → 5`, `[+0x4f0] = 0 ∧ [+0x4f1] ≠ 0 → 6` | utasítás (`0x618209`–`0x618236`) | **megerősített** |
| Mód-7 beállítja `[+0x4f0] := 1` (`0x618270`) | utasítás | **megerősített** |
| `0x824090` flag = `(mód == 6)`; `0` → `0x8223e0`, `≠ 0` → `0x8226e0` | utasítás (`0x69a308`, `0x8240e9`) | **megerősített** |
| `[obj+0x738] := [esp+0x40]` (`0x8242f0`) | utasítás | **megerősített** |
| Horgony = kimeneti vektor 0. kulcsa, ha `esi ≠ 0`; egyébként `-1` | utasítás (`0x822668`–`0x822675`) | **megerősített**; az `esi` feltétel (`[0xc40284]`) feltételes |
| Mód 6 horgonya `-1` | utasítás | **megerősített** |
| `0x81c9b0` horgonykeresés, korai kilépés, szigorú minimum | utasítás | **megerősített** |
| `+0x738` írói a `0x699cd0`-osztályon | bájt-pásztázás | **feltételes** (pointeres írók nincsenek kizárva) |
| `[+0x4f1]` írói (a `0x612aaa` nullázó, több nem azonosított) | bájt-pásztázás | **NYITOTT** (csak az init-nullázás látszik) |
| `[obj+0x504]` feltöltője | — | **NYITOTT** |
| `0x617110` (mód-7 feltétel) | — | **NYITOTT** |
| Konkrét megtartott fotóindex | — | **NYITOTT** |

**Nyitott pontok, és mi zárná le őket.**

1. `[panel+0x4f1]` 1-re állító írói: a `0x612860`-as rutin osztályának
   azonosítása, és a `0x618050` osztályán belüli bájt-pásztázás vagy
   dekompilátum. Ez dönti el, mikor lesz mód 6.
2. `0x823620` és a `[obj+0x504]` feltöltője: a `[obj+0x4e0]` lista sorrendje
   (időrend-e). Ez a legfontosabb a „melyik” kérdéshez.
3. A `call ebp` (`[0xc40284]`) azonosítása: mikor nem nulla az `esi`, vagyis
   mikor lesz a horgony az album-vektor 0. eleme.
4. A `0x824144` `[esp+0x18]` feltétele: dekódolás.
5. A HOG/Neven getter visszatérési értékének iránya: a minimum a
   legkisebb hasonlóságot vagy a legkisebb távolságot választja-e.
6. A `0x617110` (mód-7 feltétel) olvasata.
7. Natív viselkedésmérés: a QEMU-hám nem ad kimenetet (G/2c); a Wine alatti
   Picasa nem készít filmet (picasa-colab-jobs #106). Mérés csak Windows-
   gépen lehetséges.

**Kész, ha (a #4194 jegy szerint) — állapot: NEM teljesül.**

- [ ] 1. feltétel: a kiválasztási szabály a specben, két független úttal — a
  mechanizmus megvan, a konkrét megtartott fotó nincs; a jegy nem zárható.
- [ ] 2. feltétel: a fejlesztői teendő kimondva (Eredeti | Nálunk | Teendő).
  Lásd lent.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Mód 5/6 horgony, `0x81c9b0` spirál, szigorú minimum, `+0x4f0` mód-7 beállítás. | A `slideshow.py` színátlagos legközelebbi képet választ; a film-szűrés nincs. | **#4182:** a csoportosítás (G) és a horgony-szabály (G/3b) implementálható; a megtartási lépést csak az 1–3. nyitott pont lezárása után szabad eredetihűnek nevezni. |

#### G/3c. A 10. kör (2026-10-13): a [obj+0x4e0] rendezése, a horgony-feltétel, a `+0x4f0/+0x4f1` írói, az IAT-név (#4194)

**Módszer.** Utasításszintű olvasat az EXE-n (`research/copy_Picasa_3_7/Picasa3/Picasa3.exe`,
capstone a `~/picasapy-agent/.venv`-ben, `pefile` a PE-fejhez és az importtáblához).
Bájt-pásztázás a teljes `.text`-en (index-független). A segédszkriptek a scratchpadban
vannak, a repóba nem kerültek. Natív QEMU-futás nem készült (a G/2c szerint a szintetikus
rekordokkal a kiválasztó a végső indexig nem jut el).

**1. A `[obj+0x4e0]` lista feltöltése és rendezése.**

- Egyetlen közvetlen hívó: `0x00824090` → `0x00823620` a `0x0082417d`-ön (E8-pásztázás).
- Argumentumok (`0x823620` belépési stackje): arg1 = a helyi forrásvektor (`lea eax,[esp+0x18]`),
  arg2 = `&[obj+0x4e0]` (cél; a darabszám `[+4]>>1`, elemméret `0x38`), arg3 = `&[obj+0x4f8]`.
  A `0x823620` a `0x82368e`-hez közel a `0x8256a0` rendezőt hívja a helyi `[esp+0x3c]` vektoron.
- `0x8256a0`: alulról felfelé összefésülő rendezés (`0x825930` az összefésülés), a
  comparátor a `0x819570`.
- `0x819570`: a két elem kulcsát a `0x4edf60` olvassa (zárolt gyorsítótáras kulcsolvasó; a
  kimenet a bejegyzés `+4…+0x10` dwordjeit másolja, a 8 bájtos kulcs az `+0xc/+0x10`-en van).
  A kulcs összehasonlítása **előjel nélküli 64 bites** (`ja`/`jb`/`jae`): −1, ha `k1 < k2`,
  különben +1. A rendező csak `< 0` esetén cserél ⇒ a sorrend **dátum szerint növekvő**.
- A kulcs azonossága: ugyanaz a `0x4edf60` dátumolvasó, amelyet a G-szakasz `0x0081ae10`
  csoportosítója használ (`+0x34` mező). A „FILETIME” azonosítás a G-szakaszban mért
  (QEMU-s) tény; itt csak a rendező kulcsának típusát és irányát igazoltam.
- **Nem követtem végig:** a `0x8256a0` kimenetének `arg2`-be jutását (a `0x823620` 0x82392e–0x823b76
  tartománya). Ezért a „a lista tényleg rendezett” állítás **feltételes**.
- **Nyitott:** egyenlő dátumnál a sorrend (a comparátor `+1`-et ad egyenlőségnél; a
  összefésülés stabilitása nincs ellenőrizve).

**2. Horgony-feltétel: a `call [0xc40284]` azonosítva.**

- A `0x00c40284` IAT-slot neve: **KERNEL32.dll!GetCurrentThreadId** (pefile-lel, az importtáblából).
- Hívóhelyek: `0x008225cb` (a `0x8223e0` belsejében), `0x004edf71` (a `0x4edf60`-ban),
  `0x00823b53` (a `0x823620`-ban). Mindhárom a szál-azonosítót a tulajdonos-ellenőrző
  mintához használja (`[obj+0x20]` / `[esp+0x38]` tulajdonos, `+0x24` / `+0x3c` számláló).
- A `0x8223e0` horgony-ága (`0x822668`): `test esi,esi` után, ha `esi ≠ 0`, a horgony a
  `this`-vektor 0. eleme (`mov eax,[edi]; mov ecx,[eax]`, `edi = this`). A szál-azonosító
  felhasználói szálon nem nulla, tehát a gyakorlatban a feltétel mindig teljesül; üres
  vektornál a `-1` marad. Ezzel a G/3b „`[0xc40284]` nyitott” pontja lezárult.

**3. A `+0x4f0` / `+0x4f1` bájtok írói (bájt-pásztázás, `mov byte [reg+disp]` alakok).**

| cím | művelet | kontextus | fok |
|---|---|---|---|
| `0x0057cc69` | `[ebx+0x4f0] := 1` | a `cmp ebp,0x9d59` ág (`0x57cc61`) | erős (utasítás) |
| `0x0057cc7a` | `[ebx+0x4f1] := 1` | a `cmp ebp,0x9d5a` ág (`0x57cc72`) | erős (utasítás) |
| `0x00612aa4`, `0x00612aaa` | `[edi+0x4f0] := bl`, `[edi+0x4f1] := bl` (bl = 0) | a `0x612a80` nullázó (a `+0x4e0` mellett) | erős (utasítás) |
| `0x00618270` | `[ebp+0x4f0] := 1` | mód-7 mellékhatás (G/3b) | erős (utasítás) |
| `0x004ec587` | `[reg+0x4f0] := 1` | nem azonosított osztály | feltételes |
| `0x004ec027`, `0x004f6a8f` | `[reg+0x4f0] := 0` | nem azonosított osztály | feltételes |
| `0x004e4550` | `[ebx+0x4f0] := bl` | nem azonosított | feltételes |

- A `0x9d59` / `0x9d5a` azonosítók a **makemoviepanel vezérlő-azonosítói**: a `0x0056f7a0`
  állapotfrissítő a `0x56f830` ágban ugyanezekkel az azonosítókkal hívja a `call ebx`-et
  (a `0x9d30`, `0x9d62`, `0x9d5c`, `0x9d58` társaságában). Ezért a `+0x4f0` / `+0x4f1` nem
  számított állapot, hanem **egy vezérlő bekapcsolt állapotából** íródik.
- **Nyitott:** melyik vezérlő a `0x9d59` és a `0x9d5a` (a felirat). A fájlban nincs MENU-erőforrás;
  a dialógus-leírás a REGISTRY-erőforrásban vagy a `.tre`-ben lehet — nincs megnézve.
- A mód-választás (`0x618209`–`0x618236`) így: `[+0x4f0] ≠ 0` → 5, különben `[+0x4f1] ≠ 0` → 6.
  Ez utasításszinten megerősített, de a bejövő érték **vezérlőből** jön, nem számításból.

**4. A kiválasztó összehasonlítása (`0x81d7b0`–`0x81d7d9`, megerősített).**

- A `fcompp` a `best` és a `v` (jelölt-összeg) között hasonlít; csak `best > v` esetén cserél
  (`test ah,0x41` ⇒ `best ≤ v` esetén marad). **A kisebb összegű jelölt nyer**, döntetlennél a
  korábbi marad. Ez a G/2c „szigorú minimum” állítását megerősíti.
- **Nyitott:** a getterek (HOG `0x00873e40`, Neven `0x008742a0`, a `0x00873170` összegző) iránya:
  távolság (a kisebb = hasonlóbb) vagy hasonlóság (a kisebb = kevésbé hasonló). A minimum
  mindkét esetben a kisebbet választja, tehát a **választás iránya** a getter jelentésétől függ,
  és azt ebben a körben nem fejtettem vissza.
- **Nyitott:** a csoportkizárás iránya. A G-szakasz szerint a spirál csak „a középponttól eltérő
  csoportból” vesz jelöltet, a `0x81d41d`–`0x81d428` ág viszont az aktuális jelölt csoportjával
  egyezőt hagyja ki. Hogy ez a középpont vagy a jelölt csoportja, nincs egyértelműen igazolva.

**5. A szabály állása (feltételes, nem zárt).**

1. Csoport: a küszöb alatti szomszédos csoportosítás (G, megerősített).
2. Rendezés: a `[obj+0x4e0]` dátum szerint növekvő (feltételes, lásd 1.).
3. Középpont (`ordering = 0`): mód 5 (`0x9d59`) → a `this`-vektor 0. eleme, ha nem üres; mód 6 (`0x9d5a`) vagy üres → index 0 (a legkorábbi dátumú rekord, feltételes).
4. Jelöltsor: kifelé spirál (+1, −1, +2, −2 …), legfeljebb 100 jelölt (G/2c).
5. Pontszám: a getterek súlyozott összege; a kisebb nyer, szigorú minimum, döntetlenre a korábbi (megerősített); a getter-irány **nyitott**.
6. Kimenet: a nyertes rekord `+0x30` kulcsa (G/2c).

**Bizonyítottsági fok (G/3c):**

| Állítás | Forrás | Fok |
|---|---|---|
| `call [0xc40284]` = `KERNEL32.dll!GetCurrentThreadId` | import-tábla (pefile) | **megerősített** |
| A `0x823620` egyetlen közvetlen hívója a `0x824090` (`0x82417d`) | E8-pásztázás | **megerősített** (vtábla-hívás nincs kizárva) |
| A `[obj+0x4e0]` feltöltő rendezője 64 bites előjel nélküli, dátum-kulcsú összefésülés, növekvő irány | utasítás (`0x819570`, `0x8256a0`, `0x825930`) | **megerősített** a comparátorra; **feltételes** a lista végső sorrendjére |
| A horgony a `this`-vektor 0. eleme, ha a TID ≠ 0 | utasítás (`0x822668`) | **megerősített** |
| `+0x4f1 := 1` a `0x9d5a` ágon (`0x57cc7a`) | utasítás | **megerősített** (a vezérlő neve **nyitott**) |
| `+0x4f0`, `+0x4f1` többi írója | bájt-pásztázás | **feltételes** (zajos minta) |
| `0x81d7b0` szigorú minimum | utasítás | **megerősített** |
| Getter-irány (távolság vagy hasonlóság) | — | **NYITOTT** |
| Csoportkizárás iránya | — | **NYITOTT** |
| Egyenlő dátum sorrendje | — | **NYITOTT** |
| Konkrét megtartott fotóindex | — | **NYITOTT** |

**Nyitott pontok és a lezárásuk útja.**

1. A getter-irány: a `0x873170` → `0x873e40` (HOG) és `0x8742a0` (Neven) törzse; a visszatérési érték jelentése (a kisebb = hasonlóbb?).
2. A `0x9d59`/`0x9d5a` vezérlő felirata: a makemoviepanel dialógus-leírása (REGISTRY-erőforrás vagy `.tre`).
3. A `0x8223e0` mód-5 forrásvektora: a `[esp+0x14]` kitöltője mód 5-nél nincs igazolva (a `0x8223e0` nem kap vektor-kimenetet).
4. Egyenlő dátumú rekordok sorrendje: a `0x8256a0` összefésülés stabilitása, vagy a `0x825930` ágai.
5. A csoportkizárás: a `0x81d41d`–`0x81d428` ág melyik csoportot zárja ki.
6. Natív viselkedésmérés: Windows-gép kell (Wine alatt a Picasa nem készít filmet, picasa-colab-jobs #106).

#### G/3d. A 11. kör (2026-10-13): a getterek iránya, a csoportkizárás, a rendező stabilitása, a mód-5 forrásvektor (#4194)

**Módszer és határ.** Utasításszintű olvasat az EXE-n (`research/copy_Picasa_3_7/Picasa3/Picasa3.exe`,
capstone + pefile; a segédszkriptek a scratchpadban vannak, a repóba nem kerültek). A kiválasztó
ágait a G/3c óta újraolvastam. Második út: a `ghidra-koteg-2026-10-12/00823620.c` és a `0081b800.c`
dekompilátuma (a kiíró ciklus és a hívási argumentumok). Natív futás nem készült. A getterek
(HOG, Neven) és a rekognáló törzse csak az EXE-ből olvasott, egy úton állnak.

**1. A getterek iránya — MEGERŐSÍTVE: mindkettő TÁVOLSÁG (kisebb = hasonlóbb).**

- **HOG** (`0x00873e40`, argumentumok `a`, `b`, `this` = `ecx`): a `[this+0x4c]` jelzőtömb szerint
  kiszámolja a két rekord vektorát (`0x873cb0`), majd a visszatérési érték
  `Σ_j (A_j − B_j)² / (A_j + B_j + ε)`, `ε = 1e-8` (a `0xcf4bd8` double). A vektor hossza
  `[+0x4] >> 1`, az elemek `float`-ok. A `0x873e40` törzsében nincs `fsqrt`: ez χ²-típusú
  **távolság** (hisztogram-összehasonlítás), azonos vektornál 0.
- **Neven** (`0x008742a0`): kiindulás `1.0`. (i) Ha a `[this+0x34]` klaszter-azonosítók
  megegyeznek és nem nullák, a visszatérés `1 − 1.0 = 0` (korai ág `0x8742c2`). (ii) Egyébként
  `0x48c440` (rekognáló). Hiba vagy arc-hiány esetén a kimenet 0, így a visszatérés `1.0`
  (maximális távolság). Sikernél a `0x48c440` kimeneti paramétere lesz `x` (a `0x3c`-es vtábla-slot
  írja, a törzsét nem olvastam), és a visszatérés `1 − x`. Tehát Neven = `1 − hasonlóság`,
  kisebb = hasonlóbb. ⚠️ A `0x3c` slot törzse nincs igazolva, ezért a „hasonlóság” jelleg feltételes.
- **Következmény:** a `0x81d7b0` minimum-választója (legkisebb súlyozott összeg) a **legkisebb
  távolságú** jelöltet viszi, azaz a középponthoz legjobban hasonlítót. Súlyok: HOG `1.0`,
  Neven `0.4f` (`0xc7c838`, kétszer ellenőrizve), a Neven-kapu a G/3 4. pontja szerint.

**2. A csoportkizárás — MEGERŐSÍTVE: a KÖZÉPPONT csoportja.** (A G/3c 5. nyitott pontja lezárva.)

- `0x81d41d`–`0x81d428`: `esi = G[j]` (a jelölt csoportja), `if (esi == G[c]) → 0x81d4ca` (kihagyás).
  Itt `ecx = c` végig: a `0x81d3d4`/`0x81d3d8` és a `0x81d3a2`/`0x81d3a6` ágak is a `c`-t töltik.
- `G` = `*[ebp+0x14]` = `[this+0x6cc]`. A `0x81b800` (`piVar10 = this+0x1b3` ha `param_4 ≠ 0`) adja át,
  és a csoport-azonosítót a `0x81ae10` írja (`0x81ae48`, `0x81ae96`: `mov [esi+0x6cc], …`).
- Ugyanebben a szakaszban további kizárások: a már kiválasztott jelölt (`[esp+0x48]` bájt, `0x81d404`) és
  a zászlós elem (`*[ebp+0x10]`, `0x81d40e`), ahol a zászló a `[this+0x6dc]`/`[this+0x6e4]` mögött áll.
- ⚠️ **Nyitott:** a `0x81d338`–`0x81d390` határ-ellenőrzés a `[this+0x708]` tömböt olvassa. Ez a 0x6999c0
  konstruktorban `0`-ra áll (`mov [edi+0x708], ecx`, `ecx = 0`), és ordering 0 ágon nem látszik írója
  (a `0x874e40` írja, de csak nem nulla ordering ágon fut). Ha az ág elérhető, null-olvasás lenne; ezt
  futás nem igazolta, ezért **nyitott**.

**3. Egyenlő dátumkulcs — MEGERŐSÍTVE: a rendező stabil, nincs másodlagos kulcs.**

- A kulcs 64-bit előjel nélküli dátum (`0x4edf60`). A `0x819570` összehasonlító `−1`-et ad, ha `k1 < k2`
  (a `0x8195ab`–`0x8195dc` ágak: a magas dword `ja`/`jb`, alacsony `jae`), **egyenlőnél `+1`**.
- A `0x825930` összefésülés a jobb futamelemet csak akkor veszi előre, ha `cmp(jobb, bal) < 0`
  (`0x825962` `jl`); egyenlőnél a **bal** (korábbi) marad.
- A páronkénti kezdő lépés (`0x825740`–`0x825771`) csak `cmp(második, első) < 0` esetén cserél.
- **Következmény:** egyenlő dátumnál a forrásvektor eredeti sorrendje marad. A másodlagos kulcs tehát
  a **forrásvektor pozíciója**, nincs más kulcs. Ez a forrás-generátortól függ (G/3d 4. pont), ezért a
  „melyik marad” kérdésben a sorrend a forrás ismeretéig nyitott.
- Feltételes: az `0x8256a0` futamszintű ciklusai (`0x825790`, `0x825801`) nincsenek végigkövetve, csak a
  két összefésülési szabály igazolt.

**4. A mód-5 forrásvektor töltője — MEGERŐSÍTVE a töltő, RÉSZBEN a tartalom. (A G/3c 3. nyitott pontja.)**

- **Helyesbítés G/3c-hez:** a `0x8223e0` MEGKAP vektor-kimenetet. A `0x8240fe` `lea eax,[esp+0x14]`
  után a `0x824114` hívás (mód 5, `flag == 0`) `eax`-ban hagyja a címet, így `0x8223e0` `edi = eax` a
  forrásvektor (`{ptr, size}`). Mód 6-nál a `0x8226e0` ugyanezt `push eax`-szal kapja.
- A `0x8223e0` kitöltési ágai (`0x822402`–`0x822521`), sorrendben:
  (a) ha `[builder+0xeac]` album-objektum és `[album+0x3c9] ≠ 0`: a vtábla `[0xdc]` slotja (`push 1; push edi`);
  (b) különben ha `[builder+0xea8] ≠ 0`: `0x7166c0(…, 1)`; nulla visszatérésnél és nem üres vektornál tovább;
  (c) különben, ha a vektor üres, a zászlóbit `0`, és `[builder+0xe64] ≠ −1`: **egyetlen elem**, a
  `[builder+0xe68]` (`0x822506`–`0x822521`).
  Ha a vektor üres marad, `0x822524` → `eax = 9`, a horgony nem áll be, és `0x824090` nem épít listát.
- **Horgony:** nem üres vektornál és `TID ≠ 0` esetén (`0x82265f`) a horgony `vec[0]`, a `+0x30` kulcs
  szerint keresve (G/2c). A `TID` a `GetCurrentThreadId` (G/3c 2. pont).
- ⚠️ **Nyitott:** (a) az album-slot `0xdc` törzse (melyik fotók), (b) a `0x7166c0` törzse, (c) a
  `[builder+0xe68]` és `[builder+0xe64]` értelme. Ezek döntik el, mi kerül a mód-5 listába.

**5. A rendezés kimenete — MEGERŐSÍTVE (utasítás + Ghidra `00823620.c` 262–300. sor).**

- A `0x8256a0` a forrás-indexlistát rendezi a dátumkulcs szerint (3. pont). Az `s = sorted[p]` kiíró
  ciklus (`00823620.c` 268–277. sor): `inv[s] = p` a `[obj+0x4f8]`-ba; a `dst[p]` 0x38 bájtos rekordba
  `+0x30 = forrás-kulcs[s]` és `+0x34 = local_80[s]`; majd `0x446610`-hívás.
- Tehát a `[obj+0x4e0]` lista a dátum szerint rendezett, és a jelöltindex a **rendezett pozíció**.

**6. A ordering 0 kiválasztási lánc, összefoglalva (a G/3c 5. pontjának részletezése).**

- **Darabszám:** `k` = a `0x81b800` `uStack_30` (a `hossz` argumentum 2…n közé szorítva, `param_2 < 3 → 2`,
  `n < k → n`). A ciklus `[this+0x500] < k` mellett fut, minden lépésben egy nyertest vesz fel.
- **Kezdő középpont `c`:** mód 5 és a horgony megtalálva → annak indexe; különben index 0 (mód 6, vagy üres).
- **Jelöltek:** spirál `c+1, c−1, c+2, c−2, …` (`0x81d298`–`0x81d4df`), legfeljebb 100 rögzített
  jelölt (`0x81d4e4`, `ebx & ~1 == 0xc8`). Jelölt, ha nincs még nyertes, nincs zászlózva, és
  `G[j] ≠ G[c]`.
- **Pontszám:** `score(j) = Σ_k w_k · G_k(j, c)`. A `0x873170` a `(g_k, c, &vec, &cnt, flag)` argumentumokkal
  minden listaelemre a `g_k` objektum vtábla `+0x8` slotját hívja (`call edx`, `ecx = g_k`, `0x8733d1`–`0x8733f6`),
  és a visszatérést `fstp`-pel az elem vektorába írja (`0x8733f8`). A súlyozott összeget a hívó képzi:
  `out_i += w_k · vec_k[i]` a `0x81d75e`–`0x81d77d` ágban, `w_k = [this+0x50c][k]`. A getter argumentum-sorrendje `(jelölt, c)`.
- **Választás:** a `0x81d7b0`-ban a legkisebb `score`, szigorú `<`, az 1e8 kezdőhatár alatt; döntetlennél
  a korábban bejárt (G/2c). Ha egy sem éri el az 1e8-at, a spirál első eleme.
- **Nyertes:** `+0x30` kulcs a kimenetbe (`0x81d832`), a jelölés, és új középpont (`0x81d8a0`).
- **Következmény a küszöbön belüli képekre:** (i) a nyertes csoportja a következő lépésben ki van zárva, tehát
  **két egymást követő választás nem lehet azonos csoportból**; (ii) egy csoport képviselője az a tagja,
  amelyik a legkisebb `HOG-χ² + 0,4·Neven` távolságot adja az **előző választotthoz**. Nem az első, nem az
  utolsó, és nem a minőség alapján dől el. Ez a mechanizmus; a konkrét fotóindex futás nélkül nem adható meg.

**7. Mód 7 (`0x699cd0(7)` → `0x6999c0`).** A `0x6999c0` ctor a 0x770 bájtos objektumot `[+0x4e0] = 0`,
`[+0x738] = −1`, `[+0x708] = 0` állapotban hagyja. Mód 7 nem hívja a `0x824090`-et, így a lista üres és a
`0x81c9b0` korai kilépéssel tér vissza (G/3b). Ez azt jelenti, hogy mód 7-nél nincs küszöbszűrés. ⚠️ Ez a
G/3b feltételes olvasata, mert a mód-7 objektum további használata nincs végigkövetve.

**Bizonyítottsági fok (G/3d):**

| Állítás | Forrás | Fok |
|---|---|---|
| HOG = `Σ (A−B)²/(A+B+1e-8)`, távolság (kisebb = hasonlóbb) | utasítás (`0x873e40`–`0x874003`), konstans `0xcf4bd8` | **megerősített** (egy út) |
| Neven = `1 − x`, azonos klaszter → 0, rekognáló-hiba → 1 | utasítás (`0x8742a0`–`0x874314`, `0x48c440`) | **megerősített**; az `x` a `0x3c` slotból **feltételes** |
| Neven súly `0.4f` | `0xc7c838` (olvasott érték) | **megerősített** |
| Csoportkizárás: a jelölt csoportja = a középpont csoportja → kihagy | utasítás (`0x81d41d`–`0x81d428`), `ecx = c` ellenőrizve | **megerősített** |
| `G` = `[this+0x6cc]`, írója `0x81ae10` | utasítás (`0x81ae48`, `0x81ae96`), `0x81b800` argumentum | **megerősített** |
| `[this+0x708]` határ-ellenőrzés írója és null-kockázata | — | **NYITOTT** |
| Egyenlő dátum: a rendező stabil, másodlagos kulcs a forrásvektor pozíciója | utasítás (`0x819570`, `0x825930`, `0x825740`) + Ghidra `00823620.c` | **megerősített** (összefésülési szabály); a futamszintű sorrend **feltételes** |
| Mód-5 forrásvektor töltője: `0x8223e0` (`eax = &[esp+0x14]`) | utasítás (`0x8240fe`, `0x824114`) | **megerősített** (a G/3c helyesbítve) |
| A `0x8223e0` ágai (album `0xdc`, `0x7166c0`, egyelemű `[+0xe68]`) | utasítás (`0x822402`–`0x822521`) | **megerősített** az ágszerkezet; a `0xdc` és a `0x7166c0` törzse **NYITOTT** |
| Horgony = `vec[0]`, ha `TID ≠ 0` | utasítás (`0x82265f`–`0x822675`) | **megerősített** |
| `0x8256a0` kimenete a `[obj+0x4e0]` rendezett listája; `inv` és `+0x30/+0x34` | utasítás + Ghidra `00823620.c` 268–277. sor | **megerősített** (két út) |
| Választási lánc: spirál, 100 jelölt, `G[j] ≠ G[c]`, `argmin Σ w·távolság` | utasítás (`0x81d298`–`0x81d8a0`, `0x81d7b0`) | **megerősített** |
| Konkrét megtartott fotóindex | — | **NYITOTT** (futás nélkül) |

**Nyitott pontok, és mi zárná le őket.**

1. `[this+0x708]`: a határ-tömb írója ordering 0 ágon, és az, hogy az ág elérhető-e nullpointerrel. Lezárja: a `0x81d338` ág futás-mérése vagy a `0x874e40` ordering 0 előfeltételének igazolása.
2. `0x8223e0` `0xdc` (album fotólista) és `0x7166c0` törzse, valamint `[builder+0xe68]`/`[+0xe64]` értelme. Lezárja: a két virtuális törzs olvasása és a `0x6175c0` hívóhely visszakövetése.
3. A HOG-vektor forrása (`0x873cb0`) és a Neven `0x3c` slot törzse (a hasonlóság skálája). Lezárja: a két törzs olvasása.
4. A `hossz` argumentum (`0x6175c0` `param_2`) forrása: mit jelent a darabszám a film szempontjából. Lezárja: a hívó visszakövetése.
5. Natív viselkedésmérés: Windows-gép kell (Wine alatt a Picasa nem készít filmet, picasa-colab-jobs #106). Lezárja: 4–6 képes, ismert időbélyegű mappa a Filmkészítő csúszkájával.

**Kész, ha (a #4194 jegy szerint) — állapot: NEM teljesül.** A mechanizmus most már utasításszinten áll
(csoport, rendezés, horgony, spirál, `argmin` súlyozott távolsággal), de a konkrét megtartott fotóhoz két
nyitott bemenet kell: a 1. (`[this+0x708]`) és a 2. (mód-5 forrás) pont. A jegy nem zárható.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Dátum szerint rendezett lista, küszöb alatti csoport (Δ<T szomszéd), horgony (album első eleme vagy 0. index), spirál (+1, −1, +2 …, ≤100 jelölt, más csoport), `argmin Σ w·távolság` (HOG χ² + 0,4·Neven), láncos választás. | `slideshow.py` színátlag szerinti legközelebbi képet választ; burst-szűrő nincs. | **#4182:** a csoportosítás (G) és a rendezés (G/3d 3. pont) implementálható. A pontszámhoz arc-leíró kell (HOG-szerű χ² és Neven-szerű távolság); enélkül a „melyik marad” nem egyezik az eredetivel. A megtartási lépést csak az 1–2. nyitott pont lezárása után szabad eredetihűnek nevezni. |

#### Bizonyítottsági fok

**Megerősített** (utasításszinten olvasva): a négy tálcagomb ága és
előfeltételei, a beszúrás a lista végére, a törlés utáni feltételes
újraszámolás, a három `ordering`-érték, a rádió-csoport kézi kezelése,
a `remove_low_res_faces` bájtja, a két csúszka képlete és konstansai, az
`s` normalizáltsága (a hangerő `×1000` skálázásából), az `N` azonossága a
felirattal, az öt bemenet sorrendje, a kapu mind az öt lépése és a három
visszatérési érték, a két külön preferencia-kulcs.

**Megerősített, a G szakaszra korlátozva:** a készítési idő szerinti
szomszédos csoportosítás, az egész másodpercre kerekítés és a `delta >= T`
határ (utasításszintű olvasat + natív QEMU-mérés). Az `ordering=0`
súlyozott minimumának útja és a getterek bekötése **feltételes** a G/2c
szerint: az utasításolvasatot a Ghidra-hívási lánc és a vtable/RTTI
azonosítás támasztja alá, de a kiválasztott indexet egyik független út sem
állapította meg. Az `ordering=1/2` gráfút-választási mechanizmusát a
Ghidra-dekompilátum és az utasításszintű olvasat támasztja alá.
**Nyitott:** a konkrét nyertes fotóindex, a `+0x30/+0x34` mezők szemantikája
és a gráfélek teljes költségképzése.

**Erős**: a `[panel+0x4f0]`/`[+0x4f1]` jelzők jelentése.

#### G/3e. A 12. kör (záró, 2026-10-13): a [this+0x708] tömb és a mód-5 forrás — RÉSZLEGES, a szabály NEM zárult le (#4194)

**Eredmény egy mondatban:** a megtartási szabály utasításszinten sem lett teljes; a két nyitott pont
közül az elsőt szűkítettem, a másodikat csak a fordítási ág elején tudtam olvasni. A „Kész, ha" lista
ezért **nem írható meg konkrét megtartott indexekkel** — nem akarok kitalált teszteseteket adni.

**Módszer.** Utasításszintű olvasat (capstone 4 + pefile, `~/picasapy-agent/.venv`), lineáris szkennelés
a `.text` egészén (`0x708]` operandus-minta és `call 0x81e…` hívók). Segédszkriptek a scratchpadban
(`g3e/scan.py`, `g3e/dis.py`), a repóba nem kerültek. Natív futás nem készült.

**(a) `[this+0x708]` — szűkítve.**

- **Nem határlista.** A `0x81e5a0` (`this` = `eax`) a `[this+0x4e4] >> 1` = a rekordszám `n` alapján
  átméretezi a **három** int-tömböt: `[+0x700]` (méret-jelző `+0x704`), `[+0x708]` (`+0x70c`) és
  `[+0x710]` (`+0x714`). A `[+0x708]` mérete tehát **n**, rekordonként egy elem — nem időcsoportonként.
  A `0x81e8e0`-es átméretező (`0x97c810` realloc, `0x97caf0` free, `(n << 1) | flag` a méret-szóban) a
  közös tömb-kezelő.
- **Hívási hely:** a `0x8242c7` (`mov eax, ebp; call 0x81e5a0`), a `0x824090`-es lista-építő után, a
  `0x81e3a0` és `0x819370` előtt. Tehát a ordering-0 ág rekordlistájának építésekor a tömb mindig n elemű.
  Ez azt jelenti, hogy a `0x81d353`/`0x81d382` olvasásánál a null-pointer-kockázat az n = 0 esetre szűkül,
  és ott a határ-ellenőrzés (`cmp eax, esi; jge`) megakadályozza az olvasást.
- **Nem igazolt:** a tömb ELEM-tartalma. Az elemek írása közvetett (betöltött mutatón keresztül), ezért a
  `0x6`-os mintás szkennelés nem találta meg. A `0x81d338`-as ág `esi`-határa (a `cmp eax, esi`-t megelőző
  töltés) sem lett végigkövetve. Tehát: a tömb neve „határ" csak feltételes; a tartalma **NYITOTT**.

**(b) Mód-5 forrásvektor — részben.**

- **`0x7166c0`** (`esi` = a kimeneti vektor `{ptr, size}`, `ebx` = a forrásobjektum, `[esp+8]`): először
  felszabadítja a kimeneti vektor régi bufferét, majd a `[ebx]` vtábla `+0xb4`/`+0xb8` slotjait hívja
  (az első a darabszám, a második az elem), és a `[ebx+0x2cc]` jelzőre a `+0xc4` slot is fut. Ez egy
  **gyűjteményből vektort építő** rutin. Hogy a `+0xb4`/`+0xb8` pontosan mit ad (album-sorrend, kijelölés),
  a vtábla-törzsekből nem igazoltam — **feltételes**.
- **`0x8223e0`-ban** a `0xdc` album-slot törzse nincs olvasva; a `0x7166c0` a `[builder+0xea8]` ágon hívódik.
  A két ág kiválasztása (album `[+0x3c9]`, `[builder+0xea8]`) a G/3d 4. pontjában leírt.
- **Következmény:** a mód-5 lista tartalmát (az album kézi sorrendjét vagy a kijelölést) még **nem** tudom
  megállapítani; ezért a 0x7166c0-ág eredménye sem zárható le.

**Megtartási szabály (G/3e) — összefoglaló, ami igazolt és ami nem:**

| Lépés | Állapot |
|---|---|
| Csoportosítás: szomszédos `delta < T` → ugyanaz a csoport | **megerősített** (G, natív QEMU) |
| Rendezés dátum szerint, egyenlőnél a forrásvektor pozíciója | **megerősített** (G/3d 3. pont) |
| Horgony = `vec[0]` (mód 5, `TID ≠ 0`), különben index 0 | **megerősített** (G/3d 4. pont), a `vec` tartalma **NYITOTT** |
| Spirál `c+1, c−1, c+2, …`, ≤ 100 jelölt, `G[j] ≠ G[c]` | **megerősített** (G/2c) |
| Pontszám `Σ w · távolság` (HOG χ², Neven `1 − x`, súly 0,4), argmin, 1e8 kezdőhatár | **megerősített** a szerkezetben; a Neven `x` skálája **feltételes** |
| `[this+0x708]` mint „határ-tömb" | **CSÖKKENT** — per-rekord int tömb, hossza n; tartalma **NYITOTT** |
| Mód-5 album-ág (`0xdc`) és `0x7166c0` tartalma | **NYITOTT** |
| Konkrét megtartott fotóindex | **NYITOTT** (natív futás nélkül nem adható meg) |

**Kész, ha — állapot: NEM teljesül.** A jegy nem zárható. Ami most megírható tesztként: a csoportosítás
(már mérve: `[0, 3240, 6480]`, `T = 3600` → mind egy csoport, `[0,0,0]`; `[0, 3600, 7200]` → `[0, 1, 2]`).
A megtartott index tesztjéhez az (a) elem tartalma és a (b) album-ág kell.

**Következő, lezáró lépés (csak ha van rá erőforrás):** a `[this+0x708]` elem-írója (közvetett mutató
követése a `0x81e5a0`-t hívó `0x8242c7`-ből felfelé, és a `0x81d338`-as blokk `esi`-határa), valamint a
`0x7166c0` `+0xb4`/`+0xb8` vtábla-törzsei. Natív QEMU-próba előtt ezek kellenek, különben kitalált vtáblát mérne.

#### G/3f. A 13. kör (2026-10-13): a [this+0x708] írói, a nearest-flag kitöltő — NEM ZÁRULT LE (#4194)

**Eredmény egy mondatban:** a `[this+0x708]` elemeinek íróját nem találtam meg; a `0x7166c0` vtábla-törzseit
és a `0xdc` album-slotot ebben a körben nem olvastam; a megtartási szabály tehát továbbra sem zárható le.
Új, utasításszinten igazolt rész: a `0x874ac0` szomszédos-jelölt (nearest-flag) kitöltője (2. pont).

**Módszer.** Capstone 5.0.7 (`~/picasapy-agent/.venv`), a teljes `.text` szkennelése szinkron-újraindítással
(érvénytelen bájtnál egy bájttal tovább), a `0x708` minden operandusalakja (`0x708]`, `add`, `push` stb.).
Segédszkriptek a scratchpadban (`g3f/`), a repóba nem kerültek. Ghidra: `ghidra-koteg-2026-10-12/0081b800.c`.
Natív futás nem készült. A `00874e40`/`00874320`/`00874ac0` dekompilátuma nincs a referencia-kötegekben.

**1. A `[this+0x708]` teljes hozzáférés-listája.**

- A teljes szkennelés a G/3e 29 találatát adja (`0x708]` alak), plusz egy `lea` (`0x81bb95`) és a
  konstruktor-írás (`0x699ac3`). Más alak nincs (sem `add reg, 0x708`, sem `push`).
- **Csak a mutatót írják** (újraallokálás): `0x81a272`, `0x81e916`, `0x81e98f`, `0x81e99e`, `0x81e9c3`,
  `0x81e9c9`, `0x81ea91`, `0x81eaa0`. Ezek a `0x81e8e0` realloc/free ágai; a méret a `+0x70c`-ben van,
  `(n << 1) | flag` alakban.
- **Olvasó helyek:** `0x81d353`/`0x81d382` (szomszédos egyenlőség, `arr[k] != arr[k∓1]` megszakítja a
  spirált; a 0x81b800 Ghidra-kimenetének ~1799–1803. sora); `0x81f3c8`–`0x81f52a` (különbség és
  `cmp ebx, 0x16e`); a `0x874e40` a3-argumentumán át (`arr[edi] - arr[edx] ≤ 0x16e` ablak).
- **Elemíró: NEM TALÁLTAM.** A 29 hozzáférési hely blokkjaiban nincs `[reg+idx*4]` írás. A `0x874e40`
  `[ebx+esi]`-írásai a `0x97c810`-zel frissen foglalt lokális bufferbe mennek (`0x874f9c`), nem a `+0x708`-ba.
- **Ellentmondás — NYITVA.** A `0x874320` (a `0x874e56`-ban a3-at kapja `eax`-ben) `[eax]` → `[ecx]` → vtábla
  `+0xc` láncot követ, ami objektumra utal, nem int-tömbre. A3 verem-offszete (`[E+0xc]`) és ez a lánc
  nincs összeegyeztetve. Amíg ez nincs, a „a3 int-tömb” olvasat is csak feltételes.

**2. A `0x874ac0` — nearest-flag kitöltő (utasításszinten megerősítve).**

- Signatúra: `0x874ac0(src, Lki, Rki)`. `src` = bájt-jelzővektor (`{ptr, (n<<1)|flag}`), `Lki`/`Rki` = int-vektorok
  (`0x874ac0` eleje: `[esp+4]` = src, `mov esi,[eax+4]; shr esi,1` = n).
- A `0x874e40` a `src`-nek a `+0x6f8` mezőt adja (`0x874e75`: `ecx = [esp+0x98]`, a4 = `p1+0x1be`), az
  `Lki`/`Rki` a saját lokálisai (`[esp+0x78]`, `[esp+0x6c]`).
- Működés (`0x874c8c`–`0x874e2f`, a kitöltő ciklusa):
  - `L[i]` = az i-nél **korábbi** legnagyobb `j`, amelyre `src[j] ≠ 0`; ha nincs, `-1`.
  - `R[i]` = az i-nél **későbbi** legkisebb `j`, amelyre `src[j] ≠ 0`; ha nincs, `n`.
  - Az `L[i]` a `[edx+ecx*4]` írásból és az `edi = ecx` frissítésből, az `R[k]` a `[edx+eax*4]` írásból
    (`eax = n−1−ecx`) és az `esi = eax` frissítésből jön.
- **Teszteset (a kódból levezetve):** `src = [0,1,0,0,1,0]`, n = 6 → `L = [-1,-1,1,1,1,4]`,
  `R = [1,4,4,4,6,6]`.
- **Kapcsolat a spirálhoz NEM igazolt.** A 0x81b800 Ghidra-kimenetében a spirál határait a `param_1+0x720`
  (balra) és `+0x728` (jobbra) táblákból olvassa (~1763–1771. sor). A G/2b szerint ezekbe csak szentinel kerül
  (`0x81e5a0`: `-1`, `n`). A `0x874ac0` szomszédot ír, nem szentinelt. Hogy a `0x874e40` lokálisai eljutnak-e
  a `+0x720/+0x728` mezőkbe, nem láttam. **A G/2b szentinel-állítás ezért nyitott.**

**3. A `0x7166c0` vtábla-törzsei és a `0xdc` album-slot — ebben a körben NEM olvastam.** A G/3e (b) nyitott marad.

**4. A 2. KÖR tételei** (`0x699cd0` hívóhely, `0x824090` flag, `0x6999c0`, `0x618050` mód-7, `0x8242f0`,
`0x81c9b0`): ezek a G/3b–G/3d szakaszban már le vannak írva, ebben a körben nem ismételtem meg. Csak a
`0x8242f0` `mov [ebp+0x738], edx` írását ellenőriztem (egyezik a G/3b-vel).

**Megtartási szabály (G/3f) — állapot:**

| Lépés | Állapot |
|---|---|
| Csoportosítás: szomszédos `delta < T` → ugyanaz a csoport | **megerősített** (G, natív QEMU) |
| Rendezés dátum szerint | **megerősített** (G/3d 3. pont) |
| Spirál `c±k`, ≤ 100 jelölt | **megerősített** (G/2c) |
| Pontszám, argmin, 1e8 kezdőhatár | szerkezet **megerősített**; a Neven-skála **feltételes** |
| `[this+0x708]` tartalma és írója | **NYITOTT** (írót nem találtam; ellentmondás a `0x874320` láncban) |
| `+0x720/+0x728` írója (a `0x874ac0` kimenete?) | **NYITOTT** (az összekötés nincs igazolva) |
| `0x7166c0` vtábla-törzsek, `0xdc` album-ág | **NYITOTT** (ebben a körben nem vizsgált) |
| Konkrét megtartott fotóindex | **NYITOTT** |

**Tesztesetek (G/3f).** Megtartott indexet nem adok: nincs igazolva. Amit a bizonyíték már megenged:

- csoportosítás (G): `[0, 3240, 6480]`, `T = 3600` → `[0, 0, 0]`; `[0, 3600, 7200]` → `[0, 1, 2]`;
- nearest-flag kitöltő (G/3f 2. pont, függvényszintű): `src = [0,1,0,0,1,0]` → `L = [-1,-1,1,1,1,4]`,
  `R = [1,4,4,4,6,6]`. A spirálhoz való kapcsolata nincs igazolva.

**Kész, ha — állapot: NEM teljesül.** A jegy nyitva marad. Lezáró lépés, két független úton:
(a) a `+0x708` írója: a `0x874e40` a3 verem-offszetének és a `0x874320` vtábla-láncának összevetése
(utasítás + egy Ghidra-dekompilátum a `00874e40`-re, ami még nincs a kötegben);
(b) a `0x874e40` kimeneti másolása: hova kerül a `Lki`/`Rki` (`+0x720`/`+0x728`?).

#### G/4. A 9. kör (2026-10-17): a megtartás szerkezete a Ghidra-dekompilátumból; a párdistancia natívan mérve (#4194)

**Kérdés.** Ha két kép készítési ideje a küszöbön belül van, melyik marad meg: az első, az utolsó, a középső vagy a legjobb pontszámú?

**Válasz, fokonként.** Általános „első", „utolsó" vagy „legjobb minőségű" szabály **nem igazolható**. Bizonyított szerkezet:

1. a `burstmodethresh` csak csoportokat képez, képet nem választ (**megerősített**, G szakasz);
2. a kiválasztó távolságot minimalizál, nem minőséget (**megerősített**, 5. pont);
3. `ordering != 0` esetén a jelöltsorozat első és utolsó eleme a gráfút végpontja (**feltételes**, 3. pont);
4. `ordering = 0` esetén a horgony, alapesetben a 0. jelölt, megmarad (**feltételes**, 4. pont).

A csoporton belül **konkrét** kimaradó kép nem nevezhető meg: a választás a getterek és az élek értékeitől függ, a `0x0081c9b0` és a `0x00877c50` dekompilátuma hiányzik (9. pont), a rekordok fotóindexe pedig nincs megmérve.

**Módszer és határ.** (A) út: Ghidra-dekompilátum (`referencia/ghidra/2026-10-17-film-4400-4194.txt`: `0x0081b800`, `0x00874320`, `0x008742a0`, `0x00873e40`, `0x008781a0`). (B) út: (a) qemu-i386 natív futtatás a `0x00873e40`-en szintetikus `this` objektummal (a `[this+0x4c]` jelzőtömbben 1 áll, így a `FUN_00873cb0` feature-építő nem fut: a mérés a párképletet méri, a jellemzőgyártást nem); (b) capstone-os utasításolvasat a `0x0081ba16`-`0x0081bad8` tartományban. Még nincs dekompilálva: `0x0081c9b0`, `0x00877c50`, `0x00874e40`, `0x00875ee0`, `0x0081ae10`, `0x0048c440`, `0x00873170`, `0x008773d0`, `0x00877820`.

**1. Korrekció a G szakaszhoz.** A G szakasz (2026-10-07) a `0x0081b800` 4. paraméterét `burstmodethresh`-nek nevezte. A dekompilátumban ez **mutató**: `if (param_4 != 0) FUN_0081ae10(param_4)` (830-832. sor), a csoportlista-ágazás pedig `param_4 == 0`-n dől el (849-856. sor). Hogy a hívó a küszöb értékére mutató pointert ad-e, vagy más objektumot, a hívóból dől el (`0x00617810`, `0x006175c0`): **NINCS MEG**. A csoportosítás szabálya ettől nem változik, mert a QEMU-mérés (G szakasz) a `0x0081ae10`-et közvetlenül hívta.

**2. A `0x0081b800` megtartó szerkezete (A; a végpont-írás B-vel is).**

- **Ordering-ágazás:** `param_3 == 0` esetén `0x0081c9b0` (844-859. sor) írja a kimenetet, és a függvény a `0x0081c980` ágra ugrik. Egyéb érték: gráfút (956-1110. sor).
- **Szakaszolás (gráfút):** `L` a kért darabszám (`hossz`, legalább 2), `N` a bemeneti elemszám. `U` a legkisebb egész, amelyre `⌊L·N/U⌋ ≤ 5·10^7` (862-868. sor). Határok: `0`, `⌊N·j/U⌋` (j = 1 … U-1) és `N-1` (949-951. sor). Hétköznapi méretnél (`L·N ≤ 5·10^7`) `U = 1`, vagyis egyetlen szakasz: `[0, N-1]`.
- **Egy szakaszon belül** a `0x00877c50` legkisebb összköltségű utat ad a két határ között. A kimenetbe az út 1. elemétől az utolsóig kerül (1066-1103. sor). A kimenet kezdő eleme a 0. jelölt (982-986. sor).
- **Kimeneti azonosító:** a kiválasztott rekord `+0x30` dwordje (1553-1554. sor). A `+0x34` dátumkulcs egy virtuális hívásba megy (1556-1559. sor).

**3. Végpontok (`ordering != 0`).** Az `N-1` tárolása (0x0081ba45-0x0081bad0, az allokáció sikeres ágán): `ebp = [esp+0x18] - 1`, és az `[esp+0x18]` a ciklus léptéke, amelyet a dekompilátum 880. és 915. sora `N`-nel növel (utasításszinten a `add [esp+0x14], edx` a 0x0081ba2e-n). Ez egyezik a 949-951. sorral (**megerősített**, A + B). A kezdő `0` elem írása (873. és 982-986. sor) csak az A úton igazolt.

Következmény (**feltételes**): a gráfúton a jelöltsorozat első és utolsó eleme megmarad; a köztes képeket a legkisebb összköltségű út dönti el. Két feltétel: (a) a jelöltlista (`param_1[0x13c]`) azonos a bemeneti sorrenddel; ha a `removelowresfaces` szűr, a „végpont" a szűrt lista végpontja. Ezt a lista írója nem igazolja. (b) A `0x00877c50` végpont-kényszere (az út az `N-1` csúcsban végződik) nincs dekompilálva.

**4. Horgony (`ordering = 0`).** A `0x0081c9b0` horgonya (G/2 szerint) `[obj+0x738]`-tól függ; ha `-1`, a 0. rekord. A `0x006999c0` konstruktor `-1`-re állítja, az egyetlen direkt író a `0x00824090` (G/2b). Alapesetben tehát a 0. jelölt a horgony (**feltételes**: a UI-ból beállított horgony forrása, a `0x008223e0` és a `0x008226e0`, nincs dekompilálva).

**5. A bizonyított képletek.**

| Képlet | A: dekompilátum | B: natív / utasítás | Fok |
|---|---|---|---|
| `d_HOG(a,b) = Σ_i (a_i - b_i)^2 / (a_i + b_i + ε)`, `ε = 1e-8` (a `0x00cf4bd8` double-ja: 9.99999993922529e-09) | `0x00873e40`, 2040-2077. sor (a 4-es blokkos ciklus és a farok) | qemu-i386, 3 vektorpár (n = 8, 5, 6): relatív eltérés ≤ 4.6e-8 (float32-kerekítés). Az a=0, b=1e-8 pár 3.0e-8-at ad, ami ε = 1e-8-cal egyezik (ε = 0 esetén 6.0e-8) | **megerősített** |
| `d_Neven(a,b) = 1 - sim(a,b)`; ha a két `+0x34` kulcs egyenlő és nem nulla, 0; ha a `0x0048c440` hibát ad, 1 | `0x008742a0`, 1988-1996. sor | nincs B-út (`0x0048c440` nincs dekompilálva) | **feltételes** |
| reducer: `új[t] = min_i (régi[i] + w(i→t))`, szigorú `<`, csak `régi[i] < 1e8`-nál; kezdőérték `1e8` (`0x4cbebc20` float) | `0x008781a0`, 2144-2157. sor | G/2b natív QEMU-mérés | **megerősített** |

A `d_HOG` B-útja a `0x00873e40` natív futtatása `qemu-i386` alatt: a `this` objektum a `hb.Image` harnessben épült (`[this+0x4c]` jelzőtömb = 1, `[this+0x54]` = `{adatpointer, 2·n}` párok), a hívás thiscall (`ECX = this`, két stack-index), az eredmény x87 `ST0`, double-ként kiírva. A harness ideiglenes fájljai a munkafa `.bt/` mappájában voltak, a futtatás után törölve.

**6. Natív fixture (#4182 teszteléséhez).** A bemenetek közvetlen vektorok, NEM rekordból képzettek:

- `a = [1,2,3,4,5,6,7,8]`, `b = [2,2,1,4,6,6,9,8]` → natív `1.6742424964904785`; Python (float64, ε = 1e-8): `1.6742424203924187`
- `a = [0.5,1.5,2.5,3.5,4.5]`, `b = [1,0,2,4,3]` → natív `2.055555582046509`; Python: `2.0555555438765434`
- `a = [0,0,0,0,0,0]`, `b = [1e-8]×6` → natív `2.999999892949745e-08`; Python: `3.0000000091162064e-08` (ε = 0 esetén `6e-08`)

Tűrés: 1e-6 relatív. A fixture a képlet helyességét igazolja, a jellemzővektor forrását nem: a rekord-jellemző (a `FUN_00873cb0` kimenete) **NINCS MEG**.

**7. Válasz a kérdés részeire.**

- **„Első kép" általános szabályként: NEM.** `ordering = 0`: horgony (feltételes). `ordering != 0`: végpont (feltételes).
- **„Utolsó kép":** csak `ordering != 0`-n, és csak feltételesen végpont.
- **„Legjobb minőség": NEM.** A kiválasztó összköltséget (`ordering != 0`) vagy súlyozott párdistanciát (`ordering = 0`) minimalizál. A legkisebb távolság a középponthoz (vagy az út szomszédjához) legjobban hasonló kép. Minőségről nincs állítás.
- **„Láncszerűen" vagy „párosan"?** A csoportosítás a **szomszédhoz** mérve dolgozik (az előző BEMENETI elemhez, nem az előző megtartotthoz), és **láncolt**: egyesített csoportot képez (QEMU: `[0,3240,6480]` egy csoport). A kiválasztásban a csoportkizárás `ordering = 0`-n az **előző megtartott** (középponti) képhez mérve szól, de csak a következő lépésre; a csoporttársak később újra választhatók.
- **Mi esik ki?** A csoport azon tagjai, amelyeket a választott út vagy a spirál nem vesz be. Hogy KONKRÉTAN melyik: **NINCS MEG**.

**8. Kizárt hipotézisek.**

- „A csoportban mindig az első marad": kizárva általános szabályként (nincs ilyen ág a dekompilátumban).
- „A csoportkizárás az egész csoportot kiveszi a kimenetből": kizárva; `ordering = 0`-n a kizárás csak a következő lépést érinti.
- „A kiválasztás minőség-getteren alapul": kizárva; a getter párdistancia (5. pont).
- A G szakasz 4. paraméter-azonosítása: helyesbítve (1. pont).

**9. Nyitott kérdések mérlege.**

| # | kérdés | állapot | indoklás, Ghidra-kör |
|---|---|---|---|
| 1 | `ordering = 0`: melyik rekord a középpont és melyik a jelölt a pontozó hívásban; a 100-as jelöltlimit és a csoportkizárás C-szinten | BLOKKOLT | `Ghidra-kör kell: 0x0081c9b0: a 0x00873170 hívás argumentum-sorrendje (középpont, jelölt?), a 100-as limit és a csoportkizárás [blokkoló]` |
| 2 | `ordering != 0`: a gráfélek és a szakaszonkénti út | BLOKKOLT | `Részben (24. kör, G/12): a rétegek, a végpont-feltétel, a visszakövetés és az útvektor sorrendje megvan; nyitott az élköltség forrása és a végső fotóindex-leképezés. Ghidra-kör kell: 0x0081b800, 0x00878720 [blokkoló]`; `Ghidra-kör kell: 0x00874e40: az élek halmaza, az élablak (az utolsó paraméter, N/(L-1)) és a csoportkizárás helye [blokkoló]` |
| 3 | a szakaszonkénti darabszám alsó és felső határa | BLOKKOLT | `Ghidra-kör kell: 0x008773d0 és 0x00877820: az L-1 darabszám korlátozása, ez már U = 1-nél is hat [blokkoló]` |
| 4 | a Neven-hasonlóság (`sim`) képlete | BLOKKOLT | `Ghidra-kör kell: 0x0048c440: a sim számítása és a visszatérési kódja [blokkoló, ha a SmartMultiPersonTrans be van kapcsolva]` |
| 5 | a horgony forrása (`[obj+0x738]`) | BLOKKOLT | `Ghidra-kör kell: 0x008223e0 és 0x008226e0: az alapértelmezett horgony beállítása [blokkoló]` |
| 6 | a rádió alapállapota (smart / album / chronological) | BLOKKOLT | `Ghidra-kör kell: a makemoviepanel inicializálója, a smart_order_radio sztring hivatkozásai alapján (a cím NINCS MEG; index: string_xrefs) [blokkoló: ez dönti el, melyik ág a valódi alap]` |
| 7 | melyik konkrét kép marad (a jegy kérdése) | BLOKKOLT | az 1-6. tételek függvénye |
| 8 | csoportosítás (T > 0) | LEZÁRVA | megerősített, QEMU-mérve (G szakasz) |
| 9 | párdistancia (HOG) | LEZÁRVA | megerősített (5. pont) |
| 10 | reducer | LEZÁRVA | megerősített (G/2b, 5. pont) |
| 11 | végpontok | LEZÁRVA, feltételes fok | 3. pont; a kezdő elem B-útja nem blokkoló |
| 12 | a 4. paraméter jelentése | LEZÁRVA | helyesbítve (1. pont); a hívóoldal nem befolyásolja a csoportokat |
| 13 | „első / utolsó / minőség" | LEZÁRVA | 7. pont (NEM) |
| 14 | láncszerű vagy párosan | LEZÁRVA | 7. pont |

Nyitott kérdések: 0 nyílt · 7 lezárva · 7 blokkolt · 0 hatókörön kívül · 0 csak nyitva

**10. Fejlesztési átvezetés (#4182).**

| Eredeti | Nálunk (mérve) | Teendő |
|---|---|---|
| Szomszédos, egész másodpercre kerekített csoportosítás; `delta >= T` új csoport; `T = 0`-nál nincs csoport (**megerősített**) | `burstmodethresh` csak tárolódik és validálódik (`src/picasapy/movie/slideshow.py:75, 99`; `mxf.py:126, 203, 323`; `app/create_controller.py:728-729, 807, 872`). A `movie/` alatt nincs csoportosító (mérve: `grep -i burst`). | #4182: implementálható. Etalon-tesztek: `[0,3240,6480]→[0,0,0]`, `[0,3600,7200]→[0,1,2]`, `[0,3240,7200]→[0,0,1]`; `T = 0` → nincs csoport. |
| Párdistancia: chi-négyzet, `ε = 1e-8` (**megerősített**, natív) | Nincs ilyen mérőszám. A `slideshow.py:691-701` színátlag-normát használ. | #4182: a 6. pont fixture-je szerint implementálható primitív. A jellemzővektor forrása **NINCS MEG**; a színátlag nem helyettesíti. |
| `ordering = 0`: horgony, spirál, csoportkizárás, HOG/Neven-minimum (**feltételes**) | `slideshow.py:691-701`: színátlag-lánc a TELJES listán; nincs horgony, spirál, csoport, darabszám-korlát. | **Eltér.** Nem jelölhető eredetinek. A kimeneti darabszám (`felhasznált képek`) nálunk ebben a körben nincs ellenőrizve. |
| `ordering = 2`: gráfút (**feltételes**), NEM időrend | `slideshow.py:689-690`: `st_mtime` szerinti rendezés. | **Eltér.** A gráfút visszafejtése (Ghidra-kör) a teendő. |
| `ordering = 1`: gráfút (**feltételes**) | `slideshow.py:74` alapja `1`; a bemeneti sorrend marad. | **Eltér** (nem az eredeti gráfút). Az alapérték egyeztetése nyitott (9. pont, 6. tétel). |

**Kész, ha** (a #4182 fejlesztési köréhez):
1. `T = 0`-nál nincs csoportosítás.
2. A három csoportosítási etalon teljesül.
3. A `d_HOG` primitív a 6. pont fixture-jén 1e-6 relatív tűréssel egyezik.
4. A megtartási algoritmus csak akkor nevezhető eredetinek, ha a 9. pont 1-7. tétele lezárult (jelenleg nem).

**11. Ami NEM bizonyított (kimondva).** A kimaradó konkrét kép; a getterek képi jelentése (a `d_Neven` sim-je); a horgony forrása UI-ból; a rádió alapállapota; a jelöltlista azonossága a bemeneti sorrenddel; a gráfélek költsége. Ezek nélkül a fotóindex-szintű eredetiség **nem állítható**.

**Frissítés (2026-10-17, G/5):** a 9. pont 1. és 7. tétele `ordering = 0`-ra LEZÁRULT (G/5); a 2., 3., 4., 5. és 6. tétel nyitott maradt, a 3. csak `ordering != 0`-n releváns.

#### G/5. A 10. kör (2026-10-17): a megtartott kép `ordering = 0`-n, natív mérés és dekompilátum-modell (#4194)

**Kérdés.** Melyik kép marad meg a küszöbön belüli csoportból, és láncolt vagy párosított-e a ritkítás? (A G/4 9. pont 1-7. tételei.)

**Válasz (`ordering = 0`, a „Legjobb átmenetek" rádió).** A kód nem az első vagy az utolsó képet választja pozíció alapján, és nem azonosít külön minőségi mezőt; nincs minden időcsoporthoz rögzített egyetlen kép. A kiválasztás **láncolt**: a horgonyból indul (alapállapotban a 0. pozíció, az időrendben legkorábbi kép), és minden lépésben azt a még nem választott jelöltet veszi, amelynek az aktuális középponthoz számolt, regisztrált getterekből képzett **súlyozott pontszáma a legkisebb**. A HOG getter súlya `1.0`; a Neven getter `0.4` súllyal csak a `Preferences\SmartMultiPersonTrans` lekérdezésekor kapott igaz érték és a `[obj+0x6f4]` kapu mellett kerül be (`0x00824090`). A beállításkimeneti lokális változó a Preferences-lekérdezés előtt nullázódik, de a mérendő Windows-profil tárolt értéke nincs meg. A csoportkizárás csak az **aktuális** lánctagot érinti: egy csoport több tagja is bekerülhet, ha a lánc más csoportokon át tér vissza. A csoportosítás is láncolt (a szomszédos bemeneti képek között, G szakasz).

**Bizonyítottsági fok: megerősített** a kiválasztási szabályra (két független út egyezik, 125 natív eset), **feltételes** a bemeneti feltételekre (lásd „Ami még nem zárult le").

**Két független út.**
- **A (dekompilátum és utasításszint):** a `0x0081c9b0` törzse (`referencia/ghidra/2026-10-17-film-idoszuro-2.txt`, 35-1135. sor) és az utasítás-ellenőrzés: `0x81d3a2`-`0x81d4f3` (ciklus, ablak, jelöltfeltételek, léptetés), `0x81d1f1`-`0x81d229` (a vtábla-hívás két argumentummal), `0x81ca9b`-`0x81caaf` (a jelzőtömb nullázása és a horgony jelölése), `0x81d400`-`0x81d428` (a jelölt-szűrő).
- **B (natív futtatás):** az eredeti `0x0081c9b0` qemu-i386 alatt, szintetikus `this`-szel (`hb.py` harness, `.bt/sel/sel_native.py`). Ugyanazon a bemeneten az A-ból épített modell (`.bt/sel/model.py`) ugyanazt a sorrendet adja.

**Algoritmus** (`0x0081c9b0`, `ordering = 0`):
1. **Horgony** `c`: `[obj+0x738]` = -1 esetén a 0. pozíció (`0x0081ca05`-`0x0081ca33`, G/2c). A kimenet első eleme a horgony, `[obj+0x500] = 1` (`0x0081b800`: `param_1[0x140] = 1`).
2. **Zárt-jelzők:** nullázott bájttömb (`0x81ca9b` memset), a horgony 1-re állítva (`0x81caaf`). A jelölt kizárja a már zártakat.
3. **Lépés** `c` körül, irány `it` (kezdetben előre, +1). Ablak: előre `(c-1, RB[c])`, hátra `(LB[c], c+1)`; `LB = -1`, `RB = N` (az `0x81e5a0` szentinelei, spec 3407). Az első irányváltás után (`b2`) az előre-határ `-1`, a hátra-határ `N`. **Spirál:** `d` = +1, -1, +2, -2, … (`0x81d4ca`-`0x81d4db`: `d = -d`, ha `d > 0`, akkor `d += 1`), a jelölt `p = c + d`.
4. **Jelölt:** `0 <= p < N`, nincs zárva, csoportja különbözik `c` csoportjától (`0x81d400`-`0x81d428`), és előre `p > lo`, hátra `p < hi`. Legfeljebb **100 jelölt** (`cmp eax, 0xc8`, azaz 2·100, `0x81d4e4`).
5. **Irányváltás:** ha a jelöltek száma **15 alatt** van, és a spirál mindkét határt elérte, a kör nem választ, hanem irányt vált: `it = -it` (első alkalommal `b2 = true`), másodszor `it = 0` (mindkét irány). Hogy ez a választás helyett áll-e, azt a `d + c` helyzete dönti el a határokhoz képest (dekompilátum 605-618. sor). Ha nincs jelölt, a sorozat rövidebb marad a kértnél.
6. **Költség:** `cost(p) = Σ_g w_g · getter_g(c, p)` (`0x0081d730`-`0x0081d78c`; a getterlista `[obj+0x504]`, darabszáma `[obj+0x508]`, súlyai `[obj+0x50c]`). A HOG-tag `1.0 · d_HOG(c,p)`; a Neven-tag a Neven getter 0,4 súlyú kimenete, csak a fent megadott beállítási és kapufeltételekkel. A Neven-kimenet képi jelentése NINCS MEG. A QEMU-fixture V1-V3 HOG-only regisztrációval futott, ezért natív egyezésük a Neven-tag bekapcsolt esetére nem bizonyíték. Választás szigorú `<`-lel, kezdőérték `1e8` (`0x00c7da00`, bináris 0x4cbebc20), holtversenyben a spirálban korábbi jelölt nyer; ha egy sem éri el az 1e8-at, a 0. jelölt a tartalék.
7. A választott lesz az új `c`, és a sorozat következő eleme.

`d_HOG(a, b) = Σ (a_i - b_i)^2 / (a_i + b_i + ε)`, `ε = 1e-8` (`0x00873e40`).

**Bizonyíték.**

| állítás | forrás |
|---|---|
| a HOG-pontozó vtábla +8 slotja = `0x00873e40` | bináris `0x00cbdec4 + 8` |
| getterenkénti pontszám-összegzés: `összeg += getterérték × [obj+0x50c][getter]` | bináris `0x0081d730`-`0x0081d78c` |
| `ε = 1e-8` | bináris `0x00cf4bd8` (double, 9.99999993922529e-09) |
| kezdőküszöb `1e8` | bináris `0x00c7da00` = 0x4cbebc20 (f32) |
| Neven-súly `0.4` (csak SmartMultiPersonTrans) | bináris `0x00c7c838` = 0x3ecccccd (f32) |
| Neven getter regisztrálása csak a Preferences-kulcs és `[obj+0x6f4]` kapu mellett | bináris `0x00824090` (`0x8241ef`-`0x82428f`) |
| spirál `+1, -1, +2, -2, …` | asm `0x81d4ca`-`0x81d4db` |
| 100 jelölt | asm `0x81d4e4` (`cmp 0xc8`) |
| 15-ös irányváltó küszöb | dekompilátum 605. sor (`uVar6 < 0xf`); cáfoló, lásd lent |
| horgony kizárása | asm `0x81caaf` (zárt-bájt = 1); olvasás `0x81d400` (`[esp+0x48]` = `esi` = a nullázott tömb) |
| horgony -1 → 0. pozíció | dekompilátum 96-106. sor; natív: V1 |
| a kimenet a választás sorrendje | dekompilátum 739-750. sor; natív: V1 |
| csoportok (küszöb) | G szakasz (mérve, `0x0081ae10`); a natív teszt szintetikus csoportokat ad |

**Natív mérés (B út), a modell (A út) összevetése:**

| készlet | eset | egyezés |
|---|---|---|
| véletlen, horgony 0, dátumkulcs-tábla nulla (N = 5-8) | 40 | 40/40 |
| véletlen, horgony 0, dátumkulcs-tábla véletlen 0-2 | 30 | 30/30 |
| véletlen, nem nulla horgony | 30 | 30/30 |
| nagy N (20-58 és 120) | 22 | 22/22 |
| N = 300, L = 40 | 3 | 3/3 |

**Cáfoló kísérletek (15.2).** Ugyanazokon a bemeneteken a modell variánsai (a cáfoló ugyanazt a mércét kapja):

| variáns | egyezés |
|---|---|
| nincs csoportkizárás | 56/100 |
| első jelölt a minimum helyett | 18/100 |
| horgony nincs kizárva | 59/100 |
| irányváltó küszöb 5 / 10 / 20 / 30 (22 nagy-N eset) | 4 / 13 / 13 / 10 |
| jelöltlimit 50 (22 nagy-N eset) | 20/22 |
| jelöltlimit 80 / 120 / 150 (N = 300, 3 eset) | 0 / 0 / 0 (a 100 egyezik: 3/3) |

A 15-ös küszöb és a 100-as limit a mért tartományon belül igazolt. A limit 100 és 150 között az N ≤ 120 készleten nem különül el (a jelöltek száma ritkán lépi túl a 100-at); az N = 300 készlet viszont elkülöníti.

**Teszt-vektorok (kézzel ellenőrizhetők, natívan mérve).** Nyolc dimenziós jellemzők, N = 6, csoportok `[0,0,0,1,1,2]`:

```
F0 = [0.10,0.20,0.30,0.40,0.50,0.60,0.70,0.80]
F1 = [0.12,0.22,0.28,0.41,0.52,0.58,0.72,0.79]
F2 = [0.90,0.10,0.05,0.80,0.10,0.70,0.20,0.60]
F3 = [0.15,0.25,0.35,0.45,0.55,0.65,0.75,0.85]
F4 = [0.50,0.50,0.50,0.50,0.10,0.10,0.10,0.10]
F5 = [0.48,0.52,0.49,0.51,0.12,0.09,0.11,0.10]
```

| eset | horgony | L | kimenet (pozíciók) |
|---|---|---|---|
| V1 | 0 | 4 | `0, 3, 1, 5` |
| V2 | 3 | 4 | `3, 1, 5, 4` |
| V3 (mind egy csoport: `[0,0,0,0,0,0]`) | 0 | 3 | `0` (rövidebb a kértnél) |

- **V1:** 0-ból a 3 nyer (d = 0,029963): 1 és 2 a horgony csoportjából kizárva, 4 és 5 távolabb. 3-ból a 4 kizárva (ugyanaz a csoport), a 1 nyer (d = 0,022519) a 2 (1,598) és az 5 (2,063) felett. 1-ből az 5 nyer (d = 1,997) a 4 (2,040) felett. A 2 kimarad.
- **V2:** horgony 3. Az előre-jelöltek csak `[5]` (4 kizárva), kevesebb mint 15, ezért irányváltás; a kétirányú passz `[2,5,1,0]`-t ad, és az 1 nyer (d = 0,022519), nem a 0 (d = 0,029963), pedig az időrendben korábbi.

**Ami még nem zárult le (feltételek):**
- **Neven:** a 0,4-es tag külső arcfelismerő könyvtár (`0x0048c440` vtábla +0x3c hívása). Getter-kimenetének képi jelentése NINCS MEG; a modell és a teszt HOG-only. A Preferences-lekérdezés kimeneti lokálisa a hívás előtt nulla (`0x00824090`, `0x8241ef`-`0x824228`), de a mérendő Windows-profil tárolt értéke NINCS MEG.
- **Jellemzővektor forrása (`0x00873cb0`):** G/6 részlegesen vizsgálta. A hossz, a cella- és iránysorrend, valamint az egyesített kimeneti vektor normálása NINCS MEG; a G/4 teszt előre megadott vektorokat használt. **13. kör (2026-10-20, #4194):** a `0x00873cb0` burkoló: a vektort a `0x0088c1a0` írja a `[obj+0x54] + index*8` slotba (hívóhely: 5149. sor). A hossz, a sorrend és a normálás a `0x0088c1a0` törzsében van, a G/7-G/8 C-kódja szerint (2016 elem); a konstansok és a `0x0088c480` bemenete nyitott.
- **Pozíciósorrend (`[obj+0x4f0]`):** a dátum szerinti rendezés feltételes (G/3c). Egyenlő dátumnál a sorrend nincs ellenőrizve.
- **Horgony a felhasználói állapotból (`0x008223e0`, `0x008226e0`):** NINCS MEG; alapállapotban -1 (0. pozíció).
- **Dátumkulcs-tábla (`[obj+0x708]`):** a törési feltétel a tesztelt kulcsoknál egyezik (30/30). A valódi tartalom NINCS MEG (G/3e, G/3f).
- **Rádió alapállapota:** G/6 megerősítette az általános új film úton: az alap `ordering = 0`, a „Legjobb átmenetek” rádió bejelölve; a `0x00618050` külön speciális ága `ordering = 2`-t ír.
- **`ordering = 1` (album) és `2` (időrend):** a `0x00878310`, `0x00874ac0` és `0x00875ee0` G/6-ban dekompilálva lett. A gráfág eredő kiválasztási szabálya és a kimeneti indexsorrend továbbra is nyitott.
- **Csoportkizárás hiánya:** ha egy csoport minden tagja kizárt, a sorozat rövidebb a kértnél (V3). A jelenlegi `slideshow.py` ezt nem kezeli.

**A G/5-ben kért Ghidra-függvények:** mind az ötöt dekompilálták; a részleges eredményeket és a megmaradt nyitott kérdéseket a G/6 rögzíti.

A `0x00877c50` és a `0x008773d0`/`0x00877820` szakasz-darabszámai (9. pont 3.) csak `ordering != 0`-n hatnak: a `0x0081b800` ordering-0 ága (`param_3 == 0`) a `0x0081c9b0` hívása után visszatér, és nem éri el ezeket.

**A G/4 9. pont állapota G/5 után:** 1. LEZÁRVA (`ordering = 0`); 2. NYITVA (`ordering != 0`); 3. csak `ordering ≠ 0`; 4. NYITVA (külső könyvtár, feltételes); 5. NYITVA; 6. NYITVA; 7. LEZÁRVA `ordering = 0`-ra, feltételekkel; 8-14. változatlan.

**Fejlesztési teendő (#4182, Codex-kész):**

| Eredeti (`ordering = 0`, bizonyított) | Nálunk (mérve) | Teendő |
|---|---|---|
| Lánc-kiválasztás: horgony, spirál-jelöltek a középponttól (+1, -1, +2, -2, …), 100 jelölt, csoportkizárás az aktuális középpontra, a regisztrált HOG/engedélyezett Neven getterek súlyozott minimuma (szigorú `<`, 1e8, tartalék: a 0. jelölt), 15-ös irányváltás, a kimenet a választás sorrendje | `src/picasapy/movie/burst.py`: a G/5 láncmodell megvan; az injektált jellemző jelenleg a korábbi színátlag, mert a `0x00873cb0` valódi HOG-vektora nincs feltárva; Neven-jellemző nincs | A lánc szerkezete és a d_HOG primitív implementálva. Az eredetit követő képkiválasztás nyitott marad, amíg a HOG-vektor forrása és az esetleges Neven-tag összehasonlítható bemenete nincs bizonyítva. |
| Csoportosítás: szomszédos, egész másodpercre kerekített idők, `delta >= T` új csoport, `T = 0`-nál nincs csoport (G szakasz) | A `burstmodethresh` az `ordering = 0` exportban csoportokat képez és befolyásolja a láncválasztást (`src/picasapy/movie/slideshow.py`, `src/picasapy/movie/burst.py`) | A három G szakaszbeli etalon implementálva; más `ordering`-ágak képkiválasztása továbbra sincs feltárva. |

**Frissítés (2026-10-17, G/6):** új filmnél a „Best Transitions” rádió az alapértelmezett (`ordering = 0`).

**Kész, ha:**
1. `T = 0`-nál nincs csoportosítás.
2. A három csoportosítási etalon teljesül (`T = 3600`: `[0,3240,6480]→[0,0,0]`, `[0,3600,7200]→[0,1,2]`, `[0,3240,7200]→[0,0,1]`).
3. A `d_HOG` primitív a G/4 6. pont fixture-jén 1e-6 relatív tűréssel egyezik.
4. A kiválasztó a három teszt-vektoron pontosan adja: V1 `[0,3,1,5]`, V2 `[3,1,5,4]`, V3 `[0]`.
5. Az „eredeti" jelölés csak akkor, ha a jellemzővektor (`0x00873cb0`) és a rádió alapállapota (G/4 9. pont 6.) is lezárult. **Állapot G/6 után: ⛔ részben teljesült.** Az általános új film út rádióállapota lezárult, a HOG-jellemzővektor hossza, cella- és iránysorrendje, valamint végső normálása nyitott.

#### G/6. A 11. kör (2026-10-17): a HOG-kivonó részleges feltárása, rádió-alapállapot, ordering ≠ 0 ágak (#4194)

**Forrás.** A Ghidra-kimenet neve: `referencia/ghidra/2026-10-17-film-idoszuro-3.txt`. Az öt kért cím: `0x00873cb0`, `0x006173c0`, `0x00878310`, `0x00874ac0`, `0x00875ee0`. Az utasításszintű ellenőrzés az eredeti binárisból készült a helyi `annot_disasm.py` eszközzel; a natív fixture-mérés a meglévő QEMU-harness-szel futott.

**HOG-jellemzővektor (`0x00873cb0`).** A függvény a rekordból származó mezőket és transzformációs adatokat készít elő, majd a `[param_2+0x54]` vektortár `iStack_10 * 8` címére hívja a `0x0088c1a0`-t. A dekompilátumban `in_EAX`, `unaff_ESI` és `unaff_EDI` bemenetként szerepel, ezért a képi bemenet és a vektorépítő segédfüggvények teljes adatkapcsolata nem állt helyre. A végső vektor hossza, a cellák sorrendje és az irányrekeszek sorrendje **NINCS MEG**.

A `0x0088c1a0` belső műveleteiből ennyi olvasható ki: a feldolgozó ciklusok 8 bájtos lépésekkel a `0x38` és `0x20` határértékig futnak; egy forrás-hozzáférés `0x24` bájtos lépést használ. Ezek a ciklushatárok önmagukban nem bizonyítják, hogy a végső leíróban milyen cella- vagy iránysorrendet jelentenek. A belső feldolgozott szakasz négyzetösszegéhez a kód `1.0` értéket ad, négyzetgyököt számol, majd a szakasz komponenseit ezzel osztja: `y_i = x_i / sqrt(1.0 + Σ(x_j²))`, ahol a `j` tartomány az adott belső szakasz, de annak megfeleltetése a végső HOG-vektorhoz **NINCS MEG**. A `0x0088c480` segédvektora legfeljebb `0x28` bejegyzést másol, a `0x0088cd10` segédvektora legfeljebb `5` bejegyzést kezel; ezek köztes tárolók, nem a végső HOG-vektor méretei.

**Natív fixture a HOG-távolsághoz.** A G/4 6. pont három vektorpárja a `0x00873e40` távolságfüggvénybe előre beadott bemenet volt. QEMU-i386 alatt a kimenetek pontosan egyeztek a G/4-ben feljegyzett natív értékekkel. Ez megerősíti a távolságfüggvényt, de nem a képből vektort építő `0x00873cb0`-t, mert a mérés azt az utat nem hívta.

**Rádió-alapállapot.** A `0x006173c0` három rádiógombot regisztrál, és a callback-adatként átadott lokális egész értékeket nullázza. Ez önmagában nem mondja meg, melyik gomb van bejelölve. A panel beállítás-beolvasója, `0x00616940`, a `Preferences` alól a `showcaptions` és `cropfit` kulcsot olvassa, majd a modell `[+0x2cc]` mezőjét `0`-ra írja (`0x00616a18`). A panelépítő `0x00618050` a `0` értékű mezőnél a `smart_order_radio` bejelölt bájtját `1`-re állítja (`0x0061881a`-tól). A beállítás-visszaolvasó `0x006175c0` ugyanezt a bejelölt rádiót `ordering = 0` értékként menti. A vizsgált új film út alapállapota tehát a „Legjobb átmenetek” rádió; ebben a beolvasóban nincs hozzá Preferences-kulcs. A panelépítő külön speciális útja a `[+0x2cc]` mezőbe `2`-t ír (`0x00618c83`), ezért a megállapítás nem terjed ki erre a speciális állapotra.

**`ordering != 0` ágak.** A `0x00874ac0` a jelzővektorból minden pozícióhoz a legközelebbi előző és következő megjelölt indexet tölti ki. A `0x00875ee0` ezt a segédfüggvényt használja az album/gráf jelöltút építésekor, csoport- és kiválasztási jelzőket vizsgál, és a `0x00873170` gettert hívja. A `0x00878310` az elődmutatókon visszafelé járva út-elemeket fűz egy listába. A dekompilátum több regiszterbemenete és a függvényhívó argumentumainak kapcsolata nem tisztázott, így az ordering 1 és 2 végső kiválasztási szabálya és kimeneti sorrendje **NINCS MEG**. E három eredmény utasításszintű vagy QEMU-ellenőrzése ebben a körben nem készült.

**Bizonyítottsági fok.** A teljes HOG-jellemzővektor leírása **nyitott**, mert a hossz, cella- és iránysorrend nem azonosítható, és a natív fixture nem futtatta a kivonót. A belső normálási művelet és az ordering ≠ 0 részfunkciói **feltételesek**, mert ezekre csak a bináris/dekompilátum út áll rendelkezésre. A rádió állítása az általános új film útra **megerősített**: a beállítás-beolvasó `0`-t ad, a panelépítő ezt a smart rádióra fordítja, a beállítás-visszaolvasó pedig ugyanazt `ordering = 0`-ként kódolja. A három lépés eltérő függvényben és két irányban ellenőrizhető.

**A két független út.**
- **A, HOG:** Ghidra-C és utasításszintű olvasat a `0x00873cb0` és `0x0088c1a0` útján. Ez belső normálási műveletet mutat, de a végső vektor hosszát és rendezését nem.
- **B, natív mérés:** a G/4 fixture-párjainak közvetlen bemérése a `0x00873e40`-be. A három eredmény egyezik a G/4 értékeivel. Ez külön ellenőrzi a metrikát, nem a HOG-kivonót, így a két út a jellemzővektor-kérdésre nem egyezik és nem ad két független bizonyítékot.
- **Rádió:** az A út a `0x00616940` mezőinicializálása; a B út a `0x00618050` mezőből gombállapotot készít, amelyet a `0x006175c0` `ordering = 0`-ként olvas vissza. Az általános új film út következtetése egyezik.

**Cáfoló kísérlet (15.2).** Megpróbáltam a G/4 fixture-kimenetet a HOG-kivonó független igazolásaként használni. A QEMU-hívás útjának ellenőrzése kimutatta, hogy az előre megadott tömböket közvetlenül a `0x00873e40` pontozó kapja, a `0x00873cb0` nem fut. Ez cáfolja azt az erősebb állítást, hogy a fixture a képből épített jellemzővektort is validálja. Külön cáfoló ellenőrzésként a `0x006173c0` lokális nulláit tekintettem lehetséges „mindegyik rádió kikapcsolva” állapotnak; a `0x00618050` `ordering = 0` ága ezzel szemben kifejezetten bejelöli a smart rádiót, ezért a lokális nullákból levont következtetés hamis.

**Bizonyíték.**

| állítás vagy érték | forrás |
|---|---|
| `0x00873cb0` a `[param_2+0x54] + iStack_10 * 8` címre írja a `0x0088c1a0` eredményét | bináris `0x00873cb0` |
| belső ciklushatárok `0x38` és `0x20`, forráslépés `0x24` | bináris `0x0088c1a0`, `0x0088c1f4`-`0x0088c460` |
| belső normálás: négyzetösszeg + `1.0`, gyök, osztás | bináris `0x0088c3b4`-`0x0088c423`; `0x00c7e328` = `1.0` double |
| köztes vektorhatárok: `0x28`, illetve `5` bejegyzés | bináris `0x0088c480`, `0x0088cd10`; nem végső HOG-dimenzió |
| végső HOG-vektor hossza, cella- és iránysorrendje | NINCS MEG |
| G/4 fixture 1 távolsága: `1.6742424964904785` | mérés (QEMU-i386, G/4 6., `0x00873e40`) |
| G/4 fixture 2 távolsága: `2.055555582046509` | mérés (QEMU-i386, G/4 6., `0x00873e40`) |
| G/4 fixture 3 távolsága: `2.999999892949745e-08` | mérés (QEMU-i386, G/4 6., `0x00873e40`) |
| általános új film modellje `ordering = 0`-ra indul | bináris `0x00616940`, `0x00616a18` |
| `ordering = 0` esetén a smart rádió bejelölt | bináris `0x00618050`, `0x0061881a`-tól |
| a smart rádió visszaolvasása `ordering = 0` | bináris `0x006175c0`, `0x006177a3`-`0x006177a7` |
| a speciális panelág `ordering = 2`-t ír | bináris `0x00618c83` |
| a 3 rádió callback-lokálisai nullázódnak, de ez nem a kijelölési állapot | bináris `0x006173c0`, `0x006173c8`-`0x006173cf`; cáfolat: `0x0061881a` |
| `ordering != 0` út-kiválasztás végső sorrendje | NINCS MEG |

**Fejlesztési teendő (#4182, frissítve).**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `ordering = 0` algoritmusa G/5 szerint; az általános új film úton a smart rádió az alap | `src/picasapy/movie/slideshow.py:691-701` színátlagos lánc, `src/picasapy/movie/mxf.py` saját alapérték | A G szerinti csoportosítás és a `d_HOG` primitív fejleszthető a rögzített etalonokkal. A kiválasztó ne kapjon „eredeti” jelölést, amíg a HOG-jellemzővektor hossza, cella- és iránysorrendje, végső normálása nincs bizonyítva. Az alap rádió-értéket az általános új film úton egyeztesd `ordering = 0`-ra. |
| `ordering = 1/2` gráfút: részfunkciói G/6-ban láthatók, teljes út és kimeneti sorrend nyitott | jelenlegi `slideshow.py` nem valósítja meg ezt a gráfutat | Az ordering 1/2 implementációt ne vedd fel a #4182 eredetit követő fejlesztésébe a gráfút és a sorrend lezárásáig. |

**Kész, ha:**
1. A G csoportosítási etalonok teljesülnek.
2. A `d_HOG` primitív a G/4 6. pont mindhárom natív fixture-jén a feljegyzett értéket adja.
3. A HOG-kivonó végső hossza, cella- és iránysorrendje, valamint normálása bináris útból és független natív méréssel egyezik.
4. Az általános új film út `ordering = 0`-t és a smart rádiót használja.
5. Az ordering 1/2 ág csak azután nevezhető eredetinek, ha az út költsége, kiválasztott indexei és végső sorrendje bizonyított.

**Nyitott.**
- **Válasz (G/10):** a blokkrács (4 × 7 blokk, 2016 elem), a cellánkénti 18 érték és a blokkonkénti L2-normálás megvan; a cella-irányok a `0x0088c480`-ban vannak, lásd G/10.
- **Megválaszolva részben (23. kör, G/11):** a `0x00878310(param_2, &local_20)` két argumentuma a kezdőcsomópont indexe és az elődút-vektor címe. Az elődút iránya megvan (24. kör, G/12: az útvektor a végponttól a kezdőpontig tart). A végső fotóindex-sorrend nyitott: `Ghidra-kör kell: 0x00878720 - a visszakövetés utáni, paraméter nélkül hívott utófeldolgozás: a végső fotóindexek sorrendje ordering = 1/2 esetén [blokkoló]`.
- Az ordering 1/2 teljes út natív QEMU-mérése nincs meg; a `0x00878310` és `0x00875ee0` kiválasztási útja csak dekompilátum alapján vizsgált. A `0x00874ac0` önálló helper függvényszintű leírása a G/3f-ben szerepel, az ordering 1/2 útba kapcsolása nincs natívan ellenőrizve.
- Az általános új film úttól eltérő, `ordering = 2`-t beállító speciális panelág pontos felhasználói feltétele nincs meg.

#### G/7. A HOG-vektor a C-kódból (2026-10-17, #4194)

**Kérdés.** Mi a HOG-jellemzővektor hossza, a cellák és az irányrekeszek bejárási sorrendje, a gradiens számítása, a normálás képlete és blokktartománya, és hogyan kerül a vektor a `0x00873cb0` kimenetébe? Ez a G/6 „HOG-jellemzővektor” része, és a G/5 „Kész, ha” 5. pontjának feltétele.

**Forrás.**
- **A, C-kód:** `referencia/ghidra/2026-10-17-hog-qshow-k4.txt`, a `0x0088c1a0` szakasz (13-144. sor). A hívó: `referencia/ghidra/2026-10-17-film-idoszuro-3.txt`, a `0x00873cb0` szakasz (1-95. sor).
- **B, utasításszintű olvasat:** a G/6 szakasz (`0x0088c1a0` és `0x00873cb0`, a bináris, `annot_disasm.py`). Ez független az A úttól.
- A `0x0088c480` és a `0x0088cd10` törzse nincs a két fájlban, csak a hívóhelyeik. A rájuk vonatkozó állítások ezért nincsenek meg.

**Eredmények (a C-kódból).**

1. **Ciklusok** (A, 43-142. sor). Négy egymásba ágyazott ciklus, a belső elemekkel:
   - `local_20` 0-tól 0x20-ig, 8-as lépéssel: 4 ablak-sor (a = 0..3).
   - `local_24` 0-tól 0x38-ig, 8-as lépéssel: 7 ablak-oszlop (b = 0..6).
   - `local_1c` 2 körben: 2 cella-sor az ablakon belül (i = 0..1).
   - `param_2` 2 körben: 2 cella-oszlop az ablakon belül (j = 0..1).
   - `iVar5` 0xc-től, 0x24-es lépéssel, 2 körben: a cella 18 eleme (9 + 9).

2. **Vektorhossz: 2016 float.** 4 × 7 ablak × 72 elem. Egy ablak 72 eleme = 2 × 2 cella × 18 elem. A 72 osztható 4-gyel, a farok-ciklusok (103-112. és 128-136. sor) nulla kört futnak.

3. **Rács és forrás.** A bemenet 5 × 8-as rács. A `this+0x10` tábla (T) 8 bájtos rekordjainak első dword-je a sor-tábla címe (a sor: `local_20 + 8i`). A sor-tábla 8 bájtos rekordjainak első dword-je a cella-blokk címe (az oszlop: `local_24 + 8j`). Egy cella-blokk 18 folytonos float (72 bájt). A C nem ellenőrzi az 5 × 8 méretet.

4. **Bejárási sorrend.** A kimeneti index (float, a 0. elemtől): k = 504a + 72b + 36i + 18j + m. A forrás: a cella (a+i, b+j), a cella m. eleme.
   - Az ablakok a külső (a) és a belső (b) ciklus sorrendjében követik egymást: w = 7a + b, az ablak kezdete 72w.
   - Egy ablakon belül a cellák sorrendje (i, j) = (0,0), (0,1), (1,0), (1,1), vagyis a cella-koordináták (a,b), (a,b+1), (a+1,b), (a+1,b+1).
   - Egy cellán belül az elemek sorrendje m = 0..17, közvetlen másolással.
   - A kimeneti lépések float-ban: ablak 72, i-sor 36, j-oszlop 18 (a C-ben a mutató-lépés 0x48, 0x24, 0x12 dword).

5. **Átfedés.** Az ablak 1 cella-lépéssel tolódik: a forrás-index b-nként és j-nként is 8 bájttal nő. Egy cella ezért több ablakban is szerepel. A másolatok száma a cella sor-darabszámának (1, 2, 2, 2, 1) és oszlop-darabszámának (1, 2, 2, 2, 2, 2, 2, 1) szorzata. Összesen 8 × 14 = 112 másolat, ez 28 ablak × 4 cella. A legtöbb másolat 4 (például az (1,1) cella).

6. **Gradiens.** A `0x0088c1a0` törzsében nincs gradiens-számítás: nincs különbség-, szög- vagy irányképzés. A törzs másolást, négyzetösszeget, egy függvényhívást (`FUN_0049fe60`) és osztást végez. A két segédhívás (`0x0088c480`, `0x0088cd10`) végezhet számítást, ez a C-ből nem látszik. **NINCS MEG** (a gradiens helye és képlete).

7. **Normálás** (A, 89-136. sor). Ablakonként, a másolás után:
   - S_w = Σ x_t² az ablak 72 elemén (94-101. sor, 18 négyes csoport);
   - d_w = `FUN_0049fe60(S_w + c)`, ahol `c` a `_DAT_00c7e328` (113. sor);
   - y_t = x_t / d_w (115-127. sor).
   - Az ablakok tartománya [72w, 72w + 72), w = 0..27. Az ablakok a kimenetben nem fedik egymást, és együtt lefedik a 2016 elemet.
   - A C-ben a `c` értéke és a hívott függvény neve nincs kiírva. A gyök és az 1,0 a G/6 utasításszintű olvasatából jön.

8. **Kimenet** (A, a `0x00873cb0` 92. sora). A `0x00873cb0` nem ír vektort. A `FUN_0088c1a0(*(int *)(param_2 + 0x54) + iStack_10 * 8)` hívás egy 8 bájtos rekord címét adja át. A `0x0088c1a0` a rekord első dword-jében lévő címre (OUT) írja a 2016 elemet, majd helyben normálja. Az `iStack_10` a C-ben csak deklarálva és használva van, értékadása nincs meg. A kimeneti tároló foglalása (legalább 2016 float = 8064 bájt) a C-ben nincs. A `0x00873cb0` saját számításai (`local_8c`, `local_88`, `FUN_00819f50`, `FUN_008198e0`) a C-ben nem kötődnek a hívás argumentumához. A `this` (ECX) átadása a hívásnál nem látszik.

**Bizonyítottsági fok.**

**Megerősített** (két úton: A a C-kód, B a G/6 utasításszintű olvasata):
- Ciklushatárok: 0x20 (4 ablak-sor) és 0x38 (7 ablak-oszlop). A: 43-142. sor. B: G/6, a 0x38 és a 0x20 határérték.
- Forráslépés 0x24 a 18 elemű blokk két fele között. A: `iVar5 + 0x24`, 64-77. sor. B: G/6, a 0x24 bájtos forráslépés.
- A normálás szerkezete: négyzetösszeg a 72 elemen, majd egy skalárral való osztás. A: 94-127. sor. B: G/6, „négyzetösszeg + 1.0, gyök, osztás”.

**Feltételes** (csak A úton; B nem vizsgálta):
- A 2016 hossz, a 4 × 7 ablak és az 5 × 8 rács.
- Az 1 cella-lépéses átfedés és az ablakon belüli sorrend (i, j, m).
- A `c = 1,0` konstans és a gyök-azonosítás. Ezek B úton állnak, A-ban nincsenek kiírva.

**Nincs meg:**
- A 18 elemű blokk jelentése (irányrekesz-e?) és az 5 × 8 rács jelentése (cellák pozíciója?). A „cella” és „irányrekesz” nevek a HOG-névből jönnek, a C nem nevezi meg.
- A T tábla tartalma és mérete, valamint a `this+0x8` tömb. A `0x0088cd10` és a `0x0088c480` törzse hiányzik.
- A gradiens helye és képlete.
- A kimeneti tároló foglalása és az `iStack_10` index.
- A köztes pontosság: a `float10` (x87) és a float32 tárolás közötti kerekítés nincs a C-ben.

**Cáfoló kísérlet (15.2).** A ciklusokat szó szerint másoló gépi modell futtatását a futtatási engedély megtagadása miatt nem végeztem el. Az alábbi cáfolatok kézi nyomkövetések, nem gépi vagy natív ellenőrzések.
- **H1: az ablakok nem fedik át egymást** (cellánként legfeljebb 1 másolat). **Cáfolva.** A forrás-index b-nként 8 bájttal nő, így a b = 0 és a b = 1 ablak ugyanazt a cellát olvassa. Az (1,1) cella 4-szer másolódik: (a = 0, i = 1) vagy (a = 1, i = 0), és (b = 0, j = 1) vagy (b = 1, j = 0).
- **H2: a normálás a teljes 2016 elemű vektoron fut.** **Cáfolva.** A négyzetösszeg és az osztás ciklusa 72 elemre szól (a végét a `local_28 = 72w + 69` adja, a csoportszám 18), és ablakonként újraindul.
- **H3: a hossz 1008 (két ablak-sor).** **Cáfolva.** A külső ciklus határa `local_20 < 0x20`, ez 4 kört ad.
- **Nyomkövetés, k = 72** (a = 0, b = 1, i = j = 0, m = 0). Az első írás címe `puVar8 - 8`, azaz OUT + 4·72. A forrás a sor-tábla 0. sora (`TB + 0`), majd az 1. oszlop (`+ 8·1`), a 0. elem: X[0][1][0]. Az első írás OUT + 0 címre esik, tehát a -2 dword-eltolás nem ír OUT elé.
- **Eredmény:** a három hipotézis mind ellentmond a C-kódnak. Ez nem második út, a bizonyítottsági fok ettől nem nő.

**G/5 „Kész, ha” 5. pontjának új állapota.** ⛔ Még részben teljesült. A rádió-rész lezárult (G/6). A HOG-vektor normálásának szerkezete két úton áll. A 2016-os hossz és a rács-/ablak-sorrend csak C úton áll (feltételes). A rács forrása, a gradiens és a kimeneti tároló nincs meg. Az „eredeti” jelölés továbbra sem adható. (A G/5 szövegét nem írtam át.)

**Fejlesztési következmény (#4182).** A `d_HOG` primitív (G/4 6. pont) és a G csoportosítás továbbra is fejleszthető. A C szerinti elrendezés (2016 elem, 4 × 7 ablak, ablakonkénti normálás) megírható, de feltételesként kell jelölni, amíg a második út és a rács forrása nincs meg.

**Nyitott.**
- **Megválaszolva részben (23. kör, G/11):** a `0x0088cd10` harmadik argumentuma (`param_3`) a 5 × 8 cellarács; hogy ez a hívóban a `this+0x10` tábla-e, a hívó (`0x0088c1a0`) dekompilálásával dől el, ez nincs ebben a körben.
- **Megválaszolva (23. kör, G/11):** a `0x0088c480` nem ír a `this+0x10` táblába: a `param_2` (nagyság) és `param_3` (szög) vektorokba ír, 40 sor × 64 float. Számol gradienst: csatornánkénti központi különbség, a három csatorna közül a legnagyobb `dx² + dy²`.
- `Ghidra-kör kell: 0x0088c1a0 - a `0x0088c480` és a `0x0088cd10` hívási argumentumai (melyik kép-struktúra és melyik `this` mező adja a cellarácsot) [nem blokkoló]`
- `Ghidra-kör kell: 0x00873510 - a 0x00873cb0 hívójának a rekordtömb (`*(param_2+0x54)`) és a kimeneti tároló (legalább 2016 float) foglalása, valamint az `iStack_10` értékadása [blokkoló]`
- `Ghidra-kör kell: 0x0049fe60 - a hívott függvény azonosítása (gyök-e) és a `_DAT_00c7e328` értéke [nem blokkoló: a G/6 utasításszintű olvasata gyöknek mondja, a C-ben nincs kiírva]`

#### G/8. A HOG-rács és a gradiens a C-kódból (2026-10-17, #4194)

**Kérdés.** Mekkora a HOG-rács, és mit jelent egy cella? Mi a 18 elemű blokk? Mi a gradiens szűrője, iránya és nagysága, és hogyan kerül a rekeszbe? Hogyan készül elő a bemeneti kép? Hol foglalódik a kimeneti tároló, mi az `iStack_10`, és mi a `0x0049fe60`? Ez a G/7 „Nincs meg" listájának a folytatása.

**Forrás.**
- **A, C-kód (ez a kör):**
  - `referencia/ghidra/2026-10-17-hog-racs-ytwindow.txt`: `0x0088cd10` (1-331. sor), `0x0088c480` (334-730. sor), `0x00873510` (733-1123. sor), `0x0049fe60` (1126-1231. sor).
  - `referencia/ghidra/2026-10-17-hog-qshow-k4.txt`: `0x0088c1a0` (1-146. sor).
  - `referencia/ghidra/2026-10-17-film-idoszuro-3.txt`: `0x00873cb0` (1-96. sor).
- **B, utasításszintű olvasat (G/6):** a `0x0088c1a0` ciklushatárai (0x20, 0x38), a 0x24 forráslépés, a normálás szerkezete és a `0x0049fe60` „gyök" olvasata. Ezt a kör nem mérte újra.
- A `0x00980670` és a `0x00982d00` szakasz a #4443-hoz tartozik, ezt nem használtam.

**Eredmények (a C-kódból).**

1. **Rács: 5 sor × 8 oszlop, azaz 40 cella.** A `0x0088cd10` öt sort épít (`local_6c`: 0, 8, 16, 24, 32), soronként nyolc cella-rekorddal (`local_70`: 0..56, 8-as lépéssel). Minden cella 19 float-os tárolót kap (count 0x13). A `0x0088c1a0` is 5 × 8 rácsot olvas.
2. **Egy cella 8 × 8 gradiens-pixel.** A (R, C) cella a gradiens-tábla 8R..8R+7 sorait és 8C..8C+7 oszlopait fedi. A tábla 40 sor × 64 oszlop. A 0. oszlop x = 73, a 0. sor y = 169. A (R, C) cella képterülete: x = 73+8C és 80+8C között, y = 169+8R és 176+8R között. A teljes terület 64 × 40 pixel (x = 73..136, y = 169..208).
3. **Gradiens-szűrő.** Központi különbség, félszorzó nélkül, három bájt-csatornán (a 4 bájtos pixel 0., 1., 2. bájtja). Egy (x, y) pixelre dx_c = I_c(x+1, y) - I_c(x-1, y) és dy_c = I_c(x, y+1) - I_c(x, y-1). Csatornánként g_c² = dx_c² + dy_c². A végső g² = max_c g_c² (egész szám). Ha g² = 0, a nagyság és a szög is 0.
4. **Nagyság és szög.** A nagyság M = F(g²), ahol F = `FUN_0049fe60` (lásd 12. pont). A szög A = `FUN_00c29cca()`. Ha A < 0, akkor A += W (W = `_DAT_00cf4b88`). A `FUN_00c29cca()` nem kap argumentumot a C-ben, ezért nem látszik, melyik (dx, dy) pár és melyik csatorna a bemenete. Az atan2-szerű viselkedés csak feltevés, a negatív ágú korrekció alapján.
5. **Rekesz.** p = A × s (s = `_DAT_00cf4b80`). k a p egész része; ezt a `FUN_00c0b1e0` és a `FUN_00c29990` hívás adja (azonosításuk nyitott). H[k] += M × ((k+1) - p), H[k+1] += M × (p - k). A súly tehát a nagyság, nem a négyzete, ha F gyök. A cella összegzése után H[0] += H[18]: a 19. slot a 0. rekeszbe adódik. A használt rekesz 18 db (0..17). A korrekció után A nem negatív, ezért negatív rekesz nincs.
6. **Blokk.** A `0x0088c1a0` az (a, b) ablakban (a = 0..3, b = 0..6) a (a+i, b+j) cellákat másolja (i, j ∈ {0, 1}). Kimeneti index: 504a + 72b + 36i + 18j + m, m = 0..17. Egy ablak 72 elem, összesen 28 × 72 = 2016. Az ablakok 1 cella lépéssel tolódnak, ezért egy cella több ablakban is szerepel.
7. **Normálás (blokkonként).** S = Σ x² az ablak 72 elemén. d = F(S + c), c = `_DAT_00c7e328`. y = x / d. Nincs második normálás és nincs levágás.
8. **Bemeneti kép.** A C-ben nincs méretezés és nincs szürkeárnyalat-képzés; a gradiens három bájt-csatornát olvas. A kép forrása rejtett: a `0x0088c1a0` a `FUN_0088c480()` hívást argumentum nélkül mutatja. A kép legalább 138 × 210 pixel kell, hogy minden gradiens-pixel számoljon. A széli pixelekre nincs `else` ág, a `0x0088c480`-ban pedig nincs memset: a kihagyott pixelek helyén a tábla régi, nullázatlan érték marad.
9. **Kimeneti tároló.** A `0x00873510` rekordonként 2016 float-os tömböt foglal. A fejléc 0. bitje 1 ágon `FUN_0097c810(ptr, 0x1f80)` (8064 bájt), 0 ágon 8192 bájt. Mindkét ágon a count 0x7e0 (2016) lesz. A rekord-lista (this+0x54) N elemű, ahol N a bemeneti lista (this+0x14) elemszáma.
10. **iStack_10: megválaszolva (13. kör, feltételes).** A `0x00873cb0` törzsében nincs értékadás, az érték a hívó `edi`-je. A `0x00873510` `0x00873aed` sorában `push edi`, majd `0x00873af0`-ban `push esi` áll, a callee `esi` (az első verem-argumentum) az `ebx`-be kerül, a második (az `edi`) pedig a `0x00873e08` `mov ecx, [esp+0xd4]` sorban olvasódik, és a `[ebx+0x54] + index*8` címet adja. A `0x00873510` 1119. sora `FUN_00873cb0(param_1, uVar7)` alakban hív: az `uVar7` az `edi`, a `param_1` az `esi`, a C és az asm így egyezik. A hívó `edi`-je a ciklusindex (az első hívásnál 0). A verem-egyenleg teljes ellenőrzése (a `0x00873cb0` közbenső `push`-jai) nem futott le, ezért ez feltételes.
11. **A két tábla összerendelése: NINCS MEG.** A `0x0088cd10` a this+0 tömböt súlyként, a this+0x8 tömböt szögként olvassa. A `0x0088c480` a nagyságot az első, a szöget a második kimeneti táblába írja. Ez csak akkor egyezik, ha a hívás (kép, this+0, this+0x8) sorrendben adja a táblákat. Ez ellenőrzés, nem bizonyíték.
12. **`0x0049fe60`: burkoló.** `float10 FUN_0049fe60(void)`: meghívja a `FUN_00c0b310()`-t, az eredményt float-ra kerekíti. Más művelet nincs benne. Hogy a cél gyök-e, a C-ből NINCS MEG. A G/6 bináris olvasata gyöknek mondja.

**Bizonyítottsági fok.**
- **Megerősített (A és B úttal):** 4 × 7 ablak és 2016 elem (A: a `0x0088c1a0` ciklusai és a `0x00873510` 0x7e0 / 0x1f80 foglalása; B: a G/6 határértékei, 0x20 és 0x38, és a 0x24 lépés). A 72 elemű blokk. A blokk-normálás szerkezete: négyzetösszeg, konstans, osztás (A: `0x0088c1a0`; B: G/6).
- **Feltételes (csak A úton):** az 5 × 8 rács és a 8 × 8 cella; a 18 rekesz és a 0. rekeszbe való összevonás; a lineáris szögsúlyozás; a [-1, 0, +1] szűrő és a csatorna-maximum; a kimeneti sorrend.
- **Nincs meg:** s, W és c értéke; a szög-függvény bemenete; F azonosítása; a kép forrása és előkészítése; az iStack_10; a két tábla összerendelése.

**Cáfoló kísérlet (15.2).** Kézi nyomkövetés a C-kódon, gépi futtatás nélkül.
1. H: a cella 4 × 4 pixel. **Cáfolva:** a `0x0088cd10` sorciklusa 8 sort jár be (`local_60 + 8`), az oszlopciklusa 8 oszlopot, oszloponként 8 pixelt jár be.
2. H: a gradiens egycsatornás (szürke). **Cáfolva:** a `0x0088c480` három csatornát olvas, és maximumot vesz (`iVar8 < iVar17`).
3. H: L2-Hys (levágás, majd második normálás). **Cáfolva:** a `0x0088c1a0` normálása egyetlen osztás-ciklus.
4. H: a 19. slot elvész. **Cáfolva:** `pfVar16[0x12] + *pfVar16` a 0. rekeszhez adja.
5. H: a normálás cellánként történik. **Cáfolva:** az összeg az ablak 72 elemén fut.
6. H: a két tábla fel van cserélve. **Nem cáfolt:** a hívási argumentumok rejtettek (lásd 11. pont).

**A G/5 „Kész, ha" 5. pontjának új állapota.** ⛔ Még részben teljesült, de szűkebb. Megvan a hossz (2016), a blokk-szerkezet és a sorrend (a sorrend feltételes). Nincs meg: s, W, c, a szög-függvény, F azonosítása és a kép forrása. A G/5 szövegét nem írtam át.

**Fejlesztési következmény (#4182).** A HOG-kivonó teljes képlete nem áll össze: hiányzik s, W, c, a szög-függvény bemenete és a képforrás. Ezért nincs megvalósítható leírás. Feltételesen megírható az elrendezés: 5 × 8 cella, 8 × 8 pixel, 18 rekesz, 2 × 2 blokk, 2016 elem, blokkonkénti L2 normálás. Eredetinek nem jelölhető, amíg a konstansok és a szög nincs bizonyítva. A `d_HOG` primitív (G/4 6. pont) ettől független.

**Nyitott.**
- `Ghidra-kör kell: 0x00c29cca - az irányszög bemenete (melyik (dx, dy) pár, melyik csatorna) és a függvény azonossága [blokkoló]`
- `Ghidra-kör kell: 0x00c0b310 - a 0x0049fe60 célja: gyök-e (sqrt) [blokkoló]`
- `Ghidra-kör kell: 0x00cf4b80 - a rekesz-skála (s) double-értéke [blokkoló]` **Lezárva (kiegészítés): közvetlen PE-olvasás.**
- `Ghidra-kör kell: 0x00cf4b88 - a szögkorrekció (W) double-értéke [blokkoló]` **Lezárva (kiegészítés): közvetlen PE-olvasás.**
- `Ghidra-kör kell: 0x00c7e328 - a normálás epsilonja (c) double-értéke; a G/6 bináris olvasata szerint 1.0, ezt a kör nem ellenőrizte [blokkoló]` **Lezárva (kiegészítés): közvetlen PE-olvasás.**
- `Ghidra-kör kell: 0x0088c1a0 - a FUN_0088c480 hívásának argumentumai: a kép-struktúra és a két tábla sorrendje [blokkoló]`
- **0x00873cb0 hívóhelye (13. kör, #4194): megválaszolva (asm, egy út, a C-vel egyezik); a kép forrása nyitott.** A `0x00873af1` (`0x00873510` 469. sora): `ECX = [[esi+0x14]] + ebx` (a rekordtömb `ebx` bájt-eltolású eleme), `EAX = [ebp+0xc]` (a 0x00873510 második argumentuma), verem: `push edi` (kimeneti index, `iStack_10`), `push esi` (a 0x00873510 objektuma). A callee `EAX`-ben kapott `edi`-je a kép-forrás objektum (`in_EAX`): ettől jön a `+0x4c` vtábla-hívás a rekord `+0x30` mezőjével, és a `+0x48` vtábla-hívás a `+0x34` mezővel. A HOG-kivonó: a `0x00873e1b` `call 0x0088c1a0`, `ECX = esi+0x34` (a 0x00873510 objektum `+0x34` mezője), `EAX = a rekord`, kimenet a `[ebx+0x54] + index*8` slot. A cella-, irány- és normálási részletek a `0x0088c1a0`-ban vannak, lásd G/7-G/8. Ghidra-kör kell: 0x00873510 - a `[ebp+0xc]` kép-forrás objektumának osztálya és a `+0x4c`/`+0x48` vtáblái [blokkoló a kép forrásához] → **a G/9 szerint: a `0x00873510` csak továbbadja (nincs osztály-információ); a következő cím a `0x00699cd0` és a `0x008149a0`**
- `Ghidra-kör kell: 0x00c0b1e0 és 0x00c29990 - a padló- és egész-konverzió azonosítása [nem blokkoló: p >= 0 esetén a két művelet egyezik]`

**Kiegészítés: a konstansok és a két CRT-belépő a binárisból (2026-10-17, közvetlen PE-olvasás, `pe_dis.read`/`f64`).**

| cím | bájtok | érték | jelentés |
|---|---|---|---|
| `0x00cf4b80` (s) | `0000006016eb0640` | 2,8647887706756592 | 9/π float32-pontossággal tárolva (9/π = 2,864788975…) |
| `0x00cf4b88` (W) | `f1d4c853fb211940` | 6,2831853 | 2π (nyolc tizedesre) |
| `0x00c7e328` (c) | `000000000000f03f` | 1,0 | a normálás állandója; a G/6 olvasatával egyezik |

Ebből: a szög [0, 2π) tartományban van (negatív esetén + W), a rekesz-index p = A · 9/π ∈ [0, 18), tehát **18 előjeles irányrekesz, rekeszenként 20°**, a 19. hely (p ≥ 17 felső szomszédja) a 0. rekeszbe fordul vissza (5. pont). A két hívott függvény a CRT matematikai belépőinek mintáját mutatja: `0x00c29cca` = `mov edx, 0x00d491c0; jmp` (a CRT táblás belépője, az atan2 jelöltje), `0x00c0b310` = `sub esp,0xc; fst qword [esp]; call …` (a `_CIsqrt` mintája). Ez a két azonosítás **feltételes** (bájtminta, a cél nincs végigkövetve); a három konstans **megerősített** (a bájtok közvetlen kiolvasása, és a G/6 utasításszintű olvasata a c-re ugyanezt adja).

#### G/9. A 15. kör (2026-10-20, #4194): a `[ebp+0xc]` kép-forrás a `0x00873510`-ben csak továbbadódik; a HOG-hívók adják

*Forrás:* utasításszintű olvasat (`annot_disasm.py`) a `0x00873510` (1930 bájt), a `0x00873cb0` (390), a `0x00819680` (145), a `0x0081fc30` (5855) és a `0x00824090` (662) címen; a `.ghidra/2026-10-20-ghidra-15.txt` C-törzse a `0x00873510`-re (1701-2093. sor); a `0x00cbdec4` vtábla-immediate pásztázása a teljes `.text`-en (`paszta.py`, 2 884 879 utasítás, csúcs RSS 49 MiB).

- **A `0x00873510` nem olvassa a kép-forrást (megerősített, C és asm, két út).** A `[ebp+0xc]` (C-ben `param_3`) csak tárolódik: `mov dword ptr [esi+0x18], edx` (0x00873b37 és 0x00873c97, a két kilépési ágon; C: `*(param_1+0x18) = param_3`). Ezen kívül minden rekordra EAX-ként adódik át a `0x00873cb0`-nak (`mov eax, [ebp+0xc]` 0x00873aea, `call 0x00873cb0` 0x00873af1). A függvény hívott céljai (7 db) között nincs vtábla-hívás a kép-objektumon.

- **A rekordok és a kimenet (megerősített, asm és C).** A bemeneti lista a `[esi+0x14]`, a rekord 0x38 bájtos (`add ebx, 0x38`, 0x00873b01); a hívás ECX-e a k-adik rekord (`mov ecx, [eax]`, `add ecx, ebx`, 0x00873ae5-0x00873aee). A rekordonkénti kimenet 2016 float (8064 bájt): `push 0x1f80` (0x008737f1), a darabszám `0x7e0` (`cmp eax, 0x7e0`), a tag `or eax, 0xfc0`. A `[this+0x4c]` jelzőtömb minden eleme 0 a `param_4 == 0` ágon (asm: `mov dword ptr [ecx+eax*4], 0`, 0x00873c86), és 1 a másik ágon (C: 2070. sor).

- **A kép-forrás a `0x00873cb0`-ban (megerősített, asm).** Az `edi` (EAX-ből) a kép-objektum. A `mov eax, [edi+0x4c]`, `lea ecx, [edi+0x4c]`, `mov edx, [esi+0x30]`, `call eax` (0x00873d04-0x00873d16) és a `[edi+0x48]`-es megfelelője (`[esi+0x34]`, 0x00873d40-0x00873d5e) a kép-objektumon belüli két alobjektum slot 0 metódusát hívja, a rekord `+0x30` és `+0x34` mezőjével. Ez a korábbi G/8 olvasatot erősíti meg. Az alobjektumok osztálya: NINCS MEG.

- **A HOG-objektum és a kép-forrás hívói (megerősített, asm, egy keresés).** A `0x00cbdec4` (`HOGSimilarityComputer::vftable`) immediate-je egyetlen helyen fordul elő: a konstruktor `0x00819680` (`mov dword ptr [esi], 0xcbdec4`, 0x0081968a). A konstruktort két függvény hívja: `0x0081fc30` (0x00821174) és `0x00824090` (0x008241bf). Mindkettő a vtábla 1-es slotját (`mov edx, [edx+4]`, a `0x00873510`) hívja, és a kép-forrás a 2. stack-argumentum (`[ebp+0xc]` a hívottban):
  - `0x00824090`: `mov eax, [ebx+0x2bc]`, `push eax` (0x008241d3-0x008241dc); a bemeneti lista `edi`.
  - `0x0081fc30`: `mov ecx, [ebp+0x94]`, `push ecx` (0x0082117f-0x00821190); a bemeneti lista `lea eax, [ebp+0x4e0]`.

- **Az osztály és a méret: NINCS MEG.** A kép-forrás osztálya, a `[ebx+0x2bc]` és `[ebp+0x94]` mezők írója, a `+0x4c`/`+0x48` alobjektumok vtábla-célja, és így a kép tartalma (teljes kép, arc-kivágás, szürkeárnyalat) és mérete nem olvasható ki ebből. A rekord 0x38 bájtos, a `0x00873cb0` a `+0x30`, `+0x34` mezőket adja a kép-objektumnak; hogy ez arc-kivágást jelent-e, feltételes.

- **Bizonyítottsági fok.** A `0x00873510` tárolása és a rekordonkénti EAX-átadás: **megerősített** (C és asm, két út). A 2016 float-os kimenet: **megerősített** (asm és C). A `0x00873cb0` két vtábla-hívása a kép-objektumon: **megerősített** (asm, egy út). A HOG-hívók és a `[obj+0x2bc]`, `[obj+0x94]` forrás: **megerősített** (asm, két hívó). A kép osztálya, tartalma és mérete: **NINCS MEG**.

- **Cáfoló kísérlet.** (1) Azt állítottam, hogy a `0x00873510` olvassa a kép-objektumot. Cáfolva: a függvény csak tárolja (`+0x18`) és továbbadja (EAX). (2) Azt állítottam, hogy a HOG-objektum a saját képét hozza létre. Cáfolva: a kép-forrás a hívótól jön (`[ebx+0x2bc]` vagy `[ebp+0x94]`). (3) Azt állítottam, hogy csak az egyik HOG-hívó létezik. Cáfolva: mindkettő megvan (`0x00824090`, `0x0081fc30`).

- **Következő cím (c).** `0x00699cd0` (a `0x00824090` hívója, a `[ebx+0x2bc]` kép-forrás és az `ebx` objektum forrása) és `0x008149a0` (a `0x00814330` hívottja; a `0x0081fc30` a hívottja, nem a hívója, 17. kör helyesbítés; a `[ebp+0x94]` mező forrása): ezek adják a kép-forrás osztályát és a `+0x4c`/`+0x48` alobjektumok slot 0 célját.

**17. kör (2026-10-20, #4194): a `0x00699cd0` módválasztó gyár; a `0x008149a0` nem olvassa a `[ebp+0x94]` mezőt.**

*Forrás:* `.ghidra/2026-10-20-ghidra-17.txt` (C: `0x00699cd0` 696-893. sor, `0x008149a0` 894-1199. sor; a HÍVÓK és HÍVOTTAK fejlécek).

- **`0x00699cd0(mód)` (megerősített, C, egy út; az osztályok nincsenek megnevezve).** A mód szerint ad objektumot: `5` és `6`: a `0x00824090` eredménye (osztály és méret NINCS MEG); `7`: nullázás `0x770` (1904) bájtra, majd `0x006999c0`; `0`-`4`: nullázás `0x498` (1176) bájtra, majd `0x0068c880` (a `2`-nél előbb `0x00698100` hívás). A `4`-nél, ha `FUN_005c7e40() < 2`, a `3`-as ág fut (`FUN_005cb180`, két 32 bites elemből álló tömb); egyébként az `1` és a `4` ágon `FUN_005c76b0` hívódik. Tehát a `[ebx+0x2bc]` módfüggő objektum; a mód értéke a hívóban van (NINCS MEG).
- **`0x008149a0` (megerősített, C): nem olvassa a `[ebp+0x94]` mezőt.** A `param_1+0x48` (lista) és `param_1+0x4c` (darabszám) mezőkön dolgozik, a `3` és `4` típusú elemekre sorszámot ír (`+8`). Egyetlen hívója a `0x00814467` a `0x00814330`-ban. A 15. kör G/9 szövege a hívási irányt fordítva írta le: helyesbítve.
- **A `[ebp+0x94]` kép-forrás osztálya: NINCS MEG.** A mező forrása a `0x00814330`-ban keresendő.
- **Bizonyítottsági fok.** A `0x00699cd0` ágai és a `0x498`/`0x770` nullázási méretek: **megerősített** (C, egy út; asm-összevetés nincs). Az osztályok és a tartalom: **NINCS MEG**. A `0x008149a0` és a `+0x94` függetlensége: **feltételes** (C, egy út).
- **Cáfoló kísérlet.** A 15. kör hívási irányát a HÍVÓK és HÍVOTTAK fejléc cáfolta. A `5`/`6` ág `0x00824090`-jét nem cáfoltuk, csak nincs leírva.
- **Következő cím (c).** `0x00814330`: megválaszolva a 18. körben (lent); a `[ebp+0x94]` ebben a függvényben nincs.

**18. kör (2026-10-20, #4194): a `0x00814330` nem olvassa a `[ebp+0x94]`-et; a `0x008149a0` mód-argumentuma `[this+0x2d8]`; a megtartott kép nincs ebben az ágban.**

*Forrás:* `annot_disasm.py` a `0x00814330` (503 bájt) és a `0x00625000` (a `0x0062515d` körül); a `.ghidra/2026-10-20-ghidra-18.txt` HÍVÓK-fejléce és C-je a `0x00814330`-ra; a teljes `.text` pásztázása (`paszta.py`, `memoria_kapu()` első művelet, 2 884 879 utasítás, csúcs RSS 93 MiB) a `[reg+0x2d8]` célú dword-írásokra (25 találat).

- **A hívás (megerősített, asm és C).** A `0x00814467` (`call 0x8149a0`) két argumentumot tol: a `[ebp+0x2d8]`-at (második) és az `esi = ebp+0x48` listát (első). A C ugyanezt adja: `FUN_008149a0(iVar2, *(param_1+0x2d8))`, ahol `iVar2 = param_1 + 0x48`.
- **A `[ebp+0x94]` nincs a `0x00814330`-ban (megerősített, asm).** Az 503 bájtos függvényben nincs `+0x94`-es operandus. A G/9 ezt a mezőt ide tette; ez téves volt. A `[ebp+0x94]` a `0x0081fc30` (HOG-hívó) saját keretének mezője, a 0x0081fc30 pedig nem hívója a `0x00814330`-nak. A kép-forrás kérdése a 0x0081fc30 láncában marad.
- **A mód-argumentum forrása (feltételes).** A `0x00814330` két hívója a `0x0061d1c0` (`0x0061d1d2`) és a `0x00625000` (`0x0062515d`). A `0x00625000`-ban a tárolás (`mov dword ptr [esi+0x2d8], edi`, `0x0062512b`) előtt az `edi` a `lea edi, [esp+0x10]` (`0x006250ce`) verem-lokális címe, a későbbi `add dword ptr [edi+4], ebx` (`0x00625136`) pedig ugyanennek a szerkezetnek a darabszámát növeli. A `+0x2d8` tehát egész módérték helyett egy `[mutató, darabszám]` szerkezet címe lehet. Ez csak a lineáris olvasatból jön: a tárolás előtt az `esi` `xor`-ral nullázódik (`0x00625129`), a pontos ágat vezérlési gráf nélkül nem döntöttem el. A `0x0061d1c0` ágát nem olvastam.
- **A `+0x2d8` írói (megerősített: pásztázás).** A 25 íráshely közül literál 1 (`0x006d90fb`, `FUN_006d8eb0`), literál 4 (`0x00639d02`, `FUN_00639c00`), literál 0 (több hely); a többi regiszterből vagy argumentumból ír. A 0x00814330 mód-argumentumának egyetlen írója sincs azonosítva a hívóláncig.
- **A kiválasztási szabály (NINCS MEG ebben az ágban).** A `0x00814330` fájlt nyit (`CreateFileA`-szerű hívás, a `.\\yt\\ytIO.cpp` assert alapján), a `0x008149a0` pedig csak a `param_1+0x48` lista 3-as és 4-es típusú elemeire ír sorszámot (`+8`); egyik sem választ képet. A megtartott kép szabálya a G/2-G/5 láncban van (`0x0081b800` → `0x00874320`, a `0x00874e40` költségképzés), és ott nyitott: a pontszámhoz a HOG és a Neven getter-osztályok `+0x30`/`+0x34` mezőinek jelentése kell.
- **Bizonyítottsági fok.** A hívás és az argumentumok: **megerősített** (asm és C). A `[ebp+0x94]` hiánya: **megerősített** (asm; a G/9 állítás helyesbítve). A mód-argumentum forrása: **feltételes** (egy lineáris olvasat). A kiválasztási szabály: **NINCS MEG**.
- **Cáfoló kísérlet.** (1) Azt állítottam (G/9), hogy a `0x00814330` a `[ebp+0x94]`-et olvassa: cáfolva az 503 bájtos törzsben. (2) Azt feltételeztem, hogy a `0x008149a0` választ képet: cáfolva, a `3`/`4` típusra sorszámoz.
- **Lezárás.** Nem zárható. A megvalósítható rész, a csoportosítás, már kódban van: `src/picasapy/movie/burst.py`, `capture_groups`, szomszédos, egész másodpercre kerekített időkkel, `delta >= T` új csoporttal, ez egyezik a natív méréssel. A kiválasztó (`select_chain`) színátlagot használ, a kód saját megjegyzése szerint nem az eredeti HOG-szabályt; a fejlesztői teendő tehát a kiválasztás pontszáma, amely a megtartott kép szabályától függ, ezért nincs ismeretlen nélküli (a) jegytörzs. A (c) lépés (a 19. körben a getterek mezői megvannak, lásd lent): `0x00874e40` és `0x0088c1a0`. A viselkedési ellenőrzéshez a jegy törzsében kért, Windowson készített hat képes felvétel szolgál.

**19. kör (2026-10-20, #4194): a két getter mezői megvannak; a pontszám súlyai és a megtartott kép szabálya NYITOTT.**

*Forrás:* `.ghidra/2026-10-20-ghidra-19.txt` (a `0x00873e40` és a `0x008742a0` C-kódja); `.ghidra/2026-10-20-ghidra-14.txt` (a `0x00873cb0`); a PE-olvasás a vtáblákra és a `0x00cf4bd8` konstansra; `annot_disasm.py` a `0x0048c440`-re (299 bájt); a bináris-index `xrefs` táblája; a `src/picasapy/movie/burst.py` és a `src/picasapy/movie/slideshow.py` 717-724. sora.

- **Az osztályok (megerősített, PE-olvasás).** A `0x00cbdecc` és a `0x00cbdec4` a `HOGSimilarityComputer` vtáblájában áll (COL `0x00d0fb9c`), a `0x00cbdedc` és a `0x00cbded4` a `NevenSimilarityComputer`-ében (COL `0x00d0fb4c`). Mindkét this-eltolás 0. A getter a 2. slot; a 0. slot `0x00819720`, illetve `0x00819890`, az 1. slot `0x00873510`, illetve `0x00874010`.
- **A HOG-getter (`0x00873e40`) mezői (megerősített, C, egy út).** A törzsben nincs `+0x30` és nincs `+0x34` eltolás. A getter a `this+0x4c` jelzőtömböt olvassa (0-nál a `0x00873cb0` tölti be és 1-re állítja), a `this+0x54` 8 bájtos bejegyzéseit pedig `[mutató, méret]` párként: a bin-szám a méret `>> 1`. A távolság `Σ (a_i - b_i)^2 / (a_i + b_i + ε)`; a ciklus négyes csoportokban fut, a maradék külön ágon. A `0x00873cb0` a bejegyzés címét a `0x0088c1a0`-nak adja át, amely kitölti; a tartalma nyitott.
- **Az ε (megerősített, PE-olvasás).** A `0x00cf4bd8` float32-ként `0x3e79458e`, vagyis 9,99999993922529e-09 (a Ghidra `(float)_DAT_00cf4bd8`-ja). A kódunk double-ben számol (`_HOG_EPSILON = 1e-8`), ezért bitpontos egyezést nem állítunk.
- **A Neven-getter (`0x008742a0`) mezői (megerősített, C és asm).** A visszatérés `1 - sim`. `sim = 1,0`, ha a `this+0x34` egész-tömb mindkét indexén nem nulla és a két érték egyenlő: ilyenkor nincs Neven-hívás, a távolság 0. Egyébként `sim` a `0x0048c440`-ből jön, a rekord `+0x30` mezőjével (a cím `**(this+0x14) + idx*0x38 + 0x30`); ha a hívás nem nulla, `sim = 0`. A `+0x30` tehát a rekord mezője, a `+0x34` a getter-objektum tagja, nem a rekordé.
- **A `0x0048c440` (megerősített, asm, egy út).** A két kulcsot a `this+0x269c` objektumban (`0x006b6a50`) keresi meg. Ha a keresés sikertelen, vagy a motor nulla (a `this+0x2e14` jelző nélküli első hívásnál a `0x0045f0c0` inicializál), a visszatérés nem nulla (9 vagy `-1`), ezért `sim = 0`. Sikeres keresésnél a `this+0x2e10` objektum virtuális hívása (`[vtbl+0x3c]`, a 15. indexű slot) írja a `sim` értékét a kimeneti float-ba. A korábbi nyitott kérdés (a Neven 0/1 szemantikája) így válaszolt: a visszatérési érték siker/hiba kód, a hasonlóság a kimeneti float. A `this+0x2e10` osztálya NINCS MEG (futásidejű objektum).
- **A pontszám és a kiválasztó.**
  - *Mai kódunk (mérve).* A `src/picasapy/movie/burst.py` `select_chain` a `d_hog` χ²-alakú távolságot használja. A jelöltek sorrendje +1, -1, +2, -2 …, kizárja a már választottat és a középpont csoportját, szigorú minimumot keres (`_MAX_COST = 1e8`), döntetlennél a korábbi jelölt marad. Neven-tag nincs. A jellemzőt a `slideshow.py` 717-724. sora adja: a kép színátlaga (`np.mean(frame, axis=(0, 1))`), nem a `0x00873cb0` HOG-vektora.
  - *A súlyok (NINCS MEG).* A korábbi körök (Codex, Haiku) „1,0·HOG + 0,4·Neven" szorzókat írtak le. Ezeknek nincs bináris forrásuk a specben, és ebben a körben sem igazoltam őket. A `0x00874e40` összegzése a következő lépés.
- **A három kérdésre adott válasz.** (1) A `+0x30`/`+0x34` jelentése: a `+0x30` (rekord) a Neven-kulcs, a `this+0x34` a Neven-getter azonossági rövidzárja; mindkettő a Neven-tagban van, a HOG-tagban nincs. (2) A megtartott kép: NINCS MEG, a súlyok és a `0x00874e40` hiányzik. (3) A `select_chain` csere: a HOG-vektor (`0x0088c1a0`) és a súlyok nélkül nem végezhető el bináris alapon.
- **Bizonyítottsági fok.** A getter-mezők és a `0x0048c440` törzse: **megerősített** (C és asm). A `+0x30` kulcs szerepe a keresésben: **feltételes** (a `0x006b6a50` keresőt nem olvastam végig). A `this+0x34` jelentése: **feltételes** (a feltöltője NINCS MEG). A súlyok és a megtartott kép: **NINCS MEG**.
- **Cáfoló kísérlet.** (1) Azt feltételeztük, hogy a HOG-getter a `+0x30`/`+0x34` mezőket olvassa: cáfolva, a törzsben nincs ilyen eltolás. (2) Azt, hogy a `+0x34` a rekord mezője: cáfolva, a `0x008742a0` a getter-objektumról (`param_1`) olvassa.
- **Lezárás (#4194): (c).** A (b) nem lehetséges, mert a megtartott képre nincs két független út. Az (a) sem, mert a jegy Eredeti oszlopa a súlyokat és a HOG-vektort kéri. Következő Ghidra-címek:
  - **Válasz (G/10):** a `0x00874e40` nem ad vissza indexet (`void`), és nem a megtartott kép útja `ordering = 0`-n; a Neven-szorzó nincs benne, csak a bájtflag szerinti `-2^-63` szorzó. Lásd G/10.
  - **Válasz (G/10):** a `this+0x54` bejegyzés 2016 elemű, 4 × 7 blokkos, L2-normált vektor; a cella-irányok nyitottak (`0x0088c480`, lásd G/10).
  - A 2026-10-19-es export a hálózati mappában van; ezt a kör nem olvasta (a NAS-tilalom miatt), és a viselkedési ellenőrzés a felhasználó kérésében marad.
- **Nyitott kérdések mérlege.** 0 nyílt · 1 lezárva (a getter-mezők) · 2 blokkolt (a súlyok és a megtartott kép; a `select_chain` cseréje) · 0 hatókörön kívül · 0 csak nyitva.

#### G/10. A 20. kör (2026-10-20, #4194): a `0x00874e40` gráfépítő és a `0x0088c1a0` HOG-blokkok

*Forrás:* `.ghidra/2026-10-20-ghidra-20.txt`: a `0x00874e40` C-törzse (14-768. sor), a `0x0088c1a0` C-törzse (771-914. sor), a HÍVÓK és HÍVOTTAK fejlécek. Kiegészítő: a 3514-3546. sor (`ordering != 0` ág), a 3906. sor (a `0xcf4968` konstans PE-olvasata) és a G/8 (`0x00c7e328`, 5178. sor).

**Kérdés 1 (`0x00874e40`):** melyik kép marad egy sorozatból? Ez a pontszám-összegzés súlyait és a visszatérési indexet kérdezi.

**Válasz 1: a `0x00874e40` nem ad vissza képet.** A függvény `void`, nincs visszatérési indexe. A `0x0081b800` az `ordering != 0` ágon hívja (a `0x0081bbac` hívóhelyen), a kiválasztást pedig a `0x00877c50` végzi (legkisebb összköltségű út). Az `ordering = 0` ágon (alapbeállítás, a tulajdonos exportja) a `0x0081c9b0` dönt, lásd G/5.

- **Pontszám-összegzés (megerősített, C, egy út).** A törzsben nincs súlyozott összeg és nincs getter-ciklus. A `0x00873170` hívás (390. sor) a `local_3c` float-tömbbe jelöltenként egy értéket ír; a `local_44` a jelöltek indexlistája, a középpont `local_74`. Ha a `*param_4` bájttömb `p` indexű eleme nem nulla, az érték `(float)_DAT_00cf4968` szorzót kap. Ez a konstans `-2^-63` (PE-olvasás: kb. -1,0842·10^-19). Más szorzó nincs. A Neven-tag 0,4-es súlya nem ebben a függvényben van (lásd G/5, `0x00824090`).
- **Élszűrés (megerősített, C).** A jelölt-ablak szélét `c + param_7`-ről lefelé csökkenti, amíg az index az elemszám (`*param_1`) alatt van és a `*param_3` dátumtábla különbsége legfeljebb `0x16e` (366). Egy középponthoz legfeljebb 150 (`0x96`) jelölt kerül a listába. Az élek a `param_1[3]` és a `param_1[5]` listákba íródnak, 12 bájtos rekordokként. A `0x16e` egysége NINCS MEG.
- **Kimenet.** A függvény a `param_1+2` mezőt 1-re állítja, és kilép. Ez a gráf, nem egy kiválasztott kép.
- **Bizonyítottsági fok.** A `void` és a `0x00873170`-os hívás: **megerősített** (C). A `-2^-63` szorzó: **megerősített** (PE). A bájtflag forrása (`*param_4`): **NINCS MEG** (3946. sor). A kiválasztási szabály `ordering != 0`-ra: **NINCS MEG** (a `0x00877c50` a következő cím).
- **Cáfoló kísérlet.** A jegy feltételezése szerint ez a sorozat-kiválasztó. Cáfolva: nincs visszatérési érték, és a `0x0081b800` a kiválasztást a `0x00877c50` után végzi. Súlyozott összeg sincs (csak a flag-szorzó), tehát a 0,4-es Neven-súly nem innen jön.

**Kérdés 2 (`0x0088c1a0`):** a HOG-vektor tartalma: cellák, irányok, normálás.

**Válasz 2: a blokkrács és a normálás megvan, a cella-irányok nincsenek.**

- **Rács (megerősített, C és G/8).** A külső ciklus 4 lépést tesz (`0x20`), a belső 7-et (`0x38`): 4 × 7 = 28 blokk. Az (a, b) blokk a (a+i, b+j) cellák 2×2 ablaka, i, j ∈ {0, 1}. A kimeneti index `504a + 72b + 36i + 18j + m`, m = 0..17. A teljes vektor 2016 float.
- **Cellánként 18 érték (megerősített, C).** A cellarekord 19 float (G/8). A blokk minden cellából a 0..17. mezőt másolja két 9-es lépésben (`iVar5 = 0xc` és `0x30`). A 18. mező (index 18) nem kerül a blokkba.
- **Normálás (megerősített, C és PE).** Blokkonként `S = Σ x²` a 72 elemen, majd `d = sqrt(S + c)`, ahol `c = _DAT_00c7e328 = 1.0` (PE: `000000000000f03f`). Ezután minden elem `x / d`. Nincs második normálás és nincs levágás.
- **Cella-irányok: NINCS MEG.** A cellahisztogram (gradiens-szög, rekeszek száma, előjel) a `0x0088c480`-ban és a `0x0088cd10`-ben van. A `0x0088c480` nincs dekompilálva, a `0x0088c1a0` nem olvassa a gradienst. A 18 érték tehát a cella 0..17. mezője, de hogy melyik irányrekesz, azt nem mondja meg.
- **Bizonyítottsági fok.** A rács, a 72 elemű blokk, a 2016 elem és a normálási képlet: **megerősített** (két út: a C-törzs és a G/6 utasításszintű olvasata egyezik). A cellánkénti irányok: **NINCS MEG**. Az `1.0` konstans: **megerősített** (PE).
- **Cáfoló kísérlet.** (1) A G/6-ban feltételezett L2-Hys normálás: cáfolva, egyetlen osztásciklus van. (2) A 4 cella × 19 érték blokk: cáfolva, a 19. mező nem másolódik.

**Lezárás (#4194, 20. kör): (c).** (A 23. kör G/11 szakasza felülírja.) Az `ordering = 0` kiválasztási szabály megvan (G/5, két független út). Az (a) lezárás nem lehetséges: a Codex-kész jegytörzs a HOG-vektort kéri, a cellahisztogram nélkül a vektor nem reprodukálható. A (b) sem: az irányrész és a Neven-tag nyitott. Következő Ghidra-címek:

- **Megválaszolva (23. kör, G/11):** gradiens-szög a győztes csatornán, `atan2(dy, dx)`, előjeles (0 és 2π között), 18 irányrekesz (s = 9/π); a bemeneti ablak fix: x = 73 ... 136, y = 169 ... 208. Részletek: G/11.
- **Megválaszolva (23. kör, G/11):** 5 × 8 cella, cellánként 8 × 8 pixel és 19 float; a 19. mező (index 18) a 0. rekeszhez adódik a cella lezárásakor.

**Jegytörzs-hatás.** A tulajdonos exportja `burstmodethresh = 0` mellett készült, tehát nincs csoportosítás (G/5, Kész ha 1. pont). Csoportok nélkül a „melyik kép marad egy sorozatból" kérdés nem merül fel, a sorrendet viszont a `ordering = 0` lánc adná. Az export időrendje nincs megmagyarázva: a lánc a legkorábbi képből indul, és a jellemzőtávolság szerint választ. Hogy az időrend ebből következik-e, azt a HOG-vektor nélkül nem lehet ellenőrizni.

#### G/11. A HOG-cella, a gradiens és a kiválasztás szerződése (23. kör, 2026-10-20, #4194)

**Kérdés.** A jegy három címet kér a HOG-hoz: `0x0088c480` és `0x0088cd10` (cellahisztogram: gradiens-szög, rekeszek száma, előjel, irányrekeszek), és `0x00877c50` (a kiválasztási szabály `ordering != 0` esetén).

**Forrás.** `.ghidra/2026-10-20-ghidra-23.txt` (C, 1-732. sor), és a helyi `Picasa3.exe` diszasszemblyje (`annot_disasm.py`): a `0x0088c480` teljes függvénye, valamint a `0x0049fe60`, `0x00c29cca`, `0x00c2a6ec` és `0x00c0b310` törzse.

**Ablak és bemenet (`0x0088c480`).**
- A `param_1` képstruktúra: `+0x4` sorlépés (pixelben), `+0x8` szélesség, `+0xc` magasság, `+0x10` pixelpuffer. Egy pixel 4 bájt, sorrendben B, G, R (a `+2` bájt a piros). A határ-ellenőrzés: x < szélesség - 1 és y < magasság - 1.
- A kiolvasott ablak fix, a C-ben és az asm-ben is (`add edi, 0xa9`): x = 73 ... 136 (64 oszlop), y = 169 ... 208 (40 sor). Határon kívüli pixelhez nincs írás.
- Kimenet: a `param_2` a nagyságokat, a `param_3` a szögeket kapja, mindkettő 40 sor × 64 float.

**Gradiens, nagyság, szög (`0x0088c480`).**
- Csatornánként központi különbség: `dx_k = c(x+1) - c(x-1)`, `dy_k = c(y+1) - c(y-1)`, `k` = R, G, B. Az asm a `[esp+0x38]` ... `[esp+0x4c]` mezőkbe rakja: dyR, dyG, dyB, dxR, dxG, dxB.
- A legnagyobb `dx_k² + dy_k²` csatorna győz (`cmp eax, edi; jle`: szigorúan nagyobb kell, döntetlennél a korábbi marad). A győztes csatorna dy és dx értéke a `[esp+0x1c]` és `[esp+0x20]` helyen marad.
- Nagyság: `M = sqrt(max_k(dx_k² + dy_k²))` (`call 0x0049fe60` → `call 0x00c0b310`, benne `fsqrt`). A súly M, nem M².
- Szög: `A = atan2(dy*, dx*)`, ahol `*` a győztes csatorna. A hívó `fild` sorrendje: ST(1) = dy*, ST(0) = dx*. A célfüggvény (`0x00c2a6ec`) `fabs` után `fpatan`-t hajt végre, amely ST(1) = y, ST(0) = x konvenciót követ.
- Negatív szög korrekció: ha `A < 0`, `A += W` (`fadd qword [0x00cf4b88]`). Eredmény: `A` a [0, 2π) tartományban, tehát előjeles, teljes 360 fokos irány.
- Nulla gradiens (a legnagyobb összeg 0): a C szerint `M = 0` és `A = 0`. Az asm ezt `fst` utasítással írja ki, az ST(0) értékét nem igazoltam (a függvényben nincs `fldz`): **feltételes**.

**Rekesz, cella, blokk (`0x0088cd10`).**
- `param_1` a nagyság-vektor, `param_2` a szög-vektor, `param_3` a cellarács: 5 sor, soronként 8 cella.
- Cella: 8 × 8 pixel (cellasor 8 képsor, cellaoszlop 8 képoszlop).
- Cellarekord: 19 float (`0x13`), a `_memset` nullázza.
- Rekesz-index: `p = A × s`, ahol `s = _DAT_00cf4b80 = 9/π` (2,8647887706756592, PE-olvasat). Mivel `A` a [0, 2π) tartományban van, `p` a [0, 18) tartományban. `k` a padló: `p ≥ 0` esetén a csonkolt egész adja (`0x00c29990`, asm: `cvttsd2si`). A `0x00c0b1e0` padló-azonosítása nincs ellenőrizve, de a `p ≥ 0` miatt az eredményt nem befolyásolja.
- Lineáris súlyozás két rekeszbe: `H[k] += M × ((k+1) - p)`, `H[k+1] += M × (p - k)`.
- A 19. mező (index 18) a 0. rekeszhez adódik a cella lezárásakor: `H[0] += H[18]`. Így 18 előjeles irányrekesz van (0 ... 17), egyenként 20 fok (360 / 18).
- Blokk: 2 × 2 cella × 18 rekesz = 72 elem, L2-normálás, `c = _DAT_00c7e328 = 1,0`. A 4 × 7 blokkrács 2016 elemet ad (G/7). A blokkréteget ebben a körben nem olvastam újra (G/10).

**Kiválasztás (`0x00877c50`, részben).**
- Megvan a szerkezet: rétegenkénti legolcsóbb-út ciklus. A költségtömb `*param_1` darab f32 elemből áll, kezdőértéke 1e8 (`0x4cbebc20`). A kezdőcsomópont (`param_2`) költsége 0. Minden rétegben: `0x008781a0` (relaxálás), `0x00878820` (a jelölt-vektor kezelése), majd a lezárás-ellenőrzés.
- Lezárás: ha a rétegszám ≥ `param_4` ÉS `cost[param_3] < _DAT_00c7da00` (1e8), akkor visszakövetés (`0x00878310(param_2, &local_20)`) és kilépés. A dekompilált `(c < x) == (c == x)` alak `x < c`-t jelent. Ez a végpont-feltétel: a végpont költsége véges, és legalább `param_4` lépés történt.
- Nincs megvan: az élköltség forrása (`0x008781a0`), a jelölt-vektor rendezése (`0x00878820`), a visszakövetés (`0x00878310`), és a fotóindex-leképezés. Ezek nincsenek dekompilálva.

**Bizonyítottsági fok.**
- Ablak, csatornánkénti központi különbség, győztes csatorna, `M = sqrt(max)`, súly `M`: **megerősített** (C és asm, két út).
- Szög `atan2(dy*, dx*)`, operandussorrend: **megerősített** (két út: a hívó `fild` sorrendje, a célfüggvény `fpatan` konvenciója). Az SSE2-ág (a `0x00c2a450` dispatcher másik ága) nincs végignézve, ezen az ágon **feltételes**; a fejlesztői teszt kényszeríti ki a sorrendet.
- `W = 2π`, `s = 9/π`, `c = 1,0`: **megerősített** (PE-olvasat és asm `fadd qword [0x00cf4b88]`).
- 18 előjeles rekesz és a 19. mező összevonása: **feltételes** (egy út: a `0x0088cd10` C-törzse).
- Cella 8 × 8, 5 × 8 rács, 19 float: **feltételes** (egy út: a ciklusszámlálók a C-ben).
- Kiválasztás (`0x00877c50`): szerkezet **megerősített** (C); élköltség és visszakövetés **NINCS MEG**.

**Két független út.** (A) a dekompilált C (`0x0088c480`, `0x0088cd10`, `0x00877c50`); (B) a helyi EXE utasításai (`0x0088c480` teljes diszasszemblyje, a segédfüggvények törzse). A gradiens-ablak, a csatornaválasztás, `M`, a szög operandusa, `W` és `s` egyezik. A cella-méret és a 19. mező kezelése csak (A) úton van.

**Cáfoló kísérletek.**
1. „A szög az összegzett csatornák gradiense": cáfolva, a szöget a győztes csatornán számolja (asm: `[esp+0x1c]`, `[esp+0x20]`).
2. „A nagyság M²": cáfolva, a `0x0049fe60` hívásláncban `fsqrt` van.
3. „A szög `atan2(dx, dy)`": cáfolva, a hívó `fild` sorrendje és a célfüggvény `fpatan` konvenciója együtt adja `atan2(dy, dx)`-et.
4. „A 19. mező a 18. szögrekesz": cáfolva, a cella lezárása `H[0] += H[18]`-cal összevonja.
5. „Az ablak a hívótól függ": a konstansok (`73`, `169`) a kódban fixek. Hogy a hívó melyik képet adja, az a `0x0088c1a0` hívójától függ, és az nincs dekompilálva.

**Fejlesztési következmény (#4194).** A HOG-leíró (gradiens, 18 előjeles rekesz, 8 × 8 cella, 2 × 2 blokk, 2016 elem) a G/11 szerint megírható. A `d_hog` már van a `src/picasapy/movie/burst.py`-ban. A kiválasztás (`ordering != 0`) és a bemeneti kép-forrás nyitott, ezért a jegy nem zárható.

**Lezárás (#4194, 23. kör): (a) a HOG-leíróra.** A megvalósítható rész (a HOG-leíró) megvan. A nyitott mellékkérdés a „Nem része” pont: a kiválasztási szabály (`ordering != 0`) és a bemeneti kép-forrás (`0x00873cb0`, G/9).

A két cím (`0x008781a0`, `0x00878310`) a 24. körben megválaszolva, lásd G/12 alább.
Ghidra-kör kell: `0x00878820 - a jelölt-vektor rendezése vagy nyesése a rétegek között [nem blokkoló]`

#### G/12. Az élköltség, a visszakövetés és a végpont szerződése (24. kör, 2026-10-20, #4194)

**Kérdés.** A G/11 két nyitott címe: `0x008781a0` (rétegenkénti élköltség) és `0x00878310` (visszakövetés: az útvektor sorrendje és a végső fotóindex-leképezés).

**Forrás.** `.ghidra/2026-10-20-ghidra-24.txt` (C, a két függvény); a hívó `0x00877c50` (`.ghidra/2026-10-20-ghidra-23.txt`, 733-1030. sor); a helyi `Picasa3.exe` diszasszemblyje (`annot_disasm.py 0x00877c50`: a hívóhely a `0x0087813b`-`0x0087814d` szakaszban, a prológus a `0x00877c50`-nél).

**Hívási szerződés (asm, megerősített).** A hívóhelyen: `edx = [esp+0x50]` (kezdőcsomópont), `eax = [esp+0x54]` (végpont), `esi = [esp+0x5c]` (kimeneti útvektor objektuma), `ecx = lea [esp+0x28]` (`&local_20`, a rétegenkénti elődtár); a verembe `push ecx`, majd `push edx`. A prológus négy `push`-t tesz (`ebx`, `ebp`, `esi`, `edi`), ezért a `0x00877c50` argumentumai: gráf `esp+0x4c`, kezdőcsomópont `+0x50`, végpont `+0x54`, minimális rétegszám `+0x58`, kimeneti útvektor `+0x5c`. A C-dekompiláció az 5. argumentumot nem mutatja. A `0x00878310` az útvektort ESI-n kapja; a `&local_20` a rétegenkénti elődök tára, nem az útvektor.

**A gráfobjektum (C, megerősített).** A `+0x0` mező a csomópontok száma `N` (rétegenként ugyanannyi). A `+0xc` csomópontonként 8 bájtos rekordot tart: az élek listájára mutató és az élek száma (`>> 1`). Élrekord 12 bájt: `+0x4` a célcsomópont indexe (int), `+0x8` az élköltség (float). A rétegenkénti költségtömb `N` elemű, kezdőértéke `1e8`; a kezdőcsomópont költsége 0.

**`0x008781a0` (rétegenkénti relaxálás).**
- Az élköltség itt nem keletkezik: a függvény a rekord `+0x8` float-ját olvassa. HOG-távolság, időkülönbség és súly a törzsben NINCS; ezek a gráfobjektum építőjében dőlnek el (a `0x00877c50` hívója a `0x0081bd62`-ben a `0x0081b800`).
- Képlet: `új[c] = min(régi[u] + w(u, c))` a `(u, c)` élekre, ahol `régi[u] < 1e8` (`_DAT_00c7da00`, PE-olvasat: 100000000.0). A forrás-indexek növekvő sorrendben futnak.
- Döntetlen: szigorú `<`, ezért a kisebb forrás-index (és a listában előbb álló él) marad.
- Kimenet: az új költségtömb a `0x00891110(&local_8)` hívással kerül a hívó költségtömbjébe (a hívás célja a C-ben nincs kiírva); az elődtömbbe `elődtömb[c] = u` kerül.

**`0x00878310` (visszakövetés).**
- Bemenet: EAX = végpont, 1. argumentum = kezdőcsomópont, 2. argumentum = `&local_20`, ESI = kimeneti útvektor.
- A ciklus a végponttól indul. Amíg a csomópont-index nem egyezik a kezdőcsomópont indexével, hozzáfűzi a csomópontot az útvektorhoz, majd az elődtárból (a `local_1c` szerinti rétegrekordból, visszafelé) veszi a következőt. A ciklus után a kezdőcsomópont kerül a végére.
- Sorrend: `[végpont, előd(végpont), …, kezdőcsomópont]`, azaz időrendben fordított (megerősített: a C és a hozzáfűzés sorrendje).
- Megállási feltétel: csomópont-index, nem rétegindex (`while (in_EAX != param_1)`). Ha a kezdőcsomópont indexe egy köztes rétegben is megjelenik az úton, a visszakövetés ott leáll. Hogy a gráfban ilyen ismétlés előfordul-e, nem vizsgáltam (feltételes).
- A végén paraméter nélkül hívott `FUN_00878720()` az ESI-ben kapott útvektoron átrendez vagy fotóindexre képez-e, nincs dekompilálva. A végső fotóindex-leképezés innen nyitott.

**Tulajdonosi export (`burstmodethresh = 0`).** A csoportosítás szabálya (G/5, megerősített): `delta < T` esetén a kép a csoportban marad, `delta >= T` esetén új csoport. `T = 0` mellett minden kép új csoport, a kiválasztás nem fut, és a bemeneti (időrendi) sorrend marad. Az export ezzel magyarázható, a kiválasztási lánc ehhez nem kell.

**Bizonyítottsági fok.**
- Hívási szerződés, ESI-kimenet, útvektor-sorrend: **megerősített** (két út: az asm a hívóhelyen és a prológuson, a C a törzsben).
- Relaxálási képlet, döntetlen, `1e8`-határ: **megerősített** (C; a konstans PE-olvasata).
- A `0x00891110` célja: **feltételes** (egy út).
- Élköltség forrása (HOG, idő, súly): **NINCS MEG**.
- Végső fotóindex-leképezés: **NINCS MEG** (`0x00878720`).

**Cáfoló kísérletek.**
1. „A `0x008781a0` számolja a HOG-távolságot": cáfolva. A törzsben nincs gradiens-, hisztogram- vagy időhívás, csak a `+0x8` olvasás.
2. „A visszakövetés a rétegszámot nézi": cáfolva. A feltétel csomópont-index (`in_EAX != param_1`).
3. „Az útvektor a kezdőponttól indul": cáfolva. Az első elem a végpont.

**Jegy „Kész, ha” (kiválasztási szabály).** ⛔ Nem teljesül: a szabály egésze nincs meg, az élköltség forrása és a fotóindex-leképezés nyitott. A HOG-leíró (G/11) a 23. körben már lezárult.

**Lezárás (#4194, 24. kör): (c).** Nem zárható, mert az élköltség és a végső leképezés hiányzik. Következő Ghidra-címek:

#### G/13. A végső fotóindex-sorrend és a gráfépítő hívója (25. kör, 2026-10-20, #4194)

**Kérdés.** (1) A `0x00878720`: a visszakövetés utáni, paraméter nélkül hívott függvény átrendezi-e az útvektort, vagy fotóindexre képezi-e le? (2) A `0x0081b800`: ki írja a gráfobjektum élrekordjainak célindexét és élköltségét, és honnan jön a HOG-távolság és az időkülönbség?

**Forrás.** `.ghidra/2026-10-20-ghidra-25.txt` (C, a két törzs és a hívási listáik); `.ghidra/2026-10-20-ghidra-24.txt` (a `0x00878310` C-törzse); a bináris-index `functions` és `xrefs` táblája. A `0x00875ee0` és a `0x00874e40` törzse nincs dumpolva; róluk csak a hívási éleket olvastam ki az indexből.

**1. A `0x00878720` helyben fordít, nem képez le (C, megerősített).** A függvény a `*param_1` 4 bájtos elemű tömböt fordítja meg: az `n` elemű tömb (`n = param_1[1] >> 1`, ugyanígy olvassa a `0x0081b800` is) `i`. és `n-1-i`. eleme cserélődik, `i < n/2`-ig. Nincs benne hívás, táblaolvasás vagy fotóindex-keresés. Hívói az indexben, mind feltétel nélküli `call`: `0x00878310` (hívóhely `0x00878707`), `0x005e5ce0` (`0x005e5dcd`), `0x0071abc0` (`0x0071af70`). A `0x00878707` a `0x00878310` 1029 bájtos törzsének végén áll, utána csak néhány bájt van, tehát ez a visszakövetés utolsó hívása. A másik két hívó vizsgálatlan.
- Következmény: a `0x00878310` által épített `[végpont, …, kezdőcsomópont]` sorrend a `0x00878720` után `[kezdőcsomópont, …, végpont]`.
- Cáfolat („a `0x00878720` fotóindexre képez"): cáfolva, a törzsben csak csere van.

**2. A végső sorrend: a lánc sorrendje, a fotórekord-leképezés a `0x0081b800` végén (C, megerősített a műveletekre; feltételes a jelentésükre).** A `0x0081b800` a láncot a `puStack_18` tömbben építi:
- kezdete a 0. csomópont (25. dump 283-287. sor);
- minden szakaszban a visszakövetett út `puStack_10[1..n-1]` elemei kerülnek a láncba; a `puStack_10[0]` (a szakasz kezdőpontja) kimarad, mert már a láncban van (364-404. sor);
- `param_3 == 1` és `[0x1da]` nulla esetén a láncelemek a `[0x13e]` táblán át képződnek (842-847. sor);
- a kiírás (848-865. sor): `[0x13a][k] = [0x13c][lánc[k]]`; a `[0x1c][k]` a 56 bájtos rekord `+0x30` mezőjét kapja, a `+0x34` mező egy virtuális getteren át a `[0x23]` tömbbe kerül. Utólagos rendezés nincs; a függvény a lánc hosszát adja vissza (895. sor).
- A lánc növekvő sorrendje és a `[0x13c]` tábla jelentése (csomópont → fotórekord-index) nincs igazolva: a relaxálás csak a forrás-indexek sorrendjét rögzíti, a `[0x13c]` írója nincs dumpolva. Ezért a „végső fotóindex-sorrend" feltételes.

**3. A `0x0081b800` nem írja az élrekordot (C, megerősített; a hívási szint, vtábla-hívás nélkül).** A függvény a gráfobjektumot (`param_1+0x1d1`) és a bemeneti tömböket adja át az építőnek (257-280. sor): `[0x1da]` nulla és `param_3 != 2` esetén a `0x00875ee0`-t, egyébként a `0x00874e40`-t. Átadott paraméterek: a szomszéd-tartomány `uVar4 = N / (K-1)` (127. sor); a `param_1+0x1b3` vagy `+0x1b5` (a `param_4` függvényében) és a `param_1+0x1b7` vagy `+0x1b9` (a `param_5` függvényében) mutató. Az élrekord (G/12: `+0x4` célindex, `+0x8` float élköltség) írása az építőkben van. A `0x0081b800` törzsében nincs 12 bájtos élrekord-mező írása, csak tömbelem-írás.
- Időkülönbség: a `0x0081ae10` egyetlen hívója a `0x0081b800` (index), a `param_4` nem nulla ágban (131-133. sor). A csoportosítás szabályában megerősített (G/5, QEMU-mérés). Az élköltségbe való bevonása NINCS MEG.
- HOG-távolság: a `0x00875ee0` és a `0x00874e40` közvetlen hívottjai között nincs sem a HOG-leíró (`0x0088c480`, `0x0088cd10`), sem a `0x0081ae10`. A hívottak: `0x00873170`, `0x00874320` (G/3g: index-vektor), `0x00874ac0` (szomszéd-kitöltő), `0x00878760` (3×), és memóriakezelők. A HOG-távolság tehát a mutatóként átadott tömbökből jön, vagy a getterekből (`0x00873170`, `0x00878760`); melyik, azt a `0x00875ee0` törzse dönti el.

**Bizonyítottsági fok.** Az építők kiválasztása és a láncépítés műveletei: megerősített (C; a hívási élek az indexszel egyeznek). A végső fotóindex jelentése és a lánc növekvő volta: feltételes. Az élköltség összetétele (HOG, időkülönbség, súly): NINCS MEG.

**Cáfoló kísérletek.** (1) „A `0x00878720` fotóindexre képez": cáfolva, csak csere van benne. (2) „A `0x0081b800` írja az élrekordot": cáfolva a törzs alapján, csak tömbelem-írások vannak. (3) „A `0x0081b800` számolja a HOG-távolságot": cáfolva, nincs HOG-leíró-hívás.

**Jegy „Kész, ha” (kiválasztási szabály).** ⛔ Nem teljesül: az élköltség összetétele nincs megírva. Nálunk: a `src/picasapy/movie/burst.py` `select_chain` a HOG-χ²-távolságot (`d_hog`) pontozza, Neven-tag és időkülönbség nélkül; a jellemzőforrás injektált. Fejlesztői (a) lista a költségképlet nélkül nem írható meg.

**Lezárás (#4194, 25. kör): (c).** A `0x00875ee0` kérdéseit a 26. kör részben megválaszolta (lásd G/13b). Ghidra-kör kell: 0x00874e40 - a másik építő: mikor hívódik (`[0x1da] != 0` vagy `param_3 == 2`), és ugyanazt a költséget számolja-e [nem blokkoló]

#### G/13b. A 26. kör (2026-10-20): a `0x00875ee0` törzse, az élrekord írói, a költség és a bemenetek (#4194)

**Kérdés.** A G/13 két nyitott pontja: (1) ki írja az élrekord célindexét és élköltségét a `0x00875ee0`-ban; (2) a HOG-távolság és az időkülönbség honnan jön (a `param_1+0x1b3`/`+0x1b5` és `+0x1b7`/`+0x1b9` tömbökből, vagy máshonnan).

**Forrás.** `.ghidra/2026-10-20-ghidra-26.txt` (C, a `0x00875ee0` törzse); `.ghidra/2026-10-20-ghidra-25.txt` (a hívó `0x0081b800`: a 127. és 132. sor, a hívóhely a 266. sor); `referencia/ghidra/2026-10-17-film-idoszuro-2.txt` (a `0x00873170` C-törzse, 2204. sortól). Az `int *` indexelés miatt a dekompilátum `+0x1b3` jelölése bájtban `+0x6cc` (4 × 0x1b3); a `+0x141` = `+0x504`, a `+0x13e` = `+0x4f8`, az `+0x1be` = `+0x6f8`, az `+0x1d1` = `+0x744`.

**1. Az élrekord értékei (C, megerősített).** A `0x00875ee0` minden horgony `c` és jelölt `k` párra három értéket állít össze: forrás `c` (`local_34`), cél `local_30 = local_84[k]` (a jelölt pozíciója a rendezett sorban), költség `local_2c = local_64[k]` (a getter kimenete). Ezt a 12 bájtos rekordot a `FUN_00878760(&local_34)` hívás adja át, három helyen. A C-törzsből látszik, hogy a rekord egy ideiglenes vektorba kerül (`local_4c`, mérete `local_48`), és az utána következő ciklus másolja a csomópont-listákba: a horgony előre-listájába (`param_1[3] + c*8`, `+0xc`), a horgony `param_1[5] + c*8` (`+0x14`) listájába, és a harmadik hívásnál a cél `param_1[5] + cél*8` listájába, a forrás és a cél felcserélve. A `0x00878760` törzse nincs dumpolva, a `this` átadása a C-ben nem látszik; a `+0x4` cél és `+0x8` költség mezőkiosztás a G/12 szerinti (feltételes).

**2. A költség: gyorsítótáras getter a provider `+8` slotjából (C, megerősített a hívási lánc).** A `0x00875ee0` egyetlen költséghívást tesz: `FUN_00873170(*(*param_2), horgony, &jelöltek, &költségek, 0)`. Az első argumentum a provider objektum, `O = *(*param_2)`, vagyis a `this+0x504` mutatón át elért burkoló első mezője. A `0x00873170` a `(**(code **)(*O + 8))(horgony, jelölt)` vtábla-hívással kéri a távolságot, és gyorsítótárat használ: a kulcs `O[+0xc] * horgony + jelölt` (64 bites), találatnál a tárolt float. A költségtömb kezdőértéke 1,0 (`0x3f800000`).

**3. Jelzőbájt-szorzó (C, a művelet megerősített; a jelentése nincs meg).** Ha a jelölt elemre a `*param_3` (a `this+0x6f8` bájt-vektora) nem nulla, a költség a `_DAT_00cf4968` szorosára változik. A konstans a G/2b szerint negatív és nagyságrendileg 2^-63, így a jelölt költsége gyakorlatilag nulla; ez a PE-olvasatra támaszkodik. A jelzőbájt jelentése: NINCS MEG.

**4. Időkülönbség (C, megerősített a törzsre).** A `0x00875ee0` törzsében nincs időtag. Az idő egyetlen úton jut be: a `*param_4` egész tömb (a hívó `+0x6cc`, ha a `param_4` nem nulla, különben `+0x6d4`) a csoportkizárásban szerepel, a jelölt csoportja nem lehet a horgonyé. A tömböt a `0x0081ae10` állítja elő (a hívó 132. sora); a dátum- és küszöbbemenete NINCS MEG.

**5. HOG-távolság (C, megerősített a törzsre).** A `0x00875ee0` nem hívja a HOG-leírót (`0x0088c480`, `0x0088cd10`), és a `0x0081ae10`-t sem. A távolság a provider `+8` slotjából jön (2. pont). Ha a provider a HOG-osztály, a slot a `0x00873e40` (G/2c; a dekompilátuma a `2026-10-17-film-4400-4194.txt`-ben van). A Neven-tag (G/3: `SmartMultiPersonTrans` és `+0x6f4`) egy összetett objektum slotjában lenne; ez a `0x00875ee0`-ból nem látszik.

**Cáfoló kísérletek.**
1. „A `0x00875ee0` számolja a HOG-távolságot": cáfolva, a törzsben nincs HOG-leíró hívás; a távolság egyetlen getter-hívásból jön.
2. „Az időkülönbség az élköltségbe kerül": cáfolva a törzsre; az idő csak egyenlőség-vizsgálatot ad a csoportazonosítón át.
3. „A `0x00875ee0` írja a célt a memóriába": részben cáfolva: az értékeket ő állítja elő, a memóriaírás a `0x00878760`-ban van.

**Bizonyítottsági fok.** Az értékek előállítása és a getter-hívás: megerősített (C; a hívási élek az indexszel egyeznek). A provider osztálya és a `+8` slot célja: NINCS MEG. A jelzőbájt jelentése: NINCS MEG. Az időkülönbség forrása (a `0x0081ae10` bemenete): NINCS MEG.

**Jegy „Kész, ha” (kiválasztási szabály).** ⛔ Nem teljesül: az élköltség összetétele (provider osztály, jelzőbájt, Neven-tag) hiányzik, ezért nincs olyan fejlesztői (a) lista, amely a `select_chain` cseréjéhez elég lenne. A 25. kör „Nálunk” megállapítását ebben a körben nem ellenőriztem újra.

**Lezárás (#4194, 26. kör): (c).** A kiválasztási szabály még nincs teljesen meg: a provider osztálya, a jelzőbájt jelentése és a csoportazonosító-tömb bemenete hiányzik.

**Válasz (27. kör, #4194):** a provider osztálya és a `+8` slot megvan (HOG, `0x00873e40`); a `0x0081ae10` kimenete és küszöb-argumentuma megvan, a küszöb forrása és a dátum-mező nyitott. Részletek és bizonyítottsági fok: G/14.

#### G/14. A 27. kör (2026-10-20): a provider osztálya, a csoportazonosító-tömb bemenetei, és a T=0 eltérés (#4194)

**Kérdés.** (1) A `0x00873170` a `this+0x504` tömb 0. elemének `+8` slotját hívja: melyik osztály, és HOG-e vagy Neven-tag az élköltség? (2) A `0x0081ae10` a `+0x6cc` csoportazonosító-tömböt tölti: mi a dátum- és a küszöbbemenete?

**Forrás.** `.ghidra/2026-10-20-ghidra-27.txt` (a `0x00873170` és a `0x0081ae10` C-törzse); `.ghidra/2026-10-20-ghidra-25.txt` és `-26.txt` (a hívóhelyek); asm (`annot_disasm.py`): `0x00824090` (662 bájt), `0x0081fab0` (369), `0x0081fc30` (a hívóhely körül), `0x0081b800` (4514), `0x006175c0` (a hívás környéke), `0x00819680` (145), `0x00819850` (51), `0x00873e40` (454, az eleje); bináris-index: `rtti` (vtábla-slotok), `xrefs` (konstruktor-hívók).

##### G/14/1. Az élköltség provider-osztálya: HOG (megerősített, két út)

- A provider-tömb a gráfobjektum `this+0x504` mezőjében van (elemszám: `this+0x508`), a súlytömb `this+0x50c` (méret: `this+0x510`). A `0x0081fab0` tölti: az első argumentum a provider (`mov [eax+edx*4], ecx` @`0x0081fb4b`), a második a súly (`fstp [eax+edx*4]` @`0x0081fc01`).
- A `0x00873170` a `this+0x504` tömb 0. elemét kapja: `O = *(*param_2)`, a 25. dumpban a `param_2` a `this+0x504` címe.
- **Út A (vezérlési folyam).** A `0x00824090` (a Filmkészítő építője) @`0x008241bf` hívja a HOG-konstruktort (`0x00819680`), @`0x008241e1` `fld1` (súly 1,0), @`0x008241ea` `call 0x81fab0`: ez az első hozzáadás, tehát index 0. A Neven-konstruktor (`0x00819850`) csak @`0x0082425c`-nél van, a HOG után, súllyal `[0x00c7c838]` (@`0x00824284`; az értéke nincs kiolvasva), tehát index 1. A `0x0081fc30` ugyanezt teszi: @`0x00821174` HOG-konstruktor, @`0x0082119b` `fld1`, @`0x008211a4` `call 0x81fab0`; Neven-hívás nincs benne.
- **Út B (adat- és vtábla-lánc, a vezérlési folyamtól független).** A HOG-konstruktor @`0x0081968a` írja a `0x00cbdec4` vtáblát; a `rtti` tábla szerint slotjai: +0 `0x00819720`, +4 `0x00873510`, **+8 `0x00873e40`**. A Neven-konstruktor @`0x0081985f` a `0x00cbded4` vtáblát írja, slotjai `0x00819890`, `0x00874010`, `0x008742a0` (+8).
- Eredmény: a `+8` slot a HOG-osztályé, `0x00873e40`. A Neven-slot (`0x008742a0`) ebből a két építőből nem hívódik.
- A két élépítő (`0x00875ee0` @`0x00876aa9`, és `0x00874e40` @`0x00875653`) egyaránt a 0. elemet adja át: a `0x00874e40`-ben `mov ecx,[eax]; mov edx,[ecx]; push edx` (@`0x0087564d`-`0x00875652`), a `0x00875ee0`-ben `*(undefined4 *)*param_2`.

**Bizonyítottsági fok (1).** Az osztály és a slot: megerősített (A és B egyezik). A `0x00873e40` képlete: feltételes. Ebben a körben csak a törzs elejét olvastam (gyorsítótár a `[this+0x4c]` tömbön; a `0x00873cb0` index szerint épít HOG-vektort); a χ²-összeg záró részét nem olvastam újra. A G/3c `d_hog` a hivatkozás.

**Cáfoló kísérletek (1).** (a) „a Neven-tag adja az élköltséget”: cáfolva, mindkét építő a 0. elemet adja át, a `0x008742a0` nincs hívva. (b) „a HOG az 1. elem”: cáfolva, a `0x00824090` első hozzáadása a HOG (@`0x008241ea`). (c) „a súly bekerül az élköltségbe”: a két építő nem olvassa a súlytömböt. Teljes .text-seprés (újraszinkronizált, 2 886 751 utasítás): a `+0x504`…`+0x510` memóriaoperandusokat 177 utasításban találja, 44 függvényben (és öt, függvényen kívüli találatban), de ezek többsége más osztályé. Hogy melyik olvassa a Neven-súlyt, nem dől el: NINCS MEG.

##### G/14/2. A `0x0081ae10` bemenetei

- **Kimenet.** A `+0x6cc` (adatmutató) és a `+0x6d0` (elemszám·2 | jelző) csoportazonosító-tömb. A `+0x6d4` a párja: a `0x0081b800` a `param_4 == 0` ágban a `+0x6d4` (`param_1+0x1b5`) tömböt adja át, amelyet a `0x0081ae10` nem tölt.
- **Csoportszabály (megerősített: a törzs és a G/5 QEMU-mérés egyezik).** A `0x0081ae10` a `this+0x4f4` elemszámon (`>>1`) megy végig. A dátumot a `0x004edf60` iterátor adja, 64 bites, 100 ns-os egységben; a `+5 000 000` és a `/10 000 000` kerekítés másodpercre. Új csoport, ha a szomszédos különbség nagyobb vagy egyenlő a küszöbbel (`delta >= T`).
- **Küszöb (`T`).** A `0x0081ae10` `param_1` argumentuma a `0x0081b800` 4. stack-argumentuma: `cmp dword ptr [esp+0x50], 0` @`0x0081b8be`, `mov edx,[esp+0x50]` @`0x0081b8c5`, `push edx` @`0x0081b8c9`, `call 0x81ae10` @`0x0081b8ca`. A prológus `sub esp,0x30` és 4 `push`, így a 4. argumentum a `[esp+0x50]`. Az egyetlen hívó a `0x006175c0` (index). Ott @`0x00617801`-`0x00617810` a 4. argumentum a `mov edx,[esp+0x14]` értéke (`push edx` @`0x00617806`). `T = 0` esetén a `0x0081ae10` nem fut (`je` @`0x0081b8cf`).
- **A `s²·X` számítás helye.** A `0x006177de`-`0x006177f8` blokk (`fld [esp+0x18]` = s, `fild [ebp+0x48c]` = X, két `fmulp`, `call 0xc29990`) eredménye `eax`-ban marad, és a **2.** argumentumként (`push eax` @`0x00617808`) kerül át, nem a 4.-ként. A 4. argumentum [esp+0x14]-je a `0x006176b4` (`fstp`) és a `0x006176fe` (`mov [esp+0x14], eax`) környékén íródik; ennek számítása nyitott. A D szakasz `⌊s²·86400⌋` képletének összevetése a 4. argumentummal tehát még nem zárult le.
- **Dátum-mező.** A `0x004edf60` (753 bájt) olvassa. Hogy a mező EXIF-es felvételi idő (`DateTimeOriginal`) vagy fájlidő, nincs megnevezve. Nálunk: `src/picasapy/movie/slideshow.py:611` (`_capture_timestamp`: EXIF 36867, majd 306, majd fájl mtime).

**Bizonyítottsági fok (2).** A kimenet és a csoportszabály: megerősített. A küszöb-argumentum helye: megerősített (asm, a prológus-számítással). A küszöb értékének forrása (a 4. argumentum): NINCS MEG. A dátum-mező jelentése: NINCS MEG.

##### G/14/3. A kiválasztás szerződése, a Nálunk-eltérések, és a fejlesztői jegytörzs

**Eredeti (a bináris és a mérések szerint).**
1. Időcsoport: szomszédos, egész másodpercre kerekített idők, `delta >= T` új csoport (megerősített: QEMU, G/5).
2. Kiválasztó: horgony (`[obj+0x738]`, vagy a 0. elem), spirál +1, -1, +2, -2 …, legfeljebb 100 jelölt, a csoport kizárva (G/2c és G/3b-G/3d; asm: feltételes).
3. Pontszám: az élköltség, bizonyítottan a HOG-távolság (`0x00873e40`, G/14/1); szigorú minimum, döntetlennél a korábbi (feltételes).
4. **T = 0 (alapbeállítás): időrendben marad.** Mérés: a 2026-10-19-i export (6 kép, `ordering` = 0, `burstmodethresh` = 0); a kimenet a `DateTimeOriginal` szerinti sorrend. A kimenet megerősített; a mechanizmus (a `+0x6d4` tömb) nincs visszafejtve.

**Nálunk (a mai kód, `src/` greppel ellenőrizve).** `src/picasapy/movie/slideshow.py:803-812`: `capture_groups(capture_times, settings.burstmodethresh)`, majd `select_chain(...)`, a jellemző `np.mean(frame, axis=(0, 1))` (színátlag; a kódkomment szerint ez nem az eredeti HOG). A `burstmodethresh` alapértéke 0 (`slideshow.py:79`), a `ordering` alapértéke 0 (`slideshow.py:78`).
- **Eltérés 1 (hiba az alapbeállításban).** T = 0 esetén a `capture_groups` minden képet külön csoportba tesz, így a `select_chain` átrendezi a filmet. Reprodukció (a projekt saját kódja, csak olvasva): `capture_groups([1,2,3,4,5,6], 0)` → `[0,1,2,3,4,5]`; a `select_chain` egy szintetikus jellemzővel `[0,3,4,5,2,1]`-et ad. A natív export időrendet mutat.
- **Eltérés 2.** A jellemző színátlag, nem HOG-vektor.

**Teendő (Codex-kész, fejlesztői jegytörzs):**
1. `slideshow.py`: T = 0 esetén a `select_chain` ne fusson, a film időrendben maradjon. Teszt: T = 0 és hat kép esetén a sorrend megegyezik a bemenettel (az export mérését tükrözi).
2. `feature_for_index`: HOG-vektort kell adni a színátlag helyett. A leírás a G/11 szakaszban van (18 előjeles rekesz, s = 9/π, a szög `atan2(dy, dx)` a győztes csatornán, 8×8 cella, 19 float; `0x0088c480`, `0x0088cd10`). A `d_hog` (χ², 1e-8) már megvan, és egyezik a G/3c képlettel.
3. Neven-tag: nem kerül az élköltségbe; ehhez nincs fejlesztői teendő.

**Kész, ha (kiválasztási szabály).**
- ✅ Az élköltség provider-osztálya és `+8` slotja, bizonyítottsági fokkal, két úttal (G/14/1).
- ✅ A csoportszabály mint mért rész (G/5, QEMU), és a T = 0 kimenet mérése (export).
- ⛔ A kiválasztó spirál és minimum egy úton áll (asm). A HOG-vektor egyezése a natív kimenettel nincs mérve (a natív futtatás a 4. körben a gyűjteményobjektum rekonstrukciójánál elakadt).
- ✅ A fejlesztői teendő kimondva (Eredeti | Nálunk | Teendő), a #4182-höz kapcsolva.

**Nem része (nyitott mellékkérdések; a mai kód viselkedését tartjuk meg).** (i) A 4. argumentum (küszöb) forrása, a `[esp+0x14]` a `0x006176fe`-nél. (ii) A dátum-mező jelentése a `0x004edf60`-ban (EXIF vs fájlidő). (iii) A `this+0x6f8` jelzőbájt jelentése: a 26. kör szerint, ha be van állítva, az élköltség a `_DAT_00cf4968` szorosa (PE-olvasat, ~2^-63); ez a Neven-taghoz vagy az arcokhoz kötődhet. (iv) A horgony forrása (`[obj+0x738]` írója, `0x008223e0`). (v) A Neven-súly (`this+0x50c`) olvasója a gráfobjektumra nézve.

**Lezárás (#4194, 27. kör): (a).** A megvalósítható rész (élköltség = HOG, csoportszabály, T = 0 időrend) megvan. A nyitott mellékkérdések a „Nem része” pontban vannak, és nem zárják ki a fejlesztői listát. A fejlesztői lista az alapbeállítású T = 0 hibát is tartalmazza.

Ghidra-kör kell: 0x004edf60 - a dátum-mező: a rekord melyik mezőjét olvassa (EXIF `DateTimeOriginal` vagy fájlidő), és ki tölti a `[this+0x3f0]` táblát [nem blokkoló: a mai kód EXIF-et használ]

Ghidra-kör kell: 0x006176fe - a `0x006175c0` `[esp+0x14]` (a `0x0081b800` 4. argumentuma, a küszöb) számítása, és az `s²·X` eredmény (2. argumentum) szerepe [nem blokkoló: a fejlesztői lista a küszöböt a felhasználói értékből veszi]

### 2.5/d Az Arcfilm teljes útja: eredeti ↔ PicasaPy (#5657, 2026-10-23)

**Címhelyesbítés.** A jegyben megadott `0x00c9cf28` és `0x00c9cf68` nem
kód-belépési pontok, hanem az eredeti bináris karakterláncai:
`CMakeFaceMoviePanel::askapplyswitchconfirm`, illetve
`CMakeFaceMoviePanelRememberDialog`. A hívható segéd a **`0x0061dcf0`**;
a render-parancsot fogadó panelkezelő a **`0x0061df10`**. A következő
összevetés a menütől a kimenetig követi a bizonyítható részeket; a
`NINCS MEG` soroknál a megszerzés útját is megadja.

| Útlépés | Eredeti (bináris cím) | Nálunk (mai forrás) | Teendő |
|---|---|---|---|
| Menü és belépés | Két parancs: `ID_FACES` és `ID_FACESRANDOM`; a `0x0057cb60` diszpécser a `+0x4f0` / `+0x4f1` módjelzőt állítja (`0x0057cc69`, `0x0057cc7a`). A menü szövegei: `0x00c8d93c`, `0x00c8d908`. | `PicasaMenuBar.qml:2300-2324` ugyanezt a két tételt adja; `Main.qml:2247-2248` a kijelölt arcok, illetve az Emberek-albumok útjára kapcsol. | **EGYEZIK** a két menüpont és a két mód szintjén. |
| Emberek-albumok forráslistája | A `0x008226e0` az albumazonosítókat járja végig, az üres alsó képlistát kihagyja, és nem rendez át (`2.5`, `0x00822715`, `0x0082274f-0x00822775`, `0x008229f0-0x008229fb`). | `Main.qml:1031-1035`, `people_controller.py:144-155`, `index/people.py:210-256`: minden nem üres személyalbum képei, a személylista sorrendjében; a képeket az index `folder_path, name` szerint rendezi. | Az albumlista szűrése egyezik. Az eredeti alsó lista képsorrendjének és a mi mappanév szerinti sorrendünknek az azonossága **NINCS MEG**; ehhez ugyanazon képkészlet eredeti panel-kivonata és a két képlista soronkénti összevetése kell. |
| Kijelölt képek arcadata | A panel arc-módja megvan (`0x0057cb60`, `0x00616b42-0x00616b5f`), a timeline az átadott régióazonosítót használja (`0x00813c50`), de a `this+0x48` rekordlista és az azonosító eredete nem bizonyított (`2.5/c`, `0x00812470`). | `CreateDialogs.qml:41-47, 786-805`, `movie/slideshow.py:565-589, 752-778`: a kijelölt képek `.picasa.ini` `faces=` téglalapjai közül minden nem figyelmen kívül hagyott, használható arc külön képkockát ad. | Az adatút azonossága **NINCS MEG**. A már meglévő Ghidra-kérdés: `0x00812470`: mi tölti a timeline 0xf8 bájtos rekordjait, ki írja a `+0x8` régióazonosítót, és kötődik-e `faces=`-hez vagy több-arcos kiválasztáshoz; az elkészült `2026-10-17-idorend-film-sav.txt` csak a rekord mintavételezését/másolását mutatja. Ne kérjük ugyanazt újra. |
| Filmkészítő felület | A `0x00618050` építi a közös MakeMoviePanelt. Az Arcfilm harmadik fülének kulcsa `CMakeMoviePanel::face_movie_tab3_label` (`0x00c9c5f8`, xref `0x006173c0`); a stringres EN értéke „Options” (a `2.6` vezérlőleltár), a kliptálca külön vezérlői a 2.5/c-ben vannak. | `Main.qml:363-371, 474-481` dokumentumlapot nyit; `CreateDialogs.qml:1130-1148` a fülek `Movie`, `Slide`, `Clips`. Az opciók a `Movie` fülre, a hossz-/burst-szűrő és a kliptálca a `Clips` fülre került (`CreateDialogs.qml:1158-1414, 1669-1760`). | **ELTÉR** az opciók fülszintű csoportosítása. A viselkedési eltérést lásd a render-kapuban; az elrendezés termékdöntés, alább külön jegyvázlat. |
| Beállítások és igazolt alapértékek | Felbontáslista: hét érték `0x00c7db50`; Arcfilm-kulcs `facemakemovieres`, alapindex 3 (`0x00616b42-0x00616b5f`), amely 1024×768. A `showcaptions` és `cropfit` olvasó alapja 0 (`0x00616961-0x0061699a`); `showdates`, `removelowresfaces`, illetve a többi modelljelző nullázása `0x006169f0-0x00616a26`; az új film `ordering=0` és a „Best Transitions” kijelölése `0x00616a18`, `0x0061881a`; a burst-alap 0 (`0x00616a26`). A `facemakemovieres` teljes `.text`-beli hivatkozás-ellenőrzése csak olvasót talált; kontrollként a normál `makemovieres` írója is előkerült (`0x00619431-0x00619469`, 2.8/b). | `CreateDialogs.qml:480-505, 1278-1320, 1336-1414, 1690-1717`: ugyanaz a hét felbontás, Arcfilm alapindex 3, kapcsolók hamisak, Smart/Best Transitions kijelölve, burst-csúszka 0, hosszcsúszka 1, diaidőcsúszka 30 (= 3,0 s), átfedés 0,5 s; `create_controller.py:100-105, 222-242` ugyanilyen Arcfilm-felbontási alapot ad, és nem írja vissza a kiválasztott Arcfilm-felbontást. | **EGYEZIK** a bizonyított felbontás-, kapcsoló-, rendezés- és burst-alapértékekben. Az eredeti hosszcsúszka-induló `t`, diaidő és átfedés-induló érték **NINCS MEG**. Megszerzés: `0x00613b50` panelépítő és `0x0061adf0`/`0x0061ae80` frissítő célzott követése; a tényleges widget-induló értéket friss Picasa-profillal végzett pontos UI-méréssel kell igazolni. A mérőarchívum fájllistájában Arcfilm/film/MXF fixture nincs. |
| Újraszámolás megerősítése | `0x0061df10`: a `recompute` parancs alapból megnyitja az `askapplyconfirm` dialógust; a szöveg a szöveges diák törlésére figyelmeztet (`0x0061e078`, `0x00c9d0b8`), a „Do not ask again” csak az Igen ággal tárolódik (`0x0061e0f7-0x0061e12c`). | `CreateDialogs.qml:999-1021, 2288-2293` ugyanezt a kulcsot és kérdésszöveget használja; csak akkor kérdez, ha vannak szöveges diák. A `ConfirmDialog.qml:59-79` a bejelölést csak az Igen (`onAccepted`) ágon jegyzi meg. | **RÉSZBEN EGYEZIK**: a romboló eset megerősítést kap, és az „emlékezz” Igenhez kötött; nálunk üres szövegdia-listánál nincs kérdés. A feltétel eltérése igazolt; lásd a harmadik jegyvázlatot. |
| Render előtti `askapplyswitchconfirm`-kapu | A `0x0061df10` render-ágában a `0x006204ec` ellenőrzi a `+0x4f0/+0x4f1` jelzőket, majd `vt[0xb0]`-n hívja a `0x0061dcf0`-et (`0x00620502-0x0062050c`). A segéd alapból 0-ra inicializálja a `Preferences\CMakeFaceMoviePanel::askapplyswitchconfirm` kulcsot, és a kapu feltételeinek teljesülésekor Opciók-üzenetet jelenít meg (`0x0061dd5a-0x0061de9d`; erőforráscímek `0x00c9cf28`, `0x00c9cf68`, szöveg `0x00c9cfd0`). A caller eredményága: 0 → `recompute`; 2 → megszakítás; egyéb → render/export folytatása (`0x00620510-0x006205a5`). A dialógus Cancel/No/Yes gombjainak konkrét eredménykód-leképezése **NINCS MEG**. A pipa bármely dialógusválasz után beállítja a kulcsot 1-re, ha be volt jelölve (`0x0061dea9-0x0061dedf`); a későbbi elnyomott kapu 1-et ad, tehát folytatja a renderelést, nem alkalmaz. A jelzők „függő beállítás” jelentése a 2.5/c végén feltételes: a dialógus szövege ezt mondja, de a `+0x4f0` a panelépítés egy másik ágában is állhat. | A `CreateDialogs.qml:1059-1087` a létrehozáskor a pillanatnyi vezérlőértékeket adja át az `exportMovie`-nak; `create_controller.py:690-739, 912-983` ezekből közvetlenül épít `MovieSettings`-et. A `src/picasapy` alatt nincs `askapplyswitchconfirm` vagy függő/alap-állapotot tároló megfelelő. A meglévő `askapplyconfirm` kizárólag a szöveges diák miatti újraszámolást védi. | **ELTÉR: igazolt termékteendő-jelölt.** PicasaPy-ban a változtatás azonnal érvényesül filmkészítéskor; az eredeti render-ág kódjai szerint a 0 újraszámol és nem exportál, a 2 megszakít, más eredmény exportál. A kódok és a Cancel/No/Yes címkék leképezése még nyitott. Lásd az első jegyvázlatot. |
| Fájl-kimenet | A panel a Picasa/Movies (honosítva) mappába, alapértelmezett névvel és `.wmv` kiterjesztéssel ment; ha kell, a My Videos tartalékot használja (`0x0061cf20`, `0x00620af9-0x00620b1d`, `0x00620ab1`, `.wmv`: `0x00620b84`). | `app/movie_output.py` ugyanazt a mappát, nevet, ütközés-sorszámozást és tartalékot követi; a film `.mp4`, mellette `.mxf` projekt készül (`create_controller.py:954-1016`). | Mappa/név/automatikus út **EGYEZIK**. A `.wmv`→`.mp4` eltérés igazolt, de a kódban kimondottan szándékos (#1977: a Windows Media SDK csak Windowson érhető el); a kutatás nem javasol „visszajavítást” és nem nyit duplikált fejlesztési jegyet. |

**Bizonyítottsági fok.** A render előtti kapu eltérése **megerősített**: az A út az eredeti két függvény utasításszintű vezérlésfolyama és visszatérési ágai; a B út a PicasaPy QML→controller→`MovieSettings` adatfolyama, valamint a helyi forrásszöveg teljes `rg` keresése. A felbontáslista/alapértékek is **megerősítettek** (bináris értékek + független mai QML/controller értékek). A menu-szintű Emberek-album-szűrés **megerősített**; a képen belüli rekord-sorrend és arcazonosító adatút **nyitott**. A fülszervezés és a kimeneti formátum eltérése a két forrásréteg közvetlen összeolvasásával igazolt.

**A két független út.**

- **A: eredeti bináris:** célzott diszasszemblálás: a `0x0061df10` `render` ága `0x006204ec`-től meghívja a vtable `+0xb0` slotot; a `0x0061dcf0` mutatja meg a `askapplyswitchconfirm` beolvasását, a párbeszédet, a pipa-írást és a visszatérést. A hívó `0`/`2`/egyéb ágain külön ellenőriztem a recompute/cancel/export eredményt.
- **B: független visszakötés és mai megvalósítás:** az önálló bináris-ellenőrzés az eredeti EXE SHA-256-át egyezőnek találta az indexelt 3.9.141.259 fájllal, majd a MakeMoviePanel vtable `+0xb0` slotját kötötte vissza a `0x0061dcf0` helperhez; ez külön út a `0x0061df10` közvetlen diszasszemblálásától. A mai QML `Create Movie` gombja `startMovieExport`-ot hív, az aktuális mezők a controllerben közvetlenül `MovieSettings`-sé válnak. A külön `recomputeMovie` út csak a szöveges diák védelmi kérdése; a teljes runtime Python/QML kódban az eredeti beállításkulcs nincs. A két bináris út egyezik a kapu meglétében, a mai forrásút pedig igazolja, hogy ilyen render előtti kapu nálunk nincs.

**Cáfoló kísérlet (15.2).** Azt próbáltam megcáfolni, hogy a PicasaPy futásidejű kódjából hiányzik a kapu: a pontos `askapplyswitchconfirm` kulcsot az `app/` Python/QML-részben kerestem, az `i18n/` TS erőforrásfájlokat külön kezelve, majd végigkövettem a Create Movie → `startMovieExport` → controller útvonalat. A preference-kulcs és a Remember-dialog futásidejű használata nem található; a dialog neve viszont fordítási metaadatként szerepel az i18n-fájlokban, ami önmagában nem bizonyít bekötött párbeszédet. A létrehozási út kapu vagy alkalmazott/piszkozat-állapot-ellenőrzés nélkül a jelenlegi vezérlőértékeket exportálja. Ellenpróbaként a meglévő `askapplyconfirm` megtalálható, de csak a `recomputeMovie` hívja, szöveges diák esetén. Ez a kódhely nem cáfolja a render előtti kapu hiányát; a közvetlen adatút és a bináris render-ág összevetése mellett a következtetés **megerősített**.

**Javasolt jegytörzs-bővítés.**

1. **Az Arcfilm render előtti alkalmazási kapujának pótlása**

   **Javasolt cím:** Arcfilm: kezelje a render előtt a nem alkalmazott Opciókat.

   **Eredeti:** `CMakeFaceMoviePanel::askapplyswitchconfirm`,
   `0x0061dcf0`; alapbeállítás 0. A párbeszéd Cancel/No/Yes gombokat mutat;
   a render hívója 0 eredménynél újraszámol és nem exportál, 2-nél megszakít,
   más eredménynél folytatja a render/export ágat. A gombcímkék és az
   eredménykódok megfeleltetése **NINCS MEG**.

   **Nálunk:** a Create Movie út a pillanatnyi értékeket közvetlenül
   exportálja; nincs Arcfilm függő/alkalmazott állapot és nincs külön
   `askapplyswitchconfirm`.

   **Teendő:** ha termékdöntés az eredeti viselkedés követése, válaszd szét
   az Opciók szerkesztett és utoljára alkalmazott állapotát, és a Create
   Movie előtt implementáld a három döntési ágat és a külön megjegyzett
   `askapplyswitchconfirm` kulcsot. A Cancel/No/Yes eredménykód-leképezését
   implementáció előtt a `0x009bab50` párbeszéd-eredményútján vagy pontos
   UI-méréssel kell igazolni; ne rendelj hozzá becsült kódot. Az eredeti
   pipa-viselkedést ne keverd a `recomputeMovie` `askapplyconfirm` kulcsával.

   **Kész, ha:**
   - az eredeti gombcímke-kód leképezés binárisan vagy pontos UI-méréssel
     igazolt, és a 0/2/egyéb ág a megfelelő felhasználói választ követi;
   - újraszámolásra váltáskor az aktuális kattintás nem készít filmet;
   - a folytatás az utoljára alkalmazott Opciókat használja;
   - megszakításkor nem ír kimenetet;
   - a pipa beállítja a `askapplyswitchconfirm` értékét bármelyik válasz
     mellett, az elnyomott későbbi kapu pedig az eredeti szerint folytatja
     a renderelést;
   - nem függő Opcióknál a render kérdés nélkül indul, a `recompute`
     `askapplyconfirm` útja pedig külön marad.

2. **Az Opciók fül összevetése a Movie Maker lapjával**

   **Javasolt cím:** Filmkészítő: adjon külön Opciók fület az Arcfilmhez.

   **Eredeti:** a beállítások az `Options` fülön, a klipek kezelése a
   külön kliptálcán van (`0x00618050`, 2.5/c).

   **Nálunk:** a beállítások a `Movie` fülön, a hossz-, burst- és kliptálca
   vezérlők a `Clips` fülön vannak.

   **Teendő:** termékdöntés után vagy állítsd vissza a külön `Options`
   fület, vagy jelöld a mostani fülszervezést elfogadott felületi eltérésnek.

   **Kész, ha:** a döntés dokumentált; visszaállítás esetén az összes eredeti
   Opció-vezérlő egy külön `Options` fülön jelenik meg, az értékek/defaultok
   változatlanok, és a filmcsík/előnézet/készítés tovább működik.

3. **Az újraszámolási kérdés feltételének rögzítése**

   **Javasolt cím:** Filmkészítő: rögzítse az üres szövegdia-lista újraszámolási viselkedését.

   **Eredeti:** az `askapplyconfirm` alapból minden `recompute` parancs előtt
   kérdez (`0x0061df10`, `0x0061dfa9-0x0061e0f7`), ha a kulcs nincs
   elnyomva.

   **Nálunk:** csak akkor kérdez, ha van szöveges dia; egyébként rögtön
   újraszámol (`CreateDialogs.qml:999-1008`).

   **Teendő:** dokumentáld a feltételes megerősítést elfogadott eltérésként,
   vagy termékdöntés után állítsd vissza az eredeti, minden kézi `recompute`
   előtti kérdést.

   **Kész, ha:** a viselkedésről szóló termékdöntés rögzítve van; visszaállítás
   esetén a kérdés diák nélkül is megjelenik, a „ne kérdezze meg újra” csak
   Igen után tárolódik, és a szöveges diák törlése kizárólag Igenre történik.

**Nyitott.**

- Ghidra-kör kell: 0x009bab50: a 0x009ba4d0-vel felépített Cancel/No/Yes párbeszéd melyik gombhoz milyen eredménykódot ad; a meglévő 0x0061df10-dekompilátum csak a 0/2/egyéb hívóágakat mutatja [blokkoló].
- Az eredeti képlista sorrendje az Emberek-albumon belül: NINCS MEG; a
  `0x008226e0` megőrzi a kapott sorrendet, de az alsó vtable-lista rendezése
  nincs megnevezve. Picasa futásból származó forrás-/kimeneti listával kell
  összevetni a mai `ORDER BY folder_path, name` sorrendet.
- Az eredeti Arcfilm téglalap-azonosító és a `faces=` forrás kapcsolata:
  meglévő, még meg nem válaszolt kérdés a `0x00812470`-hez (lásd 2.5/c és
  `referencia/ghidra/2026-10-17-idorend-film-sav.txt`); az ismert kimenet a
  timeline-rekord mintavételezését mutatja, az upstream rekordírót nem.
- A hosszcsúszka alapállása, diaidő, átmenet- és átfedés-alapérték az
  eredeti Arcfilmben: NINCS MEG; a megszerzési út a táblázatban. Ezek nélkül
  ezen értékek egyezéséről vagy eltéréséről nem állítok semmit.

### 2.6 A MakeMoviePanel (a „Film készítése” felület) teljes beállítás-leltára

*A 2.2 szakasz a csúszkákat és beállításokat a felirat-szintig írta le. Ez
a szakasz a lefordított VALUES-t és a TÁROLÁSI kulcsokat adja — az olcsó
láncból (`0x00613b50` + `0x00616940` diszasszemblálásából).*

#### A kimeneti méretlista — 7 méret (`CMakeMoviePanel::size0..size6`)

A `makemoviepanel/moviesize` listbox építője a `0x00613b50`-ben, a rendezett
sorrend:

| index | érték | honosítási kulcs |
|---|---|---|
| 0 | `320x240` | `CMakeMoviePanel::size0` |
| 1 | `640x480` | `CMakeMoviePanel::size1` |
| 2 | `800x600` | `CMakeMoviePanel::size2` |
| 3 | `1024x768` | `CMakeMoviePanel::size3` |
| 4 | `1600x1200` | `CMakeMoviePanel::size4` |
| 5 | `1280x720 (720p)` | `CMakeMoviePanel::size5` |
| 6 | `1920x1080 (1080p)` | `CMakeMoviePanel::size6` |

*(A `size5`/`size6` felirata magában hordozza a minőségi jelölőt — a
honosított szöveget `XxY` alakban kell kezelni, nem kulcsként.)*

**Bizonyíték:** a `0x00613b50`-ben a `0x9ae560` (érték feloldó) hívásait
követő literálok: `0xc9bf04`=`320x240`, `0xc9bf24`=`640x480`,
`0xc9bf44`=`800x600`, `0xc9bf64`=`1024x768`, `0xc9bf88`=`1600x1200`,
`0xc9bfac`=`1280x720 (720p)`, `0xc9bfd4`=`1920x1080 (1080p)`.

#### A hangsáv-opciók — 3 állás (`CMakeMoviePanel::audiooption0..2`)

| index | felirat | kulcs |
|---|---|---|
| 0 | Truncate audio | `CMakeMoviePanel::audiooption0` |
| 1 | Fit photos into audio | `CMakeMoviePanel::audiooption1` |
| 2 | Loop photos to match audio | `CMakeMoviePanel::audiooption2` |

**Bizonyíték:** `0xc9c018` / `0xc9c048` / `0xc9c080` a `0x00613b50`-ben.

#### A film-beállítások TÁROlása — `Preferences` kulcsok (`0x00616940`)

A `0x00616940` (1021 b) a MakeMoviePanel beállítás-beolvasója, amely a
létező kulcsokból tölti a film-modell szerkezetét:

| kulcs | jelentés | beolvasó |
|---|---|---|
| `Preferences\CMakeMoviePanel::showcaptions` | a `makemoviepanel/show_captions` kapcsoló állása | `0x00616961` |
| `Preferences\CMakeMoviePanel::cropfit` | a „Full frame photo crop" kapcsoló | `0x00616981` |
| `makemoviepanel/remove_low_res_faces` | a „Remove Low Resolution Faces" | a `0x00618050`-ből |
| `Preferences\movievolume` | a hangerő (ld. 2.7) | a `0x00618050`-ből |
| `Preferences\makemovie1to1` | az „1:1 / valódi méret" kapcsoló (ld. 2.7) | a `0x00618050`-ből |

A beolvasott kapcsolók a `[+0x4bc]` (a film-modell) `+0x2c4`–`+0x2c8`
bájtjaira kerülnek (`0x006169cf`–`0x00616a08`); a `+0x2cc`/`+0x2d0` a
méretlistáé, a `+0x2d8` a modell-mutató. A MakeMoviePanel **három rádiója**
(`smart_order_radio` / `album_order_radio` / `chronological_order_radio`)
a `0x00618050`-ben épül; a diasorrend az `.mxf` `<ordering>%d</ordering>`
mezőjébe kerül (2.4/b), nem Preferences-be.

#### A szakasz által lefedett vezérlők — TELJES ELEMNÉVVEL (2026-09-02)

A fenti leltár a vezérlőket a **feliratukkal** azonosította. A
lefedettségi mérő viszont a **teljes elemnévre** keres, ezért ezek
„feltáratlan"-ként számítottak, pedig itt le vannak írva. A tábla ezt
pótolja — a bizonyíték a szakasz fenti címei (`0x00613b50`,
`0x00616940`, `0x00618050`):

| elem | mit azonosít | hol áll a bizonyíték |
|---|---|---|
| `makemoviepanel/moviesize_label` | a kimeneti méretlista felirata („Méretek") | a 7 méret táblája |
| `makemoviepanel/sizelist` | maga a méret-lista | ugyanott (`0x00613b50`) |
| `makemoviepanel/audio_label` | „Hangsáv:" — a hangsáv-blokk felirata | a 3 hangsáv-opció |
| `makemoviepanel/aoptions_label` | „Opciók" — a hangsáv-opciók felirata | ugyanott |
| `makemoviepanel/ordering_header_label` | „Diák rendezése:" | a három rádió bekezdése |
| `makemoviepanel/smart_order_radio` | „A legjobb átmenetek" rádiógomb | `0x00618050` |
| `makemoviepanel/smart_order_label` | ugyanannak a felirata | `0x00618050` |
| `makemoviepanel/album_order_radio` | „Album szerint" rádiógomb | `0x00618050` |
| `makemoviepanel/album_order_label` | ugyanannak a felirata | `0x00618050` |
| `makemoviepanel/chronological_order_radio` | „Időrend" rádiógomb | `0x00618050` |
| `makemoviepanel/chronological_order_label` | ugyanannak a felirata | `0x00618050` |
| `makemoviepanel/remove_low_res_faces_label` | „Kis felbontású arcok eltávolítása" | `0x00618050` |
| `makemoviepanel/crop_to_fit_label` | „Teljes képkockás fotó körbevágása" (`cropfit`) | `0x00616981` |

⚠️ **Amit ez a szakasz NEM fed le**, tehát valóban feltáratlan marad:
`add_audio` („Betöltés…") és `remove_audio` („Törlés") — a hangsáv
BETÖLTÉSE és törlése; a leltár csak a betöltött sáv **kezelési
opcióit** adja meg, a fájlválasztás útját nem.

### 2.6/b A HANGSÁV betöltése és törlése — MŰKÖDÉS (2026-09-02)

*A 2.6 a hangsáv három **kezelési opcióját** adta (Truncate / Fit / Loop).
Ez a szakasz azt írja le, **hogyan kerül oda a hangsáv**, és mi történik
törléskor — a két gomb az előző kör „valóban feltáratlan" listájáról.*

| elem | felirat | **hivatalos magyar** | az ág címe |
|---|---|---|---|
| `makemoviepanel/add_audio` | Load… | **„Betöltés…"** | `0x0061e48c` |
| `makemoviepanel/remove_audio` | Clear | **„Törlés"** | `0x0061ea4e` |

*(Mindkettő a `0x0061df10` panelkezelőn belül, névösszehasonlítással
kiválasztott ág.)*

#### Mit nyit meg a „Betöltés…" — fájlválasztó, PLATFORMFÜGGŐ szűrővel

A `0x0061e48c`-nél kezdődő ág (a `0x0061df10` panelkezelőben) a
szövegtárból veszi a szűrő leírását, és utána a nyers mintát:

| | angol | **magyar** | cím |
|---|---|---|---|
| leírás (Windows) | `Music Files (*.mp3,*.wma)` | **„Zenei fájlok (*.mp3, *.wma)"** | `MakeMoviePanel::AudioTypesWin`, `0x00c9d40c` |
| leírás (Mac) | `Music Files (*.mp3,*.m4a)` | **„Zenei fájlok (*.mp3, *.m4a)"** | `MakeMoviePanel::AudioTypesMac` |
| minta | `*.mp3;*.wma` | — | `0x00c9d42c` (11 bájt, `0x0061e57d`) |

⇒ **A Picasa csak KÉT hangformátumot fogad el**, és a kettőből az egyik
platformfüggő: Windowson `wma`, Macen `m4a`. *(Linuxon a `wma` a
kézenfekvő megfelelő nélkül marad — ez megvalósítási döntés lesz, nem
mérés.)*

#### ⭐ MINDKÉT gomb ELŐBB SZÜNETELTETI a lejátszást

Ugyanaz a három lépés a `add_audio` (`0x0061e4e3`) és a `remove_audio`
(`0x0061ea9f`) ágában:

```
mov eax, [panel+0x4a0]                     ; a lejátszó objektum
cmp byte ptr [eax+0x7c], 0 / je …          ; JÁTSZIK ÉPPEN?
mov byte ptr [panel+0x499], 1              ; jelző: „le kellett állítani"
mov edx, 0xc9bea4                          ; "video_control_bar2/moviecontrols/pause"
call 0x9cd8a0                              ; a PAUSE névparancs elküldése
```

⇒ **A hangsáv cseréje vagy törlése nem futó lejátszás közben történik**: a
panel előbb megnyomja a saját szüneteltető gombját, és megjegyzi, hogy
tette. *(A `[panel+0x499]` a törlés-ágban előbb **nullázódik**
(`0x0061ea99`), és csak akkor lesz 1, ha tényleg futott a lejátszás.)*

A törlés végén `0x00619910(panel)` — a panel újraépítése.

#### Hova kerül a betöltött fájl

Az `.mxf` projektfájl **`<musicfile>`** elemébe (2.4/b), az
**`<audiooption>`** mellé, ami a három kezelési mód indexe (2.6). Vagyis
a hangsáv a **projekt** része, nem globális beállítás.

#### ⭐ REJTETT ÁG: CTRL + „Betöltés…"

A `0x0061e76a`-nál:

```
push 0x11                       ; VK_CONTROL
call dword ptr [0xc406f8]       ; = GetAsyncKeyState  (IAT[0xc406f8] = 0x922efc)
shr eax, 0xf / and al, 1 / je   ; a magas bit: NYOMVA VAN-E
…
push 0xc9d438                   ; "AudioWebSupport"
push 0xc7eafc                   ; "Preferences"
```

⇒ **CTRL-t nyomva tartva a „Betöltés…" más ágra megy**, és beolvassa a
`Preferences\AudioWebSupport` kulcsot. Ha az értéke **nem üres**
(`0x0061e7fb`–`0x0061e807`), a panel a `[panel+0x4b4]` objektum
**`vt[0x10]`** rekeszét hívja (`0x0061e809`–`0x0061e82f`) — a rendes ág
ehelyett a `0x0061e86d`-nél folytatódik, más rekesszel.

⚠️ **Hogy ez az ág MIT csinál, NINCS mérve.** A kulcsnév webes
hangforrásra utal, de ez következtetés, nem mérés; a `vt[0x10]` mögötti
osztály nincs azonosítva. **Megszerzés:** a `[panel+0x4b4]` típusának
meghatározása (RTTI) és a `0x0061cc90` (a hívott segéd) dekompilálása.

*(Ugyanaz az idióma, mint a 33. tétel `FILM_GRAIN` ágában:
`GetAsyncKeyState(0x10)` = SHIFT. A Picasa több helyen rejt
módosítóbillentyűs ágat.)*

**Bizonyítottsági fok: megerősített** a szűrőre, a két platformváltozatra,
a szüneteltetésre és a CTRL-kapura (utasításszinten olvasva); a rejtett ág
**tartalma nincs mérve**.

### 2.6/c A „Mozgófilm létrehozása" gomb — MI KÉSZÜL, HOVA, MILYEN NÉVEN (2026-09-02)

*A 2.6 a panel beállításait sorolja, a 2.6/b a hangsávot. Ez a szakasz azt
írja le, mi történik a **lemezen**, amikor a felhasználó megnyomja a
`makemoviepanel/render` gombot („Mozgófilm létrehozása").*

Minden cím a `Picasa3.exe` 3.9-es változatáé, image base `0x00400000`.
A vezérlő-parancsokat ugyanaz a kezelő fogadja, mint a hangsávét:
**`0x0061df10`**.

#### A három parancs egy ágon — `render`, `export_youtube`, `cancel`

| parancs | elem | felirat | magyar | összehasonlítás |
|---|---|---|---|---|
| `render` | `makemoviepanel/render` | Create Movie | Mozgófilm létrehozása | `0x0061e17f` |
| `cancel` | `makemoviepanel/cancel` | Cancel | Mégse | `0x0061e1e0` |
| `export_youtube` | `makemoviepanel/export_youtube` | — (YT) | — | `0x0061e241` |

Mindhárom **ugyanoda ugrik**: `0x00620421`. Ott dől el, melyik az
(`0x006204bf`): a `cancel` a `0x00620ed3` bezáró ágra megy, a másik kettő
a **kimenet-készítő** ágra.

**Előkapu (`0x006204c7`):** a `[panel+0x4a0]` lejátszó `vt[0x38]` rekesze
igazat kell adjon; ha nem, a gomb **némán nem csinál semmit**.

#### 1. A YouTube-ág csak egy ELŐLÉPÉS

`export_youtube` esetén a rendes menet ELŐTT lefut `0x00624cf0` → ez hívja
a `youtube` sztringet ismerő `0x00827020`-at. Ha `0xf4242`-vel tér vissza
(a felhasználó megszakította), az **egész művelet elmarad**
(`0x006205bc`). Egyébként a menet ugyanaz, mint a `render`-nél, és a
kapott objektum a feladat `+0x74` mezőjébe kerül (`0x00620ce5`).

⇒ **A YT-gomb nem külön kimenet: előbb ugyanaz a `.wmv` készül el, és azt
tölti fel.**

#### 2. „Lecseréli a meglévőt, vagy újat hoz létre?" — mikor jön elő

A panel a `[panel+0x4d4]` mezőben megjegyzi a **korábban elkészített film
teljes útvonalát**. A menet ebből három állapotot vezet le:

| állapot | feltétel | mód |
|---|---|---|
| **nincs korábbi** | `[panel+0x4d4]` üres, vagy `autoplay` | 1 (új) |
| **helyreállított automatikus mentés** | a név része a honosított `autosave` | 2 (csere) |
| **volt korábbi** | minden más | a **párbeszéd** dönti el |

A párbeszéd (`0x00620718`–`0x0062082c`) három gombja:

| kulcs | angol | **magyar** |
|---|---|---|
| `CCollageUI::ConfirmTitle` | Replace Existing or Create New? | **Lecseréli a meglévőt, vagy újat hoz létre?** |
| `CMakeMoviePanelConfirmDialog` | You have been editing a previously created slideshow.… | **Eddig egy korábban készült diavetítést szerkesztett.…** |
| `CCollageUI::ButtonCreateNew` | Create New | **Új létrehozása** |
| `CCollageUI::ButtonReplace` | Replace Existing | **Meglévő cseréje** |
| `il_CancelButton` | Cancel | **Mégse** |

A **Mégse** (`0x00620804`: a visszatérés 2) az egész műveletet elhagyja —
a szerkesztés mentés nélkül folytatódik, ahogy a szöveg ígéri.

#### 3. A célmappa — `<Képek>\Picasa\<honosított „Movies">`

A mappát a **`0x0061cf20`** adja (`CMakeMoviePanel::SlideshowFolder`):

1. `0x009966a0` → a **`My Pictures`** gyökér;
2. hozzáfűzve a `Picasa` (`0x00c7f0fc`) közbülső szint;
3. hozzáfűzve a **honosított** mappanév — kulcs
   `CMakeMoviePanel::SlideshowFolder`, angolul `Movies`, magyarul
   **`Mozgófilmek`** (`0x00c9ce34` / `0x00c9ce3c`);
4. `0x00992ed0` (`Exists`) ellenőrzi; ha nincs, `0x009a3db0` létrehozza,
   és sikertelenségnél a függvény **`0xf4240`**-nel tér vissza.

**ÉLŐ BIZONYÍTÉK a tulajdonos gyűjteményéből** (`ini-korpusz`): a
`/mnt/photo/Picasa/` alatt **egyszerre** áll `Movies`, `Filmek` **és**
`Mozgófilmek` — a nyelvváltás új mappát nyit, a régit nem költözteti. Ezt
a mi oldalunkon a `project_folder_names.letezo_vagy_honos_mappa` már
kezeli (#1131).

**Tartalék: a `My Videos` mappa.** Ha a fenti mappa üres útvonal marad
vagy **nem létezik**, a menet a `0x009968a0` adta **`My Videos`** mappára
vált (`0x00620af9`–`0x00620b1d`). Ez nem elméleti ág: a `0x0061cf20`
hibája után ide esik a film.

**A célmappa `.picasa.ini`-t is kap.** A `0x0061cf20` a végén
`0x00445a30`-at hívja (`0x0061d005`), és az a függvény ismeri mindhárom
sztringet: `.picasa.ini`, `P2category`, **`Projects (internal)`**.
A korpusz megerősíti: mind a négy projekt-mappa `.picasa.ini`-je
`[Picasa] P2category=Projects (internal)`. (Az „Exportált videoklipek"
kivétel: ott `P2category=tech`.)

#### 4. A fájlnév — négy lépés, ebben a sorrendben

| # | lépés | cím | mit tesz |
|---:|---|---|---|
| 1 | alapnév | `0x00620998` | a `[panel+0x4d4]` útvonal **név-része** |
| 2 | üres → alapértelmezés | `0x00620ab1` | `CMakeMoviePanel::deffilename` = `slideshowmovie` / **`diavetites_jellegu_film`** |
| 3 | automatikus mentésből | `0x00620b2d` | `CMakeMoviePanel::recoveredautosave` = `Recovered Autosave` / **`Helyreállított automatikus másolat`** — **felülírja** az 1–2. lépést |
| 4 | tiltott karakterek | `0x00620b61` → `0x009946f0` | a `\ / : * ? " < > \|` készlet kiszűrése |

Ezután: `0x009a37b0` fűzi a mappához, `0x009a3620` teszi rá a
**`.wmv`** kiterjesztést (`0x00c81a44`, a `0x00620b84`-nél).

**Végül két, egymást kizáró lépés:**

- **csere mód (2):** `0x00991f00(útvonal, 5)` — a `0x00d694c0` globális
  függvénymutatót hívja az útvonalra; ha az nem sikerül és a
  `GetLastError` **5** (`ERROR_ACCESS_DENIED`), **5 másodpercig újrapróbál**
  (`QueryPerformanceCounter` + `WaitForSingleObject`). ✅ **A mutató
  2026-09-03 óta MEGVAN: a fájltörlés platformfüggő mutatója** (NT-n
  UTF-8 → UTF-16 átalakítás + `DeleteFileW`, 9x-en `DeleteFileA`) — a
  levezetés lent.
- **mindkét mód:** `0x00993030(útvonal)` — az **egyediesítő**: `0x00992ed0`
  (`Exists`) és a `%s%lu` formátum, azaz létező névnél **sorszám** kerül a
  végére. Csere módban a fenti lépés után a név már szabad, tehát
  változatlan marad.

#### 5. Maga a kódolás — `wmvcore.dll`, futásidőben betöltve

A tényleges filmkészítést a `0x0061d820` indítja (`0x00620d8d`). A
láncban a `0x00555e40` a `0x00549240`-et hívja, és **az** tölti be a
`wmvcore.dll`-t, belőle a **`WMCreateProfileManager`** és
**`WMCreateWriter`** belépési pontot.

⇒ A kimenet **Windows Media (WMV)**, a Windows Media Format SDK írójával.
A DLL **nincs az importtáblában** — `LoadLibrary`-vel jön, tehát a
Picasa maga is számol a hiányával.

⚠️ **Linuxra ez nem másolható.** A `.wmv` + WMF SDK párost nálunk mással
kell kiváltani; ez **megvalósítási döntés lesz, nem mérés**.

#### 6. Amíg készül: PISZKOZAT

A `0x0061d820` hívja a `0x0061d350`-et, ami a `projectutils::draft`
kulcsot ismeri: angolul `DRAFT`, magyarul **`PISZKOZAT`** (a
`projectutils::draft_format` szerint `PISZKOZAT -- %s`). A hozzá tartozó
üzenet a `projectutils::draft_slideshow`:

> „Ez a diavetítés még nem készült el teljesen. A diavetítés jellegű film
> elkészítéséhez kattintson a »Létrehozás« gombra."

#### 7. Hibaeset — és egy néma ág

Ha a `0x0061d820` **nem nullát** ad vissza (`0x00620d94`), a menet hibát
jelez… **de csak feltételesen** (`0x00620db2`–`0x00620dfe`): előbb
beolvassa a `Preferences\SupportMovies` kulcsot, és ha az **be van
állítva**, a hibaüzenet **elmarad**, a menet a siker-ágra megy tovább.

Az üzenet egyébként (`0x00620e00`):

| kulcs | angol | **magyar** |
|---|---|---|
| `MakeMoviePanelNoMovie` | Error creating movie file (error %d) | **Hiba történt a mozgófilmfájl létrehozása során (hibakód: %d)** |

A `%d` a `0x0061d820` visszatérési értéke.

#### 8. Siker után

`0x00620e68`-tól: a `[panel+0x4bc]` projektobjektum a feladatra száll át,
a `[panel+0x4bc]` **kinullázódik** (`0x00620eaf`), a `0x00631cb0` fut le,
majd a panel visszavált a **`panelroot/picasatab`** névparancssal
(`0x00620f77`, `0x00c801c8`) — vagyis a felhasználó a **könyvtárban**
találja magát.

#### Bizonyítottsági fok

**Megerősített** (utasításszinten olvasva): a három parancs közös ága és a
`cancel` szétválása, az előkapu, a párbeszéd három gombja és a magyar
szövegei, a mappalánc három szintje, a `My Videos` tartalék, a négylépéses
névképzés, a `.wmv` kiterjesztés, az egyediesítő, a `wmvcore.dll` két
belépési pontja, a `SupportMovies`-tól függő néma hibaág, a záró
névparancs.

**Erős** (a hívási környezetből következik, de az API neve nincs kiolvasva):
a csere módban futó `0x00991f00` **törlés**-szemantikája.

**Élő mintával megerősítve:** a `Picasa/Movies` · `Filmek` · `Mozgófilmek`
együttállása és a `P2category=Projects (internal)` — a tulajdonos
NAS-korpuszából.

#### ✅ MEGVÁLASZOLVA — a `0x00d694c0` a FÁJLTÖRLÉS platformfüggő mutatója (2026-09-03)

> **Bizonyítottság: megerősített** — minden lépés cím szerint, az
> import-nevek a PE **import-táblájából** feloldva.

A mutatót az induláskor futó `0x00c32bda` blokk tölti fel, **a Windows-verzió
szerint elágazva**:

```asm
0x00c32bda  call dword ptr [0xc40450]              ; GetVersion()
0x00c32be0  mov  dword ptr [0xd6fc58], eax
0x00c32bde  cmp  dword ptr [0xd6fc58], 0x80000000  ; a magas bit = Windows 9x/ME
0x00c32be8  jae  0xc32bf5
0x00c32bea  mov  dword ptr [0xd694c0], 0x009aecc0  ; NT-ág: SAJÁT burkoló
0x00c32bf4  ret
0x00c32bf5  mov  eax, dword ptr [0xc40528]         ; 9x-ág: KERNEL32!DeleteFileA
0x00c32bfa  mov  dword ptr [0xd694c0], eax
```

| IAT-rekesz | feloldva (import-tábla) |
|---|---|
| `0xc40450` | `KERNEL32.dll!GetVersion` |
| `0xc40528` | **`KERNEL32.dll!DeleteFileA`** |
| `0xc402e4` | `KERNEL32.dll!MultiByteToWideChar` |
| `0xc403c4` | **`KERNEL32.dll!DeleteFileW`** |

**A `0x009aecc0` burkoló (143 bájt) — mit csinál:**

1. `MultiByteToWideChar(0xFDE9, 0, útvonal, -1, NULL, 0)` — a **`0xFDE9`
   = 65001 = `CP_UTF8`** (`0x009aece9`); a hossz **`0xFFFF`-re vágva**
   (`0x009aecf0`–`0x009aecf7`);
2. verem-foglalás `2 × hossz` bájtra (`0x009aed13` → `0xbf5d60`);
3. második `MultiByteToWideChar` a tényleges átalakításhoz (`0x009aed29`);
4. **`DeleteFileW(széles útvonal)`** (`0x009aed2f` → `0xc403c4`).

⇒ **`0x00d694c0` = „töröld ezt a fájlt", platformhelyesen.** Windows NT-n a
Picasa **UTF-8-ként értelmezi a saját útvonal-sztringjeit**, átalakítja
UTF-16-ra, és a **széles** API-t hívja; csak a 9x-ágon megy a nyers ANSI
`DeleteFileA`.

**Ez zárja le a 2.6/c „csere mód" lépését is:** a `0x00991f00(útvonal, 5)`
**a régi fájlt törli**, és hozzáférés-megtagadásnál (`ERROR_ACCESS_DENIED`)
5 másodpercig újrapróbálja — most már tudjuk, hogy pontosan mit.

> ⭐ **Tanulságos párhuzam a saját kódunkkal.** Ugyanez a hibaosztály nálunk
> a **#1991** volt (a `cv2.imread`/`imwrite` **fájlútvonalas** alakja
> ékezetes néven Windowson némán elbukik). A jegy **le van zárva**: a
> `src/picasapy/cvimage.py` `np.fromfile` + `imdecode` úton olvas, és a
> `scripts/cv2_utvonal_or.py` őr vigyáz rá. **A Picasa ugyanezt a problémát
> ugyanígy kerülte meg** — nem az ANSI API-t hívta, hanem átalakított és a
> széles változatot használta. A mi megoldásunk tehát nem kényszerű
> kerülőút, hanem **ugyanaz a bevált minta**.

#### 2.7 A Film-készítő elrendezése (#5262, 2026-10-17)

**Következtetés:** az eredeti Film-készítő a főablak `panelroot` területébe ágyazott panel, nem külön párbeszédablak. Saját C++ erőforrásosztálya van (`MakeMoviePanel::ResCreate`), de a létrehozási út a `panelroot/makemoviepanel` gyökérelemet kapcsolja a közös felületgyökérhez. A panel tervvászna `800 × 534` egység. Ez a `respack.yt` szerkesztői koordinátája, nem igazolt futásidejű képpontméret. A `panelroot.tre` a panelt a `tabdiv` és a gyökér alsó széle közé horgonyozza; a panel tényleges megjelenési mérete a főablak méretét követi.

**Bizonyítottsági fok: megerősített.** Az A út a `makemoviepanel.tre` és a `respack.yt` dekódolt rétegkoordinátái. A B út a `MakeMoviePanel` típusleíróját használó erőforrás-létrehozó kód, valamint a menüből a `panelroot/makemoviepanel` elemre váltó kód. A két út különböző forrásrétegből jut ugyanarra a főablak-panel következtetésre.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Főablak-panel a `panelroot` alatt. A `MakeMoviePanel::ResCreate` saját C++ erőforrásosztály, nem bizonyíték külön felső szintű ablakra. | A `src/picasapy/app/qml/PicasaPy/CreateDialogs.qml:362-372` `movieDialog` eleme külön `Dialog`, 700 egység széles, magassága legfeljebb 720, illetve a főablak magassága mínusz 24. `modal: false`. | A filmkészítő tartalma a főablak nézetébe kerüljön. A meglévő filmvezérlő és előnézeti logika maradjon használatban. |
| Bal oldalon füles beállító hasáb, jobb oldalon előnézet, alul a filmcsík. A `.tre` kényszerei a főablakhoz igazítják a panelt. | A beállításlapok és az előnézet a párbeszédablak tartalmában vannak. A külön ablakkeret miatt a jelenlegi elrendezés szűkebb területre kerül. | A bal hasáb és a jobb oldali előnézet az eredeti elemfát kövesse. A filmcsík az előnézeti terület alján maradjon. A tervvászon koordinátái legyenek kiinduló arányok, ne rögzített képernyőméretek. |
| A `cancel` elem súgója `Close Movie Maker panel`, és az Escape billentyű is aktiválja. A parancs-elosztó cancel ága a `panelroot/picasatab` könyvtárlapra vált (`0x0061df10`, `0x00620f77`). A klipgyűjtő nézetből a `Back to Movie Maker` gomb visz vissza a filmkészítőbe (`0x0056c2b0`). | A `movieCancelButton` bezárja a párbeszédablakot. | A `Close` és az Escape a könyvtárlapra lépjen vissza. A klipek könyvtárból való kiválasztása után maradjon elérhető a `Back to Movie Maker` visszatérés. |

#### A tervvászon elemei

| Eredeti elem | Hely és méret a tervvásznon | Forrás |
|---|---|---|
| `docbounds`, `basepanel` | `(0,0)`, `800 × 534` | bináris, `respack.yt` rétegfejlécek a `0x001eedc9` és `0x001eedda` fájleltoláson |
| `edittabbase`, fülek | `(4,20)`, `276 × 389`; a fülsáv `(4,26)`, `276 × 25` | bináris, `0x001f0122` és `0x001f88bb` |
| `tabpanel1`, `tabpanel2`, `tabpanel3` | `(5,44)`, `275 × 351`; `(6,57)`, `269 × 351`; `(5,52)`, `276 × 357` | bináris, rendre `0x001f56fc`, `0x001f24ed`, `0x001f0d1e` |
| `previewpanel` | `(287,11)`, `507 × 361` | bináris, `0x001f0005` |
| `moviebk` | `(291,6)`, `501 × 326` | bináris, `0x001f0027` |
| `movieparent` | `(305,6)`, `489 × 326`; kezdetben rejtett belső előnézeti ablak | bináris, `0x001f0049`; szülője a `moviebk`, `makemoviepanel.tre:12-32` |
| `filmcontainer` | `(330,444)`, `455 × 72` | bináris, `0x001eee2f` |
| `cancel` | `(12,451)`, `130 × 28` | bináris, `0x001f0ceb`; `makemoviepanel.tre:542-545` |

Az `edittabbase` és a `tabpanel` méretei az eredeti `800 × 534` tervvászon adatai. A `panelroot/makemoviepanel` függőlegesen a `tabdiv` változóhoz és a főablak aljához horgonyzott (`panelroot.tre:24-33`); a `basepanel` méretezve követi ezt (`makemoviepanel.tre:557-569`). A számok ezért nem garantálnak azonos fizikai képpontméretet más főablak-méretnél. A skálázás mértéke NINCS MEG, és nem becsültük meg.

#### A két bizonyítási út

**A út, erőforrás és geometria.** A `panelroot.tre:24-33` szerint a `panelroot/makemoviepanel` szülője a közös `root`, és a panel a főablak `tabdiv` sora alatt jelenik meg. A `makemoviepanel.tre:515`, `557-569` a jobb oldali előnézetet és a teljes panel alapját rendezi el. A fenti geometria a `respack.yt` megnevezett rétegeinek első négy előjeles `int16` koordinátájából származik. Összevetésként a kollázs ugyanezen tervvásznon a `collagepanel/base` alatt tartja a `rightcontainer` előnézetet; lásd az 1.10 szakaszt.

**B út, létrehozó kód.** A `0x00579550` függvény a `panelroot/makemoviepanel` kulcsot a `MakeMoviePanel::RTTI_Type_Descriptor` (`0x00d3e7bc`) mellett adja át az erőforrás-gyárnak (`0x00c07db2`), majd meghívja a panel inicializálóját (`0x00622150`). A `0x0057cb60` menüút ugyanennek a `panelroot/makemoviepanel` elemnek a betöltését kéri; ezen az úton szerepel a `This feature is not supported for Linux` ág is. A külön `Back to Movie Maker` gombot építő `0x0056c2b0` a `panelroot/makemoviepanel` és a `panelroot/makemovietab` elemet ellenőrzi, így ez a klipgyűjtőből visszatérés útja, nem egy modalitást jelző ablakcím.

#### Cáfoló kísérlet

Az ellenhipotézis az volt, hogy a `movieparent` `window` típusú erőforrás miatt maga a Film-készítő is külön ablak lehet. A szülőfa ezt cáfolja: a `movieparent` a `moviebk` gyereke, és `m_hidden` jelölést kap; a teljes felület alapja ezzel szemben a `root` gyerekeként deklarált `basepanel`. A binárisban a `MakeMoviePanel` osztály gyárútja is a `panelroot/makemoviepanel` felületi elemhez vezet. A külön Win32 ablakosztály neve és az egyes `RT_DIALOG` sablonazonosítók MakeMoviePanelhez rendelése NINCS MEG. Megszerzésük útja a `0x00579550` erőforrás-létrehozó és a `0x006129c0` osztálygyár hívási láncának folytatása, majd az érintett PE-erőforrások azonosítóinak hozzárendelése. Ez nem változtat a két pozitív út egyező elrendezési bizonyítékán.

#### Fejlesztői pontok

Ha a filmkészítő elrendezését a kutatás alapján át kell alakítani:

1. A `CreateDialogs.qml` külön `movieDialog` ablakát cseréld a főablak tartalmi területén megjelenő filmkészítő nézetre. A meglévő filmvezérlő és előnézeti műveletek maradjanak bekötve.
2. A füles beállításokat a bal hasábba, a film előnézetét jobbra, a filmcsíkot az előnézet aljára rendezd. A fenti tervvászon-méretekhez igazodó arányokat használd, miközben a rendelkezésre álló főablak-mérethez rugalmasan igazodsz.
3. A `Close` és Escape állítsa vissza a könyvtárlapot. A klipek kiválasztásához megnyitott könyvtárnézetből a `Back to Movie Maker` térjen vissza ugyanahhoz a filmprojekt-nézethez.
4. A filmkészítés, a projektfájl megnyitása és az előnézet működése maradjon meg a nézetváltás után.

**Kész, ha:**

- a Film-készítő a főablak tartalmi területét használja, külön párbeszédablak nélkül;
- a bal beállító hasáb, a jobb előnézet és az alsó filmcsík a fenti erőforrás-geometriának felel meg, és a panel nem lóg ki a főablakból;
- a `Close` és az Escape a könyvtárlapra vezet vissza, a klipgyűjtőből pedig működik a `Back to Movie Maker` út;
- a filmkészítés, projektfájl és előnézet meglévő funkciói tovább működnek.

### 2.7 A film-előnézet vezérlősávja (`video_control_bar2`) - MŰKÖDÉS

*A 2.2/2.6 a felső panel beállításait, ez a szakasz a film-előnézet ALUL
lévő `video_control_bar2` vezérlősávját (a #1154 „nem feltárt" pontját).
A `.tre`-t és a kezelőket összevetve:*

#### A felület (`video_control_bar2.tre`)

*Forrás: `video_control_bar2.tre:79` (`video_control_bar2/1to1`) · `video_control_bar2.tre:82` (`video_control_bar2/controlbar`) · `video_control_bar2.tre:70` (`video_control_bar2/fullscreen`) — és további 5 elem ugyanott.*

| elem | típus / horgony | szerep |
|---|---|---|
| `video_control_bar2/controlbar` | `root`, `m_scaleX m_offsetT` | a sáv maga |
| `video_control_bar2/moviescrubslider_container` | `m_offsetLTR` | a scrub-tartály |
| `video_control_bar2/time` | `m_systemfont11 textalign center` | **a lejátszási idő** (2.7/b) |
| `video_control_bar2/scaleslider` | `slider 3`, `YConstraint 1,1,0` | a scrub-csúszka |
| `video_control_bar2/volumeslider` | `slider 0`, `m_offsetRT` | a hangerő |
| `video_control_bar2/moviecontrolsclip` | `m_offsetLT` | a play/pause clip |
| `video_control_bar2/1to1` | `m_offsetRT` | a **valódi méret** gomb; Tooltip: „Show actual movie size (don't stretch)" |
| `video_control_bar2/fullscreen` | `m_offsetRT` | a **teljes képernyő** gomb; Tooltip: „Play full screen" |
#### A kezelők (a `MoviePreviewHandler` `0x006248e0` és a hozzá tartozó magok)

| függvény | méret | szerep |
|---|---|---|
| `0x006248e0` | 1030 b | a **MoviePreviewHandler** fő művelet-kezelő (billentyű + felület) |
| `0x00619380` | 86 b | a play/pause **állapot-szinkron** — a `[+0x4a0]` videó-objektum `[+0x7c]` bájtja alapján a `moviecontrols/play` vs `pause` (+ ikonjaik) mutatása |
| `0x0061ca80` | 435 b | a **pause-toggle** — a `[+0x4f2]` flag váltása, a `[+0x4b4]` mediaszolgáltató lejátszás-leállítás, majd a `moviecontrols/pause` elem frissítése |
| `0x0061b1f0` | 611 b | a `video_control_bar2/time` **szövegfrissítő** (2.7/b) |
| `0x0061cc40` | 76 b | az 1to1 gomb **állapotkérdője** |
| `0x005931c0` | 647 b | a `video_control_bar` (SZERKESZTŐ) volumeslider kezelő — a `movievolume` SetPreference-írója |

#### A két preferencia, amit a sáv kezel

| kulcs | tartomány / alap | kezelő |
|---|---|---|
| `Preferences\movievolume` | egész, **0..1000**, alap **500** (=50%, `/1000`-nel normál) | olvasó: `0x00618a0f–0x00618a53` (a MakeMoviePanel-konstruktor: `video_control_bar2/volumeslider`, `fild` + `fdiv [1000.0]`, alap `0x1f4`); író: `0x005931c0` |
| `Preferences\makemovie1to1` | bool, alap **1** (bekapcsolva) | olvasó/író: `0x006161ff`–`0x00616234` (`SetPreference`) + `0x0061cc40` |

### 2.7/b A `video_control_bar2/time` formátuma — MEGFEJTVE

A `0x0061b1f0` (611 b) a `time` elem szövegét építi **két konvertált
időből, `/` elválasztóval** (`0x2f` push a `0x0061b382`-nél):

```
HH:MM:SS / HH:MM:SS
 (eltelt)   (összes)
```

| lépés | művelet | bizonyíték |
|---|---|---|
| bemenet | két 64 bites **DirectShow `REFERENCE_TIME`** (100 ns), a videó 0-pontjától | `fild qword` a `0x0061b2b2` / `0x0061b317` |
| konverzió | `/ 10 000 000` (a `0xcf3e88` = `10000000.0` double) | `0x0061b2bd` |
| kerekítés | az összes-hossz `+0.5` (`0xc72150` = `0.5`) | `0x0061b328` |
| formátum | `ytDateTime::Format4` = **`%.2d:%.2d:%.2d`** (óra:perc:másodperc) | `0x98c9a0`; a `0x9ae560` a formátum-kulcsra: `0xca85f0` |
| fűzés | az eltelt + `/` + az összes string | `0x0061b382` |

Tehát az **eltelt idő** a `video_control_bar2/time` bal oldalán, az **összes
időtartam** a jobb oldalán, `HH:MM:SS`-ben — a DirectShow 100 ns-os
időbázisából. *(A `video_control_bar` — a SZERKESZTŐ — időjelzője ettől
külön él, `m_systemfont11 textalign center`, a `ui-audit-editor.md` videó
szakaszában.)*

### 2.7/c A MoviePreviewHandler billentyű-kezelése (#1154 42–44. rekesz)

A `0x006248e0` a **műveletkód + VK-pár** alapján diszpécsel: a `[+0xc]`
struktúra `[+8]` mezője a műveletkód, a `[+0x10]` a VK-kiegészítő. ⚠️ **Ez
NEM a 26-os közös belső eseménykód-készlet** (`picasa-eger-es-kijeloles.md`
4.2/b) — a `MoviePreviewHandler` modulnak **saját** a kódolása; ahol a
`0x13` itt a Play/Pause-t váltja, ott a 26-os készletben (a rács
kontextusában) a 0x13 „találat-vizsgálat" — a két modul nem osztozik a
jelentésen. A mért váltások:

| `[+8]` | `[+0x10]` | akció | bizonyíték |
|---|---|---|---|
| `0x13` | — | **Pause/Play** (`0x619ac0`) | `0x006248f1`→`0x0062490a` |
| `0x18` | `0x20` (Space le) | a `video_control_bar2/moviecontrols` play/pause + ikon frissítése | `0x00624c3b`–`0x00624c67` |
| `0x17` | `0x20` (Space fel) | **szünet**, ha a `[+0x4f2]` (lejátszik) (a `0x61ca80`) | `0x00624cba`–`0x00624cc5` |
| `0x17` | `0x0d` (Enter) | seek-eltérés-ellenőrzés | `0x00624c82`–`0x00624ca4` |
| `0x0d` | — | **teljes képernyő** (méret-ellenőrzéssel) | `0x00624b67`–`0x00624bec` |
| `0x1f` / `0x20` | — | a teljes-képernyő jelző `[+0x217]` = 1 / 0 | `0x00624b2d`–`0x00624b59` |
| `0x1b` | — | **Esc** — a teljes képernyőből kilépés (a `[+0x213]`-feltétellel) | `0x00624918` |

A 42–44. rekesz (`/`, `,`, `.`) a #1154-ben ⬜-ként szerepelt; a mért
térkép szerint a film-előnézet a **Space-t** és a **Pause-t** használja
lejátszás/szünetre, az **Entert** és az **Escet** a teljes képernyőre — a
`/`, `,`, `.` (SHORTCUTS.XML, 2.4-ben) **nem** ezen a kezelőn megy.

### 2.8 Mi aktiválja a filmkészítést? — a belépési pontok (#1397, #1408)

A `Létrehozás ▸ Film` almenü (`eMenuCreateMovie::ID_MAKEMOVIE`) a
`0x00618050` (a MakeMoviePanel) létrehozásával indul — ez indítja a
`i18n\moviecreate_text.xml` és `i18n\tooltips.xml` betöltését
(`0x00618064`, `0x0061807b`), majd a `video_control_bar2` és a
`makemoviepanel/*` vezérlők felépítését. Az **arc-film** a
`CMakeFaceMoviePanel` (a `0x0061df10` kezelő) — **ugyanaz a `video_control_bar2`
sáv**, `askapplyconfirm`-kapuval (2.5/b). A két filmtípus **egy modul**,
két beállítás-készlettel: a `Preferences\makemovieres` és a
`Preferences\facemakemovieres` külön-külön a normál- és az arc-film
felbontását tárolja (`0x006193e0`).

### 2.8/b A film FELBONTÁSA: hét tétel, két kulcs, két különböző alapérték (2026-09-15, 311. kör, #3155)

*A 2.8 csak annyit mondott, hogy a `makemovieres` és a `facemakemovieres`
„külön-külön" tárolja a felbontást. Ez a szakasz megadja, MIT tárol, MI az
alapértéke, MIKOR melyiket olvassa, és hogy az egyiket SOHA nem írja.*

#### A felbontás-tábla — `0x00c7db50`, hét rekord, 12 bájt egyenként

| index | 16:9-jelző (`+0x00`) | szélesség (`+0x04`) | magasság (`+0x08`) | a legördülő felirata |
|---:|---:|---:|---:|---|
| 0 | 0 | 320 | 240 | 320x240 |
| 1 | 0 | **640** | **480** | 640x480 |
| 2 | 0 | 800 | 600 | 800x600 |
| 3 | 0 | **1024** | **768** | 1024x768 |
| 4 | 0 | 1600 | 1200 | 1600x1200 |
| 5 | **1** | 1280 | 720 | 1280x720 (720p) |
| 6 | **1** | 1920 | 1080 | 1920x1080 (1080p) |

*Forrás: a tábla `0x00c7db50`-től; a rekord-felosztást a `0x008142d0`–`0x008142f1`
bizonyítja (a három mezőt egymás után másolja a beállítás-objektum `+0x2a4`,
`+0x2a8`, `+0x2ac` mezőjébe), a szélesség/magasság szerepét pedig a
`0x00614b40` ciklus, amely PÁRBAN veti össze őket (`[eax-4]` a `+0x2a8`-cal,
`[eax]` a `+0x2ac`-cal).*

**Határ-kontroll:** a tábla pontosan **hét** rekord. A `0x00614b55`-ös ciklus
felső határa `0x00c7dbac`, a `0x00616b0e`-esé `0x54` (= 84 bájt = 7 × 12), és
a 8. rekord helyén már idegen adat áll (`0x3b23d70a` = 0,0025f).

**Független megerősítés a szövegtárból:** a `CMakeMoviePanel::size0` …
`size6` sorok pontosan ezt a hét tételt adják, ugyanebben a sorrendben
(`stringres-en-hu.tsv`) ⇒ **a beállítás értéke a fenti tábla INDEXE**, nem
képpontszám. (A `CMakeMovie::size0`…`size4` egy MÁSIK, ötös lista — nem ez.)

#### A két kulcs alapértéke — binárisból

```
0x00616b19  cmp byte [panel+0x4f0], 0
0x00616b1f  jne 0x00616b42                  ; ID_FACES     -> arc-ág
0x00616b21  cmp byte [panel+0x4f1], 0
0x00616b27  jne 0x00616b42                  ; ID_FACESRANDOM -> arc-ág
            ; NORMÁL film:
0x00616b29  push 0x00c9c598                 ; "makemovieres"
0x00616b37  mov dword [esp+0x74], 1         ; ALAPÉRTÉK = 1  -> 640x480
            ; ARC-film:
0x00616b42  push 0x00c9c584                 ; "facemakemovieres"
0x00616b50  mov dword [esp+0x74], 3         ; ALAPÉRTÉK = 3  -> 1024x768
0x00616b5f  call 0x00407a20                 ; GetPreference
```

**Kontroll-mérés az alapérték-konvencióra:** ugyanez az alak áll a már
dokumentált `CMakeFaceMoviePanel::askapplyconfirm` olvasásánál
(`0x0061dfbe mov dword [esp+0x2c], ebx` = 0, majd `0x0061dfc2 call 0x00407a20`),
ahol az alapérték a 2.5/b szerint **0**. A `lea ecx, [esp+…]` ugyanarra a
rekeszre mutat, mint a beírt érték — a két veremcím a közbeeső `push`-okkal
együtt számolva azonos. A konvenció tehát igazolt.

⇒ **Az arc-film alapból 1024×768, a normál film alapból 640×480.**

#### Mikor melyik kulcs — a két jelzőt a MENÜPARANCS állítja be

```
0x0057cc61  cmp ebp, 0x9d59                 ; ID_FACES
0x0057cc69  mov byte [panel+0x4f0], 1
0x0057cc72  cmp ebp, 0x9d5a                 ; ID_FACESRANDOM
0x0057cc7a  mov byte [panel+0x4f1], 1
```

A két parancsazonosító a `picasa-arcfelismeres.md` táblájából származik
(`eMenuCreateMovie::ID_FACES` = **0x9d59**, `ID_FACESRANDOM` = **0x9d5a**) ⇒

| jelző | jelentése |
|---|---|
| `panel+0x4f0` | a panel **„A kijelölésben lévő arcokból…"**-ként nyílt |
| `panel+0x4f1` | a panel **„Az Emberek albumból…"**-ként nyílt |
| `panel+0x4f3` | származtatott „ez arc-film" jelző (`0x0061823c`) |

A panel felépítésekor ugyanez a pár dönti el a panel-fajta kódját is:
`+0x4f0` → **5**, `+0x4f1` → **6** (`0x00618213`, `0x00618223`), és a 7-es
fajtánál a `0x00618270` maga kapcsolja be a `+0x4f0`-t.

#### ⛔ A `facemakemovieres`-nek NINCS írója

A `"facemakemovieres"` sztring címére (`0x00c9c584`) a teljes `.text`-ben
**pontosan egy** hivatkozás van: a fenti OLVASÁS (`0x00616b43`). A
`"makemovieres"` (`0x00c9c598`) ezzel szemben **kettő**: az olvasás
(`0x00616b2a`) és egy ÍRÁS — a `0x00619469`-es `SetPreference` (`0x00401900`),
amely a kiválasztott indexet menti (`0x00619431`, `−1` esetén **1**-et:
`0x00619437`).

Ez indextől független pásztázás (4 bájtos mutató a nyers képben), és a
**kontroll-pozitív maga a `makemovieres`**, amelyre ugyanez a módszer megtalálja
az írót is. ⇒ **Az eredeti Picasa az arc-film felbontását nem menti vissza**:
a legördülőn beállított érték a panel bezárásával elvész, a következő
megnyitás újra az 1024×768-at kapja.

**Termékre:** ha nálunk a felhasználó át tudja állítani az arc-film
felbontását, döntsük el kimondva, hogy az eredeti (nem mentő) viselkedést
másoljuk-e — ez nem ízléskérdés, hanem mért eltérés.

#### Ami NYITVA marad

A tábla első mezőjének (`+0x00`) a NEVE. Értéke **1** pontosan a két 16:9-es
tételnél és **0** az öt 4:3-asnál, és a `0x008142d0` a beállítás-objektum
`+0x2a4` mezőjébe másolja — de a `+0x2a4` eltolás a binárisban több osztályban
is szerepel (a `0x006191e9` például egy egészen más objektumra ír ugyanide),
ezért az olvasóját ez a kör nem szűrte le. A megszerzés útja: a `+0x4bc`
alobjektum osztályának RTTI-je, és azon belül a `+0x2a4` olvasói.

## 3. A Létrehozás menü többi tétele

| menüpont | ID | mit tudunk |
|---|---|---|
| Poszter készítése… | `ID_POSTER` | dialógusa megvan: `runtime/poster.fen` — nagyítás 200–1000% tíz lépésben, papírméret-választó, **„Overlap tiles"** jelölő; a súgó-szöveg: *„ha nem akarsz vágni, vágd a képet a papír méretére"* |
| Beállítás háttérképként | `ID_WALLPAPER` | egyképes asztali háttér (a kollázs-panelnek külön `Desktop Background` gombja van) |
| Hozzáadás a képernyővédőhöz… | `ID_SCREENSAVER` | a bináris a `]screensaver` albumcímkét és a `#db3\saverlist.txt` listát frissíti; a `CAlbumState` a címkét `screensaver` INI-kulcsra képezi, de a menüút tényleges `.picasa.ini`-írása nincs igazolva. Részletek: `picasa-menu-parancsok-viselkedes.md` 35.3. |
| Ajándék CD készítése… | `ID_BURNCD` | a `cdautorun/` mappa tartalma megy a lemezre (Windows autorun + Mac `.app`), dialógus: `runtime/cdchoose.fen` |
| Közzététel a Bloggeren… | `ID_EXPORT_SENDTOBLOGGER` | a `buttons/core-lh2.pbz` `custombutton/blogger` gombja: `verb="hybrid"`, URL `https://photos.blogger.com/picasa-post.g` — a szolgáltatás megszűnt |
| Exportálás TiVo DVR-re… | `ID_TIVO` | a `plugins/ytITivo.yti` plugin (TiVo Desktop-integráció) |
| Indexképek nyomtatása… | `ID_FILE_PRINTCONTACTSHEET` | a Contact Sheet kollázs-típus nyomtatási párja |

### 3.1 Poszterlapokra bontás és kimenet (#5469, 2026-10-21)

**Bizonyítottsági fok: feltételes.** A parancs bekötése, a vezérlőnevek, a
rács elemszáma, a kimeneti mappa és névminta, valamint a JPEG-minőség útja
bináris címmel alátámasztható. Az átfedéses téglalap pontos képlete, a
papírmérethez igazított levágás, az első megnyitás alapértékei, egy mentőopció
jelentése és a metaadat-kezelés nem dőlt el; ezek nélkül a teljes viselkedés
nem tekinthető lezártnak.

#### Parancskezelő, vezérlők és beállítások

Az `ID_POSTER` parancsazonosító `0x9d30`; a diszpécser `0x005cc150` címe a
`0x00530c10` kezelőt hívja. A kezelő a `0x007387c0` konstruktorral építi fel a
`poster` párbeszédet. A kötőfüggvény `0x00738a70` a `factor`, `paper` és
`overlap` nevű vezérlőket olvassa vissza. A `factor` listaindexéhez 2-t ad,
így a vezérlő értékei a 200%-os és 1000%-os nagyításokhoz tartozó 2 és 10
közötti osztószámot adják.

A `paper` választás utolsó értékének megőrzését a párbeszéd `0x00738800`
függvénye végzi; a méretlista a területi beállítástól függ: metrikus esetben
`10x15` és `20x25`, amerikai esetben `4x6` és `8.5x11`. Ezek a méretnevek a
`0x00738800` függvényben, a `CPosterDlg::size1` és `CPosterDlg::size2` fordítási
kulcsokban szerepelnek. A konstruktor a három vezérlő háttérmezőit nullázza,
de ez önmagában nem bizonyítja, hogy első megnyitáskor melyik listaelem látszik:
a teljes, első indítási alapérték és a tárolási névtér nincs meg. A
`paper` kulcs olvasása és az utolsó választás visszaállítása igazolt
(`0x0073883e`-`0x00738862`); a `factor` és az `overlap` tartós kulcsa nincs
megállapítva.

#### Lapszám, papírméret és DPI

A kezelő a nagyítási lista indexéből `N=2..10` osztószámot képez, majd két,
`0`-tól `N-1`-ig futó ciklussal `N×N` képkimenetet állít elő. A forrás két
képponttengelyét egyenként `N` egyenlő részre osztja; a határokat lebegőpontos
értékekből egész koordinátává alakítja (`0x00530d6f`-`0x00531081`). Ez a kód
nem számít lapméretből képpontméretet, és nem olvas DPI-értéket. A párbeszéd
`paper` mezőjének indexe a kezelő lapgeneráló részében nem jelenik meg, ezért
a papírméret és a DPI kapcsolatára **NINCS MEG** bizonyíték. Nyitott marad,
hogy más, közvetett hívási út használja-e ezt a választást.

#### Átfedés

Az `overlap` jelölő a párbeszédben hamis értékről indul (`0x007387c0`), a
kezelő pedig csak bejelölt állapotnál lép az átfedéses ágba
(`0x00530eb4`). Ebben az ágban a bináris a `0xcf4f20` címen levő
`1.100000023841858` és a `0xcf50b0` címen levő `-0.10000002384185791`
konstanst használja, majd egy x87 koordináta-transzformációval állítja elő a
kimeneti határokat. Az ág és a konstansok igazoltak, de a transzformáció
eredője nincs teljesen visszafejtve, ezért az átfedés pontos szélessége és az
egyes szélek kiterjesztési iránya **NINCS MEG**. Megszerzéséhez a
`0x00530c10` célzott Ghidra-dekompilációja és aszimmetrikus, jelölt képpel
készült eredeti programfelvétel kell.

#### Levágás és képarány

A leíró súgója azt tanácsolja, hogy a csonkolás elkerüléséhez a forrásképet a
papírral azonos méretarányra kell vágni. Ez nem mondja meg, hogy eltérő
képaránynál a program melyik oldalt, milyen irányban és hol vágja le. A
binárisban azonos arányú forrásrács készül, de a papírmérethez igazított
levágás helye és iránya **NINCS MEG**. A kérdést a `0x00530c10` Ghidra-köre
és különböző képarányú, ismert mintájú képekkel végzett Colab-felvétel dönti
el.

#### Kimeneti mappa, név, formátum, minőség és metaadat

A kezelő a `%d-%d-%s` formátumot használja (`0x00c89808`); a két egész
argumentum oszlop, majd sor sorrendű, a harmadik mező a forrás alapnevéből és
eredeti kiterjesztéséből áll (`0x00531124`-`0x00531134`, `0x0049ff10`). Az
eredeti forráskönyvtárat megtartó útvonal-objektumot az `0x004089e0` hozza
létre; az új nevet a `0x009a37b0` állítja be, majd a `0x009a3620` a végső
kiterjesztést `.jpg`-re állítja. A fájlt a `0x009d6010` író `wb` módban
nyitja meg (`0x009d6041`-`0x009d6053`). Az eredeti mappába tehát
`<oszlop>-<sor>-<alapnév>.jpg` kerül.

A poszterkezelő a mentőnek `1`, `4` és `90` értékeket ad át
(`0x00531191`-`0x005311a5`). A `0x009d6010` általános ága a
`0x009d64e0` → `0x009d7120` → `0x009d53e0` útvonalon adja tovább ezeket. A
`90` érték a `0x00ad3b30` JPEG-kvantálási útjába jut; ott a `100-90`, majd
kétszeres átskálázás eredménye 20, amelyet a `0x00c75260` és `0x00c75360`
kvantálótáblákra alkalmazó `0x00ad3970` használ. Ez alátámasztja a JPEG
kimenetet és a 90-es minőségi paramétert; a `4` opció jelentése **NINCS
MEG**. A metaadat megőrzése vagy eltávolítása **NINCS MEG**; ezt eredeti
kimeneti fájl metaadatainak forrásképpel történő összevetése dönti el.

#### Nálunk és a megvalósítási következmény

Jelenlegi kódunk ugyan `N×N` rácsot készít, de az átfedést cellánként a
cellaméret 10%-aként számolja, `sor-oszlop-eredetifájlnév` sorrendet és a
forrás kiterjesztését használja, valamint nem ad át explicit JPEG-minőséget
(`src/picasapy/printing/poster.py`). Az eredeti sorrend
`oszlop-sor-alapnév.jpg`, a forrás mappájában, JPEG-minőség 90-nel. A
`paper_size` paramétert a vágáshoz nem használja. Az átfedés pontos geometriája,
a levágás, az első indítási alapértékek, a `4` íróopció és a metaadat-kezelés
fejlesztés előtt további Ghidra-kört vagy Colab-felvételt igényel.

#### Cáfoló kísérlet

Ellenőriztem azt az alternatív feltevést, hogy a Poszter az kontaktlap-nyomtató
kezelőt használja. A `0x005ddb80` gyorsgomb-kezelő `makeposter` ága a
`0x00530c10`-et hívja, a `printcontactsheet` ág pedig külön útvonalon a
`0x00744ee0`-et. A két művelet nem ugyanaz a kezelő; ez a cáfoló kísérlet
egyező eredményt adott a külön menüparancs diszpécserével.

#### Nyitott kérdések és megszerzésük

- Ghidra-kör kell: `0x00530c10` - az átfedéses x87 koordináta-transzformáció
  pontos képlete, a határok kerekítése, valamint a vágási irány [blokkoló].
- Ghidra-kör kell: `0x009d6010` - a `{1, 4, 90}` íróbeállítások közül a `4`
  pontos jelentése, valamint az, hogy a mentő milyen képadatot ír a JPEG-be
  [blokkoló].
- Colab-felvétel kell: eredeti programból készített poszter ismert
  aszimmetrikus és eltérő képarányú képből, be- és kikapcsolt átfedéssel; a
  kimeneti fájlok helyének, nevének, pixelhatárainak, bájtformátumának és
  metaadatainak rögzítésével.
- Colab-felvétel kell: friss beállítási profillal megnyitott párbeszéd és
  második megnyitás, hogy az első indítási alapértékek és a `factor`, `paper`,
  `overlap` tartós kulcsai igazolhatók legyenek.

### 2.8/c A mappa-fejléc FILM-gombja — alapból látszik (2026-10-09, #4539)

*A #4539 első kérdése: van-e film-gomb a MAPPA fejlécében, és alapból látszik-e.
A válasz igen.*

**Bizonyíték (a képernyőkép, nagyítva):** a referencia-képernyőkép
`research/testdata/screenshot/2026-07-17 20 54 38.png` (Picasa 3.9.141,
Windows 11) mappa-fejlécének gombsora, balról jobbra:
`▸` (diavetítés) · `[+kép]` (kollázs) · **`[+filmszalag]` (film)** · `☆`
(csillagozottak, halvány) · mentés (halvány) · `Feltöltés ▾`.
Ugyanez a sor látszik a másik két fejléces képernyőképen is
(`2026-07-17 20 57 35.png`, `2026-07-17 20 54 38.png`).

**Szövegtár és elem:** `headerpanel/create_movie` — tooltip „Create Movie
Presentation" / „Mozgófilmes prezentáció létrehozása"
(`referencia/i18n-hu/headerpaneltext.xml`); a `referencia/ui-leltar.csv`
szerint a `headerpanel` gyermeke, `mousedown` tulajdonsággal, **rejtés
(`m_hidden`) nélkül**, a `movie_icon` gyermekével. A 2.8-as belépési pontok
(`Létrehozás ▸ Film`) mellé tehát egy HARMADIK, mappa-fejléc-belépés is van.

**Elhelyezés:** a kollázs után, a csillag előtt; a `faceheaderpanel`-ben a
kollázs és a film egymás mellett van (`create_collage` 115 → `create_movie`
147), a mappa-fejlécben ugyanez a sorrend. A teljes sorrend (play · kollázs ·
film · csillag · mentés · feltöltés) a képernyőképről olvasható.

**Mit csinál:** a fejléc SAJÁT csoportjának képeit adja a Filmkészítőnek
(ugyanaz a halmaz, mint a kollázs-gombnál — #1006). A film-gomb nem
testreszabható elem (mint a Feltöltés); a gombsor testreszabásában nincs
benne, így a régi, mentett sorok sem rejtik el.

⛔ **Nyitva marad:** a `headerpanel/create_movie` GUID-jének és az alapkészlet
`+0xdb5` jelzőjének megfeleltetése (2.8 / 44.4 a `picasa-menu-parancsok-viselkedes.md`-ben).
A képernyőkép a kérdésre (alapból látszik-e) már önmagában válaszol, a GUID
csak a testreszabhatóságot érintené — az nálunk nincs kimondva.

⛔ **Nem mért:** a gomb pixel-geometriája. Az eredeti képernyőképen a gomb
nagyjából a kollázs méretű (a 29 × 27 a faceheaderpanel mért értéke);
nálunk ugyanez a méret van.

## 2/b. A diavetítés vezérlősávja — teljes leltár a binárisból (#433, 2026-08-15)

Forrás: `oneup.tre`, `oneuptext.tre`, `slideshowctrls.tre`, és a `respack.yt`
rétegtéglalapjai (a módszer és a csapdája:
[`binaris-regeszet-modszertan.md`](binaris-regeszet-modszertan.md) 14/c —
a **méretek** authoroltak, az abszolút pozíciókat a `.tre` felülírhatja).

### A sáv maga

*Forrás: `oneup.tre:168` (`oneup/caption`) · `oneup.tre:164` (`oneup/stripback`).*

```
oneup/stripback: root
YConstraint 1, 1, -20      # az ablak aljától 20 képponttal feljebb
m_centerX                  # vízszintesen középre
```

Mérete a csomagban **797 × 50** képpont; a fölötte lebegő felirat
(`oneup/caption`) **550 × 10**, `YConstraint 1, 1, -100`.

### A tíz vezérlő, balról jobbra

*Forrás: `oneup.tre:156` (`oneup/centergroup`).*

| elem | méret | típus / szerep | felirat |
|---|---|---|---|
| `exit` | **74 × 35** | kilépés a diavetítőből, ikon + felirat | **Kilépés a diavetítőből** |
| `timeline` | **157 × 35** | a teljes képernyős qshow Időrend módjának indítása | **Időrend** |
| `rotateleft` · `rotateright` | **26 × 34** | forgatás | — |
| `prev` | **26 × 30** | előző kép | — |
| `auto` (lejátszás) | **36 × 36** | indít/szünet | — |
| `next` | **26 × 30** | következő kép | — |
| `star` | **27 × 33** | csillagozás | — |
| **`transtype`** | **143 × 21** | **`popuplist` = legördülő** | az átmenet neve |
| `captionbutton` | **54 × 33** | **kétállású** felirat-kapcsoló | — |
| `dtclip` | **103 × 44** | a diaidő csoportja | **Megjelenítési idő** |

A `prev` · `auto` · `next` hármas külön konténerben ül
(`oneup/centergroup`, 118 × 47, `m_centerX`) — vagyis **a lejátszás-vezérlők
a sáv közepére vannak igazítva**, a többi elem tőlük balra/jobbra rendeződik.

### A diaidő-csoport (`dtclip`)

| elem | méret | mi ez |
|---|---|---|
| `tpslabel` | 103 × 11 | a **„Megjelenítési idő"** felirat, a csoport TETEJÉN |
| `minusone` | **14 × 13** | −1 mp, `Property setautorepeat 1` (nyomva tartható) |
| `tps` | 48 × 15 | a szám (középre igazítva) |
| `plusone` | **14 × 13** | +1 mp, szintén auto-ismétlő |

### ⚠️ A feliratmód KÉTÁLLÁSÚ, nem hármas

*Forrás: `oneup.tre:112` (`oneup/caption_icon`) · `oneup.tre:116` (`oneup/caption_yesicon`) · `oneup.tre:121` (`oneup/captionbutton`) · `oneup.tre:164` (`oneup/stripback`).*

A jegy 3. pontja azt feltételezte, hogy a feliratmód **három**állású
(felirat / fájlnév / nincs), a nyomtatás-opciókkal azonos módon. **A forrás
ezt nem támasztja alá:** a `captionbutton` egyetlen kapcsoló, ami két ikon
között vált:

```
oneup/captionbutton: oneup/stripback
Property showtarget oneup/caption_yesicon
Property hidetarget oneup/caption_icon
```

Két ikon (`caption_icon` 17 × 19 és `caption_yesicon` 16 × 18), show/hide
párban — vagyis **felirat BE / KI**. Hármas választó a diavetítés sávjában
nincs.

*Bizonyítottsági fok: erős* (a két ikon és a show/hide pár explicit; azt nem
zártuk ki, hogy a mód máshol — pl. a Beállításokban — háromállású legyen).

### Két külön sáv létezik

| erőforrás | sáv mérete | tartalma |
|---|---|---|
| `oneup/*` | 797 × 50 | a **teljes** vezérlősor (a fenti tíz elem) |
| `slideshowctrls/*` | **235 × 50** | **csak** a `transtype` legördülő (196 × 21) |

Mindkettő ugyanúgy horgonyzott (`YConstraint 1,1,-20`, `m_centerX`), és az
átmenet-választó mindkettőben `popuplist`, azonos
`Property itempadding 2 2 22 2` beállítással (a jobb oldali 22 képpont a
legördülő-nyílnak).

### 2/b/1 ⛳ Tételes összevetés a MAI felülettel (2026-09-15, #2992)

A #2992 azt kérdezte, a **spec** vagy a **kutatás** volt-e hiányos, amiért a
vetítő vezérlő-készlete hiányzik. **Egyik sem:** a fenti leltár teljes, és a
#433 kutatása is átkerült ide. A hiány a **megvalósításban** volt — és azóta
nagyrészt megszűnt.

| a leltár eleme | nálunk (`SlideshowView.qml`) |
|---|---|
| `exit` | ✅ `slideshowExitButton` |
| **`timeline`** | ❌ nincs a diavetítőben; a meglévő `TimelineView.qml` év/hónap-rács nem az eredeti qshow Időrend módja |
| `rotateleft` · `rotateright` | ✅ (`↺` · `↻`) |
| `prev` · `auto` · `next` | ✅ (`◀` · `slideshowPlayButton` · `▶▶`) |
| `star` | ✅ `slideshowStarButton` |
| `transtype` (`popuplist`) | ✅ `slideshowTransitionBox` |
| `captionbutton` (kétállású BE/KI) | ⚠️ `slideshowCaptionModeButton`: háromállapotú (felirat / fájlnév / nincs), ezért nem azonos az eredeti láthatóságkapcsolóval |
| `dtclip` (`tpslabel` + `minusone` + `tps` + `plusone`) | ✅ `slideshowTimeBlock` |
| **`minusone`/`plusone` `setautorepeat 1`** | ✅ **2026-09-15 óta** (`autoRepeat: true`) |
| a sáv lebegése/elrejtése | ✅ `HoverHandler` + `slideshowHideTimer` |

#### ⚠️ Az eredeti `timeline` gomb a qshow Időrend módja, nem a könyvtárrácsé

Az eredeti `oneup/timeline` a teljes képernyős **qshow Időrend módba** visz
(a kattintási és inicializáló ág részletei a 2/b/2 pontban, a qshow belépési
útja a [`picasa-menu-parancsok-viselkedese.md`](picasa-menu-parancsok-viselkedese.md)
38.2.16-38.2.17 pontjában). Ez nem az alkalmazásablakon belüli dátumrács.
A #5377 a `TimelineView.qml`-ben teljes képernyős, mappakártyás Időrend-
bemutatót valósít meg; a Nézet ▸ Időrend és a Ctrl+5 aktív. A PicasaPy
fejlécében nincs Időrend-gomb: a binárisban mért eredeti `timeline` gomb
`m_hidden`, és a bemutató vezérlői a teljes képernyős ablakban vannak. A
gyűjtemény-forrás és a dátumjelentés nyitott kérdéseit a #5401 tartja nyilván.

⇒ Az eredeti gomb útja binárisból ismert; a bemutató felületi mozgásának
mért részképletei a #5377-ben elkészültek, a gyűjtemény-forrás kutatása nyitott.

### 2/b/2 - A `timeline` és a `captionbutton` kattintási ága (#5547, 2026-10-22)

**A `timeline` kattintása és módja.** A `0x008032e0` (`OneUpUI` esemény-
elosztó) a `oneup/timeline` nevet a `0x008034ce`-`0x008034fe` ágban
azonosítja, majd a `0x00803522` címen meghívja a `0x007fda00`-t. Ez nem a
főablak dátumrácsára vált: a `0x007fda00` a qshow-objektumot csak akkor
állítja át, ha `[this+0x2d8] != 0` és `[this+0x538] != 0`; a negatív
`[this+0x3f4]` értéket nullázza, a `0x0097e510(0)` segédet hívja, beállítja
`[this+0x3be] := 1`-et, lekéri az időt a `0xc40298` függvényimporton át,
majd `0x00802230(this, 1)`-et hív. Ezután `[this+0x3ba] := 0`,
`[this+0x3bb] := 0`, `[this+0x3b8] := 1` és `[this+0x3b9] := 1`.
Az Időrend-mód jelzőjét a qshow eseménykezelője (`0x007fde80`) is olvassa;
az Időrend-lista építője `0x008018a0` (részletek: a menü-parancsok spec
38.2.35-38.2.42). A `0x00802230` már a meglévő `[this+0x3ec]` listából
veszi az aktuális azonosítót, véletlen eltolásokat készít, a
`[this+0x2e4]` forrásobjektum virtuális metódusától kér tartalmat, frissíti
a puffert és QPC-időt ment (`0x008022ba`-`0x00802629`). A lista
szolgáltatója, az adott kép/felirat forrása és a futásidejű ütemezés
**NINCS MEG**; a `0x00802630` automatikus léptetőút ugyanezt a függvényt
`0` paraméterrel hívja, míg a `0x007fda00` a `1` paraméteres ágat indítja.

**A gomb láthatósága.** A `0x008037e0` `Preferences\BigSlideshow2`-t
olvassa, a lekérdezés alapértékét `1`-re állítja, majd a `0x004019b0`
visszatérési értékéből számít egy lokális jelzőt. A `oneup/timeline` akkor
kap mutató (`+0x68`) hívást, ha mindhárom feltétel igaz:

1. a `0x004019b0` lekérdezés eredménye nem nulla;
2. `[0x00d33958]` értéke `0x10` vagy `0x20`;
3. a `0x008037e0` második paraméterének második bájtja nulla.

Ellenkező esetben a timeline csomópont rejtő (`+0x6c`) hívást kap, a
`oneup/transtype` pedig fordítva: mutatást, illetve rejtést. A
`0x0097e030` a `[0x00d33958]` értékét a GDI `GetDeviceCaps` függvény
`BITSPIXEL` (`0x0c`) lekérdezéséből írja; ez a képpontonkénti bitek száma,
nem a korábban nyitva hagyott bemutatómód-jelző. A második bájt forrása a
`0x005e8a70` `param_2` argumentuma: a `thumbui/timelinebutton` 1-et, a
`thumbui/sbutton` 0-t ad át (38.2.16). A root és a név szerinti csomópont
létezése szintén szükséges ahhoz, hogy a láthatósági hívás lefusson.

**A `captionbutton` kattintási ága.** A `0x008032e0` `0x00803373`-
`0x008033b7` közötti ága megkeresi a `oneup/captionbutton` csomópontot,
összeveti a `[node+0x359]` állapotjelző bájtot, majd a `oneup/caption` csomópontot
mutatja (`0x009cd730`) vagy rejti (`0x009cd760`). Ebben az ágban
`[node+0x359]`-be **nem ír**. Az erőforrás (`oneup.tre:121`) a
`caption_yesicon` / `caption_icon` párost `showtarget` / `hidetarget`
kapcsolatként deklarálja, tehát az eredeti feliratvezérlő kétállapotú.

Az `ytButtonNode::vftable` (`0x00ce4874`) `+0x78` slotja a `0x00a65170`;
ez a metódus a saját `this+0x359` mezőjét írja (`0x00a651ae`,
`0x00a651e1`, `0x00a6525f`), majd a `0x00a64a10` felé eseményt indít.
Ez **lehetséges író**, de a binárisból nem igazolt, hogy a
`oneup/captionbutton` futásidejű objektuma `ytButtonNode`, vagy hogy az adott
kattintás ezen a sloton éri el a `0x008032e0`-t. Mérés (a `paszta.py`
teljes `.text` pásztázása, memória-kapuval): 2 884 879 utasításban 218
közvetlen `+0x359` hivatkozás és 47 íróhely; az írójelölt tehát nem egyedi.
Az eseményút feltételesen követhető: a `0x00a65170` a `0x00a64a10`-en át
`0x8000004` kódú eseményt indít; a `0x009e3b00` a `[this+0x213]` értékétől
függően a szülő `+0x58` vagy `+0x70` slotját hívja, a `OneUpUI` `+0x58`
slotja pedig `0x008032e0`. A konkrét TRE-erőforrás runtime vtable-je,
útválasztási bájtja és szülőkapcsolata hiányzik, ezért ez az út nem bizonyítja,
hogy a kattintás a jelölt írót használja. A pontos objektum-/eseménykapcsolat:

`Ghidra-kör kell: 0x00a65170 - a oneup/captionbutton futásidejű vtable-je, a [+0x213] útválasztási jelzője és szülőlánca; eléri-e a kattintás a +0x78 → 0x00a64a10 → 0x009e3b00 → OneUpUI +0x58 útvonalat? [blokkoló]`

**Két független út.** A) Az `0x008032e0` utasításszintű olvasása azonosítja a
`timeline` hívását, a feliratbájt olvasását és a két láthatósági segédet;
az `0x007fda00` külön diszasszemblálása mutatja a qshow-állapotírást.
B) A `0x008037e0` hívási ágai és az `0x0097e030` adatútja egymástól
függetlenül megadják a `timeline`/`transtype` fordított láthatóságát és a
`BITSPIXEL` eredetét; a `0x005e8a70` módparaméter-hívói a második bájt
jelentését erősítik. A `captionbutton` esetén a teljes `.text`-pásztázás
azt erősíti meg, hogy a diszpécserág nem író, de a konkrét erőforrás és az
`ytButtonNode` író slot közötti él továbbra is hiányzik.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a `timeline` a főablaki
év/hónap-rácsot jelenti: az eseményág célját (`0x007fda00`), az általa
beállított `+0x3b8` állapotot és annak qshow-fogyasztóit (`0x007fde80`,
`0x008018a0`) külön követtem. Az út a teljes képernyős qshow Időrend módba
vezet; a rácsra mutató kapcsolat nem része ennek az útnak. Azt is próbáltam
cáfolni, hogy a `0x00803373` ág írja a `+0x359`-et: az utasításokban csak
összehasonlítás és show/hide hívás van, a teljes pásztázás pedig más
íróhelyeket talált. Ez megerősíti, hogy a vizsgált ág maga nem az író; a
konkrét kattintási író azonosítása ettől továbbra is nyitott.

| vezérlő | Eredeti | Nálunk | Teendő |
|---|---|---|---|
| `timeline` | `0x00803522` → `0x007fda00`: a qshow Időrend-mód állapotát indítja; láthatósága a fenti feltételektől függ. | A könyvtári `TimelineView.qml` dátumrács létezik; a vetítő sávban nincs qshow-vezérlő. | Ha termékparitás kell, külön qshow bemutatómódot tervezzünk; a dátumrácsot ne kössük be ennek helyettesítőjeként. Az animáció/tartalom részletei előbb nyitott kutatást igényelnek. |
| `captionbutton` | A `.tre` két ikonállapotot deklarál; a `0x00803381` olvassa a `+0x359`-et és az alapján mutat/rejt. A kattintási író **NINCS MEG**; `0x00a65170` csak jelölt. | `slideshowCaptionModeButton` három módot vált: felirat / fájlnév / nincs. | A láthatóságkapcsolót válasszuk külön a felirat tartalmi módjától, vagy dokumentáljuk a három mód eltérő terméki célját. Az eredeti kattintásíró bekötését a blokkoló Ghidra-kör döntse el. |

**Bizonyítottsági fok: nyitott a teljes jegyre.** A `timeline` mód és
láthatósági feltétele két egymást ellenőrző bináris útból
**megerősített**. A feliratgomb olvasó-/show-hide ága és kétállapotú
erőforrása **megerősített**; az adott kattintás `+0x359`-írója nyitott,
`0x00a65170` csak feltételes jelölt.

**A #5547 „Kész, ha” mérlege.** ✅ A `timeline` kattintásának célja és a
láthatósági feltétel megvan bináris címmel; a gomb a qshow Időrend-módba
vezet, nem a főablaki dátumrácsba. ✅ A feliratág olvasó/show-hide
viselkedése binárisból megvan; az adott kattintási íróra adott indokolt
statikus negatív (az elosztóág nem ír, a lehetséges író futásidejű
bekötése nincs meg) és a célzott Ghidra-kérdés fent szerepel.

#### ⚠️ Az ismétlés SEBESSÉGE nincs mérve

A `.tre` csak a **jelzőt** adja (`setautorepeat 1`), a késleltetést és az
ismétlési időt nem. A megvalósítás a Qt alapértelmezését használja
(300 ms / 100 ms), és ezt a kód kommentje is kimondja — **nem mért érték**.

*Bizonyítottsági fok: megerősített* (a `respack.yt` rétegtéglalapjai és a
`.tre` kötések; a feliratok a `panel-feliratok-hu.tsv` magyar oszlopából).

## 4. Mit érdemes ebből átvenni

1. A **hat kollázs-típus** és a **három keret** jól definiált, mind
   megvalósítható tisztán geometriából — nincs benne titkos algoritmus.
2. A **`.cxf` mezőnevek** adják a saját projektformátumunk vázát; ha
   ugyanezeket használjuk, egy későbbi `.cxf`-import is nyitva marad.
3. Az **automatikus mentés + helyreállítás** a kollázsnál és a filmnél is
   alapfelszereltség volt — a felhasználó munkája sosem veszett el.
4. Az **átmenet-készlet** (18 darab) és a **11 szövegstílus** kész
   specifikáció a filmkészítőhöz.
5. A **Pan and Zoom – face** az arcfelismerés és a diavetítés
   összekapcsolása — ez a Picasa egyik legkedveltebb apró trükkje.

## A biztonsági mentés (Back Up Pictures) — teljes üzenet-leltár (2026-08-16)

A funkció a **`il_BurnPanel`** osztály körül él, és a magyar szövegforrásban
**147 bejegyzése** van. A menütétel: `eMenuTools::ID_TOOLS_BACKUP` →
**„Képek biztonsági mentése…"**.

### Három célfajta

| cél | vezérlő / erőforrás | magyar |
|---|---|---|
| **mappa** | `il_BurnPanel::bkbutton`, `bkfolder` | „Biztonsági mentés" |
| **CD/DVD írás** | `il_BurnPanel::burnbutton` | „Írás" |
| **ISO-fájl** | `ISOFilter`, `ISOFolder`, `ISONoWrite` | „ISO-fájlok", „ISO-k" |

Ha nincs író meghajtó, a program **felajánlja az ISO-t**:

> `nodrives` — „Nincs elérhető CD-meghajtó. … Esetleg inkább szeretne egy
> .ISO-fájlt létrehozni?"

### Alapértékek

| erőforrás | EN | HU |
|---|---|---|
| `il_BurnPanel::bksetname` | My Backup Set | **Saját mentési készlet** |
| `il_BurnPanel::DefBkFolder` | `\Picasa Backup\` | **`\Picasa biztonsági másolat\`** |
| `il_BurnPanel::picfolder` | Pictures | **Képek** |
| `il_BurnPanel::PicasaCDName` | Picasa CD | Picasa CD |
| `il_NewBkDialogTitle` | Backup Set | **Mentési készlet** |

### A készlet ÚJRAFUTTATHATÓ — külön üzenetcsoport az első és a további futásra

| csoport | mikor | db |
|---|---|---:|
| `InitialCollect::*` | **első** mentés | 11 |
| `UpdateCollect::*` | **ismételt** mentés (inkrementális) | 14 |
| `UpdateCollectUpload::*` | ismételt, feltöltéssel | 1 |
| `UpdateMedia::*` | a hordozó frissítése | 4 |
| `InsertNext::*` | a következő lemez kérése | 13 |
| `WriteProgress::*` | írás közbeni állapotok | **21** |
| `BackgroundProc::*` | háttérfolyamat | 6 |
| `BackupCopy::*` | másolás | 3 |
| `debugmenu::*` | meghajtó- és lemezadatok | 18 |

**Ez igazolja a jegy címét:** a mentési készlet valóban újrafuttatható, és a
program külön szövegkészletet tart az **első** és a **további** futásokra.

A készlet szerkeszthető és törölhető:
`il_NewBkDialog::EditTitle` → **„Mentési készlet szerkesztése"**,
`il_NewBkDialog::EditOKButton` → **„Módosítás"**,
`il_NewBkDialog_delete` → **„Biztosan törli a(z) … mentési készletet?"**

### A visszaállítás ÖNÁLLÓ program, jegyzékfájllal

A `RestoreDialog::*` csoport mást ír le, mint a mentés:

| erőforrás | HU |
|---|---|
| `RestoreDialog::open` | **Jegyzékfájl megnyitása…** |
| `RestoreDialog::cantFind` | Nem található „%1$s" vagy „%2$s" nevű **jegyzékfájl** |
| `RestoreDialog::cantcopy` | Nem sikerült **az alkalmazás átmeneti példányának** másolása |
| `RestoreDialog::cantlaunch` | Nem lehet megnyitni az alkalmazást |
| `RestoreDialog::changetitle` | Hely kijelölése a fájloknak |
| `RestoreDialog::deflocation` | **a Picasa biztonsági mentésből\\** |
| `RestoreDialog::finished` | %1$d fájl visszaállítása befejeződött; összesen %2$s. |
| `RestoreDialog::quit` | Kilépés |

**Két dolog derül ki:**

1. A mentés **jegyzékfájlt** ír a hordozóra, és a visszaállítás abból
   dolgozik. A fájl neve `%s.%s` mintával épül, a típusjelzője
   **`PicasaManifest`** (`0x00843a90`, `0x00844e40`).
2. A visszaállító **maga az alkalmazás**, amit a mentés **rámásol a
   hordozóra** („az alkalmazás átmeneti példányának másolása") — vagyis a
   mentés önhordó: Picasa nélkül is visszaállítható.

### Webalbumba mentés

`PWA_storage_needed`, `PWA_storage_total`, `PWA_no_storage_change`,
`…_nolimit` — a mentés célja a **Picasa Webalbumok** is lehetett, és a
program kiírta, mennyi további tárhely kell hozzá.

### Ami Linuxon értelmetlen

`imapierror` — „Nem sikerült csatlakozni a **Windows IMAPI2** CD-író
motorhoz" + egy súgó-URL. A CD/DVD-írás Windows-specifikus API-ra épül; egy
Linux-változatnak sajátot kell használnia.

*Bizonyítottsági fok: megerősített* (a 147 erőforrás-bejegyzés és a
`PicasaManifest` két hivatkozása).

## A diavetítés: három beállítás, három üzemmód, 22 átmenet (2026-08-16)

### A három beállítás — alapértékkel

A diavetítő konfigurációját egyetlen függvény olvassa be
(**`0x007fa7f0`**, 1 690 bájt):

| kulcs | alapérték | cím | mit szabályoz |
|---|:---:|---|---|
| **`SlideshowEffectTime`** | **3** | `0x007facd3` (`mov dword ptr [esp+0x3c], 3`) | **másodperc/dia** |
| `LoopSlideshow` | **0** | `0x007fad0a` | ismétlés |
| `PlayMP3Tracks` | **1** | `0x007fadbb` | háttérzene lejátszása |

*(Az utóbbi kettő alapértéke a `0x006e0cb0` regisztrálójából, lásd
`picasa-fo-ablak-elrendezes.md`.)*

A zene forrása a **`MP3SlideshowPath`** kulcs (`0x005e8a70`, `0x006e1100`,
`0x006e3990`, `0x0075cdc0`).

### A kezelőfelület: egy lebegő sáv a képernyő alján

*Forrás: `slideshowctrls.tre:15` (`slideshowctrls/stripback`) · `slideshowctrls.tre:7` (`slideshowctrls/transtype`).*

`slideshowctrls.tre` — mindössze két elem:

```
slideshowctrls/stripback: root
YConstraint 1, 1, -20        # a képernyő aljához, 20 px-szel feljebb
m_centerX                    # vízszintesen KÖZÉPRE

slideshowctrls/transtype: slideshowctrls/stripback
m_offsetLT
Property itempadding 2 2 22 2   # az átmenet-választó legördülő belső margói
```

Vagyis a diavetítés vezérlője **egyetlen, középre igazított sáv** a
képernyő alján, benne az **átmenet-választóval**.

### Három bemutató-üzemmód, nem egy

A `0x005e8a70` (3 614 bájt) háromféle bemutatót indít:

| belső név | folyamatjelző | HU |
|---|---|---|
| `BigSlideshow2` | — | **Diavetítés** |
| `Flipbook` | `CThumbUI::MakeFlip` | **Lapozható könyv előkészítése…** |
| (időrend) | `CThumbUI::MakeTimeline` | **Időrend előkészítése…** |

A menütételek: `eMenuView::ID_VIEW_SLIDESHOW` → **„Diavetítés"**,
`eMenuView::ID_VIEW_TIMELINE` → **„Időrend"**,
`eMenuLabelFolder::ID_ALBUM_SLIDESHOW` → **„Diavetítés megtekintése"**.

Mindháromhoz kell tálca-tartalom: „You must have images in the Picture Tray
to do this."

### ⚠️ Az átmenetek száma 22, nem 18

A `CTransitions::*` erőforrás-család **22 bejegyzést** tartalmaz. A
korábbi jegyzet 18-at említett, és a felsorolásból hiányzott a **`rect`**
(**„Négyszög"**).

| kulcs | EN | HU |
|---|---|---|
| `cut` | Cut | **Kivágás** |
| `dissolve` | Dissolve | **Szétoszlás** |
| `dissolveblack` | Dissolve through black | **Szétoszlás feketén át** |
| `dissolvewhite` | Dissolve through white | **Szétoszlás fehéren át** |
| `wipeleft` | Wipe - left | **Törlés - balra** |
| `wiperight` | Wipe | **Törlés** |
| `wipeup` | Wipe - top | **Törlés - felfelé** |
| `wipedown` | Wipe - bottom | **Törlés - lefelé** |
| `diagwipeul` | Wipe - up left | **Törlés - balra fel** |
| `diagwipeur` | Wipe - up right | **Törlés - jobbra fel** |
| `diagwipedl` | Wipe - down left | **Törlés - balra le** |
| `diagwipedr` | Wipe - down right | **Törlés - jobbra le** |
| `pushleft` | Push - left | **Tolás - balra** |
| `pushright` | Push | **Tolás** |
| `pushtop` | Push - top | **Tolás - felfelé** |
| `pushdown` | Push - bottom | **Tolás - lefelé** |
| `circlein` | Circle - inwards | **Kör - befelé** |
| `circleout` | Circle | **Kör** |
| **`rect`** | **Rectangle** | **Négyszög** |
| `kenburns` | Pan and Zoom | **Pásztázás és nagyítás** |
| `kenburnsaoi` | Pan and Zoom - face | **Pásztázás és nagyítás - arc** |
| `timelapse` | Time Lapse | **Gyorsítás** |

> Figyeld meg a **fordítási aszimmetriát**: a „sima" irány neve nem
> tartalmaz irányjelzőt (`wiperight` = „Törlés", `pushright` = „Tolás",
> `circleout` = „Kör"), a többi igen. Ez az eredeti Picasa saját
> megoldása — ne „egységesítsük".

*Bizonyítottsági fok: megerősített* (a beállítás-olvasó függvény, a
`slideshowctrls.tre` teljes tartalma, és a 22 erőforrás-bejegyzés).

### #4856 — `kenburnsaoi`: a binárisban talált arcút és a nyitva maradt képkockák (2026-10-13)

**A regisztráció megerősített.** A `CTransitions::kenburnsaoi` sztring
(`0x00cb2f00`) és a „Pan and Zoom - face" felirat (`0x00cb2a90`) a
`0x00771a10` átmenet-regisztrálóban szerepel. A `0x00d34188` táblában a
20. indexű, 16 bájtos rekord címe `0x00d342c8`; első mezője `0x0a`. A
`0x00771e60` a `0x0a` csoporthoz a `0x0076ed30`-as
`ytDoubleAffineAOITransitionNode` konstruktorát választja. Kontrollként az
1. indexű `kenburns` rekord csoportja `1`, amelyhez a
`ytDoubleAffineTransitionNode` (`0x0076e100`) tartozik. A RTTI-vtáblák
mindkettőnél a `0x0076e880` renderelőt adják; az AOI-változat
`0x0076ee50`-et, az általános változat `0x0076e4e0`-t használ célterület
építésére. Forrás: bináris `0x00771a10`, `0x00771e60`, `0x00d34188`,
`0x00cb320c`, `0x00cb313c`.

**A filmkészítő útján van arc-régió lekérés.** A `0x00813330` a
`0x00813593` környezetében ellenőrzi, hogy az átmenet indexe `0x14`
(20); csak ezen az ágon hívja a `0x00813c50` segédet. A segéd elfogadott
bemeneti rekordjánál `[rekord] == 3` és `[rekord+8] != -1` feltételt
ellenőriz, majd a `+0x2d8` objektum vtbl `+0x58` és `+0xa0` metódusán
keresztül lekéri az azonosítóhoz tartozó adatot, a téglalapot a kép
határaihoz igazítja, és a `+0x2c5` jelző szerint választ illesztő ágat. Ez azt
mutatja, hogy a filmkészítő út egy előre átadott, azonosítóval megadott
régióból képez célterületet. A hívó `ESI`-je a `this+0x1a8` rekordra mutat
(`0x008134b5`, a segédhívás `0x008135c5`); a régióazonosítót a segéd a
rekord `+0x8` mezőjéből olvassa, vagyis az objektum `+0x1b0` címéről.
A segéd nem választ több arc közül, hanem az átadott azonosítót használja.
Az azonosító közvetlen runtime forrása megvan: a `0x00812470` a `this+0x48`
időzített sávból hívja a `0x00610d30` mintavevőt, majd a mintát a
`this+0x1a8` rekordba másolja (`0x00612350`; az alaprekord `+0x8` mezőjét a
`0x006123d0` is másolja). A mintavevő a sáv 0xf8 bájtos rekordjai közül az
aktuális időponthoz tartozó rekordot dolgozza fel. Azt viszont ezek az
utasítások nem mutatják meg, hogy a sávrekord honnan kerül a memóriába, vagy
hogy az azonosító a `.picasa.ini` `faces=` mezőjéből származik-e; a több arc
közötti választás is a rekord előállításának nyitott része. Forrás: bináris
`0x00812470`,
`0x00610d30`, `0x00612350`, `0x006123d0`, `0x00813330`, `0x00813c50`.

A `+0x1a8`/`+0x1b0` eltolások teljes `.text`-pásztázása sok találatot adott,
köztük verem-lokális és objektummezőnek látszó címzéseket is; az eltolás
egyezését ezért nem tekintettem íróazonosításnak. A `0x00812470` hívási
útjának követése adott pozitív láncot a mintavevőtől a rekordmásolásig.

**A gyár két azonos négyelemű téglalapot ad az AOI-konstruktornak, majd a
filmút az egyik jelöltet felülírja.** A `0x00771dc0` a beolvasott
`(x0,y0,x1,y1)` négy dwordöt kétszer másolja a `0x00771e60`-nak; a 10-es
csoport a `0x0076ed30` konstruktort választja (`0x00772221`–`0x00772286`).
A filmkészítő az arcsegéd eredményét később az objektum `+0x4b0…+0x4bc`
mezőibe írja (`0x008137b0`–`0x008137d2`). A két bemeneti halmaz tehát az
AOI-osztályban külön mezőpár, de ezek „kezdő”/„vég” képkockához rendelése
nem olvasható ki ebből az adatláncból. Ez az utasításszintű út nem bizonyítja,
hogy a két mező melyik képre hat.

**A cél-téglalap számítása mért, de ez még nem a képkocka-mozgás.** A
`0x0076ed30` két, egyenként 4 floatos téglalap-jelöltet kap; a
`0x00cf3ed0`-n lévő `−1.0` a hiányjelző. Ha az első jelölt érvényes,
`0x0076ee50` kiszámolja; ha a második négy értéke nem mind `−1.0`, az
`ee50` újra lefut, és felülírja az első eredményét. Ha a második teljes
sentinel, az első eredménye marad. A cél `+0x448…+0x454`
mezőbe kerül. A `0x0076ee50` modellje előző helyi körben QEMU-i386 alatt
10/10 eseten egyezett a natív kimenettel. A mért képlet: érvényes
`(x0,y0,x1,y1)` esetén a befoglaló cél `rne(x0−0.5, y0−0.5, x1+0.5,
y1+0.5)`; a `0.5` konstans címe `0x00c72150`. A forrásméretre a
`0x009b4b60` lefedő illesztése fut, majd a kód eltolja a téglalapot a kép
határáig úgy, hogy a méretét megtartja. Ez a mérés a célterület-építőt
ellenőrzi, nem az eredeti program képkockáját.

**A renderelő simított paramétert használ, a végpontok jelentése nyitott.**
A `0x0076e880` a `0x0076eb40`-et hívja; az utóbbi a
`0x0076dd10` interpolátort kétszer futtatja, `(t+1)×0.5` és `t×0.5`
paraméterrel. A `0x0076dd10` paraméterét `[0,1]` közé korlátozza, majd a
`u²×(3−2u)` simítófüggvényt alkalmazza. A `3.0` bináris konstans címe
`0x00cf39f8`, az `0.5`-é `0x00c72150`. Ez egyutas disassembly-olvasat;
QEMU-mérés és renderelt frame-összehasonlítás nem készült erre az
interpolátorra. A két tömb (`+0x414`, `+0x438`), a képpárhoz való
hozzárendelésük, az időparaméter tényleges tartománya, valamint a kezdő- és
végképkocka pontos képi jelentése ezért **nem tekinthető megállapítottnak**.

**A teljes képernyős vetítés útja továbbra sincs összekötve az AOI-renderelővel.**
A `0x005e8a70` a `Preferences/BigSlideshow2` beállítást olvassa
(`0x005e93f8`–`0x005e9415`). A cáfoló keresés közben előkerült egy másik,
korábban nem dokumentált közösgyár-használat: a `0x00760b00` függvény a
`ThumbUISlideShow::transition` beállítást írja, majd hívja a `0x00760d50`
függvényt; ez a `0x00771e60` gyárat használja. A `0x00760d50` azonban
kifejezetten az `editpanel/previewclip` objektumot kéri le (`0x00760d6b`–
`0x00760d9f`), és ennek `%x-transition` tulajdonságához rendeli az elkészült
csomópontot. Ez az út tehát az előnézetet bizonyítja, nem a
`BigSlideshow2` renderelését.

Az index közvetlen hivatkozásai és a `paszta.py` memóriakapun át futtatott
teljes `.text`-pásztázása egyaránt a gyár következő közvetlen hívásait
találta: `0x0057c9f4`, `0x00760eac`, `0x00771e2c`. A pásztázás nem talált
közvetlen gyárhívást a `0x005e8a70` függvényben; ez az indirekt, virtuális vagy
esemény-visszahívásos bekötést nem zárja ki. A keresés cáfolta a „gyárat csak
a filmkészítő használja” munkahipotézist, de nem döntötte el a
`BigSlideshow2` útját. A jelenlegi `SlideshowView.qml`-ben a két Ken Burns
kulcs viselkedése különvált: a `kenburns` két provider-kivágást
interpolál, a `kenburnsaoi` külön középre igazított skálázást futtat
(`SlideshowView.qml:426-463`, `778-812`, `835-857`). Ez a helyi kód nem
bizonyítja a `BigSlideshow2` eredeti bekötését. A vetítési súgó továbbra is
csak azt írja, hogy az „arc” változat erősebben nagyít
(`src/picasapy/help/features/nezegetes.md:303-324`).

**Nyitott, a fejlesztést blokkoló kérdések:**

- `Ghidra-kör kell: 0x00812470 - honnan kerül a this+0x48 időzített sáv memóriájába a 0xf8 bájtos rekord, ki állítja be a +0x8-as régióazonosítót, és igazolható-e .picasa.ini faces= kapcsolat vagy többarcos kiválasztás? [blokkoló]`
- `Ghidra-kör kell: 0x005e8a70 - a BigSlideshow2 hogyan köti a teljes képernyős renderelőt a ThumbUISlideShow::transition beállításhoz; eljut-e a kiválasztott átmenet a ytDoubleAffineAOITransitionNode osztályhoz? [blokkoló]`
- `Ghidra-kör kell: 0x0076ed30 - a két négyfloatos AOI-paraméter melyik bemeneti kép célterületét állítja, és hogyan kerül ez a +0x414 / +0x438 interpolált képkockákra? [blokkoló]`
- `Ghidra-kör kell: 0x0076eb40 - a +0x414 és +0x438 interpolált tömb melyik bemeneti képkockához tartozik, mi a t tartománya, és melyik a renderelt kezdő-/végállapot? [blokkoló]`

**Bizonyítottság:** a név- és osztályregisztráció megerősített (regisztráló, statikus rekord és RTTI-vtáblák); a filmkészítő arc-lekérési út feltételes (utasításszintű olvasat, de az azonosító forrása nyitott); a vetítés teljes viselkedése nyitott. A `kenburnsaoi` tényleges, archoz tartó vetítési képkockáihoz renderelt ellenőrzés szükséges.

### #4856 — 3. kör: a `kenburnsaoi` útja, és mi NEM igazolt (2026-10-13)

**Kérdés:** a teljes képernyős diavetítés (`BigSlideshow2`) a `kenburnsaoi` AOI-átmenetet használja-e; honnan jön az arc-régió; mi a kezdő- és végkép képlete.

**Röviden.** (1) Az arc-ág feltétele bizonyított: a képkocka-függvény (`0x00813330`) a `this+0x28c == 0x14` (`kenburnsaoi`) esetén hívja az arcsegédet (`0x00813c50`). (2) A régió-rekord a `0x0074dfc0` képkocka-metódusból jön (`0x00812470` → mintavevő a `this+0x48` sávból), de hogy ez `.picasa.ini faces=` adat-e, nem igazolt. (3) A `kenburnsaoi`-t tényleg használó út a **film-/diaszerkesztő** (`MakeMoviePanel`), nem a `BigSlideshow2`. (4) A `BigSlideshow2` útja **nyitott**. (5) A kezdő/végkép képlete **nyitott**: nincs renderelt végpont.

#### 3.1 Az arc-ág (bizonyított, dekompilált `0x00813330`)

Forrás: `~/picasapy-agent/referencia/ghidra-koteg-2026-10-13/008127b0.c`, a `CALLEE FUN_00813330` blokk (1069–1275. sor).

- A `0x00813330` a `this+0x28c` átmenet-indexet olvassa; a `0x00812aa0(this, this+0x1a8, this+0x7ec, …)` hívás után, de az AOI-csomópont építése előtt: `if (*(int*)(this+0x28c) == 0x14) FUN_00813c50();`.
- Ha már van átmeneti csomópont (`this+0x560`) és típusa `0x14`, a csomópont `+0x4b0…+0x4bc` mezőit a `_DAT_00cf3ed0` konstanssal (−1.0 hiányjelző) írja felül.
- Ha nincs csomópont, a `0x00771dc0(this+0x7c4, this+0x7ec, …)` hívás építi az AOI-csomópontot két téglalappal: `this+0x7c4` és `this+0x7ec`.
- A `0x00812aa0` törzse ebben a körben **nincs** dekompilálva; a `this+0x7ec` kitöltése a `this+0x1a8` rekordból csak a hívási mintából következik.

#### 3.2 A régió-rekord forrása (részben bizonyított)

- `0x0074dfc0` a `CDXSlideshowPin` vtábla bejegyzése (`rtti.csv`, `CDXSlideshowPin::vftable`, `0x00cb1a08`, 5. oszlop) — a bináris-indexben ez a pin-osztály egyik virtuális metódusa. Közvetlen hívója nincs (vtábla-hívás nem látszik az xref-indexben).
- `0x0074dfc0` közvetlenül hívja: `0x00812470` és `0x008127b0` (`xrefs.csv`). Ezek hívják a `0x00813330`-at.
- `0x00812470` a `this+0x48` időzített sáv rekordját mintavevővel (`0x00610d30`) olvassa, és a `this+0x1a8` rekordba másolja (`0x00612350`, `0x006123d0`) — az előző körök szerint.
- Ami NINCS: a sáv 0xf8 bájtos rekordjainak fájlbeli forrása, és hogy az azonosító (`+0x8`) `faces=` adat-e. Több arc közti választás: nincs a láncban bizonyítva.

#### 3.3 Melyik út használja a `kenburnsaoi`-t (hívási gráf, xref-index)

Ez a szakasz a közvetlen `call`-élekre támaszkodik (`xrefs.csv`, kind = `call` — más típus nincs). Pozitív lánc, nem negatív bizonyíték.

| # | Lépés | Bizonyíték |
|---|---|---|
| 1 | `0x005de8e0` (szerkesztőpanel-dispatcher) hívja `0x005d59f0`-t | xref |
| 2 | `0x005d59f0` tartalmazza az `editpanel/editslideshow` sztringet (0x005d59f0 string-xref) | string_xrefs |
| 3 | `0x005d59f0` → `0x00689f40` (`MakeMoviePanel::autosave` sztring) → `0x00625000` (`IPicasaApp`) | xref + string_xrefs |
| 4 | `0x00625000` → `0x008287b0` (`IPVCommunicate`, `CTransTimeline` sztring) | xref + string_xrefs |
| 5 | `0x008287b0` → `0x0074e670` (72 bájtos függvény; a szomszédos `0x0074e710` a `CTransTimeline` sztringet és a filter-vtábla-tagok közül is egyet tartalmaz — a `0x0074e670` szerepe nincs dekompilálva) | xref + string_xrefs |
| 6 | `0x0074e670` → … → a `CDXSlideshowPin` példány vtábla-hívása → `0x0074dfc0` | `0x0074dfc0` a pin-vtábla tagja (rtti); a 5→6 él NEM látszik xrefben |
| 7 | `0x0074dfc0` → `0x00812470`/`0x008127b0` → `0x00813330` (arc-ág) | xref |

A 6. lépés a gyenge pont: a pin-példány létrehozását és a vtábla-hívást az xref-index nem látja. Ezt a lépést a `0x0074e670` dekompilált törzsének olvasása döntené el (nincs még a körben).

#### 3.4 A `BigSlideshow2` útja (NYITOTT)

- `0x005e8a70` olvassa a `BigSlideshow2` beállítást; a sztringjei: `BigSlideshow2`, `Flipbook`, `CThumbUI::MakeFlip`, `Preparing timeline...`, `CThumbUI::MakeTimeline`.
- A beállítás-betöltő `0x008037e0`: `Preferences`, `BigSlideshow2`, `oneup/timeline`, `qshow`, `oneup/transtype`. A `oneup/transtype` a teljes képernyős nézet átmenet-vezérlője.
- Hívási gráf (közvetlen `call`-élek, mélység ≤ 6): `0x005e8a70` **nem éri el** sem a gyárat (`0x00771e60`), sem `0x00760b00`-t, sem a `CTransTimeline`/pin láncot (`0x008287b0`, `0x0074e670`, `0x0074dfc0`, `0x00813330`). Ez a 0x005e8a70 gráfja — nem zárja ki a vtábla-, indirekt- vagy esemény-visszahívásos bekötést, ezért **nem negatív bizonyíték**.
- Nyitott kérdés: a `CThumbUI::MakeTimeline` (a `BigSlideshow2` builder) ugyanazt a `CTransTimeline` objektumot hozza-e létre, mint a `MakeMoviePanel` — ez a kör nem döntötte el.

#### 3.5 A szerkesztő átmenet-választója (bizonyított, de nem a vetítés)

- `0x005d3290` (`editoneup/transtype`) → `0x00760b00` (`ThumbUISlideShow::transition`) → `0x00760d50` (`editpanel/previewclip`, `%x-transition`) → `0x00771e60` (gyár). Ez az **előnézeti** csomópont (a `editpanel/previewclip` a szerkesztő előnézete), nem bizonyított, hogy a teljes képernyős lejátszás ugyanezt használja.
- A `0x0075d810` (szintén `ThumbUISlideShow::transition` sztring) hívója a `0x005733f0`.

#### 3.6 A kezdő- és végkép (NYITOTT)

Kódból ismert, renderelt ellenőrzés nincs:

- A célterület-mérés (`0x0076ee50`, 10/10 QEMU-egyezés, előző kör): érvényes `(x0,y0,x1,y1)` esetén `rne(x0−0.5, y0−0.5, x1+0.5, y1+0.5)`, majd a forrásméretre illesztés a `0x009b4b60` szerint, a kép határára tolva (méret-megtartással).
- Az interpolátor (`0x0076eb40`, csak disasm, 10-12c szakasz): a `0x0076dd10`-et kétszer hívja, `(t+1)×0.5` és `t×0.5` paraméterrel; a paramétert `[0,1]`-re szorítja, és `u²×(3−2u)` simítást alkalmaz. A `+0x414` és `+0x438` tömbök hozzárendelése a kezdő/végképkockához **nyitott**.
- Nincs renderelt kezdő- és végkép. A jelenlegi `kenburns` QML-ág két kivágást interpolál, de ezek megfeleltetése az eredeti `+0x414` és `+0x438` tömböknek, valamint a Picasa képkockáinak **NINCS MEG** (`SlideshowView.qml:426-463`, `778-812`, `835-846`).

Nem becsültem a képletet: a fenti két tömb és a `t` tartománya kimondottan nyitott.

#### 3.7 Nyitott pontok (ebben a körben)

- [blokkoló] `0x0074e670` dekompilálása: a pin-példány létrehozása és a vtábla-beállítás (3.3 6. lépés).
- [blokkoló] `0x005e8a70` és `0x008037e0` vtábla-/indirekt hívásai: a `BigSlideshow2` tényleg a `CTransTimeline`/pin-ágon megy-e (3.4).
- `0x00812aa0` dekompilálása: a `this+0x7ec` és a `this+0x1a8` közti pontos leképezés.
- `0x00813c50` dekompilálása: a `+0x4b0…+0x4bc` írói, és hogy a face-régió `faces=`-eredetű-e.
- Renderelt végpont: még egyetlen kezdő- vagy végképkocka sincs.

#### 3.8 4. kör: a pin-hívó és az arcsegéd dekompilálva, a vetítési kapcsolat nyitott (2026-10-13)

**Eredmény.** A három új Ghidra-kivonat két részletet tisztáz: a `0x0074e670` egy indirekt vtbl-hívás előtt felépíti a `CDXSlideshowFilter` objektumot; a `0x00813c50` bemeneti rekordból és egy azonosítóból téglalap-kimenetet képez, amelyet a `0x00813330` a meglévő AOI-csomópont `+0x4b0…+0x4bc` mezőibe ír. Egyik eredmény sem köti össze a `BigSlideshow2` teljes képernyős útját ezzel az AOI-csomóponttal, és egyik sem mutatja meg a rekord `.picasa.ini`-beli eredetét. A kezdő-/végképkocka képlete és a renderelt ellenőrzés továbbra sincs meg.

**Az új bináris olvasat.** A `0x0074e670` a `0x0074e580` létrehozó segédet hívja; a segéd `CDXSlideshowFilter`-t állít be, `0x4c0` bájtos objektumot foglal és meghívja a `0x0074d1c0` konstruktort. Ezután a `0x0074e670` a kapott objektum vtbl-jén indirekt metódust hív az `&DAT_00c43490` argumentummal és a hívótól kapott paraméterrel. Ez a filter-/pin-út helyi felépítését támasztja alá, de a virtuális cél és a teljes képernyős vetítéstől való elérése ebből a kivonatból nem következik. Forrás: bináris `0x0074e670`, `0x0074e580`, `0x0074d1c0`; a `0x00c43490` argumentum jelentése: **NINCS MEG**.

A `0x00813c50` a hívótól kapott, `EAX`-ban mutatott rekord első és harmadik dwordjét vizsgálja: az elsőnek `3`-nak, a harmadiknak `−1`-től különbözőnek kell lennie. Ezután a `this+0x2d8` objektum virtuális `+0x58` és `+0xa0` metódusát hívja az azonosítóval, és négy floatot ír a kimeneti pufferbe. Sikertelenségkor a négy kimeneti floatot előbb a `0x00cf3ed0` sentinelértékre állítja. A `0x00813330` a kapott négy floatot egy már létező, megfelelő RTTI-típusú AOI-csomópont `+0x4b0…+0x4bc` mezőibe másolja (`0x008137b8`–`0x008137d2`). A vizsgált függvényekben nincs `.picasa.ini`-olvasás; a rekord előállítási helye és az azonosító `faces=`-hez kötése **NINCS MEG**. A `+0x4b0…+0x4bc` mezőket nem azonosítottuk kezdő-/végképkocka-mezőként. Forrás: bináris `0x00813c50`, `0x00813330`, `0x008137b8`–`0x008137d2`, `0x00cf3ed0`.

**Két külön út összevetése.**

| Út | Pozitív bizonyíték | Mit nem dönt el |
|---|---|---|
| A — teljes képernyős bemutatás | A `0x005e8a70` út a `0x008037e0` beállítás-/nézetépítőhöz vezet; a kód a `BigSlideshow2`, `oneup/timeline` és `oneup/transtype` bemutatási beállításokat használja. Forrás: bináris `0x005e8a70`, `0x008037e0`. | A kiválasztott `oneup/transtype` csomópontja, illetve az AOI-gyár/pin felé vezető konkrét kapcsolat: **NINCS MEG**. |
| B — filter- és AOI-részletek | Két külön pozitív részlet ismert: a `0x0074e670` létrehozza a filter-objektumot és vtbl-hívást végez; a `0x00813330` → `0x00813c50` út rekordból AOI-téglalapot készít és ír. Forrás: bináris `0x0074e670`, `0x00813330`, `0x00813c50`; xref `0x008287b0` → `0x0074e670`, `0x0074dfc0` → `0x00812470`/`0x008127b0`. | A két részlet közötti virtuális kapcsolat, a filter-hívás konkrét célja és az A útba való becsatlakozás: **NINCS MEG**. |

A két út tehát nem ad egyező, végigkövethető láncot. Ez nem bizonyítja, hogy a teljes képernyős vetítés nem használ AOI-t: a hiányzó él lehet virtuális vagy esemény-visszahívásos. A bináris-index negatív találatát nem tekintettem cáfolatnak. A független újraolvasás — a három dekompilált függvényből kiindulva, a korábbi következtetések nélkül — ugyanerre jutott; az xref-adatokkal összevetve a pozitív élek egyeznek, a vetítési összekötő él továbbra sem ismert.

**Cáfoló kísérlet.** Azt a hipotézist próbáltam cáfolni, hogy a `BigSlideshow2` a már ismert timeline/AOI utat használja: a teljes képernyős bemutatási ágat a filter/pin út ismert hívóihoz és az AOI-íróhoz követtem. A teljes képernyős ág `oneup/transtype`-ot választ, a másik ág filter-vtábla-hívást és a timeline rekord/AOI írói láncot mutat; a vizsgált bizonyíték nem ad köztük összekötő élt. Ez a hipotézist **nem erősíti meg**, de az indirekt hívás lehetősége miatt **nem is cáfolja**. Ellenőrzésként a két útból külön indított újraolvasás és az xref-lánc egyezett a fenti pozitív részletekben; a negatív kapcsolat hiányát egyik sem kezeli leletként.

**A megmaradt nyitott kérdések.**

- `Ghidra-kör kell (pontosítva, 4.5): a 0x008037e0 által az oneup/transtype csomóponton hívott +0x68/+0x6c célok osztálya és vtáblája; elérheti-e a 0x00771e60 vagy a 0x0074e670 útját? [blokkoló]`
- `Ghidra-kör kell: 0x008287b0 - mi a 0x0074e670 által használt interfész-vtábla-hívás konkrét célja, és milyen objektumot ad át a pin/AOI út következő szakaszának? [blokkoló]`
- `Ghidra-kör kell: 0x00812470 - mi tölti fel a this+0x48 időzített sáv rekordjait, és ki állítja be a rekord +0x8 régióazonosítóját; van-e bizonyítható faces= adatút? [blokkoló]`
- `Ghidra-kör kell: 0x00812aa0 - hogyan képeződik le pontosan a this+0x1a8 időzített rekord a this+0x7ec téglalapra, és melyik téglalap melyik átmeneti végállapothoz tartozik? [blokkoló]`
- `Ghidra-kör kell: 0x0076e880 - a +0x414 és +0x438 tömbökből milyen bemeneti képkocka lesz, és hogyan jut el a két végállapot a renderelőhöz? [blokkoló]`
- Renderelt frame-pár vagy frame-sorozat, amely az arc nélküli és arcos dián a tényleges induló-/végállapotot igazolja: **NINCS MEG**. A célterület-mérés (3. kör) önmagában nem ilyen mérés.

**Bizonyítottsági fok ebben a körben: nyitott.** Az egyedi függvényutasítások a fenti címeken olvashatók, de a `BigSlideshow2` → AOI kapcsolat, a `faces=` eredet és a renderelt mozgás nincs két független úttal megerősítve. Következésképp nincs átadható, eredeti Picasa-viselkedést leíró kezdő-/végképlet vagy küszöb.

#### 4.1 A `BigSlideshow2` idővonal-építőjének virtuális kapuja (2026-10-16)

**Kérdés.** A teljes képernyős vetítés `oneup/transtype` kiválasztása eljut-e a filmkészítőben ismert `kenburnsaoi` AOI-ágig; mi a dia arc-régiójának forrása; és mi a Picasa fallbackje arc nélkül?

**Következtetés.** A teljes képernyős út egy virtuális callbackig követhető, de annak célja nem oldódott fel. Ezért sem az AOI-ág használata, sem a régió forrása (`faces=`, `imagedata_facerect` vagy más), sem az arc nélküli teljes képernyős skála és középpont nem állapítható meg. Ez nyitott eredmény, nem negatív bizonyíték arra, hogy a vetítés nem használ arcot.

**A teljes képernyős út pozitív nyoma.** A `0x005e8a70` a `BigSlideshow2` beállítást olvassa, és a `CThumbUI::MakeTimeline` ciklusban képenként a CThumbUI-vtábla `+0x90` helyét hívja (`0x005e9494`-től). Az RTTI-vtábla `+0x90` bejegyzése `0x00562cc0`; ez a thunk a `this+0x2bc` mezőből vesz objektumot, majd annak vtáblája `+0x20` helyén végez indirekt hívást. A CThumbUI-konstruktor (`0x005643e0`) ezt a mezőt a hívótól kapott mutatóval tölti; a hívó `0x004039f0` a szülő `+0x1034` mezőjét adja át. A callback célobjektumának típusa és a virtuális hívás célfüggvénye **NINCS MEG**. A `0x008037e0` beállítás-/nézetépítő a `BigSlideshow2`, `oneup/timeline` és `oneup/transtype` kulcsokat is olvassa, de ezek olvasása nem bizonyítja, hogy az átmenet az AOI-gyárhoz vagy a filmkészítő pinjéhez jut. Forrás: bináris `0x005e8a70`, `0x005e9494`-`0x005e94f1`, `0x00562cc0`, `0x005643e0`, `0x004039f0`, `0x008037e0`; RTTI: `CThumbUI::vftable`.

**Összevetés a bizonyított filmkészítő ággal.** A film-/diaszerkesztő útján a `0x00813330` csak `this+0x28c == 0x14` (`kenburnsaoi`) esetén hívja a `0x00813c50` segédet. A segéd a bemeneti rekord `+0x8` mezőjéből régióazonosítót olvas, és a `this+0x2d8` objektum virtuális `+0x58` és `+0xa0` metódusait használja a téglalap elkészítéséhez. A vizsgált függvény nem olvas `.picasa.ini` `faces=` mezőt, és nem olvas közvetlenül `imagedata_facerect` oszlopot. Más, külön útvonalon a `0x00446610` olvas `imagedata_facerect` adatot; ez nem köti a mezőt a teljes képernyős vetítéshez. A `.picasa.ini`-től az adatbázis-oszlopig, illetve az AOI-régióazonosítóig tartó adatút **NINCS MEG**. Forrás: bináris `0x00813330`, `0x00813c50`, `0x00446610`; adatbázis-mezőleltár: `picasa-imagedata-rekord.md`, `facerect` `+0xdc0`.

**Arc nélküli eset és render.** A filmkészítő AOI-segéd sikertelen rekordnál a négy kimeneti értéket a `0x00cf3ed0` címen lévő `-1.0` sentinelre állítja; az AOI-konstruktor is ezzel inicializálja a `+0x4b0`-`+0x4bc` mezőket. Ez a lokális sentinelviselkedés nem bizonyítja a `BigSlideshow2` látható fallbackjét. A teljes képernyős út pontos középpontja, zoomaránya és kezdő-/végképkockája: **NINCS MEG**. A korábbi QEMU-próba a célterület-számítást mérte, nem képkockát renderelt. Ebben a körben nem készült QEMU-render: a hívási út és a renderelőhöz szükséges objektumkapcsolatok nem ismertek, a meglévő harnessnek nincs kész slideshow-transition futtatója. Forrás: bináris `0x00813c50`, `0x0076ed30`, `0x00cf3ed0`; renderelt mérés: **NINCS MEG**.

**Két független út és cáfoló kísérlet.** A) A Ghidra-kimenet a `0x005e8a70` függvényben pozitívan mutatja a `Preferences/BigSlideshow2` olvasását és a `0x008037e0` hívását. B) A külön RTTI- és konstruktorút a `CThumbUI +0x90` slotot, a `+0x2bc` thunkot és a `CThumbDB::vftable +0x20` célját (`0x00423300`) azonosítja (`0x005e9494`, `0x00562cc0`, `0x005643e0`, `0x004039f0`, `0x00415790`, `0x00c81f78`). A két út nem ad bizonyított kapcsolatot a `0x00771e60` átmenetgyárral vagy a `0x0076d900` illesztővel, ezért a teljes képernyős használat **nyitott**. Cáfoló próbálkozásként a callback `0x00423300` célját vetettem össze a transition-gyár hívóival. A pozitív RTTI-találat szerint a cél `CThumbDB`-metódus, nem átmenetkonstruktor; a `0x005e8a70`-ből ismert pozitív közvetlen él a `0x008037e0` felé vezet. Ez cáfolja azt a konkrét feltevést, hogy a `0x00423300` maga a transition-gyárhívás, de nem zárja ki a későbbi virtuális bekötést. Az index negatív találatát nem használtam bizonyítékként.

**Nálunk.** A `Main.qml:2935`-`2953` a képeket és az átmenet-beállításokat adja át, arc-téglalapot nem. A `kenburns` a providerből két kivágást kap és ezeket animálja (`SlideshowView.qml:426-463`, `778-812`, `835-846`); a `kenburnsaoi` külön, középre igazított animációval `1.12`-ig nagyít (`847-857`). A kivágások képlete a `slideshow_pan_zoom.py`-ban van, részleteit és az eredetitől való eltéréseit a 4.4 szakasz rögzíti. A `movie/slideshow.py:242`-`252` külön film-renderelő út, középre vág. A diavetítési súgó (`src/picasapy/help/features/nezegetes.md:319`-`321`) csak az erősebb nagyítást írja.

**Következő felvehető irány.** Az 5. kör feloldotta a `CThumbUI+0x2bc` callback `+0x20` virtuális célját `0x00423300`-ra; a célobjektum pontos osztálya és a `oneup/transtype` gyárhoz vezető kapcsolata nyitott maradt. Következő lépésként a callback adatútját és a `0x008037e0` átmenetfogyasztóját kell feltárni. Ha a gyárkapcsolat bizonyított, a teljes képernyős út kezdő- és végképkockáját kell renderelt arcos és arc nélküli kontrollal mérni.

#### 4.2 5. kör: callback cél, átmenetindex és gyár (2026-10-16)

**Eredmény.** A `CThumbUI::MakeTimeline` `+0x90` slotján át elért virtuális callback célja a `0x00423300`. A `0x00c81f78` címen lévő RTTI-rekord ezt a `CThumbDB::vftable` `+0x20` metódusaként sorolja fel; az utasításai gyűjtemény- és adatbázismezőket használnak. A Ghidra-kimenet szerint a `0x005e8a70` a `Preferences/BigSlideshow2` értékét olvassa, és meghívja a `0x008037e0`-t. Ez a függvény a `oneup/timeline` és `oneup/transtype` csomópontokat olvassa, majd virtuális `+0x6c` és `+0x68` metódusokat hív. A `0x008037e0` és a `0x00771e60` átmenetgyár, illetve a `0x0076d900` illesztő közötti kapcsolat továbbra sincs bizonyítva.

**A `+0x2bc` callback célja.** A `0x005e8a70` a `CThumbUI` vtáblájának `+0x90` helyét hívja (`0x005e9494`). Az RTTI a `CThumbUI::vftable` bejegyzéseként a `0x00562cc0` thunkot adja. A thunk a `this+0x2bc` mezőből veszi a callback objektumot, majd annak vtbl `+0x20` bejegyzésére ugrik. A `CThumbUI` konstruktora (`0x005643e0`) az argumentumot a `+0x2bc` mezőbe menti; a hívó (`0x004039f0`) az argumentumot a szülő `+0x1034` mezőjéből tölti. A szülőobjektum konstruktora (`0x00415790`) a `0x00c81f78` vtáblacímet írja az objektumba (`0x004157fd`). Az RTTI-rekord neve `CThumbDB::vftable`, és a `+0x20` bejegyzés `0x00423300`. Ez a callbackút és a `0x005e8a70` által meghívott `0x008037e0` átmenetfogyasztó közötti adatkapcsolat nincs meg. Forrás: bináris `0x005e8a70`, `0x005e9494`, `0x00562cc0`, `0x005643e0`, `0x004039f0`, `0x00415790`, `0x004157fd`, `0x00c81f78`, `0x00423300`; RTTI: `CThumbUI::vftable`, `CThumbDB::vftable`.

**A beállításolvasó.** A `0x008037e0` a `oneup/timeline` és `oneup/transtype` csomópontokat olvassa, majd a node-ok virtuális `+0x6c` és `+0x68` metódusait használja (`0x00803a11`-`0x00803a30`). A függvénytörzsben nincs közvetlen `0x00771dc0` átmenetgyár-hívás. Ez nem zárja ki, hogy a beállítás egy másik későbbi vagy virtuális útba kerüljön. Forrás: bináris `0x008037e0`, `0x00803a11`-`0x00803a30`.

**A `kenburnsaoi` indexe és gyára.** A `0x00771a10` regisztráló a `CTransitions::kenburnsaoi` kulcsot és a `Pan and Zoom - face` feliratot a táblarekordhoz rendeli. A rekord címe `0x00d342c8`, a táblában a 20. helyen (`0x14`), első dwordje `0x0a`; a feliratmutató a rekord `+0x0c` mezőjében van (`0x00d342d4`). A `0x00771dc0` a kiválasztott rekordot a `0x00771e60` általános gyárhoz adja. A gyár `0x0a` ága a `0x0076ed30` konstruktort hívja; a konstruktor a `ytDoubleAffineAOITransitionNode` RTTI-vtábláit állítja be. Független ellenőrzésként a filmkészítő `0x00813330` képkockaútja a `this+0x28c` mezőt `0x14`-hez hasonlítja, az egyező ágon hívja a `0x00813c50` arcsegédet, majd a `0x00771dc0` gyárhívás elérhető ugyanebben a függvényben. Ez a filmkészítő arcágát igazolja, nem a teljes képernyős vetítést. Forrás: bináris `0x00771a10`, `0x00d34188`, `0x00d342c8`, `0x00d342d4`, `0x00771dc0`, `0x00771e60`, `0x0076ed30`, `0x00813330`, `0x00813c50`; RTTI: `ytDoubleAffineAOITransitionNode::vftable`.

**Az arcadat eredete.** A filmkészítő `0x00813c50` segédje a neki átadott rekordból és régióazonosítóból képez téglalapot. A vizsgált `0x00813330` és `0x00813c50` út nem olvassa közvetlenül sem a `.picasa.ini` `faces=` mezőjét, sem az `imagedata_facerect` adatbázismezőt. A különálló `0x00446610` olvasó az adatbázismezőt használja, de a teljes képernyős úttal való kapcsolata **NINCS MEG**. A teljes képernyős vetítés arcadatának forrása tehát **NINCS MEG**. Forrás: bináris `0x00813330`, `0x00813c50`, `0x00446610`; adatbázis-mező: `picasa-imagedata-rekord.md`, `facerect` `+0xdc0`.

| Réteg | Eredeti Picasa | Nálunk | Teendő |
|---|---|---|---|
| Átmenetazonosítás | `kenburnsaoi` index `0x14`; gyártípus `0x0a`; `ytDoubleAffineAOITransitionNode` konstruktor `0x0076ed30` | A sima `kenburns` két provider-kivágást animál; a `kenburnsaoi` külön, középre igazított animációval `1.12`-ig nagyít (`SlideshowView.qml:426-463`, `778-812`, `835-857`) | A teljes képernyős út beállításától az AOI-node-ig bizonyítani a kapcsolatot, utána arcrégióval renderelni |
| Arc nélküli eset | A teljes képernyős fallback **NINCS MEG**; a filmkészítő segéd `-1.0` sentinelje önmagában nem bizonyít vetítési viselkedést | A sima `kenburns` két véletlen kivágást animál, de a 4.4-ben rögzített képlete, a mag és a teljes képernyős bekötés nem azonosított teljes egyezésként | Renderelt arc nélküli kontrollal mérni az eredeti és a PicasaPy kezdő- és végkivágását |
| Súgó | A „Pan and Zoom - face” felirat arcot nevez meg | A `nezegetes.md:319-321` csak az erősebb nagyítást írja | Fejlesztés után a súgót a renderelt, bizonyított viselkedéshez igazítani |

**Bizonyítottsági fok és cáfoló kísérlet.** A `kenburnsaoi` indexe és gyára megerősített: az átmenetregisztráló és rekord mellett a filmkészítő képkockaútja külön is a `0x14` ágat köti az arcsegédhez és a gyárhoz. A teljes képernyős viselkedés **nyitott**, mert a `0x005e8a70` és `0x008037e0` útja nem ad bizonyított kapcsolatot ehhez a gyárhoz vagy az AOI-node-hoz. Cáfoló próbálkozásként a `CThumbUI +0x90` slotot, a `+0x2bc` thunkt, a konstruktor által beállított vtáblát és a `0x008037e0` beállításolvasóját vetettem össze a transition-gyár hívóival. A vizsgált közvetlen hívásláncokban nem jelent meg összekötő él. Ellenőrzésként a negatív eredményt nem tekintettem cáfolatnak: a thunk célja pozitívan feloldódott `0x00423300`-ra, de a virtuális vagy későbbi átmenetbekötést ez nem zárja ki. Az index negatív találatát sem használtam negatív leletként.

**Nyitott pontok és következő irány.**

- Válasz (2026-10-18, lásd 4.5): a `0x009c2fc0` nem beszúró, hanem kereső; a beszúró és a csomópont-osztály vtáblája NINCS MEG.
- `Ghidra-kör kell: 0x00812470 - honnan töltődik fel a this+0x48 időzített sáv, és a rekord +0x8 régióazonosítója faces= vagy imagedata_facerect adathoz kötött-e? [blokkoló]`
- A teljes képernyős vetítésből renderelt arcos és arc nélküli képkockapár, a középpont és az arc nélküli fallback mérésével: **NINCS MEG**.

Következő felvehető munka: célzottan feloldani a `0x00423300` callback adatútját és a `0x008037e0` `oneup/transtype` fogyasztóját; ha ezek a gyárhoz vezetnek, utána renderelt arcos és arc nélküli képkockával ellenőrizni a viselkedést. Külön kutatási jegyet ez a kör nem javasol, mert a megmaradt kérdések ugyanannak a #4856 átmenetútjának részei.

#### 4.3 6. kör: a választólista, a „Pan and Zoom” célterülete és a `kenburnsaoi` (2026-10-17)

**Kérdés:** az eredeti diavetítés átmenet-választójának hét eleme közül a „Pan and Zoom” (`kenburns`) a nagyítás célterületét arcadatból számolja-e, vagy anélkül? Létezik-e az arc-változat (`kenburnsaoi`) az eredetiben, el van-e rejtve a választóból, és ha létezik, mit csinál?

**Röviden.** (1) A választó két külön listából épül: a diavetítés hét elemet mutat (`0x00d342e8`), a filmkészítő tízet (`0x00d345e4`). Az arc-változat a filmben választható, a diavetítésben nincs a listában, és a mentett érték sem tudja elérni. (2) A „Pan and Zoom” célterületét nem arcadat adja: a kivágás helyét a `rand()` véletlen törtjei döntik el, az útban nincs arc-mező. (3) A `kenburnsaoi` a filmben arcjelöltekből számol célt; érvényes arcjelölt hiányában a sima Pan and Zoom véletlen illesztése marad. Az arcjelölt forrása (`faces=`?) ebben a körben nem igazolt.

**Bizonyítottsági fok.**
- Választólista (7 és 10 elem, a mentett érték 0-6 tartománya): **megerősített**. (A) A diavetítés lista-feltöltő ciklusa (`0x0075d9a0`-`0x0075db78`, `cmp eax, 0x1c`) a 7 elemű tömbön fut. (B) A Colab-felvétel (job-182) ugyanezt a hét elemet mutatta, ugyanebben a sorrendben. A diavetítés-sáv és a 7 elemű lista összerendelése a Colab-egyezésen alapul (feltételezés, nem közvetlen kódbizonyíték).
- „Pan and Zoom” célterülete arcmentes (szerkesztő-előnézeti út): **megerősített**. (A) Utasításszintű lánc: gyár (csoport 1) → `0x0076e100` → `0x0076e4e0` → vtábla `+0x30` (`0x009e08b0`) → illesztés `0x0076d900`. (B) Az arc-mezőket (`+0x4b0…+0x4bc`) a kenburns-konstruktor (`0x0076e100`) nem írja; az arc-csomópont (`0x0076ed30`) csak a 0x0a csoport ágából hívódik. A B-rekord a `0x00760d50` lokális kitöltéséből származik, amely az `editpanel/previewclip` objektum `vtbl+0x30` kimenetét használja (a mezőleképezés részben követve).
- A véletlen pozíció: **feltételes**. A `0x00c08221` azonosítása erős (MSVC LCG), a hívási helyek megvannak, de renderelt képkocka-sorozat nincs, és a mag (`srand`) nem igazolt.
- Az arc-változat léte és viselkedése a filmben: **megerősített** a regisztrálóban, a rekordban, a gyárban és az arc-csomópontban; **nyitott** az arcjelölt forrása.
- A teljes képernyős diavetítés futásidejű útja: **nyitott** (lásd 4.2, `0x00423300`).

**Bizonyíték.**

| állítás | forrás |
|---|---|
| 22 rekord, 16 bájt: `dword0` = csoport, `dword1` = irány. Az 1. rekord `kenburns` (csoport 1), a 20. `kenburnsaoi` (csoport 0x0a) | bináris `0x00d34188` (+16·i), `0x00d34198`, `0x00d342c8` |
| feliratok: „Pan and Zoom” (`0x00cb2c84`), „Pan and Zoom - face” (`0x00cb2a90`); a `Picasa3i18n.dll` `stringres id="CTransitions::kenburnsaoi"` bejegyzése ugyanezt adja | bináris `0x00cb2a90`, `0x00cb2f00`; `Picasa3i18n.dll` |
| regisztráló: minden kulcsot szűrés nélkül vesz fel; a kenburnsaoi a `0x00771d46`-nál | bináris `0x00771a10`, `0x00771d46` |
| rekord-lekérő: `0xd34188 + 16·i`, i ≥ 22 esetén 0 | bináris `0x00771d8e`-`0x00771d98` |
| diavetítés-lista: `[0, 1, 2, 6, 9, 12, 15]` (7 dword), ciklus `eax += 4`, `cmp eax, 0x1c` | bináris `0x00d342e8`; `0x0075d9a0`, `0x0075db71`-`0x0075db78` |
| filmkészítő-lista: `[0, 1, 2, 3, 4, 6, 9, 12, 20, 21]` (10 dword), ciklus `cmp ebp, 0xa` | bináris `0x00d345e4`; `0x00613c2d`, `0x00613dea`-`0x00613df1` |
| diavetítés mentett értéke: kulcs `ThumbUISlideShow::transition`, szekció `Preferences`; a kiolvasás előtti kezdőérték 2 (Dissolve); az érték 0-6-ra szorul | bináris `0x00cb22b0`, `0x00c7eafc`, `0x0075d84f`, `0x0075d865`-`0x0075d872` |
| a kiválasztott rekord csoportja és iránya → `0x00760b00` → `0x00760d50` (a `kind` a csoport) → gyár | bináris `0x0075d888`, `0x0075d8a3`, `0x00760ccc`, `0x00760eac` |
| csoport 1 → `0x0076e100` (vtábla `0x00cb313c`); csoport 0x0a → `0x0076ed30` (vtábla `0x00cb320c`) | bináris `0x00771e97`, `0x00772286`, `0x0076e12e`, `0x0076ed4c` |
| célszámítás `0x0076e4e0`; forráshatár: vtábla `+0x30` = `0x009e08b0`; illesztés `0x0076d900` | bináris `0x0076e4e0` (`0x0076e512`, `0x0076e551`); `0x00cb313c` + `0x30` |
| `rand()` = MSVC LCG: `x = x·214013 + 2531011`, kimenet `(x >> 16) & 0x7fff` | bináris `0x00c08221`-`0x00c08242` |
| véletlen törtek: `(rand + 0x3f8000) << 8` float-bitekként, majd 1,0 kivonása → [0, 1); 4 hívás az illesztésben | bináris `0x0076db61`, `0x0076db7c`, `0x0076dbe0`, `0x0076dbfb` |
| a kenburns-konstruktor két rand-hívása | bináris `0x0076e16a`, `0x0076e1a4` |
| arc-csomópont: előbb meghívja a kenburns-konstruktort, majd csak akkor írja felül az arc-célt (`0x0076ee50`), ha az arcjelölt nem tartalmaz `-1.0` sentinelt | bináris `0x0076ed41`, `0x0076ed5c`-`0x0076ed6e`, `0x0076edcd`, `0x0076ee33` |
| `0x0076ee50` csak `0x0076ed30`-ból hívódik; `0x0076ed30` csak a gyár 0x0a ágából | xref: `0x0076ee50` ← `0x0076ed30` ← `0x00771e60` (`0x00772286`) |
| film arc-ága: a `this+0x28c == 0x14` ágon `0x00813c50` az azonosítóhoz tartozó téglalapot adja; az azonosító forrása nyitott | bináris `0x00813330`, `0x00813c50` (4.1-4.2) |

**A két független út.** (A) Utasítás-lánc: gyár → konstruktor → illesztés, a `rand()` hívásokkal. (B) Adat- és hívási gráf: a két tábla, a választólista-ciklusok, a preview-rekord forrása és az arc-ág kizárólagossága. A két út a választólistában és az arc-ág kizárólagosságában egyezik. A véletlen mechanizmust az (A) út adja; a (B) út ettől független.

**Cáfoló kísérlet.**
1. „A diavetítés listája erőforrásból épül, a 7 elem csak a binárisban látszik." Cáfolat nem sikerült: a szűrést a kódban lévő ciklus végzi (`cmp eax, 0x1c`), a felirat-erőforrás mind a 22 kulcsot tartalmazza, és a Colab-felvétel is hét elemet mutatott.
2. „A mentett érték a 7 elemen túlra is mutathat." Cáfolva: a `cmp eax, 6` / `ja` a 0-6 tartományra szorít.
3. „A kenburns B-rekordja (célméret) arcadatból jön." Nem cáfolható teljesen ebben a körben: a B-mezők leképezése részben követett. A forrás a previewclip befoglaló téglalapja (`vtbl+0x30`), nem arc.
4. „A pásztázás nem véletlen, hanem konstans." Cáfolva: a `0x0076db5f`-`0x0076dbfb` szakaszban a rand-törtek adják a kivágás helyét; a `-1.0` sentinel csak az arc-jelöltnél jelenik meg.
5. „A kenburnsaoi a teljes képernyős úton mégis elérhető." Nem zárható ki: a teljes képernyős út (`0x005e8a70` → `0x00423300`) nyitott (4.2). Ez a kör egyetlen gyenge pontja.

**A jegy „Kész, ha” pontjai.**
- ⛔ Arcot tartalmazó dián a nagyítás középpontja az arc felé mozdul (renderelt): **nem igazolható** az eredetiben. A diavetítés választójában nincs arc-változat (`0x00d342e8`); a filmben az arcforrás nyitott; render nincs.
- ⛔ Arc nélküli dián a viselkedés változatlan: a jelenlegi `kenburns` már két véletlen kivágást animál, de a 4.4-ben dokumentált eredeti méret- és eltolásképletet, seedet és teljes képernyős bekötést nem reprodukálja igazoltan. Azonos eredményt renderelt kontrollal kell mérni.
- ⛔ A súgó igazodik: függ attól, hogy a diavetítés kap-e arc-változatot (termékdöntés).

**Nyitott.**
- Renderelt bizonyíték: két egymást követő Pan and Zoom futás képkockái (véletlen-e a pásztázás, és mennyire determinisztikus a sorozat): **NINCS MEG**. Ehhez Colab-felvétel kell.
- A `0x0076d900` képletét, a középre igazítás ágát és a használt konstansokat a következő, 4.4 szakasz binárisból rögzíti. A fit egészre kerekítésének aktív x87 módja továbbra is **NINCS MEG**.
- A teljes `.text` pásztázása 10 hívóhelyet talált a `0x00c08214` belső seed-beállítóhoz; hogy ezek közül melyik fut le a slideshow előtt, és mi a CRT-mag, **NINCS MEG** (lásd 4.4).
- A film arcjelölt-forrása (`0x00813c50` azonosító → `faces=`): nyitott (4.2).

**Módosított fájl:** `docs/specs/picasa-create-features.md` (új 4.3 szakasz).

#### 4.4 8. kör: a véletlen pásztázás képlete és magja (#5225, 2026-10-18; a 7. kör helyesbítése)

**Következtetés.** A `0x0076d900` két, képarányra illesztett alaptéglalapból indul, azokat feltételesen a forrás jobb és alsó széle felé igazítja, majd két véletlen méretű és helyzetű kivágást készít. Nincs középre igazító ág az illesztőben. A `0x0076d6f0` mindkét kivágást a saját téglalapközepe körül méretezi; a `0x0076d7e0` az eltolást a forráshatárok közé szorítja, a méret megtartásával. A nagyobb méretű jelölt kapja az első két `_rand()`-törtből készült eltolást, a kisebb a második kettőből.

**Képlet.** A `0x009b4aa0` a forrás és a célterület arányához illesztett `(0,0,w,h)` alaptéglalapot készít. A `0x0076d900` ebből két másolatot hoz létre. Feltételesen az egyik téglalapot a jobb, illetve az alsó forrásszélhez tolja (`0x0076d9a0`-`0x0076dac7`); a két `0x0076d790` hívás teljes téglalapokat cserélhet. Így a méretezés előtti középpontok különbözhetnek: `C₁=(cx₁,cy₁)` és `C₂=(cx₂,cy₂)`. Legyen a forráshatár `[L,T,R,B]`, `W=R-L`, `H=B-T`, az alaptéglalap mérete pedig `w×h`.

A `0x009b4aa0` méretillesztése a `0x00cf4160` binary64 `0.499` és a `0x00cf41e0` binary64 `0.00001` konstansokat is használja. A skálát a két arány közül a kisebb adja, az eredményt `fistp` írja egész méretbe. Az aktív x87 kerekítési módot nem állapítottam meg, ezért a félértékek egészre kerekítésének részlete **NINCS MEG**.

A helyi LCG két törtje `u₁,u₂ ∈ {0/32768,…,32767/32768}`; a kód újrahúzza őket, amíg `|u₁-u₂| ≥ 0,5`. A nagyobb skálájú jelölt `sₙ=0,75+0,2·max(u₁,u₂)`, a kisebb `sₖ=0,75+0,2·min(u₁,u₂)`. A `0x0076db4b`-`0x0076db5f` a nagyobb méretű téglalapot az első eltolási csoporthoz választja. Legyen a kiválasztott téglalapok méretezés előtti közepe rendre `Cₙ` és `Cₖ`, a négy `_rand()`-tört pedig hívási sorrendben `ρ₀…ρ₃`, ahol `ρᵢ=Rᵢ/32768`:

| jelölt | célméret | kért bal felső sarok a `0x0076d7e0` előtt |
|---|---|---|
| nagyobb | `wₙ=w·sₙ`, `hₙ=h·sₙ` | `xₙ=cxₙ-wₙ/2+W·(0,2ρ₁-0,1)`, `yₙ=cyₙ-hₙ/2+H·(0,2ρ₀-0,1)` |
| kisebb | `wₖ=w·sₖ`, `hₖ=h·sₖ` | `xₖ=cxₖ-wₖ/2+W·(0,2ρ₃-0,1)`, `yₖ=cyₖ-hₖ/2-H·0,2ρ₂` |

A `Rᵢ` a `0x00c08221` `_rand()` kimenete. A kisebb y-eltolása aszimmetrikus: a bináris a `0,2ρ₂` értéket negálja, `0,1` levonása nincs benne (`0x0076dc37`-`0x0076dc5f`). A `0x0076d7e0` határolása `x'=min(max(x,L),R-w)`, `y'=min(max(y,T),B-h)` alakban írható le; az eltolást azonosan adja hozzá a téglalap szemközti éleihez, így a méret változatlan.

A tömör `wₙ=w·sₙ`, `hₙ=h·sₙ` jelölés a `0x0076d6f0` középpont körüli műveletét fejezi ki. A függvény külön számolja a bemeneti szélesség és magasság felét, mindkettőt megszorozza ugyanazzal a mérettényezővel, majd a négy új élt 32 bites floatként írja vissza (`0x0076d712`-`0x0076d785`). Az alaptéglalap egész mérete a korábbi `0x009b4aa0` `fistp` lépéseiből jön; annak x87 kerekítési módja nyitott.

| konstanscím | bináris érték és típus | szerep |
|---|---|---|
| `0x00cf4748` | `0.2`, double, bájtok `9a9999999999c93f` | méret- és eltolásszorzó |
| `0x00c7dd30` | `0.1`, double, bájtok `9a9999999999b93f` | nagyobb x/y és kisebb x képletének tagja |
| `0x00cf3b08` | `0.75`, double, bájtok `000000000000e83f` | alap méretszorzó |
| `0x00c7dafc` | `0.5`, float, bájtok `0000003f` | újrahúzási küszöb |
| `0x00cf4160` | `0.499`, double, bájtok `560e2db29defdf3f` | az alap fit méretarányához |
| `0x00cf41e0` | `0.00001`, double, bájtok `f168e388b5f8e43e` | egész méretre alakítás előtt |

**A tört és a konstruktor magja.** A `0x00c08221` `_rand()` MSVC LCG-je: `state=(state·0x343fd+0x269ec3) mod 2^32`, kimenete `(state>>16)&0x7fff`. A kód a `(R+0x3f8000)<<8` bitmintát floatként `1+R/32768` értelmezéssé alakítja, majd kivonja az 1-et. A helyi LCG ugyanezt az állapotléptetést használja. A két előzetes `0x0076d790` hívás egy-egy állapotlépése megelőzi az `u₁,u₂` húzását. A `0x0076e100` konstruktor a `0x0076e16a` visszatérési értékét a `this+0x434`, a `0x0076e1a4` értékét a `this+0x458` mezőbe írja. A `0x0076e4e0` a `this+0x438` tömböt adja át; a helyi LCG állapota ennek `+0x20` mezője, vagyis a konstruktor által beállított `this+0x458`.

**Teljes .text pásztázás.** A `paszta.py` kapuján át a teljes .text (`0x00401000`, méret `0x0083e160`, záró cím `0x00c3f160`) 2 884 879 utasítást dolgozott fel. A belső srand-wrapper (`0x00c08214`) 10 közvetlen hívóhelye: `0x00423a6c`, `0x00565cc5`, `0x006804c4`, `0x0071d993`, `0x0071e23b`, `0x0085b76d`, `0x0087cb85`, `0x0088fed7`, `0x009180df`, `0x009902b8`. Mind a 10 találat közvetlen hívás; további hivatkozás és importált srand nincs. A slideshow út futás előtti konkrét seedelő hívása és a CRT-állapot számszerű értéke **NINCS MEG**.

**Bizonyítottsági fok: feltételes.** (A) A `0x0076d900` utasításszintű adatfolyama adja a méret- és pozícióképleteket; a `0x0076d6f0`, `0x0076d790` és `0x0076d7e0` külön diszasszemblálása az egyes segédek műveletét igazolja. (B) A Ghidra C-kimenet és a hívási lánc (`0x0076e100` -> `0x0076e4e0` -> `0x0076d900`) ellenőrzi a két helyi tört újrahúzását, a két méretezést és a négy `_rand()`-hívást; a konstansok típusát a PE nyers bájtjai igazolják. A két út a méretválasztásban és a hívássorrendben egyezik. A pozícióképletekhez nincs független képkockamérés; a BigSlideshow2 átmenetútja, a futás előtti CRT-mag és a renderelt eredmény nyitott.

**Cáfoló kísérlet.** Az előző 4.4-változat közös középpontot használt, a kisebb y-eltolásra pedig `H·(0,2ρ₂-0,1)`-et írt. Ezt a két állítást a nyers x87-adatfolyam cáfolta. A `0x0076d900` külön igazítja a két alap-téglalap élét, a `0x0076d6f0` mindegyik saját középpontját veszi; a `0x0076dc37`-`0x0076dc5f` blokk a kisebb csoport y-értékéből csak a `0,2ρ₂` szorzatot képzi és negálja. A független újralevezetés ugyanezt adta: a `ρ₀,ρ₁` csoport a nagyobb, a `ρ₂,ρ₃` a kisebb skálájú téglalaphoz tartozik. A korábbi közös középpont és kisebb y-képlet hibás volt.

**#5225 „Kész, ha” pontjai.**

- ✅ Képlet címekkel: a két méretszorzó, mind a négy eltolási tag, a törtleképezés és a határkorlátozás a `0x0076d900`, `0x0076d6f0`, `0x0076d7e0`, `0x00c08221` és konstanscímek alapján szerepel.
- ✅ Középre igazítás: az illesztőben nincs középre igazító ág. A `0x0076d9a0`-`0x0076dac7` feltételes élre igazítást végez, a `0x0076d6f0` a saját téglalapközép körül méretez.
- ⛔ Futás előtti számszerű CRT-mag és két egymást követő renderelt futás: **NINCS MEG**. A job-184/185 felvételek nem találhatók a helyi meroadat.tar tagjai között; pontos eredeti képkockamérés kell.
- ✅/⛔ srand: a teljes binárisban 10 közvetlen hívóhely van. Hogy ezek közül melyik seedeli a slideshow CRT-állapotát a futás előtt, és mi a mag értéke, **NINCS MEG**.
- ⛔ Teljes képernyős használat: a `0x005e8a70` hívja a `0x008037e0`-t, de a `oneup/transtype` virtuális céljaitól a `0x00771e60` gyárhoz vagy a `0x0076d900` illesztőhöz vezető adatút nincs bizonyítva.

**Nyitott.** A runtime seedelő hívás és a CRT-állapot számszerű értéke; a job-184/185 képkockasora; továbbá a BigSlideshow2 `oneup/transtype` virtuális célfüggvényei és az átmenetgyárhoz vezető adatút. A dekompilált `0x005e8a70` a `0x008037e0` hívását mutatja, a virtuális célok és a híd nincsenek feloldva. Célzott Ghidra-kör (pontosítva a 4.5 szerint): `0x009c2fc0` és az `oneup/transtype` csomópont vtáblája, a `+0x68` és `+0x6c` virtuális célok feloldásával. A képletből önálló kutatási jegy nem következik.

**Helyi viszonyítás.** A QML providerből két kivágást kap (`SlideshowView.qml:426-463`, `778-812`); a számítást a `slideshow_pan_zoom.py` végzi. A jelenlegi kód közös középpontú alaptéglalapot használ, a méreteket a törtek eredeti sorrendjéhez rendeli, és egyetlen LCG-forrásból veszi a két mérettörtet, a négy eltolási törtet, majd a kimeneti sorrend felcserélésének döntését (`slideshow_pan_zoom.py:56-123`, `126-138`). Az eredeti bináris élre igazít, a nagyobb méretű jelölthöz rendeli az első két offsetet, a négy eltolási értéket a CRT `_rand()` adja, és nincs plusz helyi LCG-húzás a végső felcseréléshez. A QML kétkivágásos útjának és a binárisnak pontos megfelelése méréssel nincs igazolva. A `0x0076d900` teljes képernyős használata a 4.2 szerint nyitott.

#### 4.5 9. kör: az `oneup/timeline` és `oneup/transtype` csomópontok virtuális hívásai (#5225, 2026-10-18)

**Kérdés.** A 4.3 nyitott sora: az `oneup/transtype` csomópontok +0x68 és +0x6c célfüggvényei, és az adatútjuk a `0x00771e60` gyárig vagy a `0x0076d900` illesztőig.

**Forrás.** A `0x008037e0` helyi diszasszemblálása (719 bájt, `annot_disasm.py`), a `0x009c2fc0` diszasszemblálása (134 bájt), és a bináris-index `string_xrefs` táblája. A dekompilátum (C) a `0x009c2fc0` hívásából kihagyja az útvonal-argumentumot (EDX), ezért a C-ből a csomópontok nem olvashatók ki; a sorrend a diszasszemblálásból jön.

**A hívott csomópontok (megerősített).**
- A `0x009c2fc0` útvonal-kereső: EDX-ben C-sztring (csomópont-útvonal), a `[0x00d67914]` gyökér `+0xc` hash-táblájában keres (`0x00409df0` a hash-index, `0x006f9890` a kulcs-összevetés), és 0-t ad, ha nincs találat.
- `EDX = 0x00cbd528` („oneup/timeline", `0x00803a11`), `EDX = 0x00cbd54c` („oneup/transtype", `0x00803a30`). A `oneup/transtype` sztringet a `string_xrefs` szerint csak a `0x008037e0` használja.

**A virtuális hívások sorrendje (megerősített, diszasszembly).** Az ágat a `cmp byte ptr [esp+0x10], bl` (`0x00803a03`) dönti el; a függvényben a BL nulla (az `ebx` a null-ellenőrzésekre van használva), tehát az ág a jelző nullaságától függ:
- jelző = 0: timeline `+0x68` (`0x00803a64`), majd transtype `+0x6c` (`0x00803a83`);
- jelző ≠ 0: timeline `+0x6c` (`0x00803a26`), majd transtype `+0x68` (`0x00803a83`).

Mindkét hívás előtt: a gyökér nem nulla (`cmp dword ptr [0xd67914], ebx`), és a csomópont nem nulla. A C-kód (`unaff_BL == '\0'`) ugyanezt a sorrendet adja. A 4.3 „0x00803a11-0x00803a30" tartománya csak a timeline-hívást fedi; a transtype-olvasás hívása a `0x00803a30`-tól a `0x00803a83`-ig tart. Ez a helyesbítés.

**Az adatút: NINCS MEG.**
- Közvetlen él a `0x00771e60` vagy a `0x0076d900` felé nincs: a `0x008037e0` törzsében egyik cím sem fordul elő, és a hívottak listájában sincs.
- A virtuális célok (`+0x68`, `+0x6c`) a csomópont-osztály vtáblájából jönnének. Az osztály nincs azonosítva: a `0x008037e0` nem írja a vtáblát, a csomópontok beszúrója pedig nincs ebben a körben. Jelölt osztályok, nem igazolva: `ITransitionNode` (`0x00cb2f38`), `CTransitionInfo` (`0x00cbdca0`), `CTransTimeline` (`0x00cbdcc4`).

**Két út.** A: a `0x008037e0` diszasszembly hívásai. B: az adatkonstans-út: a két literál címe (`0x00cbd528`, `0x00cbd54c`) a diszasszemblálásból, és a `string_xrefs` táblából. Egyezik.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a `0x008037e0` közvetlenül a gyárat vagy az illesztőt hívja: a diszasszemblált törzsben a `0x00771e60` és a `0x0076d900` egyike sem szerepel (0 találat). Ez a közvetlen élt cáfolja; a virtuális úton át nem zárja ki.

**Válasz [részben; 2026-10-18, dekompilált C]: a kérdés előfeltétele téves.** A `0x009c2fc0` (134 bájt, 1604 hívóval) **nem beszúró**, hanem útvonal-kereső: a `[DAT_00d67914]+0xc` hash-táblát járja be (`FUN_00409df0` a hash-index, `FUN_006f9890` a kulcs-összevetés), és a találat `puVar5[1]` mezőjét adja vissza, különben `0`. Nincs benne vtábla-hívás, ezért a `+0x68`/`+0x6c` cél a `0x009c2fc0`-ból nem olvasható ki. **A beszúró NINCS MEG**: a `DAT_00d67914` 1712 hivatkozása közül (`find_data_refs.py`) a `[root+0xc]` írója nincs azonosítva; a vtábla és a célok ezzel együtt nyitottak. Következő lépés: a `[root+0xc]` íróinak pásztázása (`paszta.py`, memóriakapuval), majd a beszúró konstruktorának vtábla-olvasata. A `0x008037e0` hívási sorrendje (4.5) ettől független és változatlan.

**Bizonyítottsági fok:** a hívási szerkezet megerősített; a célok és az adatút NINCS MEG.

**Fejlesztési következmény:** nincs. A 4.4 képlete (`0x0076d900`) ezzel nem változik.

#### 4.6 11. kör: a 4.4 képlet soronkénti újraolvasása, a srand-hívók és a mért eltérés (#5225, 2026-10-19)

**Kérdés.** Megáll-e a 4.4 szerkezete a `0x0076d900` utasításszintű olvasatával (a segédek külön, a jelölt-alaptéglalapok felépítése, van-e középre igazító ág)? Melyik `srand`-hely seedeli a diavetítést? Hol tér el a `src/picasapy/app/slideshow_pan_zoom.py` a bináris képlettől, méréssel?

**Forrás.** `annot_disasm.py` a `Picasa3.exe`-n: `0x0076d900` (1039 bájt), `0x0076d6f0` (156), `0x0076d790` (79), `0x0076d7e0` (273), `0x009b4aa0` (184), `0x00c08221` (34). A srand-hívók tulajdonosa a bináris-index `functions` és `string_xrefs` tábláiból.

**Megerősített szerkezet (utasításszint, címekkel).**

- `_rand` (`0x00c08221`): `state = state·0x343fd + 0x269ec3`, a kimenet `(state >> 16) & 0x7fff` (`0x00c08229`-`0x00c0823d`).
- `0x0076d6f0(téglalap, s)`: a téglalapot a saját közepe (`cx`, `cy`) körül méretezi, `x0 = cx - s·W/2`, `x1 = cx + s·W/2`, `y0 = cy - s·H/2`, `y1 = cy + s·H/2`. Az `s` a verem `[esp+0x28]` argumentuma (`0x0076d733`-`0x0076d785`).
- `0x0076d790(struktúra)`: a helyi LCG állapota a `[+0x20]` mezőben van, és minden hívás lépteti (`0x0076d790`-`0x0076d79f`). Ha az új állapot 16. bitje (`0x10000`) 1, a két téglalap (`A` a `+0x00`-nál, `B` a `+0x10`-nél) felcserélődik (`0x0076d7a8`-`0x0076d7da`).
- `0x0076d7e0(téglalap, eltolás)`: az eltolást a határokhoz szorítja: `dx' = clamp(dx, -x0, [esi+8] - x1)`, `dy' = clamp(dy, -y0, [esi+0xc] - y1)`. A bal és a felső határ literál 0, a jobb és az alsó az `esi` forrásrekord egész mezője. Utána eltolja a téglalapot (`0x0076d81f`-`0x0076d8ea`).
- `0x0076d900` menete:
  1. `0x009b4aa0` két egész alaptéglalapot ad, `(0,0,w,h)` alakban. A kerekítés `fistp`, a bemenő arány `(forrás + 0,499) / célméret`, a végső hozzáadás `0,00001` (`0x009b4acc`-`0x009b4b57`).
  2. `A` és `B` kezdetben egyforma. `B`-t a forrás szélesebb, illetve magasabb oldala felé tolja: jobbra `srcW - w`-vel, ha `srcW > w`; lefelé `srcH - h`-val, ha `srcH > h` (`0x0076d9dc`-`0x0076da24`, `0x0076da72`-`0x0076dac5`).
  3. Két `0x0076d790` hívás (`0x0076da2c`, `0x0076dac7`) cserélheti `A`-t és `B`-t, a helyi LCG-ből.
  4. `u` és `v` a helyi LCG-ből jön. Újrahúzás, amíg `|u - v| >= 0,5` (`0x0076dc82`-`0x0076dd05`; a küszöb `0x00c7dafc` = 0,5; az abszolútérték a `0x0049f5c0` `fabs`, 26 bájt).
  5. A két jelölt skálája `s_u = 0,75 + 0,2·u` és `s_v = 0,75 + 0,2·v`, mindkettőt a saját közepe körül (`0x0076daf9`-`0x0076db3e`). A nagyobb skálájú jelölt kapja az első eltolási csoportot (`0x0076db45`-`0x0076db5f`).
  6. Négy `_rand()` (`0x0076db61`, `0x0076db7c`, `0x0076dbe0`, `0x0076dbfb`) adja a `ρ0…ρ3` törteket. A nagyobb jelölt: `x = cx - w_n/2 + W·(0,2ρ1 - 0,1)`, `y = cy - h_n/2 + H·(0,2ρ0 - 0,1)`. A kisebb: `x = cx - w_k/2 + W·(0,2ρ3 - 0,1)`, `y = cy - h_k/2 - H·0,2ρ2` (`0x0076dc37`-`0x0076dc5f`).
  7. Mindkét jelöltre `0x0076d7e0` szorítás (`0x0076dc63`, `0x0076dc6e`).

**Középre igazító ág: nincs.** A `0x0076d900`, `0x0076d6f0` és `0x0076d7e0` törzsében nincs olyan ág, amely a forrás közepét írná a kivágásba. A kivágás közepe a jelölt saját alaptéglalapjából jön. Középre esés csak a törtek egy értékénél áll elő: a nagyobb jelöltnél `ρ1 = 0,5` az x-re és `ρ0 = 0,5` az y-ra, a kisebbnél `ρ3 = 0,5` az x-re és `ρ2 = 0` az y-ra. Ez nem ág, hanem a véletlen törtek értéke.

**Srand-hívók (a tíz hely tulajdonosa az index szerint).**

| hívóhely | függvény | sztring-nyom |
|---|---|---|
| `0x00423a6c` | `FUN_00423780` | album-kupac mag (`srand(rés ^ 0x133475)`, lásd `pmp-database.md`) |
| `0x00565cc5` | `FUN_00565920` | UI-panel (`panelroot`, `HLISTDIV`) |
| `0x006804c4` | `FUN_00680370` | feltöltés (`Uploads\Pending\`) |
| `0x0071d993` | `FUN_0071d940` | nincs; hívója `FUN_0071c380` |
| `0x0071e23b` | `FUN_0071e120` | nincs; hívója `FUN_0071c380` |
| `0x0085b76d` | `FUN_0085b730` | azonosító-formátum (`%I64x`, `%x%x%x%x-`) |
| `0x0087cb85` | `FUN_0087cb70` | hívója a kollázs-panel (`collagepanel/cnode_`) |
| `0x0088fed7` | `FUN_0088fcf0` | a kollázs keverése (1.9, `VeletlenKeveres`) |
| `0x009180df` | `FUN_00917f50` | online-állapot |
| `0x009902b8` | `FUN_00990000` | összeomlás-jelentés, regisztrációs kulcs |

Diavetítéshez egyik sem tartozik bizonyítottan. A `0x0071d993` és a `0x0071e23b` a `FUN_0071c380`-ból hívódik; ez a diavetítés indításának jelölt útja. Az index a vtábla-hívásokat nem látja, ezért az „nincs más hívó” nem negatív bizonyíték.

**Korábbi mért eltérés (történeti adat; a #5351 előtti kód, nem a jelenlegi megvalósítás).** Azonos törtekkel, csere nélkül: forrás 1000×500, nézet 1024×768, `u = 0,9`, `v = 0,2`, `ρ = (0,5; 0,25; 0,75; 0,1)`. Az alaptéglalap mindkét oldalon `666,67 × 500` (lebegőpontos, a bináris egész alapja nélkül). A régi `slideshow_pan_zoom.py` kimenete és a fenti képlet (`x`, `y` a határra szorítás után):

| jelölt | `slideshow_pan_zoom.py` (x, y, w, h) | bináris 4.6 képlet (x, y, w, h) |
|---|---|---|
| nagyobb | 140,00 · 17,50 · 620,00 · 465,00 | 0,00 · 17,50 · 620,00 · 465,00 |
| kisebb | 156,67 · 0,00 · 526,67 · 395,00 | 323,33 · 0,00 · 526,67 · 395,00 |

Az eltérés az x-koordinátában volt: a régi Python-kód mindkét jelöltet a forrás közepére (`cx = 500`) építette, a bináris a saját alaptéglalapjának közepére (`A`: `333,33`; `B`: `(srcW + w)/2 = 666,67`). A méretek és az y-koordináták egyeztek.

**A #5351 előtti kód eltérései (történeti leírás, nem a jelenlegi megvalósítás).**

- A Python egyetlen közös középponttal dolgozik. A bináris a jelölt saját alaptéglalapjának közepét használja, a `B` alaptéglalapot pedig a forrás jobb, illetve alsó széléhez tolja.
- A méretsorrendet a Python az első húzásból adja (`meret_a` = `u`); a bináris a nagyobb skálát a `ρ0`, `ρ1` csoporthoz rendeli. A két sorrend csak akkor egyezik, ha `u > v`.
- A cserék: a bináris két LCG-csere a skálázás előtt történik, és mindkettő húz a helyi LCG-ből. A Python egyetlen húzással dönt a visszatérési sorrendről, a skálázás után. A 4.4 „helyi viszonyítás” bekezdésében szereplő „nincs plusz húzás” ezért a bináris két csere-húzását nem említi.
- Véletlenforrás: a bináris `u`, `v` és a csere a helyi LCG-ből jön, a `ρ`-k a CRT `_rand`-ból. A Python egyetlen generátort használ.
- Alap: a bináris egész (`fistp`, `+0,499`), a Python lebegőpontos.
- Mag: a régi Python-út `random.getrandbits(32)`-t használt; a bináris mag NINCS MEG.

**Jelenlegi kód kontrollmérése (#5351; 18. kör).** Forrás 1000×500, nézet 1024×768, csere nélkül; `u=29491/32768`, `v=6554/32768`, `ρ=(16384,8192,24576,3277)/32768`. A bináris-alap egész mérete 667×500. A `pan_zoom_rectangles(...)` mért kimenete:

| jelölt | jelenlegi kód (x, y, w, h) |
|---|---|
| A | 0,00 · 17,50 · 620,31 · 465,00 |
| B | 323,04 · 0,00 · 526,93 · 395,00 |

Ez a kód kontrollmérése, nem eredeti Picasa-renderkocka; a képlet és a kód közös forrású levezetése miatt önmagában nem független bináris-megerősítés. A bitpontos futásidejű véletlenszám-sorozat és az alkalmazandó `+0x37c` ág továbbra sincs meg.

**Helyi viszonyítás helyesbítése.** A `SlideshowView.qml:752-761` a `slide` képelem sorai, nem nagyítás. A fájlban nincs `1,08`. Az 1,0 → 1,12-es nagyítás a `kenburnsaoi` (`SlideshowView.qml:847-857`): ez középre igazított és nem véletlen. A sima `kenburns` (Pan and Zoom) a `slideshow_pan_zoom.py` véletlen kivágásait használja (#5258), tehát az a „nem véletlen” állítás csak az arcos változatra igaz.

**Bizonyítottsági fok: feltételes.** (A) A szerkezet és a címek utasításszintű olvasatból jönnek. (B) A második út a Python-kimenet, de az saját megvalósítás, nem független a binárisra vonatkozó olvasattól; ezért nem megerősített.

**Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy van középre igazító ág. A `0x0076d6f0`, `0x0076d7e0` és `0x0076d900` törzsében nincs ilyen ág, és a középre esés csak a törtek értékénél áll elő (lásd fent). A cáfolat nem sikerült.

**Kész, ha (a jegy pontjai).**

- ✅ Képlet címekkel: 4.4 és 4.6, a 4.6 szerkezeti lépéseivel.
- ✅ Középre igazítás: nincs külön ág (címekkel, fent).
- ⛔ Mag és futás előtti CRT-állapot: NINCS MEG (a diavetítés srand-helye nincs azonosítva; a két lehetséges hely a `FUN_0071c380`-ból hívódik).
- ⛔ Két egymást követő renderelt Colab-futás (job-184/185): NINCS MEG. A felvétel nincs a helyi mérőadatban, a megszerzéséhez a colab-jobs repó kell (hálózat).
- ⛔ Teljes képernyős használat: változatlanul nyitott (4.5).

**Nyitott.**

- Ghidra-kör kell: `0x0071c380` - hívja-e a diavetítés indítása a `0x0071d940` vagy a `0x0071e120` függvényt, és van-e srand a hívás előtt? [blokkoló]
- NINCS MEG: az x87 kerekítési mód (`fistp`) futás közben; megszerzés: a CRT-indítás utáni kontrollszó olvasása natív próbában (QEMU).
- NINCS MEG: a job-184/185 képkockasor (lásd fent).

**Fejlesztési következmény.** A #5351 szerinti kód a 18. kör kontrollvektorán a 4.4 képlet szerkezetét követi. Bitpontos eredeti véletlenszám-sorozat azonban nem állítható, amíg nem ismert, hogy a diavetítés melyik `+0x37c` ágat használja és melyik magérték jut a CRT-be.

**12. kör (2026-10-19, #5225): a diavetítés indítási lánca és a `srand`.** (A 4.6 szakasz nincs a munkafában, ezért ide került.)

*Forrás:* a `0x00783de0` (109 bájt) és a `0x0071d940` (381 bájt) és a `0x0071e120` (547 bájt) diszasszemblálása (`annot_disasm.py`), a `0x0071c380` dekompilált C-je (`.ghidra11/2026-10-19-ghidra-12.txt`), a bináris-index `xrefs` és `data_symbols` táblája.

- **Az indítási lánc (megerősített: C és diszasszembly).** A `0x00783de0` a `this` (ECX) `+0x2c8` mezőjét ellenőrzi (0 esetén `4`-gyel tér vissza), majd a `0x0071c2d0`-t hívja, és a `+0x37c` módértékre ágaz: 5 és 6 esetén a `0x007853e0` fut, 10 esetén a `0x00785020`, mindkettő után `0x0071c0b0`. Minden más módértéknél (0-4, 7-9 és 11 fölött) a `0x00783e40`-`0x00783e42` sor a `0x0071c380`-t hívja (`mov ecx,edi; call 0x71c380`).
- **A `0x0071c380` elágazása (megerősített: C és index).** A `+0x37c` (`param_1[0xdf]`) szerint: 1 → `0x0071d940`, 7 → `0x0071e120`, 2 → `0x0071ca60`, 8 → `0x0071dd40`, 9 → `0x0071dac0`. A `0x0071d940` és a `0x0071e120` közvetlen hívója az index szerint kizárólag a `0x0071c380` (egy-egy `call` él, adatreferencia nincs).
- **A vtábla-bejegyzés.** A `0x00cad62c` DATA-hivatkozás a `CSelectionNode::vftable` (`0x00cad5b4`) `+0x78` slotja (a 30.), tehát a `0x0071c380` virtuális metódusként is elérhető, a `0x00783e42` közvetlen hívás mellett.
- **Melyik ág a diavetítésé: NINCS MEG.** A `+0x37c` módértéket a hívó oldal írja. Ebben a körben nem néztem meg, melyik érték a diavetítés indításáé, ezért azt nem dönti el a szöveg: a diavetítés a `0x0071d940` (1) vagy a `0x0071e120` (7) ágon fut, a módérték szerint.
- **`srand` a hívás előtt: NINCS.** A `0x00783de0` diszasszemblált törzsében és a `0x0071c380` hívott-listájában nincs `0x00c08214`. A `0x00c08214` a CRT `srand` (`call 0x00bf0583`, majd a seed a szál állapotának `+0x14` mezőjébe kerül); a `0x00c08221` a `rand`. A 10 közvetlen `srand`-hely közül kettő a két célfüggvényben van: `0x0071d993` (a `0x0071d940` törzsében) és `0x0071e23b` (a `0x0071e120` törzsében).
- **A `0x0071d940` seedje (feltételes).** A `0x0071d98a`-`0x0071d993` sorok: `mov eax,edi; imul eax,eax,0xee6d00b1; push eax; call 0x0c08214`, ahol `edi` a ciklusindex. A seed tehát `i * 0xEE6D00B1` (32 bites szorzat), és a `srand` a ciklus minden elemén a `rand`-hívások előtt fut (`0x0071d9c0` és a többi `rand`). Ez a korábbi „mag nem igazolt” kijelentést pontosítja: a mag nem állandó, az elem indexéből jön. A `0x0071e120` seedje NINCS MEG: a `push eax` (`0x0071e23a`) előtti `eax` számítása a diszasszemblált ablakon kívül van.
- **Bizonyítottsági fok.** Az indítási lánc és az elágazás: **megerősített** (C és diszasszembly: két út). A srand-helyek: **megerősített** (diszasszembly és index). A `0x0071d940` magképlete (seed): **feltételes** (egy út, az asm). A diavetítés módértéke és a `0x0071e120` seedje: **NINCS MEG**.
- **Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy van srand a hívás előtt: a `0x00783de0` teljes diszasszemblált törzsében és a `0x0071c380` hívott-listájában nincs `0x00c08214`, a cáfolat nem sikerült. Azt is megnéztem, hogy a `0x0071d940` és a `0x0071e120` vtábla-slotból érhető-e el: a DATA-hivatkozások között nincs rájuk mutató bejegyzés. A vtábla-hívás kizárása nem negatív állítás, az index csak a közvetlen hívásokat látja.
- **13. kör (2026-10-20, #5225): a `0x0071e120` seedje megvan, a módérték nincs.** A `0x0071e120` ciklusában a `0x0071e21b` `mov esi, [ecx+eax*4]` után az `eax` a lista eleme (`[ecx+ebp*4]`; a lista a `[edi+0x358]` tömb, vagy ha a `[edi+0x360]` nem nulla, annak `[0]`-ján át). A `0x0071e23a` `push eax` és a `0x0071e23b` `call 0x0c08214` (srand) ezt az elemet kapja magként, minden olyan elemre, ahol a `[esi+0x5a]` és a `[esi+0x5b]` bájt nulla. A mag tehát nem állandó és nem `i * 0xEE6D00B1`, hanem az elem indexe (feltételes: egy út, az asm; a lista eredete NINCS MEG). A `0x00783de0` `+0x37c` olvasása C és asm szerint megerősített (lásd fent); a `+0x37c` írója és a diavetítés módértéke NINCS MEG.
- **15. kör (2026-10-20, #5225): a `+0x37c` írói megvannak; a módérték nincs.** A teljes `.text` pásztázása (`paszta.py`, `memoria_kapu()` első műveletként; 2 884 879 utasítás, 45 MiB csúcs) a `[reg+0x37c]` célú írásokra 26 találatot adott, 23 függvényben (ideiglenes kimenet, törölve). Konstanst ír két helyen: `0x00714bad` (`mov dword ptr [esi+0x37c], 2`, függvény `0x00714990`) és `0x0077ff0d` (`mov dword ptr [esi+0x37c], 5`, függvény `0x0077fd80`). A többi 24 írás regiszterből ír; az értékük a hívóláncból jön, azt nem követtem. A `0x0077fd80` hívói az index szerint `0x0074ad40` és `0x00789820`. Nem fedett: a számított, nem literál `0x37c` eltolású írás (pl. `memcpy`, `rep movs`). A diavetítés módértéke: **NINCS MEG.** Megválaszolva a 17. körben (lent): a `0x0077fd80` `5`-öt ír, hívóágtól függetlenül. A diavetítés módértékére új Ghidra-kérdés van.

**17. kör (2026-10-20, #5225): a `0x0077fd80` módértéke feltétel nélkül `5`; a diavetítés módértéke NINCS MEG.**

*Forrás:* `annot_disasm.py` a `0x0077fd80` (414 bájt) és a `0x00714990` (`0x00714bad`) részein; a `.ghidra/2026-10-20-ghidra-16.txt` C-je a `0x00789820`-ra és a `0x0074ad40`-re.

- **`0x0077fd80` (megerősített, asm, egy út).** Az `AlbumSelectionNode` konstruktora (a `+0x300` a `"AlbumSelectionNode"` sztringre mutat). Előbb a bázis-konstruktort hívja (`call 0x714990`, `0x0077fd86`), amely `+0x37c = 2`-t ír (`0x00714bad`), majd a `0x0077ff0d`-ban `mov dword ptr [esi+0x37c], 5` felülírja. Nincs feltételes ág a két érték között: a `0x0077fd80`-nal épített objektum módértéke `5`.
- **A két hívó (megerősített, C).** A `0x0074ad40` a `local_15d == 0` ágon hívja (`FUN_0077fd80()`), a `0x00789820` (CFoundFaceSelectionNode konstruktor) pedig az elején, és `+0x37c`-t maga nem ír. Mindkét hívó `5`-öt kap, tehát a `2` és `5` közti választás nem a hívóágon dől el.
- **Az `5` nem diavetítés-módérték.** A `0x0071c380` elágazása (`1`, `7`, `2`, `8`, `9`) nem tartalmazza az `5`-öt; az `5`/`6` ág a `0x00783de0`-ban a `0x007853e0`-hoz vezet.
- **A diavetítés módértéke: NINCS MEG.** A `srand`-os ágak (`0x0071d940` = `1`, `0x0071e120` = `7`) a jelöltek. Írójuk a 24 regiszterből író `+0x37c` hely egyike; az értéket a hívóláncból kell visszafejteni. Megválaszolva a 18. körben (lent): a `1` és a `7` nem literálból íródik; a `0x00714510` a legközelebbi jelölt; a diavetítés ága NINCS MEG.
- **Bizonyítottsági fok.** Az `5` a `0x0077fd80`-ban: **megerősített** (asm; a két hívó C-je egyezik). A `2` a bázisból: **megerősített** (asm). A diavetítés módértéke: **NINCS MEG**.
- **Cáfoló kísérlet.** Azt feltételeztem, hogy a `0x0077fd80` `5`-je a diavetítés módja: cáfolva, mert a `0x0071c380` nem ágaz az `5`-re, és az `5`-ös objektum az `AlbumSelectionNode` család.
- **Fejlesztési következmény.** A 4.4 képlet (`0x0076d900`) és a srand-magok továbbra is feltételesek; a Python-port nem zárható le a módérték nélkül.

**18. kör (2026-10-20, #5225): a `+0x37c` 1-es és 7-es értéke nem literálból íródik; a `0x0076d900` képlete a jelenlegi kódban egyezik a 4.6-tal.**

*Forrás:* a teljes `.text` pásztázása (`paszta.py`, `memoria_kapu()` első művelet, 2 884 879 utasítás, csúcs RSS 93 MiB) a `dword ptr [reg+0x37c]` célú írásokra (26 találat, a 17. körben is 26); a 16 utasításos visszakeresés, és a `NINCS` találatok teljes függvénytörzsre kiterjesztett visszakeresése; `annot_disasm.py` a `0x00783de0` (109 bájt) és a `0x00714510` (17 bájt) címen; a `src/picasapy/app/slideshow_pan_zoom.py` és a `tests/app/test_slideshow_pan_zoom_5351.py`.

- **A 26 írás felosztása (megerősített, pásztázás).** Nyolc literál: `2` (`0x00714bad`, `FUN_00714990`), `5` (`0x0077ff0d`, `FUN_0077fd80`), `-1` (`0x005a6431`, `or eax, 0xffffffff`), és öt nulla (`0x00466929`, `0x008c76c6`, `0x00a5d9a8` `xor`-ral; `0x00612b7b`, `0x006161ea` a pásztázás szerint). A másik tizennyolc íráshoz a forrás argumentum (`0x00593711`, `0x00593942`, `0x005d1f24`, `0x00714518`, `0x008bfc2b`, `0x008c1eb4`), memória (`[edi+8]`, `[eax+4]`, `[eax+8]`, `[esi+0x448]`, `[ebx+0x388]`, `[ebp+0x380]`, `[edx+0xe00]`, `[ebp+0x268]`), vagy a régi érték átalakítása: a `0x00636c17` a `[ebx+0x37c]` 0. bitjét törli (`and`/`xor`, páros értéket ír); a `0x007681d1` forrása nem azonosított (a függvényben nincs `eax`-író).
- **A `1` és a `7` nem literálként íródik (megerősített, pásztázás).** A 26 íráshoz sem a 16 utasításos ablakban, sem a függvénytörzs teljes visszakeresésében (a `NINCS` esetek) nincs `mov reg, 1` vagy `mov reg, 7` a tárolás előtt. Ez a visszakeresés lineáris, elágazás-követés nélkül készült; a két érték tehát argumentumon vagy memórián át jut a mezőbe.
- **A legközelebbi jelölt: `0x00714510` (feltételes).** A 17 bájtos függvény a `[ecx+0x37c]`-be az `[esp+4]` argumentumot írja (`0x00714518`), tehát argumentumból beállító. Az indexben nincs közvetlen hívója; a hívók vtábla-hívások, a vtábla azonosítatlan.
- **A diavetítés ágának kérdése: NINCS MEG.** A `0x00783de0` (109 bájt) a `+0x37c` szerint ágaz: 5-6 → `0x007853e0`, 10 → `0x00785020`, minden más → `0x0071c380` (ebből 1 → `0x0071d940`, 7 → `0x0071e120`). A `0x00783de0`-nak nincs közvetlen hívója, két adat-hivatkozása van (`0x00cb476c`, `0x00cb48b4`), feltehetően vtábla-slot; az osztályt nem azonosítottam. Melyik ág a diavetítésé, az a `+0x37c` értékének hívóláncától függ, amelyet literálból a fenti okból nem lehetett kiolvasni.
- **A `0x0076d900` képlete és a kód egyezése.** A képlet megerősített (4.4 és 4.6). A jelenlegi `slideshow_pan_zoom.py` (#5351) a 4.6 szerkezetét követi: A és B alaptéglalap, két LCG-csere a skálázás előtt, `u` és `v` újrahúzás, a nagyobb skálájú jelölt a `ρ0`, `ρ1` párt kapja, határolás a méret megtartásával. A 4.6 tesztvektorával (forrás 1000×500, nézet 1024×768, `u` = 29491/32768, `v` = 6554/32768, `ρ` = (16384, 8192, 24576, 3277)/32768, csere nélkül) a függvény: A = (0,00; 17,50; 620,31; 465,00), B = (323,04; 0,00; 526,93; 395,00). Az alap egész: 667×500, a `(forrás + 0,499) / célméret` aránnyal és `round` kerekítéssel. A kód és a 4.6 ugyanabból az olvasatból készült, ezért ez a két oldal nem független út: a függvény értékei mértek, az egyezés feltételes.
- **A 4.6 „Mért eltérés” táblázata elavult.** Az A 140,00 / B 156,67 értékek a #5351 előtti kódot írják le (közös középpont, nem egész alap); a kód a 4.6 szerkezetét követi.
- **Bizonyítottsági fok.** A `+0x37c` literál-írói: **megerősített** (pásztázás). A `1` és a `7` hiánya literálból: **megerősített** (pásztázás és visszakeresés). A `0x00714510` mint jelölt: **feltételes**. A diavetítés ága: **NINCS MEG**. A képlet: **megerősített** a 4.4/4.6 szerint; a kód egyezése: **feltételes** (ugyanabból az olvasatból).
- **Cáfoló kísérlet.** (1) Azt feltételeztem, hogy a `1` vagy `7` literál a `0x00783de0` közelében íródik: cáfolva, a teljes `.text` pásztázása ilyet nem talál. (2) Azt feltételeztem, hogy a `slideshow_pan_zoom.py` még a régi, közös középpontú képletet használja: cáfolva, a jelenlegi kód A/B-alapú, és a 4.6 vektorán a fenti értékeket adja.
- **Lezárás (#5225).** A képlet-rész lezárható, (a) jegytörzs-javaslat. Eredeti: a `0x0076d900` (4.4 és 4.6, címekkel). Nálunk: `src/picasapy/app/slideshow_pan_zoom.py` (#5351), a 4.6 vektorán mért értékekkel. Teendő kódra: nincs a képletre; a 4.6 elavult táblázatát a spec-ben ki kell cserélni (ez a fenti bekezdés). Kész, ha (képlet): ✅ címekkel; ✅ középre igazító ág nincs (4.6); ✅ a kód a tesztvektoron a 4.6 képletéből, egész alappal számolt értékeket adja. Nem része: a diavetítés CRT-magja (a `0x0071d940` és a `0x0071e120` `srand`-ágai) és a `+0x37c` mód (melyik ág a diavetítésé). Ez a két kérdés új kutatási jegyet kap; a futásidejű képkocka-mérés (job-184/185) és a teljes képernyős út külön marad.

**19. kör helyesbítése (2026-10-20, #5225): a `0x00714510` a `CSelectionNode` 44. slotja; a teljes `.text`-keresés hét `+0xb0`-s diszpécselési jelöltet talált, de közülük kettő négyargumentumos hívás, ezért nem azonosítható közvetlenül az egyargumentumos setterrel; a diavetítés ága NINCS MEG.**

*Forrás:* `.ghidra/2026-10-20-ghidra-19.txt` (a `0x00714510` C-kódja); a PE-olvasás a három slot-címre és a COL-okra; a teljes `.text` `mov reg,[reg+0xB0]` + `call reg` mintázatának keresése (139 betöltés, 14 utasításos ablak); `annot_disasm.py` és a hívóhelyek környezete; a bináris-index `xrefs` táblája.

- **A vtábla és az osztály (megerősített, PE-olvasás).** A `0x00714510` a 44. slot (eltolás `0xB0`) három vtáblában: `CSelectionNode` (vtábla `0x00cad5b4`, COL `0x00d0a50c`, 50 slot; a slot címe `0x00cad664`), `CAlbumSelectionNode` (vtábla `0x00cb46f4`, COL `0x00d0d258`, 61 slot; `0x00cb47a4`), `CFoundFaceSelectionNode` (vtábla `0x00cb483c`, COL `0x00d0d1a8`, 61 slot; `0x00cb48ec`). Mindhárom this-eltolása 0, és a leszármazottak a 44. slotot nem írják felül.
- **A `+0xb0` diszpécselési jelöltek (asm, teljes `.text`; a célosztályt külön kell igazolni).** A `0x00714510` setter egy argumentumot olvas a `[esp+4]`-ről és `ret 4`-gyel tér vissza (`0x00714510`-`0x0071451e`). A teljes `.text` keresése 139 `mov reg,[reg+0xb0]` betöltést talált; 11-nél volt közeli `call reg`, ezek közül 7 adott át argumentumot. Négy hívás egy-egy literált ad át (2, 2, 9, 6), egy paraméteres hívás egy argumentumot ad át (`0x008de9b0`), kettő pedig négy argumentumot ad át (`0x004331c0`, `0x00433680`). Az utóbbi kettő `+0xb0`-s célfüggvénye ABI alapján nem azonosítható közvetlenül a `0x00714510` setterrel. A másik négy közeli hívás (`0x0061fdb7`, `0x00620504`, `0x007a90b6`, `0x0094fda8`) nem adott át argumentumot. A `call [reg+0xb0]` alakra nulla találat volt.

| `+0xb0`-s hívójelölt | hívóhely | átadott argumentum(ok) |
|---|---|---|
| `FUN_005154f0` | `0x00515695` | literál `2` |
| `FUN_0071c4f0` | `0x0071c534` | literál `2` |
| `FUN_005733f0` | `0x00573667` | literál `9` |
| `FUN_0074ad40` | `0x0074b0d8` | literál `6` |
| `FUN_004331c0` | `0x004335f9` | négy stack-argumentum; a hívó `0x006ed5e0` negyedik paramétere dinamikus |
| `FUN_00433680` | `0x00433a2e` | négy stack-argumentum |
| `FUN_008de9b0` | `0x008debe4` | egy dinamikus stack-argumentum (`[esp+0x14]`); a vtable-célosztály nincs azonosítva |

- **Az `1` és a `7` (NINCS MEG a forrásig).** Egyik egyargumentumos jelölt hívó sem ad át közvetlenül `1`-et vagy `7`-et literálként. A `0x008de9b0` egyargumentumos `+0xb0` hívásának paraméterét a `0x008de6b0` adja tovább, de a dinamikus célobjektum osztálya és a paraméter előállítása nincs dekompilálva. A `0x004331c0` és `0x00433680` paraméteres `+0xb0` hívásai négyargumentumosak, ezért önmagukban nem bizonyítják a `0x00714510` setter elérését. A `0x006ed5e0`-t és a `0x007b2210`-et a `0x004331c0` hívja; az előbbi UploadImage-hibakezelési út, az utóbbi albumtörlés (`AlbumDeleter::progress`), egyik sem slideshow-bizonyíték.
- **A diavetítés ága (NINCS MEG).** A `0x00783de0` (a `CAlbumSelectionNode` és a `CFoundFaceSelectionNode` 30. slotja) a `+0x37c` szerint ágaz: 5-6 → `0x007853e0`, 10 → `0x00785020`, egyébként `0x0071c380`. Ez utóbbi a `CSelectionNode` 30. slotja, és benne 1 → `0x0071d940`, 7 → `0x0071e120`. Hogy melyik objektum melyik értéket kapja, az a fenti paraméteres láncon dől el.
- **Bizonyítottsági fok.** A vtábla, a 44. slot és a négy `CSelectionNode`-család-vtábla-bejegyzés: **megerősített** (PE/RTTI). A hét `+0xb0`-s hívójelölt és a négy literál (2, 2, 9, 6): **megerősített** (asm), de a célosztályok egyezése nincs mindegyiknél bizonyítva. Az `1`/`7` forrása és a diavetítés módértéke: **NINCS MEG**.
- **Cáfoló kísérlet.** (1) Azt feltételeztük, hogy az 1 vagy a 7 literálként íródik valamely egyargumentumos `+0xb0` jelölt hívónál: cáfolva, az öt ABI-kompatibilis jelölt közül egyik sem ad ilyen literált; a két négyargumentumos hívás pedig nem azonosítható közvetlenül a setterrel. (2) Azt, hogy a közvetlen memória-hívás (`call [reg+0xb0]`) is használja a slotot: cáfolva, nulla találat.
- **Lezárás (#5225): a képlet-port átadható, a magot kérő kutatás nyitott.**
  - *Eredeti.* A képlet a `0x0076d900`-ban van (4.4 és 4.6). A `0x00714510` setter a `CSelectionNode` 44. slotja; a teljes `.text`-pásztázás hét `+0xb0`-s hívójelöltet talált, amelyek közül a célosztály/ABI egyezése további ellenőrzést igényel.
  - *Nálunk (mérve a `src/` alatt).* A `src/picasapy/app/slideshow_pan_zoom.py` `qml_pan_zoom_rectangles` függvénye (a `controller.py:573` és a `screensaver_mode.py:97` hívja) a 4.6 szerkezetét követi (#5351). Mag nélkül (`seed=None`) a `_lcg_fraction_source` a `random.getrandbits(32)`-ből húz, így a sorozat nem a binárisé. A jegy Nálunk-sora (`SlideshowView.qml:752-761`, középre igazított 1,08 / 1,12) elavult: a fájlban az 1,08 nincs meg, az 1,12 a 856. sorban áll, és a 752-761 sorokat nem vizsgáltam tovább.
  - *Teendő.* A jegytörzs Nálunk-sorát kell cserélni. A bitpontos egyezéshez a mag kell, ez a Nem része.
  - *Kész, ha.* ✅ képlet címekkel (4.4, 4.6); ✅ nincs középre igazító ág (4.6); ✅ a kód a 4.6 kontrollvektorán a képlet szerkezetét követi (a 18. kör mérése); ⛔ a slideshow mód és a kiválasztott CRT-mag a binárisból: NINCS MEG, ez a kutatás nyitott része.
- **Nem része (nyitott mellékkérdések).**
  - `Ghidra-kör kell: 0x008de9b0 - a 0x008debe4 +0xb0 virtuális hívás dinamikus célja a 0x00714510 setter-e, és honnan kapja az egyetlen argumentumát? [blokkoló]`
  - `Ghidra-kör kell: 0x00425f60 - a 0x00426f28 +0x5c virtuális hívás célosztálya/célfüggvénye; van-e a slideshow-ágban bizonyított adatút a CSelectionNode +0xb0 setterhez? [blokkoló]`
  - A diavetítés srand-magja: NINCS MEG. A binárisból nem olvasható ki, ha futásidejű állapotból jön. Ezt két egymás utáni, azonos bemenetű Pan and Zoom diavetítés képkockáinak összevetése dönti el (a job-184/185 kiterjesztése): azonos kimenet állandó magra, eltérő kimenet időalapú magra utal.
- **Nyitott kérdések mérlege.** 2 lezárva (a vtábla és a hívók) · 2 blokkolt (az 1/7 forrása és a diavetítés ága; a mag) · 0 hatókörön kívül · 0 csak nyitva.

**20. kör (2026-10-20, #5225): a `0x006ed5e0` upload-út, a `0x004331c0` négyargumentumos virtuális hívása nem bizonyítja a `0x00714510` settert; az 1/7 forrása és a diavetítés ága továbbra is nyitott.**

*Forrás:* `.ghidra/2026-10-20-ghidra-20.txt` (`FUN_006ed5e0` C-kódja és hívói); a bináris-index `string_xrefs`, `xrefs` és RTTI táblái; `annot_disasm.py` a `0x00714510`, `0x004331c0`, `0x00433680`, `0x008de9b0`, `0x00425f60` környezetében; a korábban, a `paszta.py` `memoria_kapu()` kapuján át végzett teljes `.text`-pásztázás eredménye.

- **A `0x006ed5e0` útja (feltételes, két független út egyezik).** (A) A Ghidra C-kimenet egyetlen közvetlen hívóként a `0x006f18a0`-t adja, a függvény pedig `UploadImage:InvalidPendingImage`, `UploadImage:AlbumFetchError`, `UploadImage::AlbumNotFound`, `UploadImage:NoAlbum` és `UploadPhoto::DoesNotExist` hibákhoz fut; a `0x004331c0` segéd negyedik argumentuma a `param_1[0x15]`. (B) Ettől függetlenül a bináris-index `string_xrefs` ugyanezeket az `UploadImage`/`UploadPhoto` hibaüzeneteket rendeli a `0x006ed5e0`-hoz, az indexelt hívási lánc pedig a `0x006f18a0`-n át az UploadManager hibakezeléséhez vezet. A két út az upload-besorolásban egyezik.
- **A módérték ebből az útból nem olvasható ki.** A `0x006ed5e0` a `0x004331c0`-t hívja, és a Ghidra C negyedik argumentuma `param_1[0x15]`. A `0x004331c0` diszasszemblyje viszont a `0x004335f9`-nél egy `+0xb0` virtuális hívásra **négy** stack-argumentumot készít elő (`0x004335ff`-`0x0043360a`); e hívás dinamikus célosztálya nincs azonosítva, és ABI alapján nem azonosítható közvetlenül a `0x00714510` egyargumentumos, `ret 4` setterrel. Ezért a `param_1[0x15]` nem bizonyítja az `1`/`7` setterértéket.
- **Cáfoló kísérlet.** Azt próbáltam cáfolni, hogy a `0x006ed5e0` lenne a slideshow `1`/`7` beállítója: a feltöltési hibaüzenetek és a `0x006f3cd0` (`UploadManager::process_error`) → `0x006f18a0` → `0x006ed5e0` hívási út az upload-besorolást erősíti. A közbeiktatott `0x004331c0` négyargumentumos `+0xb0` hívása az ABI-kontrollon sem egyezik a `0x00714510` setterével. Kontrollként a másik `0x004331c0` hívó, `0x007b2210` string-xrefje `"Deleting album: %s"` / `AlbumDeleter::progress`; ez sem slideshow-bizonyíték. A független mérce a Ghidra C/hívó és a bináris-index string-/xref-út; egyik sem azonosítja az `1`/`7` setterforrást.
- **Két megmaradt Ghidra-kérdés (blokkoló).** (1) `0x008de9b0`: a `0x008debe4` egyargumentumos `+0xb0` hívásának dinamikus célja valóban a `0x00714510`-e, és honnan kapja az argumentumát (`0x008de6b0` hívó)? (2) `0x00425f60`: a slideshow-gyökerek alatti jelölt `0x00426f28` `+0x5c` hívásának célosztálya/célfüggvénye mi, és vezet-e bizonyított adatút a `CSelectionNode` `+0xb0` setterhez? A `0x0049f440` → `0x00433680` út csak vtable-jelölt; a `0x00433680` saját `+0xb0` hívása is négyargumentumos, ezért ezt sem szabad a setterrel azonosítani.
- **Lezárás (#5225): (c) célzott Ghidra-kör szükséges.** Következő batch-címek: `0x008de9b0` (a setter-alakú, egyargumentumos `+0xb0` hívás célja és értéke) és `0x00425f60` (a slideshow-leszármazott `+0x5c` hívás fogadója/célja, valamint az esetleges út a `+0x37c` setterig). Az első dönti el, hogy a paraméteres `+0xb0` jelölt valóban setter-e; a második a slideshow-kapcsolatot vizsgálja. Ha a diavetítés `1`/`7` módja megvan, a megfelelő seedág pontos bináris képlete a `0x0071d940` vagy `0x0071e120` függvényből olvasható ki.
- **Bizonyítottsági fok.** A `0x006ed5e0` upload-besorolása: **megerősített** (Ghidra C/hívó és független string-/xref-út egyezik). A `0x00426f28` vtable `+0x5c` hívás ténye és a `0x004331c0`/`0x00433680` négyargumentumos `+0xb0` hívási alakja: **megerősített** (utasításszintű diszasszembly). Hogy a `0x008debe4` célja a `0x00714510` setter-e, a slideshow-kapcsolat, az `1`/`7` módforrás és a kiválasztott seedág: **NINCS MEG**.
- **Kódhatás.** Kódmódosítást ez a kör nem indokol: a képlet portja (#5351) már megvan, de a módérték/seed bináris szerinti hozzárendelése blokkolóan nyitott.

**Frissített nyitott kérdések:**

- **Válasz (21. kör):** a `0x008debe4` `+0xb0` hívás receptora dinamikus, célja nem bizonyított; az argumentuma a 38. sor kimeneti paramétere (`local_c`). Lásd lent.
- **Válasz (21. kör):** a `0x00426f28` `+0x5c` hívásának célosztálya nincs megnevezve, nem ad bizonyított utat a `CSelectionNode +0xb0` beállítóhoz. Lásd lent.

A `.ghidra/2026-10-20-ghidra-20.txt` bemenet, nem módosított fájl.

**21. kör (2026-10-20, #5225): a `0x008de9b0` `+0xb0` hívásának receptora dinamikus, a `0x00425f60` `+0x5c` hívásának célja nincs megnevezve; a setter-út nem bizonyított.**

*Forrás:* `.ghidra/2026-10-20-ghidra-21.txt`: a `0x008de9b0` C-törzse (14-127. sor), a `0x00425f60` C-törzsének `+0x5c` hívóhelye (1536. sor).

- **A `0x008de9b0` hívási alakja (megerősített, C).** A függvény a `this` (`in_EAX`) vtábla `+0x50` slotját több helyen hívja (38., 48., 109., 112. sor). A `+0xb0` hívás (113. sor, a jegyben a `0x008debe4` címen) a 112. sor visszatérésén hívódik. Feltételei: `piVar8[0x1a] == -1` (45-46. sor), `piVar8[1] == 0x80` (104. sor), és a `+0x140` vtábla-hívás nem ad `3`-at (105-106. sor).
- **Az argumentum forrása (megerősített, C).** A `local_c` a 38. sor `+0x50` hívásának kimeneti paramétere (`&local_c`), a bemenete a függvény első stack-argumentuma (`param_1`). Nem literál. A `param_1` értékét a hívó, a `0x008de6b0` adja, a `0x008de9b0` egyetlen hívója.
- **A receptor és a célfüggvény: NINCS MEG.** A receptor a `this` `+0x50` slotjának visszatérése, osztálya nincs azonosítva. A `0x00714510` a hét jelölt egyike (19. kör); a slot-egyezés nem igazolja a célt.
- **A `0x00425f60` `+0x5c` hívása (megerősített, C).** A `0x00426f28` (1536. sor) a `local_181c+0x48` beágyazott objektum vtábla `+0x5c` slotját hívja, egyszer minden elemre a `FUN_009881d0(&lista, 0x2c)` által töltött listából (`piStack_1824 >> 1` darab). A receptor minden iterációban ugyanaz. A célosztály és a célfüggvény: **NINCS MEG**. Ebből nem következik út a `0x00714510`-hez, és nem ad módértéket (1/7).
- **Bizonyítottsági fok.** A hívási alakok és az argumentum forrása: **megerősített** (C, egy út). A receptorok osztálya és a célok: **NINCS MEG**. A `+0xb0` = `0x00714510` azonosítás: **feltételes** (csak a slot-egyezésen alapul).
- **Cáfoló kísérlet.** (1) Feltételeztem, hogy a `+0xb0` a `0x00714510`-et hívja: nem bizonyított, mert a receptor dinamikus. (2) Feltételeztem, hogy a `+0x5c` hívás a slideshow-setterhez vezet: nem igazolt, mert a célosztály nincs megnevezve.
- **Lezárás (#5225): (c).** Nem zárható. A módérték forrása a receptorok osztályától függ, ezt a vtábla-írók és a hívó adja meg; ez a következő kör dolga. Következő Ghidra-címek:
  - **Megválaszolva részben (23. kör):** a `0x008de6b0` nem a `+0xb0` receptor, hanem a Fen-ablak üzenetkezelője. A `0x008de9b0`-t a WM_COMMAND (`0x111`) ága hívja: `FUN_008de9b0(param_2 >> 0x10, param_5)`, tehát a `param_1` az üzenet wParam felső szava (értesítési kód). A `this` (`param_3`) osztálya nincs a törzsből; a `this+0x50` slot vezérlőkeresés: a WM_NOTIFY ágban az argumentum `*param_5` (az NMHDR `hwndFrom` mezője), a 0x112 ágban nincs argumentum. A `0x00714510` kérdése így nem dől el: (24. kör: a `0x008de3c0` nem a receptor, lásd 4.7; a két nyitott cím: `0x008de220`, `0x008de2a0`.)
  - `Ghidra-kör kell: 0x009881d0 - a `FUN_009881d0(&lista, 0x2c)` gyűjtő: mely objektumokat ad vissza, és a 0x2c kulcs jelentése a `0x00425f60` `+0x5c` receptorának azonosításához [blokkoló]`
- **A mag (seed).** Nyitott: a `srand` ágak (`0x0071d940` = 1, `0x0071e120` = 7) a módértéktől függnek, a mag így sem olvasható ki.

#### 4.7 24. kör (2026-10-20, #5225): a `0x008de3c0` és a receptor eredete

**Kérdés.** A 23. kör nyitott címe: a `0x008de3c0` (a `0x008de6b0` hívója, a `0x008de523` hívási helyen): a dialógus-objektum, annak osztálya, és a módértéket adó listaelem.

**Forrás.** `.ghidra/2026-10-20-ghidra-24.txt` (C, a `0x008de3c0` törzse); `.ghidra/2026-10-20-ghidra-23.txt` (a `0x008de6b0` C-törzse és hívási listái); a bináris-index DATA-hivatkozásai: `008de267` (a `0x008de220` törzsében) és `008de2f0` (a `0x008de2a0` törzsében) a `0x008de3c0` címére mutat.

**Mit csinál a `0x008de3c0`.** Ablak-üzenetkezelő (WndProc). `WM_CREATE` (1) és `WM_NCCREATE` (0x81) csak visszatér (0, illetve 1). `WM_INITDIALOG` (0x110): `SetWindowLongA(hwnd, -0x15, lParam)`, vagyis a GWL_USERDATA-ba a lParam kerül; `this+0x20 = hwnd`; a vezérlőfa lekérdezése virtuálisan (`+0x50`, `+0xc0`, `+0xd4`), majd a `0x28` üzenet küldése egy vezérlőnek. Minden más üzenetnél, ha a GWL_USERDATA nem nulla, `return FUN_008de6b0(LVar7, hwnd, lParam)`.

**Következmény a receptorra.** A `0x008de6b0` első argumentuma `__fastcall`, az ECX-ben érkezik, és a GWL_USERDATA-objektum (a `0x008de3c0` `LVar7`-je). A `0x008de9b0`-t (WM_COMMAND-ág) a `0x008de6b0` hívja, de a `+0xb0` hívás `this`-ének forrása a C-ben nincs kiírva: a `0x008de6b0` `param_3`-at objektumként dereferálja, ami argumentum-leképezési bizonytalanságot jelez. A receptor osztálya tehát a WM_INITDIALOG lParam-jának forrásától függ (feltételes).

**A `0x008de3c0` nem a `+0xb0` receptor.** A törzsben nincs `+0xb0` hívás. A virtuális slotok: `+0x4`, `+0x28`, `+0x50`, `+0xc0`, `+0xd4`, `+0x134`. Közvetlen hívás a `0x00714510`-re nincs (C, megerősített). A címet kódrészlet adja át (DATA-hivatkozás a `0x008de220` és `0x008de2a0` törzsében), nem vtábla-bejegyzés.

**Módérték.** A törzsben nincs `+0x37c` írás, és a `1`, `7` érték nem jelenik meg ebben a függvényben (C).

**Cáfoló kísérletek.**
1. „A `0x008de3c0` a `+0xb0` receptor”: cáfolva, a `+0xb0` nincs a törzsben.
2. „A `0x008de3c0` közvetlenül hívja a `0x00714510`-et”: cáfolva, a hívási listában nincs.
3. „A módértéket ez a törzs adja”: cáfolva, nincs `+0x37c` írás.

**Bizonyítottsági fok.** A `0x008de3c0` ágai és a `this` = GWL_USERDATA: **megerősített** (C, egy út). A receptor osztálya: **NINCS MEG**. A `+0xb0 = 0x00714510` és a módérték (1/7): **NINCS MEG**.

**Lezárás (#5225, 24. kör): (c).** A receptor osztálya a dialógus létrehozójától (a lParam forrásától) függ, ezt a dump nem tartalmazza. Következő Ghidra-címek:

**25. kör (2026-10-20, #5225): a `0x008de220` lParam-ja, a `this` osztálya és a receptor.** Kérdés: a `0x008de3c0` létrehozója mi kerül lParam-ként, ebből mi a `+0xb0` receptor, és a módérték 1 vagy 7. Forrás: `.ghidra/2026-10-20-ghidra-25.txt` (C, a `0x008de220` törzse és hívási listája); a bináris-index `rtti` (vtábla-sorok) és `data_symbols` táblája; `referencia/ghidra/2026-10-20-ghidra-21.txt` (a `+0xb0` cél; nincs benne `+0x37c`).

- **Létrehozó (C, megerősített).** `CreateDialogIndirectParamA(hInstance, FUN_008decc0(), param_2, FUN_008de3c0, param_1)`: az lParam a `this` (`param_1`). A `this+0x8` = 1, a `this+0x20` a létrehozott HWND (25. dump 912-941. sor). A 4.7 szerint a WM_INITDIALOG ezt a lParam-ot a GWL_USERDATA-ba írja, így a `0x008de6b0`-nak átadott objektum ugyanez a `this`.
- **A `this` osztálya (bináris-index, megerősített: két út egyezik).** A C-törzs és a vtábla-index: a `0x008de220` a `Fen::Win32WindowImp::vftable` (`0x00cced4c`, 23 slot a `data_symbols` szerint) 15. slotja (`0x00cced4c + 0x3c = 0x00cced88`), és a 25. dump DATA-hivatkozása ide mutat. A `this` tehát `Fen::Win32WindowImp`, vagy olyan leszármazott, amely ezt a slotot nem írja felül.
- **A `+0xb0` receptor (vtábla-index, feltételes).** A `0x00714510` a 44. slotban (`+0xb0`) csak három vtáblában áll: `CSelectionNode::vftable` (`0x00cad5b4`), `CAlbumSelectionNode::vftable` (`0x00cb46f4`) és `CFoundFaceSelectionNode::vftable` (`0x00cb483c`). A `Fen::Win32WindowImp` vtáblájának nincs 44. slotja, tehát a `this` nem a `+0xb0` receptor; a receptor a kiválasztás-csomópont család egyike. Feltétel: az index rtti-listája teljes, a futásidejű objektum nincs követve.
- **Módérték (1 vagy 7): NINCS MEG.** A `+0x37c` írása és olvasása nincs a 25. dumpban; a 21. kör dumpjában nincs `37c` (grep). A `0x00714510` hívóhelye vtábla-hívás (`call [reg+0xb0]`), amelyet a közvetlen hívási gráf nem lát.
- **Cáfoló kísérletek.** (1) „A `this` a `+0xb0` receptor": cáfolva, a `Fen::Win32WindowImp` vtáblájában nincs 44. slot. (2) „A `0x008de220` közvetlenül hívja a `0x00714510`-et": cáfolva, a hívottak között nincs (CreateDialogIndirectParamA, FUN_008decc0, GlobalFree, IsIconic, ShowWindow, FUN_00512030). (3) „Az 1/7 érték a `0x008de220`-ban van": cáfolva, a törzsben nincs ilyen literál.
- **Lezárás (#5225, 25. kör): (c).** A módérték írója vtábla-hívás helyén van, ezért a címe nem adható meg a közvetlen hívási gráfból: a `call [reg+0xb0]` hívóhelyeit pásztázással kell megtalálni (`paszta.py`, a memória-kapuval első lépésként). A 26. körben a hívóhely megvan (`0x008debed`, lásd 4.7/c); a módérték forrása a `0x008de9d0` hívás kimeneti paramétere.
Ghidra-kör kell: 0x008de2a0 - a `0x008de3c0` másik adatreferenciája: ugyanaz-e a létrehozó-minta, mint a `0x008de220`-é [nem blokkoló]

#### 4.7/c A 26. kör (2026-10-20, #5225): a `+0xb0` pásztázás és a módérték forrása

**Kérdés.** A 25. kör (c) pontja: a diavetítés módértékének írója, a `+0xb0` vtábla-hívóhelyek pásztázással.

**Pásztázás (bináris, megerősített).** `.bt/pasztazas.py` (a munkafában; a hívó takarít). A teljes `.text` egy menetben, `paszta.utasitasok()` darabolt kimenetével; a `memoria_kapu()` az első lépés, külső plafonnal (`MemoryMax=2400M`, `MemorySwapMax=0`). Dekódolt utasítás: 2 884 879; csúcs RSS 94 MiB.
- A jelzett forma, `call dword ptr [reg+0xb0]`: **0 találat**. A fordító a vtábla-hívást nem így írja: ez a memóriaforma a `.text`-ben nincs.
- A `mov reg, dword ptr [obj+0xb0]` + `call reg` forma (6 utasításon belül): **9 találat**.

| hívóhely | hívó függvény | argumentum (12 utasításos ablak) |
|---|---|---|
| `0x0051569d` | `0x005154f0` | `push 2` |
| `0x0057366f` | `0x005733f0` | `push 9` |
| `0x0061fdbf` | `0x0061df10` | nincs literál |
| `0x0062050c` | `0x0061df10` | nincs literál |
| `0x0071c53e` | `0x0071c4f0` | `push 2` |
| `0x0074b0e0` | `0x0074ad40` | `push 6` |
| `0x007a90bc` | `0x007a90a0` | `push esi` |
| `0x008debed` | `0x008de9b0` | `push ecx` (a `[esp+0x14]` kimeneti érték, lásd lent) |
| `0x0094fdb0` | `0x0094fc90` | regiszter (`esi`) |

- Literál 1 vagy 7: **nincs** a kilenc találat között. Sztring-hivatkozás a hívó függvényekben: egyiknek sincs (`string_xrefs`).
- A diavetítés-kapcsolat: a `0x008debed` a `0x008de9b0`-ban van, amelyet a 23. kör szerint a WM_COMMAND-ág hív. A `0x008de220` dialógus diavetítéshez kötése még nincs igazolva.

**A hívóhely (C és asm, megerősített).** A `0x008debe4` a `[edx+0xb0]` slotot tölti, a `0x008debed` a `call edx`; a `this` az `eax`, amelyet a `[edi+0x50]` második hívása (`0x008debdc`) ad vissza. Az argumentum `ecx = [esp+0x14]`. Ez nem a függvény paramétere: a `0x008de9c1` (`lea eax,[esp+0x14]`; `push eax`) a `[edi+0x50]` első hívásának (`0x008de9d0`) kimeneti paramétere, a hívás tölti ki. A `0x008de9b0` `sub esp,0x10` és négy `push`-a után a `[esp+0x14]` helyi változó; az első stack-paraméter a `[esp+0x24]`.

**A setter (C és asm, megerősített).** A `0x00714510` (17 bájt): `this+8 |= 4; this+0x37c = arg`. Ez a `+0xb0` slot célja a `CSelectionNode`, `CAlbumSelectionNode` és `CFoundFaceSelectionNode` vtáblákban (25. kör). Ha a `0x008debdc` által visszaadott receptor e három osztály egyike, a módérték (`+0x37c`) a `0x008de9d0` kimeneti paramétere.

**Eredmény.** A módérték nem literál a binárisban. A `+0xb0` írója feltételesen a `0x008debed`; az értéke a `0x008de9d0` hívás kimeneti paramétere, amelyet a `[edi+0x50]` állít elő. Ez a slot a `Fen::Win32WindowImp` vtáblájában (`0x00cced4c`) a `0x00a4a070`. Az `edi` osztálya feltételes (a 4.7/b szerint `Fen::Win32WindowImp` vagy leszármazott). A kimeneti érték konkrét 1 vagy 7 volta: NINCS MEG.

**Bizonyítottsági fok.** A pásztázás eredménye (0 és 9 találat): megerősített a teljes lineáris bejáráson; a bejárás dekódolása feltételes, mert a lineáris dekódolás elcsúszhat az utasításhatárokon. A hívóhely és a setter: megerősített (asm + C). A `0x00a4a070` mint slot-cél: feltételes. A módérték értéke: NINCS MEG.

**Cáfoló kísérletek.**
1. „A diavetítéshez tartozó függvénycsoportban van 1 vagy 7 literálú `+0xb0` hívás": cáfolva a kilenc találatra.
2. „A módérték-író a `call [reg+0xb0]` alakban van": cáfolva, ilyen alak nincs a `.text`-ben.
3. „A `0x008debed` literált ad át": cáfolva, kimeneti paraméter a forrás.

**Lezárás (#5225, 26. kör): (c).** A módérték-író helye megvan, az értéke nem konstans a binárisban. A `0x00a4a070` kérdéseit a 27. kör megválaszolta (4.7/d). A diavetítés-kapcsolat (a `0x008de220` dialógus azonosítása) külön nyitott, nem blokkoló.

#### 4.7/d A 27. kör (2026-10-20, #5225): a `0x00a4a070` slot nem ír kimeneti paramétert; a módérték ezen az úton 0 (feltételes)

**Kérdés.** (1) A `0x008de9d0`-ban (a `[edi+0x50]` első hívása) milyen értéket ír a kimeneti paraméterbe a módérték? (2) A `0x008debdc`-ben (a második `[edi+0x50]` hívás) visszaadott objektum osztálya?

**Forrás.** `.ghidra/2026-10-20-ghidra-27.txt` (a `0x00a4a070` C-törzse: `return *(undefined4 *)(param_1 + 4)`); asm (`annot_disasm.py`): `0x00a4a070` (4 bájt: `8b 41 04 c3`), `0x008de9b0` (694 bájt), `0x008d7550` (123 bájt), `0x008ddea0` (64 bájt); bináris-index: `rtti` (a `Fen::Win32WindowImp::vftable`, `0x00cced4c` 21. slotja, azaz +0x50, a `0x00a4a070`), `xrefs`.

**1. Az első hívás nem ír kimeneti paramétert (a Win32WindowImp-slotra, megerősített).**
- A `0x00a4a070` törzse `mov eax,[ecx+4]; ret`: a `this+4` mezőt adja vissza EAX-ben; a stack-argumentumot nem olvassa és nem írja.
- A `0x008de9b0` a kimeneti helyet a hívás előtt nullázza: `xor ebx,ebx` (@`0x008de9b9`), majd `mov [esp+0x1c], ebx` @`0x008de9cc`, a két `push` után. Ez ugyanaz a cím, mint a `lea eax,[esp+0x14]` @`0x008de9c1` által adott kimeneti paraméter (`push eax` @`0x008de9c5`). A slot nem ír, tehát a kimenet 0 marad.
- Az olvasás a `mov ecx,[esp+0x14]` @`0x008debde`, ez a `+0xb0` hívás argumentuma. Az esp-követés a `0x008debde`-ig nem teljes (több kilépési ág, köztük a `0x008deb92`-es `ret 8`), ezért a „0” feltételes.
- Következmény: a 26. kör állítása („az érték a `0x008de9d0` kimeneti paramétere”, 1 vagy 7) a Win32WindowImp-slotra cáfolva. Az `edi` dinamikus osztálya más +0x50 implementációval felülírhatná ezt. A `0x00a4a070`-et 25 vtábla használja, ezek is nem írnak kimenetet; a többi slot-implementáció nincs végigellenőrizve.

**2. A második hívás (0x008debdc) objektuma a `this+4` mező.** A slot a `this+4`-et adja vissza, és a `0x008debe4` ezt a `+0xb0` vtábla-hívás receptoraként használja. A `Fen::Win32WindowImp` konstruktora (`0x008ddea0`, a vtábla `0x00cced4c` írásával) első utasítása `mov [esi+4], eax`: a `+4` a konstruktor bemeneti `eax`-e. A konstruktort a `0x008d7550` hívja @`0x008d75bc`; az `eax` a `mov eax,[esp+8]` (@`0x008d75b8`) értéke, vagyis a `0x008d7550` 1. argumentuma. A `0x008d7550` és a `0x008ddee0` nem hívódik közvetlenül az indexben (közvetett hívás: vtábla vagy függvénymutató). Az objektum osztálya: NINCS MEG.

**Bizonyítottsági fok.** A Win32WindowImp-slot nem ír kimeneti paramétert: megerősített (4 bájtos törzs és asm). A kimenet értéke ezen az úton 0: feltételes (az esp-követés nem teljes). A `[edi+4]` objektum osztálya: NINCS MEG. A módérték 1 vagy 7 volta: NINCS MEG.

**Cáfoló kísérletek.** (1) „a `0x008de9d0` az 1 vagy 7 értéket írja ki”: cáfolva a Win32WindowImp-slotra, a slot nem ír. (2) „a `0x00a4a070` a kimeneti paramétert tölti”: cáfolva a 4 bájtos törzsből. (3) „a kimenet a hívás után íródik”: a hívás (`0x008de9d0`) és az olvasás (`0x008debde`) között nincs olyan írás, amely a kimeneti címet érné; az esp-követés nélkül ez feltételes.

**Lezárás (#5225, 27. kör): (c).** A kimeneti paraméter útja a Win32WindowImp-re lezárva (negatív eredmény). A `[edi+4]` osztálya nyitott, és az 1/7 módérték ebből dől el.

**Válasz (28. kör): NINCS MEG ésszerű lépésben.** Az első argumentum szerződése a binárisból megvan (a Win32WindowImp `this+4` mezője, lásd 4.7/e). A hívók viszont virtuális, közvetett hívások (874 hívóhely), a diavetítés dialógusának objektuma nem azonosítható, ezért a módérték (1 vagy 7) és a mag sem dől el. A lezárás a 4.7/e szakaszban.

#### 4.7/e A 28. kör (2026-10-20, #5225): a `0x008d7550` szerződése, vtábla-helye és hívói

**Kérdés.** Melyik objektum az első argumentuma (`mov eax,[esp+8]` @`0x008d75b8`), amit a diavetítés dialógusa ad; ebből a `+0x37c` módérték (1 vagy 7) és a mag.

**Forrás.** `.ghidra/2026-10-20-ghidra-28.txt` (`FUN_008d7550`: C-törzs, hívók, hívottak); asm: `annot_disasm.py` a `0x008d7550` (123 bájt) és a `0x008ddea0` (64 bájt) címre; bináris-index: `rtti`, `xrefs`, `functions`, `string_xrefs`; `find_data_refs.py 0x008d7550 --data`; bájtszintű pásztázás a `paszta.py` kapuján át (`memoria_kapu()` első lépésként).

**1. A szerződés (bináris, feltételes: egy út).**
- `ret 8` (@`0x008d75c2`, `0x008d75c8`): a függvény két stack-argumentumot vesz, a hívó nem takarít. Az `ecx` (this) nem olvasódik.
- A `push esi` (@`0x008d7570`) után a `[esp+8]` (@`0x008d75b8`) a bejövő első argumentum (a belépési `esp`-hez képest `[E+4]`). A második argumentumot (`[E+8]`) a 123 bájtos törzs egyetlen utasítása sem olvassa.
- A `call 0x008ddea0` (@`0x008d75bc`) az `eax`-ot adja át. A konstruktor első utasítása `mov dword ptr [esi+4], eax` (@`0x008ddea0`), a vtábla `0x00cced4c`, a visszatérési érték az új objektum (`mov eax, esi`, @`0x008ddedd`). Vagyis a Fen::Win32WindowImp `this+4` mezője az első argumentum.
- Ha a `0x0097c5d0(0x40)` foglalás nullát ad, a függvény nullát ad vissza (`je 0x8d75c5`).

**2. A vtábla-hely (megerősített, két független út).** A: a bináris-index `rtti` táblája szerint a `Fen::Win32::vftable` (`0x00cce3a4`) 5. tagja (`0x00cce3b8`, azaz `+0x14`) a `0x008d7550`; más vtáblában nincs. B: `find_data_refs.py 0x008d7550 --data` egyetlen találatot ad, ugyanerre a címre (`.rdata`). Közvetlen `call` vagy `jmp` a `0x008d7550`-re a teljes .text bájtszintű pásztázásában nincs. Tehát a hívók virtuális hívások, a vevő `Fen::Win32` (vagy a slotot örökítő) objektum.

**3. A hívóhelyek.** A teljes .text-ben a `mov R, [X+0x14]` ... `call R` alakú helyek száma 874 (a `call R` előtt legfeljebb 12 utasításon belül). Ebből 356-nál a 12 utasításos ablakban legalább két `push` áll, control-flow utasítás nélkül. Közvetlen `call [reg+0x14]` alak nincs (a találatok csak `[esp+0x14]`-re mutatnak). A `string_xrefs` szerint a `slideshow`, `diavet`, `BigSlide`, `ThumbUISlide` és `CDSlide` sztringeket használó 27 függvényben egyetlen jelölt sincs. Ez az index függvényhatáraira épül, ezért csak tájékoztató.

**Bizonyítottsági fok.** A szerződés (két argumentum, az első a `this+4`, a második nem olvasódik): feltételes, egy út (a két asm-törzs kézi olvasata; a Ghidra C nem adja a paramétert, `FUN_008d7550(void)`, így a második út hiányzik). A vtábla-hely (slot 5): megerősített (két út). A hívóhelyek halmaza: feltételes (12 utasításos ablak, index-függvényhatárok). A diavetítés hívója, a módérték (1 vagy 7) és a mag: NINCS MEG.

**Cáfoló kísérletek.** (1) „Van közvetlen hívója”: cáfolva, nincs `call` vagy `jmp` a célra. (2) „A diavetítés ága a sztringes függvények egyikében hívja”: a 27 függvényben nincs jelölt. Gyenge cáfolat, mert a függvényhatárokat az index adja, és a sztringhez tartozó függvény hiányozhat belőle. (3) „A második argumentum a módérték”: cáfolva, a törzs nem olvassa a `[E+8]`-at.

**Miért nem dönthető el ésszerű lépésben.** A dialógus-objektum azonosításához a 356 (vagy a 874) hívóhely vevőjét kellene visszakövetni: minden helyen a `[X]` vtábla-forrását, a konstruktort és az osztályt. Ez sok, egyenként visszakövetett hely. A mag (a `srand` magja, lásd 4.6 és a 13. kör) a 13. kör szerint egy lista elemének indexe, a lista eredete NINCS MEG, ezért futásidejű adatnak tekintendő. A módérték is a hívó futásidejű állapotából jöhet.

**#5225 „Kész, ha” pontjai (28. kör).**
- ✅ Képlet címekkel: a 4.4 és a 4.6 szakasz (`0x0076d900`, `0x0076d6f0`, `0x0076d7e0`, `0x00c08221`, konstanscímek). A kódban: `src/picasapy/app/slideshow_pan_zoom.py` (#5351). Greppel ellenőriztem (2026-10-20): a konstansok (0,75; 0,2; 0,1; 0,5; 0,499; 0,00001; 32768) és a négy eltolás előjele (`_eltolas`) egyezik a 4.4 táblájával. A tesztfájlt ebben a körben nem futtattam.
- ✅ Középre igazítás: nincs, sem a binárisban (4.4), sem a kódban.
- ⛔ Mag (a futás előtti CRT-állapot számszerűen): NINCS MEG. A kód docstringje is ezt rögzíti.
- ⛔ Módérték (1 vagy 7) és a dialógus-objektum: NINCS MEG.

**Lezárás (#5225, 28. kör): (a) a képletre; a magra és a módértékre nyitott (Nem része).** A megvalósítható rész (a képlet) kész és a kódban van. A mag és a módérték a binárisból ebben a körben nem dönthető el, ezért a „Nem része” pontba kerülnek. Új kutatási jegy kell hozzájuk (a jelentésben).

### A diavetítés vezérlősávja — mind a 39 eleme (`oneup`, 2026-08-16)

A korábbi szakasz a `slideshowctrls.tre`-t idézte (két elem). **Az igazi
vezérlősáv az `oneup`** — a teljes képernyős nézet alsó sávja, **39
elemmel** a `respack.yt`-ban.

### A sáv

| elem | pozíció | méret |
|---|---|---|
| `docbounds` / `rect: back` / `clip: base` | (0, 0) | **800 × 83** |
| `vbutton: auto2` | (0, 0) | 800 × 14 | *(a teljes szélességű felső kattintósáv)* |
| `caption: caption` | (**126**, 18) | **550 × 10** | a **felirat** a sáv fölött |
| `stripback` | (3, **33**) | **797 × 50** | a látható sáv |

### A vezérlők balról jobbra

| # | elem | x | méret | mi ez |
|---:|---|---:|---|---|
| 1 | `exit` (+ ikon 17 × 15, felirat **„Exit"**) | **36** | **74 × 35** | kilépés |
| 2 | `timeline` (+ ikon 26 × 9, felirat **„Timeline"**) | **107** | **157 × 35** | **Időrend** |
| — | `sszoomsliderclip` | 114 | 157 × 27 | nagyító-csúszka *(a `timeline` helyén, váltakozva)* |
| 3 | `rotateleft` | **276** | **26 × 34** | forgatás balra |
| 4 | `rotateright` | **312** | **26 × 34** | forgatás jobbra |
| — | `rect: centergroup` | 346 | **118 × 47** | a lejátszó-hármas kerete |
| 5 | `prev` | **353** | **26 × 30** | előző |
| 6 | **`auto`** (+ `auto_icon` 20 × 22) | **387** | **36 × 36** | **lejátszás/szünet** |
| 7 | `next` | **431** | **26 × 30** | következő |
| 8 | `star` | **458** | **27 × 33** | csillagozás |
| 9 | **`transtype`** | **498** | **143 × 21** | **az átmenet-választó** (legördülő) |
| 10 | **`captionbutton`** | **644** | **54 × 33** | **a feliratmód kapcsolója** |
| — | `dtclip` | 691 | 103 × 44 | a diaidő-blokk |
| 11 | `tpslabel` (**„Display Time"**) | 691 | 103 × 11 | |
| 12 | `minusone` (+ ikon 6 × 2) | **704** | **14 × 13** | diaidő **−** |
| 13 | `tps` (a szám) | 722 | 48 × 15 | |
| 14 | `plusone` (+ ikon 5 × 6) | **774** | **14 × 13** | diaidő **+** |

### A feliratmód: KÉT ikon, egy gomb

*Forrás: `oneup.tre:112` (`oneup/caption_icon`) · `oneup.tre:116` (`oneup/caption_yesicon`).*

```
oneup/caption_icon      (677, 49)  17x19   ← felirat KI
oneup/caption_yesicon   (678, 49)  16x18   ← felirat BE
```

A `captionbutton` **két ikonállapotot** vált — ez a jegy „feliratmód"
tétele. A felirat maga a **`caption`** elem (126, 18, **550 × 10**), a sáv
**fölött**, középre igazítva.

### A diaidő ± gombokkal

A `SlideshowEffectTime` (alapérték **3**) a sávon **`minusone`** /
**`plusone`** gombbal állítható, a `tps` mező mutatja az értéket. A
`globalbuttons/disp_n`/`_p`/`_h` képcsalád **14 × 13**.

### Kikommentezett, elhagyott elemek

```
#button(Auto Play,oneupbuttons/autonormal,…): auto   (362, 15)  79x24
#button: rotateleft                                  (270, 40)  38x35
#button: rotateright                                 (310, 40)  36x35
```

Az „Auto Play" gombnak **feliratos** változata is készült (79 × 24), és a
forgatógomboknak egy korábbi, nagyobb (38 × 35 / 36 × 35) verziója — mindet
kivették.

### ⚠️ A feliratok NINCSENEK lefordítva

`oneuptext.tre` **három** szöveget tartalmaz, angolul:
`tllabel` = „Timeline", `bcklabel` = „Exit", `tpslabel` = „Display Time".

Ugyanez a helyzet az `editoneup` változatban (a **szerkesztő** teljes
képernyős nézete), ami betűre ugyanezt a három szöveget hordozza.

> A „Timeline" hivatalos magyar megfelelője **másutt** létezik:
> `eMenuView::ID_VIEW_TIMELINE` → **„Időrend"**. A másik kettőre javasolt:
> **„Kilépés"** és **„Megjelenítési idő"**.

*Bizonyítottsági fok: megerősített* (a `respack.yt` 39 `oneup` rétege és az
`oneuptext.tre` teljes tartalma).

### 2.9 A filmkészítő FILMSZALAGJA és a négy csúszka (2026-09-01, UI-lefedettségi kör)

*A 2.6 a beállítás-leltárt adta, a 2.7 az előnézet-vezérlősávot. Ez a
szakasz a **filmszalag interakcióit**, a **négy csúszkát** és a
**projekt-állapotot** teszi hozzá — ezek eddig sehol nem szerepeltek.*

#### A filmszalag teljes interakció-készlete

A `0x006223b0` kezelő névparancsai — mind a filmszalagra vonatkoznak:

| név | mit jelent |
|---|---|
| `filmstripmove` · `filmstripselmove` | dia **áthelyezése** (egyedi és kijelölés) |
| `filmstripinsert` · `filmstripinsertnew` | **beszúrás** meglévő és új diával |
| `filmstripdragtoclips` | **húzás a kliptálcára** |
| `filmstripdeletedragged` · `filmstripdeletesel` | törlés húzással és kijelölésből |
| `filmstripdoubleclick` | **dupla kattintás** (a dia megnyitása) |
| `filmstripcontext` | **helyi menü** |

⇒ **A filmszalag teljes értékű fogd-és-vidd felület**, nem puszta
előnézet-sor.

#### A négy csúszka — mind ugyanabban a kezelőben

`durationslider` („Dia időtartama") · `transitionslider` („Átfedés") ·
`lengthslider` („Összes fénykép") · `burstslider` („Ne legyen szűrés a
készítés ideje alapján"), mind `…/scaleslider` alakban, ugyanabban a
`0x006223b0`-ban, a `video_control_bar2` hangerő- és pozíció-csúszkája
mellett.

⚠️ **A `burstslider` felirata félrevezető:** „Don't filter by time
taken" a csúszka **egyik végállása**, nem a funkciója. A csúszka a
sorozatfelvételek (burst) **időalapú ritkítását** állítja — a szélső
állásban nincs szűrés.

#### Projekt-állapot: automatikus mentés és visszatérés

A `0x0061df10` (az `insert_slide` és a `tab3` kezelője) három, eddig
nem dokumentált tételt hoz:

| bizonyíték | mit jelent |
|---|---|
| **`CMakeMoviePanel::autosave`** + `autosave` | a filmprojekt **automatikus mentése** |
| **`CMakeMoviePanel::back_to_slideshow`** — *„Back to Movie Maker"* | visszatérés a filmkészítőbe másik nézetből |
| `panelroot/makemovietab` · `panelroot/picasatab` | a filmkészítő **saját felső lapja** a panelgyökérben |
| **`Preferences\SupportMovies`** | kapcsoló: kezeljen-e a program mozgóképeket egyáltalán |

⇒ A filmkészítő **saját, menthető projekt** — nem egyszeri párbeszéd.
*(Ugyanaz a minta, mint a kollázsnál: `collage/autosave`, piszkozat.)*

**Bizonyítottsági fok: megerősített** a névparancsok és a kulcsok léte;
**nem mérve** a csúszkák értéktartománya és az automatikus mentés
időzítése.

#### A szakasz által lefedett vezérlők — TELJES ELEMNÉVVEL (2026-09-02)

| elem | mit azonosít | bizonyíték a szakaszban |
|---|---|---|
| `makemoviepanel/durationslider_label` | „Dia időtartama" | a négy csúszka, `0x006223b0` |
| `makemoviepanel/transitionslider_label` | „Átfedés" | ugyanott |
| `makemoviepanel/lengthslider_label` | „Összes fénykép" | ugyanott |
| `makemoviepanel/burstslider_label` | „Ne legyen szűrés a készítés ideje alapján" | ugyanott + a félrevezető felirat magyarázata |
| `makemoviepanel/insert_slide` | „Új szöveges dia" | a `0x0061df10` névparancsa |
| `makemoviepanel/remove_slide` | „A kijelölt dia eltávolítása" | a `filmstripdeletesel` névparancs (`0x006223b0`) |
| `makemoviepanel/viewedit` | a filmszalag mint szerkesztő felület | a nyolc `filmstrip*` névparancs |

⚠️ **Amit ez a szakasz NEM fed le:** `addtomovie` és `deleteclips` — a
**kliptálca** két gombja. A szakasz a filmszalag húzási parancsait adja
(`filmstripdragtoclips`, `filmstripdeletedragged`), a tálca-oldali
gombokat nem; a „Továbbiak…" belépési pontja külön lapon van
([`getmore-klipgyujto-mod.md`](getmore-klipgyujto-mod.md) 1.1).

### 2.11 ⭐ A `makemoviepanel` TELJES ELEMLELTÁRA — és a VALÓDI hiánylista (2026-09-06)

A UI-lefedettségi rangsor a `makemoviepanel`-t **49 feltáratlan elemmel** hozza
az első helyre. Ez a szakasz **megméri**, mennyi ebből valódi hiány.

**A mérés:** a `makemoviepanel.tre` **102** elemnevet deklarál
(`^makemoviepanel/<név>:` sorok, egyedi). Ezek közül a `docs/specs/*.md`
**60**-at említ **teljes néven**; **42**-t nem.

#### A 42 nem említett elem — osztályozva a `.tre` szülőviszonyából

| csoport | darab | elemek | építendő? |
|---|---:|---|---|
| **ikon-gyerek** (egy már dokumentált gomb ikonja/felirata) | 12 | `add_icon` (`addtomovie`), `back_icon` (`addclips`), `bold_icon` (`bold`), `delete_icon` (`deleteclips`), `export_youtube_icon` (`export_youtube`), `inserticon` (`insert_slide`), `italic_icon` (`italic`), `outline_icon` (`outline`), `removeicon` (`remove_slide`), `bgcolorpicker_bevel` (`backcolor`), `txcolorpicker_bevel`, `show_captions_label` (`show_captions`) | **nem** — a gazdájuk része |
| **konténer / vágókeret / alaplap** | 15 | `basepanel` (root), `insetleft`, `filmbase`, `filmclip`, `filmcontainer`, `filmoverlaycontainer`, `infotext_clip`, `previewpanel`, `moviebk`, `movieparent_tracker`, `video_control_container`, `audioclip`, `tabs`, `tabpanel1`, `tabpanel3` | **nem** — szerkezet |
| **csúszka-tok** (a csúszka maga dokumentált) | 4 | `burstslider_container`, `durationslider_container`, `lengthslider_container`, `transitionslider_container` | **nem** |
| **elválasztó / osztóvonal** | 4 | `sepA`, `sepB`, `vdiv1`, `vdiv2` | **nem** — dísz |
| **kezdetben rejtett** (`m_hidden`) | 4 | `backcolor`, `movieparent`, `previewimage`, (+ a `tabpanel1`/`tabpanel3` a fülváltás miatt) | **feltételes** |
| **VALÓDI, eddig nem dokumentált** | **3** | **`albumname`**, **`indicator`**, **`audiostrip`** | **igen** |

⇒ **A panelre a tényleges hiány három elem, nem 49.**

#### ⛔ HELYESBÍTÉS (2026-09-06, 6. kör): a rangsor száma NEM a szerkezeti elemektől nagy

Ez a szakasz eredetileg így zárult: *„a rangsor száma a szerkezeti elemeket
is beszámolja."* **Ez az állítás HAMIS**, és az egész összevetés
alma-körte volt.

**Mi dönti el:** a `ui-lefedettseg.md` fogalmi szakasza. A rangsor száma
`feltáratlan + lekutatva + bizonytalan`, és **kizárólag az „értékelhető"
elemekre**; a `rajzoló` osztály (`nem-ertekelheto`) — a teljes leltár
**1284** eleme — **eleve ki van hagyva** belőle. A `makemoviepanel` sora
(`ui-lefedettseg.md:76`): 111 elem, ebből **55 értékelhető**, **56 rajzoló**;
a 49 = **0 feltáratlan + 43 lekutatva + 6 bizonytalan**.

**Tehát a két szám nem ugyanazt méri:**

| | ez a szakasz (2.11) | a lefedettségi rangsor |
|---|---|---|
| mit számol | **említi-e a `docs/specs/`** teljes néven | **megépítettük-e** QML-ben |
| a 42 / 49 jelentése | nincs dokumentálva | nincs megvalósítva |
| a `rajzoló` elemek | benne vannak | **kihagyva** |

A `makemoviepanel` **feltáratlan** száma a mérés szerint **0** — a 49 mind
**`lekutatva`**, azaz **fejlesztői**, nem kutatói munka. Az itteni leltár
attól még érvényes lelet (a három elem valóban hiányzott a specekből), de
**nem cáfolja és nem javítja a rangsort.**

#### A három valódi elem — MŰKÖDÉS

| elem | mit tudunk | bizonyíték |
|---|---|---|
| **`makemoviepanel/albumname`** | felirat a **1. fülön** (`m_displayfont12`, `XConstraint 0, 0, 35`, `Property textwrap 0`); a szövegét **két** függvény állítja | sztring `0x00c9c9e8`; hivatkozók `0x0061a6c0` (429 b), `0x0061bbd0` (614 b) |
| **`indicator`** | a **filmszalag lejátszásjelzője**: a `filmstrip` gyereke, vízszintesen középre kényszerítve (`m_centerX`, `YConstraint 0, 0, 0`); a húzás-/találatkezelő kiszámolja a **téglalapja közepét** (`(x0+x1)/2`, `(y0+y1)/2`) | sztring `0x00c9c52c`; a panelépítő `0x00613b50` és a kezelő **`FUN_006214e0`** (2020 b): elemkeresés `0x0062166b`, középpont `0x00621684`–`0x006216c1` |
| **`audiostrip`** | a filmszalaggal párhuzamos **hangsáv-csík** (`audioclip` → `filmcontainer`, `m_scaleXY`) | csak a `.tre` |

#### ⛔ NEGATÍV LELET: az `audiostrip` és az `audioclip` nevére NINCS kódhivatkozás

A `string_xrefs` szerint a `makemoviepanel/audiostrip` és a
`makemoviepanel/audioclip` **egyetlen** függvényből sem kerül elő névvel —
szemben a `filmstrip`-pel (`0x00613b50`), az `indicator`-ral
(`0x00613b50`, `0x006214e0`), a `previewimage`-dzsel (`0x00618050`,
`0x0061ca80`), a `makemoviepanel/backcolor`-ral (`0x00621240`) és a `show_captions`-szel
(`0x00618050`, `0x0061df10`).

⇒ **A hangsáv-csíkot a kód sosem kéri le a nevén.** Vagy a szülőjén
keresztül vezérli, vagy **maradvány** a fájlban. Ez nem azt jelenti, hogy a
felületen nincs ott — csak azt, hogy **nevesített kezelője nincs**.

> **Bizonyítottság:** **megerősített** a 102-es elemszám, a 60/42-es
> megoszlás, az osztályozás (a `.tre` szülőviszonyából) és a sztring-xref
> jelenléte/hiánya; **erős** az `indicator` „lejátszásjelző" olvasata (a
> geometriai kényszer + a középpontszámítás együtt, futásidejű
> megerősítés nélkül).

#### A korábbi öt „bizonytalan" elem státusza — LEZÁRVA (#3328)

A lefedettségi mérés öt, felirat nélküli elemet `bizonytalan`-ként hagyott: `previewimage`, `previewpanel`, `tabs`, `tabpanel1` és `tabpanel3`. A `makemoviepanel.tre` szülő- és állapotsorai ezt közvetlenül eldöntik:

| elem | mért szerep | bizonyíték |
|---|---|---|
| `makemoviepanel/previewimage` | a `moviebk` rejtett gyereke; az előnézeti kép rétege, önálló parancs nélkül | `makemoviepanel.tre:15–16`, `m_hidden` |
| `makemoviepanel/previewpanel` | az `insetleft` előnézeti területe; a `moviebk` ennek gyereke, tehát tartó/klipkeret | `makemoviepanel.tre:515–520` |
| `makemoviepanel/tabs` | az `edittabbase` alá kötött fülsáv-tartó | `makemoviepanel.tre:554–565` |
| `makemoviepanel/tabpanel1` | az első, „Movie" fül tartalma; a `tab1` `showtarget`-je | `makemoviepanel.tre:103–111`, `:267–269` |
| `makemoviepanel/tabpanel3` | a harmadik, „Options"/„Klipek" fül tartalma; a `tab3` `showtarget`-je | `makemoviepanel.tre:402–410`, `:509–511` |

⇒ Ezek **nem önálló felhasználói vezérlők**, hanem a már feltárt filmkészítő panel szerkezeti vagy rejtett rétegei. A kutatási státuszuk `lekutatva`; a filmkészítő panel megépítése továbbra is fejlesztési munka a #432-ben, nem új kutatási kérdés.

### 2.12 ⭐ A `makemoviepanel` PARANCS-ELOSZTÓJA — mind a 34 parancs, és a `rewind` MŰKÖDÉSE (2026-09-06)

⛔ **Egy korábbi kör lezárása MEGDŐLT.** A `00-index.md` 2026-09-05-i
bejegyzése azt írta a `makemoviepanel/rewind` gombról, hogy **„NINCS MÉRVE,
mit csinál a gomb kattintásra (az olcsó lánc kimerült)"**. A lánc **nem**
merült ki: a kör a **minősített** nevet (`makemoviepanel/rewind`) kereste, az
elosztó viszont a **puszta** nevet hasonlítja (`rewind`, `0x00c9d3dc`) —
és az egyetlen hivatkozója a **`FUN_0061df10`** (12 420 b), a panel
**parancs-elosztója**.

#### A 34 parancs, az elosztó sorrendjében

Minden tétel egy `mov esi, <névsztring>` + `repe cmpsb` összehasonlítás:

| # | cím | parancs | | # | cím | parancs |
|---:|---|---|---|---:|---|---|
| 1 | `0x0061df56` | `recompute` | | 18 | `0x0061f0a6` | `1to1` |
| 2 | `0x0061e17f` | `render` | | 19 | `0x0061f12c` | `show_captions` |
| 3 | `0x0061e1e0` | `cancel` | | 20 | `0x0061f20a` | `crop_to_fit` |
| 4 | `0x0061e241` | `export_youtube` | | 21 | `0x0061f335` | `remove_low_res_faces` |
| 5 | `0x0061e2a2` | `play` | | 22 | `0x0061f396` | `smart_order_radio` |
| 6 | `0x0061e303` | `pause` | | 23 | `0x0061f3f7` | `album_order_radio` |
| 7 | **`0x0061e364`** | **`rewind`** | | 24 | `0x0061f458` | `chronological_order_radio` |
| 8 | `0x0061e48c` | `add_audio` | | 25 | `0x0061f4b9` | `tab1` |
| 9 | `0x0061e8b7` | `.mp3` (kiterjesztés-ág) | | 26 | `0x0061f51a` | `tab2` |
| 10 | `0x0061ea4e` | `remove_audio` | | 27 | `0x0061f57b` | `tab3` |
| 11 | `0x0061eaff` | `next` | | 28 | `0x0061f5dc` | `addclips` |
| 12 | `0x0061eb60` | `prev` | | 29 | `0x0061f6d4` | `addtomovie` |
| 13 | `0x0061ebc1` | `insert_slide` | | 30 | `0x0061f972` | `deleteclips` |
| 14 | `0x0061ed77` | `remove_slide` | | 31 | `0x0061fae4` | `bold` |
| 15 | `0x0061edfc` | `viewedit` | | 32 | `0x0061fb8c` | `italic` |
| 16 | `0x0061ef90` | `fullscreen` | | 33 | `0x0061fc2c` | `outline` |
| 17 | `0x0061f012` | `aspectratiochk` | | 34 | `0x006206be` | `autoplay` |

⇒ **Ez a panel teljes vezérlő-készlete a MŰKÖDÉS oldaláról** — a `.tre`
elemlistája (2.11) mellé most a parancslista is megvan.

#### A `rewind` — utasításonként (`0x0061e3b7`–`0x0061e45a`)

```
0x0061e3bb  mov edx, 0xc9bea4              ; "video_control_bar2/moviecontrols/pause"
0x0061e3c0  mov byte [esi+0x498], 1        ; „programozott változtatás" jelző BE
0x0061e3c7  call 0x9cd8a0                  ; ⇒ a PAUSE elem AKTIVÁLÁSA
0x0061e3cc  mov edx, [esi+0x494]           ; a KIJELÖLT dia indexe
0x0061e3da  mov eax, [esi+0x4bc]; add eax,0x48
0x0061e3e3  call 0x611320                  ; a klip-lista zárolt lekérdezése
0x0061e3e8  cmp dword [esi+0x4a0], 0       ; van-e lejátszó?
0x0061e3ee  je  0x61e42e                   ;   ha nincs, kihagyja
0x0061e407  call 0x80ff20                  ; a dia KEZDŐ IDŐPONTJA (float, mp)
0x0061e410  fmul qword [0xcf3e88]          ; × 10 000 000 ⇒ 100 ns-os egység
0x0061e420  call 0xc299c6                  ; float → 64 bites egész
0x0061e42c  call [edi+0x5c]                ; a lejátszó POZÍCIÓ-BEÁLLÍTÁSA
0x0061e432  mov eax, [edi+0x494]
0x0061e439  mov [edi+0x388], eax           ; az AKTUÁLIS dia := a KIJELÖLT dia
0x0061e43f  mov byte [edi+0x498], 0        ; a jelző KI
0x0061e445  call 0x619ac0                  ; felület-frissítés
0x0061e44c  call 0x61ca30
```

**Emberi nyelven:** a gomb (1) **megállítja a lejátszást** — nem közvetlenül,
hanem a `video_control_bar2/moviecontrols/pause` elem **aktiválásával**
(`FUN_009cd8a0` névre keres a felületi fában, majd a `[vtbl+0x78]`
metódust hívja rajta); (2) kiszámolja a **kijelölt dia kezdő időpontját**;
(3) a lejátszót oda **tekeri**; (4) az „aktuális dia" mezőt a kijelöltre
állítja; (5) frissíti a felületet. A `+0x498` jelző a menet idejére be van
kapcsolva — ez akadályozza meg, hogy a saját pozíció-változtatás
visszahasson a kijelölésre.

**Az időegység:** `0x00cf3e88` = **10 000 000,0** — a lejátszó tehát
**100 nanoszekundumos** egységben kapja a pozíciót (a Windows-os
médiaidő szokásos egysége).

#### ⛔ HELYESBÍTÉS: a `0xF4240` visszatérési kód NEM jelent semmit

Egy 2026-09-06-i korábbi kör (`picasa-imagedata-rekord.md`) úgy írta le a
`facerect == 1` ágat, hogy az „**saját** visszatérési kóddal" (`0xF4240` =
1 000 000) tér vissza — mintha ez az ág megkülönböztető jegye volna.
**Nem az.** A `mov eax, 0xF4240` a `.text`-ben **809** helyen szerepel — a
`rewind` ág is ezzel zár (`0x0061e45a`) —, tehát ez a program **általános
„kezeltem / rendben" kódja**, nem az adott ág sajátja.

**Bizalmi fok: megerősített** — minden lépés utasításonként olvasva.
⛔ **Amit NEM mértem:** a `FUN_0080ff20` belső képlete (hogyan számol
kezdő időpontot a klip-listából), és a `[vtbl+0x78]` metódus neve.

### 2.10 A `titledialog` — a szöveges dia szerkesztője (2026-09-01)

*A 2.9 megtalálta az `insert_slide` névparancsot („Add a new text
slide"); ez a szakasz a mögötte álló **párbeszédet** írja le. A
2.5/b már rögzítette, hogy az **újraszámítás eldobja a kézzel felvett
szöveges diákat** — az a figyelmeztetés ehhez a funkcióhoz tartozik.*

#### A párbeszéd vezérlői (elemleltár, `titledialog`)

*Forrás: `titledialog.tre` — a sorszámok a felületleíró saját sorai.*

| elem | felirat | `titledialog.tre` |
|---|---|---|
| `titledialog/previewimage` · `titledialog/previewtext` | a dia **élő előnézete** (szöveg + háttér) | `titledialog.tre:20` |
| `titledialog/stylelist` | a dia **stílusa** | `titledialog.tre:14` |
| `titledialog/sizelist` | a **betűméret** | `titledialog.tre:37` |
| `titledialog/captionchk` | jelölőnégyzet — a **képfelirat** átemelése | `titledialog.tre:40` |
| `titledialog/add` · `titledialog/cancel` | „Add" / „Cancel" | — |

⇒ A szöveges dia **nem puszta szövegmező**: stílus- és
méretválasztóval, élő előnézettel, és azzal a lehetőséggel, hogy a
szöveg a kép **feliratából** jöjjön (`titledialog/captionchk`).

#### Az infósor a filmkészítőben

A `0x0061be40` a `makemoviepanel/infotext` tartalmát építi:

| formátum | mit mutat |
|---|---|
| `%s     %dx%d pixels` | a dia neve és **képpont-mérete** |
| `(%d of %d)` | a dia **sorszáma** a filmben |
| **`Text Slide`** | a szöveges diák neve a listában |

⇒ A szöveges dia a filmszalagon **„Text Slide" néven** jelenik meg, és
az infósor ugyanúgy mutatja a méretét és a helyét, mint a fotókét.

**Bizonyítottsági fok: megerősített** a vezérlőkészlet és a
formátumsztringek; **nem mérve** a `stylelist` és a `sizelist` konkrét
értékkészlete.

> ⚠️ **A kapcsolódó romboló figyelmeztetés már dokumentálva van** a
> **2.5/b** pontban (`askapplyconfirm`, *„This will generate a new movie
> removing all the text slides you added. Are you sure?"*) — ez a kör
> **nem** találta meg újra, csak összeköti vele a szöveges dia
> funkcióját. Aki a `titledialog`-ot megvalósítja, annak a
> figyelmeztetést is meg kell építenie, különben a felhasználó kézi
> munkája némán elveszik.

### 2.10/b A három animált szövegdia-stílus — ami bizonyított, és ami nyitott (2026-10-12, #4615)

*Állapot: **NYITOTT; első rögzítés, részben frissítve a G.7.8-ban.** A három stílus referenciafilmes menete nincs megmérve. A G.7.8 a binárisból már kiolvasható animációs szerkezetet és az időút egy részét rögzíti; a képkockánkénti egyezéshez szükséges seed, XML→render-desc másolás és geometria továbbra is nyitott.*

#### A) Bizonyított

| tény | forrás |
|---|---|
| A három stílus azonosítója: `textstyle8` = Gördülő stáblista, `textstyle11` = Képfelirat – Írógép, `textstyle1` = „I'm Feeling Lucky" (magyarul „Jó napom van") | `referencia/stringres-en-hu.tsv`; `string_xrefs.csv`: mindhárom név a `0x00613b50` (a stílus-lista építője) hivatkozása |
| A mentett `.mxf`-ben a stílus a `<styleid>` (0–11) mezőben van, a szövegdia betűparaméterei a `textparm` alatt: `fontname`, `size`, `color`, `weight`, `italic`, `outline`, `styleid`, `facerect*` | `string_xrefs.csv`: a `0x00816440` (átmenet-író) és a `0x008152f0` (beolvasó) sztringjei; 2.4/b szakasz |
| A diánkénti idő a `trans` elemben van (`advanceinterval`, `transitiontime`, `blacktime`), **nem** a szövegdia-elemben | 2.4/b szakasz |
| A mentett formában **nincs** sebesség-, irány-, karakteridő- vagy kurzor-mező. Ez a mentési szerkezet tartalma; az animáció paraméterei tehát a megjelenítő kódban vannak, vagy kódba égettek | 2.4/b szakasz (a felsorolt mezők teljes listája) |

#### B) Név-ütközés: két különböző „Jó napom van"

A `enhance` képi művelet (automatikus javítás, `ID_PICTURE_ENHANCE`) is a magyar „Jó napom van" nevet viseli (lásd `picasa-native-filter-workers.md`, `picasa-hu-terminology.md`). A szövegdia `textstyle1` stílusa **más dolog**, csak ugyanazt az angol „I'm Feeling Lucky" eredetet fordítja. Az animációs kérdésnél a kettőt nem szabad összekeverni: a képi `enhance` nem animál, a szövegdia-stílus viselkedését csak a szövegdia-megjelenítőben lehet megtalálni.

#### C) Nyitott — az első kör kérdései (a G.7.8 részben megválaszolja őket)

1. **Gördülő stáblista:** a smoothstep képlete és az `advanceinterval` mező megvan (G.7.8.3); a pixel-végpontok, irány és sebesség tényleges értéke, továbbá a render-desc XML-forrása nyitott.
2. **Írógép:** a bájtszám-alapú képlet megvan (G.7.8.3); a `k→t` leképezés, a több-bájtos szöveg glyph-viselkedése és a kurzor kérdése nyitott.
3. **„Jó napom van” (`textstyle1`):** az első körben nem volt ismert, mit animál; a G.7.8.3 alfa- és egydimenziós pozíció-animációt igazol, de a mozgás végpontja/időtartama és a képkockánkénti érték továbbra sincs meg.

#### D) A megszerzés útja

- **Bináris:** az első kör csak a stílusazonosítót ismerte. A render-factoryt, a három kezelő útját és a DirectShow-pin időátadását a G.7.8 utasításszinten részben összeköti; az XML-adatok élő render-desc-be másolása és a teljes exporthívási lánc továbbra is nyitott.
- **Mérés (ez adja a számokat):** az eredeti Picasa 3.9 fut Colabon (Wine alatt), egy-egy szövegdia mindhárom stílussal, filmre exportálva; a kimenetből képkockánként kimérni a pozíciót és a megjelenést. Ez a `#4615` jegy kommentjében már kijelölt út. Ennek hiányában a menet nem írható le.

#### E) Mai kód (2026-10-12)

- `src/picasapy/movie/slideshow.py:406–470` (`_szovegdia`): minden stílus **álló kép**. A 2, 3, 11 alul, a 9 bal szélen, a 10 jobb szélen, a 4–7 sávban, a többi (0, 1, 8) középen. A 8 és az 1 ugyanúgy álló kép, mint a 0; a 11 ugyanúgy, mint a 2.
- `slideshow.py:623`: a szövegdiák **egyszer**, előre renderelődnek (`text_frames`), így egy állóképként, nem kockánként.
- `slideshow.py:679–700`: a szövegdia ugyanazt a tartási időt kapja, mint a fotó (`frames_per_photo − transition_frames`), nem a mentett `advanceinterval`-t. Ez külön eltérés, nem a stílus-animáció része.

#### F) Kész, ha — a korábbi vázlatot a G.7.8.5 pontosítja

Az elfogadási feltételek a kódból kiolvasott képleteket követik; a referenciaexport adja meg a film-kockákhoz kötött értékeket. Az előző vázlat lineáris `y(k)` és `n(k)` képletei nem tekinthetők natív viselkedésnek.

- [ ] **Mérés megvan és dokumentált:** `docs/benchmarks/` alatt az exportbeállítás, a natív kocka-időbélyegek, a vizsgált kockák és a három stílus mért pozíció/alfa/szöveg-állapota.
- [ ] **Gördülő (8):** a G.7.8.3 `B + S(p)·(A−B)` smoothstep-képlete fut; a kocka `t`-je, a live `advanceinterval`, valamint A/B geometriája igazolt. Pixel/s értéket csak a tényleges A/B és duration méréséből szabad közölni.
- [ ] **Írógép (11):** `n(t)=max(1,trunc(len·clamp((t+0.02−L)/d,0,1)+0.5))`; `len` bájtszám, `d=transitiontime`, nulla esetén `advanceinterval/3`. A `k→t` leképezés és a látható glyph-szám külön ellenőrizve; kurzor csak akkor specifikálható, ha a referencia mutatja.
- [ ] **„Jó napom van” (1):** az alfa 0→255 lineárisan, a pozíció egy komponense smoothstep-pel animál; a duration, végpont, tengely és kocka-időkapcsolat pontosan feloldva vagy mérve.
- [ ] **A kockák renderelése k szerint:** `_szovegdia`/az export render út minden textslide kockát a kimeneti ciklusban állít elő `k` alapján; a régi egyszeri `text_frames`-előrenderelés nincs.
- [ ] **Kimenet-teszt:** a három stílus mért referenciakockái összevetve a helyi kimenettel; az eltérési tolerancia a mért képekből származik. A kockaszám és a `holds` viselkedése megőrzött.
- [ ] **Időmezők:** a mentett `trans` mezők tényleges bekötése lezárt; az `advanceinterval`-ből eredő diahossz-eltérés külön kezelési tételként marad.

#### G) 2. kör (2026-10-12): a rajzoló azonosítása — ami most bizonyított, és ami még nincs

*Állapot: a **rajzoló szerkezete** megvan (osztályok, konstruktorok, a stílus-elágazás helye, a képkocka-függvény szerkezete). **A görgetés sebessége és a karakteridő számértéke még nincs kiolvasva**, mert az idővonal-összegző (`0x009e5e70`) pontos kiértékelése hiányzik. Ez a szakasz nem ad számot.*

**⚠️ ELLENTMONDÁS a 2.10/b szakasz A) pontjával — a kör ezt NEM simította el:** a `TextTypeWriterHandler` vtáblája a spec szerint `0x008bdbbc`. A binárisban az RTTI (COL-mutató, `vtable-4`) és a konstruktor írása (`mov [esi], 0x00cbdbbc`, `0x00809fe0`) **`0x00cbdbbc`-t** mutat, és a `0x008bdbbc`-n lévő bájtok nem függvénymutatók. Ugyanígy a `CRenderMovie` spec-vtáblája (`0x0089e07c`) mért értéke `0x00c9e07c`. Mindkettő pontosan `0x400000`-lal tér el. A **kódcímek** a specben (`0x008152f0`, `0x00816440`, `0x00613b50`) viszont egyeznek a `.text` tartalmával, tehát az eltérés csak a vtábla-címekre igaz. A kör a **mért** címeket használja; a régi vtábla-címek (0x400000-val eltolt alapból felírva) a fenti bekezdésben javítva.

#### G.1 Bizonyított — a három szövegdia-kezelő osztálya

Az RTTI-sztringekből (`.?AV…@@`, a TypeDescriptor = sztring − 8, a COL a TD-re mutat, a vtábla = COL-mutató + 4) mért megfeleltetés:

| osztály | vtábla (mért) | slotok | konstruktor | per-frame (slot 3) |
|---|---|---|---|---|
| `TextTypeWriterHandler` | `0x00cbdbbc` | 4 | `0x00809fe0` (float, `eax` = szövegének hossza) | `0x0080a080` |
| `TextFadeHandler` | `0x00cbdb80` | 4 | `0x00809af0` (float; `al` = A, `cl` = B bájt) | `0x00809b40` |
| `TextFadeMoveHandler` | `0x00cbdb94` | 4 | `0x00809c50` (float + két float; `al`, `cl`) | `0x00809d20` |

A slot 0 a `TextFade`-nél és a `TypeWriter`-nél azonos (`0x0080a150`, a `[esi+0x20]` objektum felszabadítása és a vtábla `0x00c80918`-ra írása). A slot 1 és 2 (`0x009d79f0`, `0x009d7a00`) minden három osztályban közös: a `[ecx+4]`-es tag felszabadítása (a `0x009d7a00` ugyanezt végzi, és a tag törlése után `push 1`-gyel hívja a vtábla slot 0-ját, azaz a törlő-slotot). A `TextFadeMoveHandler` slot 0 más (`0x00809e00`).

A `CRenderMovie` (RTTI TD `0x00d400b4`) négy COL-ja (többszörös öröklés) ugyanazokat a vtábla-mutatókat adja, mint a spec-jegyzet: `0x00c9e07c`, `0x00c9e0b4`, `0x00c9e0d0`, `0x00c9e0dc`. A `CTranscodeMovie` (`0x00d40094`) vtábla-családja: `0x00c9e100`, `0x00c9e138`, `0x00c9e154`, `0x00c9e160`.

#### G.2 Bizonyított — ki példányosít, és a stílus-elágazás

- **Gyár:** a szövegdia-szöveget építő függvény a `0x00810420` (a `push ebp`-es belépő; a 0x810420-tól 0x811e51-ig terjedő egy függvény). Hívói: `0x008128aa`, `0x008128e8`, `0x0081293d`, `0x0081380c`, `0x0081388d`, `0x008138bf`. Ezek a hívók még **nincsenek** azonosítva (melyik `CRenderMovie`-metódus), ez a 2. kör nyitott pontja.
- **Elágazás:** a dia `[ebx+0x44]` mezője a stílus-azonosító (`0`–`11`); `test eax,eax` (`0x00810596`) → `cmp eax,1` (`0x00810656`) → `cmp eax,2` (`0x00810a40`) → … → `cmp eax,6/7/0xb` (`0x00810ea3`, ugrás `0x00811a27`-re) → `cmp eax,8` (`0x00810ed3`) → `cmp eax,9`, `cmp eax,0xa` (`0x00811031`) → az alapág `0x00811e4a`.
- **Stílusonkénti konstruktor** (a belső ugrásokból):
  - `0` (az alapág, `0x00810596` után) → `TextFadeHandler` (`call 0x809af0`, `0x0081061b`), `al = 0`, `cl = 0xff`.
  - `1` ("Jó napom van", `textstyle1`) → `TextFadeMoveHandler` (`call 0x809c50`, `0x008107a7`).
  - `8` (Gördülő stáblista) → `TextFadeMoveHandler` (`call 0x809c50`, `0x00810fee`), a három float-argumentum: `[ebx+0xe8]`, egy egész `[esp+0x50]`-ből, és `0,5 ×` egy egész `[esp+0x18]`-ből (`0x00810fc9`: `fmul [0x00c72150]`, a `0,5`).
  - `11` (Képfelirat – Írógép) → `TextTypeWriterHandler` (`call 0x809fe0`, `0x00811db7`/`0x00811dca`). A `cmp dword ptr [ebx+0x44], 0xb` a `0x00811cd8`-on van; `sete cl`, `test cl,cl`, `jne 0x811d64` → a `0x809fe0` ág csak `11`-re.
  - `6`, `7` és a többi a `0x00811cf0`-ágon → `TextFadeHandler` (`0x809af0`).
  - **Nem vizsgált:** `2`–`5`, `9`, `10`, és hogy a `0x00810b7c`, `0x00810e1d`, `0x0081122f`, `0x008114c5`, `0x00811993`, `0x0081202a` hívások melyik stílushoz tartoznak. *(2026-10-12: részben megvan, lásd G.6.5.)* A `0x00809af0`-t ezek is hívják, a `0x00809c50`-et a `0x008109eb` is.

#### G.3 Bizonyított — az animáció szerkezete (képkocka-függvény)

Minden per-frame függvény (`0x0080a080`, `0x00809b40`, `0x00809d20`) ugyanazzal a szerkezettel indul:

1. `dynamic_cast` a célobjektumra (`call 0x00c07db2`, a típusleírók `0x00d3eea4`/`0x00d3b8a0`, illetve `0x00d3ef9c`).
2. Az eseményrekord `[edi+8] == 0x13` (az esemény típusa), különben kilép.
3. A handler `[ebx+8]` float (a ctor-argumentum, a **szegmens hossza**) `> 0`; `fcomp`/`jp` (NaN vagy ≤ 0 esetén kilép).
4. `t = [edi+0x10]` (double, az eseményidő) és `0x009e5e20(this+0x10 (TypeWriter/Fade) vagy +0x30 (FadeMove), t)` — ha 1, kilép (ez az „idő még nem jött el / már lejárt” ellenőrzés; a `0x009e5e20` a `[ecx+0x14]>>1` darabszámú szegmensen fut).
5. `P = 0x009e5e70(this+0x10 …, t)` — az idővonal-kiértékelő (double).

**A TypeWriter kimenete (bizonyított lépések):**

- `0x0080a030` (a TypeWriter idővonal-építője) egyetlen szegmenst ír: kezdet `t0 = a ctor-argumentum` (`[esp+0x2c]`), vége `t1 = t0 + [this+8]`, az érték-amplitúdó **`[this+0xc]`** = a szöveg hossza (`fild`, a negatív egész-korrekcióval), az interpolátor a **identitás** (`0x00809ae0`: `fld [esp+4]; ret`), vagyis a szegmens-függvény `f(p) = p`.
- A képkocka-függvény: `n = fistp(P + 0,5)` (`0x0080a0f0`: `fadd [0x00c72150]`, a `0,5`), `n == 0` → `n = 1`, majd `[esi+0x34c] = n` (a megjelenített karakterek száma) és `[esi+0xc] |= 7` (újrarajzolás), ha változott.
- Vagyis a látható karakterek száma `n(t) = max(1, round(P(t)))`, és `P` a `0x009e5e70` kimenete.

**A Fade/FadeMove kimenete:** a `0x00809eb0` (Fade idővonal-építője) és a `0x00809d20` (FadeMove) ugyanilyen szegmenst építenek, de a `+0xc`/`+0xd` bájtokkal (`A` = 0, `B` = `0xff` a Fade-nél). A `FadeMove` a `P`-t a `[esi+0x14c]`, `[esi+0x150]` float-párok közti interpolációra (`0x009debd0`) használja. **A `0x009debd0` nincs kiolvasva**, ezért a pozíció-képlet nincs bizonyítva.

#### G.4 NYITOTT — ami még hiányzik a számhoz

| kérdés | mi kell hozzá | állapot |
|---|---|---|
| `P(t)` pontos képlete | a `0x009e5e70` szegmens-összegzés (a `0x009e5f03`–`0x009e5f71` ciklus) kiértékelése: az `fmulp` mit szoroz, és a `t0`/`t1` honnan jön (a `0x009e6010` szegmens-építő, `0x009e5b20` a darabszámolás) | **megvan** (G.6.1–G.6.2, natív mérés) |
| Írógép karakteridő-üteme | `P(t)` ismeretében `n(t)`; a karakter/s = `len / dur` csak akkor, ha `P` lineáris — ez **nem bizonyított** | **képlet megvan** (G.6.3: lineáris, `f` = identitás); bemenetei (`d`, `L`, `t` nulla pontja) nyitottak (G.6.6) |
| Gördülő görgetés sebessége és iránya | a `0x009debd0` és a `[esi+0x14c]`/`[esi+0x150]` mezők forrása (a dia-objektum), és a `[ebx+0x49]` jelző szerepe | **a mozgás forrása megvan** (G.6.4: smoothstep, `P` a `dia+0x150`-be; `A`, `B` geometria és a `0x00819040` ütközés nyitott) |
| „Jó napom van” (`textstyle1`) animált tulajdonsága | a `0x00810656`-ág (`cmp eax,1`) hátralévő része: a `0x00812110`, `0x009863f0`, `0x00810773`-as vtábla-hívás célja; a `0x2bc` (700) állandó értelme | **nyitott** |
| Kurzor (villogás) az Írógépnél | a `0x0080a080` után a rajzoló-hívó olvassa-e a `[esi+0x34c]`-t és ír-e kurzort | **nyitott** |
| Natív futtatás | Wine nincs a gépen; a DirectShow-láncot a harness nem futtatja | **nem lehetséges itt** |

#### G.5 Mérés és eszköz (reprodukálhatóság)

A mérések szkriptjei ideiglenesek: `/tmp/claude-1000/kd-r4615/scripts/` (`pe.py` — PE-fejléc; `rtti.py` — RTTI-osztály → TD → COL → vtábla; `vtname.py` — vtábla → osztálynév és slotok; `xref.py` / `callers.py` — `mov [reg], imm32` és `E8`/`E9` hívóhelyek; `disasm_va.py` — capstone, a `pe_dis.py` alternatívája az `~/picasapy-agent/eszkozok/`-ban). A capstone a `/tmp/claude-1000/kd-r4615/venv`-ben van. Az `objdump` ezen a gépen nem olvassa a PE-t (ARM-build).

**Ami NEM mérés, hanem következtetés:** a stílus→osztály táblát (G.2) a kód-elágazásokból olvastam, és csak a kiemelt stílusokra (0, 1, 8, 11) ellenőriztem a konstruktor-hívás helyét; a többi stílus hozzárendelése nyitott.

#### G.6 3. kör (2026-10-12): a `P(t)` képlete — natívan mérve; az Írógép és a Gördülő bemenetei

*Állapot: a `0x009e5e70` kiértékelője **natívan lefuttatva** (qemu-i386, a harness `hb.py`-jával), és a szintetikus bemenetekre a modellel **0 eltéréssel** egyezik. Az Írógép és a Gördülő képlete a kódból olvasott; a bemeneti értékeik (dia-idő, kezdet, geometria) és az eseményidő nulla pontja **nyitott** (G.6.6). Filmből mért számot ez a kör nem ad.*

**Mérés módja.** A T-objektum és a szegmens-tömb kézzel épül a `0x009e6010` (hozzáfűzés) és a `0x0080a030` (Írógép-építő) kódja szerint; a szegmens-függvény a valódi kód (`0x00809ae0` azonosság, `0x00818cf0` smoothstep). A futtató szkriptek ideiglenesek: `/tmp/claude-1000/kd-r4615/scripts/p_native.py`, `p_native2.py`, `p_store.py`, `p_gate.py`.

##### G.6.1 A kiértékelő (`0x009e5e70`), utasításszinten

Bemenet: `t` (double, `[esp+4]`); a T-objektum `edi`-ben: `[T+0x8]` gyorsítótár, `[T+0x10]` a szegmens-tömb, `[T+0x14]` = 2·darabszám. Szegmens (0x28 bájt): `+0` interpolátor (függvény-mutató), `+0x8` B (double), `+0x10` A, `+0x18` s (kezdet), `+0x20` e (vég).

1. `t' = t + 0,02` — a `0x009e5e7e` `fadd [0x00cf48a8]`; a konstans mért értéke **0,02** (double).
2. `0x009e5b20` hívás. Ha `t' < e_0` (az első szegmens vége), 0-t ad, és nem módosít. Különben a szegmenseket a `t'`-nél **hasítja** (0x28-as rekordok másolása, újraallokálás). Egy szegmensnél (`darab < 2`) a `0x009e5dee` ág fut; a mérésben ez a várt eredményt adta.
3. `acc = B_0` (a `[seg0+8]`).
4. Minden szegmensre: `s = e` esetén `p = 1`; különben `q = (t' − s)/(e − s)`, `p = clamp(q, 0, 1)`. A `p`-t float32-re kerekíti (`fstp dword`), majd `S = f(p)` (az interpolátor, `call eax`), és `acc += S·(A − B)`.
5. `P = acc` (double); a `[T+8]`-ba írja, és st0-ban adja vissza.

Összefoglalva (a G.6.2 mérései igazolják):

    P(t) = B_0 + Σ_i f_i(p_i)·(A_i − B_i),   p_i = clamp((t + 0,02 − s_i)/(e_i − s_i), 0, 1)

##### G.6.2 Mért értékek (natív futás)

Szintetikus bemenetek — **nem** a film értékei. Az eltérés = natív − modell.

| eset | bemenet | pontok (t → natív) | eltérés |
|---|---|---|---|
| egy szegmens, identitás | B=0, A=12, s=0,5, e=2,5 | 0→0; 0,48→0; 0,5→0,12; 0,51→0,18; 1→3,12; 1,5→6,12; 2→9,12; 2,4→11,52; 2,49→12; 2,5→12; 2,6→12 | 0 (11/11) |
| két szegmens, identitás | (B₀=1, A₀=5, [0;1]), (B₁=5, A₁=9, [1;3]) | −1→1; 0,2→1,88; 0,5→3,08; 0,97→4,96 (csak `t' < e_0`) | 0 (4/4) |
| egy szegmens, smoothstep | B=10, A=50, s=1, e=3 | 0,5→10; 1→10,012; 1,5→16,706; 2→30,600; 2,5→44,194; 3→50; 3,2→50 | 0 (7/7) |

**Nyers-idő kapu** (`0x009e5e20`, mért; s=0,5, e=2,5): t = 0,48; 0,5; 2,49; 2,5 → `al = 0` (a kockafüggvény **frissít**); t = 2,6; 3,0 → `al = 1` (**nem** frissít).

**Tárolás-ha-változott** (`0x009debd0`, mért):
- cur = (0,0; 0,0), a = 0,0, b = 0,5 → (0,0; 0,5), a `dia+8` bit0 = 1;
- cur = (1,0; 2,0), a = 1,0 + 1 ULP, b = 2,0 → nem változik (1,0; 2,0), bit0 = 0;
- cur = (1,0; 2,0), a = 1,0 + 16 ULP, b = 3,0 → (1,0 + 16 ULP; 3,0), bit0 = 1.

##### G.6.3 Az Írógép: a képlet (`0x00809fe0`, `0x0080a030`, `0x0080a080`)

Kódolvasás és a G.6.2 mérés alapján:

- **Hossz** `len`: a szöveg **bájtszáma** (`0x00811da4`: bájtonként olvasott, NUL-ig számoló ciklus; nem Unicode-kódpont).
- **Időtartam** `d` (`0x008104b9`–`0x008104dc`): `d = [desc+0xec]`; ha nulla, akkor `[desc+0xe8] / 3,0` (`fdiv [0x00cf39f8]`, a konstans 3,0).
- **Kezdet** `L = [desc+0xf0] + [desc+0xf4]` (`0x00810459`–`0x00810464`, float32).
- A `desc` a gyár második argumentuma; a filmhívókban `desc = film+0x1a8` (`0x008128aa`, `0x008138bf`), tehát `[desc+0xec] = film+0x294` stb.
- **Szegmens** (`0x0080a030`): kezdet `L`, vég `L + d`, `B = 0`, `A = len`.
- **Kockafüggvény** (`0x0080a080`): `d > 0` kapu; a nyers-idő kapu (G.6.2); `P = 0x009e5e70(t)`; `n = trunc(P + 0,5)` (`fadd [0x00c72150]`, csonkoló kerekítés); `n = max(1, n)`; `[dia+0x34c] = n`; `[dia+0xc] |= 7` csak változáskor.

Következmény (a szerkezet mért, a paraméterek olvasottak):

    P(t) = len · clamp((t + 0,02 − L) / d, 0, 1)
    n(t) = max(1, trunc(P(t) + 0,5))
    r    = len / d      (bájt/s; lineáris, mert f = identitás: 0x00809ae0 = `fld [esp+4]; ret`)

A 2.10/b F-ben szereplő `n(k) = min(len, ⌊r·t_k⌋)` közelítés ettől eltér: van benne `+0,02` és `−L`, a kerekítés nem csonkol, és `t + 0,02 ≤ L`-re `n = 1`. Ezt a G.6.7 írja felül.

A nyers-idő kapu miatt a film végén az állapot az **utolsó olyan kocka** értéke, ahol a nyers `t ≤ e` (ha `len·0,02/d < 0,5`, ez gyakorlatilag `len`; különben a szöveg hiányosan marad). Ezt a kódolvasás adja; a kockafüggvény natív futtatása nincs (RTTI-t kér).

##### G.6.4 A Gördülő (`FadeMove`, stílus 8): a mozgás forrása

- **Idővonal:** a `H` kezelő (`0x00809c50`) második idővonala `T2 = H+0x30`, az építő `0x00809cd0`. Egy szegmens: kezdet `L` (mint G.6.3), vég `L + [H+8]`, `[H+8] = [desc+0xe8]` (közvetlenül, nincs `/3`), az interpolátor **`0x00818cf0`** = smoothstep: `f(p) = 3p² − 2p³` (mért, G.6.2).
- **Amplitúdó:** `B = [H+0x28]` = a második argumentum = `R_b.h` (a `0x009e51a0` hívás téglalapjának magassága), `A = [H+0x2c]` = `0,5 · V1`, `V1 = R_a.h − ([E+0x54] − [E+0x4c])` (`0x00810f7b`–`0x00810fbe`). **A és B geometria**, nem konstans. Forrásuk a `0x009e51a0` és a `[E+0x54]`/`[E+0x4c]` (vtábla-hívás, `0x00810f55`); ezek nincsenek visszakövetve (G.6.6-4).
- **Pozíció-írás** (`0x00809d20`): `P_f = float32(0x009e5e70(T2, t))`, a kapu ugyanaz. A kezelő `[H+0x49]` jelzője dönti el, melyik mezőbe: `≠ 0` → `0x009debd0(a = P_f, b = X2)`; `= 0` → `0x009debd0(a = X1, b = P_f)`, ahol `X1 = [dia+0x14c]`, `X2 = [dia+0x150]`.
- **Gördülőnél** a gyár a kezelő konstruktora után **`[H+0x48] = 0` és `[H+0x49] = 0`** értéket ír (`0x00811005`, `0x00811009`), tehát a konstruktor `al = 0xff` argumentuma felülíródik. Így `P_f` a **`dia+0x150`**-be kerül, a `dia+0x14c` változatlan marad.
- **`0x009debd0` (mért): „tárolás, ha változott”.** Ha `X1` vagy `X2` és az új érték bitjei között a különbség ≥ 8 ULP, akkor `X1 := a`, `X2 := b` és `[dia+8] |= 1`; különben nem ír (G.6.2).

Összegezve: a Gördülő görgetése `X2(k) = B + S(p)·(A − B)`, `S(p) = 3p² − 2p³`, `p = clamp((t + 0,02 − L)/dur, 0, 1)`, `dur = [desc+0xe8]`. Az `A` és a `B` geometriából jön (G.6.6-4).

⚠️ **Ellentmondás-gyanú, nincs eldöntve:** a `0x00819040` fogyasztó (virtuális hívás, a `[eax+0x78]` slot) minden hívásakor összeveti `dia+0x14c/0x150` értékét `dia+0x388/0x38c`-vel, és ha eltér, `0x009debd0(a = dia+0x388, b = dia+0x38c)`-t hív (`or [dia+8], 7`). Ha ugyanarra a `dia` objektumra fut, felülírná a `P_f`-et. Hogy ez a Gördülő objektuma-e, és a `dia+0x388/0x38c` mit tartalmaz az animáció alatt, **nincs mérve** (G.6.6-3).

A `[H+0x49]` jelző az 1-es stílusnál (`0x008107a7` előtt) nincs kiolvasva; az 1-es stílus is a `0x00809c50`-et hívja.

##### G.6.5 Stílus-hozzárendelés a `0x00810420` elágazásaiból (részleges)

| stílus | ág (cím) | hívott kezelő(k) | állapot |
|---|---|---|---|
| 0 | `0x00810598` → `0x0081061b` | TextFade `0x809af0` (építő `0x809eb0`) | olvasott |
| 1 | `0x00810656` → `0x008107a7` | FadeMove `0x809c50` + `0x809cd0` (`0x008107ba`) | olvasott; a flag-ág nem |
| 2 | `0x00810a40` → `0x00810b7c` | TextFade `0x809af0` (építő `0x809eb0`, `0x00810b91`) | olvasott |
| 3 | `0x00810bce` → `0x00810e1d` | TextFade `0x809af0` + `0x809e60` (vtábla `0x00cbdba8`, **nem azonosított** osztály) | olvasott |
| 4, 5 | `0x00810ebe`, `0x00810ec7` → `0x00811572` | a blokkban nincs `0x809`/`0x80a` hívás (csak `0x812110`) | olvasott |
| 6, 7 | `0x00810ea6`, `0x00810eaf` → `0x00811a27` → `0x00811cf0` | TextFade `0x809af0` | olvasott |
| 8 | `0x00810ed3` → `0x00810ed9` | FadeMove `0x809c50` + `0x809cd0`, flag 0 (G.6.4) | olvasott + mért alak |
| 9, 10 | `0x00811031` → `0x0081103f` / `0x00811088` | a blokk több kezelőt hív (`0x809af0`, `0x809eb0`, `0x809e60`), de az ágakhoz nincs szétválasztva | **nyitott** |
| 11 | `0x00811cd8` (`cmp 0xb`) → `0x00811db7` | TypeWriter `0x809fe0` + `0x80a030` | olvasott + mért alak |

##### G.6.6 Nyitott — a megszerzés útjával

1. **A `t` nulla pontja** (az esemény `[edi+0x10]` ideje, a kockafüggvények bemenete). Ez blokkolja a `k → t` leképezést. A hívó nincs azonosítva: a `0x0080a080` és a `0x00809d20` a kezelő vtábla 3-as slotja (`ecx` = `this`, három stack-argumentum, `ret 0xc`). **Megszerzés:** a `call [reg+0xc]` hívóhelyek keresése a film-osztályokban, és az eseményrekord `[+8] = 0x13` töltésének megkeresése.
2. **A dia-időmezők értéke** (`desc+0xe8..0xf4` = `film+0x290..0x29c`). A film-konstruktor a `0x0080a1c2` körül (`mov [esi], 0xcbdbd4`) dword-öt ír ezekbe (`+0x28c` mód). **Ellentmondás-gyanú:** a `0x008122f1` egész értéket (`fistp`, csonkolás) ír `+0x298`-ra, míg a gyár `fld dword`-ként (float) olvassa a `+0xf0`-t. Ha ez ugyanarra az objektumra vonatkozik, a típus nem egyezik. A `d` és az `L` számértéke ettől függ. **Megszerzés:** a film-konstruktor hívóinak kiolvasása, és a `0x008122xx` függvény azonosítása. *(3. kör: a `0x8122f1` írás a `0x812110`-ben van, és a render-objektumé — G.7.1; az alapértékek G.7.2; a fájlértékek G.7.3 szerint nyitottak.)*
3. **A `0x00819040` fogyasztó** (Gördülő): felülírja-e a `dia+0x150`-et. **Megszerzés:** a `[eax+0x78]` vtábla-slot hívóinak azonosítása, és natív teszt ugyanazon `dia`-n.
4. **A Gördülő A és B értéke:** a `0x009e51a0` visszatérési téglalapja és a `[E+0x54]`/`[E+0x4c]` (a `0x00810f55`-ös vtábla-hívás kimenete). **Megszerzés:** a két függvény és a vtábla kiolvasása; a valódi méretek (kép- és szöveg-keret) a film futtatásából jönnek, a jelenlegi harnesszel nem mérhetők.
5. **A `0x809e60` osztály** (vtábla `0x00cbdba8`, a 3-as stílus), és a 4, 5, 9, 10 stílusok ágai (G.6.5).
6. **A `[H+0x49]` az 1-es stílusnál** (`0x008107a7` előtt).
7. **Natív film-futtatás nincs:** a DirectShow-lánc a harnessben nem fut (a README szerint), Wine nincs a gépen. Filmből mért érték a 2.10/b D szerinti Colab-os Picasa-mérésből jöhet.

##### G.6.7 „Kész, ha” — az Írógépre és a Gördülőre (feltételes; `src/picasapy/movie/slideshow.py`)

- [ ] **Bemenetek (blokkoló):** G.6.6-1 (a `t` nulla pontja) és G.6.6-2 (`d` és `L` számértéke) tisztázva. Enélkül a képlet csak paramétereiben áll.
- [ ] **Írógép:** `n(k) = max(1, trunc(len·clamp((t_k + 0,02 − L)/d, 0, 1) + 0,5))`, ahol `t_k` a G.6.6-1 szerint, `len` a szöveg **bájtszáma**, `d` és `L` a G.6.3 szerint. A `slideshow.py` `_szovegdia` jelenleg a karakter-hosszt használja; ezt bájtszámra kell cserélni.
- [ ] **Nyers-idő kapu:** ahol `t_k > e`, a `n` nem változik (G.6.2, mért); a tesztben külön ellenőrizni.
- [ ] **Bájt, nem karakter:** a teszt többbájtos (UTF-8 vagy CP1250) szöveget is tartalmazzon. Hogy a rajzoló a `[dia+0x34c]`-t bájtként vagy karakterként használja, **nincs kiolvasva**; ez nyitott.
- [ ] **Gördülő:** `X2(k) = B + S(p)·(A − B)`, `S(p) = 3p² − 2p³`, `p = clamp((t_k + 0,02 − L)/dur, 0, 1)`, `dur = [desc+0xe8]`; `A`, `B` a G.6.4 szerint. Előfeltétel: G.6.6-3 és G.6.6-4.
- [ ] **Regresszió:** a 0–7, 9, 10 stílusok kimenete bájtra egyezzen a mostanival, amíg a 2, 3, 4, 5, 9, 10 viselkedése nincs kiolvasva (G.6.5); ezek maradjanak álló képként.

#### G.7 4. kör (2026-10-12): a három nyitott pont — mi dőlt el, mi nem

*Állapot: a (b) ellentmondás **álellentmondásnak** bizonyult (G.7.1); a (b) alapértékei **kódból olvasott konstansok** (G.7.2); a (a) és a (c) **nyitott** maradt. Számérték ez a kör sem ad: nincs futtatás (Wine nincs), a film értékei statikusan nem olvashatók ki. Az Írógép karakter/s és a stáblista sebessége **most nem mondható ki számként**.*

##### G.7.1 (b) A `+0x298` int- és float-olvasata — utasításszintű döntés

- A `0x8122f1` írás (`mov [esi+0x298], edx`, a `fistp qword` alsó dwordja) a **`0x812110`** függvényben van. Ennek `this`-e (`esi`) nem a desc, hanem a **render-objektum**: a factory (`0x810420`) `edi`-je a film (`ctx`), és a `this` a `[ctx+0x7c0]` → `+0x264` → `[ptr]` láncon jön (`0x8105b0`–`0x8105b6`; a többi hívóhely is `[ctx+0x7c0]`-ből indul: `0x8106d5`, `0x810b31`, `0x810bd7`, `0x810edb`, `0x8110a6`). A `0x812110` hívói (E8): `0x8105ec`, `0x810733`, `0x810884`, `0x810b47`, `0x810c18`, `0x810ef9`, `0x81118a`, `0x8112e1`, `0x8115b3`, `0x811a68`.
- A desc a factoryban `ebx` = `[ebp+0xc]`, a hívók szerint `desc = ctx+0x1a8` (`0x8128a2`–`0x8128aa`, `0x8128e0`–`0x8128e8`, `0x813885`–`0x8138bf`; a `push` sorrend: desc először, ctx másodszor). A desc+0xf0 tehát `ctx+0x298`, és a factory **float**-ként olvassa: `fld dword [ebx+0xf4]`, `fadd dword [ebx+0xf0]` (`0x810453`–`0x81045e`). A `0x8138a7` is `fld dword [ebx+0x298]`-et olvas.
- **Döntés:** a desc `+0xf0` float; a `0x8122f1` int-írása egy **másik objektum** (render) `+0x298`-át írja. Nincs típusütközés a desc-en belül.
- **Korlát:** a `ctx+0x7c0`-objektum különbözősége a `ctx`-től a láncból következik, abszolút bizonyíték nélkül (futás kellene). A kódban nincs jel arra, hogy a lánc `ctx`-re mutatna.
- A `+0x28c…+0x298` írásai (`0x80a1df`, `0x80a1e9`, `0x80a1f4`) a `0x80a190` konstruktorban vannak; ennek `this`-e a factory `esi`-je (`mov esi, [esp+0x54]`, `0x8117db`), tehát ez sem a film. (A hívóhely: `0x8117ed`.)

##### G.7.2 (b) A desc-blokk alapértékei — kódból olvasott konstansok

A `desc+0xe8..0xf4` (= film `+0x290..0x29c`) alapértékeit két inicializáló írja. A konstansokat a `.rdata`-ból olvastam (`0xc7e4a4` = 4.0 f32; `0xc72150` = 0,5 f64; `0xcf39f8` = 3,0 f64).

| mező | alapérték | író |
|---|---|---|
| `+0xe8` | **4,0 s** (f32, `fld [0xc7e4a4]`) | `0x80a330` (`CTransitionInfo`, `0x80a399`–`0x80a39f`); `0x816326`–`0x81632c` (`TimelineXML`, a `trans` / `defaulttrans` csomópont-törlés) |
| `+0xe4` | 2 (egész) | ugyanott |
| `+0xec` | **1,0** (f32, `fld1`) | ugyanott |
| `+0xf0` | **0,0** (f32, `fldz`) | ugyanott |
| `+0xf4` | **0,0** (f32, `fldz`) | ugyanott |

Következmény az alapértékből (ha nincs felülírás): `L = f0 + f4 = 0`; a Írógép `d = ec = 1,0 s` (a `0x8104b9` szerint `d = [desc+0xec]`, és csak `ec = 0` esetén `e8/3`). **Ez alapérték, nem a film értéke.**

⚠️ **Nyitott összekötés:** a két inicializáló a `this+0x50` blokkot írja (`CTransitionInfo` a `0x80a330`-ban, `TimelineXML` a `0x8162f0`-ban), a factory viszont a `ctx+0x1a8` blokkot olvassa. A `0x80f39c`-ben a `CTransitionInfo` a `[ebp+0x48]`-on épül, így a blokkja `ebp+0x98`-on van, nem `ebp+0x1a8`-on. **Nem igazolt**, melyik objektum `ctx+0x1a8`-ja inicializálódik ezekkel; ehhez a `ctx` osztályának és a `TimelineXML`-nek a beágyazását kell megtalálni.

##### G.7.3 (b) A `desc+0xe8..0xf4` értékei a fájlból — NYITOTT

A `0x8152d0`–`0x816400` tartományban csak a fenti alapértékek írói vannak (`0x81632c`–`0x81634c`). A `trans` attribútumok (`advanceinterval`, `transitiontime`, `blacktime`; spec 2.4/b) desc-mezőkbe írása **nem** közvetlen `[reg+0xe8]`-írással történik, tehát a beolvasó egy általános segédrutinon megy át. **Megszerzés:** a `TimelineXML` beolvasó (`0x8152f0` és a csomópont-kezelő) hívólánca, és a `trans` nevű csomópont attribútum-név → mező táblája.

##### G.7.4 (a) Az eseményidő `t` nulla pontja — NYITOTT, de a lánc megvan

- Az eseményrekord konstruktora `0x809a10` (vtábla `0xc8b4b0`, RTTI: `ytUIEvent`). A `t` a double argumentum (`[esp+4]` → `[+0x10]`, `0x809a56`); a típus `[+8] = 0x13` a `0x809a65`-ben íródik.
- Egyetlen E8-hívója: `0x80c24a`, a `0x80c230` függvényben; ennek `t`-je a `[ebp+8]` (double argumentum). A `0x80c230`-nak **nincs E8-hívója** (virtuális slot 0 a `0xcbdd60` vtáblában; ennek nincs érvényes COL-neve).
- Tehát a `t` nulla pontja a `0x80c230` **hívóján** dől el. Ennek azonosítása (a `0xcbdd60`-as vtábla hívóinak keresése) **nyitott**. Addig nem dönthető el, hogy a `t` a film vagy a dia kezdetéhez mér. A G.6.3 képlete (`L` és `t` azonos nulla) csak ezután igazolható.

##### G.7.5 (c) A Gördülő A és B geometria — képlet teljes, a számok futásfüggők

Kódlánc (`0x810f49`–`0x810fee`, a stílus-8 ág):

1. `R_a` = `0x9e51a0( [text+0x2e0] )`, `h_a = [R_a+0xc] − [R_a+4]` (RECT bottom − top).
2. `E` a `0x810f55` vtábla-hívás (slot `+0x30`) kimenete: `E.54 = [esp+0x54]`, `E.4c = [esp+0x4c]`.
3. `R_b` = `0x9e51a0( [ctx+0x2e0] )`, `h_b = [R_b+0xc] − [R_b+4]`.
4. `V1 = h_a − (E.54 − E.4c)` (egész, `fild`, `0x810fb2`–`0x810fbe`).
5. A `0x809c50` argumentumai: `dur = [desc+0xe8]` (`0x810fe5`), `B = h_b` (`fild [esp+0x50]`, `0x810fdd`), `A = 0,5 · V1` (`fmul [0xc72150]`, `0x810fc9`).

Tehát `A` és `B` **egész pixel-értékek**, a valós képkeret- és szövegkeret-téglalapokból. Konstans nincs bennük. **Nyitott:** a két `0x9e51a0` hívás téglalapjának és az `E` vtábla-kimenetének mért értéke (futás kell; a harness nem futtatja a DirectShow-láncot).

##### G.7.6 „Kész, ha” — mi áll most

- **Írógép (11):** a G.6.7 képlete változatlan, de blokkolva: (i) a `t` nulla pontja (G.7.4), (ii) `L` és `d` fájlértéke (G.7.3), (iii) a desc-blokk összekötése a factory `ctx+0x1a8`-jával (G.7.2). Karakter/s = `len / d` csak lineáris `P`-nél, és `d` most csak az alapértékből (1,0 s) ismert: **nem mondható ki számként.**
- **Gördülő (8):** blokkolva: `A`, `B` (G.7.5), `dur` fájlértéke (G.7.3), a desc-összekötés (G.7.2). A görgetés teljes útja `A − B` (a `S(p)` smoothstep 0-tól 1-ig fut), az átlagsebesség `(A − B) / dur` px/s; a számértékek most sem adhatók meg.
- **Nincs implementáció:** a `slideshow.py` változatlan; a jegy megvalósítása a fenti (i)–(iii) és G.7.5 mérése után indulhat.

#### G.7.7 5. kör (2026-10-12): a `desc` írói, a `+0x298` típusa, a vtábla-hívó — mi dőlt el

*Állapot: (b) a **trans-attribútumok írói és a desc-leképezés** eldőlt (kódból, utasításszinten); a `+0x298` típusa **float**. A (b) film-oldali összekötése (desc = `ctx+0x1a8`) és a (a) `t` nulla pontja **nyitott**. Számérték továbbra sincs: nincs futtatás.*

##### G.7.7.1 (b) A `desc` = a TimelineXML-objektum `+0x50` blokkja

- A **TimelineXML** vtáblája `0xcbddb8` (RTTI: `.?AVTimelineXML@@`, COL `0xd0f634`); a konstruktor `0x8151c0`, a vtábla-írás `0x8151e2`.
- A `0x8162f0` (vtábla 1. slot) a `trans` / `defaulttrans` nevű elemre a `this+0x50`-et alapértékkel tölti (`0x816326`–`0x81634c`): `+0xe8 = 4,0`, `+0xe4 = 2`, `+0xec = 1,0`, `+0xf0 = 0,0`, `+0xf4 = 0,0`. Ez azonos a G.7.2 layoutjával, tehát **`desc = this+0x50`**.
- A `0x8152f0` (vtábla 2. slot, `ret 4`, az attribútum neve az argumentum) az attribútum-dispatch. A `trans` attribútumai:

| attribútum (`.rdata`) | írás (`this+…`) | desc-mező | érték |
|---|---|---|---|
| `transition` (`0xcbda2c`) | `+0x134` (`0x815978`, sztring-lookup) | `+0xe4` | egész / enum |
| `advanceinterval` (`0xcbda38`) | `fstp [+0x138]` (`0x815a06`) | `+0xe8` | float |
| `transitiontime` (`0xcbda48`) | `fstp [+0x13c]` (`0x815a7a`) | `+0xec` | float |
| `blacktime` (`0xcbda58`) | `fstp [+0x140]` (`0x815aea`) | `+0xf0` | float |

- A float-olvasó `0x50a830`: a sztring-objektum `+4` mezőjét hívja (`0xc080d7`), üres érték esetén `fldz`. Tehát a fájlból érkező érték **float**.
- A `desc+0xf4` (`this+0x144`) **nincs** attribútumhoz kötve a dispatchben: csak az alapérték írja (0,0). Így `L = f0 + f4 = blacktime`.
- Az attribútum-dispatch nem csak a `trans`-t kezeli: ugyanabban a függvényben van `type`, `bkcolor`, `index`, `text`, `filename`, `showflags`, `fontname`, `size`, `color`, `weight`, `italic`, `outline`, `styleid`, `facerect*`, `facemoviesrc`. Tehát a `trans` attribútumait egy közös elem-rekord fogadja, és a `trans`-hez tartozást az elemnév (`0x8162f0`) jelöli.

##### G.7.7.2 (b) A `+0x298` típusa: **float** (döntés)

- A desc `+0xf0` (= `blacktime`) float-ként íródik (`fstp dword`), és a gyár is float-ként olvassa (`fld dword [ebx+0xf4]`, `fadd dword [ebx+0xf0]`, G.7.2). Ha `desc = ctx+0x1a8`, akkor `ctx+0x298` = `blacktime`, float.
- A `0x8122f1` int-írás (`mov [esi+0x298], edx`) a G.7.1 szerint a **render-objektumé**, nem a desc-é. Ez nem ellentmondás.
- **Nyitott összekötés:** hogy a TimelineXML (vagy a `CTransitionInfo`) a film `ctx+0x158`-ában él-e (ahonnan `desc = ctx+0x1a8`). A TimelineXML-konstruktor hívói (`0x617140`, `0x617c15`, `0x618b7b`, `0x814250`-ből / `0x814337`-ből) **verem- vagy tag-objektumot** építenek (`lea esi,[esp+…]`), tehát a desc-et valahol másolni kell a `ctx+0x1a8`-ba. A másoló **nincs azonosítva**.
- A film `+0x290..+0x29c` (= desc `+0xe8..+0xf4`) **teljes író-listája**: 366 tároló-utasítás a `.text`-ben (`[reg+0x290|0x294|0x298|0x29c]`). Ezek túlnyomó része más objektum; a film-típusú szűrés **nincs kész**, ezért nem sorolom ide.

##### G.7.7.3 (a) A `0x80c230` hívója és vtáblája — HELYESBÍTVE G.7.8-ban

Az eredeti G.7.7.3 hibásan a `0xcbdd60` címet a vtábla kezdetének vette, és emiatt a `0x80c230`-at a 0. slothoz rendelte. A G.7.8.4 ezt megcáfolta: a vtábla `0xcbdcec`-nél kezdődik, a függvény a 29. sloton van (`+0x74`). A „18 slot-0 jelölt” lista és a `0xcbdd60`-as vtábla-pointerre épülő következtetések elvetendők. A függvénynek nincs közvetlen E8-hívója; a DirectShow-pin virtuálisan hívja.

##### G.7.7.4 Kész, ha — változás a G.7.6-hoz képest

- **Írógép (11):** `L`-re a G.7.7.1 mezőket megadja: `L = blacktime (+f0) + f4 (=0)`; a `d = transitiontime (+ec)`, **fájlérték**, és `advanceinterval` (`+e8`) a `e8/3` ágat fedi. Blokkolva maradt: (i) a `t` nulla pontja (G.7.7.3), (ii) a film–desc összekötés (G.7.7.2).
- **Gördülő (8):** a `dur = advanceinterval (+e8)` **fájlérték-forrása most megvan** (G.7.7.1). Blokkolva: `A`, `B` (G.7.5), és a desc-összekötés (G.7.7.2).
- A `slideshow.py` változatlan: az implementáció a (ii) összekötés és a `t` nulla pontja után indulhat.

#### G.7.8 Kiegészítő ellenőrzés (2026-10-13): a natív időalap, a render-desc és a textstyle1

*Állapot: a render-oldali időparaméter, a gyár `ctx+0x1a8` desc-argumentuma, valamint a TimelineXML-desc → idővonal-lista → render-desc másolási lánc utasításszinten részben megvan. A parser szülőobjektumának és a render-`ctx`-nek az azonossága, a pin seedjének exportkori forrása, a `textstyle1` mozgáscsatornájának pontos végpontja és időértelmezése, továbbá a kockaindex és a DirectShow-időbélyeg megfeleltetése nyitott. Referenciafilmes képkockamérés nincs.*

##### G.7.8.1 A `t` a CDXSlideshowPin felhalmozott mintavételi órája

- Az RTTI szerint a `CDXSlideshowPin::vftable` címe `0x00cb1a08`; slot 2 = `0x0074dfc0`, slot 3 = `0x0074d970` (RTTI `kind`, 0-alapú slotindex).
- A slot 3 függvény (`0x0074d970`) a `[this+0x108]` és `[this+0x10c]` qwordot másolja a kezdő akkumulátorba `[this+0x4b0..0x4b7]`, valamint az utolsó minta idejébe `[this+0x4b8..0x4bf]` (`0x74d981`–`0x74d9b4`). Ez a reset seed; az értéket beállító külső út nincs azonosítva.
- A pin létrehozó útja `0x74e580`-ból hívja a `0x74d1c0` konstruktort. A konstruktor az akkumulátor mezőit és a szomszédos `+0x100/+0x104`, `+0x110/+0x114` mezőket nullázza, de a seed `+0x108/+0x10c` mezőket nem (`0x74d4f5`–`0x74d517`). A CDXSlideshowPin RTTI-metódusain végzett offszet-térkép a seedet a resetben olvassa, de közvetlen írót nem mutat; a korlátos, `paszta.memoria_kapu()` után futtatott `.text`-pásztázás sem azonosított seedet író pin-metódust. Ez kizárja a konstruktorból levezetett „seed = 0” feltevést, de nem zárja ki a más objektumon át vagy indirekten végzett írást. A tényleges exportkori seed továbbra is `NINCS MEG`.
- A slot 2 (`0x0074dfc0`) a minták közötti időt hozzáadja a `[this+0x4b0]` 64 bites akkumulátorhoz (`0x74e1c0`–`0x74e1e2`). A renderhívás előtt ezt qwordként beolvassa (`0x74e1e8`), elosztja a `0x00989680` literállal (`0x74e1ee`–`0x74e207`), majd double másodpercértékként adja tovább. `0x00989680 = 10 000 000` bináris konstans.
- Ugyanez a double jut (a) a `0x008127b0` render-helpernek, a `[pin+0x308]` kontextussal (`0x74e209`–`0x74e219`), és (b) a `[ctx+0x2e8]` objektum `vtable+0x74` slotjának (`0x74e232`–`0x74e251`). A `CTransTimeline::UI::vftable` RTTI-címe `0x00cbdcec`; a 0x74 slot 29. bejegyzése `0x0080c230` (`0xcbdcec + 29×4 = 0xcbdd60`). Ez a függvény a kapott double-t `ytUIEvent`, 0x13-as típusú eseményként továbbítja (`0x809a10`, `0x80c230`).
- **Következtetés:** a handler `t` értéke a DirectShow-pin 100 ns-os mintavételi órájából képzett másodpercérték, a `[pin+0x108/+0x10c]` seedhez viszonyítva. A vizsgált factoryhívás maga ezt a seedelt órát kapja; a teljes exportvezérlés nincs végigkövetve, ezért nem állítható, hogy a DirectShow reset minden dia kezdetével hogyan viszonyul. A `t=k/fps` és a dia saját `k=0` pontja **nem bizonyított**.
- A `0x0080c230`-ban a Ghidra-kimenet `local_b4=0` értéke nem a `t` nullapontja: külön helyi változó, szerepét a dump nem nevezi meg. A Ghidra #38 helyesen jelzi, hogy a függvénynek nincs közvetlen E8-hívója; a hívás virtuális.

##### G.7.8.2 A render factory desc-e `ctx+0x1a8`; a TimelineXML-adat útja részben megvan

- A `0x00810420` factory első argumentuma a render-kontextus (`edi=[ebp+8]`), második argumentuma a desc (`ebx=[ebp+0xc]`). A `0x008127b0` három hívóhelyén (`0x8128a2`–`0x8128aa`, `0x8128e0`–`0x8128e8`, `0x812935`–`0x81293d`) a hívó a saját `ctx+0x1a8` címét és a `ctx`-t adja át. A `0x0074dfc0` útja közvetlenül ide ér: `ctx=[pin+0x308]`.
- Másik gyárhívó-ág a `0x00813330`: a `0x813804`–`0x81380c`, `0x813885`–`0x81388d` és `0x8138b7`–`0x8138bf` helyeken szintén `ctx+0x1a8` és `ctx` kerül a `0x00810420`-nak. Ugyanezt a render-desc elrendezést mutatja, de az xref szerint az első hívási láncba ágyazott út, ezért csak keresztellenőrzés.
- A factory ezen a desc-en olvassa a `+0xe8`, `+0xec`, `+0xf0`, `+0xf4` mezőket (`0x810453`–`0x8104dc`); a típusuk float. Ez lezárja a **render-oldali** összekötést: a factory desc pointere `ctx+0x1a8`.
- A TimelineXML attribútum-dispatch (`0x8152f0`) a `transition` és `advanceinterval` értékeket a `this+0x50` blokk mezőibe írja (`this+0x134/+0x138`, azaz a blokkon belül `+0xe4/+0xe8`). A `trans` gyermek feldolgozásakor a `0x816360` a `this+0x50` címet adja át a `0x80a460`-nak, amely a szülő `[this+0x4c]+0x48` idővonal-listájába teszi a rekordot; az append `0xf8` bájtos rekordokkal dolgozik, és a `0x612350` másolósegédet használja.
- A film render-oldalán a `0x812470` a `ctx+0x48` listát adja a `0x610d30` mintavételezőnek az aktuális double idővel, majd a visszaadott rekordot a `0x612350`-tel a `ctx+0x1a8` desc-be másolja (`0x812553`–`0x81258c`). A `0x74dfc0` ezt az ágat a `[pin+0x308]` contexttel hívja; innen a `0x813330` hívja a `0x810420` factoryt. A másik renderágban a `0x8127b0` a `0x611320`-szal választ rekordot, majd ugyancsak a `0x612350`-tel másolja azt a `ctx+0x1a8` mezőbe (`0x8129c1`–`0x8129e2`).
- **A fennmaradó rés:** a kód igazolja a parseroldali `szülő+0x48` lista és a renderoldali `ctx+0x48` lista azonos rekordlayoutját és másolási segédjét, de nem bizonyítja, hogy exportkor a parser `[this+0x4c]` szülőpointere pontosan a `0x812470/0x8127b0` által használt render-`ctx`. Ezért a teljes XML→élő factory-desc objektumazonosság `NINCS MEG`; a célzott Ghidra-kör pontos kérdése a G.7.8.6-ban szerepel.

##### G.7.8.3 Az animációk kódból olvasható menete

**Írógép (`textstyle11`)**

- A stílus-11 factory-ág a `0x00809fe0` kezelőt és a `0x0080a030` építőt használja; a `len` a szöveg bájthossza. A `d` értéke `desc+0xec` (`transitiontime`); ha ez pontosan nulla, `d=desc+0xe8/3` (`0x8104b9`–`0x8104dc`). Negatív `d`-t a factory nem helyettesít, és a kezelő `d>0` feltétele miatt az animáció nem frissül. A kezdőpont `L=desc+0xf0+desc+0xf4` (`0x810453`–`0x810464`), ahol a parserben `+0xf0=blacktime`, a `+0xf4` mezőnek nincs XML-attribútuma és alapértéke 0 (`0x8162f0`, `0x8152f0`).
- A kockafüggvény képlete a G.6.3/G.6.7 szerint: `n(t)=max(1, trunc(len·clamp((t+0.02−L)/d,0,1)+0.5))`, ha `d>0`. A lineáris rész szerinti ütem `len/d` bájt/s; az `advanceinterval/3` visszaesés csak nulla `transitiontime` esetén aktiválódik, és csak pozitív eredményű `d` mellett frissül a kezelő.
- A képlet a **bájtszámot** bizonyítja, nem azt, hogy a natív rajzoló egy több-bájtos UTF-8 karaktert hány látható karakterként kezel. A glyph-szintű ütem és a kurzor kérdése továbbra is mérendő.

**Gördülő stáblista (`textstyle8`)**

- A kezelő `FadeMove` második idővonala a `desc+0xe8` (`advanceinterval`) hosszát kapja; a start `L=desc+0xf0+desc+0xf4`. `p=clamp((t+0.02−L)/advanceinterval,0,1)`, `S(p)=3p²−2p³` (interpolátor `0x00818cf0`).
- A natív scalar-érték `P(t)=B+S(p)·(A−B)`, tehát az idővonal `B`-ből `A`-ba halad, és a `dia+0x150` mezőbe kerül (`0x809cd0`, `0x809d20`; a style-8 flag beállítása `0x811005`–`0x811009`). `A=0.5·(h_a−(E+0x54−E+0x4c))`, `B=h_b`; ezek a futás közbeni kép- és szövegréteg-geometriából származnak (G.7.5).
- A képlet és az időtartam mezőforrása megvan, de `A`, `B`, a tényleges irány pixel-koordinátán, a `TimelineXML`-értékek élő desc-be jutása és a kocka `t`-je nincs. A mozgás tényleges pixel/s értéke ezért `NINCS MEG`.

**„Jó napom van” (`textstyle1`)**

- A factory 1-es stílusága a `FadeMove` konstruktort (`0x00809c50`, `0x8107a7`) és építőt (`0x00809cd0`, `0x8107ba`) hívja. A kezelő a lineáris alfa- és a smoothstep pozíció-idővonalat is bekapcsolja (`H+0x48=1`, `H+0x49=1`, `0x809cb9`–`0x809cbc`).
- A gyár `AL=0xff` értéket ad át (`0x81079a`); a konstruktor alfa-kezdőértéke 0 (`0x809c68`), végértékét `H+0x0d` tárolja. Az alfa-építő a lineáris `0x00809ae0` interpolátort adja a `0x009e6010` szegmensnek (`0x809eb0`), tehát a kódból olvasható alfaút 0→255.
- A pozícióút a `H+0x28`→`H+0x2c` végpontokat smoothstep-pel interpolálja; a stílus-1 hívásban `H+0x28=0`, a `H+0x2c` végpontot a hívó stackadja adja, forrása nyitott. Az 1-es jelző miatt a `dia+0x14c` mezőt írja (`0x809cd0`, `0x809d20`). A gyár a közös `L=desc+0xf0+desc+0xf4` kezdőértéket adja át (`0x810453`–`0x810464`, `0x8107b2`).
- A stílus-1 ág `0x8107a0` betöltése a factory által korábban kiszámított `d` lokális értéket használja: `d=desc+0xec`, ha nem nulla, egyébként `d=desc+0xe8/3` (`0x8104b9`–`0x8104dc`). Ezt az értéket a factory a `0x809c50` konstruktor első argumentumaként adja át, ahol `H+0x08` mezőbe kerül; az alfa- és pozíció-idővonal is ezt használja. A negatív `d` nem vált ki visszaesést, és a kezelő `d>0` kapuja miatt nem frissít. A `0x809cd0` a pozíciószegmenst `[L,L+H+0x08]` időintervallumra építi, tehát itt `H+0x08` a szegmens időtartama; a kockaidőből számolt arányt a közös kiértékelő állítja elő.
- **Nyitott:** a pozíció-végpont forrása nincs teljesen lezárva. A gyár a kiválasztott szövegobjektum `+4` alobjektumának `vtable+0x30` metódusát hívja (`0x810761`–`0x810771`), majd egy visszaadott egész értéket előjellel megfordítva floatként a konstruktor stackterületére ír (`0x810783`–`0x81079c`). A helper–argumentum–`H+0x2c` kapcsolatot és a koordinátatengelyt a helyi diszasszemblálás nem dönti el; ezekre nincs pixelérték vagy becslés.

##### G.7.8.4 Két ellenőrzési út és cáfoló kör

- **A út:** `CDXSlideshowPin` RTTI → `0x74dfc0` minta-delta és időegység-átváltása → `0x8127b0` → factory `ctx+0x1a8`; ugyanaz a timestamp a `CTransTimeline::UI` virtuális slot 29-én a `0x80c230`-ba jut.
- **B út (külön fogyasztói ág):** ugyanazt a double-t a pin külön virtuális hívásban a `[ctx+0x2e8]` objektum `+0x74` slotjának adja. Az RTTI ezt a `0x80c230` függvényhez köti, a Ghidra-dekompilátum pedig a bemenő double-t a `0x809a10` eseménykonstruktorba követi. Ez függetlenül ellenőrzi az UI-esemény útját és típusát; az A és B út ugyanabból a pin-hívásból indul, ezért a seed-nullapontot nem két független forrás igazolja.
- **Desc-út, két külön kódrészről:** a parseroldali út (`0x8152f0` → `0x816360` → `0x80a460`) a `this+0x50` blokkot a szülő `+0x48` listájába másolja. A filmoldali utak ettől külön fogyasztók: `0x812470` a `ctx+0x48` listát időpontra mintavételezi, és az eredményt `ctx+0x1a8`-ba másolja; `0x8127b0` ugyanezt a lista/desc kapcsolatot a `0x611320`-as mintavételezővel használja. Az egyező `0xf8` rekordlépés és a `0x612350` másolósegéd alátámasztja az azonos rekordlayoutot. Ez két független utasításszintű út az adatstruktúrához, de **nem** bizonyítja, hogy a parser szülőpointere exportkor azonos a film render-`ctx`-vel; a teljes állítás ezért feltételes.
- **Cáfoló kísérlet:** a korábbi G.7.7.3 azt állította, hogy `0x80c230` a `0xcbdd60` vtábla 0. slotja. Ezt megpróbáltam cáfolni a Ghidra #38 hívólistájával, az RTTI-táblával és a natív vcall utasítással. Az RTTI teljes sora `CTransTimeline::UI::vftable = 0xcbdcec`; a `0x80c230` a 29. slot (`+0x74`), ezért `0xcbdd60` csak a 29. elem címe, nem vtábla-kezdőcím. A `0xcbdd5c`-beli `0x52d480` az előző bejegyzés. A korábbi 18 slot-0 jelölt erre a függvényre nézve érvénytelen. A DirectShow-hívóban a `call [edx+0x74]` utasítás ezt függetlenül megerősíti. **A falszifikáció ellenőrzése:** ugyanaz a slot-szám jön ki mind az RTTI-lista (`29×4=0x74`), mind a futásidejű vcall offset alapján. A Ghidra „nincs közvetlen E8-hívó” állítása nem cáfolja a virtuális hívást.
- **Új cáfoló kísérlet:** azt próbáltam megcáfolni, hogy a seed konstruktorból nullázódik. A `0x74e580` létrehozó út és a `0x74d1c0` konstruktor követése azt mutatja, hogy a konstruktor a szomszédos mezőket és az akkumulátort nullázza, a `+0x108/+0x10c` mezőket viszont nem. A pin RTTI-metódusain futtatott offszet-térkép és a `paszta.memoria_kapu()`-val védett `.text`-pásztázás nem talált pin-metódusban közvetlen seedírót. **Ellenőrzés azonos mércével:** a bizonyíték csak a közvetlen, pinhez rendelhető mezőírás hiányát mutatja; az indirekt/helperes upstream írást nem zárja ki. Emiatt az alapértelmezett seed értékét nem állítom nullának.

##### G.7.8.5 Kész, ha — fejlesztői átadás, `src/picasapy/movie/slideshow.py`

- [ ] A szövegdia képkockája a kimeneti ciklusban, a dia helyi `k` indexével épül; az egyszeri `text_frames` előrenderelés megszűnik. A kockaszám és a fotók tartási ideje nem változik.
- [ ] A natív időbélyeg és a helyi kocka indexének leképezése rögzítve van. `t_k=k/fps` önmagában **nem igazolt**: a natív `t` a pin 100 ns-os órájából származik, a reset seedje `+0x108/+0x10c`.
- [ ] A 11-es stílus a G.7.8.3 képletét alkalmazza a mentett `trans` mezőkkel; a több-bájtos próbaszöveg kimenetén eldől, hogy a byte-index és a látható glyph-index hogyan felel meg.
- [ ] A 8-as stílus `advanceinterval`-hosszú smoothstep útja `B→A`, a 1-es stílus 0→255 lineáris alfája és egykomponensű smoothstep mozgása kockánként renderelődik. A textstyle1 `d` bemenete binárisan `desc+0xec`, nulla értéknél `desc+0xe8/3`; negatív értéknél a kezelő nem frissít. A `H+0x08` időeltolás tényleges szerepe és a `H+0x2c` geometriai végpont exportkori értéke pontosan feloldandó vagy referenciából mérendő, becslés nélkül.
- [ ] A Picasa 3.9 referenciából mindhárom stílus kockái `k` szerint dokumentálva; a kimeneti teszt kiválasztott kockái a referencia képkockáival összevetve. A tolerancia a mérésből származik, nem előre beállított érték.

##### G.7.8.6 Nyitott — a konkrét megszerzési út

- Ghidra-kör kell: `0x0074e580` — a `CDXSlideshowPin` létrehozásától az export-resetig melyik DirectShow-határ vagy segéd állítja a `+0x108/+0x10c` seedet, és milyen bináris értékkel? [blokkoló]
- Ghidra-kör kell: `0x0074d970` — a resetet megelőző exporthívási útban hol és milyen értékkel írják a két seedmezőt, ha az író nem a pin saját virtuális metódusa? [blokkoló]
- Ghidra-kör kell: `0x00814330` — a `.mxf`/TimelineXML `this+0x50` rekord szülőobjektuma a filmexportban hogyan jut el a `0x812470/0x8127b0` render-`ctx+0x48` listájához? Az objektumazonosságot kell eldönteni. [blokkoló]
- Ghidra-kör kell: `0x00816360` — a TimelineXML `this+0x4c` szülőpointere exportkor ugyanarra a kontextusra mutat-e, amelynek `+0x48` listáját a render-helper olvassa? [blokkoló]
- Ghidra-kör kell: `0x008127b0` — a `ctx+0x48` mintavételezett rekordjának `ctx+0x1a8`-ba másolása mely exportágon történik, és hogyan kapcsolódik az előző XML-parser szülőjéhez? [blokkoló]
- Ghidra-kör kell: `0x00810420` — a `0x809c50` hívásban a `H+0x2c`-t adó virtuális geometriai eredményt melyik konkrét osztály és mező állítja elő, és mi a koordinátajelentése/mértékegysége? [blokkoló]
- Mérés kell: eredeti Picasa 3.9 filmexport mindhárom stílussal, kockánkénti timestamp/pozíció/alfa/karakter-kiolvasással. A helyi `meroadat.tar` releváns film- vagy szövegdia-exportmintát nem tartalmazott; a referenciakockák és a natív ütem ezért `NINCS MEG`.

##### G.7.8.7 6. kör (2026-10-13): a két blokkoló Ghidra-pont — mi dőlt el, mi nem

*Bemenet: `~/picasapy-agent/referencia/ghidra-koteg-2026-10-13/0074d970.c` és `008127b0.c` (a `0x813330`, `0x80a930`, `0x611320`, `0x612350` callee-törzsekkel). A kötegben lévő `00715280.c` és `0071c4f0.c` a `+0x108/+0x10c` és a `+0x1a8` mezőt nem említi (szövegesen ellenőrizve), ezért nem releváns. A `0x74e580` és a `0x812470` dekompilátuma ebben a körben nincs meg.*

**1. A seed forrása (`CDXSlideshowPin+0x108/+0x10c`) — NYITOTT maradt.**

- Új, teljes reset-törzs (`0074d970.c`): `EnterCriticalSection(this+0x228)` alatt a `+0x108/+0x10c` qwordot **olvassa**, és ebből másol: `+0x208/+0x20c`, `+0x4b0/+0x4b4`, `+0x4b8/+0x4bc`. Nullázza: `+0x1fc`, `+0x4a8/+0x4ac`, `+0x218/+0x21c`. Visszatérési érték 0. A G.7.8.1 `[this+0x4b0]`/`[this+0x4b8]` másolása megerősítve; a `+0x208/+0x20c` másolás új.
- A reset **nem ír** a seedbe, az író tehát nincs ebben a fájlban. A seed írója a `0x74e580` (a pin létrehozója) vagy az exporthívási út egy eleme; ennek dekompilátuma nincs a kötegben. Az exportkori seed tehát továbbra is `NINCS MEG`. Ezt nem lehet következtetéssel pótolni, és a `0`-ra való beállítás sem igazolt.

**2. A TimelineXML → render-desc másolási út — RÉSZBEN zárva.**

Zárva (a `008127b0.c` / `0x813330` törzsében látszik):

- A factory desc-argumentuma a `ctx+0x1a8`: `008127b0.c:52`, `:69`, `:83` (`FUN_00810420(param_1, param_1 + 0x1a8)`).
- A `0x813330` ugyanezt a desc-et adja a `0x812aa0`-nak (`FUN_00812aa0(param_1, param_1 + 0x1a8, …)`), és a `*(int *)(param_1 + 0x1a8) == 4` ellenőrzéssel a `ctx+0x1432` jelzőt állítja be. A desc első dword-je tehát típusmező.
- A másoló-segéd (`0x612350`) a `[ESI+0xe4 … 0xf4]` öt dword-öt a `[EDI+0xe4 … 0xf4]`-ből másolja. Ez pontosan a factory által olvasott időblokk: `+0xe8` advanceinterval, `+0xec` transitiontime, `+0xf0` blacktime, `+0xf4` extra. A cél (ESI) és a forrás (EDI) a hívás előtt regiszterben van.
- A rekordlépés `0xf8`: a `0x813330` a `ctx+0x90` bázisból és a `ctx+0x94 >> 1` darabszámból számolja az utolsó rekord végidejét (`rec[+0xe8] + rec[+0xf0] + rec[+0xf4]`). A `0x611320` és a `0x80a930` ugyanezt a darabszámot az objektum `+0x4c`-jéről olvassa (`>> 1`), az indexet `+0x148`-ról. Ha az objektum `ctx+0x48`, ez egybevág a `ctx+0x90/+0x94` olvasásával (`obj+0x48` bázis, `obj+0x4c` darabszám). **Ez szerkezeti egyezés, nem bizonyíték** az objektum azonosságára: a `008127b0`-ban az EAX-ban lévő `this` értéke nem látszik.

Nyitva:

- A `008127b0` melyik objektumból (EAX) és melyik rekordból (EDI) másol `0x612350`-nel `ctx+0x1a8`-ba. A `.c`-ben a hívások argumentumai nem látszanak (`FUN_00611320();`, `FUN_00612350();`). A „`ctx+0x48` → `ctx+0x1a8`” állítás a korábbi asm-olvasatra támaszkodik (`0x812553`–`0x81258c`, `0x8129c1`–`0x8129e2`), amelyet ez a kör nem tudott újraellenőrizni.
- A parser-szülő azonossága: a TimelineXML `this+0x4c` szülőpointere exportkor ugyanaz-e, mint a render `ctx` — `NINCS MEG`.

**3. Mit nem lehet ebből még állítani.** Az animáció képkockánkénti értéke (`t_k`, a `k↔t` leképezés, a Gördülő pixel-végpontjai, a „Jó napom van” `H+0x2c` végpontja) a seed és a parser-szülő azonossága nélkül nem zárható le. A referencia-mérés (Picasa 3.9 filmexport) szintén hiányzik. A jegy „Kész, ha” pontjai ezért nem teljesíthetők ebből a körből.

#### G.7.9 Értékjegyzék a #4615 átadáshoz

| érték vagy állítás | forrás |
|---|---|
| `CDXSlideshowPin` vtable `0x00cb1a08`, render slot `0x0074dfc0`, reset slot `0x0074d970` | bináris (`RTTI 0x00cb1a08`, `0x74dfc0`, `0x74d970`) |
| A pin konstruktor nem írja a `+0x108/+0x10c` seedmezőket | bináris (`0x74e580`, `0x74d1c0`, `0x74d4f5`–`0x74d517`) |
| timestamp átváltó osztó `10 000 000` | bináris (`0x00989680`, operandus `0x74e1ee`) |
| `+0.02` időeltolás | mérés (G.6.2 szintetikus natív ellenőrzés; literál `0x00cf48a8`) |
| `CTransTimeline::UI::vftable = 0x00cbdcec`, `0x80c230` slot = 29 / vcall offset `0x74` | bináris (`RTTI 0xcbdcec`; `0x74e248`–`0x74e251`) |
| render factory desc pointere `ctx+0x1a8` | bináris (`0x8128a2`–`0x8128aa`; `0x813804`–`0x81380c`; `008127b0.c:52,69,83`; `0x813330` → `0x812aa0`) |
| reset (`0x74d970`) olvassa a seedet, és másolja `+0x208/+0x20c`, `+0x4b0`, `+0x4b8`-ba; nullázza `+0x1fc`, `+0x4a8`, `+0x218`-at | bináris, teljes dekompilátum (`0074d970.c`, G.7.8.7) |
| film-végidő és darabszám: `ctx+0x90` bázis, `ctx+0x94>>1` darabszám, `0xf8` lépés | bináris (`0x813330`, a `008127b0.c` callee-törzse); az objektum azonossága `ctx+0x48` szerkezeti egyezés, nem bizonyíték |
| TimelineXML `this+0x50` → szülő `+0x48` lista, majd render `ctx+0x48` → `ctx+0x1a8` rekordmásolás | bináris (`0x8152f0`, `0x816360`, `0x80a460`, `0x812470`, `0x8127b0`, `0x612350`); a szülőpointer és render-context azonossága nyitott |
| Írógép natív üteme `len/d` bájt/s; `d=transitiontime`, nulla esetén `advanceinterval/3`, negatív esetén nincs frissítés | bináris (`0x8104b9`–`0x8104dc`, `0x80a080`; G.6.3/G.6.7) |
| Gördülő interpoláció `3p²−2p³`, időmező `advanceinterval` | bináris (`0x818cf0`; `0x810fe5`; G.6.4/G.7.5) |
| `textstyle1` alfa `0→255`, lineáris; `d` input `desc+0xec`, nulla értéknél `desc+0xe8/3`; negatív értéknél a kezelő nem frissít | bináris (`0x8104b9`–`0x8104dc`, `0x8107a0`–`0x8107b2`, `0x809c50`, `0x809cd0`, `0x809af0`, `0x809d20`) |
| export seed tényleges értéke, parser-szülő és render-context azonossága, `k↔t` leképezés | NINCS MEG |
| Gördülő tényleges pixeles A/B és textstyle1 `H+0x2c` mozgásvégpont/időszemantika | NINCS MEG |
| referenciafilm képkockái, a három stílus natív mérési táblája, kimeneti képteszt | NINCS MEG |

#### G.7.10 7. kör (2026-10-14): célzott újraellenőrzés a #4615 átadáshoz

*Bizonyítottsági fok: **feltételes** arra, hogy az animáció ténylegesen látszik a film exportjában. A factory és a kockakezelők animációs útját két külön bináris nézet támasztja alá; a natív kimenet és az esetleges későbbi pozíció-felülírás nincs képkockán mérve.*

**A út — a factory hívási ágai és a kockakezelők.** A stíluslista neveit a `referencia/stringres-en-hu.tsv:456,458,465` rendeli a `textstyle1`, `textstyle11`, illetve `textstyle8` beállításhoz. A `0x00810420` film-factory kódjában az 1-es ág (`0x00810656`) a `TextFadeMove` konstruktort és építőt hívja (`0x008107a7` → `0x00809c50`; `0x008107ba` → `0x00809cd0`); a 8-as ág (`0x00810ed0`) ugyanezt a kezelőt hívja (`0x00810fee`, `0x0081100d`), majd a `+0x48/+0x49` jelzőket nullázza (`0x00811005`–`0x00811009`). A 11-es ág (`0x00811cd8`) a `TextTypeWriter` kezelőt hívja (`0x00811db7` → `0x00809fe0`). A `0x00809d20` kockakezelő az `0x13` eseményen, az esemény `[+0x10]` időbélyegéből frissíti a dia `+0x14c/+0x150` pozícióját a `0x009debd0` híváson át; a `0x0080a080` az idővonal értékét egész karakterhosszként írja a dia `+0x34c` mezőjébe, és változáskor újrarajzolást kér. Forrás: célzott diszasszemblálás a hivatkozott címeken.

**B út — RTTI-vtáblák, az első út nélkül újraolvasva.** A bináris-index RTTI-táblájában a `TextFadeMoveHandler::vftable` (`0x00cbdb94`) 3. slotja `0x00809d20`, a `TextTypeWriterHandler::vftable` (`0x00cbdbbc`) 3. slotja `0x0080a080`; a beágyazott `TextFadeHandler::vftable` (`0x00cbdb80`) 3. slotja `0x00809b40`. Ez a külön RTTI→slot út a factory által elért kezelők per-frame függvényeit azonosítja, és egyezik az utasításszintű leolvasással. A két út a kezelőstruktúra meglétét támasztja alá; önmagában egyik sem képkockamérés.

**Cáfoló kísérlet — lehetséges pozíció-visszaírás.** A `ytFlyingNode::vftable` RTTI-sora tartalmazza a `0x00819040` metódust. Ennek célzott diszasszemblálása szerint a metódus a dia `+0x14c/+0x150` mezőit a `+0x388/+0x38c` mezőkkel veti össze, eltéréskor pedig a `0x009debd0`-val visszaírja az utóbbi párt. Ez valódi lehetséges cáfoló út a Gördülő pozíciójára. A célobjektum azonossága és az exportkori meghívás nincs bizonyítva, ezért a keresés nem cáfolta, de nem is igazolta a filmben látható mozgást; a `+0x388/+0x38c` tartalma **NINCS MEG**.

**Mérőanyag és a #4615 elfogadási pontjai.** A helyi mérőarchívum tagneveiben nem találtam film-/szövegdia-/MXF-hivatkozást, és videófájl-kiterjesztésű tagot sem; a repóban nincs `research/testdata/` könyvtár. Semmit nem bontottam ki. A meglévő `slideshow.py` útja továbbra is állóképet ír: a 623. sor egyszer hozza létre a `text_frames` listát, a 640. sor fűzi ezt a filmbe, a 697–699. sorok pedig ugyanazt a képkockát írják ki a tartási ciklusban.

- [ ] A három stílus animációja a natív filmben és képkockás referencia-összevetése — **NINCS MEG**; Picasa 3.9 export és képkockánkénti mérés kell.
- [ ] A helyi kimenet képkocka-tesztje — **NINCS MEG**; ez fejlesztői és tesztmunka, nem kutatási lelet.

#### G.7.11 #4615 célzott bináris kör: kockaidő, pozíció és írógép-hossz (2026-10-14)

*Bizonyítottsági fok: **feltételes**. A factory → kezelő út és a kezelők idővonal-kiértékelése utasításszinten leolvasható; az RTTI és a nyers vtábla ettől függetlenül megerősíti a slot–függvény azonosságot. A képletekhez nincs külön Picasa 3.9 képkockamérés, és a lehetséges későbbi pozíció-felülírás, valamint az exportkori objektumazonosság nyitott. Ezért a binárisból következő képlet nem bizonyítja önmagában, hogy ugyanaz az érték látható a film kimenetében.*

**Képkockaidő és arány a két kezelőben.** A `TextFadeMoveHandler` slot 3 függvénye (`0x00809d20`) és a `TextTypeWriterHandler` slot 3 függvénye (`0x0080a080`) a `0x13` eseményből a qword időbélyeget olvassa (`event+0x10`). Mindkettő a kezelőhöz épített idővonalat adja a `0x009e5e20` kapunak, majd a `0x009e5e70` kiértékelőnek. A kapu csak pozitív `H+0x08` időtartamnál enged frissítést. Az idővonal-kiértékelő a `t+0.02` értéket használja, a szegmens startját (`L`) kivonja, majd az eredményt az `end−start` időtartammal osztja és `[0,1]` közé korlátozza. Így `p=clamp((t+0.02−L)/d,0,1)`. A `0.02` konstans címe `0x00cf48a8`; az esemény időbélyegének magasabb szintű, filmkockaindexhez viszonyított leképezése itt nincs bizonyítva.

- A Gördülő stáblista (`textstyle8`) `d=desc+0xe8` (`advanceinterval`), és `L=desc+0xf0+desc+0xf4`. A pozíció interpolátora `S(p)=3p²−2p³`, ezért a kezelt komponens `P=B+S(p)(A−B)`. A kezelő `H+0x49=0` jelzője miatt a `dia+0x150` komponenst (Y) írja; `H+0x48=0` miatt alfát nem animál. A factory által beállított végpontok: `B=h_b`, `A=0.5·(h_a−(E+0x54−E+0x4c))`. `h_a` a szövegdia téglalapjának alsó–felső különbsége, `h_b` a háttérdia téglalapjának alsó–felső különbsége, `E+0x4c/+0x54` a szövegobjektum metódusa által visszaadott függőleges pár. Az induló és végső érték tehát futásidejű geometriai képlet, nem rögzített pixelkonstans; konkrét exportérték **NINCS MEG**.
- A „Jó napom van” (`textstyle1`) `d=desc+0xec` (`transitiontime`), ha ez nem nulla; pontosan nulla esetén `d=desc+0xe8/3`. Negatív `transitiontime` esetén a factory megtartja a negatív értéket, de a kezelő pozitív-időtartam kapuja nem frissít. Az idővonal kezdete `L=desc+0xf0+desc+0xf4`; az alfa- és a pozíció-idővonal is a `[L,L+d]` intervallumot használja, ezért `d` ezek időtartama. A kockaidőből számolt arány `p=clamp((t+0.02−L)/d,0,1)`. A lineáris alfa `0→255`; a pozíció smoothstep útjának kezdete `H+0x28=0`, vége `H+0x2c=−M`, és az X komponenst (`dia+0x14c`) írja. `M` a kiválasztott szövegobjektum `vtable+0x30` metódusának visszatérési értéke; a metódus pontos osztálya, `M` geometriai jelentése, egysége és exportkori értéke **NINCS MEG**.
- Az Írógép (`textstyle11`) az időarányt ugyanezzel a `p` képlettel kapja. `d=desc+0xec`, ha nem nulla; nulla esetén `d=desc+0xe8/3`; negatív `d` mellett nincs frissítés. A timeline értéke `len·p`; a kezelő ehhez `0.5`-et ad, egészre csonkítja, és legalább `1`-et ír a dia `+0x34c` mezőjébe. Ez bájtindex, nem bizonyított Unicode-karakterindex.

**Az írógép hosszának egysége.** A `0x00811d9e` körüli factory-ciklus a `+4`-es szövegadat-pointert bájtonként növeli, az első NUL bájtnál áll meg, és a terminátor nélküli pointerkülönbséget adja a `0x00809fe0` konstruktornak. A konstruktor ezt a bájthosszt tárolja `H+0x0c`-ban; a `0x0080a030` építő ezt a mezőt teszi az idővonal végértékévé. Ez a vizsgált út keskeny, NUL-terminált karaktertárat és bájtszámot bizonyít, nem UTF-16 kódosegység- vagy Unicode-kódpontszámot. Az adattár pontos kódolása (MBCS, UTF-8 vagy más), illetve a több-bájtos karakter részleges megjelenítése **NINCS MEG**.

| érték vagy állítás | forrás |
|---|---|
| `TextFadeMoveHandler` slot 3 = `0x00809d20`; `TextTypeWriterHandler` slot 3 = `0x0080a080` | bináris (`RTTI 0x00cbdb94`, `0x00cbdbbc`; nyers PE-vtábla-dwordok ugyanott; factory-ágak `0x810fee`, `0x811d9e`) |
| Az esemény típusa `0x13`, időbélyege qword `event+0x10` | bináris (`0x809d20`, `0x80a080`) |
| Időkapu `H+0x08>0`; kiértékelési arány `clamp((t+0.02−L)/d,0,1)` | bináris (`0x9e5e20`, `0x9e5e70`); `0.02` literál: `0x00cf48a8` |
| `textstyle8`: `d=desc+0xe8`, `L=desc+0xf0+desc+0xf4`, `B=h_b`, `A=0.5·(h_a−(E+0x54−E+0x4c))`, Y-írás; smoothstep `3p²−2p³` | bináris (`0x810ed0`–`0x811009`, `0x809cd0`, `0x809d20`, `0xc72150`, `0x818cf0`; geometriához G.7.5 és `0x9e51a0`) |
| `textstyle1`: `d=desc+0xec`, pontosan nulla esetén `desc+0xe8/3`; negatív d-nél nincs frissítés; `L` közös; alfa `0→255`; X út `0→−M` | bináris (`0x8104b9`–`0x8104dc`, `0x8107a7`–`0x8107b2`, `0x809c50`, `0x809cd0`, `0x809eb0`, `0x809d20`) |
| `textstyle1` `M` metódusának szemantikája/egysége és futásidejű értéke | NINCS MEG |
| `textstyle11` bájthossza és az idővonal végértéke | bináris (`0x811d9e`–`0x811db7`, `0x809fe0`, `0x80a030`, `0x80a080`) |
| Az írógép-adat pontos kódolása és a bájtindex glyph-megjelenítési hatása | NINCS MEG |
| Diahelyi kockaindex ↔ esemény-időbélyeg, referenciakockák, exportkori geometriai számok | NINCS MEG; a helyi `meroadat.tar` tagnevei között nem volt film-/szövegdia-minta, így nem bontottam ki mérőadatot |

**A két független út.**

- **A út — utasításszintű adatfolyam:** a `0x00810420` factory stíluságai a desc mezőket a megfelelő konstruktoroknak/építőknek adják; a `0x809cd0` és `0x80a030` a startot, végidőt és végértéket állítja be; a két slot 3 függvény az esemény időbélyegével meghívja a közös időkaput és kiértékelőt. Ez az út adja a fenti arányt és a stílusmezőket.
- **B út — RTTI és nyers vtable:** az index RTTI-bejegyzései és a PE-ben közvetlenül kiolvasott négy dword egyaránt a `0x00cbdb94`/`0x00cbdbbc` vtáblák 3. elemét köti a két slot 3 függvényhez. Ez egyezik a factory által létrehozott kezelőtípusokkal, de önmagában nem méri vagy bizonyítja az időképletet. A négy kérdés képlet-szintű állításai ezért **feltételesek**: a B út a függvényazonosságot ellenőrzi, nem egy második, független képletmérést.

**Cáfoló kísérlet — a pozíció későbbi felülírása.** Azt próbáltam cáfolni, hogy a `TextFadeMoveHandler` által írt pozíció biztosan a kimeneti képkockán marad. A `ytFlyingNode::vftable` RTTI-sora a `0x00819040` metódushoz vezet; az offset-térkép a `+0x14c/+0x150` olvasását és írását, illetve a `+0x388/+0x38c` mezők írását mutatja; a metódus utasításai összevetik a két mezőpárt, és eltéréskor a `+0x388/+0x38c` párból visszaírják a dia pozícióját. **Az ellenőrzés ugyanazzal a mércével:** az RTTI azonosítja a metódust, az offset-térkép és az utasítások alátámasztják a mezőkapcsolatot, de nincs bizonyíték arra, hogy ez ugyanaz az objektum, és a metódus a handler után, a filmkocka mentése előtt fut. Ez valódi lehetséges felülírás, de nem bizonyítja és nem is cáfolja a látható animációt; a kimeneti képkocka-mérés továbbra is szükséges.

**A #4615 „Kész, ha” pontjai a kutatás után.**

- [ ] A három stílus animál a filmben, mért kép-összevetés a referenciával — **NINCS MEG**. A bináris út animációs kezelőket és képleteket igazol, de nincs eredeti Picasa 3.9 kockamérés, referencia-összevetés vagy exportkori érték.
- [ ] Kimenet-teszt a képkockákra — **NINCS MEG**. Ez implementációs és tesztfeladat; a jelen kutatási kör nem módosított kódot vagy tesztet.

#### G.7.12 #4615: a textstyle1 X-végpontja és az írógép szövegkódolása (2026-10-14)

*Bizonyítottsági fok: mindkét kérdésre **feltételes**. A bináris két külön útja egyezik az M geometriájáról és az UTF-8 belső szövegkezelésről; a futásidejű objektum pontos típusa/exportértéke, illetve egy ékezetes `.mxf` mintafájl bájtsorozata nem áll rendelkezésre. A következtetés nem képkockamérés.*

**1. `textstyle1` („Jó napom van”): M a transzformált szövegdoboz X-minimuma.** A `0x00810761`–`0x00810771` a kiválasztott objektum `vtable+0x30` metódusát hívja egy négyelemű kimeneti téglalappal. A visszaadott téglalap első egész mezőjét a factory `0x00810783` olvassa, előjelét megfordítja (`neg ecx`), majd a `0x00809c50` konstruktorba adja; így az idővonal végpontja `H+0x2c=−M`. A dia X koordinátáját (`dia+0x14c`) író kezelő ezt a végpontot használja.

A `0x009e08b0` ismert text-node megvalósítása előbb a saját `vtable+0x28` téglalap-metódusát hívja. Érvénytelen/üres téglalapnál a `+0x244` gyermek téglalapját is felhasználhatja; a `0x009de880`-nal lekéri az objektum és ősei transzformációját, a `0x00a4a240` pedig a helyi téglalap négy sarkát transzformálja, majd a befoglaló X/Y-minimumot és maximumot egész téglalapként adja vissza. A `ytMultiTextNode` RTTI-táblájában a `vtable+0x30` erre a `0x009e08b0` metódusra mutat; a `vtable+0x28` (`0x009e0ad0`) gyorsítótár esetén az objektum `+0x188/+0x18c/+0x190/+0x194` mezőiből olvassa a helyi téglalapot, máskülönben a `vtable+0x20` metódusra delegál. A geometriai képlet tehát:

`R=[x0,y0,x1,y1]` a szövegobjektum helyi téglalapja; `T(x,y)=(m0·x+m1·y+m2, m3·x+m4·y+m5)` a hat floatból álló összegzett affin mátrix; `M` a `T` által transzformált négy sarok X-koordinátájának minimuma, a kódban az `0x00cf4160`-ból olvasott `0.499` levonása és `fistp` egészkonverziója után. Ez a szövegdoboz téglalapjától és az objektum/ősök transzformációjától függ; közvetlen, önálló dia-szélesség-képletet a vizsgált ág nem olvas. A konkrét exportkori `R`, mátrix, `M` és koordinátaegység (képpont vagy más exportegység) **NINCS MEG**. Az `0x00809eb0` nem M-kiértékelő: az alfa idővonalát építi az alfa-bájtos mezőkből (`+0x0c/+0x0d`), ezért nem ez szolgáltatja az X-végpontot.

**2. Írógép (`textstyle11`): bájtszám, UTF-8 belső szövegút.** A G.7.11-ben rögzített factory-ciklus (`0x00811d9e`–`0x00811db7`) a `+4` pointert bájtonként lépteti az első NUL-ig, a bájthosszt a `0x00809fe0` konstruktornak adja; ez nem UTF-16 kódosegység-számolás. Az azonos factory közeli stringsegédje (`0x008106a9`–`0x008106bf` → `0x009863f0`) UTF-8-szerű vezetőbájt-hosszakat léptet: ASCII bájt 1, `0xc0`–`0xdf` 2, `0xe0`–`0xef` 3, `0xf0`–`0xf7` 4, és ellenőrzi a folytató bájtok `0x80` alsó határát. Az MXF `text` XML-elemének dispatch ága (`0x00815c48`–`0x00815cb1`) a szöveget stringobjektummá olvassa, majd a propertybe másolja. Egy ettől különálló Windows-határfüggvény (`0x009affb0`) a `MultiByteToWideChar` importot `0xfde9` kódlappal, azaz CP_UTF8-ként hívja.

Ez az út a film szövegének keskeny bájttárolójára és az alkalmazás UTF-8-kezelésére mutat. A magyar ékezetes betűk UTF-8 alakja 2 bájt (az ASCII karakteré 1); a típusról azonban a bájtonkénti NUL-keresés önmagában nem döntene. A konkrét MXF fájlba írt kódolás és egy ékezetes szöveg tényleges bájtsora **NINCS MEG**, mert helyi `.mxf`/`.pxc` minta nem volt elérhető.

| érték vagy állítás | forrás |
|---|---|
| `textstyle1` M-et a kiválasztott objektum `vtable+0x30` metódusától kapja; `H+0x2c=−M`; a dia X mezője `+0x14c` | bináris (`0x00810761`–`0x008107a7`, `0x00809c50`, `0x00809d20`) |
| Az ismert text-node getter a helyi RECT-et az objektum/ősök mátrixával befoglaló téglalappá alakítja; M annak X-minimuma, `0x00cf4160=0.499` korrekcióval egészítve | bináris (`0x009e08b0`, `0x009de880`, `0x00a4a240`, adat `0x00cf4160`; RTTI: `ytMultiTextNode::vftable`, `0x009e08b0`; helyi RECT: `0x009e0ad0`) |
| A `ytMultiTextNode` gyorsítótárazott helyi RECT mezői `+0x188/+0x18c/+0x190/+0x194`; az érvényesség jelzője `+0x20f` | bináris (`ytMultiTextNode` RTTI és offset-térkép; `0x009e0ad0`) |
| A factory bájthosszt ad az írógép-konstruktornak; az ékezetes betűk belső UTF-8 bájtszáma 2 | bináris (`0x00811d9e`–`0x00811db7`, `0x00809fe0`, UTF-8 léptető `0x009863f0`); fájlszintű példa: **NINCS MEG** |
| Az MXF `text` mező stringobjektumba kerül; az app egyik több-bájtos → UTF-16 határa CP_UTF8-at választ | bináris (`0x00815c48`–`0x00815cb1`, `0x009affb0`, import: `MultiByteToWideChar`) |
| Exportkori helyi RECT, transzformációs mátrix, `M` és koordinátaegység; konkrét ékezetes MXF bájtsor | **NINCS MEG**; Picasa 3.9-es minta/export és célzott kockamérés kell |

**A két független út.**

- **A út — közvetlen adatfolyam:** a `0x00810761` vtable-hívás kimeneti téglalapjának első mezője kerül negálva `H+0x2c`-ba. A `0x009e08b0` és `0x00a4a240` utasításai visszavezetik ezt a mezőt a text-node RECT-re és a transzformált sarkok X-minimumára. A string oldalon a factoryban hívott `0x009863f0` a több-bájtos karakterek UTF-8 vezetőbájtjai alapján léptet.
- **B út — RTTI/adatmezők és külön kódolási határ:** az RTTI a `ytMultiTextNode` `+0x30` slotját `0x009e08b0`-hoz, a `+0x28` slotját `0x009e0ad0`-hoz köti; az offset-térkép és a mezőolvasások külön igazolják a lokális RECT-forrást. A másik kódolási út az MXF `text`-dispatcher stringobjektum-másolása és a független `0x009affb0` CP_UTF8 hívása. Mindkét pár ugyanabba az irányba mutat; a konkrét exportpéldát egyik sem helyettesíti.

**Cáfoló kísérlet.** M-re azt az alternatívát próbáltam igazolni, hogy a végpont közvetlenül a dia szélessége vagy egy rögzített `desc` érték. A factory közvetlenül egy objektum-vtábla `+0x30` slotját hívja, a getter pedig RECT-et és összegzett transzformációt olvas; az RTTI-s slotkötés és az offset-térkép ezt külön ellenőrzi. Az alternatíva nem állja ki ugyanazt az utasításszintű mércét. Kódolásnál az ANSI/CP_ACP lehetőséget a bájtonkénti ciklus önmagában nem cáfolja; a külön UTF-8 léptető és a CP_UTF8 hívás az alkalmazáson belüli UTF-8 értelmezést támasztja alá. A fájlszintű alternatíva a hiányzó MXF-minta miatt nyitva marad.

**A #4615 „Kész, ha” pontjai.**

- [ ] A három stílus animál a filmben, mért kép-összevetés a referenciával — **NINCS MEG**; az M geometriai bináris útja és a korábbi G.7.11 képletei nem helyettesítik a Picasa 3.9 referenciaexportot és a kockánkénti mérést.
- [ ] Kimenet-teszt a képkockákra — **NINCS MEG**; ez kód- és tesztmunka, ebben a kutatási körben nem készült.
