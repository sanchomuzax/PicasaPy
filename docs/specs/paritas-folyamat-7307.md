# Az asztali háttér és a képernyővédő beállításának teljes folyamata az eredeti Picasával összevetve: belépési pontok, hatás

Issue: #7307. Eredeti: Picasa 3.9.141.259, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.

Ez a lap a háttérkép és screensaver útvonalakat követi a menütől a fájl- vagy rendszerhatásig. A bináris kizárólag statikusan volt vizsgálva. A `job-*` jelű korábbi felvételek közül a `ki03/kepernyo__11.png` a háttérkép megerősítő ablakát rögzíti; maga a művelet nem lett megerősítve. A mérési archívumban nincs képernyővédő-beállító ablakot vagy tényleges háttérbeállítást mutató felvétel.

## Következtetés

Az eredeti Picasa a Létrehozás menüből állít be háttérképet és vesz fel képeket a külön telepített Google Photos képernyővédőbe; a képernyővédő konfigurálása a Windows `desk.cpl` útjára irányít. A PicasaPy háttérkép-útja általában ugyanazt a BMP-formátumot és középre igazított Windows-hatást adja, de egyéni kollázs-kimeneti mappa esetén másik könyvtárba ír, Windows API-hívásának sorrendje és jelzői is eltérnek. A képernyővédő PicasaPy-változata dokumentált Linuxos adaptáció, nem az eredeti külső Windows program másolata.

## Bizonyítottsági fok

**Feltételes.** A menük, a kezelőhívások, a BMP-írás, a Windows rendszerhívás és a PicasaPy jelenlegi forrásútjai címmel követhetők. A korábbi futtatott mérés csak a háttérkép megerősítő ablakát ellenőrzi. Az eredeti menüelemek pontos engedélyezési feltétele, a teljes screensaver felületi út, az OS-hatás, a hálózati és írásvédett hibák, valamint a visszavonás futásidejű viselkedése nincs mérve.

## Eredeti folyamat

### Belépési pontok és feltételek

| Belépési pont | Eredeti bináris út | Feltétel és bizonyíték |
|---|---|---|
| Létrehozás > Set as Desktop... | A menüépítő `0x00559150` bejegyzése; a `0x005cb990` diszpécser a `0x9cd2` parancsot a `0x0057ae90` megerősítőhöz küldi. | A menühely és parancs azonosított. A menüpont eredeti engedélyezési feltétele és kijelölés nélküli állapota NINCS MEG. |
| Létrehozás > Add to Screensaver... | A menüépítő `0x00559150`; a `0x005cb990` diszpécser a `0x9d5c` parancsot a `0x00531900` kezelőhöz küldi. | Album kiválasztásakor a kezelő az album képeinek hozzáadására kér megerősítést. Az eredeti engedélyezési feltétel más nézetekben NINCS MEG. |
| Eszközök > Configure Screensaver... | A `0x00559150` menüépítő és a `0x005cb990` diszpécser a `0x9dc9` parancsot a `0x00531ac0` kezelőhöz küldi. | A kezelő a telepített külső Google Photos képernyővédő rendszerbeállító útját indítja. Az eredeti menüelem pontos állapotkapuja NINCS MEG. |
| Műveleti nevek és egyéb felületek | A `setasdesktop` és `addtoscreensaver` actionnevek a `0x005ddb80` diszpécseren át a fenti kezelőkhöz vezetnek. Az `action/screensaver` a `0x005d9cc0`-hoz kötött. A `collagepanel/makedesktop` erőforrás és a kollázs-befejező `0x0088a020` a `0x0057aa10` háttérkép-írót is eléri. | A belső út bizonyítja a műveleti neveket, de az `action/screensaver` és `setasdesktop` pontos képernyőbeli gazdája, feltétele és láthatósága NINCS MEG. A kollázs Desktop Background út külön belépési pont. |
| Gyorsbillentyű | NINCS MEG. A helyi telepítési példányban nincs külön shortcut vagy keymap erőforrásként azonosítva. | Negatív állításhoz teljes billentyűregisztrációs út vagy futtatott menü- és billentyűmérés szükséges. |

### Párbeszédek és megjegyzett állapot

