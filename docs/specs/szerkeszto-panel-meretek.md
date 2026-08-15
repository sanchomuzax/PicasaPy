# A szerkesztő bal panelje — KÖTELEZŐ méretspecifikáció

**Ez a lap normatív.** A szerkesztő bal panelje **pontosan** így nézzen ki.
A tulajdonos döntése (`../decisions/szerkeszto-bal-panel.md`):

> A felület PONTOSAN úgy nézzen ki, mint az eredeti Picasa.
> **Egyetlen kivétel:** hét fül az eredeti öt helyett.

Aki ehhez a panelhez nyúl, ezt a lapot pipálja végig. Ahol a mai kódunk mást
mond, **a kód a rossz**.

## 0. Forrás és módszer

Minden szám a `respack.yt` **rétegtéglalapjaiból** való (`int16 x0, y0, x1, y1`
a 13 bájtos rekordfejlécben — [`picasa-respack-format.md`](picasa-respack-format.md)
3. szakasz, a módszer [`binaris-regeszet-modszertan.md`](binaris-regeszet-modszertan.md)
14/c). A kötéseket az `editpanel.tre` adja. **Nem képernyőkép-mérés.**

```python
import sys; sys.path.insert(0, "tools/picasa"); import respack
adat = open("research/copy_Picasa_3_7/Picasa3/runtime/respack.yt", "rb").read()
for e in respack.read_index(adat):
    if not e.is_tre and e.name.startswith("layer:editpanel/"):
        r = respack.decode_layer(adat, e)     # r.x0, r.y0, r.x1, r.y1
```

**201 elem** a bal panelen (`x0 ≤ 285`), plusz **55** a szöveg-eszköz saját
paneljén (`edittextpanel`).

### Mi kötelező és mi tájékoztató

| | státusz |
|---|---|
| **méretek** (szélesség × magasság) | **KÖTELEZŐ** |
| **osztásközök, hézagok, egymáshoz képesti eltolás** | **KÖTELEZŐ** |
| abszolút `y` a panel tetejétől | tájékoztató — a tervezővászon értéke |

Az `x` a panelen belül kötelező (a `.tre` `MaintainOffset`-tel őrzi), az
abszolút `y`-t viszont a futásidő eltolhatja. **Keresztellenőrzés:** az
effekt-rács mérete és osztásköze a csomagban `88 × 71`, a képernyőképes
mérésben ([`ui-audit-editor.md`](ui-audit-editor.md) 3.2) szintén `88 × 71` —
a két független forrás a **méretekre betűre egyezik**, az abszolút tetőre
nem. Ezért a fenti szétválasztás.

---

## 1. A panel váza

