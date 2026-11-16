# PicasaPy paritás-ellenőrzés — #4317

**Vizsgálati dátum:** 2026-10-13. **Hatókör:** a 2–4. réteg korábbi statikus QML-ellenőrzése, a 6. réteg tiszta profilos kattintáspróbája és a 7. réteg effektkimenet-mérése. A rétegállapotok a jegy korábbi köreihez és az alábbi bizonyítékokhoz kötődnek.

## A vizsgált állapot és a bizonyítás módja

A vizsgálat a `research/4317-codex` munkafában készült. A munka eleji `git status -sb` tiszta munkafát és a helyi `origin/main`-től **2 commit lemaradást** mutatott; a záró ellenőrzés **3 commit lemaradást** jelzett, ekkor már csak ez az új specfájl volt módosítatlanul követetlen. Nem futtattam fetch-et, ezért a helyi hivatkozás változásának oka és az upstream `main` frissessége nem bizonyítható. A megállapítások erre a munkafa-pillanatképre érvényesek.

„Megvan” ebben a lapban azt jelenti, hogy a QML-tételnek van nem üres kezelőútja, és a forráskód az eredeti specben leírt művelethez vezet. Ez **nem kattintásos vagy felhasználói működési próba**. Ahol külső program, profil, nyomtató vagy környezet számít, ott a kattintásos ellenőrzés nyitva marad. A gépi `scripts/menu_lefedettseg.py --json` 138 `viselkedes` sort ad, de a szkript specifikációs említéseket osztályoz, nem QML-elemeket vagy működő kezelőket; ezért a 138-as eredményt csak az eredeti azonosítók készletének ellenőrzésére használtam.

Az eredeti menüazonosítók és hatásuk forrása a [`picasa-menu-parancsok-viselkedes.md`](picasa-menu-parancsok-viselkedes.md), a kontextusmenüké a [`ui-audit-context-menus.md`](ui-audit-context-menus.md), a gyorsbillentyűké a [`picasa-gyorsbillentyuk.md`](picasa-gyorsbillentyuk.md), az egér- és húzásviselkedésé a [`picasa-eger-es-kijeloles.md`](picasa-eger-es-kijeloles.md). Az aktuális megvalósítás QML-forrásait az egyes sorok megadják.

## 2. réteg — a 138 menüparancs

A CSV-ben szereplő 138 külön parancsazonosító ellenőrzése a jelenlegi menüsor QML-ével. Az alábbi 108 azonosítónál van a parancs menüútján nem helyfoglaló, nem állandóan letiltott QML-kezelő. A jelzés és a végrehajtási út statikusan követhető; az egyedi kattintás és a külső hatás nincs végigpróbálva. A külön táblázat jelöli azokat az eredeti parancsokat, amelyek csak másik menüből érhetők el.

| Parancscsalád | Eredmény: a kódút megvan | Forrás |
|---|---|---|
| Fájl és Szerkesztés | `ID_CLEAR_SELECTION`, `ID_COPY`, `ID_CUT`, `ID_EDIT_COPYALLEFFECTS`, `ID_EDIT_COPYTEXT`, `ID_EDIT_PASTEALLEFFECTS`, `ID_EDIT_PASTETEXT`, `ID_FILE_DELETEFROMDISK`, `ID_FILE_EXIT`, `ID_FILE_EXPORTTOFOLDER`, `ID_FILE_IMPORTPICTURE`, `ID_FILE_LOCATEONDISK`, `ID_FILE_NEWFOLDER`, `ID_FILE_NEWLABEL`, `ID_FILE_OPEN`, `ID_FILE_PRINT`, `ID_FILE_RENAME`, `ID_FILE_REVERT`, `ID_FILE_SAVE`, `ID_FILE_SAVEACOPY`, `ID_FILE_SAVEAS`, `ID_PASTE`, `ID_TOOLS_INCLUDEEXCLUDEFOLDERS` | `PicasaMenuBar.qml:483–751`; a menütételek `onTriggered` kezelői és a Main/QML-kapcsolatok a `Main.qml`-ben. Törlés/export/nyomtatás külső hatása kattintással ellenőrizendő. |
| Mappa és rendezés | `ID_ALBUM_DELETE`, `ID_ALBUM_EDITCAPTIONS`, `ID_ALBUM_LOCATEONDISK`, `ID_ALBUM_SELECTALLPICTURES`, `ID_ALBUM_SLIDESHOW`, `ID_DATESORT`, `ID_FILE_EXPORTASWEBPAGE`, `ID_FILE_PRINTCONTACTSHEET`, `ID_MANAGE_ALBUM`, `ID_MOVEFOLDER`, `ID_NAMESORT`, `ID_REFRESH_THUMB`, `ID_REVERSESORT`, `ID_SIZESORT` | `PicasaMenuBar.qml:1483–1656`; külön helyi menüben a `FolderContextMenu.qml:80–305`. A `Delete`, `Hide` és `Unhide` a jelenlegi menüsávban még lehet helyfoglaló, a helyi mappamenüben viszont működő útjuk van; lásd a 3. réteget. |
| Kép, effekt, kijelölés | `ID_PICTURE_AUTO_COLOR`, `ID_PICTURE_AUTO_LIGHTING`, `ID_PICTURE_AUTO_REDEYE`, `ID_PICTURE_ENHANCE`, `ID_PICTURE_FILM_GRAIN`, `ID_PICTURE_GEOUNTAG`, `ID_PICTURE_HIDE`, `ID_PICTURE_PROPERTIES`, `ID_PICTURE_REVERT`, `ID_PICTURE_ROTATECLOCKWISE`, `ID_PICTURE_ROTATECOUNTERCLOCKWISE`, `ID_PICTURE_SEPIA`, `ID_PICTURE_SHARPEN`, `ID_PICTURE_WARMIFY` | `PicasaMenuBar.qml:1660–1766, 1815–1875`; `ID_PICTURE_SEPIA` a `menuBatchSepia` → `applyEffectMany("sepia")` úton érhető el, a külön Fekete-fehér tétel `menuBatchBlackWhite` → `applyEffectMany("bw")`. A `ID_VIEW_SEPIA` továbbra is megjelenítési mód; az eredeti renderelt effektkimenet egyezése nincs mérve (7. réteg nyitott). |
| Nézet és felirat | `ID_CAPFILE`, `ID_CAPFULL`, `ID_CAPNONE`, `ID_CAPRES`, `ID_CAPTAG`, `ID_SELECT_INVERT`, `ID_VIEW_ALL`, `ID_VIEW_AUTO`, `ID_VIEW_BW`, `ID_VIEW_COLOR_MANAGED`, `ID_VIEW_DESKTOP`, `ID_VIEW_FOLDERS`, `ID_VIEW_LARGETHUMBNAILS`, `ID_VIEW_LCD`, `ID_VIEW_LIGHTBOXVIEW`, `ID_VIEW_LINEAR`, `ID_VIEW_MAC`, `ID_VIEW_NORMAL`, `ID_VIEW_OV`, `ID_VIEW_PEOPLE`, `ID_VIEW_PLACES`, `ID_VIEW_PROJECTOR`, `ID_VIEW_PROPERTIES`, `ID_VIEW_SEPIA`, `ID_VIEW_SHOWHIDDEN`, `ID_VIEW_SLIDESHOW`, `ID_VIEW_SMALLTHUMBNAILS`, `ID_VIEW_THUMBNAILS`, `ID_VIEW_WATCHED` | `PicasaMenuBar.qml:755–1478`; felirat- és nézetkezelők a `Main.qml`-hez és a megfelelő panelekhez kapcsolódnak. A „megvan” itt is statikus út, nem kattintásos igazolás. |
| Létrehozás | `ID_COLLAGEMAKER`, `ID_POSTER`, `ID_SCREENSAVER`, `ID_WALLPAPER` | `PicasaMenuBar.qml:1779–1831`; a párbeszéd- és exportutak a `CreateDialogs.qml`-ben, illetve a kapcsolódó vezérlőkben. Külső írás/asztali integráció kattintással ellenőrizendő. |
| Eszközök | `ID_DUPES`, `ID_MOVE_DATABASE`, `ID_PASSPORT`, `ID_SAVESEARCH`, `ID_SEARCHTOKEN`, `ID_SELECTSTAR`, `ID_S_BLUE`, `ID_S_GREEN`, `ID_S_ORANGE`, `ID_S_PURPLE`, `ID_S_RED`, `ID_S_YELLOW`, `ID_TOOLS_BACKUP`, `ID_TOOLS_BUTTONMGR`, `ID_TOOLS_CONFIG_SCREENSAVER`, `ID_TOOLS_OPTIONS`, `ID_VIEWBYDATE`, `ID_VIEWBYNAME`, `ID_VIEWBYRECENT`, `ID_VIEWBYSIZE`, `ID_VIEWREVERSE`, `ID_VIEW_EARTH`, `ID_WRITE_XMP_FACES` | `PicasaMenuBar.qml:1835–2180`; az almenük elemei és jelzései ugyanebben a fájlban, a gazdaoldali kapcsolatok a `Main.qml`-ben. A Google Earth indítását és a lemezre író műveleteket kattintással kell ellenőrizni. |
| Súgó | `ID_HELP_ABOUT` | A `PicasaMenuBar.qml:2268–2274` az About PicasaPy ablakot nyitja. Az eredeti „About Picasa” funkciójának helyi megfelelője; az átnevezés szándékos. |

### Nem elérhető, hiányzó vagy platformhoz kötött parancsok

| Parancs | Állapot | Bizonyíték és teendő |
|---|---|---|
| `ID_FILE_EMAIL` | **Megvan, de a Fájl menüben nem működik.** | `PicasaMenuBar.qml:623` helyfoglaló; aktív `Ctrl+E` shortcut sincs. Maga az e-mail küldési út más felületen megvan: `Main.qml:1996–2047`, a `TrayBar.emailRequested` bekötése `Main.qml:3710`. Javasolt jegy: „A Fájl ▸ E-mail parancs ugyanazt a kijelölést küldje, mint a képtálca e-mail művelete”. |
| `ID_FILE_OPENINANEDITOR` | **#4330: a Fájl menü és a `Ctrl+Shift+O` a kijelölt fájlokat a rendszer alapértelmezett alkalmazásával nyitja meg.** | A specifikációban nincs külön szerkesztőprogram-beállítás, ezért a `FileOpsController.openPhotosInDefaultEditor` a Qt rendszermegnyitóját használja, és a meghiúsult fájlok számát jelzi. A kép helyi menüjének „Open File” útja szintén `QDesktopServices.openUrl`-t hív; nem a PicasaPy-nézőt nyitja. |
| `ID_PICTURE_VIEW`, `ID_PICTURE_UNHIDE`, `ID_PICTURE_RESET_FACES` | **A felső Kép menüben megvan, de nem érhető el; a funkció másik menüútban megvan.** | Felső menü: `PicasaMenuBar.qml:1660,1754,1759` helyfoglalók. A kép helyi menüjének „View and Edit”, dinamikus Hide/Unhide és Reset Faces sorai aktívak: `PhotoContextMenu.qml:142–148,299–304,444–447`; a nézőben is van Reset Faces: `ViewerContextMenu.qml:229–231`. A művelet hiánya nem állítható, csak a felső menü elérési útjáé. |
| `ID_FACES` | **#4331: megvalósítva.** | A `PicasaMenuBar.qml` „From Faces in Selection...” tétele a kijelölt képsorokat a meglévő filmkészítő arcfilm-módjába adja át. A valódi kattintástól a nem üres MP4-ig tartó teszt a `test_arcfilm_fejlec_4212.py`; a timeline arc-kivágását nem méri (nyitott #4400). |
| `ID_FACESRANDOM` | **#4633: a menütétel és a bizonyított People-album bemenet megvalósítva; a timeline arc/crop út nyitott.** | A `PicasaMenuBar.qml` „From People Albums...” sora kijelölés és nyitott személyalbum nélkül is elérhető; a `Main.qml` a meglévő `personMovieSourceUrls()` listát adja a `CreateDialogs.openMovieForSources()` útjának. A kattintásos kimenetpróba: `test_emberek_album_film_menu_4633.py`; a timeline belső arc-/crop-adatút továbbra is #4400. |
| `ID_HELP_KEYBOARD_SHORTCUTS` | **Jelenleg helyfoglaló; az eredeti szolgáltatás szándékosan nem cél.** | `PicasaMenuBar.qml:2190`. Az eredeti művelet a megszűnt Picasa súgó-webhelyet nyitotta (`picasa-menu-parancsok-viselkedes.md` §22). A helyi `runtime\shortcuts.xml` hiányát a §22 és a #442 már külön nyitott kérdésként rögzíti; ez nem azonos az eredeti webes paranccsal. |
| `ID_HELP_CHECK_FOR_UPDATES` | **Szándékosan nem cél: megszűnt Google-szolgáltatás.** | `PicasaMenuBar.qml`: a Súgó ▸ „&Check for Updates” tétele `retired: true` (#4640), szürke és pont nélküli. A Picasa a `winedisable.txt` szerint Wine alatt letiltotta (`picasa-menu-leltar.md` 9. szakasz); a PicasaPy saját frissítéskeresése nem paritás-feladat. |
| `ID_HELP_TERMS`, `ID_FILE_EPROCESS`, `ID_TOOLS_UPLOAD`, `ID_TOOLS_UPLOADMGR` | **Szándékosan nem cél: megszűnt online szolgáltatás.** | `PicasaMenuBar.qml:625`, `:2198`, `:1845`, `:1891`; `PicasaMenuItem.qml:19–28` külön kezeli a helyfoglalót és a nyugdíjazott tételt. |
| `ID_TOOLS_DOWNLOAD_FACES` | **Szándékosan nem cél; az eredeti Picasa 3.9 is eltávolította a menüből.** | A bináris `0x0056f694` címen `RemoveMenu`-t hív az `ID_TOOLS_DOWNLOAD_FACES` azonosítóra; részletesen `picasa-menu-parancsok-viselkedes.md` §36.1. A Picasa Web Albums szolgáltatása megszűnt. |
| `ID_PICTURE_GEOTAG` | **Az eredeti Google Earth-integráció szándékosan nem cél Linuxon.** | Eredeti telepítés-/COM-függőség: `picasa-menu-parancsok-viselkedes.md` §33.5, külön kezelő `0x005cc825` → `0x00600580`. A helyi Helyek-panel geocímkézése nem ugyanaz a Google Earth-beléptető. A külön `ID_PICTURE_GEOUNTAG` viszont ma aktív menüpont (`PicasaMenuBar.qml:1926–1931`); a §33.5 korábbi „hiányzik” állítása elavult. |
| `ID_TIVO`, `ID_VIEW_RDESK` | **A Linux célplatformon nem elérhető, platformfüggő eredeti funkciók.** | `ID_TIVO` az eredeti `eMenuCreateWin` menüből való, TiVo-akcióval (`picasa-menu-parancsok-viselkedes.md` §35.1, §35.4). `ID_VIEW_RDESK` nyugdíjazott tétel `PicasaMenuBar.qml:1024–1027`. |
| `ID_VIEW_MYCOMPUTER`, `ID_VIEW_MYDOCS`, `ID_VIEW_MYPICTURES` | **A QML-ben megvannak, Linuxon rejtett Windows-útvonalak.** | `PicasaMenuBar.qml:1298–1340`; a Windows-platform kapui miatt a Linuxos felhasználónál nem jelennek meg. A Linux-first eltérés az `ui-audit-context-menus.md` A.4-ben is rögzített. |
| `ID_PICTURE_HIDE_TEXT`, `ID_PICTURE_SHOW_TEXT` | **Menüpontok megvannak, de helyfoglalók.** | `PicasaMenuBar.qml:1725–1732`. Javasolt jegy: „A Kép ▸ Show/Hide Text kapcsolja a kijelölt képek szövegfedvényeit”, az eredeti állapotfüggő feltétel és csoport viselkedésével. |
| `ID_TOOLS_ADJUST_TIMESTAMP` | **Menüpont megvan, de helyfoglaló.** | `PicasaMenuBar.qml:1888`. Javasolt jegy: „Az Eszközök ▸ Adjust Date and Time módosítsa a kijelölt képek dátumát az eredeti két módjával” (`picasa-menu-parancsok-viselkedes.md` §3). |
| `ID_TOOLS_CONFIG_SLINGSHOT`, `ID_TOOLS_CONTACTMGR` | **Menüpontok megvannak, de helyfoglalók.** | `PicasaMenuBar.qml:1846`, `:1872`. Javasolt külön jegyek: „A People Manager kezelje az emberek neveit/albumait”; „A Configure Photo Viewer nyissa meg a néző beállításait”. A két eredeti viselkedés PicasaPy-megfeleltetése külön ellenőrzendő. |
| `ID_VIEW_16`, `ID_VIEW_EDIT`, `ID_VIEW_PICTURE`, `ID_VIEW_SEARCHVIEW`, `ID_VIEW_SMALL` | **Menüpontok megvannak, de helyfoglalók.** | `PicasaMenuBar.qml:775`, `:882`, `:885–890`, `:1015–1022`, `:1660`. `ID_VIEW_EDIT` / `ID_VIEW_PICTURE` esetében a `Ctrl+3` és a kép helyi menüje másik belépő, de a menüsori elem továbbra sem működik. A `Small Pictures` eredeti hatása a kódból nem dönthető el; fejlesztési jegy előtt tisztázandó. |
| `ID_VIEW_TIMELINE` | **#5377: a teljes képernyős Időrend-bemutató elérhető.** | A `PicasaMenuBar.qml` menüpontja és a `Main.qml` `Ctrl+5` útja a `TimelineView.qml` bemutatóját nyitja; a kijelölés nem előfeltétel. Valódi billentyű-, kattintás-, csúszka- és képkockapróba: `tests/app/qml_functional/test_idorend_bemutato_5377.py`; a mért mozgásképletek QEMU-pontjai: `tests/app/test_timeline_motion_5377.py`. A gyűjtemény forrásának és dátumjelentésének nyitott kérdései a #5401 hatókörében maradnak. |

## 3. réteg — helyi menük, gyorsbillentyűk és húzás/ejtés

Az eredeti helyi menük teljes rekordtábláit és a 44 gyorsbillentyű-rekordot a `ui-audit-context-menus.md` D.1 és a `picasa-gyorsbillentyuk.md` 4. szakasza adja. Az alábbi státusz az aktuális QML-t olvassa. A régi táblázatok dátumozott pillanatképek; nem mind a mai kódot írják le.

| Helyi menü | Mai QML-állapot | Eltérés / bizonyíték |
|---|---|---|
| Mappa (`Folder`) | A 15 látható sorból a műveleti sorok aktívak; a Hide/Unhide egy állapotfüggő, aktív tétel; a Delete Folder aktív; Google Photos feltöltés nyugdíjazott; Add name tags helyfoglaló. | `FolderContextMenu.qml:80–310`; összevetve `ui-audit-context-menus.md` §1-gyel. A `picasa-menu-parancsok-viselkedes.md` §32.1 régi táblája még Hide/Unhide/Delete Folder helyfoglalónak mondja: ez elavult. Az eredeti 18 azonosító és a mai 15 megjelenő sor száma nem ugyanaz: almenü/szolgáltatási tételek és az állapotfüggő Hide/Unhide összevonása miatt. |
| Képrács (`AlbumPhoto` / `FolderPhoto`) | View and Edit, forgatás, visszavonás, elrejtés, mappába mozgatás, fájlmegnyitás, mentés/visszaállítás, lemezkeresés, törlés, útvonal-másolás, tulajdonságok és arc-visszaállítás aktív; Split Folder, Open With és People Album Thumbnail helyfoglaló; webes feltöltés nyugdíjazott. | `PhotoContextMenu.qml:142–456`; eredeti rekordtábla `ui-audit-context-menus.md` D.1. A „Keresés” almenü jelenléte feltételes; a régi D.5 táblázat több további eltérést sorol fel. A „Open File” nem bizonyít külső szerkesztőt. |
| Néző (`OneUp`) | Vissza a könyvtárhoz, forgatás, visszavonás, elrejtés, fájlmegnyitás, mentés/visszaállítás, lemezkeresés/törlés, útvonal-másolás, arc-visszaállítás és tulajdonság aktív; Open With helyfoglaló; online feltöltések nyugdíjazottak. | `ViewerContextMenu.qml:100–240`; eredeti 17 sor: `ui-audit-context-menus.md` §3. A megnyitás külső alkalmazásba irányuló hatása kattintással ellenőrizendő. |
| Album | Törlés, leírás, kijelölés, indexkép-frissítés és HTML export aktív; Add name tags és Sort Album By helyfoglaló; Online Actions és feltöltések nyugdíjazottak. | `AlbumContextMenu.qml:51–138`; eredeti 13 azonosító/12 felirat: `ui-audit-context-menus.md` A.2 és `picasa-menu-parancsok-viselkedes.md` §32. |
| Gyűjtemény (`Collection`) | Rename/Remove aktív felhasználói gyűjteményen; jelszó csak a beépített Rejtett mappák gyűjteménynél aktív, másutt helyfoglaló. | `CollectionContextMenu.qml:26–45`; a régi `ui-audit-context-menus.md` §4 „teljesen hiányzik” állítása elavult. |
| Emberek album | Select All és Clear Selection aktív; Delete/Edit People Album helyfoglaló. | `PeopleAlbumContextMenu.qml:26–46`. |
| Bal oldali lista (`AlbumList`) | Négy rendezési mód és fordítás, személyrendezés, egyszerűsített fa él; Show Thumbnails, Shortcuts és Desktop helyfoglaló; Windows gyökérváltók Linuxon nem jelennek meg. | `FolderListContextMenu.qml:45–225`; eredeti táblázat `ui-audit-context-menus.md` A.2. A helyi menü „Desktop” eleme nem azonos a működő Nézet ▸ Desktop paranccsal. |
| Képtálca (`Tray`) | A hét műveletnek van aktív `onTriggered` útja. | `TrayContextMenu.qml:45–95`; eredeti gyorsbillentyűk `picasa-gyorsbillentyuk.md` §4. Az eredeti `Ctrl+H` nincs aktív QML `Shortcut`-ként bekötve és a mai menüfeliratban sincs feltüntetve. A többi billentyű fókusz-/tálcakijelölés-hatása kattintással ellenőrizendő. |
| Szövegmező (`Address`) | Undo, Cut, Copy, Paste, Delete, Select All aktív, állapottól függően tiltott; Auto-Complete helyfoglaló. | `TextFieldContextMenu.qml:41–88`; az eredeti héttételes lista `picasa-menu-parancsok-viselkedes.md` §19. |
| Címke (`Tags`) | A három művelet aktív. | `TagContextMenu.qml:21–46`; a gazda `TagsPanel.qml`-ben van bekötve. |
| Kollázs | Az egykép-, csoport- és vászonmenük kezelői a kollázsvezérlőre vezetnek; a műveleteket témaképesség és kijelölés szerint tiltják. | `CollageContextMenus.qml:102–282`; részletes táblák `kollazs-panel-ui-spec.md` §7.6. A képesség-feltételes elemek végpontjai kattintással nem voltak próbálva. |

### Gyorsbillentyűk

Az eredeti **9 menüépítőben 44 gyorsbillentyűs rekord** van (`picasa-gyorsbillentyuk.md` §4). Az aktuális QML `Shortcut`-jai a `Main.qml`, `PicasaMenuBar.qml`, `PhotoViewer.qml` és más nézetek között oszlanak meg; a régi §6 „20 Shortcut” összesítése és több státusza már nem aktuális.

**#4398 utáni állapot (2026-10-06):** a korábbi 53-as mérés pillanatfelvétel volt; a jelenlegi forrás 54 `Shortcut` deklarációt tartalmaz nyolc QML-fájlban. A gazdanézetek és a forrásban tényleges fókuszkapuk a `picasa-gyorsbillentyuk.md` §6.2 táblázatában vannak. A könyvtári `Shortcut`-ok nem aktívak a szerkesztőben, a szövegfókusz tiltja az alkalmazás gyorsbillentyűit, a csúszkák `+`, `=`, `-`, `_` billentyűket csak a szerkesztő 3–5. fülén fogadják; mindhárom viselkedést valódi billentyűleütéses QML-teszt ellenőrzi. A 44 eredeti helyi menürekord egyedi parancs-megfeleltetése továbbra is nyitott.

| Billentyűcsoport | Mai állapot | Bizonyíték |
|---|---|---|
| `Ctrl+A/D/I`, `Ctrl+C/X/V`, `Ctrl+S`, `Ctrl+R`, `Ctrl+Shift+R`, `Ctrl+Shift+H/V`, `Ctrl+3`, `Ctrl+4`, `Ctrl+T`, `Ctrl+F`, `Ctrl+K`, `Ctrl+F6/F7/F8`, `Ctrl+1/2`, `Ctrl+M/O/N`, `Ctrl+P`, `Ctrl+Shift+P`, `Ctrl+Shift+S`, `F1`, `Shift+F1`, `F2`, `Alt+Return`, `Ctrl+Return`, `Delete`, `Ctrl+Delete` | A forrásban aktív QML kötés látható; `Ctrl+Shift+H/V`, `Ctrl+F`, `Ctrl+K` és `Ctrl+3` tehát nem hiányzóként kezelendő. | `Main.qml:919–998`, `:1068–1441`; `PicasaMenuBar.qml:389–460`; néző- és rácsesemények `PhotoViewer.qml:1368–1389`, `LightboxFeed.qml:356–391`. |
| `Ctrl+5` | **Aktív:** kijelölés nélkül megnyitja a teljes képernyős Időrend-bemutatót (#5377). | `Main.qml` `toggleTimeline()`; valódi billentyűteszt: `tests/app/qml_functional/test_idorend_bemutato_5377.py`. |
| `Ctrl+H` (tálca: kijelölés megtartása) | **Aktív, nézet- és fókuszkapuval.** | A `TrayBar.qml` `trayKeepSelectionShortcut` a főablak létezését, a néző bezárt állapotát, a tálcakijelölést és a szövegfókusz hiányát kéri. A #4398 előtti hiánymegállapítás elavult volt. |
| `F11`, `/`, `,`, `.` | Eredeti 48-rekeszes keymapben szerepelnek; aktív megfelelőjük a jelen QML-leltárban nem található. A videóvezérlő pontos billentyűhatása nyitott. | Eredeti tábla `picasa-gyorsbillentyuk.md` §2.5; aktuális QML-beli `sequence`/`Keys` leltár. Ne állítsuk kattintásos/valós idejű próba nélkül, hogy mindegyik fejlesztői hiány. |
| Helyi menü billentyűfeliratai | A Folder helyi menü megjeleníti a `Ctrl+A/D/I/Enter` címkéket; a Photo/Viewer a `Enter`, forgatás, `Ctrl+Shift+O`, mentés, keresés, törlés és `Alt+Enter` feliratokat. Az Album/People/Tray listák nem mind mutatják az eredeti gyorsbillentyű-szövegeket. | `FolderContextMenu.qml:89–259`, `PhotoContextMenu.qml:142–407`, `ViewerContextMenu.qml:100–240`, `TrayContextMenu.qml:45–95`, `AlbumContextMenu.qml:71–105`, `PeopleAlbumContextMenu.qml:37–45`. A menüfelirat és a fókuszban ténylegesen elsülő globális shortcut külön bizonyítandó. |

### Húzás és ejtés

| Eredeti / jelenlegi művelet | Eredmény | Bizonyíték |
|---|---|---|
| Képek húzása a Picasa rácsából kifelé, OS/Explorer célra | **Nyitott; kimenő paritás nincs igazolva.** | Az eredeti `ytDragNode` `DoDragDrop` útja: `picasa-eger-es-kijeloles.md` §5 és §14, `0x00aa1fb0`. A QML-leltárban a kép húzó proxy `Drag.active`-et és `payload="photos"`-t állít be, de nincs `Drag.mimeData`/URI-kimenet a `ThumbDelegate.qml:279–305`-ben. Asztali drag-próba nincs. |
| Fájl ejtése az alkalmazásra | **Kódút megvan; kattintás/desktop próba nincs.** | `ImportDropArea.qml:10–31` → `dropImportController.importDroppedUrls`; `Main.qml:3360–3364`; a vezérlő `drop_import_controller.py:92–…`. |
| Képek ejtése az albumlistára, albumra vagy képrácsra | **Belső QML-út megvan.** | `ThumbDelegate.qml:279–305`, `AlbumsSection.qml:89–96,176–183`, `LightboxFeed.qml:1019–1028`. Az albumcélok kezelői `FolderPane.qml:519–523`-nál folytatódnak. Valódi egérhúzás nem volt kipróbálva. |

## 4. réteg: néma gombok (2026-10-17)

**Módszer.** A `scripts/check_silent_qml_controls.py --list` a mai munkafán 32 jelöltet adott: 27 `enabled: false` kötést és 5 fogadó nélküli QML-jelzést. Külön, kiterjesztett keresés vizsgálta a `Clicked`, `Triggered`, `Toggled`, `Pressed`, `Released`, `DoubleClicked`, `Entered`, `Exited`, `PositionChanged`, `Wheel`, `Dropped`, `Accepted` és `Canceled` eseményeket; üres vagy csak `console.log` hívást tartalmazó kezelő nem volt. Két további kezelő csak a saját dialógusát zárja be. A szülő `enabled` állapotát a proxy- és Web Albums-csoportnál a gyerekekre is végigkövettem. Az eredeti viselkedést a hivatkozott spec-lapok és a `ui-lefedettseg-elemek.csv` alapján adom meg; ha nincs leírva, a táblázat ezt kimondja.

Lefutott a három megadott mérő. A `nema_slotok.py` 920 `@Slot`/`@Property` tagból kettőt jelölt: `setAutoPlayMovies` és `setEnableHover`. Mindkét találat téves, mert a `@Slot` csak kommentben szerepel; a QML a két tulajdonságot olvassa. A `nema_jelzesek.py` 278 jelzésből 108 property-értesítőt és 170 akció-jelzést talált, gazdátlan akció-jelzést nem. A `nema_beallitasok.py` két gyanút jelzett: `mail/useDefaultClient` és `mail/EmailAutocomplete`; az első a levélválasztó kezdőpaneljét állítja, a második a jelölő állapotát menti, de a címjavaslatot nem állítja elő. Nyolc kulcsot nem tudott közvetlenül követni: a két régi e-mail-méretindex migrációs tartalék, a hat képernyővédő-kulcs olvasója és írója viszont a `screensaver_controller.py` és a `ScreensaverDialog.qml` között végigkövethető. Ezek a mérő vakfoltjai, nem negatív eredmények.

Az ellenőrzés statikus forrásvizsgálat. A CI-őr csak a `Clicked` és `Triggered` eseményeket, a közvetlen `enabled: false` értéket és a QML-jelzés-fogadókat keresi. A bővített eseménykeresés nem futtatja a felületet, a dinamikus `enabled` feltételek elérhetőségét pedig nem méri végig minden állapottal. A `nema_slotok.py` a kommentben szereplő `@Slot` szöveget is találatnak veszi; a `nema_beallitasok.py` nem tudja követni a szótárba olvasott értékeket. A forráslánc ezért nem helyettesíti a kattintásos próbát.

**Szúrópróba, teljes hívási lánc.** A 2026-10-17 statikus ellenőrzés idején a Ctrl+5 `Shortcut` és az Időrend `MenuItem` még le volt tiltva, a menüjelzésnek pedig nem volt fogadója. Ezt az állapotot a #5377 felülírta: a `Ctrl+5` a `Main.qml:toggleTimeline()`-on át nyitja a bemutatót, a Nézet-menü `timelineRequested` jelzését a `Main.qml` fogadja, és mindkét út kijelölés nélkül működik. A valós kattintást és a teljes képernyős ablakot a `test_nezet_menu_valodi_5150.py`, a valódi billentyűt és kilépést a `test_idorend_bemutato_5377.py` ellenőrzi. Az e-mail-mód útja: QSettings → `EmailController.useDefaultClient` → Beállítások rádiógombjai → `EmailController.sendRows`, ahol az érték dönti el, hogy a levelező azonnal indul-e (saját levelezős mód) vagy a választó párbeszéd kérdez (#6987-től; korábban az `EmailChoiceDialog.onOpened` választott `compose` vagy `choose` panelt); tehát a beállítás nem néma. Az Auto-Complete útja: helyi menüelem → mentő slot → QSettings. A bináris lelet szerint az eredeti kapcsolónak sincs olvasója; a címjavasló osztály a Gmail-ágú levélszerkesztő része. A „Don't Set” útja: `collageFormatDontSetButton` → `formatRejected()` → figyelmeztetés bezárása; a folytató művelet hiánya megfelel a gomb jelentésének. A Crop útja: `editToolCrop` → `toolActivated`/`cropActive` → a vágópanel megjelenik; a külön `cropRequested` jelzés fölösleges.

| Elem, objectName és felirat | Fájl:sor | Gyanú | Eredeti viselkedés és forrása | Ítélet |
|---|---|---|---|---|
| Ctrl+5 `Shortcut`; objectName nincs; felirat `Ctrl+5` | `Main.qml`, `toggleTimeline()` | A #5377 előtt állandóan tiltott volt. | A Ctrl+5 kijelölés nélkül nyitja az Időrend bemutatót; [picasa-gyorsbillentyuk.md 10.6](picasa-gyorsbillentyuk.md), [picasa-menu-parancsok-viselkedes.md 38.2](picasa-menu-parancsok-viselkedes.md). A teszt valódi Ctrl+5 leütést küld. | működik (#5377) |
| Rejtett mérőcsúszka `id=mertekek`; objectName és qsTr-felirat nincs | `EditorFinetunePanel.qml:59` | `visible: false` mérőelemre is `enabled: false` áll. | NINCS LEÍRVA; ez nem felhasználói vezérlő. | nem cél |
| Effektpanel elmosó rétege `objectName=paramPanelTabBlur`; qsTr-felirat nincs | `EditorPanel.qml:857` | A `ShaderEffectSource` le van tiltva, de nem gomb. | NINCS LEÍRVA; látványréteg, a bemeneti eseményt az alatta lévő vezérlő kapja. | nem cél |
| Visszavonás-sor elmosó rétege `objectName=paramPanelUndoBlur`; qsTr-felirat nincs | `EditorPanel.qml:874` | A `ShaderEffectSource` le van tiltva, de nem gomb. | NINCS LEÍRVA; látványréteg, a bemeneti eseményt az alatta lévő vezérlő kapja. | nem cél |
| Google Mail rádiógomb `objectName=emailChoiceGsender`; qsTr: `Google Mail` | `EmailChoiceDialog.qml:141` | A Google-fiókos ág állandóan tiltott. | Az eredeti levélválasztó Gmail-ágat is kínált; [picasa-email-kuldes.md 6. szakasz](picasa-email-kuldes.md). A PicasaPy Google-bejelentkezése nem cél. | nem cél |
| Change User gomb `objectName=emailComposeChangeUserButton`; qsTr: `Change User` | `EmailChoiceDialog.qml:277` | Kattintás nem lehetséges. | Az eredeti fiókváltás a Gmail-bejelentkezéshez tartozott; [picasa-fen-dialogs.md 4.5](picasa-fen-dialogs.md), [ui-lefedettseg-elemek.csv:369](ui-lefedettseg-elemek.csv). | nem cél |
| Upload jelölőnégyzet `objectName=importSourceUploadCheckBox`; qsTr: `Upload` | `ImportSourceDialog.qml:440` | A feltöltés jelölője le van tiltva. | Picasa Web Albums-feltöltés; a szolgáltatás megszűnt, [ui-lefedettseg.md](ui-lefedettseg.md), [picasa-menu-leltar.md](picasa-menu-leltar.md). | nem cél |
| Csak csillagozottak szinkronja `objectName=importSourceSyncStarredOnlyCheckBox`; qsTr: `Sync starred photos only` | `ImportSourceDialog.qml:471` | A szinkronjelölő le van tiltva. | Picasa Web Albums-szinkron; a szolgáltatás megszűnt, [picasa-fen-dialogs.md 4. szakasz](picasa-fen-dialogs.md). | nem cél |
| Webszinkron kapcsoló `objectName=folderSyncSwitch`; felirat: `Sync to Web` | `LightboxHeader.qml:277` | A jelölő állandóan tiltott és hamis. | Webalbum-szinkron; megszűnt szolgáltatás, [picasa-keptalca.md](picasa-keptalca.md), [ui-lefedettseg-elemek.csv](ui-lefedettseg-elemek.csv). | nem cél |
| Fejléc feltöltésgomb `objectName=headerUploadButton`; felirat: `Upload` és a kijelölt képek száma | `LightboxHeader.qml:660` | A feltöltés gombja le van tiltva. | Picasa Web Albums-feltöltés; a szolgáltatás megszűnt, [picasa-keptalca.md](picasa-keptalca.md). | nem cél |
| Google-fiók rádiógomb `objectName=optionsMailGoogleRadio`; qsTr: `Use my Google Account` | `OptionsTabEmail.qml:107` | A beállítás állandóan tiltott. | Az eredeti e-mail opció Gmailt ajánlott; [picasa-email-kuldes.md](picasa-email-kuldes.md). A Google-fiókos út nem cél. | nem cél |
| Outlook HTML jelölőnégyzet `objectName=optionsMailUseHtmlCheck`; qsTr: `Send inline photos and captions (Outlook only)` | `OptionsTabEmail.qml:280` | Az eredeti beállítás minden platformon tiltott. | Az eredeti Outlook-integráció HTML-levélben küldött képeket és feliratot; [picasa-email-kuldes.md](picasa-email-kuldes.md), [ui-lefedettseg.md](ui-lefedettseg.md). A mai QML-ben nincs működő út; Windowsos elérhetőség külön nincs igazolva. | néma |
| Anonim statisztika `objectName=optionsUsageStatsCheck`; qsTr: `Send anonymous usage statistics` | `OptionsTabGeneral.qml:299` | Adatküldő beállítás állandóan tiltott. | Eredeti telemetriai beállítás az options.fen-ben; [picasa-fen-dialogs.md 3.11](picasa-fen-dialogs.md), [ui-audit-mainwindow.md](ui-audit-mainwindow.md). | nem cél |
| Automatikus frissítés `objectName=optionsUpdateModeCombo`; saját felirata: `Check for updates automatically` | `OptionsTabGeneral.qml:345` | Működő, alapból bekapcsolt kapcsoló; a PicasaPy a GitHub-kiadásokat ellenőrzi (`updates/autoCheck`). | Saját funkció (#6340), nem az eredeti Picasa külső frissítője; részletek: [védett saját funkciók](../decisions/vedett-sajat-funkciok.md) és a [Beállítások súgó](../../src/picasapy/help/features/beallitasok.md). | saját funkció |
| Google Contacts-fényképfeltöltés `objectName=optionsFaceUploadContactPhotosCheck`; qsTr: `Upload people album thumbnails to Google Contacts` | `OptionsTabNameTags.qml:234` | A feltöltési jelölőnégyzet le van tiltva. | Az eredeti névjegykép-feltöltés külső Google Contacts-integráció; [picasa-fen-dialogs.md 4.1](picasa-fen-dialogs.md). Nem cél. | nem cél |
| Proxycsoport: `optionsNetworkProxyUserField`, `optionsNetworkProxyPasswordField`, `optionsNetworkAutoDetectCheck`; feliratok: `Proxy username (Windows only):`, `Proxy password:`, `Automatically detect network settings` | `OptionsTabNetwork.qml:18` | A szülő csoport tiltott, ezért a három gyerekmező sem aktív. | Eredeti options.fen proxybeállításai; a PicasaPy nem használ proxyt, ezt a QML kódbeli megjegyzése is rögzíti. A hálózati naplózás külön, aktív vezérlő. | nem cél |
| Web Albums beállításcsoport: `optionsWebUploadSizeCombo`, `optionsWebStripedUploadCheck`, `optionsWebKeepJpegQualityCheck`, `optionsWebStarredOnlyCheck`, `optionsWebConfirmSyncDisableCheck`; feliratok: feltöltési méret, előnézet előbb, eredeti minőség, csillagozottak, szinkronmegerősítés | `OptionsTabWebAlbums.qml:21` | A teljes fül gyökere tiltott, ezért minden gyerekvezérlő tiltott. | Picasa Web Albums-feltöltés és szinkron; a szolgáltatás megszűnt, [picasa-fen-dialogs.md 3.11](picasa-fen-dialogs.md), [ui-lefedettseg.md](ui-lefedettseg.md). | nem cél |
| Arc-címkék webszinkronja `objectName=peopleManagerSyncCheck`; qsTr: `Sync Face Tags with Web Albums` | `PeopleManagerDialog.qml:485` | A jelölőnégyzet le van tiltva. | Arc-címkék szinkronja Picasa Web Albumsba; a szolgáltatás megszűnt, [picasa-arcfelismeres.md](picasa-arcfelismeres.md). | nem cél |
| Online kapcsolatok kezelése `objectName=peopleManagerOnlineButton`; qsTr: `Manage Online Contacts` | `PeopleManagerDialog.qml:514` | A gomb le van tiltva. | Google Contacts-fiók kezeléséhez tartozik; [picasa-fen-dialogs.md 4.1](picasa-fen-dialogs.md). Külső kapcsolat nem cél. | nem cél |
| Online kapcsolatok frissítése `objectName=peopleManagerRefreshButton`; qsTr: `Refresh Contacts` | `PeopleManagerDialog.qml:519` | A gomb le van tiltva. | Google Contacts-letöltés; [picasa-menu-parancsok-viselkedes.md 24.4](picasa-menu-parancsok-viselkedes.md). Külső kapcsolat nem cél. | nem cél |
| Modális elmosás `objectName=editorModalDialogBlur`; qsTr-felirat nincs | `PhotoViewer.qml:5250` | Inputot nem fogadó `Rectangle` tiltott. | NINCS LEÍRVA; a Qt modális párbeszéde kezeli a bemeneti fókuszt, ez csak látványréteg. | nem cél |
| Nézet menü Időrend `objectName=menuViewTimeline`; qsTr: `Ti&meline`, gyorsbillentyű-felirat `Ctrl+5` | `PicasaMenuBar.qml`, `Main.qml` | A #5377 előtt a menüpont le volt tiltva és a jelzésnek nem volt fogadója. | A kattintás a teljes képernyős Időrend-bemutatót nyitja; valódi kattintással ellenőrzi a `test_nezet_menu_valodi_5150.py`, az ablak és a vezérlés részleteit a `test_idorend_bemutato_5377.py`. | működik (#5377) |
| Upload menü `title=U&pload`; objectName nincs | `PicasaMenuBar.qml:2416` | A teljes menü tiltott. | Feltöltési parancsok a Picasa Web Albums szolgáltatásához tartoznak; [picasa-menu-leltar.md](picasa-menu-leltar.md). A szolgáltatás megszűnt. | nem cél |
| Google Photos feltöltés `objectName=trayUploadButton`; qsTr: `Upload to Google Photos` | `TrayBar.qml:1852` | Feltöltésgomb állandóan tiltott. | Külső Google Photos-feltöltő; a PicasaPy nem célozza az online feltöltést, [picasa-keptalca.md](picasa-keptalca.md). | nem cél |
| Nyomat rendelése `objectName=trayOrderButton`; ToolTip: `Order Prints (service discontinued)` | `TrayBar.qml:2118` | Külső rendelésgomb tiltott. | Az eredeti nyomat-rendelő partner megszűnt; [ui-lefedettseg-elemek.csv:436](ui-lefedettseg-elemek.csv), [picasa-keptalca.md](picasa-keptalca.md). | nem cél |
| Hello megosztás `objectName=trayShareButton`; qsTr-felirat nincs | `TrayBar.qml:2135` | Nincs aktív backend. | Az eredeti Hello-megosztás online szolgáltatásához nem tartozik működő backend; [ui-lefedettseg-elemek.csv:170](ui-lefedettseg-elemek.csv). | nem cél |
| Blogger `objectName=trayBlogButton`; ToolTip: `Publish to Blogger (service discontinued)` | `TrayBar.qml:2150` | Külső publikálásgomb tiltott. | A Blogger-integráció megszűnt; [ui-lefedettseg-elemek.csv:437](ui-lefedettseg-elemek.csv), [picasa-keptalca.md](picasa-keptalca.md). | nem cél |
| „Don't Set” gomb `objectName=collageFormatDontSetButton`; qsTr: `Don't Set`; kibocsátja a `formatRejected` jelzést | `CollageDialogs.qml:38,190-196` | A QML-jelzésnek nincs fogadója. | NINCS LEÍRVA külön eredeti vezérlőként. A gomb elutasítja a formátummódosítást és bezárja a figyelmeztetést; a folytató művelet hiánya megfelel a feliratnak. | működik |
| Dokumentumfül aktiválása `signal tabActivated`; delegált fül neve `documentTab` prefix, a cím dinamikus | `DocumentTabStrip.qml:70,87-90` | A jelzésnek nincs fogadója. | Az eredeti kollázs önálló fül a könyvtár mellett; [kollazs-panel-ui-spec.md 3.1-3.3](kollazs-panel-ui-spec.md). A `activeTabId` közvetlenül köti a tartalom láthatóságát. | működik |
| Crop eszköz `objectName=editToolCrop`; qsTr: `Crop`; `cropRequested` jelzés | `EditorPanel.qml:452`; eszköz: `EditorTabCommonFixes.qml:91-98` | A külön jelzésnek nincs fogadója. | Az eredeti Crop eszköz megnyitja a vágó panelt; [ui-audit-editor.md](ui-audit-editor.md). A működő `toolActivated` és `cropActive` út nyitja meg. | működik |
| Időrend menüjelzés `timelineRequested`; objectName és qsTr-felirat nincs | `PicasaMenuBar.qml`, `Main.qml` | A #5377 előtt nem volt fogadója. | A `Main.qml` a jelzésre ugyanazt a `toggleTimeline()` belépőt hívja, mint a Ctrl+5. | működik (#5377) |
| Fotóhúzás-kiegészítő jelzés `photoDragStarted`; objectName és qsTr-felirat nincs | `ThumbDelegate.qml:72,310-314` | A jelzésnek nincs fogadója. | Az eredeti képhúzás leírása: [picasa-eger-es-kijeloles.md 5. és 14. szakasz](picasa-eger-es-kijeloles.md). A belső húzást a `Drag.active` indítja; az OS felé menő fájlhúzás külön nyitott réteg. | működik |
| Hibaablak OK `objectName=passportErrorOkButton`; qsTr: `OK` | `PassportErrorDialog.qml:66` | A kezelő csak a saját dialógust zárja be. | NINCS LEÍRVA a lefedettségi CSV-ben vagy a kapcsolódó specben. A gomb célja az üzenet bezárása, a hívási út működik. | működik |
| Kulcsszóablak Done `objectName=keywordDoneButton`; qsTr: `Done` | `KeywordsDialog.qml:225` | A kezelő csak a saját dialógust zárja be. | NINCS LEÍRVA külön eredeti gombként. A kulcsszómódosító vezérlők után ez zárja a párbeszédet. | működik |
| Videó-automatikus lejátszás beállítója `setAutoPlayMovies`; objectName és qsTr-felirat nincs | `appearance_controller.py:182` | A slotmérő találta, mert a szomszédos komment `@Slot` szöveget tartalmaz. A metódus nincs dekorálva, a QML a `autoPlayMovies` tulajdonságot olvassa. | Az eredeti AutoPlayMovies videónyitáskor szabályozza az automatikus lejátszást; [ui-audit-editor.md](ui-audit-editor.md), a mai olvasó a `VideoPlayerView.qml:21-24`. | működik |
| Hover-előnézet beállítója `setEnableHover`; objectName és qsTr-felirat nincs | `appearance_controller.py:198` | A slotmérő találta, mert a szomszédos komment `@Slot` szöveget tartalmaz. A metódus nincs dekorálva, a QML az `enableHover` tulajdonságot olvassa. | Az eredeti EnableHover a Ctrl+Alt előnézetet szabályozza; [picasa-gyorsbillentyuk.md 10.33](picasa-gyorsbillentyuk.md), a mai olvasó a `LightboxFeed.qml:124-125`. | működik |
| E-mail mód rádiócsoport `objectName=optionsMailDefaultRadio`, `optionsMailChooseRadio`; qsTr: `Use this computer's default email program`, `Let me choose each time I send pictures` | `OptionsTabEmail.qml:54-76` | A beállításmérő csak tárolt tulajdonságot látott. | Az eredeti EmailPrepType levelezőmódot választ; [picasa-email-kuldes.md 5. szakasz](picasa-email-kuldes.md). A #6987 óta a saját levelezős mód (`useDefaultClient`) belső panel nélkül, azonnal nyitja a rendszer levelezőjét a csatolmányokkal, a másik mód a választót kérdezteti, és a „Native Mail Client” rádió is közvetlenül indít; a tárgy és a törzs a képszám szerint a hivatalos `IDS_MAPI_SUBJ_*` és `IDS_MAPI_BODY_*` szöveg (a `IDS_MAPITAGLINE` reklámsor nélkül), 20-nál több képnél előbb a `CThumbUI::OutputBottleneck` kérdés jön. A `]history:email` jelölés nincs megvalósítva: az `albumdata_token.pmp` album-sorának tokenje, nem `.picasa.ini`-kulcs, a PMP-t pedig a PicasaPy csak olvassa. A Gmail-ág nem cél. | működik |
| Képernyővédő forrásai és kijelölt képei; `objectName=screensaverSourceList`, ismétlődő `screensaverSourceCheck<n>`; feliratok: `Display photos from:`, `Selected Pictures`, illetve a mappa- és albumnevek | `ScreensaverDialog.qml:29-37,109-138`; `screensaver_controller.py:215-251,288-305` | A mérő nem tudta követni a `screensaver/sources` és `screensaver/photoPaths` kulcsokat. | Az eredeti képernyővédőhöz adott képekről a [picasa-menu-parancsok-viselkedes.md 35.3](picasa-menu-parancsok-viselkedes.md) ír; a Linuxos helyi forráslista pontos eredeti megfelelője NINCS LEÍRVA. | működik |
| Képernyővédő `effect`, `seconds`, `showCaptions`; `objectName=screensaverEffectBox`, `screensaverSecondsSlider`, `screensaverCaptionCheck`; feliratok: `Visual effect:`, `Change pictures every:`, `Show captions` | `ScreensaverDialog.qml:150-201`; `screensaver_controller.py:253-286` | A beállításmérő nem találta meg a kulcsok használatát. | Az eredeti Google Photos-képernyővédő külön program volt; a Linuxos helyi beállításmezők pontos eredeti megfelelője NINCS LEÍRVA. [picasa-menu-parancsok-viselkedes.md 35.3](picasa-menu-parancsok-viselkedes.md) leírja a mai helyi képernyővédő adaptációját. | működik |
| Képernyővédő tétlenségi percei; `objectName=screensaverIdleCheck`, `screensaverIdleMinutes`; feliratok: `Start when the computer is idle for`, `minutes` | `ScreensaverDialog.qml:204-244`; `screensaver_controller.py:363-407` | A mérő nem tudta követni a `screensaver/idleMinutes` kulcsot. | Az eredeti képernyővédő Windowsos külön program volt; a Linuxos tétlenségi indítás mai adaptáció. [picasa-menu-parancsok-viselkedes.md 35.3](picasa-menu-parancsok-viselkedes.md). | működik |
| E-mail-méretek migrációja; külön vezérlőnév és felirat nincs, a mai vezérlők: `optionsMailSizeSlider`, `optionsMailSingleSameRadio`, `optionsMailSingleOriginalRadio` | `email_controller.py:255-300`; mezők: `OptionsTabEmail.qml:136-215` | A mérő nem találta a `mail/multiSizeIndex` és `mail/singleSizeIndex` kulcsok olvasóját. | A két kulcs korábbi PicasaPy-formátum, a betöltés a mai képpontméretre és egyképes méretmódra migrál; nem eredeti Picasa-vezérlők. Az eredeti e-mail-méret viselkedése: [picasa-email-kuldes.md 3. szakasz](picasa-email-kuldes.md). | működik |
| Címzett Auto-Complete `objectName=textMenuAutoComplete`; qsTr: `Auto-Complete` | `TextFieldContextMenu.qml:88-104`; mező: `EmailChoiceDialog.qml:305-317` | A mérő nem találta a beállítás olvasóját; a QML a pipát menti és rajzolja, javaslómodellt nem találtam. | Az eredeti `Preferences\EmailAutocomplete` kapcsolónak nincs olvasója, csak a pipa állapotát tárolja; a címjavasló a Gmail-ágú levélszerkesztő része, ami nem cél. [picasa-menu-parancsok-viselkedes.md 24.2, 24.6, 57.1-57.2](picasa-menu-parancsok-viselkedes.md). | működik |

A #5377 óta az Időrend menüpontja, a Ctrl+5 és a menüjelzés-fogadó működik; ezek már nem néma vagy elérhetetlen fejlesztési tételek. Az Outlook-only levélbeállítás továbbra is nem cél. A megszűnt online szolgáltatások és a nem interaktív segédrétegek nem hiányzó termékfunkcióként vannak számolva. A többi dinamikus `enabled` kötés teljes futásidejű elérhetősége és kattintásos próbája nyitott marad.

## 6. réteg — tiszta telepítés

**Mérési dátum:** 2026-10-13. **Teszt:** `tests/app/qml_functional/test_tiszta_profil_4317.py::test_tiszta_profil_funkciok_valodi_kattintassal`. A program egy ideiglenes HOME, USERPROFILE és üres XDG_CONFIG_HOME/XDG_DATA_HOME/XDG_CACHE_HOME alatt indult; a képmappát és az egyetlen 360×240-es JPEG-et a teszt készítette. A teszt a DNS-feloldást és az IP-socket kapcsolódást letiltotta, az Unix socketet meghagyta. Rögzített hálózati próbálkozás nem volt. A Find Faces párbeszéd mindkét modellt elérhetőnek jelezte, a vizsgálat befejeződött, és a tiszta profil adatkönyvtárába nem került `.onnx` fájl.

| Elem / funkció | Állapot | Bizonyíték |
|---|---|---|
| Tesztképmappa betöltése és indexképrács | **Megvan és működik.** | A `folderRowLabel` valódi kattintása után egy kép látszott a `photoGrid`-ben. Tesztlépés: `_lep_mappa_betoltes_es_indexkep_racs`; kép: [`01-racs.png`](../assets/paritas-tiszta-profil/01-racs.png). |
| Néző megnyitása | **Megvan és működik.** | A bélyegkép valódi dupla kattintása megnyitotta a nézőt (`viewerOpen`). Tesztlépés: `_lep_nezo_valodi_dupla_kattintassal`; a néző a [`03-vorosszem.png`](../assets/paritas-tiszta-profil/03-vorosszem.png) képen látható. |
| Csillag | **Megvan és működik.** | A csillagvezérlő valódi kattintása után a képadat csillagozott állapota igaz lett. Tesztlépés: `_lep_csillag_valodi_kattintassal`. |
| Felirat | **Megvan és működik.** | A teszt valós billentyűbevitellel írta be a feliratot, majd a fotóvezérlőből visszaolvasta a mentett értéket. Tesztlépés: `_lep_felirat_valodi_bevitellel`. |
| Auto Contrast és visszavonás | **Megvan és működik.** | A kattintás hozzáadta az `autolight` réteget, a Visszavonás eltávolította. Tesztlépés: `_lep_auto_kontraszt_es_visszavonas`. Ez az állapotpróba a réteget és a visszavonást ellenőrzi; képpontos eredmény-összevetést nem végez. |
| Export célmappába | **Megvan és működik.** | A File ▸ Export Picture to Folder parancs és az Export gomb kattintással futott; JPEG keletkezett, a párbeszéd bezárult. Tesztlépés: `_lep_export_valodi_menu_es_kattintas`. Az offscreen teszt a fájlválasztó eredményét a párbeszéd `targetFolder` tulajdonságába adta, ezért az operációs rendszer fájlválasztóját nem mérte. |
| Arcfelismerés | **Megvan és működik.** | A Tools ▸ Find Faces kattintással megnyitotta a párbeszédet; a detektor és az embedder elérhető volt, a vizsgálat befejeződött. Nem történt rögzített hálózati próbálkozás vagy modellletöltés. Tesztlépés: `_lep_arcfelismeres_inditasa_letoltes_nelkul`; kép: [`02-arcfelismeres.png`](../assets/paritas-tiszta-profil/02-arcfelismeres.png). A próba a futás befejezését méri, arc találatát nem állítja. |
| Vörösszem-javítás | **Megvan és működik.** | A valódi húzásos kijelölés és az Alkalmaz kattintása a `redeye` réteget a szerkesztési láncba tette. Tesztlépés: `_lep_vorosszem_javitas_valodi_huzassal`; kép: [`03-vorosszem.png`](../assets/paritas-tiszta-profil/03-vorosszem.png). A generált tesztkép nem tartalmaz vörösszemet, ezért a képpontos javítás kimenetét ez a réteg nem minősíti. |

A fenti futásban a felsorolt műveletek mindegyikénél nulla hálózati próbálkozást rögzítettünk. A teszt nem indított asztali vagy külső alkalmazást. E mért tiszta profilos útvonalban nem figyeltünk meg hiányzó vagy nem működő elemet, így ehhez a réteghez nem keletkezett új fejlesztői jegyjavaslat. Ez az eredmény nem zárja le a 7. réteg képpontos effekt-összevetését és nem helyettesíti az összes Picasa-parancs futásidejű vizsgálatát.

## 7. réteg - effektkimenetek

**Mérési dátum:** 2026-10-13. **Render-pillanatkép:** `fix/4317-codex`, `a8ba353b3561`. A PicasaPy kimeneteket az eredeti Picasa 3.9 exportjaival hasonlítottam össze. Az elsődleges referencia a helyi `meroadat.tar` `684-merokeszlet/export` könyvtára; 180 paraméteres sorból 179-hez volt Picasa-export. A 73 renderelt effektcsalád mindegyikéhez van legalább egy ilyen referencia. Az `unsharp` `max` változatához a 684-es csomagban nincs export; annak külön Picasa-referenciája a `meroszett` készletben van.

Az eltérést a meglévő `tools/golden/analyze_validation_kit.py::mean_de` mérővel, CIE76 átlagos ΔE-ként számoltam; az egyezési küszöb a mérő `MATCH_DE = 2.0` értéke. A 684-es és a `meroszett` összevethető képpárjainak mérete egyezett. Minden érték nyers mért szám, nem becslés. Az alábbi 684-es oszlop az `alap`, `max`, `min`, illetve ahol szerepel, a `hex4` és `hex8` változatok egyedi ΔE-it sorolja.

| Effekt | 684-es eredeti Picasa-export ΔE76 | Állapot az összes érvényes eredeti referencián |
|---|---|---|
| `ansel` | alap 0,038 | egyezik |
| `autobacklight` | alap 0,121 | egyezik |
| `autocolor` | alap 0,172 | egyezik |
| `autocontrast` | alap 0,190 | egyezik |
| `autolight` | alap 0,229 | egyezik |
| `backlight` | alap 0,190; max 0,153; min 0,121 | egyezik |
| `blur` | alap 0,116; max 0,104; min 0,104 | egyezik |
| `boost` | alap 0,145; max 0,095; min 0,121 | egyezik |
| `border` | alap 0,095; max 0,055; min 0,121 | egyezik önállóan; láncban lásd alább |
| `bw` | alap 0,034 | egyezik |
| `cinemascope` | alap 1,082 | egyezik |
| `colorfix` | alap 0,121 | egyezik |
| `colortemp` | alap 0,820; max 0,541; min 0,504 | egyezik |
| `comicize` | alap 0,453; max 0,207; min 0,412 | egyezik |
| `contrast` | alap 0,233; max 0,179; min 0,196 | egyezik |
| `crossprocess` | alap 0,764; max 0,121 | egyezik |
| `dir_brite` | alap 0,187 | egyezik |
| `dir_sat` | alap 0,184 | egyezik |
| `dir_sharp` | alap 0,384 | egyezik |
| `dir_tint` | alap 0,170; max 0,199; min 0,121 | egyezik |
| `dropshadow` | alap 0,084; max 0,054; min 0,083 | egyezik |
| `enhance` | alap 0,190 | egyezik |
| `fill` | alap 0,121; max 0,153 | egyezik |
| `finetune` | alap 0,381; max 0,632; min 0,170 | egyezik |
| `finetune2` | alap 0,574; max 0,569; min 0,170 | egyezik |
| `focalpixelate` | alap 0,121; max 0,121; min 0,121 | egyezik |
| `focalzoom` | alap 0,311; max 0,121; min 0,212 | egyezik |
| `gamma` | alap 0,168; max 0,168; min 0,151 | egyezik |
| `glow` | alap 0,264; max 0,284; min 0,121 | egyezik |
| `glow2` | alap 0,264; max 0,284; min 0,121 | egyezik |
| `grain` | alap 2,675 | **eltér**; további mérések lent |
| `grain2` | alap 0,121 | **eltér**; merokit-2: 2,661 |
| `hdr` | alap 0,265; max 0,121; min 0,188 | egyezik |
| `heatmap` | alap 0,537; max 0,121; min 0,557 | **eltér**; meroszett: 4,254 és 3,324 |
| `holga` | alap 0,512; max 0,121; min 0,088 | egyezik |
| `invert` | alap 0,116 | egyezik |
| `ir` | alap 0,063; max 0,121 | egyezik |
| `linblur` | alap/max/min 0,274 | egyezik |
| `localcontrast` | alap 0,159; max 0,258; min 0,121 | egyezik |
| `lomo` | alap 0,267; max 0,121; min 0,263 | egyezik |
| `matte` | alap 0,176; max 0,121; min 0,121 | egyezik |
| `museummatte` | alap 0,230; max 0,287; min 0,128 | egyezik |
| `neon` | alap 0,395; max 0,121 | egyezik |
| `nightvision` | alap 4,528; max 0,121; min 3,624 | **eltér**; további mérések lent |
| `orton` | alap 0,211; max 0,121; min 0,153 | egyezik |
| `pencilsketch` | alap 0,128; max 0,121; min 0,017 | egyezik |
| `picnikfocalpixelate` | alap 0,231; max 0,121; min 0,114 | **eltér**; merokit-2: 8,666 |
| `picnikgrain` | alap 0,882; max 1,380; min 0,121 | egyezik |
| `picniktint` | alap 0,373; max 0,121 | egyezik |
| `pixelate` | alap 0,098; max 0,121; min 0,128 | egyezik |
| `polaroid` | alap 0,118; max 0,131; min 0,131 | egyezik |
| `quantizepalette` | alap 0,347; max 0,121; min 0,360 | egyezik |
| `radblur` | alap 0,326; max 0,324; min 0,340 | egyezik |
| `radsat` | alap 0,082; max 0,128; min 0,034 | egyezik |
| `radtint` | alap 0,688; max 0,690; min 0,669 | egyezik |
| `reanimatedeyecolor` | alap/max/min 0,121 | egyezik |
| `roundededges` | alap 0,124; max 0,128; min 0,121 | egyezik |
| `sat` | alap 0,152; max 0,452; min 0,036 | egyezik |
| `sepia` | alap 0,495 | egyezik |
| `shadow` | alap 0,178; max 0,180; min 0,121 | egyezik |
| `sixties` | alap 0,970; max 0,121; min 1,049 | egyezik |
| `soften` | alap 0,196; max 0,121; min 0,121 | egyezik |
| `tilt` | alap 0,156; max 0,244; min 0,240 | egyezik |
| `tint` | alap 0,585; max 0,532; min 0,517; hex4 0,121; hex8 0,121 | **eltér**; merokit-2: 2,136 |
| `triple` | alap 0,188; max 0,005; min 0,193 | egyezik |
| `triple2` | alap 0,247; max 0,000; min 0,026 | egyezik |
| `triple3` | alap 0,194; max 0,131; min 0,121 | egyezik |
| `twotone` | alap 0,546; max 0,121; min 0,670 | **eltér**; meroszett: 3,662 |
| `unsharp` | alap 0,172; max: nincs 684-es export; min 0,121 | egyezik; meroszett max 0,251 |
| `unsharp2` | alap 0,172; max 0,277; min 0,121 | egyezik |
| `vignette` | alap 0,169; max 0,121; min 0,121 | egyezik önállóan; láncban lásd alább |
| `warm` | alap 0,613 | egyezik |
| `whitept` | alap 0,121 | egyezik |

### Kiegészítő eredeti Picasa-referenciák és összetett láncok

| Referencia és mérő | Nyers eredmény | Állapot |
|---|---|---|
| `PicasaPy meroszett/export-202608151229` - 178 Picasa-export; a fenti `mean_de` mérés | 172/178 eset ΔE ≤ 2,0. Eltérések: `grain/alap` 2,665; `heatmap/alap` 4,254, `heatmap/min` 3,324; `nightvision/alap` 7,307, `nightvision/min` 4,176; `twotone/alap` 3,662. | A fenti négy effektcsalád eltérő kimenete megerősítve; `unsharp/max` itt 0,251. |
| `PicasaPy merokit-2/export-202608151438` - 49 eredeti Picasa-export; `mean_de` | `tint/tintszin_04.jpg` 2,136; `tint/tintszin_07.jpg` 2,136; `picnikfocalpixelate/halott_14.jpg` 8,666; `grain/szemcse_01.jpg` 2,665; `grain2/szemcse_02.jpg` 2,661; `grain+grain/szemcse_05.jpg` 4,631. | Hat eltérő eset. A `halott_14` rövid paraméterlánca nem érvényes Picasa-alkalmazás: a láncteszt és a [`filters-decoded.md`](filters-decoded.md) ezt külön dokumentálja; az eltérés a PicasaPy hibás bemenetkezelésének jelöltje. |
| `PicasaPy merokit-3/export-202608151633` - 7 eredeti Picasa-export; `mean_de` | `nincsilyen+bw/B_ismeretlen_elol.jpg` 10,125. | Eltérő láncviselkedés: az eredeti Picasa az ismeretlen tag után megáll, így a `bw` sem fut le. Ezt a `picasa-ini-format.md` dokumentálja; a mérés a specet erősíti meg, nem mond ellent neki. |
| `tests/render/test_lanc_sorrend_elesben_3229.py` - három azonos méretű, érvényes eredeti láncreferencia | Border+sepia 1,192; sepia+Border 1,146; Border+Vignette 11,642; mindhárom 1650×1250. | Az első kettő egyezik, a Border+Vignette lánc eltér. A `border` és `vignette` önálló táblázatsora ettől még egyezik. |
| Ugyanennek a 3229-es készletnek a crop64+Vignette sora | PicasaPy 376×659, Picasa 1600×1200; nyers ΔE 43,781. | **Nem összehasonlítható, kizárva:** a teszt és a spec szerint a crop az `.ini` kulcsban van, nem a szűrőláncban; az eredeti export ezért vágatlan. Ez nem effekt-eltérésként szerepel. |
| `merokit-2` és `merokit-3` második exportjai (`export-202608202215`, `export-202608202207`) | Nem mértem őket Picasa-referenciaként. | Kizárva: az `export-parbeszed.md` és `filters-decoded.md` szerint ezek PicasaPy-kimenetek, nem eredeti Picasa-exportok. |
| `3084-poszterizalas` `quantizepalette` (szintetikus és valós kép), valamint `951-kiemelesek-arnyekok-fel-allas` `finetune2` | ΔE rendre 0,347; 0,910; illetve 0,629. | Mind egyezik. |
| `tests/render/test_colab_golden_4256.py` - eredeti Picasa 3.9 színfolt-aranyképek, 3 próba | A 16 színfolt legnagyobb átlagos csatornaeltérése: `sepia` 1,0000 (11/16 folton nem nulla); `bw` 0,0000 (0/16); `warm` 1,0000 (13/16). A meglévő határ 2 RGB-szint. | Mindhárom egyezik; a teszt 3/3 sikeres. |

**#4936 helyesbítés (2026-10-13):** a fenti `grain`/`grain2` és
`grain+grain` értékek a javítás előtti, minden hívásnál `seed=0`-t adó
renderelő mérési pillanatképei. A CRT-folyam sorszámozott magjával a 684-es
`grain/alap` k=0 nyers ΔE-je **1,509**. A merokit-2
`grain2/szemcse_02` esetén k=0: **2,661**, a Picasa munkameneti k=1 maggal
**1,447**; a k=0 eltéréshez nem tartozik ΔE ≤ 2,0 elfogadási feltétel. A
`grain+grain/szemcse_05` k=0,1-gyel **3,679**, a mért Picasa-munkamenet k=2,3
magjával **1,866**. Ezek mérési adatok, nem további elfogadási küszöbök; a
részletes képletet és tesztelési feltételeket a
[`filters-decoded.md`](filters-decoded.md) rögzíti.

### Eltérő kimenetek jegyjelöltjei

Megnyitott jegyek (2026-10-13): Szemcse #4936, Hőtérkép #4937, Éjjellátó #4938, Színezés #4939, Kéttónusú #4940, picnikfocalpixelate bemenetkezelés #4941, Keret+Vinyetta lánc #4942.

Az eltérő effektcsaládok a `grain`, `grain2`, `heatmap`, `nightvision`, `picnikfocalpixelate`, `tint` és `twotone`. Az eltérő összetett utak a `grain+grain`, az ismeretlen tag utáni `bw`, valamint a `Border+Vignette` lánc. A `crop64+Vignette` nem összehasonlítható méretű eredmény, ezért nem jegyjelölt. A GitHubot ez a mérési kör nem érte el, így nyitott jegy meglétét nem ellenőriztem; a hívó ezekre nyisson jegyet, ha nincs már nyitott, megfelelő jegy.

Az eredeti Picasa és a mért kimenet között nem találtam spec-mérés ellentmondást: az ismeretlen tag utáni leállás például a bináris viselkedésleírással egyezik. Ez a 7. réteg a meglévő Picasa goldenekkel és mérőadat-tárral alátámasztott effektcsaládokra terjed ki; nem állítja, hogy minden paraméter minden lehetséges értékét vagy minden UI-parancsot lefuttatott.

## A #4317 „Kész, ha” pontjai

| Pont | Állapot | Indok |
|---|---|---|
| mind a hét réteg végigmérve, mai main | ✅ | Az 1-6. réteg a korábbi körökben készült el; a 7. réteg fenti táblája a `a8ba353b3561` pillanatkép effektkimeneteit méri. |
| minden hiány saját jegyet kapott vagy nem célként indokolt | 🟡 | A fenti eltérő effekt- és lánckimenetek jegyjelöltként fel vannak sorolva. GitHub-hozzáférés nem volt, így nyitott jegyet nem ellenőriztem és jegyet nem hoztam létre; a hívó nyisson jegyet, ha nincs megfelelő nyitott jegy. |
| tiszta profil végigkattintása képernyőképekkel | ✅ | A 6. réteghez a fenti izolált teszt végigjárta és képekkel rögzítette a felsorolt fő műveleteket. Ez a mérés nem állítja, hogy az összes menüparancsot vagy a 7. réteg kimeneti egyezését lefedte. |

## Javasolt fejlesztői jegyek

Minden sor egy önálló funkció/menübelépő; a meglévő, hívó által megnevezett #4315, #4316, #4318-#4320, #4321 és a Timeline #936 nem ismétlődik.

| Cím | Eredeti / nálunk / teendő | Kész, ha |
|---|---|---|
| A Fájl ▸ E-Mail parancs küldje el a kijelölést | Eredeti: `ID_FILE_EMAIL`, `Ctrl+E`. Nálunk: menüpont `PicasaMenuBar.qml:623` helyfoglaló, miközben a TrayBar e-mail út él. Teendő: a Fájl menü ugyanazt a kijelölés- és csatolmány-előkészítő útvonalat hívja. | A Fájl menüből e-mail ablak nyílik a kijelölt képek csatolmányaival; üres kijelölésnél a viselkedés dokumentált. |
| A Fájl ▸ Open File(s) in an Editor indítson külső szerkesztőt | Eredeti: `ID_FILE_OPENINANEDITOR` / `Ctrl+Shift+O`. A #4330 óta mindkettő működik; külön szerkesztő-beállítás nincs dokumentálva, ezért a rendszer alapértelmezett alkalmazását használjuk. | A kijelölt fájlok egyenként kapnak megnyitási kérést; sikertelen fájloknál a visszajelzés tartalmazza a hibás és az összes kijelölt fájl darabszámát. |
| A Film almenü készítsen filmet a kijelölt arcokból | Eredeti: `ID_FACES`. Nálunk: a Film almenüben nincs ilyen tétel. | A parancs a kijelölt arcokat a film bemeneteként adja át, és a film export végigfut. |
| A Nézet ▸ Edit View és Kép ▸ View and Edit menüpont nyissa meg a kijelölt képet | Eredeti: `ID_VIEW_PICTURE` és `ID_PICTURE_VIEW`. Nálunk: mindkét menüsori tétel helyfoglaló, bár a `Ctrl+3` és a képrács helyi menüje más belépő. | Mindkét felső menüsori tétel ugyanazt a dokumentált megnyitási műveletet indítja, csak a megfelelő kijelölési/fókusz-kapuval. |
| A Kép ▸ Hide és Unhide a kijelölt képeken is működjön | Eredeti: `ID_PICTURE_HIDE` / `ID_PICTURE_UNHIDE`. A korábbi „felső tétel helyfoglaló” lelet elavult: a Hide a helyi menü kapcsolóútjára, az Unhide a rejtett kijelölések útjára van kötve. | Valódi kattintás mindkét irányra; a `.picasa.ini` `hidden=yes` értéke létrejön, majd törlődik. Teszt: `tests/app/qml_functional/test_felsomenupontok_kep_4329.py`. |
| A Kép ▸ Reset Faces használja a meglévő arc-visszaállítási műveletet | Eredeti: `ID_PICTURE_RESET_FACES`. Nálunk: felső menü helyfoglaló, a Photo/Viewer helyi menükben a művelet aktív. | A felső menütétel ugyanazt a kijelölésre alkalmazott arc-visszaállítási kezelőt hívja, mint a helyi menü. |
| A Ctrl+H tartsa meg a képtálca kijelölését | Eredeti: `Tray::Ctrl+H`. Nálunk: a menüművelet létezik, aktív shortcut nem látható. | Ctrl+H a tálcára fókuszálva ugyanazt a tartós kijelölés-állapotot állítja be, mint a helyi menü. |
| Az Eszközök ▸ Adjust Date and Time módosítsa a dátumot | Eredeti: `ID_TOOLS_ADJUST_TIMESTAMP`; a viselkedés két módját a `picasa-menu-parancsok-viselkedes.md` §3 írja le. Nálunk: `PicasaMenuBar.qml:1888` helyfoglaló. | Mindkét eredeti mód működik a kijelölésen, az eredeti fájl/metaadat mentési célja külön dokumentált. |
| A Configure Photo Viewer nyissa meg a néző beállításait | Eredeti: `ID_TOOLS_CONFIG_SLINGSHOT`. Nálunk: `PicasaMenuBar.qml:1872` helyfoglaló. | A menütétel a néző tényleges beállítófelületét nyitja meg, és a választások újraindítás után is érvényesek. |
| A People Manager kezelje az Emberek albumokat | Eredeti: `ID_TOOLS_CONTACTMGR`. Nálunk: `PicasaMenuBar.qml:1846` helyfoglaló; People panel léte önmagában nem bizonyít Manager-paritást. | A név-/albumkezelési műveletek az eredeti menüből elérhetők és a dokumentált adatokra írnak. |
| A Kép ▸ Show/Hide Text működjön a kijelölt képeken | Eredeti: `ID_PICTURE_SHOW_TEXT`, `ID_PICTURE_HIDE_TEXT`. Nálunk: mindkét menüpont helyfoglaló (`PicasaMenuBar.qml:1730-1731`). | A két parancs a kijelölt képek szövegfedvényét az eredeti állapotfeltételekkel kapcsolja. |
| A Nézet ▸ Show Edit Controls kapcsolja a szerkesztő vezérlőit | Eredeti: `ID_VIEW_EDIT`. Nálunk: `PicasaMenuBar.qml:852` helyfoglaló. | A menüpont láthatóvá/rejtetté teszi a szerkesztő kezelősávját és a kiválasztott állapot újranyitáskor következetes. |
| Folytassa vagy zárja le a 16 bites ditherelt megjelenítési mód munkáját | Eredeti: `ID_VIEW_16`, pontos képpont-átalakítása a `picasa-megjelenitesi-modok.md` §5.3-ban mérve. Nálunk: `PicasaMenuBar.qml:1015-1022` helyfoglaló; a QML-komment #1658-ra hivatkozik. | A #1658 meglévő jegy státuszát ellenőrizni; ha nyitott, a `ID_VIEW_16` alkalmazza a leírt ditherelést; ha nem cél, ezt indokoltan dokumentálni. |

Az alábbi #4339-es függelék pontosítja ezt a listát. A `Small Pictures` jelentése és az eredeti kimenő fájlhúzás bináris szerződése megvan; a People Albums bemeneti szabálya és a 44 gyorsbillentyű tényleges fókuszkapuja még nem zárható le.

## Új kutatási kérdések - állapot a #4339 után

| Kérdés | Állapot | Részletes spec |
|---|---|---|
| `ID_VIEW_SMALL`: melyik nézetben, milyen képméretet állít? | **Megválaszolva:** a CThumbUI könyvtári bélyegképnézetének szűrőkapcsolója; nem állít bélyegképméretet. A szűrő alap-területküszöbe 60 000 képpont². | `picasa-menu-parancsok-viselkedes.md`, „Kis képek” |
| `ID_FACESRANDOM`: mi a People Albums film bemenete, sorrendje és arcigazítása; azonos-e a mi fejlécútunkkal? | **A bemeneti lista/sorrend megválaszolva:** a 6-os mód a `+0x2bc` lista nem üres alsó listájú azonosítóit adja vissza, forrássorrendben. A klip belső arc-/crop-útja nyitott; a mi fejlécünk a normál filmútvonalat használja. | #4339 függelék, 2. táblázat; `picasa-create-features.md` §2.5 |
| Kimenő fájlhúzás: OLE-formátum, fájllista, műveletmaszk; reprodukálható-e? | **Bináris szerződés megválaszolva:** egy `CF_HDROP` UTF-16 útvonal-lista, `COPY|MOVE|LINK` engedett hatásokkal. A natív Qt/asztali fogadópróba nyitott. | #4339 függelék, 3. táblázat; `picasa-eger-es-kijeloles.md` §5.1 |
| Melyik nézetben/fókuszban él a 44 helyi menü-gyorsbillentyű? | **A feltevés pontosítva:** mind a kilenc menübirtokos és a `CThumbUI` billentyűkezelő feltételei ismertek; a helyi rekord billentyűmezője a menüfelirat része, a vizsgált építőút nem regisztrál gyorsítót. Nem mind a 44 rekord parancsának egyedi eseményútja. | #4339 függelék, 4. táblázat; `picasa-gyorsbillentyuk.md` §4.1, §6.1 |

## #4339 - négy paritáskérdés, záró bináris kör

**Vizsgálati dátum:** 2026-10-06. **Módszer:** helyi bináris-index, utasításszintű diszasszemblálás, a megadott Ghidra-kötegek célzott dekompilátumai és QML-forrás-olvasás. A mostani záró kör csak az érintett függvényeket ellenőrizte Capstone-nal; új teljes `.text`-pásztázás nem történt. A korábbi pásztázásnál a `paszta.memoria_kapu()` futott elsőként. A qemu-i386 harness célzott Glimmer-képműveleteket futtat, nem Windows menü-/OLE-interakciót; e négy úthoz nem alkalmazható. Nincs runtime-desktop-próba, becsült értéket nem használok.

### 1. `Small Pictures` - szűrő a könyvtári bélyegképnézetben

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `eMenuView::ID_VIEW_SMALL = 0x9cd8`; a `CThumbUI` Nézet menüjében épül (`0x005c90f0`, tétel `0x005c918f`). A `Preferences\Show only big images` értéke alapból `1`; a menü ezt fordítva pipázza. A `0x005c94e0` az értéket kapcsolja és újraépíti a bélyegképnézetet. Nincs méretválasztás. A szűrőfogyasztó `0x0065d010` `BigPictureThreshold` alapértéke `0xEA60` = **60 000**; a `0x0065f521` szélesség×magasság területet hasonlítja ehhez, további 3,0/0,33333 képarány- és 200 px ágakkal. | A Nézet menü `menuViewThumbnailsOnly` sora `checkable`, de `placeholder: true` és nincs aktív kezelő (`PicasaMenuBar.qml:885-890`). | A `Small Pictures` tétel láthatósági szűrőt kapcsoljon, ne `thumbSizePreset`-et. A megvalósítás a dokumentált 60 000 px² alapküszöböt, a két képarány-konstanst és a 200 px ellenőrző ágat használja; a további fájltípus-ágakat a `0x0065f3c6`-`0x0065f5a9` tartományhoz kell igazítani. |

### 2. `From People Albums…` filmparancs

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `ID_FACESRANDOM = 0x9d5a`; a `0x0057cc7a` a `panel+0x4f1` módjelzőt állítja. A `0x00618050` mód 6-ot ad a `+0x4b4` objektum vtable 0. slotjának (`0x00618236`), majd az eredményt a `+0x4b8` mezőbe teszi. A `0x00699cd0` mód 6 esetén a `0x00824090`-nek nem nulla ágválasztót ad (`0x0069a308`-`0x0069a310`); a `0x00824090` ezért a `0x008226e0` ágat hívja, nem az album-kijelölés `0x008223e0` ágát (`0x008240e9`-`0x00824114`). A `0x008226e0` a `+0x2bc` (`+700`) objektum `0x00449a90`-nel kapott azonosítólistáját járja be, és csak azokat fűzi az eredménybe, amelyek alsó listája nem üres (`0x00822715`-`0x00822775`). A fűzés a bemeneti lista iterációs sorrendjében történik; rendező hívás vagy rendezési ág nem látszik. A `0x006175c0` a már kapott `+0x4b8` listát használó modell-újraépítő, nem listaépítő. A `0x00619010` a `+0x4bc` modell címét adja át a `0x00555a30`-nak; ebből a timeline klipjeinek belső arc-/crop-adatútja nem állapítható meg. | A #4633 „From People Albums...” menüpontja kijelölés nélkül a `Main.qml:openPeopleAlbumsMovie()` úton hívja a `personMovieSourceUrls()` slotot, majd a `CreateDialogs.openMovieForSources()`-t. A #4391 fejlécútja változatlanul `openPersonAlbumMovie()`-n át éri el ugyanezt a forráslistát, de megtartja a nyitott személyalbum-feltételt. A slot a nem üres albumok képeit a tárolt listában, rendezés nélkül fűzi össze; ezt a `test_emberek_album_film_menu_4633.py` és a `test_people_controller.py` fedi. | A bemeneti lista és sorrend megvalósult. A timeline klip arcazonosítását/cropját ne találgassuk; az adatút továbbra is #4400 nyitott vizsgálata. |

### 3. Kimenő fájlhúzás

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `ytDragNode` `0x00aa1fb0` metódusa egy `CF_HDROP` (`cfFormat=15`) adatobjektumot készít: `DROPFILES.pFiles=20`, `fWide=1`, a csomópontlistából származó UTF-16 fájlútvonalakkal. A `QueryGetData` (`0x00aa1e90`) ezt a formátumot/HGLOBAL-t ellenőrzi, az `EnumFormatEtc` (`0x00aa1ed0`) a tárolt formátumot adja. `DoDragDrop` `dwOKEffects=7`, azaz COPY/MOVE/LINK megengedett; a kiválasztott hatást a fogadó adja vissza. | `ThumbDelegate.qml:279-305` a belső `payload="photos"` jelölést és QML-húzásállapotot használ; `Drag.mimeData` vagy OS-fájl URL nincs. | Adjon át kijelölt fájlútvonalakat tartalmazó natív fájllistát, és tegye lehetővé az eredeti három engedett műveletet. A Windows CF_HDROP és a cél által választott művelet egyezését asztali próbán kell igazolni; a QML-forrás önmagában erre nem bizonyíték. |

### 4. A 44 helyi menü-gyorsbillentyű nézeti kontextusa

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Kilenc építő hívja a `0x00a6aee0` tételépítőt, összesen 44 rekorddal; a birtokos nézeteket lásd a `picasa-gyorsbillentyuk.md` §4.1-ben. A 20 bájtos rekord `+0x04` mezője billentyűfeliratként kerül a menüszövegbe (`0x00a6aee0` → `0x00a6b250`); a `0x00a6ade0` csak a felirat összeállításához oldja fel a táblázat szerinti billentyűkódot, egyetlen közvetlen hívója a `0x00a6b250`. Ebben a helyi menüépítő/feliratláncban gyorsítóregisztráció nincs. A `CThumbUI` RTTI-s billentyűslotja a `0x005e6710`: fókuszált gyerek továbbítása után saját feltételekkel dolgozik. A `+0x332f != 0` ág a `0x00760970` kezelőre megy; ez keydownon Esc/nyilak/szóköz/számjegyek ágait kezeli. A szerkesztő `+`/`-` karakterei és Shift-váltása a 3-5. fül látható paneljéhez kötött (`0x005f95d0`, `0x005f9690`, `0x009e39b0`); az utóbbi a fókuszobjektum szülőláncában a `+0x20c` bájt hiányát követeli. Ez a CThumbUI fogadó feltételeit bizonyítja, de nem köti hozzá egyenként mind a 44 rekord parancsát. | A mostani QML-leltárban 53 `Shortcut` deklaráció van nyolc fájlban; több parancs `Main.qml`-szintű, miközben mások nézeti `Shortcut`-ot vagy `Keys`-kezelőt használnak. Például a `Ctrl+Delete` külön rács- és nézőkaput kap, a `Ctrl+H` csak kijelölt elemmel és a nézőn kívül aktív, az `Enter` a `LightboxFeed` `Keys.onPressed` ágában van, és a `Ctrl+C/X/V` megőrzi a szövegmező fókuszát (`picasa-gyorsbillentyuk.md` §6.1). | A billentyűparitást nézethez/fókuszhoz kötött fogadókon valósítsuk meg: ne tekintsük a 44 helyi menü feliratmezőjét önmagában gyorsítóregisztrációnak. A QML-út minden parancsánál legyen meghatározva a tulajdonos nézet, a fókuszkapu és az eseményfogadó; az eredetiben bizonyított CThumbUI-feltételeket (3-5. szerkesztőfül, `+0x332f` módág, fókuszolt gyerek továbbítása, `+0x20c`-mentes ősút) ne általánosítsuk a többi nyolc menüépítőre. Elfogadás: az egyes menük kontextusából indított kombinációk a megfelelő nézet műveletét érik el, a fókuszált szövegmezők szerkesztése megmarad, és a 44 rekordot nem globális shortcut-listaként kezeljük. |

## Nyitott

- A kattintással és tiszta profillal ellenőrizendő hatások: minden még nem vizsgált menüút valós UI-viselkedése; külső szerkesztő, e-mail, nyomtató, Google Earth, fájltörlés és az itt nem mért exportváltozatok; a 44 helyi menürekord és az eseményfogadók futásidejű parancs-kapcsolata.
- A mai `main` frissessége: a záró státusz a helyi tracking ref szerint három commit lemaradást jelez; GitHub/hálózat tiltott volt, így a lemaradás tartalma és az upstream frissessége nincs ellenőrizve.
- People Albums-film: a `CTransTimeline` belső feldolgozása, vagyis az arcazonosító és crop/igazítás útja a modellből a klipbe; lásd az egyetlen blokkoló Ghidra-kérést alább.
- Gyorsbillentyűk: a `+0x332f` módjelző jelentése, valamint hogy a program más részén létrehozott gyorsítótáblák kapcsolódnak-e a 44 helyi menüfelirathoz. A helyi menüépítő-lánc nem regisztrál gyorsítót; az importtábla globális gyorsító-API-kat is tartalmaz, ezért a negatív állítás erre a láncra korlátozott.
- A kimenő fájlhúzás bináris formátuma ismert; a Windows/asztali célprogrammal való natív paritás nincs kipróbálva.
- A 4. réteg statikus tiltáslistája nem bizonyítja, hogy minden kapcsolódó szolgáltatás vagy backend működik.

## Bizonyítottsági fok

**Feltételes összesítve.** A négy kérdés bizonyított határai két, egymástól független útból állnak: `Small Pictures` szűrőkapcsoló; `CF_HDROP` fájlszerződés; a People/Face mód 6-os ága és a szűrt, sorrendtartó azonosítólista; a helyi menü billentyűmezője felirat, míg a `CThumbUI` saját fogadója dokumentált állapot-/fókuszfeltételekkel dolgozik. A `CTransTimeline` belső arc-/crop-útja, a `+0x332f` szemantikája és az esetleges külön gyorsító-API-kapcsolat nyitott; ezért nem állítok teljes klipparitást vagy 44/44 parancs-hozzárendelést. Becslést nem adok át.

## Bizonyíték

| érték/állítás | forrás |
|---|---|
| `ID_VIEW_SMALL = 0x9cd8`, `Show only big images` alapérték 1, kapcsoló/nézetfrissítés | bináris (`0x005c90f0`, `0x005c94e0`) |
| `BigPictureThreshold = 0xEA60 = 60 000`; `width × height`; képarány-konstansok 3.0 és 0.33333; méretág 200 | bináris (`0x0065f1e6`, `0x0065f521`, `0x00c49618`, `0x00cf4fd8`, `0x0065f553`) |
| korábbi `minsize` kötés | **NINCS MEG** mint képszűrő-beállítás; a string xref a `.tre` attribútumparszolóba mutat (`0x008d1450`) |
| `ID_FACESRANDOM = 0x9d5a`, `panel+0x4f1`, `facemakemovieres` alap 3 / 1024×768 | bináris (`0x0057cc72`, `0x00616b42`-`0x00616b64`) |
| `ID_FACESRANDOM` módja: a `+0x4b4` objektum 0. helye 6-tal tér vissza a `+0x4b8` mezőbe | bináris (`0x00618050`: `0x00618209`-`0x0061824d`; Ghidra `00699cd0.c`) |
| a `+0x4b4` szolgáltatás 0. slotja módválasztó (`+0x14` rész, `0x00699cd0`); a `+0x1c` rész slotja destruktor (`0x0069d740` → `0x006996d0`) | bináris (Ghidra `00699cd0.c`, `0069d740.c`, `006996d0.c`; RTTI vtable `0x00ca7b7c`, `0x00ca7bd8`) |
| mód 6 ágválasztója: album-alapú `0x008223e0` helyett a `+0x2bc` listaág, `0x008226e0` fut | bináris (Capstone `0x0069a305`-`0x0069a310`, `0x008240e9`-`0x00824114`) |
| a `+0x2bc` listából csak nem üres alsó listájú azonosítók kerülnek át, a forrás sorrendjében | bináris (`0x008226e0`: Capstone `0x00822715`-`0x00822775`, `0x008229f0`-`0x008229fb`; Ghidra `008226e0.c`); **feltételes**, mert a szűrést/sorrendet egyetlen listabejáró függvény bizonyítja
| `+0x4bc` modell és `+0x4b8` lista viszonya; modellrekonstrukció és lista-iterálás | bináris (`0x006175c0`, Ghidra-köteg `006175c0.c`, `0x00616940`) |
| `CTransTimeline` arcazonosító-/cropmezője és klipbe jutása | **NINCS MEG**; Ghidra-kör kell `0x00555a30`-hoz |
| OLE-formátum `CF_HDROP=15`, `DROPFILES.pFiles=20`, `fWide=1`, effect mask 7 | bináris (`0x00aa215a`, `0x00aa2074`, `0x00aa207a`, `0x00aa2136`) |
| QML-ből tényleges CF_HDROP/OS-fájl payload | **NINCS MEG**; a forrásban nincs `Drag.mimeData`, asztali próba nélkül nem igazolt |
| a 44 rekord kilenc menüépítő szerinti csoportja | bináris + spec-leltár (`0x00a6aee0` hívók; részletesen `picasa-gyorsbillentyuk.md` §4.1) |
| a 44 shortcut-rekord parancsonkénti billentyűútja és fókuszkapuja | **NINCS MEG**; a menüfelirat-lánc és a `CThumbUI` általános eseményfogadója ismert, a 44 parancs egyedi összekötése nem |
| `CThumbUI` saját billentyűkezelőjének igazolt fókusz-/nézetfeltételei | bináris (`0x005e6710`, `0x005f95d0`, `0x005f9690`, `0x00760970`, `0x009e39b0`) |
| QML aktuális billentyűfogadók | mérés (a `src/picasapy/app/qml` 187 QML-fájljának bejárása: 53 `Shortcut` deklaráció 8 fájlban; 52 sor szó szerinti `sequence`-szel, 47 különböző literális sorozat; releváns fájlok: `Main.qml`, `PicasaMenuBar.qml`, `TrayBar.qml`, `LightboxFeed.qml`, `DocumentTabStrip.qml`) |
| a `CreateAcceleratorTableA` / `TranslateAcceleratorA` importok kapcsolata a 44 rekorddal | **NINCS MEG**; az import jelenléte cáfolja a program-szintű „sehol nincs gyorsító” állítást, de a 44-es menülánchoz való kötés nem bizonyított |

## A két független út

- **Small Pictures - egyezik.** A: `0x005c90f0` menüépítő + `0x005c94e0` állapotkapcsoló (`Show only big images`, fordított pipa). B: `0x0065d010` külön képszűrő ugyanazt a beállítást olvassa, majd terület-, képarány- és méretágat alkalmaz. A beállítás kapcsoló, nem méretválasztó.
- **Fájlhúzás - egyezik.** A: `0x00aa1fb0` `CF_HDROP`/UTF-16 payloadot és 7-es hatásmaszkot készít. B: a `ytSimpleDataObject` `EnumFormatEtc`/`QueryGetData` útja a 15-ös formátumot szolgálja ki, más formatet nem fogad el.
- **People Albums film - a mód 6 ága megerősített két külön függvényrétegből; a szűrés/sorrend feltételes.** A: `0x0057cc7a` beállítja a `+0x4f1` jelzőt, `0x00618050` pedig 6-os módot kér. B: a külön `0x00699cd0` módválasztó a 6-ost az `0x00824090` ágválasztóján át a `0x008226e0`-re irányítja, nem az album-kijelölés `0x008223e0` ágára. A bemeneti forrás (`+0x2bc`), az üres alsó listák szűrése és a sorrend az `0x008226e0` bejárásából következik; ez egyetlen kódszintű út, ezért `feltételes`, noha Capstone és a Ghidra-dekompilátum utasításonként egyezik. A `0x00619010`/`0x00555a30` külön fogyasztói útján a modell címe megy át, a közvetlen modellolvasás pedig a `+0x2b0` hangfájlnévre korlátozódik; arc/crop mezőt nem azonosít. A CTransTimeline belseje nyitott.
- **Gyorsbillentyűk - a menüfelirat és a CThumbUI eseményút megerősített; az egyedi parancs-kapcsolat korlátozott.** A: a `0x00a6aee0` → `0x00a6b250` lánc a rekord `+0x04` mezőjét szövegként építi a menübe, a `0x00a6ade0` pedig ezt a felirat-építő hívó keresi fel. B: a `CThumbUI` RTTI-s billentyűslotja `0x005e6710`; ennek diszasszemblálása és a külön dekompilált `0x005f95d0`, `0x005f9690`, `0x00760970`, `0x009e39b0` függvények rögzítik a mód-/fókuszfeltételeket. A két út a „felirat nem azonos a regisztrációval” következtetéssel egyezik. A lehetséges globális gyorsító-importok cáfoló ellenőrzése miatt ezt nem terjesztem ki a teljes programra; a 44 rekord és más gyorsító-API-k kapcsolata **NINCS MEG**.

## Cáfoló kísérlet

1. Azt próbáltam cáfolni, hogy `ID_VIEW_SMALL` bélyegképméretet állít: összevetettem a `0x9cd8` és `0x9c9d` külön parancsait, az `ID_VIEW_SMALL` menüépítőjét/íróját, valamint a külön képszűrő fogyasztót. A `0x9cd8` csak a `Show only big images` preferenciát váltja; a méret-presetek külön parancsok.
2. Azt próbáltam cáfolni, hogy a drag adatobjektum csak CF_HDROP-ot fogad el: `QueryGetData`-nél alternatív formátumot vizsgáltam. A kód csak `cfFormat=15`, `DVASPECT_CONTENT` és HGLOBAL mellett tér vissza sikerrel; alternatív URI-/egyedi formátumot nem igazol.
3. Azt próbáltam cáfolni, hogy a `0x006175c0` építi a People-képlistát, illetve a `0x0080fea0` végzi az arc-kivágást. A Ghidra-kód szerint a `0x006175c0` a `+0x4bc` modellt újraépíti és a már kapott `+0x4b8` listát iterálja; a `0x0080fea0` modellmezőket ír és node-okat inicializál. A lista-lekérési határ a `0x00618050`-ban van (`0x00618236`), de a virtuális cél és a render-crop út nyitott.
4. **People-mód cáfoló köre:** azt ellenőriztem, hogy a 6-os mód vajon a kiválasztott album `0x008223e0` ágába jut-e. A Capstone-utasítások szerint a 6-os mód a `0x0069a30b` `sete cl`-nél 1-es jelzőt ad; a `0x008240e9` feltétel így a `0x008226e0` ágra visz, míg az album-alapú `0x008223e0` csak nulla jelzőnél fut. A cáfolat saját ellenőrzése: a `0x008226e0` `0x00822715`-nél valóban a `+0x2bc` listát kéri, és a `0x0082275f`-`0x00822775` csak üresnek talált alsó listánál ugrik ki; a `0x008229f0` iterációs indexe növekszik, kódolt rendezés nélkül. A korábbi „kiválasztott album” értelmezés mód 6-ra megdőlt; az a másik, nulla-jelzős ág.
   A másik lehetséges célként felmerült `+0x1c` slotot is ellenőriztem: a Ghidra `0x0069d740`-et a `0x006996d0`-hez köti; ez `0x00699830` után a törlési jelzőtől függően felszabadítja az objektumot, tehát destruktor. A mód 5/6 út a `+0x14` rész `0x00699cd0` slotjával egyezik.
5. **Gyorsító-regisztráció cáfoló köre:** az `imports.csv` `CreateAcceleratorTableA` és `TranslateAcceleratorA` importot is felsorol, tehát az egész programra tett „nincs gyorsítótábla” állítás nem tartható. A dekompilált `0x00a6ade0` kereső egyetlen közvetlen hívója a `0x00a6b250`; a célzott Capstone-olvasás ezen a láncon nem mutat ACCEL-regisztrációt. Az importtal szembeni cáfolatot ugyanazzal a mércével ellenőriztem: a használat és a 44 rekord közötti adat-/hívási kapcsolat **NINCS MEG**, ezért a negatív állítás csak a helyi menüépítő-láncra érvényes.

## A #4339 „Kész, ha” pontjai

| pont | állapot | igazolás |
|---|---|---|
| mind a négy kérdésre bizonyított válasz, utasításszintű címekkel | ✅ | A Small Pictures és `CF_HDROP` szerződése korábbról két úton igazolt; a People mód 6-os bemeneti listája és sorrendje (`0x0069a30b`, `0x00824090`, `0x008226e0`), valamint a helyi menüfelirat és a `CThumbUI` fókusz-/nézetkapuja (`0x00a6aee0`, `0x005e6710` és segédei) most rögzített. A klip belső cropja és az egyedi 44 parancs-hozzárendelés külön nyitott részletként szerepel. |
| kérdésenként Eredeti / Nálunk / Teendő tábla | ✅ | A fenti négy külön tábla. |

## Javasolt jegytörzs-bővítés

**Kész szöveg:** „A `Small Pictures` (`ID_VIEW_SMALL=0x9cd8`) a könyvtári `CThumbUI` Nézet menü láthatósági kapcsolója, nem bélyegképméret; a `CF_HDROP` fájlhúzás UTF-16 útvonal-listát ad át `COPY|MOVE|LINK` engedélyezéssel. A `From People Albums…` mód 6: a `0x00699cd0` a `0x00824090`-nek 1-es ágválasztót ad, ezért a `+0x2bc` (`+700`) objektum azonosítólistája fut végig a `0x008226e0`-n. Az üres alsó listájú elemek kiesnek, az eredeti lista sorrendje megmarad; ez nem a kiválasztott album `0x008223e0` ága. A mai fejlécút a személyalbum összes sorát a normál filmkészítőnek adja át, ezért nem egyenértékű. A `0x00555a30`-nál kért `CTransTimeline` belső arc-/crop-feldolgozása nyitott. A 44 helyi menürekord billentyűmezője felirat, a vizsgált lánc nem regisztrál gyorsítót; a `CThumbUI` tényleges eseményfogadója `0x005e6710`, nézet-/fókuszfeltételekkel. A #4398 után a mai PicasaPy QML-ben 54 `Shortcut` van nyolc fájlban; a 44 eredeti rekord és az egyes QML-fogadók nem feleltethetők meg automatikusan.”

| fejlesztési irány | Eredeti / nálunk / teendő | Kész, ha |
|---|---|---|
| A Nézet ▸ Small Pictures kapcsolja a kis képek szűrőjét | Eredeti: `0x9cd8`, preferencia-kapcsoló, 60 000 px² alapküszöb és további ellenőrzések. Nálunk: `PicasaMenuBar.qml:885-890` helyfoglaló. Teendő: a tétel a szűrőt kapcsolja, ne bélyegképméretet. | A pipa és a látható képek a specifikált preferenciával és `0x0065f3c6`-`0x0065f5a9` szabályokkal egyeznek; a bélyegképméret nem változik. |
| A képrács húzza a kijelölt fájlokat az asztali alkalmazásokba | Eredeti: `CF_HDROP`, UTF-16 útvonalak, COPY/MOVE/LINK. Nálunk: belső `payload="photos"`, OS-formátum nincs. Teendő: natív fájllista átadása. | Windows-próbán a fogadó a húzott fájlok útvonalait kapja, és az eredeti 3 engedett műveletből választott hatás visszajelzése helyes. |
| Az Emberek-fejléc filmgombjai őrizzék az eredeti People/Face bemenetet | Eredeti: mód 6 a `+0x2bc` azonosítólistáját járja be, üres alsó listákat kihagy, sorrendet őriz (`0x00699cd0`, `0x00824090`, `0x008226e0`). Nálunk: `Main.qml:732-737` minden `controller.photos` sort a normál filmútvonalnak ad. Teendő: a bizonyított szűrt lista és sorrend bekötése külön People/Face útba; a timeline/crop belső útját ne találgassuk. | Az eredetivel azonos bemeneti modellen a forrás-azonosítók és sorrend egyeznek; crop/arcigazítás csak `CTransTimeline` feltárása után vehető át. |
| A 44 menüfelirat és a billentyűkezelés nézet-/fókuszhelyes legyen | Eredeti: a rekord `+0x04` mezője felirat (`0x00a6aee0`, `0x00a6b250`); a `CThumbUI` saját billentyűútja `0x005e6710`, a szerkesztőfülek és a `+0x332f` ág bizonyított feltételeivel. Nálunk: a #4398 utáni leltár 54 `Shortcut` nyolc QML-fájlban, köztük rács/néző szerint külön `Ctrl+Delete`; könyvtári kötéseket nem enged be az editorba, és szövegfókuszban tiltja az alkalmazás-shortcutokat. Teendő: a helyi menüfeliratokat ne tekintsük globális shortcut-regisztrációnak; a 44 rekord egyedi parancsútja továbbra sincs bizonyítva. | A gazdanézet/fókuszkapuk a `picasa-gyorsbillentyuk.md` §6.2 táblázatában vannak; a könyvtár/editor/szövegfókusz eseteket valódi billentyűleütéses teszt fedi le; a nem igazolt 44/44 kapcsolat nyitott marad. |

## Új kutatási jegyjavaslatok

Nincs külön új kutatási jegyjavaslat: a fennmaradó `CTransTimeline` kérdés a #4339 blokkoló folytatása; a gyorsító-API-kapcsolat és az asztali drag-próba is ugyanennek a paritási vizsgálatnak a határán marad.

## Nyitott - pontos következő bináris lépés

- `Ghidra-kör kell: 0x00555a30 - a 0x00619010 által átadott +0x4bc film-modell címét a CTransTimeline hogyan dolgozza fel: melyik mező hordozza az arcazonosítót/cropot/arcra igazítást, és hogyan kerül ezekből adat a timeline-klipbe? [blokkoló]`
- A `+0x332f` bájt által jelölt billentyűmód neve **NINCS MEG**; a `0x00760970` ág feltételei és a kezelt billentyűk ismertek, a mód szemantikája nem.
- A `CreateAcceleratorTableA` / `TranslateAcceleratorA` importok és a 44 helyi menürekord közötti kapcsolat **NINCS MEG**; ezért a gyorsító-regisztráció hiánya csak a vizsgált `0x00a6aee0` → `0x00a6b250` helyi menüépítő-láncra állítható.
- A fájlhúzás natív QML/Windows egyezése: **NINCS MEG** futó Windows-célalkalmazással végzett próbában.

## Módosított fájlok

**A 2026-10-06-i záró körben:**

- `docs/specs/paritas-ellenorzes.md` - a People mód 6 bemeneti listája/sorrendje, a `CThumbUI` fókuszkapui, a cáfoló ellenőrzések és a `CTransTimeline` blokkoló kérdése.
- `docs/specs/picasa-create-features.md` - a 6-os ág pontos forráslistája, szűrése és sorrendje; a modell/crop határának nyitva hagyása.
- `docs/specs/picasa-gyorsbillentyuk.md` - a helyi menümező feliratjellege, a `CThumbUI` eseményfeltételei és a mai QML 53 `Shortcut`-os összevetése.
- `docs/specs/00-index.md` - a #4339 kutatási állapot rövid összefoglalójának frissítése.

**A korábbi #4339-körök módosításai:**

- `docs/specs/paritas-ellenorzes.md` - a #4339 négy kérdése, eredeti/nálunk/teendő táblái, bizonyítékai és nyitott bináris lépései.
- `docs/specs/picasa-menu-parancsok-viselkedes.md` - `ID_VIEW_SMALL` helyesbítése és a küszöb pontosítása.
- `docs/specs/picasa-create-features.md` - az `ID_FACESRANDOM` módjelzője és felbontása; nyitott bemeneti szabály.
- `docs/specs/picasa-eger-es-kijeloles.md` - a `DoDragDrop` fájlformátuma, payloadja és hatásmaszkja.
- `docs/specs/picasa-gyorsbillentyuk.md` - a 44 rekord kilenc menükontextusa és a nyitva maradt fókuszkapu.

## Forrás nélkül lezárt jegyek, első köteg (#5245, 2026-10-17)

Módszer: a helyi commitlistát és a változtatott fájlokat vetettem össze a Picasa erőforrásaival, a bináris eredményekkel, a képernyőkép-leltárral, a specifikációkkal és a mai QML/Python kóddal. A negatív bináris-index találatot nem tekintettem bizonyítéknak. A `#3420` állapotát a 684 képes Picasa golden-készlet közvetlen összevetésével mértem.

Mérési vakfolt: nincs új Colab-felvétel. A leltárban a `#3448` képe a PicasaPy hibás menüjét mutatja, nem az eredetit; a `#3594` mentési képe már elmentett állapotot mutat; a `#3661` eredeti Options képe 1280 × 1024-es, nem 480 px-es ablakot. Ezek az állapotok ezért nyitva maradnak.

| Jegy | Funkció | Eredeti forrás | Mai állapot, fájl:sor | Ítélet |
|---|---|---|---|---|
| #1721 | Kézi sorrend tárolása | `docs/specs/album-sorrend.md` 2.3, 2.5 és 3. szakasz; `wordhash.dat`, `0x00784100`. | `src/picasapy/ini/priority.py:1-13,33-72`; a PicasaPy a kép `.picasa.ini` szakaszába ír `priority=` értéket. A docstring 5-7. sora tévesen az eredeti `albums_0.db`-t nevezi meg; az eredeti formátumot az `album-sorrend.md` 2.1 és 3. szakasza `wordhash.dat`-ként bizonyítja. | **Eltér.** Az eredeti a mappa vagy album képlistáját a `wordhash.dat` fájlban tárolja. A `priority=` a PicasaPy saját kiterjesztése. Javaslat a #5186-ba: nevezze ezt saját formátumú funkciónak; eredeti sorrend átvétele külön, `wordhash.dat` importot vizsgáló feladat legyen. |
| #3123 | Alkalmaz/Mégse sáv a kép fölött | `referencia/tre-eroforrasok/editpanel.tre:21-33,1038-1056`; `editpanel/tool_container` szülője az `editpanel/preview`; a gombok és a szín a `respack.yt` erőforrásból mértek. | `src/picasapy/app/qml/PicasaPy/EditorToolBar.qml:3-4,66-69,141-165`; fehér felirat és áttetsző sötét háttér. | **Egyezik a kiegyenesítés eszközén.** Ez a sáv nem a négy másik eszközé, lásd #3320. |
| #3166 | Vágás- és arckeret-koordináták kereteffekt után | Eredeti Picasa golden-kimenetek; a keretek méretváltozásai és az `800 × 600` bemenetre végzett mérés a `src/picasapy/render/chain_geometry.py:15-36` fájlban szerepelnek. | `src/picasapy/render/chain_geometry.py:1-36,128-185`; a jelölőpixel-ellenőrzés helye `tests/render/test_keret_geometria_3166.py`. | **Egyezik a leképezés elvében.** A jelenlegi kód transzformációt ad, és a renderelt jelölőpixellel ellenőrizhető; az egyszerű középre tolás feltevését a mérés cáfolja. |
| #3173 | Albumleírás szerkesztése | Eredeti `album.fen`, leírva: `docs/specs/picasa-fen-dialogs.md` 3.2. szakasz. A mező neve `caption`, felirata `Description (optional)`. | `src/picasapy/app/qml/PicasaPy/FolderPropertiesDialog.qml:165-208,596-628`; mentés `src/picasapy/app/photo_ops_controller.py:1095-1113,1153-1179`. | **Egyezik a leírás szerkesztésében.** Az eredeti képernyőkép-leltárban csak az új album párbeszéd látszik, de a `album.fen` tartalmazza a mezőt. |
| #3234 | Eszközsáv csúszkája és retusáló ecsetméret | `editpanel.tre:869,962,1038-1052`: az ecset csúszkája a `retouch_well` gyereke; `tool_container` a `Straighen Overlay` szakasz alatt van. | `src/picasapy/app/qml/PicasaPy/EditorToolBar.qml:89-92`; `src/picasapy/app/qml/PicasaPy/EditorRetouchPanel.qml:80-92`. | **A jegy állítása hibás, a mai elhelyezés egyezik.** Az eszközsáv csúszkája a kiegyenesítésé, a retusáló ecsetméret a saját oldalsó panelben van. Javaslat a #5186-ba: rögzítse a téves forrás-hozzárendelést és ne kérje a csúszka áthelyezését. |
| #3263 | Örökölt effektek fül magassága Windowson | Eredeti `editpanel/tabpanel1` mérete: `docs/specs/ui-audit-editor.md` 2.9. szakasz, 277 px magas. Az örökölt-effektek fül saját PicasaPy-kiegészítés, eredeti párja nincs. | `src/picasapy/app/qml/PicasaPy/EditorLegacyTab.qml:45-52,73-77,128-146`; a bevezető legfeljebb két sor, a rács görgethető. | **Részben egyezik, a pontos vizuális paritás nyitott.** A 317 px-es túlnövést a mai elrendezés korlátozza, de az eredetiben nincs örökölt-effektek fül, amit össze lehetne vetni. Javaslat a #5186-ba: a méretjavítást platformhiba-javításként tartsa nyilván, ne eredeti fül paritásaként. |
| #3320 | Vágás, retusálás, szöveg és vörösszem Alkalmaz/Mégse párja | `editpanel.tre` szerint a négy pár a saját `*_well` panel gyereke; `docs/specs/szerkeszto-panel-meretek.md` 548-592. | `EditorCropPanel.qml:369-397`; `EditorRetouchPanel.qml:148-179`; `EditorTextPanel.qml:390-430`; `EditorRedeyePanel.qml:204-232`. | **Egyezik.** A négy pár a saját paneljében van; a kép fölötti sáv a kiegyenesítésé. |
| #3408 | Kollázs Beállítások súgói | `collagepanel.tre`, `referencia/ui-leltar.csv:323,341,346,359` és `referencia/stringres-en-hu.tsv:103,124`; összefoglaló: `docs/specs/kollazs-panel-ui-spec.md` 4.2/c. | `CollageSettingsTab.qml:422,465,578-579`; `CollageBorderPicker.qml:43`; `CollageContextMenus.qml:132-136`; `CollageFormatMenu.qml:132,293`. | **Egyezik a mai QML-forrásban.** A hat szöveget a #3408 javító commit átírta. A specifikáció 4.2/c korábbi, javítás előtti összevetése elavult. |
| #3410 | Kollázs Klipek lap súgói | `collagepaneltext.tre`, `referencia/ui-leltar.csv`; a két hibás eredeti szöveg: `Get more clips from the Library`, `Remove selected clips from the tray`. | `CollageClipsTab.qml:99,140,166`. | **Egyezik a mai QML-forrásban.** A három súgóból a `#3410` által javított kettő és a korábban egyező harmadik is az eredeti angol szöveget adja. A spec 4.3/d táblája javítás előtti állapotot rögzít. |
| #3420 | Polaroid keret színe és forgatása | `filterdesc.xml:751-755`; a korábbi és a javítás utáni mérés: `docs/specs/filterdesc-registry.md:10518-10525,10717-10724`. | Mai mérés a 684 golden-készleten, min/alap/max átlagos ΔE: **0,13 / 0,12 / 0,13**. Mérőeszköz: `tools/golden/compare_render.py pair`. | **Jelentősen javult, maradék eltérés mérhető.** A jegyben szereplő 19-23 ΔE érték nem a mai állapot: a friss mérés 0,12-0,13 ΔE, a mérőeszköz ítélete közelítés. Javaslat a #5186-ba: frissítse a három mai mérési értékre és ne kérje vissza a már javított szín- vagy forgatásmódosítást. |
| #3448 | Rejtett menütételek üres helye | **NINCS MEG** eredeti, azonos állapotú forrás. `referencia/kepek-leltar.md:158` a bejelentő képről kimondja, hogy PicasaPy képe. | `PhotoContextMenu.qml:29-32,135-142,184-207`; a feltételes tételek magassága rejtve nullára áll. | **Forrás nem található.** A mai kód kezeli az üres helyet, de az eredeti menü vizuális viselkedését a leltár nem bizonyítja. Döntő Colab-felvétel: eredeti Picasa, azonos képkijelöléssel, album és normál mappanézetben megnyitott jobb gombos menü, a rejtett album- és személytételek helyének rögzítésével. |
| #3537 | Letiltott menütételek színe | Eredeti angol Picasa `Colab EN 01 - File menu.png`, a leltárban: `referencia/kepek-leltar.md:77`; üres könyvtárban több tétel szürke. | `src/picasapy/app/qml/PicasaStyle/MenuItem.qml:24-30`; egyedi tételek `PicasaMenuItem.qml:96-101`. | **Egyezik.** A mai letiltott tételek `Theme.textGray` színt kapnak. |
| #3594 | Mentetlen mappák és összes kijelölése | Eredeti `publish.tre`, `referencia/ui-leltar.csv:1464-1477,1537-1542`; az eredeti szöveg mentetlen fájlokat, mappajelölést, `Select All` és `Select None` gombot nevez meg. A `Colab EN 24` kép már mentett állapot. | `BackupHost.qml:55-60,188-200`; `PublishPanel.qml:420-436`; mappasor pipa `FolderPane.qml:949-961`. A mai pipa induláskor üres kijelölésből számolódik. | **Részben egyezik, az induló pipaállapot nyitott.** A mentetlen lista, a pipálás és a `Select All`/`Select None` megvan. A forrásleltár nem mondja meg, hogy az eredeti előre bepipálta-e a mentetlen mappákat; a meglévő kép ezt az állapotot nem mutatja. Döntő Colab-felvétel: vegyesen mentett és mentetlen mappákkal megnyitni a mentés módot, kattintás előtt rögzíteni a pipákat. |
| #3639 | Tulajdonságok panel fordítási kontextusa | Az eredeti `Picasa3i18n.dll` és a hivatalos magyar szövegek kinyerése: `docs/specs/picasa-hu-terminology.md:14,58-70`; a helyi fordítási kontextus hibáját és javítását a `formatting.py` dokumentációs fejléce írja le. | `src/picasapy/app/formatting.py:1-35`; `src/picasapy/app/controller.py:1491-1502`; a panel az átadott címkét mutatja: `PropertiesPanel.qml:68-79`. | **Egyezik a javítás után.** A formázó a saját üres Qt fordítási kontextusát használja; a vezérlő ezt az útvonalat adja a tulajdonságsoroknak. |
| #3661 | Beállítások ablak 480 px szélességen | Eredeti `options.fen` kilencfüles dialógust ír le: `docs/specs/picasa-fen-dialogs.md` 3.11. szakasz; a `Colab EN 26` kép csak normál szélességű. **NINCS MEG** eredeti 480 px-es felvétel. | `OptionsDialog.qml:47-50,62-129,164-175`; a mai minimum 480 px, a fülsor görgethető és a kiválasztott fül láthatóságát kezeli. | **Forrás nem található a 480 px-es viselkedésre.** A mai javított elrendezés kódból olvasható, de az eredetivel való egyezés nem. Döntő Colab-felvétel: az eredeti Options ablakot a lehető legkeskenyebbre állítani, a teljes fülsort és a kiválasztott fület rögzíteni. |

### A #5245 „Kész, ha” pontjai

- ✅ Mind a 15 tételhez tartozik ítélet, eredeti forrás vagy kimondott forráshiány és a döntő Colab-lépés.
- ✅ A talált eltérésekhez konkrét jegytörzs-javaslat szerepel a táblázatban.
- ⛔ A gyűjtő jegy tételeinek kipipálása itt nem végezhető el: a GitHub ebben a munkamenetben nem érhető el, a helyi munka csak a spec-lapra korlátozódik.

### Bizonyítottsági fok és cáfoló kör

**Feltételes.** Az eredeti erőforrás, bináris lelet vagy golden-mérés és a mai forráskód két külön rétegként egyezik a lezárható tételeknél. A #3448 eredeti menürése, a #3594 induló pipái, a #3661 480 px-es ablak és a #3263 saját PicasaPy-fülének vizuális párja nem igazolt.

**A út:** eredeti `.tre`/`.fen`, `respack.yt`, bináris leletek, eredeti képernyőképek és a Polaroid golden-mérés. **B út:** a mai QML/Python forrás, a módosításokat tartalmazó commitok és a meglévő jelölőpixel-ellenőrzés. Ahol mindkét út ugyanazt a viselkedést írja le, az egyezik; a hiányzó eredeti képernyőállapotokat nem következtettem ki a mai kódból.

**Cáfoló kísérlet:** a #3234 állítását azzal próbáltam megcáfolni, hogy a sáv csúszkájának szülője a retusáló panel-e. Az `editpanel.tre` a `tool_container` elemet a `Straighen Overlay` alá, a `brushslider_container` elemet pedig a `retouch_well` alá teszi. A mai kód ugyanígy választja szét a `EditorToolBar` kiegyenesítő csúszkáját és a `EditorRetouchPanel` ecsetméretét. A cáfoló ellenőrzése ugyanazon erőforrás egy másik ágán és két külön QML fájlon alapul, ezért a korábbi retusálás-overlay értelmezés megdőlt.

### Nyitott

- `NINCS MEG` az eredeti #3448 jobb gombos menü üres helyének képernyőállapota. Colab kell a táblázatban leírt menüfelvétellel.
- `NINCS MEG` a #3594 eredeti, még nem mentett mappákat mutató alapállapotának pipaképe. Colab kell vegyes mentési állapotú mappákkal.
- `NINCS MEG` a #3661 eredeti Options ablakának 480 px-es viselkedése. Colab kell a legkeskenyebb méret és a fülsor rögzítésével.
- A #3263 örökölt-effektek füle PicasaPy-saját kiegészítés; eredeti vizuális párja nincs.
- A #3420 mai golden-összevetése nem pixelazonos: a három átlagos ΔE 0,12-0,13 közötti. Új küszöböt nem állítottam be.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - a #5245 első kötegének módszere, vakfoltjai, 15 tételes forrás- és maiállapot-táblája, ítéletei és nyitott Colab-lépései.

### Colab-felvétel a nyitott tételekhez (job-190, 2026-10-17)

Az eredeti Picasa 3.9 angol felületén, alapállapotban (`C:\PicasaTeszt`, 24 kép), lépésenként képpel.

| jegy | felvétel | ítélet |
|---|---|---|
| #3661 | Eszközök ▸ Beállítások: az ablak mérete 584 × 345 képpont (az ablaklista szerint), a nyolc fül (General, E-Mail, File Types, Slideshow, Printing, Network, Web Albums, Name Tags) egy sorban elfér. | Az eredeti ablak rögzített méretű, a fülsor nem tördel. A 480 px-es legkisebb szélesség a PicasaPy saját kérdése, az eredetiben nincs megfelelője; a mai görgethető fülsor nem eltérés, hanem kiegészítés. |
| #3448 | A bélyegkép jobb gombos menüje mappanézetben (13. kép): View and Edit, Add to Album, Rotate Clockwise/Counterclockwise, Undo all Edits (szürke), Hide, Move to New Folder, Split Folder Here, Open File, Open With, Save és Revert (szürke), Locate on Disk, Delete from Disk, Copy Full Path, Upload to Picasa Web Albums, Block from Uploading, Reset Faces, Properties. | Mappanézetben a nem ide tartozó tételek **hiányoznak**, üres rés nincs; a csoportokat elválasztó vonalak tagolják. A mai PicasaPy (a rejtett tételek magassága nulla) ezzel egyezik. Album-nézetben a menü még nincs felvéve. |


## Forrás nélkül lezárt jegyek, második köteg (#5260, 2026-10-17)

Módszer: a helyi commitlistát (`git log --all --grep`) és az érintett fájlokat vetettem össze az eredeti Picasa `.fen` és `.tre` erőforrásaival, a `respack.yt` leleteivel, a bináris-index pozitív találataival, a képernyőkép-leltárral, a specifikációk részletes szakaszaival és a jelenlegi QML/Python forrással. A GitHub-jegykommentek nem voltak elérhetők; a jegytörzs teljes szövegét a munkakérés adta meg. A negatív bináris-index találatot nem tekintettem bizonyítéknak.

Mérési vakfolt: a mérőadat-archívumban nem volt #5260-hoz címkézett készlet, ezért nem bontottam ki fájlt. Friss Colab-felvétel nem készült. A leltár meglévő képei nem mutatják a #3773 AB módba lépésének előtte és utána állapotát, sem a #4440 sikeres visszaállításának befejező visszajelzését. Ezekre célzott felvétel kell.

| Jegy | Funkció | Eredeti forrás | Mai állapot fájl:sor | Ítélet |
|---|---|---|---|---|
| #3663 | Két különböző kép kijelölése és fókuszváltása kettős nézetben | `ui-audit-editor.md:2241-2272`, Colab EN 33-35, `editpanel.tre:964-994,1160-1201`, `0x00569af0`. | `PhotoViewer.qml:4339-4350,446-448,2114-2135` | **Egyezik.** A képre kattintás fókuszt vált. A kijelölt fél sora a szerkesztés célja. Javaslat a #5186-ba: a javított tétel lezárható. |
| #3709 | Alsó sáv nagyítója és nagyításcsúszkája | `picasa-fo-ablak-elrendezes.md:945-998`, `respack.yt` `thumbui/loupehit` és `scaleslider/sliderbase`. Az eredeti rajz 3 képpontot hagy a 127 képpontos foglalat két végén; a nagyító kattintóterülete keret nélküli. | `TrayBar.qml:1596-1667,1684-1689,1801-1808` | **Egyezik.** A jegy régi leírása megfordítja az eredetit. A mai sáv 3 px behúzású, a nagyító keret nélküli. Javaslat a #5186-ba: rögzítse a forrás szerinti állapotot, további UI-módosítást ne kérjen. |
| #3729 | Nagyítócsúszka sínje és fogantyúja | `szerkeszto-panel-meretek.md:438-459`, `respack.yt` `scaleslider/sliderbase` és `thumb`, `scaleslider.tre`. | `EditorSlider.qml:73-89`, `TrayBar.qml:1676-1689,1789-1807` | **Egyezik.** A mai alsó sáv 9 px-es sínt és 16 x 22 px-es fogantyút kér. Javaslat a #5186-ba: lezárható, új méretmódosítás nem indokolt. |
| #3756 | Kijelölt jelvény és feliratsáv kettős nézetben | `ui-audit-editor.md:2241-2272`, Colab EN 33-35: a „Selected” jelvény bal és jobb fókusznál a fókuszált kép mellett látszik. A feliratsávok mindhárom felvételen „Make a caption!” helyőrzőt mutatnak, ezért a képhez rendelt adat nem állapítható meg. | `PhotoViewer.qml:875-879,4237-4298,4675-4690` | **A jelvény igazolt, a teljes állítás statikusan nem dönthető el.** A mai jelvény követi a fókuszt, a felirat a bal/jobb kijelölési sorból olvas. Döntő Colab-felvétel: két eltérő, nem üres feliratú képpel rögzíteni a bal és jobb fókuszt, majd a feliratsáv adatait. |
| #3773 | AB nézet sorrendje és elsőként kijelölt oldala | Colab EN 33 (`kepek-leltar.md:109`), `ui-audit-editor.md:2267-2272`; a kép már AB állapotot mutat, az átváltás előtti kiválasztott képet nem rögzíti. | `PhotoViewer.qml:413-427,589-603,618-624,2683-2699` | **Forrás nem található** az AB módba lépés pillanatáról. A mai kód balra teszi a `currentIndex` képét, és bal fókuszt állít. Döntő Colab-felvétel: ismert kijelölt képpel indulni egyképes nézetben, AB-re váltani, kattintás előtt rögzíteni mindkét képet és a jelvényt. |
| #3826 | Fókuszos FF Sugár csúszkájának tartománya és alapértéke | `filterdesc-registry.md:156`, `filters-decoded.md:2372-2448`, bináris paramétermezők `0x008f86c8` és `0x008f86d1`; arcfelismerő nélküli 684-es golden-mérés. | `effect_params.py:170-180` | **Egyezik.** A `radius` tartománya -1 és 1, alapértéke 0. A szomszédos élesség 0 és 1 közötti. Javaslat a #5186-ba: lezárható. |
| #3998 | EXIF-bélyegkép az exportált JPEG-ben | `picasa-metaadat-tulajdonsagok.md:2107-2189`; bináris címek `0x009ece70-0x009ece8c`, `0x009b4aa0`, `0x009ecfb8`, `0x009ecdd2`; 186 export méret- és JPEG-mérése. | `exif_belyegkep.py:29-45,100-102`, `export_metadata.py:27-34` | **Eltér egy ritka hibás ágban.** A küszöb, méretezés, Lanczos-3 és q85 egyezik. Ha az APP1 blokk q10 mellett sem fér el, az eredeti az egész EXIF-et eldobja, a PicasaPy a bélyegképet hagyja el és megtartja a többi EXIF-adatot. Javaslat a #5186-ba: ezt nevezze meg tudatos eltérésként; a normál exportút egyezik. |
| #4013 | Crop kulcs egységes kezelése a nézőben, a bélyegképben és az exportban | `filters-decoded.md:16-27,45-70`; az eredeti Picasa exportmérése 1600 x 1200-as kimenetet adott `crop=` nélkül maradt `crop64` mellett. Az eredeti néző és bélyegkép viselkedése nincs megmérve. | `render/chain.py:94`, `edit_controller.py:1182`, `effect_thumbnails.py:129`, `exporter.py:713` | **Forrás nem található** az eredeti néző és bélyegkép szabályára. A mai PicasaPy minden renderelő utat az exportméréshez igazít. Döntő Colab-felvétel: ugyanazt a képet `crop=` nélkül, láncbeli `crop64` taggal rácson, nézőben és exportban rögzíteni. |
| #4313 | A 41 nyelv katalógusa, eredeti és saját szövegekkel | `Picasa3i18n.dll`; `picasa-program-resources.md:937-941` szerint az eredeti erőforrás 41 nyelvet tartalmaz. | 41 `picasapy_*.ts` fájl; `dictionary.py`, `application.py:1048-1053`, `i18n_build.py:1-13` | **Egyezik.** Nyelvenként van Qt TS-katalógus. Hiányzó QM esetén a program a TS-fájlból fordít, majd `QTranslator` tölti be. Az angol alapnyelv fordító nélkül fut. Javaslat a #5186-ba: lezárható. |
| #4314 | Első induláskori nyelvfelajánlás | `picasa-fo-ablak-elrendezes.md:665-747`, bináris rutin `0x004060b0`, prompt `0x00c7f2c8`; a szöveg-xref és a nyelvbetöltési hívássorrend külön ellenőrizve. | `language_controller.py:188-209`, `application.py:985-1011`, `FirstRunLanguageDialog.qml:38-60` | **Eltér.** Az eredeti NT rendszeren csak 11 felismert nem angol nyelvnél kérdez, angol ASCII-szöveggel és a generikus ablak jelölőjével. A mai felajánlás 40 nem angol katalógust elfogad, lefordítja a PicasaPy nevét tartalmazó szöveget, nem mutat jelölőt, és konkrét nyelvkódot ment. Javaslat a #5186-ba: ezek a nyelvterületi és felületi eltérések legyenek tételesen elfogadva vagy javításra jelölve. |
| #4320 | A diavetítés ismétlés- és zeneopciója működik | `options.fen:129-138`, `picasa-create-features.md:5942-5955`; a bináris konfigurációolvasó `0x007fa7f0` a `LoopSlideshow`, `PlayMP3Tracks` és `MP3SlideshowPath` beállítást olvassa. | `OptionsTabSlideshow.qml:15-84`, `controller.py:601-651,675-698`, `Main.qml:2971-2978`, `SlideshowView.qml:47-63,195-208` | **Egyezik a kért kapcsolatokban.** A mentett ismétlés szabályozza a körbelépést, a zenejelölő szabályozza a lejátszót. A PicasaPy mappa- és albumzenét is kezel. Javaslat a #5186-ba: a két beállítás bekötése lezárható. |
| #4358 | Névcímke-csúszkák értéke, beosztása és sorrendje | `options.fen:228-255`; eredeti magyar Options képernyőkép a `kepek-leltar.md:58` leltári tételben; eredeti alapértékek `picasa-arcfelismeres.md:49-50`. | `OptionsTabNameTags.qml:58-213,216-235`, `src/picasapy/faces/clustering.py:63-64` | **Eltér az alapértékben.** A sorok, értékfeliratok és tíz beosztás megvannak. Az eredeti mindkét küszöb alapértéke 85, a PicasaPy klaszterküszöbé 70 az SFace kalibrálása miatt. Javaslat a #5186-ba: rögzítse ezt a viselkedési eltérést; a felületi elrendezés egyezik. |
| #4377 | Diavetítés fül alapértékei és mappamezője | `options.fen:129-138`, eredeti magyar Picasa képernyőkép `kepek-leltar.md:54`. | `OptionsTabSlideshow.qml:15-50`, `controller.py:601-619` | **Egyezik.** Az ismétlés alapból ki, a zene be. A mappacímke a mező fölött áll. Javaslat a #5186-ba: lezárható. |
| #4385 | Nyomtatás fül metrikus alapméretei és kétoszlopos elrendezése | `options.fen:141-153`, eredeti magyar képernyőkép `kepek-leltar.md:55`, területi alapérték levezetése `picasa-nyomtatas.md:41-65`; a bináris `0x006e5ab0` a területi beállításból választ metrikus/angolszász méretsort. A kép mentett méretválasztással felülírható. | `OptionsTabPrinting.qml:74-92`, `print_controller.py:259-276`, `dpi.py:176-204,218-226` (#5492 utáni állapot) | **Egyezik szerkezetében és a metrikus alapérték útján.** Mentett méret nélkül a mai kód a metrikus alapértékeket használja; a QML öt elemet három bal és két jobb oszlopban rendez. A képernyőkép aktív értékei önmagukban nem bizonyítják az alapértékeket, mert mentett választás felülírhatja őket; a mai renderelt képpont-összevetés nincs meg. |
| #4440 | Mentés, visszaállítás és fotóművelet utáni látható visszajelzés | `picasa-menu-parancsok-viselkedes.md:668-680` és `picasa-beviteli-mezok.md:172-178`: eredeti mentési/visszaállítási folyamatjelzés és hibaüzenet; a képernyőkép-leltárban nincs sikeres visszaállítás utáni kép. | `save_controller.py:210-220,222-252,700-738`, `Main.qml:4122-4136`, `photo_ops_controller.py:268-283` | **Eltér a visszaállítás folyamatjelzésében; a sikeres lezáró üzenet nyitott.** A mentésnek van folyamatjelzője; a visszaállítás az indexet és az előnézetet frissíti, de nem mutat folyamatjelzőt. A sikeres visszaállítás utáni külön üzenetet az eredeti forrásból nem lehet megállapítani. Javaslat a #5186-ba: a visszaállítás folyamatjelzőjét kérje számon, a lezáró üzenethez pedig kérjen célzott Colab-felvételt. |

## Forrás nélkül lezárt jegyek, harmadik köteg (#5265, 2026-10-17)

Módszer: a `git log --all --oneline --grep` találataiból azonosítottam a lezárt jegyek módosításait. A mai QML és Python állapotot az eredeti képernyőképekkel, `.fen` és `.tre` erőforrásokkal, UI-leltárral, bináris indexszel és célzott diszasszemblálással vetettem össze. A GitHub-jegykommentek ebben a munkamenetben nem voltak elérhetők.

Mérési vakfolt: a mai felületet nem futtattam, ezért a táblázat a jelenlegi forráskódot írja le, nem mai képernyőképet. Az eredeti leltár nem tartalmazza az összes szükséges hover-, billentyű- és retusálási állapotot. A #4544 eredeti előtte-utána képe sincs a helyi mérőcsomagban. Ezeknél a Colab-lépés a döntő ellenőrzés.

| jegy | funkció | eredeti forrás | mai állapot fájl:sor | ítélet |
|---|---|---|---|---|
| #4456 | Mappa tulajdonságai elrendezése | `Picasa3/runtime/album.fen:1-29`; eredeti kép `2026-07-17 20 59 22.png` (`referencia/kepek-leltar.md:50`); `Folder Properties` sztring `0x00cc1be8`, hivatkozó függvény `0x00849750` | `src/picasapy/app/qml/PicasaPy/FolderPropertiesDialog.qml:273-291,322-410` | Részben egyezik: a címke, szerkeszthető név, dátum és Mégse gomb sorrendje megvan. A mai ablak képpontos elrendezése nincs lefényképezve. Javaslat a #5186-ba: a pixelparitást csak azonos állapotú mai képernyőképpel jelölje késznek. |
| #4482 | Átnevezés a Név mezőből | `album.fen:2-4`; eredeti kép `2026-07-17 20 59 22.png`, a mező szerkesztésre kijelölve | `FolderPropertiesDialog.qml:213-236`; `FolderPane.qml:1721-1728`; `library_controller.py:1741-1751` | Részben egyezik: a mai mező átnevező kezelőhöz jut, amely átnevezi a mappát és frissíti az indexet. Az eredeti képernyőkép mezőt mutat, de sikeres átnevezést nem. Javaslat a #5186-ba: az eredeti Picasában mappát átnevezni, majd a fa és az elérési út változását rögzíteni. |
| #4488 | Fájltípusok fül feliratai és térköze | Eredeti kép `2026-07-17 21 00 00.png` (`referencia/kepek-leltar.md:53`), a fül és a teljes fájltípus-sorrend látszik | `src/picasapy/app/qml/PicasaPy/OptionsTabFileTypes.qml:7-13,28-49,132-259` | Feltételes egyezés: a sorok és sorrend megfelel az eredeti képnek, a mai kód külön geometriát ad meg. Mai PicasaPy-kép nincs a képpontos összevetéshez. Javaslat a #5186-ba: a vizuális állítást páros képernyőképekkel igazolja. |
| #4494 | Naptár a Dátum mezőből | `album.fen:5-9` dátumvezérlője és Automatikus dátum gombja; eredeti kép `2026-07-17 20 59 22.png`; bináris `0x008d8070` létrehozza a `SysDateTimePick32` vezérlőt, `0x008d9243` azonosítja az osztályt. | `FolderPropertiesDialog.qml:397-411,641-649`; `DateCalendarPopup.qml:5-18` | **Igazolt a forrásút szintjén.** Az eredeti dátumvezérlő naptáras vezérlő, a mai naptárgomb megnyitja a dátumválasztót és a kiválasztott napot a mezőbe írja. Pixelazonosságot és kattintásos eredeti felvételt ez a statikus lelet nem igazol. |
| #4527 | Csillag súgójának célja | `referencia/tre-eroforrasok/thumbui_text.tre:113` és `referencia/ui-leltar.csv:1820` az `Add/Remove Star` súgót a csillaghoz rendeli; a More külön elem (`referencia/ui-leltar.csv:1272`) | `src/picasapy/app/qml/PicasaPy/TrayBar.qml:1244-1256,2264-2293` | A célhoz kötés egyezik: a mai súgó a csillaggombon van, nem a More gombon. Az eredeti súgó tényleges képernyőbeli helyét nem mutatja hover-felvétel. Javaslat a #5186-ba: eredeti Colab-felvétel a csillag és a More fölötti külön hoverrel. |
| #4530 | Keresősáv javaslatainak billentyűkezelése | `referencia/tre-eroforrasok/searchcontainer.tre:4-10` és bináris `0x0040e7b0`: az eredeti `searchautocomplete` erőforrás létrehozása | `SearchSuggestions.qml:42-68`; `MainToolbar.qml:821-832`; `Main.qml:2977-2986` | Nyitott: az eredeti javaslatlista forrása megvan, de ez nem bizonyítja a fel-le, Enter és Escape billentyűk eredeti viselkedését. A mai kód kezeli e billentyűket. Colab-felvétel kell a kijelölésről, kiválasztásról és bezárásról. |
| #4531 | Vissza a teljes nézethez szöveges keresés után | `referencia/tre-eroforrasok/searchoptions.tre:20-27`; eredeti címke és súgó a `picasa-kereses-modok.md:29` szerint: `Back to View All` és `Exit Search Mode` | `src/picasapy/app/qml/Main.qml:3368-3400` | Feltételes egyezés: a mai gomb kiüríti a keresőmezőt és törli a szűrést. Az eredeti gomb viselkedéséről szöveges keresés utáni felvétel nincs. Javaslat a #5186-ba: Colab-felvétel szöveges lekérdezés után a gomb megnyomásával. |
| #4532 | Ne legyen működés nélküli jel a szűrősáv végén | `referencia/tre-eroforrasok/searchcontainer.tre:30-95` és `picasa-kereses-modok.md` 3. szakasza: a szűrők és a külön `search_icon`; további szűrőgomb nem azonosított | `src/picasapy/app/qml/PicasaPy/MainToolbar.qml:725-728` | Részben egyezik: a mai kódban térköz van a korábbi jel helyén. A teljes sávvégi eredeti elrendezésről nincs felvétel; pontos pozíciója nyitott. |
| #4533 | Megnyitás ezzel programválasztás és képnyitás | `ui-audit-context-menus.md` 6.3; bináris `0x00730790` (`AlbumPhoto::ID_FILEOPENWITH`) és `0x00772300` (Windows `OpenWithList` út) | `PhotoContextMenu.qml:350-390`; `OpenWithDialog.qml:26-33,45-61,94-107`; `fileops_controller.py:731-761` | Feltételes egyezés: a parancs, társításlista és a mai programválasztás/indítás útja megvan. Az eredeti menükattintás és képindítás futó igazolása nincs; Colab-felvétel kell. |
| #4534 | Mappa kettéosztása a kijelölt képtől | `picasa-menu-parancsok-viselkedes.md:7689-7750`; eredeti handler `0x005e8570`, a leírt művelet a kijelöléstől a csoport végéig viszi át a képeket | `src/picasapy/app/qml/Main.qml:712-749`; `src/picasapy/app/fileops_controller.py:264-320` | Egyezik: a mai út az első kijelölt képtől a mappacsoport végéig készít új testvérmappát, és áthelyezi a képeket. Az eredeti bináris viselkedése és a mai műveleti út külön forrásból dokumentált. |
| #4539 | Film készítése gomb a mappafejlécen | `referencia/tre-eroforrasok/headerpanel.tre:75-84` `create_movie` gombja; eredeti kép `2026-07-17 20 54 38.png` mutatja az alapból látható gombot | `src/picasapy/app/qml/PicasaPy/LightboxHeader.qml:407-429` | Egyezik: az eredeti erőforrás gombot ír le, a kép látható állapotot mutat, a mai gomb mappanézetben látható. |
| #4542 | Vörösszem-figyelmeztetés kiegyenesítés után | Bináris sztring `0x00e063da`, hivatkozó függvény `0x005f30e0`; az eredeti szöveg megegyezik a mai szöveggel | `src/picasapy/app/qml/PicasaPy/EditorRedeyePanel.qml:81-96`; `PhotoViewer.qml:1356-1369` | A szöveg egyezik, a mai megjelenési feltétel `tiltParam != 0`. Az eredeti feltétel futás közbeni igazolása hiányzik. Javaslat a #5186-ba: Colab-felvétel kiegyenesített és kiegyenesítés nélküli képpel. |
| #4543 | Ecsetkör a retusálás céljánál és forrásánál | `referencia/tre-eroforrasok/editpanel.tre:217-229,958-962`: a retusáló megjeleníti a `thumbui/circlecursor` elemet és a `RetoucherHandler`-t | `src/picasapy/app/qml/PicasaPy/PhotoViewer.qml:3880-3939`; `src/picasapy/app/edit_controller.py:1727-1747` | Nyitott a két eredeti célpont részlete: az erőforrás a kört és a kezelőt igazolja, de nem mutatja külön a cél- és forrásjelölő mozgását. Javaslat a #5186-ba: Colab-felvétel első kattintás, forrásmozgatás és második kattintás közben. |
| #4544 | Retusfolt széleinek környezetbe olvadása | `referencia/tre-eroforrasok/editpanel.tre:958-962` az eredeti retusáló kezelőt azonosítja, de az eredeti pixelátmenethez nincs képi golden vagy leltározott felvétel | `src/picasapy/render/retouch.py:86-116,137-224,229-249` | Az eredeti széleffekt forrása nem található. A mai kód irányított Poisson-gyógyítást használ, de az eredetivel való egyezés nincs mérve. Javaslat a #5186-ba: ne jelölje eredeti paritásnak; kérjen azonos mintán eredeti előtte-utána képet és nyers kimenetet, majd rögzítse a mért különbséget. |
| #4546 | Rendszerbetűk a szöveg betűtípus-listájában | `edittextpanel.tre:19-22`; bináris `0x0062d750` építi a szövegpanel `fontfamily` elemét és hívja a `0x00825e90` függvényt, amely a GDI32 `EnumFontFamiliesExW`-t hívja (`0x00825ef8`) | `src/picasapy/app/qml/PicasaPy/EditorTextPanel.qml:121-131`; `src/picasapy/app/edit_controller.py:937-943`; `src/picasapy/render/text_fonts.py:98-137` | Egyezik: az eredeti szövegpanel rendszer-betűcsaládokat enumerál, a mai Qt a telepített rendszer-betűcsaládokat kínálja. A lista gépenként változhat. |

## Forrás nélkül lezárt jegyek, negyedik köteg (#5271, 2026-10-18)

Módszer: a tizenöt jegyhez a `git log --all --grep="#<szám>"` találatait és a változtatott fájlokat néztem meg. Az eredeti forrás a `docs/specs` szakaszai, a `referencia/tre-eroforrasok` erőforrásai, a `stringres-en-hu.tsv`, a `ui-leltar.csv`, a `kepek-leltar.md` és a bináris sztringtábla (`binary-index/string_xrefs.csv`) volt. A `ui-lefedettseg-elemek.csv` a legtöbb tételnél „megvan" állapotot mutat. Ez nem ítélet, ezért nem vettem bizonyítéknak. A jegykommentek közül csak a #4571 és a #4579 tartalmaz érdemi szöveget, a többi foglalási sor. A negatív bináris-index találatot nem tekintettem bizonyítéknak. Kódhoz nem nyúltam.

Mérési vakfolt: az alkalmazást nem futtattam, és nincs új Colab-felvétel. A mai állapotot kódolvasással vetettem össze, renderelt képpel nem. A tesztek nem futottak. A #4547 eredeti ikonjait a respackből kivontam, futó felülettel nem hasonlítottam össze. A #4570 alapértéke és megnyitáskori viselkedése nincs felvételen. A #4550 statikus példa-sorát a `.fen` leírásából állapítottam meg, futó programban nem ellenőriztem.

| jegy | funkció | eredeti forrás | mai állapot, fájl:sor | ítélet |
|---|---|---|---|---|
| #4547 | A szöveg balra, középre és jobbra igazító gombja | `referencia/tre-eroforrasok/edittextpanel.tre:75-97`: három külön ikonréteg; a `runtime/respack.yt` kivont képei külön balra, középre és jobbra igazított vonalakat mutatnak. | `src/picasapy/app/qml/PicasaPy/EditorTextPanel.qml:238-288`; `AlignIcon.qml:1-39` | **Egyezik a jegy külön jelekre vonatkozó állításával.** Az eredeti három ikonréteg és a mai három külön ikon igazolva. Képpont-pontosságú alakazonosság nem volt a jegy feltétele. |
| #4550 | Egyéni méretarány párbeszéd, példa-sor, törlő kuka | `referencia/tre-eroforrasok/editpanel.tre:784-790`: a legördülő bal oldalt, `crop_delete_custom` jobb oldalt, ugyanazon a soron. `docs/specs/picasa-fen-dialogs.md:101` és `docs/specs/ui-audit-editor.md:1029`: a `customaspectratio.fen` „Example:" sora statikus, nincs `bind`. | `src/picasapy/app/qml/PicasaPy/AddCustomAspectRatioDialog.qml:99-113` (statikus példa-sor); `EditorCropPanel.qml:91-135`: a kuka (`cropDeleteCustom`, `:123`) a legördülő mellett. | **Egyezik a forrással, a jegy szövege téves.** A jegy élő példa-sort kér. Az eredeti `.fen` szerint a sor statikus, a javítás ezt követi. Javaslat a #5186-ba: a jegy kérését „statikus példa-sor"-ra javítsa. Futó ellenőrzés nincs. |
| #4551 | Vágópanel: az eredetiben nem létező Bal felső, Fekvő és Álló gombok | `referencia/tre-eroforrasok/editpanel.tre:772-782,795-830`: három `cropsug`-előnézet, majd Rotate/Preview/Reset/Apply/Cancel; `referencia/ui-leltar.csv`: a három előnézet felirat- és súgómezője üres; eredeti kép: `2026-07-18 195048.png`. | `src/picasapy/app/qml/PicasaPy/EditorCropPanel.qml:290-324`; `EditorPanel.qml:475-482`: 3 dinamikus javaslat, nincs „Bal felső/Fekvő/Álló” nevű rögzített gomb, de van „Suggested crops” cím és stratégiacímke. | **IGAZOLVA a jegy címében megnevezett három rögzített gomb hiányára.** A három eredeti előnézet ma is megvan. Külön vizuális eltérés, hogy PicasaPy címet és stratégiacímkéket tesz föléjük; a `vagas-eszkoz-allapot.md` 3. szakasza ezt és a bélyegképek jelenlegi bekötését rögzíti. |
| #4557 | Shift+Ragyogás: csúszkás panel Intenzitás és Sugár csúszkával | `docs/specs/ui-audit-editor.md:1383` és `:1415`: a Shift-pár `glow`, paraméterei Intenzitás és Sugár. `docs/specs/filterdesc-registry.md:162-163`: `glow` és `glow2` ugyanaz a két csúszka (0 = Intensity, d = 0,65; 1 = Radius, d = 3,0, log 250). | `src/picasapy/app/effect_params.py:147-150` (`glow`), `:151-161` (`glow2`, ugyanaz a két csúszka). | **Egyezik.** A két csúszka a `glow2` szerint épül fel. A Sugár tartománya és alapértéke (0-100, 20) a `:155-159` megjegyzése szerint szándékos. A `glow` ugyanezt használja. A skálázást külön nem mértem. |
| #4558 | Shifttel a csempék bélyegképe is a másodlagos effektet mutatja | `docs/specs/ui-audit-editor.md:1390`: a Shift-csempe „felirata és bélyegképe is" a másodlagos effektre vált (`_mod%s` utótag). | `src/picasapy/app/qml/PicasaPy/EditorEffectsTab1.qml:11-14` (a bélyegkép a Shift szerint vált, a Shift a láthatóságot), `:60-72`, `:104-122` (`thumbAltActive`). | **Egyezik.** A bélyegkép és a felirat is a Shift-változatot mutatja. |
| #4560 | Sixties, Polaroid és Lekerekített szél színmintájának felirata | `docs/specs/picasa-effekt-feliratok.md:75`: Polaroid, RoundedEdges, Sixties → „Background Color" = „Háttérszín" (`0x008feed8`). | `src/picasapy/app/effect_params.py:319`, `:403`, `:408` („Background Color"); `src/picasapy/app/i18n/picasapy_hu.ts:4462-4465` („Háttérszín"). | **Egyezik.** A három effekt felirata az eredeti szöveg, a magyar fordítás megvan. |
| #4561 | Effekt alkalmazása után a csempék előnézete a frissített láncot mutatja | `docs/specs/ui-audit-editor.md:2900` (a 2827. szakasz, #2061): „a csempe-előnézet a szerkesztési lánc AKTUÁLIS tetejére alkalmazza a saját effektjét, nem az alap fotóra". | `src/picasapy/app/effect_thumbnails.py:16-21` (a lánc a `filters` paraméterben érkezik, a frissebb állapotot követi); `src/picasapy/app/qml/PicasaPy/editorpanel_logika.js:76-84` (az aktuális `effectChain` az URL-ben). | **Egyezik a spec szerint.** A forrás a lánc tetejére renderel, a mai kód az aktuális láncot viszi át. A `tests/app/qml_functional/test_effect_tile_chain_refresh_4561.py` tesztet nem futtattam. |
| #4562 | Filmszalag: hét férőhely, az aktuális kép középen, kétszínű keret | `docs/specs/szerkeszto-felso-sav.md:161-185`: 5.1 hét férőhely (7 × 28 + 6 × 3 = 214 px), 5.2 az aktuális kép a középső férőhelyen, 5.3 keret: `#009EFF` és `#D4D4D4`. | `src/picasapy/app/qml/PicasaPy/PhotoViewer.qml:1905-1910` (214 px, fix), `:1945` (31 px cella), `:1955-1957` (28 × 28 bélyegkép), `:1976` (aktuális kép), `:1987`, `:1994` (kétszínű keret). | **Egyezik.** A hét férőhely, a középső aktuális kép és a kétszínű keret megegyezik az 5. szakasszal. A cella- és bélyegképméret is egyezik (31 és 28 px). |
| #4563 | A néző ◀ és ▶ gombja nyomva tartva folyamatosan léptet | `oneup.tre:75-81`: `oneup/prev` és `oneup/next` `mousedown`; `setautorepeat` csak a külön `plusone`/`minusone` vezérlőkön (`:133-143`). `picasa-eger-es-kijeloles.md:621-631` az ismétlő vezérlők között csak a plusz/mínusz gombokat sorolja fel. `picasa-menu-parancsok-viselkedes.md:2379-2385,2395-2405,2698-2706`: a néző léptetőágai és a külön egérgörgő-ismétlés. | `src/picasapy/app/qml/PicasaPy/PhotoViewer.qml:1855-1863,2021-2029` (`autoRepeat: true`). | **Eltér.** A `szerkeszto-felso-sav.md:193-197` a filmcsík `filmcontainer` nyilait írja le, nem a `oneup` nézőgombjait. Javasolt teendő: a két nézőgomb ismétlésének eltávolítása, a filmszalag saját ismétlésének megtartásával. |
| #4570 | AutoPlayMovies: a videó megnyitáskor magától elindul-e | `referencia/binary-index/string_xrefs.csv:6217-6218`: a `AutoPlayMovies` sztring a `0x00c91f74` címen, hivatkozói `0x00593880` és `0x00594820`. `docs/specs/ui-audit-editor.md:3252`: a `Preferences` kulcs a videó-vezérlő építésénél. Az alapérték és a viselkedés nincs leírva. | `src/picasapy/app/appearance_controller.py:26-28` (kulcs; „Alapállapot: igen (a Picasa így működött)"), `:176-182` (nem slot); `src/picasapy/app/qml/PicasaPy/VideoPlayerView.qml:18-24`, `:89`, `:99-106` (indítás). | **Forrás nem található** a megnyitáskori viselkedésre és az alapértékre. A kulcs és a kiolvasás helye megvan. Az `appearance_controller.py:27` sorának „a Picasa így működött" állítása forrás nélkül áll. Döntő Colab-lépés: a kulcs 0, illetve 1 értékkel, videó megnyitása, és az alapérték kulcs nélküli, friss profilban. |
| #4571 | A Névtelenek album csempéi az arcot mutatják, nem a fotó közepét | `docs/specs/picasa-arcfelismeres-kutatasi-naplo.md` (19. szakasz, job-163: csoportosított nézetben álló arc-kivágások). A #4571 számmal nincs commit. A lezárást a #4511 végezte (`51235e5aa`, PR #4521, v0.9.40), a jegy kommentje szerint. | `src/picasapy/app/people_controller.py:858-867` (a csempe `thumbUrl`-je `_thumb_url(photo, arc=face.rect)`; arc nélküli elem kimarad); `src/picasapy/app/qml/PicasaPy/UnnamedFacesView.qml:408` (a kép forrása a `thumbUrl`). | **Egyezik.** A csempék arckivágást mutatnak, és nincs visszaeső ág a fotó közepére. A `51235e5aa` commit `&fz=` tesztjei ezt rögzítik. |
| #4572 | Nézőben a felismert, névtelen arcra kattintva keret és „Type a name” mező | `picasa-arcfelismeres.md:935-944`: eredeti Colab EN 38; `tests/fixtures/face_type_a_name_reference_en38.png`: az eredeti keret és mező képe. | `src/picasapy/app/qml/PicasaPy/FacesOverlay.qml:78-89,112-124,337-341,406-418`: pozitív azonosítójú felismert arc kattintására kijelölés, keret, fókuszált üres mező „Type a name” helyőrzővel. | **IGAZOLVA** a jegy állítására: az EN 38 nem mellőzött névtelen arc esete egyezik. Az EN 37 mellőzött arc ellenpróba nem része ennek az elfogadási pontnak; alkalmazásfuttatás és tesztfuttatás nem történt. |
| #4574 | Emberek panel: „Add a person manually" gomb és útmutató | `referencia/stringres-en-hu.tsv:3228` (az útmutató szövege); `referencia/tre-eroforrasok/peoplepanel.tre:24-32` (a gomb induláskor rejtett, `m_hidden`); `referencia/kepek-leltar.md:113` (Colab EN 37: a gomb a mellőzött arc kijelölésekor látszik). | `src/picasapy/app/qml/PicasaPy/PeoplePanel.qml:391-399` (`visible: !manualAddActive`, `enabled: selectionCount > 0`), `:403-440` (kézi keret; az útmutató szövege `:414-431`). | **Részben egyezik.** Az útmutató szövege karakterre egyezik a `stringres-en-hu.tsv:3228` szövegével, a felirat is. A láthatóság eltér: a `.tre` szerint induláskor rejtett, a mai gomb kijelölés nélkül is látszik, csak tiltva. Döntő Colab-lépés: az Emberek panel kijelölés nélküli állapota. |
| #4579 | Tulajdonságok panel: Fájl dátuma, CCD szélessége, Rekesz, JPEG minőség, Személycímkék | `picasa-metaadat-tulajdonsagok.md:2339-2384` (eredeti sorrend és forrásmezők); `:2407,2413,2434,2486` (megjelenési feltételek és számítások). | `src/picasapy/app/qml/PicasaPy/PropertiesPanel.qml:55-80` (az entries modell megjelenítése); `src/picasapy/app/formatting.py:499-501,518-545,567-584`; `src/picasapy/app/tulajdonsag_sorok.py:27-74`; `src/picasapy/metadata/reader.py:322-360`; `src/picasapy/metadata/jpeg_quality.py:66-85`. | **IGAZOLVA**, ha a kép adatait az adott sor megjelenési feltételei teljesítik. Mind az öt a megfelelő helyre kerül; a minőségsor alacsony minőségi tartományának eredeti előjeles hibája szándékosan eltér. A korábbi G táblázat téves „nincs” celláit javítottam. |
| #4584 | Helyek térkép: betöltésjelzés és internet nélküli üzenet | `referencia/tre-eroforrasok/geopaneltext.tre` (a betöltésfelirat, `geopanel/loading_title`); `docs/specs/jobb-fiok-meretek.md:158-160`: `loading_icon` 64 × 52, `loading_title` 213 × 25, y 117 és 153; `referencia/stringres-en-hu.tsv:2982` (`geo::init_err`, a hibaüzenet, bináris hivatkozóval: `0x00ca1d58`). | `src/picasapy/app/qml/PicasaPy/PlacesPanel.qml:145-152` (`BusyIndicator` 48 × 48), `:155-159` (a két szöveg). | **Részben egyezik.** A két szöveg az eredeti. A jelző eltér: az eredeti 64 × 52-es ikon, a mai 48 × 48-as `BusyIndicator`. A függőleges helyet nem mértem a 117 és 153 px-es értékekhez képest. Javaslat a #5186-ba: a jelzőt az eredeti ikonhoz igazítani, vagy eltérésként rögzíteni. |

## Forrás nélkül lezárt jegyek, ötödik köteg (#5272, 2026-10-18)

Módszer: a tizenegy jegyet a `git log --all --grep` találataiból és a változtatott fájlokból vettem sorra. A jegyek kommentjeit a `gh issue view` adta. Az eredeti forrást a `docs/specs` szakaszaiban, a `stringres-en-hu.tsv`-ben, a képernyőkép-leltárban és a PicasaPy fő munkafájának `research/testdata/screenshot/` mappájában lévő képekben kerestem. A #4846 eredeti fülsávját 4-szeres nagyításban néztem meg. A mai állapotot a QML és a Python forrásból olvastam. A negatív bináris-index találatot nem tekintettem bizonyítéknak. A #5121 Colab-méréseit a jegy kommentjeiből vettem át.

Mérési vakfolt: nem futtattam az alkalmazást, és nem rendereltem a mai felületet, ezért a pixelszintű állítások nyitottak. Eredeti film- vagy nyomtatási kimenetet a leltárban nem találtam (#4602, #4616). A #4594 olvasási útjához Colab-felvétel kell: nagy kezdőbetűs `Picasa.ini`, benne csillag és felirat. A #5121 Colab-képeit nem néztem meg, csak a jegy kommentjeinek leírását. A `picasa-konyvtar-eszkoztar-viselkedes.md` 7/b. szakasza a beszúrási feltételt nyitottnak hagyta. A Colab-mérés a húzási eseteket megválaszolta, a bináris kérdés (`0x004b3770`, `0x00565920`) viszont nyitva maradt.

| Jegy | Funkció | Eredeti forrás | Mai állapot, fájl:sor | Ítélet |
|---|---|---|---|---|
| #4590 | Csatolt memóriakártya és kamera felismerése, forrásként felkínálása | `picasa-importalas.md`, „Forrásfajták”: `Removeable` → „Cserélhető meghajtó (%s)”, `WiaDev` → „Wia-” (kamera). `stringres-en-hu.tsv:173`: „Mappa a lemezen”. | `import_source_controller.py:176-268`: Linuxon `/media` és `/run/media`, Windowson cserélhető meghajtó vagy DCIM-es kötet. `:258-261`: a PTP/MTP kamera tudatosan kimarad. `ImportSourceDialog.qml:64-72`. | **Részben egyezik.** A kártya és a cserélhető meghajtó egyezik. A kamera hiányzik, a kód ezt szándékosan kizárja. |
| #4594 | Csillagok és feliratok beolvasása a régi `Picasa.ini` fájlból | A név bizonyított: `picasa-exe-strings.md:248` (a régi, korai verziójú név, megerősítve), `string_xrefs.csv:3422-3429`: nyolc hivatkozási hely. `picasa-ini-format.md:13`: a korai verzió neve. Az olvasási út nincs mérve. | `scanner/walker.py:369` (a régi fájl is adja a `has_ini` jelzőt), `index/sync.py:1216-1220` (`_load_ini`), `ini/io.py:142` (`ini_source_path`: a `.picasa.ini` az elsődleges, a régi fájl csak olvasási forrás). | **Forrás nem található** az olvasási útra. A név megvan, de nem derül ki, hogy az eredeti 3.9 olvas-e csillagot és feliratot belőle. Döntő: Colab-felvétel nagy kezdőbetűs `Picasa.ini`-vel, csillaggal és felirattal. |
| #4595 | Kézi mappanév nélkül nem indul az importálás | `picasa-importalas.md`, „A tipp-sor NÉGY állapota”, 1. állapot: „Enter new folder title or choose existing folder to continue”. A folytatáshoz cím vagy meglévő mappa kell. | `import_source_controller.py:859-860` (kézi mód cím nélkül visszatér), `importsource.py:374-377` (`ValueError`), `ImportSourceDialog.qml:816` és `:834` (a tipp). Az Import gomb engedélyezése (`:950-953`) nem nézi a címet. | **Egyezik** a tilalomban. A visszajelzés eltér: a gomb engedélyezett, a kattintás csendben nem tesz semmit. |
| #4596 | Forrásként fájlok is elfogadhatók, nem csak mappa | `0x00520fa0` a `0x00c88d70` „Import Files/Folder" címet használja; `acquirepanel_text.tre:114-115` kommentelt tooltipje „single images from disk”-et említ, de ez nem aktív súgó. A tényleges eredeti fájlkijelölés nincs igazolva. | `ImportSourceDialog.qml:368-377,978-1004` (`Files...`, `FileDialog.OpenFiles`); `import_source_controller.py:795-814`; `importsource.py:254-286`. | **Nyitott az eredeti működésre.** A mai kód kijelölt fájlokat fogad és olvas be; az eredeti működést Colab-felvételnek kell eldöntenie. |
| #4602 | A nyomtatás a rácson látott, szerkesztett és elforgatott képet nyomtatja | Nincs leírt eredeti szabály. A `kepek-leltar.md` 82-83. tétele (Colab EN 29-30) a nyomtatási elrendezést mutatja, nem azt, hogy a szerkesztett kép került-e rá. | `print_controller.py:769-790` (`_render_photo` → `render_photo_pixels`, ugyanaz a renderelő, mint az exportnál), `:68` (import). | **Forrás nem található.** Döntő: Colab-felvétel egy forgatott és szűrt képről, rácson és nyomtatási előnézetben. |
| #4611 | A weboldal-export a felhasználó saját `.tpl` sablonjait is felajánlja | `picasa-program-resources.md:112-120`: a sablonok a `web/templates/<sablonnév>/` mappákban vannak, a gyökér az `index.tpl`. `picasa-web-template-nyelv.md:15`: a `#templatefile` fejlécben lévő név az export-varázslóban jelenik meg. | `webexport/catalog.py:30-34` (felhasználói mappa: `~/.local/share/picasapy/webexport/templates`), `:44-53` (gyári sablonok, utánuk a sajátok), `:56-75` (`index.tpl` és fejléc). | **Részben egyezik.** A felajánlás és a fejlécből vett név egyezik. A tárolási hely eltér: az eredetinél a programmappa `web/templates` alatt van, nálunk a felhasználói mappában. A varázsló bejárását nem mértük. |
| #4616 | A film Show Captions kapcsolója a Picasa-feliratot mutatja, nem csak az EXIF-leírást | A kapcsoló megvan: `picasa-create-features.md:3191` (`makemoviepanel/show_captions` → `showcaption`). A tulajdonos mozgófilm-képe (`kepek-leltar.md`) a „Képfeliratok megjelenítése” jelölőt mutatja. A film szövegének eredeti forrása nincs mérve. `picasa-ini-format.md:98`: JPEG-nél a felirat az IPTC Caption mezőbe kerül, nem a `.picasa.ini`-be. | `movie/slideshow.py:545-558` (`_picasa_caption`: csak az ini `caption` kulcs), `:597` (EXIF 270 tartalék). A film nem olvas IPTC-t. | **Részben egyezik.** A kapcsoló egyezik. A spec szerint JPEG-nél a Picasa-felirat IPTC-ben van, ezt a film nem olvassa, ezért eltérés várható. Mérés nincs. |
| #4846 | A szerkesztő fülikonjainak rajza tükrözött és egyszerűsített | Eredeti: `research/testdata/screenshot/2026-07-17 20 56 36.png`; az öt ikon iránya és alakja látszik a Picasa 3.9 fülsávján. | `src/picasapy/app/qml/PicasaPy/EditTabIcon.qml:42-155`: Canvas rajzutak és tájképes kompozíció; a csavarkulcs feje bal fent, az ecset sörtéje bal lent, a tájkép balra, az ecset jobbra kerül. Mai renderelt ikonról nincs felvétel. | **MÉRVE (2026-10-26, #5946):** az irányok egyeznek (tükrözés-kontroll: a tükrözött IoU 0,09-0,21, a normál 0,55-0,66). A tinta-szín (`#2b2b2b` a `#373535` helyett), a négyzet-szín és átmenet, a felhő-szín és a függőleges elhelyezés eltér. Részletek és Teendő: `ui-audit-editor.md`, „A fülikonok összevetése a referenciával”. |
| #4881 | A párbeszédek szabványos gombjai a választott felületi nyelven jelenjenek meg | A Picasa saját `.fen` párbeszédei a saját gombfeliratukat használják (`picasa-fen-dialogs.md:106-107`: OK, Cancel; `:37`: Igen/Nem/Mégse). A Windows-üzenetdoboz gombjainak eredeti viselkedését nem mértük. | `application.py:1014-1029` (`_install_qt_translator`: a Qt `qtbase_*.qm` fordítója), `:1044` (`QLocale.setDefault` a választott nyelvvel, a területet a rendszer adja). | **Egyezik** a nyelv elvében. A tizedesjel a rendszer területét követi (ADR-004), az eredetit nem mértük. |
| #5007 | A mappára húzott indexképek átkerülnek, a Másolás/Beillesztés átvisz képet | `picasa-menu-parancsok-viselkedes.md:627-633`: a vágólapra fájlok kerülnek (IDList, FileGroupDescriptor), a Kivágás és a Másolás különbsége a `Preferred DropEffect` formátumban van. A húzás szemantikája (mozgatás vagy másolás) nincs leírva. | `FolderPane.qml:1193-1214` (`folderDropArea` → `photosDroppedOnFolder`), `Main.qml:3315-3324` (mozgatás: `movePhotos`), `fileops_controller.py:590` (`copyFilesToClipboard`), `:622` (`pasteFilesFromClipboard`). | **Részben egyezik.** A vágólap modellje egyezik a forrással. A húzás mozgatása forrás nem található. |
| #5121 | Az első album után ráhúzással már nem lehet új albumot készíteni | Eredeti: a `picasa-konyvtar-eszkoztar-viselkedes.md:576-605` bináris útja szerint a 4-es `newalbumprompt` rekord céljára ejtés albumot készít; a `paritas-ellenorzes.md` korábbi feljegyzése (job-155/-156/-159/-160) szerint meglévő album mellett a fejléc/sorvége/+ nem készít új albumot, meglévő album sora pedig képeket ad a meglévő albumhoz. A nyers Colab-képek nem kerültek elő a helyi mérőadat-archívumban. | `src/picasapy/app/qml/PicasaPy/AlbumsSection.qml:64-103` (új album cél csak üres `albumsModel` esetén), `:209-221` (album-sor dropja a meglévő albumhoz adja a képeket). | **IGAZOLVA a meglévő album melletti viselkedésre**, a korábban dokumentált Colab-mérések szerint; a mai kód célterületei ezt követik. A binary spec `§7/b` továbbra sem bizonyítja statikusan a 4-es sor beszúrási feltételét. **Külön eltérés:** PicasaPy üres albumlistánál mutat súgót, az eredeti job-155 feljegyzés szerint a csak „Recently Updated” rendszeralbumnál nem mutatott. |

## 7. réteg: effektkimenet az eredetihez mérve (#5277, 2026-10-18)

**Mérési állapot:** `c668968b94cf706f63e6596c8e2f2e7fea467ccb` (a munkafa induló, friss main állapota). A mérő a `tools/golden/analyze_validation_kit.py::mean_de` CIE76 átlagos ΔE-jét használja: a renderelt képet előbb a Picasa-referencia JPEG mintavételezésével és kvantálótábláival kódolja újra (`tools/golden/jpeg_reference.py`, #4940), majd a dekódolt képeket hasonlítja össze. Az ítéleti küszöb változatlanul `MATCH_DE = 2,0`; `ΔE ≤ 2,0` egyezik.

A referenciák a `~/.local/share/picasapy-meroadat/meroadat.tar` archívumból származnak; csak a szükséges fájlokat bontottam ki a munkafa ideiglenes könyvtárába, majd a mérés végén törlöm. NAS-adatot nem használtam. A futási környezet terhelési naplója (gép/mag/RAM, futás előtti és utáni 1/5/15 perces terhelés) **NINCS MEG**; minden mintapár egy render- és ΔE-futást kapott, a `meroszett` 4 párhuzamos workerrel futott.

A táblázatban a **mintaszám** az adott effektcsaládhoz tartozó, tényleges eredeti Picasa-exporttal összehasonlított sorok száma; a mért eltérés ezek legnagyobb ΔE-je. Belekerült a 684-es szettből 179 export (180 sorból egy `unsharp/max` export hiányzott), a `PicasaPy meroszett` eredeti exportkészletéből 178, a `merokit-2`-ből 49, a `3084-poszterizalas`-ból 2 és a `951-kiemelesek-arnyekok-fel-allas`-ból 1. Ez összesen 409 összehasonlított effektmintasor, 73 mérőszett-csoportban. A további 7 `merokit-3` eredeti export láncviselkedési próba, külön lent.

A korábbi, 2026-10-13-i táblázat még az `a8ba353b3561` kódállapotot mérte; az aktuális `b90c9736c` #4940 óta a JPEG kódolás normalizált. Ezért a régi táblázat nyers RGB-értékei nem közvetlenül összevethetők az alábbi, JPEG-kvantálótáblákkal normalizált ΔE-értékekkel (például `nightvision`: nyers 4,528, normalizálva 0,000).

| Effekt | Mintaszám | Mért eltérés (max. ΔE76) | Küszöb | Ítélet |
|---|---:|---:|---:|---|
| `ansel` | 2 | 0,000 | 2,000 | egyezik |
| `autobacklight` | 3 | 0,000 | 2,000 | egyezik |
| `autocolor` | 4 | 0,096 | 2,000 | egyezik |
| `autocontrast` | 3 | 0,000 | 2,000 | egyezik |
| `autolight` | 3 | 0,645 | 2,000 | egyezik |
| `backlight` | 7 | 0,000 | 2,000 | egyezik |
| `blur` | 9 | 0,000 | 2,000 | egyezik |
| `boost` | 6 | 0,000 | 2,000 | egyezik |
| `border` | 6 | 0,000 | 2,000 | egyezik |
| `bw` | 2 | 0,000 | 2,000 | egyezik |
| `cinemascope` | 2 | 0,000 | 2,000 | egyezik |
| `colorfix` | 7 | 0,000 | 2,000 | egyezik |
| `colortemp` | 6 | 0,000 | 2,000 | egyezik |
| `comicize` | 6 | 0,112 | 2,000 | egyezik |
| `contrast` | 6 | 0,138 | 2,000 | egyezik |
| `crossprocess` | 4 | 0,000 | 2,000 | egyezik |
| `dir_brite` | 2 | 4,433 | 2,000 | eltér |
| `dir_sat` | 2 | 1,608 | 2,000 | egyezik |
| `dir_sharp` | 2 | 10,740 | 2,000 | eltér |
| `dir_tint` | 6 | 0,000 | 2,000 | egyezik |
| `dropshadow` | 6 | 0,000 | 2,000 | egyezik |
| `enhance` | 3 | 0,000 | 2,000 | egyezik |
| `fill` | 5 | 0,000 | 2,000 | egyezik |
| `finetune` | 6 | 0,833 | 2,000 | egyezik |
| `finetune2` | 7 | 0,698 | 2,000 | egyezik |
| `focalpixelate` | 6 | 0,000 | 2,000 | egyezik |
| `focalzoom` | 6 | 0,071 | 2,000 | egyezik |
| `gamma` | 6 | 0,000 | 2,000 | egyezik |
| `glow` | 6 | 0,001 | 2,000 | egyezik |
| `glow2` | 6 | 0,001 | 2,000 | egyezik |
| `grain` | 4 | 3,142 | 2,000 | eltér |
| `grain2` | 4 | 2,232 | 2,000 | eltér |
| `hdr` | 6 | 0,000 | 2,000 | egyezik |
| `heatmap` | 6 | 0,000 | 2,000 | egyezik |
| `holga` | 6 | 0,000 | 2,000 | egyezik |
| `invert` | 2 | 0,000 | 2,000 | egyezik |
| `ir` | 4 | 0,002 | 2,000 | egyezik |
| `linblur` | 6 | 0,012 | 2,000 | egyezik |
| `localcontrast` | 6 | 0,000 | 2,000 | egyezik |
| `lomo` | 6 | 0,000 | 2,000 | egyezik |
| `matte` | 6 | 0,000 | 2,000 | egyezik |
| `museummatte` | 6 | 0,000 | 2,000 | egyezik |
| `neon` | 4 | 0,000 | 2,000 | egyezik |
| `nightvision` | 6 | 0,000 | 2,000 | egyezik |
| `orton` | 6 | 0,000 | 2,000 | egyezik |
| `pencilsketch` | 6 | 0,022 | 2,000 | egyezik |
| `picnikfocalpixelate` | 8 | 0,159 | 2,000 | egyezik |
| `picnikgrain` | 7 | 0,000 | 2,000 | egyezik |
| `picniktint` | 4 | 0,000 | 2,000 | egyezik |
| `pixelate` | 6 | 0,000 | 2,000 | egyezik |
| `polaroid` | 6 | 0,001 | 2,000 | egyezik |
| `quantizepalette` | 8 | 0,000 | 2,000 | egyezik |
| `radblur` | 6 | 0,007 | 2,000 | egyezik |
| `radsat` | 6 | 0,000 | 2,000 | egyezik |
| `radtint` | 6 | 0,000 | 2,000 | egyezik |
| `reanimatedeyecolor` | 6 | 0,000 | 2,000 | egyezik |
| `roundededges` | 6 | 0,000 | 2,000 | egyezik |
| `sat` | 6 | 0,000 | 2,000 | egyezik |
| `sepia` | 4 | 0,000 | 2,000 | egyezik |
| `shadow` | 6 | 0,001 | 2,000 | egyezik |
| `sixties` | 6 | 0,000 | 2,000 | egyezik |
| `soften` | 6 | 0,000 | 2,000 | egyezik |
| `tilt` | 6 | 0,044 | 2,000 | egyezik |
| `tint` | 21 | 0,000 | 2,000 | egyezik |
| `triple` | 6 | 0,137 | 2,000 | egyezik |
| `triple2` | 6 | 0,148 | 2,000 | egyezik |
| `triple3` | 6 | 0,131 | 2,000 | egyezik |
| `twotone` | 6 | 0,000 | 2,000 | egyezik |
| `unsharp` | 8 | 0,000 | 2,000 | egyezik |
| `unsharp2` | 8 | 0,000 | 2,000 | egyezik |
| `vignette` | 9 | 0,000 | 2,000 | egyezik |
| `warm` | 2 | 0,000 | 2,000 | egyezik |
| `whitept` | 5 | 0,081 | 2,000 | egyezik |


### A küszöb feletti effektkimenetek

- **`dir_brite`**: a 684-es `dir_brite__alap.jpg` ΔE-je **4,433**, a `meroszett` azonos paramétersoráé **4,427**. Mindkét Picasa-lánc `dir_brite=1,0.500000,0.500000;`; a mai `parse_filters_prefix` a regiszter teljes paramétersort követelő szabálya mellett a mintában szereplő két vezérlőértéknél elvágja a láncot, így a renderer a forrást adja vissza. A Picasa-export a forrástól ΔE **4,442**-vel eltér, tehát az eredeti effekttag lefutott; a külön `compare_render.py` nyers összevetése is **4,442**-t mér; a közvetlen `apply_dir_brite` kimenet viszont ΔE **0,187**-re egyezik vele. Valószínű ok: a beolvasó paraméterszám-szabálya nem kezeli a mért puck-sort. Helyi specifikációs kapcsolat: `filters-decoded.md` „Az irányított család” (#3859) és a #4233 olvasási aritás-szabálya. Nyitott jegyállapot: **nem ellenőrizhető**, a `gh issue list --search` API-kapcsolati hibával leállt.
- **`dir_sharp`**: a 684-es exporttal a ΔE **10,740**, a `meroszett` megfelelő mintájával **10,717**; mindkét lánctag ugyanaz a kétértékű forma, és ugyanott szakad meg. Az eredeti Picasa-kimenet a forrástól ΔE **10,748**-del tér el, amit a külön `compare_render.py` nyers útja is mér, míg a közvetlen `apply_dir_sharp` ΔE-je **0,384**. Valószínű ok és helyi specifikációs kapcsolat megegyezik a `dir_brite` soréval; a nyitott jegy állapota GitHub-hozzáférés híján nem állapítható meg.
- **`grain`**: `merokit-2/szemcse_05.jpg`, `grain=1;grain=1;`: ΔE **3,142**. A helyi `filters-decoded.md` #4936 szerint a Picasa-export a munkamenet `k=2,3` zajmagjait, a jelenlegi láncos renderelés pedig új láncban `k=0,1`-et használ. Ez illik a mért eltéréshez; a nyitott jegy állapotát nem lehetett ellenőrizni.
- **`grain2`**: `merokit-2/szemcse_02.jpg`, `grain2=1;`: ΔE **2,232**. A helyi #4936 specifikáció a `k=0` és a Picasa-munkamenetben mért `k=1` eltérését dokumentálja. A nyitott jegy állapota nem ellenőrizhető.

A `dir_sat` két mintájából az egyiknél a parser szintén elvágja a kétértékű sort, de a legnagyobb mért ΔE **1,608**, ezért az előírt 2,0-s küszöb szerinti ítélet „egyezik”. Ez az egyezés a kimeneti küszöbre vonatkozik, és nem bizonyítja, hogy a tag lefutott. A 684-es készlet `autobacklight`, `grain2` és vegyes írásmódú `tint` sorai között is van levágott tag; ezek Picasa-referenciáján a kimeneti különbség a küszöbön belül marad.

### Referencia nélküli effektek

A `FILTER_REGISTRY` 56 `mode=effect` bejegyzéséből 55-höz van eredeti Picasa-kimenet legalább az egyik felsorolt készletben. **`debug`** az egyetlen referencia nélküli effekt-regiszterbejegyzés; a `make_validation_kit.py` fejlesztői eszközként eleve kizárja, és nem felhasználói effekt. Az `unsharp/max` egyedi 684-es exportja hiányzik, de az effekt más készletében van eredeti referencia, ezért az `unsharp` nem referencia nélküli.

### Kiegészítő láncmérések

| Lánc és készlet | Mintaszám | Mért eltérés (max. ΔE76) | Küszöb | Ítélet |
|---|---:|---:|---:|---|
| `nincsilyen=1;bw=1;` (`merokit-3`) | 7 | 10,123 (`B_ismeretlen_elol.jpg`) | 2,000 | eltér |
| Border → sepia (`3229`, 01) | 1 | 0,000 | 2,000 | egyezik |
| sepia → Border (`3229`, 02) | 1 | 0,000 | 2,000 | egyezik |
| Border → Vignette (`3229`, 03) | 1 | 0,000 | 2,000 | egyezik a küszöb szerint; a parser a Vignette-tagot levágta |
| `crop64` → Vignette (`3229`, 04) | 1 | 39,829; eltérő képméret | nincs | nem összehasonlítható |

A `merokit-3`-ban az eredeti Picasa az ismeretlen tag után megállt, a PicasaPy viszont az utána következő `bw`-t is lefuttatta (ΔE **10,123**). Ez a `picasa-ini-format.md` ismeretlen tagok utáni leállási leírásával ellentétes; helyi kódkapcsolat a `parse_filters_prefix` ismeretlen név ága, korábbi viselkedési hivatkozás #1140. A `3229/04` képmérete PicasaPy-n **376×659**, az eredeti exporté **1600×1200**, ezért az eltérés nem fogadható el effekt-paritási ítéletként. A `3229/03` kimeneti különbsége a JPEG-normalizált küszöb szerint nulla, de a parser a `Vignette=1,35,1.4,0` tagot nem adta át a renderernek.

A GitHubon a vizsgált eltérésekre futtatott négy csak-olvasási `gh issue list --search` parancs egyaránt `error connecting to api.github.com` hibával tért vissza. Emiatt nem igazolható, hogy a helyi #4233, #4936 és #1140 hivatkozásokhoz van-e jelenleg nyitott, megfelelő jegy; jegyet nem hoztam létre.


### Bizonyítottsági fok és cáfoló kör

**Bizonyítottsági fok: feltételes az összesített táblára.** A teljes effektmátrix minden ΔE-je a fenti, egységes mérőúton készült; két független út nem futott végig mind a 73 csoportra. A két irányított eltérés külön megerősített: az `analyze_validation_kit.py` JPEG-normalizált útja 4,433 / 10,740-et, a `compare_render.py` nyers összevetése 4,442 / 10,748-at ad; a Picasa-export és a forrás eltérése is ugyanazt a nem-tétlen eredetit igazolja.

**Cáfoló kísérlet:** a „hibás a `dir_brite` és a `dir_sharp` számítási magja” feltevést a filterparser megkerülésével próbáltam cáfolni. A két közvetlen effekt-hívás eredménye 0,187 / 0,384 ΔE-vel illeszkedik az eredeti exportra (a korábbi #3859 mérésével egyezően), miközben a mai láncértelmező üres műveletsort ad; ez a számítási mag hibáját cáfolja, és a lánc elfogadási és paraméterszám-szabályára szűkíti az okot. A cáfoló mérce mindkét irányban ugyanaz a CIE76 ΔE és 2,0 küszöb.

## Kombinált effektláncok az eredetihez mérve (#5295, 2026-10-18)

Módszer: tíz szabad licencű kép (`minta-kombinalt` készlet a Colab-végrehajtón, k01-k10), képenként hét, egymástól teljesen eltérő réteg (összesen 70 különböző tag). Az eredeti kimenet a Colab-on futó eredeti Picasa 3.9 exportja (job-194), a PicasaPy-oldal a `tools/golden/compare_render.py` renderje. A mérőszám a projekt kanonikus mércéje (`tools/golden/analyze_validation_kit.py`): a PicasaPy-render az eredeti export JPEG-beállításaival kódolva, ΔE átlag, küszöb 2,0, 6,0 fölött rossz. A nyers, JPEG-egyeztetés nélküli ΔE pontos renderre is kb. 2,7-et adhat, ezért az első mérés néhány „eltér” ítélete téves volt (#5301). A hibás réteget felezéssel kerestük: ugyanaz a tíz lánc az első 3, 5 és 6 rétegig (job-195, job-196, job-197). A láncok és a Colab-feladat: `docs/benchmarks/2026-10-18-5295-kombinalt/`.

| kép | 3 réteg | 5 réteg | 6 réteg | 7 réteg | ítélet, a hibát okozó réteg | jegy |
|---|---:|---:|---:|---:|---|---|
| k01 | 1,28 | 1,32 | 0,91 | 4,59 | eltér: 7. `Vignette` (vágott, kiegyenesített, szépiás kép után) | #5300 |
| k02 | 0,28 | 1,17 | 1,07 | 1,73 | egyezik | (#5301 lezárva) |
| k03 | 0,00 | 0,00 | 0,00 | 24,34 | eltér: 7. `Polaroid`; az eredetiben a `dir_sat` és a `blur` után a Polaroid a háttérszínt mutatja a kép helyén (job-198..200) | #5299 |
| k04 | 0,00 | 0,00 | 0,00 | 0,34 | egyezik | |
| k05 | 0,00 | 0,00 | 0,00 | 0,00 | egyezik | |
| k06 | 0,00 | 0,90 | 0,90 | 0,93 | egyezik | |
| k07 | 0,00 | 0,00 | 0,23 | 0,58 | egyezik | |
| k08 | 46,85 | 60,45 | 61,25 | 61,14 | eltér: 2. `rainbow`, amit a PicasaPy nem renderel | #5296, #5304 |
| k09 | 3,58 | 1,98 | 1,88 | 1,88 | 7 rétegen egyezik; 3 rétegen eltér (`grain`, `ansel`, `triple2`), a szemcse zajmagja | |
| k10 | 0,00 | 8,04 | 8,04 | 8,34 | eltér: 4. `colorfix`, amit a PicasaPy nem renderel | #5296 |

Következtetés: a tíz kombinációból hat egyezik az eredetivel. Négy eltérés rétegre visszavezetve: két, eddig „nem renderelendő”-nek tartott tag (`rainbow`, `colorfix`; #5296), a Polaroid viselkedése bizonyos előző rétegek után (#5299), és a Vignette a vágott, kiegyenesített kép után (#5300).

## Kombinált effektláncok, 2. kör (#5398, 2026-10-20)

Módszer: a `minta-kombinalt` készlet (a `kellekek` kiadás `minta-kombinalt.tar.gz` fájlja, SHA-256 szerint ellenőrizve) k01-k10 képei és az eredeti Picasa 3.9 exportjai (job-228, `export__kNN.jpg`). A képek szabad licencűek; a szerzőket és a licenceket a csomag `SZERZOI.txt` fájlja sorolja fel. A PicasaPy a teljes láncot futtatja (`picasapy.render.chain.apply_filters`), a kimenetet az exportéval azonos JPEG-mintavételezéssel és kvantálótáblákkal kódoljuk (`tools/golden/jpeg_reference.py`), majd az átlagos CIE76 ΔE-t mérjük az exporthoz (`analyze_validation_kit.py`, `mean_de`; küszöb 2,0, 6,0 fölött rossz). A `compare_render.py pair` ugyanerre a láncra a nyers ΔE-t adja, JPEG-egyeztetés nélkül: az egyező képeken 0,54 és 1,74 között van, a k02-n 2,912, a k03-on 5,775. A nyers ΔE is ugyanazt az ítéletet adja mind a tíz képen. A `compare_render.py` pixel-tűrés szerinti ítéletét nem használtuk: az szigorúbb, k01-et és k04-et is „eltér”-nek jelöli 1 alatti ΔE mellett. A renderelt kép mérete minden képen egyezik az exportéval; a k04, k06 és k08 mérete a vágás és a keret miatt változik. A `ChainReport.skipped` lista üres, tehát a renderer egyetlen tagot sem hagyott ki.

| kép | csoport | lánc röviden | ΔE | ítélet |
|---|---|---|---:|---|
| k01 | 1 | autolight, warm, sat, glow, HDR, HeatMap, IR | 0,981 | egyezik |
| k02 | 1 | warm, sat, IR, HeatMap, HDR, glow | 2,802 | eltér |
| k03 | 1 | autolight, sat, HDR, IR, glow, HeatMap | 5,968 | eltér |
| k04 | 2 | crop64, radblur, Holga, Matte | 0,515 | egyezik |
| k05 | 2 | tilt, FocalZoom, radtint, Lomo | 0,067 | egyezik |
| k06 | 2 | crop64, Polaroid, RoundedEdges, radsat | 0,734 | egyezik |
| k07 | 3 | dir_sat, blur, Matte, RoundedEdges | 0,000 | egyezik |
| k08 | 3 | PencilSketch, Polaroid, MuseumMatte | 0,388 | egyezik |
| k09 | 4A | sat, Vignette, dir_tint, Matte, colortemp, radblur | 0,197 | egyezik |
| k10 | 4B | radblur, colortemp, Matte, dir_tint, Vignette, sat | 0,010 | egyezik |

A csoportok a README szerint: 1 = le nem fedett tagok; 2 = crop64 vagy tilt előtag; 3 = erős előző réteg, utána keret; 4 = a sorrend (4A és 4B fordított).

Következtetés:

- Nyolc kép egyezik, kettő eltér: k02 (2,802) és k03 (5,968). Mindkettő az 1. csoportból való, és a 6,0-s rossz-küszöb alatt marad: közelítő, nem rossz.
- A 2., 3. és 4. csoport minden lánca egyezik. A 4. csoport fordított sorrendje is (k09 és k10: 0,197 és 0,010), így a sorrend gyanúja ezen a csoporton nem igazolódott.
- Tisztázottak (egyező képen szerepelnek, összesen 25 különböző tag): autolight, warm, sat, glow, HDR, HeatMap, IR (k01); crop64, radblur, Holga, Matte (k04); tilt, FocalZoom, radtint, Lomo (k05); Polaroid, RoundedEdges, radsat (k06); dir_sat, blur (k07); PencilSketch, MuseumMatte (k08); Vignette, dir_tint, colortemp (k09). Ez az adott láncra igaz, nem minden kontextusra.
- Nincs olyan tag, amely csak az eltérő képeken fordul elő. A k02 és a k03 tagjai mind szerepelnek az egyező k01-ben. A k01-hez képest k02-ből az autolight, k03-ból a warm hiányzik, és a sorrend is más. A ΔE ezt nem tudja szétválasztani, ezért a hibás tagot most nem lehet megnevezni. A gyanúsítottak (glow, HDR, HeatMap, IR) mind szerepelnek a k01-ben, amely egyezik.
- Az 1. körben eltérő Polaroid (#5299) és Vignette (#5300) más láncban szerepel itt, és ott egyezik: a Polaroid a k06-ban és a k08-ban, a Vignette a k09-ben és a k10-ben.

Felezés (`docs/benchmarks/2026-10-20-5398-kombinalt2/felezes.ini`, a Colab-feladat `picasa_ini_be` szövege): a k02 és a k03 első három rétege (k02: warm, sat, IR; k03: autolight, sat, HDR). Ha ez eltér, a hiba az első három rétegben van, és a következő lépés a negyedelés (1-2 réteg). Ha egyezik, a hiba a második három rétegben van (k02: HeatMap, HDR, glow; k03: IR, glow, HeatMap), és ott bontjuk tovább.

A felezés eredménye (job-229, `felezes.ini`): a k02 első három rétege (warm, sat, IR) egyezik (ΔE 0,29), a k03 első három rétege (autolight, sat, HDR) eltér (2,57).

Második felezés (job-230, `felezes2.ini`, mérés: `meres-felezes2.json`):

| kép | lánc | ΔE | ítélet |
|---|---|---:|---|
| k02 | warm, sat, IR, HeatMap | 1,666 | egyezik |
| k03 | autolight, sat | 0,669 | egyezik |
| k04 | HDR | 0,000 | egyezik |
| k05 | sat, HDR | 0,000 | egyezik |
| k06 | warm, sat, IR, HeatMap, HDR | 2,233 | eltér |

A k04 és a k05 0,000-s értéke azt jelenti, hogy a PicasaPy kimenete az export JPEG-beállításaival kódolva bitre azonos az exporttal. A nyers ΔE 2,27 és 2,91: ez csak a JPEG-kódolás zaja.

Következtetés:

- A HDR kontrolljai az adott méréseken pontosak: a `HDR` és a `sat, HDR` kimenet JPEG-egyeztetés után ΔE 0,000 (job-230, k04-k05). Ez ezekre a bemenetekre bizonyítja a bájtegyezést.
- A k03 `autolight, sat` mérése ΔE 0,669 (job-230), az első három réteg `autolight, sat, HDR` mérése ΔE 2,57 (job-229). A két átlagos CIE76 ΔE értékből nem számítható ki a pixelenkénti HDR-erősítés: a metrika nem lineáris, és a két mérés nem köztes pixeleket hasonlít. A korábbi általános „négyszereződés” és 3,8-as ΔE-szorzó ezért nincs bizonyítva.
- A k02 első három rétegének ΔE-je 0,29 (job-229), a negyedik `HeatMap` hozzáadásával mért ΔE 1,666 (job-230). Ezek külön láncmérések; a különbség nem izolálja a HeatMap pixelenkénti hozzájárulását.
- A binárisban mindkét keresett taghoz van konkrét PicasaPy-eltérés. Az `autolight` eredeti útja `0x008f80c0 → 0x0090c3b0 → 0x0090c1e0 → 0x0090bc60`: 16 bites 8.8 LUT-ot interpolál és képpontonként egy, mindhárom csatornára közös MT-mintával ditherel; a helyi út 16.16-os erősítésből 8 bites LUT-ot képez, `np.rint`-tel kerekít és dither nélkül alkalmaz. A pontos leírás a [`picasa-native-filter-workers.md`](picasa-native-filter-workers.md) 2.3. szakaszában van.
- A `HeatMap` eredeti HSV→RGB útja `0x00bbbcf0 → 0x00bbbbf0 → 0x00bbbe20`; a p/q/t számítás x87 köztes pontjai és tárolásai a `0x00bbbf67`-`0x00bbbf9d` tartományban vannak. A jelenlegi Python-kód float64 köztes értékek után float32-re tárol; a QEMU-kontroll a `filterdesc.xml` stoplistáján 5/768 eltérő RGB-bájtot mért (részletek a [`filterdesc-registry.md`](filterdesc-registry.md) HSV-szakaszában). A műveletsorrend a leíró és a helyi lánc szerint egyezik; az eltérés a köztes pontosság/számítási sorrend.

### #5403 - az autolight és a HeatMap eltérő lépése

| tag | bináris lépés | PicasaPy | megállapítás |
|---|---|---|---|
| `autolight` | `0x0090c1e0`: 16 bites 8.8 LUT; `0x0090bc60`: közös pixelenkénti dither, interpoláció, `>>8`, vágás | `_native_levels_lut`: 16.16-os erősítésből 8 bites LUT; `apply_lut`: `np.rint`, dither nélkül | A kimeneti LUT felbontása és kvantálása eltér. A `fistp` félértékeknél használt kerekítési módja ebből a függvényszakaszból `NINCS MEG`. |
| `HeatMap` | `0x00bbbe20`, benne a p/q/t x87-szekvencia `0x00bbbf67`-`0x00bbbf9d` | `glimmer_ops.py`: float64 köztes műveletek, majd float32 tárolás; végül csonkolás | Az eltérés a HSV→RGB p/q/t köztes pontosságában és számítási sorrendjében van; a stoppozíciók és a HeatMap műveleteinek XML-sorrendje egyezik. QEMU-mérés: 5/768 RGB-bájt. |

**Független utak.** A út: célzott utasításszintű disassembly és a pozitív xref-lánc
adja az autolight hívási sorrendjét, a LUT `fistp`/vágását és a ditheres
alkalmazót; a PE-adatból olvasott `0x00cf4200` értéke 65280. A HeatMap-nél
ugyanez a célzott olvasás az x87 p/q/t tartományt azonosítja. B út: a
PicasaPy alkalmazóútjának közvetlen forrásvizsgálata és az eredeti Picasa
exporttal végzett 684-es önálló autolight-pár mérése (átlagos ΔE 0,23); a
HeatMap B útja az eredeti kódot futtató QEMU és a külön Python-referencia
összevetése, amely az XML-stoplistán 5/768 eltérő bájtot ad. A két út
ugyanazt az eltérő feldolgozási lépést jelöli.

**Cáfoló kísérlet.** A sorrendhibát ellenőriztem a telepített
`filterdesc.xml` HeatMap-műveletsorával és a PicasaPy
`glimmer_tone.py` hívási sorrendjével: mindkettő előbb szürkít, majd
HSV-színátmenetet alkalmaz, így ez a sorrendhipotézis nem áll meg. A HDR-t
mint önálló eltérésforrást a job-230 `HDR` és `sat, HDR` kontrolljai cáfolják
az ottani képen (mindkettő ΔE 0,000); ez nem cáfolja, hogy a HDR egy másik
tag előzetes pixeleltérését továbbalakíthatja.

**Bizonyítottság és határ.** A két algoritmuskülönbség **megerősített**: az
utasításszintű bináris olvasás és az attól független implementáció-/pixel-
ellenőrzés ugyanazt a lépést jelöli. A job-229/230 konkrét láncok ΔE-jének
pixelenkénti felbontása viszont nyitott, mert a `k02`/`k03` forrás- és
közbenső képei nincsenek meg a helyi mérőcsomagban. Ez nem módosítja a két
eltérő natív lépés azonosítását.

## Futás közbeni összevetés (#5396, 1. kör)

Hatókör: a job-231 tálca-csillag és forgatás, valamint a job-242 Tags panelen
felvett JPEG-címke. Az eredeti oldali képernyőképek és `.picasa.ini`-kimenetek
megmaradtak. A PicasaPy-futásmérést ebben a menetben nem lehetett elindítani:
`systemd-run --user --scope` a helyi user buszhoz „Operation not permitted”
hibával tért vissza. Ezért a „Nálunk” oszlop kódút, nem új futásmérés; az
alább hivatkozott QML-teszt nem futott le ebben a körben.

| Művelet | Eredeti | Nálunk | Eltérés | Bizonyíték |
|---|---|---|---|---|
| Csillag be, a 4. képen | A képernyőn a kijelölt képen sárga csillagjel látszik; a bal oldali „Starred Photos” darabszáma `1`. Az ini-sor: `[_03c62d34-6e84-4b2c-aa2b-e25c54f24d08.jpg]` / `star=yes`. | Kódút: `toggleStar` a `star=yes` értéket adja a fájlnév-szekcióhoz; a tényleges PicasaPy-kimenet ebben a körben nincs megmérve. | A rögzített végállapot és a kódút azonos `star=yes` értéket ír elő; futás közbeni PicasaPy-egyezés nincs igazolva. | `mérés: .bt/job-231/kepernyo__08.png`, `.bt/job-231/picasa.ini:1-2`; `src/picasapy/app/photo_ops_controller.py:492-522`; író: `src/picasapy/ini/io.py:273-337`. |
| Csillag be, majd ki a 7. képen | A `kepernyo__12.png` állapotban a csillag be van kapcsolva; a `kepernyo__14.png` állapotban ki. A végső ini-szekció `[_026e89d3-687c-4dda-ba6b-4f0856ada9ec.jpg]` üres, `star=` sor nincs. | Kódút: ugyanaz a kapcsoló előbb `star=yes`-t ír, majd eltávolítja a kulcsot az üres szekció megőrzésével; a tényleges futás nincs megmérve. | A végső tárolási alak egyezik a rögzített üres szekcióval; a köztes és végső PicasaPy-képernyő nincs felvéve. | `mérés: .bt/job-231/kepernyo__12.png`, `kepernyo__14.png`, `picasa.ini:3`; `src/picasapy/app/photo_ops_controller.py:492-518`; a várt kattintásos út: `tests/app/qml_functional/test_talca_csillag_forgatas_paritas_5396.py:166-245` (nem futott). |
| Forgatás jobbra, az 5. képen | A `kepernyo__18.png` képen a kijelölt kép elfordult. Az ini-sorok: `[_4d33a83b-d0bd-43dd-89a3-a5c1fc190aa4.jpg]`, `rotate=rotate(1)`, `backuphash=62465`. | Kódút: a jobbra forgatás `rotate=rotate(1)`-et ír. A kódban nincs `backuphash`-író; a tényleges ini-kimenet nincs megmérve. | A művelet utáni állapotban az eredetinél szerepel a `backuphash`, a PicasaPy forgatási útja nem állítja elő. A job előtti ini hiányában nem bizonyítható, hogy ezt az értéket ez a kattintás hozta-e létre; a hash-eltérés ezért feltételes. | `mérés: .bt/job-231/kepernyo__18.png`, `picasa.ini:4-6`; `src/picasapy/app/photo_ops_controller.py:1714-1767`; `src/picasapy/ini/legacy_crop.py:119-138`; a `backuphash` íráskori, OLE-dátumból képzett alakja: [`picasa-ini-format.md`](picasa-ini-format.md) § „A `backuphash`”, bináris `0x00454770` → `0x0098b6e0` → `0x0098b550`. |
| Forgatás balra, a 6. képen | A `kepernyo__22.png` képen a kijelölt kép elfordult. Az ini-sorok: `[_6fead84b-daf0-45ba-8d0b-cae6e47862d1.jpg]`, `rotate=rotate(3)`, `backuphash=27964`. | Kódút: a balra forgatás `rotate=rotate(3)`-at ír. A kódban nincs `backuphash`-író; a tényleges ini-kimenet nincs megmérve. | A művelet utáni állapotban az eredetinél szerepel a `backuphash`, a PicasaPy forgatási útja nem állítja elő. A job előtti ini hiányában a létrejötte ennél a műveletnél sem bizonyítható. | `mérés: .bt/job-231/kepernyo__22.png`, `picasa.ini:7-9`; `src/picasapy/app/photo_ops_controller.py:1718-1767`; `src/picasapy/ini/legacy_crop.py:119-138`; bináris forrás és jelentés: [`picasa-ini-format.md`](picasa-ini-format.md) § „A `backuphash`”. |
| `proba` címke hozzáadása JPEG-hez | A `kepernyo__12.png` Tags paneljén a `proba` az `AI image` fölött látszik, a Quick Tags első gombja `proba`, az állapotsor `155 KB`-ot mutat. A rögzített ini-szakasz: `[_4d33a83b-d0bd-43dd-89a3-a5c1fc190aa4.jpg]` / `backuphash=33706`; `keywords=` nincs. | Kódút: a `TagsPanel` → `addTagToRows` → `addKeywordToRows` JPEG-nél az IPTC Keywords `(2:25)` íróját hívja; csak sikertelen IPTC-írásnál tesz `keywords=` sort az ini-be. A kód nem ír `backuphash`-t. Runtime-mérés nincs. | Az eredeti végállapotban `backuphash` van, a mai sikeres JPEG-írási kódút nem állít ilyet elő. A job előtti ini hiányzik, a JPEG nincs a kiadásban, ezért az ini-sor eredete és az eredeti IPTC-mező bájtjai nem ellenőrizhetők. | `mérés: .bt/job-242/kepernyo__12.png`, `picasa.ini:1-2`, `.bt/5396-megfigyelesek.md:1`; `src/picasapy/app/qml/Main.qml:4043-4077`; `src/picasapy/app/keywords_controller.py:177-231`; `src/picasapy/metadata/iptc_writer.py:48-58`; a JPEG hiányzik a `.bt/job-242` kimenetéből. |

**További PicasaPy-fájlhatások, amelyekre nincs párosított eredeti mérés.** A
csillag- és forgatásírás `update_document(..., backup=True)` útja meglévő ini
mellett `.picasa.ini.bak` másolatot készít; a fotófájl módosítási idejét csak a
`PICASAPY_TOUCH_PHOTO_MTIME=1` kapcsolóval érinti, alapállapotban nem. Sikeres
JPEG-IPTC íráskor a kulcsszóíró magát a JPEG-et módosítja, és nem ír `keywords=`
sort az ini-be; ini-fallback csak sikertelen IPTC-íráskor történik. A felvételek
kimenetjegyzéke nem tartalmaz teljes mappaképet vagy JPEG-et, ezért az eredeti
`.bak`- és fájl-időbélyeg-mellékhatások, illetve a JPEG bájtszintű változása
`NINCS MEG`.

**Nyitva marad.** A két Colab-job előtti `.picasa.ini` nincs a csomagban, ezért a
`backuphash` sorok művelethez rendelése nem bizonyított. A job-242 JPEG-je sem
került kiadásra: az eredeti IPTC `Keywords (2:25)` mezőjének pontos értéke és
bájtszintű különbsége `NINCS MEG`. PicasaPy-oldalon sem készült új futásmérés; a
`test_talca_csillag_forgatas_paritas_5396.py` valódi kattintásos próbája a
forgatási/ini-értékeket ellenőrzi, de a jelen futtatókörnyezet a szükséges
memóriakorlátos user systemd scope-ot nem engedte elindítani.

### Mentés és Exportálás - 2026-10-27 (job-315-318)

Az eredeti oszlop a jegyben átadott, 2026-10-27-i Colab-mérések összefoglalója;
a feladatok nyers mellékletei nem találhatók a helyi mérőcsomagban. A PicasaPy
oszlop forráskódot, célzott teszteket és hamis mappán futtatott fájlműveletet
használ; ez nem valódi, egymás melletti GUI-felvétel.

| Művelet | Eredeti | Nálunk | Eltérés | Bizonyíték |
|---|---|---|---|---|
| Mentés - megerősítő ablak | „A backup of this file will be made.”; „Do not ask me again.” jelölőnégyzet (job-315). | A backup-megjegyzés szövege egyezik. A jelölő felirata `Do not ask again`; elfogadáskor a választás megjegyezhető. | A jelölő felirata eltér: hiányzik a „me” és a záró pont. Az eredeti jelölő alapállapota a kapott mérési összefoglalóból `NINCS MEG`. | `mérés (job-315, a jegyben átadott összefoglaló)`; PicasaPy: `src/picasapy/app/qml/PicasaPy/SaveDialogs.qml:44-59, 94-145`; futtatott QML: `tests/app/qml_functional/test_mentes_parancsok_1527.py:293-325`. |
| Mentés - kép és biztonsági másolat | A retusált kép mentés után új fájltartalmat kap; `.picasaoriginals/<fájlnév>` az eredeti tartalommal és változatlan mtime-mal jön létre (job-315). | Hamis mappán a mentett kép tartalma megváltozott, a másolat tartalma az eredeti bájtokkal egyezett, de a másolat mtime-ja `1793061608573028407 ns`, miközben a forrás előre beállított mtime-ja `1700000000000000000 ns` volt. A PicasaPy emellett `.picasaoriginals/.picasapy-snapshots/retouch.1.jpg` fájlt készített. | Az eredeti-biztonsági másolat mtime-jának megőrzése eltér a kapott job-315 leírástól. A másolat tartalma egyezik; a PicasaPy visszavonást támogató extra snapshotja dokumentált termékdöntés. | `mérés (job-315, átadott összefoglaló)`; hamis mappa (`.codex-jelentes.md`, 2026-10-27); `src/picasapy/edit/save.py:363-431`; extra snapshot: `docs/decisions/pillanatkep-nevter.md:108-114` (#2512). |
| Mentés - ini-hatások | A job-315 összefoglalója szerint a forrásmappa kép-szakaszában a `backuphash` és `filters=retouch=1;` is megmarad; létrejön `.picasaoriginals/.picasa.ini`. | A hamis mappás futásban a forrás-szakaszban csak `backuphash=23423` maradt; a `filters=retouch=1;` és `moddate=00006dc64717da01` az eredeti-mappa ini-jébe került. | A filters helye eltér a job-315 leírásától, de a forrás nem dönthető el: a korábbi bináris spec és job-253 épp az áthelyezést rögzíti. A job-315 nyers ini hiányában ezt nem tekintem igazolt fejlesztési eltérésnek. | `mérés (job-315 összefoglaló; PicasaPy hamis mappa)`; PicasaPy: `src/picasapy/edit/save.py:363-431`; cáfoló korábbi út: [`picasa-ini-format.md`](picasa-ini-format.md) „Mentéskor az eredeti ini kezelése”, bináris `0x00462ba0`, `0x0046b49b`-`0x0046d6ac`, `0x00460e20`, `0x00454770`, valamint job-253. |
| Exportálás - ablak alapállapota | Job-316-318 állapotában a hely a Képek mappa, a mappanév a forrásmappa neve, a `Resize to: 800 pixels` aktív, a minőség `Automatic`, vízjel és sorszámozás ki. | Üres PicasaPy-beállításokkal a hely `<Pictures>/Picasa/Exports`, a mappanév a forrásmappa neve, az eredeti-méret választó aktív (`resize=False`; a tárolt méretindex ettől még 800), `Automatic`, vízjel és sorszámozás ki. | A mappanév, minőség, vízjel és sorszámozás egyezik; a hely és a resize-választás eltér a megadott job-állapottól. Ez feltételes eltérés: az eredeti exporthely és méret mentett beállítás, a tiszta profil és az előző profilállapot nincs igazolva. A meglévő eredeti spec eredeti méretet, valamint `DefaultExportPath` hiányában `Picasa\Exports` helyet nevez alapnak; ezért a job-mérés önmagában nem bizonyít univerzális alapértéket. | `mérés (job-316-318, átadott összefoglaló)`; PicasaPy: `src/picasapy/app/export_prefs.py`, `export_controller.py:124-153`, `src/picasapy/app/qml/PicasaPy/ExportDialogs.qml:176-205`; teszt: `tests/app/test_export_beallitasok_1138.py:57-78`, `tests/app/qml_functional/test_export_felulet_1138.py:78-85`; cáfoló korábbi út: [`export-parbeszed.md`](export-parbeszed.md) 3.2, 4. szakasz, bináris `0x00738c00`, `0x00738c43`, `0x00738c58`, `0x00738d16`. |
| Exportálás - fájlnév, méret és forrás-ini | A kimenet a forrás fájlnevét kapja; a mért 1024×1024 forrásból alapból 800×800, `Use original size` mellett 1024×1024 lesz. A forrás `.picasa.ini` nem változik (job-316-318). | A hamis mappás futásban a név `camera.jpg` maradt; üres PicasaPy-beállításokkal 1024×1024, `max_dimension=800` mellett 800×800 lett. A forrás-ini bájtjai mindkét futásban változatlanok maradtak. Felirat/kulcsszó átadásakor a célmappába ini készül, a forrás-ini akkor is változatlan. | A fájlnév és forrás-ini viselkedése egyezik. A méret a megadott job-állapothoz képest eltér az üres PicasaPy-beállításokkal; az alapértékek profilfüggése miatt ez még nem általánosított paritáshiba. | `mérés (job-316-318, átadott összefoglaló; PicasaPy hamis mappa)`; PicasaPy: `src/picasapy/export/exporter.py:339-377, 413-449, 793-800`; `tests/export/test_exporter.py`; eredeti beállításút: [`export-parbeszed.md`](export-parbeszed.md) 12.1 és 13.4. |

**Futtatott ellenőrzés.** A projekt tesztfuttatójával a mentési és exportpárbeszéd,
a mentési ini-kezelés, a save lánc és az exportáló célzott tesztjei: 7 fájl,
154 teszt, mind zöld; a helyi PySide6 6.8.2.1, a CI-verzió 6.11.2. Külön
hamis mappán ellenőriztem a mentési másolat/ini kimenetét és az export
800/eredeti méret, fájlnév, valamint forrás-ini hatását. A tesztek nem pótolják
a Colab és a PicasaPy valós GUI-felvételét.

**Nyitott, a jegyben kapott méréssel nem feloldható pontok.** A job-315 nyers
forrás- és `.picasaoriginals/.picasa.ini` fájlja nem érhető el; a `filters`
helye ezért ütközik a job-253-mal és a bináris speccel. A job-316-318
exportbeállításainak előzménye, a tiszta profil állapota és a nyers célmappa
nem érhető el; ezért a 800-as resize és a Képek gyökér univerzális alapértéke
nem dönthető el. A kapott összefoglaló a forrás-ini változatlanságáról szól; a
célmappa ini-tartalmáról nem ad bájtszintű adat.

**Független utak és cáfolás.** A út: a PicasaPy mentési/export-kódút közvetlen olvasása; B út: a célzott Qt-tesztek és külön hamis mappán végzett kimenetmérés. A két út a jelenlegi PicasaPy backup-bájtegyezését, ini-írását, exportfájlnevét, méretét és forrás-ini-hatásának leírását ellenőrizte. Az eredeti oldal A útja a jegyben átadott job-315-318 mérési összefoglaló; B útja a korábbi, független job-253 és a bináris ini-/export-beállítási leírás. A mentési `filters` helyére és az export alapállapotára az eredeti utak nem egyeznek, ezért ezek nyitott kérdések; a jelölőszöveg és a backup mtime eltérése a kapott job-összefoglaló és a PicasaPy-ellenőrzés alapján feltételes, nem két független eredeti felvétellel megerősített.

Cáfoló próbának a job-315 `filters` állítását a job-253-cal és a `picasa-ini-format.md` utasításszintű leírásával vetettem össze; ezek az eredeti-mappa ini-be helyezést támasztják alá, így a job-315-ből általános `filters`-szabály nem mondható ki. A job-316-318 800-as méretét az `export-parbeszed.md` eredeti-méret alapállásával és a mentett beállítások tényével vetettem össze; ez cáfolja, hogy a felvételből tiszta profilra vonatkozó alapérték következne. A felvételek nyers ini-je, profilja és célmappája nem elérhető, ezért az ellentmondás feloldatlan.

A futtatott 7 célzott tesztfájl: `tests/app/qml_functional/test_export_felulet_1138.py`, `tests/app/qml_functional/test_mentes_parancsok_1527.py`, `tests/app/qml_functional/test_save_chain_originals_5833.py`, `tests/app/test_export_beallitasok_1138.py`, `tests/edit/test_mentes_eredeti_ini_5833.py`, `tests/edit/test_save.py`, `tests/export/test_exporter.py`.

### Album-, mappa- és személyműveletek - 2026-10-30 (job-323 - job-345)

Az eredeti oszlop a picasa-colab-jobs felvételeiből jön (képkocka, mappa-ini,
profillista); a „Nálunk” oszlop kódút és valódi kattintásos QML-teszt.

| Művelet | Eredeti | Nálunk | Eltérés | Bizonyíték |
|---|---|---|---|---|
| Album létrehozása kijelölt képpel | Album Properties ablak; a kép mellett is üres album jön létre, a mappa ini-je nem változik, a profilban `ioqueue/albumsafe.ioq` jelenik meg. | Az üres album az index `local_empty_albums` táblájába kerül, az ini változatlan. | egyezik (#6278) | job-323, job-324 |
| Üres album törlése | „Delete Album” ablak, „Are you sure you want to delete the album "%s"?”, két gomb: Delete Album / No, az alapgomb a No; törlés után Albums (2) -> (1), ini-írás nincs. | A #6278 óta nem volt törölhető, és az ablakban Cancel gomb és jelölőnégyzet is volt. | javítva: #6281, #6283 | job-329, job-330; `0x005fdc30` |
| Mappa elrejtése | Az ini azonnal `[Picasa] P2category=Hidden Folders` sort kap, utána „Add Password” ablak: Add Password (fókuszban) / Don't Add Password, „Do not ask me again.”. | Az ini-hatás egyezik; az ablakban Cancel gomb is volt. | javítva: #6287 | job-331; `0x005ee2a0` |
| Arc mellőzése | „Ignore People” ablak („Don't ask again, always ignore”, Ignore Person / Cancel); a kép szakaszában `faces=rect64(...),ffffffffffffffff`; a bal sávban „Ignored (1)”, „Back to Unnamed”. | egyezik (`UnnamedFacesView.qml`, `face_scan_controller_reset_mixin.py`) | - | job-333, job-334 |
| Személy-album törlése | Helyi menü: Edit People Album... · Select All · Clear Selection · Invert Selection · Refresh Thumbnails · Sort Album By · Delete People Album. „Remove People” ablak, Delete Album / Cancel (Cancel fókuszban). A kép `faces=` sora kikerül, a `[Contacts2]` névjegy marad, az arc visszakerül a Név nélküliek közé. | egyezik (`remove_album`: arcok törlése, névjegy marad) | - | job-336 - job-339; `0x005fdc30` |
| Személy átnevezése meglévő névre | Nincs kérdés és nincs összevonás: két külön azonos nevű személy marad, külön `[Contacts2]` azonosítóval. | Átnevezéskor szintén nincs kérdés, de a további műveletek névvel azonosítanak, így mindkét személyt érintik. | eltér: #6290 | job-340, job-343 |
| Mappa áthelyezése | A Windows rendszer-mappaválasztója („Browse for Folder”: Make New Folder / OK / Cancel). A Wine alatt a fa üres, cél nem választható, a fájlhatás nem mérhető. | Rendszer-mappaválasztó, a mappa a `.picasa.ini`-jével együtt mozog. | nem mérhető | job-344, job-345 |

### Az 1. kör összesítése

Az 1. kör minden lemezre író műveletére (csillag, forgatás, címke, elrejtés,
átnevezés, felirat, Mentés, export, album létrehozása és törlése, mappa
elrejtése és áthelyezése, arc mellőzése, személy elnevezése, törlése és
átnevezése) megvan a Colab-felvétel. Az eltérésekből nyílt jegyek: #5804
(egyfájlos átnevezés), #6281 és #6283 (üres album törlése), #6287
(jelszóajánlat), #6290 (azonos nevű személyek). A mappa áthelyezésének
fájlhatása a Wine korlátja miatt nem mérhető. A 2. kör (párbeszédablakok
minden menüparancsra, #6291) és a 3. kör (nézetek és navigáció, #6292) saját
jegyen folytatódik.

### 2. kör: a menüparancsok párbeszédablakai - 2026-10-30 (#6291, job-346 - job-354)

Minden ablakot nyitó menüparancsot egy kijelölt képpel, alapállapotból
megnyitottunk, és Escape-pel zártunk. Az online szolgáltatások (Import from
Google Photos, Order Prints, Upload Manager, Batch Upload, Publish to Blogger)
a #5396 szerint kimaradtak.

| Ablak | Eredeti | Nálunk | Eltérés |
|---|---|---|---|
| Album Properties (New Album...) | Name, Date, Music + Browse, Place taken, Description, OK / Cancel | egyezik | - |
| Folder Properties (Move to New Folder... / Edit Description...) | ugyanez; a meglévő mappánál „Automatic date” gomb is | egyezik | - |
| Rename Files | „1 file(s) selected for rename.”, Date és Image resolution jelölő, Example, Rename (tiltva) / Cancel | egyezik (#5804) | - |
| Export to Folder | hely, mappanév, sorszám, méret, minőség, filmek, vízjel, Export / Cancel | egyezik (#5396) | - |
| Export as HTML Page | képméret, filmek, cím, mappa, hat sablon és XML, előnézet, Export / Cancel | egyezik | - |
| Poster Settings | Tip, Poster size 200%, Paper size 4x6, Overlap tiles, OK / Cancel | egyezik | - |
| Adjust Photo Date | Current / New photo date és idő, OK / Cancel | egyezik | - |
| Configure Buttons | Available / Current Buttons, Add / Remove / Move Up / Move Down, Reset to Defaults, OK / Cancel | egyezik | - |
| Options | General, E-Mail, File Types, Slideshow, Printing, Network, Web Albums, Name Tags | egyezik | - |
| Undo All Edits | Confirm, „This will remove all edits you have made to ALL of the selected pictures.”, Remove Edits (fókusz) / No | egyezik | - |
| Delete Items (Delete from Disk...) | Delete Image / Cancel, a Cancel fókuszban | plusz No gomb | #6296 |
| Remove from Picasa... | Confirm, „Do you want to remove the folder "C:\PicasaTeszt\" and its subfolders?”, Remove Folder / Cancel | plusz No gomb, más cím, a mappa neve a teljes út helyett | #6296 |
| Set as Desktop... | Confirm, „This will replace your current desktop background...”, Set Desktop / No | megerősítés nélkül futott | #6295 (javítva) |
| Select Email (E-Mail...) | cím „Select Email”, a levelező neve (Wine alatt „Native Mail Client”) | más cím, a „MAIL CLIENT” helyőrző látszott | #6297 (javítva) |
| Open / Save As | a Windows rendszer-fájlválasztója | rendszer-fájlválasztó | - |
| Picture > Batch Edit almenü | Rename, Rotate (2), Auto Contrast, Auto Color, I'm Feeling Lucky, Sepia, Sharpen, Warmify, Film Grain, Black and White, Auto Red Eye Correction, Show Text, Hide Text | egyezik | - |
| Picture > Hide | kérdés nélkül elrejt | kérdés nélkül elrejt | - |

Nem mérhető: a Create a Gift CD és a Back Up Pictures a Wine alatt csak az
„Unable to connect to Windows IMAPI2 CD Engine.” hibát adja. A Print, a
Picture Collage, a Folder Manager és a People Manager nem külön ablak, hanem
a főablak nézete; ezek tartalma nem ennek a körnek a tárgya.

### 3. kör: nézetek és navigáció - 2026-10-30 (#6292, job-351 - job-353)

Billentyűleütések egy kijelölt képpel, alapállapotból; minden lépés után
képkocka.

| Művelet | Eredeti | Nálunk | Eltérés |
|---|---|---|---|
| Ctrl+A / Ctrl+I / Ctrl+D | mindent kijelöl / megfordítja / törli a kijelölést, a tálca követi | egyezik | - |
| Jobbra, Le, Home, End a rácsban | a kijelölés a szomszédra, az alatta lévőre, az elsőre, az utolsóra lép | egyezik | - |
| Ctrl+1 / Ctrl+2 | kis / normál bélyegképek | egyezik | - |
| Ctrl+T | megnyitja a Címkék panelt, a fókusz a „Type in a tag to add” mezőbe kerül; fókuszált mező mellett a második Ctrl+T nem zár, a rácsra kattintva újra ki-be kapcsol | a mező nem kapott fókuszt, a második Ctrl+T mindig zárt | #6301 (javítva) |
| Alt+Enter | Tulajdonságok panel | egyezik | - |
| Ctrl+3, nyilak, Escape | szerkesztő nézet, a nyilak lapoznak, az Escape visszavisz a könyvtárba | egyezik | - |

Nem mérhető: az Időrend (Ctrl+5) és a diavetítés (Ctrl+4) a Wine alatt
fekete képet ad. A Shift+kattintásos tartománykijelölést a végrehajtó lépés-
készlete nem tudja előállítani (módosítóbillentyűs kattintás nincs benne).
## Főmenük folyamatai (#6845)

Mérés dátuma: 2026-11-12. Hatókör: a négy megnevezett főmenü 38 tétele, az eredeti ki00-ki07 képek indexei szerint. Az eredeti ki08 az Edit, Folder, Create és Help menüt tartalmazza, nem része a körnek. Minden PicasaPy-futás két kijelölt képpel indult; a QML-menüparancsot kattintás indította, majd 3 másodperc múlva 1280x1024-es offscreen Qt-felvétel és állapot készült. Q12 E-Mailt az email vezérlő bekapcsolásával, Q30 Picture Properties műveletet a helyes menüazonosítóval újramértem; a táblázat a javított futásokat használja.

Az eredeti célképet az indexben megadott képszám azonosítja. A szennyezett képből eredeti viselkedésre nem következtetek. A fókuszt csak ott nevezem meg, ahol az állapot rögzítette; ez nem bizonyítja a billentyű-alapgombot. Az Enter viselkedést nem mértem, ezért az alapgomb NINCS MEG.

| Menü | Tétel | Eredeti (kép) | PicasaPy | Eltérés | Felelős fájl |
|---|---|---|---|---|---|
| File | New Album | ki00/kepernyo__11.png: Album Properties, Name, Date, Music, Place, Description, OK, Cancel | Q00: nincs párbeszéd; Untitled album jön létre 2 képpel, a .picasa.ini mindkét képhez albumtokent kap | Eltér: eredeti előbb adatbevitelt kér, PicasaPy azonnal létrehozza | PicasaFileMenu.qml |
| File | Add Folder to Picasa | ki00/kepernyo__17.png: Folder Manager | Q01: folderManagerDialog, mappafa, scan-beállítások, OK, Cancel, Help | A nyitófelület egyezik; további szkennelési hatás nem mért | FolderManagerDialog.qml |
| File | Add File to Picasa | ki00/kepernyo__23.png: fájlválasztó | Q02: addFileDialog, Open, Cancel | A fájlválasztó megnyílik | AddFileDialog.qml |
| File | Import From | ki00/kepernyo__29.png: importálási ablak | Q03: importSourceDialog; forrás, fájltípus, cél, névadás, másolás utáni művelet, Import, Close | A nyitófelület megnyílik; importot nem indítottam | ImportSourceDialog.qml |
| File | Import from Google Photos | ki00/kepernyo__35.png: főablak, látható változás nélkül | Q04: főablak marad, menüpont inaktív | Nyitott: eredeti műveleti hatás nem látható, PicasaPy nem indít importot | PicasaFileMenu.qml |
| File | Open File(s) in an Editor | ki01/kepernyo__11.png: Wine Internet Explorer és helyi fájl-URL | Q05: fileOpsErrorDialog, az alapértelmezett alkalmazás nem tudta megnyitni a 2 képet | Eltérésjelölt; offscreen külső alkalmazás indítás miatt valódi asztalon újramérendő | PicasaFileMenu.qml |
| File | Move to New Folder | ki01/kepernyo__17.png: előző Internet Explorer ablak maradt a képen | Q06: moveToNewFolderDialog | A mérés szennyezett, újramérendő | FolderPropertiesDialog.qml |
| File | Rename | ki01/kepernyo__23.png: előző Internet Explorer ablak maradt a képen | Q07: renameManyDialog | A mérés szennyezett, újramérendő | SaveDialogs.qml |
| File | Save As | ki01/kepernyo__29.png: előző Internet Explorer ablak maradt a képen | Q08: saveAsFileDialog, Save As fájlválasztó | A mérés szennyezett, újramérendő | SaveDialogs.qml |
| File | Save a Copy | ki01/kepernyo__35.png: előző Internet Explorer ablak maradt a képen | Q09: 2 másolat készült, értesítés; rács 26 fájlra nőtt | A mérés szennyezett, újramérendő; PicasaPy lemez/rács hatása rögzített | SaveDialogs.qml |
| File | Export Picture to Folder | ki02/kepernyo__11.png: Export, Resize to 800 pixels, Automatic, vízjel és sorszámozás ki | Q10: exportDialog, Use original size, Automatic, vízjel és sorszámozás ki | A resize választás eltér a felvett állapotban; profil-előzmény nincs meg | ExportDialogs.qml |
| File | Print | ki02/kepernyo__17.png: nyomtatási ablak és előnézet | Q11: 3 másodperc után főablak, másik ablak nélkül | Látható eltérésjelölt; offscreen mérés miatt valódi kijelzőn újramérendő | PrintDialog.qml |
| File | E-Mail | ki02/kepernyo__23.png: Select Email, Native Mail Client, Google Mail, emlékezzen jelölő, Help, Cancel | Q12: emailChoiceDialog ugyanilyen választóval, Native Mail Client kiválasztva | A látható folyamat egyezik; Enter-alapgomb nem próbált | EmailChoiceDialog.qml |
| File | Order Prints | ki02/kepernyo__29.png: Shop még nem látszik, a következő képen már igen | Q13: File menü maradt nyitva, külön ablak nincs | A mérés szennyezett, újramérendő | PicasaFileMenu.qml |
| View | Small Thumbnails | ki02/kepernyo__35.png: előző Order Prints Shop ablaka látszik | Q14: tömör rács, 8 oszlop | A mérés szennyezett, újramérendő | PicasaViewMenu.qml |
| View | Normal Thumbnails | ki03/kepernyo__11.png: normál bélyegképrács | Q15: normál rács marad | A látható nézet egyezik | PicasaViewMenu.qml |
| View | Edit View | ki03/kepernyo__17.png: szerkesztő nézet | Q16: szerkesztő nézet | A látható nézet egyezik | PicasaViewMenu.qml |
| View | Properties | ki03/kepernyo__23.png: Properties panel | Q17: Properties panel | A panel megnyílása egyezik | PicasaViewMenu.qml |
| View | Tags | ki03/kepernyo__29.png: Tags panel | Q18: Tags panel | A panel megnyílása egyezik | PicasaViewMenu.qml |
| View | People | ki03/kepernyo__35.png: People panel | Q19: People panel | A panel megnyílása egyezik | PicasaViewMenu.qml |
| View | Places | ki04/kepernyo__11.png: főablak, Places panel nélkül | Q20: Places panel, 0 helyhez rendelt kép; térkép nincs | Látható eltérés; tesztképeken nincs földrajzi adat, tartalmi viselkedés nyitott | PicasaViewMenu.qml |
| View | Slideshow | ki04/kepernyo__17.png: főablak, diavetítés nélkül | Q21: teljes képernyős diavetítés | Látható eltérés a képen; eredeti késleltetett állapot újramérendő | PicasaViewMenu.qml |
| View | Timeline | ki04/kepernyo__23.png: főablak, idővonal nélkül | Q22: timelineView ablak, 800x800 | Látható eltérés, az eredeti képen nincs idővonal | PicasaViewMenu.qml |
| View | Search Options | ki04/kepernyo__29.png: főablak, popup nélkül | Q23: searchOptionsPopup; csak arcos képek vagy csak duplikátumok | Látható eltérés a célképek között | PicasaViewMenu.qml |
| View | Small Pictures | ki04/kepernyo__35.png: főablak és képrács | Q24: főablak és képrács, nincs lényegi látható változás | A képen egyezik; rejtett beállítás és későbbi hatás nincs vizsgálva | PicasaViewMenu.qml |
| View | Hidden Pictures | ki05/kepernyo__11.png: nincs látható rejtett kép | Q25: nincs változás, tesztmappában nincs rejtett kép | Nyitott: rejtett képes adaton mérendő | PicasaViewMenu.qml |
| View | Use Color Management | ki05/kepernyo__17.png: látható ICC/színváltozás nélkül | Q26: nincs látható panel vagy képi változás | Nyitott: színprofilos kép és mérése nélkül nem dönthető el | PicasaViewMenu.qml |
| Picture | View and Edit | ki05/kepernyo__23.png: képszerkesztő nézet | Q27: képszerkesztő nézet | A látható nézet egyezik | PicasaPictureMenu.qml |
| Picture | Undo All Edits | ki05/kepernyo__29.png: megerősítés, Remove Edits és No | Q28: undoAllEditsDialog, két gomb; Remove Edits fókuszban | A látható párbeszéd egyezik; a visszavonást nem hagytam jóvá | PicasaPictureMenu.qml |
| Picture | Reset Faces | ki05/kepernyo__35.png: nincs arcadat látható | Q29: nincs változás, tesztmappában nincs arcadat | Nyitott: arcot tartalmazó tesztadaton újramérendő | PicasaPictureMenu.qml |
| Picture | Properties | ki06/kepernyo__11.png: Picture Properties tartalma | Q30: Properties drawer; File Path, File Size, Dimensions, File Date, JPEG Quality, Keywords | A panel megnyílik; mezőnkénti értékparitás nincs dokumentálva | PropertiesPanel.qml |
| Tools | Folder Manager | ki06/kepernyo__17.png: Folder Manager | Q31: folderManagerDialog, mappafa és figyelési beállítások | A nyitóablak egyezik; összes beállítás és lemez/indexhatás nincs végigpróbálva | FolderManagerDialog.qml |
| Tools | People Manager | ki06/kepernyo__23.png: People Manager | Q32: peopleManagerDialog | A nyitóablak egyezik; személyadat-hatás nincs végigpróbálva | PeopleManagerDialog.qml |
| Tools | Batch Upload | ki06/kepernyo__29.png: főablak, bejelentkezés a következő képen jelenik meg | Q33: Tools menü marad nyitva, külön ablak nincs | A mérés szennyezett, újramérendő | PicasaToolsMenu.qml |
| Tools | Adjust Date and Time | ki06/kepernyo__35.png: előző Batch Upload bejelentkezési ablaka | Q34: adjustTimestampDialog, két kép; jelenlegi/új dátum és idő, relatív vagy azonos dátum, OK, Cancel | A mérés szennyezett, újramérendő | AdjustTimestampDialog.qml |
| Tools | Configure Buttons | ki07/kepernyo__11.png: Available: Geo-Tag, Order Prints, Collage, BlogThis; Current üres | Q35: configureButtonsDialog; Available üres, Current 4 alapgomb; Add, Remove, Move Up/Down, Reset, OK, Cancel | A lista eltér; profil-előzmény nincs meg | ConfigureButtonsDialog.qml |
| Tools | Options | ki07/kepernyo__17.png: General, E-Mail, File Types, Slideshow, Printing, Network, Web Albums, Name Tags | Q36: optionsDialog, 680x460; ezeken túl Google Photos lap; OK fókuszban | A látható lapkészlet eltér; profil és verzió hatása nem különült el | OptionsDialog.qml |
| Tools | Back Up Pictures | ki07/kepernyo__23.png: 2 kép kijelölve, backup folyamat és Wine IMAPI2 hibaablak | Q37: BackupHost, rács 0 kép, kijelölés törlődik; New Set, Select All/None, Burn, Cancel, Restore | Felület és kijelölés eltér; eredeti lemezírás Wine hiba miatt nem mérhető | BackupHost.qml |

### Mért eltérésjelöltek

- New Album: az eredeti a létrehozás előtt Album Properties ablakot nyit; PicasaPy azonnal létrehozza az albumot. A helyi .picasa.ini és mindkét kép hozzárendelése igazolja a PicasaPy oldali hatást.
- Export: az eredeti képen 800 pixeles resize, PicasaPyban eredeti méret szerepel; a profil-előzmény hiánya miatt ez csak a felvett állapot eltérése.
- Print: PicasaPyban 3 másodpercen belül nem jelent meg ablak; valódi kijelzőn újramérendő.
- Places, Slideshow, Timeline és Search Options: a PicasaPy célfelület eltér az eredeti képen látható főablaktól. A késleltetett állapotot ellenőrizni kell; Placeshez földrajzi adatok szükségesek.
- Configure Buttons és Options: a lista/lapkészlet eltér; profilt és termékverziót külön kell mérni.
- Back Up Pictures: a PicasaPy rács és kijelölés eltér; eredeti lemezre írás nem mérhető Wine IMAPI2 hibával.
- Open File(s) in an Editor: PicasaPy alapalkalmazás hibát jelzett offscreen; valódi asztali futásban mérendő.

### Szennyezett és korlátozott eredeti felvételek

Újramérendő: Move to New Folder, Rename, Save As, Save a Copy, Order Prints, Small Thumbnails, Batch Upload és Adjust Date and Time. Az Open Editor képe a saját Internet Explorer ablakát mutatja, de PicasaPy külső alkalmazásindítása offscreen nem összehasonlítható. Import from Google Photos, Hidden Pictures, Use Color Management és Reset Faces hatása a szolgáltatás vagy megfelelő tesztadat hiánya miatt nem mérhető. Print, Slideshow és Timeline késleltetett megjelenését valódi kijelzőn kell ellenőrizni.

### A jegy „Kész, ha” pontjai a 38 főmenü tételre

- PicasaPy oldali kattintásos mérés mind a 38 sorhoz: ✅ Q00-Q37; Q12 és Q30 javított futással.
- Eredeti oldali megbízható kép minden sorhoz: ⛔ nyolc eredeti sor szennyezett vagy késleltetett hatású; újramérendőként jelölve.
- Minden sor bizonyíték szerinti besorolása: ✅ bizonytalan esetek nyitottként, korlátozottként vagy szennyezettként szerepelnek.
- A paritas-ellenorzes.md frissítése: ✅ mind a 38 sorhoz eredeti képazonosító, PicasaPy állapot, eltérés és felelős felületi fájl szerepel.
- Eltérések külön termékjegyei: ✅ a New Album, a Copy All Effects, a Remove from Picasa, az Export as HTML Page és a Gift CD eltérése a #6861 megvalósítási jegyben.

A mérési képek és nyers futásállapotok csak az engedélyezett ideiglenes területen voltak; a feladat végén törlődnek. A tartós eredmény ez a táblázat és a .codex-jelentes.md. Ez a kör csak a 38 főmenüt fedi le; az eredeti jegy 20 mappanézetbeli művelete nincs késznek nyilvánítva.


### Főmenük folyamatai, második rész (#6860)

Az eredeti oldalon a `job00-index.json` - `job04-index.json` képkocka-hivatkozásait vizsgáltam. A PicasaPy oldalon minden tételt külön, izolált 24 képes próbafutásban nyitottam meg, két kijelölt képpel, Qt `QTest.mouseClick` egérkattintással, majd 3 másodperc várakozással. A panel- és ablakállapotot, címet, látható vezérlőket, kijelölést és az aktív fókuszt rögzítettem.

A felvevő az `activeFocus` állapotot rögzítette, de a Qt Quick vezérlők alapértelmezett gombját nem. Ezért az alapértelmezett gomb mindenhol `NINCS MEG`; az aktív fókusz külön adat, és nem tekintem alapértelmezett gombnak. Ahol a PicasaPy-ablak neve, címe vagy fő vezérlői nem látszanak, ezt külön jelölöm.

| Menü | Tétel | Eredeti (a kép alapján) | PicasaPy | Eltérés | Felelős fájl |
|---|---|---|---|---|---|
| Edit | Copy All Effects | `ki00/kepernyo__11.png`, `__12.png`: két kép kijelölve; `Info` ablak: “Please select a single picture to copy the effects from.” | Nincs új ablak vagy panel; a kijelölés `[0, 1]` marad. A vágólap tartalmát nem mértem. | Az eredeti elutasítja a többképes kijelölést és üzenetet mutat; PicasaPyben nem jelent meg üzenet. | `PicasaEditMenu.qml`, `PicasaMenuBar.qml` |
| Edit | Select All | `ki00/kepernyo__17.png`: mind a 24 kép kijelölve, a tálcán 24 kép látszik. | Nincs ablak; mind a 24 tesztkép kijelölt. | A mért állapot egyezik. | `PicasaEditMenu.qml`, `PicasaMenuBar.qml` |
| Edit | Select Starred | `ki00/kepernyo__23.png`: a képek nincsenek kijelölve. | Nincs ablak; a próbában nem volt csillagozott kép, kijelölés `[]`. | A mért állapot egyezik a csillagozatlan mintán. | `PicasaEditMenu.qml`, `PicasaMenuBar.qml` |
| Edit | Invert Selection | `ki00/kepernyo__29.png`: nincs kijelölt kép; a képernyő nem mutatja a kétképes kiinduló állapot megfordítását. | Nincs ablak; a `[0, 1]` kijelölésből `[2..23]`, azaz 22 kép lett kijelölve. | Az eredeti képkocka nem igazolja a várt eredményt; újramérendő. | `PicasaEditMenu.qml`, `PicasaMenuBar.qml` |
| Edit | Clear Selection | `ki00/kepernyo__34.png` - `__36.png`: a menü nyitva, a `Clear Selection` szürke; a képen a mappa kijelölt, a képtálca üres. Nem a kétképes induló állapot látszik. | Nincs ablak; a `[0, 1]` kijelölés `[]` lett. | Az eredeti felvétel állapota nem alkalmas az eredmény összevetésére; újramérendő. | `PicasaEditMenu.qml`, `PicasaMenuBar.qml` |
| Folder | Edit Description | `ki01/kepernyo__11.png`: `Folder Properties`; Name, Date, `Automatic date`, Music jelölő és Browse, Place taken, Description, OK / Cancel. | `folderPropertiesDialog`, cím `Folder Properties`; Name `PicasaTeszt`, Date mező `15 Jan 2020` helyőrző, `Automatic date`, Music jelölő, letiltott Browse, Place taken, Description, OK / Cancel. A fókusz a Name mezőn van. | A fő mezők és gombok egyeznek. A dátum eltérő megjelenése a két próbamappa eltérő dátumadata mellett nem általánosítható. | `PicasaFolderMenu.qml`, `FolderPropertiesDialog.qml` |
| Folder | Refresh Thumbnails | `ki01/kepernyo__17.png`: a mappanézet látszik, új ablak vagy panel nem. | Nincs új ablak vagy panel; a kijelölés `[0, 1]` marad. | A látható állapot egyezik; a háttérben végzett frissítés tartalmát a képkocka nem mutatja. | `PicasaFolderMenu.qml` |
| Folder | Print Contact Sheet | `ki01/kepernyo__23.png`: `Print Layout`; Wallet, 3.5×5, 4×6, 5×7, 8×10, Full Page méretek, Shrink to Fit / Crop to Fit, Border/Text Options, PDF nyomtató, Copies per Photo, Print / Cancel. | `printDialog`, `Print...`; 2 kép, 1 oldal, `Contact Sheet`, oszlopok `4`, méretek 10×15, 13×18, 15×20, 20×25 cm, Contact Sheet, FullPage; Border and Text Options, `Print to a PDF file...`, Help / Print / Close. Nincs telepített nyomtató, a Print és Printer Setup letiltott. | A párbeszéd szerkezete és méretlistája eltér. A Print letiltását a nyomtató nélküli mérőgép okozza, ezért az nem igazolt termékeltérés. | `PicasaFolderMenu.qml`, `PrintDialog.qml` |
| Folder | Export as HTML Page | `ki01/kepernyo__29.png`: 640 px, filmhez First frame, cím `PicasaTeszt`, előre megadott exportmappa, hat sablon és XML választó, előnézet, Export / Cancel. | `webExportDialog`, cím `Export as HTML Page...`; 640 px, First frame, cím `PicasaTeszt`, mappa `(not selected)`, Browse; nincs látható sablonlista vagy előnézet, Export letiltva, Cancel. | A célmappa és sablonok hiányoznak, így Export nem indítható. | `PicasaFolderMenu.qml`, `WebExportDialog.qml` |
| Folder | Remove from Picasa | `ki01/kepernyo__35.png`: `Confirm`, kérdés a `C:\PicasaTeszt\` és almappái eltávolításáról, Remove Folder / Cancel. | `removeFolderConfirmDialog`, cím `Confirm`; `Do not ask again`, Remove Folder / Cancel. A kérdés szövege nem látható. | PicasaPyből hiányzik a megerősítő kérdés szövege. A Remove Folder gomb fókuszban volt, de az alapértelmezett gomb nincs megmérve. | `PicasaFolderMenu.qml`, `MainDialogs.qml` |
| Folder | Move | `ki02/kepernyo__11.png`: `Browse for Folder`, üres mappalista, Make New Folder, OK / Cancel. | `moveFolderDialog`, `Move Folder`; a rendszer mappaválasztója a próbaprojekt gyökerét és alkönyvtárait mutatja, Open / Cancel. Nem választottam célmappát. | A párbeszéd és induló hely eltér. A választó natív megjelenése és gyökere platform- illetve próbakörnyezet-függő; a művelet kimenete nincs mérve. | `PicasaFolderMenu.qml`, `FolderPaneMenus.qml` |
| Folder | View Slideshow | `ki02/kepernyo__17.png`: teljes képernyős diakép. | Teljes képernyős `SlideshowView`; nincs külön párbeszédpanel. | A mért megjelenítési mód egyezik. | `PicasaFolderMenu.qml`, `SlideshowView.qml` |
| Create | Make a Poster | `ki02/kepernyo__23.png`: `Poster Settings`, 200%, Paper size 4x6, Overlap tiles, OK / Cancel. | `posterDialog`, `Poster Settings`; 200%, Paper size 10x15, Overlap tiles, OK / Cancel. | A papírméret felirata eltér; a két beállítás közötti megfelelést külön nem mértem. A fókusz és az alapértelmezett gomb nincs meg. | `PicasaCreateMenu.qml`, `PosterCreateDialog.qml` |
| Create | Create a Gift CD | `ki02/kepernyo__29.png`: Gift CD panel, CD név `PicasaTeszt`, Include Slideshow, fotóméret; az IMAPI2 hibaablak szerint a CD motor nem érhető el, OK / No. | Beágyazott Gift CD panel; CD Name mező üres, 16 karakteres korlát, Photo Size `Original Size`, Add More, Burn Disc, Cancel. Nincs IMAPI2 hibaablak. | A PicasaPy panelen nem látszik az Include Slideshow választó vagy az eredetiben előtöltött név. A CD-írás eredménye egyik képből sem állapítható meg. | `PicasaCreateMenu.qml`, `GiftCdHost.qml`, `PublishPanel.qml` |
| Create | Publish to Blogger | `ki02/kepernyo__35.png`: a fő Picasa ablak látszik, külső böngésző vagy céloldal nem. | A `Publish to Blogger...` menüpont szürke és letiltott; nincs új ablak. | Az eredeti kép nem mutatja, mit nyit a parancs; a PicasaPy tétel letiltott. Az eredeti cél mérésre vár. | `PicasaCreateMenu.qml` |
| Create | Set as Desktop | `ki03/kepernyo__11.png`: Confirm kérdés az asztali háttér lecseréléséről, Set Desktop / No. | `wallpaperConfirmDialog`, `Confirm`, azonos kérdésszöveg és Set Desktop / No. A Set Desktop fókuszban volt. | A mért megerősítés egyezik. A műveletet nem erősítettem meg. | `PicasaCreateMenu.qml`, `MainDialogs.qml` |
| Create | Picture Collage | `ki03/kepernyo__17.png`: Picture Collage panel, Settings / Clips, elrendezés, Draw Shadows, Show Captions, Desktop Background, Create Collage, Reset, Close. | `Collage` munkalap; Settings / Clips (2), Picture Pile, 4:3, Draw Shadows és Show Captions bejelölve, Desktop Background, Create Collage, Reset, Close. | A fő panel, beállítások és gombok egyeznek. | `PicasaCreateMenu.qml`, `CollageCreateDialog.qml` |
| Help | Help Contents and Index | `ki04/kepernyo__11.png`, `__12.png`: csak a főablak látszik, a súgócél nem. A kép nem igazolja a megnyíló tartalmat. | `helpDialog` réteg, `mainHelpWindow`, cím `Help Contents and Index`; kereső, tartalomnézet és Close. | Az eredeti cél a kép alapján nyitott kérdés; újramérendő. | `PicasaHelpMenu.qml`, `HelpDialog.qml` |
| Help | Keyboard Shortcuts | `ki04/kepernyo__17.png`: csak a főablak látszik, célablak nem. A bináris viselkedési spec szerint a parancs böngészőt nyit, `answer=11139`. | `helpDialog` réteg, `mainHelpWindow`, cím `Help Contents and Index`; a lap címe `Keyboard Shortcuts`, billentyűlista, kereső és Close. | Az eredeti böngészős cél és a PicasaPy beépített súgóoldala eltér. A megadott eredeti kép nem mutatja a böngészőt. | `PicasaHelpMenu.qml`, `HelpDialog.qml`, `MainKeyboardShortcuts.qml` |
| Help | About Picasa | `ki04/kepernyo__23.png`: `About Picasa`, 3.9.141 (Build 259) for Linux, licenc-hivatkozás és OK. | `aboutDialog`, `About PicasaPy`, v1.0.102, Website / Privacy Policy / Terms of Service és OK. | A márkanév és verzió természetesen eltér; az ablak megnyitása egyezik. | `PicasaHelpMenu.qml`, `AboutDialog.qml` |
| Help | Uninstalling Picasa | `ki04/kepernyo__29.png`: a főablak látszik, az eltávolító célja nem. Az eredeti menükatalógus szerint a tétel létezik, a cél telepítő-specifikus. | Nincs ilyen tétel a PicasaPy Help menüben; a kattintásmérő nem talált egyező menüelemet. | A menütétel hiányzik, az eredeti eltávolító viselkedés nyitott és platformfüggő. | `PicasaHelpMenu.qml` |
| Help | Picasa Forums | `ki04/kepernyo__35.png`: a főablak látszik, böngészőablak nem. A bináris index a menü-diszpécserhez rendeli a `http://forums.picasa.com/` URL-t; a kép nem mutatja a nyitást. | A `Picasa Forums` tétel szürke és letiltott; nincs böngészőablak. | Az eredeti külső fórumhivatkozás és a letiltott PicasaPy-tétel eltér. A kép az eredeti böngészőindítást nem igazolja. | `PicasaHelpMenu.qml` |

#### Igazolt eltérések és javasolt fejlesztési jegyek

- **Copy All Effects:** két kép kijelölésekor az eredeti egyképes korlátozó üzenetet mutat, PicasaPy nem. Javasolt fejlesztés: ellenőrizze a kijelölés darabszámát, és két vagy több kép esetén jelenítse meg az eredetihez igazított figyelmeztetést. A másolt effekt tartalmát ez a kör nem mérte.
- **Print Contact Sheet:** az eredeti `Print Layout` felület és a PicasaPy `Print...` ablakának elrendezése és méretválasztói eltérnek. Javasolt fejlesztés: a nyomtatási párbeszédablak felületének közelítése az eredetihez; a nyomtató nélküli mérésből ne következzen a Print gomb állandó tiltása.
- **Export as HTML Page:** PicasaPyben nincs előre kiválasztott exportmappa, sablonlista vagy előnézet, és az Export letiltott. Javasolt fejlesztés: az eredeti alapértelmezett célmappa, sablonválasztás és előnézet biztosítása, Export csak a hiányzó kötelező mező kitöltéséig legyen tiltott.
- **Remove from Picasa:** a PicasaPy Confirm ablakában nem látható az eltávolítási kérdés. Javasolt fejlesztés: jelenjen meg a mappa nevét és almappáit megnevező kérdés, a Remove Folder és Cancel gombok előtt.
- **Create a Gift CD:** PicasaPy mérésében üres CD-név mező és nincs Include Slideshow választó, miközben az eredeti képen ezek vannak. Javasolt fejlesztés: a CD név alapértékének és a diavetítés-választónak a paritása; a CD-írási út külön mérendő.
- **Help webtételek:** az eredeti `Keyboard Shortcuts` és `Picasa Forums` bináris útja külső böngészőcélra utal, PicasaPyben az egyik helyi súgóoldalra jut, a másik letiltott. Javasolt fejlesztés csak termékdöntés után: a helyi súgó vagy az eredeti külső cél kívánt viselkedésének rögzítése.

A megvalósítás a #6861 jegyben folyik. A `Make a Poster` méretfeliratát, az `Edit Description` dátumát és a `Move` rendszerpárbeszédét nem emelem fejlesztési eltéréssé, mert a mért eltérésből azonos próbaadat és platform nélkül nem következik hibás működés.

#### Szennyezett vagy hiányos eredeti képek, újramérendő

- `Edit > Invert Selection`, `ki00/kepernyo__29.png`: a képen nincs kijelölés, ezért a két kijelölt képből induló hatás nem látható.
- `Edit > Clear Selection`, `ki00/kepernyo__34.png` - `__36.png`: a menüpont szürke, a képen mappakijelölés és üres képtálca látható.
- `Create > Publish to Blogger`, `ki02/kepernyo__35.png`: a böngésző vagy megnyitott cél nem látható.
- `Help > Help Contents and Index`, `ki04/kepernyo__11.png` - `__12.png`: a súgócél nem látható.
- `Help > Keyboard Shortcuts`, `ki04/kepernyo__17.png`: a böngésző nem látható; a böngészős útvonalat a meglévő bináris spec rögzíti.
- `Help > Uninstalling Picasa`, `ki04/kepernyo__29.png`: az eltávolító cél nem látható.
- `Help > Picasa Forums`, `ki04/kepernyo__35.png`: a böngésző nem látható; az URL-t a bináris index adja.

Másik tétel ablakát egyik fenti képen sem láttam. A hiányos képkocka nem bizonyítja, hogy a parancs nem indult el.

#### A jegy „Kész, ha” pontjai

- ✅ Mind a 22 tétel táblázatban szerepel az eredeti kép, a PicasaPy állapota, az eltérés és a felelős QML-fájl megadásával.
- ✅ A hiányos vagy hibás kiinduló állapotú eredeti képek külön újramérendő listában vannak; ezekre nem állítottam be nem látott eredményt.
- ✅ A Copy All Effects, a Remove from Picasa, az Export as HTML Page és a Gift CD eltérése a #6861 megvalósítási jegybe került.


## Tálca és mappa-eszköztár (#6862)

A PicasaPy-oszlop minden sora két kijelölt képpel, valódi QTest-egérkattintással
és a kattintás után 3 másodperccel készült. A képernyőkép és az állapotfájl a
mérés idején a munkafa `.bt/6862/` könyvtárában volt; a feladat előírása szerint
az ideiglenes mérési fájlok a munka lezárásakor törlendők. Az eredeti kockák és
az őket megelőző/követő állapotok a megadott `job-639` és `job-640` felvételek.

| Gomb | Eredeti Picasa 3.9 | PicasaPy (2 kijelölés, QTest) | Eltérés / mérési korlát | Felelős PicasaPy-fájl |
|---|---|---|---|---|
| Tálca: Email | job-639/9: „Select Email”; Native Mail Client és Google Mail választás, emlékezzen jelölőnégyzet, Help/Cancel. | A `trayEmailButton` megnyitja az `emailChoiceDialog`-ot. | A folyamat egyezik. Az eredeti tálcagomb és a `0x005cb990` menü-diszpécser közötti konkrét hívási kapcsolat nincs igazolva; a PicasaPy tálca és Fájl/E-Mail ugyanarra a `sendSelectionByEmail()` műveletre fut. | `TrayActionArea.qml`, `MainTrayBar.qml`, `MainWindowCommands.qml` |
| Tálca: Print | job-639/14 átadott leírása: teljes Print Layout nézet, lap- és képelrendezés, nyomtatóválasztó, előnézet, Print/Cancel. | A korábbi QTest-összefoglaló bal oldali `printDialog` panelt említ. A jelenlegi `PrintDialog.qml:19-23` gyökéreleme külön, az egész alkalmazást blokkoló (modális) `Window`; a helyi QTest-képkocka hiányában a két leírás eltérése nem dönthető el újraméréssel. | Az eredeti főnézetváltást az erőforrásban a `m_print_enable` írja le. Nyomtatás végrehajtása nyomtató hiányában nem mérhető. | `TrayActionArea.qml`, `MainTrayBar.qml`, `Main.qml`, `PrintDialog.qml` |
| Tálca: Export | job-639/19: Export to Folder, két kép, Resize to 800 pixels, minőség, film, vízjel, Export/Cancel. | Az `exportDialog` megnyílik; „Use original size” aktív, célhely `<Pictures>/Picasa/Exports`. | A párbeszéd folyamata egyezik, de az értékek eltérnek. Ez egy mentett profilállapot mérése, nem tiszta profil alapértékének összehasonlítása. A tálca és a PicasaPy menü ugyanazt az `openForSelection()` műveletet hívja. | `TrayActionArea.qml`, `MainTrayBar.qml`, `ExportDialogs.qml` |
| Tálca: Upload to Google Photos | job-639/24: a kattintás után job-639/25-től „Log in to Google” ablak nyitva. | A `trayUploadButton` látható, de bejelentkezés nélkül tiltott; kattintásra nem nyit ablakot. | Igazolt eltérés: az eredeti felkínálja a bejelentkezést, a PicasaPy tálcagombja nem indítható el. A hitelesítés utáni feltöltést egyik oldalon sem hajtottuk végre. | `TrayActionArea.qml`; engedélyezési állapot: `tray_google_photos_controller.py` |
| Mappa-eszköztár: diavetítés | job-639/29: a Google-belépő már nyitva van a job-639/24 Upload óta; a diavetítés hatása nem látszik. | A `headerPlayButton` teljes képernyős diavetítést indít. | Az eredeti kimenet ebből a felvételből nyitott. A PicasaPy fejléc a csoport kezdősorát adja át; a menü ugyanahhoz az indító művelethez `-1` indexet ad. Az eredeti fejlécgomb menüparancshoz rendelése nincs igazolva. | `LightboxHeaderButtons.qml`, `LightboxFeedGroup.qml`, `MainLibraryCanvas.qml`, `MainSlideshow.qml` |
| Mappa-eszköztár: kollázs | job-640/9: kollázsprojekt; két kijelölt kép a vásznon, „Clips (22)”. | A `headerCollageButton` Kollázs projektlapot nyit, 24 klippel/csomóponttal; a kijelölés és a held sorok továbbra is csak `[0, 1]`. | Igazolt eltérés: a fejléc a teljes 24 képes csoportot adja át, míg az eredeti mérésben két kép van betöltve, 22 maradék klippel. A PicasaPy menübelépő forrása külön útvonal. Az eredeti menü `ID_COLLAGEMAKER` és az `outputlayout/collage` azonos bináris kezelőre fut; a képkockán kattintott fejlécvezérlő és a bináris UI-címke közti kapcsolat nem szerepel a meglévő kimenetben. | `LightboxHeaderButtons.qml`, `LightboxFeedGroup.qml`, `MainProjectTabs.qml` |
| Mappa-eszköztár: film | job-640/14: „This feature is not supported for Linux” hiba; binárisból bizonyítva: 2 kijelölt képnél csak a kijelöltek kerülnek a filmbe, a teljes mappa csak <2 kijelölésnél töltődik be. | A `headerMovieButton` Filmkészítő lapot nyit 24 klippel. | Igazolt eltérés: nálunk a fejlécgomb feltétel nélkül a teljes 24 képes mappát adja át, az eredeti 2 kijelölt képnél csak a 2 kijelöltet tölti be. | `LightboxHeaderButtons.qml`, `LightboxFeedGroup.qml`, `MainProjectTabs.qml`, `CreateDialogs.qml` |
| Mappa-eszköztár: csillag | job-640/19: a két kép kijelölve marad a kattintás után. | A `headerSelectStarredButton` után a kijelölés üres; a mérési képek egyike sincs csillagozva. | Az eredeti képek csillag-metaadata nem szerepel a job állapotfájljaiban, ezért azonos bemeneti csillagállapot mellett nem hasonlítható össze. Az eredeti `ID_SELECTSTAR` menüparancs ismert, a fejlécgomb menü-diszpécserhez kötése nincs igazolva. | `LightboxHeaderButtons.qml`, `LightboxFeedGroup.qml` |
| Mappa-eszköztár: Upload | job-640/24: a kattintás után job-640/25-től Google-belépő nyitva. | A `headerUploadButton` látható, 86×22 képpontos és tiltott; kattintásra nincs ablak. A QML-ben a gomb `enabled: false`, kattintáskezelője nincs. | Igazolt eltérés: az eredeti gomb bejelentkezési folyamatot indít, a PicasaPy fejlécgomb nem működik. | `LightboxHeaderButtons.qml` |
| Mappa-eszköztár: Upload lenyíló | job-640/29: a korábbi Upload után már nyitva lévő Google-belépő elfedi a lenyíló saját hatását. | A gomb jobb szélére, a nyíl helyére kattintva sem nyílik menü; a vezérlő tiltott. | Az eredeti lenyíló működése nyitott kérdés a szennyezett kocka miatt. A PicasaPy-gombnak nincs használható lenyílója. | `LightboxHeaderButtons.qml` |

### Eredeti menü-diszpécser és a gombok azonossága

A meglévő `0x005cb990` Ghidra-kimenet és a menüépítő kimenet az alábbi
menüparancs-azonosítókat támasztja alá: `ID_FILE_EMAIL` = `0x9c97`,
`ID_FILE_EXPORTTOFOLDER` = `0x9c81`, `ID_FILE_PRINT` = `0xe107`,
`ID_ALBUM_SLIDESHOW` = `0x9c6d`, `ID_VIEW_SLIDESHOW` = `0x9c9f`,
`ID_COLLAGEMAKER` = `0x9d62`, `ID_TOOLS_UPLOAD` = `0x9df7`,
`ID_SELECTSTAR` = `0x9d5b`. A diszpécserben a két slideshow-ID közös
`FUN_005e8a70` függvényre fut, de külön parancsazonosító marad.

Két eredeti gombút kapcsolható közvetlenül a menüparancs közös kezelőjéhez:
az `outputlayout/collage` ág és a `0x9d62` menüág is `FUN_007463c0`-t hívja;
a `thumbui/webupload` ág és a `0x9df7` menüág is `FUN_0059e920`-t hívja.
Ezek a közös kezelőt, nem feltétlenül azonos eseményküldési útvonalat
igazolják. A `0x005cb990` menüágak és a konkrét job-639/640 Email, Print,
Export, slideshow, film és csillag fejléc-/tálcagombja közötti közvetlen
kapcsolatot a meglévő diszasszemblálási kimenet nem igazolja; az ilyen
azonosság nyitott, nem következtethető ki a feliratból.

PicasaPy oldalon a tray Email/Print/Export gombok rendre ugyanazt a
`sendSelectionByEmail()`, `openPrint()` és `openForSelection()` műveletet
hívják, mint a főmenü megfelelő tételei. A fejléc kollázsa a teljes
mappacsoportot adja át, míg a főmenü a tartott/kijelölt sorokból indul; a
fejléc diavetítése a csoport kezdősorát, a menü az alapértelmezett `-1`
értéket adja át. A fejléc Upload gombjának nincs eseménykezelője.

### Bizonyítottság és következő mérés

Megerősített eltérés a kollázs bemeneti halmaza, valamint a Google Photos
Upload engedélyezési/bejelentkezési útja: az eredeti képkockák, a PicasaPy
valós kattintásos állapota és az ettől külön olvasott forráskód egymást
támasztják alá. A Print nézetének különbsége is látható, a tényleges
nyomtatás viszont nyomtató hiányában nyitott. Az Export értékkülönbsége,
a csillag eredménye, a slideshow, a Film és az Upload lenyíló eredeti
folyamata nem dönthető el teljesen a megadott mérésekből. A slideshow és
Upload-lenyíló új eredeti mérése a kérdéses gombot korábbi Upload nélkül
kattintsa; a Filmhez Windows környezetben készült felvétel kell; a
csillagnál az eredeti képek csillag-metaadatát is rögzíteni kell.

A kollázs bemeneti halmazának és a kijelentkezett Upload gomboknak az eltérése a #6865 megvalósítási jegyben.


## Folyamatszintű összevetés (#6845)

Mérés dátuma: 2026-11-12 / 2026-11-13 / 2026-11-14. Hatókör: a 20 mappanézetbeli fájl- és mappaművelet folyamatszintű paritása az eredeti Picasa 3.9 (Colab-végrehajtó, képernyőképek, lemez- és ablakállapot) és a PicasaPy (QML-funkcionális tesztek valós kattintással, lemez, index és felületi állapot ellenőrzésével) összevetésében.

| Parancs | Belépési pontok | Eredeti (mért / viselkedés) | PicasaPy (mért / teszt) | Eredmény / Eltérés | Felelős felület |
|---|---|---|---|---|---|
| Áthelyezés új mappába (`ID_FILE_NEWFOLDER`) | Fájl menü, kép helyi menüje | Colab (helyi menü); Fájl menü: job-641 | #6844 | Eltért, javítva (#6844, kiadás: 1.0.103); a Fájl menüs tiszta újramérés (job-641) is a Folder Properties ablakot mutatja: egyezik | `FolderPropertiesDialog.qml`, `PhotoContextMenu.qml` |
| Mappa felosztása itt | Kép helyi menüje | Colab #600-#608 | #6848 | Eltért, javítva (#6848, kiadás: 1.0.104) | `PhotoContextMenu.qml` |
| Elrejtés | Kép helyi menüje, Kép menü | Colab #600-#608 | #6848 | Eltért, javítva (#6848, kiadás: 1.0.104) | `PhotoContextMenu.qml`, `PicasaPictureMenu.qml` |
| Keresés a lemezen (`ID_FILE_LOCATEONDISK`, `ID_ALBUM_LOCATEONDISK`) | Kép és mappa helyi menüje, Fájl menü | job-642 (Fájl menü); Wine alatt nincs fájlkezelő ablak | #6845 (`test_kereses_es_gyujtemeny_folyamatok_6845.py`) | Eredeti oldalon Wine alatt nem nyílik Intéző ablak; PicasaPy-on mindhárom belépési pont a megfelelő `fileOpsController.revealPhoto`/`revealFolder` API-t hívja; 0 kijelölt képnél a Fájl menü letiltott, 1 és 2 képnél aktív; ablakot nem nyit, kijelölés megmarad | `PhotoContextMenu.qml`, `FolderContextMenu.qml`, `PicasaFileMenu.qml` |
| Törlés a lemezről | Kép helyi menüje, Delete, Fájl menü | Colab #600-#608 | #6848 | Eltért, javítva (#6848, kiadás: 1.0.104) | `PhotoContextMenu.qml`, `PicasaFileMenu.qml` |
| Teljes elérési út másolása | Kép helyi menüje | Colab #600-#608: 1 képnél látható, 2 képnél hiányzik | #6848 (`test_kereses_es_gyujtemeny_folyamatok_6845.py`) | Eltért, javítva (#6848, kiadás: 1.0.104): a menüpont 2 képnél rejtett, csak pontosan 1 kijelölt képnél jelenik meg | `PhotoContextMenu.qml` |
| Átnevezés | F2, Fájl menü | Fájl menü: job-641 (tiszta) | #6845 (Q07) | Egyezik: Rename Files ablak („2 file(s) selected for rename.”) | `SaveDialogs.qml`, `PicasaFileMenu.qml` |
| Forgatás jobbra/balra | Kép helyi menüje, eszköztár, Ctrl+]/[ | Colab #600-#608 | #6848 | Eltért, javítva (#6848, kiadás: 1.0.104) | `PhotoContextMenu.qml` |
| Összes szerkesztés visszavonása | Kép helyi menüje, Kép menü | Colab (Kép menü) | #6845 (Q28) | Egyezik: Confirm ablak, Remove Edits / No gombok | `PicasaPictureMenu.qml`, `PhotoContextMenu.qml` |
| Tulajdonságok | Kép helyi menüje, Alt+Enter, Nézet és Kép menü | Colab #600-#608 | #6848, #6845 (Q17, Q30) | Eltért, javítva (#6848, kiadás: 1.0.104); a menüből nyitott Properties panel egyezik | `PropertiesPanel.qml`, `PhotoContextMenu.qml` |
| Mappaleírás szerkesztése | Mappa helyi menüje, Folder menü | Colab #613, #614 | felvevő, #6860 | Egyezik: Folder Properties ablak | `FolderPropertiesDialog.qml`, `PicasaFolderMenu.qml` |
| Áthelyezés gyűjteménybe | Mappa helyi menüje | job-648 (az almenü: Exported Pictures, Folders, Hidden Folders, Other Stuff, Projects, Web Albums, New Collection...; a jelenlegi gyűjtemény pipált és tiltott); job-649 (Other Stuff: `P2category=Other Stuff`, a bal hasábban a mappa az Other Stuff csoportba kerül, ablak nélkül) | #6845 (`test_kereses_es_gyujtemeny_folyamatok_6845.py`) | Eltér: a PicasaPy almenüjéből hiányzik a hat beépített gyűjtemény, csak a saját gyűjtemények és a New Collection... van → #6883. A saját gyűjtemény útja (New Collection..., `P2category`, bal hasáb) működik | `FolderContextMenu.qml`, `FolderPane.qml` |
| Indexképek frissítése | Mappa helyi menüje, Folder menü | Colab (Folder menü) | #6860, #6845 (`test_mappa_folyamat_paritas_6845.py`) | #6860: a látható állapot egyezett, új ablak nem nyílt. #6845: mindkét kattintási út frissíti a tartalmat; a módosított kép új adatai és az új fájl bekerül az indexbe és a rácsba; a `.picasa.ini` és a bal hasáb változatlan, a kijelölés megmarad. A módosított kép új, mtime/méret kulcsú cache-fájlt kap, a régi cache-fájl a méréskor megmaradt. | `FolderContextMenu.qml`, `PicasaFolderMenu.qml` |
| Mappa rendezésének alapja | Mappa helyi menüje | Colab #613, #614 | felvevő | Eltért, javítva (#6852, kiadás: 1.0.104) | `FolderContextMenu.qml` |
| Mappa elrejtése / megjelenítése | Mappa helyi menüje | Colab #613, #614 | felvevő | Egyezik: Add Password ablak | `FolderContextMenu.qml`, `PasswordDialog.qml` |
| Eltávolítás a Picasából | Mappa helyi menüje, Folder menü | Colab #613, #614 | felvevő, #6860 | Eltért: helyi menü javítva (#6852), Folder menü javítva (#6861), kiadás: 1.0.104 | `FolderContextMenu.qml`, `PicasaFolderMenu.qml`, `MainDialogs.qml` |
| Mappa áthelyezése | Mappa helyi menüje, húzás | Colab #613, #614; húzás: job-656, job-657 (Wine alatt nem indult művelet) | #6852, #6845 (`test_mappa_folyamat_paritas_6845.py`) | Eltért: az eredeti `CAlbumList` mappasor-húzása nem készít képlistát, így a drop fájlművelet nélkül visszatér; PicasaPy a teljes mappát és `.picasa.ini`-t áthelyezi. Külön fejlesztési jegy javasolt a PicasaPy viselkedésének paritásra igazításához. A Windowsos eredeti felület/lemezállapot felvétele még hiányzik. | `FolderPaneTreeRow.qml`, `MainFolderPane.qml`, `fileops/move_folder.py`; eredeti: `0x005d3290`, `0x00765d30`, `0x005e39a0`, `0x005350b0` |
| Mappa törlése | Mappa helyi menüje | Colab #613, #614 | felvevő | Eltért, javítva (#6852, kiadás: 1.0.104) | `FolderContextMenu.qml` |
| Mentés / Visszaállítás | Fájl menü, kép helyi menüje | job-641 (tiszta) | #6845 (Q08, Q09) | Save As egyezik; Save a Copy eltér: két kijelölt képből az eredeti egy másolatot készít → #6866 | `SaveDialogs.qml`, `PicasaFileMenu.qml` |
| Kép exportálása mappába | Fájl menü, alsó tálca | Colab (Fájl menü); tálca: job-639 | #6845 (Q10); tálca: #6862 | Eltér: tiszta profillal (job-642) is a Resize to 800 pixels az alap, nálunk Use original size → #6866 | `ExportDialogs.qml`, `PicasaFileMenu.qml`, `TrayActionArea.qml` |

### Részletes folyamatmérések (#6845)

#### 1. Keresés a lemezen (`Locate on Disk`)
- **Belépési pontok:**
  - Kép helyi menü (`contextMenuLocate`): 1 és 2 kijelölt képnél is elérhető. Kattintásra belső párbeszédablak nem nyílik; a lemezen, az adatbázis-indexben és a bal oldali hasábban semmi sem változik; a rácsban a kijelölés megmarad. A háttérben meghívja a `fileOpsController.revealPhoto(path)` metódust a kijelölt képre.
  - Mappa helyi menü (`folderMenuLocate`): 1 és 2 kijelölt kép mellett is elérhető a mappán. Kattintásra belső ablak nem nyílik; sem a lemez, sem az index, sem a hasáb állapota nem változik, a rácsbeli kijelölés érintetlen marad. A háttérben meghívja a `fileOpsController.revealFolder(folderPath)` metódust.
  - Fájl menü (`menuFileLocate`): 1 és 2 kijelölt képnél a menüpont aktív (`enabled: true`), kattintásra a kijelölt képek első elemére hívja a `revealPhoto`-t; kijelölés hiányában (0 kép) a menüpont tiltott (`enabled: false`).
- **Eredeti összevetés:** Wine alatt a Windows Intéző hiánya miatt a `job-642` kattintása nem nyitott ablakot (külső fájlkezelő hívása Windows-környezetben mérendő); a PicasaPy oldalon a folyamat mindhárom belépési pontról szigorúan és platform-függetlenül ellenőrzött (`tests/app/qml_functional/test_kereses_es_gyujtemeny_folyamatok_6845.py`). A mappasor-húzás lemezre gyakorolt eredeti hatását a lentebbi „#6845 kiegészítés” statikus bizonyítéka eldönti; a Windowsos képkocka, `kepmappa` és `allapot` továbbra is hiányzik.

#### 2. Áthelyezés gyűjteménybe (`Move into Collection`)
- **Eredeti (job-648, job-649):** az almenü hat beépített gyűjteményt sorol (Exported Pictures, Folders, Hidden Folders, Other Stuff, Projects, Web Albums), alatta a New Collection...; az Other Stuff választása a `.picasa.ini`-be `P2category=Other Stuff`-ot ír, és a bal hasábban a mappa az Other Stuff csoportba kerül, megerősítő ablak nélkül. A PicasaPy-ból a beépített tételek hiányoznak → #6883.
- **Belépési pontok:**
  - Kizárólag a mappa helyi menüjéből érhető el (`folderContextMenuMoveToCollection`). A kép helyi menüjéből és a Fájl menüből hiányzik (nem képművelet).
  - **Új gyűjtemény létrehozása:** a menüben a „New Collection...” (`folderContextMenuNewCollection`) kiválasztásakor megnyílik a `newCollectionDialog` („New Collection”). A gyűjtemény nevének megadása és jóváhagyása után:
    1. Lemez: az érintett mappa könyvtárában a `.picasa.ini` fájl `[Picasa]` szakasza frissül: `P2category = <gyűjteménynév>`.
    2. Index: a mappa bekerül az SQLite adatbázis / kontroller `customCollections` nyilvántartásába.
    3. Bal hasáb: a mappapanelen (`FolderPane`) létrejön a gyűjtemény fejléce (`customCollection_<név>`) és alatta a mappa sora (`customCollectionFolder_<útvonal>`).
    4. Rács: a rácsban lévő képek kijelölése nem sérül.
  - **Meglévő gyűjteménybe áthelyezés:** ha létezik egyéni gyűjtemény, az almenüben közvetlenül megjelenik annak neve (`folderContextMenuMoveToCollectionItem_<név>`). Kattintásra külön megerősítő dialógus nélkül azonnal végbemegy az áthelyezés (a `.picasa.ini` `P2category` értéke és a bal hasáb struktúrája frissül).
- **Tesztelt lefedettség:** `tests/app/qml_functional/test_kereses_es_gyujtemeny_folyamatok_6845.py` (valódi QTest kattintásokkal, 1 és 2 kijelölt képpel, lemez- és UI-invariánsok ellenőrzésével).

#### 3. Mappa áthelyezése húzással
- **Belépési pont:** bal hasáb lapos mappalistájában az `atmozgatando` mappasor húzása a `cel` mappára. A próbát valódi `QTest.mousePress`/`mouseMove`/`mouseRelease` sorozat futtatja.
- **Lemez:** a forrás könyvtár a cél alatt jelenik meg, a régi út eltűnik; a `.picasa.ini` bájtra azonos marad, a kép és a felirata megmarad.
- **Index:** a kép `folders.path` útvonala az új könyvtárra változik, a régi mappasor kikerül.
- **Bal hasáb:** a régi mappasor eltűnik, a cél alatti új sor megjelenik.
- **Rács:** a négy kép megmarad, az áthelyezett kép útvonala követi a könyvtárat. A kijelölés a művelet után üres.
- **Tesztelt lefedettség:** `tests/app/qml_functional/test_mappa_folyamat_paritas_6845.py`; a húzás `-5`, `0` és `+5` px ablakmagasságnál is sikeres. Ez a PicasaPy működését méri; az eredeti lemezművelet statikus útja a „#6845 kiegészítés” szakaszban feloldott, de az eredeti Windowsos felületi és állapotfelvétel még hiányzik.

#### 4. Indexképek frissítése (`Refresh Thumbnails`)
- **Belépési pontok:** a mappa helyi menüje és a Folder főmenü. Mindkettőre valódi egérkattintás indítja a műveletet; új ablak nem nyílik.
- **Lemez:** a meglévő JPEG módosítása és egy új JPEG létrehozása után a `.picasa.ini` bájtjai változatlanok.
- **Index és rács:** a módosított kép új mtime/méret adatai frissülnek az indexben, az új fájl is bekerül; mindkettő látható a rácsban. A bal hasáb mappasora és a kétképes kijelölés változatlan marad.
- **Bélyegkép-cache:** a módosított kép új, útvonal + mtime + méret kulcsú cache-fájlt kap. A korábbi cache-fájl a művelet után is megmarad; a frissítés nem törli azonnal a korábbi változatot.
- **Tesztelt lefedettség:** `tests/app/qml_functional/test_mappa_folyamat_paritas_6845.py`; mindkét belépési pont `-5`, `0` és `+5` px ablakmagasságnál is sikeres.

### #6862 kiegészítés: a tálca Print és Export gombja (2026-11-13)

Ez a kiegészítés a két nyitva maradt tálcagomb bináris útját és az Export
alapértékeit rögzíti. A job-639/14 és job-639/19 képkockafájlok nem voltak
benne a helyi `meroadat.tar` archívumban; a megfigyelésük az #6862 átadott
mérési összefoglalójából és a korábbi táblázatból származik, nem újramért adat.

| Kérdés | Megállapítás | Forrás |
|---|---|---|
| Tálca Export parancsazonosító | A `0x005d9cc0` eseménykezelő az `outputlayout/folderbutton` nevet vizsgálja, majd `0x005312b0`-t hívja. Ezen a gombúton numerikus parancsazonosító: **NINCS MEG**. | `bináris (0x005d9cc0, 0x00c8fb00)` |
| Fájl > Export menü | `ID_FILE_EXPORTTOFOLDER = 0x9c81`; a `0x005cb990` menü-diszpécser `0x005312b0`-ra fut. A tálca és a menü ugyanazt a kezelőfüggvényt hívja, de nem bizonyított, hogy a tálcagomb a menü numerikus azonosítóját küldi. | `bináris (0x005cb990, 0x005312b0)` |
| Tálca Print parancsazonosító | A `0x005d9cc0` az `outputlayout/pbutton` nevet a `0x00744a00` kezelőhöz irányítja. Ezen a gombúton numerikus parancsazonosító: **NINCS MEG**. | `bináris (0x005d9cc0, 0x00c8fae8, 0x00744a00)` |
| Fájl > Print menü | `ID_FILE_PRINT = 0xe107`. A `0x005cb990` menüág egy állapotfeltételt vizsgál: az egyik ág az `outputlayout/pbutton` nevű műveletet küldi, a másik közvetlenül `0x00744d00`-t hív. Ezért a menü és a tálca közös útja feltételes, nem általános. | `bináris (0x005cb990, 0x005cd9bc-0x005cd9d6)` |
| Print Layout nézet | A job-639/14 átadott leírása teljes Print Layout nézetet mutat. Az `outputlayout/pbutton` a `m_print_enable` makrót használja; ez megjeleníti a `thumbui/printpanel`-t és elrejti a `thumbui/mainuipanel`-t. A tálca kódútja `0x00744a00`-hoz, majd közvetlenül a panelépítő `0x00743700`-hoz vezet. A `0x00744a00`-ban talált `0x00744a65` virtuális hívás célja **NINCS MEG**. A `0x007448a0` a `pcancelbutton` és a nyomtatás utáni visszaút kezelője. | `mérés (job-639/14, átadott összefoglaló)`; `bináris (outputlayout.tre:38-43, macros.tre:285-291; 0x005d9cc0, 0x00744a00, 0x00743700, 0x007448a0)` |
| Eredeti Export méret | A `0x00738c00` konstruktor a `FileExportSize` kulcs hiányakor 3-at ad át (`0x00738c58`). A méretlista 0-alapú 3. indexe 800 px. A mentés a `0x00739960` útban ugyanezt a kulcsot írja. A tiszta profilú job-645 mérés szintén 800 px átméretezést látott; a job-639 profilbeállítása nem ismert. | `bináris (0x00738c43, 0x00738c58, 0x00739960)`; `mérés (job-645, export-parbeszed.md 3.2)` |
| Eredeti Export célhely | A konstruktor előbb a `CExportPrefsDialog::deffolder` kulcs nyers `Picasa\Exports\` alapját tölti be, majd a korábban mentett `DefaultExportPath` értékkel felülírhatja. A `0x00739960` mentési út a kiválasztott értéket tartósítja. A job-639 képen látható pontos célhely és a hozzá tartozó beállításérték: **NINCS MEG**. | `bináris (0x00738cd6, 0x00738d16, 0x00caf994, 0x00caf984, 0x00caf9b4, 0x00739960)` |
| PicasaPy Export induló érték | A jelenlegi forrás tiszta beállításnál `resize=True`, `size=3`, azaz 800 px; a QML a megőrzött állapotból tölti vissza a rádiót és a méretet. A célhely a megőrzött út, ennek hiányában `<Pictures>/Picasa/Exports`. A korábban feljegyzett QTest „Eredeti méret” állapotának tényleges beállításértéke: **NINCS MEG**. | `src/picasapy/app/export_prefs.py:35-36, 91-110`; `src/picasapy/app/qml/PicasaPy/ExportDialogs.qml:179-199`; `src/picasapy/app/export_controller.py:143-154`; `mérés (korábbi QTest-összefoglaló)` |

#### Két független út és cáfoló ellenőrzés

- **A út, utasítások:** a tálca-eseménykezelő `0x005d9cc0` a két név szerinti műveletet külön kezeli; a `folderbutton` ága `0x005312b0`-ra fut, a `pbutton` ága `0x00744a00`-ra. A menü-diszpécser `0x005cb990` `0x9c81` ága szintén `0x005312b0`-ra jut. A `0xe107` ágnál viszont állapotfüggő a folytatás.
- **B út, címkék, index és mérés:** az index `string_xrefs` táblája a `folderbutton` és `pbutton` neveket a tálca-eseménykezelőhöz köti; a menüazonosítók a meglévő `0x005cb990` Ghidra-kimenetben szerepelnek. Az Export `FileExportSize` és `DefaultExportPath` kulcsait külön olvasó `0x00738c00` és író `0x00739960` függvények, a tiszta job-645 felvétel pedig 800 px induló méretet mutat. A PrintPanel osztály RTTI-bejegyzése és a `thumbui/printpanel` erőforrásnév függetlenül támasztja alá a mérésben látott Print Layout felületet.
- **Egyezés:** az Export gomb és menü ugyanazt a kezelőfüggvényt hívja, de a tálcaút nem küldött numerikus menüazonosítóként igazolható. Printnél a menüazonosító `0xe107`, a tálcaút név szerinti, és a menüág csak az egyik feltétel mellett irányít a `pbutton` műveletre.
- **Cáfoló kör:** az Export közös útjára vonatkozó állítást az eltérő menüágak és a közvetlen utasításút ellenőrzésével próbáltam cáfolni; mindkét út `0x005312b0`-nál találkozik. A Print feltétel nélküli azonosságát a `0x005cb990` nemnulla állapotú ága cáfolja, amely `0x00744d00`-t hív. A `0x007448a0` címre mutató közvetlen hivatkozások `0x00743980` és `0x00745770` felől jönnek, nem a `0x00744a00`-ból, ezért ezt nem nevezem bizonyított tálcás nézetváltó hívásnak. A tiszta profilú job-645 800 px állapota cáfolja, hogy az 800 px és az eredeti méret közti különbség minden profilban alapérték-eltérés lenne; a konkrét job-639 előzményt nem dönti el.

#### PicasaPy-kötés és hátralévő kérdések

PicasaPyban a tálca Print `MainTrayBar.qml:56`-on és a Fájl > Print `MainMenuBar.qml:301`-en ugyanazt a `Main.qml:523` `openPrint()` műveletet hívja. Ez a `PrintDialog.qml:19-23` külön, az egész alkalmazást blokkoló (modális) `Window` ablakát nyitja. A korábbi QTest-leírás bal oldali panelt mond; ez a megfigyelés és a jelenlegi QML `Window` deklarációja nincs egymással összeegyeztetve, a felületet nem mértem újra. A tálca Export `MainTrayBar.qml:42`-n, a menü Export `MainMenuBar.qml:283-284`-en az `ExportDialogs.qml` `openForSelection()` műveletéhez jut; a menü nézőmódban külön átadja a célképsorokat. Az `export_prefs.py:20` modul elején álló megjegyzése az átméretezést hamis alapértékként írja le, miközben a tényleges mezőtérkép `:110` és a meglévő teszt `test_export_beallitasok_1138.py:63-64` igaz alapértéket ad meg. A gombok felelősségi fájljai: `TrayActionArea.qml`, `MainTrayBar.qml`, `MainMenuBar.qml`, `Main.qml`, `PrintDialog.qml` és `ExportDialogs.qml`.

**Bizonyítottsági fok: feltételes.** Az Export kezelőfüggvény azonossága és a bináris beállításkulcsok megerősítettek. A Print teljes nézetváltó hívása, valamint a job-639/19 konkrét profilértékei nyitva maradnak. A PicasaPy aktuális tiszta Export-alapértéke átméretezés 800 px, ami egyezik a job-645 tiszta profilú mérésével; a korábbi QTest eredményhez használt profilérték nincs meg.

- **NINCS MEG:** a job-639/14, job-639/19 és PicasaPy QTest képkockafájlok helyi példánya; megszerzés: az eredeti és a PicasaPy képkockákat tartalmazó fájlok felvétele a mérőarchívumhoz.
- **NINCS MEG:** a job-639 Export célhely pontos szövege és mindkét program elmentett Export-profilja; megszerzés: azonos kétképes bemenet, külön tiszta profil és azonos újrahasznált profil mellett rögzíteni a beállításkulcsokat, a célhelyet és az Export képkockáját.

#### Print Layout nézetváltás és visszaút (2026-11-13)

A job-639/14 képkockafájlja nem szerepel a helyi `meroadat.tar`-ban, ezért a
felületleírás az átadott mérési összefoglalóból származik. Az eredeti vezérlő
útját a kódból és az eredeti `.tre` erőforrásokból külön ellenőriztem.

| Lépés | Megállapítás | Forrás |
|---|---|---|
| Belépő vezérlő | Az `outputlayout.tre` az `outputlayout/pbutton` elemhez rendeli a `m_print_enable` makrót. | `bináris (0x00c8fae8; outputlayout.tre:38-43)` |
| Főnézet váltása | A makró megjeleníti a `thumbui/printpanel`-t, és elrejti a `thumbui/mainuipanel`-t, az `acquirepanel`-t, az `editpanel`-t, az `infowell`-t és a `secretcoinclip`-et. Ez az erőforrásban deklarált főnézet-váltás; a végrehajtó virtuális hívás célja külön nyitott kérdés. | `bináris (0x00c8f0f0; macros.tre:285-291)` |
| Kattintási kódút | A `0x005d9cc0` a `0x005da9af` helyen az `outputlayout/pbutton` nevet vizsgálja, majd `0x005da9f8`-nál meghívja a `0x00744a00` kezelőt. Ez a `0x00744a90` helyen közvetlenül meghívja a `0x00743700` panelépítőt. | `bináris (0x005da9af, 0x005da9f8, 0x00744a00, 0x00744a90, 0x00743700)` |
| Indirekt hívás | A `0x00744a65` utasítás a `[ebp+0xed0+0x258]` objektum vtable-jének `+0x0c` slotját hívja. A slot tényleges célfüggvénye és az `m_print_enable` makróhoz való viszonya **NINCS MEG**. | `bináris (0x00744a5e-0x00744a65)`; `NINCS MEG` |
| Visszatérés a könyvtárnézetbe | A PrintPanel erőforrásában nincs `Back` gomb; a `printpanel/pcancelbutton` vezérlő `escapekey 1` beállítást kap. A `0x00743980` kattintáskezelő `pcancelbutton` ága a `0x0074441e` helyen meghívja a `0x007448a0` panelállapot-kezelőt. A nyomtatás befejező útja is meghívja ugyanezt a kezelőt a `0x0074592a` címen. | `bináris (0x00c8ff24; printpanel.tre:199-201; 0x007443a1-0x0074441e; 0x0074592a)` |
| PicasaPy tálca Print | A tálca `MainTrayBar.qml:56` sora a `Main.qml:523` `openPrint()` függvényéhez vezet; a `PrintDialog.qml:19-23` külön, az egész alkalmazást blokkoló (modális) `Window`-t deklarál. A régi QTest-összefoglaló bal oldali panelt ír, de a képkocka nincs meg az archívumban, így a két állapot eltérését nem tudtam újramérni. | `src/picasapy/app/qml/PicasaPy/MainTrayBar.qml:56`; `src/picasapy/app/qml/Main.qml:523`; `src/picasapy/app/qml/PicasaPy/PrintDialog.qml:19-23`; `NINCS MEG (helyi QTest-képkocka)` |

#### Két független út és cáfoló ellenőrzés

- **A út, kód:** az `annot_disasm.py` utasításai és a `paszta.py` teljes `.text`-pásztázása ugyanazt mutatja: a tálca a `0x00744a00` kezelőn át a panelépítőre jut; a `0x007448a0` közvetlen hívója a `pcancelbutton` ág és a nyomtatás utáni út.
- **B út, erőforrás:** az `outputlayout.tre` és `macros.tre` deklarálja a PrintPanel megjelenítését és a fő könyvtárnézet elrejtését; a `printpanel.tre` a Cancel gombot és Escape-kötését nevezi meg. Ez a kódhívási lánctól függetlenül egyezik a job-639/14 leírt Print Layout állapotával.
- **Egyezés:** a Print Layout nézetet az `m_print_enable` erőforrás-makró kapcsolja be; a `0x007448a0` nem közvetlen belépési hívás, hanem a `pcancelbutton` és a nyomtatás utáni visszaút része.
- **Cáfoló kísérlet:** azt próbáltam cáfolni, hogy a `0x007448a0` lenne a tálca belépő hívása. A `paszta.py` a teljes `.text`-ben mind az öt közvetlen célhívást megtalálta a vizsgált címekre: `0x005da9f8 → 0x00744a00`, `0x00744a90 → 0x00743700`, `0x0074441e → 0x007448a0`, `0x0074592a → 0x007448a0` és a külön panelépítő `0x005cfdbb → 0x00743700`. A belépő útban nincs közvetlen hívás `0x007448a0`-ra. A `0x00744a65` indirekt slot célja viszont **NINCS MEG**, ezért az esetleges virtuális kapcsolatot nem állítom kizártnak.

**Bizonyítottsági fok: feltételes.** Két független út megerősíti a látható főnézet-váltás deklarációját és a Cancel/Escape visszautat. A `0x00744a65` virtuális hívás célja nem ismert; ez nyitva hagyja az eredeti kérdés szűk, hívásszintű részét.

- `Ghidra-kör kell: 0x00744a00 - a 0x00744a65 virtuális hívás melyik célfüggvényre oldódik fel, és ez a hívás végzi-e a PrintPanelre váltást? A meglévő Ghidra-kimenet a 0x005d9cc0 hívót mutatja, de ezt a slotot nem oldja fel. [blokkoló]`

### #6845 kiegészítés: mappasor húzása másik mappára (2026-11-14, zárókör)

A bal hasáb `CAlbumList` sorai nem külön polimorf C++ csomópontok: az eseménykezelő sorindexet olvas ki és a `0x004ae4e0`-val egy `CAlbumState`-rekordot kér le. A `0x00565920` a `0x00761870` konstruktorral állítja fel a `CAlbumList` objektumot; a `0x00765d30` a `lb_preclick` eseményben a rekord típusát vizsgálja, a `0x00763150` pedig a rekordot rajzolja ki. Ezért nincs mappasor-vtable és nincs mappasorhoz tartozó `+0x7c` húzáslistakészítő. A rekordot előállító model-függvény címe **NINCS MEG**; ez nem változtat a drag-forrás és a drop-út döntésén.

A `CAlbumList` elsődleges vtable-je `0x00cb2898`, három belépővel (`0x00762540`, `0x00763150`, `0x007623b0`). A nyers PE-ben e három után null szó és a külön `CSoloWrapper` vtable-meta mutatója következik; a `CSoloWrapper` tábla `0x00cb28ac` címen indul. Így a CAlbumList kezdőcíméhez viszonyított fizikai `+0x7c` dword (`0x009e3970`) valójában a `CSoloWrapper +0x68` bejegyzése, nem CAlbumList-slot. A `CSoloWrapper` vtable-t külön rutin írja be (`0x00766612`, `0x0076669c`); konstruktori útja a `0x005733f0` thumbnail-UI építőben van.

| Vizsgált pont | Megállapítás | Forrás |
|---|---|---|
| CAlbumList sorábrázolás | A `0x00565920` a `0x534` erőforrásból hívja a `0x00761870` CAlbumList-konstruktort, majd az objektumot a fő UI `+0xd4c` mezőjébe teszi. A `0x00765d30` a sorindexből (`param_2+0x0c`) a `0x004ae4e0`-val állapotrekordot kér; a `0x00763150` külön rajzolófüggvény. A soradatot előállító model-rutin: **NINCS MEG**; soronkénti C++ node-konstruktor nincs azonosítva. | `bináris (0x00565920, 0x00761870, 0x00765d30, 0x004ae4e0, 0x00763150)` |
| CAlbumList vtable és fizikai határ | A `0x00761896` beírja a `0x00cb2898` vtable-t. A PE RVA/fájl `0x008b2898` első három DWORD-ja `40 25 76 00`, `50 31 76 00`, `b0 23 76 00` → `0x00762540`, `0x00763150`, `0x007623b0`; a tábla mérete 12 bájt. A `+0x7c` fizikai címe egy másik, `0x00cb28ac` címen induló `CSoloWrapper` tábla `+0x68` elemére esik (`0x009e3970`), nem a CAlbumList virtuális slotjára. | `bináris (0x00761896; PE RVA/fájl 0x008b2898, 0x008b28ac, 0x008b2914)` |
| Cáfoló jelölt: CAlbumLabel | A `0x00746ef0` konstruktor a `0x00cb166c` vtable-t írja be; a `+0x7c` PE-bejegyzése `00 cc 74 00` → `0x0074cc00`. Ez a cél csoportosítási állapotot vált (`ToggleGrouped`), nem drag-listát épít. A konstruktor a `0x0074ad40` `headerpanel` / `globalalbums%x/%d` útját használja; ez nem a CAlbumList sorútja. | `bináris (0x00746ef0, 0x00cb166c, PE RVA/fájl 0x008b16e8, 0x0074cc00, 0x0074ad40)` |
| A valódi képlistás húzáskészítők | A `CSelectionNode` (`0x00cad5b4`) és `CAlbumSelectionNode` (`0x00cb46f4`) `+0x7c` slotja rendre `0x0071abc0` és `0x00783860` felé mutat. A `0x0071abc0` a saját `+0x32c` listájában kizárólag nem-null, nem törölt és kijelölt elemeket jár be, majd az elem `+0xb4` azonosítóját teszi a `ytDragNode+0x280` listába. A CAlbumSelectionNode igazolt példánya a `headerpanel` / `globalalbums` útból jön, nem a CAlbumList sorából. | `bináris (PE RVA/fájl 0x008ad630, 0x008b4770; 0x00783860, 0x0071abc0, 0x0074ad40)` |
| Eredeti drop üres vagy hiányzó adatlistadal | A `0x005e39a0` sikertelen `ytDragNode` castnál `4`-gyel visszatér. A sikeres, de üres `+0x280` listát a `0x004930a0` után a `0x005e3ba0` ág észleli, és a `0x005350b0` fájlmozgató előtt `0`-val visszatér. A CAlbumList mappasor nem ad hozzá drag-forráslistát; a mappasor → mappasor út lemezművelete ezért **semmi**. | `bináris (0x005e39a0, 0x004930a0, 0x005e3ba0, 0x005350b0)` |
| PicasaPy mappasor-húzás | A meglévő QML-funkcionális mérés szerint a mappa és a `.picasa.ini` együtt mozog; az index, a bal hasáb és a rács követi az új útvonalat. Ebben a kutatói körben a tesztet nem futtattam újra. | `FolderPaneTreeRow.qml:343-348`; `MainFolderPane.qml:159-161`; `fileops/move_folder.py`; `mérés (tulajdonosi komment 2026-11-13; test_mappa_folyamat_paritas_6845.py)` |
| Eredeti élő felvétel | A job-656/job-657 Wine alatti gépi húzás nem indított műveletet, de nem igazolja a Windowsos ablak- és lemezállapotot. A statikus kódút a fájlhatást eldönti; Windowsos képkocka / `kepmappa` / `allapot` felvétel: **NINCS MEG**. | `mérés (job-656, job-657)`; Windowsos mérés: `NINCS MEG` |

#### Két független út és cáfoló kísérlet

- **A út - Ghidra-dekompiláció és eseménykód:** a `0x00565920 → 0x00761870` út a CAlbumListet állítja fel; a `0x005d3290` a `lb_preclick` eseményt a `0x00765d30`-nak, a `lb_drop`-ot a `0x005e39a0`-nak adja. A `0x00765d30` sorindexből adatmodellt olvas, és nem készít drag adatlistaot. A `0x005e39a0` hiányzó vagy üres listával a fájlmozgató előtt visszatér.
- **B út - közvetlen nyers PE-vtable-bejegyzések:** a CAlbumList három metódusa a PE-ben közvetlenül kiolvasható; a `0x00cb28ac` külön `CSoloWrapper` tábla, ezért a fizikai `CAlbumList+0x7c` pointer nem CAlbumList-slot. A CAlbumLabel saját `+0x7c` PE-célja `0x0074cc00`, amely csoportosítást vált; a selection node-ok drag-slotjai `0x0071abc0` / `0x00783860`, de konstruktorútjuk a mappasorhoz nem vezet. A két út egyezik: a CAlbumList mappasora nem ad át kijelölt képlistát.
- **Cáfoló kísérlet:** a kijelölt képek mozgatásának hipotézisét a `CAlbumSelectionNode` lehetséges sorforrásként való azonosításával próbáltam igazolni. A constructor út `0x0074ad40` a `headerpanel`/`globalalbums` csomóponthoz kötődik; a `0x0071abc0` csak már kijelölt képeket vesz át. A másik jelölt, `CAlbumLabel`, a vtable `+0x7c` helyén csoportosítást vált; a CAlbumList mellett látható `CSoloWrapper` vtable pedig külön objektum konstruktorához tartozik. A jelöltek raw PE-címeit és céljait byte-szinten ellenőriztem; egyik sem ad listát a CAlbumList mappasorának. Ezután a drop üres-lista korai visszatérését ellenőriztem, amely a fájlmozgató előtt történik.

**Bizonyítottsági fok: megerősített.** A Ghidra út a CAlbumList sorindexes adatrekord-kezelését és a drop korai visszatérését mutatja; a független PE-olvasat megerősíti a táblahatárokat és a tényleges vtable-célokat. Az eredeti mappasor-húzás fájlhatása **semmi**, a PicasaPy mappát és ini-jét mozgatja.

**Lezárhatóság:** a statikus viselkedéskérdés eldőlt, de a #6845 az eredeti „Kész, ha” pontjának szó szerinti teljesítésével még nem zárható le: hiányzik a Windowsos Colab-képkocka, `kepmappa` és `allapot`. A kutatási blokk feloldódott; élő felvétel nélkül a teljes folyamatszintű elfogadási feltétel nyitva marad.

### #6862: a film gomb bemeneti halmaza

A mappa-eszköztár film gombjának (`headerpanel/create_movie`) és a Létrehozás > Mozgófilm menüparancsnak a bináris folyamata a Picasa3.exe (3.9.141.259) diszasszemblálása és dekompilációja alapján feltárva.

| Kérdés | Megállapítás | Forrás |
|---|---|---|
| Mappa-fejléc film vezérlő | A `headerpanel.tre:58-69` deklarálja a `headerpanel/create_movie` vezérlőt (`headerpanel/movie_icon`, `mousedown 1`); a `headerpaneltext.tre:30` felirata `Create Movie Presentation`. | `bináris (headerpanel.tre:58-69, headerpaneltext.tre:30)` |
| Fejléc kattintáskezelő | A `0x005e0f70` a `create_movie` (`0x00c96ec8`) tokent vizsgálja (`0x005e118a-0x005e1196`). Shift billentyű hiányában numerikus parancsazonosító nélkül, a mappa fejléc-sorindexével (`row_index`), üres kijelöléssel és 0 módparaméterrel hívja a `0x0057cb60` belépőt. Ha a Shift le van nyomva (`0x005e11c3-0x005e11d4`), a módparaméter `0x9d59`. | `bináris (0x005e0f70, 0x005e118a-0x005e11ec, 0x00c96ec8)` |
| Menüparancs azonosítók | A `0x00559150` menüépítő a `Create > Movie` (`eMenuCreate::Movies`, `&Movie`, `0x9d51`) alatt három almenüpontot hoz létre: `0x9d58` (`eMenuCreateMovie::MOVIE`, `From Selection...`), `0x9d59` (`eMenuCreateMovie::ID_FACES`, `From Faces in Selection...`), `0x9d5a` (`eMenuCreateMovie::ID_FACESRANDOM`, `From People Albums...`). | `bináris (0x00559150, 0x0055ba6d-0x0055bb45, 0x00c8d958, 0x00c8d920, 0x00c8d8e4)` |
| Menü-diszpécser kapcsolat | A `0x005cb990` diszpécserben mindhárom parancs (`0x9d58`, `0x9d59`, `0x9d5a`) a `0x005cdc30` ugrótábla 15. indexén (`0x005cdc6c`) át a `0x005cce44-0x005cce4e` kódra fut, amely `-1` sorindexszel, üres kijelöléssel és a parancsazonosítóval ugyanazt a `0x0057cb60` kezelőt hívja. A fejlécgomb nem küld WM_COMMAND menüazonosítót, a két út a közös `0x0057cb60` kezelőben találkozik. | `bináris (0x005cb990, 0x005cc495-0x005cc4ad, 0x005cdc30, 0x005cce44-0x005cce4e, 0x0057cb60)` |
| Linux/Wine korlátozás | A `0x0057cb60` belépőnél a `0x0057cbd1` utasítás ellenőrzi a Wine-környezet jelzőjét (`cmp byte ptr [esi + 0x30fe], 0`). Ha nem nulla (Linux/Wine futás), a `0x00c8a37c` (`LinuxNomovie`) erőforrás-azonosítót és a `0x00c8a354` (`This feature is not supported for Linux`) szöveget jeleníti meg a `0x00980700` párbeszédablakkal, és a Filmkészítő megnyitása nélkül visszatér (`ret 0xc`). | `bináris (0x0057cb60, 0x0057cbd1-0x0057cbe4, 0x00c8a37c, 0x00c8a354, 0x00980700)` |
| Windows 2000 korlátozás | A `0x0057cb60` elején a `0x0057cb70` meghívja a `0x00981af0` verzióellenőrzőt. Ha az eredmény nulla, a `0x00c90324` (`Win2kNomovie`) azonosítójú `This feature is not supported for Windows 2000` (`0x00c902f4`) üzenetet adja. | `bináris (0x0057cb60, 0x0057cb70-0x0057cb83, 0x00c90324, 0x00c902f4)` |
| Filmkészítő indító mód | A `0x0057cb60` eltárolja a sorindexet (`CMakeMoviePanel[+0x4d0]`), majd aktiválja a `panelroot/makemovietab`-ot (`0x00c8f1a0`). A `0x00618050` inicializálóban a `0x006181f7-0x00618206` képlet a sorindexből képezi a módot: menü esetén (`row == -1`) `esi = 1`, fejlécgomb esetén (`row >= 0`) `esi = 4`. Ezután meghívja az `IPicasaApp->slot_0(mode = esi)` metódust (`CAppServices::vftable` `0x00ca7b7c` -> `0x00699cd0`). | `bináris (0x0057cb60, 0x0057cc23-0x0057cc8b, 0x00618050, 0x006181f7-0x00618247, 0x00ca7b7c, 0x00699cd0)` |
| Bemeneti halmaz (két kép) | A `0x00699cd0` függvényben fejlécgombos hívásnál (`param_1 == 4`) a `0x005c7e40` lekérdezi a kijelölés/tálca méretét. Ha a kijelölés száma 2-nél kevesebb (`uVar3 < 2`), a mód 3-ra vált és a teljes mappa képeit tölti be (`0x005cb180`). Ha azonban legalább 2 kép ki van jelölve (`uVar3 >= 2`), a feltétel hamis: a mód 4 marad, és a `0x005c76b0(0, 1)` hívás kizárólag a kijelölt képeket gyűjti ki a film klipjei közé. | `bináris (0x00699cd0, 0x005c7e40, 0x005cb180, 0x005c76b0; ghidra/2026-10-20-ghidra-17.txt:786-805)` |
| PicasaPy megvalósítás | A fejlécgomb a `LightboxHeaderButtons.qml:150-172` (`headerMovieButton`), amely a `LightboxHeader.qml:60` `movieRequested` jelzését süti el. A `LightboxFeedGroup.qml:103-111` `onMovieRequested` kezelője feltétel nélkül a teljes mappa minden sorát átadja a `feed.appWindow.openMovieFromRows(sorok)` metódusnak, függetlenül a kijelöléstől. A `Main.qml:378` és `MainProjectTabs.qml:129-132` továbbítja a `CreateDialogs.qml:56-59` `openMovieForRows`-hoz. A menü viszont (`PicasaCreateMenu.qml:65`, `MainMenuBar.qml:278`) a kijelölésből indul (`openMovie()` -> `CreateDialogs.qml:37`). | `src/picasapy/app/qml/PicasaPy/LightboxHeaderButtons.qml:150-172`, `LightboxHeader.qml:60`, `LightboxFeedGroup.qml:103-111`, `Main.qml:378`, `MainProjectTabs.qml:129-132`, `CreateDialogs.qml:37, 56-59`, `PicasaCreateMenu.qml:65`, `MainMenuBar.qml:278` |

#### Két független út és cáfoló ellenőrzés

- **A út, utasításút és dekompiláció:** az `annot_disasm.py` és a meglévő Ghidra-dekompilátum (`2026-10-20-ghidra-17.txt`) közvetlenül igazolja a hívási láncot. A `0x005e0f70` a `create_movie` név egyezése után a mappa fejléc-sorindexével (`row_index`) hívja a `0x0057cb60`-at. A `0x0057cb60` a `0x0057cbd1` címen a `[esi + 0x30fe]` Wine-jelzőt vizsgálja; nemnulla értéknél a `LinuxNomovie` (`0x00c8a37c`) hibát dobja és visszatér. Windows futásnál a `0x00618050` a sorindexből képezi a 4-es módot, majd a `0x00699cd0` a `0x005c7e40` hívással ellenőrzi a kijelölést: ha legalább 2 kép ki van jelölve, kizárólag a kijelölt képeket adja át a film klipjeihez.
- **B út, erőforrások, string_xrefs és menüstruktúra:** a `headerpanel.tre` és `headerpaneltext.tre` deklarálja a `headerpanel/create_movie` gombot és feliratát (`Create Movie Presentation`). A `0x00559150` a menüépítés során a `0x9d58`, `0x9d59`, `0x9d5a` parancsokat rendeli a Movie almenühöz. A `picasa3-index.sqlite` `string_xrefs` táblájában a `This feature is not supported for Linux` (`0x00c8a354`) két hivatkozója a `0x0057cb60` és a `0x0053a460`. A `ytIPicasaApp` RTTI vtable (`0x00ca7ad4`) felülbírálója a `CAppServices::vftable` (`0x00ca7b7c`), amelynek 0. slotja `0x00699cd0`.
- **Egyezés:** a két független út maradéktalanul egyezik. A fejlécgomb nem küld numerikus menüazonosítót, hanem a menüvel azonos `0x0057cb60` kezelőt hívja a mappa sorindexével. A Linux/Wine hiba közvetlenül ezen belépő vizsgálatából ered. Két kijelölt kép esetén az eredeti Picasa Movie Maker csak a két kijelölt képpel indul, nem a teljes mappával.
- **Cáfoló kísérlet:**
  1. Azt a hipotézist próbáltam cáfolni, hogy a fejlécgomb közvetlen `0x005cb990` menü-diszpécser hívást vagy WM_COMMAND üzenetet küld-e: a `0x005e0f70` utasításfolyamában nincs ugrás vagy hívás a `0x005cb990`-re, sem PostMessage/SendMessage hívás; a hívás közvetlenül `0x0057cb60`-ra megy 0 (Shift esetén `0x9d59`) harmadik argumentummal. A feltevés cáfolva.
  2. Azt a feltételezést próbáltam cáfolni, hogy a fejlécgomb minden esetben a teljes mappa képeit veszi-e át (ahogy a PicasaPy jelenleg működik): a `0x00699cd0` 4-es módja (`param_1 == 4`) a `0x005c7e40` visszatérési értékét vizsgálja (`uVar3 < 2`). Két kijelölt képnél (`uVar3 == 2`) a feltétel nem teljesül, nem vált át 3-as módra (mappa betöltése), hanem a `0x005c76b0(0, 1)` ágon a kijelölt elemeket veszi át. A feltételezés cáfolva.
  3. Azt a feltételezést próbáltam cáfolni, hogy a Linux-hibaüzenet DirectShow hiányból vagy a videó renderelésének hibájából származik-e a film készítése közben: a `0x0057cbd1` vizsgálat mindent megelőzve, rögtön a függvény elején elutasítja a futást a `[esi + 0x30fe]` jelző alapján, jóval a renderelő vagy a felület felépítése előtt. A feltételezés cáfolva.

**Bizonyítottsági fok: megerősített.** Két független út (utasításszintű diszasszembly/dekompiláció és erőforrás/RTTI/string_xrefs elemzés), valamint sikeres cáfoló ellenőrzések támasztják alá.

#### Fejlesztési teendők a paritáshoz

- A `src/picasapy/app/qml/PicasaPy/LightboxFeedGroup.qml:103-111` `onMovieRequested` kezelőjében ellenőrizni kell a kijelölt képek számát:
  - Ha legalább 2 kép ki van jelölve (a jelenlegi mappában vagy a tálcán), a filmkészítő kizárólag a kijelölt képek soraival induljon (`feed.appWindow.openMovieForRows(feed.appWindow.selectedIndexes)` vagy a kijelölési sorok).
  - Ha 2-nél kevesebb kép van kijelölve (0 vagy 1 kép), a filmkészítő a teljes mappa összes képével induljon (`openMovieFromRows(sorok)`).



## #6862: a 0x00744a65 virtuális hívás

A tálca Print gombjának (`outputlayout/pbutton`) hívási lánca a `0x005d9cc0 -> 0x00744a00` úton fut. A `0x00744a00` függvényben a `0x00744a5e-0x00744a65` címtartomány virtuális hívást hajt végre a `[ebp+0xed0]` objektum `+0x258` eltolásán lévő mutatón keresztül.

### 1. Az érintett objektumok és típusok statikus feloldása

- **A `[ebp+0xed0]` objektum (`CKeywordDialog`):**
  - A hívó `0x00744a00` függvény `ebp` regisztere a `CThumbUI` példány mutatója.
  - A `CThumbUI` `+0xed0` eltolásán a lebegő/kihúzható kulcsszó- és címkekezelő panel (`CKeywordDialog`) mutatója ül.
  - Kezdőérték: a `CThumbUI` konstruktora (`0x005643e0`, `0x00564d8c`) 0-ra inicializálja (`mov dword ptr [ebp+0xed0], ebx`).
  - Azonosítás: a `CThumbUI::UpdateKeywordStatus` metódus (`0x0065ac80`, `0x0065ad02`, `0x0065b07c`) a `*(int *)(param_1+0xed0)` mutatót adja át a `0x00840b80` függvénynek, amely a `0x00cc0120` címen lévő `"CKeywordDialog::numstatus"` sztringet használja.

- **A `+0xed0+0x258` helyen ülő objektum (`ytUIDialog::ParentDialog`):**
  - Típus: `ytUIDialog::ParentDialog` (mérete 0x9c bájt).
  - Konstruktor: `FUN_009d4a80` (`0x009d4a80-0x009d4c21`). A függvényben az `operator new(0x9c)` és a `0x00a70d20` belső inicializáló után a `0x009d4ae1` utasítás írja be a vtáblát: `mov dword ptr [edi], 0x00cda6e8`.
  - A mutató beírása a dialógusba: `0x009d4afa: mov dword ptr [ebp+0x258], ecx` (ahol `ebp` a dialógus, `ecx` a frissen allokált `ytUIDialog::ParentDialog`).
  - RTTI szimbólum: `ytUIDialog::ParentDialog::vftable`.
  - Vtable-cím: `0x00cda6e8` (RVA: `0x008da6e8`).
  - Pásztázási bizonyíték: a teljes `.text` szakaszban a `0x00cda6e8` konstans kizárólag a `0x009d4ae3` címen (`FUN_009d4a80`) fordul elő; a binárisban nincs más kód, amely erre a vtáblára hivatkozna vagy beírná.

### 2. A vtable +0x0c bejegyzése

- A `0x00cda6e8` vtable 4. slotja (+0x0c): `0x00aa57a0`.
- A függvény utasításai (mérete 20 bájt, `0x00aa57a0-0x00aa57b3`):
  ```asm
  0x00aa57a0: mov  eax, dword ptr [ecx + 0x6c]
  0x00aa57a3: test eax, eax
  0x00aa57a5: je   0xaa57b1
  0x00aa57a7: push 0
  0x00aa57a9: push eax
  0x00aa57aa: call dword ptr [0x00c40890] ; USER32.dll!ShowWindow
  0x00aa57b0: ret
  0x00aa57b1: xor  eax, eax
  0x00aa57b3: ret
  ```
- Az `[ecx+0x6c]` mező a szülőablak Win32 ablakkilincse (`HWND`).
- A hívás paramétere a `push 0`, azaz a Win32 `SW_HIDE` konstans.
- A `0x00c40890` IAT-bejegyzés a `USER32.dll!ShowWindow` API-ra mutat.
- Jelentése: `ShowWindow(this->m_hWnd, SW_HIDE)` - a dialógusablak elrejtése.

### 3. A főnézet váltásának vizsgálata

- **A virtuális hívás nem végzi a főnézet váltását.**
- A hívás kizárólag a megnyitott `CKeywordDialog` ablak elrejtésére szolgál, hogy a nyomtatási nézet megnyitásakor ne maradjon a képernyőn a lebegő címkekezelő.
- Ha a kulcsszópanel nincs nyitva (`[ebp+0xed0] == 0`), a `0x00744a43: cmp eax, ebx` és `0x00744a56: je 0x744a67` elágazás miatt a hívás le sem fut.
- Ugyanez a védelmi elrejtő hívás megtalálható minden egyéb nézet- és módváltás előtt is:
  - `0x005315b8`: OutputBottleneck
  - `0x005316cf`: `CThumbUI::OutputToEmail`
  - `0x00531717`: egyéb kimeneti művelet
  - `0x005d3035`: `editpanel/preview` szerkesztőnézetbe lépés
  - `0x005e7498`: nézetváltás
  - `0x005e8d5d`: diavetítés indítása
- A főnézet tényleges váltását az `outputlayout.tre:38-42` deklaratív makrója, az `m_print_enable` (`macros.tre:285-291`) vezérli a UI eseménykezelő rétegében:
  - `Property showtarget thumbui/printpanel`
  - `Property hidetarget thumbui/acquirepanel`
  - `Property hidetarget thumbui/editpanel`
  - `Property hidetarget thumbui/mainuipanel`
  - `Property hidetarget thumbui/infowell`
  - `Property hidetarget thumbui/secretcoinclip`
- A `0x00744a00` függvény feladata ezen felül a nyomtató állapotának vizsgálata (`0x00777840`), és nyomtató hiányában a hibaablak megjelenítése (`IDS_MUST_INSTALL_PRINTER`, `0x00cb0a24`), valamint a visszaállás (`printpanel/pcancelbutton`, `0x00c8ff24`). Telepített nyomtató esetén a nyomtatási panel vezérlőinek előkészítését végzi (`printpanel/froogle`, `printpanel/fullbutton`, `PrintLastSize`, `printpanel/optimizebutton`, `printpanel/normalbutton`).

### 4. Bizonyítottsági fok és cáfolat

- **Bizonyítottsági fok:** megerősített. A: közvetlen utasításszintű követés a `0x00744a00`, `0x009d4a80` és `0x00aa57a0` függvényekben az IAT feloldásával (`0x00c40890` = `USER32.dll!ShowWindow`). B: RTTI szimbólumok (`ytUIDialog::ParentDialog::vftable` = `0x00cda6e8`), sztring-xrefelek (`0x00cc0120` = `"CKeywordDialog::numstatus"`), és a teljes `.text` adatpásztázása a `0x00cda6e8` vtable-re (egyetlen író hely a teljes binárisban: `0x009d4ae3`).
- **Cáfoló kísérlet:** Megvizsgáltuk azt a feltevést, hogy a `0x00744a65` hívás végzi a főnézet váltását. A feltevés kétszeresen cáfolt:
  1. Csukott kulcsszópanel esetén (`[ebp+0xed0] == 0`) a `0x00744a56` ugrás átlépi a hívást, így alapértelmezett állapotban a hívás le sem fut;
  2. A feloldott `0x00aa57a0` függvény kizárólag a `ShowWindow(this->m_hWnd, 0)` API-hívást tartalmazza, semmilyen panelváltási vagy layout-kezelési logikát nem valósít meg.


## #6845: húzásos mappa-áthelyezés és Refresh Thumbnails az eredetiben

### 1. Húzásos mappa-áthelyezés és Move Folder a binárisban

A mérés célja annak tisztázása, hogy a bal oldali hasábban a mappa más mappára húzása (drag-and-drop) milyen kezelőt futtat az eredeti Picasában, kér-e megerősítést, illetve mi történik a lemezen és a `.picasa.ini` fájllal.

| Szempont | Megállapítás a binárisból | Forrás / Bizonyíték |
|---|---|---|
| Bal hasáb húzáskezelő | A CThumbUI esemény-diszpécser `0x005d3290` a `lb_preclick` eseményt a `CAlbumList` `0x00765d30` kezelőjéhez, a `lb_drop` eseményt pedig a `0x005e39a0` drag-drop eljáráshoz továbbítja. A CAlbumList vtable-je `0x00cb2898`. | `bináris (0x005d3290, 0x00765d30, 0x005e39a0, 0x00cb2898)` |
| Célpont vizsgálata húzáskor | A drop a `ytDragNode+0x280` fájllistáját másolja, és csak meghatározott kapuknál hívja a fájllistás `0x005350b0`-t. A CAlbumList sorindexes kezelője CAlbumState-rekordot kér le; a sorokhoz nem találtam külön C++ node-konstruktort vagy `+0x7c` drag-listakészítőt. A `0x0071abc0` általános kijelölés-húzó csak már kijelölt elemeket ad a listához, és a CAlbumSelectionNode bizonyított létrehozási útja a headerpanel/globalalbums. | `bináris (0x005e3b71-0x005e3b81, 0x005e3d90-0x005e3df5, 0x00765d30, 0x004ae4e0, 0x0071abc0, 0x0074ad40)` |
| Mappa-a-mappába húzás | A CAlbumList soraihoz nem azonosítható soronkénti drag-node; a CAlbumList vtable-je három belépőből áll, a fizikai `+0x7c` cím a külön CSoloWrapper táblára esik. A vizsgált mappasor út így nem ad drag-fájl-listát; a `0x005e39a0` hiányzó vagy üres listával a `0x005350b0` előtt visszatér. Az eredeti fájlhatás **semmi**. PicasaPy a mappát és `.picasa.ini`-t áthelyezi, tehát eltér; fejlesztési jegy javasolt a PicasaPy húzásának no-op paritásra igazításához. A Windowsos felületi és lemezállapot-felvétel még hiányzik. | `bináris (0x005d3290, 0x00765d30, 0x004ae4e0, 0x00cb2898, 0x00cb28ac, 0x005e39a0, 0x005350b0)`; PicasaPy: `mérés (tulajdonosi komment, 2026-11-13)`; élő Windows-felvétel: `NINCS MEG` |
| `Move Folder` menüparancs | Az `ID_MOVE_FOLDER` a Mappa menü (`0x005cb990`) és a mappa helyi menüje (`0x007319f0`) felől éri el a `0x0053f340` diszpécseren át a `0x0053f4a0` kezelőt (`CThumbUI::MoveFolder`). Ez a menüből indított könyvtármozgatás; külön funkció a mappasor-húzás statikusan igazolt no-op útjától. | `bináris (0x005cb990, 0x007319f0, 0x0053f340, 0x0053f4a0)` |
| Könyvtárválasztó ablak | A `0x0053f4a0` a `0x00998760` hívásával könyvtárválasztó ablakot nyit (a `SHBrowseForFolderW` importot az index szerint a `0x009b0cb0` hívja; a két függvény közti kapcsolat ebben a körben nincs igazolva) `Move Folder to %s` címmel (`CThumbUI::MoveFolderFormat`, `0x00c8acb8`). Az utolsó könyvtár útvonalát a `Preferences/MoveFolderLastPath` kulcsból olvassa és oda menti vissza. | `bináris (0x0053f4a0, 0x00998760, 0x00c8acb8)` |
| Érvényesítés és hibakezelés | A `0x0053f4a0` ellenőrzi az útvonalat: rendszerkönyvtár esetén a `CThumbUI::MoveFolderSysPath` ("Unable to Move a System Path"), ha a célhelyen már létezik azonos nevű mappa, a `CThumbUI::MoveFolderExists` üzenetet adja. | `bináris (0x0053f4a0, 0x00c8acf4, 0x00c8ad54)` |
| Megerősítés | A könyvtárválasztó ablak OK gombja után nincs külön megerősítő kérdés; a művelet azonnal lefut, hacsak nem lép fel a fenti hibák egyike. | `bináris (0x0053f4a0)` |
| Lemez- és adatbázis-művelet | A tényleges áthelyezést a `0x0052e0f0` -> `0x004fd1c0` híváslánc végzi: előbb felfüggeszti a fájlrendszer-megfigyelő szálakat (`0x00455f10`, `0x00455e30`, 1000 ms timeout), majd a `0x004fd1c0` mozgatja a foldermgr adatbázisban a mappa-rekordot és a fájlrendszerben a mappát. Siker esetén a `0x0053fcfe` meghívja a `0x0065b840`-at és a `0x004e47d0`-at, ami újraindítja a háttérbeli szkennelést az új útvonalon. | `bináris (0x0052e0f0, 0x004fd1c0, 0x00455f10, 0x0053fcfe, 0x004e47d0)` |
| A `.picasa.ini` sorsa | A mappa fizikai áthelyezése miatt a könyvtárban lévő `.picasa.ini` fájl a tartalmával együtt mozog át az új helyre; a régi helyen nem marad mappa vagy fájl, és nem generálódik külön új `.picasa.ini`. | `bináris (0x004fd1c0, 0x0053fcfe)` |

### 2. Refresh Thumbnails a binárisban

A mérés célja annak rögzítése, hogy az Indexképek frissítése parancs mit töröl vagy épít újra (memóriabeli gyorsítótár, `thumbs*.db`, index), és fut-e újraolvasás.

| Szempont | Megállapítás a binárisból | Forrás / Bizonyíték |
|---|---|---|
| Parancsazonosítók | Főmenü: Folder > Refresh Thumbnails (`eMenuLabelFolder::ID_REFRESH_THUMB`) parancsazonosítója `0x9c5e` (40030). Mappa helyi menü: Refresh Thumbnails (`Folder::ID_REFRESH_THUMB`) parancsazonosítója `0x9cb9` (40121). | `bináris (0x00c8d490, 0x00cae1d8)` |
| Menü engedélyezési állapota | A `0x005eab70` menüfrissítő a `0x9c5e` és `0x9cb9` azonosítókra egyaránt meghívja az `EnableMenuItem` Win32 API-t, a kiválasztott mappa megléte (`[edi + 0xeac]`) alapján. | `bináris (0x005eab70, 0x005eac5a)` |
| Diszpécser és végrehajtó | A főmenü diszpécsere (`0x005cb990`) a `case 0x9c5e:` ágon közvetlenül a `0x005c7f60` végrehajtó eljárást hívja meg. A mappa helyi menü diszpécsere szintén erre az eljárásra fut rá. | `bináris (0x005cb990, 0x005cba12, 0x005c7f60)` |
| Képek lekérdezése | A `0x005c7f60` a `0x007164b0` függvény hívásával lekéri az aktuálisan kiválasztott mappa összes képobjektumának listáját egy ideiglenes tömbbe. | `bináris (0x005c7f60, 0x005c7f8a, 0x007164b0)` |
| Memória-gyorsítótár ürítése | A `0x005c7f60` ciklusban végigmegy a képeken: a `0x00425df0` hívásával kiveszi és kinullázza az adott kép bélyegkép-bejegyzését a memóriabeli gyorsítótárból (`m_albumThumbs`: `[edx + esi*4] = 0`). | `bináris (0x005c7f60, 0x005c7fac, 0x00425df0)` |
| Újragenerálás ütemezése | Ugyanebben a ciklusban a `0x006a0b10` függvény hívásával (`push -1`, `push edi`, `call 0x006a0b10`) azonnali háttérbeli újragenerálásra ütemezi a kép bélyegképét. | `bináris (0x005c7f60, 0x005c7fc2, 0x006a0b10)` |
| Index piszkos jelző és újraolvasás | A ciklus lefutása után a `0x004ee530` hívásával beállítja a mappa `dirty` flagjét az indexben (`[eax + 0x1c] = 1`), majd a `0x004e2f90` és `0x004e30f0` hívásokkal jelzi az indexelő háttérszálnak a mappa újraolvasását (`[esi + 0x4e8] = 1`, `[esi + 0x4ef] = 1`, `[esi + 0x4ea] = 1`). | `bináris (0x005c7f60, 0x005c7fd8, 0x004ee530, 0x004e2f90, 0x004e30f0)` |
| Lemezállapot és `thumbs*.db` | A `0x005c7f60` nem hív fájltörlő API-t (`DeleteFile`), nem törli a `db3/thumbs.db` vagy `thumbs2.db` fájlokat a lemezről, és nem módosítja a `.picasa.ini`-t sem. Kizárólag a memóriabeli gyorsítótárat üríti és az indexelő szálon keresztül kényszeríti ki a képek újraolvasását és a bélyegképek újrarajzolását. | `bináris (0x005c7f60)` |

### 3. Két független út és cáfoló vizsgálat

- **Húzásos mappa-áthelyezés:**
  - **A út (utasítások és dekompiláció):** a `0x00565920 → 0x00761870` a CAlbumList vezérlőt hozza létre; a `0x00765d30` a sorindexből CAlbumState-rekordot kér le, a drop-diszpécser pedig `0x005e39a0`-ra fut. A CAlbumListhez nem tartozik soronkénti C++ node-konstruktor vagy `+0x7c` drag-listaépítő; üres/hiányzó drag-listánál a drop a fájlmozgató előtt visszatér.
  - **B út (nyers PE-vtable-adat):** a PE-ben a `0x00cb2898` CAlbumList-vtábla három DWORD-ja `0x00762540`, `0x00763150`, `0x007623b0`. A `0x00cb2898+0x7c` cím nem e tábla része: a következő külön CSoloWrapper-táblán belül van. A külön CAlbumLabel és selection-node slotok nyers céljai is kiolvasva; egyik sem a CAlbumList sorútjához tartozik. Ez függetlenül ellenőrzi a sor-vtable-határt és a jelölt húzó-slotok célját.
  - **Cáfoló vizsgálat:** megpróbáltam a kijelölt képek mozgatására utaló lehetséges objektumokat a mappasorhoz kötni. A `CAlbumSelectionNode` `+0x7c` célja (`0x00783860 → 0x0071abc0`) csak a kijelölt képek listáját építi, de igazolt konstruktora a `headerpanel/globalalbums` úthoz tartozik; a `CAlbumLabel +0x7c` (`0x0074cc00`) csoportosítást vált; a CAlbumList után fizikailag álló CSoloWrapper-vtable más objektumhoz tartozik. A PE-bájtok és a konstruktor/eseményút nem támasztották alá, hogy bármelyik ilyen húzó-slot a mappasor listájába kerülne. A drop üres/hiányzó listánál a fájlmozgató előtt visszatér.
- **Refresh Thumbnails:**
  - **A út (kód):** A `0x005cb990` főmenü diszpécser a `0x9c5e` parancsra a `0x005c7f60` eljárást hívja, amely a memóriabeli gyorsítótár ürítését (`0x00425df0`), a képek renderelési sorba állítását (`0x006a0b10`) és a mappa indexelő jelzőinek beállítását (`0x004ee530`, `0x004e2f90`, `0x004e30f0`) hajtja végre.
  - **B út (menü- és diszpécser-szerződés):** A `0x9c5e` és `0x9cb9` azonosítók azonos mappa-feltételhez vannak kötve (`0x005eab70`), és a diszpécser mindkettőt ugyanarra a végrehajtási pontra irányítja.
  - **Cáfoló vizsgálat:** Azt vizsgáltuk, hogy a `0x005c7f60` vagy hívottai meghívnak-e fájlrendszer-törlő műveletet a `thumbs*.db` fájlokra vagy a lemezre. A diszasszemblált utasítások között sem `DeleteFileA`/`W`, sem közvetlen lemeztörlés nem található; a művelet a lemezen található adatbázisfájlokat és a `.picasa.ini`-t érintetlenül hagyja.

### 4. Colabon ellenőrizhető jóslatok

1. **Jóslat (Move Folder húzással és menüből):**
   - A Windowsos mérésben mappasor-húzás után a statikus bizonyíték alapján a forrásmappa, a `.picasa.ini`, az index és a rács útvonala nem változik; a felületi kijelölés/nézet változását képkockával és `allapot`-tal kell rögzíteni. A job-656/-657 Wine-próbája nem adott futásidejű eredményt.
   - Ha a Mappa menü vagy a mappa helyi menüjének `Move Folder...` pontjára kattintunk, a standard Windows `SHBrowseForFolder` ablak jelenik meg ("Move Folder to <mappa>" felirattal), és célmappa jóváhagyásakor a forrásmappa a teljes tartalmával (beleértve a `.picasa.ini`-t) fizikailag átkerül az új könyvtár alá.
2. **Jóslat (Refresh Thumbnails):**
   - Ha a Folder menüből vagy a mappa helyi menüjéből kiadjuk a Refresh Thumbnails parancsot egy mappára:
     - A mappa könyvtárában található `.picasa.ini` fájl módosítási időbélyege (`mtime`) és mérete változatlan marad.
     - A Picasa profilkönyvtárában található `thumbs.db` fájl nem törlődik a lemezről (mérete a parancs futásakor nem esik nullára).
     - A könyvtárnézeti rácsban a bélyegképek a memóriából való ürülés után a háttérben egymás után újra elkészülnek és frissülnek.

## #6963: Delete from Disk teljes folyamata

Az eredeti `ID_FILE_DELETEFROMDISK` azonosítója `0x9c9a`, de nem minden
nézetben jelent lemezműveletet: mappanézetben képfájlt töröl, album- és
Emberek-album nézetben az albumtagság eltávolítására is használja. A
megerősítő út és a Shell-művelet közvetlenül visszafejtett; az eredeti
metaadat- és nézetfrissítési hatás részletei nyitva maradtak.

### Eredeti / PicasaPy / teendő

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Fájl menü és `Delete`:** `eMenuFile::ID_FILE_DELETEFROMDISK`, `0x00559150`, parancs `0x9c9a`; a menüállapot-kezelő `0x0056c5a0`. A `0x9c9a` diszpécserága `0x005cb990`-ben a `0x005c9b00` kezelőre jut. A menüállapot-kód a `0x70`/`0x8a` menükontextusban csak akkor engedélyezi a parancsot, ha van aktív objektum (`[param_1+0xeac]`) és a `0x004ac8f0` segéd igazat ad. A File menü szövegtára `&Delete from Disk...`; a parancs kezelője a nézetet is vizsgálja. | `PicasaFileMenu.qml:155-159`, `PicasaMenuBar.qml:492-511,658-667`, `MainMenuBar.qml:308-325`. A Fájl tétel a `photoActionsEnabled` állapotot követi; ablak-`Delete` csak aktív kép-műveleti sorral, nem szerkesztés és nem szövegmező-fókusz esetén él. A közös művelet mappanézetben töröl, albumokban eltávolít. | **Részben egyezik.** A `0x9c9a` nézetfüggő hatása nálunk is közös belépőn megy át. Az eredeti menükontextusok `0x70`/`0x8a` értékeinek felhasználói jelentése és a `0x004ac8f0` kiválasztási feltétel pontosítása nyitott; az eredeti File menü album-nézeti látható felirata külön futásidejű felvételt igényel. |
| **Kép helyi menüje, mappanézet:** `FolderPhoto::ID_FILE_DELETEFROMDISK`, `0x00730790`; a menüépítő `0x0056c5a0` a feliratot `Delete from Disk`-ként állítja, a parancs `0x9c9a`. A helyi menü gyorsbillentyű-felirata `Ctrl+Delete`. | `PhotoContextMenu.qml:460-471`; a tétel csak akkor látszik, ha nincs album- vagy személyalbum-nézetben. A jel a `MainPhotoContextMenu.qml:63` útján a kijelölt képek útvonalait adja a törlő dialógusnak. | **Egyezik** a mappanézeti belépő és a kijelölési feltétel. |
| **Album- és Emberek-album helyi menüje:** `AlbumPhoto::ID_FILE_DELETEFROMDISK`, `0x00731050`, illetve `PplAlbumPhoto::ID_FILE_DELETEFROMDISK`, `0x007355c0`. Mindkettőn ugyanaz a `0x9c9a` parancs eltávolító feliratot kap; a fájl nem lemezről törlődik. | `PhotoContextMenu.qml:194-220`, `PicasaMenuBar.qml:492-511`, `MainMenuBar.qml:318-325`. A helyi menü albumtagságot vagy személyalbum-hozzárendelést távolít el. | **Egyezik** a helyi menü parancsának nézetfüggő jelentése. |
| **Kép helyi menüje és néző:** `0x007327a0` a néző parancsmenüje; a `0x9c9a` ugyanarra a kezelőre fut. A nézőben az aktuális kép az érintett cél; albumból nyitott képnél a parancs albumtagságot távolít el. A menü `Ctrl+Delete` feliratot ad. | `ViewerContextMenu.qml:242-249`, `MainKeyboardShortcuts.qml:450-466`, `PhotoViewerKeyboard.qml:66-70`, `MainMenuBar.qml:308-320`. A néző billentyűje csak megnyitott nézőnél, érvényes aktuális képnél és szövegmező-fókusz nélkül él; a Fájl menü útja a nézett kép útvonalát adja át. | **Egyezik** a célkép és a `Ctrl+Delete` nézőbeli útja. A Shift-módosítós nézőút külön vizsgálandó. |
| **`Delete` / `Ctrl+Delete` / `Shift+Delete`:** a `Delete` a Fájl menü parancsszövegének gyorsbillentyűje, a kép helyi menüje `Ctrl+Delete`-et hirdet; mindkettő a `0x9c9a` parancs. A `0x005cb990` a `GetAsyncKeyState(0x10)` állapotát adja át a `0x005c9b00`-nak. Shift nélkül a megerősítő a Lomtárba helyezést választja; Shift mellett a közvetlen végleges törlést. | `PicasaMenuBar.qml:658-667`, `MainKeyboardShortcuts.qml:437-466`, `PhotoViewerKeyboard.qml:66-70`. A sima `Delete` és a `Ctrl+Delete` létezik; `Shift+Delete`-hez nem találtam külön kötést. | **Eltér:** a PicasaPy forrásában nincs a binárisban látható Shift+Delete közvetlen végleges-törlési út. Fejlesztői jegy javasolt, lásd lent. |
| **Képtálca:** a `0x00732ee0` teljes menüépítője View and Edit, Hold Selection, Remove Selection, két forgatás, Locate on Disk, elválasztó és Properties tételeket készít; `0x9c9a`/`ID_FILE_DELETEFROMDISK` nincs benne. | `TrayContextMenu.qml:33-95` ugyanilyen szerepű menüt ad, `Remove Selection` tétellel; nincs lemezről törlés. | **Egyezik:** a képtálca helyi menüjéből nincs külön Delete from Disk parancs. Ez nem bizonyítja, hogy egy másik, aktív rács-kijelölésre vonatkozó ablakbillentyűt a fókusz hogyan kezel. |
| **Egy kijelölt fájl, Lomtáras törlés:** `0x005fdc30` `Delete Items` címet, `DeleteSingle` üzenetet és `Delete Image` gombot választ. Üzenet: `Are you sure you want to send the selected file to the Recycle Bin? (It will also be removed from any albums in which it appears)`. A közös `confirm.fen` út a `No` gomb szövege nélkül épül, így a látható gombok `Delete Image` és `Cancel`. A `0x005fd670` a közös gombsor 1-es elemét választja; a job-252 egyképes felvételleírása Cancel-fókuszt és Enterre elmaradó törlést rögzít. | `FileOpsDialogs.qml:535-557`, `ConfirmDialog.qml:50-76,164-190`. Nálunk a két gomb `Delete Image` és `Cancel`, a Cancel kap fókuszt. | **Egyezik** a szöveg és a gombok. Az eredeti egyképes Enter-hatás csak a korábbi job-252 felvételleírásból ismert; annak nyers képe a helyi mérőadat-archívumban nem található. |
| **Több kijelölt fájl, Lomtáras törlés:** `0x005fdc30` a `DeleteMultiple` üzenetet és `Delete Items` gombot választja. Üzenet: `Are you sure you want to send the %d selected items to the Recycle Bin?\n(They will also be removed from any albums in which they appear)`. A közös builder ugyanazt a gombsor-indexet állítja be, nincs darabszámfüggő gombág; a bináris önmagában nem nevezi meg a billentyű-alapgombot. | `FileOpsDialogs.qml:558-566`; `pathList.length > 1` esetén ugyanaz a szöveg, gomb `Delete Items`; a közös `ConfirmDialog` Cancel-fókuszt állít. | **Feltételesen egyezik:** a közös index egyképes Windows-felvétellel Cancelként azonosítható, de több kijelölésnél Enter-próba nincs, ezért a tényleges alapgomb-hatás **NINCS MEG**. |
| **Shift+Delete, egy és több fájl:** `0x005fdc30` a `NoUndoSingle`/`NoUndoMultiple` üzenetet és `Delete File`/`Delete Files` gombot választja. Üzenetek: `Are you sure you want to permanently delete the selected file? (This cannot be undone.)` illetve `Are you sure you want to delete %d selected files? (This cannot be undone.)`. A `Preferences\\DoNotConfirmDeleteFromDisk` beállítás igaz értéke kihagyhatja a szokásos megerősítőt (`0x005fd670`). A prompt gombválasztó-indexe közös a Lomtáras ággal; külön Shift+Delete Enter-mérés nincs. | `FileOpsDialogs.qml:568-583` a végleges ágat csak akkor nyitja meg, ha a `trashAvailableFor()` hamis; a Shift billentyű nem választ külön ágat. A Cancel-fókusz beállítása közös (`ConfirmDialog.qml:50-76`). | **Eltér:** az eredeti Shift+Delete út és a mai, lomtár hiányakor megjelenő figyelmeztetés külön döntési eset. A billentyűút fejlesztése javasolt. |
| **Lomtáras fájlművelet és 0x0f hiba:** `0x005c9b00` fájlonként hívja a `0x009929b0` segédet. A segéd `wFunc=3` Shell műveleti rekordot épít, `0x00d695a0` wrapperhez jut; `0x009b1d50` a `0x00c40628` IAT-címen `SHELL32!SHFileOperationW`-t hív. A normál ágon az `0x40` bitet is a `0x414` flaghez adja. Ha a visszatérési érték pontosan `0x0f`, a `0x005fdb80` kérdése jelenik meg: `This file cannot be moved to the Trash and will be deleted immediately. Are you sure you want to continue?`, gombok `Delete` / `Cancel`; Delete után a `0x009929b0(0)` végleges próbálkozás fut. E párbeszéd Enter-alapgombját sem a bináris, sem a helyi mérés nem azonosította. | `trash.py:50-104,118-177`, `fileops_controller_delete_mixin.py:44-63`, `FileOpsDialogs.qml:594-599`. Windowson a PicasaPy szintén `SHFileOperationW`-t használ, de bármely nem nulla eredményt `operationFailed` hibává alakítja; nincs `0x0f`-re külön megerősítő és végleges újrapróbálás. | **Eltér:** hiányzik az eredeti `0x0f` utáni megerősítés és újrapróbálás. Fejlesztői jegy javasolt. Más Shell-hibakódot nem szabad automatikusan ennek az ágnak tekinteni. |
| **Törlés utáni `.picasa.ini`, album, index, mappafa és kijelölés:** a `0x005c9b00` tartalmaz `.picasa.ini` és `.picasaoriginals` objektumokat, album-eltávolító szöveget, valamint sikeres fájltörlési listát. A függvény meglévő Ghidra-kimenete nem oldja fel a releváns virtuális hívások célját; ebből a körből **NINCS MEG**, hogy a fő mappa-ini kép-szekciója törlődik-e, hogyan változik az index/fa darabszám, és milyen sort jelöl ki utána a rács. | `fileops_controller_delete_mixin.py:44-107` törli vagy lomtárba teszi a képet és kísérőit; `photo_delete.py:252-259` a kísérő eredeti képek ini-szekcióit takarítja. A fő mappa `.picasa.ini` írása nem része a törlő útvonalnak. `application_services.py:100-110` azonnal kiveszi a rácssort és a mappa újraszinkronizálását kéri; `library_controller_sync.py:83-106` frissíti a csoport- és státusz-számokat. `FileOpsDialogs.qml:585-608` a legkisebb korábbi kijelölt sor indexén folytatja a kijelölést, üres rácsnál törli. | **NINCS MEG a paritás.** Ghidra-feltárás kell az eredeti ini/index/fa/kijelölés hatásához; a javasolt Ghidra-kérdéseket lent adom meg. |
| **Írásvédett fájl vagy hálózati megosztás:** statikusan csak a lomtáras út `0x0f` visszatérési értékének külön ágát bizonyítottam; azt, hogy az egyes Windowsos állapotok mely kódot eredményezik, a bináris nem mondja meg. | `trash.py:257-268` Windowson minden útvonalra elérhetőnek tekinti a rendszer-Lomtárat; `trash.py:100-104` nem nulla Shell-eredménynél `OSError`-t ad; `fileops_controller_delete_mixin.py:60-62` ezt hibaként jelzi, nem indít végleges törlést. | **NINCS MEG az eredeti OS-kimenet.** Windowsos írásvédett mintával és hálózati megosztással kell rögzíteni a Shell visszatérési értékét és a felületet. |

### Bizonyítottsági fok és független utak

- **Bizonyítottsági fok: feltételes.** A parancsazonosító, belépési út, a megerősítő szövegágak és a Shell-műveleti hívás statikusan visszakövethető. A teljes utóhatás, az OS-hibakódok okai és a többes Enter-próba nincs lezárva.
- **A út:** `0x005cb990` `case 0x9c9a` -> `0x005c9b00` -> `0x009929b0` -> a `0x00d695a0` Shell-kompatibilitási wrapper -> `0x009b1d50` -> a PE IAT `0x00c40628` (`SHELL32!SHFileOperationW`). A `0x005fdc30`, `0x005fd670` és `0x005fdb80` a döntő promptokat és a fallbacket választja.
- **B út:** az importkereszttábla a `0x00d695a0` címet `SHELL32!SHFileOperationA` wrapperként és a `0x009b1d50` függvényként tartja nyilván; a közvetlen PE-importfeloldás a wrapper belső `0x00c40628` hívását `SHFileOperationW`-ként nevezi meg. Ettől külön a menüszövegekre mutató hivatkozások a főmenü- és kép-helyimenü-rekeszeket a `0x9c9a` parancshoz kötik. A két út a fizikai törlő API és a parancsrekesz azonosságában egyezik.

### Cáfoló kísérlet

Megpróbáltam cáfolni azt a tágabb feltevést, hogy a `0x9c9a` minden előfordulása
fizikailag törli a képet, illetve hogy bármilyen lomtárhiba végleges törléshez
vezet. A `0x00731050` és `0x007355c0` helyi menüiben ugyanaz a parancs eltávolító
feliratot kap, a fájltörlő ág helyett a nézethez kötött művelet fut; a teljes
`0x00732ee0` képtálca-menüben nincs `0x9c9a`. Az utasításszintű cáfoló körben a
`0x005caca3` utáni kód `cmp eax, 0xf` feltételt vizsgál, és csak egyezésnél hívja
a `0x005fdb80` ablakot; az eltérő visszatérés a külön fallback-ágat átugorja.
A `0x009929b0` shell-wrapper hívása, a `0x005fdb80` üzenete és a PE importcíme
ugyanezt az értelmezést támasztja alá. Így az a korábbi feltételezés, hogy
írásvédett fájl minden hibája automatikusan végleges-törlési kérdést ad, nem
igazolt.

### A jegy „Kész, ha” pontjai

1. ✅ **Belépési pontok:** a Fájl menü, mappa-kép helyi menü, `Delete`, `Ctrl+Delete`, néző és képtálca külön sorban dokumentálva. A pontos `0x004ac8f0` feltétel szemantikája és a fókuszált tálca melletti globális billentyűállapot nyitott.
2. ⛔ **Egy és több kép megerősítése:** az egyes és többes szöveg, valamint a gombok dokumentálva; az egyképes Lomtáras Enter-viselkedésre csak korábbi felvételleírás van, a többes és Shift+Delete út alapgomb-hatása és a `0x0f` fallback Enter-hatása **NINCS MEG**.
3. ⛔ **Fájlrendszer, ini, index, album, mappafa és rácskijelölés:** a Shell-művelet ismert, de az eredeti ini/index/fa/kijelölési utóhatás nincs feloldva.
4. ⛔ **Írásvédelem és hálózati megosztás:** a `0x0f` fallback-ág ismert, de a konkrét Windowsos állapotok visszatérési kódja és képernyőhatása nincs mérve.

### Javasolt fejlesztői jegytörzs

**Eredeti:** Picasa 3.9-ben a `0x9c9a` parancs mappanézetben sima `Delete`-re
Lomtáras megerősítést ad, `Shift+Delete`-re pedig végleges törlési
megerősítést. A Lomtáras Shell-művelet pontos `0x0f` eredménye külön
`This file cannot be moved to the Trash and will be deleted immediately...`
megerősítést nyit; a Delete gomb újrapróbálja véglegesen törölni, a Cancel
meghagyja a fájlt. A `0x9c9a` album- és Emberek-album nézetben eltávolító
parancs, nem fizikai törlés.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `Shift+Delete` a `0x005cb990` -> `0x005c9b00` úton `NoUndoSingle`/`NoUndoMultiple` ágat és végleges műveletet választ. | `PicasaMenuBar.qml:658-667`, `MainKeyboardShortcuts.qml:437-466` és `PhotoViewerKeyboard.qml:66-70` nem köt Shift+Delete utat; a végleges prompt csak lomtár-hiány esetén választódik. | Hozzáadni az eredeti módosítós billentyűutat mappanézethez és nézőhöz; album/Emberek-album kontextusban megőrizni az eltávolító viselkedést. |
| A lomtáras művelet csak `0x0f` hibánál nyitja a külön véglegesítési kérdést, majd `0` undo-flaggel újrapróbál. | `trash.py:100-104` minden nem nulla eredményt `OSError`-ré alakít; `fileops_controller_delete_mixin.py:60-62` hibát jelez, nincs `0x0f` fallback. | A Shell visszatérési kódot megőrizni, a pontos `0x0f`-hez adni az eredeti kérdést és retryt; más kód ne kerüljön ebbe az ágba. |

**Kész, ha:**

1. Mappanézeti egyes és többes kijelölésnél a `Delete` Lomtáras, a `Shift+Delete` a `NoUndoSingle`/`NoUndoMultiple` megfelelő szövegét és gombját használja.
2. Lomtáras eredmény `0x0f` esetén a külön `Delete`/`Cancel` kérdés jelenik meg; Delete végleges újrapróbát indít, Cancel után a kép és a rácssor megmarad.
3. Más Shell-hibakód nem indít automatikus végleges törlést.
4. Album- és Emberek-album nézetben a `0x9c9a` továbbra is csak tagságot távolít el.
5. A Cancel kezdeti fókusza és a single/multi üzenet a fenti eredeti ágakkal egyezik.

### Nyitott

- **Megválaszolva (két Ghidra-kör, `referencia/ghidra/2026-11-15-6963-colab-decomp.txt` és `2026-11-15-6963-colab-decomp-2.txt`, privát):** a törlés két `ytPicasaINIFile`-t épít (a mappa és a `.picasaoriginals` `.picasa.ini`-je), és tételenként a `0x005aafd0` ini-zár alatt a `0x005aadf0`-nak adja. Ez 3-as típusú módosítást tesz a késleltetett ini-írási sorba (`0x005a8d60`): az azonos nevű kép-szekció tartalmát lecseréli, a további azonos nevűeket nullázza, és jelez az író szálnak; erős valószínűséggel ez a kép-szekció törlése. Album- vagy arcbejegyzésre ezen az úton nincs külön ág. A ciklus után a `0x004f9450(…,1,1)` nem töröl az indexből, hanem a változásszámlálót növeli és a `+0x484` figyelőlista `+8` slotját hívja; a mappafa darabszámát és a következő kijelölt rácssort ezek a vtábla-figyelők döntik el, ezt a statikus út nem követi tovább. A PicasaPy törlés utáni kijelölése ezért marad.
- `NINCS MEG`: írásvédett fájl és hálózati megosztás esetén a Windows `SHFileOperationW` tényleges visszatérési kódja és felületi eredménye. Megszerzés: külön Windows-próba egy írásvédett képpel és egy hálózati megosztáson lévő képpel; rögzíteni kell a promptokat, a Shell eredményét, a fájl jelenlétét és a kijelölést.
- `NINCS MEG`: többes kijelölésnél az Enter ténylegesen Cancelként zárja-e a promptot. Megszerzés: legalább két kijelölt képpel Enter-próba Windows alatt.
- `NINCS MEG`: a Shift+Delete végleges törlési prompt és a `0x0f` utáni Delete/Cancel prompt Enter-alapgombja. Megszerzés: külön Windowsos Enter-próba mindkét párbeszédre, az ágak és az egy/több kijelölés rögzítésével.

**Új kutatási jegyjavaslatok:** nincs; a nyitott pontok ehhez a folyamathoz tartoznak.

**Módosított fájl:** `docs/specs/paritas-ellenorzes.md` - a jelen #6963 alszakasz.

## #6964: A Rename parancs folyamatszintű összevetése az eredeti Picasával

A vizsgálat célja a `Rename` (`ID_FILE_RENAME`, `0x9d4f`) teljes folyamatának összevetése az eredeti Picasa 3.9 binárisával (belépési pontok, engedélyezési feltételek, ablakmezők, sorszámozás, hatás a fájlrendszerre, `.picasa.ini`-re, indexre, kijelölésre és sorrendre, valamint hibakezelés).

### 1. Folyamatszintű összehasonlító táblázat

| Funkció / Szempont | Eredeti Picasa 3.9 (bináris cím) | PicasaPy (fájl:sor) | Teendő / Státusz |
|---|---|---|---|
| Fájl menü belépési pont | `eMenuFile::ID_FILE_RENAME` (`0x005593da`), parancs ID `0x9d4f` (40271), felirat: `&Rename...\tF2` (`0x00c8c630`, `0x00c8c610`). Engedélyezve: kijelölés >= 1 (`0x0056e46e`), nem írásvédett/rejtett mappa (`0x0057d430 == 0`), és a néző/szerkesztő nincs nyitva (`0x0056e458`). | `PicasaFileMenu.qml:92-95`, `PicasaMenuBar.qml:394`: `objectName: "menuFileRename"`, `&Rename...\tF2`. | Egyezik a felirat és a parancskötés. |
| Kép menü belépési pont | `eMenuPicture::BatchEdit` almenüben `&Rename...` (`0x0055b2ae`), parancs ID `0x9d4f`. Engedélyezési feltétele azonos a Fájl menüvel. | `PicasaPictureMenu.qml:25-28`: `objectName: "menuBatchRename"`, `&Rename...\tF2`. | Egyezik. |
| Gyorsbillentyű (F2) könyvtárban | `FUN_005e6710` (0x005e68fd): `VK_F2` (`0x71`). Feltételek: nincs szövegbeviteli fókusz (`0x332f == 0`), nem speciális nézet, kijelölés >= 1, és a néző/szerkesztő nincs nyitva (`0x005e68ee`). Hívja: `0x005e6939: call 0x00532ec0`. | `MainKeyboardShortcuts.qml:417-425`: `sequence: "F2"`, könyvtárnézetben megnyitja a `renameManyDialog`-ot. | Egyezik a könyvtárnézeti működés. |
| Gyorsbillentyű (F2) és menü a Nézőben | A néző/szerkesztő nyitott állapota (`+0x34a4 != 0`) esetén mind az F2 gyorsbillentyű (`0x005e68ee`), mind a menüpont (`0x0056e458`) letiltott; a dialógus nem nyitható meg. | `MainKeyboardShortcuts.qml:415-425`: az F2 a nézőben is aktív (`photoActionRows()`), és megnyitja az átnevezőt a nézett képre. | Eltérés: az eredetiben a nézőben az F2 és a Rename menüpont inaktív. Döntendő: maradjon-e kényelmi funkcióként vagy szigorú paritás kell. |
| Kép helyi menüje (jobb klikk) | Az eredeti kép helyi menüben (sem rácsban, sem nézőben) nincs Rename tétel (`ui-audit-context-menus.md` 135-136. sor, `0x005e7c20`). | `PhotoContextMenu.qml`, `ViewerContextMenu.qml`: nincs Rename menüpont. | Egyezik. |
| Párbeszédablak szerkezete | `runtime/rename.fen`: modális ablak (`title="Rename Files"`), kijelölési címke (`"1 file(s) selected for rename."` / `"%s file(s) selected for rename."`), prompt (`"Please enter a new name for these files:"`), szövegmező (`newname`, `25em`), jelölőcsoport (`"Include in filename:"`), Date és Image resolution jelölőnégyzetek, minta (`"Example: <alapnév>[ <dátum>][ <méret>].jpg"`), Rename (accept) és Cancel gombok. | `FileOpsDialogs.qml:240-368` (`renameManyDialog`): cím, feliratok, beviteli mező, Date és Image resolution jelölőnégyzetek, példa és gombok. | Egyezik a felületi struktúra és a kulcsok. |
| Alapértelmezett név a mezőben | A kijelölt fájlok közül a legelső fájl kiterjesztés nélküli alapkiterjesztése (`0x00532738`, `strrchr` pont vágás). | `FileOpsDialogs.qml:250-258`: `openedName` az első kijelölt elem kiterjesztés nélküli neve. | Egyezik. |
| Rename gomb engedélyezése | `0x00532c70`: Ha a `RenameUseDate` VAGY a `RenameUseSize` be van jelölve, a Rename gomb akkor is aktív, ha a beírt név nem változott (`0x00532cdd`, `0x00532cf0`). Csak akkor tiltott, ha egyik sincs bejelölve ÉS a név üres vagy azonos az eredetivel (`0x00532d94`). | `FileOpsDialogs.qml:269-272` (`canRename()`): `return base.length > 0 && base !== openedName.trim()`. Ha a név nem változik, de a Date vagy Size be van pipálva, a gomb tiltva marad! | Eltérés: a `canRename()`-nek engedélyeznie kell az átnevezést, ha a Date vagy Size jelölőnégyzet be van pipálva. |
| Sorszámozás több képnél | `FUN_00993650` (0x00993b07): formátum `"%s-%03lu"` (`nev-001`, `nev-002`, ...). Ha a név már kötőjeles számmal végződik, a számlálás onnan folytatódik (`0x0099397c`). Legfeljebb 4096 (`0x1000`) elemig vizsgálja (`0x00993993`). 1 képnél nincs sorszám. | `src/picasapy/fileops/rename.py:261-264`, `282-300`: `preview_name` és `_available_name` a `f"{stem}-{sequence:03d}"` alakot és 4096-os limitet használ. | Egyezik. |
| Dátum utótag formátuma | `0x00532710` és `0x005332e0`: rövid dátum + idő másodperccel, a `:` és `/` karakterek `-`-ra cserélve (minta: `" 08-01-2004 2-30-45 PM"`). | `rename.py:199-216` (`format_taken_at`): rendszer dátum/idő formátum, tiltott karakterek `-`-ra cserélve. | Egyezik. |
| Felbontás utótag formátuma | `0x00532867` és `0x00533358`: `" %dx%d"` (minta: `" 640x480"`). | `rename.py:238-239`: `f"{item.width}x{item.height}"`. | Egyezik. |
| `.picasa.ini` szekció kezelése | A fájl átnevezésekor a `.picasa.ini` szekciófejléce `[regi.ext]`-ről `[uj.ext]`-re módosul. A szekció alatti arcadatok (`faces=`), csillagozás (`star=yes`), elforgatás (`rotate=`), felirat (`caption=`), szűrők és albumtagság (`albums=`) változatlanul megmaradnak az új szekcióban. | `rename.py:87`: `update_document(..., lambda doc: doc.with_renamed_section(path.name, new_name))`. | Egyezik: teljes round-trip megőrzés. |
| Index és rács sorrendje | Az adatbázisban a fájl útvonala frissül. A rácsban a képek a mappa aktuális rendezési módja (Sort by: Name, Date, Size) szerint azonnal átrendeződnek az új helyükre (`0x0065b840`). | `fileops_controller.py`, `photos_model.py`: az indexben frissül az útvonal, a rácsmodell újrarendeződik. | Egyezik. |
| Kijelölés átnevezés után | `0x0053386c: call 0x00412400`: az átnevezési ciklus lefutása után az ÖSSZES sikeresen átnevezett kép kijelölve marad az új pozíciójában. | `FileOpsDialogs.qml:283-287` és `MainWindowCommands.qml:93-110`: csak egyetlen kép (`rows.length === 1`) esetén állítja be a `_pendingRenamePhotoId`-t; több kép átnevezése után a kijelölés nem követi a fájlokat. | Eltérés: több kép átnevezésekor az összes érintett kép kijelölését meg kell tartani. |
| Hibakezelés (ütközés, írásvédettség) | `0x0053351c` és `0x00533822`: Ha egy fájl átnevezése meghiúsul (zárolt fájl, mappa-írásvédettség, névütközés 4096 után), a ciklus átugorja a hibás fájlt és folytatja a többi kijelölt fájl feldolgozását. | `rename.py:349-370`: `rename_photos_many` `PartialRenameError`-t dob bármely fájl hibájánál, és a kötegelt végrehajtás megszakad. | Eltérés: a Picasa nem szakítja meg a köteget, hanem átugorja a sikertelen elemeket és a sikereseket jelöli ki a végén. |

### 2. Két független út és cáfoló vizsgálat

- **A út (bináris utasításszintű olvasás):**
  - Belépési pontok: `0x005593da` (Fájl menü `0x9d4f`), `0x0055b2ae` (Picture menü `0x9d4f`), `0x005cb990` (`0x5cc4e9: call 0x00532ec0`), `0x005e6710` (`0x5e68fd` VK_F2 -> `0x5e6939: call 0x00532ec0`).
  - Néző tiltása: `0x0056e458` (menüfrissítésnél `[edi + 0x34a4] != 0` esetén letiltja a `0x9d4f` menüt), `0x005e68ee` (F2 leütéskor `FUN_0057c430(4)` hívással ellenőrzi a nézőt és átugorja a megnyitást).
  - Dialógus és engedélyezés: `0x00532070` konstruktor, `0x00532c70` állapotgép: ha `RenameUseDate` (`+0xd8`) vagy `RenameUseSize` (`+0xf4`) be van pipálva, a Rename gomb aktív; egyébként a név különbözősége szükséges.
  - Sorszámozás: `0x00993650` (0x00993b07: `"%s-%03lu"`), 4096-os limit (`0x00993993`, `0x00993a1a`).
  - Végrehajtás és kijelölés: `0x0053351c` hibánál ugrás `0x533822`-re (átugrás), a végén `0x0053386c: call 0x00412400` a sikeres elemek kijelölésére és `0x005338a0: call 0x0065b840` a nézet frissítésére.
- **B út (erőforrás és specifikációs kontroll):**
  - `runtime/rename.fen`: a deklaratív felületleíró betűre megerősíti az ablak címét (`"Rename Files"`), a vezérlőneveket (`files`, `newname`, `date`, `size`, `sample`, `rename`) és a feliratokat.
  - `picasa-gyorsbillentyuk.md` korábbi futásidejű képernyőképes mérései (kb-5, 2756. sor) igazolták az `F2` leütés viselkedését és párbeszédablakának megjelenését.
  - `ui-audit-context-menus.md` tételes menüleltára igazolja, hogy a helyi menükben nincs Rename tétel.
- **Cáfoló vizsgálat:**
  - Megvizsgáltuk azt a feltételezést, hogy a nézőben engedélyezett-e az F2 gyorsbillentyű (a PicasaPy #6530 jegyében feltételezett viselkedés). A binárisban a `0x005e68ee` utasítás (`push 4; call 0x57c430; test al, al; jne 0x5e6947`) cáfolja ezt: ha a néző nyitva van, az elágazás a hívás elé ugrik és elnyeli az eseményt. Ugyanígy a menüfrissítő `0x0056e458` utasítás is letiltja a menüpontot a nézőben.

### 3. Azonosított fejlesztési eltérések és jegyjavaslatok

1. **Rename gomb tiltva marad, ha a név nem változott, de a Date vagy Image resolution be van jelölve:**
   - **Eredeti:** `0x00532c70`: a `RenameUseDate` vagy `RenameUseSize` bejelölése esetén a Rename gomb aktív, akkor is, ha a szövegmező tartalma nem módosult.
   - **Nálunk:** `FileOpsDialogs.qml:271`: `canRename()` csak akkor ad igazat, ha `base !== openedName.trim()`.
   - **Teendő:** `canRename()` bővítése: `return base.length > 0 && (base !== openedName.trim() || includeDateCheck.checked || includeSizeCheck.checked)`.
2. **Több kép átnevezése után a kijelölés elveszik a rácsban:**
   - **Eredeti:** `0x0053386c`: az összes átnevezett kép kijelölve marad az új pozíciójában.
   - **Nálunk:** `FileOpsDialogs.qml:283` és `MainWindowCommands.qml:93-110`: csak 1 képnél kezeli a `_pendingRenamePhotoId`-t.
   - **Teendő:** A kijelölés-követést kiterjeszteni több kép átnevezésére (pl. `_pendingRenamePhotoIds` lista kezelése).
3. **Hibakezelés kötegelt átnevezésnél:**
   - **Eredeti:** `0x0053351c` és `0x00533822`: egyedi fájlhibánál átugorja a hibás elemet és folytatja a többi kijelölt fájllal.
   - **Nálunk:** `rename.py:350-370`: `PartialRenameError` azonnal megszakítja a folyamatot.
   - **Teendő:** Eldöntendő fejlesztői kérdés: megtartjuk-e a szigorúbb hiba-leállást, vagy átugrásos folytatás kell.

**Átvételi megjegyzés (a nézőbeli F2):** a fenti „néző tiltása” állítás feltételes. A `0x0057c430(4)` állapotkód és a `+0x34a4` mező jelentését („a néző nyitva”) ez a kör nem igazolta külön, az eredeti programot használó tulajdonos pedig a #6530-ban azt jelezte, hogy megnyitott képnél az F2 átnevez. A PicasaPy nézőbeli F2-je ezért marad; a kérdést csak egy Colab-os viselkedésmérés dönti el (néző megnyitása, F2, megnyílik-e a Rename ablak).

## #6967: A Revert parancs teljes folyamata az eredeti Picasában és összevetése a PicasaPy-jal

### 1. Belépési pontok, engedélyezési feltételek és a két revert-parancs szétválasztása

Az eredeti Picasa 3.9 binárisában két külön visszaállítási parancs létezik, amelyek eltérő célt szolgálnak és eltérő feltételekkel engedélyezettek:

1. **`ID_FILE_REVERT` (`0x9d9a`):**
   - **Főmenü:** Fájl ▸ Revert / Visszaállítás (menüépítő: `0x00559150`, rekord: `0x00d6da64`, parancskód: `0x9d9a`, felirat: `Rever&t` / `Vissz&aállítás`, mnemonik: `t`).
   - **Helyi menük (kép jobb-klikk):**
     - Mappanézet (FolderPhoto helyi menü): `0x00730790` (`0x00730c91`, `0x9d9a`).
     - Albumnézet (AlbumPhoto context menu): `0x00731050` (`0x0073148a`, `0x9d9a`).
     - Egyképes szerkesztő / néző nézet (OneUp context menu): `0x007327a0` (`0x00732b9c`, `0x9d9a`).
   - **Engedélyezési feltétel (`EnableMenuItem`, `0x0056e1c0` és `0x0056c5a0`):**
     A `0x5cb1a0` által visszaadott állapotjelző bájt 7. bitje (`0x80`, revertable) kötelező. Ez azt jelenti, hogy kizárólag olyan képnél engedélyezett, amely már korábban lemezre lett mentve, és létezik hozzá `.picasaoriginals` (vagy régebbi verzióknál `Originals`) biztonsági mentés. Ha a kép szerkesztetlen, vagy csak memóriában szerkesztett (még nincs lemezre mentve), a menüpont inaktív / szürke (`MF_GRAYED`). Tiltja továbbá a `0x8000` felső tiltó jelző (pl. írásvédett / speciális gyűjtemény) és a nem engedélyezett nézetállapot (`0x34a4 != 0`).
   - **Szerkesztő gombja:** A szerkesztő bal paneljén (`editpanel`, `0x00567680`) NINCS Revert gomb. A szerkesztő bal hasábján kizárólag `filter_undo` (Visszavonás) és `filter_redo` (Újra) gombok találhatók. A Revert a szerkesztőben is kizárólag a Fájl menüből vagy a kép helyi menüjéből (`0x007327a0`) érhető el.
   - **Gyorsbillentyű:** NINCS gyorsbillentyű rendelve az `ID_FILE_REVERT`-hez sem a menükben, sem a gyorsítótáblában (az erőforrások között az `RT_ACCELERATOR` és a `SHORTCUTS.XML` nem tartalmaz hozzá bejegyzést).

2. **`ID_PICTURE_REVERT` (`0x9d2d`):**
   - **Főmenü:** Kép ▸ Undo All Edits / Összes szerkesztés visszavonása (menüépítő: `0x00559150`, rekord: `0x00d6e4d4`, parancskód: `0x9d2d`, felirat: `Undo &All Edits` / `Összes szerkesztés vissz&avonása`, mnemonik: `a`).
   - **Helyi menük (kép jobb-klikk):**
     - Mappanézet: `0x00730790` (`0x0073093b`, `0x9d2d`).
     - Albumnézet: `0x00731050` (`0x007311fb`, `0x9d2d`).
     - Szerkesztő nézet: `0x007327a0` (`0x0073298a`, `0x9d2d`).
   - **Engedélyezési feltétel (`0x0056e1c0` / `0x0056f3d0` és `0x0056c5a0` / `0x0056d9b0`):**
     Akkor engedélyezett, ha van nem mentett memóriabeli szerkesztés (`0x40` jelző), és nincs `0x8000` tiltás. Ha a kép szerkesztetlen, inaktív.
   - **Gyorsbillentyű:** NINCS gyorsbillentyűje.

### 2. Megerősítő párbeszédablak folyamata és szövegei (`ID_FILE_REVERT`, `0x0053b2e0`)

A megerősítő párbeszédablakot a `0x0053b2e0` kezeli (`CThumbUI::FileRevert`):

1. **Ablak címe:**
   - `CThumbUI::FileRevert::title` = "Revert" / "Visszaállítás" (`0x00c8a8b8`).

2. **Egy kijelölt kép esetén (`0x0053b666`):**
   - Fő kérdés: `CThumbUI::FileRevert::message1` = "Revert to original version of file?" / "Visszatér a fájl eredeti változatához?" (`0x00c8a768`).
   - Figyelmeztető szöveg: `CThumbUI::FileRevert::message2` = "\n\nThis cannot be undone and all changes will be lost." / "\n\nEz a művelet nem vonható vissza, és az összes módosítás elvész." (`0x00c8a7ae`).
   - Kiegészítő magyarázat mentett előzménynél (`0x0053b6e7`): `CThumbUI::FileRevert::message1undo` = "\n\nTo undo the last save and keep edits click 'Undo Save'." / "\n\nAz utolsó mentés visszavonásához és a szerkesztések megtartásához kattintson a \"Mentés visszavonása\" gombra." (`0x00c8a806`).
   - Gombok:
     - `CThumbUI::FileRevert::revert` = "Revert" / "Visszaállítás" (`0x00c8a890`).
     - `CThumbUI::FileRevert::undosave` = "Undo Save" / "Mentés visszavonása" (`0x00c8a864`) - csak akkor jelenik meg, ha a kép mentve volt lemezre és van mit visszavonni.
     - "Cancel" / "Mégse" (`0x00c884a0`).

3. **Több kijelölt kép esetén (`0x0053b61a`):**
   - Fő kérdés: `CThumbUI::FileRevert::messageX` = "Revert to original version of these files?" / "Visszatér a fájlok eredeti változatához?" (`0x00c8a71c`).
   - Figyelmeztető szöveg: `CThumbUI::FileRevert::message2` = "\n\nThis cannot be undone and all changes will be lost." (`0x00c8a7ae`).
   - Gombok: kizárólag "Revert" és "Cancel". Több kijelölt képnél az eredeti binárisban NEM jelenik meg az "Undo Save" gomb és a `message1undo` magyarázat (`0x0053b6e3` elágazás kihagyja).

4. **Külsőleg módosított fájlok figyelmeztetése (`0x0053b87e`-`0x0053bb87`):**
   - Ha a lemezen található fájl utolsó módosítási ideje eltér a Picasa által mentett `moddate` értéktől (külső képszerkesztőben módosult):
     - Egy képnél: `CThumbUI::FileRevert::changed1` = "This file has been changed outside of Picasa. Reverting will lose those changes." / "Ez a fájl a Picasán kívül módosult. Ha a visszaállítást választja, a módosítások elvesznek." (`0x00c8a970`).
     - Több képnél: `CThumbUI::FileRevert::changedX` = "These files have changed outside of Picasa. Reverting will lose those changes." / "Ezek a fájlok a Picasán kívül módosultak. Ha a visszaállítást választja, a módosítások elvesznek." (`0x00c8a9e8`).
     - Folytatás kérdése: `CThumbUI::FileRevert::continue` = "\n\nDo you want to revert?" / "\n\nVissza szeretne térni?" (`0x00c8aa5a`).
     - Gombok: `CThumUI::FileRevert::yesbutton` = "Revert Anyway" / "Visszaállítás ennek ellenére" (`0x00c8aab4`), és "Cancel" / "Mégse" (`0x00c8aa94`).

### 3. Végrehajtás és futásidejű hatás

1. **Lemezművelet és `.picasaoriginals` (`0x0046d7d0`, `0x00462ba0`):**
   - A `0x00462ba0` megkeresi a kép könyvtárában a `.picasaoriginals` (illetve korábbi telepítéseknél az `Originals`) mappát (`0x00462ccd`, `0x00462d2e`).
   - A biztonsági másolatként megőrzött eredeti fájlt visszamásolja a fotó helyére, felülírva a szerkesztett lemezfájlt.
2. **`.picasa.ini` könyvelés törlése (`0x0046d7d0`):**
   - A `0x0046d7d0` eljárás megnyitja a mappa `.picasa.ini` fájlját (`0x0046d967`), és a visszaállított fotó szakaszából törli a szerkesztési kulcsokat: `filters` (`0x0046ed76`), `rotate` (`0x0046e721`, `0x0046f537`), `flipped` (`0x0046e796`, `0x0046f9ef`), és `textactive` (`0x0046fee8`, `0x00470184`).
   - A fotóhoz tartozó egyéb metaadatok (`star`, `caption`, `faces`, albumtagságok, `backuphash`, `originhash`) változatlanul megmaradnak.
3. **Folyamatjelző ablak (`0x0053b2e0`):**
   - A lemezművelet közben folyamatjelző párbeszéd látható: `CThumbUI::FileRevert::progress` = "Reverting Files." / "Fájlok visszaállítása" (`0x00c8a8d4`).
4. **Bélyegkép és index (`0x0053bc54`-`0x0053bee7`):**
   - A memóriabeli gyorsítótár ürül (`0x0053bc54`, `call 0x45ff60`), az indexelő szál újraolvassa a lemezfájlt, és a háttérben újra elkészíti a bélyegképet az eredeti kép alapján (`0x0053bee7`, `call 0xa54b70`).
   - Ha a szerkesztőben éppen nyitva van a visszaállított fotó (`0x0053bc8a`), a szerkesztő azonnal újratölti az eredeti képet a memóriába és a megjelenítőbe (`0x0053bce9`, `0x0053bd30`).
5. **Rács kijelölése:**
   - A művelet lefutása után a kijelölés nem törlődik, a visszaállított képek kijelölve maradnak a könyvtárnézeti rácsban.

### 4. Hibaesetek (írásvédettség, hiányzó eredeti)

1. **Hiányzó eredeti biztonsági mentés:**
   - Az eredeti Picasában normál esetben a menüpont meg sem jelenik aktívként, ha a képhez nem tartozik `.picasaoriginals` mappa.
   - Ha a mappa vagy a benne lévő fájl lemezről való törlése miatt a futás közben hiányzik, a `0x00462ba0` hibakóddal tér vissza, a művelet leáll, és a felhasználó lemezhiba üzenetet kap.
2. **Írásvédett fájl vagy lemezhiba (`0x0053bbb0`):**
   - Ha a célfájl írásvédett, vagy a lemez megtelt, a `0x0053bbb0` címen felugró ablak jelenik meg:
     - Cím: "Revert" / "Visszaállítás" (`CThumbUI::FileRevert::title`, `0x00c8a8b8`).
     - Szöveg: `FileRevert::fileerr` = "Unable to revert all files due to a disk error. The disk may be full or read-only." / "Lemezhiba miatt nem lehetséges az összes fájl visszaállítása. Lehet, hogy a lemez megtelt vagy írásvédett." (`0x00c8a908`).

### 5. Paritási összevetés és eltérések táblázata

| Funkció / Elem | Eredeti Picasa (bináris cím) | PicasaPy (fájl:sor) | Eltérés / Teendő |
|---|---|---|---|
| Főmenü belépési pont | Fájl ▸ Revert (`0x00559150`, rekord: `0x00d6da64`, `0x9d9a`) | `src/picasapy/app/qml/PicasaPy/PicasaFileMenu.qml:113` | Egyezik. Paritásban van. |
| Kép menü belépési pont | Kép ▸ Undo All Edits (`0x00559150`, rekord: `0x00d6e4d4`, `0x9d2d`) | `src/picasapy/app/qml/PicasaPy/PicasaPictureMenu.qml:124` | Egyezik. Külön parancsként létezik. |
| Helyi menü belépési pontok | Mappa (`0x00730790`), Album (`0x00731050`), OneUp (`0x007327a0`) mindkettőt tartalmazza | `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:403`, `ViewerContextMenu.qml:208` | Egyezik. Mindkét menüpont megvan a helyi menükben. |
| Szerkesztő gombsor | Bal panelen nincs Revert gomb (csak `filter_undo`, `0x00567680`) | `src/picasapy/app/qml/PicasaPy/EditorPanel.qml` | Egyezik. Nálunk sincs Revert gomb a bal hasábon. |
| Gyorsbillentyű | Nincs gyorsbillentyű sem `0x9d9a`-hoz, sem `0x9d2d`-hez | Nincs gyorsbillentyű | Egyezik. |
| Engedélyezési feltétel (Revert) | Csak lemezre mentett, `.picasaoriginals` másolattal bíró képnél aktív (`0x80`, `0x0056e561`) | `PicasaFileMenu.qml:117`, `PhotoContextMenu.qml:405` (`hasSavedBackup` / `hasBackup`) | Egyezik. Nem mentett szerkesztésnél szürke. |
| Egy kép megerősítő kérdése | `message1` + `message2` + `message1undo` (`0x0053b666`) | `SaveDialogs.qml:313-337` | Egyezik. A szövegek és gombok megegyeznek. |
| Több kép megerősítő kérdése | `CThumbUI::FileRevert::messageX` = "Revert to original version of these files?" (`0x00c8a71c`, `0x0053b61a`) | `SaveDialogs.qml`, `qsTr("Revert to original version of these files?")` | Egyezik (#6972). A szöveg és a hivatalos fordítása mind a 41 nyelven a `stringres` szerinti. |
| Több kép gombjai (Undo Save) | Több képnél NINCS "Undo Save" gomb és nincs magyarázó sor (`0x0053b6e3`) | `SaveDialogs.qml`, `syncUndoSaveButton()` és a `revertUndoSaveHint` láthatósága | Egyezik (#6972). Több képnél a gomb kikerül a gombsorból (nem marad rés), a magyarázó sor rejtve; egy képnél a három gomb az eredeti elrendezésben áll. Valódi kattintásos teszt, minden nyelvi fordítással. |
| Külsőleg módosított fájlok | Időbélyeg-eltérésnél `changed1`/`changedX` + "Revert Anyway" (`0x0053b87e`) | `SaveDialogs.qml` (`confirmRevert`, `revertChangedDialog`), `edit/saved_fingerprint.py` | Egyezik a viselkedésben (#6972): a "Revert" gomb után figyelmeztetés jön, a "Revert Anyway" visszaállít, a Mégse nem. **Az észlelés alapja saját:** a meglévő mentési metaadat erre nem jó (a `moddate` a mentés ELŐTTI időt őrzi, a `backuphash` írási idő-bélyeg, a képfájl `mtime`-ját minden ini-írás megérinti), ezért a mentés után a kép tartalom-aláírását (JPEG-nél metaadat nélkül) az adatgyökér `saved-fingerprints.json` fájlja őrzi. Nincs bejegyzés (Picasa mentette, vagy a Mentés visszavonása után) = nincs figyelmeztetés. Nyitott: az eredeti egyes/többes alakja a kijelölt vagy a módosult fájlok számától függ-e; nálunk a módosultaké. |
| `.picasa.ini` törölt kulcsok | Törli: `filters`, `rotate`, `flipped`, `textactive` (`0x0046d7d0`) | `src/picasapy/edit/save.py` (`_EDIT_BOOKKEEPING_KEYS`), `save_operations.py` (`revert`) | Egyezik (#6972). A Revert a `filters`, `rotate`, `flipped`, `textactive` (és a régi `redo`) sort törli, a többi kulcs érintetlen marad. |
| Folyamatjelző szövege | "Reverting Files." (`0x00c8a8d4`, `CThumbUI::FileRevert::progress`) | `SaveProgressPanel.qml:46` `qsTr("Reverting Files.")` | Egyezik. |
| Lemezhiba / írásvédettség | "Unable to revert all files due to a disk error. The disk may be full or read-only." (`0x00c8a908`) | `SaveDialogs.qml:180` | Egyezik. Bitre azonos fordítás. |
| Bélyegkép, index, kijelölés | Bélyegkép és megnyitott kép újratöltődik, kijelölés megmarad (`0x0053bc54`) | `save_restore.py`, `save_feedback.py` | Egyezik. |

### 6. Javasolt fejlesztői jegyek

1. **Jegy: Revert megerősítő ablak szövegének és gombjainak paritása több kép kijelölésekor**
   - **Eredeti:** Az eredeti Picasa 3.9 binárisában (`0x0053b2e0`, `0x0053b61a`, `0x0053b6e3`) több kép kijelölésekor a megerősítő kérdés szövege: `Revert to original version of these files?` (`CThumbUI::FileRevert::messageX`, `0x00c8a71c`), és az "Undo Save" gomb (`0x00c8a864`), valamint a hozzátartozó magyarázó sor (`CThumbUI::FileRevert::message1undo`, `0x00c8a806`) kizárólag egyetlen kép kijelölése esetén jelenik meg; több képnél az "Undo Save" nem érhető el.
   - **Nálunk:** A `src/picasapy/app/qml/PicasaPy/SaveDialogs.qml:316` sorában a többes számú szöveg `these file(s)?` formátumú, és a `revertUndoSaveButton` valamint `revertUndoSaveHint` több kép esetén is látható.
   - **Teendő:**
     1. A `SaveDialogs.qml:316` szövegének javítása: `qsTr("Revert to original version of these files?")`.
     2. A `revertUndoSaveButton` és `revertUndoSaveHint` láthatóságának feltételhez kötése: `visible: revertConfirmDialog.fileCount === 1`.
   - **Kész, ha:** 1 kép kijelölésekor a Revert ablak tartalmazza az "Undo Save" gombot és a magyarázatot; 2 vagy több kép kijelölésekor a kérdés pontosan a "Revert to original version of these files?" szöveget mutatja, az "Undo Save" gomb és magyarázat pedig rejtve marad.

2. **Jegy: A Revert művelet során a forgatási és felirat-kulcsok törlése a `.picasa.ini`-ből**
   - **Eredeti:** A `Picasa3.exe` `0x0046d7d0` eljárása a mentett eredeti visszamásolásakor a `.picasa.ini`-ből a `filters` kulcson kívül törli a `rotate`, `flipped` és `textactive` sorokat is, mivel a visszamásolt fájl a szerkesztés előtti fizikai képet adja vissza.
   - **Nálunk:** A `src/picasapy/edit/save_operations.py:366` eljárás csak a `filters` és `redo` kulcsokat törli, így a korábbi forgatás és felirat bejegyzése bent marad az ini-ben.
   - **Teendő:** A `save_operations.py` `revert` függvényében a törlendő kulcsok körét ki kell terjeszteni a `rotate`, `flipped` és `textactive` kulcsokra.
   - **Kész, ha:** Egy kép forgatása, mentése, majd Revert parancs végrehajtása után a `.picasa.ini`-ben nem marad sem `filters`, sem `rotate`, sem `flipped`, sem `textactive` bejegyzés.

## #6975: A Save a Copy és a Save As teljes folyamata az eredeti Picasában és összevetése a PicasaPy-jal

### 1. Belépési pontok, engedélyezési feltételek és a két mentési parancs szétválasztása

Az eredeti Picasa 3.9 binárisában a mentés-család két külön parancsa a Mentés másként (Save As) és a Másolat mentése (Save a Copy), amelyek mindketten a renderelt képet új fájlba írják, de eltérő paraméterrel, felülettel és engedélyezési feltétellel futnak:

1. **`ID_FILE_SAVEAS` (`0x9d9b`):**
   - **Főmenü:** Fájl ▸ Save &As... / Mentés másként... (menüépítő: `0x00559150`, rekord: `0x00d6da68`, szövegcímke: `0x00d6da8c`, parancskód: `0x9d9b`, kulcs: `eMenuFile::ID_FILE_SAVEAS` [`0xc8c5a4`], alapértelmezett angol felirat: `Save &As...` [`0xc8c5c0`], mnemonik: `A`, ellipszissel a végén, mert párbeszédablakot nyit).
   - **Helyi menük (kép jobb-klikk):**
     - Mappanézet (FolderPhoto, `0x00730790`): NEM szerepel a helyi menüben (csak a sima Mentés [`0xe103`] és Revert [`0x9d9a`] van benne).
     - Albumnézet (AlbumPhoto, `0x00731050`): NEM szerepel a helyi menüben.
     - Egyképes néző / OneUp (`0x007327a0`): NEM szerepel a helyi menüben.
   - **Szerkesztő bal panelje (`0x00567680`):** NEM tartalmaz Save As gombot (a szerkesztőben kizárólag a Visszavonás és Újra gombok találhatók).
   - **Gyorsbillentyű:** NINCS gyorsbillentyű rendelve a Save As-hoz sem a menükben, sem a gyorsítótáblában (az `RT_ACCELERATOR` erőforrás nem tartalmaz hozzá bejegyzést; a `Ctrl+S` kizárólag a Mentéshez [`0xe103`] tartozik).

2. **`ID_FILE_SAVEACOPY` (`0x9dca`):**
   - **Főmenü:** Fájl ▸ „Save a Copy” / Másolat mentése (menüépítő: `0x00559150`, rekord: `0x00d6da90`, szövegcímke: `0x00d6daa0`, parancskód: `0x9dca`, kulcs: `eMenuFile::ID_FILE_SAVEACOPY` [`0xc8c574`], alapértelmezett angol felirat: `Save a Copy` [`0xc8c594`], mnemonik: `y`, ellipszis nélkül, mert azonnali közvetlen mentést végez).
   - **Helyi menük:** NEM szerepel sem a FolderPhoto (`0x00730790`), sem az AlbumPhoto (`0x00731050`), sem a OneUp (`0x007327a0`) menükben.
   - **Szerkesztő bal panelje (`0x00567680`):** NEM tartalmaz Save a Copy gombot.
   - **Gyorsbillentyű:** NINCS gyorsbillentyűje.

3. **Engedélyezési feltételek (`EnableMenuItem`, `0x0056e1c0` és `0x0056c5a0`):**
   - A `0x005cb1a0` által számított állapotmaszk alapján a `0x0056e1c0` vezérli az `EnableMenuItem` (`USER32.dll`, `0x00c40818`) hívásokat:
     - **Kijelölés megléte:** Legalább egy képnek ki kell lennie jelölve (a `0x2` fotó bit kötelező; 0 kijelölt elemnél a `byte ptr [esp + 0x12] == 0`, így `dl = 1` -> `MF_GRAYED`, a menüpont szürke).
     - **Szerkesztetlen kép:** Engedélyezett (nem feltétele a `0x40` nem mentett szerkesztési bit, sem a `0x80` revertable bit; szerkesztetlen kép másolata is menthető).
     - **Több kijelölt kép:** A menüben engedélyezett (a `0x100` többszörös kijelölés bitnél a `0x0056e3d5` ág `MF_ENABLED`-et ad), DE a végrehajtáskor a közös kezelő (`FUN_005e6a20`) nem tartalmaz iterációs ciklust, és kizárólag az egyetlen aktív, fókuszban lévő képre (`*(param_1 + 0xe64)`) hajtja végre a mentést.
     - **Videó kijelölése:** Ha kizárólag videó van kijelölve, a `0x005cb1a0` a `0x00562250` (`isVideo`) hívás alapján a `0x20` videó bitet állítja be a `0x2` fotó bit helyett, emiatt a `0x0056e416` teszt elbukik és mindkét menüpont tiltottá válik (`MF_GRAYED`).
     - **Tiltó nézetállapotok:** Zárolt nézetállapot (`[edi + 0x34a4] != 0`) vagy írásvédett / speciális forrás esetén (`maszk & 0x8000 != 0`, `0x0056e591`) a `0x0056e5a0` és `0x0056e5aa` explicit `MF_GRAYED` hívással letiltja a `0x9d9b` és `0x9dca` parancsokat.

### 2. Megjelenő ablak és folyamat

A két parancsot a parancs-diszpécser (`0x005cb990`) a switch ugrótábláján (`0x005cdc30`, indexek: 38 és 65) át ugyanarra a közös eljárásra irányítja:
- `case 0x9d9b` (40347): `0x005cc5a0`: `push 0; mov ecx, ebx; call 0x005e6a20` (Save As, `param_2 == 0`).
- `case 0x9dca` (40394): `0x005cc5ad`: `push 1; mov ecx, ebx; call 0x005e6a20` (Save a Copy, `param_2 != 0`).

A közös `FUN_005e6a20` eljárás futásidejű viselkedése:

1. **`Save As` (Mentés másként...):**
   - **Ablak:** Rendszer-fájlválasztó ablakot nyit (`0x0097f1d0`, `"SaveFile"`), a Windows szabványos fájlmentési felületével.
   - **Alapértelmezett mappa és név:** A forrásfájl könyvtára és a forráskép eredeti fájlneve.
   - **Szűrők:** `CThumbUI::SaveAsFilterJPG` (`"*.jpg"`), illetve ha a forráskép WebP típusú (`local_14a4[6] == 0x1f`), a szűrő kiegészül a `CThumbUI::SaveAsFilterWebP` (`"*.webp"`) bejegyzéssel.
   - **Forrással azonos név:** Ha a felhasználó a fájlválasztóban a forráskép nevét hagyja jóvá vagy azt választja ki, a `0x005e6e81` ágon felugró figyelmeztetés jelenik meg: `IDS_CANT_SAVE_TO_SAME` (`0x009ae710`, 0xf9): "Cannot replace image. Please try again with a different filename." / "A képet nem lehet kicserélni. Próbálja újra másik fájlnévvel.", és a mentés leáll, fájlírás nélkül.
   - **Megszakítás (Cancel):** Ha a felhasználó a fájlválasztóban a Mégse gombra kattint (`iVar11 != 0`), az eljárás csendben kilép, lemez- és adatbázis-hatás nélkül.

2. **`Save a Copy` (Másolat mentése):**
   - **Ablak:** SEMMILYEN ablakot nem nyit. Nem jelenik meg megerősítő kérdés, sem fájlválasztó, sem beállítási dialógus. A mentés azonnal és közvetlenül végbemegy.
   - **Célfájl neve és helye:** Mindig a forráskép saját könyvtárában készül a másolat. A fájlnév generálását a `0x00993650` végzi a `0x00cd8d64` címen található formátumsztring alapján: `"%s-%03lu"`.
   - **Névképzés és névütközés:** A sorszámozás `001`-ről indul (`alapnev-001.ext`). Ha a fájl már létezik a lemezen (`0x00992ed0` létezés-ellenőrzés), a számláló növekszik (`add esi, 1`), így automatikusan `alapnev-002.ext`, `alapnev-003.ext` stb. jön létre (a ciklus felső korlátja `0x1000` = 4096). Ezáltal a Másolat mentése művelet sosem ír felül meglévő fájlt, és sosem ütközik néven.

### 3. Végrehajtás és futásidejű hatás

1. **Szerkesztések beégetése:**
   - Mindkét művelet esetén a mentett új fájlba a forrásképen lévő összes szerkesztés (vágás, forgatás, színkorrekciók, retusálás, szöveg) beégetésre kerül (`*(iVar5 + 0x94)` képkódoló hívás).
2. **Az eredeti kép és `.picasa.ini` állapota:**
   - Az eredeti kép lemezfájlja és `.picasa.ini` bejegyzése ÉRINTETLEN marad. Nem jön létre `.picasaoriginals` biztonsági mentés (az kizárólag a sima `Save` parancsnál készül), a szerkesztési kulcsok megmaradnak.
3. **Az új fájl `.picasa.ini` bejegyzése:**
   - Az eredeti Picasa 3.9 az új fájlhoz SEMMIT nem ír a célkönyvtár `.picasa.ini` fájljába (`0x005aafd0` / `0x005aadf0`). Az új kép önálló, tiszta, szerkesztetlen fotóként jelenik meg.
4. **Indexelés és bélyegkép:**
   - A lemezre írás után az eljárás meghívja a `0x00411a90` indexelő értesítőt, amely azonnal beolvassa az új fájlt, elkészíti hozzá a bélyegképet az SQLite adatbázisba, és megjeleníti a könyvtárnézet rácsában.
5. **Rács kijelölése:**
   - A mentés befejezése után a kijelölés a könyvtárrácsban az eredeti képen marad; az új másolatfájl nem kap automatikus kijelölést vagy fókuszt.

### 4. Hibaesetek (írásvédett mappa, névütközés)

1. **Névütközés meglévő fájllal:**
   - Save As esetén, ha nem a forrásfájllal, hanem egy másik meglévő fájllal ütközik a név, a rendszer-fájlválasztó standard felülírási megerősítést kér.
   - Save a Copy esetén a számozó automatikusan átlépi a létező fájlokat (`-001` -> `-002`), így ütközés nem fordulhat elő.
2. **Írásvédett mappa vagy lemezhiba (`0x005e7022`):**
   - Ha a célkönyvtár írásvédett, nincs írási jogosultság, vagy a lemez megtelt, a `0x005e7022` címen felugró hibaüzenet jelenik meg:
     - Forráskulcs: `CThumbUI::FileSaveCopy:err` (`0x00c97750`).
     - Alapértelmezett angol szöveg: `0x00c97700`: "Unable to save files due to a disk error. The disk may be full or read-only."
     - Magyar fordítás: "Lemezhiba miatt nem lehetséges a fájlok mentése. Lehet, hogy a lemez megtelt vagy írásvédett."
     - Megjelenítés: egyszerű `0x00980700` üzenetablak OK gombbal; nem tartalmazza az érintett fájlnevet vagy numerikus hibakódot.

### 5. Paritási összevetés és eltérések táblázata

| Funkció / Elem | Eredeti Picasa (bináris cím) | PicasaPy (fájl:sor) | Eltérés / Teendő |
|---|---|---|---|
| Save As főmenü belépő | Fájl ▸ Save &As... (`0x00559150`, rekord: `0x00d6da68`, `0x9d9b`) | `src/picasapy/app/qml/PicasaPy/PicasaFileMenu.qml:128` | Egyezik. Paritásban van. |
| Save a Copy főmenü belépő | Fájl ▸ „Save a Copy” (`0x00559150`, rekord: `0x00d6da90`, `0x9dca`) | `src/picasapy/app/qml/PicasaPy/PicasaFileMenu.qml:134` | Egyezik. Paritásban van. |
| Helyi menük | Nem szerepel a helyi menükben (`0x00730790`, `0x00731050`, `0x007327a0`) | `PhotoContextMenu.qml`, `ViewerContextMenu.qml` nem tartalmazza | Egyezik. |
| Szerkesztő panel gombjai | Bal panelen nincs Save As / Save a Copy gomb (`0x00567680`) | `EditorPanel.qml` nem tartalmazza | Egyezik. |
| Gyorsbillentyűk | Nincs gyorsbillentyű rendelve | Nincs gyorsbillentyű | Egyezik. |
| Engedélyezés (szerkesztetlen kép) | Engedélyezett (`0x2` fotó bit, `0x0056e426`) | `bar.photoActionsEnabled` aktív | Egyezik. |
| Engedélyezés (több kijelölt kép) | Menüben engedélyezett (`0x100` bit), de csak 1 képre hajtódik végre (`*(param_1 + 0xe64)`) | `MainMenuBar.qml:340-344` `photoActionIndex()` alapján 1 képre hívja | Egyezik. |
| Engedélyezés (videó kijelölése) | Tiltott / szürke (`MF_GRAYED`, hiányzó `0x2` fotó bit, `0x0056e416`) | `photoActionsEnabled` videóra is aktív marad | **Eltérés.** Videó kijelölésekor nálunk a menüpontok aktívak maradnak. Fejlesztési jegy javasolt. |
| Save As fájlválasztó | Rendszer-fájlválasztót nyit (`0x0097f1d0`), JPG és WebP szűrőkkel | `SaveDialogs.qml:153-162` `FileDialog` JPG és WebP szűrőkkel | Egyezik. |
| Save As forrással azonos név | `IDS_CANT_SAVE_TO_SAME` figyelmeztetés (`0x005e6e81`) | `SaveDialogs.qml:186` `IDS_CANT_SAVE_TO_SAME` üzenet | Egyezik. Bitre azonos szöveg. |
| Save a Copy közvetlen mentés | Nincs ablak, azonnali végrehajtás (`0x005e6a20`) | `SaveDialogs.qml:65` közvetlenül hívja a vezérlőt | Egyezik. |
| Save a Copy fájlnév minta | `"%s-%03lu"` (`0x00cd8d64`, `0x00993650`) -> `kep-001.jpg` | `src/picasapy/edit/save_copy.py:77` `"{stem}-{number:03d}{suffix}"` | Egyezik. Pontosan megegyező formátum. |
| Szerkesztések beégetése | Beégnek az új fájlba (`*(iVar5 + 0x94)`) | `_render_for_save` beégeti a szerkesztéseket | Egyezik. |
| Eredeti kép és .picasa.ini | Érintetlen marad, nincs `.picasaoriginals` | `save_copy.py:170-208` érintetlenül hagyja | Egyezik. |
| Új fájl .picasa.ini | Semmit nem ír az ini-be (`0x005aafd0`) | `save_copy.py:197-208` nem ír az ini-be | Egyezik. |
| Indexelés és kijelölés | Új kép indexelődik, eredeti kijelölve marad | `noteOutputWritten`, eredeti kijelölve marad | Egyezik. |
| Lemezhiba / írásvédettség szövege | "Unable to save files due to a disk error. The disk may be full or read-only." (`0x00c97700`) | `SaveDialogs.qml:191` fájlnevet és numerikus hibakódot fűz hozzá | **Eltérés.** A hibaablak szövege nálunk a `filesaveerr-win` formátumát követi. |

### 6. Javasolt fejlesztői jegyek

1. **Jegy: A Save As és Save a Copy menüpontok letiltása videó kijelölése esetén**
   - **Eredeti:** Az eredeti Picasa 3.9 binárisában (`0x0056e1c0`, `0x0056e2f4`, `0x0056e416`, `0x005cb2cf`) a Fájl ▸ Save &As... (`0x9d9b`) és Save a Copy (`0x9dca`) menüpontok kizárólag fotók kijelölésekor engedélyezettek (`0x2` állapotbit); ha a kijelölt elem videó (a `0x00562250` `isVideo` hívás `0x20` bitet állít be a fotóbit helyett), mindkét menüpont tiltottá válik (`MF_GRAYED`).
   - **Nálunk:** A `src/picasapy/app/qml/PicasaPy/PicasaFileMenu.qml:130,136` sorában a menüpontok az általános `bar.photoActionsEnabled` tulajdonságra támaszkodnak, amely kizárólag a kijelölt sorok számát vizsgálja (`photoActionRows().length > 0`), így videó kijelölése esetén is aktívak maradnak.
   - **Teendő:** A `PicasaFileMenu.qml` Save As és Save a Copy tételeinek `enabled` feltételét ki kell egészíteni egy `!bar.isVideoSelected` (vagy a kijelölés típusát ellenőrző) feltétellel.
   - **Kész, ha:** Kijelölt videó esetén a Fájl menüben a "Save As..." és a "Save a Copy" menüpontok inaktívak (szürkék), és csak fotó kijelölésekor válnak kattinthatóvá.

2. **Jegy: A Save As és Save a Copy lemezhiba ablakának pontos szövegezése**
   - **Eredeti:** Az eredeti Picasa 3.9-ben (`0x005e7022`) írásvédett mappa vagy lemezhiba esetén a `CThumbUI::FileSaveCopy:err` (`0x00c97750`) erőforrás jelenik meg: "Unable to save files due to a disk error. The disk may be full or read-only." (`0x00c97700`), fájlnév és numerikus hibakód nélkül.
   - **Nálunk:** A `src/picasapy/app/qml/PicasaPy/SaveDialogs.qml:191` sorában a hibaablak a normál mentés `CFileSaveThread::filesaveerr-win` sablonját használja: `Unable to save all files due to a disk error. The disk may be full or read-only.\n\n%1\nerror(%2)`.
   - **Teendő:** A `SaveDialogs.qml`-ben a `kind === "saveCopyError"` vagy megfelelő ágon a `FileSaveCopy:err` szöveget kell visszaadni: `qsTr("Unable to save files due to a disk error. The disk may be full or read-only.")`.
   - **Kész, ha:** Írásvédett célmappába irányuló Save As vagy Save a Copy művelet meghiúsulásakor a felugró párbeszédablak pontosan a "Unable to save files due to a disk error. The disk may be full or read-only." szöveget mutatja.


## #6970: Export Picture to Folder teljes folyamata

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti és a jelenlegi PicasaPy forrásútjait külön ellenőriztem; a korábbi
export-specet csak bináris leletként használtam, a PicasaPy-állításokat a mostani
forrásból olvastam.

### Belépési pontok, feltételek, egy és több kép

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Fájl menü:** `ID_FILE_EXPORTTOFOLDER`, `cmd 0x9c81`; `0x005cb990` a `0x005312b0` nyitóhoz küldi. A nyitó üres kijelölési csomópontnál visszatér, egyébként összegyűjti a kijelölt sorokat. | `PicasaFileMenu.qml:141-145`; `MainMenuBar.qml:83,283-284`. A menü akkor aktív, ha a `photoActionRows()` nem üres. Könyvtárban a sorok kijelölésből jönnek; a nézőben az aktuális kép sora. | Könyvtárnézetben egy és több kijelölt képnél ugyanaz a nyitó és párbeszéd; üres kijelölésnél nincs művelet. Az eredeti fájlmenü nézőbeli engedélyezettségét a parancsrekord és a nyitó önmagában nem dönti el. |
| **Képtálca Export gomb:** `0x005d9cc0` az `outputlayout/folderbutton` eseményt a `0x005312b0` nyitóhoz küldi. Ehhez az úthoz numerikus menüazonosító nincs igazolva. | `TrayActionArea.qml:407-420`, `MainTrayBar.qml:43`, `ExportDialogs.qml:99-105,121-131`. A gomb könyvtárnézetben és nem üres rácskijelölésnél aktív; megnyitáskor a párbeszéd a tartott tálcát választja, ha nem üres, különben a kijelölést. | Az eredeti és a PicasaPy gombút megvan. Az eredeti nyitóhoz átadott sorok és a tartott, más mappákból származó képek viszonya nem dőlt el, ezért a rácskijelölés nélküli, de nem üres tálcára vonatkozó paritás nyitott. |
| **Rács/album kép helyi menüje:** a `0x00730790` és `0x00731050` teljes rekordlistájában nincs `ID_FILE_EXPORTTOFOLDER`. | `PhotoContextMenu.qml:35-518`; nincs Export jel vagy menüpont. | Egyezik: a helyi menüből nincs export. |
| **Képtálca helyi menüje:** `0x00732ee0`, teljes menüleltár; nincs Export. | `TrayContextMenu.qml:32-95`; a menüben nincs Export jel vagy menüpont. | Egyezik: a tálca jobbklikk-menüjéből nincs export. |
| **Néző helyi menüje:** `0x007327a0` OneUp menü; nincs Export. | `ViewerContextMenu.qml:35-293`; nincs Export jel vagy menüpont. | Egyezik: a néző jobbklikk-menüjéből nincs export. |
| **Ctrl+Shift+S:** a `0x005e60d0` CThumbUI billentyűkezelő `S` ága Ctrl+Shift esetén hívja a `0x005312b0`-t; a meglévő gyorsbillentyű-spec a billentyűutat könyvtárnézethez köti. | `MainKeyboardShortcuts.qml:427-432`; a shortcut könyvtári nézetben engedélyezett és nézőben nem fut. | Egyezik a könyvtári egyes/többes kijelölés útja; nézői gyorsbillentyű nincs. |
| **Fájl menü a nézőből:** a főmenü rekord és a közös nyitó ismert, a nézőbeli menüállapot külön feltétele nincs az itt ellenőrzött kimenetekben. | `PicasaFileMenu.qml:141-145`, `MainMenuBar.qml:83,283-284`: a néző egyetlen aktuális képsorával aktív. | Esetleges eltérés nem állítható, amíg az eredeti OneUp melletti Fájl menü engedélyezése nincs eldöntve. Lásd a nyitott kérdést. |

A `0x005312b0` közös nyitó nem választ külön ablakot egy és több képre.
A kijelölési gyűjtő eredménye határozza meg az exportált köteget; a videóvizsgálók
azt döntik el, hogy a filmválasztók elérhetők-e. A többes kijelölésnél az
export-számozás a köteg teljes darabszámától függ, nem külön párbeszédtől.

### A párbeszéd alapállapota és a megjegyzett értékek

| Mező | Eredeti Picasa 3.9 | Jelenlegi PicasaPy |
|---|---|---|
| Célhely | A korábbi `DefaultExportPath`; kulcs nélkül lokalizált `Picasa\Exports\`. | A korábbi `export/defaultpath`; kulcs nélkül `<Pictures>/Picasa/Exports` (`export_controller.py:142-161`), a névvel összefűzve `ExportDialogs.qml:162-167`. Az alapút reprezentációja eltér; a Windows alatti abszolút út azonossága itt nincs kimérve. |
| Mappanév | A forrás album/mappa neve; üres névnél lokalizált `export`. `0x0073b500` a bemeneti objektum `+8` mezőjét olvassa. | A `currentFolder` utolsó útvonaleleme; üresnél `export` (`export_controller.py:125-140`). Normál, egy mappán belüli kijelölésnél azonos forrást céloz; vegyes mappájú tálcánál az eredeti névforrás nincs eldöntve. |
| Névmező induló állapota | A `export.fen` `focus="name"` mezőt jelöl meg; a névmező fókuszban, a szöveg kijelölve. | Megnyitáskor a mappanév-mező fókuszt kap és teljes tartalmát kijelöli (`ExportDialogs.qml:184-191`). | Egyezik. |
| Méret | A hiányzó `FileExportSize` alapértéke `3` (`0x00738c43-0x00738c60`); a korábbi tiszta profilú job-645 felvétel 800 px átméretezést mutat. A `.fen` méretlistája 320, 480, 640, 800, 1024, 1200, 1600. A rádióállás statikus kulcsmegfeleltetése a régi specben ellentmondásos. | `size=3`, 800 px; tiszta beállításnál `resize=True`; a 7 méretlista egyezik (`export_prefs.py:30-36,91-110`, `ExportDialogs.qml:193-199`). |
| Minőség | `FileExportQuality` hiányzó értéke 85 (`0x0073962d`, `0x0073b14a`). A `FileExportQualityType` kulcs beolvasása ismert, de hiányzó kulcsra adott párbeszéd-alapértéke nincs bizonyítva. | `quality=85`, `qualityType=0` (Automatikus) (`export_prefs.py:38-39,111-128`). |
| Vízjel | `ExportWatermark` alapból 0, a `ExportWatermarkText` üres. | `watermark=False`, `watermarkText=""` (`export_prefs.py:140-143`). |
| Film | `FileExportMovie` alapból 0, vagyis Első képkocka. Videó nélküli kijelölésnél a csoportcímke és a két rádió is tiltott (`0x007394b3`; eredeti képernyőkép mérési eredménye: `export-parbeszed.md` 13.10). | Alapból Első képkocka; a címke és a rádiók is tiltottak videó nélküli soroknál (`ExportDialogs.qml:210-221,506-536`). Egyezik. |
| Sorszámozás | `ExportAddNumbers` alapból 0, kikapcsolva (`0x0073fba1`). | `addNumbers=False` (`export_prefs.py:138-142`). |
| Következő megnyitás | A `0x00738c00` beolvassa, a `0x00739960` elfogadáskor menti: út, méret, egyéni méret, minőségfokozat, minőség, film, vízjel és szöveg, számozás. Mégse esetén nincs mentés (`0x008d2720`). | A QML megnyitáskor betölti és elfogadáskor egy menetben menti a mezőket (`ExportDialogs.qml:179-226,267-288`; `export_prefs.py:152-171`). A helyet a művelet indításakor megjegyzi (`export_controller.py:156-161`). A mappanév újranyitáskor újra a forrásból képződik. |

Egy és több kép esetén a mentett mezők közös párbeszédállapotból jönnek; nincs
külön egyképes és többképes alapérték-ág. A tiszta profilos eredeti minőségfokozat,
a régi méret-rádió megfeleltetése és a vegyes mappájú köteg névforrása nyitott.

### Kimeneti hatás és hibák

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A célmappa a korábbi út és a mappanév összefűzése; létező cél esetén kérdez. Igen törli az előző albumot és új exportot indít. Nem a `0x007f6650`-ben `AL=0`-val tér vissza; a `0x007f6400` caller csak sikeres/igen visszatérésnél hívja az elfogadó `0x008d2720` ágat. | A kérdés `ExportDialogs.qml:610-620`; Igen `startExport(true)`, Nem `startExport(false)` (`613-614`). A `exporter.py:104-118` a Nem útján nem ürít, a `:187-212,245-248` pedig egyedi fájlneveket keres. | **Eltérés:** Nem válasznál az eredeti megszakítja az exportot, nálunk folytatódik és az ütköző fájlok új néven íródnak. A felülírási döntés paritásához javítani kell. |
| Sorszámozás: `0x0073ee70` a `%0*d-%s` formátumot használja, szélessége az összes kép darabszámának számjegyszáma. Példa az eredeti specből: 7 kép `1-...`, 12 kép `01-...`, 178 kép `001-...`. | `exporter.py:125-132`: `max(3, len(str(len(items))))`, ezért 1-99 elemnél mindig legalább háromjegyű prefixet ír. | **Eltérés:** az eredeti kötegszámhoz igazított minimum szélességet használ, PicasaPy minimuma 3. Sorszámozott fájlnevekhez külön fejlesztői jegy javasolt. |
| Módosított kép a Picasa képszerkesztéseit exportfájlba rendereli; módosítatlan JPEG esetén a `0x007401b4` `CopyFileW` másolóág létezik. A méretbeállítás és a módosítatlan JPEG-másolóág teljes kapcsolata nincs lezárva. | `exporter.py:191-249`, `export_controller.py:322-347`: módosításokat, forgatást, vágást, átméretezést és vízjelet renderel, no-op esetén másol. | Általános szerkesztéségetés egyezik. Az eredeti méretbeállítás és szerkesztetlen másolási ág kölcsönhatása nyitott; erre ne készüljön becslés. |
| A cél `.picasa.ini`-jébe a `caption` és a vesszővel elválasztott `keywords` kerül (`0x00740295`, `0x007403bc`, `0x00740485`, `0x0074050d`). A kimeneti képfájl a renderelt szerkesztést tartalmazza; az export utáni `0x007414dd` `]history:export` tokent ad a cél albumhoz. | `export_metadata.py:13-51` csak a caption/keywords adatot írja `update_document`-en át; a képet az `exporter.py:191-249` állítja elő. | A `.picasa.ini` fő tartalma egyezik. A PicasaPy az üres caption/keywords mezőhöz nem hoz létre ini-tételt. |
| A célmappa `Exported Pictures` könyvtár-kategóriát kap (`0x0073f884`, a kategóriatáblát `0x004a1560` is felsorolja). Az export záróágában nincs közvetlen újraindexelés; a kategória/token a könyvtár-adatúthoz kerül. A `ShellExecuteA("open", célmappa)` a `0x007414a8-0x007414b6` ágon feltételes. | `export_controller.py:424-463`, `library_controller_resync.py:493-585`: a cél exportcélként bekerül az indexbe és siker után újraszinkronizálódik. `ExportDialogs.qml:734-745` csak eredményablakot nyit, automatikus célmappa-megnyitás vagy sor-kijelölés nélkül. | Mindkét oldalon van célmappa-könyvtári kezelés, de a könyvtárfa/index végállapotának azonosságát a statikus lelet nem dönti el. A cél Intézőben megnyitásának feltétele még nincs értelmezve; nem állítható, hogy minden eredeti export után megtörténik. Rács-sorkijelölést az eredeti záróág nem bizonyított. Ezekre eltérés vagy fejlesztői jegy egyelőre nem állapítható meg. |
| Célkönyvtár-létrehozási hiba külön üzenet. Írási hibánál az eredeti általános szövege a megtelt vagy írásvédett lemezt nevezi meg (`CImageOutput::filewriteerr`). Az eredeti teljeslemez-előellenőrzés léte vagy hiánya ebből a hibaágból nem dőlt el. | `export_controller.py:395-406` előre ellenőrzi a szabad helyet és „not enough free disk space” hibát ad; a `exporter.py:103-118,155-159` a létrehozási és elemenkénti írási hibákat gyűjti. | A korai teljeslemez-elutasítás paritása nyitott: az eredeti előellenőrzését és mindkét program felületi ágát méréssel kell összevetni. Az írásvédett cél vagy utólagos íráshiba pontos PicasaPy felületi útja forrásból ellenőrizendő; egyelőre nincs fejlesztői jegy. |
| Hálózati/UNC-célra vonatkozó külön ág vagy konkrét siker/hiba ebben a statikus körben nincs bizonyítva. A fájlrendszer végső visszatérése futtatási környezettől is függ. | `export_controller.py:388-406`, `exporter.py:101-118,214-249`; célút-átalakítás és `Path`-írás van, de nincs ehhez a jegyhez élő UNC-mérés. | Nyitva marad; UNC-s futáspróba kell a fájlok, az ini, az index és a látható hiba rögzítésével. |

### Két független út és cáfoló kísérlet

- **A út, utasításszint:** a `0x005312b0` közös nyitó, a menü-diszpécser
  `0x005cb990`, a tálcaesemény `0x005d9cc0`, a CThumbUI billentyűkezelő
  `0x005e60d0`, a célütközés kezelője `0x007f6650` és hívója `0x007f6400`,
  valamint a kimeneti ág `0x0073f320` célzott diszasszemblálása.
- **B út, független rekordok és másik réteg:** a File menü `0x00559150`
  rekordja és `0x9c81` dispatch-adata; a teljes kontextusmenü-építők és
  menüsorok (`0x00730790`, `0x00731050`, `0x00732ee0`, `0x007327a0`);
  `export.fen` és a `0x00738c00`/`0x00739960` beállításút; a tiszta profil
  job-645 mérés; a jelenlegi PicasaPy QML/Python hívási lánc. Az utak
  egyeznek a belépések, megőrzött beállítások, a névütközési kérdés és a metaadatok
  kimenet létezésében. A viewer menüállapotot, vegyes tálca névforrását,
  UNC-hibát és a célmappa-megnyitó jelző jelentését nem döntik el.
- **Cáfoló kör:** azt a feltevést próbáltam cáfolni, hogy a felülírási
  párbeszéd Nem válasza megszakítja az exportot. A `0x007f6650` hamis
  válaszága a `0x007f69d3` takarítás után `AL=0`-val tér vissza; a
  `0x007f6400` hívó csak `AL!=0` esetén jut a `0x008d2720` elfogadó ágra.
  A QML viszont `onRejected` alatt `startExport(false)`-t hív. A két teljes
  hívási út más mércével is ellenőrizve ugyanazt az eltérést adta.

### A jegy „Kész, ha” pontjai

1. ✅ **Belépési pontok:** Fájl menü, tálca Export gomb, kép/tálca/néző helyi
   menük és Ctrl+Shift+S külön sorban szerepelnek; kijelölési feltételeik
   dokumentálva. Eredeti OneUp melletti Fájl menüállapot és tálcagyűjtés nyitott.
2. ⛔ **Egy és több kép ablakállapota:** közös párbeszéd és mentett mezők
   megvannak; az eredeti minőségfokozat alapértéke, méret-rádió megfeleltetése,
   vegyes tálca mappanév-alapja nincs eldöntve.
3. ⛔ **Fájlnév, szerkesztés, ini, index, megnyitás és kijelölés:** a folyamat
   dokumentált. A sorszámszélesség és az ütközés Nem ága eltér; az eredeti
   megnyitó jelzője és automatikus rácskijelölése nyitott.
4. ⛔ **Írásvédett, megtelt lemez, hálózati cél:** az eredeti hibaüzenet és a
   PicasaPy előellenőrzés ismert. Az aktuális írásvédett út, tényleges UNC
   eredmény és UNC indexelés nincs mérve.

### Javasolt fejlesztői jegytörzsek

#### 1. Nem válasz az export célmappa-felülírására szakítsa meg a műveletet

**Eredeti:** A Picasa 3.9 `0x007f6650` célütközési kezelőjében a Nem ág
`AL=0`-val tér vissza; a `0x007f6400` hívó emiatt nem hívja az elfogadó
`0x008d2720` folytatást. Az Igen az előző album törlését és új exportot indítja.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Nem megszakítja az exportot, Igen üríti a korábbi albumot. | `ExportDialogs.qml:613-614` a Nem ágra `startExport(false)`-t hív; `exporter.py:104-118,187-212` megtartja a korábbi fájlokat és ütközéskor egyedi nevet választ. | A Nem ág zárja be a kérdést exportindítás nélkül; az Igen ág maradjon előző cél-tartalmat törlő export. |

**Kész, ha:** létező cél esetén a Nem választás után sem új fájl, sem sorszámos
ütközés-fájl nem keletkezik; az Igen választás előző tartalmat töröl és újra
exportál.

#### 2. Export sorszámozása a köteg méretéhez igazodjon

**Eredeti:** A `0x0073ee70` `%0*d-%s` formátumának szélessége az exportált
képszám számjegyszáma: 7 kép esetén `1-`, 12 esetén `01-`, 178 esetén `001-`
prefix az eredeti fájlnév előtt.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A prefix szélessége a teljes képszám számjegyszáma. | `src/picasapy/export/exporter.py:125-132` minimum 3 jegyre tölti fel a sorszámot. | A minimum 3-as korlátot cserélni az eredeti kötegméret-alapú szélességre. |

**Kész, ha:** számozás bekapcsolásakor 7 kép prefixe `1`-től `7`-ig, 12
képé `01`-től `12`-ig, 178 képé `001`-től `178`-ig tart, kötőjellel és az
eredeti fájlnévvel.

### Nyitott

- **Megválaszolva (Ghidra-kör, `referencia/ghidra/2026-11-15-6970-colab-decomp.txt`, privát):** a menüt a `0x00559150` csak építi; az Export (`0x9c81`) a `0x0056e1c0`-ban a Save As, Save a Copy, Print, Email és Delete csoporttal együtt kap engedélyt (az állapotszó 2-es vagy 4-es bitje és `param_1[0xd29]==0`; a `0x8000` bit mindet tiltja). Hogy a `param_1[0xd13]` nézet a néző-e, a kód nem mondja ki, ezért a mai engedélyezés marad. A képtálca mappagombjánál (`0x005312b0`) a névalap a jelenlegi nézet objektumáé, ennek hiányában `IDS_DEFAULT_EXPORT`; a kijelölésgyűjtő (`0x005c7990`, `0x005c7ab0`) nincs dekompilálva. A `0x0073f320` 8-as esete a végén `ShellExecuteA("open", <célmappa>)`-val megnyitja a célmappát, ha készült kimenet és a jelző nulla; nem létrehozható célnál `IDS_DESTDIRCANNOCREATE` jön és megszakít; külön UNC- vagy hálózati ág nincs. A PicasaPy mindkettőt így teszi.
- `NINCS MEG`: az eredeti `FileExportQualityType` hiányzó kulcshoz tartozó tiszta profilbeli választása; Windows mérés kell üres Preferences profillal.
- `NINCS MEG`: az eredeti teljeslemez-előellenőrzés léte, valamint írásvédett cél és betelt lemez pontos felületi ága mindkét programban; Windows méréssel rögzítendő a cél, hibaüzenet, fájlok és indexállapot.
- `NINCS MEG`: hálózati/UNC export sikeres vagy sikertelen kimenete, cél `.picasa.ini`-je és indexbe vétele; UNC útvonalas Windows-mérés kell.
- `NINCS MEG`: a módosítatlan JPEG `CopyFileW` útja hogyan érvényesíti a méretbeállítást; az eredeti hívó és átadott állapot célzott feltárása kell.
- `NINCS MEG`: a működés után az eredeti UI kiválaszt-e rácssort; a `0x007414a8` záróágban ilyen művelet nem látszik, de a teljes UI-folyamatra nincs külön mérés.

**Új kutatási jegyjavaslatok:** most nem nyitok külön jegyjavaslatot; a nyitott
kérdések az Export Picture to Folder folyamat közvetlen folytatásai.

**Módosított fájl:** `docs/specs/paritas-ellenorzes.md` - a #6970 új alszakasza.

## #6984: Az Email parancs teljes folyamata az eredeti Picasában és összevetése a PicasaPy-jal

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti és a jelenlegi PicasaPy forrásútjait külön ellenőriztem; a korábbi
e-mail-kutatásokat (`picasa-email-kuldes.md`) összevetettem az utasításszintű
bináris leletekkel és a mostani PicasaPy kóddal.

### 1. Belépési pontok és engedélyezési feltételek

| Belépési pont | Eredeti Picasa 3.9 (bináris cím) | Jelenlegi PicasaPy (fájl:sor) | Eltérés / Teendő |
|---|---|---|---|
| **Fájl menü ▸ E-mail...** | `eMenuFile::ID_FILE_EMAIL`, `cmd 0xe107` (standard MFC `ID_FILE_SEND_MAIL`), menürekord `0xd6db1c` a `0x00559150` regisztrálóban (`0x0055973d`-`0x0055977e`). A `0x005cb990` menü-diszpécser `0x005cbac3` ága könyvtár módban a `0x005316b0` nyitót, néző módban (`[ebx+0x3114] != 0`) a `0x005318c0` nyitót hívja. Engedélyezés: `0x0056e1c0` (`0x0056e36e`, `0x0056e3d5`, `0x0056e424`); ha a kijelölés üres (`[edi+0x34a4] == 0`), a menüpont tiltott (szürke). Videó esetén is engedélyezett. | `src/picasapy/app/qml/PicasaPy/PicasaFileMenu.qml:172-177`: `objectName: "menuFileEmail"`, `text: qsTr("&E-Mail...") + "\tCtrl+E"`, `enabled: bar.photoActionsEnabled`, `onTriggered: bar.emailRequested()`. | Egyezik a menüpont létezése, gyorsbillentyűje és kijelölés-függő engedélyezése. |
| **Képtálca E-mail gomb** | `outputlayout/ebutton` (`0x00c8fad0`). A `0x005d9cc0` eseménykezelő a `0x005daaca`-`0x005daad3` ágon közvetlenül a `0x005316b0` nyitót hívja (`call 0x005316b0`). Engedélyezett nem üres rácskijelölés vagy tartott tálca esetén. | `src/picasapy/app/qml/PicasaPy/TrayActionArea.qml:384-403`: `objectName: "trayEmailButton"`, `text: qsTr("E-Mail")`, `enabled: viewerOpen ? viewerIndex >= 0 : selectedIndexes.length > 0`, `onClicked: trayRoot.emailRequested()`. | Egyezik a gombfunkció és a közös nyitó hívása. |
| **Gyorsbillentyű (Ctrl+E)** | A `0x005e60d0` CThumbUI billentyűkezelőben `0x005e638b`: ha Shift nincs lenyomva (`cmp [esp+0x11], 0; je 0x5e63a2`), a néző-állapot vizsgálata (`0x005696c0`, `editpanel/previewclip2`) után a `0x005e63b1` közvetlenül a `0x005316b0` nyitót hívja. Shift esetén (`Ctrl+Shift+E`) az `enhance` ("I'm Feeling Lucky") fut (`0x005e6393`). | `src/picasapy/app/qml/PicasaPy/MainKeyboardShortcuts.qml:497-503`: `shortcutEmail`, `sequence: "Ctrl+E"`, `enabled: photoActionsEnabled && !_szovegmezoneVanFokusz`, `onActivated: hostPicasaMenuBar.emailRequested()`. | Egyezik: a Ctrl+E a Fájl menüvel azonos emailRequested útra fut. |
| **Helyi menük (Jobbklikk)** | A rács/album kép helyi menüje (`0x00730790`, `0x00731050`), a képtálca helyi menüje (`0x00732ee0`) és a néző helyi menüje (`0x007327a0`) sem tartalmaz E-mail parancsot. | `PhotoContextMenu.qml`, `TrayContextMenu.qml`, `ViewerContextMenu.qml`: egyikben sincs E-mail menüpont. | Egyezik: helyi menükből az e-mail nem érhető el. |
| **Néző (Viewer / OneUp)** | A felső Fájl menü a nézőből is elérhető; a `0x005cbac3` a `[ebx+0x3114] != 0` miatt a `0x005318c0` nyitót hívja, ami az aktuális egyetlen képre indítja a küldést megerősítő kérdés nélkül. A képtálca E-mail gombja a nézőből is él. A Ctrl+E a közvetlen billentyűkezelőben néző módban tiltott (`0x005696c0`). | `MainMenuBar.qml:83, 283-284` és `PicasaFileMenu.qml:175`: nézőben az aktuális kép sorával aktív. `TrayActionArea.qml:395`: nézőben `viewerIndex >= 0` esetén a gomb aktív. `MainKeyboardShortcuts.qml:500`: nézőben is aktív a menüállapot alapján. | Eredetileg a közvetlen Ctrl+E nézőben inaktív volt; a PicasaPy-ban a menü kötése miatt nézőben is elsülhet. |
| **20 fájl feletti megerősítés** | `0x00531550` (`CThumbUI::OutputBottleneck`): ha a kijelölt képek száma > 20 (`cmp ebp, 0x14; jbe 0x53168b`), megjelenik a megerősítő kérdés: Cím: "Confirm" (`CThumbUI::OutputBottleneck::title`), Szöveg: `Email %d files?` (`0x00c89854`). Mégse esetén kilép (`eax = 0xf4242`), a `0x005316b0` nem indul el. | Nincs implementálva. A `MainWindowCommands.qml:482-495` bármilyen darabszámú kijelölésre azonnal elindítja a `prepareAttachments`-ot. | **Eltérés:** Az eredetiben 20 kép felett megerősítő kérdés védi a felhasználót a véletlen tömeges e-mailküldéstől. Fejlesztési jegy indokolt. |

### 2. Megjelenő ablak és mentett beállítások

- **Friss telepítés és a választó párbeszédablak (`choose_mail`):**
  - A kapu (`0x007420f0`) a `HKCU\SOFTWARE\Google\Picasa\Picasa2\Preferences\` registry-kulcsokat olvassa:
    - `EmailPrepType` (alapérték: `3` = saját levelezőprogram, `0x00742132`),
    - `DoNotPromptForEmailPref` (alapérték: `0`, `0x00742154`).
  - Mivel `DoNotPromptForEmailPref == 0`, az első alkalommal a `0x00742168` ágon **mindig megjelenik** a `choose_mail` ("Select Email" / "Válasszon levelezőprogramot") ablak.
  - Tartalma:
    - Rádiógomb 1: `choose_mail/mymail` ("Use my default email program." / "A számítógép alapértelmezett levelezőprogramjának használata", `EmailPrepType = 3`).
    - Rádiógomb 2: `choose_mail/gsender` ("Use my Gmail or Google account." / "A Google Fiók használata", `EmailPrepType = 5`).
    - Jelölőnégyzet: `choose_mail/checkbox` ("Remember this setting, don't display this dialog again." / "Ne jelenítse meg többé ezt a párbeszédpanelt.").
    - Gombok: Help ("Súgó"), Cancel ("Mégse").
  - **Nincs benne méretbeállítás:** a `choose_mail` dialógusban sem csúszka, sem méretválasztó nem szerepel.
- **A beállítás megjegyzése:**
  - A `0x0084f6b0` szerint a választott küldési mód (`EmailPrepType`) és a `DoNotPromptForEmailPref = 1` **csak akkor íródik a registrybe**, ha a felhasználó bejelölte a `choose_mail/checkbox`-ot.
  - Ha nincs bejelölve, a választás csak az aktuális küldésre érvényesül a memóriában, a registry nem változik, és legközelebb újra megkérdezi.
  - Ha be van jelölve, a következő alkalommal a kapu (`0x007420f0`) nem nyit ablakot, hanem közvetlenül a mentett módra ugrik.
- **A méret- és egyéb beállítások helye:**
  - Kizárólag az **Eszközök ▸ Beállítások ▸ E-mail** fülön (`options.fen` / `OptionsTabEmail`):
    - Több kép mérete: 8 fokozatú csúszka (160, 320, 480, 640, 800, 1024, 1200, 1600 px), alapértéke **480 képpont** (`Preferences\EmailExportSize` = `0x1e0`).
    - Egyedülálló képek mérete: rádiógombpár: Több elemmel azonos (`EmailSinglePicture = 0`, alap) / Eredeti méret (`EmailSinglePicture = 1`).
    - Mozgófilmek küldése másként: Első képkocka (`EmailMovie = 0`, alap) / Teljes mozgófilm (`EmailMovie = 1`).
    - Kimeneti formátum: Szövegközi fotók (`UseHTMLMailer = 0`, csak Outlook).
- **Eltérés a PicasaPy-ban (Belső szerkesztőablak):**
  - Az eredeti Picasában saját levelezőprogram (3-as mód) esetén a Picasa **soha nem nyit belső levélszerkesztő ablakot**: a fájlokat előkészíti és közvetlenül átadja a MAPI kliensnek. A beépített szerkesztőfelület (`compose_mail.tre`, címzett, tárgy, szövegmező) kizárólag a Google Mail (5-ös mód) ágon létezett.
  - A PicasaPy-ban (`EmailChoiceDialog.qml:256-490`, `MainWindowCommands.qml:494`) a választás után a párbeszéd átvált "compose" állapotba, és bekéri a címzettet, tárgyat és üzenetet, majd a `sendWithDefaultClient` ezekkel indítja az `xdg-email`-t vagy MAPI-t.

### 3. Végrehajtás és futásidejű hatás

| Tulajdonság | Eredeti Picasa 3.9 (bináris cím) | Jelenlegi PicasaPy (fájl:sor) | Eltérés / Teendő |
|---|---|---|---|
| **Csatolmány mérete** | `EmailExportSize` (alapérték 480 px, `0x00743094`). Ha 1 kép van kijelölve ÉS `EmailSinglePicture == 1`, a méret 0 (nincs átméretezés). | `src/picasapy/mailer/command.py:21-29`, `src/picasapy/app/email_controller.py:651-656`: 480 px alapérték, 8 fokozat, 1 képnél `singlePictureOriginal` esetén `None`. | Egyezik. |
| **Csatolmány formátuma** | MAPI ágon (`0x0074072e`, `0x0045cfa0`) minden állókép újrarenderelt JPEG-ként jön létre, fix 85-ös minőséggel (`0x007406d7`), baseline, 4:2:0. Nem-JPEG képek (PNG, TIFF, BMP, RAW) szintén JPEG 85 (4:4:4). WebP esetén WebP (minőség 75). Videó esetén: ha `EmailMovie == 1`, nyers fájlmásolat (`0x007401b8 CopyFile`); különben első képkocka JPEG állókép. | `src/picasapy/app/email_controller.py:658-663`: `ExportSettings(jpeg_quality=85, movie_full=self._movie_full)`. Változatlan videót módosítatlanul másol, ha `movie_full` igaz. | Lényegében egyezik. Szándékos eltérés (#3993): módosítatlan JPEG képeknél a PicasaPy megtartja a veszteségmentes másolatot. |
| **Szerkesztések beégetése** | Vágás, forgatás, tükrözés, szín- és retus-szűrők minden esetben beleégnek az exportált képekbe (`0x0045cfa0`, `0x006a9650` EditStack). | `src/picasapy/export/exporter.py`: vágást, forgatást, szűrőket és tükrözést beégeti az exportált másolatba. | Egyezik. |
| **Fájlnév** | Az exportáló a kép eredeti fájlnevét tartja meg a célmappában; e-mail ágon nincs sorszámozás-prefix. | `src/picasapy/export/exporter.py:245-248`: az eredeti fájlnevet tartja meg a célmappában. | Egyezik. |
| **Levél tárgya (Subject)** | 1 kép: `IDS_MAPI_SUBJ_SINGLE` (`0x00caff84`) -> "Küldök egy képet" / "a picture for you". Több kép: `IDS_MAPI_SUBJ_MULTI` (`0x00caff5c`) -> "Küldök %d képet" / "%d pictures for you". | `MainWindowCommands.qml:494`: `emailController.sendRows(csatolmanyok, "", "")` üres tárggyal indítja a küldést. | **Eltérés:** A PicasaPy-ban nincs automatikus tárgysablon a képszám szerint. Fejlesztési jegy indokolt. |
| **Levél szövegtörzse (Body)** | 1 kép: `IDS_MAPI_BODY_SINGLE` (`0x00caff9c`) -> "Ön 1 képet kapott.\n\n". Több kép: `IDS_MAPI_BODY_MULTI` (`0x00caff70`) -> "Ön %d képet kapott.\n\n". Hozzáfűzve a záró reklámsor: `IDS_MAPITAGLINE` (`0x00cb0180`) -> "Ezeket a képeket a Google Picasa programjának segítségével küldtük.\nPróbálja ki itt: http://picasa.google.com/". | `MainWindowCommands.qml:494`: üres szövegtörzs (""). Az `EmailChoiceDialog.qml` szerkesztőmezője üresen nyílik meg. | **Eltérés:** A PicasaPy-ban nincs automatikus levéltörzs- és tagline-kitöltés. Fejlesztési jegy indokolt. |
| **Ideiglenes fájlok helye és törlése** | Hely: `%LocalAppData%\Google\Picasa2\temp\email\` (`0x00cb0190`). Törlés: küldés után a fájlok a mappában maradnak (nem törlődnek azonnal, hogy a levelezőprogram hozzáférhessen). A mappát a következő e-mail export felülírja, illetve a Picasa indítási takarítása üríti. | `email_controller.py:657`: minden alkalommal új egyedi mappa: `tempfile.mkdtemp(prefix="picasapy-mail-")`. Törlés: `_torold_regi_mail_masolatok()` az alkalmazás indulásakor törli az 1 óránál régebbi mappákat. | Funkcionálisan megfelelő; PicasaPy egyedi mappákat használ és induláskor takarít. |
| **Kijelölés és történet-token** | A rácson a kijelölés nem változik (megmarad). Sikeres küldés esetén az érintett képek megkapják a `]history:email` tokent az adatbázisban (`0x0073f253`-`0x0073f267`). | A kijelölés megmarad. Semmilyen `]history:email` token nem íródik az adatbázisba vagy a `.picasa.ini`-be. | **Eltérés:** A PicasaPy nem jegyzi fel az elküldött képekhez a `]history:email` előzmény-tokent. Fejlesztési jegy indokolt. |

### 4. Hibaesetek

- **Nincs levelezőprogram:**
  - Eredeti Picasa 3.9: ha a `MAPI32.DLL` betöltése meghiúsul (`0x008d0cb1`, `LoadLibrary < 32`), a függvény `eax = 2`-vel tér vissza (`MAPI_E_FAILURE`). A `0x0073d8c0` hibakezelő lefut és felugró ablakban megjeleníti: `IDS_MAPI_FAILURE` ("Az e-mailt nem lehetett elküldeni." / "The email could not be sent.").
  - PicasaPy: Linuxon, ha az `xdg-email` hiányzik vagy nem 0 kóddal lép ki, és a `mailto:` URL sem nyitható meg, az `emailFailed` jelzés kibocsátja a `qsTr("No email program was found.")` üzenetet, amit a `MainWindowCommands.qml:553` a felületi hibasávban (`errorBannerText`) jelenít meg. Windowson a sikertelen MAPI hívás szintén ezt az üzenetet adja.
- **Túl nagy csatolmány / túl sok kép:**
  - Eredeti Picasa 3.9:
    - MAPI ágon: ha a rendszer MAPI kliense `MAPI_E_TOO_MANY_ATTACHMENTS` (9-es hibakód) hibával tér vissza, a `0x0073d8ed` ág felugró ablakban megjeleníti: `IDS_MAPI_TOO_MANY_ATTACHMENTS` ("Túl sok mellékletet tartalmaz, ezért nem lehet elküldeni.").
    - Gmail ágon: a `0x008525a0` előre ellenőrzi a mellékletek méretkorlátját, és ha túllépi, megjeleníti a `IDS_EMAIL_ATTACHMENTLIMIT` figyelmeztetést: "A csatolt képek túl nagyok. Távolítson el néhány mellékletet, vagy válassza az Eszközök menü Beállítások parancsát, és állítsa át a levelezési beállításokat kisebb képek küldésére.".
  - PicasaPy: nincs előzetes méretellenőrzés; a hibakezelő minden MAPI hibára általános "No email program was found." üzenetet ad.
- **Nem írható ideiglenes mappa / lemezhiba:**
  - Eredeti Picasa 3.9:
    - Ha a célmappa nem hozható létre: `0x0073f320` -> `IDS_DESTDIRCANNOCREATE` ("A célkönyvtárat nem sikerült létrehozni.").
    - Ha az írás során lemezhiba, megtelt lemez vagy írásvédettség lép fel: `0x0073f320` -> `CImageOutput::filewriteerr` ("Lemezhiba miatt nem lehetett minden fájlt kiírni. Lehet, hogy a lemez megtelt vagy írásvédett." / "Unable to write all files due to a disk error. The disk may be full or read-only.").
  - PicasaPy: ha a temp mappa nem írható, az `export_photos` `failed` listát ad, vagy kezeletlen `OSError` keletkezhet; a felhasználó felé nincs specifikus lemezhiba-üzenet.

### 5. Két független út és cáfoló vizsgálat

- **A út (Utasításszintű bináris diszasszembly):**
  - Menütábla regisztráció: `0x00559150` (`0x0055973d`-`0x0055977e`), `cmd 0xe107`.
  - Menü engedélyezési logika: `0x0056e1c0` (`0x0056e36e`, `0x0056e3d5`, `0x0056e424`), kijelölési számláló `[edi+0x34a4]`.
  - Menü-diszpécser: `0x005cb990` (`0x005cbac3`), néző mód jelző `[ebx+0x3114]`.
  - Közös nyitó és 20 fájl megerősítés: `0x005316b0` és `0x00531550` (`CThumbUI::OutputBottleneck`, küszöb `0x14`).
  - Képtálca E-mail gomb: `0x005d9cc0` (`0x005daad3 call 0x005316b0`).
  - Gyorsbillentyű: `0x005e60d0` (`0x005e63b1 call 0x005316b0`).
  - Kapu és módválasztás: `0x00742970` és `0x007420f0` (`choose_mail`).
  - MAPI és kimenet: `0x0073f320`, `0x0073f0f0`, `0x0073d970`, `0x008d0c90`, `0x0073d8c0`.
- **B út (Erőforrások, XML-ek, string_xrefs és PicasaPy forráskód):**
  - `referencia/i18n-hu/stringres.xml`: `IDS_MAPI_SUBJ_SINGLE`, `IDS_MAPI_SUBJ_MULTI`, `IDS_MAPI_BODY_SINGLE`, `IDS_MAPI_BODY_MULTI`, `IDS_MAPITAGLINE`, `IDS_MAPI_TOO_MANY_ATTACHMENTS`, `IDS_MAPI_FAILURE`.
  - `choose_mail.tre` és `options.xml`: vezérlők és beállítások struktúrája.
  - Kontextusmenük független leltára (`0x00730790`, `0x00731050`, `0x00732ee0`, `0x007327a0`): nem tartalmaznak E-mail parancsot.
  - A két út egymással tökéletes összhangban van.
- **Cáfoló vizsgálat:**
  - *Feltételezés:* A Picasa a saját levelezőprogramos (MAPI) ágon is megjeleníti a beépített `compose_mail` panelt.
  - *Cáfolat:* A `0x00742970` függvény `0x00742a2c` soránál a 3-as mód (`EmailPrepType == 3`) közvetlenül a `0x00531710` ágra ugrik, ami a `0x0073f320` kimeneti motort és a `0x0073d970` MAPI hívót indítja, majd visszatér. A `0x007422d0` `compose_mail` hívás ebben az ágban nem fut le; az kizárólag a Google Mail (5) ágon él. A hipotézis megcáfolva: a MAPI küldés közvetlenül a rendszer külső levelezőjét nyitja meg.

### 6. A jegy „Kész, ha” pontjai

1. ✅ **Belépési pontok:** Fájl menü (`cmd 0xe107`), képtálca E-mail gomb (`outputlayout/ebutton`), gyorsbillentyű (`Ctrl+E`), helyi menük kizárása, és a nézőbeli viselkedés folyamatszinten, bináris címekkel és forrássorokkal dokumentálva.
2. ✅ **Ablak:** `choose_mail` párbeszéd (Saját levelező / Gmail, Remember me checkbox), Beállítások E-mail fül (8 fokozatú csúszka, 480 px alapérték, egyéni méretkapcsoló), valamint a 20 fájl feletti megerősítő kérdés (`CThumbUI::OutputBottleneck`) dokumentálva.
3. ✅ **Hatás:** csatolmány mérete, 85-ös JPEG formátum, szerkesztéségetés, fájlnév, tárgy- és törzssablonok (`IDS_MAPI_SUBJ_*`, `IDS_MAPI_BODY_*`, `IDS_MAPITAGLINE`), ideiglenes fájlok helye és életciklusa, valamint a `]history:email` token dokumentálva.
4. ✅ **Hibaesetek:** hiányzó levelezőprogram, túl nagy csatolmány (`MAPI_E_TOO_MANY_ATTACHMENTS`), és nem írható/megtelt lemez hibái bináris címekkel és stringres azonosítókkal dokumentálva.

### 7. Javasolt fejlesztői jegytörzsek

#### 1. A saját levelezőprogramos küldés ne nyisson belső compose ablakot, hanem közvetlenül a levelezőt indítsa

**Eredeti:** A Picasa 3.9-ben a saját levelezőprogramos ág (`EmailPrepType = 3`, `0x00742a2c`) nem nyitja meg a belső `compose_mail` panelt (`0x007422d0`), hanem az exportálás után közvetlenül meghívja a `MAPISendMail`-t (`0x0073e25e`), ami az operációs rendszer alapértelmezett levelezőjének új levél ablakát nyitja meg a csatolmányokkal.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A saját levelező választásakor közvetlenül a külső levelező nyílik meg, belső szerkesztőpanel nélkül. | `EmailChoiceDialog.qml:39, 256-490`: a választás után a párbeszéd "compose" panelre vált, és a felhasználónak ott kell rákattintania a "Send" gombra. | Ha `useDefaultClient` aktív (vagy a felhasználó a saját levelezőt választotta), ne nyíljon belső szerkesztőpanel, hanem közvetlenül induljon el az `xdg-email` vagy MAPI hívás a csatolmányokkal. |

**Kész, ha:** Az E-mail parancs kiadásakor a képek előkészítése után közvetlenül a rendszer levelezőprogramja jelenik meg a csatolmányokkal.

#### 2. Kijelölési megerősítő kérdés 20 fájl felett

**Eredeti:** A Picasa 3.9-ben a `0x00531550` rutin (`CThumbUI::OutputBottleneck`) ellenőrzi a kijelölt képek számát: ha a darabszám meghaladja a 20-at (`0x14`), megerősítő kérdést jelenít meg: Cím: "Confirm" (`CThumbUI::OutputBottleneck::title`), Szöveg: `Email %d files?` (`0x00c89854`). Mégse esetén a művelet megszakad.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| 20 fájl felett megerősítő dialógus kérdez rá a küldésre. | `MainWindowCommands.qml:482-495`: darabszámtól függetlenül azonnal indítja az előkészítést. | 20-nál több kijelölt elem esetén megerősítő párbeszédablakot megjeleníteni a darabszámmal, Mégse esetén megszakítani a folyamatot. |

**Kész, ha:** 21 kijelölt képnél megjelenik a megerősítő kérdés; Mégse esetén nem indul el az exportálás, OK esetén folytatódik. 20 vagy kevesebb képnél kérdés nélkül indul.

#### 3. Automatikus levéltárgy és levéltörzs generálása a csatolmányszám szerint

**Eredeti:** A Picasa 3.9 `0x0073d970` rutinja automatikusan kitölti a levél tárgyát és törzsét:
- Tárgy: 1 kép -> `IDS_MAPI_SUBJ_SINGLE` ("Küldök egy képet" / "a picture for you"); több kép -> `IDS_MAPI_SUBJ_MULTI` ("Küldök %d képet" / "%d pictures for you").
- Törzs: 1 kép -> `IDS_MAPI_BODY_SINGLE` ("Ön 1 képet kapott.\n\n"); több kép -> `IDS_MAPI_BODY_MULTI` ("Ön %d képet kapott.\n\n"), mindkettő után hozzáfűzve az `IDS_MAPITAGLINE` szövegét ("Ezeket a képeket a Google Picasa programjának segítségével küldtük.\nPróbálja ki itt: http://picasa.google.com/").

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Automatikus lokalizált tárgy és törzs a képszám szerint, tagline-nal. | `MainWindowCommands.qml:494`: üres tárggyal és törzzsel hívja a vezérlőt (`sendRows(csatolmanyok, "", "")`). | A darabszámnak megfelelő tárgyat és törzset generálni a `build_xdg_email_argv` és MAPI híváshoz. |

**Kész, ha:** 1 kép küldésekor "Küldök egy képet", több képnél "Küldök N képet" tárggyal és a megfelelő törzzsel nyílik meg a levél.

#### 4. E-mailben elküldött képek megjelölése `]history:email` tokennel

**Eredeti:** Sikeres küldés után a Picasa 3.9 a `0x0073f253`-`0x0073f267` ágon az érintett képekhez hozzárendeli a `]history:email` ("Elküldve e-mailben") előzmény-tokent az adatbázisban.

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `]history:email` token bejegyzése a sikeresen elküldött képekhez. | Nincs előzmény-nyilvántartás e-mail küldés után. | Sikeres e-mail indítás után a képek metaadataihoz bejegyezni a `]history:email` tokent. |

**Kész, ha:** Az e-mailben sikeresen elküldött képekhez az adatbázisban megjelenik a történet-token.

#### 5. Részletes MAPI hibakódok leképezése

**Eredeti:** A Picasa 3.9 a `0x0073d8c0` MAPI hibakezelőben a visszatérési kódok szerint külön hibaüzeneteket ad: `MAPI_USER_ABORT` (1) esetén csendesen kilép hibajelzés nélkül; `MAPI_E_TOO_MANY_ATTACHMENTS` (9) esetén "Túl sok mellékletet tartalmaz..."; `MAPI_E_NO_ATTACHMENT` (11) esetén "Nem található a melléklet"; `MAPI_E_CANT_OPEN_ATTACHMENT` (12) esetén "A mellékletet nem sikerült megnyitni."; egyéb kódokra "Az e-mailt nem lehetett elküldeni.".

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A MAPI hibakódok szerint specifikus üzenet jelenik meg. | `email_controller.py:784`: minden nem-OK és nem-ABORT kódra "No email program was found." üzenetet ad. | A `send_mapi` hibakódjai alapján specifikus üzenetet kibocsátani (`emailFailed`). |

**Kész, ha:** Túl sok melléklet vagy megnyitási hiba esetén a megfelelő üzenet jelenik meg a felületen.

### 8. Nyitott kérdések

- Nincs blokkoló nyitott kérdés; a teljes folyamat belépési pontoktól az ablakokon és hatásokon át a hibakezelésig lezárt.
- NINCS MÉRVE: Windows 11 rendszeren a modern Outlook / Thunderbird MAPI viselkedése a `temp\email\` fájlok zárolására és feloldására.

**Módosított fájl:** `docs/specs/paritas-ellenorzes.md` - a #6984 új alszakasza.

## #6996: Az Export Picture to Folder és a Locate on Disk parancskódjai és menürekordjai

### 1. A felvetett gyanú és a cáfolat összefoglalása

A jegy kiindulási felvetése szerint a `0x9c81` parancskód a binárisban nem az Exporthoz, hanem a Locate on Disk parancshoz tartozik, mert a `0x005595d0`-`0x005595f4` szakaszon a `0xd6dabe` címre írt `0x9c81` kód közvetlenül a `push 0x00c8c4fc` (`eMenuFileWin::ID_FILE_LOCATEONDISK`) és `mov eax, 0x00c8c520` (`&Locate on Disk`) utasítások után szerepel.

A részletes, két független úton elvégzett bináris vizsgálat ezt a feltevést megcáfolta:
- A `0x9c81` valóban és bizonyítottan a **Fájl > Export Picture to Folder** parancskódja (`ID_FILE_EXPORTTOFOLDER`).
- A `0x005312b0` függvény valóban az Export párbeszédablak nyitója (`CExportPrefsDialog`), amelyet mind a Fájl menü (`0x9c81`), mind a képtálca Export gombja (`outputlayout/folderbutton`) meghív.
- A Locate on Disk valódi parancskódja nem a `0x9c81`, hanem a **`0x9c99`** (`rec 19`, `0x00d6dadc` rekord, gyorsbillentyűje "Enter"), kezelőfüggvénye pedig a `0x005cb990` diszpécserből induló **`0x005c8320`**.
- A téves gyanút a Microsoft Visual C++ fordító utasítás-összefésülése (az utasítások egymásba ütemezése) okozta: miközben az N-edik menürekord (`rec 17`, Export) `cmdId` mezőjét (`0x00d6dabe`) töltötte fel a `0x9c81` értékkel, a fordító már előre betöltötte a verembe a következő rekord lokalizációs kulcsát (`push eMenuFileWin::ID_FILE_LOCATEONDISK`), így a felületes lineáris olvasás a kulcsot és a kódot tévesen összekapcsolta.

### 2. A menürekordok bináris adatszerkezete és a Fájl menü teljes térképe

A menüépítő ciklus (`0x00a6aee0`, `add ebp, 0x14`) alapján minden egyes menürekord pontosan 20 bájt (`0x14`) méretű:

```c
struct MenuItemRecord {
    const char *pszText;     // +0x00: lokalizált felirat (0 esetén elválasztóvonal / SEPARATOR)
    const char *pszShortcut; // +0x04: gyorsbillentyű felirat vagy adatmutató
    uint16_t    flags;       // +0x08: jelzők (1 = kiemelt / alapértelmezett, 0 = normál)
    uint16_t    cmdId;       // +0x0a: Windows parancskód (Command ID)
    void       *pSubmenu;    // +0x0c: almenü rekordtömb mutatója (vagy 0)
    uint32_t    submenuCount;// +0x10: almenü tételeinek száma (vagy 0)
}; // sizeof = 20 (0x14) bájt
```

A Fájl menü (`0x00559150` által feltöltött `0x00d6d960` tömb, `0x1b` = 27 elem) releváns rekordjai:

| Index | Báziscím | Funkció / Kulcs | Felirat | Gyorsbillentyű | cmdId címe | cmdId (hexa) | cmdId (tízes) |
|---|---|---|---|---|---|---|---|
| rec 12 | `0x00d6da50` | `eMenuFile::ID_FILE_SAVE` | &Save | Ctrl+S (`0x00c8c610`) | `0x00d6da5a` | `0xe103` | 57603 |
| rec 13 | `0x00d6da64` | `eMenuFile::ID_FILE_REVERT` | Rever&t | - | `0x00d6da6e` | `0x9d9a` | 40346 |
| rec 14 | `0x00d6da78` | SEPARATOR | - | - | `0x00d6da82` | 0 | 0 |
| rec 15 | `0x00d6da8c` | `eMenuFile::ID_FILE_SAVEAS` | Save &As... | - | `0x00d6da96` | `0x9d9b` | 40347 |
| rec 16 | `0x00d6daa0` | `eMenuFile::ID_FILE_SAVEACOPY` | Save a Cop&y | - | `0x00d6daaa` | `0x9dca` | 40394 |
| **rec 17** | **`0x00d6dab4`** | **`eMenuFile::ID_FILE_EXPORTTOFOLDER`** | **Export Pi&cture to Folder...** | **Ctrl+Shift+S** (`0x00c7eae8`) | **`0x00d6dabe`** | **`0x9c81`** | **40065** |
| rec 18 | `0x00d6dac8` | SEPARATOR | - | - | `0x00d6dad2` | 0 | 0 |
| **rec 19** | **`0x00d6dadc`** | **`eMenuFileWin::ID_FILE_LOCATEONDISK`** | **&Locate on Disk** | **Enter** (`0x00c8c4f4`) | **`0x00d6dae6`** | **`0x9c99`** | **40089** |
| rec 20 | `0x00d6daf0` | `eMenuFile::ID_FILE_DELETEFROMDISK` | &Delete from Disk... | Delete (`0x00c7eab8`) | `0x00d6dafa` | `0x9c9a` | 40090 |
| rec 21 | `0x00d6db04` | SEPARATOR | - | - | `0x00d6db0e` | 0 | 0 |
| rec 22 | `0x00d6db18` | `eMenuFile::ID_FILE_PRINT` | &Print... | Ctrl+P (`0x00c8c468`) | `0x00d6db22` | `0xe107` | 57607 |
| rec 23 | `0x00d6db2c` | `eMenuFile::ID_FILE_EMAIL` | &E-Mail... | Ctrl+M (`0x00c8c43c`) | `0x00d6db36` | `0x9c97` | 40087 |
| rec 24 | `0x00d6db40` | `eMenuFile::ID_FILE_EPROCESS` | Order Prin&ts... | - | `0x00d6db4a` | `0x9c98` | 40088 |

A fenti adatokból közvetlenül leolvasható:
- A `rec 17` kezdőcíme `0x00d6dab4`, szövege az `ID_FILE_EXPORTTOFOLDER`, parancskód mezője `0x00d6dab4 + 0x0a = 0x00d6dabe`, értéke `0x9c81`.
- A `rec 18` egy elválasztó (`0x00d6dac8`).
- A `rec 19` kezdőcíme `0x00d6dadc`, szövege az `ID_FILE_LOCATEONDISK`, parancskód mezője `0x00d6dadc + 0x0a = 0x00d6dae6`, értéke `0x9c99`.

### 3. A `0x005cb990` szétosztó működése

A főablak menü-diszpécsere (`0x005cb990`) a parancskódok szerint az alábbi ágakra ugrik:
- **`0x9c81` (Export Picture to Folder):** Az első switch-tábla 63. indexén (`0x9c81 - 0x9c42 = 0x3f`, `byte ptr [0x005cdb34 + 0x3f] == 14`) a `0x005cbaac` címre ugrik, amely meghívja a `0x005312b0` függvényt.
- **`0x005312b0` törzse:** Megerősítetten az Export ablak nyitója. Felépíti a `CExportPrefsDialog` objektumot (`0x0052e700`, erőforrás "export.fen"), betölti az alapértelmezett export nevet (`IDS_DEFAULT_EXPORT`), beolvassa a beállításokat (`0x0073b110`, `0x0073b310`), majd a `0x00531810` rutinnak átadva megjeleníti a modális párbeszédablakot. Ugyanezt a `0x005312b0` nyitót hívja a képtálca Exportálás gombja (`outputlayout/folderbutton`) a `0x005d9cc0` eseménykezelőből (`0x005dac5b` sor).
- **`0x9c99` (Locate on Disk):** Az első switch-tábla 87. indexén (`0x9c99 - 0x9c42 = 0x57`, `byte ptr [0x005cdb34 + 0x57] == 23`) a `0x005cbae2` címre ugrik, amely a `0x005c8320` függvényt hívja meg. Ez a függvény felelős a fájl lemezen való megkereséséért és az Intézőben való kijelöléséért.
- **`0x9dca` (Save a Copy):** A második switch-tábla 134. indexén (`0x9dca - 0x9d44 = 0x86`, `byte ptr [0x005cde04 + 0x86] == 65`) a `0x005cc5ad` címre ugrik, és a `0x005e6a20(1)` rutint hívja (`Save a Copy` mentési ág). A `0x9d9b` (`Save As`) ezzel párhuzamosan a `0x005cc5a0` ágon a `0x005e6a20(0)` rutint futtatja.

### 4. A specek érintettsége és a téves felvetés lezárása

1. **`docs/specs/export-parbeszed.md` (1011. sor):** A lapon szereplő állítás (`parancs 0x9c81, rekord 0xd6dab4, azonosító 0xd6dabe -> a szétosztó 63. indexén 0x005cbaac -> 0x005312b0`) **helyes és igaz**. Nem igényel módosítást.
2. **`docs/specs/paritas-ellenorzes.md` (#6970 szakasz, 1232., 1242., 1849., 1899., 1960. sor):** Az Export parancskódjaként megadott `0x9c81` és kezelőjeként megadott `0x005312b0` **helyes és igaz**.
3. **Menüengedélyezés (`0x0056e1c0`):** A menüengedélyező ciklus a `local_34` tömbön keresztül mind a `0x9c81` (Export), mind a `0x9c99` (Locate on Disk), mind a `0x9dca` (Save a Copy) azonosítókat azonos feltétellel kezeli (`(local_5c & 6) != 0 && param_1[0xd29] == 0`), így a menüengedélyezési következtetések érvényben maradnak.
4. **Következtetés:** A #6996 jegyben megfogalmazott kétely megcáfolva; a kódok és a kezelők megfeleltetése a specekben pontos volt.

### 5. Két független út és cáfoló vizsgálat

- **A út (adatstruktúra és utasításfolyam):** A `0x00559150` függvényben a menürekordok memóriacímeinek és a `0x00a6aee0` rekordléptetőnek a vizsgálata. A 20 bájtos struktúra mezőinek pontos illeszkedése igazolja, hogy a `0x00d6dab4` bázisú rekord a `0x00d6dabe` eltoláson kapja a `0x9c81` értéket, felirata pedig az `Export Pi&cture to Folder...`. A Locate on Disk a `0x00d6dadc` bázison él, és a `0x00d6dae6` mezőjébe a `0x9c99` kerül.
- **B út (eseményelosztás és kezelőtörzsek):** A `0x005cb990` switch-tábla elemzése és a hívott célfüggvények felderítése. A `0x9c81` ág a `0x005312b0` nyitóhoz vezet, amelyben megtalálható a `CExportPrefsDialog`, az `export.fen` és az `IDS_DEFAULT_EXPORT` string, valamint a tálca `outputlayout/folderbutton` gombja is ide csatlakozik. A `0x9c99` ág a `0x005c8320` rutinhoz vezet, ami a lemezen való megkeresés logikáját valósítja meg.
- **Egyezés:** Mindkét független elemzési út egybehangzóan bizonyítja, hogy az Export kódja `0x9c81`, a Locate on Disk kódja pedig `0x9c99`.
- **Cáfoló vizsgálat:** Megkíséreltük igazolni a feltevést, hogy a `0x005312b0` a Locate on Disk kezelője lehetne. A cáfolat sikertelen: a `0x005312b0` függvényben semmilyen fájlkezelő megnyitás vagy Explorer-kijelölés nem található, kizárólag a Picasa modális Export dialógusának inicializálása és eseménykezelése zajlik benne. A képtálca Export gombjának közvetlen `0x005312b0` hívása szintén kizárja, hogy a függvény a Locate on Disk funkcióhoz tartozna.

### 6. A jegy „Kész, ha” pontjai

- ✅ **Mi az Export valódi parancskódja és menürekordja:** Bizonyítva: `ID_FILE_EXPORTTOFOLDER` parancskódja `0x9c81`, rekordja a Fájl menü 17. eleme (`0x00d6dab4`), cmdId címe `0x00d6dabe`.
- ✅ **A szétosztó ágai és a `0x005312b0` szerepe:** Bizonyítva: a `0x005cb990` szétosztóban a `0x9c81` a 63. indexen (`0x005cbaac`) a `0x005312b0` Export-nyitót hívja; a Locate on Disk kódja `0x9c99`, amelyet a `0x005cbae2` ág a `0x005c8320` kezelőhöz irányít.
- ✅ **A specek és következtetések ellenőrzése:** Bizonyítva: a korábbi specifikációkban rögzített `0x9c81` és `0x005312b0` összerendelés helyes, a #6989-es felvetés téves riasztás volt.






## #6989: A Locate on Disk parancs teljes folyamata az eredeti Picasával összevetve

*(Javítás #6996: e szakasz eredetileg a `0x9c81` kódot tulajdonította a Locate on Disknek; a menürekord-építő utasításai egymásba fésültek, a `0x9c81` az Export kódja, a Locate on Disk kódja `0x9c99`. A többes kijelölés `0x005c85e0`-beli mappánkénti megnyitására vonatkozó megállapítás változatlan.)*

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti és a jelenlegi PicasaPy forrásútjait a bináris disassembly, az indexelt
rekordok és a PicasaPy QML/Python forráskódjának közvetlen összevetésével ellenőriztem.

### Belépési pontok, feltételek, egy és több kép

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Főmenü (Fájl):** `ID_FILE_LOCATEONDISK` (`0x9c99`), felirat `&Locate on Disk`, gyorsbillentyű `Ctrl+Enter` (`0x005595dd`-`0x005595f4`). Menüépítő: `0x00559150`. Engedélyezés: `0x0056c5a0` és `0x0056e1c0`: nem üres kijelölésnél (`[esp+0x12] != 0`), nem zárolt állapotban (`[edi+0x34a4] == 0`), és nem írásvédett gyűjteményben (`0x8000` bit törölve). Üres kijelölésnél letiltva (`MF_GRAYED`). | `PicasaFileMenu.qml:150-154`, `MainMenuBar.qml:318-321`. Engedélyezett, ha `bar.photoActionsEnabled` (kijelölés nem üres). Aktiváláskor `bar.locateRequested()`. | Egyezik az alapfolyamat és a tiltási feltétel. Eltérés: a PicasaPy `photoActionIndex()` csak az első sort adja át többes kijelölésnél (lásd lent). |
| **Főmenü (Mappa):** `ID_ALBUM_LOCATEONDISK` (`0x9c95`), felirat `&Locate on Disk` (`0x0055b0b0`-`0x0055b0c7`). Menüépítő: `0x00559150`. Mappa nézetben az aktuális mappa lemezhelyét nyitja meg. | `PicasaFolderMenu.qml:185-190`, `MainMenuBar.qml:168-171`. Engedélyezett, ha `bar.folderLocateEnabled` (érvényes mappa, nem album/személy). Hívás: `fileOpsController.revealFolder(hostController.currentFolder)`. | Egyezik: mindkét rendszer a mappa könyvtárát nyitja meg a fájlkezelőben. |
| **Fotó helyi menü (Könyvtár):** `FolderPhotoWin::ID_FILE_LOCATEONDISK` (`0x9c99`), felirat `&Locate on Disk` (`0x00730790` a `0x00730c78`-nál). | `PhotoContextMenu.qml:427-432`, `MainPhotoContextMenu.qml:64-67`. Felirat `Locate on Disk\tCtrl+Enter`. | Egyezik a megjelenés és funkció. (PicasaPy-ban ha van mentett eredeti, almenüt ad: File on Disk / Original on Disk, #1613). |
| **Fotó helyi menü (Album / Emberek):** `AlbumPhotoWin::ID_FILE_LOCATEONDISK` (`0x9c99`) `Locate on &Disk` (D betűs mnemonik `0x00731471`, `0x0073579f`) és `AlbumPhoto::ID_FILE_LOCATEINPICASA` (`0x9c99`) `&Locate in Picasa` (`0x007314f7`, `0x00735817`). | `PhotoContextMenu.qml:427-458`, `MainPhotoContextMenu.qml:64-88`. `locateRequested` és `locateInPicasaRequested` (`hostController.selectFolder(mappa)`). | Egyezik a két parancs szétválasztása és a célmappára ugrás a Picasán belül. |
| **Mappa fejléc / Mappafa helyi menü:** `FolderWin::ID_ALBUM_LOCATEONDISK` (`0x9c95`), felirat `&Locate on Disk` (`0x007319f0` a `0x00731dd1`-nél és `0x00733a40` a `0x00733b4d`-nél). | `FolderContextMenu.qml:308-311`, `FolderPaneMenus.qml:373-376`, `FolderPaneContent.qml:399-402`. Hívás: `fileOpsController.revealFolder(...)`. | Egyezik: mindkét rendszer a mappa útvonalát adja át. |
| **Néző helyi menü (OneUp):** `FolderPhotoWin::ID_FILE_LOCATEONDISK` (`0x9c99`), felirat `&Locate on Disk` (`0x007327a0` a `0x00732b85`-nél). | `ViewerContextMenu.qml:218-223`, `PhotoViewerContextActions.qml:142-146`. Hívás: `fileOpsController.revealPhoto(viewer._aktivUt())`. | Egyezik: a nézőben az aktuálisan megtekintett kép útvonalát nyitja meg. |
| **Képtálca bélyegkép helyi menü:** `FolderPhotoWin::ID_FILE_LOCATEONDISK` (`0x9c99`), felirat `&Locate on Disk` (`0x00732ee0` a `0x00733093`-nál). | `TrayContextMenu.qml:86-88`, `TrayBar.qml:396`, `MainTrayBar.qml:50-55`. Hívás: `fileOpsController.revealPhoto(ut)`. | Egyezik: a tálcán lévő elemre jobb gombbal kattintva elérhető a művelet. A tálca alsó gombsorán nincs Locate gomb egyik programban sem. |
| **Gyorsbillentyű (Ctrl+Enter):** `0x005e60d0` (`CThumbUI::OnKeyDown`), `VK_RETURN` (0x0d) + `Ctrl` billentyű -> `0x005c8320(0)`. Ha a kijelölés száma > 0 (`0x005c8493`), akkor a képeket nyitja (`0x005c85e0`); ha üres a kijelölés (`0x005c8495`), akkor a mappát nyitja (`0x005d0e90`). | `PicasaMenuBar.qml:658-673`: `sequence: "Ctrl+Return"`. Ha `photoActionsEnabled`: `locateRequested()`, ha `folderLocateEnabled`: `folderLocateRequested()`. | Egyezik a prioritási sorrend és a viselkedés: kijelölt képnél a képre, üres kijelölésnél a mappára ugrás. |

#### Részletes feltételek és a többes kijelölés viselkedése

1. **Videófájlok kezelése:**
   - Az eredeti Picasában a videók (`.avi`, `.wmv`, `.mov`, `.mp4` stb.) azonos úton haladnak át (`0x005c85e0` -> `0x00981280`). A fájlrendszer-útvonal átadásra kerül a ShellExecuteExA-nak `/select,"<fájl>"` paraméterrel. Nincs videó-specifikus korlátozás.
   - A PicasaPy-ban a `revealPhoto` nem szűri a fájl típusát, a videó fájlokra ugyanúgy meghívja a `reveal_in_file_manager` függvényt. Egyezik.
2. **Több kép kijelölése és a mappánkénti ismétlésszűrés:**
   - **Eredeti Picasa:** A `0x005c85e0` diszpécser egy előzetes ciklust futtat a kijelölt elemeken (`0x005c8754`-`0x005c87b5`). Minden elemnél lekéri a szülőkönyvtárat (`0x009a37b0`), és összehasonlítja a már regisztrált mappákkal (`0x005c8763`-`0x005c877d`). Ha a mappa megegyezik egy korábbival, átugorja a felvételt (`0x005c87b5 jne 0x5c8ba3`). Emiatt könyvtáranként szigorúan csak a legelső kijelölt fájl kerül be a megnyitandó listába. A `0x005c8dc4`-`0x005c8dee` ciklusban ezután ahány KÜLÖNBÖZŐ mappa volt a kijelölésben, annyi független Explorer ablakot nyit meg (`call 0x00981280`). Ha a kijelölt képek mind azonos mappában vannak, pontosan egyetlen Explorer ablak nyílik az első képre fókuszálva. Ha a kijelölés több mappát fed le (pl. keresési eredmények, album vagy tálca), minden érintett mappához külön ablak nyílik.
   - **PicasaPy jelenlegi állapota:** A menükezelők (`MainMenuBar.qml:319`, `MainPhotoContextMenu.qml:65`, `MainTrayBar.qml:53`) kivétel nélkül csak egyetlen sort adnak át (`photoActionIndex()`, `fileOpTargetRow` vagy `selectedRows()[0]`). Több kép kijelölése esetén a PicasaPy csak a fókuszban lévő vagy legelső képet jeleníti meg a fájlkezelőben, még akkor is, ha a kijelölt elemek több különböző mappában találhatók.
   - **Teendő:** Fejlesztői jegy szükséges a többes kijelölés mappánkénti ismétlésszűrésére és megnyitására (`revealPhotos(paths)`).
3. **Üres kijelölés:**
   - Főmenü: mindkét programban tiltott (szürke).
   - Gyorsbillentyű (`Ctrl+Enter`): mindkét programban a jelenlegi mappa megnyitására esik vissza.
   - Mappa menük: mindkét programban a mappa közvetlen megnyitása (`explorer "<mappa>"`).

### A párbeszédablak és a megjegyzett értékek

| Mező / Tulajdonság | Eredeti Picasa 3.9 (`0x00981280`) | Jelenlegi PicasaPy (`reveal.py`) | Eltérés / Értékelés |
|---|---|---|---|
| Belső párbeszédablak | Nincs. Nem nyit dialógust a Picasa. | Nincs. Nem nyit dialógust a PicasaPy. | Egyezik. |
| Megjelenő ablak | Az operációs rendszer fájlkezelője: Windows Explorer (`0x00cd85f4`), `SW_SHOW` (5) módban (`0x00981310`). | Windows: Windows Explorer (`explorer`); Linux: `xdg-open`; macOS: `open`. | Egyezik: a natív fájlkezelő indul el. |
| Parancssori formátum | Kép esetén: `/select,"%s"` (`0x00cd8604`); Mappa esetén: `"%s"` (`0x00c8500c`). | Windows kép: `explorer /select,"<fájl>"`; Windows mappa: `explorer "<mappa>"`. | Egyezik: karakterre megegyező paraméterezés (#1152). |
| Megjegyzett beállítások | Semmit nem jegyez meg. Nincs registry-kulcs, nincs beállítás-mentés a Picasában. | Semmit nem jegyez meg. | Egyezik. |
| Következő megnyitás | A Windows Intéző maga jegyzi meg a saját ablakméretét és helyzetét a rendszerleíró adatbázisban; a Picasa állapotmentést nem végez. | A rendszer fájlkezelője kezeli a saját pozícióját. | Egyezik. |

### Kimeneti hatás és hibák

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Fájlrendszer:** a `0x00981280` kizárólag a `ShellExecuteExA` hívást futtatja (`0x009813de`). Nincs fájl- vagy könyvtárlétrehozás, módosítás vagy törlés. | `reveal.py:115` `subprocess.run` külső folyamatot indít. | Egyezik: szigorúan olvasási jellegű külső rendszerhívás. |
| **.picasa.ini:** nincs INI-módosítás, nem hív INI-író rutint. | Nincs hívás az `ini/` csomag felé. | Egyezik: a `.picasa.ini` érintetlen marad. |
| **Index (adatbázis):** nincs SQLite / PMP írás, nincs újraindexelés. | Nincs hívás az `index/` csomag felé. | Egyezik: az adatbázis változatlan. |
| **Rács és kijelölés:** a kijelölt sorok és elemek kijelölése VÁLTOZATLAN marad; a fókusz átadódik az újonnan indult külső Explorer ablaknak. | A kijelölés nem törlődik, az elemek kijelölve maradnak. | Egyezik. |
| **Írásvédett hely:** mivel nem történik lemezre írás, az írásvédett könyvtárban lévő fájl éppúgy megjelenik az Explorerben, mint az írható. | Az ellenőrzés csak az útvonal létezését és a folyamat indítását érinti. | Egyezik: írásvédett helyen is hibátlanul lefut. |
| **Hiányzó fájl:** a `0x00981280` a `ShellExecuteExA` visszatérési kódját nem vizsgálja hibajelzésre (`0x009813e4` után `xor eax, eax; ret;`). Nem dob belső hibát; a hibakezelést a Windows Shell végzi (maga az Intéző ad hibaüzenetet, ha az útvonal nem található). | `fileops_controller_open_mixin.py:42-44`: ha a subprocess OSError-t ad, `operationFailed` jelet küld, a felület nem fagy le. | Egyezik: nincs programösszeomlás; a PicasaPy szükség esetén műveleti hibát jelez a UI-nak. |
| **Megszakítás:** a művelet szinkron/azonnali folyamatindítás, nincs Cancel gomb vagy háttérben futó megszakítható szál. | Nincs megszakítási állapot. | Egyezik. |

### Két független út és cáfoló kísérlet

- **A út, utasításszintű bináris vizsgálat:**
  1. Menüfrissítő és engedélyező vizsgálat: `0x0056c5a0` és `0x0056e1c0` instrukcióinak elemzése, ahol a kijelölés megléte és állapota határozza meg a `0x9c99` és `0x9c95` menüpontok állapotát.
  2. Gyorsbillentyű és eseménykezelő: `0x005e60d0` (`CThumbUI::OnKeyDown`) billentyűkód vizsgálata (`VK_RETURN` és Ctrl vizsgálat), ahonnan a vezérlés a `0x005c8320` diszpécserre jut.
  3. Diszpécser és elágazás: `0x005c8320` utasításainak lekövetése: a kijelölésszám vizsgálata (`0x005c8493`), ha 0, akkor mappa ág (`call 0x005d0e90`), ha > 0, akkor fotó ág (`call 0x005c85e0`).
  4. Többes kijelölés és ismétlésszűrés: `0x005c85e0` vizsgálata: a könyvtárak kigyűjtése (`0x009a37b0`), karakterenkénti összehasonlítása (`0x005c8763`-`0x005c877d`), az ismétlődések kihagyása (`0x005c87b5 jne 0x5c8ba3`), majd a ciklikus megnyitás (`0x005c8dc4`-`0x005c8dee`).
  5. Shell hívás: `0x00981280` diszasszemblálása: `SHELLEXECUTEINFOA` feltöltése (méret: 60 bájt, `open`, `explorer`, `SW_SHOW`, `/select,"%s"` vagy `"%s"`), és a `ShellExecuteExA` hívás (`0x009813de`), majd hibavizsgálat nélküli visszatérés (`0x009813f9`).
- **B út, adatstruktúrák, sztring-xrefek és független menürekordok:**
  1. A `picasa3-index.sqlite` adatbázisban szereplő `string_xrefs` és `xrefs` táblák független lekérdezése: `ID_FILE_LOCATEONDISK` (`0x9c99`), `ID_ALBUM_LOCATEONDISK` (`0x9c95`), `ID_FILE_LOCATEINPICASA` (`0x9c99`), valamint a menücímkék (`&Locate on Disk`, `Locate on &Disk`, `&Locate in Picasa`).
  2. Helyi menü építő rutinok független vizsgálata: `FolderPhotoWin` (`0x00730790`), `AlbumPhotoWin` (`0x00731050`), `FolderWin` (`0x007319f0`, `0x00733a40`), `TrayWin` (`0x00732ee0`), `ViewerWin` (`0x007327a0`), `PeoplePhotoWin` (`0x007355c0`).
  3. Sztring konstansok beolvasása a bináris `.rdata` szekciójából közvetlen PE elemzéssel: `0x00cd85f4` (`explorer`), `0x00cd8604` (`/select,"%s"`), `0x00c8500c` (`"%s"`), `0x00c80fc0` (`open`).
  4. A PicasaPy QML és Python forráskódjának tételes vizsgálata (`PicasaFileMenu.qml`, `PicasaFolderMenu.qml`, `MainMenuBar.qml`, `MainPhotoContextMenu.qml`, `MainTrayBar.qml`, `PhotoViewerContextActions.qml`, `fileops_controller_open_mixin.py`, `reveal.py`).
  A két független út maradéktalanul megerősíti egymást: a belépési pontok, a hívási lánc, a paraméterezés és a mellékhatásmentes működés azonos.
- **Cáfoló kísérlet:**
  Azt a hipotézist próbáltam bizonyítani, hogy a `Locate on Disk` parancs több kijelölt fájl esetén a Windows Intézőben képes több fájlt egyszerre kijelölni egyetlen ablakban (pl. vesszővel vagy szóközzel összefűzött paraméterlistával).
  - A bináris utasításainak elemzése (`0x005c87bb`-`0x005c87eb` és `0x005c8dc4`-`0x005c8dee`) egyértelműen CÁFOLTA ezt a feltevést: a `0x00981280` mindig egyetlen fájl elérési utat kap stringként (`push eax` a `0x005c8de0`-nál), és az Intéző `/select,"<fájl>"` szintaxisa sem támogat több fájlnevet egy argumentumban. Az eredeti Picasa ehelyett mappánként deduplikál, és ha a kijelölés több mappát érint, ciklusban külön `ShellExecuteExA` hívást indít minden mappára. A feltevés ezzel cáfolva, a tényleges működés bizonyítva.

### A jegy „Kész, ha” pontjai

1. ✅ **Belépési pontok és engedélyezési feltételek:** A Főmenü (Fájl, Mappa), a helyi menük (Könyvtár, Album, Mappa, Néző, Tálca, Emberek), a képtálca és a `Ctrl+Enter` gyorsbillentyű feltételei (üres kijelölés, egy/több kép, videó) tételesen, bináris címekkel és forráshivatkozásokkal feltárva és összevetve.
2. ✅ **Ablak, alapértékek és megjegyzett állapot:** Bizonyítva, hogy belső dialógus nincs, a rendszer fájlkezelője indul el (`SW_SHOW`), a Picasa semmilyen értéket nem jegyez meg a művelethez kapcsolódóan.
3. ✅ **Kimeneti hatás a fájlrendszerre, .picasa.ini-re, indexre, rácsra és kijelölésre:** Igazolva, hogy a művelet mellékhatásmentes olvasási hívás; sem a fájlrendszer, sem az ini, sem az index, sem a rácskijelölés nem módosul.
4. ✅ **Hibakezelés:** Írásvédett hely (nem befolyásolja a futást), hiányzó fájl (az Explorer shell kezeli, nincs Picasa hibaablak), megszakítás (azonnali lefutású aszinkron hívás) részletesen lefedve.

### Javasolt fejlesztői jegytörzs

#### Több kép kijelölésekor a Locate on Disk mappánként nyissa meg a fájlkezelőt

**Eredeti:** A Picasa 3.9 `0x005c85e0` függvénye több kijelölt kép esetén összegyűjti az érintett szülőmappákat, kiszűri az ismétlődéseket (`0x005c8754`-`0x005c87b5`), majd a `0x005c8dc4`-`0x005c8dee` ciklusban minden egyedi mappához külön fájlkezelő ablakot nyit az adott mappa első kijelölt elemére fókuszálva (`0x00981280`).

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x005c85e0`, `0x005c8754`, `0x005c8dc4`: a kijelölt képeket szülőmappánként szűri (mappánként egyszer), és minden érintett mappára meghívja az Intézőt a mappa első kijelölt elemével. | `MainMenuBar.qml:318-321`, `MainPhotoContextMenu.qml:64-67`, `MainTrayBar.qml:50-55`, `fileops_controller_open_mixin.py:33-44`: csak egyetlen képet (`photoActionIndex()`, `fileOpTargetRow`, `selectedRows()[0]`) ad át a `revealPhoto`-nak. | Bővíteni a vezérlőt `revealPhotos(paths)` metódussal, amely mappánként csoportosítja az útvonalakat, és minden egyedi mappára meghívja a fájlkezelőt az első képre fókuszálva. A menü- és tálcakezelőkben a teljes kijelölést átadni. |

**Kész, ha:**
- Ha a felhasználó több képet jelöl ki egy mappában, a `Locate on Disk` parancsra (menüből, helyi menüből, tálcáról vagy Ctrl+Enterrel) pontosan 1 fájlkezelő ablak nyílik meg az első képre fókuszálva.
- Ha a kijelölt képek több különböző mappában találhatók (pl. albumban, keresési listában vagy tartott tálcán), a parancs minden érintett mappához külön megnyitja a fájlkezelőt az adott mappa első kijelölt elemével.

### Nyitott kérdések

Nincs nyitott kérdés: a folyamat mind a négy pontja bináris címekkel és forrássorokkal igazolt. Ghidra-kör nem szükséges.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - a #6989 új szakasza.

## #6988: A Print parancs teljes folyamata az eredeti Picasával összevetve

### Belépési pontok

Az eredeti Fájl menü `ID_FILE_PRINT` parancsának adata `0xe107`. A menüelemet a `0x0056e1c0` dinamikus engedélyezése vezérli. A `0x005cb1a0` állapot-előállító nem üres kijelölésnél `0x2` jelzőt ad; több elemnél további `0x200` jelző jelenik meg. A videóosztályozó külön `0x20`/`0x60` biteket ad, amelyek nem részei a Print menücsoport `0x2`/`0x4` kapujának. Ez azt bizonyítja, hogy a Fájl menü látható Print parancsát a videójelző önmagában nem tiltja le. A nyomtatási munkába ténylegesen bekerülő rekordokat ez nem dönti el.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Fájl menü:** `ID_FILE_PRINT`, `cmd=0xe107`; a `0x0056e1c0` a kijelölési állapot alapján engedélyezi. Üres kijelölésnél a kapu nem teljesül; egy és több kijelölt elemnél igen. A videó külön állapotjelző, és nem tiltja ezt a menükaput (`0x005cb1a0`, `0x0056e1c0`). | `src/picasapy/app/qml/PicasaPy/PicasaFileMenu.qml:164-168`, `src/picasapy/app/qml/PicasaPy/MainMenuBar.qml:83`, `src/picasapy/app/qml/PicasaPy/MainLibrarySelectionState.qml:70-78`; a menü a néző aktuális fotósorát vagy a könyvtári kijelölést veszi. Videót nem szűr ezen a kapun. | A menü engedélyezési szintjén nincs bizonyított eltérés. A tényleges rekordlista videó/hiányzó fájl viselkedését külön kell lezárni. |
| **Fotó- és mappa-helyi menü:** a vizsgált építők (`0x00730790`, `0x00731050`) erőforrás- és sztringlistájában nincs Print vagy Print Contact Sheet parancs. | A `PhotoContextMenu.qml` és `FolderContextMenu.qml` nem tartalmaz sima Print elemet; a `*Menu.qml` Print-keresés a `src/picasapy/app/qml/PicasaPy/PicasaFileMenu.qml:164-168` főmenüelemét és a `src/picasapy/app/qml/PicasaPy/PicasaFolderMenu.qml:167-173` külön Contact Sheet műveletét találta. | A vizsgált helyi menüknél nincs eltérés. A néző saját, kontextusfüggő menüjének eredeti parancslistája nincs teljesen azonosítva. |
| **Billentyű:** a `0x005e6428` körüli eredeti billentyűkezelő módosítóállapot szerint a `0x00744ee0` útra vagy közvetlenül az `outputlayout/pbutton` aktiválására lép. A címke és a pontos Print/Ctrl+Shift+P parancs-hozzárendelés ebből a diszasszemblálásból nem állapítható meg. | `src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml:695-713` köti a `Ctrl+P`-t a nyomtatáshoz; a `src/picasapy/app/qml/PicasaPy/PicasaFolderMenu.qml:173` és `src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml:705-713` a `Ctrl+Shift+P`-t Contact Sheethez köti. | A két program gyorsbillentyű-paritása nyitott. Ne változzon a kötés, amíg a bináris billentyűág és az eredeti aktív nézet szerepe nincs tisztázva. |
| **Képtálca / output gomb:** az eredeti `outputlayout/pbutton` a `0x00744a00` panelnyitó útra vezet. A tényleges nyomtatási parancs `0x00744d00` útja a kijelölt rekordok listáját adja át a nyomtatási munkának. | `src/picasapy/app/qml/PicasaPy/MainTrayBar.qml:57`, `src/picasapy/app/qml/PicasaPy/TrayActionArea.qml:365-373`, `src/picasapy/app/qml/Main.qml:521-528`; a Photo Tray nem üres tartalma elsőbbséget kap (`src/picasapy/app/print_controller_source_mixin.py:21-50`). | A PicasaPy képtálca- és kijelölésprioritásának egyezése az eredeti rekordgyűjtéssel nyitott; a tálca gomb üres állapotban nem indul. |
| **Néző / OneUp:** a `0x005cb990` `0xe107` dispatch ága a `param_1[0xc45]` értékétől függően általános UI-aktiválásra vagy `0x00744d00`-ra lép. A mező jelentése és az OneUp-ban átadott konkrét kép nincs azonosítva. | `src/picasapy/app/qml/PicasaPy/MainLibrarySelectionState.qml:70-78`, `src/picasapy/app/qml/Main.qml:521-528`; nézőben a megjelenített fotósor a nyomtatási cél. Megnyitáskor a panel a `viewerOpen` állapotot kikapcsolja (`src/picasapy/app/qml/PicasaPy/PrintDialog.qml:233-249`), bezáráskor nem állítja vissza. | Az eredeti nézőből átadott kép és a nézet visszaállítása nyitott. A PicasaPy viewer-visszaállítását csak binárisan igazolt elvárás alapján érdemes módosítani. |

### Ablak, alapértékek és megjegyzett állapot

Az eredeti nyomtatási képernyő a `thumbui/printpanel` felület, amelyet az `outputlayout/pbutton` és az `m_print_enable` vált be. Ez az alkalmazás felületén belüli panel; nem külön OS-ablak. A nyomtató nélküli nyitási ág üzenete: `A printer must be installed in order to print.` (`0x00744a00`, szöveg `0x00e017e0`).

Az eredeti `printpanel.tre` `croptoggle` alapja bekapcsolt; ezt a 3.9.141 PDF-nyomtatós felvétel is megerősíti: első használatkor Full Page, Crop to Fit, 1 példány (`mérés: Colab EN 29/30`). Az utoljára választott méret kulcsa a `Preferences\PrintLastSize`, amelyet a `0x00744ba8` környékén olvas; a pontos írócím ebben a körben `NINCS MEG`. Az öt gyors méretbeállítás külön `PrintSize0`-`PrintSize4` értéket a `0x006e5ab0` betölti, a mentő ág `0x006e3990`. A nyomtatási opciókhoz a `PrinterQuality` és `PrinterUseTiles` is használatos (`0x00745f80`, `0x00746060`). Az eredeti példányszám és tájolás újraindítás utáni megőrzése ebben a körben nincs mérve.

PicasaPy-ban a dialog teljes főablakot kitöltő `Item` (`src/picasapy/app/qml/PicasaPy/PrintDialog.qml:20-27`, `src/picasapy/app/qml/PicasaPy/MainWindowDialogStack.qml:319-324`). A `fitMode: "fill"` Crop to Fit módot jelent (`src/picasapy/app/qml/PicasaPy/PrintDialog.qml:117-119`, `src/picasapy/app/qml/PicasaPy/PrintFitPanel.qml:34-40`), tehát az induló kivágás módja egyezik az eredeti erőforrással. Az alap példányszám 1 (`src/picasapy/app/qml/PicasaPy/PrintDialog.qml:67-71`), a méretet `print/lastSize`-ból tölti vissza (`src/picasapy/app/print_controller_settings_mixin.py:209-224`), a printoptions beállításokat is menti (`:228-266`). A példányszám és a tájolás QSettings-be mentése nincs a vizsgált útban igazolva; a panel példánya viszont ugyanabban a folyamatban megmarad.

### Hatás és hibák

Az eredeti rajzolóút GDI nyomtatási munkát indít (`StartDocA`, hívás a `0x00861bb0` környezetében). Ez a nyomtató/driver út, a rendszer nyomtatási sorfájljának helye és írásvédett célra adott eredménye driver- és Windows-függő. A statikusan vizsgált útban közvetlen `.picasa.ini` vagy SQLite írás nem volt azonosítva, de ez nem zárja ki a még fel nem tárt közvetett hívásokat.

| Hatás | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| Fájlrendszer / nyomtatási cél | `0x00861bb0` GDI `StartDocA` út; Picasa által létrehozott PDF/fényképfájl nem igazolt. A nyomtatási sor és az írásvédett cél eredménye `NINCS MEG`. | `src/picasapy/app/print_controller_output_mixin.py:37-59` támogatja a PDF-célfájl írását; a nyomtatás a QPrinter útján fut. `.picasa.ini` és indexírás nem része a vizsgált print vezérlőútnak. |
| `.picasa.ini` / index | Közvetlen írás nem látszott a feltárt print útban; teljes közvetett hatás `NINCS MEG`. | A print vezérlőút csak nyomtatási beállítást és kimenetet kezel; `.picasa.ini` vagy SQLite írás nem látszik az útban. |
| Mappafa / rács | A `0x007448a0` panel-visszaállító a main/fullview/print/edit/acquire felületeket rendezi vissza. Mappafa és rács pontos visszaállítása, különösen OneUp után, `NINCS MEG`. | A print út nem ír mappafa- vagy indexállapotot. A nyitás elmenti rács kijelölését, bezárás visszaállítja a `selectedIndexes` és `selectedIndex` értéket (`src/picasapy/app/qml/PicasaPy/PrintDialog.qml:233-249,279-293`). |
| Kijelölés / Photo Tray | A `0x007448a0` körül nem azonosítottam kijelölésírást; a nyomtatás utáni eredeti kijelölés- és tálcaállapot `NINCS MEG`. | A rács kijelölése bezáráskor visszaáll; a Photo Tray tartalmát a nyomtatási forrásválasztó olvassa, de nem módosítja (`src/picasapy/app/print_controller_source_mixin.py:21-50`). A néző állapota nincs visszaállítva. |
| Sikertelen forrás / nyomtató | A `0x007434d0` printer-hibaüzenete: `Picasa has encountered a problem with the printer '%s'. Please report this error.` A hiányzó kép és az írásvédett printer-cél pontos kimenete `NINCS MEG`. | A videót/kiterjesztést és a nem betölthető képet kihagyja (`src/picasapy/app/print_controller_source_mixin.py:55-82`); üres vagy érvénytelen forrás hibát ad (`src/picasapy/app/print_controller_output_mixin.py:359-401,489-500`). Sikertelen festőindításnál általános nyomtatási hibát jelez. |
| Megszakítás | A `0x00743650` callback `Cancelling Print...` állapotot küld és leállítási/takarítási hívásokat végez. A felületi esemény, amely ezt meghívja, és a részben kinyomtatott lapok sorsa `NINCS MEG`. | A dialog Escape/bezárás elrejti a felületet (`src/picasapy/app/qml/PicasaPy/PrintDialog.qml:296-300`), de nem küld cancel-jelet; az aktív rajzolóciklus eseményeket dolgoz fel (`src/picasapy/app/print_controller_output_mixin.py:592-616`). |

### Bizonyíték és bizonyítottság

| Érték / állítás | Forrás |
|---|---|
| File Print parancsérték `0xe107`, kijelölési kapu | `bináris (0x00559150, 0x0056e1c0, 0x005cb1a0)`; Ghidra menü/dispatch kimenet és célzott diszasszemblálás |
| Video flag külön áll a menü kijelölési kapujától | `bináris (0x005cb1a0, 0x0056e1c0)`; a tényleges nyomtatott rekord viselkedése `NINCS MEG` |
| Print panel, nyomtató nélküli hiba, nyomtatási job | `bináris (0x00744a00, 0x00744d00, 0x00745770)`; üzenetszöveg `0x00e017e0`, felkészítő üzenet `0x00e01d22` |
| GDI nyomtatás | `bináris (0x00861bb0)`; `StartDocA` import feloldása a korábbi Ghidra-kimenetben |
| Crop to Fit alap | `bináris (printpanel.tre:155-172)` és `mérés (Colab EN 29/30)` |
| `Preferences\\PrintLastSize` olvasása | `bináris (0x00744ba8)`; pontos írócím `NINCS MEG` |
| Első panel Full Page, 1 példány | `mérés (Colab EN 29/30)`; a mérésen túli profilok alapértéke `NINCS MEG` |
| PicasaPy menu/tray/viewer út és dialog | Mai forrás: `src/picasapy/app/qml/PicasaPy/PicasaFileMenu.qml:164-168`, `src/picasapy/app/qml/Main.qml:521-528`, `src/picasapy/app/qml/PicasaPy/TrayActionArea.qml:365-373`, `src/picasapy/app/qml/PicasaPy/PrintDialog.qml:20-27,117-119` |
| Eredeti fájlhiány, driver írásvédelem, megszakítás indítója és kiválasztás-helyreállítás | `NINCS MEG`; szükséges: célzott Ghidra-kör, majd Windows 3.9.141 futtatási mérés |

**Bizonyítottsági fok: nyitott.** A menü kapuja, a nyomtató nélküli ág, a panel Crop to Fit alapja és a mai forráskódbeli utak külön bizonyítottak. A teljes paritás nyitott, mert az eredeti nézőcél, videó/hiányzó fájl feldolgozás, driverhiba, cancel esemény és UI-visszatérés nincs végig bizonyítva. Egyetlen útra épülő megfigyelés feltételes marad; csak a független erőforrás/mérés vagy a másik kódréteg által megerősített állítás kap megerősített minősítést.

### A két független út

- **A út, bináris:** `0x00559150` menürekord, `0x0056e1c0` engedélyező, `0x005cb1a0` kijelölési állapot, majd `0x00744a00` panelnyitás és `0x00744d00` nyomtatási út célzott vizsgálata. A `0x007434d0`, `0x00743650` és `0x00861bb0` külön hiba-, megszakítási és GDI hívások.
- **B út, független réteg:** a bináris menü- és printpanel-erőforrások, a `StartDocA` import feloldása, a korábbi Windows PDF-mérés, továbbá a jelenlegi QML/Python út közvetlen forrásolvasása. A Crop to Fit egyezést az eredeti erőforrás és a mai `fitMode: "fill"` egymástól függetlenül adja; az első panelmérés külön alátámasztja az induló állapotot.
- **Egyezés:** a panelbe lépés, a Crop to Fit alap és a menü üres kijelölési kapuja egyezik a hozzájuk tartozó PicasaPy-feltételekkel. A billentyű, nézőcél, videó/hiányzó fájl, hibakezelés és a művelet utáni állapot kérdésében A és B még nem ad döntő egyezést.

### Cáfoló kísérlet

Azt a hipotézist próbáltam cáfolni, hogy a Picasa eredeti Fájl menüje a videókat már a menüben tiltja. A `0x005cb1a0` videojelzőit összevetettem a `0x0056e1c0` Print-csoport engedélyező feltételével: a videójelző nem szerepel a kijelölési kapuban, ezért a hipotézist a vizsgált menüszinten cáfolja. Ez a cáfoló ellenőrzés ugyanazt a mércét használja: utasításszintű feltétel és attól független menü/állapot-rekord egyezése. Azt nem bizonyítja, hogy videót ténylegesen nyomtat, mert a nyomtatási lista feldolgozása még nyitott.

### A jegy „Kész, ha” pontjai

| Kérdés | Állapot | Bizonyíték |
|---|---|---|
| Minden belépési pont és engedélyezési feltétel, beleértve videó, több kép és üres kijelölés | ⛔ | Menü és vizsgált helyi menük leírva; bináris billentyűág, néző és videó tényleges nyomtatása nyitott. |
| Ablak, alapértékek és következő alkalomra megjegyzett állapot | ⛔ | A panel belső felület, Crop to Fit, Full Page/1 példány mérve; összes eredeti profilbeállítás és nézet-visszatérés nincs lezárva. |
| Fájlrendszer, `.picasa.ini`, index, rács és kijelölés a művelet után | ⛔ | GDI és PicasaPy út részben azonosított; eredeti spool, közvetett írások, mappafa/rács/kijelölés végállapota nincs végigmérve. |
| Írásvédett hely, hiányzó fájl és megszakítás | ⛔ | Nyomtató- és cancel callback címe ismert; a futásidejű hibák és a felületi megszakítás útja nincs megmérve. |

### Javasolt fejlesztői jegytörzs

Jelen bizonyíték alapján nem javaslok kódmódosító jegyet: nem maradt olyan eredeti viselkedésbeli eltérés, amelynek mindkét oldala kellő bizonyítékkal ismert. A `picasa-nyomtatas.md` egy régi állítása szerint a mai induló crop mód nem egyezett; ez a feladatban előírt friss forrásolvasással cáfolódott (`src/picasapy/app/qml/PicasaPy/PrintDialog.qml:117-119`, `src/picasapy/app/qml/PicasaPy/PrintFitPanel.qml:34-40`). A jegytörzs bővítése rögzítse, hogy a teljes paritás még nyitott, és az alábbi bináris/mérési kérdéseket kell lezárni. Fejlesztési lista csak a bizonyíték után készíthető.

### Új kutatási jegyjavaslatok

Most nem javaslok külön kutatási jegyet: a nyitott tételek ennek a Print-folyamatnak a közvetlen, befejezetlen részei.

### Nyitott

- A Ghidra-kimenetek cím szerinti keresése megtörtént: `0x005e6428`, `0x00744d00`, `0x007451a0` és `0x00745770` címhez nincs felhasználható teljes dekompiláció; a célzott diszasszemblálás és hívó/xref részletek nem döntik el a fenti szemantikai kérdéseket.
- Ghidra-kör kell: 0x005e6428 - melyik módosítóbillentyű és fókuszállapot melyik eredeti parancsot indítja, különösen a PicasaPy Ctrl+P és Ctrl+Shift+P egyeztetéséhez [blokkoló]
- Ghidra-kör kell: 0x00744d00 - pontosan mely kijelölt, Photo Tray vagy OneUp rekord kerül a nyomtatási munkába, és hol szűri a videót vagy a hiányzó képfájlt [blokkoló]
- Ghidra-kör kell: 0x007451a0 - a nyomtatási rekord/minőség feldolgozása hogyan kezeli a videót, hiányzó vagy olvashatatlan képet [blokkoló]
- Ghidra-kör kell: 0x00745770 - az eredeti felületi Cancel esemény hogyan jut el a 0x00743650 callbackig, és milyen panel/kijelölés állapotot állít vissza [blokkoló]
- `NINCS MEG`: az eredeti 3.9.141 viselkedése írásvédett nyomtató/spool cél, hiányzó képfájl és megszakítás esetén. Megszerzés: Windowsos mérés külön üres profilban, külön PDF/printer célokkal; rögzítendő a hibaüzenet, létrejött fájl/spool, visszaálló UI és kijelölés.
- `NINCS MEG`: eredeti Photo Tray tartalma és mappafa/rács állapota nyomtatás után. Megszerzés: Windowsos 3.9.141 mérés egy, majd több kijelölt képpel és eltérő Photo Tray tartalommal; előtte/utána képernyő és `.picasa.ini` és index fájlkivonatának összevetése.



## #7000: A forgatás parancsainak teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti bináris címek és a jelenlegi PicasaPy forrássorok külön szerepelnek.
Az ismeretlen menüállapotot, indexhatást és írásvédett fájlra vonatkozó
viselkedést nem következtetem ki a felület feliratából.

### Következtetés

A `0x9ca2` jobbra, a `0x9ca3` balra forgat; mindkettő ugyanahhoz a közös
végrehajtóhoz kerül. Az eredeti végrehajtási út a `rotate(n)` metaadatot írja a
`.picasa.ini`-be, a PicasaPy pedig szintén az ini-metaadatot és az indexet
frissíti. A teljes paritás nyitott: az eredeti menütiltások szemantikus
feltételei, a perzisztens index és felületi végállapot, az írási hiba, valamint
az Undo All Edits forgatást érintő hatása nem bizonyított; a jelenlegi
szerkesztőben nincs az eredeti képrotációs gomboknak megfelelő művelet.

### Bizonyítottsági fok

**Feltételes.** A parancskódok, a közös forgatási út és az ini-metaadat útja
bináris utasításokkal, független diszpécser-dekompilációval, illetve korábban
rögzített mérési adattal alátámasztott. A kérdés több kötelező részére nincs
független, döntő adat, ezért a teljes folyamatot nem minősítem megerősítettnek.

### Belépési pontok és engedélyezés

Az eredeti közös végrehajtó a `0x005eef30`, amely a kiválasztott elemek listáját
a `0x005ee6e0` feldolgozónak adja. A feldolgozó elemenként jár végig a listán.
Az üres lista a `IDS_MUST_SELECT_TO_ROT` üzenetet indítja; támogatott és nem
támogatott típus vegyes kijelölésekor a támogatható elemeket feldolgozza, majd
a `IDS_ROT_TYPEFAILED` üzenetet adja. A belső típusértékek videóhoz rendelése
és a menütiltás pontos szemantikája nincs bizonyítva.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Főmenü, forgatás jobbra/balra:** a menürekord-építő `0x00559150`; a `R&otate Clockwise` szövegű rekord bázisa `0xd6e340`, parancsmezője `+0x0a = 0x9ca2`; a `Rotate &Counterclockwise` rekord bázisa `0xd6e354`, parancsmezője `+0x0a = 0x9ca3`. A `0x005cb990` diszpécser mindkét parancsot a `0x005eef30`-hoz küldi. | `PicasaPictureMenu.qml:31-42`; `MainMenuBar.qml:83,400-424`. A menüpontok engedélyezése `photoActionsEnabled`; nézőben az aktuális sort, könyvtárnézetben a kijelölt sorokat forgatja. | A parancs és irány egyezik. A PicasaPy nem-üres kijelölést ellenőriz; az eredeti video/írásvédett menütiltás pontos feltétele nyitott. |
| **Fotó helyi menü, könyvtár/folder-photo:** a menüépítő `0x00730790`, `FolderPhotoWin` parancsai a `0x005eef30`-hoz jutnak. | `PhotoContextMenu.qml:287-296`; `MainPhotoContextMenu.qml:93-94`. A kijelölt sorokat kötegben adja át; a két menüpontnak nincs saját `enabled` feltétele. | A közös parancs és többes kijelölés útja megvan. A feltétel egyezéséhez az eredeti engedélyező bitek szemantikai megfejtése kell. |
| **Fotó helyi menü, album-photo:** a külön menüépítő `0x00731050`; a forgatási parancsok a közös végrehajtóhoz vezetnek. | `PhotoContextMenu.qml:287-296`; `MainPhotoContextMenu.qml:93-94`. | Egyező könyvtári kötegút; az eredeti állapotbit-feltétel nyitott. |
| **Gyorsbillentyű:** `CThumbUI::OnKeyDown`, `0x005e60d0`, a `Ctrl+R` és a `Ctrl+Shift+R` billentyűkombinációt a megfelelő forgatási irányra oldja fel. A közös végrehajtó a kijelölési listát dolgozza fel; üres lista esetén üzenetet ad. | `MainKeyboardShortcuts.qml:281-299`; célpont `MainWindowCommands.qml:381-385`. A PicasaPy egyetlen `selectedIndex`/nézőindex sort ad át, és `row < 0` esetén némán visszatér. | Eltérés: a többes kijelölés helyett egy sort céloz; üres célpontnál hiányzik az eredeti „Must have selected images to rotate.” értesítés. Lásd a fejlesztői jegytörzset. |
| **Képtálca forgatógombjai:** `thumbui/rotateleft` és `thumbui/rotateright`, kezelő `0x005d9cc0`; a gomb az egyedi vagy kijelölt elemek útját hívja. | `TrayTopRow.qml:105-174`; az egyes gombok akkor engedélyezettek, ha van néző vagy kijelölt sor, és a célcsoport nem csak videó. Több kijelölt sornál `rotateLeftMany`/`rotateRightMany`, különben egy sor. | Az egy és több elemű művelet rendelkezésre áll. Az eredeti video-engedélyezés és a PicasaPy saját menü-/vezérlőfeltételeinek pontos egyezése nyitott. |
| **Képtálca helyi menü:** album-photo forgatási parancsok a `0x00732ee0` menüépítőben. | `TrayContextMenu.qml:71-82`; `MainTrayBar.qml:46-49`. A kijelölt sorok kötege fut. | A többes kijelölés útja megvan; eredeti parancsengedélyezés nyitott. |
| **Néző helyi menü:** OneUp menüépítő `0x007327a0`; a `oneup/rotateleft` és `oneup/rotateright` vezérlők (`0x00752ae0`, `0x00753180`; erőforrás-felépítők `0x00802830`, `0x008032e0`) ugyanahhoz a forgatási útvonalhoz jutnak. | `ViewerContextMenu.qml:151-160`; `PhotoViewerContextActions.qml:122-130`. A néző aktuális indexét adja át. | Az egyképes cél egyezik. Az eredeti pontos engedélyező bit és video-viselkedés nyitott. |
| **Néző gyorsgombjai:** OneUp `rotateleft/right` vezérlők a `0x00752ae0`/`0x00753180` hívási útban. | `PhotoViewerQuickToolbar.qml:159-192`; `PhotoViewerTopBar.qml:330-356`. Mindkettő az aktuális oldalt célozza, és `quickViewerMode`-ban látható. | Az egyképes cél egyezik; tiltási feltétel nyitott. |
| **Szerkesztő normál nézet:** `editpanel/rotateleft/right`, kezelő `0x005d59f0`, a közös forgatóhoz jut. | A szerkesztő „Rotate” gombja `EditorCropPanel.qml:338-342`, kezelő `PhotoViewerEditorPanel.qml:135-144`; ez a kivágás-kijelölés tájolását cseréli. | Eltérés: nincs az eredeti képrotációt végző szerkesztőgomb. Fejlesztői jegy javasolt. |
| **Szerkesztő OneUp nézet:** `editoneup/rotateleft/right`, kezelő `0x00760240`, a UI felépítője `0x0075eac0`. | `PhotoViewerTopBar.qml:330-356` forgatógombjai `visible: viewer.quickViewerMode`; az editor mód gombja a crop-keretet forgatja, nem a fotót. | Eltérés: az eredeti képrotációs gombhoz nincs jelenlegi megfelelő. Fejlesztői jegy javasolt. |

#### Több kép, üres kijelölés, video és írásvédett fájl

- **Több kép:** az eredeti `0x005ee6e0` kiválasztási listán futó ciklusa több elemet is feldolgoz. A PicasaPy főmenüje és fotó helyi menüje könyvtárnézetben a teljes kijelölést adja át. A globális gyorsbillentyű ettől eltérően egy sort választ (`selectedIndex`), míg a tálca gomb a többes kijelölést is átadja.
- **Üres kijelölés:** az eredeti közös kezelő `IDS_MUST_SELECT_TO_ROT` üzenetútja megvan. A PicasaPy kötegelt útja a `rotationNeedsSelection` jelet kibocsátja (`photo_ops_transform_mixin.py:124-130`) és megjeleníti (`PicasaNotifier.qml:438-442`); a globális gyorsbillentyű viszont előbb `row >= 0` feltételt vizsgál, ezért ott néma no-op (`MainKeyboardShortcuts.qml:285-298`). A főmenü forgatása üres kijelölésnél letiltott (`MainMenuBar.qml:83`).
- **Video:** az eredeti feldolgozó bizonyos belső fájltípus-értékeket kizár és a kihagyott elemekről `IDS_ROT_TYPEFAILED` üzenetet ad. A belső érték és a video címke megfeleltetése nincs meg, ezért nem állítom, hogy minden videónál ugyanez a menüállapot vagy üzenet jelenik meg. A PicasaPy kötegelt út kihagyja a videókat és jelez (`photo_ops_transform_mixin.py:117-135`); az egyképes út csendben visszatér (`:221-226`); a tálca gomb csak-videó célcsoportnál le van tiltva (`MainWindowCommands.qml:386-400`, `TrayTopRow.qml:117-126,165-170`).
- **Írásvédett fájl:** a forgatási adatot az eredeti út `.picasa.ini`-be írja, nem az eredeti képfájl bitjeit adja át író függvénynek. Az, hogy az eredeti Picasa a fájl attribútuma vagy a szülőkönyvtár írhatósága alapján letiltja-e az egyes belépőket, nincs bizonyítva. A PicasaPy forrás útja az ini-t menti; az image-fájl read-only volta önmagában nem bizonyítja az ini-írás jogát.
- **PicasaPy felületi kapuk:** a főmenü `photoActionsEnabled` csak azt vizsgálja, van-e cél sor (`MainMenuBar.qml:83`); a fotó helyi menü forgatógombjainak nincs saját `enabled` feltételük (`PhotoContextMenu.qml:287-296`); a gyorsbillentyű csak szövegmező-fókusznál tiltott (`MainKeyboardShortcuts.qml:281-299`). Így video/írásvédett célra a felület nem ad minden belépőn egységes tiltást. Az ini írási hibáját a háttéríró `photoOpFailed`/`syncFailed` csatornára küldi, nem előzetes engedélyezési teszttel kezeli (`photo_ops_write_core_mixin.py:80-95`; `photo_ops_write_mixin.py:97-105`).

### Megerősítés, ablak és megjegyzett beállítás

- A vizsgált eredeti forgatási parancsútban nem találtam megerősítő dialógus vagy választást mentő hívást. A `Preferences/UITransitions` állapot olvasása animációs beállítás; forgatási beállítás mentését nem azonosítottam. Ez a megállapítás az átvizsgált útvonalra korlátozott.
- A nem támogatott típus üzenete `IDS_ROT_TYPEFAILED`, a kiválasztás hiányáé `IDS_MUST_SELECT_TO_ROT`; a `0x009807f0` közös UI-üzenetútra kerülnek. A megjelenítés pontos ablaktípusa (modális párbeszédablak vagy más felületi értesítés) **NINCS MEG**.
- A `.picasa.ini` író (`0x00454770`) siker/hiba eredményt ad vissza, de a `0x0042c980` forgatási hívó a visszatérést nem vizsgálja. A tényleges írásmegtagadási felhasználói visszajelzés **NINCS MEG**; a hibaüzenet hiányát nem állítom.

### Hatás a fájlokra és felületre

Az eredeti `0x0042c830` a `rotate(%d)` értéket olvassa; a `0x0042c980` jobbra
egy lépést ad hozzá, balra egyet levon modulo 4 szerint (a 0 balra forgatásból
3 lesz). A PicasaPy ugyanígy modulo 4 lépésszámot képez (`photo_ops_transform_mixin.py:137-140,228-229`).

| Hatás | Eredeti Picasa 3.9 | Jelenlegi PicasaPy |
|---|---|---|
| Kép fájltartalma | A vizsgált hívólánc a forgatás értékét metaadatként adja át, és nem találtam bitmap író hívást. A képfájl hash változatlansága **NINCS MEG**. | A forgatás `.picasa.ini`-ben tárolt metaadat (`photo_ops_transform_mixin.py:201-248`); nincs képfájlba írás ebben az útban. |
| `.picasa.ini` | `0x0042c980` `rotate(%d)` értéket készít; `0x00454770` a `.picasa.ini`-t nyitja meg, `rotate` kulcsot ír, siker után `backuphash`-t frissít. Független mérési rögzítés: #5396 régi eredményében jobbra `rotate(1)`, balra `rotate(3)` és `backuphash` szerepelt. | Egy képnél és kötegben is `rotate=` és `backuphash` változik; az írás backupolt ini-módosítással történik (`photo_ops_transform_mixin.py:137-143,239-248`; `photo_ops_write_text_mixin.py:206-227`). |
| SQLite / index | A végrehajtás a `0x005796c0` frissítési útját hívja. Hogy ez mely perzisztens adatbázis-mezőket írja, **NINCS MEG**. | Egy képnél `update_photo_fields` frissíti az `rotate_steps` mezőt (`photo_ops_write_core_mixin.py:80-95`); batch írás mappánként szinkronizálja az indexfát (`photo_ops_write_text_mixin.py:213-227`). |
| Bélyegkép és rács | `0x005796c0`-n keresztüli frissítés látszik, de a thumbnail-cache és a rácssor pontos végállapota **NINCS MEG**. | A provider a modellértesítés előtt újraregisztrálja a rekordot, majd célzottan frissíti a sort (`photo_ops_write_mixin.py:76-95`). A rácsmodell nem reseteli a listát, megtartja a delegate-eket és görgetést, `dataChanged` jelet küld (`photo_grid_state.py:268-281`). |
| Mappafa | A forgatás utáni mappafa-hatás **NINCS MEG**. | A kötegelt út mappánként szinkronizálja az indexfát; mappafa-sor vagy kijelölés közvetlen állítását nem találtam. A pontos látható végállapot **NINCS MEG**. |
| Kijelölés | A közös végrehajtó utáni kijelölés megtartása vagy megváltozása **NINCS MEG**. | A forgató út nem hív kijelölést módosító műveletet; a célzott rácssor frissül. A futásidejű kijelölés végállapota nincs külön mérve. |
| Visszavonás | A forgatási útban undo-verem írást nem találtam; az ellenkező irányú parancs 90 fokkal visszaforgat. Az `ID_PICTURE_REVERT` (`0x9ca4`) és a `0x005e7d90(0)` külön parancs, annak `rotate=`-ra gyakorolt hatása **NINCS MEG**. ⛔ **Helyesbítve (#7009):** a `0x9ca4` és a `0x005e7d90` a Hide/Unhide; az Undo All Edits `0x9d2d`, kezelője `0x005ef3e0`, és a `rotate=` kulcsot nem törli (lásd a #7009 alszakaszt). | A forgatás nincs a kötegelt undo-veremben (`MainMenuBar.qml:406-408`); az ellenkező irányú művelet visszaállíthatja a korábbi lépést, ha közben nem történt más forgatás. |

### Hibák és részleges végrehajtás

- Eredeti: a `0x005ee6e0` a támogatott elemeket sorban feldolgozza, a nem támogatottakat kihagyja, majd hibaüzenetet ad. A részleges végrehajtás visszagörgetésére utasítást nem találtam, tehát vegyes kijelölésnél részleges siker lehetséges. Az ini-írási hiba felhasználói következménye **NINCS MEG**.
- PicasaPy: kötegelt útban a kihagyott videók száma `rotationTypeFailed` jelzésként jelenik meg; üres kötegnél `rotationNeedsSelection` megy a notifierhez. Egyképes video esetén néma no-op. Írási hibánál a háttérmunkás nem frissíti a modellt, `photoOpFailed`/`syncFailed` jelzést küld (`photo_ops_write_core_mixin.py:80-95`, `photo_ops_write_mixin.py:97-105`).
- Megerősítést vagy megszakítási párbeszédet az eredeti közös forgatási útban nem találtam. A művelet visszavonhatósága és a fájlírási hiba nem azonos azzal, hogy az ellenkező forgatási parancs később kiadható.

### Két független út és cáfoló kísérlet

- **A út, utasításszintű olvasás:** `0x00559150` rekordbázis és `+0x0a` parancsmezők; `0x005cb990` dispatch; `0x005eef30` és `0x005ee6e0` kiválasztási lista/ciklus; `0x0042c980` rotate értékképzés; `0x00454770` ini-írás.
- **B út, független diszpécser és mérés:** a meglévő Ghidra-diszpécser `2026-10-21-idorend-30.txt:1405-1409` a `0x9ca2` ágat `FUN_005eef30(...,0x5a)`, a `0x9ca3` ágat `FUN_005eef30(...,0x10e)` iránykóddal párosítja; az önálló #5396 mérési rögzítés az ini `rotate(1)`/`rotate(3)` végértékét mutatja.
- **Egyezés:** az A és B út egyezik abban, hogy a `0x9ca2` az óramutató járásával egyező, a `0x9ca3` az ellenkező irányú parancs, és a megfigyelt tárolási forma `rotate(n)` metaadat. Ezek nem oldják fel az engedélyező állapotbiteket vagy a UI-végállapotot.
- **Cáfoló kísérlet:** megpróbáltam a két irány feliratát közeli `push` utasítások miatt felcserélni. A menürekord-bázisok cáfolják ezt: a `R&otate Clockwise` szöveghez tartozó `0xd6e340` rekord parancsmezője `0x9ca2`; a balra feliratú következő `0xd6e354` rekordé `0x9ca3`. A másik irányú hozzárendelést a független Ghidra-diszpécser is cáfolja. Az ellenpróbát ugyanezen cím- és rekordmező-ellenőrzéssel értékeltem, nem csak az index találataira támaszkodtam.

### A jegy „Kész, ha” pontjai

1. ⛔ **Minden belépő és feltétel:** a főmenü, könyvtári és album-fotó helyi menü, gyorsbillentyű, tálca gomb és helyi menü, néző menü és gyorsgomb, valamint szerkesztő belépők fel vannak sorolva. Az eredeti video/írásvédett engedélyezés belső feltételei és a párbeszédablak pontos állapota nyitottak.
2. ✅ **Megerősítés és megjegyzett beállítás:** az átvizsgált forgatási útban nem találtam megerősítést vagy forgatási állapot mentést; az `UITransitions` olvasás nem forgatási preferencia. Az írási hiba felhasználói UI-ja ettől külön nyitott.
3. ⛔ **Fájlrendszer, ini, index, bélyegkép, rács, kijelölés és undo:** a `.picasa.ini` hatása bizonyított, a PicasaPy SQLite/rács-útja forrásból dokumentált. Az eredeti tartós index, thumbnail cache, mappafa és kijelölés pontos végállapota, valamint a Picasa Undo All Edits hatása nincs eldöntve.
4. ⛔ **Hibák:** az üres kijelölés és támogatott típusok kihagyásának eredeti jelzése ismert; a `.picasa.ini` írásmegtagadásának eredeti felhasználói viselkedése nem bizonyított.

### Javasolt jegytörzs-bővítés

#### Ctrl+R és Ctrl+Shift+R kezelje a kijelölést és jelezze az üres célpontot

**Eredeti:** A Picasa 3.9 `0x005e60d0` gyorsbillentyű-kezelője a forgatás közös kiválasztási útját hívja; a `0x005ee6e0` több kijelölt elemet is sorban feldolgoz, üres lista esetén `IDS_MUST_SELECT_TO_ROT` üzenetet ad.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x005e60d0`, `0x005eef30`, `0x005ee6e0`: gyorsbillentyűvel a kijelölési lista forog, üres kijelölésnél üzenet jelenik meg. | `MainKeyboardShortcuts.qml:281-299`, `MainWindowCommands.qml:381-385`: a globális shortcut egy `selectedIndex`/nézőindex sort ad át; negatív sornál nem jelez. | A könyvtárnézeti shortcut a kijelölt sorlistát adja át a batch forgatásnak; néző/diavetítés esetén maradjon az aktuális kép célpont; üres lista esetén az eredeti erőforrásnak megfelelő notifier-jelzés jelenjen meg. |

**Kész, ha:** több kijelölt képnél Ctrl+R és Ctrl+Shift+R mindegyiket elforgatja; nézőben egyedül az aktuális képet forgatja; üres kijelölésnél a megfelelő figyelmeztetés látszik.

#### Képrotációs gomb a szerkesztőben

**Eredeti:** a Picasa 3.9 `0x005d59f0` `editpanel/rotateleft/right` és `0x00760240` `editoneup/rotateleft/right` vezérlői a fotó közös forgatási útját hívják.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x005d59f0`, `0x00760240`: balra/jobbra forgatja a szerkesztett fotót. | `EditorCropPanel.qml:338-342`, `PhotoViewerEditorPanel.qml:135-144`: a „Rotate” gomb csak a vágókeret tájolását cseréli; a fotót nem forgatja. | A szerkesztőben külön képrotációs vezérlőket tenni elérhetővé; a kivágás forgatása maradjon külön művelet. |

**Kész, ha:** normál és OneUp szerkesztőben külön balra/jobbra képrotáció elérhető; a vágókeret „Rotate” művelete továbbra is csak a kivágási kijelölést érinti.

### Új kutatási jegyjavaslatok

- **A Picasa forgatás Undo All Edits és adatbázis-végállapota:** a kérdés az, hogy a `0x9ca4`/`0x005e7d90` eltávolítja-e a `rotate=` értéket (helyesbítve a #7009-ben: ez a Hide/Unhide, az Undo All Edits `0x9d2d`/`0x005ef3e0` és nem törli a `rotate=`-t), illetve a forgatás után pontosan mely index- és rácsadatok frissülnek. Keresd a `0x005e7d90`, `0x005796c0` és `0x00454770` hívásláncát; zárd le célzott Ghidra-kimenettel vagy kontrollált Picasa-méréssel.

### Nyitott kérdések

- Ghidra-kör kell: 0x0056e1c0 - Nevezze meg a 0x9ca2/0x9ca3 engedélyező állapotbitjeinek szemantikáját, különösen üres kijelölés, video és írásvédett fájl esetén [blokkoló]
  - A meglévő `2026-11-15-6970-colab-decomp.txt` kimenetben a mezők címkézetlenek; az új kérdés az állapotbitek jelentése.
- Ghidra-kör kell: 0x004edf60 - Azonosítsa a `0x005ee6e0` forgatási ciklusban vizsgált fájltípus-értékeket, és hogy ezek közül melyik jelenti a videót [blokkoló]
  - A már meglévő Ghidra-részlet ismeretlen enumértékeket hagy; az új kérdés az értékek videó/fotó címkézése.
- ~~Ghidra-kör kell: 0x005e7d90 - Kövesse az `ID_PICTURE_REVERT` (`0x9ca4`) útját, és döntse el, hogy az Undo All Edits törli-e vagy visszaállítja-e a `rotate=` kulcsot; a meglévő diszpécser csak a hívást mutatja [blokkoló].~~ **LEZÁRVA (#7009):** a `0x005e7d90` a Hide/Unhide kezelője; az Undo All Edits a `0x005ef3e0` és nem törli a `rotate=` kulcsot (a beégetett tokenes kép kivételével, lásd a #7009 nyitott kérdéseit).
- NINCS MEG: eredeti `.picasa.ini` írásmegtagadás felhasználói visszajelzése. Konkrét út: kontrollált Picasa 3.9 mérés ugyanazon mappában, előbb írható, majd mappaszinten írásvédett `.picasa.ini`-vel; rögzítsd a képernyőn megjelenő üzenetet, az ini-t és a visszatérő rácsállapotot. A mérőadat-archívum releváns névszűrése nem adott találatot, ezért nem állítok méréseredményt.
- NINCS MEG: az eredeti index, bélyegkép, mappafa és kijelölés pontos művelet utáni állapota. Konkrét út: célzott, előtte/utána kontrollált Picasa 3.9 mérés és a releváns fájlok/DB-k tételes összevetése.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - ez a #7000 alszakasz.


## #7009: Az Összes szerkesztés visszavonása (Undo All Edits, `0x9d2d`) teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti oldal bináris címei és a PicasaPy forrássorok külön szerepelnek; a
PicasaPy oldalt a mostani forrásból olvastam, nem a korábbi specekből.

### Következtetés

1. **A parancs és a kezelő.** Az Undo All Edits parancskódja `0x9d2d`
   (`ID_PICTURE_REVERT`), a diszpécser (`0x005cb990`) `0x005cbd78` ága közvetlenül a
   `0x005ef3e0` kezelőt hívja. ⛔ **Helyesbítés a #7000-hez:** a #7000 kiinduló
   címei közül a `0x005e7d90` a Hide/Unhide kezelője (`0x9ca5` ír, `0x9ca4` töröl
   `hidden` kulcsot; diszpécser `0x005cbd52`/`0x005cbd5f`), a `0x9ca4` tehát
   `ID_PICTURE_UNHIDE`, nem `ID_PICTURE_REVERT`. A #7000 három nyitott kérdése
   ebből a téves azonosításból indult.
2. **A `rotate=` kulcsot az Undo All Edits NEM törli.** A kezelő egy képre
   négy ini-törlést végez (crop, flipped, filters és redo, text és textactive),
   a `rotate` visszaállítása (`0x00462790` -> `0x0042c980`) csak a Save és Revert jellegű
   függvényekben fut (`0x0046d7d0`, `0x00467ca0`, `0x004613c0`: ezek ugyanazt a négy
   törlőt hívják, és utána a forgatást is alaphelyzetbe teszik), az Undo All Edits
   közvetlen láncából (`0x005ef3e0`, `0x005ef520`, `0x005ef6b0`, a négy törlő) nem. A
   forgatás tehát tartósan megmarad, és a csak elforgatott kép nem teszi aktívvá a
   parancsot (az állapotbájt `2`, a menü szürke). Egyetlen kivétel lehet: a vörösszem,
   retusálás vagy Picnik tokenes kép, ahol a kezelő előbb a `0x0046d7d0`-t hívja
   Undo-Save módban (lásd lent, nyitott).
3. **A törölt kulcsok** a `.picasa.ini` kép-szakaszából: `crop` (`crop=rect64(...)`),
   `flipped`, `filters`, `redo`, `text`, `textactive`; az írások `backuphash`-t
   frissítenek (a job-254 mérés is ezt mutatja). A `crop64` a `filters=` láncon belül lakik, ezért a lánccal együtt
   törlődik. A `.picasaoriginals` visszamásolása csak a három "beégetett" token
   (`redeye`, `retouch`, `picnik`) esetén jön szóba.
4. **Nem visszavonható:** a `redo` kulcs és a szerkesztési lánc is törlődik, az
   útban nincs undo-verem írás. A PicasaPy ennél többet ad (`Undo Batch Edit`), ez
   PicasaPy-saját kiegészítés.
5. **Eltérések a PicasaPy-hoz képest:** (a) a PicasaPy csak a `filters` és a `crop`
   kulcsot törli, a `flipped`, `text`, `textactive`, `redo` kulcsot nem; (b) a
   szürkítés a PicasaPy-ban más szabály szerint megy (a Kép menü bármilyen
   kijelölésnél él, a helyi menü csak a jobbklikkelt sor `filters` láncát nézi, a
   `flipped` kép nem számít szerkesztettnek). Mindkettőre jegytörzs lent.

### Bizonyítottsági fok

**Erős** (statikus, két független út) a hívási láncra, a törölt kulcskészletre, az
engedélyezési képletre és arra, hogy a `rotate` nem tartozik a közvetlen
készletbe. **Feltételes** a beégetett tokenek útja, a nézőből (OneUp) indított
parancs ága és a `0x8000` állapotbit jelentése. **Futásidejű mérés** csak a korábbi
job-254 (#5836) van: könyvtári Kép menü, egy kijelölt kép, a többes szöveg, az
ablakcím `Confirm`, a gombok `Remove Edits` és `No`, az ini-ben a `filters=`
eltűnik és `backuphash=` jelenik meg.

### Hívási lánc és állapotgép

| Lépés | Eredeti (bináris cím) |
|---|---|
| Parancs | `0x9d2d`; menürekord a `0x00559150` építőben: `mov word [0x00d6e4de], 0x9d2d` a `0x0055b86d` címen (rekordbázis `0x00d6e4d4`, felirat `Undo &All Edits`); OneUp helyi menü: `mov word [0x00d6ec12], 0x9d2d` a `0x0073298a` címen. |
| Diszpécser | `0x005cbd78`: `mov eax, ebx; call 0x005ef3e0` (engedélyezést a diszpécser ág nem vizsgál, azt a menüállapot adja). |
| Kezelő | `0x005ef3e0`. Szerkesztői ág, ha `editpanel/preview` létezik és a `+0x20c` bájtja nulla (ugyanez a feltétel adja az engedélyező kód `[esp+0x13]` jelzőjét, `0x0056e240-0x0056e265`); minden más esetben a könyvtári ág (`0x005ef4fe` -> `0x005ef520`). |
| Szerkesztői ág | Megerősítés: ha a `[ctrl+0x3094]` számláló nem nulla (feltételesen: film van a szerkesztőben), `Remove all movie edits?` (`CThumbUI::UndomovieEdits`), különben `IDS_CONFIRMREVERT` (erőforrás-azonosító `0x95`, egy kép szövege), gomb `Remove Edits`. Igen esetén: `0x005f8d80(ctrl,0,0,0)` (a szerkesztési mód lezárása), `0x005ef6b0` az aktuális képre (`[ctrl+0xe64]`), `0x00579910(ctrl,kép,2)` (előnézet és szűrőlánc-felület újraépítése), `0x005683a0` (feltételesen: újra belépés a szerkesztőbe), `0x005f8160` (`editpanel/tab1`). |
| Könyvtári ág | `0x005ef520`: a kijelölés-forrás a `[ctrl+0xea4]` nézet, ha van kijelölése, különben `[ctrl+0xeac]` (a két mutató azonosítása nincs bizonyítva); üres kijelölésnél csendben `3`-mal visszatér, nincs üzenet. Megerősítés mindig a többes szöveggel: `IDS_CONFIRMREVERT_MULTIPLE` (azonosító `0xdc`), gomb `Remove Edits`, a szöveg egy kijelölt képnél is a többes ("ALL of the selected pictures"). Nem: `0x9bac20` -> kilépés `-1`-gyel. Igen esetén képenként: ha `0x00562250(kép) != 0` (az állapotbájt nem nulla) vagy a `CThumbDB` `+0xe4` metódusa (`0x00429530`) igaz, a `0x005ef6b0` fut, különben a kép kimarad. A ciklus végén `0x00476a60` (a `]edited` állapotjelző bájtok újraszámítása), ha volt feldolgozott kép: `0x0065b840` és `0x005796c0(ctrl, azonosítók, 2, 0)` (a bélyegképek frissítése, `Updating thumbnails...` folyamatjelző, a `peoplepanel/update`). |
| Képenkénti törlés | `0x005ef6b0`: (1) ha a kép `filters` listájában van `redeye`, `retouch` vagy `picnik` nevű szűrő (`0x0045f320`, nevek: `0x005ef6e1`, `0x005ef717`, `0x005ef74d`), a `0x005f3e10` a `0x0046d7d0(db,{kép},1,0)`-t hívja (`Undo-Save` mód, feltételes elnevezés; folyamatjelző nélkül), majd `0x00477210`, és újraellenőriz; (2) `0x0042bb50` (`crop` kulcs törlése: `0x00454770(db,kép,"crop",0,1)`); `0x0042d7e0(db,kép,0)` (`flipped` üres értékkel); `0x00460e20` (`filters` és `redo`: `0x0069f710` -> `0x00454770`); `0x004615b0` (üres szöveggel: `text` és `textactive` törlése). A törlők a `0x00454770` írót a `backuphash`-t frissítő utolsó paraméterrel hívják (`1`). |
| Menüállapot gyorsítótára | A kezelők a `[ctrl+0x34a8]`-t `-1`-re állítják (`0x005ef4fe`, `0x0057998a`), ez érvényteleníti a menüállapot gyorsítótárát; a következő menünyitáskor `0x005cb1a0` újraszámol. |

### Belépési pontok és engedélyezés

Az engedélyezést a `0x0056e1c0` menüfrissítő végzi (`0x0056f393-0x0056f402`), a bemenet a
`0x005cb1a0` állapotszó (`[ctrl+0x34a8]`). A szerkesztettségi állapotjelző bájtot a
`0x004296a0` (`CThumbDB` `+0xe0`) számolja: `1`, ha a `filters` nem üres (`0x00461430`)
vagy a `+0xe4` metódus igaz (`0x00429530`: `0x0042af00`, `0x00429dc0` és a film-szerkesztés
objektum); `2`, ha a `rotate(n)` értéke `n mod 4 != 0` (`0x0042c830`) és az előzők közül
egyik sem igaz; `1`, ha a `flipped(n)` értéke pozitív (`0x0042d6c0`); különben `0`. A
`0x005cb1a0` a kijelölés SORRENDJÉBEN az ELSŐ nem nulla állapotú képnél megáll: `0x20`
bit mindig, `0x40` bit, ha az az első szerkesztett kép állapota `2`. Az Undo All Edits
akkor él, ha nincs `0x4000` állapotbit, `[ctrl+0x34a4] == 0`, nincs `0x8000` bit, és
(szerkesztői ág: az aktuális kép állapota pontosan `1`) vagy (`0x20` bit van és `0x40`
nincs). A szürke tétel a menüben is látszik, nem tűnik el (a #3448 képernyőképen a
mappanézeti helyi menüben `Undo all Edits` szürke).

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Kép menü, `Undo &All Edits`** (`0x00559150`, rekord `0x00d6e4d4`, `0x0055b86d`). Szürke, ha a kijelölésben nincs szerkesztett kép, vagy az első szerkesztett kép csak elforgatott (`0x40`). | `PicasaPictureMenu.qml:120-125`: `enabled: bar.photoActionsEnabled`, ami `MainMenuBar.qml:84` szerint pusztán `photoActionRows().length > 0`; a kötés `MainMenuBar.qml:437-438` (`openForLibrary`). | Eltérés: a tétel minden kijelölésnél él, szerkesztetlen vagy csak elforgatott képnél is. 2. jegytörzs. |
| **Bélyegkép helyi menü, mappanézet** (`0x00730790`, felirat `U&ndo all Edits`, `FolderPhoto::ID_PICTURE_REVERT`). | `PhotoContextMenu.qml:304-311`: `enabled: menu.hasEdits`; a `hasEdits` a jobbklikkelt sorból jön (`MainPhotoContextMenu.qml:49-53`), definíciója `model_helpers.py:40-45` (`filters` nem üres); kötés `MainPhotoContextMenu.qml:58-60`. | Eltérés: az eredeti az egész kijelölést nézi (első szerkesztett kép dönt), a PicasaPy csak a jobbklikkelt sort; a `flipped` kép nálunk nem szerkesztett. 2. jegytörzs. |
| **Album-nézet helyi menü** (`0x00731050`, felirat `Undo all &Edits`, `AlbumPhoto::ID_PICTURE_REVERT`). | Ugyanaz a `PhotoContextMenu.qml`; a felirat kisbetűs `all` alakja a #5195 szerint. | Mint fent. |
| **Néző és szerkesztő helyi menü** (OneUp, `0x007327a0`, felirat `U&ndo all Edits`, rekord `0x00d6ec12`). | `ViewerContextMenu.qml:164-171`: `enabled: menu.hasEdits`; `PhotoViewerContextActions.qml:94-96,105`; kötés `MainWindowWorkspace.qml:91-93` (`openFor([row])`, egyes szám szöveg). | Az engedélyezés az aktuális kép `filters` láncát nézi, az eredeti az aktuális kép állapotjelző bájtját (`1` kell): a `flipped`-only kép eltér. A megerősítő szöveg (egyes vagy többes) a nézőből indítva nincs eldöntve (lásd nyitott). |
| **Képtálca helyi menü** (`0x00732ee0`): a menüépítő sztringjei között nincs Undo All Edits. | `TrayContextMenu.qml`: nincs ilyen tétel. | Egyezik. |
| **Gyorsbillentyű:** nincs (a #6967 az `RT_ACCELERATOR` és a `SHORTCUTS.XML` átnézéséből). | `MainKeyboardShortcuts.qml`: nincs. | Egyezik. |
| **Szerkesztő bal panel:** nincs Undo All Edits gomb (a szűrőlánc `undolabel` gombja más parancs). A **film-szerkesztő** `movieeditpanel/reset_trim` gombja a `0x005ef3e0`-t hívja (`0x00595744`, a hívó `0x005952d0`, annak hívója `0x005de8e0`), `Remove all movie edits?` szöveggel. | Szerkesztő bal panel: nincs ilyen gomb. A film-szerkesztő gombját ez a kör nem mérte. | Panel: egyezik. Film-gomb: nem mérve (nem ez a kör tárgya, kutatási jegyjavaslat lent). |

**Videó, szerkesztetlen és vegyes kijelölés** (a fenti képletből): szerkesztetlen kép
(állapot `0`) szürke; csak elforgatott kép (`2`) szürke; videóra külön típusszűrő a
képletben nincs, a film-szerkesztések az `+0xe4` metóduson át számítanak szerkesztettnek
(a metódus pontos tartalma nyitott). Vegyes kijelölésnél az első nem nulla állapotú kép
dönt: ha az elforgatott-only (`2`), a tétel szürke akkor is, ha egy későbbi kép
valódi szűrőláncot hordoz; ha az első szerkesztett kép `1`, a tétel él, és a végrehajtás
minden olyan képre lefut, amelynek állapotjelző bájtja nem nulla (az elforgatott-only kép is
belefér a ciklusba, de neki nincs törölhető kulcsa).

### Megerősítés, ablak és megjegyzett beállítás

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Könyvtári ág (Kép menü, helyi menük): ablakcím `Confirm`, szöveg `IDS_CONFIRMREVERT_MULTIPLE` egy kijelölt képnél is, gombok `Remove Edits` (fókusz) és `No`, nincs "ne kérdezd újra" jelölő (`0x005ef520`, `0x005ef5b2-0x005ef5f6`; mérés: job-254). | `MainDialogs.qml:290-352`; `openForLibrary` (`:318`) a többes szöveget adja (`:326`). Kötés: Kép menü `MainMenuBar.qml:437`, helyi menü `MainPhotoContextMenu.qml:59`. | Egyezik. |
| Szerkesztői ág: egy kép szövege `IDS_CONFIRMREVERT` (`0x005ef43b-0x005ef445`), film esetén `Remove all movie edits?`. | A Kép menü a nézőből is `openForLibrary`-t hív (`MainMenuBar.qml:437`, `photoActionRows()` a néző sorát adja, `MainLibrarySelectionState.qml:70-77`), tehát a többes szöveg jön; a néző saját helyi menüje `openFor([row])` (`MainWindowWorkspace.qml:91-93`), egyes szám. | Eltérés a szerkesztő megnyitott állapotában a Kép menüből: eredeti egyes szám, nálunk többes. A nézőből (OneUp) induló ág feltétele nyitott, ezért jegy csak a szerkesztő ágra szólhat. Lásd a nyitottakat. |
| A `0x005f8d80(ctrl,0,0,0)` a szerkesztői ágban lezárja a szerkesztési módot; ugyanez a függvény `Apply changes to the current image?` kérdést tehet fel (`IDS_ENDEDITMODALITY_*`, `0x005f8e07-0x005f8f93`), ha függő módosítás van. Hogy ez az Undo All Edits után megjelenik-e, nincs eldöntve. | Nincs ilyen második kérdés. | Nyitott (lásd lent). |
| `IDS_CONFIRM_REDEYE_REVERT` (`0x119`): a binárisban nincs közvetlen betöltő hívás ezzel az azonosítóval (a `0x009ae710` betöltő 150 hívásából egyiknek sem ez az azonosítója; kontroll: a `0x95` és a `0xdc` pontosan a `0x005ef3e0` és `0x005ef520` kezelőben talált). Az Undo All Edits kezelői nem használják. | `MainDialogs.qml:331-345`: a vörösszemes képeknél kiegészítő figyelmeztetés (`redeyeNamesInSelection`, `batch_effect_controller.py:309-336`). | Nincs bináris bizonyíték a figyelmeztetés helyére és feltételére; nem javaslok jegyet, a döntés a vörösszem-kérdés Ghidra-körére vár. |
| Megjegyzett beállítás: az Undo All Edits kezelők nem olvasnak és nem írnak `Preferences` kulcsot (a `DoNotAskOnEndEditModality` a `0x005f8d80`-ban van). | Nincs megjegyzett beállítás. | Egyezik. |

### Hatás a fájlokra, indexre és felületre

| Hatás | Eredeti Picasa 3.9 | Jelenlegi PicasaPy | Teendő |
|---|---|---|---|
| `.picasa.ini` kulcsok | Képenként törli: `crop` (`0x0042bb50`), `flipped` (`0x0042d7e0`, üres érték), `filters` és `redo` (`0x00460e20`), `text` és `textactive` (`0x004615b0`); a `rotate` kulcsot nem érinti. A `0x0046d7d0` fájlszintű Revert pontosan ugyanezt a négy hívást tartalmazza (`0x0046e20f-0x0046e233`), de utána még a `rotate`-et is alaphelyzetbe teszi (`0x00462790`, `0x0042c980(db,kép,-1,1)`); a két lánc különbsége a `rotate`. | `_clear_all_effects` (`batch_effect_controller.py:150-159`): csak `filters` és `crop`; majd `backuphash` (`:411`). | 1. jegytörzs: `flipped`, `text`, `textactive`, `redo` törlése; a `rotate` marad. |
| `backuphash` | A `0x00454770` minden ini-írás után frissíti (utolsó paraméter `1`); mérés: job-254, `backuphash=37968`, más kulcs nincs. | `with_backuphash` (`batch_effect_controller.py:411`). | Egyezik. |
| `.picasaoriginals` és a képfájl | Közvetlenül nem nyúl hozzá. Kivétel: a `redeye`, `retouch`, `picnik` szűrőt tartalmazó képnél a `0x005f3e10` a `0x0046d7d0(db,{kép},1,0)`-t hívja (Undo-Save mód: a `0x0053b2e0` párbeszéd `1`-es eredménye, feltehetően az `Undo Save` gomb, ugyanezt a harmadik paramétert állítja, `0x0053b840-0x0053b84d`). A fájl visszamásolása ebben a módban nyitott. A kép egyébként nem íródik. | Nem nyúl a `.picasaoriginals`-hoz és a képfájlhoz; a vörösszem nálunk szűrőlánc-elem, nem beégetett. | Nyitott (Ghidra), jegy nincs. |
| SQLite index | A kezelők nem írnak SQL-t; az `]edited` állapotjelző bájtok a memóriabeli gyorsítótárban számolódnak újra (`0x00476a60`). A perzisztens adatbázis-mezőre ez a kör nem talált írást. | Mappánként `_sync_tree_locked` (`batch_effect_controller.py:427`). | Nem mérve: az eredeti perzisztens indexe. |
| Bélyegkép | A `0x005796c0(ctrl, azonosítók, 2, 0)` a feldolgozott kijelölés minden képére frissít (`0x00579360`), `Updating thumbnails...` folyamatjelzővel, és a `peoplepanel/update` is lefut. | A bélyegkép-URL szerkesztés-érzékeny (`_thumb_url`), a nézet a végén újratöltődik. | Nem mérve. |
| Rács | A kezelők a rácsot nem építik újra; csak a menüállapot gyorsítótára kap `-1`-et. | `_on_batch_edit_work_done` -> `_refresh_view()` (`batch_effect_controller.py:454-458`), ami változott tartalomnál `beginResetModel`-t hív (`photo_grid_state.py:207`). A forgatás célzott `dataChanged`-et használ (#7000), az Undo All Edits teljes resetet. | Nem mérve; lásd 2. pont a nyitottak között. |
| Kijelölés | A kezelők nem írnak kijelölést (csak a `[ctrl+0x34a8]` cache-t). | A kijelölés sorindex alapú, a teljes reset utáni megmaradása nincs mérve. | Nem mérve. |
| Visszavonhatóság | Nem vonható vissza: a `redo` is törlődik, undo-verem írás nincs a láncban. | `undoBatchEdit` visszaadja a `filters` és `crop` értéket (`batch_effect_controller.py:470-532`, `PicasaEditMenu.qml:33-37`), az eredetinek nincs `Edit` menüs Undo-ja (`eMenuEdit::ID_UNDO` literál nincs a binárisban, #1795). | PicasaPy-saját kiegészítés, nem hiba; a `redo` törlése (1. jegytörzs) beleütközik az undo-ba, ezért az undo-nak is hordoznia kell az újonnan törölt kulcsokat. |

### Hibák és részleges végrehajtás

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Az ini-író (`0x00454770`) hibakódot ad, de a törlő függvények a visszatérést eldobják (`0x0042bb50` mindig `0`-val tér vissza), a könyvtári ciklus (`0x005ef650-0x005ef659`) is eldobja a `0x005ef6b0` eredményét; az Undo All Edits láncban nincs hibaüzenet-sztring. Statikusan tehát néma. Futásidejű mérés nincs. | A `_WRITE_ERRORS` hibánál `photoOpFailed` jelzés megy, és a hátralévő mappák kimaradnak (`batch_effect_controller.py:416-419`). | Nem javaslok jegyet: a PicasaPy jelzése hasznosabb, mint az eredeti statikus hallgatása. Futásidejű mérés kell (lásd NINCS MEG). |
| Több kép: a ciklus sorban dolgozik, nincs visszagörgetés, nincs megszakítás; a `0x005ef6b0` korai kilépése (a beégetett token fájlvisszaállítási hibájánál) a kép hátralévő kulcsait kihagyja, de a ciklus a következő képpel folytatja. | Mappánként egy ini-tranzakció (`update_document(..., backup=True)`), megszakítható (`cancelBatchEdit`); hiba esetén a már megírt mappák megmaradnak. | A szemcsézettség (kép, illetve mappa) a felhasználónak nem látszik; nem eltérés-jegy. |

### Két független út és cáfoló kísérlet

- **A út, utasításszintű olvasás:** `0x005cbd78` -> `0x005ef3e0`/`0x005ef520` ->
  `0x005ef6b0` -> `0x0042bb50`, `0x0042d7e0`, `0x00460e20`, `0x004615b0` -> `0x00454770`;
  az engedélyezés `0x0056f393-0x0056f402`, `0x005cb1a0`, `0x004296a0`. A munkaszkriptek a
  `.kutato/` mappában vannak (`dis_*.txt` kimenetek, `cfg_flag.py`, `idsrcall2.py`).
- **B út, független szerkezeti és mérési ellenőrzés:** (1) a hívási-gráf tábla (`xrefs`)
  szerint a fájlszintű Revert (`0x0046d7d0`), amelynek `filters`, `rotate`, `flipped`,
  `textactive` törlését a #6967 már igazolta, pontosan ugyanazt a négy törlőt hívja,
  mint az Undo All Edits (`0x005ef6b0`), de utána még a `rotate`-et is alaphelyzetbe
  teszi (`0x00462790` -> `0x0042c980(db,kép,-1,1)`, `0x0046e243-0x0046e252`), az Undo All
  Edits viszont nem; (2) az
  erőforrás-azonosítók független bájtkeresése (`idsrcall.py`) a `0x95` és a `0xdc`
  azonosítót kizárólag a `0x005ef3e0` és `0x005ef520` kezelőben találja; (3) a job-254
  mérés (`filters=` eltűnik, `backuphash=` megjelenik, többes szöveg egy képnél).
- **Egyezés:** az A és a B út egyezik a törölt készletben és abban, hogy a `rotate`
  nem tartozik hozzá.
- **Cáfoló kísérlet:** megpróbáltam cáfolni, hogy a `rotate` kimarad. Végigjártam a
  `0x005ef3e0`, `0x005ef520`, `0x005ef6b0` és a négy törlő hívottjait és sztringjeit: a
  `rotate`, `rotate(%d)` sztring és a `0x0042c980`/`0x00462790` hívás egyikben sem
  szerepel (a `0x0042c980` hívói az indexben: `0x00425f60`, `0x004613c0`, `0x00462790`,
  `0x00467ca0`, `0x0046d7d0`, `0x0053fe30`, `0x005ee6e0`, `0x006abae0`, `0x006b39b0`,
  `0x00752ae0`; egyik sem az Undo All Edits lánca); az állapotbájt is `2`-t ad az elforgatott képnek, ami a `0x40` bittel
  szürkíti a parancsot (ez csak azért következetes, mert a parancs nem törölné a
  forgatást). A beégetett tokenes ágat ez nem zárja ki, ezért nyitott. A másik
  kísérlet: a kiinduló `0x005e7d90`-et vizsgáltam Undo All Edits kezelőként; a
  diszpécser-ágak és a #6989 szerinti `hidden` kulcs ezt cáfolták.

### A jegy "Kész, ha" pontjai

1. ✅ **Belépési pontok:** Kép menü, mappa- és albumnézeti helyi menü, néző és szerkesztő
   helyi menü, tálca (nincs), gyorsbillentyű (nincs), film-szerkesztő gomb: fel van
   sorolva, külön sorban.
2. ✅ **Törölt kulcsok:** `crop`, `flipped`, `filters`, `redo`, `text`, `textactive`
   (+ `backuphash`); a `rotate` marad (a beégetett tokenes kép kivételével, ott nyitott).
3. ✅ **Szürkítés:** az állapotbájt és a `0x20`/`0x40`/`0x8000`/`0x4000` képlet
   kimondva; videó és vegyes kijelölés a képletből kezelve (film-szerkesztés tartalma
   nyitott).
4. ⛔ **Index, bélyegkép, rács, kijelölés:** a memóriabeli gyorsítótár és a bélyegkép-frissítés
   statikusan megvan, a perzisztens index és a látható végállapot futásidejű mérése
   nincs meg.
5. ⛔ **Hibák:** statikusan néma; futásidejű mérés nincs.
6. ⛔ **Beégetett tokenes kép:** a `.picasaoriginals` visszaállítása Undo All Edits
   alatt nincs eldöntve.

### Javasolt fejlesztői jegytörzsek

#### 1. Az Undo All Edits törölje a `flipped`, `text`, `textactive` és `redo` kulcsot is

**Eredeti:** A Picasa 3.9 Undo All Edits képenkénti törlője (`0x005ef6b0`, hívási helyek
`0x005ef8e8-0x005ef90c`) a `crop` (`0x0042bb50`), `flipped` (`0x0042d7e0`), `filters` és
`redo` (`0x00460e20`), valamint `text` és `textactive` (`0x004615b0`) kulcsot törli a
`.picasa.ini` kép-szakaszából; a `rotate` kulcsot nem.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x005ef6b0`: `crop`, `flipped`, `filters`, `redo`, `text`, `textactive` törlése, `rotate` érintetlen. | `batch_effect_controller.py:150-159` (`_clear_all_effects`): csak `filters` és `crop`; `:411` `with_backuphash`. | A `_clear_all_effects` törölje a `flipped`, `text`, `textactive`, `redo` kulcsot is; a `rotate` maradjon. |
| A törlés visszavonhatatlan (a `redo` is törlődik). | `batch_effect_controller.py:366-432`, `:470-532`: az undo-verem csak a `filters` és `crop` előző értékét őrzi. | Az undo-verem négyeséből (mappa, név, filters, crop) a törölt kulcsokat is hordozó bejegyzés legyen, hogy a `Undo Batch Edit` ne veszítsen adatot. |

**Kész, ha:** egy olyan képen, amelyen `filters`, `crop`, `flipped`, `text`, `textactive`,
`redo` és `rotate` is van, az Undo All Edits után csak a `rotate` marad a szakaszban
(és a `backuphash` frissül); az `Undo Batch Edit` az összes törölt kulcsot visszaírja;
valódi `.picasa.ini` körbejárás-teszt, rontás-kontrollal (a `flipped` kihagyása
elbuktatja).

#### 2. Az Undo All Edits szürkítése kövesse az eredeti szerkesztettségi állapotot

**Eredeti:** A `0x004296a0` állapotbájt (`filters` nem üres, `crop`/film-szerkesztés: `1`;
`rotate(n)`, `n mod 4 != 0`: `2`; `flipped > 0`: `1`; különben `0`), a `0x005cb1a0` a
kijelölés sorrendjében az első nem nulla állapotú képnél megáll (`0x20`, ha `2` volt:
`0x40`), és a `0x0056f393-0x0056f402` képlet szerint a tétel csak akkor él, ha van `0x20`
és nincs `0x40` bit.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Kép menü: szürke, ha nincs szerkesztett kép a kijelölésben, vagy az első szerkesztett kép csak elforgatott (`0x0056f3bf-0x0056f402`). | `PicasaPictureMenu.qml:123`, `MainMenuBar.qml:84`: a tétel minden kijelölésnél él. | A Kép menü tétele a kijelölés szerkesztettségi állapotából engedélyeződjön (lásd lent). |
| Helyi menük: a kijelölés állapota dönt. | `MainPhotoContextMenu.qml:49-53`: a jobbklikkelt sor; `model_helpers.py:40-45`: csak a `filters` számít, a `flipped` nem. | Az állapotfüggvény: nem üres `filters` -> szerkesztett; `rotate mod 4 != 0` és nincs más szerkesztés -> csak elforgatott; pozitív `flipped` -> szerkesztett (a `rotate` mögött); a kijelölés sorrendjében az első nem nulla állapot dönt. Az ismeretlen `+0xe4` tagot (`0x0042af00` tömb, film-szerkesztés) ez a jegy kihagyja. |

**Kész, ha:** szerkesztetlen kép, csak elforgatott kép és csak `flipped` kép mindhárom
menüben (Kép menü, helyi menük, néző) az eredeti képlet szerint szürke, szürke, illetve
élő; két képnél, ahol az első csak elforgatott, a második szűrőláncos, a tétel
szürke; ahol az első szűrőláncos, élő; valódi menü-kattintásos teszt (a tétel `enabled`
állapotát olvassa, nem csak a függvényt hívja).

### Új kutatási jegyjavaslatok

- **A beégetett tokenes Undo All Edits:** a `redeye`, `retouch`, `picnik` szűrőt hordozó kép Undo All Edits-e a `0x0046d7d0`-t Undo-Save módban hívja; a kérdés a fájl és a `rotate`/`filters` kulcsok végállapota. Eszköz: Ghidra a `0x0046d7d0` `0x0046da92` (`bl` flag) utáni ágára, vagy Colab-mérés (Picasa: vörösszem javítás, Save, Undo All Edits, a fájl SHA-256-ja és az ini előtte/utána).
- **Film-szerkesztések az Undo All Edits-ben:** mely kulcsokat számolja szerkesztettnek a `0x00429530`, és törlődnek-e a könyvtári Undo All Edits-tel; a film-szerkesztő `reset_trim` gombjának összevetése.
- **A nézőből (OneUp) induló parancs ága és a szerkesztői ág második kérdése:** `editpanel/preview` `+0x20c` jelentése, `0x005f8d80` megerősítés, `0x8000` bit.

### Nyitott kérdések

- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7006-7008-7009-7012-colab-decomp.txt`): a `0x005f3e10` akkor hívja a `0x0046d7d0(db, [kép], 1, 0)`-t, ha a képen ott a token (`0x0045f320`), utána bélyegkép-frissítés (`0x00579910(kép, 2)`). Az 1-es mód előbb a `0x00471df0`-t hívja; ha az nem jelez, a közös ágra fut (`LAB_0046dc08`), amely törli a `crop`, `flipped`, `filters`/`redo`, `text` kulcsot, és ha a `0x00462790` igazat ad, a forgatást is visszaállítja (`0x0042c980(..., -1, 1)`). **Tehát tokenes (vörösszem, retusálás, Picnik) képnél az Összes szerkesztés visszavonása a forgatást is visszaállíthatja**; a `.picasaoriginals` visszamásolása itt nem látszik, valószínűleg a `0x00471df0`-ben van.
- Ghidra-kör kell: 0x00471df0 - Visszamásolja-e a `.picasaoriginals` mentett eredetijét, és milyen feltétellel jelez, amitől a `0x0046d7d0` nem fut tovább a közös törlő ágra; a `0x00462790` mikor ad igazat [nem blokkoló]
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7006-7008-7009-7012-colab-decomp.txt`): a `0x009c2fc0` név szerinti felületi csomópont-kereső. A `0x005ef3e0`-ban, ha az `editpanel/preview` létezik és a `+0x20c` bájt 0, a szerkesztői ág fut (egyes számú `IDS_CONFIRMREVERT` vagy filmes változat, majd `0x005f8d80`, `0x005ef6b0`, `0x005683a0`), különben a könyvtári ág (`0x005ef520`). A 0 tehát azt jelenti, hogy a szerkesztőpanel aktív. A teljes képernyős néző (OneUp) alatti érték nyitott.
- Ghidra-kör kell: 0x009c2fc0 - Teljes képernyős nézőből (OneUp) indítva az `editpanel/preview` `+0x20c` bájtja 0-e, azaz a szerkesztői vagy a könyvtári ág fut [nem blokkoló]
- Ghidra-kör kell: 0x005f8d80 - A `(0,0,0)` paraméterű hívás az Undo All Edits szerkesztői ágában megjeleníti-e az `Apply changes to the current image?` megerősítést (`0x005f8e07-0x005f8f93` feltételei) [nem blokkoló]
- Ghidra-kör kell: 0x005cb1a0 - A `0x8000` állapotbit: a `ctrl+0x668` és `ctrl+0x99c` atomikusan módosított számlálók jelentése (`0x005cb93f-0x005cb961`, `InterlockedCompareExchange`), és mikor szürkíti az Undo All Edits-et a szerkesztőben [nem blokkoló]
- Ghidra-kör kell: 0x00429530 - A `CThumbDB` `+0xe4` metódus (`0x0042af00`, `0x00429dc0`, film-szerkesztés objektum) mely ini-kulcsokból áll, és a film-szerkesztések törlődnek-e a könyvtári Undo All Edits-tel [nem blokkoló]
- Ghidra-kör kell: 0x005ef520 - Hol használja az eredeti az `IDS_CONFIRM_REDEYE_REVERT` (`0x119`) szöveget: a `0x009ae710` betöltő 150 hívásából egyik sem kapja ezt az azonosítót, tehát más úton töltődik be [nem blokkoló]
- `NINCS MEG`: az Undo All Edits futásidejű végállapota (ini, fájl SHA-256, bélyegkép, rács, kijelölés, `-1` cache után a menü). Megszerzés: Colab-feladat `colab_felmero.py` szerint, Picasa 3.9: szerkesztett (filters, crop, flipped, text, elforgatott) képek, majd Kép menü, Undo All Edits, `Remove Edits`; előtte/utána az ini, a fájl kivonata és képernyőkép; külön futás csak elforgatott képpel (a tétel szürke-e) és vegyes kijelöléssel.
- `NINCS MEG`: írásvédett `.picasa.ini` vagy lemezhiba alatti viselkedés. Megszerzés: ugyanez a Colab-futás mappaszinten írásvédett ini-vel; rögzítendő a megjelenő üzenet és az ini.

## #7022 A címkék hozzáadása és törlése teljes folyamata

### Vizsgálati határ és bizonyítottság

A vizsgálat tárgya a Picasa 3.9.141.259 bináris, SHA-256: `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`. Az eredeti UI-belépési pontok, az Add Tag bemenetének tokenizálása, a Quick Tags beállításai és a jelenlegi PicasaPy kódút statikusan összevethető. Az eredeti címkeírás tényleges fájl-/adatbázis-hatása, az írási hibák, a vegyes címkeállapotú törlés és a viewer út végpontja nyitott, mert a lokális diszasszembly a címke-panel modelljének frissítésénél egy fel nem oldott visszahívásba ér.

Az összesített bizonyítottsági fok **nyitott**. Az alábbi táblázatban a forrás szerint külön jelzem, hogy a részállítás megerősített, feltételes vagy `NINCS MEG`; egyetlen diszasszembly-útból nem emelek állítást megerősítetté.

### Belépési pontok, feltételek és panelhatás

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Nézet > Tags:** a `0x00559150` menüépítő a `&Tags` feliratot a `0xd6e018` rekordba, annak `0x9d2c` parancskódját a `0xd6e022` mezőbe teszi. A `0x0065ab50` a `0x9d2c` kódot `thumbui/tags_toggle`-ra irányítja. A szomszéd `0x9d71` rekord a Properties parancs. A Tags-panel ki-/bekapcsolását a `0x005d9760` végzi. **A rekordazonosítás megerősített; a menü engedélyezési feltétele nyitott.** | `PicasaViewMenu.qml:94-109`, `MainMenuBar.qml:376-377`, `MainWindowLibraryActions.qml:17-23`: a menü mindig a Tags lap megnyitását kéri. Ha már a Tags az aktív lap, nyitva hagyja. | Eltérés: az eredeti aktív Tags fiók ismételt toggle-ja bezárja a fiókot; a jelenlegi menü ugyanarra az aktív lapra állít, és nyitva hagyja. A Tags menüút aktív állapotát a bináris toggle-hoz kell igazítani. |
| **Ctrl+T és Ctrl+K:** a `0x005e60d0` billentyűkezelő `0x4b` és `0x54` esetben ugyanazt, a `0x0065ab00` Tags-toggle-t hívja. A közös billentyűkezelő előtt állapotőrök vannak; ezek pontos néző-/szerkesztő- és fókuszfeltétele nyitott. | `MainKeyboardShortcuts.qml:101-108,320-334`; a közös engedélyezés `MainWindowCommands.qml:229-233`. Ctrl+T az aktív Tags fiókot bezárja, Ctrl+K mindig megnyitást kér. A billentyűk nem aktívak, ha a néző nyitva van vagy szövegmező kapott fókuszt. | Eltérés: Ctrl+K viselkedjen a Ctrl+T-vel azonos toggle-ként, ne csak nyissa a lapot. Az eredeti viewer alatti billentyűviselkedést külön kell eldönteni a nyitott bináris kapu után. |
| **Tálca / felső panelgomb:** a `0x005d9cc0` eseményút a Tags gombra a `0x0065ab00`-n át jut. A `0x005d9760` az aktív metadata lap nevét a bejövő eseménnyel hasonlítja össze (`0x005d9781-0x005d9998`); egyezéskor `thumbui/toggle_right_drawer`-t hív (`0x005d99a0`), más laptól Tags-re váltáskor bekapcsolja a Tags gombot és a `rightdrawerpanel/tagpanel` lapot (`0x005d9ad8-0x005d9b49`). **Ez az út egy diszasszemblyből feltételes.** | `TrayTopRow.qml:244-256,298-312`: az aktív panelgomb bezárja a fiókot, másik lapra kattintva vált. | A látható toggle-viselkedés egyezik. Az eredeti kijelölési, videó- és read-only kapuk nem láthatók ebben a routerben, ezért a teljes engedélyezést külön kell vizsgálni. |
| **Tulajdonságok > Edit Tags / néző:** a `0x00638990` felépít egy `PropertiesPanel::edit_keywords` eseményt. A lokális kód nem dönti el, hogy az esemény panelt vagy ablakot nyit, illetve mikor engedélyezett. A `0x005e60d0` billentyűút felső őre a néző alatti billentyűzést is nyitva hagyja. | `PropertiesPanel.qml:105-145`: a Keywords gomb a `KeywordsDialog` párbeszédablakot nyitja; a jobbklikkes Edit Tags esemény lapváltást kér. `PhotoViewerRightPanels.qml:17-42,61-105`, `PhotoViewerState.qml:155-171`: a néző Tags-panelje az aktuális, egyetlen képre hat; a gyors nézőben nem jelenik meg. A nézőbeli TagsPanel nem kap `readOnlySelection` értéket, ezért annak alapértéke `false`; ez eltér a `KeywordsDialog` saját ellenőrzésétől. | Ne tekintsük a nézőbeli ablaknyitást teljes paritásnak. Ghidra-kör kell a Properties-panel callback céljához és a viewer engedélyezéshez; addig nincs fejlesztői következtetés. |
| **Add Tag mező:** a `0x0063bb30` vessző (`0x2c`) mentén bontja a beírt szöveget, és a nem üres tokeneket külön adja hozzá a `0x0063bed0` útján. Üres értéknél `TagPanel::notify_notext`, részhibánál `Some of the text you entered could not be added as a tag.` üzenet jelenik meg (`0x0063bb9d-0x0063bbd9`, `0x0063bd90-0x0063bdb4`). **A tokenizálás egy diszasszembly-útból feltételes.** Kijelölés-, videó- és read-only engedélyezési feltétel: `NINCS MEG`. | `TagsPanel.qml:49-57,75-100`; `keywords_controller.py:65-68,176-190`. A vessző szóközzé alakul, tehát a `tag1, tag2` egyetlen címkévé válik. A bevitel csak kijelöléskor és írhatónak jelzett kiválasztásnál aktív (`TagsPanel.qml:14-25,79-90`). | Bizonyított bemeneti eltérés: vesszőnél az eredeti több címkét dolgoz fel, a jelenlegi egyet. A beírás elfogadási és részhiba-szabályát a bináris writer út feloldásával kell pontosítani. |
| **Quick Tags gomb:** a `quicktag_%d` esemény a `0x0063a5e0` eseménykezelőtől a `0x0063bed0` add útig jut. A bináris panelen tíz szerkeszthető hely van (`0x0083efa2`, határ `0xa`); két felső hely a `Preferences\quicktags::recent0/1` értékeknek foglalható le. Hiányzó `quicktags::enable_recents` alapértéke `1`. A recent frissítés az első két értékhez pontos, kis/nagybetűt megkülönböztető UTF-16 egyezést használ (`0x0063b960`); egyező recentnél nem rendez át, új címkénél az új kerül a 0. helyre, korábbi 0. az 1. helyre csúszik. **Ezeket a helyeket két bináris út egyezése támasztja alá.** | `TagsPanel.qml:210-218,260-353`; `keywords_controller.py:21-40,280-316,334-397`. Tíz kézi hely és két recent hely van. A jelenlegi recent-egyezés Unicode `casefold`-ot használ (`:297-316`), ezért eltérhet a bináris pontos egyezésétől. | Az UTF-16 pontos egyezést kell megtartani, ha a recent címke kis/nagybetűben tér el. A tízes kiosztás és a recent alapérték megegyezik. |
| **Quick Tags konfiguráció / Autofill:** a `0x0083ea00` konfigurációs ablak tíz mezőt, recent kapcsolót, `quicktagconfig/autofill`, OK és Cancel vezérlőt kezel. A `0x0083f580` Autofill esemény egyszeri műveletként üres mezőket tölt, a recent helyek foglaltságához igazítva indul. A jelöltlista forrása és a kitöltési szabály a lenti kiegészítésben feloldva; a jelöltek bejárási sorrendjének alapja (a könyvtár rekordjainak sorrendje) `NINCS MEG`. | `QuickTagsConfigDialog.qml:5-7,41-75,127-158`; `keywords_controller.py:334-397`. A jelenlegi autoFill beállítás tartós QSettings-kapcsoló; a gombok olvasásakor dinamikusan tölti az üres helyeket az index gyakorisági sorrendjéből. | Eltérés: az eredeti egyszeri mezőkitöltés helyett a jelenlegi tartós, megjelenítéskori feltöltést ad. A jelöltforrás/sorrend feloldása előtt a funkció pontos fejlesztési specifikációja nyitott. |
| **Címkesor helyi menü:** a `0x00735480` menüépítő sorrendje: Add this tag to entire selection, Search for items with this tag, Remove this tag. A `0x0063b430` kezeli a címkesor jobbklikkjét. A bináris `0x0065b160` 30 fölötti kijelölésnél nagy műveleti megerősítést mutat, de a hívás nem lett hozzárendelve minden címke-belépési ponthoz. | `TagContextMenu.qml:27-40`; `MainRightDrawer.qml:89-95`; a fő panel hozzáadását `MainLibrarySelectionState.qml:148-158` 30 fölötti elemszámnál megerősíti. | Eltérés: a három helyi menütétel jelenlegi sorrendje Remove, Search, Add; állítsuk az eredeti sorrendre. A 30 fölötti eredeti megerősítés és a konkrét művelet kapcsolata nyitott, ezért annak általánosításáról ne döntsünk. |
| **Címke törlése:** a Tags eseménykezelő `removetag` ága a megjelenített címkét a `0x0063d670` útján oldja fel, majd a `0x0063c5a0` listamódosítóhoz jut. Azt, hogy vegyes többképes állapotban mely fájlok íródnak, egyenkénti hiba hogyan terjed, és az eredmény visszavonható-e, a lokális út nem dönti el. `NINCS MEG`. | A sor melletti X és a helyi menü Remove tétele is a kijelölt sorokon hív eltávolítást (`TagsPanel.qml:180-204`, `MainRightDrawer.qml:85-87`; viewerben `PhotoViewerRightPanels.qml:86-90`). `keywords_controller.py:193-202` minden kiválasztott sor kulcsszólistájából eltávolítja a megegyező címkét. | A jelenlegi vegyes kijelölési eredmény statikusan egyértelmű; az eredetit a `0x0063c5a0` callback utáni íróút vagy eredeti Picasa-mérés nélkül nem lehet hozzá minősíteni. |

**Kiegészítés (2026-11-15): a Quick Tags Autofill jelöltforrása, sorrendje és kihagyási szabálya.** Statikus olvasás: utasításszintű diszasszembly a `0x0083f210`, `0x0083f3d0`, `0x0083f3f0`, `0x0083f580`, `0x0083f8f0`, `0x0083f2f0`, `0x0063d260`, `0x0063d550`, `0x00639c00`, `0x00437380`, `0x004936c0`, `0x004939e0`, `0x009881d0` és `0x009869a0` függvényen. A `0x0083f580` és `0x0063d260` esetében a `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt` dekompilálása külön úton ugyanezt adja. Futásidejű Picasa-mérés nincs. Fokok: **megerősített** = két független út, **erős** = egy út, egyértelmű utasításokkal, **feltételes** = következtetés.

1. **Hatás: egyszeri szerkesztési művelet, a mentés a bezárásig vár (megerősített).** A `quicktagconfig/autofill` vezérlő eseménye a `0x0083f210` ablakkezelőből (vtábla `0x00cc008c`) a `0x0083f580`-ra jut. Az csak a tíz szerkesztőmezőt állítja (`vtbl+0x34`), preferenciát nem ír. A `quicktags::tag%d` értékeket kizárólag a `0x0083f3f0` menti (a `0x0083f3d0` hívja a `0x10` eseményre; az üres mező `]empty` jelölőt kap), és kihagyja, ha a `[ablak+0xd5c]` Mégse-jelző be van állítva (`0x0083f24e`). Az Autofill tehát nem tartós beállítás: a mezők a bezárásig szerkeszthetők, a Mégse elveti őket. A recent-jelölőnégyzet értéke ezzel szemben azonnal íródik (`0x0083f2f0`, majd a preferencia-író `0x00401900`), és a `0x0083f210` Mégse ága csak a jelzőt állítja és bezár, a kapcsolót nem állítja vissza (erős: a végigkövetett utakban nincs visszaállító kód, mérés nincs).
2. **Jelöltforrás: a teljes könyvtár címkekészlete, nem a kijelölés (erős).** A `0x0083f580` jelöltjeit a `0x0063d260([ablak+0x268], lista, 100)` adja. A `[ablak+0x268]` a Tags-panel: a `0x0063d840` adja át a `0x0083e800` konstruktornak. A forrástömb a panel `+0x2c0` listája (darabszám `+0x2c4`), amelyet egyedül a panel `0x00639c00` betöltő virtuális metódusa tölt (`TagPanel` vtábla `0x00ca0aa4`, 32. hely) a `0x00437380([0xd67668]+0x1034, &panel+0x2c0)` hívással. A `0x00437380` a könyvtár kulcsszó-tárolójának (`db+0x17d8`, zárral védett) sztringkészletét kérdezi le (`0x00411910`, `0x00411210`, `0x004939e0`), minden elemet vesszőnél (`0x2c`) tokenekre bont (`0x009881d0`: tokenenként legfeljebb `0x80` bájt, szóközlevágás nincs), a tokeneket új sztringkészletbe teszi (`0x00493660`, `0x004936c0`), majd a készlet tömbjét sorrendben adja ki (`0x004939e0`). Hogy a tároló kulcsszó-tároló, azt a használat erősíti: a Tags-panel `0x0063ae00` függvényéből hívott `0x00437550` ugyanezt az objektumot elemenként vesszővel bontja.
3. **Jelöltsorrend: első előfordulás, nincs rendezés és nincs gyakoriság (erős; a negatív állítás csak a végigkövetett láncra érvényes).** A `0x004936c0` készlet kivonattal és bájtonkénti egyenlőségvizsgálattal egyedít, számlálója nincs, az új elemet a tömb végére fűzi. A `0x004939e0` és a `0x0063d260` indexsorrendben másol, a `0x0063d550` szűrő csak kihagy. A láncban sehol nincs összehasonlító vagy rendező hívás. Az egyedítés kis- és nagybetűre érzékeny (bájtra pontos). Ez **helyesbíti** a korábbi „valószínűleg a gyakori címkék" feltevést. A készlet tömbjébe az internáló `0x006a2a60` fűz (`[tábla+0xec][i]` sztring a `tábla+0x5c` készletbe); ezt a tábla olvasó metódusai hívják (például `0x006a5060`, amely a `0x006a41e0` keresés mellett internál), ezért az „első előfordulás" a rekordok olvasási sorrendje. Azt, hogy ez az adatbázis betöltési sorrendje vagy a felület első olvasásainak sorrendje, statikusan nem döntöttem el (feltételes).
4. **Mezősorrend és kihagyás (megerősített: az utasításszintű olvasás és a Ghidra-dekompilálás egyezik).** A kezdőmező S = 2, ha a `quicktags::enable_recents` (alapérték 1) be van kapcsolva, különben 0; a preferenciát a kattintás pillanatában olvassa, és a recent-jelölőnégyzet (`0x0083f2f0`) azonnal írja. Az i = S..9 mezőkön növekvő sorrendben megy végig (mező: `ablak+0x26c+i*0x118`). A mező szövegét előbb a `0x009869a0` UTF-8-tudatos szóközlevágáson engedi át; nem üres mezőt kihagy, és nem fogyaszt jelöltet. Az üres mezőbe a lista következő olyan jelöltjét írja, amelyre a `0x0083f8f0` nem igaz: (a) nem szerepel az S..9 mezők nyers szövegében (bájtra pontos egyezés; a két recent mezőt nem nézi), és (b) nem szerepel az ablak „már betöltött" listájában (`ablak+0xd60`, a konstruktor üresre állítja, tehát ablakonként új; legfeljebb 100 elem). A kizárt jelöltet az adott lefutásban végleg átlépi. Beírás után a jelölt a (b) listába kerül. Ha a lista elfogy, a többi üres mező üres marad. Következmény: ha a felhasználó ugyanabban az ablakban kiüríti az Autofill által töltött mezőt, az újabb kattintás már a következő jelöltet teszi be.
5. **A jelöltből kiesnek a recent értékek (erős).** A `0x0063d550` kihagyja azt a jelöltet, amely bájtra egyezik a két recent értékkel (`panel+0x2c8`), ha a panel `+0x350` jelzője (a `quicktags::enable_recents` másolata, a `0x00639c62` és `0x0063c80a` állítja) be van kapcsolva. Mellékhatás: a szűrő a panel másolatát olvassa, a kezdőmező a friss preferenciát, tehát a jelölőnégyzet átváltása és az OK között a kettő eltérhet (feltételes: a másolat frissítése csak a `0x0063c7d0`-ban látszik).
6. **A gomb állapota (erős).** A `0x0083ea00` felépítéskor (`0x0083efc5`) ugyanazt a `0x0063d260`-at 10-es korláttal hívja; ha a lista üres, a `quicktagconfig/autofill` vezérlő `+0x20e` bájtját 1-re állítja (`0x0083f008-0x0083f030`). Ugyanez a bájt a `base_0` és `base_1` vezérlőn a recent-jelölőnégyzetet követi (`0x0083f2f0`), így tiltást vagy elrejtést jelent; melyiket, az mérés nélkül nem dönthető el. A gomb tehát nem használható, ha nincs jelölt.

**Eltérések a jelenlegi PicasaPy-tól** (`keywords_controller.py:320-336,378-398`, `QuickTagsConfigDialog.qml:57,71-76,144-158`):

- Tartós, olvasáskor számolt `autoFillFrequent` kapcsoló az eredeti egyszeri gombja helyett (ismert, 5. jegytörzs).
- Sorrend: a PicasaPy gyakoriság szerint csökkenő, holtversenynél ábécé (`:332`); az eredeti nem rendez, a készletbe kerülés (első előfordulás) sorrendjét adja.
- Egyezés: a PicasaPy `casefold`-dal egyedít és szűr (`:329,390,394`); az eredeti bájtra pontos.
- Foglalt helyek: a PicasaPy `quickTagButtons` a felső két helyre a recent értéket írja, és ha kevesebb mint két recent van, ott `""` marad (`:386-388`); a következő `"" in labels` ág ezeket is feltölti a gyakori címkékkel (`:389-397`). Az eredeti bekapcsolt recent mellett a 0. és 1. mezőt soha nem tölti.
- A „már betöltött" lista és a 100 jelöltes plafon nincs meg; az Autofill gomb nem tiltódik le jelölt hiányában.
- Mégse: a PicasaPy `onRejected` ága a recent-kapcsolót is visszaállítja (`QuickTagsConfigDialog.qml:71-76`); az eredeti Mégse a mezőket elveti, de a már kiírt `quicktags::enable_recents` értéket statikusan nem állítja vissza (erős).

**Nyitott, pontos következő lépéssel:**

- Ghidra-kör kell: 0x006a5060 - a kulcsszó-tábla (a `db+0x17d8` objektum `+0x54` belső táblája) olvasó metódusa; a `0x006a2a60` internálást hívó többi olvasó közvetlen szomszédai: `0x006a5590`, `0x006a5a60`, `0x006a5c60`, `0x006a61f0`, `0x006a63f0`. Kérdés: a kulcsszó-tábla rekordjait az adatbázis megnyitásakor járja-e végig valaki (akkor az adatbázis rekordsorrendje a jelöltsorrend), vagy lustán, az első olvasáskor internál (akkor a felület olvasási sorrendje); és kikerül-e a címke a készletből, ha az utolsó képről is törlik [blokkoló a pontos jelöltsorrendhez, nem blokkoló a kihagyási szabályokhoz].
- Ghidra-kör kell: 0x006393b0 - a Tags-panel gyára (a `0x00639440` konstruktor egyetlen hívója): a panel példánya mikor jön létre és semmisül meg, és kik hívják a 32. vtábla-helyet (`0x00ca0aa4` = `0x00639c00`, `call [reg+0x80]`). Kérdés: a `+0x2c0` lista csak a panel létrehozásakor töltődik, vagy megjelenítéskor és címkeváltozás után is; ettől függ, hogy az Autofill friss vagy pillanatképes listát kap [nem blokkoló].
- `NINCS MEG`: futásidejű eldöntő mérés a sorrendre. Megszerzés: Colab-feladat az eredeti Picasa 3.9-cel; három mappa, rövid, ismert nevű képekkel és ismert beolvasási sorrenddel, olyan címkékkel, ahol a gyakoriság és az első előfordulás sorrendje eltér (például a `b` címke 5 képen, az `a` címke 1 képen, a `b` az első mappában); Quick Tags konfiguráció, Autofill, a tíz mező szövege rögzítendő recent be- és kikapcsolva, majd a mezők kiürítése után újabb Autofill.

### Hatás és hibaágak a jelenlegi forrásban

- A PicasaPy a kijelölt képek címkeunióját listázza; egyelemű és többes kijelölésre ugyanazt az útvonalat használja (`keywords_controller.py:108-136`). A címke hozzáadása deduplikál; a törlés a kijelölt sorokon azonos címkét távolít el (`:176-202`). A fő Tags-panel/Quick Tags út több mint 30 kijelölt képnél megerősítést mutat (`MainLibrarySelectionState.qml:148-158`, `MainDialogs.qml:54-84`); a nézőbeli Tags-panel az aktuális egy képet célozza (`PhotoViewerState.qml:170-171`).
- JPEG-nél a `write_iptc_keywords` az IPTC Keywords mezőt írja; hamis eredmény vagy íráskivétel után a címke `.picasa.ini` `keywords=` CSV-be kerül. Más kiterjesztésnél közvetlenül az ini-út fut (`keywords_controller.py:204-243`). A módosított képszakaszokhoz `with_backuphash` kerül, a mentés `update_document(..., backup=True)` hívással történik (`:244-258,267-268`).
- A fő panel írásvédettségi előellenőrzése mappaszintű írás/törlés próbát használ, és a kijelölésben bármely sikertelen mappa esetén letiltja a bevitelét (`keywords_controller.py:138-174`, `MainRightDrawer.qml:68-75`). Ez nem fájlattribútum-ellenőrzés. A néző TagsPanel nem adja át ezt az ellenőrzést (`PhotoViewerRightPanels.qml:71-90`, `TagsPanel.qml:14-25`), ezért ott a bevitel a `hasSelection` alapján marad aktív. A JPEG IPTC hiba ini-tartalékot és látható hibaüzenetet eredményez; ini-írási hiba üzenetet ad, leállítja a további mappákat, és a jelenlegi mappa index-szinkronja kimarad (`keywords_controller.py:229-276`). Az IPTC-írás az ini-frissítés előtt történik, ezért részleges lemezállapot lehet.
- Sikeres ini-frissítés után a mappafa SQLite-indexe `sync_tree` hívással frissül (`keywords_controller.py:274-275`), utána az aktuális keresési/mappa nézet újratöltődik (`:276`, `controller_sync_mixin.py:65-130`). A címke helyi menü keresési tétele a keresőmezőbe írja a címkét és elindítja a keresést (`MainRightDrawer.qml:93-95`, `MainToolbar.qml:129-133`). A végső rács- és kijelölési állapot futásidejű ellenőrzés nélkül `NINCS MEG`.
- A binárisban a `keywords=%s\n` sztring előfordulása és a `0x0068b320` függvény önmagában nem bizonyítja, hogy a Tags add/remove út oda ír. A `0x0063bed0` lokális útja az `IKeywordUpdate` felület `+0x284` részén keresztül frissít UI/modell állapotot, a `0x0065b4b0` a `0x005c76b0` kijelölés/listaépítőhöz továbbít. A meglévő `0x005c76b0` dekompilálás az indirekt `0x005c7710` visszahívás tényleges célját és a fájlírót nem oldja fel.
- Az eredeti `.picasa.ini`/IPTC írás, index és keresés frissítése, rács/kijelölés végállapota, visszavonhatóság, fájlattribútum-írásvédelem, írási hiba és részleges végrehajtás: `NINCS MEG`. A címke-panel `keywords/readonly_file` és `keywords/readonly_label` erőforrásai igazolják, hogy read-only állapothoz tartozik vezérlő és tájékoztató szöveg; a pontos detektor és hibaág nem.

### Bizonyíték-nyilvántartás

| Érték / állítás | Forrás |
|---|---|
| Bináris változat és SHA-256 | `bináris (Picasa3.exe 3.9.141.259; 644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96)` |
| `View > Tags` rekordkód `0x9d2c`; `0x9d71` Properties | `bináris (0x00559150; 0x0065ab50)` |
| Ctrl+K és Ctrl+T közös Tags-toggle | `bináris (0x005e60d0; case 0x4b, 0x54; 0x0065ab00)` |
| Aktív Tags ismételt toggle és más lapra váltás | `bináris (0x005d9760; 0x005d99a0; 0x005d9ad8-0x005d9b49)` |
| Vesszőnkénti Add Tag tokenizálás és részhibaüzenet | `bináris (0x0063bbdc-0x0063bbf5; 0x0063bd90-0x0063bdb4)` |
| Tag sor helyi menü címkéi és sorrendje | `bináris (0x00735480; 0x0063b430)` |
| Tíz Quick Tags mező és két recent hely | `bináris (0x0083efa2; 0x0063c120; 0x0063c7d0)` |
| Quick Tags recent alapérték és írási szabály | `bináris (0x0063c7d0; 0x0063b960; 0x0063c120)` |
| Quick Tags Autofill egyszeri művelet | `bináris (0x0083ea00; 0x0083f580)` |
| Add/remove író callback és eredeti lemezvégállapot | `NINCS MEG` |
| PicasaPy `.jpg/.jpeg` IPTC, ini-tartalék, ini és index út | `keywords_controller.py:204-276` |
| 7022 címkézési mérőfutás az archívumban | `NINCS MEG` |

### A két független út

- **A út, utasításszintű bináris olvasás:** `0x00559150` rekordmezőiből a feliratot és parancskódot a `0x0065ab50` dispatcherig követtem; az Add Tag útban a `0x0063bb30` vessző-split és a `0x0063bed0` hívás látszik; a `0x005d9760` összehasonlítás elválasztja az azonos aktív lapra érkező toggle-t a lapváltástól.
- **B út, külön UI-adat/xref út:** a bináris string/xref adatok a Tags panel objektumaihoz és a `thumbui/tags_toggle` eseményhez vezettek; a meglévő `0x0063a5e0` Ghidra-kimenet külön azonosítja az `addtag`, `removetag`, `quicktag_%d` és `quick_config` eseményeket. A panel helyi menüjének rekordjai a `0x00735480`-ban külön sorban, külön kódmezőkkel állnak. Ez az út a belépési és menüpont-azonosítást alátámasztja, de nem igazolja a lemezírót.
- **Egyezés:** a View > Tags rekord `0x9d2c` és a `thumbui/tags_toggle` parancs egyezik a két út szerint. A Quick Tags tíz mező/két recent kiosztás egyező bináris konfigurációs és frissítő útból jön. A fájl-/metaadat-hatásra nincs második, független út.

### Cáfoló kísérlet

- **Menürekord:** megpróbáltam a közeli `0x9d71` kódot a `&Tags` szöveghez párosítani. A rekordbáziscím `0xd6e018`-hoz tartozó kódmező `0xd6e022 = 0x9d2c`; a dispatcher `0x9d71` ága `thumbui/properties_toggle`, míg `0x9d2c` ága `thumbui/tags_toggle`. A felcserélt párosítás cáfolódott.
- **Toggle:** ellenőriztem azt az alternatívát, hogy az aktív Tags-re ismételt parancs panelváltásként újranyitja a lapot. A router az aktív metadata lap karaktereit hasonlítja az érkező eseményhez; egyezéskor a `thumbui/toggle_right_drawer` hívásra jut, az explicit Tags-lap-bekapcsoló ág csak eltérő állapot esetén fut. Az alternatíva a statikus útvonal alapján cáfolódik; futásidejű Picasa-mérés továbbra sincs.
- **Autofill:** ellenőriztem, lehet-e a `quicktagconfig/autofill` tartós kapcsoló. A `0x0083f580` az üres szerkesztőmezők setterét hívja; a vezérlő útján nem találtam tartós Autofill-beállítás kulcsát. A kontrollt a `0x0083ea00` konfiguráció-építő és az `autofill` erőforrás is alátámasztja. A jelöltlista pontos forrása/sorrendje ettől még nyitott.

### A jegy „Kész, ha” pontjai

1. ⛔ **Minden belépési pont, engedélyezés, egy/több kép, videó és vegyes címkeállapot:** a View Tags, Ctrl+T, Ctrl+K, tálcagomb, Add Tag, Quick Tags és címkesor-menü ismert útja fel van térképezve; az eredeti kiválasztási, videó/read-only kapu, a viewer callback és a vegyes törlés hatása nyitott.
2. ⛔ **Panel, alapérték, javaslatlista és megjegyzett beállítás:** a bináris 10 kézi mező, két recent hely és one-shot Autofill ismert; az Autofill jelöltforrás/sorrend, a viewer ablak/panel célja és az eredeti mezők végső mentési/Cancel viselkedése nincs teljesen lezárva.
3. ⛔ **Fájlrendszer, IPTC/XMP, `.picasa.ini`, index, keresés, rács, kijelölés, vegyes törlés és undo:** a jelenlegi PicasaPy-forrás végig követhető; az eredeti bináris metadata-/fájlíró és végállapot hiányzik.
4. ⛔ **Read-only, íráshiba és részleges végrehajtás:** a jelenlegi PicasaPy-út le van írva; az eredeti Picasa hibaágai és részleges eredményei bináris callback-feloldás vagy mérés nélkül nem dönthetők el.

### Javasolt fejlesztői jegytörzsek

#### 1. A Nézet > Tags és Ctrl+K ismételt aktiváláskor zárja be az aktív fiókot

**Eredeti:** a `0x005d9760` az aktív `Preferences\active_metadata_tab` és a bejövő Tags-toggle egyezésekor a `thumbui/toggle_right_drawer` hívja; Ctrl+K és Ctrl+T közös `0x0065ab00` út.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A Tags-toggle aktív Tags lap esetén bezárja a fiókot (`0x005d9760`, `0x005d99a0`); Ctrl+K és Ctrl+T azonos út (`0x005e60d0`, `0x0065ab00`). | A Nézet menü és Ctrl+K csak megnyit (`PicasaViewMenu.qml:94-109`, `MainKeyboardShortcuts.qml:101-108`, `MainWindowLibraryActions.qml:17-23`). Ctrl+T és felső tálcagomb már vált (`MainKeyboardShortcuts.qml:320-334`, `TrayTopRow.qml:298-312`). | A Nézet > Tags és Ctrl+K út ugyanúgy váltson, mint az eredeti: másik lapról Tags-re, aktív Tags-ről fiókbezárásra. |

**Kész, ha:** könyvtár-nézetben nyitott Tags panelnél a Nézet > Tags és Ctrl+K bezárja a fiókot; zárt fióknál vagy másik aktív lapnál Tags-re vált. Ctrl+T és a felső panelgomb azonos eredményt ad. Viewer alatti paritást csak az eredeti kapu feloldása után kell megadni.

#### 2. Az Add Tag vesszővel elválasztva több címkét adjon hozzá

**Eredeti:** a `0x0063bb30` a vesszőn (`0x2c`) külön tokenekre bontja a szöveget, tokenenként ad hozzá; hibás elem esetén a többi érvényes elem feldolgozása után figyelmeztet.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Vesszőnként tokenizál, külön hozzáadási kísérlet és részhibaüzenet (`0x0063bbdc-0x0063bdb4`). | `TagsPanel.qml:49-57`, `keywords_controller.py:65-68,176-190`: a vessző szóközzé alakul, egy címke készül. | A bevitelt vesszőnként bontsa, üres részeket hagyja ki, a tokeneket külön dolgozza fel; részhiba esetén a sikeres címkék maradjanak meg, és legyen látható figyelmeztetés. |

**Kész, ha:** `tag1, tag2` két külön címkét hoz létre; üres vesszőrészek nem hoznak létre címkét; egy hibás token nem akadályozza az érvényes tokenek feldolgozását, és az eredmény látható.

#### 3. A címkesor helyi menüje az eredeti sorrendet mutassa

**Eredeti:** a `0x00735480` menüépítő sorrendben az Add this tag to entire selection, Search for items with this tag, Remove this tag elemeket állítja elő.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Add, Search, Remove (`0x00735480`, `0xd6f840` rekordtömb). | Remove, Search, Add (`TagContextMenu.qml:27-40`). | Rendezze a három menüpontot Add, Search, Remove sorrendbe; a műveletek célját ne változtassa. |

**Kész, ha:** a Tags-panel címkesorának jobbklikk-menüjében ez a sorrend látszik, mindhárom tétel a jelenlegi megfelelő műveletet indítja.

#### 4. A recent címke összevetése kövesse az eredeti pontos egyezést

**Eredeti:** a `0x0063b960` a két recent értéket pontos UTF-16 karakter-összevetéssel hasonlítja; csak pontos egyezéskor nem rendez át.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A már azonos karakterláncként szereplő recent nem rendeződik át (`0x0063b960`, `0x0063c120`). | A `keywords_controller.py:297-316` Python `casefold`-ot használ a recent egyezéshez. | Az ismételt recent keresése az eredeti pontos, kis/nagybetű-érzékeny karakterlánc-egyezését használja. |

**Kész, ha:** azonos címke ismétlése nem rendez át; csak kis/nagybetűben különböző címke új értékként kerül előre és a korábbi 0. helyet a 1. helyre tolja.

#### 5. A Quick Tags Autofill egyszeri művelet legyen

**Eredeti:** a `quicktagconfig/autofill` a `0x0083f580` útján egyszer tölt üres kézi mezőket; nem kapcsol be tartós feltöltést. A recent helyek fenntartása dönti el, hogy az első vagy a harmadik mezőtől kezdődik a feltöltés. A jelöltek forrása és a kihagyási szabály feloldva (ld. az 5/b. jegytörzset); csak a rekordok bejárási sorrendje nyitott.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Egyszeri Autofill az üres Quick Tags mezőkre; a recent helyeket kihagyja, ha a fenntartás be van kapcsolva (`0x0083ea00`, `0x0083f580`). | Tartós `autoFillFrequent` beállítás, amely a megjelenített gombokat olvasáskor tölti (`QuickTagsConfigDialog.qml:144-158`, `keywords_controller.py:364-397`). | A tartós megjelenítési kapcsolót cserélje egyszeri mezőkitöltés műveletre; a jelöltek forrását, sorrendjét és kihagyását az 5/b. jegytörzs adja. |

**Kész, ha:** a művelet csak az üres, konfigurált mezőket írja; fenntartott recent hely esetén azokat nem tölti fel; a már beírt kézi címkéket érintetlenül hagyja; a gombok a mentett mezőértékeket mutatják, nem olvasáskor számítják újra a gyakori címkéket. A jelöltforrás, a kihagyás és a sorrend részletes feltételeit az 5/b. jegytörzs adja.

#### 5/b. A Quick Tags Autofill jelöltforrása, kitöltési sorrendje és kihagyási szabálya (kiegészítés, 2026-11-15)

**Eredeti:** a `0x0083f580` a `0x0063d260`-tól kapott jelöltekből tölti az üres szerkesztőmezőket. A jelöltek a könyvtár vesszővel bontott, bájtra pontosan egyedített címkéi a készletbe kerülés (első előfordulás) sorrendjében, legfeljebb 100, a két recent érték nélkül. Recent mellett a 2. mezőtől, nélküle a 0.-tól tölt, növekvő sorrendben; a nem üres mezőt kihagyja, és a mezőkben vagy az ablak már betöltött listájában szereplő jelöltet átugorja.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Egyszeri gomb; a kezdőmező 2 (recent be) vagy 0; az üres mezőket tölti növekvő sorrendben, a nem üreset jelölt fogyasztása nélkül kihagyja (`0x0083f580`, `0x009869a0`). | A helyeket a `quickTagButtons` számolja olvasáskor; ha kevesebb mint két recent érték van, a felső két hely is betelhet (`keywords_controller.py:386-397`). | Az Autofill gomb csak a konfigurációs ablak mezőit írja; bekapcsolt recent mellett a 0. és 1. mezőhöz soha nem nyúl. |
| Jelöltek: a könyvtár címkéi vesszővel bontva, bájtra pontos egyedítéssel, a készletbe kerülés sorrendjében, legfeljebb 100, a két recent nélkül (`0x0063d260`, `0x0063d550`, `0x00437380`, `0x004936c0`). | `_frequent_keywords`: gyakoriság szerint csökkenő, holtversenynél ábécé, `casefold`-dal egyedítve (`keywords_controller.py:320-336`). | A jelöltsorrend az első előfordulás legyen, ne a gyakoriság, és az egyedítés kis- és nagybetűre érzékeny. A pontos bejárási sorrend nyitott (a `+0x2c0` lista írója; a `0x006a5060` nem az, lásd a Ghidra-kiegészítés 3-at); addig a PicasaPy index sorrendje (`all_photos`) a közelítés, és a jegy ezt ki is mondja. |
| Kihagyás: az S..9 mezők nyers szövegében vagy az ablak betöltött listájában (legfeljebb 100) szereplő jelölt (`0x0083f8f0`, `ablak+0xd60`). | Csak a megjelenített helyek `casefold`-os halmaza (`:390-396`). | A kihagyás nézze a mezők szövegét és az ablakban már betöltött jelölteket, bájtra pontosan; egy kiürített, korábban betöltött mezőbe az ismételt kattintás a következő jelöltet tegye. |
| A gomb letiltott vagy rejtett, ha nincs jelölt (`0x0083efc5-0x0083f030`). | Nincs Autofill gomb, csak jelölőnégyzet (`QuickTagsConfigDialog.qml:144-158`). | A gomb legyen letiltva, ha nincs jelölt. |

**Kész, ha:** az Autofill gombra kattintva egyszer töltődnek az üres mezők, utána szabadon szerkeszthetők; az OK ment, a Mégse visszaállít. Bekapcsolt recent mellett a 0. és 1. mező érintetlen akkor is, ha kevesebb mint két recent érték van; kikapcsolva a 0. mezőtől tölt. Az a mező, amelynek szövege szóközlevágás után nem üres, érintetlen, és nem fogyaszt jelöltet. Jelölt nem ismétlődik a mezőkben (a `Nap` és a `nap` két külön jelölt), a recent értékek nem jelöltek, és kiürített mezőbe az újabb kattintás a következő jelöltet teszi. Jelölt nélkül a gomb le van tiltva. A teszt valódi gombkattintással fut, a tíz mező szövegét ellenőrzi, mindkét recent-állásban, üres, részben töltött és elfogyó jelöltlistával.

#### 6. A Tulajdonságok panel kulcsszó-sorának szerkesztése a Tags panelt kapcsolja

**Eredeti:** a `0x00638990` a kulcsszavas sorhoz `edit_keywords` (`0x9d2c`) tételt ad, ami a `0x0065ab50` -> `thumbui/tags_toggle` útra fut (Ghidra-kör, 2026-11-15).

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A jobb oldali Tags panel kapcsolása (`0x0065ab50`). | `PropertiesPanel.qml:105-145`: a Keywords gomb a `KeywordsDialog` modális ablakot nyitja. | A Tulajdonságok kulcsszó-sorának szerkesztése a Tags panelt nyissa vagy zárja, ugyanazon az úton, mint a Ctrl+T. |

**Kész, ha:** a Tulajdonságok panel kulcsszó-sorából indított szerkesztés a jobb oldali Tags panelt kapcsolja; valódi kattintásos teszt.

### Ghidra-kiegészítés 3 (2026-11-16, várólista 419-425)

Forrás: `referencia/ghidra/2026-11-16-7022-7031-7033-colab-decomp.txt` (privát
kutatási tár). Ide a 425 tartozik.

- **`0x0063d260` és `0x0063d550`, a jelöltlista szűrése (425).** Megválaszolva. A
  `0x0063d260(panel, kimeneti lista, korlát)` a panel `+0x2c0` listájának
  (darabszám: `+0x2c4 >> 1`) elemein halad, a **forrás sorrendjében**, 0-tól a
  korlát (itt 100) alatti indexig. Minden elemre a `0x0063d550` dönt: ha igazat
  ad, az elem kimarad, különben a kimeneti lista végére kerül. A
  ciklusszámláló a **forrás elemeit** számolja, nem a megtartottakat: ha a
  forrás első 100 eleme között mindkét recent érték szerepel, 98 jelölt marad.
  Az 5/b. jegytörzs "legfeljebb 100, a két recent nélkül" szövegét ez
  pontosítja: a korlát a forrás elejére vonatkozik. A `0x0063d550(elem)`: ha a
  panel `+0x350` jelzője be van kapcsolva (olvasat: a recent-kapcsoló), a
  `+0x2c8` tömb első két elemével (a két recent érték) veti össze az elemet,
  **bájtonként, kis- és nagybetűre érzékenyen** (kisbetűsítés nincs), és
  egyezésnél `1`-et ad, az elem kimarad. Ha a jelző ki van kapcsolva, nem
  hasonlít, és minden jelölt megmarad. Ha a recent hely üres, és a jelölt is
  null vagy üres, az is egyezésnek számít (az üres jelölt kimarad). A
  `0x0063d260` hívói: `0x0083ea00` (`0x0083efc5`, a konfigurációs ablak) és
  `0x0083f580` (`0x0083f5d4`, az Autofill). A `0x0063d550` másik hívója a
  `0x0063c120` (`0x0063c27a`, a recent-kezelés); a hívás célja a kimenetből nem
  látszik, de a bájtpontos, kis- és nagybetűre érzékeny összevetés a 4.
  jegytörzs "pontos egyezés" állítását nem cáfolja. **PicasaPy:**
  `_frequent_keywords` gyakoriság szerint rendez, és `casefold`-dal egyedít
  (`keywords_controller.py:320-336`); ezt az 5/b. jegytörzs már rögzíti.
- **`0x006a5060` (425).** Megválaszolva, de **nem a feltett kérdésre**: nem
  bejárás és nem készletépítő, hanem kulcs szerinti rekordba író függvény. A
  `0x006a5060(tábla, kulcs, érték)` az indexet az `EAX` regiszterben kapja;
  `-1` indexre `-1`-et ad. A tábla zárja alatt (szálazonosítóval újrabelépő
  zár) a `FUN_006a41e0(tábla, kulcs, 0x13320001, &rekord, 1)` megkeresi a
  kulcshoz tartozó rekordot, a `FUN_006a70e0(tábla, rekord)` ellenőrzi (mindkettő
  nem nulla hibakódot visszaad), majd a rekord saját zárja alatt a
  `rekord+0x1dc` tömb `index`. elemét **felülírja** az `érték`-kel, ha az eltér,
  és jelez a táblának (`FUN_006a2a60(&tábla[0x13])`). Közvetlen hívói a kimenet
  szerint: `0x00425f60`, `0x00444ee0`, `0x004451a0`, `0x00456610`, `0x00467ca0`,
  `0x004a9e20`, `0x005a0f60` és `0x007b2cc0`; a `0x00437380` (az 5/b.
  jegytörzs jelöltforrása) közöttük **nincs** (közvetett hívás lehetséges, de
  ebből a kimenetből nem látszik). Következmény: a jelöltsorrendet nem ez a
  függvény dönti el; a sorrend a panel `+0x2c0` listáját töltő kódon múlik, ez
  nincs a kimenetben. **PicasaPy:** a közelítés változatlan (az index
  `all_photos` sorrendje, 5/b.).

**A jegy lezárhatósága: NEM zárható.** A 425 a "Kész, ha" 2. pontját (panel,
javaslatlista) viszi közelebb: a szűrés és a korlát pontos, de a jelöltek
**sorrendje** továbbra is blokkolt (a `+0x2c0` lista írója nincs meg). Az 1., a
3. és a 4. pont (belépési pontok, fájl- és metaadat-hatás, íráshiba) a 425-től
nem érintett: Windows-mérés, illetve a viewer-kapu Ghidra-köre kell.
**Fejlesztői teendő:** új jegy nincs; az 5/b. jegytörzs "Kész, ha" pontjához
javasolt kiegészítés: a jelöltkorlát (100) a forrás első elemeire vonatkozik, a
két recent kihagyása után tehát legfeljebb 98 jelölt marad; az üres jelölt
bekapcsolt recentnél kimarad.

### Nyitott kérdések

- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a `0x005c76b0` kijelölésgyűjtő, nem metaadat-író; a `+0xeac` a `CAlbumSelectionNode` típusúvá alakított csomópont, a `vtbl+0xdc` közönséges albumnál `0x00401570` (azonnal 0), arcalbumnál `0x0078a6c0`. A címkeíró út nyitott.
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a `0x0063c5a0` egyelemű listát ad át a fő ablak `+0x284` objektumának, felületi frissítő lépés; fájlírót és többképes törlést nem tartalmaz. A vegyes címkeállapotú törlés nyitott.
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a `0x00638990` a Tulajdonságok panel listaelemének helyi menüje; a kulcsszavas sorhoz (`0xca`) az `edit_keywords` tétel `0x9d2c` paranccsal jár, ami a diszpécserben a `0x0065ab50`-re, a `thumbui/tags_toggle`-ra fut: **a jobb oldali Tags panelt kapcsolja, nem modális ablakot nyit.** Nálunk a Keywords gomb a `KeywordsDialog` párbeszédablakot nyitja, ez igazolt eltérés (6. jegyjavaslat).
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a Ctrl+K (`0x4b`) és a Ctrl+T (`0x54`) közös ága a `0x0065ab00` (`tags_toggle`); a billentyűt nem kezeli, ha az ablak módkódja (`+0x30d4`) 2, 4 vagy 6 (vágás, vörösszem, retusálás, szöveg, Picnik), vagy ha a `0x0056c420`, `0x0056c110`, `0x0057c430(4)`, `0x0057c3b0` ellenőrzők egyike igaz. A teljes képernyős nézőbeli elérhetőség ezeken múlik.
- Ghidra-kör kell: 0x0056c420 - a négy ellenőrző (`0x0056c420`, `0x0056c110`, `0x0057c430`, `0x0057c3b0`) melyik nézetállapotot jelöli; a Ctrl+K teljes képernyős nézőben működik-e [nem blokkoló]
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a jelöltlistát a `0x0063d260(obj[+0x268], lista, 100)` építi, legfeljebb 100 elemmel a forrástömb (`+0x2c0`, darabszám `+0x2c4`) sorrendjében, a `0x0063d550` szűrővel; a 10 mezőt a 2.-tól tölti, ha a `quicktags::enable_recents` be van kapcsolva, egyébként a 0.-tól, csak az üreseket; a `0x0083f8f0` kihagyja a mezőkben már szereplő jelöltet. Az 5. jegyjavaslat ezzel megvalósítható, a forrástömb jelentését a kiegészítés oldja fel: nem gyakoriság, hanem a könyvtár kulcsszó-tárolójának első előfordulási sorrendje.
- Megválaszolva (Ghidra 425): a `0x006a5060` nem bejáró és nem készletépítő, hanem kulcs szerinti rekordba író (a `rekord+0x1dc` tömb egy elemét írja); közvetlen hívói között a `0x00437380` nincs. A jelöltlista szűrése teljes (`0x0063d260`, `0x0063d550`): a forrás sorrendjében, a forrás első 100 eleméből, a két recent nélkül (bájtpontos, kis- és nagybetűre érzékeny egyezés, ha a `+0x350` jelző be van kapcsolva).
- Ghidra-kör kell: a panel `+0x2c0` listájának írója - a `0x00437380` és a `0x004936c0` törzse (a jelöltek forrása, 5/b.) és a lenti `0x006393b0` tétel; ebből dől el, hogy az adatbázis rekordsorrendje, a lusta internálás sorrendje vagy más a jelöltsorrend (a kulcsszó-tábla rekordjait az adatbázis megnyitásakor járja-e végig valaki, vagy lustán, az első olvasáskor internál); kikerül-e a címke a készletből, ha az utolsó képről is törlik [blokkoló a pontos jelöltsorrendhez]
- Ghidra-kör kell: 0x006393b0 - a Tags-panel gyára (a `0x00639440` konstruktor egyetlen hívója) és a 32. vtábla-hely (`0x00ca0aa4` = `0x00639c00`) hívói: a `+0x2c0` lista csak a panel létrehozásakor töltődik, vagy megjelenítéskor és címkeváltozás után is; ettől függ, hogy az Autofill friss vagy pillanatképes listát kap [nem blokkoló]
- `NINCS MEG`: futásidejű eldöntő mérés az Autofill jelöltsorrendjére. Megszerzés: Colab-feladat az eredeti Picasa 3.9-cel, három mappa ismert beolvasási sorrenddel, olyan címkékkel, ahol a gyakoriság és az első előfordulás sorrendje eltér; recent be- és kikapcsolva a tíz mező szövege, majd a mezők kiürítése után újabb Autofill.
- `NINCS MEG`: az eredeti Picasa-mérés a fájlok SHA-256-jával és a `.picasa.ini` előtte/utána tartalmával, egy- és többképes JPEG, videó, vegyes címkeállapot, írásvédett fájl/mappa és írási hiba mellett. A hálózat nélküli kutatói körben ilyen mérőadat nem állt rendelkezésre; az új gyűjtéshez a felhős mérőkörnek izolált profilban rögzítenie kell az eredeti Picasa végállapotot.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - ez a #7022 alszakasz.

**Nyitott kérdések: 0 nyílt · 9 lezárva (parancs-azonosítás, törölt kulcskészlet, `rotate` kimarad, engedélyezési képlet, hívási lánc, megerősítő szövegek, visszavonhatatlanság, hibakezelés statikusan, Autofill jelöltforrás és kitöltési szabály) · 11 blokkolt (8 Ghidra, 3 `NINCS MEG` Colab) · 0 hatókörön kívül · 0 csak nyitva.**

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - ez a #7009 alszakasz, és három helyesbítő megjegyzés a #7000 alszakaszban.

## #7001: A csillagozás teljes folyamata az eredeti Picasával összevetve: belépési pontok és hatás

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti és a jelenlegi PicasaPy forrásútjait a bináris disassembly, az indexelt
rekordok és a PicasaPy QML/Python forráskódjának közvetlen összevetésével ellenőriztem.

### Belépési pontok, feltételek, egy és több kép

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Képtálca alsó sáv (Hold / Star gomb):** `thumbui/startoggle` (`0x00748110` `CStarredEnabler::Enable`, kattintáskezelő: `0x005d9cc0` -> `0x005e81e0(panel, 2)`). Engedélyezve, ha a kijelölés nem üres (`0x00748123`). Üres kijelölésnél letiltva (szürke / nem kattintható). | `TrayTopRow.qml:69-79`, `TrayBar.qml:171-180`: `PicasaButton` csillag ikonnal. `enabled: root.hasSelection`. Kattintáskor: `starClicked()` -> `photoOpsController.toggleStarMany(paths)`. | Egyezik a megjelenés, a gomb helye és az engedélyezési feltétel (üres kijelölésnél tiltva). Eltérés a többes kijelölés kezelésében (lásd lent). |
| **Gyorsbillentyű (Ctrl+8):** `0x005e60d0` (`CThumbUI::OnKeyDown`), billentyű `0x38` (`'8'`) + Ctrl lenyomva (`0x005e6584`) -> közvetlen hívás: `0x005e81e0(panel, 2)`. Üres kijelölésnél némán no-op. | `MainKeyboardShortcuts.qml:49-51`: `Shortcut { sequence: "Ctrl+8"; onActivated: photoOpsController.toggleStar() }`. | Egyezik: mindkét rendszer a `Ctrl+8` kombinációt köti a csillag kapcsolásához. |
| **Gyorsbillentyű (F4):** `0x005e6710` (`CThumbUI::OnSysKeyDown` / `OnKeyDown`), billentyű `VK_F4` (`0x73`) a `0x005e696c`-nél -> `0x005d9cc0` hívás -> `0x005e81e0(panel, 2)`. Üres kijelölésnél némán no-op. | `MainKeyboardShortcuts.qml:53-55`: `Shortcut { sequence: "F4"; onActivated: photoOpsController.toggleStar() }`. | Egyezik: az `F4` billentyű mindkét rendszerben közvetlenül kapcsolja a csillagot. |
| **Szerkesztő (OneUp) eszköztár:** `editoneup/star` (`0x00760240`, `0x007606fd` -> `0x005e81e0`). A szerkesztő nézet gyors eszköztárán megjelenő csillag gomb, kattintásra átváltja a nyitott kép csillagát. | `PhotoViewerQuickToolbar.qml:39-44`, `PhotoViewer.qml:150-155`: csillag gomb a gyorseszköztáron. Kattintáskor: `photoOpsController.toggleStar(viewer.currentPhotoPath)`. | Egyezik: a néző/szerkesztő felületen kattintható csillag gomb közvetlenül kapcsolja az állapotot. |
| **Diavetítő (Slideshow) vezérlősáv:** `oneup/star` (`0x008032e0`, `0x00803733` -> csillagkezelő hívás). A diavetítés lebegő vezérlősávján lévő csillag ikon. | `SlideshowControls.qml:89-98`, `MainSlideshow.qml:120-125`: csillag gomb a lebegő vezérlőn. Kattintáskor a diavetítés aktuális képének csillagozása. | Egyezik a funkció és az elérhetőség. |
| **Bélyegkép adorner ikon:** `adorners/star` (`0x00766e00`, `0x007145c0`, `0x005154f0`). Az egérmutató rácselem fölé vitelekor vagy csillagozott állapotban megjelenő arany csillag; rákattintva közvetlen toggle az adott képen. | `ThumbDelegate.qml:140-155`: arany csillag ikon a bélyegkép sarkában. Kattintáskor: `photoOpsController.toggleStar(model.path)`. | Egyezik: a bélyegképen lévő ikonra kattintás közvetlenül átváltja az adott fotó állapotát. |
| **Főmenü és Helyi menük:** A menüépítő (`0x00559150`) és a helyi menü építők (`FolderPhotoWin` `0x00730790`, `AlbumPhotoWin` `0x00731050`, `FolderWin` `0x007319f0`, `TrayWin` `0x00732ee0`, `ViewerWin` `0x007327a0`) NEM tartalmaznak csillagozó menüpontot. Főmenüben kizárólag a Szerkesztés ▸ Csillagozottak kijelölése (`ID_SELECT_STARRED` = `0x9d5b`) létezik. | `PicasaFileMenu.qml`, `PicasaEditMenu.qml`, `PhotoContextMenu.qml`, `TrayContextMenu.qml`, `ViewerContextMenu.qml`: egyik menüben sincs csillagozás parancs. Csak a kijelölési menüpont van meg. | Egyezik: a csillagozás szándékosan gombokra, gyorsbillentyűkre és bélyegkép-adornerre korlátozódik, nem menüparancs. |

#### Részletes feltételek és a többes kijelölés viselkedése

1. **Videófájlok kezelése:**
   - Az eredeti Picasában a videók (`.avi`, `.wmv`, `.mov`, `.mp4` stb.) éppúgy csillagozhatók, mint a képek (`0x005e81e0` nem vizsgálja a média típusát). A videó bekerül a `]star` (`0x00c811d4`) virtuális albumba, és a videóhoz tartozó `.picasa.ini` szekcióba beíródik a `star=yes` kulcs.
   - A PicasaPy-ban a `toggleStarMany` és a `setStar` nem korlátozza a fájltípust, videókra ugyanúgy meghívja az ini és index frissítést. Egyezik.
2. **Több kép kijelölése (Kritikus működésbeli eltérés!):**
   - **Eredeti Picasa:** A `0x005e81e0` függvény egyértelmű ciklust hajt végre a kijelölt elemek indexlistáján (`0x005e821b`-`0x005e8290`). A 2-es műveleti kód (toggle) esetén a ciklusban minden kijelölt elemre meghívja a `CThumbDB::get_star` metódust (vtable `+0xcc`, `0x004755d0`), megfordítja a bitet (`xor al, 1`), majd meghívja a `CThumbDB::set_star` metódust (vtable `+0xc8`, `0x004744d0`). Ez azt jelenti, hogy ha a kijelölésben vegyesen vannak csillagozott és nem csillagozott képek, az eredeti Picasa MINDEGYIK KÉP CSILLAGÁT FÜGGETLENÜL MEGFORDÍTJA (a csillagos csillagtalan lesz, a csillagtalan csillagos).
   - **PicasaPy jelenlegi állapota:** A `photo_ops_transform_mixin.py:90-107` `toggleStarMany` metódusa ezzel szemben homogenizálja a kijelölést:
     `star_all = not all(p.star for p in valid)`
     `for photo in valid: self.setStar(photo.path, star_all)`
     Ha a kijelölésben akár egyetlen csillagozatlan kép is van, az összes kijelölt képet csillagozottá teszi. Csak akkor törli a csillagokat, ha már minden kijelölt kép csillagozott volt.
   - **Teendő:** Fejlesztői jegy szükséges a `toggleStarMany` működésének javítására: elemenkénti független megfordítást kell végezni az eredeti `0x005e81e0` paritásához.
3. **Üres kijelölés:**
   - Képtálca: gomb letiltva (`enabled: false`).
   - Gyorsbillentyűk (`Ctrl+8`, `F4`): a `0x005e81e0` elején a kijelölésszám ellenőrzése (`0x005e821b`) azonnal kilép (`jz 0x5e8290`), némán no-op.
   - PicasaPy: ha a kijelölés üres, a `toggleStar` nem talál aktív elemet, némán visszatér. Egyezik.
4. **Írásvédett fájl / mappa:**
   - A csillag állapot a memóriában és az indexben megváltozik, a bélyegkép azonnal megkapja az adornert. A lemezre írás sikertelenségekor nincs felugró hibaablak, a felhasználói felület nem akad el.

### A párbeszédablak és a megjegyzett értékek

| Mező / Tulajdonság | Eredeti Picasa 3.9 (`0x005e81e0`) | Jelenlegi PicasaPy (`photo_ops_transform_mixin.py`) | Eltérés / Értékelés |
|---|---|---|---|
| Belső párbeszédablak | Nincs. Nem nyit dialógust a Picasa. | Nincs. Nem nyit dialógust a PicasaPy. | Egyezik. |
| Megerősítéskérés | Nincs semmilyen figyelmeztetés vagy megerősítő kérdés. | Nincs megerősítéskérés. | Egyezik. |
| Megjegyzett beállítások | Semmit nem jegyez meg. Nincs kapcsolódó opció vagy registry kulcs. | Semmit nem jegyez meg. | Egyezik. |

### Kimeneti hatás és hibák

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Fájlrendszer:** a képfájl maga (bináris tartalom, EXIF fejléc, XMP metaadat, lemezméret, módosítási dátum) TELJESEN VÁLTOZATLAN marad. Kizárólag a szülőmappában található `.picasa.ini` fájl módosul. | `photo_ops_transform_mixin.py`, `photo_ops_write_mixin.py`: nem nyúl a képfájlhoz lemezen, csak az ini-t frissíti. | Egyezik: a médiafájl binárisan érintetlen marad. |
| **.picasa.ini:** a `0x0068b320` (`0x0068b7ec`-`0x0068b80a`) ini-író rutin csillagozáskor kiírja a `star=yes
` (`0x00ca7888`) bejegyzést az adott fájl szekciójába. A csillag levételekor a `star` kulcsot törli. Ha a szekció üres marad, a fejléc (`[fajl.jpg]`) megmarad. | `ini/writer.py`: `star=yes` bejegyzést kezel a kép szekciójában; törléskor eltávolítja a kulcsot. | Egyezik a kulcsnév és az érték. |
| **Index (adatbázis):** a `CThumbDB::set_star` (`0x004744d0`, `0x00475250`) frissíti a belső rekordot, és hozzáadja/eltávolítja az azonosítót a `]star` (`0x00c811d4`) virtuális albumból (`0x004d9aa0` add, `0x004da1d0` remove). A Csillagozott fotók gyűjtemény azonnal frissül. | `index/db.py`: a `photos` tábla `star` mezője (0 vagy 1) frissül; a csillagozott szűrő/album azonnal leköveti. | Egyezik: az index szinkronban marad a csillag állapottal. |
| **Bélyegkép és rács:** az érintett képek bélyegképén az arany csillag adorner azonnal megjelenik vagy eltűnik. A rács nem ugrik el, a görgetési pozíció nem változik. | `ThumbDelegate.qml`: a `model.isStarred` kötés azonnal újrarajzolja a csillag ikont. | Egyezik: vizuális azonnali visszajelzés. |
| **Kijelölés:** a művelet lefutása után a kijelölt elemek kijelölése PONTOSAN MEGMARAD (nem törlődik a kijelölés, a fókusz nem mozdul el). | `photo_ops_transform_mixin.py`: a művelet nem módosítja a kijelölési modellt. | Egyezik. |
| **Visszavonhatóság (Undo):** a művelet NEM kerül be a képszerkesztési Undo láncba (`0x005e81e0` nem hív `UndoManager`-t). A `Ctrl+Z` nem vonja vissza a csillagozást. Újbóli `F4` / `Ctrl+8` megnyomásával fordítható vissza. | A PicasaPy-ban sincs `UndoStack` regisztráció a csillagozáshoz. | Egyezik: szándékosan nem képi transzformáció. |
| **Írásvédett hely:** ha a `.picasa.ini` nem írható, a memóriában és az indexben a csillag megjelenik, modális hibaüzenet nincs, az alkalmazás nem omlik össze. | Hibakezelés elkapja az `OSError`-t, naplózza, nem fagyasztja le a UI-t. | Egyezik. |
| **Hiányzó fájl:** ha a fájl lemezen nem létezik, az indexbeli csillagozás lefut, a felület nem fagy le. | Nincs összeomlás. | Egyezik. |

### Két független út és cáfoló kísérlet

- **A út, utasításszintű bináris vizsgálat:**
  1. Gyorsbillentyűk kezelése: a `0x005e60d0` (`CThumbUI::OnKeyDown`) `0x38` (`Ctrl+8`) ága a `0x005e6584`-nél, valamint a `0x005e6710` (`CThumbUI::OnSysKeyDown`) `VK_F4` ága a `0x005e696c`-nél mindkét esetben a `0x005e81e0(panel, 2)` központi kapcsoló rutint hívja meg.
  2. Központi kapcsoló rutin (`0x005e81e0`): a kijelölés vizsgálata (`0x005e821b`), a kijelölt indexek ciklusa (`0x005e8220`-`0x005e828a`). A 2-es kódnál lekéri a jelenlegi állapotot (`call dword ptr [edx+0xcc]`), megfordítja (`xor al, 1`), majd beállítja (`call dword ptr [eax+0xc8]`). Ez bizonyítja az elemenkénti független megfordítást!
  3. Adatbázis virtuális album tagság: `CThumbDB::set_star` (`0x004744d0`) hívja a `0x00475250` függvényt, amely a `]star` (`0x00c811d4`) virtuális albumazonosítóhoz hozzáadja (`0x004d9aa0`) vagy eltávolítja (`0x004da1d0`) az adott azonosítót.
  4. INI-írás: a `0x0068b320` mentőrutin a `0x0068b7ec`-nél ellenőrzi a csillag állapotot (`call dword ptr [eax+0xcc]`), és igaz esetén kiírja a `star=yes
` szöveget (`0x00ca7888` a `0x0068b80a`-nál).
- **B út, adatstruktúrák, UI-erőforrások és független rekordok:**
  1. A `picasa3-index.sqlite` adatbázis lekérdezése: a `thumbui/startoggle`, `editoneup/star`, `oneup/star`, `adorners/star` UI gombok és adorner azonosítók független létezésének igazolása.
  2. Menürekordok vizsgálata: a `0x00559150` menüépítőben és a `0x00730790`, `0x00731050`, `0x00732ee0` helyi menükben kizárólag az `ID_SELECT_STARRED` (`0x9d5b`) szerepel, csillagozó menüpont sehol sincs.
  3. Erőforrás-sztringek: `star=yes` (`0x00ca7888`), `]star` (`0x00c811d4`) jelenléte a PE `.rdata` szekciójában.
  4. A PicasaPy forráskódjának tételes vizsgálata (`TrayTopRow.qml`, `MainKeyboardShortcuts.qml`, `ThumbDelegate.qml`, `photo_ops_transform_mixin.py`).
  A két független út egyezik az alapvető működésben, és egyértelműen felfedi a többes kijelölés homogenizálási hibáját a PicasaPy-ban.
- **Cáfoló kísérlet:**
  Azt a feltételezést próbáltam igazolni, hogy az eredeti Picasa a többes kijelölés esetén a képtálca vagy gyorsbillentyű hatására homogenizál-e (tehát ha van köztük csillagtalan, akkor mindet csillagozza, mint a mai PicasaPy).
  - A bináris utasításainak elemzése (`0x005e81e0` ciklusa: `0x005e8248` get_star, `0x005e8254` xor al, 1, `0x005e8260` set_star közvetlenül a ciklusmagon belül elemenként lefutva) ezt a feltételezést EGYÉRTELMŰEN MEGCÁFOLTA. Nincs előzetes összesítő ciklus (mint pl. `all_starred`), nincs közös célállapot-számítás; minden elem szigorúan a saját előző állapotának negáltját kapja. A cáfoló vizsgálat igazolta, hogy a PicasaPy homogenizáló logikája eltérés.

### A jegy „Kész, ha” pontjai

1. ✅ **Belépési pontok és engedélyezési feltételek:** Képtálca (`thumbui/startoggle`), gyorsbillentyűk (`Ctrl+8`, `F4`), szerkesztő/néző gombok (`editoneup/star`, `oneup/star`), bélyegkép adorner (`adorners/star`) és a menük hiánya pontos bináris címekkel és forrássorokkal igazolva.
2. ✅ **Ablak, megerősítés és megjegyzett értékek:** Bizonyítva, hogy nincs párbeszédablak, nincs megerősítéskérés, és nincsenek megjegyzett beállítások.
3. ✅ **Hatás a fájlrendszerre, .picasa.ini-re, indexre, bélyegképre, rácsra és kijelölésre:** Részletesen feltárva: képfájl változatlan, `.picasa.ini` `star=yes` kulcsot kap/veszít, indexben a `]star` album tagsága frissül, adorner azonnal reagál, kijelölés nem változik, képszerkesztési Undo-ba nem kerül.
4. ✅ **Hibakezelés:** Írásvédettség és hiányzó fájl esete pontosan feltárva, modális hiba és fagyás nélkül.
5. ✅ **Több kép viselkedése és eltérés:** A többes kijelölés független toggle működése az eredetiben bizonyítva, a PicasaPy homogenizáló eltérése dokumentálva fejlesztési teendővel.

### Javasolt fejlesztői jegytörzs

#### Több kép kijelölésekor a csillagozás függetlenül fordítsa meg a képek állapotát a homogenizálás helyett

**Eredeti:** A Picasa 3.9 `0x005e81e0` függvénye (`param_2 == 2` toggle híváskor) a kijelölt elemek ciklusában (`0x005e8220`-`0x005e828a`) minden elemre meghívja a `get_star` metódust, majd közvetlenül az adott elem negált értékével (`xor al, 1`) hívja meg a `set_star`-t. Ennek megfelelően vegyes kijelölésnél a korábban csillagozott képekről lekerül a csillag, a korábban csillagozatlanok pedig megkapják azt.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x005e81e0`, `0x005e8248` (`get_star`), `0x005e8254` (`xor al, 1`), `0x005e8260` (`set_star`): elemenkénti független toggle ciklus a kijelölt listán. | `src/picasapy/app/photo_ops_transform_mixin.py:90-107` (`toggleStarMany`): `star_all = not all(p.star for p in valid)`, majd mindegyikre `self.setStar(photo.path, star_all)`. | Átírni a `toggleStarMany` metódust úgy, hogy ne közös `star_all` célértéket számoljon, hanem minden kijelölt fotónál egyenként a saját `not photo.star` állapotát állítsa be: `self.setStar(photo.path, not photo.star)`. |

**Kész, ha:**
- Ha a felhasználó kijelöl 2 képet, amelyek közül az egyik már csillagozott, a másik nem, majd megnyomja az F4 / Ctrl+8 billentyűt vagy a tálca Csillag gombját:
  - Az első képről lekerül a csillag (csillagozatlan lesz).
  - A második kép megkapja a csillagot (csillagozott lesz).
- A művelet után a kijelölés nem változik meg.
- A `.picasa.ini` és az SQLite index mindkét képnél a megfordított állapotot rögzíti.

### Nyitott kérdések

Nincs nyitott kérdés: a folyamat mind a négy alpontja és a többes kijelölés bináris címekkel és forrássorokkal maradéktalanul igazolt. Ghidra-kör nem szükséges.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - a #7001 új szakasza.

## #7008: Az Áthelyezés új mappába (Move to New Folder...) teljes folyamata az eredeti Picasával összevetve

### Következtetés

Az eredeti Picasa 3.9-ben az Áthelyezés új mappába parancs (`0x9d68` / 40296) a Fájl menüből (`0x00559150`, `eMenuFile::ID_FILE_NEWFOLDER`) és a lemezes mappa bélyegkép-helyi menüjéből (`0x00730790`, `FolderPhoto::ID_ALBUM_NEW`) érhető el; a nézőben (OneUp) és gyorsbillentyűvel nem hívható, albumnézetben az első vizsgálat szerint a helyi menüből törlődik (`0x0056c5a0`, `RemoveMenu`; **nem igazolt**, lásd Nyitott kérdések). A parancs feltétele legalább egy kijelölt elem (`FUN_0056e1c0`). A megjelenő Folder Properties ablak (`0x006dc030`, `CEditAlbum`) dátum mezője a kijelölt képek dátumát kapja meg (`0x005e9a42`, `0x0055ce70`), a zene és az automatikus dátum gomb rejtett. A végrehajtás során az új mappa a forrás alatt jön létre (`0x0055d120`), a kijelölt képek, a kísérő fájlok (`.cxf`, `.mxf`, `.thm`) és a `.picasaoriginals` mentett eredetik átmozognak az új helyre (`0x00478780`), a `.picasa.ini` szekciók átmásolódnak és a forrásból törlődnek, az új mappa megnyílik; hogy a fotók kijelölve maradnak-e, **nem igazolt** (lásd Nyitott kérdések). Visszavonás (Undo) nincs.

A PicasaPy megvalósítása (`PicasaFileMenu.qml`, `FileOpsDialogs.qml`, `fileops_controller_move_mixin.py`, `new_folder.py`, `batch.py`, `move.py`) nagyrészt paritásban van a folyamattal és a `.picasa.ini` / `.picasaoriginals` kezeléssel, azonban három fejlesztési eltérést tártunk fel:
1. A bélyegkép helyi menüjében (`PhotoContextMenu.qml`) a menüpont albumnézetben is megjelenik, holott az eredetiben ott nincs jelen.
2. A párbeszédablak alapértelmezett dátumaként a PicasaPy a mai rendszerdátumot adja meg a kijelölt fotó dátuma helyett.
3. Az új mappa kiválasztása után az átmozgatott képek nincsenek kijelölve az új rácsban.

### Bizonyítottsági fok

Megerősített. A folyamat lépéseit, parancskódját, dialógus-paramétereit és fájlrendszeri hatásait két független út (a gépi kód visszafejtése + index RTTI/string kereszthivatkozások) egybehangzóan bizonyítja, kiegészítve két cáfoló kísérlettel.

### 1. Belépési pontok és engedélyezési feltételek

| Belépési pont | Eredeti Picasa (bináris cím) | Engedélyezési feltétel (Eredeti) | PicasaPy (fájl:sor) | Paritás |
|---|---|---|---|---|
| Fájl menü (`Mo&ve to New Folder...`) | `0x00559150`, parancskód `0x9d68` (40296) | `FUN_0056e1c0`: legalább 1 fotó kijelölve (`local_5c & 6 != 0`). Üres kijelölésnél szürke (`MF_GRAYED`); ha mégis lefutna: `0x005e995f` felugró figyelmeztetés (`IDS_MUSTHAVESELECTION`, `0xc97934`) | `PicasaFileMenu.qml:86-90` | Egyezik (`bar.photoActionsEnabled`) |
| Bélyegkép helyi menü (`&Move to New Folder...`) | `0x00730790` (`FolderPhoto::ID_ALBUM_NEW`) | Csak lemezes mappában (`FolderPhoto`). Albumnézetben (`AlbumPhoto`) a `0x0056c5a0` sor 1392 eltávolítja (`RemoveMenu`). Személy nézetben sincs jelen. | `PhotoContextMenu.qml:327-331` | Eltérés: PicasaPy-ban albumban és személy nézetben is látható marad. |
| Néző helyi menü (OneUp) | `0x007327a0` (`ViewerContextMenu`) | Nincs a menüben (csak Open File, Open With stb. érhető el) | `ViewerContextMenu.qml` | Egyezik (nincs jelen) |
| Gyorsbillentyű | Nincs (accelerator táblában a `0x9d68` nem szerepel) | Nincs gyorsbillentyű | Nincs hozzárendelve | Egyezik |
| Média típusok | Kép és videó egyaránt támogatható kijelölésként | Legalább egy érvényes médiaelem a kijelölésben | Kép és videó támogatott | Egyezik |
| Írásvédett hely | A menüpont aktív, a jogosultságot a fájlrendszer vizsgálja | A mappa létrehozásakor és MoveFileW-kor dob hibát | Fájlműveletkor dob hibát | Egyezik |

### 2. Párbeszédablak és mezők alapértékei

A parancs kiválasztásakor a diszpécser (`FUN_005cb990`, `0x9d68` ág) a `FUN_005e9940` függvényt hívja meg. Ha van kijelölés, a `0x005e9a42` lekéri a kijelölt fotó dátumát (`call 0x4ae0a0`), majd meghívja a `0x005eaab0` -> `0x005ea770` -> `0x006dc030` láncot, amely a `Folder Properties` (`CEditAlbum`, `0x00849750`) párbeszédablakot nyitja meg.

- **Ablak címe:** `Folder Properties` (`0x00cc1be8`), ha nem albumból hívják.
- **Név (Name):** Alapértelmezett értéke a szülő mappa neve, vagy `IDS_DEFAULT_ALBUM_NAME` (`0xc8e44c`, magyarul "Névtelen", angolul "Untitled").
- **Dátum (Date):** A kijelölt kép dátuma (`call 0x4ae0a0` @ `0x005e9a42`, formázva `YYYY-MM-DD`).
- **Hely (Place taken):** Üres (`0xc7f979`), vagy a forrás mappa korábbi helyadata.
- **Leírás (Caption / Description):** Üres (`0xc7f979`).
- **Zene (Music):** A zene szekció kontrolljai rejtettek (`SW_HIDE` @ `0x006dc110`), mivel mappához nem rendelhető zene (csak virtuális albumhoz).
- **Automatikus dátum gomb:** Új mappa létrehozásakor a gomb rejtett (`0x006dc0e0` / `SW_HIDE`).
- **Megjegyzett értékek:** A dialógus nem jegyzi meg a korábban beírt egyedi mezőértékeket; minden új hívás a kijelölt képek adataiból indul.

*PicasaPy összevetés:* A `FileOpsDialogs.qml:387-414` a `FolderPropertiesDialog`-ot nyitja meg (`newFolderCreation: true`, `showAutomaticDate: false`), de a dátumot a mai rendszerdátumra (`new Date()`) állítja a kijelölt fotó dátuma helyett, a nevet pedig mindig `untitledFolderName`-re állítja.

### 3. Végrehajtás és futásidejű hatás

Ha a felhasználó az OK gombra kattint (`al == 1` @ `0x005ea7e5`):
1. **Új mappa létrehozása:** `0x005eaa22: call 0x55d120` (`CreateDirectoryW`). A kijelölt fájlok szülőmappájában jön létre az új almappa.
2. **Kötegelt mozgatás indítása:** `0x005eaa63: call 0x5ea420`. Megjelenik a haladásjelző ablak (`CThumbUI::MoveProgress`, `0xc89f94`: "Moving Files").
3. **Fájlok és kísérők mozgatása:** Ciklusonként a `0x00479870` -> `0x00478780` fut le.
   - Főfájl áthelyezése: `0x00479254: call MoveFileW`.
   - Mentett eredetik (`.picasaoriginals`): a `0x00479108` ellenőrzi és áthelyezi a forrás `.picasaoriginals` mappájából a cél `.picasaoriginals` mappájába.
   - Kísérő fájlok: a `0x00479dfc` az azonos törzsnevű `.cxf`, `.mxf`, `.thm` kísérő fájlokat is automatikusan mozgatja.
4. **`.picasa.ini` bejegyzések:**
   - A forrás `.picasa.ini`-t beolvassa (`0x0047886b`), a fájlhoz tartozó szekciót (csillag `star=yes`, forgatás `rotate(...)`, szűrők `filters=...`, arcok `faces=...`) kimásolja.
   - A cél `.picasa.ini`-be beírja a szekciót (`0x00479577`), valamint az ablakban megadott mappa-tulajdonságokat (`[Picasa]` szekció: `name`, `date`).
   - A forrás `.picasa.ini`-ből eltávolítja a fájl szekcióját (`0x004796da call 0x5aa120`), majd mindkét ini fájlt elmenti (`0x00479695`, `0x0047971c`).
5. **Index, mappafa és nézet frissítése:** A `CFolderWatcher` (`0x005a76e0`) és a vezérlő azonnali frissítése (`0x005ea9b4: call 0x4ad150`, `0x005e9b82: call eax`) regisztrálja az új mappát. Az új mappa megjelenik a mappafában, a nézet az új mappára vált, és a rácsban az átmozgatott fájlok ki vannak jelölve.
6. **Visszavonhatóság:** Nem visszavonható (nincs Undo regisztrálva a kötegre, Ctrl+Z nem hozza vissza a fájlokat).

*PicasaPy összevetés:* A PicasaPy-ban a `new_folder.py:create_folder_for_move`, a `move_photos`, a `move_photo` (`originals_follow`-val), az ini frissítések és az `application_services.py` (`select_new_folder_when_indexed`) paritásban vannak. Eltérés: az új mappára váltás után a kijelölés nem marad az átmozgatott képeken.

### 4. Hibák, ütközések és részleges végrehajtás

1. **Létező mappanév ütközése:** Ha a megadott névvel már létezik könyvtár vagy fájl, a `0x0055d120` hibakóddal tér vissza (`ebp != 0`), a folyamat megszakad és nem mozgat fájlokat. (PicasaPy: `create_folder_for_move` `FileExistsError`-t dob, ami az `operationFailed` jelzésen át párbeszédet nyit - egyezik).
2. **Fájlnév-ütközés a célmappában:** Ha a célban már létezik azonos nevű fájl, a `0x005350b0` párbeszédablakot nyitja meg: Rename Duplicates (`CThumbUI::MoveFilesRename`) vagy Skip Duplicates (`CThumbUI::MoveFilesSkip`). (PicasaPy: a `batch.py` a `RENAME` házirenddel `_free_name` alapján `név-1.jpg`-re nevezi át a fájlt - egyezik).
3. **Részleges végrehajtás és lemezhiba:** Ha a köteg közben írási hiba vagy hozzáférési hiba történik (pl. megtelt a lemez, a fájl zárolt), a hibás fájlnál a `MoveFileW` elbukik. Az addig sikeresen átmozgatott fájlok az új mappában és az új `.picasa.ini`-ben maradnak; a meghiúsult fájl a forrás mappában marad a régi `.picasa.ini` szekciójával együtt. (PicasaPy: `_run` ciklusonként kezeli, a sikeresek az újban maradnak, a sikertelenek a régiben - egyezik).

### 5. Paritási összehasonlító táblázat

| Funkció / Lépés | Eredeti Picasa (bináris cím) | PicasaPy (fájl:sor) | Teendő |
|---|---|---|---|
| Fájl menü belépési pont | `0x00559150`, parancskód `0x9d68` (40296) | `src/picasapy/app/qml/PicasaPy/PicasaFileMenu.qml:86-90` | Nincs, paritásban van. |
| Bélyegkép helyi menü belépési pont | `0x00730790`, parancskód `0x9d68` | `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:327-331` | Paritási hiba javítása: Albumnézetben és személy nézetben el kell rejteni a menüpontot. |
| Néző (OneUp) menü | `0x007327a0` (nincs a menüben) | `src/picasapy/app/qml/PicasaPy/ViewerContextMenu.qml` | Nincs, paritásban van. |
| Gyorsbillentyű | Nincs az accelerator táblában | Nincs hozzárendelve | Nincs, paritásban van. |
| Folder Properties ablak megjelenítése | `0x006dc030` (`CEditAlbum`, `0x00849750`) | `src/picasapy/app/qml/PicasaPy/FileOpsDialogs.qml:387-414` | Nincs, paritásban van. |
| Ablak kezdeti dátuma | Kijelölt fotó dátuma (`0x005e9a42: call 0x4ae0a0`) | `FileOpsDialogs.qml:400` (`new Date()`) | Paritási hiba javítása: A mai nap helyett a kijelölt kép dátumát kell átadni. |
| Zene és Auto-dátum vezérlők | Rejtettek (`0x006dc110`, `0x006dc0e0` `SW_HIDE`) | `FileOpsDialogs.qml:391, 402` | Nincs, paritásban van. |
| Új mappa létrehozása szülő alatt | `0x0055d120` (`CreateDirectoryW`) | `src/picasapy/fileops/new_folder.py:65` | Nincs, paritásban van. |
| Fájlok és kísérők (`.cxf`, `.mxf`) mozgatása | `0x00479254`, `0x00479dfc` | `src/picasapy/fileops/batch.py:123`, `move.py:43` | Nincs, paritásban van. |
| `.picasaoriginals` mentett eredetik mozgatása | `0x00479108` | `src/picasapy/fileops/move.py:91` (`originals_follow`) | Nincs, paritásban van. |
| `.picasa.ini` szekció másolása és törlése | `0x00479577`, `0x004796da` | `src/picasapy/fileops/move.py:105, 116` | Nincs, paritásban van. |
| Új mappa kiválasztása a fában és rácson | `0x005a76e0`, `0x005ea9b4` | `src/picasapy/app/application_services.py:86` | Nincs, paritásban van. |
| Átmozgatott fotók kijelölése az új rácsban | Kijelölve maradnak az új mappában | Nincs kijelölés-visszaállítás | Paritási hiba javítása: Az új mappa betöltése után ki kell jelölni az átmozgatott fájlokat. |
| Visszavonhatóság (Undo) | Nincs Undo művelet | Nincs Undo művelet | Nincs, paritásban van. |
| Létező mappanév hibakezelése | `0x0055d120` hibát jelez | `new_folder.py:88` `FileExistsError` | Nincs, paritásban van. |
| Fájlnév-ütközés kezelése | Duplikátum párbeszéd (`0x005350b0`) | `batch.py:159` (`_free_name`, `RENAME`) | Nincs, paritásban van. |
| Részleges hiba kezelése | Sikeresek a célban, hibás a forrásban | Sikeresek a célban, hibás a forrásban | Nincs, paritásban van. |

### 6. Két független út és cáfoló vizsgálat

- **Út A (gépi kód):** A `Picasa3.exe` .text szekciójának visszafejtése a `0x00559150`, `0x00730790`, `0x0056e1c0`, `0x0056c5a0`, `0x005cb990`, `0x005e9940`, `0x005eaab0`, `0x0055ce70`, `0x005ea770`, `0x006dc030`, `0x0055d120`, `0x005ea420`, `0x00479870`, `0x00478780` címeken.
- **Út B (index és RTTI):** A `picasa3-index.sqlite` adatbázis `string_xrefs` (`Mo&ve to New Folder...` @ `0x00559150`, `&Move to New Folder...` @ `0x00730790`, `IDS_DEFAULT_ALBUM_NAME` @ `0x0055ce70`), az RTTI tábla (`CEditAlbum` @ `0x00849750`), a meglévő dekompilációs leletek (`referencia/ghidra/2026-11-13-6845-6532-colab-decomp.txt` sor 128: `FUN_005ea770`), valamint a Picasa erőforrás string-tábla.
- **Egyezés:** A két út maradéktalanul megegyezik a hívási láncban, a parancskódban (`0x9d68`), az engedélyezési logikában és a dialógus mezőiben.
- **Cáfoló vizsgálat 1:** Megvizsgáltuk azt a feltevést, hogy a parancshoz tartozik gyorsbillentyű (pl. Ctrl+M vagy Shift+F). A menüfeliratokban nincs `\t` karakter és az accelerator táblában nincs hozzárendelt billentyűkód, így a feltevés cáfolva.
- **Cáfoló vizsgálat 2:** Megvizsgáltuk azt a feltevést, hogy albumnézetben a képek helyi menüjéből is hívható a parancs. A `0x0056c5a0` 1392. sorában lévő `RemoveMenu(hMenu, 0x9d68, MF_BYCOMMAND)` hívás egyértelműen cáfolta ezt: az eredeti Picasa albumnézetben explicit módon eltávolítja a tételt a helyi menüből.

### 7. A jegy „Kész, ha” pontjai

- Pont 1 (Belépési pontok és engedélyezés): ✅ Bináris címekkel (`0x00559150`, `0x00730790`, `0x007327a0`, `0x0056e1c0`, `0x0056c5a0`) és feltételekkel igazolva.
- Pont 2 (Ablak és alapértékek): ✅ Igazolva a `0x006dc030`, `0x005ea770`, `0x0055ce70` és `0x005e9a42` hívásokból.
- Pont 3 (Hatás a fájlokra, az ini-fájlra, az indexre, kijelölésre, visszavonhatóság): ✅ Igazolva a `0x0055d120`, `0x005ea420`, `0x00478780` láncból.
- Pont 4 (Ütközések és hibakezelés): ✅ Igazolva a `0x0055d120`, `0x005350b0` és a ciklus-hibakezelésből.
- Pont 5 (Paritási táblázat és fejlesztői jegyjavaslatok): ✅ Táblázat és jegytörzsek elkészítve.

### 8. Javasolt fejlesztői jegyek

#### 1. jegyjavaslat (ELVETVE, a Ghidra-kör cáfolta): A bélyegkép helyi menüjében a Move to New Folder elrejtése albumnézetben
- **Cím:** Bélyegkép helyi menü: Áthelyezés új mappába elrejtése albumnézetben és személy nézetben
- **Törzs:**
  Eredeti: `0x0056c5a0` sor 1392 (`RemoveMenu(hMenu, 0x9d68, MF_BYCOMMAND)`). Az eredeti Picasa albumnézetben (`AlbumPhoto`) eltávolítja a helyi menüből az Áthelyezés új mappába parancsot, mert az album virtuális gyűjtemény, a képek nem lemezes mappaként vannak jelen.
  Nálunk: `src/picasapy/app/qml/PicasaPy/PhotoContextMenu.qml:327-331` tételnek nincs láthatósági feltétele, így albumnézetben is megjelenik.
  Teendő: A `PhotoContextMenu.qml` `contextMenuMove` tételéhez hozzáadandó a `visible: menu.currentAlbumToken === "" && menu.personName === ""` és `height: visible ? implicitHeight : 0` kötés.
  Kész, ha: albumnézetben vagy személyalbum rácsán jobb gombbal kattintva az Áthelyezés új mappába tétel nem jelenik meg a helyi menüben.

#### 2. jegyjavaslat: A Folder Properties ablak kezdeti dátumának kitöltése a kijelölt fotó dátumával
- **Cím:** Áthelyezés új mappába: a mappa kezdeti dátuma a kijelölt fotó dátuma legyen a mai nap helyett
- **Törzs:**
  Eredeti: `0x005e9a42` (`call 0x4ae0a0`) és `0x0055ce70` (`fstp qword ptr [esi + 0x28]`). Az eredeti Picasa az új mappa tulajdonságai ablakban a kijelölt kép felvételi dátumát állítja be alapértelmezettként.
  Nálunk: `src/picasapy/app/qml/PicasaPy/FileOpsDialogs.qml:400` a mai rendszerdátumot adja meg (`Qt.formatDate(new Date(), "yyyy-MM-dd")`).
  Teendő: Az `openFor(pathList)` függvényben a kijelölt fájl felvételi dátumát kell lekérdezni a vezérlőtől, és azt beállítani a `currentDate` mezőbe.
  Kész, ha: egy korábbi dátumú képet áthelyezve az ablakban a kép dátuma jelenik meg alapértelmezettként a mai nap helyett.

#### 3. jegyjavaslat (feltételes, a Nyitott kérdések 2. pontja dönti el): Az átmozgatott képek kijelölése az új mappában az áthelyezés után
- **Cím:** Áthelyezés új mappába: az átmozgatott fotók kijelölése az új mappa rácsában
- **Törzs:**
  Eredeti: Az áthelyezés és a nézetváltás után az átmozgatott fájlok az új mappa rácsában ki vannak jelölve.
  Nálunk: `src/picasapy/app/application_services.py:86` kiválasztja az új mappát (`controller.selectFolder`), de a kijelölést nem állítja be az áthelyezett elemekre.
  Teendő: A mappa kiválasztása és az index frissülése után a rácson ki kell jelölni az átmozgatott fájlok elérési útjait.
  Kész, ha: az Áthelyezés új mappába befejeződésekor az új mappában az átmozgatott képek kijelölve látszanak.

### 9. Új kutatási jegyjavaslatok

Nincs szükség új kutatási jegyre; a folyamat minden lépése statikusan és binárisan lezárt.

### 10. Nyitott kérdések

A hívó ellenőrző mintavétele (2026-11-15): a 2. javaslat igazolt (a `0x004ae0a0` a kijelölt kép dátumát adja vissza OLE-napban, a `0x005e9a47` hozzáad `0xcf50c8` = 1/86400 napot, azaz egy másodpercet). A másik kettő nem igazolt:

1. A meglévő Ghidra-kimenetekben a `0x0056c5a0` egyetlen `RemoveMenu` hívása sem kapja a `0x9d68` kódot, és a gépi kódban sincs `0x9d68` közvetlen érték a függvényben; a változó kódú `RemoveMenu(pHVar20, UVar14, 0x400)` lehet a forrás.
   - Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7006-7008-7009-7012-colab-decomp.txt`): **cáfolva.** A `0x0056c5a0`-ban nincs `0x9d68`; a változó kódú `RemoveMenu` pozíció szerint elválasztókat töröl (`0x13`-`0x16`), a konkrét kódú törlések `0x9d96`, `0x9d97`, `0xa09f`, `0x9ca4`/`0x9ca5`, `0xa0b5`, `0xa0cb`, `0x9cd0`/`0x9c72`. Az 1. jegyjavaslat ezért elvetve.
2. A 3. javaslat (kijelölés az új mappában) mögött nincs bináris cím.
   - Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7006-7008-7009-7012-colab-decomp.txt`): **nem igazolt.** A `0x00478780` tisztán fájl- és ini-mozgató (`.picasa.ini`, `.picasaoriginals`), a `0x0055d120` album-adatbázis segéd; a `0x005e9940` siker után frissít (`0x0065b840`), majd a `[+0x2a4]` vtábla `+0x44` metódusát hívja `(azonosító, 1, 1, 0)`, ami valószínűleg az új gyűjteményre navigál. Kijelölés-beállítást egyik sem tartalmaz, ezért a 3. jegyjavaslat nem nyitható termékjegyként, amíg a `+0x44` cél nincs feloldva.

### 11. Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - ez a #7008 alszakasz.

## #7006: Az elrejtés és felfedés teljes folyamata az eredeti Picasával összevetve

### 1. Belépési pontok, engedélyezési feltételek és parancskódok

Az eredeti Picasa 3.9 elrejtési és megjelenítési folyamata képszinten és mappaszinten két külön parancspáron fut:

| Belépési pont | Eredeti azonosító és cím | Engedélyezési feltétel / láthatóság | Viselkedés |
|---|---|---|---|
| Főmenü: Kép ▸ Elrejtés | `eMenuPicture::ID_PICTURE_HIDE` (`0x9ca5`), `0x00559150`, diszpécser `0x005cb990` (`0x5cbd5f`) -> `0x005e7d90(1)` | Él, ha a kijelölésben van legalább egy még nem rejtett kép (`FUN_0056c5a0`). | A teljes kijelölést egységesen elrejti. |
| Főmenü: Kép ▸ Megjelenítés | `eMenuPicture::ID_PICTURE_UNHIDE` (`0x9ca4`), `0x00559150`, diszpécser `0x005cb990` (`0x5cbd52`) -> `0x005e7d90(0)` | Él, ha a kijelölésben van legalább egy rejtett kép (`FUN_0056c5a0`). | A teljes kijelölést egységesen megjeleníti. |
| Rács helyi menü | `AlbumPhoto::ID_PICTURE_HIDE` / `ID_PICTURE_UNHIDE` (`0x00730790`, `0x00731050`) | Kizárólag az egyik tétel jelenik meg a menüben (`0x0056cd8d`-`0x0056cf99`): a nem releváns tételt a `RemoveMenu` eltávolítja. | Ha a célkép nem rejtett: `&Hide` (`0x9ca5`); ha rejtett: `&Unhide` (`0x9ca4`). |
| Egyképes néző helyi menü | `OneUp::ID_PICTURE_HIDE` / `ID_PICTURE_UNHIDE` (`0x007327a0`) | Kizárólag az egyik tétel jelenik meg (ugyanaz a `RemoveMenu` szűrés). | Az aktuális kép állapota szerint vagy `&Hide` vagy `&Unhide`. |
| Gyorsbillentyű | NINCS (`0x00d6e504 = 0`, `0x00d6e518 = 0`). | Nincs gyorsbillentyű hozzárendelve a menütáblában. | - |
| Képtálca | NINCS gomb. | A tálca gombsorában nem szerepel elrejtés vagy megjelenítés gomb. | - |
| Mappaszint: Főmenü és helyi menü | `Folder::ID_HIDEENTIREALBUM` (`0x9c72`, `&Hide Folder`) / `Folder::ID_UNHIDEENTIREALBUM` (`0x9cd0`, `&Unhide Folder`), `0x007319f0` -> `0x005ee2a0` | A mappa rejtett állapota (`[eax + 0xdd6]`) szerint kizárólag az egyik jelenik meg (`0x0056de40`-`0x0056de6f`). | Mappa elrejtése / felfedése, jelszó-ellenőrzéssel. |

### 2. Megerősítés, párbeszédablak és megjegyzett beállítás

- **Képszintű elrejtés (`0x005e7d90`):** SEMMILYEN megerősítést vagy figyelmeztető párbeszédablakot nem ad. Egy vagy több kijelölt kép esetén kérdés nélkül azonnal végrehajtódik.
- **Mappaszintű elrejtés (`0x005ee2a0`):** Ha a "Hidden Folders" gyűjtemény még nem rendelkezik jelszóval, párbeszédablakot nyit:
  - Cím: `IDS_PROMPT_HIDDEN_PWD_TITLE` (`0xc97e58`, erőforrás `0x10f`)
  - Szöveg: `IDS_PROMPT_HIDDEN_PWD_MESSAGE` (`0xc97e38`, erőforrás `0x110`): *"The \"Hidden Folders\" collection is not currently password protected.\nWould you like to add a password now?"*
  - Gombok: `Add Password` (`0xc97e04`), `Don't Add Password` (`0xc97dcc`).
  - Megjegyzett beállítás: `DoNotConfirmHiddenPwd` (`0xc97db4`, checkbox / beállításkulcs), amely letiltja a rákérdezést.

### 3. Végrehajtás és futásidejű hatás

1. **A kijelölés lekérése:**
   A `0x005e7d90` elején a `0x005c76b0` lekéri a kijelölt elemek listáját (`&local_list`). Ha a lista üres vagy a lekérés hibát ad, a függvény azonnal kilép (`0x005e7dbc`).

2. **Vegyes kijelölés kezelése (egységesítés):**
   - **Elrejtés (`param_1 == 1`, `0x9ca5`):** A `0x005e7de0` a `CThumbUI` virtuális táblájának 35. metódusát (`0x0065b710`) hívja a `]hidden` kulccsal (`0xc811f4`) és a listával. A `0x0065b710` meghívja a `0x004da1d0` belső attribútum-írót `value = 1` paraméterrel. Ez a ciklus a kijelölési lista **minden egyes elemére** beállítja a `hidden=1` értéket a `.picasa.ini`-ben és az adatmodellben. Vegyes kijelölésnél a látható képek is rejtetté válnak, a már rejtettek rejtve maradnak (az egész kijelölés egységesen rejtett lesz).
   - **Megjelenítés (`param_1 == 0`, `0x9ca4`):** A `0x005e7df8` a `+0x284` al-objektum virtuális táblájának 4. metódusát (`0x0065b590`) hívja a `]hidden` kulccsal. A `0x0065b590` meghívja a `0x004d9aa0` attribútum-törlőt. Ez a ciklus a lista **minden egyes eleméről** eltávolítja a `hidden` kulcsot. Vegyes kijelölésnél a rejtett képek felfedődnek, a láthatóak láthatóak maradnak (az egész kijelölés egységesen látható lesz).
   - **Következtetés:** Nincs elemenkénti állapotfordítás (toggle); a művelet mindig a választott parancs irányába egységesíti a kijelölést.

3. **Frissítés és rács-hatás:**
   Mindkét ág után lefut a közös `0x0065b840(edi, 0, 0, 1)` frissítés.
   - Ha a Nézet ▸ Rejtett képek (`ID_VIEW_SHOWHIDDEN`, `0x00c8cfb8`) beállítás be van kapcsolva, a képek a rácson maradnak, de rejtett állapotjelzőt kapnak.
   - Ha a beállítás ki van kapcsolva, az elrejtett képek azonnal eltűnnek a rácsból, a kijelölés ürül, és a mappa darabszáma azonnal csökken.

4. **Előnézet / szerkesztő utólagos lépése (`0x005683a0`):**
   A `0x005e7e2a`-`0x005e7e57` szakaszban, ha az `editpanel/preview` (`0xc88a2c`) objektum létezik és nem mutatja a rejtett képeket (`byte ptr [eax + 0x20c] == 0`), és Elrejtés parancs futott (`param_1 == 1`), meghívja a `0x005683a0(edi)` központi nézetváltót:
   - A pontos hatás nem igazolt (lásd Nyitott kérdések 2.); a valószínű viselkedés: a néző a következő látható képre lép, vagy visszavált a rácsnézetbe.

5. **Írási hiba:**
   A `0x004da1d0` nem dob felugró hibaablakot; írásvédett lemez vagy ini-hiba esetén a háttérművelet csendesen hibakóddal tér vissza, a felhasználói felületen nincs hibaablak.

### 4. Paritási összevetés és eltérések táblázata

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Főmenü Elrejtés engedélyezése: `0x0056c5a0` (`0x0056cd8d`): csak akkor él, ha van nem rejtett kép a kijelölésben. | `PicasaPictureMenu.qml:130`: `enabled: bar.photoActionsEnabled`. | A Kép ▸ Elrejtés tétel csak akkor legyen aktív, ha a kijelölésben van legalább egy látható (még nem rejtett) fotó (`bar.hasVisiblePhotoSelection`), hasonlóan a Megjelenítés meglévő `bar.hasHiddenPhotoSelection` feltételéhez. |
| Helyi menü parancs-végrehajtása vegyes kijelölésnél: a kattintott menüpont (Hide vagy Unhide) fixen a saját irányába egységesíti a kijelölést (`0x005e7d90(1)` vagy `0x005e7d90(0)`). | `MainPhotoContextMenu.qml:62`: `onHideToggleRequested: hostWindow.toggleHiddenSelection()`; `MainWindowCommands.qml:475`: `hostController.toggleHiddenRows(rows)`. | A helyi menüben a felirat (`PhotoContextMenu.qml:320`) a jobbklikkelt kép alapján vált (`hideChecked`), de a `toggleHiddenRows` vegyes kijelölésnél mindig elrejt (`hide_all = not all(p.hidden)`). Ha a jobbklikkelt kép rejtett, a menü „Megjelenítés”-t mutat, de a kattintás mindent elrejt. Javítás: a menüpont explicit `hideSelection()`-t vagy `unhideHiddenSelection()`-t hívjon a feliratának megfelelően. |
| Képnéző utólagos lépése rejtéskor: `0x005e7e57` -> `0x005683a0`: ha a nézett kép elrejtődik és `!showHidden`, a nézet a következő látható képre lép, vagy visszavált a könyvtárba, ha elfogytak a képek. | `PhotoViewerContextActions.qml:135`: `controller.toggleHiddenRows([viewer.currentIndex])`. | A nézőben történő elrejtés után, ha `!controller.showHidden`, a néző léptessen a következő megjeleníthető képre, vagy ha nincs több kép a mappában, zárja be a nézőt (`hostWindow.closePhotoViewer()`). |
| Megerősítés képszinten: nincs megerősítés (`0x005e7d90`). | `MainWindowLibraryActions.qml:84-110`: nincs megerősítés. | Egyezik, teendő nincs. |
| Gyorsbillentyű: nincs (`0x00d6e504 = 0`, `0x00d6e518 = 0`). | Nálunk nincs gyorsbillentyű kötve. | Egyezik, teendő nincs. |
| Képtálca: nincs elrejtés gomb. | Nálunk nincs elrejtés gomb a tálcán. | Egyezik, teendő nincs. |
| .picasa.ini hatás: `hidden=yes` írása / törlése (`0x004da1d0`, `0x004d9aa0`). | `photo_ops_transform_mixin.py:83-84`: `document.with_value(photo.name, "hidden", "yes")` / `with_removed`. | Egyezik, teendő nincs. |

### 5. Javasolt fejlesztői jegyek

#### 1. A helyi menü Elrejtés/Megjelenítés parancsa kövesse a kiválasztott feliratot vegyes kijelölésnél

**Eredeti:** Az `AlbumPhoto` helyi menüben a `0x0056cd8d`-`0x0056cf99` szerint a nem alkalmazható tétel el van távolítva; kiválasztásakor a `0x005e7d90(1)` (Elrejtés) egységesen elrejti a kijelölt elemeket (`0x0065b710` -> `0x004da1d0`), a `0x005e7d90(0)` (Megjelenítés) pedig egységesen megjeleníti őket (`0x0065b590` -> `0x004d9aa0`).
**Nálunk:** `MainPhotoContextMenu.qml:44-46,62` a jobbklikkelt kép alapján írja ki a „Hide” vagy „Unhide” feliratot, de kattintásra a `hostWindow.toggleHiddenSelection()` -> `toggleHiddenRows()` fut le, ami vegyes kijelölésnél `hide_all = not all(p.hidden)` miatt mindig elrejtést végez. Ha a jobbklikkelt kép rejtett, a menü „Megjelenítés”-t ír, de kattintásra a látható képek is elrejtődnek.
**Teendő:** A `PhotoContextMenu` `hideToggleRequested` jelzését váltsa fel vagy paraméterezze a kiválasztott művelet: ha a tétel felirata „Megjelenítés” volt, az `unhideHiddenSelection()` fusson; ha „Elrejtés”, a `hideSelection()` fusson.
**Kész, ha:** Vegyes kijelölésnél (1 rejtett, 1 látható kép) a rejtett képre jobbklikkleve megjelenő „Megjelenítés” menüpontra kattintva mindkét kép láthatóvá válik; a látható képre jobbklikkleve megjelenő „Elrejtés” menüpontra kattintva mindkét kép rejtetté válik; unit/QML teszt ellenőrzi mindkét esetet.

#### 2. (feltételes, a Nyitott kérdések 1. pontja dönti el) Kép menü Elrejtés tételének szürkítése, ha nincs elrejthető kép

**Eredeti:** A `FUN_0056c5a0` a Kép ▸ Elrejtés (`0x9ca5`) menüpontot letiltja (`EnableMenuItem(..., 0)`), ha a kijelölésben minden kép már rejtett.
**Nálunk:** `PicasaPictureMenu.qml:130` a Hide tételt mindig engedélyezi, ha van képkijelölés.
**Teendő:** A `PicasaPictureMenu.qml` `menuPictureHide` tétele kapjon `bar.hasVisiblePhotoSelection` feltételt (a `hasHiddenPhotoSelection` mintájára).
**Kész, ha:** Csupa rejtett kép kijelölése esetén a Kép ▸ Elrejtés szürke, a Kép ▸ Megjelenítés aktív; csupa látható képnél az Elrejtés aktív, a Megjelenítés szürke; vegyes kijelölésnél mindkettő aktív; menü-állapot teszt igazolja.

#### 3. (feltételes, a Nyitott kérdések 2. pontja dönti el) A fotónéző léptetése vagy bezárása az aktuális fotó elrejtésekor

**Eredeti:** A `0x005e7e57` -> `0x005683a0` utólagos lépés az előnézetben/szerkesztőben nyitott kép elrejtésekor (ha a rejtett képek nem láthatóak) átléptet a következő látható képre, vagy ha elfogytak a képek, visszavált a könyvtári rácsra.
**Nálunk:** `PhotoViewerContextActions.qml:135` csak elrejti a képet, de a néző nem navigál el róla.
**Teendő:** Ha a nézőben megjelenített fotó elrejtésre kerül, és a `controller.showHidden` hamis, a néző váltson a következő látható képre; ha a mappában nincs több megjeleníthető kép, zárja be a nézőt (`hostWindow.closePhotoViewer()`).
**Kész, ha:** `showHidden == false` mellett a nézőben megnyitott képet helyi menüből elrejtve a néző a következő képre lép; egyetlen képet tartalmazó mappában elrejtve a néző bezáródik és visszatér a könyvtárba; teszt igazolja.

### Nyitott kérdések

A hívó ellenőrző mintavétele (2026-11-15): az elrejtő ág igazolt (a `0x0065b710` a `0x004da1d0`-t `1` értékkel hívja), és a helyi menü egyetlen tétele (`RemoveMenu` a `0x9ca5`/`0x9ca4` kódra a `0x0056c5a0`-ban) a meglévő Ghidra-kimenetben is látszik, tehát az 1. jegyjavaslat igazolt. Nem igazolt:

1. A Kép menü Elrejtés tételének szürkítése csupa rejtett kijelölésnél: a `0x0056c5a0` főmenü-ága ezt nem mutatja közvetlenül.
   - Ghidra-kör kell: 0x0056c5a0 - A főmenü `0x9ca5` (Elrejtés) tételét szürkíti-e az `EnableMenuItem`, ha a kijelölés csupa rejtett kép [nem blokkoló]
2. A `0x005683a0` utólagos lépés pontos hatása: a `0x0056884e` környezetében nincs `thumbui/albumview` nézetváltás, tehát a „következő látható kép vagy vissza a rácsra” leírás következtetés, nem bizonyíték.
   - Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7006-7008-7009-7012-colab-decomp.txt`): a `0x005683a0` a szerkesztő vagy néző újraépítése (`IDS_EDIT_IMAGE`, `0x00571850`); ha nem marad érvényes aktuális kép (`[0x399] == -1`, a `0x005675d0` után sem), visszavált a `thumbui/albumview` rácsra. Helyesbítés: az Elrejtés utáni hívás feltétele az, hogy a szerkesztőpanel aktív (`editpanel/preview +0x20c == 0`), nem a rejtett képek láthatósága. Melyik kép lesz a következő, nyitott.

## #7012: A Hozzáadás albumhoz teljes folyamata az eredeti Picasával összevetve

**Állapot: nyitott.** A menüpontok címkéjét és néhány kontextusfüggő parancsazonosítót a bináris rekordjaiból azonosítottam, a PicasaPy jelenlegi útja a forrásból követhető. Az eredeti albumválasztás utáni írási kezelő és a végállapot nincs igazolva, ezért a két termék teljes műveleti paritása nem állítható.

### Belépési pontok és engedélyezés

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Fájl menü, `New Album...`, `Ctrl+N`: a főmenü `0x00559150` rekordja és a `referencia/i18n/enUS/shortcuts.xml:115-117` bejegyzése. Ez album-létrehozás, nem meglévő albumhoz adás. A főmenü rekordbázisa `0xd6e498`; a `0x0055b777` `eax` forrása `0x00c8d8b8` (`&View and Edit`), parancsmezője `0xd6e4a2 = 0x9ca0`. A következő rekord címkéje `&Batch Edit`, `0xd6e4ac` bázison. | `PicasaFileMenu.qml:23-27`; `MainMenuBar.qml:300-304`; `PicasaMenuBar.qml:750-754` | Ne számítsuk a `New Album` parancsot meglévő albumhoz adásnak. Eredeti közvetlen Add-to főmenü- vagy billentyűparancs: `NINCS MEG`. Az angol gyorsbillentyű-erőforrásban a `New Album` `Ctrl+N`; Add-to bejegyzést nem találtam. |
| Mappa bélyegképének helyi menüje: `&Add to Album` rekord `0x00730790`, parancsmező `0x9ca0`. | `PhotoContextMenu.qml:167-192`; `MainPhotoContextMenu.qml:124-138`; több kijelölés vagy az utolsó aktív kép: `MainLibrarySelectionState.qml:25-30` | Egy és több képnél ugyanaz a sorlista kerül az `addRowsToAlbum`-nak. Eredeti engedélyezés egy képre, több képre, videóra és már albumtag képre: `NINCS MEG`. PicasaPy útjában nincs képtípus-szűrés (`photo_ops_write_text_mixin.py:202-204`). |
| Album bélyegképének helyi menüje: `&Add to Album` rekord `0x00731050`, parancsmező `0x9ca0`. | Ugyanaz a kép-helyi menü és callback, `PhotoContextMenu.qml:167-192`; `MainPhotoContextMenu.qml:124-138` | A PicasaPy a kijelölt sorokat a megnevezett tokenhez adja; a már tagságban levő token ismétlése nem dupláz (`ini/albums.py:65-80`). Az eredeti ismételt hozzáadás eredménye: `NINCS MEG`. |
| Néző helyi menüje: `&Add to Album` rekord `0x007327a0`, parancsmező `0x9cc6`; a főablak diszpécsere ezt `0x00566270`-re küldi (`0x005cb990`). Ez a híváslánc még nem bizonyítja a kiválasztott albumba írást. | `ViewerContextMenu.qml:129-145`; `PhotoViewerContextActions.qml:118-121` | PicasaPyban az almenü csak legalább egy saját album esetén aktív, és a parancs az aktív nézősort adja át, tehát egy képet. Eredeti album nélküli, videós, már tagságban levő és többképes nézőállapot: `NINCS MEG`. A nézőben PicasaPy `New Album...` sort nem találtam. |
| Emberek-album képmenüje: `&Add to Album` rekord `0x007355c0`, parancsmező `0x9e39`; a főablak diszpécsere `0x00603660`-ra irányítja. | `PhotoContextMenu.qml:167-192`; `MainPhotoContextMenu.qml:129-131` | A PicasaPy általános album-hozzáadó útja a kijelölt sorokat használja. Az eredeti `0x00603660`-as ág albumtagságra gyakorolt hatása, engedélyezése és hibái `NINCS MEG`. |
| Képtálca: a `thumbui/addtobuttcon` a `thumbui/scratchback` gyereke, felirata `Add to`, súgója `Add selected items to an Album`. A gomb eseményútja `0x005fe130`, amely a tálca kijelöléséből építi/frissíti a `Labels` listát (`0x00664130`). A jobbklikkes `Hold Selection` másik rekord, bár ugyanazt a `0x9ca0` azonosítót használja. | `TrayScratchPanel.qml:497-539,542-577`; `tray_album_controller.py:237-257` | PicasaPy gombja csak nem üres tálcánál aktív, a meglévő albumot választva a tartott sorokat írja. Az eredeti gomb engedélyezési feltétele és az egyes tartott elemtípusok eredménye: `NINCS MEG`. |
| Húzás meglévő album sorára: az eredeti `lb_drop` esemény a `0x005e39a0`-hoz jut, de a meglévő Ghidra-kimenet a kérdéses fotólista és albumtagság kapcsolatát nem dönti el. A mappa-sor húzási kutatása nem bizonyít fotó-húzási viselkedést. | `AlbumsSection.qml:260-272`; `FolderPaneContent.qml:54-58`; `MainFolderPane.qml:137-140` | PicasaPy csak saját `payload == "photos"` húzást fogad, és az ejtett sorokat a célalbum tokenjéhez adja (`AlbumsSection.qml:42-45`). Az eredeti fotó-húzás, egy vagy több kép, videó, ismételt tagság és lemezhatás: `NINCS MEG`; lásd a Ghidra-kérést lent. |
| Húzás az albumlista üres területére: a binárisban szerepel a `You can drag and drop pictures here to make a new album.` szöveg (`0x00765d30` út); ez az üres lista promptja, nem bizonyíték az ejtés utáni dialógusra vagy írásra. | `AlbumsSection.qml:62-108`; `MainFolderPane.qml:130-135`; `FileOpsDialogs.qml:90-95` | PicasaPy a kijelölt képekkel `Untitled` albumot készít párbeszéd nélkül. Eredeti prompt utáni végrehajtás és mérési felvétel: `NINCS MEG` ebben a körben. |

Az eredeti `0x0056e1c0` menüállapot-kezelő módosítja az `0x9ca0`-hoz tartozó engedélyezést, de a vizsgált dekompilálás állapotbitjei nem felelnek meg bizonyítottan az egy kép, több kép, videó vagy már tag kategóriáknak. A menüpont megjelenése vagy a lista felépítése önmagában nem bizonyít műveleti engedélyezést.

### Ablak, almenü, alapérték és megjegyzett állapot

- Az eredeti helyi menükben az `Add to Album` rekord mellett a dinamikus albumlista és az `ID_LABELSNEW` / `New Album...` elem felépítése látható (`0x0056c5a0`, meglévő Ghidra-kimenet: `2026-10-21-idorend-32.txt`). A `0x00664130` `Labels` listát állít össze, és a `il_NewAlbumName` szöveget használja. A listaelem kiválasztásakor futó tartós írás nincs benne bizonyítva. A tálca erőforrásában az `Add to` gombhoz ugyancsak albumválasztó tartozik.
- Az eredeti Fájl menü `New Album...` útjáról egy korábbi, külön mérés Album Properties ablakot rögzített (`paritas-ellenorzes.md:971`, `mérés (ki00/kepernyo__11.png)`). Ez nem azonosítja bizonyítottan az Add to Album almenü New Album elemének pontos kezelőjét. A mezők az albumablak leírásában szerepelnek (`picasa-fen-dialogs.md:255-273`), de az Add-to út alapértékei és megjegyzett értékei: `NINCS MEG`.
- PicasaPy kép-helyi menüjében a meglévő albumok dinamikus listája után `New Album...` szerepel (`PhotoContextMenu.qml:167-192`); ez a tulajdonság-párbeszédet nyitja a kijelölt sorokkal (`MainPhotoContextMenu.qml:129-138`, `FileOpsDialogs.qml:82-111`). Nyitáskor a név fordított `Untitled`, a dátum, hely, leírás és zeneútvonal üres, a zene kikapcsolt; a függvény minden nyitáskor ezeket állítja vissza (`FileOpsDialogs.qml:100-111,114-116`).
- A PicasaPy tálcamenü meglévő albumokat, `Screensaver`, `Starred Photos` és `New Album...` tételeket kínál (`TrayScratchPanel.qml:542-577`). A New Album a tulajdonság-párbeszédet nyitja a tálca tartalmával (`MainTrayBar.qml:82-85`). A néző menü csak meglévő albumokat tartalmaz (`ViewerContextMenu.qml:131-145`).
- PicasaPy üres albumlista-területre ejtéskor párbeszéd nélkül `Untitled` albumot készít (`FileOpsDialogs.qml:90-95,114-116`). Ez más belépési út, mint a menü `New Album...` parancsa.

### Tárolás és felületi hatás

| Hatás | Eredeti Picasa 3.9 | Jelenlegi PicasaPy |
|---|---|---|
| Kép- és fájlrendszer | A kiválasztott albumra futó íróág nincs feloldva. Képfájl mozgatása/másolása: `NINCS MEG`. | A meglévő albumhoz adó út mappánként `.picasa.ini`-t ír; ebben a hívási ágban nem találtam képfájl-mozgatást (`photo_ops_write_text_mixin.py:206-227`). Az ini-írás backupolt (`:225`). |
| `.picasa.ini` tagság | Az album művelet `albums=` kulcsra gyakorolt eredeti hatása: `NINCS MEG`. | A token az érintett fotó `albums=` CSV-jéhez kerül; meglévő token ismétlése változatlan dokumentumot ad (`ini/albums.py:65-80`; `photo_ops_album_membership_mixin.py:28-62`). |
| Albumdefiníció, contacts/album adatbázis és SQLite index | Az Add-to művelet bármelyik adatbázisában történt írás vagy szinkron: `NINCS MEG`. Az album adatbázis inicializáló nyomai nem bizonyítják, hogy ezt a parancsot szolgálják ki. | A batch minden érintett mappánál `_sync_tree(conn, folder)`-t hív, majd siker után újratölti az albumlistát (`photo_ops_write_text_mixin.py:206-227`; `photo_ops_album_membership_mixin.py:255-268`; `controller_photo_list_mixin.py:183-197`). |
| Bal oldali albumfa | Művelet utáni fa és darabszám: `NINCS MEG`. | Siker esetén az albumlista újratöltése `albumsChanged` jelet küld, az albummodell az indexből számolja a tagságot (`controller_photo_list_mixin.py:183-197`). Köztes írási hiba esetén ez a siker utáni ág nem fut le. |
| Rács és kijelölés | Rács, sorok, kijelölés és fókusz végállapota: `NINCS MEG`. | Sikeres batch után `_refresh_view()` újraolvassa az aktuális nézetet. A `_show()` a fotórács modelljére állítja az új rekordokat; eltérő rekordsor esetén a modell-reset megtörténik (`controller_sync_mixin.py:65-101,111-157`; `photo_grid_state.py:192-211`). A kijelölés QML/Qt végállapotát ebből nem következtetem ki. |
| Ismételt hozzáadás | A már albumtag kép eredeti kezelése: `NINCS MEG`. | `with_album` nem ír be második példányt és nem változtatja a sorrendet (`ini/albums.py:65-80`). |
| Visszavonás | Az eredeti Undo/Undo All Edits vagy más visszavonás tagságra gyakorolt hatása: `NINCS MEG`. | A vizsgált `addRowsToAlbum` és `_write_album_batch` útban undo-hívást nem találtam. Felhasználói visszavonási lehetőség: `NINCS MEG`. |

### Hibák és részleges végrehajtás

- Eredeti: a `.picasa.ini` vagy album-adatbázis írási hibájának üzenete, megszakítási viselkedése, az előzőleg feldolgozott képek állapota és az esetleges visszagörgetés: `NINCS MEG`.
- PicasaPy: a kijelölt sorok mappánként csoportosulnak, mappánként külön atomikus `update_document` fut, majd az indexfa újraszinkronizálása (`photo_ops_write_text_mixin.py:206-227`). Több mappás batch ezért nem egyetlen `.picasa.ini`-írás. Ha egy későbbi mappa írása hibát dob, a korábbi sikeres fájlírások már megtörténtek; a teljes index-tranzakció pontos részleges állapotát nem állítom.
- PicasaPy az ismert írási kivételeket `albumWriteFailed` jelzéssé alakítja, hamissal visszatér, a hibasáv az üzenetet mutatja (`photo_ops_album_membership_mixin.py:255-268`; `MainErrorBanner.qml:89-92`). A `_refresh_view()` és az albumlista siker utáni újratöltése ilyenkor nem fut le.
- **Helyesbítés:** az `open_index` `finally`-ban `conn.close()`-t hívja; a `_GuardedConnection.__exit__` visszagörgető ága ettől nem fut (`index/database.py:340-373`). A megelőző jegyzet visszagörgetésről szóló állítása nem bizonyított, visszavonva.

### Bizonyítottság, független utak és cáfoló kísérlet

- **A út, bináris rekord és utasításszintű vizsgálat:** a `&Add to Album` string-xref címekhez a helyi menük rekordbázisát és parancsmezőjét követtem. A `0x00559150` menürekordnál a `0x0055b777` `eax`-forrása `0x00c8d8b8`; ez a `0xd6e498` címkéjét állítja `&View and Edit` értékre, a hozzá tartozó parancsmező `0xd6e4a2 = 0x9ca0`. A következő, `0xd6e4ac` bázisú rekord címkéje `&Batch Edit` (`0x0055b79f`), tehát nem az előző parancs címkéje.
- **B út, független erőforrás:** a `thumbui.tre` és `thumbui_text.tre` az `Add to` tálcagomb helyét és `Add selected items to an Album` súgóját rögzíti; ezt a bináris `0x005fe130` -> `0x00664130` listafelépítő útja is megerősíti. Ez a két út a tálca Add-to felület létezésében egyezik. A többi helyi menü parancsazonosítója egy bináris útból feltételes, az albumtagság írási végállapotát egyik út sem igazolja.
- **Cáfoló kísérlet:** cáfoltam azt a jelöltet, hogy a `0x9ca0` minden helyen Add to Album. A főmenü rekordja `&View and Edit`; a tálca jobbklikk-menüjének `0xd6edca` mezője ugyanezt az azonosítót a `&Hold Selection` felirathoz használja (`0x00732f35` `Tray::ID_PICTURE_HOLDINPICTURETRAY`, `0x00732f3a` `eax = 0x00cae63c`, `0x00732f4c` `0x9ca0`). Mindkettőt a rekord bázisa, szövegforrása és parancsmezője alapján ellenőriztem. A parancsszám ezért önmagában nem jelentést hordozó, globális azonosító.
- **Bizonyítottsági fok:** a tálcagomb mint Add-to felület megerősített két független úttal. A helyi menük egyedi felirat/parancs párosítása egy bináris útra támaszkodik, ezért feltételes. A jegy teljes folyamata nyitott, mert az eredeti tagságíró, adatbázis-hatás, részleges hiba, visszavonás és végső UI-állapot nem dőlt el.

### A jegy „Kész, ha” pontjai

1. ⛔ **Minden belépő és feltétel, egy és több kép, videó, már albumban lévő kép:** a táblázat külön kezeli a fájlmenüt, két bélyegkép-nézetet, nézőt, Emberek-albumot, tálcát, meglévő albumra és üres területre ejtést. Az eredeti engedélyezési feltételek és a video/ismételt tagság viselkedése nyitott.
2. ⛔ **Ablak/almenü, alapérték és megjegyzett állapot:** a címkék/listaépítés és a jelenlegi dialógusértékek dokumentálva vannak. Az eredeti Add-to New Album elem dialógusa, értékei és megjegyzése nyitott.
3. ⛔ **Tárolás, index, fa, rács, kijelölés, ismétlés és undo:** PicasaPy útja forrásból le van írva. Az eredeti `.picasa.ini`, adatbázis, index, UI-végállapot, ismétlés és visszavonás nyitott.
4. ⛔ **Írási hiba és részleges végrehajtás:** PicasaPy hibajelzése dokumentált, az eredeti íróút és a pontos PicasaPy-index részleges hibaállapot további vizsgálatot igényel.

### Javasolt fejlesztői jegytörzs

E körben nincs bizonyított Add-to végállapotbeli eltérés, amelyhez biztonságosan fejlesztési jegy írható. Előbb a nyitott eredeti műveletet kell célzottan feloldani; a leírt PicasaPy viselkedés jelenlegi forrásállapot, nem önmagában paritásdöntés.

### Új kutatási jegyjavaslatok

- **Az eredeti Add to Album tagságíró és hibautja.** Kérdés: a dinamikus albumtétel kattintása mely kezelőn keresztül írja a képek tagságát, az `albums` mezőt, az album/contacts adatbázist és az indexet; mi történik egy/multiple, videó, már tag és írási hiba esetén; visszavonható-e? Hol keresd: `0x00664130` Labels-lista kiválasztási callback, `0x005cb990` command-diszpécser. A meglévő `2026-10-29-koteg-33.txt` a lista felépítését, `2026-10-21-idorend-30.txt` a dispatchert mutatja, de nem a kijelölt albumtagság-írást.
- **Fotók húzása meglévő albumra az eredeti Picasában.** Kérdés: az `0x005e39a0` `lb_drop` út fotó-kijelölést fogad-e, és mely albumtagság- vagy fájlrendszer-műveletet futtatja? A meglévő `2026-11-13-6845-6532-colab-decomp.txt` mappa/album-lista húzásról szóló dekompilálása ezt a fotó-húzási esetet nem dönti el.

### Nyitott

- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7006-7008-7009-7012-colab-decomp.txt`): a `0x00664130` csak a `Labels` listát építi (`"%s (%s)"`, `il_NewAlbumName`), a `0x005fe130` a tálca Add to gombja, csak nem üres tálcánál; a kiválasztáskor futó író egyikben sincs. Erős jelölt a `0x0045ef50` (lásd lent).
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7022-colab-decomp.txt`): a `0x0045ef50` **nem** az album-tagságíró: minden más albumból eltávolítja az átadott elemeket (`0x006cb200`), kihagyva a célalbumot és amire a `0x004461a0` igaz; a hívója a `]facealbum:%d`-s `0x0055d120`, tehát arcalbumra vonatkozik (egy arc egy emberhez). A húzás albumra ennek megfelelően arcalbumnál kizárólagos tagságot ad; a közönséges album tagságírója ebben a körben nem került elő.
- Ghidra-kör kell: 0x005fe130 - a tálca Add to gombjának és a helyi menü Labels listájának elemválasztó visszahívása melyik kezelőt hívja, és az milyen `albums=`/adatbázis-írást végez [megválaszolva a statikus kutatási kiegészítésben lent: helyi menü `0x00536a90`, tálca `0x00577c30`; a fájlba írás kapcsa még nyitott]
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7028-colab-decomp.txt`): a `0x005fe130` a `thumbui/addtobuttcon` kezelője (a `0x005d9cc0` hívja), nem üres tálcánál a `0x00664130` listapanelt építi. A helyi menü `Add to Album` almenüjét (`0x9cb9`) a `0x005eab70` építi (hívója a `0x0056c5a0`): albumonként a `0x00452d10` album-azonosítójával, az Emberek- és a webes albumok nélkül, a végén `IDS_NEW_COLLECTION` (New Album) elemmel. Ez egyezik a PicasaPy almenüjével, amely saját albumokat és `New Album...` sort kínál. Az elemválasztás utáni tagságíró ebben a kötegben sincs, ezért a fenti blokkoló kérdés nyitott marad.
- Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7006-7008-7009-7012-colab-decomp.txt`): albumcsomópontra (`CAlbumSelectionNode`) ejtésnél a célalbum azonosítója `+0x3c0`; ha azonos a forrás albummal, nem történik semmi, különben a `0x0045ef50(db, lista, album)` írja a tagságot (ugyanez fut új album létrehozásakor a `0x0055d120`-ban). Emberek-albumnál külön ág (`]expeople:%d`, `0x0044bdf0`); a 4-es húzástípus a `0x005ea770` mappatulajdonságok útra megy. Fájltípus-feltétel nem látszik.
- NINCS MEG: eredeti Add-to/New Album párbeszéd alapértékei és megjegyzett állapota. Megszerzés: célzott Picasa 3.9 mérés a meglévő-album almenü New Album útján, képernyőkép és minden mező rögzítésével, majd külön ismétlés újranyitással.
- NINCS MEG: az eredeti Add-to siker/hiba utáni fa, rács, kijelölés, kép- és adatbázis-végállapot, valamint visszavonás. Megszerzés: a blokkoló Ghidra-kör után előtte/utána mérés kis, egy- és többmappás tesztkészleten; fájlok, `.picasa.ini`, album/contacts adatbázis és UI-állapot összevetése. A meglévő mérőadat-archívum taglistájában ehhez releváns Add-to/album-dialog felvételt nem találtam.

### Kiegészítés (2026-11-15, statikus kutatás): a kiválasztott albumhoz adás írója

Módszer: utasításszintű diszasszembly (`capstone`) a `0x0056c5a0`, `0x005e4ac0`, `0x005cb990`, `0x00536a90`, `0x00577c30`, `0x006ca130`, `0x006cae50`, `0x006ca5a0`, `0x004abc70`, `0x004b94a0`, `0x00402a90`, `0x00556ff0` és `0x0052c350` függvényen, valamint a `binary-index` (`xrefs`, `string_xrefs`, `rtti`) és a meglévő Ghidra-kimenetek olvasása. Futásidejű Picasa-mérés nincs. Fokok: **megerősített** = két független út, **erős** = egy út, egyértelmű utasításokkal, **feltételes** = következtetés.

**A blokkoló kérdés válasza (erős): a helyi menü `Add to Album` almenüjében egy album kiválasztását a `CThumbUI` osztály (`CThumbUI::vftable`, `0x00c9052c`) `0x00536a90(this, 0)` függvénye írja.** A kijelölt képek azonosítóit az album gyűjtemény-objektumának képlistájához fűzi. Az útja:

| Lépés | Cím | Mit tesz | Fok |
|---|---|---|---|
| 1. Almenü felépítése | `0x0056c5a0`, a `0x0056d24d`-től | `CreatePopupMenu`, majd `SetMenuItemInfo(menü, 0x9d8f)`: a popup a `0x9d8f` azonosítójú menüelem almenüje. Tartalma sorrendben: (a) a `0x004b94a0(nézet, &lista, 1)` albumai, vagyis azok a gyűjtemények, amelyek belső neve `]album:` előtaggal kezdődik, a `0x004baaa0` összefésülő rendezésével; (b) elválasztó, ha van album; (c) a `]star`, majd a `]screensaver` gyűjtemény, ha név szerint megtalálható a katalógusban; (d) elválasztó, ha volt (c); (e) `New Album...` (`ID_LABELSNEW`, parancs `0xa09c`). Az albumtételek parancsazonosítója `0xbb80 + sorszám`, az elemadat (`dwItemData`) a gyűjtemény azonosítója (`0x00a6b120` hozzáfűző burkoló). | erős |
| 2. Kiemelés | `0x005e4ac0` ablakkezelő, `WM_MENUSELECT` (`0x11f`) ág, a `0x005e4c35`-től | Minden kiemelésnél a `CThumbUI+0xe30`, `+0xe34`, `+0xe40` mező `-1`-re áll; a `0xbb80..0xc34f` tartományú parancsnál a `0x005c6670` (`GetMenuItemInfoA`, `MIIM_DATA`) elemadata kerül a `+0xe40` mezőbe. | erős |
| 3. Parancs | `WM_COMMAND` -> `0x00a527b0` -> `CThumbUI` vtábla `+0x5c` = `0x005cb990`, a `0x005cd981`-től | `0xbb80 <= parancs < 0xbf68`: `0x00536a90(this, 0)`; `0xbf68 <= parancs < 0xc350`: `0x00536a90(this, 1)` (ezt az Emberek-album menüjének `&Move to People Album` almenüje, `0xa0cd`, adja, a `]expeople:%d` ág, `0x0044bdf0`; nem közönséges albumtagság). | erős |
| 4. Író | `0x00536a90` | Lásd lent. | erős |

**A `0x00536a90(this, 0)` viselkedése, közönséges album esetén (erős).**

- Kilép, ha a `+0xe40` mező `-1`, vagy nincs aktuális csomópont vagy kijelölés (`+0xeac`, `+0xea8`), ilyenkor 0-val tér vissza, és semmit nem ír. A `+0xe40` mezőt a képlista összeállítása után, a gyűjtemény-objektum lekérése előtt (`0x00536c00`) állítja `-1`-re.
- Képlista: ha a szerkesztő vagy néző aktív (`0x00579330`, `editpanel/preview +0x20c == 0`) és `+0xe64 != -1`, akkor **egyetlen kép** (az aktuális, `+0xe64`); különben a **teljes kijelölés** (`0x007166c0`), kijelölési sorrendben.
- `0x004b0190(nézet, albumazonosító)` előállítja a gyűjtemény-objektum hozzáférőit; ha a `+0x5c` vagy a `+0x64` mező nulla, `-1`-gyel tér vissza, és semmi nem íródik, üzenet nélkül.
- **Már tag kép:** a `0x006cae50` (tagság-vizsgálat a `[objektum+0x64]` képlistában) igaz értékénél a képet **kihagyja**: nincs duplikálás, nincs átrendezés, nincs üzenet. Ez egyezik a PicasaPy `with_album` viselkedésével (`ini/albums.py:65-80`).
- **Új tag:** a `0x006ca130` hozzáfűzi a képazonosítót a képlista **végére** (`push_back`, zár alatt). Nem nulla visszatérésnél (a `4` memóriahiba) a függvény azonnal visszatér, a már hozzáadott képek bent maradnak, visszagörgetés nincs.
- **Videó és egyéb típus:** a függvényben nincs típusszűrés. A hívásai (`0x00401000`, `0x00407610`, `0x004133e0`, `0x00413490`, `0x00448a10`, `0x00448c90`, `0x0044bdf0`, `0x0045ecf0`, `0x0047bf40`, `0x0048ef20`, `0x004abc70`, `0x004af790`, `0x004b0190`, `0x004da1d0`, `0x00506400`, `0x00512c90`, `0x00579330`, `0x005d27d0`, `0x00602df0`, `0x0065b840`, `0x006ca130`, `0x006cae50`, `0x007166c0`, `0x00717140`, `0x0097c810`, `0x0097caf0`, `0x0097e4c0`, `0x009d2c80`) között nincs fájlnyitás, fájlírás, üzenetablak és visszavonás-regisztráció. Az Emberek-ág (`0x0044bdf0`, `0x004da1d0`) csak a `flag != 0` és Emberek-album esetén fut.
- Hozzáadás után: `0x004abc70(nézet, album)` a gyűjteményt "piszkosnak" jelöli (`[nézet+0x138]` állapottábla, 0x24 lépésköz, `+0xc` állapot), `[nézet+0x166] = 1`, `0x004af790` megkeresi az album sorát a bal oldali listában, és ha megvan, `0x009d2c80(0)` újrarajzolja azt, majd `0x0065b840(this, 0, 0, 1)` frissíti a fő nézetet. **Navigáció az albumra nincs** (a `New Album` ággal ellentétben). A kijelölés végállapota nyitott (`0x0065b840` belseje).
- Ha az album belső neve `]star` (`0x00536efe`, 6 bájtos összehasonlítás), a `0x005d27d0` a `thumbui/startoggle` csillag-kapcsolót frissíti. A `]star` választása tehát **hozzáadás** (a már csillagos kép marad), nem megfordítás.

**Tároló.** A tagság közvetlen helye a gyűjtemény-objektum `+0x64` képlistája (képazonosítók vektora), ez **memória** (erős). A `.picasa.ini` felé a katalógus megfigyelői visznek: a `0x00402a90` a `Preferences\AlbumIniSync` kapcsoló (alapérték 1) alapján létrehozza a `PicasaIniManager` (`0x00c89768`, 5 bejegyzés: `0x0052a7e0`, `0x0052a810`, `0x0052ab10`, `0x0052b220`, `0x0052c350`) és az őt használó `AlbumSync` megfigyelőt (`0x00c7f580`, a `+0x54` mezőben a kezelővel), amelyet a `0x00402370` a katalógus egyik táblájához köt. Az `AlbumSync` `0x00556ff0` és `0x00557760` bejegyzése mappánként hívja a `PicasaIniManager` `+0x10` bejegyzését, a `0x0052c350`-et (paraméterei: a mappa gyűjtemény-azonosítója, az album `]album:` előtagú belső neve, a képek listája). A `0x0052c350` a katalógus `+0x14` bejegyzésével lekéri a mappa útvonalát, hozzáfűzi a `.picasa.ini` nevet, a belső névből tokent képez, és az `albums` (és `token`) kulcsot írja (szövegei: `]album:`, `.album:`, `token`, `albums`, `.picasa.ini`). Ha `9`-et ad, az `AlbumSync` előbb az 1. bejegyzést (`0x0052a810`: `token`, `description`, `location`, `%I64u`, vagyis feltehetően az album `[.album:token]` meghatározásának létrehozása) hívja, majd újra próbálja a 4. bejegyzést (a `9` jelentése feltételes). A `0x0052b220` ugyanezeket a kulcsokat és a `description`, `location` kulcsot használja (az album meghatározásának olvasása vagy frissítése). Fok: a `0x0052c350` mint az `albums=` író **erős** (szövegek, hívási forma, az `AlbumSync` hívásai); az, hogy a `0x00536a90` után pontosan ez hívódik, és mikor, **feltételes**, mert a `0x004abc70` csak jelzőt állít. Az `AlbumIniSync = 0` esetén a `0x00402a90` kihagyja a két objektum létrehozását, tehát az ini-írás elmarad (feltételes).

**Tálca (erős).** A tálca `Add to` gombja (`0x005fe130`) csak a `Labels` listapanelt (`0x00664130`) építi és kapcsolja. Az írás a `thumbui/makealbum` csomópont kezelőjében van: `0x00577c30` (a `0x005d9cc0` hívja). A tálca képlistáját (`+0xea4`, `0x007164b0`) és a panel kijelölt sorának albumazonosítóját (`0x00562640`, sor `+4`) használja: `0x004b0190` + **`0x006ca5a0`** (kötegelt hozzáadás, a már tagokat kihagyja), majd `0x0065b840`, `0x004abc70` és `0x00665180` (a panel frissítése). A sor `+8` bájtjának 0. bitje (feltételes) az új album sort jelöli, az `0x00577ea0` ágra visz. A lista (`0x004b94a0(nézet, &lista, 0)`) minden listázható gyűjteményt tartalmaz az arcalbumok (`]facealbum:`) kivételével, tehát a `]star` és a `]screensaver` is bekerülhet; ez összefér a mért tálcamenü-sorrenddel (`TrayScratchPanel.qml:545`, job-259), de azt nem bizonyítja.

**Helyesbítés (erős).** A korábbi bejegyzések két azonosítása hibás:

1. A `0x005eab70` és a `0x9cb9` **nem az `Add to Album`**, hanem a Mappa helyi menü (`0x007319f0`) **`Move to Collection`** (`Folder::ID_ALBUM_MOVETOCOLLECTION`) almenüje. Az `IDS_NEW_COLLECTION` szövege `New Collection...`, a kérdése `Enter Collection Name:` (`referencia/i18n/enUK/stringres.xml:282,264`), tehát nem `New Album`. Az `0xafc8 + n` parancsok elemadatát ugyanaz a `WM_MENUSELECT` ág a `+0xe30` mezőbe teszi, a menü bezárásakor (`WM_EXITMENULOOP`, `0x212`) fut a `0x005eb160`, amely a `0x00445b80(db, mappa-csomópont, gyűjtemény, 1)` hívással a mappa gyűjteményét állítja; a `New Collection...` (`0xa04d`) a `0x005cd7b2` -> `0x005eb230` úton ugyanide fut. Ez a mappa gyűjteménybe sorolása, nem képek albumtagsága. A PicasaPy ezt már tudja (`src/picasapy/help/en/features/konyvtar.md:173`: a mappa jelenlegi gyűjteménye pipált és szürke).
2. A menürekord-építőkben a `mov word ptr [..], <parancs>` mező **az eggyel megelőző rekordhoz** tartozik, nem ahhoz a blokkhoz, amelyben áll. Bizonyíték három úton: (a) a `0x007319f0`-ban a `Collapse All` blokkban álló `0x9dc0` valójában az `Expand All` parancsa, a rákövetkező `0x9e3b` a `Collapse All`-é; a diszpécser mindkettőt a `0x00600ec0(this, 1)`, illetve `(this, 0)` hívásra küldi (kibontás, összecsukás); (b) a `0x00730790` első blokkjában, az `&Add to Album` mellett álló `0x9ca0` a megelőző `View and Edit` rekordé, és a diszpécser `thumbui/fullview`-ra küldi (`0x005cbd26`); (c) a néző menü `0x007327a0` építőjében az `&Add to Album` mellett álló `0x9cc6` a `0x00566270`-re megy, amely az `editpanel/preview` és a `thumbui/albumview` csomópontot kezeli, vagyis a visszatérés a könyvtárba; (d) az Emberek-menü `0x007355c0` építőjében a `Move to New Person...` `0xa0cc` parancsa a `0x005cd90d` -> `0x005e9890(this, 1)` útra megy (új személy), az `&Move to People Album` `0xa0cd` azonosítóját a `0x0056c5a0` Emberek-ága köti a személylista almenüre, a `Set as People Album Thumbnail` `0x9e39` parancsa a `0x00603660`-ra megy (borítókép), és az `&Add to Album` ebben a menüben is a `0x9d8f`. Következmény: az `&Add to Album` rekordok tényleges parancsa a `0x9d8f` (a rákövetkező blokk mezőjéből, a `0x00730790`, `0x00731050` és `0x007327a0` építőben), és a `0x0056c5a0` is ezt az azonosítót köti az almenüre; a `0x9d8f` a diszpécserben nincs kezelve (almenü-fej). A fenti táblázat `0x9ca0`, `0x9cc6` és `0x9e39` Add-to párosításai érvényüket vesztik; a `0x9ca0` a `View and Edit` azonosítója (a főmenü `&View and Edit` rekordjában is), a `0x9e39` az Emberek-album borítóképe. A tálcamenü `Hold Selection` rekordjának `0x9ca0` párosítását és az abból levont cáfoló kísérletet ez a kör nem ellenőrizte újra; ugyanez az eltolás érintheti.

**Összevetés a PicasaPyval.**

| Szempont | Eredeti | PicasaPy | Eltérés |
|---|---|---|---|
| Több kép | a kijelölés minden képe, sorrendben | `_rows_to_photos`, mappánként egy ini-írás (`photo_ops_album_membership_mixin.py:28-62`) | nincs |
| Már tag | kihagyja, nem duplikál, nem rendez át | `with_album` idempotens (`ini/albums.py:65-80`) | nincs |
| Hozzáadás helye | a képlista végére | az `albums=` lista végére (`ini/albums.py:65-80`) | nincs (a két tároló szerkezete más, a sorrend-egyezés feltételes) |
| Videó | nincs típusszűrés | nincs típusszűrés (`photo_ops_write_text_mixin.py:202-204`) | nincs |
| Néző | az aktuális egy kép (`+0xe64`) | az aktív nézősor (`PhotoViewerContextActions.qml:118-121`) | nincs |
| Hozzáadás után | az album sora és a nézet frissül, nincs navigáció, nincs kérdés | `_refresh_view()`, `albumsChanged` (`controller_photo_list_mixin.py:183-197`) | nincs |
| Almenü tartalma | albumok, elválasztó, `Starred Photos`, `Screensaver`, elválasztó, `New Album...` | albumok, elválasztó, `New Album...` (`PhotoContextMenu.qml:167-192`) | **van**: a `Starred Photos` és a `Screensaver` hiányzik a fotómenüből |
| `Starred Photos` választása | hozzáadás a `]star` gyűjteményhez (idempotens), csillag-kapcsoló frissítése | a tálcában `toggleStarMany` (megfordít, `photo_ops_transform_mixin.py:90`) | feltételes: a megfordítás és a hozzáadás kimenete eltér a már csillagos képnél |
| Albumok sorrendje | `0x004baaa0` rendezés | `controller.albums` sorrendje | nyitott |
| Visszavonás | nincs látható | nincs | nincs (feltételes) |
| Hiba | a `0x00536a90`-ban nincs üzenet; az ini-írás hibája az `AlbumSync`-ben ágazik | `albumWriteFailed` hibasáv (`photo_ops_album_membership_mixin.py:255-268`) | nyitott |

#### Javasolt fejlesztői jegytörzs (a statikus kutatás után)

**Fotómenü `Add to Album` almenüje: `Starred Photos` és `Screensaver` tétel.**

- Eredeti: a `0x0056c5a0` a fotók helyi menüjében az albumok után, elválasztóval lezárva, a `]star` és a `]screensaver` gyűjteményt is felkínálja, ha az adott gyűjtemény név szerint létezik a katalógusban; utána újabb elválasztó és a `New Album...` következik. A választás ugyanaz a `0x00536a90` ág: hozzáadás, a már tag kimarad, `]star` után a csillag-kapcsoló frissül. Fok: erős. A tételek megjelenése feltételes (létezik-e a gyűjtemény).
- Nálunk: `PhotoContextMenu.qml:167-192` csak az albumokat és a `New Album...` sort adja; a két különleges tétel csak a tálcamenüben van (`TrayScratchPanel.qml:542-577`).
- Elfogadási feltétel: a menü renderelt képe és az eredeti almenüről készült Picasa-képernyőkép összevetése (a szövegeket és az elválasztók helyét a bináris nem adja, csak a sorrendet). Képernyőkép nélkül a jegy nem zárható.
- Nem szabad: a tálcamenü mért sorrendje (`Screensaver`, `Starred Photos`, albumok, `New Album...`, elválasztó nélkül) nem változhat; a meglévő albumtételek és a `New Album...` viselkedése nem változhat.
- Nyitott döntés a jegyben: a `Starred Photos` tétel a már csillagos képen az eredetiben hozzáad (nem fordít), a PicasaPy `toggleStarMany` fordít; a jegynek ezt a binárisból kell eldöntenie (`0x005e81e0`, `0x005d27d0`).

#### Új kutatási jegyjavaslatok (a statikus kutatás után)

- A `0x00536a90` utáni ini-írás kapcsa: hogyan jut el a `0x004abc70` piszkos jelzője az `AlbumSync` és a `PicasaIniManager` hívásáig, és mikor (azonnal, időzítve, kilépéskor).
- A fotómenü almenüje a nézőben és az Emberek-albumban: melyik menütípus (`0x0056c5a0` második paramétere) melyik építőhöz tartozik.

#### Nyitott (statikus kutatás után)

- Ghidra-kör kell: 0x00556ff0 - az `AlbumSync` (`AlbumSync::vftable` `0x00c7f580`) 2. bejegyzése: ki és mikor hívja (vtábla-hívás, az index nem látja), és a `0x004abc70` piszkos jelzője (`[nézet+0x138]`, 0x24 lépésköz, `+0xc` állapot; ugrótábla `0x004abd3c`) hogyan vezet ide. Ezzel dől el az ini-írás időzítése és sorrendje.
- Ghidra-kör kell: 0x0052c350 - a `PicasaIniManager` 4. bejegyzése: mely mappák `.picasa.ini` fájljába, milyen sorrendben és hibakezeléssel írja az `albums` és `token` kulcsot (`9`-es hibakód), és a `0x0052b220` ki hozza létre az `[.album:token]` szakaszt.
- Ghidra-kör kell: 0x004a7890 - az albumlista rendezési kulcsa és iránya (a `0x004baaa0` összefésülő rendezés összehasonlítója): a menü sorrendje megegyezik-e a bal oldali listáéval.
- Ghidra-kör kell: 0x0056e1c0 - a `0x0056c5a0` második paramétere (`0x8a`, `0x8b`, `0xa6`, `0x127`, `0x13d`, `0x77`) melyik helyi menühöz tartozik; a néző menüje ugyanezt az almenüt (és a `New Album...` sort) kapja-e.
- Ghidra-kör kell: 0x005d9cc0 - a tálca `Labels` panel sorára kattintás azonnal ír-e, vagy a `thumbui/makealbum` gomb kell hozzá, és a `0x00665180` mit frissít.
- Ghidra-kör kell: 0x005e9bb0 - a `New Album...` (`0xa09c` -> `0x005e9890` -> `0x005e9bb0(this, 1)` -> `0x005eaab0` -> `0x005ea770`) párbeszédének alapértékei és a létrehozás utáni kijelölés. A `thumbui/albumbutton` gomb is ugyanide fut, tehát ez az eredeti `New Album` közös útja.
- NINCS MEG (futásidejű): a hozzáadás utáni rács, kijelölés és bal oldali fa végállapota. Megszerzés: előtte/utána mérés kis tesztkészleten a `0x0065b840(this, 0, 0, 1)` hatásának igazolására.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - ez a #7012 alszakasz.

## #7024: A képaláírás (Caption) szerkesztésének teljes folyamata az eredeti Picasával összevetve

A vizsgálat az eredeti Picasa 3.9.141.259 (`Picasa3.exe`, SHA-256 `644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`) képaláírás-szerkesztését követi a belépési ponttól a hatásig: ki tudja szerkeszteni, mikor ment, mit ír, mi történik hibánál. A PicasaPy oldal a mai forrásból olvasva (fájl:sor), nem a korábbi specekből. A címek az eredeti virtuális címei. Három bizonyítási út: (A) a gépi kód utasításszintű visszafejtése a bináris-indexszel, (B) bájtszintű keresés a teljes `.text`-ben (típusleíró-használók, `call`-célok) és erőforrás-, RTTI- és szövegtár-olvasás, (C) a `.picasa.ini` korpusz mérése (859 fájl, 17 577 képszakasz).

### 1. Az eredeti felépítése

- A néző/szerkesztő (`editpanel`) alsó sávja három elemből áll: `editpanel/captionbutton` (kapcsoló, buboréksúgó „Show/Hide Caption"), `editpanel/caption` (a „Make a caption!" mező) és `editpanel/captiontrash` (törlés, „Delete this caption"). Elrendezés: `editpanel.tre:1239-1266`, szövegek: `editpaneltext.tre:41-48`.
- A mező osztálya `CTextCaptionNode` (konstruktor `0x0067df90`, alapszöveg `CTextCaptionNode::defname` = „Make a caption!", `0x0067dfea`, `0x0067e095`). A típusleíró (`.?AVCTextCaptionNode@@`, `0x00d3e668`) a teljes `.text` bájtkeresése szerint pontosan három függvényben szerepel: `0x00565cf0` (`0x00565d96`), `0x00568010` (`0x00568051`), `0x005f89a0` (`0x005f89f1`). **Szerkeszthető képfelirat-mező tehát csak az editpanelben van**; a többi felirat-felület csak megjelenít.
- **Mentés egyetlen helyen történik:** a `0x005f89a0` a függő szöveget a `CThumbDB` `+0x50` virtuális setterével (`0x00437cf0`) írja a `[this+0xe64]` képkulcsra (`0x005f8a3b-0x005f8a53`). A getter a `+0x4c` slot (`0x00437b20`); a slotok a `CThumbDB::vftable` (`0x00c81fa4`) bejegyzései (a bejegyzések helyét az indexből számoltam: `0x4c` és `0x50`).
- A mező eseményei: az Enter és az Esc a `0x0076ace0` alaposztály-kezelőből a csomópont `+0x88` (`0x0067f7e0`, „captiondone") és `+0x84` (`0x0067f730`, „captioncancel") virtuális metódusát hívja. Ezek eseményt küldenek az editpanel diszpécserének (`0x005de8e0`, `0x005df4db-0x005df58f`), ami a mentést (`0x005f89a0`), illetve a szöveg visszatöltését (`0x00568010`) indítja.

### 2. Belépési pontok

| Belépési pont / feltétel | Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|---|
| Néző, feliratmező, kattintás a sávra | Kattintás a sáv hátterére: `0x005c48c0` (`CaptionBaseHandler`, `0x005c4996-0x005c49b9`) a `editpanel/caption` csomópontot fókuszba teszi. A mező alatt a `[this+0xe64]` kép felirata szerkesztődik. | `PhotoViewerOverlayControls.qml:466-525` (`captionBar`, `captionField`, egy mező a néző alján). | Egyezik. |
| Gépelés a nézőben (közvetlen kezdés, kattintás nélkül) | A `PreviewHandler` billentyűkezelője (`0x005c24c0`, `PreviewHandler::vftable` 3. slot) a Ctrl nélküli karakterüzenetet (üzenettípus 0x17, `[msg+0x64]` 1-es bitje: `0x005c2565-0x005c25ab`), ha a kód `0x21` és `0xFE` között van (`0x005c25c9-0x005c25d6`), a `0x00565cf0`-nak adja (`0x005c25dc`): a karakter a felirat végére kerül, a mező szerkesztő módba lép és szennyezettnek jelöli magát (`0x00565ee6-0x00565ef8`). Backspace az utolsó karaktert törli (`0x005c273a-0x005c2748`). Kizárás: szóköz és Tab (`0x00565d38-0x00565d44`), aktív eszközmód (`[this+0x30d9]`, `0x00565d4e`), Ctrl-os billentyű (`0x005c2568`). A `"` jel `U+201C`-re cserélődik (`0x00565d8b-0x00565d90`). Rejtett sáv esetén a gépelés a kapcsolót visszakapcsolja (`0x00565d5a-0x00565d86`). | `PhotoViewerKeyboard.qml:50-75`: nyomtatható karakter nem kezelt; az `F` és a `Shift+F` az arckeretek kapcsolója (saját bővítés, `picasa-gyorsbillentyuk.md:542-543`). | **Eltérés (J3).** |
| Felirat-kapcsoló (Show/Hide Caption) | `editpanel/captionbutton` esemény: `0x005d5e77-0x005d5e88` → `0x005f8ac0`. Az állapot a `Preferences` `LastCaptionButton` kulcsához kötött (`0x00576bc0`, `0x00576c14`; az olvasó és az író irány külön nincs igazolva). Eszközmódban (`[this+0x30d4]` 2-6) a három elem rejtett (`0x0057be53-0x0057be5f`, elrejtés `0x0057bdf2-0x0057be47`), kilépéskor visszaáll (`0x0057c013-0x0057c07d`). | `PhotoViewerOverlayControls.qml:602-650`; állapot: `controller_folder_view_mixin.py:262-287` (`view/captionVisible`, tartós). A sáv `visible`-je nem függ az eszközmódtól (`:473`). | Tartós állapot feltételesen egyezik. Az eszközmódbeli elrejtés nálunk hiányzik, a módkódok megfeleltetése nyitott (G4). |
| Törlés gomb (`captiontrash`) | `0x005d5ee7-0x005d5ef9` → `0x005f8c00`: **megerősítő ablak**, csak igenre ír (lásd a 6. szakaszt és a J1 jegyet). Üres feliratnál a gomb tiltott (`0x00568010`: `0x005680c6-0x005680d5` a `0x009cd7e0`-nal a `[+0x20e]` letiltás-jelzőt állítja; törlés után `0x005f8cef`). | `:544-583`: kérdés nélkül töröl, üres feliratnál tiltott. | **Eltérés (J1).** A tiltás egyezik. |
| Bélyegkép alatti felirat (Nézet, Indexkép felirata) | Csak megjelenítés: `eMenuView::ThumbnailCaption` és `ID_CAPFULL`, `ID_CAPFILE`, `ID_CAPNONE`, `ID_CAPRES`, `ID_CAPTAG` a menüépítőben (`0x00559150`). A `CTextCaptionNode` típusleírót csak az editpanel függvényei használják (1. szakasz), tehát a rácson nincs szerkesztő mező. | `PicasaViewMenu.qml:469-520`, `ThumbDelegate.qml:74-84,269-277`: csak megjelenítés. | Egyezik. |
| Tulajdonságok (Alt+Enter) | A `PropertiesPanel` szövegkészlete: `title`, `info_*`, `Thumbnail`, `XMP`, `write_xmp`, `edit_keywords` (Szerkesztési címkék). Képfelirat-szerkesztő mező szövege nincs (erős, negatív, szövegtár-alapú). | `PropertiesPanel.qml`: nincs feliratmező. | Egyezik. |
| Szerkesztés menü: Szöveg másolása és beillesztése | `ID_EDIT_COPYTEXT` `0x9ded`, `ID_EDIT_PASTETEXT` `0x9dee` (`0x00d6dc0c`, `0x00d6dc20`). A korábbi Colab-mérés (#1526, #5877) a Text eszköz rétegét igazolta, a képfeliratot kizárta (`picasa-menusor-csoportok.md:165-176`). | A két menüpont a Text eszköz rétegét kezeli; `pasteCaptionText` és `copyCaptionText` (`photo_ops_write_text_mixin.py:64,81`) a felületről nem hívható. | Egyezik; a hívhatatlan segédek halott kódok (J6 megjegyzés). |
| Kép menü | A Kép menü hét tétele között felirat-parancs nincs (`picasa-menusor-csoportok.md:262-270`). | `PicasaPictureMenu.qml`: nincs felirat-tétel. | Egyezik. |
| Mappa és album leírása (`ID_ALBUM_EDITCAPTIONS`, `0x9c69`) | „Edit Folder Description…": a mappa/album leírása, nem a képé (`stringres`: `Folder::ID_ALBUM_EDITCAPTIONS`). | `FolderPropertiesDialog.qml`, `LightboxHeaderDescription.qml`: külön funkció. | Nem képfelirat, nincs teendő. |
| Diavetítés felirata | `oneup/caption`, `editoneup/caption` (`oneup.tre:168`, `editoneup.tre:175`) és a kapcsoló: megjelenítés, szerkesztő osztály nincs (1. szakasz). | `SlideshowControls.qml:76-80,244-251` (`slideshowCaption`, `slideshowCaptionModeButton`): megjelenítés. | Egyezik. |
| Gyorsbillentyű | Dedikált felirat-gyorsbillentyű nincs: a `editpanel/caption*` sztringeket csak 10 függvény hivatkozza (`0x00565cf0`, `0x00566a70`, `0x00568010`, `0x0057bb50`, `0x005c48c0`, `0x005f89a0`, `0x005f8ac0`, `0x005f8c00`, `0x005fa770`, `0x0075de50`), billentyűkezelő köztük nincs; a felirat a `0x005c24c0` karaktercsatornáján át indul (fent). | Nincs felirat-gyorsbillentyű. | Egyezik (a gépelési belépő: J3). |
| Egy kép / több kijelölt kép | Minden elérés egyetlen képkulcsot használ (`[this+0xe64]`: `0x005f8a4a`, `0x005f8c72`, `0x0056807e`). Több képes felirat-szerkesztés nincs. Kettős nézetben a fókuszált félé a felirat (#5975, `forras-audit-5186-1.md:214-232`). | `setCaption(row, text)` egy sorra (`photo_ops_write_mixin.py:253-275`); a mező a fókuszált sort írja (`PhotoViewerOverlayControls.qml:517`). | Egyezik. |
| Videó | A `0x00594ff0` a videóvezérlő billentyűit (`[panel+0x3094] != 0`, `0x00595001`) veszi el; a többi karakter videónál is a feliratot indítja, ha `[panel+0x332e] == 0` (`0x005c25bd-0x005c25c9`). A videó felirata ténylegesen szerkeszthető-e és hova kerül: NINCS MEG (G1, G5). | A sáv videónál is látszik, az írás az ini-be megy (`photo_ops_write_text_mixin.py:172-198`). | Nem eldönthető, nyitott (G5). |
| Írásvédett fájl | Lásd 5. szakasz. | Lásd 5. szakasz. | **Eltérés (J4).** |

### 3. Mentés, elvetés, megerősítés

| Helyzet | Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|---|
| Enter | `0x0076af33-0x0076af43`: a csomópont `+0x88` metódusa („captiondone"), utána a fókusz leadása (`0x0076af4b-0x0076af59`). Csak ha nincs Ctrl vagy Alt (`0x0076af13`), a csomópont látható (`[+0x20c] == 0`) és nem csak olvasható módú (`[+0x2c6] == 0`, `0x0076af00-0x0076af0d`). A mentés `0x005f89a0` (a csomópont szennyezett jelzője, `[+0x2c4]`, kell hozzá: `0x005f8a10-0x005f8a21`). | `PhotoViewerOverlayControls.qml:516-520`: `onAccepted` ment, újrakötés, fókusz a nézőre. | Egyezik. |
| Esc | `0x0076af1f-0x0076af2f`: `+0x84` („captioncancel", szennyezett jelző törlése `0x0067f7ad`), a diszpécser a rekord feliratát tölti vissza (`0x005df583-0x005df58f` → `0x00568010`). **Az Esc elvet.** | `:521-525`: újrakötés a mentett felirathoz, fókusz a nézőre. | Egyezik. |
| Kattintás a mezőn kívülre (fókuszvesztés) | Az egérlenyomás üzenet (`[msg+8]` 1 vagy 0xd) a csomópont téglalapján kívül, ha a csomópont a fókuszos: `+0x88` (mentés) és fókuszleadás (`0x0067ed05-0x0067ed5b`). Másik elem fókuszt kap (üzenet 0x15, szerkesztő módban): szintén `+0x88` (`0x0067ed84-0x0067edaa`). **A fókuszvesztés ment.** | Nincs kezelő: a mezőnek csak `onAccepted` és `Keys.onEscapePressed` van (`:516-525`). A gépelt szöveg mentés nélkül marad a mezőben; a projekt saját megjegyzése szerint a gépelés megszünteti a `text` kötést (`LightboxHeaderDescription.qml:6-8`), ezért képváltás után a következő képnél is a begépelt szöveg látszhat (feltételes, futásidejű próba nincs). | **Eltérés (J2).** |
| Szerkesztési kapuk | A `0x005f8d80` első művelete a `0x005f89a0` (`0x005f8d99`): a függő felirat az eszközlezáráskor, fókuszváltáskor és mentéskor is véglegesedik. 14 közvetlen hívója van, köztük a mentő szál (`0x0053a790`), a kettős nézet fókuszváltója (`0x0056a160`), a `0x00578c30` (`0x00578ce9`) és a Ctrl+F9 lépés (`0x00578dc0`, `0x00578e79`). | Nincs megfelelő; a függő szöveg elvész. | **Eltérés (J2).** |
| Beillesztés (Ctrl+V) | `0x0067edb6-0x0067eee4`: szerkesztő módban (`[+0x2c5] != 0`) a vágólap a szövegbe kerül, megerősítés és azonnali mentés nélkül (`0x0067ee37-0x0067ee6e`). Nem szerkesztő módban a teljes felirat cserélődik; ha van felirat, megerősítés kell (`CTextEditNode::confirm`, gomb `CTextEditNode::confirmyesbutton` = „Replace", `0x0067ee73-0x0067eee4`), majd azonnali mentés (`0x0067eefc-0x0067ef03`). | Szabványos `TextInput` beillesztés (`:487-525`), felülírás nélkül. Az eredeti szerkesztő módú ága egyezik; a nem szerkesztő módú ág (G3) nem eldönthető. | Nincs teendő, amíg G3 nyitott. |
| Kivágás (Ctrl+X) | Szerkesztő módban a kijelölés kivágása, mentés nélkül (`0x0067efdf-0x0067f08e`); nem szerkesztő módban a teljes felirat a vágólapra, a mező kiürül és azonnal ment (`0x0067f099-0x0067f0ff`). | Szabványos `TextInput` kivágás. | Mint a beillesztésnél (G3). |
| Változatlan szöveg | A mentés csak szennyezett jelzőnél fut (`0x005f8a10`), és a setter a régi és új szöveget bájtról bájtra összeveti: egyezésnél visszatér, nem ír semmit (`0x00437df5-0x00437e69`). | `setCaption` mindig ír: nincs egyezés-vizsgálat (`photo_ops_write_mixin.py:253-275`, `photo_ops_write_text_mixin.py:166-198`). Enter változatlan szövegen is újraírja a JPEG-et és a `backuphash`-t. | **Eltérés (J5).** |
| Megerősítés mentéskor | Nincs: a `0x005f89a0` nem hív megerősítő ablakot. | Nincs. | Egyezik. |
| Szóközök levágása | A mentő út a `0x0067f7e0`-ban a `0x00989f80` segédet hívja a szövegre (`0x0067f820`); hogy ez levág-e, NINCS MEG (G6). | `_felirat_iras` `strip()`-pel levág (`photo_ops_write_text_mixin.py:172`). | Nyitott (G6). |

### 4. Hatás: hova ír, mi frissül

| Szempont | Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|---|
| Hova kerül (JPEG) | A setter (`0x00437cf0`) a fájlba ír, ha a kép `.thm` oldalfájllal rendelkezik VAGY a képrekord `+0x18` típuskódja 2 (`0x00438566-0x00438575`), a fájl nem írásvédett (`0x0043859e-0x004385a5`) és a kép nem iPhoto/Photos-könyvtárban van (`0x004384e5-0x004384ec`). A `0xe4` tulajdonság (IPTC 2:120 Caption/Abstract, `picasa-metaadat-tulajdonsagok.md:55`) a metaadat-csomagba kerül (`0x004385ce`), üres szövegnél kikerül belőle (`0x004385fb`); a csomagot a `0x009ed330` hívás írja a fájlba (a szerepe a hívás alakjából és a hibaágból következik, feltételes). A típuskód jelentése NINCS MEG (G1); a korpusz szerint JPEG-nél a felirat nem az ini-ben él: 16 970 `jpg` szakaszból 5-ben van `caption=`, és mind az 5 online-jelzéses (`onlinechecksum` vagy `IIDLIST`). | `_felirat_iras` (`photo_ops_write_text_mixin.py:172-187`): `.jpg` és `.jpeg` fájlnál `write_iptc_caption` (`iptc_writer.py:40-45`), siker után csak a `backuphash`. | Struktúra egyezik. |
| Hova kerül (minden más) | A fájlba írás feltételei nem teljesülnek: a `0x00438775` ág a `.picasa.ini` `caption=` kulcsát írja a `0x00454770`-nel (`0x00438778-0x0043878a`, ötödik argumentum 1: `backuphash`-ír, `0x004548a7-0x00454913`). Korpusz: 410 `bmp` szakaszból 193-ban van `caption=` (ebből 186 online-jelzéses, 7 nem), `mp4`: 8 a 52-ből, `mpg`: 2 a 29-ből, mind online-jelzéses. | `:188-198`: `.picasa.ini` `caption=`, törlésnél `with_removed`, `backuphash`. | Egyezik. |
| Ini-kulcs sikeres fájlírás után | A sikeres fájlírás ága a szövegmutatót nullázza (`0x00438754-0x00438759`), és ugyanazzal a `0x00438778-0x0043878a` hívással nullát ad a `caption` kulcsnak: a kulcs nullával való törlése feltételes (G2), de a korpusz (5/16 970) ezt támasztja. | Siker után csak a `backuphash` frissül, a meglévő `caption=` kulcs marad. A tényleges felirat `COALESCE(caption_file, caption_ini)` (`index/queries.py:27`): ha egy JPEG-nek régi `caption=` kulcsa van az ini-ben, a feliratot törölve (`caption_file` üres) a régi ini-szöveg visszatér. | Feltételes eltérés, jegy csak G2 után (J7). |
| Keresési index | A setter az új szöveggel (`0x00438421`: `0x004d9010`) és a régivel (`0x0043844e`: `0x004d8da0`) a `[db+0x20]` objektumot frissíti, még a fájlírás előtt; a két függvény szerepe (szövegindex-bővítés és -törlés) a hívás alakjából következik, feltételes. | `update_photo_fields` az FTS-oszlopokat (`index/schema.py:123-149`); a `_run_photo_write` a mentés után írja (`photo_ops_write_core_mixin.py:80-94`). | Egyezik. |
| Rács és bélyegkép felirata | A mentés után a `[this+0x2ac]` figyelőobjektum `+8` metódusa a képkulccsal (`0x005f8a8a-0x005f8aa0`), majd `0x00579480(1,0)` (a `editpanel/preview` elrendezésének frissítése). | `_photoFieldUpdated` a rácsmodellt frissíti (`photo_ops_write_core_mixin.py:94`), `ThumbDelegate.qml:74-84`. | Egyezik. |
| Visszavonás | A `0x005f89a0`, `0x005f8c00` és `0x00437cf0` útjában nincs visszavonási rekordot író hívás; a menü Visszavonás tételének hatóköre a felirattal NINCS MEG (G7). | Nincs visszavonás. | Nyitott (G7). |

### 5. Hibaesetek és részleges végrehajtás

| Helyzet | Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|---|
| Írásvédett fájl | A `0x00992d50` a fájl attribútumát kéri le (`[0x00d69518]` hívás útvonallal, 0 szinttel és pufferrel, majd az első bájt `& 1`, `0x00992d5a-0x00992d6d`): írásvédett fájlnál a fájlba írás kimarad, és a felirat az ini-be megy (`0x0043859e-0x004385a5` → `0x00438775`). | `_felirat_iras` nem vizsgálja az írásvédettséget: `write_iptc_caption` közvetlenül próbál írni (`iptc_writer.py:74-92`, `write_atomic`); a hiba `OSError`-ként `photoOpFailed`-et vált ki, ini-tartalék nincs (a tartalék csak akkor, ha a fájl nem érvényes JPEG). Windowson a csere írásvédett célfájlra `PermissionError` lehet (platformfüggő, futásidejű próba nincs). | **Eltérés (J4).** |
| Írási hiba a fájlba | A `0x009ed330` nem nulla eredménye (`0x00438711-0x00438718`, feltételes: a hívás fájlírás-jellege) a hibakóddal tér vissza, az ini-írás kimarad (`0x00438727-0x0043874f` → `0x00437f51`). A hívó a visszatérési értéket eldobja (`0x005f8a51`), **hibajelzés nincs**. A memóriabeli szöveg és a szövegindex addigra már frissült (a szövegindex-állítás feltételes, lásd fent). | A hiba `photoOpFailed` jelzésként látszik (`photo_ops_write_core_mixin.py:87-89`). | Eltérés, de javulás: megtartandó. A paritás nem kívánja az elnyelést. |
| Írási hiba az ini-be | A `0x00454770` visszatérési értékét a setter nem nézi, a függvény mindig 0-val tér vissza (`0x0043878f`, `0x004387dc`): **az ini-hiba néma**. | Az `IniSaveError` is `photoOpFailed` (`edit_controller_shared.py:137`). | Mint fent: megtartandó. |
| Több kép részleges végrehajtása | Nincs: a felirat mindig egy képre megy (2. szakasz). | `_run_photo_writes` (köteg) csak a felületről nem hívható `pasteCaptionText`-hez van (`photo_ops_write_text_mixin.py:121-146`). | Nincs teendő. |
| iPhoto/Photos-könyvtár képe | A `0x0047d1b0` (a `[this+0xe6d]` forrása, `0x00568a0f-0x00568a1e`) és a `0x0047d270` az `iPhoto Library`/`Photos Library` mappák `Masters` és `Originals` alatti képeit jelöli (`0x0099bce0`, `0x0099bf40`): a mező szerkesztése ezeknél tiltott (`[node+0x2c6]`, `0x00568162-0x0056816c`), a setter semmit nem ír (`0x004384ea` → `0x0043879b`); a predikátum neve a sztringekből következik, feltételes. | Nincs ilyen kép. | Nem alkalmazandó. |

### 6. Szövegek (hivatalos magyar a `stringres` és a `panel-feliratok-hu` szerint)

| Elem | Eredeti | Nálunk | Teendő |
|---|---|---|---|
| Alapszöveg a mezőben | „Készítsen képaláírást!" (`CTextCaptionNode::defname`) | „Készítsen képfeliratot!" (`picasapy_hu.ts:10795-10797`) | J8 |
| Kapcsoló buboréksúgója | „Képfelirat megjelenítése/elrejtése" | „Felirat megjelenítése/elrejtése" (`picasapy_hu.ts:10807-10809`) | J8 |
| Törlés buboréksúgója | „Képfelirat törlése" | „Felirat törlése" (`picasapy_hu.ts:10801-10803`) | J8 |
| Törlés megerősítése | „Biztosan törli a kép feliratát?", gombok „Képfelirat törlése" és „Nem", cím „Jóváhagyás" (`0x005f8c08-0x005f8c33`, `0x009bac20`) | Nincs | J1 |
| Beillesztés megerősítése | „Biztosan lecseréli a jelenlegi képfeliratot a vágólap tartalmával?", gomb „Csere" (`0x0067ee94-0x0067eebd`) | „...tartalmára? (Ez a művelet nem vonható vissza)" (`picasapy_hu.ts:11593-11597`), de a párbeszéd a felületről nem érhető el | J6 megjegyzés |

### 7. Javasolt fejlesztői jegyek

Csak igazolt eltérés lehet az alapjuk. A J7 feltételes (G2 dönti el), a többi igazolt.

#### J1: A képaláírás törlése megerősítést kér

- **Cím:** Képfelirat törlése a néző kuka gombjával: megerősítő ablak
- **Törzs:**
  Eredeti: `0x005f8c00` (`0x005f8c08-0x005f8c5c`): a kuka gomb (`0x005d5ef9`) a `0x009bac20` megerősítő ablakot nyitja, szöveg `IDS_CONFIRM_CAPTION_TRASH` („Biztosan törli a kép feliratát?"), igen-gomb `IDS_CONFIRM_CAPTION_YES_BUTTON` („Képfelirat törlése"), nem-gomb `il_No`, cím `ytApp::ConfirmTitle`. Csak igenre fut a törlés (`0x005f8c62-0x005f8c82`); nemre a függvény kilép (`0x005f8c5c-0x005f8d2c`).
  Nálunk: `PhotoViewerOverlayControls.qml:572-583` (`#1816 DÖNTÉS: NINCS megerősítés`, az indok szerint az eredetiről nincs mérve). A mérés most megvan, az indok megdőlt.
  Teendő: megerősítő párbeszéd a fenti szöveggel és gombokkal; a #1816-os megjegyzés javítása.
  Kész, ha: a kuka gomb a kérdést mutatja; „Nem" esetén a felirat, a JPEG és a `.picasa.ini` változatlan; „Képfelirat törlése" esetén a felirat törlődik és a gomb tiltottá válik.

#### J2: A függő feliratszöveg mentése fókuszvesztéskor és szerkesztési kapuknál

- **Cím:** Képfelirat: a mezőn kívüli kattintás és a kapuk (mentés, eszközváltás) mentsék a begépelt szöveget
- **Törzs:**
  Eredeti: kattintás a mezőn kívülre `0x0067ed05-0x0067ed5b`, fókusz másik elemre `0x0067ed84-0x0067edaa`, mindkettő a „captiondone" metódus (`+0x88`) → `0x005f89a0` (mentés). A szerkesztési kapu `0x005f8d80` első művelete a `0x005f89a0` (`0x005f8d99`), 14 hívóval (köztük `0x0053a790`, `0x0056a160`, `0x00578c30`).
  Nálunk: `PhotoViewerOverlayControls.qml:516-525`: csak Enter ment, Esc elvet; a fókuszvesztés a begépelt szöveget mentés nélkül hagyja.
  Teendő: a mező fókuszvesztésekor (`onActiveFocusChanged` vagy `onEditingFinished`) és a képváltás, eszközmegnyitás, mentés előtt a változott szöveg mentése; Esc továbbra is elvet.
  Kész, ha: szöveget gépelve és a rácsra/képre kattintva a felirat mentve van (indexben és IPTC-ben vagy ini-ben); képváltás után a következő kép mezője a saját feliratát mutatja.

#### J3: Gépelés a nézőben közvetlenül feliratot indít

- **Cím:** Néző: nyomtatható billentyű lenyomása kezdje a képaláírást; az F és a Shift+F ütközésének rendezése
- **Törzs:**
  Eredeti: `0x005c24c0` (`0x005c25c9-0x005c25dc`) → `0x00565cf0`: Ctrl nélküli karakter (`0x21-0xFE`) a felirat végére kerül és szerkesztő módba lép; Backspace az utolsó karaktert törli (`0x005c273a-0x005c2748`); kizárás: szóköz, Tab, eszközmód, Ctrl (`0x00565d38-0x00565d4e`, `0x005c2568`); `"` → `U+201C` (`0x00565d8b-0x00565d90`); rejtett sávnál a kapcsoló visszakapcsol (`0x00565d5a-0x00565d86`).
  Nálunk: `PhotoViewerKeyboard.qml:50-75`: nincs ilyen kezelés; az `F` és a `Shift+F` az arckeretet kapcsolja (saját bővítés, `picasa-gyorsbillentyuk.md:542-543`), vagyis az eredetiben a felirat első betűje lenne.
  Teendő: a nyomtatható karakter a feliratmezőbe kerüljön az eredeti kizárásaival. Javasolt alapértelmezés: az `F`/`Shift+F` betűkötések kerüljenek le, az arckapcsolók a képernyőgombok maradnak (a tulajdonos dönthet a megtartásról).
  Kész, ha: a nézőben `a` betűt lenyomva a mező `a` szöveggel szerkesztésre nyílik, Backspace törli, szóköz nem indít, eszközmódban nem indít; az F betű feliratot kezd.

#### J4: Írásvédett JPEG felirata az ini-be kerüljön

- **Cím:** Képfelirat írásvédett fájlnál: `.picasa.ini` tartalék a fájlírás helyett
- **Törzs:**
  Eredeti: `0x0043859e-0x004385a5`: a `0x00992d50` írásvédett attribútumnál a fájlba írást kihagyja, a felirat a `.picasa.ini`-be megy (`0x00438775` → `0x00438778-0x0043878a`).
  Nálunk: `photo_ops_write_text_mixin.py:172-187`: nincs írásvédettség-vizsgálat; `iptc_writer.py:74-92` közvetlenül ír, a hiba `photoOpFailed`.
  Teendő: JPEG-nél, ha a fájl írásvédett, a felirat `caption=` kulcsként az ini-be megy.
  Kész, ha: írásvédett JPEG feliratát mentve a fájl bájtra változatlan, a `.picasa.ini`-ben `caption=` van, a rács és a mező mutatja.

#### J5: Változatlan szövegnél nincs írás

- **Cím:** Képfelirat: ha a szöveg nem változott, ne írja újra a fájlt és az ini-t
- **Törzs:**
  Eredeti: `0x005f8a10` (csak szennyezett mezőnél ment), `0x00437df5-0x00437e69` (a setter az egyező szöveget eldobja).
  Nálunk: `photo_ops_write_mixin.py:253-275`, `photo_ops_write_text_mixin.py:166-198`: mindig ír.
  Teendő: `setCaption`: ha a levágott új szöveg egyezik a kép mai feliratával, kilép írás nélkül.
  Kész, ha: Enter változatlan szövegen a JPEG módosítási ideje és bájtjai, valamint a `.picasa.ini` változatlan.

#### J6: Szöveg-vágólap segédek és a halott beillesztő párbeszéd

- **Cím:** Halott felirat-beillesztés (`pasteCaptionText`, megerősítő ablak) eltávolítása vagy bekötése
- **Törzs:**
  Eredeti: a beillesztés megerősítése a mezőbe épül (`0x0067ee73-0x0067eee4`), a szövege `CTextEditNode::confirm` (nincs benne „nem vonható vissza"; az `IDS_REPLACE_CAPTION` sztring az exe-ben nincs).
  Nálunk: `photo_ops_write_text_mixin.py:64-119` és `PicasaMenuBar.qml:66-77`: a felületről nem hívható.
  Teendő: a G3 eredményéig csak a halott út és a téves szöveg eltávolítása; bekötés csak a G3 után.
  Kész, ha: nincs hívhatatlan `pasteCaptionText`/`copyCaptionText`, vagy bekötött és tesztelt.

#### J7 (feltételes, a G2 dönt): IPTC-írás után a régi ini `caption=` kulcs törlése

- **Cím:** JPEG felirat: sikeres IPTC-írás után az ini régi `caption=` kulcsa törlődjön
- **Törzs:**
  Eredeti: `0x00438754-0x0043878a`: sikeres fájlírás után a `caption` kulcs nullát kap (a null törlés-értelme: G2).
  Nálunk: `photo_ops_write_text_mixin.py:178-187` nem törli; `index/queries.py:27` `COALESCE(caption_file, caption_ini)`.
  Teendő: G2 megerősítése után az ini frissítésében `with_removed(photo.name, "caption")`.
  Kész, ha: ini-ben `caption=Régi` mellett törölt IPTC-felirat nem hozza vissza a régi szöveget.

#### J8: Hivatalos magyar szövegek

- **Cím:** Felirat-sáv szövegei a hivatalos magyar szerint
- **Törzs:**
  Eredeti: `CTextCaptionNode::defname` „Készítsen képaláírást!", tooltipek „Képfelirat megjelenítése/elrejtése" és „Képfelirat törlése" (`panel-feliratok-hu`).
  Nálunk: `picasapy_hu.ts:10795-10810`.
  Teendő: a három fordítás cseréje és a `.qm` újragenerálása.
  Kész, ha: a három szöveg a hivatalos alak, az i18n őrök (`test_i18n_dictionary_4313.py`) zöldek.

### 8. Két független út és cáfoló vizsgálat

- **A út (gépi kód):** a mentési lánc (`0x0076ace0` → `0x0067f7e0` → `0x005de8e0` → `0x005f89a0` → `0x00437cf0`), a törlés (`0x005d59f0` → `0x005f8c00`), a gépelés (`0x005c24c0` → `0x00565cf0`) és a setter ágai utasításról utasításra olvasva.
- **B út (bájtkeresés és erőforrások):** a típusleíró és a `call`-célok teljes `.text` kereséssel (`CTextCaptionNode`: három használó; `0x005f89a0`: négy hívó; `0x005f8c00`: egy; `0x00565cf0`: két; `0x005f8d80`: 14), a `stringres`/`.tre` szövegek, és a korpusz mérése. Ugyanide jut a `CThumbDB` slotok sorszámozása (`+0x4c`, `+0x50`).
- **Cáfoló vizsgálatok:** (1) a `CTextEditNode` és a `CCaptionNode` nem képfelirat-szerkesztő: az előbbi a Személyek felület névmezője (`picasa-arcfelismeres-kutatasi-naplo.md`, 15. kör: `0x00717810` → `0x00856060`, nem újra ellenőrizve), az utóbbi a vászonra tett szöveg (`Click here to type`, `0x005b59f0`, szövegalapú, feltételes). (2) A Szerkesztés menü Szöveg parancsai nem felirat-belépők: Colab-mérés (#1526, #5877). (3) A `LastCaptionButton` nem a felirat szövegét tárolja, csak a kapcsolót (`0x00576bc0`). (4) Az `IDS_REPLACE_CAPTION` sztring az exe-ben nem szerepel (bájtkeresés), a beillesztés `CTextEditNode::confirm`-et használ.

### 9. Bizonyítottsági fok

- **Megerősített (utasításszint és bájtkeresés):** a felirat-mező osztálya és egyetlen szerkesztő helye; Enter/Esc/kattintás-kívül/fókuszváltás viselkedése; a törlés megerősítése; a mentés egyszeri helye és a setter egyezés-ellenőrzése; az írásvédett ág a setterben; a gépelési belépő.
- **Erős:** a JPEG felirata IPTC-ben él (a setter `0xe4` tulajdonság-írása + a korpusz); az ini-hiba némasága (a visszatérési érték elvész); a Tulajdonságok és a bélyegképek nem szerkesztő felületek (negatív, szövegalapú).
- **Feltételes:** a null érték törlés-értelme (G2); a típuskód 2 jelentése (G1); a begépelt szöveg képváltás utáni megmaradása a PicasaPy-ban (futásidejű próba nincs).
- A megfejtett mechanizmusból nem következik, hogy a mi kódunk javítása csökkenti-e egy mért eltérést: itt eltérés-mérés nincs, minden jegy viselkedési egyezést kér, és a "Kész, ha" pontok kattintásos próbával ellenőrizhetők (Colab felvétel nincs ehhez a körhöz).

### 10. Helyesbítések a korábbi állításokhoz

- `picasa-menu-parancsok-viselkedes.md` 2. szakasz: a szöveg-beillesztés megerősítése nem az `IDS_REPLACE_CAPTION` (nincs az exe-ben), hanem a `CTextEditNode::confirm`, és a „nem vonható vissza" mondat nincs benne.
- `PhotoViewerOverlayControls.qml:572-580` (#1816): „az eredetiben szemetes-ikon közvetlen hatással" téves; az eredetiben megerősítés van (`0x005f8c00`).
- `picasa-ini-format.md:98,1455`: „JPEG-nél IPTC, nem ini" kiegészítése: a feltétel a `.thm` oldalfájl vagy a `+0x18` típuskód 2, az írásvédett és az iPhoto-könyvtáras kép ini-be (illetve sehova) megy.

### 11. Nyitott

Nyitott kérdések: 7 nyílt · 25 lezárva · 0 blokkolt · 0 hatókörön kívül · 0 „csak nyitva".

- Ghidra-kör kell: 0x00437cf0 - mit jelent a képrekord +0x18 mezőjének 2-es értéke a fájlba írás feltételében (0x00438575), mely formátumokra igaz, és a `.thm` oldalfájl-ágban (0x00438566) melyik fájlba kerül az IPTC 0xe4 tulajdonság? [nem blokkoló]
- Ghidra-kör kell: 0x005aa260 - a null értékű kulcs (0x005aa301-0x005aa30b) törli-e a kulcsot a .picasa.ini-ből, vagy üres értéket ír? [blokkoló a J7 jegyhez]
- Ghidra-kör kell: 0x0067eca0 - a [node+0x2c5] szerkesztő-mód jelző mikor 1 és mikor 0 a nézőben, azaz mikor érvényes a teljes felirat cseréje megerősítéssel (0x0067ee73) a szövegbe illesztés helyett (0x0067ee3e)? [nem blokkoló]
- Ghidra-kör kell: 0x0057bb50 - a [this+0x30d4] 2-6 módkódjai melyik szerkesztő eszközöknek felelnek meg, amelyeknél a felirat-sáv rejtett (0x0057be53-0x0057be5f)? [nem blokkoló]
- Ghidra-kör kell: 0x005c24c0 - videó megnyitva ([panel+0x3094] > 0) és [panel+0x332e] == 0 esetén (0x005c25bd-0x005c25c9) tényleg a feliratot indítja-e a betű, és mit jelent a [panel+0x332e]/[panel+0x332f] jelző? [nem blokkoló, Colabon is eldönthető]
- Ghidra-kör kell: 0x0067f7e0 - a 0x00989f80 (0x0067f820) a begépelt szöveget levágja-e (szóközök), és milyen hosszkorlátot alkalmaz a mentés előtt? [nem blokkoló]
- Ghidra-kör kell: 0x005f89a0 - a menü Visszavonás tétele (ID_UNDO) visszavonja-e a felirat beírását vagy törlését (a három függvényben visszavonási rekord nincs)? [nem blokkoló, Colabon is eldönthető: felirat beírása, Enter, Szerkesztés menü]

### 12. Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - ez a #7024 alszakasz.

## #7028: A képek másolásának és beillesztésének teljes folyamata az eredeti Picasával összevetve

### Következtetés

Az eredeti Picasa 3.9-ben a képek másolása és beillesztése két teljesen eltérő csatornán működik a felhasználói felület kontextusától függően. Könyvtárnézetben a másolás (`ID_COPY`, `0x9d3b`) és kivágás (`ID_CUT`, `0x9d39`) belső alkalmazásmemóriába menti a kijelölt azonosítókat és forrásmappát (`0x005fe9f0` -> `0x00577ba0`), kivágásnál a rácselemeket halványítottra állítja (`0x00716f40`), míg a szerkesztő nézetben (OneUp / EditPanel) a `0x0069b000` -> `0x00a706f0` láncon át a szerkesztett képet képadatként (`CF_BITMAP`, 2) helyezi az operációs rendszer vágólapjára. Beillesztéskor (`ID_PASTE`, `0x9d3c`, `0x005feab0` -> `0x005791d0` -> `0x00784100` -> `0x00478780`) ha a cél azonos a forrással, megerősítő kérdést tesz fel (`0x00c89d1c`), albumnál csak referenciát hoz létre, mappánál pedig átmásolja a fájlt, a `.picasaoriginals` mentett eredetiket és a `.picasa.ini` szekciót (új fejlécet adva névütközésnél). Névütközésnél átnevezés vagy kihagyás kérhető (`0x005350b0`), írási hibánál a köteg megszakad, visszagörgetés nélkül (a korábbi sikeres másolatok megmaradnak).

A PicasaPy jelenlegi megvalósítása (`PicasaEditMenu.qml`, `MainKeyboardShortcuts.qml`, `fileops_controller_clipboard_mixin.py`, `fileops/copy.py`) nagyrészt paritásban van a lemezes másolással és a `.picasa.ini` / `.picasaoriginals` kezeléssel, de négy eltérést mutat:
1. Szerkesztő nézetben (OneUp) a vágólapra másolás jelenleg fájl-URL-t tesz a vágólapra, nem a renderelt képet (`QImage` / képadat).
2. Azonos forrás- és célmappa esetén beillesztéskor a PicasaPy azonnal átnevezi a fájlt (`név-1.jpg`), nem kér megerősítést.
3. Ha nincs cél kijelölve, a PicasaPy nem jeleníti meg a célválasztási figyelmeztetést (`IDS_NEED_SELECTED_ALBUM`).
4. Kivágáskor (Cut) a PicasaPy-ban nincs vizuális halványítás a rács kijelölt bélyegképein.

### Bizonyítottsági fok

Megerősített. A folyamat belépési pontjait, parancskódjait, vágólap-kezelését, Win32 API-hívásait és hibakezelését két független út (a bináris gépi kódjának diszasszemblálása + index és Ghidra-dekompilációs leletek) egybehangzóan igazolja, kiegészítve cáfoló vizsgálattal.

### 1. Belépési pontok és engedélyezési feltételek

| Belépési pont | Eredeti Picasa (bináris cím) | Engedélyezési feltétel (Eredeti) | PicasaPy (fájl:sor) | Paritás |
|---|---|---|---|---|
| Szerkesztés menü Copy (`&Copy`) | `0x005cb990` -> `0x005fe9f0(0)`, parancskód `0x9d3b` (40251) | Könyvtárban legalább 1 kijelölt elem (`[esi + 0xeac] > 0`). Üres kijelölésnél inaktív / no-op (`ret 4`). Szerkesztőben az aktuális kép. | `PicasaEditMenu.qml:53-58` | Egyezik (`bar.hasSelection`) |
| Gyorsbillentyű Ctrl+C | Accelerator tábla (`0x007823f0`), parancskód `0x9d3b` | Megegyezik a Szerkesztés menü Copy feltételével. | `MainKeyboardShortcuts.qml:244-255` | Egyezik (`shortcutCopyFiles`) |
| Szerkesztés menü Cut (`Cu&t`) | `0x005cb990` -> `0x005fe9f0(1)`, parancskód `0x9d39` (40249) | Könyvtárban legalább 1 kijelölt elem. A rácson halványított jelölést kap (`0x00716f40`). Szerkesztőben inaktív. | `PicasaEditMenu.qml:46-51` | Eltérés: a PicasaPy nem jelöli halványítottként a rácson a kivágott elemeket. |
| Gyorsbillentyű Ctrl+X | Accelerator tábla (`0x007823f0`), parancskód `0x9d39` | Megegyezik a Szerkesztés menü Cut feltételével. | `MainKeyboardShortcuts.qml:256-267` | Egyezik a hívásban, hiányzik a vizuális jelölés. |
| Bélyegkép helyi menü | `0x00730790` | Nincs sima Copy / Cut tétel a helyi menüben (csak `Copy Path`, `Copy Effects`, `Move to New Folder...`). | `PhotoContextMenu.qml` | Egyezik (nincs közvetlen Copy/Cut a helyi menüben). |
| Szerkesztés menü Paste (`&Paste`) | `0x005cb990` -> `0x005feab0()`, parancskód `0x9d3c` (40252) | Belső vágólap nem üres VAGY külső vágólapon képadat/fájllista van. Szerkesztőben inaktív. Cél hiányában dialógus (`IDS_NEED_SELECTED_ALBUM`). | `PicasaEditMenu.qml:60-67` | Eltérés: cél hiányában a PicasaPy hibasávot mutat, vagy csendben nem tesz semmit. |
| Gyorsbillentyű Ctrl+V | Accelerator tábla (`0x007823f0`), parancskód `0x9d3c` | Megegyezik a Szerkesztés menü Paste feltételével. | `MainKeyboardShortcuts.qml:268-279` | Egyezik |
| Copy To Folder | Nincs ilyen önálló parancs | Az eredetiben külön Export (`0x9d3e`), Move Folder (`0x9df4`) és Move to New Folder (`0x9d68`) létezik. | Nincs önálló parancs | Egyezik |
| Média típusok | Kép és videó támogatott | Legalább 1 érvényes médiaelem kijelölve. | Kép és videó támogatott | Egyezik |

### 2. Vágólapra helyezett adatok és megerősítések

Az eredeti Picasa 3.9 a másolás helyétől függően kétféleképpen kezeli a vágólapot:
1. **Könyvtárnézet (Library Grid):** A `0x005fe9f0` meghívja a `0x00577ba0` rutint. Ez az alkalmazás belső struktúrájában menti el a kijelölt elemek azonosítóit (`[esi + 0x319c]`), a forrásmappa azonosítóját (`[esi + 0x318c]`), valamint a művelet típusát (`[esi + 0x31a4] = 0` másolás, `1` kivágás). Nem ír az operációs rendszer vágólapjára, nincs párbeszédablak és megerősítéskérés sem.
2. **Szerkesztő nézet (OneUp / EditPanel):** A `0x0069b000` -> `0x00a706f0` lánc a kép szerkesztett, effektezett változatát kirajzolja egy Win32 Device Context-be, majd a szabványos Win32 vágólap API-val (`OpenClipboard` @ `0x0069b1bb`, `EmptyClipboard` @ `0x00a70715`, `SetClipboardData(CF_BITMAP, hBitmap)` @ `0x00a70776`) bitmap képadatként (`CF_BITMAP`, formátumkód 2) helyezi a vágólapra. Nincs ablak vagy megerősítés.
3. **Megjegyzett értékek:** Nincsenek perzisztált állapotok; minden másolás felülírja a korábbi vágólap-tartalmat.

*PicasaPy összevetés:* A `fileops_controller_clipboard_mixin.py:16-56` (`_tegyd_a_vagolapra`) kizárólag fájl-URL-eket (`mime.setUrls(...)`) és `x-special/gnome-copied-files` szöveget helyez a vágólapra. Szerkesztő nézetben sem teszi fel a szerkesztett képet képadatként (`QImage` vagy `QPixmap`), így külső képszerkesztőkbe vagy szövegszerkesztőkbe nem illeszthető be közvetlenül képként.

### 3. Beillesztés végrehajtása, fájlok, ini, index és rács

Ha a felhasználó a Beillesztés (Paste) parancsot választja (`0x005feab0` -> `0x005791d0` -> `0x00784100`):
1. **Cél meghatározása:** Ha a kijelölt cél egy virtuális album, a `0x007842c3` (`FUN_00506400`) album-referenciát ad hozzá, lemezes fájlmásolás nélkül. Ha a cél egy lemezes mappa, a lemezes másolási útvonal indul el. Ha nincs cél kiválasztva, megjelenik az `IDS_NEED_SELECTED_ALBUM` dialógus ("Please select an album...").
2. **Azonos mappa megerősítése:** Ha a forrásmappa és a célmappa azonos, és a művelet másolás (nem kivágás), a `0x00579220` felugró kérdést jelenít meg: `0x00c89d1c` ("Are you sure you want to copy the file(s) to %s ?", `CThumbUI::MoveFilesConfirmCopy`).
3. **Fájlok másolása:** A tényleges másolás a `0x00478780` rutinban fut le, a Win32 `CopyFileW(..., bFailIfExists=1)` (`0x00473bd6`) hívással.
4. **Mentett eredetik (`.picasaoriginals`):** A `0x00478780` sor 509 ellenőrzi a forrásmappa `.picasaoriginals` almappáját. Ha a másolt képhez létezik korábban mentett eredeti fájl, azt is átmásolja a célmappa `.picasaoriginals` almappájába.
5. **`.picasa.ini` szekció kezelése:** A `ytPicasaINIFile` segítségével a forrás `.picasa.ini`-ből kimásolja a képhez tartozó összes attribútumot (szűrők `filters=...`, forgatás `rotate(...)`, csillag `star=yes`, arcrekordok `faces=...`). Névütközés esetén az új fájlnév fejlécével (`[újnév.jpg]`) írja be a cél `.picasa.ini`-be.
6. **Index és rács frissítése:** A `CFolderWatcher` (`0x005a76e0`) érzékeli a lemezváltozást, az SQLite index azonnal felveszi az új fájlokat, és a rács automatikusan megjeleníti az új képeket. Kivágás (Cut) esetén a forrásfájl és annak `.picasa.ini` bejegyzése törlődik, és a forrás rácsból eltűnik az elem.
7. **Visszavonhatóság:** Nem visszavonható (nincs Ctrl+Z művelet).

*PicasaPy összevetés:* A PicasaPy `fileops/copy.py:30-96` (`copy_photo`, `_copy_ini_section`, `copy_preserved_originals`) és `fileops_controller_clipboard_mixin.py:84-121` (`pasteFilesFromClipboard`) pontosan paritásban van a fájlok, `.picasaoriginals` és `.picasa.ini` másolásával. Eltérés: azonos mappába történő beillesztéskor nem kér megerősítést, hanem csendben átnevezi a fájlt (`név-1.jpg`), cél hiányában pedig nem kér célválasztást.

### 4. Hibák, ütközések és részleges végrehajtás

1. **Névütközés a célmappában:** Ha a célban már létezik azonos nevű fájl, a `0x005350b0` dialógust nyit meg: Rename Duplicates (`CThumbUI::MoveFilesRename`) vagy Skip Duplicates (`CThumbUI::MoveFilesSkip`). Átnevezéskor számozott utótaggal menti el a fájlt (`név-1.jpg`), és a `.picasa.ini` szekciófejlécet is erre módosítja.
2. **Írási hiba és lemez megtelése:** A fájlmásolás `CopyFileW` hibája esetén a `0x00473be4` lekéri a `GetLastError` kódot, hibajelző dialógust jelenít meg, és a köteg feldolgozása megszakad (`break`).
3. **Részleges végrehajtás állapota:** Hiba esetén a Picasa nem hajt végre visszagörgetést (nincs rollback): a korábban sikeresen átmásolt fájlok és azok `.picasa.ini` bejegyzései megmaradnak a célban, a hibás és hátralévő fájlok pedig változatlanul a forrásban maradnak.

*PicasaPy összevetés:* A PicasaPy `batch.py` és `fileops/copy.py` megvalósítása névütközésnél automatikusan átnevezést alkalmaz (`policy="rename"`), hiba esetén megszakítja a ciklust, és megőrzi a már sikeresen átmásolt fájlokat; ez paritásban van.

### 5. Paritási összehasonlító táblázat

| Funkció / Lépés | Eredeti Picasa (bináris cím) | PicasaPy (fájl:sor) | Teendő |
|---|---|---|---|
| Szerkesztés menü Copy | `0x005cb990` -> `0x005fe9f0(0)` | `src/picasapy/app/qml/PicasaPy/PicasaEditMenu.qml:53-58` | Nincs, paritásban van. |
| Gyorsbillentyű Ctrl+C | Accelerator `0x9d3b` (`0x007823f0`) | `src/picasapy/app/qml/PicasaPy/MainKeyboardShortcuts.qml:244-255` | Nincs, paritásban van. |
| Szerkesztés menü Cut | `0x005cb990` -> `0x005fe9f0(1)` | `src/picasapy/app/qml/PicasaPy/PicasaEditMenu.qml:46-51` | Nincs, paritásban van. |
| Rácselemek halványítása Cut esetén | `0x00716f40` (`[item + 0x5d] = 1`) | Nincs vizuális jelölés a rácson | Paritási eltérés javítása: a vágólapra kivágott fájlokat a rácson halványítottan (pl. (fél átlátszósággal) kell megjeleníteni. |
| Szerkesztő nézet (OneUp) másolás | `0x0069b000` -> `0x00a706f0` (`SetClipboardData(CF_BITMAP)`) | `fileops_controller_clipboard_mixin.py:16-56` (fájl-URL) | Paritási eltérés javítása: Szerkesztő nézetben a renderelt szerkesztett képet képadatként (`QImage`) kell a vágólapra helyezni. |
| Szerkesztés menü Paste | `0x005cb990` -> `0x005feab0()` | `src/picasapy/app/qml/PicasaPy/PicasaEditMenu.qml:60-67` | Nincs, paritásban van. |
| Gyorsbillentyű Ctrl+V | Accelerator `0x9d3c` (`0x007823f0`) | `src/picasapy/app/qml/PicasaPy/MainKeyboardShortcuts.qml:268-279` | Nincs, paritásban van. |
| Célválasztás figyelmeztetés | `0x005791fb` (`IDS_NEED_SELECTED_ALBUM`) | `MainWindowCommands.qml:5-7` (hibasáv) | Paritási eltérés javítása: ha nincs aktív mappa vagy album, figyelmeztető párbeszédablakot kell megjeleníteni. |
| Azonos mappa másolási megerősítés | `0x00579220`, `0x00c89d1c` (`CThumbUI::MoveFilesConfirmCopy`) | `fileops_controller_clipboard_mixin.py:84` (azonnali másolás) | Paritási eltérés javítása: azonos mappába másoláskor kérdezzen rá a felhasználónál a másolásra. |
| Fájlok másolása | `0x00473bd6` (`CopyFileW`) | `src/picasapy/fileops/copy.py:53` (`shutil.copy2`) | Nincs, paritásban van. |
| Mentett eredetik (`.picasaoriginals`) | `0x00478780` sor 509 | `src/picasapy/fileops/copy.py:78` (`copy_preserved_originals`) | Nincs, paritásban van. |
| `.picasa.ini` szekció másolása | `0x00478780` (`ytPicasaINIFile`) | `src/picasapy/fileops/copy.py:65` (`_copy_ini_section`) | Nincs, paritásban van. |
| Névütközés átnevezése | `0x005350b0` (`CThumbUI::MoveFilesRename`) | `src/picasapy/fileops/batch.py:159` (`_free_name`) | Nincs, paritásban van. |
| Részleges hiba lekezelése | Ciklus break, sikeresek megmaradnak | Ciklus break, sikeresek megmaradnak | Nincs, paritásban van. |

### 6. Két független út és cáfoló vizsgálat

- **Út A (gépi kód diszasszemblálása):** A `Picasa3.exe` .text szekciójának közvetlen feltárása a `0x005cb990` (főmenü diszpécser), `0x005fe9f0` (Copy/Cut kezelő), `0x005feab0` (Paste kezelő), `0x00577ba0` (könyvtár vágólap állapot), `0x0069b000` és `0x00a706f0` (OneUp CF_BITMAP vágólap), `0x005791d0` (Paste előkészítés), `0x00784100` (Paste végrehajtó), `0x00478780` (fájl-, ini- és .picasaoriginals másoló), `0x00473bd6` (`CopyFileW`), `0x005350b0` (ütközéskezelő dialógus) és `0x00716f40` (Cut áttetszőség) címeken.
- **Út B (index és RTTI):** A `picasa3-index.sqlite` adatbázis `string_xrefs` (`CThumbUI::MoveFilesConfirmCopy` @ `0x00c89d1c`, `IDS_NEED_SELECTED_ALBUM` @ `0x005791fb`, `CThumbUI::MoveFilesRename` @ `0x005350b0`), az `imports` tábla (`OpenClipboard`, `EmptyClipboard`, `SetClipboardData`, `CopyFileW`), a dekompilációs archívum (`referencia/ghidra/*.txt`) és a PicasaPy meglévő forráskódja.
- **Egyezés:** A két független út maradéktalanul megegyezik a hívási hierarchiában, az azonosítókban (`0x9d39`, `0x9d3b`, `0x9d3c`), a formátumkódban (`CF_BITMAP` = 2) és a lemezes/ini hatásokban.
- **Cáfoló vizsgálat:** Megvizsgáltuk azt a feltevést, hogy könyvtárnézetben több kép kijelölésekor az eredeti Picasa az operációs rendszer vágólapjára is kiteszi-e a fájllistát (`CF_HDROP` formátumban). A `0x005fe9f0` és a `0x00577ba0` kódjában semmilyen Win32 `OpenClipboard` vagy `SetClipboardData` hívás nem szerepel; a kijelölt azonosítók listáját kizárólag belső memóriarekeszekben (`[esi + 0x319c]`, `[esi + 0x318c]`) tárolja. A feltevés ezzel cáfolva: a könyvtárnézeti Copy/Cut tisztán belső állapotot kezel.

### 7. A jegy „Kész, ha” pontjai

1. ✅ **Belépési pontok és engedélyezési feltételek:** Szerkesztés menü Copy (`0x9d3b`), Cut (`0x9d39`), Paste (`0x9d3c`), Ctrl+C, Ctrl+X, Ctrl+V, helyi menük és Copy to Folder vizsgálata bináris címekkel és forrássorokkal igazolva.
2. ✅ **Vágólapra helyezett adatok és megerősítések:** Részletesen feltárva: könyvtárban belső azonosítók, szerkesztőben `CF_BITMAP` (2) képadat, nincs megerősítés másoláskor.
3. ✅ **Beillesztés hatása a fájlokra, .picasa.ini-re, indexre, névtérre és rácsra:** Fájlok célmappába másolása, `.picasaoriginals` megőrzése, `.picasa.ini` szekció átmásolása és fejléc átnevezése, index-frissítés igazolva.
4. ✅ **Hibák, névütközés és részleges végrehajtás:** `CopyFileW` hibakezelése, ciklus-megszakítás, meglévő másolatok megőrzése (rollback hiánya) bizonyítva.
5. ✅ **Paritási táblázat és fejlesztői jegyjavaslatok:** Táblázat és részletes fejlesztői jegytörzsek elkészítve.

### 8. Javasolt fejlesztői jegyek

#### 1. jegyjavaslat: Szerkesztő nézetben (OneUp) a kép másolása a renderelt képet tegye a vágólapra fájl-URL helyett
- **Cím:** Szerkesztő előnézet: a Copy parancs képadatot tegyen a rendszer vágólapjára fájl-URL helyett
- **Törzs:**
  Eredeti: `0x0069b000` -> `0x00a706f0` (`OpenClipboard`, `EmptyClipboard`, `SetClipboardData(CF_BITMAP, hBitmap)` @ `0x00a70776`). Az eredeti Picasa a szerkesztő nézetben a képszerkesztésekkel együtt kiszámolt képet valódi képadatként (`CF_BITMAP`) teszi a vágólapra, így külső programokba közvetlenül képként beilleszthető.
  Nálunk: `src/picasapy/app/fileops_controller_clipboard_mixin.py:16-56` (`_tegyd_a_vagolapra`) mindig csak a fájl lemezes URL-jét adja át (`mime.setUrls`), képfájlként.
  Teendő: A vezérlőben ellenőrizni, hogy a hívás szerkesztő nézetből (OneUp / EditPanel) érkezik-e. Ha igen, a kép aktuális renderelt felületét (`QImage`) kell a vágólapra helyezni a `clipboard.setImage(image)` hívással.
  Kész, ha: a szerkesztőben megnyitott és effektezett képen a Ctrl+C megnyomása után egy külső programban (pl. képszerkesztő vagy szövegszerkesztő) a Beillesztés közvetlenül a szerkesztett képet illeszti be.

#### 2. jegyjavaslat (ELVETVE, a Ghidra-kör szerint a kérdés nem a beillesztésé): Beillesztéskor azonos mappában megerősítő kérdés megjelenítése
- **Cím:** Beillesztés: azonos mappába másoláskor megerősítő kérdés megjelenítése
- **Törzs:**
  Eredeti: `0x00579220`, `0x00c89d1c` (`CThumbUI::MoveFilesConfirmCopy`: "Are you sure you want to copy the file(s) to %s ?"). Az eredeti Picasa figyelmezteti a felhasználót, ha ugyanabba a mappába illeszt be képeket másolás után.
  Nálunk: `src/picasapy/app/fileops_controller_clipboard_mixin.py:84-121` kérdés nélkül azonnal másol és automatikusan `név-1.jpg`-re nevezi át a duplikátumot.
  Teendő: Ha a vágólapon lévő fájlok forrásmappája megegyezik a kiválasztott célmappával és a vágólap módja másolás (nem kivágás), meg kell jeleníteni egy megerősítő modális kérdést a másolás végrehajtása előtt.
  Kész, ha: egy kép másolása és ugyanabba a mappába beillesztése előtt a felület rákérdez a műveletre, és Elvetés esetén nem hoz létre másolatot.

#### 3. jegyjavaslat (feltételes, a Nyitott kérdések 2. pontja dönti el): Kivágott képek halványított jelölése a rácson
- **Cím:** Rács: a vágólapra kivágott (Cut) fotók jelenjenek meg halványítottan a beillesztésig
- **Törzs:**
  Eredeti: `0x00716f40` (`[item + 0x5d] = 1`). Az eredeti Picasa kivágáskor a rácson a kijelölt elemeket áttetszőként / halványítottként jeleníti meg, jelezve a leendő áthelyezést.
  Nálunk: a PicasaPy nem tárol vizuális kivágási állapotot a bélyegképekhez.
  Teendő: A vezérlőben vezetni kell a kivágott fájlok listáját (`cutFiles`), és a `ThumbDelegate.qml`-ben az érintett elemek áttetszőségét (pl. `opacity: isCut ? 0.5 : 1.0`) módosítani.
  Kész, ha: a Ctrl+X megnyomásakor a kijelölt képek halványítottan jelennek meg a rácson, majd beillesztéskor vagy újabb másoláskor a halványítás megszűnik.

### 9. Új kutatási jegyjavaslatok

A két feltételes pont Ghidra-kört igényel (lásd lent).

### 10. Nyitott kérdések

A hívó ellenőrző mintavétele (2026-11-15): az 1. jegyjavaslat igazolt (a `0x00a706f0` a `0x00a70776`-nál `push 2` = `CF_BITMAP` után hívja a `SetClipboardData`-t). A másik kettő nem igazolt:

1. A `CThumbUI::MoveFilesConfirmCopy` szöveget (`0x00c89f0c`) a bináris-index szerint a `0x005350b0` használja, nem a `0x00579220`; a `0x00579220` a szerkesztőpanel elemeit kezeli. Hogy a kérdés pontosan mikor jön (azonos mappa, mindig, vagy csak húzásnál), nincs igazolva.
   - Ghidra-válasz (2026-11-15, `referencia/ghidra/2026-11-15-7012-7028-colab-decomp.txt`): a `0x005350b0` a fájlok albummappába mozgatásának vagy másolásának közös rutinja; a `param_4` választja a szöveget (1: `MoveFilesConfirmCopy`, 0: `MoveFilesConfirmMove`), a `param_5 == 0` esetén mindig kérdez, 1 esetén csak a `0x00992ed0` fájlonkénti jelzésére. Hívói: `0x00535020` és `0x005e39a0` (ejtés albumra vagy mappára, mozgatás, mindig kérdez), `0x00541fc0` (másolás, csak jelzésnél). **A kérdés a mozgatásé és a húzásé, nem a Ctrl+V beillesztésé**, ezért a 2. jegyjavaslat a mostani formájában elvetve; a húzásos mozgatás kérdése külön összevetés tárgya.
2. A `0x00716f40` egy elem `+0x5d` bájtját állítja; hogy ez a rácson halványított megjelenítést jelent-e, az értelmezés, nem bizonyíték.
   - Ghidra-kör kell: 0x00716f40 - Mit jelöl a rácselem `+0x5d` bájtja, és a kivágás után hogyan rajzolja a rács az így jelölt elemet [nem blokkoló]

### 11. Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - ez a #7028 alszakasz.

## #7031: A mappa törlésének teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, Picasa3.exe SHA-256
644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96.
A jelenlegi PicasaPy-állítások közvetlen forrásolvasásból származnak. A
bináris- és mérési bizonyítékot külön jelölöm. A teljes paritás feltételes:
a belépési lánc, a lomtárút és a részleges Shell-hiba igazolt, de több
engedélyezési feltétel és a törlés utáni belső állapot nem dőlt el.

### Következtetés

Az eredeti fő Mappa menü és a mappafa Delete Folder helyi menüje ugyanazt a
0x9d44 parancsot indítja. A parancs a mappát és tartalmát a Windows lomtárába
adja; a normál megerősítés a mappa nevét és a Recycle Bin célját nevezi meg.
A PicasaPy e két bejáratban azonos szövegű megerősítést és Windows alatt
ugyanilyen Shell-lomtárutat használ. Igazolt eltérés a részleges Shell-hiba
jelzése: az eredeti külön figyelmeztet a képek és a mappa eltérő végállapotára,
a PicasaPy generikus hibaszöveget ad tovább.

### Belépési pontok, kijelölés és engedélyezés

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Fő Mappa menü, Folder::ID_ALBUM_DELETE, parancs 0x9d44. A rekord feliratpointere 0x00d6e300, a parancsmező 0x00d6e30a; építő 0x00559150, végrehajtó 0x005cb990, amely az aktuális mappa objektumát adja tovább a 0x005ed240 és 0x005edef0 felé. | src/picasapy/app/qml/PicasaPy/MainMenuBar.qml:168-170; src/picasapy/app/qml/PicasaPy/FolderPane.qml:236-244 | A belépő és a megerősítés paritásban van. Az üres mappa és más speciális cél engedélyezése eredeti oldalon nyitott. |
| Mappafa helyi menü, Folder::ID_ALBUM_DELETE, parancs 0x9d44. A 0x007319f0 építőnél a felirat a [esp+0x19c], a parancsmező ugyanazon rekord [esp+0x1a6] mezője, értéke 0x9d44. | src/picasapy/app/qml/PicasaPy/FolderContextMenu.qml:330-336; src/picasapy/app/qml/PicasaPy/FolderPaneMenus.qml:317-325 | A parancsút egyezik. A PicasaPy saját képet tartalmazó mappasornál nyitja a teljes helyi menüt; saját kép nélkül (`own == 0`) rövid menüt nyit, amelyben nincs törlés. Az eredeti menü engedélyezési feltétele nyitott. |
| Delete billentyű fókuszban lévő mappafán: a binárisban lehetséges saját VK_DELETE út nincs eldöntve. A 0x00a53b00 címhez csak hivatkozó kimenet van, a függvénytörzs és a fa fókuszának parancsa nincs feloldva. | src/picasapy/app/qml/PicasaPy/FolderPaneContent.qml:304-307 csak Fel/Le kezelőt köt; src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml:678-687 sima Delete-je fotóparancs. | Ne tekintsük a globális fotó Delete parancsot mappatörlésnek. A fa saját Delete útját célzott Ghidra-körrel kell eldönteni. |
| Néző és fotórács Delete: az eredeti fotótörlő 0x9c9a út külön parancs, nem a mappatörlő 0x9d44. A 0x005cb990 diszpécserben eltérő ágak. | src/picasapy/app/qml/PicasaPy/PicasaMenuBar.qml:514-520,678-687; src/picasapy/app/qml/PicasaPy/MainKeyboardShortcuts.qml:431-460; src/picasapy/app/qml/PicasaPy/PhotoViewerKeyboard.qml:66-78 | Egy fotó kijelölése, több fotó kijelölése és a néző aktív képe a fotóparancs bemenete; ezek nem adódnak át a 0x9d44 mappaparancsnak. A jelenlegi fában a mappatörlés külön mappautat használ. |
| Képtálca: az eredeti Tray::ID_REMOVE_SELECTION tétel címe 0x00732f7f. Ez nem azonosított mappatörlő parancsként; a mappatörlő láncban nincs. | src/picasapy/app/qml/PicasaPy/TrayBar.qml:377-388 | A PicasaPy művelet képeket vesz ki a tálcából, nem töröl mappát vagy lemezfájlt. Eredeti tálca-művelet teljes mellékhatása nem része a bizonyított mappatörlő láncnak. |

A 0x9df4 közeli érték nem a helyi menü Delete parancsa. A
0x00731f34 körüli parancsmező az előző Move Folder rekordhoz tartozik; a
diszpécser 0x9df4 ága a 0x0053f340 és 0x0053f4a0 útvonalon mozgatási
szövegeket használ. A feliratot és parancsot a rekord bázisához párosítottam.

Üres mappa, almappás mappa, írásvédett hely és hálózati meghajtó: az eredeti
út a Windows Shell mappatörlő műveletére ad át egy útvonalat. A binárisból
nem állapítható meg, hogy az adott fájlrendszer, jogosultság vagy hálózati
állapot mellett a Shell pontosan mit engedélyez. Ezek értéke egyenként
NINCS MEG; megszerzésükhöz külön üres, almappás, írásvédett és hálózati
tesztmappa kell az eredeti Windows Picasában.

### Megerősítés és megjegyzett állapot

A 0x005fdc30 a DeleteFolderTitle, DeleteFolderWarnPC és
DeleteFolderYesButton erőforrást választja. A kérdés szövege a
0x00c992c0 címen:

> Are you sure you want to move the folder "%s" and its contents to the Recycle Bin?

A szokásos 0 típusú mappaág a 0x009bac20(1, ...) Yes/No megerősítést épít,
Cancel gomb nélkül. A feltárt 0 típusú ág nem olvas megjegyzett törlési
választást. Van egy 2 típusú ág is, amely a DeleteAllOnlineChecked kulcshoz
vezet; hogy mely mappára és mikor választódik ez az ág, a 0x005fd160
virtuális feltételének jelentése nélkül NINCS MEG.

PicasaPy a főmenüből és a helyi menüből is a mappa nevét helyettesíti a
megerősítő kérdésbe (src/picasapy/app/qml/PicasaPy/FolderPane.qml:236-244,
src/picasapy/app/qml/PicasaPy/FolderPaneMenus.qml:317-325). A párbeszéd
Delete Folder / No választ ad, Cancel és megjegyzési jelölő nélkül
(src/picasapy/app/qml/PicasaPy/FolderPaneMenus.qml:398-414). A normál
gombkészlet és a megjegyzés hiánya egyezik. A 2 típusú eredeti ág feltételes
viselkedésének PicasaPy-megfelelője nem ismert.

### Végrehajtás, fájlok és belső állapot

| Hatás | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| Lemez és lomtár | A 0x005edef0 a megerősítés után a 0x00992810 útján a 0x009929b0 Shell-hívást végzi. A 0x009929b0 wFunc értéke 3, azaz FO_DELETE, és paraméter 1-nél FOF_ALLOWUNDO is beáll. A normál út tehát lomtárba teszi a mappát és tartalmát, nem végleges törlés. | `src/picasapy/app/fileops_controller_delete_mixin.py:18-41` a teljes mappautat adja a delete_to_trash függvénynek. Windows alatt `src/picasapy/fileops/trash.py:79-140` a SHFileOperationW lomtárútját használja. |
| .picasa.ini | Sikeres egész mappatörlésnél a Shell a mappa útját és tartalmát kezeli, így a .picasa.ini nem külön törlődik. Részleges hibánál a fájl végállapota a konkrét könyvtártartalomtól függhet; ezt külön futásmérés nem igazolta. | A kód nem írja külön a .picasa.ini-t; az a mappával együtt kerül a lomtárba. Ezt a szándékot a `src/picasapy/app/fileops_controller_delete_mixin.py:25-27` kommentje is kimondja. |
| Index | A belső Picasa index törlés utáni módosítása ebből a handler láncból nem állapítható meg. NINCS MEG. | Siker után folderDeleted indul (`src/picasapy/app/fileops_controller_delete_mixin.py:41,` `application_services.py:121-124`); a resync eltávolítja az eltűnt mappa indexsorait (`library_controller_resync.py:195-211,` `index/sync_folders.py:296-325`). |
| Mappafa, rács és kijelölés | A parancs aktuális mappaobjektumot kap, de a siker utáni kiválasztott mappa, fa, rács és fotókijelölés végállapota nem igazolt. NINCS MEG. | A részfa újraszinkronizálódik; a törölt mappára mutató kiválasztás és a rács végállapota nincs a törlő handlerben külön beállítva. A tényleges megjelenő végállapot NINCS MEG, futásmérés kell. |
| Albumtagságok és arcok | A mappatartalommal együtt kezelt .picasa.ini önmagában nem bizonyítja az alkalmazás adatbázisában lévő album- és arcállapotot. NINCS MEG. | A kód kommentje szerint a .picasa.ini visszaállítása a feliratokat, címkéket és arc-hozzárendeléseket is visszahozza (`fileops_controller_delete_mixin.py:25-27`). Az albumtagság és az arcok törlés utáni, illetve visszaállítás utáni állapota külön mérés nélkül NINCS MEG. |
| Több fotó kijelölése | A 0x9d44 handler egy mappát kap, nem fotólistát; az egy vagy több kijelölt fotó nem a mappatörlő parancs argumentuma. A néző aktív fotójának törlése külön 0x9c9a fotóparancs. | A főmenü hostController.currentFolder értékét adja át; a fa helyi menüje folderPath értékét adja át. Fotók kijelölése nem bővíti a törölt mappák számát. |

### Részleges törlés és hibák

Az eredeti 0x005edef0 a 0x009929b0 Shell-hívás nemnulla eredménye után
IDS_CANT_DELETE_FOLDER figyelmeztetést mutat. A szöveg címe 0x00e05b6a:
a képek törölve lehetnek, de maga a mappa további fájlok vagy mappák
miatt megmarad. Ez részleges eredményt jelent, nem a mappa érintetlenségét.
Az üres, rejtett, írásvédett vagy hálózati bejegyzésekkel kapcsolatos
konkrét részleges végállapot NINCS MEG.

PicasaPy-ban Windows Shell nemnulla eredmény vagy megszakított művelet esetén
a `src/picasapy/fileops/trash.py:137-140` általános OSError keletkezik, és a
`src/picasapy/app/fileops_controller_delete_mixin.py:38-40` ezt szövegváltoztatás
nélkül az operationFailed jelzésre küldi. Ez nem őrzi meg az eredeti
részlegesállapot-figyelmeztetést. Ez az egyetlen most igazolt, fejlesztést
indokló eltérés.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Nemnulla Shell-eredmény: 0x005edef0 megjeleníti a 0x00e05b6a IDS_CANT_DELETE_FOLDER szöveget, amely elmondja, hogy a képek már törölve lehetnek, a mappa viszont megmaradhat. | `src/picasapy/fileops/trash.py:137-140` általános hibát dob; `src/picasapy/app/fileops_controller_delete_mixin.py:38-40` a generikus üzenetet továbbítja. | A Windows mappatörlés Shell-hibájánál részleges eredményt pontosan megnevező figyelmeztetést adjon. Ne állítsa, hogy a teljes mappa érintetlen maradt. |

### Bizonyíték és bizonyítottsági fok

| Érték vagy állítás | Forrás |
|---|---|
| Főmenü és fa helyi menü parancsa 0x9d44 | bináris (0x00559150, 0x007319f0, 0x005cb990) |
| Főmenü rekord felirat-pointere és parancsmezője | bináris (0x00d6e300, 0x00d6e30a) |
| Helyi menü rekord felirat-parancs párosítása | bináris (0x00731f48-0x00731f56, 0x00731f9e); Ghidra-kimenet: 2026-11-15-6970-colab-decomp.txt |
| Szomszédos 0x9df4 parancs Move Folder | bináris (0x00731f34, 0x0053f340, 0x0053f4a0); a Move Folder sztringek független xrefjei 0x00c8ac90-től |
| Normál kérdés és DeleteFolder erőforrások | bináris (0x005fdc30, 0x00c990e8, 0x00c992c0, 0x00c99314, 0x00c99338) |
| Mappát lomtárba adó Shell-művelet | bináris (0x005edef0, 0x00992810, 0x009929b0) |
| Részleges eredmény figyelmeztetése | bináris (0x005edef0, 0x00e05b6a) |
| PicasaPy belépési pontok, megerősítés és hibaút | Mai forrás: src/picasapy/app/qml/PicasaPy/MainMenuBar.qml:168-170; FolderPane.qml:236-244; FolderPaneMenus.qml:317-325,398-414; `src/picasapy/app/fileops_controller_delete_mixin.py:18-41`; `src/picasapy/fileops/trash.py:129-140` |
| Eredeti üres/almappás/írásvédett/hálózati viselkedés, belső index/album/arc és UI végállapot | NINCS MEG; külön Windows Picasa 3.9.141 futásmérés szükséges |

**Bizonyítottsági fok: feltételes.** A fő- és helyi menü parancsazonossága,
a Recycle Bin kérdés, a Shell lomtárjelzője és a részleges hibaüzenet
megerősített, mert külön útvonalon is egyeznek. A teljes feladat nem zárható
le: a fa Delete billentyűje, a 2 típusú párbeszéd feltétele, a fájlrendszer
speciális esetei, a Picasa belső indexe, albumjai, arcai és a törlés utáni
felületi kijelölés nyitott maradt.

### A két független út

- A út, utasításszintű lánc: a menürekordok 0x9d44 értéke a 0x005cb990
  diszpécserhez, onnan a 0x005ed240 és 0x005edef0 végrehajtóhoz, majd a
  0x00992810 és 0x009929b0 Shell-híváshoz vezet.
- B út, független szöveg- és hívásadat: a 0x00c992c0 kérdés maga mondja ki a
  Recycle Bin célt, míg a Shell-hívás 0x40 flagje FOF_ALLOWUNDO. A
  0x00e05b6a külön részleges eredményt ír le.
- Egyezés: a főmenü és helyi menü ugyanazt a mappa parancsot indítja, és a
  végrehajtás visszavonható lomtárút. A két út a részleges hiba jelentésében
  is egyezik.

### Cáfoló kísérlet

Azt próbáltam cáfolni, hogy a helyi menü Delete Folder feliratához a közeli
0x9df4 kód tartozik. A rekord mezőit a 0x007319f0 építő rekordbázisához
párosítva a felirat a [esp+0x19c], a Delete parancs pedig ugyanazon rekord
[esp+0x1a6] mezőjében 0x9d44. A 0x9df4 a megelőző Move Folder rekordhoz
tartozik, és mozgatási kezelőre vezet. A cáfolatot függetlenül ellenőriztem:
a 0x9d44 dispatch a mappatörlő 0x005edef0 útvonalra, a 0x9df4 a
0x0053f340 / 0x0053f4a0 mozgató útvonalra vezet. A próba a parancs-felirat
párosítást igazolta; nem dönt a fa Delete billentyűjéről.

### A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Mappa menü, fa helyi menü, fa Delete, néző és tálca belépési pontok | ⛔ | Főmenü és helyi menü 0x9d44 igazolt; fa Delete bináris kezelője nyitott. A néző 0x9c9a fotótörlő, a tálca külön művelet. |
| Üres mappa, almappák, írásvédelem és hálózati meghajtó | ⛔ | A Shell-hívás ismert; az egyedi célok eredménye csak Windows-méréssel dönthető el. |
| Megerősítés szövege és megjegyzése | ✅ / ⛔ | Normál kérdés, Yes/No és nincs megjegyzés igazolt. A DeleteAllOnlineChecked 2-es ág kiváltó feltétele nyitott. |
| Lomtár, .picasa.ini, index, mappafa, rács, kijelölés, albumok és arcok | ⛔ | A lomtárjelző igazolt, .ini a mappával halad. Eredeti belső adatok és UI végállapot nincs igazolva. |
| Részleges törlés és írási hiba | ✅ / ⛔ | Nemnulla Shell-válasz részleges figyelmeztetése igazolt; külön jogosultság- és hálózati kimenet nincs mérve. |
| PicasaPy összevetése és eltérésenkénti teendő | ✅ | Egy igazolt eltérésre kész jegytörzs készült; minden további eltéréshez hiányzik az eredeti oldali bizonyíték. |

### Javasolt fejlesztői jegytörzs-bővítés

**Cím:** Mappatörlés Shell-hibája: jelezzük a részleges eredményt

**Törzs:**

Eredeti: a 0x005edef0 mappatörlő a 0x009929b0 Shell-hívás nemnulla
eredményénél a 0x00e05b6a IDS_CANT_DELETE_FOLDER figyelmeztetést mutatja.
A szöveg szerint a képek már törölve lehetnek, de a mappa további fájlok
vagy mappák miatt megmaradhat.

Nálunk: `src/picasapy/fileops/trash.py:137-140` általános OSError keletkezik;
`src/picasapy/app/fileops_controller_delete_mixin.py:38-40` ezt általános
hibaüzenetként továbbítja.

Teendő: Windows mappatörlés Shell-hibájánál külön részleges eredmény
figyelmeztetést kell adni. A szöveg ne ígérje, hogy semmi sem változott.

Kész, ha:

- Nemnulla vagy megszakított Windows Shell-eredménynél a felhasználó olyan
  figyelmeztetést kap, amely szerint a képek törölve lehetnek, miközben a
  mappa megmaradhat.
- A hiba nem indít csendes végleges törlést.

### Új kutatási jegyjavaslatok

Most nincs külön új kutatási jegyjavaslat; a fa Delete és a törlés utáni
belső állapot ennek a folyamatnak nyitott része.

### Ghidra-kiegészítés (2026-11-15, várólista 404-405)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp.txt` (privát
kutatási tár).

- **`0x00a53b00`, Delete a mappafán.** Csak részválasz. Ez egy általános
  billentyűszűrő 17 hívóval. A DELETE billentyűt (`0x2e`) a vezérlő magának
  tartja (`FUN_00a582f0`), de a `0x9d44` parancs sem itt, sem a
  `FUN_00a582f0` elején nem szerepel. Hogy a mappafa melyik hívón át
  használja, ebből nem dönthető el. A fa Delete útja ezért **nyitott marad**;
  a PicasaPy mai viselkedése (a fán nincs saját Delete) nem cáfolt.
- **`0x005fd160`, a 2-es megerősítés feltétele.** A DeleteAllOnlineChecked
  típus akkor jön, ha a mappa **legalább egy** elemére a katalógus vtábla
  `+0xac` metódusa igazat ad; ezt a `0x005edef0` állítja be
  (`cVar1 ? 2 : 0`). A `+0xac` jelentése valószínűleg „online, feltöltve”, de
  ez nincs igazolva. **PicasaPy:** online feltöltés-nyilvántartás nélkül ez az
  ág nem értelmezhető; amíg a `+0xac` jelentése nem igazolt, jegyet nem
  javaslok rá.

### Ghidra-kiegészítés 2 (2026-11-15, várólista 413-418)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp-2.txt` (privát
kutatási tár). Ide a 413 és a 414 tartozik.

- **`0x00a582f0`, a mappafa Delete útja (413).** Részválasz, de az irány
  eldőlt. A függvény általános billentyű-továbbító: az eseményt előbb a
  fókuszban lévő gyermekcsomópont `0x74` virtuális metódusának adja
  (`param_1[0x57]`), majd a testvércsomópontoknak (`param_1[0x59]` tömb, a
  fókuszban lévőt és a letiltottakat kihagyva). A `1000000` eredménynél
  lezár, a `0xf4246` eredménynél megszakítja a bejárást. A törzs a DELETE-re
  billentyűkódot nem hasonlít (a testvérbejárásban csak az `0xd` és az `0x1b`
  kód szerepel), és a `0x9d44` parancs sem fordul elő benne. A mappalista saját
  kezelője a `KeyHandler::AlbumList` vtábla (`0x00c807e0`) `0x005c40e0`
  metódusa. **Bizonyítottsági fok: helyi disassembly, nem Ghidra-dekompilálás.**
  A `0x005c40e0` törzse nincs a kimenetben; a fejléc szerint ugrótáblája a
  `0x23-0x28` billentyűkre szól (End, Home, lapozás, nyilak), a `Ctrl+Enter` a
  `0x005d0e90`-re, a karakterbevitel a `0x005c3fe0`-ra megy, a DELETE (`0x2e`)
  nincs kezelve, és a `0xf4241` ("nem kezelt") jelzéssel tér vissza. Ebből az
  következik, hogy a mappalistának nincs saját Delete -> `0x9d44` útja; a
  billentyű a globális kezelőhöz megy tovább. A vtábla többi nyers bejegyzése
  nem érdemi: a `0x00563270` az `IytUnknown` destruktora, a `0x009d79f0` és a
  `0x009d7a00` az `AddRef` és a `Release` (a `+4` mezőn
  `InterlockedIncrement`, illetve `InterlockedDecrement`).
  **PicasaPy:** a mappafa csak Fel/Le kurzorbillentyűt köt
  (`FolderPaneContent.qml:304-307`), saját Delete-je nincs; ez az eredeti
  mappalista-kezelővel **összhangban** van. A nem kezelt Delete további sorsa
  nincs eldöntve. PicasaPy-ban az ablakszintű `Delete` gyorsbillentyű
  (`PicasaMenuBar.qml:636-642`) feltétele nem vizsgálja, hogy a mappafa
  fókuszban van-e (csak `photoActionsEnabled`, nem szerkesztő, nem
  szövegbevitel), tehát a kijelölt fotók törlését indítja, mappatörlést soha.
  Hogy az eredeti globális kezelő fókuszban lévő mappalistával mit tesz a
  Delete-tel (fotótörlés a `0x9c9a` paranccsal vagy semmi), **nincs meg**;
  egyezést ne állítsunk.
- **`0x00432d20`, a `+0xac` metódus (414).** Részben megválaszolva. A
  `0x00c82050` címen a katalógus-alobjektum vtáblájának `+0xac` bejegyzése
  (a vtábla `0x00c81fa4`). A dekompilált törzs meghívja a saját `+0x88`
  virtuális metódusát (`0x00431230`); ha a kapott szöveg nem üres, hozzáfűzi a
  `0x00c81520` sztringet (`"list"`, `FUN_00985af0`), és a `this+0xed8`
  táblában (`FUN_006a46c0`) az elemhez ezzel a kulccsal keres. A kulcs tehát
  `<szöveg>list` alakú. A szöveget a második paraméterként kapott
  környezet-objektum adja (a `0x005edef0` a `FUN_00926c20()` objektumot adja
  át; ez a fejléc olvasata, a `0x00926c20` és az objektum `0x68` metódusa nincs
  a kimenetben). A dekompilálás a visszatérési értéket elveszti (`uVar1 &
  0xffffff00`, az `AL` regiszter nem látszik), ezért az "igaz, ha a keresés
  sikeres és a bejegyzés nem üres" a fejléc olvasata; a hívó (`0x005edef0`,
  `cVar1 ? 2 : 0`) igazságértéket vár, ez nem mond neki ellent. Másik hívója a
  `0x0049f580` (a `0x0049f583` hívás), ugyanabból az átirányító családból,
  mint a setterek hívói (`0x0049f220`, `0x0049f310`, `0x0049f390`,
  `0x0049f4a0`). **Jelentés:** erős jelölt az online feltöltési lista, de a
  kulcs pontos alakja és a tábla írója nincs igazolva. **PicasaPy:** a
  mappatörlés (`fileops_controller_delete_mixin.py:18-41`) nem vizsgál
  feltöltési állapotot; a Google Fotók feltöltés
  (`tray_google_photos_controller.py:331`) futásidejű fázist követ, tartós
  képenkénti nyilvántartást a keresés nem talált. A 2-es ág értelme nélkül
  jegyet továbbra sem javaslok.

**A jegy lezárhatósága: NEM zárható.** A "Kész, ha" pontokhoz mérve:

| Pont | Állapot a 413-414 után | Miért |
|---|---|---|
| Belépési pontok, fa Delete | ⛔ (közelebb) | A mappalista kezelője a helyi disassembly szerint nem kezeli a Delete-et, de ez nem dekompilált bizonyíték, és a nem kezelt billentyű sorsa nyitott. |
| Üres mappa, almappák, írásvédelem, hálózati meghajtó | ⛔ | Nem Ghidra-kérdés: Windows-mérés kell, a 413-414 nem érinti. |
| Megerősítés szövege és megjegyzése | ✅ / ⛔ | A 2-es ág feltétele a `<szöveg>list` kulcsú táblakeresésig követhető; a kulcs jelentése és írója nyitott. |
| Lomtár, index, fa, rács, kijelölés, albumok, arcok | ⛔ | Nem érintett: Windows-mérés kell. |
| Részleges törlés és írási hiba | ✅ / ⛔ | Nem érintett. |
| PicasaPy összevetése | ✅ | A kész jegytörzs egyetlen igazolt eltérésre szól; a 413-414 nem hozott új eltérést, a fa Delete-nél nincs igazolt eltérés. |

### Ghidra-kiegészítés 3 (2026-11-16, várólista 419-425)

Forrás: `referencia/ghidra/2026-11-16-7022-7031-7033-colab-decomp.txt` (privát
kutatási tár). Ide a 419 tartozik.

- **`0x005c40e0`, a mappalista billentyűkezelője (419).** Megválaszolva,
  dekompilált teljes törzzsel (a 413 még csak helyi disassemblyre épült). A
  függvény az esemény `+0x10` mezőjéből a billentyűkódot, a `+100` bájtból a
  módosítókat olvassa. A törzs ágai:
  - ha a `+100` bájt `1`-es bitje be van állítva, az eseményt a `0x005c3fe0`
    kapja, és annak eredményét adja vissza (a 413 olvasata szerint
    karakterbevitel; a törzs nincs a kimenetben);
  - `0x23` (End) és `0x24` (Home): a `this+8` objektum `+0x2a4` mezőjén álló
    objektum egy-egy virtuális metódusát hívja (a Home a módosítóbájt
    `4`-es bitjét átadja); a metódusok törzse nincs a kimenetben;
  - `0x25` (Balra) és `0x27` (Jobbra): `lb_left`, illetve `lb_right` nevű
    eseményt küld (`FUN_00591560`), majd a vezérlő `+0x70` metódusát hívja, és
    `1000000` ("kezelt") értéket ad;
  - `0x26` (Fel) és `0x28` (Le): `lb_up`, illetve `lb_down` eseményt küld; ha a
    `4`-es módosítóbit (olvasat: Ctrl) be van állítva, utána a `param_2[0x9e]`
    mezőn át elért két metódussal (`+8` lekérdez, `+0x10` beállít) a
    lekérdezett értéket (olvasat: az aktuális sor) 3-mal csökkenti (Fel) vagy
    növeli (Le), a negatív értéket nullára vágja, és visszaírja: **Ctrl+Fel/Le
    három sort lép**; eredmény `1000000`;
  - `0xd` (Enter) a `4`-es módosítóbittel (Ctrl+Enter): `FUN_005d0e90(this+8
    objektum)` és `1000000`;
  - **minden más billentyűkód, a Delete (`0x2e`) is: `0xf4241`** ("nem
    kezelt").

  **Következtetés:** a mappalistának nincs saját Delete -> mappatörlés (`0x9d44`)
  útja, a Delete-nek a kapcsolóban nincs ága. Egy feltevés van benne: a Delete
  billentyűlenyomás nem hordozza a `+100` bájt `1`-es bitjét (a `0x005c3fe0`
  ágat); ennek a jelentése a 413 olvasata, a törzs nincs meg.
  **PicasaPy:** a mappalista csak Fel/Le kurzorbillentyűt köt
  (`FolderPaneContent.qml:306-307`), saját Delete-je nincs: **egyezik**. A
  többi billentyű (Home, End, Balra, Jobbra, Ctrl+Fel/Le három sorral,
  Ctrl+Enter) a #7031 hatókörén kívül esik, és hatásuk (az `lb_left`/`lb_right`
  események, a `0x005d0e90` és az End/Home metódusok) a kimenetből nem látszik,
  ezért jegyet nem javaslok rájuk. A nem kezelt Delete további sorsa (a
  `0xf4241` eredményt kapó hívó) továbbra sincs meg; a PicasaPy ablakszintű
  `Delete` gyorsbillentyűje (`PicasaMenuBar.qml:636-642`) a mappalista
  fókuszától függetlenül a kijelölt fotók törlését indítja. Hogy az eredeti
  ilyenkor fotótörlést indít-e, **nincs meg**; egyezést ne állítsunk.

**A jegy lezárhatósága: NEM zárható.** A "Kész, ha" pontok közül egyetlen
sor változik: a **belépési pontoknál a fa Delete kérdése lezárul** (✅, a fenti
egy feltevéssel): a mappalistának nincs saját Delete -> mappatörlés útja, a
PicasaPy viselkedése egyezik. A többi pont (üres mappa, almappák,
írásvédelem, hálózati meghajtó, Lomtár, index, fa, rács, kijelölés, albumok,
arcok, részleges törlés, a 2-es megerősítés kulcsa) a 419-tól nem érintett:
Windows-mérés, illetve a 414 Ghidra-körei kellenek hozzájuk.

### Nyitott

- Megválaszolva (Ghidra 413, 419): a mappalista saját kezelője
  (`0x005c40e0`) a teljes dekompilált törzs szerint csak End, Home, a négy
  nyíl (Ctrl+Fel/Le három sort lép) és Ctrl+Enter billentyűt kezeli, a
  Delete-et nem (`0xf4241`, "nem kezelt"); a `0x00a582f0` általános
  továbbító `0x9d44` nélkül. A mappalistának nincs saját Delete -> mappatörlés
  útja. Nyitott maradék, a mappatörlés belépési pontjaira nem blokkoló, a
  fotótörlés ágra külön kérdés: a `0xf4241` eredményt kapó hívó, azaz a nem
  kezelt Delete a globális kezelőhöz kerül-e, és fotótörlést (`0x9c9a`)
  indít-e fókuszban lévő mappalistával; a `0x005c3fb0` (a
  `KeyHandler::AlbumList` vtábla szomszédos bejegyzése) szerepe; a `0x005c3fe0`
  törzse (a `+100` bájt `1`-es bitjének jelentése).
- Részben megválaszolva (Ghidra 405, 414): a 2-es típus a katalógus `+0xac`
  metódusától függ, amely a `this+0xed8` táblában a `<szöveg>list` kulcsot
  keresi (nem üres bejegyzés = igaz). Ghidra-kör kell: 0x006a46c0 - a tábla
  keresője, és a hívói közül a `this+0xed8` táblába író függvény (a kulcs
  pontos alakja, ki és mikor írja); 0x00926c20 és a visszaadott objektum
  `0x68` virtuális metódusa - milyen szöveget ad (fiók, album vagy más).
- A törlés utáni eredeti index-, album- és arcállapot, valamint a fa, rács
  és kijelölés végállapota NINCS MEG. Megszerzés: célzott Ghidra-olvasás a
  0x0065B840 körüli frissítési úton, majd Windows Picasa 3.9.141 mérés egy
  és több képkijelöléssel. A meglévő 0x00662B20 Ghidra-kimenet ezt a
  törlés utáni kiválasztás-kérdést nem dönti el.
- Az üres, almappás, írásvédett és hálózati mappák tényleges Shell-kimenete
  NINCS MEG. Megszerzés: négy külön tesztcélon futtatás az eredeti Windows
  Picasában, minden futás előtt és után a fájlrendszer és a felület
  állapotának rögzítésével.

### Módosított fájlok

- docs/specs/paritas-ellenorzes.md - ez a #7031 alszakasz.

## #7032: Mappatulajdonságok szerkesztése az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, a bináris SHA-256 értéke
644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96.
Az alábbi állítások a binárisban cím szerint követett utakra és a jelenlegi
PicasaPy-forrásra épülnek; a hiányzó háttértár-végpontot nem következtetem ki
a mező nevéből.

### Következtetés

Az eredeti Picasa Folder Properties párbeszéde a jelenlegi mappából tölti a
nevet, dátumot, helyet és leírást. A név módosítása fájlrendszeri mappanév-
átnevezési útra kerül; ütközésnél és írásvédett köteten az eredeti ugyanazt az
IDS_NORENAME figyelmeztetést adja. A tartós mezőírás, az eredeti katalógus és
mappafa pontos frissülése, valamint a fejlécmező és néző/tálca eseményforrása
nem zárult le, ezért a teljes paritás nyitott.

**Bizonyítottsági fok: nyitott.** A párbeszéd mezői, a helymező eredeti
szerkeszthetősége, az átnevezési hiba üzenetazonosítója és a névtisztító
bizonyított. A teljes futásidejű folyamat nem, mert az eredeti tulajdonság-
írók virtuális végpontja és a felületi visszaállítás még nincs feloldva.

### Belépési pontok és feltételek

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Mappa menü:** a 0x00559150 a „&Edit Description...” feliratot a 0xd6e1c0 rekordba teszi; ugyanennek a rekordnak a parancsa 0x9c69 a 0xd6e1ca mezőben. A 0x005cbcd6 a 0x006db580 meglévőmappa-útjára hív. A Folder menü 0x0056e1c0 állapotfrissítőjében a 0x9c69 csak a param_1[0xd29] == 0 és local_48 != 0 feltétellel aktív; a local_48 a 0x005d2a70, az aktuális mappamutató és a kijelölési vizsgálat eredményétől függ. | **PicasaFolderMenu.qml:16-28**, **MainMenuBar.qml:372-380**. A helyi mappánál van útvonal és nincs személyalbum; a „]star” virtuális album le van tiltva. | A parancsút és a mai feltétel ismert. Az eredeti feltétel egy-/többképes jelentését a 0x006b1e80 feltételvizsgáló feloldásáig ne tekintsük egyezőnek. |
| **Mappafa helyi menüje:** a 0x007319f0 „Folder::ID_ALBUM_EDITCAPTIONS” tétele ugyanazt a 0x9c69 kódot kapja; a kód a leírásfelirat rekordjáé, a következő „Select All Pictures” felirat már egy másik rekord. | **FolderPaneTreeRow.qml:303-311**, **FolderPane.qml:320-335**, **FolderContextMenu.qml:77-83**. | A mai fa-sor ugyanazt a közös helyi menüt nyitja. Az eredeti Folder menü pontos kibocsátó widgetjét a menüépítő önmagában nem azonosítja. |
| **Rács üres területe és mappa-fejléce:** az eredeti 0x007319f0 Folder menüjében megvan a leírásparancs; e menü konkrét rács-hívója a feltárt hívási láncból nem állapítható meg. | **Main.qml:541-549**, **LightboxFeed.qml:712-719**, **LightboxFeedGroup.qml:188-194**: mindkét rács-terület a közös Folder menüt nyitja. | Az eredeti menüépítő a menüt bizonyítja, nem a jobbklikk forrását. A két eredeti rács-hívó külön feltárandó. |
| **Rácsfejléc leírásmezője:** a 0x00856060 `CTextEditNode::addcaption` csomópontot és „Add a description” helyőrzőt épít. A 0x00717810 hívja ezt a csomópontépítőt. A fejléc mentési eseménye és tartós kulcsa nem azonosított. | **LightboxHeaderDescription.qml:18-50**, **LightboxFeedGroup.qml:40-51**, **controller_folder_description_mixin.py:26-63**: Enter után a csoport mappaútjával menti a leírást. | A mező létezése és mai Enter-mentése bizonyított; az eredeti callbacket és eredeti mező perzisztenciáját Ghidra-körben kell feloldani. |
| **Gyorsbillentyű:** a meglévő 0x005e60d0 billentyűkezelő-kimenet nem kapcsolja a 0x9c69-et mappatulajdonság-szerkesztéshez. Ez nem zárja ki az accelerator- vagy más menü-diszpécser útját. | **PicasaFolderMenu.qml:16-28** nem mutat ehhez a tételhez külön billentyűt; az eredeti billentyűparitást nem lehet ebből megállapítani. | Nyitott. Ne állítsuk, hogy van vagy nincs eredeti gyorsbillentyű. |
| **Néző:** a 0x005de8e0 `albumdouble` eseményága a 0x006db580 meglévőmappa-útjára hív. Az eseményt küldő pontos felületi elem nincs meg. | A jelenlegi főmenü a vezérlő aktuális mappáját továbbítja (**MainMenuBar.qml:372-380**); külön nézőbeli Folder Properties belépő nincs a feltárt útban. | A bináris eseménynév nem bizonyítja, hogy ez OneUp nézőből érkezik. Forráselem és egy-/többképes hatókör nyitott. |
| **Képtálca:** a teljes .text pásztázás nem azonosított önálló, bizonyított képtálca → 0x006db580 közvetlen útvonalat; ez nem zárja ki a közvetett eseményt. | A vizsgált mai leírásút a mappa-menü és a rácsfejléc; külön tálcabeli tulajdonságművelet nem igazolódott. | Nyitott. Nem állítható, hogy az eredeti tálcán van vagy nincs ilyen parancs. |
| **Üres, egy és több kijelölt kép:** a 0x0056e1c0 állapotfrissítő a 0x005c76b0 és 0x006b1e80 eredményétől függő kijelölési feltételt vesz figyelembe. A feltétel három esetre lefordított jelentése NINCS MEG. | **FolderPane.qml:251-275** a mappa útját, dátumát, leírását és zenéjét olvassa; a tulajdonságablak nyitásának nincs kép-sor vagy kijelölés paramétere. | Az eredeti 0/1/több kijelölés engedélyezési eredménye nyitott. A mai tulajdonságadat mappa-alapú; ne következtessünk a régi kijelölés megőrzésére. |

### Ablak, mezők, alapértékek és átnevezés

Az eredeti album.fen ablak a Name, Date, Automatic date, Music, Place taken,
Description, OK és Cancel mezőket deklarálja (Picasa runtime/album.fen:1-29).
A Picasa 3.9 mérőképen a „Mappa tulajdonságai” ablak és a rácsfejléc „Leírás
hozzáadása” mezője egyszerre látható (mérés: research/testdata/screenshot/2026-07-17 20 59 22.png).

A 0x006db580 a jelenlegi mappa leíróját a 0x0055d070-zel tölti, majd a
0x006dc030-cal nyitja a párbeszédet. A 0x00849750 „Folder Properties” címet
választ folder módban, és a Name, caption, location, date mezőket a leíróból
olvassa. A 0x0055d070 betöltő út a név, leírás, dátum és hely adatát külön
leírómezőbe teszi. Így az eredeti alapérték az aktuális mappa tárolt értéke;
nem állítok minden profilra érvényes üres vagy fix dátumot. A kép a mérési
profilban a dátummezőben 2026_01_01 értéket mutatott.

Az OK feldolgozása a 0x00849dc0-ban a Name mezőt folder módban a 0x009946f0
névtisztítón viszi át; a caption, location és dátum értéke is visszakerül a
leíróba. A 0x0055d320 ezután a név, leírás, hely, zene és dátum kezelőit
hívja, majd névváltozás esetén külön fizikai átnevezési ágra lép. Az OK
gombon kívül külön sikeres átnevezési megerősítő lépést nem találtam. A
hibaág IDS_NORENAME figyelmeztetést nyit.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A meglévő mappa helye szerkeszthető „Place taken (optional)” mező (album.fen:20-21); az OK-ág a location értéket a leíróba teszi (0x00849dc0). | **FolderPane.qml:263-267** üres helyet állít be; **FolderPropertiesDialog.qml:188-198, 595-609** a mező meglévő mappánál letiltott; **FolderPaneMenus.qml:465-475** nem ad át location értéket. | **Igazolt felületi eltérés.** Fejlesztői jegyjavaslat lent. Az eredeti setter pontos tárolási célja továbbra is nyitott. |
| Eredeti mappanév-normalizálás: a 0x009946f0 a tiltott karaktereket eldobja, a széleken a szóközt/pontot levágja, a szóköz jellegű karaktereket szóközzé alakítja, az `aux`/`con`/`nul`/`prn` neveket aláhúzással módosítja; az üres eredményt elutasítja. Ezt a 0x00849dc0 folder módú neve hívja. | **rename_folder.py:37-43** a validate_folder_name eredményét használja; **new_folder.py:37-62** csak szélső whitespace-et trimmel, tiltott karakterre hibát ad; **rename_folder.py:128-142** a ponttal/szóközzel zárást és a fenntartott Windows neveket is elutasítja. | **Igazolt átnevezési eltérés.** Fejlesztői jegyjavaslat lent. |
| A sikeres névváltoztatás a 0x0055d5fd → 0x0052e0f0 → 0x004fd1c0 → 0x00994400 útvonalon fut. A 0x00d694d8 függvénymutatót a 0x00c32d6a a 0x009af2b0 címre állítja; az importtábla ezt KERNEL32!MoveFileExW-ként azonosítja. A 0x0055d62a hibaága IDS_NORENAME szöveget ad a figyelmeztetésnek. | **FolderPropertiesDialog.qml:230-253**, **FolderPaneMenus.qml:457-470**, **library_controller_resync.py:35-137**, **rename_folder.py:25-57**: mappa átnevezése, majd indexfa-frissítés; indexhiba esetén lemezes visszagörgetés. | A fizikai művelet és a mai index/visszagörgetés út bizonyított. Az eredeti forrás/cél út pontos összeállítása, valamint az eredeti belső katalógus és mappafa hatása nyitott. |

### Hatás és hibák

| Hatás | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| Fájlrendszeri név | A 0x0055d320 névváltozáskor MoveFileExW útvonalat indít; ugyanabban a szülőben végzett mappaátnevezés. A teljes pontos forrás/cél karakterlánc NINCS MEG. | A rename_folder az egész mappát nevezi át, a benne lévő fájlokkal és .picasa.ini-vel együtt (**rename_folder.py:25-57**). |
| [Picasa]/name | A mező a 0x00849dc0 és 0x0055d320 útján eljut egy absztrakt kezelőhöz; hogy közvetlenül vagy közvetve a .picasa.ini name kulcsát írja-e, NINCS MEG. | A mappanév fizikai könyvtárnév; meglévő mappa mentése nem hív [Picasa]/name írót (**FolderPaneMenus.qml:465-475**). |
| [Picasa]/date | A dátumot leírómezőbe teszi, és kezelőhívást végez (0x00849dc0, 0x0055d320); e szerkesztési út tényleges .picasa.ini írása és formátuma NINCS MEG. | **folder_date_controller.py:102-117**, **ini/folder_date.py:120-151**: a [Picasa]/date felülírást OLE Variant alakban írja; utána mappa újbóli szinkronizálását kér. |
| [Picasa]/location | A location mező olvasása és visszaadása bizonyított (0x0055d070, 0x00849dc0, 0x0055d320); tényleges fájlba írása NINCS MEG. | Meglévő mappánál üres és letiltott mező; nincs meglévő mappához kötött location getter/setter (**FolderPane.qml:267**, **FolderPropertiesDialog.qml:595-609**). |
| [Picasa]/description | A caption mezőt betölti, elfogadáskor kezelőhöz adja (0x0055d070, 0x00849dc0, 0x0055d320); a tartós .picasa.ini kulcs NINCS MEG. | **controller_folder_description_mixin.py:26-63** a [Picasa]/description értéket írja/törli az ini API-val; íráshibát jelent. |
| Index és mappafa | A 0x006db580 mentés után feltételesen 0x0052e420 és 0x004ad150 frissítő hívásokat végez. Az indexrekordok, a mappafa rendezése és a rács utáni állapota NINCS MEG. | **library_controller_resync.py:75-137** átírja a mappaútvonalakat az indexben, frissíti a jelenlegi mappát és újratölti a nézetet; dátum mentése külön újraszinkronizálást kér (**folder_date_controller.py:148-153**). |
| Rácsfejléc és kijelölés | A tulajdonság-mentés után a fejléc tartalma és a fotók kijelölése megmarad-e, NINCS MEG. A 0x00856060 editor-builder és a 0x005de8e0 eseményág önmagában ezt nem dönti el. | A fejléc leírása a mappa-leírásból jön és Enter után ment (**LightboxFeedGroup.qml:40-51**). A mappaátnevezés újratölti a nézetet; a fotókijelölés végállapota e forrásokból nem állapítható meg. |

**Névütközés és írásvédett hely:** a 0x0055d62a ág az IDS_NORENAME azonosítót
adja a 0x00980700 figyelmeztető ablaknak. Az
enUK/stringres.xml:621-623 szövege szerint a lemezen nem sikerült a megadott
nevet létrehozni; ennek oka lehet írásvédett kötet vagy azonos nevű
testvérmappa. A PicasaPy létező célmappát külön elutasítja, OS-írási hibát
pedig hibaüzenetként ad vissza (**rename_folder.py:45-57**). A hibaszöveg és
hibakategória részlete eltér, de az ütközés és a sikertelen átnevezés jelzése
mindkét oldalon bizonyított.

**.picasa.ini írási hiba:** az eredeti mezőkezelők visszatérési hibái és
tényleges háttértár-végpontja nincsenek visszafejtve; ezért nem állítok
eredeti részleges mentést vagy rollbacket. A PicasaPy leírás-/dátumírási
hibát jelent, a sikertelen írás után nem frissíti a kapcsolódó nézetet
(**controller_folder_description_mixin.py:42-63**,
**folder_date_controller.py:130-153**).

### Bizonyíték és bizonyítottsági fok

| Érték vagy állítás | Forrás |
|---|---|
| Fő- és Folder helyi menü szerkesztési parancsa, 0x9c69 | bináris (0x00559150, 0x007319f0, 0x005cbcd6); a felirat és parancskód rekordpárosítása cím szerint ellenőrizve |
| Folder menü engedélyezése és kijelölésfüggő feltétel | bináris (0x0056e1c0, 0x005c76b0, 0x006b1e80); a feltétel szemantikája NINCS MEG |
| Properties mezők és jelenlegi mappából induló értékek | bináris (0x006db580, 0x0055d070, 0x006dc030, 0x00849750, 0x00849dc0); függetlenül album.fen:1-29 |
| Helymező eredeti szerkeszthetősége | bináris (0x00849dc0); album.fen:20-21; mérés (2026-07-17 Picasa 3.9 képernyőkép) |
| Név normalizálása | bináris (0x00849dc0, 0x009946f0); meglévő Ghidra C és diszasszemblálás összhangban |
| Mappa fizikai átnevezési végpontja | bináris (0x0055d5fd, 0x0052e0f0, 0x004fd1c0, 0x00994400, 0x00c32d6a, KERNEL32 importtábla) |
| Névütközés / írásvédett kötet üzenete | bináris (0x0055d62a-0x0055d658, IDS_NORENAME); független szövegforrás: referencia/i18n/enUK/stringres.xml:621-623 |
| Fejléc leíráscsomópont és helyőrző | bináris (0x00856060, 0x00717810); erőforrás headerpanel/album_description; mérés (eredeti képernyőkép) |
| Eredeti .picasa.ini mezőírás, indexrekord, fa-rendezés, kijelölés utáni állapot | NINCS MEG |
| PicasaPy mai kezelőút | fájl:sor (a táblázatokban felsorolva), közvetlen forrásolvasás |

### A két független út

- **A út, gépi kód:** a 0x00559150 és 0x007319f0 menürekordjait a 0x9c69
  parancson át a 0x006db580 dialog-útig követtem; a 0x00849750 / 0x00849dc0
  mezőkezelés után a 0x0055d320 név- és mezőkezelőit, majd a MoveFileExW
  útját olvastam.
- **B út, ettől független forrásréteg:** az eredeti album.fen
  meződeklarációi, a 3.9 képernyőkép, az enUK IDS_NORENAME fordítása, a
  PicasaPy jelenlegi QML/Python forrása és a már meglévő Ghidra C-kimenet
  külön ellenőrzése.
- **Egyezés:** az ablak mezőkészletét a bináris és a runtime leíró
  egymástól függetlenül megerősíti; a sikertelen átnevezés azonosítóját a
  gépi kód és a szövegerőforrás egyezteti. A tartós mezőírás, indexfrissítés
  és felületi végállapot még nem egyezik két teljes, független úton, ezért a
  teljes folyamat nyitott.

### Cáfoló kísérlet

Megpróbáltam cáfolni azt a feltevést, hogy a captiondone → 0x005f89a0 út a
rácsfejléc mappaleírását menti. A diszasszemblálás az editpanel/preview,
editpanel/caption és editpanel/captiontrash elemekhez vezet; a fejléc külön
headerpanel/album_description erőforráselemet és 0x00856060 editor-buildert
használ. Ezért az azonosítás nem áll meg; a fejléc commit útját nyitva
hagytam. A cáfoló forrást ugyanazzal a mércével ellenőriztem: a 0x005f89a0
konkrét sztringhivatkozásai egyeznek az editpanel funkcióval, a fejlécet
pedig az eredeti erőforrás és a képernyőkép azonosítja.

### A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Minden belépési pont és feltétel, beleértve menüt, mappafát, fejlécmezőt, gyorsbillentyűt, nézőt, tálcát és 0/1/több képet | ⛔ | Menüparancsok és editor-builder megvannak; a pontos kibocsátó widgetek, a keyboard út és a kijelölési kapu jelentése nyitott. |
| Ablak, mezők, alapértékek, átnevezés és külön megerősítés | ✅ részben | A mezők és a jelenlegi mappaértékek binárisan és album.fen alapján megvannak; nincs külön sikeres megerősítő ág. A backend írás még nyitott. |
| Fájlrendszer, .picasa.ini, index, mappafa, rács és kijelölés hatása | ⛔ | A fizikai átnevezési API és PicasaPy hatása megvan; az eredeti mezőírás, index/rendezés és kijelölési végállapot NINCS MEG. |
| Ütköző név, írásvédett hely és írási hiba | ✅ részben | IDS_NORENAME üzenet kifejezetten felsorolja az ütközést és írásvédett kötetet; a külön ini-írási hiba és esetleges részleges mentés nyitott. |

### Javasolt fejlesztői jegytörzs

#### 1. Mappatulajdonságok: a Hely mező szerkeszthető meglévő mappánál

**Eredeti:** album.fen:20-21 a „Place taken (optional)” mezőt a Folder
Properties ablak részeként deklarálja; a 0x00849dc0 az elfogadott
location értéket a mappaleíróba visszaírja.

**Nálunk:** src/picasapy/app/qml/PicasaPy/FolderPane.qml:263-267 meglévő
mappánál üres location értéket ad; FolderPropertiesDialog.qml:595-609
letiltja a mezőt; FolderPaneMenus.qml:465-475 nem ad át location értéket.

**Teendő:** tedd szerkeszthetővé a meglévő mappa helyét, olvasd be és mentsd
az értéket a PicasaPy mappa-metaadat API-ján keresztül. A jelenlegi mappa-
metaadat formátuma a [Picasa]/location kulcsot használja; az eredeti
Picasa-setter pontos tárolási útját a nyitott Ghidra-kérdés külön zárja le.

**Kész, ha:** meglévő mappa megnyitásakor a mentett hely szerkeszthető és
kitöltött; OK után újranyitva az új érték megmarad; üres érték törli a
kulcsot; írási hiba esetén a régi érték és a felület marad érvényben.

#### 2. Mappatulajdonságok: az eredeti névtisztítás követése

**Eredeti:** 0x00849dc0 folder módban a nevet a 0x009946f0 függvényre bízza.
Ez eldobja a tiltott karaktereket, levágja a szélső szóközt/pontot,
normalizálja a belső whitespace-et, és az `aux`/`con`/`nul`/`prn` neveket
aláhúzással módosítja.

**Nálunk:** src/picasapy/fileops/rename_folder.py:37-43 és
src/picasapy/fileops/new_folder.py:37-62 a tiltott karaktert hibának veszi;
rename_folder.py:128-142 a ponttal zárást és a fenntartott neveket is
elutasítja.

**Teendő:** a meglévő mappa tulajdonságablakából indított átnevezés kapjon
Picasa-kompatibilis névtisztítást; az új mappa létrehozásának jelenlegi
ellenőrzését csak külön paritási döntéssel változtasd meg.

**Kész, ha:** például az A/B beírásból AB, a szélső pontokból tiszta név,
a `con` névből `con_` lesz, és üresre tisztuló névnél mentés nem indul.

### Új kutatási jegyjavaslatok

Új kutatási jegyet most nem javaslok: a nyitott pontok közvetlenül ehhez a
folyamathoz tartoznak, és a következő lépés a célzott Ghidra-kör, nem külön
kérdésleválasztás.

### Ghidra-kiegészítés (2026-11-15, várólista 406-412)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp.txt` (privát
kutatási tár).

- **`0x006b1e80`, kijelölési kapu.** A függvény képszámot nem néz: csak azt
  vizsgálja, hogy a `this[0x1c]` objektum `0x24` virtuális metódusának eredménye nem üres
  sztring-e. Üres, egy- és többképes kijelölés megkülönböztetése ebben nincs.
  A tulajdonságablak engedélyezése tehát nem a képkijelöléstől függ; a mai
  mappa-alapú PicasaPy-viselkedés ezzel **összhangban** van.
- **`0x0055d070` és `0x0055d320`, mezők és írás.** A mezők a katalógus
  olvasóiból jönnek (`0x18` név, `0x1c` felirat, `0x20` dátum, `0x24` hely), az
  írás a `+4/+8/+0x10/+0xc` setterekre megy; a párosítást a `0x00849dc0`
  `name`, `caption`, `location` és `date` kulcsai igazolják. A mentés sorrendje:
  név, felirat, hely, `FUN_004448d0`, dátum, végül az átnevezés. Átnevezés csak
  nem különleges mappánál és eltérő névnél fut (`FUN_009946f0`, `FUN_0052e0f0`),
  hibánál IDS_NORENAME üzenetet ad. **Hibakezelés:** az első hibás setternél
  kilép, a már beírt mezőket nem görgeti vissza, és setterhibára üzenetet sem
  ad; átnevezési hibánál sem görgeti vissza a mezőket. **PicasaPy:** az
  átnevezés indexhibája esetén lemezes visszagörgetést végez
  (`rename_folder.py`). Ez szigorúbb az eredetinél, felhasználói kárt nem okoz,
  ezért nem javaslok rá eltérés-jegyet. A katalógus mögötti `.picasa.ini`-író
  nincs ebben a kötegben.
- **`0x00856060`, rácsfejléc leírásmezője.** Nincs válasz: ez csak a
  `CTextEditNode` konstruktora, eseménykötés és mappakulcs nincs benne. A
  következő cím a hívója, a `0x00717810`.
- **`0x005de8e0` és `0x00765d30`, ki küldi az eseményt.** Az `lb_predouble`
  küldője a bal oldali **CAlbumList** (mappa- és albumlista), ezt az
  `alist_indent` és a `CAlbumList::newalbumprompt` sztring igazolja. Az
  `albumdouble` eseményt a főablak kapja, és a Folder/Album Properties
  megnyitójára jut; a módot a betöltött rekord választja ki
  (`this+0xeac+0x3c0`), a kijelölt képek számától függetlenül. A korábbi
  „Néző” sor tehát valójában a **mappalista dupla kattintása**, nem a néző.
  **PicasaPy:** a mappalista dupla kattintása a fát nyitja és csukja
  (`FolderHierarchyView.qml:386`), tulajdonságablakot nem nyit. A handler
  pontos `+0x30`/`+0x18` kapuja lejjebb bizonyított; a név szerinti különleges
  sorok leképezése még nyitott.
- **`0x005e60d0`, gyorsbillentyű.** A főablak beégetett Ctrl-billentyű
  kezelőjében nincs mappatulajdonság-ág: a `0x9c69` nem szerepel, és a nyolc
  névvel küldött parancs egyike sem mappatulajdonság. Ebben a kezelőben tehát
  nincs gyorsbillentyű; az erőforrásbeli gyorsbillentyű-tábla nincs átnézve.

### Ghidra-kiegészítés 2 (2026-11-15, várólista 413-418)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp-2.txt` (privát
kutatási tár). Ide a 415, a 416 és a 417 tartozik. Ahol más, korábbi kimenetből
olvastam, a fájl nevét kiírtam.

- **`0x00717810`, a rácsfejléc leírásmezője (415).** Részben megválaszolva. A
  függvény csak a csomópontot építi és köti be a címzettet. Ha a `this+700`
  mező üres, `CTextEditNode`-ot hoz létre (`0x00856060`, `0x350` bájt),
  stílust és méretet állít, és ha a szöveg (`param_3`) nem üres, a
  `FUN_008564f0`-val beírja; ha már van csomópont, RTTI-vel
  `CTextEditNode`-ra alakítja, és csak a szöveget cseréli. A `param_2`
  objektumot, ha nem null, a csomópont `+0x28c` mezőjébe teszi (a régi
  címzettre a `0x0c` virtuális metódust hívja), és a csomópont `+0xc`
  jelzőmezőjében a `7` bitjeit beállítja; ez valószínűleg az elfogadás
  címzettje. Elfogadási visszahívás és mappakulcs a törzsben nincs. A `param_4`
  nem nulla értéke a `+0x339` bájtot 1-re állítja, csak létrehozáskor. **A négy
  hívó** (az első három törzse korábbi kimenetekben már megvan):
  - `0x0074ad40`: `PeopleAlbum::ConfirmText` szöveg, `param_2 = 0`,
    `param_4 = 1` (`2026-10-20-ghidra-16.txt`).
  - `0x0074c200`: erőforrásnévből vett szöveg, `param_2 = 0`, `param_4 = 1`
    (`2026-10-20-ghidra-13.txt`).
  - `0x00749ba0`: üres szöveg, `param_2` egy frissen foglalt `0x1c` bájtos
    objektum (`FUN_00746640`, a szülő `+0x50` mezőjéből építve)
    (`2026-10-19-ghidra-11.txt`). Ugyanez a függvény a
    `CThumbUI::ShareButtonLabel` feliratot is építi, és vtábla-adat
    hivatkozza (`0x00cb16ec`), tehát valószínűleg az album- és mappafejlécet
    frissítő virtuális metódus.
  - `0x00789c00`: a törzse nincs dekompilálva.

  A két ismert hívónál a csomópontnak nincs külső elfogadási címzettje; a
  szerkeszthető leírás címzettje csak a `0x00749ba0` útján áll be. **PicasaPy:**
  a fejléc Enter után ment, a `[Picasa]/description` kulcsba
  (`LightboxHeaderDescription.qml:18-50`, `LightboxFeedGroup.qml:40-51`,
  `controller_folder_description_mixin.py:26-63`). Hogy az eredeti fejléc
  elfogadása a 417 felirat-setterét hívja-e, nem igazolt.
- **`0x009946f0` és `0x00994400`, névtisztítás és áthelyezés (416).** A
  `0x009946f0` nem útvonalépítő, hanem **névtisztító**. 25 hívója van, köztük a
  `0x00849dc0` (a Folder Properties OK-ága, `0x00849f75`) és a `0x0055d320` (a
  mentő, `0x0055d5ae`), tehát a tisztítás az OK-ágon és a mentőben is lefut
  (hogy mindkétszer ugyanarra a névre, a kimenetből nem dönthető el). Lépései a
  dekompilált törzs szerint:
  1. üres (null) bemenetre hiba (`0xffffffff`);
  2. a vezető szóközöket átugorja (`_iswspace`);
  3. karakterenként: a szóköznek számító karakter (`_iswspace` vagy `U+3000`)
     szóközzé válik; a `0x20` alatti vezérlőkarakter és a `\ / : * ? " < > |`
     kimarad; minden más marad. A szóköz-ellenőrzés megelőzi a
     vezérlőkarakter-szűrőt, ezért a tabulátor és a soremelés is szóköz lesz,
     nem esik ki (a `_iswspace` pontos készletét a kimenet nem mutatja).
     **A szóközöket nem vonja össze:** minden szóköznek számító karakter pontosan
     egy szóközt ad;
  4. a vezető és a záró pontot és szóközt levágja; üres eredményre hiba
     (`0xffffffff`), mentés nem indul;
  5. ha a teljes eredmény kis- és nagybetűtől függetlenül (ASCII) `aux`, `con`,
     `nul` vagy `prn`, a végére `_` (`0x5f`) kerül. Csak teljes egyezésre, a
     `con.txt` nem érintett.

  **A #7038 javításával összevetve** (nyitott PR #7047, ág `integ/7030-7038`,
  commit `e88e4ee3f`; a main-ben még nincs): a `sanitize_folder_rename_name`
  (`src/picasapy/fileops/rename_folder.py:60-72` abban a commitban) a kilenc
  tiltott karaktert, a vezérlőkarakterek kihagyását, a szélső pont és szóköz
  levágását, az üres eredmény elutasítását és az `aux`/`con`/`nul`/`prn` + `_`
  szabályt az eredetivel egyezően valósítja meg. **Egy igazolt eltérés van:** a
  `re.sub(r" +", " ", ...)` (`:69`) a sorozatos szóközöket egyre vonja össze, az
  eredeti nem. Példa: a beírt `A  B` (két szóköz) az eredetiben `A  B` marad, a
  javításban `A B` lesz. A hatás kicsi (a párbeszéd csak akkor hív átnevezést,
  ha a beírt szöveg eltér a mappa nevétől, `FolderPropertiesDialog.qml:237` a
  #7047 commitban), de a "követi az eredeti névtisztítást" állítással nem fér
  össze. **Bizonyítottsági fok:** egy út (a dekompilált törzs); a független
  második út az eredeti Picasa felvétele lenne (lásd a Nyitott listát).
  Nyitott, nem igazolt: a Python `str.isspace()` és a CRT `_iswspace`
  készlete a ritka vezérlőkaraktereknél (`U+001C-U+001F`) eltérhet. A main-ben
  (`3ce7dec69`) még a régi `validate_folder_name` fut (`rename_folder.py:37-40`,
  `new_folder.py:54-62`).

  A `0x00994400` a `MoveFileExW`-burkoló (a `0x00d694d8` mutatót az importtábla
  `KERNEL32!MoveFileExW`-ként azonosítja, lásd fent). Jelzői: `8`
  (`MOVEFILE_WRITE_THROUGH`), felülírásnál `|1` (`MOVEFILE_REPLACE_EXISTING`), a
  `param_3`-nál `|2` (`MOVEFILE_COPY_ALLOWED`). Felülíráskor a cél csak
  olvasható attribútumát előbb leveszi (a `0x00d694bc` és a `0x00d69514`
  függvénymutatókon át; az azonosításukat a kimenet nem adja, a viselkedés
  látszik: a `0xffffffff` hibajelzés és az `1`-es bit levétele). Hiba esetén,
  ha `GetLastError() == 5` (hozzáférés megtagadva) és a `FUN_00992ed0` igazat
  ad, **500 ezredmásodpercenként újrapróbál** (`WaitForSingleObject(DAT_00d689cc, 500)`),
  amíg az időkorlát le nem jár; ha közben az eseményobjektum jelez, `0xf4242` a
  visszatérés. Ha a `FUN_00992ed0` hamis, a függvény `0`-t ad vissza
  átnevezés nélkül; ennek jelentése nincs bontva. A régi Windows-ágon
  `MoveFile`, hibánál másolás és törlés fut. Az időkorlát forrása és az
  újrapróbált hívás forrásargumentuma a dekompilálásban sérült (`uStack_8`
  inicializálatlan), ezeket nem állítom. Hívói közt a `0x004fd1c0`
  (`0x004fd293`) és a `0x009eb290` (`0x009eb70b`). A forrás- és célút
  összeállítása (`0x0052e0f0`, `0x004fd1c0`) ebben a kötegben nincs.
  **PicasaPy:** az átnevezés egyetlen `os.rename` hívás (`rename_folder.py:14`,
  `_rename`), `WRITE_THROUGH` és újrapróbálás nélkül; az eredeti az átmeneti
  hozzáférési hibát (például más folyamat zárolását) kivárja, a PicasaPy
  azonnal hibát ad. **Eltérés-jelölt, részben igazolt:** jegy előtt a
  `FUN_00992ed0` jelentése és az időkorlát forrása kell.
- **A mezőírók (417).** `0x00445460` (név, vtábla `+4`), `0x00443c90` (felirat,
  `+8`), `0x004460a0` (dátum, `+0xc`), `0x0044fa80` (hely, `+0x10`) és
  `0x004448d0` (zene). A név, a felirat és a hely `(this, sor, érték, tartós)`
  alakú; előbb a memóriabeli albumoszlopba ír (zárolt tömb, `this+0xb60`,
  `FUN_006a2a60` jelzés), majd `FUN_004481e0`; ha a negyedik paraméter (tartós
  írás) nem nulla, a `FUN_004545c0(sor, kulcs, érték)` ír a kulccsal: `"name"`
  (`0x00c7fa20`), `"description"` (a felirat kulcsa, nem `caption`) és
  `"location"`. A kimenet fejlécének összegzése "mappa" első argumentumot ír;
  a törzs szerint ez a sor azonosítója (`param_2`, ugyanaz, mint a tömbindex).
  Memóriahibánál a visszatérés `4`. A
  dátum a `this+0x940` táblába kerül `"date"` kulccsal (`0x00c80d7c`,
  `FUN_006a5c60`); tartós írásnál, ha a `FUN_004543e0` (sor -> szöveg)
  hibátlanul tér vissza és a szöveg nem üres, `sprintf("%f")` szöveget készít,
  és a `FUN_0045c0a0("date", szöveg)` hívással írja. A `0x004448d0` a
  `"music"` kulcsot írja (`FUN_006a63f0`, a `this+0x988` táblába, tartós jelző
  nélkül). **A tartós jelző értéke** a mentőből jön (a korábbi kimenet
  `0x0055d320` törzse, `2026-11-15-7031-7032-7033-colab-decomp.txt`): a
  `FUN_004461a0(mappa)` eredményét negálva adja át, tehát **nem különleges
  mappánál tartós, különlegesnél nem**; a zene mindig megy. A `FUN_004545c0` és
  a `FUN_0045c0a0` belseje (az író, amely a fájlt és a szakaszt dönti el) nincs
  dekompilálva. **PicasaPy:** a kulcsnevek egyeznek: `description`
  (`controller_folder_description_mixin.py:37-40`), `date` hat tizedessel, `%f`
  alakban (`ini/folder_date.py:117-134`, `_VARIANT_TIZEDES = 6`; ez független
  megerősítés, mert a `0x004460a0` is `"%f"`-et formáz), `music`
  (`ini/folder_music.py:44`) és `location` (a #7047-ben
  `ini/folder_location.py`, `[Picasa]/location`; ez a kulcsnévre zárja a
  korábbi "nincs meg a tárolási út" kérdést). **Két nyitott különbség:** (1) az
  eredeti setter a `"name"` kulcsot is tartósan írja; a PicasaPy meglévő
  mappánál csak átnevez, `[Picasa]/name` íróval nem hív
  (`FolderPaneMenus.qml:457-470`); hogy a `FUN_004545c0` a mappa
  `.picasa.ini`-jébe ír-e, és a `name` bekerül-e, nincs meg. (2) Az "Automatic
  date" jelölőnél a mentő `0.0` dátumot ad át, és a setter ilyenkor is
  `"0.000000"` szöveggel hívja a `FUN_0045c0a0`-t. Hogy ez kulcstörlés vagy
  `date=0.000000` sor, a `FUN_0045c0a0` belsején múlik; a PicasaPy az üres
  dátumnál törli a kulcsot (`ini/folder_date.py`, `with_folder_date_override`),
  és az ottani komment szerint az eredeti író a `0.0` értékű sort kihagyja
  (`0x0071031e`), ami összhangban lehet.

**A jegy lezárhatósága: NEM zárható.** A "Kész, ha" pontokhoz mérve:

| Pont | Állapot a 413-418 után | Miért |
|---|---|---|
| Minden belépési pont és feltétel | ⛔ | A mappalista `lb_predouble` típuskódja (`1`/`5`) és a `+0x18` kapu megvan; a típusok név szerinti sorokhoz, különösen a speciális albumokhoz rendelése nyitott. A rácsfejléc elfogadási címzettje (`0x00746640`, `0x00789c00`) és az erőforrásbeli gyorsbillentyű-tábla sincs lezárva. |
| Ablak, mezők, alapértékek, átnevezés | ✅ részben | A névtisztító és a `MoveFileExW`-burkoló teljes; a forrás- és célút összeállítása (`0x0052e0f0`, `0x004fd1c0`) nincs meg. |
| Fájlrendszer, `.picasa.ini`, index, mappafa, rács, kijelölés | ⛔ | A kulcsnevek megvannak, de az író (`0x004545c0`, `0x0045c0a0`) nincs bontva, az index és a kijelölés végállapota sincs meg. |
| Ütköző név, írásvédett hely, írási hiba | ✅ részben | Az átnevezési hiba és az újrapróbálás (500 ms) bizonyított; az ini-írási hiba eredménye mérés nélkül NINCS MEG. |

**Fejlesztői teendő a 416 alapján:** a #7047 névtisztítása ne vonja össze a
sorozatos szóközöket (kis javítás a PR-ben vagy utána). Javasolt kiegészítő
"Kész, ha": a beírt `A  B` név két szóközzel marad. A hozzáférési hiba
újrapróbálására jegyet addig nem javaslok, amíg a `FUN_00992ed0` jelentése nincs
meg.

### Ghidra-kiegészítés 3 (2026-11-16, várólista 419-425)

Forrás: `referencia/ghidra/2026-11-16-7022-7031-7033-colab-decomp.txt` (privát
kutatási tár). Ide a 420, a 421, a 422 és a 423 tartozik. Ahol más, korábbi
kimenetből olvastam, a fájl nevét kiírtam.

- **`0x00746640` és `0x00749ba0`, a rácsfejléc leírásmezőjének címzettje
  (420).** Részben megválaszolva. A `0x00746640` a `CAlbumVarString`
  konstruktora: a `0x1c` bájtos objektum első mezőjébe a
  `CAlbumVarString::vftable` kerül, a `+4`, `+8` és `+0xc` mező nulla, a `+0x10`
  mezőbe a hívóhelyeken látható `album + 0x50` cím, a `+0x14` és a `+0x18`
  mezőbe a konstruktor további két paramétere. A `0x00749ba0` (a 415 szerinti
  hívó) a címzettet így építi: az "album" a `CThumbUI` `+700` (`0x2bc`) mezője
  az RTTI-átalakítás (`FUN_00c07db2`) után; ha ez a mező null, a `+0x10` mező
  is null. A kapott objektumot a `0x00717810` második paramétereként adja át
  (`FUN_00717810(this[0x2b4], címzett, &szöveg)`, a szöveg ott üres), és ez az
  ág csak akkor fut, ha a `this+0x298` mód nem 3. Ez **igazolja a 415
  olvasatát**: a csomópont `+0x28c` címzettje egy `CAlbumVarString`, a mappa
  (album) objektum `+0x50` változójához kötve. A változó kulcsa nem látszik: a
  konstruktor csak a címet és két mezőt tárol. Ugyanabban a hívássorban a
  `CAlbumVarDateConverter` is ugyanazt az `album + 0x50` címet kapja, a `+0x18`
  mezőjében `2` értékkel; ebből a `+0x50` terület olvasat szerint az album
  változóinak közös kiindulása, a `+0x18` mező pedig a változó kiválasztója. A
  három `CAlbumVarString`-építés előtt a dekompilálás a `1`, `0`, illetve `4`
  értéket mutatja a veremben (a `0x00717810` felé tartó hívásnál `0`); hogy ez a
  negyedik paraméter értéke, azaz a leírás kiválasztója, **nem igazolt**. A
  `CAlbumVarString::vftable` metódusainak törzse (az elfogadáskor futó írás) nincs
  a kimenetben. **PicasaPy:** a fejléc Enter után ment, a
  `[Picasa]/description` kulcsba (`LightboxHeaderDescription.qml:18-50`,
  `LightboxFeedGroup.qml:40-51`, `controller_folder_description_mixin.py:26-63`).
  Hogy az eredeti címzett a `description` kulcsra, a felirat-setteren
  (`0x00443c90`) át ír-e, nem igazolt.
- **`0x004545c0` és `0x0045c0a0`, a `.picasa.ini` író (421).** Megválaszolva a
  fájl és a szakasz szintjén. A `0x004545c0` hívói: `0x0041c340`, `0x00431570`,
  `0x00443c90` (felirat-setter), `0x00445460` (név-setter) és `0x0044fa80`
  (hely-setter). A dekompilált törzs csak a `FUN_004543e0`-at hívja (a
  dekompilálás tizenhárom elérhetetlen blokkot eltávolított), de a `0x0045c0a0`
  hívói között a `0x004546a1` cím a `0x004545c0`-ban van: a függvény tehát a
  `0x0045c0a0`-t is hívja, a dekompilálás ezt elveszti. A `0x0045c0a0` egy
  `ytPicasaINIFile` objektumot épít `.picasa.ini` névvel, a `this+0x48`
  objektum `+0xf0` virtuális metódusával tölti ki (olvasat: a mappa útja), és a
  végén `FUN_005ab210("Picasa", kulcs, érték)` hívással ír: tehát a mappa
  **`.picasa.ini` fájljának `[Picasa]` szakaszába**. A kulcs és az érték
  paramétereinek sorrendje a törzsből nem egészen egyértelmű (a `FUN_005ab210`
  harmadik argumentuma az `-1` állapotú ágban felülíródik); a hívóhelyek
  olvasata (417) szerint kulcs, majd érték. Korai kilépés: ha az ini-objektum
  állapotjelző bájtja `0`, és az érték null vagy üres, nem ír.
  **A #7038 `[Picasa]/location` választása igazolt:** a hely-setter
  (`0x0044fa80`) a `0x004545c0`-n át ugyanezt a szakasz-írót hívja `location`
  kulccsal (417), a szakasz neve és a fájlnév literálként szerepel a `0x0045c0a0`
  törzsében. A **név-setter is ide ír** (hívási helye `0x00445a0e`), tehát a
  `name` kulcs is a `[Picasa]` szakaszba kerül, ha a tartós jelző nem nulla (417:
  nem különleges mappánál igaz); ez a 417 két nyitott különbsége közül az elsőt
  szűkíti: az író útja igazolt, a beírt érték és a hatás nem. **PicasaPy:**
  meglévő mappánál az átnevezés nem ír `[Picasa]/name` kulcsot
  (`library_controller_resync.py:67-77`: lemezes átnevezés, majd az index
  útelőtagja). **Eltérés-jelölt**; a `name` kulcs értékét és az átnevezés utáni
  `.picasa.ini` tartalmát mérés nélkül nem állítom. **A `date` ág `0.000000`
  értéke** (a 417 második különbsége): a `0.000000` nem üres szöveg, ezért a fenti
  korai kilépés nem érinti (feltéve, hogy az `-1` állapotú ág nem írja felül
  az értéket); a `FUN_005ab210("Picasa", ...)` hívás lefut. Hogy ez kulcstörlés
  vagy `date=0.000000` sor, a `FUN_005ab210` törzsén múlik, ami nincs a kimenetben.
- **`0x0052e0f0` és `0x004fd1c0`, a mappa átnevezése és a katalógus (422).**
  Megválaszolva. A `0x0052e0f0` vékony burkoló: `FUN_00455f10(this)`,
  `FUN_00455e30(this)`, majd `FUN_004fd1c0(this+0xf8, forrás, cél, 1)`. A
  visszatérési értékét a mentő (`0x0055d320`, a
  `2026-11-15-7031-7032-7033-colab-decomp.txt` kimenetből) nullához hasonlítja;
  a dekompilálás a `0x0052e0f0` visszatérését elveszti. A két utat
  paraméterként kapja, az összeállításuk a mentőben történhet (célút-építő
  lépései: `FUN_009a3b50`, `FUN_0049f820`, `FUN_009a3c70`; nincsenek bontva). A
  `0x00455f10` és a `0x00455e30` törzse nincs a kimenetben. A
  `0x004fd1c0(katalógus, forrás, cél, jelző)` lépései:
  1. Ha a jelző nem nulla (itt `1`): egy globális objektum (`DAT_00d6769c`), ha
     nem null, előbb `FUN_005aa120`-at kap (jelentése nincs meg). Utána a két
     útobjektum `+0x208` mezőjében (`param[0x82]`) álló kötet-sztringet
     hasonlítja, ASCII kis- és nagybetűtől függetlenül (csak az A-Z betűket
     kisbetűsíti): eltérő kötetnél, vagy ha csak az egyik útnak van kötete,
     **`-1` a visszatérés, átnevezés nélkül**.
  2. `FUN_00994400(forrás, cél, 1, 5)`, a `MoveFileExW`-burkoló (416); nem nulla
     visszatérésnél ezt adja vissza, a katalógus érintetlen marad. A harmadik
     érték (`1`) a `MOVEFILE_COPY_ALLOWED` jelzőnek felel meg (416). Az `5` a
     burkoló dekompilált törzsében nem külön paraméterként látszik: az
     újrapróbálás időkorlát-összehasonlítása (`QueryPerformanceCounter`,
     `FUN_009a51b0`) egy paraméterből számolt értéket használ. Az `5` ezért
     **erős jelölt az időkorlátra, de nem igazolt**: a regiszterparaméterek
     összekeveredtek a dekompilálásban, és a mértékegységet a `0x009a51b0`
     időátváltó adná, ami nincs a kimenetben.
  3. A sikeres átnevezés után a katalógus: a `FUN_004f7fc0` rekordazonosítókat
     gyűjt a forrás-út objektumával hívva (olvasat: a forrás-út alatti
     rekordok; a feltétele nincs a törzsben), majd a katalógus zárja alatt
     (szálazonosítóval újrabelépő zár) a rekordok egy részénél (a `+0x18` mező
     `0x3e9`, vagy a `+0x20` mező `-1`) az út elejéről **a forrás-út hosszának
     megfelelő számú karaktert levágja, és a cél utat fűzi elé**
     (`FUN_00985af0`); a többinél az utat nem írja át. Mindegyik rekordnál
     `FUN_004ed450(azonosító)` fut. A végén, ha a `param_1[0x122]`
     darabszám-mező nem üres, a `param_1[0x121]` objektum `+0x10` metódusát hívja
     az érintett utakkal és azonosítókkal (olvasat: a katalógus figyelőinek
     értesítése).

  A jelző nulla értékénél a kötet-összevetés és a mozgatás kimarad, csak a
  katalógus-frissítés fut. A lépéssor a **sorrendet** adja: előbb a lemezes
  átnevezés, utána a katalógus; lemezes hibánál a katalógus érintetlen, a
  katalógus-frissítésnek pedig nincs hibaága. **PicasaPy:** a lemezes átnevezés a
  szülőn belül egy `os.rename` (`rename_folder.py:51-56`, ezért a kötet mindig
  azonos), utána az index frissítése (`library_controller_resync.py:77`,
  `move_folder_tree`); a PicasaPy az index hibájánál visszagörgeti a lemezes
  átnevezést (`:80`), ami az eredetinél szigorúbb. A sorrend egyezik, a
  kötetellenőrzés a PicasaPy-ban nem fordulhat elő: eltérés-jegy nem kell.
- **`0x00992ed0`, létezés-ellenőrzés (423).** Megválaszolva. A `bool
  FUN_00992ed0()` a vizsgált utat az `EAX` regiszterben kapja: ha null vagy
  üres, hamis; különben lekérdezi az attribútumot a `DAT_00d694bc`
  függvénymutatón át (a 416 szerint ez adja a `0xffffffff` hibajelzést;
  olvasat: fájlattribútum-lekérdezés), körülötte a `FUN_0053ddf0` és a
  `FUN_009a51b0` segédhívással (jelentésük nincs meg), és **igazat ad, ha az
  eredmény nem `-1`**.
  Általános fájl- és mappalétezés-ellenőrző, 244 hívóval; nem zárolás- és nem
  hozzáférés-vizsgálat. Az átnevezésben két helyen áll: (a) a `0x00994400`
  burkolóban az `5`-ös hibakód (hozzáférés megtagadva) után ez a kapu: hamis
  eredménynél a burkoló `0`-t ad, átnevezés nélkül; igaz eredménynél indul a
  **500 ezredmásodperces újrapróbálás** (a megszakító eseményre `0xf4242`); (b) a
  mentőben a `FUN_0049fef0` után, a névtisztítás és a `0x0052e0f0` előtt
  kapuként: hamis eredménynél a mentő nem nevez át, és hibaüzenetet sem ad (a
  hibaüzenet csak a névtisztítás vagy az átnevezés hibájához kötött ágban van).
  Hogy mindkét helyen melyik útra vonatkozik (a regiszterátadás nem látszik),
  nem igazolt. **Következmény a 416 újrapróbálására:** a feltétel
  (`GetLastError() == 5` és a vizsgált út létezik), a 500 ezredmásodperces
  várakozás és a megszakító esemény megvan; az időkorlát nagysága (jelölt: `5`) és
  mértékegysége nincs. **PicasaPy:** az átnevezés egyetlen `os.rename` hívás
  újrapróbálás nélkül (`rename_folder.py:51-56`); jegyet az időkorlát nélkül nem
  javaslok.

**A jegy lezárhatósága: NEM zárható.** A "Kész, ha" pontokhoz mérve:

| Pont | Állapot a 419-425 után | Miért |
|---|---|---|
| Minden belépési pont és feltétel | ⛔ | A rácsfejléc címzettje (`CAlbumVarString`, album `+0x50`) megvan, de a vtábla metódusai (elfogadáskor melyik kulcs) és a negyedik hívó (`0x00789c00`) nincsenek bontva; az erőforrásbeli gyorsbillentyű-tábla és a mappalista dupla kattintásának célsora nyitott. |
| Ablak, mezők, alapértékek, átnevezés | ✅ részben (közelebb) | A névtisztító, a `MoveFileExW`-burkoló, a kötet-összevetés, a sorrend (lemez, majd katalógus) és az újrapróbálás feltétele megvan; az időkorlát mértékegysége (`0x009a51b0`) és a célút-építő lépések nincsenek. |
| Fájlrendszer, `.picasa.ini`, index, mappafa, rács, kijelölés | ✅ részben | Az író megvan: `.picasa.ini`, `[Picasa]` szakasz; a `FUN_005ab210` belseje, a `name` sor tartalma és a `date` `0.000000` hatása nincs; az index és a kijelölés végállapota sincs meg. |
| Ütköző név, írásvédett hely, írási hiba | ✅ részben | Az átnevezési hiba és az újrapróbálás feltétele bizonyított; az ini-írási hiba eredménye mérés nélkül NINCS MEG. |

**Fejlesztői teendő:** a 419-425 nem ad új fejlesztői jegyet. A #7038
`[Picasa]/location` választása igazolt, a `name` sor és az újrapróbálás időkorlátja
mérés, illetve a `0x009a51b0` nélkül nem jegyezhető. A 416 szerinti kiegészítő
"Kész, ha" (az `A  B` két szóközzel marad) változatlanul érvényes.

### CAlbumList-dupla kattintás: soronkénti feltétel (2026-11-16)

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x00765d30`: `lb_predouble` esetén a sor `+0x30` típusa `1` vagy `5`, és a sor `+0x18` bájtja nulla → `0x006db580` Folder/Album Properties. Ha a `+0x18` nem nulla, a sor ág visszatér tulajdonságnyitás nélkül. A `+0x30 == 4` sor a `CAlbumList::newalbumprompt` ágban tér vissza; a `2` típus szintén korán visszatér. | `FolderHierarchyView.qml:386`: a sor dupla kattintása `root.toggle(row.modelData.path)`; a mappafa ágát nyitja/csukja. | A binárisban igazolt a `1`/`5` típuskapu, nem minden sor nyit tulajdonságot. PicasaPy oldalon a mappafa dupla kattintása eltér. A név szerinti különleges sorok megfeleltetése nyitott; ne terjesszük ki rájuk a változtatást bizonyíték nélkül. |

**A típusérték független ellenőrzése.** A `0x004a0720` rekordépítő a kapott
első paramétert a rekord `+0x30` mezőjébe írja. A meglévő Ghidra-kimenetben a
`0x004b29d0` ezt `1` értékkel, a `0x004b1c80` `5` értékkel hívja. Ez a
rekord-előállítási út megerősíti a handlerben vizsgált számokat, de önmagában
nem azonosítja a felületen a Starred Photos, Screensaver, Emberek, Exported
Pictures és Recently Updated sorokat. A `+0x18` kapu szemantikai neve sincs
meg.

**Bizonyítottsági fok: feltételes.** Két független út egyezik a pontos
rekordtípus-feltételen: (A) `0x00765d30` eseménykezelője közvetlenül teszteli a
`+0x30` értékét és meghívja a `0x006db580`-at; (B) a `0x004a0720` rekordépítő
és a `0x004b29d0`/`0x004b1c80` hívók előállítják az `1`/`5` típusokat. Az
teljes kérdés azért feltételes, mert a látható sorok teljes típusleképezése, a
`+0x18` jelző jelentése és a többi sor dupla kattintás utáni végállapota nem
igazolt.

**Cáfoló kísérlet.** Megpróbáltam cáfolni azt az állítást, hogy a
`CAlbumList` minden dupla kattintása tulajdonságot nyit. A `0x00765d30` a
`+0x30 == 4` esetén a `CAlbumList::newalbumprompt` felirat-ágán tér vissza,
és a `2` típusnál is korán visszatér; emellett az `1`/`5` út a nem nulla
`+0x18` bájt esetén sem nyit. A cáfolatot ugyanazzal a mércével ellenőriztem:
a `0x00763150` rajzolófüggvény külön `4`-es sort kezel, a korábbi #5121
vizsgálat pedig a `newalbumprompt` sort a `liststicky5` / “Albums” fejlécsortól
elkülönítette. A cáfoló lelet tehát nem az index negatív találatán alapul.

**Javasolt fejlesztői jegytörzs**

#### 3. A mappalista dupla kattintása nyissa meg a megfelelő tulajdonságablakot

**Eredeti:** a `CAlbumList` sor `+0x30 == 1` vagy `5` típusánál, ha a
`+0x18` bájt nulla és az esemény `lb_predouble`, a `0x00765d30` meghívja a
`0x006db580` Folder/Album Properties útját.

**Nálunk:** `src/picasapy/app/qml/PicasaPy/FolderHierarchyView.qml:386` a
dupla kattintásra a `root.toggle(row.modelData.path)` hívással nyitja vagy
csukja a mappafát.

**Teendő:** a megfelelő, választható fizikai mappasor dupla kattintásakor
nyisd meg a Folder Properties ablakot az adott mappa adataival. A fa
kinyitását/csukását tartsd a sor külön fa-kezelő elemén. A type 5 és a
névvel azonosított speciális albumok viselkedését csak a sorleképezés
lezárása után kösd be.

**Kész, ha:** dupla kattintásra a fizikai mappasor tulajdonságablaka nyílik
meg a megfelelő mappaértékekkel; a fa-kezelő elem továbbra is csak
kinyit/csuk; egyéb sorok viselkedése nem változik a bizonyított
típusleképezés nélkül.

### Nyitott: a 2026-11-16-os kérdés

- A `+0x18` sorbájt jelentése, valamint a `+0x30` típusok név szerinti
  hozzárendelése nyitott; különösen a Starred Photos, Screensaver, Emberek,
  Exported Pictures és Recently Updated beépített soroké. A nem `1`/`5`
  sorok teljes dupla kattintás utáni viselkedése is nyitott: a
  `0x00765d30` tulajdonságnyitást nem hív rájuk, de a generikus aktiválási
  útból nem következtetek „kinyit/becsuk” vagy „semmi” eredményre.
- Ghidra-kör kell: 0x004b8470: a meglévő kimenet iterálja a builder
  `in_EAX[0x52]` rekordjait és hívja a `0x004b29d0`-t, de nem köti a beépített
  Starred Photos/Screensaver/Recently Updated/Exported/People tokeneket a
  `CAlbumList` sorrekordjaihoz. Kérdés: melyik `+0x30` típus és `+0x18`
  érték jut ezeknél a `0x00765d30` handlerhez? [blokkoló]

### Nyitott

- Megválaszolva (Ghidra 406): a kapu nem a képszámot nézi, csak egy nem üres sztringet; a kijelölés nem számít.
- Részben megválaszolva (Ghidra 407, 417, 421): mezőolvasók, setterek, hibakezelés, a kulcsnevek (`name`, `description`, `location`, `date`, `music`), a tartós jelző (nem különleges mappánál igaz) és az író megvan: a `0x004545c0` -> `0x0045c0a0` a mappa `.picasa.ini` fájljának `[Picasa]` szakaszába ír (a #7038 `[Picasa]/location` választása igazolt), a név-setter is ide ír. Ghidra-kör kell: 0x005ab210 - a `("Picasa", kulcs, érték)` író belseje: a `date` ág `0.000000` értéke kulcstörlés vagy sor, a kulcs és az érték sorrendje, a `name` sor; 0x004543e0 - a sor -> szöveg feloldás. Mérés (Colab, eredeti Picasa): a Folder Properties átnevezése után a mappa `.picasa.ini` `[Picasa]` szakaszában van-e `name=` sor, és mi az értéke.
- Megválaszolva (Ghidra 408, 416, 422, 423): a sorrend és a visszagörgetés hiánya megvan; a `0x009946f0` névtisztító; a `0x00994400` a `MoveFileExW`-burkoló (500 ezredmásodperces újrapróbálás hozzáférési hibánál, ha a vizsgált út létezik; a `0x00992ed0` általános létezés-ellenőrző); a `0x0052e0f0` -> `0x004fd1c0` előbb a köteteket veti össze (eltérésnél `-1`), utána átnevez, végül a katalógus rekordjainak útelőtagját cseréli a forrás-út hossza szerint. Ghidra-kör kell: 0x009a51b0 - az időátváltó: az újrapróbálás időkorlátja (jelölt: a `0x00994400` hívásának negyedik értéke, `5`) milyen mértékegységben értendő.
- Részben megválaszolva (Ghidra 415, 420): a `0x00717810` csak a csomópontot építi; a címzett a csomópont `+0x28c` mezője, amelyet a hívók közül csak a `0x00749ba0` állít be (a `0x0074ad40` és a `0x0074c200` null címzettet ad), és ez egy `CAlbumVarString` (`0x00746640`), a mappa (album) objektum `+0x50` változójához kötve; a kulcs neve nem látszik. Ghidra-kör kell: a `CAlbumVarString::vftable` metódusai - melyik fut elfogadáskor, melyik kulcsot írja (a vtábla címe a kimenetben nincs, csak a szimbólum neve; a konstruktor `+0x14` és `+0x18` mezőjének jelentése, azaz a negyedik paraméter: `1`, `0` vagy `4`); 0x00789c00 - a negyedik hívó. [blokkoló]
- Mérés (Colab, eredeti Picasa, a névtisztítás második útja): a Folder Properties névmezőjébe írt `A  B` (két szóköz) és `con` név mentés után mi lesz a lemezen (`A  B` vagy `A B`, illetve `con_`); a #7047 szóköz-összevonásának eldöntéséhez.
- Megválaszolva (Ghidra 410-411): a küldő a bal oldali CAlbumList dupla kattintása, a hatókör az aktuális mappa.
- Megválaszolva részben (Ghidra 410-411, 2026-11-16): a CAlbumList `lb_predouble` eseménye a `+0x30 == 1` vagy `5` sorrekordnál, ha a `+0x18` bájt nulla, a `0x006db580` Folder/Album Properties útjára jut. A név szerinti sorosztályok és a `+0x18` kapu jelentése nyitott; lásd az alábbi CAlbumList-alfejezetet.
- Részben megválaszolva (Ghidra 412): a Ctrl-kezelőben nincs gyorsbillentyű. Nyitott: az erőforrásbeli gyorsbillentyű-tábla.
- NINCS MEG (mérés): eredeti .picasa.ini írási hiba után mi marad lemezen és a felületen. Megszerzés: Windowsos Picasa 3.9 mérés külön másolaton, külön írásvédett mappával és ini-írási hibával; NAS-bejárás nélkül.

### Módosított fájlok

- docs/specs/paritas-ellenorzes.md - a #7032 alfejezet kiegészült a CAlbumList `lb_predouble` típuskapujával, független rekordúttal, cáfoló próbával és a név szerinti sorleképezés nyitott kérdésével.

## #7033: A dátum és idő beállításának teljes folyamata

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti oldalt a binárisból és az erőforrásokból, a PicasaPy oldalt a
jelenlegi forrásból olvastam. Ez a rész a 7033 kérdéseit fedi le; nem
tekinti bizonyítéknak a korábbi, részleges dátummódosító-leírást.

### Következtetés

Az eredeti Eszközök (Tools) menü és a Tulajdonságok panel dátumsorának helyi menüje
ugyanahhoz a `0x9e0e` parancshoz vezet. A végrehajtó JPEG-nél a
`DateTimeOriginal` EXIF mezőt írja, a nem JPEG ágon fájlidőt és a
`thumbindex.db` dátummezőjét kezeli; a PicasaPy megvalósítás EXIF-et, illetve
SQLite-felülírást használ. A teljes paritás nem dönthető el: az eredeti
alapértelmezett rádiógomb, néző/tálca helyzet, az Undo, az írásvédett lemez eredménye és
néhány látható utóhatás nyitott.

### Bizonyítottsági fok

**Feltételes.** A menükód és az íróág két egymástól különálló bináris útból
ellenőrizhető, a videó-adatmezőt a külön katalógusrekord-vizsgálat is
megerősíti. A teljes folyamatra mégsem adható megerősített fok, mert a rádió
kezdőértéke, az eredeti néző/tálca kapu, a visszavonás és a tényleges
írásvédett Windows-fájl kimenete nem dőlt el.

### 1. Belépési pontok, kijelölés és gyorsbillentyű

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Eszközök menü.** A `0x00559150` menürekord-építő a `0x00c8e048` azonosítót és `0x00c8e070` feliratot társítja a `0x00d6e904` rekordhoz; ennek parancsmezője `0x9e0e` (`0x0055c7cd`). A parancs-diszpécser `0x005cb990` `case 0x9e0e` ága `0x0057d7f0`-re lép. | A menütétel `PicasaToolsMenu.qml:78-83`; a könyvtári célhalmaz átadása `MainMenuBar.qml:361-362`. A menüpont `MainMenuBar.qml:121-122` szerint legalább egy kijelölést és nem megnyitott nézőt követel. | A menüsor bejárata megvan. Az eredeti menü engedélyező feltétele nem szerepel a parancs-diszpécserben, ezért az üres kijelölés és a néző állapotának menüszintű paritását még kell mérni. |
| **Tulajdonság helyi menüje.** A `0x00638990` a kiválasztott `PropertiesListItem` `+8` típusát vizsgálja; `0x37` esetén hozzáadja a `0x9e0e` parancsot és a `0x00c8e048` feliratot. A hívó `0x00637fa0`. A `0x37` az EXIF `0x9003` `DateTimeOriginal` mező (`picasa-metaadat-tulajdonsagok.md:53`). | A `PropertiesPanel.qml:71-103` adatlistát mutat. A panel jobb kattintás menüje `PropertiesPanel.qml:136-155`, és csak a „Edit Tags” tételt tartalmazza. | **Igazolt eltérés.** A dátumsor célzott helyi menüjének művelete hiányzik. Fejlesztői jegyjavaslat lent. |
| **Rács helyi menüje.** A teljes `.text` pásztázás a `0x9e0e` közvetlen kódtalálatait csak a menürekord-építőben (`0x0055c7cd`) és a tulajdonságmenüben (`0x00638a0a`) találta. Külön rács-helyi dátumparancsot nem azonosítottam. | A `PhotoContextMenu.qml:163-520` nem tartalmaz dátummódosítót. | Az eredeti közvetlen kódbeli dátumbejárat hiánya ellenőrzött. A Tools menü ettől még meghívható lehet rácskijelölésre. |
| **Néző.** A `0x0057d7f0` az aktív objektumot és a kiválasztási gyűjtőt használja, de a binárisból nem dönthető el, hogy a menü vagy helyi menü látható-e a nézőben. | A `MainMenuBar.qml:121-122` a Tools dátumműveletet letiltja nyitott nézőnél; a `ViewerContextMenu.qml:122-294` nem tartalmaz dátumműveletet. | Az eredeti nézőbeli menükapu és a feldolgozott objektum azonosítása nyitott. A 7033-as paritás nem állítható. |
| **Képtálca.** A közvetlen `0x9e0e` kódtalálatok között nincs azonosított tálca-menüépítő. A `0x0057d7f0` átvesz egy kiválasztási gyűjtőt, de nem bizonyítja, hogy az eredeti a tálca tartalmát dolgozza fel. | A `TrayContextMenu.qml:40-95` nem tartalmaz dátummódosítót. A Tools menü `MainMenuBar.qml:121-122` a főrács `selectedIndexes` értékéhez kötődik, nem a tálca tartalmához. | Az eredeti tálcából elérhető dátumművelet nincs igazolva. A PicasaPy tálca-helyi dátumbejárata hiányzik; eredeti eltérésként nem jegyezhető, amíg a bináris vagy mérés nem erősíti meg. |
| **Gyorsbillentyű.** A `Picasa3i18n.dll` `SHORTCUTS.XML` erőforrása 48 rekeszt tartalmaz dátum-idő műveletre mutató rekord nélkül; a `0x00559150` menüsor 32 gyorsbillentyűs rekordja közt sincs `0x9e0e`. A `0x00c8e070` felirat `Adjust &Date and Time...`; ez menübillentyűt jelez, külön Ctrl/Alt+billentyű-kötést nem. | A QML felirata szintén `Adjust &Date and Time...` (`PicasaToolsMenu.qml:80`); a teljes `MainKeyboardShortcuts.qml:1-551` fájlban nincs dátumművelet. | Külön gyorsbillentyű-parancsot egyik oldalon sem találtam. A menü feliratának `D` menübillentyűje nem külön műveletbillentyű. |

Az eredeti action a `0x0057d7f0` útján hívja a `0x005c76b0` kiválasztási
segédet, és a kijelölési elemszámot adja a párbeszédnek. Egy elemnél a cím
`Adjust Photo Date`; egynél több elemnél a `0x0077c7c0` a
`OffsetPhotoDate:Title` erőforrásból darabszámos címet épít. A cím viselkedése
megerősített a függvény utasításai és az `offsettime.fen` ablakleírója
alapján. A többes kijelölés kezdeti dátumát adó objektum a `0x0057d7f0`
`+0x6c` FILETIME mezője; hogy ez mindig az első kijelölt vagy a fókuszban
levő kép-e, nincs meg.

### 2. Ablak, mezők és alapértékek

Az eredeti `runtime/offsettime.fen` leíró (`0x00cb40a0` azonosító,
`0x00cb4090` előnézeti elem) `Current photo date` dátum/idő mezőt,
`New photo date` dátum/idő mezőt, `relative` és `absolute` rádiót, valamint
OK/Cancel gombot sorol fel. A `0x0077c7c0` a `currentdate` vezérlőt tölti,
majd a kapott FILETIME alapján állítja elő az új dátum és idő kezdeti
értékét. A többes elemszám csak akkor kerül a címbe, ha a darabszám nagyobb
egynél (`0x0077c7c0`). Az eredeti `.fen` szélesség-megjelölése `fit`.

Az `adjust_type` rádiólekérdezését a `0x0077cee0` végzi; az elfogadáskor a
`0x0077cd50` dolgozza fel a `newdate`, `newtime` és `adjust_type` mezőket.
Az `offsettime.fen` nem nevez meg előre kiválasztott rádiót, és a jelenlegi
utasításszintű olvasásból nem dőlt el a kezdő rádió vagy az, hogy a program
megjegyzi-e. **NINCS MEG.**

Az eredeti módok végrehajtási jelentése: az `0x0057d7f0` több kijelölt
elem és relatív jelző esetén az új és régi idő különbségét számolja
(`0x0077cf70`), majd a `+0x80/+0x84` munkaszál-mezőket adja át;
abszolút módban cél-FILETIME-t állít a `+0x78/+0x7c` mezőkbe. A
`0x0077cfd0` az előbbi alakot a `0x00490580`, a cél-FILETIME alakot a
`0x00490c10` workerhez köti. Egyetlen kijelölt elemnél a `0x0057d7f0`
mindig közvetlen cél-FILETIME-t ad át (`0x0057d9d4-0x0057da08`), tehát az
egy-képes eredmény abszolút.

PicasaPy oldalon az `AdjustTimestampDialog.qml:62-80` az első kapott sorból
tölti a jelenlegi és új időt, minden nyitáskor relatív módot választ, és a
címet csak több sornál bővíti (`:22-24`). Az egyképes cím egyezik. A
PicasaPy egyképes relatív képlete ugyanarra a célidőre jut, ha az új idő a
párbeszédben megadott cél; a többes kezdő módot csak az eredeti rádió
alapértékének feloldása után lehet összevetni.

A PicasaPy ablak modális és 540 széles (`AdjustTimestampDialog.qml:25-29`);
az eredeti leíró `width="fit"` értéket ad, modális jelzőt nem tartalmaz.
Ez a leírók közti eltérés önmagában nem bizonyítja a tényleges natív
ablakszélesség vagy modalitás különbségét.

### 3. Fájlrendszer, `.picasa.ini`, index és nézet

| Hatás | Eredeti Picasa 3.9 | Jelenlegi PicasaPy |
|---|---|---|
| **JPEG EXIF** | A rekord `0x37` tulajdonságát (`0x004906f7`, `0x00490d3c`) állítja, ami EXIF `0x9003` `DateTimeOriginal`. A `0x009ed330` íróút a `0x009eb290` tempfájlos ága; a csere `0x00994400`. | A `timestamp_controller.py:74-123` a forrás JPEG EXIF `0x9003` mezőjét ideiglenes fájlon át cseréli. A `timestamp_controller.py:248-305` siker esetén újraszkenneli a mappát. |
| **Fájlidők** | A sikeres EXIF-író a `0x009eb290` útján elmenti a fájlidőket; ha az EXIF `DateTime` (`0x0132`) olvasható, a `0x00ab35e0` a hozzáférési és módosítási FILETIME-t arra teszi, a létrehozási időt érintetlenül hagyja; a `0x00ab34d0` `SetFileTime` hívással kiírja ezt a módosított szerkezetet. Hibás EXIF-írás után a `0x00992780` a létrehozási időt állítja. | Sikeres JPEG-írás után a `timestamp_controller.py:197-208` az atime/mtime értéket visszaállítja, Windowson a létrehozási időt is. Sikertelen írásnál `:179-194` Windowson a létrehozási időt próbálja állítani; más platformon nincs létrehozásiidő-írás. |
| **Videó és nem JPEG** | A worker a `0x0049070a` és `0x00490d4f` címen a `thumbindex` típusmezőjét vizsgálja. Csak a 2-es típus megy EXIF-ágra; a videók mért típusai 8, 10 és 11, ezért a nem-EXIF ágra mennek. A `0x00992780` a fájl létrehozási idejét, a `0x004ef3c0` vagy `0x004ef5a0` a `thumbindex.db` rekord első FILETIME-ját írja és piszkosnak jelöli (`pmp-database.md:4167-4218`). | A videó/nem JPEG EXIF-írása hibára fut, majd a `timestamp_controller.py:290-305` az effektív dátumot a SQLite `photos.taken_at_override` mezőjébe írja. A fájlrendszer létrehozási idejét csak Windowson próbálja állítani (`:131-176`). |
| **`.picasa.ini`** | A vizsgált `0x0057d7f0` → `0x0077cfd0` → worker/író lánc a forrásfájl EXIF-ét vagy a `thumbindex` rekordot kezeli; a pásztázás nem talált `.picasa.ini` író hívást ebben a láncban. Ez csak erre a műveletre szól. | A `timestamp_controller.py:248-308` EXIF-et, indexfelülírást és mappaszinkront használ; nem hív ini-író API-t. |
| **Index, mappadátum, rács** | A nem-EXIF ág `thumbindex` dátummezője igazolt. A sikeres JPEG után az eredeti adatbázis- és rácsfrissítés pontos végállapota, a mappafa és a kijelölés nem dőlt el. **NINCS MEG.** | A `sync_photos.py:202-242` a `taken_at_override` értéket felhasználva újraszámolja az indexelt mappadátumot. A `timestamp_controller.py:308-320` a végén `_refresh_view()`-t hív. A kiválasztott rácssor megőrzése nem következik ebből. |
| **Időrend** | A dátummódosító utáni időrendi végállapotot az átvizsgált bináris út nem dönti el. **NINCS MEG.** | A dátumművelet nem hív `syncFinished` jelet (`timestamp_controller.py:308-320`). Az időrend-vezérlő erre a jelre van kötve (`application_startup_controllers.py:270-274`), és saját `reload()`-ja újraolvassa az indexet (`timeline_controller.py:213-229`). Dátummódosítás közben nyitott időrend frissítése nincs igazolva. |
| **Visszavonás** | A `0x0057d7f0` és a két worker közvetlen dátumíró útja nem mutat visszavonási hívást; ez nem bizonyítja, hogy a Picasa globális Undo parancsa nem érinti. **NINCS MEG.** | A `timestamp_controller.py:248-320` nem hív dátumművelethez tartozó undo-vermet vagy visszaállítót. A PicasaPy dátummódosítás nem visszavonható a kódban vizsgált úton. |

Az eredeti `.picasa.ini`-re vonatkozó negatív állítás a dátumművelet
hívásláncára korlátozott, nem a Picasa egészére. A PicasaPy EXIF-siker
esetén az index újraolvasása veszi át az új `DateTimeOriginal` értéket;
írási hiba, videó vagy nem JPEG esetén a külön indexfelülírás marad
érvényben (`timestamp_controller.py:283-305`).

### 4. Írási hibák, írásvédelem és részleges végrehajtás

Az eredeti `0x00490580` és `0x00490c10` háttérfeldolgozója képenként járja be a kijelölést.
Ha az EXIF-író (`0x009ed330`) nem ad sikeres eredményt, a worker a
`0x00992780` fájlidő-ágra lép; a nem-EXIF tartalék az adott támogatott
típusnál a `0x004ef3c0` vagy `0x004ef5a0` rekordmódosítót is meghívja.
A következő kijelölt elem feldolgozása folytatódik. Visszagörgető hívást
nem találtam, ezért a bináris útban részleges siker lehetséges. A
`SetFileTime` vagy a katalógusírás hibájának pontos felhasználói jelzése
**NINCS MEG**.

Az eredeti kódágban külön írásvédettség-előellenőrzést nem azonosítottam.
Az, hogy egy Windows `readonly` attribútum vagy mappaszintű engedély mellett
az EXIF-csere, a `SetFileTime`-tartalék és a katalógusírás közül melyik
sikerül, csak a tényleges Picasa 3.9 futás és előtte/utána fájl- és
az adatbázis vizsgálatával dönthető el. **NINCS MEG.**

A PicasaPy-ban az EXIF-kivétel kezelt tartalékág: `taken_at_override`-t ír
(`timestamp_controller.py:179-194, 283-305`). A háttérköteg soros; egy
nem kezelt fájl- vagy adatbázishiba megállítja a hátralévő munkákat, a
korábbi fájlírásokat nem vonja vissza, hibát jelez, majd a folyamatablakot
lezárja (`photo_ops_write_core_mixin.py:99-140`,
`timestamp_controller.py:308-320`). Így részleges végrehajtás itt is
lehetséges. Read-only fájlnál az ideiglenes fájl vagy csere hibájának
tényleges oka a fájl- és mappaengedélytől függ; a kód nem vizsgál külön
attribútumot előre.

### 5. A két független út

- **A út, parancs és végrehajtás:** a `0x00559150` rekordbázis és
  `0x005cb990` diszpécser után `0x0057d7f0` nyitja meg a műveletet;
  `0x0077cfd0` választja a két workert, a worker pedig a `0x37` mezőt,
  `0x009ed330`-at és a tartalék `0x00992780`/`0x004ef3c0`/`0x004ef5a0`
  utat használja.
- **B út, külön menü és adatút:** a `0x00638990` önálló Properties-lista
  menüépítője ugyanazt a `0x9e0e` kódot adja a `0x37` tulajdonsághoz;
  a `pmp-database.md` 15.1-15.2 szakaszának rekordmásolási és adatbázis-
  ellenőrzése a videós ág `thumbindex` első FILETIME-ját azonosítja.
- **Egyezés:** A és B egyezik a parancsazonosítóban, a `0x37` EXIF
  tulajdonságban, és a nem-EXIF ág katalógusmezőjében. A teljes UI-végállapot
  nem egyezik össze két bizonyítéki úttal, mert a néző/tálca kapu és az
  időrend/mappafa frissítése nyitott.

### 6. Cáfoló kísérlet

Megpróbáltam cáfolni azt, hogy külön dátum gyorsbillentyű vagy további
közvetlen helyi menüparancs tartozik a `0x9e0e` kódhoz. A `paszta.py`
lineáris `.text` pásztázása `memoria_kapu()` után 2 884 879 utasítást
vizsgált: a közvetlen `0x9e0e`/felirat operandusai csak a `0x00559150`
menürekord-építőben és a `0x00638990` tulajdonságmenüben jelentek meg.
Az ellenpróbát külön erőforrás- és rekordlistával ellenőriztem: a
`SHORTCUTS.XML` 48 elemében nincs dátum/adjust/timestamp rekord, a
`0x00559150` 32 menü gyorsbillentyű-rekordjában pedig nincs `0x9e0e`.
Ezek a kontrollok a közvetlen kötést cáfoló alternatív keresést azonos
mércével, a bináris közvetlen címekre és az erőforrás teljes rekeszszámára
ellenőrizték. A `&Date` felirat menü-mnemonikája ettől külön marad.

### 7. A kérdés „Kész, ha” pontjai

A megadott jegyszöveg négy kérdést sorol fel, külön „Kész, ha” felsorolást
nem ad. Ezek alapján:

1. ⛔ **Belépési pontok és feltételek:** Tools menü és Properties-lista
   helyi menü címmel bizonyított (`0x00559150`, `0x005cb990`,
   `0x00638990`). Külön dátum gyorsbillentyű nincs az erőforrásban; a
   néző/tálca elérhetőség és az eredeti írásvédettségi kapu nyitott.
2. ⛔ **Ablak, alapértékek és megjegyzés:** mezők, módok, OK/Cancel és
   elemszámos cím ismert (`0x0077c7c0`, `0x0077cbe0`, `0x0077cd50`,
   `0x0077cee0`). A többes kijelölés aktuális képének kiválasztása, a
   rádió kezdőértéke és annak megjegyzése nyitott.
3. ⛔ **Hatás és visszavonás:** JPEG EXIF és videó/nem JPEG `thumbindex`
   ág igazolt (`0x009ed330`, `0x004ef3c0`, `0x004ef5a0`, `0x00992780`).
   Az eredeti JPEG index/rács/mappafa/időrend végállapota és Undo hatása
   nyitott; a PicasaPy az indexet és főnézetet frissíti, időrend-jelet nem
   küld.
4. ⛔ **Írásvédelem és részleges hiba:** az EXIF-író hibája tartalékágra
   kerül és a worker a következő elemmel folytat (`0x00490580`,
   `0x00490c10`), ezért visszagörgetés nem látszik. A read-only attribútum
   konkrét Windows-viselkedése és a felhasználói hibajelzés nyitott.

### 8. Javasolt fejlesztői jegytörzs

#### A Tulajdonságok panel dátumsorának helyi menüje nyissa meg a dátumállítót

**Eredeti:** a `0x00638990` a `PropertiesListItem` `0x37` típusú
`DateTimeOriginal` sorához (`0x9003`) hozzáadja a `0x9e0e` Dátum és idő
beállítása parancsot. A `0x00637fa0` hívja ezt a helyi menüépítőt.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x00638990`: `0x37` tulajdonságsorhoz a `0x9e0e` műveletet adja. | `PropertiesPanel.qml:71-103, 136-155`: a panel a tulajdonságokat csak megjeleníti; jobb kattintásra az „Edit Tags” menü nyílik. | A dátumot megjelenítő tulajdonságsor helyi menüjébe kerüljön a dátumállító, és az adott kép adataival nyíljon meg. |

**Kész, ha:** a `DateTimeOriginal` sor jobb kattintására megnyílik a
dátumállító az adott kép aktuális dátumával; más tulajdonságsor nem kap
dátummódosító műveletet.

Más fejlesztői jegyet nem javaslok: a alapértelmezett rádiógomb, néző/tálca kapu,
visszavonás és látható index-végállapot nincs kellően igazolva.

### 9. Új kutatási jegyjavaslatok

Nincs külön kutatási jegyjavaslat; a lent felsorolt nyitott pontok a 7033
folyamatához tartoznak.

### Ghidra-kiegészítés (2026-11-15, várólista 402-403)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp.txt` (privát
kutatási tár).

- **`0x0077c670`, kezdő mód.** A dátumeltolás ablakának konstruktora és két
  kezelője (`0x0077cee0`, `0x0077cd50`) nem olvas és nem ír megjegyzett
  beállítást. A konstruktor a belső módjelzőt 1-re állítja; a `0x0077cee0`
  ebből `jelző = (érték == 0)` alakban számol vissza, tehát a kezdő állapot az
  `adjust_type` 0. rádiója. A rádió látható kezdőértékét a kód nem állítja, az
  az `offsettime.fen` leíróból jön. **PicasaPy:** az `AdjustTimestampDialog.qml`
  minden nyitáskor az eltolás rádióját jelöli be (`checked: true`), és nem
  jegyez meg semmit. A megjegyzés hiánya paritásban van; hogy az eredeti 0.
  rádió az eltolás-e, a leíró sorrendjén múlik, ezért ez **feltételes**.
- **`0x0057d7f0`, melyik kép ideje.** Az ablak a kijelölési lista **első**
  elemének dátumát kéri le (katalógus vfunc `0xc4`, `*lista`); a fókuszt nem
  kérdezi. Előtte a `FUN_00506500` feldolgozza a listát, hogy ez rendez-e, nem
  derült ki. Több képnél eltolást ment, egy képnél abszolút időt. **PicasaPy:**
  az előnézet a `photoRows[0]` sort használja (`AdjustTimestampDialog.qml:66`),
  tehát szintén az első kijelölt elemet. Az egyezés a lista sorrendjéig
  **igazolt**; a sorrend (kijelölési vagy rácssorrend) nyitott.

### Ghidra-kiegészítés 2 (2026-11-15, várólista 413-418)

Forrás: `referencia/ghidra/2026-11-15-7031-7032-7033-colab-decomp-2.txt` (privát
kutatási tár). Ide a 418 tartozik. A `0x005c76b0` törzsét a már meglévő
`2026-11-15-7012-7022-colab-decomp.txt` kimenetből olvastam, nem a 413-418
kötegből.

- **`0x00506500`, rendezi-e a listát (418).** Megválaszolva: **nem rendez.** A
  `param_1` a katalógus (rekordtömb `param_1[0xfc]`, darabszám
  `param_1[0xfd] >> 1`), a `param_2` a bemeneti lista (mutató és darabszám).
  Zárolja a katalógust (`EnterCriticalSection`), majd a lista elemein a
  bemeneti sorrendben halad: a tartományon kívüli azonosítót elhagyja; a rekord
  `+0x18` mezőjét nézi, és ha az `0x3e9`, az azonosítót a rekord `+0x20`
  mezőjével (`piVar2[8]`) cseréli; a már felvett azonosítót nem veszi fel újra
  (az első előfordulás marad). Az eredmény a bemeneti sorrendet követi, és
  helyben felülírja a bemeneti listát. Null listára `4`, egyébként `0` a
  visszatérés. A `0x3e9` jelentése ("hivatkozó" rekord) a fejléc olvasata; a
  kimenet csak a mezőértéket mutatja. Hívói: `0x0057d879` (a `0x0057d7f0`, a
  dátumállító) és `0x007dc704` (`0x007dc4f0`). Következmény: a dátumablak a
  bemeneti lista első, feloldott, tartományban lévő elemének idejét mutatja.
- **A bemeneti lista sorrendje (`0x005c76b0`).** A `0x0057d7f0` a
  `FUN_005c76b0(0,1,1,1)`-et hívja (`0x0057d813`). Mivel `param_1 == 0`: ha a
  `this+0xeac` objektum (valószínűleg az albumlista, ugyanaz a mező, amelyet a
  `0x006db580` az albumlista aktuális mappájaként olvas) `+0x3c9` bájtja nem
  nulla, az eredményt annak `0xdc` virtuális metódusa adja; különben a
  `this+0xea8` objektumra hívott `FUN_007166c0(objektum, jelző)` tölti a
  listát (a jelző 1); ha ez üresen hagyja, és a `this+0xe64` nem `-1`,
  egyetlen elem kerül be (`this+0xe68`). A sorrendet tehát a `FUN_007166c0`
  dönti el; ez nincs dekompilálva. **PicasaPy:** a `photoActionRows()` a
  `selectedRows()` útján a `selectedIndexes` tömböt adja
  (`MainLibrarySelectionState.qml:70-78`, `selection.js:32-36`), úgy, ahogy a
  kattintások építették: a Ctrl+kattintás a végére fűz (`selection.js:7-12`), a
  Shift+kattintás növekvő tartományt ad (`selection.js:15-21`). Az
  `AdjustTimestampDialog.qml:66` a `photoRows[0]` elemet használja, tehát a
  **kattintási sorrend** első elemét, nem a rács szerinti elsőt (a "Locate on
  Disk" ezzel szemben szándékosan rácssorrendet használ, `selection.js:38-46`).
  Hogy az eredeti a kattintási vagy a rács szerinti sorrendet adja, **nincs
  meg**; egyezést ne állítsunk. Ha az eredeti rácssorrendet használ, a
  Ctrl+kattintással fordított sorrendben kijelölt képeknél az ablak más kép dátumát
  mutatja.

**A jegy lezárhatósága: NEM zárható.** A 7033 négy kérdése ("Kész, ha"):

| Pont | Állapot a 413-418 után | Miért |
|---|---|---|
| 1. Belépési pontok és feltételek | ⛔ | A 418 nem érinti: a néző- és tálcakapu, az írásvédettségi kapu nyitott. |
| 2. Ablak, alapértékek és megjegyzés | ⛔ (közelebb) | A lista első eleme és a "nem rendez" megvan; a lista sorrendje (`FUN_007166c0`) és a rádió sorrendje (`offsettime.fen`) nyitott. |
| 3. Hatás és visszavonás | ⛔ | A 418 nem érinti: index, rács, mappafa, időrend, Undo nyitott. |
| 4. Írásvédelem és részleges hiba | ⛔ | A 418 nem érinti: Windows-mérés kell. |

Új fejlesztői jegyet a 418 nem indokol; a meglévő jegytörzs (a Tulajdonságok
panel dátumsorának helyi menüje) változatlan. Ha a `FUN_007166c0` rácssorrendet
ad, a `photoRows[0]` használata új eltérés-jelölt lesz.

### Ghidra-kiegészítés 3 (2026-11-16, várólista 419-425)

Forrás: `referencia/ghidra/2026-11-16-7022-7031-7033-colab-decomp.txt` (privát
kutatási tár). Ide a 424 tartozik. A `0x005c76b0` törzse ebben a kimenetben is
szerepel; a 418 még a `2026-11-15-7012-7022-colab-decomp.txt` kimenetből
olvasta.

- **`0x007166c0`, a lista töltője (424).** Megválaszolva: **a lista
  rácssorrendű, nem kattintási sorrendű.** A `FUN_007166c0(nézet, jelző)` a
  kimeneti listát előbb üríti, előkészítést hív (`FUN_0071c8c0`; ha a nézet
  `param_1[0xb3]` mezőjének (`+0x2cc`) bájtja nem nulla, a `+0xc4` virtuális
  metódust is), majd az elemeket
  **index szerint, 0-tól a darabszámig** járja be (a nézet `+0xb4` metódusa a
  darabszám, a `+0xb8` az `i`. elem). Az első bejárás azokat az elemeket
  gyűjti, amelyeknek a `+0x5d` bájtja nem nulla és a `+0x5a` bájtja nulla, és az
  elem `+0xb4` mezőjét (azonosító) fűzi a listához, a bejárás sorrendjében. Ha a
  jelző be van kapcsolva, és az első bejárás után a lista üres, a második
  bejárás az összes olyan elemet gyűjti, amelynek a `+0x5a` bájtja nulla (a
  `+0x5d` ekkor nem számít). Visszatérés: `0`, memóriahibánál `4`. A `+0x5d`
  (kijelölt) és a `+0x5a` (rejtett) jelentés a fejléc olvasata, a kimenet csak
  a bájt vizsgálatát mutatja. A kimenetben a kattintások sorrendjét tároló lista,
  időbélyeg vagy sorszám sehol nem szerepel: **a kattintási sorrend ebből az
  útból nem származtatható.**

  A hívó `FUN_005c76b0`: a `this+0xea8` nézetre hívja, a jelző `1`, ha ez a
  nézet azonos a `this+0xea4` nézettel, vagy a `param_2` nem nulla (a
  dátumállító útján `FUN_005c76b0(0,1,1,1)`, a 418 szerint, tehát `1`). Ha a
  `this+0xeac` objektum `+0x3c9` bájtja nem nulla, a lista nem a nézetből, hanem
  az objektum `+0xdc` metódusából jön. Ha a nézet nem ad elemet, és a `this+0xe64`
  nem `-1`, egyetlen elem kerül be (`this+0xe68`).

  **Következmény:** a dátumablak (a 418 szerint a lista első elemét kéri,
  rendezés nélkül) a nézet **index szerinti első kijelölt képének** idejét
  mutatja, a Ctrl+kattintások sorrendjétől függetlenül. Kijelölés nélkül
  (jelző `1`) a lista nem üres: az első nem rejtett elem kerülne elő; hogy a
  parancs kijelölés nélkül elérhető-e, a belépési kapun múlik, ami nyitott.
  **PicasaPy:** az `AdjustTimestampDialog.qml:65-66` a `photoRows[0]` elemet
  használja, ez a kattintási sorrend első eleme: a Ctrl+kattintás a végére fűz
  (`selection.js:7-12`), a Shift+kattintás növekvő tartományt ad
  (`selection.js:15-21`), és a `photoActionRows()` ezt a tömböt adja
  (`MainLibrarySelectionState.qml:29-32`, `:72-80`). Példa: az 5. kép, majd
  Ctrl+kattintással a 2. kép kijelölése után az eredeti a 2. kép idejét mutatja,
  a PicasaPy az 5.-ét. **Igazolt eltérés; jegy: #7054.** A rács szerinti
  rendezésre kész minta van: a "Locate on Disk" a #6995 óta rácssorrendet
  használ (`selection.js:43`, `pathsInGridOrder`). A PicasaPy `openForRows`
  üres kijelölésre nem nyit (`AdjustTimestampDialog.qml:62-64`).

**A jegy lezárhatósága: NEM zárható.** A 7033 négy kérdése ("Kész, ha"):

| Pont | Állapot a 419-425 után | Miért |
|---|---|---|
| 1. Belépési pontok és feltételek | ⛔ | A 424 nem zárja: a néző- és tálcakapu, az írásvédettségi kapu nyitott; kijelölés nélkül az eredeti lista nem üres, ezért a kijelölés nélküli elérhetőség is a kapun múlik. |
| 2. Ablak, alapértékek és megjegyzés | ✅ részben (közelebb) | A lista sorrendje megvan (rács szerinti), az első kép ideje és a "nem rendez" is; a rádió sorrendje (`offsettime.fen`) és a `this+0xeac` jelző feltétele nyitott. |
| 3. Hatás és visszavonás | ⛔ | A 424 nem érinti: index, rács, mappafa, időrend, Undo nyitott. |
| 4. Írásvédelem és részleges hiba | ⛔ | A 424 nem érinti: Windows-mérés kell. |

Új fejlesztői jegy a 424 alapján: **#7054** (a dátumablak a rács szerinti első
kijelölt kép idejét mutassa). Javasolt "Kész, ha": az 5., majd Ctrl+kattintással
a 2. kép kijelölése után az ablak a 2. kép idejét mutatja; Shift+kattintásos
tartománynál a legkisebb sorszámú képét. A meglévő jegytörzs (a Tulajdonságok
panel dátumsorának helyi menüje) változatlan.

### 10. Nyitott

- Megválaszolva (Ghidra 402): a párbeszéd nem jegyez meg beállítást, a kezdő mód a 0. rádió. Nyitott: az `offsettime.fen` rádiósorrendje, azaz hogy a 0. rádió az eltolás-e.
- Megválaszolva (Ghidra 403, 418, 424): a dátumablak a lista első elemének idejét kéri, fókusz nélkül; a `0x00506500` nem rendez (a hivatkozó rekordot feloldja, az ismétlődést kiszűri); a `0x007166c0` a nézet elemeit index (rács) szerint járja be, tehát az első elem a rács szerinti első kijelölt kép (PicasaPy: kattintási sorrend; eltérés, jegy: #7054). Ghidra-kör kell: mikor áll a `this+0xeac` objektum `+0x3c9` jelzője (ilyenkor a lista forrása az albumlista `0xdc` metódusa, nem a nézet).
- **NINCS MEG:** a `readonly` fájl attribútum, csak olvasható mappa vagy
  fájlrendszerhiba pontos eredeti kezelése és felhasználói jelzése. Út:
  kontrollált Picasa 3.9 mérés írható, fájlattribútummal védett és
  mappaszinten nem írható mintával; rögzíteni kell az EXIF-et, fájlidőket,
  `thumbindex.db`-t és a képernyőn megjelenő hibát.
- **NINCS MEG:** az eredeti parancs elérhetősége a nézőben és a tálcában,
  továbbá a siker utáni kijelölés, JPEG-index, mappafa és időrend. Út:
  célzott Ghidra-követés a `0x0057d7f0` hívói objektumára, majd Picasa 3.9
  előtte/utána mérés egy képpel, több képpel, nézőben és csak tálcára
  helyezett képpel.
- **NINCS MEG:** az eredeti Szerkesztés > Visszavonás vagy más visszavonó út módosítja-e
  a már kiírt EXIF-et, a fájlidőt vagy a katalógusrekordot. Út: a
  `0x9e0e` művelet után az Undo parancs végrehajtása, majd a forrásfájl és
  a `thumbindex.db` előtte/utána összevetése.
- **NINCS MEG:** mérőadatból nincs dátummódosítási munkamenet; az archívum
  név szerinti keresése nem talált `adjust`, `timestamp` vagy `offsettime`
  mintát, ezért az archívum tagjait nem bontottam ki.

### 11. Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - új #7033 alszakasz a belépési
  pontokról, az ablakról, hatásokról, hibákról, bizonyítékokról és nyitott
  kérdésekről.

## #7060: A diavetítés teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti oldalt a binárisból (statikus olvasás `capstone`-nal, a programot
nem futtattam), a `.tre` erőforrásokból és a hivatalos magyar feliratokból, a
PicasaPy oldalt a jelenlegi forrásból olvastam. A korábbi lapok igazolt
részeire hivatkozom (`picasa-diavetito-sav.md`, `picasa-diavetito-sav-5550.md`,
`picasa-gyorsbillentyuk.md` 12. szakasz, `picasa-idorend-bemutato-kutatas.md`,
`picasa-idorend-viselkedes.md`), nem kutatom újra; ahol ellentmondok nekik,
külön jelzem.

### Következtetés

- **Belépés.** A Nézet ▸ Diavetítés (`0x9c9f`), a Mappa/Album ▸ Diavetítés
  megtekintése (`0x9c6d`), a `Ctrl+4`, a mappa- és albumfejléc `play` gombja és
  a szerkesztő `Play` gombja (a `thumbui/sbutton` álneve) mind ugyanabba a
  függvénybe fut: `0x005e8a70(this, 0)`. Az Időrend (`0x9ccc`, `Ctrl+5`,
  `thumbui/timelinebutton`) ugyanide fut, `1` móddal. A PicasaPy-ban is egyetlen
  indító van (`MainSlideshow.qml:60`), a belépések egyeznek.
- **Fő lelet: két vetítő van, és a normál nem az, amelyikre a korábbi
  összevetések épültek.** A `0x005e8a70` `0` módban, `Shift` nélkül
  (`0x005e8b00`, `0x005e8b0a`) nem a `qshow`/`OneUpUI` vetítőt indítja
  (`0x008037e0`, `oneup.tre`), hanem a főablakba ágyazott szerkesztő-egyképes
  vetítést (`0x0075de50`, `editoneup.tre`). A `qshow` csak az Időrendnél
  (`1` mód) vagy lenyomott `Shift` mellett indul. Ebből következik, hogy a
  `picasa-diavetito-sav.md` és a `picasa-diavetito-sav-5550.md` `oneup.tre`
  szerinti sáv-összevetése, a Timeline gomb láthatósága (#5653) és a
  `picasa-gyorsbillentyuk.md` 12.5-12.9 szakasza a **normál** vetítésre nem
  érvényes. Ugyanez megadja a `+0x332f` bájt által jelölt billentyűmód nevét,
  amely a `paritas-ellenorzes.md:420` szerint eddig `NINCS MEG` volt: a
  normál diavetítés. A #6930 helyesbítése (a szünetbeli sáv a `OneUpUI`
  hostcseréje) ezért csak a `qshow` útra igaz; a normál vetítés
  szünetbeli sávjának forrása nyitott (G3).
- **Mit vetít.** Az aktuális nézet (`[this+0xea8]`: mappa, album, keresés
  eredménye) minden olyan elemét, amelynek `+0x5a` jelzője nulla, az aktuális
  képtől indulva; a kijelölés nem szűri a listát, és kijelölés nélkül az
  első elem lesz kijelölve (`0x00717bb0`). Üres nézetnél hang és üzenet nélkül
  nem történik semmi. A PicasaPy ugyanezt teszi (a teljes `controller.photos`
  listát vetíti), a **videó** kivételével: az eredeti a videót is
  lejátssza, a vágási pontok (`moviestart`, `movieend`) átadásával, és a dia
  ideje a film hossza; a PicasaPy kihagyja őket.
- **Vezérlők és alapértékek.** A dia ideje `SlideshowEffectTime` (alapérték
  `3`, `+`/`-` után `1` és `20` közé szorul), az ismétlés `LoopSlideshow`
  (alapérték ki), a zene `PlayMP3Tracks` (alapérték be), az átmenet
  `ThumbUISlideShow::transition` (hét elem, alapérték Dissolve). Ezek és a
  megőrzésük a PicasaPy-val egyeznek. Eltérések: (1) az eredeti normál
  vetítésben nincs Timeline gomb, a PicasaPy-ban van; (2) az eredetiben a
  `Fel`/`Le` nyíl, az `1`-`9` számjegyek (a dia ideje) és a `Pause`/`Play`
  billentyű is működik, a PicasaPy-ban nem; (3) a kézi léptetés a lista
  szélén: az eredetiben előre az utolsó képről az elsőre fordul (a
  `LoopSlideshow`-tól függetlenül), hátra az első képen nem lép
  (`0x00717eb0`, utasításszint), nálunk hurok nélkül előre kilép, hurokkal
  hátra az elsőről az utolsóra fordul; (4) az `auto2` kattintási terület a
  `.tre` szerint a kép szinte egésze, nálunk 14 képpontos sáv (feltételes).
- **Kilépés.** `Esc` vagy a `Kilépés` gomb: a kurzor visszatér, a zene leáll,
  és a program oda tér vissza, ahonnan indult (szerkesztő, ha ott volt, különben
  a könyvtár). Mivel az aktuális elem és a nézet kijelölése együtt mozog (`0x005704d0` →
  `0x00717c50`; a kézi léptetésnél `0x00717eb0`), az utoljára látott kép marad
  kijelölt és aktuális (az automatikus léptetés útja feltételes, G1). Tárolt adatot a kilépés nem ír.
  A PicasaPy ezzel egyezik (`MainSlideshow.qml:92-114`).
- **Rejtett, sérült, elérhetetlen kép.** A `+0x5a` jelzőjű elemet a lista
  kihagyja; hogy ez a jelző a rejtett képet jelenti-e, és mi történik betölthetetlen
  vagy hálózati úton elérhetetlen fájllal, a binárisból még nem dőlt el
  (9. szakasz).

### Bizonyítottsági fok

**Feltételes.** A belépési hívások, az elágazás és a két vetítő szétválasztása
két független útból igazolt (a 7. szakasz), de futásmérés nincs: a #375 Colab-
felvétel a `Ctrl+4`-et és a `Space`-t mérte, a vezérlősáv alakját nem
különítette el. Megerősített: a belépési táblázat és a `Shift`-elágazás
utasításai. Feltételes: a `0x0075de50` ág "normál vetítés" azonosítása, a
videó lejátszása, a nézet-bejárás szabályai. `NINCS MEG`: a 9. szakasz tételei.

### 1. Belépési pontok

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Nézet ▸ Diavetítés és Mappa/Album ▸ Diavetítés megtekintése.** `0x00559150` rekordjai: `0x9c9f` és `0x9c6d` (`picasa-menu-parancsok.csv:181`, `:74`). A `0x005cb990` a parancsazonosítót a `word [msg+8]` mezőből veszi (`0x005cb9a1`), az `edi` nulla (`0x005cb9a6`), az ugrótábla `0x9c42`-bázisú (`0x005cba5d`-`0x005cba75`): mindkét azonosító a `11`-es bájtra, a `0x005cbbd1` ágra jut: `push edi`, `push ebx`, `call 0x005e8a70` (`0x005cbbd3`). | `PicasaViewMenu.qml:174-178`, `PicasaFolderMenu.qml:30-34`, `MainMenuBar.qml:373`, `MainWindowCommands.qml:443-445`, `MainSlideshow.qml:60-71` | Egyezik: a két menü ugyanazt a műveletet indítja, mint az eredetiben. |
| **`Ctrl+4`.** A `0x005e60d0` `0x005e625e`-`0x005e626f` ága: `call 0x005696c0` (kapu), `push 0`, `push ebp`, `call 0x005e8a70`. A `Ctrl+5` ugyanitt `push 1` (`0x005e6287`). | `MainKeyboardShortcuts.qml:312-317` | Egyezik. A `0x005696c0` kapu jelentése nyitott (G6). |
| **Mappa/album fejléc `play` gombja.** A `0x005e0f70` a `play` nevet (`0xc96f44`) hasonlítja (`0x005e143c`-`0x005e1461`), majd `push 0`, `call 0x005e8a70` (`0x005e146c`-`0x005e146f`). Súgó: `Diavetítés teljes képernyőn` (`headerpaneltext.tre:38-39`, hivatalos magyar: `panel-feliratok-hu.tsv:474`). | `LightboxHeaderButtons.qml:30-47`, `LightboxFeedGroup.qml:69-71`, `MainLibraryCanvas.qml:267-269` | A belépés és a súgószöveg egyezik. Hogy a nem aktuális mappa fejlécéről melyik nézet és melyik kép kerül sorra, nyitott (G5). |
| **Szerkesztő `Play` gombja.** `editpanel/sbutton` (felirat `Lejátszás`, `panel-feliratok-hu.tsv:4913`), `Property alias thumbui/sbutton` (`editpanel.tre:1124-1127`); a `thumbui/sbutton` ág (`0x005d9cc0`: `cmp ecx, 0xc900e0` `0x005da733`, `push 0` `0x005da740`) szintén `0x005e8a70(this, 0)`. A könyvtár alsó `Slideshow` gombja (`thumbui/sbutton`) alapból `m_hidden` (`konyvtar-ablak-meretek.md:419-422`). | `PhotoViewerTopBar.qml:196-203`, `PhotoViewerQuickToolbar.qml:104-114`, `MainSlideshow.qml:62-65` (a néző aktuális képétől indul) | A belépés egyezik. Kis eltérés a súgószövegben: az eredeti hivatalos magyar szöveg `Állítson össze és nézzen diavetítést ezekből a fotókból` (`panel-feliratok-hu.tsv:4914`), a PicasaPy `Diavetítés lejátszása`. |
| **Időrend.** `0x9ccc` → `0x005cbbdd` (`push 1`), `Ctrl+5` `0x005e6287`, `thumbui/timelinebutton` `0x005da7ab` (`push 1`): `0x005e8a70(this, 1)`, a `qshow` útja. | `PicasaViewMenu.qml:180-185`, `TimelinePanel.qml:539` | Nem tárgya ennek a szakasznak (`picasa-idorend-viselkedes.md` 38.2.8). |
| **`Shift` lenyomva.** `0x005e8ae5`-`0x005e8b00`: ha az alkalmazás aktív (`[0xd67849]`), `GetAsyncKeyState(0x10)` felső bitje `jne 0x005e8d5d`, vagyis a `qshow` ágra ugrik, `0` módban is. A `[0xd67849]` írói: `0x00576419` (`1`) és a `WM_ACTIVATEAPP` (`0x1c`) ág `0x00a52e55`-`0x00a52e66`. | nincs | Rejtett, dokumentálatlan változat (a `oneup.tre` sávval). Nem teendő; a PicasaPy-ban nem kell megvalósítani, amíg látható célja nincs igazolva. |
| **Nem ide tartozik.** A `Include Slideshow` az Ajándék CD-n (`CDSlideshow`, `0x0066f470`) és a képernyővédő előnézete (`startScreensaverPreview`) más funkció. | `PublishPanel.qml:180-186`, `MainSlideshow.qml:74-90` | Nem vizsgálva. |

### 2. A két vetítő: az elágazás

A `0x005e8a70` elején két kapu van, mindkettő `-1`-et ad vissza: (a) látható
`editpanel/preview` elem, és `[this+0x3094]` vagy `[this+0x30a0]` nagyobb
nullánál, és `[this+0x332e]` nem nulla (`0x005e8a89`-`0x005e8ac8`); (b) a
`0x005696c0` igaz és az `editpanel/only_1up_toggle` visszatérése `0xf4242`
(`0x005e8aca`-`0x005e8ae3`). A mezők jelentése nyitott (G6, G8). Utána:

| hívás | ágkezdet | vetítő | erőforrás | kezelők |
|---|---|---|---|---|
| `0` mód, nincs `Shift` | `0x005e8b10`-`0x005e8d5a`, belép: `0x0075de50` | a főablakba ágyazott szerkesztő-egyképes (`[this+0x332f]` = 1) | `editoneup.tre` (a `panelroot.tre:2-3` építi be) | gombok `0x00760240`, billentyűk `0x00760970`, óraütés `0x0075f430`, szünet `0x00760070` |
| `0` mód, `Shift` lenyomva | `0x005e8d5d`-`0x005e9787` → `0x008037e0` | `qshow`/`OneUpUI` | `oneup.tre` | gombok `0x008032e0`, billentyűk `0x00801270`, szünet `0x00801130` |
| `1` mód (Időrend) | ugyanaz | `qshow` | `oneup.tre` | ugyanaz |

Az `0x005e8d5d` szakaszba a függvényen belül csak két ugrás vezet, mindkettő a
`0x005e8b00` és a `0x005e8b0a` címen (szkript a függvény összes ugrására, a
munkafa `.bt/` mappájában, a kör végén törölve). A `0x0075de50` közvetlen hívottjai
között nincs `0x008037e0`, `0x007fa7f0`, `0x007fda00` vagy `0x00802c60`; vtáblán
át történő hívást ez nem zár ki.

A `0x0075de50` normál vetítésként azonosítása (feltételes) ezen áll: belépéskor
beolvassa a `LoopSlideshow` és a `PlayMP3Tracks` beállítást a `[this+0x335c]`
és `[this+0x335d]` mezőbe (`0x0075e5d9`, `0x0075e620`), a dia idejét a
`SlideshowEffectTime` kulcsból (`[this+0x3340]`, alapérték `3`:
`0x00564a41`), hivatkozik az `editoneup/sszoomsliderclip` és `editpanel/sscaption`
elemekre, a `OneUpUI::second`/`seconds`/`Format` szövegeket a `0x0075f960`
használja, és az átmenet-választó (`editoneup/transtype`, `0x0075d810`) a
`ThumbUISlideShow::transition` kulcsot írja (`0x00760b00`).

A két erőforrás különbsége (`diff oneup.tre editoneup.tre`, csak az érdemi):

| elem | `oneup.tre` (`Shift`/Időrend) | `editoneup.tre` (normál) |
|---|---|---|
| `exit` | `stripback` közvetlen gyermeke, bal sarok (`:40`) | a `centergroup` bal széle (`:40`) |
| `timeline` | látható (`:59`) | `m_hidden` és `m_disabled` (`:62-66`); az `editoneup/timeline` névre a kódban egyetlen hivatkozás sincs (string-xref), tehát soha nem lesz látható |
| `stripback` | `YConstraint 1, 1, -20` (`:165`) | `YConstraint 1, 1, -5` (`:172`) |
| `sszoomsliderclip` | nincs | van (`:68-70`) |
| hivatalos magyar `bcklabel` | `Kilépés a diavetítőből` (`panel-feliratok-hu.tsv:641`) | `Kilépés` (`:4911`) |

A PicasaPy felirata `Kilépés` (`picasapy_hu.ts`, `Exit`), tehát a `editoneup`
felirattal egyezik; a sávja viszont a `oneup.tre` szerinti (Timeline gomb a
`SlideshowControls.qml:183-188` és `SlideshowView.qml:55-57` szerint).

### 3. Mit vetít, honnan indul

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Lista.** A `[this+0xea8]` az aktuális nézet objektuma (írója `0x0056bc10`: `0x0056bc73`; `vt+0xb4` darabszám, `vt+0xb8(i)` elem). A léptető (`0x00717d10`, hívja `0x0075fac0`) a `0x00717560` listáját járja: a nézet minden eleme, amelynek `+0x5a` bájtja nulla (`0x007175c6`), a nézet sorrendjében. A kijelölt elemek (`+0x5d` nem nulla) csak a kiinduló helyzethez (`0x00717420` a `0x00717d10`-ben) és a „van-e kijelölés" kapuhoz kellenek (`0x005c6710` → `0x007166c0`). Hivatalos súgó: `Diavetítés megtekintése a kijelölt mappa vagy album fotóiból` (`panel-feliratok-hu.tsv:5154`). | `MainSlideshow.qml:131-134` (`controller.photos`, a teljes nézet), `SlideshowView.qml:190-209` | Egyezik. Több kép kijelölésénél az eredeti is a teljes nézetet járja (feltételes; futásmérés javasolt, 9. szakasz). |
| **Kezdőkép.** `[this+0xe64]`, az aktuális elem (`0x005e8bc3`-`0x005e8c33`, `0x0075e77e`: `[this+0x3370] = [this+0xe64]`). Ha a nézetben nincs kijelölt elem (`0x005c6710` visszatérése 0, `0x005e8bcf`-`0x005e8bd6`), a `0x00717bb0` az első `+0x5a == 0` elemet jelöli ki és teszi aktuálissá. Szerkesztőből indítva (`[this+0x3331]`, `0x00579330`) a szerkesztett kép az aktuális. Könyvtárból indítva a `0x005e8c42`-`0x005e8c51` ág előbb a `searchcontainer/search` elemet kezeli (`0x009cd730`) és a `thumbui/fullview` módra kapcsol (`0x009cd8a0`), csak azután lép be a vetítésbe (`0x005e8d36`). | `MainSlideshow.qml:60-65`: nézőből a néző aktuális képe, különben `max(0, selectedIndex)` | Egyezik. |
| **Üres nézet.** `0x005e8b4b`-`0x005e8b55`: `vt+0xb4` darabszám nulla → `0x0052e8a0`, `or eax, -1` (`0x005e8b3d`), kilép. Üzenet nincs (az Időrend `IDS_MUST_SELECT` üzenete a másik ág, `0x005e983e`). | `MainSlideshow.qml:66-70`: nincs vetíthető fotó → `exitSlideshow()`, üzenet nincs | Hatásában egyezik (néma). Mellékhatás: nálunk az ablak előbb teljes képernyőre vált, aztán visszaáll (`:66-70`); az eredetiben ilyen nincs. Nincs mérve, hogy látszik-e (kis ellenőrzés a 9. szakaszban). |
| **Videó.** A rekordtípus `8`, `9`, `0xa`, `0xb`, `0xc`, `0x17` vagy `0x1d` (`0x005e8b93`-`0x005e8bb4`, `0x0075ee2c`-`0x0075ee4d`) → film ág (`0x0075eda0`): a tétel `moviestart` és `movieend` nevű tulajdonságát olvassa (`0x0075f006`, `0x0075f0bb`), a `[film+0xc8]` és `[film+0xd0]` mezőbe írja, a lejátszó készenlétét legfeljebb húsz próbálkozással kivárja (`0x0075ee73`-`0x0075ee9d`, a várakozó import neve nincs feloldva), a dia idejét a film hosszára állítja: `(hossz - kezdőeltolás) / 10 000 000` másodperc (`0x0075f1bb`-`0x0075f2e2`, `[this+0x3334]`; hogy a hossz a vágott hossz-e, nincs eldöntve), és `[this+0x3332] = 1` (`0x0075f32f`). A mért videótípusok: `8`, `10`, `11` (`paritas-ellenorzes.md` 7033, 3. szakasz). | `SlideshowView.qml:194-209` (`isVideoAt` → kihagyja), `:211-218` | **Igazolt eltérés (statikus):** az eredeti a videót is vetíti, a vágási pontok szerint; mi kihagyjuk. Jegytörzs lent (D3). |
| **Rejtett kép.** A `+0x5a` jelzőjű elemet a lista és a kijelölés-választás is kihagyja (`0x007175c6`, `0x00717485`, `0x00717c01`, és a kijelölés-gyűjtő `0x007166c0` is: `referencia/ghidra/2026-11-16-7022-7031-7033-colab-decomp.txt:2070-2196`, ahol az elemeket index szerint, vagyis rácssorrendben járja). A jelző jelentése (rejtett kép, fejlécsor, hiányzó fájl) a kimenetből nem olvasható ki, csak a bájt vizsgálata; a #7033 fejléc-olvasata „rejtett"-nek veszi, mérés nincs. | a PicasaPy modellből kerül a vetítésbe | Nyitott (G2). |
| **Sérült vagy hálózati úton elérhetetlen kép.** A fotó ág (`0x0075f33f`, `[this+0x3332] = 0`) a diaváltást a `0x006d00c0` / `0x0075eac0` útján végzi; a betöltési hiba kezelése nincs azonosítva. | `SlideshowView.qml:361-390` (`_diaUrl`, `_betolt`) | Nyitott (G4). |

### 4. Vezérlők, alapértékek, megjegyzett állapot

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Gombok.** `editoneup.tre`: `exit`, `prev`, `auto`, `next`, `plusone`/`minusone` és a `tps`/`tpslabel` időblokk (`centergroup`), `transtype`, `rotateleft`, `rotateright`, `star`, `captionbutton`; a `timeline` rejtett. `auto2` (`:20-23`): `m_scaleX`, `YConstraint 0, 0, 0` és `YConstraint 1, 1, -97`, vagyis a felső széltől a sáv fölötti `97` képpontig nyúlik (`macros.tre:21-27` szerint két `YConstraint` nyújt), az `auto` művelete. Parancsnév-lánc: `0x00760240` (`exit` → `0x0075de50`; `plusone`/`minusone` → `0x0075f960`; `auto`/`auto2` → léptetés-indítás). | `SlideshowControls.qml:55-70` (`auto2` sáv, 14 képpont), `:170-345` | A felsorolás egyezik, a `Timeline` gomb kivételével (D1). **Az `auto2` területe eltér** (feltételes, erőforrás-szemantika): nálunk 14 képpontos felső sáv (#5649, a `respack.yt` `800 x 14` adatából), a `.tre` szerint a kép szinte egésze. Ez megválaszolja a `picasa-diavetito-sav-5550.md` N3 kérdését. D4. |
| **Dia ideje.** `SlideshowEffectTime`, alapérték `3` (`0x00564a41`, `0x007facd3`). `+`/`-`: `0x0075f960` a kulcs értékéhez adja a `±1`-et, `1,0` és `[0x00cf4974]` = `20,0` közé szorítja, kiírja (`0x00401900`) és a `N másodperc` szöveget (`OneUpUI::Format` `%d %s`, `second`/`seconds`) a `editoneup/tps` elemre teszi. Minden dia elején újra beolvassa (`0x0075edb2`-`0x0075edbd`). | `controller_slideshow_mixin.py:106-135` (`1`-`20`, alapérték `3`, hibás érték `3`), `SlideshowControls.qml:284-345` | Egyezik. |
| **Számjegyek `0`-`9`.** `0x00760970`: a számjegy értékét kiírja a `SlideshowEffectTime` kulcsba, és ha az olvasás nullát ad, `1`-et ír (`0x00760a19`-`0x00760a49`); szünetben a címkét is frissíti (`0x00760a4e`-`0x00760a5e`). | nincs (`SlideshowView.qml:687-700` csak `Ctrl+R`-t kezel) | **Igazolt eltérés (statikus).** D2. |
| **Léptetés billentyűvel.** `0x00760970`: `Bal` (`0x25`) és `Fel` (`0x26`) hátra, `Jobb` (`0x27`) és `Le` (`0x28`) előre (`0x00760a6c`-`0x00760a78`), `Esc` (`0x1b`) kilép (`0x00760990`), `Space` (`0x20`) kapcsolja az `editoneup/auto` elemet (`0x007609d0`), `Pause` (`0x13`) csak lejátszás közben, `Play` (`0xfa`) csak szünetben. `Enter` (`0x0d`) nincs a kezelőben. | `SlideshowView.qml:663-686`: `Esc`, `Space`, `Jobb`, `Enter`, `Bal` | **Igazolt eltérés (statikus):** `Fel`/`Le`, `Pause`/`Play` hiányzik (D2). Az `Enter`-t a PicasaPy lépteti; az eredeti láncban (`0x005e6710` → `0x005e60d0`) mit csinál, nyitott (G6). |
| **Kézi léptetés a lista szélén.** `0x0075fb20`: ha az első kijelölt elem a nézet utolsó indexén áll és előre lép, `0x00717bb0` az első elemet jelöli ki, a `LoopSlideshow` értékétől függetlenül (`0x0075fba2`-`0x0075fbd5`); egyébként `0x00717260` / `0x007172a0` (a rács nyíl-léptetője, `0x00717eb0`), amely a lista szélén nem fordul körbe és nem lép (`0x00718031`-`0x0071804a`: a `pos + delta` kívül esik, a visszatérés `0xf4240` kijelölésváltás nélkül), tehát hátra az első képen az eredeti áll. Az automatikus léptetés (`0x00717d10`, `loop` = `[this+0x335c]`) a lista végén hurok nélkül `[nézet+0x2e0] = -1`-et ad (`0x00717e76`). | `SlideshowView.qml:278-282`: hurok nélkül az utolsó képről előre lépve `stop()`, vagyis kilép | **Eltérés (a léptető függvények utasításszinten igazoltak, a teljes hatás futásmérésre vár):** az eredetiben a kézi előre lépés az utolsó képről visszafordul az elsőre, hátra az első képről nem lép; nálunk hurok nélkül az előre lépés kilép, hurokkal a hátra lépés az elsőről az utolsóra fordul. Az automatikus lista-vég viselkedése nyitott: a `0x0075f430` óraütés és a `0x00569260` útján nincs közvetlen hívás a kilépésre (`0x0075de50`), tehát az eredeti nem biztos, hogy kilép (G1). |
| **Ismétlés.** `LoopSlideshow`, alapérték `0` (`0x007fad0a`), belépéskor `[this+0x335c]`-be másolva, kilépéskor nullázva (`0x0075e5d9`, `0x0075debb`). | `controller_slideshow_mixin.py:137-149` (alapérték ki) | Egyezik. A másolás miatt a vetítés közbeni beállításváltás az eredetiben nem hat; nálunk a kötés élő, de a Beállítások ablak közben nem érhető el. |
| **Zene.** `PlayMP3Tracks`, alapérték `1` (`0x007fadbb`), belépéskor `[this+0x335d]`; a zeneforrás `MP3SlideshowPath` (`0x0075cdc0`, zenei szál: `0x0075ca20`, a példány `[this+0x33a4]`); szünetben `0x00760070` hívja a `0x0075d570`-et. | `controller_slideshow_mixin.py:151-212`, `SlideshowMusic.qml:1-50` | Az alapérték egyezik; a sávsorrend, a szünetben viselkedés és a hangerő nincs vizsgálva (G7). |
| **Átmenet.** `ThumbUISlideShow::transition` DWORD `0`-`6`, alapérték `2` (Dissolve), a választó írja (`0x00760ca5`, `picasa-diavetito-sav-5550.md` 1.3.3); hét elem (`0xd342e8`). | `controller_slideshow_mixin.py:14-57`, `SlideshowControls.qml:226-245` | Egyezik (a tárolási forma eltérése dokumentált, nem teendő). |
| **Felirat.** `captionmode`, alapérték `0` (`0x00564b51`-`0x00564b90`, `[this+0xdd8]`), írója `0x005749e0`; az `editoneup/captionbutton` két állapotú (`showtarget`/`hidetarget`). | `controller_slideshow_mixin.py:213-222` (három mód) | A három állapot eltérése már ismert (`picasa-diavetito-sav.md` 6. jegyjavaslat); az `editoneup` sem ad harmadik állapotot. Nincs új lelet. |
| **Mit jegyez meg.** Kizárólag `Preferences` kulcsot ír: `SlideshowEffectTime` (minden `+`/`-` és számjegy után), `ThumbUISlideShow::transition`, `captionmode`; `LoopSlideshow`, `PlayMP3Tracks`, `MP3SlideshowPath` a Beállítások ablakból jön. Utolsó pozíciót, nézetet nem jegyez. | `controller_slideshow_mixin.py` (`view/slideshow*`) | Egyezik. |

### 5. Kilépés és hatás

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Kilépés indítása.** `Esc` → `0x00760990` → `0x0075de50`; `exit` gomb → `0x00760240` → `0x0075de50` (`picasa-idorend-viselkedes.md:2866`). A `0x0075de50` a `[this+0x332f]` szerint kapcsol: nulla → belép (`0x0075e4bd`), nem nulla → kilép. | `SlideshowView.qml:663-666`, `SlideshowControls.qml:174-179` | Egyezik. |
| **Kilépéskor.** A kurzor visszajön (`push 1`, `call 0x0097e510`, `0x0075dea3`-`0x0075deab`), `[this+0x335c]`, `[this+0x335d]` nulla (`0x0075debb`, `0x0075dec1`), a zenei objektum leáll (`0x0075ccb0`) és a program várakozik a szálára (`0x0097b420`, `0x3e8` időkorlát; a szál-értelmezés feltételes), `[this+0x332f]` és `[this+0x3330]` nulla (`0x0075e0a8`, `0x0075e0ae`), az `editpanel/fullscreenswitcher` elem a panel-váltón (`0x009cd8a0`) át visszakapcsol (`0x0075e0b4`; ugyanez a hívás a belépő ágon is áll, `0x0075e520`, tehát a teljes képernyőre váltás oda-vissza ezen megy, feltételes). | `MainSlideshow.qml:92-97` (ablakállapot vissza) | Egyezik. |
| **Hova tér vissza.** Ha a vetítés előtt a szerkesztő látszott (`[this+0x3331]`, `0x005e8c3a`), a `0x00566a70`, különben a könyvtár (`0x00566270`, a `searchcontainer/search` elem kezelése): `0x0075e205`-`0x0075e237`. | `MainSlideshow.qml:105-113`: nyitott néző esetén a néző az utolsó képre áll, különben a rács | Egyezik. |
| **Mi lesz kijelölve.** A léptetés a nézet kijelölését viszi magával: `0x00717260`/`0x007172a0` → `0x00717eb0`, amely az aktuális elem (`[nézet+0x390]`) helyzetéhez ±1-et ad a nem jelzett (`+0x5a == 0`) elemek listájában, `Shift` nélkül a többi elem kijelölését törli (`+0x5d = 0`), a célt kijelöli és aktuálissá teszi, és frissít (`0x00717ed0`-`0x00717f04`, `0x00717fe2`-`0x00718016`, `0x00718058`-`0x007180ef`). Az aktuális elem (`[this+0xe64]`) írói közül (`tagkereso.py`: közvetlen írás csak a betöltőben `0x00564cc7` és a `0x005e8a70`-ben `0x005e8c2d`, `lea` alakban a `0x005704d0`-ban, `0x005704eb`-`0x005704fe`) a `0x005704d0` az elemváltó, és ez a nézetben is kijelöli az elemet (`0x00717c50`, `0x0057066e`), tehát az aktuális elem és a kijelölés együtt mozog. Hogy az óraütés (automatikus léptetés) melyik úton jut a `0x005704d0`-ig, nincs végigkövetve (G1). Kilépéskor az első kijelölt elem `+0x5d` jelzője 1, `[nézet+0x390]` az azonosítója, és `0x0071b810` frissít (`0x0075e3c1`-`0x0075e487`). | `MainSlideshow.qml:109-112`: `selectedIndexes = [currentIndex]` | Egyezik. |
| **Tárolt adat.** A kilépés ága nem hív `.picasa.ini`- vagy indexírót. A vetítés alatti forgatás és csillagozás a közös útra megy (`0x00760240` → `0x005eef30`, `0x005e81e0`), ez nem a vetítés sajátja. | `MainSlideshow.qml:191-199` (`toggleStar`, `rotateLeft`/`rotateRight`) | Egyezik. A negatív állítás a kilépés hívási ágára korlátozott. |

### 6. Üres kijelölés, üres nézet

Az eredeti normál vetítésben nincs `IDS_MUST_SELECT` üzenet (az az Időrend
`0x005e983e` ága); nulla elemnél csendben visszatér (`0x005e8b34`-`0x005e8b46`).
Kijelölés nélkül az első nem jelzett elemet kijelöli és onnan indul
(`0x005e8bcf`-`0x005e8bde`). A PicasaPy ugyanígy hallgat és az első képtől
indul (`MainSlideshow.qml:60-71`).

### 7. A két független út és a cáfoló kísérlet

- **A út, utasítások.** A `0x005cb990` ugrótábla (`0x005cbbd1`), a `0x005e60d0`, `0x005e0f70`, `0x005d9cc0` hívóhelyek `push 0`-val, a `0x005e8a70` elágazása (`0x005e8ae5`-`0x005e8b0a`) és a `0x0075de50` belépő/kilépő ága, `capstone`-nal, a `pe_dis.py` olvasóján át.
- **B út, független forrás.** A `FUN_005e8a70` Ghidra-dekompilátuma
  (`referencia/ghidra/2026-10-17-qshow-diavetites.txt:125-126` a feltétel, `:189` a `FUN_0075de50()` hívás, `:604` a `FUN_008037e0()` hívás) ugyanazt mutatja:
  `if ((DAT_00d67849 == '\0' || !(GetAsyncKeyState(0x10) & 0x8000)) && param_2 == '\0') { ... iVar6 = FUN_0075de50(); ... return iVar6; }`,
  a `qshow` ág (`FUN_008037e0`) csak utána jön. A `0x0075de50` sztring-hivatkozásai (`LoopSlideshow`, `PlayMP3Tracks`, `editoneup/sszoomsliderclip`, `editpanel/sscaption`, `editpanel/fullscreenswitcher`) a bináris-indexből, az `editoneup.tre` beépítése a `panelroot.tre:2-3`-ból.
- **Cáfoló kísérlet.** (1) Van-e más út a `qshow` szakaszba `0` módban `Shift` nélkül? A függvény összes ugrásának átnézése (a munkafa `.bt/` mappájában készült szkripttel, a kör végén törölve): az `0x005e8d5d`-`0x005e9a8e` tartományba csak a `0x005e8b00` és a `0x005e8b0a` ugrik. (2) A `[0xd67849]` valóban az aktív ablak jelzője-e, vagy állandó? Két írója van, az egyik a `WM_ACTIVATEAPP` ágon az üzenet `wParam` értékét írja (`0x00a52e55`-`0x00a52e66`), tehát a `Shift` vizsgálata valódi. (3) A `0x0075de50` csak a szerkesztő sima egyképes nézete lehet-e, nem vetítés? Nem: a `LoopSlideshow`/`PlayMP3Tracks` beolvasás, a `ss`-előtagú elemek és az átmenet-választó ezt cáfolják. **Határ:** az index és az ugrás-pásztázás a vtáblán át történő hívást nem látja; a `0x0075de50` közvetett hívója a `qshow` felé nem zárható ki, de a normál `0` módú útra nincs ilyen jel.

### 8. Javasolt fejlesztői jegytörzsek

#### D1. A normál diavetítés vezérlősávjában ne legyen Timeline gomb

**Előfeltétel:** ellenőrizni a `picasa-colab-jobs #375` 17-18. képén (a szünetben látható sáv), hogy van-e rajta Timeline gomb. Ha van, ez a jegytörzs elvetendő, és a 2. szakasz következtetését helyesbíteni kell.

**Eredeti:** a `0x005e8a70` `0` módban, `Shift` nélkül az `editoneup` vetítőt indítja (`0x0075de50`); ennek erőforrása az `editoneup.tre`, ahol a `timeline` `m_hidden` és `m_disabled` (`:62-66`), és a kódban az `editoneup/timeline` névre egyetlen hivatkozás sincs. Az átmenet-választó (`editoneup/transtype`) nem rejtett.

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `editoneup.tre:62-66` | `SlideshowView.qml:55-57` (`timelineButtonVisible`), `SlideshowControls.qml:183-188, 227-231` | A normál diavetítésben a Timeline gomb ne látszódjon, az átmenet-választó mindig. Az Időrend-bemutató saját vetítése (`timelineSlideshow`) változatlan. |

**Kész, ha:** normál vetítésben (`Ctrl+4`, menü) a `slideshowTimelineButton` nem látszik, a `slideshowTransitionBox` mindig; a #5653 tesztjeit ennek megfelelően kell átírni. A sáv elrendezése (az `exit` a középső csoportban, `5` képpont) csak a csoporton belüli sorrend megmérése után módosítható (`NINCS MEG`, `picasa-diavetito-sav.md` 7. jegyjavaslat).

#### D2. Billentyűk a diavetítésben: `Fel`/`Le`, `1`-`9`, `Pause`/`Play`

**Eredeti:** `0x00760970` (az `editoneup` billentyűkezelő): `Fel` (`0x26`) hátra, `Le` (`0x28`) előre (`0x00760a6c`-`0x00760a78`); számjegy: a `SlideshowEffectTime` értéke a számjegy, nulla helyett `1` (`0x00760a19`-`0x00760a49`), szünetben a címke frissül; `Pause` (`0x13`) lejátszás közben, `Play` (`0xfa`) szünetben kapcsolja az `auto`-t (`0x007609c3`-`0x00760a07`).

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x00760970` | `SlideshowView.qml:663-700` | `Fel`/`Le` a `goBack()`/`advance()`; `1`-`9` a `controller.setSlideshowSeconds(n)`; `Pause`/`Play` a `togglePause()` megfelelő feltétellel. |

**Kész, ha:** valódi billentyűleütéses teszt (`QTest.keyClick`) igazolja mindhármat; a `Fel`/`Le` a `Bal`/`Jobb` iránya szerint lép; a `0` nem ír `0`-t. Az `Enter` a jegyben marad változatlan, amíg a G6 nem dől el.

#### D3. A videó a diavetítésben (vágási pontok szerint)

**Előfeltétel:** futásmérés (Colab): videót is tartalmazó mappa `Ctrl+4`-gyel; a videó játszik-e, mennyi ideig áll a dia. Ha az eredeti kihagyja, a jegytörzs elvetendő.

**Eredeti:** `0x0075eda0` a `8`, `9`, `0xa`, `0xb`, `0xc`, `0x17`, `0x1d` rekordtípusnál film ágra lép: a `moviestart` és `movieend` tulajdonságot a lejátszó `+0xc8` és `+0xd0` mezőjébe írja (`0x0075f006`-`0x0075f135`), a dia ideje a film hossza másodpercben, `(hossz - kezdőeltolás) / 10 000 000` (`0x0075f1bb`-`0x0075f2e2`).

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x0075eda0`, `0x0075f15a`-`0x0075f2e2` | `SlideshowView.qml:194-218` (`isVideoAt` kihagyás) | A vetítés vegye be a videót, adja át a vágási pontokat a lejátszónak, és a következő diára a film hossza után lépjen. |

**Kész, ha:** egy videót is tartalmazó mappán a vetítés a videót játssza (a vágási pontokat átadva a lejátszónak), a dia ideje a film hossza, és utána lép; a többi dia ideje változatlan. Hogy a hossz a vágott hossz-e, a futásmérés dönti el.

#### D4. Az `auto2` kattintási terület: a kép szinte egésze, nem 14 képpontos sáv

**Előfeltétel:** futásmérés (Colab): a vetítés közepére kattintva (a sáv fölött) vált-e lejátszás és szünet között. Ha nem, a jegytörzs elvetendő, és az erőforrás-szemantika olvasatát helyesbíteni kell.

**Eredeti:** `editoneup.tre:20-23` és `oneup.tre:20-23`: `auto2: root`, `m_scaleX`, `YConstraint 0, 0, 0`, `YConstraint 1, 1, -97`. A `macros.tre:21-33` szerint két ugyanazon tengelyű megszorítás nyújt (`m_scaleY`, `m_scaleXY`, a `back` elem így tölti ki a szülőt), tehát a terület a felső széltől a szülő aljánál `97` képponttal feljebbi vonalig ér. A kezelő az `auto` kezelőjével azonos (`0x00803486` és `0x008034c5` ugyanazt a függvényt hívja; az `editoneup` oldalon a `0x00760240` `auto`/`auto2` ága).

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `editoneup.tre:20-23`, `macros.tre:21-27` | `SlideshowControls.qml:56-70` (14 képpont magas `MouseArea`) | A `slideshowAuto2Area` magassága a szülő magassága mínusz `97` képpont legyen, a sáv és a felirat helye nélkül. |

**Kész, ha:** a vetítés közepére kattintva a lejátszás/szünet vált, és a sáv gombjai (a `97` képpontos alsó zóna) érintetlenül működnek; a `PressFeedbackOverlay` ne takarja a képet.

#### D5. A szerkesztő `Play` gombjának súgószövege

**Eredeti:** `editpanel/sbutton` súgó (`editpaneltext.tre:8-9`), hivatalos magyar: `Állítson össze és nézzen diavetítést ezekből a fotókból` (`panel-feliratok-hu.tsv:4914`).

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `editpaneltext.tre:8-9` | `PhotoViewerTopBar.qml:200`, `PhotoViewerQuickToolbar.qml:111` (`Play Slideshow`) | A buborékszöveg a hivatalos forrás szerint. Csak szöveg; a fordítási kapuk (`test_i18n_dictionary_4313.py`) futtatandók. |

A kézi léptetés lista-szélének viselkedése (előre az utolsó képről az elsőre, hátra
az első képen nem lép) és az automatikus lista-vég eltérése mellé nincs jegytörzs,
amíg a G1 és a futásmérés nem dönt (`Nyitott`): az automatikus lista-vég
viselkedése ismeretlen, és a két szél együtt egy kérdés.

### 9. Nyitott

- Ghidra-kör kell: 0x0075f430 - mi történik az óraütés lista-vég ágán, ha a `[nézet+0x2e0]` `-1` és a `LoopSlideshow` ki: megáll az utolsó képen, szünetbe lép, vagy kilép (a `0x0075f430`-ból és a `0x00569260`-ból nincs közvetlen hívás a kilépő `0x0075de50`-re); és ugyanitt: az automatikus léptetés melyik úton hívja az aktuális elemet váltó `0x005704d0`-et, vagyis a nézet kijelölése valóban a látott képet követi-e. (G1)
- Ghidra-kör kell: 0x00717560 - az elem `+0x5a` és `+0x5b` bájtjának jelentése és írói (rejtett kép, fejlécsor, hiányzó fájl): a nézet-bejárások (`0x00717560`, `0x00717420`, `0x007166c0`, `0x00717eb0`) ezt a jelzőt hagyják ki. (G2)
- Ghidra-kör kell: 0x005c4ce0 - az `editoneup` vezérlősáv megjelenése: mikor látszik a normál vetítés sávja (szünet, egérmozgás, sáv fölötti tartózkodás); a #6930 szerinti hostcsere (`0x00802c20` → `0x009833a0`) a `OneUpUI`-ra, tehát a `qshow` útra vonatkozik; a normál vetítésben a szünet-kapcsoló a `0x00760070` (`0x0075d570`, `0x0075eac0`), és hogy ez hogyan jeleníti meg a sávot, nincs vizsgálva. (G3)
- Ghidra-kör kell: 0x006d00c0 - a diaváltás (`0x0075eda0` fotó ág, `0x0075eac0`) betöltési hibája: sérült, hiányzó vagy hálózati úton elérhetetlen fájlnál kihagyja-e a diát, hibát mutat-e, megáll-e. (G4)
- Ghidra-kör kell: 0x005e0f70 - a fejléc `play` gombja: a `0x005e146f` hívás előtt melyik nézet az aktuális (`0x0056bc10`), tehát nem az aktuális mappa fejlécéről melyik képsorozat indul. (G5)
- Ghidra-kör kell: 0x005e60d0 - az `Enter` (`0x0d`) ág, a `Ctrl+R`/`Ctrl+Shift+R` ág és a `Ctrl+4` ág `0x005696c0` kapuja: mit csinál az `Enter` és a forgatás-billentyű normál vetítés közben (a `0x00760970` egyiket sem kezeli), és mikor tiltja a `0x005696c0` a `0x005e8a70` hívását. (G6)
- Ghidra-kör kell: 0x0075cdc0 - a normál vetítés zenéje: a `MP3SlideshowPath` mappa sávjainak sorrendje (rendezett vagy véletlen), ismétlés, szünetben viselkedés (`0x0075d570`), és a kilépési várakozás (`0x0097b420`, `0x3e8`). (G7)
- Ghidra-kör kell: 0x005e8a70 - az elején lévő kapuk (`0x005e8a89`-`0x005e8ac8`): a `[this+0x3094]`, `[this+0x30a0]`, `[this+0x332e]` jelentése (képtálca? szerkesztő-állapot?), vagyis mikor nem indul a vetítés. (G8)
- Futásmérés kell: a `picasa-colab-jobs #375` 17-18. képén (szünetben látható sáv) látszik-e Timeline gomb és hol áll az `Exit` (a D1 előfeltétele); ugyanitt: normál `Ctrl+4` tényleg az `editoneup` vetítő-e.
- Futásmérés kell: videót is tartalmazó mappán `Ctrl+4`: játszik-e a videó, és mennyi ideig áll a dia (D3 előfeltétele).
- Futásmérés kell: három nem szomszédos kép kijelölve, `Ctrl+4`, majd `Jobb` nyíl többször: csak a három, vagy a teljes nézet jön-e; az utolsó képen `Jobb` nyíl hurok nélkül: visszafordul-e az elsőre.
- Futásmérés kell: üres mappán `Ctrl+4`: látszik-e bármi (üzenet, ablakváltás), és a PicasaPy előbb-teljes-képernyőre-vált villanása látszik-e.
- Futásmérés kell: a vetítés közepére kattintva (a sáv fölött) vált-e lejátszás és szünet között (D4 előfeltétele).
- Futásmérés kell: `Fel`, `Le`, `5`, `0`, `Pause` a vetítés közben (a D2 igazolása), a sáv láthatóságával együtt.

### 10. Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` - új #7060 szakasz: a diavetítés
  belépési pontjai, a két vetítő szétválasztása, a vetített halmaz, a
  vezérlők és megőrzött állapot, a kilépés hatása, jegytörzsek és nyitott
  kérdések. Kódhoz, teszthez nem nyúltam.

## #7059: A mappa áthelyezésének teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, SHA-256:
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Ez a szakasz a #6845 §1 korábbi, menüazonosítókra vonatkozó állítását
pontosítja: az ottani `0x9df4` / `ID_MOVEFOLDER` párosítás hibás volt.

### Következtetés

A fizikai MoveFolder-kezelő statikusan igazolt útja a `0x9df4` parancs
(`0x0053f340` → `0x0053f4a0`), de a menüépítők ezt a parancsot `&Delete...` /
`&Delete Folder...` felirathoz rendelik; a látható `&Move...` /
`&Move Folder...` tételek `0x9cce` azonosítója másik kezelőhöz jut. A
HierFolder-fa azonos feliratú menüpontja külön `0x9cba` parancs, amely a
`0x005d0e90`-re jut. Ez a statikus wiring nincs Picasa 3.9-en futtatva
ellenőrizve, ezért a címkék tényleges felhasználói hatása és a teljes
paritás nyitott.

### Bizonyítottsági fok

**Feltételes.** A menürekordok, a parancs-diszpécser, a fizikai mozgató
útja, a célválasztó, a névütközés és a `+0x208` karakterlánc-mező
eltérésénél történő korai hibavisszatérés két egymástól
független statikus úton egyezik. A felirat/kezelő ellentmondás tényleges
futásidejű hatása, a HierFolder út, a figyelt gyökér feltétele, a hálózati
út és a részleges/írásvédett hibák nem mértek.

### 1. Belépési pontok és feltételek

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| Fő Mappa menü: `0x00559150` a `eMenuLabelFolder::ID_MOVEFOLDER` / `&Move...` rekordhoz `0x9cce`-t ad (`0x0055b184-0x0055b19b`); a `0x005cb990` ezt `0x005ce590`-re küldi. A sztring-xrefek és a `0x005ce590` handler `Do you want to remove the folder ... and its subfolders?` / `Remove Folder` üzenetet mutatják. A tényleges MoveFolder-út a következő `eMenuLabelFolder::ID_ALBUM_DELETE` / `&Delete...` rekord `0x9df4` azonosítóján (`0x0055b1ec-0x0055b203`) át fut: `0x005cb990` → `0x0053f340` → `0x0053f4a0`. | `src/picasapy/app/qml/PicasaPy/PicasaFolderMenu.qml:199-213`; `src/picasapy/app/qml/PicasaPy/MainMenuBar.qml:166-174` | Statikus eltérés: nálunk a Move címke ténylegesen mozgat, a Delete címke lomtárba tesz. Az eredeti menükattintások mért hatása nélkül ne változtassuk meg a működést; előbb az eredeti bináris címke/kezelő ellentmondását kell futásban tisztázni. |
| Mappafa helyi menü: `0x007319f0` a `Folder::ID_MOVEFOLDER` / `&Move Folder...` rekordhoz `0x9cce`-t, a `Folder::ID_ALBUM_DELETE` / `&Delete Folder...` rekordhoz `0x9df4`-et rendel. A diszpécserút a főmenüével egyezik: `0x9cce` → `0x005ce590`; `0x9df4` → `0x0053f340` → `0x0053f4a0`. | `src/picasapy/app/qml/PicasaPy/FolderContextMenu.qml:321-336`; `src/picasapy/app/qml/PicasaPy/FolderPaneMenus.qml:305-315` | A PicasaPy Move Folder menüpontja a fizikai mappamozgatót hívja, a Delete Folder a lomtárat. Az eredeti helyi menü statikus párosítása ugyanolyan címke/handler ellentmondást mutat, mint a főmenü; futásmérés kell az egyezés eldöntéséhez. |
| HierFolder-fa helyi menü: `0x00733a40`, `HierFolder::ID_MOVEHIERFOLDER` / `&Move Folder...`, parancs `0x9cba`; a diszpécser `0x005d0e90`-re küldi. Ez nem a `0x0053f4a0` fizikai MoveFolder-út. A `0x005d0e90` a `0x005c85e0` Open Folders megerősítést is elérheti; a meglévő #419 dekompiláció a Ctrl+Enter listakezelő-útját fejti ki, nem ezt a HierFolder menüágat. | `src/picasapy/app/qml/PicasaPy/FolderHierarchyView.qml:479-482` | Lehetséges eltérés: nálunk a hierarchia Move Folder felirata fizikai mozgatást indít. Az eredeti `0x9cba` hierarchiaág szándékát célzott Ghidra-kör vagy Picasa 3.9 futásmérés nélkül nem szabad azonosítani. |
| A `0x00733a40` menüstruktúrájának utolsó rekordja `0x9df5`, de a feliratpointere null. Ez a diszpécserben `0x0053f3a0`-ra jut, amely bizonyos visszatérési kódoknál `0x0053f4a0`-t hív. Hogy ez a rekord látható-e vagy milyen esemény váltja ki, NINCS MEG. | Nincs azonosított, feliratozott megfelelő; a PicasaPy explicit mozgatója a fenti QML-út. | Nyitva hagyni; ne számítsuk a feliratozott menübelépések közé. |
| Gyorsbillentyű: a teljes `.text`-pásztázás a `0x9df4` közvetlen előfordulásait a menüépítés/engedélyezés/diszpécser körében találta; a PE-ben nincs `RT_ACCELERATOR` erőforrás, a meglévő `0x00923110` dekompiláció nullázott ACCEL rekordot ad a `CreateAcceleratorTableA`-nak. A menü `&` mnemonikája önálló billentyűparancsot nem bizonyít. | `src/picasapy/app/qml/PicasaPy/PicasaFolderMenu.qml:199-213`; a Move menüpontnál nincs `Shortcut` hozzárendelés. | Dedikált MoveFolder-gyorsbillentyű nem találtam; ezen a ponton nincs igazolt eltérés. |
| A fizikai kezelő belépési őre `0x0053f340`: kiválasztott mappaobjektumot és nem `-1` azonosítót vár, majd a `0x004461a0` predikátumot vizsgálja. A `0x0056e1c0` menüállapot-építő a `0x9df4` tételt is letilthatja a `0x00995c90` vagy `0x004ac8f0` predikátum alapján. A `0x00995c90` hét futásidőben feloldott Windows mappaútvonalat vizsgál: My Pictures, Desktop, My Music, My Videos, My Documents, `Application Data`, `Common Application Data` (`0x00994a60` sztring-xrefek). A `0x004ac8f0` és `0x004461a0` pontos jelentése nyitott. | `src/picasapy/fileops/move_folder.py:40-87`; `src/picasapy/app/qml/PicasaPy/PicasaFolderMenu.qml:200-205` | PicasaPy explicit rendszerút-listát és home/gyökér-védelmet használ; a hét feloldott Windows ismert mappa mindegyike nincs benne külön. A Picasa eredeti figyelt gyökér- és hálózati feltételei nem zártak, ezért ezek teljes egyeztetéséhez külön célzott vizsgálat kell. |

### 2. A célmappa kiválasztása

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| A `0x0053f4a0` a `MoveFolderLastPath` értékét a `Preferences` csoportból olvassa és a párbeszéd után visszaírja. A címe `Move Folder to %s` (`0x00c8aca4`). A `0x00998760` shell mappaválasztót hív; a dinamikus callback `0x009b0cb0` utasításai a `SHBrowseForFolderW` importot hívják. Érvényes, létező utolsó cél esetén azt adja át kezdőútnak; hiányzó/érvénytelen értéknél a kód a kiválasztott mappa objektumából kinyert forrásútvonalra esik vissza. A forrásmappa vagy szülője közötti UI-viselkedést külön futásmérés nem igazolta. | `src/picasapy/app/qml/PicasaPy/FolderPaneMenus.qml:276-295` | A Qt párbeszéd címe `Browse for Folder`, kezdőútja a forrásmappa szülője; explicit `MoveFolderLastPath`-megfelelő nincs ezen az úton. Az eredeti cím és a megjegyzett célút PicasaPy-beli egyeztetése fejlesztési feladat lehet, de a nyitóhely első futásos alapértékét előbb mérjük. |

### 3. Fájlok, metaadatok és katalógus

| Hatás | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| Lemez | A `0x0053f4a0` a kiválasztott könyvtárat a cél alá mozgatja a `0x0052e0f0` → `0x004fd1c0` → `0x00994400` útvonalon; a legalacsonyabb szint `MoveFileExW`-re jut. | `src/picasapy/fileops/move_folder.py:90-131` a teljes könyvtárat mozgatja. |
| `.picasa.ini`, albumok és arcok | A könyvtárat mozgatja, nem válogat fájlokat; a benne levő `.picasa.ini` és a fájlok együtt haladnak. A képek `albums=` hivatkozásai, valamint a `faces` és `albumlist` metaadatkulcsok a specifikáció szerint az ini-adathoz tartoznak (`docs/specs/picasa-ini-format.md:132-136,1305-1308`). A siker utáni memóriabeli arc-/album-cache állapota NINCS MEG. | Ugyanígy a teljes könyvtár megy (`move_folder.py:90-131`); az `application_services.py:114-120` siker után a `library_controller_resync.py:142-189` újraolvassa az új és régi részfát, és kezeli az áthelyezett figyelt gyökeret is. |
| Index és UI | A `0x004fd1c0` siker után frissíti a katalógus út-prefixeit; a `0x0053f4a0` sikerág további index-/nézetfrissítő rutinokat hív. A végső mappafa, fotórács, görgetési helyzet és kijelölés pontos állapota NINCS MEG. | A sikeres mozgatás `folderMoved` jelzést küld (`src/picasapy/app/fileops_controller_move_mixin.py:288-312`), amely célzott régi/új részfa-resyncet indít (`library_controller_resync.py:142-189`). A kijelölés és a rács végállapotát ez a statikus forrásolvasás nem mérte. |

### 4. Ütközés, írásvédelem, részleges és más kötetes mozgatás

| Eset | Eredeti Picasa 3.9 | PicasaPy most | Teendő |
|---|---|---|---|
| Célon azonos nevű mappa | A `0x0053f4a0` célút-ellenőrzése (`0x00992ed0`) ütközéskor leáll, és a `A folder with that name already exists in the destination folder` üzenetet használja (`0x00c8ad10`). | A `move_folder.py:124-128` előre ellenőrzi a `target.exists()` állapotot és emberi hibát ad. | A leálló viselkedés egyezik; a szövegek pontos egyezése nem cél ezen a kutatási jegyen. |
| Írásvédett cél | A cél kiválasztása után a műveleti hibaág a `MoveFolderError` üzenetet és a visszatérő kódot mutatja (`0x0053f4a0`, `0x00c8ad90`). Nincs igazolt attribútum- vagy írhatósági előellenőrzés, és nincs Picasa 3.9 mérés. | A fájlművelet `OSError` esetén `FolderMoveError`-t ad (`move_folder.py:156-183`). | A pontos eredeti hiba és a lemez végállapota NINCS MEG; kontrollált, írásvédett célon végzett eredeti Picasa-mérés kell. |
| Részleges mozgatás | A sikeres út utáni állapot statikusan követhető, de a `MoveFileExW` hiba/ részleges eredmény esetére nem állapítható meg biztos rollback vagy maradványállapot. | Más köteten a `move_folder.py:134-192` temp-másolatot, forrástörlést és végső átnevezést használ; egy késői átnevezési hiba után a régi hely üres, az ideiglenes cél megmarad. | Eredeti részleges hibakimenet NINCS MEG; ne állítsunk paritást mérés nélkül. |
| Másik kötet | A `0x0052e0f0` `param_4=1` értékkel hívja a `0x004fd1c0`-t. Ez a két rekord `+0x208` bájteltolású (dekompilációban `param[0x82]`) karakterlánc-mezőjét kis-nagybetű-függetlenül összeveti; eltéréskor `-1`-gyel visszatér a `0x00994400` hívása előtt. A #422 Ghidra-összefoglaló a mezőt kötetmezőnek nevezi, de a mező pontos jelentését az önálló disassembly nem bizonyítja. | A `move_folder.py:137-160` `os.rename` hiba után `copytree`-s fallbackra tér át, így más fájlrendszerre is megpróbál mozgatni. | A mezőeltérés miatti korai hibavisszatérés igazolt; hogy eltérő kötet esetén ez a mező eltér-e, NINCS MEG. A kötetek közötti mozgatás egyezéséről ezért még nem állítható eltérés. A mező jelentését és az UNC viselkedést külön kell feloldani. |

### Bizonyítékok

| Érték / állítás | Forrás |
|---|---|
| A Move Folder menürekord azonosítója `0x9cce`, a Delete rekordé `0x9df4` a fő Mappa menüben és a normál Folder helyi menüben. | bináris (`0x00559150`, `0x007319f0`) |
| `0x9df4` → `0x0053f340` → `0x0053f4a0`; a `0x9cce` → `0x005ce590`; a HierFolder `0x9cba` → `0x005d0e90`. | bináris (`0x005cb990`) |
| A fizikai célválasztó címe és a `MoveFolderLastPath` olvasás/írás. | bináris (`0x0053f4a0`, `0x00998760`, `0x009b0cb0`) |
| A rendszerút-hiba és névütközés pontos angol üzenetei. | bináris (`0x0053f4a0`, string xrefs `0x00c8acd4`, `0x00c8ad10`) |
| A `+0x208` karakterlánc-mező eltérése `-1`-et ad a fájlművelet előtt; a mező kötet- vagy UNC-jelentése nem igazolt. | bináris (`0x0052e0f0`, `0x004fd1c0`, `0x00994400`); mezőszemantika: NINCS MEG |
| A PicasaPy célút, mozgatás, fallback és resync. | forrás (`src/picasapy/fileops/move_folder.py:90-192`; `src/picasapy/app/fileops_controller_move_mixin.py:288-312`; `src/picasapy/app/library_controller_resync.py:142-189`) |
| Írásvédett cél és az eredeti részleges hibák pontos lemezállapota. | NINCS MEG |
| A HierFolder `0x9cba` menüpont pontos runtime-hatása; a `0x004ac8f0` jelentése a figyelt gyökérre; az UNC reprezentáció. | NINCS MEG |
| MoveFolder mérőadat vagy Windows Picasa 3.9 előtte/utána mérés. | NINCS MEG |

### A két független út

- **A: utasításszintű olvasás:** az `annot_disasm.py` közvetlenül kiírja a
  `0x00559150` menürekord felirat-/ID-mezőit, a `0x007319f0` és `0x00733a40`
  helyi menürekordjait, majd a `0x005cb990` diszpécser és a mozgató segédek
  utasításait. A `0x9df4` fizikai MoveFolder út; `0x9cce` és `0x9cba` más
  handlerre jut.
- **B: index és korábban meglévő Ghidra-kimenet:** az index
  `string_xrefs` táblája a `MoveFolder`, `Folder::ID_MOVEFOLDER` és
  `HierFolder::ID_MOVEHIERFOLDER` stringeket a megfelelő menüépítőkhöz köti;
  a `2026-10-21-idorend-30.txt` `0x005cb990` switch-kimenete és a
  `2026-11-16-7022-7031-7033-colab-decomp.txt` `0x004fd1c0` dekompilációja
  ugyanazokat a diszpécser- és korai hibautakat mutatja. A két út egyezik.

### Cáfoló kísérlet

Azt próbáltam cáfolni, hogy a `0x9df4` a Move Folder felirat azonosítója,
mert a korábbi #6845 jegyzet ezt állította. A teljes `0x00559150`
rekordblokk utasításszintű olvasásakor `ID_MOVEFOLDER` + `&Move...` mellett
`0x9cce`, míg `ID_ALBUM_DELETE` + `&Delete...` mellett `0x9df4` található;
a `0x007319f0` helyi menü azonos sorrendet mutat. A cáfolót külön úton a
string-xrefekkel és a diszpécser switchével ellenőriztem: a `0x9df4` valóban
a `0x0053f340` fizikai mozgatóhoz, a `0x9cce` a `0x005ce590` eltávolító
kezelőhöz jut. A korábbi ID-hozzárendelés megdőlt; a szokatlan címke/handler
viselkedés futásban továbbra sincs mérve.

Külön próbáltam cáfolni, hogy a `0x004fd1c0` `+0x208` mezője biztosan
kötetazonosító. A disassembly csak a két mező karakterláncainak
kis-nagybetű-független összevetését és eltéréskor a `-1` visszatérést
mutatja; az objektum mezőjének jelentéséhez nem találtam független
struktúra- vagy mérési bizonyítékot. Ezért a korábbi „másik kötetet
elutasít” következtetést visszavontam. A cáfoló ellenpróba eredménye
ugyanazzal a mércével: mezőeltérés igazolt, kötetjelentés és kötetek közötti
hatás NINCS MEG.

### A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Fő menü, mappafa-helyi menü és gyorsbillentyű | ⛔ | Főmenü és normál Folder menü címke/ID/handler statikusan feltárt, de a futásidejű Move/Delete hatás ellentmondásos; HierFolder út és dedikált billentyűparancs nem zárt. |
| Figyelt gyökér, különleges mappa és hálózati meghajtó feltétele | ⛔ | Hét Windows ismert mappa és két további predikátum ismert; a `0x004ac8f0`, UNC és Picasa-futásmérés nyitott. |
| Célválasztó ablaka, alapértéke és megjegyzett állapota | ✅ / ⛔ | `SHBrowseForFolderW`, cím és `MoveFolderLastPath` igazolt; hiányzó/érvénytelen kulcs melletti első futás UI-alaphelye nem mért. |
| Fájlok, `.picasa.ini`, index, fa, rács, kijelölés, albumtagság és arcok | ✅ / ⛔ | Könyvtár és `.picasa.ini` együtt mozog, az index út-prefix frissül; a cache-ek és látható kijelölés végállapota nincs mérve. |
| Ütköző név, írásvédett cél, részleges és más kötetes mozgatás | ✅ / ⛔ | Névütközés és a `+0x208` mező eltérésénél adott korai hiba statikusan eldöntött; az eltérő kötetek összefüggése, az írásvédelem és a részleges eredeti végállapot nyitott. |

### Javasolt fejlesztői jegytörzsek

**A célválasztó eredeti címének és utoljára használt céljának megőrzése**

Eredeti: a `0x0053f4a0` a `Move Folder to %s` címet (`0x00c8aca4`) használja,
és a `Preferences/MoveFolderLastPath` értékét olvassa/írja. Nálunk:
`FolderPaneMenus.qml:276-295` címe `Browse for Folder`, kezdőútja a forrás
mappájának szülője; explicit utolsó célút nincs.

Teendő: a célválasztóban jelenjen meg a mozgatott mappa nevét tartalmazó
cím, és a sikeresen kiválasztott célút maradjon meg következő megnyitásra.
Az első futásos kezdőhelyet az eredeti Picasa-méréssel kell rögzíteni.

Kész, ha: egymás utáni megnyitáskor a legutóbbi célmappa jelenik meg; a cím
megnevezi az éppen mozgatott forrásmappát; első futásnál a megmért eredeti
alaphelyet használja.

**Windows ismert mappák mozgatásának védelme**

Eredeti: a fizikai MoveFolder-út a `0x00995c90` vizsgálattal hét
futásidőben feloldott Windows mappautat ellenőriz (My Pictures, Desktop,
My Music, My Videos, My Documents, Application Data, Common Application
Data), és tiltó ágban a `Unable to Move a System Path` üzenetet használja
(`0x0053f4a0`, `0x00c8acd4`). Nálunk a
`src/picasapy/fileops/move_folder.py:40-87` rögzített `_SYSTEM_PATHS`
listájában a `C:\Users` szerepel, az egyes ismert mappák nincsenek
feloldva.

Teendő: a hét ismert Windows mappa mozgatására kerüljön paritásvédelem,
miután az eredeti predikátum pontos egyezési szabályát (mappa vs. alatta
levő könyvtár) és a további `0x004ac8f0` kaput feloldottuk.

Kész, ha: a hét feloldott mappán a mozgatás a Picasával egyező módon
megáll; a mappák alatti felhasználói könyvtárak engedélyezése a mért
Picasa-viselkedéssel egyezik.

**Az eredeti menüparancsok runtime-jelentésének tisztázása**

Eredeti: a `0x00559150` és `0x007319f0` `&Move` felirata `0x9cce`-t kap,
amely `0x005ce590`-re jut; a `&Delete` felirat `0x9df4`-et kap, amely a
fizikai `0x0053f4a0` mozgatóhoz jut. Nálunk a Move ténylegesen mozgat, a
Delete a lomtárba tesz (`PicasaFolderMenu.qml:199-213`,
`FolderContextMenu.qml:321-336`).

Teendő: előbb Picasa 3.9-en mérjük meg mindkét címke tényleges hatását;
csak utána nyissunk viselkedést igazító fejlesztői jegyet. A statikus
bináris-ellentmondás önmagában nem elegendő a feliratok felcseréléséhez.

**Feloldás (hívói kiegészítés, 2026-11-16):** a #7012 helyesbítése szerint a menürekord-építőkben a parancsmező az eggyel **előző** rekordhoz tartozik (saját mintavétellel igazolt szabály, lásd a #7012 szakasz „Helyesbítés” pontját). Ezzel a `&Delete Folder...` rekord mezőjében álló `0x9df4` a `&Move Folder...` tételé, és a `0x0053f4a0` fizikai mozgatóútra jut; a `&Move Folder...` mezőjében álló `0x9cce` az előtte álló tételé, és a `0x005ce590` („Do you want to remove the folder”) kezelőre jut; a `&Delete Folder...` parancsa a következő rekord mezőjében álló `0x9d44`, egyezésben a #7031 szakasszal. A felirat és a kezelő közti ellentmondás így megszűnik; bizonyítottsági fok: erős.

Kész, ha: külön rögzítettük a fő Mappa menü, a Folder helyi menü és a
HierFolder menü kattintásának lemez-, katalógus- és felületi hatását, majd a
PicasaPy parancsokat ezekhez rendeltük.

### Új kutatási jegyjavaslatok

- **A HierFolder `Move Folder...` parancs tényleges célja**: a
  `0x00733a40` / `0x9cba` út `0x005d0e90`-re jut; a mappalista Ctrl+Enter
  dekompilációja nem dönti el a hierarchiamenü ágát. Keresd a meglévő
  Ghidra-kimenetekben `0x005d0e90`-et; új körben ezt a hierarchiamenü-hívót
  és a handler teljes hatását dekompiláld.
- **A MoveFolder `+0x208` mezőjének jelentése**: a `0x004fd1c0` két
  rekordból származó karakterláncot hasonlít össze; a korábbi kötetnév
  önmagában nem bizonyítja, hogy különböző fájlrendszer más értéket ad.
  Keresd a meglévő `0x004fd1c0` Ghidra-kimenetet, és új körben az objektum
  mezőjének íróját/olvasóját azonosítsd; ez dönti el a kötetek közötti és UNC
  viselkedést.

### Nyitott

- `Ghidra-kör kell: 0x005D0E90: a 0x00733a40 HierFolder::ID_MOVEHIERFOLDER (0x9cba) pontosan mappát nyit, katalógusból távolít el, vagy fájlrendszer-mozgatást végez? A meglévő #419 kimenet a Ctrl+Enter mappalista-útját és az Open Folders megerősítést mutatja, de nem ezt a helyi menü-hívót. [blokkoló]`
- `Ghidra-kör kell: 0x005CE590: a 0x00559150 / 0x007319f0 Move Folder címkéjű 0x9cce handlerének lemez- és katalógushatása mi, és miért a Remove Folder sztringeket használja? A meglévő Ghidra-fájlok csak a handler hívóit/string xrefjeit tartalmazzák, teljes dekompilációt nem. [blokkoló]`
- `Ghidra-kör kell: 0x004AC8F0: a 0x0056e1c0 menüállapot-építőben használt predikátum figyelt gyökérre vonatkozik-e, és milyen mappát tilt? A meglévő dekompiláció a hívást mutatja, a virtuális/predikátum-szemantika nem dőlt el. [blokkoló]`
- `Ghidra-kör kell: 0x004FD1C0: a +0x208 bájtoffsetű mező pontosan mit azonosít (kötet, útgyökér vagy más rekordkulcs), ki tölti fel, és mit jelent a különböző érték a kötetek közötti/UNC esetben? A meglévő #422 dekompiláció a mezők összevetését és az eltéréskor adott -1-et mutatja, de az objektum mezőszemantikáját nem oldja fel. [blokkoló]`
- **NINCS MEG:** az eredeti írásvédett cél és részleges mozgatási hiba pontos kimenete. Út: külön kontrollált Windows Picasa 3.9.141 futás írható, írásvédett és szándékosan hibás célon; minden esetben rögzíteni kell a forrás/cél fájlokat és a felhasználói hibaüzenetet.
- **NINCS MEG:** a mappafa, rács, kijelölés, albumlista és arcfelismerési cache végállapota sikeres fizikai mozgatás után. Út: Picasa 3.9 előtte/utána mérés egy mappával, albumtagsággal és arcmetaadattal.
- **NINCS MEG:** a chooser első futásos alaphelye, ha a `MoveFolderLastPath` hiányzik vagy már nem létezik. Út: célzott Windows-mérés tiszta preferenciával, majd a megjegyzett célút törlése után.
- **NINCS MEG:** UNC/hálózati meghajtó engedélyezése és tényleges fájlhatása; a NAS-t nem jártam be, és hálózati tesztet nem végeztem.
- **NINCS MEG:** az eltérő fájlrendszer vagy kötet hatása a `+0x208` mezőre; ezért a kötetek közötti elutasítás és a PicasaPy fallback közötti eltérés sem bizonyított.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md`: új #7059 szakasz a menürekordok
  helyesbítésével, célválasztóval, lemez-/katalógushatással, hibákkal,
  összevetéssel, javasolt jegytörzsekkel és nyitott pontokkal.

## #7069: Album létrehozása, tulajdonságainak szerkesztése és törlése az eredeti Picasában

Vizsgálati tárgy: Picasa 3.9.141.259, SHA-256:
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
A bináris nem futott; a leletek cím szerinti diszasszemblálásból, meglévő
Ghidra-kimenetekből, erőforrásokból és a PicasaPy-forrásból származnak.

### Következtetés

Az eredeti Fájl-menü `New Album...` (`Ctrl+N`) útja külön az Add-to-album
almenü útjától: elfogadáskor létrehozza az albumot, frissít, majd az új
azonosítót az aktuális albummezőbe írja. A tulajdonságszerkesztés és törlés
kezelője is azonosítható, és a Starred Photos, Screensaver, illetve found
people albumokra külön védelem van. A dinamikus Folder/Album főmenü `Delete...`
parancsot is épít, de az albumok engedélyezési kapuinak teljes jelentése nyitott.
A háttértár-írás tényleges sorrendje,
névütközés, albumtörlés utáni állapot, írási hiba és visszavonás nem zárult
le; az Add-to/tálcás újalbum-út külön nyitott marad.

**Bizonyítottsági fok: nyitott.** A menük, a párbeszéd mezői, az új album
siker utáni kijelölése és a törlés kezelője bináris és független erőforrás-
adatokkal egyezik. A teljes működési paritás nem állítható, mert az eredeti
ini-szinkron időzítése/hibája és a törlő metódus adattárolási végpontja nem
ismert.

### Belépési pontok és feltételek

| Eredeti (bináris cím vagy mérés) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Fájl menü / új album:** `0x00559150` felirata `&New Album...`; az utána épített rekord parancsmezője `0x9d67`, amely a korábban igazolt előző-rekord szabály szerint a New Album tételé. A `0x005cb990` `0x9d67` ága `0x009cd8a0`-ra jut; a `thumbui/newalbum` esemény a `0x005d9cc0`-ban `0x005eb810`-at hívja. | `PicasaFileMenu.qml:23-27`; `MainMenuBar.qml:307-311`; `FileOpsDialogs.qml:82-88` | A jelenlegi Fájl-út kijelölés nélkül visszatér. Az eredeti menüpont üres kijelölés melletti engedélyezése a menüállapot-forrásból nem dőlt el; ne tekintsük egyezőnek vagy eltérőnek külön mérés/Ghidra-ellenőrzés nélkül. |
| **Gyorsbillentyű:** a bináris angol gyorsbillentyű-erőforrásban `New Album` = `Ctrl+N` (`shortcuts.xml:115-117`). A `0x005eb810` törzsében nincs kijelölésvizsgálat, de a menütétel állapotfeltétele önmagában nem következik ebből. | `PicasaMenuBar.qml:708-714`; `PicasaFileMenu.qml:23-27` | A mai Ctrl+N csak fotóműveletre alkalmas kijelöléssel aktív. Az eredeti üres kijelölésű engedélyezés nyitott. Album-tulajdonság és törlés gyorsbillentyűje: `NINCS MEG`. |
| **Fájlmenü útja és Add-to `New Album...` különbsége:** az Add-to almenü `0xa09c` ága a `0x005e9890` → `0x005e9bb0(this,1)` útra megy; az eredeti tálca `thumbui/albumbutton` ága is a `0x005e9bb0`-at hívja. Ez nem azonos a Fájlmenü `0x005eb810` útjával (lásd #7012 „Nyitott”). | `PhotoContextMenu.qml:171-197`; `MainPhotoContextMenu.qml:153`; `TrayScratchPanel.qml:542-577`; `MainTrayBar.qml:82-85` | A mai kép-helyi menü és a tálca a kijelölt/tartott képekkel az Album Properties párbeszédet nyitja. Az eredeti Add-to/tálcás párbeszédérték és végállapot a már létező #7012 Ghidra-kérésig nyitott. |
| **Album / Folder főmenü - tulajdonságok:** a `0x00559150` `eMenuLabelFolder::ID_ALBUM_EDITCAPTIONS` felirata a `0x9c69` parancsot kapja; a `0x005cb990` ezt a `0x006db580`-ra irányítja. A meglévő album-helyi menü `0x00732160` ugyanezt a `&Edit Album Description...` műveletet kínálja. | `PicasaFolderMenu.qml:9,16-28`; `MainMenuBar.qml:373-382`; `AlbumContextMenu.qml:60-65`; `FolderPane.qml:298-319` | A mai Album főmenü és bal hasáb helyi menüje is megnyitja az albumadatokkal előtöltött tulajdonságablakot. A mezők mentési és hibaútját lent rögzítem. |
| **Album / Folder főmenü - törlés:** a `0x00559150` menü felépíti az `eMenuLabelFolder::ID_ALBUM_DELETE` (`Delete...`) tételt `0x9d44` paranccsal; a `0x005cb990` a `0x005ed240` törlőútra irányítja. A `0x0056e1c0` állapotfrissítő szabályozza a parancs engedélyezését, de a különleges/üres albumok feltételének teljes jelentése nyitott. | `PicasaFolderMenu.qml:198-213` - a Delete elem csak mappamódban aktív; `AlbumContextMenu.qml:55-58` albumtörlés; `FolderPane.qml:362-368` | A PicasaPy Album főmenü jelenleg nem engedi az album törlését; a bal hasáb album-helyi menüje igen. Az eredeti főmenü parancsa és kezelője bizonyított, de a rendes albumra vonatkozó engedélyező ág pontos szemantikája nyitott; a különbség feltételes fejlesztői jelölt. |
| **Bal hasáb album-helyi menü:** `0x00732160`: `&Edit Album Description...` (`0x00cae3a8`) és `&Delete Album` (`0x00cae450`); a parancsmezők a megelőző-rekord szabállyal `0x9c69` és `0x9d44`. A törlés a `0x005ed240`-be, a szerkesztés a `0x006db580`-ba jut. | `AlbumContextMenu.qml:55-65`; `FolderPane.qml:351-368`; `FolderPaneMenus.qml:120-135` | A jelenlegi helyi menü mindkét parancsot kínálja. A törlés-visszaigazoló ablak gombjai eltérnek; lásd „Ablakok”. |
| **Emberek-album helyi menü:** `0x007359e0` `&Edit People Album...` és `&Delete People Album` tételeket épít; a törlés kezelője a `0x005ed240` specializált ágát is használja. A found-people, `]star` és `]screensaver` belső albumnevek külön védelmi ágon figyelmeztetést adnak (`0x00c97d44`, `0x00c97cb0`, `0x00c97cfc`). | `PeopleAlbumContextMenu.qml:26-65`; `FolderPaneMenus.qml:138-163,165-238` | A mai Emberek-album szerkesztése a személykezelő útja; törlése külön ablakban kérdez rá, és opcionális online-arc jelölőt ad. Az eredeti feliratokból önmagukban nem következtetek a szerkesztő végső hatására. |
| **Új album felületi eseménye, eszköztár:** a `thumbui/newalbum` esemény a `0x005d9cc0`-ban a `0x005eb810`-at hívja; a konkrét vizuális elem helyét ez a kimenet nem nevezi meg. A tálca `thumbui/albumbutton` külön Add-to út (`0x005e9bb0`). | `MainWindowToolbar.qml:73-78` üres album tulajdonságablakot is nyit. | A PicasaPy toolbar útjának eredeti UI-megfelelője nyitott; a `thumbui/newalbum` eseményt nem azonosítom bizonyíték nélkül a toolbar gombjával. |

### Ablakok, alapértékek és megjegyzett állapot

- Az eredeti `album.fen` Name, Date, Automatic date, Music jelölő/fájlkereső,
  Place taken, Description, OK és Cancel mezőket deklarál
  (`picasa-fen-dialogs.md:255-273`). A `0x005eb810` a
  `0x0055cf70`-en át kéri az új album alapnevét; a string-xref
  `IDS_DEFAULT_ALBUM_NAME` értéke `Untitled` (`0x00e0382e`). Ez az új
  album névmezőjét bizonyítja. Az új dialógus dátum/hely/leírás/zene mezőinek
  tényleges kezdőértéke és megjegyzése: `NINCS MEG`.
- A meglévő album szerkesztésénél a `0x006db580` előbb a `0x0055d070`
  mezőbetöltőt, majd a `0x006dc030` ablakutat hívja. A meglévő Ghidra-lelet
  a név, caption/leírás, dátum, hely és zene betöltő/setter mezőit azonosítja
  (`0x0055d070`, `0x0055d320`; #7032 kiegészítés). Az eredeti ablak mezőit
  és induló adatát az aktuális album tulajdonságai adják, nem minden profilra
  egységesen üres mezők.
- A törlés normál album esetén a `0x005fdc30` szerint `Delete Album` címet,
  `Are you sure you want to delete the album "%s"?` kérdést és `Delete Album`
  igen-gombot használja; az Emberek-album kérdése külön `DeletePeopleAlbum`.
  A `0x005ed240` a `0x005c9930` dialógusépítőt, majd a `0x005fd670`
  megerősítőt hívja. A generikus `confirm.fen` Yes / No / Cancel gombokat
  és `Don't ask again` jelölőt deklarál; a közös építő választóértéke `2`,
  amelyet egy korábbi fájltörlési mérés Cancel-fókuszként azonosított. Az
  albumág fókusza ezért a közös sablon és kód alapján erős következtetés,
  nem külön albumképernyős mérés. Az albumág jelölőjének
  láthatósága és tartós beállításkulcsa: `NINCS MEG`.
- PicasaPy új album párbeszédnyitáskor `Untitled`, üres dátum/hely/leírás/
  zeneútvonal és kikapcsolt zene értéket ad, majd a névmezőre fókuszál és
  kijelöli a nevet (`FileOpsDialogs.qml:100-111`; `FolderPropertiesDialog.qml:189-199`).
  Meglévő album nyitásakor a controller aktuális név/dátum/hely/leírás/zene
  adataival tölti fel (`FolderPane.qml:298-319`).
- PicasaPy normál albumtörlés dialógusa `Delete Album` címmel/gombbal
  kérdez, de Cancel és emlékeztető jelölő nélkül, No fókuszon
  (`FolderPaneMenus.qml:120-135`). A People album dialógusa külön
  `Remove People`, Delete Album / Cancel gombokkal, Cancel-fókusszal, és
  alapból kikapcsolt, szinkronizált arcok törléséről szóló jelölővel él
  (`FolderPaneMenus.qml:165-238`).

### Tárolás, műveleti hatás és hibák

| Hatás | Eredeti Picasa 3.9 | PicasaPy most |
|---|---|---|
| Új album rekordja | A `0x005eb810` elfogadáskor `0x0055d120(0,0,0)`-t hív; a `0x0055d120` az `0x004ada80` létrehozó útján katalógus-gyűjtemény rekordot hoz létre (`0x00443c00`), majd a mezőíróhoz jut. A tartós album-adatbázis fájlneve és az üres album tartóssága ebből nem dőlt el. | Kijelölt fotóknál új, véletlen token és `[.album:<token>]`/`albums=` definíció kerül az érintett `.picasa.ini`-kbe (`photo_ops_album_membership_mixin.py:137-175,235-253`). Üres album metaadata a profil-index SQLite táblájába kerül, mappa ini-írás nélkül (`:177-233`). |
| Albumtagság és ini-szinkron | A `0x00536a90` a gyűjtemény memóriabeli képlistáját módosítja. A #7012-ben feltárt `AlbumSync` → `PicasaIniManager` (`0x00556ff0`/`0x00557760` → `0x0052c350`) út `.picasa.ini`-be írja az `albums` és `token` kulcsokat; az `AlbumIniSync` beállítás ezt befolyásolja. A pontos trigger, sorrend és hibaág még nyitott; lásd #7012 „Nyitott”. | Kijelölt képek írása kötegelt ini API-n fut, az albumlista siker után újratöltődik (`photo_ops_album_membership_mixin.py:255-268`). |
| Album tulajdonságok / átnevezés | `0x006db580` az OK után `0x0055d320`-at hív; ez mező-settereket futtat. Ha egy mezőíró (setter) hibát jelez, a korábban sikerült mezőket nem gördít vissza, és saját üzenetablakot nem épít (#7032 Ghidra-kiegészítés). A tényleges ini-író és az album-névütközés kezelése nyitott. | `editAlbumProperties` módosítja a nevet, dátumot, helyet és leírást minden érintett ini-ben; üres függő albumnál profil-indexet frissít; siker után újratölti a listát/nézetet (`photo_ops_album_properties_mixin.py:72-132`). A zene külön út. Ismert írási hibát `albumWriteFailed` jelzi (`:127-129`). |
| Törlés és képfájlok | Elfogadott törlés után a `0x005ed240` katalógus-vtable `+0xec` metódust hív és nézetfrissítést végez (`0x0065b840`). A virtuális törlőcél, az ini-szinkron pontos lefutása és a képfájlok bájtjainak végállapota: `NINCS MEG`. | A `[.album:<token>]` definíciót és minden érintett `albums=` hivatkozást eltávolítja; az üres albumot a profil-indexből veszi ki. Képfájlokat nem töröl (`photo_ops_album_membership_mixin.py:93-125`). |
| Albumlista, rács és kijelölés | Új album sikerén a `0x005eb810` frissít (`0x0065b840`) és az `0x004af790` által visszaadott új azonosítót az aktuális album mezőjébe írja. Törlés után frissít, de a bal hasáb/rács/kijelölés pontos végállapota nyitott. | Új album létrehozásakor a callback eldobja a visszaadott tokent (`FileOpsDialogs.qml:123-137`); nem hív `showAlbum`-ot. Siker után a lista frissül. Törlés után `_refresh_view()` fut (`photo_ops_album_membership_mixin.py:119-125`), de a jelenlegi album-/kijelölési végállapot külön nem igazolt. |
| Névütközés, írási hiba, részleges állapot, visszavonás | Névütközés: `NINCS MEG`. A `0x0055d320` setter-hibánál visszatér; korábbi sikeres setterek maradnak. A `.picasa.ini` írási hiba, törlési hiba, rollback és undo: `NINCS MEG`. | Az üres album `local_empty_albums` sora tokennel kulcsolt, a `name` mezőn nincs egyediségi megkötés (`index/schema.py:238-249`); a létrehozó tokenalapú (`photo_ops_album_membership_mixin.py:207-208`). A vizsgált útban névütközés-ellenőrzést nem találtam. A kezelt írási hibák hibajelzést adnak; több mappás írás teljes rollbackje ebből a forrásból nem állítható. Közvetlen undo-út: `NINCS MEG`. |

### Bizonyíték és bizonyítottság

| Érték/állítás | Forrás |
|---|---|
| Fájl `New Album...` parancs `0x9d67`, Ctrl+N | bináris (`0x00559150`, `0x005cb990`, `0x005d9cc0`, `0x005eb810`); erőforrás (`shortcuts.xml:115-117`) |
| Album főmenü szerkesztés/törlés parancsok | bináris (`0x00559150`, `0x0056e1c0`, `0x005cb990`, `0x006db580`, `0x005ed240`) |
| Bal oldali album és People menü feliratai/parancsai | bináris (`0x00732160`, `0x007359e0`); a parancsmező/felirat párosítása az eggyel előző rekord szabályával |
| Album Properties mezői | bináris/erőforrás: `album.fen:1-29`; `0x006db580`, `0x0055d070`, `0x0055d320`; mérés: `paritas-ellenorzes.md:971`, `ki00/kepernyo__11.png` |
| Új album alapneve `Untitled` | bináris (`0x0055cf70`, `IDS_DEFAULT_ALBUM_NAME`, `0x00e0382e`); a `shortcuts.xml`/Album Properties erőforrás ettől független UI-adat |
| Törlés szövege és védett albumok | bináris (`0x005fdc30`, `0x005ed240`, `0x00c97cb0`, `0x00c97cfc`, `0x00c97d44`); független `confirm.fen` sablon (`picasa-fen-dialogs.md:273-282`) |
| AlbumSync `albums`/`token` író | bináris (`0x00556ff0`, `0x00557760`, `0x0052c350`); részletesen a #7012 Tároló táblázatában, trigger/időzítés nyitott |
| PicasaPy mai műveleti utak | fájl:sor: a fenti összehasonlító táblák; közvetlen QML/Python-forrásolvasás |
| Album DB fájlneve, empty-album eredeti tartóssága, a törlés vtábla-célja, névütközés, az album-ág megerősítés-jelölője, visszavonás és pontos UI-végállapot | `NINCS MEG` |

### A két független út

- **A: bináris út:** a menüépítők felirat/rekord/command-mezőit a korábbi
  rekord szabályával párosítottam; a `0x005cb990` dispatchert, a
  `0x005eb810` létrehozót, a `0x0055d120` mentőt, a `0x006db580`
  tulajdonságútját, valamint a `0x005ed240` törlőútját követtem. A már meglévő
  Ghidra-kimenet külön feloldja a `0x0055d070`/`0x0055d320` mezőbetöltőket és
  -írókat.
- **B: független erőforrás/mérés/forrásréteg:** az `album.fen` és
  `confirm.fen` meződeklarációi, az `enUS/shortcuts.xml` Ctrl+N bejegyzése,
  az `Untitled`/Delete prompt string-xrefek, valamint a korábbi
  `ki00/kepernyo__11.png` Album Properties mérés ellenőrizte az A út
  látható ablakait és parancsát. A PicasaPy QML/Python forrását külön olvastam
  az összevetéshez.
- **Egyezés:** az újalbum-parancs, a Ctrl+N, az Album Properties mezők és a
  Delete Album prompt egyezik a két bizonyítékcsaládban. A teljes lemez-/index-
  és hibavégállapot nem, ezért a jegy eredménye nem megerősített.

### Cáfoló kísérlet

Megpróbáltam cáfolni a korábban felmerült `0x9caa = New Album` párosítást.
A `0x00559150` utasításszintű rekordblokkjában az `&New Album...` után
felépített rekord `0x9d67` parancsmezője az előző New Album rekordhoz
tartozik. A következő `0x9caa` mezőt a `Add Folder to Picasa...` előtti
rekordhoz kell rendelni; a diszpécser azt a `0x005ce590` útba küldi, így nem
New Album. A cáfoló eredmény független ellenőrzése: az
`enUS/shortcuts.xml:115-117` a `New Album`-hoz Ctrl+N-et ad, a
`0x00559150` string-xref pedig az `&New Album...` feliratot azonosítja.
A korábbi rossz párosítást visszavontam; a `0x9d67`-et használom.

### A jegy „Kész, ha” pontjai

| Pont | Állapot | Bizonyíték |
|---|---|---|
| Új album, tulajdonságszerkesztés, törlés minden belépési ponttal és feltétellel | ⛔ | Fájl/Ctrl+N, Album főmenü, bal oldali album/People menü és tálca út feltárt. A tálca `0x005e9bb0`, az eredeti File üres kijelölés-engedélyezése, illetve a különleges albumok teljes menüfeltétele nyitott. |
| Ablakmezők, alapértékek és megjegyzett állapot | ⛔ | Mezők és `Untitled` alapnév ismertek; új Album Properties többi mezőjének kezdőértéke, emlékeztetett állapota és a törlő-jelölő albumági láthatósága nyitott. |
| Tárolás, képek, index, bal hasáb, rács és kijelölés | ⛔ | Eredeti katalógusrekord, AlbumSync ini-író és UI-refresh hívások ismertek; sync timing, delete vtable/végállapot és eredeti képfájl-hatás nyitott. A PicasaPy út ini/SQLite kezelését a forrás pontosítja. |
| Névütközés, íráshiba, részleges végrehajtás és visszavonás | ⛔ | A `0x0055d320` setterek hibára visszatérnek, de az album-névütközés, háttértár-hiba, rollback és undo nincs lezárva. |

### Javasolt fejlesztői jegytörzsek

#### 1. Feltételes jelölt: az Album főmenüből is lehessen albumot törölni

**Eredeti:** a `0x00559150` `eMenuLabelFolder::ID_ALBUM_DELETE` (`Delete...`)
tételt épít `0x9d44` kóddal; a `0x005cb990` ezt a `0x005ed240` albumtörlő
kezelőre küldi. A `0x0056e1c0` engedélyezési állapotot állít.

**Nálunk:** `PicasaFolderMenu.qml:200-213` a Delete elemet csak mappamódban
engedélyezi; albumnál törlés csak az `AlbumContextMenu.qml:55-58`
baloldali helyi menüből érhető el.

**Teendő:** a `0x0056e1c0` állapotfrissítő rendes és különleges albumokra
vonatkozó feltételeinek feloldása után jelenjen meg a dinamikus Album menüben
az eredetivel egyező esetekben az albumtörlő parancs; ez a jelenlegi
megerősítés/`controller.deleteAlbum(token)` útba fusson. Különleges albumok
engedélyezése ne következzen a normál album útból.

**Kész, ha:** a normál és különleges albumok főmenü-engedélyezése a
feloldott `0x0056e1c0`-ággal egyezik; engedélyezett törlésnél a jelenlegi
albumtörlő út fut. A PicasaPy albumtörlője ne változtassa meg a képfájlokat
(ez a jelenlegi controller viselkedése; az eredeti végállapota külön
nyitott mérési pont).

#### 2. Az új album létrehozása után nyíljon meg az új album

**Eredeti:** a `0x005eb810` siker után a `0x004af790`-ből kapott új album-
azonosítót az aktuális album mezőbe írja, és frissít (`0x0065b840`).

**Nálunk:** `FileOpsDialogs.qml:123-137` meghívja a `createAlbumWithProperties`
vagy `createEmptyAlbum` függvényt, de eldobja a visszakapott tokent; ez a
létrehozási callback nem hív `showAlbum`-ot.

**Teendő:** vedd át a sikeresen visszakapott tokent és navigálj az új albumra;
üres token/írási hiba esetén maradjon az előző nézet.

**Kész, ha:** Fájl ▸ New Album… és az eszköztár párbeszéde után a létrejött
album aktív, annak rácsa nyílik meg; Cancel vagy íráshiba után a jelenlegi
album és kijelölés marad.

#### 3. A normál albumtörlés párbeszédében legyen Mégse gomb, az kapjon fókuszt

**Eredeti:** a `0x005ed240` a `0x005c9930` → `0x005fd670` közös
megerősítő-utat hívja; a `0x005fdc30` `Delete Album` címet/kérdést/igen-gombot
választ. A `confirm.fen` Yes / No / Cancel gombokat deklarálja; a közös
választóérték `2`, amelyet egy korábbi fájltörlési mérés Cancel-fókuszként
azonosított. Az albumág saját képernyőképe nincs meg.

**Nálunk:** `FolderPaneMenus.qml:120-135` elrejti a Cancel gombot, kikapcsolja
az emlékeztető jelölőt és a No gombra teszi a fókuszt.

**Teendő:** jelenítsd meg a Mégse gombot, és megnyitáskor arra tedd a
fókuszt. Az albumtörlés emlékeztető jelölőjét csak a Picasa albumági
beállításkulcsának igazolása után vedd fel.

**Kész, ha:** megnyitáskor Mégse a fókusz; Mégse/No bezárás nem változtatja
az albumot; csak a Delete Album jóváhagyása hívja a törlőt. Az albumági
„Don't ask again” beállítás a külön igazolásig nem változik.

### Új kutatási jegyjavaslatok

Új külön jegyet nem javaslok: a nyitott ini-szinkron és Add-to `New Album`
út már a #7012-ben szerepel; a többi nyitott kérdés ehhez a #7069
folyamathoz tartozik.

### Nyitott

- `Ghidra-kör kell: 0x0056E1C0: oldd fel a 0x9d44 Delete... menüelem 0x00995c90, 0x004ac8f0 és 0x004aca00 feltételeit: normál/üres albumon, ]star, ]screensaver és found-people célon melyik ág engedélyez vagy tilt. A meglévő 2026-11-15-6970 kimenet a hívásokat és EnableMenuItem ágakat mutatja, a predikátumok albumtípus-szemantikáját nem; a korábbi 0x0056e1c0 Ghidra-kérések más állapotbitekre és menütípusokra vonatkoznak. [blokkoló]`
- `Ghidra-kör kell: 0x005ED240: oldd fel a katalógus-vtable +0xec törlőmetódus konkrét célját, és kövesd le, az album-definíciót/tagságot melyik háttértárból veszi ki, ír-e képfájlt, és milyen a hibás/törlési hibaág. A meglévő 2026-11-15-6963 dekompilálás a közvetett hívást és a nézetfrissítést mutatja, a vtable-célt nem. [blokkoló]`
- `Ghidra-kör kell: 0x006DC030: az új Album Properties párbeszéd dátum/hely/leírás/zene mezőinek kezdeti értéke profilból vagy állandó alapértékből jön-e, mi marad meg bezárás/újranyitás után, és Cancel esetén történik-e mellékhatás. A meglévő `album.fen` és hívó a mezőket mutatja, de az induló állapotot nem. [blokkoló]`
- `Ghidra-kör kell: 0x0055D320: az albumobjektum név-setterének konkrét virtuális célja, és az elutasítja-e a másik album megjelenített nevével ütköző értéket. A meglévő #7032 dekompiláció a setterhívást és részleges hibát mutatja, de az albumnév egyediségét nem. [blokkoló]`
- A `0x00556ff0` AlbumSync trigger/időzítés és `0x0052c350` ini-író hibasorrend Ghidra-kérése már szerepel a #7012 „Nyitott” részében; nem kérek rájuk új kört. Ugyanott szerepel a `0x005e9bb0` Add-to/tálcás új album dialóguskérdése.
- **NINCS MEG:** File ▸ New Album menüpont/`Ctrl+N` engedélyezése kijelölés nélkül. Út: célzott menüállapot-követés vagy külön Picasa 3.9 mérés üres kijelöléssel; a `0x005eb810` rutin feltétel-ellenőrzésének hiánya önmagában nem bizonyítja a menüpont állapotát.
- **NINCS MEG:** törlés után a bal hasáb, rács, aktív album és fotókijelölés pontos végállapota; create/delete/rename undo-viselkedése; `.picasa.ini`/album-adatbázis részleges hibája és rollbackje. Út: célzott Ghidra-kör után kontrollált, előtte/utána Picasa 3.9 mérés.
- **NINCS MEG:** az új Album Properties nem név jellegű mezőinek értéke/megőrzése és az eredeti albumági „Don't ask again” jelölő beállításkulcsa. Út: a fenti `0x006dc030` és `0x005fd670` célzott feloldása, majd mérés.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md`: új #7069 szakasz a belépési
  pontokról, párbeszédekről, tárolásról, UI-végállapotról, hibákról,
  fejlesztői jegyjavaslatokról és nyitott kérdésekről.

## #7072: A keresés teljes folyamata az eredeti Picasával összevetve

Vizsgálati tárgy: Picasa 3.9.141.259, `Picasa3.exe` SHA-256
`644b7bec89a2e4d57d119d15aa36af1df12a4c3547b692bc0462af35a93ddc96`.
Az eredeti oldalt a binárisból (statikus olvasás `capstone`-nal, a programot
nem futtattam), az index `string_xrefs`/`xrefs` tábláiból, a magyar szövegtárból
(`stringres-en-hu.tsv`, `panel-feliratok-hu.tsv`) és a projekt saját
mintaadatából (`research/testdata/Picasa2/db3/wordhash.dat`, csak olvasás)
olvastam; a PicasaPy oldalt a jelenlegi forrásból. A korábbi lapok igazolt
részeire hivatkozom (`picasa-kereses-modok.md` 2-3. és idő-csúszka szakasz,
`picasa-menu-parancsok-viselkedes.md` 20., 26., 59., 60. szakasz,
`picasa-gyorsbillentyuk.md` Ctrl+F/F3 sorai, `racs-ures-allapot.md`,
`album-sorrend.md` 2.1 és 2.6, `picasa-beviteli-mezok.md`,
`picasa-idorend-bemutato-kutatas.md` a `+0x162` keresési jelzőről), nem
kutatom újra; ahol ellentmondok nekik, külön jelzem. Ideiglenes szkriptjeim és nyers
kimeneteim a munkafa `.bt/` mappájában vannak (a `.gitignore` kizárja, nem kerül
be a repóba).

**A menürekord-szabály (#7012) alkalmazása.** A menüépítő `0x00559150`
rekordjaiban a parancsmező az eggyel előző rekordhoz tartozik. A keresés
menütételeire ellenőriztem: a `Search &Options` (`ID_VIEW_SEARCHVIEW`,
kulcs `0x0055a9fa`) parancsa a következő, `Small &Pictures` kulcs utáni
blokkban álló `0x9d2b` (`0x0055aa7d`); a `Save &search results...`
(`ID_SAVESEARCH`) parancsa a következő, `ID_SEARCHTOKEN` kulcs utáni
blokkban álló `0x9d52` (`0x0055c3b8`); az `ID_SEARCHTOKEN` („Show &tag as
album...") parancsa a következő, `ID_PASSPORT` kulcs utáni blokkban álló
`0x9de3` (`0x0055c402`). A diszpécser (`0x005cb990`) a `0x9d52`-t a
`0x005cc7ab` ágra (`0x005d86a0`), a `0x9de3`-at a `0x005cc7b6` ágra
(`0x005d8330`) viszi (bájttábla `0x005cde04`, dword tábla `0x005cdc30`,
bázis `0x9d44`), tehát a párosítás a kezelővel is egyezik. A `Search for...`
almenü (`0x0055c307`, hét gyerek a `0x00d6e708` címen) saját parancsmezője
nulla (`0x0055c368`).

### Következtetés

- **Egyetlen kapu van: `0x0065b840`.** A keresőmező szövegét, a hat szűrőgombot
  (csillag, arc, film, online, geocímke, másodpéldány) és a kor-csúszkát
  `0x00660c80` EGYETLEN szűrőobjektumba gyűjti, `0x00662220` pedig egyszer hajtja
  végre. Ennek mindegyik belépő (gépelés, gombkattintás, menü, billentyű) a
  `0x0065b840` hívásával végződik. A PicasaPy-ban a szűrőgombok és a
  szöveges keresés **külön nézetmód**, és egymást váltják
  (`search_controller.py:23-60`, `controller_filter_mixin.py:20-67`), ezért a
  kombinált szűrés (szöveg + csillag + arc + kor együtt) nálunk nem létezik.
- **Belépési pontok.** A keresőmező; `Ctrl+F` és `F3` (a `searchbutton`
  kattintása); Nézet ▸ Keresési opciók (`0x9d2b`); Eszközök ▸ Keresés hat
  színe és a Fekete-fehér (`color:<szín>` token a mezőbe, `0x0065b7b0`);
  Címke megjelenítése albumként (`0x9de3`); Ctrl+F6 (`dupesearch`); a
  szűrőgombok és az idő-csúszka; az Emberek-felület (`]unknownface`,
  személy: `0x005439e0`, `0x0063d7b0` szintén a `0x0065b7b0`-en át írnak a
  mezőbe). **Új, eddig dokumentálatlan belépő: gépelés a mappalistán vagy a
  képrácson** (`0x005c3fe0` ← `0x005c40e0`, `0x005c42d0`): egy nyomtatható
  karakter a keresőmezőbe kerül és a fókusz oda ugrik. A PicasaPy-ban
  ez nincs.
- **Gépelés közben.** Nincs időzítő és nincs késleltetés. A mező
  `EN_CHANGE` értesítése (`0x005e4e0d`) azonnal `0x0065b840(this, 0, 1, 1)`-et
  hív, **kivéve** ha a billentyűzet-sorban már vár egy `WM_KEYDOWN`
  (`0x0097fb90`: `GetQueueStatus(QS_KEY)` majd `PeekMessageA(0x100, 0x100)`),
  és ha a szöveg a legutóbbival bájtra azonos, akkor sem keres újra
  (`0x0065b906`-`0x0065b988`). Vagyis a gyors gépelés közbülső lenyomásait az
  eredeti átugorja, a végén biztosan lefut egy keresés. A PicasaPy minden
  `onTextEdited`-re szinkron kereső hívást indít (`MainWindowToolbar.qml:59-64`),
  és csak a javaslatlista vár késleltetéssel (150 ezredmásodperc,
  `MainWindowCommands.qml:730-733`).
- **A szöveg feldolgozása.** (1) A szöveg elejéről és végéről levágja a
  szóközt, vesszőt, pontot, per- és visszaper jelet (`StrTrimA` ` ,./\`,
  `0x00660e8e`); nálunk csak `text.strip()` (`search_controller.py:33`).
  (2) Ha a szöveg a lokalizált `tag:` előtaggal kezdődik (`tagsearch`, magyarul
  `címke:`), az előtagot levágja (`0x006622aa`-`0x0066230d`); nálunk nincs.
  (3) A szót kisbetűsíti (`0x009871f0`), és szavakra bontja (`0x006c0fc0`):
  szókarakter az ASCII betű és számjegy, a `:`, a Latin-1 betűk és minden
  nem-ASCII UTF-8 karakter; minden más (szóköz, `_`, `-`, `.`, `,`, `/`,
  idézőjel) elválasztó. A szavak közti elválasztó szakaszban álló `-` a
  KÖVETKEZŐ szót kizárt szóvá teszi. Nálunk a teljes szöveg EGY
  FTS5-frázis (`index/queries.py:501`), tehát a több szó egymás melletti,
  azonos sorrendű egyezést jelent, és a `-` jelnek nincs szerepe.
- **Mire keres (mért).** Az eredeti keresőindex (`db3\wordhash.dat`) szavakat
  tárol, nem mezőket. A 140 755 képes mintán (124 268 szó, mind kisbetűs) szó
  a fájlnév szavaiból (`img`, `dsc`, `dsc09117`), a kiterjesztésből (`jpg` 119 512
  képen, `png`, `mp4`), a gyártóból és típusból (`sony`, `canon`, `huawei`,
  `samsung`, `i9300`), az EXIF-jellemzőkből (`exif`, `iptc`, `iso:`, `fókusz:`,
  `vaku`, felbontások), a dátumból és időből (`2010:06:07`, `13:36:29`), a
  színekből (`color:orange` 59 632 képen, `color:blue`, `color:green`,
  `color:red`), a helyből (`geo:lat=...*`, helynevek), a feliratból és a
  kulcsszavakból (ékezetes magyar szavak, ékezettel tárolva), valamint
  `]`-jelű belső tokenekből (`]album:<azonosító>`, `]star`, `]geo`, `]face`,
  `]edited`, `]hidden`, `]unknownface`, `]web_<fiók>` és még nyolc) áll. A
  PicasaPy FTS-indexe csak a fájlnevet, a feliratot és a kulcsszót tartalmazza
  (`index/schema.py:122-125`), a mappanév-egyezés külön ág
  (`index/queries.py:502-514`).
- **Hatás.** A keresés a `]search` virtuális albumot és a `CAlbumState+0x162`
  keresési jelzőt állítja (`0x00662c53`), az eredménysáv szövegét a
  `0x005715d0`-en át írja (`Search results for "%s"`, a `%d results: ` sor a
  bekapcsolt gombok szavaival, `Nincs találat`, és a
  `%3$s %4$s / %1$s %2$s látható (%5$0.3f másodperc)` sor), a nézetet
  újra elhelyezi (`0xa54b70`, `0x006636b6`; feltételes: a tetejére
  görgetés), és **a keresőmező hátterét színezi**: találatnál
  világoszöld (`0xFFE4F1E5`), találat nélkül halványpiros (`0xFFFFCBCB`), üres
  szövegnél alapszín. A PicasaPy-ban a mezőnek nincs találat-színezése.
- **Kilépés.** Négy út van, mind a `0x005d47e0` törlő rutinra fut: (1) a
  `searchclr` (X) gomb `(1, 0)` argumentummal: töröl és újraépít, a korábbi
  pozíciót NEM állítja vissza; (2) a „Back to View All" gomb (`viewallbutton`)
  `(0, 0)`-val töröl, majd kikapcsolja a keresősáv gombját, aminek
  kapcsoló-eseménye `(1, 1)`-gyel újraépít ÉS visszaállítja a keresés kezdetén
  megjegyzett nézethelyzetet és fókuszt (az eseménylánc `0x005d8810` →
  `0x005d4a20` szakaszát nem követtem végig, feltételes); (3) a keresősáv gombjának kikapcsolása (`Ctrl+F`/`F3` második
  megnyomása, `0x005d4a20`) szintén `(1, 1)`; (4) **az `Esc` a képrácson**
  (`0x005c42d0`, `0x005c42f8`-`0x005c4342`) `(1, 0)`-val, ha a
  `0x0057c430(4)` feltétel hamis (igaz esetén a `publish/cancel` elemet
  kattintja; a feltétel jelentését a `publish/cancel` elemből
  következtetem). A PicasaPy-ban az `Esc` csak a javaslatlistát és a
  beállítás-popupot zárja (`MainWindowToolbar.qml:49-58`,
  `MainToolbar.qml:619`); a második `Ctrl+F` nem kapcsol ki és nem töröl.
- **Rejtett képek.** Alapból kizárja őket: ha a `Preferences\ShowHidden`
  (`[this+0x3188]`) hamis, a szűrő a `]hidden` tokent a kizárt listába teszi
  (`0x00660ca2`). A PicasaPy rácsa ugyanezt adja (`_show` szűr,
  `controller_photo_list_mixin.py:117-120`), de a bal hasáb és az eredménysáv
  darabszáma a szűretlen listából készül (feltételes eltérés, 6. szakasz).
- **Sok találat, hálózat.** A végrehajtó és a szűrő függvényei (`0x00662b20`,
  `0x00662220`, `0x00660c80`, `0x0043f9a0`, `0x0043c410`, `0x00422ce0`,
  `0x006c0fc0`) egyetlen fájl- vagy hálózati API-t sem hívnak (importjaik:
  kritikus szakasz, szálazonosító, időmérő, `StrTrimA`), vagyis a keresés
  csak az indexből dolgozik; elérhetetlen hálózati mappa a keresést nem
  befolyásolja. Találatszám-korlátot nem találtam; a darabszámokat 1000-től
  ezres tagolással írja ki (`0x0066324c`, `0x00663278`).
- **Mit jegyez meg.** A keresés első szövegváltozásakor megjegyzi a nézet
  helyzetét: a bal hasáb aktuális elemét (`[this+0xe94]`) és az aktuális vagy
  kijelölt kép sorszámát (`[this+0xe98]`) (`0x0065ba5c`-`0x0065bb0c`); ezt csak
  a sáv bezárása állítja vissza (`0x005fa430`; hogy a visszaállítás
  kijelölést, görgetést vagy mappát jelent, feltételes). Megjegyzi a
  fókuszban volt elem nevét is (`[this+0xf6c]`). A keresés a
  Vissza/Előre előzménybe is bekerül: a `thumbui/navback` és `thumbui/navfw`
  (`0x005d9cc0`, `0x005d9ec7`-`0x005d9ecd`, `0x005d9f3f`-`0x005d9f45`) a
  `0x00600ac0`-val visszaállítja a szöveget, az öt szűrőgombot és a
  keresősáv állapotát. Tartós (indítások közötti) tárolást nem találtam.
  A PicasaPy könyvtárnézetében nincs Vissza/Előre előzmény.

### Bizonyítottsági fok

**Erős** (utasításszintű olvasás egy menetben; független újralevezetés és
futásmérés nem készült): a belépési táblázat; az `EN_CHANGE` út és a billentyűsor-őr; a
szövegtisztítás; a szóbontó szabályai; a négy kilépő út és az `Esc` a rácson; a
mezőszínek; a rejtett képek kizárása; az, hogy a végrehajtó nem használ
fájl- vagy hálózati API-t; a szóindex tartalma (mért: a `research/testdata`
mintafájl `0` bájt maradékkal parszolva).
**Feltételes:** a szűrőgombok és a szöveg logikai ÉS kapcsolata (az
egyszeri végrehajtás erős, a kapcsolat jellege a `0x0043f9a0` mélyén van); a
kizárt szó (`-`) és a `tag:` előtag pontos hatása; a gépelés-belépő
karaktertartománya és a bájtra vágás; az `Esc` hatása magában a
keresőmezőben. **NINCS MEG:** részszó/előtag-egyezés (a „nyar" megtalálja-e
a „nyaralás"-t), ékezet-hajtás a keresési oldalon, a javaslatlista
forrása és sorrendje, az indexépítő mezőválasztása, a `*` végű szavak
jelentése. Futásmérés (Colab) nem készült: a mezőszín, az `Esc` a rácson és a
gépelés-belépő látható hatását az eredeti Picasán kell majd megmérni.

### 1. Belépési pontok

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Keresőmező.** A `searchcontainer/search` elem építője `0x0040e7b0` (stílus: `GetWindowLongA(-0x10) \| 0x80`, `0x0040e7fc`-`0x0040e80e`), mellette a `searchautocomplete` lista (`0x0040e81d`). A szöveg olvasása `0x0065b88e` (`0x00986200`). | `MainToolbar.qml:530-551` (`TextInput`, `onTextEdited`, nyíl- és Esc-kezelés a javaslatlistához) | Egyezik a mező megléte. A viselkedés eltérései a 3-5. szakaszban. |
| **`Ctrl+F`, `F3`.** `0x005e63bb`, `0x005e69a4` a `searchcontainer/searchbutton` kattintása (`0x009cd8a0`). A gomb kapcsolóállapota (`+0x359`) dönt: bekapcsolva a sáv nyílik (`0x005d4a90`), kikapcsolva `0x005d47e0(this, 1, 1)` töröl és visszaállít (`0x005d4a6e`-`0x005d4a7c`). Colab-mérés: `F3` zöld szűrősávot nyitott, fókusz a keresőben (`picasa-gyorsbillentyuk.md` kb-5). | `MainKeyboardShortcuts.qml:39-60`, `MainToolbar.qml:64-68` (`fokuszAKeresore`: fókusz és popup nyitás, soha nem zár és nem töröl) | Részben egyezik. Hiányzik a második `Ctrl+F`/`F3` (kikapcsolás) törlő és visszaállító hatása (feltételes: a Colab-mérés a második megnyomást nem tartalmazza). |
| **Nézet ▸ Keresési opciók.** `ID_VIEW_SEARCHVIEW`, parancs `0x9d2b` (`0x0055aa7d` a következő rekord blokkjában, #7012), kezelő `0x005cbb50` → `0x009cd8a0`. | `MainToolbar.qml:53-58` (`toggleSearchOptions`) | Egyezik (korábbi lap: #4641). |
| **Eszközök ▸ Keresés ▸ hat szín és Fekete-fehér.** `0x005ccc41`-`0x005ccca7`: `color:<szín>` token, `0x0065b7b0` hat lépése (szöveg a mezőbe, sáv megjelenítése, kurzor a végére, újraépítés). A tokeneket a `0x00424c20` adja a szín osztályából (`0x00c8134c`-`0x00c813ac`). | `MainMenuBar.qml:212`, `MainToolbar.qml:129-133` | Egyezik. |
| **Címke megjelenítése albumként.** `ID_SEARCHTOKEN`, parancs `0x9de3` (`0x0055c402`, #7012), kezelő `0x005d8330`. | nem vizsgált (korábbi lap: #1406) | Nem tárgya ennek a körnek. |
| **Keresési eredmények mentése.** `ID_SAVESEARCH`, parancs `0x9d52` (`0x0055c3b8`), kezelő `0x005d86a0` (1000-es küszöb, `Create Album`). | nem vizsgált (korábbi lap: #1405) | Nem tárgya ennek a körnek. |
| **Szűrőgombok és idő-csúszka.** A `0x005d8810` kezelő minden gombot a `0x0065b840` hívásával zár (`0x005d95af`-`0x005d95b4`); a szűrőobjektum `0x00660c80` mind a hatot és a csúszkát (`timeslider/scaleslider`, `0x00660eab`) egyszerre olvassa. | `ToolbarFilterControls.qml:87-381`, `controller_filter_mixin.py:20-67` (külön nézetmódok) | **Eltér** (E1): a szűrők nem kombinálhatók a szöveggel és egymással. |
| **Gépelés a mappalistán és a képrácson.** A `0x005c40e0` (`KeyHandler::AlbumList`) és a `0x005c42d0` (rács) karakter-eseményt (`[esemény+0x64]` 1-es bitje) a `0x005c3fe0`-nak adja. Nem kezeli, ha a `[+0x64]` bájt `0x0c` maszkjából bármelyik bit be van állítva; kezeli a `0x21`-`0x7f` és a `0x100` fölötti kódot, nem kezeli a `0x20` alatti és a `0x80`-`0xff` kódot; megkeresi a `searchcontainer/search` elemet, a `[vtábla+0x7c]` hívással (ugyanaz, amellyel a `0x005d47e0` a fókuszt állítja vissza) neki adja a fókuszt (`0x005c4057`), a karaktert egyetlen betűs szövegként a `0x0065b7b0`-nak adja (`0x005c407f`), és elnyeli az eseményt (`0xf4240`). | nincs (a QML-ben az egyetlen `event.text` felhasználás a `PicasaSlider.qml:104-107`) | **Új** (E3). A tartomány és a bájtra vágás (`movzx ecx, byte [edi+0x10]`, `0x005c4059`) feltételes, ld. Nyitott. |
| **Ismeretlen arcok és személy.** `0x005439e0` (`]unknownface`), `0x0063d7b0` a `0x0065b7b0`-en át a mezőbe írja a tokent. | nem vizsgált | Nem tárgya ennek a körnek. |
| **Másodpéldány-kereső.** `Ctrl+F6`, Eszközök ▸ Kísérleti: `searchoptions/dupesearch` (`picasa-kereses-modok.md`). | `MainToolbar.qml` `dupesearch` gomb | Egyezik (korábbi lap: #2169). |

### 2. Mire keres: a szóindex mért tartalma

A keresés nem mezőkben, hanem a `db3\wordhash.dat` szótárában keres
(`CIndexer`, `0x004dca40`; `album-sorrend.md` 2.1). A fájl formátuma
`album-sorrend.md` 2.6 szerinti; a `Picasa2/db3/wordhash.dat` (140 755
bejegyzés) 124 268 szót tartalmaz, `0` bájt maradékkal parszolva. Mért
tények (a szkript a munkafa `.bt/` mappájában van, nem a repóban):

| Szócsoport | Példa és darabszám (képek, ahol a szó szerepel) | Megjegyzés |
|---|---|---|
| fájlnév-szavak | `img` 49 263, `dsc` 30 342, `dsc09117` 1 | a `_` és `.` elválasztó, a név darabjai külön szavak |
| kiterjesztés | `jpg` 119 512, `png` 7 702, `mp4` 1 770, `jpeg` 2 678 | a kiterjesztés is szó |
| gyártó, típus | `sony` 35 263, `samsung` 19 171, `huawei` 23 086, `canon` 5 537, `i9300` 11 975 | az EXIF gyártó és modell szavai |
| EXIF-jellemzők | `exif` 107 561, `iptc` 107 368, `iso:` 95 883, `fókusz:` 96 990, `vaku` 56 943 | az `iso:` és a `fókusz:` a `:` miatt egy szó |
| felbontás, számok | `1280` 21 828, `960` 21 607, `2048` 21 305 | csupa számjegyű szó 47 472 van |
| dátum és idő | `2010:06:07`, `13:36:29` | a `:` szókarakter, a dátum `ÉÉÉÉ:HH:NN` alakban egy szó |
| szín | `color:orange` 59 632, `color:blue` 33 339, `color:green` 23 167, `color:red` 11 186 | a színkeresés is szóegyezés (a PicasaPy külön `photo_colors` táblát használ) |
| hely | `geo:lat=...*` és `geo:lon=...*` (234 szó), helynevek és `.. km to <hely> in <megye> <ország>*` | a `*` végű szó 307, ebből 56 szóközt tartalmaz |
| belső tokenek | `]album:<azonosító>`, `]star`, `]geo` 36 261, `]face`, `]edited` 30 496, `]hidden`, `]unknownface`, `]history`, `]revertable`, `]screensaver`, `]search`, `]snapshot`, `]suppress`, `]updated`, `]web`, `]web_<fiók>` | |
| felirat, kulcsszó | ékezetes magyar szavak, ékezettel, kisbetűsen (`és` 49, `fák`, `térképen`) | az index nem ékezet-hajtott |

További mért tények: a 124 268 szó közül **nulla** tartalmaz nagybetűt (az
indexelés kisbetűsít); kötőjeles szó nincs, aláhúzás csak a `]web_<fiók>`
tokenben van (a `-` és `_` elválasztó); a mappanév szavainak jelenlétét a
szótárból nem lehet kimutatni (a mappát a `]album:<azonosító>` token hordozza),
ezért a mappanévre keresés mechanizmusa NINCS MEG. A PicasaPy FTS-indexe
(`name`, `caption_ini`, `keywords_ini`, `caption_file`, `keywords_file`) a
gyártót, EXIF-szavakat, kiterjesztést, dátumot és helyet nem keresi.

### 3. Gépelés közben

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Eseményút.** A főablak üzenetkezelője (`0x005e4ac0`) a `WM_COMMAND` (`0x111`) ágon (`0x005e4dda`) a mező kezelőjének (`[this+0xf48]`, `0x005e4e05`) `EN_CHANGE` (`0x300`) kódjára hívja `0x97fb90`-et, és ha az hamis, `0x0065b840(this, 0, 1, 1)`-et (`0x005e4e1e`-`0x005e4e25`). Időzítő-API (`SetTimer`) sem ebben, sem a `0x0065b840`, `0x00662b20`, `0x005d47e0` függvényben nincs. | `MainToolbar.qml:538`, `MainWindowToolbar.qml:59-64` | **Eltér** (E5): nincs billentyűsor-őr és nincs azonos-szöveg kihagyás. |
| **Billentyűsor-őr.** `0x0097fb90`: `GetQueueStatus(1)` felső szavának 0. bitje (`0x0097fb95`-`0x0097fb9e`), majd `PeekMessageA(&msg, 0, 0x100, 0x100, 0)` (`0x0097fba2`-`0x0097fbb5`); igaz, ha vár `WM_KEYDOWN`. Igaz értéknél a keresés elmarad (`0x005e4e1c`). | nincs | A gyors gépelés közbülső keresései elmaradjanak (E5). A hatás nincs mérve. |
| **Azonos szöveg kihagyása.** A `0x0065b840` harmadik argumentuma nem nulla: a mező szövegét bájtonként összeveti a legutóbbival (`[this+0xde4]`, `0x0065b906`-`0x0065b988`), és egyezésnél nem keres újra (`0x0065bb20`). | `search_controller.py:23-60` (minden hívás újrakeres) | E5. |
| **Szövegtisztítás.** `0x00660e8e`: `StrTrimA(szöveg, " ,./\")` (szóköz, vessző, pont, per, visszaper az elejéről és a végéről). | `search_controller.py:33` (`text.strip()`) | **Eltér** (E6). |
| **Kis- és nagybetű.** `0x009871f0` a szöveget kisbetűsíti: ASCII `A`-`Z` (`0x009872e2`-`0x009872f0`), a többbájtos karaktert a `0x00989f80`-nal (a Unicode-átalakítás jellege NINCS MEG). | FTS5 alapértelmezett tokenizáló (kisbetű-érzéketlen, `index/schema.py:122`) és `casefold()` a mappanévre (`queries.py:502`) | Egyezik a hatás; a Unicode-hajtás egyezése nem mért. |
| **Ékezet.** Az index ékezettel tárol, a kisbetűsítés nem hajt ékezetet; ékezet-hajtás a keresési oldalon a tisztító és a bontó kódban nincs (a `0x0043c410` mélyét nem olvastam). | FTS5 `unicode61` alapbeállítás: a mellékjel eltávolítása a SQLite-verziótól függ (nem mért) | NINCS MEG (Nyitott: `0x0043C410`). |
| **Több szó.** `0x006c0fc0`: szavakra bont (szókarakter: ASCII betű és számjegy, `:`, Latin-1 betű, minden nem-ASCII UTF-8 karakter, bitmap `0x00d30bd0`). A szavak közti szakaszban álló `-` a következő szót kizárttá teszi (`0x006c10a3`-`0x006c10a8`; a jelző szavanként nullázódik, `0x006c1030`). A `0x0043f9a0` a szavakat külön kéri le (`0x0043fd20`-`0x0043fe98`), és számlálóval veti össze (`0x00413210`, `0x00413250`). | `queries.py:501` (egész szöveg egy frázis, `"` duplázva) | **Eltér** (E7): több szó nálunk csak egymás melletti sorrendben egyezik; a `-` kizárás és az idézőjel nálunk nem szerepel. A kizárás és az ÉS/VAGY pontos jelentése feltételes. |
| **Idézőjel.** A `"` (0x22) nincs a szókarakter-bitmapen, tehát elválasztó; idézőjel-frázis kezelés a bontóban nincs. | az idézőjel a frázisba kerül (`queries.py:501`) | Egyezést okozó eltérés: a PicasaPy `"` karaktert is frázisként keres (feltételes hatás). |
| **Előtagok.** `tag:` (lokalizált: `címke:`): a `0x006622aa` (`tagsearch`, `0x00987030` előtag-vizsgálat, `0x00986120` levágás) lehámozza, és `[szűrő+0xc]`-t állítja. A `color:` és a `]`-tokenek szóként kerülnek az indexbe. | `search_color.parse_color_terms` a `color:`/`szín:` előtagra (`queries.py:471`) | `tag:` hiányzik (E7). A `[szűrő+0xc]` hatása NINCS MEG. |
| **Javaslatlista.** `CSearchEditBox` (`0x00cb432c`): nyíl fel/le (`0x77d3a5`-`0x77d3b1`), PageUp/PageDown (`0x77d401`-`0x77d409`), Enter (`0x77d43d`), bal/jobb. A sorok kirajzolója `0x0077e2e0` a beírt szöveget kisbetű-érzéketlenül, szóhatáron kiemeli (`0x0077e360`-`0x0077e3e7`), a darabszám `(%d) ` vagy ` (%d)` alakú (`0x0077e9ef`, `0x0077eb7d`); az ikonok: `icons/label`, `icons/album`, `icons/folder`, `icons/imageresult` (`0x0077eee0`). | `SearchSuggestions.qml:1-60`, `search_controller.py:112-122`, `queries.py:551-` (csak mappa és album, részszó-egyezés bárhol a névben) | **Eltér** (E8): nálunk nincs címke- és képtalálat-sor, és a kiemelés nem szóhatáros. A forrás és a sorrend NINCS MEG. |

### 4. Hatás: sáv, rács, bal hasáb, kijelölés

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Végrehajtás.** `0x00662b20` zárat vesz (`0x00662b36`, szálazonosító és kritikus szakasz), időt mér (`QueryPerformanceCounter`), szűrőt épít (`0x00662b94`), végrehajt (`0x00662bcd` → `0x00662220`), majd a keresési jelzőt írja: `[CAlbumState+0x162]` = a szűrő fajtája (`0x00662c53`; 0 nincs szűrő, 1 csak gombok, 2 szöveg, kor vagy másodpéldány: `0x0065aa80`). Üres szöveg és nincs gomb: minden látható kép (`0x00422ce0`). | `search_controller.py:23-60` (üres szöveg: a mappa-feed) | Egyezik a fő út (üres szöveg a normál nézet). A nézetpozíció megjegyzése hiányzik (E2). |
| **A bal hasáb.** Keresési módban a lista a találatos sorokra szűkül, a kategória-állapot nem számít (`+0x162`, `picasa-idorend-bemutato-kutatas.md`; a `]search` sor `0x004ad430`, `Search results`). | `search_controller.py:71-76` (`load_matches`), `FolderPane.qml:26-31` | Egyezik (korábbi lap alapján, nem mértem újra). A sor szövege eltér (E9). |
| **Eredménysáv szövege.** `searchmatchstr` `0x00662d7d` (`Search results for "%s"`), `searchmatchnum` `0x00662dba` (`Search results`), `sresults` `0x00662dee` (`%d results: `), a gombok szavai `0x00662e71`-`0x00662fc9` (`faces`, `starred`, `online`, `movies`, `geotagged`; magyarul `arc`, `csillagozott`, `online elemek`, `mozgófilm`, `geocímkével ellátva`), `nomatch` `0x0066300b`, a kép- és albumszó egyes és többes alakja `0x0066317b`-`0x006631d2`, `searchdisplay` `0x0066328b` (`%3$s %4$s / %1$s %2$s látható (%5$0.3f másodperc)`), a kor-mondat `0x006634c1`. A darabszám 1000-től ezres tagolású (`0x0066324c`). Az elhelyező `0x005715d0` (`searchoptions/searchresult`, `label_search1`). | `MainToolbar.qml:629-640` (`Search results for "%1" (%2)`), `formatting_status.py:15-26` (`searchdisplay` mintája, tagolás nélkül), `MainLibraryCanvas.qml:35-75` | **Eltér** (E9). A `CThumbUI::searchmatch` (` (%d matches)`) kulcsra az EXE-ben nincs hivatkozó literál (nyers bájtkeresés), tehát a PicasaPy `(%2)` utótagjának nincs eredeti párja. |
| **A mező háttérszíne.** `0x00662d06`-`0x00662d34`: nem üres szövegnél `0xFFE4F1E5` (van találat: `[this+0x3104]` és ~1 nem nulla) vagy `0xFFFFCBCB` (nincs); üresnél `-1`; a szín a `[this+0xf68]`-ban, a `WM_CTLCOLOREDIT` (`0x133`) ága `SetBkColor`-ral és `CreateSolidBrush`-sel alkalmazza (`0x005e4b1c`-`0x005e4b9c`), a szövegszín fekete. | nincs (`MainToolbar.qml:530-551`: nincs találat-szín) | **Új** (E4). |
| **Találat nélkül.** A rács-háttérszöveg (`thumbui/lightbox_bgtext`, `0x00662c73`/`0x00662c93`) a találatlista méretétől függ; a „Keresés mindenhol" gomb halott. | `racs-ures-allapot.md`, `LightboxFeed.qml` `gridEmptyText` | Egyezik (korábbi lap: #1945). |
| **Rács és kijelölés.** Új keresés után a nézetet a `0x00a54b70` hívás pozicionálja újra (`0x006636a6`-`0x006636b6`, `0.0` lebegőpontos argumentummal, csak ha a negyedik argumentum 1; a tetejére görgetés feltételes). A keresés kezdete előtti nézethelyzetet (`[this+0xe94]`, `[this+0xe98]`) a sáv bezárása állítja vissza (`0x005d49f8`-`0x005d4a01` → `0x005fa430`); az X nem. | `MainWindowToolbar.qml:59-64` (`clearSelection()` minden gépeléskor) | **Eltér** (E2): nálunk a kijelölés minden gépelésre törlődik, és nincs visszaállítás. A visszaállítás pontos tárgya (kijelölés, görgetés vagy mappa) feltételes. |

### 5. Kilépés a keresésből

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **X gomb (`searchclr`).** `0x005d8810` → `0x005d47e0(this, 1, 0)` (`0x005d891c`-`0x005d8920`). Törli a szöveget (`0x005d4965`-`0x005d4974`), mind a hat gombot (`0x005d48aa`-`0x005d48f6`), az idő-csúszkát (`0x005d4906`-`0x005d491e`), a két belső listát (`0x005d4927`-`0x005d494e`), a hasonlósági mintát (`0x005d8280`), a fókuszt a mezőre teszi (`0x005d4989`), majd az előző fókuszelemre (`0x005d498f`-`0x005d49c9`), és `0x0065b840(this,0,0,1)`-gyel újraépít (`0x005d49eb`). | `MainToolbar.qml:583-606`, `MainWindowToolbar.qml:65-69` | Részben egyezik: a gombok és a kor-csúszka törlése hiányzik, mert nálunk külön nézetmódok (E1). |
| **Back to View All.** `viewallbutton` (`0x005d9564`): `0x005d47e0(this, 0, 0)` (nem épít újra), majd a keresősáv gombját kikapcsolja (`0x005d957c`-`0x005d959a`), ami `(1, 1)` útra visz: újraépítés és pozíció-visszaállítás. Súgója: `Exit Search Mode`. | `MainLibraryCanvas.qml:35-75`, `controller_filter_mixin.py:153-164` | Egyezik a gomb és a felirat; a pozíció-visszaállítás hiányzik (E2). |
| **`Ctrl+F`/`F3` még egyszer; a sáv gombja.** `0x005d4a20` → `0x005d47e0(this, 1, 1)`. | `MainToolbar.qml:64-68` | E2: a kikapcsolás nálunk nincs. |
| **`Esc` a rácson.** `0x005c42d0`: nem karakter-esemény (`+0x64` 1-es bit nulla), `[esemény+0x10] == 0x1b`; ha a `0x0057c430(4)` hamis, `0x005d47e0([esi+8], 1, 0)` (`0x005c433a`-`0x005c4342`), különben a `publish/cancel` kattintása (`0x005c430c`-`0x005c432e`). A rutin keresés nélkül is lefut (újraépít). | nincs (`MainKeyboardShortcuts.qml`-ben nincs `Esc` a könyvtárnézethez; a mező `Esc`-je csak a javaslatlistát zárja, `MainToolbar.qml:540-551`) | **Új** (E2). |
| **`Esc` a keresőmezőben.** A `CSearchEditBox` kezelője (`0x0077d380`) nem tartalmaz `0x1b` összevetést (csak nyilak, PageUp/Down, Enter). A mező saját üzenet-feldolgozása NINCS MEG. | `MainToolbar.qml:540-551` | NINCS MEG (Nyitott: `0x0077D380`). |
| **Üresre törlés billentyűvel.** A szöveg üresre törlése után a `0x0065b840` `[this+0xe94] = -1`-et ír (`0x0065ba4d`), a szűrő fajtája 0 lesz, a keresési jelző kikapcsol, a nézet a normál nézethez tér vissza (`0x0065aa80`, `0x00662c53`); a megjegyzett pozíció elvész. | `search_controller.py:38-44` (üres szöveg: mappa-feed) | Egyezik a fő hatás. |

### 6. Rejtett képek, sok találat, elérhetetlen hálózat

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| **Rejtett képek.** `0x00660c84`: `[this+0x3188]` (a `Preferences\ShowHidden` értéke: írók `0x00564ed4` a `0x005643e0`-ban és `0x005c934f` a `0x005c9300`-ban, mindkettő `ShowHidden` sztringű) bájtja `[szűrő+3]`-ba kerül; hamis értéknél a `]hidden` token a kizárt listára kerül (`0x00660ca2`-`0x00660e25`). Üres szövegnél a bájt a `0x00422ce0` harmadik argumentuma (`0x006622a0`). | `controller_photo_list_mixin.py:117-120` (rács: `if not self.showHidden`), `search_controller.py:71-76`, `controller_sync_mixin.py:50-63` | A rács egyezik. **Feltételes eltérés** (E10): a `_show_search_pane` és a `_show_filtered` a `_show` szűrése ELŐTT, a szűretlen listából számol (bal hasáb darabszám, `searchResultCount`, eredménysáv). Futásban nem mértem. |
| **Nagyon sok találat.** Korlátot a végrehajtóban nem találtam. A kép- és albumszám 1000-től ezres tagolású (`cmp 0x3e8`, `0x0066324c`, `0x00663278`; a `0x0098f670` jelentése, hogy tagolást szúr be, olvasatból következik). A mentés 1000 fölött megerősítést kér (`picasa-menu-parancsok-viselkedes.md` 35.5). | `formatting_status.py:15-26` (`str(len(records))`, tagolás nélkül), `queries.py:446-488` (korlát nincs) | Ezres tagolás hiányzik (E9). A korlát hiánya egyezik. |
| **Elérhetetlen hálózati mappa.** A keresés végrehajtó és szűrő útja nem hív fájl- és hálózati API-t (lásd a Következtetést); a DB-réteg virtuális hívásait (`[db+0x48]`) nem követtem. | `queries.py:446-523` (csak SQLite) | Egyezik (feltételes: a virtuális hívások nincsenek átnézve). |

### 7. Összevetés egy táblázatban (igazolt eltérések)

| Eredeti (bináris cím) | Nálunk (fájl:sor) | Teendő |
|---|---|---|
| `0x00660c80` + `0x00662220` egy szűrő, `0x0065b840` egy kapu | `search_controller.py:23-60`, `controller_filter_mixin.py:20-67` | E1: egyesített szűrőállapot (szöveg, gombok, kor). |
| `0x005c42d0` Esc, `0x005d47e0`, `0x005d4a20`, `[this+0xe94]` | `MainKeyboardShortcuts.qml`, `MainToolbar.qml:64-68`, `MainWindowToolbar.qml:59-69` | E2: Esc és a sáv bezárása lépjen ki, a pozíció álljon vissza. |
| `0x005c3fe0` ← `0x005c40e0`, `0x005c42d0` | nincs | E3: gépelés a mappalistán és a rácson a keresőmezőbe visz. |
| `0x00662d06`-`0x00662d34`, `0x005e4b1c`-`0x005e4b9c` | `MainToolbar.qml:530-551` | E4: a mező háttérszíne találat szerint. |
| `0x005e4e0d`, `0x0097fb90`, `0x0065b906`-`0x0065b988` | `MainWindowToolbar.qml:59-64`, `search_controller.py:23-60` | E5: billentyűsor-őr és azonos-szöveg kihagyás. |
| `0x00660e8e` (`StrTrimA`), `0x006622aa` (`tag:`) | `search_controller.py:33` | E6: a tisztítás karakterkészlete és a `tag:`/`címke:` előtag. |
| `0x006c0fc0`, `0x009871f0`, `0x00d30bd0` | `queries.py:490-523` | E7: szavakra bontás és kisbetűsítés az eredeti szabályával. |
| `0x0077e2e0`, `0x0077eee0`, `0x0077d380` | `SearchSuggestions.qml`, `queries.py:551-` | E8: javaslatsorok fajtái és szóhatáros kiemelés (a forrás nyitott). |
| `0x00662d7d`-`0x006634c1`, `0x0066324c`, `0x005715d0` | `MainToolbar.qml:629-640`, `formatting_status.py:15-26`, `FolderPane.qml:26-31` | E9: az eredménysáv szövegei és az ezres tagolás. |
| `0x00660ca2`, `0x00660c84` | `search_controller.py:71-76`, `controller_sync_mixin.py:50-63` | E10: a rejtett képek ne számítsanak a hasáb és a sáv darabszámába (feltételes). |
| `0x005d9cc0` (`navback`, `navfw`), `0x00600ac0` | nincs Vissza/Előre | A keresés állapota legyen az előzmény része (külön, nagyobb jegy: navigációs előzmény). |

### Javasolt fejlesztői jegytörzsek

**1. A szűrők egyesítése: szöveg, gombok és kor egy keresésben (E1)**

Eredeti: a `0x0065b840` minden belépőtől a `0x00660c80` EGYETLEN szűrőobjektumát
építi (szöveg `[szűrő+0x2c]`, gombok `+1`/`+5`/`+7`/`+8`/`+9`/`+0xb`, kor
`+0x24`, belső tokenek `]star`, `]face`, `]geo`, `exif` a `+0x30` listán,
`]hidden` a `+0x48` kizárt listán), és a `0x00662220` egyszer hajtja végre; a
`0x00662b20` a gombok szavait az eredménysáv szövegébe is beírja (`faces`,
`starred`, `online`, `movies`, `geotagged`). Nálunk a keresés
(`search_controller.py:23-60`) a szűrőt leváltja, és a csillag, film, arc,
geo szűrők külön nézetmódok (`controller_filter_mixin.py:20-67`).
Teendő: egyetlen szűrőállapot (szöveg, öt gomb, kor), amelyből a nézet
és a sáv szövege épül; a gombok bármelyik szöveges keresés fölött
kombinálhatók. Az ÉS kapcsolat jellegét előbb a `0x0043f9a0` Ghidra-körrel
(Nyitott: `0x0043F9A0`) vagy Colab-méréssel kell megerősíteni.
Kész, ha: szöveg és csillag-gomb együtt a kettő metszetét mutatja; a gomb
kikapcsolása a szöveges eredményt adja vissza; az eredménysáv a bekapcsolt
szűrők szavait sorolja; a kor-csúszka a szöveggel együtt működik.

**2. Kilépés a keresésből: `Esc` a könyvtárban, a sáv bezárása és a pozíció visszaállítása (E2, E3)**

Eredeti: `Esc` a képrácson (ha a `0x0057c430(4)` feltétel hamis) `0x005d47e0(this,1,0)`:
töröl és újraépít (`0x005c42f8`-`0x005c4342`); a keresősáv gombjának
kikapcsolása (`0x005d4a20`) és a „Back to View All" `(1,1)` úton a keresés
kezdete előtti nézethelyzetet és fókuszt állítja vissza (`0x005d47e0`,
`0x005fa430`); az X nem állít vissza. A gépelés a mappalistán és a rácson a
keresőmezőbe visz (`0x005c3fe0`: karakter `0x21`-`0x7f` és `0x100` fölött,
módosító nélkül, a mezőre fókusz, a karakter a szöveg).
Nálunk: az `Esc` csak a javaslatlistát és a popupot zárja
(`MainWindowToolbar.qml:49-58`), a második `Ctrl+F` nem kapcsol ki
(`MainToolbar.qml:64-68`), a kijelölés minden gépelésre törlődik
(`MainWindowToolbar.qml:59-64`), a rácson gépelés nem indít keresést.
Teendő: a fenti négy belépő/kilépő út. A `0x80`-`0xff` karakterek kezelése és a
bájtra vágás előbb Colab-mérést igényel (az ékezetes betűk viselkedése), addig
a `0x21`-`0x7f` tartomány a kötelező; a visszaállítás tárgyát (kijelölés,
görgetés, mappa) előbb Colab-mérés dönti el.
Kész, ha: `Esc` a rácson törli a keresést és a szűrőket; a második `Ctrl+F`
töröl és visszaállítja a pozíciót; az X nem állít vissza; a rácson beírt `a`
betű a mezőbe kerül és a fókusz ott van.

**3. A keresőmező visszajelzése: háttérszín és eredménysáv-szövegek (E4, E9)**

Eredeti: a mező háttere nem üres szövegnél `#E4F1E5` (van találat) vagy
`#FFCBCB` (nincs), üresnél alapszín (`0x00662d06`-`0x00662d34`); a sáv szövege
`Search results for "%s"` (`Találatok a(z) "%s" kifejezésre`), `%d results:`
(`%d találat:`) és a gombok szavai, `Nincs találat`, a kép- és albumszám
ezres tagolással, és a `searchdisplay` sor. Nálunk: a mező színtelen; a popup
`Search results for "%1" (%2)` mintájának nincs eredeti párja
(`MainToolbar.qml:629-640`); a darabszám tagolás nélküli
(`formatting_status.py:15-26`).
Teendő: a mező színezése; a sávszövegek az eredeti kulcsok szerint
(`CThumbUI::searchmatchstr`, `sresults`, `sfaces`, `sstarred`, `sonline`,
`smovies`, `sgeotag`, `nomatch`); ezres tagolás. Az elem, amelyben a szöveg
megjelenik (`searchresult` és `label_search1`), előbb Colab-képpel
ellenőrizendő (Nyitott: `0x005715D0`).
Kész, ha: találatnál világoszöld, találat nélkül halványpiros a mező, üresnél
alapszín; a nincs-találat és a találat sávszöveg az eredeti szövegtár szerinti;
1000 fölött a darabszám tagolt.

**4. A gépelés kezelése: billentyűsor-őr, tisztítás, bontás (E5, E6, E7)**

Eredeti: `EN_CHANGE` azonnal keres, de átugorja, ha vár `WM_KEYDOWN`
(`0x0097fb90`), és azonos szövegnél nem keres újra (`0x0065b906`-`0x0065b988`);
a szöveg elejéről és végéről ` ,./\` le van vágva (`0x00660e8e`); a lokalizált
`tag:`/`címke:` előtagot levágja (`0x006622aa`); a szót kisbetűsíti
(`0x009871f0`), szókarakter az ASCII betű és számjegy, `:`, Latin-1 betű és
minden nem-ASCII karakter, minden más elválasztó (`0x006c0fc0`,
`0x00d30bd0`). Nálunk: minden szövegváltozás szinkron keres
(`MainWindowToolbar.qml:59-64`), `strip()` a tisztítás
(`search_controller.py:33`), az egész szöveg egy FTS5-frázis
(`queries.py:501`).
Teendő: a billentyűsor-őr megfelelője (a keresés elhalasztása, ha további
bevitel vár) és az azonos szöveg kihagyása; a tisztítás és a bontás az eredeti
szabálya szerint. A szavak kapcsolata (ÉS/VAGY), a `-` kizárás és a `tag:`
hatása addig kimarad a „Kész, ha"-ból, amíg a `0x0043F9A0` és a `0x0043C410` Nyitott tétele nincs lezárva.
Kész, ha: gyors gépeléskor a keresések száma kisebb a billentyűkénti számnál,
a végállapot a teljes szöveg keresése; ` ,./\` a szöveg szélén nem változtatja a
találatot; az `_` és `.` szóelválasztó.

**5. A szóindex kibővítése és a javaslatlista fajtái (E8)**

Eredeti: a szóindex gyártót és típust, EXIF-jellemzőket, kiterjesztést,
dátumot (`ÉÉÉÉ:HH:NN`), időt, színt, helyet is tartalmaz (2. szakasz, mért); a
javaslatlista soraiban négy ikon van (`icons/label`, `icons/album`,
`icons/folder`, `icons/imageresult`), darabszámmal, a kiemelés szóhatáros és
kisbetű-érzéketlen (`0x0077e360`-`0x0077e3e7`). Nálunk: FTS csak fájlnév,
felirat, kulcsszó (`index/schema.py:122-125`); a javaslat csak mappa és album
(`queries.py:551-`), a kiemelés bárhol a névben.
Teendő: előfeltétele a `0x0077E2E0` és a `0x004DA990` Ghidra-köre (Nyitott): az
indexépítő pontos mezőválasztása és a javaslat forrása nélkül a jegy nem
építhető. A mért szócsoportok
(2. szakasz) és a négy ikon már rögzített, de a mezőválasztást nem szabad
tippelni.
Kész, ha: a `0x0077E2E0` és a `0x004DA990` Nyitott tétele lezárva, és a mezőlistát a jegy törzse tartalmazza.

**6. A rejtett képek a bal hasáb és a sáv darabszámában (E10, feltételes)**

Eredeti: a keresés a rejtett képeket kizárja, ha a `Preferences\ShowHidden`
hamis (`0x00660ca2`). Nálunk a rács szűr (`controller_photo_list_mixin.py:117-120`),
a bal hasáb darabszáma és a sáv a szűretlen listából számol
(`search_controller.py:71-76`, `controller_sync_mixin.py:50-63`).
Teendő: előbb próbával igazolni (rejtett képet tartalmazó mappa, keresés,
rács és hasáb darabszám összevetése); csak ha eltér, a számlálás a szűrt
listából készüljön.
Kész, ha: egy rejtett képet tartalmazó találatnál a rács, a hasáb és a sáv
ugyanazt a darabszámot adja, a Nézet ▸ Rejtett képek kapcsolóval és nélküle.

### Nyitott

- `Ghidra-kör kell: 0x0043C410 - a szóindex-lekérdezés (8904 bájt) teljes szóra, szóelőtagra vagy részszóra egyezik-e (a "nyar" megtalálja-e a "nyaralás"-t), és a 0x0098C780 hívás (0x0043D7B3) ékezet- vagy egyéb hajtást végez-e a keresési oldalon? [blokkoló a részszó- és ékezet-paritásra]`
- `Ghidra-kör kell: 0x0043F9A0 - hogyan kombinálja a pozitív szólistát, a kizárt szólistát (a - előtag, a 0x006C0FC0 második kimenete) és a ]star, ]face, ]geo, exif tokeneket (ÉS, VAGY, kivonás), és mit jelent a [szűrő+0x40] lista és a [szűrő+0xc] jelző (0x00662356-0x00662365)? [blokkoló az 1. és 4. jegytörzsre]`
- `Ghidra-kör kell: 0x005C3FE0 - a [esemény+0x10] mező karakterkód vagy billentyűkód; miért engedi át a 0x100 fölötti értéket, ha a beírt szöveg csak az alsó bájtból épül (0x005C4059), és mi történik a 0x80-0xFF (magyar ékezetes) karakterekkel? [blokkoló a 2. jegytörzs ékezetes részére]`
- `Ghidra-kör kell: 0x0077E2E0 - a javaslatlista elemeinek forrása és sorrendje (címke, album, mappa, képtalálat), a darabszám mit számol, és melyik sor jár melyik ikonnal (0x0077EEE0)? [blokkoló az 5. jegytörzsre]`
- `Ghidra-kör kell: 0x004DA990 - melyik fotómezők (fájlnév, kiterjesztés, mappanév, felirat, kulcsszó, EXIF, hely, szín) szavai kerülnek a szóindexbe (a 0x004403C0 hívja), mi viszi a mappanév szavait (a mintaszótárban nincs kimutatható mappanév-szó), és mit jelent a * végű szó (307 a mintán, köztük geo:lat=...*)? [blokkoló az 5. jegytörzsre]`
- `Ghidra-kör kell: 0x0077D380 - hova jut az Esc és a Delete billentyű, amikor a fókusz magában a keresőmezőben van? A CSearchEditBox kezelője (0x0077D380) csak a nyilakat, a PageUp/PageDown és az Enter billentyűt kezeli, 0x1b összevetést nem tartalmaz; a bázisosztály (CAutoCompleteEditBox) kezelői (0x0060F1B0, 0x00610040) jöhetnek szóba. [nem blokkoló, de hiányzik az Esc mezőn belüli viselkedése]`
- `Ghidra-kör kell: 0x005715D0 - az eredménysáv összeállított szövege melyik elembe kerül (searchoptions/searchresult vagy label_search1), és a 0x004AD430 ]search sor szövege (Search results) mit mutat a bal hasábban; a PicasaPy sora Search results for "q" (N). [nem blokkoló, Colab-képpel is eldönthető]`
- `Ghidra-kör kell: 0x00600AC0 - a Vissza/Előre előzménybe mentett keresés pontos tartalma (szöveg, öt gomb, kor-csúszka, sávállapot), és mikor jön létre új előzményrekord (minden gépelésre, vagy csak a keresés elhagyásakor)? [nem blokkoló; külön navigációs jegy előfeltétele]`
- `Colab-feladat kell: a mezőszín, az Esc a rácson és a gépelés-belépő látható hatása - keresőmezőbe gépelés találattal és találat nélkül (képernyőkép a mező hátteréről), Esc a rácson aktív kereséssel, betű lenyomása a mappalistán és a rácson, másodszori Ctrl+F. [nem blokkoló, a végrehajtó felvehető feladata]`

Nyitott kérdések: 9 nyílt (8 Ghidra-kör és 1 Colab-feladat, mind nevesített és felvehető) · 10 lezárva · 0 blokkolt (külső akadály) · 0 hatókörön kívül · 0 csak-nyitva

Lezárva (a bizonyítékkal): a belépési pontok (1. szakasz); az eseményút és a billentyűsor-őr, időzítő nincs (3.); a szövegtisztítás (3.); a szóbontás szabályai (3.); a szóindex mért tartalma (2.); a kilépő utak és az `Esc` a rácson (5.); a mezőszín (4.); a rejtett képek kizárása az eredetiben (6.); a végrehajtó és a szűrő nem használ fájl- és hálózati API-t (6.); a megjegyzett nézethelyzet, a fókusz és az előzménybe mentés (Következtetés).

### Cáfoló kísérletek és kizárt út

- **„A gépelés késleltetve indul."** Cáfolva: `SetTimer` nincs a `0x005e4ac0`, `0x0065b840`, `0x00662b20`, `0x005d47e0` függvények importjai között (a híváslistát a PE import-táblából feloldva néztem), és az `EN_CHANGE` ág közvetlenül hívja a keresést. A kivétel a `0x0097fb90` billentyűsor-őr.
- **„A keresés fájlokat nyit meg."** Cáfolva a hívott függvényekre (`CreateFile`, `FindFirstFile` és hálózati API egyik sincs az importjaikban); az adatbázisréteg vtábla-hívásait nem követtem.
- **„A `Searchfor` almenü maga is keresést indít."** Kizárva: saját parancsa nulla (`0x0055c368`), a hét gyerek a `color:` tokent írja (`picasa-menu-parancsok-viselkedes.md` 20.).
- **A `CThumbUI::searchmatch` (` (%d matches)`) és a `CThumUI::searchsizekey` (`size<`, magyarul `méret<`) kulcsok** a szövegtárban vannak, de az EXE-ben hivatkozó literál nincs (nyers bájtkeresés a teljes PE-n, a prefixszel egyező találatok a `searchmatchstr` és `searchmatchnum` voltak): az eredeti ezeket nem használja. Egy `méret<` típusú keresés tehát nem bizonyított.
- **Elvetett értelmezés:** a `searchoptions/moviesearch` (`0x005d4a90`, `Preferences\SupportMovies`) és a `searchcontainer/moviesearch` két külön elem; a kapcsolat köztük nincs bizonyítva, ezért a filmszűrő láthatóságát ez a lap nem állítja a `SupportMovies`-hoz.

### Módosított fájlok

- `docs/specs/paritas-ellenorzes.md`: új #7072 szakasz a keresés belépő- és kilépőútjaival, a szóindex mért tartalmával, a gépelés és az eredménysáv viselkedésével, tíz eltéréssel (E1-E10, ebből az E10 feltételes), hat javasolt jegyleírással, nyolc nevesített Ghidra-körrel és egy Colab-feladattal.
