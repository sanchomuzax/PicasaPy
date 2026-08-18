# A Kollázs funkció teljes működése (2026-08-17)

Ez a lap a **működést** írja le: mit csinál minden vezérlő, mi történik az
egérrel a vásznon, mikor melyik panelrész látszik, és mi kerül a lemezre.

A **geometria** (mind a 156 elem koordinátája és mérete) és a **feliratok**
(mind az 52, hivatalos magyarral) nem itt vannak, hanem a
`picasa-create-features.md` **1.10** szakaszában — a kettő együtt adja ki a
teljes képet. A **megvalósításhoz** ezen felül a
`kollazs-panel-ui-spec.md` kell: az az építési rajz (elemfa,
`objectName`-ek, méretezési törvény, vezérlő-API, teszt-szerződés). Az elrendezés-algoritmusok (a hat téma pakolói) ugyanott, az
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

A megfejtett bitek *(a 2026-08-18-i kör tizenegyre bővítette az eredeti
ötöt — a keresés a teljes kollázs-kódterületre ment, `0x00829000`+90 KB és
`0x0087a000`+72 KB)*:

| bit | ha 1 | hol dől el |
|---|---|---|
| 0 (`0x1`) | a **háttér-beállítások engedélyezve** (rádiógombok, háttérkép-doboz, színválasztó) | `0x00831932` → `0x00831ac0` |
| 1 (`0x2`) | oldalformátum-váltáskor lefut egy csomópontonkénti újraszámolás (`0x0087e960`) | `0x00839f07`, `0x0083a201` |
| 2 (`0x4`) | a **„Képek összekeverése"** gomb engedélyezve (ha ≥ 2 kép) | `0x0082fa0f` |
| 3 (`0x8`) | a **„Véletlenszerű kollázs"** gomb engedélyezve (ha ≥ 1 kép) | `0x0082fa60` |
| 4 (`0x10`) | a **kijelölés engedélyezett** (`select_all` aktív) | `0x008318ed` |
| 5 (`0x20`) | a képek **szabadon elhelyezhetők** — a `ringnode` létrejön, és a `collage::shadows` beállítás a modellbe kerül (`spec+0x28c`) | `0x008307ef`, `0x0083a512` |
| 7 (`0x80`) | a csomópont `+0x168` lebegőpontos mezője (elforgatás) él | `0x0083ad5f` |
| 8 (`0x100`) | a **darabszámfüggő alapméret** kiszámolódik (ld. 9.0) | `0x0082ca95`, `0x00831a6a` |
| 9 (`0x200`) | a **három képkeret-gomb** (`borders_group`) látszik; és `spec+0x37` = 1 | `0x008317f5`, `0x0082cb3a` |
| 10 (`0x400`) | a **térköz-csúszka** (`spacing_group`) látszik | `0x00831860` |
| 11 (`0x800`) | az **árnyék-jelölő engedélyezett** | `0x00831818` |

Ebből a hat témára:

| téma | keretek | térköz | árnyék | kijelölés | gyűrű | összekeverés | szétszórás | háttér |
|---|---|---|---|---|---|---|---|---|
| Képkupac | **igen** | nem | igen | igen | **igen** | igen | **igen** | igen |
| Mozaik | nem | **igen** | igen | igen | nem | igen | **nem** | igen |
| Képkockamozaik | nem | **igen** | igen | igen | nem | igen | **nem** | igen |
| Rács | nem | **igen** | igen | igen | nem | igen | **nem** | igen |
| Indexkép | **igen** | nem | igen | igen | nem | **nem** | **nem** | igen |
| Többszörös exponálás | nem | nem | **nem** | **nem** | nem | **nem** | **nem** | **nem** |

> **Ez magyarázza, amit a felületen látni.** Rácsba rendezett képeket nincs
> értelme „szétszórni" — csak a sorrendjüket keverni; az Indexkép rendezett,
> ott egyik sincs; a Többszörös exponálás pedig egymásra vetít, ezért ott
> sem kijelölés, sem háttérválasztás, sem árnyék nincs.

##### A maradék hat bit — 2026-08-18, második kör

A keresés ezúttal a **teljes `.text`-re** ment (8,4 MB): mintaillesztéssel
összegyűjtöttük az összes `mov r32,[r32+0x1c]` + `call r32` + bit-teszt
hármast. **39 találat**, ebből 29 valódi maszk-fogyasztó. Eredmény:

| bit | mit jelent | bizonyíték |
|---|---|---|
| **6** | a kollázs-csomópont `+0x219` jelzőjét 1-re állítja, és érvényteleníti (`\|= 7`) | `0x00860470` |
| **12** | **a téma megvalósítja a 9. vtable-slotot** | `0x0087e861` |
| **13** | a vászon-kezelő magától **`collage_adapt`-ot küld**, ha egy mérték a **2,0**-t (`0xc7d9d0`) nem lépi túl | `0x00886142` |
| **14** | **a `collage::shadows` beállítás ALAPÉRTÉKE** | `0x0082c6e9` |
| **15, 16** | **nincs fogyasztójuk sehol a `.text`-ben** — halott bitek | a teljes pásztázás |

**A 12. bit önmagát bizonyítja a vtable-ökből.** Ha áll, a kód meghívja a
téma `vt[0x24]`-ét (`0x0087e870`). Márpedig a 9. slot **csak** a
`CGridTheme`-nél és a `CFrameGridTheme`-nél valódi függvény
(`0x00881710`); a másik négy témánál a generikus üres tő
(`0x005baa00`) áll ott. Ez pontosan az a két téma, amelyiknél a 12. bit
be van állítva — a bit tehát **képesség-hirdetés**, nem viselkedés.

**A 14. bit a legkézzelfoghatóbb.** A beállítás-betöltőben
(`0x0082c4e0`) a sorrend: `collage::theme` → `collage::orientation` →
`collage::bgcolor` → `collage::showcaptions` → **`collage::shadows`**, és
az utolsó olvasás **alapértékét** a bit adja (`0x0082c6ee` → `0x0082c70c`).
Vagyis:

> **Az árnyékrajzolás alapból BE van kapcsolva a Képkupacnál és az
> Indexképnél, és KI a másik négy témánál.**
>
> Ez egyezik a felhasználó képernyőképével: Képkupac elrendezésnél az
> „Árnyékok rajzolása" jelölő be van pipálva.

