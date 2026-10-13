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
utasításai nem számítanak arckivágást. A későbbi timeline-út
(`0x0074dfc0`, `0x008127b0`) a modell kliplistáját dolgozza fel, de a
teljes arcmező-író/olvasó lánc és a renderelt képkivágás képlete nincs
azonosítva.

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

`0x008127b0` a `0x00810420`-nak a timeline objektumot és annak `+0x1a8` staging-objektumát adja át (`0x008128a2`–`0x008128aa`). A `0x00810420` közvetlenül olvassa a staging-objektum `+0x14` bájtját, de nincs benne közvetlen `+0x18…+0x24` operandus; a cropfogyasztó az indirekt hívások mögött maradt.

**Cáfoló keresés a mezőeltolásos találatokra:** a `paszta.py` streaming
`.text`-pásztája talált `+0x18…+0x24` olvasót a `0x00819f50` címen, de az
`0x38`-as arcrekord landmark-floatjait transzformáló HOG-geometriai
segédfüggvény; hívója `0x00873cb0`, RTTI-je a
`HOGSimilarityComputer::vftable`-hez tartozik, nem a `0xf8` timeline-klip
bejárója. A `0x007fd8c0` jelölt `0xf8` lépést és `+0x18/+0x20` hivatkozást
is tartalmaz, de az időintervallum-rekord double mezőit olvassa. Mindkettő
hamis pozitív, ezért az offset-egyezés vagy a lépésköz önmagában nem
azonosítja a cropfogyasztót.

Ghidra-kör kell: 0x008127b0 — oldd fel a `0x00810420` indirekt hívásai mögötti per-klip renderelőt, és kösd a `0xf8` lépésű kliprekord `+0x18…+0x24` pixel-rectjét a kivágást/transzformációt számító fogyasztóhoz; add meg a pontos crop-, margó-, képarány- és szemigazítási képletet, továbbá hogy a `+0x8` selector hozzáfér-e a `+0x4e0` rekord landmark-mezőihez. [blokkoló]
Ghidra-kör kell: 0x00456610 — kösd össze a `faces=` ág `rect64`-feldolgozását az imagedata `facerect` mezőjével, amelyet a `0x00446610` olvas; döntsd el, hogy a `.picasa.ini` `faces=` sorához a `0x0049d560` út tartozik-e. [blokkoló]
- **NINCS MEG:** a teljes `.picasa.ini faces=` → imagedata `facerect` → `+0x4e0` adatút; a lejátszási crop képlete, margója, cél-képaránya, szemhez igazítása és a clip-selector landmark-használata.

**Bizonyítottsági határ:** a klipmezők nyers másolása és a low-res maszk
képlete a diszasszemblálás és az elkülönített QEMU-futás egyezésével
megerősített. A tényleges lejátszási cropképlet nincs meg; a QEMU-próbák
nem hajtották végre az INI-betöltést vagy a teljes timeline-renderelést.

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
| **0** (Igen) | alkalmazd | átvált a `makemoviepanel/tab3`-ra és elsüti a `recompute` parancsot — **a film nem készül el most** |
| **2** (Mégse) | ne csinálj semmit | a művelet elmarad |
| egyéb (Nem, vagy a kapu ki van kapcsolva) | menj tovább | a függő módosítások **eldobódnak**, a film a legutóbb alkalmazott állapotból készül |

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

#### G) A készítési idő küszöbe: szomszédos csoportosítás, ordering-függő kiválasztás (#4194)

**2026-10-07, 4. kör — a kiválasztási ág azonosítva; a paraméternevek
helyesbítve.** A `0x006175c0` hívó utasításai és az öt argumentumot takarító
`ret 0x14` alapján a `0x0081b800` argumentumai: `param_1` = gyűjtemény,
`param_2` = hossz, `param_3` = `.mxf` `ordering`, `param_4` =
`burstmodethresh`, `param_5` = `removelowresfaces`. Tehát a lentebbi korábbi
„mode” azonosítás **helyesbítendő**: az ágakat az `ordering` választja,
`param_5` nem kiválasztási mód.

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

