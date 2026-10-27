# A #5186 negyedik helyi kutatói köre - 10 tétel (2026-10-24)

Ez a lap a gyűjtő tíz megmaradt állítását veti össze az eredeti Picasa
forrásaival és a jelenlegi PicasaPy-kóddal. A vizsgálat helyi, statikus
forrásokra és a már meglévő Colab-képernyőképekre támaszkodik. Nem készült
kódmódosítás vagy futóalkalmazásos mérés. Az eredeti referencia binárisa a
Picasa 3.9.141.259; a jegy teljes szövegét a munkakérés adta.

**Későbbi kiegészítés (2026-10-27):** a #5975 folytatásához job #313 két feliratú
eredeti leírása és job #318/#319 retus előtte-utána képpárja érkezett. A
#4544-hez a PicasaPy filterlánc közvetlen renderelt kimenetét is mértem a brief
reprodukciós koordinátáival és a mai alap ecsettel; az eredeti pontos
kattintás- és ecsetérték továbbra sincs meg, így az azonos paraméterű
összevetés nyitott. A PicasaPy valódi UI-kattintás nem készült el.

## Következtetés

Hét állítás forrás szerint igazolt, és a mai kód szerkezetileg megfelel neki.
#3756-ra a job #313 eredeti futásleírása megmutatja, hogy a caption a
fókuszban lévő képet követi; a mai QML is a fókusz szerinti sort olvassa, de
PicasaPy valódi kattintásos pár híján a teljes jegy nyitott. #4544-re a job
#318/#319 eredeti képpár eltérésprofilja mért; ez nem közvetlen alfa-súly és a
három vizsgált bináris függvény sem ad ilyen képletet. A PicasaPy mentett
kimenetét renderer-úton megmértem: a brief egész pontjaival és a PicasaPy
alap ecsetével számolt profil eltér az eredetitől, de az eredeti pontos
ecset-/kattintásparaméter híján ez nem bizonyít azonos paraméterű viselkedési
eltérést. #4482 eredeti átnevezése szintén mérésre vár.

## Bizonyíték és verdikt

