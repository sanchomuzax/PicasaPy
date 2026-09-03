# A specifikációk tartalomjegyzéke

**Ez a lap a belépési pont a `docs/specs/`-be.** Alább előbb a **valóban
nyitott kérdések** listája (ebből válasszon témát egy kutatói kör), majd a
spec-lapok témakörönként.

*(A lapok DARABSZÁMA szándékosan nincs kiírva: kézzel karbantartott
leltár-szám némán elavul — ezt a hibaosztályt a #1512 őre tiltja.
A 2026-09-02-i állapotban a kiírt „34" már 71 fájl mellett állt.)*

**A lenti „Nyitott kérdések" lista kézzel ellenőrzött**, nem gépi
szó-számlálás. Egy 2026-08-16-i átvilágítás kimutatta, hogy a
`Nyitva`/`dekódolatlan` szavak **kétharmada hivatkozás** egy máshol már
megválaszolt pontra — a gépi számlálás tehát háromszorosára fújta a
képet (pl. `filterdesc-registry.md`: 6 találat, **0** valódi nyitott
kérdés).

*Utolsó átvilágítás: 2026-08-16 (a második, tízkörös menet után).*

## 🔶 Nyitott kérdések — innen válassz kutatói kört

### [ui-audit-editor.md](ui-audit-editor.md) — 1 nyitott kérdés (a #2061)

⭐ **2026-09-03 — az effekt-csempe előnézetének betöltési lánca kimérve a képforrás-leíróig (#2061), de a leíró JELENTÉSE nincs meg.** A `FilterGridItemLoaderJob` (RTTI `0x00c874ac`) konstruktorára (`0x0050e7b0`) a **teljes `.text`-ben pontosan egy** hívás mutat: `0x005d7e2b`, a csempeépítő `0x005d7c20`-on belül; a futtató (`0x0050e8d0`) az `editpanel/fxpreview%d` elembe tölt. A job egy **16 bájtos leírót** kap (`0x005d7e1f`), aminek az alakja **{0, 0, [X+8], [X+0xc]}** — az első két mező **hard nulla** (`0x005d7c93`, `0x005d7c97`) —, ahol `X` a `0x00a67be0` visszatérése, a **szerkesztőpanel + 0x324**. A hozzáférő `[panel+0x264] != 0` esetén **újraépíti nulláról** a leírót (`0x00a67bfd`–`0x00a67c4e`). **NINCS MÉRVE:** hogy a `[X+8]`/`[X+0xc]` pár az ALAP fotót vagy a szerkesztési lánc tetejét azonosítja; ehhez a `panel+0x324` típusát és íróit kell megtalálni. A kör NEM következtetett a két nullából. **Az olcsóbb út a tulajdonosé:** egy képernyőkép, amin egy jól látható effekt már alkalmazva van — ezért a jegy `felhasználóra-vár`. Jegy: **#2061**.

### [picasa-menusor-csoportok.md](picasa-menusor-csoportok.md) — nincs nyitott kérdés

⭐ **2026-09-03 — a Szerkesztés menü TELJES szerkezete kimérve, és a visszavonás-kérdés LEZÁRVA (#1795).** A menüt ugyanaz a táblavezérelt függvény építi (`0x00559150`), mint az Eszközökét: a tábla `0x00d6db80`-on áll, **20 bájtos rekordokkal**, a **darabszám-konstans 14** (`push 0xe`, `0x00559c76`; gyerekmutató `push 0xd6db80`, `0x00559c7c`) = **11 tétel + 3 elválasztó**, tehát a csoportosztás **3 | 2 | 2 | 4**. A lap tartalmazza mind a 14 rekordot címmel, kulccsal, angol ÉS magyar felirattal, gyorsbillentyűvel és parancsazonosítóval (`0x9d39` Kivágás … `0x9c90` Kijelölés törlése). ⛔ **A #1774 „feltételes visszavonás"-hipotézise MEGDŐLT, két független mérésből:** (1) a feltöltő blokkban (`0x005598b2`–`0x00559c4c`) **pontosan 11** feltételes ugrás van, mind a felirat-feloldás `NULL`-ellenőrzése — állapotfüggő elágazás nincs; (2) az `eMenuEdit::ID_UNDO`/`ID_REDO` **literál a teljes `Picasa3.exe`-ben 0 alkalommal** fordul elő (ASCII és UTF-16LE), tehát halott erőforrás-bejegyzés. **Hol VAN visszavonás:** a szerkesztő panel gombján (`CFilterStackUI::undolabel`), a **Kép** menü `Undo All Edits` tételén, a szövegmező helyi menüjében (`Address::ID_UNDO`, a menüt a `0x007331e0` építi) és a mentés-visszavonó párbeszédben. **Melléklelet:** a lap „nem dönti el" listájáról a **mnemonikok** is lekerültek — a szövegtár 142 honosított mnemonikot ad, nálunk 144 menütételből 11-en van; jegy: **#2152**. Jegyek: **#1795** (lezárva), **#2151** (a hamis indoklás javítása), **#2152**.

⭐ **2026-09-03 — az Eszközök menü TELJES szerkezete kimérve (#1794).** A menüt **egyetlen** függvény építi (`0x00559150`, 15 495 b), és nem `AppendMenuW`-vel: az egész függvényben **két** Win32-hívás van, a menü egy `.data`-beli rekord-tábla (`0x00d6e678`…`0x00d6e9a8`). Az `eMenuTools::` névtér mind a **36** kulcsa itt szerepel. **A Kísérleti almenü darabszáma konstans `9`** (`0x0055c928`), a gyerek-mutatója `0x00d6e798` (`0x0055c91e`); a kilenc tétel a `0x0055c295`…`0x0055c4c9` blokkban épül: FTP-közzététel · **Fájlok másodpéldányainak megjelenítése** (`ID_DUPES`, a 2. helyen) · Keresés… ▸ (maga is almenü, **hat színnel**: Piros/Narancssárga/Sárga/Zöld/Kék/Lila, `0x0055c078`…`0x0055c1c8`) · Keresési eredmények mentése · Címke megjelenítése albumként · Útlevélkép · Üres online albumok törlése · **Adatbázis helyének kiválasztása** · Arcinformációk írása XMP-adatokba. A Feltöltés almenü 3, a Geocímke 4 tételes. ⛔ **A „Find Faces" felirat a TELJES szövegtárban nem létezik** — az arckeresés az eredetiben **nem menüparancs**, a miénk tudatos eltérés. A felső szint fedi a tulajdonos képernyőmentését, egy feltételesnek tűnő tétellel több (`ID_TOOLS_DOWNLOAD_FACES`). Megvalósítás (a duplikátum-kereső áthelyezése, a feliratok, az eltérés kimondása): **#2142**. Jegyek: **#1794** (lezárva), **#2142**.

### [picasa-lebego-ertesito.md](picasa-lebego-ertesito.md) — nincs nyitott kérdés

⭐ **2026-09-03 — a két animált sáv JELENTÉSE megvan, és a #2034 egyik következtetése MEGDŐLT (#2122).** A rajzoló **nem** a gyorsítótárazott `cella+0x88`/`+0xa0` értéket olvassa — **újra kiértékeli** a sávokat (`0x00658423`, `0x0065903b`, `0x006590b4` → `0x00655950` → az általános kulcskocka-kiértékelő `0x009e5e70`, a sávot `edi`-ben kapva). A skálázás adja meg a mértékegységet: `fild [popup+0x1c0]` × **B sáv** (`0x00659040`–`0x00659061`) és `fild [popup+0x1bc]` × **A sáv** (`0x00659069`–`0x0065908a`). A `popup+0x1b4` a **`notifier/cell1`** réteg rekesze, a rétegstruktúra `+8` mezője **szélesség**, a `+0xc` **magasság** (a fogantyú rajzolása bizonyítja, `0x0065879b`) ⇒ **`+0x1bc` = 247 px, `+0x1c0` = 45 px, `+0x1e4` = a `basedecrect` 21 px-e**. Független megerősítés: a kattintáskezelő a cella sorszámát `(egérY − 2) / [popup+0x1c0]` alakban számolja (`0x00657eb4`). ⇒ **az A sáv vízszintes eltolás cellaszélesség-egységben (a `−1,0` = −247 px), a B sáv függőleges eltolás cellamagasság-egységben (a cél a verembeli sorszám = sorszám × 45 px)** — tehát a becsúszás VALÓDI, és a cellák egymáshoz is **csúsznak**, nem ugranak. ⛔ **HELYESBÍTÉS:** a #2034 köre azt írta, hogy „a becsúszás-hipotézis megdőlt, mert a pozíciót a tick közvetlen `mov`-val írja" — a `mov` által írt érték épp a sáv-kiértékelőtől jön, és a `+0xb0`/`+0xb4` csak **változás-őr** (utolsó ismert pozíció), ami a popup vtable `+0x50` újrarajzolóját ébreszti. **Melléklelet:** a cellaelhelyezés a `0x00d678d4` bájton ágazik el, ami a **jobbról balra (RTL) elrendezés** jelzője — a `Preferences`/`RTL` beállításkulcsból töltve (`0x0098f8af`–`0x0098f8e1`), 114 hivatkozással. **Nálunk (mérve):** csak átlátszóság-animáció van (250/500 ms), `x`/`y` animáció sehol. Jegyek: **#2122** (lezárva), **#2157** (a csúszás megépítése).

⭐ **2026-09-03 — a cella jobb sávjának három rétegéről kiderült, hogy EGYIK SEM vezérlő (#2035).** Az **összecsukás** halott erőforrás: a `popup+0x13c` slotra a `0x00654800`–`0x0065AC00` tartományban (a `CNotifierPopup` és a `CBaseNotifier` MINDEN vtable-metódusa beleesik) **csak** a konstruktor (`0x00657046`) és a destruktor (`0x006572d3`) hivatkozik — **sosem rajzolódik ki**. A **fogantyú** kirajzolódik (`0x0065878e` → réteg-blit `0x009ab410`), de nem interaktív. **Miért lehetetlen a vonszolás:** az ablak üzenetkezelője (`0x00657d10`) pontosan **hat** üzenetet kezel — `WM_LBUTTONDOWN` (0x201), `WM_SIZING` (0x214), `WM_MOVING` (0x216), `WM_SETCURSOR` (0x20), `WM_CLOSE` (0x10), `WM_SHOWWINDOW` (0x18) —, és **nincs köztük `WM_MOUSEMOVE` és `WM_LBUTTONUP`**; a `WM_SETCURSOR` egyetlen kurzort tölt (`IDC_ARROW`, `0x7F00`). A kattintás **egyetlen** téglalapot vizsgál és **egyetlen** jelzőt állít (`cella+0x14`, `0x00657f13`); a három rétegre nincs külön találati vizsgálat. A lap tartalmazza mind a nyolc réteg slotját hivatkozás-számmal. Megvalósítás (a fogantyú kirajzolása, a komment pontosítása): **#2133**. Jegyek: **#2035** (lezárva), **#2133**.

⭐ **2026-09-03 — a két animált sáv TELJES ÁLLAPOTGÉPE mérve (#2122), benne egy eddig ismeretlen animációval.** A sáv-író (`0x006558b0`) hívási helyei **kimerítően** végigpásztázva: **pontosan kettő van**. Élő cellára képkockánként a cél (**−1,0** ; a cella **sorszáma**), **0,6 s** alatt (`0x00c7e304`); **elbocsátáskor** viszont (**0,0** ; **0,0**), **0,3 s** alatt (`0x00c7dcc8`, `0x00655c98`) — tehát **az eltűnés kétszer gyorsabb, mint a beállás**, és ez a 0,3 s eddig sehol nem szerepelt. Az elbocsátás egyben `cella+0x11 = 1`-et állít (a tick ezt nézi) és **nullázza a határidőt** (`+0xb8`). A kezdőállapot mindkét sávra **0,0**; a cella `+0x0c` mezője **−1,0** (ugyanaz a konstans, mint az A sáv célja). **NEGATÍV EREDMÉNY, mérve:** a `0x00654800`–`0x0065AC00` teljes tartományban (a `CNotifierPopup` és a `CBaseNotifier` MINDEN vtable-metódusa beleesik) a `cella+0x88`/`+0xa0` értékeket **semmi nem olvassa rajzoláshoz** — csak a legutolsó kulcskocka kiolvasása, két cella-másolás és a konstruktor. ⇒ a sávokat **nem az értesítő** fordítja képi mennyiséggé; a kulcskocka-rendszer általános (`0x009e6010`-nek **22** hívója van). **Nyitva:** melyik képi mennyiséget vezérlik és mit jelent a `−1,0` — **#2122**.

⭐ **2026-09-03 — az ANIMÁCIÓ ALAKJA MEGVAN, és EGYIK felkínált lehetőség sem volt jó.** A #2034 „becsúszás VAGY áttűnés" kérdésére a válasz a harmadik: a tick (`0x006575b0`) cellánként **két absztrakt skalársávot** animál kulcskockásan (`cella+0x80…0x94` és `+0x98…0xac`, 40 bájt/kulcskocka, az utolsó érték `[bázis + n·40 − 0x18]`). Az átmenet **hossza 0,6 s** (`0x00c7e304`, kiolvasva), a **görbe exponenciális** `u = 8·t` skálán (`0x0072df60` függvénymutató + `0x00c7ea10` = 8,0). Az egyik sáv célértéke állandó **−1,0** (`0x00cf3ed0`), a másiké a cella **sorszáma a veremben**. **A becsúszás-hipotézis MEGDŐLT:** a pozíciót (`cella+0xb0`/`+0xb4`) a tick **közvetlen `mov`-val** írja (`0x00657827`), tehát a képernyőn kívüli parkolóhely nem egy vízszintes animáció kiindulópontja. A lap „Elszámolás" táblájának 2. sora ✅-re váltott. **Nyitva:** mit vezérel a két sáv a rajzoló oldalon — **#2122**. Jegyek: **#2034** (lezárva), **#2122**.

### [filterdesc-registry.md](filterdesc-registry.md) — 1 nyitott kérdés (a #2125)

⭐ **2026-09-03 — a Glow maszképítője (`0x00bcc2e0`) TELJESEN kiolvasva, és a lépcsős képlet ROSSZ paraméterhez volt kötve (#2102).** A két 255-re vágott egész a **két blur-sugár**: `r_x = min(255, trunc(ceil((xblur−1)·0,5)·quality + 1))` és ugyanez `yblur`-rel — a két blokk azért néz ki egyformának, mert az elsőt egy `push ecx` (`0x00bcc3d4`) előzi meg, így ott az `[esp+0x88]` a bázis `[esp+0x84]`, azaz az `xblur`. ⛔ **HELYESBÍTÉS:** az előző kör a `ceil((s−1)/2)` képletet a **`strength`**-hez kötötte, és ebből azt jósolta, hogy a tag minden Glow-hívásra állandó 1 — **mindkettő megdőlt**. A `strength` valójában a `0x00bcbd90`-ben lép be **8.8-as fixpontos szorzóként**: `trunc(strength × 256)` (`0x00cf39d8` = 256,0), négyszer az `mm7`-be, mellette a `0x0100` (= 1,0) az `xmm7`-be és a `0x0080` (= 0,5 kerekítés) az `mm6`-ba. **A vágások mind kiolvasva** (`0x00bc52c0` + a hívó törzse): `glowalpha` **[0,1]** → bájt `trunc(a×255)`; `xblur`, `yblur` **[0, 253]** (`0x00cf0b4c` = 253,0f); `strength` **[0, 255]**; `quality` egész **[1, 15]** (alap 3). **A blur átváltója (`0x00bb89b0`) is teljesen kiolvasva** — zárt alakja `k = (p<255) ? 1 : 255/p`, `X = ((100+d) − d·k)/p`, `return (X>3) ? k : k·X/3` —, és **a gyakorlatban azonosság: minden filterdesc-beli Glow-értékre pontosan 1,0**, a képmérettől függetlenül. **Nálunk (mérve):** a `glimmer_ops.py` a nyers blurt szigmaként használja (`:575`) és a `strength`-et **[0,1]-re vágott** keverési súlyként (`:578`) — négy pontos eltérés. ⚠️ **A hatás NINCS mérve**, ezért a megvalósítási jegy MÉRÉSSEL kezdődik: **#2159**. Jegyek: **#2102** (lezárva), **#2159**.

⭐ **2026-09-03 — mind a HÁROM effekt-fül összevetve a csempe-táblával: az 1. fülön HÁROM téves kötés (#2141).** A tábla 36 rekordja pontosan a három eredeti fül 3×12-es rácsa, és a mi `EditorEffectsTab1/2/3.qml`-ünk **pozícióról pozícióra** ennek felel meg. **A 2. és a 3. fül mind a 24 csempéje egyezik.** Az 1. fülön három csempe **ugyanazt a hibát** követi el — a felirat az eredeti elsődlegesé, a hívás viszont másik szűrőt indít: „Élesítés" → `unsharp` (**Élesítés (régi)**) `unsharp2` helyett · „Filmszemcse" → `grain2` a `PicnikGrain` helyett · „Árnyalás" → `tint` (**Árnyalás (régi)**) a `PicnikTint` helyett. Kettőnél a hívott kulcs éppen az, amit az eredeti a **Shift** alá rejt ⇒ a felhasználó ma jelzés nélkül a „(régi)" változatot kapja. **Melléklelet:** a mi 7. (örökölt) fülünk bevezetője azt állítja, hogy ezek a szűrők „nem érhetők el a mai Picasában" — a lista első eleme, a `radtint` (*Sugaras árnyalás*) viszont **elérhető**: az 1. fül 12. csempéjén (`dir_tint`) a Shift hozza elő. Jegyek: **#2141** (hatóköre nőtt, a címe javítva), **#2146**, **#2148**.

⭐ **2026-09-03 — a csempe MÁSODIK szűrőjét a SHIFT kapcsolja be (#2141).** A csempe-tábla (`0x00c7e5a0`) hármasainak második mezője **nem passzív tartalék**: a fül felépülésekor a program egyszer lekérdezi a Shift állapotát — `push 0x10` (VK_SHIFT) → `call [0xc406f8]` = **`GetAsyncKeyState`** (a betöltési táblából feloldva: `0x00c406f8` → `0x00922efc`, hint 256) → `shr eax,0xf` / `and al,1` → `[panel+0x33a8]` (`0x005d7c91`…`0x005d7cc0`) —, és a csempeépítő ez alapján választ: Shift nélkül az elsődleges (`0x005d7d2e`), Shifttel a másodlagos (`0x005d7d70`), ha van (`0x005d7d78`). **Kilenc** csempének van másodlagosa: `unsharp2`/`unsharp` · `PicnikGrain`/`grain` · `PicnikTint`/`tint` · `glow2`/`glow` · `dir_tint`/`radtint` · `HeatMap`/`NightVision` · `Vignette`/`Matte` · `Pixelate`/`PicnikFocalPixelate` · `Border`/`RoundedEdges`; a maradék **27** mezője `NULL`. **Helyesbítés a #1869 köréhez:** a második mezőt „örökölt id"-nek nevezni pontatlan — négy felirata tényleg „(Old)", **öté viszont önálló effekt** (Radial Tint, Night Vision, Matte, Focal Pixelate, Rounded Edges). **Nálunk (mérve):** a `ShiftModifier`/`Qt.Shift` **egyáltalán nem fordul elő** az `EditorEffectsTab*.qml`-ben és a `ToolTile.qml`-ben — a funkció hiányzik. Jegyek: **#2141** (a kérdése megválaszolva), **#2146** (a Shift-ág megépítése).

⭐ **2026-09-03 — az effekt-csempe KÉK JELVÉNYE MEGFEJTVE (#1869): `mode="oneclick"`.** A parser (`0x008ff550`) a `mode` attribútumot egésszé fordítja (`0x00900490`: **`oneclick`→1**, `hard`→2, `effect`→4, `soft`→5, `tool`→6, `history`→7, más→0) és a `FilterDesc + 4`-be írja (`0x008ff847`); a csempeépítő (`0x005d7c20`) ezt olvassa (`CGenericFilter` vtbl `+0x14` = `0x008f6cc0`), `cmp eax, 1` (`0x005d7ec2`), és ezzel mutatja/rejti az `editpanel/fx%d_adorn` vezérlőt (`0x005d8108` → `[vtbl+0x6c]` / `[vtbl+0x68]`). Az „1" tehát **nem számláló és nem erőforrás-index**, hanem az `oneclick` mód enum-értéke. **Melléktermék:** az effekt-csempék TELJES táblája — `0x00c7e5a0`, **36 rekord × 12 bájt** (mai id + örökölt id), 12 csempe/fül ⇒ három effekt-fül; a lap tartalmazza mind a 36-ot. Ez oldja fel a „Filmszemcse nincs megjelölve" rejtvényt: annak csempéje a **`PicnikGrain`**-hez kötődik (`effect`), nem a `grain`/`grain2`-höz. **Nyitva:** a tulajdonos NEGYEDIK jelvényt látott a 2. effekt-fülön (`Invert`, `mode="effect"`) — ellentmondás, jegy **#2125** (`felhasználóra-vár`). A megvalósítás: **#2126** (nálunk ma az „alkalmazva" számláló kapcsolja, `EditorPanel.qml:352`). Jegyek: **#1869** (lezárva), **#2125**, **#2126**.

⭐ **2026-09-03 — a `GlowImageOperation` KEVERÉSE kimérve, és a `strength` LÉPCSŐSNEK bizonyult.** A kompozitálás (`0x00bb992d → 0x008f59d0 → 0x008f4780`) **közönséges source-over**, erősség-tag nélkül: `T = src·a + dst·(255−a)`, `out = (T + (T>>8) + 1) >> 8`; az SSE-konstansok kiolvasva (`0xcd0550` = 1, `0xcd0560` = 255), az alfa a FORRÁS képpont 4. bájtja. ⇒ **a `strength` nem keverési súly** — ezt a modellcsaládot (a `glimmer_ops.py:578`-at is) a mérés kizárja. A rajzoló argumentumlistája most a binárisból van (nem a Flash-analógiából): `(forrás, color, glowalpha, xblur, yblur, strength, quality, cél)`, és két meglepetéssel: a **`strength` natív alapértéke 0,0** (`fldz`, `0x00bb8eb5`), a `color` alfa-bájtja pedig **beégetve `0xFF`** (`0x00bb8e5f`). A `strength` a maszképítőben (`0x00bcc2e0`) **`ceil((s−1)/2)`** alakban lép be (`−1,0` a `0xc7e328`, `×0,5` a `0xc72150`; a `0x00529e10` = **`ceilf`**, a `0x00c12fd0` névtáblájával bizonyítva). **Ellenőrizhető jóslat:** a `filterdesc.xml` MINDEN Glow-hívására (1,1…1,5 és a Vignette/Matte `[1..2]` csúszkája) ez a tag **állandó 1** — ezért illeszkedik a Vignette-goldenre kalibrált modellünk. **Nyitva:** a `0x00bcc2e0` második fele (`0x00bcc438`-tól) — célzott dekompiláció kell. Jegy: **#2102**.

### [filters-decoded.md](filters-decoded.md) — nincs nyitott kérdés

✅ **2026-08-24 — az utolsó kérdés (a `FocalZoom` perem-módja) LEZÁRVA MÉRÉSSEL:**
a halmozás csak nagyít (`zoom ≥ 1`), ezért minden minta a képen belülre esik —
négy perem-mód **bitre azonos** kimenetet ad képen belüli fókuszpontra. A mai
`cv2.BORDER_REPLICATE` helyes. Melléklelet: a natív mag (`0x00bcf4b0`) igazolja a
`zoom_max_offset` és `zoom_sample_count` képleteinket. Jegy: **#1351**.

### [picasa-create-features.md](picasa-create-features.md) — 1 nyitott kérdés (a #1412)

⭐ **2026-09-03 (2.1 bővítés) — a 22 átmenet HIVATALOS MAGYAR neve.** A lap
eddig csak az **angol** neveket adta meg, és a **#432 sem** tartalmazta a
magyart — így a legördülő magyar felületen angolul jelent volna meg. A teljes
22 soros tábla most a lapon áll (`CTransitions::*`, `stringres-en-hu.tsv`).
⚠️ **Négy fordítás megtévesztő:** `wiperight` = **„Törlés"** (nem „…jobbra"),
`pushright` = **„Tolás"**, `circleout` = **„Kör"** — az alapirány rövid nevet
kap; és `timelapse` = **„Gyorsítás"**, nem „Időzített felvétel".
⚠️ **NE keverd össze a `CThemePrefs::` családdal** — az egy MÁSIK, **tíz**
elemű készlet (Sakktábla, Kollázs, Google Modulok…): *ha egy kör tíz
átmenetet talál, rossz családot néz.* **Új mérés:** a `makemoviepanel/rewind`
(**„Vissza a kijelölt diához"**) megjelenítése `0x0061681e`
(`[+0x210]=1`, `[+0x248]=0xff`); ⛔ **elvetett hipotézis:** az őrző globális
(`0xd67914`) **nem** szolgáltatás-kapcsoló, hanem a **felületi fa
gyökérmutatója** — egyetlen írója a keret-indító (`0x009c3a36`), és mind az
1712 olvasója `cmp …, 0` null-ellenőrzés. **NINCS MÉRVE**, mit csinál a gomb
kattintásra (az olcsó lánc kimerült). A fülek magyarul: **„Mozgófilm" ·
„Dia" · „Klipek"**. ⇒ **A `makemoviepanel` feltáratlan listája ÜRES: 5 → 0**
(globálisan 116 → 111); ezzel a **#2093** 3. pontjának négy elavult
felülbírálása is rendezve. Komment: **#432**.

⭐ **2026-09-01 — a #1412 egyik KORLÁTJA MEGDŐLT:** a jegy szerint „egy mintánk van (AI6)", de a `kollazs-golden/` **tizenegy** `.cxf`-je közt a **`regulargrid` (AI5) is egyetlen `scale`-t** használ (330) ⇒ **második adatpont**. Levezetve: a kizárt 300 és 359 az **oszlop-** és **sor-osztás**; az AI5-re pontos a megfelelés (`0,322266 × 1024 = 330`), az AI6-ra keresett tört **0,305664** — a felirat-sávot is tartalmazó cella lehet. Részletek a #1412 kommentjében. **Folytatás (2026-09-01):** mind a hat téma átmérve (`kollazs-eletciklus.md` **17.**) — a `picturepile` szorzója **pontosan 1,25000**, a `regulargrid`-é **1,00000**, a `contactsheet`-é **node-független**; a `scale` a **rajzolt méret**, nem a befoglaló dobozé; a 313 **nem beégetett konstans** (nulla találat a `.text`-ben). **Folytatás (2026-09-02):** a `.cxf`-író bináris oldala kimérve (`picasa-create-features.md` **1.6/g**): a csomópont-tömb **56 bájtos**, a `scale` a `+0x2c` (`0x008350b2`), a `theta` a `+0x28`; a mentés-szervező (`0x00834700`) **nem készíti elő** a csomópontokat. A 2026-08-30-i „vetítés/render-scale" magyarázat **MEGDŐLT**: a `regulargrid` elhelyezője **ugyanúgy `1,0`-t ír** a `+0x2c`-be (`0x0088520d`→`0x0088522d`), mint a contactsheeté — az `1,0` a norma. Kimerítő negatív pásztázás: indexelt, SSE- és disp32-alakú `+0x2c`-író **nincs**; a végleges értéket a kollázs-sáv 37 mutatós írójának egyike adja. A jegy **`blocked` + `felhasználóra-vár`** (fekvő Indexkép-minta). **⛔ Két SZÁMHELYESBÍTÉS a FILM fejezetben (2026-09-03):** az átmenetek száma **22, nem 18/21** — a 2.1 táblájából kimaradt a **`rect`** („Négyszög"), és a `0x00771a10` átmenet-nyilvántartó (934 b) **mind a 22 kulcsra** hivatkozik, tehát élő; a szövegdia-stílusoké **12, nem 11** — a 2.3 kilencet nevezett meg „+ további kettő" megjegyzéssel, holott **három** hiányzott (`Centered`, `I'm Feeling Lucky`, `Caption`). Mindkét lista most teljes, hivatalos magyar fordítással. Jegy-komment és címjavítás: **#432**.

⭐ **2026-09-02 (2.3/b) — a SZÖVEGES DIA fülének működése:** a beszúrás `<type>=2` rekordot hoz létre „Szöveg" placeholderrel, **a kijelölt dia UTÁN** (üres kijelölésnél a lista elejére), majd átvált a 2. fülre és a beviteli mezőre teszi a fókuszt (`WM_SETFOCUS`); a három kapcsoló mezői: **`<weight>` = 400/700** (GDI-súly, nem logikai!), `<italic>`, `<outline>`; a három legördülő a `<fontname>`, `<size>` és `<styleid>` mezőt írja, a **betűméret-lista teljes tartalma** `8·10·12·14·16·18·20·22·26·30·36·48·60·72·84·96` (`0x00c7e4f0`), a betűtípus a **`Preferences\makemovie::textfont`** kulcsba is bekerül; a két színválasztó `text_` / `bkg_` **előtag** szerint dől el. **Negatív eredmény:** a `titleoption_listbox` ága **halott kód** (a panelépítő nem hozza létre, és a névre egyetlen hivatkozás van a binárisban). Kommentek: **#432**, **#436**.

⭐ **2026-09-02 (2.5/c) — az „Opciók" fül és a KLIPTÁLCA működése:** a négy tálcagomb (`addclips` → klipgyűjtő mód, `addtomovie` → a lista **végére** fűz, `deleteclips` → töröl, `solo` → nincs parancs-ága); a három rendezés-rádiógomb az `.mxf` **`<ordering>`** mezőjét adja (**smart=0, album=1, chronological=2**), és a kattintás **önmagában nem számol újra**; a két csúszka képlete **kimérve**: `burstmodethresh = ⌊s²×86 400⌋` másodperc (maximum **pontosan 24 óra**, négyzetes görbe) és `felhasznált képek = ⌊t²×N⌋`, ahol N az „Összes fotó" darabszám — az `s` normalizáltsága a hangerő `×1000`-es skálázásából **mért**; új vezérlő: **„Dátumok megjelenítése"** (`showdates`); és egy eddig ismeretlen kapu: a **`CMakeFaceMoviePanel::askapplyswitchconfirm`** („Még nem alkalmazott módosítások vannak az Opciók lapon"), amelynek „Ne kérdezze meg újra" beállítása után a Mozgófilm létrehozása **némán eldobja** a függő módosításokat. Kommentek: **#1408**, **#432**, **#436**.

⭐ **2026-09-02 (2.6/c) — a „Mozgófilm létrehozása” gomb TELJES kimeneti menete:** a `render`, a `cancel` és az `export_youtube` **egy ágon** fut (`0x00620421`), a YT csak **előlépés** ugyanahhoz a `.wmv`-hez; a célmappa `<Képek>\Picasa\<honosított „Movies”>` (magyarul **Mozgófilmek**), **`My Videos` tartalékkal**, és a mappa `.picasa.ini`-t kap `P2category=Projects (internal)` sorral; a fájlnév négy lépésben áll össze (alapnév → `diavetites_jellegu_film` → „Helyreállított automatikus másolat” → tiltott karakterek kiszűrése), a kiterjesztés **`.wmv`**, a kódoló a futásidőben betöltött **`wmvcore.dll`** (`WMCreateProfileManager`, `WMCreateWriter`); a „Lecseréli a meglévőt, vagy újat hoz létre?” párbeszéd **felszabadítja** a régi fájl helyét, a másik mód **sorszámoz**; hibánál a `Preferences\SupportMovies` kulcs **elnémítja** az üzenetet. Jegy: **#1977**, komment: **#432**. ✅ **2026-09-03: a `0x00d694c0` mutató MEGVAN** — a **fájltörlés platformfüggő mutatója**: Windows NT-n a saját `0x009aecc0` burkoló (**`MultiByteToWideChar(CP_UTF8)`** → **`DeleteFileW`**), Windows 9x-en a nyers **`DeleteFileA`**; az elágazás a `GetVersion()` magas bitjén (`0x00c32bde`). Ezzel a 2.6/c „csere mód" lépése is teljes: a régi fájlt **törli**, `ERROR_ACCESS_DENIED`-nél 5 másodpercig újrapróbálja. Melléklelet: ugyanez a hibaosztály nálunk a **#1991** volt (lezárva) — a Picasa **ugyanazt a mintát** használta, amit mi is. A feloldás receptje: `binaris-regeszet-modszertan.md` **20.**

⭐ **2026-09-01 (2.9):** a filmkészítő **filmszalagja teljes fogd-és-vidd felület** (`filmstripmove/insert/dragtoclips/doubleclick/context`), a **négy csúszka** egy kezelőben, és a filmkészítő **saját, menthető projekt** (`CMakeMoviePanel::autosave`, „Back to Movie Maker", `Preferences\SupportMovies`). **2.10 (2026-09-01):** a `titledialog` — a **szöveges dia szerkesztője** (stílus- és méretválasztó, élő előnézet, `captionchk` a képfelirat átemelésére); a szöveges dia a filmszalagon **„Text Slide"** néven jelenik meg, az infósor `%s  %dx%d pixels` + `(%d of %d)`.

⭐ **2026-08-30 — a „Film készítése" szakasz MŰKÖDÉS-sel bővült** (2.5/b–2.8):
a `CMakeFaceMoviePanel` **„recompute" megerősítője** (`askapplyconfirm`
preferencia, a „Do not ask again" párbeszéd → #1408); a **7 kimeneti méret**
(320x240 … 1920x1080), a **3 hangsáv-opció** (Truncate/Fit/Loop), a film
**Preferences-kulcsok** (`showcaptions`, `cropfit`, `movievolume` 0..1000
alap 500, `makemovie1to1` alap 1); a **`video_control_bar2` sáv MŰKÖDÉSE**
(a `time` = `%02d:%02d:%02d` / `%02d:%02d:%02d` a DirectShow 100 ns-os
időből), és a **MoviePreviewHandler billentyű-térképe** (Space/Pause →
play-pause, Enter/Esc → teljes képernyő → #1154 42–44.). Jegy-kommentek:
**#432**, **#452**, **#1408**.

3. **Az Indexkép (contactsheet) `.cxf` `scale=313`-ának levezetése** — a
   Ghidra-C (2026-08-30) kizárta a layout-ból (a `0x00888210` 1,0-t ad a
   node `+0x2c`-be); a `313` a vetítés/render-scale képlete kell →
   `docs/specs/picasa-create-features.md` 1.9.14 + **#1412** (a jegy nyitva,
   fejlesztés + kutatás).

1. ~~**A Képkockamozaik kényszeres vágási szabálya**~~ — **A SZABÁLY KUTATÁSA MEGVAN**
   (#431/#916, 1.9.14, 2026-08-18): a kényszeres levél a téglalapot
   változatlanul átveszi és nem darabol tovább; a „nincs kényszer" jelölés
   mind a négy koordináta −1,0. A „melyik részfába irányítja" kérdés
   **tárgytalan**: nincs irányítás — a keresés körönként, képenként
   stempeli be a kényszert a csomópontba, és elutasításos mintavétellel
   találja meg a jó elrendezést. Ugyanitt megvan a pakoló **célfüggvénye**
   is (`0x00893570`, mindhárom rácsos témára közös): az **elpazarolt
   terület** minimalizálása. ⚠️ **A #916-os JEGY (a `CLocationTree` pakoló
   MEGVALÓSÍTÁSA és annak feltárása) NYITOTT** — a mai bekötésben a
   `_FRAMEGRID_CENTER` közelítés áll; a `0x008906e0` 7. slot ciklusa és a
   `0x008910b0` csomópont-gyártó dekompilációja a teendő
   (`kollazs-panel-ui-spec.md:1188`).
2. ~~**A Képkupac kezdeti (x, y) szórása**~~ — **elavult jelölés volt**: a
   szórás az 1.9.12-ben már 2026-08-14 óta megvan („legjobb jelölt"
   mintavételezés). A 2026-08-17-i átvilágítás vette le.

### [picasa-kollazs-felulet.md](picasa-kollazs-felulet.md) — nincs nyitott kérdés

⭐ **2026-09-03 — a 9. bit (keretválasztó) RENDERELT bizonyítéka megvan, a #997 leletje ELAVULT.** Eddig a bit jelentését csak a `0x00831750` fogyasztó-oldala támasztotta alá; most a tulajdonos valódi `AI6.jpg`-jén (3841 × 5120, `contactsheet`) képpontszinten is megvan: az első csempe körül **`(238,238,238)`** sáv fut — bájtra a `frames.WHITE_BORDER_BGR` —, a szélessége **41 / 42 / 43 px** három élen, a szabály pedig szabad paraméter nélkül `b = 0,05·(907 − 2b) ⇒ **41,23 px**`. Tehát az eredeti Indexkép **kirajzolja** a keretet, nem csak a `.cxf`-be írja. A lap **2.1/b**. **A mai kódunk is helyes** (**2.1/c**): a három keret-állás három különböző lapot ad, a felületi lánc ép — a #997 („a keretválasztó nem hat") a #1273 óta nem áll. **Új lelet:** a `test_indexkep_1273.py` tűrése elnyeli a keret elhagyását (`noborder`-rel is ÁTMEGY), tehát az őrnek **nincs foga** erre — önálló jegy: **#2118**. Jegyek: **#997** (lezárva), **#2118**.

✅ **2026-08-24 — az utolsó kérdés (a 6. bit MIÉRT a három rácsos témán van) LEZÁRVA**, ld. a lap **2/c** szakaszát: a bit pontosan a három `*Grid*` osztályon áll, és **nem öröklődésből** (a `CRegularGridTheme` szerkezetileg külön áll, mégis beállítja) — szándékos, témánként kiírt képesség-deklaráció. A *szándék* hatókörön kívül: nincs a binárisban. Jegy: **#1170**.

⭐ **2026-08-21, működés-kör (kilenc kérdés):** a
`kollazs-eletciklus.md` **16.** szakasza négy, eddig sehol nem szereplő
viselkedést rögzít — a **kattintható kész-értesítés**
(`collage::done` = „A kollázs kész (kattintson ide)"), a **„Mentés
mellőzve"** és a **formátum-eltérés** figyelmeztetése, a főablak
**várakozó állapota**, és a **`hascollage` PMP-oszlop** (1 bájt/sor,
valódi adaton mérve; a PMP-oszlopok **nem egyforma hosszúak**).
*(2026-08-21: a `hascollage` **jelentése is megfejtve** — ALBUM-oszlop,
„ehhez az albumhoz tartozik `PicasaCollage.cxf`", és az album
betöltésekor/mentésekor **fájl-létezésből** áll elő, nem a kollázs
mentésekor: [pmp-database.md](pmp-database.md).)*
Jegy: **#1168**. Az alábbi hat kérdést ez a kör NEM érintette.


*(A 2026-08-18-i két kör az eredeti hét kérdést **mind** lezárta — az
elszámolás a lap **12.** szakaszában. Ugyanaznap a harmadik, kimenet-kör
megfejtette a mentés TELJES törvényét — hova, milyen néven, hogyan, mi
történik utána; fájlválasztó bizonyítottan NINCS — a lap **9.1/b**
szakaszában. Az alábbi kérdések egyike sem igényel futó Picasát.)*

1. ~~A képesség-maszk **6. bitje** mit kapcsol?~~ — **MEGFEJTVE**
   (2026-08-21, a lap **2.**): a `collagepanel/groupnode`
   (`CollageNodeHandler` vtable 5. rekesze, `0x008603c0`) **külön,
   overlay feldolgozási ágba** kerül; a `+0x219` jelző hatására a
   jelenetgráf-bejáró (`0x009e2aa5`) külön verembe másolja a rekordot és
   korán kilép. A bit a három **rács-témánál** áll. A csomópont
   **vizuális szerepe is mérve** (a lap **2/b**): egy **`#F85E0F` színű,
   2 képpont vastag, élsimított KÖRVONALAS téglalap**
   (`ytShapeNode` + `ShapeDraw<RectSampler>`); a raszterező a belső
   képpontokat kihagyja (`0x007deddd` → `0x007defb0`), a bájtsorrend
   pedig a `0xFF7D8397` négy előfordulásával kalibrálva.
   **Ami MARAD:** miért épp a három rács-téma kapja a bitet.
   Jegy: **#1170**.
   *(A többi öt bit 2026-08-18-án lezárult: 12. = a téma megvalósítja a
   9. vtable-slotot, 13. = automata `collage_adapt`, 14. = a
   `collage::shadows` alapértéke, 15./16. = halott bitek.)*
2. ~~Mi a **célja** a `FILE_ATTRIBUTE_TEMPORARY`-nak?~~ — **LEZÁRVA**
   (2026-08-21, a lap **9.1/c**): a **hatóköre** kimérve — **öt** hely,
   mind projekt-kimenet (végleges és piszkozat kollázs-JPEG, kollázs- és
   film-automentés, film-kimenet); a Picasa **soha nem veszi le** és
   **soha nem olvassa vissza**, tehát a programon belül semmit nem
   vezérel. A **szándék** nincs a binárisban és nem is lesz. Linuxon
   nincs megfelelője — **nincs teendő**. Jegy: **#979**.
3. ~~Az **5120-as felső renderméret** szemantikája~~ — **LEZÁRVA**
   (2026-08-21, a lap **9.1/d**): négy dwordként utazik
   (`0, 0, 5120, 5120` = **négyzetes** doboz), és a mentési feladat
   `+0x64..+0x70` mezőibe kerül (`0x00838fc3`–`0x00838fe1`). Szabály:
   **lépték = 5120 / max(szél, mag)**, oldalarány megtartásával; hat
   golden fájl igazolja **mindkét tájolásban**. A `0x0087dcd0`-s nyom
   **téves volt** — az a hívás a mentés előkészítése.
4. ~~Az árnyék-képlet bemenete~~ — **LEZÁRVA** (2026-08-18, második
   árnyék-kör): az árnyék **témánként négy külön paraméterkészlettel**
   dolgozik (alfa 102 a Képkupacnál és a rácsos témáknál, 153 a Rácsnál
   és az Indexképnél); a `k` a képek cellaéle képpontban, az `A` lépték
   a 9.0 darabszám-képlete. Nem maradt feltételes állítás — a lap
   **9/b**-je. *(A jegy #977, már nem blokkolt.)*
5. ~~A polaroid-felirat **`vt[0x38]`** kapcsolója~~ — **HATÓKÖRÖN KÍVÜL**
   (2026-08-21, a lap **9/c**): a lánc végigkövetve (`ytSkia` `vt[0x28]`
   → `0x009033e0`), de a kapcsolónak **nincs „ki" állapota** — a `.text`
   teljes pásztázása szerint egyetlen szövegcsomópont-hívó sem ad 0-t —,
   ezért nincs megfigyelhető különbség, amit reprodukálni lehetne.
   Képernyőkép sem segítene. *(A `vt[0x2c]` ugyanaznap MEGFEJTVE: a
   `.tre` `textalign` bejárata — `0x009c7c00` hívja pontosan ezt a
   rekeszt, `"right"`→2, `"center"`→1 —, a kollázs **1**-et ad, tehát
   **KÖZÉPRE**; a `_draw_polaroid_caption`-ünk már így csinálja.)*
   Jegy: **#978**.
6. ~~Az **`avgcolor` adatbázismezőt** mi és milyen képlettel állítja elő?~~
   — **LEZÁRVA** (2026-08-21): a képlet a
   [pmp-database.md](pmp-database.md) „Az `imagedata_avgcolor` oszlop"
   szakaszában — csatornánkénti összeg / képpontszám **csonkoló** egész
   osztással, `0xAARRGGBB`-be csomagolva (`0x009ac640`); az élő,
   140 755 soros oszlop eloszlása a csonkolást függetlenül igazolja.
   A mi képletünk **két ponton eltér** → **#1171**.


### [export-parbeszed.md](export-parbeszed.md) — nincs nyitott kérdés

*(2026-08-20, három kör. A lap teljes: a `.fen` leíró, mind a 28 magyar
felirat, a kötések, a 9 beállítás-kulcs, a **képpontra mért geometria** a
tulajdonos képernyőképéről, a **teljes eseménykezelő-térkép** címekkel, és
az öt minőség-fokozat számértéke. A három korábbi nyitott kérdés a lap
**11.** szakaszában lezárva: a film-rádió alapértéke **0 = „Első
képkocka"**; a 193-as minőségérték
gyakorlati következménye bizonyítottan nulla, tehát a „Maximális"
nálunk maradhat 100.)*

0. ⭐ **2026-08-21, működés-kör:** a lap **8.** szakasza a kilenc
   működés-kérdést válaszolja meg (három belépési pont, a közös
   `CImageOutput` mag, a `.picasa.ini`-átvitel, az `]history:export`
   token, tíz hibaág, a registry-állapot). A **film-rádió
   ALAPÉRTELMEZÉSE lezárva** (`FileExportMovie` → `setne`). A maradék
   hét kérdés a lap **9.** szakaszában és a munkasorban. Jegy: **#1166**.

   ⭐ **2026-08-21, `CImageOutput`-kör** — a lap **10.** szakasza a
   9. szakasz 1., 3. és 4. pontját zárja le, utasításszinten:
   **az export után megnyílik a célmappa az Intézőben**
   (`ShellExecuteA`, `0x007414b6`), majd `]history:export` token —
   **indexelés és nézetfrissítés NINCS** a záró ágban; a **sorszámozás**
   teljes szabálya (`%0*d-%s`, szélesség = a kijelölt képek számának
   jegyszáma, 1-től, kötőjel + teljes eredeti fájlnév, `0x0073ee70`);
   az exportált mappa `.picasa.ini`-je **csak `caption` + `keywords`**
   (vesszős, `0x00740485`/`0x0074050d`); és **minden exportált fájl
   UGYANAZT az időbélyeget kapja** — mind a három mezőben, az export
   indulásának pillanatát (`0x00740c14` → `0x00740e57`).
   *(Ugyanaznap a **13.7**: a beállítások **OK-ra, egyetlen menetben**
   íródnak ki — a közös lezáró `0x008d2720` hívja a `vt[0x164]`-et, ha a
   lezárási kód 0 —, és **Mégsére semmi nem történik**: a `vt[0x168]` a
   `CExportPrefsDialog`-nál üres tő, `0x00b0d990`.)*
   *(És a **13.8**: az alapértelmezett célmappa neve a **szövegtárból**
   jön — angolul `export`, **magyarul `exportálás`** —, a név
   **fájlnév-tisztításon** megy át (`0x009946f0`, tiltott halmaz
   `\ / : * ? " < > |`), és a megjelenített útvonal **Wine-észleléssel**
   Unix-alakú is lehet (`0x0073a140`, `ShowUnixPaths`). Mellékesen egy
   **ütközés**: a mért időbélyeg-viselkedés és a mi `shutil.copy2`-nk
   kizárja egymást → **#1138**.)*
   *(És a **13.9**: az `]history:*` **NEM ini-token**, hanem az
   `albumdata_token.pmp` album-sorának tokenje — a tulajdonos valódi
   adatbázisában **kettő él** belőle (`]history:email` = „Elküldve
   e-mailben", `]history:upload` = „Feltöltve"), a négy literál a
   `0xc81238`–`0xc81268` blokkban, közös regisztrálóval (`0x0041c340`).
   **Exportot kérni a felhasználótól NEM kell.** Névcsapda: a
   `CThumbDB::Exported` kulcs a **feltöltés** gyűjteményét nevezi meg.)*

1. ~~**Mi TILTJA LE a film-rádiókat?**~~ — **LEZÁRVA** (2026-08-21, a lap
   **13.10**). **A párbeszéd SAJÁT kódja tiltja**, ha a kijelölésben
   **egyetlen film sincs**: `0x007394b3` (`[dlg+0xcd] == 0`) →
   `vt[0x114]("movies", 0)` (`0x007394e1`); a jelzőt a létrehozó
   (`0x005312b0`) teszi oda a `0x005c7990` vizsgálóból; a filmtípusok
   kódjai **8, 9, 10, 11, 12, 23, 29**. **KÉT korábbi állításunk
   megdőlt:** (a) „a párbeszéd saját kódja NEM tiltja le" — de igen, a
   `movies` név **második** hivatkozása épp a tiltás; (b) „a csoport
   címkéje fekete marad" — a képernyőképen a **címke is szürke**.

### [vagas-eszkoz-allapot.md](vagas-eszkoz-allapot.md) — nincs nyitott kérdés

~~A **kollázs Oldalformátum** legördülőjének sorrendje~~ — **MEGVAN**
(#876): a felépítő `0x007cc990` két kapcsolója adja; a kollázs esete az,
amikor **mindkettő hamis**. Ugyanitt derült ki, hogy a nyomatméretek
**metrikus/angolszász** ágra oszlanak.

### [picasa-gomb-es-menu-rendszer.md](picasa-gomb-es-menu-rendszer.md) — nincs nyitott kérdés

1. ~~a **letiltott** gomb rajza~~ — **MEGVAN** (#893): a rajzoló az alfát
   **néggyel osztja** (`0x009e3178`), kivétel nélkül
2. ~~a `popuplist` **lenyíló panel** színei~~ — **MEGVAN** (#894):
   `listdecrect`, sík `#E8E8E8` kitöltés, `#BABABA` keret
3. ~~**A kiemelt sor SZÍNE**~~ — **MEGVAN** (2026-08-21, a lap 8.
   szakasza): **`#7D8397`**, kódkonstans, a binárisban **`0xFF7D8397`**
   alakban, **négy** helyen (`0x006084e2` = `ytTextPopupListItem`,
   `0x00665bc9` = `CAddToList`, `0x007af034` = a feltöltés-lista,
   `0x007cea13` = a webalbum-panel), mindenütt a
   `test byte ptr [sor+4], 2` kijelölt-bit mögött. A nem kijelölt sor
   **`#FDFDFD`**. **A 2026-08-18-i „nincs a binárisban" negatív eredmény
   TÉVES VOLT:** a 24 bites alakra kerestünk, a konstans 32 bites
   (alfával) — a képernyőkép-mérés végig helyes volt. Jegy: **#894**.
4. ~~**A buboréksúgó rajza**~~ — **MEGVAN** (2026-08-21, a lap **8/c**):
   a tulajdonos képernyőképéből képpontonként mérve — kitöltés
   **`#F4F1E5`**, keret **`#B7B5AC` 1 px**, **derékszögű** sarkok, fekete
   szöveg, és **árnyék CSAK a jobb és alsó élen** (a bal/felső élen
   nincs). Az utóbbi a döntő nyom: ez pontosan a Win32
   **`CS_DROPSHADOW`** ablakstílus automatikus, rendszer-rajzolta
   árnyéka — ami megmagyarázza, miért nem volt sehol árnyék-kód a
   binárisban (a 8/b tizenegy pontos negatív leltára). Jegy: **#901**.

### [picasa-konyvtar-eszkoztar-viselkedes.md](picasa-konyvtar-eszkoztar-viselkedes.md) — nincs nyitott kérdés

⭐ **2026-08-24** — a lap egyetlen nyitott kérdése (**a `folderviewpopup` ▾
menü feliratai**) **LEZÁRVA**, és **képernyőkép nélkül**: a menüépítő
(`0x00559150`) 20 bájtos rekordtömbjének gépi végigjárása **160
parancsazonosítót** oldott fel egyértelműen. A ▾ menü a
`Nézet ▸ Mappanézet` almenü.

⭐ **2026-08-30 — a két további NYITVA pont LEZÁRVA, és a `prenotify`
„dekódolatlan" jelölés MEGFEJTVE** (a lap **4/c** szakasza): a
`0x005e2000` kezelő **teljes parancstérképe** a dokumentum-mezőkből — a
`ShowAlbumThumbnails2` preferencia a **„Indexképek megjelenítése a
könyvtárban"** (0x9cd7) pipa-tétel a ▾ menüben; a mód-mező
(`+0x2c0+0xd8`) 0/1/2/5 = a **rendezés-mód kódja** (Dátum / Legutóbbi
változtatások / Név / Méret); a `0x9e18/19/38` hármas a `+0x2c0+0xdc`
mező 0/1/2 rádiója — **2026-08-31 óta azonosítva is: a személy-lista
rendezésének három módja** (`Preferences\peoplesort`), ld.
`picasa-menu-parancsok-viselkedes.md` 36.3. A `prenotify` a `.tre`-parszerből (0x009ca5e0 →
0x009c7840) `[elem+0x380]=1` — a folderview a váltás előtt értesít.

**Két helyesbítés ugyanebből a körből:**
1. ⛔ a lap korábban a `flatview`-hoz `0x9c8b`-t, a `folderview`-hoz
   `0x9cbd`-t rendelt — **mindkettő TÉVES**, azok **rendezés**-parancsok
   (`ID_VIEWBYDATE`, `ID_VIEWBYRECENT`). A valódiak: **`0x9db6`**
   (Egyszerű mappanézet) és **`0x9db9`** (Fanézet).
2. ⭐ **HÁROM** mappanézet-mód van, nem kettő — a harmadik a
   **`ID_VIEW_WATCHED` = „Egyszerűsített fanézet"** (`0x9db8`), ami eddig
   sehol nem szerepelt nálunk (a `FolderHierarchyView.qml` fejléce is két
   módról ír). Jegy: **#853**.

### [picasa-arcfelismeres.md](picasa-arcfelismeres.md) — nincs nyitott kérdés (2 BLOKKOLT tétel)

⭐ **2026-08-22, arcfelismerés-kör (#26)** — új lap, a funkció **működése**
(nem a felülete): a három független réteg és a hét `Preferences`-kapcsolójuk
alapértékekkel, a két küszöb-legördülő teljes létrája (**50–95, ötösével,
alap 85**, az ugrótáblák nyers bájtjaiból), a `.picasa.ini` **KÉT** írási
útvonala és egy eddig sehol nem dokumentált kulcs (**`facedata`** — a 859
fájlos korpuszban **0** előfordulás), a `db3` kilenc arc-oszlopa **élő
adaton mérve**, a három romboló művelet pontos hatóköre, és a
`frversion="1.5"` migrációs kapu.

**Két korábbi állításunk MEGDŐLT:** a `facerect` nem „szentinel-es rect",
hanem **tisztán 0/1 logikai jelző**; és a tesztkészletben **igenis van
nevesítés** (13 941 régió).

✅ **Ugyanaznap FELOLDVA:** a tulajdonos adott egy nevesített arcokat
tartalmazó adatbázist, és ezzel a **teljes személy-album modell** megvan
(`]facealbum:<N>` ↔ `albumcontactids` ↔ `contacts.xml`, **9/9 egyezés**),
a **`facerectdata` jellemzőpontjai** (`conf`/`pan`/`leye`/`reye`/`mouth`),
és a felismerési **javaslat + pontszám** oszlopok. Ugyanitt **megdőlt a
saját reggeli állításunk**: a `facerect` IGENIS tárol valódi rect64-et.
Blokkolt maradt: a két `*checksum` képzési szabálya és a
`CreateAcceleratorTableA` tartalma (**#1238**).

### [picasa-elso-inditas.md](picasa-elso-inditas.md) — nincs nyitott kérdés

*(Új lap, 2026-08-21: az első indítás `initialscan` panelje — két
szövegkészlet (migráció / tiszta telepítés), 640×463 geometria, két rádió,
**rejtett Mégse**. Jegy: **#1167**. Egyik kérdés sem igényel futó Picasát.)*

1. ~~Mit ír a két rádió?~~ — **LEZÁRVA** (6.1): a panel nem ír fájlt,
   **−1/1/2 kódot** ad vissza. Ami MARAD: hol lesz ebből
   `scanlist.txt`-bejegyzés (`0x0040d6e3`-tól).
2. ~~Mi dönti el, melyik szövegkészlet~~ (`Text1` migráció / `Text2`
   tiszta telepítés) jelenik meg — **LEZÁRVA** (6.6): a felderítő
   `0x00406c00` a `+0x1020` sztringet a p1import ágon tölti
   (`0x00406ee9`), az indulás-rutin ez alapján dönt (0=migráció,
   1=tiszta). Megerősítve dekompilációval (2026-08-30).
3. ~~Hol jelenik meg a panel~~ (saját ablak vagy beágyazva), és mi
   történik, ha a felhasználó bezárja az ablakot (a Mégse rejtett) —
   **LEZÁRVA** (6.7): saját MODÁLIS ablak, bezárásra −1 a rekeszbe, az
   indulás `0xF4242`-vel megszakad.

### [picasa-mappanezet.md](picasa-mappanezet.md) — nincs nyitott kérdés

### [picasa-mappakezelo.md](picasa-mappakezelo.md) — 2 BLOKKOLT tétel (a hatókörön kívüli Apple-ágon felül)

⭐ **2026-09-02 (16.2/b) — a könyvtárbejáró hibakereső kiíratása TELJESEN
feltárva, és egy eddig sehol nem dokumentált MÁSODIK kimenettel.** A
`0x004f25f0` **négy módban** hívható: az 1–3. a `dirscanner-start/up/
shutdown.csv`-t írja a `Preferences\WriteDirscannerCSV` **kapu** mögött, a
**4. mód a kaput átugorja és meg is nyitja** a fájlt. Mindkét kimenet a
**`#db3\`** mappába megy, `"w"` módban. A sorformátum
`"%s",%f,%f,%d,%d,%d,%d` (a hét oszlop forrás-eltolásaival), és a `Dirty`
meg a `Valid` **külön** jelző. ⭐ **A `badfiles.txt`** ugyanabban a
függvényben készül: a `Type == 4` → `%s (badfile)`, a `Type == 5` →
`%s (baddirectory)` ⇒ **a bejáró nyilvántartja a hibás fájlokat és
mappákat**. ⛔ Ebből termékhiba is előkerült: a mi `scanner/walker.py`-unk
**hét `OSError`-ágat némán elnyel** → **#1998**.

1. **Mit jelent a `Type` 1, 25 (`0x19`) és 1001 (`0x3e9`) értéke?** A
   névfeloldó ág (`0x004f2804`–`0x004f2825`) megkülönbözteti őket, de
   sztring nincs hozzájuk. **Megszerzés:** a `ytDirScannerChangeList`
   dekompilációja. A #1998-at nem blokkolja.
2. **Mit csinál a `Preferences\DirscanRegression` kulcs?** Csak az
   olvasása látszik (`0x004e9b00`, 649 b). **Fejlesztői kapcsoló**, a
   termékre nincs hatása. **Megszerzés:** a `0x004e9b00` dekompilációja.

✅ **2026-08-24 — a két megmaradt „erős, nem megerősített" állítás MEGERŐSÍTVE:**

1. **Nincs minimális ablakméret** (2.3) — a kikötés megszűnt: a program **4**
   ablakosztályt regisztrál, mind a négy ablakeljárás átnézve, `WM_GETMINMAXINFO`
   és `WM_SIZING` **egyikben sincs**, ugrótáblás diszpécser sincs. *(Melléklelet:
   a 9. szakasz összevető táblájának 2. sora ELAVULT volt — a mi kódunk már
   `minimumWidth: 0` / `minimumHeight: 0`.)*
2. **A meghajtó-figyelmeztetés „NEM" ága** (6.1/b) — az út végigkövetve: sehol
   nem menti el a korábbi rádióállást, tehát **nem visszaállít, hanem feltétel
   nélkül** az „Eltávolítás" tételre kapcsol; a `+0x359` általános „benyomva"
   jelző (235 előfordulás), nem állapotmentő. Jegy: **#1334**.

### [picasa-eger-es-kijeloles.md](picasa-eger-es-kijeloles.md) — nincs nyitott bináris kérdés

⭐ **2026-08-22, mappahatár-kör (#1219)** — a **15.** szakasz bizonyítja, hogy
a mappahatáron való átnyúlás az eredetiben **nem egy ellenőrzés, hanem
szerkezetileg lehetetlen**: a feed konténere (`0x0076a390`) mindig pontosan
EGY sor kijelölés-csomópontját éri el, és mind a négy mag (tartomány
`0x00716ae0`, léptetés `0x00717eb0`, határ-ág `0x00717d10`, lasszó-teszt
`0x0071bc90`) csak a saját csomópontja `count()`/`itemAt()` párján iterál.
**A #1219 kifejezetten mérendőnek jelölt kérdése megválaszolva:** a nyilas
léptetés a mappa végén **MEGÁLL** (`0x00718031` `jbe`, mindkét vég ugyanaz
az ág), nem lép át és nem jelöl ki újat. **Egy állítás MEGDŐLT:** a
lasszónk hatóköre már ma is helyes.

*(A #905 nyolc, korábban csak névből következtetett `.tre` tulajdonsága a lap
1/c szakaszában kapott bináris választ; a végső látványbeli finomítások a
szakaszban külön bizonyítottsági fokkal szerepelnek.)*

⭐ **2026-08-20, kijelölés-kör:** a lap négy ÚJ szakaszt kapott, és ezek a
kijelölés eddig hiányzó **hatókörét** rögzítik:
**10.** a könyvtárnézet `CMultiAlbumNode`, **mappánként külön
`CSelectionNode`**-dal — mappaváltáskor a régi mappa kijelölése törlődik,
tehát a Picasában **nem létezik mappákon átnyúló kijelölés** ·
**11.** a Ctrl+A / Ctrl+D / Ctrl+I / Csillagozottak parancsazonosítói
(`0x9cb8` / `0x9c90` / `0x9c47` / `0x9d5b`) a kezelőikig, és a
„mindent kijelöl" mag (`0x00716f40`) · **12.** Home / End / Shift+Home /
Shift+End / Ctrl+Home / Ctrl+End / PageUp / PageDown teljes leképezése ·
**13.** a kijelölés-változás ára — az eredetiben egy menet, nálunk
**mért** 10 010 `stat()` + 6 006 ini-beolvasás egyetlen Ctrl+A-ra ·
**14.** a lasszó és a képhúzás **geometriai** szétválasztása: a
találat-vizsgálat a **kirajzolt képre** szűkít (középre igazítva,
`0.5` @ `0x00c72150`), a rács a mozgást elemtalálatnál **nem nyeli el**
(`0xF4241`), és az elrendezés cellák közti hézagot hagy — vagyis **ez sem
a mi döntésünk**, mint korábban gondoltuk
(jegyek: #1145, #1146, #1147, #1148).

1. ~~A **gumikeretes kijelölés** szabálya~~ — a `ytSelectionDragHandler` a
   **szerkesztő** téglalapjaié, nem a rácsé: **arányt kényszerít**
   (Shift 1,0 · Ctrl 4/3 · Alt 3/2, #891). ~~A RÁCS lasszójának szabálya~~ — **MEGVAN**
   (2026-08-18, 4/e): **metszés-teszt**, nem tartalmazás; a metszetnek
   szigorúan pozitív területűnek kell lennie.
2. ~~A **Shift-tartomány horgonya**~~ — **MEGVAN** (#892): a horgony a
   `[this+0x390]`, és Shifttel **egyesével bővít**, a horgony **továbblép**
   (nem Intéző-féle tartomány)
3. ~~A **26 belső eseménykód** jelentése~~ — **A GYAKORLATHOZ ELÉG MEGVAN**
   (2026-08-18, 4.2/b): a harmadik nekifutás megfordította az irányt, és
   nem az ablakeljárás felől, hanem a **84 `*Handler` viselkedéséből**
   olvasta ki. Nyolc kód jelentése megerősítve (1 = bal le, 2/3 = mozgás,
   4 = fel, 5 = jobb le, 0x0b = ejtés, 0x13 = találat-vizsgálat,
   0x1b = elrendezés, 0x1f/0x20 = be/ki), a visszatérési értékekkel együtt
   (`0xF4240` = kezeltem, `0xF4241` = add tovább). **Maradék:** a `WM_*` →
   belső leképezés — de a megvalósításhoz nem kell
4. ~~A **jobbklikk útja**~~ — **MEGVAN** (2026-08-18, 4/f): tizenhat helyi
   menü erőforrásneve a birtokló függvénnyel; a rácsnak album- és
   mappanézetben **külön** menüje van

### [picasa-ini-format.md](picasa-ini-format.md) — 5 BLOKKOLT tétel (a `text=` stílusblokk, a `rotate(0)` és a legacy `crop=`)

⛔ **2026-09-02 — SAJÁT HELYESBÍTÉS a `geotag` írásán:** a lap írási-sorrend
táblája azt állította, hogy a kulcsnak „két ága" van (`%lf %lf` **vagy**
`%lf,%lf`). Ez téves: a szóközös alak a **belső érték beolvasása**
(`sscanf`, `0xca74d8`, pontosan két mezőt vár), a vesszős a **fájlba írás**
(`sprintf`, `0xc8187c`). A lemezre írt alak egyféle, és **hat tizedesjegyű** —
84/84 élő sor igazolja. Részletek: `picasa-helyek-panel.md` 1. szakasz.

⭐ **2026-09-02 (3. kör) — a LEGACY `crop=` alak és a MIGRÁCIÓ.** A
binárisban van egy **második, Picasa 2 korabeli** vágás-alak:
`crop=%d,%d,%d,%d,%d;` (`0x00c8130c`, mind az öt mező kötelező:
`cmp eax, 5`). A `0x004221b0` **négy 16 bites szót** pakol egy 64 bitesbe,
és **`crop64=1,<hex>`** filter-tokenné alakítja — a hívó a
`0x00425f60` **olvasó**, tehát a **migráció beolvasáskor fut**. Élő adat:
a korpusz **761/761** `crop=` sora már `rect64` ⇒ a tulajdonos gyűjteménye
teljesen migrált. Nálunk a régi alak `ValueError`-t adna
(`ini/rect64.py:28`) → **#2008** (P4, megelőző).

1. **Melyik szám melyik koordináta a régi alakban?** A `sscanf` kimeneti
   címeinek veremre pakolása ezen a szinten nem fejthető ki.
   **Megszerzés:** a `0x004221b0` dekompilációja, **vagy** egyetlen régi
   `.picasa.ini` ismert vágású képpel. **A #2008 addig nem indítható.**
2. **Mi lesz a `crop=` sorral a migráció után** (átírja / törli /
   meghagyja)? A korpusz csak a végállapotot mutatja. **Megszerzés:**
   ugyanaz a régi minta, migráció előtti és utáni fájllal.


⭐ **2026-09-02 (2. kör) — az ini ÍRÓJA két függvény, és van egy
kulcs→ALAPÉRTÉK tábla.** A `0x0068ac80` az album-szintű részt
(`name`/`description`/`location`/`category`/`date`), a `0x0068b320` a
képenkénti szekciókat írja; ugyanaz a két hívó fűzi őket össze. ⭐ A
`0x0068b320` két NULL-lal lezárt tömbje kimondja, mit tekint a Picasa
**alapértéknek**: `flipped`→**`flipped(0)`**, `rotate`→**`rotate(0)`**,
`filters`/`text`/`moddate`→**üres**. ⇒ **a `rotate` nullája NEM a kulcs
elhagyása** — a korpuszban **1 735** `rotate=rotate(0)` sor van. ⛔ Nálunk
a forgatás 0-nál **törli** a kulcsot, és a kód kommentje ezt „bitre pontos
round-trip"-nek mondja — Picasa-eredetű fájlon **fordítva igaz** →
**#2004**. Plusz: a `[encoding]` literál pontos alakja **CRLF-fel**
(`0x00ca77f0`, 30 bájt), és **0/859** valós fájl tartalmazza (694
album-jellegűből is nulla) ⇒ írásnál **nem szabad magunktól bevezetni**.

1. **Ha a `rotate=` sor HIÁNYZIK és a felhasználó 0-ra forgat, kiírja-e a
   Picasa a `rotate(0)`-t?** A korpusz csak a végállapotot mutatja.
   **Megszerzés:** a tulajdonos windowsos Picasájában egy `rotate=` nélküli
   képet 4×90°-kal elforgatni. A #2004-et nem blokkolja.


⭐ **2026-09-02 — a `text=` STÍLUSBLOKK két nyitott mezőjéből kettő megvan.**
A szerkesztő szöveg-eszközének (`edittextpanel`) kezelőiből: a formátum
maga `v1,%u,%u,%f,%f,%f,%f,%u,%u,%u` (`0x00ce42e8`; az olvasó `cmp eax, 9`),
és **az olvasó két RÉGEBBI, `v1` nélküli alakot is ismer** ⇒ a `v1`
formátum-verzió. Az **5. mező (`<a>`) a KÖRVONAL VASTAGSÁGA** (0…1, alap
**0,5**, **0 = nincs körvonal**), a **8. mező a betűsúly** (400 / **700**
félkövéren), az **igazítás** értékkészlete **0 = bal · 1 = közép ·
2 = jobb** (`0x0062f300`). ⛔ **Ebből kiderült egy termékhiba is:** a mi
írónk **csak a két színt** adja át, tehát nálunk a körvonal mindig eltűnik
és minden felirat félkövér → **#1994**.

1. **Melyik float az ÁTLÁTSZATLANSÁG — a 4. vagy a 6.?** Mindkettő
   `1.000000` mind a három valós blokkban (az alapérték), ezért a korpusz
   nem különbözteti meg őket. **Megszerzés:** egyetlen `.picasa.ini` a
   tulajdonos windowsos Picasájából, amelyben a felirat **csökkentett
   átlátszósággal** készült.
2. **Mi a `<b>` (9. mező)?** A korpuszban `0` és `258` (`0x102`); az
   `<a>`-val együtt mozog, de ez következtetés. **Megszerzés:** ugyanaz
   az egy minta, ha benne az **igazítás** és a **dőlt/aláhúzott** is
   eltér az alapértelmezettől.

✅ **2026-08-24 — LEZÁRVA.** „Mit tesz a Picasa, ha külső program írja az
inifájlt?" A kulcs **nem a képfájl, hanem maga a `.picasa.ini`**: a Picasa
mappánként eltárolja az ini **utolsó írási idejét** (`albumdata_inisync`,
FILETIME), és ha a lemezen lévő fájl újabb, újraolvassa — **`flags = 3`**-mal,
tehát a `filters` is hatókörben. Mérés: **783/787 bitre egyező** valódi
mappán (99,5%). ⇒ **elég írni az ini-t**; a képfájl érintése az eredetiben
nem létező út → **#1320**. Részletek: a lap „MEGFEJTVE: az újraolvasás
kulcsa az INI FÁJL saját dátuma" szakasza.

A megmaradt szál (miért nem jelenik meg mégsem a `filters=`) **nem a
kiváltás** kérdése — a szigorú beolvasás ága, **#685**.

### [szerkeszto-felso-sav.md](szerkeszto-felso-sav.md) — 1 BLOKKOLT tétel (ÚJ, 2026-09-02)

⭐ **2026-09-02, #1905-kör:** a szerkesztő fejlécének mind a hét vezérlője
kimérve (a tervezővászon mérete = a futásidejű képpontméret, hat elemen
igazolva a tulajdonos felvételén); a „paletta-ikonos gomb" = **`quickupload`**
(„Upload to your Web Albums Drop Box", `OneUp::ID_QUICKUPLOAD`) → **#1935**;
a filmszalag **hét férőhelyes** (`7 × 28 + 6 × 3 = 214`), az aktuális kép
**mindig a középső férőhelyen**; a hisztogram-doboz horgonya **`root.alsó − 95`**.

1. **A bélyegképre kattintás szemantikája** — hogy a kattintás kijelöli-e
   azt a képet, NINCS mérve. Az olcsó lánc kimerült (`.tre`: csak
   `m_scaleXY`, se `Handler`, se `Property`; szövegtár: nincs; sztring-xref:
   öt függvény, egyikben sem kattintás-ág). **Megszerzés:** célzott
   Ghidra-kör a `CFilmstrip::vftable` (`0x00c9359c`) egérkezelő rekeszére.
   Lap: `szerkeszto-felso-sav.md` 5.5; jegy **#1905**.

### [getmore-klipgyujto-mod.md](getmore-klipgyujto-mod.md) — 1 BLOKKOLT tétel (ÚJ, 2026-09-02)

⭐ **2026-09-02:** a `thumbui` `single_action_*` hármasa feltárva — a
kollázs/filmkészítő **klip-gyűjtő módja**. Két belépési pont, három
visszatérő felirat (`collagepanel::back_to_collage` · `CMakeMoviePanel::back_to_slideshow`
· `thumbui::back_to_previous_tab`), a ✕ **csak elrejt**. Helyesbítés: a
`konyvtar-ablak-meretek.md` 5.8 „haladásjelzés" elnevezése téves volt. → **#1939**.

1. **Villog-e a visszatérő gomb?** A gomb makrója hozza a negyedik
   („throb") bőrt — mért különbség: a keret `#BBBBBB` → **`#629BC3`** —, de a
   `.tre` nem ír rá `Property throb 1`-et, tehát ha bekapcsolódik, azt kód
   teszi. **Megszerzés:** célzott Ghidra-kör a `0x00601090`-re (`eThrobOff`).
   Lap: `getmore-klipgyujto-mod.md` 3.3; jegy **#1939**.

### [racs-nagyito.md](racs-nagyito.md) — 1 BLOKKOLT tétel (ÚJ, 2026-09-02)

⭐ **2026-09-02:** a rács-nagyító működése feltárva — az 51.3 három korábbi
blokkolt részkérdéséből **három lezárva**. Helyesbítés: az 51.3
„nálunk nincs" állítása **elavult** (a #1808 azóta megépítette, a #1911
vette ki a gombot). Jegy-komment: **#1911**, **#460**.

1. **Mekkora a nagyítás?** A kezelő (`0x0077be10`) és négy testvére
   (`0x0077b4b0`, `0x0077b6e0`, `0x0077b780`, `0x0077b8e0`) teljes
   diszasszemblátumában **nincs nagyítási arány**. **Megszerzés:** a
   rajzoló ág, `0x0077bb10` célzott dekompilációja (a `80.0` és a
   `2276,5556` konstansokkal). Lap: `racs-nagyito.md` 6.; jegy **#1911**.

### [racs-ures-allapot.md](racs-ures-allapot.md) — 1 BLOKKOLT tétel (ÚJ, 2026-09-02)

⭐ **2026-09-02:** a `thumbui` `lightbox_esolo_*` párja **HALOTT** az
eredetiben (nyers bájtkeresés: 0 találat; pozitív kontroll a testvér
`lightbox_bgtext`-en) ⇒ **nem építjük meg**; helyette a `lightbox_bgtext`
**hét** kontextus-szövege él. Helyesbítés: a
`picasa-menu-parancsok-viselkedes.md` 51.4 „kis jegy értéke lehet" sora.
Jegy: **#1945**.

1. **Melyik kontextus melyik szöveg-indexet adja?** A két közvetlen hívóból
   egy immediate (`push 3` = „All photos have been uploaded"), a másik
   **számított** (`0x0067b285`). **Megszerzés:** a `0x00679ca0` (6960 b)
   közzététel-panel célzott dekompilációja. Lap: `racs-ures-allapot.md` 5.;
   jegy **#1945**.

### [biztonsagi-mentes.md](biztonsagi-mentes.md) — 2 BLOKKOLT tétel

⭐ **2026-09-03 (11.1 ÁTÍRVA) — a `files.txt` írása MEGVAN, és két korábbi
olvasat MEGDŐLT.** A `0x00677f6d` **nem** írás-hívás: a `0x00d69518` mutató
`GetFileAttributesEx`. A valódi menet **bájtra fűzés** (`0x00677de6`–
`0x00677ecb`): `CreateFile(OPEN_ALWAYS, R/W)` a célra + `CreateFile(OPEN_EXISTING,
GENERIC_READ)` a forrásra, **mindkettő teljes beolvasása**, `SetFilePointer(0,
FILE_BEGIN)`, majd **a régi, utána az új tartalom** kiírása — és a blokk csak
akkor fut, ha a másolandó elem célja maga a `files.txt` (mért `strcmp`,
`0x00677d38`). **Sorformázó a Picasa3.exe-ben NINCS**, a `\files.txt` sztring
egyszer fordul elő és **egyik társ-binárisban sem** (14 index, két lekérdezési
alak). A kérdés átfogalmazódott: nem „mi a sorformátum", hanem **„mi van a
forrásfájlban"** — BLOKKOLT, megszerzés: valódi `files.txt`, vagy a
`0x00678630` dekompilációja — **jegy #2090**. Komment: **#440**.

⭐ **2026-09-03 (12. szakasz) — a LEMEZRE ÍRÁS menete.** A 10. szakasz a
`publish` sávot írta le; ez azt, ami az **OK után** történik. **Mért képlet**
a lemez használható kapacitására (`0x0066be90`): `szektorszám × 2048 −
tartalék`, ahol a tartalék **DVD-nél 4 096 000**, **CD-nél 409 600** bájt
(`0x0066bf50` / `0x0066bf58`); kétrétegű lemeznél (médiatípus **`0x214`**)
rögzített **8 547 991 552** bájt; ha a kapacitás nem olvasható, a tartalék
alapérték **688 072 704** bájt. A „DVD-e?" hat kódra igaz (`0x00666400`).
⭐ **A mentés TÖBB LEMEZRE folytatódhat**, és a Picasa sorszámozza őket
(„Ez lesz a(z) %d. számú lemez a(z) %d darabból", `InsertNext::13`) —
**lemezíró nélkül ISO-fájl(ok)ba** is dolgozik (`InsertNext::7*`), ez a mi
környezetünkben az implementálható ág. A 21 írás-állapot, a törlés-
figyelmeztetés és a médiatípus-nevek hivatalos magyar szövege a lapon.
Melléklelet: a `WriteProgress::13` („Mentési készlet frissítése") kimondja,
hogy a **`BKTag` címkézés az írás VÉGÉN** fut, nem az elején. Új jegy:
**#2074**.

⭐ **2026-09-03 (12.8) — HÁROM külön kódkészlet, kettő megfejtve.** A lemez
felismerése nem egy számozáson megy: **(a)** az írhatósági állapot `0x301`–
`0x304` (`0x006665c0`, négy név + „Unknown"); **(b)** a **lemezformátum
`0xA1`–`0xFA`, 25 nevesített eset** (`0x00666630`, kétszintű ugrótábla
`0x0066682c` → `0x006667c4`) — a teljes tábla hivatalos magyar fordítással a
lapon (31 `ytICDVDR::MT*`/`MF*` kulcs); **(c)** a családkód `0x2xx`, hat érték,
**továbbra is megfejtetlen**.

⛔ **Megdőlt magyarázat:** a `0x2xx` **nem** az IMAPI2
`IMAPI_MEDIA_PHYSICAL_TYPE` + `0x200` — az illesztés ellentmond önmagának (a
kétrétegű IMAPI-kódok hiányoznak a „DVD-e?" listából, miközben a `0x214`
kapja a kétrétegű kapacitást). A `CDVDR.yti` indexében nincs médiatípus-szöveg,
és a nyers konstanskeresés sem szűkít. **NINCS MEG:** öt kód jelentése; a
megszerzés útja a `0x2xx` mezőt beállító COM-hívási lánc
(`IDiscRecorder2` → `CurrentPhysicalMediaType`). Lap: `biztonsagi-mentes.md`
12.8; jegy **#2074**.

⭐ **2026-09-02 (11. szakasz):** a `files.txt` **megnyitási módja MÉRVE** —
`OPEN_ALWAYS` + `GENERIC_READ | GENERIC_WRITE` (`0x00677de6`), `OPEN_EXISTING`
tartalékkal (`0x00677e31`) ⇒ a Picasa **vissza is olvassa**, nem csonkolja; a
csak-olvasható jelzőt itt is leveszi (`0x0067834e` → `0x00678362`). A
**sorformátum továbbra is BLOKKOLT, de szűkítve**: az író hívás
(`0x00677f6d`) **belső függvénymutatón** (`0xd69518`) megy, nem nevesített
importon — ezért nem találja meg sem a sztring-, sem az importnév-keresés.
Melléklelet: a `replicates.xml` mezőlistája **tételesen azonos** a
`backups.xml`-ével (közös író `0x006759c0`, közös olvasó `0x00676910`), az
utoljára használt cél **két külön kulcsban** él (`LastBkSet` /
**`LastReplTarget`**), és megvan a replikáció **négy állapotszövege** hivatalos
magyar fordítással. ⭐ **Strukturális kulcs:** a parancsdiszpécser
(`0x005fa770`) a sáv gombjait **`publish/%s_go` / `publish/%s_cancel`** alakban
szólítja meg, a `%s` ∈ {`backup`, `presentcd`, `replicate`} — ez egy **mért,
konkrét példa** a módszertani lap 19. szakaszának „dinamikusan összerakott
név" hamis-pozitív osztályára. Jegy-komment: **#440**.

⭐ **2026-09-02:** a mentés **MIT ÍR** oldala feltárva (az 50.2 a fogalmat és
a felületet adta, ezt nem): `backups.xml` négy mezővel, **három**
tartalom-mód, `files.txt` a célmappában, honosított
`\Picasa biztonsági másolat\`, lemezhely-ellenőrzés. Jegy: **#440**.

⭐ **2026-09-02 (2. kör) — HÁROM lezárás és KÉT helyesbítés:**
a `backups.xml` **a `db3` mappában** van (`#db3\` token, `0x00c7eeb8`,
átadva `0x00670ca8`/`0x00670aa8`), `"wb"` módban, a csak-olvasható jelző
levétele után; **az inkrementalitást adatbázis-CÍMKE adja: `BKTag ` +
a készlet neve** (`0x00670b25`) — nincs külön mentés-nyilvántartás.
⛔ **Megdőlt:** a `0x009bfde0` **nem** útvonal-építő, hanem az **XML
behúzása** (80 szóköz, a `0x009bfed0` elem-író hívja); és a
**`Picasa2Backups` nem mappa, hanem a fájl XML-gyökéreleme**. Új
szakaszok: 9. (BKTag), 10. (a `publish` sáv három módja, hét
beállításkulcsa, öt párbeszéde és tizenhárom tájékoztató szövege).

1. **Mi a `files.txt` sorformátuma?** A név (`\files.txt`, `0x00ca5c78`) és
   a hely megvan; a függvény **egyetlen formátum-sztringet sem** hivatkozik
   (csak a három állapotüzenetet), tehát nyers írás. **Megszerzés:** a
   `0x00677a70` (3005 b) dekompilációja.
2. **A `BKTag` címke a `.picasa.ini`-be is kikerül, vagy csak az
   SQLite-indexbe?** ⚠️ A korpusz **nem tudja eldönteni**: a `BKTag`-re
   nulla találat, de a `keywords=`-re **is** — a korpusz kulcsszavakat
   egyáltalán nem tartalmaz. **Megszerzés:** a `0x00670b25` utáni
   felhasználó dekompilációja, vagy egy `.picasa.ini` olyan gépről, ahol
   futott a mentés.

### [ajandek-cd-kimenet.md](ajandek-cd-kimenet.md) — 1 BLOKKOLT tétel (ÚJ, 2026-09-02; bővítve 2026-09-03)

### [ui-audit-editor.md](ui-audit-editor.md) — nincs nyitott kérdés

⭐ **2026-09-03 — a szerkesztő MARADÉK három vezérlője.** Mindhárom
`m_hidden` alapállapotban, ezért ránézésre nem tűnnek fel. ⭐ **Ugyanaz a
funkció KÉT ALAKBAN:** a szöveg-overlay láthatósága a **menüben két külön
parancs** (`ID_PICTURE_SHOW_TEXT`/`…HIDE_TEXT`), a szerkesztő panelen viszont
**egyetlen jelölőnégyzet** (`editpanel/showtextcheckbox`,
`superbutton(buttcon_checkbox)`, az **1. fülön**, felirata **„Szöveg
megjelenítése"**) — aki csak a menü-specet olvassa, lemarad a
jelölőnégyzetről. ⛔ **NINCS hozzá `Preferences`-kulcs** (mérve, két
lekérdezési alakkal) ⇒ munkamenet-szintű nézetkapcsoló, nem tartós
beállítás. ⭐ **Az `editpanel/editslideshow` a már megépített `editcollage`
IKERPÁRJA:** mindkettő `root`-gyerek, mindkettő `m_hidden`, és **ugyanaz a
kezelő** (`0x00567a00`) — a szerkesztő felismeri, hogy a kép egy PROJEKT
kimenete, és felkínálja a forrás újranyitását. Nálunk a **kollázs-ág megvan**
(#1002), a **mozgófilm-ág nincs** ⇒ **#2114**. Végül: az
`editpanel/edithelpbutton` **ikonja ki van kommentezva** — ugyanaz a
„lecsupaszított súgógomb" minta, mint a `printpanel/phelpbutton`-nál ⇒ nem
kell megépíteni. ⇒ **Az `editpanel` feltáratlan listája ÜRES: 3 → 0**
(globálisan 103 → **100**). Komment: **#425**, **#1002**.

⭐ **2026-09-03 — a KETTŐS NÉZET (2-up) teljes vezérlőkészlete.** A **#434** a
*fogalmat* rögzítette (három üzemmód, `TwoUp*` kulcsok), de **egyetlen
elemnevet és címet sem** tartalmazott. Most megvan: a három üzemmód **egyetlen
háromszegmenses kapcsoló** (`only_1up` **bal** · `ab_2up` **közép** · `aa_2up`
**jobb**, a respack `buttcon_LS/MS/RS` rajzaiból), a kölcsönös kizárás
**`Property uptarget`**-tel megy — mindegyik **név szerint felengedi a másik
kettőt**, ezért az aktív gombra kattintva **nem tűnik el minden pipa** *(ez a
mi rádió-csapdánk ellenszere)*; az alapértelmezett a `only_1up`
(**`setpressed 1`**, `editpanel.tre:1196`). Két segédgomb **alapból rejtett**
(`swap_2up_focus` = „Fókusz váltása a képek között", `swap_2up_layout` =
„Váltás a vízszintes és a függőleges elrendezés között"), ahogy az
`editpanel/weblink` is. ⭐ **A szerkesztési ütközés párbeszéde teljes
szöveggel** (`CThumbUI::Confirm2up*`, `0x0056aad0`): **„Szerkesztett
változatok kiválasztása"** / „A képnek két szerkesztett változata van.
Melyiket szeretné megtartani?" — és a válaszgombok **NEM „A/B", hanem
HELYZETEK**, **négy** darab (`Bal` · `Jobb` · `Fent` · `Lent`), mert a
párbeszéd az aktuális elrendezéshez igazodik. ⛔ **A `wipe_2up_toggle` a
kódban NÉV, a felületen NINCS** — sem `.tre`, sem respack-réteg. ⇒ Az
`editpanel` feltáratlan listája **11 → 3** (globálisan 111 → **103**).
Komment: **#434**.

### [picasa-nyomtatas.md](picasa-nyomtatas.md) — nincs nyitott kérdés

⭐ **2026-09-03 — HÁROM TÉVES ÁLLÍTÁS JAVÍTVA, és a panel alsó gombjai
feltárva.** ⛔ A lap azt írta, hogy a nyomtatási beállítások párbeszéd
**„21 felirat, mind angolul, nem került át a fordítható erőforrásokba"** —
**mindhárom állítás téves**: **26 bejegyzés** (23 felirat + 3 buboréksúgó),
**mind magyarul is megvan**, a kicsomagolt `i18n\printoptionstext.xml`-ben
(`referencia/i18n-hu/`, 4 202 bájt). A teljes magyar tábla most a lapon áll.
⚠️ **Két hivatalos buboréksúgó HIBÁS fordítás:** az `apply` és az `ok` súgója
„a Google Fotókra" alkalmazásról beszél, holott a párbeszéd a nyomat
szegélyét és feliratát állítja. ⛔ Második helyesbítés: a `phelpbutton`
**nincs** „teljesen kikommentezva" — csak az **ikonja, felirata, színe és
horgonya**; maga a gomb él, `vbutton`-ként (rajz nélküli találati terület).
**Új mérés:** a `psetupbutton` a **Windows nyomtató-tulajdonságok**
párbeszédét nyitja (`0x00861750`: `OpenPrinterA` + kétszer
`DocumentPropertiesA`); a `froogle` **megerősítést kér**, majd a
**`https://uploader.picasa.com/froogle.php?q=%s`** címet nyitja meg a
**nyomtató nevével** — adatvédelmi szempontból nem semleges, és a
szolgáltatás megszűnt ⇒ **hatókörön kívül**. Végül: **két** minőségszöveg-
család van (`CPrintDlg::*qual` és `ThumbUIPrint::Review*`), és a magyar
`PrintCount` **megcseréli a pozicionális argumentumokat** (`%2$d / %1$d`).
⇒ **A `printpanel` ezzel teljesen feltárt: feltáratlan 6 → 0**
(globálisan 122 → 116). Komment: **#1780**, **#446**; új jegy: **#2103**.

⭐ **2026-09-03 (11. szakasz) — a panel HÁROM JELÖLŐNÉGYZETE, és egy REJTETT
MELLÉKHATÁS.** A 3./10. szakasz a *belső* beállításokat írta le; a felhasználó
viszont három négyzetet lát: **„Diavetítéssel együtt"** (`publish/optionbox1` →
`Preferences\CDSlideshow`, alapérték **1**), **„Adathordozó törlése"**
(`optionbox2`), **„A Picasával együtt"** (`optionbox3` →
`Preferences\CDSlideshowInclSetup`, alapérték **1**). ⭐ **A „Diavetítéssel
együtt" NEM csak a vetítőt teszi a lemezre:** ugyanaz az érték állítja be az
`option_convertnonjpeg` kulcsot (`0x0066f6f3`) — vagyis **bekapcsolva a
nem-JPEG képek JPEG-be konvertálódnak**, és ezt a felület sehol nem jelzi.
A mentés-ágon nincs ilyen kapcsoló: a visszaállító **mindig** rákerül a
lemezre (`0x0066f57d`). A `_go`/`_eject` **nem külön gomb**, hanem
**mód-függő rés** (`0x0066bf90` → `[obj+0x2a0]`, `[obj+0x2a4]`). A készlet
alapértelmezett neve **„Saját mentési készlet"** (`il_BurnPanel::bksetname`).
A Kiadás gomb tényleges művelete a **`CDVDR.yti` COM-oldalán** van — ugyanaz a
tétel, mint a **#2074**. ⇒ **A `publish` panel ezzel TELJESEN feltárt:
feltáratlan 5 → 0**, lekutatva 30/30. Komment: **#32**, **#440**.

⭐ **2026-09-03 (9–10. szakasz) — a BELÉPÉSI PONTOK, és egy BLOKKOLT tétel
LEZÁRVA.** A lap eddig azt írta le, mi kerül a lemezre; azt nem, **honnan
indul**. Öt belépési pont: `eMenuCreate::ID_BURNCD` (a **Létrehozás** menüben —
a lap korábban `eMenuTools`-t írt, **helyesbítve**), a `thumbui/cdmode`
üzemmód-gomb (magyarul **„Ajándék CD"**, buboréksúgó: *„CD/DVD létrehozása
beépített diavetítéssel…"*), a `publish/presentcd_go` (**„Lemezre írás"**), és
**kettő, ami a `.tre`-ben KI VAN KOMMENTEZVE**: `headerpanel/create_cd` és
`faceheaderpanel/create_cd` — a bináris ismeri a nevüket, a felületleíró
kikapcsolja őket. ⭐ **A 7. mérleg BLOKKOLT tétele („a 16 beállítás
értékkészlete") LEZÁRULT dekompiláció nélkül:** a `0x0068eea0` a **második**
függvény (a blokkolás indoka „egyetlen olvasó" volt), és a 16 kulcsot **16
egymás utáni dwordre** képezi (`+0x454`…`+0x490`, hézag nélkül) — ez egyben
igazolja a lista teljességét, és megadja a **hiányzó tizenhatodik** kulcsot
(`option_copysrctotempdest`). A `0x0066f470` húsz beállító híváshelye
kiolvasva, köztük **`option_jpegquality = 85`** — ugyanaz, amit mi is adunk
(`exporter.py:62`), **egyezik**. **Megdőlt:** „a beállításokat a `Preferences`
tárolja" (nulla `Preferences\option…` sztring) és „az Ajándék CD nem
fényképexport" (`picasa-menu-parancsok-viselkedes.md` `ID_BURNCD`, javítva).
Komment: **#32**, új jegy: **#2095**.

⭐ **2026-09-02:** az Ajándék-CD kimenete feltárva — a lemez **önjáró**
(`PicasaCD.exe` + `Picasa CD Slideshow.app` + `PicasaRestore.exe` +
`Picasa Restore.app` + `setup.exe` + `Download Picasa.url` + generált
`autorun.inf`), a forrásmappa **élő mintaként megvan** a repóban, és a
lemez mappanevei **honosítottak**. Nálunk a menüpont **halott helyőrző**
(`PicasaMenuBar.qml:1329`). Jegy-komment: **#32**, **#440**.

1. ~~Mi a 16 kimeneti beállítás ÉRTÉKKÉSZLETE?~~ **LEZÁRVA (2026-09-03)** —
   dekompiláció nélkül: a `0x0068eea0` a **második** függvény (a blokkolás
   indoka „egyetlen olvasó" volt), és 16 egymás utáni dwordre képezi a
   kulcsokat; a `0x0066f470` húsz beállító híváshelye kiolvasva. Lap:
   `ajandek-cd-kimenet.md` **10.**
2. **Melyik ÁG melyik üzemmódhoz tartozik?** A `0x0066f470` három ágon állít
   értékeket, de a `[ebp+0x13f]` jelzőbit és a `0x0066f546` `test edi, edi`
   hozzárendelése a három üzemmódhoz (mentés / Ajándék-CD / feltöltés)
   **NINCS MÉRVE**. **Megszerzés:** a `0x0066f470` (923 b) célzott
   dekompilációja, VAGY egy valódi kiírt lemez tartalomjegyzéke. Lap:
   `ajandek-cd-kimenet.md` 7.; jegy **#2095**.

### [pmp-database.md](pmp-database.md) — 1 nyitott kérdés (ÚJ, 2026-09-02)

⭐ **2026-09-02 — SAJÁT HELYESBÍTÉS a bélyegkép-gyorstár kulcsvektorán:** a lap
korábbi következtetése („a kulcs tárankénti, nem globális fotó-azonosító")
**érvénytelen** — két **eltérő hosszú** vektort vetett össze rés szerint
(`thumbs` 140 755 vs. `previews` 273 921). Azonos résterű tárak közt mérve a
kulcsvektor **bitre azonos**: `thumbs` ≡ `thumbs2` (140 755/140 755 és
3 338/3 338), `previews` ≡ `bigthumbs` (273 921/273 921) — noha a tárolt blob
más (144 px vs. 72 px JPEG). ⇒ **a kulcs nem lehet a blob ellenőrzőösszege**,
hanem a forrásfotóra vonatkozó, sorindexhez kötött bélyeg.
Melléklelet: az „elavult sorok maradnak a `previews`/`bigthumbs` vektorban"
eddigi *következtetés* **MÉRÉSSÉ** vált (az `arcok` készletben 216, illetve 217
élő bejegyzés nem valódi JPEG-re mutat, ebből 185+185 a katalóguson túli
sloton; a tulajdonos nagy mentésében **0 anomália** mind a négy tárban) ⇒ a
beolvasónak a `FFD8`/`FFD9` tartalom-ellenőrzés **kötelező**. Plusz a tároló
bináris oldala: `CBlockFile` (`.\thumblab\CBlockFile.cpp`), a
`Preferences ▸ Write blockfile CSV` kapuval kapuzott `Size,Offset,Checksum`
hibakereső dump (`0x006b5e00`) és a `Restore` helyreállító ág.
Jegy-komment: **#1446**.

1. **Hogyan képződik az `*_index.db` kulcsvektora?** Réshez (sorindexhez)
   kötött bélyeg, amivel a Picasa eldönti, hogy a gyorstárazott blob még a mai
   forráshoz tartozik-e. **Hét jelölt kizárva** (`imagedata_originfast`,
   `originslow`, `onlinechecksum`, `long`, `rotate`, `filetype`, `tagdate` —
   alsó és felső 32 biten is, 0/3 204 egyezés). **Megszerzés:** a `CBlockFile`
   írási útjának (`0x006b61e0` környéke) célzott dekompilációja, vagy a kulcs
   változásának megfigyelése egy fájl módosítása után élő Picasában.
   Lap: `pmp-database.md`; jegy **#1446**.

### [picasa-email-kuldes.md](picasa-email-kuldes.md) — 1 BLOKKOLT tétel (ÚJ, 2026-09-02)

⭐ **2026-09-02 — az e-mail méret-beállítás SZEMANTIKÁJA mérve:** az
`EmailExportSize` **közvetlen képpont-érték** (a hosszabb oldal), **nem**
listaindex, és az alapértéke **480** — három független helyen kiolvasva
(`0x006e1756`, `0x006e3f2b`, `0x00743094`). A `0` jelentése **eredeti méret**
(`option_useorig`); nem nulla értéknél az `option_imagesizelimit` **és** az
`option_estimate` is megkapja. Az `EmailSinglePicture` **kapcsoló**, nem méret:
egy kép + bekapcsolt állapot ⇒ a méret 0 lesz. Az `EmailMovie` az
`option_preservemovies`-t állítja; a mellékletek a `temp\email\` mappába
kerülnek. **Nálunk ez szerkezetileg más** (két ötfokozatú index-csúszka,
kitalált értékekkel, és a mért 480 elő sem fordul a listánkban) → **#2020**.

1. **Mik a Beállítások ▸ E-mail lap csúszkájának LÉPÉSEI?** Az olcsó lánc
   kimerült: a lap natív Win32 erőforrás, ezért sem a `.tre`, sem a
   `respack.yt`, sem a `stringres` nem tartalmazza; a `%d pixels (for e-mail)`
   sablon megvan a PE sztringtáblájában, de a számot futásidőben kapja, és
   statikus méret-tömb nincs a binárisban (végigkeresve). **Megszerzés:**
   egyetlen képernyőkép a futó Picasa `Eszközök ▸ Beállítások ▸ E-mail`
   lapjáról. Jegy: **#2020** (`blocked` + `felhasználóra-vár`).

### [picasa-beepitett-webszerver.md](picasa-beepitett-webszerver.md) — nincs nyitott kérdés (ÚJ lap, 2026-09-02)

⭐ **2026-09-02 — a Picasa 3 BEÉPÍTETT HTTP/WebDAV-kiszolgálója feltárva.** Az
eredeti **hallgatózó kiszolgálót** futtat: HTTP Basic hitelesítés
(`WWW-Authenticate: Basic realm="Picasa"`, jelszó a `LANPassword`-ből, a
felhasználónév fixen `picasaserver`), WebDAV (`OPTIONS`/`PROPFIND`, 13 `D:*`
elem, a megosztás `\\localhost\picasa`, a DAV-ág **80-as portot** igényel),
**14 végpont** (`/albumlist` … `/dbdebug`) plusz `/repost` és `/upload`,
kép-végpontok (`image/`, `thumb/`, `sthumb/`, `original/`), két hibakereső lap
(a `/dbdebug` **adatbázis-böngésző**, a `/uidebug` rajzolási időmérésekkel), és
egy LAN-hirdetés, ami **gépnevet és felhasználónevet** tesz a hálózatra
(`0x00937800`). Külön beérkező felület a **`picasa://` URL-séma**, amelynek egy
ága **külső URL-ről tölt be bővítményt**. **Nálunk mindebből semmi nincs
(mérve), és a javaslat: ne is legyen** → **#2023** (döntés-jegy, őr-teszttel).
Melléklelet: a `/filesigs` `text/plain` mezőlistája **független** megerősítése
a fotó-rekordunknak — és a **`flip` mező negatív eredmény**
(`imagedata_flipped.pmp`: 3 011/3 011 üres; a 859 fájlos ini-korpuszban 0 db
`flip=` sor).

### [binaris-regeszet-modszertan.md](binaris-regeszet-modszertan.md) — nincs nyitott kérdés (ÚJ szakasz, 2026-09-02)

⭐ **2026-09-03 (22. szakasz) — MEKKORA a 18. szakasz hibája? Lemérve.** A 18.
kimondta a szabályt (*elemnév és cím egy szakaszban*), de senki nem mérte, hány
elemet érint — pedig a szám egy KÖZÖLT mutatóban ül. A 168 „feltáratlan" elemből
**50 (30%) teljes néven szerepel** egy kézzel írt spec-lapon; 41 dedikált lapon
is. **Három mechanizmus rejti el a bizonyítékot:** (1) nincs horgony a
szakaszban (a `biztonsagi-mentes.md` 10.3 tizenkét `publish/…` feliratát a
`panel-feliratok-hu.tsv`-sorszám igazolja, ami nem illeszkedik a mintára);
(2) a lap a **levélnevet** használja (a `konyvtar-ablak-meretek.md` 4. szakasza
mind a 18 lebegő gomb geometriáját megadta `thumbui/` előtag nélkül —
**egyetlen sort sem** talált a detektor); (3) **kézi `hianyzik` felülbírálás
árnyékolja** a gépi `lekutatva`-t (hat elem; kettőnek a saját megjegyzése
mondta ki, hogy „De FELTÁRVA"). ⛔ **Egy aggály ELVETVE:** a részsztringes
keresés a mai 88 `lekutatva`-ból **nullát** igazol hamisan (szóhatáros
újrafuttatás: 88/88). **Javítva ebben a körben:** 37 felülbírálás + a
`konyvtar-ablak-meretek.md` 4. szakasza teljes nevekre —
**feltáratlan 164 → 128** (ugyanazzal a QML-fával mérve). Jegy: **#1878**,
maradék: **#2093**.

⭐ **2026-09-03 (21. szakasz) — a Picasa UTF-8 rétege: a TELJES futásidejű
thunk-tábla.** A 20. szakasz receptjét az egész `.text`-en végigfuttatva
kiderült, hogy nem elszigetelt trükk: a Picasa **68 ANSI Win32 API-t** vezet át
globális mutatókon (`0x00d694bc`–`0x00d695c8`), és induláskor a `GetVersion`
magas bitje szerint tölti fel őket — 9x-en a nyers `…A` importtal, NT-n **saját
UTF-8 burkolóval** (`MultiByteToWideChar(CP_UTF8= 65001)` → `…W`). A lap most a
**teljes 68 soros táblát** tartalmazza (mutató · DLL · `…A` név · IAT-rekesz ·
burkoló), a szkript pedig a privát repóban él (`eszkozok/rt_thunks.py`).
**Két következmény:** (1) minden `call dword ptr [0x00d69…]` egy lépésben névre
hozható — a „nem oldható fel, futásidejű mutató" indoklás ma **hiba**, nem
korlát; (2) a Picasa belső sztringjei NT alatt **UTF-8-asak**, ami a
`.picasa.ini`, a `files.txt` és a `watchedfolders.txt` kódolására nézve
**normatív**.

⭐ **2026-09-02 — egy ELVETETT mérőszám, kontrollal megbuktatva (19. szakasz).**
A kézenfekvő ötlet — „ha egy felületi elem neve nincs benne a `Picasa3.exe`-ben,
akkor halott" — **használhatatlan**: a 2 020 elemű leltárból **935 (46,3%)** és
a lefedettségi hiánylista 363 tételéből **78 (21,5%)** esne bele, köztük a
`thumbui/loupehit` (a rács-nagyító, amit a #1911/#1951 épp megépített) és a
`printpanel/printsizes`. Két megnevezett hamis-pozitív osztály: a **dinamikusan
összerakott név** (`quickcontainer%d`, `palette_%d`, `tabpanel%d`, `%s_label` —
a formátumsztringek mérve megvannak) és a **szerkezeti gyerek** (`-label`,
`_icon`, `_group`, `_well`). A helyükre egy **négyfeltételes** szabály lépett
(`m_hidden` + nulla névtalálat + nincs névelőállító sablon + a felirat sincs
sehol); ezt a 2 020 elemből **három** állja ki: a `thumbui/lightbox_esolo_button`
(„Search All"), a `thumbui/lightbox_esolo_text` („No results found in this
album") és a közös szülőjük, a `thumbui/albumsback` — egy **album-szűkített
keresés üres állapota**, amit a kódból kivettek, a felületleíróban viszont
bennmaradt. Jegy: **#2027**.

### [picasa-keptalca.md](picasa-keptalca.md) — nincs nyitott kérdés (ÚJ szakasz, 2026-09-02)

⭐ **2026-09-02 (19. szakasz) — a tálcának SAJÁT kijelölése van.** A tulajdonos
képernyőképe (futó Picasa 3) mutatja: a tálcán a középső kép **kijelölve**. A
bináris ezt megmagyarázza: a tálca **ugyanolyan `CSelectionNode`**, mint a
fotórács (`[ebx+0xea4]`), és a számlálója (`0x00716cb0`) **elemenkénti**
jelzőt olvas (`cmp byte ptr [ecx+0x5a], 0`). Ezért van értelme a helyi menü
„Kijelölés eltávolítása" tételének. **Nálunk a tálca bélyegképein egyetlen
kattintás-kezelő sincs** (mérve: `TrayBar.qml:503`, a csíkban csak jobb gombos
`TapHandler` a 250. sorban), és a tálca parancsai a **RÁCS** kijelölésén
dolgoznak → **#2039**.
⛔ **Ugyanaznapi SAJÁT HELYESBÍTÉS:** a #2039 először azt állította, hogy a
kijelölés keretének színe „NINCS MÉRVE". **Téves** — a
`runtime/constants.ui`-ban áll, a fájl saját megjegyzésével együtt:
`thumbsel_color1=#009EFF` (kívül) / `thumbsel_color2=#FFFFFF` (belül), és a
`design-guide.md` 63. sora **2026-08-06 óta** dokumentálja (#384); a rácsunk
meg is valósítja. **Módszertani tanulság:** a `runtime/*.ui` szövegfájlok a
bizonyítéklánc **elejére** tartoznak — a Picasa a felület számadatainak egy
részét szándékosan kiszervezte oda.

### [design-guide.md](design-guide.md) — nincs nyitott kérdés (ÚJ szakasz, 2026-09-02)

⭐ **2026-09-02 — a `runtime/constants.ui` ÁTVILÁGÍTVA.** A fájl **46 élő
kulcsot** tartalmaz; ezek közül **csak a 23 szín-kulcs mérhető** azzal, hogy
megkeressük az értéket a `src/`-ben (egy `#634B45` megkülönböztető, egy puszta
`22` bármire illeszkedik — a számos kulcsokról ezért **nem állítunk semmit**).
Mérés: **11 megvan** a kódunkban, **3 hatókörön kívül** (Mac-változatok,
Linux-first projekt), **9 hiányzik**. ⚠️ A legfontosabb hiányzó az
**`alayout_titleColor=#634B45`** (mappa-cím): ugyanannak a blokknak a betűjét
(`Georgia`) és méretét (20) **már átvettük** (`LightboxHeader.qml:96–97`), a
színt nem — nálunk `Theme.folderTitle` → `ink` → `#1c1b19`. ⛔ **A lap
korábbi `✅` jelölése ezen a soron félrevezető volt** (a hármasból kettő volt
kész), javítva. A maradék nyolc színre a **szerepük NINCS MÉRVE** a mi
felületünkön — vakon átvenni tilos. Jegy: **#2043**.

### [pmp-database.md](pmp-database.md) — a BORÍTÓ-kérdés lezárva (2026-09-02)

⭐ **2026-09-02 — az ÖTÖDIK bélyegkép-tár: `albums.db`, a mappák BORÍTÓJA.**
A tulajdonos képernyőképe mutatta, hogy a bal hasáb fastruktúrájában **fotó-kupac**
áll a sárga mappaikon helyett. Nem futásidejű: **mappánként egy mentett
raszter**. A tár-nevek egyetlen függvényben (`0x00415790`) állnak, és az
`albums.db` **együtt szerepel** a másik néggyel (`m_albumThumbs`). Kapcsoló:
`Preferences\ShowAlbumThumbnails2` (a Nézet menü „Indexképek megjelenítése a
könyvtárban" pipája, alapérték **0**). **A formátum NEM JPEG**: 8 bájt fejléc
(`uint32 width`, `uint32 height`) + `w*h*4` bájt **BGRA** — a
`8 + w*h*4 == hossz` azonosság **37/37** élő bejegyzésre teljesül, `FFD8`
kezdet 0/37. Aránytartó (leghosszabb oldal 72–119 px), **valódi
átlátszósággal** (1 400–2 200 átlátszó képpont mintánként). Kirenderelve:
**egy elülső fotó + 1–3 mögötte, kifordítva** ⇒ a „legrégebbi kép mini
ikonja" feltevés **megdőlt**. A rés-index az **albumtábla sorindexe**, és a
lemezes mappák is albumként szerepelnek (élő minta: `wallpapers`, `space`,
`volt` a `albumdata_filename`-mel). Nálunk **minden sor ugyanaz a mappaikon**
(`FolderTreeItem.qml:101`) → **#2049**.

**A kérdés — „MELYIK fotókból áll a kupac, és milyen sorrendben?" —
2026-09-02-án LEZÁRULT** (`pmp-database.md` **7. szakasz**, jegy **#2049**):
az összeállító a `0x00423780` (2167 b), amit a `0x00423500` hív. A lista
**első `min(N,4)`** eleme kerül a kupacba (`0x004237ab` `cmp eax,4`), hátulról
előre rajzolva, tehát a **lista első eleme kerül legfelülre**
(`0x00423f45`–`0x00423f4d`). Az elrendezés **albumonként determinisztikus**:
`srand(rés-index ^ 0x133475)` (`0x00423a2b`), MSVCRT-generátorral
(`0x00c08221`). Fotónként: forgatás **±0,1 rad = ±5,73°** (a legalsó fotó
forgatás nélkül), oldaleltolás `±4·i`, függőleges `5i…9i`. A vászon a kupac
**befoglaló téglalapja** (`0x00423f70`). A lágy árnyék **sugara 5 px**
(mérve: ~5 képpontos alfa-lefutás 37 valódi borítón), **alfája 153**
(`0.6 × 255`, `0x00a6e32e`). Megdőlt: „a legrégebbi képből készül".

### Nincs nyitott kérdés

`filterdesc-registry.md` · `ui-audit-context-menus.md` · `ui-audit-mainwindow.md` · `picasa-native-filter-registry.md` · **`ui-audit-editor.md`** · és a lenti táblák
minden további lapja.

## Formátum-specifikációk (adatfájlok, erőforrások)

| lap | miről szól |
|---|---|
| [picasa-ini-format.md](picasa-ini-format.md) | A `.picasa.ini` — az igazságforrás, round-trip szabályokkal |
| [picasa-beepitett-webszerver.md](picasa-beepitett-webszerver.md) | **A Picasa 3 beépített HTTP/WebDAV-kiszolgálója** — a bekapcsoló beállítások (`AllowRemoteWeb`, `LANShareAlbums`, `LANPassword`, `DAVSupport`, `EnableTester`, `UIProfiling`), a 14 végpont teljes listája, a kép- és bélyegkép-URL-ek, a WebDAV-válaszok, a LAN-hirdetés mezői, a `text/plain` metaadat-alak (album + fájl), és a `picasa://` URL-séma öt művelete. Döntés: **nem építjük meg** (#2023) |
| [pmp-database.md](pmp-database.md) | A központi adatbázis (`db3` / PMP) — **és a bélyegkép-gyorstár blokkfájl-formátuma**: a négy szint mért mérete (72/144/288/640 px), az `*_index.db` három vektora (`20 + 12n`, 11 fájlon mérve), a slot ↔ `thumbindex.db` sorindex kötés, a kulcsvektor **azonos résterű tárak közt bitre azonos** (⇒ nem blob-ellenőrzőösszeg), az elavult sorok mért veszélye és a `CBlockFile` bináris oldala |
| [picasa-arcfelismeres.md](picasa-arcfelismeres.md) | **Az arcfelismerés TELJES működése** — a három réteg és kapcsolóik, a két küszöb-létra, a KÉT ini-írási útvonal (`facedata`!), a `db3` arc-oszlopai élő adaton mérve, a három romboló művelet, a verzió-migráció |
| [picasa-imagedata-rekord.md](picasa-imagedata-rekord.md) | Az `imagedata` rekord — belső kép-nyilvántartás |
| [picasa-respack-format.md](picasa-respack-format.md) | `respack.yt` — a bináris erőforráscsomag (megfejtve) |
| [picasa-program-resources.md](picasa-program-resources.md) | Erőforrás- és formátum-leltár (gombok, web-export, plugin-ök) |
| [picasa-fen-dialogs.md](picasa-fen-dialogs.md) | A `.fen` dialógus-definíciók |
| [picasa-web-template-nyelv.md](picasa-web-template-nyelv.md) | A web-export sablonnyelve |
| [picasa-exe-strings.md](picasa-exe-strings.md) | Bináris string-bányászat |
| [picasa-beepitett-konyvtarak.md](picasa-beepitett-konyvtarak.md) | A Picasa beépített nyílt forráskódú könyvtárai |
| [picasa-linux-mod.md](picasa-linux-mod.md) | **A Picasa Linux-módja** — mit tiltott le maga a Google Wine alatt, és miért |

## Képfeldolgozás (szűrők, render)

| lap | miről szól |
|---|---|
| [filters-decoded.md](filters-decoded.md) | A szűrők visszafejtett modelljei + golden-verdiktek |
| [filterdesc-registry.md](filterdesc-registry.md) | A `filterdesc.xml` — csúszkanevek, tartományok, alapértékek |
| [picasa-native-filter-registry.md](picasa-native-filter-registry.md) | A natív szűrő-tábla: 49 név → kezelő + képen belüli vezérlők |
| [picasa-native-filter-workers.md](picasa-native-filter-workers.md) | A natív szűrők munkafüggvényei — hívási térkép |
| [histogram-reference.md](histogram-reference.md) | Hisztogram-referencia és összevetés |

## Felület — KÖTELEZŐ méretspecifikációk

Ezek **normatívak**: a felületnek pontosan ezeket kell követnie.

| lap | miről szól |
|---|---|
| [szerkeszto-panel-meretek.md](szerkeszto-panel-meretek.md) | A szerkesztő bal panelje (201 elem) — **az 1. fül gombsorrendjének EGYETLEN érvényes forrása** |
| [szerkeszto-felso-sav.md](szerkeszto-felso-sav.md) | **A szerkesztő FELSŐ SÁVJA (`oneup_controls`)** — a hét vezérlő képpontos geometriája két, egymást igazoló forrásból; a „paletta-ikonos gomb" = `quickupload` (Web Albums Drop Box); a filmszalag **hét férőhelyes**, az aktuális kép **mindig középen**; a kijelölés-keret `#009EFF`+`#D4D4D4`; a hisztogram-doboz horgonya `root.alsó − 95` |
| [getmore-klipgyujto-mod.md](getmore-klipgyujto-mod.md) | **A „Továbbiak…" klip-gyűjtő MÓD** — két belépési pont (kollázs, filmkészítő), a visszatérő gomb **pontosan három** felirata, a kijelölés a **képtálcán át** megy a projektbe, a ✕ **csak elrejti** a sávot (`hidetarget`), és a sáv **eltakarja** a Nyomtatás/E-mail/Export/Feltöltés sort |
| [racs-nagyito.md](racs-nagyito.md) | **A rács-NAGYÍTÓ** — kör alakú üveglencse **103 × 103** (belső 65), a `loupe_sm` a **belső rétege** (51 × 51); a kurzor **közepére** ül; **áttűnéssel** jelenik meg (0,4 be / 1,2 ki, alfa 1…256); **nincs saját egérmutató** (mért negatív); nálunk a réteg megvan, a **kapcsoló hiányzik** |
| [racs-ures-allapot.md](racs-ures-allapot.md) | **A rács ÜRES ÁLLAPOTA** — a `lightbox_bgtext` **hét** kontextus-szövege (ebből négy megnyugtató, nem hibaüzenet), a választó `0x00676b10` és a `LastUserESState`-től függő márkaváltás („Picasa Web Albums" ↔ „Google Photos"); és hogy a **„Keresés mindenhol" gomb HALOTT** az eredetiben (négy lekérdezés-alak + pozitív kontroll) |
| [biztonsagi-mentes.md](biztonsagi-mentes.md) | **A biztonsági mentés MŰKÖDÉSE** — `backups.xml` a **`db3`** mappában (`setname` · `diskroot` · `filter` · `type`), **három tartalom-mód** (`bkallfiles`/`bkonlypics`/`bkonlyexif`), a célmappába írt `files.txt`, a honosított alapértelmezett mappanév, a lemezhely-ellenőrzés — és hogy **ugyanaz a függvény írja a `replicates.xml`-t is** |
| [ajandek-cd-kimenet.md](ajandek-cd-kimenet.md) | **Az Ajándék-CD / mentő lemez KIMENETE** — a lemez **önjáró**, Windows ÉS macOS vetítővel és visszaállítóval, telepítővel és letöltő-linkkel; az `autorun.inf` **pontos sablonja**; a **16 kimeneti beállítás** teljes listája; és hogy a lemez mappanevei **honosítottak** („Biztonsági mentés" / „Képek") |
| [konyvtar-ablak-meretek.md](konyvtar-ablak-meretek.md) | A könyvtár-ablak (156 elem) |
| [picasa-konyvtar-eszkoztar-viselkedes.md](picasa-konyvtar-eszkoztar-viselkedes.md) | A fő eszköztár öt gombjának VISELKEDÉSE (Import, Új album, nézetváltó pár, Nézet-beállítások, Webkamera) — nem geometria |
| [jobb-fiok-meretek.md](jobb-fiok-meretek.md) | A jobb oldali fiók („Metaadatok", 80 elem) |
| [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) | A fő ablak elrendezése — a forrásból; **és a MEGŐRZÖTT állapot** (2026-09-03): `Preferences/mainwinpos` = `rect(%ld %ld %ld %ld)` + `mainwinismax`; az induláskori állapot-alkalmazó `0x0040bf70`; a `HLISTDIV=0.216406` / `VLISTDIV=0.1` **beírva, de SOHA nem olvasva** (három független negatív) — csapda, ne valósítsuk meg; a bal panel osztója a `HLISTOFFSET2=240`, ami **kódból is** megvan (`0xcf48b0`), és a kezelőjében (`ytSplitterOffsetHandler`, `0x009d9d80`) **nincs beégetett alsó/felső határ** |

## Felület — auditok és lefedettség

| lap | miről szól |
|---|---|
| [ui-audit-editor.md](ui-audit-editor.md) | A szerkesztőpanel: fülek, effekt-csempék, dialógusok |
| [ui-audit-mainwindow.md](ui-audit-mainwindow.md) | Főablak: mappafa, eszköztár, tálca, görgetősáv |
| [ui-audit-menus.md](ui-audit-menus.md) | A teljes menürendszer |
| [ui-audit-context-menus.md](ui-audit-context-menus.md) | Jobbklikkes helyi menük |
| [ui-lefedettseg.md](ui-lefedettseg.md) | Az eredeti panelek ↔ a mi QML-fánk megfeleltetése |
| [picasa-beviteli-mezok.md](picasa-beviteli-mezok.md) | Beviteli mezők és párbeszédpanelek |
| [picasa-gyorsbillentyuk.md](picasa-gyorsbillentyuk.md) | **A gyorsbillentyűk teljes tára ÉS a funkciójuk** — a `Picasa3i18n.dll` 48 rekeszes `SHORTCUTS.XML` keymapje (nyolc nyelv, **magyar nincs** → az angol alaptábla fut); a menüsáv 32 és a helyi menük 44 rekordja **parancsazonosítóval és rekordcímmel**; a jelzőbájt három bitje mérve (a 2. bit fordított: `Ctrl` akkor van, ha 0); a keymap kommentjei **három helyen elavultak** (`Ctrl+S`, `Ctrl+T`, `Ctrl+W`); és a mai kiosztásunk tételes összevetése (34 egyedi kombinációból 18 megvan / 2 eltér / 14 hiányzik). Jegy: **#1154** |

## Viselkedés és funkciók

| lap | miről szól |
|---|---|
| [picasa-create-features.md](picasa-create-features.md) | A „Létrehozás" menü funkciói |
| [picasa-kollazs-felulet.md](picasa-kollazs-felulet.md) | A Kollázs teljes működése — parancstábla, gyűrű, helyi menük, kimenet |
| [kollazs-atvilagitas.md](kollazs-atvilagitas.md) | **A Kollázs TELJES átvilágítása** — eredeti / nálunk / jegy minden vezérlőre, a panelen kívüliekkel; és kimondva, amit NEM néztünk meg. *(2026-08-21: a 9. szakasz átvizsgálva — két tétel ELAVULT volt (a lap 1. szakasza már lezárta őket), a `.cxf` visszaolvasása MEGMÉRVE (`CCollageParser`, a mi olvasónk lefedi a teljes szótárt); valóban nyitott már csak a **futó program** viselkedése és a **betöltési sorrend nagy albumon**.)* |
| [kollazs-panel-ui-spec.md](kollazs-panel-ui-spec.md) | **A Kollázs-panel MEGVALÓSÍTÁSI UI-specifikációja** — elemfa, `objectName`-ek, a `.tre` kényszereiből levezetett méretezési törvény, vezérlő-API, teszt-szerződés, jegyekre bontás |
| [export-parbeszed.md](export-parbeszed.md) | **Az „Exportálás mappába" párbeszéd** — a `export.fen` leíró, mind a 28 magyar felirat, a kötések, a 9 megőrzött beállítás, és a képminőség öt fokozatának **számértéke a binárisból** |
| [kollazs-eletciklus.md](kollazs-eletciklus.md) | **A kollázs életciklusa** — a három állapot, az átmenetek, mindhárom párbeszéd szó szerint |
| [picasa-bezaras-es-kilepes.md](picasa-bezaras-es-kilepes.md) | Mit zár be az „X" — bezárás és kilépés; a kilépési kapu 8 lépése, a négy kilépési figyelmeztetés (feltöltés, import, aktív szerkesztő-eszköz, `WarnClosePlugins`), minden bezáró gomb névparancsa, kilépéskori mentések. Nyitva: az `exit_nag` kapcsoló hatása |
| [picasa-nyomtatas.md](picasa-nyomtatas.md) | A nyomtatás — panel (61 elem), 17 méret, beállítások |
| [picasa-email-kuldes.md](picasa-email-kuldes.md) | E-mail-küldés — választó, beépített Gmail-szerkesztő, beállítások |
| [picasa-importalas.md](picasa-importalas.md) | Az importálás panelje — tipp-sor, kártyatörlés-figyelmeztetés, hibák |
| [picasa-elso-inditas.md](picasa-elso-inditas.md) | **Az első indítás `initialscan` panelje** — migrációs és tiszta-telepítés változat, geometria, a kihagyhatatlan választás |
| [lanc-szakadasok-leltar.md](lanc-szakadasok-leltar.md) | **Ahol a háttér kész, de a felület nem éri el** — mért leltár: a regisztrált vezérlők közül egy sem holt, de több tucat tag elérhetetlen a QML-ből, jelentős részüket csak a teszt hívja. A pontos, mindig friss számot a lap generált blokkja és a `scripts/kepesseg_or.py` futásának kimenete adja — ide szándékosan nem írjuk ki (#1508, #1512). Négy megerősített lelet (Nyomtatás · arckeresés-indítás · e-mail küldés · visszavonás-gombok) és a naiv `.tagnév` keresés csapdája (négy név két gazdával). Jegyek: **#1472**–**#1476** |
| [nema-tagok-1052.md](nema-tagok-1052.md) | **A #1052 huszonhat néma vezérlő-tagjának döntése** — tagonként HIBA / SZÁNDÉKOS / HALOTT, kétféle alakú kereséssel igazolva. A jegy **„gomb aktív állapota" feltevése MEGDŐLT**: a #116 az egygombos javításokról szándékosan levette a „benyomva" állapotot, a csempe a `*Enabled` párt köti — a három `*Active` property maradék. Egy új, felhasználót érintő lelet: a vágás „Alaphelyzet" gombja csak a KIJELÖLÉST törli, a mentett vágást nem. Négy tag azóta bekötést kapott (#1472, #1473), egy soron a jegy tévedett (`setSimplified`). Jegy: **#1052** |
| [picasa-szinkereses.md](picasa-szinkereses.md) | **A hat szín szerinti keresés MEGFEJTVE** — NEM az átlagszínt osztályozza: telítettséggel súlyozott **hue-hisztogram** az egész rasztról, hét vödörrel, a legnagyobb nyer (`0x009dbd10`). Küszöbök: `MAX==0` és `S<=50` képpont kimarad; `b=H/10`; mért **rés** 353,0–358,8°-nál; akromatikus ⇒ mind a három token. Jegy: **#1480** |
| [picasa-tartalomkulcs.md](picasa-tartalomkulcs.md) | **A tartalom-kulcs (`originfast`) — 10/10 igazolva** valódi fájlokon: `MD5(uint32_le(méret) ‖ első 16834 bájt ‖ utolsó 16834 bájt)` első 8 bájtja. Három téves jelölt mérve kizárva (`onlinechecksum` u32, `originhash` 0/32, `backuphash` u16). Jegyek: **#1481**, **#1482** |
| [picasa-mappanezet.md](picasa-mappanezet.md) | **A `Nézet ▸ Mappanézet` MŰKÖDÉS-specje — egy funkcionális félreértést javít**: ez NEM rendezés, hanem a bal hasáb **gyökere és hierarchiája**. A lapos↔fa **kizáró pár** (`[+0x9d]`), az „Egyszerűsített fanézet" viszont **független kapcsoló**, ami a `SimplifiedHierarchy` beállítással az `all` gyökeret **`watched`-re cseréli**. Hat gyökér-token, négy gyökér a helyi menüben, a fejlécfelirat („Alapértelmezett nézet" / „Sajátgép"), a `LastViewRoot`/`LastViewRoot2` tárolás, és a visszaesés a Sajátgépre hibaesetben. Jegyek: **#1407**, **#1454** |
| [picasa-mappakezelo.md](picasa-mappakezelo.md) | **A Mappakezelő TELJES specifikációja** — elrendezés és tervezővászon-geometria, az átméretezés szabályai (`winsize` → `SC_SIZE`), a fa és az öröklődő állapot, a három rádió, az arcfelismerés-kapcsoló, a három figyelmeztetés, az OK/Mégse delta-szemantikája, a Súgó URL-je |
| [picasa-keptalca.md](picasa-keptalca.md) | **A Képtálca (`scratch`, „Selection") MŰKÖDÉS-specje** — a döntő lelet, hogy a tálca **nem marad meg újraindítás után** (három független negatív ellenőrzés); a négy vezérlő felirat NÉLKÜL, csak ikon+súgó; a helyi menü **nyolc sora** (ebből csak kettő a `Tray::` névtérből); a bélyegképek **négyzetesek és középre vágottak** (16 mért eset, a méret-képlet NINCS MEG); a `scratch` a `scratchlabel` FÖLÖTT; az összecsukott mappa-token; **két külön** ürítés-megerősítés; a 36,5%-os doboz-kényszer; a `trayexec` adatvezérelt műveletsor; két negatív eredmény (a `.pbz` placement NEM az alap-sorrend, a `Tray contains:` hibakereső lap); **a rács osztásköze a két irányban AZONOS** (a #1914 „3 px sor / 0 px oszlop" kérése megdőlt, 18.) |
| [picasa-helyek-panel.md](picasa-helyek-panel.md) | **A Helyek panel (geocímkézés) MŰKÖDÉS-specje** — a `geotag=` kulcs alakja **kimérve** (`%lf,%lf`, mindig **hat tizedesjegy**; a korpusz 84/84 sora 6/6 jegyű) és a mi `format_geotag()`-ünk **19/84 (22,6%) értéket másképp írna** (→ **#2012**); a **két megerősítő kérdés MÉRT küszöbökkel** — hely megváltoztatása **> 20 kijelölt** elem (`0x00652585` `cmp ebx,0x14`), hely törlése **> 5 GEOCÍMKÉZETT** elem (`0x006527ad` `cmp esi,5`, a számláló `0x006524c0`) —, nálunk **egyik sincs** (→ **#2013**); a törlőgomb felirata **dinamikus** (`Clear %d Geotag(s)`); a beágyazott Google-térkép **kétirányú JS-hídja** teljes táblával (11 natív→JS hívás és a `geotag:` / `cleargeotag:` / `showphotos:` visszaút, mind **ellenőrzőösszeggel**, a parancskezelő a `0xca2470` vtable-ben); a buborékablak 12 felirata, köztük a **külön „Move" és „Put"** szöveg; és két negatív lelet: **a `picasa.setMapType` a v3-as szkriptben ÜRES FÜGGVÉNY** (a mentett térképtípus némán hatástalan — a v2-ben még működött), illetve a panelnek **nincs `respack.yt`-geometriája** |
| [picasa-menu-leltar.md](picasa-menu-leltar.md) | **A menüsor gépi leltára a binárisból** — 189 tétel 18 `eMenu*` névtérben; a lefedettségünk 150/189 (79%), a 39 hiányzó három csoportban (14 hatókörön kívül, 18 érdemi, 1 almenü). Jegy: **#1397** |
| [picasa-menu-parancsok-viselkedes.md](picasa-menu-parancsok-viselkedes.md) | **A menüparancsok VISELKEDÉSE** (#1434) — a `.fen` párbeszédleírók mint leggyorsabb út; az effektus-vágólap **nem** rendszer-vágólap; a dátum-állítás **nem** fájlidőt ír; a menüsor **kilenc almenüje**; a Beállítások 8 füle és ~78 vezérlője (köztük a nyomtatás **Lanczos-3/8** választása); a Személyek kezelése hat azonosító-mezője; és a beállítások tárolási helye (`SOFTWARE\Google\Picasa\Picasa2\Preferences\`). **33. tétel (2026-08-30): a KÉP menü teljes cmd→kezelő térképe** (16 + 4 geotag-parancs, a kép-menübeli Szépia/Fekete-fehér `0x9d4a`/`0x9d4c` külön batch-parancsok), a Csoportos szerkesztés **kétágú mintája** (szerkesztő-navigáció `0x579330` vs. batch `0x5fe370`), a FILM_GRAIN **Shift-függő grain/grain2** váltása (`GetAsyncKeyState(0x10)`), az AUTO_REDEYE keret-útja (`0x602100(0x5f39d0)`), és a Geotag almenü: Google Earth-ellenőrzés CLSID-vel + InstallEarth-párbeszéd, a GEOUNTAG megerősítője (`ClearGeoTag::warn`). **34. tétel (2026-08-31): az öt lefedettségi parancs** — forgatás (fix 90/270°, háttérszálon, `rotate=` = negyedfordulat-tároló, **#1162 lezárva**), Undo All Edits (egy/több/film megerősítés-hármas, `redeye`/`retouch`/`picnik` token-törlés), Unhide/Hide (`hidden=yes` kulcs, online-album-megerősítés), Reset Faces (sima = kijelölés, kérdés nélkül; Ctrl/Shift = könyvtárszintű FIGYELEM-párbeszéd). **35. tétel (2026-08-31): Poszter (papírméret-lista nyelvi feltétellel), képernyővédő (saverlist.txt a #db3 mappában, telepítés-ellenőrzés, rundll32-install), TiVo (Windows-only akció — hatókörön kívül-javaslat), keresés-mentése (1000-es küszöb, „Create Album" gomb), biztonsági mentés (backup.xml + backuphash + il_BurnPanel). **36. tétel (2026-08-31):** a névcímke-letöltés **halott menütétel** (`RemoveMenu` feltétel nélkül); a Mappakezelő **engedélyezési kapuja** (szürke, amíg a szerkesztő-előnézet aktív) és a `+0x34a4` holt jelzőbit; a lista-rendezés **három registry-kulcsa** (`datesort` = teljes módszám, `peoplesort`, `albumlistflip`), a „méret" = **64 bites bájtösszeg**, és hogy a rendezés-tételek **három menüben** élnek (a menüsáv Nézet menüjében is — a #1454 megjegyzésének helyesbítése). **37. tétel (2026-08-31):** a jobb fiók négy lapja **kizáró rádiócsoport** (minden ág elrejti a másik hármat), a menü→névparancs híd (`0x0065ab50`), az `ID_CAPTAG` **két menüben két külön azonosítóval** (`0x9d2c` vs `0x9de4`), és az `active_metadata_tab` kulcs, amelynek **három olvasója és nulla írója** van. **38. tétel (2026-08-31):** a „Rejtett képek" bekapcsolása **jelszót ajánl** (`IDS_PROMPT_HIDDEN_PWD_*`, „Add Password"/„Don't Add Password", `DoNotConfirmHiddenPwd`); az Idővonal **teljes képernyős bemutató-mód** a Flipbookkal közös kezelőn; a háttérkép **BMP-t ír** a `Picasa\Backgrounds`-ba és **középre** teszi (`WallpaperStyle=0`, `TileWallpaper=0`). **39. tétel (2026-08-31, az első UI-lefedettségi kör):** a `printoptions` panel **tizenegy `Preferences\printoptions::*` kulcsot** ír (felirat forrása/helye/betűje/mérete/színe/tördelése, szegély megléte/vastagsága/színe/csak-alul/egyenletes); a fogyasztó a nyomtatási rajzoló (`0x00776180`); indexkép-nyomtatásnál a panel **tiltva**, saját magyarázó szöveggel. **39.8 (2026-09-03):** a panel **felirat-rétege külön fájlból** jön
(`i18n\printoptionstext.xml`, `0x0085d550`), és a fájl **kicsomagolva megvan**
(`referencia/i18n-hu/printoptionstext.xml`, 27 bejegyzés) — négy felirattal,
amit a lefedettségi lista nem nevezett meg (`border_size_label`,
`border_none_label`, `border_max_label`, `caption_color_label`);
⭐ **a szegélyvastagság CSÚSZKA** („Egyik sem" … „Maximális",
`printborderslider/scaleslider`, `Property slider 2`, saját névtérben a `root`
alatt), nem számmező; a két legördülő (`fontfamily`, `sizelist`) **runtime
töltődik** (`maxrows 7`, tételek sem a `.tre`-ben, sem az i18n-fájlban) ⇒ a
betűméret-lista blokkolt kérdése két további forrásra nézve negatív;
⚠️ **hibás hivatalos szöveg:** az `apply`/`ok` buboréksúgója
nyomtatás helyett **„a Google Fotókra"** hivatkozik — hogy fordítási hiba-e
vagy az angol is ilyen, **NINCS MEG** (angol i18n-csomag nincs a kutatási
anyagban); ezt a két szöveget **nem vesszük át**. Jegy-komment: **#1780**.
**39.3–39.7 (2026-09-02):** a **Mégse VISSZATÖLT** (a vezérlők azonnal írnak, az „Alkalmaz" csak újrarajzol, az ablak X-ével bezárva a módosítások BENT MARADNAK); a két rádiócsoport értékkészlete **0–3** (nincs szöveg/képfelirat/fájlnév/Exif) és **0–2** (kép alatt/képen/szegélyen); mind a tizenegy kulcs **alapértéke** kimérve (`textsize`=12, `bordersize`=10, **`evenborder`=1** az egyetlen bekapcsolt), a `.tre` `setpressed` értékeivel keresztmérve — egy eltéréssel (`wrap_checkbox`), ahol a **beállítás nyer**; ⛔ helyesbítés: a `usefilename`-nek **VAN** felirata („Fájlnév"); ⛔ negatív: a betűméret-lista **nem** a filmkészítő statikus táblájából jön. Nyitva: honnan töltődik a lista. **40. tétel (2026-08-31):** a `printpanel` **DPI-őrt** tartalmaz („Smallest picture: %d pixels/inch.", „%d small picture(s) found.", „Please review before printing."), a nyomatméretet a `Preferences\PrintLastSize` **tartósan** őrzi, a példányszám **képenkénti**, és a „Szegély- és szövegopciók" gomb nyitja a `printoptions`-t. **41. tétel (2026-08-31):** az `acquirepanel` importálás — `AcquirePath` / `LastImport%x` / `acquireUseSubFolder` kulcsok, az almappa-elnevezés **három módja** (kézi cím / „Date Taken (YYYY-MM-DD)" / mai dátum), kártya-törlés megerősítéssel; **és a lecke: a „hiányzik" oszlop JELÖLT, nem ítélet** — tíz elem téves riasztás volt. **42. tétel (2026-08-31):** a `collagepanel` megfeleltetési sora **elavult** volt (egyetlen fájlra mutatott, és azt állította, hogy nincs interaktív szerkesztő) — **egy sor 38 helyesen megvalósított elemet rejtett el**; javítás után a tábla 87 → 132 párosítva, 425 → 397 hiány. **43. tétel (2026-08-31):** a megfeleltetési fájl **mind a 74 sorának** átvilágítása — a `collagepanel` volt az EGYETLEN elavult (negatív eredmény); és a gyorscímke-beállító az eredetiben **TÍZ** helyet ad (`edit_0..9`, `cmp eax, 0xa`), nálunk nyolc. **44. tétel (2026-08-31):** a `buttonmgr` — a Picasa gombsávja **BŐVÍTMÉNY-RENDSZER** volt (`http://picasa.smo/buttons`, „Launch Picasa and import buttons?", `#buttons\` mappa); a testreszabás a `Preferences\Buttons\UserConfig` és `…\Exclude` kulcsokban él. **45. tétel (2026-09-01):** a mérés **VAK a csoportosztásra, a sorrendre és az elrendezésre** (az elválasztókat kidobja) — a „hiányzik = 0" csak annyit jelent, hogy *nincs hiányzó vezérlő*; plusz egy **tudott eltérések** táblája a kimondatlanság ellen. **46. tétel (2026-09-01):** a `faceheaderpanel` javaslat-munkafolyamata **négy külön parancs** (`selectsug`/`confirmsug`/`sug_filter`/`moresug`), és a „További javaslatok keresése" **újra-klaszterezés**, nem szűrő; a lelet a #26-ra ment, mert arcfelismerő motor nélkül nem valósítható meg. **47. tétel (2026-09-01):** a `choose_mail` levelezőprogram-választó (`EmailPrepType`, `DoNotPromptForEmailPref`) — **és egy NÉMA BEÁLLÍTÁS nálunk**: a „Let me choose each time" rádiógomb tárolódik, de a `sendRows()` nem olvassa el. **48. tétel (2026-09-01):** a **néma beállítás** mint önálló hibaosztály — a két meglévő őr (`nema_jelzesek.py`, `nema_slotok.py`) **mérve NEM fogja meg**; „a beállítás él, csak nem hat". **49. tétel (2026-09-01):** KÉT SAJÁT HELYESBÍTÉS — a `GetSubMenu(…,2)` a menü **fogantyúját** adja, nem a tétel helyét (#1766 leállítva); és a #1798 valódi oka nem a beállítás olvasása volt, hanem hogy a `sendRows()`-nak **nem volt hívója** ⇒ néma vezérlőnél a **teljes láncot** kell mérni, mindkét irányból. **50. tétel (2026-09-01):** a `publish` **HÁROM panel egy névtérben** (mentés · Ajándék-CD · webre töltés), és csak a harmadik halott; a mentés **nevesített KÉSZLETEKBE** szerveződik (új/szerkeszt/töröl, `LastBkSet`, „My Backup Set"); plusz: a Picasa **maga tudott a Wine-ról** (`wine_get_unix_file_name`, `ShowUnixPaths` hét helyen). **51. tétel (2026-09-01):** a `thumbui` hiányainak nagy része **ELHELYEZÉS-kérdés** (nálunk menüben, az eredetiben eszköztáron) — nyolc elem felülbírálva; a valódi hiány a **rács-NAGYÍTÓ** („Click and drag over photos to magnify them"). **52. tétel (2026-09-01):** a szerkesztő **kétképes módja** (A-A / A-B) — az A-A-ban a két példány **KÜLÖN szerkeszthető**, és kilépéskor a Picasa megkérdezi, melyiket tartsd meg („Choose Edits", Top/Bottom/Left/Right, `DoNotAskOnEnd2Up`); a lelet a #6-ra ment. **53. tétel (2026-09-01):** az `editpanel` **vágás / retus / vörösszem** füle — mind a tíz jelölt elem **téves riasztás**, nálunk megvan; sőt helyenként gazdagabb (egyenesítés-figyelmeztetés, egyéni képarány hozzáadása, régió-számláló). **54. tétel (2026-09-01):** a szöveg-fül nálunk teljes, de a **FELIRAT két vezérlője hiányzik** (`captionbutton` = elrejtés, `captiontrash` = törlés); a láthatóság **tartós** (`Preferences\LastCaptionButton`), és **két belépési pontja** van (szerkesztő + egyképes nézet) **55. tétel (2026-09-01):** a **finomhangolás** és az **effekt-fülek** — négy téves riasztás (`filllight_icon`, `droppertoggle`, `faces_button`, `filter_name` mind megvan); az egyetlen valódi hiány az **„Edit Movie" gomb**, ami a #432/#452 belépési pontja. **56. tétel (2026-09-01):** a `headerpanel` tíz eleméből **öt halott** (webes szinkron) és **öt élő**; valódi hiány a **`save_edits`** és a **`select_star`**; a fejléc gombjai **számlálós feliratúak** (`albumbutton_*%d`). **57. tétel (2026-09-01):** a `compose_mail` a Gmail-ághoz tartozik ⇒ **hatókörön kívül** (mérve, nem feltételezve), **de két élő részletet** hoz a #1798-ra: `Preferences\EmailAutocomplete` (címzett-kiegészítés) és a **„Preparing attachments…"** folyamatjelző. **59. tétel (2026-09-01):** a keresősávból **három szűrő hiányzik** (arcos képek, csak filmek, dátum-tartomány — ez utóbbi **CSÚSZKA**, nem dátumválasztó); és van egy eddig nem dokumentált, gazdagabb **`searchoptions`** réteg (hasonlóság-keresés mintaképpel, másodpéldány, gép szerinti szűrés). **60. tétel (2026-09-01):** a `searchoptions` feltárva — a **hasonlóság-keresésnek SAJÁT ADATBÁZISA** van („Updating similarity database (will be fast next time)") és **saját eredmény-albuma** („Similarity Search Results"); ez NEM ugyanaz, mint a mi másodpéldány-keresőnk. **61. tétel (2026-09-01):** a „rejtett vezérlőcsoportok" keresése — **NEGATÍV eredmény**: a leltárból hiányzó tíz csoportból kilenc **grafikai erőforrás**, a tizedik (`notifier`) már feltárva ⇒ a keresést nem érdemes megismételni. Melléklelet: a gombok **HÁROM állapotúak** (`_n`/`_h`/`_p`, 1252 erőforrásnév). **62. tétel (2026-09-01):** a névtelen/mellőzött arcok fejléce — két téves riasztás (a mellőzés és a kézi hozzáadás megvan), a névtelen↔mellőzött váltás pedig nálunk **albumon** át megy, nem fejléc-gombbal ⇒ tudatos eltérés a 45.3 táblában. **63. tétel (2026-09-01):** a címke-panel nálunk **teljes**, és a geocímke-párbeszéd `tagall` művelete is megvan (`setGeotagRows` a teljes kijelölésre) — a Google Earth-párbeszéd navigációja hatókörön kívül. **64. tétel (2026-09-01):** a **videó VÁGHATÓ** az eredetiben (`setin`/`setout`/`trimslider`, a vágáspontok a `.picasa.ini` `filters=` láncába kerülnek `moviestart`/`movieend` néven), és **képkocka menthető** belőle (`capture_frame`); nálunk a tokent **megőrizzük**, de beállítani nem tudjuk. **58. tétel (2026-09-01):** a webkamera-panel **KÉT rögzítési módot** ad (videoklip ÉS `snapshot` állókép), **külön kép- és hangforrást**, a klip **visszajátszását a panelen belül**, és tartós méretet (`Preferences\capturemoviesize`) — a tartalom a #853-hoz **58.5–58.6 (2026-09-02):** ⭐ a KIMENET is megvan — a felvétel a `<Képek>\Picasa\`**Rögzített videoklipek** mappába megy (ugyanaz a hármas lánc, mint a filmnél), a mappa **`.picasa.ini`-t kap** `P2category=Projects (internal)` sorral, **de csak létrehozáskor**; az állókép neve **`snapshot.jpg`**, és ütközésnél a **`%s-%03lu`** mintával sorszámozódik (`snapshot-001.jpg`) — ez **MÁS**, mint a kollázs/film `%s%lu`-ja —, legfeljebb 4096-ig; a videóból mentett **képkocka UGYANIDE** megy (`CCaptureFrame::CaptureFolder`, négy magyar állapotszöveggel); a panel kilenc állapotszövege és mind a tizenegy vezérlője **teljes névvel** kiírva. Élő minta: a korpuszban a `Captured Videos` és a `Rögzített videoklipek` egyszerre áll. |
| [picasa-megjelenitesi-modok.md](picasa-megjelenitesi-modok.md) | **A `Nézet ▸ Megjelenítési mód` almenü MEGFEJTVE** (#1409) — nem hat mód, hanem **tizenegy, egyetlen kizáró rádiócsoportban** (`0x00575670`); nincs köztük kapcsoló. Minden mód egy **képsoronkénti képpont-átalakító**, a `+0x254` horgon át, az ablak újrarajzolásakor. Mérve: a túlcsordulás-jelölés **csak a tiszta fehéret** festi **`#FF7F7F`**-re; a Projektor mód ×220/256, az LCD fehérpont ×246/256 (egyenletes sötétítés, színeltolás nélkül); a 16 bites szemcsézés MT-zaj +0…7/0…3/0…7 telítő összeadással; a Lineáris gamma egy **beégetett 256 bájtos LUT** (NEM `x^(1/2.2)`, hanem ≈ gamma 1,44) — a lap közli a teljes táblát. **A mód nem tárolódik**: minden indításkor „Automatikus”. Két korábbi spec-tévedés javítva (elcsúszott parancsazonosító-tábla; „12 tétel / az AUTO nincs a tömbben”). ✅ **2026-08-30 — a NY-5 (`Színkezelés használata`, #1582) LEZÁRVA az olcsó lánccal**: önálló kapcsoló, `Preferences\EnableColorManagement` (alap 0), bekapcsoláskor a szerkesztő-előnézet újraépül, az ICC a beágyazott `icc_camera_profile`/`icc_camera_to_tone_matrix` tagokból. Melléklelet (⚠️): a `0x9c9e` funkcionálisan a `ShowHidden`-t kezeli, az `EnableColorManagement` pipája a `0x9d72`-n ül — a menü-felirat párosítás a tulajdonos képeivel MEGERŐSÍTVE (a pipa a „Színkezelés használata" során), ld. 5.12. ✅ **A NY-1/3/4 (#1580) is LEZÁRVA**: NY-1 a mód NEM hat az exportra/nyomtatásra (a kimenetek bájtszinten azonosak); NY-3 a Mac gamma VILÁGOSÍT (`pow(x,1/1,6)`, teljes felületre, a fotó +15,7%), a „fekete képernyő" feltételezés megdőlt → **#1730** a megvalósítási jegy; NY-4 diavetítésben nem hat. ✅ **2026-08-30 — NY-2 („miért 1,44") LEZÁRVA matematikailag**: a 256 bájtos tábla legjobb hatványillesztése p=0,6944 (`round(255·(i/255)^p)`), azaz gamma 1,440; a tábla a szerződés, képlet-illesztés NEM kell. Maradt: NY-6 (csak bit-szemcséhez). |
| [picasa-kereses-modok.md](picasa-kereses-modok.md) | **A keresési módok és a másodpéldány-kereső** — az `ID_DUPES` keresési MÓD, nem panel; a keresési sáv 6 élő és **13 halott** eleme tételesen; a „hasonló képek" keresés az eredetiben NEM létezik; az importáláskori dupe-ellenőrzés aszinkron feladatsor. **A másodpéldány-DÖNTÉS KULCSA Ghidrával MEGFEJTVE (2026-08-30):** az \`originfast\` (MD5) 64 bites keresése a dupe-listában — a #1481 képlete. Jegy: **#1398** |
| [picasa-nerdview-panel.md](picasa-nerdview-panel.md) | **A „Hisztogram és fényképezőgép-adatok" panel MÉRT geometriája** — a panel 238 × 144; a felirat egysoros, 11 képpont magas és **nem félkövér** (a `.tre` semmit nem jelöl); a hisztogram 213 × 59 (ez nálunk helyes); a két adatoszlop 138 + 6 rés + 69. Jegy: **#1344** |
| [picasa-lebego-ertesito.md](picasa-lebego-ertesito.md) | A lebegő értesítősáv (`CNotifierPopup`) — képernyőfelvétel- és import-értesítés, kattintás-viselkedés. ⚠️ **Az „a geometria NYITOTT" megjegyzés 2026-08-24-én ELAVULTNAK bizonyult:** a geometria mérve van (a lap „Geometria — mérve a binárisból" szakasza), a pozicionálás dekompilálva (`SPI_GETWORKAREA` + 144 képpont). **Ami tényleg nyitva volt: a cella élettartama és az animáció ütemforrása** — a cella élettartama **LEZÁRVA 2026-08-26** (abszolút határidő `cella+0xb8`, képkockánként ellenőrizve), az ütemforrás **LEZÁRVA 2026-08-30** (a vtable 0x60 rekesze: `CNotifierPopup::vftable` 25. rekesz = `0x006575b0`). Jegy: **#1130** |
| [vorosszem-eszkoz-terve.md](vorosszem-eszkoz-terve.md) | A vörösszem-eszköz terve |
| [vagas-eszkoz-allapot.md](vagas-eszkoz-allapot.md) | A vágás-eszköz állapota — 19 arány, egyéni arányok, 3 javaslat |

## Nyelv és megjelenés

| lap | miről szól |
|---|---|
| [picasa-hu-terminology.md](picasa-hu-terminology.md) | Hivatalos Picasa-magyar terminológia |
| [picasa-effekt-nevek.md](picasa-effekt-nevek.md) | Az effektek nevei és buboréksúgói |
| [picasa-effekt-feliratok.md](picasa-effekt-feliratok.md) | Az effekt-vezérlők feliratai |
| [picasa-gomb-es-menu-rendszer.md](picasa-gomb-es-menu-rendszer.md) | **A gomb- és menürendszer** — 9-szeletes gombok, állapotszínek, tipográfia, a kétféle menü |
| [picasa-eger-es-kijeloles.md](picasa-eger-es-kijeloles.md) | **Egér, kijelölés, kattintás-viselkedés** — a `.tre` interakciós szótár, a Ctrl/Shift-modell, a kijelölés **mappa-hatóköre**, a Ctrl+A/Home/End teljes leképezése |
| [design-guide.md](design-guide.md) | Dizájn-kézikönyv — hűség-referencia |
| [ux-principles.md](ux-principles.md) | UX-alapelvek — „a Picasa lelke" |

## Módszertan és tervezés

| lap | miről szól |
|---|---|
| [binaris-regeszet-modszertan.md](binaris-regeszet-modszertan.md) | **A szerszámosláda**: mit hoz ki egy eszköz, és mit NEM lát |
| [feature-map.md](feature-map.md) | Funkciótérkép és fázisterv |

## Mikor kell ezt a lapot frissíteni

| mikor | mit |
|---|---|
| **Új spec-lap születik** | egy sor a témakör táblájába — **ugyanabban a PR-ban** |
| **Egy kör nyitott kérdést ZÁR LE** | a kérdés kikerül a „Nyitott kérdések" listáról; ha a lapon nem marad több, a lap fejléce is |
| **Egy kör ÚJ nyitott kérdést talál** | egy sor a lap listájába, **egy mondatban megfogalmazva** — ne csak „Nyitva" szót írj a spec-lapra |
| **Egy lap átnevezése/összevonása** | a hivatkozás javítása |
| **Kutatói kör INDULÁSAKOR** | csak olvasod — innen választasz témát |

**A frissítés nem külön kör.** Aki hozzányúl egy spec-laphoz, ugyanabban a
PR-ban hozza rendbe ezt a listát is — így az index nem tud elavulni.

⚠️ **Ne gépi szó-számlálással tartsd karban.** A `Nyitva`/`dekódolatlan`
szavak nagy része **hivatkozás** egy máshol megválaszolt pontra; a
számlálás háromszorosára fújja a képet. A lista **kézzel írt kérdésekből**
áll, mert egy kutatói kör kérdést választ, nem szót.

A gyanús helyek gyors előkeresésére (ellenőrzésre, nem karbantartásra):

```bash
grep -n 'Nyitva\|NYITOTT\|dekódolatlan\|uncalibrated' docs/specs/*.md \
  | grep -v '~~' | grep -v 'LEZÁRVA\|MEGVÁLASZOLVA\|MEGOLDVA\|MEGDŐLT'
```
