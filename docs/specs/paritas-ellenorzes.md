# PicasaPy paritás-ellenőrzés — #4317

**Vizsgálati dátum:** 2026-10-06. **Hatókör:** a 2–4. réteg statikus QML-ellenőrzése; nem teljes kiadási paritásmérés.

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
| `ID_VIEW_TIMELINE` | **Megvan, de nem érhető el.** | A menüsori elem `PicasaMenuBar.qml:874–879`, a `Ctrl+5` gyorsbillentyű `Main.qml:1358–1362` állandóan tiltott. A komment szerint a teljes képernyős, animált eredeti helyett a jelenlegi megoldás még nem kész; meglévő #936 munka nyitott, új jegy helyett annak állapotát kell követni. |

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
| `Ctrl+5` | **Állandóan tiltott.** | `Main.qml:1358–1362` és `PicasaMenuBar.qml:874–879`. |
| `Ctrl+H` (tálca: kijelölés megtartása) | **Aktív, nézet- és fókuszkapuval.** | A `TrayBar.qml` `trayKeepSelectionShortcut` a főablak létezését, a néző bezárt állapotát, a tálcakijelölést és a szövegfókusz hiányát kéri. A #4398 előtti hiánymegállapítás elavult volt. |
| `F11`, `/`, `,`, `.` | Eredeti 48-rekeszes keymapben szerepelnek; aktív megfelelőjük a jelen QML-leltárban nem található. A videóvezérlő pontos billentyűhatása nyitott. | Eredeti tábla `picasa-gyorsbillentyuk.md` §2.5; aktuális QML-beli `sequence`/`Keys` leltár. Ne állítsuk kattintásos/valós idejű próba nélkül, hogy mindegyik fejlesztői hiány. |
| Helyi menü billentyűfeliratai | A Folder helyi menü megjeleníti a `Ctrl+A/D/I/Enter` címkéket; a Photo/Viewer a `Enter`, forgatás, `Ctrl+Shift+O`, mentés, keresés, törlés és `Alt+Enter` feliratokat. Az Album/People/Tray listák nem mind mutatják az eredeti gyorsbillentyű-szövegeket. | `FolderContextMenu.qml:89–259`, `PhotoContextMenu.qml:142–407`, `ViewerContextMenu.qml:100–240`, `TrayContextMenu.qml:45–95`, `AlbumContextMenu.qml:71–105`, `PeopleAlbumContextMenu.qml:37–45`. A menüfelirat és a fókuszban ténylegesen elsülő globális shortcut külön bizonyítandó. |

### Húzás és ejtés

| Eredeti / jelenlegi művelet | Eredmény | Bizonyíték |
|---|---|---|
| Képek húzása a Picasa rácsából kifelé, OS/Explorer célra | **Nyitott; kimenő paritás nincs igazolva.** | Az eredeti `ytDragNode` `DoDragDrop` útja: `picasa-eger-es-kijeloles.md` §5 és §14, `0x00aa1fb0`. A QML-leltárban a kép húzó proxy `Drag.active`-et és `payload="photos"`-t állít be, de nincs `Drag.mimeData`/URI-kimenet a `ThumbDelegate.qml:279–305`-ben. Asztali drag-próba nincs. |
| Fájl ejtése az alkalmazásra | **Kódút megvan; kattintás/desktop próba nincs.** | `ImportDropArea.qml:10–31` → `dropImportController.importDroppedUrls`; `Main.qml:3360–3364`; a vezérlő `drop_import_controller.py:92–…`. |
| Képek ejtése az albumlistára, albumra vagy képrácsra | **Belső QML-út megvan.** | `ThumbDelegate.qml:279–305`, `AlbumsSection.qml:89–96,176–183`, `LightboxFeed.qml:1019–1028`. Az albumcélok kezelői `FolderPane.qml:519–523`-nál folytatódnak. Valódi egérhúzás nem volt kipróbálva. |

## 4. réteg — állandóan tiltott és néma QML-vezérlők