| elem | méret | pozíció |
|---|---:|---|
| **tartalom-oszlop** (`editcontrols`, `edittabbase`, `fxthumbs`) | **276 × 351** | x 3..279 |
| `editcontrol_well` (a beágyazott eszközök kerete) | **266 × 276** | x 8..274 |
| **fülsáv** (`tabs`) | **276 × 25** | x 3..279, a panel tetején |
| `filter_name` (az aktív szűrő neve) | **140 × 16** | x 14 |
| **`filter_undo`** (Visszavonás) | **132 × 28** | x **7..139** |
| **`filter_redo`** (Újra) | **132 × 28** | x **144..276** |
| `albumview` („Vissza a könyvtárhoz") | **122 × 22** | x 10..132, y 9..31 |
| `toggle_left_drawer` (panel be/ki) | 15 × 16 | x 1..16 |

**A panel teljes szélessége 280 képpont** — a képnézet `x = 280`-nál kezdődik
(`insetleft`), és a `LEFTDRAWEROFFSET` alapértéke **279**. A mai
`EditorPanel.qml` `implicitWidth: 280` **helyes, ezen ne változtass.**

### A Visszavonás/Újra sor

- a két gomb **azonos szélességű (132)**, közöttük **5 px** hézag
  (139 → 144), és együtt **kitöltik a 276 px-es oszlopot** (7 + 132 + 5 +
  132 = 276);
- **a panel ALJÁHOZ van kötve**, nem a tartalom után úszik: a
  tartalom-oszlop alja 391, a gombsor 361..389 — vagyis **2 px** margóval a
  panel aljára ül;
- magassága **28 px**.

> ⚠️ A mai `EditTabButton.qml` `width: Math.max(120, implicitWidth)` szabálya
> **nem** ezt adja. Fix 132, 5 px hézaggal.

### A fülsáv magassága 25 px

A fülgombok `y 45..70`, az ikonjaik `y 49..68` — vagyis a **25 px-es** sávban
**16–19 px magas** ikonok ülnek, függőlegesen középre. A mai
`EditTabButton.qml` 22 × 22-es ikonja **túl nagy**.

| fül | ikon mérete |
|---|---|
| `tab1` (`basic_icon`) | 15 × 16 |
| `tab2` (`tuning_icon`) | 17 × 18 |
| `tab3` | 20 × 19 |
| `tab4` | 25 × 19 |
| `tab5` | 25 × 19 |

---

## 2. ⚠️ A KIVÉTEL: hét fül öt helyett

Az eredeti öt fül **hézag nélkül, pontosan kitölti** a 276 px-es oszlopot:

| fül | x | szélesség |
|---|---|---:|
| `tab1` | 3..58 | 55 |
| `tab2` | 58..113 | 55 |
| `tab3` | 113..169 | **56** |
| `tab4` | 169..224 | 55 |
| `tab5` | 224..279 | 55 |

**5 × 55 + 1 = 276.** A minta: egyenlő szélesség, és a maradék egyetlen fülre
kerül.

**Hét fülre ugyanez a szabály:** `276 / 7 = 39,43`, tehát **39 px** az alap,
és a maradék `276 − 7 × 39 = 3` képpont három fülre oszlik:

```
39 · 39 · 40 · 39 · 40 · 39 · 40   =  276
```

**A fülsáv magassága ettől NEM változik: marad 25 px**, és a fülek továbbra is
hézag nélkül, pontosan kitöltik a 276 px-et. Az ikonok a keskenyebb fülben is
középre kerülnek.

---

## 3. 1. fül — „Gyakori javítások" (`tabpanel1`)

A fül lapja **273 × 277** (x 3..276).

### A nyolc eszközcsempe

**Minden csempe 44 × 30 képpont.**

| | 1. oszlop **x 37** | 2. oszlop **x 118** | 3. oszlop **x 198** |
|---|---|---|---|
| **1. sor** (y 91) | `crop` Vágás | `horizonadjust` Kiegyenesítés | `redeye` Vörösszem |
| **2. sor** (y 155) | `enhance` Jó napom van | `autolighting` Auto. kontraszt | `autocolor` Auto. szín |
| **3. sor** (y 223) | `retouch` Retusálás | `edittext` Szöveg | `picnik` Kreatív Kit |

- **oszlopköz: 81 px** (37 → 118 → 198)
- **sorköz: 64 px** az 1.→2. sor közt, **68 px** a 2.→3. közt
- a felirat **külön elem, a csempe ALATT**, középre zárva
  (`m_buttonfontCbelow` → `YConstraint 0, 1, 0`)

> ⚠️ A mai `ToolTile.qml` `Layout.preferredHeight: 94` és az
> `EditorTabCommonFixes.qml` `rowSpacing: 10` együtt **104 px** sorközt ad a
> **64** helyett. Ez a bal sáv szétesésének fő oka (#741).
> **Cél: 64 px-es sorköz, 44 × 30-as csempekép.**

### A Derítőfény-sor

| elem | méret | x |
|---|---:|---|
| `filllight_icon` (a kis kép) | **44 × 30** | **37..81** — a csempe-rács 1. oszlopával AZONOS x |
| `filllightlabel` (felirat) | **141 × 14** | 94..235 |
| `backlight_container` (csúszka) | **127 × 27** | 101..228 |

A felirat `y 283..297`, a csúszka `y 294..321` — a **felirat a csúszka
FÖLÖTT**, enyhén rálógva. A kis kép ugyanakkora, mint egy eszközcsempe.

---

## 4. 2. fül — „Finomhangolás" (`tabpanel2`)

A fül lapja **273 × 316**.

### A négy csúszka

| elem | méret | x | y |
|---|---:|---|---|
| `editslider1_container` | **191 × 27** | 30..221 | 111 |
| `editslider2_container` | 191 × 27 | 30..221 | 164 |
| `editslider3_container` | 191 × 27 | 30..221 | 218 |
| `editslider4_container` | 191 × 27 | 30..221 | 270 |

**A csúszkák osztásköze 53 · 54 · 52 px** — gyakorlatilag egyenletes ~53.

### A feliratok és a jelölők

| elem | méret | x |
|---|---:|---|
| `editlabel1..4` (a csúszkák feliratai) | **151 × 12** | 50..201 |
| `editcheckbox1` · `editcheckbox2` | **14 × 14** | 38..52 |
| `editlabel5` · `editlabel6` (a jelölők feliratai) | 151 × 12 | 52..203 |
| `greybalancelabel` | **219 × 14** | 25..244 |

A felirat mindig **a csúszka fölött 17 px-rel** ül (94 → 111, 147 → 164,
201 → 218, 253 → 270).

### A színkorongok és a pipetta

| elem | méret | x | y |
|---|---:|---|---|
| `colorwheel0` · `colorwheel1` | **62 × 50** | 94..156 | 94..144 |
| `colorwheel_label0/1` | 151 × 12 | 50..201 | 96 / 80 |
| `slidercircle0` · `slidercircle1` | **19 × 19** | 61 / 81 | 122..141 |
| `droppertoggle` (pipetta) | **29 × 24** | 138..167 | 324..348 |
| `editcircle1` | 21 × 22 | 111..132 | 325..347 |
| `magic_lighting` | **26 × 24** | 245..271 | 165..189 |
| `magic_color` | 26 × 24 | 245..271 | 325..349 |

A két „varázspálca" gomb (`magic_lighting`, `magic_color`) a panel **jobb
széléhez** tapad, a hozzájuk tartozó csúszka magasságában.

---

## 5. 3–5. fül — az effekt-rács (`fxthumbs`)

**Tizenkét hely, 3 × 4 elrendezésben.** Ez a rács ma **már helyes**
(a #704 a mért értékekre állította) — a számok itt a teljesség kedvéért
állnak.

| elem | méret | x | y |
|---|---:|---|---|
| `fx1..fx12` (a csempe kattintható rectje) | **88 × 71** | 8 / 96 / 184 | 102 / 173 / 244 / 315 |
| `fxpreview1..12` (a bélyegkép) | **78 × 48** | +5 a csempétől | +5 a csempétől |
| `fxlabel1..12` (felirat) | **86 × 14** | 9 / 97 / 185 | a csempe alja − 15 |
| `fx1_adorn..fx12_adorn` (alkalmazva-jelvény) | **13 × 12** | a csempe jobb alsó sarka | |

- **oszlopköz 88 px**, **sorköz 71 px**
- a **látható** csempe 86 px széles (a 88-ból 2 px a hézag)
- a jelvény a csempe **jobb alsó sarkában** ül

---

## 6. Az eszköz-panelek (a fül helyére nyílnak)

Mindegyik a `editcontrol_well`-be (266 × 276) épül.

### 6.1 Vágás (`crop_well`, 276 × 312)

| elem | méret | x | y |
|---|---:|---|---|
| `crop_icon2` (a panel ikonja) | 44 × 30 | 14..58 | 81 |
| `crop_label` | 208 × 16 | 62..270 | 82 |
| `croptext` (magyarázó szöveg) | 257 × 54 | 14..271 | 115 |
| **`crop_aspect_menu`** (képarány-legördülő) | **249 × 21** | 9..258 | 172 |
| `crop_delete_custom` | 14 × 14 | 261..275 | 175 |
| **`cropsug1..3`** (a három vágás-javaslat) | **80 × 50** | **10 / 102 / 190** | 203 |
| `cropsug_preview1..3` | 77 × 47 | +1 a gombtól | |
| `croprotatecrop` · `croppreview` | **98 × 28** | 38 / 142 | 282 |
| `cropdiscard` | 98 × 28 | 90..188 | 316 |
| **`cropapply` · `cropcancel`** | **98 × 28** | **38 / 142** | 351 |

A három vágás-javaslat **osztásköze 92 · 88 px**, a gombok 80 px szélesek.

### 6.2 Vörösszem (`redeye_well`, 276 × 288)

| elem | méret | x | y |
|---|---:|---|---|
| `redeye_icon2` | 44 × 29 | 14..58 | 81 |
| `redeye_label` | 88 × 16 | 62..150 | 82 |
| `redeyetext` (állapotüzenet) | **242 × 129** | 18..260 | 115 |
| `redeyeauto` · `redeyepreview` | **98 × 29** | **38 / 144** | 280 |
| `redeyediscard` | 98 × 28 | **91..189** (középen) | 314 |
| `redeyeapply` · `redeyecancel` | **98 × 29** | 38 / 144 | 348 |

**A `Reset` gomb középre van igazítva** (x 91), a többi négy párban áll.

### 6.3 Retusálás (`retouch_well`, 276 × 288)

| elem | méret | x | y |
|---|---:|---|---|
| `retouch_label` | 256 × 16 | 14..270 | 80 |
| `retouchtext` | 258 × 96 | 12..270 | 101 |
| `retouch_brush_label` | 243 × 16 | 18..261 | 211 |
| `brushslider_container` (ecsetméret) | **127 × 27** | 74..201 | 227 |
| `retouchreset` | **118 × 28** | 80..198 | 257 |
| `retouchundo` · `retouchredo` | **118 × 28** | **18 / 143** | 293 |
| `retouchapply` · `retouchcancel` | **118 × 29** | 18 / 144 | 339 |
| `eraserbutton` | 14 × 14 | 1..15 | 93 |

A retusálás gombjai **118 px** szélesek (nem 98!), 25 px hézaggal.

### 6.4 Szöveg (`edittextpanel`, 276 × 321)

| elem | méret | x | y |
|---|---:|---|---|
| `text_icon` | 54 × 36 | 5..59 | 8 |
| `edittext_label` | 207 × 16 | 59..266 | 15 |
| `font_label` · `size_label` | 66 × 15 | 0..66 | 57 / 87 |
| **`fontfamily`** (betűtípus-legördülő) | **202 × 21** | 70..272 | 55 |
| **`sizelist`** (méret-legördülő) | **48 × 21** | 70..118 | 85 |
| `style_label` | 46 × 15 | 121..167 | 86 |
| **`bold` · `italic` · `underline`** | **27 × 27** | **172 / 202 / 232** | 81 |
| `outline` | 29 × 23 | 258..287 | 83 |
| `align_label` | 94 × 15 | 72..166 | 117 |
| **`leftalign` · `centeralign` · `rightalign`** | **27 × 27** | **172 / 202 / 232** | 112 |
| `separatorA` · `separatorB` | **250 × 2** | 13..263 | 145 / 193 |
| `colorcircle` · `bgcolorcircle` | 19 × 19 | 31 / 115 | 159 |
| `colorpicker_bevel` · `bgcolorpicker_bevel` | 21 × 21 | 30 / 114 | 158 |
| `no_fill` | 29 × 22 | 55..84 | 158 |
| `outlineweightslider_container` | **127 × 27** | 137..264 | 158 |
| `transparency_label` | 127 × 15 | 79..206 | 202 |
| `textopacityslider_container` | **127 × 27** | 79..206 | 217 |
| `usecaption` · `clearall` | **98 × 29** | 38 / 141 | 250 |
| `edittextapply` · `edittextcancel` | **98 × 29** | 38 / 141 | 284 |

A stílus- és igazítás-gombok **azonos rácson** ülnek: 27 × 27, x = 172 / 202 /
232, tehát **30 px osztásköz**.

---

## 7. Visszatérő méretek — ezeket tartsd egységesen

| minta | méret | hol |
|---|---:|---|
| „párban álló" művelet-gomb | **98 × 28–29** | crop, redeye, szöveg apply/cancel |
| széles művelet-gomb | **118 × 28–29** | retusálás |
| a panel teljes szélességű gombja | **132 × 28** | Visszavonás / Újra |
| csúszka-konténer | **127 × 27** vagy **191 × 27** | ecsetméret / derítőfény, ill. finomhangolás |
| legördülő (`popuplist`) | magasság **21** | képarány, betűtípus, méret |
| jelölőnégyzet | **14 × 14** | finomhangolás, szöveg |
| eszközcsempe (1. fül) | **44 × 30** | |
| effekt-csempe (3–5. fül) | **88 × 71** (látható 86) | |

---

## 8. Megvalósítási ellenőrzőlista

Ezt kell végigpipálni — mindegyik állítás **mérhető**:

- [ ] a panel szélessége **280**, a tartalom-oszlop **276**
- [ ] a fülsáv **25 px** magas, a hét fül **39/39/40/39/40/39/40** szélességgel,
      hézag nélkül kitölti a 276-ot
- [ ] a fülikonok **16–19 px** magasak (nem 22)
- [ ] az 1. fül csempéi **44 × 30**, oszlopköz **81**, **sorköz 64**
- [ ] a felirat a csempe **alatt**, középre zárva
- [ ] a Derítőfény kis képe **44 × 30**, az **x 37**-en (a rács 1. oszlopával
      egy vonalban), a felirat **a csúszka fölött**, a csúszka **127 × 27**
- [ ] a Visszavonás/Újra **132 × 28**, 5 px hézag, a **panel aljához** kötve
- [ ] a finomhangolás négy csúszkája **191 × 27**, ~53 px osztásközzel
- [ ] az effekt-rács **88 × 71** osztásközzel (ez ma már jó)
- [ ] a párban álló gombok **98 × 28**, a retusálásé **118 × 28**
- [ ] a legördülők **21 px** magasak

**Kirajzolt teszt kötelező** (`tests/app/qml_functional/test_editor_panel_rendered_651.py`
mintájára): a méreteket a **megjelenített** fán kell állítani, nem property-ből
olvasva — és a javítás nélkül el kell buknia.

### Állapot (#741)

A fenti lista **a felső sáv kivételével teljesítve**; az őr-teszt
`tests/app/qml_functional/test_editor_panel_geometry_741.py` (49 állítás, a
javítás előtt 44 bukott el). Ami NYITVA maradt:

- a `MainToolbar` elrejtése szerkesztő módban — a `Main.qml`-t érinti, ezért
  külön körben (ld. [`ui-audit-editor.md`](ui-audit-editor.md) 2.9,
  eltérés-táblázat 15. sora).

Két helyen a megvalósítás **szándékosan** tér el a lap betűjétől, mindkettő
indoklással:

1. **A Visszavonás/Újra sor függőleges helye.** A méret (132 × 28) és a
   hézag (5) átvéve, de a sor NEM a panel aljára van szegezve: nálunk a
   panel nyúlik, és a #616 épp azt javította, hogy nagy ablakban a gombok
   több száz képponttal a tartalom alatt jelentek meg. A sor a tartalom
   alja + kis rés, de sosem lejjebb a látható terület aljánál.
2. **A csempe-cella 80 + 1 képpont** a 81 + 0 helyett — így a 44 képpontos
   csempekép egész számú eltolással ül a cella közepén, és nem csúszik el
   fél képponttal a Derítőfény-sorhoz képest. Az OSZTÁSKÖZ változatlanul 81.

---

*Bizonyítottsági fok: megerősített.* A `respack.yt` rétegtéglalapjai
(201 + 55 elem), az `editpanel.tre` kötései, és a `.tre` makrói
(`macros.tre`, `fontmacros_win.tre`). Az effekt-rács méretei független
képernyőkép-méréssel is egyeznek ([`ui-audit-editor.md`](ui-audit-editor.md)
3.2).
