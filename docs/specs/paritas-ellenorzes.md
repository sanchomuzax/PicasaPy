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

## 4. réteg: néma gombok (2026-10-17)

**Módszer.** A `scripts/check_silent_qml_controls.py --list` a mai munkafán 32 jelöltet adott: 27 `enabled: false` kötést és 5 fogadó nélküli QML-jelzést. Külön, kiterjesztett keresés vizsgálta a `Clicked`, `Triggered`, `Toggled`, `Pressed`, `Released`, `DoubleClicked`, `Entered`, `Exited`, `PositionChanged`, `Wheel`, `Dropped`, `Accepted` és `Canceled` eseményeket; üres vagy csak `console.log` hívást tartalmazó kezelő nem volt. Két további kezelő csak a saját dialógusát zárja be. A szülő `enabled` állapotát a proxy- és Web Albums-csoportnál a gyerekekre is végigkövettem. Az eredeti viselkedést a hivatkozott spec-lapok és a `ui-lefedettseg-elemek.csv` alapján adom meg; ha nincs leírva, a táblázat ezt kimondja.

Lefutott a három megadott mérő. A `nema_slotok.py` 920 `@Slot`/`@Property` tagból kettőt jelölt: `setAutoPlayMovies` és `setEnableHover`. Mindkét találat téves, mert a `@Slot` csak kommentben szerepel; a QML a két tulajdonságot olvassa. A `nema_jelzesek.py` 278 jelzésből 108 property-értesítőt és 170 akció-jelzést talált, gazdátlan akció-jelzést nem. A `nema_beallitasok.py` két gyanút jelzett: `mail/useDefaultClient` és `mail/EmailAutocomplete`; az első a levélválasztó kezdőpaneljét állítja, a második a jelölő állapotát menti, de a címjavaslatot nem állítja elő. Nyolc kulcsot nem tudott közvetlenül követni: a két régi e-mail-méretindex migrációs tartalék, a hat képernyővédő-kulcs olvasója és írója viszont a `screensaver_controller.py` és a `ScreensaverDialog.qml` között végigkövethető. Ezek a mérő vakfoltjai, nem negatív eredmények.

Az ellenőrzés statikus forrásvizsgálat. A CI-őr csak a `Clicked` és `Triggered` eseményeket, a közvetlen `enabled: false` értéket és a QML-jelzés-fogadókat keresi. A bővített eseménykeresés nem futtatja a felületet, a dinamikus `enabled` feltételek elérhetőségét pedig nem méri végig minden állapottal. A `nema_slotok.py` a kommentben szereplő `@Slot` szöveget is találatnak veszi; a `nema_beallitasok.py` nem tudja követni a szótárba olvasott értékeket. A forráslánc ezért nem helyettesíti a kattintásos próbát.

**Szúrópróba, teljes hívási lánc.** A Ctrl+5 útja: letiltott `Main.qml` `Shortcut` → `toggleTimeline()`. Az Időrend menü útja: letiltott `MenuItem` → `timelineRequested`, amelynek nincs fogadója. Az e-mail-mód útja: QSettings → `EmailController.useDefaultClient` → Beállítások rádiógombjai → `EmailChoiceDialog.onOpened`, ahol az érték a `compose` vagy `choose` panelt választja; tehát a beállítás nem néma. Az Auto-Complete útja: helyi menüelem → mentő slot → QSettings. A bináris lelet szerint az eredeti kapcsolónak sincs olvasója; a címjavasló osztály a Gmail-ágú levélszerkesztő része. A „Don't Set” útja: `collageFormatDontSetButton` → `formatRejected()` → figyelmeztetés bezárása; a folytató művelet hiánya megfelel a gomb jelentésének. A Crop útja: `editToolCrop` → `toolActivated`/`cropActive` → a vágópanel megjelenik; a külön `cropRequested` jelzés fölösleges. A teljes statikus láncok alapján az első két út nem érhető el, a másik négy a feladatuk szerint működik.

