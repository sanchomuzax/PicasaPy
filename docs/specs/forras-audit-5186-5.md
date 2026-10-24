# A #5186 negyedik helyi kutatói köre - 10 tétel (2026-10-24)

Ez a lap a gyűjtő tíz megmaradt állítását veti össze az eredeti Picasa
forrásaival és a jelenlegi PicasaPy-kóddal. A vizsgálat helyi, statikus
forrásokra és a már meglévő Colab-képernyőképekre támaszkodik. Nem készült
kódmódosítás vagy futóalkalmazásos mérés. Az eredeti referencia binárisa a
Picasa 3.9.141.259; a jegy teljes szövegét a munkakérés adta.

## Következtetés

Hét állítás forrás szerint igazolt, és a mai kód szerkezetileg megfelel neki.
#3756 jelvénye megfelel, de a feliratsáv eredeti kép-hozzárendelése a meglévő
felvételből nem olvasható ki; #4482 eredeti átnevezése és #4544 retusfolt-
széle továbbra is mérésre vár. Eltérésre nincs elegendő bizonyíték.

## Bizonyíték és verdikt

| Jegy | Eredeti bizonyíték | Mai PicasaPy | Verdikt |
|---|---|---|---|
| #3729 | **mérés** (`respack.yt` `scaleslider/sliderbase` és `thumb` rétegméretei, `scaleslider.tre`; részletezve `szerkeszto-panel-meretek.md:438-459`): 9 px sín, 16 × 22 px réteg | `EditorSlider.qml:73-89` ezt a méretcsaládot adja; `TrayBar.qml:1684-1694,1799-1807` mindkét alsó sávbeli használatot `scaleslider`-ként állítja | **IGAZOLVA - megerősített.** |
| #3756 | **mérés** (Colab EN 33-35; `ui-audit-editor.md:2241-2272`): a jelvény a fókuszált kép mellett, a margóban áll. A képeken a felirat mindenütt „Make a caption!” helyőrző | `PhotoViewer.qml:4237-4298` a jelvényt a fókuszált félhez számolja; `:875-879,4675-4690` a feliratsávot a kijelölt képsorhoz köti | **NEM DÖNTHETŐ EL STATIKUSAN** a teljes állítás: a jelvény egyezik, az eredeti felirat-hozzárendelés nem látható (**NINCS MEG**). |
| #3826 | **bináris** (`0x008f86c8`, `0x008f86d1`); `filters-decoded.md:2557`; `filterdesc-registry.md:156`: `Size` -1…1, alap 0 | `effect_params.py:170-180`: `radsat.radius` minimum -1, maximum 1, alapérték 0 | **IGAZOLVA - megerősített.** |
| #4377 | **bináris** (`0x007fad0a`: ismétlés ki; `0x007fadbb`: zene be); eredeti `options.fen`; **mérés** (`2026-07-17 21 00 04.png`): a mappafelirat a mező fölött áll | `OptionsTabSlideshow.qml:15-22,29-37` false/true alapérték; `:47-55` a mappafelirat a mező előtt áll | **IGAZOLVA - megerősített.** |
| #4385 | **bináris** (`0x006e5ab0`, `0x006e5d70`): metrikus hiányzó kulcsok `[7,8,9,10,12]` → `10x15`, `13x18`, `15x20`, `20x25 cm`, `Contact Sheet`; **mérés** (`2026-07-17 21 00 07.png`): két oszlop, de a mentett `PrintSize0`-`PrintSize4` felülírhatja az alapot | `dpi.py:176-204,218-226` a QLocale területi rendszerét és ugyanazt az öt alapot használja; `print_controller.py:259-276` a mentett méreteket kezeli; `OptionsTabPrinting.qml:74-92` öt elemet 3 soros, oszloponként feltöltött, 3+2-es rácsba tesz | **IGAZOLVA - megerősített** az alapértékek és a szerkezeti elrendezés tekintetében. A képernyőkép önmagában nem alapérték-bizonyíték. |
| #4456 | `album.fen` 3.2; **bináris** (`0x00849750` választja a `Folder Properties` címet, `0x00cc1be8`); **mérés** (`2026-07-17 20 59 22.png`): bal oldali feliratok, kijelölt Név és Cancel | `FolderPropertiesDialog.qml:29-39,322-357,283-290`: cím, bal oldali feliratmező, szerkeszthető név és Cancel | **IGAZOLVA - megerősített** a jegyben felsorolt szerkezeti elemekre; pixel-összevetés nincs. |
| #4482 | `album.fen` 3.2: `edit name="name" filter="filename"`; **mérés** (`2026-07-17 20 59 22.png`): a Név mező kijelölt és szerkeszthető. Az eredeti sikeres átnevezés **NINCS MEG**. | `FolderPropertiesDialog.qml:213-236` hívja a rename kezelőt; `FolderPane.qml:1757` és `library_controller.py:1709-1741` továbbítja a mappa átnevezését | **NEM DÖNTHETŐ EL STATIKUSAN.** A mező és a mai átnevező út bizonyított, az eredeti sikeres mentés nem. |
| #4488 | Eredeti `options.fen` Windows-fájltípus csoportja; **mérés** (`2026-07-17 21 00 00.png`): eredeti sor- és oszlopelrendezés | `OptionsTabFileTypes.qml:7-13,28-169` a **mérés** szerinti 242/744 bal behúzást, 22 px-es sorokat és forrás szerinti sorrendet írja le | **IGAZOLVA - megerősített** a feliratok, sorrend és sorköz tekintetében; mai renderelt pixelmérés nincs. |
| #4494 | `album.fen` 3.2 `date` mező; **bináris** (`0x008d8070`: `SysDateTimePick32`, `0x50810000` stílus; `0x008d9243`: osztályfelismerés); **mérés** (`2026-07-17 20 59 22.png`): legördülő gomb látszik | `FolderPropertiesDialog.qml:397-411,641-649` a naptárgomb kattintását a felugró ablak megnyitására és a választott dátum mezőbe írására köti | **IGAZOLVA - megerősített** a vezérlőtípus és a mai működési út; pixel-összevetés nincs. |
| #4544 | `editpanel.tre:958-963` az eredeti retusáló eszközt és ecsetvezérlőt azonosítja; a pontos széleffektet mutató eredeti kimenet **NINCS MEG** a képleltárban vagy a mérőadat-archívumban | `render/retouch.py` irányított Poisson-gyógyítást használ | **NEM DÖNTHETŐ EL STATIKUSAN.** Az eredeti retusfolt szélének kimenetét nem mértem. |

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

