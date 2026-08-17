# A Kollázs funkció teljes működése (2026-08-17)

Ez a lap a **működést** írja le: mit csinál minden vezérlő, mi történik az
egérrel a vásznon, mikor melyik panelrész látszik, és mi kerül a lemezre.

A **geometria** (mind a 156 elem koordinátája és mérete) és a **feliratok**
(mind az 52, hivatalos magyarral) nem itt vannak, hanem a
`picasa-create-features.md` **1.10** szakaszában — a kettő együtt adja ki a
teljes képet. Az elrendezés-algoritmusok (a hat téma pakolói) ugyanott, az
**1.9**-ben.

Forrás: a `Picasa3.exe` (3.9.141.259) helyi diszasszemblálása, a `respack.yt`
`collagepanel` rétegei és `.tre`-je, a `stringres` EN↔HU táblája, valamint a
tulajdonos futó Picasa 3-áról készült képernyőképek (2026-08-17).
Bizonyítottsági fok szakaszonként jelölve; cím nélküli állítás nincs.

---

## 1. A vezérlő→függvény tábla — a panel teljes parancskészlete

A `collagepanel` minden vezérlőjét **egyetlen** kezelő szolgálja ki:
`0x0082d570` (4721 bájt). Név szerinti összehasonlítás-lánc; a
teljes tábla, ahogy a binárisban áll:

| vezérlő | mit hív | mit csinál |
|---|---|---|
| `theme_popup` | `0x00830530` | témaváltás + `Preferences\collage::theme` írása |
| `border0/1/2` | `border%d` ág | képkeret-választás (`noborder`/`whiteborder`/`polaroid`) |
| `shadow_checkbox` | `0x0083d3a0` | `collage::shadows` |
| `caption_checkbox` | `0x0083d460` | `collage::showcaptions` |
| `portrait` / `landscape` | `0x0083a1a0` | tájolás + `collage::orientation` |
| `format_menu` | (lista, ld. 7.) | oldalformátum |
| `delete_custom_aspect` | `0x0083df40` → `0x007cb7b0` | egyéni oldalarány törlése a `Preferences\AspectRatios`-ból |
| `color_bg` | rádiógomb | egyszínű háttér → a színválasztó látszik |
| `bitmap_bg` | `0x009cd8a0` | képháttér → a háttérkép-doboz látszik |
| `bkg_from_selection` | — | a kijelölt kép legyen a háttér |
| `set_background` | — | ugyanez a vászon feletti gombról |
| `set_frame_center` | `0x0083d520` | a kijelölt kép a Képkockamozaik közepére |
| `select_all` | `0x0083a490(…, 1)` | az összes kijelölése |
| `select_none` | `0x0083a490(…, 0)` | kijelölés megszüntetése |
| `remove_node` | `0x0083abe0` | kijelölt képek eltávolítása |
| `move_top` | `0x008419b0`+`0x00841920` → `0x0083ab30` | legfelülre |
| `move_up` | `0x0083ab30(-1)` | egy réteggel feljebb |
| `move_down` | `0x0083ab30(+1)` | egy réteggel lejjebb |
| `move_bottom` | `0x008419b0`+`0x00841920` → `0x0083ab30` | legalulra |
| `snap_12/3/6/9` | `0x0083b900(szög)` | forgatás-igazítás (ld. 5.4) |
| `rand_order` | `0x0083aab0` | Képek összekeverése (sorrend) |
| `rand_placement` | `0x0083aaf0` | Véletlenszerű kollázs (elhelyezés) |
| `view_and_edit` | `0x0083de20` | a kijelölt kép megnyitása a könyvtárban |
| `addclips` | `0x0083b180` | a kijelölt klipek felvétele |
| `deleteclips` | `0x0083b590` | klipek törlése |
| `getmoreclips` | (ld. 8.) | vissza a könyvtárba „Vissza a kollázshoz" gombbal |
| `tab1` / `tab2` | `0x0083d610` / `0x0083d670` | lapváltás |
| `sharebutton` | `0x0083ce90(…, 0)` | **Kollázs létrehozása** |
| `makedesktop` | `0x0083ce90(…, 1)` | **Asztali háttérkép** — ugyanaz a függvény |
| `resetbutton` | `0x0083d090` | Alaphelyzet |
| `cancelbutton` | `0x0082e35f`… | Bezárás (Esc is, `Property escapekey 1`) |