| Művelet | Eredeti ablak vagy kérdés | Alapérték és megjegyzett állapot |
|---|---|---|
| Háttérkép beállítása | A `ki03/kepernyo__11.png` képen `Confirm` ablak kérdezi: `This will replace your current desktop background with the current image.  Are you sure you want to proceed?`; gombok: `Set Desktop` és `No`. A futtatott felvétel szerint a PicasaPy ablakának szövege és gombjai egyeznek. | Külön háttérkép-beállító mező nincs kimutatva. A kérdésre adott válasz vagy a korábbi háttér megjegyzésének állapota NINCS MEG. |
| Képek hozzáadása a képernyővédőhöz | A kezelő az album összes képére rákérdez: `Are you sure you want to add all of the selected album's images?`. A `0x00531900` elfogadás után a `0x00531a20` listázó ágát hívja. A `0x00741840` szövegtáblában `Adding to screensaver` felirat van. | A hozzáadott képek pontos kiválasztási szabálya, a mezők, a megjegyzett állapot és a progress-felület helye NINCS MEG. |
| Képernyővédő konfigurálása | A `0x00531ac0` a `HKLM\Software\Google\Google Photos Screensaver\AppPath` értéket olvassa, majd `rundll32.exe desk.cpl,InstallScreenSaver %s` folyamatot indít. Hiányzó `AppPath` esetén `The screensaver hasn't been installed.` hibát ad. | A külső program nincs a kutatási példányban. A mezői, alapértékei, megjegyzett állapota, előnézete és a Windows képernyővédő tényleges kimenete NINCS MEG. |

### Hatás, megszakítás és hibák

| Terület | Eredeti Picasa bizonyítéka | Ami nem dőlt el |
|---|---|---|
| Háttérkép fájl | A `0x0057aa10` BMP-t ír `Picasa\Backgrounds\picasabackground.bmp` néven, a Picasa `Backgrounds` mappájába. Nem az eredeti fotó útvonalát állítja be háttérként. | A fájlírás hibájának felületi jelzése, részleges fájl megmaradása, hálózati és csak olvasható cél viselkedése NINCS MEG. |
| Háttérkép OS-beállítás | A `0x0057aca1` `SystemParametersInfoW(0x14, 0, <BMP út>, 0)` hívást végzi. Utána a `HKCU\Control Panel\Desktop` ágban a `Wallpaper` értéket a BMP útjára, a `WallpaperStyle` értéket `0`-ra, a `TileWallpaper` értéket `0`-ra állítja. A `0x14` művelet a `SPI_SETDESKWALLPAPER`; a két nulla középre igazított, nem csempézett és nem nyújtott hátteret jelent. | A rendszerhívás és a registry író visszatérését a vizsgált kezelő nem ellenőrzi. Hogy a Windows ténylegesen elfogadta-e a módosítást, futásmérés nélkül NINCS MEG. |
| Screensaver-adatok | A `0x00531a20` a `]screensaver` tokent és a `#db3\saverlist.txt` fájlt használja. A fájllistázó `0x004755f0` `%s\n` formátummal ír. A profilban talált `saverlist.txt` üres, ezért a sorok tényleges tartalma ebből nem állapítható meg. Egy másik állapotfigyelő a `]screensaver` tokent `screensaver` INI-kulcshoz köti, de a menüút és a tényleges `.picasa.ini` írás összekapcsolása nincs végig igazolva. | A pontos `.picasa.ini` változás, indexfrissítés, bal hasáb, rács, kijelölés és háttérmunka hatása NINCS MEG. A fájllista nem bizonyít indexírást. |
| Megszakítás és visszavonás | A háttérkép művelet előtt látható megerősítés van; a `No` válasz a `0x0057aa10` meghívása előtt visszatér. Az albumos screensaver megerősítés elutasítása a hozzáadási ág előtt visszatér. | A háttérkép futás közbeni megszakítása, a konfiguráló Windows párbeszéd megszakítása, a már beállított háttér visszaállítása és a screensaver-tagság visszavonása NINCS MEG. |
| Háttérmunka és állapotsor | A háttérkép kezelő ütemezett feladatra teszi a munkát, ha az ütemező elfogadja, egyébként közvetlenül futtatja a `0x0057aa10` ágat. A screensaver szövegtáblában van `Adding to screensaver`. | A pontos folyamatjelző, állapotsor, várakozási állapot és a kezelő megszakíthatósága NINCS MEG. |

