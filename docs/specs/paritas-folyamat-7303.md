# A Helyek (geocímkézés) teljes folyamata az eredeti Picasával összevetve: belépési pontok, ablak, hatás

Ez a lap a 7303-as kérdésre szűkít: az eredeti Picasa Helyek panelje, a hely keresése és hozzárendelése, a térkép, a geocímke törlése és a Google Earth menüútja, a PicasaPy mai viselkedésével összevetve.

Az eredeti programot nem futtattam. Az eredeti oldal forrása a statikusan olvasott Picasa 3.9.141.259 bináris és a telepített runtime/geotag/ állományok. A 7303-hoz illő futtatott felvételt nem találtam. A job-225 csak az Eszközök menü Geotag almenüjének jelenlétét mutatja; a kb-2 felvétel a Ctrl+Shift+G működését méri Google Earth nélkül.

## 1. Belépési pontok

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Nézet > Places: ID_VIEW_PLACES=0x9d6d, majd thumbui/places_toggle (0x0065abb4) és a 0x005d9760 fiókvezérlő. A menüépítő 0x00559150. A Places a jobb fiók négy, egymást kizáró lapjának egyike. | PicasaViewMenu.qml:131-145; a panel ikonja TrayTopRow.qml:244-250; a fiók állapota MainRightDrawer.qml:29-48,117. | A panel elérési útja egyezik. Az eredeti aktív lap állapotának tartós megjegyzése nem dőlt el: a Preferences\active_metadata_tab olvasásai ismertek, író nem került elő (picasa-menu-parancsok-viselkedes.md:2354-2365). |
| Ctrl+Shift+G: 0x005e6547 -> 0x00600580, a Geotag With Google Earth... parancs. A 0x00600580 ellenőrzi a Google Earth telepítését. A kb-2 felvételen hiányzó Earth mellett Warning párbeszéd nyílt, Escape bezárta (picasa-gyorsbillentyuk.md:2727,2780). | MainKeyboardShortcuts.qml:177-184: ugyanaz a billentyű a Helyek fiókot nyitja; a kötés csak könyvtári nézetben aktív és diavetítés alatt tiltott. | Ismert, szándékos termékeltérés: az Earth-integrációt nem kell visszaépíteni. A jelenlegi billentyű-hozzárendelés maradhat; a súgó a Places-panelt nevezze meg. |
| Eszközök > Geotag: Geotag With Google Earth... (0x9db4, 0x005cc825 -> 0x00600580), Clear Geotags (0x9db5 -> 0x00600670), View in Google Earth... (0x9d9e) és Export to Google Earth File (0x9db0). A telepítés hiányánál a 0x00600580 telepítési üzenetet ad; az ID_PICTURE_GEOUNTAG a ClearGeoTag::warn kérdésen megy át. | PicasaToolsMenu.qml:118-153; a törlési kérdés MainMenuBar.qml:306-308 és MainDialogs.qml:28-50. | A törlés, megtekintés és export helyi párja megvan. A Google Earth-geotag menüpont hiányzik a PicasaPy-ból, ez a megszűnt külső kliens miatt elfogadott eltérés. |
| A GeoPanel címe Places (0x0064ec30); a fiók fejlécének places_toggle vezérlője szintén belépési pont (0x005d9760, 0x0065abb4). A panelen belül az Add a new place... gomb és a jelölő buborékának Search / Erase műveletei is vannak. | Helyek panel és jelölőbuborék: PlacesPanel.qml:72-99,215-247,282-314; PlacesMarker.qml:40-80. | A panel és a jelölőből indított helyi műveletek megvannak. A fotórács helyi menüjében külön geocímke-parancsot nem azonosítottam; ennek hiánya az eredeti programban nincs bizonyítva. |
| Menüparancsok üres kijelölésnél való tiltása, illetve az eredeti panel nyitási feltételei: NINCS MEG. A vizsgált függvények a kijelölés objektumát olvassák, ez nem bizonyítja a menüpont engedélyezési szabályát. | A panel beállító művelete üres sorlistánál visszatér (PlacesPanel.qml:300-309, geo_controller.py:105-123); a menüs törlő párbeszéd üres kijelölésnél nem nyílik (MainDialogs.qml:40-42). | Az eredeti engedélyezettséget futtatott Picasa-felvétellel vagy teljes menüállapotot feltáró célzott Ghidra-körrel kell eldönteni. |