Az ellenőrzés a QML-fájlokon végigkereste a `enabled: false` állandó értéket, valamint az üres vagy kizárólag naplózó `onClicked`, `onTriggered`, `onActivated` és hasonló blokkokat.

| Vezérlő | Státusz és forrás |
|---|---|
| Időrend és üres Upload almenü | `PicasaMenuBar.qml:874–879` (Timeline) és `:1891` (üres Upload) állandóan tiltott. Az Upload webes funkciója nem cél; az Időrend fejlesztése #936 alatt nyitott. |
| Általános beállítások | `OptionsTabGeneral.qml:64,70,76,264,289,322`: különleges felületi effektek, súgóbuborékok, egykattintásos szerkesztőkilépés, anonim statisztika, automatikus frissítés és importcélmappa vezérlői/területei tiltottak. |
| E-mail beállítások | `OptionsTabEmail.qml:81,175,181,188` és `EmailChoiceDialog.qml:141,277`: Google-/levélküldési szolgáltató opciók tiltottak. Ez nem cáfolja a kijelölés e-mail küldésének működő TrayBar-útját. |
| Mappa tulajdonságai | `FolderPropertiesDialog.qml:157–159`: diavetítés/film zene beállítása tiltott; a komment szerint nincs bekötve. |
| Import és webes műveletek | `ImportSourceDialog.qml:334,365`, `LightboxHeader.qml:271,597`, `TrayBar.qml:1724,1961,1978,1993`: upload/sync/Google Photos/rendelés/megosztás/blog műveletek tiltottak; a webszolgáltatás-vezérlőket nem szabad fejlesztési hiányként összeszámolni. |
| További teljesen tiltott beállításlapok | `OptionsTabNetwork.qml:11`, `OptionsTabFileTypes.qml:15`, `OptionsTabWebAlbums.qml:21`, továbbá `OptionsTabPrinting.qml:12`, `OptionsTabNameTags.qml:18`, `OptionsTabSlideshow.qml:13`. Az utóbbi három már #4318–#4320 alatt van; nem vettem fel őket új jegyjavaslatként. |
| Vizuális/segéd-elemek | `PhotoViewer.qml:4447`, `EditorPanel.qml:816,833`, `EditorFinetunePanel.qml:59` tiltásai látványréteghez vagy rejtett adat-vezérlőhöz tartoznak, nem kattintható funkciógombok. A `FolderPane.qml:851` `enabled:false` csak komment, nem futó tulajdonság. |

