# A vágás-eszköz állapota (#448)

**Státusz:** a jegy három fő követelménye **megvalósítva**; egyetlen érdemi
hiányosság maradt (a javaslat-gombok **előnézeti bélyegképe**).

Ez a lap **leltár**, nem terv. A #448 jegy leírása és kommentfolyama
2026-08-07 → 2026-08-13 között több kört futott, és a két utolsó komment még
„hátravan"-ként jelöli a vágás-javaslatokat, miközben azok a kódban **már
készen álltak** — a jegy tehát elavult a valós állapothoz képest. Az alábbi
számok a `feat/448-vagas-eszkoz` ág kódját tükrözik, nem a kommentfolyamot.

## 1. Képarányok — KÉSZ (19 beépített tétel)

`src/picasapy/app/qml/PicasaPy/EditorPanel.qml` `aspectPresets`: **19 tétel**,
mindegyik a bináris **tényleges kulcsnevével** (a jegy 2026-08-07-i javító
kommentje ezt kérte: „a kulcsneveket használjuk, ne a magyarázatokat"):

```
Manual · CurrentRatio · CurrentDisplay · 4x4 · Desktop4x3 · 4x6 · 5x7 ·
8x10 · 8.5x11 · 5x3 · 9x13 · 10x15 · 13x18 · 20x25 · 5x8 · 16x10 ·
HDTV16x9 · Square · FullPage
```

- **11 tétel visel magyarázó alcímet** (`note`), a `Picasa3i18n.dll`-ből:
  Normál képernyő · Kisméretű nyomat (2×) · Nagyméretű nyomat (2×) · Letter
  méretű papír · Szélesvásznú képkocka · Szélesvásznú képernyő · HDTV ·
  CD-borító · Teljes oldal. A legördülő ezeket halványan, a sor jobb szélén
  mutatja (`cropAspectNote<index>`).
- **Két dinamikus tétel** megvan: `CurrentRatio` (`ratio: -1`, a kép aktuális
  aránya) és `CurrentDisplay` (`ratio: -2`, a képernyő aránya).
- A **`lastCropRatio`** perzisztencia megvan: `restoreLastCropRatio()` a
  vágó-eszköz megnyitásakor (`onCropActiveChanged`), a kulcs
  `LAST_CROP_RATIO_SETTING_KEY = "crop/lastRatioKey"`.

### ✅ A `20x25` MARAD — eldőlt (2026-08-16)

A korábbi jelölés szerint *„a `20x25` benne maradt, noha a javított bináris
kulcslistában nem szerepel"*. **Ez téves volt: benne VAN a binárisban.**

| bizonyíték | mit mond |
|---|---|
| `Picasa3.exe`, 9143556. fájloffszet | a `20 x 25` felirat, közvetlenül utána a kulcsa: `AspectRatioList::Crop20x25m` |
| `stringres-en-hu.tsv` | `AspectRatioList::Crop20x25m` → EN `20 x 25` · **HU `20x25`** |
| `ui-audit-editor.md` méretarány-táblája | a valódi Picasa képernyőképén a **7. sor** |

Három, egymástól független forrás. A kulcsban a **kettős kettőspont**
(`AspectRatioList::…`) a Picasa saját elgépelés-osztálya — négy kulcs viseli
(`::A4`, `::A4Page:Description`, `::A4PageCollage`, `::Crop20x25m`,
`::FullPage:Description`), és nem jelent külön névteret.

### ⛔ HELYESBÍTÉS: a lista MÉRTÉKEGYSÉG-VÁLTÓS, nem „hat fölösleges tétel"

A felépítő függvény (**`0x007cc990`**, 8140 b) **két, egymást kizáró ágra**
oszlik:

```asm
0x007cccea  cmp byte ptr [ebp+0x14], 0
            je  0x7cd5a6          ; ← hamis → az ANGOLSZÁSZ ágra ugrik
            … 5x8m · 9x13m · 10x15m · Crop13x18m · Crop20x25m · A4 …
0x007cd5a1  jmp 0x7cdb32          ; ← a metrikus ág ÁTUGORJA az angolszászt
0x007cd5aa  … 4x6 · 5x7 · FullPage (8,5×11) · 8x10 …
```

| `[+0x14]` | a nyomatméretek |
|---|---|
| **igaz — metrikus** | `5x8` · `9x13` · `10x15` · `13x18` · **`20x25`** · `A4` |
| **hamis — angolszász** | `4x6` · `5x7` · `8,5x11` · `8x10` |

**A felhasználó képernyőképe a metrikus ágat mutatja.** A `4x6`, `5x7`,
`8x10`, `8,5x11` tehát **nem fölösleges** — az angolszász ág tagjai, és a
területi beállításhoz kell kötni őket. Részletek: **#876**.

*(A `4x4` viszont tényleg nem tétel: a felépítő csak a `Desktop4x3`
leírás-kulcsaként használja, `0x007cde49`.)*

### A teljes felépítési sorrend

Két kapcsoló vezérli: `[+0x28]` = **„Kézi" kell**, `[+0x14]` = **metrikus**.

```
1.  Kézi                     ha [+0x28]                       (0x007cc9da)
2.  Jelenlegi megjelenítés   ha van érvényes képernyő-téglalap (0x007ccb7b)
3.  metrikus VAGY angolszász nyomatméretek
4.  A4 paper + A4            ha MINDKÉT kapcsoló hamis        (0x007cdb73)
                             — 297 × 210 mm beégetve (push 0x129 / 0xd2)
5.  Négyzet · 4:3 · 16:10 · 16:9 · 5:3
6.  Egyéni méretarányok + Egyéni méretarány hozzáadása…
```

### ✅ És ezzel megvan a KOLLÁZS Oldalformátum-listája is

A 4. lépés feltétele (**mindkét kapcsoló hamis**) pontosan a kollázs esete:

```
Jelenlegi megjelenítés · A4-es méretű papír · A4 · Négyzet: CD-borító ·
4:3: Normál képernyő · 16:10: Szélesvásznú képernyő · 16:9: HDTV ·
5:3: Szélesvásznú képkocka · Egyéni méretarányok ·
Egyéni méretarány hozzáadása…
```

**Nincs benne „Kézi", és nincs benne egyetlen nyomatméret sem.** Ez
lezárja a lap korábbi nyitott kérdését — képernyőkép nélkül.

### ⚠️ A lista tételszáma (#876)

A `aspectPresets` 19 tétele közül a valódi Picasa vágó-legördülőjében
**13** van (`ui-audit-editor.md` képernyőképe: Kézi + Jelenlegi méretarány +
11 fix arány + a két egyéni sor). Részletek és a teljes hivatalos
kulcs↔felirat tábla: **#876**.

## 2. Egyéni képarányok — KÉSZ

- `src/picasapy/app/custom_aspect_ratios.py` (**115 sor**) — tiszta réteg:
  `parse_custom_aspect_ratios` · `serialize_custom_aspect_ratios` ·
  `add_custom_aspect_ratio` · `delete_custom_aspect_ratio`. Sérült
  beállítás-fájl nem omlaszt: üres listát ad.
- `src/picasapy/app/custom_aspect_ratios_controller.py` (**89 sor**) — a
  QSettings-I/O, egyetlen JSON-kulcs alatt (`crop/customAspectRatios`).
- A felületen: `AddCustomAspectRatio` sor a beépítettek alatt
  (`cropAspectAddRow`), és **törlés** „✕"-szel, megerősítéssel, **csak az
  egyéni** tételeken (`cropAspectDelete<index>`, `isCustom === true`).
- A lista alakja a jegy szerinti: `"<szél> x <mag>   <név>"`.
- Teszt: `tests/app/test_custom_aspect_ratios.py` (115 sor) +
  `tests/app/test_custom_aspect_ratios_controller.py` (140 sor).

## 3. A HÁROM automatikus vágás-javaslat — KÉSZ (a bélyegkép kivételével)

`src/picasapy/render/crop_suggest.py` (**303 sor**) — **öt stratégia**, a
binárisban nevesített mind az öt:

| függvény | bináris felirat |
|---|---|
| `close_crop_to_faces` | „Close crop to faces" |
| `compose_around_faces` | „Compose picture around faces" |
| `crop_by_horizon` | „Crop by horizon line" |
| `crop_by_red_green` | „Crop by Red/Green" |
| `crop_by_variance` | „Crop by variance" |

A `suggest_crops` **pontosan hármat** ad (`SUGGESTION_COUNT = 3`), és a
választás determinisztikus: **arccal** szoros arc-vágás → kompozíció az arcok
köré → variancia; **arc nélkül** variancia → horizont → szín-dominancia.

A bekötés végig megvan:

```
crop_suggest.suggest_crops
  → edit_controller.cropSuggestions   ({key,x,y,w,h}, mentett arcokkal)
  → EditorPanel.cropSuggestions + cropSuggestionLabel(key)
  → EditorCropPanel három gombja      (cropSuggestion0..2)
  → PhotoViewer.onCropSuggestionChosen → cropOverlay.loadSelection
```

Az `editController.setCropAspect` a kiválasztott arányt átadja, tehát a
javaslatok a **választott képarányban** születnek.

### A HIÁNYZÓ darab: előnézeti bélyegkép a javaslat-gombokon

A jegy bináris bizonyítéka **három javaslat-gombot ÉS három előnézetet** ad:

```
editpanel/cropsug1   editpanel/cropsug2   editpanel/cropsug3
editpanel/cropsug_preview%d
```

> „Három javaslat-gomb, **mindegyikhez saját előnézeti kép**
> (`cropsug_preview1..3`)."

A mai három gomb **csak feliratot** visel (`PanelButton { label: … }`, a
`thumbSource` üresen marad), tehát a felhasználó a kattintás előtt **nem
látja, mit kap**. Ez a #448 utolsó érdemi hiánya.

A megvalósításhoz minden alkatrész adott:

- a `PanelButton` **már tud bélyegképet** (`thumbSource`, #338);
- van képszolgáltató-precedens ugyanerre a célra:
  `src/picasapy/app/effect_thumbnails.py` (`image://effectthumb/<id>/<effekt>`).

## 4. Lezárt nyitott kérdés: harmadolóvonal

A jegy 2026-08-13-i kommentje a teljes bináris-indexben **egyetlen találatot
sem** talált „thirds"/„gridline"/„guides"-ra, és a vágó-panel vezérlői közt
sincs ilyen kapcsoló: **az eredetiben nem volt harmadoló segédrács.** A
kódban sincs (`grep -i thirds|harmadol` a QML-en: 0 találat). Ha egyszer
kap ilyet a PicasaPy, az **saját kiegészítés**, nem az eredeti utánzása.

## 4/b. Lezárt nyitott kérdés: mit tesz az „Alaphelyzet"? (#1528)

*Forrás: `editpanel.tre:830` (`editpanel/cropdiscard`).*

A #1528 nyitó kérdése az volt, hogy az eredeti „Alaphelyzet" a MENTETT
vágást szünteti-e meg, vagy csak a húzott kijelölést. **A választ az
eredeti saját szövegforrása adja, nem következtetés:**

| forrás | sor | szöveg |
|---|---|---|
| `referencia/tre-eroforrasok/editpaneltext.tre` | 231–235 | `Label editpanel/cropdiscard` → **Reset**; `Tooltip editpanel/cropdiscard` → **„Discards any applied cropping"** |
| `referencia/panel-feliratok-hu.tsv` | 4981–4982 | **„Alaphelyzet"** / **„Az összes alkalmazott vágás elvetése"** |

Az „applied" / „alkalmazott" szó zárja a kérdést: a gomb a **ténylegesen
alkalmazott** vágást veti el, nem a félkész kijelölést. Ezt erősíti a
testvér-vezérlő is: a `redeyediscard` buboréksúgója „Undo Red-Eye changes"
(`ui-audit-editor.md` 975), tehát ott is a már elvégzett korrekciót veszi
le.

**A PicasaPy ehhez igazodik (#1528):** az `onCropResetRequested`
(`app/qml/PicasaPy/PhotoViewer.qml`) a kijelölés nullázása MELLETT az
`editController.clearCrop()`-ot is hívja, ha van mentett vágás; a gomb
pedig tiltott, ha nincs mit elvetni (`cropResetEnabled` — kijelölés VAGY
`hasCrop`). Az elvetés a szokásos visszavonás-veremre kerül `crop` néven,
tehát a Visszavonás gomb visszahozza (#465).
## 4/c. Lezárt nyitott kérdés: az Alkalmaz HALMOZ, nem von össze (#1553)

A #1550 mérése közben derült ki, hogy a vágó-eszköz **Alkalmaz** gombja
összevonta a szerkesztési láncot egyetlen `crop64`-re, tehát egy
Picasa-eredetű, több-vágásos képnél (a korpuszban **38** ilyen) az **első
Alkalmaz eldobta a korábbi vágás-rétegeket**. Mérve, a valódi gombra
kattintva: `crop64=1,0000000080008000;bw=1;crop64=1,c0008000ffffffff;` +
Alkalmaz → `crop64=1,40004000c000c000;bw=1;`.

**Az eredeti halmoz** — a bizonyítás (a `filters=` mint visszavonás-verem a
binárisban, a `Recrop`/„Vágás megismétlése" felirat, és a Picasa saját
`redo=` sora két `crop64`-gyel) teljes terjedelmében:
`filters-decoded.md` → „Az ÍRÁS oldala: az újravágás HALMOZ (#1553)".

A PicasaPy ehhez igazodik: az `EditSession.append_crop()` a lánc végére fűz,
a Visszavonás rétegenként bont vissza (az újravágás visszavonása a KORÁBBI
vágást hozza vissza), a `crop=` tükörkulcs pedig továbbra is az utolsót
tükrözi. Őr: `tests/app/qml_functional/test_vagas_halmozas_1553.py`.

## 5. Amit az eredetiből átvettünk, és megvan

- **Kiegyenesítés-figyelmeztetés** (`IDS_WARN_CROP_ACCURACY`) — szó szerinti
  szöveggel, `cropStraightenWarning`, csak aktív kiegyenesítésnél.
- **Gombkészlet:** Forgatás · Előnézet (nyomva tartva) · Alaphelyzet
  (egyedül, középen — #741) · Alkalmaz · Mégse.
- **Súgószöveg** a panel tetején.
- A #741 mért geometria (98 × 28 gombok, 21 px legördülők) és a #779
  betűfüggetlen, felső-korlátos elrendezés.