| Jegy | Eredeti bizonyíték | Mai PicasaPy | Verdikt |
|---|---|---|---|
| #3729 | **mérés** (`respack.yt` `scaleslider/sliderbase` és `thumb` rétegméretei, `scaleslider.tre`; részletezve `szerkeszto-panel-meretek.md:438-459`): 9 px sín, 16 × 22 px réteg | `EditorSlider.qml:73-89` ezt a méretcsaládot adja; `TrayBar.qml:1684-1694,1799-1807` mindkét alsó sávbeli használatot `scaleslider`-ként állítja | **IGAZOLVA - megerősített.** |
| #3756 | **Mérés** (job #313, a briefben átadott 23., 25. és 27. képkocka-leírás): bal fókusznál `BAL FELIRAT`, jobb fókusznál `JOBB FELIRAT`; a Selected és az információs sáv is a fókuszt követi. **Bináris** (`0x00566a70`, `0x00568010`, `0x005f8ac0`): caption-adatkérés `e64`-ből; a fókuszváltók (`0x0056a160`, `0x0056a680`) preview-node-ot állítanak, `e68`-at is olvasnak/továbbítanak. | `PhotoViewer.qml` `_kijeloltSort()`-ja fókusz szerint választ sort; a `captionField` ezt olvassa és íráskor is erre a sorra hívja a kezelőt. | **NYITOTT, feltételesen egyező:** az eredeti méréssel a mai forrásút egybeesik, de PicasaPy valódi kattintásos képkockapár nincs. |
| #3826 | **bináris** (`0x008f86c8`, `0x008f86d1`); `filters-decoded.md:2557`; `filterdesc-registry.md:156`: `Size` -1…1, alap 0 | `effect_params.py:170-180`: `radsat.radius` minimum -1, maximum 1, alapérték 0 | **IGAZOLVA - megerősített.** |
| #4377 | **bináris** (`0x007fad0a`: ismétlés ki; `0x007fadbb`: zene be); eredeti `options.fen`; **mérés** (`2026-07-17 21 00 04.png`): a mappafelirat a mező fölött áll | `OptionsTabSlideshow.qml:15-22,29-37` false/true alapérték; `:47-55` a mappafelirat a mező előtt áll | **IGAZOLVA - megerősített.** |
| #4385 | **bináris** (`0x006e5ab0`, `0x006e5d70`): metrikus hiányzó kulcsok `[7,8,9,10,12]` → `10x15`, `13x18`, `15x20`, `20x25 cm`, `Contact Sheet`; **mérés** (`2026-07-17 21 00 07.png`): két oszlop, de a mentett `PrintSize0`-`PrintSize4` felülírhatja az alapot | `dpi.py:176-204,218-226` a QLocale területi rendszerét és ugyanazt az öt alapot használja; `print_controller.py:259-276` a mentett méreteket kezeli; `OptionsTabPrinting.qml:74-92` öt elemet 3 soros, oszloponként feltöltött, 3+2-es rácsba tesz | **IGAZOLVA - megerősített** az alapértékek és a szerkezeti elrendezés tekintetében. A képernyőkép önmagában nem alapérték-bizonyíték. |
| #4456 | `album.fen` 3.2; **bináris** (`0x00849750` választja a `Folder Properties` címet, `0x00cc1be8`); **mérés** (`2026-07-17 20 59 22.png`): bal oldali feliratok, kijelölt Név és Cancel | `FolderPropertiesDialog.qml:29-39,322-357,283-290`: cím, bal oldali feliratmező, szerkeszthető név és Cancel | **IGAZOLVA - megerősített** a jegyben felsorolt szerkezeti elemekre; pixel-összevetés nincs. |
| #4482 | `album.fen` 3.2: `edit name="name" filter="filename"`; **mérés** (`2026-07-17 20 59 22.png`): a Név mező kijelölt és szerkeszthető. Az eredeti sikeres átnevezés **NINCS MEG**. | `FolderPropertiesDialog.qml:213-236` hívja a rename kezelőt; `FolderPane.qml:1757` és `library_controller.py:1709-1741` továbbítja a mappa átnevezését | **NEM DÖNTHETŐ EL STATIKUSAN.** A mező és a mai átnevező út bizonyított, az eredeti sikeres mentés nem. |
| #4488 | Eredeti `options.fen` Windows-fájltípus csoportja; **mérés** (`2026-07-17 21 00 00.png`): eredeti sor- és oszlopelrendezés | `OptionsTabFileTypes.qml:7-13,28-169` a **mérés** szerinti 242/744 bal behúzást, 22 px-es sorokat és forrás szerinti sorrendet írja le | **IGAZOLVA - megerősített** a feliratok, sorrend és sorköz tekintetében; mai renderelt pixelmérés nincs. |
| #4494 | `album.fen` 3.2 `date` mező; **bináris** (`0x008d8070`: `SysDateTimePick32`, `0x50810000` stílus; `0x008d9243`: osztályfelismerés); **mérés** (`2026-07-17 20 59 22.png`): legördülő gomb látszik | `FolderPropertiesDialog.qml:397-411,641-649` a naptárgomb kattintását a felugró ablak megnyitására és a választott dátum mezőbe írására köti | **IGAZOLVA - megerősített** a vezérlőtípus és a mai működési út; pixel-összevetés nincs. |
| #4544 | **Bináris** (`0x005de8e0` → `0x005f80d0`, `0x0060a980` → `0x0060b350` → `0x0060b430`; előzmény: `0x00848030`, `0x00848a10`): slider- és eseményút részben azonosított; a tényleges effektív sugár/default/peremsúly **NINCS MEG**. **Mérés** (job #318/#319): `>12` 835 px, legnagyobb komponens 789 px, befoglaló téglalap `(25,607,46,40)`. | PicasaPy `filters=retouch=2,0bc09b801ec0aec0051f;` renderút, brief koordinátái `(47,622)`/`(123,699)`, saját alap ecset 20 → `>12` 498 px, legnagyobb 477 px, befoglaló téglalap `(31,608,33,31)`; a radiális profil is mért. | **NYITOTT.** A távoli JPEG-kontroll kizárja, hogy a foltablak eltérése pusztán tömörítési zaj legyen, de az eredeti pontos pont/ecsetsugár **NINCS MEG**, ezért azonos paraméterű egyezés/eltérés és fejlesztési igény nem állítható. |

