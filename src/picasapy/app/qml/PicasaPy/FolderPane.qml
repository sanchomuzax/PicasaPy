import QtQuick
import QtQuick.Window

// Bal oldali gyűjtemény-hasáb — Picasa "Folder List" gyökere (#320): öt
// önálló, csukható gyűjtemény (Albumok/Emberek/Projektek/Mappák/Egyéb),
// mindegyik saját fejléccel; csak a Mappák gyűjtemény tagolt évszám-
// szakaszokra (ld. docs/specs/ui-audit-mainwindow.md, mappafa szakasz).
Rectangle {
    id: pane
    //: #3463: a Shift+F1 fejezete (ld. `Main.qml` `helpTopicUnderCursor`)
    property string helpTopic: "features/konyvtar.md"
    color: Theme.panelBg

    // #384: constants.ui alist_selcolor_win/alist_scatcolor (#25648B) —
    // a VALÓDI kijelölés sötétebb, mint a hover/jelölő tónus
    // (Theme.panelSelection = #83a7bd, alist_hicolor_win). A Theme.qml-ben
    // MÉG NINCS erre saját token (hot file, ld. jelentés:
    // Theme.panelSelectionActive) — amíg az integrátor fel nem veszi, itt
    // helyi állandóként él; a csere csak ezt a sort érinti.

    property alias foldersModel: paneContent.folderListModel
    property string selectedPath: ""
    property bool starredActive: false
    property bool searchActive: false
    property string searchQuery: ""
    property int searchResultCount: 0
    readonly property string searchResultsAlbumText: searchActive
        ? qsTr("Search results for \"%1\" (%2)")
            .arg(searchQuery).arg(searchResultCount)
        : ""
    // #9: az albumok listája ({token, name, count} elemek) és az éppen
    // kiválasztott album token-je (a kijelölés-kiemeléshez)
    property var albumsModel: []
    property string selectedAlbumToken: ""
    // #320: a felhasználó egyéni gyűjteményei ({name, folders} elemek) —
    // a controller.customCollections tükre, a mappasor jobbklikk-menüjéhez
    property var customCollectionsModel: []
    // #26: a bal hasáb Emberek gyűjteménye ({name, count} elemek) és az
    // éppen kiválasztott személy neve (a kijelölés-kiemeléshez) — az
    // albumsModel/selectedAlbumToken mintáját követi.
    property var peopleModel: []
    property string selectedPersonName: ""
    // #26 (3. lépcső): a SAJÁT arcfelismerés „Névtelenek" sora — a
    // People-gyűjteményben él (a Picasa is a személyek mellett mutatta),
    // csak akkor látszik, ha van legalább egy szkennelt, még névtelen arc
    // (modell nélkül ez a szám mindig 0 — a sor eleve rejtve marad).
    property int unnamedFaceCount: 0
    // #449: a háttérben futó arc-beolvasás haladása (−1 = nem fut). Az
    // eredeti Picasa ezt AZ ALBUMLISTÁBAN mutatta, nem modális ablakban —
    // a felhasználót semmi nem blokkolta közben.
    property int faceScanPercent: -1
    property bool unnamedFacesActive: false
    // #26: a „Mellőzött emberek" album (`CAlbumLabel::Ignored`) — az
    // eredetiben is ALBUM volt, tehát látszania kell, ha van tartalma
    property int ignoredFaceCount: 0
    // #457: „Exportált képek" — `[{path, name}]`, az exportált célmappák
    property var exportedFolders: []
    // #1029: a Projektek gyűjtemény mappái — `[{path, name, count}]`, a
    // `.picasa.ini` `[Picasa]` `P2category=Projects (internal)` kulcsából
    // (Kollázsok, Filmek, Rögzített videoklipek, …)
    property var projectFolders: []
    property bool ignoredFacesActive: false
    // #5341: a People-csoport LÁTHATÓ sorai. Az eredetiben (job-210, 13. és
    // 16. kép) a Névtelenek és a mellőzött sor ugyanazon a helyen váltja
    // egymást: mellőzés után a normál nézetben csak a Névtelenek látszik, a
    // mellőzött nézetben csak a mellőzött sor. A fejléc a látható sorokat számolja.
    readonly property bool unnamedSlotShown: !ignoredFacesActive
        && (unnamedFaceCount > 0 || faceScanPercent >= 0)
    readonly property bool ignoredSlotShown: ignoredFacesActive
    // #730: a hasáb egységes sormagassága. A mappalista magasságát ebből és
    // a sordarabszámból számoljuk (a lista a görgethető hasábban a teljes
    // tartalmát kirakja), ezért nem maradhat a delegate-be égetett szám.
    readonly property int rowHeight: 22
    // #702: a Mappák gyűjtemény MÁSODIK nézetmódja — a hierarchikus fa. Az
    // eredeti Picasa bal hasábjának két, egymást kizáró módja van
    // (`thumbui/hviewtoggle`): a lapos lista (`eMenuView::ID_VIEW_FOLDERS`)
    // és a fa (`eMenuView::ID_VIEW_ALL`) — ld. ui-audit-mainwindow.md 1.4/1.7.
    // A `hierarchyController` a `FolderHierarchyController` példánya (a
    // gazda köti be). #1454: a nézetmód is ONNAN jön — a `Nézet ▸
    // Mappanézet` „Egyszerű mappanézet"/„Fanézet" tételpárja azt állítja.
    // A kötés felülírható (a hasábot önmagában rajzoló próbák élnek vele),
    // vezérlő nélkül pedig a lapos lista az alapállapot.
    property var hierarchyController: null
    // #1572: a `!== undefined` a hiányzó TULAJDONSÁGRA véd — a próbák
    // stub-vezérlőjén nincs rajta. Az őr: scripts/qml_undefined_or.py
    property bool treeViewMode:
        (pane.hierarchyController && pane.hierarchyController.treeView !== undefined)
            ? pane.hierarchyController.treeView : false

    //: #1407 (spec 4.2 / 4.5/c): a Mappák gyűjtemény fejléce a HASÁB
    //: GYÖKERÉT nevezi meg — az eredetiben pontosan KÉT rögzített
    //: erőforrás-szöveg van rá (`ViewRoot::AllFolders`, `ViewRoot::All`), a
    //: három rendszermappa pedig a feloldott mappa SAJÁT nevét mutatja
    //: (`0x00575483  mov esi, eax`), amihez nincs erőforrás-szöveg.
    //:
    //: ⚠️ A két rögzített szöveget SZÁNDÉKOSAN itt fordítjuk, nem a
    //: vezérlőben: a `FolderHierarchyController` nem tölt be fordítást, a
    //: `rootLabel` property-je a mért leképezés gépi tanúja (a próbái azt
    //: olvassák). A mappa-név viszont onnan jön — az nem fordítható.
    readonly property string folderRootLabel: {
        var token = (pane.hierarchyController
                     && pane.hierarchyController.viewRoot !== undefined)
                    ? pane.hierarchyController.viewRoot : "flat"
        if (token === "flat")
            return qsTr("Default View")
        if (token === "all" || token === "watched")
            return qsTr("My Computer")
        return (pane.hierarchyController
                && pane.hierarchyController.rootLabel !== undefined)
               ? pane.hierarchyController.rootLabel : qsTr("My Computer")
    }
    // a fa sorainak száma — a magasságszámításhoz (#305 null-őrrel)
    //: #2049: „Indexképek megjelenítése a könyvtárban" — ugyanaz a
    //: kapcsoló, mint a `Nézet ▸ Mappanézet` menü tételéé. A
    //: `!== undefined` a próbák stub-vezérlőjére véd (#1572).
    readonly property bool albumThumbs:
        (pane.hierarchyController && pane.hierarchyController.albumThumbs !== undefined)
            ? pane.hierarchyController.albumThumbs : false

    // #3681: a mentés-üzemmód SZŰRŐ-módja — a `BackupHost` állítja, amíg a
    // mentés-panel nyitva van. Aktív módban a hasáb (lapos lista ÉS fa,
    // amelyik éppen látszik) a MÉG EL NEM MENTETT mappákra szűkül, pipával
    // — a `BackupFolderStrip` korábbi külön sávja helyett, az eredeti
    // Picasa `backuptext2`/`backuptext3` viselkedését követve.
    property bool mentesSzuroAktiv: false
    //: {mappa, nev, darab, fajlok, bajt} sorok — a
    //: `BackupController.mentetlenMappakLekerese()` háttérben számolt
    //: eredménye (`BackupHost.mentetlenek`)
    property var mentesMentetlenMappak: []
    //: a bepipált mappák útjai (`BackupHost.pipaltMappak`)
    property var mentesPipaltMappak: []
    //: egy mappa pipája vált (a lapos listán vagy a fán)
    signal mentesPipaldKert(string mappa, bool be)
    //: a mentetlen mappák listája háttérszálon készül (`BackupHost.
    //: mappakToltodnek`) — addig a hasáb a „Számítás…" feliratot mutatja
    property bool mentesToltodnek: false
    //: van-e kiválasztott mentési készlet — nélküle a „minden el van
    //: mentve" felirat hamis volna
    property bool mentesVanKeszlet: false
    //: gyors tagság-ellenőrzéshez — csak az útvonalak, a `mentesMentetlenMappak` sorrendjében
    readonly property var mentesMentetlenUtak:
        pane.mentesMentetlenMappak.map(function (sor) { return sor.mappa })
    //: #3776: a lapos lista összehasonlító kulcsa — a `BackupController`
    //: tiszta függvényét hívja, hogy egy eltérő betűzésű Windows-gyökér
    //: alatt se okozzon pontos-egyezés-hibát a `mentesTerkep` keresése.
    function mentesKulcs(path) {
        return (typeof backupController !== "undefined" && backupController)
            ? backupController.mentesKulcs(path) : path
    }
    //: kulcs (`mentesKulcs`) → a mentetlen mappa sora (darab, fájlnevek)
    readonly property var mentesTerkep: {
        var terkep = {}
        pane.mentesMentetlenMappak.forEach(function (sor) {
            terkep[pane.mentesKulcs(sor.mappa)] = sor
        })
        return terkep
    }
    //: a mentetlen mappa fájlnevei a sor végén (ami elfér) — sok fájlnál
    //: a vezérlő csak az első néhány nevet adja, a folytatást „…" jelzi
    //: (a megszűnt külön mappasáv, #3594, alakjában)
    function mentesFajlSor(path) {
        var sor = pane.mentesTerkep[pane.mentesKulcs(path)]
        if (!sor) return ""
        return sor.fajlok.join(", ")
            + (sor.darab > sor.fajlok.length ? ", …" : "")
    }
    //: a lapos listán TÉNYLEGESEN kirajzolt mentetlen sorok száma — csak az
    //: a mappa kap sort, amely a lista modelljében is szerepel
    readonly property int mentesLaposSorok: {
        var modell = paneContent.folderListModel
        //: a modell változására is számoljon újra
        var osszes = paneContent.folderListView.count
        if (!pane.mentesSzuroAktiv || !modell || osszes === 0) return 0
        return pane.mentesMentetlenUtak.filter(function (ut) {
            return modell.rowOfPath(ut) >= 0
        }).length
    }
    //: a szűrő-mód állapotfelirata: számolás közben, üres készletnél és
    //: készlet nélkül a hasáb ne maradjon szó nélkül üres
    readonly property string mentesAllapotSzoveg:
        !pane.mentesSzuroAktiv ? ""
        : !pane.mentesVanKeszlet ? qsTr("Create a Set or use an existing one")
        : pane.mentesToltodnek ? qsTr("Calculating…")
        //: `thumbui/lightbox_bgtext` Text2 — az eredeti mentés-ágának szövege
        : pane.mentesMentetlenMappak.length === 0
          ? qsTr("All Files are backed up in this set") : ""

    signal folderChosen(string path)
    // #3461: a Rejtett mappák fejlécének „Jelszó megadása/módosítása…" tétele
    signal hiddenPasswordRequested()
    signal collectionPasswordRequested(string collectionName)
    signal starredChosen()
    signal albumChosen(string token)
    signal personChosen(string name)
    signal unnamedFacesChosen()
    signal ignoredFacesChosen()
    // #455: fogd-és-vidd az albumlistára — új album, illetve meglévőbe
    // sorolás. A tényleges munkát a gazda végzi (a névkérő párbeszéd és a
    // kijelölés is ott van).
    signal newAlbumPhotosDropped(var photoRows)
    signal photosDroppedOnAlbum(string token, var photoRows)
    // #5007: a kijelölt rácsképek útvonalaihoz tartozó sorok ejtése egy
    // mappára. A gazda a lemezműveletet a FileOpsControllerre bízza.
    signal photosDroppedOnFolder(string path, var rows)
    signal folderDroppedOnFolder(string sourcePath, string targetPath)

    // #320: a controller friss gyűjtemény-listájának lekérése — a
    // Component.onCompleted-en kívül minden create/rename/delete/move
    // után is meghívandó (#305 null-őrrel).
    function refreshCustomCollections() {
        if (!controller) return
        pane.customCollectionsModel = controller.customCollections
    }

    // #320: a mappasor jobbklikk-menüjének megnyitása — a `MouseArea`
    // delegate-ből (Repeater/ListView-elem, findChild-dal el nem érhető,
    // ld. MEMORY 2026-07-31) kiszervezve pane-szintű, névvel hívható
    // függvénybe, hogy közvetlenül (a valódi kattintás szintetizálása
    // nélkül) tesztelhető legyen.
    // #1595: a Mappa MENÜSÁV-menü ugyanazokat a műveleteket kínálja, mint a
    // mappa helyi menüje — csak a MEGNYITOTT mappára. A párbeszédek és a
    // megerősítések itt élnek, ezért a menüsáv is innen hívja őket: egy
    // művelet, egy út (különben két helyen kellene ugyanazt a
    // megerősítés-szöveget karbantartani).
    function mozgatasMappara(path) {
        if (!path) return
        pane._movingFolder = path
        paneMenus.moveFolderDialog.open()
    }

    function torlesLomtarba(path) {
        if (!path) return
        paneMenus.deleteFolderConfirm.pendingPath = path
        paneMenus.deleteFolderConfirm.message = qsTr(
            "Are you sure you want to move the folder \"%1\" and its "
            + "contents to the Recycle Bin?").arg(
                path.substring(path.lastIndexOf("/") + 1))
        paneMenus.deleteFolderConfirm.open()
    }

    function eltavolitasAPicasabol(path) {
        if (!path) return
        paneMenus.folderContextMenu.folderPath = path
        paneMenus.removeFolderConfirm.open()
    }

    //: #422/#3460: a mappa `album.fen` párbeszéde (név, dátum, hely,
    //: leírás). Két belépője van: a mappa helyi menüje és a menüsor
    //: Mappa ▸ Leírás szerkesztése… tétele.
    function openFolderDescription(path) {
        if (!path)
            return
        //: #3173: a párbeszéd két használatú — a mappa-ág visszaállítja
        paneMenus.folderPropertiesDialog.mode = "folder"
        paneMenus.folderPropertiesDialog.newFolderCreation = false
        paneMenus.folderPropertiesDialog.folderPath = path
        paneMenus.folderPropertiesDialog.folderName =
            path.substring(path.lastIndexOf("/") + 1)
        paneMenus.folderPropertiesDialog.currentDate =
            controller ? controller.folderDateOverride(path) : ""
        paneMenus.folderPropertiesDialog.currentDescription =
            controller ? controller.folderDescriptionOf(path) : ""
        paneMenus.folderPropertiesDialog.folderLocation = ""
        paneMenus.folderPropertiesDialog.currentMusicEnabled =
            controller && controller.folderMusicEnabled
                ? controller.folderMusicEnabled(path) : false
        paneMenus.folderPropertiesDialog.currentMusicFile =
            controller && controller.folderMusicFile
                ? controller.folderMusicFile(path) : ""
        paneMenus.folderPropertiesDialog.open()
    }

    // #4534: a rács „Mappa felosztása itt” parancsa ugyanazt a
    // tulajdonságablakot használja, de új testvérmappa metaadatait kéri.
    function openSplitFolderHere(paths, isoDate) {
        if (!paths || paths.length === 0 || !isoDate)
            return
        paneMenus.folderPropertiesDialog.mode = "folder"
        paneMenus.folderPropertiesDialog.newFolderCreation = true
        paneMenus.folderPropertiesDialog.splitPaths = paths.slice()
        paneMenus.folderPropertiesDialog.folderPath = ""
        paneMenus.folderPropertiesDialog.folderName =
            paneMenus.folderPropertiesDialog.untitledFolderName
        paneMenus.folderPropertiesDialog.folderLocation = ""
        paneMenus.folderPropertiesDialog.currentDate = isoDate
        paneMenus.folderPropertiesDialog.currentDescription = ""
        paneMenus.folderPropertiesDialog.currentMusicEnabled = false
        paneMenus.folderPropertiesDialog.currentMusicFile = ""
        paneMenus.folderPropertiesDialog.open()
    }

    //: #4630: az Album menü az éppen megnyitott album tulajdonságait nyitja.
    function openAlbumDescription(token, name) {
        if (!token)
            return
        var adat = (controller && controller.albumProperties)
            ? controller.albumProperties(token) : {}
        paneMenus.folderPropertiesDialog.mode = "album"
        paneMenus.folderPropertiesDialog.newFolderCreation = false
        paneMenus.folderPropertiesDialog.albumToken = token
        paneMenus.folderPropertiesDialog.albumName =
            adat.name !== undefined ? adat.name : (name || "")
        paneMenus.folderPropertiesDialog.currentDate =
            adat.date !== undefined ? adat.date : ""
        paneMenus.folderPropertiesDialog.albumLocation =
            adat.location !== undefined ? adat.location : ""
        paneMenus.folderPropertiesDialog.currentDescription =
            adat.description !== undefined ? adat.description : ""
        paneMenus.folderPropertiesDialog.currentMusicEnabled =
            adat.use_music !== undefined ? adat.use_music : false
        paneMenus.folderPropertiesDialog.currentMusicFile =
            adat.music_file !== undefined ? adat.music_file : ""
        paneMenus.folderPropertiesDialog.open()
    }

    function openFolderContextMenu(path) {
        paneMenus.folderContextMenu.folderPath = path
        paneMenus.folderContextMenu.customCollections = pane.customCollectionsModel
        if (controller) {
            // #1637: a tétel felirata állapotfüggő („Mappa elrejtése" ↔
            // „Megjelenítés"), tehát a menü NYITÁSAKOR kell megkérdezni.
            // A `!== undefined` a #1572-őr mintája.
            paneMenus.folderContextMenu.folderHidden =
                (controller.isFolderHidden !== undefined)
                    ? controller.isFolderHidden(path) : false
        }
        paneMenus.folderContextMenu.popup()
    }

    // #422: a bal panel saját menüjének megnyitása — a rendezési pipák
    // nyitáskor átveszik a vezérlő friss állapotát; a nézetpipák kötöttek.
    function openFolderListContextMenu() {
        if (controller) {
            // #461/3: a BAL HASÁB saját rendezése — az eredetiben ez a
            // menü (`AlbumList`) a hasábot rendezte, nem a rácsot
            paneMenus.folderListContextMenu.sortMode = controller.paneSort
            paneMenus.folderListContextMenu.sortReverse = controller.paneSortReverse
        }
        paneMenus.folderListContextMenu.popup()
    }

    // #422 (4. lépcső): az album / Emberek-album jobbklikk-menüje — a
    // sor-delegátumból (Repeater-elem) kiszervezve pane-szintű, névvel
    // hívható függvénybe, a mappa-menü mintájára
    function openAlbumContextMenu(token, name) {
        paneMenus.albumContextMenu.albumToken = token
        paneMenus.albumContextMenu.albumName = name
        paneMenus.albumContextMenu.popup()
    }
    function _askDeleteAlbum(token, name) {
        if (!token) return
        paneMenus.deleteAlbumConfirm.pendingToken = token
        paneMenus.deleteAlbumConfirm.ask(
            "",
            qsTr("Are you sure you want to delete the album \"%1\"?")
                .replace("%1", name))
    }
    function openPeopleAlbumContextMenu(name) {
        paneMenus.peopleAlbumContextMenu.personName = name
        paneMenus.peopleAlbumContextMenu.popup()
    }

    // #422 (utolsó menü): a felhasználói gyűjtemény jobbklikk-menüjének
    // megnyitása — az album-menü mintájára, pane-szintű, névvel hívható
    // függvényben (tesztelhetőség).
    function openCollectionContextMenu(name) {
        paneMenus.collectionContextMenu.collectionName = name
        paneMenus.collectionContextMenu.hiddenCollection = false
        paneMenus.collectionContextMenu.popup()
    }
    // #3461: a beépített „Rejtett mappák" csomópont fejlécének helyi menüje
    // — ugyanaz a Collection menü, de ott a jelszó-tétel él.
    function openHiddenCollectionContextMenu(name) {
        paneMenus.collectionContextMenu.collectionName = name
        paneMenus.collectionContextMenu.hiddenCollection = true
        paneMenus.collectionContextMenu.popup()
    }

    // #422: melyik gyűjtemény átnevezése fut éppen a newCollectionDialog-on
    // keresztül — üres string esetén a dialógus a régi
    // "létrehozás" ágon fut (createCollection + esetleg
    // moveFolderToCollection), nem üres esetén az átnevezés ágon
    // (renameCollection). A newCollectionDialog egyetlen példány, ezt a
    // property-t kell megnézni a created(name) jelre.
    property string _renamingCollection: ""
    property string _movingFolder: ""

    // Gyűjtemény-csukottság — kezdőérték a collections.py
    // DEFAULT_COLLAPSED-jét tükrözi (controller hiányában is ésszerű).
    property bool albumsCollapsed: false
    property bool peopleCollapsed: true
    property bool projectsCollapsed: true
    property bool foldersCollapsed: false
    property bool otherCollapsed: true

    // #476: a felhasználói gyűjtemények (customCollectionsModel) csukottsága
    // — név → bool térkép, csak memóriában (a controller-perzisztálásra még
    // nincs API, ellentétben a beépített öt gyűjteménnyel fent).
    property var collapsedCollections: ({})

    function isCustomCollectionCollapsed(name) {
        return pane.collapsedCollections[name] === true
    }

    // A toggleCollection mintáját követi, de a `next` állapotot új
    // objektumként írja vissza — a QML csak referenciaváltásra frissíti a
    // Repeater-kötéseket, helyben módosított property var-ra nem.
    function toggleCustomCollection(name) {
        var next = {}
        for (var key in pane.collapsedCollections) next[key] = pane.collapsedCollections[key]
        next[name] = !pane.isCustomCollectionCollapsed(name)
        pane.collapsedCollections = next
    }

    // #461: a gyűjtemény bezárása/megnyitása. A megnyitás mindig azonnali;
    // a BEZÁRÁS előtt viszont — ha utána egyetlen kép sem maradna a rácsban
    // — az eredeti figyelmeztetése jön, „ne kérdezze újra" kapcsolóval
    // (a bináris `DoNotAskOnLastCollectionClose` kulcsának megfelelője).
    function requestCollectionCloseToggle(name, currentlyClosed) {
        if (typeof controller === "undefined" || !controller) return
        if (currentlyClosed) {
            controller.setCollectionClosed(name, false)
            return
        }
        if (controller.closingHidesEverything(name)) {
            paneMenus.closeCollectionConfirm.pendingName = name
            // a szöveg EGY darabban: a `qsTr` kulcsa a teljes string, és a
            // QML-beli összefűzés (`"a" + "b"`) miatt a kulcs nem egyezne a
            // fordításfájl forrásával (a test_i18n_completeness ezt fogja meg)
            paneMenus.closeCollectionConfirm.ask(
                "view/dontAskOnLastCollectionClose",
                qsTr("You are about to close your last collection. No pictures will be shown in the thumbnail area. Do you want to continue?\n\nTo open a collection, double-click its name or click the icon next to it."))
            return
        }
        controller.setCollectionClosed(name, true)
    }

    Component.onCompleted: {
        // #305: null-őr — a controller a QML-engine leépítésekor
        // átmenetileg null lehet (itt: induláskor még nem biztos, hogy
        // kötve van, ha a teszt csak magát a komponenst tölti be).
        if (!controller) return
        pane.albumsCollapsed = controller.isCollectionCollapsed("albums")
        pane.peopleCollapsed = controller.isCollectionCollapsed("people")
        pane.projectsCollapsed = controller.isCollectionCollapsed("projects")
        pane.foldersCollapsed = controller.isCollectionCollapsed("folders")
        pane.otherCollapsed = controller.isCollectionCollapsed("other")
        pane.refreshCustomCollections()
    }

    // #320: a gyűjtemény-lista kívülről (más ablakból, pl. a Mappakezelőből
    // induló módosítás) is változhat — a controller jelzésére frissítünk.
    Connections {
        target: controller
        function onCustomCollectionsChanged() { pane.refreshCustomCollections() }
    }

    // Egy gyűjtemény nyitása/csukása: a helyi állapotot azonnal frissíti
    // (a fejléc-nyíl és a tartalom eltűnése ne várjon a controllerre), a
    // perzisztálás a controlleren át fut (#305: null-őrrel).
    function toggleCollection(name) {
        var next
        if (name === "albums") { pane.albumsCollapsed = !pane.albumsCollapsed; next = pane.albumsCollapsed }
        else if (name === "people") { pane.peopleCollapsed = !pane.peopleCollapsed; next = pane.peopleCollapsed }
        else if (name === "projects") { pane.projectsCollapsed = !pane.projectsCollapsed; next = pane.projectsCollapsed }
        else if (name === "folders") { pane.foldersCollapsed = !pane.foldersCollapsed; next = pane.foldersCollapsed }
        else if (name === "other") { pane.otherCollapsed = !pane.otherCollapsed; next = pane.otherCollapsed }
        else return
        if (controller) controller.setCollectionCollapsed(name, next)
    }

    // Kurzor/görgő léptetés a könyvtárelemek között (#77): a szomszéd
    // mappát a modell adja (az évszám-sorokat átugorva), a kiválasztás a
    // szokásos folderChosen-úton fut. A görgő itt nem görget, hanem a
    // kijelölt mappát lépteti (Picasa-viselkedés); a touchpad kis deltáit
    // egy teljes fokozatig (120) gyűjtjük.
    function stepFolder(delta) {
        //: #3681: mentés-szűrő módban a sorra kattintás pipál, nem nyit meg
        //: mappát — a léptetés sem nyithat meg (kiszűrt) mappát
        if (pane.mentesSzuroAktiv) return
        if (!paneContent.folderListModel) return
        var target = paneContent.folderListModel.neighborFolder(pane.selectedPath, delta)
        if (target !== "" && target !== pane.selectedPath)
            pane.folderChosen(target)
    }
    property real wheelAccum: 0
    function wheelStep(delta) {
        wheelAccum += delta
        while (wheelAccum <= -120) { wheelAccum += 120; stepFolder(1) }
        while (wheelAccum >= 120) { wheelAccum -= 120; stepFolder(-1) }
    }
    // #730: a hasáb görgetése óta a mappalista a teljes tartalmát kirakja,
    // tehát ő maga nem görget — a látótérbe hozás a hasáb közös
    // `paneFlickable`-jének dolga. Csak akkor mozdul, ha tényleg kell, és a
    // tartalom határain belül marad.
    function ensurePaneRowVisible(top, rowHeight) {
        var bottom = top + rowHeight
        var maxY = Math.max(0, paneContent.contentHeight - paneContent.height)
        if (top < paneContent.contentY)
            paneContent.contentY = Math.max(0, Math.min(top, maxY))
        else if (bottom > paneContent.contentY + paneContent.height)
            paneContent.contentY =
                Math.max(0, Math.min(bottom - paneContent.height, maxY))
    }

    // #1454: a NÉZETMÓD-váltás is nyissa ki a kijelölt mappáig az ágakat.
    // A `revealPath()` eddig csak a `selectedPath` VÁLTOZÁSÁRA futott — a
    // nyitott ágak halmaza viszont induláskor üres, és a `flatten()` a
    // virtuális gyökeret sem tekinti nyitottnak. Fa-módra váltva ezért a
    // hasáb egyetlen összecsukott „Sajátgép" sorra zsugorodott, a kijelölt
    // mappa pedig eltűnt. (A fanézet menüből eddig elérhetetlen volt, így
    // ez a hiba még sosem látszott.)
    onTreeViewModeChanged: {
        if (pane.treeViewMode && pane.hierarchyController)
            pane.hierarchyController.revealPath(pane.selectedPath)
    }

    // a kijelölt mappa maradjon látótérben (kívülről is változhat:
    // kereső-javaslat, feed-görgetés)
    onSelectedPathChanged: {
        // #702: a fa is kövesse a kijelölést, és nyissa ki hozzá az őseit.
        // A kötést NEM elég deklaratívan megadni: a `FolderHierarchyView`
        // `choose()`-a maga is ír a `selectedPath`-ba, ami elszakítaná —
        // utána a kívülről (kereső, rács) érkező váltás nem érne el a fáig.
        paneContent.folderHierarchyView.selectedPath = pane.selectedPath
        if (pane.treeViewMode && pane.hierarchyController)
            pane.hierarchyController.revealPath(pane.selectedPath)
        if (!paneContent.folderListModel || !paneContent.folderListView.visible) return
        var row = paneContent.folderListModel.rowOfPath(pane.selectedPath)
        if (row < 0) return
        paneContent.folderListView.positionViewAtIndex(row, ListView.Contain)
        pane.ensurePaneRowVisible(
            paneContent.folderListView.y + row * pane.rowHeight, pane.rowHeight)
    }

    // #422: jobbklikk a bal panel üres részén — a Picasa `AlbumList`
    // menüosztálya (a mappasorok saját menüje hamarabb elkapja az eseményt,
    // így ez tényleg csak a sorokon kívül fut le).
    TapHandler {
        objectName: "folderPaneContextMenuHandler"
        acceptedButtons: Qt.RightButton
        gesturePolicy: TapHandler.ReleaseWithinBounds
        onSingleTapped: pane.openFolderListContextMenu()
    }

    // #730: a hasáb EGÉSZE görgethető. Korábban a `ColumnLayout` az ablak
    // magasságába préselődött, ezért 30 személynél a mappalista magassága
    // 0 px lett, az „Egyéb” fejléc pedig kicsúszott az ablakból. Az eredeti
    // Picasa bal panelének SAJÁT, mindig látszó görgetősávja van
    // (docs/specs/ui-audit-mainwindow.md 3.1) — ez itt a `PicasaScrollBar`.
    FolderPaneContent {
        id: paneContent
        anchors.fill: parent
        folderPane: pane
        folderHierarchyController: pane.hierarchyController
    }

    // #320: a mappasor jobbklikk-menüje + a hozzá tartozó két kis
    // dialógus (önálló, signal-alapú komponensek — ld. FolderContextMenu/
    // NewCollectionDialog/FolderDateDialog.qml). A controller-kötést a
    // FolderPaneMenus.qml végzi; a #1637 rejtésjelzést a menükomponens fogadja.
    // A hívott controller-slotok (createCollection, moveFolderToCollection,
    // setFolderDate, clearFolderDate, customCollections) az AppController
    // öröklés-listájának bővítésével válnak élővé (controller.py, forró
    // fájl — az integrátor dolga).
    // #422: a fő ablak a kijelölés-parancsokhoz és a webexport-dialógushoz
    // (a PhotoViewer.qml `Window.window` mintája — így a forró Main.qml-hez
    // nem kell hozzányúlni; önálló példányosításnál egyszerűen hiányzik)
    readonly property var appWindow: Window.window
    readonly property var appController:
        typeof controller !== "undefined" ? controller : null

    FolderPaneMenus {
        id: paneMenus
        folderPane: pane
        controller: pane.appController
        folderHierarchyController: pane.hierarchyController
    }

    function _askRemoveFolder(path) {
        paneMenus.folderContextMenu.folderPath = path
        var nev = String(path).split(/[\\/]/).filter(Boolean).pop() || path
        paneMenus.removeFolderConfirm.ask(
            "removeFolder",
            qsTr("Do you want to remove the folder %1 and its subfolders?")
                .arg(nev))
    }


}