## 2. Ablak, térkép, keresés és megjegyzett állapot

Az eredeti Places nézet egy Google Maps v3 térképet tartalmazó helyi HTML-oldal. A v3 JavaScript kezdő térképe ROADMAP, középpontja 40.979898,-98.261719, nagyítása 4 (runtime/geotag/picasa_geopanel_bin_v3.js:18). A bináris a runtime/geotag/geopanelscript_v3.html oldalt tölti be (0x00650ba0), az oldal pedig a Google Maps API-t tölti le (geopanelscript_v3.html:63-64). A Google online címkeresője címből helyet keres, majd jelölőt nyit; keresési hibaüzenete: Sorry, search failed. Please try a different address. (geopanelscript_v3.html:72-74, picasa_geopanel_bin_v3.js:48-49). Az alap térképtípus és kameraérték forráskódból ismert, de az ablak bezárása utáni vagy következő indításkori kameraállapot megjegyzése NINCS MEG.

Az eredeti Picasa a `Preferences\maptype` kulcsból visszaolvassa a típust, és picasa.setMapType(%d) hívást ad a v3 oldalnak. A v3 függvény üres, ezért a mentett típus visszaállítása ebben a változatban nem történik meg (picasa-helyek-panel.md:5.4). Az active_metadata_tab kulcsot a panelvezérlő olvassa, de a vizsgált indexben nem találtunk író útvonalat (picasa-menu-parancsok-viselkedes.md:2354-2365). A két beállításból nem következik, hogy a panelkamera vagy a kiválasztott lap teljes állapota megmarad.

PicasaPy-ban a Places panel a képek helyeit térképen mutatja, egy helyi szövegszűrővel. A kereső a már látható jelölők fájlnevét, feliratát, kulcsszavait és mappanevét vizsgálja; nem indít címkeresést (PlacesPanel.qml:28-42,215-247,312-314). A térkép QtLocation `osm` plugint használ, üres jelölőlista esetén Budapestre, 47.4979,19.0402 középpontra és 4 nagyításra áll (PlacesMap.qml:78-90). Jelölők érkezésekor a középpont a jelölők koordinátáinak átlaga lesz (PlacesMap.qml:62-70,173-174). A térkép és a kereső állapota a panel példányának helyi QML-állapota; újraindítások közötti megőrzést a vizsgált út nem mutat.