| Elem, objectName és felirat | Fájl:sor | Gyanú | Eredeti viselkedés és forrása | Ítélet |
|---|---|---|---|---|
| Ctrl+5 `Shortcut`; objectName nincs; felirat `Ctrl+5` | `Main.qml:1724-1726` | A gyorsbillentyű állandóan tiltott, noha a `toggleTimeline()` függvény létezik. | A Ctrl+5 az Időrend teljes képernyős nézetét indítja; [picasa-gyorsbillentyuk.md 10.6](picasa-gyorsbillentyuk.md), [picasa-menu-parancsok-viselkedes.md 38.2](picasa-menu-parancsok-viselkedes.md). | néma |
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
| Automatikus frissítés `objectName=optionsUpdateModeCombo`; qsTr: `Automatic updates:` | `OptionsTabGeneral.qml:360` | Az automatikus frissítés kapcsolója le van tiltva. | Eredeti frissítés-ellenőrzés, Windowsra kötve; [picasa-fen-dialogs.md 3.11](picasa-fen-dialogs.md), [pmp-database.md](pmp-database.md). A külső frissítési szolgáltatás nem cél. | nem cél |
| Google Contacts-fényképfeltöltés `objectName=optionsFaceUploadContactPhotosCheck`; qsTr: `Upload people album thumbnails to Google Contacts` | `OptionsTabNameTags.qml:234` | A feltöltési jelölőnégyzet le van tiltva. | Az eredeti névjegykép-feltöltés külső Google Contacts-integráció; [picasa-fen-dialogs.md 4.1](picasa-fen-dialogs.md). Nem cél. | nem cél |
| Proxycsoport: `optionsNetworkProxyUserField`, `optionsNetworkProxyPasswordField`, `optionsNetworkAutoDetectCheck`; feliratok: `Proxy username (Windows only):`, `Proxy password:`, `Automatically detect network settings` | `OptionsTabNetwork.qml:18` | A szülő csoport tiltott, ezért a három gyerekmező sem aktív. | Eredeti options.fen proxybeállításai; a PicasaPy nem használ proxyt, ezt a QML kódbeli megjegyzése is rögzíti. A hálózati naplózás külön, aktív vezérlő. | nem cél |
| Web Albums beállításcsoport: `optionsWebUploadSizeCombo`, `optionsWebStripedUploadCheck`, `optionsWebKeepJpegQualityCheck`, `optionsWebStarredOnlyCheck`, `optionsWebConfirmSyncDisableCheck`; feliratok: feltöltési méret, előnézet előbb, eredeti minőség, csillagozottak, szinkronmegerősítés | `OptionsTabWebAlbums.qml:21` | A teljes fül gyökere tiltott, ezért minden gyerekvezérlő tiltott. | Picasa Web Albums-feltöltés és szinkron; a szolgáltatás megszűnt, [picasa-fen-dialogs.md 3.11](picasa-fen-dialogs.md), [ui-lefedettseg.md](ui-lefedettseg.md). | nem cél |
| Arc-címkék webszinkronja `objectName=peopleManagerSyncCheck`; qsTr: `Sync Face Tags with Web Albums` | `PeopleManagerDialog.qml:485` | A jelölőnégyzet le van tiltva. | Arc-címkék szinkronja Picasa Web Albumsba; a szolgáltatás megszűnt, [picasa-arcfelismeres.md](picasa-arcfelismeres.md). | nem cél |
| Online kapcsolatok kezelése `objectName=peopleManagerOnlineButton`; qsTr: `Manage Online Contacts` | `PeopleManagerDialog.qml:514` | A gomb le van tiltva. | Google Contacts-fiók kezeléséhez tartozik; [picasa-fen-dialogs.md 4.1](picasa-fen-dialogs.md). Külső kapcsolat nem cél. | nem cél |
| Online kapcsolatok frissítése `objectName=peopleManagerRefreshButton`; qsTr: `Refresh Contacts` | `PeopleManagerDialog.qml:519` | A gomb le van tiltva. | Google Contacts-letöltés; [picasa-menu-parancsok-viselkedes.md 24.4](picasa-menu-parancsok-viselkedes.md). Külső kapcsolat nem cél. | nem cél |
| Modális elmosás `objectName=editorModalDialogBlur`; qsTr-felirat nincs | `PhotoViewer.qml:5250` | Inputot nem fogadó `Rectangle` tiltott. | NINCS LEÍRVA; a Qt modális párbeszéde kezeli a bemeneti fókuszt, ez csak látványréteg. | nem cél |
| Nézet menü Időrend `objectName=menuViewTimeline`; qsTr: `Ti&meline`, gyorsbillentyű-felirat `Ctrl+5` | `PicasaMenuBar.qml:1160-1163` | Állandóan tiltott, bár `onTriggered` jelet bocsát ki. | Az eredeti Időrend nézete a CThumbUI időrendi teljes képernyős útja; [picasa-menu-parancsok-viselkedes.md 38.2](picasa-menu-parancsok-viselkedes.md). | néma |
| Upload menü `title=U&pload`; objectName nincs | `PicasaMenuBar.qml:2416` | A teljes menü tiltott. | Feltöltési parancsok a Picasa Web Albums szolgáltatásához tartoznak; [picasa-menu-leltar.md](picasa-menu-leltar.md). A szolgáltatás megszűnt. | nem cél |
| Google Photos feltöltés `objectName=trayUploadButton`; qsTr: `Upload to Google Photos` | `TrayBar.qml:1852` | Feltöltésgomb állandóan tiltott. | Külső Google Photos-feltöltő; a PicasaPy nem célozza az online feltöltést, [picasa-keptalca.md](picasa-keptalca.md). | nem cél |
| Nyomat rendelése `objectName=trayOrderButton`; ToolTip: `Order Prints (service discontinued)` | `TrayBar.qml:2118` | Külső rendelésgomb tiltott. | Az eredeti nyomat-rendelő partner megszűnt; [ui-lefedettseg-elemek.csv:436](ui-lefedettseg-elemek.csv), [picasa-keptalca.md](picasa-keptalca.md). | nem cél |
| Hello megosztás `objectName=trayShareButton`; qsTr-felirat nincs | `TrayBar.qml:2135` | Nincs aktív backend. | Az eredeti Hello-megosztás online szolgáltatásához nem tartozik működő backend; [ui-lefedettseg-elemek.csv:170](ui-lefedettseg-elemek.csv). | nem cél |
| Blogger `objectName=trayBlogButton`; ToolTip: `Publish to Blogger (service discontinued)` | `TrayBar.qml:2150` | Külső publikálásgomb tiltott. | A Blogger-integráció megszűnt; [ui-lefedettseg-elemek.csv:437](ui-lefedettseg-elemek.csv), [picasa-keptalca.md](picasa-keptalca.md). | nem cél |
| „Don't Set” gomb `objectName=collageFormatDontSetButton`; qsTr: `Don't Set`; kibocsátja a `formatRejected` jelzést | `CollageDialogs.qml:38,190-196` | A QML-jelzésnek nincs fogadója. | NINCS LEÍRVA külön eredeti vezérlőként. A gomb elutasítja a formátummódosítást és bezárja a figyelmeztetést; a folytató művelet hiánya megfelel a feliratnak. | működik |
| Dokumentumfül aktiválása `signal tabActivated`; delegált fül neve `documentTab` prefix, a cím dinamikus | `DocumentTabStrip.qml:70,87-90` | A jelzésnek nincs fogadója. | Az eredeti kollázs önálló fül a könyvtár mellett; [kollazs-panel-ui-spec.md 3.1-3.3](kollazs-panel-ui-spec.md). A `activeTabId` közvetlenül köti a tartalom láthatóságát. | működik |
| Crop eszköz `objectName=editToolCrop`; qsTr: `Crop`; `cropRequested` jelzés | `EditorPanel.qml:452`; eszköz: `EditorTabCommonFixes.qml:91-98` | A külön jelzésnek nincs fogadója. | Az eredeti Crop eszköz megnyitja a vágó panelt; [ui-audit-editor.md](ui-audit-editor.md). A működő `toolActivated` és `cropActive` út nyitja meg. | működik |
| Időrend menüjelzés `timelineRequested`; objectName és qsTr-felirat nincs | `PicasaMenuBar.qml:492` | A QML-jelzésnek nincs fogadója. | Az eredeti Időrend útja a fenti menüsorban hivatkozott; a mai menü és Ctrl+5 kapuja tiltott, a Main oldalon nincs jelzésfogadó. | néma |
| Fotóhúzás-kiegészítő jelzés `photoDragStarted`; objectName és qsTr-felirat nincs | `ThumbDelegate.qml:72,310-314` | A jelzésnek nincs fogadója. | Az eredeti képhúzás leírása: [picasa-eger-es-kijeloles.md 5. és 14. szakasz](picasa-eger-es-kijeloles.md). A belső húzást a `Drag.active` indítja; az OS felé menő fájlhúzás külön nyitott réteg. | működik |
| Hibaablak OK `objectName=passportErrorOkButton`; qsTr: `OK` | `PassportErrorDialog.qml:66` | A kezelő csak a saját dialógust zárja be. | NINCS LEÍRVA a lefedettségi CSV-ben vagy a kapcsolódó specben. A gomb célja az üzenet bezárása, a hívási út működik. | működik |
| Kulcsszóablak Done `objectName=keywordDoneButton`; qsTr: `Done` | `KeywordsDialog.qml:225` | A kezelő csak a saját dialógust zárja be. | NINCS LEÍRVA külön eredeti gombként. A kulcsszómódosító vezérlők után ez zárja a párbeszédet. | működik |
| Videó-automatikus lejátszás beállítója `setAutoPlayMovies`; objectName és qsTr-felirat nincs | `appearance_controller.py:182` | A slotmérő találta, mert a szomszédos komment `@Slot` szöveget tartalmaz. A metódus nincs dekorálva, a QML a `autoPlayMovies` tulajdonságot olvassa. | Az eredeti AutoPlayMovies videónyitáskor szabályozza az automatikus lejátszást; [ui-audit-editor.md](ui-audit-editor.md), a mai olvasó a `VideoPlayerView.qml:21-24`. | működik |
| Hover-előnézet beállítója `setEnableHover`; objectName és qsTr-felirat nincs | `appearance_controller.py:198` | A slotmérő találta, mert a szomszédos komment `@Slot` szöveget tartalmaz. A metódus nincs dekorálva, a QML az `enableHover` tulajdonságot olvassa. | Az eredeti EnableHover a Ctrl+Alt előnézetet szabályozza; [picasa-gyorsbillentyuk.md 10.33](picasa-gyorsbillentyuk.md), a mai olvasó a `LightboxFeed.qml:124-125`. | működik |
| E-mail mód rádiócsoport `objectName=optionsMailDefaultRadio`, `optionsMailChooseRadio`; qsTr: `Use this computer's default email program`, `Let me choose each time I send pictures` | `OptionsTabEmail.qml:54-76` | A beállításmérő csak tárolt tulajdonságot látott. | Az eredeti EmailPrepType levelezőmódot választ; [picasa-email-kuldes.md 5. szakasz](picasa-email-kuldes.md). A mai `EmailChoiceDialog.qml:35-40` a beállításból `compose` vagy `choose` kezdőlapot választ; a küldő mindkét esetben az alapértelmezett programot hívja, a Gmail-ág nem cél. | működik |
| Képernyővédő forrásai és kijelölt képei; `objectName=screensaverSourceList`, ismétlődő `screensaverSourceCheck<n>`; feliratok: `Display photos from:`, `Selected Pictures`, illetve a mappa- és albumnevek | `ScreensaverDialog.qml:29-37,109-138`; `screensaver_controller.py:215-251,288-305` | A mérő nem tudta követni a `screensaver/sources` és `screensaver/photoPaths` kulcsokat. | Az eredeti képernyővédőhöz adott képekről a [picasa-menu-parancsok-viselkedes.md 35.3](picasa-menu-parancsok-viselkedes.md) ír; a Linuxos helyi forráslista pontos eredeti megfelelője NINCS LEÍRVA. | működik |
| Képernyővédő `effect`, `seconds`, `showCaptions`; `objectName=screensaverEffectBox`, `screensaverSecondsSlider`, `screensaverCaptionCheck`; feliratok: `Visual effect:`, `Change pictures every:`, `Show captions` | `ScreensaverDialog.qml:150-201`; `screensaver_controller.py:253-286` | A beállításmérő nem találta meg a kulcsok használatát. | Az eredeti Google Photos-képernyővédő külön program volt; a Linuxos helyi beállításmezők pontos eredeti megfelelője NINCS LEÍRVA. [picasa-menu-parancsok-viselkedes.md 35.3](picasa-menu-parancsok-viselkedes.md) leírja a mai helyi képernyővédő adaptációját. | működik |
| Képernyővédő tétlenségi percei; `objectName=screensaverIdleCheck`, `screensaverIdleMinutes`; feliratok: `Start when the computer is idle for`, `minutes` | `ScreensaverDialog.qml:204-244`; `screensaver_controller.py:363-407` | A mérő nem tudta követni a `screensaver/idleMinutes` kulcsot. | Az eredeti képernyővédő Windowsos külön program volt; a Linuxos tétlenségi indítás mai adaptáció. [picasa-menu-parancsok-viselkedes.md 35.3](picasa-menu-parancsok-viselkedes.md). | működik |
| E-mail-méretek migrációja; külön vezérlőnév és felirat nincs, a mai vezérlők: `optionsMailSizeSlider`, `optionsMailSingleSameRadio`, `optionsMailSingleOriginalRadio` | `email_controller.py:255-300`; mezők: `OptionsTabEmail.qml:136-215` | A mérő nem találta a `mail/multiSizeIndex` és `mail/singleSizeIndex` kulcsok olvasóját. | A két kulcs korábbi PicasaPy-formátum, a betöltés a mai képpontméretre és egyképes méretmódra migrál; nem eredeti Picasa-vezérlők. Az eredeti e-mail-méret viselkedése: [picasa-email-kuldes.md 3. szakasz](picasa-email-kuldes.md). | működik |
| Címzett Auto-Complete `objectName=textMenuAutoComplete`; qsTr: `Auto-Complete` | `TextFieldContextMenu.qml:88-104`; mező: `EmailChoiceDialog.qml:305-317` | A mérő nem találta a beállítás olvasóját; a QML a pipát menti és rajzolja, javaslómodellt nem találtam. | Az eredeti `Preferences\EmailAutocomplete` kapcsolónak nincs olvasója, csak a pipa állapotát tárolja; a címjavasló a Gmail-ágú levélszerkesztő része, ami nem cél. [picasa-menu-parancsok-viselkedes.md 24.2, 24.6, 57.1-57.2](picasa-menu-parancsok-viselkedes.md). | működik |