A statikus keresés **nem talált üres vagy csak `console.log/warn/error` hívásból álló eseménykezelőt** a keresett QML-kezelőtípusok között. Ez nem ellenőrzi a jelzések Python-oldali fogadóját; az ismert 12 bekötetlen vezérlőtag (#4316) és 30 néma művelet-jelzés (#4321) a hívó által megadott korábbi lelet, itt nem mértem újra.

## A #4317 „Kész, ha” pontjai

| Pont | Állapot | Indok |
|---|---|---|
| mind a hét réteg végigmérve, mai main | ⛔ | Ez a kör csak a 2–4. réteg forráskódját vizsgálta; a záró státusz a helyi `origin/main`-tól három commit lemaradást mutatott, és a hivatkozás frissessége nem ellenőrizhető. |
| minden hiány saját jegyet kapott vagy nem célként indokolt | ⛔ | A statikus hiányokra javaslatok lent vannak, de GitHub-hozzáférés nem volt, így nem ellenőriztem duplikált/nyitott jegyeket, és nem hoztam létre jegyet. Több eredeti parancs egyenértékűsége nyitott. |
| tiszta profil végigkattintása képernyőképekkel | ⛔ | Nem futtattam alkalmazást tiszta felhasználói profillal, nem kattintottam végig a fő funkciókat, és nem készítettem képernyőképet. A #4315-ös modell-elérhetőségi eset a hívó által megadott korábbi lelet. |

## Javasolt fejlesztői jegyek

Minden sor egy önálló funkció/menübelépő; a meglévő, hívó által megnevezett #4315, #4316, #4318–#4320, #4321 és a Timeline #936 nem ismétlődik.

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
| A Kép ▸ Show/Hide Text működjön a kijelölt képeken | Eredeti: `ID_PICTURE_SHOW_TEXT`, `ID_PICTURE_HIDE_TEXT`. Nálunk: mindkét menüpont helyfoglaló (`PicasaMenuBar.qml:1730–1731`). | A két parancs a kijelölt képek szövegfedvényét az eredeti állapotfeltételekkel kapcsolja. |
| A Nézet ▸ Show Edit Controls kapcsolja a szerkesztő vezérlőit | Eredeti: `ID_VIEW_EDIT`. Nálunk: `PicasaMenuBar.qml:852` helyfoglaló. | A menüpont láthatóvá/rejtetté teszi a szerkesztő kezelősávját és a kiválasztott állapot újranyitáskor következetes. |
| Folytassa vagy zárja le a 16 bites ditherelt megjelenítési mód munkáját | Eredeti: `ID_VIEW_16`, pontos képpont-átalakítása a `picasa-megjelenitesi-modok.md` §5.3-ban mérve. Nálunk: `PicasaMenuBar.qml:1015–1022` helyfoglaló; a QML-komment #1658-ra hivatkozik. | A #1658 meglévő jegy státuszát ellenőrizni; ha nyitott, a `ID_VIEW_16` alkalmazza a leírt ditherelést; ha nem cél, ezt indokoltan dokumentálni. |

Az alábbi #4339-es függelék pontosítja ezt a listát. A `Small Pictures` jelentése és az eredeti kimenő fájlhúzás bináris szerződése megvan; a People Albums bemeneti szabálya és a 44 gyorsbillentyű tényleges fókuszkapuja még nem zárható le.

## Új kutatási kérdések — állapot a #4339 után

| Kérdés | Állapot | Részletes spec |
|---|---|---|
| `ID_VIEW_SMALL`: melyik nézetben, milyen képméretet állít? | **Megválaszolva:** a CThumbUI könyvtári bélyegképnézetének szűrőkapcsolója; nem állít bélyegképméretet. A szűrő alap-területküszöbe 60 000 képpont². | `picasa-menu-parancsok-viselkedes.md`, „Kis képek” |
| `ID_FACESRANDOM`: mi a People Albums film bemenete, sorrendje és arcigazítása; azonos-e a mi fejlécútunkkal? | **A bemeneti lista/sorrend megválaszolva:** a 6-os mód a `+0x2bc` lista nem üres alsó listájú azonosítóit adja vissza, forrássorrendben. A klip belső arc-/crop-útja nyitott; a mi fejlécünk a normál filmútvonalat használja. | #4339 függelék, 2. táblázat; `picasa-create-features.md` §2.5 |
| Kimenő fájlhúzás: OLE-formátum, fájllista, műveletmaszk; reprodukálható-e? | **Bináris szerződés megválaszolva:** egy `CF_HDROP` UTF-16 útvonal-lista, `COPY|MOVE|LINK` engedett hatásokkal. A natív Qt/asztali fogadópróba nyitott. | #4339 függelék, 3. táblázat; `picasa-eger-es-kijeloles.md` §5.1 |
| Melyik nézetben/fókuszban él a 44 helyi menü-gyorsbillentyű? | **A feltevés pontosítva:** mind a kilenc menübirtokos és a `CThumbUI` billentyűkezelő feltételei ismertek; a helyi rekord billentyűmezője a menüfelirat része, a vizsgált építőút nem regisztrál gyorsítót. Nem mind a 44 rekord parancsának egyedi eseményútja. | #4339 függelék, 4. táblázat; `picasa-gyorsbillentyuk.md` §4.1, §6.1 |

## #4339 — négy paritáskérdés, záró bináris kör

**Vizsgálati dátum:** 2026-10-06. **Módszer:** helyi bináris-index, utasításszintű diszasszemblálás, a megadott Ghidra-kötegek célzott dekompilátumai és QML-forrás-olvasás. A mostani záró kör csak az érintett függvényeket ellenőrizte Capstone-nal; új teljes `.text`-pásztázás nem történt. A korábbi pásztázásnál a `paszta.memoria_kapu()` futott elsőként. A qemu-i386 harness célzott Glimmer-képműveleteket futtat, nem Windows menü-/OLE-interakciót; e négy úthoz nem alkalmazható. Nincs runtime-desktop-próba, becsült értéket nem használok.

### 1. `Small Pictures` — szűrő a könyvtári bélyegképnézetben

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `eMenuView::ID_VIEW_SMALL = 0x9cd8`; a `CThumbUI` Nézet menüjében épül (`0x005c90f0`, tétel `0x005c918f`). A `Preferences\Show only big images` értéke alapból `1`; a menü ezt fordítva pipázza. A `0x005c94e0` az értéket kapcsolja és újraépíti a bélyegképnézetet. Nincs méretválasztás. A szűrőfogyasztó `0x0065d010` `BigPictureThreshold` alapértéke `0xEA60` = **60 000**; a `0x0065f521` szélesség×magasság területet hasonlítja ehhez, további 3,0/0,33333 képarány- és 200 px ágakkal. | A Nézet menü `menuViewThumbnailsOnly` sora `checkable`, de `placeholder: true` és nincs aktív kezelő (`PicasaMenuBar.qml:885–890`). | A `Small Pictures` tétel láthatósági szűrőt kapcsoljon, ne `thumbSizePreset`-et. A megvalósítás a dokumentált 60 000 px² alapküszöböt, a két képarány-konstanst és a 200 px ellenőrző ágat használja; a további fájltípus-ágakat a `0x0065f3c6`–`0x0065f5a9` tartományhoz kell igazítani. |

### 2. `From People Albums…` filmparancs

| Eredeti | Nálunk | Teendő |
|---|---|---|
| `ID_FACESRANDOM = 0x9d5a`; a `0x0057cc7a` a `panel+0x4f1` módjelzőt állítja. A `0x00618050` mód 6-ot ad a `+0x4b4` objektum vtable 0. slotjának (`0x00618236`), majd az eredményt a `+0x4b8` mezőbe teszi. A `0x00699cd0` mód 6 esetén a `0x00824090`-nek nem nulla ágválasztót ad (`0x0069a308`–`0x0069a310`); a `0x00824090` ezért a `0x008226e0` ágat hívja, nem az album-kijelölés `0x008223e0` ágát (`0x008240e9`–`0x00824114`). A `0x008226e0` a `+0x2bc` (`+700`) objektum `0x00449a90`-nel kapott azonosítólistáját járja be, és csak azokat fűzi az eredménybe, amelyek alsó listája nem üres (`0x00822715`–`0x00822775`). A fűzés a bemeneti lista iterációs sorrendjében történik; rendező hívás vagy rendezési ág nem látszik. A `0x006175c0` a már kapott `+0x4b8` listát használó modell-újraépítő, nem listaépítő. A `0x00619010` a `+0x4bc` modell címét adja át a `0x00555a30`-nak; ebből a timeline klipjeinek belső arc-/crop-adatútja nem állapítható meg. | A #4633 „From People Albums...” menüpontja kijelölés nélkül a `Main.qml:openPeopleAlbumsMovie()` úton hívja a `personMovieSourceUrls()` slotot, majd a `CreateDialogs.openMovieForSources()`-t. A #4391 fejlécútja változatlanul `openPersonAlbumMovie()`-n át éri el ugyanezt a forráslistát, de megtartja a nyitott személyalbum-feltételt. A slot a nem üres albumok képeit a tárolt listában, rendezés nélkül fűzi össze; ezt a `test_emberek_album_film_menu_4633.py` és a `test_people_controller.py` fedi. | A bemeneti lista és sorrend megvalósult. A timeline klip arcazonosítását/cropját ne találgassuk; az adatút továbbra is #4400 nyitott vizsgálata. |

### 3. Kimenő fájlhúzás

| Eredeti | Nálunk | Teendő |
|---|---|---|
| A `ytDragNode` `0x00aa1fb0` metódusa egy `CF_HDROP` (`cfFormat=15`) adatobjektumot készít: `DROPFILES.pFiles=20`, `fWide=1`, a csomópontlistából származó UTF-16 fájlútvonalakkal. A `QueryGetData` (`0x00aa1e90`) ezt a formátumot/HGLOBAL-t ellenőrzi, az `EnumFormatEtc` (`0x00aa1ed0`) a tárolt formátumot adja. `DoDragDrop` `dwOKEffects=7`, azaz COPY/MOVE/LINK megengedett; a kiválasztott hatást a fogadó adja vissza. | `ThumbDelegate.qml:279–305` a belső `payload="photos"` jelölést és QML-húzásállapotot használ; `Drag.mimeData` vagy OS-fájl URL nincs. | Adjon át kijelölt fájlútvonalakat tartalmazó natív fájllistát, és tegye lehetővé az eredeti három engedett műveletet. A Windows CF_HDROP és a cél által választott művelet egyezését asztali próbán kell igazolni; a QML-forrás önmagában erre nem bizonyíték. |

### 4. A 44 helyi menü-gyorsbillentyű nézeti kontextusa

| Eredeti | Nálunk | Teendő |
|---|---|---|
| Kilenc építő hívja a `0x00a6aee0` tételépítőt, összesen 44 rekorddal; a birtokos nézeteket lásd a `picasa-gyorsbillentyuk.md` §4.1-ben. A 20 bájtos rekord `+0x04` mezője billentyűfeliratként kerül a menüszövegbe (`0x00a6aee0` → `0x00a6b250`); a `0x00a6ade0` csak a felirat összeállításához oldja fel a táblázat szerinti billentyűkódot, egyetlen közvetlen hívója a `0x00a6b250`. Ebben a helyi menüépítő/feliratláncban gyorsítóregisztráció nincs. A `CThumbUI` RTTI-s billentyűslotja a `0x005e6710`: fókuszált gyerek továbbítása után saját feltételekkel dolgozik. A `+0x332f != 0` ág a `0x00760970` kezelőre megy; ez keydownon Esc/nyilak/szóköz/számjegyek ágait kezeli. A szerkesztő `+`/`-` karakterei és Shift-váltása a 3–5. fül látható paneljéhez kötött (`0x005f95d0`, `0x005f9690`, `0x009e39b0`); az utóbbi a fókuszobjektum szülőláncában a `+0x20c` bájt hiányát követeli. Ez a CThumbUI fogadó feltételeit bizonyítja, de nem köti hozzá egyenként mind a 44 rekord parancsát. | A mostani QML-leltárban 53 `Shortcut` deklaráció van nyolc fájlban; több parancs `Main.qml`-szintű, miközben mások nézeti `Shortcut`-ot vagy `Keys`-kezelőt használnak. Például a `Ctrl+Delete` külön rács- és nézőkaput kap, a `Ctrl+H` csak kijelölt elemmel és a nézőn kívül aktív, az `Enter` a `LightboxFeed` `Keys.onPressed` ágában van, és a `Ctrl+C/X/V` megőrzi a szövegmező fókuszát (`picasa-gyorsbillentyuk.md` §6.1). | A billentyűparitást nézethez/fókuszhoz kötött fogadókon valósítsuk meg: ne tekintsük a 44 helyi menü feliratmezőjét önmagában gyorsítóregisztrációnak. A QML-út minden parancsánál legyen meghatározva a tulajdonos nézet, a fókuszkapu és az eseményfogadó; az eredetiben bizonyított CThumbUI-feltételeket (3–5. szerkesztőfül, `+0x332f` módág, fókuszolt gyerek továbbítása, `+0x20c`-mentes ősút) ne általánosítsuk a többi nyolc menüépítőre. Elfogadás: az egyes menük kontextusából indított kombinációk a megfelelő nézet műveletét érik el, a fókuszált szövegmezők szerkesztése megmarad, és a 44 rekordot nem globális shortcut-listaként kezeljük. |

## Nyitott

- A kattintással és tiszta profillal ellenőrizendő hatások: minden menüút valós UI-viselkedése; külső szerkesztő, e-mail, nyomtató, Google Earth, fájltörlés/export; a 44 helyi menürekord és az eseményfogadók futásidejű parancs-kapcsolata.
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
| `ID_FACESRANDOM = 0x9d5a`, `panel+0x4f1`, `facemakemovieres` alap 3 / 1024×768 | bináris (`0x0057cc72`, `0x00616b42`–`0x00616b64`) |
| `ID_FACESRANDOM` módja: a `+0x4b4` objektum 0. helye 6-tal tér vissza a `+0x4b8` mezőbe | bináris (`0x00618050`: `0x00618209`–`0x0061824d`; Ghidra `00699cd0.c`) |
| a `+0x4b4` szolgáltatás 0. slotja módválasztó (`+0x14` rész, `0x00699cd0`); a `+0x1c` rész slotja destruktor (`0x0069d740` → `0x006996d0`) | bináris (Ghidra `00699cd0.c`, `0069d740.c`, `006996d0.c`; RTTI vtable `0x00ca7b7c`, `0x00ca7bd8`) |
| mód 6 ágválasztója: album-alapú `0x008223e0` helyett a `+0x2bc` listaág, `0x008226e0` fut | bináris (Capstone `0x0069a305`–`0x0069a310`, `0x008240e9`–`0x00824114`) |
| a `+0x2bc` listából csak nem üres alsó listájú azonosítók kerülnek át, a forrás sorrendjében | bináris (`0x008226e0`: Capstone `0x00822715`–`0x00822775`, `0x008229f0`–`0x008229fb`; Ghidra `008226e0.c`); **feltételes**, mert a szűrést/sorrendet egyetlen listabejáró függvény bizonyítja
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

- **Small Pictures — egyezik.** A: `0x005c90f0` menüépítő + `0x005c94e0` állapotkapcsoló (`Show only big images`, fordított pipa). B: `0x0065d010` külön képszűrő ugyanazt a beállítást olvassa, majd terület-, képarány- és méretágat alkalmaz. A beállítás kapcsoló, nem méretválasztó.
- **Fájlhúzás — egyezik.** A: `0x00aa1fb0` `CF_HDROP`/UTF-16 payloadot és 7-es hatásmaszkot készít. B: a `ytSimpleDataObject` `EnumFormatEtc`/`QueryGetData` útja a 15-ös formátumot szolgálja ki, más formatet nem fogad el.
- **People Albums film — a mód 6 ága megerősített két külön függvényrétegből; a szűrés/sorrend feltételes.** A: `0x0057cc7a` beállítja a `+0x4f1` jelzőt, `0x00618050` pedig 6-os módot kér. B: a külön `0x00699cd0` módválasztó a 6-ost az `0x00824090` ágválasztóján át a `0x008226e0`-re irányítja, nem az album-kijelölés `0x008223e0` ágára. A bemeneti forrás (`+0x2bc`), az üres alsó listák szűrése és a sorrend az `0x008226e0` bejárásából következik; ez egyetlen kódszintű út, ezért `feltételes`, noha Capstone és a Ghidra-dekompilátum utasításonként egyezik. A `0x00619010`/`0x00555a30` külön fogyasztói útján a modell címe megy át, a közvetlen modellolvasás pedig a `+0x2b0` hangfájlnévre korlátozódik; arc/crop mezőt nem azonosít. A CTransTimeline belseje nyitott.
- **Gyorsbillentyűk — a menüfelirat és a CThumbUI eseményút megerősített; az egyedi parancs-kapcsolat korlátozott.** A: a `0x00a6aee0` → `0x00a6b250` lánc a rekord `+0x04` mezőjét szövegként építi a menübe, a `0x00a6ade0` pedig ezt a felirat-építő hívó keresi fel. B: a `CThumbUI` RTTI-s billentyűslotja `0x005e6710`; ennek diszasszemblálása és a külön dekompilált `0x005f95d0`, `0x005f9690`, `0x00760970`, `0x009e39b0` függvények rögzítik a mód-/fókuszfeltételeket. A két út a „felirat nem azonos a regisztrációval” következtetéssel egyezik. A lehetséges globális gyorsító-importok cáfoló ellenőrzése miatt ezt nem terjesztem ki a teljes programra; a 44 rekord és más gyorsító-API-k kapcsolata **NINCS MEG**.

## Cáfoló kísérlet

1. Azt próbáltam cáfolni, hogy `ID_VIEW_SMALL` bélyegképméretet állít: összevetettem a `0x9cd8` és `0x9c9d` külön parancsait, az `ID_VIEW_SMALL` menüépítőjét/íróját, valamint a külön képszűrő fogyasztót. A `0x9cd8` csak a `Show only big images` preferenciát váltja; a méret-presetek külön parancsok.
2. Azt próbáltam cáfolni, hogy a drag adatobjektum csak CF_HDROP-ot fogad el: `QueryGetData`-nél alternatív formátumot vizsgáltam. A kód csak `cfFormat=15`, `DVASPECT_CONTENT` és HGLOBAL mellett tér vissza sikerrel; alternatív URI-/egyedi formátumot nem igazol.
3. Azt próbáltam cáfolni, hogy a `0x006175c0` építi a People-képlistát, illetve a `0x0080fea0` végzi az arc-kivágást. A Ghidra-kód szerint a `0x006175c0` a `+0x4bc` modellt újraépíti és a már kapott `+0x4b8` listát iterálja; a `0x0080fea0` modellmezőket ír és node-okat inicializál. A lista-lekérési határ a `0x00618050`-ban van (`0x00618236`), de a virtuális cél és a render-crop út nyitott.
4. **People-mód cáfoló köre:** azt ellenőriztem, hogy a 6-os mód vajon a kiválasztott album `0x008223e0` ágába jut-e. A Capstone-utasítások szerint a 6-os mód a `0x0069a30b` `sete cl`-nél 1-es jelzőt ad; a `0x008240e9` feltétel így a `0x008226e0` ágra visz, míg az album-alapú `0x008223e0` csak nulla jelzőnél fut. A cáfolat saját ellenőrzése: a `0x008226e0` `0x00822715`-nél valóban a `+0x2bc` listát kéri, és a `0x0082275f`–`0x00822775` csak üresnek talált alsó listánál ugrik ki; a `0x008229f0` iterációs indexe növekszik, kódolt rendezés nélkül. A korábbi „kiválasztott album” értelmezés mód 6-ra megdőlt; az a másik, nulla-jelzős ág.
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
| A Nézet ▸ Small Pictures kapcsolja a kis képek szűrőjét | Eredeti: `0x9cd8`, preferencia-kapcsoló, 60 000 px² alapküszöb és további ellenőrzések. Nálunk: `PicasaMenuBar.qml:885–890` helyfoglaló. Teendő: a tétel a szűrőt kapcsolja, ne bélyegképméretet. | A pipa és a látható képek a specifikált preferenciával és `0x0065f3c6`–`0x0065f5a9` szabályokkal egyeznek; a bélyegképméret nem változik. |
| A képrács húzza a kijelölt fájlokat az asztali alkalmazásokba | Eredeti: `CF_HDROP`, UTF-16 útvonalak, COPY/MOVE/LINK. Nálunk: belső `payload="photos"`, OS-formátum nincs. Teendő: natív fájllista átadása. | Windows-próbán a fogadó a húzott fájlok útvonalait kapja, és az eredeti 3 engedett műveletből választott hatás visszajelzése helyes. |
| Az Emberek-fejléc filmgombjai őrizzék az eredeti People/Face bemenetet | Eredeti: mód 6 a `+0x2bc` azonosítólistáját járja be, üres alsó listákat kihagy, sorrendet őriz (`0x00699cd0`, `0x00824090`, `0x008226e0`). Nálunk: `Main.qml:732–737` minden `controller.photos` sort a normál filmútvonalnak ad. Teendő: a bizonyított szűrt lista és sorrend bekötése külön People/Face útba; a timeline/crop belső útját ne találgassuk. | Az eredetivel azonos bemeneti modellen a forrás-azonosítók és sorrend egyeznek; crop/arcigazítás csak `CTransTimeline` feltárása után vehető át. |
| A 44 menüfelirat és a billentyűkezelés nézet-/fókuszhelyes legyen | Eredeti: a rekord `+0x04` mezője felirat (`0x00a6aee0`, `0x00a6b250`); a `CThumbUI` saját billentyűútja `0x005e6710`, a szerkesztőfülek és a `+0x332f` ág bizonyított feltételeivel. Nálunk: a #4398 utáni leltár 54 `Shortcut` nyolc QML-fájlban, köztük rács/néző szerint külön `Ctrl+Delete`; könyvtári kötéseket nem enged be az editorba, és szövegfókuszban tiltja az alkalmazás-shortcutokat. Teendő: a helyi menüfeliratokat ne tekintsük globális shortcut-regisztrációnak; a 44 rekord egyedi parancsútja továbbra sincs bizonyítva. | A gazdanézet/fókuszkapuk a `picasa-gyorsbillentyuk.md` §6.2 táblázatában vannak; a könyvtár/editor/szövegfókusz eseteket valódi billentyűleütéses teszt fedi le; a nem igazolt 44/44 kapcsolat nyitott marad. |

## Új kutatási jegyjavaslatok

Nincs külön új kutatási jegyjavaslat: a fennmaradó `CTransTimeline` kérdés a #4339 blokkoló folytatása; a gyorsító-API-kapcsolat és az asztali drag-próba is ugyanennek a paritási vizsgálatnak a határán marad.

## Nyitott — pontos következő bináris lépés

- `Ghidra-kör kell: 0x00555a30 — a 0x00619010 által átadott +0x4bc film-modell címét a CTransTimeline hogyan dolgozza fel: melyik mező hordozza az arcazonosítót/cropot/arcra igazítást, és hogyan kerül ezekből adat a timeline-klipbe? [blokkoló]`
- A `+0x332f` bájt által jelölt billentyűmód neve **NINCS MEG**; a `0x00760970` ág feltételei és a kezelt billentyűk ismertek, a mód szemantikája nem.
- A `CreateAcceleratorTableA` / `TranslateAcceleratorA` importok és a 44 helyi menürekord közötti kapcsolat **NINCS MEG**; ezért a gyorsító-regisztráció hiánya csak a vizsgált `0x00a6aee0` → `0x00a6b250` helyi menüépítő-láncra állítható.
- A fájlhúzás natív QML/Windows egyezése: **NINCS MEG** futó Windows-célalkalmazással végzett próbában.

## Módosított fájlok

**A 2026-10-06-i záró körben:**

- `docs/specs/paritas-ellenorzes.md` — a People mód 6 bemeneti listája/sorrendje, a `CThumbUI` fókuszkapui, a cáfoló ellenőrzések és a `CTransTimeline` blokkoló kérdése.
- `docs/specs/picasa-create-features.md` — a 6-os ág pontos forráslistája, szűrése és sorrendje; a modell/crop határának nyitva hagyása.
- `docs/specs/picasa-gyorsbillentyuk.md` — a helyi menümező feliratjellege, a `CThumbUI` eseményfeltételei és a mai QML 53 `Shortcut`-os összevetése.
- `docs/specs/00-index.md` — a #4339 kutatási állapot rövid összefoglalójának frissítése.

**A korábbi #4339-körök módosításai:**

- `docs/specs/paritas-ellenorzes.md` — a #4339 négy kérdése, eredeti/nálunk/teendő táblái, bizonyítékai és nyitott bináris lépései.
- `docs/specs/picasa-menu-parancsok-viselkedes.md` — `ID_VIEW_SMALL` helyesbítése és a küszöb pontosítása.
- `docs/specs/picasa-create-features.md` — az `ID_FACESRANDOM` módjelzője és felbontása; nyitott bemeneti szabály.
- `docs/specs/picasa-eger-es-kijeloles.md` — a `DoDragDrop` fájlformátuma, payloadja és hatásmaszkja.
- `docs/specs/picasa-gyorsbillentyuk.md` — a 44 rekord kilenc menükontextusa és a nyitva maradt fókuszkapu.