Nem teljes a kétutas egyezés a #3756 feliratsáv-adatára, a #4482 sikeres
eredeti átnevezésre és a #4544 retusfolt-szélre; ezekhez az eredeti
viselkedést kell még mérni.

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
  a mai QML is a fókuszált félhez teszi. ⛔ Az eredeti feliratsávot eltérő,
  nem üres feliratú képekkel nem mértem.
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
- #4544 - ✅ Az eredeti retusáló eszköz léte igazolt. ⛔ A retusfolt szélének
  eredeti kimenetét nem hasonlítottam össze.

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
| #3756: a jelvény a fókuszált kép mellett; a feliratsáv kép-hozzárendelését a meglévő felvétel nem mutatja | A jelvény és feliratsáv a kijelölt fókuszsorhoz kötődik | Külön feliratú két képpel Colab-mérés kell a sáv hozzárendelésére. |
| #3826: `Size` -1…1, alap 0 | `radsat.radius` ugyanígy van megadva | A tartományjavítás lezárható. |
| #4377: ismétlés ki, zene be, mappacímke felül | A mai alapértékek és címke-elrendezés egyeznek | A tétel lezárható. |
| #4385: metrikus alapötös a `LOCALE_IMEASURE` alapján; két oszlop | A hiányzó mentett értékek alapja egyezik, a QML 3+2 mezőt rendez két oszlopba | Alapérték-javítás nem kell; csak a pixelmérés marad, ha azt külön kéri a jegy. |
| #4456: cím, bal feliratmező, szerkeszthető Név, Cancel | A jelenlegi QML-ben megvan | A szerkezeti tétel lezárható; pixel-egyezés nincs mérve. |
| #4482: a szerkesztett Név elfogadása átnevez | A mai OK-kezelő átnevezést hív; az eredeti sikeres művelet nincs mérve | Colabban nevezzen át mappát, majd rögzítse az új útvonalat és a mappafát. |
| #4488: fájltípus-sorok és sorköz | A címkesorrend és 22 px-es sorhely kódban egyezik | A szerkezeti állítás igazolt; mai pixel-összevetés nincs. |
| #4494: naptáras dátumvezérlő | Az eredeti natív osztály és a mai popup-út igazolt | Forrás alapján kódjavítás nem kell; renderelt pixel-egyezést nem mértem. |
| #4544: a folt széle a környezetbe olvad | Az eredeti kimenet és a mai renderer nincs azonos mintán összevetve | Ne állítsunk egyezést/eltérést; kérjünk azonos bemenetes Colab-kimenetet. |

**Kész, ha:** a nyitott #3756 felirat-hozzárendelés, #4482 sikeres eredeti
átnevezés és #4544 retusfolt-szél azonosított mérési adatokkal eldől; a hét
igazolt állításnál az eredeti és a jelenlegi kód bizonyítéka megmarad.

## Új kutatási jegyjavaslatok

Külön új kutatási jegyet nem javaslok. A hiányzó Colab-mérések a három
érintett állítás (#3756, #4482, #4544) közvetlen folytatásai.

## Nyitott

- #3756: készítsen két különböző, nem üres Picasa-feliratú képet; AB nézetben
  rögzítse a bal fókusz feliratszövegét, majd kattintson a jobb képbe és
  ellenőrizze, hogy a sáv követi-e a kijelölt képet.
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
- `docs/specs/forras-audit-5186-1.md` - #3756 feliratsáv-állításának
  bizonytalansága és a mai kódállapot rögzítése.
- `docs/specs/forras-audit-5186-2.md` - #4385 és #4494 elavult
  megállapításainak helyesbítése.
- `docs/specs/picasa-nyomtatas.md` - #5492 óta friss metrikus alapötös és
  #4385 kétoszlopos forrás-összevetése.
- `docs/specs/picasa-fen-dialogs.md` - a #4494 dátumvezérlő natív
  bináris-horgonya.
- `docs/specs/ui-audit-editor.md` - a #3756 mai QML-állapotának dátumozott
  helyesbítése.
- `docs/specs/00-index.md` - hivatkozás erre a kutatói körre.