## PicasaPy folyamat

### Belépési pontok és feltételek

| Belépési pont | Jelenlegi út és kapu |
|---|---|
| Létrehozás > Set as Desktop... | `PicasaCreateMenu.qml:17-21`; aktív, ha `libraryPhotoActionsEnabled`, azaz a néző nincs nyitva és van kijelölt sor: `MainMenuBar.qml:148-149`. A kijelölés első sorát adja át a megerősítő párbeszédnek: `MainMenuBar.qml:259-266`. |
| Létrehozás > Add to Screensaver... | `PicasaCreateMenu.qml:38-42`; ugyanaz a nem üres kijelölésű kapu. Album-nézetben az összes kiválasztott albumképre megerősítést kér `MainWindowCommands.qml:672-690`, majd a `MainLibrarySelectionState.qml:167-179` helyi képernyővédő-listába adja a képeket. |
| Képernyővédő konfigurálása | `PicasaToolsMenu.qml:64-68`; szerkesztőnézetben letiltott. A `MainMenuBar.qml:219-223` a saját `ScreensaverDialog` ablakot nyitja. |
| További hozzáadási pontok | Fotó helyi menü: `MainPhotoContextMenu.qml:160-162`; fotómenü: `PhotoContextMenu.qml:207-221`; néző helyi menü: `ViewerContextMenu.qml:169-177`; Képtálca hozzáadás menüje: `TrayScratchPanel.qml:542-572`, bekötése `MainTrayBar.qml:77`. Ezek a helyi menük közvetlenül hozzáadnak, nem kérik az albumos Create menü megerősítését. |
| Kollázs háttérként | A Kollázs panel `Desktop Background` gombja `CollagePanel.qml:203-229` a mentési út háttérkép ágát indítja; a kimenet létrejötte után állít hátteret `collage_save.py:295-329`. |
| Gyorsbillentyű | A PicasaPy `MainKeyboardShortcuts.qml` regisztrált csoportjaiban nincs háttérkép vagy screensaver parancs. Ez a forrásleolvasás a PicasaPy-ról szól; az eredeti gyorsbillentyű kérdését nem dönti el. |

### Párbeszéd, beállítások és tárolás

- A háttérkép megerősítés címe `Confirm`, szövege az eredeti felvétellel egyező, gombjai `Set Desktop` és `No`; külön Cancel és megjegyzésjelölő nincs. Elutasításkor a függő sor törlődik, elfogadáskor a `setPhotoAsDesktopBackground` fut (`MainDialogs.qml:427-460`).
- A helyi, modális `Configure Screensaver...` ablak forráslistát, öt effektet, diaidőt, képaláírás-kapcsolót és támogatott környezetben tétlenségi indítást mutat (`ScreensaverDialog.qml:8-17, 102-145, 150-265`). Első használatkor a figyelt gyökerekből származó mappák vannak kijelölve; ha ezek egyike sem szerepel a katalógusban, minden nem üres mappa kijelölt (`screensaver_controller.py:105-117`). Az effekt és értékek a vezérlőből betöltődnek megnyitáskor; alap diaidő 3 másodperc, képaláírás bekapcsolva, tétlenségi idő 10 perc, tartományok 1-30 másodperc és 1-120 perc (`ScreensaverDialog.qml:22-60, 150-265`).
- A képernyővédő beállításai a QSettings kulcsaiba kerülnek (`screensaver_controller.py:41-46`). Az effekt-, diaidő- és feliratváltozás azonnal mentődik (`:253-286`); a hozzáadott fotóútvonalak a `screensaver/photoPaths` kulcsba kerülnek, és a `photos:selected` forrás engedélyeződik (`:288-305`). A forráskód útján nincs `.picasa.ini` írás vagy SQLite-séma módosítás.
- A `ScreensaverDialog` bezárása nem állítja vissza az előzőleg módosított értékeket: azok a vezérlőben azonnal mentődnek. Az előnézet bezárja a konfigurációs ablakot és elindítja a helyi vetítést (`ScreensaverDialog.qml:256-265`).

### Háttérfájl, OS-hatás és visszajelzés

