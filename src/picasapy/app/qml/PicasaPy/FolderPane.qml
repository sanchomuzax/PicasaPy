import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window

// Bal oldali gyűjtemény-hasáb — Picasa "Folder List" gyökere (#320): öt
// önálló, csukható gyűjtemény (Albumok/Emberek/Projektek/Mappák/Egyéb),
// mindegyik saját fejléccel; csak a Mappák gyűjtemény tagolt évszám-
// szakaszokra (ld. docs/specs/ui-audit-mainwindow.md, mappafa szakasz).
Rectangle {
    id: pane
    color: Theme.panelBg

    // #384: constants.ui alist_selcolor_win/alist_scatcolor (#25648B) —
    // a VALÓDI kijelölés sötétebb, mint a hover/jelölő tónus
    // (Theme.panelSelection = #83a7bd, alist_hicolor_win). A Theme.qml-ben
    // MÉG NINCS erre saját token (hot file, ld. jelentés:
    // Theme.panelSelectionActive) — amíg az integrátor fel nem veszi, itt
    // helyi állandóként él; a csere csak ezt a sort érinti.

    property alias foldersModel: folderList.model
    property string selectedPath: ""
    property bool starredActive: false
    property bool searchActive: false
    property string searchQuery: ""
    property int searchResultCount: 0
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
    property bool unnamedFacesActive: false
    signal folderChosen(string path)
    signal starredChosen()
    signal albumChosen(string token)
    signal personChosen(string name)
    signal unnamedFacesChosen()

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
    function openFolderContextMenu(path) {
        folderContextMenu.folderPath = path
        folderContextMenu.customCollections = pane.customCollectionsModel
        // #422: a rendezés-almenü pipái a jelenlegi rács-rendezést mutatják
        if (controller) {
            folderContextMenu.sortMode = controller.folderSort
            folderContextMenu.sortReverse = controller.folderSortReverse
        }
        folderContextMenu.popup()
    }

    // #422: a bal panel saját menüjének megnyitása — a pipák a menü
    // nyitásakor veszik át a vezérlő friss rendezés-állapotát
    function openFolderListContextMenu() {
        if (controller) {
            folderListContextMenu.sortMode = controller.folderSort
            folderListContextMenu.sortReverse = controller.folderSortReverse
        }
        folderListContextMenu.popup()
    }

    // #422 (4. lépcső): az album / Emberek-album jobbklikk-menüje — a
    // sor-delegátumból (Repeater-elem) kiszervezve pane-szintű, névvel
    // hívható függvénybe, a mappa-menü mintájára
    function openAlbumContextMenu(token, name) {
        albumContextMenu.albumToken = token
        albumContextMenu.albumName = name
        albumContextMenu.popup()
    }
    function openPeopleAlbumContextMenu(name) {
        peopleAlbumContextMenu.personName = name
        peopleAlbumContextMenu.popup()
    }

    // #422 (utolsó menü): a felhasználói gyűjtemény jobbklikk-menüjének
    // megnyitása — az album-menü mintájára, pane-szintű, névvel hívható
    // függvényben (tesztelhetőség).
    function openCollectionContextMenu(name) {
        collectionContextMenu.collectionName = name
        collectionContextMenu.popup()
    }

    // #422: melyik gyűjtemény átnevezése fut éppen a newCollectionDialog-on
    // keresztül — üres string esetén a dialógus a régi
    // "létrehozás" ágon fut (createCollection + esetleg
    // moveFolderToCollection), nem üres esetén az átnevezés ágon
    // (renameCollection). A newCollectionDialog egyetlen példány, ezt a
    // property-t kell megnézni a created(name) jelre.
    property string _renamingCollection: ""

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
        if (!folderList.model) return
        var target = folderList.model.neighborFolder(pane.selectedPath, delta)
        if (target !== "" && target !== pane.selectedPath)
            pane.folderChosen(target)
    }
    property real wheelAccum: 0
    function wheelStep(delta) {
        wheelAccum += delta
        while (wheelAccum <= -120) { wheelAccum += 120; stepFolder(1) }
        while (wheelAccum >= 120) { wheelAccum -= 120; stepFolder(-1) }
    }
    // a kijelölt mappa maradjon látótérben (kívülről is változhat:
    // kereső-javaslat, feed-görgetés)
    onSelectedPathChanged: {
        if (!folderList.model) return
        var row = folderList.model.rowOfPath(pane.selectedPath)
        if (row >= 0) folderList.positionViewAtIndex(row, ListView.Contain)
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

    // A görgő-kezelő a pane gyökerén él: Flickable-be (ListView) ágyazott
    // pointer-handler nem támogatott, és itt a fejléc-sávok fölött is működik.
    WheelHandler {
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        onWheel: function(event) { pane.wheelStep(event.angleDelta.y) }
    }

    // Egy gyűjtemény-fejléc: zöld ▼ (nyitva) / piros ▶ (csukva) háromszög +
    // felirat, a meglévő fejléc-gradienssel. A `headerText` felülírhatja a
    // "label (itemCount)" alapértelmezést (pl. kereső-eredmény szövege).
    component CollectionHeader: Rectangle {
        id: header
        property string label: ""
        property int itemCount: 0
        property string headerText: ""
        property string labelObjectName: ""
        property bool collapsed: false
        signal toggled()
        // #422: a felhasználói gyűjtemény-fejléc jobbklikk-menüjéhez — a
        // beépített öt gyűjtemény fejléce (Albumok/Emberek/…) nem köti be,
        // csak a customCollectionsRepeater-beli példány (ld. lent).
        signal rightClicked()

        // a sor saját objectName-je a fejlécéből képezve (teszthez: a
        // "toggled" jel innen közvetlenül kiváltható, ahogy a projektben
        // szokásos egyedi gombok "clicked" jelének közvetlen hívása)
        objectName: header.labelObjectName !== "" ? header.labelObjectName + "Row" : ""
        height: 22
        gradient: Gradient {
            GradientStop { position: 0.0; color: Theme.panelHeaderTop }
            GradientStop { position: 1.0; color: Theme.panelHeaderBg }
        }
        border.color: Theme.chromeBorder
        Row {
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left; anchors.leftMargin: 4
            spacing: 4
            Text {
                text: header.collapsed ? "▶" : "▼"
                font.pixelSize: 8
                // Audit: az eredeti Picasában a nyitott gyűjtemény zöld, a
                // csukott piros — ez itt ÁLLAPOT-jelzés, nem márka-szerep;
                // külön "collapsed" jelzőszín híján a brandRed tokent
                // kölcsönözzük erre a célra.
                color: header.collapsed ? Theme.brandRed : Theme.picasaGreen
            }
            Text {
                objectName: header.labelObjectName
                text: header.headerText !== "" ? header.headerText
                      : header.label + " (" + header.itemCount + ")"
                font.pixelSize: Theme.fontSize; font.bold: true
                color: Theme.panelHeaderText
            }
        }
        MouseArea {
            anchors.fill: parent
            onClicked: header.toggled()
        }
        // #422: jobbklikk a gyűjtemény-menühöz — a mappasor/albumsor
        // mintáját követve TapHandler-rel (ReleaseWithinBounds), hogy a
        // sima MouseArea bal-kattintás-kezelését ne zavarja.
        TapHandler {
            acceptedButtons: Qt.RightButton
            gesturePolicy: TapHandler.ReleaseWithinBounds
            onTapped: header.rightClicked()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("Albums")
            // #9: 1 a csillagozott sorért + az összes virtuális album
            itemCount: 1 + pane.albumsModel.length
            labelObjectName: "albumsHeader"
            collapsed: pane.albumsCollapsed
            onToggled: pane.toggleCollection("albums")
        }

        Rectangle {
            id: starredItem
            objectName: "starredItem"
            visible: !pane.albumsCollapsed
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            // #384: hover ≠ kijelölés — a hover a korábbi jelölő tónust
            // kapja, a tényleges kijelölés a hitelesebb, sötétebb színt.
            color: pane.starredActive ? Theme.panelSelectionActive
                   : (starredMouse.containsMouse ? Theme.panelSelection : "transparent")
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 16
                spacing: 5
                Text { text: "★"; color: Theme.starYellow; font.pixelSize: Theme.fontSize }
                Text {
                    text: qsTr("Starred photos")
                    font.pixelSize: Theme.fontSize
                    color: pane.starredActive || starredMouse.containsMouse
                           ? Theme.panelSelectionText : Theme.textDark
                }
            }
            MouseArea {
                id: starredMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: pane.starredChosen()
            }
        }

        // #9: a virtuális albumok a csillagozott sor ALATT, ugyanabban
        // az Albumok gyűjteményben — mindegyik album név + darabszám sor.
        Repeater {
            id: albumRepeater
            objectName: "albumRepeater"
            model: pane.albumsModel
            delegate: Rectangle {
                id: albumItem
                required property var modelData
                objectName: "albumItem_" + modelData.token
                readonly property bool isSelectedAlbum:
                    pane.selectedAlbumToken === modelData.token
                visible: !pane.albumsCollapsed
                Layout.fillWidth: true
                Layout.preferredHeight: 22
                // #384: hover ≠ kijelölés (ld. starredItem fent)
                color: albumItem.isSelectedAlbum ? Theme.panelSelectionActive
                       : (albumMouse.containsMouse ? Theme.panelSelection : "transparent")
                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 16
                    spacing: 5
                    Rectangle {
                        width: 10; height: 8
                        radius: 1
                        anchors.verticalCenter: parent.verticalCenter
                        color: Theme.picasaGreen
                    }
                    Text {
                        text: modelData.name + " (" + modelData.count + ")"
                        font.pixelSize: Theme.fontSize
                        color: albumItem.isSelectedAlbum || albumMouse.containsMouse
                               ? Theme.panelSelectionText : Theme.textDark
                    }
                }
                MouseArea {
                    id: albumMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: function(mouse) {
                        // #422: jobbklikk = az album menüje; bal = megnyitás
                        if (mouse.button === Qt.RightButton) {
                            pane.openAlbumContextMenu(
                                albumItem.modelData.token,
                                albumItem.modelData.name)
                            return
                        }
                        pane.albumChosen(albumItem.modelData.token)
                    }
                }
            }
        }

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("People")
            // #26: a `faces=`/`[Contacts2]`-ből aggregált, névvel ellátott
            // személyek száma (arcfelismerés nélkül — a meglévő ini-
            // adatokból, ld. picasapy.index.people).
            itemCount: pane.peopleModel.length
            labelObjectName: "peopleHeader"
            collapsed: pane.peopleCollapsed
            onToggled: pane.toggleCollection("people")
        }

        // #26: egy-egy sor személyenként — az albumRepeater mintáját követi.
        Repeater {
            id: peopleRepeater
            objectName: "peopleRepeater"
            model: pane.peopleModel
            delegate: Rectangle {
                id: personItem
                required property var modelData
                objectName: "personItem_" + modelData.name
                readonly property bool isSelectedPerson:
                    pane.selectedPersonName === modelData.name
                visible: !pane.peopleCollapsed
                Layout.fillWidth: true
                Layout.preferredHeight: 22
                color: personItem.isSelectedPerson ? Theme.panelSelectionActive
                       : (personMouse.containsMouse ? Theme.panelSelection : "transparent")
                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 16
                    spacing: 5
                    Rectangle {
                        width: 10; height: 10
                        radius: 5
                        anchors.verticalCenter: parent.verticalCenter
                        color: Theme.picasaGreen
                    }
                    Text {
                        text: modelData.name + " (" + modelData.count + ")"
                        font.pixelSize: Theme.fontSize
                        color: personItem.isSelectedPerson || personMouse.containsMouse
                               ? Theme.panelSelectionText : Theme.textDark
                    }
                }
                MouseArea {
                    id: personMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: function(mouse) {
                        // #422: jobbklikk = az Emberek-album menüje
                        if (mouse.button === Qt.RightButton) {
                            pane.openPeopleAlbumContextMenu(
                                personItem.modelData.name)
                            return
                        }
                        pane.personChosen(personItem.modelData.name)
                    }
                }
            }
        }

        // #26 (3. lépcső): a „Névtelenek" sor — a személyek listája ALATT,
        // ugyanabban az Emberek gyűjteményben (a personRepeater mintáját
        // követi, de nincs saját modell-elem, csak egy darabszám).
        Rectangle {
            id: unnamedFacesItem
            objectName: "unnamedFacesItem"
            visible: !pane.peopleCollapsed && pane.unnamedFaceCount > 0
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            color: pane.unnamedFacesActive ? Theme.panelSelectionActive
                   : (unnamedFacesMouse.containsMouse ? Theme.panelSelection : "transparent")
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 16
                spacing: 5
                Rectangle {
                    width: 10; height: 10
                    radius: 5
                    anchors.verticalCenter: parent.verticalCenter
                    color: Theme.textDark
                    opacity: 0.45
                }
                Text {
                    text: qsTr("Unnamed") + " (" + pane.unnamedFaceCount + ")"
                    font.pixelSize: Theme.fontSize
                    color: pane.unnamedFacesActive || unnamedFacesMouse.containsMouse
                           ? Theme.panelSelectionText : Theme.textDark
                }
            }
            MouseArea {
                id: unnamedFacesMouse
                anchors.fill: parent
                hoverEnabled: true
                onClicked: pane.unnamedFacesChosen()
            }
        }

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("Projects")
            // #320: a tartalom forrása még kutatás alatt — egyelőre üres.
            itemCount: 0
            labelObjectName: "projectsHeader"
            collapsed: pane.projectsCollapsed
            onToggled: pane.toggleCollection("projects")
        }

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("Folders")
            itemCount: folderList.model ? folderList.model.folderCount : 0
            headerText: pane.searchActive
                        ? qsTr("Search results for \"%1\" (%2)")
                          .arg(pane.searchQuery).arg(pane.searchResultCount)
                        : ""
            labelObjectName: "folderPaneHeader"
            collapsed: pane.foldersCollapsed
            onToggled: pane.toggleCollection("folders")
        }

        ListView {
            id: folderList
            objectName: "folderListView"
            visible: !pane.foldersCollapsed
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true

            // kurzorgombok, amikor a lista fókuszban van (#77)
            activeFocusOnTab: true
            Keys.onUpPressed: pane.stepFolder(-1)
            Keys.onDownPressed: pane.stepFolder(1)

            // A háttér-szinkron utáni modell-frissítés ne nullázza a
            // görgetési pozíciót — enélkül a lista folyton visszaugrik,
            // és nem lehet görgetni. A reset 0-ra ugrása nem írhatja
            // felül a mentett pozíciót (#10, a fotórács mintájára).
            property real savedY: 0
            property bool restoring: false
            onContentYChanged: {
                if (!restoring && (contentY > 0 || moving))
                    savedY = contentY
            }
            onMovementEnded: savedY = contentY
            Connections {
                target: folderList.model
                function onFolderCountChanged() {
                    folderList.restoring = true
                    folderList.contentY = Math.min(
                        folderList.savedY,
                        Math.max(0, folderList.contentHeight
                                    - folderList.height))
                    folderList.restoring = false
                }
            }
            delegate: Rectangle {
                required property string kind
                required property string name
                required property string path
                required property int count
                // #459/5: „jelenleg nem elérhető" mappa (levált NAS-mount,
                // kihúzott lemez) — a sor bennmarad, csak jelölést kap.
                required property bool offline
                width: folderList.width; height: 22
                // #9: album-nézetben a mappa-kijelölés szűnjön meg — a
                // hasábon csak az aktív album sora legyen kiemelve.
                readonly property bool isSelectedFolder:
                    kind === "folder" && pane.selectedPath === path
                    && pane.selectedAlbumToken === ""
                // #384: hover ≠ kijelölés (ld. starredItem/albumItem) —
                // a "year" sorok nem kattinthatók, a MouseArea rájuk
                // enabled: false, így containsMouse mindig false marad.
                color: isSelectedFolder ? Theme.panelSelectionActive
                       : (folderRowMouse.containsMouse ? Theme.panelSelection : "transparent")

                // évszám-elválasztó: arányos betűs címke + vékony
                // vízszintes elválasztó vonal a panel széléig (audit:
                // docs/specs/ui-audit-mainwindow.md, mappafa szakasz)
                Text {
                    id: yearLabel
                    visible: kind === "year"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 6
                    text: name
                    font.pixelSize: Theme.fontSize
                    color: Theme.panelYearText
                }
                Rectangle {
                    visible: kind === "year"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: yearLabel.right; anchors.leftMargin: 6
                    anchors.right: parent.right; anchors.rightMargin: 6
                    height: 1
                    color: Theme.chromeBorder
                }

                Row {
                    // Audit (ui-audit-mainwindow.md, mappafa 1.3/8): az
                    // eredeti Picasa mappasorai nem nyithatók (nincs
                    // almappa-szint a lapos Mappák-listában), ezért nincs
                    // nyílglif előttük sem — csak a sárga mappaikon + név.
                    visible: kind === "folder"
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 12
                    spacing: 5
                    FolderIcon {
                        size: 13
                        anchors.verticalCenter: parent.verticalCenter
                        // az elérhetetlen mappa ikonja halvány (#459/5)
                        opacity: offline ? 0.45 : 1.0
                    }
                    Text {
                        objectName: "folderRowLabel"
                        text: name + " (" + count + ")"
                        font.pixelSize: Theme.fontSize
                        // #459/5: a nem elérhető mappa dőlt és halvány —
                        // a sor kattintható marad (a bélyegképek a
                        // gyorsítótárból még látszanak), csak jelzi az
                        // állapotot; a részletet a súgószöveg mondja el.
                        font.italic: offline
                        opacity: offline ? 0.55 : 1.0
                        color: isSelectedFolder || folderRowMouse.containsMouse
                               ? Theme.panelSelectionText : Theme.ink
                    }
                }
                ToolTip.visible: offline && folderRowMouse.containsMouse
                ToolTip.text: qsTr("Currently unavailable — the folder stays in the database, thumbnails come from the cache.")
                MouseArea {
                    id: folderRowMouse
                    enabled: kind === "folder"
                    hoverEnabled: true
                    anchors.fill: parent
                    acceptedButtons: Qt.LeftButton | Qt.RightButton
                    onClicked: function(mouse) {
                        folderList.forceActiveFocus()   // kurzorgombokhoz (#77)
                        if (mouse.button === Qt.RightButton) {
                            pane.openFolderContextMenu(path)
                            return
                        }
                        pane.folderChosen(path)
                    }
                }
            }
            ScrollBar.vertical: PicasaScrollBar {}
        }

        // #476: a felhasználói mappa-gyűjtemények (#320 óta léteznek, de
        // eddig sehol nem jelentek meg) — a beépített "Mappák" gyűjtemény
        // ALATT, az "Egyéb" fejléc ELŐTT, gyűjteményenként egy csukható
        // fejléc + a hozzá sorolt mappák sorai (az albumRepeater/folderList
        // sor-mintáját követve).
        Repeater {
            id: customCollectionsRepeater
            objectName: "customCollectionsRepeater"
            model: pane.customCollectionsModel
            delegate: Column {
                id: customCollectionItem
                required property var modelData
                objectName: "customCollectionItem_" + customCollectionItem.modelData.name
                Layout.fillWidth: true
                spacing: 0

                CollectionHeader {
                    width: customCollectionItem.width
                    label: customCollectionItem.modelData.name
                    itemCount: customCollectionItem.modelData.folders.length
                    labelObjectName: "customCollection_" + customCollectionItem.modelData.name
                    collapsed: pane.isCustomCollectionCollapsed(customCollectionItem.modelData.name)
                    onToggled: pane.toggleCustomCollection(customCollectionItem.modelData.name)
                    onRightClicked: pane.openCollectionContextMenu(
                        customCollectionItem.modelData.name)
                }

                Repeater {
                    objectName: "customCollectionFoldersRepeater_" + customCollectionItem.modelData.name
                    model: customCollectionItem.modelData.folders
                    delegate: Rectangle {
                        id: customFolderItem
                        required property var modelData
                        objectName: "customCollectionFolder_" + customFolderItem.modelData
                        readonly property bool isSelectedFolder:
                            pane.selectedPath === customFolderItem.modelData
                            && pane.selectedAlbumToken === ""
                        visible: !pane.isCustomCollectionCollapsed(customCollectionItem.modelData.name)
                        width: customCollectionItem.width
                        height: 22
                        color: customFolderItem.isSelectedFolder ? Theme.panelSelectionActive
                               : (customFolderMouse.containsMouse ? Theme.panelSelection : "transparent")
                        Row {
                            anchors.verticalCenter: parent.verticalCenter
                            anchors.left: parent.left; anchors.leftMargin: 16
                            spacing: 5
                            FolderIcon { size: 13; anchors.verticalCenter: parent.verticalCenter }
                            Text {
                                text: customFolderItem.modelData.substring(
                                          customFolderItem.modelData.lastIndexOf("/") + 1)
                                font.pixelSize: Theme.fontSize
                                color: customFolderItem.isSelectedFolder || customFolderMouse.containsMouse
                                       ? Theme.panelSelectionText : Theme.ink
                            }
                        }
                        MouseArea {
                            id: customFolderMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            onClicked: pane.folderChosen(customFolderItem.modelData)
                        }
                    }
                }
            }
        }

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("Other")
            // #320: még nincs kijelölt tartalom-forrás ehhez a
            // gyűjteményhez — a fejléc addig is látszik, üresen.
            itemCount: 0
            labelObjectName: "otherHeader"
            collapsed: pane.otherCollapsed
            onToggled: pane.toggleCollection("other")
        }
    }

    // #320: a mappasor jobbklikk-menüje + a hozzá tartozó két kis
    // dialógus (önálló, signal-alapú komponensek — ld. FolderContextMenu/
    // NewCollectionDialog/FolderDateDialog.qml). A controller-kötést itt,
    // a FolderPane.qml-ben végezzük (nem forró fájl) — a hívott
    // controller-slotok (createCollection, moveFolderToCollection,
    // setFolderDate, clearFolderDate, customCollections) az AppController
    // öröklés-listájának bővítésével válnak élővé (controller.py, forró
    // fájl — az integrátor dolga).
    // #422: a fő ablak a kijelölés-parancsokhoz és a webexport-dialógushoz
    // (a PhotoViewer.qml `Window.window` mintája — így a forró Main.qml-hez
    // nem kell hozzányúlni; önálló példányosításnál egyszerűen hiányzik)
    readonly property var appWindow: Window.window

    AlbumContextMenu {
        id: albumContextMenu
        onSelectAllRequested:
            if (pane.appWindow && pane.appWindow.selectAll) pane.appWindow.selectAll()
        onClearSelectionRequested:
            if (pane.appWindow && pane.appWindow.clearSelection)
                pane.appWindow.clearSelection()
        onInvertSelectionRequested:
            if (pane.appWindow && pane.appWindow.invertSelection)
                pane.appWindow.invertSelection()
        // az album tartalma a jelenlegi mappákból áll — a frissítés a
        // megnyitott mappa újraszinkronja (a mappa-menü mintája)
        onRefreshThumbnailsRequested:
            if (controller) controller.resyncFolder(controller.currentFolder)
        onExportAsHtmlRequested:
            if (pane.appWindow && pane.appWindow.openWebExport)
                pane.appWindow.openWebExport()
    }

    PeopleAlbumContextMenu {
        id: peopleAlbumContextMenu
        onSelectAllRequested:
            if (pane.appWindow && pane.appWindow.selectAll) pane.appWindow.selectAll()
        onClearSelectionRequested:
            if (pane.appWindow && pane.appWindow.clearSelection)
                pane.appWindow.clearSelection()
    }

    FolderListContextMenu {
        id: folderListContextMenu
        onSortModeRequested: function(mode) {
            if (controller) controller.setFolderSort(mode)
        }
        onSortReverseRequested: if (controller) controller.toggleFolderSortReverse()
    }

    FolderContextMenu {
        id: folderContextMenu
        onMoveToCollectionRequested: function(collectionName) {
            if (controller) controller.moveFolderToCollection(
                folderContextMenu.folderPath, collectionName)
        }
        onNewCollectionRequested: {
            // #422: a létrehozás-ág — a _renamingCollection üresen marad,
            // az initialName is üres (a korábbi átnevezésből esetleg
            // bennragadt értéket felülírjuk)
            pane._renamingCollection = ""
            newCollectionDialog.initialName = ""
            newCollectionDialog.open()
        }

        // #422: az eredeti `album.fen` dialógusa — a mappa DÁTUMA is itt
        // lakik, ezért szűnt meg a külön „Mappa dátumának beállítása…"
        // menütétel
        onEditDescriptionRequested: {
            var path = folderContextMenu.folderPath
            folderPropertiesDialog.folderPath = path
            folderPropertiesDialog.folderName =
                path.substring(path.lastIndexOf("/") + 1)
            folderPropertiesDialog.currentDate =
                controller ? controller.folderDateOverride(path) : ""
            folderPropertiesDialog.currentDescription =
                controller ? controller.folderDescriptionOf(path) : ""
            folderPropertiesDialog.open()
        }

        onSelectAllRequested:
            if (pane.appWindow && pane.appWindow.selectAll) pane.appWindow.selectAll()
        onClearSelectionRequested:
            if (pane.appWindow && pane.appWindow.clearSelection)
                pane.appWindow.clearSelection()
        onInvertSelectionRequested:
            if (pane.appWindow && pane.appWindow.invertSelection)
                pane.appWindow.invertSelection()

        onRefreshThumbnailsRequested:
            if (controller) controller.resyncFolder(folderContextMenu.folderPath)
        onSortModeRequested: function(mode) {
            if (controller) controller.setFolderSort(mode)
        }
        onSortReverseRequested: if (controller) controller.toggleFolderSortReverse()

        onLocateRequested: {
            if (typeof fileOpsController !== "undefined" && fileOpsController)
                fileOpsController.revealFolder(folderContextMenu.folderPath)
        }
        onRemoveFromPicasaRequested: removeFolderConfirm.ask(
            "removeFolder",
            qsTr("Remove this folder from PicasaPy? The files stay on disk."))
        onExportAsHtmlRequested:
            if (pane.appWindow && pane.appWindow.openWebExport)
                pane.appWindow.openWebExport()
    }

    // „Eltávolítás a Picasából…" — a fájlok a lemezen maradnak, csak a
    // figyelt mappák közül kerül ki (#422)
    ConfirmDialog {
        id: removeFolderConfirm
        namePrefix: "removeFolderConfirm"
        onConfirmed: {
            if (controller && folderContextMenu.folderPath !== "")
                controller.removeWatchedFolder(folderContextMenu.folderPath)
        }
    }

    FolderPropertiesDialog {
        id: folderPropertiesDialog
        onFolderPropertiesAccepted: function(path, isoDate, description) {
            if (!controller) return
            controller.setFolderDescriptionOf(path, description)
            // üres dátum = „automatikus dátum": a felülírás törlése
            if (isoDate.length > 0) controller.setFolderDate(path, isoDate)
            else controller.clearFolderDate(path)
        }
    }

    NewCollectionDialog {
        id: newCollectionDialog
        onCreated: function(name) {
            if (!controller) return
            // #422: ugyanaz a dialógus szolgálja a létrehozást (a
            // FolderContextMenu "Új gyűjtemény…" ága) ÉS az átnevezést (a
            // CollectionContextMenu "Gyűjtemény átnevezése…" ága) — a két
            // használatot a pane._renamingCollection különbözteti meg.
            if (pane._renamingCollection !== "") {
                controller.renameCollection(pane._renamingCollection, name)
                pane._renamingCollection = ""
            } else {
                controller.createCollection(name)
                // Picasa-mintára: a "Move to Collection ▸ New Collection…"-ból
                // indított létrehozás a jobbklikkelt mappát rögtön bele is
                // sorolja az új gyűjteménybe.
                if (folderContextMenu.folderPath !== "")
                    controller.moveFolderToCollection(
                        folderContextMenu.folderPath, name)
            }
            pane.refreshCustomCollections()
        }
    }

    // #422: a gyűjtemény jobbklikk-menüje (átnevezés/eltávolítás/jelszó) —
    // a Collection menüosztály, a #476-ban készült CollectionHeader
    // fejlécre kötve (pane.openCollectionContextMenu).
    CollectionContextMenu {
        id: collectionContextMenu
        onRenameRequested: {
            pane._renamingCollection = collectionContextMenu.collectionName
            newCollectionDialog.initialName = collectionContextMenu.collectionName
            newCollectionDialog.open()
        }
        // #461: az eredeti Picasa szövege kimondja, hogy a mappák NEM
        // vesznek el — az alapértelmezett gyűjteménybe kerülnek. Ez a
        // megnyugtató mondat a lényeg, ezért szó szerint átvesszük.
        onRemoveRequested: removeCollectionConfirm.ask(
            "removeCollection",
            qsTr("Are you sure you want to remove the collection \u201c%1\u201d? "
                 + "All folders in it will be moved to the collection "
                 + "\u201c%2\u201d.")
                .replace("%1", collectionContextMenu.collectionName)
                .replace("%2", qsTr("Folders on Disk")))
    }

    // „Gyűjtemény eltávolítása" megerősítése (#422) — egyedi namePrefix,
    // hogy ne ütközzön a removeFolderConfirm-mal
    ConfirmDialog {
        id: removeCollectionConfirm
        namePrefix: "removeCollectionConfirm"
        onConfirmed: {
            if (controller && collectionContextMenu.collectionName !== "")
                controller.deleteCollection(collectionContextMenu.collectionName)
            pane.refreshCustomCollections()
        }
    }

}
