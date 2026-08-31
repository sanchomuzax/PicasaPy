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
- A kimeneti mappa mellé **`.picasa.ini` készül** `[encoding] utf8=1` és
  `[Picasa] name=…` szekciókkal (az `.exe`-ben közvetlenül az `autosave.cxf`
  után állnak ezek a format-sztringek) — vagyis a projekt-albumok is a
  normál ini-modellt használják.

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
| `contactsheet` | **Ghidra-C (2026-08-30): NEM a layout állítja** — a `0x00888210` a node `+0x2c`-be `1,0`-t ad; a `313` a vetítés/render-scale adja | AI6 | tovább kutatva (#1412, nyitva) |

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
   ráhagyásával csökkentett cella (311) nem adja ki. **Ghidra-C (2026-08-30,
   #1412):** a `0x00888210` layout a node `+0x2c`-be `1,0`-t tesz, a
   `0x00887e50` csomópont-allokátor (nem `k`-képző) — tehát a `313`-at a
   **vetítés/render-scale** írja, a `scale_for_theme`-unk contactsheet-ágát a
   vetítés-scale-képlettel kell összekötni (#1412 nyitva).
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

### 1.10 A kollázs-panel TELJES felülete — 156 elem (2026-08-16)

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

A `kenburnsaoi` külön említést érdemel: a Picasa az **arcfelismerés
eredményét** használta a Ken Burns-mozgás célpontjául.

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

### 2.3 Szöveges dia — 11 stílus

`CMakeMoviePanel::textstyleN`: Caption – Classic · Gradient – Black ·
Gradient – White · Transparent – Black · Transparent – White ·
**Scrolling Credits** · Music Video – Left · Music Video – Right ·
Caption – Typewriter (+ további kettő). Betűbeállítás: család, méret,
`Bold`, `Italic`, és **„Automatic Outline (like movie subtitles)"**.

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

### 2.7 A film-előnézet vezérlősávja (`video_control_bar2`) — MŰKÖDÉS

*A 2.2/2.6 a felső panel beállításait, ez a szakasz a film-előnézet ALUL
lévő `video_control_bar2` vezérlősávját (a #1154 „nem feltárt" pontját).
A `.tre`-t és a kezelőket összevetve:*

#### A felület (`video_control_bar2.tre`)

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

## 2/b. A diavetítés vezérlősávja — teljes leltár a binárisból (#433, 2026-08-15)

Forrás: `oneup.tre`, `oneuptext.tre`, `slideshowctrls.tre`, és a `respack.yt`
rétegtéglalapjai (a módszer és a csapdája:
[`binaris-regeszet-modszertan.md`](binaris-regeszet-modszertan.md) 14/c —
a **méretek** authoroltak, az abszolút pozíciókat a `.tre` felülírhatja).

### A sáv maga

```
oneup/stripback: root
YConstraint 1, 1, -20      # az ablak aljától 20 képponttal feljebb
m_centerX                  # vízszintesen középre
```

Mérete a csomagban **797 × 50** képpont; a fölötte lebegő felirat
(`oneup/caption`) **550 × 10**, `YConstraint 1, 1, -100`.

### A tíz vezérlő, balról jobbra

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