## 3. Kérdések és megszakítás

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Hely beállításakor a geotag: parancs 0x006520d0-nál %u,%f,%f mezőket olvas, majd 0x00652520-at hívja. A kijelölés 20 elem fölött GeoPanel::geotag_warning_change kérdés jelenik meg; Mégse ág a per-kép ciklus előtt 0xf4242 értékkel tér vissza (0x00652585-0x0065260a). | MainDialogs.qml:162-199; geo_controller.py:105-123; küszöbértékek a geo_controller.py:29-39,125-137 részen. | A 20 elem fölötti kérdés és a küszöb alatti közvetlen beállítás megfelel a feltárt eredeti ágnak. |
| Paneles helytörlés: cleargeotag: -> 0x00652760; a 0x006524c0 számláló alapján 5-nél több geocímkézett elemnél GeoPanel::geotag_warning_clear kérdés jelenik meg. A Mégse ág a törlő ciklus előtt visszatér (0x006527ad-0x0065283a). | MainDialogs.qml:271-303; geo_controller.py:139-166. A mai számláló csak PhotoRecord.geotag ini-értéket néz (geo_controller.py:140-151). | A számláló bemenete eltérhet, ha az eredeti predikátum EXIF-et is figyelembe vett. A 0x006524c0 virtuális predikátumának jelentése nyitott; ne nyissunk fejlesztési jegyet, amíg ez nincs feloldva. |
| A térképen új hely beállításánál az eredeti Put photo(s) here? vagy Move photo(s) here? szöveget használ, koordinátától és meglévő jelölőtől függően; a két felirat a v3 szkriptben van. A pontos vegyes kijelölési feltétel NINCS MEG. | Jobb kattintásnál a Places panel a >20 beállító kérdést használja (MainDialogs.qml:162-199, PlacesMap.qml:116-122). Rácsról ejtésnél mindig Move vagy Put kérdés nyílik, a jelenlegi INI-geocímkék száma alapján (MainDialogs.qml:203-239). | A térképre jobb kattintás és a rácsból ejtés ma nem azonos kérdésutat használja. Az eredeti vegyes kijelölési szabályhoz mérés kell. |
| Az Eszközök menü Clear Geotags útja a ClearGeoTag::warn szöveggel Igen/Nem választ kér; a disassembly alapértelmezett választása No. A panel saját kérdése külön szövegű és küszöbös. | A menü mindig a külön clearGeotagDialog kérdést nyitja (MainDialogs.qml:28-50); a panel külön küszöbös dialógust használ (MainDialogs.qml:271-303). | A kérdés szétválasztása és a panel küszöbe megfelel a megfigyelt útvonalnak. Az eredeti tényleges paneldialógus felvétele hiányzik. |

## 4. Helyi hatás: fájl, INI, index és felület

### 4.1 Eredeti Picasa

- Geotag parser: 0x006520d0 kezeli a geotag:, cleargeotag: és `showphotos`: üzeneteket. A hely beállítása a 0x00652520, törlése a 0x00652760 útján megy. A beállítás a kijelölt képeken vtable +0x70 és +0x68 metódusokat hív; utána 0x00653bf0 callback/object-életciklus út és 0x0064f980 panelfrissítés fut.
- Törlési út cáfolata: a paneles 0x00652760 és a menüs 0x00600670 is 0x006beef0-et hív a kiválasztott elemekre. Mindkét út adatfrissítő értesítést is küld: a paneles út 0x00653bf0 és 0x0064f980, a menüs út 0x006022a0 felé megy. Ez nem támasztja alá a korábbi picasa-helyek-panel.md 2. és 6. szakaszának azt az állítását, hogy a panel csak .picasa.ini-t ír, míg a menü az EXIF-fájlt írja. A közös helperből az sem következik, hogy semmilyen háttérírás nincs.
- .picasa.ini: a `0x007d55f0` szerializáló formázza a `geotag` kulcsot, %lf,%lf mezőkkel. A most feltárt híváslánc nem kapcsolta ezt a szerializáló hívást a 0x00652520 vagy 0x00652760 művelethez. Ezért a panel műveletének .picasa.ini hatása NINCS MEG, bár a formátum és az általános szerializáló léte bizonyított.
- EXIF/GPS, adatbázis és index: GPS-kulcsnevek és külön GPS-olvasó utak vannak a binárisban, de a Places művelettől a képíróig vagy az adatbázis-frissítésig vezető út NINCS MEG. A PicasaPy SQLite-indexe nem vonatkozik az eredeti Picasára; az eredeti saját katalógusának Places-frissítése itt nincs feloldva.
- Rács, bal hasáb, állapotsor, háttérmunka: a panel és a kijelölés frissítésére vannak callbackek, de a teljes képernyőhatás, állapotsor, háttéríró és mappa-hasáb frissítése NINCS MEG futtatott Places felvétel vagy célzott dekompilálás nélkül.

### 4.2 PicasaPy

