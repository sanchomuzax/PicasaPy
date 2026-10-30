import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import PicasaPy

Item {
    id: root
    objectName: "mainLibraryWorkspace"

    required property var hostWindow
    required property var hostController
    required property var hostToolbar
    required property var hostPhotoViewer
    required property var hostMainDialogs
    required property var hostBackupHost
    required property var hostGiftCdHost
    required property var hostSearchSuggestionsBox
    required property var hostCollectionPasswordDialog
    required property var hostFileOpsDialogs
    required property var hostFileOpsController
    required property var hostFaceScanController
    required property var hostFolderHierarchyController
    required property string propertiesLabel
    required property string tagsLabel
    required property string peopleLabel
    required property string placesLabel

    property alias documentTabStrip: _documentTabStrip
    property alias mainSplit: _mainSplit
    property alias folderPane: _folderPane
    property alias mainLibraryCanvas: _mainLibraryCanvas
    property alias rightDrawer: _jobbFiok
    property alias rightDrawerHandle: _jobbFiokFogo
    property alias peoplePanel: _jobbFiok.peoplePanel

    // #985: a dokumentum-fülsáv (#944) a tartalomterület TETEJÉN, az
    // eszköztár alatt. Nyitott projekt-lap nélkül a magassága 0, tehát a mai
    // elrendezés egyetlen képponttal sem csúszik el — ezt a
    // `test_collage_panel_wiring_985.py` külön állítja.
    DocumentTabStrip {
        id: _documentTabStrip
        textEntryHasFocus: root.hostWindow._szovegmezoneVanFokusz
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        projectTabs: root.hostWindow.openProjectTabs

        // A néző és az Időrend a TELJES ablakot fedi; ilyenkor a sáv se ne
        // látsszon, se ne foglaljon helyet (a komponens `height`-kötését
        // ezért írjuk felül, nem csak a `visible`-t).
        visible: _documentTabStrip.hasProjectTabs
                 && !root.hostWindow.viewerOpen && !root.hostWindow.timelineOpen
        height: _documentTabStrip.visible ? _documentTabStrip.savMagassag : 0

        onCloseAccepted: function(tabId, saveDraft) {
            if (tabId === root.hostWindow.movieMakerTabId) {
                root.hostWindow.movieMakerTabOpen = false
                return
            }
            if (!root.hostController || tabId !== root.hostWindow.collageTabId) return
            // A háromgombos kérdés már eldőlt (#944); itt csak a
            // következményt hajtjuk végre — a piszkozat a Kollázsok albumba
            // megy (#949), majd a lap bezárul.
            if (saveDraft) root.hostController.saveCollageDraft()
            root.hostController.closeCollage()
        }
    }

    SplitView {
        id: _mainSplit
        objectName: "mainSplit"
        // #985: a `anchors.fill: parent` négy horgonyra bomlik, hogy a
        // tartalom a fülsáv ALATT kezdődjön. Üres sávnál a sáv magassága 0,
        // tehát `documentTabStrip.bottom === parent.top` — a mai elrendezés
        // képpontra ugyanaz marad.
        anchors.top: _documentTabStrip.bottom
        anchors.left: parent.left
        //: #3037: a fiók a jobb szélen ül, a könyvtár mellette ér véget —
        //: ez a mért `RIGHTDRAWEROFFSET` viselkedés (a tartalom eltolása).
        anchors.right: _jobbFiok.visible ? _jobbFiok.left : parent.right
        //: #3503: nyitott Ajándék-CD panelnél a könyvtár a panel fölött ér
        //: véget — a panel nem takarhatja el a képeket
        //: #3504: ugyanez a mentés-panelre is vonatkozik
        anchors.bottom: parent.bottom
        anchors.bottomMargin: root.hostGiftCdHost.visible
            ? parent.height - root.hostGiftCdHost.y
            : (root.hostBackupHost.visible
               ? parent.height - root.hostBackupHost.y : 0)
        // A Könyvtár lapjának tartalma. NEM `Loader.active`: a lap váltásakor
        // a feed nem semmisülhet meg, különben elveszne a görgetési helye és
        // a kijelölése (a #944 kimérte, a #985 tesztje állítja).
        // #1026: a KERET közös kapcsolójára kötve (a `libraryFrameVisible`
        // a `documentTabStrip.libraryActive`-ot hordozza) — így a könyvtár
        // tartalma, az eszközsáv és az alsó sáv EGYSZERRE megy.
        visible: !root.hostWindow.viewerOpen && !root.hostWindow.timelineOpen
                 && root.hostWindow.libraryFrameVisible
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
            id: _folderPane
            objectName: "folderPane"
            // #305: null-őr — a controller a leépítéskor átmenetileg null
            SplitView.preferredWidth: root.hostController ? root.hostController.folderPaneWidth : 240
            //: #2329: MÉRT korlátok. A legkisebb szélesség ugyanaz a szám,
            //: mint az alapértelmezés (240) — a hasáb nem húzható alá.
            SplitView.minimumWidth: 240
            //: A felső korlát az eredetiben ABLAKFÜGGŐ: a főpanel
            //: szélessége mínusz 240 (`0x009d9e21`–`0x009d9e50`). A fix 600
            //: széles ablakon szűkebb volt az eredetinél, keskenyen pedig
            //: tágabb. A `Math.max` azért kell, hogy nagyon keskeny
            //: ablakon se csússzon a maximum a minimum ALÁ — a `SplitView`
            //: ilyenkor kiszámíthatatlanul viselkedne.
            SplitView.maximumWidth: Math.max(240, _mainSplit.width - 240)

            hostWindow: root.hostWindow
            hostController: root.hostController
            hostToolbar: root.hostToolbar
            hostBackupHost: root.hostBackupHost
            hostFileOpsDialogs: root.hostFileOpsDialogs
            hostCollectionPasswordDialog: root.hostCollectionPasswordDialog
            hostFileOpsController: typeof root.hostFileOpsController !== "undefined"
                ? root.hostFileOpsController : null
            hostFaceScanController: typeof root.hostFaceScanController !== "undefined"
                ? root.hostFaceScanController : null
            hostFolderHierarchyController: typeof root.hostFolderHierarchyController !== "undefined"
                ? root.hostFolderHierarchyController : null
        }

        MainLibraryCanvas {
            id: _mainLibraryCanvas
            hostWindow: root.hostWindow
            hostController: root.hostController
            hostToolbar: root.hostToolbar
            hostSearchSuggestionsBox: root.hostSearchSuggestionsBox
            hostBackupHost: root.hostBackupHost
            hostRightDrawerHandle: _jobbFiokFogo
            hostPeoplePanel: root.peoplePanel
        }

    }

    MainRightDrawer {
        id: _jobbFiok
        hostWindow: root.hostWindow
        hostController: root.hostController
        hostToolbar: root.hostToolbar
        hostPhotoViewer: root.hostPhotoViewer
        hostMainSplit: _mainSplit
        hostMainLibraryCanvas: _mainLibraryCanvas
        hostMainDialogs: root.hostMainDialogs
        propertiesLabel: root.propertiesLabel
        tagsLabel: root.tagsLabel
        peopleLabel: root.peopleLabel
        placesLabel: root.placesLabel
    }

    //: #3035: `m_fakehidden` (`thumbui.tre:696`) — NEM LÁTSZÓ, de
    //: kattintható sáv a fiók szélén, ami billenti a fiókot. Csukott
    //: fióknál is ott van: ez a MÁSIK belépési pont a Nézet menü mellett.
    Rectangle {
        id: _jobbFiokFogo
        objectName: "toggle_right_drawer"
        //: a `kattints()` a próbáké is: a vezérlőre kattintunk, nem a
        //: kezelő metódusát hívjuk
        function kattints() { root.hostWindow.billentsdAFiokot() }
        visible: _mainSplit.visible
        opacity: 0
        width: 6
        anchors.top: _mainSplit.top
        anchors.bottom: _mainSplit.bottom
        anchors.right: _jobbFiok.visible ? _jobbFiok.left : parent.right
        color: "transparent"
        TapHandler { onTapped: _jobbFiokFogo.kattints() }
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
        anchors.top: _documentTabStrip.bottom
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        readonly property bool kellene: !root.hostWindow.viewerOpen && !root.hostWindow.timelineOpen
                 && _documentTabStrip.activeTabId === root.hostWindow.collageTabId
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
            controller: root.hostWindow.appController
            librarySelection: root.hostWindow.selectedIndexes

            // #1028: a mentés VÉGE — a panel jelez, a navigáció a gazdáé
            onCollageSaved: function(path) { root.hostWindow.locateSavedCollage(path) }

            // spec 4.3/13.: a panel csak JELEZ, a fülváltás a gazdáé
            onGetMoreClipsRequested: {
                root.hostWindow.backToCollagePrompted = true
                _documentTabStrip.activateTab(_documentTabStrip.libraryTabId)
            }
        }
    }

    // #1001: a „Megjelenítés és szerkesztés" FOGADÓJA. A parancs három
    // helyről indul (a `CollageRandomRow` gombja, a `CollageNode`
    // duplakattintása és a `CollageContextMenus` tétele), de mind a három a
    // vezérlő `viewAndEditSelection()`-jébe fut, tehát EGY fogadó elég — és
    // egy is kell, mert a lapváltás meg a néző a gazdáé, nem a panelé.
    Connections {
        target: root.hostController
        function onCollageEditRequested(path) {
            root.hostWindow.openCollageNodeInEditor(path)
        }
    }

    }