**Bizonyítottsági fok: megerősített** (minden sor a `0x0082d570`
diszasszemblátumából, a hívott cím a `call` operandusa).

> **A „Kollázs létrehozása" és az „Asztali háttérkép" ugyanaz a művelet.**
> Egyetlen függvény, egyetlen logikai paraméterrel. Aki kettőt ír meg
> belőle, kétszer fogja karbantartani.

---

## 2. A téma képesség-maszkja — ebből következik az egész bal oldal

A hat téma osztálya közös ősre épül, és a **7. vtable-slot** (`+0x1c`) egy
konstans bitmaszkot ad vissza. A `0x00831750` ebből a maszkból mutatja,
rejti és tiltja a panel vezérlőit — **nincs témánkénti külön UI-kód**.

| téma (kulcs) | maszk |
|---|---|
| `picturepile` — Képkupac | **`0x1EBBF`** |
| `picturegrid` — Mozaik | **`0x1C55`** |
| `framegrid` — Képkockamozaik | **`0x1C55`** |
| `regulargrid` — Rács | **`0x0C55`** |
| `contactsheet` — Indexkép | **`0x4B11`** |
| `multiexp` — Többszörös exponálás | **`0x0100`** |

Az eddig megfejtett bitek:

| bit | ha 1 | hol dől el |
|---|---|---|
| 0 (`0x1`) | egy további panelág (`0x00831ac0`) fut le | `0x00831932` |
| 4 (`0x10`) | a **kijelölés engedélyezett** (`select_all` aktív) | `0x008318ed` |
| 9 (`0x200`) | a **három képkeret-gomb** (`borders_group`) látszik | `0x008317f5` |
| 10 (`0x400`) | a **térköz-csúszka** (`spacing_group`) látszik | `0x00831860` |
| 11 (`0x800`) | az **árnyék-jelölő engedélyezett** | `0x00831818` |

Ebből a hat témára:

| téma | keretek | térköz | árnyék | kijelölés |
|---|---|---|---|---|
| Képkupac | **igen** | nem | igen | igen |
| Mozaik | nem | **igen** | igen | igen |
| Képkockamozaik | nem | **igen** | igen | igen |
| Rács | nem | **igen** | igen | igen |
| Indexkép | **igen** | nem | igen | igen |
| Többszörös exponálás | nem | nem | **nem** | **nem** |

**A keretsor és a térköz-csúszka egymást váltja:** a `borders_group`
(13, 122) 266×89 és a `spacing_group` (19, 123) 250×81 **ugyanazt a helyet
foglalja el** a panelen. Sosem látszik mindkettő.

**Két további szabály ugyanitt:**

- Ha a térköz-csúszka látszik és az értéke **0**, az árnyék-jelölő
  **bekapcsolódik** (`0x008318be`, `0x0083193f`) — nulla térköznél az
  árnyék az egyetlen, ami a képeket elválasztja.
- A `set_frame_center` gomb **csak a `framegrid` témánál** látszik
  (`0x00830530`, `framegrid` sztring-összehasonlítás). A `.tre`-ben
  `m_hidden`, tehát alapból rejtett.

**Bizonyítottsági fok: megerősített** a maszkokra és a 4/9/10/11 bitre;
a 0. bit hatása **feltételes** (a hívott `0x00831ac0` nincs kibontva).
A Képkupac-sor egyezik a felhasználó képernyőképével (Képkupac kiválasztva
→ a három keretgomb látszik, térköz-csúszka nincs).

---

## 3. A háttér — három mód, nem kettő

A `background_types` rádiócsoport két gombot mutat (`color_bg`,
`bitmap_bg`), de a modell **három** hátteret ismer:

| mód | kulcs | mit ír a `.cxf`-be |
|---|---|---|
| egyszínű | `solid` | a választott ARGB |
| kép | (a `background_container` képe) | a háttérkép hivatkozása |
| a képek **átlagszíne** | `collage::avgcolor` | `solid`-ként, a kiszámolt színnel |