- A beállító út a `document.with_value(photo.name, "geotag", value)` hívást adja át; a törlő út `document.with_removed(photo.name, "geotag")` hívást ad át. A vizsgált geotag út nem hív EXIF-írót (geo_controller.py:105-123,154-166). Ezért a rögzített EXIF GPS olvasásra marad, törléskor is olvasható marad (`metadata/gps.py:176-186`).
- A közös _apply_batch fotókat mappa szerint csoportosít, update_document(..., backup=True) hívást végez, mappánként szinkronizálja az indexet, majd frissíti a nézetet (photo_ops_write_text_mixin.py:110-131). Az ini-író mentés előtt .picasa.ini.bak másolatot készít a létező célról és atomikus mentési útvonalat használ (ini/io.py:212-270,292-360). Ez mentési másolat, nem felhasználói Visszavonás.
- Az indexelő a geotag= értéket geotag_ini mezőbe szinkronizálja; a Places-lista .picasa.ini vagy EXIF GPS alapján épül (index/sync_photos.py:141-164, index/queries.py:498-513). Így az ini-kulcs törlése után egy EXIF-hely továbbra is megjelenhet a listában.
- Sikeres írás után geoChanged frissíti a jelölőket; írási hiba esetén a geoWriteFailed üzenet a hibasávba kerül, és nem bocsátódik ki geoChanged (geo_controller.py:174-181, MainErrorBanner.qml:93-96). A mappánként soros írás miatt későbbi mappa hibája előtt korábbi mappák már elmentődhettek. Ez a kódsorrendből következik, futtatott hibapróba nincs.
- Hálózati térképhibánál az offline állapotot a Places panel külön felirattal jelzi; hiányzó QtLocation modulnál külön tartaléküzenet van, és a helylista/törlőgomb térkép nélkül is elérhető (PlacesMap.qml:38-45,78-90, PlacesPanel.qml:133-188,251-295). A mai offline felirat még Google Maps-et nevez meg, miközben a térkép QtLocation `osm` plugint használ. Ez a szöveg pontatlan.
- A vizsgált Places írási útban nincs undo-hívás. Ebből nem következik, hogy az app más globális felületén nincs ilyen lehetőség; a geocímke felhasználói undo-viselkedése mindkét programban NINCS MEG.

## 5. Eredeti / nálunk / teendő összefoglaló

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| View > Places (0x00559150, 0x9d6d, 0x0065abb4): a GeoPanel nyílik. | PicasaViewMenu.qml:131-145, TrayTopRow.qml:244-250, MainRightDrawer.qml:117. | Egyező panel-hozzáférés; nincs fejlesztési teendő. A teljes állapotmegőrzés nyitott. |
| Ctrl+Shift+G (0x005e6547 -> 0x00600580): Google Earth geotag akció. A hiányzó telepítést a kb-2 mérés Warning ablakkal igazolja. | MainKeyboardShortcuts.qml:177-184: Places fiók nyílik. | Szándékos, platformhoz kötött eltérés. Az Earth-integráció pótlása nem cél; a mai hozzárendelést a felhasználói súgó mondja ki. |
| Google Maps API v3 `Geocoder`-alapú címkeresés (0x00650ba0 által betöltött runtime/geotag/ oldal). | PlacesPanel.qml:28-42,215-247,312-314: helyi metadata-szűrés; PlacesMap.qml:78-90: OSM plugin. | Szolgáltatáspótlási feladat nincs; a különbség a megszűnt online út és a mai helyi keresés. |
| Clear Geotags panelen és menüből; mindkettő közös 0x006beef0 helperen át. A végső EXIF/INI írási hatás nincs bizonyítva. | geo_controller.py:154-181: csak ini-kulcs eltávolítása. | Előbb Ghidra-körrel kell a régi út tartós hatását megállapítani; az EXIF-törlést ne feltételezzük. |
| Offline térkép hiba: az eredeti HTML Picasa failed to initialize Google Maps üzenetet mutat (geopanelscript_v3.html:70-74). | PlacesPanel.qml:178-188: ugyanazt a Google Maps nevet mutatja, de a mai plugint a PlacesMap.qml:78-89 OSM-ként deklarálja. | Fejlesztői jegyjavaslat: a mai offline felirat legyen szolgáltatófüggetlen, mert nem Google Maps komponens áll mögötte. A helyi adatok szerkesztése és a térképszolgáltatás-csere ne bővüljön. |