- A `setPhotoAsDesktopBackground` olvassa a kijelölt fotót, a szerkesztett rasztert BMP-be írja, majd meghívja az OS-beállítót (`photo_ops_album_actions_mixin.py:13-54`, `wallpaper.py:147-172,316-343`). Ez a metódus egyetlen szinkron hívásban végzi a lépéseket, nincs hozzá háttérmunkás.
- A háttér könyvtára a beállított kollázs-kimenet mappájának szomszédja; alapbeállításban `<Képek>/Picasa/Backgrounds`, de egyéni kollázs-célmappával együtt elmozdul (`wallpaper.py:120-139`). A fájlnév `picasabackground.bmp` (`:142-172`).
- Windows alatt a PicasaPy előbb `WallpaperStyle=0` és `TileWallpaper=0` registry-értékeket ír, majd `SystemParametersInfoW` hívást indít `0x03` jelzőkkel (`wallpaper.py:175-219`). Sikertelen API-hívás vagy kivétel esetén `None` tér vissza és hibát jelez. Siker esetén a hibasáv megnevezi a beállító eszközt; ha a BMP elkészült, de az OS-hívás nem sikerült, a hibasáv megmutatja a BMP útját (`MainErrorBanner.qml:162-175`).
- Nem Windows alatt a vezérlő a felismert asztali környezet eszközével állít hátteret; a támogatott Linux ágak a `wallpaper.py:316-380` alatt vannak. A hálózati vagy csak olvasható mappák élő viselkedése ezen a feladatkörön nem lett mérve.

## Összevetés

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x0057ae90` megerősítés; `0x0057aa10` BMP-írás. Eredeti cél: Picasa `Backgrounds` mappa, `picasabackground.bmp`. | `photo_ops_album_actions_mixin.py:39-45`; a célmappa a kollázs-kimenet szomszédja: `wallpaper.py:120-139`. | **Eltérés egyéni célmappa esetén.** Alapbeállításnál a cél megfelel; az egyéni `collage/outputDir` viszont eltéríti az eredeti Picasa-helyről. Fejlesztői javaslat: döntse el és dokumentálja, hogy a menüparancs az eredeti állandó Picasa `Backgrounds` helyet használja-e, függetlenül a kollázs célmappájától. |
| `0x0057aca1`: `SystemParametersInfoW(0x14, 0, path, 0)`, majd `Wallpaper`, `WallpaperStyle=0`, `TileWallpaper=0` registry-írás. A két API/registry út hibáját a kezelő nem ellenőrzi. | `wallpaper.py:200-221`: előbb a két stílusérték, majd API hívás `0x03` jelzőkkel; az API hibáját és kivételét jelzi. | **Windows-végrehajtási eltérés.** A művelet eredménye és a tartósítás sorrendje eltér. Fejlesztői javaslat: a Windows út szándékos eltérését rögzítse, vagy hozzon létre külön eredeti-kompatibilis sorrendet; a jelenlegi hiba-visszajelzést tartsa meg explicit termékdöntésként. |
| `0x00531900` -> `0x00531a20`: screensaver tagság és `#db3\saverlist.txt`; `0x00531ac0`: külső `desk.cpl` telepítő/beállító út. | QSettings-alapú helyi képernyővédő: `screensaver_controller.py:41-46, 288-305`; saját beállító: `ScreensaverDialog.qml:22-60, 150-265`. | **Szándékos platformadaptáció, #4259.** Nincs paritás-helyreállító jegy, amíg a Linuxos helyi képernyővédő a termékdöntés. Windows-paritás igény esetén külön fejlesztői jegy kell a külső Windows út kezelésére és a régi profilállapot mérésére. |
| `0x00531a20` listázó és `]screensaver` token. A token `screensaver` INI-kulcshoz kapcsolódik egy külön megfigyelő útban, de a menüút tényleges INI-írása nincs igazolva. | `screensaver_controller.py:288-305`: kiválasztott képek QSettings-be kerülnek. | **Tárolási modell eltér.** Régi Picasa profil átvétel csak akkor tervezhető, ha nem üres `saverlist.txt` mintát és a tényleges INI-írást megmérjük. Ez jelenleg kutatási nyitott pont, nem kész implementációs követelmény. |
| `0x0057ae90` megerősítési ág és `0x0057aa10` művelet. A mérés a promptot igazolja, de az eredmény lefutását nem. | `MainDialogs.qml:427-460`; írási hibák és OS-hibák látható visszajelzést kapnak (`photo_ops_album_actions_mixin.py:46-53`, `MainErrorBanner.qml:162-175`). | **Kimeneti összevetés NINCS MEG.** A felvétel nem zárta le a megerősítést, ezért a sikeres állapot, állapotsor, fájl és rendszerbeállítás futásidejű paritása nyitott. |
| `0x00531900` album-megerősítés; elutasítás előtt nincs hozzáadás. További megszakítás és visszavonás viselkedése NINCS MEG. | Albumos Create menü a teljes albumra kérdez (`MainWindowCommands.qml:672-690`); fotó- és tálca-helyi menük közvetlenül hozzáadnak (`MainPhotoContextMenu.qml:160-162`, `PhotoContextMenu.qml:207-221`, `ViewerContextMenu.qml:174-177`, `TrayScratchPanel.qml:563-566`). | **Belépési pontok részben eltérnek.** Az eredeti helyi menü/action gazdáját és megszakítás utáni állapotát célzottan kell felmérni, mielőtt a PicasaPy megerősítési viselkedését egységesítenénk. |
| Eredeti gyorsbillentyű NINCS MEG; a menüazonosítók és handlerláncok önmagukban nem zárják ki. | A `MainKeyboardShortcuts.qml` regisztrált shortcut listáiban nincs háttérkép- és képernyővédő parancs. | **Nincs állítható eltérés.** Az eredeti teljes billentyűregisztrációs út vagy futásmérés szükséges. |