A `.tre` szerint a **`color_bg` az alapértelmezés** (`Property setpressed 1`),
és mindegyik gomb `showtarget`-tel kapcsolja a saját dobozát:
`color_bg → colorpick_container`, `bitmap_bg → background_container` **és**
`background_bitmap`.

A színválasztó két részből áll: a `colorcircle` (153, 241) 37×37 kör
(`Property round 3`) és a `dropper_icon` (193, 253) 24×14 **pipetta**. A
kattintásra megnyíló paletta a `picker_panel` (61, 64) 218×178, ami a
`.tre`-ben `m_hidden`, `Property palette 1`, és fókuszt ad a
`bkgcolorpick/base`-nek.

A **„Beállítás háttérként"** két helyről érhető el: a `bkg_from_selection`
gomb a panelen (198, 241) 71×37 és a `set_background` a vászon felett
(628, 37) 134×26. Ugyanaz a művelet.

**Bizonyítottsági fok: megerősített** (a `.tre` és a `0x0082d570`);
az `avgcolor` a `0x008364a0`-ból, ld. `picasa-create-features.md` 1.9.11.

---

## 4. A vászon körüli négy gombcsoport

| csoport | hely | tartalom |
|---|---|---|
| `action_group` | (318, 36) 445×28 | Az összes kijelölése · Az összes kijelölés megszüntetése · Eltávolítás · Beállítás háttérként |
| `rand_group` | (346, 475) 354×28 | Véletlenszerű kollázs · Képek összekeverése · Megjelenítés és szerkesztése |
| `snap_rotation_group` | (383, 230) 17×65 | négy forgatás-igazító gomb, **függőlegesen**, a vászon bal széle mellett |
| `z_order_group` | (727, 226) 17×65 | négy rétegsorrend-gomb, **függőlegesen**, a vászon jobb széle mellett |

A két oldalsó csoport 15×15-ös gombokból áll, 16 képpont osztással.

**A `rand_group` a `.tre` szerint a `previewshadow` gyereke,
`m_centerX`, `YConstraint 0, 1, 2`** — azaz a vászon alá tapad, tőle
2 képponttal, vízszintesen középre.

---

## 5. A közvetlen manipuláció a vásznon — a gyűrű

### 5.1 A kezelők

A vászon **nem** saját megoldást használ: a Picasa általános
„gyűrű"-vezérlőjét kapja meg, ugyanazt, amit a filmkészítő
szövegcsomópontjai. A kezelő-osztályok (RTTI):

| osztály | kezelő | mire való |
|---|---|---|
| `RingNodeLayoutHandler` | `0x007e65a0` | a gyűrűt a csomópont **befoglaló téglalapjának közepére** rakja: `((x0+x1)/2, (y0+y1)/2)` |
| `RingMoveHandler` | `0x00868e90` | egy kép **mozgatása** |
| `GroupRingMoveHandler` | `0x008695f0` / `0x008691e0` | többes kijelölés mozgatása |
| `GroupRingMoveEdgeHandler` | `0x008696d0` | mozgatás a gyűrű pereménél fogva |
| `RingKnobHandler` | `0x008680f0` | egy kép **forgatása + méretezése** |
| `GroupRingKnobHandler` | `0x00868570` | többes kijelölés forgatása + méretezése |
| `AngleMarkHandler` / `GroupAngleMarkHandler` | `0x007e6700` / `0x007e6760` | a szögjelölő |
| `RingNodeFadeHandler`, `RingNodeFadeLockHandler` | `0x007e6220`, `0x007e6390` | a gyűrű elhalványítása |
| `CollageNodeHandler` | `0x008609e0` | a képre eső egéresemények (kijelölés, helyi menü, vonszolás) |
| `CollageDeselectHandler` | `0x00886370` | üres területre kattintás |
| `CollagePreviewHandler` | `0x008860e0` | a vászon egésze |
| `MultiExposureNodeHandler` | `0x00887920` | külön kezelő a Többszörös exponáláshoz |