Az egyértelmű néma vagy nem elérhető fejlesztési tételek ebben a mintában az Időrend három belépési pontja és az Outlook-only levélbeállítás. A megszűnt online szolgáltatások és a nem interaktív segédrétegek nem hiányzó termékfunkcióként vannak számolva. A dinamikus `enabled` kötések teljes futásidejű elérhetősége és a valódi kattintásos próba nyitott marad.

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
| #1721 | Kézi sorrend tárolása | `docs/specs/album-sorrend.md` 2.3, 2.5 és 3. szakasz; `wordhash.dat`, `0x00784100`. | `src/picasapy/ini/priority.py:1-13,33-72`; a PicasaPy a kép `.picasa.ini` szakaszába ír `priority=` értéket. | **Eltér.** Az eredeti a mappa vagy album képlistáját a `wordhash.dat` fájlban tárolja. A `priority=` a PicasaPy saját kiterjesztése. Javaslat a #5186-ba: nevezze ezt saját formátumú funkciónak; eredeti sorrend átvétele külön, `wordhash.dat` importot vizsgáló feladat legyen. |
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
| #3756 | Kijelölt jelvény és feliratsáv kettős nézetben | `ui-audit-editor.md:2264-2272`, Colab EN 33-35. A képek a bal és jobb fókuszt, valamint az álló elrendezést mutatják. | `PhotoViewer.qml:446-448,4178-4257,4633-4636` | **Egyezik.** A jelvény a fókuszált képhez igazodik. A felirat a kijelölt sorból olvas. Javaslat a #5186-ba: a két javítást a jelenlegi QML alapján lezárhatja. |
| #3773 | AB nézet sorrendje és elsőként kijelölt oldala | Colab EN 33 (`kepek-leltar.md:109`), `ui-audit-editor.md:2267-2272`; a kép már AB állapotot mutat, az átváltás előtti kiválasztott képet nem rögzíti. | `PhotoViewer.qml:413-427,589-603,618-624,2683-2699` | **Forrás nem található** az AB módba lépés pillanatáról. A mai kód balra teszi a `currentIndex` képét, és bal fókuszt állít. Döntő Colab-felvétel: ismert kijelölt képpel indulni egyképes nézetben, AB-re váltani, kattintás előtt rögzíteni mindkét képet és a jelvényt. |
| #3826 | Fókuszos FF Sugár csúszkájának tartománya és alapértéke | `filterdesc-registry.md:156`, `filters-decoded.md:2372-2448`, bináris paramétermezők `0x008f86c8` és `0x008f86d1`; arcfelismerő nélküli 684-es golden-mérés. | `effect_params.py:170-180` | **Egyezik.** A `radius` tartománya -1 és 1, alapértéke 0. A szomszédos élesség 0 és 1 közötti. Javaslat a #5186-ba: lezárható. |
| #3998 | EXIF-bélyegkép az exportált JPEG-ben | `picasa-metaadat-tulajdonsagok.md:2107-2189`; bináris címek `0x009ece70-0x009ece8c`, `0x009b4aa0`, `0x009ecfb8`, `0x009ecdd2`; 186 export méret- és JPEG-mérése. | `exif_belyegkep.py:29-45,100-102`, `export_metadata.py:27-34` | **Eltér egy ritka hibás ágban.** A küszöb, méretezés, Lanczos-3 és q85 egyezik. Ha az APP1 blokk q10 mellett sem fér el, az eredeti az egész EXIF-et eldobja, a PicasaPy a bélyegképet hagyja el és megtartja a többi EXIF-adatot. Javaslat a #5186-ba: ezt nevezze meg tudatos eltérésként; a normál exportút egyezik. |
| #4013 | Crop kulcs egységes kezelése a nézőben, a bélyegképben és az exportban | `filters-decoded.md:16-27,45-70`; az eredeti Picasa exportmérése 1600 x 1200-as kimenetet adott `crop=` nélkül maradt `crop64` mellett. Az eredeti néző és bélyegkép viselkedése nincs megmérve. | `render/chain.py:94`, `edit_controller.py:1182`, `effect_thumbnails.py:129`, `exporter.py:713` | **Forrás nem található** az eredeti néző és bélyegkép szabályára. A mai PicasaPy minden renderelő utat az exportméréshez igazít. Döntő Colab-felvétel: ugyanazt a képet `crop=` nélkül, láncbeli `crop64` taggal rácson, nézőben és exportban rögzíteni. |
| #4313 | A 41 nyelv katalógusa, eredeti és saját szövegekkel | `Picasa3i18n.dll`; `picasa-program-resources.md:937-941` szerint az eredeti erőforrás 41 nyelvet tartalmaz. | 41 `picasapy_*.ts` fájl; `dictionary.py`, `application.py:1048-1053`, `i18n_build.py:1-13` | **Egyezik.** Nyelvenként van Qt TS-katalógus. Hiányzó QM esetén a program a TS-fájlból fordít, majd `QTranslator` tölti be. Az angol alapnyelv fordító nélkül fut. Javaslat a #5186-ba: lezárható. |
| #4314 | Első induláskori nyelvfelajánlás | `picasa-fo-ablak-elrendezes.md:665-747`, bináris rutin `0x004060b0`, prompt `0x00c7f2c8`; a szöveg-xref és a nyelvbetöltési hívássorrend külön ellenőrizve. | `language_controller.py:188-209`, `application.py:985-1011`, `FirstRunLanguageDialog.qml:38-60` | **Eltér.** Az eredeti NT rendszeren csak 11 felismert nem angol nyelvnél kérdez, angol ASCII-szöveggel és a generikus ablak jelölőjével. A mai felajánlás 40 nem angol katalógust elfogad, lefordítja a PicasaPy nevét tartalmazó szöveget, nem mutat jelölőt, és konkrét nyelvkódot ment. Javaslat a #5186-ba: ezek a nyelvterületi és felületi eltérések legyenek tételesen elfogadva vagy javításra jelölve. |
| #4320 | A diavetítés ismétlés- és zeneopciója működik | `options.fen:129-138`, `picasa-create-features.md:5942-5955`; a bináris konfigurációolvasó `0x007fa7f0` a `LoopSlideshow`, `PlayMP3Tracks` és `MP3SlideshowPath` beállítást olvassa. | `OptionsTabSlideshow.qml:15-84`, `controller.py:601-651,675-698`, `Main.qml:2971-2978`, `SlideshowView.qml:47-63,195-208` | **Egyezik a kért kapcsolatokban.** A mentett ismétlés szabályozza a körbelépést, a zenejelölő szabályozza a lejátszót. A PicasaPy mappa- és albumzenét is kezel. Javaslat a #5186-ba: a két beállítás bekötése lezárható. |
| #4358 | Névcímke-csúszkák értéke, beosztása és sorrendje | `options.fen:228-255`; eredeti magyar Options képernyőkép a `kepek-leltar.md:58` leltári tételben; eredeti alapértékek `picasa-arcfelismeres.md:49-50`. | `OptionsTabNameTags.qml:58-213,216-235`, `src/picasapy/faces/clustering.py:63-64` | **Eltér az alapértékben.** A sorok, értékfeliratok és tíz beosztás megvannak. Az eredeti mindkét küszöb alapértéke 85, a PicasaPy klaszterküszöbé 70 az SFace kalibrálása miatt. Javaslat a #5186-ba: rögzítse ezt a viselkedési eltérést; a felületi elrendezés egyezik. |
| #4377 | Diavetítés fül alapértékei és mappamezője | `options.fen:129-138`, eredeti magyar Picasa képernyőkép `kepek-leltar.md:54`. | `OptionsTabSlideshow.qml:15-50`, `controller.py:601-619` | **Egyezik.** Az ismétlés alapból ki, a zene be. A mappacímke a mező fölött áll. Javaslat a #5186-ba: lezárható. |
| #4385 | Nyomtatás fül metrikus alapméretei és kétoszlopos elrendezése | `options.fen:141-153`, eredeti magyar képernyőkép `kepek-leltar.md:55`, területi alapérték levezetése `picasa-nyomtatas.md:41-65`. | `OptionsTabPrinting.qml:62-77`, `print_controller.py:237-253`, `dpi.py:189-217` | **Egyezik metrikus rendszerterület mellett.** Alapból az öt eredeti cm-méretet adja, ha nincs mentett méretválasztás. A kétoszlopos, három bal és két jobb elrendezés is egyezik. Javaslat a #5186-ba: a mentett beállítás felülírását kivételként jegyezze fel. |
| #4440 | Mentés, visszaállítás és fotóművelet utáni látható visszajelzés | `picasa-menu-parancsok-viselkedes.md:668-680` és `picasa-beviteli-mezok.md:172-178`: eredeti mentési/visszaállítási folyamatjelzés és hibaüzenet; a képernyőkép-leltárban nincs sikeres visszaállítás utáni kép. | `save_controller.py:210-220,222-252,700-738`, `Main.qml:4122-4136`, `photo_ops_controller.py:268-283` | **Eltér a visszaállítás folyamatjelzésében; a sikeres lezáró üzenet nyitott.** A mentésnek van folyamatjelzője; a visszaállítás az indexet és az előnézetet frissíti, de nem mutat folyamatjelzőt. A sikeres visszaállítás utáni külön üzenetet az eredeti forrásból nem lehet megállapítani. Javaslat a #5186-ba: a visszaállítás folyamatjelzőjét kérje számon, a lezáró üzenethez pedig kérjen célzott Colab-felvételt. |

