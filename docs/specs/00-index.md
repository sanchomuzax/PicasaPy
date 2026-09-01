# A specifikációk tartalomjegyzéke

**Ez a lap a belépési pont a `docs/specs/`-be.** Alább előbb a **valóban
nyitott kérdések** listája (ebből válasszon témát egy kutatói kör), majd a
34 spec-lap témakörönként.

**A lenti „Nyitott kérdések" lista kézzel ellenőrzött**, nem gépi
szó-számlálás. Egy 2026-08-16-i átvilágítás kimutatta, hogy a
`Nyitva`/`dekódolatlan` szavak **kétharmada hivatkozás** egy máshol már
megválaszolt pontra — a gépi számlálás tehát háromszorosára fújta a
képet (pl. `filterdesc-registry.md`: 6 találat, **0** valódi nyitott
kérdés).

*Utolsó átvilágítás: 2026-08-16 (a második, tízkörös menet után).*

## 🔶 Nyitott kérdések — innen válassz kutatói kört

### [filters-decoded.md](filters-decoded.md) — nincs nyitott kérdés

✅ **2026-08-24 — az utolsó kérdés (a `FocalZoom` perem-módja) LEZÁRVA MÉRÉSSEL:**
a halmozás csak nagyít (`zoom ≥ 1`), ezért minden minta a képen belülre esik —
négy perem-mód **bitre azonos** kimenetet ad képen belüli fókuszpontra. A mai
`cv2.BORDER_REPLICATE` helyes. Melléklelet: a natív mag (`0x00bcf4b0`) igazolja a
`zoom_max_offset` és `zoom_sample_count` képleteinket. Jegy: **#1351**.

### [picasa-create-features.md](picasa-create-features.md) — 1 nyitott kérdés (a #1412)

⭐ **2026-09-01 — a #1412 egyik KORLÁTJA MEGDŐLT:** a jegy szerint „egy mintánk van (AI6)", de a `kollazs-golden/` **tizenegy** `.cxf`-je közt a **`regulargrid` (AI5) is egyetlen `scale`-t** használ (330) ⇒ **második adatpont**. Levezetve: a kizárt 300 és 359 az **oszlop-** és **sor-osztás**; az AI5-re pontos a megfelelés (`0,322266 × 1024 = 330`), az AI6-ra keresett tört **0,305664** — a felirat-sávot is tartalmazó cella lehet. Részletek a #1412 kommentjében. **Folytatás (2026-09-01):** mind a hat téma átmérve (`kollazs-eletciklus.md` **17.**) — a `picturepile` szorzója **pontosan 1,25000**, a `regulargrid`-é **1,00000**, a `contactsheet`-é **node-független**; a `scale` a **rajzolt méret**, nem a befoglaló dobozé; a 313 **nem beégetett konstans** (nulla találat a `.text`-ben).

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

### [picasa-mappakezelo.md](picasa-mappakezelo.md) — nincs nyitott kérdés (a hatókörön kívüli Apple-ágon felül)

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

### [picasa-ini-format.md](picasa-ini-format.md) — nincs nyitott kérdés

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

### Nincs nyitott kérdés

`filterdesc-registry.md` · `ui-audit-context-menus.md` · `ui-audit-mainwindow.md` · `picasa-native-filter-registry.md` · **`ui-audit-editor.md`** · és a lenti táblák
minden további lapja.

## Formátum-specifikációk (adatfájlok, erőforrások)