## A két független út

Az igazolt tételeknél az A út az eredeti bináris, erőforrás vagy Colab-kép;
a B út a jelenlegi Python/QML forrás. A forrásokat egymástól függetlenül
vetettem össze.

| Jegy | A út | B út | Egyezés |
|---|---|---|---|
| #3729 | `respack.yt` rétegek + `scaleslider.tre` | `EditorSlider.qml` + a `TrayBar.qml` két bekötése | igen: 9 px / 16 × 22 px |
| #3826 | natív mezők `0x008f86c8`, `0x008f86d1` és a filter-spec | `effect_params.py` paramétertartománya | igen: -1…1, alap 0 |
| #4377 | `options.fen`, `0x007fad0a`, `0x007fadbb`, eredeti kép | QML-kapcsolók és mappafelirat | igen: ki / be / felirat a mező fölött |
| #4385 | `0x006e5ab0` és `0x006e5d70` | a QLocale szerinti öt méret és 3+2-es QML-rács | igen; a mentett értékek felülírása mindkét oldalon számít |
| #4456 | `album.fen`, a cím szövege `0x00cc1be8`, eredeti kép | `FolderPropertiesDialog.qml` | igen a cím, mezők és Cancel gomb tekintetében |
| #4488 | eredeti `options.fen` és a magyar Options-kép | `OptionsTabFileTypes.qml` | igen a sorrend és forrásban megadott sorköz tekintetében |
| #4494 | `album.fen`, vezérlő-létrehozó `0x008d8070`, osztályfelismerő `0x008d9243`, eredeti kép | dátumgomb és `DateCalendarPopup` QML-kötése | igen a dátumvezérlő és popup út tekintetében |
| #3756 | A job #313 briefben átadott futásmérése: bal fókusznál bal, jobb fókusznál jobb felirat. A bináris `e64` caption-mezője önmagában nem ad oldalnevet. | `_kijeloltSort()` a fókusz szerinti sort kapcsolja a caption-mezőhöz; PicasaPy runtime-kattintás nem futott. | A két út elvárt viselkedése egyezik, de a teljes runtime-pár nyitott. |
| #4544 | Job #318/#319 eredeti pixel- és sugárirányú profil; `0x005de8e0` slider dispatch, `0x0060a980` retus-esemény, `0x0060b350`/`0x0060b430` overlay-frissítés; a vizsgált utak nem adják meg az effektív peremsúlyt. | A PicasaPy filterlánc-kimenete a brief egész pontjaival és `brushSize=20`-szal; a közvetlen effektfüggvénnyel pixelazonos. | A mért profilok eltérnek ezen bemenetekkel; az eredeti egzakt pont/ecset hiányában ez nem azonos-paraméterű paritásítélet. A brushmező pixel-sugárra képezéséhez célzott dekompilálás kell. |

Nem teljes a kétutas, futásidejű egyezés a #3756 bal/jobb feliratának
PicasaPy-oldali párjára, a #4482 sikeres eredeti átnevezésére és a #4544
látható folthatárára. A #3756 eredeti mérése megvan (job #313); a
felirat-gettere, illetve a #4544 terület-/másolási útja binárisból részben
azonosított. A #4544 eredeti és PicasaPy renderer-profilja is megvan, de a
reprodukciós koordináták és PicasaPy-ecset nem igazoltan azonosak az eredeti
pontos beállításaival; az azonos paraméterű állítás ezért nyitott.

## Cáfoló kísérlet