### Fejlesztői jegytörzs javaslata

**Cím:** Helyek panel: a hálózati térképhiba ne Google Maps-et nevezzen meg

**Eredeti:** 0x00650ba0 a runtime/geotag/geopanelscript_v3.html oldalt tölti be; az eredeti oldal Google Maps API v3-at használ, és a hibaüzenet Google Maps inicializálási hibát nevez meg.

**Nálunk:** PlacesMap.qml:78-89 QtLocation `osm` plugint használ, de PlacesPanel.qml:178-188 offline üzenete Google Maps-et említ.

**Teendő:** írjuk át az offline térképüzenetet szolgáltatófüggetlen hálózati/térképcsempe hibára. Ne vezessünk be új térképszolgáltatást.

**Kész, ha:**

- a QtLocation ConnectionError állapot szolgáltatófüggetlen üzenetet mutat;
- a térkép nélküli helylista és a geocímke törlése továbbra is elérhető;
- az üzenet nem állít Google Maps-függőséget.

**Cím:** A Ctrl+Shift+G súgója a Helyek panelt nevezze meg

**Eredeti:** 0x005e6547 -> 0x00600580 a Google Earth geotag műveletre jut; a kb-2 felvételen a hiányzó kliens Warning ablakot mutatott.

**Nálunk:** MainKeyboardShortcuts.qml:177-185 a Helyek fiókot nyitja.

**Teendő:** a felhasználói billentyűsúgóban nevezzük meg a jelenlegi Helyek-panel műveletet. A külső Earth funkció ne kerüljön vissza.

**Kész, ha:**

- a billentyűsúgó a Ctrl+Shift+G billentyűt a Helyek panelhez rendeli;
- a súgó jelzi, hogy ez a könyvtári nézetben érhető el.

**Cím:** A Helyek keresője jelezze, hogy a fotók adataiban szűr

**Eredeti:** 0x0064f090 a v3 térképoldali picasa.search hívást építi; a telepített JavaScript Google Maps `Geocoder` címet keres (picasa_geopanel_bin_v3.js:48-49).

**Nálunk:** PlacesPanel.qml:28-42,215-247,312-314 név, felirat, kulcsszó és mappanév szerint szűr, hálózati keresés nélkül.

**Teendő:** a mező súgója vagy helyőrzője mondja ki, hogy a keresés a fotóadatok között történik. Online címkeresőt ne vezessünk be.

**Kész, ha:**

- a kereső magyarázata felsorolja a helyben keresett fotóadatokat;
- a keresés helyi marad, és a helytalálat nem igényel hálózatot.

## 6. Bizonyítottsági fok és független utak

**Összkép: nyitott.** A Ctrl+Shift+G külső Google Earth útja és a hiányzó kliensnél megjelenő Warning két független forrásból egyezik: bináris hívási út és a kb-2 futtatott felvétel. A Tools menü Geotag almenüjének jelenlétét a bináris menüépítő és a job-225 képernyőkép egymástól függetlenül igazolja. A Places beállító/törlő ágak küszöbe és hívási sorrendje feltételes, mert itt az utasítási út az egyetlen bizonyítási mód. A feladat fő hatáskérdése, hogy az eredeti Places beállítás/törlés pontosan mit ír .picasa.ini-be, EXIF-be vagy adatbázisba, nincs eldöntve. A geotag futtatott felvétel hiánya miatt az eredeti hiba-, írásvédettségi, megszakítási és visszavonási viselkedés sem igazolt.