**A rekordmezők íróinak pásztázása — pontos eltolás, a célrekord írója nyitott
(2026-10-05, #4194 folytatás).** A teljes `.text` `+0x30/+0x34` írásainak
pásztázása több, egymástól eltérő rekord- és objektumtípust talált; az
eltolás egyezése önmagában nem azonosít típust. A releváns jelölt
`0x00823620`: `0x823b3b`-nél a saját, `0x38` bájtos kimeneti rekord
`+0x30` mezőjébe egy bemeneti dword-vektor elemét, `0x823b4b`-nél a
`+0x34` mezőjébe egy másik bemeneti vektor elemét írja. Ugyanebben a
függvényben a rekord `+0x30` értékével egy táblázatot indexel
(`0x823b92`–`0x823bb0`), a `+0x34` értékét pedig egy virtuális metódusnak
adja át (`0x823c53`–`0x823c69`); a rekord további mezőit a
`conf/pan/leye/reye/mouth` szövegannotáció köti arcjellemzőkhöz
(`0x823c41`).

Ezt az írót a `0x00824090` közvetlen hívása kapcsolja egy
`[this+0x4e0]` kimenethez (`0x824164`–`0x824181`). A Filmkészítő útján
`0x006175c0` hívja a `0x0081b800`-at, amely szintén `[this+0x4e0]`-t
használ. A két, azonos eltolású lista objektumazonossága
**nincs bizonyítva**. A teljes írópásztázás más ütközést is talált:
`0x004e41f0` egy beágyazott `0x38` bájtos alobjektum `+0x30/+0x34`
mezőit nullázza (`0x4e438c`–`0x4e43cd`), miközben ugyanazon külső objektum
`+0x4e0` listáját külön inicializálja (`0x4e4510`–`0x4e4516`). Ezért a
Filmkészítő rekordjának tényleges írója és a `+0x30/+0x34` szemantikája
**NINCS MEG**; az `0x00823620` archoz kötött adatútja nem bizonyítja, hogy
a Filmkészítő rekordjában a mezők arcszámot, arcméretet vagy pontszámot
tárolnak.

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

**Bizonyítottsági határ:** a `0x008781a0` reducer minimum- és döntetlenszabálya
**megerősített**: A) utasításszintű olvasat; B) külön natív QEMU-futtatás.
A kiválasztási algoritmus ága és döntési szabálya szintén **megerősített**:
`ordering=0` alatt súlyozott getterminimum, `ordering=1/2` alatt minimális
összköltségű gráfút. A HOG/Neven nevesítése és súlyainak hozzárendelése
**feltételes** (utasításszintű bizonyíték). A csoport konkrét fotójának
indexe, a gettermezők szemantikája és a gráf-élek pontos költségképzése **NINCS MEG**. Ezért az
„első”, „utolsó” vagy „jobb minőségű” fotó minden csoportra érvényes állítása
nem tehető; csak a nulla `ordering` pontozott útján bizonyított, hogy nem
mindig az első nyer.