A gyűrű rajza a `respack.yt`-ben megvan, de a panel fájában
**kikommentezve** (`#`-prefix): `#ring` **132×132**, `#move_chicklet`,
`#rotate_chicklet`, `#scale_chicklet`, `#scale_chicklet_alt`,
`#target_chicklet`, `#target_chicklet2` 23×15, `#angle_placemark` 9×10.
Ez nem ellentmondás: ezek **kódból rajzolt** overlay-elemek, nem a
statikus panelfa részei — a képenkénti overlay dinamikus. A felhasználó
képernyőképe mutatja is a gyűrűt a kijelölt képen.

**Bizonyítottsági fok: megerősített** az osztályokra és a címekre;
**erős** arra, hogy a képernyőképen látható gyűrű ez a 132×132-es rajz
(a méret és az elhelyezés egyezik, de a rajzot nem vetettük össze
képpontról képpontra).

### 5.2 Mozgatás

`RingMoveHandler` (`0x00868e90`):

- **1. esemény (egérlenyomás):** megjegyzi a fogási eltolást; a
  csomópont átlátszósága **0,9**-re vált (`0xc7dd40 = 0.9f`,
  `0x008690da`).
- **2./3. esemény (mozgatás):** az új hely = egérpozíció − fogási
  eltolás (`0x0086912b`, `0x00869146`), majd `0x009debd0(node, x, y)`.
- **4. esemény (felengedés):** az átlátszóság vissza **1,0**-ra
  (`0x008690a3` `fld1`).

**Az `Alt` billentyűnek külön ága van** (`0x00868f99`,
`GetKeyState(VK_MENU)`): más útvonalon fut (`0x005121d0`,
`0x009df680`, `0x009df290`, `0x0075c860`). **Hogy pontosan mit csinál,
még nincs megfejtve** — ld. 11.

### 5.3 Forgatás és méretezés — EGY fogantyú, két hatás

`GroupRingKnobHandler` (`0x00868570`). A fogantyú lenyomásakor a kurzor
`pan_hand_drag`-re vált (`0x008687ae`), felengedéskor `pan_hand_normal`-ra.

A gyűrű középpontja `(cx, cy)`; az egér `(mx, my)`;
`dx = mx − cx`, `dy = my − cy` (`0x00868850`).

```
Ctrl NINCS lenyomva  →  FORGATÁS  aktív:
    szög = atan2(−dx, dy)                       (0x008688c9)
    a kijelzett fok = −szög · 180/π             (0xcf4c68 = −57.29577951309)

Alt  NINCS lenyomva  →  MÉRETEZÉS aktív:
    táv  = sqrt(dx² + dy²)                      (0x0086890d)
```

- `GetKeyState(0x11)` = **Ctrl** → `0x00868870`
- `GetKeyState(0x12)` = **Alt** → `0x0086888b`

Tehát **alapesetben a fogantyú egyszerre forgat és méretez**; a `Ctrl` a
forgatást, az `Alt` a méretezést kapcsolja ki. Egyik sem „mód" — mindkettő
nyomva tartva a fogantyú nem csinál semmit.

**Az `atan2(−dx, dy)` az +y tengelytől mér**, nem az +x-től: a 0° a
**12 óra** iránya. Ez pontosan illeszkedik az óralap-elnevezésű
igazítógombokhoz (`snap_12`, `snap_3`, `snap_6`, `snap_9`).

**Visszajelzés vonszolás közben:** a `collagepanel/angletext` a
„Szög: %d" (`collage::angle_format`), a `collagepanel/scaletext` a
„Méretarány: %d%%" (`collage::scale_format`). A méretarány
lenyomáskor **100** (`0x00868992` `push 0x64`). Felengedéskor mindkét
szöveg eltűnik (`0x009cd730`), és lefut egy **`collage_adapt`** nevű
lépés (`0x00868aa4`).

**A szög kijelzése ELŐJELET VÁLT:** a tárolt szöget a kiírás előtt
`fchs`-szel negálja (`0x00868947`). Aki a tárolt fokot írja ki, ellentétes
előjelű számot mutat.

**Bizonyítottsági fok: megerősített.**

### 5.4 Forgatás-igazítás — a `snap_9` **−90°**, nem 270°

`0x0083b900`: végigmegy a kijelölésen, minden csomópontnál a **befoglaló
téglalap közepét** teszi forgásponttá (`0x009dee90`), majd a kapott fokot
`× π/180` (`0xcf3fc8 = 0.017453292519938`) beírja a csomópont
szögmezőjébe (`+0x15c`).