## Forrás nélkül lezárt jegyek, harmadik köteg (#5265, 2026-10-17)

Módszer: a `git log --all --oneline --grep` találataiból azonosítottam a lezárt jegyek módosításait. A mai QML és Python állapotot az eredeti képernyőképekkel, `.fen` és `.tre` erőforrásokkal, UI-leltárral, bináris indexszel és célzott diszasszemblálással vetettem össze. A GitHub-jegykommentek ebben a munkamenetben nem voltak elérhetők.

Mérési vakfolt: a mai felületet nem futtattam, ezért a táblázat a jelenlegi forráskódot írja le, nem mai képernyőképet. Az eredeti leltár nem tartalmazza az összes szükséges hover-, billentyű- és retusálási állapotot. A #4544 eredeti előtte-utána képe sincs a helyi mérőcsomagban. Ezeknél a Colab-lépés a döntő ellenőrzés.

| jegy | funkció | eredeti forrás | mai állapot fájl:sor | ítélet |
|---|---|---|---|---|
| #4456 | Mappa tulajdonságai elrendezése | `Picasa3/runtime/album.fen:1-29`; eredeti kép `2026-07-17 20 59 22.png` (`referencia/kepek-leltar.md:50`); `Folder Properties` sztring `0x00cc1be8`, hivatkozó függvény `0x00849750` | `src/picasapy/app/qml/PicasaPy/FolderPropertiesDialog.qml:273-291,322-410` | Részben egyezik: a címke, szerkeszthető név, dátum és Mégse gomb sorrendje megvan. A mai ablak képpontos elrendezése nincs lefényképezve. Javaslat a #5186-ba: a pixelparitást csak azonos állapotú mai képernyőképpel jelölje késznek. |
| #4482 | Átnevezés a Név mezőből | `album.fen:2-4`; eredeti kép `2026-07-17 20 59 22.png`, a mező szerkesztésre kijelölve | `FolderPropertiesDialog.qml:213-236`; `FolderPane.qml:1721-1728`; `library_controller.py:1741-1751` | Részben egyezik: a mai mező átnevező kezelőhöz jut, amely átnevezi a mappát és frissíti az indexet. Az eredeti képernyőkép mezőt mutat, de sikeres átnevezést nem. Javaslat a #5186-ba: az eredeti Picasában mappát átnevezni, majd a fa és az elérési út változását rögzíteni. |
| #4488 | Fájltípusok fül feliratai és térköze | Eredeti kép `2026-07-17 21 00 00.png` (`referencia/kepek-leltar.md:53`), a fül és a teljes fájltípus-sorrend látszik | `src/picasapy/app/qml/PicasaPy/OptionsTabFileTypes.qml:7-13,28-49,132-259` | Feltételes egyezés: a sorok és sorrend megfelel az eredeti képnek, a mai kód külön geometriát ad meg. Mai PicasaPy-kép nincs a képpontos összevetéshez. Javaslat a #5186-ba: a vizuális állítást páros képernyőképekkel igazolja. |
| #4494 | Naptár a Dátum mezőből | `album.fen:5-9` dátumvezérlője és Automatikus dátum gombja; eredeti kép `2026-07-17 20 59 22.png` | `FolderPropertiesDialog.qml:382-411,641-649`; `DateCalendarPopup.qml:5-18` | Részben egyezik: a mai mező naptárgombot nyit és a választott napot a mezőbe írja. Az eredeti vezérlő nyitási és kiválasztási útjáról nincs felvétel. Javaslat a #5186-ba: eredeti Colab-felvétel a naptár nyitásáról és egy nap kiválasztásáról. |
| #4527 | Csillag súgójának célja | `referencia/tre-eroforrasok/thumbui_text.tre:113` és `referencia/ui-leltar.csv:1820` az `Add/Remove Star` súgót a csillaghoz rendeli; a More külön elem (`referencia/ui-leltar.csv:1272`) | `src/picasapy/app/qml/PicasaPy/TrayBar.qml:1244-1256,2264-2293` | A célhoz kötés egyezik: a mai súgó a csillaggombon van, nem a More gombon. Az eredeti súgó tényleges képernyőbeli helyét nem mutatja hover-felvétel. Javaslat a #5186-ba: eredeti Colab-felvétel a csillag és a More fölötti külön hoverrel. |
| #4530 | Keresősáv javaslatainak billentyűkezelése | `referencia/tre-eroforrasok/searchcontainer.tre:4-10` és bináris `0x0040e7b0`: az eredeti `searchautocomplete` erőforrás létrehozása | `SearchSuggestions.qml:42-67`; `MainToolbar.qml:811-832`; `Main.qml:2839-2848` | Nyitott: az eredeti javaslatlista forrása megvan, de ez nem bizonyítja a fel-le, Enter és Escape billentyűk eredeti viselkedését. Javaslat a #5186-ba: Picasa Colab-felvétel a javaslatlista megnyitásával és a négy billentyű rögzítésével. |
| #4531 | Vissza a teljes nézethez szöveges keresés után | `referencia/tre-eroforrasok/searchoptions.tre:20-27`; eredeti címke és súgó a `picasa-kereses-modok.md:29` szerint: `Back to View All` és `Exit Search Mode` | `src/picasapy/app/qml/Main.qml:3368-3400` | Feltételes egyezés: a mai gomb kiüríti a keresőmezőt és törli a szűrést. Az eredeti gomb viselkedéséről szöveges keresés utáni felvétel nincs. Javaslat a #5186-ba: Colab-felvétel szöveges lekérdezés után a gomb megnyomásával. |
| #4532 | Ne legyen működés nélküli jel a szűrősáv végén | `referencia/tre-eroforrasok/searchcontainer.tre:30-93` felsorolja az öt szűrőt és az idősávot; ezek között nincs további szűrővezérlő | `src/picasapy/app/qml/PicasaPy/MainToolbar.qml:725-728` | Egyezik a forrás szerkezetével: a mai kódból eltávolított jel helyén csak térköz marad, a mozgófilmnek külön gombja van. |
| #4533 | Megnyitás ezzel programválasztás és képnyitás | `AlbumPhoto::ID_FILEOPENWITH`; az eredeti Windows Shell társításait a `ui-audit-context-menus.md:232` rögzíti | `PhotoContextMenu.qml:350-390`; `OpenWithDialog.qml:26-33,45-61,94-100`; `fileops_controller.py:731-761` | Funkcionálisan egyezik: program választható és azzal nyílik meg a kép. Windowson az eredeti Shell párbeszéd marad, más platformon a mai saját lista jelenik meg. |
| #4534 | Mappa kettéosztása a kijelölt képtől | `picasa-menu-parancsok-viselkedes.md:7689-7750`; eredeti handler `0x005e8570`, a leírt művelet a kijelöléstől a csoport végéig viszi át a képeket | `src/picasapy/app/qml/Main.qml:712-749`; `src/picasapy/app/fileops_controller.py:264-320` | Egyezik: a mai út az első kijelölt képtől a mappacsoport végéig készít új testvérmappát, és áthelyezi a képeket. Az eredeti bináris viselkedése és a mai műveleti út külön forrásból dokumentált. |
| #4539 | Film készítése gomb a mappafejlécen | `referencia/tre-eroforrasok/headerpanel.tre:75-84` `create_movie` gombja; eredeti kép `2026-07-17 20 54 38.png` mutatja az alapból látható gombot | `src/picasapy/app/qml/PicasaPy/LightboxHeader.qml:407-429` | Egyezik: az eredeti erőforrás gombot ír le, a kép látható állapotot mutat, a mai gomb mappanézetben látható. |
| #4542 | Vörösszem-figyelmeztetés kiegyenesítés után | Bináris sztring `0x00e063da`, hivatkozó függvény `0x005f30e0`; az eredeti szöveg megegyezik a mai szöveggel | `src/picasapy/app/qml/PicasaPy/EditorRedeyePanel.qml:81-96`; `PhotoViewer.qml:1356-1369` | A szöveg egyezik, a mai megjelenési feltétel `tiltParam != 0`. Az eredeti feltétel futás közbeni igazolása hiányzik. Javaslat a #5186-ba: Colab-felvétel kiegyenesített és kiegyenesítés nélküli képpel. |
| #4543 | Ecsetkör a retusálás céljánál és forrásánál | `referencia/tre-eroforrasok/editpanel.tre:217-229,958-962`: a retusáló megjeleníti a `thumbui/circlecursor` elemet és a `RetoucherHandler`-t | `src/picasapy/app/qml/PicasaPy/PhotoViewer.qml:3880-3939`; `src/picasapy/app/edit_controller.py:1727-1747` | Nyitott a két eredeti célpont részlete: az erőforrás a kört és a kezelőt igazolja, de nem mutatja külön a cél- és forrásjelölő mozgását. Javaslat a #5186-ba: Colab-felvétel első kattintás, forrásmozgatás és második kattintás közben. |
| #4544 | Retusfolt széleinek környezetbe olvadása | `referencia/tre-eroforrasok/editpanel.tre:958-962` az eredeti retusáló kezelőt azonosítja, de az eredeti pixelátmenethez nincs képi golden vagy leltározott felvétel | `src/picasapy/render/retouch.py:86-116,137-224,229-249` | Az eredeti széleffekt forrása nem található. A mai kód irányított Poisson-gyógyítást használ, de az eredetivel való egyezés nincs mérve. Javaslat a #5186-ba: ne jelölje eredeti paritásnak; kérjen azonos mintán eredeti előtte-utána képet és nyers kimenetet, majd rögzítse a mért különbséget. |
| #4546 | Rendszerbetűk a szöveg betűtípus-listájában | `referencia/tre-eroforrasok/edittextpanel.tre:19` és bináris `GDI32.EnumFontFamiliesExW` hívója `0x00825e90` | `src/picasapy/app/qml/PicasaPy/EditorTextPanel.qml:121-131`; `src/picasapy/app/edit_controller.py:938-943`; `src/picasapy/render/text_fonts.py:98-137` | Funkcionálisan egyezik: az eredeti Windows-betűcsaládokat kérdez le, a mai Qt futáskor a telepített rendszer-betűcsaládokat kínálja. A lista elemei gépenként változnak. |

