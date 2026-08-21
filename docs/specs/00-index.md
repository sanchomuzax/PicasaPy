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

### [filters-decoded.md](filters-decoded.md) — 1 kérdés

1. ~~**`autocolor` pontos gain-képlete** (Nyitva 1)~~ — **TELJESEN MEGVAN**
   (#759, 2026-08-18): `M · diag(g) · M⁻¹`, és a becslő egész-osztásai
   **nulla felé csonkolnak** (C-szemantika). Kimérve **0,614** (a mai kód
   2,352, a JPEG-zajszint ~0,69) — nincs nyitott kérdés, csak bekötés
2. ~~**`unsharp` kernel finomítása** (Nyitva 3)~~ — **MEGVAN** (#762):
   köbös B-spline, `× 1,5` szélesítéssel, σ ≈ 0,87. A mérés szerint a mai
   Gauss már „JÓ" (0,47) — finomítás, nem hiba
3. **Render-pontosítás** — ⭐ **a rangsor alapja a mért korpusz-gyakoriság**
   (`filters-decoded.md`, „A szűrők TÉNYLEGES gyakorisága").
   **A rangsor 2026-08-18-án ÚJRAÍRVA**, mert a régi alak nyolc áthúzott
   beszúrástól olvashatatlanná vált, és a tételei nagyrészt elavultak.

   | tétel | régi verdikt | MA | jegy |
   |---|---|---|---|
   | `finetune2` Csúcsfény+Árnyék | 55,94 ΔE · 561 kép | ✅ **KÉSZ (2026-08-18)** — a kettő EGY közös LUT, a kompozit eltérés 217 szintről 0-ra (a valódi ini-korpusz 22 %-a kompozit) | #879 |
   | `finetune2` hőmérséklet | — | **a művelet TELJES 3×3 mátrix — a binárisból** (2026-08-18): a `0x0090e9d0` a feketetest-táblából vett színnel az `autocolor` mátrix-alkalmazóját hívja. Az átlón kívüli tag a hideg végen **11,8 %**, a melegen 3,2 %, `temp=0`-nál 0,63 %. A mai csatornánkénti modellünk ezt **szerkezetileg** nem tudja. **Nincs szükség új felhasználói anyagra.** | #956 |
   | `tint` | 20,6 | megfejtve (`preserve` skálája −1…255) | #872 |
   | `sat` pozitív ág | 12 | ✅ **kész és kimérve: 0,74** | #693 |
   | `dir_tint` | 9 | ✅ **teljesen megvan** — az átmenet-görbe is (2026-08-18) | #874 |
   | `fill` | 6,5 | ✅ **eredeti exportokhoz mérve 1,20–1,77** (2026-08-18) — nincs teendő a szűrőn; a mérés bekötése #938 | — |
   | `ansel` | 5,6 | ✅ **fehér szűrővel 0,53**; a SZÍNES szűrő igazolatlan — exportra vár | #939 |
   | `Vignette` | 4,6 | ✅ a zóna **ELLIPSZIS** — eredeti exportokkal igazolva (2026-08-18) | #859 |

   **Vagyis a rangsorból nem maradt bekötésre kész rendermunka:** a
   `finetune2` szintvágó ága 2026-08-18-án elkészült (#879), a
   hőmérséklet-tengelye pedig új mérésre vár (#956). A többi vagy kész,
   vagy külső exportra vár.

   - **Korábban megválaszolva:** a `tint` (és a `rainbow`, `autocontrast`)
     **szinthúzással kezd** — a `0x009db610` helyben módosítja a képet, nem
     csak elemez (#872)
4. ~~**A `tint` virtuális színátalakítása**~~ — **GYAKORLATILAG LEZÁRVA** (#872): a `ctx` a **lánc-építő objektum**, a `[ctx+8]` egy függvénymutató-**mező** (nem vtable-slot), és a szokásos renderelési úton nem áll be. A recept teljes nélküle
5. ~~**A `ytResampler` utolsó, nem 2-hatvány lépése**~~ — **MEGVAN** (#871,
   #762): kilenc szűrőmag, a `ResampleFilter2` beállítás választ, alapérték
   **6 = Lanczos-4**; az `unsharp` a 2-est (köbös B-spline) használja.
   Maradék: ~~a **4-es mód** pontos alakja~~ **MEGVAN (#871): háromlebenyes
   köbös konvolúció, 11/209-es törtekkel, két matematikai ellenőrzéssel
   igazolva** · ~~a **10-es** mód~~ **MEGVAN (#871): MMX-es bilineáris,
   8 bites súlyokkal, `>> 8` osztással** → **a `ytResampler` mind a
   tizenegy módja feltárva**

### [picasa-create-features.md](picasa-create-features.md) — nincs nyitott kérdés

1. ~~**A Képkockamozaik kényszeres vágási szabálya**~~ — **TELJESEN MEGVAN**
   (#431/#916, 1.9.14, 2026-08-18): a kényszeres levél a téglalapot
   változatlanul átveszi és nem darabol tovább; a „nincs kényszer" jelölés
   mind a négy koordináta −1,0. A „melyik részfába irányítja" kérdés
   **tárgytalan**: nincs irányítás — a keresés körönként, képenként
   stempeli be a kényszert a csomópontba, és elutasításos mintavétellel
   találja meg a jó elrendezést. Ugyanitt megvan a pakoló **célfüggvénye**
   is (`0x00893570`, mindhárom rácsos témára közös): az **elpazarolt
   terület** minimalizálása
2. ~~**A Képkupac kezdeti (x, y) szórása**~~ — **elavult jelölés volt**: a
   szórás az 1.9.12-ben már 2026-08-14 óta megvan („legjobb jelölt"
   mintavételezés). A 2026-08-17-i átvilágítás vette le.

### [picasa-kollazs-felulet.md](picasa-kollazs-felulet.md) — 5 kérdés

⭐ **2026-08-21, működés-kör (kilenc kérdés):** a
`kollazs-eletciklus.md` **16.** szakasza négy, eddig sehol nem szereplő
viselkedést rögzít — a **kattintható kész-értesítés**
(`collage::done` = „A kollázs kész (kattintson ide)"), a **„Mentés
mellőzve"** és a **formátum-eltérés** figyelmeztetése, a főablak
**várakozó állapota**, és a **`hascollage` PMP-oszlop** (1 bájt/sor,
valódi adaton mérve; a PMP-oszlopok **nem egyforma hosszúak**).
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
2. Mi a **célja** a `FILE_ATTRIBUTE_TEMPORARY`-nak a kész kollázs-JPEG-en?
   (A tény három címen bizonyított: `0x0083c3b8`, `0x0083cda5`,
   `0x0068a81f` — a szándék nem ismert; ld. a lap 9.1/b 4. pontját.)
3. Az **5120-as felső renderméret** (`0x0083d050`) pontos szemantikája a
   renderelőn (`0x0087dcd0`) belül — a konstans megvan, az útja nincs
   végigkövetve.
4. ~~Az árnyék-képlet bemenete~~ — **LEZÁRVA** (2026-08-18, második
   árnyék-kör): az árnyék **témánként négy külön paraméterkészlettel**
   dolgozik (alfa 102 a Képkupacnál és a rácsos témáknál, 153 a Rácsnál
   és az Indexképnél); a `k` a képek cellaéle képpontban, az `A` lépték
   a 9.0 darabszám-képlete. Nem maradt feltételes állítás — a lap
   **9/b**-je. *(A jegy #977, már nem blokkolt.)*
5. A polaroid-felirat **két logikai kapcsolójának** jelentése
   (`ytVectorTextNode` `vt[0x2c]` → `+0x2a4`, `vt[0x38]` → `+0x2f3`;
   mindkettő 1) — a mechanikájuk megvan, a nevük nem: a lap **9/c**-je.
6. Az **`avgcolor` adatbázismezőt** mi és milyen képlettel állítja elő?
   (A kollázs csak **kiolvassa** — a lap **3/b**-je; ez az **indexelő**
   területe, nem a kollázsé.)


### [export-parbeszed.md](export-parbeszed.md) — 7 kérdés

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

1. **Mi TILTJA LE a film-rádiókat?** A tény mért (a rádiók szürkék, a
   csoport **címkéje fekete marad**), és négy dolog **kizárva**: nincs
   `.fen`-beli `enabled` kötés; a motor csak abból ismeri a letiltást
   (`0x008d2210`); a `movies` névre a teljes párbeszéd-kódban két
   hivatkozás van, egyik sem tilt; és a kötés-osztály ugyanaz
   (`0xC7F790`), mint a nem letiltott `sizeradio`/`quality`-é. **Az
   export-párbeszéd saját kódja tehát NEM tiltja le.** Folytatás: a közös
   vezérlő-réteg (`0x008d1450`, a `0x008d2210` hívói) vagy a befogadó
   `CExportPrefsPage` (`0x007f6650`). **A megvalósítást nem blokkolja.**

### [vagas-eszkoz-allapot.md](vagas-eszkoz-allapot.md) — nincs nyitott kérdés

~~A **kollázs Oldalformátum** legördülőjének sorrendje~~ — **MEGVAN**
(#876): a felépítő `0x007cc990` két kapcsolója adja; a kollázs esete az,
amikor **mindkettő hamis**. Ugyanitt derült ki, hogy a nyomatméretek
**metrikus/angolszász** ágra oszlanak.

### [picasa-gomb-es-menu-rendszer.md](picasa-gomb-es-menu-rendszer.md) — 1 kérdés

1. ~~a **letiltott** gomb rajza~~ — **MEGVAN** (#893): a rajzoló az alfát
   **néggyel osztja** (`0x009e3178`), kivétel nélkül
2. ~~a `popuplist` **lenyíló panel** színei~~ — **MEGVAN** (#894):
   `listdecrect`, sík `#E8E8E8` kitöltés, `#BABABA` keret
3. **A kiemelt sor SZÍNE** — a `respack`-ben nincs hozzá réteg, kódból jön.
   *(2026-08-18: négy helyen kerestük, nincs ott — a negatív eredmény és a
   folytatás helye a lap 8. szakaszában. A legolcsóbb út egy
   színmérés a felhasználó képernyőképéről.)*
4. **A buboréksúgó rajza** — saját osztály (`ytToolTip`), de nincs hozzá
   képréteg; a háttér/keret/árnyék kódból jön (#901)

### [picasa-elso-inditas.md](picasa-elso-inditas.md) — nincs nyitott kérdés

*(Új lap, 2026-08-21: az első indítás `initialscan` panelje — két
szövegkészlet (migráció / tiszta telepítés), 640×463 geometria, két rádió,
**rejtett Mégse**. Jegy: **#1167**. Egyik kérdés sem igényel futó Picasát.)*

1. ~~Mit ír a két rádió?~~ — **LEZÁRVA** (6.1): a panel nem ír fájlt,
   **−1/1/2 kódot** ad vissza. Ami MARAD: hol lesz ebből
   `scanlist.txt`-bejegyzés (`0x0040d6e3`-tól).
2. **Mi dönti el, melyik szövegkészlet** (`Text1` migráció / `Text2`
   tiszta telepítés) jelenik meg — a „van-e korábbi Picasa" vizsgálat helye.
3. **Hol jelenik meg a panel** (saját ablak vagy beágyazva), és mi
   történik, ha a felhasználó bezárja az ablakot (a Mégse rejtett).

### [picasa-mappakezelo.md](picasa-mappakezelo.md) — 1 kérdés (a hatókörön kívüli Apple-ágon felül)

*(A lap 2026-08-20-án készült, a tulajdonos két képernyőképéből és a
binárisból. A kör négy kérdést tett fel és kettőt le is zárt — a
lista-térképet (5.2/5.4) és a „teljes meghajtó" feltételét (10.). Ami
maradt, egyik sem igényel futó Picasát, és egyik sem blokkolja a
megvalósítást — jegy: **#1161**.)*

0. *(A lap 12. szakasza a hiteles, naprakész lista — 2026-08-21-én
   nyolc pontra bővült, majd az **M1–M5, M7, M8** lezárult. A tételek a
   `picasapy-agent` → `memory/nyitott-kerdesek-sor.md` munkasorban is
   szerepelnek, feldolgozási sorrendben.)*

   ⭐ **2026-08-21, fa-kör** — a lap **13. szakasza** lezárja a fa
   feltöltését: **lusta betöltés háttérszálon** (`SetEvent`,
   `0x007bf378` → a `0x007c9e70` szál), rögzített gyökérsorrend
   (Asztal → Képek → Dokumentumok → meghajtók), a meghajtó-felsorolás
   három hívása (a **hálózati ág fájlrendszer-ellenőrzés nélkül**, ezért
   a **leválasztott hálózati meghajtó is látszik**), és **negatív
   eredmény** a rejtett mappákra: a fa nem szűr. A kizárási lista három
   forrása (beégetett nevek + `filters.txt` + regisztrációs útvonalak) a
   **beolvasóé**, nem a fáé → **#1169**.

   ⭐ **2026-08-21, jobb-lista-kör** — a lap **14. szakasza**: a „Figyelt
   mappák" lista **teljes értékű kiválasztó vezérlő**. Kattintásra átáll a
   három rádió és az arcfelismerés-sor (a közös `0x007c60d0`), a **fa
   odaugrik**, és ha az ág még nincs betöltve, **lustán kinyílik**
   (`0x007bf130` + `SetEvent [dlg+0x550]` — ugyanaz az esemény, mint a
   13.2-ben). Fordítva a fa kattintása **törli a jobb lista
   kijelölését**: a két kijelölés kölcsönösen kizáró. **Rendezés nincs.**

1. **Az iPhoto / Apple Photos ág LÁTHATÓ különbsége.** A kódbeli helye, a
   két beállítás-kapcsoló és a használt lista megvan (a lap 6.2), de nem
   követtük végig, mit lát ebből a felhasználó. **A PicasaPy-ban nem
   megvalósítandó** (macOS-örökség).
2. **A dialógusnak tényleg nincs minimális mérete?** A `0x00920fa0`
   ablakeljárás nem kezeli a `WM_GETMINMAXINFO`-t — de a negatív állítás
   egyetlen ablakosztály átvizsgálásán alapul.
3. ~~A `[dlg+0x270]` és a `[dlg+0x2a8]` viszonya~~ — **LEZÁRVA**
   (2026-08-21, a lap **5.2/d**): a `+0x2a8` munkamenet-helyi delta, ami az
   alkalmazóig el sem jut; a `watchedfolders.txt` a **látható listából**
   (`+0x270`) íródik a közös `+0xf8` scan-lista tárolón át. Az 5.2/b
   táblázata helyesbítve.
4. ~~A `filters.txt` szakaszainak szemantikája~~ — **LEZÁRVA**
   (2026-08-21): a mérés a
   [picasa-program-resources.md](picasa-program-resources.md) **3.1**
   szakaszába került (hat szakasz, két külön teszt, a `FileIncludes`
   sorai eldobódnak). Jegy: **#1169**.
5. ~~A `ytVolumeIsExternalFS` (`0x007c84c0`) HASZNÁLATA~~ — **LEZÁRVA**
   (2026-08-21, a lap 13.5 újraírva): a példány a `CDirArray` `+0x84`
   mezőjében **használatlan** (csak konstruktor + destruktor), a
   név/viselkedés feszültség pedig **szerkesztői összevonás**
   (`/OPT:ICF`) — a `ytVolumeIsNTFS` törzsével bájtra azonos.
6. ~~A `0x007c91c0` háromértékű visszatérése~~ — **LEZÁRVA**
   (2026-08-21, a lap **14.7**): **két** érték van (`0` = siker,
   `9` = kudarc); a `1` egy tömb-növelő rutin helyi változója volt. A
   siker ága nyitja ki az ősöket és kéri a háttérbetöltést, a kudarcé
   törli a fa kijelölését.

### [picasa-eger-es-kijeloles.md](picasa-eger-es-kijeloles.md) — nincs nyitott kérdés

*(Mind a négy lezárult; a maradék apró pontok — a `WM_*` leképezés és az
egyes menük tételsora — a lap saját szakaszaiban vannak jelölve.)*

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

### [picasa-ini-format.md](picasa-ini-format.md) — 1 kérdés

1. Mit tesz a Picasa, ha külső program **írja az inifájlt ÉS megérinti a kép `mtime`-ját** (537. sor) — ⚠️ **windowsos próbára vár**, gépi úton nem eldönthető

### Nincs nyitott kérdés

`filterdesc-registry.md` · `ui-audit-context-menus.md` · `ui-audit-mainwindow.md` · `picasa-native-filter-registry.md` · **`ui-audit-editor.md`** · és a lenti táblák
minden további lapja.

## Formátum-specifikációk (adatfájlok, erőforrások)

| lap | miről szól |
|---|---|
| [picasa-ini-format.md](picasa-ini-format.md) | A `.picasa.ini` — az igazságforrás, round-trip szabályokkal |
| [pmp-database.md](pmp-database.md) | A központi adatbázis (`db3` / PMP) |
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

## Viselkedés és funkciók

| lap | miről szól |
|---|---|
| [picasa-create-features.md](picasa-create-features.md) | A „Létrehozás" menü funkciói |
| [picasa-kollazs-felulet.md](picasa-kollazs-felulet.md) | A Kollázs teljes működése — parancstábla, gyűrű, helyi menük, kimenet |
| [kollazs-atvilagitas.md](kollazs-atvilagitas.md) | **A Kollázs TELJES átvilágítása** — eredeti / nálunk / jegy minden vezérlőre, a panelen kívüliekkel; és kimondva, amit NEM néztünk meg |
| [kollazs-panel-ui-spec.md](kollazs-panel-ui-spec.md) | **A Kollázs-panel MEGVALÓSÍTÁSI UI-specifikációja** — elemfa, `objectName`-ek, a `.tre` kényszereiből levezetett méretezési törvény, vezérlő-API, teszt-szerződés, jegyekre bontás |
| [export-parbeszed.md](export-parbeszed.md) | **Az „Exportálás mappába" párbeszéd** — a `export.fen` leíró, mind a 28 magyar felirat, a kötések, a 9 megőrzött beállítás, és a képminőség öt fokozatának **számértéke a binárisból** |
| [kollazs-eletciklus.md](kollazs-eletciklus.md) | **A kollázs életciklusa** — a három állapot, az átmenetek, mindhárom párbeszéd szó szerint |
| [picasa-bezaras-es-kilepes.md](picasa-bezaras-es-kilepes.md) | Mit zár be az „X" — bezárás és kilépés |
| [picasa-nyomtatas.md](picasa-nyomtatas.md) | A nyomtatás — panel (61 elem), 17 méret, beállítások |
| [picasa-email-kuldes.md](picasa-email-kuldes.md) | E-mail-küldés — választó, beépített Gmail-szerkesztő, beállítások |
| [picasa-importalas.md](picasa-importalas.md) | Az importálás panelje — tipp-sor, kártyatörlés-figyelmeztetés, hibák |
| [picasa-elso-inditas.md](picasa-elso-inditas.md) | **Az első indítás `initialscan` panelje** — migrációs és tiszta-telepítés változat, geometria, a kihagyhatatlan választás |
| [picasa-mappakezelo.md](picasa-mappakezelo.md) | **A Mappakezelő TELJES specifikációja** — elrendezés és tervezővászon-geometria, az átméretezés szabályai (`winsize` → `SC_SIZE`), a fa és az öröklődő állapot, a három rádió, az arcfelismerés-kapcsoló, a három figyelmeztetés, az OK/Mégse delta-szemantikája, a Súgó URL-je |
| [picasa-lebego-ertesito.md](picasa-lebego-ertesito.md) | A lebegő értesítősáv (`CNotifierPopup`) — képernyőfelvétel- és import-értesítés, kattintás-viselkedés; a geometria és az animáció NYITOTT |
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
