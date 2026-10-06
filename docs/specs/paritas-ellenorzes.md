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
| Kép, effekt, kijelölés | `ID_PICTURE_AUTO_COLOR`, `ID_PICTURE_AUTO_LIGHTING`, `ID_PICTURE_AUTO_REDEYE`, `ID_PICTURE_ENHANCE`, `ID_PICTURE_FILM_GRAIN`, `ID_PICTURE_GEOUNTAG`, `ID_PICTURE_HIDE`, `ID_PICTURE_PROPERTIES`, `ID_PICTURE_REVERT`, `ID_PICTURE_ROTATECLOCKWISE`, `ID_PICTURE_ROTATECOUNTERCLOCKWISE`, `ID_PICTURE_SEPIA`, `ID_PICTURE_SHARPEN`, `ID_PICTURE_WARMIFY` | `PicasaMenuBar.qml:1660–1766`; az eredetihez képesti effektkimenet nem volt mérve, a 7. réteg továbbra is nyitott. |
| Nézet és felirat | `ID_CAPFILE`, `ID_CAPFULL`, `ID_CAPNONE`, `ID_CAPRES`, `ID_CAPTAG`, `ID_SELECT_INVERT`, `ID_VIEW_ALL`, `ID_VIEW_AUTO`, `ID_VIEW_BW`, `ID_VIEW_COLOR_MANAGED`, `ID_VIEW_DESKTOP`, `ID_VIEW_FOLDERS`, `ID_VIEW_LARGETHUMBNAILS`, `ID_VIEW_LCD`, `ID_VIEW_LIGHTBOXVIEW`, `ID_VIEW_LINEAR`, `ID_VIEW_MAC`, `ID_VIEW_NORMAL`, `ID_VIEW_OV`, `ID_VIEW_PEOPLE`, `ID_VIEW_PLACES`, `ID_VIEW_PROJECTOR`, `ID_VIEW_PROPERTIES`, `ID_VIEW_SEPIA`, `ID_VIEW_SHOWHIDDEN`, `ID_VIEW_SLIDESHOW`, `ID_VIEW_SMALLTHUMBNAILS`, `ID_VIEW_THUMBNAILS`, `ID_VIEW_WATCHED` | `PicasaMenuBar.qml:755–1478`; felirat- és nézetkezelők a `Main.qml`-hez és a megfelelő panelekhez kapcsolódnak. A „megvan” itt is statikus út, nem kattintásos igazolás. |
| Létrehozás | `ID_COLLAGEMAKER`, `ID_POSTER`, `ID_SCREENSAVER`, `ID_WALLPAPER` | `PicasaMenuBar.qml:1779–1831`; a párbeszéd- és exportutak a `CreateDialogs.qml`-ben, illetve a kapcsolódó vezérlőkben. Külső írás/asztali integráció kattintással ellenőrizendő. |
| Eszközök | `ID_DUPES`, `ID_MOVE_DATABASE`, `ID_PASSPORT`, `ID_SAVESEARCH`, `ID_SEARCHTOKEN`, `ID_SELECTSTAR`, `ID_S_BLUE`, `ID_S_GREEN`, `ID_S_ORANGE`, `ID_S_PURPLE`, `ID_S_RED`, `ID_S_YELLOW`, `ID_TOOLS_BACKUP`, `ID_TOOLS_BUTTONMGR`, `ID_TOOLS_CONFIG_SCREENSAVER`, `ID_TOOLS_OPTIONS`, `ID_VIEWBYDATE`, `ID_VIEWBYNAME`, `ID_VIEWBYRECENT`, `ID_VIEWBYSIZE`, `ID_VIEWREVERSE`, `ID_VIEW_EARTH`, `ID_WRITE_XMP_FACES` | `PicasaMenuBar.qml:1835–2180`; az almenük elemei és jelzései ugyanebben a fájlban, a gazdaoldali kapcsolatok a `Main.qml`-ben. A Google Earth indítását és a lemezre író műveleteket kattintással kell ellenőrizni. |
| Súgó | `ID_HELP_ABOUT` | A `PicasaMenuBar.qml:2268–2274` az About PicasaPy ablakot nyitja. Az eredeti „About Picasa” funkciójának helyi megfelelője; az átnevezés szándékos. |

