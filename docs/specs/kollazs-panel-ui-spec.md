# A Kollázs-panel MEGVALÓSÍTÁSI UI-specifikációja (2026-08-18)

Ez a lap **nem kutatási jegyzőkönyv**, hanem *építési rajz*: annyira
részletes, hogy egy fejlesztő session találgatás nélkül meg tudja írni a
felületet. Amit tartalmaz: elemfa, komponensnevek, `objectName`-ek,
geometria és annak **méretezési törvénye**, a vezérlő API-szerződése, az
interakciós állapotgép, a feliratok, a rajzolandó ikonok, a teszt-szerződés
és a jegyekre bontás.

**A viselkedés és a bizonyítékok forrása** (ezeket ne másold ide, hivatkozz
rájuk):

| lap | mit ad |
|---|---|
| `picasa-kollazs-felulet.md` | a **működés**: parancstábla, képesség-maszk, gyűrű-matematika, helyi menük, kimenet, megőrzött beállítások |
| `picasa-create-features.md` **1.10** | a **statikus geometria**: mind a 156 elem koordinátája és mérete, mind az 52 felirat hivatalos magyarral |
| `picasa-create-features.md` **1.9** | a hat **elrendezés-algoritmus** (a pakolók) |
| `picasa-gomb-es-menu-rendszer.md` | a gombok és menük rajza (9-szeletes gomb, állapotszínek) |
| `picasa-eger-es-kijeloles.md` | az egérmodell (Ctrl/Shift, a modosítók **folyamatos** lekérdezése) |
| `design-guide.md` | színtokenek, tipográfia |

**Új ebben a lapban** (a 2026-08-18-i kör eredménye, máshol nem szerepel):
a 2. szakasz — a panel **elrendezés-törvénye** a `respack.yt` `.tre`
kényszereiből. Ez válaszolja meg azt, amire eddig egyetlen lapon sem volt
válasz: **mi történik, ha az ablak nem 800×534.**

---

## 1. A lelet — mi van meg, és mi nincs

| | eredeti | PicasaPy ma (`CreateDialogs.qml` 37–139) |
|---|---|---|
| forma | **teljes lap** a dokumentum-fülsávban | modális párbeszédablak |
| vezérlők száma | ~30 a panelen + 12 a vászon körül | **3** (típus, keret, célfájl) |
| vászon | élő, szerkeszthető, WYSIWYG | **nincs** — a kép csak a mentés után látszik |
| kép-manipuláció | mozgatás / forgatás / méretezés / csere / rétegsorrend | nincs |
| háttér, oldalformátum, tájolás, térköz, árnyék, feliratok | mind állítható | **egyik sem** |
| Klipek lap | van, „Klipek (N)" felirattal | nincs |
| kimenet | Kollázsok album + `.cxf` piszkozat + asztali háttérkép | egyetlen JPEG a fájlválasztóból |

**A mag ellenben KÉSZ.** A `src/picasapy/collage/` csomag (3537 sor, 214+
teszt) tartalmazza mind a hat elrendezést, a három keretet, a
képesség-maszkot (`themes.capabilities_for`), a vászonműveleteket
(`canvas.py`: rétegsorrend, snap, keverés, feliratszámok) és a `.cxf`
írót/olvasót. **Ez a jegy tehát nem algoritmus-, hanem felület-munka:
a meglévő tiszta függvényekre kell felületet húzni.**

Egyetlen mag-hiány van, és ezt előre ki kell mondani (ld. 6.5):
a `picasa_render.make_picasa_collage` **maga számolja ki az elrendezést**,
így nem tud kirenderelni egy KÉZZEL átrendezett vásznat. Kell mellé egy
`render_nodes(nodes, settings)` bejárat, különben a WYSIWYG hazudik.

---

## 2. ⭐ A panel elrendezés-törvénye — a `.tre` kényszerrendszeréből

**Forrás:** `referencia/tre-eroforrasok/collagepanel.tre` (514 sor) és
`macros.tre`. **Bizonyítottsági fok: megerősített** — a makrók
definíciója szó szerint ott áll.

### 2.1 A kényszer-nyelvtan

```
XConstraint  sajátArány, szülőArány, eltolás
```

= *a saját szélességem `sajátArány`-ánál lévő pont a szülő szélességének
`szülőArány`-ánál lévő ponthoz igazodik, `eltolás` képponttal.*
Ugyanez `YConstraint`-tel függőlegesen. A `MaintainOffset <él>` azt jelenti:
az adott él **megtartja a tervezői távolságát** a szülő megfelelő élétől
(azaz odahorgonyzódik).

A használt makrók:

| makró | jelentése |
|---|---|
| `m_centerX` / `m_centerY` / `m_centerXY` | `0.5, 0.5, 0` — középre |
| `m_scaleXY` | mind a négy él 0 eltolással a szülőére → **kitölti a szülőt** |
| `m_offsetLT` | bal + felső él horgonyzva (méret marad) |
| `m_offsetLB` | bal + **alsó** él horgonyzva |
| `m_offsetLTR` | bal + felső + jobb → vízszintesen nyúlik |
| `m_offsetLTRB` | mind a négy → **minden irányban nyúlik** |
| `m_hidden` | alapból rejtett |

### 2.2 A törvény, egy mondatban

> **A bal hasáb FIX MÉRETŰ, a vászon-oldal NYÚLIK.**

A hivatkozott sorok:

```
collagepanel/rightcontainer: collagepanel/base
m_offsetLTRB                       ; mind a négy él horgonyozva → NYÚLIK

collagepanel/tabbase: collagepanel/base
m_offsetLT                         ; bal+felső horgony
YConstraint 1, 0, 406              ; az ALSÓ élem a szülő TETEJÉTŐL 406 px
Property enableclip 0              ; → FIX 276 × 386, nem nyúlik

collagepanel/cancelbutton|resetbutton|makedesktop|sharebutton: collagepanel/tabbase
m_offsetLB                         ; a fix tabbase ALJÁHOZ kötve → szintén fix
```

Ezt a felhasználó képernyőképe **számszerűen igazolja**: egy ~1352 px
széles ablakban a négy alsó gomb ugyanott van, ahol 800 px-esben
(a panel tetejétől 415 / 448 px-re), és alattuk **nagy üres sáv** marad a
bal hasábban. Ha a hasáb nyúlna, a gombok az ablak aljára ülnének.

### 2.3 A vászon-oldal láncolata

```
rightcontainer  = base − (bal 289, fent 20, jobb 10, lent 10)    ; nyúlik
previewcontainer= rightcontainer                                  ; m_scaleXY → kitölti
previewclip     = previewcontainer                                ; 0,0,0 mind a négy élen
previewinset    = previewclip − (bal 12, fent 35, jobb 12, lent 35)
previewshadow   = A LAP (az oldalformátum arányára illesztve, középen)
previewroot     = ugyanott — ebben ülnek a kép-csomópontok
```

```
collagepanel/previewinset: collagepanel/previewclip
XConstraint 0, 0, 12       XConstraint 1, 1, -12
YConstraint 0, 0, 35       YConstraint 1, 1, -35
```

**A 35 képpontos függőleges behúzás nem véletlen:** pontosan a fölötte és
alatta lebegő gombsor (28 px) + 2 px rés + 5 px levegő. A rendszer
önmagával konzisztens — ez erős megerősítés arra, hogy az olvasat helyes.

### 2.4 A négy lebegő csoport — a LAP-hoz kötve, nem a kerethez

Mind a négy a `previewshadow` (= a lap) gyereke, tehát **együtt mozog a
lappal**, amikor az oldalformátum vagy az ablak mérete változik:

| csoport | kényszer | jelentés |
|---|---|---|
| `action_group` | `m_centerX` + `YConstraint 1, 0, -2` | az alsó élem a lap TETEJE fölött 2 px-re → **a lap fölött**, középen |
| `rand_group` | `m_centerX` + `YConstraint 0, 1, 2` | a felső élem a lap ALJA alatt 2 px-re → **a lap alatt**, középen |
| `z_order_group` | `m_centerY` + `XConstraint 0, 1, 2` + `m_hidden` | a bal élem a lap JOBB széle mellett 2 px-re → **a laptól jobbra**, függőlegesen középen |
| `snap_rotation_group` | `m_centerY` + `XConstraint 1, 0, -2` + `m_hidden` | a jobb élem a lap BAL széle előtt 2 px-re → **a laptól balra**, függőlegesen középen |

> ⚠️ **Helyesbítés a `picasa-kollazs-felulet.md` 4. szakaszához.** Ott a
> két oldalsó csoport „a vászon bal/jobb széle mellett" szerepel, a
> tervezővászon abszolút koordinátáival (383 / 727). A `.tre` szerint
> **a LAP széléhez** tapadnak, nem a vászonkerethez — és mindkettő
> **`m_hidden`**, azaz alapból REJTETT. A képernyőképen sem látszanak.
> Az abszolút 383/727 a tervezői alapállás, nem a futásidejű hely.

**Mikor látszanak?** A `m_hidden` + a képesség-maszk 4. bitje (kijelölés)
együtt adja: **akkor, ha van kijelölt kép** és a téma engedi a kijelölést.
*(Bizonyítottsági fok: **erős**. A `m_hidden` megerősített; az, hogy a
kijelölés hozza elő őket, a parancsaik természetéből következik — mind a
nyolc kijelölésre hat —, közvetlen `showtarget` nincs rájuk.)*

### 2.5 A bal hasáb belső kényszerei