**Fejlesztési átvezetés a #4182-höz:**

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Az eredeti bináris a szomszédos idők között `delta >= T` esetén új csoportot kezd. `ordering=0` súlyozott getterminimumot választ; a feltételes scorerazonosítás szerint ez HOG `1.0` súlyú és beállítástól függő Neven `0.4f` súlyú értékeit összegzi. `ordering=1/2` minimumköltségű gráfútvonalat választ. A `+0x30/+0x34` rekordmezők használata ismert, a rekordírójuk és szemantikájuk, a gráfélek pontos költsége és a végső fotóindex **NINCS MEG**. | A `burstmodethresh` tárolódik és átadódik a QML/controller rétegen; az `src/` alatti hivatkozásokban nincs képszűrési fogyasztó. Az `ordering` 0/1/2 és a `removelowresfaces` mező átadása megvan. | A #4182-ben a `delta >= T` szomszédos csoportosítás implementálható. A megtartási algoritmusban `ordering=0`-nál reprodukáld a getterek súlyozott minimumát, `ordering=1/2`-nél a költségminimumú útvonalat; ne nevezd a minimális pontszámot képi minőségnek. A fotórekord mezőinek előállítását és a gráf-élek költségét csak az alább nyitott rekordíró/index-visszakötés tisztázása után implementáld. `Kész, ha`: (1) #4182 implementációja ugyanazt az időcsoportot adja a QEMU-s `[0,3240,6480]` és `[0,3600,7200]` esetekre; (2) `ordering=0` két valós rekordos etalonban a súlyozott getterminimumot és döntetlennél az első bejárt jelöltet adja; (3) `ordering=1/2` valódi rekord-indexű etalonjai a minimális összköltségű útvonalat és döntetlen esetén a korábbi elődöt adják; (4) az etalonok kimeneti fotóindexe diszasszemblálással vagy natív futással függetlenül egyezik. |

Nyitott: melyik konkrét fotórekord-index felel meg egy kiválasztott
jelöltnek; ki írja a Filmkészítő `[obj+0x4e0]` rekordlistáját; mit jelentenek
a `+0x30/+0x34` mezők; hogyan áll elő a `ordering=1/2` gráf minden élének
költsége. Célzott következő kör:
`Ghidra-kör kell: 0x00823620 — a Filmkészítő [obj+0x4e0] lista 0x38 bájtos rekordjának írója, a +0x30/+0x34 mezők forrása és jelentése [blokkoló]`
`Ghidra-kör kell: 0x00874320 — a nyolcbájtos kimeneti elemek mezői/indexei hogyan kötődnek a fotórekordokhoz, és mi a 0x00877c50 teljes bemeneti szerződése? [blokkoló]`
`Ghidra-kör kell: 0x00877c50 — az ordering=1/2 út minden élköltsége mely rekordadatokból áll elő, és hogyan lesz a végső útból fotóindex? [blokkoló]`

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
határ (utasításszintű olvasat + natív QEMU-mérés); továbbá az `ordering=0`
súlyozott minimum- és az `ordering=1/2` gráfút-választási mechanizmusa
(Ghidra-dekompilátum + utasításszintű olvasat). **Nyitott:** a kiválasztott
gráfjelölt pontos fotóindexe, a `+0x30/+0x34` mezők szemantikája és a
gráfélek teljes költségképzése.

**Erős**: a `[panel+0x4f0]`/`[+0x4f1]` jelzők jelentése.

### 2.6 A MakeMoviePanel (a „Film készítése" párbeszéd) teljes beállítás-leltára

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