A #4482 nyitott következtetését próbáltam cáfolni: hátha az eredeti sikeres
átnevezés statikusan bizonyítható. Újra ellenőriztem az `album.fen`
`edit name="name" filter="filename"` mezőjét, a párbeszédet felépítő
`0x00849750` rutint és a névmezőt mutató eredeti képet. A rutin a mezőt
felveszi a `Folder Properties` ablakba, a kép pedig szerkeszthető állapotot
mutat; egyik sem rögzíti az OK utáni új útvonalat vagy mappanevet. Ez a próbálkozás
nem cáfolja az átnevezést, és nem bizonyítja annak hiányát. Ugyanazt a
pozitív mércét alkalmaztam, mint a többi állításnál: az eredeti sikeres
átnevezés csak a mentés utáni új útvonal vagy azzal egyenértékű műveleti
bizonyíték alapján lenne igazolt. Ilyet nem találtam, ezért a #4482 nyitott
marad.

### #5975 cáfoló kör - küszöbmaszk nem azonos a blend-súllyal

A job #318/#319 JPEG-ek `max(|ΔR|,|ΔG|,|ΔB|)` eltérését 2/4/8/12/16/24/32
küszöböknél újraszámoltam, ugyanazzal a 8-szomszédos komponenskereséssel.
Küszöbönkénti `pixel / komponens / legnagyobb komponens / befoglaló téglalap xywh`:
`>2`: 40803 / 16398 / 2103 / `(16,598,59,53)`; `>4`: 4537 / 1262 / 1646 /
`(22,600,52,49)`; `>8`: 1195 / 42 / 1136 / `(24,603,49,44)`; `>12`: 835 /
17 / 789 / `(25,607,46,40)`; `>16`: 615 / 34 / 486 / `(30,613,40,32)`;
`>24`: 331 / 36 / 233 / `(32,620,37,21)`; `>32`: 202 / 32 / 148 /
`(33,621,33,19)`. A `>12` maszkon belüli, 1 px-es radiális gyűrűk nyolc
irányú külső, legalább 50%-os sűrűségi határa 19, 15, 16, 21, 19, 18, 14,
20 px (a sorrend a képen jobbra mutató iránytól, az óramutató járása szerint
halad). A falszifikáció sikeres: a küszöbölt JPEG-különbségből nem adható meg
küszöbfüggetlen pontos körsugár vagy alfa-/keverési profil. A mérés a látható
kimeneti eltérés térbeli profilját írja le; a Picasa belső súlyfüggvénye és
névleges ecsetsugara **NINCS MEG**. Ezt az ellenpróbát ugyanazzal a csatorna-
maximummal, komponensképzéssel és képpárral ellenőriztem, mint az alapmérést.

Külön ellenpróbaként ellenőriztem a régi nyomtatási spec állítását, hogy a
mai PicasaPy metrikus alapötöse `5x8`, `9x13`, `10x15`, `13x18`, `20x25 cm`.
Az eredeti `0x006e5ab0` hiányzó kulcsra adott értékeit újra leképeztem a
`0x006e5d70` szerint; a mai kód `METRIKUS_ALAPMERETEK` sora ugyanazt az öt
eredményt adja. A régi kódleírást ez cáfolja; a specet a mostani
forrásállapothoz igazítottam. Az Opciók QML-je három sort és oszloponkénti
feltöltést ír elő, ami az öt mezőt 3+2-es kétoszlopos szerkezetbe rendezi.

## A jegy „Kész, ha” pontjai

- #3729 - ✅ Az eredeti sín 9 px, fogantyú-réteg 16 × 22 px; a mai komponens
  ugyanilyen méretcsaládot használ a két alsó sávcsúszkán.
- #3756 - ✅ Az eredeti job #313 leírás szerint bal fókusznál `BAL FELIRAT`,
  jobb fókusznál `JOBB FELIRAT`; a binary getter `e64`-et kér, a mai QML a
  fókusz sort adja a caption-mezőnek. ⛔ PicasaPy kattintásos képkockapár nincs,
  ezért a jegy futásidejű kész-pontja még nyitott.
- #3826 - ✅ A „Sugár” / `Size` tartománya -1…1, alapértéke 0; a bináris
  paramétermezők és a mai paraméterleírás egyeznek.
- #4377 - ✅ Ismétlés ki, zene be, a mappaválasztó címkéje a mező fölött;
  eredeti forrás és mai QML egyezik.