### Nem elérhető, hiányzó vagy platformhoz kötött parancsok

| Parancs | Állapot | Bizonyíték és teendő |
|---|---|---|
| `ID_FILE_EMAIL` | **Megvan, de a Fájl menüben nem működik.** | `PicasaMenuBar.qml:623` helyfoglaló; aktív `Ctrl+E` shortcut sincs. Maga az e-mail küldési út más felületen megvan: `Main.qml:1996–2047`, a `TrayBar.emailRequested` bekötése `Main.qml:3710`. Javasolt jegy: „A Fájl ▸ E-mail parancs ugyanazt a kijelölést küldje, mint a képtálca e-mail művelete”. |
| `ID_FILE_OPENINANEDITOR` | **Menüpont megvan, hatása hiányzik.** | `PicasaMenuBar.qml:526` helyfoglaló. A kép helyi menüjének „Open File” művelete `Main.qml:3788–3791` a képet a PicasaPy-nézőben nyitja meg; ez a forráskód alapján nem bizonyítja a külső szerkesztő indítását. Javasolt jegy: „A Fájl ▸ Open File(s) in an Editor nyissa meg a kijelölt fájlokat a külső szerkesztőben”. A `Ctrl+Shift+O` helyi menüfelirat önmagában nem bizonyítja ezt a hatást. |
| `ID_PICTURE_VIEW`, `ID_PICTURE_UNHIDE`, `ID_PICTURE_RESET_FACES` | **A felső Kép menüben megvan, de nem érhető el; a funkció másik menüútban megvan.** | Felső menü: `PicasaMenuBar.qml:1660,1754,1759` helyfoglalók. A kép helyi menüjének „View and Edit”, dinamikus Hide/Unhide és Reset Faces sorai aktívak: `PhotoContextMenu.qml:142–148,299–304,444–447`; a nézőben is van Reset Faces: `ViewerContextMenu.qml:229–231`. A művelet hiánya nem állítható, csak a felső menü elérési útjáé. |
| `ID_FACES` | **Hiányzik a Film almenüből.** | Az eredeti bemenete a kijelölt arcok köre (`picasa-menu-parancsok-viselkedes.md` §30); a `PicasaMenuBar.qml:1816–1827` csak a „New Movie…” parancsot tartalmazza. Javasolt jegy: „A Film almenü készítsen filmet a kijelölésben lévő arcokból”. |
| `ID_FACESRANDOM` | **Eredeti menütétel hiányzik; az egyenértékűség nyitott.** | Az eredeti a People Albums-ból indít filmet (`picasa-menu-parancsok-viselkedes.md` §30). A `CreateDialogs.qml:40–45` tartalmaz People-album sorokból filmet indító belépőt, de nem bizonyítja, hogy ez az eredeti „From People Albums…” kiválasztási szabályával azonos. Ne nyissunk fejlesztési jegyet az egyenértékűség tisztázása előtt. |
| `ID_HELP_KEYBOARD_SHORTCUTS` | **Jelenleg helyfoglaló; az eredeti szolgáltatás szándékosan nem cél.** | `PicasaMenuBar.qml:2190`. Az eredeti művelet a megszűnt Picasa súgó-webhelyet nyitotta (`picasa-menu-parancsok-viselkedes.md` §22). A helyi `runtime\shortcuts.xml` hiányát a §22 és a #442 már külön nyitott kérdésként rögzíti; ez nem azonos az eredeti webes paranccsal. |
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
| Album | Leírás, kijelölés, indexkép-frissítés és HTML export aktív; Delete Album, Add name tags és Sort Album By helyfoglaló; Online Actions és feltöltések nyugdíjazottak. | `AlbumContextMenu.qml:51–138`; eredeti 13 azonosító/12 felirat: `ui-audit-context-menus.md` A.2 és `picasa-menu-parancsok-viselkedes.md` §32. |
| Gyűjtemény (`Collection`) | Rename/Remove aktív felhasználói gyűjteményen; jelszó csak a beépített Rejtett mappák gyűjteménynél aktív, másutt helyfoglaló. | `CollectionContextMenu.qml:26–45`; a régi `ui-audit-context-menus.md` §4 „teljesen hiányzik” állítása elavult. |
| Emberek album | Select All és Clear Selection aktív; Delete/Edit People Album helyfoglaló. | `PeopleAlbumContextMenu.qml:26–46`. |
| Bal oldali lista (`AlbumList`) | Négy rendezési mód és fordítás, személyrendezés, egyszerűsített fa él; Show Thumbnails, Shortcuts és Desktop helyfoglaló; Windows gyökérváltók Linuxon nem jelennek meg. | `FolderListContextMenu.qml:45–225`; eredeti táblázat `ui-audit-context-menus.md` A.2. A helyi menü „Desktop” eleme nem azonos a működő Nézet ▸ Desktop paranccsal. |
| Képtálca (`Tray`) | A hét műveletnek van aktív `onTriggered` útja. | `TrayContextMenu.qml:45–95`; eredeti gyorsbillentyűk `picasa-gyorsbillentyuk.md` §4. Az eredeti `Ctrl+H` nincs aktív QML `Shortcut`-ként bekötve és a mai menüfeliratban sincs feltüntetve. A többi billentyű fókusz-/tálcakijelölés-hatása kattintással ellenőrizendő. |
| Szövegmező (`Address`) | Undo, Cut, Copy, Paste, Delete, Select All aktív, állapottól függően tiltott; Auto-Complete helyfoglaló. | `TextFieldContextMenu.qml:41–88`; az eredeti héttételes lista `picasa-menu-parancsok-viselkedes.md` §19. |
| Címke (`Tags`) | A három művelet aktív. | `TagContextMenu.qml:21–46`; a gazda `TagsPanel.qml`-ben van bekötve. |
| Kollázs | Az egykép-, csoport- és vászonmenük kezelői a kollázsvezérlőre vezetnek; a műveleteket témaképesség és kijelölés szerint tiltják. | `CollageContextMenus.qml:102–282`; részletes táblák `kollazs-panel-ui-spec.md` §7.6. A képesség-feltételes elemek végpontjai kattintással nem voltak próbálva. |

