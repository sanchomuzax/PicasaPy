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

**Nyitott, de nem fejlesztői döntés:** a `20x25` benne maradt, noha a javított
bináris kulcslistában nem szerepel. A megtartásáról/törléséről a jegy
2026-08-10 óta a felhasználó döntésére vár.

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

## 5. Amit az eredetiből átvettünk, és megvan

- **Kiegyenesítés-figyelmeztetés** (`IDS_WARN_CROP_ACCURACY`) — szó szerinti
  szöveggel, `cropStraightenWarning`, csak aktív kiegyenesítésnél.
- **Gombkészlet:** Forgatás · Előnézet (nyomva tartva) · Alaphelyzet
  (egyedül, középen — #741) · Alkalmaz · Mégse.
- **Súgószöveg** a panel tetején.
- A #741 mért geometria (98 × 28 gombok, 21 px legördülők) és a #779
  betűfüggetlen, felső-korlátos elrendezés.