- #4385 - ✅ Metrikus alapötös és kétoszlopos, 3+2-es mezőszerkezet a mai
  kódban megvan. ⛔ Mai renderelt kép pixelmérése nem történt.
- #4456 - ✅ A cím, bal oldali feliratmező, szerkeszthető Név és Cancel
  gomb szerepel az eredeti forrásban és a mai QML-ben. ⛔ Pixelmérés nincs.
- #4482 - ✅ Az eredeti Név mező szerkeszthető; a mai OK út átnevezést hív.
  ⛔ Azt, hogy az eredeti Picasa elfogadáskor ténylegesen átnevez-e, nem
  bizonyítja a FEN vagy a párbeszéd-építő. Colab-mérés kell.
- #4488 - ✅ A fájltípus-feliratok sorrendje és 22 px-es sorhelye a forrás
  és mai QML között egyezik. ⛔ Mai képpontos render-összevetés nincs.
- #4494 - ✅ Az eredeti natív dátumvezérlő és a mai naptár-popup útja forrásban
  igazolt. ⛔ Pixelmérés nincs.
- #4544 - ✅ Eredeti job #318/#319 képpár és profil megvan; a PicasaPy
  filterlánc renderer-kimenete és azonos szabályú pixel-/sugárirányú profil-mérése
  is megvan. A `>12` legnagyobb komponens eredeti/PicasaPy: 789/477 px; befoglaló téglalap:
  46×40 / 33×31 px. A távoli kontrollablak kereszteltérése átlag 0.306763,
  max 3, a célablaké átlag RGB-csatornánként 10.653462, max 60. ⛔ Az eredeti
  pontos ecsetsugár és kattintáspont nincs meg, ezért ez nem azonos paraméterű
  ítélet; valódi PicasaPy UI-kattintás sem készült.

## Javasolt jegytörzs-bővítés

„Az eredeti forrás-összevetés alapján a #3729, #3826 és #4377 állításai
igazolódnak a jelenlegi PicasaPy-forrásban. A #4385 metrikus alapötöse is
egyezik, ha nincs mentett `PrintSize0`-`PrintSize4` felülírás; az Opciók
méretválasztója három soros, kétoszlopos (3+2) rács. A #4456 és #4488
szerkezeti állításai egyeznek. A #4494 eredeti `SysDateTimePick32` dátum-
vezérlőjét a bináris és az `album.fen` igazolja; a mai QML naptár-popupot nyit.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| #3729: scaleslider 9 px sín, 16 × 22 px fogantyú | Az alsó sáv az eredeti méretcsaládot használja | A méretjavítás lezárható. |
| #3756: job #313 szerint bal fókusznál `BAL FELIRAT`, jobb fókusznál `JOBB FELIRAT`; a binary getter `e64` mezőt használ | A QML a fókusz szerinti sort olvassa/írja; PicasaPy kattintásos kimenet nem készült | A job #313 képkockáinak valódi PicasaPy-kattintásos párja és egymás melletti összevetése kell. |
| #3826: `Size` -1…1, alap 0 | `radsat.radius` ugyanígy van megadva | A tartományjavítás lezárható. |
| #4377: ismétlés ki, zene be, mappacímke felül | A mai alapértékek és címke-elrendezés egyeznek | A tétel lezárható. |
| #4385: metrikus alapötös a `LOCALE_IMEASURE` alapján; két oszlop | A hiányzó mentett értékek alapja egyezik, a QML 3+2 mezőt rendez két oszlopba | Alapérték-javítás nem kell; csak a pixelmérés marad, ha azt külön kéri a jegy. |
| #4456: cím, bal feliratmező, szerkeszthető Név, Cancel | A jelenlegi QML-ben megvan | A szerkezeti tétel lezárható; pixel-egyezés nincs mérve. |
| #4482: a szerkesztett Név elfogadása átnevez | A mai OK-kezelő átnevezést hív; az eredeti sikeres művelet nincs mérve | Colabban nevezzen át mappát, majd rögzítse az új útvonalat és a mappafát. |
| #4488: fájltípus-sorok és sorköz | A címkesorrend és 22 px-es sorhely kódban egyezik | A szerkezeti állítás igazolt; mai pixel-összevetés nincs. |
| #4494: naptáras dátumvezérlő | Az eredeti natív osztály és a mai popup-út igazolt | Forrás alapján kódjavítás nem kell; renderelt pixel-egyezést nem mértem. |
| #4544: job #318/#319 `>12` maszk: 835 px, legnagyobb komponens 789 px, 46×40 px befoglaló téglalap; a vizsgált bináris rutinok nem adnak peremsúlyt | A PicasaPy renderer a brief pontjain és saját alap ecsetével futott; `>12` legnagyobb komponens 477 px, 33×31 px befoglaló téglalap; célablak átlagos kereszteltérés 10.653462, maximum 60 | A mai mérés jelölt bemenetre eltérő profilt mutat. Az eredeti egzakt ecset-/kattintásparamétert kell rögzíteni; csak azzal ismételve dönthető el, hogy ez fejlesztési eltérés-e. |