| gomb | átadott érték | cím |
|---|---|---|
| `snap_12` | `0.0` (`fldz`) | `0x0082e0e9` |
| `snap_3` | **`+90.0f`** (`0xcf4370`) | `0x0082e163` |
| `snap_6` | **`+180.0f`** (`0xcf409c`) | `0x0082e1e1` |
| `snap_9` | **`−90.0f`** (`0xcf50d0`) | `0x0082e25f` |

> ⚠️ **Helyesbítés.** A `picasa-create-features.md` 1.4 eddig
> „0° / 90° / 180° / **270°**"-ot írt, és a mi
> `src/picasapy/collage/canvas.py`-nk is `270.0`-t tárol. A bináris
> **−90.0f**-et ad át. Rajzban ugyanaz, **tárolásban nem**: a `.cxf`-be
> `−1.570796` kerül `4.712389` helyett. A helyi menü felirata
> (`Rotate::ID_COLLAGE_ALIGN_270` = „270 fok") a **feliratról** szól, nem a
> tárolt értékről.

Egyetlen kijelölt kép esetén a szög a csoport `+0x288` mezőjébe is
bekerül (`0x0083ba3a`) — ez a fogantyú kiinduló szöge.

**Bizonyítottsági fok: megerősített.**

---

## 6. A három helyi menü

Jobb egérgomb (5. esemény) a `CollageNodeHandler`-ben (`0x00860c5d`,
`0x00860c7a`) a kijelölés mérete szerint választ:

**`collagenode_context_single`** — egy kijelölt kép (`0x007344b0`):

| tétel | kulcs | magyar |
|---|---|---|
| Remove | `CollageS::ID_COLLAGE_REMOVE` | Eltávolítás |
| Set as Background | `CollageS::ID_COLLAGE_SET_BACKGROUND` | Beállítás háttérként |
| Set as Frame Center | `CollageS::ID_COLLAGE_SET_CENTER` | Beállítás képkockaközéppontként |
| Change Border ▸ | `CollageS::ChangeBorder` | Szegély módosítása |
| Align Rotation ▸ | `CollageS::AlignRotation` | Forgatás igazítása |
| Bring to Top | `CollageS::ID_COLLAGE_MOVE_TOP` | Legfelülre helyezés |
| Move to Bottom | `CollageS::ID_COLLAGE_MOVE_BOTTOM` | Legalulra helyezés |
| View and Edit | `CollageS::ID_COLLAGE_VIEW_AND_EDIT` | Megjelenítés és szerkesztés |

**`collagenode_context_group`** — több kijelölt kép (`0x007347a0`),
**három** tétel: Eltávolítás · Szegély módosítása · Forgatás igazítása.

**A vászon menüje** (`0x007348f0`), **négy** tétel:
Az összes kijelölése · Az összes kijelölés megszüntetése ·
Képek összekeverése (`Shuffle Pictures`) ·
**Képek szétszórása** (`Scatter Pictures`).

> ⚠️ **Ugyanannak a parancsnak két felirata van.** A `rand_placement`
> **gomb** felirata „Scramble Collage" / **Véletlenszerű kollázs**, a
> **menütételé** „Scatter Pictures" / **Képek szétszórása**. Nem
> elírás — a két erőforrás külön szöveget tart.

**Két almenü:**

- **Szegély módosítása** (`0x00734260`): `Border::ID_COLLAGE_BORDER_0`
  „Egyik sem" · `_1` „Fehér szegély" · `_2` „Polaroid fényképezőgép".
- **Forgatás igazítása**: `Rotate::ID_COLLAGE_ALIGN_0/90/180/270` —
  „0 fok" · „90 fok" · „180 fok" · „270 fok".

**Bizonyítottsági fok: megerősített** (a menüépítő függvények
sztringjeiből és a `stringres` EN↔HU táblájából).

---

## 7. Az oldalformátum-lista

A `format_menu` **ugyanazt a listaépítőt** használja, mint a szerkesztő
vágóeszköze: `0x007cc990` (8140 bájt, egyetlen hívó: `0x007cae10`).
`Property maxrows 0` — a lenyíló nem korlátozza a sorok számát.

A tételek, sorrendben, a kódból kiolvasott arányokkal:

| kulcs | felirat | leírás | arány (h × sz) |
|---|---|---|---|
| `Manual` | Manual | — | — |
| `5x8m` | 5 x 8 | — | 8 : 5 * |
| `9x13m` | 9 x 13 | Small print | **13 : 9** |
| `10x15m` | 10 x 15 | Large print | **15 : 10** |
| `Crop13x18m` | 13 x 18 | — | 18 : 13 * |
| `Crop20x25m` | 20 x 25 | — | 25 : 20 * |
| `A4` | A4 | Full page | **297 : 210** |
| `4x6` | 4 x 6 | Small print | **6 : 4** |
| `5x7` | 5 x 7 | Large print | **7 : 5** |
| `FullPage` | 8.5 x 11 | Letter paper | **22 : 17** |
| `8x10` | 8 x 10 | — | 10 : 8 * |
| `A4PageCollage` | **A4 paper** / A4-es méretű papír | — | **297 : 210** |
| `Square` | Square | CD Cover | **1 : 1** |
| `Desktop4x3` | 4:3 | Standard screen | **4 : 3** |
| `Widescreen` | 16:10 | Widescreen monitor | **16 : 10** |
| `HDTV16x9` | 16:9 | HDTV | **16 : 9** |
| `WideFrame` | 5:3 | Widescreen Photo Frame | **5 : 3** |
| `CurrentDisplay` | Current display / Jelenlegi megjelenítés | — | a képernyő aktuális mérete |
| `CustomAspectRatios` | Custom Aspect Ratios | — | csoportcím |
| `AddCustomAspectRatio` | Add Custom Aspect Ratio… | — | a `customaspectratio.fen` párbeszéd |

A **vastagon** szedett arányokat közvetlenül a kódból olvastuk ki
(`push h; push w` az elem építése előtt). A `*`-gal jelölt négy tételnél a
számpár máshonnan érkezik; ott az arány a **feliratból** következik —
bizonyítottsági fok: **erős**, nem megerősített.

Az `A4PageCollage` („A4-es méretű papír") a **kollázsnak külön** tétel:
a lista két helyen is ad A4-et, más kulccsal és más felirattal
(`0x007cd488` és `0x007cdba4`).

A `delete_custom_aspect` (262, 314) 14×14-es kuka **az egyéni arányt**
törli a `Preferences\AspectRatios`-ból (`0x0083df40` → `0x007cb7b0`).

Az egyéni arány hibaüzenetei: `CustomAspectRatioDlg::AddError`,
`CustomAspectRatioDlg::ErrorTitle`.

---

## 8. A „Klipek" lap

A fül felirata **számot tartalmaz**: `collageUI::tab2_title` =
„Clips (%d)" / **„Klipek (%d)"** — a képernyőképen „Klipek (80)".

Három gomb, mind a lap tetején:

| gomb | hely | mit csinál |
|---|---|---|
| `getmoreclips` | (19, 60) 166×28 | vissza a könyvtárba |
| `addclips` | (214, 60) 28×28 | a kijelölt klipek felvétele (`0x0083b180`) |
| `deleteclips` | (247, 60) 28×28 | klipek törlése (`0x0083b590`) |

A lap többi részét a `solo` lista tölti ki: (17, 91) 247×311.

**A „További klipek" folyamata** (`0x0082dcec`): a Picasa átvált a
`panelroot/picasatab`-ra (a könyvtárra), és odarak egy
**„Vissza a kollázshoz"** gombot (`collagepanel::back_to_collage`).
A kollázs lapja közben nyitva marad.

**Bizonyítottsági fok: megerősített** a folyamatra és a feliratokra;
az `addclips`/`deleteclips` belső működése nincs kibontva.

---

## 9. A kimenet

### 9.1 Létrehozás

`0x0083ce90(this, asztali_háttérkép_e)`.

- Ha **egy kép sem maradt**: „Mentés mellőzve" (`collageUI::noimages_title`)
  + „A kollázs nem menthető, mert az összes képet eltávolították. Vegyen fel
  legalább egy képet, és próbálkozzon újra." (`collageUI::noimages`).
- **Asztali háttérképnél**, ha a kollázs oldalformátuma nem egyezik a
  képernyőével: **„Figyelmeztetés: eltérő formátumok"**
  (`collage::formatmismatch`), a `collage::formatwarning` szöveggel, és két
  gombbal: **„Beállítás ennek ellenére"** / **„Beállítás mellőzése"**.
  A szöveg maga ajánlja a megoldást: válaszd a „Jelenlegi megjelenítés"
  tételt az Oldalformátum menüből.

A folyamatjelző szövegei: „Kollázs létrehozása... inicializálás"
(`collage::initializing`) → „Kollázs létrehozása - %d%%"
(`collage::refining_format`) → „Kollázs létrehozása... leállítás"
(`collage::cancelling`) → **„A kollázs kész (kattintson ide)"**
(`collage::done`). A megszakítás megerősítést kér:
`il_CollageMakerCancel` „Megszakítja a kollázs létrehozását?" a
„Kollázs megszakítása" / „Megszakítás mellőzése" gombokkal.

A Többszörös exponálásnak saját folyamatszövege van:
`collage:multiexp_progtitle` „Képek egymásra helyezése" és
`collage:multiexp_progstatus_format` „%1$d / %2$d feldolgozva".

### 9.2 A lap bezárása és az újramentés — két külön kérdés

**Bezáráskor**, ha van mentetlen módosítás (`CCollageUI::ConfirmCloseTitle`
„Jóváhagyás…"): **Piszkozat mentése** / **Módosítások elvetése** / Mégse.
A piszkozat a „Kollázsok" albumba kerül.

**Mentéskor**, ha a kollázs egy korábban létrehozottból készült
(`CCollageUI::ConfirmTitle` „Lecseréli a meglévőt, vagy újat hoz létre?"):
**Meglévő cseréje** / **Új létrehozása** / Mégse.

A piszkozatra a könyvtárban külön magyarázó szöveg tartozik
(`projectutils::draft_collage`): „Ez a kollázs még nem készült el
teljesen…".

### 9.3 Hiányzó képek

| kulcs | mikor |
|---|---|
| `CollageUI::AllImagesMissing` | a kollázs egyik képe sem található → nem szerkeszthető |
| `CollageUI::SomeImagesMissing` / `ImagesMissing` | „%d kép nem található, ezért nem jeleníthető meg…" |
| `CollageUI::FileMissing` | „Nem található a(z) %s kollázsfájl" |
| `CollageUI::ReadError` | „Hiba történt a(z) %s kollázsfájl betöltése során" |
| `CCollageManager::LoadFailed` | „Nem sikerült a kollázs betöltése." |
| `CollageUI::OnSaveError` | „Hiba történt a kollázs mentése során." |

A kimeneti fájlnév töve: `il_collagefilename` = „collage" / **„kollázs"**.

---

## 10. Megőrzött beállítások

Mind a `Preferences` ág alatt, kulcsonként:

| kulcs | mit tárol | alapérték |
|---|---|---|
| `collage::theme` | a kollázs-típus kulcsa | **`picturepile`** (`0x0082b3d0`) |
| `collage::format` | az oldalformátum | `2` (`0x0082b07a`) — feltételes |
| `collage::orientation` | álló / fekvő | (`0x0083a1a0`) |
| `collage::shadows` | árnyékrajzolás | (`0x0082afb6`) |
| `collage::showcaptions` | képfeliratok | **1** (`0x0082b828`) |
| `collage::bgcolor` | a háttér színe | (`0x0082c4e0`) |
| `collage::autosave` | az automatikus mentés útvonala | — |
| `Preferences\AspectRatios` | az egyéni oldalarányok | — |

A `.tre` szerint a **`landscape`** gomb kap `Property setpressed 1`-et,
azaz az erőforrásban a fekvő az előre lenyomott állapot; a tényleges
kezdőérték a `collage::orientation` beállításból jön.

---

## 11. Elhagyott és holt elemek — amit NEM kell megépíteni

- **`savebutton`, `loadbutton`** — a parancskezelőben ott van a két ág
  (`0x0082d7df` → `0x0083a6b0`, `0x0082d855` → `0x0083a5b0`), de a
  `respack.yt` panelfájában **nincs hozzájuk vezérlő**. Fejlesztői
  maradvány.
- **`layer_up`, `layer_down`** — a parancskezelőben szerepelnek, de nincs
  mögöttük hívás, és a rajzuk (`#layer_up`, `#layer_down`) kikommentezve.
  A rétegsorrendet a `move_*` négyes viszi.
- **A háromgombos eszközpaletta** (`#tools_group` (86, 244) 149×32,
  benne `#movetool`, `#scaletool`, `#rotatetool` 30×22-es gombok és egy
  `#tools_label`) — **kikommentezve**. Egy korábbi terv, amiben eszközt
  kellett választani; a kiadott változat közvetlen manipulációt használ.
  **Ne épüljön meg.**
- **A Picasa 2-es kollázs-párbeszéd** szövegei még bent vannak:
  `IDS_COLLAGE_MAKER_DIALOG_TITLE` „Kollázs készítése",
  `IDS_CONFIRM_COLLAGE`, `IDS_CONFIRM_DESKTOPCOLLAGE`,
  `CollageType::bkoption1..4` (Háttérkép / Fehér / Szürke / Fekete háttér),
  `CollageType::locoption1..4` (Mentés háttérképként / Aktuális mappa /
  Képernyővédő képek mappája / Mappa kiválasztása),
  `CollageType::ePicturePile|ePictureGrid|eContactSheet|eMultiExposure`,
  `il_MakeCollageButton`, `LighthouseConfirm::MAKECOLLAGE?`.
  **Ez a RÉGI, egyszeri párbeszédablakos kollázs** — a 3.9-ben már a
  panel váltotta le. Aki ezekre a kulcsokra épít, a leváltott funkciót
  építi meg.

---

## 12. Ami nyitva marad

1. **Az `Alt`+vonszolás ága a `RingMoveHandler`-ben** (`0x00868f99`).
   Folytatás: `0x005121d0` (19 bájt, általános elérő), majd
   `0x009df680`, `0x009df290`, `0x0075c860`.
2. **A `CollageNodeHandler` 11. eseménye** (`0x00860ce7`): két csomópont
   adatait veszi elő (`0x00860e60`, `0x00860270`), és a `+0x44`
   vtable-slot 5-ét hívja a két pozícióval — **valószínűleg két kép
   cseréje** vonszolással, de ez **feltételes**.
3. **A képesség-maszk többi bitje** (1, 2, 3, 5, 7, 8, 12–16). A 0. biten
   függő `0x00831ac0` sincs kibontva.
4. **Az `addclips` / `deleteclips` belső működése** (`0x0083b180`,
   `0x0083b590`).
5. **A `collage_adapt` lépés** (`0x00868aa4`) — mi fut le a manipuláció
   végén.
6. **A négy `*`-gal jelölt oldalarány számpárja** (5x8, 13x18, 20x25,
   8x10) — a `0x007cc990`-ben a sztring **után** épül az elem.
7. **A vonszolás 10 képpontos küszöbe** (`0xcf3b28 = 10.0f`,
   `0x008606d0`) a `CollageNodeHandler` OLE-vonszolásához tartozik; hogy a
   gyűrűs mozgatásnak van-e saját küszöbe, nem néztük meg.

---

## 13. Amit KIZÁRTUNK

- **Nem** igaz, hogy a forgatás és a méretezés külön fogantyú vagy külön
  eszköz: **egy** fogantyú mindkettőt viszi, a `Ctrl`/`Alt` kapcsolja ki az
  egyiket (`0x00868870`, `0x0086888b`).
- **Nem** igaz, hogy a `snap_9` 270°-ot tárol: `−90.0f`-et
  (`0xcf50d0`). A „270 fok" a menü **felirata**.
- **Nem** igaz, hogy a témánkénti panelkülönbségek külön UI-kódból
  jönnek: egyetlen bitmaszk vezérli őket (`0x00831750`).
- **Nem** igaz, hogy a kikommentezett `#ring` / `#chicklet` rajzok
  halottak: a panelfából vannak kivéve, de a gyűrű a felhasználó
  képernyőképén ott van — ezek kódból rajzolt overlay-elemek. (A
  `#tools_group` viszont **tényleg** halott: ahhoz nincs kezelő.)