## Forrás nélkül lezárt jegyek, negyedik köteg (#5271, 2026-10-18)

Módszer: a tizenöt jegyhez a `git log --all --grep="#<szám>"` találatait és a változtatott fájlokat néztem meg. Az eredeti forrás a `docs/specs` szakaszai, a `referencia/tre-eroforrasok` erőforrásai, a `stringres-en-hu.tsv`, a `ui-leltar.csv`, a `kepek-leltar.md` és a bináris sztringtábla (`binary-index/string_xrefs.csv`) volt. A `ui-lefedettseg-elemek.csv` a legtöbb tételnél „megvan" állapotot mutat. Ez nem ítélet, ezért nem vettem bizonyítéknak. A jegykommentek közül csak a #4571 és a #4579 tartalmaz érdemi szöveget, a többi foglalási sor. A negatív bináris-index találatot nem tekintettem bizonyítéknak. Kódhoz nem nyúltam.

Mérési vakfolt: az alkalmazást nem futtattam, és nincs új Colab-felvétel. A mai állapotot kódolvasással vetettem össze, renderelt képpel nem. A tesztek nem futottak. A #4547 ikonjainak bitképe nincs kivonva. A #4570 alapértéke és megnyitáskori viselkedése nincs felvételen. A #4550 statikus példa-sorát a `.fen` leírásából állapítottam meg, futó programban nem ellenőriztem.