**Kész, ha:** a nyitott #3756 felirat-hozzárendelés, #4482 sikeres eredeti
átnevezés és #4544 retusfolt-szél azonosított mérési adatokkal eldől; a hét
igazolt állításnál az eredeti és a jelenlegi kód bizonyítéka megmarad.

## Új kutatási jegyjavaslatok

Külön új kutatási jegyet nem javaslok. A hiányzó Colab-mérések a három
érintett állítás (#3756, #4482, #4544) közvetlen folytatásai.

## Nyitott

- #3756: a job #313 két feliratú eredeti felvétel mellé kell PicasaPy-
  kattintásos képpár bal, majd jobb fókusznál. A helyi GUI-próba X11 és
  Wayland kijelző-kapcsolódási engedélyezési hibával leállt; Xvfb alatt a Qt
  XCB plugin betöltéséhez szükséges xcb-cursor0 hiányzik.
- #4482: Colabban írjon át egy mappanevet; ellenőrizze a mentés után az
  útvonalat, mappafát, ütközést már létező névvel és az esetleges hibajelzést.
- #4544: az eredeti és PicasaPy renderer pixel- és sugárirányú profilja megvan. Az
  eredeti pontos ecsetszám és kattintáspont **NINCS MEG**; a briefben átadott
  egész koordináták reprodukciós jelöltek. Az eredeti `[this+0x1c]` slidermező
  effektív képpont-sugár leképezése **NINCS MEG**; a meglévő Ghidra-kimenet a
  `0x0060b430` hívását mutatja, de nem a függvény törzsét. Azonos paraméterű
  végső ítélethez Colab-metaadat vagy új, pontosan rögzített eredeti futás kell.

Ghidra-kör kell: 0x0060b430 - a 0x0060a980 kezelő [this+0x1c] brushslider értékéből a kurzorgyűrű és az effektív, forrásképi retussugár pontos leképezése és egysége [blokkoló]

- A #4385, #4456, #4488 és #4494 mai renderelt pixel-összevetése nem készült;
  a leírt értékek és vezérlőutak statikusan igazoltak.

## Módosított fájlok

- `docs/specs/forras-audit-5186-5.md` - a tíz tétel eredeti bizonyítéka, mai
  kód-összevetése, verdiktjei és konkrét nyitott mérései.
- `docs/specs/forras-audit-5186-1.md` - #3756 caption-getter és nyitott
  bal/jobb hozzárendelés.
- `docs/specs/forras-audit-5186-2.md` - #4544 RetouchEdit/filter területút,
  mai kód és nyitott pixelhatár.
- `docs/specs/forras-audit-5186-5.md` - a #3756/#4544 összefoglaló
  bizonyítékai és elfogadási pontjai frissítve.
- `docs/specs/picasa-nyomtatas.md` - #5492 óta friss metrikus alapötös és
  #4385 kétoszlopos forrás-összevetése.
- `docs/specs/picasa-fen-dialogs.md` - a #4494 dátumvezérlő natív
  bináris-horgonya.
- `docs/specs/ui-audit-editor.md` - a #3756 mai QML-állapotának dátumozott
  helyesbítése.
- `docs/specs/00-index.md` - hivatkozás erre a kutatói körre.