**A 6. bit** a `+0x219` általános yt-csomópont-tulajdonságot állítja. A
mező a keretrendszerben sok panelen ugyanezzel a mintával („ha más,
érvénytelenít, aztán beállít") íródik. **Hogy pontosan mit kapcsol, nem
megállapított** — de a helye ezzel megvan.

*2026-08-18-i kiegészítés (a kérdés továbbra is NYITOTT, de szűkült):* a
teljes `.text` pásztázása szerint a `+0x219`-nek **mindössze 30
érintője** van, és a keretrendszerben **egyetlen olvasója**:
`0x009e2aa5`, a `0x009e2a60` (3207 bájt) függvényen belül. Ez a rutin a
csomópont **gyerekein megy végig** (`[ebx+4] >> 1` elemszám), és a
`+0x219` **egy külön, gyerekenkénti ágat kapcsol be** — ha a jelző 0, az
egész ág kimarad (`je 0x9e2bc4`). A hívói (`0x009e16d0`, `0x00a54b70`) a
`UITransitions` / `UIProfiling` beállításokat kezelő rétegben ülnek. A
mezőt az általános yt-csomópont-konstruktor (`0x009dd800`, `0x009dda0b`)
nullázza a testvér-jelzőkkel (`+0x205`…`+0x217`) együtt.

**Amit ez kizár:** a 6. bit **nem** szövegelrendezési kapcsoló (ez a lap
korábbi feltevése volt, és nem igazolódott) — a gyerek-bejárás egy
általános megjelenítési ága. **Nem blokkolja a megvalósítást.**

Teljes bitlista témánként, hogy a folytatás ne kelljen újraszámolni:

| téma | beállított bitek |
|---|---|
| `picturepile` | 0, 1, 2, 3, 4, 5, 7, 8, 9, 11, 13, 14, 15, 16 |
| `picturegrid`, `framegrid` | 0, 2, 4, 6, 10, 11, 12 |
| `regulargrid` | 0, 2, 4, 6, 10, 11 |
| `contactsheet` | 0, 4, 8, 9, 11, 14 |
| `multiexp` | 8 |

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

**Bizonyítottsági fok: megerősített** a maszkokra és a 0/2/3/4/9/10/11
bitre. A **7.** bit jelentése („elforgatás") **erős**, nem megerősített: a
`+0x168` mező azonosítása a környező kódból következik. Az **1.** és az
**5.** bit hatása megerősített, a *célja* feltételes.
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

A módot a specifikáció **`+0x2c`** mezője tartja, és a beállító
(`0x008364a0(mód, b1, b2)`) így működik:

```
spec[0x2c] = (Preferences\collage::avgcolor != 0) ? 0 : mód
spec[0x34] = b1
spec[0x35] = b2
```

Vagyis az **átlagszín-beállítás felülír mindent**: ha be van kapcsolva, a
mód **0** lesz, akármit kért a hívó. A rendes út `mód = 1`, `(1, 1)`
paraméterrel hívja; a **Többszörös exponálás** viszont `mód = 2`,
`(0, 0)` paraméterrel, és mellé `spec[0x36] = 1`-et ír
(`0x0082cafc`–`0x0082cb1a`). Ez a saját, külön háttérkezelése — ezért nincs
neki háttér-beállítása a panelen (0. bit).

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

### 3/b Az átlagszín NEM menet közben számolódik — adatbázis-mező (2026-08-18)

A „képek átlagszíne" háttér értékét a kollázs **nem számolja ki**: egy
**adatbázis-tulajdonságot olvas ki** `"avgcolor"` kulccsal, ugyanazzal a
hívással két helyen —

```
0x006a4cd0( adatbázistábla + 0xf20, kulcs, "avgcolor", &kimenet )
```

a végleges renderelőben (`0x0087e216`) és a csomópont-építőben
(`0x0087c067`). A tábla az alkalmazásobjektum `+0x2bc → +0xf20`
mezőjén ül; ugyanezt a kulcsot a beállítás-/adatbázis-réteg
(`0x00425f60`, 12 452 bájt) kezeli a `moviestart`, `geoview` és társai
mellett — vagyis **képenként tárolt, indexeléskor kiszámolt attribútum**.

**Ami ebből következik a megvalósításra:** az eredeti pontos átlagszíne a
`.picasa.ini`-ből **nem állítható elő** — az érték a Picasa saját
adatbázisában élt. Nekünk **saját átlagot kell számolnunk**, és ki kell
mondani, hogy ez **nem bitre azonos** az eredetivel. A számítás módja
(mintavétel, súlyozás, színtér) **nem megfejtett**, mert nem a kollázs
kódjában van.

**Bizonyítottsági fok:** hogy a kollázs **kiolvassa és nem számolja** —
**megerősített**. Hogy pontosan mi írja be és milyen képlettel —
**nyitott**, és a kollázson kívüli terület.

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

> ⚠️ **Helyesbítés (2026-08-18): a fenti négy koordináta a TERVEZŐI
> alapállás, nem a futásidejű hely.** Mind a négy csoport a
> `previewshadow` — vagyis **maga a LAP** — gyereke, és kényszerekkel
> tapad hozzá; a `respack`-beli abszolút x/y csak a tervezővásznon
> érvényes. A teljes kényszertábla:
>
> | csoport | kényszer | jelentés |
> |---|---|---|
> | `action_group` | `m_centerX` + `YConstraint 1, 0, -2` | a lap **fölött** 2 px-re, középen |
> | `rand_group` | `m_centerX` + `YConstraint 0, 1, 2` | a lap **alatt** 2 px-re, középen |
> | `z_order_group` | `m_centerY` + `XConstraint 0, 1, 2` + **`m_hidden`** | a laptól **jobbra** 2 px-re, függőlegesen középen |
> | `snap_rotation_group` | `m_centerY` + `XConstraint 1, 0, -2` + **`m_hidden`** | a laptól **balra** 2 px-re, függőlegesen középen |
>
> Két következmény: (1) a négy csoport **együtt mozog a lappal**, tehát
> oldalformátum- vagy ablakméret-váltáskor is a lap szélén marad;
> (2) a két oldalsó oszlop **alapból REJTETT** (`m_hidden`) — ezért nem
> látszik a felhasználó képernyőképén sem. A `move_up`/`move_down`
> ezen felül `m_autorepeat` (nyomva tartva ismétel), a `move_top`/
> `move_bottom` nem.
>
> **Bizonyítottsági fok: megerősített** —
> `referencia/tre-eroforrasok/collagepanel.tre` 13–24., 285–322. sor,
> a makrók jelentése `macros.tre` 11–83. sor.
>
> A panel **teljes elrendezés-törvénye** (mi fix és mi nyúlik, ha az
> ablak nem 800 × 534) a `kollazs-panel-ui-spec.md` **2.** szakaszában.

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

**Nincs vonszolási küszöb.** A gyűrűs mozgatás az első egérmozdulatra
elindul: a kezelőben **egyetlen** gyökvonás vagy távolság-összehasonlítás
sincs. A máshol emlegetett **10 képpontos** küszöb (`0xcf3b28 = 10.0f`)
**kizárólag** a `CollageNodeHandler` OLE-vonszolásához tartozik
(`0x008606d0`), a vásznon belüli mozgatáshoz nem.

**Az `Alt` billentyű külön ága** (`0x00868f99`, `GetAsyncKeyState(VK_MENU)`) —
2026-08-18-án kibontva:

```
csoport = GetSelectionGroup(node)          ; 0x005121d0 → node[0x244]
ha (csoport) {
    node->vt[1]()                          ; érvénytelenítés
    UnionGroupBounds(csoport, node)        ; 0x009df680 — a csoport
                                           ;   befoglaló téglalapját
                                           ;   (+0x178..+0x184) bővíti
    AddToSelection(node, csoport)           ; 0x009df290 — de a node MÁR
                                           ;   ebben a csoportban van,
                                           ;   ezért azonnal visszatér
    node->vt[2]()
}
n = NodeByName([ebx+0x20]); ha (n) 0x0075c860(n)   ; a csoport horgony-
                                                   ; csomópontját állítja
                                                   ; (csoport[0x24c])
```

**Amit ez kizár:** az `Alt` **nem másol** és **nem klónoz** — a teljes ágon
nincs foglalás, nincs új csomópont. (Ez volt a kézenfekvő feltevés, és
téves.)

#### Mit csinál valójában: a képet a kupac TETEJÉRE hozza

A `0x0075c860` a csoport **horgonymezőjét** (`+0x24c`) állítja:

```
csoport = node[0x244]
ha (csoport[0x24c] == 0) {
    ha (node == tömb[darab − 1])   csoport[0x24c] = 1     ; „nincs teendő"
    egyébként                      csoport[0x24c] = node  ; „ezt kell mozgatni"
                                   node.flags |= 7
}
```

A horgonyt a **`0x009dfde0(csoport)`** dolgozza fel: megkeresi a horgony
indexét a tömbben (`0x00a59000`), **a tömb végére mozgatja**, majd
`csoport[0x24c] = 0` (`0x009e0084`). Ugyanez a párosítás megvan a
`0x009dfbb0`-ban is, ott a `0x009dfde0` hívása a beállítás **előtt és
után** is látszik.

**A tömb a rétegsorrend, és az utolsó elem van legfelül.** Ez nem
feltevés, hanem levezethető: a `move_down` parancs
(`0x0083ab30(+1)` → `0x009dfc70` → **`0x009dfd60`**) a csomópontot a
**0. index felé** cseréli (`0x009dfd9c`–`0x009dfdaf`), és −1-gyel tér
vissza, ha már a 0. indexen áll. Tehát 0 = legalul, utolsó = legfelül.

> **Így az őrfeltétel kimondja a választ:** „ha a kép **már az utolsó**,
> nincs teendő". Egy művelet, aminél a *legfelső* elem a nincs-dolgunk
> eset, csakis **a tetejére hozás** lehet.

**Vagyis: `Alt`-ot nyomva tartva megfogni egy képet = a kép a kupac
tetejére ugrik, és onnan mozog tovább.** A húzás maga változatlan (5.2).

**Bizonyítottsági fok: megerősített.** Két független darab mondja
ugyanazt: az őrfeltétel („már utolsó → nincs teendő") és a rétegsorrend
iránya (`0x009dfd60`). *A futó eredetiben való próba ezek után nem
szükséges — 2026-08-18-án ez volt a lap utolsó, felhasználóra váró
kérdése, és lekerült a listáról.*

### 5.2/b Két kép cseréje vonszolással — MEGFEJTVE (2026-08-18)

A `CollageNodeHandler` **11. eseménye** (`0x00860ce7`) egy csomópontra
ejtés. Amit csinál:

```
tmp1 = masik_node.path      ; 0x00860e60 — sztringpár másolása
tmp2 = ez_a_node.path
masik_node.SetPath(tmp2)    ; 0x00860270
ez_a_node.SetPath(tmp1)
[ebx+0x44]->vt[5](masik.x, masik.y, ez.x, ez.y)
```

A `0x00860270(this, út)` a csomópont **`+0x48` fájlútvonal-mezőjét** írja
át, „piszkos" jelzéssel (`this[0x20] = 1`) és újratöltéssel
(`0x00860140`). Ugyanez a `+0x48` mező az, amit a „Megjelenítés és
szerkesztés" is olvas.

**Tehát: két képet egymásra húzva a kettő KICSERÉLŐDIK** — a képek
váltanak helyet, a keret, a méret és az elforgatás **marad**. A négy
koordinátával hívott `vt[5]` az animációt/értesítést viszi.

**Bizonyítottsági fok: megerősített.**

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

- `GetAsyncKeyState(0x11)` = **Ctrl** → `0x00868870`
- `GetAsyncKeyState(0x12)` = **Alt** → `0x0086888b`

> ⚠️ **Helyesbítés (2026-08-18): `GetAsyncKeyState`, nem `GetKeyState`.**
> A `0xc406f8` import neve a PE importtáblájából **`USER32.dll!
> GetAsyncKeyState`**. A különbség nem szőrszálhasogatás: a Picasa a
> módosítót a húzás **közben, folyamatosan** kérdezi (a pillanatnyi
> fizikai billentyűállást), nem az egéresemény pillanatában rögzíti.
> Tehát ha valaki húzás **közben** engedi el a `Ctrl`-t, a forgatás
> onnantól él. Ugyanez a `picasa-eger-es-kijeloles.md` 3. szakaszának
> megállapítása az egész felületre.

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
szöveg eltűnik (`0x009cd730`), és lefut a **`collage_adapt`** lépés
(`0x00868aa4`, ld. 5.5).

### 5.5 A `collage_adapt` lépés — MEGFEJTVE (2026-08-18)

A `collage_adapt` **nem függvényhívás, hanem egy névvel küldött parancs**:
a Picasa sztringet épít belőle (`0x00985ff0`, 13 karakter), üzenetobjektumba
csomagolja (`0x00591560`), és a csomópont `vt[0x70]` bejáratán küldi el —
**pontosan ugyanaz a mechanizmus, mint a helyi menük megnyitása**
(ott a név `collagenode_context_single` / `_group`).

A nevet a panel kezelője kapja el (`0x0082cb50`, `0x0082d40b`
sztring-összehasonlítás) és a **`0x0083d730`**-ra irányítja. Ez:

1. **Pillanatképet készít a specifikáció mezőiről** — a `+0x2c…+0x3c`
   blokkot átmásolja a `+0x40…+0x4c` árnyékblokkba (háttérmód, munkaméret,
   három jelző, alapméret).
2. Végigmegy az **összes csomóponton** (`[esi+0xe8]`, darabszám
   `[+0x19c] >> 1`), és a befoglaló téglalapjuk szélességét
   **`× 1/1024`**-gyel normalizálja (`0xcf3f68 = 0.0009765625`).
3. Meghívja a `0x00835380`, `0x008366c0`, `0x00837e40`, `0x00885fd0`
   rutinokat (újraépítés/újrarajzolás).

Küldi még a `CollagePreviewHandler` is (`0x008860e0`).

**Bizonyítottsági fok:** a mechanizmus és a pillanatkép **megerősített**;
hogy a lépés *célja* a kézi szerkesztés megőrzése egy későbbi
újrarendezésnél, **erős** következtetés.

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

**A vászon menüje** — az erőforrásneve **`collagenode_context_document`**
(`0x0082d37e`), a tételeit a `0x007348f0` építi. **Négy** tétel:
Az összes kijelölése · Az összes kijelölés megszüntetése ·
Képek összekeverése (`Shuffle Pictures`) ·
**Képek szétszórása** (`Scatter Pictures`).

> ⚠️ **Ugyanannak a parancsnak két felirata van.** A `rand_placement`
> **gomb** felirata „Scramble Collage" / **Véletlenszerű kollázs**, a
> **menütételé** „Scatter Pictures" / **Képek szétszórása**. Nem
> elírás — a két erőforrás külön szöveget tart.

> ⚠️ **A vászon-menü a Többszörös exponálás témánál EL VAN NYOMVA**
> (2026-08-18). A kezelő (`0x0082d3af`–`0x0082d3d0`) lekérdezi a téma
> kulcsát, és `multiexp` esetén más ágra ugrik — nem nyitja meg. Ez
> független megerősítése a képesség-maszk 4. bitjének (`multiexp` →
> nincs kijelölés): két külön kódút mondja ugyanazt.
>
> A menü-erőforrások teljes leltára (mind a tizenhat, felületrészenként) a
> [`picasa-eger-es-kijeloles.md`](picasa-eger-es-kijeloles.md) **4/f**
> szakaszában.

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

**Mind a tizenhét számpár a kódból van** *(2026-08-18: a `*`-gal jelölt
négy is)*. Kétféle írásmód van rá: a leírással rendelkező tételeknél
`push h; push w` az elem építése előtt, a leírás nélkülieknél viszont
`mov [esp+0x20], w` és `mov [esp+0x24], h` **a sztring után** — ezért
maradtak ki az első körből. Az értékek:
**5 × 8** (`0x007ccd2b`), **13 × 18** (`0x007cd190`),
**20 × 25** (`0x007cd316`), **8 × 10** (`0x007cda22`) — vagyis pontosan
annyi, amennyit a felirat mond. **Bizonyítottsági fok: megerősített.**

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

> ⚠️ A `.tre` **statikus** fülcímkéje (`collagepanel/tab2-label`) magyarul
> „**Képek**" — ez egy MÁSIK erőforrás, és gyakorlatilag sosem látszik:
> a `0x0083b890` frissítő (négy hívó: `0x00830f30`, `0x00831e10`,
> `addclips`, `deleteclips`) a „Klipek (%d)" formátummal felülírja.
> A látható felirat a képernyőkép szerint is „Klipek (N)". *(A két
> erőforrás léte megerősített; hogy a négy hívó közül melyik fut pontosan
> a panel megnyitásakor, erős.)*

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

**A két gomb belső működése** *(2026-08-18)*:

- **`addclips`** (`0x0083b180`): a klip-lista **kijelöléséből** dolgozik
  (`[panel+0x124]` → `0x007166c0`); ha üres, azonnal kilép. A felvétel egy
  **zárral védett** szakaszban fut (`[panel+0x218]` őrszerkezet,
  `GetCurrentThreadId` + rekurziószámláló `+0x24`, belépés/kilépés a
  `0xc4055c` importon át), és a kiválasztott elemeket a kollázs
  csomópont-tömbjéhez (`+0x4c`) fűzi.
- **`deleteclips`** (`0x0083b590`): ugyanennek a párja, eltávolítással.
- **Mindkettő ugyanazzal zárul:** `0x0083b890` — ez **frissíti a fül
  feliratát** a „Klipek (%d)" formátummal
  (`collageUI::tab2_title` → `collagepanel/tab2-label`). Vagyis a fülön
  látszó szám a klipek tényleges darabszáma, minden felvétel/törlés után
  újraírva.
- Az `addclips` ezen felül meghívja a `0x0082fa00`-t (a két
  véletlenszerűsítő gomb engedélyezésének újraszámolása — ld. 2., 2./3.
  bit) és a `0x008320d0`-t (újrarendezés).

**A zár típusa** *(2026-08-18)*: valódi **`CRITICAL_SECTION`** —
a `0xc4055c` import a PE-táblából `KERNEL32.dll!EnterCriticalSection`,
és a `[panel+0x218]` szerkezet `+0x28`-as offszetjén ül. Köré a Picasa
**saját újrabelépés-őrt** épít: `GetCurrentThreadId` (`0xc40284`) a
`+0x20`-ban, és ha ugyanaz a szál lép be újra, csak a `+0x24`
számlálót növeli (`0x0083b1cf`) — a kritikus szakaszba nem lép be
másodszor.

**Bizonyítottsági fok: megerősített** — a folyamat, a feliratok, a záró
lépések és a zár típusa is.

---

## 9. A kimenet

### 9.0 A modell számai — a kollázs 1024 egység széles (2026-08-18)

A `collage_adapt` (5.5) és a beállítás-frissítő (`0x0082c9a0`) együtt
elárulja, milyen egységekben gondolkodik a kollázs.

**A lap belső szélessége 1024 egység.** A csomópontok szélességét a
`0x0083d730` `1/1024`-gyel szorozza (`0xcf3f68 = 0.0009765625`), az
alapméretet pedig `× 1024`-gyel állítja elő. Nem képpont: **normalizált
lapkoordináta**.

**A képek alapmérete a darabszámból jön.** `0x0082c9a0`, `n` = a képek
száma:

```
ha n <= 1:  s = 1.0
egyébként:  s = 1 / sqrt( sqrt(n) − 1.0 )        ; 0x0082ca29–0x0082ca4d
            ha s > 1.0: s = 1.0
ha (téma_maszk & 0x100):                          ; 8. bit
    spec[0x3c] = (egész) ( s × 1024.0 × 0.33 )   ; 0xcf4218, 0xcf46c0
egyébként:
    spec[0x3c] = 0
```

Vagyis **egyetlen kép a lap szélességének 33%-át kapja**, és onnantól a
`1/sqrt(sqrt(n)−1)` görbe szerint zsugorodik: 10 képnél ~0,68-szoros,
100 képnél ~0,33-szoros. A 8. bit miatt ez **csak a Képkupacra, az
Indexképre és a Többszörös exponálásra** vonatkozik — a rácsos témák a
pakolóból kapják a méretet.

**A munkafelbontás a darabszámmal lépcsőzik.** Ugyanitt, `spec[0x30]`:

| képek száma | `spec[0x30]` |
|---|---|
| ≤ 99 | a `0xd35808` globálisból (**2276**, nulla felé csonkolva) |
| 100 – 199 | **256** |
| 200 – 349 | **128** |
| ≥ 350 | **64** |

(Küszöbök: `0x63`, `0xc7`, `0x15d` a `0x0082c9d2`, `0x0082c9ee`,
`0x0082c9fc` címeken.) Ez az, ami miatt a nagy kollázsok az eredetiben nem
fulladtak meg: **350 kép fölött már csak 64 képpontos változatokkal
dolgozik**.

**A `spec[0x30]` tényleg a kért képméret** *(2026-08-18)*. A
`0xd35808` globális **konstans** — a `.text` mind a 15 hivatkozása
`fld`, egyetlen írás sincs —, és **nem csak a kollázs használja**:
ugyanez a szám megy át egész számra csonkolva a **miniatűr-**
(`0x00568e4a`) és a **filmkészítő** (`0x005e8c9a`) ágban is, mindkét
helyen közvetlenül **argumentumként** egy kép-lekérő hívásnak, a
kép objektuma (`+0x4c`) mellé. Vagyis egy **alkalmazás-szintű
„legnagyobb kért képélhossz"**, amit a kollázs a darabszám szerint
levisz 256 / 128 / 64-re.

**Bizonyítottsági fok: megerősített** a képletekre, a konstansokra és a
küszöbökre; **erős** arra, hogy a `spec[0x30]` jelentése a forrásképektől
kért képpontméret.

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

### 9.1/b A kimeneti fájl TELJES törvénye — hova, milyen néven, hogyan (2026-08-18)

**A Picasa a kollázs mentésekor SOHA nem kérdez fájlnevet vagy mappát.**
Ez nem hiányzó funkció, hanem bizonyított tervezési döntés: az egész
EXE-ben egyetlen fájldialógus-csomagoló van (`0x009b16f0`, ez hívja a
`GetSaveFileNameW`/`GetOpenFileNameW`-t), és a kollázs-alrendszer
(`0x008?????` tartomány) **egyetlen függvénye sem hivatkozik rá** (a
teljes xref-tábla negatív). A felhasználó a Létrehozás gombot nyomja meg,
minden más automatikus.

#### A két mentőfüggvény és hívóik

| út | hívási lánc |
|---|---|
| **Kollázs létrehozása** / **Asztali háttérkép** | `sharebutton`/`makedesktop` → `0x0082d570` → `0x0083ce90` → **`0x0083ba60`** (2887 bájt) |
| **Piszkozat mentése** (a lap bezárásakor) | `cancelbutton` → `0x0082c0a0` → **`0x0083c5b0`** (2260 bájt) |

Mindkettő ugyanazt a név- és hely-törvényt követi; a különbségeket a
végén adjuk meg.

#### 1. A célmappa: `<Képek>\Picasa\<Kollázsok>` — a mappanév HONOSÍTOTT

Mindkét mentő (és a `CCollageManager::CollagesFolder` segéd,
`0x0068a6a0`) így építi az utat:

```
<a Picasa képmappája>            ; 0x9966a0 → a saját "Picasa" gyökér
  + "Picasa"                     ; 0xc7f0fc (fix, NEM honosított)
  + stringres("CCollageManager::CollagesFolder")   ; 0x9ae560
                                 ; EN "Collages" → HU "Kollázsok"
```

A mappanév tehát **erőforrásból jön, nyelvenként más** — a magyar
Picasa `…\Picasa\Kollázsok`-ba ment. *(Élő bizonyíték: a tulajdonos
NAS-án `/mnt/photo/Picasa/Kollázsok` — és az angol korszak
`…\Picasa\Collages` mappája is ott van mellette.)* A mappa
`.picasa.ini`-jébe a Picasa `P2category=Projects (internal)` sort ír —
ettől jelenik meg az album a **Projektek** gyűjtőben.

#### 2. A fájlnév: a FORRÁSMAPPA CÍME, nem „kollázs"

A név kiválasztása (mindkét mentőben azonos, pl. `0x0083c7b0`–`0x0083c83c`):

1. **Ha egy korábban mentett kollázst szerkesztünk újra** (állapot
   `[obj+0x14] == 3`, és a neve nem „autosave"): a név a kollázs saját,
   adatbázisban tárolt címe (`[obj+0x16c]`), a cél pedig az **eredeti
   útvonala** (`[obj+0x13c]`) — a „Meglévő cseréje" válasz esetén.
2. **Új kollázsnál**: `0x0087db30` — az **éppen nyitott mappa/album
   címét** kéri le az adatbázisból (a nézet `[+0xeac]→[+0x3c0]`
   azonosítójával, a `vt[0x48]+0x18` cím-lekérdezővel). *(Élő bizonyíték:
   a NAS-on a kollázsfájl neve „2010-08-01 Sátor alkatrész.jpg" — pontosan
   a forrásmappa címe.)* A `0x0087db30` a mappa **dátumát is** lekéri és
   formázza (`ytDateTime::Format2`), de a fájlnévhez a hívó ezt NEM
   használja fel.
3. **Tartalék**: ha a cím üres vagy használhatatlan, a tő a
   `stringres("il_collagefilename")` = EN „collage" / HU **„kollázs"**
   (`0x0083c7d7`).
4. **Tisztítás**: `0x009946f0` — szóközök és pontok levágása a szélekről,
   és védelem a DOS-eszköznevek ellen (`aux`, `con`, `nul`, `prn`).

#### 3. Ütközéskor számozás: `%s%lu` — szóköz NÉLKÜL

Az egyedivé tétel a `0x00993030`: ha a `név.jpg` létezik, sorban
`név1.jpg`, `név2.jpg`, … A formátum szó szerint **`"%s%lu"`**
(`0xcd8d5c`) — a tő és a szám között **nincs szóköz, nincs zárójel**.
Legfeljebb 4096 próba (`0x009930d2`, `cmp ebx, 0x1000`). *(Élő
bizonyíték: a NAS-on „…Exp test.jpg" mellett „…Exp test1.jpg".)*

#### 4. Atomi írás: tmp-fájlok, átnevezés — előbb a `.cxf`, aztán a `.jpg`

1. Ideiglenes nevek a `0x009a40d0`-ból: `"%.4u%.4u%s"` —
   `GetCurrentThreadId()` + egy második számláló (erős feltevés:
   `GetTickCount`) + a `.jpg.tmp` / `.cxf.tmp` utótag; létezés-ellenőrzés
   `GetFileAttributes`-szel.
2. A **JPEG** a tmp-be íródik a `0x009d6010`-zel, a paraméterblokk
   `{1, 4, 0x5a}` — a harmadik mező a **90-es JPEG-minőség**
   (`0x0083c14b`; az automentés 640×480-as helykitöltője ugyanígy,
   de `0x55` = 85-tel készül, `0x0068a7f6`).
3. A **`.cxf`** (a szerkeszthető specifikáció) ugyanazzal a névtővel,
   ugyanabba a mappába íródik (`0x00834700` írja a tmp-be).
4. Átnevezés a véglegesre (`0x00994400`, paraméterei `(tmp, végleges,
   1, 5)`): **előbb a `.cxf`** (`0x0083c2e3`), **aztán a `.jpg`**
   (`0x0083c31b`) — ha a spec-írás elhasal, nem marad árva JPEG.
5. A kész JPEG-re a Picasa **rárakja a `FILE_ATTRIBUTE_TEMPORARY`
   (0x100) attribútumot** (`GetFileAttributes` → `or 0x100` →
   `SetFileAttributes`; végleges mentés: `0x0083c3b8`–`0x0083c3d1`,
   piszkozat: `0x0083cda5`, helykitöltő: `0x0068a81f`). A TÉNY
   megerősített; a *célja* nem megállapított (nyitott kérdés).

#### 5. Ami a mentés UTÁN történik — ez is a törvény része

A **végleges** mentés (`0x0083ba60`) záró lépései sorban:

1. az új JPEG indexelése a `indexonlyreadonly` paranccsal (`0x0083c404`);
2. miniatűr-/adatbázis-munka (`0x0088b0a0`, `0x008390e0`);
3. **a kollázs-lap magát zárja be**: a panel „Bezárás" gombját nyomja
   meg programból (`0x009cd8a0(panel, "collagepanel/cancelbutton")`),
   előtte `[panel+0x18] = 1` — a mentetlen-módosítás kérdés **elnyomva**;
4. **`locate` parancs az új fájlra** (`0x0083c509`) — a könyvtár
   **odaugrik a kész kollázshoz** a Kollázsok albumban.

A **piszkozat**-mentés (`0x0083c5b0`) ehhez képest: `indexonly`-val
indexel (nem readonly), **nem** zárja a lapot és **nem** ugrik sehova —
a hívó (`0x0082c0a0`) zárja a lapot a maga útján.

A `0x0083ce90` (Létrehozás-belépő) a mentés ELŐTT: képhiány-üzenet
(9.1); asztali háttérképnél formátum-összevetés a képernyővel
(`GetSystemMetrics(0/1)`, oldalarány-hányadosok egészosztásos
összehasonlítása, `0x0083cf3d`–`0x0083cf5b`); a függőben lévő
„CollageAutosave" háttérfeladat törlése (`0x9b3950` név szerinti keresés
→ `0x97ae70` leállítás); és a renderelés felső mérete: **0x1400 = 5120**
egység két példányban (`0x0083d050`) megy tovább a mentőnek — a kész
JPEG hosszabbik oldala legfeljebb 5120 képpont *(erős; a pontos
felhasználását a renderelőben nem követtük végig)*. Siker után
`0x008421a0`: az automentés-állapot takarítása (`collage::lastautosave`).

#### 6. Az „Asztali háttérkép" második fele: `picasabackground.bmp`

A kollázs a Kollázsok albumba **ugyanúgy elmentődik**; a háttérképpé
tétel a kész-értesítés kezelőjéből (`0x0088a020`, itt él a
`collage::done` „A kollázs kész (kattintson ide)" szöveg is) hívott
**`0x0057aa10`**-ben történik:

```
<Képek>\Picasa\<stringres("CThumbUI::BackgroundsFolder")>   ; EN "Backgrounds" / HU "Hátterek"
  \picasabackground.bmp                                     ; BMP-be konvertálva
HKCU\Control Panel\Desktop\  →  Wallpaper, WallpaperStyle, TileWallpaper
SystemParametersInfo(SPI_SETDESKWALLPAPER)
```

A registrybe írt **három érték** (`0x0057acaf`–`0x0057ad76`, mind
`HKEY_CURRENT_USER` = `0x80000001`):

| érték | tartalom |
|---|---|
| `Wallpaper` | a `picasabackground.bmp` teljes útvonala |
| `WallpaperStyle` | **`"0"`** (`0xc7fe6c`) |
| `TileWallpaper` | **`"0"`** (ugyanaz a sztring) |

> **A `0` / `0` páros a Windowsban azt jelenti: KÖZÉPRE, nyújtás és
> mozaik nélkül.** Ez magyarázza meg, miért van egyáltalán
> „Figyelmeztetés: eltérő formátumok" (9.1): a Picasa **nem nyújt** — ha a
> kollázs oldalformátuma nem a képernyőé, a kép középen marad, körülötte
> csíkkal. Ezért ajánlja a figyelmeztetés szövege pont a „Jelenlegi
> megjelenítés" oldalformátumot. A két lelet egymást igazolja.

**Bizonyítottsági fok az egész 9.1/b-re: megerősített**, kivéve ahol
jelölve („erős": a tmp-név második számlálója; az 5120 pontos
szemantikája). A `FILE_ATTRIBUTE_TEMPORARY` célja **nyitott**.

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

## 9/b Az ÁRNYÉK rajza — a teljes paraméterkészlet (2026-08-18)

Eddig csak az „Árnyékok rajzolása" **kapcsoló** volt megfejtve (mikor
látszik, mikor kapcsol be magától, melyik témánál alapértelmezett) — az,
hogy az árnyék **hogyan néz ki**, nem. Most megvan, számokkal.

### 9/b.1 A két résztvevő

| osztály | hol jön létre | mi |
|---|---|---|
| `ShapeDraw<ShadowSampler>` (`0x00cbf4bc`) | **kétszer, azonosan**: a panelben (`0x0082b51f`) és a végleges renderelő útján (`0x0088a4de`) | a raszterizáló; a dokumentum `+0x274` mezőjén ül |
| `ytShadowNode` (`0x00cc4af4`) | csomópontonként, `0x0087b170` | maga az árnyék-csomópont |

A raszterizálót 100 bájtos foglalás hozza létre, a `0x00761720`
konstruktorral (alapértékek: `+4 = +8 = 256`, `+0xc = 0.0`), majd a hívó
**`+0xc = 60,0`**-ra és `+0x5c = 0`-ra állítja. A 60,0 csak **kezdőérték**:
az elrendezés minden menetben felülírja (ld. lent). Az árnyék rajzolása
`0x0082fdd0` — külön X és Y irányú lecsengés **szorzata** ad egy 0…255
alfát; ha a rámpa-tábla (`+0x5c`) nincs beállítva (a kollázsban nincs), a
lecsengés a beépített ág szerint megy.

### 9/b.2 A képlet — ezt kell megvalósítani

A csomópontonkénti árnyékot a `0x00888d02`–`0x00888d89` állítja elő. Legyen
`k` a rajzolt (kerettel együtt vett) kép **`+0x18` egész mezője**:

```
eltolás_x = 0.001 · k + 1.0          ; 0xcf3db0 = 0.001, 0xc7e328 = 1.0
eltolás_y = 0.002 · k + 2.0          ; 0xcf4120 = 0.002, 0xc7d9d0 = 2.0
elmosás   = 0.03  · k                ; 0xcf4dc8 = 0.03
átlátszatlanság = 0.6                ; 0xc7e304 = 0.6f
```

és ezekből az elrendezés (`0x0087b1e0`):

```
raszterizáló.sugár = elmosás · 8.0               ; 0xc7ea10 = 8.0
raszterizáló.alfa  = (egész)(átlátszatlanság · 256.0)   ; 0xcf39d8 = 256.0
                   = (egész)(0.6 · 256) = 153
befoglaló_téglalap += elmosás · 1.5   MINDEN élen  ; 0xd34128 = 1.5
```

Az eltolás **hozzáadódik** a csomópont eltolásához (`0x0087b411`:
`+0x278 → +0x1e4`, `0x0087b423`: `+0x27c → +0x1f0`) — vagyis az árnyék a
képhez képest jobbra-**le** csúszik, és a **függőleges eltolás pontosan
kétszerese a vízszintesnek**.

> **Három szám, amit meg kell jegyezni:** az árnyék **60 %-os** (alfa
> **153/255**), az eltolás **1 : 2 arányú** jobbra-le, az elmosás sugara a
> mérettel **lineárisan** nő (`0.24 · k`, mert `0.03 · 8`).

### 9/b.3 Ami NEM derült ki

A `k` (a csomópont `+0x18` egész mezője) **pontos jelentése nem
megállapított**. Amit tudunk: a rajzoló út ugyanezt a mezőt a `+0x14`
párjával együtt olvassa és **0,08-dal** szorozza (`0x008882bc`–`0x008882d4`,
`0xcf4df0 = 0.08`), tehát egy **méret-jellegű, előjel nélkül kezelt egész**
— erős a gyanú, hogy a kerettel együtt vett kép **képpontban mért
magassága**, de ezt nem bizonyítottuk. **A megvalósítás előtt ezt le kell
mérni** (golden-pár: eredeti Picasa-kollázs árnyékkal vs. a miénk) — a
képlet alakja megerősített, a bemenete nem.

**Bizonyítottsági fok:** a konstansok, a képlet alakja, az alfa-számítás,
az eltolás iránya és aránya, valamint a befoglaló-téglalap bővítése
**megerősített**. A `k` jelentése **feltételes**. Hogy a mi kimenetünk
ettől lesz-e az eredetivel egyező, **NINCS mérve**.

---

## 9/c A POLAROID-KÉPFELIRAT — doboz, szín, betűméret (2026-08-18)

A keret geometriája eddig is megvolt (1.9.5), a **feliraté** nem. A
felirat-csomópontot a `0x0087c820` építi; a `0x00839830` dönti el, hogy
egyáltalán kell-e (a **`collage::showcaptions` BE** *és* a csomópont
kerete **`polaroid`** — a `0x00839bef`–`0x00839d1c` háromszor is
összehasonlítja a keretnevet).

### A felirat-doboz — a polaroid-kerethez normalizálva

```
bal   = 0.098      jobb = 0.098 + 0.804 = 0.902     ; 0xcf4e18, 0xcf4e28
fent  = 0.792      lent = 0.792 + 0.188 = 0.980     ; 0xcf4e1c, 0xcf4e20
```

A doboz méretét a `0x0087c8ed`–`0x0087c903` adja (`0.804 × 0.188`, a
csomópont léptékével szorozva), a helyét a `0x009debd0(csp, 0.098, 0.792)`
(`0x0087c9b0`), a léptéket a `0x009deca0(csp, 1/S)` (`0x0087c9cb`).

> **A szám önmagát ellenőrzi.** A bal és a jobb margó **egyenlő**
> (0,098 – 0,098), az alsó 0,020. És a keret-geometriából (1.9.5) a fotó
> alsó éle négyzetes képnél `(1 + 0,0725) / 1,374 = 0,781` — a felirat
> pedig **0,792**-nél kezdődik, épp a fotó alatt. Két, egymástól
> független helyről számolt érték illeszkedik: ez erős megerősítés arra,
> hogy az olvasat helyes.

### Szín és betűméret

| mi | érték | cím |
|---|---|---|
| a szöveg színe | **ARGB `0xFF4A4A4A`** = RGB(74, 74, 74), sötétszürke — **nem fekete** | `0x0087c9fa` |
| a betűméret | `(egész)( magasság × 14 / 360 )` — azaz a referenciadoboz magasságának **3,89 %-a** | `0x0080c510`, `0xcf3d50 = 360.0` |
| elforgatás | 0 (`0x005ba590(csp, 0.0)`) | `0x0087ca78` |
| két logikai kapcsoló | mindkettő **1** (a szövegcsomópont `vt[0x38]` és `vt[0x2c]` bejáratán) | `0x0087ca4e`, `0x0087ca59` |

A felirat-csomópont neve `collagepanel/textclip_<sorszám>`
(`0xcc4ad8`), és `0x350` = 848 bájtos szövegcsomópont-osztály.

**Bizonyítottsági fok: megerősített** a dobozra, a színre, a
betűméret-képletre és a feltételre (showcaptions ÉS polaroid). A két
logikai kapcsoló **jelentése** (feltehetően középre igazítás és
sortörés) **nem megállapított** — csak az, hogy mindkettő 1.

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

## 12. A hét nyitott kérdés — 2026-08-18-i elszámolás

A lap első kiadása hét kérdést hagyott nyitva. A 2026-08-18-i kör
mindegyiket megnézte; **mind a hét lezárult** (az 1. egy második
menetben).

| # | kérdés | eredmény | hol |
|---|---|---|---|
| 1 | az `Alt`+vonszolás ága | **LEZÁRVA** — a képet a kupac **tetejére** hozza; klónozás nincs | 5.2 |
| 2 | a 11. esemény | **LEZÁRVA** — két kép **cseréje** vonszolással | 5.2/b |
| 3 | a képesség-maszk bitjei | **nagyrészt** — 5-ről **11**-re nőtt a megfejtett bitek száma; hat marad | 2. |
| 4 | `addclips` / `deleteclips` | **LEZÁRVA** | 8. |
| 5 | a `collage_adapt` lépés | **LEZÁRVA** — névvel küldött parancs → `0x0083d730` | 5.5 |
| 6 | a négy hiányzó oldalarány | **LEZÁRVA** — mind a kódból, a felirat szerint | 7. |
| 7 | van-e a gyűrűnek vonszolási küszöbe | **LEZÁRVA** — **nincs** | 5.2 |

**Ami tényleg nyitva maradt** *(a 2026-08-18-i második kör után már csak
három, és egyik sem igényel futó Picasát)*:

**Nyitott kérdések** *(a 2026-08-18-i kimenet-kör után)*:

1. mit kapcsol a képesség-maszk **6. bitje**? A helye megvan — a
   kollázs-csomópont `+0x219` tulajdonságát állítja (`0x00860470`), amit
   a keretrendszer a `0x009e2aa5`-nél olvas —, a jelentése nem. *(A
   `spec[0x30]` és az `addclips` zárja 2026-08-18-án lezárult, ld. 9.0
   és 8.)*
2. **mi a célja a `FILE_ATTRIBUTE_TEMPORARY`-nak** a kész kollázs-JPEG-en
   (9.1/b 4. pont)? A tény három helyen bizonyított, a szándék nem.
3. az **5120-as felső méret** pontos szemantikája a renderelőben
   (9.1/b 5. pont) — a konstans megvan, az útja a `0x0087dcd0`-n belül
   nincs végigkövetve.
4. az árnyék-képlet bemenete: a csomópont **`+0x18`** egész mezőjének
   jelentése (9/b.3) — a képlet megvan, a bemenet feltételes.
5. a felirat-csomópont **két logikai kapcsolójának** jelentése
   (`vt[0x38]`, `vt[0x2c]`, mindkettő 1) — 9/c.
6. az **`avgcolor` adatbázismező** előállítása (3/b) — a kollázson
   **kívüli** terület, az indexelőé.

---

## 13. Amit KIZÁRTUNK

- **Nem** igaz, hogy a forgatás és a méretezés külön fogantyú vagy külön
  eszköz: **egy** fogantyú mindkettőt viszi, a `Ctrl`/`Alt` kapcsolja ki az
  egyiket (`0x00868870`, `0x0086888b`).
- **Nem** igaz, hogy a `snap_9` 270°-ot tárol: `−90.0f`-et
  (`0xcf50d0`). A „270 fok" a menü **felirata**.
- **Nem** igaz, hogy az `Alt`+vonszolás **másolna** vagy **klónozna** egy
  képet: a teljes ágon nincs memóriafoglalás és nincs új csomópont
  (`0x00868fac`–`0x00868ffe`). Ez volt a kézenfekvő feltevés, és téves —
  valójában a **kupac tetejére** hozza a képet (5.2).
- **Nem** igaz, hogy a gyűrűs mozgatásnak lenne **elhúzási küszöbe**: a
  `RingMoveHandler`-ben egyetlen gyökvonás sincs. A 10 képpontos küszöb
  másé (`0x008606d0`).
- **Nem** igaz, hogy a `collage_adapt` egy közvetlen függvényhívás volna:
  **névvel küldött parancs**, ugyanazon a bejáraton, mint a helyi menük.
- **Nem** igaz, hogy a kollázs képpontban gondolkodna: a belső lapszélesség
  **1024 egység** (`0xcf3f68 = 1/1024`).
- **Nem** igaz, hogy a témánkénti panelkülönbségek külön UI-kódból
  jönnek: egyetlen bitmaszk vezérli őket (`0x00831750`).
- **Nem** igaz, hogy a mentéshez fájlválasztó tartozna: az EXE egyetlen
  fájldialógus-csomagolóját (`0x009b16f0`) a kollázs-alrendszer egyetlen
  függvénye sem hívja (teljes xref-tábla, negatív bizonyíték). A nevet és
  a mappát a program adja (9.1/b).
- **Nem** igaz, hogy a kimeneti fájl neve „kollázs.jpg" volna: a tő a
  **forrásmappa címe**; az „il_collagefilename" = „kollázs" csak üres cím
  esetén tartalék (9.1/b 2.).
- **Nem** igaz, hogy a kikommentezett `#ring` / `#chicklet` rajzok
  halottak: a panelfából vannak kivéve, de a gyűrű a felhasználó
  képernyőképén ott van — ezek kódból rajzolt overlay-elemek. (A
  `#tools_group` viszont **tényleg** halott: ahhoz nincs kezelő.)
