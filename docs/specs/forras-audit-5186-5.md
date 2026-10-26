# A #5186 negyedik helyi kutatói köre - 10 tétel (2026-10-24)

Ez a lap a gyűjtő tíz megmaradt állítását veti össze az eredeti Picasa
forrásaival és a jelenlegi PicasaPy-kóddal. A vizsgálat helyi, statikus
forrásokra és a már meglévő Colab-képernyőképekre támaszkodik. Nem készült
kódmódosítás vagy futóalkalmazásos mérés. Az eredeti referencia binárisa a
Picasa 3.9.141.259; a jegy teljes szövegét a munkakérés adta.

## Következtetés

Hét állítás forrás szerint igazolt, és a mai kód szerkezetileg megfelel neki.
#3756 jelvénye megfelel; az eredeti caption-utak az `e64`, a fókuszút az
`e68` mezőt is használja, de a bal/jobb megfeleltetés futásmérése hiányzik.
A #4544 bináris területútja koordinátákból/float-paraméterből képszélhez korlátozott
téglalapot és képsor-másolást mutat; a látható folthatár és az eredeti
kimenet összevetése nyitott. #4482 eredeti átnevezése szintén mérésre vár.

## Bizonyíték és verdikt

| Jegy | Eredeti bizonyíték | Mai PicasaPy | Verdikt |
|---|---|---|---|
| #3729 | **mérés** (`respack.yt` `scaleslider/sliderbase` és `thumb` rétegméretei, `scaleslider.tre`; részletezve `szerkeszto-panel-meretek.md:438-459`): 9 px sín, 16 × 22 px réteg | `EditorSlider.qml:73-89` ezt a méretcsaládot adja; `TrayBar.qml:1684-1694,1799-1807` mindkét alsó sávbeli használatot `scaleslider`-ként állítja | **IGAZOLVA - megerősített.** |
| #3756 | **mérés** (Colab EN 33-35, job #58; `ui-audit-editor.md:2241-2272`): a jelvény a fókuszált kép mellett áll, a felirat viszont „Make a caption!” helyőrző. **Bináris** (`0x00566a70`, `0x00568010`, `0x005f8ac0`): caption-adatkérés `e64`-ből; a fókuszváltók (`0x0056a160`, `0x0056a680`) preview-node-ot állítanak, `e68`-at is olvasnak/továbbítanak. A bal/jobb kulcs-hozzárendelés nem bizonyított. | `PhotoViewer.qml:882-885` fókusz szerint választ sort; `:4831,4844` azt olvassa/írja. | **NYITOTT.** Az eredeti bal/jobb hozzárendelésre alkalmas futásmérés **NINCS MEG**. |
| #3826 | **bináris** (`0x008f86c8`, `0x008f86d1`); `filters-decoded.md:2557`; `filterdesc-registry.md:156`: `Size` -1…1, alap 0 | `effect_params.py:170-180`: `radsat.radius` minimum -1, maximum 1, alapérték 0 | **IGAZOLVA - megerősített.** |
| #4377 | **bináris** (`0x007fad0a`: ismétlés ki; `0x007fadbb`: zene be); eredeti `options.fen`; **mérés** (`2026-07-17 21 00 04.png`): a mappafelirat a mező fölött áll | `OptionsTabSlideshow.qml:15-22,29-37` false/true alapérték; `:47-55` a mappafelirat a mező előtt áll | **IGAZOLVA - megerősített.** |
| #4385 | **bináris** (`0x006e5ab0`, `0x006e5d70`): metrikus hiányzó kulcsok `[7,8,9,10,12]` → `10x15`, `13x18`, `15x20`, `20x25 cm`, `Contact Sheet`; **mérés** (`2026-07-17 21 00 07.png`): két oszlop, de a mentett `PrintSize0`-`PrintSize4` felülírhatja az alapot | `dpi.py:176-204,218-226` a QLocale területi rendszerét és ugyanazt az öt alapot használja; `print_controller.py:259-276` a mentett méreteket kezeli; `OptionsTabPrinting.qml:74-92` öt elemet 3 soros, oszloponként feltöltött, 3+2-es rácsba tesz | **IGAZOLVA - megerősített** az alapértékek és a szerkezeti elrendezés tekintetében. A képernyőkép önmagában nem alapérték-bizonyíték. |
| #4456 | `album.fen` 3.2; **bináris** (`0x00849750` választja a `Folder Properties` címet, `0x00cc1be8`); **mérés** (`2026-07-17 20 59 22.png`): bal oldali feliratok, kijelölt Név és Cancel | `FolderPropertiesDialog.qml:29-39,322-357,283-290`: cím, bal oldali feliratmező, szerkeszthető név és Cancel | **IGAZOLVA - megerősített** a jegyben felsorolt szerkezeti elemekre; pixel-összevetés nincs. |
| #4482 | `album.fen` 3.2: `edit name="name" filter="filename"`; **mérés** (`2026-07-17 20 59 22.png`): a Név mező kijelölt és szerkeszthető. Az eredeti sikeres átnevezés **NINCS MEG**. | `FolderPropertiesDialog.qml:213-236` hívja a rename kezelőt; `FolderPane.qml:1757` és `library_controller.py:1709-1741` továbbítja a mappa átnevezését | **NEM DÖNTHETŐ EL STATIKUSAN.** A mező és a mai átnevező út bizonyított, az eredeti sikeres mentés nem. |
| #4488 | Eredeti `options.fen` Windows-fájltípus csoportja; **mérés** (`2026-07-17 21 00 00.png`): eredeti sor- és oszlopelrendezés | `OptionsTabFileTypes.qml:7-13,28-169` a **mérés** szerinti 242/744 bal behúzást, 22 px-es sorokat és forrás szerinti sorrendet írja le | **IGAZOLVA - megerősített** a feliratok, sorrend és sorköz tekintetében; mai renderelt pixelmérés nincs. |
| #4494 | `album.fen` 3.2 `date` mező; **bináris** (`0x008d8070`: `SysDateTimePick32`, `0x50810000` stílus; `0x008d9243`: osztályfelismerés); **mérés** (`2026-07-17 20 59 22.png`): legördülő gomb látszik | `FolderPropertiesDialog.qml:397-411,641-649` a naptárgomb kattintását a felugró ablak megnyitására és a választott dátum mezőbe írására köti | **IGAZOLVA - megerősített** a vezérlőtípus és a mai működési út; pixel-összevetés nincs. |
| #4544 | **Bináris** (`0x0060a980`, `0x00847880`, `0x00848030`, `0x00848a10`, `0x00901110`, `0x00913960`, `0x00913420`): eseménykezelő, 40 bájtos rekordból téglalap, koordináták/float-paraméter alapján képszélhez korlátozott ROI és képsor-másolási út. A látható szél képletét/kimenetét mutató eredeti mérés **NINCS MEG**. Az RTTI típusnevek a 3.9-es helyi indexből valók, a célfüggvények diszasszemblyje az eredeti 3.7-es EXE-ből. | `render/retouch.py:68-71,150-161,203` relatív sugárból körmaszkot és seamlessClone-feldolgozást épít. | **NYITOTT.** A feldolgozási utak szerkezetileg eltérnek; kimeneti egyezés/eltérés nem mért. |

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
| #3756 | `0x00566a70`, `0x00568010`, `0x005f8ac0`: caption-kérés `e64`-ből; `0x0056a160`/`0x0056a680`: preview-node út és `e68` használata, bal/jobb kapcsolat nélkül | `_kijeloltSort()` fókusz szerinti sort ad át a caption-mezőnek | nyitott: a két felirattal végzett eredeti bal/jobb futásmérés hiányzik |
| #4544 | `0x00847880`: RetouchEdit-rekordból téglalap; `0x00901110` → `0x00913960` → `0x00913420`: koordináta/float-paraméter ROI- és sor-másolási út | körmaszk + irányított Poisson-gyógyítás | nyitott: a bináris látható peremképlete és azonos bemenetes eredeti/PicasaPy kimenet nincs meg |

