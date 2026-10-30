import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

// A bal hasáb görgethető szakaszai és a mappafa listanézete.
Flickable {
    property var folderPane: null
    property var folderHierarchyController: null
    property alias folderListModel: folderList.model
    property alias folderListView: folderList
    property alias folderHierarchyView: folderHierarchyView
    id: paneFlickable
    objectName: "folderPaneFlickable"
    anchors.fill: parent
    clip: true
    contentWidth: width
    contentHeight: paneColumn.height
    boundsBehavior: Flickable.StopAtBounds

    ScrollBar.vertical: PicasaScrollBar {
        objectName: "folderPaneScrollBar"
        // az eredeti sávja akkor is ott van, amikor nincs mit görgetni
        policy: ScrollBar.AlwaysOn
    }

    ColumnLayout {
        id: paneColumn
        width: paneFlickable.width
        // a magasságot a TARTALOM adja (nem az ablak) — ez a görgethető
        // tartalommagasság forrása is
        height: implicitHeight
        spacing: 0

        // Az Albumok gyűjtemény (fejléc + súgó + csillagozott sor +
        // album-sorok) önálló komponensben él — ld. AlbumsSection.qml.
        AlbumsSection {
            Layout.fillWidth: true
            collapsed: folderPane.albumsCollapsed
            albumsModel: folderPane.albumsModel
            selectedAlbumToken: folderPane.selectedAlbumToken
            starredActive: folderPane.starredActive
            searchResultsText: folderPane.searchResultsAlbumText
            rowHeight: folderPane.rowHeight
            onToggled: folderPane.toggleCollection("albums")
            onStarredChosen: folderPane.starredChosen()
            onAlbumChosen: function(token) { folderPane.albumChosen(token) }
            onAlbumContextMenuRequested: function(token, name) {
                folderPane.openAlbumContextMenu(token, name)
            }
            onNewAlbumPhotosDropped: function(photoRows) {
                folderPane.newAlbumPhotosDropped(photoRows)
            }
            onPhotosDroppedOnAlbum: function(token, photoRows) {
                folderPane.photosDroppedOnAlbum(token, photoRows)
            }
        }

        CollectionHeader {
            Layout.fillWidth: true
            label: qsTr("People")
            // #5190: a látható sorok száma, a „Névtelenek" albumot is
            // beleszámítva, ha van névtelen arc vagy folyik a keresés.
            // #5341: a mellőzött sort is, ha látszik.
            itemCount: folderPane.peopleModel.length
                       + (folderPane.unnamedSlotShown ? 1 : 0)
                       + (folderPane.ignoredSlotShown ? 1 : 0)
            labelObjectName: "peopleHeader"
            collapsed: folderPane.peopleCollapsed
            onToggled: folderPane.toggleCollection("people")
        }

        // #5190: a „Névtelenek" sor a személyek elé kerül, és a fejléc
        // darabszámába is beleszámít.
        Rectangle {
            id: unnamedFacesItem
            objectName: "unnamedFacesItem"
            // Beolvasás közben a sor akkor is látszik, ha még nincs találat.
            visible: !folderPane.peopleCollapsed && folderPane.unnamedSlotShown
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            color: folderPane.unnamedFacesActive ? Theme.panelSelectionActive
                   : (unnamedFacesMouse.containsMouse ? Theme.panelSelection : "transparent")
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 16
                spacing: 5
                Image {
                    objectName: "unnamedFacesIcon"
                    width: 18; height: 18
                    anchors.verticalCenter: parent.verticalCenter
                    source: Qt.resolvedUrl("icons/person-silhouette.svg")
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                }
                Text {
                    objectName: "unnamedFacesLabel"
                    text: folderPane.faceScanPercent >= 0
                          ? qsTr("Scanning for faces... %1% complete")
                            .arg(folderPane.faceScanPercent)
                          : qsTr("Unnamed") + " (" + folderPane.unnamedFaceCount + ")"
                    font.pixelSize: Theme.fontSize
                    font.italic: folderPane.faceScanPercent >= 0
                    color: folderPane.unnamedFacesActive || unnamedFacesMouse.containsMouse
                           ? Theme.panelSelectionText : Theme.textDark
                }
            }
            MouseArea {
                id: unnamedFacesMouse
                anchors.fill: parent
                hoverEnabled: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: function(mouse) {
                    if (mouse.button === Qt.RightButton) {
                        folderPane.openPeopleAlbumContextMenu(qsTr("Unnamed"))
                        return
                    }
                    folderPane.unnamedFacesChosen()
                }
            }
        }

        // #26: egy-egy sor személyenként — az AlbumsSection.qml album-sorainak
        // mintáját követi.
        Repeater {
            id: peopleRepeater
            objectName: "peopleRepeater"
            model: folderPane.peopleModel
            delegate: Rectangle {
                id: personItem
                required property var modelData
                readonly property string personRowKey:
                    modelData.name + (modelData.person_id
                        ? "_" + modelData.person_id : "")
                objectName: "personItem_" + personItem.personRowKey
                readonly property bool isSelectedPerson:
                    folderPane.selectedPersonName === modelData.name
                visible: !folderPane.peopleCollapsed
                Layout.fillWidth: true
                Layout.preferredHeight: 22
                color: personItem.isSelectedPerson ? Theme.panelSelectionActive
                       : (personMouse.containsMouse ? Theme.panelSelection : "transparent")
                Row {
                    anchors.verticalCenter: parent.verticalCenter
                    anchors.left: parent.left; anchors.leftMargin: 16
                    spacing: 5
                    Image {
                        objectName: "personThumbnailImage_"
                            + personItem.personRowKey
                        width: source !== "" ? 18 : 0
                        height: 18
                        anchors.verticalCenter: parent.verticalCenter
                        source: modelData.thumbUrl || ""
                        fillMode: Image.PreserveAspectCrop
                        smooth: true
                        mipmap: true
                        asynchronous: true
                        visible: source !== ""
                    }
                    Rectangle {
                        width: 10; height: 10
                        radius: 5
                        anchors.verticalCenter: parent.verticalCenter
                        color: Theme.picasaGreen
                        visible: !modelData.thumbUrl
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
                            folderPane.openPeopleAlbumContextMenu(
                                personItem.modelData.name,
                                personItem.modelData.person_id || "")
                            return
                        }
                        folderPane.personChosen(personItem.modelData.name)
                    }
                }
            }
        }

        // #26: a mellőzött arcok sora, ugyanabban a gyűjteményben. #5341:
        // csak a mellőzött nézetben látszik, a Névtelenek sora helyén.
        Rectangle {
            objectName: "ignoredFacesItem"
            visible: !folderPane.peopleCollapsed && folderPane.ignoredSlotShown
            Layout.fillWidth: true
            Layout.preferredHeight: 22
            color: folderPane.ignoredFacesActive ? Theme.panelSelectionActive
                   : (ignoredFacesMouse.containsMouse ? Theme.panelSelection : "transparent")
            Row {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left; anchors.leftMargin: 16
                spacing: 5
                Rectangle {
                    width: 10; height: 10
                    radius: 5
                    anchors.verticalCenter: parent.verticalCenter
                    color: Theme.textDark
                    opacity: 0.25
                }
                Text {
                    objectName: "ignoredFacesLabel"
                    text: qsTr("Ignored") + " (" + folderPane.ignoredFaceCount + ")"
                    font.pixelSize: Theme.fontSize
                    color: folderPane.ignoredFacesActive || ignoredFacesMouse.containsMouse
                           ? Theme.panelSelectionText : Theme.textDark
                }
            }
            MouseArea {
                id: ignoredFacesMouse
                anchors.fill: parent
                hoverEnabled: true
                // #732: a „Mellőzött emberek" is ALBUM az eredetiben
                // (`CAlbumLabel::Ignored`) — ld. a „Névtelenek" sort
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: function(mouse) {
                    if (mouse.button === Qt.RightButton) {
                        folderPane.openPeopleAlbumContextMenu(
                            qsTr("Ignored people"))
                        return
                    }
                    folderPane.ignoredFacesChosen()
                }
            }
        }

        // A Projektek gyűjtemény (fejléc + a P2category-alapú
        // projekt-mappák + az „Exportált képek" csomópont) önálló
        // komponensben él — ld. ProjectsSection.qml (#1029).
        ProjectsSection {
            objectName: "projectsSection"
            Layout.fillWidth: true
            collapsed: folderPane.projectsCollapsed
            projectFolders: folderPane.projectFolders
            exportedFolders: folderPane.exportedFolders
            selectedPath: folderPane.selectedPath
            selectedAlbumToken: folderPane.selectedAlbumToken
            rowHeight: folderPane.rowHeight
            onToggled: folderPane.toggleCollection("projects")
            onFolderChosen: function(path) { folderPane.folderChosen(path) }
            onFolderContextMenuRequested: function(path) {
                folderPane.openFolderContextMenu(path)
            }
        }

        CollectionHeader {
            Layout.fillWidth: true
            //: #1407: a fejléc a GYÖKERET nevezi meg, nem a gyűjteményt —
            //: az eredeti hasábban is ez a felirat áll itt. A darabszám
            //: és a csukhatóság változatlan.
            label: folderPane.folderRootLabel
            itemCount: folderList.model ? folderList.model.folderCount : 0
            labelObjectName: "folderPaneHeader"
            collapsed: folderPane.foldersCollapsed
            onToggled: folderPane.toggleCollection("folders")
        }

        ListView {
            id: folderList
            objectName: "folderListView"
            // #702: a lapos lista és a fa KIZÁRJA egymást — az eredeti
            // `thumbui/hviewtoggle` is egyszerre csak az egyiket rajzolja
            visible: !folderPane.foldersCollapsed && !folderPane.treeViewMode
            Layout.fillWidth: true
            // #730: a lista a TELJES tartalmát kirakja, a görgetés a
            // hasáb közös `paneFlickable`-jéé. A korábbi
            // `Layout.fillHeight: true` alsó korlát nélkül működött:
            // amint a fölötte lévő sorok kitöltötték az ablakot, a
            // maradék hely — és vele a lista magassága — 0 lett.
            // A sormagasság állandó, ezért a darabszámból pontosan
            // számolható (a `contentHeight`-ra kötés a még meg nem
            // született delegate-ek miatt becsléssel indulna).
            //
            // #3681: mentés-szűrő módban a lista a MENTETLEN mappákra
            // szűkül (a delegate a többit 0 magasságúra állítja) — a
            // sorszám ekkor a ténylegesen kirajzolt mentetlen soroké.
            Layout.preferredHeight:
                (folderPane.mentesSzuroAktiv
                    ? folderPane.mentesLaposSorok
                    : folderList.count) * folderPane.rowHeight
            clip: true

            // kurzorgombok, amikor a lista fókuszban van (#77)
            activeFocusOnTab: true
            Keys.onUpPressed: folderPane.stepFolder(-1)
            Keys.onDownPressed: folderPane.stepFolder(1)

            // #731: a görgő-léptetés (#77) CSAK a mappalista fölött
            // aktív. Korábban a hasáb GYÖKERÉN ült egy `WheelHandler`,
            // ezért a görgő bárhol a hasáb fölött MÁSIK mappát nyitott
            // meg görgetés helyett. Ez a kezelő a listán mélyebben van,
            // mint a hasáb `paneFlickable`-je, ezért a találati sorrend
            // szerint itt ő kapja meg előbb az eseményt; a hasáb többi
            // része fölött viszont a `paneFlickable` görget.
            WheelHandler {
                objectName: "folderStepWheelHandler"
                //: #3681: szűrő módban nem léptet — a görgő ilyenkor a
                //: hasábot görgeti (`paneFlickable`)
                enabled: !folderPane.mentesSzuroAktiv
                acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
                onWheel: function(event) { folderPane.wheelStep(event.angleDelta.y) }
            }

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
                // #305 null-őr: fa-nézetben (és a komponens önálló
                // betöltésekor) a lapos listának nincs modellje
                target: folderList.model ? folderList.model : null
                function onFolderCountChanged() {
                    folderList.restoring = true
                    folderList.contentY = Math.min(
                        folderList.savedY,
                        Math.max(0, folderList.contentHeight
                                    - folderList.height))
                    folderList.restoring = false
                }
            }
                delegate: FolderPaneTreeRow {
                    folderPane: paneFlickable.folderPane
                    listView: folderList
                }
            // #730: a lista SAJÁT görgetősávja megszűnt — a hasáb
            // egészét a `paneFlickable` görgeti, egyetlen sávval (az
            // eredetiben is egy sáv van a bal panelen).
        }

        // #702: ugyanennek a gyűjteménynek a MÁSIK nézetmódja — a
        // hierarchikus fa. A rajzolás a `FolderHierarchyView.qml`-ben
        // van, az adat a `FolderHierarchyController`-ben; itt csak a
        // hasábba illesztés és a jelzések bekötése történik.
        FolderHierarchyView {
            id: folderHierarchyView
            objectName: "folderHierarchyView"
            visible: !folderPane.foldersCollapsed && folderPane.treeViewMode
            Layout.fillWidth: true
            // #730: a fa is a TELJES tartalmát kirakja — a hasáb
            // egyetlen görgetője a `paneFlickable` marad. A sorok
            // számát a KIRAJZOLT (mentés-szűrő módban SZŰKÍTETT) lista
            // adja, nem a vezérlő teljes fája — #3681 előtt a kettő
            // ugyanaz volt.
            Layout.preferredHeight: folderHierarchyView.rowCount * folderPane.rowHeight
            hierarchy: folderHierarchyController
            selectedPath: folderPane.selectedPath
            rowHeight: folderPane.rowHeight
            // #3681: közös szerződés a lapos listával — a mentés-panel
            // (`BackupHost`, `Main.qml`-en át) ide is eljut
            mentesSzuroAktiv: folderPane.mentesSzuroAktiv
            mentesMentetlenMappak: folderPane.mentesMentetlenMappak
            mentesPipaltMappak: folderPane.mentesPipaltMappak
            onMentesPipaldKert: function (mappa, be) {
                folderPane.mentesPipaldKert(mappa, be)
            }
            onFolderChosen: function(path) { folderPane.folderChosen(path) }
            onFolderDroppedOnFolder: function(sourcePath, targetPath) {
                folderPane.folderDroppedOnFolder(sourcePath, targetPath)
            }
            //: #5119: a rácsból a fa mappasorára húzott képek
            onPhotosDroppedOnFolder: function(path, photoRows) {
                folderPane.photosDroppedOnFolder(path, photoRows)
            }
            onFolderContextMenuRequested: function(path) {
                folderPane.openFolderContextMenu(path)
            }

            // A `HierFolder` menü három tétele, aminek a rétege a
            // gazdában van — ugyanazokra a hívásokra kötve, mint a
            // mappa-menü megfelelő parancsai (FolderContextMenu).
            onLocateOnDiskRequested: function(path) {
                if (typeof fileOpsController !== "undefined" && fileOpsController)
                    fileOpsController.revealFolder(path)
            }
            onRemoveFromPicasaRequested: function(path) {
                folderPane._askRemoveFolder(path)
            }
            onMoveFolderRequested: function(path) {
                    folderPane.mozgatasMappara(path)
            }
        }

        // #3681: a mentés-szűrő állapotfelirata a mappák helyén —
        // számolás közben, üres készletnél és készlet nélkül
        Text {
            objectName: "folderPaneMentesAllapot"
            visible: folderPane.mentesAllapotSzoveg !== "" && !folderPane.foldersCollapsed
            Layout.fillWidth: true
            Layout.leftMargin: 12
            Layout.rightMargin: 6
            Layout.topMargin: 4
            Layout.bottomMargin: 4
            text: folderPane.mentesAllapotSzoveg
            wrapMode: Text.WordWrap
            font.pixelSize: Theme.fontSize
            color: Theme.textGray
        }

        // #476: a felhasználói mappa-gyűjtemények (#320 óta léteznek, de
        // eddig sehol nem jelentek meg) — a beépített "Mappák" gyűjtemény
        // ALATT, az "Egyéb" fejléc ELŐTT, gyűjteményenként egy csukható
        // fejléc + a hozzá sorolt mappák sorai (az AlbumsSection/folderList
        // sor-mintáját követve).
        Repeater {
            id: customCollectionsRepeater
            objectName: "customCollectionsRepeater"
            model: folderPane.customCollectionsModel
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
                    collapsed: folderPane.isCustomCollectionCollapsed(customCollectionItem.modelData.name)
                    closable: true
                    closed: customCollectionItem.modelData.closed === true
                    onCloseToggled: folderPane.requestCollectionCloseToggle(
                        customCollectionItem.modelData.name,
                        customCollectionItem.modelData.closed === true)
                    onToggled: folderPane.toggleCustomCollection(customCollectionItem.modelData.name)
                    onRightClicked: folderPane.openCollectionContextMenu(
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
                            folderPane.selectedPath === customFolderItem.modelData
                            && folderPane.selectedAlbumToken === ""
                        // #461: a bezárt gyűjtemény tartalma sem a fában, sem a
                        // rácsban nem látszik — a fejléce viszont marad, hogy
                        // vissza lehessen nyitni
                        visible: !folderPane.isCustomCollectionCollapsed(customCollectionItem.modelData.name)
                                 && customCollectionItem.modelData.closed !== true
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
                            // #732: a gyűjteménybe sorolt mappa ugyanaz
                            // a MAPPA, mint a Mappák-listában — ugyanazt
                            // a menüt kell adnia (egy komponens, több
                            // hívó; ui-audit-context-menus.md 1.b)
                            acceptedButtons: Qt.LeftButton | Qt.RightButton
                            onClicked: function(mouse) {
                                if (mouse.button === Qt.RightButton) {
                                    folderPane.openFolderContextMenu(
                                        customFolderItem.modelData)
                                    return
                                }
                                folderPane.folderChosen(customFolderItem.modelData)
                            }
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
            collapsed: folderPane.otherCollapsed
            onToggled: folderPane.toggleCollection("other")
        }
    }
}