- **A út:** a 0x006520d0, 0x00652520, 0x00652760, 0x00600670, 0x006beef0, 0x00653bf0 és 0x0064f980 célzott utasításszintű olvasása. Ez a parser, a küszöbök, a közös törlő segédfüggvény és a UI-frissítő hívások sorrendjét mutatja. A paneles és menüs törlő ág külön hívási helye két útvonal, de ugyanabban a binárisban van.
- **B út:** a kb-2 futtatott Picasa-mérés közvetlenül ellenőrzi a Ctrl+Shift+G hatását; ez egyezik a bináris hívási útjával. A job-225 függetlenül azt mutatja, hogy az Eszközök menüben a Geotag almenü látszik, de a gyermekműveleteket nem méri. A telepített HTML/JavaScript az eredeti térkép és keresés külön forrásrétege; a PicasaPy QML/Python/INI/index kódja a mai út forrása. A korábbi spec-lapok tájékozódást adnak, nem számítanak önálló bizonyítási útnak.
- **A és B eredménye:** a gyorsbillentyű és a hiányzó Earth-üzenet egyezik. A Places tárolóhatására nincs B út, ezért az a rész nyitott.
- **Cáfoló kísérlet:** azt próbáltam igazolni vagy cáfolni, hogy a paneles Clear és a menübeli Clear két eltérő íróút, egyik ini-, másik EXIF-törléssel. Külön disassembly olvasással mindkét hívási ág ugyanahhoz a 0x006beef0 helperhez vezet, ezért a külön helperre alapozott hipotézis megdőlt. Ellenpróbaként megvizsgáltam magát a helper utasításait is: hash-tároló művelet látszik, közvetlen fájlírás nem. Az ellenpróba ugyanilyen statikus kódelemzés, nem független futtatott adateltérés; nem bizonyítja, hogy későbbi eseménykezelő nem ír lemezre, ezért a végső storage-kérdés nyitva marad.

## 7. Nyitott kérdések

- Ghidra-kör kell: 0x00652520 - a vtable +0x68 és +0x70 hívások mely fotóadatot módosítják, és milyen út menti az új helyet .picasa.ini-be vagy EXIF GPS mezőbe? [blokkoló]
- Ghidra-kör kell: 0x006beef0 - a két Clear út közös helperje mely adattárolót módosítja, és mely esemény vagy író végzi a tartós ini/EXIF változtatást? [blokkoló]
- Ghidra-kör kell: 0x00600670 - a menüs törlés utáni 0x006022a0 értesítés mely katalógus/index/frissítési útvonalakat indít? [blokkoló]
- Eredeti Places művelet írásvédett mappában, hálózati megosztáson és megszakításkor: NINCS MEG; célzott Picasa-felvétel és a fenti íróút feltárása szükséges.
- Eredeti és PicasaPy felhasználói Visszavonás: NINCS MEG; célzott felületi mérés és a geocímke műveletet fogadó undo-út ellenőrzése szükséges.
- Eredeti grid context menu geocímke-út és a menüpont engedélyezési feltétele: NINCS MEG; teljes helyi menü mérés szükséges.
- Az eredeti kiválasztott lap és térkép kameraállapot következő megnyitáskor megmarad-e: NINCS MEG; panel bezárás/újranyitás és program-újraindítás felvétel szükséges.

## 8. Vizsgálatkor átnézett korábbi anyagok

- `rg -rn "job-[0-9]" docs/specs/` és a Places/geotag kulcsszavas ellenőrzés: a job-225 az Eszközök menüben a Geotag almenüt mutatja, a kb-2 a Ctrl+Shift+G Warning ablakát; egyik sem rögzíti a teljes Places adatírást.
- A meroadat.tar 944 bejegyzéses archívumának olvasási listája: tíz fő címke, `geo/gps/place/geotag/7303` nevű tag nélkül. Nem bontottam ki adatot.
- ls docs/specs | grep -i 'backup\|mentes': biztonsagi-mentes.md. Ez a Picasa Back Up Pictures termékfunkcióról szól, nem a geotag ini-írásáról.
- Geotag tárgyú lapok: picasa-helyek-panel.md, továbbá a menü- és gyorsbillentyű-specifikáció. Az összefoglalók helyett a hivatkozott részek és források kerültek ellenőrzésre.