| jegy | funkció | eredeti forrás | mai állapot, fájl:sor | ítélet |
|---|---|---|---|---|
| #4547 | A szöveg balra, középre és jobbra igazító gombja | `referencia/tre-eroforrasok/edittextpanel.tre:70-94`: három külön ikon (`leftalign_icon` `:75`, `centeralign_icon` `:83`, `rightalign_icon` `:91`), bitképpel. | `src/picasapy/app/qml/PicasaPy/EditorTextPanel.qml:239-290` (`AlignIcon` a `:250`, `:267`, `:284`); `AlignIcon.qml:1-39`: négy rajzolt vonal. | **Részben egyezik.** Külön jel van, az azonos `≡` megszűnt. A forma nem igazolt, mert az eredeti bitképet nem vontam ki. Döntő lépés: a respack `leftalign_icon` bitképe, vagy nagyított Colab-kép. Javaslat a #5186-ba: a „külön jel" részt zárja, a formát külön tételként nyissa. |
| #4550 | Egyéni méretarány párbeszéd, példa-sor, törlő kuka | `referencia/tre-eroforrasok/editpanel.tre:784-790`: a legördülő bal oldalt, `crop_delete_custom` jobb oldalt, ugyanazon a soron. `docs/specs/picasa-fen-dialogs.md:101` és `docs/specs/ui-audit-editor.md:1029`: a `customaspectratio.fen` „Example:" sora statikus, nincs `bind`. | `src/picasapy/app/qml/PicasaPy/AddCustomAspectRatioDialog.qml:99-113` (statikus példa-sor); `EditorCropPanel.qml:91-135`: a kuka (`cropDeleteCustom`, `:123`) a legördülő mellett. | **Egyezik a forrással, a jegy szövege téves.** A jegy élő példa-sort kér. Az eredeti `.fen` szerint a sor statikus, a javítás ezt követi. Javaslat a #5186-ba: a jegy kérését „statikus példa-sor"-ra javítsa. Futó ellenőrzés nincs. |
| #4551 | Vágópanel: az eredetiben nem létező Bal felső, Fekvő és Álló gombok | `referencia/tre-eroforrasok/editpanel.tre:795-830`: az eredeti gombok Rotate, Preview, Reset, Apply, Cancel. `referencia/ui-leltar.csv`: `cropsug1-3` címke és súgó nélkül, csak előnézeti képpel. Bináris sztring: „Crop by horizon line" (`binary-index/string_xrefs.csv:13485`). | `EditorCropPanel.qml:337-355` (Rotate, Preview, Reset); `:298-328` (három javaslatgomb felirattal); `EditorPanel.qml:472-474` (feliratok). | **Részben egyezik.** A három nem eredeti gomb eltűnt, ezt a jegy helyesen állítja. A három javaslatgomb felirata nincs az eredeti erőforrásban. A mai „Crop by horizon" (`EditorPanel.qml:474`) eltér a bináris „Crop by horizon line" szövegtől. A „Suggested crops" címsor (`EditorCropPanel.qml:293`) nincs a leltárban, és ASCII sztringként a bináris indexben sem található. Javaslat a #5186-ba: a feliratokat és a címsort külön igazolja. |
| #4557 | Shift+Ragyogás: csúszkás panel Intenzitás és Sugár csúszkával | `docs/specs/ui-audit-editor.md:1383` és `:1415`: a Shift-pár `glow`, paraméterei Intenzitás és Sugár. `docs/specs/filterdesc-registry.md:162-163`: `glow` és `glow2` ugyanaz a két csúszka (0 = Intensity, d = 0,65; 1 = Radius, d = 3,0, log 250). | `src/picasapy/app/effect_params.py:147-150` (`glow`), `:151-161` (`glow2`, ugyanaz a két csúszka). | **Egyezik.** A két csúszka a `glow2` szerint épül fel. A Sugár tartománya és alapértéke (0-100, 20) a `:155-159` megjegyzése szerint szándékos. A `glow` ugyanezt használja. A skálázást külön nem mértem. |
| #4558 | Shifttel a csempék bélyegképe is a másodlagos effektet mutatja | `docs/specs/ui-audit-editor.md:1390`: a Shift-csempe „felirata és bélyegképe is" a másodlagos effektre vált (`_mod%s` utótag). | `src/picasapy/app/qml/PicasaPy/EditorEffectsTab1.qml:11-14` (a bélyegkép a Shift szerint vált, a Shift a láthatóságot), `:60-72`, `:104-122` (`thumbAltActive`). | **Egyezik.** A bélyegkép és a felirat is a Shift-változatot mutatja. |
| #4560 | Sixties, Polaroid és Lekerekített szél színmintájának felirata | `docs/specs/picasa-effekt-feliratok.md:75`: Polaroid, RoundedEdges, Sixties → „Background Color" = „Háttérszín" (`0x008feed8`). | `src/picasapy/app/effect_params.py:319`, `:403`, `:408` („Background Color"); `src/picasapy/app/i18n/picasapy_hu.ts:4462-4465` („Háttérszín"). | **Egyezik.** A három effekt felirata az eredeti szöveg, a magyar fordítás megvan. |
| #4561 | Effekt alkalmazása után a csempék előnézete a frissített láncot mutatja | `docs/specs/ui-audit-editor.md:2900` (a 2827. szakasz, #2061): „a csempe-előnézet a szerkesztési lánc AKTUÁLIS tetejére alkalmazza a saját effektjét, nem az alap fotóra". | `src/picasapy/app/effect_thumbnails.py:16-21` (a lánc a `filters` paraméterben érkezik, a frissebb állapotot követi); `src/picasapy/app/qml/PicasaPy/editorpanel_logika.js:76-84` (az aktuális `effectChain` az URL-ben). | **Egyezik a spec szerint.** A forrás a lánc tetejére renderel, a mai kód az aktuális láncot viszi át. A `tests/app/qml_functional/test_effect_tile_chain_refresh_4561.py` tesztet nem futtattam. |
| #4562 | Filmszalag: hét férőhely, az aktuális kép középen, kétszínű keret | `docs/specs/szerkeszto-felso-sav.md:161-185`: 5.1 hét férőhely (7 × 28 + 6 × 3 = 214 px), 5.2 az aktuális kép a középső férőhelyen, 5.3 keret: `#009EFF` és `#D4D4D4`. | `src/picasapy/app/qml/PicasaPy/PhotoViewer.qml:1905-1910` (214 px, fix), `:1945` (31 px cella), `:1955-1957` (28 × 28 bélyegkép), `:1976` (aktuális kép), `:1987`, `:1994` (kétszínű keret). | **Egyezik.** A hét férőhely, a középső aktuális kép és a kétszínű keret megegyezik az 5. szakasszal. A cella- és bélyegképméret is egyezik (31 és 28 px). |
| #4563 | A néző ◀ és ▶ gombja nyomva tartva folyamatosan léptet | `docs/specs/szerkeszto-felso-sav.md:193-197`: 5.4, mindkét nyíl `m_autorepeat`, nyomva tartva folyamatos léptetés. | `src/picasapy/app/qml/PicasaPy/PhotoViewer.qml:1856`, `:2022` (`autoRepeat: true`); `PicasaButton.qml:129-163` (ismétlő időzítő). | **Egyezik.** A nyomva tartás a spec szerint léptet. A kör alak már megvan (30 × 31, `PhotoViewer.qml:1840-1846`, #1993). A spec 29 × 30-as mérete egy képponttal tér el, ezt nem vizsgáltam. A `szerkeszto-felso-sav.md` 311. sorának „nálunk" oszlopa a javítás előtti állapotot írja. |
| #4570 | AutoPlayMovies: a videó megnyitáskor magától elindul-e | `referencia/binary-index/string_xrefs.csv:6217-6218`: a `AutoPlayMovies` sztring a `0x00c91f74` címen, hivatkozói `0x00593880` és `0x00594820`. `docs/specs/ui-audit-editor.md:3252`: a `Preferences` kulcs a videó-vezérlő építésénél. Az alapérték és a viselkedés nincs leírva. | `src/picasapy/app/appearance_controller.py:26-28` (kulcs; „Alapállapot: igen (a Picasa így működött)"), `:176-182` (nem slot); `src/picasapy/app/qml/PicasaPy/VideoPlayerView.qml:18-24`, `:89`, `:99-106` (indítás). | **Forrás nem található** a megnyitáskori viselkedésre és az alapértékre. A kulcs és a kiolvasás helye megvan. Az `appearance_controller.py:27` sorának „a Picasa így működött" állítása forrás nélkül áll. Döntő Colab-lépés: a kulcs 0, illetve 1 értékkel, videó megnyitása, és az alapérték kulcs nélküli, friss profilban. |
| #4571 | A Névtelenek album csempéi az arcot mutatják, nem a fotó közepét | `docs/specs/picasa-arcfelismeres.md:2346` (19. szakasz, job-163: csoportosított nézetben álló arc-kivágások). A #4571 számmal nincs commit. A lezárást a #4511 végezte (`51235e5aa`, PR #4521, v0.9.40), a jegy kommentje szerint. | `src/picasapy/app/people_controller.py:858-867` (a csempe `thumbUrl`-je `_thumb_url(photo, arc=face.rect)`; arc nélküli elem kimarad); `src/picasapy/app/qml/PicasaPy/UnnamedFacesView.qml:408` (a kép forrása a `thumbUrl`). | **Egyezik.** A csempék arckivágást mutatnak, és nincs visszaeső ág a fotó közepére. A `51235e5aa` commit `&fz=` tesztjei ezt rögzítik. |
| #4572 | Nézőben a felismert, névtelen arcra kattintva keret és „Type a name" mező | `referencia/kepek-leltar.md:113-114`: Colab EN 37 (mellőzött arc: nincs keret) és EN 38 (nem mellőzött névtelen arc: keret és „Type a name"). A teszt az EN 38 képből mért keretet használja: `tests/app/qml_functional/test_viewer_unnamed_face_4572.py:21-36`, `tests/fixtures/face_type_a_name_reference_en38.png` (538 × 807). | `src/picasapy/app/qml/PicasaPy/FacesOverlay.qml:79-82` (a keret kattintásra látszik), `:414` („Type a name"). | **Egyezik, feltételesen.** A keret helye és a mező felirata megfelel a forrásnak. A mellőzött arc esetét (EN 37) nem ellenőriztem. A tesztet nem futtattam. |
| #4574 | Emberek panel: „Add a person manually" gomb és útmutató | `referencia/stringres-en-hu.tsv:3228` (az útmutató szövege); `referencia/tre-eroforrasok/peoplepanel.tre:24-32` (a gomb induláskor rejtett, `m_hidden`); `referencia/kepek-leltar.md:113` (Colab EN 37: a gomb a mellőzött arc kijelölésekor látszik). | `src/picasapy/app/qml/PicasaPy/PeoplePanel.qml:391-399` (`visible: !manualAddActive`, `enabled: selectionCount > 0`), `:403-440` (kézi keret; az útmutató szövege `:414-431`). | **Részben egyezik.** Az útmutató szövege karakterre egyezik a `stringres-en-hu.tsv:3228` szövegével, a felirat is. A láthatóság eltér: a `.tre` szerint induláskor rejtett, a mai gomb kijelölés nélkül is látszik, csak tiltva. Döntő Colab-lépés: az Emberek panel kijelölés nélküli állapota. |
| #4579 | Tulajdonságok panel: Fájl dátuma, CCD szélessége, Rekesz, JPEG minőség, Személycímkék | `docs/specs/picasa-metaadat-tulajdonsagok.md` 17. szakasz: a sorrend (B), a dátum (C), a CCD-képlet (D), a minőségbecslő (E), a személycímkék (F). A számok szöveggé alakítását futtatott CRT-vel mérték. A feliratok a `picasapy_hu.ts` fájlban is megvannak. | `src/picasapy/app/formatting.py:508` (Fájl dátuma), `:524` (CCD Width), `:532` (Aperture), `:560` (JPEG Quality), `:568` (People Tags); `src/picasapy/metadata/reader.py:343` (CCD-képlet). | **Egyezik a 17. szakasz szerint.** Szándékos eltérés: a JPEG-minőség nem veszi át a Picasa előjeles olvasási hibáját (17. E). Nyitott: a nem pontosan ábrázolható félértékek kerekítése (17.). A 17. szakasz G táblája (`:2510`) még „nálunk: nincs" állítást tesz. Ez elavult, frissítendő. |
| #4584 | Helyek térkép: betöltésjelzés és internet nélküli üzenet | `referencia/tre-eroforrasok/geopaneltext.tre` (a betöltésfelirat, `geopanel/loading_title`); `docs/specs/jobb-fiok-meretek.md:158-160`: `loading_icon` 64 × 52, `loading_title` 213 × 25, y 117 és 153; `referencia/stringres-en-hu.tsv:2982` (`geo::init_err`, a hibaüzenet, bináris hivatkozóval: `0x00ca1d58`). | `src/picasapy/app/qml/PicasaPy/PlacesPanel.qml:145-152` (`BusyIndicator` 48 × 48), `:155-159` (a két szöveg). | **Részben egyezik.** A két szöveg az eredeti. A jelző eltér: az eredeti 64 × 52-es ikon, a mai 48 × 48-as `BusyIndicator`. A függőleges helyet nem mértem a 117 és 153 px-es értékekhez képest. Javaslat a #5186-ba: a jelzőt az eredeti ikonhoz igazítani, vagy eltérésként rögzíteni. |

