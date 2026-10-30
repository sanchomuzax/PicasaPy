import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy
import "selection.js" as Selection

// Főablak (#150 után): a nagy nézet-blokkok külön komponensekben élnek
// (LightboxFeed = könyvtár-feed, MainToolbar = felső sáv, TrayBar = alsó
// sáv, MainPeopleAlbumState = személyalbum-műveletek,
// FileOpsDialogs/ExportDialogs/AboutDialog = dialógusok, selection.js =
// kijelölés-logika) — itt csak az állapot és a bekötés marad.
ApplicationWindow {
    id: window
    // A kivont komponens mellett a főablak korábbi QML-neve megmarad.
    property alias shortcutSave: mainWindowCommands.exportShortcutSave
    property alias errorBanner: mainWindowPeripheralLayers.exportErrorBanner
    property alias errorBannerText: mainWindowPeripheralLayers.exportErrorBannerText
    property alias searchSuggestionsBox: mainWindowCommands.exportSearchSuggestionsBox
    property alias suggestionsTimer: mainWindowCommands.exportSuggestionsTimer
    property alias mainDialogs: mainWindowCommands.exportMainDialogs
    property alias emailChoiceDialog: mainWindowCommands.exportEmailChoiceDialog
    property alias openWithDialog: mainWindowCommands.exportOpenWithDialog
    property alias folderManager: mainWindowCommands.exportFolderManager
    property alias peopleManagerLoader: mainWindowCommands.exportPeopleManagerLoader
    property alias dedupDialog: mainWindowCommands.exportDedupDialog
    property alias faceScanDialog: mainWindowCommands.exportFaceScanDialog
    property alias screensaverDialog: mainWindowCommands.exportScreensaverDialog
    property alias screensaverAlbumConfirmLoader: mainWindowCommands.exportScreensaverAlbumConfirmLoader
    property alias photoViewerSettingsDialog: mainWindowCommands.exportPhotoViewerSettingsDialog
    property alias picasaImportDialog: mainWindowCommands.exportPicasaImportDialog
    property alias importSourceDialog: mainWindowCommands.exportImportSourceDialog
    property alias addFileDialog: mainWindowCommands.exportAddFileDialog
    property alias tesztuzemNaploDialog: mainWindowCommands.exportTesztuzemNaploDialog
    property alias documentTabStrip: mainWindowWorkspace.exportDocumentTabStrip
    property alias folderPane: mainWindowWorkspace.exportFolderPane
    property alias photoViewer: mainWindowWorkspace.exportPhotoViewer
    property alias slideshow: mainWindowWorkspace.exportSlideshow
    property alias utolsoFiokLap: mainWindowLibraryActions.utolsoFiokLap
    property alias configureButtonsContextMenu: mainWindowCommands.exportConfigureButtonsContextMenu
    property alias kilepesDialog: mainWindowCommands.exportKilepesDialog
    property alias mainKeyboardShortcuts: mainWindowCommands.exportMainKeyboardShortcuts
    property alias saveSearchDialog: mainWindowCommands.exportSaveSearchDialog
    property alias showTagAsAlbumDialog: mainWindowCommands.exportShowTagAsAlbumDialog
    property alias _pendingSelectedIds: mainWindowCommands._pendingSelectedIds
    property alias _pendingAnchorId: mainWindowCommands._pendingAnchorId
    readonly property alias _kulonAblakosParbeszedNyitva: mainWindowCommands._kulonAblakosParbeszedNyitva
    property point helpCursor: Qt.point(-1, -1)
    readonly property alias _szovegmezoneVanFokusz: mainWindowCommands._szovegmezoneVanFokusz
    readonly property alias _konyvtariGyorsbillentyuEngedelyezve: mainWindowCommands._konyvtariGyorsbillentyuEngedelyezve
    property alias trayHasPictures: mainWindowCommands.trayHasPictures
    readonly property alias keyboardShortcutGroups: mainWindowCommands.keyboardShortcutGroups
    property alias activityCancelConfirm: mainWindowPeripheralLayers.exportActivityCancelConfirm
    property alias xmpFacesWriteDialog: mainWindowPeripheralLayers.exportXmpFacesWriteDialog
    property alias brokenPhotoDialog: mainWindowPeripheralLayers.exportBrokenPhotoDialog
    property alias brokenPhotoBatchTimer: mainWindowPeripheralLayers.exportBrokenPhotoBatchTimer
    property alias removeFromAlbumDialog: mainWindowPeripheralLayers.exportRemoveFromAlbumDialog
    property alias removePeopleFacesDialog: mainWindowPeripheralLayers.exportRemovePeopleFacesDialog
    property alias moveToNewPersonDialog: mainWindowPeripheralLayers.exportMoveToNewPersonDialog
    property alias initialScanDialog: mainWindowPeripheralLayers.exportInitialScanDialog
    property alias collectionPasswordDialog: mainWindowPeripheralLayers.exportCollectionPasswordDialog
    property alias hiddenPasswordOfferDialog: mainWindowPeripheralLayers.exportHiddenPasswordOfferDialog
    property alias collageDraftDialog: mainWindowPeripheralLayers.exportCollageDraftDialog
    property alias saveDialogs: mainWindowPeripheralLayers.exportSaveDialogs
    property alias fileOpsDialogs: mainWindowPeripheralLayers.exportFileOpsDialogs
    property alias exportDialogs: mainWindowPeripheralLayers.exportExportDialogs
    property alias createDialogs: mainWindowPeripheralLayers.exportCreateDialogs
    property alias helpDialog: mainWindowPeripheralLayers.exportHelpDialog
    property alias configureButtonsDialog: mainWindowPeripheralLayers.exportConfigureButtonsDialog
    property alias aboutDialog: mainWindowPeripheralLayers.exportAboutDialog
    property alias optionsDialog: mainWindowPeripheralLayers.exportOptionsDialog
    property alias webExportDialog: mainWindowPeripheralLayers.exportWebExportDialog
    property alias printDialog: mainWindowPeripheralLayers.exportPrintDialog
    property alias moveDatabaseDialog: mainWindowPeripheralLayers.exportMoveDatabaseDialog
    property alias compactDatabaseDialog: mainWindowPeripheralLayers.exportCompactDatabaseDialog
    property alias picasaDataImportDialog: mainWindowPeripheralLayers.exportPicasaDataImportDialog
    width: 1280
    height: 800
    // #641: az ablak nem mehet olyan kicsire, hogy a szerkesztő bal panelje
    // ne férjen el — különben a Visszavonás/Újra sor kicsúszik a látható
    // területről, és a felhasználó egyáltalán nem látja. A #628 a panel
    // `implicitHeight`-jét már kiszámolta, de a garanciát egy
    // `Layout.minimumHeight`-re bízta, amit semmi nem érvényesít az ablak
    // szintjén — ez az a hely, ahol érvényesíteni kell.
    minimumHeight: photoViewer.requiredHeight
                   + (window.menuBar ? window.menuBar.height : 0)
    // #1367: az ablak nem mehet olyan keskenyre, hogy az alsó
    // műveletsáv kilógjon — a #1345 fix gombcellái óta a sáv nem
    // zsugorodik tovább. Az igény MÉRT (ld. `TrayBar.requiredWidth`),
    // és őr-teszt méri újra élőben.
    minimumWidth: trayBar.requiredWidth
    //: A mutatókövető a főablak gyökerén marad, hogy a munkaterület fölötti
    //: elemek fölött is megkapja a hover-eseményt, ahogy a bontás előtt.
    HoverHandler {
        objectName: "helpCursorTracker"
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onPointChanged: window.helpCursor = point.position
    }
    visible: true
    //: #671: az ablak „X"-e UGYANAZT az utat járja, mint a Fájl ▸ Kilépés.
    //: Ha háttérmunka fut, a bezárást visszavonjuk, és a kérdés dönt;
    //: egyébként a Qt zárja az ablakot, ahogy eddig.
    onClosing: function (close) {
        if (!window.aaKapu(window.kilepes)) {   // #3644
            close.accepted = false
            return
        }
        if (controller && controller.backgroundWorkRunning()) {
            close.accepted = false
            kilepesDialog.askExit()
        }
    }
    title: "PicasaPy"
    color: Theme.lightboxBg

    // #28: a téma a Theme-tokenekből jön, azok pedig a controller
    // kapcsolójából — az OS saját sötét módja sehol nem üthet át, a
    // váltás kizárólag a Nézet → Sötét téma menüponté (alapértelmezés:
    // világos; ld. design-guide).
    Binding {
        target: Theme
        property: "dark"
        value: controller ? controller.darkTheme : false
    }

    // #3070: a Nézet ▸ Megjelenítési mód a FELÜLET színeire is hat, nem csak
    // a fotóra. A vezérlő EGY menetben átalakítja a `Theme.nyers` tokenjeit
    // (`apply_display_mode` — ugyanaz a MÉRT szabály, ami a képen fut), és az
    // eredményt a szingleton palettájába tesszük; onnantól minden kötés
    // magától követi (a 11.7/2. szerződés „mindent újrafest" pontja nálunk a
    // szingleton jelzése). Üres paletta = a mód nem mozdít képpontot, tehát a
    // nyers értékek mennek ki változatlanul.
    //
    // A diavetítés SZÁNDÉKOSAN kimarad (11.7/3., NY-4): az a saját útján kapja
    // meg a módot (#1640), a téma színeit pedig nem használja.
    function frissitsdAMegjelenitesiPalettat() {
        Theme.megjelenitesiPaletta = controller
            ? controller.uiPalette(Theme.nyers) : ({})
    }

    Connections {
        target: controller
        function onDisplayModeChanged() { window.frissitsdAMegjelenitesiPalettat() }
        //: a sötét/világos váltás a NYERS értékeket cseréli ki, tehát a
        //: paletta is újraszámolandó — különben az előző téma átalakított
        //: színei ragadnának be
        function onDarkThemeChanged() { window.frissitsdAMegjelenitesiPalettat() }
    }

    palette {
        window: Theme.canvasBg
        active.windowText: Theme.ink
        inactive.windowText: Theme.ink
        base: Theme.controlBase
        alternateBase: Theme.panelBg
        active.text: Theme.ink
        inactive.text: Theme.ink
        button: Theme.buttonBg
        active.buttonText: Theme.ink
        inactive.buttonText: Theme.ink
        highlight: Theme.selectionBlue
        highlightedText: Theme.panelSelectionText
        placeholderText: Theme.placeholderText
        mid: Theme.chromeBorder
        light: Theme.shadeLight
        dark: Theme.shadeDark
        // #5874: az aktív/inaktív tinták ne írják felül a Qt Controls
        // disabled csoportját; a Theme token mindkét témában olvasható.
        disabled.windowText: Theme.textGray
        disabled.text: Theme.textGray
        disabled.buttonText: Theme.textGray
    }

    // #985: a globális `controller` egy KONTEXTUS-property, a `CollagePanel`
    // viszont saját `controller` property-t deklarál (hogy a komponens-
    // tesztekben becserélhető legyen). A `controller: controller` sor ezért
    // önmagára kötne (kötési hurok) — ez az álnév oldja fel, egy helyen.
    readonly property var appController: controller
    property alias peoplePanel: mainWindowWorkspace.exportPeoplePanel

    property string pendingPeopleManagerPersonName: ""
    property string pendingPeopleManagerPersonId: ""
    property int thumbSize: 144
    //: #598: a cellaméret átadása a bélyegkép-tárnak — a SZINTET (72 · 144 ·
    //: a maximum) a tár választja ki belőle. A csúszka húzása nem kér újra
    //: mindent: egy szint több fokozatot fed le.
    onThumbSizeChanged: if (controller) controller.setThumbCellSize(thumbSize)
    property int selectedIndex: -1        // horgony (utoljára kattintott)
    property var selectedIndexes: []      // a teljes kijelölés
    // #5396: átnevezéskor a fájl útvonal alapján új fotóazonosítót kaphat
    // az indexfrissítésben; a következő modell-reset visszateszi a kijelölést.
    property string _pendingRenamePhotoId: ""
    property string _pendingRenameTargetPath: ""
    // #142: a kijelölés set-alakban (sor → true) — a rács-cellák O(1)
    // lookupja; az indexOf-os kötés O(cellák × kijelöltek) volt, ami
    // Ctrl+A-nál minden cellán végigjárta a teljes kijelölés-listát
    property var selectedSet: ({})
    property alias _lastFolder: mainLibrarySelectionState._lastFolder
    onSelectedIndexesChanged: {
        var s = {}
        for (var k = 0; k < selectedIndexes.length; ++k)
            s[selectedIndexes[k]] = true
        selectedSet = s
    }
    readonly property bool quickViewerLaunch:
        controller ? controller.quickViewActive === true : false
    property bool viewerOpen: quickViewerLaunch
    // #4656: a néző saját megjelenítési módot kap, bezáráskor visszaáll az
    // előző ablakállapot. A valódi megnyitás külön belépőn fut át, így a
    // közvetlen állapotbeállítások (például a QML-próbapadban) nem váltanak módot.
    property int visibilityBeforeViewer: Window.Windowed
    property bool viewerVisibilityManaged: false
    onViewerOpenChanged: {
        // A gyorsnézet a könyvtár beolvasása előtt indul. Bezáráskor
        // takarítsuk el az ideiglenes listát, és csak ekkor kérjük a rendes
        // könyvtár betöltését.
        if (!window.viewerOpen && window.quickViewerLaunch) {
            controller.returnToLibraryFromQuickView()
            Qt.callLater(function() {
                initialScanDialog.openIfNeeded()
                collageDraftDialog.openIfNeeded()
                if (typeof discoveryController !== "undefined"
                        && discoveryController)
                    discoveryController.discoverAtStartup()
            })
        }
        if (!window.viewerOpen && window.viewerVisibilityManaged) {
            window.visibility = window.visibilityBeforeViewer
            window.viewerVisibilityManaged = false
        }
    }
    // Az eredeti főablaki állapotnevek az Időrend-komponensre mutatnak.
    property alias timelineOpen: mainWindowWorkspace.exportTimelineOpen
    property alias timelineSlideshowActive: mainWindowWorkspace.exportTimelineSlideshowActive
    property alias timelineSlideshowModel: mainWindowWorkspace.exportTimelineSlideshowModel
    //: #1808: rács-nagyító be/ki. A rácsban a nagyító-réteg
    //: ELNYELI az egéreseményeket, tehát bekapcsolva a húzás nem
    //: jelöl ki — ez szándékos, ld. LightboxFeed.qml.
    //:
    //: ⚠️ #1911: ma SENKI nem billenti igazra — az eszköztári
    //: kapcsológomb kikerült, mert élesben felfedezhetetlen volt. A
    //: tulajdonság és a rács oldali réteg SZÁNDÉKOSAN marad: mérve van
    //: és működik, csak felfedezhető felület kell hozzá (külön jegy).
    //: Ne töröld „halott kódként" — a hiányzó darab a KAPCSOLÓ.
    property bool loupeActive: false
    // #1773: a jobb fiók négy lapja KIZÁRÓ csoport — egyszerre pontosan
    // egy látszik, vagy a fiók üres. Ezért EGYETLEN állapot írja le mind a
    // négyet; négy független billenőből a mérés szerint nem előfordulható
    // állapotok álltak elő (négy panel egyszerre nyitva).
    //
    // MÉRVE (`0x005d9760`, mind a négy ág): a vezérlő elrejti a másik
    // hármat, kikapcsolja a másik három fejléc-gombot, bekapcsolja a
    // sajátját, majd megjeleníti a saját panelt.
    //
    // Az érvényes értékek: "" (a fiók üres) · "tags" · "places" ·
    // "properties" · "people".
    property string activeDrawerTab: ""

    // A négy régi jelző SZÁRMAZTATOTT — a kötések és a menüpipák
    // változatlanul rájuk hivatkoznak, de már nem írhatók külön-külön.
    readonly property bool tagsPanelOpen:
        window.activeDrawerTab === "tags"        // Címkék-panel (#12, Ctrl+T)
    readonly property bool placesPanelOpen:
        window.activeDrawerTab === "places"      // Helyek-panel (#30, térkép)
    // Tulajdonságok-panel (#13, Alt+Enter)
    readonly property bool propertiesPanelOpen:
        window.activeDrawerTab === "properties"
    // Emberek-panel (#26) — a jobb fiók negyedik panelje
    // (`rightdrawerpanel/peoplepanel`), a Címkék/Helyek/Tulajdonságok mellett
    readonly property bool peoplePanelOpen:
        window.activeDrawerTab === "people"

    MainWindowLibraryActions {
        id: mainWindowLibraryActions
        hostWindow: window
        hostController: typeof controller !== "undefined" ? controller : null
        hostPhotoViewer: photoViewer
        hostToolbar: toolbar
    }
    function valtsFiokLapot(nev) { mainWindowLibraryActions.valtsFiokLapot(nev) }
    function ureseidAFiokot() { mainWindowLibraryActions.ureseidAFiokot() }
    function fokuszAKeresore() { mainWindowLibraryActions.fokuszAKeresore() }
    function openPhotoViewer(row) { mainWindowLibraryActions.openPhotoViewer(row) }
    function startQuickViewer() { mainWindowLibraryActions.startQuickViewer() }
    function nezdEsSzerkeszd() { mainWindowLibraryActions.nezdEsSzerkeszd() }
    function hideSelection() { mainWindowLibraryActions.hideSelection() }
    function unhideHiddenSelection() { mainWindowLibraryActions.unhideHiddenSelection() }
    function masodpeldanyokMutatasa() { mainWindowLibraryActions.masodpeldanyokMutatasa() }
    function torolAHasonlosagMintat() { mainWindowLibraryActions.torolAHasonlosagMintat() }
    function keressHasonlot() { mainWindowLibraryActions.keressHasonlot() }
    function kotegEffekt(nev) { mainWindowLibraryActions.kotegEffekt(nev) }
    function billentsdAFiokot() { mainWindowLibraryActions.billentsdAFiokot() }

    // #26 (3. lépcső): a „Névtelenek" nézet — a fő rács helyén jelenik
    // meg, amíg be van kapcsolva (ld. UnnamedFacesView.qml)
    property bool unnamedFacesOpen: false
    // #26: melyik arc-album van nyitva — „unnamed" vagy „ignored"
    // (`CAlbumLabel::Ignored` = „Mellőzött emberek")
    property string facesAlbumMode: "unnamed"
    // A névadás után a fotókijelölés nem változik, ezért külön frissítőjel
    // kell az Emberek-panel sorlistáinak újraolvasásához.
    property int peopleFaceRevision: 0
    // #4586: csak az `unnamedFacesHere` frissítéséhez (keresés közben)
    property int unnamedFaceRevision: 0
    Timer {
        id: unnamedFaceRefreshTimer
        interval: 500
        onTriggered: window.unnamedFaceRevision++
    }
    // nyitáskor az arc-lista friss: a nyitott-panel kapu miatt a zárt panel
    // alatt érkezett `facesStored` jelek kimaradtak
    onPeoplePanelOpenChanged: if (window.peoplePanelOpen) unnamedFaceRevision++
    Connections {
        target: photoViewer
        function onPeopleOpenChanged() {
            if (photoViewer.peopleOpen) window.unnamedFaceRevision++
        }
    }
    // a kijelölt képek közül a futó keresés által még nem ellenőrzöttek
    // száma — csak nyitott panelnél és nem a Név nélküliek albumban számolunk
    readonly property int _selectionPending:
        (window.peoplePanelOpen && !window.unnamedFacesOpen)
            ? window.selectionPendingCount() : 0

    // #4586: a kijelölt képek közül hányat nem vizsgált még át a futó
    // háttér-arckeresés (`PeoplePanel` betöltés / ellenőrizetlen fájlok)
    function selectionPendingCount() {
        var scan = window._faceScanController
        if (!scan || !controller)
            return 0
        // a függés az `uncheckedFiles`-en: a keresés haladására újraszámol
        var remaining = scan.uncheckedFiles
        if (remaining <= 0)
            return 0
        return scan.pendingAmong(window.selectedPaths())
    }
    // #1236: külön ablak-szintű név kell. Az UnnamedFacesView azonos nevű
    // property-jének jobb oldalán a `faceScanController` önmagára oldódna.
    readonly property var _faceScanController:
        typeof faceScanController !== "undefined" ? faceScanController : null
    // a jobbklikkelt kép sora (#15) — a kontextusmenü egyedi műveleteinek
    // (átnevezés, fájlkezelő) célpontja
    property int fileOpTargetRow: -1

    // A kollázs- és filmprojektlapok állapota és navigációja (#6136).
    MainProjectTabs {
        id: mainProjectTabs
        hostWindow: window
        hostController: controller
        hostDocumentTabStrip: documentTabStrip
        hostSlideshow: slideshow
        hostCreateDialogs: createDialogs
        collageTitle: qsTr("Collage")
        movieMakerTitle: qsTr("Movie Maker")
    }
    readonly property string collageTabId: mainProjectTabs.collageTabId
    readonly property string movieMakerTabId: mainProjectTabs.movieMakerTabId
    property alias movieMakerTabOpen: mainProjectTabs.movieMakerTabOpen
    readonly property real documentTabsBottom: mainProjectTabs.documentTabsBottom
    readonly property string activeDocumentTabId: mainProjectTabs.activeDocumentTabId
    readonly property bool movieMakerActive: mainProjectTabs.movieMakerActive
    property alias backToMovieMakerPrompted: mainProjectTabs.backToMovieMakerPrompted
    readonly property var openProjectTabs: mainProjectTabs.openProjectTabs
    readonly property bool libraryFrameVisible: mainProjectTabs.libraryFrameVisible
    readonly property bool slideshowRunning: mainProjectTabs.slideshowRunning
    property alias backToCollagePrompted: mainProjectTabs.backToCollagePrompted

    function collageSourceRows() { return mainProjectTabs.collageSourceRows() }
    function openCollageFromRows(rows) { mainProjectTabs.openCollageFromRows(rows) }
    function openMovieFromRows(rows) { mainProjectTabs.openMovieFromRows(rows) }
    function openMovieMakerTab() { mainProjectTabs.openMovieMakerTab() }
    function openMovieClipCollector() { mainProjectTabs.openMovieClipCollector() }
    function returnToMovieMaker() { mainProjectTabs.returnToMovieMaker() }
    function closeMovieMakerTab() { mainProjectTabs.closeMovieMakerTab() }
    function openCollageTab() { mainProjectTabs.openCollageTab() }
    function openSavedMovie(path) { mainProjectTabs.openSavedMovie(path) }
    function openSavedCollage(path) { mainProjectTabs.openSavedCollage(path) }
    function locateSavedCollage(path) { mainProjectTabs.locateSavedCollage(path) }
    function folderOfPath(path) { return mainProjectTabs.folderOfPath(path) }
    function openCollageNodeInEditor(path) {
        mainProjectTabs.openCollageNodeInEditor(path)
    }

    // A könyvtári kijelölés és műveletei külön komponensben élnek; a régi
    // főablak-nevek és a fordítási kontextus változatlanul megmaradnak.
    MainLibrarySelectionState {
        id: mainLibrarySelectionState
        hostWindow: window
        hostController: typeof controller !== "undefined" ? controller : null
        hostPhotoViewer: photoViewer
        hostMainDialogs: mainDialogs
        hostPhotoContextMenu: mainWindowPeripheralLayers.exportPhotoContextMenu
        hostFolderPane: folderPane
        hostScreensaverAlbumConfirmLoader: screensaverAlbumConfirmLoader
        hostFaceScanDialog: faceScanDialog
        hostFaceScanController: typeof faceScanController !== "undefined"
            ? faceScanController : null
        screensaverAddedMessage: qsTr("Added %1 pictures to Screensaver.")
    }
    readonly property bool kijelolesbenVanMentetlenSzerkesztes:
        mainLibrarySelectionState.kijelolesbenVanMentetlenSzerkesztes
    readonly property bool muveletiCelbanVanMentetlenSzerkesztes:
        mainLibrarySelectionState.muveletiCelbanVanMentetlenSzerkesztes

    function selectedRows() { return mainLibrarySelectionState.selectedRows() }
    function vanMentetlenSzerkesztes(sorok) { return mainLibrarySelectionState.vanMentetlenSzerkesztes(sorok) }
    function photoActionRows() { return mainLibrarySelectionState.photoActionRows() }
    function prepareRenameSelection(row, newName) { mainLibrarySelectionState.prepareRenameSelection(row, newName) }
    function photoActionIndex() { return mainLibrarySelectionState.photoActionIndex() }
    function photoActionPaths() { return mainLibrarySelectionState.photoActionPaths() }
    function newAlbumFolderPath() { return mainLibrarySelectionState.newAlbumFolderPath() }
    function addPhotosToScreensaver(paths) { mainLibrarySelectionState.addPhotosToScreensaver(paths) }
    function requestAddToScreensaver() { mainLibrarySelectionState.requestAddToScreensaver() }
    function addTagToRows(rowList, keyword) { mainLibrarySelectionState.addTagToRows(rowList, keyword) }
    function selectedPaths() { return mainLibrarySelectionState.selectedPaths() }
    function resetFacesForPaths(paths) { mainLibrarySelectionState.resetFacesForPaths(paths) }
    function openPhotoContextMenu(index, item, x, y) { mainLibrarySelectionState.openPhotoContextMenu(index, item, x, y) }
    function splitFolderHere() { mainLibrarySelectionState.splitFolderHere() }
    function handleThumbClick(index, modifiers) { mainLibrarySelectionState.handleThumbClick(index, modifiers) }
    function _folderOfRow(row) { return mainLibrarySelectionState._folderOfRow(row) }
    function _selectionInFolder(path) { return mainLibrarySelectionState._selectionInFolder(path) }
    function clearSelection() { mainLibrarySelectionState.clearSelection() }
    function _currentGroup() { return mainLibrarySelectionState._currentGroup() }
    function _groupRows() { return mainLibrarySelectionState._groupRows() }
    function selectAll() { mainLibrarySelectionState.selectAll() }
    function invertSelection() { mainLibrarySelectionState.invertSelection() }
    function selectStarred() { mainLibrarySelectionState.selectStarred() }

    // A személyalbum-javaslatok állapota külön komponensben él. A régi
    // főablak-tulajdonságok és függvények továbbra is nyilvánosak.
    MainPeopleAlbumState {
        id: mainPeopleAlbumState
        hostWindow: window
        hostController: controller
        hostFaceScanController: typeof faceScanController !== "undefined"
            ? faceScanController : null
        hostRemovePeopleFacesDialog: removePeopleFacesDialog
        hostCreateDialogs: createDialogs
    }
    property alias _javaslatRevizio: mainPeopleAlbumState._javaslatRevizio
    readonly property string personAlbumName:
        mainPeopleAlbumState.personAlbumName
    readonly property string personAlbumAvatarUrl:
        mainPeopleAlbumState.personAlbumAvatarUrl
    readonly property bool personAlbumCanRemoveSelection:
        mainPeopleAlbumState.personAlbumCanRemoveSelection
    readonly property bool personAlbumCanSetThumbnail:
        mainPeopleAlbumState.personAlbumCanSetThumbnail
    readonly property int personSuggestionCount:
        mainPeopleAlbumState.personSuggestionCount
    readonly property var personSelectedSuggestionIds:
        mainPeopleAlbumState.personSelectedSuggestionIds
    readonly property bool personSuggestionsOnly:
        mainPeopleAlbumState.personSuggestionsOnly
    readonly property bool personFaceZoom: mainPeopleAlbumState.personFaceZoom
    function removePersonAlbumSelection() {
        mainPeopleAlbumState.removePersonAlbumSelection()
    }
    function setPersonAlbumThumbnailFromSelection() {
        mainPeopleAlbumState.setPersonAlbumThumbnailFromSelection()
    }
    function openPersonAlbumMovie() { mainPeopleAlbumState.openPersonAlbumMovie() }
    function openPeopleAlbumsMovie() { mainPeopleAlbumState.openPeopleAlbumsMovie() }
    function selectPersonSuggestions() {
        mainPeopleAlbumState.selectPersonSuggestions()
    }
    function confirmPersonSuggestions() {
        mainPeopleAlbumState.confirmPersonSuggestions()
    }
    function removePersonSuggestions() {
        mainPeopleAlbumState.removePersonSuggestions()
    }
    function setPersonSuggestionsOnly(csak) {
        mainPeopleAlbumState.setPersonSuggestionsOnly(csak)
    }
    function setPersonFaceZoom(arc) {
        mainPeopleAlbumState.setPersonFaceZoom(arc)
    }
    function findMoreSuggestions() {
        mainPeopleAlbumState.findMoreSuggestions()
    }
    function _javaslatFrissult() {
        mainPeopleAlbumState._javaslatFrissult()
    }

    //: #1823: „szerkesztések mentése lemezre" a mappa-fejlécről. A
    //: művelet a #444 mentés-párbeszédéé — ez csak egy újabb belépési
    //: pont, ugyanazzal a megerősítéssel és biztonsági mentéssel.
    function saveSelectedEdits() {
        saveDialogs.ensure().openSave(window.selectedIndexes)
    }
    // #422: „Exportálás HTML-oldalként…" a mappa-kontextusmenüből — a
    // dialógus itt él (a menüsáv is ezt nyitja)
    function openWebExport() { webExportDialog.open() }
    // #1472: nyomtatás — HÁROM belépési pont vezet ide (Fájl ▸ Nyomtatás…,
    // Ctrl+P, és a képtálca „Nyomtatás" gombja), ahogy az exportnál is.
    // A célpont ugyanaz a HÁROM ág, mint a `rotateTargetRow()`-nál:
    // diavetítés közben a VETÍTETT kép, a nézőben a MEGJELENÍTETT kép, a
    // rácsban a kijelölés.
    //
    // ⚠️ A diavetítés ága nem elhagyható: a `startSlideshow()` NEM állítja
    // a `viewerOpen`-t, tehát a menü és a Ctrl+P vetítés közben is
    // engedélyezett marad — enélkül a felhasználó egy képet néz, és a
    // RÁCS kijelölése menne nyomtatásra.
    function printTargetRows() {
        if (slideshow.visible)
            return slideshow.currentIndex >= 0 ? [slideshow.currentIndex] : []
        if (window.viewerOpen)
            return window.photoActionRows()
        return window.selectedRows()
    }
    function openPrint() { printDialog.ensure().openForRows(window.printTargetRows()) }
    // #1590: Mappa ▸ Bélyegképek nyomtatása… — ugyanaz a párbeszéd,
    // indexkép-elrendezésre állítva. Kijelölés nélkül a MEGNYITOTT MAPPA
    // egésze a célpont: az eredetiben ez a parancs a mappa/album tétele,
    // nem a kijelölésé.
    function openContactSheetPrint() {
        var sorok = window.printTargetRows()
        // a `_groupRows` a MEGNYITOTT mappa sorai (nem az egész rácsé,
        // ha az több mappát mutat) — pontosan az, amire a mappa-menü
        // tétele vonatkozik
        if (sorok.length === 0) sorok = window._groupRows()
        printDialog.ensure().openForContactSheet(sorok)
    }
    // #422: a mappa-kontextusmenünek HÁROM megnyitási pontja van (a rács
    // üres területe, a bal panel mappa-sora, a rács mappa-fejléce), és
    // mindhárom UGYANAZT a menüt nyitja. A menü a FolderPane-ben él; a
    // másik két hívó ezen az ablak-szintű átjárón éri el.
    function openFolderContextMenu(path) {
        var target = path && path.length > 0
            ? path : (controller ? controller.currentFolder : "")
        if (target.length > 0) folderPane.openFolderContextMenu(target)
    }
    // #4637: az alsó kimeneti gombsor helyi menüje.
    function openConfigureButtonsContextMenu(anchorItem, x, y) {
        if (!anchorItem) return
        configureButtonsContextMenu.popup(anchorItem, x, y)
    }

    MainWindowCommands {
        id: mainWindowCommands
        anchors.fill: parent
        hostWindow: window
        hostController: typeof controller !== "undefined" ? controller : null
        hostRefs: ({
            documentTabStrip: documentTabStrip,
            photoViewer: photoViewer,
            picasaMenuBar: picasaMenuBar,
            slideshow: slideshow,
            timelineView: mainWindowWorkspace.exportTimelineView,
            toolbar: toolbar,
            trayBar: trayBar
        })
    }
    property alias visibilityBeforeViewerFullscreen:
        mainWindowWorkspace.exportVisibilityBeforeViewerFullscreen
    property alias visibilityBeforeSlideshow:
        mainWindowWorkspace.exportVisibilityBeforeSlideshow

    function _temaAPontban(elem, x, y) { return mainWindowCommands._temaAPontban(elem, x, y) }
    function nyisdASugot(tema) { mainWindowCommands.nyisdASugot(tema) }
    function helpTopicUnderCursor() { return mainWindowCommands.helpTopicUnderCursor() }
    function mentsdAKeresest() { mainWindowCommands.mentsdAKeresest() }
    function aaKapu(folytatas) { return mainWindowCommands.aaKapu(folytatas) }
    function kilepes() { mainWindowCommands.kilepes() }
    function masoldASzovegreteget() { mainWindowCommands.masoldASzovegreteget() }
    function illeszdBeASzovegreteget() { mainWindowCommands.illeszdBeASzovegreteget() }
    function beillesztAVagolaprol() { mainWindowCommands.beillesztAVagolaprol() }
    function rotateTargetRow() { return mainWindowCommands.rotateTargetRow() }
    function rotateTargetsAllVideo() { return mainWindowCommands.rotateTargetsAllVideo() }
    function tukrozesiSorok() { return mainWindowCommands.tukrozesiSorok() }
    function timelineCollectionForId(collectionId) { return mainWindowCommands.timelineCollectionForId(collectionId) }
    function selectTimelineCollection(collection) { mainWindowCommands.selectTimelineCollection(collection) }
    function closeTimeline() { mainWindowCommands.closeTimeline() }
    function toggleTimeline() { mainWindowCommands.toggleTimeline() }
    function startTimelineSlideshow(collectionId) { mainWindowCommands.startTimelineSlideshow(collectionId) }
    function toggleViewerFullscreen() { mainWindowCommands.toggleViewerFullscreen() }
    function startSlideshow(fromIndex) { mainWindowCommands.startSlideshow(fromIndex) }
    function startScreensaverPreview() { mainWindowCommands.startScreensaverPreview() }
    function exitSlideshow() { mainWindowCommands.exitSlideshow() }
    function toggleHiddenSelection() { mainWindowCommands.toggleHiddenSelection() }
    function sendSelectionByEmail() { mainWindowCommands.sendSelectionByEmail() }
    function openSelectionInDefaultEditor() { mainWindowCommands.openSelectionInDefaultEditor() }
    function openPeopleManagerForPerson(name, personId) {
        mainWindowCommands.openPeopleManagerForPerson(name, personId)
    }

    menuBar: MainMenuBar {
        id: picasaMenuBar
        hostWindow: window
        hostController: controller
        hostFileOpsController: typeof fileOpsController !== "undefined"
            ? fileOpsController : null
        hostPassportController: typeof passportController !== "undefined"
            ? passportController : null
        hostAboutDialog: aboutDialog
        hostAddFileDialog: addFileDialog
        hostBackupHost: mainWindowPeripheralLayers.exportBackupHost
        hostCollectionPasswordDialog: collectionPasswordDialog
        hostCompactDatabaseDialog: compactDatabaseDialog
        hostConfigureButtonsDialog: configureButtonsDialog
        hostCreateDialogs: createDialogs
        hostDedupDialog: dedupDialog
        hostExportDialogs: exportDialogs
        hostFaceScanDialog: faceScanDialog
        hostFileOpsDialogs: fileOpsDialogs
        hostFolderManager: folderManager
        hostFolderPane: folderPane
        hostGiftCdHost: mainWindowPeripheralLayers.exportGiftCdHost
        hostHelpDialog: helpDialog
        hostImportSourceDialog: importSourceDialog
        hostMainDialogs: mainDialogs
        hostMoveDatabaseDialog: moveDatabaseDialog
        hostOptionsDialog: optionsDialog
        hostPeopleManagerLoader: peopleManagerLoader
        hostPhotoViewer: photoViewer
        hostPhotoViewerSettingsDialog: photoViewerSettingsDialog
        hostPicasaDataImportDialog: picasaDataImportDialog
        hostRemoveFromAlbumDialog: removeFromAlbumDialog
        hostRemovePeopleFacesDialog: removePeopleFacesDialog
        hostSaveDialogs: saveDialogs
        hostSaveSearchDialog: saveSearchDialog
        hostScreensaverDialog: screensaverDialog
        hostShowTagAsAlbumDialog: showTagAsAlbumDialog
        hostToolbar: toolbar
        hostTrayBar: trayBar
        hostWebExportDialog: webExportDialog
        hostXmpFacesWriteDialog: xmpFacesWriteDialog
    }

    // első indítás: nincs még figyelt mappa → Mappakezelő felajánlása
    // #449: első indítás — az eredeti EGYETLEN kérdést tett fel (teljes gép
    // vs. Dokumentumok/Képek/Asztal), és nem nyitott mappalistát. Eddig
    // nálunk üres könyvtárnál rögtön a Mappakezelő nyílt ki: az egy fát és
    // egy jóval nagyobb döntést tett a felhasználó elé az első percben.
    Component.onCompleted: { mainWindowCommands.onWindowCompleted() }

    function refreshSuggestions() { mainWindowCommands.refreshSuggestions() }

    // Eszköztár: a fejléc önálló komponens, változatlan ablakfejlécként.
    header: MainWindowToolbar {
        id: toolbar
        hostWindow: window
        hostRefs: ({
            searchSuggestionsBox: searchSuggestionsBox,
            suggestionsTimer: suggestionsTimer,
            picasaMenuBar: picasaMenuBar,
            importSourceDialog: importSourceDialog,
            fileOpsDialogs: fileOpsDialogs
        })
    }

    MainWindowWorkspace {
        id: mainWindowWorkspace
        anchors.fill: parent
        hostWindow: window
        hostController: typeof controller !== "undefined" ? controller : null
        hostRefs: ({
            backupHost: mainWindowPeripheralLayers.exportBackupHost,
            giftCdHost: mainWindowPeripheralLayers.exportGiftCdHost,
            importSourceDialog: importSourceDialog,
            mainDialogs: mainDialogs,
            picasaMenuBar: picasaMenuBar,
            searchSuggestionsBox: searchSuggestionsBox,
            toolbar: toolbar
        })
    }

    // #1939: a „Vissza a kollázshoz" visszaútja AZ ALSÓ SÁVBA került
    // (`TrayBar.qml` → `traySingleActionBar`), mert az eredetiben a
    // „Továbbiak…" után egy teljes üzenetsáv ül a vezérlőkészletben
    // (`thumbui/single_action_container`), nem egy lebegő gomb a jobb
    // felső sarokban. A visszatérés MŰVELETE változatlan — csak a
    // felülete került a helyére; a kezelő lent, a `TrayBar`-on.
    //
    // Ezért NINCS itt `backToCollageButton`: ne tegye vissza egy későbbi
    // kör „hiányzó gombként", mert akkor két vezérlő kínálná ugyanazt.

    MainWindowPeripheralLayers {
        id: mainWindowPeripheralLayers
        anchors.fill: parent
        hostWindow: window
        hostController: typeof controller !== "undefined" ? controller : null
        hostRefs: ({
            photoViewer: photoViewer,
            documentTabStrip: documentTabStrip,
            unnamedFaceRefreshTimer: unnamedFaceRefreshTimer,
            tesztuzemNaploDialog: tesztuzemNaploDialog,
            brokenPhotoDialog: brokenPhotoDialog,
            brokenPhotoBatchTimer: brokenPhotoBatchTimer,
            fileOpsDialogs: fileOpsDialogs,
            mainDialogs: mainDialogs,
            moveToNewPersonDialog: moveToNewPersonDialog,
            openWithDialog: openWithDialog,
            removeFromAlbumDialog: removeFromAlbumDialog,
            removePeopleFacesDialog: removePeopleFacesDialog,
            saveDialogs: saveDialogs,
            toolbar: toolbar
        })
    }

    // alsó sáv: infó-sáv + kijelölés-tálca (MainTrayBar → TrayBar, #150)
    footer: MainTrayBar {
        id: trayBar
        objectName: "trayBar"
        hostWindow: window
        hostController: controller
        hostPhotoViewer: photoViewer
        hostExportDialogs: exportDialogs
        hostCreateDialogs: createDialogs
        hostFileOpsDialogs: fileOpsDialogs
        hostFileOpsController: typeof fileOpsController !== "undefined"
            ? fileOpsController : null
        hostDocumentTabStrip: documentTabStrip
    }


}