### Javasolt jegytörzsek az eltérésekhez és nyitott kérdésekhez

#### Javaslat 1: A háttérkép célmappája és Windows-beállítási sorrend

**Eredeti: 0x0057aa10, 0x0057aca1.**

Az eredeti Picasa a háttér BMP-t a saját `Picasa\Backgrounds\picasabackground.bmp` helyére írja, majd `SystemParametersInfoW(0x14, 0, path, 0)` hívást végez, és utána állítja a `Wallpaper`, `WallpaperStyle=0`, `TileWallpaper=0` registry-értékeket. A PicasaPy jelenleg a kollázs célmappájából vezeti le a háttérkönyvtárat; Windows alatt a stílusértékeket előbb írja, az API-hívásnak `0x03` jelzőket ad, és hibát jelez.

**Teendő:** a közös menü- és kollázs-háttérkép út használja az eredeti Picasa `Backgrounds` projektmappát a `collage/outputDir` értékétől függetlenül. Windows alatt állítsd be a hátteret `SystemParametersInfoW(0x14, 0, path, 0)` hívással, majd írd a `Wallpaper`, `WallpaperStyle=0`, `TileWallpaper=0` értékeket. A PicasaPy látható hiba-visszajelzése maradjon meg, mert az eredeti hibakimenet nincs futásban igazolva.

**Kész, ha:** egyéni kollázs-célmappa mellett is az eredeti `Backgrounds` célhelyet használja a menü- és kollázs-háttérkép út; Windows alatt az API-hívás nulla jelzővel megelőzi a három registry-írást; az írási vagy OS-hiba továbbra is látható; a Linuxos asztali környezeti ág nem változik.

#### Javaslat 2: az eredeti képernyővédő-belépések gazdája és kapuja

**Eredeti: 0x005d9cc0, 0x0059bbc0.**

Az eredeti bináris az `action/screensaver` műveletet a `0x005d9cc0` címhez köti, a screensaver konfigurálását pedig a `0x0059bbc0` indirekt útja is eléri. A menüút ismert, de a további felületi gazda, láthatósági feltétel és a képernyőn megjelenő pontos belépési pont nincs azonosítva.

**Teendő:** a fejlesztési feladat előtt célzott Ghidra-körrel azonosítsd a művelet gazdáját és kapuját. Csak ezután dönts arról, szükséges-e további PicasaPy belépési pont vagy engedélyezési kapu.