## Forrás nélkül lezárt jegyek, ötödik köteg (#5272, 2026-10-18)

Módszer: a tizenegy jegyet a `git log --all --grep` találataiból és a változtatott fájlokból vettem sorra. A jegyek kommentjeit a `gh issue view` adta. Az eredeti forrást a `docs/specs` szakaszaiban, a `stringres-en-hu.tsv`-ben, a képernyőkép-leltárban és a PicasaPy fő munkafájának `research/testdata/screenshot/` mappájában lévő képekben kerestem. A #4846 eredeti fülsávját 4-szeres nagyításban néztem meg. A mai állapotot a QML és a Python forrásból olvastam. A negatív bináris-index találatot nem tekintettem bizonyítéknak. A #5121 Colab-méréseit a jegy kommentjeiből vettem át.

Mérési vakfolt: nem futtattam az alkalmazást, és nem rendereltem a mai felületet, ezért a pixelszintű állítások nyitottak. Eredeti film- vagy nyomtatási kimenetet a leltárban nem találtam (#4602, #4616). A #4594 olvasási útjához Colab-felvétel kell: nagy kezdőbetűs `Picasa.ini`, benne csillag és felirat. A #5121 Colab-képeit nem néztem meg, csak a jegy kommentjeinek leírását. A `picasa-konyvtar-eszkoztar-viselkedes.md` 7/b. szakasza a beszúrási feltételt nyitottnak hagyta. A Colab-mérés a húzási eseteket megválaszolta, a bináris kérdés (`0x004b3770`, `0x00565920`) viszont nyitva maradt.

| Jegy | Funkció | Eredeti forrás | Mai állapot, fájl:sor | Ítélet |
|---|---|---|---|---|
| #4590 | Csatolt memóriakártya és kamera felismerése, forrásként felkínálása | `picasa-importalas.md`, „Forrásfajták”: `Removeable` → „Cserélhető meghajtó (%s)”, `WiaDev` → „Wia-” (kamera). `stringres-en-hu.tsv:173`: „Mappa a lemezen”. | `import_source_controller.py:176-268`: Linuxon `/media` és `/run/media`, Windowson cserélhető meghajtó vagy DCIM-es kötet. `:258-261`: a PTP/MTP kamera tudatosan kimarad. `ImportSourceDialog.qml:64-72`. | **Részben egyezik.** A kártya és a cserélhető meghajtó egyezik. A kamera hiányzik, a kód ezt szándékosan kizárja. |
| #4594 | Csillagok és feliratok beolvasása a régi `Picasa.ini` fájlból | A név bizonyított: `picasa-exe-strings.md:248` (a régi, korai verziójú név, megerősítve), `string_xrefs.csv:3422-3429`: nyolc hivatkozási hely. `picasa-ini-format.md:13`: a korai verzió neve. Az olvasási út nincs mérve. | `scanner/walker.py:369` (a régi fájl is adja a `has_ini` jelzőt), `index/sync.py:1216-1220` (`_load_ini`), `ini/io.py:142` (`ini_source_path`: a `.picasa.ini` az elsődleges, a régi fájl csak olvasási forrás). | **Forrás nem található** az olvasási útra. A név megvan, de nem derül ki, hogy az eredeti 3.9 olvas-e csillagot és feliratot belőle. Döntő: Colab-felvétel nagy kezdőbetűs `Picasa.ini`-vel, csillaggal és felirattal. |
| #4595 | Kézi mappanév nélkül nem indul az importálás | `picasa-importalas.md`, „A tipp-sor NÉGY állapota”, 1. állapot: „Enter new folder title or choose existing folder to continue”. A folytatáshoz cím vagy meglévő mappa kell. | `import_source_controller.py:859-860` (kézi mód cím nélkül visszatér), `importsource.py:374-377` (`ValueError`), `ImportSourceDialog.qml:816` és `:834` (a tipp). Az Import gomb engedélyezése (`:950-953`) nem nézi a címet. | **Egyezik** a tilalomban. A visszajelzés eltér: a gomb engedélyezett, a kattintás csendben nem tesz semmit. |
| #4596 | Forrásként fájlok is elfogadhatók, nem csak mappa | `stringres-en-hu.tsv:175`: `CAcquireUI::importfilestitle`, „Import Files/Folder”, magyarul „Fájlok/mappa importálása”. A forrástípusok listájában (`picasa-importalas.md`) nincs külön fájlforrás. A fájl-gomb eredeti felirata nincs azonosítva. | `ImportSourceDialog.qml:375` (gomb: „Files...”), `:981` (párbeszéd címe), `import_source_controller.py:805` (`scan_files` hívása), `importsource.py` (`scan_files`). | **Egyezik.** Az eredeti párbeszéd címe is fájlt és mappát nevez meg. A gomb szövegét nem mértük. |
| #4602 | A nyomtatás a rácson látott, szerkesztett és elforgatott képet nyomtatja | Nincs leírt eredeti szabály. A `kepek-leltar.md` 82-83. tétele (Colab EN 29-30) a nyomtatási elrendezést mutatja, nem azt, hogy a szerkesztett kép került-e rá. | `print_controller.py:769-790` (`_render_photo` → `render_photo_pixels`, ugyanaz a renderelő, mint az exportnál), `:68` (import). | **Forrás nem található.** Döntő: Colab-felvétel egy forgatott és szűrt képről, rácson és nyomtatási előnézetben. |
| #4611 | A weboldal-export a felhasználó saját `.tpl` sablonjait is felajánlja | `picasa-program-resources.md:112-120`: a sablonok a `web/templates/<sablonnév>/` mappákban vannak, a gyökér az `index.tpl`. `picasa-web-template-nyelv.md:15`: a `#templatefile` fejlécben lévő név az export-varázslóban jelenik meg. | `webexport/catalog.py:30-34` (felhasználói mappa: `~/.local/share/picasapy/webexport/templates`), `:44-53` (gyári sablonok, utánuk a sajátok), `:56-75` (`index.tpl` és fejléc). | **Részben egyezik.** A felajánlás és a fejlécből vett név egyezik. A tárolási hely eltér: az eredetinél a programmappa `web/templates` alatt van, nálunk a felhasználói mappában. A varázsló bejárását nem mértük. |
| #4616 | A film Show Captions kapcsolója a Picasa-feliratot mutatja, nem csak az EXIF-leírást | A kapcsoló megvan: `picasa-create-features.md:3191` (`makemoviepanel/show_captions` → `showcaption`). A tulajdonos mozgófilm-képe (`kepek-leltar.md`) a „Képfeliratok megjelenítése” jelölőt mutatja. A film szövegének eredeti forrása nincs mérve. `picasa-ini-format.md:98`: JPEG-nél a felirat az IPTC Caption mezőbe kerül, nem a `.picasa.ini`-be. | `movie/slideshow.py:545-558` (`_picasa_caption`: csak az ini `caption` kulcs), `:597` (EXIF 270 tartalék). A film nem olvas IPTC-t. | **Részben egyezik.** A kapcsoló egyezik. A spec szerint JPEG-nél a Picasa-felirat IPTC-ben van, ezt a film nem olvassa, ezért eltérés várható. Mérés nincs. |
| #4846 | A szerkesztő fülikonjainak rajza tükrözött és egyszerűsített | Eredeti: `research/testdata/screenshot/2026-07-17 20 56 36.png` (a PicasaPy fő munkafájában), az ötös fülsáv 4×-es kivágása. A csavarkulcs feje bal fent; az ecset sörtéje bal lent; a 4-5. fülön tájképes négyzet bal fent, az ecset jobb lent. | `EditTabIcon.qml:45-66` (csavarkulcs, feje bal fent), `:94-111` (ecset, sörte bal lent), `:113-135` (tájképes négyzet, az ecset eltolva), `:137` (`onPaint`). | **Részben egyezik.** Az irány a kivágás és a QML-koordináták szerint egyezik. A forma közelítés. A jegy tesztje (`tests/app/qml_functional/test_fulikon_rajz_4846.py`) negyedenkénti tömeget mér; ezt nem futtattam. |
| #4881 | A párbeszédek szabványos gombjai a választott felületi nyelven jelenjenek meg | A Picasa saját `.fen` párbeszédei a saját gombfeliratukat használják (`picasa-fen-dialogs.md:106-107`: OK, Cancel; `:37`: Igen/Nem/Mégse). A Windows-üzenetdoboz gombjainak eredeti viselkedését nem mértük. | `application.py:1014-1029` (`_install_qt_translator`: a Qt `qtbase_*.qm` fordítója), `:1044` (`QLocale.setDefault` a választott nyelvvel, a területet a rendszer adja). | **Egyezik** a nyelv elvében. A tizedesjel a rendszer területét követi (ADR-004), az eredetit nem mértük. |
| #5007 | A mappára húzott indexképek átkerülnek, a Másolás/Beillesztés átvisz képet | `picasa-menu-parancsok-viselkedes.md:627-633`: a vágólapra fájlok kerülnek (IDList, FileGroupDescriptor), a Kivágás és a Másolás különbsége a `Preferred DropEffect` formátumban van. A húzás szemantikája (mozgatás vagy másolás) nincs leírva. | `FolderPane.qml:1193-1214` (`folderDropArea` → `photosDroppedOnFolder`), `Main.qml:3315-3324` (mozgatás: `movePhotos`), `fileops_controller.py:590` (`copyFilesToClipboard`), `:622` (`pasteFilesFromClipboard`). | **Részben egyezik.** A vágólap modellje egyezik a forrással. A húzás mozgatása forrás nem található. |
| #5121 | Meglévő album mellett ráhúzással nem lehet új albumot készíteni | Colab, eredeti Picasa 3.9, a jegy kommentjei szerint (job-155, -156, -159, -160): húzás az Albumok fejlécére, a sorok alá és az Új album (+) gombra nem készít albumot, meglévő albummal sem. A kontroll húzás a meglévő „Teszt album” sorra működik. Kiinduláskor, csak a „Recently Updated” rendszeralbummal, nincs súgósor (job-155). | `AlbumsSection.qml:65-67` (súgó és ejtési terület csak `albumsModel.length === 0` esetén), `:93-94` (`albumDropArea`). | **Egyezik** a meglévő album melletti viselkedésben. **Eltér** a nyugalmi súgósorban: a mai kódban üres albumlistánál látszik, az eredetinél a job-155 szerint nem. |

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

- A HDR maga pontos. Önmagában és a telítettség után is bitre egyezik, és a sorrend sem hiba: ha a HDR-t a lánc elejére tesszük, a k03 ΔE-je 5,28, a k06-é 28,09 lesz.
- A HDR felnagyítja a bemenete eltérését. A kimenete `be + C·(be - elm)`, így a bemenet helyi eltérése `C = 3`-nál nagyjából (1 + C)-szeresére, négyszeresére nő. A k03-ban az autolight és a sat eltérése 0,669, a HDR után 2,57: a szorzó 3,8. Ugyanez látszik, ha a saját HDR-ünket a Picasa JPEG-ként mentett autolight+sat exportjára futtatjuk: a JPEG-zaj is felnagyítódik, a ΔE 3,63.
- Az eltérés forrása tehát a HDR előtti tagokban van, azoknak a maradékában, amely önmagában a küszöb alatt marad: az autolight és a sat együtt 0,669 (a k03-ban), a HeatMap az IR után +1,38 (a k02-ben az első három réteg 0,29, a negyedikkel 1,666). Ezek külön-külön egyeznek, csak a HDR mögött lépik át a küszöböt.
- A k06-ot más képen mértük, mint a k02 négyrétegű láncát, ezért a HDR előtti ΔE-je nincs külön mérve. Az ítélete ugyanezzel a felnagyítással magyarázható, de ez nincs kimérve.