### 2.7 A film-előnézet vezérlősávja (`video_control_bar2`) — MŰKÖDÉS

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
| Hozzáadás a képernyővédőhöz… | `ID_SCREENSAVER` | a képek `screensaver=yes` ini-kulcsot kapnak (`picasa-ini-format.md`); a `saverlist.txt` tárolja a listát |
| Ajándék CD készítése… | `ID_BURNCD` | a `cdautorun/` mappa tartalma megy a lemezre (Windows autorun + Mac `.app`), dialógus: `runtime/cdchoose.fen` |
| Közzététel a Bloggeren… | `ID_EXPORT_SENDTOBLOGGER` | a `buttons/core-lh2.pbz` `custombutton/blogger` gombja: `verb="hybrid"`, URL `https://photos.blogger.com/picasa-post.g` — a szolgáltatás megszűnt |
| Exportálás TiVo DVR-re… | `ID_TIVO` | a `plugins/ytITivo.yti` plugin (TiVo Desktop-integráció) |
| Indexképek nyomtatása… | `ID_FILE_PRINTCONTACTSHEET` | a Contact Sheet kollázs-típus nyomtatási párja |

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
| `timeline` | **157 × 35** | ugrás az idővonalra | **Időrend** |
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
| **`timeline`** | ❌ **nincs — és ez SZÁNDÉKOS** (ld. lent) |
| `rotateleft` · `rotateright` | ✅ (`↺` · `↻`) |
| `prev` · `auto` · `next` | ✅ (`◀` · `slideshowPlayButton` · `▶▶`) |
| `star` | ✅ `slideshowStarButton` |
| `transtype` (`popuplist`) | ✅ `slideshowTransitionBox` |
| `captionbutton` (kétállású) | ✅ `slideshowCaptionModeButton` |
| `dtclip` (`tpslabel` + `minusone` + `tps` + `plusone`) | ✅ `slideshowTimeBlock` |
| **`minusone`/`plusone` `setautorepeat 1`** | ✅ **2026-09-15 óta** (`autoRepeat: true`) |
| a sáv lebegése/elrejtése | ✅ `HoverHandler` + `slideshowHideTimer` |

#### ⛔ Miért NINCS `timeline` gomb — és miért helyes így