**Kész, ha:** eredeti felület, állapotfeltétel és parancs a bináris címekhez van rendelve; PicasaPy megfelelő belépési pontját fájl:sor hivatkozással összevetették; puszta felirat-egyezést működési egyezésnek nem neveztek.

#### Javaslat 3: Windows képernyővédő konfigurációs út

**Eredeti: 0x00531ac0.**

Az eredeti `Configure Screensaver...` a Google Photos Screensaver `AppPath` értékéből indítja a Windows `desk.cpl` telepítő/beállító útját, telepítés nélkül pedig hibát jelez. A PicasaPy jelenleg minden platformon a saját `ScreensaverDialog` ablakát nyitja.

**Teendő:** ha Windows paritás is termékkövetelmény, Windowson legyen külön OS-integráció az eredeti külső képernyővédő útjához. A nem Windowsos saját beállító maradjon elérhető. Az eredeti külső program beállításait, alapértékeit és a régi Picasa profillistáját ne migrálja becslésből.

**Kész, ha:** Windows alatt telepített külső program esetén a rendszerbeállító út nyílik meg, hiányzó telepítésnél látható hiba jelenik meg; nem Windows rendszeren a helyi párbeszéd továbbra is működik; a régi Picasa lista átvétele külön, mért formátumspecifikációra vár.

#### Javaslat 4: régi képernyővédő-lista átvételének mérése és specifikálása

**Eredeti: 0x00531a20.**

Az eredeti képernyővédő-halmaz a `#db3\saverlist.txt` útvonalat és a `]screensaver` tokent használja. A jelenlegi PicasaPy a hozzáadott fotóútvonalakat a QSettings `screensaver/photoPaths` kulcsába menti. A vizsgált eredeti profil `saverlist.txt` fájlja üres, ezért a rekordok alakja és a `screensaver` INI-kulcs tényleges írási kapcsolata nem állapítható meg.

**Teendő:** mielőtt profilimport készül, szerezz egy nem üres `saverlist.txt` mintát eredeti Picasa 3.9 műveletből, és igazold a `.picasa.ini` írást művelet előtti és utáni profilméréssel. Ezek alapján írj import-leképezést a PicasaPy QSettings célkulcsaira. Üres vagy hiányzó lista esetén ne következtess tagságra.

**Kész, ha:** a specifikáció rögzíti a mért listaformátumot, az INI-kulcs és menüút kapcsolatát, valamint a profil előtti és utáni diffet; az import tesztelt nem üres, üres, hiányzó és hibás mintán; a régi fájl olvasása nem módosítja az eredeti profilt.

## Két független út és cáfoló kísérlet

**A út:** a bináris menüépítő `0x00559150` és parancs-diszpécser `0x005cb990` megadja a Create és Tools menüpontokat, majd a célkezelőket. A célkezelők utasításszintű követése megadja a háttérkép fájl- és OS-hatását, illetve a screensaver listázó és telepítő hívását.

**B út:** külön action string-xrefek a `setasdesktop`, `addtoscreensaver` és `action/screensaver` neveket a műveleti diszpécserekhez kötik; a `collagepanel/makedesktop` erőforrás és a `0x0088a020` befejező út külön megerősíti, hogy a kollázs háttérbeállítása ugyanazt a `0x0057aa10` írót éri el. A háttérkép fájlnév, registry-értékek és `SystemParametersInfoW` importja az adat- és importált karakterláncokból külön ellenőrizhető. Az út megerősíti a kezelő szerepét, de nem adja meg az action-felületek gazdáját vagy a futásidejű OS-sikert.

**Cáfoló kísérlet:** megpróbáltam cáfolni a háttérkép célmappa eltérését azzal, hogy összevetettem az alapértelmezett konfigurációt. Abban a helyzetben a jelenlegi kód `<Képek>/Picasa/Backgrounds` helyet eredményez, tehát az általános „mindig másik helyre ír” állítás megdől. A szűkebb eltérés viszont fennmarad: a PicasaPy a kollázs-kimenet szomszédjához köti a háttérkönyvtárat, így egyéni `collage/outputDir` mellett elmozdul; az eredeti út a Picasa `Backgrounds` mappa-erőforrását használja. Ezt a korlátozott állítást a bináris erőforrásút és a PicasaPy `backgrounds_dir` forráskódja egyaránt alátámasztja. Tényleges Windows futásmérést nem végeztem.