| lap | miről szól |
|---|---|
| [picasa-ini-format.md](picasa-ini-format.md) | A `.picasa.ini` — az igazságforrás, round-trip szabályokkal |
| [pmp-database.md](pmp-database.md) | A központi adatbázis (`db3` / PMP) |
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
| [konyvtar-ablak-meretek.md](konyvtar-ablak-meretek.md) | A könyvtár-ablak (156 elem) |
| [picasa-konyvtar-eszkoztar-viselkedes.md](picasa-konyvtar-eszkoztar-viselkedes.md) | A fő eszköztár öt gombjának VISELKEDÉSE (Import, Új album, nézetváltó pár, Nézet-beállítások, Webkamera) — nem geometria |
| [jobb-fiok-meretek.md](jobb-fiok-meretek.md) | A jobb oldali fiók („Metaadatok", 80 elem) |
| [picasa-fo-ablak-elrendezes.md](picasa-fo-ablak-elrendezes.md) | A fő ablak elrendezése — a forrásból |

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
| [picasa-keptalca.md](picasa-keptalca.md) | **A Képtálca (`scratch`, „Selection") MŰKÖDÉS-specje** — a döntő lelet, hogy a tálca **nem marad meg újraindítás után** (három független negatív ellenőrzés); a négy vezérlő felirat NÉLKÜL, csak ikon+súgó; a `Tray` helyi menü két parancsa; **két külön** ürítés-megerősítés; a 36,5%-os doboz-kényszer; a `trayexec` adatvezérelt műveletsor; két negatív eredmény (a `.pbz` placement NEM az alap-sorrend, a `Tray contains:` hibakereső lap) |
| [picasa-menu-leltar.md](picasa-menu-leltar.md) | **A menüsor gépi leltára a binárisból** — 189 tétel 18 `eMenu*` névtérben; a lefedettségünk 150/189 (79%), a 39 hiányzó három csoportban (14 hatókörön kívül, 18 érdemi, 1 almenü). Jegy: **#1397** |
| [picasa-menu-parancsok-viselkedes.md](picasa-menu-parancsok-viselkedes.md) | **A menüparancsok VISELKEDÉSE** (#1434) — a `.fen` párbeszédleírók mint leggyorsabb út; az effektus-vágólap **nem** rendszer-vágólap; a dátum-állítás **nem** fájlidőt ír; a menüsor **kilenc almenüje**; a Beállítások 8 füle és ~78 vezérlője (köztük a nyomtatás **Lanczos-3/8** választása); a Személyek kezelése hat azonosító-mezője; és a beállítások tárolási helye (`SOFTWARE\Google\Picasa\Picasa2\Preferences\`). **33. tétel (2026-08-30): a KÉP menü teljes cmd→kezelő térképe** (16 + 4 geotag-parancs, a kép-menübeli Szépia/Fekete-fehér `0x9d4a`/`0x9d4c` külön batch-parancsok), a Csoportos szerkesztés **kétágú mintája** (szerkesztő-navigáció `0x579330` vs. batch `0x5fe370`), a FILM_GRAIN **Shift-függő grain/grain2** váltása (`GetAsyncKeyState(0x10)`), az AUTO_REDEYE keret-útja (`0x602100(0x5f39d0)`), és a Geotag almenü: Google Earth-ellenőrzés CLSID-vel + InstallEarth-párbeszéd, a GEOUNTAG megerősítője (`ClearGeoTag::warn`). **34. tétel (2026-08-31): az öt lefedettségi parancs** — forgatás (fix 90/270°, háttérszálon, `rotate=` = negyedfordulat-tároló, **#1162 lezárva**), Undo All Edits (egy/több/film megerősítés-hármas, `redeye`/`retouch`/`picnik` token-törlés), Unhide/Hide (`hidden=yes` kulcs, online-album-megerősítés), Reset Faces (sima = kijelölés, kérdés nélkül; Ctrl/Shift = könyvtárszintű FIGYELEM-párbeszéd). **35. tétel (2026-08-31): Poszter (papírméret-lista nyelvi feltétellel), képernyővédő (saverlist.txt a #db3 mappában, telepítés-ellenőrzés, rundll32-install), TiVo (Windows-only akció — hatókörön kívül-javaslat), keresés-mentése (1000-es küszöb, „Create Album" gomb), biztonsági mentés (backup.xml + backuphash + il_BurnPanel). **36. tétel (2026-08-31):** a névcímke-letöltés **halott menütétel** (`RemoveMenu` feltétel nélkül); a Mappakezelő **engedélyezési kapuja** (szürke, amíg a szerkesztő-előnézet aktív) és a `+0x34a4` holt jelzőbit; a lista-rendezés **három registry-kulcsa** (`datesort` = teljes módszám, `peoplesort`, `albumlistflip`), a „méret" = **64 bites bájtösszeg**, és hogy a rendezés-tételek **három menüben** élnek (a menüsáv Nézet menüjében is — a #1454 megjegyzésének helyesbítése). **37. tétel (2026-08-31):** a jobb fiók négy lapja **kizáró rádiócsoport** (minden ág elrejti a másik hármat), a menü→névparancs híd (`0x0065ab50`), az `ID_CAPTAG` **két menüben két külön azonosítóval** (`0x9d2c` vs `0x9de4`), és az `active_metadata_tab` kulcs, amelynek **három olvasója és nulla írója** van. **38. tétel (2026-08-31):** a „Rejtett képek" bekapcsolása **jelszót ajánl** (`IDS_PROMPT_HIDDEN_PWD_*`, „Add Password"/„Don't Add Password", `DoNotConfirmHiddenPwd`); az Idővonal **teljes képernyős bemutató-mód** a Flipbookkal közös kezelőn; a háttérkép **BMP-t ír** a `Picasa\Backgrounds`-ba és **középre** teszi (`WallpaperStyle=0`, `TileWallpaper=0`). **39. tétel (2026-08-31, az első UI-lefedettségi kör):** a `printoptions` panel **tizenegy `Preferences\printoptions::*` kulcsot** ír (felirat forrása/helye/betűje/mérete/színe/tördelése, szegély megléte/vastagsága/színe/csak-alul/egyenletes); a fogyasztó a nyomtatási rajzoló (`0x00776180`); indexkép-nyomtatásnál a panel **tiltva**, saját magyarázó szöveggel. **40. tétel (2026-08-31):** a `printpanel` **DPI-őrt** tartalmaz („Smallest picture: %d pixels/inch.", „%d small picture(s) found.", „Please review before printing."), a nyomatméretet a `Preferences\PrintLastSize` **tartósan** őrzi, a példányszám **képenkénti**, és a „Szegély- és szövegopciók" gomb nyitja a `printoptions`-t. **41. tétel (2026-08-31):** az `acquirepanel` importálás — `AcquirePath` / `LastImport%x` / `acquireUseSubFolder` kulcsok, az almappa-elnevezés **három módja** (kézi cím / „Date Taken (YYYY-MM-DD)" / mai dátum), kártya-törlés megerősítéssel; **és a lecke: a „hiányzik" oszlop JELÖLT, nem ítélet** — tíz elem téves riasztás volt. **42. tétel (2026-08-31):** a `collagepanel` megfeleltetési sora **elavult** volt (egyetlen fájlra mutatott, és azt állította, hogy nincs interaktív szerkesztő) — **egy sor 38 helyesen megvalósított elemet rejtett el**; javítás után a tábla 87 → 132 párosítva, 425 → 397 hiány. **43. tétel (2026-08-31):** a megfeleltetési fájl **mind a 74 sorának** átvilágítása — a `collagepanel` volt az EGYETLEN elavult (negatív eredmény); és a gyorscímke-beállító az eredetiben **TÍZ** helyet ad (`edit_0..9`, `cmp eax, 0xa`), nálunk nyolc. **44. tétel (2026-08-31):** a `buttonmgr` — a Picasa gombsávja **BŐVÍTMÉNY-RENDSZER** volt (`http://picasa.smo/buttons`, „Launch Picasa and import buttons?", `#buttons\` mappa); a testreszabás a `Preferences\Buttons\UserConfig` és `…\Exclude` kulcsokban él. **45. tétel (2026-09-01):** a mérés **VAK a csoportosztásra, a sorrendre és az elrendezésre** (az elválasztókat kidobja) — a „hiányzik = 0" csak annyit jelent, hogy *nincs hiányzó vezérlő*; plusz egy **tudott eltérések** táblája a kimondatlanság ellen. **46. tétel (2026-09-01):** a `faceheaderpanel` javaslat-munkafolyamata **négy külön parancs** (`selectsug`/`confirmsug`/`sug_filter`/`moresug`), és a „További javaslatok keresése" **újra-klaszterezés**, nem szűrő; a lelet a #26-ra ment, mert arcfelismerő motor nélkül nem valósítható meg. **47. tétel (2026-09-01):** a `choose_mail` levelezőprogram-választó (`EmailPrepType`, `DoNotPromptForEmailPref`) — **és egy NÉMA BEÁLLÍTÁS nálunk**: a „Let me choose each time" rádiógomb tárolódik, de a `sendRows()` nem olvassa el. **48. tétel (2026-09-01):** a **néma beállítás** mint önálló hibaosztály — a két meglévő őr (`nema_jelzesek.py`, `nema_slotok.py`) **mérve NEM fogja meg**; „a beállítás él, csak nem hat". **49. tétel (2026-09-01):** KÉT SAJÁT HELYESBÍTÉS — a `GetSubMenu(…,2)` a menü **fogantyúját** adja, nem a tétel helyét (#1766 leállítva); és a #1798 valódi oka nem a beállítás olvasása volt, hanem hogy a `sendRows()`-nak **nem volt hívója** ⇒ néma vezérlőnél a **teljes láncot** kell mérni, mindkét irányból. **50. tétel (2026-09-01):** a `publish` **HÁROM panel egy névtérben** (mentés · Ajándék-CD · webre töltés), és csak a harmadik halott; a mentés **nevesített KÉSZLETEKBE** szerveződik (új/szerkeszt/töröl, `LastBkSet`, „My Backup Set"); plusz: a Picasa **maga tudott a Wine-ról** (`wine_get_unix_file_name`, `ShowUnixPaths` hét helyen). **51. tétel (2026-09-01):** a `thumbui` hiányainak nagy része **ELHELYEZÉS-kérdés** (nálunk menüben, az eredetiben eszköztáron) — nyolc elem felülbírálva; a valódi hiány a **rács-NAGYÍTÓ** („Click and drag over photos to magnify them"). **52. tétel (2026-09-01):** a szerkesztő **kétképes módja** (A-A / A-B) — az A-A-ban a két példány **KÜLÖN szerkeszthető**, és kilépéskor a Picasa megkérdezi, melyiket tartsd meg („Choose Edits", Top/Bottom/Left/Right, `DoNotAskOnEnd2Up`); a lelet a #6-ra ment. **53. tétel (2026-09-01):** az `editpanel` **vágás / retus / vörösszem** füle — mind a tíz jelölt elem **téves riasztás**, nálunk megvan; sőt helyenként gazdagabb (egyenesítés-figyelmeztetés, egyéni képarány hozzáadása, régió-számláló). **54. tétel (2026-09-01):** a szöveg-fül nálunk teljes, de a **FELIRAT két vezérlője hiányzik** (`captionbutton` = elrejtés, `captiontrash` = törlés); a láthatóság **tartós** (`Preferences\LastCaptionButton`), és **két belépési pontja** van (szerkesztő + egyképes nézet) **55. tétel (2026-09-01):** a **finomhangolás** és az **effekt-fülek** — négy téves riasztás (`filllight_icon`, `droppertoggle`, `faces_button`, `filter_name` mind megvan); az egyetlen valódi hiány az **„Edit Movie" gomb**, ami a #432/#452 belépési pontja. **56. tétel (2026-09-01):** a `headerpanel` tíz eleméből **öt halott** (webes szinkron) és **öt élő**; valódi hiány a **`save_edits`** és a **`select_star`**; a fejléc gombjai **számlálós feliratúak** (`albumbutton_*%d`). **57. tétel (2026-09-01):** a `compose_mail` a Gmail-ághoz tartozik ⇒ **hatókörön kívül** (mérve, nem feltételezve), **de két élő részletet** hoz a #1798-ra: `Preferences\EmailAutocomplete` (címzett-kiegészítés) és a **„Preparing attachments…"** folyamatjelző. **59. tétel (2026-09-01):** a keresősávból **három szűrő hiányzik** (arcos képek, csak filmek, dátum-tartomány — ez utóbbi **CSÚSZKA**, nem dátumválasztó); és van egy eddig nem dokumentált, gazdagabb **`searchoptions`** réteg (hasonlóság-keresés mintaképpel, másodpéldány, gép szerinti szűrés). **60. tétel (2026-09-01):** a `searchoptions` feltárva — a **hasonlóság-keresésnek SAJÁT ADATBÁZISA** van („Updating similarity database (will be fast next time)") és **saját eredmény-albuma** („Similarity Search Results"); ez NEM ugyanaz, mint a mi másodpéldány-keresőnk. **61. tétel (2026-09-01):** a „rejtett vezérlőcsoportok" keresése — **NEGATÍV eredmény**: a leltárból hiányzó tíz csoportból kilenc **grafikai erőforrás**, a tizedik (`notifier`) már feltárva ⇒ a keresést nem érdemes megismételni. Melléklelet: a gombok **HÁROM állapotúak** (`_n`/`_h`/`_p`, 1252 erőforrásnév). **62. tétel (2026-09-01):** a névtelen/mellőzött arcok fejléce — két téves riasztás (a mellőzés és a kézi hozzáadás megvan), a névtelen↔mellőzött váltás pedig nálunk **albumon** át megy, nem fejléc-gombbal ⇒ tudatos eltérés a 45.3 táblában. **63. tétel (2026-09-01):** a címke-panel nálunk **teljes**, és a geocímke-párbeszéd `tagall` művelete is megvan (`setGeotagRows` a teljes kijelölésre) — a Google Earth-párbeszéd navigációja hatókörön kívül. **64. tétel (2026-09-01):** a **videó VÁGHATÓ** az eredetiben (`setin`/`setout`/`trimslider`, a vágáspontok a `.picasa.ini` `filters=` láncába kerülnek `moviestart`/`movieend` néven), és **képkocka menthető** belőle (`capture_frame`); nálunk a tokent **megőrizzük**, de beállítani nem tudjuk. **58. tétel (2026-09-01):** a webkamera-panel **KÉT rögzítési módot** ad (videoklip ÉS `snapshot` állókép), **külön kép- és hangforrást**, a klip **visszajátszását a panelen belül**, és tartós méretet (`Preferences\capturemoviesize`) — a tartalom a #853-hoz |
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