A gomb az **Időrend nézetre** ugrik, ami nálunk **nincs megépítve**: a
menütétel is kifejezetten INAKTÍV (`PicasaMenuBar.qml:827`, „amíg a valódi
Időrend nincs megépítve"), a nézet maga a **#24** hatóköre. Egy működő
gomb, ami nem visz sehová, a #936 szabályába ütközne („a kattintható
vezérlő, ami mást ad, mint amit ígér, rosszabb, mint a hiánya").

⇒ A `timeline` gomb a **#24-gyel együtt** kerül be, nem előbb.

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

- A stílus-11 factory-ág a `0x00809fe0` kezelőt és a `0x0080a030` építőt használja; a `len` a szöveg bájthossza. A `d` értéke `desc+0xec` (`transitiontime`); ha nem pozitív, `d=desc+0xe8/3` (`0x8104b9`–`0x8104dc`). A kezdőpont `L=desc+0xf0+desc+0xf4` (`0x810453`–`0x810464`), ahol a parserben `+0xf0=blacktime`, a `+0xf4` mezőnek nincs XML-attribútuma és alapértéke 0 (`0x8162f0`, `0x8152f0`).
- A kockafüggvény képlete a G.6.3/G.6.7 szerint: `n(t)=max(1, trunc(len·clamp((t+0.02−L)/d,0,1)+0.5))`. A lineáris rész szerinti ütem `len/d` bájt/s, tehát a szövegdia teljes `advanceinterval`-je csak akkor határozza meg a karakterütemet, ha `transitiontime` nem pozitív és a `d=advanceinterval/3` visszaesés aktiválódik.
- A képlet a **bájtszámot** bizonyítja, nem azt, hogy a natív rajzoló egy több-bájtos UTF-8 karaktert hány látható karakterként kezel. A glyph-szintű ütem és a kurzor kérdése továbbra is mérendő.

**Gördülő stáblista (`textstyle8`)**

- A kezelő `FadeMove` második idővonala a `desc+0xe8` (`advanceinterval`) hosszát kapja; a start `L=desc+0xf0+desc+0xf4`. `p=clamp((t+0.02−L)/advanceinterval,0,1)`, `S(p)=3p²−2p³` (interpolátor `0x00818cf0`).
- A natív scalar-érték `P(t)=B+S(p)·(A−B)`, tehát az idővonal `B`-ből `A`-ba halad, és a `dia+0x150` mezőbe kerül (`0x809cd0`, `0x809d20`; a style-8 flag beállítása `0x811005`–`0x811009`). `A=0.5·(h_a−(E+0x54−E+0x4c))`, `B=h_b`; ezek a futás közbeni kép- és szövegréteg-geometriából származnak (G.7.5).
- A képlet és az időtartam mezőforrása megvan, de `A`, `B`, a tényleges irány pixel-koordinátán, a `TimelineXML`-értékek élő desc-be jutása és a kocka `t`-je nincs. A mozgás tényleges pixel/s értéke ezért `NINCS MEG`.

**„Jó napom van” (`textstyle1`)**

- A factory 1-es stílusága a `FadeMove` konstruktort (`0x00809c50`, `0x8107a7`) és építőt (`0x00809cd0`, `0x8107ba`) hívja. A kezelő a lineáris alfa- és a smoothstep pozíció-idővonalat is bekapcsolja (`H+0x48=1`, `H+0x49=1`, `0x809cb9`–`0x809cbc`).
- A gyár `AL=0xff` értéket ad át (`0x81079a`); a konstruktor alfa-kezdőértéke 0 (`0x809c68`), végértékét `H+0x0d` tárolja. Az alfa-építő a lineáris `0x00809ae0` interpolátort adja a `0x009e6010` szegmensnek (`0x809eb0`), tehát a kódból olvasható alfaút 0→255.
- A pozícióút a `H+0x28`→`H+0x2c` végpontokat smoothstep-pel interpolálja; a stílus-1 hívásban `H+0x28=0`, a `H+0x2c` végpontot a hívó stackadja adja, forrása nyitott. Az 1-es jelző miatt a `dia+0x14c` mezőt írja (`0x809cd0`, `0x809d20`). A gyár a közös `L=desc+0xf0+desc+0xf4` kezdőértéket adja át (`0x810453`–`0x810464`, `0x8107b2`).
- A stílus-1 ág `0x8107a0` betöltése a factory által korábban kiszámított `d` lokális értéket használja: `d=desc+0xec`, ha pozitív, különben `d=desc+0xe8/3` (`0x8104b9`–`0x8104dc`). Ezt az értéket a factory a `0x809c50` konstruktor első argumentumaként adja át, ahol `H+0x08` mezőbe kerül; az alfaág `0x809af0` hívása is ugyanezt a `d`-t kapja. A `0x809cd0` a bemenő időhöz hozzáadja `H+0x08`-at, ezért a számforrás ismert, de a natív időtengelyen betöltött szerepét nem szabad pusztán „mozgás-időtartamnak” nevezni.
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
- [ ] A 8-as stílus `advanceinterval`-hosszú smoothstep útja `B→A`, a 1-es stílus 0→255 lineáris alfája és egykomponensű smoothstep mozgása kockánként renderelődik. A textstyle1 `d` bemenete binárisan `desc+0xec`, nem pozitív értéknél `desc+0xe8/3`; a `H+0x08` időeltolás tényleges szerepe és a `H+0x2c` geometriai végpont exportkori értéke pontosan feloldandó vagy referenciából mérendő, becslés nélkül.
- [ ] A Picasa 3.9 referenciából mindhárom stílus kockái `k` szerint dokumentálva; a kimeneti teszt kiválasztott kockái a referencia képkockáival összevetve. A tolerancia a mérésből származik, nem előre beállított érték.

##### G.7.8.6 Nyitott — a konkrét megszerzési út

- Ghidra-kör kell: `0x0074e580` — a `CDXSlideshowPin` létrehozásától az export-resetig melyik DirectShow-határ vagy segéd állítja a `+0x108/+0x10c` seedet, és milyen bináris értékkel? [blokkoló]
- Ghidra-kör kell: `0x0074d970` — a resetet megelőző exporthívási útban hol és milyen értékkel írják a két seedmezőt, ha az író nem a pin saját virtuális metódusa? [blokkoló]
- Ghidra-kör kell: `0x00814330` — a `.mxf`/TimelineXML `this+0x50` rekord szülőobjektuma a filmexportban hogyan jut el a `0x812470/0x8127b0` render-`ctx+0x48` listájához? Az objektumazonosságot kell eldönteni. [blokkoló]
- Ghidra-kör kell: `0x00816360` — a TimelineXML `this+0x4c` szülőpointere exportkor ugyanarra a kontextusra mutat-e, amelynek `+0x48` listáját a render-helper olvassa? [blokkoló]
- Ghidra-kör kell: `0x008127b0` — a `ctx+0x48` mintavételezett rekordjának `ctx+0x1a8`-ba másolása mely exportágon történik, és hogyan kapcsolódik az előző XML-parser szülőjéhez? [blokkoló]
- Ghidra-kör kell: `0x00810420` — a `textstyle1` `d` (`desc+0xec`, nem pozitív értéknél `desc+0xe8/3`) pontos időszemantikája, valamint a `0x809c50` hívásban a `H+0x2c`-t adó virtuális geometriai eredmény forrása? [blokkoló]
- Mérés kell: eredeti Picasa 3.9 filmexport mindhárom stílussal, kockánkénti timestamp/pozíció/alfa/karakter-kiolvasással. A helyi `meroadat.tar` releváns film- vagy szövegdia-exportmintát nem tartalmazott; a referenciakockák és a natív ütem ezért `NINCS MEG`.

#### G.7.9 Értékjegyzék a #4615 átadáshoz

| érték vagy állítás | forrás |
|---|---|
| `CDXSlideshowPin` vtable `0x00cb1a08`, render slot `0x0074dfc0`, reset slot `0x0074d970` | bináris (`RTTI 0x00cb1a08`, `0x74dfc0`, `0x74d970`) |
| A pin konstruktor nem írja a `+0x108/+0x10c` seedmezőket | bináris (`0x74e580`, `0x74d1c0`, `0x74d4f5`–`0x74d517`) |
| timestamp átváltó osztó `10 000 000` | bináris (`0x00989680`, operandus `0x74e1ee`) |
| `+0.02` időeltolás | mérés (G.6.2 szintetikus natív ellenőrzés; literál `0x00cf48a8`) |
| `CTransTimeline::UI::vftable = 0x00cbdcec`, `0x80c230` slot = 29 / vcall offset `0x74` | bináris (`RTTI 0xcbdcec`; `0x74e248`–`0x74e251`) |
| render factory desc pointere `ctx+0x1a8` | bináris (`0x8128a2`–`0x8128aa`; `0x813804`–`0x81380c`) |
| TimelineXML `this+0x50` → szülő `+0x48` lista, majd render `ctx+0x48` → `ctx+0x1a8` rekordmásolás | bináris (`0x8152f0`, `0x816360`, `0x80a460`, `0x812470`, `0x8127b0`, `0x612350`); a szülőpointer és render-context azonossága nyitott |
| Írógép natív üteme `len/d` bájt/s; `d=transitiontime`, nem pozitív esetén `advanceinterval/3` | bináris (`0x8104b9`–`0x8104dc`; G.6.3/G.6.7) |
| Gördülő interpoláció `3p²−2p³`, időmező `advanceinterval` | bináris (`0x818cf0`; `0x810fe5`; G.6.4/G.7.5) |
| `textstyle1` alfa `0→255`, lineáris; `d` input `desc+0xec`, nem pozitív értéknél `desc+0xe8/3`; `H+0x08`-ba kerül | bináris (`0x8104b9`–`0x8104dc`, `0x8107a0`–`0x8107b2`, `0x809c50`, `0x809cd0`, `0x809af0`) |
| export seed tényleges értéke, parser-szülő és render-context azonossága, `k↔t` leképezés | NINCS MEG |
| Gördülő tényleges pixeles A/B és textstyle1 `H+0x2c` mozgásvégpont/időszemantika | NINCS MEG |
| referenciafilm képkockái, a három stílus natív mérési táblája, kimeneti képteszt | NINCS MEG |