## A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Belépési pontok, állapotfeltételek | ⛔ Részben. A három menüparancs és a PicasaPy belépési pontjai megvannak; az eredeti action-gazda, gyorsbillentyű és eredeti engedélyezési kapuk nyitottak. | `0x00559150`, `0x005cb990`, `0x005ddb80`, `0x005d9cc0`; PicasaPy fájl:sor hivatkozások a belépési pont táblában. |
| Ablakok, mezők, alapértékek, megjegyzett állapot és kérdések | ⛔ Részben. A háttérkép prompt egyezését egy korábbi felvétel mutatja; az eredeti külső screensaver ablak nem áll rendelkezésre. | Mérés: `ki03/kepernyo__11.png`; bináris `0x00531900`, `0x00531ac0`; `ScreensaverDialog.qml:22-60, 150-265`. |
| Fájlok, `.picasa.ini`, index, bal hasáb, rács, kijelölés, háttérmunka és állapotsor | ⛔ Részben. Háttérkép fájl és rendszerút statikusan le van írva; a screensaver lista/token út ismert; `.picasa.ini` tényleges írása, index és felületi frissítés nincs végig igazolva. | Bináris `0x0057aa10`, `0x00531a20`; a mérési profilban `saverlist.txt` 0 bájt; PicasaPy forrásutak a fenti táblákban. |
| Hibák, megszakítás, hálózati vagy írásvédett hely, visszavonás | ⛔ Nyitott. Az eredeti írók hibakezelése és az OS-hatás nincs élő mérésen ellenőrizve. | NINCS MEG: Windows futásmérés tiszta profilon, sikeres és hibás célkönyvtárral, megszakítási próbával és rendszerértékek előtte/utána mérésével. |
| Eltérésenként fejlesztői jegytörzs | ✅ Az igazolt eltérésekhez és a megvalósítást megelőző nyitott kutatáshoz javasolt törzs készült; a Linuxos platformadaptáció szándékosként szerepel. | A fenti összevető táblázat és a javasolt törzsek. |

## Nyitott

- Ghidra-kör kell: 0x005D9CC0 - melyik CThumbUI-felület és állapotkapu hozza létre az action/screensaver műveletet, és az `action/setasdesktop` hol látható? [blokkoló]
- Ghidra-kör kell: 0x0059BBC0 - melyik felületi hit `zone` hívja a Configure Screensaver utat és mikor látható? [blokkoló]
- Mérés szükséges: eredeti Picasa 3.9-ben háttérkép megerősítés elfogadása, BMP- és registry-változás előtte/utána, háttérmunka és állapotsor; sikeres, csak olvasható és hálózati célmappával.
- Mérés szükséges: eredeti képernyővédő AppPath értéke és a hozzá tartozó program beszerzése; tiszta Windows-profilon a mezők, alapértékek, megjegyzett állapot, előnézet és konfiguráló ablak felvétele.
- Nyitott: a screensaver hozzáadás utáni `.picasa.ini` tényleges írása, index vagy felületi frissítés, nem üres `saverlist.txt` tartalom, művelet-visszavonás és megszakítás.
- Nyitott: eredeti háttérkép gyorsbillentyű és a három menüelem pontos engedélyezési feltétele.

## Új kutatási jegyjavaslatok

**A Google Photos Screensaver eredeti Windows-beállításai és profilszinkronja.** Kérdés: mely mezőket és alapértékeket adja a külön telepített program, mit jegyez meg, mit vetít előnézetben, és hogyan kapcsolódik a `saverlist.txt` a `.picasa.ini` `screensaver` kulcsához? Hol keresd: a `0x00531ac0` által olvasott `AppPath`, az általa mutatott külső program, a `0x00531a20` listázó és egy legalább egy képet tartalmazó eredeti Picasa 3.9 profil művelet előtti/utáni mérése.

## Módosított fájlok

- `docs/specs/paritas-folyamat-7307.md`: az eredeti és a jelenlegi teljes háttérkép- és képernyővédő út összevetése, bizonyítékok, eltérések, cáfoló kísérlet és nyitott kérdések.
- `docs/specs/00-index.md`: új paritáslapra mutató indexbejegyzés.