| elem | kényszer | következmény |
|---|---|---|
| `tabs` | `m_offsetL` + `YConstraint 0,0,5` | a fülsáv a tabbase tetejétől 5 px |
| `tabpanel1`, `tabpanel2` | `X 0,0,4` / `X 1,1,-4` / `Y 0,0,30` / `Y 1,1,-4` | a laptartalom a tabbase-t tölti ki 4/30/4/4 behúzással |
| `borders_group` | `m_offsetT` + `X 0,0,0` + `X 1,1,0` + `m_hidden` | **teljes szélességű**, alapból rejtett |
| `spacing_group` | `m_offsetT` + `m_centerX` + `m_hidden` | középre, alapból rejtett |
| `theme_popup` | `m_offsetT` + `m_centerX` + `Property itempadding 2 2 20 4` | középre; a lenyíló tételek belső margója |
| `format_menu` | `m_offsetT` + `X 0,0,4` + `Property maxrows 0` | balra 4 px-re; a lista **nem korlátozza a sorok számát** |
| `delete_custom_aspect` | `m_offsetT` + `X 1,1,-4` | **jobbra igazítva**, a laptartalom jobb szélétől 4 px |
| `orientation_container`, `leftdivider`, `format_title_clip`, `bkg_settings_title_clip`, `borders_label_clip`, `spacing_label_clip` | `m_centerX` | vízszintesen középre |
| `set_frame_center` | `m_offsetLT` + `m_hidden` | fix hely, alapból rejtett |
| `solo` (klip-lista) | `m_offsetLTR` + `YConstraint 1,1,-10` | vízszintesen nyúlik, alul 10 px-re a laptartalom aljától |
| `shadow_checkbox`, `caption_checkbox` | `Property setpressed 1` + `m_hit_childlabel` | **alapból bepipálva**; a **feliratra** kattintva is kapcsol |
| `color_bg` | `Property setpressed 1` + `showtarget colorpick_container` | az egyszínű az alapértelmezés |
| `bitmap_bg` | `showtarget background_container` + `showtarget background_bitmap` | két dobozt hoz elő egyszerre |
| `tab1` | `setpressed 1` + `showtarget tabpanel1` | a Beállítások lap az alapértelmezett |
| `cancelbutton` | `Property escapekey 1` | **az Esc a Bezárás** |
| `move_up`, `move_down` | `m_autorepeat` | nyomva tartva **ismétlődnek** (a `move_top`/`move_bottom` NEM) |

### 2.6 A mi méretezési szabályunk — ezt kell megvalósítani

A tervezővászon 800 × 534. A panel a **teljes tartalomterületet** kapja
(a dokumentum-fülsáv alatt).

> **Mi a „teljes tartalomterület" (#1026).** A `panelroot.tre` szerint a
> `collagepanel` a `mainuipanel` **testvére**: a felső éle a fülsáv alatt
> (`YConstraint 0, 0, tabdiv`), az alsó az **ablak alján**
> (`YConstraint 1, 1, 0`). A könyvtár felső eszközsávja és alsó
> tálca-/kimeneti sávja viszont a `mainuipanel` **gyereke**
> (`thumbui.tre`: `importbutton`, `sbutton`, `timelinebutton`,
> `globalmode`, `bottombevel_base`, `#include outputlayout.tre`) — tehát a
> projekt-lapon nem ez a két sáv „rejtőzik el", hanem a **könyvtár panelja
> tűnik el egészben**, és a helyét a vászon kapja meg. Nálunk ezt egyetlen
> kapcsoló hordozza (`Main.qml`: `libraryFrameVisible`), hogy a keret ne
> bomolhasson darabonkénti elrejtésekre; az őre a
> `tests/app/qml_functional/test_library_frame_hidden_1026.py`. Mért
> nyereség 1280 × 800-as ablakban: a panel 631 → 737 px (+106 px), a lap
> 708 × 531 → 849 × 637 px (+44% terület).

A leképezés:

```
base            = a tartalomterület
tabbase         = (3, 20)  FIX 276 × 386
makedesktop     = (10, 415)  127 × 28      ; mind a négy gomb FIX helyen,
sharebutton     = (147, 415) 133 × 28      ; a base bal-felső sarkához mérve
resetbutton     = (10, 448)  127 × 28
cancelbutton    = (147, 448) 133 × 28
rightcontainer  = base − (289, 20, 10, 10)          ; NYÚLIK
previewinset    = rightcontainer − (12, 35, 12, 35)
lap (sheet)     = previewinset-be illesztve, arány = az oldalformátumé,
                  KÖZÉPEN, egész pixelre kerekítve
```

**Minimális panelméret:** 800 × 534 alatt a bal hasáb már nem fér el.
A panel `implicitWidth: 800`, `implicitHeight: 534`; ennél kisebb ablaknál
a vászon-oldal zsugorodik a `previewinset` nulla méretéig, a bal hasáb
soha. *(Ez a #411 precedense: a fix szélességű oldalpanelt tilos
ablakarányosan skálázni.)*

---

## 3. A panel helye az alkalmazásban

### 3.1 Dokumentum-fülsáv (`collagetab`)