### Gyorsbillentyűk

Az eredeti **9 menüépítőben 44 gyorsbillentyűs rekord** van (`picasa-gyorsbillentyuk.md` §4). Az aktuális QML `Shortcut`-jai a `Main.qml`, `PicasaMenuBar.qml`, `PhotoViewer.qml` és más nézetek között oszlanak meg; a régi §6 „20 Shortcut” összesítése és több státusza már nem aktuális.

| Billentyűcsoport | Mai állapot | Bizonyíték |
|---|---|---|
| `Ctrl+A/D/I`, `Ctrl+C/X/V`, `Ctrl+S`, `Ctrl+R`, `Ctrl+Shift+R`, `Ctrl+Shift+H/V`, `Ctrl+3`, `Ctrl+4`, `Ctrl+T`, `Ctrl+F`, `Ctrl+K`, `Ctrl+F6/F7/F8`, `Ctrl+1/2`, `Ctrl+M/O/N`, `Ctrl+P`, `Ctrl+Shift+P`, `Ctrl+Shift+S`, `F1`, `Shift+F1`, `F2`, `Alt+Return`, `Ctrl+Return`, `Delete`, `Ctrl+Delete` | A forrásban aktív QML kötés látható; `Ctrl+Shift+H/V`, `Ctrl+F`, `Ctrl+K` és `Ctrl+3` tehát nem hiányzóként kezelendő. | `Main.qml:919–998`, `:1068–1441`; `PicasaMenuBar.qml:389–460`; néző- és rácsesemények `PhotoViewer.qml:1368–1389`, `LightboxFeed.qml:356–391`. |
| `Ctrl+5` | **Állandóan tiltott.** | `Main.qml:1358–1362` és `PicasaMenuBar.qml:874–879`. |
| `Ctrl+H` (tálca: kijelölés megtartása) | **Nincs aktív kötés.** | Az eredeti tálca-rekord a `picasa-gyorsbillentyuk.md` §4-ben `0x00732ee0`; a mai `TrayContextMenu.qml` művelete nincs ezzel a szekvenciával feliratozva, a teljes QML `sequence:` leltárban nincs `Ctrl+H`. Javasolt jegy: „A Ctrl+H tartsa meg a kijelölést a képtálcán”. |
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
| A Fájl ▸ Open File(s) in an Editor indítson külső szerkesztőt | Eredeti: `ID_FILE_OPENINANEDITOR` / `Ctrl+Shift+O`. Nálunk: helyfoglaló; a „Open File” a belső nézőt nyitja. | Kijelölésből a beállított külső szerkesztő indul; hiányzó program és több fájl esetén is dokumentált visszajelzés van. |
| A Film almenü készítsen filmet a kijelölt arcokból | Eredeti: `ID_FACES`. Nálunk: a Film almenüben nincs ilyen tétel. | A parancs a kijelölt arcokat a film bemeneteként adja át, és a film export végigfut. |
| A Nézet ▸ Edit View és Kép ▸ View and Edit menüpont nyissa meg a kijelölt képet | Eredeti: `ID_VIEW_PICTURE` és `ID_PICTURE_VIEW`. Nálunk: mindkét menüsori tétel helyfoglaló, bár a `Ctrl+3` és a képrács helyi menüje más belépő. | Mindkét felső menüsori tétel ugyanazt a dokumentált megnyitási műveletet indítja, csak a megfelelő kijelölési/fókusz-kapuval. |
| A Kép ▸ Unhide állítsa láthatóra a kijelölt képeket | Eredeti: `ID_PICTURE_UNHIDE`. Nálunk: a felső menüsor tétele helyfoglaló; a helyi menü állapotfüggő Hide/Unhide művelete él. | A felső menüsori parancs a rejtett kijelölést megjeleníti, nem csak átvált egy másik állapotba. |
| A Kép ▸ Reset Faces használja a meglévő arc-visszaállítási műveletet | Eredeti: `ID_PICTURE_RESET_FACES`. Nálunk: felső menü helyfoglaló, a Photo/Viewer helyi menükben a művelet aktív. | A felső menütétel ugyanazt a kijelölésre alkalmazott arc-visszaállítási kezelőt hívja, mint a helyi menü. |
| A Ctrl+H tartsa meg a képtálca kijelölését | Eredeti: `Tray::Ctrl+H`. Nálunk: a menüművelet létezik, aktív shortcut nem látható. | Ctrl+H a tálcára fókuszálva ugyanazt a tartós kijelölés-állapotot állítja be, mint a helyi menü. |
| Az Eszközök ▸ Adjust Date and Time módosítsa a dátumot | Eredeti: `ID_TOOLS_ADJUST_TIMESTAMP`; a viselkedés két módját a `picasa-menu-parancsok-viselkedes.md` §3 írja le. Nálunk: `PicasaMenuBar.qml:1888` helyfoglaló. | Mindkét eredeti mód működik a kijelölésen, az eredeti fájl/metaadat mentési célja külön dokumentált. |
| A Configure Photo Viewer nyissa meg a néző beállításait | Eredeti: `ID_TOOLS_CONFIG_SLINGSHOT`. Nálunk: `PicasaMenuBar.qml:1872` helyfoglaló. | A menütétel a néző tényleges beállítófelületét nyitja meg, és a választások újraindítás után is érvényesek. |
| A People Manager kezelje az Emberek albumokat | Eredeti: `ID_TOOLS_CONTACTMGR`. Nálunk: `PicasaMenuBar.qml:1846` helyfoglaló; People panel léte önmagában nem bizonyít Manager-paritást. | A név-/albumkezelési műveletek az eredeti menüből elérhetők és a dokumentált adatokra írnak. |
| A Kép ▸ Show/Hide Text működjön a kijelölt képeken | Eredeti: `ID_PICTURE_SHOW_TEXT`, `ID_PICTURE_HIDE_TEXT`. Nálunk: mindkét menüpont helyfoglaló (`PicasaMenuBar.qml:1730–1731`). | A két parancs a kijelölt képek szövegfedvényét az eredeti állapotfeltételekkel kapcsolja. |
| A Nézet ▸ Show Edit Controls kapcsolja a szerkesztő vezérlőit | Eredeti: `ID_VIEW_EDIT`. Nálunk: `PicasaMenuBar.qml:852` helyfoglaló. | A menüpont láthatóvá/rejtetté teszi a szerkesztő kezelősávját és a kiválasztott állapot újranyitáskor következetes. |
| Folytassa vagy zárja le a 16 bites ditherelt megjelenítési mód munkáját | Eredeti: `ID_VIEW_16`, pontos képpont-átalakítása a `picasa-megjelenitesi-modok.md` §5.3-ban mérve. Nálunk: `PicasaMenuBar.qml:1015–1022` helyfoglaló; a QML-komment #1658-ra hivatkozik. | A #1658 meglévő jegy státuszát ellenőrizni; ha nyitott, a `ID_VIEW_16` alkalmazza a leírt ditherelést; ha nem cél, ezt indokoltan dokumentálni. |

