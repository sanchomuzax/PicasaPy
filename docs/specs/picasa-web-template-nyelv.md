# A Picasa web-export sablonnyelve — teljes specifikáció

Forrás: a telepítés saját dokumentációja (`web/documentation/index.html`), a
`web/templates/TemplateNotes.txt`, és **mind a hét beépített sablon tényleges
használata** (`blackbg`, `blackfrm`, `greybg`, `greyfrm`, `whitebg`, `whitefrm`,
`xml`). Feldolgozva: 2026-08-07.

A hivatalos doksi több ponton **hiányos** — az alábbi lista a sablonok
átvizsgálásával egészül ki; ahol a forrás eltér, ott jelezve van.

## 1. Parancsok (a `.tpl` fájlban, soronként)

| parancs | paraméterek | mit csinál |
|---|---|---|
| `#templatefile -v "1.0" -n "Név" -d "Leírás"` | — | **kötelező fejléc** minden `.tpl` tetején; ez jelenik meg az export-varázslóban |
| `define` | `név érték` | belső változó; a `<%név%>` mindenhol kicserélődik. Ütközésnél **az utolsó nyer** |
| `include` | `fájlnév` | fájl beszúrása; ha a fájl `#templatefile`-lal kezdődik, teljes al-sablonként fut le |
| `loop` | `képenkénti_fájl` | a fájlt **minden képre** lefuttatja |
| `targetloop` | `tpl_fájl` `include_fájl` | a `tpl_fájl`-t **külön exportált oldalként** futtatja minden képre (sorszámozva), majd az `include_fájl`-t szúrja a hívó oldalba, `<%targetPath%>`-szal a generált oldalra mutatva |
| `copy` | `forrás\` [`cél\`] | könyvtár rekurzív másolása az exportba (a záró `\` kötelező) |
| `#` | — | megjegyzés |

A `loop`/`targetloop` oszlop-paraméterei (`columnCount`, `rowStartInclude`,
`rowEndInclude`) a hivatalos doksiban is **`notImplemented`** jelzésűek, és a hét
sablon egyikében sincsenek használva.

## 2. Változók

**Album-szintű (mindig érvényes):** `albumNumber` · `albumName` · `albumCaption`
· `albumDate` · `albumItemCount` · `exportDescription` *(a hivatalos doksiban
nem szerepel, de a sablonok használják)*

**Kép-hurokban:** `itemNumber` · `itemName` · **`itemNameOnly`** · `itemOriginalPath`
· `itemWidth` · `itemHeight` · `itemSize` · **`itemCaption`** · `itemThumbnailImage`
· **`itemThumbnailWidth`/`Height`** · `itemLargeImage` · `nextImage`/`prevImage` ·
`nextThumbnail`/`prevThumbnail` · **`firstImage`/`lastImage`/`lastThumbnail`**

A **félkövérrel** jelöltek a hivatalos dokumentációban **nem szerepelnek** — csak
az `xml` sablonból derülnek ki.

**Cél-oldalon (`targetloop` által generált fájlban):** `referrer` ·
`nextTarget`/`prevTarget`/`firstTarget`/`lastTarget` · `outputIndex`

**Beállítható `define`-változók:** `exportFileName` · `imageWidth`/`imageHeight`
(0 = eredeti méret) · `thumbnailWidth`/`thumbnailHeight` · `bgColor` ·
`shadowedThumbnails` · `shadowedImages`. Dokumentálatlan, de használt:
`fgColor`, `noImageExport` *(jelentése nyitott)*.

## 3. Feltételek

```
<%if isNextImage%> … <%endif%>
<%if !isNextImage%> … <%endif%>     ← a ! a tagadás
```

**Nincs `else`** — a gyakorlatban két, egymást követő blokkal oldják meg.
Egymásba ágyazható, és a nyitó/záró HTML-tag külön feltételbe is tehető.

Feltétel-nevek: `isNextImage` · `isPrevImage` · `isFirstImage` · `isLastImage` ·
`isNextTarget` · `isPrevTarget` · `isFirstTarget` · `isLastTarget`, valamint a
videóhoz: **`isImage` · `isSimpleEmbed` · `isExtendedEmbed`** (ld. 6.).

## 4. Kimeneti fájlnevek

Az `exportFileName` `define` adja. `targetloop`-nál az alapnév **sorszámot kap**
a kiterjesztés elé: `index0.html`, `index1.html`, … A hét sablon mintája:
főoldal `index.html` (vagy `index.xml`), célkép-oldal `target.html`, a keretes
(`*frm`) változatokban `index.html` + `thumbnails.html` + `caption.html` +
`imageset.html`, al-sablononként külön `exportFileName`-mel.

## 5. Képek előállítása

A bélyegkép a `thumbnail/`, a nagy kép az `image/` alkönyvtárba kerül; méretüket
a `thumbnailWidth/Height` és `imageWidth/Height` szabja meg (**0 = eredeti**).
A `bgColor`, `shadowedThumbnails`, `shadowedImages` a keret/árnyék megjelenést
vezérli. Mind felülírható a sablonból.

## 6. Videó-támogatás — a doksiban NEM szerepel

Három feltétel kezeli: **`isImage`** (állókép) · **`isSimpleEmbed`**
(`<embed>`, QuickTime-jellegű) · **`isExtendedEmbed`** (ActiveX Windows Media
Player `<OBJECT>`). Mind a hét sablon tartalmazza.

Mai újraírásnál ez egyetlen `<video>` elemre cserélhető — de a **három ág
létezését** ismerni kell, mert a régi sablonok ezekre épülnek.

## 7. Amit a nyelv NEM tud

- **Nincs `else`**, nincs ciklusváltozó-aritmetika.
- **Nincs lapozás / több oldalra bontás** — a keretes sablonok ezt
  `targetloop` + HTML-frame trükkel oldják meg, nem valódi lapozással.
- Az egyéni CSS nem nyelvi elem: a `copy` paranccsal átmásolt `style.css` és egy
  `<link>` a fejlécben — puszta konvenció.

## 8. Az `xml` sablon

Nem vizuális: **nyers XML-kimenet további feldolgozásra** (a saját leírása:
*„Raw XML-formatted text for further translation."*). Album- és képadatokat
csomagol XML-elemekbe.

**Ez nekünk külön hasznos:** ha a PicasaPy előbb ezt az XML-t állítja elő, és a
HTML-t abból generálja, akkor egyszerre kapunk (a) Picasa-kompatibilis
sablontámogatást és (b) egy tiszta, saját adatmodellt a modern kimenetekhez.