Nem teljes a kétutas egyezés a #3756 bal/jobb feliratának hozzárendelésére, a
#4482 sikeres eredeti átnevezésére és a #4544 látható folthatárára. A #3756
felirat-gettere, illetve a #4544 terület-/másolási útja binárisból részben
azonosított; a nyitott állításokat eredeti futásméréssel kell eldönteni.

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
- #3756 - ✅ A „Selected” jelvény az eredetiben a fókuszált kép mellett áll;
  a bináris felirat-gettere az `e64` kulcsot használja (`0x00568010`), a mai
  QML fókusz szerint választ sort. ⛔ Azt, hogy az eredeti fókuszcsere mely
  képkulcs feliratát jeleníti meg, eltérő, nem üres feliratokkal nem mértem.
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
- #4544 - ✅ A bináris RetouchEdit útja 40 bájtos rekordból téglalapot képez;
  a CRetouchFilter képsorokat másoló útja is azonosított. ⛔ A látható
  folthatár és az eredeti kimenet nincs mérve.

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
| #3756: a caption-getter az `e64` kulcsot használja (`0x00568010`); a fókuszváltó preview-node-ot cserél (`0x0056a160`), de a bal/jobb leképezés nem bizonyított | A feliratsáv a `_kijeloltSort()` által kiválasztott fókuszsor feliratát olvassa | Két külön feliratú képpel Colab- és PicasaPy-kattintásos mérés, majd egymás melletti képkocka-összevetés kell. |
| #3826: `Size` -1…1, alap 0 | `radsat.radius` ugyanígy van megadva | A tartományjavítás lezárható. |
| #4377: ismétlés ki, zene be, mappacímke felül | A mai alapértékek és címke-elrendezés egyeznek | A tétel lezárható. |
| #4385: metrikus alapötös a `LOCALE_IMEASURE` alapján; két oszlop | A hiányzó mentett értékek alapja egyezik, a QML 3+2 mezőt rendez két oszlopba | Alapérték-javítás nem kell; csak a pixelmérés marad, ha azt külön kéri a jegy. |
| #4456: cím, bal feliratmező, szerkeszthető Név, Cancel | A jelenlegi QML-ben megvan | A szerkezeti tétel lezárható; pixel-egyezés nincs mérve. |
| #4482: a szerkesztett Név elfogadása átnevez | A mai OK-kezelő átnevezést hív; az eredeti sikeres művelet nincs mérve | Colabban nevezzen át mappát, majd rögzítse az új útvonalat és a mappafát. |
| #4488: fájltípus-sorok és sorköz | A címkesorrend és 22 px-es sorhely kódban egyezik | A szerkezeti állítás igazolt; mai pixel-összevetés nincs. |
| #4494: naptáras dátumvezérlő | Az eredeti natív osztály és a mai popup-út igazolt | Forrás alapján kódjavítás nem kell; renderelt pixel-egyezést nem mértem. |
| #4544: a bináris 40 bájtos rekordokból téglalapot állít elő, a filter út képsorokat másol; a látható szél képlete nincs meg | A mai renderer körmaszkot és Poisson-gyógyítást használ | Azonos bemenettel/ecsetmérettel eredeti és PicasaPy mentett kimenet, majd képpont-különbség kell; addig egyezés/eltérés nem állítható. |

**Kész, ha:** a nyitott #3756 felirat-hozzárendelés, #4482 sikeres eredeti
átnevezés és #4544 retusfolt-szél azonosított mérési adatokkal eldől; a hét
igazolt állításnál az eredeti és a jelenlegi kód bizonyítéka megmarad.

## Új kutatási jegyjavaslatok

Külön új kutatási jegyet nem javaslok. A hiányzó Colab-mérések a három
érintett állítás (#3756, #4482, #4544) közvetlen folytatásai.

## Nyitott

- #3756: készítsen két különböző, nem üres Picasa-feliratú képet; AB nézetben
  rögzítse a bal fókusz feliratszövegét, majd kattintson a jobb képbe és
  ellenőrizze, hogy a sáv követi-e a kijelölt képet. A mostani job #58 nem
  megfelelő, mert üres helyőrzőket mutat.
- #4482: Colabban írjon át egy mappanevet; ellenőrizze a mentés után az
  útvonalat, mappafát, ütközést már létező névvel és az esetleges hibajelzést.
- #4544: ugyanazt a bemeneti képet és azonos ecsetvonást futtassa az
  eredetiben; mentsen előtte-utána képet és kimeneti fájlt, majd mérje a
  folthatár átmenetét.
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