Az eredetiben a kollázs **saját lap** a fülsávban: `panelroot/collagetab`
(390, 8) 125 × 21, felirata „Kollázs", jobb szélén **✕ bezárógomb**.
A könyvtár lapja („Könyvtár") mellette marad, tartalma megőrződik.

Nálunk ilyen fülsáv **még nincs**. A megvalósítás:

- Új komponens: **`DocumentTabStrip.qml`** — a `MainToolbar` alatt, a
  tartalomterület fölött; magassága 29 px (a `design-guide.md`
  „felső fül-sáv 29 px" sora). Balra a rögzített **„Könyvtár"** fül
  (nem zárható), mellette a nyitott projekt-lapok.
- A sáv **csak akkor látszik**, ha legalább egy projekt-lap nyitva van —
  különben a mai kinézet nem változik (regresszió-mentesség).
- Fülváltásnál a könyvtár állapota (kijelölés, görgetés) **nem vész el**:
  a `LightboxFeed` `visible: false`-ra vált, nem semmisül meg.

### 3.2 Belépési pontok

| honnan | mai állapot | teendő |
|---|---|---|
| Létrehozás ▸ Képkollázs… (`PicasaMenuBar.qml`) | modálist nyit | a lapot nyitja meg |
| `TrayBar` kollázs-gombja | modálist nyit | ua. |
| `LightboxHeader` (mappa-fejléc) | nincs | `create_collage` gomb, 29 × 27 |
| a Projektek ▸ **Kollázsok** album egy elemére duplakattintás | nincs | a `.cxf` betöltése a lapra |

**A forrás** a mai `_sources_for` szabályt követi (#455): **ha a
képtálcán van kép, az a forrás**, egyébként a rács kijelölése. Ha egyik
sincs, a lap **akkor is megnyílik**, üres vászonnal és a mai
„Select pictures in the library first…" tippel a bal hasábban (#922).

### 3.3 Bezárás

- **Bezárás gomb / Esc** (`escapekey 1`): ha van mentetlen módosítás,
  `CCollageUI::ConfirmCloseTitle` háromgombos kérdés →
  **Piszkozat mentése** / **Módosítások elvetése** / Mégse. A piszkozat a
  **Kollázsok** albumba kerül `.cxf`-ként.
- Piszkozat nélküli állapotban a lap kérdés nélkül bezárul.

---

## 4. Az elemfa — komponensek, `objectName`-ek, geometria

A `objectName` **szerződés**: a funkcionális tesztek ezen keresztül
találják meg az elemeket (ld. 12.). A nevek az eredeti `.tre`-neveket
követik `collage` előtaggal, camelCase-ben.

### 4.1 A váz

| QML komponens | `objectName` | geometria |
|---|---|---|
| `CollagePanel.qml` (gyökér) | `collagePanel` | a tartalomterület |
| ↳ `Item` bal hasáb | `collageTabBase` | (3, 20) **fix** 276 × 386 |
| ↳↳ `CollagePanelTabBar.qml` | `collageTabBar` | (3, 25) 276 × 25; két fül 92 × 25 |
| ↳↳ `CollageSettingsTab.qml` | `collageSettingsTab` | (13, 55) 266 × 351 |
| ↳↳ `CollageClipsTab.qml` | `collageClipsTab` | (13, 55) 256 × 352 |
| ↳ `PicasaButton` ×4 | `collageMakeDesktopButton`, `collageShareButton`, `collageResetButton`, `collageCloseButton` | ld. 2.6 |
| ↳ `CollageCanvas.qml` | `collageCanvas` | `rightcontainer` (nyúlik) |

A két fül felirata: **„Beállítások"** és **„Klipek (%1)"** — a második a
**tényleges klip-darabszám**mal (`collageUI::tab2_title`), minden
felvétel/törlés után újraírva.

> ⚠️ **Két külön erőforrás — ne keverd (2026-08-18).** A `.tre` statikus
> fülcímkéje (`collagepanel/tab2-label`) magyarul „**Képek**"
> (`panel-feliratok-hu.tsv`), a futásidejű formátum viszont
> `collageUI::tab2_title` = „Clips (%d)" / „**Klipek (%d)**". A frissítőt
> (`0x0083b890`) **négy** hely hívja (`0x00830f30`, `0x00831e10` —
> panelépítés/újraépítés —, `addclips` `0x0083b180`, `deleteclips`
> `0x0083b590`), ezért a látható felirat gyakorlatilag mindig
> „Klipek (N)" — a felhasználó képernyőképén is „Klipek (80)". A
> megvalósításban a fül felirata `qsTr("Clips (%1)")` → „Klipek (%1)";
> a „Képek (%1)" hibrid az eredetiben **nem létezik**.

### 4.2 „Beállítások" lap — elemenként

Az `x, y` a **`tabpanel1` bal-felső sarkához** képest értendő (a
1.10-es abszolút értékből 13 / 55 levonva).

| # | komponens | `objectName` | x, y | méret | mikor látszik |
|---|---|---|---|---|---|
| 1 | `CollageThemePopup.qml` | `collageThemePopup` | 0, 8 | 266 × 56 | mindig |
| 2 | `Text` „Képszegélyek" | `collageBordersLabel` | 3, 67 | 239 × 15 | maszk 9. bit |
| 3 | `Item` keretsor | `collageBordersGroup` | 0, 67 | **266** × 89 | maszk 9. bit |
| 3a–c | `CollageBorderButton.qml` ×3 | `collageBorder0/1/2` | 34 / 103 / 172, 88 | 62 × 62 | ua. (69 px osztás) |
| 4 | `Item` térköz-csoport | `collageSpacingGroup` | 6, 68 | 250 × 81 | maszk 10. bit |
| 4a | `Text` „Rács vastagsága" | `collageSpacingLabel` | 21, 76 | 225 × 21 | ua. |
| 4b | `Slider` | `collageSpacingSlider` | 35, 98 | 191 × 27 | ua. |
| 4c–d | `Text` „Egyik sem" / „Maximális" | `collageSpacingMinLabel` / `…MaxLabel` | 35 / 140, 125 | 83 / 86 × 14 | ua. |
| 5 | `Rectangle` elválasztó | `collageLeftDivider` | 0, 154 | 256 × 3 | mindig |
| 6 | `Text` „Háttér beállításai" | `collageBkgTitle` | 3, 159 | 239 × 15 | maszk 0. bit |
| 7 | `Item` rádiócsoport | `collageBackgroundTypes` | 6, 178 | 127 × 55 | maszk 0. bit |
| 7a | `RadioButton` „Egyszínű" | `collageColorBgRadio` | 6, 179 | 24 × 24 (+ felirat 31, 182 / 101 × 24) | ua. |
| 7b | `RadioButton` „Kép használata" | `collageBitmapBgRadio` | 6, 206 | 24 × 24 (+ felirat 31, 209) | ua. |
| 8 | `Item` színválasztó doboz | `collageColorPickContainer` | 134, 180 | 49 × 49 | 7a aktív |
| 8a | `Rectangle` (kör) | `collageColorCircle` | 140, 186 | 37 × 37, `radius: 18.5` | ua. |
| 8b | pipetta ikon | `collageDropperIcon` | 180, 198 | 24 × 14 | ua. |
| 9 | `Item` háttérkép-doboz | `collageBackgroundContainer` | 134, 180 | 135 × 49 | 7b aktív |
| 9a | minta | `collageCurrentBackground` | 140, 186 | 37 × 37 | ua. |
| 9b | `PicasaButton` „A kijelölt elemek használata" | `collageBkgFromSelection` | 185, 186 | 71 × 37 | ua. |
| 10 | felugró paletta | `collagePickerPanel` | 48, 9 | 218 × 178 | 8-ra kattintva |
| 11 | `Text` „Oldalformátum" | `collageFormatTitle` | 3, 235 | 239 × 15 | mindig |
| 12 | `CollageFormatMenu.qml` | `collageFormatMenu` | 3, 255 | 243 × 21 | mindig |
| 13 | kuka gomb | `collageDeleteCustomAspect` | **jobbra igazítva −4** | 14 × 14 | ha egyéni arány az aktív |
| 14 | `Item` tájolás | `collageOrientation` | 88, 280 | 74 × 22 | mindig |
| 14a–b | `collageLandscapeButton` / `collagePortraitButton` | | 88 / 125, 280 | 37 × 22 | ua. |
| 15 | `CheckBox` „Árnyékok rajzolása" | `collageShadowCheckbox` | 5, 303 | 14 × 14 (+ felirat 22, 302) | maszk 11. bit |
| 16 | `CheckBox` „Képfeliratok megjelenítése" | `collageCaptionCheckbox` | 4, 328 | 14 × 14 (+ felirat 22, 327) | mindig |
| 17 | `PicasaButton` „Beállítás képkockaközéppontként" | `collageSetFrameCenter` | 137, 310 | 124 × 30 | **csak** `framegrid` |

**A 3. és a 4. UGYANAZT a helyet foglalja** — soha nem látszik együtt.
A 15. és 16. jelölőnél a **feliratra kattintva is kapcsol**
(`m_hit_childlabel`).

**A `collageThemePopup` lenyílója** (a 4. képernyőkép): hat sor, mind
**ikon + kétsoros szöveg** — a téma neve és a leírása egy sorban, a
hivatalos magyar szöveggel:

| kulcs | a lenyíló sora |
|---|---|
| `picturepile` | **Képkupac**: szétszórt képek hatását kelti |
| `picturegrid` | **Mozaik**: a képek automatikus illesztése az oldalra |
| `framegrid` | **Képkockamozaik**: mozaik hangsúlyos központi képpel |
| `regulargrid` | **Rács**: a képek szabályos sorokba és oszlopokba rendezése |
| `contactsheet` | **Indexkép**: Miniatűr tájékoztató jellegű fejléccel |
| `multiexp` | **Többszörös exponálás**: Képek egymás tetejére helyezése |

A kiválasztott sor a becsukott vezérlőn is ugyanígy, ikonnal jelenik meg.
A tételek belső margója `itempadding 2 2 20 4` (bal 2, felső 2, jobb 20,
alsó 4) — a jobb oldali 20 px a lenyíló-nyílnak.

### 4.3 „Klipek" lap

| komponens | `objectName` | x, y (a `tabpanel2`-höz) | méret |
|---|---|---|---|
| `PicasaButton` „Továbbiak..." (bal ikonnal) | `collageGetMoreClips` | 6, 5 | 166 × 28 |
| `PicasaButton` „+" | `collageAddClips` | 201, 5 | 28 × 28 |
| `PicasaButton` „–" | `collageDeleteClips` | 234, 5 | 28 × 28 |
| `GridView` a klipekkel | `collageClipList` | 4, 36 | vízszintesen nyúlik, alul −10 |

A „Továbbiak..." átvált a **Könyvtár** fülre, és ott megjelenít egy
**„Vissza a kollázshoz"** gombot; a kollázs lapja nyitva marad.

### 4.3/b ⭐ MI a Klipek lista FORRÁSA — megfejtve (2026-08-23, #1276)

A 4.3 eddig a lap **geometriáját** írta le. A #1276 azt kérdezi, ami
ennél fontosabb: **honnan jön a lista tartalma.**

**A számláló megadja a választ.** A fülfeliratot a `0x0083b890(darab)`
írja ki (`"Clips (%d)"`), és a darabszámot a hívó számolja. A
`0x0083b590` (a `deleteclips` ága) végén ez áll:

```asm
0x0083b7c3  mov  ecx, [ebp + 0x124]      ; a panel FORRÁS-CSOMÓPONTJA
0x0083b7c9  mov  eax, [ecx + 0x330]      ; elemszám
0x0083b7d1  shr  eax, 1
0x0083b7d5  mov  edx, [ecx + 0x32c]      ; elem-mutatótömb
0x0083b7e0  mov  ecx, [edx]              ; az elem
0x0083b7e6  cmp  byte ptr [ecx + 0x5a], 0
0x0083b7ea  jne  …                       ; a JELÖLT elemeket KIHAGYJA
0x0083b7ec  add  esi, 1
0x0083b7f7  push esi
0x0083b7f8  call 0x83b890                ; -> "Klipek (N)"
```

⚠️ **A `+0x32c` (elemtömb) / `+0x330` (elemszám) mezőpár és a `+0x5a`
elem-jelző NEM a kollázsé** — ez a **`CSelectionNode`** szerződése, amit
a `picasa-eger-es-kijeloles.md` **10.** szakasza már rögzít
(„a `CSelectionNode` minden művelete a saját elemtömbjén — `+0x32c`,
darabszám `+0x330 >> 1`"), és a `+0x5a` ugyanott a **kizáró jelző**
(a lasszóból is kihagyja, 4/e).

⇒ **A Klipek lap egy `CSelectionNode` elemlistáját mutatja** — vagyis
**ugyanazt a fajta fotó-készletet, amiből a rács is él**, nem a kollázs
saját csomópontjait. A lista építő ciklusa (`0x0083b610`) szintén ezen a
`[panel+0x124]` csomóponton megy, és a `0x007166c0` (a
kijelölés-csomópont segédfüggvény-tartománya) hívásán át kéri az elemeket.

**A „Továbbiak…" gomb ezt megerősíti.** A `collagepanel/getmoreclips`
kezelője (`0x0082dcec`–`0x0082dd09`) **átvált a könyvtárra**
(`panelroot/collagetab`), és megjelenít egy **„Vissza a kollázshoz"**
gombot (`collagepanel::back_to_collage` = *Back to Collage*). Vagyis a
munkamenet-készlet **bővítése a könyvtárban történik**, nem a lapon —
ami csak akkor értelmes, ha a lap egy **készletet** mutat, amiből
válogatni lehet, és nem a már bekerült elemeket.

### Eredeti / nálunk / teendő

| | eredeti | nálunk | teendő |
|---|---|---|---|
| a lista forrása | egy **`CSelectionNode`** elemlistája (`[panel+0x124]` → `+0x32c`/`+0x330`) | `controller.collageNodes` — a **kollázs saját csomópontjai** | a forrást a fotó-készletre cserélni |
| a `+0x5a`-jelölt elemek | **kimaradnak** a számból és a listából | nincs megfelelője | szűrő kell |
| „Klipek (N)" száma | a **szűrt** elemszám | a csomópontok száma | a szűrt készletből |
| „Továbbiak…" | átvált a könyvtárra + **„Vissza a kollázshoz"** gomb | — | ez a bővítés útja |

> **Ez magyarázza az üres lapot is:** ha az újranyitott kollázsnak nincs
> csomópontja, a mi listánk üres — miközben az eredetiben a lap a
> **készletet** mutatja, ami a kollázs tartalmától független.

*Bizonyítottsági fok: **megerősített** a mezőhasználatra (a
`CSelectionNode` szerződése a saját specünkben már rögzítve) és a
„Továbbiak…" ágra (szó szerinti sztringek). **NYITVA marad**, hogy a
`[panel+0x124]` csomópontot **melyik** forrásból tölti fel a panel
megnyitásakor (az aktuális mappa, a kijelölés vagy a fotótálca) — az
írási helyet nem sikerült megtalálni (ld. a 16.1 módszertani
megjegyzését a lineáris szken elcsúszásáról).*

### 4.3/c ⭐ A „Klipek" lap = a KÉPTÁLCA — a hat kérdés vezérlőnként (2026-08-23, #1153)

A #1276 megállapította, hogy a lista egy `CSelectionNode`, de nyitva
hagyta, **melyik**. A `.tre` súgószövegei eldöntik: **a Képtálca**
(Picture Tray).

#### A döntő bizonyíték: a súgószövegek

| vezérlő | súgó (EN) | súgó (HU) |
|---|---|---|
| `addclips` | *Add selected clips to the **collage*** | **Kijelölt klipek felvétele a kollázsba** |
| `deleteclips` | *Remove selected clips from the **tray*** | **A kijelölt képek eltávolítása a tálcáról** |
| `getmoreclips` | *Get more clips from the Library* | **További képek beolvasása a könyvtárból** |

⇒ A „+" a tálcából **a kollázsba** vesz fel; a „–" **a TÁLCÁRÓL** töröl,
**nem a kollázsból**. A lap tehát a **gyűjtő-munkaterület**, nem a kollázs
tartalma — pontosan ezért lehet benne olyan kép, ami még nincs a
kollázsban.

**A Képtálca önálló, projekt-szintű fogalom** a Picasában:
`Tray::ID_PICTURE_HOLDINPICTURETRAY` („Kijelölés megtartása"),
`Tray::ID_REMOVE_SELECTION` („Kijelölés eltávolítása"), `IDS_CLEARTRAY`
(„Ezzel a művelettel a teljes tálcát kiüríti…"), és
`IDS_MUST_SELECT` — *„A művelet elvégzéséhez a **képtálcán** elemeknek
kell lenniük."*

> ⛔ **Ebből következik a függőség:** a Klipek lap **nem építhető meg
> helyesen Képtálca nélkül** — az a **#455**. A #1153 és a #1276 tehát a
> #455-re épül, nem előzi meg.

#### A négy vezérlő, hat kérdés szerint

| | `getmoreclips` | `addclips` („+") | `deleteclips` („–") | `solo` (a lista) |
|---|---|---|---|---|
| **felirat** | **„Továbbiak..."** (`Label`) | **nincs** — a `.tre`-ben a `-label` sor **ki van kommentezve** (`#collagepanel/addclips-label`), csak ikon | **nincs**, ugyanígy | — |
| **ikon** | `back_icon`, **`m_buttoniconleft`** (balra) — **vissza-nyíl** | `add_icon`, `m_centerXY` | `delete_icon`, `m_centerXY` | — |
| **mit csinál** | átvált a **könyvtárra** (`panelroot/collagetab`) és megjelenít egy **„Vissza a kollázshoz"** gombot (`0x0082dcec`–`0x0082dd09`) | a **kijelölt** klipeket felveszi a kollázsba | a **kijelölt** klipeket törli **a tálcáról** | a tálca elemeit mutatja |
| **stílus** | `superbutton(listheader_button)` | `superbutton(button_notext)` | `superbutton(button_notext)` | — |
| **geometria** (a `tabpanel2`-höz képest) | (6, 5) **166 × 28** | (201, 5) **28 × 28** | (234, 5) **28 × 28** | (4, 36) **247 × 311** |
| **billentyű** | nincs (a `.tre`-ben nincs kötés) | nincs | nincs | — |

*(A `tabpanel2` maga: abszolút (13, 55), **256 × 352**, alapból
`m_hidden` — a tab1 látszik először. A fül gombja: `tab2`, abszolút
(95, 25), 92 × 25.)*

#### ⛔ NEGATÍV EREDMÉNY: a kollázs-panelnek NINCS `.fen` fájlja

A #1153 első javasolt lépése a `.fen` párbeszéd-leíró megkeresése volt.
**Nincs ilyen:** a 46 `.fen` között egyetlen kollázs- vagy klip-vonatkozású
sincs. Ennek oka szerkezeti — a `.fen` a **modális párbeszédeké**, a
kollázs-panel viszont a főablakba ágyazott `.tre`-panel. A források tehát:
`.tre` (szerkezet + súgó), `respack.yt` (geometria), bináris (viselkedés).

#### Eredeti / nálunk / teendő

| | eredeti | nálunk | teendő |
|---|---|---|---|
| a lista forrása | **a Képtálca** elemei | `controller.collageNodes` — a kollázs csomópontjai | **#455** után a tálcára kötni |
| „+" | tálca → **kollázs** | — | felvétel a kollázsba |
| „–" | törlés **a TÁLCÁRÓL** | — | ⚠️ nem a kollázsból! |
| „Továbbiak..." | könyvtárra vált + „Vissza a kollázshoz" | — | a bővítés útja |
| „+"/„–" felirata | **nincs, csak ikon** | — | ikonos gomb |
| „Továbbiak..." ikonja | **vissza-nyíl**, balra | — | — |

*Bizonyítottsági fok: **megerősített** — a súgószövegek szó szerint a
`.tre`-ből és a honosítási táblából; a geometria a `respack.yt` nyers
rectjeiből; a „Továbbiak…" ága a binárisból. A `.fen` hiánya
kimerítő keresés (mind a 46 fájl).*

### 4.4 A vászon körüli csoportok

| komponens | `objectName` | elhelyezés (2.4) | tartalom |
|---|---|---|---|
| `CollageActionRow.qml` | `collageActionRow` | a lap fölött, 2 px, középen | Az összes kijelölése (100 × 26) · Az összes kijelölés megszüntetése (100) · Eltávolítás (100) · Beállítás háttérként (134); 3 px rés |
| `CollageRandomRow.qml` | `collageRandomRow` | a lap alatt, 2 px, középen | Véletlenszerű kollázs (115 × 26) · Képek összekeverése (116) · Megjelenítés és szerkesztés (115) |
| `CollageSnapColumn.qml` | `collageSnapColumn` | a laptól balra, 2 px, függőlegesen középen | `collageSnap12/3/6/9`, 15 × 15, 16 px osztás |
| `CollageZOrderColumn.qml` | `collageZOrderColumn` | a laptól jobbra, 2 px, függőlegesen középen | `collageMoveTop/Up/Down/Bottom`, 15 × 15, 16 px osztás |

A két oszlop **csak kijelöléskor** látszik (2.4). A `collageMoveUp` és
`collageMoveDown` **`autoRepeat: true`**.

Gombok engedélyezése:

| gomb | engedélyezve, ha |
|---|---|
| Az összes kijelölése | maszk 4. bit **és** van legalább 1 kép |
| Az összes kijelölés megszüntetése · Eltávolítás | van kijelölés |
| Beállítás háttérként · Megjelenítés és szerkesztés | **pontosan egy** kép van kijelölve |
| Képek összekeverése | maszk 2. bit **és** ≥ **2** kép |
| Véletlenszerű kollázs | maszk 3. bit **és** ≥ **1** kép |

*(A 2./3. bit küszöbei: `0x0082fa0f`, `0x0082fa60`.)* A 2. képernyőkép
ezt igazolja: kijelölés nélkül a „Az összes kijelölés megszüntetése",
„Eltávolítás", „Beállítás háttérként" és a „Megjelenítés és szerkesztés"
**halvány**, a 3. képen — egy kijelölt képpel — mind aktív.

---

## 5. A téma-váltás hatása — a képesség-maszk mátrixa

Egyetlen forrás: `collage.themes.capabilities_for(theme)`; ne szülessen
témánkénti `if` a QML-ben. A vezérlő `collageCapabilities` térképként adja
tovább (ld. 8.).

| téma | keretsor | térköz | árnyék | árnyék alapból | kijelölés | gyűrű | összekeverés | szétszórás | háttér |
|---|---|---|---|---|---|---|---|---|---|
| Képkupac | **✓** | – | ✓ | **BE** | ✓ | **✓** | ✓ | **✓** | ✓ |
| Mozaik | – | **✓** | ✓ | KI | ✓ | – | ✓ | – | ✓ |
| Képkockamozaik | – | **✓** | ✓ | KI | ✓ | – | ✓ | – | ✓ |
| Rács | – | **✓** | ✓ | KI | ✓ | – | ✓ | – | ✓ |
| Indexkép | **✓** | – | ✓ | **BE** | ✓ | – | – | – | ✓ |
| Többszörös exponálás | – | – | **–** | KI | **–** | – | – | – | **–** |

Két külön szabály:

1. **Ha a térköz-csúszka látszik és az értéke 0, az árnyék-jelölő
   bekapcsolódik** (`0x008318be`) — nulla térköznél az árnyék az egyetlen,
   ami elválasztja a képeket. (Bekapcsolódik, nem tiltódik le.)
2. Téma-váltáskor a **kézi elrendezés újraszámolódik** (maszk 1. bit): a
   csomópontok helye a téma pakolójából jön újra. A kézi mozgatás tehát
   téma-váltásnál **elveszik** — ez az eredeti viselkedés, nem hiba;
   előtte nem kérdez.

---

## 6. A vászon

### 6.1 Koordinátarendszer — 1024 egység

**A lap belső szélessége 1024 egység**, nem képpont
(`0xcf3f68 = 1/1024`). A magasság `1024 × arány`, ahol az arány az
oldalformátumból és a tájolásból jön. Minden tárolt szám ebben él, és a
`.cxf` is ezt írja.

```
képernyő_x = lap.x + u * lap.szélesség / 1024
képernyő_y = lap.y + v * lap.szélesség / 1024      ; UGYANAZ az osztó!
```

Az azonos osztó a lényeg: a lap **nem torzít**, csak méretez.

### 6.2 A csomópont-modell

`src/picasapy/app/collage_model.py` — `QAbstractListModel`, a lista
sorrendje a **rajzolási sorrend**: a **0. index van legalul, az utolsó
legfelül** (`canvas.py` már ezt tartja).

| szerep | típus | jelentés |
|---|---|---|
| `path` | str | a kép útvonala (a `.cxf` `+0x48` mezője) |
| `centerX`, `centerY` | float | a középpont **lapegységben** |
| `width`, `height` | float | a csomópont mérete lapegységben, **forgatás előtt**, a kerettel együtt |
| `theta` | float | elforgatás **radiánban**; 0 = felfelé, pozitív = az óramutató járása szerint |
| `border` | str | `noborder` / `whiteborder` / `polaroid` |
| `caption` | str | a Polaroid-keretre írt felirat |
| `selected` | bool | a kijelölés |
| `missing` | bool | a fájl nem található (ld. 9.4) |

⚠️ **A `theta` előjele (golden-mérés, #1035).** Az eredeti a `.cxf` tárolt
`theta`-ját előjelváltás nélkül használja, képernyő-koordinátában (`y`
lefelé):

```
X = cx + u*cos(theta) - v*sin(theta)
Y = cy + u*sin(theta) + v*cos(theta)
```

A **megkülönböztető próba**: a csempe felső élének közepe (`u = 0`, `v = -b`)
pozitív `theta` mellett `X = cx + b*sin(theta)`, vagyis **jobbra** mozdul;
negatív `theta`-nál a kép **jobb oldala kerül magasabbra**. A QML
`Item.rotation` és a mag `render.screen_rotation`-je egyaránt ezt követi. A
`cv2.getRotationMatrix2D` viszont a pozitív szöget az ELLENKEZŐ irányba
forgatja — az átfordítás egyetlen helyen, a `screen_rotation`-ben történik, a
**tárolt** `theta`-hoz tilos hozzányúlni (azt a Picasa is visszaolvassa).

**A kezdő méret** a darabszámból (spec 9.0):

```
n <= 1 → s = 1.0
n  > 1 → s = min(1.0, 1 / sqrt(sqrt(n) - 1))
alapszélesség = s * 1024 * 0.33          ; ha a maszk 8. bitje áll
```

Vagyis **egy kép a lap szélességének 33%-át kapja**; 10 képnél ~0,68-szoros,
100-nál ~0,33-szoros. Ez csak a Képkupacra, az Indexképre és a Többszörös
exponálásra vonatkozik — a rácsos témák a pakolóból kapnak méretet.

> ⚠️ **Pontosítás (#989).** Ez az `alapszélesség` a **viszonyítási pont**
> (`spec[0x3c]`; a fogantyú 1,0-s méretaránya, nálunk
> `collageBaseNodeWidth`), nem minden csomópont tényleges szélessége. A
> csomópontok geometriáját **a téma pakolója** adja, mind a hat témánál —
> ugyanaz a kód, ami mentéskor is fut
> (`collage.picasa_render.layout_nodes_for_aspects`). A Képkupacnál ez azt
> jelenti, hogy a képek egy NÉGYZETBE illeszkednek (`pile.pile_size`,
> 1.9.2) — az álló és a fekvő kép tehát egyforma nagy —, és a szögük sem
> nulla (`pile.pile_rotation` legyezőhatása). A #920 első változata minden
> témára a Képkupac egyszerűsített szórását futtatta; ettől a
> téma-választó egyáltalán nem hatott a vászonra.

### 6.3 Rajzolás a QML-ben

- A lap: `Rectangle` a háttérszínnel (vagy `Image` háttérképpel), 1 px
  `#9a9a9a` kerettel és **külső vetett árnyékkal** (`previewshadow` — ezért
  hívják így).
- A csomópontok: `Repeater` a modellre; minden elem
  `Image { source: "image://thumbs/" + path }` + `transform: [Scale, Rotation]`.
  A miniatűr-szolgáltató **már létezik** (`thumbnail_provider.py`,
  `application.py:640`) — ne szülessen új.
- **A miniatűr-méret a darabszámmal lépcsőzik** (spec 9.0, `spec[0x30]`):
  ≤ 99 kép → 2276 px, 100–199 → 256, 200–349 → 128, ≥ 350 → **64**.
  Ez az, amitől a 350 képes kollázs nem fullad meg.
- A keret rajza (`whiteborder`, `polaroid`) a `collage/frames.py`
  geometriájából jön (`polaroid_geometry`, `white_border_width`) — a QML
  ne találjon ki sajátot.
- **Az árnyék csomópontonként**, ha a `collageShadows` be van kapcsolva
  (#1021). A csomópont ELSŐ gyereke, negatív `z`-vel: így a saját képe alá,
  de a lejjebb lévő csomópontok fölé kerül — pontosan úgy, ahogy a rajzoló
  teszi („minden csempének a saját árnyéka közvetlenül előtte rajzolódik",
  `collage/nodes.py`). Ettől plasztikus a Képkupac.
  - A rajzelem `BorderImage`, a forrása a vezérlőtől kapott `data:` URL
    (`collageShadowSprite`). Az árnyék **szeparábilis** elmosás egy
    téglalapon (9/b.1), ezért kilenc szeletre bontva **pontosan**
    újraépíthető — nem közelítés (mérve 2/255 alatti eltéréssel a mag
    `draw_shadow`-jához képest).
  - Az **eltolást vissza kell forgatni** a csomópont saját rendszerébe: a
    mag az eltolást a forgatás UTÁN adja hozzá, tehát az a lap tengelyei
    szerint értendő, a csempe viszont a csomóponttal együtt fordul.
  - ⚠️ **Shader (`QtQuick.Effects.MultiEffect`) NEM használható**: a modul a
    disztribúciós PySide6 mellett nincs telepítve („module
    "QtQuick.Effects" is not installed"), a `pip`-es CI-ban viszont igen —
    egy shaderes megoldás zöld CI mellett hagyna árnyék nélkül éles gépet.
  - **Ára** (RPi5, valódi OpenGL, vsync nélkül, 350 csomópont):
    7,9 → 23,7 ms/képkocka. A költség NEM a technikáé: egy 4 × 4 képpontos
    átlátszó `Rectangle` csomópontonként ugyanennyibe kerül (25,6 ms) —
    a jelenetgráf csomópontonkénti EXTRA eleme a drága, tehát más rajzolási
    mód sem volna olcsóbb. 100 képnél 7,1 → 11,2 ms.
- A Polaroid-felirat csak akkor látszik, ha a **Képfeliratok
  megjelenítése** be van pipálva (a buboréksúgó ki is mondja: „…szövegként
  való megjelenítése *Polaroid fényképezőgép* szegélyű képeken").

### 6.4 A háttér — három mód

| mód | mikor | mit rajzol |
|---|---|---|
| `solid` | „Egyszínű" rádiógomb | a választott ARGB |
| `image` | „Kép használata" | a háttérkép, **tompítva** (`DimmedBitmapTheme`) |
| `avg` | a `collage::avgcolor` beállítás | a képek **átlagszíne**, `solid`-ként |

⚠️ **Az `avgcolor` felülír mindent**: ha be van kapcsolva, a mód 0 lesz,
akármit kért a felhasználó (`0x008364a0`). A Többszörös exponálásnak saját
háttérkezelése van (mód 2), ezért nincs is háttér-beállítása.

**A háttérkép a kollázs SAJÁT képeinek egyike** (#1009), indexszel
hivatkozva: az előnézetet a `0x00830a00(this, index)` tölti fel, és
`index == -1` esetén kilép (`0x00830a8b`). Ebből három szabály következik,
és mindhármat a `collage_background.CollageBackgroundMixin` tartja:

1. A „Kép használata"-ra váltás **azonnal választ képet** — alapból az
   elsőt. (*Erős, nem megerősített*: a golden `AI2.cxf` és `AI5.cxf`
   mindkettőjében az első kép a háttér — ld. `picasa-create-features.md`
   1.6/e. Alapértelmezés, nem törvény.)
2. „A kijelölt elemek használata" ezt **felülírja**.
3. A háttér a **képet** követi, nem a rést: keverés és csere után is
   ugyanaz a kép marad a háttér, és ha a képet kiveszik a kollázsból, a
   háttér a következő érvényesre esik vissza — törött hivatkozás nem
   maradhat.

A `.cxf`-be a háttérkép `<background type="image"><src>…</src></background>`
alakban megy ki (a `color` attribútum ilyenkor elmarad). A **kirajzolt
JPEG** háttere a #1015 óta szintén a választott kép: a lapot KITÖLTI
(arányt tartva, középről vágva), és **TOMPÍTVA**: a golden háttere a
forráskép **85,1%-án** áll.

A tompítás mérve, nem stílusból: az `AI2.jpg` háttérképe csempeként is
szerepel az `AI1.jpg`-ben, tompítás nélkül. Csempeként a telített fehér a
99,9. percentilisen is 255; háttérként **217-nél falba ütközik** (117 646
képpont egyetlen tüskében, fölötte 0,06%). `(255 − 217) / 255 = 38/255 =
0x26` — bájtra a `#26000000`, amit az élő előnézet is ráfest.

⚠️ A kitölt-vagy-nyújt kérdés **nincs lemérve** — a kitöltés a mi
döntésünk, és `tests/collage/test_kephatter_1015.py` rögzíti, hogy a
megváltoztatása szándékos legyen.

### 6.5 ⚠️ A mag hiánya: `render_nodes`

A `picasa_render.make_picasa_collage(sources, settings)` **maga rendezi el**
a képeket. Egy kézzel átrendezett vászon kirenderelésére nem alkalmas —
ha a mentés újraszámolja az elrendezést, a felhasználó **mást kap, mint
amit lát**. Ezért kell:

```python
def render_nodes(nodes: Sequence[CollageNode],
                 settings: PicasaCollageSettings) -> CollageReport:
    """A MEGADOTT csomópont-elhelyezésekből rajzol — nem számol elrendezést."""
```

A meglévő `make_picasa_collage` marad, és mostantól így épül fel:
elrendezés (a téma pakolója) → `render_nodes`. Így a felület és a mentés
**ugyanazt az egy rajzolót** használja. Ez a jegy **első** lépése; enélkül
minden más WYSIWYG-hazugság.

---

## 7. Interakció

### 7.1 Kijelölés

- Kattintás egy képre: kijelöli, a többiről leveszi.
- **Ctrl+kattintás**: hozzáad / elvesz. **Shift+kattintás**: tartomány a
  rajzolási sorrend szerint. (A `picasa-eger-es-kijeloles.md` modellje.)
- Kattintás **üres területre**: a kijelölés megszűnik (`CollageDeselectHandler`).
- **Ctrl+A** / **Ctrl+D**: mind / semmi (a buboréksúgók kimondják).
- **Del**: a kijelöltek eltávolítása.
- Kijelölt kép köré **gyűrű** kerül, és megjelenik a két oldalsó gombsor.

### 7.2 A gyűrű

A `respack` rajza: **`#ring` 132 × 132**, `#target_chicklet` 23 × 15,
`#angle_placemark` 9 × 10 — kódból rajzolt overlay, ezért van
kikommentezve a panelfából. A gyűrű a csomópont **befoglaló téglalapjának
közepére** kerül (`RingNodeLayoutHandler`: `((x0+x1)/2, (y0+y1)/2)`).

**A gyűrű mérete képernyő-egységben állandó** (132 px), nem a képpel
együtt méreteződik. *(Bizonyítottsági fok: **erős** — a méret a
`respack`-ből megerősített, az, hogy nem skálázódik, a rajz overlay
természetéből következik.)*

Két érzékeny terület:
- **a gyűrű belseje** → mozgatás (`RingMoveHandler`),
- **a fogantyú a gyűrű peremén** → forgatás + méretezés (`RingKnobHandler`).

### 7.3 Mozgatás

```
lenyomás:   fogási_eltolás = egér − csomópont_pozíció
            csomópont.opacity = 0.9
mozgatás:   csomópont_pozíció = egér − fogási_eltolás
felengedés: csomópont.opacity = 1.0  ;  collage_adapt lépés
```

**Nincs elhúzási küszöb** — az első egérmozdulatra indul. (A 10 képpontos
küszöb a fájlrendszer felé menő OLE-vonszoláshoz tartozik, nem ide.)

**`Alt` + lenyomás:** a kép **a legfelső rétegbe ugrik**, és onnan mozog
tovább. Ha már a legfelső, **nem történik semmi** (nincs „villanás").
Az `Alt` **nem másol és nem klónoz** — ha a megvalósításban „Alt =
másolat" jelenne meg, az kitalált funkció.

**Ejtés egy másik képre:** a két kép **kicserélődik** — a fájlútvonalak
cserélnek helyet, a **fogadó keret, méret és elforgatás változatlan**.
Nem áthelyezés, hanem csere.

> ⚠️ **A cserét kizárólag VALÓDI EJTÉS-GESZTUSHOZ kösd, ne a
> felengedéshez** (2026-08-18-i élő hiba: feltétel nélküli kereséssel
> minden kijelölő kattintás némán kicserélt két fájlt, mert a kupac képei
> fedik egymást). Az eredeti három kapuja: (1) az ejtés **külön
> eseményazonosító** (11), nem a felengedés (4); (2) találat-ellenőrzés a
> csere előtt; (3) **„ugyanaz a csomópont → nincs csere"**. Részletek és
> címek: `picasa-kollazs-felulet.md` **5.2/b**. A „nincs elhúzási küszöb"
> szabály a **gyűrűs mozgatásra** vonatkozik, nem arra, hogy történt-e
> egyáltalán vonszolás.

### 7.4 Forgatás és méretezés — EGY fogantyú

```
dx = egér.x − gyűrű_közép.x ;  dy = egér.y − gyűrű_közép.y
ha NINCS Ctrl:  szög = atan2(−dx, dy)            → FORGATÁS
ha NINCS Alt:   táv  = sqrt(dx² + dy²)           → MÉRETEZÉS
```

- Az `atan2(−dx, dy)` a **+y tengelytől** mér: a **0° a 12 óra iránya** —
  ezért hívják az igazítógombokat óralap szerint.
- **A `Ctrl` a forgatást, az `Alt` a méretezést KAPCSOLJA KI.** Egyik sem
  „mód"; mindkettőt nyomva tartva a fogantyú nem csinál semmit.
- ⚠️ **A módosítót a húzás KÖZBEN, folyamatosan kell kérdezni**
  (`GetAsyncKeyState`), nem a lenyomás pillanatában rögzíteni. Qt-ben:
  a **`onPositionChanged` eseményének `event.modifiers()`-e**, nem a
  `onPressed`-ben eltárolt érték. Aki elmenti, más programot ír.
- Kurzor: lenyomáskor `pan_hand_drag`, felengedéskor `pan_hand_normal`
  (nálunk `Qt.ClosedHandCursor` / `Qt.OpenHandCursor`).

**Visszajelzés húzás közben** (a vászon fölött, `collagepanel/angletext`
és `scaletext`):

- **„Szög: %1"** — ⚠️ a kiírás előtt a szög **előjelet vált**
  (`fchs`): a `canvas.angle_caption_degrees()` ezt már helyesen csinálja,
  **használd azt**, ne számolj újra.
- **„Méretarány: %1%"** — a lenyomás pillanatában **100**
  (`canvas.scale_caption_percent(scale, base_scale)`).
- Felengedéskor mindkét szöveg eltűnik.

### 7.5 A négy igazítógomb

`canvas.SNAP_COMMANDS` — a forgáspont a befoglaló téglalap közepe.

| gomb | tárolt érték |
|---|---|
| `snap_12` | 0,0 |
| `snap_3` | +90,0 |
| `snap_6` | +180,0 |
| `snap_9` | **−90,0** (a menü „270 fok" felirata a SZÖVEG, nem a tárolt érték) |

### 7.6 A három helyi menü

Jobb egérgomb; a kijelölés mérete dönt.

**Egy kijelölt kép** (8 tétel): Eltávolítás · Beállítás háttérként ·
Beállítás képkockaközéppontként · Szegély módosítása ▸ · Forgatás
igazítása ▸ · Legfelülre helyezés · Legalulra helyezés · Megjelenítés és
szerkesztés.

**Több kijelölt kép** (3 tétel): Eltávolítás · Szegély módosítása ▸ ·
Forgatás igazítása ▸.

**A vászon üres területén** (4 tétel): Az összes kijelölése · Az összes
kijelölés megszüntetése · Képek összekeverése · **Képek szétszórása**.

Almenük: **Szegély módosítása** → Egyik sem · Fehér szegély · Polaroid
fényképezőgép. **Forgatás igazítása** → 0 fok · 90 fok · 180 fok · 270 fok.

> ⚠️ Ugyanannak a parancsnak **két felirata** van: a gombon
> „Véletlenszerű kollázs", a menüben „Képek szétszórása". Nem elírás —
> mindkettőt úgy kell átvenni, ahogy van.

### 7.7 A `collage_adapt` lépés

Minden manipuláció **végén** (felengedéskor) lefut: pillanatképet készít a
beállítás-mezőkről egy árnyékblokkba, a csomópontok szélességét
`1/1024`-gyel normalizálja, majd újraépít. Nálunk ez a
`collageAdapt()` belső lépés: **a kézi szerkesztés nem veszhet el** egy
későbbi újrarajzoláskor. *(A mechanizmus megerősített; hogy a CÉLJA a
kézi szerkesztés megőrzése, erős következtetés.)*

---

## 8. A vezérlő API-szerződése

Új fájl: **`src/picasapy/app/collage_controller.py`** (`CollageMixin`), és
**`src/picasapy/app/collage_model.py`** (`CollageNodeModel`). A mai
`create_controller.makeCollage` **marad** (a mozgófilm és a régi
API-hívók miatt), de a panel NEM azt hívja.

### 8.1 Property-k

| név | típus | jelentés |
|---|---|---|
| `collageOpen` | bool | nyitva van-e a lap |
| `collageTheme` | str | a hat kulcs egyike |
| `collageBorder` | str | a három keret egyike |
| `collageSpacing` | float | 0…1 (nem képpont!) |
| `collageShadows` | bool | árnyékrajzolás |
| `collageCaptions` | bool | képfeliratok |
| `collageOrientation` | str | `landscape` / `portrait` |
| `collageFormatKey` | str | pl. `10x15m` |
| `collagePageRatio` | float | magasság / szélesség — ebből él a lap alakja |
| `collageBackgroundMode` | str | `solid` / `image` / `avg` |
| `collageBackgroundColor` | QColor | |
| `collageBackgroundImage` | str | a háttérkép útvonala (a csomópont-indexből számolva) |
| `collageBackgroundImageUrl` | QUrl | UGYANAZ URL-ként — a QML `Image.source`-a ezt kösse be, kézzel fűzött `"file://" + út` HELYETT (#1009) |
| `collageNodes` | QAbstractListModel | a vászon modellje |
| `collageSelection` | list[int] | |
| `collageFrameCenter` | int | −1 = nincs |
| `collageClipCount` | int | a „Klipek (%1)" száma |
| `collageDirty` | bool | van-e mentetlen módosítás |
| `collageCapabilities` | QVariantMap | `{borders, spacing, shadow, selection, background, shuffle, scramble, ring, rotate}` — a `themes.capabilities_for`-ból |
| `collageShadow` | QVariantMap | `{offsetX, offsetY, blur, opacity, alpha}` **lapegységben**, vagy üres térkép, ha nincs árnyék (#1021). A MENTÉS `render_settings()`-éből számol (`picasa_render.shadow_for_settings`), tehát a vászon és a mentett kép nem tud elválni. Értesítője a `collageShadowChanged`, amit a jelölőnégyzet, a téma, a darabszám és a laparány jelzése egyaránt kivált. |

Minden property-hez `<név>Changed` jelzés. Kivétel a
`collageBackgroundImageUrl`: ugyanaz az adat más alakban, ezért a
`collageBackgroundImageChanged`-re jár (külön jelzésnek nem volna fogadója —
`scripts/check_dead_signals.py`).

⚠️ **Útvonal → URL: sose kézzel.** A `"file://" + útvonal` Windowson
**érvénytelen** URL-t ad (a `C:` portnak látszik), a `"file:" + útvonal`
pedig `#`-et tartalmazó fájlnévnél vágja el a nevet — mindkét esetben
NÉMÁN, üres képpel. Az átalakítás egy helyen él:
`app/formatting.to_file_url` (a `to_local_path` párja). A #1009-ben ez éles
hiba volt, és a windows-CI-láb fogta meg.

### 8.2 Slotok

```python
@Slot(list)          def openCollage(rows)            # a lap megnyitása
@Slot()              def closeCollage()
@Slot(str)           def setCollageTheme(key)
@Slot(str)           def setCollageBorder(key)        # a kijelöltekre, ha van
@Slot(float)         def setCollageSpacing(value)
@Slot(bool)          def setCollageShadows(on)
@Slot(bool)          def setCollageCaptions(on)
@Slot(str)           def setCollageOrientation(kind)
@Slot(str)           def setCollageFormat(key)
@Slot(str)           def setCollageBackgroundMode(mode)
@Slot("QColor")      def setCollageBackgroundColor(color)
@Slot()              def setBackgroundFromSelection()
@Slot(list)          def setCollageSelection(indices)
@Slot()              def selectAllNodes()
@Slot()              def selectNoNodes()
@Slot()              def removeSelectedNodes()
@Slot(int, float, float)        def moveNode(index, cx, cy)     # lapegység
@Slot(int, float, float)        def transformNode(index, scale, theta)
@Slot(int, int)                 def swapNodes(a, b)
@Slot(int)                      def raiseNodeToTop(index)       # Alt+húzás
@Slot()  def moveSelectionTop() / moveSelectionUp() / moveSelectionDown() / moveSelectionBottom()
@Slot(str)           def snapRotation(command)        # "snap_12" …
@Slot()              def shufflePictures()            # rand_order
@Slot()              def scrambleCollage()            # rand_placement
@Slot()              def setFrameCenterFromSelection()
@Slot()              def viewAndEditSelection()
@Slot(bool)          def createCollage(asDesktopBackground)   # EGY kódút!
@Slot()              def resetCollage()
@Slot(list)          def addClips(rows)
@Slot(list)          def deleteClips(rows)
@Slot(float, int, result="QVariantMap")  def collageShadowSprite(blur, alpha)
```

> A `collageShadowSprite` a KIRAJZOLHATÓ árnyék-csempét adja vissza
> (`{url, support, border}`), az elmosást a vászon **képpontjaiban** kérve.
> Kép és geometria egy kérésben: két külön forrásból a kettő elválna, és az
> árnyék elcsúszna a saját csempéjétől.

> **A „Kollázs létrehozása" és az „Asztali háttérkép" UGYANAZ a művelet**,
> egyetlen logikai paraméterrel. Aki kettőt ír meg belőle, kétszer fogja
> karbantartani.

### 8.3 Jelzések

```python
collageProgress   = Signal(int, str)   # százalék, szakasz-szöveg
collageDone       = Signal(str)        # a kész fájl útvonala
collageFailed     = Signal(str)
collageNoImages   = Signal()           # „Mentés mellőzve"
collageFormatMismatch = Signal()       # asztali háttérkép, eltérő formátum
collageNeedsSelection  = Signal()      # „Kötelező a kijelölés"
collageDraftSaved = Signal(str)
```

A háttérmunka a meglévő `BackgroundWorkerMixin`-en fut (`_start_background`),
ahogy a mai `makeCollage` — új szálkezelés ne szülessen.

---

## 9. Kimenet, megőrzött beállítások, üzenetek

### 9.1 Létrehozás

- Kép nélkül: **„Mentés mellőzve"** + „A kollázs nem menthető, mert az
  összes képet eltávolították. Vegyen fel legalább egy képet, és
  próbálkozzon újra."
- Asztali háttérképnél, ha az oldalformátum ≠ a képernyőé:
  **„Figyelmeztetés: eltérő formátumok"**, két gombbal: **Beállítás ennek
  ellenére** / **Beállítás mellőzése**. A szöveg maga ajánlja a megoldást
  (válaszd a „Jelenlegi megjelenítés" tételt).
- Folyamat: „Kollázs létrehozása... inicializálás" → „Kollázs létrehozása
  - %1%" → „Kollázs létrehozása... leállítás" → **„A kollázs kész
  (kattintson ide)"**. Megszakításkor megerősítés: „Megszakítja a kollázs
  létrehozását?" — *Kollázs megszakítása* / *Megszakítás mellőzése*.
- A Többszörös exponálásnak saját szövege van: „Képek egymásra helyezése",
  „%1 / %2 feldolgozva".

**A kimeneti fájl törvénye** (a teljes bizonyíték:
`picasa-kollazs-felulet.md` **9.1/b**) — **fájlválasztó NINCS, soha**:

| kérdés | az eredeti válasza |
|---|---|
| hova | `<Képek>/Picasa/Kollázsok` (a mappanév honosított erőforrás) |
| milyen néven | a **forrásmappa/album címe**; üres címnél tartalék: „kollázs" |
| ütközéskor | `név1.jpg`, `név2.jpg`… — `%s%lu`, **szóköz nélkül** |
| mi íródik | a JPEG (minőség **90**) ÉS a vele azonos nevű **`.cxf`** |
| hogyan | tmp-fájlba, majd átnevezés — előbb a `.cxf`, aztán a `.jpg` |
| utána | indexelés + **a lap bezárja magát** + `locate`: a könyvtár a kész fájlra ugrik |
| újramentéskor | „Meglévő cseréje" → az **eredeti útvonal** felülírása, nincs számozás |

**Eredeti / nálunk / teendő** (a mai `app/collage_output.py`-hoz mérve):

| | eredeti | `collage_output.py` ma | teendő |
|---|---|---|---|
| mappa | `<Képek>/Picasa/Kollázsok` | `~/Pictures/Kollázsok` | a `Picasa` közbülső szint pótlása |
| név | forrásmappa címe | `kollázs-<időbélyeg>` | cím-alapú név + `%s%lu` számozás |
| `.cxf`-pár | mindig | nincs | a mentés írja a `.cxf`-et is |
| JPEG-minőség | 90 | a `write_collage` alapértéke | 90-re rögzíteni |
| felső méret | 5120 (hosszabbik oldal, erős) | fix 1600 széles | 5120-ra emelni |
| atomi írás | tmp + átnevezés | közvetlen írás | tmp + átnevezés, `.cxf` előbb |
| mentés után | lap bezárul + `locate` | jelzés a felületnek | a panel-jegyekben (#948/#949) |

- A fájlnév töve (tartalék): **„kollázs"**; a cél a **Kollázsok** album.

**A folyamatjelző overlay** a vászon közepén (`m_centerXY`, alapból
rejtett): 224 × 80 doboz, benne cím (fent), pörgő (középen), állapotsor
(lent). `objectName: collageProgressOverlay`.

### 9.2 Mentés meglévő fölé

Ha a kollázs egy korábbiból készült: **„Lecseréli a meglévőt, vagy újat
hoz létre?"** — *Meglévő cseréje* / *Új létrehozása* / Mégse.

### 9.3 Megőrzött beállítások (QSettings)

| kulcs | alapérték |
|---|---|
| `collage/theme` | **`picturepile`** |
| `collage/format` | `2` |
| `collage/orientation` | a `.tre`-ben a **fekvő** az előre lenyomott |
| `collage/shadows` | a téma maszkjának **14. bitje** (Képkupac és Indexkép: BE) |
| `collage/showcaptions` | **1** |
| `collage/bgcolor` | — |
| `collage/autosave` | — |
| egyéni arányok | a **meglévő** `custom_aspect_ratios.py`-t használd (#448), ne szüless újat |

### 9.4 Hiányzó képek

| eset | üzenet |
|---|---|
| egyik kép sem található | a kollázs nem szerkeszthető |
| néhány hiányzik | „%1 kép nem található, ezért nem jeleníthető meg…" |
| a `.cxf` hiányzik / olvashatatlan | „Nem található a(z) %1 kollázsfájl" / „Hiba történt a(z) %1 kollázsfájl betöltése során" |

A hiányzó képek a vásznon **helykitöltő csempeként** jelenjenek meg
(`missing: true`), ne tűnjenek el némán.

---

## 10. Feliratok

Mind az 52 felirat és buboréksúgó **hivatalos magyarral**:
`picasa-create-features.md` **1.10.6**. A QML-be a **forrásszöveg
angolul** kerül (`qsTr("Draw Shadows")`), a magyar a `.ts`-be — ez az
i18n-konvenciónk. A hivatalos magyar szöveget **szó szerint** kell
átvenni, még ott is, ahol mi szebbet írnánk (pl. „Beállítás
képkockaközéppontként").

Két csapda:
- „Scramble Collage" = **Véletlenszerű kollázs** (gomb) **és** „Scatter
  Pictures" = **Képek szétszórása** (menü) — ugyanaz a parancs, két
  felirat.
- A „Klipek (%1)" fülfelirat **futásidőben** frissül.

---

## 11. Rajzolandó ikonok

Az eredeti bitmapek nem szállíthatók; SVG-ben kell megrajzolni őket a
meglévő `qml/PicasaPy/icons/` mintájára (`iconInk` tinta, 1 px rács).

| fájl | mit ábrázol | méret |
|---|---|---|
| `collage-theme-picturepile.svg` | szétszórt, döntött fotók | 24 × 24 |
| `collage-theme-picturegrid.svg` | eltérő méretű, illesztett csempék | 24 × 24 |
| `collage-theme-framegrid.svg` | csempék hangsúlyos középső képpel | 24 × 24 |
| `collage-theme-regulargrid.svg` | szabályos 3 × 3 rács | 24 × 24 |
| `collage-theme-contactsheet.svg` | fejléces indexkép | 24 × 24 |
| `collage-theme-multiexp.svg` | egymásra vetített, áttetsző képek | 24 × 24 |
| `collage-border-none.svg` / `-white.svg` / `-polaroid.svg` | a három keret **előnézete** | 62 × 62 |
| `collage-snap-12/3/6/9.svg` | óralap-nyíl a négy irányba | 15 × 15 |
| `collage-move-top/up/down/bottom.svg` | rétegsorrend-nyilak | 15 × 15 |
| `collage-orientation-landscape.svg` | fekvő lap | 23 × 12 |
| `collage-orientation-portrait.svg` | álló lap | 11 × 16 |
| `collage-back.svg` | vissza-nyíl a „Továbbiak..."-hoz | 17 × 15 |
| `collage-trash.svg` | kuka az egyéni arányhoz | 14 × 14 |
| `collage-ring.svg` | a gyűrű overlay | 132 × 132 |

A **pipetta** már megvan (`icons/pipetta.svg`), a kollázs-ikon is
(`icons/collage.svg`).

---

## 12. Teszt-szerződés

A `PROTOKOLL.md` „a KIMENETET ellenőrizd, ne a szándékot" szabálya szerint
**kirajzolt** ellenőrzés kell, minta:
`tests/app/qml_functional/test_editor_panel_rendered_651.py` (valódi
`QQuickView`, több ablakméret, a `_walk()` a vizuális fához — a
`Repeater` elemeit a `findChild` **nem** találja meg).

| teszt | mit állít |
|---|---|
| `test_collage_panel_layout_rendered.py` | 3 ablakméretnél (800 × 534, 1280 × 800, 1920 × 1080): a bal hasáb szélessége **mindig 276**, a négy alsó gomb **mindig ugyanott**, a vászon-oldal nő |
| `test_collage_sheet_aspect.py` | a lap oldalaránya = a formátumé ±0,5 %, a lap a `previewinset`-en belül van, középen |
| `test_collage_groups_follow_sheet.py` | az akciósor a lap fölött, a rand-sor alatta, a két oszlop a lap két oldalán; formátumváltás után is |
| `test_collage_capability_mask_ui.py` | mind a hat témára: a keretsor és a térköz-csúszka **soha nem látszik együtt**; multiexp-nél nincs árnyék/kijelölés/háttér |
| `test_collage_ring_math.py` | `atan2(−dx, dy)`, a 0° a 12 óra; Ctrl→nincs forgatás, Alt→nincs méretezés, mindkettő→nincs semmi |
| `test_collage_drag.py` | nincs elhúzási küszöb; húzás közben `opacity == 0.9`; felengedve 1,0 |
| `test_collage_swap.py` | egy képet a másikra ejtve **cserélnek**, a fogadó mérete/kerete/szöge marad |
| `test_collage_alt_to_top.py` | `Alt`+lenyomás a legfelső rétegbe visz; ha már ott van, a modell **nem változik** |
| `test_collage_render_nodes.py` | a `render_nodes` a kézi elhelyezést rajzolja ki — a mentett kép a vászon állapotát tükrözi |
| `test_collage_labels.py` | mind a 26 felirat és 24 buboréksúgó megvan és lefordított |
| `test_collage_settings_roundtrip.py` | a hét `Preferences`-kulcs mentődik és visszatölt; alapértelmezett téma `picturepile` |

**Az őrnek legyen foga:** minden új tesztet futtass le a javítás **nélkül**
is, és győződj meg róla, hogy elbukik.

---

## 13. Munkamegosztás — nyolc jegy, ütköző fájlok nélkül

Ez a panel egyetlen PR-ban 3000+ sor lenne. A bontás úgy készült, hogy
**két session sose írja ugyanazt a fájlt**:

| # | jegy | érintett fájlok |
|---|---|---|
| 1 | **`render_nodes`** — a rajzoló szétválasztása elrendezésre és rajzolásra (6.5) | `collage/picasa_render.py`, `tests/collage/` |
| 2 | **Csomópont-modell + vezérlő** — a 8. szakasz teljes API-ja, felület nélkül | `app/collage_model.py`, `app/collage_controller.py`, `tests/app/` |
| 3 | **Dokumentum-fülsáv** (3.1) | `qml/PicasaPy/DocumentTabStrip.qml` |
| 4 | **A panel váza + a méretezési törvény** (2., 4.1) | `qml/PicasaPy/CollagePanel.qml` |
| 5 | **Beállítások lap** (4.2, 5.) | `CollageSettingsTab.qml`, `CollageThemePopup.qml`, `CollageBorderPicker.qml`, `CollageFormatMenu.qml`, `CollageBackgroundBox.qml` |
| 6 | **A vászon és a gyűrű** (6., 7.1–7.5) | `CollageCanvas.qml`, `CollageSheet.qml`, `CollageNode.qml`, `CollageRing.qml` |
| 7 | **Gombcsoportok + helyi menük** (4.4, 7.6) | `CollageActionRow.qml`, `CollageRandomRow.qml`, `CollageSnapColumn.qml`, `CollageZOrderColumn.qml`, `CollageContextMenus.qml` |
| 8 | **Klipek lap, kimenet, piszkozat, beállítások** (4.3, 9.) | `CollageClipsTab.qml`, `CollageProgressOverlay.qml`, `app/collage_controller.py` (9. szakasz) |

**Sorrend:** 1 → 2 párhuzamosan a 3-mal; 4 a 2 után; 5/6/7 párhuzamosan a
4 után; 8 utoljára. Az **1-es és a 2-es a torlódási pont** — azokat kell
először elvinni.

⚠️ A `controller.py` és a `Main.qml` **forró fájl**: a `CollageMixin`
beörökítése és a panel Main.qml-beli bekötése **az integrátor session
dolga** — a feature-branch csak leírja az igényt a jegyben.

---

## 14. Amit NEM szabad megépíteni

- **A háromgombos eszközpaletta** (`#tools_group`: mozgatás / méretezés /
  forgatás gombok) — kikommentezve, nincs mögötte kezelő. Elhagyott terv;
  a kiadott Picasa **közvetlen manipulációt** használ.
- **`savebutton`, `loadbutton`, `layer_up`, `layer_down`** — a
  parancskezelőben ott vannak, de nincs hozzájuk vezérlő. Fejlesztői
  maradványok.
- **A Picasa 2-es kollázs-párbeszéd** kulcsai (`CollageType::*`,
  `IDS_COLLAGE_MAKER_DIALOG_TITLE`, `IDS_CONFIRM_COLLAGE`,
  `il_MakeCollageButton`) — a **leváltott** funkció. Aki ezekre épít, a
  régi programot írja meg.
- **`Alt` = másolat** — kitalált funkció, a binárisban nincs (7.3).
- **Külön forgató és külön méretező fogantyú** — egy fogantyú van (7.4).
- **Elhúzási küszöb a vásznon** — nincs (7.3).

---

## 15. Bizonyítottsági fok és nyitott kérdések

| állítás | fok |
|---|---|
| a `.tre` kényszerek és a belőlük levezetett méretezési törvény (2.) | **megerősített** — a makródefiníciók szó szerintiek, és a felhasználó képernyőképe számszerűen egyezik |
| a két oldalsó gombsor a LAPHOZ tapad és alapból rejtett (2.4) | **megerősített** a kényszerre és a `m_hidden`-re |
| a két oldalsó gombsort a **kijelölés** hozza elő | **erős** — a `m_hidden` bizonyított, a kiváltó ok következtetés |
| a parancstábla, a képesség-maszkok, a gyűrű matematikája, a menütételek, a feliratok | **megerősített** |
| a gyűrű 132 × 132-es rajz, és képernyő-egységben állandó | **erős** |
| a maszk **7.** bitje = elforgatás | **erős** |
| a maszk **6.** bitje mit kapcsol | **NYITOTT** — a helye megvan (`+0x219`, `0x00860470`), a jelentése nem. **Nem blokkolja a megvalósítást.** |
| a `framegrid` `CLocationTree` pakolója | **NYITOTT** (#916) — a mai közelítés (középre rögzített kép) marad |

**Ez a lap nem igényel további bináris kutatást a megvalósítás
megkezdéséhez.** A két nyitott pont egyike sem érinti a felületet.
