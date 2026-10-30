pragma ComponentBehavior: Bound
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy

// A könyvtár, a néző és az időrend közös tartalmi vászna.
Item {
    id: workspace
    objectName: "mainWindowWorkspace"
    anchors.fill: parent
    required property var hostWindow
    required property var hostController
    required property var hostRefs

    property alias exportDocumentTabStrip: documentTabStrip
    property alias exportPeoplePanel: jobbFiok.peoplePanel
    property alias exportTimelineOpen: timelineView.timelineOpen
    property alias exportTimelineSlideshowActive: timelineView.timelineSlideshowActive
    property alias exportTimelineSlideshowModel: timelineView.timelineSlideshowModel
    property alias exportVisibilityBeforeViewerFullscreen: slideshow.visibilityBeforeViewerFullscreen
    property alias exportVisibilityBeforeSlideshow: slideshow.visibilityBeforeSlideshow
    property alias exportFolderPane: folderPane
    property alias exportRightDrawer: jobbFiok
    property alias exportPhotoViewer: photoViewer
    property alias exportSlideshow: slideshow
    property alias exportTimelineView: timelineView

    // #8: a diavetítés a főablak önálló vetítési rétege.
    MainSlideshow {
        id: slideshow
        hostWindow: workspace.hostWindow
        hostController: workspace.hostController
        hostPhotoViewer: photoViewer
        hostErrorBanner: workspace.hostWindow.errorBanner
        hostErrorBannerText: workspace.hostWindow.errorBannerText
        noScreensaverPicturesMessage: qsTr(
            "The selected screensaver sources contain no available pictures.")
    }

    PhotoViewer {
        id: photoViewer
        objectName: "photoViewer"
        anchors.fill: parent
        visible: hostWindow.viewerOpen
        // #305: null-őr
        photosModel: hostController ? hostController.photos : null
        // #422: a mentés-parancsok a nézőből — ugyanazok a megerősítések,
        // mint a rácsból (egy parancs, egy út)
        onSaveRequested: function(row) { saveDialogs.ensure().openSave([row]) }
        onRevertRequested: function(row) { saveDialogs.ensure().openRevert([row]) }
        onUndoAllEditsRequested: function(row) {
            hostRefs.mainDialogs.undoAllEditsDialog.ensure().openFor([row])
        }
        onResetFacesRequested: hostWindow.resetFacesForPaths(
            hostController && photoViewer.aktivSor >= 0
                ? [hostController.photos.filePathAt(photoViewer.aktivSor)] : [])
        // #2566: a jobb fiók a nézőben is nyílik (a panelek a nézőn belül
        // élnek, ld. PhotoViewer.qml). A Helyek-panel két írási művelete
        // UGYANAZON a megerősítésen megy át, mint a könyvtár-nézetben —
        // egy parancs, egy út.
        onClearGeotagRequested: (rows) => hostRefs.mainDialogs.panelClearGeotagDialog.ensure().futtasd(rows)
        onSetGeotagRequested: (rows, la, lo) => hostRefs.mainDialogs.setGeotagDialog.ensure().futtasd(rows, la, lo)
        onDropGeotagRequested: (rows, la, lo) => hostRefs.mainDialogs.dropGeotagDialog.ensure().futtasd(rows, la, lo)
        // #2566: a fiók két KIVEZETŐ parancsa. Mindkettő a könyvtár rácsát
        // cseréli le, amit a néző eltakarna — ezért előbb ZÁRUL a néző.
        // Nem az `onClosed` útján: az `resyncFolderOfRow`-t hív, ami épp a
        // most beállított nézetet írná felül.
        onFindTaggedRequested: function(keyword) {
            if (!hostWindow.aaKapu(function () { photoViewer.findTaggedRequested(keyword) }))
                return
            hostWindow.viewerOpen = false
            if (hostController) hostController.search(keyword)
        }
        onPersonChosen: function(name) {
            if (!hostController) return
            if (!hostWindow.aaKapu(function () { photoViewer.personChosen(name) }))
                return
            hostWindow.viewerOpen = false
            hostWindow.clearSelection()
            hostWindow.unnamedFacesOpen = false
            hostController.showPerson(name)
        }
        onPlayRequested: hostWindow.startSlideshow(currentIndex)
        onStarRequested: function(row) {
            if (hostController) hostController.toggleStar(row)
        }
        onRotateRequested: function(row, delta) {
            if (!hostController) return
            if (delta < 0) hostController.rotateLeft(row)
            else hostController.rotateRight(row)
        }
        // #1002: a néző csak JELEZ — a panel feltöltése és a lapváltás
        // a gazdáé, ugyanúgy, ahogy a `CollagePanel` jelzéseinél.
        onEditCollageRequested: function(path) {
            hostWindow.openSavedCollage(path)
        }
        //: #2114: a film forrásprojektje — a `.mxf` képeit kijelöljük, és
        //: a filmkészítő párbeszéd a projekt diaidejével nyílik.
        onEditMovieRequested: function(path) {
            hostWindow.openSavedMovie(path)
        }
        onClosed: {
            var quickViewWasActive = hostController
                && hostController.quickViewActive === true
            hostWindow.viewerOpen = false
            if (quickViewWasActive) return
            hostWindow.selectedIndex = currentIndex   // a rács kövesse a nézőt
            hostWindow.selectedIndexes = [currentIndex]
            // a szerkesztések (filters=) azonnal látsszanak a rácson —
            // NAS-on a fájlfigyelő nem szól, nem várhatunk a rescanre (#59);
            // a feedben (#64) a néző át is léphetett másik mappába, ezért a
            // nézett kép mappáját frissítjük
            // #173: a megnyitás előtti feed-pozíciót megőrizzük — a resync
            // modellcseréje után NE a mappa elejére ugorjunk. A rögzítés a
            // resync ELŐTT történik (a savedY még a megnyitáskori), az
            // alkalmazás pedig a modellcsere UTÁN (Qt.callLater), illetve az
            // onFeedChanged ágon.
            mainLibraryCanvas.grid.beginRevealAfterViewer()
            hostController.resyncFolderOfRow(currentIndex)
            Qt.callLater(mainLibraryCanvas.grid.applyRevealAfterViewer)
        }
        onCurrentIndexChanged: if (visible) hostWindow.selectedIndex = currentIndex
        // #422: a néző kontextusmenüjének törlés-tétele — a megerősítő
        // dialógusok itt élnek (a menü maga a PhotoViewer-ben)
        // #4621: a néző saját `Ctrl+Delete`-je és a helyi menü tétele is a
        // menüsáv KÖZÖS, nézetfüggő elágazásán megy át
        deleteRemovesFromAlbum: hostRefs.picasaMenuBar.deleteRemovesFromAlbum
        onDeleteRequested: hostRefs.picasaMenuBar.activateDeleteCommand()
    }


    // #5770: az Időrend állapota és ablaka a saját komponensében él.
    MainTimeline {
        id: timelineView
        objectName: "timelineView"
        transientParent: workspace.hostWindow
        hostWindow: workspace.hostWindow
        hostController: workspace.hostController
        hostTimelineController: typeof timelineController !== "undefined"
            ? timelineController : null
        hostToolbar: hostRefs.toolbar
        hostSlideshow: slideshow
    }

    // #985: a dokumentum-fülsáv (#944) a tartalomterület TETEJÉN, az
    // eszköztár alatt. Nyitott projekt-lap nélkül a magassága 0, tehát a mai
    // elrendezés egyetlen képponttal sem csúszik el — ezt a
    // `test_collage_panel_wiring_985.py` külön állítja.
    DocumentTabStrip {
        id: documentTabStrip
        textEntryHasFocus: hostWindow._szovegmezoneVanFokusz
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        projectTabs: hostWindow.openProjectTabs

        // A néző és az Időrend a TELJES ablakot fedi; ilyenkor a sáv se ne
        // látsszon, se ne foglaljon helyet (a komponens `height`-kötését
        // ezért írjuk felül, nem csak a `visible`-t).
        visible: documentTabStrip.hasProjectTabs
                 && !hostWindow.viewerOpen && !hostWindow.timelineOpen
        height: documentTabStrip.visible ? documentTabStrip.savMagassag : 0

        onCloseAccepted: function(tabId, saveDraft) {
            if (tabId === hostWindow.movieMakerTabId) {
                hostWindow.movieMakerTabOpen = false
                return
            }
            if (!hostController || tabId !== hostWindow.collageTabId) return
            // A háromgombos kérdés már eldőlt (#944); itt csak a
            // következményt hajtjuk végre — a piszkozat a Kollázsok albumba
            // megy (#949), majd a lap bezárul.
            if (saveDraft) hostController.saveCollageDraft()
            hostController.closeCollage()
        }
    }

    SplitView {
        id: mainSplit
        objectName: "mainSplit"
        // #985: a `anchors.fill: parent` négy horgonyra bomlik, hogy a
        // tartalom a fülsáv ALATT kezdődjön. Üres sávnál a sáv magassága 0,
        // tehát `documentTabStrip.bottom === parent.top` — a mai elrendezés
        // képpontra ugyanaz marad.
        anchors.top: documentTabStrip.bottom
        anchors.left: parent.left
        //: #3037: a fiók a jobb szélen ül, a könyvtár mellette ér véget —
        //: ez a mért `RIGHTDRAWEROFFSET` viselkedés (a tartalom eltolása).
        anchors.right: jobbFiok.visible ? jobbFiok.left : parent.right
        //: #3503: nyitott Ajándék-CD panelnél a könyvtár a panel fölött ér
        //: véget — a panel nem takarhatja el a képeket
        //: #3504: ugyanez a mentés-panelre is vonatkozik
        anchors.bottom: hostRefs.giftCdHost.visible ? hostRefs.giftCdHost.top
                        : (hostRefs.backupHost.visible ? hostRefs.backupHost.top : parent.bottom)
        // A Könyvtár lapjának tartalma. NEM `Loader.active`: a lap váltásakor
        // a feed nem semmisülhet meg, különben elveszne a görgetési helye és
        // a kijelölése (a #944 kimérte, a #985 tesztje állítja).
        // #1026: a KERET közös kapcsolójára kötve (a `libraryFrameVisible`
        // a `documentTabStrip.libraryActive`-ot hordozza) — így a könyvtár
        // tartalma, az eszközsáv és az alsó sáv EGYSZERRE megy.
        visible: !hostWindow.viewerOpen && !hostWindow.timelineOpen
                 && hostWindow.libraryFrameVisible
        orientation: Qt.Horizontal

        // #322: látható, fogható elválasztó. A Fusion alap-fogantyúja olyan
        // halvány, hogy a felhasználó meg sem találta — ez a delegate a
        // Picasa vékony sávját adja, hover/húzás közben kiemelkedve, és a
        // kurzort is átváltja, hogy a húzhatóság magától látsszon.
        handle: Rectangle {
            objectName: "folderPaneHandle"
            implicitWidth: 6
            implicitHeight: 6
            color: SplitHandle.pressed
                   ? Qt.darker(Theme.chromeBorder, 1.35)
                   : (SplitHandle.hovered
                      ? Qt.darker(Theme.chromeBorder, 1.15)
                      : Theme.chromeBorder)

            Behavior on color {
                ColorAnimation { duration: 100 }
            }

            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.NoButton  // csak a kurzorért
                cursorShape: Qt.SplitHCursor
            }
        }

        MainFolderPane {
            id: folderPane
            objectName: "folderPane"
            // #305: null-őr — a controller a leépítéskor átmenetileg null
            SplitView.preferredWidth: hostController ? hostController.folderPaneWidth : 240
            //: #2329: MÉRT korlátok. A legkisebb szélesség ugyanaz a szám,
            //: mint az alapértelmezés (240) — a hasáb nem húzható alá.
            SplitView.minimumWidth: 240
            //: A felső korlát az eredetiben ABLAKFÜGGŐ: a főpanel
            //: szélessége mínusz 240 (`0x009d9e21`–`0x009d9e50`). A fix 600
            //: széles ablakon szűkebb volt az eredetinél, keskenyen pedig
            //: tágabb. A `Math.max` azért kell, hogy nagyon keskeny
            //: ablakon se csússzon a maximum a minimum ALÁ — a `SplitView`
            //: ilyenkor kiszámíthatatlanul viselkedne.
            SplitView.maximumWidth: Math.max(240, mainSplit.width - 240)

            hostWindow: workspace.hostWindow
            hostController: workspace.hostController
            hostToolbar: hostRefs.toolbar
            hostBackupHost: hostRefs.backupHost
            hostFileOpsDialogs: workspace.hostWindow.fileOpsDialogs
            hostCollectionPasswordDialog: workspace.hostWindow.collectionPasswordDialog
            hostFileOpsController: typeof fileOpsController !== "undefined"
                ? fileOpsController : null
            hostFaceScanController: typeof faceScanController !== "undefined"
                ? faceScanController : null
            hostFolderHierarchyController: typeof folderHierarchyController !== "undefined"
                ? folderHierarchyController : null
        }

        MainLibraryCanvas {
            id: mainLibraryCanvas
            hostWindow: workspace.hostWindow
            hostController: workspace.hostController
            hostToolbar: hostRefs.toolbar
            hostSearchSuggestionsBox: hostRefs.searchSuggestionsBox
            hostBackupHost: hostRefs.backupHost
            hostRightDrawerHandle: jobbFiokFogo
            hostPeoplePanel: jobbFiok.peoplePanel
        }

    }

    MainRightDrawer {
        id: jobbFiok
        hostWindow: workspace.hostWindow
        hostController: workspace.hostController
        hostToolbar: hostRefs.toolbar
        hostPhotoViewer: photoViewer
        hostMainSplit: mainSplit
        hostMainLibraryCanvas: mainLibraryCanvas
        hostMainDialogs: hostRefs.mainDialogs
        propertiesLabel: qsTr("Properties")
        tagsLabel: qsTr("Tags:")
        peopleLabel: qsTr("People")
        placesLabel: qsTr("Places")
    }

    //: #3035: `m_fakehidden` (`thumbui.tre:696`) — NEM LÁTSZÓ, de
    //: kattintható sáv a fiók szélén, ami billenti a fiókot. Csukott
    //: fióknál is ott van: ez a MÁSIK belépési pont a Nézet menü mellett.
    Rectangle {
        id: jobbFiokFogo
        objectName: "toggle_right_drawer"
        //: a `kattints()` a próbáké is: a vezérlőre kattintunk, nem a
        //: kezelő metódusát hívjuk
        function kattints() { hostWindow.billentsdAFiokot() }
        visible: mainSplit.visible
        opacity: 0
        width: 6
        anchors.top: mainSplit.top
        anchors.bottom: mainSplit.bottom
        anchors.right: jobbFiok.visible ? jobbFiok.left : parent.right
        color: "transparent"
        TapHandler { onTapped: jobbFiokFogo.kattints() }
    }

    // #985: a Kollázs LAP tartalma — a Könyvtár lapjának TESTVÉRE, ugyanazon
    // a helyen. Az eredetiben a `panelroot/collagetab` a `panelroot/picasatab`
    // testvére, tehát a kollázs a mappapanellel EGYÜTT váltja le a könyvtárat
    // (`picasa-kollazs-felulet.md` 8.: a „Továbbiak..." visszavált a
    // `picasatab`-ra). A panel a saját bal hasábját hozza magával.
    // #1612: a panel az induláskor NEM látszik (külön dokumentum-lap), a
    // komponensenkénti mérés szerint viszont 74,5 ms-ba kerül. Ezért
    // `Loader` mögött él: az ELSŐ megnyitásig nem jön létre, utána viszont
    // MEGMARAD (`betoltve` ragadós) — a félkész kollázs nem veszhet el egy
    // fülváltáson. A `visible` feltétel változatlan, csak a betöltőre került.
    Loader {
        id: collagePanelLoader
        objectName: "collagePanelLoader"
        anchors.top: documentTabStrip.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        readonly property bool kellene: !hostWindow.viewerOpen && !hostWindow.timelineOpen
                 && documentTabStrip.activeTabId === hostWindow.collageTabId
        property bool betoltve: false
        onKelleneChanged: if (kellene) betoltve = true
        active: kellene || betoltve
        visible: kellene
        sourceComponent: collagePanelKomponens
    }

    Component {
        id: collagePanelKomponens

        CollagePanel {
            id: collagePanel
            // az álnév a kötési hurkot kerüli ki (ld. `appController`)
            controller: hostWindow.appController
            librarySelection: hostWindow.selectedIndexes

            // #1028: a mentés VÉGE — a panel jelez, a navigáció a gazdáé
            onCollageSaved: function(path) { hostWindow.locateSavedCollage(path) }

            // spec 4.3/13.: a panel csak JELEZ, a fülváltás a gazdáé
            onGetMoreClipsRequested: {
                hostWindow.backToCollagePrompted = true
                documentTabStrip.activateTab(documentTabStrip.libraryTabId)
            }
        }
    }

    // #1001: a „Megjelenítés és szerkesztés" FOGADÓJA. A parancs három
    // helyről indul (a `CollageRandomRow` gombja, a `CollageNode`
    // duplakattintása és a `CollageContextMenus` tétele), de mind a három a
    // vezérlő `viewAndEditSelection()`-jébe fut, tehát EGY fogadó elég — és
    // egy is kell, mert a lapváltás meg a néző a gazdáé, nem a panelé.
    Connections {
        target: hostController
        function onCollageEditRequested(path) {
            hostWindow.openCollageNodeInEditor(path)
        }
    }

}