Nem javaslok fejlesztési jegyet a `Small Pictures` eredeti jelentésének, a People Albums-film belépőjének egyenértékűségének vagy a kimenő fájlhúzásnak a tisztázása előtt.

## Új kutatási kérdések

| Kérdés | Hol keresd |
|---|---|
| Mit jelent pontosan az eredeti `ID_VIEW_SMALL` parancs, és melyik nézetben milyen képméretet állít? | `picasa-menu-parancsok-viselkedes.md` menüleírása; eredeti `ID_VIEW_SMALL` parancs- és gyorsbillentyű-lánca a binárisban. |
| Az `ID_FACESRANDOM` eredeti „From People Albums…” bemeneti szabálya ugyanaz-e, mint a jelenlegi People-album fejlécéről nyíló `openMovieForRows`? | `picasa-menu-parancsok-viselkedes.md` §30; `CreateDialogs.qml:40–45`; eredeti film-menü eseménylánc, ha a meglévő bináris jegyzetek nem döntik el. |
| A Picasa 3.9 kimenő `DoDragDrop`-ja fájlokat/URI-kat vagy Picasa-specifikus elemet adott át, és ez reprodukálható-e Qt/QML draggel? | Bináris eredeti: `picasa-eger-es-kijeloles.md` §5, §14 és `0x00aa1fb0`; jelenlegi `ThumbDelegate.qml:279–305`; kézi asztali próba. |
| A 44 helyi gyorsbillentyűből melyiket veszi át az egyes menü fókusza, nem csak mutatja a menüfelirat? | `picasa-gyorsbillentyuk.md` §4; aktuális `Main.qml`/`PhotoViewer.qml` shortcut és egyes helyi menük fókuszában végzett kézi próba. |

## Nyitott

- A kattintással és tiszta profillal ellenőrizendő hatások: minden menüút valós UI-viselkedése; külső szerkesztő, e-mail, nyomtató, Google Earth, fájltörlés/export; helyi gyorsbillentyűk fókusz szerinti célzása.
- A mai `main` frissessége: a záró státusz a helyi tracking ref szerint három commit lemaradást jelez; GitHub/hálózat tiltott volt, így a lemaradás tartalma és az upstream frissessége nincs ellenőrizve.
- Kimenő drag-to-desktop paritás: `NINCS MEG` a QML-forrásban kimutatható OS-fájl payload; valódi desktop-próba nem történt.
- Az eredeti „Small Pictures” pontos hatása és az `ID_FACESRANDOM` jelenlegi film-belépőjének egyenértékűsége.
- A 4. réteg statikus tiltáslistája nem bizonyítja, hogy minden kapcsolódó szolgáltatás vagy backend működik.

## Módosított fájlok

- `docs/specs/paritas-ellenorzes.md` — új statikus paritás-ellenőrzés a 2–4. rétegre, a bizonyítékokkal, eltérésekkel, jegyjavaslatokkal és nyitott kérdésekkel.
